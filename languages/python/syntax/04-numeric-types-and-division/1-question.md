# python/syntax/04-numeric-types-and-division — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ **손으로 계산해서 적지 마라.** 이 주제는 손계산이 실제 값과 어긋나는 자리가 많다 — 예측을 적고 **던져서 대조**한다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 음수에서 갈리는 한 줄 (예측)

```python
import math
print(-7 / 2)
print(-7 // 2)
print(-7 % 2)
print(divmod(-7, 2))
print(math.fmod(-7, 2))
print(int(-7 / 2))
```

- 여섯 줄의 출력은 각각 무엇이고, 「바닥 나눗셈」이라는 이름이 이 값들에서 어떻게 설명되는가?

### 2. 부호가 반대편에 붙는다 (예측)

```python
import math
print(7 // -2, 7 % -2, math.fmod(7, -2))
print((-17) % 8, math.fmod(-17, 8))
print((-7//2)*2 + (-7%2))
print(7.5 // 2, type(7.5 // 2).__name__)
```

- 네 줄의 출력은 각각 무엇이고, `%` 와 `math.fmod` 중 해시 버킷 번호로 쓸 수 있는 쪽은 어느 쪽인가?

### 3. 무한한 `int` 와 그 한도 (예측)

```python
import sys
print(sys.get_int_max_str_digits())
big = 10 ** 5000
print(big.bit_length())
try:
    str(big)
except ValueError as e:
    print("ValueError:", str(e)[:60])
print(len(hex(big)))
```

- 네 줄의 출력은 각각 무엇이고, 「`int` 에 상한이 없다」와 이 `ValueError` 가 어떻게 양립하는가?

### 4. 큰 정수를 `/` 로 나누면 (예측)

```python
m = 2**60 + 3
print(m // 2)
print(int(m / 2))
print(m // 2 == int(m / 2))
print(4 / 2, type(4 / 2).__name__)
```

- 네 줄의 출력은 각각 무엇이고, 이 어긋남에 에러도 경고도 없는 이유는 무엇인가?

### 5. `0.1 + 0.2` 와 세 가지 자 (예측)

```python
from decimal import Decimal
from fractions import Fraction
print(0.1 + 0.2)
print(Decimal("0.1") + Decimal("0.2"))
print(Decimal(0.1))
print(Fraction("0.1"), Fraction(0.1))
```

- 네 줄의 출력은 각각 무엇이고, `Decimal(0.1)` 과 `Decimal("0.1")` 이 갈리는 이유는 무엇인가?

### 6. `.5` 는 어디로 가나 (예측)

```python
print(round(0.5), round(1.5), round(2.5), round(3.5))
print(round(-0.5), round(-1.5))
print(round(2.675, 2))
print(type(round(0.5)).__name__, type(round(0.5, 0)).__name__)
```

- 네 줄의 출력은 각각 무엇이고, 셋째 줄이 넷 중 **다른 원인**인 이유는 무엇인가?

### 7. `bool` 이 `int` 라는 것 (왜)

- `True + True` 가 `2` 이고 `{1: 'a', True: 'b'}` 의 키가 **하나**가 되는 이유는 무엇이며, 표준 라이브러리는 이 성질에 기대는 것을 왜 권하지 않는가?

### 8. 0 으로 나누는 네 가지 (경계)

- `1 // 0` · `1 / 0` · `1 % 0` · `math.fmod(1, 0)` 이 각각 어떤 예외를 내고, `except ZeroDivisionError` 로 감싼 코드가 어디서 새는가?

### 9. 무엇이 언어 보장인가 (경계)

- 「`int` 는 범위가 무제한이다」와 「`float` 은 IEEE 754 배정밀도다」 중 **언어가 보장하는 것**은 어느 쪽이고, 다른 쪽은 문서가 뭐라고 적는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 머신·이 판의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 무엇으로 계산할 것인가 (연결)

- 금액 합계 · 페이지 수 · 해시 버킷 · 과학 계산 네 자리에 각각 어떤 수 타입과 연산자를 고르고, 그 이유를 한 줄씩 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
