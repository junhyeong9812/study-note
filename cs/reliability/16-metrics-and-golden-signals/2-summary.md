# reliability/16-metrics-and-golden-signals — 지표 형(카운터·게이지·히스토그램)·골든 시그널·RED·USE·카디널리티 — 정리 (힌트)

## 해결하는 문제

초당 요청 수천 건의 로그를 매번 다 읽어서는 "지금 괜찮은가"를 답할 수 없다.\
필요한 것은 **싸게 모으고, 빨리 집계하고, 오래 추세를 보는** 숫자다. 그것이 지표(metric)다.

```text
 로그로 "지난 5분 에러율"을 구하면                지표로 구하면
 로그 수백만 줄을 읽어 세기 → 수십 초             카운터 두 개의 증가율 나누기 → 밀리초
 저장 비용 = 줄 수에 비례                         저장 비용 = 시계열 수 × 샘플 수(요청 수와 무관)
```

- *지표(metric)*: 시간에 따라 바뀌는 숫자 하나를 주기적으로 기록한 것. 이름 + 레이블 + (시각, 값)의 줄이다.
- *시계열(time series)*: 이름과 레이블 조합 하나에 붙은 (시각, 값) 목록. `http_requests_total{route="/pay",code="500"}`이 시계열 하나다.

쉬운 예: 자동차 계기판이다. 속도계·연료계·엔진 경고등만 보고 운전한다. 엔진 내부 기록(로그)은 고장 났을 때 정비소에서 본다.\
똑같은 구조다.\
실무 예: 결제 API 대시보드에 초당 요청 수·5xx 비율·p99 지연·스레드풀 대기열 길이 네 칸을 둔다. 하나가 튀면 그때 로그(15)와 트레이스(17)를 연다.\
기초(골든 시그널 표, 성공·실패 지연 분리, 지표·로그·트레이스 3축)는 원본 [systems/server-design/08-deployment-ops](../../systems/server-design/08-deployment-ops.md) §5에 있다. 이 노트는 지표 형과 계산, 버킷·카디널리티 함정을 실험으로 본다.

## 동작·원리

### 1. 수집 — 끌어오기(pull)와 텍스트 형식

```text
 애플리케이션 프로세스                       Prometheus
 ┌──────────────────────────┐   1초~1분마다   ┌────────────────────┐
 │ 메모리 안 카운터·버킷     │ ◀── GET /metrics │ scrape → TSDB 저장 │
 │ (요청마다 +1, 매우 쌈)    │ ──▶ 텍스트 응답  │ PromQL로 rate·분위수 │
 └──────────────────────────┘                 └────────────────────┘
```

- 요청마다 하는 일은 메모리 숫자 증가뿐이다. 그래서 요청 수가 늘어도 비용이 거의 늘지 않는다.
- 저장 비용은 **시계열 수**와 수집 주기가 정한다. 요청 수와는 거의 무관하다. 반대로 레이블 값 종류가 늘면 시계열이 곱으로 는다(§6).

### 2. 지표 형 — 카운터·게이지·히스토그램

(실험의 `/metrics` 응답 일부 — coarse 버킷과 `user_id` 줄은 뺐다, 2026-10-01)

```text
# TYPE http_requests_total counter
http_requests_total{route="/pay",code="200"} 46290
http_requests_total{route="/pay",code="500"} 251
# TYPE http_inflight_requests gauge
http_inflight_requests 17
# TYPE lat_fine_seconds histogram
lat_fine_seconds_bucket{le="0.025"} 3776
lat_fine_seconds_bucket{le="0.05"} 22525
lat_fine_seconds_bucket{le="0.1"} 45131
lat_fine_seconds_bucket{le="0.25"} 45131
lat_fine_seconds_bucket{le="0.5"} 45131
lat_fine_seconds_bucket{le="1"} 45131
lat_fine_seconds_bucket{le="1.5"} 45131
lat_fine_seconds_bucket{le="2"} 45827
lat_fine_seconds_bucket{le="2.5"} 46541
lat_fine_seconds_bucket{le="5"} 46541
lat_fine_seconds_bucket{le="+Inf"} 46541
lat_fine_seconds_sum 5082.97817987675
lat_fine_seconds_count 46541
```

