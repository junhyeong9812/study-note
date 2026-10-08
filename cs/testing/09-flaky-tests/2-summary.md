# testing/09-flaky-tests — 불안정 테스트: 같은 코드에서 초록과 빨강이 번갈아 나온다 — 정리 (힌트)

## 해결하는 문제

쉬운 예부터 보자.

- 화재경보기가 일주일에 두 번씩 이유 없이 울린다고 하자. 한 달쯤 지나면 사람들은 경보가 울려도 나가지 않는다.
- 그러다 진짜 불이 나도, 경보는 울렸지만 아무도 안 움직인다.

똑같은 구조다.

- CI가 가끔 빨강을 낸다. 다시 돌리면 초록이다. 사람들은 "또 그 테스트네" 하고 재실행 버튼을 누른다.
- 어느 날 진짜 결함이 그 테스트를 빨갛게 만든다. 그 빨강도 재실행으로 넘어간다.
  - *불안정 테스트(flaky test)*: 코드와 테스트를 바꾸지 않았는데 결과가 실행마다 달라지는 테스트.

정의는 출처마다 조금 다르게 적는다.

| 출처 | 정의 |
|---|---|
| Luo 외, FSE 2014 | 같은 소프트웨어 버전에 대해 결과가 비결정적인 테스트("their outcome is non-deterministic with respect to a given software version") |
| Google Testing Blog, Micco 2016 | 같은 코드로 통과와 실패를 모두 보인 테스트("exhibits both a passing and a failing result with the same code") |
| SWE@G 13장 「Determinism」 | 결정적 테스트 = 같은 SUT 버전에서 늘 같은 결과. 비결정성이 불안정성(flakiness)으로 이어진다 |

실무에서 얼마나 큰 문제인지 수치로 보면 이렇다(전부 출처의 수치 그대로).

- Google Testing Blog(John Micco, 2016-05-27)
  - 전체 테스트 실행의 약 1.5%가 "flaky" 결과를 냈다.
  - 테스트의 약 16%가 어느 정도 불안정성을 가졌다.
  - post-submit에서 관찰한 통과→실패 전이의 약 84%에 불안정 테스트가 끼어 있었다.
- SWE@G 11장 「Case Study: Flaky Tests Are Expensive」
  - 테스트마다 0.1% 확률로 잘못 실패하고 하루 1만 개를 돌리면, 하루 10건을 조사해야 한다.
  - 저자들의 경험: 불안정 비율이 1%에 가까워지면 테스트가 가치를 잃기 시작한다. 당시 Google의 비율은 약 0.15%였다.
- Luo 외 FSE 2014 1장: Google TAP에서 15개월간 하루 평균 160만 건의 테스트 실패 중 7.3만 건(4.56%)이 불안정 테스트 때문이었다(John Micco와의 개인 교신으로 받은 수치라고 적혀 있다).

이 노트가 다루는 것은 두 가지다.

1. 불안정성은 어디서 오나(원인 분류).
2. 재시도로 덮지 않고 어떻게 찾아 고치나.

## 동작·원리

### 1. 시간축으로 본 불안정 테스트

```text
 커밋 a1b2c (코드·테스트 변화 없음)
 실행 1  ──[PASS]──
 실행 2  ──[FAIL]──   ← 같은 커밋인데 빨강
 실행 3  ──[PASS]──
 실행 4  ──[PASS]──
 실행 5  ──[FAIL]──

 바뀐 것은 코드 밖의 무엇:  스레드 스케줄 · 테스트 실행 순서 · 시각 · 네트워크 · 난수 · 머신 속도
```

- 테스트 결과는 "코드 + 환경"의 함수다.
- 환경 중 테스트가 통제하지 않는 입력이 있으면, 결과가 그 입력을 따라 흔들린다.
- 그래서 불안정 테스트를 고친다는 것은 **숨은 입력을 찾아 테스트가 통제하게 만드는 일**이다.

### 2. 원인 분류 — Luo 외 FSE 2014

Apache 재단 51개 프로젝트에서 "불안정 테스트를 고친 것으로 보이는" 커밋 201개를 읽었다. 원인을 분류할 수 있었던 커밋은 161개였다(3.1절).

```text
 161건 중
 Async Wait            ██████████████████████  74 (45%)
 Concurrency           ██████████              32 (20%)
 Test Order Dependency ██████                  19 (12%)
 나머지 7개 범주       █████████████████       36 (22%, 161-74-32-19로 계산)
   Resource Leak · Network · Time · IO · Randomness · Floating Point · Unordered Collections
```

