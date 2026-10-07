# data-analysis/28-da-incidents — 실사건: Literary Digest 여론조사(1936) · Google Flu Trends 과대 추정(2011~2013) · Reinhart–Rogoff 스프레드시트 오류(재현 2013) · 영국 PHE 확진 15,841건 누락(2020-10) — 분석 관점 — 정리 (힌트)

## 해결하는 문제

네 사건은 모두 **숫자는 나왔는데 판단이 틀린** 사고다. 공개 자료가 적는 문제는 멈춘 시스템이 아니라 틀리거나 빠진 숫자다. 틀린 것은 표본·모형·수식 범위·날짜 축이었다.

```text
  Literary Digest 1936   우편 여론조사 약 240만 응답(2차 출처) ── 표집 틀 편향 + 무응답 편향 ──▶ 패자를 승자로 예측
  Google Flu Trends      검색량으로 독감 진료 비율 추정 ────────── 과적합·측정 도구 변화 ───────▶ 2011-08 ~ 2013-09에 108주 중 100주 과대
  Reinhart–Rogoff 2010   부채/GDP 90% 이상 나라의 평균 성장률 ──── 수식 범위 누락·선택적 제외·가중 ─▶ 2.2%가 −0.1%로 발표(재현 2013)
  영국 PHE 2020-10       양성 결과 → 일일 확진 집계 ─────────────── 파일 크기 한도에서 조용히 빠짐 ──▶ 15,841건이 보고에서 빠지고 뒤늦게 몰려 들어옴
```

쉬운 예: 체중계 네 개다.\
하나는 늘 무거운 사람만 올라선다(표본). 하나는 작년 겨울에만 맞춰 둔 눈금이다(모형). 하나는 앞자리 숫자 하나를 빼고 읽는다(수식 범위). 하나는 어제 잰 몸무게를 오늘 칸에 적는다(날짜 축).\
넷 다 숫자는 나온다. 그 숫자가 무엇을 잰 것인지가 틀렸다.

똑같은 구조다.\
세 사건은 결과를 **다른 기준과 대조**했을 때 드러났다. 실제 선거 결과, CDC 감시 통계, 작업 파일로 다시 계산한 평균이다. PHE는 발견 경위가 발표문에 없지만, 원천 건수와의 대조가 같은 역할을 했을 장치다(해석).

실무 예:
- 앱 설문 응답 2만 건으로 "사용자 만족도"를 보고한다. 응답한 사람이 누구인지 보지 않으면 Literary Digest와 같은 모양이 된다([08-4](../08-confidence-intervals/2-summary.md)).
- 검색·클릭 로그로 수요를 예측하는 모형을 학습 기간에만 맞춘다. 검색 UI가 바뀌면 GFT와 같은 모양이 된다.
- 스프레드시트의 `AVERAGE(L30:L44)` 한 칸이 정책 문서의 근거가 된다. 범위가 데이터보다 짧으면 Reinhart–Rogoff와 같은 모양이 된다.

  - *1차 출처*: 사건의 당사자나 원 분석을 다시 계산한 연구자가 직접 쓴 문서 — 논문 원문·저자 사본, 정부 발표문, 정부 기록. 이 노트는 날짜·수치를 원문 그대로 옮기고, 원문에 없는 연결은 "해석"이라고 표시한다. 백과사전·언론 보도는 "2차 출처"로 따로 밝힌다.
  - *증상 → 사건*: 네 사건은 [27](../27-da-symptom-index/2-summary.md)의 증상(10절 표본이 대표하지 못함, 3-2절·11절 모델이 운영에서 깨짐, 2절 합계가 안 맞음·4절 구성이 평균을 움직임, 6절 날짜 경계)이 실제 사고가 된 모습이다.
  - PHE 사건의 **파이프라인 관점**(중간 형식의 행 한도, 행 수 대조, 복구 재적재)은 [data-engineering/17-de-incidents](../../data-engineering/17-de-incidents/2-summary.md) 사건 1이 맡는다. 이 노트는 같은 원문을 **분석 관점**(날짜 축·추세·수준과 구성)으로 읽는다.

## 동작·원리

### 사건 1 — Literary Digest 1936 대통령 선거 여론조사: 큰 표본, 틀린 예측

출처
- Peverill Squire, "Why the 1936 Literary Digest Poll Failed", *Public Opinion Quarterly* 52(1), 1988, p. 125~, DOI 10.1086/269085. 본문은 JSTOR·출판사 페이지가 2026-10-08에 접근 차단(자바스크립트 확인 페이지·403)이라 열지 못했다. **초록**은 OpenAlex 메타데이터(`api.openalex.org/works/doi:10.1086/269085`)로 읽었다.
- 미국 국립문서보관소(National Archives, Office of the Federal Register), "1936 Electoral College Results" <https://www.archives.gov/electoral-college/1936>(2026-10-08 열람).
- 2차 출처: Wikipedia "The Literary Digest"(2026-05-30 판, 2026-10-08 열람) <https://en.wikipedia.org/wiki/The_Literary_Digest>. 이 문서는 Freedman·Pisani·Purves 『Statistics』 4판(2007) pp. 335–336 등을 인용한다. 그 책과 1936년 잡지 원본(10월 31일 호 등)은 열지 못했다 — Internet Archive에 1936년 호가 없었고 HathiTrust 검색은 403.

#### 사실 (원문)

- Squire 초록: "Using data from a 1937 Gallup survey which asked about participation in the Literary Digest poll I conclude that the magazine's sample and the response were both biased and jointly produced the wildly incorrect estimate of the vote. But, if all of those who were polled had responded, the magazine would have, at least, correctly predicted Roosevelt the winner."
- 국립문서보관소: 선거인단 Roosevelt 523, Landon 8(총 531, 과반 266). Landon이 이긴 주는 Maine(5)과 Vermont(3)뿐이다.

#### 2차 출처의 수치 `[?]`

- 잡지는 약 1,000만 명에게 투표 용지를 보냈고 약 238만 명이 응답했다. Landon의 득표율 57.08%, 선거인단 370명을 예측했다. 실제 Roosevelt 득표율은 60.8%였다. Gallup은 약 5만 명 표본으로 Roosevelt 55.7%를 예측했다.
- 위 수치는 모두 Wikipedia(2차)에서 옮겼고 원 잡지·Freedman 외 원문으로 확인하지 못했다 `[?]`. 표집 틀이 "잡지 구독자, 자동차 등록 명부, 전화 가입자 명부"였다는 설명도 같은 2차 출처다 `[?]`.

#### 원리 — n을 키워도 편향은 줄지 않는다

```text
  모집단(유권자) ──▶ 표집 틀(명부) ──▶ 보낸 표본 ──▶ 응답자 ──▶ 추정
                     │ 명부에 오를 확률이       │ 응답할 확률이
                     │ 층마다 다름(틀 편향)      │ 지지 후보마다 다름(무응답 편향)
                     ▼                         ▼
                 Squire: 둘 다 편향, "jointly" 틀린 추정을 만듦. 전원이 응답했다면 승자는 맞혔을 것
```

