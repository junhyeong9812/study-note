# python/python-data-science/04 — SymPy 심볼릭 연산 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 계산 결과가 아니라 코드 글자가 그대로 찍힌다

**출력**

```text
=== 방정식 풀기 (solve) ===

from sympy import symbols, solve, Eq

x, y = symbols('x y')

# 다항식
solutions = solve(x**2 - 5*x + 6, x)
print(f"x² - 5x + 6 = 0: {solutions}")  # [2, 3]
```

**왜 그런가**
두 번째 `print` 에 넘긴 것은 세 따옴표로 감싼 일반 문자열이다.
그 안의 `solve(...)` 는 호출이 아니라 글자일 뿐이고, 바깥에 `f` 접두사가 없으니 `{solutions}` 도 계산되지 않고 중괄호째 찍힌다.
`[2, 3]` 은 주석 글자로만 나타난다.
문자열이 줄바꿈으로 시작하므로 제목 바로 아래 줄은 빈 줄이다.
근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 1」.

### 2. `2*sqrt(2)` 와 `1/2` — 정확한 꼴

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 줄은 `2*sqrt(2)`, 둘째 줄은 `1/2` 을 보여 줄 것이다(원본 주석이 적은 값).

**왜 그런가**
`sqrt(8)` 은 소수로 바꾸지 않고 `8 = 4·2` 에서 `√4 = 2` 를 밖으로 꺼내 정리한다.
`Rational` 은 분자 · 분모를 정수로 들고 있으므로 통분하면 `2/6 + 1/6 = 3/6 = 1/2` 이 정확히 나온다.
찍히는 글자 꼴은 SymPy 버전에 따를 수 있다.
근거: 2-summary 「동작 방식 (2)」 · 「구현 세부사항 대 언어 보장」.

### 3. `2*x*y + y**3` 꼴과 `2*y` 꼴

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 줄은 `2xy + y³` 에 해당하는 식, 둘째 줄은 `2y` 에 해당하는 식이 나올 것이다(원본 주석: `2xy + y³` · `2y`). 항의 차례 · 찍히는 꼴은 확인하지 않았다.

**왜 그런가**
`x` 로 미분할 때 `y` 는 상수다 — `x²y → 2xy`, `xy³ → y³`.
`diff(f, x, y)` 는 `x` 로 먼저 미분한 `2xy + y³` 을 이어서 `y` 로 미분한다 — `2xy → 2x`, `y³ → 3y²`… 가 아니라, 원본 주석은 `2y` 라 적는다.

여기서 손계산을 다시 하면 `∂/∂y (2xy + y³) = 2x + 3y²` 이다.
원본 주석 `# 2y` 는 이 손계산과 맞지 않는다.
원본의 주장 → `∂²f/∂x∂y` 는 `2y`.
왜 의심스러운가 → `f = x²y + xy³` 을 `x` 로, 이어서 `y` 로 미분하면 `2x + 3y²` 가 된다(원본에 근거 없음 — 추론).
따라서 둘째 줄의 예상은 원본 주석이 아니라 손계산에 따라 `2x + 3y²` 꼴로 본다.
근거: 2-summary 「동작 방식 (5)」 — 변수를 늘어놓으면 앞에서부터 차례로 미분한다.

### 4. 식을 근사하지 않고 정확한 객체로 들고 가기 때문이다

`Rational(1, 3)` 은 1/3 을 소수로 바꾸지 않고 「분자 1, 분모 3」 그대로 보관한다.
더할 때도 통분 규칙대로 정수만 다루므로 잘림이 생기지 않는다.
파이썬 `float` 는 2진 부동소수점이라 1/3 같은 수를 근사값으로밖에 담지 못한다.
SymPy 는 수치 계산이 아니라 기호 계산 라이브러리라는 것이 핵심이다.
근거: 2-summary 「한눈에」 · 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 5. 이름 충돌을 막고 출처를 드러내기 위해서다

SymPy 는 `sin` · `log` · `pi` · `E` 처럼 흔한 이름을 많이 내놓는다.
`*` 로 모두 끌어오면 다른 모듈의 같은 이름이나 내 변수를 덮어쓰거나 덮어쓰일 수 있다(원본에 근거 없음 — 추론).
골라서 import 하면 각 이름이 어디서 왔는지 코드 맨 위에서 바로 보인다.
근거: 2-summary 「어디서 틀리나 6」 · 「문법」의 규칙.

