# python/python-testing-deep/03 — Mock과 Patch — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `a` = 10, `b` = 20, `c` = 11, `call_count` = 2

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `next_item` 은 `side_effect` 리스트에서 호출마다 다음 원소를 꺼내므로 첫 호출 `a` 는 10, 둘째 호출 `b` 는 20 이다.
- `compute` 는 `side_effect` 함수에 인자를 넘겨 부르므로 `c = (lambda x: x + 1)(10)` = 11 이다.
- `next_item` 은 두 번 불렸으므로 `call_count` 는 2 이다 — 리스트의 30 은 아직 꺼내지 않았다.

**왜 그런가**

리스트는 「차례대로 꺼낼 값」, 함수는 「받은 인자로 대신 부를 함수」로 쓰인다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 2. `create_user` 는 0번 — `assert_not_called()` 는 통과한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `find_by_email` 이 `{"id": 1}` 을 돌려주고, 비어 있지 않은 dict 는 `if` 에서 참이다.
- 그래서 `register` 는 첫 줄에서 `ValueError("이미 존재하는 이메일")` 을 던지고, 그 아래 `create_user` · `send_welcome` 은 실행되지 않는다.
- `mock_db.create_user.call_count` 는 0 이다.
- `send_welcome` 도 한 번도 불리지 않았으므로 `assert_not_called()` 는 통과한다.

**왜 그런가**

예외가 협력자 호출보다 먼저 나므로 부작용이 생기지 않는다 — 원본의 `test_user_service_duplicate` 가 바로 이 점을 `assert_not_called()` 로 지킨다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 3. 진짜가 불리고 `m.call_count` 는 0 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `mymodule` 은 import 순간 `from os.path import exists` 로 자기 안에 `exists` 라는 이름을 따로 붙였다.
- `patch('os.path.exists')` 는 `os.path` 쪽 이름만 바꾸므로 `mymodule.exists` 는 여전히 진짜 함수를 가리킨다.
- 따라서 `has_config` 는 진짜 `exists` 를 부르고, mock `m` 은 한 번도 불리지 않아 `call_count` 는 0 이다.
- `result` 는 `m.return_value` 와 상관없이 그 경로의 파일이 실제로 있는지에 따라 정해진다.

**왜 그런가**

`patch` 는 이름표를 바꿀 뿐이고, 대상 코드가 쓰는 이름표는 `mymodule.exists` 다.
고치려면 `patch('mymodule.exists')` 로 건다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 1」.

### 4. `patch` 는 대상 코드가 실제로 찾아 쓰는 이름표를 바꿔야 하기 때문이다

- `patch` 는 「어떤 모듈의 어떤 이름이 가리키는 대상」을 잠시 바꾼다.
- `from A import x` 로 가져가면 쓰는 쪽 모듈에 따로 이름이 생기므로, 정의된 곳(`A.x`)을 바꿔도 쓰는 쪽은 옛 대상을 본다 — 그래서 사용되는 곳 기준이다.
- `fetch_weather` 는 `import urllib.request` 뒤 `urllib.request.urlopen(url)` 으로 부르므로, 호출 순간 `urllib.request` 모듈에서 `urlopen` 을 찾는다.
- 사용되는 곳이 곧 `urllib.request.urlopen` 이므로 `patch('urllib.request.urlopen')` 이 먹힌다.

근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (6)」.

### 5. 프로퍼티는 클래스에 있고, 속성 읽기는 호출이 아니기 때문이다

- `@property` 로 만든 `debug_mode` 는 `Config` 클래스에 정의되어 있다 — 그래서 `type(config)` 로 클래스를 집어 거기서 바꾼다.
- `config.debug_mode` 는 괄호 없는 속성 읽기다.
- 보통 mock 을 그 자리에 넣으면 읽은 결과가 mock 객체 자체일 뿐 `return_value` 가 쓰이지 않는다.
- `PropertyMock` 은 속성 읽기에 `return_value` 로 답하게 해 주므로 `new_callable=PropertyMock` 으로 대역을 이 클래스로 만든다 (원본에 근거 없음 — 추론).

근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 5」.

### 6. 예외 · 차례값 · 인자에 따른 값

- 호출하면 예외가 나야 할 때 — `side_effect = ValueError("에러!")`.
- 호출할 때마다 다른 값이 차례로 나와야 할 때 — `side_effect = [1, 2, 3]`.
- 받은 인자에 따라 값이 바뀌어야 할 때 — `side_effect = lambda x: x * 2`.
- `return_value` 는 몇 번 불러도 같은 값 하나만 돌려준다 — 리스트를 넣어도 리스트 전체가 매번 돌아온다.

