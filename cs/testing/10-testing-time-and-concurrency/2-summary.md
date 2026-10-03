# testing/10-testing-time-and-concurrency — 시계 주입·결정적 스케줄러·동시성 테스트 — 정리 (힌트)

## 해결하는 문제

쉬운 예부터 보자.

- 10분 뒤 울리는 요리 타이머를 시험하려고, 실제로 10분을 서서 기다린다.
- "생일에만 축하 문구가 뜬다"를 확인하려면 생일까지 기다려야 한다.
- 둘이 동시에 마지막 쿠키를 집는 상황을 보려고, 둘이 손을 뻗는 타이밍을 운에 맡긴다.

똑같은 구조다.

- 코드가 `LocalDate.now()`·`Instant.now()`로 시계를 **직접** 읽는다. 테스트는 "오늘"만 시험할 수 있다.
- 만료·재시도·타임아웃을 `Thread.sleep`으로 기다린다. 테스트가 느리고, 바쁜 머신에서는 깨진다([09](../09-flaky-tests/2-summary.md) 실험 B).
- 동시성 버그는 스레드 스케줄이 맞아떨어질 때만 드러난다. 몇 번 돌려 통과했다고 안전한 것이 아니다.

실무 예:

- 월말 정산·말일 청구가 30일까지인 달에만 틀린다.
- 세션 만료(30분)·토큰 만료(1시간) 테스트가 실제로 30분을 기다리거나, 아예 없다.
- 재시도 백오프(1초·2초·4초)를 시험하면 테스트 하나가 7초다.
- "없으면 만든다(getOrCreate)"가 동시 요청에서 두 번 만든다.

이 노트의 답은 세 가지다.

1. 시간을 **입력**으로 만든다 — `Clock` 주입.
2. 기다림을 **가상 시간**으로 바꾼다 — 가짜 시계·수동 스케줄러.
3. 동시성은 **출발선으로 겹치게** 하고, 필요하면 **이음새로 순서를 강제**한다.

## 동작·원리

### 1. 시간은 숨은 입력이다

```text
 숨은 입력                                   드러난 입력
 ┌──────────────────────┐                  ┌──────────────────────────┐
 │ isBillingDay(day)    │                  │ isBillingDay(day, clock) │  또는 생성자에 Clock
 │   LocalDate.now() ◀──┼── 시스템 시계     │   LocalDate.now(clock) ◀─┼── 테스트가 넘긴 시계
 └──────────────────────┘   (테스트가 못 바꿈) └──────────────────────────┘   (2026-04-30 고정)
```

- 시그니처에 안 보이는 입력은 테스트가 통제할 수 없다. 결과가 "언제 돌렸나"에 따라 달라진다.
- Java `Clock` javadoc(Java SE 21)이 이 목적을 직접 적는다.
  - "The primary purpose of this abstraction is to allow alternate clocks to be plugged in as and when required. Applications use an object to obtain the current time rather than a static method. This can simplify testing."
  - "Best practice for applications is to pass a `Clock` into any method that requires the current instant and time-zone. A dependency injection framework is one way to achieve this."
- SWE@G 13장 「Determinism」: 시스템 시계에 기대는 코드는 현재 시각에 따라 출력이 다르다. 대신 특정 시각을 하드코딩한 테스트 더블을 쓸 수 있다.
- 주입 방법(생성자 주입·조립 지점)은 [software-design/25](../../software-design/25-dependency-injection-and-composition-root/2-summary.md)에 있다. 이 노트는 테스트 쪽을 다룬다.

### 2. 테스트용 시계 세 가지

| 종류 | 만드는 법 | 쓰는 곳 |
|---|---|---|
| 고정 시계 | `Clock.fixed(instant, zone)` — javadoc: "always returns the same instant", "The main use case for this is in testing" | 특정 날짜·시각의 판정(말일, DST 전날) |
| 오프셋 시계 | `Clock.offset(base, duration)` | "지금부터 3일 뒤" 같은 상대 시점 |
| 가변(수동) 시계 | `Clock`을 상속해 `advance(Duration)`을 둔다(표준 라이브러리에 없음) | 만료·타임아웃처럼 **시간이 흐르는** 동작 |

