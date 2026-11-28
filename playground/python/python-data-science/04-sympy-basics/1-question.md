# python/python-data-science/04 — SymPy 심볼릭 연산 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 방정식 섹션을 찍는 코드를 돌리면 (예측)

```python
# 질문용 발췌
print("=== 방정식 풀기 (solve) ===")
print("""
from sympy import symbols, solve, Eq

x, y = symbols('x y')

# 다항식
solutions = solve(x**2 - 5*x + 6, x)
print(f"x² - 5x + 6 = 0: {solutions}")  # [2, 3]
""")
```

- 이 코드를 돌리면 화면에 `[2, 3]` 이 계산 결과로 따로 찍히는가, 아니면 무엇이 찍히는가?
- 제목 줄 바로 아래 줄에는 무엇이 오는가?

### 2. 루트와 분수를 SymPy 로 계산하면 (예측)

```python
# 질문용 발췌
from sympy import sqrt, Rational
print(sqrt(8))
print(Rational(1, 3) + Rational(1, 6))
```

- 두 줄은 각각 어떤 꼴의 값을 보여 줄 것인가?

### 3. 같은 식을 x 로, 그리고 x 와 y 로 미분하면 (예측)

```python
# 질문용 발췌
from sympy import symbols, diff
x, y = symbols('x y')
f = x**2 * y + x * y**3
print(diff(f, x))
print(diff(f, x, y))
```

- 두 줄의 결과는 각각 어떤 식인가?

### 4. SymPy 가 부동소수점 오차 없이 답하는 까닭 (왜)

- 같은 `1/3 + 1/6` 인데 SymPy 의 `Rational` 은 정확하고 파이썬 `float` 는 그렇지 않은 까닭은 무엇인가?

### 5. 필요한 이름만 import 하라는 팁 (왜)

- `from sympy import *` 대신 쓸 이름만 골라 import 하는 편이 나은 까닭은 무엇인가?

### 6. 기호 답 대신 소수 값이 필요할 때 (경계)

- `2*sqrt(2)` 같은 기호 답을 소수 근사값으로 보고 싶으면 무엇을 하고, 그 변환은 계산의 어느 시점에 하는 것이 좋은가?

### 7. 첫 섹션의 코드를 문자열 밖으로 꺼내 그대로 돌리면 (경계)

- 원본 첫 섹션의 import 줄을 그대로 두고 문자열 안 코드를 실행하면 어느 줄에서 왜 막히는가?

### 8. solve 가 돌려주는 값의 꼴 (경계)

- 한 변수 다항식 · 연립방정식 · 부등식을 `solve` 에 넘기면 답의 꼴이 각각 어떻게 다른가?

### 9. 부정적분과 미분 (연결)

- `integrate(x**2, x)` 의 결과를 다시 `diff(…, x)` 하면 무엇이 되고, 이것은 미분과 적분의 어떤 관계를 보이며 결과에 빠져 있는 것은 무엇인가?

## 실습

### 실습 1. SymPy 사용법을 섹션별로 찍는 안내 스크립트

**만들 것** — SymPy 의 주요 기능을 여섯 섹션으로 나눠, 섹션마다 제목과 「사용 예 코드 조각」을 화면에 찍는 파이썬 스크립트.
코드 조각은 세 따옴표 문자열로 찍기만 하고 실행하지는 않는다.

**준비물** — 파이썬만 있으면 된다. 코드 조각은 문자열로만 찍으므로 SymPy 설치(`pip install sympy`)는 조각을 직접 실행해 보고 싶을 때만 필요하다.

**요구 조건**

1단계 — 틀
1. 섹션은 「심볼 정의와 기본 연산」 · 「방정식 풀기 (solve)」 · 「미분 (diff)」 · 「적분 (integrate)」 · 「기타 유용한 기능」 · 「주요 함수 정리」 차례로 여섯 개다.
2. 섹션 제목은 `=== 제목 ===` 꼴로 한 줄 찍는다.
3. 앞의 다섯 섹션은 제목 뒤에 세 따옴표 문자열 하나를 `print` 로 찍고, 섹션 사이에는 `print()` 로 빈 줄을 넣는다.

