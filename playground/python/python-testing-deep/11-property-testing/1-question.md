# python/python-testing-deep/11 — Property 기반 테스트 (hypothesis) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 원본 파일을 `python` 으로 직접 실행하면 (예측)

```python
# 질문용 발췌
@given(a=st.integers(), b=st.integers())
def test_addition_commutative(a, b):
    assert add(a, b) == add(b, a)

if __name__ == '__main__':
    print("=== Property 테스트 vs 예시 테스트 ===")
```

- `python property-testing.py` 로 실행하면 `test_addition_commutative` 는 실행되는가?

### 2. `min_size` 를 뺀 최댓값 · 최솟값 테스트 (예측)

```python
# 질문용 발췌 — test_with_settings 에서 min_size=1 을 뺐다
@given(lst=st.lists(st.integers()))
def test_no_min_size(lst):
    assert max(lst) >= min(lst)
```

- 이 테스트는 어떤 입력에서 실패하고, hypothesis 가 보고할 반례는 무엇일 것으로 보나?

### 3. `n=0` 일 때의 피보나치 테스트 (예측)

```python
# 질문용 발췌
@example(0)
def test_fibonacci(n):
    ...
    result = fib(n)
    assert result >= 0  # 항상 양수
    if n >= 2:
        assert result == fib(n-1) + fib(n-2)
```

- `n=0` 이 들어오면 `result` 는 무엇이고, 이 테스트는 통과하는가?

### 4. 특정 값 대신 속성을 검사하는 까닭 (왜)

- `assert add(2, 3) == 5` 대신 `assert add(a, b) == add(b, a)` 를 무작위 입력으로 검사하면 무엇을 더 얻는가?

### 5. 실패 입력을 그대로 보여 주지 않고 줄이는 까닭 (왜)

- hypothesis 가 처음 찾은 실패 입력이 아니라 축소한 입력을 보고하는 것이 왜 쓸모 있는가?

### 6. `assume(b != 0)` 이 있어도 남는 나눗셈 테스트의 위험 (경계)

- `test_division_properties` 에서 0 을 걸렀는데도 속성이 깨질 수 있는 입력은 어떤 입력인가?

### 7. `@example(2**31 - 1)` 과 `assume(n <= 30)` 이 함께 있을 때 (경계)

- 이 경계값은 피보나치 속성 검사에 실제로 쓰이는가?

### 8. 정렬 테스트의 속성 2 와 검사 대상 (연결)

- `sorted(sorted_lst) == sorted(lst)` 가 `sort_list` 의 결함을 잡지 못할 수 있는 까닭은 무엇인가?

### 9. 원본의 테스트들과 속성의 종류 (연결)

- `reverse_string` 두 번 · `encode_decode` · `sort_list` 의 길이 검사는 교환법칙 · 역함수 · 불변성 가운데 각각 무엇에 해당하는가?

## 실습

### 실습 1. hypothesis 로 속성 테스트 모음 만들기

**만들 것** — 단순한 함수 넷을 두고, 그 함수들과 몇 가지 데이터 구조의 속성을 hypothesis 로 검사하는 pytest 테스트 파일을 만든다.
파일을 `python` 으로 직접 실행하면 property 테스트의 개념 설명을 출력한다.

**준비물** — `pip install hypothesis pytest` 로 hypothesis 와 pytest 를 설치한다.

**요구 조건**

1단계 — 검사 대상 함수
1. `add(a, b)` 는 두 값의 합을 돌려준다.
2. `reverse_string(s)` 는 슬라이싱으로 문자열을 뒤집어 돌려준다.
3. `sort_list(lst)` 는 `sorted` 로 정렬한 새 리스트를 돌려준다.
4. `encode_decode(text)` 는 UTF-8 로 인코딩한 뒤 다시 디코딩한 문자열을 돌려준다.

2단계 — 기본 속성
5. 임의의 두 정수에 대해 `add` 의 교환법칙을 검사한다.
6. 임의의 유니코드 문자열에 대해 두 번 뒤집으면 원래 문자열인지 검사한다.
7. 임의의 정수 리스트에 대해 정렬 결과의 길이가 같은지, 원소 묶음이 같은지, 이웃한 원소가 오름차순인지 검사한다.
8. 임의의 문자열에 대해 인코딩 · 디코딩 왕복이 원래 문자열인지 검사한다.

