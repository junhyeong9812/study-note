# python/python-stdlib/15 — pytest 기초 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `None` 과 `False` — 테스트마다 새 `Database` 가 오고, 끝나면 닫힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `sample_data.get('key')` 는 `None` 이다.
- `test_db_insert` 가 받았던 객체의 `connected` 는 `False` 다.

**왜 그런가**
- `db` 는 scope 를 지정하지 않았으므로 기본 `function` scope 이고, 테스트마다 새로 불린다.
- `test_sample_data` 가 받는 `db` 는 빈 `data` 를 가진 새 `Database` 이고, `sample_data` 가 넣은 것은 `user1` · `user2` 뿐이다.
- `get` 은 `dict.get` 이므로 없는 키에 `None` 을 돌려준다.
- `test_db_insert` 가 끝나면 fixture 가 `yield` 다음 줄 `database.close()` 를 실행해 `connected` 를 `False` 로 바꾼다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 2. 4개 · ID 로 구분 · `korean` 도 통과

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `test_is_positive` 는 테스트 4개로 세어진다.
- `test_string_length` 의 케이스는 `english` · `korean` · `empty` 라는 ID 로 구분된다.
- `korean` 케이스는 통과한다.

**왜 그런가**
- `parametrize` 는 목록의 튜플 하나를 별도 테스트 케이스 하나로 만든다.
- `pytest.param(..., id=...)` 은 케이스에 이름을 붙여 결과 표시를 읽기 쉽게 한다.
- `len("안녕하세요")` 는 글자 수 5 이므로 기대값 5 와 같다.
- 근거: 2-summary 「동작 방식 (4)」.

### 3. `approx` 를 쓴 `test_a` 만 통과한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `test_a` 는 통과하고 `test_b` 는 실패한다.

**왜 그런가**
- `10 / 3` 은 `3.3333…` 이라 `3.333` 과 정확히 같지 않으므로 `==` 는 거짓이다.
- `rel=1e-3` 은 기대값 `3.333` 의 0.1 %, 곧 약 `0.003333` 까지 차이를 허용한다.
- 실제 차이는 약 `0.000333` 이라 허용 범위 안이다.
- 근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 5」.

### 4. setup 과 teardown 을 한 함수에 담으려고 쓴다

- `yield` 앞의 코드가 setup(새 `Database` 만들기), 뒤의 코드가 teardown(`close()`)이 된다.
- `yield` 에서 값을 테스트에 건네고 멈춰 있다가, 테스트가 끝나면 다음 줄부터 이어서 실행된다.
- `return` 으로는 값을 돌려주는 순간 함수가 끝나므로 뒷정리 자리를 둘 수 없다.
- 근거: 2-summary 「동작 방식 (2)」.

### 5. `xfail` 은 몸통이 돌고, `skip` · `skipif(True)` 는 돌지 않는다

- 몸통이 실행되는 것은 `test_known_bug` 다. `test_not_implemented` 는 `skip` 이라 실행되지 않는다.
- `xfail` 은 실패를 「예상된 실패」로 기록하므로 전체 실행을 실패로 만들지 않는다. 다만 원본 주석의 「통과로 처리」와 달리 통과와는 따로 센다.
- `skipif` 는 조건이 참일 때만 건너뛰는데, 원본은 조건이 `True` 로 고정이라 결과가 `skip` 과 같다 — 늘 건너뛴다. 차이는 조건을 둘 수 있다는 것뿐이다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 9」.

### 6. `match` 는 메시지 안을 찾으므로 `Cannot` 도 통과, 예외가 없으면 실패

- `match` 는 정규식을 메시지 안에서 찾으므로(`re.search`) `"Cannot divide by zero"` 안의 `Cannot` 으로도 통과한다.
- `with` 블록이 예외 없이 끝나면 테스트는 실패한다 — 기대한 예외가 **나야** 통과다.
- 근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 6」.

### 7. 같은 리스트 하나를 모듈 안 테스트들이 나눠 받기 때문이다

- `module` scope 이면 한 파일 안의 테스트들이 같은 리스트 객체를 받는다.
- 앞 테스트가 그 리스트에 원소를 넣으면 뒤 테스트는 빈 리스트가 아닌 것을 받으므로, 결과가 실행 순서에 따라 달라진다.
- scope 를 지정하지 않으면 `function` 이라 테스트마다 새로 만들어진다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 7」.

### 8. 미설치면 갈 수 없고, 설치되어 있어도 fixture 테스트는 돌지 않는다

