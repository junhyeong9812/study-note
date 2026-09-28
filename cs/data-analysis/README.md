# 데이터 분석·통계 — `cs/data-analysis/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §18에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 28 · 원고 있음 0 · 초안(Claude) 0 · 검수 완료 0

> 데이터가 어디서 왔나 → 요약 → 추론 → 관계·모델 → 실험 → 실무(SQL·정제·시각화). 확률·분포 기초는 **math/07~09이 단일 출처**(여기서 반복하지 않음).
> 뼈대: OpenIntro Statistics 4판(장·절 확인), Kohavi·Tang·Xu 『Trustworthy Online Controlled Experiments』(2020, 장 번호 `[?]`), Wilke 『Fundamentals of Data Visualization』, Downey 『Think Stats』 2판, Tukey 『Exploratory Data Analysis』.

## 18.1 데이터와 수집

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `data-types-and-measurement` | 변수 유형(명목·순서·수치), 측정 척도 | 필수 | 미작성 | — |
| 02 | `sampling-and-bias` | 모집단·표본·표본 추출·편향 | 필수 | 미작성 | — |
| 03 | `observational-vs-experimental` | 관찰 연구 vs 실험, 교란 변수 | 필수 | 미작성 | — |

## 18.2 기술통계

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `descriptive-statistics` | 중심(평균·중앙값)·산포(분산·IQR)·분위수·이상치 | 필수 | 미작성 | — |
| 05 | `percentiles-and-latency-distributions` | 백분위 계산·병합·히스토그램, 긴 꼬리 | 필수 | 미작성 | — |
| 06 | `exploratory-data-analysis` | EDA — 분포·관계 먼저 보기 | 권장 | 미작성 | — |

## 18.3 추론 (확률 기초는 math/07~09)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 07 | `sampling-distributions-and-clt` | 표본 분포·표준오차·중심극한정리 | 필수 | 미작성 | — |
| 08 | `confidence-intervals` | 신뢰구간 해석과 계산 | 필수 | 미작성 | — |
| 09 | `hypothesis-testing` | 귀무·대립·p-value·1종/2종 오류 | 필수 | 미작성 | — |
| 10 | `power-and-sample-size` | 검정력·최소 탐지 효과·표본 크기 | 권장 | 미작성 | — |
| 11 | `multiple-comparisons` | 다중 비교·p-hacking·보정 | 필수 | 미작성 | — |
| 20 | `categorical-inference` | 비율 추론·카이제곱 적합도·독립성 | 권장 | 미작성 | — |
| 21 | `numerical-inference-t-anova` | t 분포·대응 표본·두 평균 차·ANOVA | 권장 | 미작성 | — |

## 18.4 관계·모델

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 12 | `correlation-vs-causation` | 상관·교란·**심슨의 역설** | 필수 | 미작성 | — |
| 13 | `linear-regression` | 최소제곱·잔차·결정계수·회귀 추론 | 필수 | 미작성 | — |
| 22 | `multiple-and-logistic-regression` | 다중 회귀·모델 선택·로지스틱 회귀 | 권장 | 미작성 | — |
| 25 | `causal-inference-basics` | 인과 DAG·교란 통제·차분의 차분·도구 변수 | 심화 | 미작성 | — |
| 26 | `bayesian-thinking` | 사전·사후·베이즈 갱신 | 심화 | 미작성 | — |

## 18.5 실험

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 14 | `ab-testing-design` | 무작위 배정·단위·지표·기간 | 필수 | 미작성 | — |
| 15 | `ab-pitfalls-srm-peeking` | **SRM**(표본 비율 불일치)·엿보기·간섭 | 필수 | 미작성 | — |
| 16 | `metrics-design` | 목표·가드레일·대리 지표 | 권장 | 미작성 | — |

## 18.6 실무

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 17 | `sql-for-analysis` | 코호트·퍼널·리텐션·세션화 SQL | 필수 | 미작성 | — |
| 18 | `data-cleaning-and-quality` | 결측·중복·이상치·타임존·스키마 드리프트 | 필수 | 미작성 | — |
| 19 | `data-visualization-principles` | 인코딩 선택·비례 잉크·축·색 | 필수 | 미작성 | — |
| 23 | `time-series-basics` | 추세·계절성·이동평균·이상 탐지 | 권장 | 미작성 | — |
| 24 | `reproducible-analysis` | 노트북 재현성·파이프라인·버전 | 권장 | 미작성 | — |

## 18.7 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 27 | `da-symptom-index` | 역색인: 실험 비율 틀어짐(SRM), 합계가 안 맞음, 너무 좋은 결과, 부분군 반전, 날짜 경계 어긋남, 백분위 병합 오류 | 필수 | 미작성 | — |
| 28 | `da-incidents` | 실사건: Literary Digest 표본 편향(1936) · Google Flu Trends 과대 추정(2013) · Reinhart–Rogoff 엑셀 범위 오류(2013) · 영국 COVID 확진 약 16,000건 누락 — 구형 XLS 행 제한(2020) | 권장 | 미작성 | — |
