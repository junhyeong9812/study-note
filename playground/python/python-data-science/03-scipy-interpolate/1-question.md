# python/python-data-science/03 — SciPy 보간법 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `y = x²` 점 다섯 개를 직선으로 이으면 (예측)

```python
# 질문용 발췌
x = np.array([0, 1, 2, 3, 4])
y = np.array([0, 1, 4, 9, 16])
f_linear = interp1d(x, y, kind='linear')
print(f"{f_linear(1.5):.4f}")
print(f"{f_linear(2.5):.4f}")
```

- 두 줄에 찍힐 값은 각각 얼마인가?

### 2. 같은 점에서 선형 보간과 3차 보간의 값이 다른 까닭 (왜)

- 위 데이터에서 3차 보간 f(1.5) 는 선형 보간보다 참값 1.5² 에 가까운데, 선형 보간이 참값에서 어느 쪽으로 왜 벗어나는가?

### 3. 기본 `interp1d` 에 데이터 범위 밖의 x 를 넣으면 (경계)

- x 범위가 0~4 인 기본 설정 `interp1d` 함수에 5.0 을 넣으면 어떻게 되는가?
- 그것을 피하는 두 옵션은 무엇이고, 각각 무엇을 돌려주는가?

### 4. 자연 스플라인의 양 끝 휘어짐 (예측)

```python
# 질문용 발췌
x = np.array([0, 1, 2, 3, 4, 5])
y = np.array([0, 0.8, 0.9, 0.1, -0.8, -1.0])
cs = CubicSpline(x, y, bc_type='natural')
print(f"{cs(0.0, 2):.4f}")
print(f"{cs(5.0, 2):.4f}")
```

- 두 줄에 찍힐 값은 각각 얼마인가?

### 5. 노이즈가 섞인 데이터에 `s=0` 을 피하는 까닭 (왜)

- `UnivariateSpline` 에서 `s=0` 으로 두면 곡선이 무엇을 따라가게 되고, 그것이 왜 문제인가?

### 6. `griddata` 결과에서 `NaN` 이 생기는 자리 (경계)

- 흩어진 점 100개를 50×50 격자로 보간할 때, `nearest` 와 `linear` 중 어느 쪽 결과에 `NaN` 이 생기며 어디에 생기는가?

### 7. 바둑판 위 값이 `x + y` 일 때 (예측)

```python
# 질문용 발췌
x = np.linspace(0, 4, 5)
y = np.linspace(0, 4, 5)
data = np.array([[i + j for j in range(5)] for i in range(5)], dtype=float)
interp = RegularGridInterpolator((x, y), data, method='linear')
print(interp([[1.5, 1.5], [2.5, 3.5]]))
```

- 찍히는 배열의 두 값은 무엇인가?

### 8. 미분 · 적분이 필요할 때 `CubicSpline` 을 고르는 까닭 (연결)

- 미적분에서 「함수의 기울기 · 넓이 · 0이 되는 자리」에 해당하는 것을 `CubicSpline` 은 각각 어떤 호출로 주는가?

### 9. 2D 데이터에서 두 도구를 가르는 기준 (연결)

- 2D 데이터를 보간할 때 `griddata` 와 `RegularGridInterpolator` 중 하나를 고르는 기준은 데이터의 어떤 성질인가?

## 실습

### 실습 1. 보간법 다섯 갈래를 보여 주는 안내 스크립트

**만들 것** — 보간 도구 네 가지의 사용 예를 섹션별로 화면에 보여 주고, 마지막에 상황별 선택 가이드를 찍는 파이썬 스크립트를 만든다.
각 섹션의 사용 예는 계산하지 않고 여러 줄 문자열로 출력한다.

**준비물** — 스크립트 자체는 표준 파이썬만으로 돈다. 문자열 안의 예제 코드를 따로 돌려 보려면 `pip install scipy numpy` 가 필요하다.

**요구 조건**

1단계 — 섹션 틀
1. 섹션은 차례대로 `interp1d` · `CubicSpline` · `UnivariateSpline` · 다차원 보간 · 선택 가이드의 다섯 개다.
2. 각 섹션은 `=== … ===` 꼴 제목 한 줄로 시작하고, 섹션 사이에는 빈 줄을 하나 찍는다.
3. 앞의 네 섹션은 제목 다음에 사용 예 코드를 `print("""…""")` 로 통째로 찍는다.

2단계 — `interp1d` 섹션의 사용 예
4. `y = x²` 인 점 다섯 개(x 0~4)로 선형 보간 함수와 3차 보간 함수를 만들어 1.5 와 2.5 에서 값을 찍는다.
5. `kind` 의 다섯 값(`linear` · `nearest` · `zero` · `quadratic` · `cubic`)을 주석으로 적는다.
6. `np.linspace` 로 만든 20개 점을 한 번에 3차 보간해 처음 5개를 찍는다.
7. `fill_value='extrapolate'` 로 외삽 함수를 만들어 5.0 에서 값을 찍는다.