3단계 — strategy 조합
9. 유니코드 문자 분류(L)의 글자로 된 1~50자 이름, 0~150 나이, 이메일 주소를 동시에 만들어 사용자 딕셔너리를 꾸리고, 이름 길이 · 나이 범위 · `@` 포함을 검사한다.
10. 키가 `items` 하나로 고정된 딕셔너리를 만든다. 그 값은 상품 딕셔너리(이름은 1자 이상 문자열, 가격은 100~1000000, 수량은 1~100) 1~10개의 리스트다. 합계(가격 × 수량의 합)가 양수이고 가장 싼 단가 이상인지 검사한다.

4단계 — 입력 덜고 더하기, 실행 설정
11. 두 정수의 나눗셈에서 나누는 수가 0 인 입력은 `assume` 으로 버리고, `a / b * b` 와 `a` 의 차이가 `1e-10` 보다 작은지 검사한다.
12. 0 이상의 정수 `n` 에 대해 반복형 피보나치를 테스트 안에 정의하고, 0 · 1 · `2**31 - 1` 을 반드시 검사할 값으로 넣으며, `n` 이 30 을 넘으면 `assume` 으로 버린다. 결과가 0 이상인지, `n >= 2` 이면 앞 두 항의 합과 같은지 검사한다.
13. 입력 200개까지 시도하고 시간 제한을 끈 설정으로, 원소가 하나 이상인 정수 리스트의 최댓값이 최솟값 이상인지 검사한다.

5단계 — 직접 실행했을 때
14. `python` 으로 직접 실행하면 예시 테스트와 속성 테스트의 차이, 주요 strategy 표(strategy 이름을 45자 폭으로 맞춘 줄), shrinking 설명을 차례로 출력한다.

**시작 코드**

```python
import pytest
# TODO: hypothesis 에서 given, settings, assume, example, HealthCheck 를 가져온다
# TODO: strategies 를 st 라는 이름으로 가져온다


def add(a, b):
    # TODO: 합을 돌려준다
    ...

def reverse_string(s):
    # TODO: 슬라이싱으로 뒤집는다
    ...

def sort_list(lst):
    # TODO
    ...

def encode_decode(text):
    # TODO: utf-8 로 인코딩한 뒤 디코딩한다
    ...


# TODO: 두 정수 strategy
def test_addition_commutative(a, b):
    """a + b == b + a (교환법칙)"""
    # TODO
    ...

# TODO: 문자열 strategy
def test_reverse_twice_is_identity(s):
    """reverse(reverse(s)) == s"""
    # TODO
    ...

# TODO: 정수 리스트 strategy
def test_sort_properties(lst):
    sorted_lst = sort_list(lst)
    # TODO: 길이 · 원소 · 오름차순 세 속성
    ...

# TODO: 문자열 strategy
def test_encode_decode_roundtrip(text):
    """인코딩 후 디코딩하면 원래 문자열"""
    # TODO
    ...

# TODO: name / age / email strategy 셋
def test_user_creation(name, age, email):
    """다양한 strategy 조합"""
    user = {"name": name, "age": age, "email": email}
    # TODO: 세 가지 검사
    ...

# TODO: 두 정수 strategy
def test_division_properties(a, b):
    # TODO: b 가 0 인 입력을 버린다
    result = a / b
    # TODO: 오차 검사
    ...

# TODO: 0 이상 정수 strategy 와 반드시 검사할 값 셋
def test_fibonacci(n):
    # TODO: 30 을 넘는 n 을 버린다

    def fib(n):
        if n <= 1: return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b

    result = fib(n)
    # TODO: 두 가지 속성
    ...

# TODO: items 고정 딕셔너리 strategy
def test_order_total(data):
    """주문 합계의 속성 테스트"""
    # TODO: 합계 계산과 두 가지 검사
    ...

# TODO: 실행 설정 (200개, 시간 제한 없음)
# TODO: 원소가 하나 이상인 정수 리스트 strategy
def test_with_settings(lst):
    """설정 커스터마이징"""
    # TODO
    ...

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
    # TODO: strategy 이름을 45자 폭으로 맞춰 설명과 함께 출력한다
    print()
    print("=== Shrinking ===")
    print("hypothesis가 실패 입력을 발견하면,")
    print("가능한 가장 작은 반례로 자동 축소한다.")
    print("예: [1000, -500, 42] → [0, -1] (최소 반례)")
```

**확인 방법** — `pytest property-testing.py` 로 테스트를 돌려 각 테스트의 통과 · 실패를 본다.
실패한 테스트가 있으면 hypothesis 가 보고한 축소된 반례를 읽고, 그 실패가 코드의 잘못인지 속성의 잘못인지 가린다.
`python property-testing.py` 로 실행해 설명 문장 세 덩어리가 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
