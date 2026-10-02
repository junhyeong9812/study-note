# reliability/10-circuit-breaker — 서킷 브레이커: 닫힘·열림·반열림 — 정리 (힌트)

## 해결하는 문제

하류가 확실히 죽었는데도 계속 부르면 세 쪽이 손해를 본다.

```text
 브레이커 없음
 요청 ─> 죽은 하류 ─> 타임아웃 1초 ─> 재시도 ─> 사용자는 몇 초 뒤 실패
           │
           ├─ 우리 스레드·커넥션이 그동안 묶인다      (장애가 우리에게 번진다)
           └─ 회복하려는 하류가 계속 두들겨 맞는다    (회복이 늦어진다)
 브레이커 있음
 요청 ─> [열림] ─> 호출하지 않고 즉시 실패(0ms) ─> 폴백(빈 추천 칸, 캐시 값)
          가끔 몇 건만 보내 회복을 확인한다
```

- *서킷 브레이커(circuit breaker)*: 최근 실패가 임계를 넘으면 하류 호출 자체를 끊고, 시간이 지나면 몇 건만 보내 회복을 확인하는 장치.
- *폴백(fallback)*: 본래 경로가 막혔을 때 대신 돌려주는 값이나 경로.

쉬운 예: 집의 누전 차단기다. 이상 전류가 감지되면 전기를 끊고, 나중에 한 번 올려 본다.\
똑같은 구조다.\
실무 예: 추천 API가 죽었을 때 상품 페이지 전체가 몇 초씩 느려지는 대신, 추천 칸만 비우고 나머지를 바로 그린다. 외부 PG 장애 때 결제 요청을 즉시 "잠시 후 다시" 응답으로 돌린다.

06(재시도)이 "다시 해 볼까"라면, 이것은 "**당분간 하지 말자**"다.\
기초(상태 전이 직접 구현, 개수·시간 창, 실패 판단 술어, 락 밖 실행)는 원본 [ops-patterns/02-circuit-breaker](../../ops-patterns/02-circuit-breaker/2-summary.md) 「동작·원리」에 있다.\
이 노트는 실제 라이브러리(Resilience4j 2.4.0)의 동작과 기본값을 실험으로 확인하고, 플래핑·폴백·느린 하류를 다룬다.

## 동작·원리

### 1. 상태 기계

```text
                 실패율 ≥ 임계  또는  느린 호출 비율 ≥ 임계
                 (단, 기록된 호출 ≥ minimumNumberOfCalls)
   ┌────────┐ ───────────────────────────────────────────> ┌────────┐
   │ CLOSED │                                              │  OPEN  │  호출 안 함
   │ 통과·  │ <──────────┐                                 │        │  CallNotPermittedException
   │ 결과기록│            │                                 └────┬───┘
   └────────┘            │ 반열림 표본의 비율 < 임계              │ waitDurationInOpenState 경과
                         │                                      v
                     ┌───┴──────┐  반열림 표본의 비율 ≥ 임계   ┌────────┐
                     │HALF_OPEN │ ─────────────────────────> │  OPEN  │
                     │ N건만 통과│                             └────────┘
                     └──────────┘
```

- *닫힘(CLOSED)*: 정상. 호출을 통과시키고 결과를 창에 기록한다. 회로가 닫혀야 전류가 흐른다는 전기 용어에서 왔다.
- *열림(OPEN)*: 차단. 호출하지 않고 즉시 실패시킨다.
- *반열림(HALF_OPEN)*: 시험. 정해진 수(`permittedNumberOfCallsInHalfOpenState`)만 통과시키고 그 결과로 닫을지 다시 열지 정한다.
- Resilience4j는 이 셋 외에 특수 상태 셋을 둔다(문서): `METRICS_ONLY`(기록만 하고 열지 않음), `DISABLED`(항상 통과), `FORCED_OPEN`(항상 차단). 운영자가 수동으로 끄고 켤 때 쓴다.

### 2. "최근"을 세는 창

```text
 COUNT_BASED (최근 N건)                    TIME_BASED (최근 N초)
 원형 배열 [성 실 성 실 실 성 ...]         원형 배열 [초0 집계][초1 집계]...[초N-1 집계]
 새 결과가 가장 오래된 칸을 밀어낸다         칸마다 (실패 수, 느린 수, 전체 수, 총 시간)
 총계 = 들어올 때 더하고 나갈 때 뺀다 (Subtract-on-Evict)  → 조회 O(1)
```

