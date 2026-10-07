# reliability/19-performance-measurement — 지연 분포·백분위·coordinated omission·open/closed 부하 모델 — 정리 (힌트)

## 해결하는 문제

"우리 API는 평균 2ms"라는 숫자는 사용자 대부분이 겪는 것을 말해 주지 못할 수 있다.\
게다가 그 숫자를 잰 도구가 **느린 순간에 측정을 멈췄다면**, 숫자 자체가 거짓이다.

```text
 같은 서버, 같은 8초, 같은 1초 멈춤(GC 흉내) — 재는 방식만 다름 (아래 실험)
 재는 방식                         평균      p99
 응답 받고 다음 요청(보낸 시각부터)    1.8ms     1.5ms   ← "아주 좋다"
 계획 시각부터 잼(도착률 고정)       84ms      939ms   ← 실제로 사용자가 겪는 것
```

- *지연(latency)*: 요청 하나가 들어와서 응답이 끝날 때까지 걸린 시간.
- *분포(distribution)*: 요청마다 지연이 다르므로, "얼마나 많은 요청이 얼마나 걸렸나"의 모양.
- *백분위(percentile, p99 등)*: 지연을 작은 것부터 줄 세웠을 때 99% 지점의 값. "100건 중 가장 느린 1건의 문턱".

쉬운 예: 식당 대기 시간이다.
- 손님 100명 중 99명은 1분, 1명은 60분을 기다렸다. 평균은 약 1.6분이다. 그 1명에게 평균은 의미가 없다.
- 더 나쁜 경우: 주방이 멈춘 1시간 동안 "새 손님이 안 왔다"고 기록하면, 대기 기록에는 그 시간이 아예 없다. 실제로는 손님이 문 앞에 줄을 섰는데 말이다.

똑같은 구조다.\
실무 예: 부하 테스트 리포트의 p99, SLO의 지연 목표, 배포 전후 비교, 용량 산정. 모두 "제대로 잰 분포"가 있어야 판단할 수 있다.\
백분위의 수학(병합·보간)은 [data-analysis/05](../../data-analysis/05-percentiles-and-latency-distributions/2-summary.md)에서 다룬다. 이 노트는 **측정 방법**이 숫자를 어떻게 왜곡하는지에 집중한다.

## 동작·원리

### 1. 평균은 꼬리를 숨긴다

```text
 지연 분포(예시) — 대부분 짧고, 드물게 아주 길다 (긴 꼬리)
 건수
  █
  █
  █▄
  ██▄
  ███▄▂▁                                  ▁            ▁
  ──────────────────────────────────────────────────────── 지연
  p50 ↑      p90 ↑     p99 ↑                      max ↑
```

- 평균은 "전체 합 ÷ 건수"라 드문 긴 값이 희석된다. 분포 모양을 하나의 숫자로 접으면 꼬리가 사라진다.
- 그래서 지연은 **p50·p90·p99·p99.9·max**를 함께 본다(아래 실험: 평균 1.8ms인데 max 999ms).
- 요청 하나가 하위 호출 여러 개를 거치면 꼬리가 사용자에게 더 자주 닿는다(→ [34-tail-latency-and-stragglers](../34-tail-latency-and-stragglers/2-summary.md)).

### 2. 백분위는 평균 낼 수 없다 — 히스토그램을 합친다

```text
 서버 A p99 = 10ms, 서버 B p99 = 500ms  → 둘의 평균 255ms ≠ 전체 p99
 올바른 방법: A·B의 원 샘플(또는 같은 버킷 경계의 히스토그램 카운트)을 합친 뒤 백분위를 다시 계산
```

- Prometheus 문서 "Histograms and summaries": summary가 미리 계산한 분위수는 **집계할 수 없다**. histogram은 버킷을 합산해 `histogram_quantile()`로 분위수를 계산할 수 있다. 단 오차가 분위수가 놓인 버킷의 폭만큼 생긴다.
  - *히스토그램(histogram)*: 값의 범위를 구간(버킷)으로 나누고 구간마다 개수만 센 것. 합치기는 같은 버킷끼리 더하면 된다.

### 3. coordinated omission — 측정기가 서버와 "짜고" 측정을 빼먹는다

```text
 closed 부하(응답 받아야 다음 요청), 5ms 간격 계획, 서버가 1초 멈춤
 계획:   |r1|r2|r3|... 5ms마다 ...|r200|r201|
 실제:   r1 ──────────(1초 멈춤)──────────> 응답   r2 r3 ... (몰아서)
 기록:   r1 = 999ms 한 건. 그 1초 동안 보냈어야 할 약 200건은 아예 기록이 없다
```

