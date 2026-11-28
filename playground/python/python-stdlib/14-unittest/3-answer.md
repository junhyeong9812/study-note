# python/python-stdlib/14 — unittest (단위 테스트) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `b'…'` 꼴이 그대로 문자열에 들어가고, 호출 확인은 통과한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`result` 는 `Processed: b'{"name": "Alice"}'` 다 — 파이썬 문자열 리터럴로 쓰면 `"Processed: b'{\"name\": \"Alice\"}'"` 이다.
`assert_called_once_with(123)` 은 통과한다.

**왜 그런가**
`patch` 가 `__main__` 모듈의 `get_user_data` 이름을 Mock 으로 바꿔 끼웠으므로, `process_user` 안의 호출은 네트워크에 나가지 않고 `return_value` 인 bytes 를 받는다.
f-string 에 bytes 를 넣으면 `b'…'` 꼴 그대로 문자열이 된다.
`process_user(123)` 이 Mock 을 `123` 으로 딱 한 번 불렀으므로 호출 기록도 맞는다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (3)」.

### 2. 네 번째 호출은 `StopIteration` 을 낸다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
앞의 세 번은 `1`, `2`, `3` 을 돌려주고, 네 번째 호출에서 `StopIteration` 이 난다.

**왜 그런가**
`side_effect` 에 리스트를 넣으면 호출마다 다음 값을 꺼내 돌려준다.
세 값을 다 꺼낸 뒤에는 꺼낼 값이 없으므로 `StopIteration` 이 난다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 3. `setUpClass` 1번, `setUp` 3번

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`setUpClass` 는 1번, `setUp` 은 3번 불린다.

**왜 그런가**
`setUpClass` 는 클래스의 테스트가 시작되기 전에 한 번만 돈다.
`setUp` 은 테스트 메서드 하나가 돌기 직전마다 도므로 `test_a` · `test_b` · `test_c` 앞에서 한 번씩, 모두 세 번이다.
근거: 2-summary 「동작 방식 (2)」.

### 4. 계산기는 격리, 임시 파일은 비용

`Calculator` 는 테스트가 상태를 바꿀 수 있는 객체라, 매번 새로 만들어야 한 테스트의 흔적이 다음 테스트에 새지 않는다(테스트 격리).
임시 디렉터리와 파일은 만들고 지우는 데 품이 들고, 두 테스트가 읽기만 하므로 클래스당 한 번 만들어 함께 쓰는 편이 낫다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 바꿔야 하는 것은 「호출하는 쪽이 찾는 이름」이다

`patch` 는 지정한 모듈의 이름 하나를 Mock 으로 바꿔 끼운다.
테스트 대상 함수는 부를 때 **자기 모듈**에서 그 이름을 찾는다.
그래서 쓰는 쪽 모듈의 이름을 바꿔야 가짜가 불린다 — `a.py` 가 `b` 모듈을 쓰면 `'a.b'` 로 patch 한다.
원본의 `'__main__.get_user_data'` 도 `process_user` 가 쓰는 위치가 `__main__` 이라서 그렇게 적은 것이다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 6. `places=4` 면 실패한다

`assertAlmostEqual` 은 두 값의 차이를 소수점 `places` 자리로 반올림해 0 인지 본다.
`10 / 3 - 3.333` 은 `0.0003…` 이다.
3자리로 반올림하면 `0.0` 이라 통과하고, 4자리로 반올림하면 `0.0003` 이라 0 이 아니어서 실패한다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 6」.

### 7. subTest 가 있으면 뒤 케이스도 검사되고, 없으면 거기서 멈춘다

`subTest` 블록 안의 실패는 그 케이스에서만 멈추고 반복문은 다음으로 넘어가므로, `5` 와 `8` 도 검사된다.
틀린 `num=4` 케이스는 `num=4` 표지를 달고 따로 실패로 보고된다.
`subTest` 를 빼면 `num=4` 에서 난 `AssertionError` 가 메서드 전체를 끝내 `5` 와 `8` 은 검사되지 않는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 7」.

### 8. 문법은 매직 메서드를 부르고, MagicMock 만 그것을 마련해 둔다

`len(x)` 는 `x.__len__()` 을, `x[0]` 은 `x.__getitem__(0)` 을 부른다.
`MagicMock` 은 이런 매직 메서드까지 미리 마련해 `return_value` 를 걸 수 있게 한다.
평범한 `Mock` 은 매직 메서드를 자동으로 마련하지 않아 `len(Mock())` 이 `TypeError` 가 난다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (3)」.

### 9. 설치가 필요 없다 · 실패 때 양쪽 값이 보인다