- *카운터(counter)*: 올라가기만 하는 값. 재시작하면 0으로 돌아간다. 값 자체보다 **증가율**(`rate()`)을 본다. 요청 수·에러 수·보낸 바이트.
- *게이지(gauge)*: 오르내리는 현재 값. 진행 중 요청 수·큐 길이·메모리 사용량. 줄어들 수 있는 값을 카운터로 내면 안 된다(Prometheus 문서 "Metric types").
- *히스토그램(histogram)*: 관측값을 버킷별로 센 카운터 묶음. classic 히스토그램은 시계열 여러 개다.
  - `_bucket{le="x"}`: x **이하**인 관측의 누적 개수(le = less or equal).
  - `_sum`·`_count`: 합과 개수. `_count`는 `le="+Inf"` 버킷과 같다.
- *summary*: 미리 정한 분위수를 앱 안에서 **추정해** 낸다(분위수 없이 `_sum`·`_count`만 내는 summary도 있다). 알고리즘이 맞으면 보통 매우 정확하지만 **인스턴스끼리 합칠 수 없다**(Prometheus 문서 "Histograms and summaries"). 서버 여러 대의 p99를 보려면 히스토그램이 필요하다.
- `rate()`는 카운터 재시작(리셋)을 보정한다. 그래서 **`rate()` 먼저, `sum()`은 나중**이다. 합친 뒤에 rate를 하면 한 대의 재시작을 올바른 리셋으로 보정하지 못한다(Prometheus 문서 `rate()`: "Otherwise rate() cannot detect counter resets").

### 3. 무엇을 잴까 — 골든 시그널·RED·USE

| 방법 | 대상 | 재는 것 | 출처 |
|---|---|---|---|
| 4 골든 시그널 | 사용자 앞 서비스 | Latency·Traffic·Errors·Saturation | SRE 6장 "The Four Golden Signals" |
| RED | 요청을 받는 서비스(마이크로서비스) | Rate·Errors·Duration | Tom Wilkie, 2015년 고안(Grafana 블로그 2018) |
| USE | 자원(CPU·디스크·네트워크·풀) | Utilization·Saturation·Errors | Brendan Gregg, USE Method |

- SRE 6장: 사용자 앞 시스템에서 네 개만 잴 수 있다면 이 넷이다.
  - Latency: 성공과 실패의 지연을 **나눠** 잰다. 빠른 500이 평균을 좋아 보이게 만든다. 느린 에러는 빠른 에러보다 나쁘다.
  - Errors: 명시적(HTTP 500), 암묵적(200인데 내용이 틀림), 정책상(1초 넘으면 실패) 실패를 다 센다.
  - Saturation: 가장 제약된 자원이 얼마나 찼나. 많은 시스템은 100% 전에 성능이 떨어지므로 목표 이용률을 정한다. 짧은 창(예: 1분)의 p99 지연이 포화의 이른 신호가 된다.
- RED는 골든 시그널에서 포화를 뺀 것과 거의 같다. Wilkie는 "RED는 사용자, USE는 기계"로 둘을 함께 쓰라고 한다(Grafana 블로그).
- USE의 정의(Gregg)
  - 이용률: 자원이 일한 시간의 비율(구간 평균).
  - 포화: 처리하지 못해 쌓인 일의 정도. 보통 대기열 길이.
  - 에러: 에러 사건 수.
  - 긴 구간의 평균 이용률이 낮아도 짧은 폭주가 포화를 만들 수 있다(Gregg, "Does Low Utilization Mean No Saturation?").

### 4. 평균은 꼬리를 숨긴다

```text
 요청 100개의 지연(예시)
 ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ (97개: 20~80ms)
                                                      ▇ ▇ ▇ (3개: 1.5~2.5s)
 평균 ≈ 110ms  ← 어느 요청의 실제 경험도 아니다
 p50  ≈ 50ms,  p99 ≈ 2.1s ← 100명 중 1명은 2초를 기다린다
```

- SRE 6장 "Worrying About Your Tail": 평균 100ms인 서비스에서 1%가 5초 걸리는 일이 쉽게 생긴다. 페이지 하나가 그런 백엔드 여럿을 부르면, 백엔드 하나의 p99가 프론트엔드의 중앙값이 될 수 있다(팬아웃 증폭은 34).
- 같은 장은 지연을 실제 값 대신 **버킷별 개수**로 모으라고 한다. 경계를 대략 지수적으로(예: 약 3배씩: 10·30·100·300ms) 둔다.

