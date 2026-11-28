# python/python-data-science/01 — SciPy 통계 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 원본 예제의 카이제곱 구획이 화면에 찍는 것 (예측)

```python
# 질문용 발췌 — 원본 예제 「카이제곱 검정」 구획의 일부 (… 는 생략한 줄)
print("""
…
chi2, p_value, dof, expected = stats.chi2_contingency(observed)
…
print(f"자유도: {dof}")
print(f"기대빈도:\n{expected}")
…
""")
```

- 이 구획을 실행하면 화면에 자유도 숫자가 찍히나, 코드 글자가 찍히나?
- `\n` 이 들어 있는 마지막 줄은 화면에 어떤 꼴로 나오나?

### 2. 남녀 × 찬반 교차표의 기대빈도와 자유도 (예측)

```python
# 질문용 발췌
observed = np.array([
    [50, 30],   # 남성: 찬성 50, 반대 30
    [35, 45]    # 여성: 찬성 35, 반대 45
])
chi2, p_value, dof, expected = stats.chi2_contingency(observed)
```

- 이 코드를 실제로 돌리면 `expected` 의 네 칸과 `dof` 는 각각 얼마가 되나?

### 3. `ppf` 에 `cdf` 의 결과를 다시 넣으면 (예측)

- `norm = stats.norm(loc=0, scale=1)` 일 때 `norm.ppf(norm.cdf(1.96))` 는 대략 얼마인가?

### 4. p값이 유의수준보다 작을 때 귀무가설을 기각하는 까닭 (왜)

- p값이 작다는 것이 왜 귀무가설을 버릴 근거가 되나?

### 5. 같은 다섯 사람의 전후 점수에 `ttest_rel` 을 쓰는 까닭 (왜)

- `before` · `after` 를 `ttest_ind` 가 아니라 `ttest_rel` 로 검정하는 이유는 무엇인가?

### 6. 이산분포에는 `pmf`, 연속분포에는 `pdf` 를 쓰는 까닭 (왜)

- 이항 · 포아송에는 `.pmf` 를, 정규 · t 에는 `.pdf` 를 부르는 이유는 무엇인가?

### 7. p값이 0.05 이상일 때 말할 수 있는 범위 (경계)

- `ttest_ind` 의 p값이 0.3 이면 「두 집단의 평균은 같다」고 결론 내려도 되나?
- `shapiro(x)` 의 p값이 0.4 면 「x 는 정규분포를 따른다」고 단정할 수 있나?

### 8. 스피어만 상관이 잡아내는 관계의 범위 (경계)

- y = x³ 처럼 굽었지만 꾸준히 오르는 관계에는 피어슨과 스피어만 중 어느 것이 더 알맞나?
- x 가 음수에서 양수까지 걸친 y = x² (U자) 관계도 스피어만이 강하게 잡아내나?

### 9. 분포 객체의 `ppf` 와 검정 함수의 다리 (연결)

- `stats.chi2(df=1).ppf(0.95)` 로 구한 값과 `chi2_contingency` 가 돌려준 통계량을 어떻게 이어 써서 판정하나?

## 실습

### 실습 1. `scipy.stats` 사용법을 절별로 찍어 주는 안내 스크립트

**만들 것** — 확률 분포 · t-검정 · 카이제곱 검정 · 상관 분석의 예제 코드를 세 따옴표 문자열로 절마다 화면에 찍고, 끝에 주요 함수 목록을 찍는 스크립트를 만든다.
스크립트 자체는 통계를 계산하지 않는다 — 각 절의 코드를 글자로 보여 주는 「사용법 안내판」이다.

**준비물** — 이 스크립트는 코드를 문자열로 찍기만 하므로 실행에 `scipy` 가 필요 없다. 찍힌 조각을 따로 돌려 보려면 `pip install scipy numpy` 가 필요하다.

**요구 조건**

