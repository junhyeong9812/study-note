# reliability/35-timeout-design-worksheet — 요청 경로 하나에 시간 예산표를 쓰고 설정으로 옮기기 — 정리 (힌트)

## 해결하는 문제

05~09에서 본 규칙(정렬, 전파, 구간 타임아웃, 예산 분배, 취소)을 한 요청 경로에 **동시에** 적용하는 연습이다.\
규칙을 하나씩 알아도, 게이트웨이·서비스·라이브러리 설정이 서로 맞지 않으면 사고가 난다.

```text
 사용자 ──> 게이트웨이(Envoy) ──> 서비스 A ──┬─> 서비스 B (재고)
                                          ├─> DB
                                          └─> 외부 PG (결제 승인)
 흔한 사고: 게이트웨이 1s 타임아웃 < A가 PG를 기다리는 1.5s
           → 사용자는 504, PG는 승인 완료 → 사용자가 다시 결제 → 이중 결제
```

- *예산표(budget sheet)*: 호출 그래프의 각 단계에 시간 몫·per-try·재시도·폴백을 적은 표. 경로마다 합이 상위 예산 이하인지 확인한다.
- *데코레이터 순서*: Resilience4j처럼 장치(재시도·타임리미터·서킷 브레이커)를 함수에 겹겹이 씌울 때 어느 것이 바깥인지. 순서가 동작을 바꾼다.

쉬운 예: 여행 일정표다.
- 비행기 출발(사용자 마감) 시각에서 거꾸로 공항 도착, 택시, 짐 싸기 시간을 뺀다.
- 택시가 안 잡히면 버스(폴백)로 갈 시간까지 남겨 둔다.
- 환전(외부 결제)은 한 번 하면 되돌리기 어렵다. 영수증 번호(멱등 키)를 받아 두면 "했는지 안 했는지" 다시 물어볼 수 있다.

똑같은 구조다.\
실무 예: 결제·주문 API의 게이트웨이(Envoy·Spring Cloud Gateway) 설정과 서비스 안 Resilience4j 설정을 같은 표에서 정하기.

## 동작·원리

### 1. 예산표 — 트리의 경로 합

```text
 사용자 SLO: 결제 API p99 ≤ 3.0 s (예시)
 게이트웨이 route timeout 3.0 s, 재시도 없음(비멱등 POST)
 └─ 서비스 A 데드라인 = 게이트웨이가 준 남은 시간 - 전송 여유 0.1 = 2.9 s
     예약: 응답·폴백 0.2 s                              → 단계 몫 2.7 s
     ├─ B 재고 확인   per-try 0.3 × 2 + 대기 0.05 = 0.65 ┐
     ├─ DB 주문 저장   0.3                               │ 직렬 합 2.45 ≤ 2.7  ✓
     └─ PG 승인       per-try 1.5 × 1 (재시도 없음)  = 1.5 ┘
 검사 1: 경로 합 ≤ 상위 몫            (2.45 ≤ 2.7)
 검사 2: 게이트웨이 > A 안의 최악 시간  (3.0 > 0.1 + 2.45 + 0.2 = 2.75)
 검사 3: per-try × 시도 + 대기 ≤ 그 단계 몫
 검사 4: 결과가 모호한 단계(PG)에 멱등 키·조회·대사 경로가 있는가
```

- 검사 2가 이 노트의 중심이다. 게이트웨이가 먼저 끊으면 A가 PG 결과를 확정해도 사용자에게 전달할 길이 없다.
- 값은 예시다. 실제 값은 각 하류의 지연 분포에서 고른다([08](../08-time-budget-allocation/2-summary.md)).

### 2. Envoy로 옮기기 — 무엇이 어디에 대응하나

