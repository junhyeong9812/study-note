# python/python-testing-deep/03 — Mock과 Patch — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 리스트와 함수를 `side_effect` 로 준 뒤 (예측)

```python
# 질문용 발췌
from unittest.mock import MagicMock

m = MagicMock()
m.next_item.side_effect = [10, 20, 30]
m.compute.side_effect = lambda x: x + 1
a = m.next_item()
b = m.next_item()
c = m.compute(a)
```

- `a` · `b` · `c` 는 각각 무엇인가?
- `m.next_item.call_count` 는 얼마인가?

### 2. 이미 있는 이메일로 `register` 를 부르면 (예측)

```python
# 질문용 발췌
mock_db = MagicMock()
mock_email = MagicMock()
mock_db.find_by_email.return_value = {"id": 1}
service = UserService(mock_db, mock_email)
try:
    service.register("Alice", "a@b.com")
except ValueError:
    pass
```

- `mock_db.create_user.call_count` 는 얼마인가?
- 이 뒤에 `mock_email.send_welcome.assert_not_called()` 를 부르면 테스트는 어떻게 되나?

### 3. `from` 으로 가져온 이름을 원래 자리에서 `patch` 하면 (예측)

```python
# 질문용 발췌
# --- mymodule.py ---
from os.path import exists

def has_config():
    return exists("/etc/app.conf")

# --- 테스트 파일 ---
from unittest.mock import patch
import mymodule

def test_has_config():
    with patch('os.path.exists') as m:
        m.return_value = True
        result = mymodule.has_config()
```

- `has_config` 안에서 불리는 `exists` 는 대역인가 진짜인가?
- 블록 끝에서 `m.call_count` 는 얼마인가?

### 4. `patch` 경로를 「사용되는 곳」으로 잡는 까닭 (왜)

- `patch` 의 경로를 객체가 정의된 모듈이 아니라 그것을 쓰는 모듈 기준으로 적어야 하는 까닭은 무엇인가?
- `fetch_weather` 테스트에서 `patch('urllib.request.urlopen')` 이 먹히는 까닭은 무엇인가?

### 5. 프로퍼티를 `type(config)` 에 `PropertyMock` 으로 거는 까닭 (왜)

- 인스턴스 `config` 가 아니라 `type(config)` 에 `patch.object` 하는 까닭은 무엇인가?
- 보통 `MagicMock` 대신 `new_callable=PropertyMock` 을 주는 까닭은 무엇인가?

### 6. `return_value` 로는 모자라는 자리 (경계)

- `return_value` 로는 할 수 없고 `side_effect` 가 있어야 하는 경우 세 가지는 무엇인가?

### 7. `ANY` 를 넣은 검증이 봐주는 범위 (경계)

- `assert_called_with({"name": "Alice", "timestamp": ANY})` 는 실제 호출의 `name` 이 `"Bob"` 이었다면 통과하나?
- 같은 mock 을 두 번 불렀고 첫 호출만 이 인자였다면 이 검증은 어느 호출을 보나?

### 8. `UserService` 테스트에 `patch` 가 없는 까닭과 의존성 주입 (연결)

- `UserService` 테스트가 `patch` 없이 격리되는 것은 클래스의 어떤 설계 덕분인가?

### 9. stub 과 mock — 한 객체의 두 역할 (연결)

- `test_user_service_register` 에서 `return_value` 를 정하는 줄과 `assert_called_once_with` 줄은 각각 stub · mock 중 어느 역할인가?

## 실습

### 실습 1. 협력자를 대역으로 바꿔 끼우는 테스트 모음

**만들 것** — 시작 코드에 들어 있는 `UserService` · `fetch_weather` 를 대상으로, `MagicMock` · `side_effect` · `patch` · `PropertyMock` · 호출 검증을 하나씩 쓰는 테스트 함수 8개를 채운다.

**준비물** — `pytest` 가 설치되어 있어야 한다(`unittest.mock` · `json` 은 표준 라이브러리다). `fetch_weather` 의 주소는 실제로 접속하지 않는 가짜 주소이고, 네트워크 호출은 `patch` 로 흉내 낸다.

**요구 조건**

1단계 — `MagicMock` 기본 (`test_magic_mock_basics`)
1. `MagicMock()` 하나에서 정의하지 않은 메서드 `some_method(1, 2, 3)` 과 체인 `nested.deep.call("hello")` 를 부른다.
2. `some_method` 가 정확히 한 번 `(1, 2, 3)` 으로 불렸는지, `nested.deep.call` 의 마지막 호출이 `"hello"` 인지 검증한다.
3. `get_data` 의 반환값을 `{"key": "value"}` 로 정하고 호출 결과가 그 dict 인지 확인한다.
4. `some_method` 의 호출 횟수가 1 인지 확인한다.

2단계 — `side_effect` (`test_side_effect`)
5. `dangerous` 가 불리면 `ValueError` 를 던지게 하고, `pytest.raises` 로 확인한다.
6. `next_item` 이 차례대로 1, 2, 3 을 돌려주게 하고 세 번 불러 확인한다.
7. `compute` 가 인자의 두 배를 돌려주게 하고 5 → 10, 3 → 6 을 확인한다.

