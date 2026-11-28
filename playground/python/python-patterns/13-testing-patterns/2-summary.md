# python/python-patterns/13 — 테스팅 패턴 — 정리 (힌트)

> 출처 — study-site 항목 `python/testing-patterns`(항목 데이터 `data/python/patterns.json`) · 정답 코드 study-practice `python/python-patterns/reference/testing-patterns.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**테스트는 「자동차 충돌 시험장」이다.**
시험할 차를 세워 두고, 사람 대신 더미 인형을 태우고, 시험마다 트랙을 새로 깔고, 속도만 바꿔 같은 시험을 여러 번 한다.
공용 장비는 시험장 창고에 두어 어느 시험이든 꺼내 쓴다.
pytest 테스트도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 시험할 차 | 테스트 대상 코드 (`UserService.create_user`) |
| 더미 인형 | 테스트 더블 (`MagicMock(spec=UserRepository)`) |
| 시험마다 새로 까는 트랙 | fixture (`user_repo`, `user_service`) |
| 속도만 바꿔 여러 번 | `@pytest.mark.parametrize` |
| 시험장 공용 창고 | `conftest.py` |
| 「충돌 후 이 값이어야 한다」 판정 | `assert`, `pytest.raises` |

```text
 conftest.py (창고)
   ├─ user_repo ──▶ user_service ──▶ sample_user      ← fixture 사슬
   │
 test_xxx(user_service, name, email)                    ← 매개변수 이름으로 받는다
   ├─ parametrize 가 (name, email) 을 바꿔 가며 여러 번 부른다
   ├─ 진짜 저장소 대신 MagicMock 을 끼울 수도 있다
   └─ assert / pytest.raises 로 판정한다
```

## 이 주제가 답하려는 질문

1. 테스트마다 필요한 준비물(저장소, 서비스, 예시 사용자)을 반복 없이, 서로 섞이지 않게 어떻게 만들어 주나?
2. 진짜 의존 대상 대신 가짜를 끼우고, 가짜가 어떤 인자로 몇 번 불렸는지 어떻게 확인하나?
3. 입력만 다른 비슷한 테스트를 어떻게 한 함수로 줄이나?
4. 비싼 준비물(테스트 DB)을 얼마나 오래 살려 두고 언제 치우나?

## 동작 방식

### (1) 테스트 대상 — 저장소와 서비스

**언제 쓰나** — 테스트를 이해하려면 먼저 무엇을 시험하는지 알아야 한다.
원본은 `User`(데이터) · `UserRepository`(메모리 저장소) · `UserService`(규칙)의 세 층을 시험한다.

```text
create_user(name, email)
  │
  ├─ name 이나 email 이 비었나? ───────── 예 ─▶ ValueError("name과 email은 필수")
  ├─ email 에 "@" 가 없나? ─────────────── 예 ─▶ ValueError("유효하지 않은 이메일")
  ├─ repo.find_by_email(email) 이 참인가? ─ 예 ─▶ ValueError("이메일 중복: <email>")
  └─ repo.add(User(name=name, email=email)) ───▶ id 가 붙은 User 를 돌려준다
```

- 검사는 위에서 아래로 하고, 처음 걸린 곳에서 예외를 던지고 멈춘다.
- `UserRepository.add` 는 `_next_id` 를 사용자에게 붙이고 `_storage` 에 넣은 뒤 `_next_id` 를 1 늘린다.
- `find_by_email` 은 `next(제너레이터, None)` 으로 이메일이 같은 첫 사용자 하나를 돌려주고, 없으면 `None` 을 돌려준다.
- `UserService` 는 저장소를 직접 만들지 않고 생성자 인자 `repo` 로 받는다.
- 그래서 테스트에서 진짜 저장소든 가짜 저장소든 마음대로 끼울 수 있다.

> **의존성 주입** — 객체가 쓸 다른 객체를 스스로 만들지 않고 바깥에서 받는 설계다.\
> 예: `UserService(repo)` 는 `repo` 를 받아서 쓴다.

### (2) `assert` 와 예외 검증

**언제 쓰나** — 결과가 기대와 같은지, 기대한 예외가 났는지 판정할 때 쓴다.

```text
assert user.name == "Alice"        조건이 참  → 조용히 지나간다
                                   조건이 거짓 → AssertionError → 테스트 실패