| 예산표 칸 | Envoy 설정 | 기본값 / 주의 (Envoy FAQ·router 문서) |
|---|---|---|
| 게이트웨이 전체 | route `timeout` | 15 s. 하류 요청을 다 받은 뒤 시작 |
| 시도 하나 | route `retry_policy.per_try_timeout` | 응답이 하류로 나가기 시작하기 전까지만 적용 |
| 재시도 조건·횟수 | `retry_on`, `num_retries` | `5xx`는 응답 없음(리셋·read timeout)도 포함. 전체 timeout 초과 504는 재시도 안 함 |
| 스트림 무활동 | route `idle_timeout`(= HCM `stream_idle_timeout` 덮어쓰기) | route 값은 기본 미설정. 그때는 HCM `stream_idle_timeout`(기본 5 min)이 적용 |
| 연결 수립 | cluster `connect_timeout` | 5 s, 상류 TLS면 핸드셰이크 포함 |
| 하류에 알려 주는 값 | `x-envoy-expected-rq-timeout-ms` 헤더 | per-try가 있으면 per-try, 없으면 라우트 timeout(1.39.1 소스). 단 per-try ≥ 전체 timeout이면 per-try를 무시하고, 헤징(`hedge_on_per_try_timeout`)을 켜면 전체 값을 쓴다. `suppress_envoy_headers`면 헤더를 안 붙인다. 재시도 때만 이 Envoy의 남은 전체 시간으로 깎는다. 끝에서 끝까지의 남은 시간이 아니다 |

### 3. Resilience4j 순서 — 바깥에서 안쪽으로

```text
 Spring Boot 애너테이션 기본 순서(Resilience4j 문서 "Aspect order"):
   Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( Function ) ) ) ) )
   바깥 ─────────────────────────────────────────────────────────> 안쪽
 의미: 시도 하나 = TimeLimiter로 자른 호출 1번.  서킷 브레이커는 그 결과(타임아웃 포함)를 센다.  재시도가 가장 바깥.
```

- 함수형으로 직접 엮으면 순서를 마음대로 바꿀 수 있고, 그래서 틀릴 수 있다. 아래 실험 B가 두 가지 착오를 보인다.

### 4. 실험 A: Envoy — 게이트웨이 타임아웃 < 결제 시간, 그리고 per-try 재시도

- 구성: 일회용 Docker 네트워크에 Envoy 1.39.1(distroless)과 결제 서비스 흉내(JDK 21 `HttpServer`). 결제 승인에 1500ms. `Idempotency-Key`가 있으면 같은 키는 한 번만 승인하고 두 번째 요청은 첫 결과를 기다려 재생한다.
- 라우트
  - `/short/`: `timeout: 1s`, 재시도 없음.
  - `/retry/`: `timeout: 3.5s`, `retry_on: "5xx"`, `num_retries: 2`, `per_try_timeout: 1s`.

```yaml
- match: { prefix: "/retry/" }
  route:
    cluster: pay
    prefix_rewrite: "/"
    timeout: 3.5s
    retry_policy:
      retry_on: "5xx"
      num_retries: 2
      per_try_timeout: 1s
```

(실험, Envoy 1.39.1 + JDK 21.0.12, curl 8.6.0, 일회용 네트워크, 2026-10-01 — 결제 서비스 시각은 서비스 시작 기준)

```text
== /short/pay timeout 1s
client: HTTP 504 after 1.002924s
charges=1
== /retry/pay per_try 1s x3, 키 없음
client: HTTP 504 after 3.030219s
charges=3
== /retry/pay per_try 1s x3, Idempotency-Key
client: HTTP 200 after 1.514583s
charges=1
```

```text
[pay t=  4002ms] 요청 도착 attempt=null expected-rq-timeout-ms=1000 key=null
[pay t=  5503ms] 결제 승인 완료 #1
[pay t=  5610ms] 응답 쓰기 실패(게이트웨이가 이미 끊음): Broken pipe
[pay t= 11328ms] 요청 도착 attempt=null expected-rq-timeout-ms=1000 key=null
[pay t= 12350ms] 요청 도착 attempt=null expected-rq-timeout-ms=1000 key=null
[pay t= 12829ms] 결제 승인 완료 #1
[pay t= 13354ms] 요청 도착 attempt=null expected-rq-timeout-ms=1000 key=null
[pay t= 13851ms] 결제 승인 완료 #2
[pay t= 14855ms] 결제 승인 완료 #3
[pay t= 20682ms] 요청 도착 attempt=null expected-rq-timeout-ms=1000 key=order-42
[pay t= 21684ms] 요청 도착 attempt=null expected-rq-timeout-ms=1000 key=order-42
[pay t= 21685ms] 같은 키 — 첫 승인 결과를 기다려 재생
[pay t= 22187ms] 결제 승인 완료 #1
```

