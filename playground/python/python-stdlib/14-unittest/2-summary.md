# python/python-stdlib/14 — unittest (단위 테스트) — 정리 (힌트)

> 출처 — study-site 항목 `python/unittest`(항목 데이터 `data/python/stdlib.json`) · 정답 코드 study-practice `python/python-stdlib/reference/unittest.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**`unittest` 는 「자동차 출고 검사장」이다.**
검사대마다 차를 새로 세워 놓고(준비), 한 항목을 재고(검사), 검사가 끝나면 차를 치운다(정리).
검사장 조명처럼 비싼 설비는 하루에 한 번만 켜고 끈다.
바깥 부품 공장에 전화를 거는 대신 모형 부품을 끼워 둔다.
그러면 검사 결과가 바깥 사정에 흔들리지 않는다.
파이썬의 `unittest` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 검사장 | `unittest.TestCase` 를 상속한 테스트 클래스 |
| 검사 항목 하나 | `test_` 로 시작하는 메서드 하나 |
| 「이 값이어야 한다」 판정 | `assertEqual` · `assertTrue` 같은 assert 메서드 |
| 검사대마다 차를 새로 세움 · 치움 | `setUp` · `tearDown` (테스트마다) |
| 조명을 하루 한 번 켬 · 끔 | `setUpClass` · `tearDownClass` (클래스당 한 번) |
| 모형 부품 | `Mock` · `MagicMock` |
| 진짜 부품 자리에 모형을 끼우기 | `patch` |
| 같은 항목을 여러 차종에 따로 재기 | `subTest` |
| 오늘은 이 항목 건너뜀 | `@unittest.skip` · `@unittest.skipIf` |
| 검사 일지 | `TextTestRunner` 가 돌려준 결과 객체 |

```text
 [setUpClass] ─────────────── 클래스당 한 번
     │
     ├─ setUp → test_a → tearDown
     ├─ setUp → test_b → tearDown      테스트마다 한 번씩
     └─ setUp → test_c → tearDown
     │
 [tearDownClass] ──────────── 클래스당 한 번
```

> **단위 테스트** — 프로그램의 작은 조각(함수 · 메서드) 하나를 떼어 내어 기대한 대로 도는지 확인하는 코드다.\
> 예: `add(2, 3)` 이 `5` 를 돌려주는지 확인하는 메서드 하나.

## 이 주제가 답하려는 질문

1. 테스트 하나는 어떤 꼴로 쓰고, 통과와 실패는 무엇으로 가르나?
2. 테스트끼리 서로 오염되지 않게 준비와 정리를 어디에 두나?
3. 네트워크 · 파일처럼 바깥에 기대는 코드를 바깥 없이 어떻게 시험하나?
4. 여러 케이스 · 건너뛸 테스트 · 실행과 집계는 어떻게 다루나?

## 동작 방식

### (1) TestCase 와 assert 메서드

**언제 쓰나** — 함수가 돌려준 값이 기대와 같은지 판정할 때 쓴다.

```text
class TestCalculator(unittest.TestCase):
    def test_add(self):
        self.assertEqual(calc.add(2, 3), 5)
            │
            ▼
  calc.add(2, 3) 이 5 를 돌려줌 → 5 == 5 → 아무 일 없음 → 이 테스트는 통과
  (만약 6 이면) → AssertionError 가 남 → 이 테스트는 실패, 양쪽 값이 메시지에 실림