- *Async Wait(비동기 대기)*: 비동기 호출을 해 놓고 결과가 준비될 때까지 제대로 기다리지 않는다. 결과가 먼저 오면 통과, 늦으면 실패다.
- *Concurrency(동시성)*: 스레드끼리 바람직하지 않게 얽힌다(데이터 경쟁·원자성 위반·교착). Async Wait과는 따로 센다.
- *Test Order Dependency(순서 의존)*: 테스트 결과가 실행 순서에 따라 달라진다. 공유 상태를 제대로 준비·정리하지 않아서 생긴다.

논문 표 1의 발견 중 실무에 바로 쓰이는 것들이다.

| 발견 | 내용 |
|---|---|
| F.2 | 불안정 테스트 대부분(78%, 161건 중 126건)은 **처음 작성될 때부터** 불안정했다 |
| F.3 | 거의 전부(96%)가 플랫폼(OS·하드웨어)과 무관했다 |
| F.4 | Async Wait의 34%(74건 중 25건)가 시간 지연을 둔 `sleep`이나 `waitFor`로 순서를 맞추려 했다 — 지연 값만 줄여도 실패를 재현할 수 있다(4.2.1절) |
| F.6 | Concurrency 실패는 거의 다 두 스레드로 줄일 수 있었다 |
| F.12 | 고친 커밋의 24%(161건 중 38건)는 테스트와 함께 제품 코드(CUT)도 고쳤고, 그중 94%가 제품 코드의 버그 수정이었다(5.2절) |

- F.12가 중요하다. 불안정 테스트의 상당수는 **진짜 버그의 증상**이었다.
- 순서 의존 19건의 출처(4.2.3절): 테스트 코드의 정적 필드 3건, 제품 코드의 정적 필드 6건, 외부 자원(공유 파일·네트워크 포트) 10건.

### 3. 원인별 메커니즘

**(a) 비동기 대기 — 고정 sleep**

```text
 테스트 스레드:  start() ──── sleep(50ms) ────▶ assert(result != null)
 작업 스레드:         [====== 작업 30ms ======]                     빠른 머신: 끝난 뒤 검사 → PASS
 작업 스레드:         [============== 작업 70ms (CPU 경합) ==============] 느린 머신: 끝나기 전 검사 → FAIL
```

- 고정 sleep은 "작업이 50ms 안에 끝난다"는 가정을 숨겨 둔다.
- CI 머신이 바쁘면 가정이 깨진다. Luo 5.1.1절: sleep으로 고친 20건 중 60%는 **이미 있던 sleep을 늘린** 수정이었다. 그런 수정은 실패 확률을 낮출 뿐 없애지 못한다고 논문은 평가한다.

**(b) 순서 의존 — 오염자(polluter)와 피해자(victim)**

```text
 공유 정적 상태:  Cart.items = []

 순서 1:  startsEmpty ✔ → addOne ✔ → addTwo ✔        피해자가 먼저 → 통과
 순서 2:  addOne ✔ → startsEmpty ✘ → addTwo ✔        오염자가 먼저 → 피해자 실패
                       ↑ items=[apple]
```

- *오염자(polluter)*: 공유 상태를 바꿔 놓고 원래대로 돌리지 않는 테스트.
- *피해자(victim)*: 공유 상태가 초기값이라고 가정하는 테스트.
- Luo 3.1.3절이 이 두 모양을 설명한다. 다른 테스트가 상태를 바꿔 놓았거나, 상태를 만들어 주던 테스트가 먼저 돌지 않았다.

**(c) 동시성 — 두 스레드의 끼어들기**

```text
 count = 5
 T1: 읽기(5) ────────────── 쓰기(6)
 T2:        읽기(5) ── 쓰기(6)          → 두 번 더했는데 6
```

- 결과가 스레드 스케줄에 달려 있다. 스케줄은 실행마다 다르다. 원리는 [os/15-race-conditions](../../os/15-race-conditions/2-summary.md)에 있다.

**(d) 나머지 숨은 입력**

| 범주(Luo 3.1.4) | 숨은 입력 | 대표 모양 |
|---|---|---|
| Time | 시스템 시각 | UTC 자정이 바뀔 때 실패. 시각 정밀도가 플랫폼마다 다름 → [10](../10-testing-time-and-concurrency/2-summary.md) |
| Network | 원격 연결·소켓 | 원격 연결 실패(60%)와 로컬 소켓 관리 잘못(40%) |
| IO | 파일 핸들 | 파일을 닫지 않아 GC 시점에 따라 다음 테스트가 파일을 못 엶 |
| Randomness | 난수 | 1바이트 난수가 정확히 0일 때만 실패 |
| Unordered Collections | 해시 순회 순서 | `Set` 순회 순서를 기대값에 박음 |
| Floating Point | 연산 순서 | 비결합적 덧셈·오버플로 |
| Resource Leak | 풀·메모리 | 반납 안 한 연결이 쌓여 나중 테스트가 실패 |

