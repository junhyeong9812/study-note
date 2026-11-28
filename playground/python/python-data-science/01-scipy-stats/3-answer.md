# python/python-data-science/01 — SciPy 통계 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 숫자가 아니라 코드 글자가 찍히고, `\n` 줄은 두 줄로 쪼개진다

**출력**

```text
print(f"자유도: {dof}")
print(f"기대빈도:
{expected}")
```

**왜 그런가**
코드 전체가 `print("""...""")` 의 세 따옴표 문자열 안에 있어서, `chi2_contingency` 는 불리지 않고 글자로만 찍힌다.
그래서 자유도 값 대신 `print(f"자유도: {dof}")` 라는 글자가 그대로 나온다.
바깥 문자열은 raw 문자열이 아니므로 그 안의 `\n` 이 줄바꿈 문자로 바뀌고, `기대빈도:` 뒤에서 줄이 끊긴다.
근거: 2-summary 「어디서 틀리나 1」.

### 2. 기대빈도는 두 행 모두 42.5 · 37.5, 자유도는 1

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 행합: 남성 50+30 = 80, 여성 35+45 = 80.
- 열합: 찬성 50+35 = 85, 반대 30+45 = 75, 총합 160.
- 기대빈도 = 행합 × 열합 ÷ 총합:
  - 남성 찬성 80×85/160 = 42.5, 남성 반대 80×75/160 = 37.5
  - 여성 찬성 80×85/160 = 42.5, 여성 반대 80×75/160 = 37.5
- 자유도 = (2−1)×(2−1) = 1.

**왜 그런가**
성별과 찬반이 독립이라면 각 칸의 빈도는 행 비율과 열 비율의 곱으로 정해진다.
두 행의 합이 모두 80 이라 두 행의 기대빈도가 같아진다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 대략 1.96 — `ppf` 는 `cdf` 의 역이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
약 1.96 이 된다.

**왜 그런가**
`norm.cdf(1.96)` 은 약 0.975 이고, `ppf` 는 누적확률을 넣으면 그 확률이 되는 x 를 돌려준다.
그래서 `cdf` 로 간 길을 `ppf` 로 되돌아와 출발점 1.96 근처로 돌아온다(부동소수 계산이라 아주 작은 오차는 있을 수 있다).
근거: 2-summary 「동작 방식 (1)」.

### 4. 「귀무가설이 참이면 거의 안 일어날 일」이 일어났다는 뜻이라서

p값은 귀무가설이 참이라고 가정했을 때 지금만큼(또는 더) 극단적인 결과가 나올 확률이다.
이 확률이 유의수준(보통 0.05)보다 작으면, 가정이 맞다고 보기에는 결과가 너무 드물다.
그래서 가정(귀무가설)을 버린다.
근거: 2-summary 「동작 방식 (5)」.

### 5. 같은 사람끼리 짝을 지어 개인차를 지우기 때문이다

`before[i]` 와 `after[i]` 는 같은 사람의 점수라 짝이 있다.
`ttest_rel` 은 사람마다 「후 − 전」을 먼저 구해 그 차이의 평균이 0 인지 본다 — 사람마다 다른 실력(개인차)이 빠진다.
`ttest_ind` 는 짝을 버리고 두 묶음을 독립 집단으로 다뤄서, 개인차가 잡음으로 남는다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 5」.

### 6. 이산분포는 한 점의 확률이 의미 있고, 연속분포는 한 점의 확률이 0 이라서

이항 · 포아송은 값이 0, 1, 2… 처럼 끊어져 있어 「정확히 5가 나올 확률」이 바로 계산된다 — 그것이 `pmf` 다.
정규 · t 는 연속이라 한 점의 확률이 0 이고, 곡선의 높이(밀도)만 의미가 있다 — 그것이 `pdf` 다.
그래서 `pdf` 값은 확률이 아니며 1 을 넘을 수도 있다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 6」.

### 7. 둘 다 안 된다 — 「기각하지 못했다」까지만 말할 수 있다

