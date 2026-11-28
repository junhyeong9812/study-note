# python/python-stdlib/14 — unittest (단위 테스트) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. bytes 를 돌려주도록 바꿔 끼운 함수 (예측)

```python
# 질문용 발췌
def process_user(user_id):
    data = get_user_data(user_id)
    return f"Processed: {data}"

@patch('__main__.get_user_data')
def test_process_user(self, mock_get):
    mock_get.return_value = b'{"name": "Alice"}'
    result = process_user(123)
    mock_get.assert_called_once_with(123)
```

- `result` 에 담기는 문자열은 정확히 어떤 꼴인가?
- 마지막 줄의 `assert_called_once_with(123)` 은 통과하나?

### 2. 세 값을 넣은 side_effect 를 네 번 부르면 (예측)

```python
# 질문용 발췌
mock = Mock()
mock.side_effect = [1, 2, 3]
mock(); mock(); mock()
mock()
```

- 마지막 줄의 네 번째 호출에서는 무슨 일이 생기나?

### 3. 테스트 셋인 클래스의 준비 고리 (예측)

```python
# 질문용 발췌
class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls): ...
    def setUp(self): ...
    def test_a(self): ...
    def test_b(self): ...
    def test_c(self): ...
```

- 이 클래스를 한 번 돌리면 `setUpClass` 와 `setUp` 은 각각 몇 번 불리나?

### 4. 계산기는 테스트마다, 임시 파일은 클래스당 한 번 (왜)

- `Calculator` 는 `setUp` 에서 매번 새로 만들고 임시 파일은 `setUpClass` 에서 한 번만 만드는 까닭은 무엇인가?

### 5. patch 경로는 정의된 곳이 아니라 쓰이는 곳 (왜)

- `patch` 에 함수가 정의된 모듈이 아니라 그 함수를 쓰는 모듈의 경로를 적어야 하는 까닭은 무엇인가?

### 6. assertAlmostEqual 의 places 를 올리면 (경계)

- `assertAlmostEqual(10 / 3, 3.333, places=3)` 은 통과하는데, `places=4` 로 올리면 판정은 어떻게 되나?

### 7. subTest 안에서 한 케이스가 틀리면 (경계)

- 짝수 판정 목록에서 `(4, True)` 를 `(4, False)` 로 잘못 적으면, 그 뒤의 `5` 와 `8` 케이스는 검사되나?
- 같은 반복문에서 `subTest` 를 빼면 무엇이 달라지나?

### 8. Mock 과 MagicMock 의 갈림길 (연결)

- `len()` 이나 `mock[0]` 처럼 파이썬 문법으로 쓰일 가짜를 만들 때 `Mock` 대신 `MagicMock` 을 고르는 까닭은 매직 메서드와 어떻게 이어지나?

### 9. unittest 와 pytest, assertEqual 과 assert 문 (연결)

- 실무에서 더 간결하다는 `pytest` 가 있는데도 `unittest` 를 고를 만한 까닭은 무엇인가?
- `unittest` 안에서 맨 `assert a == b` 대신 `self.assertEqual(a, b)` 를 쓰면 실패했을 때 무엇이 나아지나?

### 10. 건너뛴 테스트의 집계 (경계)

- `@unittest.skipIf(True, "조건부 스킵")` 를 단 테스트는 결과에서 실패 · 에러 · 건너뜀 가운데 어디로 세나?

## 실습

### 실습 1. 계산기 · 파일 · 가짜 API 를 시험하는 테스트 파일 만들기

**만들 것** — 계산기 클래스와 가짜 API 함수를 대상으로, assert 메서드 · 준비 고리 · Mock · patch · subTest · skip 을 모두 쓰는 테스트 클래스 다섯 개를 만들고 한 파일 안에서 직접 돌려 결과를 집계한다.

**요구 조건**

1단계 — `TestCalculator`
1. `setUp` 에서 테스트마다 새 `Calculator` 를 `self.calc` 에 만든다. `tearDown` 은 정리 자리만 둔다.
2. `test_add` — `add(2, 3)` 이 `5`, `add(-1, 1)` 이 `0` 인지 확인한다.
3. `test_divide` — `divide(10, 3)` 이 `3.333` 과 소수점 3자리까지 같은지 확인한다.
4. `test_divide_by_zero` — `divide(10, 0)` 이 `ValueError` 를 내는지, 그 메시지에 `'zero'` 가 들어 있는지 확인한다.
5. `test_is_positive` — `1` 은 참, `-1` 은 거짓인지 확인한다.
6. `test_collections` — 목록 포함 · 불포함, `self.calc` 의 타입, `None` 여부를 각각 assert 메서드로 확인한다.
7. `test_comparisons` — 크다 · 작다 · 크거나 같다를 각각 확인한다.