3단계 — `CubicSpline` 섹션의 사용 예
8. 점 여섯 개로 `bc_type='natural'` 스플라인을 만들고 0.5 와 2.5 에서 값을 찍는다.
9. x=1 에서 1차 · 2차 미분값을 찍는다.
10. 0~5 구간 적분값과 근을 찍는다.
11. `bc_type` 세 가지(`natural` · `clamped` · `not-a-knot`)를 주석으로 적는다.

4단계 — `UnivariateSpline` 섹션의 사용 예
12. 시드를 고정하고 사인 곡선에 노이즈를 더한 30개 점을 만든다.
13. `s=1` 평활 스플라인의 매듭점 수 · 잔차 · π 에서의 값을 찍는다.
14. `s=0` 스플라인의 매듭점 수를 찍는다.

5단계 — 다차원 보간 섹션의 사용 예
15. 무작위 2D 점 100개와 그 값으로 50×50 격자에 `nearest` · `linear` · `cubic` 세 방식의 `griddata` 를 돌리고, `nearest` 결과의 shape 와 나머지 둘의 `NaN` 개수를 찍는다.
16. 5×5 정규 격자(값 `i + j`)에 `RegularGridInterpolator` 를 만들어 두 점에서 보간한 결과를 찍는다.

6단계 — 선택 가이드
17. 「1D 소수 점 · 1D 노이즈 · 2D 산재 · 2D 정규 격자 · 미분/적분 필요」 다섯 상황마다 쓸 도구를 한 줄씩 찍는다.

**시작 코드**

```python
# scipy.interpolate - 보간법
# pip install scipy numpy

print("=== interp1d: 1차원 보간 ===")
print("""
from scipy.interpolate import interp1d
import numpy as np

# 원본 데이터 (5개 점)
x = np.array([0, 1, 2, 3, 4])
y = np.array([0, 1, 4, 9, 16])  # y = x²

# TODO: 선형 보간 함수를 만들고 f(1.5), f(2.5) 를 찍는다
# TODO: 3차 보간 함수를 만들고 f(1.5), f(2.5) 를 찍는다
# TODO: kind 다섯 가지를 주석으로 적는다
# TODO: 20개 점을 한 번에 평가해 처음 5개를 찍는다
# TODO: 외삽을 허용한 함수로 f(5.0) 을 찍는다
""")

print()
print("=== CubicSpline: 3차 스플라인 ===")
print("""
from scipy.interpolate import CubicSpline
import numpy as np

x = np.array([0, 1, 2, 3, 4, 5])
y = np.array([0, 0.8, 0.9, 0.1, -0.8, -1.0])

# TODO: 자연 스플라인을 만들고 f(0.5), f(2.5) 를 찍는다
# TODO: x=1 에서 1차 · 2차 미분을 찍는다
# TODO: 0~5 적분과 근을 찍는다
# TODO: 경계 조건 세 가지를 주석으로 적는다
""")

print()
print("=== UnivariateSpline: 평활 스플라인 ===")
print("""
from scipy.interpolate import UnivariateSpline
import numpy as np

# 노이즈가 있는 데이터
np.random.seed(42)
x = np.linspace(0, 2*np.pi, 30)
y = np.sin(x) + np.random.normal(0, 0.2, 30)

# TODO: s=1 평활 스플라인 — 매듭점 수, 잔차, f(π)
# TODO: s=0 스플라인 — 매듭점 수
""")

print()
print("=== 다차원 보간 ===")
print("""
from scipy.interpolate import griddata, RegularGridInterpolator
import numpy as np

np.random.seed(42)
points = np.random.rand(100, 2)  # 100개 랜덤 (x,y) 좌표
values = np.sin(points[:, 0] * np.pi) * np.cos(points[:, 1] * np.pi)

# TODO: 50×50 격자를 만들고 nearest / linear / cubic 세 방식으로 griddata
# TODO: nearest shape, linear · cubic 의 NaN 개수를 찍는다

x = np.linspace(0, 4, 5)
y = np.linspace(0, 4, 5)
data = np.array([[i + j for j in range(5)] for i in range(5)], dtype=float)

# TODO: RegularGridInterpolator 를 만들어 [[1.5, 1.5], [2.5, 3.5]] 를 보간해 찍는다
""")

print()
print("=== 보간법 선택 가이드 ===")
# TODO: 다섯 상황마다 쓸 도구를 한 줄씩 찍는다
```

**확인 방법** — `python scipy-interpolate.py` 로 돌려 섹션 제목 다섯 개, 네 섹션의 예제 코드, 마지막 가이드 다섯 줄이 차례대로 나오는지 본다.
예제 코드의 계산 결과를 보려면 각 문자열 안의 코드를 따로 파일에 옮겨 돌린다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
