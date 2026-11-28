# python/python-data-science/02 — SciPy 최적화 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 1차원 함수를 0 에서 출발해 최소화하면 (예측)

```python
# 질문용 발췌
def f(x):
    return (x - 3) ** 2 + 5

result = minimize(f, x0=0)
print(f"{result.x[0]:.4f}, {result.fun:.4f}")
```

- 이 코드를 실행하면 두 숫자는 대략 무엇이 나오는가?

### 2. 합이 10 인 두 수로 objective 를 최소화하면 (예측)

```python
# 질문용 발췌
def objective(x):
    return x[0]**2 + x[1]**2 + x[0]*x[1]

constraints = [
    {'type': 'eq', 'fun': lambda x: x[0] + x[1] - 10},
    {'type': 'ineq', 'fun': lambda x: x[0] - 2},
]
res4 = minimize(objective, [5, 5], method='SLSQP', constraints=constraints)
```

- `res4.x` 와 `res4.fun` 은 대략 무엇이 되는가?

### 3. 삼차식의 근을 세 출발점에서 찾으면 (예측)

```python
# 질문용 발췌
def f(x):
    return x**3 - 6*x**2 + 11*x - 6   # 근: 1, 2, 3

root1 = fsolve(f, x0=0.5)
root2 = fsolve(f, x0=1.5)
root3 = fsolve(f, x0=3.5)
```

- `root1[0]` · `root2[0]` · `root3[0]` 은 각각 어느 근이 될 것이라 보는가?

### 4. 원본 예제 파일을 돌리면 계산 결과 대신 코드 글자가 나온다 (왜)

- 예제 파일을 그대로 실행했을 때 최솟값 숫자 대신 `from scipy.optimize import minimize` 같은 줄이 찍히는 까닭은 무엇인가?

### 5. `brentq` 는 구간 양 끝의 부호가 달라야 한다 (왜)

- `brentq(f, a, b)` 가 `f(a)` 와 `f(b)` 의 부호가 다르기를 요구하는 까닭은 무엇인가?

### 6. `'ineq'` 제약에 `x[0] - 2` 를 적는다 (왜)

- 「x ≥ 2」 를 표현하려고 `'fun': lambda x: x[0] - 2` 를 쓰는 까닭은 무엇인가?

### 7. 경계를 걸어도 답이 그대로인 경우 (경계)

- `objective` 에 `bounds=[(0, None), (0, None)]` 를 걸고 `L-BFGS-B` 로 풀 때, 경계가 없을 때와 답이 달라지는가?

### 8. `p0` 없이 가우시안을 맞추면 어디까지 믿을 수 있나 (경계)

- 가우시안 피팅에서 `p0` 를 빼거나 참값에서 먼 값을 주면 무엇이 흔들릴 수 있는가?

### 9. `curve_fit` 과 `minimize` 를 잇는 다리 (연결)

- `curve_fit` 이 하는 일을 `minimize` 의 말(목적함수 · 초기값)로 바꿔 말하면 무엇인가?

## 실습

### 실습 1. `scipy.optimize` 사용법 안내 스크립트 만들기

**만들 것** — 다섯 절로 된 안내 스크립트를 만든다.
각 절은 제목 줄을 찍고, 그 절의 `scipy.optimize` 사용 예제 코드를 세 따옴표 문자열로 통째 출력한다(문자열 안의 코드는 실행하지 않는다).

**준비물** — 출력된 예제 코드를 따로 떼어 실행해 보려면 `pip install scipy numpy` 가 필요하다. 스크립트 자체는 문자열만 찍으므로 표준 Python 으로 돈다.

**요구 조건**

1. 절과 절 사이에는 `print()` 로 빈 줄을 하나 찍는다.
2. 1단계 — 제목 `=== minimize: 함수 최솟값 찾기 ===` 아래에 출력할 예제 코드:
   1. `(x - 3) ** 2 + 5` 를 `x0=0` 에서 `minimize` 로 최소화하고 `result.x[0]` · `result.fun` · `result.success` 를 출력한다.
   2. Rosenbrock 함수를 `x0=[0, 0]` · `method='BFGS'` 로 최소화하고 위치 x · y, 최솟값, 반복 횟수 `result.nit` 를 출력한다.
3. 2단계 — 제목 `=== 다양한 최적화 방법 ===` 아래 예제 코드:
   1. `objective(x) = x[0]**2 + x[1]**2 + x[0]*x[1]`, 출발점 `[5, 5]`.
   2. `Nelder-Mead` · `BFGS` 로 각각 푼다.
   3. `L-BFGS-B` 로 x ≥ 0, y ≥ 0 경계를 걸어 푼다.
   4. `SLSQP` 로 등식 제약 x + y = 10 과 부등식 제약 x ≥ 2 를 걸어 푼다.
   5. 넷 다 `res.x` 와 함수값을 출력한다.
