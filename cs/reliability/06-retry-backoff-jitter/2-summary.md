# reliability/06-retry-backoff-jitter — 지수 백오프·지터·재시도 예산 — 정리 (힌트)

## 해결하는 문제

원격 호출은 가끔 실패한다. 타임아웃, 503, 잠깐의 경합 같은 **일시 실패**다.\
이때 재시도를 정해 두지 않으면 둘 중 하나가 된다.

```text
 재시도 없음      일시 실패 1번 = 사용자 에러 1번          곧 멀쩡해질 상대를 못 기다린다
 무작정 재시도    실패한 1000명이 같은 순간 다시 요청      아픈 서버를 더 때린다 → 회복이 늦어진다
```

- *일시 실패(transient failure)*: 다시 하면 성공할 수 있는 실패. 반대는 *영구 실패*(보통 400, 404, 잔액 부족)다. 단 상태 코드의 뜻은 API마다 다르다(아래 적용 1).
- *재시도 폭풍(retry storm)*: 실패한 요청들의 재시도가 한꺼번에 몰려 장애를 키우는 현상.

쉬운 예: 콘서트 예매가 터졌다. 10만 명이 같은 순간 새로고침을 누르면 서버는 더 오래 죽어 있다.\
각자 "조금씩 더 길게, 그리고 서로 다른 시각에" 다시 누르면 서버가 숨을 쉰다.

똑같은 구조다.\
실무 예: 결제 게이트웨이(PG) 호출 타임아웃, DB 데드락 재시도, AWS SDK·gRPC 클라이언트의 자동 재시도.\
이 노트는 세 가지를 정한다.

1. **얼마나 기다릴까** — 지수 백오프.
2. **언제 다시 올까** — 지터(무작위).
3. **전체 중 몇 %까지 다시 할까** — 재시도 예산.

기초(Ticker 주입, 대기 정책 세 가지, Retryer가 멈추는 네 이유, `RetryBudget` 직접 구현)는 원본 [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) 「동작·원리」에 있다.\
이 노트는 1차 출처(AWS·Google SRE·Finagle·gRPC)의 구체형과 실험을 더한다.

## 동작·원리

### 1. 재시도 한 번의 시간축

```text
 시도1 ──X (503)
          └─ 대기 d1 ─┐
                     시도2 ──X (타임아웃)
                              └─── 대기 d2 ───┐
                                             시도3 ──O
 d_n = 지수 백오프 상한 안에서 고른 값  (n번째 실패 뒤의 대기)
 멈추는 조건: 성공 · 영구 실패 · 시도 횟수 소진 · 남은 데드라인 < 다음 대기 · 예산 소진
```

- *지수 백오프(exponential backoff)*: 실패할 때마다 대기 상한을 배수(보통 2)로 늘린다. `min(cap, base × 2^n)`.
- *지터(jitter)*: 대기 시간에 섞는 무작위. 같은 순간 실패한 클라이언트들을 서로 다른 시각으로 흩는다.
- *데드라인(deadline)*: 호출자가 기다려 주는 마지막 시각. 남은 시간보다 긴 대기는 하지 않는다(05 데드라인 전파).

### 2. 대기 식 넷

AWS 블로그(Brooker 2015)의 그림 속 식은 이미지라서, 같은 글이 링크한 시뮬레이터 소스(`aws-samples/aws-arch-backoff-simulator`, `src/backoff_simulator.py`)에서 식을 옮겼다.

| 이름 | 식 (`expo(n) = min(cap, base × 2^n)`) | 성질 |
|---|---|---|
| Exponential (지터 없음) | `expo(n)` | 같은 순간 실패하면 같은 순간 돌아온다 |
| Equal Jitter | `expo(n)/2 + random(0, expo(n)/2)` | 최소 절반은 기다린다 |
| Full Jitter | `random(0, expo(n))` | 가장 넓게 흩는다. 0에 가까운 대기도 나온다 |
| Decorrelated | `sleep = min(cap, random(base, sleep × 3))` | 직전 대기를 기준으로 넓힌다 |