### 실험 A: 공유 정적 상태 — 무작위 순서 20번

(실험, JDK 21.0.12 temurin · JUnit 5.13.4 Launcher API, `--cpus=2`, 2026-10-03)

```java
class Cart { static final List<String> items = new ArrayList<>(); }   // 모든 테스트가 같은 리스트

class CartOrderTest {
  @Test void addOne()      { Cart.items.add("apple"); assertTrue(Cart.items.contains("apple")); }
  @Test void addTwo()      { Cart.items.add("b");     assertTrue(Cart.items.contains("b")); }
  @Test void startsEmpty() {                          assertEquals(0, Cart.items.size()); }
}
// 고친 판: 같은 세 테스트 + @BeforeEach void reset() { Cart.items.clear(); }
```

- 같은 클래스를 기본 순서로 1번, `MethodOrderer.Random`에 시드 1~20을 주어 20번 실행했다.
- 실행 사이에 `Cart.items`를 비웠다. 새 JVM에서 시작한 것처럼 만들기 위해서다.

```text
  startsEmpty 실행 시 items=[apple, b]          ← 기본 순서의 첫 실행
CartOrderTest: 기본 순서 실패 1개 | 무작위 순서 시드 1..20 중 실패한 실행 12/20 (시드별 실패 수 10111011010101000111)
CartOrderFixedTest: 기본 순서 실패 0개 | 무작위 순서 시드 1..20 중 실패한 실행 0/20 (시드별 실패 수 00000000000000000000)
```

- 관찰 1 — 기본 순서에서는 이 실행 환경에서 피해자가 마지막에 돌아 실패했다. 이 실험을 3번 돌렸는데 기본 순서의 결과도, 시드별 실패 패턴(`10111011010101000111`)도 3번 모두 같았다. 기본 순서는 결정적이고, 시드를 고정한 무작위 순서는 재현된다.
  - 해석: 기본 순서가 우연히 피해자를 맨 앞에 두는 클래스라면, 결함은 숨은 채 "초록"으로 남는다. 테스트 메서드 하나를 추가하거나 이름을 바꾸면 순서가 달라져 갑자기 드러날 수 있다(Luo 3.2절: 나중에 불안정해진 23건의 첫째 원인이 "격리를 깨는 새 테스트 추가"였다).
- 관찰 2 — 무작위 순서 20번 중 12번 실패했다. 세 테스트 중 피해자가 첫 자리에 올 때만 통과하므로 기대 실패율은 2/3이다. 20번에서 12번은 그 근처다.
- 관찰 3 — `@BeforeEach`로 공유 상태를 초기화하자 20번 모두 통과했다. Luo F.10: 순서 의존 수정의 74%가 "테스트 사이 공유 상태 정리"였다.

### 실험 B: 고정 sleep 대기 — 머신이 바쁠수록 실패한다

(실험, JDK 21.0.12 temurin · JUnit 5.13.4, `--cpus=2`, 2026-10-03. 실행마다 다르다 — 조건마다 2번씩 돌렸다)

```java
// 작업: 무부하에서 약 30ms 걸리도록 반복 횟수를 보정한 CPU 계산
static Future<?> generateAsync() { result = null; return pool.submit(() -> { result = spin(ITER); }); }

class AsyncSleepTest { @Test void reportIsReady() throws Exception {
  Work.generateAsync(); Thread.sleep(50); assertNotNull(Work.result); } }           // "50ms면 끝나겠지"

class AsyncWaitTest  { @Test void reportIsReady() throws Exception {
  Work.generateAsync().get(5, TimeUnit.SECONDS); assertNotNull(Work.result); } }    // 끝났다는 신호를 기다린다
```

- 같은 JVM에 CPU를 계속 쓰는 부하 스레드 0·2·4개를 띄우고, 각 테스트를 50번 돌렸다. 부하 스레드는 CI 러너에서 다른 작업이 CPU를 나눠 쓰는 상황의 흉내다.

