# python/python-testing-deep/11 — Property 기반 테스트 (hypothesis) — 정리 (힌트)

> 출처 — study-site 항목 `python/property-testing`(항목 데이터 `data/python/testing-deep.json`) · 정답 코드 study-practice `python/python-testing-deep/reference/property-testing.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**property 기반 테스트는 「검수원에게 견본 몇 개를 주는 대신 규칙표를 주는 것」이다.**
견본 검사에서는 「이 의자는 다리가 네 개다」처럼 정해 둔 물건 몇 개만 본다.
규칙표 검사에서는 「모든 의자는 바닥에 놓으면 흔들리지 않는다」 같은 규칙을 주고, 검수원이 창고에서 아무 의자나 수백 개 꺼내 확인한다.
규칙을 어긴 의자를 찾으면, 검수원은 그 의자에서 부품을 하나씩 떼어 보며 「규칙을 어기는 가장 단순한 의자」를 들고 온다.
hypothesis 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 규칙표 | 테스트 함수 안의 `assert` (속성) |
| 창고에서 아무 의자나 꺼내기 | strategy 가 무작위 입력을 만든다 |
| 꺼낼 의자의 종류 지정 | `st.integers()` · `st.text()` 같은 strategy |
| 부품을 떼어 가장 단순한 불량품 찾기 | shrinking (최소 반례 찾기) |
| 「다리 부러진 의자는 검사 대상 아님」 | `assume()` |
| 「이 의자는 꼭 검사해라」 | `@example()` |
| 몇 개를 꺼낼지 | `@settings(max_examples=...)` |

```text
  strategy ──만든다──▶ 입력 a, b, ... ──넣는다──▶ 테스트 함수(속성 assert)
      ▲                                              │
      │                                    통과 → 다음 입력 (수백 번)
      │                                    실패 → shrinking
      └──────────── 더 작은 입력으로 다시 ◀──────────┘
                                                     │
                                        더 줄일 수 없으면 → 최소 반례 보고
```

## 이 주제가 답하려는 질문

1. 특정 값 몇 개가 아니라 「모든 입력에 대해 성립해야 할 성질」을 어떻게 검사하나?
2. 무작위 입력의 종류와 범위는 어떻게 정하나?
3. 실패를 찾았을 때 왜 원래 입력이 아니라 더 작은 입력이 보고되나?
4. 검사에서 빼야 할 입력과 꼭 넣어야 할 입력은 어떻게 다루나?

## 동작 방식

### (1) `@given` 과 strategy — 입력을 만들어 반복 실행한다

**언제 쓰나** — 함수가 지켜야 할 성질을 정했고, 그 성질을 다양한 입력으로 확인하고 싶을 때.
테스트 함수의 인자를 직접 채우지 않고 hypothesis 에 맡긴다.

```text
@given(a=st.integers(), b=st.integers())
def test_addition_commutative(a, b):
    assert add(a, b) == add(b, a)

  st.integers() → a 후보 생성 ┐
  st.integers() → b 후보 생성 ┴→ test(a, b) 호출 → assert 통과? ─ 예 → 다음 쌍
                                                              └ 아니오 → (3) shrinking