- *가변 시계(mutable clock)*: 테스트가 손으로 앞으로 돌리는 시계. 실제 시간은 흐르지 않는다.
- `Clock` javadoc: 구현은 스레드 안전해야 한다("All implementations must be thread-safe"). 직접 만든 가변 시계를 여러 스레드가 읽으면 이 요구를 지켜야 한다. 아래 실험의 가변 시계는 단일 스레드 테스트용이라 동기화를 넣지 않았다.

```java
// 단일 스레드 테스트용 가변 시계
class MutableClock extends Clock {
  private Instant now; private final ZoneId zone;
  MutableClock(Instant start, ZoneId zone) { this.now = start; this.zone = zone; }
  void advance(Duration d) { now = now.plus(d); }
  public Instant instant() { return now; }
  public ZoneId getZone() { return zone; }
  public Clock withZone(ZoneId z) { return new MutableClock(now, z); }
}
```

### 실험 A: 자정 — 코드와 테스트가 시계를 따로 읽는다

(실험, JDK 21.0.12 temurin, `--cpus=2`, 2026-10-03, `java TimeConc.java`)

```java
record Order(LocalDate createdOn) { static Order create(Clock c) { return new Order(LocalDate.now(c)); } }
// 읽을 때마다 1ms씩 흐르는 시계로 "두 번 읽는 사이 시간이 흐른다"를 흉내 낸다
Order o = Order.create(clock);                 // 운영 코드가 한 번 읽고
LocalDate expected = LocalDate.now(clock);     // 테스트가 또 읽는다(1ms 뒤)
```

```text
A. 자정
  시작 2026-10-03T12:00:00 → createdOn=2026-10-03, 테스트 기대=2026-10-03 → PASS
  시작 2026-10-03T23:59:59.999 → createdOn=2026-10-03, 테스트 기대=2026-10-04 → FAIL
```

- 기대값을 `LocalDate.now()`로 **다시 계산**하는 테스트는, 두 읽기 사이에 자정이 끼면 실패한다. 실제 시스템 시계라면 "자정 근처에 돈 CI"에서만 드물게 깨진다.
- 처방: 시계를 고정하고 기대값을 리터럴로 적는다(`assertEquals(LocalDate.of(2026, 10, 3), o.createdOn())`).

### 실험 B: 고정 시계로 1년을 훑는다 — 월말과 DST

(같은 실행)

```java
static LocalDate dueDate(Clock c) { return LocalDate.now(c).plusMonths(1); }   // "다음 달 같은 날"
for (LocalDate d = LocalDate.of(2026,1,1); d.getYear() == 2026; d = d.plusDays(1)) {
  Clock fixed = Clock.fixed(d.atTime(9,0).atZone(seoul).toInstant(), seoul);
  if (dueDate(fixed).getDayOfMonth() != d.getDayOfMonth()) bad.add(d);   // 테스트의 기대: 같은 '일'
}
// DST: 09:00 기준 now.plusHours(24) 와 now.plusDays(1) 가 다른 날
```

```text
B. 월말·DST
  '다음 달 같은 날' 기대가 깨지는 날 7일: [2026-01-29, 2026-01-30, 2026-01-31, 2026-03-31, 2026-05-31, 2026-08-31, 2026-10-31]
  America/New_York: plusHours(24) != plusDays(1) 인 날 [2026-03-07, 2026-10-31]
  Asia/Seoul: plusHours(24) != plusDays(1) 인 날 []
  2026-03-08 02:30 America/New_York 생성 → 2026-03-08T03:30-04:00[America/New_York]
```

- 관찰 1 — `plusMonths(1)`은 다음 달에 그 날이 없으면 말일로 맞춘다(1월 31일 → 2월 28일). "같은 일자"를 기대한 테스트는 2026년 365일 중 7일만 실패한다. 10월 3일에 짠 테스트는 초록이다.
- 관찰 2 — 뉴욕에서 "24시간 뒤"와 "하루 뒤"가 갈리는 날은 DST 전날 2일뿐이다(2026년 DST 시작 3월 8일, 끝 11월 1일). 서울은 DST가 없어 0일이다. **서울에서 돌린 테스트는 이 결함을 볼 수 없다.**
- 관찰 3 — 없는 시각(3월 8일 02:30)으로 `ZonedDateTime`을 만들면 예외 없이 03:30으로 밀린다. `java.time`의 규칙이고, 기대값이 02:30이면 그날만 깨진다. DST 규칙 자체는 [domain-modeling/13](../../domain-modeling/13-instant-vs-local-time-and-tz-rules/2-summary.md)에 있다.
- 고정 시계는 1년 365일을 밀리초 단위 시간에 훑게 해 준다. 경계 날짜를 사람이 떠올리지 못해도 전수로 찾는다.