```text
 attempt          1         2          3
 Exponential     100       200        400        (base=100, 예시)
 Equal Jitter   50~100   100~200    200~400
 Full Jitter     0~100    0~200      0~400
```

- 제품마다 식이 다르다.
  - gRFC A6(gRPC 재시도 설계)는 `min(initialBackoff × multiplier^(n-1), maxBackoff) × random(0.8, 1.2)`로 적는다(±20% 지터).
  - grpc-java master의 `RetriableStream.intervalWithJitter`는 플래그(`GRPC_EXPERIMENTAL_XDS_RLS_LB`, 기본 true)가 켜지면 0.8~1.2배, 꺼지면 `random(0,1)`배(Full Jitter)를 쓴다(2026-10-01 소스 열람).
  - Resilience4j 2.4.0 `IntervalFunction.ofExponentialRandomBackoff`는 `간격 × (1 ± randomizationFactor)`이고 기본 randomizationFactor는 0.5다(아래 실험 출력).

### 실험 A: 경합하는 클라이언트 — 지터가 일과 시간을 함께 줄인다

AWS 블로그의 상황을 그대로 옮겼다.
- 클라이언트 N개가 행 하나를 OCC로 한 번씩 고친다(읽기 → 버전 붙여 쓰기 → 버전이 틀리면 백오프 후 다시).
  - *OCC(낙관적 동시성 제어)*: 잠그지 않고 쓰되, 쓸 때 "내가 읽은 버전 그대로인가"를 검사해 아니면 실패시키는 방식.
- 네트워크 지연은 **구간마다**(읽기 요청·응답, 쓰기 요청·응답 각각) |N(10ms, 2ms)|이다. 원본 시뮬레이터가 `Net.delay()`를 구간마다 부르고, 이 재현도 같다(출력 머리줄의 "왕복 지연"은 이 구간 지연을 뜻한다). base=5ms, cap=2000ms, 100회 평균. 값은 시뮬레이션 시간(ms)이다.

```java
// 핵심 — 정책 넷 (scratchpad/rel/06/e06/Backoff.java)
static double expo(int n, double base, double cap) { return Math.min(cap, Math.pow(2, n) * base); }
Policy equalJitter = n -> { double v = expo(n, b, c); return v / 2 + R.nextDouble() * v / 2; };
Policy fullJitter  = n -> R.nextDouble() * expo(n, b, c);
Policy decorrelated = n -> { s[0] = Math.min(c, b + R.nextDouble() * (s[0] * 3 - b)); return s[0]; };
```

(실험, JDK 21 temurin, `--cpus=2`, 이산 사건 시뮬레이션, seed 42, 2026-10-01)

```text
(A) OCC 경합 — base=5ms cap=2000ms, 왕복 지연 |N(10,2)|ms, 100회 평균
clients  policy            writes       완료시각ms
10       None                  50          379
10       Exponential           50         3460
10       EqualJitter           42          750
10       FullJitter            38          452
10       Decorrelated          37          440
50       None                 688         1134
50       Exponential          621        36155
50       EqualJitter          346         4079
50       FullJitter           332         2902
50       Decorrelated         374         2339
100      None                2424         2029
100      Exponential         1850        63389
100      EqualJitter          811         6578
100      FullJitter           796         4892
100      Decorrelated        1001         4502
```

교차 확인으로 AWS 원본 시뮬레이터(Python 2)를 Python 3.12에서 돌렸다. 고친 것은 `xrange→range`, 클라이언트 수 목록(10·50·100만), 출력 파일 경로뿐이다. 원본은 시드를 고정하지 않아 실행마다 값이 조금 다르다(재실행: 100 클라이언트 Exponential 1863회·63573ms, FullJitter 796회·4929ms — 1% 안팎 차이). 100 클라이언트 줄이 Java 결과와 거의 같다.

(실험, python:3.12-slim, 원본 `backoff_simulator.py`, 2026-10-01)

```text
100,63840,1859,Exponential
100,4624,1002,Decorr
100,6570,812,EqualJitter
100,4916,795,FullJitter
100,2030,2423,None
```

