# python/python-patterns/13 — 테스팅 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `"name과 email은 필수"` — 첫 검사에서 멈춘다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`ValueError("name과 email은 필수")` 가 난다.
`"invalid"` 에 `@` 가 없다는 검사까지는 가지 않는다.

**왜 그런가**
`create_user` 는 필수 검증 → `@` 검증 → 중복 검증 차례로 검사하고, 처음 걸린 곳에서 예외를 던지고 멈춘다.
이름이 빈 문자열이라 `not name` 이 참이므로 첫 검사에서 끝난다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `"Test"` 가 나오고, 호출 검증은 실패한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`result.name` 은 `"Test"` 다.
`assert_called_once_with("test@test.com")` 은 `AssertionError` 를 던진다.

**왜 그런가**
가짜는 입력을 보고 계산하지 않고 `add.return_value` 에 정해 둔 `User(id=1, name="Test", …)` 를 그대로 돌려준다 — 그래서 `"Zed"` 를 넣어도 이름은 `"Test"` 다.
`find_by_email` 은 실제로 `"zed@x.com"` 으로 한 번 불렸으므로, `"test@test.com"` 으로 불렸는지 묻는 검증은 맞지 않아 실패한다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 3」.

### 3. 생성 1번 · 초기화 3번 · 삭제는 세션 끝에 1번

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`create_test_database()` 는 1번, `clear_all()` 은 3번 불린다.
`db.drop()` 은 세 테스트가 다 끝나고 세션이 끝날 때 1번 불린다.

**왜 그런가**
`database` 는 `scope="session"` 이라 세션에서 한 번 만들어지고, `yield` 뒤의 `db.drop()` 은 세션이 끝날 때 돈다.
`clean_db` 는 스코프를 정하지 않아 기본값 `function` 이고, 테스트마다 다시 돌아 `clear_all()` 을 부른다.
근거: 2-summary 「동작 방식 (6)」.

### 4. 예외가 안 났을 때 테스트를 실패시키려고

`assert False` 는 「여기까지 오면 기대한 예외가 안 난 것」을 표시한다.
대상이 `ValueError` 를 던지면 그 줄에 닿지 않고 `except` 로 간다.
대상이 예외를 안 던지면 `assert False` 가 `AssertionError` 를 던진다.
`AssertionError` 는 `ValueError` 가 아니라서 `except ValueError` 에 잡히지 않고 밖으로 나가 실패가 된다 — 만약 잡혔다면 「예외가 안 난 경우」도 통과로 둔갑한다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 4」.

### 5. 오타를 드러내고, 「참인 가짜」를 막으려고

`spec` 없는 `MagicMock` 은 없는 이름에도 새 가짜를 만들어 주므로 `find_by_emial` 같은 메서드 이름 오타가 에러 없이 숨는다.
`spec=UserRepository` 면 그런 접근이 `AttributeError` 로 드러난다.
`return_value` 를 정하지 않은 메서드는 `MagicMock` 객체를 돌려주는데, 이 객체는 참으로 평가된다.
그래서 `if self.repo.find_by_email(email):` 이 참이 되어 `ValueError("이메일 중복: …")` 로 실패한다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 1 · 2」.

### 6. 앞 테스트가 남긴 Alice 에 기댄 통과였다

전제는 「저장소에 이미 `alice@example.com` 이 있다」이다.
시뮬레이션은 저장소 하나를 세 검사가 함께 써서, 앞의 `test_create_user` 가 넣어 둔 Alice 가 남아 있었다.
기본 스코프 fixture 는 테스트마다 새 저장소를 만들므로 독립 테스트는 빈 저장소에서 시작하고, Bob 은 중복 없이 만들어져 예외가 안 난다.
통과하려면 `sample_user` fixture 를 함께 받거나 테스트 안에서 Alice 를 먼저 만들어야 한다.
한 테스트 안에서는 `sample_user` 가 쓴 `user_service` 와 테스트가 받은 `user_service` 가 같은 객체라 Alice 가 보인다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 5」.

### 7. 메시지 안에서 정규식으로 「찾는다」

잡을 수 있다 — `"유효하지 않은 이메일"` 안에 `"이메일"` 이 들어 있기 때문이다.
`match` 는 메시지 전체와 같은지 보는 것이 아니라 메시지 안에서 정규식으로 찾으므로 일부만 적어도 된다.
다만 정규식이라서, 이메일 주소의 `.` 처럼 정규식에서 특별한 뜻을 가진 글자가 그대로 들어가면 기대와 다르게 해석될 수 있다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 6」.