p ≥ 0.05 는 귀무가설을 버릴 증거가 부족하다는 뜻일 뿐, 귀무가설이 참이라는 증명이 아니다.
`ttest_ind` 의 p = 0.3 이면 「평균 차이를 보일 증거가 부족하다」이고, 표본이 작으면 실제 차이가 있어도 이렇게 나올 수 있다.
`shapiro` 의 p = 0.4 도 「정규성을 부정할 증거를 못 찾았다」이다.
원본 예제가 찍는 「귀무가설 채택」 · 「정규분포 따름」은 이 점에서 지나친 표현이다.
근거: 2-summary 「어디서 틀리나 2」 · 「어디서 틀리나 3」.

### 8. y = x³ 에는 스피어만이 알맞고, U자 관계는 스피어만도 잡지 못한다

스피어만은 값을 순위로 바꿔 재므로, 한쪽이 커질 때 다른 쪽도 늘 커지는 단조 관계면 직선이 아니어도 강하게 잡는다 — y = x³ 이 그렇다.
피어슨은 직선 기준이라 굽은 관계를 약하게 볼 수 있다.
U자(y = x², x 가 음수~양수)는 y 의 순위가 내려갔다가 올라가므로 단조가 아니다 — 스피어만 상관도 0 에 가깝게 나온다.
원본 주석의 「비선형에도 유효」는 「단조인 비선형에 유효」로 좁혀 읽어야 한다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 4」.

### 9. 통계량이 `ppf` 임계값을 넘으면 기각 — p < 0.05 와 같은 판정이다

2×2 교차표는 자유도가 1 이므로 `stats.chi2(df=1).ppf(0.95)` 가 위쪽 5% 경계, 곧 합격선이다.
`chi2_contingency` 가 돌려준 통계량이 이 값보다 크면 귀무가설(독립)을 기각한다.
이것은 p값이 0.05 보다 작은지 보는 것과 같은 판정을 다른 쪽에서 본 것이다.
t-검정에서 `stats.t(df=...).ppf(0.975)` 가 양측 합격선 역할을 하는 것과 같은 구조다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 7」.

## 실습 정답

### 실습 1. `scipy.stats` 사용법을 절별로 찍어 주는 안내 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 정규분포 객체와 네 메서드 출력 조각 | `print("=== 확률 분포 ===")` 뒤 문자열의 `norm = stats.norm(loc=0, scale=1)` · `norm.pdf(0)` · `norm.cdf(1.96)` · `norm.ppf(0.975)` · `norm.rvs(size=5)` |
| 2. t · 이항 · 포아송 · 카이제곱 분포 조각 | 같은 문자열의 `stats.t(df=10)` · `stats.binom(n=10, p=0.5)` · `stats.poisson(mu=3)` · `stats.chi2(df=5)` 와 각 `ppf` · `pmf` · `cdf` 호출 |
| 3. 두 집단 독립 t-검정과 판정 조각 | `print("=== t-검정 ===")` 뒤 문자열의 `np.random.seed(42)` · `group_a` · `group_b` · `stats.ttest_ind(group_a, group_b)` · `p_value < 0.05` 조건식 |
| 4. 대응 · 단일 표본 t-검정 조각 | `stats.ttest_rel(before, after)` · `stats.ttest_1samp(group_a, popmean=100)` |
| 5. 독립성 · 적합도 카이제곱 조각 | `print("=== 카이제곱 검정 ===")` 뒤 문자열의 `stats.chi2_contingency(observed)` · `stats.chisquare(observed_freq, expected_freq)` |
| 6. 세 상관계수와 정규성 검정 조각 | `print("=== 상관 분석 ===")` 뒤 문자열의 `stats.pearsonr(x, y)` · `stats.spearmanr(x, y)` · `stats.kendalltau(x, y)` · `stats.shapiro(x)` · `p_value > 0.05` 조건식 |
| 7. 주요 함수 여섯 줄 | `print("=== 주요 함수 정리 ===")` 뒤의 `print("분포 생성: …")` ~ `print("정규성: …")` |
| 절 사이 빈 줄 | 각 절 앞의 `print()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/scipy-stats.py`