- 표본이 크면 **표집 오차**(우연에 의한 흔들림)는 준다. 뽑히는 확률이 사람마다 다르면 생기는 **편향**은 n과 상관없이 남는다([02](../02-sampling-and-bias/2-summary.md) · [08-4](../08-confidence-intervals/2-summary.md)).
  - *표집 틀(sampling frame)*: 실제로 뽑을 수 있는 대상의 목록. 모집단과 다르면 틀에 없는 사람은 뽑힐 확률이 0이다.
  - *무응답 편향*: 응답한 사람과 안 한 사람의 답이 체계적으로 다를 때 생기는 편향([02-1](../02-sampling-and-bias/2-summary.md)).
    - 흔한 오해: "응답 수가 수백만이면 정확하다." 응답 수는 우연 오차의 크기만 정한다. 누가 응답했는지가 편향을 정한다.
- Squire의 결론 구조(초록): 틀 편향만으로는 승자가 바뀌지 않았을 것이고, 무응답 편향이 겹쳐 예측이 뒤집혔다. 아래 실험은 이 구조를 합성 숫자로 흉내 낸다.

#### 실험: 틀 편향 + 무응답 편향 모형 (`digest_sim.py`)

모든 수치는 예시(합성)다. 1936년 유권자 구성·응답률을 재현한 것이 아니다. 두 층(명부에 잘 오르는 층 25%, 나머지 75%)의 현직(R) 지지율, 명부에 오를 확률, 지지 후보별 응답 확률을 정했다.

```python
SUPPORT_R = {"high": 0.40, "low": 0.68}        # (예시) 층별 현직 지지율
IN_FRAME  = {"high": 0.80, "low": 0.20}        # (예시) 명부에 오를 확률
RESPOND   = {"R": 0.18, "L": 0.30}             # (예시) 반송 확률 — 현직 반대가 더 잘 응답
frame = [x for x in pop if rng.random() < IN_FRAME[x[0]]]
resp  = [x for x in frame if rng.random() < RESPOND[x[1]]]
srs   = rng.sample(pop, 3_000)
# 95% 구간은 단순 무작위 표본 공식 p ± 1.96·√(p(1−p)/n)을 그대로 적용(편향 표본에는 맞지 않는 공식 — 일부러)
```

(실험, 호스트 Python 3.12.3 표준 라이브러리(`random`·`math`), `random.Random(1936)`, 모집단 100만 명, 1회 실행, i7-13700HX, 2026-10-08)

```text
모집단 R 득표율(진실)               61.0%  n=1,000,000
명부 전원이 응답했다면(표집 틀 편향만)        51.9%  n=349,373  95% 구간 [ 51.8%,  52.1%]  R 승  진실 포함=False
명부 + 무응답 편향(실제 반송분)           39.1%  n= 83,514  95% 구간 [ 38.8%,  39.5%]  L 승  진실 포함=False
단순 무작위 표본 3,000               61.3%  n=  3,000  95% 구간 [ 59.5%,  63.0%]  R 승  진실 포함=True
```

- 관찰
  - 틀 편향만이면 51.9%로 승자는 맞혔다. 무응답 편향이 겹치자 39.1%로 승자가 바뀌었다. Squire 초록의 결론 구조와 같은 모양이다(수치는 모형의 것).
  - 8만 명 넘는 응답의 구간 폭은 ±0.3%p 남짓으로 매우 좁은데 진실(61.0%)에서 22%p 떨어져 있다. 3,000명 무작위 표본은 구간이 ±1.7%p 남짓으로 넓지만 진실을 포함했다.
- 해석: 구간 공식은 "무작위로 뽑았다"는 전제에서 표집 오차만 잰다. 편향 표본에 쓰면 좁은 구간이 정확성의 착각을 만든다([08-4](../08-confidence-intervals/2-summary.md)).

#### 막았을 장치 (해석)

- 확률 표집: 모든 유권자가 알려진 확률로 뽑히는 틀을 쓴다. 층별 비율을 알면 층화 추출·가중으로 맞춘다([02](../02-sampling-and-bias/2-summary.md)).
- 응답률·응답자 구성 점검: 보낸 수 대비 응답 수, 응답자와 비응답자의 알려진 속성(지역·이전 투표) 비교([02-1](../02-sampling-and-bias/2-summary.md)).
- 외부 기준과 대조: 응답자의 이전 선거 투표 분포를 실제 이전 선거 결과와 비교한다. 다르면 표본이 기울었다는 신호다.
- leaf: [02-1](../02-sampling-and-bias/2-summary.md) · [02-3](../02-sampling-and-bias/2-summary.md) · [08-4](../08-confidence-intervals/2-summary.md) · [27](../27-da-symptom-index/2-summary.md) 10절

### 사건 2 — Google Flu Trends: 학습 기간에 맞춘 모형이 계속 높게 추정 (2011-08 ~ 2013-09 · 분석 발표 2014-03)

출처
- David Lazer, Ryan Kennedy, Gary King, Alessandro Vespignani, "The Parable of Google Flu: Traps in Big Data Analysis", *Science* 343(6176), 2014-03-14, pp. 1203–1205, DOI 10.1126/science.1248506. 저자(Gary King) 사이트의 PDF <https://gking.harvard.edu/files/gking/files/0314policyforumff.pdf>로 읽었다(2026-10-08 열람). 보충 자료(SM)는 열지 않았다.

#### 사실 (원문)

- "In February 2013, Google Flu Trends (GFT) made headlines … Nature reported that GFT was predicting more than double the proportion of doctor visits for influenza-like illness (ILI) than the Centers for Disease Control and Prevention (CDC)".
- 그림 설명: "GFT overestimated the prevalence of flu in the 2012–2013 season and overshot the actual level in 2011–2012 by more than 50%. From 21 August 2011 to 1 September 2013, GFT reported overly high flu prevalence 100 out of 108 weeks."
- 오차의 모양: "These errors are not randomly distributed. For example, last week's errors predict this week's errors (temporal autocorrelation), and the direction and magnitude of error varies with the time of year (seasonality)."
- 처음 방법: "the methodology was to find the best matches among 50 million search terms to fit 1152 data points". 개발자들이 독감과 무관하지만 CDC 자료와 강하게 상관된 계절 검색어(고등학교 농구 등)를 걸러 냈다고 보고했다. 그 방식은 계절 밖의 2009년 인플루엔자 A–H1N1 대유행을 완전히 놓쳤다. 저자들의 표현으로 "part flu detector, part winter detector"였다.
- 측정 도구의 변화(algorithm dynamics): Google 검색 블로그는 2012년 6~7월에만 86개 변경을 알렸다. Google은 2011년 6월 추천 검색어, 2012년 2월 증상 검색에 대한 진단 제시를 도입했다고 알렸다. 저자들은 "Google is also changing the data-generating process"라고 썼다. 사용한 45개 검색어는 문서화된 적이 없다.
- 비교: 2010년 연구는 이미 나와 있는(보통 2주 지연) CDC 자료를 앞으로 투영한 꽤 단순한 방법보다 GFT가 별로 낫지 않음을 보였다("a fairly simple projection forward using already available (typically on a 2-week lag) CDC data"). 그림의 표본 밖 기간 평균 절대 오차(MAE)는 GFT 0.486, "Lagged CDC" 0.311, "Google Flu + CDC" 0.232다("All of these differences are statistically significant at P < 0.05"). 그림 설명에 따르면 "Lagged CDC"는 지연 CDC 자료에 52주 계절 변수를 더한 모형이고, 결합 모형은 GFT·지연 CDC·GFT의 지연 오차·52주 계절 변수를 함께 쓴다.