2단계 — 심볼 정의와 기본 연산 조각
4. 심볼 `x, y, z` 를 제약 없이, `a, b, c` 를 실수 제약으로, `n` 을 양의 정수 제약으로 만드는 줄을 보인다.
5. `sqrt(8)` 과 `Rational(1,3) + Rational(1,6)` 로 정확한 연산을 보인다.
6. `(x + y)**3` 의 전개(`expand`)와 그 전개식의 인수분해(`factor`)를 보인다.
7. `sin(x)**2 + cos(x)**2` 의 `simplify` 와 `x**2*y + x*y + x**2 + x` 를 `x` 로 `collect` 하는 줄을 보인다.

3단계 — 방정식 풀기 조각
8. `x**2 - 5*x + 6` 을 `x` 로 푸는 줄.
9. `2*x + y - 5` 와 `x - y - 1` 의 연립방정식을 `[x, y]` 로 푸는 줄.
10. `Eq(x**3 - 1, 0)` 을 만들어 푸는 줄.
11. 부등식 `x**2 - 4 < 0` 을 푸는 줄.

4단계 — 미분 조각
12. `x**3` · `sin(x)` · `exp(x)` · `log(x)` 의 한 번 미분.
13. `x**4` 의 2계 미분과 `sin(x)` 의 3계 미분(`diff(식, x, 횟수)` 꼴).
14. `f = x**2 * y + x * y**3` 의 `x` 편미분 · `y` 편미분 · `x` 와 `y` 로 잇따라 미분.

5단계 — 적분 조각
15. `x**2` · `sin(x)` · `1/x` 의 부정적분.
16. `x**2` 을 0~1, `sin(x)` 을 0~`pi` 로 정적분.
17. `exp(-x)` 를 0~`oo` 로 이상적분.
18. `x*y` 를 `x` 0~1, `y` 0~2 로 다중적분.

6단계 — 기타 기능 조각
19. `sin(x)/x` 의 `x → 0` 극한과 `(1+1/n)**n` 의 `n → oo` 극한.
20. `1/n**2` 의 1~`oo` 합과 `n` 의 1~10 합(`summation`).
21. `Matrix([[1, 2], [3, 4]])` 의 행렬식 · 역행렬 · 고유값.
22. `x**2 / (x + 1)` 을 `latex` 로 바꾸는 줄.

7단계 — 함수 정리
23. 마지막 섹션은 문자열 조각 없이 「심볼 · 대수 · 풀기 · 미적분 · 출력」 다섯 갈래의 함수 이름을 한 줄씩 찍는다.

**시작 코드**

```python
# SymPy - 심볼릭 수학 라이브러리
# pip install sympy

print("=== 심볼 정의와 기본 연산 ===")
print("""
from sympy import symbols, sqrt, Rational, pi, oo, I
from sympy import expand, factor, simplify, collect

# 심볼 정의
# TODO: x, y, z (제약 없음) / a, b, c (실수) / n (양의 정수)

# 정확한 연산 (부동소수점 오차 없음)
# TODO: sqrt(8), Rational(1,3) + Rational(1,6)

# 전개, 인수분해
# TODO: expand((x + y)**3), factor(전개식)

# 단순화
# TODO: simplify(sin² + cos²), collect(..., x)
""")

print()
print("=== 방정식 풀기 (solve) ===")
print("""
from sympy import symbols, solve, Eq

x, y = symbols('x y')

# TODO: 다항식 / 연립방정식 / Eq 객체 / 부등식
""")

print()
print("=== 미분 (diff) ===")
print("""
from sympy import symbols, diff, sin, cos, exp, log, ln

x = symbols('x')

# TODO: 기본 미분 / 고차 미분 / 편미분
""")

print()
print("=== 적분 (integrate) ===")
print("""
from sympy import symbols, integrate, sin, cos, exp, log, oo, pi

x = symbols('x')

# TODO: 부정적분 / 정적분 / 이상적분 / 다중적분
""")

print()
print("=== 기타 유용한 기능 ===")
print("""
from sympy import symbols, limit, summation, Matrix, latex, pprint
from sympy import sin, oo

x, n = symbols('x n')

# TODO: 극한 / 급수 합 / 행렬 / LaTeX 출력
""")

print()
print("=== 주요 함수 정리 ===")
# TODO: 심볼 / 대수 / 풀기 / 미적분 / 출력 — 다섯 줄
```

**확인 방법** — `python sympy-basics.py` 로 돌려 여섯 제목이 차례로 나오는지, 앞의 다섯 섹션에 코드 조각이 글자 그대로(중괄호 포함) 찍히는지, 마지막 섹션에 함수 이름 다섯 줄이 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