try:
    service.create_user("Bob", "alice@example.com")   ← ValueError 가 나야 정상
    assert False, "Should raise ValueError"           ← 여기 오면 예외가 안 난 것
except ValueError as e:
    assert "중복" in str(e)                            ← 메시지까지 확인
```

- `assert 조건` 은 조건이 거짓이면 `AssertionError` 를 던진다.
- 예외를 기대하는 원본의 수동 패턴은 `try` 안에서 대상을 부르고 바로 다음 줄에 `assert False` 를 둔다.
- 대상이 예외를 던지면 `assert False` 에 닿지 않고 `except ValueError` 로 간다.
- 대상이 예외를 안 던지면 `assert False` 가 `AssertionError` 를 던진다.
- `AssertionError` 는 `ValueError` 가 아니므로 `except ValueError` 에 잡히지 않고 밖으로 나가 실패가 된다.
- pytest 는 이 패턴을 `with pytest.raises(ValueError, match="...")` 한 줄로 줄인다.
- `with` 블록 안에서 `ValueError` 가 나면 통과하고, 안 나면 실패한다.
- `match` 는 예외 메시지 안에서 정규식으로 **찾는다** — 메시지 전체가 같을 필요가 없고 일부만 들어 있으면 된다.
- 그래서 `match="이메일"` 은 「유효하지 않은 이메일」에도, 「이메일 중복: …」에도 걸린다.

### (3) fixture 와 `conftest.py`

**언제 쓰나** — 여러 테스트가 같은 준비물을 쓸 때, 준비 코드를 테스트마다 복사하지 않으려고 쓴다.

```text
@pytest.fixture                       @pytest.fixture                    @pytest.fixture
def user_repo():          ──주입──▶   def user_service(user_repo):  ──▶  def sample_user(user_service):
    return UserRepository()               return UserService(user_repo)     return user_service.create_user("Alice", ...)

def test_xxx(user_service, sample_user):   ← 매개변수 이름 = fixture 이름
    ...                                       pytest 가 사슬을 따라 만들어 넣어 준다