### 8. 세 번 돌고, 셋째 경우는 그대로 돈다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
테스트는 3번 돈다 — 튜플 하나가 테스트 한 번이다.
둘째 경우가 실패해도 셋째 경우는 따로 실행되고 따로 판정된다.

**왜 그런가**
`parametrize` 는 목록의 항목마다 같은 함수를 한 번씩 부르는 별개의 테스트를 만든다.
그래서 한 경우의 실패가 다른 경우의 실행을 막지 않는다.
근거: 2-summary 「동작 방식 (4)」.

### 9. 바꿔 끼울 「구멍」을 만들어 준다

저장소를 생성자 인자로 받으므로, fixture 사슬은 `UserService(user_repo)` 로 진짜 저장소를 넣고, mock 테스트는 `UserService(mock_repo)` 로 가짜를 넣는다 — 서비스 코드는 한 줄도 안 바뀐다.
서비스가 안에서 `UserRepository()` 를 직접 만들었다면 인자로 넘길 자리가 없으므로, 그 이름을 테스트 동안 가짜로 바꿔치기하는 `@patch("경로")` 가 필요했을 것이다.
근거: 2-summary 「동작 방식 (1)」의 의존성 주입, 「동작 방식 (5)」의 `patch`, 「언제 쓰고 언제 안 쓰나」.

### 10. 이진 부동소수점에는 오차가 있어서

`0.1` · `0.2` 같은 수는 이진 부동소수점으로 정확히 담기지 않아서, `0.1 + 0.2` 가 `0.3` 과 `==` 로 같지 않을 수 있다.
`pytest.approx(0.3)` 는 아주 작은 오차를 허용해 같다고 본다.
근거: 2-summary 「동작 방식 (7)」, 「어디서 틀리나 9」, 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 사용자 서비스와 그 테스트 패턴 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 도구 가져오기 | `import pytest`, `from unittest.mock import MagicMock, patch, AsyncMock`, `dataclass`, `Optional` |
| 2. `User` 필드 | `@dataclass class User` 의 `id` · `name` · `email` |
| 3. 저장소 상태 | `UserRepository.__init__` 의 `_storage`, `_next_id = 1` |
| 4. 추가 | `UserRepository.add` |
| 5. 단건 조회 | `UserRepository.get` — `self._storage.get(id)` |
| 6. 이메일 검색 | `UserRepository.find_by_email` — `next((u for u in …), None)` |
| 7. 저장소 주입 | `UserService.__init__(self, repo)` |
| 8. 검증 차례와 저장 | `UserService.create_user` 의 세 `if … raise ValueError` 와 `self.repo.add(...)` |
| 9. 1절 제목과 fixture 예시 | `print("=== 1. 기본 테스트 & Fixture ===")` 와 뒤 `print("""…""")` |
| 10. 시뮬레이션 준비 | `print("테스트 실행 시뮬레이션:")`, `repo = UserRepository()`, `service = UserService(repo)` |
| 11. 정상 생성 검증 | `user = service.create_user("Alice", …)` 와 세 `assert`, `PASSED: test_create_user` |
| 12. 중복 검증 | `try: service.create_user("Bob", …)` / `assert False, "Should raise ValueError"` / `except ValueError as e: assert "중복" in str(e)` |
| 13. 형식 검증 | `try: service.create_user("Charlie", "invalid-email")` / `assert False` / `except ValueError` |
| 14. 파라미터화 예시 | `print("\n=== 2. 파라미터화 ===")` 와 뒤 문자열 |
| 15. Mock & Patch 예시 | `print("=== 3. Mock & Patch ===")` 와 뒤 문자열 |
| 16. 가짜 저장소 | `mock_repo = MagicMock(spec=UserRepository)`, 두 `return_value` |
| 17. 가짜로 시험 | `test_service = UserService(mock_repo)`, `assert result.id == 1`, `assert_called_once_with("test@test.com")`, `PASSED: test_with_mock` |
| 18. 스코프 예시 | `print("\n=== 4. Fixture 스코프 & conftest ===")` 와 뒤 문자열 |
| 19. 유용한 기능 예시 | `print("=== 5. pytest 유용한 기능 ===")` 와 뒤 문자열 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-patterns/reference/testing-patterns.py`

```python
# [디자인 패턴 & 실무] 테스팅 패턴
# 설명: pytest fixture, mock, 테스트 더블, 파라미터화, conftest 활용
# 팁: fixture는 테스트 의존성을 선언적으로 관리한다. conftest.py에 정의하면 같은 디렉토리의 모든 테스트에서 사용 가능. MagicMock(spec=클래스)는 존재하지 않는 메서드 호출을 방지한다. parametrize로 반복 테스트를 줄인다.