- *coordinated omission(조율된 누락)*: 부하 생성기가 느린 응답을 기다리는 동안 요청을 보내지 않아, **느린 구간의 표본이 측정에서 빠지는 것**. Gil Tene가 이름 붙였다.
- wrk2 README의 설명: wrk 같은 생성기는 "요청 첫 바이트를 보낸 시각부터 응답까지"를 잰다. 이것은 개별 요청의 완료 시간으로는 맞다. 하지만 응답을 받아야 다음 요청을 보내므로, 높은 지연 구간 동안 측정을 피하게 된다.
- 교정 방법 둘
  1. **계획 시각부터 잰다**(wrk2): 일정한 처리율 계획을 두고, 요청이 "보냈어야 할 시각"부터 응답까지를 잰다.
  2. **사후 보정**(HdrHistogram `recordValueWithExpectedInterval()`): 측정값이 예상 간격보다 크면, 그 사이 빠졌을 표본을 간격만큼 줄어드는 값으로 채워 넣는다.

### 4. open vs closed 부하 모델

```text
 closed (사용자 수 고정)                 open (도착률 고정)
 VU1: [요청]──응답──[요청]──응답──       t=0  5ms  10ms 15ms ... 계획대로 도착
 VU2: [요청]────응답────[요청]──         서버가 느려도 도착은 그대로
 서버가 느려지면 → 요청도 덜 온다          서버가 느려지면 → 큐가 쌓인다
```

- *closed 모델*: 정해진 수의 가상 사용자(VU)가 응답을 받아야 다음 반복을 시작한다. 도착률이 응답 시간에 묶인다.
- *open 모델*: 도착이 완료와 무관하게 일정 비율로 일어난다.
- Grafana k6 문서 "Open and closed models": closed 모델에서는 대상 시스템이 느려질수록 반복이 길어져 새 반복의 도착률이 줄고, 테스트 문헌에서 이 문제를 coordinated omission이라 부른다고 적는다. k6는 `constant-arrival-rate`·`ramping-arrival-rate` 실행기로 open 모델을 구현한다.
- 무엇을 고르나
  - 인터넷 서비스의 사용자는 서버가 느리다고 덜 오지 않는다 → 보통 **open**이 현실에 가깝다.
  - 연결 풀·워커 수가 고정된 내부 배치 소비자처럼 정말로 "N명이 돌아가며" 쓰는 경우는 closed가 맞다.

### 실험: 같은 1초 멈춤을 세 방식으로 잰다

- 서버: 워커 스레드 1개, 요청당 약 1ms. 시작 후 3.0~4.0초에 1초 멈춘다(GC 흉내).
- 부하: 5ms 간격(초당 200건) 계획, 8초.
- A: closed, **보낸 시각부터**(wrk 방식). A′: A의 기록을 HdrHistogram으로 사후 보정. B: 같은 실행을 **계획 시각부터**(wrk2 방식). C: open — 응답과 무관하게 계획대로 보낸다.

```java
// closed: 응답을 받아야 다음 요청. 두 기준으로 동시에 기록한다.
long next = System.nanoTime();
while (next < end) {
    if (System.nanoTime() < next) parkNanos(next - System.nanoTime());
    long send = System.nanoTime();
    long doneAt = callServer();                               // 응답까지 블록
    fromSend.recordValue(doneAt - send);                      // A: 보낸 시각부터
    hdrCorrected.recordValueWithExpectedInterval(doneAt - send, INTERVAL_NS); // A'
    fromPlan.recordValue(doneAt - next);                      // B: 계획 시각부터
    next += INTERVAL_NS;                                      // 계획표는 그대로 진행
}
```

(실험, Docker eclipse-temurin:21-jdk(Temurin 21.0.12) `--cpus=2`, HdrHistogram 2.2.2, 2026-10-01 — 2회 실행, 두 번째 실행 수치도 거의 같다)

```text
A closed, 보낸 시각부터(wrk 방식)          n= 1600 mean=    1.8ms p50=   1.2ms p99=    1.5ms p99.9=    4.4ms max=  999.3ms
A' A를 HdrHistogram 보정              n= 1798 mean=   56.9ms p50=   1.2ms p99=  914.4ms p99.9=  994.6ms max=  999.3ms
B closed, 계획 시각부터(wrk2 방식)         n= 1600 mean=   84.4ms p50=   1.3ms p99=  939.0ms p99.9=  996.1ms max=  999.3ms
C open, 도착률 고정(계획=보낸 시각)           n= 1600 mean=   81.2ms p50=   1.3ms p99=  935.3ms p99.9=  993.5ms max=  997.2ms
```

