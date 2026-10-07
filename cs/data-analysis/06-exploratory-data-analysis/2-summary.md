# data-analysis/06-exploratory-data-analysis — EDA: 요약하기 전에 분포와 관계를 먼저 본다 — 정리 (힌트)

## 해결하는 문제

요약 숫자가 같으면 데이터도 같을까?

```text
  네 데이터셋 (Anscombe 1973)          평균x  분산x  평균y  분산y   상관   회귀선
  I   II   III   IV   — 모두           9.00   11.00  7.50  ≈4.125 ≈0.816  y = 3.00 + 0.500x
                                       (Python 3.12 실험 — 아래)

  그런데 산점도를 그리면
  I  : 흩어진 직선 관계        II : 휘어진 곡선
  III: 직선 + 이상점 하나       IV : x가 거의 다 8, 점 하나가 상관을 만듦
```

- 요약 통계는 데이터를 **줄인** 것이다. 줄이면서 모양(봉우리 수·곡선·이상점·뭉침)을 버린다. 버린 것이 결론을 바꿀 수 있다.
  - *탐색적 데이터 분석(EDA, exploratory data analysis)*: 모델을 세우거나 검정하기 전에 그림과 간단한 요약으로 데이터의 모양·관계·이상을 먼저 살피는 일. Tukey가 1977년 책 『Exploratory Data Analysis』로 널리 알린 말이다[?] — 원서 미열람.

쉬운 예: 반 평균 70점이 두 반에서 같다. 한 반은 모두 65~75점이고, 다른 반은 절반이 40점·절반이 100점이다. 같은 수업을 하면 안 된다.

똑같은 구조다.\
"평균 지연 20ms"가 모두 20ms 근처인 서비스와, 80%는 5ms·20%는 80ms인 서비스(캐시 적중/미스)는 해결책이 완전히 다르다.

실무 예:
- 평균·표준편차만 보고 지연을 정규분포로 모델링해 타임아웃을 정했다. 실제로는 두 봉우리였다.
- 상관계수 0.8을 보고 "강한 선형 관계"로 회귀를 돌렸는데, 점 하나가 상관을 다 만들었다.
- 일별 매출 평균은 평소와 같았는데, 히스토그램을 보니 0원 주문이 갑자기 늘었다(결제 오류).

## 동작·원리

### 1. EDA의 순서 — 그림 먼저, 요약은 그 다음

```text
  ① 한 변수씩: 히스토그램 → 봉우리 몇 개? 어느 쪽 꼬리? 이상한 값(0·음수·상한 붙음)?
  ② 그룹별로:  나란히 박스플롯 / 겹친 히스토그램 → 그룹 차이가 위치인가 모양인가?
  ③ 두 변수:   산점도 → 직선? 곡선? 뭉침? 영향 큰 점?
  ④ 그다음에야: 평균·표준편차·상관·회귀 같은 요약과 모델
```

- OpenIntro 2.1은 수치형 데이터를 산점도(2.1.1) → 점그림과 평균(2.1.2) → 히스토그램과 모양(2.1.3) → 분산(2.1.4) → 박스플롯(2.1.5) → 로버스트 통계(2.1.6) → 변환(2.1.7) 순서로 다룬다. 그룹 간 비교는 2.2.6 "Comparing numerical data across groups"(나란히 박스플롯·겹친 히스토그램)다.
- 커리큘럼이 가리킨 OpenIntro 2.3은 4판 원본에서 "Case study: malaria vaccine"(무작위화 시뮬레이션 사례)이다. EDA라는 이름의 절은 원본 LaTeX에 주석 처리된 채 남아 있다. 그래서 이 노트는 EDA 도구의 근거로 2.1·2.2를 쓴다.
- 요약 숫자 자체(평균·중앙값·IQR)는 [04-descriptive-statistics](../04-descriptive-statistics/2-summary.md)가 단일 출처다.

