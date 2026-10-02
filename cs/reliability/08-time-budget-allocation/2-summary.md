# reliability/08-time-budget-allocation — 총 예산을 단계에 나누는 설계 — 정리 (힌트)

## 해결하는 문제

요청 하나가 쓸 수 있는 시간(총 예산)은 정해져 있다. 그 안에 DB 조회, 하류 호출, 재시도, 폴백, 응답 직렬화가 다 들어가야 한다.\
단계마다 "적당히" 타임아웃을 정하면 합이 예산을 넘거나, 재시도·폴백을 할 시간이 남지 않는다.

```text
 총 예산 1000ms (예시)
 단계 타임아웃을 각자 정함:  DB 500 + 하류 600 + 외부 400 = 1500  > 1000
   → 앞 단계가 느린 날, 마지막 단계는 늘 남은 시간 부족으로 잘린다
   → 폴백을 실행할 시간이 없어 결국 504
```

- *총 예산(total budget)*: 요청이 진입점에 들어온 순간부터 응답을 다 보낼 때까지 허용된 시간. 데드라인 - 도착 시각.
- *단계 예산*: 총 예산 중 한 단계(하류 호출 하나, 쿼리 하나)에 나눠 준 몫.
- *per-try 타임아웃*: 재시도가 있을 때 시도 **한 번**의 상한. 전체 타임아웃과 따로 둔다.

쉬운 예: 점심시간 1시간이다.
- 식당 대기 40분, 식사 30분, 커피 20분을 각자 정하면 합이 90분이다. 늦는 날엔 커피를 못 마신다.
- 대기가 15분을 넘으면 옆 식당(재시도)으로 간다고 정해도, 옆 식당까지 걸어갈 5분을 남겨 두지 않으면 소용없다.
- 마지막 10분은 회사로 돌아오는 시간(응답 직렬화)으로 미리 떼어 둔다.

똑같은 구조다.\
실무 예: 게이트웨이 SLO에서 서비스·DB·외부 PG 호출 타임아웃을 역산하기, Envoy `timeout` + `per_try_timeout`, gRPC 데드라인 아래의 하류 호출 설정.\
"남은 예산을 전파한다"는 기초는 [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md)에 있다. 이 노트는 그 예산을 **어떻게 나누나**를 다룬다.

## 동작·원리

### 1. 예산표 — 위에서 아래로 뺀다

```text
 SLO: 게이트웨이 기준 p99 ≤ 1000ms (예시)
 ┌──────────────────────────────── 총 예산 1000 ────────────────────────────────┐
 │ 예약: 네트워크·직렬화 100 │ 예약: 폴백 100 │ 나머지 800 = 단계에 나눌 몫          │
 │                                           ├─ 인증·검증 50                        │
 │                                           ├─ DB 조회 200                         │
 │                                           ├─ 하류 B: 시도 2회 × per-try 200 + 대기 50 = 450 │
 │                                           └─ 여유 100                            │
 └──────────────────────────────────────────────────────────────────────────────┘
 규칙: 직렬 단계의 합 ≤ 나눌 몫.  병렬 단계는 합이 아니라 최댓값.
```

- 먼저 **예약**을 뺀다. 응답 직렬화·전송, 폴백 실행 시간은 단계가 다 실패한 뒤에도 남아 있어야 한다.
- 직렬 단계는 더한다. 병렬로 부르는 단계(팬아웃)는 가장 긴 것 하나만 센다.
- 재시도가 있는 단계는 `시도 수 × per-try + 대기(백오프) 합`이 그 단계의 몫이다.
- 계산이 안 맞으면 값을 줄이는 대신 **구조**를 바꾼다: 병렬화, 시도 수 줄이기, 단계 하나를 비동기로 빼기, 캐시.

### 2. 단계 타임아웃 = 하류 지연 분포의 백분위 (오탐률을 고른다)

AWS Builders' Library(Brooker)의 방법을 그대로 옮긴다.

```text
 1. 허용할 오탐 타임아웃 비율을 고른다            예: 0.1%
 2. 하류 지연 분포에서 그에 맞는 백분위를 본다      → p99.9
 3. 그 값에서 타임아웃을 시작한다
 예외: 인터넷 너머 클라이언트 → 최악 네트워크 지연을 더한다
       p99.9가 p50에 가까운(분포가 좁은) 서비스 → 여유(padding)를 더한다
```