### 3. sleep 대신 가상 시간

```text
 sleep 테스트                         가짜 시계 테스트
 put("k") ── 실제 2.1초 대기 ── get    put("k") ─ advance(1999ms) ─ get=살아있음 ─ advance(1ms) ─ get=만료
            (경계 1999/2000ms 못 봄)                  실제로는 몇 ms
```

### 실험 C: TTL 캐시 — sleep 판 vs 가짜 시계 판

(같은 실행. 범위는 집필 3번 + 사실 점검 재실행 4번, 총 7번)

```java
class TtlCache {
  TtlCache(Clock c, Duration ttl) { ... }
  String get(String k) { Instant t = at.get(k);
    if (t == null || !clock.instant().isBefore(t.plus(ttl))) return null; return v.get(k); }
}
```

```text
C. TTL
  sleep 판: 만료 확인=true, 2101ms
  가짜 시계 판: 1999ms 살아있음=true, 2000ms 만료=true, 2.61ms
```

- sleep 판은 7번 모두 2101ms였다. 가짜 시계 판은 1.23~2.61ms였다.
- 차이는 속도만이 아니다. 가짜 시계 판은 **경계**(1999ms 살아 있음, 2000ms 만료)를 정확히 찍는다. sleep 판은 "2.1초 뒤 만료됐다"만 안다. 그래서 만료 조건을 `!now.isBefore(exp)`(now ≥ exp)에서 `now.isAfter(exp)`(now > exp)로 바꿔 **정확히 2000ms에 아직 살아 있게** 만든 경계 결함은 sleep 판이 못 잡는다. 반면 `isBefore`를 `isAfter`로 단순 치환한 `!now.isAfter(exp)`는 의미가 통째로 뒤집히므로 sleep 판도 잡는다. 아래는 세 판을 나란히 돌린 결과다.

(실험, JDK 21.0.12 temurin, 2026-10-03, 1회 — 코드 `scratchpad/ts/adj-09/e10/TtlVariants.java`, 같은 캐시에 만료 판정만 바꿔 끼움)

```text
원본  !now.isBefore(exp) | sleep 판(2100ms 뒤 null?)=PASS | 가짜 시계 판 1999ms 살아있음=true, 2000ms 만료=true → PASS
변형1 !now.isAfter(exp)  | sleep 판(2100ms 뒤 null?)=FAIL | 가짜 시계 판 1999ms 살아있음=false, 2000ms 만료=true → FAIL
변형2 now.isAfter(exp)   | sleep 판(2100ms 뒤 null?)=PASS | 가짜 시계 판 1999ms 살아있음=true, 2000ms 만료=false → FAIL
```

- 변형2(경계 1칸 밀림)는 sleep 판을 통과하고 가짜 시계 판의 2000ms 단언에서만 걸린다.

### 4. 결정적 스케줄러 — 가상 시간 위의 이산 사건 시뮬레이션

```text
 ManualScheduler (가상 시각 now=0)
   대기열(마감 시각 순 우선순위 큐):  [due=100 retry#2]
   advanceBy(99)  → now=99, 마감 지난 작업 없음
   advanceBy(1)   → now=100, retry#2 실행 → 실패 → [due=300 retry#3] 등록
   advanceBy(600) → 300에 retry#3 실행 → [due=700 retry#4] → 700에 실행 → 성공
```

- *결정적 스케줄러(deterministic scheduler)*: 작업을 실제 스레드·실제 시간 대신, 테스트가 시각을 진행시킬 때만 마감 순서대로 실행하는 가짜 실행기.
- 같은 마감 시각이면 등록 순서(일련번호)로 실행한다. 그래서 실행 순서가 매번 같다.
- 운영 코드는 `Scheduler` 인터페이스에 의존하고, 운영에서는 `ScheduledExecutorService`, 테스트에서는 수동 구현을 주입한다.

