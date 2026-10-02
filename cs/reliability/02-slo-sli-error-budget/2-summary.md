# reliability/02-slo-sli-error-budget — SLI 고르기·SLO·에러 버짓·번 레이트 경보 — 정리 (힌트)

## 해결하는 문제

"이 서비스는 충분히 안정적인가?"에 숫자가 없으면 두 가지가 무너진다.

- **결정**: 개발팀은 "더 빨리 내보내자", 운영팀은 "더 테스트하자"고 한다. 기준이 없으니 목소리 큰 쪽이 이긴다. SRE 3장은 이 긴장이 두 팀의 평가 지표가 다른 데서 나온다고 적는다.
- **경보**: "에러가 났다"마다 깨우면 사람은 무시하기 시작한다. 반대로 경보를 아끼면 천천히 새는 장애를 며칠 동안 모른다.

쉬운 예: 한 달 휴대폰 데이터 요금제다.
- 10GB(목표)를 정해 두면, 월초에 2GB를 써도 걱정할 일이 아니다. 하루에 3GB씩 쓰고 있으면 "이 속도면 4일 만에 바닥"이라 지금 줄여야 한다.
- 남은 양(버짓)과 쓰는 속도(번 레이트)를 보면 언제 행동할지 정해진다.

똑같은 구조다.\
실무 예: "30일 동안 요청의 99.9% 성공"을 목표로 두면 허용 실패가 0.1%다. 이 허용분을 배포·실험에 쓰고, 빨리 타들어 갈 때만 사람을 깨운다.

기초(SLI·SLO·SLA 표, 에러 버짓의 쓸모, SLI 설계 요령)는 원본 [systems/server-design/09-capacity-slo.md](../../systems/server-design/09-capacity-slo.md) §1에 있다. 이 노트는 SLI를 고르는 기준, 평균 지표의 함정, 번 레이트 경보를 정의부터 실험까지 다룬다.

## 동작·원리

### 1. 세 단어 — 재는 것, 목표, 계약

```text
  SLI (지표)            SLO (목표)                  SLA (계약)
  "좋은 요청 비율"  ──>  "28일 동안 ≥ 99.9%"   ──>  "99.5% 미만이면 요금 10% 환급"
  측정 시스템이 잼       팀이 정함                    사업·법무가 정함, 결과(배상)가 붙음
```

- *SLI(service level indicator)*: 서비스 수준의 한 측면을 정량으로 정의한 측정값(SRE 4장).
- *SLO(service level objective)*: SLI가 가져야 할 목표 값·범위. SRE 4장은 "SLI ≤ 목표" 또는 "하한 ≤ SLI ≤ 상한" 꼴로 쓴다. 지연처럼 낮을수록 좋은 지표는 ≤, 성공률처럼 높을수록 좋은 지표는 위 그림처럼 ≥ 목표다.
- *SLA(service level agreement)*: SLO를 지키거나 못 지켰을 때의 결과(환급·위약금)가 들어간 명시·암묵 계약. "못 지키면 무슨 일이 생기나?"에 명시된 결과가 없으면 SLA가 아니라 SLO다(SRE 4장).

### 2. SLI는 "좋은 사건 / 유효한 사건" 비율로

SRE Workbook 2장은 SLI를 **좋은 사건 수 ÷ 전체(유효) 사건 수**로 쓰기를 권한다.

```text
 가용성 SLI = 성공한 HTTP 요청 / 전체 HTTP 요청
 지연 SLI   = 300ms 안에 끝난 요청 / 전체 요청          ← 평균 지연이 아니다
 신선도 SLI = 10분 이내 데이터로 답한 재고 조회 / 전체 재고 조회
```

- 0%(전부 고장)~100%(고장 없음)로 읽기 쉽다. 에러 버짓 = 100% − SLO로 바로 이어진다(Workbook 2장).
- *SLI 명세 vs SLI 구현*: "사용자에게 중요한 결과"(명세)와 "그것을 실제로 어디서 어떻게 재나"(구현 — 서버 로그, LB 지표, 클라이언트 계측)를 나눈다(Workbook 2장). 같은 명세에도 구현마다 정확도·포괄 범위·비용이 다르다.