# pytest 테스팅 패턴 시연
# 실행: pytest test_example.py -v

# pytest 본체 (이 파일에서는 일부 데모만 실행)
import pytest
# 표준 모킹 도구 (MagicMock, patch, AsyncMock)
from unittest.mock import MagicMock, patch, AsyncMock
# dataclass로 도메인 모델 단순화
from dataclasses import dataclass
# Optional 타입 힌트
from typing import Optional

# === 테스트 대상 코드 ===
# 역할: User 엔티티 (테스트 대상 도메인)
@dataclass
class User:
    id: Optional[int] = None
    name: str = ""
    email: str = ""

# 역할: 인메모리 사용자 리포지토리 (테스트 대상)
class UserRepository:
    # 저장소와 ID 카운터 초기화
    def __init__(self):
        self._storage: dict[int, User] = {}
        self._next_id = 1

    # 추가: ID 부여 후 저장
    def add(self, user: User) -> User:
        user.id = self._next_id
        self._storage[self._next_id] = user
        self._next_id += 1
        return user

    # 단건 조회
    def get(self, id: int) -> Optional[User]:
        return self._storage.get(id)

    # 이메일 검색: next + 제너레이터로 첫 일치 한 건만 반환
    def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._storage.values() if u.email == email), None)

# 역할: 비즈니스 규칙을 가진 서비스 (테스트 대상)
class UserService:
    # 리포지토리 의존성 주입
    def __init__(self, repo: UserRepository):
        self.repo = repo

    # 회원 생성: 검증 → 중복 체크 → 저장
    def create_user(self, name: str, email: str) -> User:
        # 필수 입력 검증
        if not name or not email:
            raise ValueError("name과 email은 필수")
        # 형식 간단 검증
        if "@" not in email:
            raise ValueError("유효하지 않은 이메일")
        # 중복 검증
        if self.repo.find_by_email(email):
            raise ValueError(f"이메일 중복: {email}")
        # 저장
        return self.repo.add(User(name=name, email=email))

# fixture 사용 예시 (텍스트로만 출력)
print("=== 1. 기본 테스트 & Fixture ===")
# conftest.py에서 fixture를 정의하는 표준 패턴 데모
print("""
# conftest.py (프로젝트 루트에 위치)
import pytest

@pytest.fixture
def user_repo():
    \"\"\"매 테스트마다 새 리포지토리 제공\"\"\"
    return UserRepository()

@pytest.fixture
def user_service(user_repo):
    \"\"\"의존성 주입된 서비스 제공\"\"\"
    return UserService(user_repo)

@pytest.fixture
def sample_user(user_service):
    \"\"\"테스트용 사용자\"\"\"
    return user_service.create_user("Alice", "alice@example.com")
""")

# 실제 동작 확인 (간이 테스트 시뮬레이션)
print("테스트 실행 시뮬레이션:")
# 직접 인스턴스화하여 테스트 흐름 재현
repo = UserRepository()
service = UserService(repo)

# 정상 케이스: 사용자 생성
user = service.create_user("Alice", "alice@example.com")
# assert로 상태 검증
assert user.id is not None
assert user.name == "Alice"
assert user.email == "alice@example.com"
print("  PASSED: test_create_user")

# 중복 이메일 → ValueError 기대
try:
    service.create_user("Bob", "alice@example.com")
    assert False, "Should raise ValueError"
except ValueError as e:
    # 메시지에 '중복' 단어 포함 확인
    assert "중복" in str(e)
    print("  PASSED: test_duplicate_email")

# 잘못된 이메일 형식 → ValueError 기대
try:
    service.create_user("Charlie", "invalid-email")
    assert False
except ValueError:
    print("  PASSED: test_invalid_email")

# 파라미터화 테스트 데모
print("\n=== 2. 파라미터화 ===")
# @pytest.mark.parametrize로 입력값과 기대값을 한 번에 정의
print("""
@pytest.mark.parametrize("name,email,expected_error", [
    ("", "test@example.com", "필수"),
    ("Alice", "", "필수"),
    ("Alice", "invalid", "유효하지 않은"),
])
def test_create_user_validation(user_service, name, email, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        user_service.create_user(name, email)

@pytest.mark.parametrize("input_val,expected", [
    (0, "zero"),
    (1, "positive"),
    (-1, "negative"),
])
def test_classify(input_val, expected):
    result = classify(input_val)
    assert result == expected
""")

