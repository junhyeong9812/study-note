# python/python-data-science/03 — SciPy 보간법 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 2.5000 과 6.5000 — 구간 양 끝의 평균

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
2.5000
6.5000
```

**왜 그런가**
1.5 는 구간 [1, 2] 의 정중앙이고, 양 끝 y 는 1 과 4 다.
직선으로 이으면 정중앙 값은 (1 + 4) / 2 = 2.5 다.
2.5 는 구간 [2, 3] 의 정중앙이고, 양 끝 y 는 4 와 9 라서 (4 + 9) / 2 = 6.5 다.
`:.4f` 로 소수 넷째 자리까지 찍는다.
원본 주석도 `# 2.5` · `# 6.5` 로 적는다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 선형 보간은 참값보다 크게 나온다 — 볼록한 곡선을 현으로 자르기 때문이다

`y = x²` 는 아래로 볼록한 곡선이다.
선형 보간은 두 점을 잇는 직선(현) 위의 값을 쓰는데, 볼록한 곡선에서는 현이 곡선보다 위에 있다.
그래서 선형 f(1.5) = 2.5 는 참값 2.25 보다 크다.
3차 보간은 곡선 조각으로 이어 휘어짐을 따라가므로, 원본 주석대로 약 2.25 로 참값에 가깝다.
근거: 2-summary 「동작 방식 (1)」.

### 3. 기본은 에러 — `bounds_error=False` 는 `NaN`, `fill_value='extrapolate'` 는 외삽값

- 기본 설정에서는 범위 밖 값이라 에러가 난다.
- `bounds_error=False` 를 주면 에러 대신 `NaN` 을 돌려준다.
- `fill_value='extrapolate'` 를 주면 마지막 곡선 조각을 연장한 외삽값을 돌려준다.

근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 4. 둘 다 0 — 자연 스플라인의 경계 조건

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
0.0000
0.0000
```

**왜 그런가**
`bc_type='natural'` 은 양 끝에서 f'' = 0 이라는 경계 조건이다.
`cs(x, 2)` 는 x 에서의 2차 미분값이다.
x=0 과 x=5 는 데이터의 양 끝이므로 두 값 모두 0 이다.
부동소수 계산이라 아주 작은 수가 `-0.0000` 처럼 찍힐 가능성은 있다(원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (3)」의 `bc_type` 표.

### 5. 노이즈까지 따라가 과적합이 된다

`s=0` 이면 스플라인이 모든 점을 정확히 지난다.
점마다 노이즈가 섞여 있으면 곡선이 그 흔들림까지 따라가 지그재그가 된다.
그러면 본래 경향(원본 예에서는 사인 곡선)을 놓친다 — 과적합이다.
`s>0` 이면 오차를 허용해 부드러운 곡선을 고르고, 원본 예처럼 `s=0` 일 때보다 매듭점도 적다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 6. `linear` 쪽, 점들의 볼록 껍질 바깥 격자칸

- `nearest` 는 어디서나 가장 가까운 점의 값을 쓰므로 `NaN` 이 없다.
- `linear`(와 `cubic`)은 흩어진 점들이 둘러싼 영역(볼록 껍질) 안에서만 값을 낸다.
- 0~1 격자의 가장자리 · 모서리처럼 무작위 점들이 감싸지 못한 바깥 칸이 `NaN` 이 된다.

근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 7. `[3. 6.]` — 1차식은 선형 보간이 그대로 되살린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[3. 6.]
```