### 실험 D: 재시도 백오프 100·200·400ms — 실제 vs 수동 스케줄러

(같은 실행. 범위는 집필 3번 + 사실 점검 재실행 4번, 총 7번)

```java
interface Scheduler { void schedule(Runnable r, Duration delay); }
class ManualScheduler implements Scheduler {
  record Task(long due, long seq, Runnable r) {}
  final PriorityQueue<Task> q = new PriorityQueue<>(Comparator.comparingLong(Task::due).thenComparingLong(Task::seq));
  long now = 0, seq = 0;
  public void schedule(Runnable r, Duration d) { q.add(new Task(now + d.toMillis(), seq++, r)); }
  void advanceBy(Duration d) { long end = now + d.toMillis();
    while (!q.isEmpty() && q.peek().due() <= end) { Task t = q.poll(); now = t.due(); t.r().run(); }
    now = end; }
}
```

```text
D. 백오프
  실제 스케줄러: [실패#1→100ms 뒤, 실패#2→200ms 뒤, 실패#3→400ms 뒤, 성공#4], 744ms
  수동 스케줄러: 99ms 시점 [실패#1→100ms 뒤] | 100ms 시점 [실패#1→100ms 뒤, 실패#2→200ms 뒤] | 700ms 시점 [실패#1→100ms 뒤, 실패#2→200ms 뒤, 실패#3→400ms 뒤, 성공#4], 8.24ms
```

- 실제 스케줄러: 723~744ms. 수동 스케줄러: 6.12~11.46ms(이 시간 대부분은 첫 실행의 클래스 로딩이다 — 추정).
- 수동 판은 "99ms에는 아직 재시도 안 함, 100ms에 재시도"를 단언할 수 있다. 실제 판으로 이것을 확인하려면 타이밍 허용 오차를 둬야 하고, 그 허용 오차가 불안정성의 씨앗이 된다.
- 백오프가 1·2·4초라면 실제 판은 7초 이상이다. 수동 판은 백오프 길이와 무관하게 짧다.

### 5. 동시성 테스트 — 세 겹

```text
 (a) 스트레스: 출발선 + 반복          (b) 강제 끼어들기: 이음새 + 래치        (c) 체계적 탐색(도구)
 T1 ─┐ go.await()                     T1: check ✔ ─▶ [hook: 멈춤] ······ act      jcstress: 스트레스 하네스
 T2 ─┤  ──▶ 동시에 출발 ×N회           T2:        check ✔ ─▶ act                   Lincheck: 모델 체킹
 T3 ─┘                                 → 나쁜 순서를 1번에 100% 재현            (인터리빙을 체계적으로)
```

- *출발선(start gate)*: 모든 스레드가 `CountDownLatch`에서 기다리다가 한 번에 출발하게 하는 장치. 스레드 생성 시간 차이 때문에 겹치지 않는 문제를 줄인다.
- *강제 끼어들기*: 경쟁 구간 사이(check와 act 사이)에 테스트용 훅을 두고, 래치로 "T1이 check 뒤에 멈춘 사이 T2가 끝까지 돈다"는 순서를 만든다. 결정적이다.
  - 이 훅은 운영에서는 아무 일도 안 하는 이음새(seam)다. 이음새 개념은 [17](../17-characterization-tests-legacy/2-summary.md)·[software-design/51](../../software-design/51-legacy-change-techniques/2-summary.md)에 있다.
- 도구(문서 확인 범위):
  - OpenJDK jcstress — "JVM, 클래스 라이브러리, 하드웨어의 동시성 지원 정확성 연구를 돕는 실험적 하네스와 테스트 모음"(README).
  - JetBrains Lincheck — JVM 동시성 자료구조가 기본으로 선형화 가능성(linearizability)을 지키는지 검사한다. 무작위 시나리오를 반복하는 스트레스 모드와, 제한된 범위의 인터리빙을 체계적으로 탐색하는 모델 체킹 모드가 있다. 실패하면 재현 가능한 실행 흔적을 낸다(README).

### 실험 E: check-then-act — 출발선 유무와 강제 끼어들기