#### 원리 — 많은 후보에서 고른 상관, 그리고 바뀌는 측정 도구

```text
  후보 5천만 개 ──(학습 1,152점에 상관 순으로 고름)──▶ 고른 검색어 ──▶ 회귀 ──▶ 추정
        │                                              │
        └ 우연·계절만 공유한 후보가 섞임                     └ 검색 서비스가 바뀌면 같은 독감에도 검색량이 달라짐
          (다중 비교·과적합)                                  (측정 도구 변화 = 대리 지표와 목표의 관계 변화)
```

- **다중 비교·과적합**: 후보가 데이터 점보다 압도적으로 많으면, 독감과 무관하게 계절만 공유한 후보가 학습 기간에 잘 맞는다([11](../11-multiple-comparisons/2-summary.md) · [22-3](../22-multiple-and-logistic-regression/2-summary.md)). "winter detector"는 계절이 독감과 검색량을 둘 다 움직인 교란의 모양이다([12-2](../12-correlation-vs-causation/2-summary.md), 해석).
- **대리 지표의 관계 변화**: 검색량은 독감의 대리 지표다. 검색 서비스(추천 검색어 등)가 바뀌면 대리와 목표의 관계가 바뀐다([16-1](../16-metrics-design/2-summary.md)의 굿하트와 결은 다르지만 "대리가 목표에서 떨어져 나감"은 같은 모양, 해석). 입력의 의미가 조용히 바뀐 것은 [18-4](../18-data-cleaning-and-quality/2-summary.md) 스키마 드리프트와도 닮았다(해석).
- **오차의 패턴**: 오차가 자기상관·계절성을 가지면 모형이 쓸 수 있는 정보를 버린 것이다([13-3](../13-linear-regression/2-summary.md) 잔차 패턴, [23](../23-time-series-basics/2-summary.md)).
- **단순 기준선**: 늦게 오지만 정확한 원천(CDC)을 그대로 쓰는 기준선보다 나은지 확인하지 않으면 복잡한 모형의 가치를 알 수 없다(해석).

#### 실험: 계절만 따라가는 검색어가 뽑히는 모형 (`gft_overfit.py`)

합성 데이터다. 실제 GFT의 검색어·모형·수치를 재현한 것이 아니다. 주 단위 독감 수준 5시즌(시즌마다 정점 높이가 다름)을 만들고, 후보 "검색어" 5,000개 중 20개는 독감을 따라가되 잡음이 크게, 나머지 4,980개는 계절(겨울)만 따라가게 했다. 학습 3시즌(156주)에서 상관이 가장 큰 45개를 골라 평균을 단순 회귀 입력으로 썼다. 시험 1시즌에는 계절 밖(여름) 유행을, 시험 2시즌에는 모든 검색량 +40%(검색 서비스 변경 흉내)를 넣었다.

```python
scored = sorted(range(len(terms)), key=lambda j: -corr([terms[j][t] for t in TRAIN], tr_truth))
top = scored[:45]
x = [st.fmean(terms[j][t] for j in top) for t in range(T)]
slope, icpt = st.linear_regression([x[t] for t in TRAIN], tr_truth)     # statistics.linear_regression
lag2 = [truth[max(0, t - 2)] for t in range(T)]   # 2주 늦게 도착하는 공식 통계를 그대로 쓰는 기준선
```

(실험, 호스트 Python 3.12.3 표준 라이브러리(`random`·`statistics`), `random.Random(2013)`, 1회 실행, 2026-10-08)

```text
선택된 45개 중 진짜 독감 검색어: 0개 (후보 5,000개 중 20개)
학습 3시즌 적합: r = 0.960, MAE 모형 0.208 / 2주 지연 0.304
시험 1(여름 유행)      MAE 모형 0.507 / 2주 지연 0.472  평균 오차(부호) 모형 -0.447 / 2주 지연 -0.024  과대 추정 주 모형 12/52 · 2주 지연 24/52
시험 2(검색량 +40%)   MAE 모형 0.307 / 2주 지연 0.310  평균 오차(부호) 모형 +0.251 / 2주 지연 -0.000  과대 추정 주 모형 43/52 · 2주 지연 22/52
여름 정점 주: 진실 3.70, 모형 0.85, 2주 지연 3.00
```

- 관찰
  - 고른 45개에 진짜 독감 검색어는 하나도 없었다. 학습 기간에는 r = 0.960, MAE 0.208로 2주 지연 기준선(0.304)보다 나았다.
  - 시험 1: 여름 정점 주에 진실 3.70, 모형 0.85. 계절 검색어는 여름에 움직이지 않으니 계절 밖 유행을 놓쳤다("winter detector"의 모양).
  - 시험 2: MAE는 기준선과 비슷했지만(0.307 vs 0.310) 오차의 부호가 한쪽으로 쏠렸다. 모형은 52주 중 43주를 과대 추정했고 평균 오차 +0.251, 기준선은 22주·평균 오차 거의 0이다. MAE 하나만 보면 이 체계적 과대를 놓친다.
- 한계(모형): 입력 분포·파라미터는 이 노트가 정했다. 실제 GFT의 MAE(0.486)·과대 주 수(100/108)와 수치를 비교하는 실험이 아니다. "많은 후보에서 상관으로 고르면 계절 같은 공통 원인을 공유한 후보가 뽑히고, 측정 도구가 바뀌면 오차가 한쪽으로 쏠린다"는 **모양**만 보인다.

#### 막았을 장치 (해석)

- 학습에 쓰지 않은 기간으로 평가하고(시간 분할), 단순 기준선(지연 원천 자료·같은 주 작년 값)과 함께 보고한다([22-3](../22-multiple-and-logistic-regression/2-summary.md) · [22-5](../22-multiple-and-logistic-regression/2-summary.md) · [23](../23-time-series-basics/2-summary.md)).
- 오차의 부호·자기상관을 감시한다. 과대 추정이 몇 주 연속이면 재보정한다([13-3](../13-linear-regression/2-summary.md)). Lazer 외의 그림에서는 GFT·지연 CDC·GFT의 지연 오차·52주 계절 변수를 함께 넣은 결합 모형이 MAE 0.232로 가장 나았다.
- 입력 데이터를 만드는 시스템의 변경(검색 UI·추천 기능) 시점을 기록하고, 그 전후로 관계가 유지되는지 본다([24](../24-reproducible-analysis/2-summary.md) · [16](../16-metrics-design/2-summary.md)).
- 선택에 쓴 후보 수를 기록하고, 후보가 데이터 점보다 많으면 과적합을 기본 가정으로 둔다([11](../11-multiple-comparisons/2-summary.md)).
- leaf: [22-3](../22-multiple-and-logistic-regression/2-summary.md) · [22-5](../22-multiple-and-logistic-regression/2-summary.md) · [11-1](../11-multiple-comparisons/2-summary.md) · [12-2](../12-correlation-vs-causation/2-summary.md) · [13-3](../13-linear-regression/2-summary.md) · [16-1](../16-metrics-design/2-summary.md)