- Resilience4j 문서: 창은 개별 결과를 저장하지 않고 칸별 부분 집계와 전체 집계를 갱신한다. 시간 창의 칸은 "에포크 초" 하나다.
- *minimumNumberOfCalls*: 이만큼 기록되기 전에는 비율을 계산하지 않는다. 문서 예: 최소 10이면 9건이 다 실패해도 열리지 않는다.

### 3. Resilience4j 2.4.0 기본값 — 라이브러리에서 직접 출력

(실험, Resilience4j 2.4.0, JDK 21 temurin `--cpus=2`, `scratchpad/rel/06/e10/Cb.java`, 2026-10-01)

```text
== Resilience4j 2.4.0 CircuitBreakerConfig.ofDefaults()
failureRateThreshold=50.0 slowCallRateThreshold=100.0 slowCallDurationThreshold=PT1M slidingWindowType=COUNT_BASED slidingWindowSize=100 minimumNumberOfCalls=100 permittedNumberOfCallsInHalfOpenState=10 waitDurationInOpenState=60000ms automaticTransition=false maxWaitDurationInHalfOpenState=PT0S
```

- 기본은 최근 100건 중 50% 이상 실패면 열고, 60초 뒤 10건으로 시험한다.
- 느린 호출 기준이 60초, 비율 임계가 100%라 **기본 설정으로는 느린 호출로 사실상 열리지 않는다**. 느림을 보려면 직접 낮춰야 한다.
- `automaticTransition=false`: OPEN→HALF_OPEN은 대기 시간이 지난 **뒤 첫 호출이 일으킨다**. 문서: true면 감시 스레드가 전이시킨다.
- 이 값들은 라이브러리 기본값이다. Spring Boot 설정(`resilience4j.circuitbreaker.instances.*`)에서 바꾸면 그 값이 쓰인다.

### 실험 A: 상태 전이를 실제로 따라가기

설정: 창 10건, 최소 10, 임계 50%, 대기 500ms, 반열림 허용 4.

```java
CircuitBreaker cb = CircuitBreaker.of("pg", CircuitBreakerConfig.custom()
    .slidingWindowType(SlidingWindowType.COUNT_BASED).slidingWindowSize(10).minimumNumberOfCalls(10)
    .failureRateThreshold(50).waitDurationInOpenState(Duration.ofMillis(500))
    .permittedNumberOfCallsInHalfOpenState(4).build());
cb.getEventPublisher().onStateTransition(e -> System.out.println("** 전이 " + e.getStateTransition()));
cb.executeSupplier(() -> { if (fail) throw new IllegalStateException("503"); return "ok"; });
```

(실험, 같은 환경, 2026-10-01 — 시각은 실행마다 다르다)

```text
t=  187ms 호출2(X)     실패      state=CLOSED
...
t=  194ms 호출9(X)     실패      state=CLOSED
          ** 전이 State transition from CLOSED to OPEN
t=  205ms 호출10       성공      state=OPEN
t=  207ms 호출11       차단(호출 안 함) state=OPEN
  (550ms 대기 — automaticTransition=false 이므로 다음 호출이 반열림 전이를 일으킨다)  state=OPEN
          ** 전이 State transition from OPEN to HALF_OPEN
t=  763ms 반열림1(X)    실패      state=HALF_OPEN
t=  764ms 반열림2       성공      state=HALF_OPEN
t=  764ms 반열림3       성공      state=HALF_OPEN
          ** 전이 State transition from HALF_OPEN to CLOSED
t=  766ms 반열림4       성공      state=CLOSED
  → 반열림 4건 중 실패 1건(25%) < 50%: CLOSED
...
t= 1318ms 반열림1(X)    실패      state=HALF_OPEN
t= 1319ms 반열림2(X)    실패      state=HALF_OPEN
t= 1320ms 반열림3       성공      state=HALF_OPEN
          ** 전이 State transition from HALF_OPEN to OPEN
t= 1321ms 반열림4       성공      state=OPEN
  → 반열림 4건 중 실패 2건(50%) >= 50%: OPEN
```