결과: 수많은 (a, b) 쌍에서 교환법칙이 확인된다
```

- `@given` 은 키워드 인자마다 strategy 를 하나씩 받는다.
- hypothesis 가 각 strategy 에서 값을 뽑아 테스트 함수를 부른다.
- 이 호출을 여러 번(원본 주석에 따르면 기본 100번) 되풀이한다.
- `assert` 가 깨지거나 다른 예외가 나면 그 입력은 실패로 기록된다.

> **property(속성)** — 특정 출력값이 아니라 입력과 출력 사이에 늘 성립해야 하는 관계.\
> 예: 「`reverse(reverse(s)) == s`」.

> **strategy** — 어떤 종류 · 범위의 값을 만들지 정한 생성 규칙.\
> 예: `st.integers(min_value=0, max_value=150)` 은 0~150 의 정수를 만든다.

`assert` 뿐 아니라 테스트 안에서 일어난 **예외도 실패다**.
예를 들어 빈 리스트로 `max([])` 를 부르면 `ValueError` 가 나고, hypothesis 는 이것도 반례로 잡는다.

strategy 는 겹쳐 쌓을 수 있다.
원본 예제가 쓴 것과 `__main__` 표에 실린 것을 모으면 이렇다.

| strategy | 만드는 것 |
|---|---|
| `st.integers()` | 정수 (범위 지정 가능, 지정하지 않으면 범위 제한 없음) |
| `st.floats()` | 실수 (NaN, Inf 포함) |
| `st.text()` | 유니코드 문자열 (이모지 · 특수문자 포함) |
| `st.binary()` | 바이트열 |
| `st.booleans()` | `True` / `False` |
| `st.lists(st.integers())` | 정수 리스트 |
| `st.dictionaries(st.text(), st.integers())` | 딕셔너리 (키 · 값 모두 생성) |
| `st.fixed_dictionaries({...})` | 키가 고정된 딕셔너리 (값만 생성) |
| `st.emails()` | 이메일 주소 |
| `st.datetimes()` | `datetime` 객체 |
| `st.characters(whitelist_categories=('L',))` | 유니코드 분류가 「문자(L)」인 글자 |
| `st.one_of(st.integers(), st.text())` | 여러 타입 중 하나 |

`st.lists` 는 `min_size` 를 주지 않으면 **빈 리스트도** 만든다.
그래서 원본의 `test_with_settings` 는 `min_size=1` 로 빈 리스트를 막는다.

### (2) 속성 고르기 — 무엇을 assert 하나

**언제 쓰나** — 정답을 미리 계산해 둘 수 없는 함수를 검사할 때.
「정답 값」 대신 「정답이 지켜야 할 관계」를 적는다.

```text
함수            속성의 종류        assert
add            교환법칙          add(a, b) == add(b, a)
reverse_string 역함수(자기 역)    reverse(reverse(s)) == s
encode_decode  왕복(roundtrip)   decode(encode(t)) == t
sort_list      불변성 + 순서      길이 같다 / 원소 같다 / 이웃끼리 <=
order_total    범위 관계          total > 0, total >= 가장 싼 단가
```

- 교환법칙은 인자 순서를 바꿔도 결과가 같다는 성질이다.
- 역함수 속성은 「한 번 하고 되돌리면 원래대로」다 — 뒤집기를 두 번 하면 원래 문자열이다.
- 왕복 속성은 역함수 속성의 한 꼴로, 인코딩한 것을 디코딩하면 원래 값이 돌아온다.
- 불변성은 변환해도 바뀌지 않는 양이다 — 정렬해도 길이와 원소 묶음은 그대로다.
- 주문 합계는 가격이 100 이상, 수량이 1 이상이므로 합계는 양수이고 어느 한 상품의 단가보다 작을 수 없다.

> **불변성(invariant)** — 연산 전후로 변하지 않는 성질.\
> 예: 정렬 전후 리스트의 길이.

> **roundtrip(왕복)** — 변환한 뒤 되돌리는 변환을 거치면 처음 값이 나온다는 성질.\
> 예: `text.encode('utf-8').decode('utf-8') == text`.

### (3) shrinking — 실패 입력을 가장 작게 줄인다

**언제 쓰나** — 따로 부르지 않는다.
실패가 나면 hypothesis 가 알아서 한다.

```text
처음 찾은 실패 입력:  [1000, -500, 42]          (원본이 든 예시)
       │ 원소 빼 보기 · 값 줄여 보기 → 여전히 실패하나?
       ▼
                     [0, -1]
       │ 더 줄이면 통과해 버린다
       ▼