```text
보정: ITER=4545454, 무부하 1회 29ms
부하 스레드 0개 | AsyncSleepTest: 50회 중 실패 0회, 총 3947ms
부하 스레드 0개 | AsyncWaitTest: 50회 중 실패 0회, 총 1888ms
보정: ITER=4687500, 무부하 1회 31ms
부하 스레드 0개 | AsyncSleepTest: 50회 중 실패 1회, 총 4004ms
부하 스레드 0개 | AsyncWaitTest: 50회 중 실패 0회, 총 1996ms
보정: ITER=4687500, 무부하 1회 31ms
부하 스레드 2개 | AsyncSleepTest: 50회 중 실패 13회, 총 6844ms
부하 스레드 2개 | AsyncWaitTest: 50회 중 실패 0회, 총 4524ms
보정: ITER=4545454, 무부하 1회 30ms
부하 스레드 2개 | AsyncSleepTest: 50회 중 실패 8회, 총 6987ms
부하 스레드 2개 | AsyncWaitTest: 50회 중 실패 0회, 총 4369ms
보정: ITER=4545454, 무부하 1회 30ms
부하 스레드 4개 | AsyncSleepTest: 50회 중 실패 32회, 총 8259ms
부하 스레드 4개 | AsyncWaitTest: 50회 중 실패 0회, 총 8618ms
보정: ITER=4166666, 무부하 1회 30ms
부하 스레드 4개 | AsyncSleepTest: 50회 중 실패 30회, 총 8920ms
부하 스레드 4개 | AsyncWaitTest: 50회 중 실패 0회, 총 7322ms
```

- 사실 점검 재실행(같은 코드·같은 명령, 조건마다 3번 더, 2026-10-03): sleep 판 실패는 무부하 0·1·4회, 부하 2개 15·13·10회, 부하 4개 31·30·31회. 조건 판은 아홉 번 모두 0회였다.
- 관찰 1 — 위 출력과 재실행을 합친 다섯 번에서 sleep 판은 무부하 0~4회, 부하 2개 8~15회, 부하 4개 30~32회 실패했다. 로컬(한가한 노트북)에서 초록인 테스트가 바쁜 CI에서 빨강이 되는 모양이다. 무부하에서도 0회로 고정되지 않는다 — 30ms 작업과 50ms 대기의 여유가 작기 때문이다.
- 관찰 2 — 신호를 기다리는 판(`Future.get`)은 모든 실행에서 0회였다. 5초 상한이 작업 시간보다 훨씬 길기 때문이다. Luo F.8·5.1.1절: Async Wait 74건 중 42건(57%, 본문 수치 — 표 1은 54%로 적는다)이 `waitFor`류로 고쳐졌다. 그중 불안정성을 **완전히 없앤** 것은 23건(55%)이다. 나머지는 시간 상한이 있어 극단적으로 느린 머신에서는 여전히 실패할 수 있으므로 "확률을 낮춘" 수정으로 분류됐다.
- 관찰 3 — 무부하에서 sleep 판이 더 느렸다(50회 3947~4041ms vs 1888~2052ms, 재실행 포함). sleep은 작업이 일찍 끝나도 50ms를 다 쉰다. SWE@G 11장도 sleep을 "속도 제한"으로 지목하고, 상태 전이를 짧은 주기로 폴링하라고 권한다.

### 4. JUnit 5의 실행 순서와 병렬 실행

JUnit 5.13.4 User Guide 2.11절·2.22절로 확인한 기본값이다.

| 항목 | 기본 동작 | 바꾸는 법 |
|---|---|---|
| 메서드·클래스 순서 | "deterministic but intentionally nonobvious" — 결정적이지만 일부러 드러나지 않는 알고리즘 | `@TestMethodOrder`, `junit.jupiter.testmethod.order.default` |
| 무작위 순서 시드 | `MethodOrderer.Random`의 기본 시드는 클래스 초기화 때의 `System.nanoTime()`, `CONFIG` 수준으로 로그에 남김(javadoc) | `junit.jupiter.execution.order.random.seed` |
| 병렬 실행 | 기본은 단일 스레드 순차 실행. 5.3부터 opt-in | `junit.jupiter.execution.parallel.enabled=true` + 실행 모드 |
| 반복 실행 | `@RepeatedTest(n)` — 5.10부터 `failureThreshold`(기본 `Integer.MAX_VALUE`) | `failureThreshold = 1`이면 첫 실패 뒤 나머지 건너뜀 |

- User Guide의 문장: 진짜 단위 테스트는 실행 순서에 기대지 않는 것이 보통이다("true unit tests typically should not rely on the order").
- 무작위 순서는 숨은 순서 의존을 **드러내는 도구**다. 시드를 로그에 남겨 두면 실패한 순서를 다시 재현할 수 있다.
- 병렬 실행을 켜면 새로운 공유 상태 경쟁이 드러난다. User Guide 2.22.2절은 공유 자원에 `@ResourceLock`을 쓰라고 안내한다.

### 5. 재시도는 무엇을 하고 무엇을 못 하나

```text
 rerunFailingTestsCount=3

 Run 1: FAIL ─┐
 Run 2: FAIL  ├─▶ 한 번이라도 PASS → "Flakes: 1", BUILD SUCCESS
 Run 3: PASS ─┘
                   빨강 신호가 사라진다. 결함은 그대로다.
```