멈춤 1초 동안 실제로 보낸 요청 수(두 번째 실행에서 추가로 센 값):

```text
closed: 멈춤 1초 동안 보낸 요청 수 = 1
open:   멈춤 1초 동안 보낸 요청 수 = 200
```

- 관찰 1 — A의 p99는 1.5ms다(실행마다 다르다 — 재실행 2회에서 1.4ms·1.8ms). 1초 멈춤은 max(999ms) 한 건으로만 남았다. 평균 1.8ms도 멈춤을 거의 드러내지 못한다.
- 관찰 2 — B와 C의 p99는 약 935~939ms다(재실행 2회 포함 935~942ms). 멈춤 동안 계획됐던 약 200건이 각각 0~1초를 기다린 것이 기록에 들어갔다.
- 관찰 3 — A′(사후 보정)는 빠진 표본 198건을 채워 n=1798이 됐고 p99가 914ms로 B·C에 가까워졌다. 보정은 "예상 간격"을 알 때만 가능하다.
- 관찰 4 — closed는 멈춤 동안 요청을 1건만 보냈다. 서버가 느려지자 부하 생성기도 느려진 것이다. 이것이 k6 문서가 말하는 closed 모델의 결함이다.
- 해석: p50은 네 방식 모두 약 1.2~1.3ms로 같다. **꼬리만 달라진다.** 그래서 이 왜곡은 중앙값만 보면 발견되지 않는다.

## 쓰이는 자료구조·알고리즘

- **HdrHistogram**: 값 범위와 유효 숫자 자릿수(예: 3자리)를 정하면, 어떤 값이든 상대 오차 0.1% 이내의 버킷에 넣는다(HdrHistogram README의 예: 1µs~1시간을 3자리 정밀도로). 버킷이 로그 간격이라 메모리가 고정되고, 같은 설정끼리 더할 수 있다.
- **t-digest**: 데이터를 작은 중심점(centroid) 묶음으로 요약해 분위수를 근사한다. 분포 양 끝(p99·p99.9)에 묶음을 촘촘히 둬서 꼬리 정확도가 높다(Dunning & Ertl, arXiv 1902.04023). 병합 가능하다.
- **고정 버킷 히스토그램(Prometheus classic histogram)**: 사람이 정한 경계(`le`)마다 누적 카운트. 경계가 같으면 합칠 수 있고, 분위수는 버킷 안에서 선형 보간한 근사다.
- **정렬 후 인덱스**: 원 샘플이 메모리에 다 있으면 정렬해 `n×p` 위치를 읽는다. 위 실험의 분위수는 HdrHistogram으로 계산했다.
- **스케줄(계획표)**: open 부하와 coordinated omission 교정은 "i번째 요청의 의도된 시작 시각 = t0 + i×간격"이라는 계획이 있어야 한다.
- 링 버퍼·슬라이딩 윈도 집계(최근 N분 분위수)는 [16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md)의 지표 수집과 이어진다.

## 적용 — 풀어나가는 법

### 1. 측정 전에 적는 것

| 항목 | 예 |
|---|---|
| 무엇을 재나 | 클라이언트가 본 end-to-end 지연인가, 서버 처리 시간인가 |
| 부하 모델 | open(초당 N건) / closed(VU N명) — 이유 |
| 환경 | 코어 수, 인스턴스 종류, 데이터 크기, 캐시 상태, 버전 |
| 워밍업 | JIT·커넥션 풀·캐시를 데운 뒤 측정 구간을 분리 |
| 지표 | p50·p90·p99·p99.9·max, 처리량, 오류율(성공·실패 분리) |
| 기간 | 꼬리를 보려면 충분히 길게(p99.9면 최소 수천 건 이상) |

- 성공과 실패를 따로 잰다. 빠르게 실패하는 응답(예: 즉시 503)이 섞이면 지연 분포가 좋아 보인다(원본 [engineering-axes/performance.md](../../engineering/engineering-axes/performance.md) 「대원칙 ①」의 추가 규칙).

### 2. 도구에서

```bash
# 상수 처리율 + 계획 시각 기준 측정 (wrk2 README 예: 30초, 2스레드, 연결 100, 초당 2000건)
# open 부하는 아니다: 연결마다 응답을 받아야 다음 요청을 보낸다. 송신은 밀릴 수 있고, 지연만 계획 시각부터 잰다
wrk -t2 -c100 -d30s -R2000 --latency http://127.0.0.1:8080/
# wrk2는 보정 전 분포도 --u_latency로 함께 보여 준다 — 두 분포의 차이가 coordinated omission의 크기

# curl로 단건 시간 분해 (DNS·connect·TLS·첫 바이트·전체)
curl -o /dev/null -s -w 'dns=%{time_namelookup} conn=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://example.com/
```