- pytest 가 없으면 파일 위쪽의 `import pytest` 에서 멈추므로 `__main__` 블록까지 가지 못한다. 원본 주석 「pytest 없이도 기본 테스트 가능」은 「pytest 로 실행하지 않아도」라는 뜻이면 몰라도 「설치하지 않아도」라는 뜻으로는 맞지 않는다.
- 설치되어 있어도 `__main__` 블록은 `test_addition` 과 `test_divide_normal` 만 직접 부른다. `test_db_insert` 는 `db` 를 넣어 줄 pytest 가 실행을 맡지 않으므로 불리지 않는다.
- 근거: 2-summary 「어디서 틀리나 2」 · 「어디서 틀리나 3」.

### 9. pytest 가 `conftest.py` 를 스스로 읽기 때문이다

- pytest 가 `conftest.py` 를 자동으로 읽어, 거기 정의된 fixture 를 같은 디렉터리 트리의 테스트에 인자 이름으로 넣어 준다. 그래서 import 가 필요 없다.
- `api_client(auth_token)` 은 `sample_data(db)` 처럼 fixture 가 다른 fixture 를 인자로 받는 의존성 체인이다.
- `autouse=True` 면 인자로 요청하지 않아도 모든 테스트에 적용되어 상태 초기화 같은 일을 빠뜨리지 않는다. 대신 테스트 코드만 보고는 무엇이 돌았는지 보이지 않아 명시성을 잃는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (6)」 · 「어디서 틀리나 8」.

### 10. 내장 fixture 도 인자 이름으로 들어온다

- 셋 다 pytest 내장 fixture 라서 `db` 와 똑같이 테스트 함수의 인자 이름으로 주입된다.
- `monkeypatch` 로 바꾼 `os.path.exists` 는 테스트가 끝나면 원래 함수로 자동 복원된다.
- `readouterr()` 는 부르면 버퍼를 비우므로, 그 사이에 새로 찍힌 것이 없다면 두 번째 `out` 은 빈 문자열이다.
- 근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 12」.

## 실습 정답

### 실습 1. pytest 기능을 한 파일에 모은 테스트 모음 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 가지 `assert` | `test_addition` |
| 2. 0 이면 `ValueError` | `divide` 의 `if b == 0: raise ValueError("Cannot divide by zero")` |
| 3. 예외 · 메시지 확인 | `test_divide_by_zero` 의 `pytest.raises(ValueError, match="zero")` |
| 4. 나눗셈 값 · 근사 비교 | `test_divide_normal` 의 `pytest.approx(3.333, rel=1e-3)` |
| 5. yield 로 건네고 정리 | `db` fixture 의 `yield database` · `database.close()` |
| 6. fixture 체인 | `sample_data(db)` |
| 7. fixture 받아 확인 | `test_db_insert(db)` · `test_sample_data(sample_data)` |
| 8. scope 네 가지 | `expensive_resource` · `module_resource` · `class_resource` · `function_resource` |
| 9. 양수 판정 네 케이스 | `@pytest.mark.parametrize("input_val,expected", ...)` · `test_is_positive` |
| 10. 덧셈 네 케이스 | `@pytest.mark.parametrize("a,b,expected", ...)` · `test_add` |
| 11. ID 붙인 케이스 | `pytest.param(..., id="english")` 등 · `test_string_length` |
| 12. slow mark | `@pytest.mark.slow` · `test_slow_operation` 의 `time.sleep(0.01)` |
| 13. skip · skipif | `test_not_implemented` · `test_conditional_skip` |
| 14. xfail | `test_known_bug` 의 `assert 1 == 2` |
| 15. conftest 예시 | `conftest_example` 문자열과 `print(conftest_example)` |
| 16. 환경 변수 · 함수 교체 | `test_monkeypatch` 의 `setenv` · `setattr` |
| 17. 임시 파일 | `test_tmp_path` 의 `tmp_path / "test.txt"` |
| 18. print 가로채기 | `test_capsys` 의 `capsys.readouterr()` |
| 19. 명령 목록 찍기 | `for cmd in commands: print(f"  {cmd}")` |
| 20. 직접 실행 | `if __name__ == '__main__':` 블록 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-stdlib/reference/pytest-basics.py`

```python
# [표준 라이브러리] pytest 기초
# 설명: pytest의 assert, fixture, parametrize, mark로 효율적인 테스트 작성
# 팁: pytest는 단순 assert문으로 테스트하며, 실패 시 자동으로 상세한 diff를 보여준다. fixture는 의존성 주입 패턴이며, yield를 사용하면 setup/teardown을 하나의 함수로 작성할 수 있다. parametrize는 같은 로직을 여러 입력으로 테스트할 때 코드 중복을 제거한다. conftest.py에 공통 fixture를 넣으면 자동으로 공유된다.
# 함정: pytest는 표준 라이브러리가 아니라 별도 설치 필요. fixture scope를 잘못 지정하면 테스트 간 상태 공유로 의존성 발생. autouse=True는 편하지만 명시성을 해치므로 신중히. mock은 monkeypatch보다 unittest.mock 사용이 일반적.