### 사건 3 — Reinhart–Rogoff: 수식 범위·선택적 제외·가중이 만든 −0.1% (재현 2013-04)

출처
- Thomas Herndon, Michael Ash, Robert Pollin, "Does High Public Debt Consistently Stifle Economic Growth? A Critique of Reinhart and Rogoff", PERI Working Paper 322, 2013-04-15. PERI의 원래 PDF 주소(`peri.umass.edu/fileadmin/pdf/working_papers/working_papers_301-350/WP322.pdf`)는 2026-10-08에 410(Gone)이라 Internet Archive 사본(2014-01-09 수집) <https://web.archive.org/web/20140109090443/http://www.peri.umass.edu/fileadmin/pdf/working_papers/working_papers_301-350/WP322.pdf>으로 읽었다. 아래 "HAP"는 이 논문이다.
- 원 논문 Reinhart·Rogoff "Growth in a Time of Debt"(2010a, 2010b)는 열지 않았다. RR의 수치·방법은 HAP가 옮긴 범위만 쓴다. RR 측의 반론은 이 노트에서 열람하지 않았다 `[?]`.

#### 사실 (원문)

- RR의 핵심 결과(HAP Table 1, 20개 선진국 1946–2009의 평균 실질 GDP 성장률): 부채/GDP 30% 미만 4.1, 30~60% 2.8, 60~90% 2.8, 90% 이상 **−0.1**.
- HAP 초록: "coding errors, selective exclusion of available data, and unconventional weighting of summary statistics lead to serious errors … the average real GDP growth rate for countries carrying a public-debt-to-GDP ratio of over 90 percent is actually 2.2 percent, not −0.1 percent".
- 스프레드시트 오류: "A coding error in the RR working spreadsheet entirely excludes five countries, Australia, Austria, Belgium, Canada, and Denmark, from the analysis." 각주 5: "RR averaged cells in lines 30 to 44 instead of lines 30 to 49."
- 선택적 제외: Australia(1946–1950), New Zealand(1946–1949), Canada(1946–1950)의 가용 연도를 뺐다. 뉴질랜드의 빠진 네 해는 모두 90% 이상 구간이고 성장률이 7.7, 11.9, −9.9, 10.8%였다. 남은 한 해(1951)의 성장률이 −7.6%다.
- 가중: RR은 구간 안에서 나라별 평균을 먼저 낸 뒤 **나라마다 같은 가중**으로 평균했다. 그래서 뉴질랜드의 한 해가 영국의 19년과 같은 무게를 가졌다. 옮겨 적기 오류로 뉴질랜드 값이 −7.6이 아니라 −7.9로 들어갔다.
- 규모: 90% 이상 구간의 나라-연도는 올바르게 110개다. RR은 96개를 보고했고, 스프레드시트 오류까지 겹쳐 실제로는 71개로 계산했다. 결과에 들어간 나라는 7개다.
- HAP Table 3(90% 이상 구간): 올바른 계산 2.2, 스프레드시트 오류만 1.9, 연도 제외만 1.9, 나라 가중만 1.9, 연도 제외 + 나라 가중 0.3, 세 가지 모두 0.0, 옮겨 적기 오류까지 −0.1.
- 그 밖에: 90%라는 경계에서 비선형이 보이지 않았다. 비선형은 0~30%와 30~60% 사이에 있었다. 부채/GDP 38%~117% 사이에서는 평균 성장률 3%라는 귀무가설을 기각하지 못했다. HAP는 "we follow RR in assuming that causation runs from public debt to GDP growth"라고 인과 방향을 RR의 가정으로 따른다고 밝혔다.
- 재현 경로: "We were unable to replicate the RR results from the publicly available country spreadsheet data". RR이 작업 스프레드시트를 제공한 뒤에야 오류를 찾았다.

#### 원리 — 평균 하나에 겹친 세 가지

```text
  나라-연도 110행 ──┬─ (1) 수식 범위 30~44행 (20행 중 15행) ──▶ 다섯 나라가 통째로 빠짐       = 조용한 절단
                   ├─ (2) 가용 연도 제외 (14개 나라-연도) ──────▶ 뉴질랜드가 −7.6% 한 해만 남음   = 선택적 제외
                   └─ (3) 나라 평균의 평균 ─────────────────────▶ 한 해짜리 나라도 1/7 무게      = 가중 정의
                                                                     │
                                                       각각은 −0.3%p 안팎, 겹치면 2.2 → −0.1
```

- (1)은 [18-3](../18-data-cleaning-and-quality/2-summary.md)의 조용한 절단과 같은 모양이다. 수식은 오류 없이 평균을 냈고, 범위가 데이터보다 짧다는 신호는 행 수를 세야 보인다(해석).
- (3)은 [16-3](../16-metrics-design/2-summary.md)의 "합÷합 vs 평균의 평균"과 같은 질문이다. 나라-연도 가중(합÷합)과 나라 동일 가중(평균의 평균)은 둘 다 계산은 맞다. 무엇을 한 단위로 볼지의 정의가 다르고, 그 정의를 밝히지 않았다(HAP: "RR does not indicate or discuss the decision").
- (2)와 (3)이 겹치면 한 점이 평균을 끈다. 관측이 하나뿐인 나라의 극단값이 1/7 무게를 가졌다. [12-4](../12-correlation-vs-causation/2-summary.md)(이상값 하나가 만든 상관)·[13-2](../13-linear-regression/2-summary.md)(레버리지)와 같은 "한 점의 과대 영향"이다(해석).
- 구간으로 묶은 평균(0~30·30~60·60~90·90 이상)은 관계의 모양을 숨긴다. HAP는 산점도와 평활 곡선으로 90% 경계에 꺾임이 없음을 보였다([06-1](../06-exploratory-data-analysis/2-summary.md), 해석).
- 공개 데이터만으로 재현되지 않았고 작업 파일을 받은 뒤에야 오류가 보였다. 분석 산출물에 데이터·코드·수식이 함께 남아야 남이 확인할 수 있다([24](../24-reproducible-analysis/2-summary.md)).

#### 실험: HAP Table 2의 공개 수치로 평균을 다시 낸다 (`rr_table2.py`)

HAP Table 2는 90% 이상 구간의 나라별 연수와 평균 성장률(소수 첫째 자리 반올림)을 싣는다. 그 표만으로 각 오류의 효과를 다시 계산했다. 나라별 값이 반올림 값이라 Table 3과 0.1 안팎 차이가 날 수 있다.