(같은 실행. 범위는 집필 3번 + 사실 점검 재실행 4번, 총 7번. 실행마다 다르다)

```java
Object getOrCreate(String k) {
  if (!m.containsKey(k)) { betweenCheckAndAct.run(); created.incrementAndGet(); m.put(k, new Object()); }
  return m.get(k);
}
Object getOrCreateFixed(String k) { return m.computeIfAbsent(k, x -> { created.incrementAndGet(); return new Object(); }); }
// 시행 1번 = 스레드 4개가 같은 키로 한 번씩 호출, created > 1 이면 "중복 생성"
```

```text
E. 경쟁
  출발선=false, 고친판=false: 2000회 중 중복 생성 78회
  출발선=true, 고친판=false: 2000회 중 중복 생성 213회
  출발선=true, 고친판=true: 2000회 중 중복 생성 0회
  강제 끼어들기(이음새로 순서 고정): created=2
```

| 조건 | 2000회 중 중복 생성(7번 실행 범위) |
|---|---|
| 출발선 없음 | 55~96 |
| 출발선 있음 | 169~243 |
| 출발선 있음 + `computeIfAbsent` | 0 (7번 모두) |
| 강제 끼어들기 | 1번 시행에서 `created=2` (7번 모두) |

- 관찰 1 — 출발선만 넣어도 결함 노출이 약 1.8~3.4배 늘었다(같은 실행끼리 비교 — 집필: 213/78, 190/80, 186/55, 사실 점검 재실행: 173/92, 243/89, 215/75, 169/96). 배율 자체는 실행마다 크게 흔들린다. 스레드를 순서대로 `start()`하면 앞 스레드가 먼저 끝나 겹침이 줄어든다.
- 관찰 2 — 출발선이 있어도 2000번 중 약 8~12%만 드러났다. 몇십 번 돌려 통과한 동시성 테스트는 거의 아무것도 증명하지 않는다.
- 관찰 3 — 강제 끼어들기는 한 번에 결함을 재현했다. 대신 "어디서 끼어들지"를 사람이 알아야 한다. 스트레스는 모르는 곳을 찾고, 강제 끼어들기는 아는 곳을 확정한다.
- 관찰 4 — `ConcurrentHashMap.computeIfAbsent`로 고친 판은 14000번(7번×2000) 중 0번이었다. 0번은 "안전 증명"이 아니라 이 조건에서 안 보였다는 뜻이다. 근거는 `ConcurrentHashMap.computeIfAbsent`의 명세다(Java SE 21 javadoc: "The entire method invocation is performed atomically" — 키가 없을 때 함수는 그 호출에서 정확히 한 번, 있으면 한 번도 불리지 않는다).

## 쓰이는 자료구조·알고리즘

- **가짜 시계 = 가변 `Instant` 하나**: `instant()`는 필드를 돌려주고 `advance()`는 더한다. 상태가 하나라 동작이 결정적이다.
- **우선순위 큐(이진 힙) + 일련번호**: 수동 스케줄러는 (마감 시각, 등록 순서) 순으로 꺼낸다. 삽입·꺼내기 O(log n). 같은 마감에서 FIFO를 지켜 순서가 매번 같다. 이것이 이산 사건 시뮬레이션의 기본 구조다.
- **전수 탐색(시간 축)**: 고정 시계로 1년 365일 × 관심 시각을 훑는다. 경계(말일·윤일·DST 전환일)를 떠올리지 못해도 찾는다. 테스트 설계 기법의 경계값 분석([07](../07-test-design-techniques/2-summary.md))을 시간 축에 적용한 것이다.
- **래치·배리어**: `CountDownLatch`(한 번 열리는 문)로 출발선과 강제 순서를 만든다.
- **인터리빙 수의 폭발**: 두 스레드가 각각 m·n개 원자 단계를 가지면 가능한 끼어들기 순서는 C(m+n, n)개다(예시: m=n=10이면 184,756). 무작위 스트레스는 그중 일부만 본다. 모델 체킹 도구는 범위를 제한해 체계적으로 훑는다.

## 적용 — 풀어나가는 법

### 1. 숨은 시간 입력을 찾는다