```

- `TestCase` 를 상속한 클래스 안에서 이름이 `test` 로 시작하는 메서드가 테스트 하나가 된다.
- assert 메서드는 조건이 맞으면 조용히 지나가고, 틀리면 예외를 던져 그 테스트를 실패로 만든다.
- 한 메서드 안에서 첫 assert 가 실패하면 그 아래 줄은 실행되지 않는다.
- `assertEqual` 은 실패할 때 양쪽 값을 메시지에 함께 보여 준다.
- 그냥 `assert a == b` 문도 실패하면 `AssertionError` 를 내서 실패로 잡히지만, 양쪽 값이 메시지에 실리지 않는다.

원본이 쓰는 assert 메서드는 이렇다.

| 메서드 | 판정 |
|---|---|
| `assertEqual(a, b)` | `a == b` |
| `assertAlmostEqual(a, b, places=n)` | 부동소수 비교 — `a - b` 를 소수점 `n` 자리로 반올림한 값이 `0` 인가 |
| `assertRaises(예외)` | 블록 안에서 그 예외가 나는가 (`with ... as ctx` 로 예외 객체를 받는다) |
| `assertTrue(x)` · `assertFalse(x)` | `x` 가 참인가 · 거짓인가 |
| `assertIn(a, b)` · `assertNotIn(a, b)` | `a` 가 `b` 안에 있는가 · 없는가 (부분 문자열도 된다) |
| `assertIsInstance(obj, 클래스)` | `obj` 가 그 클래스의 인스턴스인가 |
| `assertIsNone(x)` · `assertIsNotNone(x)` | `x` 가 `None` 인가 · 아닌가 |
| `assertGreater` · `assertLess` · `assertGreaterEqual` | `>` · `<` · `>=` |

`assertAlmostEqual(10 / 3, 3.333, places=3)` 의 판정은 이렇게 흐른다.

```text
10 / 3        = 3.3333333…
3.3333333… - 3.333 = 0.0003333…
소수점 3자리로 반올림 → 0.0   → 0 과 같다 → 통과
```

`assertRaises` 는 `with` 블록과 함께 쓴다.

```text
with self.assertRaises(ValueError) as ctx:
    calc.divide(10, 0)          → ValueError("Cannot divide by zero") 가 남
        │
        ▼
블록을 빠져나올 때 예외가 ValueError 인지 확인 → 맞으면 통과, 예외를 삼킨다
ctx.exception 에 그 예외 객체가 남는다 → str(ctx.exception) 에 'zero' 가 있는지 assertIn 으로 확인
```

- 블록 안에서 예외가 나지 않으면 그 테스트는 실패한다.
- 예외 객체를 `ctx.exception` 으로 받아 메시지까지 검사할 수 있다.

> **assert 메서드** — `TestCase` 가 주는 판정 메서드로, 조건이 틀리면 테스트를 실패시킨다.\
> 예: `self.assertIn('zero', 메시지)`.

### (2) 테스트마다 준비하기 · 클래스당 한 번 준비하기

**언제 쓰나** — 테스트끼리 상태를 나누지 않게 할 때(`setUp`), 비싼 자원을 한 번만 만들 때(`setUpClass`) 쓴다.

```text
class TestCalculator:                       class TestWithClassSetup:
  setUp:  self.calc = Calculator()            @classmethod setUpClass(cls):
                                                 임시 디렉터리 + test.txt 생성
  test_add      ← 새 calc                    test_file_exists   ┐ 같은 파일을
  test_divide   ← 또 새 calc                 test_file_content  ┘ 함께 씀
  …                                          @classmethod tearDownClass(cls):
                                                 디렉터리를 통째로 지움