### 5. 실험: 히스토그램 버킷이 분위수 추정을 정한다

- 익스포터(Java, JDK `HttpServer`)가 관측값을 만든다: 97%는 20~80ms 균등, 3%는 1.5~2.5s 균등. 에러는 0.5%.
- 같은 관측을 두 버킷 구성에 넣었다.
  - coarse: `0.1, 1, 10`
  - fine: `0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 2.5, 5`
- 원시값 전체로 계산한 실제 분위수를 `/truth`로 함께 냈다.

```java
for (int i = 0; i < COARSE.length; i++) if (sec <= COARSE[i]) coarse[i]++;   // le = "이하" 누적
for (int i = 0; i < FINE.length; i++)   if (sec <= FINE[i])   fine[i]++;
sum += sec; count++; raw.add(sec);
```

(실험, Prometheus 3.15.0(`prom/prometheus:latest`) + JDK 21 익스포터, 일회용 컨테이너 각 `--cpus=1`, scrape 1초, 약 45초 수집 후 질의, 2026-10-01)

```text
histogram_quantile(0.50, sum by (le) (rate(lat_coarse_seconds_bucket[30s])))
  -> [('', 0.0516)]
histogram_quantile(0.50, sum by (le) (rate(lat_fine_seconds_bucket[30s])))
  -> [('', 0.0519)]
histogram_quantile(0.99, sum by (le) (rate(lat_coarse_seconds_bucket[30s])))
  -> [('', 7.0056)]
histogram_quantile(0.99, sum by (le) (rate(lat_fine_seconds_bucket[30s])))
  -> [('', 2.1719)]
rate(lat_fine_seconds_sum[30s]) / rate(lat_fine_seconds_count[30s])
  -> [({'instance': 'sn-rl-w15-exp:8080', 'job': 'pay'}, 0.1089)]
sum by (code) (rate(http_requests_total[30s]))
  -> [({'code': '200'}, 891.1724), ({'code': '500'}, 4.8621)]
실제(원시값 전체):
n=33199 평균=0.1084 p50=0.0511 p90=0.0757 p99=2.1433
```

- 관찰 1 — 평균 약 0.109s. p50(0.051s)의 두 배이고, p99(2.14s)와는 스무 배 차이다. 평균만 보면 "100ms쯤"으로 읽힌다.
- 관찰 2 — coarse p99 = **7.0s**, 실제 2.14s. p99가 `1 < x ≤ 10` 버킷에 떨어졌다. classic 히스토그램에서 `histogram_quantile`은 버킷 안을 **선형 보간**한다. 1 + 9 × (버킷 안에서의 위치 약 0.67) ≈ 7.0이 나온 것이다.
- 관찰 3 — fine p99 = 2.17s. 실제(2.14s)에 가깝다. 경계가 꼬리 근처(1.5·2·2.5)에 있어서다. 단 질의는 최근 30초 창이고 "실제"는 원시값 전체라 같은 요청 집합이 아니다. 0.03s 차이를 순수한 추정 오차로 읽지는 않는다.
- 값은 실행·시점마다 조금 다르다. 최근 30초 창에 꼬리 관측(3%)이 몇 개 들었느냐로 coarse 버킷 안 위치가 바뀐다. 점검 재실행 두 번 질의에서 coarse p99 6.61·6.96s, fine p99 2.12·2.16s, 실제 p99 2.14·2.16s였다(같은 환경, 2026-10-01). coarse가 실제의 약 3배로 부풀고 fine이 실제에 가깝다는 경향은 같았다.
- 관찰 4 — p50은 두 구성 모두 맞았다. 이 분포에서 0~0.1s 버킷 안 관측이 고르게 퍼져 있어 선형 보간이 잘 맞았다(우연에 가깝다).
- 초당 요청 수(891)는 실행·시점마다 다르다(같은 실험 앞선 질의에서 380, 점검 재실행에서 193·781). 익스포터의 `Thread.sleep(1)` 간격이 컨테이너 CPU 제한에서 흔들린 탓이다.
- Prometheus 문서도 같은 예를 든다: 220ms에 몰린 분포를 `{le="0.3"}`(200~300ms) 버킷이 받으면 95분위가 295ms로 추정된다. classic 버킷은 SLO 경계(예: 300ms) 근처에 촘촘히 두라는 것이 요지다. native histogram은 경계를 지수 간격으로 자동으로 잡는다. 오차는 설정한 해상도가 정하므로 필요한 정확도에 맞춰 해상도를 고른다(같은 문서).