- 관찰 1 — 9건째까지 실패가 5건(55%)이어도 열리지 않았다. 기록이 최소 10에 못 미쳤다. 10건째(성공)로 5/10 = 50%가 되자 열렸다. 비교는 **≥**다.
- 관찰 2 — 550ms를 기다린 뒤에도 상태는 OPEN이었다. 다음 호출이 HALF_OPEN 전이를 일으켰다.
- 관찰 3 — 반열림은 **비율**로 판정한다. 4건 중 1건 실패(25%)면 닫히고, 2건(50%)이면 다시 열린다. 허용한 4건이 다 끝나야 판정한다(문서: "until all permitted calls have completed").
  - 참고: 원본 노트의 직접 구현은 "반열림에서 하나라도 실패하면 즉시 OPEN"이다. 그 구현에서는 맞지만, Resilience4j 2.x는 반열림 표본의 실패율로 판정한다(위 출력, 문서 「Failure rate and slow call rate thresholds」).

### 실험 B: 예외 없이 느리기만 한 하류

(실험, 같은 환경, 창 6, 최소 6, 느림 기준 100ms, 느림 비율 임계 50%, 하류 120ms, 2026-10-01)

```text
t= 1443ms 느린호출1 성공(120ms) state=CLOSED
...
t= 2049ms 느린호출6 성공(120ms) state=OPEN
t= 2049ms 느린호출7 차단 state=OPEN
  실패율=0.0% 느린비율=100.0%
```

- 실패율 0%인데 느린 비율로 열렸다. 기본값(60초·100%)이었다면 열리지 않았다.
- 결과는 호출이 **끝나야** 기록된다. 하류가 응답을 아예 안 주면 창에 아무것도 안 들어간다. 그래서 브레이커 안쪽에 타임아웃을 두어 "안 끝남"을 "실패"로 바꾼다.
  - 동기 호출이면 클라이언트 타임아웃(연결·읽기)을 건다. Resilience4j `TimeLimiter`는 `Future`·`CompletionStage`를 감싸는 것이라, 호출을 비동기 작업으로 돌릴 때 쓴다(Resilience4j TimeLimiter 문서).

### 실험 C: 무엇을 실패로 세나

(실험, 같은 환경, `IllegalArgumentException`(400류 흉내) 10건, 2026-10-01)

```text
  ignore=false state=OPEN 기록된 호출=10 실패=10
  ignore=true  state=CLOSED 기록된 호출=0 실패=0
```

- Resilience4j 기본은 **모든 예외를 실패로 센다**(문서: "By default all exceptions count as a failure"). 400이 많다는 것은 하류가 멀쩡하다는 뜻인데 회로가 열렸다.
- `ignoreExceptions`는 성공도 실패도 아닌 것으로 빼고, `recordExceptions`를 주면 그 목록만 실패로 센다(나머지는 무시가 아니면 성공으로 센다 — 문서).

### 4. 브레이커는 프로세스마다 따로다

```text
 인스턴스 20대 × 각자 브레이커
 각자 자기 창으로 배우고 각자 시험한다 → 감지가 인스턴스마다 다르고, 반열림 시험도 20갈래
```

- Resilience4j 상태는 `AtomicReference`에 있고 호출 자체는 동기화하지 않는다(문서). 한 JVM 안의 상태다.
- Envoy의 "circuit breaking"은 이름이 같지만 다른 것이다.
  - 클러스터별 **동시 연결·대기 요청·요청·재시도 수의 상한**이다. 기본 `max_connections`·`max_pending_requests`·`max_requests` 1024, `max_retries` 3(Envoy `circuit_breaker.proto` 문서, latest).
  - 워커 스레드들이 한도를 공유하고 최종적 일관이라 경쟁 중에 한도를 살짝 넘을 수 있다(Envoy circuit breaking 문서).
  - 실패한 호스트를 일정 시간 빼는 기능은 따로 **outlier detection**이다.

### 5. 서킷 브레이커에 대한 반론

AWS Builders' Library(Brooker)는 서킷 브레이커가 시스템에 "modal behavior"(상태에 따라 완전히 다른 동작)를 들여와 시험하기 어렵고, 회복 시간을 크게 늘릴 수 있다고 적는다. AWS는 대신 로컬 토큰 버킷으로 재시도를 묶는다(06).

- 해석: 브레이커의 OPEN은 "평소엔 안 지나는 경로"다. 그 경로(폴백·503 응답)를 시험하지 않으면 장애 때 처음 실행된다.
- 해석: 대기 시간(기본 60초) 동안은 하류가 이미 회복했어도 차단이 계속된다. 회복 시간에 그 대기가 더해진다.

## 쓰이는 자료구조·알고리즘