```

- `setUp` 은 테스트 메서드 하나가 돌기 직전마다 불린다.
- 그래서 테스트 여섯 개면 `Calculator` 도 여섯 번 새로 만들어진다 — 한 테스트가 객체 상태를 바꿔도 다음 테스트에 새지 않는다(테스트 격리).
- `tearDown` 은 테스트 하나가 끝난 뒤마다 불린다. 원본에서는 비어 있고 「리소스 정리」 자리만 표시한다.
- `setUpClass` 는 그 클래스의 테스트가 시작되기 전에 **한 번**, `tearDownClass` 는 모두 끝난 뒤 **한 번** 불린다.
- 둘은 `@classmethod` 로 꾸며야 하며, 첫 인자는 `self` 가 아니라 `cls` 다.
- `cls.filepath` 처럼 클래스 속성에 담으면 각 테스트에서 `self.filepath` 로 읽을 수 있다.
- 원본은 `tempfile.mkdtemp()` 로 임시 디렉터리를 만들고, `shutil.rmtree` 로 그 안까지 재귀적으로 지운다.

> **테스트 격리** — 한 테스트의 결과가 다른 테스트가 남긴 상태에 기대지 않도록 떼어 놓는 것이다.\
> 예: 테스트마다 `Calculator()` 를 새로 만든다.

> **픽스처(fixture)** — 테스트가 돌기 전에 마련해 두는 준비물이다.\
> 예: `setUpClass` 가 만든 임시 파일 `test.txt`.

### (3) Mock — 무엇이든 받아 주는 가짜 객체

**언제 쓰나** — 진짜 객체 대신 원하는 값을 돌려주고, 어떻게 불렸는지 기록할 가짜가 필요할 때 쓴다.

```text
mock = Mock()
mock.method.return_value = 42    → mock.method 라는 속성이 그 자리에서 만들어짐
mock.method()                    → 42 를 돌려주고, 「인자 없이 1번 불림」을 기록
mock.method.assert_called_once() → 기록을 보니 정확히 1번 → 통과
```

- `Mock` 은 아직 없는 속성이나 메서드에 접근해도 그 자리에서 새 Mock 을 만들어 준다.
- `return_value` 는 불렸을 때 돌려줄 값이다.
- `side_effect` 에 리스트를 넣으면 호출마다 다음 값을 차례로 돌려준다 — `[1, 2, 3]` 이면 1, 2, 3.
- 리스트가 바닥난 뒤 또 부르면 돌려줄 값이 없어 `StopIteration` 이 난다.
- `side_effect` 에 예외(`ValueError("error!")`)를 넣으면 부를 때 그 예외가 난다.

호출 기록은 이렇게 쌓인다.

```text
mock(1, 2, key='value')   → 기록 1: call(1, 2, key='value')
mock(3, 4)                → 기록 2: call(3, 4)

assert_called_with(3, 4)                       → 「마지막」 호출만 본다 → 통과
assert_has_calls([call(1,2,key='value'), call(3,4)]) → 이 호출들이 이 차례로 있었나 → 통과
call_count                                     → 2
```

- `assert_called_once_with(123)` 은 「정확히 한 번, 그 인자로」 불렸는지 본다.
- `call(...)` 은 기대하는 호출 꼴을 적는 도우미다.

`MagicMock` 은 `Mock` 에 매직 메서드까지 마련해 둔 것이다.

```text
mock = MagicMock()
mock.__len__.return_value = 5        → len(mock) 이 5
mock.__getitem__.return_value = 'value' → mock[0] 이 'value'
```

- `len()` · `[]` 같은 문법은 객체의 `__len__` · `__getitem__` 을 부른다.
- 평범한 `Mock` 은 이런 매직 메서드를 자동으로 마련하지 않으므로 `len(Mock())` 은 `TypeError` 가 난다(원본에 근거 없음 — 추론).

> **Mock 객체** — 진짜 객체 자리를 대신 채우며 돌려줄 값을 정할 수 있고 불린 기록을 남기는 가짜 객체다.\
> 예: `Mock()` · `MagicMock()`.

> **매직 메서드** — `__len__` 처럼 앞뒤에 밑줄 둘이 붙어 `len()` · `[]` 같은 문법이 대신 부르는 메서드다.\
> 예: `len(x)` 는 `x.__len__()` 을 부른다.

### (4) patch — 이름 하나를 잠깐 가짜로 바꿔 끼우기

**언제 쓰나** — API · DB · 파일 시스템처럼 바깥에 기대는 부분을 격리할 때 쓴다. 원본 팁은 이때 「필수」라고 한다.

```text
@patch('__main__.get_user_data')           ← 「__main__ 모듈의 get_user_data 라는 이름」
def test_process_user(self, mock_get):     ← 바꿔 끼운 Mock 이 인자로 들어옴
    mock_get.return_value = b'{"name": "Alice"}'
    process_user(123)
        │  process_user 안에서 get_user_data 를 찾음
        ▼  → 지금 그 이름에 걸려 있는 것은 mock_get
    mock_get(123) → b'{"name": "Alice"}'  (네트워크에 나가지 않음)
        │
        ▼
    f"Processed: {data}" → "Processed: b'{\"name\": \"Alice\"}'"
