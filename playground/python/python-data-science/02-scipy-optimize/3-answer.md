# python/python-data-science/02 — SciPy 최적화 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 대략 3.0000, 5.0000 — 바닥 위치와 바닥 높이

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`3.0000, 5.0000` 근처가 나온다. 마지막 자리는 수치 근삿값이라 조금 다를 수 있다.

**왜 그런가**
`(x - 3)**2` 는 x = 3 에서 0 이고 다른 곳에서는 양수다.
그래서 `f` 는 x = 3 에서 가장 작고, 그 값은 0 + 5 = 5 다.
`minimize` 는 0 에서 출발해 값이 줄어드는 쪽(오른쪽)으로 걸어 그 바닥에서 멈춘다.
`result.x` 는 배열이라 `[0]` 으로 꺼냈다.
원본 주석도 `≈ 3.0` · `≈ 5.0` 이다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 대략 (5, 5), 함수값 75

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`res4.x` 는 `[5, 5]` 근처, `res4.fun` 은 `75` 근처다.

**왜 그런가**
등식 제약 x + y = 10 을 지키면 `objective = (x + y)² − xy = 100 − xy` 다.
합이 10 일 때 곱 xy 는 x = y = 5 에서 25 로 가장 크므로, objective 는 100 − 25 = 75 로 가장 작다.
부등식 제약 x ≥ 2 도 x = 5 가 지킨다.
출발점 `[5, 5]` 가 이미 답이라 많이 움직이지 않아도 된다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 0.5 → 근 1, 3.5 → 근 3, 1.5 → 장담할 수 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`root1[0]` 은 1 근처, `root3[0]` 은 3 근처일 것이다.
`root2[0]` 은 원본 주석이 기대하는 2 가 아닐 수 있다 — 어느 근인지는 확인 필요.

**왜 그런가**
`fsolve` 는 출발점 근처를 따라 0 쪽으로 간다.
0.5 와 3.5 는 각각 근 1 · 근 3 과 가깝고, 그 사이에 기울기가 0 이 되는 곳이 없다.
1.5 는 봉우리(x ≈ 1.42) 바로 옆이라 기울기가 −0.25 로 아주 작다.
f(1.5) = 0.375 를 이 작은 기울기로 나누면 한 걸음에 1.5 만큼 튀어 x = 3 근처에 떨어질 수 있다.
근거: 2-summary 「어디서 틀리나 3」 · 「동작 방식 (5)」.

### 4. 코드가 세 따옴표 문자열 안에 있어서 실행되지 않고 글자로 찍힌다

예제의 각 절은 `print("""…""")` 꼴이다.
세 따옴표 안의 내용은 코드가 아니라 문자열 값이므로, `print` 는 그 글자를 그대로 내보낼 뿐 `minimize` 를 부르지 않는다.
실제 출력의 첫머리가 그렇다.

**출력**

```text
=== minimize: 함수 최솟값 찾기 ===

from scipy.optimize import minimize
import numpy as np
```

계산값을 보려면 문자열 안의 코드를 따로 떼어 실행해야 한다.
근거: 2-summary 「어디서 틀리나 7」 · 「구현 세부사항 대 언어 보장」 첫 줄.

### 5. 부호가 바뀌어야 「구간 안에 근이 있다」가 보장되기 때문이다

f 가 a 에서 음수, b 에서 양수(또는 그 반대)면 그 사이 어딘가에서 반드시 0 을 지난다.
`brentq` 는 이 보장을 발판 삼아 구간을 좁혀 들어간다.
부호가 같으면 근이 있는지조차 모르므로 시작할 수 없다(오류를 낸다).
원본 예에서는 f(0.5) = −1.875, f(1.5) = 0.375 라 [0.5, 1.5] 가 브래킷이다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 6. `'ineq'` 는 `fun(x) >= 0` 을 요구하기 때문이다

`x[0] - 2 >= 0` 은 `x[0] >= 2` 와 같다.
그래서 「x ≥ 2」 를 「0 이상이어야 하는 식」 꼴로 옮겨 적은 것이다.
거꾸로 「x ≤ 2」 라면 `2 - x[0]` 를 적는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 7. 달라지지 않는다 — 원래 바닥 (0, 0) 이 울타리 안에 있다