```bash
# 시계·sleep 직접 사용 (예시 패턴)
grep -rnE 'LocalDate(Time)?\.now\(\)|Instant\.now\(\)|System\.currentTimeMillis\(\)|new Date\(\)' src/main/java
grep -rn 'Thread\.sleep' src/test/java | wc -l
```

### 2. `Clock`을 주입하고, 테스트에서 고정·가변 시계를 넘긴다

```java
@Configuration class TimeConfig { @Bean Clock clock() { return Clock.system(ZoneId.of("Asia/Seoul")); } }

class BillingService {
  private final Clock clock;
  BillingService(Clock clock) { this.clock = clock; }
  boolean isBillingDay(int day) {
    LocalDate d = LocalDate.now(clock);
    return d.getDayOfMonth() == Math.min(day, d.lengthOfMonth());   // 그 날이 없으면 말일
  }
}

@ParameterizedTest
@CsvSource({ "2026-04-30, 31, true", "2026-02-28, 31, true", "2026-02-27, 31, false", "2028-02-29, 30, true" })
void billingDayFallsBackToMonthEnd(LocalDate today, int day, boolean expected) {
  Clock fixed = Clock.fixed(today.atStartOfDay(ZoneId.of("Asia/Seoul")).toInstant(), ZoneId.of("Asia/Seoul"));
  assertEquals(expected, new BillingService(fixed).isBillingDay(day));
}
```

### 3. 시간 경계 체크리스트 — 고정 시계로 각각 한 번

| 경계 | 예 |
|---|---|
| 자정 직전·직후 | 23:59:59.999 / 00:00 |
| 말일 | 1·3·5·8·10월 31일(다음 달에 그 날 없음), 2월 28·29일 |
| 윤년 | 2028-02-29 |
| DST 전날·당일 | DST 있는 지역(예: America/New_York 3월·11월) |
| 연말 | 12-31 → 01-01, 주차 계산 |
| 시간대 | 같은 Instant의 서울·UTC 날짜가 다른 시각(UTC 15:00~24:00) |

### 4. 기다림은 신호로, 시간 흐름은 가상 시간으로

- 비동기 결과: `future.get(timeout)`, `CountDownLatch.await(timeout)`, Awaitility `await().atMost(5, SECONDS).until(...)`(Awaitility 문서: 기본 상한 10초, 기본 폴링 간격 100ms). 폴링 상한은 실패 시 진단 시간이고, 통과 시에는 조건이 맞는 즉시 끝난다.
- 만료·백오프·주기 작업: `Scheduler`·`Clock`을 주입하고, 테스트는 `advanceBy`로 진행한다.
- 가짜 스케줄러는 실제 실행기의 계약을 흉내 내야 한다. 예: `ScheduledExecutorService.scheduleAtFixedRate` javadoc — 작업이 예외를 던지면 "이후 실행은 억제된다(Subsequent executions are suppressed)". 가짜가 이것을 무시하면 운영에서만 주기 작업이 멈춘다.

### 5. 동시성 테스트

```java
@RepeatedTest(200)
void getOrCreateIsAtomic() throws Exception {
  Registry r = new Registry();
  int n = 8; CountDownLatch go = new CountDownLatch(1); ExecutorService ex = Executors.newFixedThreadPool(n);
  List<Future<Object>> fs = new ArrayList<>();
  for (int i = 0; i < n; i++) fs.add(ex.submit(() -> { go.await(); return r.getOrCreate("k"); }));
  go.countDown();
  Set<Object> distinct = Collections.newSetFromMap(new IdentityHashMap<>());
  for (Future<Object> f : fs) distinct.add(f.get(5, TimeUnit.SECONDS));
  ex.shutdown();
  assertEquals(1, distinct.size());   // 불변식: 모두 같은 객체를 받는다
}
```

- 단언은 "결과 값"보다 **불변식**(같은 객체 하나, 합계 보존, 음수 재고 없음)으로 쓴다.
- 알려진 위험 구간은 이음새 + 래치로 강제 끼어들기 테스트를 하나 더 둔다(실험 E).
- 자료구조 수준의 정확성은 Lincheck·jcstress 같은 전용 도구에 맡긴다.

## 장애 시나리오와 대처

### 1. `Thread.sleep` 기반 테스트 → 느리고 불안정 (⚠ 커리큘럼)