테스트가 끝나면 → 이름을 원래 함수로 되돌림
```

- `patch('모듈.이름')` 은 그 모듈의 그 이름을 테스트 동안만 `MagicMock` 으로 바꾸고, 끝나면 되돌린다.
- 데코레이터로 쓰면 바꿔 끼운 Mock 이 테스트 메서드의 인자로 들어온다.
- `process_user` 는 부를 때마다 자기 모듈에서 `get_user_data` 라는 이름을 찾는다. 그래서 그 모듈의 이름을 바꾸면 가짜가 불린다.
- 경로는 「정의된 위치」가 아니라 「쓰이는 위치」를 적는다. `a.py` 가 `b` 모듈을 쓰면 `'a.b'` 로 patch 한다.
- `'__main__.…'` 경로는 그 파일을 스크립트로 직접 돌려 모듈 이름이 `__main__` 일 때만 맞는다.
- f-string 에 `bytes` 를 넣으면 `b'...'` 꼴 그대로 문자열에 들어간다. 그래서 기대 문자열에도 `b'…'` 가 들어 있다.

> **patch** — 지정한 경로의 이름을 테스트 동안만 Mock 으로 바꿔 끼우고, 끝나면 원래대로 돌려놓는 도구다.\
> 예: `@patch('__main__.get_user_data')`.

### (5) subTest — 한 메서드 안의 여러 케이스를 따로 판정

**언제 쓰나** — 같은 검사를 여러 입력에 돌리면서, 하나가 틀려도 나머지를 계속 보고 싶을 때 쓴다.

```text
for num, expected in [(2,True), (4,True), (5,False), (8,True)]:
    with self.subTest(num=num):
        assertEqual(num % 2 == 0, expected)

subTest 가 있으면                       subTest 가 없으면
 num=2 판정 → num=4 판정                 num=2 판정 → num=4 실패 → 메서드 끝
 → num=5 판정 → num=8 판정               (5, 8 은 검사되지 않음)
 실패한 칸은 num=… 표지를 달고 따로 보고
```

- `subTest` 블록 안의 실패는 그 블록에서 멈추고, 반복문은 다음 케이스로 넘어간다.
- `num=num` 처럼 넘긴 키워드는 실패 보고에 붙어서 어느 케이스가 틀렸는지 알려 준다.

> **subTest** — 한 테스트 메서드 안에서 케이스 하나하나를 따로 판정하게 해 주는 컨텍스트 매니저다.\
> 예: `with self.subTest(num=5): …`.

### (6) skip · skipIf — 건너뛰기

**언제 쓰나** — 아직 구현되지 않았거나 조건(환경 등)이 안 맞아 돌리지 않을 테스트에 쓴다.

```text
@unittest.skip("아직 구현 안 됨")      → 무조건 건너뜀
@unittest.skipIf(True, "조건부 스킵")  → 첫 인자가 참이면 건너뜀
        │
        ▼
메서드 본문은 실행되지 않음 → 결과의 skipped 목록에 이유와 함께 들어감
```

- 건너뛴 테스트는 실패나 에러로 세지 않고 `skipped` 로 따로 센다.

### (7) 실행 — 모으고, 묶고, 돌리고, 센다

**언제 쓰나** — 파일 안에서 테스트 클래스를 골라 직접 돌리고 결과를 집계할 때 쓴다.

```text
TestLoader().loadTestsFromTestCase(TestCalculator)  → test_* 메서드를 모아 테스트 묶음으로
TestSuite().addTests(...)  × 5 클래스               → 하나의 큰 묶음
TextTestRunner(verbosity=2).run(suite)              → 테스트마다 한 줄씩 보고하며 돌림
        │
        ▼