`objective` 의 바닥은 경계 없이도 (0, 0), 값 0 이다.
x ≥ 0, y ≥ 0 은 (0, 0) 을 허용하므로(경계 위), 울타리가 답을 밀어내지 않는다.
경계가 답을 바꾸는 것은 원래 바닥이 울타리 밖에 있을 때뿐이다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 8. 수렴 속도와 찾아낸 파라미터 자체가 흔들릴 수 있다

원본의 팁대로 `p0` 는 수렴 속도와 결과에 큰 영향을 준다.
가우시안은 봉우리 하나짜리 모양이라, 출발 추정(특히 위치 mu)이 데이터의 봉우리에서 멀면 엉뚱한 곳에서 멈추거나 수렴하지 못할 수 있다.
원본은 그래서 참값과 같은 `p0=[3, 1, 1]` 을 준다.
근거: 2-summary 「어디서 틀리나 2」 · 「동작 방식 (4)」.

### 9. 「잔차 제곱합」을 목적함수로, `p0` 를 초기값으로 둔 최소화다

`curve_fit` 은 모델값과 데이터의 차이(잔차)를 제곱해 더한 값을 가장 작게 하는 파라미터를 찾는다.
`minimize` 의 말로는 목적함수 = 잔차 제곱합, 변수 = 모델 파라미터, 초기값 `x0` = `p0` 다.
그래서 (1) 의 「출발점이 답을 정한다」는 성질이 `curve_fit` 에도 그대로 온다.
`curve_fit` 은 여기에 공분산 행렬 `pcov` 까지 돌려준다는 점이 다르다.
근거: 2-summary 「동작 방식 (4)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. `scipy.optimize` 사용법 안내 스크립트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 절 사이 빈 줄 | 각 절 앞의 `print()` |
| 2-1. 1차원 최소화 | `result = minimize(f, x0=0)` 와 `result.x[0]` · `result.fun` · `result.success` 출력 |
| 2-2. Rosenbrock + BFGS | `minimize(rosenbrock, x0=[0, 0], method='BFGS')` 와 `result.nit` 출력 |
| 3-1~2. objective · Nelder-Mead · BFGS | `res1 = minimize(objective, x0, method='Nelder-Mead')` · `res2 = … method='BFGS'` |
| 3-3. 경계 | `res3 = … method='L-BFGS-B', bounds=[(0, None), (0, None)]` |
| 3-4. 등식 · 부등식 제약 | `constraints` 리스트(`'eq'` · `'ineq'`) 와 `res4 = … method='SLSQP'` |
| 4-1. 모델 함수 셋 | `def linear` · `def exponential` · `def gaussian` |
| 4-2~3. 선형 피팅과 표준 오차 | `popt, pcov = curve_fit(linear, x_data, y_data)` · `np.sqrt(pcov[0,0])` |
| 4-4. 가우시안 피팅 | `curve_fit(gaussian, x_gauss, y_gauss, p0=[3, 1, 1])` |
| 5-1~2. 삼차식과 fsolve 셋 | `def f` · `root1` · `root2` · `root3 = fsolve(f, x0=…)` |
| 5-3. brentq | `root = brentq(f, 0.5, 1.5)` |
| 5-4. root_scalar | `root_scalar(f, bracket=[0.5, 1.5], method='brentq')` · `result.iterations` |
| 5-5. 연립방정식 | `def equations(vars)` · `fsolve(equations, x0=[3, 4])` |
| 6. 시그니처 정리 | 마지막 네 `print(...)` 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/scipy-optimize.py`

```python
# [데이터 과학 & 수학] SciPy 최적화
# 설명: 최적화 문제, minimize, curve_fit, 근 찾기 (scipy.optimize)
# 팁: minimize의 method 선택이 중요하다. 기울기를 모르면 Nelder-Mead, 경계 조건이 있으면 L-BFGS-B, 등식/부등식 제약이면 SLSQP. curve_fit의 p0(초기 추정값)이 수렴 속도와 결과에 큰 영향을 준다.

# scipy.optimize - 최적화 및 근 찾기
# pip install scipy numpy