2단계 — `TestWithClassSetup`
8. 클래스당 한 번, 임시 디렉터리를 만들고 그 안에 `'test content'` 가 적힌 `test.txt` 를 만든다. 경로는 클래스 속성으로 둔다.
9. 클래스의 테스트가 다 끝나면 그 디렉터리를 통째로 지운다.
10. `test_file_exists` 는 파일이 있는지, `test_file_content` 는 내용이 `'test content'` 인지 확인한다.

3단계 — `TestWithMock`
11. `test_process_user` — `get_user_data` 를 patch 로 바꿔 `b'{"name": "Alice"}'` 를 돌려주게 하고, `process_user(123)` 의 결과 문자열과 「`123` 으로 정확히 한 번 불렸는지」를 확인한다.
12. `test_mock_basic` — `Mock` 의 메서드가 `42` 를 돌려주게 하고, 한 번 불렸는지 확인한다.
13. `test_magic_mock` — `MagicMock` 으로 `len()` 이 `5`, `[0]` 이 `'value'` 가 되게 하고 확인한다.
14. `test_side_effect` — 호출마다 `1, 2, 3` 을 차례로 돌려주게 해 확인하고, 이어서 부르면 `ValueError` 가 나게 바꿔 확인한다.
15. `test_call_args` — `mock(1, 2, key='value')` · `mock(3, 4)` 로 두 번 부른 뒤, 마지막 호출 · 전체 호출 차례 · 호출 횟수(`2`)를 확인한다.

4단계 — `TestSubTest` · `TestSkip`
16. `test_even_numbers` — `(2, True), (4, True), (5, False), (8, True)` 의 짝수 여부를 케이스마다 따로 판정한다.
17. `test_not_implemented` 는 무조건, `test_conditional` 은 조건이 참이어서 건너뛴다(이유 문자열을 단다).

5단계 — 실행
18. 다섯 클래스의 테스트를 모아 한 묶음으로 만들고, 테스트마다 한 줄씩 보고하는 러너로 돌린다.
19. 끝에 실행 수 · 실패 수 · 에러 수 · 건너뜀 수를 한 줄로 알린다.

**시작 코드**

```python
import unittest
from unittest.mock import patch, MagicMock, Mock, call
import tempfile
import os

# === 테스트 대상 코드 (그대로 둔다) ===
class Calculator:
    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def is_positive(self, n):
        return n > 0

def get_user_data(user_id):
    """외부 API 호출 시뮬레이션"""
    import urllib.request
    response = urllib.request.urlopen(f'https://api.example.com/users/{user_id}')
    return response.read()

def process_user(user_id):
    data = get_user_data(user_id)
    return f"Processed: {data}"

# === 1단계 ===
class TestCalculator(unittest.TestCase):
    def setUp(self):
        pass  # TODO: 테스트마다 새 계산기

    def tearDown(self):
        pass  # 리소스 정리

    def test_add(self):
        pass  # TODO

    def test_divide(self):
        pass  # TODO: 소수점 3자리 비교

    def test_divide_by_zero(self):
        pass  # TODO: 예외와 메시지

    def test_is_positive(self):
        pass  # TODO

    def test_collections(self):
        pass  # TODO: 포함 · 불포함 · 타입 · None

    def test_comparisons(self):
        pass  # TODO

# === 2단계 ===
class TestWithClassSetup(unittest.TestCase):
    # TODO: 클래스당 한 번 — 임시 디렉터리와 test.txt 만들기
    # TODO: 클래스당 한 번 — 디렉터리 지우기

    def test_file_exists(self):
        pass  # TODO

    def test_file_content(self):
        pass  # TODO

# === 3단계 ===
class TestWithMock(unittest.TestCase):
    # TODO: get_user_data 를 바꿔 끼우는 데코레이터
    def test_process_user(self, mock_get):
        pass  # TODO

    def test_mock_basic(self):
        pass  # TODO

    def test_magic_mock(self):
        pass  # TODO

    def test_side_effect(self):
        pass  # TODO: 리스트, 그다음 예외

    def test_call_args(self):
        pass  # TODO

# === 4단계 ===
class TestSubTest(unittest.TestCase):
    def test_even_numbers(self):
        evens = [(2, True), (4, True), (5, False), (8, True)]
        # TODO: 케이스마다 따로 판정

class TestSkip(unittest.TestCase):
    # TODO: 무조건 건너뛰기
    def test_not_implemented(self):
        pass

    # TODO: 조건부 건너뛰기
    def test_conditional(self):
        pass

# === 5단계 ===
print("=== unittest 실행 ===")
# TODO: 로더 · 스위트 · 러너(verbosity=2) · 결과 집계 한 줄
```

**확인 방법** — 파일을 `test_calc.py` 처럼 `unittest.py` 가 아닌 이름으로 저장하고 `python test_calc.py` 로 돌린다. 테스트마다 한 줄씩 결과가 나오고, 마지막 집계 줄에서 실패 0 · 에러 0 · 건너뜀 2 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