근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 7. `name` 은 여전히 검사되고, 마지막 호출만 본다

- `ANY` 는 그 자리(`timestamp`)만 무엇이든 맞다고 판정한다.
- `name` 은 `"Alice"` 와 정확히 비교되므로 `"Bob"` 이면 검증은 `AssertionError` 로 실패한다.
- `assert_called_with` 는 마지막 호출의 인자를 본다 — 첫 호출만 이 인자였고 둘째 호출이 달랐다면 실패한다.
- 횟수까지 묶으려면 `assert_called_once_with` 를 쓴다.

근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」 · 「어디서 틀리나 6」.

### 8. 의존성을 생성자로 넘겨받는 설계(의존성 주입) 덕분이다

- `UserService.__init__(self, db, email_client)` 는 DB 와 이메일 클라이언트를 안에서 만들지 않고 바깥에서 받는다.
- 그래서 테스트가 진짜 대신 `MagicMock` 두 개를 넘기기만 하면 격리가 끝난다.
- 반대로 `fetch_weather` 는 `urlopen` 을 안에서 직접 부르므로 바꿔 끼울 틈이 없어 `patch` 가 필요하다.
- 주입하도록 짠 코드는 테스트하기 쉽다는 점이 이 대비에서 드러난다.

근거: 2-summary 「동작 방식 (4)」 · 「언제 쓰고 언제 안 쓰나」.

### 9. `return_value` 줄은 stub, `assert_called_once_with` 줄은 mock(행동 검증)이다

- `find_by_email.return_value = None` · `create_user.return_value = {...}` 는 정해진 값을 돌려줘 「중복 없음 · 생성됨」이라는 상태를 꾸민다 — stub 역할이다.
- `find_by_email.assert_called_once_with("a@b.com")` 등은 대상 코드가 협력자를 어떻게 불렀는지 확인한다 — mock 의 행동 검증이다.
- 같은 `MagicMock` 객체가 두 역할을 함께 한다.

근거: 2-summary 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 협력자를 대역으로 바꿔 끼우는 테스트 모음

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 정의하지 않은 메서드 · 체인 호출 | `test_magic_mock_basics` 의 `mock.some_method(1, 2, 3)` · `mock.nested.deep.call("hello")` |
| 2. 두 호출 검증 | `assert_called_once_with(1, 2, 3)` · `assert_called_with("hello")` |
| 3. 반환값 설정 | `mock.get_data.return_value = {"key": "value"}` |
| 4. 호출 횟수 | `mock.some_method.call_count == 1` |
| 5. 예외 | `mock.dangerous.side_effect = ValueError("에러!")` + `pytest.raises(ValueError)` |
| 6. 차례값 | `mock.next_item.side_effect = [1, 2, 3]` |
| 7. 두 배 함수 | `mock.compute.side_effect = lambda x: x * 2` |
| 8. 데코레이터 교체 | `@patch('urllib.request.urlopen')` · 인자 `mock_urlopen` |
| 9. 응답 꾸미기 | `mock_response.read.return_value = json.dumps(...).encode()` · `mock_urlopen.return_value = mock_response` |
| 10. 결과 · URL 검증 | `result["city"]` · `result["temp"]` · `mock_urlopen.assert_called_once_with("https://api.weather.com/Seoul")` |
| 11. 블록 안 교체 | `test_patch_context_manager` 의 `with patch('os.path.exists') as mock_exists:` |
| 12. 성공 경로 stub | `mock_db.find_by_email.return_value = None` · `mock_db.create_user.return_value = {...}` · `UserService(mock_db, mock_email)` |
| 13. 결과 · 세 협력자 검증 | `result["id"] == 1` · 세 `assert_called_once_with` |
| 14. 실패 경로 | `test_user_service_duplicate` 의 `pytest.raises(ValueError, match="이미 존재하는 이메일")` · `send_welcome.assert_not_called()` |
| 15. 프로퍼티 교체 | `patch.object(type(config), 'debug_mode', new_callable=PropertyMock)` · `mock_prop.return_value = True` |
| 16. 호출 차례 | `mock.process.assert_has_calls([call(1), call(2), call(3)])` |
| 17. 부분 검증 | `mock.save.assert_called_with({"name": "Alice", "timestamp": ANY})` |
| 18. 요약 | `if __name__ == '__main__':` 블록의 `print` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-testing-deep/reference/pytest-mock.py`

```python
# [테스팅 심화] Mock과 Patch
# 설명: unittest.mock의 patch, MagicMock, PropertyMock, side_effect로 외부 의존성을 격리하는 테스트
# 팁: patch의 경로는 객체가 정의된 곳이 아니라 사용되는 곳(import된 모듈)을 기준으로 지정한다. side_effect에 리스트를 주면 순차적으로 반환하고, 함수를 주면 동적으로 처리할 수 있다. assert_not_called()로 부작용이 없는지 검증하는 것도 중요하다. ANY는 값의 일부만 검증할 때 유용하다.