# 섹션 제목: 함수 f의 최솟값을 찾는 minimize
print("=== minimize: 함수 최솟값 찾기 ===")
# 초기값 x0에서 시작해 다양한 알고리즘으로 최솟값 탐색
print("""
from scipy.optimize import minimize
import numpy as np

# 1차원 함수 최소화
def f(x):
    return (x - 3) ** 2 + 5

result = minimize(f, x0=0)  # 초기값 x0=0에서 시작
print(f"최솟값 위치: {result.x[0]:.4f}")  # ≈ 3.0
print(f"최솟값: {result.fun:.4f}")         # ≈ 5.0
print(f"수렴 성공: {result.success}")

# 다변수 함수 최소화
def rosenbrock(x):
    # Rosenbrock 함수: 최적화 벤치마크
    return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

result = minimize(rosenbrock, x0=[0, 0], method='BFGS')
print(f"최솟값 위치: x={result.x[0]:.4f}, y={result.x[1]:.4f}")  # ≈ (1, 1)
print(f"최솟값: {result.fun:.8f}")  # ≈ 0
print(f"반복 횟수: {result.nit}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: minimize의 다양한 method 옵션
print("=== 다양한 최적화 방법 ===")
# Nelder-Mead/BFGS/L-BFGS-B/SLSQP의 특성과 사용 상황 비교
print("""
from scipy.optimize import minimize
import numpy as np

def objective(x):
    return x[0]**2 + x[1]**2 + x[0]*x[1]

x0 = [5, 5]

# Nelder-Mead: 기울기 불필요, 로버스트
res1 = minimize(objective, x0, method='Nelder-Mead')
print(f"Nelder-Mead: {res1.x}, f={res1.fun:.6f}")

# BFGS: 기울기 기반, 빠름
res2 = minimize(objective, x0, method='BFGS')
print(f"BFGS: {res2.x}, f={res2.fun:.6f}")

# L-BFGS-B: 경계 조건 지원
res3 = minimize(objective, x0, method='L-BFGS-B',
                bounds=[(0, None), (0, None)])  # x >= 0, y >= 0
print(f"L-BFGS-B (bounded): {res3.x}, f={res3.fun:.6f}")

# 제약 조건 최적화
constraints = [
    {'type': 'eq', 'fun': lambda x: x[0] + x[1] - 10},   # x + y = 10
    {'type': 'ineq', 'fun': lambda x: x[0] - 2}           # x >= 2
]
res4 = minimize(objective, x0, method='SLSQP', constraints=constraints)
print(f"제약 조건: {res4.x}, f={res4.fun:.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 데이터에 모델을 피팅하는 curve_fit (비선형 회귀)
print("=== curve_fit: 데이터 피팅 ===")
# popt는 최적 파라미터, pcov는 공분산 행렬 (불확실도 평가에 사용)
print("""
from scipy.optimize import curve_fit
import numpy as np

# 모델 함수 정의
def linear(x, a, b):
    return a * x + b

def exponential(x, a, b, c):
    return a * np.exp(b * x) + c

def gaussian(x, amp, mu, sigma):
    return amp * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))

# 데이터 생성 (노이즈 포함)
np.random.seed(42)
x_data = np.linspace(0, 10, 50)
y_data = 2.5 * x_data + 1.3 + np.random.normal(0, 1, 50)

# 선형 피팅
popt, pcov = curve_fit(linear, x_data, y_data)
print(f"선형 피팅: y = {popt[0]:.3f}x + {popt[1]:.3f}")
print(f"표준 오차: a±{np.sqrt(pcov[0,0]):.3f}, b±{np.sqrt(pcov[1,1]):.3f}")

# 가우시안 피팅
x_gauss = np.linspace(-5, 5, 100)
y_gauss = 3 * np.exp(-((x_gauss - 1) ** 2) / 2) + np.random.normal(0, 0.1, 100)
popt, pcov = curve_fit(gaussian, x_gauss, y_gauss, p0=[3, 1, 1])
print(f"가우시안: amp={popt[0]:.3f}, mu={popt[1]:.3f}, sigma={popt[2]:.3f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 방정식의 근 찾기 (f(x)=0)
print("=== 근 찾기 (Root Finding) ===")
# fsolve(초기값 기반), brentq(구간 기반), root_scalar(통합 인터페이스)
print("""
from scipy.optimize import fsolve, brentq, root_scalar
import numpy as np

# f(x) = 0 의 근 찾기
def f(x):
    return x**3 - 6*x**2 + 11*x - 6  # 근: 1, 2, 3

# fsolve: 초기값에서 시작하여 근 탐색
root1 = fsolve(f, x0=0.5)
root2 = fsolve(f, x0=1.5)
root3 = fsolve(f, x0=3.5)
print(f"근 1: {root1[0]:.4f}")
print(f"근 2: {root2[0]:.4f}")
print(f"근 3: {root3[0]:.4f}")

# brentq: 구간 내 근 탐색 (부호 변화 필요)
root = brentq(f, 0.5, 1.5)  # [0.5, 1.5] 구간에서 탐색
print(f"brentq 근: {root:.4f}")

# root_scalar: 통합 인터페이스
result = root_scalar(f, bracket=[0.5, 1.5], method='brentq')
print(f"root_scalar: {result.root:.4f}, 반복: {result.iterations}")

# 연립방정식의 근
def equations(vars):
    x, y = vars
    eq1 = x**2 + y**2 - 25     # x² + y² = 25
    eq2 = x * y - 12            # xy = 12
    return [eq1, eq2]

solution = fsolve(equations, x0=[3, 4])
print(f"연립방정식 해: x={solution[0]:.4f}, y={solution[1]:.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: scipy.optimize 핵심 함수 시그니처 정리
print("=== 주요 함수 정리 ===")
# 일반 최적화 인터페이스
print("minimize(fun, x0, method, bounds, constraints)")
# 비선형 최소제곱 피팅
print("curve_fit(f, xdata, ydata, p0) -> (popt, pcov)")
# 근 찾기 함수들
print("fsolve(func, x0) / brentq(f, a, b) / root_scalar(f, bracket)")
# minimize의 주요 method 종류
print("방법: Nelder-Mead, BFGS, L-BFGS-B, SLSQP, Powell")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== minimize: 함수 최솟값 찾기 ===

from scipy.optimize import minimize
import numpy as np

# 1차원 함수 최소화
def f(x):
    return (x - 3) ** 2 + 5

result = minimize(f, x0=0)  # 초기값 x0=0에서 시작
print(f"최솟값 위치: {result.x[0]:.4f}")  # ≈ 3.0
print(f"최솟값: {result.fun:.4f}")         # ≈ 5.0
print(f"수렴 성공: {result.success}")

# 다변수 함수 최소화
def rosenbrock(x):
    # Rosenbrock 함수: 최적화 벤치마크
    return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

result = minimize(rosenbrock, x0=[0, 0], method='BFGS')
print(f"최솟값 위치: x={result.x[0]:.4f}, y={result.x[1]:.4f}")  # ≈ (1, 1)
print(f"최솟값: {result.fun:.8f}")  # ≈ 0
print(f"반복 횟수: {result.nit}")


=== 다양한 최적화 방법 ===

from scipy.optimize import minimize
import numpy as np

def objective(x):
    return x[0]**2 + x[1]**2 + x[0]*x[1]

x0 = [5, 5]

# Nelder-Mead: 기울기 불필요, 로버스트
res1 = minimize(objective, x0, method='Nelder-Mead')
print(f"Nelder-Mead: {res1.x}, f={res1.fun:.6f}")

# BFGS: 기울기 기반, 빠름
res2 = minimize(objective, x0, method='BFGS')
print(f"BFGS: {res2.x}, f={res2.fun:.6f}")

# L-BFGS-B: 경계 조건 지원
res3 = minimize(objective, x0, method='L-BFGS-B',
                bounds=[(0, None), (0, None)])  # x >= 0, y >= 0
print(f"L-BFGS-B (bounded): {res3.x}, f={res3.fun:.6f}")

# 제약 조건 최적화
constraints = [
    {'type': 'eq', 'fun': lambda x: x[0] + x[1] - 10},   # x + y = 10
    {'type': 'ineq', 'fun': lambda x: x[0] - 2}           # x >= 2
]
res4 = minimize(objective, x0, method='SLSQP', constraints=constraints)
print(f"제약 조건: {res4.x}, f={res4.fun:.4f}")


=== curve_fit: 데이터 피팅 ===

from scipy.optimize import curve_fit
import numpy as np

# 모델 함수 정의
def linear(x, a, b):
    return a * x + b

def exponential(x, a, b, c):
    return a * np.exp(b * x) + c

def gaussian(x, amp, mu, sigma):
    return amp * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))

# 데이터 생성 (노이즈 포함)
np.random.seed(42)
x_data = np.linspace(0, 10, 50)
y_data = 2.5 * x_data + 1.3 + np.random.normal(0, 1, 50)

# 선형 피팅
popt, pcov = curve_fit(linear, x_data, y_data)
print(f"선형 피팅: y = {popt[0]:.3f}x + {popt[1]:.3f}")
print(f"표준 오차: a±{np.sqrt(pcov[0,0]):.3f}, b±{np.sqrt(pcov[1,1]):.3f}")

# 가우시안 피팅
x_gauss = np.linspace(-5, 5, 100)
y_gauss = 3 * np.exp(-((x_gauss - 1) ** 2) / 2) + np.random.normal(0, 0.1, 100)
popt, pcov = curve_fit(gaussian, x_gauss, y_gauss, p0=[3, 1, 1])
print(f"가우시안: amp={popt[0]:.3f}, mu={popt[1]:.3f}, sigma={popt[2]:.3f}")


=== 근 찾기 (Root Finding) ===

from scipy.optimize import fsolve, brentq, root_scalar
import numpy as np

# f(x) = 0 의 근 찾기
def f(x):
    return x**3 - 6*x**2 + 11*x - 6  # 근: 1, 2, 3

# fsolve: 초기값에서 시작하여 근 탐색
root1 = fsolve(f, x0=0.5)
root2 = fsolve(f, x0=1.5)
root3 = fsolve(f, x0=3.5)
print(f"근 1: {root1[0]:.4f}")
print(f"근 2: {root2[0]:.4f}")
print(f"근 3: {root3[0]:.4f}")

# brentq: 구간 내 근 탐색 (부호 변화 필요)
root = brentq(f, 0.5, 1.5)  # [0.5, 1.5] 구간에서 탐색
print(f"brentq 근: {root:.4f}")

# root_scalar: 통합 인터페이스
result = root_scalar(f, bracket=[0.5, 1.5], method='brentq')
print(f"root_scalar: {result.root:.4f}, 반복: {result.iterations}")

# 연립방정식의 근
def equations(vars):
    x, y = vars
    eq1 = x**2 + y**2 - 25     # x² + y² = 25
    eq2 = x * y - 12            # xy = 12
    return [eq1, eq2]

solution = fsolve(equations, x0=[3, 4])
print(f"연립방정식 해: x={solution[0]:.4f}, y={solution[1]:.4f}")


=== 주요 함수 정리 ===
minimize(fun, x0, method, bounds, constraints)
curve_fit(f, xdata, ydata, p0) -> (popt, pcov)
fsolve(func, x0) / brentq(f, a, b) / root_scalar(f, bracket)
방법: Nelder-Mead, BFGS, L-BFGS-B, SLSQP, Powell
````

**풀이 요점**
- 스크립트는 예제 코드를 세 따옴표 문자열로 감싸 찍는다 — 안의 코드는 실행되지 않으므로 계산값은 나오지 않는다.
- `minimize` 는 결과 객체를 돌려주고, `.x` 가 배열이라 1차원이어도 `[0]` 으로 꺼낸다.
- method 는 문제 꼴에 맞춘다: 범위는 `L-BFGS-B` + `bounds`, 등식 · 부등식은 `SLSQP` + `constraints`(`'ineq'` 는 `fun >= 0`).
- `curve_fit` 은 `(popt, pcov)` 를 돌려주며, 봉우리 모양 모델에는 `p0` 를 챙긴다.
- 근 찾기는 출발점 방식(`fsolve`, 배열 반환)과 구간 방식(`brentq` · `root_scalar`, 부호 변화 필요)으로 나뉜다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
