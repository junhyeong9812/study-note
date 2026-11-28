# python/python-patterns/13 — 테스팅 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 빈 이름과 잘못된 이메일이 함께 들어오면 (예측)

```python
# 질문용 발췌
service = UserService(UserRepository())
service.create_user("", "invalid")
```

- 어떤 메시지의 `ValueError` 가 나는가?
- 그 메시지가 나오는 까닭은 `create_user` 의 어떤 성질 때문인가?

### 2. 미리 정해 둔 반환값과 다른 입력을 넣으면 (예측)

```python
# 질문용 발췌
mock_repo = MagicMock(spec=UserRepository)
mock_repo.find_by_email.return_value = None
mock_repo.add.return_value = User(id=1, name="Test", email="test@test.com")
result = UserService(mock_repo).create_user("Zed", "zed@x.com")
```

- `result.name` 은 무엇인가?
- 이어서 `mock_repo.find_by_email.assert_called_once_with("test@test.com")` 을 부르면 어떻게 되는가?

### 3. session 스코프 위에 function 스코프를 얹고 테스트 셋을 돌리면 (예측)

```python
# 질문용 발췌
@pytest.fixture(scope="session")
def database():
    db = create_test_database()
    yield db
    db.drop()

@pytest.fixture
def clean_db(database):
    database.clear_all()
    yield database

# test_a, test_b, test_c 가 모두 clean_db 를 매개변수로 받는다
```

- `create_test_database()` 는 몇 번 불리는가?
- `clear_all()` 은 몇 번 불리는가?
- `db.drop()` 은 언제 불리는가?

### 4. 예외를 기대하는 `try` 안에 `assert False` 가 있는 까닭 (왜)

- `service.create_user("Bob", "alice@example.com")` 바로 다음 줄에 `assert False` 를 두는 까닭은?
- 그 `AssertionError` 가 `except ValueError` 에 잡히지 않는 것이 왜 중요한가?

### 5. 가짜 저장소를 `MagicMock(spec=UserRepository)` 로 만들고 `find_by_email.return_value = None` 을 적는 까닭 (왜)

- `spec=` 없이 `MagicMock()` 으로 만들면 어떤 실수가 숨는가?
- `find_by_email.return_value = None` 줄을 빼면 `create_user` 가 왜 실패하는가?

### 6. 시뮬레이션의 중복 이메일 검사를 pytest 테스트 함수로 옮길 때 (경계)

- 시뮬레이션에서 `test_duplicate_email` 이 통과할 수 있었던 전제는 무엇인가?
- 함수 스코프 `user_service` 만 받는 독립 테스트로 옮기면 그 전제가 왜 사라지는가?
- 그 테스트가 통과하려면 무엇을 더 받거나 해야 하는가?

### 7. `pytest.raises` 의 `match` 가 어디까지 걸리나 (경계)

- `match="이메일"` 로 `"유효하지 않은 이메일"` 예외를 잡을 수 있는가?
- `match` 에 메시지 전체를 적지 않아도 되는 까닭은?
- 이메일 주소가 든 메시지를 그 주소 그대로 `match` 에 넣으면 무엇이 문제가 될 수 있는가?

### 8. `parametrize` 목록이 세 줄이면 (예측)

- `test_create_user_validation` 에 붙은 세 튜플 목록으로 테스트는 몇 번 도는가?
- 둘째 경우가 실패하면 셋째 경우는 어떻게 되는가?

### 9. 생성자로 저장소를 받는 설계와 테스트 더블 (연결)

- `UserService.__init__(self, repo)` 처럼 저장소를 바깥에서 받는 설계는 fixture 사슬과 `MagicMock` 을 쓰는 데 어떤 다리가 되는가?
- `UserService` 가 안에서 `UserRepository()` 를 직접 만들었다면 가짜를 끼우는 데 원본의 어떤 도구가 필요했겠는가?

### 10. `pytest.approx` 와 부동소수점 (연결)

- `0.1 + 0.2 == 0.3` 대신 `pytest.approx(0.3)` 와 비교하는 까닭은 숫자를 컴퓨터에 담는 방식의 어떤 성질 때문인가?

## 실습

### 실습 1. 사용자 서비스와 그 테스트 패턴 데모 만들기

**만들 것** — 사용자 저장소 · 서비스를 만들고, 그 서비스를 assert 시뮬레이션과 `MagicMock` 으로 시험한 뒤, fixture · 파라미터화 · mock/patch · 스코프 · 유용한 기능의 예시 코드를 차례로 출력하는 파이썬 스크립트를 만든다.

**준비물** — `pytest` 패키지가 설치되어 있어야 한다(`import pytest` 를 한다). `myapp.services`, `classify`, `notify_user`, `create_test_database` 는 출력하는 예시 문자열 속 이름일 뿐 실제로 만들지 않는다.

**요구 조건**

1단계 — 테스트 대상

1. `pytest`, `unittest.mock` 의 `MagicMock` · `patch` · `AsyncMock`, `dataclass`, `Optional` 을 가져온다.
2. `@dataclass` `User` 는 `id`(기본 `None`) · `name`(기본 빈 문자열) · `email`(기본 빈 문자열) 필드를 가진다.
3. `UserRepository` 는 `id → User` 사전과 1 에서 시작하는 다음 id 를 가진다.
4. `add` 는 사용자에게 다음 id 를 붙여 저장하고 다음 id 를 1 늘린 뒤 그 사용자를 돌려준다.
5. `get` 은 id 로 한 건을 찾아 돌려주고, 없으면 `None` 을 돌려준다.
6. `find_by_email` 은 이메일이 같은 첫 사용자를 돌려주고, 없으면 `None` 을 돌려준다(`next` 와 제너레이터를 쓴다).
7. `UserService` 는 생성자로 저장소를 받는다.
8. `create_user` 는 차례대로 — 이름이나 이메일이 비면 `ValueError("name과 email은 필수")`, 이메일에 `@` 가 없으면 `ValueError("유효하지 않은 이메일")`, 이미 있는 이메일이면 `ValueError(f"이메일 중복: {email}")` 를 던지고, 다 통과하면 새 `User` 를 저장소에 추가해 돌려준다.

