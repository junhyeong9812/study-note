# reliability/34-tail-latency-and-stragglers — 팬아웃의 꼬리 지연 증폭과 hedged·tied request — 정리 (힌트)

## 해결하는 문제

서버 한 대의 p99가 1초라는 것은 "100건 중 1건만 느리다"는 뜻이다. 그런데 요청 하나가 서버 100대에 동시에 물어보고 **전부의 답을 기다린다면**, 사용자 요청의 대부분이 그 1초를 겪는다.

```text
 사용자 요청 1개 ──> 루트 ──┬──> 리프 1   10ms
                           ├──> 리프 2   10ms
                           ├──> ...
                           └──> 리프 100 1000ms  ← 하나만 느려도
 루트 응답 = 가장 느린 리프 = 1000ms
```

- *팬아웃(fan-out)*: 요청 하나를 여러 하위 서버로 펼쳐 보내는 것. 검색(샤드마다 질의), 피드 조립, 마이크로서비스 집계에서 흔하다.
- *꼬리 지연(tail latency)*: 지연 분포의 높은 분위수(p99·p99.9) 쪽 값.
- *straggler(낙오자)*: 여러 대에 나눈 일 중 유독 늦게 끝나는 한 대.

쉬운 예: 단체 사진이다. 한 사람이 눈을 감을 확률이 1%여도, 100명이 찍으면 "아무도 눈을 안 감은" 사진은 약 37%뿐이다.

똑같은 구조다.\
실무 예: 검색 결과 조립, 장바구니 페이지가 서비스 20개 호출, 분산 쿼리 엔진의 스캐터-개더, 복제 쓰기 `acks=all`.\
기초(straggler의 원인 목록, quorum으로 기다리지 않기, Kafka·BookKeeper·Redpanda 비교)는 원본 [systems/straggler](../../systems/straggler/2-summary.md) 「1~5절」에 있다. 이 노트는 확률 계산을 실험으로 확인하고, hedged·tied request의 효과와 **역효과**를 실측한다.

## 동작·원리

### 1. 증폭 — 1 − (1 − q)^N

```text
 리프 하나가 느릴 확률 q, 리프 N개 전부를 기다림
 사용자 요청이 느릴 확률 = 1 − (1 − q)^N

 q = 1%     N=1: 1%   N=10: 9.6%   N=100: 63%   N=1000: ≈100%
 q = 0.01%  N=2000: 18%
```

- Dean–Barroso(CACM 2013) "Amplified By Scale"의 예: 보통 10ms, p99가 1초인 서버. 서버 100대에 병렬로 물으면 사용자 요청의 63%가 1초를 넘는다. 1만 건 중 1건만 1초를 넘는 서버라도 2000대면 사용자 요청의 거의 5분의 1이 1초를 넘는다.
- 커리큘럼의 ⚠ "100개 팬아웃 → p99가 사실상 중앙값 경험": N=100이면 사용자 요청의 **중앙값(p50)이 리프의 p99(1초)** 가 된다(아래 실험).
- 같은 논문 Table 1(구글 실제 서비스): 루트에서 잰 단일 리프 요청 p99는 10ms, 전체 리프 완료 p99는 140ms, 95% 리프 완료 p99는 70ms. 가장 느린 5%를 기다리는 것이 전체 p99의 절반을 차지했다.

### 실험 1: 팬아웃 증폭 (몬테카를로)

```java
// 리프: 99%는 10ms, 1%는 1000ms. 루트는 N개 전부를 기다린다 → 최댓값
for (int r = 0; r < reqs; r++) {
    long mx = 0;
    for (int i = 0; i < n; i++) mx = Math.max(mx, rnd.nextDouble() < 0.01 ? 1000 : 10);
    lat[r] = mx;
}
```

(실험, Docker eclipse-temurin:21-jdk(Temurin 21.0.12) `--cpus=2`, 요청 2만 건 시뮬레이션, 시드 42, 2026-10-01)

```text
  N   1초 넘은 요청 비율(시뮬)  1-0.99^N   요청 p50   요청 p99
   1                    1.0%       1.0%       10ms       10ms
  10                    9.3%       9.6%       10ms     1000ms
 100                   63.1%      63.4%     1000ms     1000ms
1000                  100.0%     100.0%     1000ms     1000ms
p=1/10000, N=2000: 시뮬 18.3%, 1-(1-0.0001)^2000 = 18.1%
```