1. 1단계 — `=== 확률 분포 ===` 제목을 찍고, 세 따옴표 문자열로 다음 조각을 찍는다: 평균 0 · 표준편차 1 인 정규분포 객체를 만들어 `pdf(0)` · `cdf(1.96)` · `ppf(0.975)` · `rvs(size=5)` 를 출력하는 코드.
2. 같은 문자열 안에 자유도 10 인 t분포의 `ppf(0.975)`, `n=10, p=0.5` 이항분포의 `pmf(5)` · `cdf(5)`, `mu=3` 포아송의 `pmf(2)`, 자유도 5 인 카이제곱분포의 `ppf(0.95)` 를 출력하는 코드를 넣는다.
3. 2단계 — 빈 줄 뒤 `=== t-검정 ===` 을 찍고, 문자열로 다음 조각을 찍는다: 씨앗 42 로 평균 100 · 110, 표준편차 15, 크기 30 인 두 집단을 만들어 `ttest_ind` 로 비교하고 t-통계량 · p값 · 「p < 0.05 면 귀무가설 기각」 판정을 출력하는 코드.
4. 같은 문자열 안에 `before` · `after` 다섯 쌍을 `ttest_rel` 로, 첫 집단을 `popmean=100` 과 `ttest_1samp` 으로 검정해 p값을 출력하는 코드를 넣는다.
5. 3단계 — 빈 줄 뒤 `=== 카이제곱 검정 ===` 을 찍고, 문자열로 다음 조각을 찍는다: 남녀 × 찬반 2×2 교차표를 `chi2_contingency` 에 넣어 통계량 · p값 · 자유도 · 기대빈도 · 독립 여부 판정을 출력하는 코드, 그리고 요일별 방문자 빈도를 균등 기대빈도와 `chisquare` 로 비교해 p값을 출력하는 코드.
6. 4단계 — 빈 줄 뒤 `=== 상관 분석 ===` 을 찍고, 문자열로 다음 조각을 찍는다: 씨앗 42 로 x 100개와 `y = 2x + 잡음` 을 만들어 `pearsonr` · `spearmanr` · `kendalltau` 계수를 출력하고, `shapiro(x)` 의 p값과 「p > 0.05 면 정규분포 따름」 판정을 출력하는 코드.
7. 5단계 — 빈 줄 뒤 `=== 주요 함수 정리 ===` 를 찍고, 분포 생성 · 분포 메서드 · t-검정 · 카이제곱 · 상관 · 정규성 여섯 갈래의 함수 이름을 한 줄씩 찍는다.

**시작 코드**

```python
# scipy.stats - 통계 분석 핵심 모듈
# pip install scipy numpy

print("=== 확률 분포 ===")
print("""
from scipy import stats
import numpy as np

# --- 정규분포 ---
# TODO: 평균 0, 표준편차 1 인 정규분포 객체를 만든다
# TODO: pdf(0), cdf(1.96), ppf(0.975), rvs(size=5) 를 출력한다

# --- 다양한 분포 ---
# TODO: t분포(자유도 10) 의 95% 임계값
# TODO: 이항분포(n=10, p=0.5) 의 P(X=5), P(X<=5)
# TODO: 포아송분포(λ=3) 의 P(X=2)
# TODO: 카이제곱분포(자유도 5) 의 95% 임계값
""")

print()
print("=== t-검정 ===")
print("""
import numpy as np
from scipy import stats

np.random.seed(42)
group_a = np.random.normal(loc=100, scale=15, size=30)
group_b = np.random.normal(loc=110, scale=15, size=30)

# TODO: 독립 표본 t-검정 — t-통계량, p-값, 유의수준 0.05 판정 출력

before = np.array([85, 90, 78, 92, 88])
after = np.array([90, 95, 82, 96, 91])
# TODO: 대응 표본 t-검정 p-값 출력

# TODO: 단일 표본 t-검정 (모평균 100) p-값 출력
""")

print()
print("=== 카이제곱 검정 ===")
print("""
from scipy import stats
import numpy as np

observed = np.array([
    [50, 30],   # 남성: 찬성 50, 반대 30
    [35, 45]    # 여성: 찬성 35, 반대 45
])
# TODO: 독립성 검정 — 통계량, p-값, 자유도, 기대빈도, 독립 여부 출력

observed_freq = [18, 22, 20, 25, 15]  # 요일별 방문자
expected_freq = [20, 20, 20, 20, 20]  # 균등 분포 기대
# TODO: 적합도 검정 p-값 출력
""")

print()
print("=== 상관 분석 ===")
print("""
from scipy import stats
import numpy as np

np.random.seed(42)
x = np.random.normal(0, 1, 100)
y = 2 * x + np.random.normal(0, 0.5, 100)  # 강한 양의 상관

# TODO: 피어슨 상관계수와 p-값
# TODO: 스피어만 상관계수
# TODO: 켄달 타우
# TODO: Shapiro-Wilk 정규성 검정 p-값과 판정
""")

print()
print("=== 주요 함수 정리 ===")
print("분포 생성: stats.norm(), stats.t(), stats.binom(), stats.poisson()")
# TODO: 분포 메서드 · t-검정 · 카이제곱 · 상관 · 정규성 다섯 줄
```

**확인 방법** — `python scipy-stats.py` 로 실행해 다섯 절의 제목과 코드 조각, 마지막 함수 목록이 차례대로 찍히는지 본다. 찍힌 조각 하나를 새 파일에 옮겨 `scipy` 가 깔린 환경에서 돌리면 숫자 결과도 볼 수 있다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