```python
T2 = [  # (나라, 연수 Correct, RR 연도 제외 후 연수, 성장률 Correct, RR 표의 값) — HAP Table 2
    ("Australia", 5, 0, 3.8, None), ("Belgium", 25, 25, 2.6, None), ("Canada", 5, 0, 3.0, None),
    ("Greece", 19, 19, 2.9, 2.9), ("Ireland", 7, 7, 2.4, 2.4), ("Italy", 10, 10, 1.0, 1.0),
    ("Japan", 11, 11, 0.7, 0.7), ("New Zealand", 5, 1, 2.6, -7.9), ("UK", 19, 19, 2.4, 2.4), ("US", 4, 4, -2.0, -2.0)]
SHEET_ERR = {"Australia", "Austria", "Belgium", "Canada", "Denmark"}
country_year_mean = Σ(연수 × 성장률) / Σ연수          # 나라-연도 가중
country_mean      = Σ 나라 평균 / 나라 수              # 나라 동일 가중
```

(실험, 호스트 Python 3.12.3, 결정적 계산, 2026-10-08)

```text
(1) 올바른 계산: 나라-연도 가중, 10개국 110개 나라-연도          =  2.17  (HAP Table 3: 2.2)
(2) 나라 동일 가중만 바꿈(10개국)                           =  1.94  (Table 3 'Country weights only': 1.9)
(3) 스프레드시트 범위 오류만(나라-연도 가중, 7개국 75행)        =  1.87  (Table 3 'Spreadsheet error only': 1.9)
(4) 범위 오류 + 연도 제외 + 나라 동일 가중 + 옮겨 적기 오류(7개국) = -0.07  (RR 발표: -0.1)
    RR 7개국 값: [2.9, 2.4, 1.0, 0.7, -7.9, 2.4, -2.0] 합 -0.5
(5) 뉴질랜드의 가중치(HAP Table 2 Weights 열): RR 나라 동일 가중 14.3%(1951년 한 해, -7.9) vs 나라-연도 가중 4.5%(5개 연도 전체, 5/110) — 1951년 한 해는 0.9%(1/110)
```

- 관찰
  - 공개된 표 하나로 2.2와 −0.1을 둘 다 다시 만들 수 있었다(2.17, −0.07 — 반올림 차이 안).
  - 오류 하나씩은 2.2를 1.9 근처로만 내린다. 여럿이 겹치자 부호가 바뀌었다. 7개국 값의 합이 −0.5라 평균 −0.07이 됐고, 그중 뉴질랜드 −7.9 하나가 합을 크게 끌어내렸다.
  - (3)의 75행은 Table 2의 "RR Spreadsheet error" 열 합계다. 연도 제외까지 겹치면 뉴질랜드가 5행에서 1행이 되어 71행이다(HAP 본문의 "only 71 country-years").

#### 막았을 장치 (해석)

- 행 수 대조: 수식이 실제로 덮는 행 수(`COUNT(L30:L44)` = 15)와 기대 나라 수(20)를 나란히 둔다. 리포트 옆 원천 대조와 같은 장치다([18-3](../18-data-cleaning-and-quality/2-summary.md) · [27](../27-da-symptom-index/2-summary.md) 2절).
- 가중 정의 명시: "나라 평균의 평균"인지 "나라-연도 평균"인지 표 머리에 적고 둘 다 보인다([16-3](../16-metrics-design/2-summary.md)).
- 민감도 표: 제외·가중을 바꿔 가며 결론이 유지되는지 본다. HAP Table 3이 바로 그 표다. 결론이 한 해·한 나라에 달려 있으면 그것이 결과다([11-2](../11-multiple-comparisons/2-summary.md)의 "고른 칸" 문제와 같은 방향, 해석).
- 모양 보기: 구간 평균 전에 산점도([06](../06-exploratory-data-analysis/2-summary.md)).
- 재현 자료 공개: 데이터·수식·코드를 함께 남긴다([24](../24-reproducible-analysis/2-summary.md)).
- leaf: [18-3](../18-data-cleaning-and-quality/2-summary.md) · [16-3](../16-metrics-design/2-summary.md) · [06-1](../06-exploratory-data-analysis/2-summary.md) · [24-1](../24-reproducible-analysis/2-summary.md) · [24-4](../24-reproducible-analysis/2-summary.md) · [03](../03-observational-vs-experimental/2-summary.md)(인과 방향은 관찰 데이터의 가정)

### 사건 4 — 영국 PHE: 15,841건이 보고에서 빠지고 몰려 들어옴 — 분석 관점 (발견 2020-10-02 밤 · 발표 2020-10-04)

출처
- Public Health England, "PHE statement on delayed reporting of COVID-19 cases", GOV.UK, 2020-10-04 게시·10-05 갱신("Added background information") <https://www.gov.uk/government/news/phe-statement-on-delayed-reporting-of-covid-19-cases>(2026-10-08 열람). [data-engineering/17](../../data-engineering/17-de-incidents/2-summary.md) 사건 1과 같은 원문이다. 파일 형식(XLS)·의회 답변은 그 노트가 정리했다.

#### 사실 (원문)

- "A technical issue was identified overnight on Friday 2 October in the data load process that transfers COVID-19 positive lab results into reporting dashboards. After rapid investigation, we have identified that 15,841 cases between 25 September and 2 October were not included in the reported daily COVID-19 cases. The majority of these cases occurred in most recent days."
- "Of these, over 75% (11,968) relate to cases that should have been reported between 30 September and 2 October."
- 원인(배경 정보 절): "some files containing positive test results exceeded the maximum file size that takes these data files and loads then into central systems."
- "The increase in cases are spread proportionally across the country as per the current levels of the virus."
- "The dashboard on GOV.UK has now been updated and the correct number of cases by specimen date is shown in the cases section. Today and yesterday's headline number are large due to the backlog of cases flowing through the total reporting process."
- 날짜별 표(원문 그대로)

```text
  Date (recorded – flow though into     Expected reported date     Cases that were not included
  following day's published numbers)    for GOV.UK                 on the expected data
  24/09/2020                            25/09/2020                    957
  25/09/2020                            26/09/2020                    744
  26/09/2020                            27/09/2020                    757
  27/09/2020                            28/09/2020                      0
  28/09/2020                            29/09/2020                  1,415
  29/09/2020                            30/09/2020                  3,049
  30/09/2020                            01/10/2020                  4,133
  01/10/2020                            02/10/2020                  4,786
```

- 계산: 여덟 칸의 합 15,841. 마지막 세 칸의 합 11,968(15,841의 75.6%). 처음 네 칸의 합 2,458.

#### 원리 — 분석가가 본 숫자: 최근이 덜 차고, 뒤늦게 한꺼번에

```text
  보고일 기준 일일 확진 (머리 숫자) — 해석: 모양만 그린 그림, 실제 일일 숫자가 아니다
     │                     빠진 건이 최근 날짜에 몰림(마지막 3일에 11,968)
     │      ┌────┐   ┌────┐
     │ ┌────┤    ├───┤    │  ← 실제로는 더 가파르게 오르던 구간이 평평해 보임
     │ │    │    │   │    │                    ┌──────────┐
     │ │    │    │   │    │                    │ 밀린 건 유입 │ ← "Today and yesterday's headline number are large"
     └─┴────┴────┴───┴────┴────────────────────┴──────────┴──▶ 보고일
       9/25                10/2                 10/3~10/4
```