- 현상: 테스트 스위트가 몇 분씩 늘었다. 바쁜 CI에서 가끔 실패한다.
- 보이는 형태: 테스트 실행 시간 상위권이 전부 sleep을 가진 테스트다. 실패 메시지는 `expected: <true> but was: <false>`·`null` 같은 "아직 안 됨" 모양이다.
- 원인: sleep은 작업이 일찍 끝나도 다 쉬고(실험 C: 2101ms vs 약 2ms), 늦게 끝나면 깨진다([09](../09-flaky-tests/2-summary.md) 실험 B).
- 대처: 비동기 결과는 신호 대기로, 시간 흐름은 가짜 시계·수동 스케줄러로 바꾼다. 운영 코드의 하드코딩된 sleep·타임아웃은 설정 가능하게 만든다(SWE@G 14장).

### 2. 자정·월말·DST에만 실패 (⚠ 커리큘럼)

- 현상: 1년에 며칠, 또는 하루 중 특정 시각에만 CI가 빨강이다. 다시 돌리면 초록이다.
- 보이는 형태: 실패 날짜가 31일·말일·DST 전환일·UTC 자정(KST 09:00) 근처에 몰린다.
- 원인: 코드나 테스트가 시스템 시계를 직접 읽는다. 또는 테스트가 기대값을 `now()`로 다시 계산한다(실험 A).
- 대처: `Clock` 주입 + 고정 시계로 경계 날짜를 명시적으로 시험한다. 의심되면 1년을 훑는 테스트를 한 번 돌린다(실험 B: 365일 중 7일).

### 3. 고정 시계로 "시간이 흐르는 코드"를 시험했다

- 현상: 테스트가 끝나지 않거나, 타임아웃 분기가 한 번도 안 탄다.
- 보이는 형태: 테스트가 멈춰 CI 잡 전체 타임아웃으로 죽는다.
- 원인(예시, 실험 안 함): `while (clock.instant().isBefore(deadline))`류 루프에 `Clock.fixed`를 넘기면 시간이 흐르지 않아 루프가 끝나지 않는다.
- 대처: 시간이 흘러야 하는 동작은 가변 시계로 시험하고, 루프가 시계를 진행시키는 훅(또는 스케줄러)을 거치게 한다. 테스트에 `@Timeout`을 걸어 멈춤을 실패로 바꾼다.

### 4. 동시성 테스트가 초록 = 안전이라는 착각

- 현상: 동시성 테스트가 있는데도 운영에서 중복 생성·합계 불일치가 난다.
- 보이는 형태: 테스트는 몇십 번 반복으로 늘 초록이다. 운영 로그에 같은 키가 두 번 생성된 흔적이 있다.
- 원인: 스레드를 순서대로 시작해 겹침이 적거나(실험 E: 출발선 없이 2000번 중 55~96번만 드러남), 반복 횟수가 노출 확률에 비해 너무 적다.
- 대처: 출발선을 넣고 반복을 늘린다. 위험 구간은 강제 끼어들기로 결정적으로 재현한다. 고친 뒤에는 원자적 API(`computeIfAbsent`, DB 유니크 제약)의 명세를 근거로 삼는다.

### 5. 가짜 스케줄러와 실제 실행기의 계약이 다르다

- 현상: 테스트에서는 주기 작업이 계속 돌았는데, 운영에서는 어느 순간 멈췄다.
- 보이는 형태: 주기 작업 로그가 특정 예외 직후부터 끊긴다. 에러 로그가 없을 수 있다(예외가 `Future` 안에 갇힌다).
- 원인: `scheduleAtFixedRate`는 작업이 예외를 던지면 이후 실행을 억제한다(javadoc). 가짜 스케줄러는 예외 뒤에도 다음 실행을 이어 갔다.
- 대처: 가짜에 실제 계약(예외 시 중단, 지연 시 겹치지 않음)을 반영하거나, 작업 본문을 `try/catch`로 감싸 예외를 기록하고 계속 돌게 한다. 가짜와 실제를 같은 계약 테스트로 함께 검증한다.

## 핵심 문장