- 관찰 1 — 지터 없는 지수 백오프는 일(쓰기 시도 1850)을 조금 줄였지만 **완료 시각이 63초**로 가장 나쁘다. 대기 후에도 다 같이 돌아와 또 부딪힌다.
- 관찰 2 — Full Jitter는 일을 796으로 절반 아래로 줄였다. AWS 글의 "100 클라이언트에서 호출 수를 절반 넘게 줄였다"와 같은 방향이다.
- 관찰 3 — Equal은 일은 Full과 비슷하고 시간은 더 길다. Decorrelated는 일이 조금 많고 시간은 조금 짧다. 글의 결론(Equal이 jitter 중 진 쪽, Full vs Decorrelated는 일 vs 시간의 교환)과 같다.
- 관찰 4 — 대기 없음(None)이 시간은 가장 짧다. 대신 일이 가장 많다(2424). 서버가 이 경합을 견딜 여유가 있을 때만 맞는 선택이다.
- 한계: 이 모델은 "한 행에 대한 경합"이다. 과부하로 인한 실패에서는 시도 수가 곧 서버 부하라 일(writes) 열이 더 중요하다. AWS 글도 지터가 N² 성질 자체는 바꾸지 못한다고 적는다.

### 실험 B: 같은 순간 실패한 1000명이 언제 돌아오나

(실험, JDK 21, 같은 파일, base=100ms cap=10s, 각 클라이언트 재시도 3번의 도착 시각을 10ms 칸에 셈, 2026-10-01)

```text
(B) 1000 클라이언트 동시 실패 → 재시도 3번의 도착, base=100ms cap=10s, 10ms 칸 최대값
Exponential   최대 1000건 (100~110ms 칸)
EqualJitter   최대  225건 (50~60ms 칸)
FullJitter    최대  169건 (80~90ms 칸)
Decorrelated  최대   76건 (270~280ms 칸)
```

- 지수 백오프는 "얼마나 자주"를 줄인다. "언제"는 흩지 않는다. 1000건이 같은 10ms 칸으로 돌아왔다.
- 원본 노트의 RetryStormTest 결과(고정·지수 1000, FULL 200 미만, EQUAL 500 미만)와 같은 방향이다. 칸 크기·회수 세는 방법이 달라 숫자는 다르다.

### 3. 재시도는 계층마다 곱해진다

```text
 사용자 ─> 게이트웨이 (시도 4) ─> 서비스 A (시도 4) ─> 서비스 B (시도 4) ─> DB (과부하로 실패)
 DB가 받는 시도 = 4 × 4 × 4 = 64
```

(실험 C, JDK 21, 같은 파일, 2026-10-01)

```text
(C) 사용자 요청 1건이 DB에 닿는 횟수 (DB 항상 실패, 계층마다 시도 4번)
  재시도 계층 1개: 4번
  재시도 계층 2개: 16번
  재시도 계층 3개: 64번
  맨 위 1계층만 재시도, 나머지 시도 1번: 4번
```

- Google SRE 책 22장 "Addressing Cascading Failures": 백엔드·프론트엔드·JavaScript가 각각 재시도 3번(시도 4번)이면 사용자 행동 하나가 DB에 **4³ = 64번**이 된다. "재시도는 한 계층에서"를 권한다.
- AWS Builders' Library "Timeouts, retries, and backoff with jitter"(Brooker): 5단 호출 스택에서 계층마다 3번이면 DB 부하가 **243배**(3⁵)다. 낮은 비용의 호출은 "retry at a single point in the stack"이 모범 사례라고 적는다.

### 4. 재시도 예산 — 전체 중 재시도 비율의 상한

시도 횟수 상한은 **요청 하나**를 묶는다. 상대가 통째로 죽으면 모든 요청이 상한까지 재시도해 부하가 상한 배수가 된다.\
그래서 **전체 트래픽 대비** 재시도를 묶는 두 번째 겹이 필요하다.

```text
 토큰 통 [●●●●●●●●●●]  요청·성공이 채운다 / 재시도·실패가 꺼낸다
 정상: 거의 안 꺼냄 → 제한 없음처럼 동작
 전면 장애: 금방 바닥 → 재시도 중단 → 부하 ≈ 원래 요청 수
```