- 관찰: N=100에서 요청 p50이 1000ms다. 리프 기준으로는 "1%의 꼬리"였던 것이 사용자 기준으로는 **보통 경험**이 됐다.
- 시뮬과 식이 1%p 이내로 맞는다.

### 2. 왜 리프가 느려지나 — 상시 현상

- 논문 "Why Variability Exists?" 절의 원인: 공유 자원 경합, 백그라운드 데몬, 전역 자원 경합(스위치·파일 시스템), 유지 작업(로그 압축·GC), 다층 큐잉, CPU 전력·열 제한, SSD 내부 가비지 컬렉션, 절전 모드 복귀.
- 원인 목록과 예방(디스크 분리·힙 밖 데이터)은 원본 [straggler](../../systems/straggler/2-summary.md) 「2·4⑤절」.
- 그래서 꼬리를 "없애기"보다 **꼬리를 견디는(tail-tolerant)** 기법이 필요하다는 것이 논문의 주장이다.

### 3. hedged request — 늦으면 한 번 더

```text
 클라이언트 ──요청──> 복제본 A ............(느림)............ 응답(버림)
            │ d ms 지나도 응답 없음
            └──요청──> 복제본 B ──응답(채택) → A의 남은 요청 취소
```

- 논문: 가장 적절해 보이는 복제본에 먼저 보내고, 짧은 지연 뒤 다른 복제본에 두 번째 요청을 보낸다. 첫 결과가 오면 나머지를 취소한다.
- 지연 d 고르기: 논문은 "이 종류 요청의 p95 예상 지연이 지나도 응답이 없으면" 보내라고 한다. 그러면 추가 부하가 약 5%로 묶인다.
- 논문의 수치: BigTable 100대에 걸친 1000개 키를 읽는 구글 벤치마크에서 10ms 뒤 hedge를 보내자 p99.9가 1,800ms → 74ms로 줄었고, 요청은 2%만 늘었다.
- 조건: 같은 요청이 두 번 실행될 수 있다. **멱등한 요청**(읽기, 또는 멱등 키가 있는 쓰기)에만 쓴다(→ [13-idempotency](../13-idempotency/2-summary.md)).

### 4. tied request — 둘 다 큐에 넣되, 시작하면 서로 취소

```text
 클라이언트 ──요청(짝=B)──> A 큐 [ x x 요청 ]
            ──요청(짝=A)──> B 큐 [ 요청 ]  ← B가 먼저 실행 시작 → A에 "취소" 전송
 A가 꺼낼 때 이미 취소됨 → 건너뜀
```

- 논문: 지연 변동의 큰 원인은 **실행 전 큐 대기**다. 실행이 시작되면 완료 시간 변동은 크게 준다. 그래서 두 서버 큐에 동시에 넣고, 먼저 실행을 시작한 쪽이 짝에게 취소를 보낸다.
- 두 큐가 다 비어 있으면 둘 다 동시에 시작할 수 있다. 논문은 두 번째 요청을 평균 네트워크 지연의 2배(1ms 이하)만큼 늦게 보내라고 한다.
- 논문 Table 2: 클러스터 파일 시스템에서 1ms 뒤 tied request를 보내 중앙값 16%, p99.9 약 40% 감소, 디스크 사용 증가는 1% 미만.

### 실험 2: hedge·tied의 효과와 역효과

- 복제본 2개, 각각 단일 스레드 큐. 서비스 시간: 99%는 2ms, 1%는 60ms(간섭 흉내). 요청은 무작위 복제본으로 가고, 도착률 고정(open)으로 6초.
- 정책: none / hedge@10ms(10ms 지나면 다른 복제본에 사본, 먼저 끝난 쪽이 나머지 취소) / hedge@0ms(처음부터 둘 다) / tied@1ms(1ms 뒤 사본, 한쪽이 **실행을 시작하면** 다른 쪽은 건너뜀).

```java
Runnable job = () -> {
    if (r.done.isDone()) return;                                // 이미 응답됨 → 건너뜀
    if (tied && !r.started.compareAndSet(false, true)) return;  // 짝이 이미 시작 → 건너뜀
    executed.incrementAndGet();
    LockSupport.parkNanos(u < 0.01 ? 60_000_000L : 2_000_000L); // 서비스 시간
    if (r.done.complete(System.nanoTime()))
        for (Future<?> f : r.copies) f.cancel(false);           // 먼저 끝난 쪽이 나머지 취소
};
r.copies.add(rep[first].submit(job));
if (!policy.equals("none")) {
    Runnable second = () -> { if (!r.done.isDone()) r.copies.add(rep[1 - first].submit(job)); };
    if (d == 0) second.run(); else timer.schedule(second, d, TimeUnit.MILLISECONDS);
}
```