(서비스 로그의 `응답 쓰기 실패` 줄 일부를 생략했다. `attempt=null`: 이 설정에서는 `x-envoy-attempt-count` 헤더가 붙지 않았다 — virtual host `include_request_attempt_count`의 기본값이 false다(Envoy `route_components.proto`). 사실 점검 재실행 결과도 같았다: 504 1.00초·승인 1, 504 3.04초·승인 3, 200 1.51초·승인 1.)

- 관찰 1 — `/short/`: 사용자는 1.0초에 504를 받았다. 결제 서비스는 1.5초에 **승인을 완료**했다. 응답은 버려졌다.
- 관찰 2 — `/retry/` 키 없음: per-try 1초마다 Envoy가 새 시도를 보냈다. 사용자는 3.03초에 504, 결제는 **3번** 승인됐다. 첫 시도가 끝나기 전에 다음 시도가 도착하므로 서버는 셋을 동시에 처리했다.
- 관찰 3 — 같은 설정에 `Idempotency-Key`: 두 번째 시도가 첫 승인을 기다려 재생했고, 1.51초에 200, 승인은 1번이다. 멱등 키가 재시도를 안전하게 만들었다.
- 관찰 4 — 상류가 받은 `x-envoy-expected-rq-timeout-ms`는 전체 3.5초가 아니라 per-try 값 `1000`이었다. 문서는 라우트 timeout에서 온다고만 적지만, Envoy 1.39.1 소스(`router.cc` `setTimeoutHeaders`)는 per-try가 있으면(전체보다 작고 헤징이 꺼진 이 설정처럼) per-try를 쓰고, 재시도 때는 `min(per-try, 전체 - 이 Envoy 안에서 흐른 시간)`으로 깎는다. 세 번째 시도(약 2초 경과)에도 남은 1.5초 > 1초라 1000이었다. 이 Envoy 앞에서 쓴 시간은 빠지지 않으므로 끝에서 끝까지의 "남은 시간"은 아니다.

### 5. 실험 B: Resilience4j 2.4.0 — 데코레이터 순서

- 하류: 1·2번째 호출은 1500ms, 3번째부터 100ms. TimeLimiter 1000ms(`cancelRunningFuture` 기본 true), Retry 최대 시도 3번(`maxAttempts=3`, 첫 호출 포함)·대기 100ms.
- A = `Retry(TimeLimiter(call))`, B = `TimeLimiter(Retry(call))`.
- 서킷 브레이커 비교에는 인터럽트에 반응하지 않는 하류(블로킹 소켓 흉내, 항상 1500ms)를 썼다.

```java
// A: 시도마다 1초
Callable<String> perTry = TimeLimiter.decorateFutureSupplier(tl, () -> ex.submit(Order::downstream));
Retry.decorateCallable(retry, perTry).call();
// B: 재시도 전체가 1초
TimeLimiter.decorateFutureSupplier(tl, () -> ex.submit(Retry.decorateCallable(retry, Order::downstream))).call();
// 서킷 브레이커: CB(TL(call)) vs TL(CB(call))
```

(실험, Resilience4j 2.4.0 + JDK 21.0.12, 컨테이너 `--cpus=2`, 2026-10-01)