- Maven Surefire의 `rerunFailingTestsCount`(문서 「Rerun Failing Tests」): 실패한 테스트를 통과하거나 횟수가 다할 때까지 다시 돌린다. 재실행으로 통과하면 **flaky로 세고 빌드는 성공**한다. 요약 줄에 `Flakes: N`이 붙는다.
- 같은 문서: 3.0.0-M6부터 `failOnFlakeCount`로 flaky 수가 기준을 넘으면 빌드를 실패시킬 수 있다.
- Google(Micco 2016)도 재실행·"3번 연속 실패해야 실패로 보고" 표시·자동 격리를 쓴다. 같은 글이 한계를 적는다.
  - 3번 연속 규칙은 개발자가 자기 테스트의 불안정성을 무시하게 만든다.
  - 15분짜리 통합 테스트라면 진짜 실패를 알기까지 45분이 걸린다.
  - 격리(quarantine)는 "진짜 경쟁 조건이나 다른 버그를 쉽게 가릴 수 있다(could easily mask a real race condition)".
- SWE@G 11장: 자동 재실행은 "CPU 시간을 엔지니어 시간과 바꾸는" 거래다. 불안정성이 낮을 때는 맞는 거래지만, 근본 원인을 고칠 시점을 미룰 뿐이다.

### 실험 C: 진짜 경쟁 조건 + 재시도 = BUILD SUCCESS

(실험, Maven 3.9.16 · surefire 3.5.3 · JUnit 5.13.4 · JDK 21.0.11(maven 이미지), `--cpus=2`, 2026-10-03)

```java
static class Counter { int count; void inc() { count++; } }   // 동기화 없음 — 제품 코드의 진짜 결함
@Test void twoThreadsCount() throws Exception {
  // 두 스레드가 출발선(CountDownLatch)에서 동시에 출발해 각각 N=1000번 inc()
  ...
  assertEquals(2 * N, c.count);
}
```

`mvn test -Dtest=RaceTest -Drace.n=1000`을 새 컨테이너에서 12번:

```text
      9 [ERROR] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0 [INFO] BUILD FAILURE
      3 [INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0 [INFO] BUILD SUCCESS
```

같은 명령에 `-Dsurefire.rerunFailingTestsCount=3`을 붙여 6번: 6번 모두 `BUILD SUCCESS`, 그중 4번이 `Flakes: 1`(사실 점검 재실행에서는 재시도 없이 12번 중 9번 실패로 같았고, 재시도 판은 6번 모두 `BUILD SUCCESS`·6번 모두 `Flakes: 1`이었다 — 실행마다 다르다). 한 번의 출력:

```text
[ERROR] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.250 s <<< FAILURE! -- in flaky.RaceTest
org.opentest4j.AssertionFailedError: expected: <2000> but was: <1607>
[ERROR] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.015 s <<< FAILURE! -- in flaky.RaceTest
org.opentest4j.AssertionFailedError: expected: <2000> but was: <1401>
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.009 s -- in flaky.RaceTest
[WARNING] Flakes: 
[ERROR]   Run 1: RaceTest.twoThreadsCount:13 expected: <2000> but was: <1607>
[ERROR]   Run 2: RaceTest.twoThreadsCount:13 expected: <2000> but was: <1401>
[INFO]   Run 3: PASS
[WARNING] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Flakes: 1
[INFO] BUILD SUCCESS
```

- 관찰 1 — 재시도 없이는 12번 중 9번 빌드가 깨졌다. 테스트는 제 일을 했다. 결함(동기화 없는 `count++`)이 실제로 있다.
- 관찰 2 — 재시도 3회를 켜자 6번 모두 빌드가 초록이 됐다(재실행 6번도 같음). 결함은 그대로인데 신호만 `[WARNING] Flakes`로 내려갔다.
- 관찰 3 — 재실행은 이미 데워진(JIT 컴파일된) 같은 JVM에서 돈다. 첫 실행보다 짧게 끝나 겹침이 줄어든다. 재시도 성공 확률은 "독립 시행"보다 높을 수 있다는 뜻이다. 이 해석은 실행 시간(0.250s → 0.009s)에서 나온 추정이다.

## 쓰이는 자료구조·알고리즘

- **비율 추정(베르누이 시행)**: 같은 커밋을 n번 돌려 k번 실패하면 실패율 추정은 k/n이다.
  - 0번 실패했다고 실패율이 0은 아니다. 통계의 "3의 규칙"으로 n번 모두 통과면 95% 신뢰 상한이 대략 3/n이다(예: 50번 모두 통과 → 약 6%까지는 배제 못 함).
  - 실패율 p인 테스트가 독립적으로 r번 재시도되면, 끝내 실패할 확률은 p^(r+1)이다. 실패율 0.5에 재시도 3회면 1/16만 빨강으로 남는다.