(실험, 같은 환경, 정책마다 별도 JVM — 2회 실행, 값은 두 번째 실행. 첫 실행의 400건/s 결과는 각 분위수가 ±4ms 안에서 비슷했다)

```text
none       rate=400/s n=2400  p50=   2.3ms p95=  62.9ms p99= 117.0ms p99.9=  165.9ms  실제 실행 2400건(요청 대비 +0.0%)
hedge@10ms rate=400/s n=2400  p50=   2.4ms p95=  31.5ms p99=  51.7ms p99.9=   60.3ms  실제 실행 2481건(요청 대비 +3.4%)
hedge@0ms  rate=400/s n=2400  p50=   2.3ms p95=  47.0ms p99=  56.3ms p99.9=   61.5ms  실제 실행 3899건(요청 대비 +62.5%)
tied@1ms   rate=400/s n=2400  p50=   2.3ms p95=  20.1ms p99=  60.2ms p99.9=   66.6ms  실제 실행 2400건(요청 대비 +0.0%)
none       rate=600/s n=3601  p50=  11.8ms p95= 106.2ms p99= 137.8ms p99.9=  160.7ms  실제 실행 3601건(요청 대비 +0.0%)
hedge@10ms rate=600/s n=3601  p50=  17.1ms p95=  87.0ms p99= 115.5ms p99.9=  128.5ms  실제 실행 3836건(요청 대비 +6.5%)
hedge@0ms  rate=600/s n=3601  p50=1121.6ms p95=2093.4ms p99=2226.5ms p99.9= 2241.5ms  실제 실행 5875건(요청 대비 +63.1%)
tied@1ms   rate=600/s n=3601  p50=   6.3ms p95=  67.6ms p99=  89.2ms p99.9=  113.7ms  실제 실행 3601건(요청 대비 +0.0%)
```

- 사실 점검 재실행(같은 명령, 2회, 부하 평균 약 14의 공유 호스트): 경향은 같고 값은 실행마다 다르다. 600건/s none의 p99는 124.5~195.4ms, hedge@10ms의 추가 실행은 +8.2~8.3%, hedge@0ms의 p50은 1,100~1,104ms, 400건/s hedge@10ms의 p99는 49.9~50.1ms였다.
- 복제본 사용률(계산): 평균 서비스 시간 0.99×2 + 0.01×60 = 2.58ms. 400건/s면 복제본당 200건/s × 2.58ms ≈ 52%, 600건/s면 약 77%.
- 관찰 1 — 400건/s: hedge@10ms가 p99를 117 → 52ms로 줄였고, 추가 실행은 3.4%였다. 논문의 "적은 추가 부하로 큰 꼬리 감소"와 같은 모양이다.
- 관찰 2 — hedge@0ms는 실행이 +62~63% 늘었다. 400건/s에서는 견뎠지만, 600건/s에서는 복제본 사용률이 77% × 1.63 ≈ 125%로 100%를 넘어 **큐가 무한히 자랐다**. p50이 11.8ms → 1,121ms가 됐다. 커리큘럼의 ⚠ "hedging 과다 → 부하 2배"가 이것이다(여기서는 큐에서 취소된 사본이 있어 2배가 아닌 1.6배).
- 관찰 3 — 600건/s의 hedge@10ms: p99는 138 → 116ms로 줄었지만 p50은 11.8 → 17.1ms로 **늘었다**(재실행에서도 p50 14.3 → 23.3ms, 9.8 → 20.5ms로 같은 방향). 추가 부하(+6.5%, 재실행 +8.2~8.3%)가 이미 바쁜 큐를 더 길게 만들었다.
- 관찰 4 — tied@1ms: 실제 실행이 요청 수와 같다(+0%). 600건/s에서 p50·p95·p99가 모두 none보다 낮다. 큐 대기를 줄이는 데 효과적이다.
- 관찰 5 — 다만 tied의 p99(400건/s에서 60ms)는 hedge@10ms(52ms)보다 높다. 한쪽이 실행을 **시작한 뒤** 60ms 간섭에 걸리면 짝이 이미 취소돼 구해 줄 수 없다. tied는 "큐 대기" 꼬리를, hedge는 "실행 중 간섭" 꼬리를 줄인다(해석).