| 구현 | 규칙 | 출처 |
|---|---|---|
| Google (SRE 21장) | 요청당 시도 3번 상한 + 클라이언트별 재시도 비율 10% 미만일 때만 재시도. 최악에 3배 가까이 늘 부하가 약 1.1배로 준다 | SRE 21장 "Handling Overload" |
| Finagle `RetryBudget` (6.31~) | 기본: 요청의 20% + 초당 최소 10회. 적립(deposit)은 10초 뒤 만료(TTL 1~60초) | Finagle 블로그 2016-02-08, `RetryBudget.scala` `DefaultTtl = 10.seconds`·`DefaultMinRetriesPerSec = 10`·`apply(..., 0.2, ...)` |
| gRPC `retryThrottling` | 서버 이름별 `token_count`(처음 = maxTokens). 실패 −1, 성공 +tokenRatio. **token_count ≤ maxTokens/2**이면 재시도·헤지 중단. maxTokens는 (0, 1000] | gRFC A6 Client Retries |
| Envoy `retry_budget` | 동시 재시도 ≤ (활성+대기 요청)의 `budget_percent`(기본 20%), 최소 `min_retry_concurrency`(기본 3) | Envoy `circuit_breaker.proto` 문서(latest, 2026-10-01 열람) |
| AWS SDK | 토큰 버킷으로 재시도를 묶는다. Builders' Library 글은 "토큰이 있으면 재시도, 바닥나면 고정 속도로만", 2016년 SDK에 추가라고 설명한다. 현행 SDK 문서(standard 모드)는 토큰이 바닥나면 **재시도하지 않고 오류를 돌려준다**고 적는다 | AWS Builders' Library 같은 글, AWS SDK 참조 가이드 "Retry behavior" |

- 계층 구분: 위 기본값은 **각 라이브러리·프록시의 기본값**이다. 기능 자체가 선택인 것도 있다 — Envoy `retry_budget`은 설정했을 때만 켜지고, 20%·3은 그 안의 필드를 생략했을 때 값이다. 설정하지 않으면 동시 재시도 한도 `max_retries`(기본 3)가 적용된다. 프로토콜이 정한 것이 아니다. 앱에서 따로 재시도하면 이 예산 밖에서 곱해진다.
- gRPC 규칙에서 실패로 세는 것은 재시도 대상 상태 코드, 헤징 정책의 non-fatal 상태 코드(`nonFatalStatusCodes`), "재시도하지 말라" pushback뿐이다. `INVALID_ARGUMENT` 같은 요청 잘못은 세지 않는다(A6).

### 실험 D: 예산이 전면 장애에서 부하를 묶는다

요청 1000건, 요청당 최대 4번, 서버 실패율 p. 세 열은 서버가 받는 총 시도 수다.\
Finagle식은 단순화했다(요청마다 0.2 적립, 재시도마다 1 인출, TTL·초당 최소치 생략).

(실험, JDK 21, 같은 파일, seed 7, 2026-10-01)

```text
실패율         예산 없음   gRPC 스로틀(10,0.1)   Finagle식 20%+최소0
0.0          1000               1000               1000
0.1          1100               1035               1100
0.3          1397               1006               1199
1.0          4000               1003               1200
```

- 전면 장애(p=1.0)에서 예산 없음은 4배(4000)다. gRPC 스로틀은 1003, Finagle식은 1200이다.
- gRPC 1003의 내역: 첫 요청이 토큰 10→9→8→7→6을 쓰며 4번 시도했다. 두 번째 요청의 실패로 5가 되어 문턱(≤5)에 닿았다. 이후는 첫 시도만 나갔다.
- 실패율 10%에서도 gRPC 스로틀이 재시도를 일부 막았다(1035 < 1100).
  - 해석: 시도마다 토큰 기대 변화는 `(1−p)×0.1 − p×1`이다. p > 0.1/1.1 ≈ 9.1%면 음수라 토큰이 서서히 줄어 문턱에 닿는다. tokenRatio가 "견딜 실패율"을 정한다.

