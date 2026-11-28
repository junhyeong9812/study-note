# python/python-testing-deep/11 — Property 기반 테스트 (hypothesis) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 실행되지 않는다 — 설명 문장만 출력된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`test_addition_commutative` 는 불리지 않는다.
`__main__` 블록의 `print` 만 실행되어 「=== Property 테스트 vs 예시 테스트 ===」로 시작하는 설명이 나온다.

**왜 그런가**
`@given` 이 붙은 함수는 정의될 뿐이고, 그 함수를 모아 부르는 쪽은 pytest 다.
`__main__` 블록 안에는 테스트 함수를 부르는 줄이 하나도 없다.
근거: 2-summary 「문법 — 형태와 규칙」, 「어디서 틀리나 8」.

### 2. 빈 리스트에서 `ValueError` 로 실패하고, 반례는 `[]` 일 것이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`st.lists(st.integers())` 는 `min_size` 가 없으면 빈 리스트를 만든다.
`max([])` 가 `ValueError` 를 내므로 테스트가 실패한다.
반례는 `lst=[]` 로 보고될 것으로 본다.

**왜 그런가**
hypothesis 는 `assert` 실패뿐 아니라 예외도 실패로 본다.
비어 있지 않은 리스트에서는 최댓값이 최솟값보다 작을 수 없으므로 실패하는 입력은 빈 리스트뿐이다.
빈 리스트는 이미 가장 작은 리스트라 shrinking 으로 더 줄어들 것이 없다.
근거: 2-summary 「동작 방식 (1)」, 「동작 방식 (3)」, 「어디서 틀리나 7」.

### 3. `result` 는 0 이고 테스트는 통과한다 — 「항상 양수」 주석은 틀렸다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`fib(0)` 은 `if n <= 1: return n` 에서 `0` 을 돌려준다.
`assert result >= 0` 은 `0 >= 0` 이라 통과한다.
`n >= 2` 가 거짓이라 두 번째 `assert` 는 건너뛴다.
따라서 테스트는 통과한다.

**왜 그런가**
코드는 「0 이상」을 확인하므로 맞지만, 주석의 「양수」는 0 을 빼는 말이라 실제 값과 어긋난다.
근거: 2-summary 「어디서 틀리나 5」.

### 4. 손으로 고른 값이 아니라 수많은 입력에서 관계가 성립함을 확인한다

예시 테스트는 `(2, 3)` 한 쌍만 확인한다.
속성 테스트는 strategy 가 만든 다양한 입력(음수 · 0 · 아주 큰 수 등)으로 같은 관계를 반복 확인하므로, 사람이 떠올리지 못한 엣지 케이스를 찾을 수 있다.
또 정답 값을 미리 계산해 두지 않아도 검사할 수 있다.
근거: 2-summary 「한눈에」, 「동작 방식 (1)」, 「문법 — 형태와 규칙」의 예시 테스트 대 속성 테스트 표, 「어디서 틀리나 1」.

### 5. 작은 반례일수록 원인을 빨리 짚을 수 있다

무작위로 처음 걸린 입력은 대개 크고 지저분해서, 그 안의 어느 부분이 실패를 일으키는지 알기 어렵다.
shrinking 은 실패가 유지되는 한 입력을 계속 줄이고, 더 줄이면 통과하는 지점에서 멈춘다.
그래서 보고된 반례에는 실패에 꼭 필요한 부분만 남는다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 9」.

### 6. 아주 큰 정수 입력

`a / b` 는 부동소수점 실수라 큰 `a` 를 실수로 바꾸면 아래 자리가 잘린다.
그러면 `result * b - a` 의 오차가 `1e-10` 을 넘어 `assert` 가 깨진다.
`st.integers()` 는 범위가 없어 이런 큰 정수를 만든다.
몫이 실수로 나타낼 수 없을 만큼 크면 나눗셈이 예외를 낼 수도 있다 (확인 필요).
`assume(b != 0)` 은 0 으로 나누기만 막을 뿐 이 문제는 걸러 주지 않는다.
근거: 2-summary 「어디서 틀리나 4」.