- *오탐 타임아웃(false timeout)*: 하류는 정상인데 분포의 꼬리에 걸려 타임아웃으로 끊긴 호출. 타임아웃 = p99.9면 정의상 약 0.1%가 이렇게 끊긴다.
- 너무 짧으면(예: p50): 절반이 오탐이다. 재시도가 붙으면 하류 부하가 늘고, 하류 지연이 조금만 올라도 모든 요청이 재시도로 바뀌어 전면 장애로 번질 수 있다(AWS 글이 짚는 두 위험).
- 너무 길면: 기다리는 동안 자원을 계속 잡는다. 05의 스레드 고갈 계산이 그 끝이다.
- 백분위는 **하류 쪽에서 잰 분포**가 기준이다. 평균이 아니다([distributed/03](../../distributed/03-partial-failure-and-timeouts/2-summary.md) 실험 B: 평균의 2배를 타임아웃으로 잡으면 요청의 수 %가 오탐이었다).

### 3. per-try 타임아웃 vs 전체 타임아웃

```text
 per-try 없음 (시도 상한 = 전체 1000)
   시도1 ───────────────────────────── 1000ms 다 씀(멈춘 복제본) ─X   재시도할 시간 0
 per-try 300 + 전체 1000
   시도1 ──── 300 ─X  시도2 ── 90 ─O                               다른 복제본이면 살 수 있다
 per-try 600 × 2 = 1200 > 전체 1000
   시도1 ──────── 600 ─X  시도2 ───── 400(잘림) ─X                    두 번째는 반쪽 시도
```

- per-try가 없으면 첫 시도가 멈춘 복제본에 걸렸을 때 예산을 다 쓴다. "최대 3회"라고 적어도 실제로는 1회다(아래 실험).
- Envoy: route `timeout`이 전체, `retry_policy.per_try_timeout`이 시도 하나다. route `timeout`은 Envoy가 클라이언트 요청을 다 받은 뒤부터 상류(B)의 응답을 다 받을 때까지이고 재시도를 포함한다(RouteAction 문서). 요청을 받는 시간·클라이언트에게 응답을 보내는 시간은 들어가지 않는다. per-try는 응답의 일부가 **클라이언트 쪽(Envoy 용어로 downstream)으로** 나가기 **전**에만 적용된다(Envoy FAQ). 전체 timeout을 넘어 504가 나면 재시도하지 않는다(router 문서 `5xx` 항목).
- per-try가 남은 전체보다 크면 마지막 시도는 잘린다. 시도 수 × per-try + 대기 ≤ 전체로 맞춘다.
- gRPC는 데드라인이 시도 전체를 덮는다. 하위 호출에는 이미 흐른 시간을 뺀 값이 간다(gRPC Deadlines 가이드).

### 4. 남은 예산이 최소치 미만이면 시작하지 않는다

- SRE 22장: 여러 단계로 처리하는 요청은 각 단계 전에 **충분한 시간이 남았는지** 확인하라.
- 최소치의 예: 그 단계의 p50(절반도 못 끝낼 시간이면 시작할 이유가 약하다), 또는 "시작 비용 + p90".
- 남은 시간으로 시작한 시도는 하류에서 끝나지 못하고 끊길 가능성이 크다. 하류는 그 일을 하다가 버린다(헛일).

### 5. 실험: per-try 정책별 성공률·부하 (시뮬레이션)

- 실제 서버 대신 하류 지연을 확률 모델로 뽑아 정책을 비교했다. **모델은 가정**이다.
  - 94.5% 정상: 로그정규(중앙 80ms, σ=0.5). 5% 느림: 로그정규(중앙 400ms, σ=0.3). 0.5% 멈춤: 응답 없음.
  - 시도마다 독립(재시도가 다른 복제본으로 간다고 가정). 대기(백오프) 0. 요청 100만 건, 난수 시드 42.
- 각 시도의 상한 = `min(per-try, 남은 단계 예산)`.

```java
for (int k = 0; k < maxTries; k++) {
    double remaining = budget - used;
    if (remaining <= 0 || remaining < minStart) break;     // 최소치 미만이면 시작 안 함
    double limit = Math.min(perTry, remaining);             // per-try도 남은 예산을 넘지 못한다
    tries++;
    double d = sample();                                    // 이번 시도의 하류 지연
    if (d <= limit) { used += d; done = true; break; }
    if (limit < perTry) doomed++;                           // 남은 예산에 잘려 실패한 시도
    used += limit;
}
```

(실험, JDK 21.0.12 Temurin, 컨테이너 `--cpus=2`, 2026-10-01 — 시뮬레이션, 시드 고정이라 다시 돌려도 같은 값)