- **순열과 시드 기반 의사난수**: 테스트 n개의 순서는 n!가지다. 시드를 고정하면 같은 순열을 다시 만든다(실험 A의 시드 1~20).
- **오염자 찾기 = 이분 탐색**: 피해자 V가 전체 실행에서만 실패한다면, V 앞에 돈 테스트 목록을 반으로 나눠 "앞 절반 + V"를 돌린다. 실패하는 쪽 절반으로 범위를 줄인다. 오염자가 하나면 log₂(n)번 안팎으로 좁혀진다.
- **조건 대기(waitFor)와 래치**: 고정 시간 대신 상태 조건을 기다린다. `CountDownLatch`·`Future.get(timeout)`·폴링 + 상한(JUnit `@Timeout`, Awaitility).
- **해시 순회 순서**: `HashSet`·`HashMap` 순회 순서는 명세가 보장하지 않는다. 순서 없는 비교(`containsExactlyInAnyOrder`)나 정렬 후 비교로 바꾼다.

## 적용 — 풀어나가는 법

### 1. 재현한다 — 같은 커밋, 여러 번

```java
@RepeatedTest(value = 200, failureThreshold = 1)   // JUnit 5.10+: 첫 실패에서 나머지 건너뜀
void reportIsReady() throws Exception { ... }
```

```bash
# 순서 의존 의심: 무작위 순서 + 시드 고정으로 재현
mvn test -Djunit.jupiter.testmethod.order.default='org.junit.jupiter.api.MethodOrderer$Random' \
         -Djunit.jupiter.execution.order.random.seed=7
# 재시도가 켜진 CI라면 "Flakes"를 실패처럼 모은다
grep -h "Flakes" target/surefire-reports/*.txt
```

- 로컬에서 재현이 안 되면 CI 조건을 흉내 낸다. CPU를 줄이고(`docker run --cpus=1`), 병렬 실행을 켜고, 다른 테스트와 함께 돌린다. 실험 B처럼 부하가 실패율을 바꾼다.

### 2. 분류한다 — 숨은 입력이 무엇인가

```text
 실패 메시지·스택을 보고
  ├─ 타임아웃·null·"아직 없음"            → Async Wait (대기 방식)
  ├─ 값이 조금 모자람·교착·ConcurrentModification → Concurrency
  ├─ 단독 실행은 통과, 전체 실행에서만 실패  → Test Order Dependency (공유 상태)
  ├─ 특정 날짜·시각에만                     → Time (10번 노트)
  ├─ 연결 거부·포트 사용 중                 → Network / 외부 자원
  └─ 순서만 다른 같은 원소                  → Unordered Collections
```

### 3. 근본 원인을 고친다

| 원인 | 고치는 방향 (Java) |
|---|---|
| 비동기 대기 | `Thread.sleep` → `future.get(5, SECONDS)`·`CountDownLatch.await(…)`·Awaitility `await().atMost(…).until(…)` |
| 순서 의존(메모리) | `@BeforeEach`에서 초기화, 정적 가변 상태 제거, 테스트마다 새 객체 |
| 순서 의존(외부) | `@TempDir`, 테스트마다 고유 DB 스키마·키 접두사, 포트 0(OS가 빈 포트 배정) |
| 시간 | `Clock` 주입 → [10](../10-testing-time-and-concurrency/2-summary.md) |
| 동시성 | 제품 코드의 동기화 결함을 고친다(Luo F.12: 수정의 24%가 제품 코드도 고침) |
| 난수 | 시드 고정 또는 생성 범위 전체를 기대값이 감당하게 |
| 순서 없는 컬렉션 | AssertJ `containsExactlyInAnyOrder`, 정렬 후 비교 |

```java
// 외부 자원 격리: 고정 포트·고정 경로 대신
@Test void writesReport(@TempDir Path dir) throws Exception {
  try (var server = new ServerSocket(0)) {             // 0 = OS가 빈 포트를 고른다
    int port = server.getLocalPort();
    ...
  }
}
```

### 4. 격리(quarantine)는 기한을 두고 쓴다

- Fowler "Eradicating Non-Determinism in Tests"(2011): 불안정 테스트를 주 스위트에서 빼 격리 스위트로 옮긴다. 격리가 쌓이지 않게 상한을 둔다 — 예로 "격리에는 8개까지" 또는 "격리 기간 최대 1주".
- Google(Micco 2016): 불안정성이 높은 테스트를 도구가 자동 격리하고 **버그를 등록**한다.
- 격리 = 주 경로에서 뺌 + 담당자 + 기한. 셋 중 하나라도 없으면 사실상 삭제다.