3단계 — `patch` 데코레이터 (`test_fetch_weather`)
8. `urllib.request.urlopen` 을 데코레이터로 바꾸고, 교체된 mock 을 테스트 함수의 인자로 받는다.
9. 응답 mock 의 `read()` 가 `{"city": "Seoul", "temp": 20}` 의 JSON 바이트를 돌려주게 하고, `urlopen` 이 그 응답 mock 을 돌려주게 한다.
10. `fetch_weather("Seoul")` 결과의 `city` · `temp` 를 확인하고, `urlopen` 이 정확히 한 번 `"https://api.weather.com/Seoul"` 로 불렸는지 검증한다.

4단계 — 컨텍스트 매니저 `patch` (`test_patch_context_manager`)
11. `with` 블록 안에서만 `os.path.exists` 를 바꿔 `True` 를 돌려주게 하고, `os.path.exists("/fake/path")` 가 `True` 인지와 그 인자로 한 번 불렸는지 검증한다.

5단계 — 주입한 의존성 (`test_user_service_register`, `test_user_service_duplicate`)
12. 성공 경로: `find_by_email` 은 `None`, `create_user` 는 `{"id": 1, "name": "Alice", "email": "a@b.com"}` 을 돌려주게 하고 두 mock 을 `UserService` 에 넘긴다.
13. `register("Alice", "a@b.com")` 결과의 `id` 가 1 인지, 세 협력자 메서드가 각각 정확히 한 번 올바른 인자로 불렸는지 검증한다.
14. 실패 경로: `find_by_email` 이 `{"id": 1}` 을 돌려주게 하고, `"이미 존재하는 이메일"` 메시지의 `ValueError` 를 확인한 뒤 환영 메일이 발송되지 않았음을 검증한다.

6단계 — 프로퍼티 (`test_property_mock`)
15. 시작 코드의 `Config.debug_mode` 프로퍼티를 클래스 쪽에 `PropertyMock` 으로 바꿔 `True` 를 돌려주게 하고, `config.debug_mode is True` 를 확인한다.

7단계 — 호출 기록 (`test_call_history`)
16. `process` 를 1, 2, 3 으로 차례로 부르고 그 차례를 `call` 목록으로 검증한다.
17. `save` 의 반환값을 `True` 로 정하고 `{"name": "Alice", "timestamp": 1234567890}` 으로 부른 뒤, `timestamp` 자리는 무시하고 마지막 호출 인자를 검증한다.

8단계 — 요약
18. 파일을 직접 실행하면 시작 코드에 채워 둔 요약 문구를 찍는다(시작 코드 그대로).

**시작 코드**

```python
import pytest
from unittest.mock import patch, MagicMock, PropertyMock, call, ANY
import json

# === 테스트 대상 코드 (그대로 둔다) ===
class UserService:
    def __init__(self, db, email_client):
        self.db = db
        self.email_client = email_client

    def register(self, name, email):
        if self.db.find_by_email(email):
            raise ValueError("이미 존재하는 이메일")
        user = self.db.create_user(name, email)
        self.email_client.send_welcome(email, name)
        return user

    def get_user(self, user_id):
        return self.db.find_by_id(user_id)

def fetch_weather(city):
    import urllib.request
    url = f"https://api.weather.com/{city}"
    response = urllib.request.urlopen(url)
    return json.loads(response.read())

# === 1단계 ===
def test_magic_mock_basics():
    mock = MagicMock()
    # TODO: some_method(1, 2, 3), nested.deep.call("hello") 호출
    # TODO: 두 호출 검증
    # TODO: get_data 반환값 설정 후 확인
    # TODO: 호출 횟수 확인

# === 2단계 ===
def test_side_effect():
    mock = MagicMock()
    # TODO: dangerous → ValueError
    # TODO: next_item → 1, 2, 3
    # TODO: compute → 두 배

# === 3단계 ===
# TODO: urllib.request.urlopen 을 바꾸는 데코레이터
def test_fetch_weather(mock_urlopen):
    """외부 HTTP 호출을 mock으로 대체"""
    # TODO: 응답 mock 과 read() 반환값, urlopen 반환값
    # TODO: fetch_weather("Seoul") 결과 확인
    # TODO: urlopen 호출 인자 검증

# === 4단계 ===
def test_patch_context_manager():
    # TODO: with 블록 안에서만 os.path.exists 교체
    pass

# === 5단계 ===
def test_user_service_register():
    mock_db = MagicMock()
    mock_email = MagicMock()
    # TODO: stub 설정
    # TODO: 서비스 생성과 register 호출
    # TODO: 결과와 세 협력자 호출 검증

def test_user_service_duplicate():
    mock_db = MagicMock()
    mock_email = MagicMock()
    # TODO: 이미 존재하도록 stub
    # TODO: ValueError 확인
    # TODO: 메일 미발송 검증

# === 6단계 ===
def test_property_mock():
    class Config:
        @property
        def debug_mode(self):
            return False  # 실제 값

    config = Config()
    # TODO: 클래스 쪽에 PropertyMock 으로 교체하고 True 확인

# === 7단계 ===
def test_call_history():
    mock = MagicMock()
    # TODO: process(1), process(2), process(3) 과 차례 검증
    # TODO: save 반환값, 호출, ANY 로 부분 검증

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

**확인 방법** — 파일을 `test_mock.py` 로 저장하고 `pytest test_mock.py -v` 로 돌려 테스트 8개가 모두 통과하는지 본다. `python test_mock.py` 로 돌리면 요약 문구를 찍는다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