`unittest` 는 표준 라이브러리라 따로 설치할 것이 없다 — 원본 팁은 `pytest` 가 더 간결하지만 이 점에서 `unittest` 가 낫다고 한다.
`assertEqual` 은 실패할 때 양쪽 값을 메시지에 실어 주므로 무엇이 어떻게 달랐는지 바로 보인다.
맨 `assert` 문은 실패로는 잡히지만 메시지에 양쪽 값이 실리지 않는다.
근거: 2-summary 「언제 쓰고 언제 안 쓰나」 · 「동작 방식 (1)」.

### 10. 건너뜀(`skipped`)으로 따로 센다

조건이 참이면 메서드 본문이 실행되지 않고, 결과 객체의 `skipped` 목록에 이유와 함께 들어간다.
실패(`failures`)나 에러(`errors`)로는 세지 않는다.
근거: 2-summary 「동작 방식 (6)」 · 「동작 방식 (7)」.

## 실습 정답

### 실습 1. 계산기 · 파일 · 가짜 API 를 시험하는 테스트 파일 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 테스트마다 새 계산기 · 정리 자리 | `TestCalculator.setUp` 의 `self.calc = Calculator()` · `tearDown` 의 `pass` |
| 2. 덧셈 확인 | `test_add` 의 `assertEqual` 두 줄 |
| 3. 소수점 3자리 비교 | `test_divide` 의 `assertAlmostEqual(..., places=3)` |
| 4. 예외와 메시지 | `test_divide_by_zero` 의 `with self.assertRaises(ValueError) as ctx` · `assertIn('zero', str(ctx.exception))` |
| 5. 참 · 거짓 | `test_is_positive` 의 `assertTrue` · `assertFalse` |
| 6. 포함 · 타입 · None | `test_collections` 의 `assertIn` · `assertNotIn` · `assertIsInstance` · `assertIsNone` · `assertIsNotNone` |
| 7. 크기 비교 | `test_comparisons` 의 `assertGreater` · `assertLess` · `assertGreaterEqual` |
| 8. 임시 디렉터리와 파일 | `@classmethod setUpClass` 의 `tempfile.mkdtemp()` · `cls.filepath` · `f.write('test content')` |
| 9. 디렉터리 지우기 | `@classmethod tearDownClass` 의 `shutil.rmtree(cls.tmpdir)` |
| 10. 파일 존재 · 내용 | `test_file_exists` 의 `os.path.exists` · `test_file_content` 의 `assertEqual(f.read(), 'test content')` |
| 11. patch 와 호출 확인 | `@patch('__main__.get_user_data')` · `mock_get.return_value` · `assert_called_once_with(123)` |
| 12. 기본 Mock | `test_mock_basic` 의 `mock.method.return_value = 42` · `assert_called_once()` |
| 13. 매직 메서드 | `test_magic_mock` 의 `mock.__len__.return_value` · `mock.__getitem__.return_value` |
| 14. 차례 값 · 예외 | `test_side_effect` 의 `side_effect = [1, 2, 3]` · `side_effect = ValueError("error!")` |
| 15. 호출 기록 | `test_call_args` 의 `assert_called_with(3, 4)` · `assert_has_calls(expected_calls)` · `call_count` |
| 16. 케이스마다 판정 | `test_even_numbers` 의 `with self.subTest(num=num)` |
| 17. 건너뛰기 | `@unittest.skip("아직 구현 안 됨")` · `@unittest.skipIf(True, "조건부 스킵")` |
| 18. 모아서 돌리기 | `TestLoader` · `TestSuite.addTests(loader.loadTestsFromTestCase(...))` × 5 · `TextTestRunner(verbosity=2).run(suite)` |
| 19. 집계 한 줄 | 마지막 `print` 의 `result.testsRun` · `len(result.failures)` · `len(result.errors)` · `len(result.skipped)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-stdlib/reference/unittest.py`