- 시계·스케줄·스레드 순서는 숨은 입력이다. 테스트가 통제하려면 `Clock`·`Scheduler`처럼 인자로 드러내야 한다.
- 고정 시계는 특정 시점의 판정을, 가변 시계와 수동 스케줄러는 시간이 흐르는 동작을 실제 대기 없이 경계까지 정확히 시험하게 한다.
- 기대값을 `now()`로 다시 계산하면 자정에 깨진다. 기대값은 고정 시계와 리터럴로 적는다.
- 동시성 테스트는 출발선으로 겹침을 늘리고 불변식으로 단언한다. 아는 위험 구간은 이음새와 래치로 강제 재현한다.
- 몇십 번 통과한 동시성 테스트는 안전 증명이 아니다. 근거는 원자적 API의 명세와 도구의 체계적 탐색에서 찾는다.

## 관련 주제·근거

- 선행·연결
  - [09-flaky-tests](../09-flaky-tests/2-summary.md) — 시간·동시성은 불안정 테스트의 주요 원인
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) — check-then-act, data race vs race condition
  - [software-design/25-dependency-injection-and-composition-root](../../software-design/25-dependency-injection-and-composition-root/2-summary.md) — 숨은 입력(시계) 주입, `mockStatic` 대신 주입
  - [software-design/26-functional-core-imperative-shell](../../software-design/26-functional-core-imperative-shell/2-summary.md) — 시각을 셸에서 읽어 코어에 값으로 넘기기
  - [domain-modeling/13-instant-vs-local-time-and-tz-rules](../../domain-modeling/13-instant-vs-local-time-and-tz-rules/2-summary.md) — DST 공백·중복, Period vs Duration
  - [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md) — 운영의 시계는 뒤로 갈 수도 있다
  - [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — 경계값 분석
  - [17-characterization-tests-legacy](../17-characterization-tests-legacy/2-summary.md) — 이음새(seam)
- 문서
  - Java SE 21 `java.time.Clock` javadoc(목적·모범 사례·`fixed`·`offset`·스레드 안전 요구) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/Clock.html>
  - Java SE 21 `ScheduledExecutorService.scheduleAtFixedRate` javadoc(예외 시 이후 실행 억제) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html>
  - 『Software Engineering at Google』 13장 「Test Doubles」 — Determinism(시스템 시계 대신 시각을 하드코딩한 더블), Seams; 11장(작은 테스트는 sleep 금지, 폴링 권고); 14장(운영 코드의 sleep·타임아웃을 테스트에서 조정 가능하게) <https://abseil.io/resources/swe-book>
  - JUnit 5.13.4 User Guide 2.21 「Timeouts」(폴링 테스트에 `@Timeout`) <https://docs.junit.org/5.13.4/user-guide/index.html>
  - Awaitility Usage(기본 상한 10초·폴링 간격 100ms) <https://github.com/awaitility/awaitility/wiki/Usage>
  - OpenJDK jcstress README <https://github.com/openjdk/jcstress>, JetBrains Lincheck README <https://github.com/JetBrains/lincheck>
- 실험 목록(코드: `scratchpad/ts/09/e10/TimeConc.java`, 실행: `docker run --rm --cpus=2 eclipse-temurin:21-jdk java TimeConc.java`, JDK 21.0.12, 2026-10-03, 집필 3번 + 사실 점검 재실행 4번)
  - A — 두 번 읽는 시계와 자정(1ms씩 흐르는 시계).
  - B — 고정 시계로 2026년 365일: `plusMonths(1)` 말일 보정 7일, 뉴욕 DST 전날 2일·서울 0일, 없는 시각 02:30 → 03:30.
  - C — TTL 캐시 sleep(2101ms) vs 가변 시계(1.23~2.61ms), 경계 1999/2000ms. 만료 판정 변형 비교(`scratchpad/ts/adj-09/e10/TtlVariants.java`, 1회): `now.isAfter(exp)` 경계 결함은 sleep 판 PASS·가짜 시계 판 FAIL, `!now.isAfter(exp)`는 둘 다 FAIL.
  - D — 백오프 100·200·400ms, 실제 스케줄러(723~744ms) vs 수동 스케줄러(6.12~11.46ms).
  - E — check-then-act 2000회×7: 출발선 없음 55~96, 있음 169~243, `computeIfAbsent` 0, 강제 끼어들기 `created=2`.