**왜 그런가**
`x` 와 `y` 는 0, 1, 2, 3, 4 이므로 격자점 (x, y) 의 값 `data[i][j] = i + j` 는 곧 x + y 다.
격자 값이 x, y 에 대한 1차식이면 선형 보간은 그 식을 그대로 되살린다.
(1.5, 1.5) → 1.5 + 1.5 = 3.0, (2.5, 3.5) → 2.5 + 3.5 = 6.0 이다.
NumPy 배열 출력 꼴이 `[3. 6.]` 이라는 것은 추론이다(원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (6)」.

### 8. 기울기는 `cs(x, 1)`, 넓이는 `cs.integrate(a, b)`, 0 이 되는 자리는 `cs.roots()`

- 기울기(1차 미분) → `cs(x, 1)`. 휘는 정도(2차 미분)는 `cs(x, 2)`.
- 넓이(정적분) → `cs.integrate(a, b)`.
- 0 이 되는 자리(근) → `cs.roots()` 가 배열로 준다.

`interp1d` 는 값만 주므로, 이 셋이 필요하면 `CubicSpline` 이 가장 다목적이다.
근거: 2-summary 「동작 방식 (3)」 · 「언제 쓰고 언제 안 쓰나」.

### 9. 점이 바둑판(정규 격자)에 놓였는가, 흩어져 있는가

- 점이 규칙 없이 흩어진 산재 데이터 → `griddata`.
- 축마다 정해진 자리에 늘어선 정규 격자 데이터 → `RegularGridInterpolator`.

`RegularGridInterpolator` 는 격자 축(`x`, `y`)과 격자 값 배열을 받으므로, 흩어진 점에는 넘길 축 자체가 없다.
근거: 2-summary 「동작 방식 (5)·(6)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 보간법 다섯 갈래를 보여 주는 안내 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 섹션 다섯 개의 차례 | `=== interp1d …` · `=== CubicSpline …` · `=== UnivariateSpline …` · `=== 다차원 보간 ===` · `=== 보간법 선택 가이드 ===` 제목 `print` |
| 2. 제목 줄 · 섹션 사이 빈 줄 | 섹션마다 `print("=== … ===")`, 섹션 사이 `print()` |
| 3. 예제 코드를 문자열로 통째로 찍기 | 네 섹션의 `print("""…""")` |
| 4. 선형 · 3차 보간과 1.5 · 2.5 값 | `f_linear = interp1d(x, y, kind='linear')` · `f_cubic = interp1d(x, y, kind='cubic')` 와 그 `print` |
| 5. `kind` 다섯 값 주석 | `# 'linear' - 선형 (기본값)` … `# 'cubic' - 3차` |
| 6. 20개 점 한 번에 평가 | `x_new = np.linspace(0, 4, 20)` · `y_new[:5].round(3)` |
| 7. 외삽 함수와 f(5.0) | `f_extrap = interp1d(..., fill_value='extrapolate')` · `f_extrap(5.0)` |
| 8. 자연 스플라인과 0.5 · 2.5 값 | `cs = CubicSpline(x, y, bc_type='natural')` · `cs(0.5)` · `cs(2.5)` |
| 9. x=1 에서 1차 · 2차 미분 | `dy = cs(1.0, 1)` · `d2y = cs(1.0, 2)` |
| 10. 적분과 근 | `cs.integrate(0, 5)` · `cs.roots()` |
| 11. `bc_type` 세 가지 주석 | `# 'natural'` · `# 'clamped'` · `# 'not-a-knot'` |
| 12. 시드 고정 · 노이즈 사인 30점 | `np.random.seed(42)` · `np.sin(x) + np.random.normal(0, 0.2, 30)` |
| 13. `s=1` 매듭점 · 잔차 · f(π) | `spline = UnivariateSpline(x, y, s=1)` · `get_knots()` · `get_residual()` · `spline(np.pi)` |
| 14. `s=0` 매듭점 수 | `spline_exact = UnivariateSpline(x, y, s=0)` |
| 15. `griddata` 세 방식과 shape · NaN 개수 | `np.mgrid[0:1:50j, 0:1:50j]` · `z_nearest` · `z_linear` · `z_cubic` · `np.isnan(...).sum()` |
| 16. 정규 격자 보간 두 점 | `interp = RegularGridInterpolator((x, y), data, method='linear')` · `interp([[1.5, 1.5], [2.5, 3.5]])` |
| 17. 선택 가이드 다섯 줄 | `print("1D 소수 점: …")` … `print("미분/적분 필요: …")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/scipy-interpolate.py`

```python
# [데이터 과학 & 수학] SciPy 보간법
# 설명: 보간법, interp1d, 스플라인, 다차원 보간 (scipy.interpolate)
# 팁: interp1d는 범위 밖 값에서 에러가 발생한다. fill_value='extrapolate'로 외삽을 허용하거나, bounds_error=False로 NaN을 반환할 수 있다. CubicSpline은 미분, 적분, 근 찾기까지 지원하여 가장 다목적이다.

# scipy.interpolate - 보간법
# pip install scipy numpy

# 섹션 제목: 1차원 보간 함수 interp1d
print("=== interp1d: 1차원 보간 ===")
# linear, cubic 등 다양한 kind 지원, 범위 밖 처리 옵션 포함
print("""
from scipy.interpolate import interp1d
import numpy as np

# 원본 데이터 (5개 점)
x = np.array([0, 1, 2, 3, 4])
y = np.array([0, 1, 4, 9, 16])  # y = x²

# 선형 보간
f_linear = interp1d(x, y, kind='linear')
print(f"선형 보간 f(1.5): {f_linear(1.5):.4f}")  # 2.5
print(f"선형 보간 f(2.5): {f_linear(2.5):.4f}")  # 6.5

# 3차 보간 (더 부드러운 곡선)
f_cubic = interp1d(x, y, kind='cubic')
print(f"3차 보간 f(1.5): {f_cubic(1.5):.4f}")    # ≈ 2.25
print(f"3차 보간 f(2.5): {f_cubic(2.5):.4f}")    # ≈ 6.25

# 보간 종류
# 'linear'   - 선형 (기본값)
# 'nearest'  - 최근접
# 'zero'     - 0차 (계단)
# 'quadratic' - 2차
# 'cubic'    - 3차

# 여러 점에서 한번에 평가
x_new = np.linspace(0, 4, 20)
y_new = f_cubic(x_new)
print(f"20개 점 보간 결과 (처음 5개): {y_new[:5].round(3)}")

# fill_value: 범위 밖 처리
f_extrap = interp1d(x, y, kind='cubic',
                     fill_value='extrapolate')  # 외삽 허용
print(f"외삽 f(5.0): {f_extrap(5.0):.4f}")  # ≈ 25.0
""")

# 줄바꿈 출력
print()
# 섹션 제목: 3차 스플라인은 미분/적분/근찾기까지 지원
print("=== CubicSpline: 3차 스플라인 ===")
# bc_type으로 경계 조건 설정 (natural/clamped/not-a-knot)
print("""
from scipy.interpolate import CubicSpline
import numpy as np

x = np.array([0, 1, 2, 3, 4, 5])
y = np.array([0, 0.8, 0.9, 0.1, -0.8, -1.0])

# 자연 스플라인 (양 끝 2차 미분 = 0)
cs = CubicSpline(x, y, bc_type='natural')

# 보간값
x_new = np.linspace(0, 5, 100)
y_new = cs(x_new)
print(f"보간 f(0.5): {cs(0.5):.4f}")
print(f"보간 f(2.5): {cs(2.5):.4f}")

# 미분과 적분
dy = cs(1.0, 1)   # 1차 미분 at x=1
d2y = cs(1.0, 2)  # 2차 미분 at x=1
print(f"f'(1.0): {dy:.4f}")
print(f"f''(1.0): {d2y:.4f}")

# 구간 적분
integral = cs.integrate(0, 5)
print(f"∫₀⁵ f(x)dx: {integral:.4f}")

# 근 찾기 (f(x) = 0)
roots = cs.roots()
print(f"근 (f(x)=0): {roots.round(4)}")

# 경계 조건 종류
# 'natural'     - 양 끝 f''=0
# 'clamped'     - 양 끝 f'=0
# 'not-a-knot'  - 기본값, 연속 3차 미분
""")

# 줄바꿈 출력
print()
# 섹션 제목: 노이즈 데이터에 적합한 평활 스플라인
print("=== UnivariateSpline: 평활 스플라인 ===")
# s 인자가 클수록 더 부드럽게 (s=0이면 모든 점 통과 → 과적합)
print("""
from scipy.interpolate import UnivariateSpline
import numpy as np

# 노이즈가 있는 데이터
np.random.seed(42)
x = np.linspace(0, 2*np.pi, 30)
y = np.sin(x) + np.random.normal(0, 0.2, 30)

# 평활 스플라인 (s: smoothing factor)
spline = UnivariateSpline(x, y, s=1)  # s가 클수록 부드러움
print(f"매듭점 수: {len(spline.get_knots())}")
print(f"잔차: {spline.get_residual():.4f}")

x_new = np.linspace(0, 2*np.pi, 100)
y_smooth = spline(x_new)
print(f"보간 f(π): {spline(np.pi):.4f}")  # ≈ 0

# s=0이면 모든 점을 정확히 통과 (과적합)
spline_exact = UnivariateSpline(x, y, s=0)
print(f"s=0 매듭점 수: {len(spline_exact.get_knots())}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 2D 이상의 다차원 보간
print("=== 다차원 보간 ===")
# griddata는 산재된 점, RegularGridInterpolator는 정규 격자에 사용
print("""
from scipy.interpolate import griddata, RegularGridInterpolator
import numpy as np

# --- 비정형 격자 보간 (griddata) ---
# 산재된 점에서의 보간
np.random.seed(42)
points = np.random.rand(100, 2)  # 100개 랜덤 (x,y) 좌표
values = np.sin(points[:, 0] * np.pi) * np.cos(points[:, 1] * np.pi)

# 새로운 정규 격자에서 보간
grid_x, grid_y = np.mgrid[0:1:50j, 0:1:50j]

# 보간 방법
z_nearest = griddata(points, values, (grid_x, grid_y), method='nearest')
z_linear = griddata(points, values, (grid_x, grid_y), method='linear')
z_cubic = griddata(points, values, (grid_x, grid_y), method='cubic')
print(f"nearest 결과 shape: {z_nearest.shape}")
print(f"linear NaN 개수: {np.isnan(z_linear).sum()}")
print(f"cubic NaN 개수: {np.isnan(z_cubic).sum()}")

# --- 정규 격자 보간 (RegularGridInterpolator) ---
x = np.linspace(0, 4, 5)
y = np.linspace(0, 4, 5)
data = np.array([[i + j for j in range(5)] for i in range(5)], dtype=float)

interp = RegularGridInterpolator((x, y), data, method='linear')
result = interp([[1.5, 1.5], [2.5, 3.5]])
print(f"정규격자 보간: {result}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 데이터 형태별 보간법 선택 가이드
print("=== 보간법 선택 가이드 ===")
# 1D 정확한 데이터 - cubic 권장
print("1D 소수 점: interp1d(kind='cubic') 또는 CubicSpline")
# 노이즈가 있는 1D 데이터 - 평활 스플라인
print("1D 노이즈 데이터: UnivariateSpline(s>0)")
# 2D 산재 데이터 - griddata
print("2D 산재 데이터: griddata()")
# 2D 정규 격자 - RegularGridInterpolator
print("2D 정규 격자: RegularGridInterpolator()")
# 미분/적분 기능까지 필요할 때
print("미분/적분 필요: CubicSpline (roots, integrate 지원)")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== interp1d: 1차원 보간 ===

from scipy.interpolate import interp1d
import numpy as np

# 원본 데이터 (5개 점)
x = np.array([0, 1, 2, 3, 4])
y = np.array([0, 1, 4, 9, 16])  # y = x²

# 선형 보간
f_linear = interp1d(x, y, kind='linear')
print(f"선형 보간 f(1.5): {f_linear(1.5):.4f}")  # 2.5
print(f"선형 보간 f(2.5): {f_linear(2.5):.4f}")  # 6.5

# 3차 보간 (더 부드러운 곡선)
f_cubic = interp1d(x, y, kind='cubic')
print(f"3차 보간 f(1.5): {f_cubic(1.5):.4f}")    # ≈ 2.25
print(f"3차 보간 f(2.5): {f_cubic(2.5):.4f}")    # ≈ 6.25

# 보간 종류
# 'linear'   - 선형 (기본값)
# 'nearest'  - 최근접
# 'zero'     - 0차 (계단)
# 'quadratic' - 2차
# 'cubic'    - 3차

# 여러 점에서 한번에 평가
x_new = np.linspace(0, 4, 20)
y_new = f_cubic(x_new)
print(f"20개 점 보간 결과 (처음 5개): {y_new[:5].round(3)}")

# fill_value: 범위 밖 처리
f_extrap = interp1d(x, y, kind='cubic',
                     fill_value='extrapolate')  # 외삽 허용
print(f"외삽 f(5.0): {f_extrap(5.0):.4f}")  # ≈ 25.0


=== CubicSpline: 3차 스플라인 ===

from scipy.interpolate import CubicSpline
import numpy as np

x = np.array([0, 1, 2, 3, 4, 5])
y = np.array([0, 0.8, 0.9, 0.1, -0.8, -1.0])

# 자연 스플라인 (양 끝 2차 미분 = 0)
cs = CubicSpline(x, y, bc_type='natural')

# 보간값
x_new = np.linspace(0, 5, 100)
y_new = cs(x_new)
print(f"보간 f(0.5): {cs(0.5):.4f}")
print(f"보간 f(2.5): {cs(2.5):.4f}")

# 미분과 적분
dy = cs(1.0, 1)   # 1차 미분 at x=1
d2y = cs(1.0, 2)  # 2차 미분 at x=1
print(f"f'(1.0): {dy:.4f}")
print(f"f''(1.0): {d2y:.4f}")

# 구간 적분
integral = cs.integrate(0, 5)
print(f"∫₀⁵ f(x)dx: {integral:.4f}")

# 근 찾기 (f(x) = 0)
roots = cs.roots()
print(f"근 (f(x)=0): {roots.round(4)}")

# 경계 조건 종류
# 'natural'     - 양 끝 f''=0
# 'clamped'     - 양 끝 f'=0
# 'not-a-knot'  - 기본값, 연속 3차 미분


=== UnivariateSpline: 평활 스플라인 ===

from scipy.interpolate import UnivariateSpline
import numpy as np

# 노이즈가 있는 데이터
np.random.seed(42)
x = np.linspace(0, 2*np.pi, 30)
y = np.sin(x) + np.random.normal(0, 0.2, 30)

# 평활 스플라인 (s: smoothing factor)
spline = UnivariateSpline(x, y, s=1)  # s가 클수록 부드러움
print(f"매듭점 수: {len(spline.get_knots())}")
print(f"잔차: {spline.get_residual():.4f}")

x_new = np.linspace(0, 2*np.pi, 100)
y_smooth = spline(x_new)
print(f"보간 f(π): {spline(np.pi):.4f}")  # ≈ 0

# s=0이면 모든 점을 정확히 통과 (과적합)
spline_exact = UnivariateSpline(x, y, s=0)
print(f"s=0 매듭점 수: {len(spline_exact.get_knots())}")


=== 다차원 보간 ===

from scipy.interpolate import griddata, RegularGridInterpolator
import numpy as np

# --- 비정형 격자 보간 (griddata) ---
# 산재된 점에서의 보간
np.random.seed(42)
points = np.random.rand(100, 2)  # 100개 랜덤 (x,y) 좌표
values = np.sin(points[:, 0] * np.pi) * np.cos(points[:, 1] * np.pi)

# 새로운 정규 격자에서 보간
grid_x, grid_y = np.mgrid[0:1:50j, 0:1:50j]

# 보간 방법
z_nearest = griddata(points, values, (grid_x, grid_y), method='nearest')
z_linear = griddata(points, values, (grid_x, grid_y), method='linear')
z_cubic = griddata(points, values, (grid_x, grid_y), method='cubic')
print(f"nearest 결과 shape: {z_nearest.shape}")
print(f"linear NaN 개수: {np.isnan(z_linear).sum()}")
print(f"cubic NaN 개수: {np.isnan(z_cubic).sum()}")

# --- 정규 격자 보간 (RegularGridInterpolator) ---
x = np.linspace(0, 4, 5)
y = np.linspace(0, 4, 5)
data = np.array([[i + j for j in range(5)] for i in range(5)], dtype=float)

interp = RegularGridInterpolator((x, y), data, method='linear')
result = interp([[1.5, 1.5], [2.5, 3.5]])
print(f"정규격자 보간: {result}")


=== 보간법 선택 가이드 ===
1D 소수 점: interp1d(kind='cubic') 또는 CubicSpline
1D 노이즈 데이터: UnivariateSpline(s>0)
2D 산재 데이터: griddata()
2D 정규 격자: RegularGridInterpolator()
미분/적분 필요: CubicSpline (roots, integrate 지원)
````

**풀이 요점**
- 이 스크립트는 예제 코드를 `print("""…""")` 문자열로 보여 줄 뿐 계산하지 않는다 — 출력에는 코드 글자가 그대로 나오고, 주석 속 숫자는 계산 결과가 아니다.
- 실제로 계산되어 나오는 것은 제목 줄과 마지막 가이드 다섯 줄뿐이다.
- 보간 도구는 「점 배치(1D · 2D 산재 · 2D 격자)」와 「노이즈 여부」 · 「미적분 필요 여부」로 고른다 — 가이드 다섯 줄이 그 기준을 그대로 담는다.
- `interp1d` 는 범위 밖이 기본 에러이므로 외삽 예에서 `fill_value='extrapolate'` 를 꼭 넣는다.
- `UnivariateSpline` 섹션은 `s=1` 과 `s=0` 을 나란히 두어 매듭점 수의 차이로 평활과 과적합을 비교한다.
- `griddata` 섹션은 `nearest` 의 shape 와 `linear` · `cubic` 의 `NaN` 개수를 찍어, 볼록 껍질 밖 처리의 차이를 드러낸다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
