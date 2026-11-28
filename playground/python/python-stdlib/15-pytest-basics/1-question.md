# python/python-stdlib/15 — pytest 기초 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 앞 테스트가 넣은 값과 뒤 테스트 (예측)

```python
# 질문용 발췌
@pytest.fixture
def db():
    database = Database()
    yield database
    database.close()

def test_db_insert(db):
    db.insert('key', 'value')
    assert db.get('key') == 'value'

def test_sample_data(sample_data):   # sample_data 는 db 를 받아 user1 · user2 를 넣고 돌려준다
    ...
```

- `test_db_insert` 가 먼저 돌고 `test_sample_data` 가 뒤에 돈다면, 뒤 테스트 안에서 `sample_data.get('key')` 는 무엇을 돌려주나?
- `test_db_insert` 가 끝난 뒤, 그 테스트가 받았던 `Database` 객체의 `connected` 는 무엇인가?

### 2. 튜플 목록과 `pytest.param` (예측)

```python
# 질문용 발췌
@pytest.mark.parametrize("input_val,expected", [(1, True), (0, False), (-1, False), (100, True)])
def test_is_positive(input_val, expected):
    assert (input_val > 0) == expected

@pytest.mark.parametrize("text,expected", [
    pytest.param("hello", 5, id="english"),
    pytest.param("안녕하세요", 5, id="korean"),
    pytest.param("", 0, id="empty"),
])
def test_string_length(text, expected):
    assert len(text) == expected
```

- `test_is_positive` 는 테스트 몇 개로 세어지나?
- `test_string_length` 의 각 케이스는 결과에서 무엇으로 구분되나?
- `korean` 케이스는 통과하나?

### 3. `10 / 3` 을 두 방식으로 비교하면 (예측)

```python
# 질문용 발췌
def test_a():
    assert divide(10, 3) == pytest.approx(3.333, rel=1e-3)

def test_b():
    assert divide(10, 3) == 3.333
```

- 두 테스트 중 통과하는 것은 어느 쪽인가?

### 4. fixture 가 `return` 대신 `yield` 를 쓰는 까닭 (왜)

- `db` fixture 가 `yield` 를 쓰는 까닭은 무엇인가?
- `yield` 다음 줄은 언제 실행되나?

### 5. `skip` · `skipif` · `xfail` 의 경계 (경계)

- `test_not_implemented` 와 `test_known_bug` 중 몸통이 실제로 실행되는 것은 어느 쪽인가?
- `test_known_bug` 의 `assert 1 == 2` 가 실패해도 전체 실행이 실패로 세지지 않는 까닭은 무엇인가?
- 원본의 `skipif(True, ...)` 는 `skip` 과 결과가 어떻게 다른가?

### 6. `pytest.raises` 의 `match` 는 어디까지 보나 (경계)

- `match="zero"` 대신 `match="Cannot"` 을 주어도 `test_divide_by_zero` 는 통과하나?
- `with` 블록 안의 호출이 아무 예외도 던지지 않으면 테스트는 어떻게 되나?

### 7. scope 를 넓히면 테스트끼리 의존이 생기는 까닭 (왜)

- `module_resource` 처럼 리스트를 돌려주는 fixture 를 `scope='module'` 로 두면 왜 테스트끼리 의존이 생길 수 있나?
- scope 를 지정하지 않은 fixture 는 얼마 만에 새로 만들어지나?

### 8. pytest 가 없는 환경에서 `python` 으로 직접 실행 (경계)

- pytest 를 설치하지 않은 환경에서 이 파일을 `python` 으로 직접 돌리면 `__main__` 블록까지 갈 수 있나?
- pytest 가 설치되어 있어도 `python` 으로 직접 돌릴 때 `test_db_insert` 가 실행되지 않는 까닭은 무엇인가?

### 9. `conftest.py` 와 fixture 체인 · `autouse` (연결)

- 테스트 파일이 `conftest.py` 의 `api_client` 를 import 없이 인자로 받을 수 있는 까닭은 무엇인가?
- `api_client(auth_token)` 은 앞의 `sample_data(db)` 와 어떤 점에서 같은 구조인가?
- `reset_state` 처럼 `autouse=True` 를 붙이면 무엇이 편해지고 무엇을 잃나?

### 10. 내장 fixture 와 직접 만든 fixture 의 다리 (연결)

- `monkeypatch` · `tmp_path` · `capsys` 는 테스트 함수에 어떤 방식으로 들어오나?
- `monkeypatch.setattr` 로 바꾼 `os.path.exists` 는 테스트가 끝난 뒤 어떻게 되나?
- `capsys.readouterr()` 를 연달아 두 번 부르면 두 번째의 `out` 에는 무엇이 들어 있나?

## 실습

### 실습 1. pytest 기능을 한 파일에 모은 테스트 모음 만들기

**만들 것** — assert · 예외 · 근사 비교, fixture 와 scope, parametrize, mark, conftest 예시, 내장 fixture, 실행 명령 목록을 한 파일에 담는다.
pytest 로 돌리면 테스트가 모이고, `python` 으로 직접 돌리면 기본 테스트 두 개를 부르고 안내 문구를 찍는다.

**준비물** — pytest 는 표준 라이브러리가 아니므로 `pip install pytest` 로 설치한다. 명령 목록의 `-n` · `--cov` 는 플러그인(`pytest-xdist` · `pytest-cov`)이 있어야 실제로 쓸 수 있지만, 이 실습에서는 문자열로 찍기만 한다.