```

- `@pytest.fixture` 를 붙인 함수가 fixture 다.
- 테스트 함수의 매개변수 이름이 fixture 이름과 같으면, pytest 가 그 fixture 를 불러 결과를 넣어 준다.
- fixture 도 다른 fixture 를 매개변수로 받을 수 있어서 사슬(`sample_user` → `user_service` → `user_repo`)이 된다.
- 테스트는 「무엇이 필요한가」만 매개변수로 선언하고, 「어떻게 만드나」는 fixture 가 맡는다 — 팁이 말하는 「의존성을 선언적으로 관리한다」가 이것이다.
- 스코프를 정하지 않으면 매 테스트마다 새로 만든다 — 원본 주석 「매 테스트마다 새 리포지토리 제공」.
- 한 테스트 안에서는 같은 fixture 를 한 번만 만들어 함께 쓴다 — `sample_user` 가 쓴 `user_service` 와 테스트가 받은 `user_service` 는 같은 객체다.
- fixture 를 `conftest.py` 에 두면 같은 디렉토리의 테스트 파일들이 `import` 없이 그 이름으로 쓸 수 있다.
- 원본은 `conftest.py` 를 프로젝트 루트에 둔다.

> **fixture** — 테스트가 쓸 준비물을 만들어 매개변수로 넣어 주는 pytest 함수다.\
> 예: `def test_a(user_repo):` 는 `user_repo()` 의 결과를 받는다.

### (4) 파라미터화 — `@pytest.mark.parametrize`

**언제 쓰나** — 입력과 기대값만 다르고 검증 방식은 같은 테스트가 여럿일 때 쓴다.

```text
@pytest.mark.parametrize("name,email,expected_error", [
    ("",      "test@example.com", "필수"),          ─▶ 1번째 테스트
    ("Alice", "",                 "필수"),          ─▶ 2번째 테스트
    ("Alice", "invalid",          "유효하지 않은"),  ─▶ 3번째 테스트
])
def test_create_user_validation(user_service, name, email, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        user_service.create_user(name, email)
```

- 첫 인자 문자열 `"name,email,expected_error"` 는 쉼표로 나눈 매개변수 이름들이다.
- 목록의 튜플 하나가 테스트 한 번이 되고, 튜플의 값이 이름 차례대로 매개변수에 들어간다.
- 경우마다 따로 실행되고 따로 통과 · 실패가 매겨지므로, 한 경우가 실패해도 다른 경우는 그대로 돈다.
- fixture 매개변수(`user_service`)와 파라미터 매개변수(`name`, `email`, …)를 한 함수에 섞어 쓸 수 있다.
- 원본의 둘째 예 `test_classify` 는 `(0, "zero")`, `(1, "positive")`, `(-1, "negative")` 세 경우를 한 함수로 시험한다.

### (5) 테스트 더블 — `MagicMock`, `spec`, `patch`

**언제 쓰나** — 대상이 기대는 다른 객체를 진짜로 쓰기 싫거나(느림 · 외부 서비스 · 메일 발송) 그 객체가 어떻게 불렸는지 확인하고 싶을 때 쓴다.

```text
mock_repo = MagicMock(spec=UserRepository)
mock_repo.find_by_email.return_value = None          ← "중복 없음" 이라고 정해 둔다
mock_repo.add.return_value = User(id=1, name="Test", email="test@test.com")

UserService(mock_repo).create_user("Test", "test@test.com")
   │ find_by_email("test@test.com") 호출 → None 반환 (기록됨)
   │ add(User(...)) 호출 → 정해 둔 User(id=1) 반환 (기록됨)
   ▼
result.id == 1
mock_repo.find_by_email.assert_called_once_with("test@test.com")   ← 정확히 1번, 이 인자로
mock_repo.add.assert_called_once()                                  ← 정확히 1번 (인자는 안 봄)
```

- 테스트 더블은 진짜 의존 대상 대신 끼우는 가짜를 통틀어 부르는 말이다.
- 정해진 값을 돌려주기만 하는 역할을 스텁(stub), 호출을 기록하고 나중에 검증하는 역할을 목(mock)이라 나눠 부른다.
- `MagicMock` 은 둘 다 한다 — `.return_value` 로 돌려줄 값을 정하고, `assert_called_…` 로 호출을 검증한다.
- 가짜는 입력을 보고 계산하지 않는다 — 무엇을 넣든 `.return_value` 에 정해 둔 값을 그대로 돌려준다.
- `.return_value` 를 정하지 않은 메서드를 부르면 결과로 또 다른 `MagicMock` 객체가 나오고, 이 객체는 `if` 에서 참으로 평가된다.
- 그래서 원본은 「중복 없음」을 흉내 내려고 `find_by_email.return_value = None` 을 일부러 적는다.
- `spec=UserRepository` 를 주면 `UserRepository` 에 있는 이름만 쓸 수 있고, 없는 이름(오타 포함)에 접근하면 `AttributeError` 가 난다 — 팁의 「존재하지 않는 메서드 호출을 방지한다」.
- `spec` 이 없으면 `mock_repo.find_by_emial` 같은 오타도 조용히 새 `MagicMock` 을 만들어 돌려준다.
- `assert_called_once_with(인자)` 는 정확히 한 번, 그 인자로 불렸는지 본다.
- `assert_called_once()` 는 횟수만 보고, `assert_called_with(인자)` 는 마지막 호출의 인자를 본다.
- `@patch("myapp.services.send_email")` 은 테스트가 도는 동안 그 경로의 이름을 `MagicMock` 으로 바꿔치기하고, 그 가짜를 테스트 함수의 인자(`mock_send_email`)로 넣어 준다.
- 대상이 의존 객체를 인자로 받지 않고 모듈 안의 이름을 직접 부를 때(`notify_user` 가 `send_email` 을 부르는 경우) `patch` 를 쓴다.
- 원본은 `AsyncMock` 도 `import` 하지만 쓰지는 않는다.

> **테스트 더블** — 테스트에서 진짜 의존 대상 대신 끼우는 가짜 객체의 통칭이다.\
> 예: `MagicMock(spec=UserRepository)` 는 저장소 자리에 들어가는 테스트 더블이다.

### (6) fixture 스코프와 `yield` 뒷정리

**언제 쓰나** — 준비물이 비싸서(테스트 DB) 매번 만들기 아깝거나, 쓰고 나서 치워야 할 때 쓴다.

```text
세션 시작
  database()  : create_test_database()  ──yield db──┐        (scope="session", 1번)
                                                     │
    test_a    : clean_db → database.clear_all() → yield → test_a 실행
    test_b    : clean_db → database.clear_all() → yield → test_b 실행   (scope="function", 매번)
    test_c    : clean_db → database.clear_all() → yield → test_c 실행
                                                     │
세션 끝       : yield 다음 줄 db.drop() ◀─────────────┘
```

- fixture 안의 `yield` 앞은 준비, `yield` 하는 값은 테스트에 주는 것, `yield` 뒤는 뒷정리다.
- `scope="session"` 인 `database` 는 전체 테스트 세션에서 한 번만 만들어지고, 세션이 끝날 때 `db.drop()` 이 돈다.
- `scope="function"` 인 `clean_db` 는 매 테스트마다 돌아 `database.clear_all()` 로 DB 를 비운 뒤 넘긴다.
- 비싼 것은 넓은 스코프로 한 번, 테스트 사이 격리는 좁은 스코프로 매번 — 두 층을 겹쳐 쓰는 것이 핵심이다.

| `scope` | 언제 새로 만드나 |
|---|---|
| `"function"` | 매 테스트 (기본값) |
| `"class"` | 매 테스트 클래스 |
| `"module"` | 매 모듈(파일) |
| `"session"` | 전체 테스트 세션에서 한 번 |

### (7) 자주 쓰는 도구 — 근사값 · 마커 · 실행 옵션

**언제 쓰나** — 부동소수점 비교, 테스트 골라 돌리기, 출력 줄이기에 쓴다.

```text
assert 0.1 + 0.2 == pytest.approx(0.3)   ← 아주 작은 오차는 같다고 본다

@pytest.mark.slow                        ← 이름표만 붙인다
@pytest.mark.skip(reason="미구현")        ← 무조건 건너뛴다
@pytest.mark.skipif(sys.platform == "win32", reason="Linux only")   ← 조건이 참이면 건너뛴다

pytest -m "not slow"      slow 표가 붙은 것 빼고
pytest -k "test_create"   이름에 test_create 가 든 것만
pytest --tb=short -q      실패 추적은 짧게, 전체 출력은 조용히
```

- `0.1 + 0.2` 는 이진 부동소수점 오차 때문에 `0.3` 과 `==` 로 같지 않을 수 있다 — 그래서 `pytest.approx` 로 비교한다.
- 마커는 테스트에 이름표를 붙이고, `-m` 이 그 이름표로 테스트를 고른다.

## 문법 — 형태와 규칙

```python
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def repo():
    return UserRepository()                     # 매 테스트 새 저장소

@pytest.mark.parametrize("email", ["", "no-at-sign"])
def test_bad_email(repo, email):                # fixture + 파라미터
    with pytest.raises(ValueError):
        UserService(repo).create_user("Kim", email)

def test_with_fake_repo():
    fake = MagicMock(spec=UserRepository)
    fake.find_by_email.return_value = None      # 스텁: 중복 없음
    fake.add.return_value = User(id=7, name="Kim", email="k@x.com")
    assert UserService(fake).create_user("Kim", "k@x.com").id == 7
    fake.add.assert_called_once()               # 목: 호출 검증
```

- 테스트 함수 이름은 `test_` 로 시작한다 (원본의 모든 예가 이 꼴이다).
- fixture 는 `@pytest.fixture` 또는 `@pytest.fixture(scope="...")` 로 만들고, 쓰는 쪽은 같은 이름의 매개변수로 받는다.
- 뒷정리가 필요하면 `return` 대신 `yield` 를 쓰고 그 뒤에 정리 코드를 둔다.
- `parametrize` 는 `("이름1,이름2", [(값1, 값2), …])` 꼴이다.
- 예외 검증은 `with pytest.raises(예외형, match="정규식"):` 꼴이다.

| 도구 | 하는 일 |
|---|---|
| `MagicMock(spec=클래스)` | 그 클래스에 있는 이름만 허용하는 가짜 |
| `가짜.메서드.return_value = 값` | 그 메서드가 돌려줄 값 고정 |
| `가짜.메서드.assert_called_once()` | 정확히 1번 불렸나 |
| `가짜.메서드.assert_called_once_with(…)` | 정확히 1번, 이 인자로 불렸나 |
| `가짜.메서드.assert_called_with(…)` | 마지막 호출이 이 인자였나 |
| `@patch("모듈.경로.이름")` | 테스트 동안 그 이름을 가짜로 바꾸고 인자로 넘김 |
| `pytest.approx(x)` | 근사값 비교 |
| `@pytest.mark.slow` / `skip` / `skipif` | 이름표 · 건너뛰기 · 조건부 건너뛰기 |

## 어디서 틀리나

### 1. `spec` 없는 `MagicMock` 은 오타를 삼킨다

`MagicMock()` 은 어떤 이름을 접근해도 새 가짜를 만들어 준다.
`mock_repo.find_by_emial.return_value = None` 처럼 오타를 내도 에러가 없고, 진짜 `find_by_email` 은 설정되지 않은 채 남는다.
`spec=UserRepository` 를 주면 이 오타가 바로 `AttributeError` 로 드러난다.

### 2. `return_value` 를 잊으면 「참인 가짜」가 돌아온다

설정하지 않은 메서드의 반환값은 `MagicMock` 객체이고 참으로 평가된다.
`find_by_email.return_value = None` 을 빼면 `create_user` 는 `if self.repo.find_by_email(email):` 에서 중복으로 판단해 `ValueError("이메일 중복: …")` 를 던진다.

### 3. 가짜는 입력을 보지 않는다

`add.return_value = User(id=1, name="Test", …)` 로 정해 두면 `create_user` 에 어떤 이름을 넣어도 그 `User` 가 돌아온다.
반환값만 확인하면 서비스가 `add` 에 무엇을 넘겼는지는 검증되지 않는다.
원본도 `add` 는 `assert_called_once()` 로 횟수만 확인한다.

### 4. 예외 테스트에서 `assert False` 를 빠뜨린다

`try` 안에 `assert False` 가 없으면, 대상이 예외를 안 던져도 테스트는 아무 일 없이 지나간다.
`except Exception` 처럼 넓게 잡으면 `AssertionError` 까지 잡혀 같은 문제가 생긴다.
`pytest.raises` 를 쓰면 이 실수를 할 자리가 없다.

### 5. 테스트끼리 상태를 나눠 쓴다

원본의 시뮬레이션은 `repo` 하나를 세 검사가 함께 쓴다.
`test_duplicate_email` 이 통과한 것은 바로 앞 `test_create_user` 가 Alice 를 넣어 두었기 때문이다.
함수 스코프 fixture 로 옮기면 테스트마다 빈 저장소를 받으므로, 중복 테스트는 Alice 를 스스로 만들거나 `sample_user` fixture 를 받아야 한다.

### 6. `match` 는 정규식이다

`match` 의 문자열은 정규식으로 해석된다.
메시지에 든 `.` · `(` · `)` 같은 글자는 정규식에서 특별한 뜻이 있어서, 이메일 주소나 괄호가 든 문구를 그대로 넣으면 기대와 다르게 걸리거나 안 걸릴 수 있다.

### 7. 원본 머리 주석의 실행 방법

원본의 주장 → 「실행: `pytest test_example.py -v`」.
왜 의심스러운가 → 이 파일의 `test_` 함수들은 모두 `print("""…""")` 문자열 안에만 있고, 실제로 도는 것은 모듈 맨 바깥의 시뮬레이션 코드다.
파일 이름도 `testing-patterns.py` 라 `test_example.py` 가 아니다.
그래서 이 파일은 `python` 으로 실행해 시뮬레이션을 보는 데모로 읽는 편이 맞다 (확인 필요).

### 8. 문자열 속 예제는 그대로 붙여 쓸 수 없다

문자열로 출력하는 예제에는 정의되지 않은 이름이 있다 — `classify`, `notify_user`, `create_test_database`, `myapp.services`, 그리고 `import` 없이 쓰는 `sys`.
`patch` 예제도 「모양」을 보이는 것이고, 이 파일 안에서 실제로 `patch` 가 도는 코드는 없다.

### 9. 부동소수점을 `==` 로 비교한다

`0.1 + 0.2 == 0.3` 처럼 직접 비교하면 오차 때문에 실패할 수 있다.
`pytest.approx` 로 비교한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `assert` 가 거짓이면 `AssertionError` 를 던진다 | 파이썬 언어 |
| `next(제너레이터, None)` 이 일치가 없을 때 `None` 을 돌려준다 | 파이썬 언어 (내장 함수) |
| `find_by_email` 이 「첫 일치」를 고르는 차례 — `dict.values()` 의 순회 순서 | 파이썬 언어 — 삽입 순서 유지 (3.7 이후, 확인 필요) |
| fixture 주입 · 스코프 · `conftest.py` 공유 · `parametrize` · `raises` · `approx` · 마커 · `-m`/`-k` 옵션 | pytest 라이브러리 (언어가 아니다) |
| `MagicMock`, `spec`, `return_value`, `assert_called_…`, `patch` | 표준 라이브러리 `unittest.mock` |
| `0.1 + 0.2` 가 `0.3` 과 정확히 같지 않다 | 이진 부동소수점(IEEE 754 배정밀도)을 쓰는 구현 — 대부분의 구현이 그렇다 (확인 필요) |
| `conftest.py` 를 프로젝트 루트에 둔다 | 관례 (원본의 선택) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 여러 테스트가 같은 준비물을 쓴다 | fixture (+ `conftest.py`) | 테스트마다 준비 코드 복사 |
| 테스트끼리 섞이면 안 되는 상태 | `scope="function"` fixture | 모듈 전역 객체 공유 |
| 만들기 비싼 자원 (테스트 DB) | `scope="session"` + `yield` 뒷정리, 그 위에 함수 스코프 초기화 | 매 테스트 새로 생성 |
| 입력만 다른 같은 검증 | `@pytest.mark.parametrize` | 거의 같은 함수 여러 개 |
| 의존 객체를 인자로 받는 대상 | `MagicMock(spec=…)` 을 직접 넘긴다 | `spec` 없는 `MagicMock` |
| 모듈 안에서 이름을 직접 부르는 대상 | `@patch("경로")` | 진짜 메일 · 네트워크 호출 |
| 예외가 나야 하는 경우 | `pytest.raises(…, match=…)` | `assert False` 없는 `try` |
| 부동소수점 비교 | `pytest.approx` | `==` |
| 느린 테스트를 평소엔 빼고 싶다 | `@pytest.mark.slow` + `-m "not slow"` | 주석 처리 |

## 핵심 문장

1. **fixture 는 「무엇이 필요한가」만 테스트가 선언하게 한다** — 매개변수 이름이 곧 주문서이고, pytest 가 사슬을 따라 만들어 넣는다.
2. **스코프가 격리와 비용을 가른다** — 기본은 매 테스트 새로, 비싼 것은 세션에 한 번, 치울 것은 `yield` 뒤에서 치운다.
3. **`parametrize` 는 표 한 줄을 테스트 한 번으로 바꾼다** — 경우마다 따로 돌고 따로 판정된다.
4. **테스트 더블은 정해진 값을 돌려주고 호출을 기록한다** — `spec` 으로 없는 이름을 막고, `return_value` 를 빠짐없이 정한다.
5. **의존성을 주입받는 설계가 테스트를 쉽게 만든다** — `UserService(repo)` 이기에 진짜와 가짜를 바꿔 끼울 수 있다.

## 관련 자료

- `dependency-injection` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `repository` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/patterns.json` 의 `testing-patterns`

## 용어 풀이

- **pytest** — 파이썬 테스트를 찾아 돌리고 결과를 보고하는 테스트 도구다.
- **assert** — 조건이 거짓이면 `AssertionError` 를 던지는 파이썬 문이다.
- **fixture** — 테스트가 쓸 준비물을 만들어 같은 이름의 매개변수로 넣어 주는 함수다.
- **conftest.py** — 여기에 둔 fixture 를 같은 디렉토리의 테스트들이 `import` 없이 쓰게 하는 pytest 설정 파일이다.
- **스코프(scope)** — fixture 를 얼마나 자주 새로 만드나 — `function` · `class` · `module` · `session`.
- **yield fixture** — `yield` 앞에서 준비하고 뒤에서 뒷정리하는 fixture 다.
- **파라미터화(parametrize)** — 값 목록의 항목마다 같은 테스트를 한 번씩 돌리는 기능이다.
- **테스트 더블** — 진짜 의존 대상 대신 끼우는 가짜의 통칭이다.
- **스텁(stub)** — 정해진 값을 돌려주는 역할의 테스트 더블이다.
- **목(mock)** — 호출을 기록하고 나중에 검증하는 역할의 테스트 더블이다.
- **MagicMock** — `unittest.mock` 의 범용 가짜 객체로, 스텁과 목을 둘 다 한다.
- **spec** — `MagicMock` 이 흉내 낼 클래스로, 그 클래스에 없는 이름 접근을 막는다.
- **return_value** — 가짜 메서드를 불렀을 때 돌려줄 값이다.
- **patch** — 테스트 동안 경로로 지정한 이름을 가짜로 바꿔치기하는 도구다.
- **의존성 주입** — 쓸 객체를 스스로 만들지 않고 바깥에서 받는 설계다.
- **마커(mark)** — 테스트에 붙이는 이름표로, `-m` 옵션이 이것으로 테스트를 고른다.
- **pytest.approx** — 작은 오차를 허용하는 근사값 비교 도우미다.

## 더 들어가면

- `spec=` 은 이름이 있는지만 막고 인자 개수 · 이름(시그니처)은 확인하지 않는다 — 시그니처까지 맞추려면 `create_autospec` 이나 `patch(..., autospec=True)` 를 쓴다 (확인 필요).
- `patch` 의 경로는 「정의된 곳」이 아니라 「대상이 그 이름을 찾아 쓰는 곳」을 적어야 한다 — `from a import f` 로 가져다 쓴 모듈 `b` 를 시험하면 `"b.f"` 를 고친다 (확인 필요).
- `conftest.py` 의 fixture 는 그 디렉토리 아래 하위 디렉토리의 테스트에도 보인다 (확인 필요).
- `@dataclass` 는 필드를 비교하는 `__eq__` 를 만들어 주므로 `mock_repo.add.assert_called_once_with(User(name="Test", email="test@test.com"))` 처럼 `add` 에 넘긴 객체까지 검증할 수 있다 (확인 필요).
- 파이썬을 `-O` 옵션으로 실행하면 `assert` 문이 제거되어, 원본 같은 맨 `assert` 시뮬레이션은 아무것도 검사하지 않게 된다 (확인 필요).
- pytest 는 `assert` 문을 다시 써서 실패할 때 양쪽 값을 자세히 보여 준다 (확인 필요).
- `AsyncMock` 은 `async def` 메서드를 흉내 내며, 부른 결과를 `await` 할 수 있다 (확인 필요).
- `@pytest.mark.slow` 같은 직접 만든 마커는 `pytest.ini` · `pyproject.toml` 에 등록하지 않으면 경고가 날 수 있다 (확인 필요).
- pytest 는 `tmp_path`(임시 디렉토리) · `monkeypatch`(속성 · 환경 변수 바꾸기) 같은 내장 fixture 도 준다 (확인 필요).