# pytest는 별도 설치 필요: pip install pytest
# 실행: pytest test_file.py -v

# === 기본 assert ===
print("=== pytest 기본 ===")

# pytest는 단순 assert문 사용 (unittest의 assertEqual 불필요)
# 실패 시 pytest가 어셈블리 분석으로 상세한 diff를 자동 출력
def test_addition():
    assert 1 + 1 == 2
    assert 'hello'.upper() == 'HELLO'
    assert [1, 2, 3] == [1, 2, 3]

# 예외 테스트: pytest.raises 컨텍스트 매니저
import pytest

# 테스트 대상 함수
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# 예외가 발생하는지, 메시지에 'zero'가 포함되는지 확인
def test_divide_by_zero():
    # match는 정규표현식 (re.search)
    with pytest.raises(ValueError, match="zero"):
        divide(10, 0)

# 부동소수 비교: pytest.approx
def test_divide_normal():
    assert divide(10, 2) == 5.0
    # rel: 상대 오차 허용
    assert divide(10, 3) == pytest.approx(3.333, rel=1e-3)

# === fixture ===
print("\n=== fixture ===")

# 테스트 대상 클래스
class Database:
    def __init__(self):
        self.data = {}
        self.connected = True
    def insert(self, key, value):
        self.data[key] = value
    def get(self, key):
        return self.data.get(key)
    def close(self):
        self.connected = False

# fixture 정의: 함수 인자로 의존성 주입
@pytest.fixture
def db():
    """테스트용 DB (setup + teardown)"""
    # yield 이전: setup
    database = Database()
    yield database          # yield 이전 = setup, 이후 = teardown
    # yield 이후: 테스트 종료 후 실행 (teardown)
    database.close()        # teardown

# fixture가 다른 fixture를 인자로 받아 의존성 체인 구성 가능
@pytest.fixture
def sample_data(db):
    """fixture가 다른 fixture를 사용"""
    db.insert('user1', {'name': 'Alice', 'age': 30})
    db.insert('user2', {'name': 'Bob', 'age': 25})
    return db

# fixture 사용: 테스트 함수의 인자명으로 자동 주입
def test_db_insert(db):
    db.insert('key', 'value')
    assert db.get('key') == 'value'

def test_sample_data(sample_data):
    assert sample_data.get('user1')['name'] == 'Alice'
    assert sample_data.get('user2')['age'] == 25

# === fixture scope ===
# scope: fixture 인스턴스의 생명 주기 (function/class/module/session)
@pytest.fixture(scope='session')     # 전체 세션에서 1번
def expensive_resource():
    return {'config': 'loaded'}

@pytest.fixture(scope='module')      # 모듈당 1번
def module_resource():
    return []

@pytest.fixture(scope='class')       # 클래스당 1번
def class_resource():
    return {}

@pytest.fixture(scope='function')    # 함수당 1번 (기본값)
def function_resource():
    return set()

# === parametrize ===
print("\n=== parametrize ===")

# parametrize: 같은 테스트 로직을 여러 입력값으로 반복 (테이블 드리븐 테스트)
@pytest.mark.parametrize("input_val,expected", [
    (1, True),
    (0, False),
    (-1, False),
    (100, True),
])
def test_is_positive(input_val, expected):
    # 각 튜플이 별도 테스트 케이스로 실행됨
    assert (input_val > 0) == expected

# 여러 파라미터: 콤마로 구분된 이름과 튜플 리스트
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add(a, b, expected):
    assert a + b == expected

# pytest.param + id로 테스트 ID 명시 (출력 가독성↑)
@pytest.mark.parametrize("text,expected", [
    pytest.param("hello", 5, id="english"),
    pytest.param("안녕하세요", 5, id="korean"),
    pytest.param("", 0, id="empty"),
])
def test_string_length(text, expected):
    assert len(text) == expected

# === mark ===
print("\n=== mark ===")

# 커스텀 마크: pytest -m 'slow'로 필터링
@pytest.mark.slow
def test_slow_operation():
    """느린 테스트 (pytest -m 'not slow'로 제외 가능)"""
    import time
    time.sleep(0.01)
    assert True

# skip: 무조건 스킵
@pytest.mark.skip(reason="아직 미구현")
def test_not_implemented():
    pass