## 쓰이는 자료구조·알고리즘

- **지수 백오프** — `min(cap, base × 2^n)`. 곱하기 전에 넘침을 막는 시프트 구현은 원본 [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) 「쓰이는 자료구조」와 [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md).
- **의사 난수(PRNG)** — 지터의 재료. 시드를 주입하면 테스트가 결정적이 된다. 의사 난수 일반은 math/12-randomness-and-prng(미작성, [math/README.md](../../math/README.md)).
  - AWS Builders' Library는 주기 작업의 지터를 호스트마다 **같은 값이 나오는 방식**(예시: 호스트 ID 해시 — 글은 "같은 호스트에서 매번 같은 수를 내는 일관된 방법"이라고만 적는다)으로 고른다고 적는다. 과부하가 나도 같은 패턴으로 나서 원인을 찾기 쉽다는 이유다.
- **토큰 버킷(재시도 예산)** — 요청·성공이 채우고 재시도·실패가 꺼낸다. 들어오는 요청을 묶는 토큰 버킷은 [11-rate-limiter](../11-rate-limiter/2-summary.md).
- **우선순위 큐(이산 사건 시뮬레이션)** — 실험 A는 사건을 도착 시각 순 힙에서 꺼내 처리한다. AWS 원본 시뮬레이터도 `heapq`를 쓴다.
- **곱셈 증폭 = 트리 경로의 곱** — 호출 그래프에서 루트→잎 경로의 시도 수를 곱한 값이 잎의 부하다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **재시도해도 되는 오류인가** — 일시 실패(타임아웃, 503, `UNAVAILABLE`, 데드락)만. 400·404·`INVALID_ARGUMENT`는 보통 하지 않는다. 단 판단은 상태 코드가 아니라 그 API의 오류 의미로 한다 — 예: AWS SDK는 HTTP 400 + 오류 코드 `RequestTimeout`을 일시 실패로 보고 재시도한다(AWS SDK 참조 가이드 "Retry behavior").
2. **재시도해도 되는 작업인가** — 부작용 있는 호출은 멱등 키가 있을 때만(AWS Builders' Library: 부작용 있는 API는 멱등성을 제공하지 않으면 재시도가 안전하지 않다). [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md).
3. **어느 계층에서 하나** — 한 곳만. 나머지 계층은 실패를 그대로 올린다.
4. **횟수·대기** — 시도 3~4번(예시), 지수 백오프 + 지터, 상한(cap).
5. **데드라인** — 남은 시간보다 긴 대기는 하지 않고 포기한다.
6. **예산** — 클라이언트(또는 프록시)에 재시도 비율 상한.
7. **서버 신호 존중** — 429·503의 `Retry-After`, gRPC `grpc-retry-pushback-ms`.

### 2. 코드 — Full Jitter + 데드라인 + 예산 (Java)

```java
// 재시도 예산: 요청마다 ratio 적립, 재시도마다 1 인출 (원본 RetryBudget과 같은 모양, 정수 고정소수점)
final class RetryBudget {
    private final long ratioMilli, maxMilli; private long tokensMilli;   // 1/1000 단위 정수
    RetryBudget(double ratio, int max) { ratioMilli = Math.round(ratio * 1000); maxMilli = max * 1000L; }
    synchronized void onRequest() { tokensMilli = Math.min(maxMilli, tokensMilli + ratioMilli); }
    synchronized boolean tryRetry() { if (tokensMilli < 1000) return false; tokensMilli -= 1000; return true; }
}

static <T> T callWithRetry(Callable<T> op, long deadlineNanos, RetryBudget budget) throws Exception {
    budget.onRequest();
    long base = 100, cap = 2_000;                                   // ms (예시)
    for (int attempt = 0; ; attempt++) {
        try { return op.call(); }
        catch (TransientException e) {                              // 일시 실패만 재시도
            if (attempt + 1 >= 4 || !budget.tryRetry()) throw e;    // 시도 4번 · 예산
            long expo = Math.min(cap, base << attempt);
            long sleepMs = ThreadLocalRandom.current().nextLong(expo + 1);   // Full Jitter: [0, expo]
            if (System.nanoTime() + sleepMs * 1_000_000 > deadlineNanos) throw e;   // 데드라인(대기만 검사)
            Thread.sleep(sleepMs);
        }
    }
}
```

- 이 코드의 데드라인 검사는 **다음 대기**가 남은 시간을 넘는지만 본다. `op.call()` 자체가 데드라인을 넘겨 도는 것은 막지 못한다. 그러려면 하위 호출에 남은 시간을 타임아웃으로 넘긴다(05 데드라인 전파).

### 3. 라이브러리 설정

```java
// Resilience4j 2.x Retry — 기본(ofDefaults)은 maxAttempts=3, 대기 500ms 고정(아래 실험 출력)
RetryConfig cfg = RetryConfig.custom()
    .maxAttempts(4)
    .intervalFunction(IntervalFunction.ofExponentialRandomBackoff(100, 2.0, 0.5))  // 100ms×2^(n-1)×(1±0.5)
    .retryOnException(e -> e instanceof TransientException)
    .build();
```

(실험, Resilience4j 2.4.0, JDK 21, `scratchpad/rel/06/e06/RetryDefaults.java`, 2026-10-01 — 표본 값은 실행마다 다르다)

```text
Resilience4j 2.4.0 RetryConfig.ofDefaults(): maxAttempts=3 interval(1)=500ms interval(2)=500ms
ofExponentialRandomBackoff(100ms, x2, 0.5) 표본: n=1:83 n=2:109 n=3:448 n=4:598
DEFAULT_RANDOMIZATION_FACTOR=0.5 DEFAULT_MULTIPLIER=1.5
```

- 기본값은 지터 없는 고정 500ms다. 지터는 직접 켜야 한다.

gRPC 서비스 설정(gRFC A6의 예시 모양):

```json
{
  "methodConfig": [{
    "name": [{"service": "pay.Gateway"}],
    "retryPolicy": {
      "maxAttempts": 4, "initialBackoff": "0.1s", "maxBackoff": "1s",
      "backoffMultiplier": 2, "retryableStatusCodes": ["UNAVAILABLE"]
    }
  }],
  "retryThrottling": { "maxTokens": 10, "tokenRatio": 0.1 }
}
```

- A6: `maxAttempts`는 원 요청을 포함한 수이고, 5보다 크면 5로 취급한다(검증 오류는 아니다). grpc-java는 이 상한을 `ManagedChannelBuilder.maxRetryAttempts`로 바꿀 수 있다(서비스 설정 값이 더 크면 이 값으로 줄인다 — 같은 파일 Javadoc).

### 4. 진단

- 재시도 비율(PromQL 예시 — 지표 이름은 계측 라이브러리마다 다르다):

```promql
sum(rate(client_requests_total{attempt!="1"}[5m])) / sum(rate(client_requests_total[5m]))
```

- 같은 요청 ID(상관 ID)가 하류 로그에 몇 번 찍히는지 센다. 계층 수 × 시도 수와 비교한다.
- Envoy: `upstream_rq_retry`, `upstream_rq_retry_overflow`(재시도 예산·한도 초과) 카운터.
- 장애 중 재시도 비율 그래프가 오르면 원인이 아니라 증상으로 오인하기 쉽다. SRE 22장도 이 함정을 적는다. 재시도 동작을 고치려면 대개 코드 배포가 필요하다는 점도 같은 절에 있다.

## 장애 시나리오와 대처

### 1. 지터 없는 재시도 → 동기화된 재시도 폭풍 (⚠ 커리큘럼)

- 현상: 하류가 잠깐 멈췄다 돌아왔는데 몇 초마다 다시 넘어진다.
- 보이는 형태: 하류 요청률 그래프가 일정 간격(100ms·200ms·400ms…)의 뾰족한 봉우리. 봉우리마다 503·타임아웃.
- 원인: 모두 같은 시각에 실패했고 같은 식으로 기다렸다. 실험 B에서 지터 없는 지수 백오프는 1000건 전부가 같은 10ms 칸에 돌아왔다.
- 대처: Full Jitter(또는 Decorrelated)로 바꾼다. 실험 A에서 100 클라이언트 경합의 일이 1850 → 796, 완료 시각이 63초 → 4.9초로 줄었다. 주기 작업(cron·하트비트)에도 지터를 넣는다.

### 2. 계층마다 재시도 → 곱셈 증폭 (⚠ 커리큘럼)

- 현상: DB가 조금 느려졌을 뿐인데 DB 쿼리 수가 평소의 수십 배로 뛰고 회복하지 못한다.
- 보이는 형태: DB에 같은 쿼리(같은 상관 ID)가 수십 번. 게이트웨이·서비스·SDK 설정에 각자 `retries: 3`.
- 원인: 계층마다 자기 시야에서 "3번"을 지켰다. 실험 C: 3계층 × 시도 4 = 64.
- 대처: 재시도는 한 계층에서만. 서비스 메시 재시도와 앱 재시도가 겹치지 않게 한쪽을 끈다(50 사이드카·서비스 메시). 남는 계층에는 예산을 둔다.

### 3. 예산 없이 장애가 길어진다

- 현상: 하류의 원인은 고쳐졌는데 부하가 내려가지 않는다.
- 보이는 형태: 하류 요청률이 평소의 (최대 시도 수)배 근처에 머문다. 재시도 비율이 50%를 넘는다.
- 원인: 요청별 상한만 있고 전체 상한이 없다. AWS Builders' Library는 과부하 실패에서 재시도가 "원래 문제가 풀린 뒤에도 부하를 높게 유지해 회복을 늦출 수 있다"고 적는다.
- 대처: 재시도 예산(Finagle 20%, gRPC `retryThrottling`, Envoy `retry_budget`). 실험 D에서 전면 장애 부하가 4000 → 1003~1200으로 묶였다.

### 4. 비멱등 작업 재시도 → 중복 부작용

- 현상: 사용자는 결제 실패를 봤는데 카드가 두 번 승인됐다.
- 보이는 형태: PG 거래 내역에 같은 주문의 승인 두 건. 우리 로그에는 첫 시도 타임아웃 + 두 번째 성공.
- 원인: 타임아웃은 "실패"가 아니라 "모름"이다(첫 승인은 됐을 수 있다). 멱등 키 없이 다시 보냈다. [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) 실험 A가 같은 사고를 재현한다.
- 대처: 멱등 키를 붙여 보내고(받는 쪽이 중복을 걸러야 한다 — 13 idempotency), 키를 못 쓰는 외부 호출은 재시도 대신 조회·대사로 결과를 확인한다.

### 5. 스로틀이 너무 예민해 정상 재시도까지 막힌다

- 현상: 하류 실패율이 10%대로 조금 올랐을 뿐인데 사용자 에러가 실패율보다 크게 는다.
- 보이는 형태: 클라이언트 쪽 "재시도 안 함(throttled)" 로그·지표가 실패 직후부터 쌓인다.
- 원인: gRPC `tokenRatio=0.1`이면 실패율 약 9.1%를 넘을 때 토큰이 줄어 문턱에 닿는다(실험 D의 p=0.1 줄, 계산은 위 해석).
- 대처: 견딜 실패율에 맞춰 tokenRatio를 고른다. 예산 소진은 지표로 내보내 경보한다.

## 핵심 문장

- 재시도의 첫 판단은 "재시도해도 되는 오류·작업인가"다. 그다음이 얼마나·언제·몇 %다.
- 지수 백오프는 빈도를 줄이지만 시각을 흩지 않는다. 실험 B에서 지터 없는 1000건이 같은 10ms에 돌아왔다.
- 지터는 일과 시간을 함께 줄인다. 100 클라이언트 경합에서 Full Jitter는 지터 없는 지수 백오프보다 쓰기 시도를 절반 아래로, 완료 시각을 1/10 아래로 줄였다.
- 재시도는 계층마다 곱해진다(4×4×4=64). 한 계층에서만 하고 나머지는 실패를 올린다.
- 요청별 상한은 요청 하나를, 재시도 예산은 전체를 묶는다. Finagle 기본 20%+초당 10회, gRPC는 토큰이 절반 이하면 재시도·헤지를 멈춘다.

## 관련 주제·근거

- 선행
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md). 기초는 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md)
  - math/12-randomness-and-prng — 미작성([math/README.md](../../math/README.md))
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 타임아웃 = 모름, 재시도와 중복
- 원본
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) — Ticker·대기 정책·Retryer·RetryBudget 구현. 참고: 원본은 `RetryBudget`이 "Hystrix, 구글 SRE 책, gRPC retry throttling이 전부 이 모양"이라고 적는다. gRPC는 요청이 아니라 **성공**이 tokenRatio만큼 채우고 **실패**가 1을 빼며, 토큰이 0이 아니라 **maxTokens/2 이하**에서 멈춘다(gRFC A6). 모양은 토큰 버킷이지만 규칙이 다르다.
- 후속·연결
  - [10-circuit-breaker](../10-circuit-breaker/2-summary.md) — 재시도를 아예 하지 않기로 정하는 쪽
  - [11-rate-limiter](../11-rate-limiter/2-summary.md) — 같은 토큰 버킷으로 들어오는 요청을 묶는다
  - [28-bulkhead](../28-bulkhead/2-summary.md) — 재시도 대기가 묶는 스레드를 칸으로 나눈다
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 과부하 때 재시도 대신 거절·셰딩
  - [13-idempotency](../13-idempotency/2-summary.md), [34-tail-latency-and-stragglers](../34-tail-latency-and-stragglers/2-summary.md)(hedged request), [50-sidecar-ambassador-and-service-mesh](../50-sidecar-ambassador-and-service-mesh/2-summary.md)
  - [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) — 메시지 소비 쪽 재시도·DLT