- **상태 기계** — CLOSED·OPEN·HALF_OPEN과 전이 규칙. 상태마다 받는 입력(허가 요청·결과 보고)이 다르다.
- **원형 배열 슬라이딩 창** — 개수 창은 최근 N건 원형 배열, 시간 창은 초 단위 칸 N개의 원형 배열. 들어올 때 더하고 나갈 때 빼서 조회가 O(1)이다. 알고리즘 쪽은 [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md)(커리큘럼 algorithm/15).
- **원자 참조(CAS)** — 상태를 `AtomicReference`로 바꾼다. 락 일반은 [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md).
- **술어(predicate)** — "무엇을 실패로 셀까". 숫자 설정보다 영향이 크다(실험 C).
- **관찰자(이벤트 퍼블리셔)** — `onStateTransition`, `onCallNotPermitted`. 전이 로그·지표의 재료.
- **히스테리시스** — 여는 조건과 닫는 조건을 다르게 둬서 진동을 줄인다. [systems/Hysteresis](../../systems/Hysteresis/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **하류 단위**로 브레이커를 둔다(PG, 추천 API 각각). 하류 여럿을 한 브레이커로 묶으면 하나의 장애가 전부를 끊는다.
2. **무엇을 실패로 셀지**: 5xx·타임아웃·연결 실패만. 400류와 우리 쪽 거절(`BulkheadFullException`)은 무시한다.
3. **느림도 실패로**: 안쪽 타임아웃 + `slowCallDurationThreshold`를 하류 p99보다 조금 위로(측정해서 정한다).
4. **창·최소 표본**: 트래픽에 맞춘다. 초당 1000건이면 100건 창은 0.1초다. 하루 10건이면 100건 창은 열흘 전까지 본다.
5. **열림 시 무엇을 줄지(폴백)**: 캐시 값·기본값·기능 축소, 또는 503 + `Retry-After`.
6. **겹치는 순서**: Resilience4j Spring Boot 기본 애스펙트 순서는 `Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( Function ) ) ) ) )`다(Resilience4j Spring Boot 문서). 재시도가 바깥이라 시도 하나하나가 브레이커 창에 기록된다.

### 2. 코드 (Java, Resilience4j 2.x)

```java
CircuitBreakerConfig cfg = CircuitBreakerConfig.custom()
    .slidingWindowType(SlidingWindowType.TIME_BASED).slidingWindowSize(30)       // 최근 30초
    .minimumNumberOfCalls(50)
    .failureRateThreshold(50)
    .slowCallDurationThreshold(Duration.ofMillis(800)).slowCallRateThreshold(50)  // 예시: 하류 p99 ≈ 600ms
    .waitDurationInOpenState(Duration.ofSeconds(10))
    .permittedNumberOfCallsInHalfOpenState(10)
    .recordExceptions(IOException.class, TimeoutException.class, ServerErrorException.class)
    .ignoreExceptions(ClientErrorException.class, BulkheadFullException.class)
    .build();
CircuitBreaker cb = CircuitBreaker.of("recommendation", cfg);

List<Item> recommend(long userId) {
    try {
        return cb.executeSupplier(() -> client.recommend(userId));
    } catch (CallNotPermittedException e) {      // 열림: 시도조차 안 했다
        return List.of();                         // 폴백: 추천 칸 비우기
    }
}
```

### 3. 관측

- 상태 전이를 이벤트로 로그·지표에 남긴다(`onStateTransition`). Micrometer 연동 시 Prometheus에서 `resilience4j_circuitbreaker_state{state="open"}`(상태별 0/1 게이지), `resilience4j_circuitbreaker_not_permitted_calls_total`(차단 수 카운터), `resilience4j_circuitbreaker_calls_seconds_count{kind="failed"|"successful"|"ignored"}` 같은 지표가 나온다(resilience4j-micrometer master 소스 `CircuitBreakerMetricNames`·`AbstractCircuitBreakerMetrics`, 2026-10-01 열람 — 이름은 `.`이 `_`로 바뀐 Prometheus 표기).
- 플래핑 탐지(PromQL 예시): 최근 10분 동안 "open" 상태 게이지(0/1)가 바뀐 횟수. 열림·닫힘을 합쳐 세므로 대략 OPEN 전이 수의 두 배다.

```promql
changes(resilience4j_circuitbreaker_state{name="recommendation",state="open"}[10m])
```

- Envoy: 클러스터 통계 `upstream_cx_overflow`(연결)·`upstream_rq_pending_overflow`(대기 요청)·`upstream_rq_active_overflow`(동시 요청)·`upstream_rq_retry_overflow`(재시도)가 오르면 그 한도에 걸린 것이다. 단 `upstream_rq_retry_overflow`는 재시도 서킷 브레이커뿐 아니라 retry budget 초과로 재시도를 안 했을 때도 오른다(Envoy cluster statistics 문서). latest 문서 기준으로 `max_requests` 초과는 `upstream_rq_active_overflow`만 올리고 예전의 `upstream_rq_pending_overflow`는 기본으로 올리지 않는다(런타임 플래그로 되돌릴 수 있다). HTTP 요청이면 라우터 필터가 `x-envoy-overloaded` 헤더를 붙인다(Envoy circuit breaking 문서).

## 장애 시나리오와 대처

### 1. 임계값 과민 → 정상 서비스 차단 플래핑 (⚠ 커리큘럼)

- 현상: 하류는 반쯤 살아 있는데(실패율 30%) 회로가 수십 ms마다 열렸다 닫힌다. 성공할 요청까지 막힌다.
- 보이는 형태: 상태 전이 로그 `CLOSED→OPEN→HALF_OPEN→CLOSED`가 초 단위로 반복. `not_permitted` 수가 실제 호출보다 많다.
- 원인: 창·최소 표본이 너무 작고 반열림 허용이 1건이다. 표본 몇 건의 운으로 열리고 닫힌다.

(실험 D, Resilience4j 2.4.0, 실패율 30% 하류, 3초간 1ms마다 호출, 대기 50ms, 임계 50%, 2026-10-01 — 실행마다 다르다. 집필 3회·점검 3회 실행에서 창 4는 OPEN 전이 53~54회, 하류로 간 호출 251~314. 창 100은 점검 3회 모두 OPEN 0회)

```text
  창=4 최소=2 반열림허용=1 → OPEN 전이 53회, 하류로 간 호출 314, 차단 2174
  창=100 최소=50 반열림허용=10 → OPEN 전이 0회, 하류로 간 호출 2604, 차단 0
```

- 대처: 창과 최소 표본을 키우고 반열림 허용을 여러 건으로. 실패율 30% 하류는 브레이커가 아니라 재시도·폴백으로 다룰 대상이다. 여는 조건과 닫는 조건을 다르게 두는 원리는 히스테리시스(33 hysteresis-and-flapping).

### 2. 폴백 없음 → 즉시 에러 전파 (⚠ 커리큘럼)

- 현상: 회로가 열렸는데 사용자 화면은 여전히 에러다. 응답이 빨라졌을 뿐이다.
- 보이는 형태: `CallNotPermittedException`이 잡히지 않고 500으로 매핑. 에러율 그대로, 지연만 0ms.
- 원인: 브레이커는 "시도하지 않았다"를 알려 줄 뿐 대신 줄 것을 정하지 않는다.
- 대처: 열림 예외를 잡아 폴백(캐시·기본값·기능 축소)을 주거나 503 + `Retry-After`로 매핑한다. 폴백 경로를 평소에 시험한다(`FORCED_OPEN`으로 강제해 보기).

### 3. 느리기만 한 하류에 회로가 안 열린다

- 현상: 하류 p99가 30초인데 브레이커는 CLOSED. 요청 스레드가 먼저 마른다.
- 보이는 형태: 창의 기록 수가 거의 늘지 않는다. 실패율 0%.
- 원인: 결과는 호출이 끝나야 기록된다. 기본 느린 호출 기준은 60초·100%라 사실상 꺼져 있다(3절 기본값 출력).
- 대처: 안쪽 타임아웃 + `slowCallDurationThreshold`/`slowCallRateThreshold`를 낮춘다(실험 B). 판단이 늦는 동안의 스레드 고갈은 [28-bulkhead](../28-bulkhead/2-summary.md)가 막는다.

### 4. 400류·내 쪽 거절을 실패로 세서 멀쩡한 하류를 끊는다

- 현상: 잘못된 입력이 몰린 뒤 하류 전체 호출이 막힌다.
- 보이는 형태: 하류 지표는 정상(4xx만 증가), 우리 쪽 회로는 OPEN.
- 원인: 기본 설정은 모든 예외를 실패로 센다(실험 C).
- 대처: `ignoreExceptions`(400류, `BulkheadFullException`, `RequestNotPermitted`) 또는 `recordExceptions`로 하류 건강을 뜻하는 예외만 센다.

### 5. 재시도가 바깥에 있어 회로가 너무 빨리 열린다

- 현상: 하류가 잠깐 흔들렸을 뿐인데 회로가 열린다.
- 보이는 형태: 창에 같은 요청의 시도가 여러 건 기록된다.
- 원인: Retry가 CircuitBreaker 바깥(Resilience4j Spring Boot 기본 순서)이라 시도마다 창 한 칸을 채운다. 요청 하나가 실패 3건이 된다.
- 대처: 의도한 순서인지 확인한다. 창·임계를 시도 수 기준으로 다시 계산하거나, 애스펙트 순서(`circuitBreakerAspectOrder` 등)를 바꾼다. 열린 회로의 `CallNotPermittedException`은 재시도 대상에서 뺀다.

## 핵심 문장

- 서킷 브레이커는 하류가 확실히 아플 때 호출 자체를 끊어 우리 자원과 하류의 회복 시간을 지킨다. 대신 줄 것(폴백)은 따로 정해야 한다.
- Resilience4j 2.4.0 기본값은 최근 100건 중 50% 이상 실패면 열고 60초 뒤 10건으로 시험한다. 느린 호출 기준은 60초·100%라 기본으로는 느림을 잡지 못한다.
- 반열림은 Resilience4j에서 허용 건수의 실패율로 판정한다. 실험에서 4건 중 1건 실패는 닫혔고 2건은 다시 열렸다.
- 무엇을 실패로 셀지가 숫자보다 중요하다. 기본은 모든 예외를 세므로 400류를 무시하지 않으면 멀쩡한 하류를 끊는다.
- 작은 창·작은 최소 표본은 플래핑을 부른다. 실패율 30% 하류에서 창 4는 3초에 53~54번 열렸고 창 100은 한 번도 안 열렸다.

## 관련 주제·근거

- 선행
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 재시도와 예산, 브레이커 대신 토큰 버킷을 쓰는 AWS의 선택
- 원본
  - [ops-patterns/02-circuit-breaker](../../ops-patterns/02-circuit-breaker/2-summary.md) — 상태 전이·개수/시간 창 직접 구현, NaN·floorDiv 함정, CircuitBreakerReliefTest(1000건 중 29건만 나감)
- 후속·연결
  - [28-bulkhead](../28-bulkhead/2-summary.md) — 회로가 열리기 전의 느림이 스레드를 말리는 것을 막는다
  - [11-rate-limiter](../11-rate-limiter/2-summary.md) — 같은 슬라이딩 창으로 요청 수를 센다
  - [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md), [35-timeout-design-worksheet](../35-timeout-design-worksheet/2-summary.md)(데코레이터 순서). 히스테리시스 기초는 [systems/Hysteresis](../../systems/Hysteresis/2-summary.md)
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 느림과 죽음을 구분할 수 없다
- 글·문서
  - Michael Nygard, 『Release It!』 2판(Pragmatic, 2018) 「Stability Patterns」 장의 Circuit Breaker 절 — pragprog 목차로 절 위치만 확인, 본문은 열람하지 못했다 [?] <https://pragprog.com/titles/mnee2/release-it-second-edition/>
  - Martin Fowler, "CircuitBreaker", 2014-03-06 — Nygard가 대중화, 실패 임계·half open 시험 호출 <https://martinfowler.com/bliki/CircuitBreaker.html>
  - Resilience4j CircuitBreaker 문서(상태 6개, 창 구현, 설정 기본값 표, AtomicReference·호출 비동기화) <https://resilience4j.readme.io/docs/circuitbreaker> · Spring Boot 애스펙트 순서 <https://resilience4j.readme.io/docs/getting-started-3>
  - Marc Brooker, "Timeouts, retries, and backoff with jitter", Amazon Builders' Library — 브레이커의 modal behavior 비판 <https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/>
  - Envoy "Circuit breaking" 아키텍처 문서·`circuit_breaker.proto`(기본 1024, max_retries 3) <https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking>
- 실험 목록 (코드: scratchpad `rel/06/e10/Cb.java`, Resilience4j 2.4.0 + slf4j-api 1.7.30 jar를 Maven Central에서 받음, JDK 21 temurin `--cpus=2`)
  - 기본값 출력 — `CircuitBreakerConfig.ofDefaults()`
  - A 상태 전이(≥ 비교, 첫 호출이 반열림 전이, 반열림 비율 판정)
  - B 느린 호출만으로 열림
  - C 400류 기본 기록 vs `ignoreExceptions`
  - D 플래핑: 창 4 vs 창 100 (3회 실행)