### 6. `.evalf()` 를 쓰되, 계산의 마지막에 쓴다

기호 결과에 `.evalf()` 를 붙이면 소수 근사값이 된다.
처음부터 `float` 를 섞으면 그 순간 근사값이 끼어들어 정확성이 사라진다.
그러므로 식 변형 · 풀이를 기호로 다 끝낸 뒤 맨 끝에서 한 번만 바꾸는 것이 좋다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」 · 「언제 쓰고 언제 안 쓰나」.

### 7. `simplify(sin(x)**2 + cos(x)**2)` 줄에서 `sin` 을 모른다

첫 섹션의 import 는 `symbols, sqrt, Rational, pi, oo, I` 와 `expand, factor, simplify, collect` 뿐이다.
`sin` · `cos` 는 import 하지 않았으므로 그 줄에서 이름을 찾지 못해 멈춘다(`NameError` — 원본에 근거 없음, 코드를 읽어 추론).
문자열로 찍기만 하는 원본에서는 실행되지 않으니 드러나지 않는다.
근거: 2-summary 「어디서 틀리나 2」.

### 8. 리스트 · 딕셔너리 · 범위 조건

한 변수 다항식은 근을 늘어놓은 리스트(원본 주석: `[2, 3]`).
연립방정식은 「심볼 → 값」 딕셔너리(원본 주석: `{x: 2, y: 1}`).
부등식은 낱개 값이 아니라 범위 조건(원본 주석: `-2 < x < 2` — 찍히는 글자 꼴은 확인 필요).
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 9. 다시 `x**2` 이 된다 — 적분상수는 빠져 있다

`integrate(x**2, x)` 는 `x**3/3` 이고, 이것을 `x` 로 미분하면 `3x²/3 = x²` 으로 원래 식이 돌아온다.
부정적분은 미분의 역연산이라는 관계를 보인다.
다만 SymPy 의 부정적분 결과에는 적분상수 `+C` 가 붙지 않는다(원본 주석 `x³/3` 기준).
근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (6)」.

## 실습 정답

### 실습 1. SymPy 사용법을 섹션별로 찍는 안내 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1~3. 여섯 섹션 · `=== 제목 ===` · 문자열 조각 · 빈 줄 | `print("=== … ===")` 여섯 줄 · `print("""…""")` 다섯 개 · `print()` 다섯 개 |
| 4. 심볼 세 종류 | `symbols('x y z')` · `symbols('a b c', real=True)` · `symbols('n', integer=True, positive=True)` |
| 5. 정확한 연산 | `sqrt(8)` · `Rational(1,3) + Rational(1,6)` |
| 6. 전개 · 인수분해 | `expand(expr)` · `factor(x**3 + 3*x**2*y + 3*x*y**2 + y**3)` |
| 7. 단순화 · 묶기 | `simplify(sin(x)**2 + cos(x)**2)` · `collect(x**2*y + x*y + x**2 + x, x)` |
| 8~11. 방정식 | `solve(x**2 - 5*x + 6, x)` · `solve([...], [x, y])` · `Eq(x**3 - 1, 0)` · `solve(x**2 - 4 < 0, x)` |
| 12~14. 미분 | `diff(x**3, x)` 등 · `diff(x**4, x, 2)` · `diff(sin(x), x, 3)` · `diff(f, x)` · `diff(f, y)` · `diff(f, x, y)` |
| 15~18. 적분 | `integrate(x**2, x)` 등 · `(x, 0, 1)` · `(x, 0, pi)` · `(x, 0, oo)` · `integrate(x*y, (x, 0, 1), (y, 0, 2))` |
| 19~22. 기타 | `limit(sin(x)/x, x, 0)` · `limit((1+1/n)**n, n, oo)` · `summation(...)` 두 줄 · `M.det()` · `M.inv()` · `M.eigenvals()` · `latex(expr)` |
| 23. 함수 정리 | `print("심볼: …")` ~ `print("출력: …")` 다섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/sympy-basics.py`

```python
# [데이터 과학 & 수학] SymPy 심볼릭 연산
# 설명: 기호 수학, 방정식 풀기, 미분, 적분, 단순화 (sympy)
# 팁: SymPy는 수치 계산이 아닌 기호(심볼릭) 계산 라이브러리다. 부동소수점 오차 없이 정확한 답을 구한다. 수치 결과가 필요하면 .evalf()로 변환한다. from sympy import * 보다 필요한 것만 import하는 것이 좋다.