# Mock & Patch 데모
print("=== 3. Mock & Patch ===")
# spec= 인자로 잘못된 메서드 호출을 차단하는 패턴이 핵심
print("""
from unittest.mock import MagicMock, patch

def test_with_mock():
    # Mock 리포지토리 생성
    mock_repo = MagicMock(spec=UserRepository)
    mock_repo.find_by_email.return_value = None  # 중복 없음
    mock_repo.add.return_value = User(id=1, name="Alice", email="alice@test.com")

    service = UserService(mock_repo)
    user = service.create_user("Alice", "alice@test.com")

    assert user.id == 1
    mock_repo.find_by_email.assert_called_once_with("alice@test.com")
    mock_repo.add.assert_called_once()

# patch 데코레이터
@patch("myapp.services.send_email")
def test_notification(mock_send_email):
    mock_send_email.return_value = True
    result = notify_user("user@test.com", "Hello")
    mock_send_email.assert_called_with("user@test.com", "Hello")
""")

# 실제 실행 가능한 Mock 데모
mock_repo = MagicMock(spec=UserRepository)
# find_by_email이 None 반환하도록 설정 (중복 없음 시나리오)
mock_repo.find_by_email.return_value = None
# add 호출 시 반환할 가짜 User 지정
mock_repo.add.return_value = User(id=1, name="Test", email="test@test.com")

# 가짜 리포지토리로 서비스 생성
test_service = UserService(mock_repo)
# 정상 흐름 실행
result = test_service.create_user("Test", "test@test.com")
# 반환값 검증
assert result.id == 1
# 호출 검증: 정확히 1번, 정확한 인자
mock_repo.find_by_email.assert_called_once_with("test@test.com")
print("  PASSED: test_with_mock")

# fixture scope 데모
print("\n=== 4. Fixture 스코프 & conftest ===")
# session/function/class/module 등 scope 차이 설명
print("""
# conftest.py
@pytest.fixture(scope="session")
def database():
    \"\"\"세션 전체에서 1번만 생성\"\"\"
    db = create_test_database()
    yield db
    db.drop()

@pytest.fixture(scope="function")  # 기본값
def clean_db(database):
    \"\"\"각 테스트 전 DB 초기화\"\"\"
    database.clear_all()
    yield database

# scope 종류:
# function: 매 테스트 (기본)
# class:    매 테스트 클래스
# module:   매 모듈
# session:  전체 테스트 세션
""")

# pytest 자주 쓰는 기능 모음
print("=== 5. pytest 유용한 기능 ===")
# raises, approx, mark 등
print("""
# 예외 검증
with pytest.raises(ValueError, match="이메일"):
    service.create_user("name", "invalid")

# 근사값 비교
assert 0.1 + 0.2 == pytest.approx(0.3)

# 마커
@pytest.mark.slow
def test_heavy_computation(): ...

@pytest.mark.skip(reason="미구현")
def test_future_feature(): ...

@pytest.mark.skipif(sys.platform == "win32", reason="Linux only")
def test_linux_feature(): ...

# 실행: pytest -m "not slow"  (slow 제외)
# 실행: pytest -k "test_create"  (이름 필터)
# 실행: pytest --tb=short -q  (간결한 출력)
""")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- 서비스가 저장소를 생성자로 받기 때문에, 같은 `UserService` 를 진짜 저장소(시뮬레이션)와 `MagicMock` 가짜(Mock 시연) 양쪽에 그대로 쓴다.
- 예외 검증은 `try` → 대상 호출 → `assert False` → `except ValueError` 꼴이라, 예외가 안 나면 `AssertionError` 가 빠져나가 실패한다.
- 시뮬레이션의 세 검사는 저장소 하나를 함께 쓰므로, 중복 검사는 앞에서 넣은 Alice 에 기댄다 — pytest 함수로 옮길 때는 fixture 로 격리해야 한다.
- 가짜 저장소는 `spec=UserRepository` 로 없는 이름을 막고, `find_by_email.return_value = None` 으로 「중복 없음」을 흉내 낸다.
- fixture · parametrize · patch · 스코프 · 마커는 이 파일에서 문자열로 출력하는 예시이고, 실제로 도는 검증은 시뮬레이션과 Mock 시연뿐이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