보고: 최소 반례 [0, -1]
```

- 무작위로 처음 걸린 입력은 대개 크고 지저분하다.
- hypothesis 는 그 입력을 조금씩 단순하게 바꿔 보며 실패가 유지되는지 확인한다.
- 더 줄이면 통과하는 지점에서 멈추고, 그 입력을 반례로 보고한다.
- 사람은 작은 반례를 보고 원인을 훨씬 빨리 짚는다.

> **shrinking** — 실패한 입력을, 실패를 유지하는 가장 단순한 입력으로 자동 축소하는 과정.\
> 예: 원소 셋짜리 리스트가 `[0, -1]` 로 줄어든다.

> **반례(counterexample)** — 속성이 성립하지 않음을 보여 주는 입력 하나.\
> 예: 교환법칙이 깨지는 `(a, b)` 쌍.

위 그림의 `[1000, -500, 42] → [0, -1]` 은 원본 `__main__` 이 출력하는 **설명용 예시 문장**이다.
어느 테스트를 돌린 결과가 아니다.

### (4) `assume` 과 `@example` — 입력 집합을 덜고 더한다

**언제 쓰나** — `assume` 은 속성이 애초에 적용되지 않는 입력을 뺄 때.
`@example` 은 무작위에 맡기면 안 뽑힐 수도 있는 경계값을 반드시 넣을 때.

```text
@given(a=st.integers(), b=st.integers())
def test_division_properties(a, b):
    assume(b != 0)          ← b == 0 이면 여기서 이 입력을 버린다
    ...

@given(n=st.integers(min_value=0))
@example(0)                 ← 0, 1, 2**31-1 은 무작위와 상관없이 반드시 넣는다
@example(1)
@example(2**31 - 1)
def test_fibonacci(n): ...

생성된 입력 ─┬─ assume 거짓 → 버림 (실패도 통과도 아님)
            └─ assume 참   → 검사 계속
@example 값 → 생성된 입력과 별도로 항상 검사 대상에 들어간다
```

- `assume(조건)` 이 거짓이면 그 입력은 실패가 아니라 「해당 없음」으로 버려진다.
- 버려진 입력은 반례 후보에서도 빠진다.
- `@example` 은 생성과 무관하게 지정한 값을 검사 목록에 더한다.
- 둘은 반대 방향이다 — `assume` 은 빼고, `@example` 은 더한다.

`test_fibonacci` 는 두 가지를 함께 쓴다.
`@example(2**31 - 1)` 로 큰 값을 넣었지만, 함수 첫 줄의 `assume(n <= 30)` 이 그 값을 다시 버린다.
이 조합이 실제로 무엇을 하는지는 「어디서 틀리나」 5번에서 다룬다.

### (5) `@settings` — 몇 번, 얼마나 오래

**언제 쓰나** — 기본 실행 횟수보다 더 많이 찾아보고 싶거나, 한 번 실행이 느려 시간 제한에 걸릴 때.

```text
@settings(max_examples=200, deadline=None)
@given(lst=st.lists(st.integers(), min_size=1))
def test_with_settings(lst): ...

max_examples=200 → 입력 200개까지 시도 (원본 주석: 기본 100)
deadline=None    → 한 번 실행에 걸리는 시간 제한을 끈다
```

- `max_examples` 는 시도할 입력 수다.
- `deadline` 은 입력 하나를 처리하는 시간의 상한이며, `None` 이면 제한이 없다.
- 원본은 `HealthCheck` 를 가져오지만 쓰지 않는다 — 원본 주석에 따르면 속도 같은 검사를 끌 때 쓰는 것이다.

## 문법 — 형태와 규칙

```python
from hypothesis import given, settings, assume, example
from hypothesis import strategies as st

def clamp(x, lo, hi):
    return max(lo, min(x, hi))

@settings(max_examples=300)
@given(x=st.integers(), lo=st.integers(), hi=st.integers())
@example(x=0, lo=0, hi=0)
def test_clamp_in_range(x, lo, hi):
    assume(lo <= hi)
    r = clamp(x, lo, hi)
    assert lo <= r <= hi