```python
# [표준 라이브러리] unittest (단위 테스트)
# 설명: TestCase, assert 메서드, setUp/tearDown, mock.patch로 단위 테스트 작성
# 팁: setUp/tearDown은 각 테스트마다, setUpClass/tearDownClass는 클래스당 한 번 실행된다. mock.patch는 외부 의존성(API, DB, 파일시스템)을 격리할 때 필수이다. subTest를 사용하면 하나의 케이스가 실패해도 나머지가 계속 실행된다. 실무에서는 pytest가 더 간결하지만, unittest는 표준 라이브러리라 별도 설치가 필요 없다.
# 함정: patch의 경로는 "정의된 위치"가 아닌 "사용되는 위치" (예: a.py에서 b 모듈 사용 시 'a.b'로 patch). setUpClass/tearDownClass는 @classmethod 필수. assertEqual 인자 순서는 (actual, expected) 권장이지만 일부는 (expected, actual)이라 메시지가 헷갈릴 수 있음.

# 표준 단위 테스트 프레임워크
import unittest
# Mock 객체와 patch 데코레이터/컨텍스트
from unittest.mock import patch, MagicMock, Mock, call
# 임시 파일/디렉토리
import tempfile
import os

# === 테스트 대상 코드 ===
# 단순 계산기 클래스
class Calculator:
    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def is_positive(self, n):
        return n > 0

# === 기본 TestCase ===
# unittest.TestCase 상속하여 테스트 클래스 작성
class TestCalculator(unittest.TestCase):

    def setUp(self):
        """각 테스트 전에 실행"""
        # 매 테스트마다 새 인스턴스 → 테스트 격리
        self.calc = Calculator()

    def tearDown(self):
        """각 테스트 후에 실행"""
        pass  # 리소스 정리

    # === assert 메서드 ===
    # assertEqual: a == b 검증 (실패 시 양쪽 값 출력)
    def test_add(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)

    # assertAlmostEqual: 부동소수 비교 (places=소수점 자릿수)
    def test_divide(self):
        self.assertAlmostEqual(self.calc.divide(10, 3), 3.333, places=3)

    # assertRaises: 예외 발생 검증 (컨텍스트 매니저로 예외 객체 접근)
    def test_divide_by_zero(self):
        with self.assertRaises(ValueError) as ctx:
            self.calc.divide(10, 0)
        # assertIn: 부분 문자열/요소 포함 검증
        self.assertIn('zero', str(ctx.exception))

    # assertTrue/assertFalse: bool 검증
    def test_is_positive(self):
        self.assertTrue(self.calc.is_positive(1))
        self.assertFalse(self.calc.is_positive(-1))

    # 컬렉션 관련 assert
    def test_collections(self):
        self.assertIn(3, [1, 2, 3])
        self.assertNotIn(4, [1, 2, 3])
        # assertIsInstance: 타입 검증
        self.assertIsInstance(self.calc, Calculator)
        # assertIsNone/assertIsNotNone: None 검증
        self.assertIsNone(None)
        self.assertIsNotNone(self.calc)

    # 비교 관련 assert
    def test_comparisons(self):
        self.assertGreater(5, 3)
        self.assertLess(3, 5)
        self.assertGreaterEqual(5, 5)

# === setUpClass / tearDownClass ===
# 클래스 단위 setup/teardown - 비싼 리소스(DB 연결, 임시 파일) 한 번만 생성
class TestWithClassSetup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """클래스 전체에서 한 번 실행"""
        # cls 사용 (self 아님)
        cls.tmpdir = tempfile.mkdtemp()
        cls.filepath = os.path.join(cls.tmpdir, 'test.txt')
        with open(cls.filepath, 'w') as f:
            f.write('test content')

    @classmethod
    def tearDownClass(cls):
        # 임시 디렉토리 재귀 삭제
        import shutil
        shutil.rmtree(cls.tmpdir)

    def test_file_exists(self):
        self.assertTrue(os.path.exists(self.filepath))

    def test_file_content(self):
        with open(self.filepath) as f:
            self.assertEqual(f.read(), 'test content')

# === Mock / patch ===
# 외부 API 호출 함수 (실제 네트워크 호출은 테스트에서 회피해야 함)
def get_user_data(user_id):
    """외부 API 호출 시뮬레이션"""
    import urllib.request
    response = urllib.request.urlopen(f'https://api.example.com/users/{user_id}')
    return response.read()

# 테스트 대상 함수 - get_user_data를 사용
def process_user(user_id):
    data = get_user_data(user_id)
    return f"Processed: {data}"

class TestWithMock(unittest.TestCase):

    # patch: 지정된 경로의 객체를 Mock으로 교체 (테스트 종료 후 자동 복원)
    # '__main__.get_user_data': 사용되는 위치 기준 경로
    @patch('__main__.get_user_data')
    def test_process_user(self, mock_get):
        # return_value: mock 호출 시 반환값 설정
        mock_get.return_value = b'{"name": "Alice"}'
        result = process_user(123)
        self.assertEqual(result, "Processed: b'{\"name\": \"Alice\"}'")
        # assert_called_once_with: 정확히 1번, 지정 인자로 호출됐는지
        mock_get.assert_called_once_with(123)

    def test_mock_basic(self):
        # Mock: 기본 mock 객체. 어떤 속성/메서드 접근도 자동 생성
        mock = Mock()
        mock.method.return_value = 42
        self.assertEqual(mock.method(), 42)
        # assert_called_once: 정확히 1번 호출 검증
        mock.method.assert_called_once()

    def test_magic_mock(self):
        # MagicMock: 매직 메서드(__len__, __getitem__ 등)도 자동 mock
        mock = MagicMock()
        mock.__len__.return_value = 5
        self.assertEqual(len(mock), 5)

        mock.__getitem__.return_value = 'value'
        self.assertEqual(mock[0], 'value')

    def test_side_effect(self):
        mock = Mock()
        # side_effect=리스트: 호출마다 다음 값 반환 (StopIteration 가능)
        mock.side_effect = [1, 2, 3]
        self.assertEqual(mock(), 1)
        self.assertEqual(mock(), 2)
        self.assertEqual(mock(), 3)

        # side_effect=예외: 호출 시 예외 발생
        mock.side_effect = ValueError("error!")
        with self.assertRaises(ValueError):
            mock()

    def test_call_args(self):
        mock = Mock()
        mock(1, 2, key='value')
        mock(3, 4)

        # assert_called_with: 마지막 호출이 지정 인자였는지
        mock.assert_called_with(3, 4)

        # call(): 호출 시그니처를 만드는 헬퍼
        expected_calls = [call(1, 2, key='value'), call(3, 4)]
        # assert_has_calls: 순서대로 모든 호출이 있었는지
        mock.assert_has_calls(expected_calls)

        # call_count: 총 호출 횟수
        self.assertEqual(mock.call_count, 2)

# === subTest ===
# subTest: 한 테스트 메서드 안에서 여러 케이스를 격리 실행 (하나 실패해도 나머지 진행)
class TestSubTest(unittest.TestCase):
    def test_even_numbers(self):
        evens = [(2, True), (4, True), (5, False), (8, True)]
        for num, expected in evens:
            # subTest 컨텍스트 내 실패는 별도로 보고됨
            with self.subTest(num=num):
                self.assertEqual(num % 2 == 0, expected)

# === skip ===
class TestSkip(unittest.TestCase):
    # @skip: 무조건 스킵
    @unittest.skip("아직 구현 안 됨")
    def test_not_implemented(self):
        pass

    # @skipIf(condition, reason): 조건부 스킵
    @unittest.skipIf(True, "조건부 스킵")
    def test_conditional(self):
        pass

# 실행: TestLoader + TestSuite + TextTestRunner
print("=== unittest 실행 ===")
loader = unittest.TestLoader()
suite = unittest.TestSuite()
# loadTestsFromTestCase: 클래스의 모든 test_* 메서드 수집
suite.addTests(loader.loadTestsFromTestCase(TestCalculator))
suite.addTests(loader.loadTestsFromTestCase(TestWithClassSetup))
suite.addTests(loader.loadTestsFromTestCase(TestWithMock))
suite.addTests(loader.loadTestsFromTestCase(TestSubTest))
suite.addTests(loader.loadTestsFromTestCase(TestSkip))

# verbosity=2: 각 테스트별 상세 출력
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# 결과 요약 (testsRun, failures, errors, skipped)
print(f"\n테스트 결과: {result.testsRun}개 실행, "
      f"{len(result.failures)}개 실패, "
      f"{len(result.errors)}개 에러, "
      f"{len(result.skipped)}개 스킵")

# 출력:
# test_add ... ok
# test_divide ... ok
# test_divide_by_zero ... ok
# test_is_positive ... ok
# test_collections ... ok
# test_comparisons ... ok
# test_file_exists ... ok
# test_file_content ... ok
# test_process_user ... ok
# test_mock_basic ... ok
# test_not_implemented ... skipped
# Ran 15 tests in 0.01s
# OK (skipped=2)
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 준비 고리는 둘로 나뉜다 — 바뀌는 객체는 `setUp`, 비싼 자원은 `@classmethod` 를 단 `setUpClass` 에 둔다.
- `patch` 데코레이터를 달면 바꿔 끼운 Mock 이 메서드의 두 번째 인자(`mock_get`)로 들어온다.
- `side_effect` 리스트는 길이만큼만 부를 수 있고, 예외를 넣으면 부를 때 그 예외가 난다.
- `subTest` 는 반복문 안에 두어야 한 케이스의 실패가 나머지 케이스를 막지 않는다.
- 정답 코드 끝의 주석은 「15개 실행」이라 적지만 `test_` 메서드는 16개이고 목록 차례 · 빠진 줄도 의심스럽다 — 2-summary 「어디서 틀리나 8」을 본다.
- 파일 이름을 `unittest.py` 로 두면 표준 모듈을 가릴 수 있으니 다른 이름으로 저장한다 (원본에 근거 없음 — 추론).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