```text
하류 한 번 호출 분포(표본 1000000): p50=83ms p90=184ms p99=586ms p99.9=∞(멈춤 0.5%이 꼬리 0.1%를 덮는다)
정책 (단계 예산 1000ms)                               성공%    시도/요청    p50ms    p99ms
단일 시도, 타임아웃=예산 1000ms                        99.483    1.000       83      593
per-try=p50, 최대 3회                           87.498    1.750       96      249
per-try=p90, 최대 3회                           99.897    1.110       83      388
per-try=p99, 최대 3회                           99.970    1.010       83      606
per-try 없음(=예산), 최대 3회                       99.492    1.000       83      588
-- 남은 예산이 최소치 미만이면 시작하지 않기 (단계 예산 600ms, per-try=p90, 최대 4회)
                                                성공%    시도/요청    p50ms    p99ms   잘린시도/100요청
최소치 없음                                       99.913    1.111       83      394        0.087
남은 예산 < p50이면 시작 안 함                         99.902    1.110       83      395        0.000
```

- 관찰 1 — per-try 없이 "최대 3회": 시도/요청이 1.000이다. 멈춘 시도가 1000ms를 다 써서 재시도가 한 번도 일어나지 않았다. 성공률도 단일 시도와 같은 수준이다(99.492% vs 99.483% — 차이는 난수 표본 차이).
- 관찰 2 — per-try = p99: 성공 99.970%, 시도/요청 1.010. 1%의 시도만 한 번 더 했고 멈춤 0.5%의 대부분을 구했다.
- 관찰 3 — per-try = p50: 시도마다 절반이 오탐이다. 3번 모두 오탐일 확률 0.5³ = 12.5%만큼 실패했고(87.5%), 하류 부하는 1.75배다. 하류가 조금만 느려지면 이 1.75가 더 커진다.
- 관찰 4 — p90은 이 모델에서 p99보다 지연 꼬리(p99 388ms)가 짧고 부하(1.11)는 조금 늘었다. 어느 쪽이 맞는지는 하류가 여분의 11%를 감당하는지에 달렸다.
- 관찰 5 — 최소치 규칙: 이 조건에서 효과는 작았다. 남은 예산에 잘려 헛일로 끝난 시도가 요청 100건당 0.087회 → 0회로 줄었고, 성공률은 0.011%p 줄었다. 예산이 빠듯하고 단계가 깊을수록 잘리는 시도가 늘어 효과가 커진다(해석).
- 한계: 시도 간 독립 가정은 과부하처럼 **모든 복제본이 함께 느린** 상황에서 깨진다. 그때 재시도는 성공률을 못 올리고 부하만 늘린다([06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md)의 재시도 예산).

## 쓰이는 자료구조·알고리즘

- **예산 차감** — `remaining = deadline - now`. 단계를 지날수록 줄기만 한다. 직렬은 합, 병렬은 최댓값.
- **백분위 추정** — 타임아웃 근거가 되는 p99·p99.9는 정렬 배열(실험), 운영에서는 히스토그램(Prometheus `histogram_quantile`, HdrHistogram)·t-digest로 근사한다. 버킷 경계 밖의 값은 근사가 거칠다. 백분위의 성질은 data-analysis 05 `percentiles-and-latency-distributions`(미작성, [data-analysis 영역](../../data-analysis/README.md)), 측정 방법은 [19-performance-measurement](../19-performance-measurement/2-summary.md).
- **예산표 = 호출 트리의 경로 합** — 트리의 각 루트→잎 경로에서 직렬 구간의 합이 예산 이하여야 한다. 35에서 표로 연습한다.

## 적용 — 풀어나가는 법

### 1. 순서

1. 총 예산: 사용자 SLO(예: p99 1000ms)에서 출발한다([02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md)). 게이트웨이 timeout은 이보다 조금 길게 둔다(그 안에서 서비스가 먼저 실패를 돌려줄 수 있게).
2. 예약을 뺀다: 응답 직렬화·전송 여유, 폴백 실행 시간.
3. 호출 그래프를 그리고 직렬·병렬을 표시한다.
4. 단계마다 하류 분포를 본다(아래 PromQL). 오탐률을 골라 per-try 값을 정한다.
5. 재시도 여부·횟수를 정한다(멱등이거나, 요청이 상대에 닿기 전 실패임이 확실할 때만 — 예: Envoy `reset-before-request`). 그 단계의 몫 = 시도 수 × per-try + 대기.
6. 합을 맞춘다. 넘으면 구조를 바꾼다.
7. 코드에서는 고정값과 남은 예산 중 작은 쪽을 쓴다: `min(per-try, remaining - 예약)`.
8. 남은 예산이 최소치 미만이면 그 단계를 시작하지 않고 바로 폴백·에러로 간다.