### 5. 그 밖의 꼬리 견디기 기법 (논문 목록)

| 기법 | 한 줄 |
|---|---|
| micro-partitions | 머신 수보다 훨씬 많은 파티션으로 쪼개 부하 균형·빠른 복구 |
| selective replication | 뜨거운 파티션만 복제본을 더 둔다 |
| latency-induced probation | 느린 머신을 잠시 제외하고 그림자 요청으로 회복을 확인 |
| good enough | 검색 등에서 충분한 비율의 리프가 답하면 나머지를 기다리지 않는다 |
| canary requests | 먼저 한두 리프에만 보내 보고 이상 없으면 전체로 펼친다 |

## 쓰이는 자료구조·알고리즘

- **백분위 추정**: hedge 지연 d를 "최근 p95"로 잡으려면 분위수를 온라인으로 추정해야 한다. HdrHistogram·t-digest·슬라이딩 윈도 히스토그램(→ [19-performance-measurement](../19-performance-measurement/2-summary.md) 「쓰이는 자료구조」).
- **최댓값 분포**: N개 독립 지연의 최댓값의 CDF = F(x)^N. 위 1 − (1 − q)^N은 그 특수한 경우다. 꼬리 부등식은 [math/08-expectation-variance-tails](../../math/README.md)(미작성).
- **타이머 휠·지연 큐**: 요청마다 "d ms 뒤 hedge" 타이머를 단다. 실험은 `ScheduledExecutorService`(내부 지연 큐 = 힙)로 구현했다.
- **취소 가능한 future**: 첫 응답에서 나머지를 `cancel` — 큐에 남은 작업은 꺼낼 때 건너뛴다(`FutureTask`가 취소 상태면 실행하지 않는다). 실행 중인 작업은 협조적 취소가 필요하다(→ [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md)).
- **CAS 플래그**: tied request의 "누가 먼저 시작했나"는 `compareAndSet` 하나로 정한다. 서버 간이면 취소 메시지로 대신한다.
- **토큰 버킷(재시도 예산)**: hedge 비율 상한. gRPC A6의 `retryThrottling`도 hedging에 적용된다. 다만 그 토큰은 **실패**(재시도 가능·non-fatal 상태 코드)로 줄어든다. 느리지만 성공하는 과부하에서는 hedge가 줄지 않으므로 별도 비율 상한이 필요하다(A6 "Throttling Retry Attempts and Hedged RPCs"의 해석, → [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 먼저 측정 — 사용자 경로의 p99와 리프의 p99를 나란히

```promql
# 리프 서비스 p99 vs 루트 p99 (지표 이름은 예시)
histogram_quantile(0.99, sum by (le) (rate(leaf_request_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(root_request_seconds_bucket[5m])))
```

- 루트 p99가 리프 p99보다 훨씬 크면 팬아웃 증폭이다. 1 − (1 − q)^N으로 예상치를 계산해 비교한다.

### 2. 순서 — 싼 것부터

1. 팬아웃 줄이기: 꼭 전부 기다려야 하나? "good enough"(일부 결과로 응답), 캐시, 사전 집계.
2. 정족수로 기다리기: 복제 쓰기라면 과반만 기다린다(원본 straggler ① Quorum).
3. hedged request: **멱등한 읽기**부터. d = 최근 p95 근처, 추가 요청 비율 상한을 둔다.
4. tied request·큐 길이 기반 선택: 서버 쪽 협조가 필요하다.
5. 느린 인스턴스 제외: Envoy outlier detection, latency-induced probation.

### 3. 코드 — Java로 hedge 하나

```java
// 첫 요청 → d 뒤에도 미완료면 다른 복제본에 한 번 더 → 먼저 온 것 채택, 나머지 취소
static <T> CompletableFuture<T> hedged(Supplier<CompletableFuture<T>> primary,
                                       Supplier<CompletableFuture<T>> backup,
                                       long delayMs, ScheduledExecutorService timer) {
    CompletableFuture<T> result = new CompletableFuture<>();
    CompletableFuture<T> p = primary.get();
    p.whenComplete((v, e) -> { if (e == null) result.complete(v); });
    ScheduledFuture<?> t = timer.schedule(() -> {
        if (result.isDone() || !hedgeBudget.tryAcquire()) return;   // 예산 없으면 hedge 안 함
        CompletableFuture<T> b = backup.get();
        b.whenComplete((v, e) -> { if (e == null) result.complete(v); });
        result.whenComplete((v, e) -> b.cancel(true));
    }, delayMs, TimeUnit.MILLISECONDS);
    result.whenComplete((v, e) -> { t.cancel(false); p.cancel(true); });
    return result;                       // 실패 처리(두 요청 모두 실패할 때 result를 예외로 완료)는 생략
}
```

- 예시 코드다. `hedgeBudget`은 "요청의 X%까지만 hedge" 같은 토큰 버킷이다.
- `CompletableFuture.cancel`은 future를 취소 상태로 만들 뿐이다. JDK Javadoc대로 `mayInterruptIfRunning` 인자는 효과가 없고, 상대 서버의 작업도 멈추지 않는다. 실제 중단은 HTTP·gRPC 클라이언트의 취소 API를 연결하고 서버가 취소를 확인해야 일어난다.

### 4. 제품 설정

```json
{ "methodConfig": [{ "name": [{ "service": "catalog.Catalog", "method": "Get" }],
    "hedgingPolicy": { "maxAttempts": 3, "hedgingDelay": "0.02s", "nonFatalStatusCodes": ["UNAVAILABLE"] } }],
  "retryThrottling": { "maxTokens": 10, "tokenRatio": 0.1 } }
```

- gRPC A6 제안서 기준: `hedgingPolicy`는 첫 RPC를 바로 보내고 `hedgingDelay`마다 하나씩 더 보낸다. `maxAttempts`는 1보다 커야 한다. 클라이언트 쪽 최대값(기본 5, 채널 인자로 바꿀 수 있음)보다 크면 그 최대값으로 취급한다(DNS로 오는 서비스 설정을 믿지 않기 위한 장치). 한 메서드에 retry와 hedging을 함께 쓸 수 없다. 호출 데드라인은 hedge 묶음 전체에 적용된다. 언어별 구현이 hedging을 지원하는지는 버전마다 확인한다 [?].
- Envoy: route의 `hedge_policy.hedge_on_per_try_timeout: true`면 per-try 타임아웃이 나도 원래 요청을 끊지 않고 재시도를 보낸다(여러 요청이 동시에 떠 있게 됨). 효과를 보려면 retry_policy가 있어야 한다(Envoy `route_components.proto`의 HedgePolicy 주석).

## 장애 시나리오와 대처

### 1. 팬아웃 100 → 사용자 중앙값이 리프 p99

- 현상: 각 리프 서비스의 p99 SLO는 다 지키는데 사용자 페이지 p50이 1초다.
- 보이는 형태: 리프 대시보드는 초록, 루트 p50·p99가 리프 p99에 붙어 있다. 실험 1처럼 N=100이면 요청의 63%가 느린 리프를 하나 이상 만난다.
- 원인: 전부 기다리는 팬아웃은 리프 꼬리를 증폭한다.
- 대처: SLO를 루트(사용자) 기준으로 잡고, 리프에는 그보다 훨씬 엄격한 꼬리(p99.9 등)를 배분한다. 팬아웃 축소·부분 결과 응답·hedge.

### 2. hedge 과다 → 부하 폭증, 모두가 느려짐

- 현상: hedge 지연을 0(또는 p50)으로 잡자 평소엔 괜찮다가 트래픽이 조금 오르자 전체 지연이 수 초로 뛴다.
- 보이는 형태: 하류 요청 수가 사용자 요청 수의 1.5~2배. 실험 2의 600건/s hedge@0ms: 실행 +63%, p50 1.1초.
- 원인: hedge가 부하를 늘려 큐가 길어지고, 길어진 큐가 더 많은 hedge를 부른다. 시스템 전체가 느릴 때 hedge는 도움이 안 된다.
- 대처: d를 p95 이상으로. hedge 비율 상한(토큰 버킷). gRPC `retryThrottling`은 실패 비율로만 줄어들어 "느린 성공"에는 작동하지 않으니 따로 둔다. hedge 요청을 낮은 우선순위로 처리(논문 제안). 하류 사용률이 높으면 hedge를 끈다.

### 3. 멱등하지 않은 요청에 hedge → 이중 처리

- 현상: 결제·주문 생성이 가끔 두 번 된다.
- 보이는 형태: 같은 사용자 요청 ID로 하류 로그 두 줄, 두 복제본에서 각각 성공.
- 원인: hedge는 첫 요청이 실패하기 **전에** 사본을 보낸다. 둘 다 끝까지 실행될 수 있다(취소는 실행 중 작업을 보장하지 않는다).
- 대처: hedge 대상은 읽기와 멱등 키가 있는 쓰기만. gRPC도 멱등성 표시 기능은 없다 — 서비스 소유자가 정한다(A6).

### 4. 취소가 전파되지 않아 낭비가 남음

- 현상: hedge 비율은 3%인데 하류 CPU는 30% 늘었다.
- 보이는 형태: 클라이언트는 응답을 받았는데 하류에서 같은 요청이 끝까지 실행된 로그가 남는다.
- 원인: 클라이언트 `cancel`이 하류 서버의 작업 중단으로 이어지지 않는다(큐 제거·실행 중 중단 모두 서버 책임). 또 hedge가 붙는 요청은 d를 넘긴 느린 요청이다. 느림이 간섭이 아니라 요청 자체의 비용(큰 응답·무거운 쿼리) 때문이면, 건수로 3%인 사본이 작업량으로는 훨씬 클 수 있다(해석).
- 대처: 서버가 취소 신호(gRPC 취소, 연결 종료)를 확인하게 한다. 큐에서 꺼낼 때 취소 여부를 본다. tied request처럼 서버 간 취소를 둔다.

## 핵심 문장

- 팬아웃 N개를 전부 기다리면 사용자 요청이 느릴 확률은 1 − (1 − q)^N이다. q=1%, N=100이면 63% — 리프의 p99가 사용자의 중앙값이 된다(실험: p50 1000ms).
- 꼬리는 상시 현상이므로 없애기보다 견딘다: 덜 기다리기, hedge, tied, 느린 노드 제외.
- hedge는 p95 근처 지연 뒤에만 보내면 적은 추가 부하로 꼬리를 크게 줄인다(실험: p99 117 → 52ms, 추가 3.4%).
- 즉시 hedge는 부하를 키워 바쁜 시스템을 무너뜨린다(실험: 600건/s에서 p50 12ms → 1.1초).
- tied request는 실행 시작 시 짝을 취소해 추가 실행 없이 큐 대기 꼬리를 줄인다. 실행 중 간섭에는 hedge가 낫다.
- hedge·tied는 같은 요청이 두 번 실행될 수 있으므로 멱등한 요청에만 쓴다.

## 관련 주제·근거

- 선행
  - [math/08-expectation-variance-tails](../../math/README.md) — 미작성(영역 표 링크)
  - 원본 [systems/straggler](../../systems/straggler/2-summary.md) — straggler 정의·원인·quorum·speculative execution
  - [19-performance-measurement](../19-performance-measurement/2-summary.md) — 분위수와 측정
- 후속·연결
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 재시도 예산, gRPC retryThrottling
  - [13-idempotency](../13-idempotency/2-summary.md) — hedge 대상의 조건
  - [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md) — 취소를 실제로 멈추게 하기
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 과부하 시 hedge 끄기
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 느림과 죽음의 구분
- 논문·문서
  - Dean, Barroso, "The Tail at Scale", Communications of the ACM 56(2), 2013 — "Why Variability Exists?", "Amplified By Scale"(63%·1/5, Table 1), "Hedged requests"(p95, 1,800 → 74ms, 2%), "Tied requests"(Table 2: 중앙값 16%·p99.9 약 40%, 디스크 1% 미만), micro-partitions·selective replication·latency-induced probation·good enough·canary requests <https://www.barroso.org/publications/TheTailAtScale.pdf>
  - gRPC proposal A6 "gRPC Retry Design" — hedgingPolicy(maxAttempts·hedgingDelay·nonFatalStatusCodes), 클라이언트 쪽 기본 최대 5("Maximum Number of Retries" 절), retry/hedging 택일 <https://github.com/grpc/proposal/blob/master/A6-client-retries.md>
  - Envoy `api/envoy/config/route/v3/route_components.proto` — `HedgePolicy.hedge_on_per_try_timeout` <https://github.com/envoyproxy/envoy/blob/main/api/envoy/config/route/v3/route_components.proto>
- 실험 목록
  - Fanout.java — 리프 99% 10ms·1% 1000ms, N=1·10·100·1000 몬테카를로 2만 건 + q=0.01%·N=2000
  - Hedge.java — 복제본 2개 단일 스레드 큐, 서비스 99% 2ms·1% 60ms, open 400·600건/s × 6초, none·hedge@10·hedge@0·tied@1. Docker eclipse-temurin:21-jdk `--cpus=2`, 2회 실행