4. 3단계 — 제목 `=== curve_fit: 데이터 피팅 ===` 아래 예제 코드:
   1. 모델 함수 `linear(x, a, b)` · `exponential(x, a, b, c)` · `gaussian(x, amp, mu, sigma)` 를 정의한다.
   2. 시드 42 로 고정한 잡음을 직선 2.5x + 1.3 에 얹은 50점을 만든다.
   3. `linear` 로 피팅해 a, b 와 각 표준 오차(`pcov` 대각의 제곱근)를 출력한다.
   4. 참값 amp 3, mu 1, sigma 1 인 가우시안에 잡음을 얹은 100점을 만들고, `p0=[3, 1, 1]` 로 피팅해 세 파라미터를 출력한다.
5. 4단계 — 제목 `=== 근 찾기 (Root Finding) ===` 아래 예제 코드:
   1. 근이 1, 2, 3 인 삼차식 `f` 를 정의한다.
   2. `fsolve` 를 출발점 0.5 · 1.5 · 3.5 에서 불러 근 셋을 출력한다.
   3. `brentq` 로 구간 [0.5, 1.5] 의 근을 출력한다.
   4. `root_scalar` 에 같은 구간과 `method='brentq'` 를 주고 근과 반복 횟수를 출력한다.
   5. 연립방정식 x² + y² = 25, xy = 12 를 `fsolve` 로 출발점 `[3, 4]` 에서 풀어 x, y 를 출력한다.
6. 5단계 — 제목 `=== 주요 함수 정리 ===` 아래에 시그니처 넷을 한 줄씩 직접 출력한다: `minimize(…)` · `curve_fit(…) -> (popt, pcov)` · 근 찾기 함수 셋 · 방법 목록(`Nelder-Mead, BFGS, L-BFGS-B, SLSQP, Powell`).

**시작 코드**

```python
# scipy.optimize - 최적화 및 근 찾기
# pip install scipy numpy

print("=== minimize: 함수 최솟값 찾기 ===")
print("""
from scipy.optimize import minimize
import numpy as np

# 1차원 함수 최소화
def f(x):
    return (x - 3) ** 2 + 5

# TODO: x0=0 에서 최소화하고 위치 · 최솟값 · 수렴 성공을 출력

# 다변수 함수 최소화
def rosenbrock(x):
    # Rosenbrock 함수: 최적화 벤치마크
    return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

# TODO: x0=[0, 0], BFGS 로 최소화하고 x · y · 최솟값 · 반복 횟수를 출력
""")

print()
print("=== 다양한 최적화 방법 ===")
print("""
from scipy.optimize import minimize
import numpy as np

def objective(x):
    return x[0]**2 + x[1]**2 + x[0]*x[1]

x0 = [5, 5]

# TODO: Nelder-Mead
# TODO: BFGS
# TODO: L-BFGS-B + bounds (x >= 0, y >= 0)
# TODO: constraints (x + y = 10, x >= 2) + SLSQP
""")

print()
print("=== curve_fit: 데이터 피팅 ===")
print("""
from scipy.optimize import curve_fit
import numpy as np

# TODO: 모델 함수 linear / exponential / gaussian

# 데이터 생성 (노이즈 포함)
np.random.seed(42)
x_data = np.linspace(0, 10, 50)
y_data = 2.5 * x_data + 1.3 + np.random.normal(0, 1, 50)

# TODO: 선형 피팅 → 계수와 표준 오차 출력

x_gauss = np.linspace(-5, 5, 100)
y_gauss = 3 * np.exp(-((x_gauss - 1) ** 2) / 2) + np.random.normal(0, 0.1, 100)
# TODO: p0 를 주고 가우시안 피팅 → amp, mu, sigma 출력
""")

print()
print("=== 근 찾기 (Root Finding) ===")
print("""
from scipy.optimize import fsolve, brentq, root_scalar
import numpy as np

def f(x):
    return x**3 - 6*x**2 + 11*x - 6  # 근: 1, 2, 3

# TODO: fsolve 를 0.5 / 1.5 / 3.5 에서 → 근 셋 출력
# TODO: brentq 로 [0.5, 1.5] 구간의 근
# TODO: root_scalar (bracket, method) → 근과 반복 횟수

# TODO: 연립방정식 x² + y² = 25, xy = 12 를 fsolve 로 (출발점 [3, 4])
""")

print()
print("=== 주요 함수 정리 ===")
# TODO: 시그니처 네 줄
```

**확인 방법** — `python scipy-optimize.py` 로 돌려 다섯 절의 제목과 예제 코드가 차례대로 찍히는지 본다. 각 절의 문자열을 따로 `.py` 파일로 떼어 scipy 가 깔린 환경에서 돌리면 실제 계산값을 볼 수 있다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