### 5. 들어오는 입구에서 막는다

- Luo F.2·I.2: 불안정 테스트의 78%가 처음부터 불안정했다. 논문은 테스트가 처음 추가될 때 집중적으로 검사하는 기법이 대부분을 잡을 수 있다고 제안한다.
- 실무 구현(이 노트의 제안): 새로 추가·수정된 테스트만 골라 머지 전에 반복 실행(`@RepeatedTest`·CI 반복 잡)과 무작위 순서 실행을 돌린다.
- SWE@G 11장의 작은 테스트(small test) 제약 — 한 프로세스, sleep·I/O·블로킹 호출 금지 — 도 불안정성의 주요 원천을 막기 위한 장치라고 설명한다.

## 장애 시나리오와 대처

### 1. 재시도로 덮기 → 진짜 경쟁 조건 은폐 (⚠ 커리큘럼)

- 현상: CI는 몇 달째 초록이다. 운영에서는 가끔 집계값이 모자란다.
- 보이는 형태: surefire 요약의 `[WARNING] Tests run: …, Flakes: 1`. 운영 지표에서 합계 불일치·중복 처리가 드문드문 보인다.
- 원인: 동기화 없는 공유 상태라는 제품 결함이 테스트를 불안정하게 만들었다. 재시도 설정이 그 신호를 경고로 낮췄다(실험 C: 재시도 없이 12번 중 9번 실패 → 재시도 3회로 6번 모두 성공).
- 대처: `Flakes`를 실패처럼 수집해 담당자에게 보낸다. `failOnFlakeCount`(surefire 3.0.0-M6+)로 상한을 건다. 불안정 테스트를 고칠 때 제품 코드 결함부터 의심한다(Luo F.12).

### 2. CI 신뢰 붕괴 — 빨강을 아무도 안 본다 (⚠ 커리큘럼)

- 현상: 빨강이 떠도 "재실행"이 첫 반응이다. 진짜 회귀가 머지된다.
- 보이는 형태: 재실행 버튼 클릭 수·같은 커밋 재빌드 수가 늘어난다. 통과→실패 전이 중 불안정 테스트가 낀 비율이 높다(Google 2016에서 약 84%).
- 원인: 불안정 비율이 쌓였다. SWE@G 11장은 1%에 가까워지면 테스트가 가치를 잃기 시작한다고 적는다.
- 대처: 테스트별 불안정 비율을 측정해 상위부터 고친다. 기한 있는 격리. 새 테스트 입구 검사(반복·무작위 순서).

### 3. 테스트 하나 추가했더니 다른 테스트가 깨진다

- 현상: 손대지 않은 `OrderServiceTest`가 내 PR에서 실패한다. 단독으로 돌리면 통과한다.
- 보이는 형태: IDE에서 단일 실행은 초록, `mvn test` 전체는 빨강.
- 원인: 새 테스트가 오염자이거나, 순서가 바뀌어 기존 오염자가 피해자 앞으로 왔다(실험 A 관찰 1, Luo 3.2절).
- 대처: 이분 탐색으로 오염자를 찾는다. 정적 가변 상태·공유 파일·DB 행을 테스트마다 초기화한다.

### 4. 로컬은 초록, CI에서만 가끔 실패

- 현상: 개발 노트북에서는 100번 돌려도 통과한다. CI에서는 하루 몇 번 실패한다.
- 보이는 형태: `expected: not <null>`·타임아웃·"element not found"류 메시지. 실패가 CI 혼잡 시간대에 몰린다.
- 원인: 고정 sleep 같은 시간 가정이 느린·바쁜 러너에서 깨진다(실험 B: 부하 4개에서 50번 중 30~32번 실패).
- 대처: sleep을 조건 대기로 바꾸고 상한은 넉넉히 둔다. sleep 시간을 늘리는 것은 확률만 낮춘다(Luo 5.1.1).

### 5. 병렬 실행을 켰더니 무작위로 실패

- 현상: 빌드 시간을 줄이려고 `junit.jupiter.execution.parallel.enabled=true`를 켰다. 서로 다른 테스트가 번갈아 실패한다.
- 보이는 형태: 포트 사용 중(`BindException`), 같은 파일·같은 DB 행 충돌.
- 원인: 순차 실행에서 드러나지 않던 외부 자원 공유가 동시에 일어난다.
- 대처: `@ResourceLock`으로 공유 자원을 표시하거나, 자원을 테스트마다 분리한다(포트 0, `@TempDir`, 테스트별 스키마).

## 핵심 문장