# skipif: 조건부 스킵 (예: 플랫폼/버전 의존)
@pytest.mark.skipif(True, reason="조건부 스킵")
def test_conditional_skip():
    pass

# xfail: 실패가 예상되는 테스트 (실패해도 통과로 처리)
@pytest.mark.xfail(reason="알려진 버그")
def test_known_bug():
    assert 1 == 2  # 실패해도 OK

# === conftest.py 패턴 ===
print("\n=== conftest.py ===")
# conftest.py: 같은 디렉토리 트리의 모든 테스트가 공유하는 fixture/플러그인 정의
conftest_example = '''
# conftest.py (같은 디렉토리의 모든 테스트에 자동 적용)
import pytest

@pytest.fixture(autouse=True)
def reset_state():
    """모든 테스트 전에 자동 실행"""
    yield
    # 정리 코드

@pytest.fixture
def auth_token():
    return "test-token-12345"

@pytest.fixture
def api_client(auth_token):
    return {"headers": {"Authorization": f"Bearer {auth_token}"}}
'''
print(conftest_example)

# === monkeypatch (mock 대안) ===
# monkeypatch: pytest 내장 fixture로 환경/속성을 안전하게 임시 변경 (테스트 종료 시 자동 복원)
def test_monkeypatch(monkeypatch):
    """monkeypatch fixture로 환경 수정"""
    # setenv: 환경 변수 설정
    monkeypatch.setenv('API_KEY', 'test-key')
    import os
    assert os.environ['API_KEY'] == 'test-key'

    # setattr: 함수/속성 임시 교체 (mock 대신 사용 가능)
    monkeypatch.setattr('os.path.exists', lambda x: True)
    assert os.path.exists('/nonexistent') == True

# === tmp_path fixture ===
# tmp_path: pytest 내장. 테스트별 고유 임시 디렉토리 (Path 객체)
def test_tmp_path(tmp_path):
    """pytest 내장 임시 디렉토리"""
    file = tmp_path / "test.txt"
    file.write_text("hello")
    assert file.read_text() == "hello"

# === capsys (stdout 캡처) ===
# capsys: stdout/stderr 캡처 fixture
def test_capsys(capsys):
    print("captured output")
    # readouterr: 캡처 후 (out, err) 반환 (호출하면 버퍼 초기화)
    captured = capsys.readouterr()
    assert captured.out == "captured output\n"

# === 실행 예시 ===
print("=== pytest 실행 명령어 ===")
# 자주 쓰는 CLI 옵션 정리
commands = [
    "pytest                      # 모든 테스트 실행",
    "pytest test_file.py         # 특정 파일",
    "pytest -v                   # 상세 출력",
    "pytest -k 'test_add'        # 이름 필터",
    "pytest -m 'not slow'        # 마크 필터",
    "pytest --tb=short           # 짧은 트레이스백",
    "pytest -x                   # 첫 실패에서 중단",
    "pytest --lf                 # 마지막 실패만 재실행",
    "pytest -n 4                 # 병렬 실행 (pytest-xdist)",
    "pytest --cov=src            # 커버리지 (pytest-cov)",
]
for cmd in commands:
    print(f"  {cmd}")

# 직접 실행으로 테스트 (pytest 미설치 환경에서도 일부 동작 확인용)
if __name__ == '__main__':
    # pytest 없이도 기본 테스트 가능
    test_addition()
    test_divide_normal()
    print("\n모든 기본 테스트 통과!")

# 출력:
# === pytest 기본 ===
# (assert 테스트 통과)
# === fixture ===
# (DB fixture 테스트 통과)
# === parametrize ===
# (파라미터화 테스트 통과)
# === mark ===
# (skip, xfail 등 마크 테스트)
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 확인은 모두 `assert` 한 줄이고, 예외와 부동소수만 `pytest.raises` · `pytest.approx` 를 곁들인다.
- fixture 는 인자 이름으로 주입되며, `yield` 가 setup 과 teardown 의 경계다.
- `parametrize` 의 튜플 · `pytest.param` 하나가 케이스 하나다.
- mark 는 꼬리표다 — `slow` 는 `-m` 으로 고르고, `skip` · `skipif` 는 몸통을 건너뛰고, `xfail` 은 몸통을 돌리되 실패를 예상된 것으로 센다.
- `monkeypatch` · `tmp_path` · `capsys` 도 같은 방식으로 받는 내장 fixture 다.
- `__main__` 블록은 기본 테스트 두 개만 부르며, 파일 맨 위의 `import pytest` 때문에 pytest 설치는 여전히 필요하다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