# pytest: 예외 검증용 (pytest.raises)
import pytest
# patch: 객체 일시 교체용
# MagicMock: 자동 생성 mock
# PropertyMock: 프로퍼티 mock 전용
# call: 호출 기록 매칭용
# ANY: 값 일부만 매칭할 때 사용
from unittest.mock import patch, MagicMock, PropertyMock, call, ANY
# json: 응답 직렬화 시뮬레이션용
import json

# === 테스트 대상 코드 ===
# UserService: DB와 이메일 클라이언트에 의존하는 서비스
class UserService:
    def __init__(self, db, email_client):
        self.db = db
        self.email_client = email_client

    # register: 중복 검사 → 생성 → 환영 메일 (3개의 협력자 호출)
    def register(self, name, email):
        if self.db.find_by_email(email):
            raise ValueError("이미 존재하는 이메일")
        user = self.db.create_user(name, email)
        self.email_client.send_welcome(email, name)
        return user

    def get_user(self, user_id):
        return self.db.find_by_id(user_id)

# 외부 HTTP 호출이 있는 함수 (patch로 격리할 대상)
def fetch_weather(city):
    import urllib.request
    url = f"https://api.weather.com/{city}"
    response = urllib.request.urlopen(url)
    return json.loads(response.read())

# === MagicMock 기본 ===
# MagicMock: 어떤 속성/메서드 접근에도 자동으로 mock 반환
def test_magic_mock_basics():
    mock = MagicMock()

    # 어떤 속성/메서드든 자동 생성 (체이닝도 자동)
    mock.some_method(1, 2, 3)
    mock.nested.deep.call("hello")

    # assert_called_once_with: 정확히 1번 + 인자 검증
    mock.some_method.assert_called_once_with(1, 2, 3)
    mock.nested.deep.call.assert_called_with("hello")

    # return_value 설정 - mock 호출 시 반환값
    mock.get_data.return_value = {"key": "value"}
    assert mock.get_data() == {"key": "value"}

    # call_count: 호출 횟수
    assert mock.some_method.call_count == 1

# === side_effect ===
# side_effect: 동적 반환/예외/순차값 - return_value보다 강력
def test_side_effect():
    mock = MagicMock()

    # 예외 발생: 호출 시 ValueError raise
    mock.dangerous.side_effect = ValueError("에러!")
    with pytest.raises(ValueError):
        mock.dangerous()

    # 순차적 반환값: 호출 순서대로 1, 2, 3 반환
    mock.next_item.side_effect = [1, 2, 3]
    assert mock.next_item() == 1
    assert mock.next_item() == 2
    assert mock.next_item() == 3

    # 함수: 인자에 따라 동적 반환
    mock.compute.side_effect = lambda x: x * 2
    assert mock.compute(5) == 10
    assert mock.compute(3) == 6

# === patch 데코레이터 ===
# @patch: 지정 경로의 객체를 mock으로 교체 (테스트 종료 시 자동 복원)
@patch('urllib.request.urlopen')
def test_fetch_weather(mock_urlopen):
    """외부 HTTP 호출을 mock으로 대체"""
    # Mock 응답 설정 - read()가 JSON 바이트 반환하도록
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {"city": "Seoul", "temp": 20}
    ).encode()
    mock_urlopen.return_value = mock_response

    # 실제 네트워크 호출 없이 테스트
    result = fetch_weather("Seoul")
    assert result["city"] == "Seoul"
    assert result["temp"] == 20

    # urlopen이 올바른 URL로 호출되었는지 검증
    mock_urlopen.assert_called_once_with("https://api.weather.com/Seoul")