```javascript
// k6 open 모델: 응답 시간과 무관하게 초당 200회 반복 시작 (k6 문서 constant-arrival-rate 예)
export const options = {
  scenarios: { open_model: { executor: 'constant-arrival-rate', rate: 200, timeUnit: '1s',
                             duration: '1m', preAllocatedVUs: 50, maxVUs: 300 } },  // maxVUs는 예시
};
```

- k6 arrival-rate는 반복의 **시작**을 계획대로 한다. 지연(`http_req_duration`)은 실제로 보낸 때부터 잰다(k6 문서 Metrics reference).
  - 빈 VU가 없으면 그 반복은 시작되지 않는다. 지연 기록에는 들어가지 않고 `dropped_iterations` 카운터로만 센다(k6 문서 "Dropped iterations"). `maxVUs`를 안 쓰면 `preAllocatedVUs`와 같다.
  - 그래서 서버가 멈추면 VU가 바닥나 같은 꼴의 누락이 다시 생길 수 있다. VU를 넉넉히 두고 `dropped_iterations = 0`인지 확인한다.

- wrk2 README의 주의: 보정 기간(calibration)을 10초로 늘렸으므로 10~20초보다 짧은 실행은 쓸모 있는 정보를 주지 않을 수 있다.

### 3. 운영 지표에서 (Prometheus)

```promql
# 5분 창, 서비스 전체 p99 — 인스턴스별 버킷을 먼저 합친 뒤 분위수 (지표 이름은 예시: Micrometer 히스토그램)
histogram_quantile(0.99, sum by (le) (rate(http_server_requests_seconds_bucket[5m])))
```

- `avg(인스턴스별 p99)`처럼 분위수를 평균 내지 않는다. 버킷을 합친 뒤 계산한다.
- 버킷 경계는 SLO 문턱 근처를 촘촘하게 둔다. 분위수 오차는 그 분위수가 놓인 버킷 폭만큼이다(Prometheus 문서).

### 4. 결과를 비교할 때

- 한 번 잰 숫자 하나로 "빨라졌다"고 하지 않는다. 같은 조건으로 여러 번 돌려 범위를 본다(통계는 [38-microbenchmarking](../38-microbenchmarking/2-summary.md)).
- 변경 하나만 바꾸고 재측정한다(방법론은 [20-performance-method-and-amdahl](../20-performance-method-and-amdahl/2-summary.md)).

## 장애 시나리오와 대처

### 1. 평균만 보고 "문제없음" 판정

- 현상: 대시보드 평균 지연은 평탄한데 고객 문의 "가끔 몇 초씩 멈춘다"가 계속 온다.
- 보이는 형태: 평균 수 ms, p99·max 패널이 없다. 로그에는 드문 수 초짜리 요청이 있다.
- 원인: 평균은 드문 긴 지연을 희석한다(위 실험 A: 평균 1.8ms, max 999ms).
- 대처: p50·p99·p99.9·max를 함께 그린다. SLI를 "요청 중 X ms 이내 비율"로 정의한다(→ [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md)).

### 2. 부하 생성기가 느린 응답 동안 요청을 안 보냄 → p99 과소 측정

- 현상: 부하 테스트 p99는 2ms였는데 운영에서는 GC 때마다 p99가 수백 ms로 튄다.
- 보이는 형태: 테스트 리포트의 처리량이 멈춤 구간에서 뚝 떨어진다(실험: 멈춤 1초 동안 1건). p99와 max의 차이가 수백 배다.
- 원인: closed 모델 + "보낸 시각부터" 측정 = coordinated omission.
- 대처: open 모델(초당 N건 고정, k6 arrival-rate)이나 계획 시각 기준 측정(wrk2)을 쓴다. 이미 모은 데이터는 예상 간격을 알면 HdrHistogram 보정으로 근사한다. 테스트 중 처리량이 목표를 지켰는지 함께 확인한다(k6면 `dropped_iterations = 0`).

### 3. 인스턴스별 p99를 평균 내 전체 p99로 보고

- 현상: "전체 p99 120ms"라고 보고했는데 실제 사용자 p99는 400ms였다.
- 보이는 형태: 쿼리가 `avg(quantile ...)` 또는 summary의 `quantile` 라벨을 평균 낸다.
- 원인: 분위수는 집계 연산이 아니다(Prometheus 문서: summary는 집계 불가).
- 대처: histogram으로 바꾸고 `sum by (le)` 후 `histogram_quantile`. 같은 버킷 경계를 모든 인스턴스에 쓴다.