### 3. 평균은 꼬리를 숨긴다

```text
 지연 분포 (요청 수 ↑)
   │█
   │██
   │███
   │█████
   │████████▁▁                                    ▂▂▂   ← 3%가 1.5~2.5초
   └──────────────────────────────────────────────────── 지연 →
     80ms(중앙)       300ms                      2000ms
   평균 = 143ms  (300ms보다 낮다 → "평균 < 200ms" SLO 통과)
   300ms 안에 끝난 비율 = 97%  (→ "≥ 99%" SLO 위반)
```

- SRE 4장: 평균은 "대부분 빠르고 일부가 훨씬 느린" 긴 꼬리를 가린다. 그래서 백분위수(p99·p99.9)를 선호한다.
- 같은 이유로 지연 SLI는 "임계값 안에 끝난 비율"로 쓰면 비율형 SLI(2절)와 모양이 같아진다.

### 실험 A: 평균 SLO는 통과, 비율 SLO는 위반

- 하루 10만 요청. 정상 요청은 중앙값 80ms 로그정규(예시). 3일차부터 3%가 1.5~2.5초(회귀).

(실험, JDK 21 eclipse-temurin, `--cpus=2`, seed 고정, 2026-10-01 — 코드 `scratchpad/rel/01/e02/Slo.java`)

```text
== A. 하루 10만 요청, SLO 후보 두 개: 평균<200ms / 300ms 안에 끝난 비율>=99%
day  slow%  mean(ms)  p50(ms)  p99(ms)  good(<300ms)  평균SLO  비율SLO
  1   0.0      85.2     80.1    181.3      99.991%   통과     통과
  2   0.0      85.0     80.0    181.4      99.989%   통과     통과
  3   3.0     143.8     81.1   2169.7      96.914%   통과     위반
  4   3.0     143.2     81.2   2167.3      96.953%   통과     위반
```

- 관찰: 회귀 뒤 p99는 181ms → 2,170ms로 12배가 됐는데 평균 SLO는 계속 "통과"다. p50도 거의 그대로(80 → 81ms)다. 느린 요청 3%를 SLO 판정에서 잡은 것은 비율 SLI이고, p99도 꼬리를 드러냈다. 평균만 놓쳤다. (실험은 요청 단위라 사용자 몇 %가 영향받았는지는 알 수 없다.)

### 4. 에러 버짓 — 남은 허용량으로 결정한다

```text
 SLO 99.9%, 28일, 요청 300만 건  →  버짓 = 0.1% × 300만 = 3,000건 (Workbook 2장의 예)
 장애 한 번에 1,500건 실패        →  버짓 50% 소모

 버짓 남음 ──> 배포·실험 계속
 버짓 소진 ──> 정책대로: 신뢰성 작업 우선, 배포 동결 등 (에러 버짓 정책)
```

- *에러 버짓(error budget)*: 1 − SLO만큼의 허용 실패량. 개발과 SRE가 같은 숫자를 보고 위험을 정한다(SRE 3장 "Motivation for Error Budgets").
- *에러 버짓 정책(error budget policy)*: 버짓을 다 썼을 때 무엇을 할지 미리 합의한 문서. Workbook 2장은 PM·개발·SRE 세 쪽이 이 정책에 동의하는지가 SLO가 맞는지의 시험이라고 적는다.
- SRE 3장은 목표를 **최소이자 최대**로 본다. 99.99%를 목표로 하면 그것을 넘기되 많이 넘기지 않으려 한다. 남는 신뢰성은 기능·부채 정리에 쓸 수 있었던 기회다.
- 윈도: Workbook 2장은 **4주 롤링 윈도**를 범용으로 권한다. 주말 수가 일정해지고(30일 윈도는 주말이 4번 또는 5번), 달이 바뀌어도 사용자는 지난 장애를 잊지 않는다.

### 5. 번 레이트 — 버짓이 타는 속도

- *번 레이트(burn rate)*: SLO 대비 버짓을 소모하는 속도. 1이면 윈도가 끝날 때 버짓이 정확히 0이 된다(Workbook 5장). 99.9% SLO에서 에러율 0.1%가 이어지면 번 레이트 1이다.