- **추세가 덜 가파르게 보였다**: 빠진 건이 최근 날짜에 몰렸다(처음 네 칸 2,458 → 마지막 세 칸 11,968). 보고일 기준 일일 숫자로 주간 증가율을 보던 분석은 그 기간의 증가를 실제보다 작게 봤을 것이다(해석 — PHE 발표문은 보고된 일일 총계를 같이 싣지 않아 증가율을 다시 계산하지 않았다).
  - 같은 모양: 관측 끝 근처 칸이 덜 찬 코호트 표([17-3](../17-sql-for-analysis/2-summary.md)). 최근 숫자가 작은 것이 실제 감소인지 "아직 안 들어온 것"인지 구분해야 한다.
- **복구 때 머리 숫자가 튀었다**: 밀린 건이 한꺼번에 보고일로 들어오면 보고일 시계열에 급등이 생긴다. 검체 날짜(이벤트 시각)로 다시 붙이면 지난 며칠이 조금씩 늘어난다. 이 급등을 기준선 학습에 넣으면 다음 이상 탐지가 둔해진다([23-4](../23-time-series-basics/2-summary.md), 해석).
- **수준은 틀리고 구성은 덜 틀렸다**: 발표문은 빠진 건이 지역에 비례해 퍼져 있었다고 적었다. 그렇다면 지역 간 비율 비교는 덜 흔들리고 전국 총량(수준)이 틀렸다는 뜻이다(해석). 판단이 상대 비교에 기댔는지 절대 수준에 기댔는지에 따라 영향이 다르다.
- **조용한 절단**: 한도를 넘은 파일에서 결과가 빠졌다. 적재 과정이 실패로 표시됐는지는 공개 자료에 없다. 빠진 건수 자체는 원천 건수와 대조해야 보이는 모양이다([18-3](../18-data-cleaning-and-quality/2-summary.md)). 파이프라인 쪽 모형 실험(XLS 행 한도 · `xls_cap.py`)은 [data-engineering/17](../../data-engineering/17-de-incidents/2-summary.md) 사건 1에 있다.

#### 막았을 장치 (해석)

- 원천 대조: 검사 기관이 센 양성 건수와 집계된 건수를 날마다 맞춘다([18-3](../18-data-cleaning-and-quality/2-summary.md) · [27](../27-da-symptom-index/2-summary.md) 2절).
- 날짜 축 명시: 보고일·검체 날짜를 둘 다 두고, 분석·추세 판단은 검체 날짜로 한다. 최근 며칠은 "아직 덜 찼음"으로 표시한다([17-3](../17-sql-for-analysis/2-summary.md) · [27](../27-da-symptom-index/2-summary.md) 6절).
- 복구 표시: 밀린 건이 들어온 날은 대시보드에 주석을 달고, 기준선 학습에서 뺀다([23-4](../23-time-series-basics/2-summary.md)).
- leaf: [18-3](../18-data-cleaning-and-quality/2-summary.md) · [17-3](../17-sql-for-analysis/2-summary.md) · [23-4](../23-time-series-basics/2-summary.md) · [06-5](../06-exploratory-data-analysis/2-summary.md)(요약만 보면 지나치는 이상)

### 네 사건을 나란히 (해석)

| 사건 | 깨진 원리 | 틀린 숫자 | 무엇과 대조해 드러났나 | 막았을 장치 | leaf |
|---|---|---|---|---|---|
| Literary Digest 1936 | 표집 틀·무응답 편향 — n은 편향을 줄이지 않음 | 승자 예측이 반대(2차 출처: Landon 57.08% 예측, Roosevelt 60.8% 득표 `[?]`). 선거인단 523 : 8 | 실제 선거 결과, 1937 Gallup 조사(Squire) | 확률 표집, 응답자 구성 점검, 외부 기준 대조 | [02-1](../02-sampling-and-bias/2-summary.md) · [08-4](../08-confidence-intervals/2-summary.md) |
| Google Flu Trends | 다중 비교·과적합, 계절 교란, 측정 도구 변화 | 2011-08 ~ 2013-09에 108주 중 100주 과대, 2013-02 Nature 보도로 CDC 추정의 두 배 넘게 | CDC 감시 통계, 지연 CDC 기준선 | 시간 분할 평가, 단순 기준선, 오차 부호·자기상관 감시, 입력 변경 기록 | [22-3](../22-multiple-and-logistic-regression/2-summary.md) · [11-1](../11-multiple-comparisons/2-summary.md) · [13-3](../13-linear-regression/2-summary.md) |
| Reinhart–Rogoff | 수식 범위 누락, 선택적 제외, 가중 정의 | 90% 이상 구간 평균 2.2%가 −0.1%로 | 작업 스프레드시트로 다시 계산(HAP) | 행 수 대조, 가중 명시, 민감도 표, 재현 자료 | [18-3](../18-data-cleaning-and-quality/2-summary.md) · [16-3](../16-metrics-design/2-summary.md) · [24-4](../24-reproducible-analysis/2-summary.md) |
| PHE 2020-10 | 조용한 절단, 날짜 축(보고일 vs 검체 날짜) | 15,841건 누락, 그중 11,968건이 마지막 3일 | 발견 경위는 발표문에 없음("identified overnight") | 원천 대조, 날짜 축 명시, 복구일 표시 | [18-3](../18-data-cleaning-and-quality/2-summary.md) · [17-3](../17-sql-for-analysis/2-summary.md) · [23-4](../23-time-series-basics/2-summary.md) |

- 공통점: 네 사건 모두 공개 자료가 적는 문제는 틀리거나 빠진 숫자다. 앞의 세 사건은 숫자를 **다른 출처나 다른 계산과 대조**했을 때 드러났고, PHE도 원천 대조가 막았을 장치다(해석).
- 차이: Literary Digest는 **누구를 쟀나**(표본), GFT는 **무엇으로 쟀나**(대리 지표와 모형), Reinhart–Rogoff는 **어떻게 합쳤나**(범위·가중), PHE는 **언제로 셌나**(누락과 날짜 축)가 틀렸다. 장치도 서로 다른 축에 있다.

## 쓰이는 자료구조·알고리즘