```python
# [데이터 과학 & 수학] SciPy 통계
# 설명: 확률 분포, t-검정, 카이제곱 검정, 상관 분석 (scipy.stats)
# 팁: p-값이 유의수준(보통 0.05)보다 작으면 귀무가설을 기각한다. 피어슨은 선형 관계만 측정하므로 비선형 관계에는 스피어만을 사용한다. t-검정 전에 shapiro()로 정규성을 확인하는 것이 좋다.

# scipy.stats - 통계 분석 핵심 모듈
# pip install scipy numpy

# 섹션 제목: 다양한 확률 분포 객체와 메서드
print("=== 확률 분포 ===")
# stats.norm/t/binom/poisson/chi2 등은 동결 분포 객체로 .pdf/.cdf/.ppf 제공
print("""
from scipy import stats
import numpy as np

# --- 정규분포 ---
norm = stats.norm(loc=0, scale=1)  # 평균=0, 표준편차=1
print(f"PDF at x=0: {norm.pdf(0):.4f}")        # 확률밀도함수
print(f"CDF at x=1.96: {norm.cdf(1.96):.4f}")  # 누적분포함수 (≈0.975)
print(f"PPF at p=0.975: {norm.ppf(0.975):.4f}") # 역CDF (≈1.96)
print(f"Random samples: {norm.rvs(size=5)}")    # 랜덤 샘플

# --- 다양한 분포 ---
# t분포 (자유도=10)
t_dist = stats.t(df=10)
print(f"t분포 95% 임계값: {t_dist.ppf(0.975):.4f}")

# 이항분포 (n=10, p=0.5)
binom = stats.binom(n=10, p=0.5)
print(f"P(X=5): {binom.pmf(5):.4f}")   # 확률질량함수
print(f"P(X<=5): {binom.cdf(5):.4f}")  # 누적확률

# 포아송분포 (λ=3)
poisson = stats.poisson(mu=3)
print(f"P(X=2): {poisson.pmf(2):.4f}")

# 카이제곱분포 (자유도=5)
chi2 = stats.chi2(df=5)
print(f"카이제곱 95% 임계값: {chi2.ppf(0.95):.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 평균 비교를 위한 t-검정
print("=== t-검정 ===")
# 독립/대응/단일표본 t-검정 함수와 p값 해석법
print("""
import numpy as np
from scipy import stats

np.random.seed(42)
group_a = np.random.normal(loc=100, scale=15, size=30)
group_b = np.random.normal(loc=110, scale=15, size=30)

# 독립 표본 t-검정 (두 그룹 평균 비교)
t_stat, p_value = stats.ttest_ind(group_a, group_b)
print(f"t-통계량: {t_stat:.4f}")
print(f"p-값: {p_value:.4f}")
print(f"유의수준 0.05에서 {'귀무가설 기각 (차이 있음)' if p_value < 0.05 else '귀무가설 채택'}")

# 대응 표본 t-검정 (같은 그룹의 전후 비교)
before = np.array([85, 90, 78, 92, 88])
after = np.array([90, 95, 82, 96, 91])
t_stat, p_value = stats.ttest_rel(before, after)
print(f"대응 t-검정 p-값: {p_value:.4f}")

# 단일 표본 t-검정 (모평균과 비교)
t_stat, p_value = stats.ttest_1samp(group_a, popmean=100)
print(f"단일 표본 t-검정 p-값: {p_value:.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 범주형 데이터의 독립성/적합도 검정
print("=== 카이제곱 검정 ===")
# chi2_contingency는 교차표 독립성, chisquare는 적합도 검정
print("""
from scipy import stats
import numpy as np

# 독립성 검정 (교차표)
observed = np.array([
    [50, 30],   # 남성: 찬성 50, 반대 30
    [35, 45]    # 여성: 찬성 35, 반대 45
])
chi2, p_value, dof, expected = stats.chi2_contingency(observed)
print(f"카이제곱 통계량: {chi2:.4f}")
print(f"p-값: {p_value:.4f}")
print(f"자유도: {dof}")
print(f"기대빈도:\n{expected}")
print(f"성별과 찬반은 {'독립이 아님 (관련 있음)' if p_value < 0.05 else '독립 (관련 없음)'}")

# 적합도 검정 (관측값이 기대 분포에 맞는지)
observed_freq = [18, 22, 20, 25, 15]  # 요일별 방문자
expected_freq = [20, 20, 20, 20, 20]  # 균등 분포 기대
chi2, p_value = stats.chisquare(observed_freq, expected_freq)
print(f"적합도 검정 p-값: {p_value:.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 두 변수 간 관계 강도 측정
print("=== 상관 분석 ===")
# 피어슨(선형), 스피어만(순위), 켄달(순서일치)의 차이
print("""
from scipy import stats
import numpy as np

np.random.seed(42)
x = np.random.normal(0, 1, 100)
y = 2 * x + np.random.normal(0, 0.5, 100)  # 강한 양의 상관

# 피어슨 상관계수 (선형 관계)
r, p_value = stats.pearsonr(x, y)
print(f"피어슨 상관계수: {r:.4f}")
print(f"p-값: {p_value:.6f}")

# 스피어만 상관계수 (순위 기반, 비선형에도 유효)
rho, p_value = stats.spearmanr(x, y)
print(f"스피어만 상관계수: {rho:.4f}")

# 켄달 타우 (순서 일치도)
tau, p_value = stats.kendalltau(x, y)
print(f"켄달 타우: {tau:.4f}")

# 정규성 검정 (Shapiro-Wilk)
stat, p_value = stats.shapiro(x)
print(f"정규성 검정 p-값: {p_value:.4f}")
print(f"정규분포 {'따름' if p_value > 0.05 else '따르지 않음'}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: scipy.stats 주요 함수와 메서드 정리
print("=== 주요 함수 정리 ===")
# 분포 객체 생성 함수
print("분포 생성: stats.norm(), stats.t(), stats.binom(), stats.poisson()")
# 분포 객체의 공통 메서드 (pdf, cdf 등)
print("분포 메서드: .pdf(), .cdf(), .ppf(), .rvs(), .mean(), .var()")
# 평균 비교용 t-검정 함수들
print("t-검정: ttest_ind(), ttest_rel(), ttest_1samp()")
# 카이제곱 검정 함수
print("카이제곱: chi2_contingency(), chisquare()")
# 상관계수 함수
print("상관: pearsonr(), spearmanr(), kendalltau()")
# 정규성 검정 함수
print("정규성: shapiro(), normaltest(), kstest()")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 확률 분포 ===

from scipy import stats
import numpy as np

# --- 정규분포 ---
norm = stats.norm(loc=0, scale=1)  # 평균=0, 표준편차=1
print(f"PDF at x=0: {norm.pdf(0):.4f}")        # 확률밀도함수
print(f"CDF at x=1.96: {norm.cdf(1.96):.4f}")  # 누적분포함수 (≈0.975)
print(f"PPF at p=0.975: {norm.ppf(0.975):.4f}") # 역CDF (≈1.96)
print(f"Random samples: {norm.rvs(size=5)}")    # 랜덤 샘플

# --- 다양한 분포 ---
# t분포 (자유도=10)
t_dist = stats.t(df=10)
print(f"t분포 95% 임계값: {t_dist.ppf(0.975):.4f}")

# 이항분포 (n=10, p=0.5)
binom = stats.binom(n=10, p=0.5)
print(f"P(X=5): {binom.pmf(5):.4f}")   # 확률질량함수
print(f"P(X<=5): {binom.cdf(5):.4f}")  # 누적확률

# 포아송분포 (λ=3)
poisson = stats.poisson(mu=3)
print(f"P(X=2): {poisson.pmf(2):.4f}")

# 카이제곱분포 (자유도=5)
chi2 = stats.chi2(df=5)
print(f"카이제곱 95% 임계값: {chi2.ppf(0.95):.4f}")


=== t-검정 ===

import numpy as np
from scipy import stats

np.random.seed(42)
group_a = np.random.normal(loc=100, scale=15, size=30)
group_b = np.random.normal(loc=110, scale=15, size=30)

# 독립 표본 t-검정 (두 그룹 평균 비교)
t_stat, p_value = stats.ttest_ind(group_a, group_b)
print(f"t-통계량: {t_stat:.4f}")
print(f"p-값: {p_value:.4f}")
print(f"유의수준 0.05에서 {'귀무가설 기각 (차이 있음)' if p_value < 0.05 else '귀무가설 채택'}")

# 대응 표본 t-검정 (같은 그룹의 전후 비교)
before = np.array([85, 90, 78, 92, 88])
after = np.array([90, 95, 82, 96, 91])
t_stat, p_value = stats.ttest_rel(before, after)
print(f"대응 t-검정 p-값: {p_value:.4f}")

# 단일 표본 t-검정 (모평균과 비교)
t_stat, p_value = stats.ttest_1samp(group_a, popmean=100)
print(f"단일 표본 t-검정 p-값: {p_value:.4f}")


=== 카이제곱 검정 ===

from scipy import stats
import numpy as np

# 독립성 검정 (교차표)
observed = np.array([
    [50, 30],   # 남성: 찬성 50, 반대 30
    [35, 45]    # 여성: 찬성 35, 반대 45
])
chi2, p_value, dof, expected = stats.chi2_contingency(observed)
print(f"카이제곱 통계량: {chi2:.4f}")
print(f"p-값: {p_value:.4f}")
print(f"자유도: {dof}")
print(f"기대빈도:
{expected}")
print(f"성별과 찬반은 {'독립이 아님 (관련 있음)' if p_value < 0.05 else '독립 (관련 없음)'}")

# 적합도 검정 (관측값이 기대 분포에 맞는지)
observed_freq = [18, 22, 20, 25, 15]  # 요일별 방문자
expected_freq = [20, 20, 20, 20, 20]  # 균등 분포 기대
chi2, p_value = stats.chisquare(observed_freq, expected_freq)
print(f"적합도 검정 p-값: {p_value:.4f}")


=== 상관 분석 ===

from scipy import stats
import numpy as np

np.random.seed(42)
x = np.random.normal(0, 1, 100)
y = 2 * x + np.random.normal(0, 0.5, 100)  # 강한 양의 상관

# 피어슨 상관계수 (선형 관계)
r, p_value = stats.pearsonr(x, y)
print(f"피어슨 상관계수: {r:.4f}")
print(f"p-값: {p_value:.6f}")

# 스피어만 상관계수 (순위 기반, 비선형에도 유효)
rho, p_value = stats.spearmanr(x, y)
print(f"스피어만 상관계수: {rho:.4f}")

# 켄달 타우 (순서 일치도)
tau, p_value = stats.kendalltau(x, y)
print(f"켄달 타우: {tau:.4f}")

# 정규성 검정 (Shapiro-Wilk)
stat, p_value = stats.shapiro(x)
print(f"정규성 검정 p-값: {p_value:.4f}")
print(f"정규분포 {'따름' if p_value > 0.05 else '따르지 않음'}")


=== 주요 함수 정리 ===
분포 생성: stats.norm(), stats.t(), stats.binom(), stats.poisson()
분포 메서드: .pdf(), .cdf(), .ppf(), .rvs(), .mean(), .var()
t-검정: ttest_ind(), ttest_rel(), ttest_1samp()
카이제곱: chi2_contingency(), chisquare()
상관: pearsonr(), spearmanr(), kendalltau()
정규성: shapiro(), normaltest(), kstest()
````

**풀이 요점**

- 각 절의 코드는 `print("""...""")` 안에 있어 실행되지 않고 글자로 찍힌다 — 그래서 실행 결과에 숫자가 하나도 없다.
- 문자열 안의 `\n` 은 진짜 줄바꿈이 되어 `기대빈도:` 줄이 둘로 쪼개져 찍힌다.
- 분포 절은 「분포 객체 만들기 → 메서드로 묻기」 틀을 다섯 분포에 되풀이한다.
- t-검정 절은 비교 대상에 따라 `ttest_ind` · `ttest_rel` · `ttest_1samp` 을 고르는 예다.
- 카이제곱 절은 교차표(`chi2_contingency`, 반환값 넷)와 한 줄 빈도(`chisquare`, 반환값 둘)를 가른다.
- 숫자 결과를 보려면 조각을 꺼내 `scipy` · `numpy` 를 깔고 따로 실행해야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