2단계 — 시뮬레이션

9. `=== 1. 기본 테스트 & Fixture ===` 를 찍고, `conftest.py` 예시(`user_repo` → `user_service(user_repo)` → `sample_user(user_service)` 세 fixture)를 문자열로 출력한다.
10. `테스트 실행 시뮬레이션:` 을 찍고 진짜 저장소 · 서비스를 하나 만든다.
11. Alice 를 만든 뒤 id 가 `None` 이 아니고 이름 · 이메일이 맞는지 `assert` 하고 `  PASSED: test_create_user` 를 찍는다.
12. 같은 이메일로 Bob 을 만들어 `ValueError` 가 나고 메시지에 「중복」이 드는지 확인한 뒤 `  PASSED: test_duplicate_email` 을 찍는다 — 예외가 안 나면 `assert False, "Should raise ValueError"` 로 실패하게 한다.
13. `"invalid-email"` 로 Charlie 를 만들어 `ValueError` 가 나는지 확인한 뒤 `  PASSED: test_invalid_email` 을 찍는다 — 예외가 안 나면 `assert False` 로 실패하게 한다.

3단계 — 예시 출력과 Mock 시연

14. `=== 2. 파라미터화 ===` 를 찍고, `test_create_user_validation`(세 경우, `pytest.raises` + `match`)과 `test_classify`(세 경우) 예시를 문자열로 출력한다.
15. `=== 3. Mock & Patch ===` 를 찍고, `test_with_mock`(spec 가짜 저장소, `return_value`, `assert_called_once_with`, `assert_called_once`)과 `@patch("myapp.services.send_email")` 예시를 문자열로 출력한다.
16. `spec=UserRepository` 인 가짜 저장소를 실제로 만들어 `find_by_email` 은 `None`, `add` 는 `User(id=1, name="Test", email="test@test.com")` 을 돌려주게 한다.
17. 가짜 저장소로 서비스를 만들어 `("Test", "test@test.com")` 사용자를 만들고, 결과 id 가 1 인지와 `find_by_email` 이 그 이메일로 정확히 한 번 불렸는지 검증한 뒤 `  PASSED: test_with_mock` 을 찍는다.

4단계 — 스코프와 유용한 기능 출력

18. `=== 4. Fixture 스코프 & conftest ===` 를 찍고, session 스코프 `database`(생성 → `yield` → `drop`)와 function 스코프 `clean_db`(`clear_all` → `yield`) 예시, 스코프 네 종류 설명을 문자열로 출력한다.
19. `=== 5. pytest 유용한 기능 ===` 을 찍고, `pytest.raises` · `pytest.approx` · `slow`/`skip`/`skipif` 마커 · `-m`/`-k`/`--tb=short -q` 실행 예시를 문자열로 출력한다.

**시작 코드**

```python
# [디자인 패턴 & 실무] 테스팅 패턴

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass
from typing import Optional

# === 테스트 대상 코드 ===
@dataclass
class User:
    # TODO: id(기본 None), name(기본 ""), email(기본 "") 필드
    pass

class UserRepository:
    def __init__(self):
        # TODO: 저장소 사전과 다음 id(1부터)
        pass

    def add(self, user: User) -> User:
        # TODO: id 부여 → 저장 → 다음 id 증가 → 반환
        pass

    def get(self, id: int) -> Optional[User]:
        # TODO: 단건 조회 (없으면 None)
        pass

    def find_by_email(self, email: str) -> Optional[User]:
        # TODO: next + 제너레이터로 첫 일치 한 건, 없으면 None
        pass

class UserService:
    def __init__(self, repo: UserRepository):
        # TODO: 저장소를 받아 둔다
        pass

    def create_user(self, name: str, email: str) -> User:
        # TODO: 필수 검증 → '@' 검증 → 중복 검증 → 저장
        pass

print("=== 1. 기본 테스트 & Fixture ===")
print("""
# TODO: conftest.py 예시 — user_repo / user_service / sample_user fixture
""")

print("테스트 실행 시뮬레이션:")
# TODO: 진짜 저장소·서비스 생성
# TODO: test_create_user — 생성 후 assert, PASSED 출력
# TODO: test_duplicate_email — try / assert False / except ValueError, '중복' 확인
# TODO: test_invalid_email — try / assert False / except ValueError

print("\n=== 2. 파라미터화 ===")
print("""
# TODO: test_create_user_validation, test_classify 예시
""")

print("=== 3. Mock & Patch ===")
print("""
# TODO: test_with_mock, @patch 예시
""")

# TODO: spec 가짜 저장소 생성, return_value 두 개 설정
# TODO: 가짜로 서비스 생성 → create_user("Test", "test@test.com")
# TODO: id 확인, find_by_email 호출 검증
print("  PASSED: test_with_mock")

print("\n=== 4. Fixture 스코프 & conftest ===")
print("""
# TODO: session database / function clean_db 예시, scope 종류
""")

print("=== 5. pytest 유용한 기능 ===")
print("""
# TODO: raises, approx, 마커, 실행 옵션 예시
""")
```

**확인 방법** — `python testing-patterns.py` 로 실행해 다섯 절의 제목과 예시 문자열이 차례로 찍히고, `PASSED:` 줄 네 개가 `AssertionError` 없이 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