- **확률 표집**: 모든 단위가 알려진 확률로 뽑히게 하는 무작위 추출(`random.sample`) — 사건 1([02](../02-sampling-and-bias/2-summary.md) · [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md)).
- **상관 순 상위 k 선택**: 후보를 점수로 정렬해 앞 k개를 고른다. 후보가 많을수록 우연히 높은 점수가 뽑힌다 — 사건 2([11](../11-multiple-comparisons/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)).
- **최소제곱 단순 회귀**: `statistics.linear_regression` — 사건 2 실험([13](../13-linear-regression/2-summary.md)).
- **가중 평균**: 나라-연도 가중 vs 나라 동일 가중 — 사건 3([16](../16-metrics-design/2-summary.md)).
- **지연 기준선·이동 평균**: 늦게 오지만 정확한 원천을 그대로 쓰는 예측 — 사건 2·4([23](../23-time-series-basics/2-summary.md)).
- **행 수·합계 대조(control total)**: 사건 3·4([18](../18-data-cleaning-and-quality/2-summary.md) · [data-engineering/10](../../data-engineering/10-data-quality-and-data-observability/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 내 분석으로 옮길 점검 목록

```text
  □ 응답·표본이 누구인지 확인했나? 응답률과 응답자 구성을 알려진 모집단 값과 비교했나?            (Digest · 02)
  □ 표본이 크다는 이유로 좁은 구간을 정확성으로 읽지 않았나? 편향은 구간에 안 나온다.              (Digest · 08-4)
  □ 모형을 학습에 쓰지 않은 기간으로 평가했나? 단순 기준선(지연 원천·작년 같은 주)과 비교했나?       (GFT · 22-3 · 23)
  □ 후보 변수·검색어·세그먼트를 몇 개 보고 골랐나? 그 수를 기록했나?                          (GFT · 11)
  □ 입력을 만드는 시스템(UI·로깅·수집기)이 바뀐 날을 기록하고, 그 전후로 오차를 나눠 봤나?           (GFT · 24)
  □ 수식·쿼리가 덮는 행 수를 기대 행 수와 나란히 뒀나?                                       (RR · 18-3)
  □ 평균의 가중(무엇을 한 단위로 보나)을 표 머리에 적었나? 다른 가중으로도 결론이 같은가?            (RR · 16-3)
  □ 제외한 데이터와 그 이유를 적고, 넣었을 때의 결과도 보였나?                                (RR · 11-2)
  □ 데이터·수식·코드를 남이 다시 돌릴 수 있게 남겼나?                                        (RR · 24)
  □ 날짜를 어느 축(사건 발생·처리·보고)으로 잘랐나? 최근 며칠이 아직 덜 찼는지 표시했나?          (PHE · 17-3)
  □ 원천 건수와 집계 건수를 날마다 맞추나? 밀린 건이 들어온 날을 표시하고 기준선에서 뺐나?          (PHE · 18-3 · 23-4)
```

### 2. 분석 결과를 넘기기 전 5분 점검 (네 사건에서 뽑은 질문)

| 질문 | 예라면 | 사건 |
|---|---|---|
| 이 숫자를 독립된 다른 출처와 비교해 봤나? | 차이가 설명되면 통과 | 넷 다 |
| 결론이 한 해·한 나라·한 세그먼트를 빼면 바뀌나? | 그것을 결과에 적는다 | Reinhart–Rogoff |
| 학습·선택에 쓴 데이터로 성능을 보고하고 있나? | 시간 분할로 다시 잰다 | GFT |
| 응답하지 않은 사람·빠진 행이 결과와 관련 있을 수 있나? | 응답자 기준임을 명시, 가중·대조 | Literary Digest · PHE |
| 최근 날짜의 숫자가 아직 덜 찼을 수 있나? | 미완 표시, 이벤트 날짜로 다시 집계 | PHE |

### 3. 틀린 숫자가 나간 뒤의 정정 순서 (네 사건의 공통 — 해석)

```text
  1. 무엇이 틀렸나를 한 문장으로      "90% 이상 구간 평균이 −0.1이 아니라 2.2" — 범위·가중 같은 원인과 함께
  2. 올바른 계산을 다시 낸다           원 데이터·작업 파일로 (HAP는 작업 스프레드시트를 받아서야 가능했다)
  3. 원인별 효과를 나눠 보인다          HAP Table 3처럼 오류 하나씩, 그리고 겹쳤을 때
  4. 그 숫자를 쓴 판단을 찾는다         정책 문서·대시보드·후속 분석 (HAP는 인용처를 찾아 적었다)
  5. 재발 방지 장치를 남긴다           행 수 대조·가중 명시·시간 분할 평가·날짜 축 표시
```

## 장애 시나리오와 대처

### 1. "응답이 많으니 정확하다" — Literary Digest형

- **현상**: 앱 내 설문 응답 5만 건으로 "기능 만족도 4.5/5"를 보고하고 유료화를 결정했다. 유료 전환율이 예측의 절반에도 못 미친다.
- **보이는 형태**: 보고서의 95% 구간이 ±0.01 수준으로 좁다. 응답자의 최근 30일 사용 시간이 전체 사용자의 몇 배다(예시).
- **원인**: 기능을 즐겨 쓰는 사람이 더 잘 응답했다. 구간은 표집 오차만 반영하고 편향은 n으로 줄지 않는다([02-1](../02-sampling-and-bias/2-summary.md) · [08-4](../08-confidence-intervals/2-summary.md)).
- **대처**: 응답자와 비응답자를 로그로 비교한다. 결과에 "응답자 기준"을 적는다. 결정에 쓸 숫자는 무작위로 고른 소수에게 묻거나 행동 로그로 잰다.

### 2. 학습 기간에만 맞는 모형을 운영한다 — GFT형

- **현상**: 검색·클릭 지표로 다음 주 수요를 예측하는 모형이 출시 후 몇 주 연속 높게 예측한다. 재고가 쌓인다.
- **보이는 형태**: 학습 기간 R²는 높았다. 운영 오차의 부호가 몇 주째 같은 쪽이고, 앱 검색 UI 개편 날짜와 오차가 커진 날짜가 겹친다.
- **원인**: 수많은 후보 지표 중 학습 기간에 상관이 높은 것을 골랐다(과적합). 입력을 만드는 UI가 바뀌어 지표와 수요의 관계가 바뀌었다([22-3](../22-multiple-and-logistic-regression/2-summary.md) · [16-1](../16-metrics-design/2-summary.md)).
- **대처**: 시간 분할로 평가하고, "지난주 실제 값" 같은 단순 기준선과 함께 보고한다. 오차 부호가 연속되면 재보정 경보를 낸다. 입력 시스템 변경 일지를 모형 감시에 붙인다.

### 3. 수식 범위·가중이 조용히 틀린다 — Reinhart–Rogoff형

- **현상**: 분기 보고서의 "지역 평균 성장률"이 경영 회의의 근거가 됐다. 다른 팀이 원자료로 다시 계산하니 부호가 다르다.
- **보이는 형태**: 스프레드시트의 평균 수식이 데이터 마지막 몇 행을 덮지 않는다. 지역 평균의 평균(지역 동일 가중)으로 계산돼, 매장이 하나뿐인 지역의 극단값이 큰 무게를 가졌다.
- **원인**: 수식이 덮는 행 수를 아무도 세지 않았다. 가중 정의가 문서에 없었다([18-3](../18-data-cleaning-and-quality/2-summary.md) · [16-3](../16-metrics-design/2-summary.md)).
- **대처**: 수식 옆에 `COUNT`(덮는 행 수)와 기대 행 수를 둔다. 가중 정의를 표 머리에 적고 두 가중을 함께 보인다. 계산을 스프레드시트 밖 코드로 옮겨 재실행할 수 있게 한다([24](../24-reproducible-analysis/2-summary.md)).

### 4. 보고일 기준 숫자로 추세를 판단한다 — PHE형

- **현상**: 일일 가입자 대시보드가 이번 주 평평해 "성장 둔화"로 보고됐다. 다음 주 월요일 가입자가 평소의 세 배로 뛴다.
- **보이는 형태**: 처리 날짜 기준 숫자다. 이벤트 날짜로 다시 집계하면 지난주가 꾸준히 늘었다. 수집 파일 몇 개가 한도에 걸려 늦게 처리됐다(예시).
- **원인**: 누락이 최근 날짜에 몰렸고, 복구분이 처리 날짜 하루로 들어왔다. 분석은 날짜 축을 확인하지 않았다([17-3](../17-sql-for-analysis/2-summary.md) · [18-3](../18-data-cleaning-and-quality/2-summary.md)).
- **대처**: 추세 판단은 이벤트 날짜로 한다. 최근 며칠은 미완으로 표시한다. 원천 건수와 날마다 대조하고, 복구분이 들어온 날은 주석을 달고 기준선 학습에서 뺀다([23-4](../23-time-series-basics/2-summary.md)).

### 5. 남이 재현하려 할 때 재료가 없다

- **현상**: 외부 감사가 작년 보고서의 핵심 수치를 다시 계산하려 한다. 공개 데이터로는 같은 숫자가 나오지 않는다.
- **보이는 형태**: 작업 파일이 개인 노트북에만 있고, 어떤 행을 제외했는지 기록이 없다.
- **원인**: 원본 보존·단계 기록·코드 공유를 하지 않았다. HAP도 공개 데이터만으로는 RR 결과를 재현하지 못했다([24-4](../24-reproducible-analysis/2-summary.md) · [24-1](../24-reproducible-analysis/2-summary.md)).
- **대처**: 원본은 읽기 전용으로 두고 정제·제외 규칙은 코드로 남긴다. 보고서마다 데이터 버전·코드 버전·제외 목록을 함께 저장한다.

## 핵심 문장

- 네 사건 모두 숫자는 나왔는데 판단이 틀렸다. Literary Digest·GFT·Reinhart–Rogoff는 다른 출처나 다른 계산과 대조했을 때 드러났다. PHE의 발견 경위는 발표문에 없다.
- Literary Digest: 응답이 수백만이어도 누가 응답했는지가 편향을 정한다. Squire는 표본과 응답이 둘 다 편향돼 함께 틀린 추정을 만들었다고 결론 냈다.
- Google Flu Trends: 5천만 개 후보에서 1,152개 점에 맞춘 처음 판은 계절을 독감으로 착각했다("winter detector"). 2009년 갱신판은 검색 서비스가 바뀌는 동안 2011-08 ~ 2013-09에 108주 중 100주를 과대 추정했고, 지연 CDC 자료(+52주 계절 변수) 모형이 더 나았다.
- Reinhart–Rogoff: 수식 범위 누락·선택적 제외·나라 동일 가중이 겹쳐 90% 이상 구간의 평균 성장률 2.2%가 −0.1%가 됐다. 하나씩은 0.3%p 안팎이었다.
- PHE: 파일 크기 한도로 15,841건이 빠졌고 그중 11,968건이 마지막 3일분이었다. 보고일 기준 숫자는 최근 추세를 덜 가파르게, 복구일을 급등으로 보이게 한다. 이 노트는 분석 관점, 파이프라인 관점은 data-engineering/17이다.

## 관련 주제·근거

- 선행: [27](../27-da-symptom-index/2-summary.md)(증상 → leaf 역색인)
- 이 노트가 가리키는 leaf: [02](../02-sampling-and-bias/2-summary.md) · [06](../06-exploratory-data-analysis/2-summary.md) · [08](../08-confidence-intervals/2-summary.md) · [11](../11-multiple-comparisons/2-summary.md) · [12](../12-correlation-vs-causation/2-summary.md) · [13](../13-linear-regression/2-summary.md) · [16](../16-metrics-design/2-summary.md) · [17](../17-sql-for-analysis/2-summary.md) · [18](../18-data-cleaning-and-quality/2-summary.md) · [22](../22-multiple-and-logistic-regression/2-summary.md) · [23](../23-time-series-basics/2-summary.md) · [24](../24-reproducible-analysis/2-summary.md)
- 다른 영역 사건 노트: [data-engineering/17-de-incidents](../../data-engineering/17-de-incidents/2-summary.md)(PHE 파이프라인 관점·XLS 행 한도 실험) · [math/17-math-incidents](../../math/17-math-incidents/2-summary.md) · [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md)
- 1차 출처
  - Squire, P. "Why the 1936 Literary Digest Poll Failed", *Public Opinion Quarterly* 52(1), 1988, DOI 10.1086/269085 — 초록만(OpenAlex 메타데이터, 2026-10-08). 본문 미열람
  - National Archives, "1936 Electoral College Results" <https://www.archives.gov/electoral-college/1936>
  - Lazer, D., Kennedy, R., King, G., Vespignani, A. "The Parable of Google Flu: Traps in Big Data Analysis", *Science* 343(6176):1203–1205, 2014, DOI 10.1126/science.1248506 — 저자 사본 <https://gking.harvard.edu/files/gking/files/0314policyforumff.pdf>
  - Herndon, T., Ash, M., Pollin, R. "Does High Public Debt Consistently Stifle Economic Growth? A Critique of Reinhart and Rogoff", PERI Working Paper 322, 2013-04-15 — Internet Archive 사본 <https://web.archive.org/web/20140109090443/http://www.peri.umass.edu/fileadmin/pdf/working_papers/working_papers_301-350/WP322.pdf>
  - Public Health England, "PHE statement on delayed reporting of COVID-19 cases", GOV.UK 2020-10-04(10-05 갱신) <https://www.gov.uk/government/news/phe-statement-on-delayed-reporting-of-covid-19-cases>
- 2차 출처: Wikipedia "The Literary Digest"(2026-05-30 판) — 1936 여론조사의 발송 수·응답 수·예측 득표율·실제 득표율·Gallup 예측(Freedman 외 2007 pp. 335–336 인용). 원문 미확인 `[?]`
- 실험 목록
  - `digest_sim.py` — 호스트 Python 3.12.3 표준 라이브러리, `random.Random(1936)`, 합성 모집단 100만 명: 틀 편향만 / 틀 + 무응답 / 단순 무작위 3,000의 추정과 구간
  - `gft_overfit.py` — 호스트 Python 3.12.3 표준 라이브러리, `random.Random(2013)`, 합성 5시즌 × 후보 5,000개: 상관 상위 45개 선택 회귀 vs 2주 지연 기준선, 계절 밖 유행·검색량 +40%
  - `rr_table2.py` — 호스트 Python 3.12.3, HAP Table 2 공개 수치로 나라-연도 가중·나라 동일 가중·범위 오류·연도 제외 조합의 평균 재계산(결정적)