```

- `@given(이름=strategy, ...)` 로 테스트 함수의 인자를 채운다.
- strategy 는 `from hypothesis import strategies as st` 로 가져와 `st.` 로 부른다.
- 범위 · 크기는 인자로 좁힌다: `min_value` · `max_value` (수), `min_size` · `max_size` (문자열 · 리스트), `alphabet` (문자열에 쓸 글자).
- `assume(조건)` 은 테스트 본문 안에서 부른다.
- `@example(...)` 은 `@given` 과 함께 데코레이터로 붙인다 — 원본은 `@given` 아래에 둔다.
- `@settings(...)` 는 원본처럼 `@given` 위에 둔다.
- 테스트 함수는 pytest 가 찾아 실행한다 — 파일을 `python 파일.py` 로 돌리면 `if __name__ == '__main__':` 아래 코드만 돈다.
- 원본의 `__main__` 블록은 설명 문장만 출력하며, 어떤 테스트 함수도 부르지 않는다.
- 설치는 `pip install hypothesis` 다.

예시 테스트와 속성 테스트를 나란히 놓으면 이렇다 (원본 `__main__` 의 문장).

| 종류 | 꼴 | 무엇을 보나 |
|---|---|---|
| 예시 테스트 | `assert add(2, 3) == 5` | 특정 값 |
| 속성 테스트 | `assert add(a, b) == add(b, a)` | 모든 값에 대한 속성 |

## 어디서 틀리나

### 1. 특정 값을 검사하는 습관

property 테스트는 특정 값이 아니라 「속성」을 검증한다.
`@given` 을 붙여 놓고 `assert add(a, b) == 5` 처럼 쓰면 대부분의 입력에서 깨진다.
입력이 무엇이든 성립하는 관계를 적어야 한다.

### 2. 속성 후보를 못 찾는다

교환법칙, 역함수, 불변성 같은 수학적 속성이 좋은 후보다.
「되돌리는 함수가 있나 (왕복)」「순서를 바꿔도 같나 (교환)」「변환 뒤에도 남는 양이 있나 (불변)」를 차례로 물어본다.

### 3. 검사 대상을 검사 도구로 쓴다

`test_sort_properties` 의 속성 2 는 `sorted(sorted_lst) == sorted(lst)` 다.
그런데 검사 대상 `sort_list` 가 바로 `sorted` 다.
정렬 결과를 같은 `sorted` 로 비교하므로, `sorted` 가 틀려도 양쪽이 똑같이 틀려 잡히지 않는다.
원본 주석은 `sort_list` 에 「멱등성」이 있다고 적지만, 멱등성(두 번 정렬해도 같다)을 직접 확인하는 `assert` 는 없다.

### 4. `assume` 이 걸러 주지 못하는 실패 — 나눗셈 테스트

원본의 주장: `assume(b != 0)` 을 두면 `a / b * b ≈ a` 가 오차 `1e-10` 안에서 성립한다.
의심스러운 까닭:
- `a / b` 는 부동소수점 실수다. `a` 가 큰 정수면 실수로 바꾸는 순간 아래 자리가 잘리고, `result * b - a` 의 오차가 `1e-10` 을 쉽게 넘는다.
- `st.integers()` 는 범위가 없으므로 아주 큰 정수도 만든다. 몫이 실수로 나타낼 수 없을 만큼 크면 나눗셈 자체가 예외(`OverflowError`)를 낼 수 있다 (확인 필요).
- 결국 이 테스트는 hypothesis 가 반례를 찾아낼 가능성이 높다 — 「property 테스트가 엣지 케이스를 찾는다」는 이 항목의 주제를 보여 주는 예이기도 하다.
고치려면 오차를 상대 오차로 바꾸거나 `a`, `b` 의 범위를 좁힌다.

### 5. `@example` 로 넣은 값을 `assume` 이 버린다 — 피보나치 테스트

`@example(2**31 - 1)` 을 넣었지만 `assume(n <= 30)` 이 이 값을 버리므로, 이 경계값은 실제로 검사되지 않는다.
explicit example 에서 `assume` 이 거짓일 때 hypothesis 가 조용히 넘기는지 오류로 다루는지는 버전에 따라 다를 수 있다 (확인 필요).
또 `st.integers(min_value=0)` 은 상한이 없어 30 을 넘는 값이 자주 나오고, 그만큼 버려지는 입력이 많다.
버리는 비율이 지나치면 hypothesis 가 건강 검사(`HealthCheck`)로 경고하거나 실패로 다룰 수 있다 (확인 필요).
범위는 `assume` 보다 strategy 에서 좁히는 편이 낫다 — `st.integers(min_value=0, max_value=30)`.

원본 주석 「항상 양수」도 정확하지 않다.
`fib(0)` 은 `0` 이고, `0` 은 양수가 아니다.
`assert result >= 0` 은 「0 이상」을 확인하므로 `0` 에서도 통과한다 — 주석이 틀렸고 코드는 맞다.

### 6. `alphabet` 의 「알파벳」은 영문자가 아니다

원본 주석은 `st.characters(whitelist_categories=('L',))` 를 「알파벳만 포함한」 이름이라고 적는다.
`'L'` 은 유니코드의 「문자(Letter)」 분류라서 영문자뿐 아니라 한글 · 한자 · 키릴 문자 같은 글자도 들어간다.
영문자만 원하면 `alphabet` 에 글자 목록을 직접 준다.

### 7. 빈 컬렉션을 잊는다

`st.lists(...)` 는 `min_size` 가 없으면 빈 리스트를 만든다.
`max([])` · `min([])` 은 `ValueError` 를 낸다.
`test_with_settings` 와 `test_order_total` 이 `min_size=1` 을 둔 까닭이다.
빈 입력이 정말 들어올 수 없는지, 아니면 함수가 처리해야 하는지 먼저 정한다.

### 8. 파일을 `python` 으로 실행하고 테스트했다고 여긴다

`@given` 이 붙은 함수는 pytest 가 모아 실행한다.
`python property-testing.py` 는 `__main__` 블록의 설명 문장만 출력한다.

### 9. shrinking 결과를 원래 입력으로 착각한다

보고된 반례는 처음 찾은 입력이 아니라 축소된 입력이다.
반례가 너무 단순해 보여도 그것이 「실패를 재현하는 가장 작은 입력」이라 원인을 좁히기에 오히려 좋다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `@given` 이 입력을 만들어 여러 번 실행한다 · shrinking · `assume` · `@example` · `@settings` | hypothesis 라이브러리 (Python 언어가 아니다) |
| 기본 실행 횟수 100 | hypothesis 의 기본 설정 — 원본 주석의 값, 버전에 따라 다를 수 있음 (확인 필요) |
| 어떤 반례가 보고되나 (`[0, -1]` 같은 구체적 모양) | hypothesis 의 축소 알고리즘 — 같은 입력이라도 버전마다 다를 수 있음 |
| `s[::-1]` 이 글자 순서를 뒤집는다 · `sorted` 가 새 리스트를 돌려준다 | Python 언어 · 표준 라이브러리 |
| 정수는 크기 제한이 없다 | Python 언어 |
| `a / b` 의 결과가 부동소수점이며 큰 수에서 오차가 생긴다 | Python 의 `float` (보통 배정밀도) — 정밀도는 구현 · 플랫폼에 기댄다 |
| `max([])` 가 `ValueError` 를 낸다 | Python 내장 함수 |
| `test_` 로 시작하는 함수를 모아 실행한다 | pytest 의 규칙 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 되돌리는 쌍이 있는 함수 (인코딩 · 직렬화 · 뒤집기) | 왕복 속성 `@given` 테스트 | 손으로 고른 문자열 몇 개만 |
| 정답을 미리 계산하기 어렵지만 관계는 아는 함수 | 불변성 · 범위 속성 | 정답 값 하드코딩 |
| 속성이 일부 입력에만 성립 (0 으로 나누기 등) | `assume` 또는 strategy 범위 좁히기 | 예외를 삼키는 `try` |
| 꼭 확인해야 할 경계값 (0, 1, 최댓값) | `@example` | 무작위에 맡기기 |
| 버려지는 입력이 대부분인 조건 | strategy 의 `min_value` · `max_value` | 넓은 strategy + 좁은 `assume` |
| 특정 버그의 재현 · 명세 문서 역할 | 예시 테스트 | property 테스트만 |
| 한 번 실행이 느린 테스트 | `@settings(deadline=None)` · `max_examples` 조정 | 기본값으로 두고 시간 초과에 놀라기 |

## 핵심 문장

1. **property 테스트는 값이 아니라 관계를 검증한다** — 교환법칙 · 역함수(왕복) · 불변성이 좋은 후보다.
2. **입력은 strategy 가 만들고, `@given` 이 그 입력으로 테스트를 여러 번 부른다** — `assert` 실패뿐 아니라 예외도 실패다.
3. **실패를 찾으면 hypothesis 는 실패가 유지되는 가장 작은 입력(최소 반례)으로 줄여 보고한다.**
4. **`assume` 은 입력을 빼고 `@example` 은 입력을 더한다** — 둘이 부딪히면 넣은 예가 버려질 수 있다.
5. **속성을 같은 구현으로 확인하면 아무것도 확인하지 않은 것이다** — 검사 대상과 검사 도구를 떼어 놓는다.

## 관련 자료

- [pytest-parametrize](../02-pytest-parametrize/2-summary.md)
- [test-patterns](../08-test-patterns/2-summary.md)
- `pytest-fixtures` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/testing-deep.json` 의 `property-testing`