```text
 번 레이트 = 관측 에러율 / (1 − SLO)

 "경보 윈도 동안 버짓의 x%를 쓰면 깨운다"
   번 레이트 = x × (SLO 기간) / (경보 윈도)
   2% / 1시간,  30일 기준 → 0.02 × 720h / 1h = 14.4
   5% / 6시간               → 0.05 × 720h / 6h = 6
   10% / 3일                → 0.10 × 720h / 72h = 1
```

Workbook 5장의 권장 시작값(99.9% SLO, 표 5-8):

| 심각도 | 긴 윈도 | 짧은 윈도 | 번 레이트 | 경보 시점의 버짓 소모 |
|---|---|---|---|---|
| page(호출) | 1시간 | 5분 | 14.4 | 2% |
| page | 6시간 | 30분 | 6 | 5% |
| ticket(티켓) | 3일 | 6시간 | 1 | 10% |

- 같은 장의 설정 예(6번째 방식)에는 ticket 규칙이 하나 더 있다: 24시간 + 2시간 윈도, 번 레이트 3. 아래 실험은 이 예처럼 ticket 규칙 둘을 썼다.

- *짧은 윈도(short window)*: "지금도 타고 있나"를 확인하는 창. 긴 윈도의 1/12이 지침이다(Workbook 5장). 장애가 끝나면 짧은 윈도가 먼저 기준 아래로 내려가 경보가 빨리 꺼진다(리셋 시간 단축).
- 경보 규칙의 품질은 네 가지로 본다: 정밀도(울린 경보 중 의미 있는 비율), 재현율(의미 있는 사건 중 울린 비율), 탐지 시간, 리셋 시간(Workbook 5장).

### 실험 B: 번 레이트 경보 vs "10분 에러율 > 0.1%"

- 30일, 분당 1,000요청(예시), SLO 99.9% → 버짓 43,200건. 배경 에러 0.02%, 1분짜리 2% 블립 30번.
- 사고 셋: A 전면 장애 5분, B 2% 에러 8시간, C 0.4% 에러 2일.
- 경보: 위 표의 multiwindow·multi-burn-rate 규칙을 분 단위 누적합으로 계산(슬라이딩 윈도).

```java
// 핵심 부분: 누적합으로 임의 길이 윈도의 에러율을 O(1)에
static double rate(int m, int win) {
    int from = Math.max(0, m - win + 1);
    return (double) (pre[m + 1] - pre[from]) / ((m - from + 1) * (double) RPM);
}
boolean page = (rate(m, 60) > 14.4 * BUDGET && rate(m, 5) > 14.4 * BUDGET)
            || (rate(m, 360) > 6 * BUDGET && rate(m, 30) > 6 * BUDGET);
boolean ticket = (rate(m, 1440) > 3 * BUDGET && rate(m, 120) > 3 * BUDGET)
              || (rate(m, 4320) > BUDGET && rate(m, 360) > BUDGET);
```

(실험, 같은 환경)

```text
== B. 30일·분당 1000요청·SLO 99.9% → 버짓 43200건
A 전면 장애 100% 5분    소모 11.6% | page 0분 뒤(그때까지 버짓 2.3%) | ticket 3분 뒤
B 2% 에러 8시간        소모 22.4% | page 41분 뒤(그때까지 버짓 2.0%) | ticket 168분 뒤
C 0.4% 에러 2일       소모 26.6% | page 없음 | ticket 872분 뒤
30일 전체 소모 80.6% (배경+블립 포함)
경보 발생 횟수: 순진한 10분>0.1% = 32회, page = 2회, ticket = 4회
```

- 관찰 1 — 심각도에 따라 반응 속도가 다르다. 전면 장애는 첫 1분 안에(출력의 "0분 뒤"는 사고 첫 1분 버킷을 평가한 시점이다. 실제 Prometheus에서는 수집·평가 주기만큼 더 늦다), 2% 에러는 41분 뒤(버짓 2% 소모 시점)에 page가 울렸다. 0.4%(번 레이트 4)는 page 없이 약 14.5시간 뒤 ticket으로 갔다.
- 관찰 2 — 순진한 경보는 32번 울렸다. 대부분 버짓을 거의 쓰지 않는 1분 블립이다. 번 레이트 page는 2번(A·B)뿐이다.
- 관찰 3 — ticket 4회 중 1회는 B 도중 2시간 짧은 윈도가 경계값 근처에서 한 번 꺼졌다 켜진 것이다(전이 로그로 확인: 17748 ON → 17749 OFF → 17750 ON). 경계값 근처 깜빡임은 경보 억제나 히스테리시스로 다룬다.
- 관찰 4 — A의 page는 시작 34분 뒤 꺼졌다. 6시간 규칙의 짧은 윈도(30분)가 사고 5분을 품고 있는 동안 켜져 있었다.

