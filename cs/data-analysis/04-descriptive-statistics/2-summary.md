# data-analysis/04-descriptive-statistics — 중심·산포·분위수·이상치 — 정리 (힌트)

## 해결하는 문제

값 1만 개를 사람이 다 볼 수는 없다. 몇 개의 숫자로 줄여야 한다. 문제는 **어느 숫자로 줄이느냐**에 따라 다른 이야기가 된다는 것이다.

```text
  응답 시간 10건(ms, 예시)   12 15 17 20 22 25 28 30 35 400
  평균        60.4 ms        ← 10건 중 9건이 이보다 빠르다
  중앙값      23.5 ms        ← 가운데 두 값(22·25)의 평균
  표본표준편차 119.5 ms      ← "보통 ±120ms씩 흔들린다"? 9건은 12~35 사이다
```

- 요약 숫자는 두 종류다. "가운데가 어디냐"(중심)와 "얼마나 퍼졌냐"(산포). 각 종류에 **극단값에 끌려가는 것**과 **잘 안 끌려가는 것**이 있다.
  - *기술통계(descriptive statistics)*: 가진 데이터 자체를 요약하는 숫자와 그림. 모집단에 대한 추측(추론)은 data-analysis 07 이후다.
  - *이상치(outlier)*: 나머지 데이터에서 수치적으로 멀리 떨어진 관찰값(OpenIntro 2.1.5).

쉬운 예: 직원 9명의 연봉이 3~5천만 원인 회사에 연봉 50억 원인 대표가 있다. "평균 연봉 약 5억 4천(예시)"은 거짓말은 아니지만, 이 회사 누구의 경험과도 맞지 않는다.

똑같은 구조다.\
지연·결제 금액·파일 크기·사용 시간은 대부분 작고 일부가 매우 크다(오른쪽으로 치우침). 평균은 그 일부에 끌려간다.

실무 예:
- API 평균 응답 60ms로 "빠르다"고 보고했는데 사용자 대부분은 20ms대, 일부는 400ms를 겪는다.
- "평균 주문 금액"으로 프로모션 기준을 정했는데 대량 구매 몇 건이 평균을 끌어올려 대부분 고객이 기준에 못 미친다.
- 같은 데이터인데 Python과 SQL의 "1사분위수"가 다르게 나와 리포트 숫자가 안 맞는다.

## 동작·원리

### 1. 중심 — 평균·중앙값·최빈값

```text
  오른쪽으로 치우친 분포 (긴 꼬리가 오른쪽)

  개수
   █
   ██
   ███
   ████▄
   ██████▄▄▁▁ ▁     ▁
  ─┴──┴──────┴──────────────▶ 값
   최빈값 중앙값   평균      ← 꼬리 쪽으로 평균이 끌려간다
```

- *평균(mean)*: 값의 합 ÷ 개수. 모든 값이 같은 무게로 들어가므로 극단값 하나가 크게 끈다.
- *중앙값(median)*: 정렬했을 때 가운데 값. 짝수 개면 가운데 두 값의 평균(OpenIntro 2.1.5, Python `statistics.median`).
- *최빈값(mode)*: 가장 많이 나온 값. 명목형에도 쓸 수 있다([01](../01-data-types-and-measurement/2-summary.md)).
- *치우침(skew)*: 분포의 한쪽 꼬리가 길게 늘어진 모양. 꼬리가 오른쪽이면 "오른쪽으로 치우쳤다(right skewed)"고 한다(OpenIntro 2.1.3).
  - 흔한 오해: "오른쪽 치우침이면 항상 평균 > 중앙값 > 최빈값." 대부분의 교과서 예에서는 맞지만, 이산 분포·다봉 분포에서는 이 순서가 깨질 수 있다(해석 — 모양을 직접 보라, [06](../06-exploratory-data-analysis/2-summary.md)).
- OpenIntro 2.1.6의 기준: "전형적인 하나"를 알고 싶으면 중앙값, "합계로 확장되는 것"(대출 1,000건에 필요한 총액)을 알고 싶으면 평균이 더 쓸모 있다. **평균이 틀린 게 아니라 질문이 다르다.**
  - 서버 비용·총 처리 시간·용량은 합계 질문이다 → 평균(× 건수). 사용자 체감은 개인 질문이다 → 중앙값과 백분위.