### 4. 워밍업·캐시를 섞어서 잼

- 현상: 배포 직후 측정한 지연이 다음 날보다 3배 나쁘다. 또는 반대로, 같은 키만 반복해 캐시 적중 100%인 숫자를 보고한다.
- 보이는 형태: 측정 초반 구간의 지연이 높고 점점 내려간다. 키 분포가 실제와 다르다.
- 원인: JIT 컴파일·커넥션 풀·캐시가 데워지는 구간을 측정에 포함했거나, 실제와 다른 입력 분포를 썼다.
- 대처: 워밍업 구간을 분리한다. 실제 트래픽의 키 분포·데이터 크기를 재현한다. 콜드 스타트 자체가 관심이면 따로 잰다(→ [42-cold-start-and-scale-from-zero](../42-cold-start-and-scale-from-zero/2-summary.md)).

## 핵심 문장

- 지연은 분포다. 평균 하나가 아니라 p50·p99·p99.9·max를 함께 본다.
- 분위수는 평균 낼 수 없다. 원 샘플이나 같은 경계의 히스토그램을 합친 뒤 다시 계산한다.
- closed 부하 + "보낸 시각부터" 측정은 서버가 멈춘 동안 측정도 멈춘다(coordinated omission). 실험에서 같은 1초 멈춤이 p99 1.5ms로도, 939ms로도 나왔다.
- 교정은 계획 시각부터 재기(wrk2), 계획대로 보내는 open 모델(빠진 반복이 없을 때), 또는 예상 간격을 아는 사후 보정(HdrHistogram)이다.
- 인터넷 사용자는 서버가 느려도 덜 오지 않는다. 그 상황을 재현하려면 open 모델을 쓴다.

## 관련 주제·근거

- 선행
  - [data-analysis/05-percentiles-and-latency-distributions](../../data-analysis/05-percentiles-and-latency-distributions/2-summary.md)
  - 원본 [engineering-axes/performance.md](../../engineering/engineering-axes/performance.md) — 「대원칙 ① 꼬리를 본다」, 「성능 작업의 함정」
  - [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) — 지연 SLI
- 후속·연결
  - [20-performance-method-and-amdahl](../20-performance-method-and-amdahl/2-summary.md) — 측정 → 병목 → 하나만 바꾸기
  - [22-capacity-and-load-testing](../22-capacity-and-load-testing/2-summary.md) — 부하 테스트 설계·open/closed 선택
  - [34-tail-latency-and-stragglers](../34-tail-latency-and-stragglers/2-summary.md) — 팬아웃에서 꼬리 증폭
  - [36-profiling](../36-profiling/2-summary.md) — 어디서 시간이 쓰이나
  - [38-microbenchmarking](../38-microbenchmarking/2-summary.md) — 코드 조각 단위 측정의 함정
  - [16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md) — 히스토그램 지표
- 문서·글
  - giltene/wrk2 README — 상수 처리율 부하, 계획 시각 기준 측정, Coordinated Omission 설명, `--u_latency` <https://github.com/giltene/wrk2>
  - HdrHistogram README — 정밀도(유효 숫자), "Corrected vs. Raw value recording calls"(`recordValueWithExpectedInterval`) <https://github.com/HdrHistogram/HdrHistogram>
  - Grafana k6 "Open and closed models" <https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/>, "Dropped iterations" <https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/dropped-iterations/>, constant-arrival-rate(`maxVUs` 기본 = `preAllocatedVUs`) <https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/constant-arrival-rate/>, Metrics reference(`http_req_duration`) <https://grafana.com/docs/k6/latest/using-k6/metrics/reference/>
  - Prometheus "Histograms and summaries"(분위수 집계 불가, 버킷 폭 오차) <https://prometheus.io/docs/practices/histograms/>
  - Dunning & Ertl, "Computing Extremely Accurate Quantiles Using t-Digests", arXiv 1902.04023
  - Gil Tene, "How NOT to Measure Latency"(강연) [?] — 원문 영상은 확인하지 못했다. coordinated omission의 정의는 위 wrk2 README로 확인했다.
  - Gregg 『Systems Performance』 2판 12장 Benchmarking(목차는 brendangregg.com 책 페이지에서 확인, 본문 세부는 [?]) · brendangregg.com/methodology.html의 "Passive Benchmarking Anti-Method"·"Active Benchmarking"
- 실험 목록
  - CO.java — 1초 멈춤 서버를 closed(보낸 시각·계획 시각·HdrHistogram 보정)와 open으로 측정. Docker eclipse-temurin:21-jdk `--cpus=2`, HdrHistogram 2.2.2, 8초 × 2모드 × 2회