```text
TimeLimiter 기본값: TimeLimiterConfig{timeoutDuration=PT1ScancelRunningFuture=true}
t=    0ms == A: Retry(TimeLimiter(call))
t=   45ms   하류 호출 #1 시작(1500ms)
t= 1039ms   하류 호출 #1 인터럽트로 중단
t= 1147ms   하류 호출 #2 시작(1500ms)
t= 2147ms   하류 호출 #2 인터럽트로 중단
t= 2247ms   하류 호출 #3 시작(100ms)
t= 2348ms   하류 호출 #3 완료
t= 2350ms A 결과: ok#3
t= 4361ms A: 하류 호출 3번, 끝까지 돈 호출 1번
t=    0ms == B: TimeLimiter(Retry(call))
t=    3ms   하류 호출 #1 시작(1500ms)
t= 1003ms   하류 호출 #1 인터럽트로 중단
t= 1003ms B 실패: java.util.concurrent.TimeoutException: TimeLimiter 'UNDEFINED' recorded a timeout exception.
t= 1104ms   하류 호출 #2 시작(1500ms)
t= 2605ms   하류 호출 #2 완료
t= 3005ms B: 하류 호출 2번, 끝까지 돈 호출 1번
CircuitBreaker 기본값: failureRateThreshold=50.0 slowCallDurationThreshold=PT1M slowCallRateThreshold=100.0 minimumNumberOfCalls=100
t= 4049ms CB(TL(call)) (인터럽트 무시 하류): 호출자는 3번 모두 TimeoutException, CB가 센 실패 3 · 성공 0 · 느린 호출 0
t= 4004ms TL(CB(call)) (인터럽트 무시 하류): 호출자는 3번 모두 TimeoutException, CB가 센 실패 0 · 성공 3 · 느린 호출 0
```

- 관찰 1 — A: 시도마다 1초로 잘리고 재시도해 3번째에 성공했다(2.35초).
- 관찰 2 — B: 재시도 **전체**가 1초에 묶여 1.0초에 실패했다. 커리큘럼의 `[?]`("재시도 전체가 한 번의 타임아웃에 묶인다")가 이 환경에서 확인됐다.
- 관찰 3 — B에는 더 나쁜 것이 있다. 호출자가 실패를 받은 **뒤에** 안쪽 Retry가 인터럽트로 끝난 1번째 시도를 실패로 보고 2번째 시도를 시작해(1104ms) 끝까지 돌렸다. 아무도 기다리지 않는 재시도다.
- 관찰 4 — `CB(TL(call))`: 타임아웃을 실패로 셌다(실패 3). `TL(CB(call))`: 호출자는 3번 다 타임아웃을 받았는데 서킷 브레이커는 **성공 3**으로 셌다. 인터럽트를 무시한 하류가 1.5초 뒤 정상 반환했기 때문이다. 이 순서라면 느린 하류를 계속 호출한다.
- 관찰 5 — 서킷 브레이커 기본 `slowCallDurationThreshold`는 60초다(`PT1M`). 1.5초 호출은 "느린 호출"로도 세지 않았다. 느린 호출로 회로를 열려면 이 값을 타임아웃 근처로 낮춘다.

## 쓰이는 자료구조·알고리즘