## 용어 풀이

- **property(속성)** — 모든 입력에 대해 입력과 출력 사이에 성립해야 하는 관계.
- **property 기반 테스트** — 속성을 정해 두고 무작위 입력으로 그 속성을 반복 확인하는 테스트.
- **예시 테스트** — 정해 둔 입력과 기대 출력을 비교하는 테스트.
- **hypothesis** — Python 의 property 기반 테스트 라이브러리.
- **`@given`** — strategy 로 테스트 함수의 인자를 채워 반복 실행하게 하는 데코레이터.
- **strategy** — 어떤 값을 어떤 범위로 만들지 정한 생성 규칙.
- **shrinking** — 실패 입력을 실패가 유지되는 가장 작은 입력으로 줄이는 과정.
- **반례(counterexample)** — 속성이 깨지는 입력.
- **엣지 케이스** — 빈 값 · 0 · 아주 큰 값처럼 경계에 있어 잘 놓치는 입력.
- **`assume`** — 조건이 거짓인 입력을 검사에서 빼는 함수.
- **`@example`** — 무작위 생성과 별도로 반드시 검사할 입력을 더하는 데코레이터.
- **`@settings`** — 실행 횟수(`max_examples`) · 시간 제한(`deadline`) 같은 실행 설정.
- **`HealthCheck`** — 너무 느리거나 입력을 너무 많이 버리는 테스트를 알리는 검사 항목.
- **교환법칙** — 인자 순서를 바꿔도 결과가 같다는 성질.
- **역함수 속성** — 변환과 되돌리기를 이어 하면 처음 값이 나온다는 성질.
- **불변성** — 변환 전후에 바뀌지 않는 성질.
- **roundtrip(왕복)** — 인코딩 · 디코딩처럼 갔다가 돌아오면 원래 값이라는 성질.
- **멱등성** — 같은 연산을 두 번 해도 한 번 한 것과 결과가 같다는 성질.
- **유니코드 분류 `L`** — 유니코드가 「문자(Letter)」로 분류한 글자 묶음.

## 더 들어가면

- hypothesis 는 찾아낸 반례를 로컬 데이터베이스(보통 `.hypothesis/` 디렉터리)에 저장해 두고, 다음 실행 때 먼저 다시 시도한다 (확인 필요).
- `st.text()` 는 기본적으로 짝 없는 서로게이트 문자를 만들지 않는다고 알려져 있다 — 만든다면 `encode('utf-8')` 가 예외를 내 왕복 테스트가 깨진다 (확인 필요).
- 나눗셈 속성은 `math.isclose(result * b, a, rel_tol=...)` 처럼 상대 오차로 적거나, `fractions.Fraction` 으로 정확한 유리수 계산을 써서 다시 쓸 수 있다 (확인 필요).
- 상태가 있는 객체(큐 · 캐시)를 검사하는 상태 기반 테스트(`hypothesis.stateful`)도 있다 (확인 필요).
- `@given` 안에서 그때그때 값을 뽑는 `st.data()` strategy 가 있다 (확인 필요).
- `st.builds(클래스, ...)` 로 객체를 직접 만드는 strategy 를 쓸 수 있다 (확인 필요).