### 2. 하류 백분위 보기 (PromQL)

```text
# 하류 B 호출 지연 p99.9 (5분 창, 지표 이름은 예시)
histogram_quantile(0.999, sum by (le) (rate(client_request_duration_seconds_bucket{target="B"}[5m])))
# 현재 타임아웃 값으로 끊긴 비율 = 오탐 + 진짜 장애
sum(rate(client_request_timeouts_total{target="B"}[5m])) / sum(rate(client_requests_total{target="B"}[5m]))
```

### 3. 코드 — Java, 단계 실행기

```java
/** 남은 예산 안에서 단계를 실행한다. 예약(reserve)은 응답·폴백 몫. */
<T> T runStage(Deadline dl, Duration perTry, int maxTries, Duration minStart, Duration reserve,
               Function<Duration, T> call, Supplier<T> fallback) {
    for (int k = 0; k < maxTries; k++) {
        Duration left = dl.remaining().minus(reserve);
        if (left.compareTo(minStart) < 0) break;                       // 시작해 봐야 못 끝난다
        Duration limit = left.compareTo(perTry) < 0 ? left : perTry;   // min(per-try, 남은 몫)
        try { return call.apply(limit); }
        catch (CallTimeoutException | RetryableException e) { /* 다음 시도 */ }
    }
    return fallback.get();                                             // 예약해 둔 몫으로 실행
}
```

- `CallTimeoutException`·`RetryableException`은 이 예에서 직접 만든 unchecked 예외로 가정한다. JDK `java.util.concurrent.TimeoutException`은 checked라 `Function.apply` 안에서 그대로 던질 수 없다.
- `Deadline`은 05의 단조 시계 기반 레코드다. `call`은 `limit`을 하류 호출 타임아웃(그리고 하류로 전파할 남은 시간)으로 쓴다.
- 대기(백오프)를 넣는다면 대기 전에 다시 `left`를 잰다. 대기가 남은 예산보다 길면 자지 않고 포기한다(원본 [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)의 Retryer 이유 4).

### 4. Envoy로 옮기면

```yaml
route:
  cluster: service_b
  timeout: 0.6s                 # 이 단계의 몫(전체 — 요청을 다 받은 뒤~상류 응답 끝, 재시도 포함)
  retry_policy:
    retry_on: "5xx,reset,connect-failure"
    num_retries: 1              # 시도 2번
    per_try_timeout: 0.25s      # 2 × 0.25 + 대기 ≤ 0.6
```

- 값은 예시다. 비멱등 호출(결제 승인)에 `retry_on`을 걸면 중복 실행이 난다 — 35번 실험에서 결제가 3번 승인됐다([35](../35-timeout-design-worksheet/2-summary.md)).

## 장애 시나리오와 대처

### 1. 단계 타임아웃의 합 > 전체 → 마지막 단계가 늘 잘린다 (⚠ 커리큘럼)

- 현상: 앞 단계가 조금 느린 날, 마지막 단계(대개 외부 호출이나 응답 조립)만 타임아웃으로 실패한다.
- 보이는 형태: 마지막 단계의 타임아웃 에러가 설정값보다 짧은 시간에 난다(남은 예산으로 잘렸기 때문). 실패 요청의 트레이스에서 앞 단계들이 길다.
- 원인: 단계를 각자 정해 합이 예산을 넘는다.
- 대처: 예산표를 만들고 합을 맞춘다. 직렬 단계를 병렬화하거나 하나를 비동기로 뺀다.

### 2. per-try 없이 재시도 → 첫 시도가 예산을 다 쓴다 (⚠ 커리큘럼)

- 현상: "재시도 3회"인데 실제 재시도 지표가 거의 0이다. 멈춘 복제본 하나 때문에 일부 요청이 꼭 실패한다.
- 보이는 형태: 실패한 요청의 지연이 전부 전체 타임아웃 값 근처에 몰린다. 실험의 "per-try 없음, 최대 3회"는 시도/요청 1.000, 성공률이 단일 시도와 같았다.
- 원인: 시도 하나의 상한 = 전체 상한.
- 대처: per-try를 하류 p99 근처로 둔다(실험: 99.49% → 99.97%).

### 3. 상류 5s·하류 10s(역전) → 헛일 (⚠ 커리큘럼)

- 현상·원인·대처는 [05](../05-timeouts-and-deadline-propagation/2-summary.md) 장애 1과 같다. 예산표에 상류부터 적으면 역전이 바로 보인다.

### 4. p50 기준 타임아웃 → 오탐 타임아웃과 재시도 폭풍 (⚠ 커리큘럼)