- 불안정 테스트는 테스트가 통제하지 않는 숨은 입력(스케줄·순서·시각·네트워크·난수·머신 속도)이 결과를 흔드는 것이다.
- Luo 외(2014)가 분류한 161건 중 비동기 대기 45%, 동시성 20%, 순서 의존 12%였고, 고친 커밋의 24%는 제품 코드를 고쳤다.
- 고정 sleep을 늘리는 수정은 실패 확률만 낮춘다. 조건을 기다리는 수정은 원인을 없애는 경우가 많다(Luo: waitFor 수정 42건 중 23건) — 시간 상한이 있으면 아주 느린 머신에서는 여전히 실패할 수 있다.
- 재시도는 빨강 신호를 경고로 낮출 뿐이다. 재시도로 통과한 테스트도 실패처럼 수집하고, 격리는 담당자와 기한을 붙여 쓴다.
- 무작위 순서와 반복 실행은 숨은 의존을 드러내는 도구이고, 시드를 남겨야 재현할 수 있다.

## 관련 주제·근거

- 선행·연결
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) — 실제 의존을 쓰는 테스트일수록 외부 자원 불안정성이 커진다
  - [10-testing-time-and-concurrency](../10-testing-time-and-concurrency/2-summary.md) — 시간·동시성 원인의 상세 처방
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) — `count++`가 왜 깨지나
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) — 재시도는 일시적 장애용이다. 결정적 결함에는 효과가 없다
  - [software-design/25-dependency-injection-and-composition-root](../../software-design/25-dependency-injection-and-composition-root/2-summary.md) — 숨은 입력(시계·난수)을 주입으로 드러내기
- 후속(AI 엔지니어링): [ai-engineering/07-decoding-and-nondeterminism](../../ai-engineering/07-decoding-and-nondeterminism/2-summary.md) — temperature 0 스냅샷 테스트의 간헐 실패
- 논문·문서
  - Qingzhou Luo, Farah Hariri, Lamyaa Eloussi, Darko Marinov, "An Empirical Analysis of Flaky Tests", FSE 2014 — 표 1(발견 F.1~F.12), 3.1절(161건 분류), 3.2절(도입 시점), 4.2.3절(순서 의존 출처), 5.1.1절(수정 방식) <https://mir.cs.illinois.edu/lamyaa/publications/fse14.pdf>
  - John Micco, "Flaky Tests at Google and How We Mitigate Them", Google Testing Blog, 2016-05-27 <https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html>
  - Titus Winters·Tom Manshreck·Hyrum Wright 편, 『Software Engineering at Google』, O'Reilly 2020 — 11장 「Testing Overview」(작은 테스트 제약, Case Study: Flaky Tests Are Expensive, sleep 대신 폴링), 13장 「Test Doubles」(Determinism), 14장 「Larger Testing」(Driving out flakiness) <https://abseil.io/resources/swe-book>
  - Martin Fowler, "Eradicating Non-Determinism in Tests", 2011 <https://martinfowler.com/articles/nonDeterminism.html>
  - JUnit 5.13.4 User Guide 2.11 「Test Execution Order」, 2.16 「Repeated Tests」, 2.21 「Timeouts」, 2.22 「Parallel Execution」 <https://docs.junit.org/5.13.4/user-guide/index.html>; `MethodOrderer.Random` javadoc(기본 시드·설정 키)
  - Maven Surefire, "Rerunning Failing Tests" <https://maven.apache.org/surefire/maven-surefire-plugin/examples/rerun-failing-tests.html>
  - Awaitility Usage(기본 상한 10초, 폴링 간격 100ms) <https://github.com/awaitility/awaitility/wiki/Usage>
- 실험 목록(코드: `scratchpad/ts/09/e09/`, 환경: Docker `--cpus=2`, 2026-10-03)
  - A — 공유 정적 상태 순서 의존. `CartOrderTest`·`CartOrderFixedTest`·`RunMany.java`(JUnit Launcher로 기본 순서 1번 + `MethodOrderer.Random` 시드 1~20). `java -cp target/test-classes:<cp> flaky.RunMany order`(eclipse-temurin:21-jdk, JDK 21.0.12).
  - B — 고정 sleep vs 조건 대기. `AsyncSleepTest`·`AsyncWaitTest`·`Work.java`. `RunMany async <부하 스레드 수>`를 0·2·4로 각 2번(사실 점검에서 각 3번 더).
  - C — 동기화 없는 카운터 + surefire 재시도. `RaceTest.java`. `mvn test -Dtest=RaceTest -Drace.n=1000`(12번) / `… -Dsurefire.rerunFailingTestsCount=3`(6번), maven:3.9-eclipse-temurin-21(Maven 3.9.16, JDK 21.0.11, surefire 3.5.3).