### 7. 쓰이지 않는다 — `assume` 이 그 값을 버린다

`@example(2**31 - 1)` 로 넣은 값도 테스트 본문을 지나야 하는데, 첫 줄 `assume(n <= 30)` 이 거짓이 되어 그 입력은 버려진다.
그래서 이 경계값으로 피보나치 속성이 확인되는 일은 없다.
이때 hypothesis 가 조용히 넘기는지 오류로 다루는지는 버전에 따라 다를 수 있다 (확인 필요).
`@example` 은 입력을 더하고 `assume` 은 입력을 빼서, 둘이 부딪힌 경우다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 8. 검사 대상과 같은 `sorted` 로 비교하기 때문이다

`sort_list` 는 `sorted` 를 그대로 부른다.
속성 2 도 양쪽을 `sorted` 로 정렬해 비교하므로, `sorted` 가 틀리면 양쪽이 똑같이 틀려 비교는 여전히 같다고 나온다.
검사 도구가 검사 대상과 독립이어야 결함이 드러난다.
(덧붙여, 원소 묶음이 같은지는 `collections.Counter` 비교처럼 정렬을 쓰지 않는 방법으로도 확인할 수 있다 — 원본에 근거 없음 — 추론)
근거: 2-summary 「어디서 틀리나 3」, 「핵심 문장 5」.

### 9. 역함수 · 역함수(왕복) · 불변성

- `reverse_string` 두 번 → 역함수 속성 (뒤집기는 스스로가 되돌리기다).
- `encode_decode` → 역함수 속성의 한 꼴인 왕복(roundtrip) 속성.
- `sort_list` 의 길이 검사 → 불변성 (정렬 전후 길이가 바뀌지 않는다).
교환법칙에 해당하는 것은 `add` 의 테스트다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. hypothesis 로 속성 테스트 모음 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 합 돌려주기 | `add` — `return a + b` |
| 2. 슬라이싱으로 뒤집기 | `reverse_string` — `s[::-1]` |
| 3. `sorted` 로 정렬 | `sort_list` — `sorted(lst)` |
| 4. UTF-8 왕복 | `encode_decode` — `text.encode('utf-8')` · `encoded.decode('utf-8')` |
| 5. 교환법칙 | `@given(a=st.integers(), b=st.integers())` + `test_addition_commutative` |
| 6. 두 번 뒤집기 | `@given(s=st.text())` + `test_reverse_twice_is_identity` |
| 7. 정렬 세 속성 | `@given(lst=st.lists(st.integers()))` + `test_sort_properties` 의 `len` 비교 · `sorted` 비교 · `for` 오름차순 검사 |
| 8. 인코딩 왕복 | `@given(text=st.text())` + `test_encode_decode_roundtrip` |
| 9. 사용자 strategy 조합 | `st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L',)))` · `st.integers(min_value=0, max_value=150)` · `st.emails()` + `test_user_creation` |
| 10. 주문 딕셔너리 | `st.fixed_dictionaries({'items': st.lists(st.fixed_dictionaries({...}), min_size=1, max_size=10)})` + `test_order_total` 의 `sum(...)` · `total > 0` · `min(...)` 비교 |
| 11. 0 나누기 버리기 | `test_division_properties` 의 `assume(b != 0)` · `abs(result * b - a) < 1e-10` |
| 12. 피보나치 경계값과 범위 | `@given(n=st.integers(min_value=0))` · `@example(0)` · `@example(1)` · `@example(2**31 - 1)` · `assume(n <= 30)` · 안쪽 `fib` · 두 `assert` |
| 13. 실행 설정 | `@settings(max_examples=200, deadline=None)` + `st.lists(st.integers(), min_size=1)` + `test_with_settings` |
| 14. 직접 실행 출력 | `if __name__ == '__main__':` 블록 — `print(f"  {s:45s}: {desc}")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-testing-deep/reference/property-testing.py`