- **호출 트리와 경로 합** — 예산표는 트리다. 각 루트→잎 경로에서 직렬 구간의 합(병렬은 최댓값)이 상위 몫 이하인지 검사한다.
- **데코레이터 = 함수 합성** — `Retry(TL(f))`와 `TL(Retry(f))`는 같은 부품의 다른 합성이다. 바깥 장치는 안쪽 전체를 한 번의 호출로 본다.
- **슬라이딩 윈도 실패율(서킷 브레이커)** — 최근 N개 호출의 실패·느린 호출 비율. 무엇을 "실패"로 세느냐가 위치에 따라 바뀐다(실험 B 관찰 4). [10-circuit-breaker](../10-circuit-breaker/2-summary.md).
- **멱등 키 저장소** — 키 → (진행 중 / 결과). 같은 키의 동시 요청은 첫 결과를 기다려 재생한다(실험 A의 `putIfAbsent` + `CompletableFuture`). 원본 [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 워크시트 순서

1. 경로를 그린다: 게이트웨이 → 서비스 → 하류 각각, 직렬·병렬 표시.
2. 맨 위 예산: 사용자 SLO. 게이트웨이 timeout = SLO 근처.
3. 서비스 데드라인 = 게이트웨이 timeout - 전송 여유. 서비스 안 최악 시간 < 게이트웨이 timeout(검사 2).
4. 예약: 응답·폴백.
5. 단계마다: 하류 p99.x → per-try, 멱등이면 재시도 횟수, 단계 몫 = 시도 × per-try + 대기.
6. 경로 합 검사(검사 1·3).
7. 결과가 모호해질 수 있는 단계(외부 효과)에 표시: 멱등 키, 상태 조회 API, 대사(검사 4).
8. 설정으로 옮긴다: Envoy(표 2), Resilience4j(순서 3).
9. 실험으로 확인: 하류를 일부러 느리게 해 504가 나는 경로에서 부작용이 몇 번 일어나는지 센다(실험 A처럼).

### 2. 예산표 양식

| 단계 | 하류 p99 / p99.9 | per-try | 시도 | 대기 | 단계 몫 | 멱등? | 모호할 때 경로 |
|---|---|---|---|---|---|---|---|
| 게이트웨이 → A | — | 3.0 s(전체) | 1 | — | 3.0 s | 아니오(POST) | — |
| A → B 재고 | 120 / 280 ms | 300 ms | 2 | 50 ms | 650 ms | 예(조회) | — |
| A → DB 저장 | 80 / 250 ms | 300 ms | 1 | — | 300 ms | 아니오 | 트랜잭션 롤백 |
| A → PG 승인 | 900 / 1400 ms | 1.5 s | 1 | — | 1.5 s | 멱등 키로 예 | 키로 상태 조회 → 대사 |
| 예약(응답·폴백) | | | | | 200 ms | | |

(수치는 모두 예시)

### 3. 설정 — Envoy

```yaml
routes:
- match: { prefix: "/api/payments", headers: [{ name: ":method", string_match: { exact: "POST" } }] }
  route:
    cluster: service_a
    timeout: 3s               # 검사 2: A 안의 최악(2.75s)보다 길게
    # 비멱등 POST: 게이트웨이 재시도 없음 (재시도는 멱등 키를 아는 A가 판단)
- match: { prefix: "/api/" }
  route:
    cluster: service_a
    timeout: 1s
    retry_policy: { retry_on: "5xx,reset,connect-failure", num_retries: 1, per_try_timeout: 0.4s }
clusters:
- name: service_a
  connect_timeout: 0.25s
```

### 4. 설정 — Resilience4j(서비스 A, PG 호출)

```java
TimeLimiter tl = TimeLimiter.of(TimeLimiterConfig.custom()
        .timeoutDuration(Duration.ofMillis(1500))     // per-try
        .cancelRunningFuture(true).build());
CircuitBreaker cb = CircuitBreaker.of("pg", CircuitBreakerConfig.custom()
        .slowCallDurationThreshold(Duration.ofMillis(1200))   // 기본 60s → 타임아웃 근처로
        .build());
Retry retry = Retry.of("pg", RetryConfig.custom().maxAttempts(1).build()); // PG는 재시도 안 함(키로 조회만)

// 바깥 → 안쪽: Retry ( CircuitBreaker ( TimeLimiter ( call ) ) )
Callable<Approval> perTry = TimeLimiter.decorateFutureSupplier(tl,
        () -> executor.submit(() -> pg.approve(orderId, idempotencyKey)));
Callable<Approval> guarded = CircuitBreaker.decorateCallable(cb, perTry);
Callable<Approval> call = Retry.decorateCallable(retry, guarded);
```

- `executor.submit` + `Future` 경로를 쓴다. CompletionStage 경로는 타임아웃 뒤 원래 작업을 취소하지 않는다([09](../09-cancellation-propagation/2-summary.md) 5절).
- PG 호출 타임아웃(1.5s)은 HTTP 클라이언트 자체에도 건다. TimeLimiter는 바깥 방어선이다.
- 타임아웃이 나면 결과를 "모름"으로 기록하고, 같은 `idempotencyKey`로 상태를 조회한다. 그래도 모르면 대사로 넘긴다.

### 5. 진단

```bash
# Envoy: 상류 타임아웃·재시도 횟수 (admin 포트, 클러스터 이름은 예시)
curl -s localhost:9901/stats | grep -E 'cluster.service_a.upstream_rq_(timeout|per_try_timeout|retry)'
# 504인데 결제됨: 같은 주문의 게이트웨이 504 시각과 PG 승인 시각을 맞대어 본다
```

## 장애 시나리오와 대처

### 1. 게이트웨이 타임아웃 < 서비스 타임아웃 → 사용자는 504, 결제는 됨 (⚠ 커리큘럼)

- 현상: "결제 실패라고 떠서 다시 했더니 두 번 빠져나갔다"는 문의.
- 보이는 형태: 게이트웨이 액세스 로그 504(응답 플래그 `UT`)와 클러스터 카운터 `upstream_rq_timeout` 증가, 같은 주문의 PG 승인 기록, 서비스 로그의 응답 쓰기 실패(실험 A `/short/`: 504 at 1.0s, 승인 at 1.5s).
- 원인: 검사 2 위반. 서비스가 결과를 확정하기 전에 게이트웨이가 끊었다.
- 대처: 게이트웨이 timeout > 서비스 안 최악 시간. 결제 요청에 멱등 키를 받아, 재결제가 같은 키면 재생되게 한다. 504 뒤 클라이언트는 "확인 중" 상태로 조회한다.

### 2. 게이트웨이 per-try 재시도가 비멱등 결제를 여러 번 실행

- 현상: 지연이 길어진 날 한 주문에 승인이 2~3건.
- 보이는 형태: Envoy `upstream_rq_per_try_timeout`·`upstream_rq_retry` 증가, 결제 서비스에 같은 요청이 1초 간격으로 도착(실험 A: 승인 3건).
- 원인: 비멱등 POST 라우트에 `retry_on`이 걸려 있다. per-try timeout은 상류가 아직 처리 중인데 새 시도를 보낸다.
- 대처: 비멱등 라우트는 게이트웨이 재시도 끔. 재시도가 필요하면 멱등 키를 강제한다(실험 A: 키가 있으면 승인 1건).

### 3. 데코레이터 순서 착오(Retry가 TimeLimiter 안쪽) → 재시도 전체가 한 번의 타임아웃에 묶임 (⚠ 커리큘럼)

- 현상: Retry를 시도 3번으로 설정했는데 일시 지연에도 바로 실패한다. 실패 뒤에도 하류 호출 로그가 이어진다.
- 보이는 형태: 실패까지 걸린 시간이 TimeLimiter 값 하나(실험 B: 1.0초). 실패 뒤 하류에 새 시도 도착(1104ms).
- 원인: `TimeLimiter(Retry(call))`. 바깥 TimeLimiter가 재시도 묶음 전체를 자르고, 안쪽 Retry는 인터럽트를 실패로 보고 재시도를 이어 간다.
- 대처: `Retry(… TimeLimiter(call))`. Spring 애너테이션 기본 순서가 이 모양이다. 함수형으로 엮을 때 순서를 테스트로 고정한다.

### 4. 서킷 브레이커가 타임아웃을 실패로 세지 않는다 → 느린 하류를 계속 호출 (⚠ 커리큘럼)

- 현상: 하류가 느려져 사용자 요청이 줄줄이 타임아웃인데 회로가 열리지 않는다.
- 보이는 형태: TimeLimiter 타임아웃 지표는 높고, 서킷 브레이커의 실패율은 0%에 가깝다(실험 B: `TL(CB(call))` 성공 3).
- 원인: 서킷 브레이커가 TimeLimiter **안쪽**에 있어, 늦게라도 정상 반환한 호출을 성공으로 센다. 기본 `slowCallDurationThreshold` 60초라 느린 호출로도 안 센다.
- 대처: `CB(TL(call))` 순서. `slowCallDurationThreshold`를 타임아웃 근처로. 실패로 셀 예외 목록에 `TimeoutException`이 빠지지 않았는지 확인.

### 5. 결과가 모호한 단계에 경로가 없다

- 현상: PG 타임아웃 건이 "실패"로 처리돼 고객 환불 문의와 정산 불일치가 매일 생긴다.
- 원인: 검사 4 누락. 타임아웃 = 실패로 단정했다.
- 대처: "모름" 상태, 멱등 키로 상태 조회, 일 단위 대사. [distributed/03](../../distributed/03-partial-failure-and-timeouts/2-summary.md)의 "모름" 처리 세 길.

## 핵심 문장

- 예산표는 호출 트리의 경로 합이다. 경로 합 ≤ 상위 몫, per-try × 시도 + 대기 ≤ 단계 몫, 게이트웨이 > 서비스 안 최악 시간, 모호한 단계엔 멱등 키·조회·대사.
- 실험에서 게이트웨이 1초 < 결제 1.5초는 사용자 504 + 결제 승인 1건, per-try 1초·재시도 2회(시도 3번)는 504 + 승인 3건이었다. 멱등 키를 붙이자 200 + 승인 1건이었다.
- Resilience4j는 `Retry(CircuitBreaker(TimeLimiter(call)))` 순서가 기본이다. `TimeLimiter(Retry(call))`는 재시도 전체를 1초에 묶고, 호출자가 포기한 뒤에도 재시도를 계속했다.
- 서킷 브레이커가 TimeLimiter 안쪽에 있으면 호출자가 본 타임아웃을 성공으로 셀 수 있다. 실험에서 실패 0·성공 3이었다.
- Envoy가 상류에 주는 `x-envoy-expected-rq-timeout-ms`는 끝에서 끝까지의 남은 시간이 아니다. 실험에서는 per-try 값이 실렸다.

## 관련 주제·근거

- 선행
  - [07-timeout-taxonomy-by-layer](../07-timeout-taxonomy-by-layer/2-summary.md) · [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md) · [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md)
  - [10-circuit-breaker](../10-circuit-breaker/2-summary.md)
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md)
  - [api-design/05-idempotency-keys](../../api-design/05-idempotency-keys/2-summary.md) · [13-idempotency](../13-idempotency/2-summary.md) · 원본 [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
- 연결
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 타임아웃 뒤 "모름"과 결제
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 재시도 예산
- 문서·소스
  - Envoy FAQ "How do I configure timeouts?" — route timeout·per_try_timeout·idle_timeout·connect_timeout <https://www.envoyproxy.io/docs/envoy/latest/faq/configuration/timeouts>
  - Envoy router filter 문서 — `retry_on: 5xx`(응답 없음 포함, 전체 timeout 504는 재시도 안 함), `x-envoy-expected-rq-timeout-ms`, `x-envoy-upstream-rq-per-try-timeout-ms`
  - Resilience4j 문서 Spring Boot "Aspect order" — `Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( Function ) ) ) ) )` <https://resilience4j.readme.io/docs/getting-started-3>
  - Resilience4j 2.4.0 소스 `TimeLimiterImpl`·`TimeLimiterConfig`, `CircuitBreakerConfig.ofDefaults()`(실험 출력: failureRateThreshold 50, slowCallDurationThreshold 60s, minimumNumberOfCalls 100)
- 실험 목록
  - A `envoy/envoy.yaml` + `envoy/Pay.java` — Envoy 1.39.1 distroless(실험 후 이미지 삭제), 일회용 네트워크, `/short/`(timeout 1s)·`/retry/`(3.5s, per-try 1s, 5xx × 2) × 멱등 키 유무, curl 8.6.0 컨테이너로 호출
  - B `Order.java` — Resilience4j 2.4.0, Retry/TimeLimiter 순서 A·B, CircuitBreaker 위치 두 가지(인터럽트 무시 하류). JDK 21.0.12 컨테이너 `--cpus=2`