### 2. 히스토그램 — 구간 폭이 모양을 바꾼다

```text
  같은 10,000건, 10ms 폭                          같은 10,000건, 60ms 폭
    0-  9ms 8047 ################...                0- 59ms 8086 ################...
   10- 19ms    0                                   60-119ms 1914 ###################
   …
   60- 69ms  235 ##                               ← 두 칸뿐: 두 번째 봉우리가
   70- 79ms  686 #######                             70~90ms에 모여 있다는 모양이 사라짐
   80- 89ms  682 #######
   90- 99ms  266 ###
```

- *히스토그램(histogram)*: 값의 범위를 구간(bin)으로 나누고 구간마다 개수를 막대로 그린 그림.
- Wilke 『Fundamentals of Data Visualization』 7.1: 히스토그램의 모양은 구간 폭에 달렸다. 너무 좁으면 뾰족하고 어수선해 주된 경향이 묻히고, 너무 넓으면 작은 특징이 사라진다. **여러 폭을 시도하라**고 권한다.
- 도구의 기본 구간 폭은 그 데이터에 맞는다는 보장이 없다(같은 절). 지연처럼 범위가 넓은 값은 로그 축 구간도 시도한다(OpenIntro 2.1.7의 변환).
  - *봉우리(mode)*: 히스토그램에서 솟은 부분. 하나면 단봉(unimodal), 둘이면 쌍봉(bimodal), 여럿이면 다봉(multimodal)이다(OpenIntro 2.1.3).

### 3. 박스플롯은 쌍봉을 못 본다

```text
  쌍봉 지연 10,000건의 박스플롯 (inclusive 사분위)

  1.5 ├[4.5 ═ 5.3 ═ 6.5]┤8.6  : 울타리 9.5      ●●●●●●●●●●●●●●●●●●●●  (1,953개 점, 약 47~115ms)
       └ 상자 = 캐시 적중 봉우리 안쪽            └ 캐시 미스 봉우리 전체가 "이상치"로 찍힌다
  (수염 끝 = 울타리 안의 실제 최댓값 8.6, 최솟값 1.5 — 재실행으로 확인)
```

- 박스플롯은 5수치(최솟값·Q1·중앙값·Q3·최댓값)와 울타리 밖 점만 그린다. 봉우리가 몇 개인지는 그리지 않는다.
- Wilke 9.1: 바이올린 그림은 쌍봉 데이터를 정확히 보여 주지만 박스플롯은 그렇지 못하다. 단 바이올린은 밀도 추정이라, 같은 절은 그룹마다 점이 충분한지 먼저 확인하라고 적는다. 같은 절에서 박스플롯은 Tukey가 1970년대 초에 고안했다고 적는다.
- 그래서 박스플롯은 **여러 그룹을 한눈에 비교**할 때 좋고, 한 변수의 모양을 처음 볼 때는 히스토그램을 같이 본다.

### 4. 산점도 — 상관 하나로 줄이기 전에

```text
  Anscombe II (텍스트 산점도)            Anscombe IV
  |                       *   *   *      |                                       *
  |                    *              *  |
  |                *                     *|
  |            *                         |*
  |        *                             |*   ← x = 8에 10개가 세로로
  |    *                                 |*
  |*                                     |*
  +--------------------------------------+---------------------------------------
   곡선인데 r = 0.816                       점 하나(x=19)가 r = 0.817을 만든다
```

- *상관계수(Pearson r)*: 두 변수의 **선형** 관계의 방향과 강도를 −1~+1로 나타낸 값(Python 3.12 `statistics.correlation` 문서: "measures the strength and direction of a linear relationship").
  - 흔한 오해: "r이 크면 관계가 직선이다." II는 곡선이고 IV는 점 하나의 효과인데 r은 I과 같다.