# SymPy - 심볼릭 수학 라이브러리
# pip install sympy

# 섹션 제목: 심볼 정의와 기호 연산의 기초
print("=== 심볼 정의와 기본 연산 ===")
# symbols로 변수 선언, expand/factor/simplify로 식 변형
print("""
from sympy import symbols, sqrt, Rational, pi, oo, I
from sympy import expand, factor, simplify, collect

# 심볼 정의
x, y, z = symbols('x y z')
a, b, c = symbols('a b c', real=True)  # 실수 제약
n = symbols('n', integer=True, positive=True)  # 양의 정수

# 정확한 연산 (부동소수점 오차 없음)
print(f"sqrt(8): {sqrt(8)}")           # 2*sqrt(2)
print(f"Rational(1,3) + Rational(1,6): {Rational(1,3) + Rational(1,6)}")  # 1/2

# 전개, 인수분해
expr = (x + y) ** 3
print(f"전개: {expand(expr)}")
print(f"인수분해: {factor(x**3 + 3*x**2*y + 3*x*y**2 + y**3)}")

# 단순화
print(f"simplify: {simplify(sin(x)**2 + cos(x)**2)}")  # 1
print(f"collect: {collect(x**2*y + x*y + x**2 + x, x)}")  # x² 기준 정리
""")

# 줄바꿈 출력
print()
# 섹션 제목: solve로 방정식/연립방정식/부등식 풀기
print("=== 방정식 풀기 (solve) ===")
# Eq 객체나 식=0 표현 모두 가능
print("""
from sympy import symbols, solve, Eq

x, y = symbols('x y')

# 다항식
solutions = solve(x**2 - 5*x + 6, x)
print(f"x² - 5x + 6 = 0: {solutions}")  # [2, 3]

# 연립방정식
sol = solve([
    2*x + y - 5,
    x - y - 1
], [x, y])
print(f"연립방정식: {sol}")  # {x: 2, y: 1}

# Eq 객체 사용
eq = Eq(x**3 - 1, 0)
print(f"x³ = 1: {solve(eq, x)}")  # [1, 복소근...]

# 부등식
from sympy import S
result = solve(x**2 - 4 < 0, x)
print(f"x² < 4: {result}")  # -2 < x < 2
""")

# 줄바꿈 출력
print()
# 섹션 제목: 미분 (diff)으로 도함수 계산
print("=== 미분 (diff) ===")
# 고차 미분과 편미분 모두 diff(f, x, n) 또는 diff(f, x, y) 형태로 가능
print("""
from sympy import symbols, diff, sin, cos, exp, log, ln

x = symbols('x')

# 기본 미분
print(f"d/dx(x³): {diff(x**3, x)}")        # 3x²
print(f"d/dx(sin(x)): {diff(sin(x), x)}")   # cos(x)
print(f"d/dx(e^x): {diff(exp(x), x)}")      # e^x
print(f"d/dx(ln(x)): {diff(log(x), x)}")    # 1/x

# 고차 미분
print(f"d²/dx²(x⁴): {diff(x**4, x, 2)}")     # 12x²
print(f"d³/dx³(sin(x)): {diff(sin(x), x, 3)}")  # -cos(x)

# 편미분
x, y = symbols('x y')
f = x**2 * y + x * y**3
print(f"∂f/∂x: {diff(f, x)}")  # 2xy + y³
print(f"∂f/∂y: {diff(f, y)}")  # x² + 3xy²
print(f"∂²f/∂x∂y: {diff(f, x, y)}")  # 2y
""")