```python
# [테스팅 심화] Property 기반 테스트 (hypothesis)
# 설명: hypothesis로 무작위 데이터를 자동 생성하여 속성(property)을 검증하고 엣지 케이스를 발견
# 팁: Property 테스트는 특정 값이 아닌 '속성'을 검증한다. hypothesis는 실패를 발견하면 자동으로 최소 반례(shrinking)를 찾아준다. assume()으로 전제조건을 설정하고, example()로 반드시 테스트할 값을 추가한다. 교환법칙, 역함수, 불변성 등의 수학적 속성이 좋은 property 후보다.

# pytest: 테스트 프레임워크 (hypothesis와 함께 동작)
import pytest
# given: 데이터 생성 전략으로 테스트 함수 파라미터 채움
# settings: 실행 횟수/데드라인 등 커스터마이징
# assume: 부적합한 입력 스킵 (전제조건)
# example: 반드시 검증할 특정 값 강제
# HealthCheck: 속도 등 검사 비활성화용
from hypothesis import given, settings, assume, example, HealthCheck
# strategies(st): 다양한 데이터 생성 전략 모음
from hypothesis import strategies as st

# === 기본 property 테스트 ===
# 설치: pip install hypothesis

# 테스트 대상 함수들 - 검증할 속성을 가지는 단순 함수
def add(a, b):
    return a + b

# 문자열 뒤집기 - 두 번 뒤집으면 원래대로 (역함수 속성)
def reverse_string(s):
    return s[::-1]

# 정렬 - 멱등성, 길이 보존, 단조 증가 속성
def sort_list(lst):
    return sorted(lst)

# 인코딩 - 디코딩 왕복 속성
def encode_decode(text):
    encoded = text.encode('utf-8')
    return encoded.decode('utf-8')

# === Property 1: 덧셈의 교환법칙 ===
# given: 두 정수를 자동 생성하여 수백 번 검증
@given(a=st.integers(), b=st.integers())
def test_addition_commutative(a, b):
    """a + b == b + a (교환법칙)"""
    assert add(a, b) == add(b, a)

# === Property 2: 문자열 두 번 뒤집으면 원래대로 ===
# st.text(): 유니코드 문자열 (이모지, 특수문자 등 포함)
@given(s=st.text())
def test_reverse_twice_is_identity(s):
    """reverse(reverse(s)) == s"""
    assert reverse_string(reverse_string(s)) == s

# === Property 3: 정렬된 리스트의 속성 ===
# st.lists(...): 정수 리스트 자동 생성
@given(lst=st.lists(st.integers()))
def test_sort_properties(lst):
    sorted_lst = sort_list(lst)

    # 속성 1: 길이가 같다
    assert len(sorted_lst) == len(lst)

    # 속성 2: 원소가 같다 (순서만 다름)
    assert sorted(sorted_lst) == sorted(lst)

    # 속성 3: 오름차순이다
    for i in range(len(sorted_lst) - 1):
        assert sorted_lst[i] <= sorted_lst[i + 1]

# === Property 4: 인코딩/디코딩 왕복 ===
# 왕복 속성(roundtrip): encode → decode == 항등
@given(text=st.text())
def test_encode_decode_roundtrip(text):
    """인코딩 후 디코딩하면 원래 문자열"""
    assert encode_decode(text) == text

# === Strategies (데이터 생성 전략) ===
# 복합 strategy: 여러 필드 동시 생성
@given(
    # 알파벳만 포함한 1~50자 이름
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L',))),
    # 0~150 범위 정수
    age=st.integers(min_value=0, max_value=150),
    # 이메일 형식 자동 생성
    email=st.emails(),
)
def test_user_creation(name, age, email):
    """다양한 strategy 조합"""
    user = {"name": name, "age": age, "email": email}
    assert len(user["name"]) >= 1
    assert 0 <= user["age"] <= 150
    assert "@" in user["email"]

# === assume: 전제조건 ===
# assume이 False면 해당 케이스를 스킵 (반례에서 제외)
@given(a=st.integers(), b=st.integers())
def test_division_properties(a, b):
    assume(b != 0)  # b가 0이면 이 테스트 스킵
    result = a / b
    # 나눗셈의 속성: a / b * b ≈ a (부동소수점 오차 허용)
    assert abs(result * b - a) < 1e-10

# === example: 특정 입력 추가 ===
# example: 반드시 포함되어야 하는 경계값 명시
@given(n=st.integers(min_value=0))
@example(0)  # 반드시 이 입력도 테스트
@example(1)
@example(2**31 - 1)  # int32 최대값
def test_fibonacci(n):
    assume(n <= 30)  # 시간 제한 (큰 n은 너무 오래 걸림)

    # 반복형 피보나치 (테스트 안정성)
    def fib(n):
        if n <= 1: return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b

    result = fib(n)
    assert result >= 0  # 항상 양수
    if n >= 2:
        assert result == fib(n-1) + fib(n-2)  # 정의에 의한 속성

# === 복합 strategy ===
# fixed_dictionaries: 키가 고정된 딕셔너리 생성
@given(data=st.fixed_dictionaries({
    'items': st.lists(st.fixed_dictionaries({
        'name': st.text(min_size=1),
        'price': st.integers(min_value=100, max_value=1000000),
        'quantity': st.integers(min_value=1, max_value=100),
    }), min_size=1, max_size=10),
}))
def test_order_total(data):
    """주문 합계의 속성 테스트"""
    total = sum(item['price'] * item['quantity'] for item in data['items'])
    assert total > 0
    # 합계는 최소 한 상품의 단가 이상
    assert total >= min(item['price'] for item in data['items'])

# === 실행 설정 ===
# settings: 기본 100회 → 200회로 증가, 시간 제한 해제
@settings(max_examples=200, deadline=None)
@given(lst=st.lists(st.integers(), min_size=1))
def test_with_settings(lst):
    """설정 커스터마이징"""
    assert max(lst) >= min(lst)

if __name__ == '__main__':
    print("=== Property 테스트 vs 예시 테스트 ===")
    print("예시 테스트: assert add(2, 3) == 5  # 특정 값")
    print("속성 테스트: assert add(a, b) == add(b, a)  # 모든 값에 대한 속성")
    print()
    print("=== 주요 Strategies ===")
    strategies = {
        "st.integers()": "정수 (범위 지정 가능)",
        "st.floats()": "실수 (NaN, Inf 포함)",
        "st.text()": "유니코드 문자열",
        "st.binary()": "바이트열",
        "st.booleans()": "True/False",
        "st.lists(st.integers())": "정수 리스트",
        "st.dictionaries(st.text(), st.integers())": "딕셔너리",
        "st.emails()": "이메일 주소",
        "st.datetimes()": "datetime 객체",
        "st.one_of(st.integers(), st.text())": "여러 타입 중 하나",
    }
    for s, desc in strategies.items():
        print(f"  {s:45s}: {desc}")
    print()
    print("=== Shrinking ===")
    print("hypothesis가 실패 입력을 발견하면,")
    print("가능한 가장 작은 반례로 자동 축소한다.")
    print("예: [1000, -500, 42] → [0, -1] (최소 반례)")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- `@given` 의 키워드 이름은 테스트 함수의 매개변수 이름과 맞아야 한다 — strategy 가 그 이름의 인자를 채운다.
- 범위 · 크기는 strategy 인자(`min_value` · `max_size` 등)로 좁히고, `assume` 은 strategy 로 표현하기 어려운 조건(`b != 0`)에만 쓰는 편이 낫다.
- `min_size=1` 은 `max` · `min` 이 빈 리스트에서 예외를 내는 것을 막는다.
- 나눗셈 테스트와 피보나치 테스트에는 원본 그대로의 약점(큰 정수의 부동소수점 오차, `assume` 에 버려지는 `@example`)이 남아 있다 — 테스트가 실패하면 축소된 반례로 속성 쪽을 의심해 볼 차례다.
- `HealthCheck` 와 `pytest` 는 가져오기만 하고 본문에서 쓰지 않는다.
- `{s:45s}` 는 문자열을 45자 폭으로 왼쪽 정렬해 설명 열을 맞춘다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