### 2. 산포 — 분산·표준편차·IQR

```text
  편차         x_i − x̄
  표본분산 s²  = Σ (x_i − x̄)² / (n − 1)        표본표준편차 s = √s²
  IQR          = Q3 − Q1                        (가운데 50%가 차지하는 폭)

  ──┬────────┬───────┬────────┬────────────────────────────▶
   min       Q1     중앙값     Q3                         max
             └──── IQR (가운데 50%) ────┘
```

- *분산(variance)*·*표준편차(standard deviation)*: 평균에서 떨어진 거리의 제곱을 평균 낸 것과 그 제곱근. 성질(덧셈·상수배)은 [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md) 3절이 단일 출처다.
- 표본분산은 n이 아니라 **n − 1로** 나눈다(OpenIntro 2.1.4). Python 3.12 `statistics.variance`·`stdev`는 n − 1(베셀 보정), `pvariance`·`pstdev`는 n이다. 문서에 따르면 `variance`(n − 1)는 데이터가 대표적(예: 독립·동일 분포)일 때 모분산의 불편 추정이다. `stdev`는 그 제곱근일 뿐, 모표준편차의 불편 추정은 아니다(NIST 핸드북 6.3.2).
  - *베셀 보정(Bessel's correction)*: 표본 평균을 데이터에서 추정했기 때문에 생기는 과소 추정을 n − 1로 나눠 바로잡는 것.
- *사분위수(quartile)*: Q1 = 25번째 백분위, Q3 = 75번째 백분위. *IQR(interquartile range)*: Q3 − Q1.
- OpenIntro 2.1.6의 용어: 중앙값·IQR은 *로버스트 통계량(robust statistic)*이다 — Q1·중앙값·Q3 근처 값에만 민감해서 극단값이 바뀌어도 보통 거의 변하지 않는다(이번 실험에서는 그대로였다. 값이 아주 적으면 Python 기본 `'exclusive'`의 Q3는 최댓값에 끌릴 수 있다). 평균·표준편차는 로버스트하지 않다.

### 3. 분위수 — 정의가 하나가 아니다

```text
  같은 10개 값: 12 15 17 20 22 25 28 30 35 400

  도구·방법                                 Q1      중앙값    Q3
  Python statistics.quantiles 'exclusive'   16.5    23.5     31.25    ← 기본값
  Python statistics.quantiles 'inclusive'   17.75   23.5     29.5
  PostgreSQL 17 percentile_cont             17.75   23.5     29.5     ← 보간(연속)
  PostgreSQL 17 percentile_disc             17      22       30       ← 실제 값 중 하나
```

- Python 3.12 문서: `quantiles(..., method='exclusive')`가 기본이다. i번째(정렬된 m개 중) 값 아래 비율을 i/(m+1)로 본다 — 모집단에 표본보다 더 극단적인 값이 있을 수 있는 경우용. `'inclusive'`는 (i−1)/(m−1) — 최솟값·최댓값을 0%·100%로 본다. 두 방법 모두 가장 가까운 두 값 사이를 선형 보간한다.
- PostgreSQL 17 문서: `percentile_cont`는 필요하면 인접 값 사이를 보간한다. `percentile_disc`는 순서상 위치가 주어진 비율 이상이 되는 **첫 값**을 돌려준다(실제 데이터 값).
- 이 실험에서 PostgreSQL `percentile_cont`는 Python `'inclusive'`와 같은 값을 냈다. 다른 도구(스프레드시트·NumPy·Prometheus 히스토그램)도 각자 정의가 있다 — 서로 다른 도구의 분위수를 비교할 때는 방법을 맞춘다. 백분위의 병합·히스토그램 근사는 [data-analysis 05](../05-percentiles-and-latency-distributions/2-summary.md).

### 4. 이상치 — 투키 울타리와 박스플롯

```text
          울타리 아래                                 울타리 위
         Q1 − 1.5·IQR                               Q3 + 1.5·IQR
             0.125       17.75  23.5  29.5           47.125
               :   ├─────────[════|════]──────────┤    :                 ●  400
               :  min=12       Q1  중앙값 Q3      35   :              (울타리 밖 = 점으로)
```

- OpenIntro 2.1.5의 박스플롯: 상자 = Q1~Q3, 가운데 선 = 중앙값. *수염(whisker)*은 상자에서 최대 1.5 × IQR까지 데이터가 있는 곳까지 뻗고, 그 밖의 관찰은 점으로 찍는다. 이 데이터의 울타리는 17.75 − 1.5 × 11.75 = 0.125, 29.5 + 1.5 × 11.75 = 47.125다(아래 실험 출력은 소수 둘째 자리로 찍어 0.12·47.12).
  - *5수치 요약(five-number summary)*: 최솟값·Q1·중앙값·Q3·최댓값.
- 1.5 × IQR은 **이상치 후보를 표시하는 관례**다. 그 값이 오류라는 판정이 아니다. 울타리 밖 값이 측정 오류인지, 중요한 꼬리(느린 요청·대량 주문)인지는 도메인이 정한다.
  - 흔한 오해: "울타리 밖 = 지워도 되는 값." 지연 데이터에서 울타리 밖은 대개 **가장 중요한** 사용자 경험이다.
- 박스플롯과 투키의 관계: Tukey가 1970년 『Exploratory Data Analysis』 예비판에서 "schematic plot"으로 처음 소개했고, 1977년 정식 출판 뒤 널리 알려졌다(Wickham·Stryjewski "40 years of boxplots" 2011 원문, Wikipedia "Box plot"도 같은 내용). 투키 원서 본문은 열지 못했다.

### 실험: 이상값 하나·분위수 정의·선택 알고리즘 (Python 3.12, PostgreSQL 17)

```python
base = [12, 15, 17, 20, 22, 25, 28, 30, 35]           # 응답 시간 ms (예시)
for last in (40, 400, 4000):
    x = base + [last]; q = st.quantiles(x, n=4, method="inclusive")
    print(st.fmean(x), st.median(x), st.stdev(x), q[2] - q[0])
```

(실험 환경: 호스트 Python 3.12.3과 `python:3.12-slim`(3.12.14)에서 출력 동일. PostgreSQL 17.11은 `postgres:17` 컨테이너, `--network none`, `psql`.)

```text
마지막 값    40: 평균    24.4 중앙값  23.5 표본표준편차     9.0 IQR(inclusive) 11.75
마지막 값   400: 평균    60.4 중앙값  23.5 표본표준편차   119.5 IQR(inclusive) 11.75
마지막 값  4000: 평균   420.4 중앙값  23.5 표본표준편차  1257.8 IQR(inclusive) 11.75
quantiles(method='exclusive') = [16.5, 23.5, 31.25]
quantiles(method='inclusive') = [17.75, 23.5, 29.5]
stdev(n-1) = 119.53  pstdev(n) = 113.4
울타리 [0.12, 47.12] 밖 = [400]
5수치(min,Q1,med,Q3,max): 12 17.75 23.5 29.5 400
quickselect 중앙값 == statistics.median: True 20.0914
로그정규 20만1건: 평균 33.00 중앙값 20.09 평균보다 작은 비율 0.690
```

```text
-- PostgreSQL 17.11, 같은 10개 값
       cont        |    disc    | avg  | sd_samp | sd_pop
 {17.75,23.5,29.5} | {17,22,30} | 60.4 |  119.53 | 113.40
```

- 관찰 1: 값 하나를 40 → 4000으로 바꾸자 평균은 24.4 → 420.4, 표준편차는 9.0 → 1257.8로 움직였다. 중앙값(23.5)과 IQR(11.75)은 그대로다. OpenIntro 2.1.6의 대출 금리 표와 같은 현상이다.
- 관찰 2: 같은 데이터의 Q1이 방법에 따라 16.5·17.75·17로 다르다. PostgreSQL `percentile_cont` = Python `'inclusive'`, `stddev_samp`·`stddev_pop` = Python `stdev`·`pstdev`.
- 관찰 3: 직접 짠 quickselect(무작위 피벗, 시드 1)가 로그정규 200,001개(시드 42)에서 `statistics.median`과 같은 값을 냈다.
- 관찰 4: 로그정규(중앙값 e³ ≈ 20.09, σ=1)에서 평균 33.00, 값의 69.0%가 평균보다 작다. 꼬리가 평균을 위로 끈다. 지연 분포의 평균 vs 백분위 자세한 실험은 [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md) 5절(같은 모양에서 "평균보다 느린 요청 30.9%")과 data-analysis 05.

## 쓰이는 자료구조·알고리즘

- **선택 알고리즘(중앙값 O(n))** — 정렬(O(n log n)) 없이 k번째 값만 찾는다. 무작위 피벗 quickselect는 **평균** O(n)이고 최악은 O(n²)이다. [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md)(퀵셀렉트) · [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md)
- **두 힙으로 스트리밍 중앙값** — 값이 하나씩 들어올 때 아래 절반(최대 힙)·위 절반(최소 힙)을 유지한다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **온라인 평균·분산** — 값 하나씩 갱신하는 방식(Welford 류)은 큰 수에서 상쇄 오차를 줄인다. 수치 안정성은 [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md).
- **분위수의 근사(히스토그램·t-digest)** — 값을 다 저장할 수 없을 때. [data-analysis 05](../05-percentiles-and-latency-distributions/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상(숫자가 틀린 모양) | 원리 | 확인 |
|---|---|---|
| 평균이 "대부분의 경험"과 안 맞는다 | 치우친 분포에서 평균은 꼬리에 끌린다 | 평균과 중앙값을 나란히, 평균보다 작은 값 비율 |
| 표준편차가 대부분 값이 모인 폭(IQR)보다 훨씬 크다 | 극단값 하나가 제곱으로 키운다 | IQR과 비교, 상위 몇 개 값 직접 보기 |
| Python과 SQL의 사분위수가 다르다 | 분위수 정의(보간 방법) 차이 | 양쪽 방법 명시: `'inclusive'` ↔ `percentile_cont` |
| 이상치를 지웠더니 p99가 좋아졌다 | 꼬리를 지운 것 | 울타리 밖 값이 오류인지 실제 경험인지 원천 로그로 확인 |

### 2. SQL로 한 번에 요약 (PostgreSQL 17)

```sql
SELECT count(*)                                                  AS n,
       round(avg(ms)::numeric, 1)                                AS mean,
       percentile_cont(0.5)  WITHIN GROUP (ORDER BY ms)          AS median,
       percentile_cont(ARRAY[0.25, 0.75]) WITHIN GROUP (ORDER BY ms) AS q1_q3,
       round(stddev_samp(ms)::numeric, 2)                        AS sd,
       min(ms), max(ms)
FROM lat;
```

- 대시보드 한 칸에 평균 하나만 두지 않는다. 최소한 중앙값과 상위 백분위를 같이 둔다.

### 3. Java 21로 같은 요약

```java
// 정렬 후 inclusive 방식 분위수: (n-1)·p 위치를 선형 보간 (Python 'inclusive', PostgreSQL percentile_cont와 같은 정의)
static double quantileInclusive(double[] sorted, double p) {
    double pos = (sorted.length - 1) * p;
    int lo = (int) Math.floor(pos), hi = (int) Math.ceil(pos);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}
```

- 실행 확인(OpenJDK 21.0.12, `eclipse-temurin:21-jdk`): 위 10개 값에서 p = 0.25·0.5·0.75 → 17.75·23.5·29.5. PostgreSQL `percentile_cont`와 같다.
- 정의를 코드 주석에 적는다. 다른 팀의 숫자와 비교할 때 이 한 줄이 시간을 아낀다.

## 장애 시나리오와 대처

### 1. 치우친 분포에 평균 보고 → 대부분의 경험과 괴리 (⚠ 커리큘럼)

- 현상: "평균 응답 60ms, SLO 100ms 이내"로 안심했는데 고객 불만이 계속된다.
- 보이는 형태: 중앙값 23.5ms, 상위 몇 %는 400ms 이상. 평균은 어느 쪽 경험과도 맞지 않는다.
- 원인: 오른쪽 치우침. 평균이 꼬리에 끌려 "가운데"도 "꼬리"도 대표하지 못한다.
- 대처: 체감 지표는 중앙값과 상위 백분위(p95·p99)로, 비용·용량 같은 합계 질문만 평균으로. 백분위 운영은 data-analysis 05, SLO 정의는 [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md).

### 2. 소득·주문 금액 평균으로 기준선 설정

- 현상: "평균 주문 금액 이상이면 VIP 쿠폰" → 쿠폰 대상이 고객의 10%(예시)도 안 된다.
- 원인: 대량 구매 몇 건이 평균을 끌어올렸다. 평균은 "보통 고객"이 아니다.
- 대처: 기준을 분위수(예: 상위 20%)로 정의한다. 분위수 정의(`percentile_cont`/`disc`)를 명시한다.

### 3. 리포트 간 사분위수 불일치

- 현상: 데이터팀(Python) 리포트의 Q1 16.5ms, 백엔드팀(PostgreSQL) 대시보드 17.75ms. "어느 쪽이 버그냐"로 하루를 썼다.
- 원인: Python `statistics.quantiles` 기본값 `'exclusive'` vs PostgreSQL `percentile_cont`(= `'inclusive'`와 같은 값).
- 대처: 분위수 정의를 지표 명세에 적는다(`method='inclusive'` 또는 `percentile_cont`). 분위 근처에 값이 촘촘한 데이터는 크면 차이가 작아지지만 작은 그룹(세그먼트별)에서는 차이가 커진다. 분위가 값이 크게 뛰는 자리에 걸리면 표본이 커도 차이가 남는다([05](../05-percentiles-and-latency-distributions/2-summary.md) 2절)(해석).

### 4. 이상치를 기계적으로 삭제

- 현상: 1.5 × IQR 밖 값을 "노이즈"로 지운 뒤 지연이 개선됐다고 보고했다.
- 보이는 형태: 대시보드의 최댓값·p99가 갑자기 낮아졌는데 사용자 불만은 그대로다.
- 원인: 울타리는 이상치 **후보** 표시 관례다. 지연 꼬리는 실제 사용자 경험이다.
- 대처: 지우기 전에 원인 분류(측정 오류·봇·실제 느린 요청). 지우면 지운 규칙과 개수를 함께 보고한다. 측정 오류 걸러내기는 [data-analysis 18](../18-data-cleaning-and-quality/2-summary.md)(정제).

### 5. 분산 계산의 정밀도 손실

- 현상: 큰 값(예: epoch 밀리초 타임스탬프)의 분산을 `(Σx² − (Σx)²/n)/(n − 1)` 한 번에 계산했더니 엉뚱한 값이 나왔다.
- 보이는 형태(실험, 호스트 Python 3.12.3, 시드 42): 1.79×10¹² 근처에 균등(0,1) 잡음 1,000개를 더한 값. 이론 분산 1/12 ≈ 0.0833인데 한 번에 계산한 값은 `5.50306e+08`, `statistics.variance`는 `0.0828404`.
- 원인: 비슷한 큰 수(Σx², (Σx)²/n)의 뺄셈에서 생기는 상쇄 오차. 부동소수점의 유효 자릿수가 차이를 담지 못한다.
- 대처: 평균을 먼저 빼는 두 단계 계산이나 온라인(Welford 류) 갱신을 쓴다. 표준 라이브러리(`statistics.variance`)를 우선 쓴다 — [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md).

## 핵심 문장

- 중심(평균·중앙값)과 산포(표준편차·IQR) 각각에 극단값에 끌리는 것과 안 끌리는 것이 있다. 중앙값·IQR은 로버스트하다(OpenIntro 2.1.6).
- 평균은 합계로 확장되는 질문(비용·용량)에, 중앙값과 백분위는 "보통 사람이 겪는 값" 질문에 맞다.
- 표본분산은 n − 1로 나눈다. Python `stdev`·PostgreSQL `stddev_samp`가 그 정의다.
- 분위수 정의는 도구마다 다르다. Python 3.12 `quantiles` 기본값(`'exclusive'`)과 PostgreSQL 17 `percentile_cont`는 같은 데이터에서 다른 Q1을 낼 수 있다.
- 1.5 × IQR 울타리는 이상치 후보를 표시하는 관례다. 지울지 여부는 도메인이 정한다.

## 관련 주제·근거

- 선행: [01-data-types-and-measurement](../01-data-types-and-measurement/2-summary.md) · [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md)
- 후속: [06-exploratory-data-analysis](../06-exploratory-data-analysis/2-summary.md) · 백분위·지연 분포([05](../05-percentiles-and-latency-distributions/2-summary.md))·표본 분포([07](../07-sampling-distributions-and-clt/2-summary.md))
- 다른 영역: [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) · [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) · [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md) · [reliability/19-performance-measurement](../../reliability/19-performance-measurement/2-summary.md) · [web-platform/20-performance-budgets-and-regression-gates](../../web-platform/20-performance-budgets-and-regression-gates/2-summary.md)(반복 측정의 중앙값)
- 근거
  - OpenIntro Statistics 4판 2.1 "Examining numerical data" — 2.1.2 평균, 2.1.3 히스토그램과 모양(치우침), 2.1.4 분산·표준편차(n − 1), 2.1.5 박스플롯·사분위수·중앙값(1.5 × IQR 수염, 이상치), 2.1.6 로버스트 통계량(대출 금리 표, 전형값 vs 합계 질문). 2.2 "Considering categorical data"(분할표·비율). 확인 경로: https://www.openintro.org/book/os/ 목차 + GitHub `OpenIntroStat/openintro-statistics` `ch_summarizing_data/TeX/ch_summarizing_data.tex` + 4판 PDF(Internet Archive 사본) 목차·본문(2.1.6 그림 2.12, 각주 13의 "1,000 loans")
  - Python 3.12 `statistics` 문서 https://docs.python.org/3.12/library/statistics.html — `median`(짝수 개는 가운데 두 값 평균), `variance`/`stdev`(n − 1, 베셀 보정), `pvariance`/`pstdev`, `quantiles`(`'exclusive'` 기본, `'inclusive'`)
  - NIST/SEMATECH e-Handbook 6.3.2 https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm — 표본분산 s²는 모분산의 불편 추정, 표본표준편차 s는 모표준편차의 불편 추정이 아님
  - PostgreSQL 17 문서 "Aggregate Functions" https://www.postgresql.org/docs/17/functions-aggregate.html — `percentile_cont`(보간), `percentile_disc`(첫 값)
  - Tukey, J. W. (1977) 『Exploratory Data Analysis』(Addison-Wesley; 1970 예비판) — 원서 본문 미열람. 박스플롯 1970 도입·1977 정식 출판은 Wickham, H. & Stryjewski, L. (2011) "40 years of boxplots" https://vita.had.co.nz/papers/boxplots.pdf (Internet Archive 사본으로 열람)와 Wikipedia "Box plot"(2차)
- 실험 목록
  - 이상값 크기(40/400/4000)에 따른 평균·중앙값·표준편차·IQR, `quantiles` 두 방법, `stdev`/`pstdev`, 투키 울타리, quickselect vs `median`(로그정규 200,001개, 시드 42·1) — Python 3.12.3(호스트)·3.12.14(`python:3.12-slim`, `--network none`) 출력 동일
  - `percentile_cont`/`percentile_disc`/`stddev_samp`/`stddev_pop` — PostgreSQL 17.11(`postgres:17`, `--network none`, `psql`)
  - `quantileInclusive` — OpenJDK 21.0.12(`eclipse-temurin:21-jdk`)
  - 한 번에 계산한 분산 vs `statistics.variance`(1.79×10¹² + 균등 잡음 1,000개, 시드 42) — 호스트 Python 3.12.3