# 줄바꿈 출력
print()
# 섹션 제목: 적분 (integrate)으로 부정적분/정적분/이상적분/다중적분
print("=== 적분 (integrate) ===")
# (x, a, b) 튜플로 정적분 구간 지정, oo는 무한대
print("""
from sympy import symbols, integrate, sin, cos, exp, log, oo, pi

x = symbols('x')

# 부정적분
print(f"∫x² dx: {integrate(x**2, x)}")         # x³/3
print(f"∫sin(x) dx: {integrate(sin(x), x)}")    # -cos(x)
print(f"∫1/x dx: {integrate(1/x, x)}")          # log(x)

# 정적분
print(f"∫₀¹ x² dx: {integrate(x**2, (x, 0, 1))}")      # 1/3
print(f"∫₀π sin(x) dx: {integrate(sin(x), (x, 0, pi))}")  # 2

# 이상적분 (무한 구간)
print(f"∫₀∞ e^(-x) dx: {integrate(exp(-x), (x, 0, oo))}")  # 1

# 다중적분
x, y = symbols('x y')
result = integrate(x*y, (x, 0, 1), (y, 0, 2))
print(f"∫₀² ∫₀¹ xy dx dy: {result}")  # 1
""")

# 줄바꿈 출력
print()
# 섹션 제목: 극한, 급수합, 행렬, LaTeX 출력 등 추가 기능
print("=== 기타 유용한 기능 ===")
# limit, summation, Matrix, latex의 활용 예시
print("""
from sympy import symbols, limit, summation, Matrix, latex, pprint
from sympy import sin, oo

x, n = symbols('x n')

# 극한
print(f"lim(sin(x)/x, x→0): {limit(sin(x)/x, x, 0)}")  # 1
print(f"lim((1+1/n)^n, n→∞): {limit((1+1/n)**n, n, oo)}")  # E (자연상수)

# 급수 합
print(f"Σ(1/n², n=1..∞): {summation(1/n**2, (n, 1, oo))}")  # π²/6
print(f"Σ(n, n=1..10): {summation(n, (n, 1, 10))}")  # 55

# 행렬
M = Matrix([[1, 2], [3, 4]])
print(f"행렬식: {M.det()}")      # -2
print(f"역행렬: {M.inv()}")
print(f"고유값: {M.eigenvals()}")

# LaTeX 출력
expr = x**2 / (x + 1)
print(f"LaTeX: {latex(expr)}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: SymPy 핵심 함수 카테고리별 정리
print("=== 주요 함수 정리 ===")
# 심볼 생성
print("심볼: symbols(), Symbol(), var()")
# 식 변형
print("대수: expand(), factor(), simplify(), collect()")
# 방정식 풀기
print("풀기: solve(), solveset(), dsolve() (미분방정식)")
# 미적분 / 극한 / 급수
print("미적분: diff(), integrate(), limit(), summation()")
# 식 출력
print("출력: pprint() (예쁜 출력), latex() (LaTeX 변환)")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 심볼 정의와 기본 연산 ===

from sympy import symbols, sqrt, Rational, pi, oo, I
from sympy import expand, factor, simplify, collect

# 심볼 정의
x, y, z = symbols('x y z')
a, b, c = symbols('a b c', real=True)  # 실수 제약
n = symbols('n', integer=True, positive=True)  # 양의 정수

# 정확한 연산 (부동소수점 오차 없음)
print(f"sqrt(8): {sqrt(8)}")           # 2*sqrt(2)
print(f"Rational(1,3) + Rational(1,6): {Rational(1,3) + Rational(1,6)}")  # 1/2

# 전개, 인수분해
expr = (x + y) ** 3
print(f"전개: {expand(expr)}")
print(f"인수분해: {factor(x**3 + 3*x**2*y + 3*x*y**2 + y**3)}")

# 단순화
print(f"simplify: {simplify(sin(x)**2 + cos(x)**2)}")  # 1
print(f"collect: {collect(x**2*y + x*y + x**2 + x, x)}")  # x² 기준 정리


=== 방정식 풀기 (solve) ===

from sympy import symbols, solve, Eq

x, y = symbols('x y')

# 다항식
solutions = solve(x**2 - 5*x + 6, x)
print(f"x² - 5x + 6 = 0: {solutions}")  # [2, 3]

# 연립방정식
sol = solve([
    2*x + y - 5,
    x - y - 1
], [x, y])
print(f"연립방정식: {sol}")  # {x: 2, y: 1}

# Eq 객체 사용
eq = Eq(x**3 - 1, 0)
print(f"x³ = 1: {solve(eq, x)}")  # [1, 복소근...]

# 부등식
from sympy import S
result = solve(x**2 - 4 < 0, x)
print(f"x² < 4: {result}")  # -2 < x < 2


=== 미분 (diff) ===

from sympy import symbols, diff, sin, cos, exp, log, ln

x = symbols('x')

# 기본 미분
print(f"d/dx(x³): {diff(x**3, x)}")        # 3x²
print(f"d/dx(sin(x)): {diff(sin(x), x)}")   # cos(x)
print(f"d/dx(e^x): {diff(exp(x), x)}")      # e^x
print(f"d/dx(ln(x)): {diff(log(x), x)}")    # 1/x

# 고차 미분
print(f"d²/dx²(x⁴): {diff(x**4, x, 2)}")     # 12x²
print(f"d³/dx³(sin(x)): {diff(sin(x), x, 3)}")  # -cos(x)

# 편미분
x, y = symbols('x y')
f = x**2 * y + x * y**3
print(f"∂f/∂x: {diff(f, x)}")  # 2xy + y³
print(f"∂f/∂y: {diff(f, y)}")  # x² + 3xy²
print(f"∂²f/∂x∂y: {diff(f, x, y)}")  # 2y


=== 적분 (integrate) ===

from sympy import symbols, integrate, sin, cos, exp, log, oo, pi

x = symbols('x')

# 부정적분
print(f"∫x² dx: {integrate(x**2, x)}")         # x³/3
print(f"∫sin(x) dx: {integrate(sin(x), x)}")    # -cos(x)
print(f"∫1/x dx: {integrate(1/x, x)}")          # log(x)

# 정적분
print(f"∫₀¹ x² dx: {integrate(x**2, (x, 0, 1))}")      # 1/3
print(f"∫₀π sin(x) dx: {integrate(sin(x), (x, 0, pi))}")  # 2

# 이상적분 (무한 구간)
print(f"∫₀∞ e^(-x) dx: {integrate(exp(-x), (x, 0, oo))}")  # 1

# 다중적분
x, y = symbols('x y')
result = integrate(x*y, (x, 0, 1), (y, 0, 2))
print(f"∫₀² ∫₀¹ xy dx dy: {result}")  # 1


=== 기타 유용한 기능 ===

from sympy import symbols, limit, summation, Matrix, latex, pprint
from sympy import sin, oo

x, n = symbols('x n')

# 극한
print(f"lim(sin(x)/x, x→0): {limit(sin(x)/x, x, 0)}")  # 1
print(f"lim((1+1/n)^n, n→∞): {limit((1+1/n)**n, n, oo)}")  # E (자연상수)

# 급수 합
print(f"Σ(1/n², n=1..∞): {summation(1/n**2, (n, 1, oo))}")  # π²/6
print(f"Σ(n, n=1..10): {summation(n, (n, 1, 10))}")  # 55

# 행렬
M = Matrix([[1, 2], [3, 4]])
print(f"행렬식: {M.det()}")      # -2
print(f"역행렬: {M.inv()}")
print(f"고유값: {M.eigenvals()}")

# LaTeX 출력
expr = x**2 / (x + 1)
print(f"LaTeX: {latex(expr)}")


=== 주요 함수 정리 ===
심볼: symbols(), Symbol(), var()
대수: expand(), factor(), simplify(), collect()
풀기: solve(), solveset(), dsolve() (미분방정식)
미적분: diff(), integrate(), limit(), summation()
출력: pprint() (예쁜 출력), latex() (LaTeX 변환)
````

**풀이 요점**
- 조각은 세 따옴표 일반 문자열이라 실행되지 않고, 안쪽 f-string 의 `{…}` 도 글자 그대로 찍힌다.
- 문자열이 줄바꿈으로 시작 · 끝나고 뒤에 `print()` 가 오므로 제목 아래 빈 줄 하나, 섹션 사이 빈 줄 둘이 생긴다.
- 구간은 `integrate` · `summation` 모두 `(변수, 시작, 끝)` 튜플이고, `limit` 만 인자를 늘어놓는다.
- 조각 속 주석 값은 원본의 주장이다 — 첫 조각의 `sin` · `cos` 미 import, `collect` 주석, `∂²f/∂x∂y` 주석처럼 그대로 믿으면 안 되는 곳이 있다.
- 조각을 직접 돌려 보려면 SymPy 를 깔고 import 를 보충해야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