### 6. 실험: 카디널리티 — 레이블 값 하나가 시계열 하나

```text
 http_requests_total{route, code}         → route 1 × code 2  = 2 시계열
 requests_by_user_total{user_id}          → 사용자 5000명      = 5000 시계열
 user_id를 route·code와 같이 붙이면       → 1 × 2 × 5000      = 10000 시계열 (사용자가 늘면 계속)
```

(같은 실험, `/api/v1/status/tsdb`)

```text
TSDB head:
  numSeries 5027
   {'name': 'requests_by_user_total', 'value': 5000}
   {'name': 'lat_fine_seconds_bucket', 'value': 11}
   {'name': 'lat_coarse_seconds_bucket', 'value': 4}
   {'name': 'http_requests_total', 'value': 2}
```

- 관찰: 시계열 5027개 중 5000개가 `user_id` 레이블 하나에서 나왔다. `/metrics` 응답도 약 211KB가 됐다(대부분 이 줄들).
- *카디널리티(cardinality)*: 한 지표 이름 아래 레이블 조합의 수 = 시계열 수.
- Prometheus 문서 "Metric and label naming": 레이블 조합마다 새 시계열이 생기므로 사용자 ID·이메일 같은 **값이 무한한 차원**을 레이블에 넣지 말라.
- 사용자별 질문("이 사용자는 왜 느렸나")은 로그·트레이스(15·17)로 답한다. 지표는 묶음의 모양을 답한다.

### 7. 저장 — 시계열 압축

```text
 시각:  t0, t0+15, t0+30, t0+45 ...   간격이 같다 → 간격의 차이(delta-of-delta) = 0 → 1비트
 값:    1042.0, 1042.0, 1043.0 ...     직전 값과 XOR → 같으면 0 → 1비트
```

- Gorilla(Pelkonen 외, VLDB 2015)는 시각을 delta-of-delta로, 값을 직전 값과의 XOR로 줄인다. Facebook 데이터에서 점 하나 16바이트를 평균 1.37바이트로 줄였다(12배). 시각의 약 96%가 1비트, 값의 약 51%가 1비트였다.
- Prometheus TSDB의 `tsdb/chunkenc/xor.go`가 이 방식(go-tsz에서 가져온 코드)이다. Gorilla는 초 단위, Prometheus는 밀리초 단위라 비트 구간을 넓혔다고 주석이 적는다.
- 그래서 시계열 하나는 싸다. 비싼 것은 **시계열 개수**(색인·메모리의 head 블록)다. 카디널리티가 문제인 이유다.

## 쓰이는 자료구조·알고리즘