result.testsRun        돌린 테스트 수
result.failures        assert 가 틀린 것들
result.errors          assert 밖에서 예외가 난 것들
result.skipped         건너뛴 것들
```

- `loadTestsFromTestCase` 는 클래스의 `test_*` 메서드를 모두 모은다.
- `verbosity=2` 는 테스트마다 이름과 결과를 한 줄씩 보여 준다.
- 실패(failure)는 판정이 틀린 것이고, 에러(error)는 판정 전에 예상치 못한 예외가 난 것이다.

> **테스트 스위트** — 여러 테스트를 하나로 묶어 한꺼번에 돌리는 묶음이다.\
> 예: `unittest.TestSuite()` 에 다섯 클래스를 넣은 것.

## 문법 — 형태와 규칙

```python
import unittest
from unittest.mock import Mock

class TestGreet(unittest.TestCase):
    def setUp(self):
        self.names = ['a', 'b']          # 테스트마다 새로

    def test_len(self):
        self.assertEqual(len(self.names), 2)

    def test_mock(self):
        m = Mock(return_value='hi')
        self.assertEqual(m('x'), 'hi')
        m.assert_called_once_with('x')

if __name__ == '__main__':
    unittest.main()
```

- 테스트 클래스는 `unittest.TestCase` 를 상속한다.
- 테스트 메서드 이름은 `test` 로 시작한다.
- 판정은 `self.assertXxx(...)` 로 한다.
- 준비 · 정리는 `setUp(self)` · `tearDown(self)`, 클래스당 한 번은 `@classmethod` + `setUpClass(cls)` · `tearDownClass(cls)` 다.
- 예외 검사는 `with self.assertRaises(예외) as ctx:` 블록으로 한다.
- 가짜는 `Mock()` · `MagicMock()`, 바꿔 끼우기는 `@patch('쓰이는모듈.이름')` 이다.
- Mock 의 동작은 `return_value` · `side_effect` 로, 확인은 `assert_called_once()` · `assert_called_once_with(...)` · `assert_called_with(...)` · `assert_has_calls([...])` · `call_count` 로 한다.
- 여러 케이스는 `with self.subTest(키=값):`, 건너뛰기는 `@unittest.skip(이유)` · `@unittest.skipIf(조건, 이유)` 다.
- 직접 돌릴 때는 `TestLoader` → `TestSuite` → `TextTestRunner(verbosity=2).run(...)` 순서다.

## 어디서 틀리나

### 1. setUp 과 setUpClass 를 헷갈린다

`setUp` · `tearDown` 은 테스트마다, `setUpClass` · `tearDownClass` 는 클래스당 한 번 돈다.
바뀌는 상태(객체)를 `setUpClass` 에 두면 테스트끼리 그 상태를 나눠 가져 서로 오염된다.
반대로 비싼 자원(DB 연결 · 임시 파일)을 `setUp` 에 두면 테스트마다 다시 만들어 느려진다.

### 2. setUpClass 에 `@classmethod` 를 빼먹는다

`setUpClass` · `tearDownClass` 는 인스턴스 없이 클래스에 대고 불린다.
그래서 `@classmethod` 가 필수이고 첫 인자는 `cls` 다.

### 3. patch 경로를 정의된 곳으로 적는다

`patch` 는 「쓰이는 위치」의 이름을 바꾼다.
`a.py` 에서 `b` 모듈을 쓰면 `'b.…'` 가 아니라 `'a.b'` 로 patch 한다.
원본의 `'__main__.get_user_data'` 는 파일을 스크립트로 돌릴 때만 맞다 — 다른 모듈에서 import 해 돌리면 모듈 이름이 달라 경로를 고쳐야 한다.

### 4. assertEqual 의 인자 순서

원본 함정은 「`(actual, expected)` 가 권장이지만 일부는 `(expected, actual)` 이라 메시지가 헷갈릴 수 있다」고 한다.
`assertEqual` 은 두 값이 같은지만 보므로 순서가 바뀌어도 판정은 같다.
다만 실패 메시지에 어느 쪽이 실제 값인지가 순서에 따라 읽힌다.

### 5. side_effect 리스트를 다 쓰고 또 부른다

`side_effect = [1, 2, 3]` 이면 네 번째 호출에서 `StopIteration` 이 난다.
Mock 을 몇 번 부를지 리스트 길이와 맞춰야 한다.

### 6. 부동소수를 assertEqual 로 비교한다

`10 / 3` 은 `3.333` 과 정확히 같지 않다.
`assertAlmostEqual(…, places=n)` 으로 자릿수를 정해 비교한다.
`places` 를 올리면 더 엄격해진다 — `places=4` 면 차이 `0.0003…` 이 `0.0003` 으로 반올림되어 0 이 아니게 된다.

### 7. 반복문에서 subTest 없이 assert 한다

subTest 없이 반복문 안에서 assert 하면 첫 실패에서 메서드가 끝나 뒤 케이스는 검사되지 않는다.

### 8. 원본 주석의 실행 결과 목록

원본의 주장 → 「15개를 돌리고 `OK (skipped=2)`, 테스트 이름이 정의한 순서대로 `... ok` 로 나온다」.
왜 의심스러운가 →
- 다섯 클래스의 `test_` 메서드를 세면 6 + 2 + 5 + 1 + 2 = **16** 개다(아래 표). 15 와 맞지 않는다.
- 목록에 `test_magic_mock` · `test_side_effect` · `test_call_args` · `test_even_numbers` · `test_conditional` 이 빠져 있고, 마지막 `print` 의 「테스트 결과: …」 줄도 없다.
- `loadTestsFromTestCase` 는 기본적으로 메서드를 이름순으로 정렬해 모으므로 정의한 순서와 다를 수 있다(확인 필요).
- 건너뛴 줄의 꼴 · 테스트 이름 옆 클래스 표기 · 걸린 시간은 파이썬 버전과 환경에 따라 달라진다(확인 필요).

| 클래스 | `test_` 메서드 수 |
|---|---|
| `TestCalculator` | 6 |
| `TestWithClassSetup` | 2 |
| `TestWithMock` | 5 |
| `TestSubTest` | 1 |
| `TestSkip` | 2 |

### 9. 파일 이름을 `unittest.py` 로 짓는다

스크립트를 돌리면 그 파일이 있는 폴더가 모듈 검색 경로의 맨 앞에 온다.
그래서 `import unittest` 가 표준 라이브러리 대신 자기 파일을 가져와 `unittest.TestCase` 를 찾지 못할 수 있다(원본에 근거 없음 — 추론).
연습 파일은 `test_calc.py` 처럼 다른 이름으로 짓는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `setUp` 은 테스트마다, `setUpClass` 는 클래스당 한 번 돈다 | `unittest` 표준 라이브러리의 문서화된 동작 |
| `patch` 는 끝나면 원래 이름으로 되돌린다 | `unittest.mock` 의 문서화된 동작 |
| `Mock` 은 없는 속성을 자동으로 만든다 · `MagicMock` 은 매직 메서드까지 마련한다 | `unittest.mock` 의 문서화된 동작 |
| f-string 에 `bytes` 를 넣으면 `b'…'` 꼴이 된다 | 언어 — `bytes` 의 문자열 변환 규칙 |
| `loadTestsFromTestCase` 가 메서드를 이름순으로 모은다 | `TestLoader` 의 기본 설정 — 바꿀 수 있다(확인 필요) |
| `verbosity=2` 의 한 줄 형식 · 건너뜀 표기 | 파이썬 버전마다 다르다(확인 필요) |
| 걸린 시간(원본의 `0.01s`) | 실행 환경에 따라 다르다 — 보장 없음 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 추가 설치 없이 테스트를 쓰고 싶다 | `unittest` (표준 라이브러리) | — |
| 테스트를 더 짧게 쓰고 싶고 설치가 괜찮다 | `pytest` (원본 팁: 실무에서 더 간결) | — |
| 테스트마다 새 객체가 필요하다 | `setUp` | `setUpClass` (상태가 샌다) |
| 임시 파일 · DB 연결처럼 비싼 자원 | `setUpClass` · `tearDownClass` | `setUp` (매번 다시 만든다) |
| 네트워크 · DB · 파일 시스템 호출 | `patch` + `Mock` | 진짜 호출 (느리고 결과가 흔들린다) |
| `len()` · `[]` 를 흉내 내야 한다 | `MagicMock` | `Mock` |
| 같은 검사를 여러 입력에 | `subTest` | 맨 반복문 + assert |
| 부동소수 비교 | `assertAlmostEqual` | `assertEqual` |

## 핵심 문장

1. **테스트는 `TestCase` 의 `test_*` 메서드이고, assert 메서드가 틀리면 그 테스트가 실패한다.**
2. **`setUp` 은 테스트마다, `setUpClass` 는 클래스당 한 번 — 격리냐 비용이냐로 고른다.**
3. **`patch` 는 「쓰이는 위치」의 이름을 테스트 동안만 Mock 으로 바꿔 바깥 의존성을 끊는다.**
4. **Mock 은 돌려줄 값(`return_value` · `side_effect`)을 정하고, 불린 기록(`assert_called_*` · `call_count`)으로 검사한다.**
5. **`subTest` 는 케이스를 따로 판정해 하나가 틀려도 나머지를 계속 본다.**

## 관련 자료

- [pytest-basics](../15-pytest-basics/2-summary.md)
- `abc-module` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `dataclasses-advanced` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/stdlib.json` 의 `unittest`