## 쓰이는 자료구조·알고리즘

- **슬라이딩 윈도 집계** — 최근 N분의 합. 분 단위 버킷 배열 + 누적합(위 실험)이나 링 버퍼(N칸 순환 배열, 새 칸 들어올 때 옛 칸 빼기)로 O(1)에 갱신한다. Prometheus `rate(x[1h])`·`increase()`도 윈도 안 카운터 증가분을 계산한다.
- **카운터와 비율** — 좋은 사건·전체 사건을 단조 증가 카운터 둘로 세고, 윈도 증가분의 비로 SLI를 만든다. 재시작으로 카운터가 0이 되는 것은 `rate`가 보정한다.
- **히스토그램 버킷** — 지연 SLI "300ms 안 비율"은 `le="0.3"` 버킷 ÷ 전체 count. Prometheus 문서는 고전 히스토그램을 고전 시계열로 수집해 `_bucket{le="0.3"}`로 조회하면 경계가 정확히 0.3에 있어야 하고, 없으면 결과가 아예 없거나 일부 대상만 계산되어 **경고 없이 불완전**해진다고 적는다(practices/histograms). NHCB(사용자 지정 경계 네이티브 히스토그램)나 네이티브 히스토그램으로 수집하면 `histogram_fraction`으로 경계 사이 비율을 추정할 수 있다. 분위수 자체는 `histogram_quantile`이 버킷 안에서 보간한 추정값이다.
- **다중 윈도 AND/OR 규칙** — 긴 윈도(정밀도) AND 짧은 윈도(리셋) 조합을 OR로 여러 개 둔다.
- 히스토그램·HDR·t-digest 자세히는 [19-performance-measurement](../19-performance-measurement/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 사용자 여정 하나(예: 주문 생성)를 고른다.
2. SLI 명세를 쓴다: "주문 생성 요청 중 성공하고 500ms 안에 끝난 비율".
3. SLI 구현을 고른다: LB 로그(포괄적이지만 앱 내부 실패 의미를 모름), 앱 지표(의미는 정확, LB 앞단 실패는 못 봄), 합성 탐침(트래픽 없을 때도 봄).
4. 지난 4주 실측으로 첫 SLO를 잡는다. Workbook 2장은 현재 성능이 출발점이 될 수 있지만 그것에 묶이지 말라고 적는다.
5. 에러 버짓 정책을 PM·개발·운영이 합의한다(소진 시 무엇을 멈추나).
6. 번 레이트 경보를 위 표 값으로 시작하고, 정밀도·재현율을 보며 조정한다.
7. 분기마다 SLO가 사용자 체감과 맞는지 다시 본다(사고와 SLO 위반 날이 겹치나).

### 2. 계측 (Java, Micrometer)

```java
// SLO 경계(300ms·500ms)를 히스토그램 버킷으로 내보낸다 → Prometheus에서 le="0.3" 버킷이 생긴다
Timer orderTimer = Timer.builder("order.create")
        .serviceLevelObjectives(Duration.ofMillis(300), Duration.ofMillis(500))
        .register(registry);
orderTimer.record(() -> orderService.create(cmd));
```

- `serviceLevelObjectives(Duration...)`는 Micrometer `Timer.Builder`의 메서드다(소스 `micrometer-core/.../Timer.java`). 실패 요청도 같은 타이머에 넣을지, 상태 라벨로 나눌지는 SLI 명세를 따른다.

### 3. PromQL

```promql
# 1시간 지연 SLI: 300ms 안 비율 (Micrometer의 Prometheus 레지스트리가 order.create 타이머를 order_create_seconds_bucket 등으로 내보낸다)
sum(rate(order_create_seconds_bucket{le="0.3"}[1h])) / sum(rate(order_create_seconds_count[1h]))

# 1시간 에러율 (번 레이트 경보의 재료)
sum(rate(http_server_requests_seconds_count{job="order", status=~"5.."}[1h]))
/ sum(rate(http_server_requests_seconds_count{job="order"}[1h]))

# page 규칙 (99.9% SLO, Workbook 5장 표 5-8 첫 줄)
job:slo_errors_per_request:ratio_rate1h{job="order"} > (14.4 * 0.001)
and
job:slo_errors_per_request:ratio_rate5m{job="order"} > (14.4 * 0.001)
```

- `job:slo_errors_per_request:ratio_rate1h`는 위 에러율 식을 기록 규칙(recording rule)으로 미리 계산해 둔 이름이다(Workbook 5장 예와 같은 이름).

## 장애 시나리오와 대처

### 1. 평균 지연 SLI라 꼬리 사용자 불만을 놓친다 (⚠ 커리큘럼)

- 현상: 대시보드 평균 지연은 정상인데 "가끔 너무 느리다"는 문의가 쌓인다.
- 보이는 형태: 평균 85 → 143ms(기준 200ms 안), p99 181 → 2,170ms(실험 A). 경보 없음.
- 원인: 평균은 3% 꼬리를 희석한다(SRE 4장).
- 대처: 지연 SLI를 "임계값 안 비율" 또는 p99로 바꾼다. 실패 요청 지연은 따로 본다(빨리 실패한 에러가 평균을 끌어내린다).

### 2. SLO가 없어 안정성 vs 속도 논쟁이 끝나지 않는다 (⚠ 커리큘럼)

- 현상: 배포 회의마다 "위험하다/괜찮다"가 반복된다. 장애 뒤에는 배포 동결, 몇 주 뒤 다시 압박.
- 보이는 형태: 결정 기록에 숫자가 없다. 동결 해제 기준이 사람마다 다르다.
- 원인: 공통 지표가 없어 협상력으로 정해진다(SRE 3장 "Hope is not a strategy" 문단).
- 대처: SLO와 에러 버짓 정책을 문서로 합의한다. "버짓이 남으면 배포, 소진되면 신뢰성 작업 우선"을 미리 정해 두면 회의가 숫자 확인으로 바뀐다.

### 3. 경보가 너무 많거나, 천천히 새는 장애를 놓친다

- 현상: 밤마다 깨는데 대부분 저절로 사라진다. 그런데 정작 이틀짜리 0.4% 에러는 블립 경보에 묻혀 아무도 심각하게 보지 않았다.
- 보이는 형태: 순진한 "10분 에러율 > 0.1%" 경보 32회, 그중 다수가 1분 블립(실험 B). 0.4% 사고(C)도 0.1%를 넘으니 순진한 경보에 걸리기는 하지만, 1분 블립과 같은 모양의 경보라 심각도를 구분하지 못한다.
- 원인: 경보 기준이 버짓 소모와 무관하다. 짧은 윈도 하나로 정밀도와 재현율을 함께 맞출 수 없다(Workbook 5장 1~3번 시도).
- 대처: multiwindow·multi-burn-rate 규칙. 빠른 소모는 page, 느린 소모는 ticket.

### 4. 지연 SLI가 조용히 비거나 일부만 계산된다

- 현상: SLO 대시보드의 지연 SLI 값이 "No data"이거나, 특정 인스턴스가 빠진 채 나온다.
- 보이는 형태: 쿼리에서 `le="0.3"`을 쓰는데 일부 서비스는 버킷 경계가 0.25·0.5다.
- 원인: 고전 히스토그램을 고전 `_bucket` 시계열로 조회하면 경계가 정확히 그 값에 있어야 한다. 없으면 결과가 없거나 불완전한데 경고가 없다(Prometheus 문서).
- 대처: SLO 경계를 계측 코드에서 버킷으로 고정한다(위 `serviceLevelObjectives`). 대상 수를 함께 세서 빠진 대상을 감시한다.

### 5. 트래픽이 적은 서비스에서 경보가 튄다

- 현상: 새벽에 요청 몇 건 중 1건 실패로 page가 울린다.
- 보이는 형태: 1시간 요청 수가 수십 건이라 1건 실패가 에러율 수 %가 된다.
- 원인: 비율 SLI는 분모가 작으면 흔들린다. Workbook 5장의 예: 시간당 10요청이면 1건 실패가 에러율 10%, 99.9% SLO에서 번 레이트 1,000이라 바로 page가 울린다.
- 대처: Workbook 5장이 권하는 셋 — 인공 트래픽(합성 탐침)으로 신호를 보충, 작은 서비스를 묶어 한 단위로 감시, 제품을 바꿔 실패 한 건의 판정·영향을 줄이기(여러 요청이 실패해야 사고로 보거나, 한 건 실패의 영향을 낮춤).

## 핵심 문장

- SLI는 재는 것, SLO는 목표, SLA는 결과가 붙은 계약이다. 결과가 없으면 SLA가 아니다.
- SLI는 "좋은 사건 / 전체 사건"으로 쓴다. 지연도 "임계값 안 비율"로 쓰면 평균이 숨기는 꼬리를 잡는다(실험: 평균 143ms 통과, 300ms 안 비율 96.9% 위반).
- 에러 버짓 = 1 − SLO. 남은 버짓이 배포 속도를, 버짓 정책이 소진 시 행동을 정한다.
- 번 레이트 = 관측 에러율 / (1 − SLO). "윈도 동안 버짓 x%"로 임계값을 정하면 심각도마다 반응 속도가 달라진다(실험: 전면 장애 1분 안, 2% 에러 41분, 0.4%는 ticket).
- 긴 윈도는 정밀도를, 짧은 윈도는 빠른 리셋을 준다. 둘을 AND로 묶는다.

## 관련 주제·근거

- 선행
  - [01-fault-error-failure-availability](../01-fault-error-failure-availability/2-summary.md) — 시간 기반·요청 기반 가용성, 직렬 합성
  - 원본 [systems/server-design/09-capacity-slo.md](../../systems/server-design/09-capacity-slo.md) §1 SLI/SLO/에러 버짓
- 후속
  - [16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md), [19-performance-measurement](../19-performance-measurement/2-summary.md), [43-alerting-and-on-call](../43-alerting-and-on-call/2-summary.md)
  - [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md) — 경계값 깜빡임, 원본 [systems/Hysteresis](../../systems/Hysteresis/)
  - [03-failure-at-scale](../03-failure-at-scale/2-summary.md) — 부분 실패가 상시화되면 분포·비율로 봐야 하는 이유
- 책·문서
  - Google 『Site Reliability Engineering』 3장 "Embracing Risk"(에러 버짓, 목표는 최소이자 최대) <https://sre.google/sre-book/embracing-risk/>, 4장 "Service Level Objectives"(SLI·SLO·SLA 정의, 평균 대신 백분위수) <https://sre.google/sre-book/service-level-objectives/>
  - 『The Site Reliability Workbook』 2장 "Implementing SLOs"(good/total SLI, SLI 명세·구현, 4주 롤링 윈도, 에러 버짓 정책) <https://sre.google/workbook/implementing-slos/>, 5장 "Alerting on SLOs"(정밀도·재현율·탐지·리셋, 번 레이트, 표 5-6·5-8, 짧은 윈도 1/12, 저트래픽 서비스) <https://sre.google/workbook/alerting-on-slos/>
  - Prometheus docs, "Histograms and summaries"(`le` 버킷 경계, 고전 히스토그램 경계 불일치 시 결과 없음) <https://prometheus.io/docs/practices/histograms/>
  - Micrometer `io.micrometer.core.instrument.Timer.Builder#serviceLevelObjectives(Duration...)` (micrometer-core 소스)
- 실험 목록
  - e02-A 평균 지연 SLO vs 300ms 안 비율 SLO(하루 10만 요청 × 4일, 3% 꼬리 회귀) — JDK 21, `scratchpad/rel/01/e02/Slo.java`
  - e02-B multiwindow·multi-burn-rate 경보 vs 순진한 10분 경보(30일 분 단위, 사고 3개 + 블립 30개) — 같은 파일, 전이 로그는 `e02/dbg/Slo.java`