- **누적 버킷 히스토그램** — `le` 경계마다 카운터. 분위수는 누적 개수에서 순위가 들어가는 버킷을 찾고 그 안을 선형 보간한다(`histogram_quantile`, classic 히스토그램 기준). 누적 합 개념은 [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md).
- **지수 버킷(native histogram)** — 경계를 일정 배율로 자동 배치해 상대 오차를 해상도만큼으로 묶는다. 표준 지수 버킷 안은 선형이 아닌 지수 보간을 쓴다(PromQL functions 문서). 원시값을 다 두지 않는 분위수 근사로는 HDR Histogram·t-digest도 있다(19에서 다룸).
- **슬라이딩 윈도 증가율** — `rate(x[5m])`는 창 안 첫·끝 샘플의 증가를 시간으로 나누고 창 끝까지 외삽한다. [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md).
- **delta-of-delta·XOR 비트 압축** — Gorilla, Prometheus XOR 청크.
- **역색인(레이블 → 시계열 ID 목록)** — 레이블 조합 검색. 시계열이 많을수록 커진다. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md).
- **해상도 계층(다운샘플링)** — 오래된 데이터를 거칠게 보관. [database/44-timeseries-resolution-tiers](../../database/44-timeseries-resolution-tiers/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 서비스마다 RED(요청 수·에러·지연 히스토그램)를 먼저 둔다. 지연은 성공·실패를 레이블로 나눈다.
2. 자원마다 USE를 둔다. 특히 스레드풀·커넥션 풀(활성·대기 수), 큐 길이, 디스크 사용률.
3. 히스토그램 버킷은 SLO 경계 주변에 촘촘히 둔다(예: SLO 300ms면 0.1·0.2·0.25·0.3·0.35·0.5).
4. 레이블은 값이 유한한 것만(route 템플릿, 상태 코드 계열, 리전). 원시 URL·사용자 ID·주문 ID는 넣지 않는다.
5. 대시보드는 위에서 아래로: 골든 시그널 → 하류 의존성 → 자원.

### 2. Micrometer로 RED 내보내기 (Java, Spring Boot Actuator + Prometheus 레지스트리 가정)

```java
Timer payTimer(String outcome) {                       // 같은 이름·같은 태그 키로 늘 이 빌더를 거친다
    return Timer.builder("pay.request")
            .tag("route", "/pay")                         // 템플릿 경로. 원시 URL(/pay/1042) 금지
            .tag("outcome", outcome)                      // success / error 두 값뿐
            .publishPercentileHistogram()                 // 버킷을 내보내 서버 쪽에서 합치고 분위수를 계산
            .serviceLevelObjectives(Duration.ofMillis(300)) // SLO 경계를 버킷에 꼭 넣는다
            .register(registry);                          // 이미 있으면 같은 Timer를 돌려준다
}

Object handle(PayRequest req) {
    Timer.Sample s = Timer.start(registry);
    String outcome = "success";
    try { return pay(req); }
    catch (RuntimeException e) { outcome = "error"; throw e; }
    finally { s.stop(payTimer(outcome)); }
}
```

- Micrometer 문서: `publishPercentiles`(클라이언트 쪽 분위수)는 태그끼리 **합칠 수 없다**. 히스토그램이 있으면 보통 필요 없다.
- 레이블 이름·값 수를 코드 리뷰에서 본다. `outcome`처럼 값이 몇 개로 닫힌 것만 붙인다.

### 3. PromQL — RED와 USE

- 지표 이름 주의: Rate·Errors 식은 §5 실험 익스포터의 `http_requests_total{route,code}`를 쓴다. 위 Micrometer 코드의 `pay.request`는 `pay_request_seconds_count{route,outcome}` 계열로 나오므로 그 이름·레이블로 바꿔 쓴다.
- Duration·SLO 식의 `http_server_requests_seconds_bucket`은 Spring Boot 자동 HTTP 타이머다. 기본값에서는 `_bucket`이 나오지 않는다. `management.metrics.distribution.percentiles-histogram.http.server.requests=true`(또는 SLO 버킷 설정)를 켜야 한다. 위 `.publishPercentileHistogram()`은 `pay.request`에만 적용된다.

```promql
# Rate: 초당 요청
sum by (route) (rate(http_requests_total[5m]))
# Errors: 5xx 비율 (rate 먼저, sum 나중)
sum(rate(http_requests_total{code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
# Duration: 인스턴스 전체 p99
histogram_quantile(0.99, sum by (le) (rate(http_server_requests_seconds_bucket[5m])))
# SLO 경계 이하 비율(300ms) — 분위수 추정 오차 없이 버킷 값 그대로
sum(rate(http_server_requests_seconds_bucket{le="0.3"}[5m])) / sum(rate(http_server_requests_seconds_count[5m]))
# Saturation: 커넥션 풀 대기 스레드 (HikariCP + Micrometer)
max(hikaricp_connections_pending)
# 카디널리티 점검: 시계열이 가장 많은 지표 10개
topk(10, count by (__name__) ({__name__=~".+"}))
```

## 장애 시나리오와 대처

### 1. 레이블 카디널리티 폭발 → TSDB 메모리 부족

- 현상: 배포 직후 Prometheus 메모리가 계속 오르다 OOM으로 재시작한다. 재시작 뒤 WAL 재생이 길어 한동안 지표가 비어 있다.
- 보이는 형태: `prometheus_tsdb_head_series` 급증. `/api/v1/status/tsdb`의 `seriesCountByMetricName` 상위에 한 지표가 수만~수백만. 위 실험에서는 `user_id` 하나로 5000개.
- 원인: 사용자 ID·주문 ID·원시 URL·에러 메시지 원문을 레이블로 붙였다.
- 대처: 해당 레이블을 제거한다(급하면 scrape 설정의 `metric_relabel_configs`로 drop). 경로는 템플릿으로 정규화한다. 시계열 수 상한(`sample_limit` 등)과 지표별 시계열 수 경보를 둔다. 개별 식별자는 로그·트레이스로 보낸다.

### 2. 평균 지표가 꼬리를 숨긴다

- 현상: 대시보드의 평균 지연은 100ms로 평온한데 고객 불만이 쌓인다.
- 보이는 형태: 위 실험처럼 평균 0.109s, p99 2.14s. 실패가 빠르면 평균이 오히려 내려간다(SRE 6장 — 빠른 500).
- 원인: `_sum / _count`만 그린다. 성공·실패 지연을 섞었다.
- 대처: p50·p99(또는 SLO 경계 이하 비율)를 그린다. 성공·실패를 레이블로 나눈다. SLI는 평균이 아니라 "300ms 이하 비율"처럼 정한다(02).

### 3. 히스토그램 버킷이 부적절 → 분위수가 엉뚱하다

- 현상: p99가 7초로 보여 비상이 걸렸는데, 트레이스로 보면 느린 요청도 2초대다. 또는 반대로 SLO 근처에서 변화가 안 보인다.
- 보이는 형태: 위 실험의 coarse(7.0s vs 실제 2.14s). p99 그래프가 버킷 경계 값 근처에서 계단처럼 움직인다.
- 원인: classic 히스토그램에서 `histogram_quantile`은 버킷 안을 선형 보간한다. 넓은 버킷에서는 오차가 버킷 폭만큼 커진다. 가장 높은 버킷(+Inf)에 떨어지면 두 번째로 높은 경계값을 돌려준다.
- 대처: SLO 경계와 관심 구간에 버킷을 촘촘히 둔다. 가능하면 native histogram을 쓴다. 경보에는 분위수 대신 "경계 이하 비율"을 쓴다.

### 4. 집계 순서를 바꿔 카운터 리셋을 놓친다

- 현상: 배포(재시작)할 때마다 요청률 그래프에 평소의 수십~수백 배 같은 거대한 스파이크가 생긴다(`rate()`는 음수를 내지 않는다). 다른 인스턴스의 증가가 그 감소를 덮으면 합이 줄지 않아 리셋을 아예 못 알아채고 **과소 계산**하기도 한다.
- 보이는 형태: recording rule로 sum해 저장한 카운터에 rate를 건 식, 또는 서브쿼리 `rate((sum(x))[5m:])`. (`rate(sum(x))`는 `sum`이 순간 벡터를 돌려줘 그대로는 실행되지 않는다.)
- 원인: 합친 값은 한 인스턴스가 0으로 돌아가도 조금 줄기만 한다. `rate()`는 값이 줄면 무조건 "0부터 다시 셌다"고 보고 직전 값 전체를 증가분에 더한다(Prometheus 소스 `promql/functions.go`의 리셋 처리). 그래서 합계 전체가 한순간의 증가로 잡혀 스파이크가 된다. 한 대의 재시작을 올바로 보정하지 못하는 것이다.
- 대처: 인스턴스별 `rate()` 먼저, `sum()`은 나중(Prometheus 문서). recording rule도 같은 순서로 만든다.

### 5. 포화를 재지 않아 "CPU는 한가한데 느리다"

- 현상: CPU 30%인데 p99가 오른다.
- 보이는 형태: 스레드풀 활성 수가 최대치에 붙어 있고 대기열이 길다. 커넥션 풀 `pending` 증가.
- 원인: 제약 자원이 CPU가 아니라 풀·락·하류 동시성이다. USE에서 그 자원을 빠뜨렸다.
- 대처: 풀·큐마다 이용률(활성/최대)과 포화(대기 수)를 지표로 낸다. 커넥션 풀은 [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md).

## 핵심 문장

- 지표는 이름·레이블 조합 하나가 시계열 하나다. 비용은 요청 수가 아니라 시계열 수가 정한다.
- 카운터는 `rate()`로 보고, 합치기 전에 rate를 건다. 게이지는 현재 값이다. 히스토그램은 버킷별 누적 카운터다.
- 사용자 앞 서비스는 골든 시그널(지연·트래픽·에러·포화) 또는 RED로, 자원은 USE로 잰다. 지연은 성공·실패를 나눈다.
- 평균은 꼬리를 숨긴다. 실험에서 평균 0.109s, p99 2.14s였다.
- classic 히스토그램에서 `histogram_quantile`은 버킷 안을 선형 보간한다. 버킷 `0.1, 1, 10`은 실제 p99 2.14s를 7.0s로 추정했고, 꼬리 근처에 경계를 둔 버킷은 2.17s로 가깝게 냈다(질의 창이 달라 차이를 순수 오차로 보지는 않는다).
- 사용자 ID 같은 무한 값은 레이블에 넣지 않는다. 실험에서 레이블 하나가 시계열 5000개를 만들었다.

## 관련 주제·근거

- 선행
  - [15-logging](../15-logging/2-summary.md) — 사건 단위 기록과 그 비용
  - 원본 [systems/server-design/08-deployment-ops](../../systems/server-design/08-deployment-ops.md) §5 — 골든 시그널 표, 성공·실패 지연 분리, 3축 관측, 알림 설계 요지
- 후속·연결
  - [17-distributed-tracing](../17-distributed-tracing/2-summary.md) — 지표가 튄 요청 하나를 따라가기(exemplar로 지표에서 트레이스로)
  - [43-alerting-and-on-call](../43-alerting-and-on-call/2-summary.md) — 이 지표들로 증상 기반·번 레이트 경보
  - [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) — SLI를 평균이 아닌 비율로
  - [19-performance-measurement](../19-performance-measurement/2-summary.md) — 분위수·coordinated omission
  - [34-tail-latency-and-stragglers](../34-tail-latency-and-stragglers/2-summary.md) · [41-autoscaling](../41-autoscaling/2-summary.md)
  - [database/44-timeseries-resolution-tiers](../../database/44-timeseries-resolution-tiers/2-summary.md) · [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md)
- 책·논문·글
  - Google SRE 책 6장 "Monitoring Distributed Systems" — The Four Golden Signals, Worrying About Your Tail(평균 100ms·1% 5초, 지수 버킷) <https://sre.google/sre-book/monitoring-distributed-systems/>
  - Brendan Gregg, "The USE Method" <https://www.brendangregg.com/usemethod.html>
  - Grafana Labs 블로그 2018-08-03, "The RED Method: How to Instrument Your Services"(Tom Wilkie, 2015년 고안) <https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/>
  - Pelkonen 외, "Gorilla: A Fast, Scalable, In-Memory Time Series Database", PVLDB 8(12), 2015 — 1.37 bytes/point, 12x, delta-of-delta·XOR <https://www.vldb.org/pvldb/vol8/p1816-teller.pdf>
- 문서·소스
  - Prometheus "Metric types", "Histograms and summaries"(분위수 추정 오차, 220ms 예), "Metric and label naming"(높은 카디널리티 금지), PromQL functions(`histogram_quantile` 선형 보간·+Inf 버킷, `rate()` 먼저 그다음 `sum()`) <https://prometheus.io/docs/>
  - Prometheus 소스 `tsdb/chunkenc/xor.go`(go-tsz 기반, Gorilla 대비 밀리초 해상도 주석)
  - Micrometer "Histograms and percentiles"(클라이언트 분위수는 합칠 수 없음), `Timer.Builder.publishPercentileHistogram`·`serviceLevelObjectives`
- 실험 목록
  - Prometheus 3.15.0 + JDK 21 익스포터(scratchpad `rel/15/Exp16.java`, `prom.yml`, `q16.sh`): 97% 20~80ms·3% 1.5~2.5s 관측을 coarse·fine 버킷에 기록 → `histogram_quantile`·평균 vs 원시값 분위수, `user_id` 레이블 5000개의 시계열 수. 일회용 컨테이너 `sn-rl-w15-exp`·`sn-rl-w15-prom`(네트워크 `sn-rl-w15-net`), 실험 뒤 삭제