## 용어 풀이

- **단위 테스트** — 작은 코드 조각 하나가 기대대로 도는지 확인하는 코드.
- **TestCase** — 테스트 클래스가 상속하는 기반 클래스로, assert 메서드와 준비 · 정리 고리를 준다.
- **assert 메서드** — 조건이 틀리면 테스트를 실패시키는 `TestCase` 의 판정 메서드.
- **테스트 격리** — 테스트끼리 상태를 나누지 않게 떼어 놓는 것.
- **픽스처** — 테스트 전에 마련해 두는 준비물.
- **Mock 객체** — 진짜 대신 쓰는 가짜로, 돌려줄 값을 정하고 호출을 기록한다.
- **MagicMock** — 매직 메서드까지 마련된 Mock.
- **매직 메서드** — `len()` · `[]` 같은 문법이 대신 부르는 `__이름__` 꼴의 메서드.
- **return_value** — Mock 이 불렸을 때 돌려줄 값.
- **side_effect** — 호출마다 차례로 돌려줄 값의 목록, 또는 부를 때 던질 예외.
- **patch** — 지정 경로의 이름을 테스트 동안만 Mock 으로 바꾸고 되돌리는 도구.
- **subTest** — 한 메서드 안의 케이스를 따로 판정하게 하는 컨텍스트 매니저.
- **테스트 스위트** — 여러 테스트를 묶어 한꺼번에 돌리는 묶음.
- **failure / error** — 판정이 틀린 것 / 판정 밖에서 예외가 난 것.