- 글·문서
  - Marc Brooker, "Exponential Backoff And Jitter", AWS Architecture Blog, 2015-03-04 <https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/> · 시뮬레이터 <https://github.com/aws-samples/aws-arch-backoff-simulator> `src/backoff_simulator.py`
  - Marc Brooker, "Timeouts, retries, and backoff with jitter", Amazon Builders' Library — selfish retries, 5단 × 3 = 243배, single point, SDK 토큰 버킷(2016), 주기 작업 지터 <https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/>
  - Google SRE 책 21장 "Handling Overload"(요청당 3번·클라이언트별 10%·약 1.1배), 22장 "Addressing Cascading Failures"(randomized exponential backoff, 4³=64, 서버 전체 예산 예: 분당 60회) <https://sre.google/sre-book/handling-overload/> · <https://sre.google/sre-book/addressing-cascading-failures/>
  - Kevin Oliver, "Retry Budgets", Finagle 블로그 2016-02-08 <https://finagle.github.io/blog/2016/02/08/retry-budgets/> · `finagle-core/.../service/RetryBudget.scala`
  - gRFC A6 "gRPC Retry Design"(Last updated 2024-08-23) — retryPolicy, ±20% 지터, retryThrottling, pushback <https://github.com/grpc/proposal/blob/master/A6-client-retries.md> · grpc-java `core/src/main/java/io/grpc/internal/RetriableStream.java`(intervalWithJitter)
  - Envoy `config.cluster.v3.CircuitBreakers.Thresholds.RetryBudget`(budget_percent 20%, min_retry_concurrency 3) <https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/circuit_breaker.proto>
  - Resilience4j Retry 문서 <https://resilience4j.readme.io/docs/retry>
- 실험 목록 (코드: scratchpad `rel/06/e06/`)
  - A OCC 경합 5정책 × 클라이언트 10·50·100 — `Backoff.java`, JDK 21 temurin `--cpus=2`. 교차: AWS 원본 시뮬레이터 Python 3.12(`aws_sim_py3.py`)
  - B 1000 동시 실패의 재도착 10ms 칸 최대값 — 같은 파일
  - C 계층 증폭 4·16·64 — 같은 파일
  - D 예산 없음 vs gRPC 스로틀 vs Finagle식 — 같은 파일
  - Resilience4j 2.4.0 Retry 기본값·지터 표본 — `RetryDefaults.java`