**요구 조건**

1단계 — 기본 확인
1. `test_addition` 은 정수 덧셈, 문자열 `upper()`, 리스트 비교를 각각 `assert` 로 확인한다.
2. `divide(a, b)` 는 `b` 가 0 이면 메시지에 `zero` 가 든 `ValueError` 를 던지고, 아니면 `a / b` 를 돌려준다.
3. `test_divide_by_zero` 는 `pytest.raises` 와 `match` 로 그 예외와 메시지를 확인한다.
4. `test_divide_normal` 은 `10 / 2` 가 `5.0` 인지, `10 / 3` 이 `3.333` 과 상대 오차 `1e-3` 안에서 같은지 확인한다.

2단계 — fixture
5. `db` fixture 는 새 `Database` 를 `yield` 로 건네고, 테스트가 끝나면 `close()` 한다.
6. `sample_data` fixture 는 `db` 를 받아 `user1`(Alice, 30) · `user2`(Bob, 25) 를 넣고 `db` 를 돌려준다.
7. `test_db_insert` 는 `db` 를 받아 넣은 값이 다시 읽히는지, `test_sample_data` 는 두 사용자의 이름 · 나이를 확인한다.

3단계 — scope
8. `session` · `module` · `class` · `function` scope 의 fixture 를 하나씩 만들어 각각 dict · list · dict · set 을 돌려준다.

4단계 — parametrize
9. `test_is_positive` 는 `(1, True)` · `(0, False)` · `(-1, False)` · `(100, True)` 네 케이스로 「0 보다 큰가」를 확인한다.
10. `test_add` 는 `(1, 2, 3)` · `(0, 0, 0)` · `(-1, 1, 0)` · `(100, 200, 300)` 네 케이스로 덧셈을 확인한다.
11. `test_string_length` 는 `pytest.param` 과 ID `english` · `korean` · `empty` 로 문자열 길이를 확인한다.

5단계 — mark
12. `slow` mark 를 단 테스트는 잠깐 쉰 뒤 통과한다.
13. `skip` 테스트와 `skipif(True)` 테스트는 각각 이유 문구를 달고 몸통이 비어 있다.
14. `xfail` 테스트는 일부러 실패하는 `assert` 를 담는다.

6단계 — conftest 예시
15. `autouse` 인 `reset_state`, `auth_token`, 그것을 받는 `api_client` 를 담은 conftest 예시를 문자열로 만들어 찍는다.

7단계 — 내장 fixture
16. `test_monkeypatch` 는 환경 변수 `API_KEY` 를 바꾸고 `os.path.exists` 를 늘 참을 돌려주는 함수로 바꾼 뒤 둘 다 확인한다.
17. `test_tmp_path` 는 임시 디렉터리에 `test.txt` 를 쓰고 다시 읽어 확인한다.
18. `test_capsys` 는 한 줄을 `print` 한 뒤 가로챈 `out` 이 그 줄(줄바꿈 포함)인지 확인한다.

8단계 — 실행
19. 명령 목록의 각 줄을 들여 써서 찍는다.
20. `__main__` 블록에서 `test_addition` 과 `test_divide_normal` 을 부르고 안내 문구를 찍는다.

**시작 코드**

```python
# pytest는 별도 설치 필요: pip install pytest
import pytest

print("=== pytest 기본 ===")

def test_addition():
    # TODO: 정수 덧셈, 문자열 upper(), 리스트 비교를 assert 로

def divide(a, b):
    # TODO: b 가 0 이면 ValueError("Cannot divide by zero")
    return a / b

def test_divide_by_zero():
    # TODO: pytest.raises + match 로 divide(10, 0) 확인

def test_divide_normal():
    # TODO: 10/2 와 10/3 (approx, rel=1e-3) 확인

print("\n=== fixture ===")

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

# TODO: db fixture (yield 로 건네고, 뒤에서 close)

# TODO: sample_data fixture (db 를 받아 user1 · user2 넣기)

# TODO: test_db_insert(db), test_sample_data(sample_data)

# TODO: scope 가 session / module / class / function 인 fixture 네 개

print("\n=== parametrize ===")

# TODO: test_is_positive (네 케이스)
# TODO: test_add (네 케이스)
# TODO: test_string_length (pytest.param + id)

print("\n=== mark ===")

# TODO: slow / skip / skipif / xfail 테스트

print("\n=== conftest.py ===")
conftest_example = '''
# TODO: autouse reset_state, auth_token, api_client(auth_token)
'''
print(conftest_example)

# TODO: test_monkeypatch(monkeypatch)
# TODO: test_tmp_path(tmp_path)
# TODO: test_capsys(capsys)

print("=== pytest 실행 명령어 ===")
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
# TODO: 각 명령을 들여 써서 찍기

if __name__ == '__main__':
    # TODO: 기본 테스트 두 개를 부르고 안내 문구 찍기
    pass
```

**확인 방법** — 파일을 `test_pytest_basics.py` 로 저장하고 `pytest test_pytest_basics.py -v` 로 돌려, parametrize 테스트가 케이스마다 따로 표시되는지, `skip` · `skipif` · `xfail` 테스트가 실패로 세어지지 않는지 본다. `python test_pytest_basics.py` 로도 돌려 맨 끝에 안내 문구가 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