## 더 들어가면

- `tearDown` 은 테스트가 실패해도 `setUp` 이 성공했다면 불린다 (확인 필요).
- `self.addCleanup(함수)` 로 정리 동작을 등록하면 `setUp` 도중 실패해도 정리가 돌게 할 수 있다 (확인 필요).
- `patch` 는 데코레이터 말고 `with patch('…') as m:` 컨텍스트로도 쓸 수 있다 (확인 필요).
- `patch(..., autospec=True)` 나 `create_autospec` 을 쓰면 진짜 함수의 인자 꼴을 따르는 Mock 이 되어 엉뚱한 인자로 부른 실수를 잡는다 (확인 필요).
- 최근 버전의 Mock 은 `assert` 로 시작하는 오타 속성(`assret_called` 등)에 접근하면 자동 생성 대신 `AttributeError` 를 낸다 (확인 필요).
- 명령줄에서 `python -m unittest` 로 돌리면 `test*.py` 파일을 찾아 돌리는 자동 탐색을 쓸 수 있다 (확인 필요).
- `pytest` 는 맨 `assert` 문을 고쳐 써서 실패 때도 양쪽 값을 보여 주고, `unittest` 로 쓴 테스트도 대체로 그대로 돌린다 (확인 필요).
- `TextTestRunner` 의 기본 출력 대상은 표준 오류(`stderr`)다 (확인 필요).