- 단조지만 직선이 아닌 관계는 순위 상관(`statistics.correlation(x, y, method='ranked')`, Spearman)이 더 맞을 수 있다(Python 3.12 문서). 상관과 인과는 [data-analysis 12](../12-correlation-vs-causation/2-summary.md), 회귀의 영향점은 [13](../13-linear-regression/2-summary.md).

### 실험: Anscombe 콰르텟과 쌍봉 지연 (Python 3.12 `statistics`)

Anscombe 자료(11쌍 × 4세트)는 Wikipedia "Anscombe's quartet" 표의 값을 썼다. 원 논문은 F. J. Anscombe, "Graphs in Statistical Analysis", *The American Statistician* 27(1):17–21, 1973(원문 미열람, 서지는 같은 항목으로 확인).

```python
for k, (x, y) in Q.items():
    lr = st.linear_regression(x, y)
    print(k, st.fmean(x), st.variance(x), st.fmean(y), st.variance(y), st.correlation(x, y), lr.intercept, lr.slope)
lat = [rng.gauss(5, 1) if rng.random() < 0.8 else rng.gauss(80, 10) for _ in range(10_000)]   # 시드 42
```

(실험 환경: 호스트 Python 3.12.3과 `python:3.12-slim`(3.12.14)에서 출력 동일.)

```text
세트  mean_x var_x  mean_y var_y  r      절편  기울기
I      9.00 11.00   7.50 4.127  0.816  3.00  0.500
II     9.00 11.00   7.50 4.128  0.816  3.00  0.500
III    9.00 11.00   7.50 4.123  0.816  3.00  0.500
IV     9.00 11.00   7.50 4.123  0.817  3.00  0.500

쌍봉 지연 10,000건: 평균 19.7 중앙값 5.3 표준편차 30.1  평균±10ms 안 비율 0.000
5수치: min 1.5 Q1 4.5 med 5.3 Q3 6.5 max 114.5  울타리 위 9.5 밖 1953건
40ms 기준 분리: 적중 8047건 중앙값 5.0  미스 1953건 중앙값 80.2
```

- 관찰 1: 네 세트의 평균·분산·상관·회귀선이 소수 둘째~셋째 자리까지 같다(Wikipedia 표: 분산 y 4.125 ±0.003, 상관 0.816). 그림은 완전히 다르다(위 텍스트 산점도).
- 관찰 2: 쌍봉 지연의 평균 19.7ms 근처(±10ms)에는 **요청이 하나도 없다**(비율 0.000). 평균은 아무도 겪지 않은 값이다.
- 관찰 3: 박스플롯 기준으로는 캐시 미스 1,953건 전부가 울타리(9.5ms) 밖 "이상치"다. 실제로는 이상치가 아니라 두 번째 무리다.
- 관찰 4: 40ms에서 나누면 각 무리는 단봉이다(중앙값 5.0 / 80.2). 원인(적중/미스)별로 나눠 보는 것이 다음 단계다.
- 이 쌍봉 분포는 예시 모델이다. 실제 캐시 지연의 모양은 서비스마다 다르다(해석).

## 쓰이는 자료구조·알고리즘