# === patch를 context manager로 ===
# with 블록 안에서만 mock 적용 - 부분 격리에 유용
def test_patch_context_manager():
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        import os
        assert os.path.exists("/fake/path") is True
        mock_exists.assert_called_once_with("/fake/path")

# === 클래스의 의존성 Mock ===
# DI를 활용하면 patch 없이 mock 주입만으로 격리
def test_user_service_register():
    # Mock 의존성 생성
    mock_db = MagicMock()
    mock_email = MagicMock()

    # Stub 설정 - 정해진 값 반환
    mock_db.find_by_email.return_value = None  # 중복 없음
    mock_db.create_user.return_value = {"id": 1, "name": "Alice", "email": "a@b.com"}

    service = UserService(mock_db, mock_email)
    result = service.register("Alice", "a@b.com")

    # 동작 검증 (Mock = 행동 검증)
    assert result["id"] == 1
    mock_db.find_by_email.assert_called_once_with("a@b.com")
    mock_db.create_user.assert_called_once_with("Alice", "a@b.com")
    mock_email.send_welcome.assert_called_once_with("a@b.com", "Alice")

# 실패 경로 검증 - 중복 시 이메일이 발송되지 않아야 함
def test_user_service_duplicate():
    mock_db = MagicMock()
    mock_email = MagicMock()
    mock_db.find_by_email.return_value = {"id": 1}  # 이미 존재

    service = UserService(mock_db, mock_email)
    with pytest.raises(ValueError, match="이미 존재하는 이메일"):
        service.register("Alice", "a@b.com")

    # assert_not_called: 부작용 없음 검증 (이메일 발송되지 않음)
    mock_email.send_welcome.assert_not_called()

# === PropertyMock ===
# PropertyMock: @property를 mock하려면 전용 클래스 사용
def test_property_mock():
    class Config:
        @property
        def debug_mode(self):
            return False  # 실제 값

    config = Config()
    # type(config) - 인스턴스가 아닌 클래스의 프로퍼티를 patch
    with patch.object(type(config), 'debug_mode', new_callable=PropertyMock) as mock_prop:
        mock_prop.return_value = True
        assert config.debug_mode is True

# === call 히스토리 검증 ===
# 호출 순서와 인자 패턴 검증
def test_call_history():
    mock = MagicMock()
    mock.process(1)
    mock.process(2)
    mock.process(3)

    # assert_has_calls: 지정한 순서대로 호출되었는지 확인
    mock.process.assert_has_calls([
        call(1), call(2), call(3)
    ])

    # ANY: 동적 값(타임스탬프 등)을 무시하고 부분 매칭
    mock.save.return_value = True
    mock.save({"name": "Alice", "timestamp": 1234567890})
    mock.save.assert_called_with({"name": "Alice", "timestamp": ANY})

# 실행: pytest test_mock.py -v

if __name__ == '__main__':
    print("=== Mock 핵심 패턴 ===")
    print("MagicMock():      자동 속성/메서드 생성")
    print("return_value:     반환값 설정")
    print("side_effect:      예외, 순차값, 함수")
    print("assert_called*:   호출 검증")
    print()
    print("=== patch 사용법 ===")
    print("@patch('모듈.객체'):  데코레이터")
    print("with patch(...):     컨텍스트 매니저")
    print("patch.object():      특정 객체의 속성")
    print()
    print("=== 주의사항 ===")
    print("patch 경로는 '사용되는 곳' 기준!")
    print("  from os.path import exists → patch('mymodule.exists')")
    print("  import os.path → patch('os.path.exists')")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**

- 정의하지 않은 이름도 `MagicMock` 이 자식 mock 으로 만들어 주므로 별도 준비 없이 호출 · 검증할 수 있다.
- 고정 값은 `return_value`, 예외 · 차례값 · 인자에 따른 값은 `side_effect` 로 준다.
- `fetch_weather` 는 `urllib.request.urlopen` 을 호출 순간 찾아 쓰므로 그 경로를 `patch` 하고, 돌려줄 응답 객체도 `MagicMock` 으로 만들어 `read()` 의 반환값을 정한다.
- `UserService` 는 의존성을 생성자로 받으므로 `patch` 없이 mock 을 넘기는 것만으로 격리된다.
- 실패 경로에서는 예외 확인 뒤 `assert_not_called()` 로 메일이 나가지 않았음까지 확인한다.
- 프로퍼티는 `type(config)` 쪽에 `new_callable=PropertyMock` 으로 걸고, 매번 바뀌는 인자는 `ANY` 로 그 자리만 무시한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