- 현상: 하류 지연이 조금 오르자 하류 요청량이 사용자 요청량의 2배 가까이로 뛰고 장애가 커진다.
- 보이는 형태: 타임아웃 비율이 수십 %, 하류의 요청 대비 성공 응답 비율은 정상. 실험의 "per-try=p50": 시도/요청 1.75, 실패 12.5%.
- 원인: 타임아웃이 분포의 한가운데라 정상 응답의 절반을 끊는다. 재시도가 그만큼 부하를 늘린다.
- 대처: 오탐률을 정해 그에 맞는 백분위(예: 0.1% → p99.9)로 올린다. 재시도 예산으로 부하 상한을 건다([06](../06-retry-backoff-jitter/2-summary.md)).

### 5. 폴백 몫이 없다 → 폴백을 실행할 시간이 없어 결국 504 (⚠ 커리큘럼)

- 현상: 폴백(캐시 응답·기본값)을 만들어 뒀는데 장애 때 사용자는 504를 본다.
- 보이는 형태: 폴백 실행 로그가 거의 없거나, 폴백이 시작되자마자 게이트웨이가 끊는다.
- 원인: 단계들이 전체 예산을 다 쓴 뒤에 폴백을 시작한다.
- 대처: 폴백·응답 직렬화 몫을 처음에 예약하고 단계 몫에서 뺀다(1절 그림). 단계 실행기가 `reserve`를 남긴다(적용 3).

## 핵심 문장

- 총 예산은 SLO에서 시작해, 응답·폴백 몫을 먼저 예약하고 남은 것을 단계에 나눈다. 직렬은 합, 병렬은 최댓값.
- 단계 타임아웃은 하류 분포의 백분위에서 고른다. 허용할 오탐률(예: 0.1%)이 백분위(p99.9)를 정한다. p50 기준은 절반을 끊는다.
- 느리거나 멈춘 시도 뒤에도 재시도하려면 per-try 타임아웃이 따로 있어야 한다(빨리 돌아온 5xx·연결 실패는 per-try 없이도 재시도된다). 실험에서 per-try 없는 "최대 3회"는 시도/요청 1.000으로 재시도가 한 번도 일어나지 않았다.
- per-try = p99는 시도/요청 1.010으로 성공률을 99.49%에서 99.97%로 올렸고, per-try = p50은 부하 1.75배에 실패 12.5%였다(시도 독립 가정의 시뮬레이션).
- 남은 예산이 최소치보다 작으면 그 단계를 시작하지 않는다. 하류의 헛일을 줄인다.

## 관련 주제·근거

- 선행
  - [07-timeout-taxonomy-by-layer](../07-timeout-taxonomy-by-layer/2-summary.md) — 나눌 대상인 구간 타임아웃
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 재시도·백오프·재시도 예산
  - [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) — 총 예산의 출발점
  - data-analysis 05 `percentiles-and-latency-distributions` — 미작성, [data-analysis 영역](../../data-analysis/README.md)
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md) — 남은 예산 전파(여기서 심화)
- 후속
  - [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md) — 예산이 끝나면 실제로 멈추기
  - [35-timeout-design-worksheet](../35-timeout-design-worksheet/2-summary.md) — 예산표 → Envoy·Resilience4j 설정
- 문서·글
  - AWS Builders' Library, Marc Brooker, "Timeouts, retries, and backoff with jitter" — 오탐률(0.1%) → 하류 p99.9, 인터넷 클라이언트·좁은 분포의 예외(padding), 너무 짧은 타임아웃의 두 위험 <https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/> (web.archive.org 2024 사본으로 열람)
  - Envoy FAQ "How do I configure timeouts?" — route timeout·per_try_timeout(응답이 나가기 전까지만)·per_try_idle_timeout; router filter 문서 `5xx`(전체 timeout 초과 504는 재시도 안 함), `x-envoy-upstream-rq-per-try-timeout-ms`(전체보다 작아야 함)
  - gRPC "Deadlines" 가이드 — 경과 시간을 뺀 타임아웃으로 전파
  - Google SRE 책 22장 — Missing deadlines(단계 전 남은 시간 확인), Picking a deadline
- 실험 목록
  - `Budget.java` — 하류 지연 혼합 모델(정상 94.5%·느림 5%·멈춤 0.5%), 단계 예산 1000ms에서 per-try p50/p90/p99/없음 × 최대 3회, 단계 예산 600ms에서 최소치 규칙 비교. 요청 100만 건, 시드 42. JDK 21.0.12 컨테이너 `--cpus=2`