- **히스토그램 = 구간 배열 카운터** — 값 → 구간 번호(`floor(v / 폭)`) → 배열 칸 +1. 고정 폭이면 O(1) 갱신. 로그 구간·병합 가능한 히스토그램(HdrHistogram 등)은 [data-analysis 05](../05-percentiles-and-latency-distributions/2-summary.md). 운영 지표의 히스토그램 형은 [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md).
- **박스플롯 = 분위수 3개 + 울타리** — 정렬 또는 선택 알고리즘. [04-descriptive-statistics](../04-descriptive-statistics/2-summary.md) · [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md)
- **큰 데이터의 EDA = 표본** — 전체를 그리기 어려우면 무작위 표본(저수지 표집)으로 먼저 본다. 단, 드문 꼬리는 표본에서 빠질 수 있다. [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md) · [02-sampling-and-bias](../02-sampling-and-bias/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상(판단이 틀린 모양) | 원리 | 확인 |
|---|---|---|
| 평균 근처 값이 실제로 거의 없다 | 다봉 분포 | 히스토그램(여러 구간 폭) |
| 이상치가 "너무 많다"(수십 %) | 이상치가 아니라 다른 무리 | 원인 변수(캐시·지역·버전)로 나눠 히스토그램 |
| 상관이 높은데 예측이 안 맞는다 | 곡선·영향점 | 산점도, 영향 큰 점 빼고 다시 r |
| 평균은 그대로인데 뭔가 이상하다 | 모양 변화(0 급증·상한 붙음) | 값별 빈도 상위, 0·NULL·최댓값 개수 |

### 2. SQL로 텍스트 히스토그램 (PostgreSQL 17)

```sql
-- 10ms 폭 히스토그램: width_bucket(값, 하한, 상한, 칸 수)
SELECT width_bucket(ms, 0, 120, 12) AS bucket,
       (width_bucket(ms, 0, 120, 12) - 1) * 10 AS from_ms,
       count(*) AS n,
       repeat('#', (count(*) / 100)::int) AS bar
FROM lat
GROUP BY bucket ORDER BY bucket;
```

- `width_bucket`은 하한 미만을 0번, 상한 이상을 칸 수 + 1번에 넣는다(PostgreSQL 17 "Mathematical Functions" 표, 하한 < 상한일 때 — 하한 > 상한이면 거울처럼 뒤집힌다). 범위 밖 칸이 크면 범위를 다시 잡는다.
- 실행 확인(PostgreSQL 17.11, `postgres:17`, `--network none`): `width_bucket(x, 0, 120, 12)`이 x = −1 → 0, 0 → 1, 119.9 → 12, 120 → 13, 500 → 13. 구간은 하한 포함·상한 제외다.
- 폭을 10·30·60으로 바꿔 몇 번 그려 본다(Wilke 7.1).

### 3. 그룹별로 나눠 보기

```sql
SELECT cache_hit,
       count(*) AS n,
       percentile_cont(ARRAY[0.25, 0.5, 0.75, 0.99]) WITHIN GROUP (ORDER BY ms) AS q
FROM request_log
GROUP BY cache_hit;
```

- 다봉의 원인 후보(캐시 적중·리전·앱 버전·요청 종류)로 나눠 각 그룹이 단봉인지 본다. 원인을 모르면 data-engineering의 차원 키를 후보로 쓴다 — [data-engineering/03-dimensional-modeling](../../data-engineering/03-dimensional-modeling/2-summary.md).

### 4. Java 21로 텍스트 히스토그램

```java
static void textHistogram(double[] xs, double width, int bins, int perHash) {
    int[] count = new int[bins + 1];                       // 마지막 칸 = 범위 밖
    for (double x : xs) count[Math.min(bins, (int) (x / width))]++;
    for (int i = 0; i <= bins; i++)
        System.out.printf("%5.0f+ %6d %s%n", i * width, count[i], "#".repeat(count[i] / perHash));
}
```

- 음수 값이 있으면 `(int)(x / width)`가 음수가 되므로 하한을 먼저 빼야 한다. 이 함수는 0 이상 값을 가정한다.
- 실행 확인(OpenJDK 21.0.12, `eclipse-temurin:21-jdk`): 값 `{1, 5, 12, 85, 300}`, 폭 10, 칸 12에서 0+ 2개, 10+ 1개, 80+ 1개, 120+(범위 밖) 1개.

## 장애 시나리오와 대처

### 1. 요약 통계만 보고 모델링 → Anscombe 함정 (⚠ 커리큘럼)

- 현상: 두 지표의 상관 0.82를 근거로 선형 회귀로 용량을 예측했다. 예측이 특정 구간에서 크게 빗나간다.
- 보이는 형태: 산점도를 그려 보니 곡선(Anscombe II형)이거나, 대형 고객 하나가 상관을 만들었다(IV형).
- 원인: 상관·회귀선은 직선 관계를 요약하는 숫자다. 가로로 멀리 떨어진 점(높은 지렛대) 하나가 기울기를 크게 끌 수 있다(OpenIntro 8.3). 요약이 모양을 버렸다.
- 대처: 모델 전에 산점도. 영향 큰 점을 빼고 다시 계산해 결론이 유지되는지 본다. 곡선이면 변환(로그)이나 다른 모델 — [data-analysis 13](../13-linear-regression/2-summary.md).

### 2. 쌍봉 지연을 단봉으로 가정한 타임아웃

- 현상: "평균 20ms, 표준편차 30ms → 평균 + 3σ = 110ms면 충분"으로 타임아웃을 정했다(예시).
- 보이는 형태: 정상 상황에서는 맞는 듯하다가, 캐시 적중률이 떨어지자 미스 무리(80ms 중심)의 꼬리가 타임아웃에 걸리기 시작한다.
- 원인: 두 무리가 섞인 분포를 평균·표준편차 하나로 요약했다. 정규분포 가정의 위험은 [math/09-common-distributions](../../math/09-common-distributions/2-summary.md) 4절.
- 대처: 원인별로 나눠 각 무리의 백분위를 본다. 타임아웃은 분포의 백분위로 정한다 — [reliability/08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md).

### 3. 박스플롯만 보고 "이상치 20%" 제거

- 현상: 박스플롯 울타리 밖 값이 20%라서 노이즈로 지웠다.
- 원인: 울타리 밖이 다른 무리(캐시 미스·다른 리전)였다. 박스플롯은 쌍봉을 보여 주지 못한다(Wilke 9.1).
- 대처: 울타리 밖 비율이 크면 히스토그램과 원인 변수 분할을 먼저 본다. 다른 무리가 아니어도 심하게 치우친 분포면 정상 값이 울타리를 많이 넘는다(Hubert·Vandervieren 2008).

### 4. 구간 폭 하나로 "정상" 판정

- 현상: 기본 구간 폭의 히스토그램이 매끈한 단봉이라 안심했다.
- 원인: 구간이 너무 넓어 작은 봉우리(특정 엔드포인트의 느린 무리)가 한 칸에 묻혔다.
- 대처: 폭을 여러 개 시도하고(Wilke 7.1), 범위가 넓으면 로그 구간으로 본다.

### 5. 평균이 그대로라 지나친 데이터 이상

- 현상: 일별 평균 주문 금액이 평소와 같아 이상 없음으로 봤다. 나중에 0원 주문 급증(결제 오류)과 고액 주문 증가가 상쇄돼 있었음을 알았다(예시).
- 대처: 요약 옆에 0·NULL·최댓값 개수, 값 빈도 상위 몇 개를 같이 본다. 파이프라인 차원의 분포 감시는 [data-engineering/10-data-quality-and-data-observability](../../data-engineering/10-data-quality-and-data-observability/2-summary.md).

## 핵심 문장

- 요약 통계는 모양을 버린다. 평균·분산·상관·회귀선이 같아도 데이터는 전혀 다를 수 있다(Anscombe 1973).
- EDA 순서: 한 변수 히스토그램 → 그룹별 비교 → 두 변수 산점도 → 그다음 요약과 모델.
- 히스토그램의 모양은 구간 폭에 달렸다. 여러 폭을 시도한다(Wilke 7.1).
- 박스플롯은 그룹 비교에 좋지만 쌍봉을 보여 주지 못한다. 울타리 밖이 많으면 다른 무리나 심하게 치우친 꼬리를 의심한다.
- 상관계수는 선형 관계만 잰다. 곡선이나 점 하나의 영향은 산점도로만 보인다.

## 관련 주제·근거

- 선행: [04-descriptive-statistics](../04-descriptive-statistics/2-summary.md) · 후속: 백분위·지연 분포([05](../05-percentiles-and-latency-distributions/2-summary.md)), 상관과 인과([12](../12-correlation-vs-causation/2-summary.md)), 선형 회귀([13](../13-linear-regression/2-summary.md)), 시각화([19](../19-data-visualization-principles/2-summary.md))
- 다른 영역: [math/09-common-distributions](../../math/09-common-distributions/2-summary.md)(정규 가정의 한계) · [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md)(히스토그램 지표) · [reliability/08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md) · [data-engineering/10-data-quality-and-data-observability](../../data-engineering/10-data-quality-and-data-observability/2-summary.md)
- 근거
  - OpenIntro Statistics 4판 2.1(2.1.1 산점도, 2.1.3 히스토그램과 모양·봉우리, 2.1.5 박스플롯, 2.1.7 변환), 2.2.6 그룹 간 수치 비교. 2.3은 "Case study: malaria vaccine"(커리큘럼 표기 OpenIntro 2.3과 주제 불일치 — 위 1절). 확인 경로: https://www.openintro.org/book/os/ 목차 + GitHub `OpenIntroStat/openintro-statistics` `ch_summarizing_data/TeX/ch_summarizing_data.tex`(`%\section{Exploratory data analysis}` 주석 줄) + 4판 PDF(Internet Archive 사본) 목차(2.3 "Case study: malaria vaccine", 81쪽)
  - Wilke, C. O. 『Fundamentals of Data Visualization』 온라인판 — 7장 "Visualizing distributions: Histograms and density plots" 7.1(구간 폭) https://clauswilke.com/dataviz/histograms-density-plots.html · 9장 "Visualizing many distributions at once" 9.1(박스플롯·울타리·바이올린과 쌍봉, Tukey 1970년대 초) https://clauswilke.com/dataviz/boxplots-violins.html
  - Anscombe, F. J. (1973) "Graphs in Statistical Analysis", *The American Statistician* 27(1):17–21, doi:10.1080/00031305.1973.10478966 — 원문 미열람, 자료 값·서지는 Wikipedia "Anscombe's quartet"
  - OpenIntro Statistics 4판 8.3 "Types of outliers in linear regression"(높은 지렛대·영향점) · Hubert, M. & Vandervieren, E. (2008) "An adjusted boxplot for skewed distributions", *Computational Statistics & Data Analysis* — 치우친 분포에서 정상 값의 울타리 초과(로그정규 μ=0·σ=1에서 약 7.76%) https://wis.kuleuven.be/statdatascience/robust/papers/2008/hubertvandervieren_adjustedboxplot_csda_2008.pdf/%40%40download/file/HubertVandervieren_AdjustedBoxplot_CSDA_2008.pdf
  - Tukey, J. W. (1977) 『Exploratory Data Analysis』, Addison-Wesley(1970 예비판) — 서지는 Wickham·Stryjewski "40 years of boxplots"(2011) 참고문헌으로 확인, 원서 본문 미열람
  - Python 3.12 `statistics` 문서(`correlation` 선형·`'ranked'`, `linear_regression`) https://docs.python.org/3.12/library/statistics.html · PostgreSQL 17 "Mathematical Functions"(`width_bucket`) https://www.postgresql.org/docs/17/functions-math.html
- 실험 목록
  - Anscombe 네 세트의 평균·분산·상관·회귀선과 텍스트 산점도, 쌍봉 지연 10,000건(시드 42)의 텍스트 히스토그램(10ms·60ms 폭)·5수치·울타리 밖 개수·원인별 분리 — Python 3.12.3(호스트)·3.12.14(`python:3.12-slim`, `--network none`) 출력 동일
  - `textHistogram` — OpenJDK 21.0.12(`eclipse-temurin:21-jdk`)
  - `width_bucket` 경계값(−1·0·119.9·120·500) — PostgreSQL 17.11(`postgres:17`, `--network none`, `psql`)
