# python/python-stdlib/15 — pytest 기초 — 정리 (힌트)

> 출처 — study-site 항목 `python/pytest-basics`(항목 데이터 `data/python/stdlib.json`) · 정답 코드 study-practice `python/python-stdlib/reference/pytest-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**pytest 는 「식당 주방의 검수 담당」이다.**
요리사(테스트 함수)는 접시가 맞는지 한 줄로 확인만 하면 된다.
재료 손질과 설거지는 보조 요리사(fixture)가 맡는다.
보조는 재료를 건네고(`yield`) 기다렸다가, 요리가 끝나면 뒷정리를 한다.
같은 레시피를 재료만 바꿔 여러 번 만들 때는 주문표(`parametrize`)를 한 장 붙인다.
접시마다 「느림」「오늘은 안 냄」「실패할 줄 앎」 같은 꼬리표(`mark`)를 달아 고를 수 있다.
pytest 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 요리사의 「맞나?」 한 줄 확인 | `assert` 문 |
| 보조 요리사 | `@pytest.fixture` 함수 |
| 재료를 건네는 순간 | `yield` |
| 요리 뒤 설거지 | `yield` 뒤의 줄(teardown) |
| 주방 공용 보조 명단 | `conftest.py` |
| 재료만 바꾼 주문표 | `@pytest.mark.parametrize` |
| 접시의 꼬리표 | `@pytest.mark.slow` · `skip` · `skipif` · `xfail` |

```text
   pytest 실행
       │
       ▼
  test_xxx(db) ──── 인자 이름 "db" 를 보고 ───▶ @pytest.fixture def db()
       │                                          │  setup
       │◀──────────── yield database ─────────────┘
       │  assert ... (테스트 몸통)
       ▼
  테스트 끝 ───────────────────────────────▶ yield 뒤 줄: database.close()  (teardown)
```

## 이 주제가 답하려는 질문

1. 기대한 값이 나왔는지, 기대한 예외가 났는지를 어떻게 가장 짧게 확인하나?
2. 테스트마다 필요한 준비물과 뒷정리를 어떻게 나누어 주고, 얼마나 오래 살려 두나?
3. 같은 검사를 입력만 바꿔 여러 번 돌리려면 어떻게 하나?
4. 어떤 테스트는 골라 돌리고, 어떤 테스트는 건너뛰거나 「실패가 정상」으로 두려면 어떻게 하나?

## 동작 방식

### (1) `assert` · `pytest.raises` · `pytest.approx` — 확인 세 가지

**언제 쓰나** — 값이 같은지(`assert`), 예외가 나는지(`pytest.raises`), 부동소수가 거의 같은지(`pytest.approx`)를 확인할 때.

pytest 의 테스트는 평범한 `assert` 문이다.
`unittest` 처럼 `assertEqual` 같은 메서드를 부르지 않는다.

> **assert** — 뒤의 식이 거짓이면 `AssertionError` 를 던지는 파이썬 문.\
> 예: `assert 1 + 1 == 2` 는 아무 일 없이 지나간다.

```text
assert 'hello'.upper() == 'HELLO'
      └ 참 ─▶ 다음 줄로
      └ 거짓 ─▶ AssertionError ─▶ pytest 가 양쪽 값을 비교해 차이(diff)를 보여 준다

with pytest.raises(ValueError, match="zero"):
    divide(10, 0)
      └ ValueError 가 나고, 메시지 "Cannot divide by zero" 안에 "zero" 가 있나? ─▶ 통과
      └ 예외가 안 나거나 다른 종류면 ─▶ 테스트 실패

divide(10, 3) == pytest.approx(3.333, rel=1e-3)
      └ 3.3333… 와 3.333 의 차이가 기대값의 0.1 % 안인가? ─▶ 통과
```

- 첫 그림: `assert` 가 참이면 그냥 지나가고, 거짓이면 예외가 나며 pytest 가 그 실패를 자세히 풀어 보여 준다.
- 둘째 그림: `pytest.raises` 는 `with` 블록 안에서 지정한 예외가 **나야** 통과다.
- `match` 는 정규표현식이고, 메시지 전체가 아니라 메시지 **안 어딘가**에서 찾는다(`re.search`).
- 셋째 그림: `10 / 3` 은 끝없는 소수라 `3.333` 과 정확히 같지 않으므로, `approx` 로 허용 오차를 준다.
- `rel=1e-3` 은 상대 오차 0.1 % 까지 같다고 본다는 뜻이다.

> **pytest.approx** — 부동소수 비교에 허용 오차를 주는 pytest 의 도우미.\
> 예: `0.1 + 0.2 == pytest.approx(0.3)`.

### (2) fixture — 인자 이름으로 받는 준비물

**언제 쓰나** — 여러 테스트가 같은 준비(DB 객체, 샘플 데이터)를 필요로 하고, 끝나면 정리까지 해야 할 때.

> **fixture** — 테스트에 필요한 준비물을 만들어 건네는 함수. `@pytest.fixture` 를 붙인다.\
> 예: `def test_db_insert(db):` 의 `db` 자리에 `db()` fixture 가 만든 값이 들어온다.

> **의존성 주입** — 필요한 것을 스스로 만들지 않고 바깥에서 받아 쓰는 방식.\
> 예: 테스트는 `Database()` 를 직접 부르지 않고 인자 `db` 로 받는다.

```text
@pytest.fixture
def db():
    database = Database()     ① setup  : 새 Database, connected=True
    yield database            ② 테스트에게 건네고 여기서 멈춤
    database.close()          ④ teardown: connected=False

def test_db_insert(db):       ③ 테스트 몸통 실행
    db.insert('key', 'value')
    assert db.get('key') == 'value'
```

- ① pytest 는 테스트의 인자 이름 `db` 를 보고 같은 이름의 fixture 를 찾아 부른다.
- ② `yield` 에서 값을 테스트에 넘기고 fixture 는 멈춘다.
- ③ 테스트 몸통이 그 값을 쓴다.
- ④ 테스트가 끝나면 fixture 가 `yield` 다음 줄부터 이어 돌아 정리한다.
- `yield` 하나로 setup 과 teardown 을 한 함수에 적을 수 있다.

> **setup / teardown** — 테스트 전에 준비하는 일 / 테스트 뒤에 정리하는 일.\
> 예: `Database()` 를 만드는 것이 setup, `close()` 가 teardown 이다.

fixture 는 다른 fixture 를 인자로 받을 수 있다(의존성 체인).

```text
test_sample_data(sample_data)
        │ 필요
        ▼
sample_data(db) ── user1·user2 를 넣고 db 를 돌려준다
        │ 필요
        ▼
db() ── 새 Database 를 yield
```

- pytest 는 아래쪽(`db`)부터 만들고, 그 값을 `sample_data` 에 넣고, 그 결과를 테스트에 넣는다.
- `sample_data` 는 `return` 을 쓰므로 정리할 일이 없지만, 그 밑의 `db` 의 teardown 은 그대로 돈다.

### (3) scope — fixture 를 얼마나 오래 살리나

**언제 쓰나** — 만들기 비싼 준비물(설정 읽기 등)을 여러 테스트가 나눠 써도 될 때.

> **scope** — fixture 값 하나가 살아 있는 범위.\
> 예: `scope='module'` 이면 한 파일 안의 테스트들이 같은 값을 받는다.

```text
scope='function' (기본값)  test_a ─[새 값]  test_b ─[새 값]  test_c ─[새 값]
scope='class'              class 안 테스트들 ─[값 1개]
scope='module'             파일 하나의 테스트들 ─[값 1개]
scope='session'            pytest 한 번 실행 전체 ─[값 1개]
```

- `function` 은 테스트마다 fixture 를 새로 부른다. 지정하지 않으면 이것이다.
- `class` 는 테스트 클래스 하나에 한 번, `module` 은 모듈(파일) 하나에 한 번, `session` 은 실행 전체에 한 번이다.
- 범위가 넓을수록 한 테스트가 값을 바꾸면 다음 테스트가 그 바뀐 값을 받는다.
- 예: `module_resource` 는 `[]` 를 돌려주는데, 한 테스트가 여기에 `append` 하면 같은 모듈의 다음 테스트는 빈 리스트가 아닌 것을 받는다.

### (4) parametrize — 같은 로직, 여러 입력

**언제 쓰나** — 검사 로직은 같고 입력과 기대값만 바뀔 때(테이블 드리븐 테스트).

> **parametrize** — 매개변수 이름과 값 목록을 주어 한 테스트 함수를 여러 케이스로 늘리는 mark.\
> 예: 튜플 4개를 주면 테스트 케이스 4개가 된다.

> **테이블 드리븐 테스트** — 입력과 기대값을 표처럼 늘어놓고 같은 검사를 돌리는 방식.\
> 예: `(1, True)`, `(0, False)` 를 한 줄씩 적는다.

```text
@pytest.mark.parametrize("input_val,expected", [(1,True),(0,False),(-1,False),(100,True)])
def test_is_positive(input_val, expected): ...
            │
            ▼
  케이스 1: input_val=1,   expected=True
  케이스 2: input_val=0,   expected=False
  케이스 3: input_val=-1,  expected=False
  케이스 4: input_val=100, expected=True     ← 넷이 각각 별도 테스트
```

- 첫 인자는 콤마로 구분한 매개변수 이름 문자열이고, 함수의 인자 이름과 같아야 한다.
- 목록의 튜플 하나가 케이스 하나다.
- 한 케이스가 실패해도 다른 케이스는 따로 판정된다.
- `pytest.param("hello", 5, id="english")` 처럼 쓰면 케이스에 이름(ID)을 붙여 결과 표시가 읽기 쉬워진다.
- `len("안녕하세요")` 는 글자 수 5 라서 `"hello"` 와 기대값이 같다.

### (5) mark — 꼬리표로 고르고 건너뛰기

**언제 쓰나** — 느린 테스트를 평소에는 빼고 싶을 때, 아직 못 만든 기능의 테스트를 잠시 두고 싶을 때, 알려진 버그를 표시할 때.

> **mark** — 테스트에 붙이는 꼬리표. `@pytest.mark.이름` 으로 단다.\
> 예: `@pytest.mark.slow`.

```text
@pytest.mark.slow                 몸통 실행. -m 'slow' / -m 'not slow' 로 고르거나 뺄 수 있다
@pytest.mark.skip(reason=...)     몸통 실행 안 함. 무조건 건너뜀
@pytest.mark.skipif(조건, ...)     조건이 참이면 건너뜀 (원본은 True 라 늘 건너뜀)
@pytest.mark.xfail(reason=...)    몸통 실행. 실패가 예상된 것으로 기록 → 전체 실패로 세지 않음
```

- `slow` 는 pytest 가 미리 정한 이름이 아니라 사용자가 붙인 꼬리표다.
- `skip` 과 `skipif` 의 `reason` 은 왜 건너뛰었는지 남기는 글이다.
- `skipif` 는 플랫폼이나 버전처럼 조건에 따라 건너뛸 때 쓴다.
- `xfail` 테스트는 몸통이 돌고, `assert 1 == 2` 처럼 실패해도 「예상된 실패」로 기록된다.

> **xfail** — expected failure. 실패할 것을 알고 표시해 두는 mark.\
> 예: 알려진 버그를 고치기 전까지 그 테스트에 단다.

### (6) `conftest.py` 와 `autouse` — 공용 fixture

**언제 쓰나** — 여러 테스트 파일이 같은 fixture 를 써야 할 때.

> **conftest.py** — pytest 가 스스로 찾아 읽는 파일. 여기 정의한 fixture 는 같은 디렉터리 트리의 테스트가 import 없이 쓴다.\
> 예: `auth_token`, `api_client` 를 여기 두면 어느 테스트든 인자로 받는다.

```text
tests/
 ├─ conftest.py      reset_state (autouse) · auth_token · api_client(auth_token)
 ├─ test_a.py        def test_x(api_client): ...  ← import 없이 받음
 └─ test_b.py        def test_y(): ...            ← 인자에 없어도 reset_state 는 돈다
```

- pytest 가 `conftest.py` 를 자동으로 읽으므로, 테스트 파일은 그 fixture 를 import 하지 않는다.
- `api_client(auth_token)` 처럼 conftest 안에서도 fixture 체인을 만들 수 있다.
- `autouse=True` 인 fixture 는 테스트가 인자로 부르지 않아도 모든 테스트에 자동으로 적용된다.
- 편하지만, 테스트 코드만 보고는 무엇이 돌았는지 보이지 않아 명시성이 떨어진다.

> **autouse** — 인자로 요청하지 않아도 모든 테스트에 자동 적용되게 하는 fixture 옵션.\
> 예: `@pytest.fixture(autouse=True)`.

### (7) 내장 fixture — `monkeypatch` · `tmp_path` · `capsys`

**언제 쓰나** — 환경 변수나 함수를 잠시 바꿀 때, 임시 파일이 필요할 때, `print` 출력을 검사할 때.

이 셋도 fixture 라서 받는 방법은 `db` 와 같다 — 테스트 인자 이름으로 받는다.

```text
def test_monkeypatch(monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')               환경 변수 임시 설정
    monkeypatch.setattr('os.path.exists', lambda x: True)  함수 임시 교체
                       ── 테스트 끝 ──▶ 둘 다 원래대로 자동 복원

def test_tmp_path(tmp_path):     tmp_path = 이 테스트만의 임시 디렉터리(Path 객체)
    (tmp_path / "test.txt").write_text("hello") ─▶ read_text() == "hello"

def test_capsys(capsys):
    print("captured output")     화면 대신 capsys 가 가로챔
    capsys.readouterr().out ─▶ "captured output\n"   (읽고 나면 버퍼가 비워짐)
```

- `monkeypatch` 는 바꾼 것을 테스트가 끝날 때 되돌려 놓으므로 다른 테스트에 번지지 않는다.
- `setattr` 에 `'os.path.exists'` 처럼 경로 문자열을 주면 그 자리의 함수를 바꾼다.
- `tmp_path` 는 테스트마다 따로 주어지는 디렉터리라 파일이 서로 섞이지 않는다.
- `capsys.readouterr()` 는 지금까지 쌓인 stdout · stderr 를 `out` · `err` 로 돌려주고 버퍼를 비운다.
- print 의 줄바꿈까지 담기므로 기대값 끝에 `\n` 이 있다.

> **monkeypatch** — 환경 변수 · 속성 · 함수를 테스트 동안만 바꾸는 pytest 내장 fixture.\
> 예: `monkeypatch.setenv('API_KEY', 'test-key')`.

## 문법 — 형태와 규칙

```python
import pytest

@pytest.fixture
def numbers():
    data = [3, 1, 2]       # setup
    yield data
    data.clear()           # teardown

@pytest.mark.parametrize("x,expected", [(4, 2), (9, 3)])
def test_sqrt(x, expected):
    assert x ** 0.5 == pytest.approx(expected)

def test_sorted(numbers):
    assert sorted(numbers) == [1, 2, 3]
```

- 테스트는 평범한 함수이고, 확인은 `assert` 로 한다.
- fixture 는 `@pytest.fixture` 를 단 함수이고, 테스트는 **인자 이름**으로 받는다.
- `yield` 앞이 setup, 뒤가 teardown 이다. 정리할 일이 없으면 `return` 으로 돌려줘도 된다.
- `scope` 는 `'function'`(기본) · `'class'` · `'module'` · `'session'` 중 하나다.
- `parametrize` 의 이름 문자열은 `"a,b,expected"` 처럼 콤마로 나누고, 값은 튜플 목록 또는 `pytest.param(..., id=...)` 목록이다.
- `pytest.raises(예외, match=정규식)` 은 `with` 와 함께 쓴다.
- pytest 는 별도 설치가 필요하다: `pip install pytest`.

자주 쓰는 실행 명령은 이렇다.

| 명령 | 하는 일 |
|---|---|
| `pytest` | 모든 테스트 실행 |
| `pytest test_file.py` | 특정 파일만 |
| `pytest -v` | 테스트마다 결과를 자세히 |
| `pytest -k 'test_add'` | 이름으로 거르기 |
| `pytest -m 'not slow'` | mark 로 거르기 |
| `pytest --tb=short` | 트레이스백을 짧게 |
| `pytest -x` | 첫 실패에서 멈춤 |
| `pytest --lf` | 지난번 실패한 것만 다시 |
| `pytest -n 4` | 병렬 실행 — 플러그인 `pytest-xdist` 필요 |
| `pytest --cov=src` | 커버리지 — 플러그인 `pytest-cov` 필요 |

## 어디서 틀리나

### 1. pytest 는 표준 라이브러리가 아니다
이 항목은 「표준 라이브러리」 분류에 있지만 pytest 는 파이썬에 들어 있지 않다.
`pip install pytest` 로 따로 설치해야 한다.

### 2. 「pytest 없이도 기본 테스트 가능」이라는 주석
원본의 주장 → `if __name__ == '__main__':` 블록은 pytest 가 없는 환경에서도 일부 동작 확인용이라고 한다.
왜 의심스러운가 → 파일 위쪽에서 `import pytest` 와 `@pytest.fixture` 가 모듈을 읽는 순간 실행된다.
pytest 가 없으면 그 `import` 에서 멈추므로 `__main__` 블록까지 가지 못한다.
또 `test_divide_normal` 은 몸통에서 `pytest.approx` 를 쓴다.
「pytest 로 실행하지 않아도」는 맞을 수 있지만, 「설치하지 않아도」는 맞지 않는다.

### 3. 직접 실행은 fixture · parametrize 테스트를 돌리지 않는다
`python 파일.py` 로 돌리면 `__main__` 블록이 부르는 `test_addition` 과 `test_divide_normal` 만 돈다.
`db` 를 인자로 받는 테스트는 누가 `db` 를 넣어 주지 않으므로, fixture · parametrize · mark 는 pytest 로 실행해야 뜻이 있다.

### 4. 상세한 diff 는 pytest 가 돌릴 때의 기능이다
파이썬의 `assert` 자체는 실패하면 `AssertionError` 만 던진다.
양쪽 값을 풀어 보여 주는 것은 pytest 가 테스트 모듈의 `assert` 를 가공해 두기 때문이다.
원본 주석은 이를 「어셈블리 분석」이라고 적었는데, 어셈블리를 분석하는 것이 아니라 assert 문을 다시 쓰는 방식으로 알려져 있다(확인 필요).

### 5. 부동소수를 `==` 로 비교한다
`divide(10, 3) == 3.333` 은 거짓이다.
허용 오차가 필요하면 `pytest.approx` 를 쓴다.

### 6. `match` 는 정규표현식이다
`match` 의 문자열은 정규식으로 해석되고 메시지 안에서 찾는다(`re.search`).
`.` · `(` 같은 특수 문자를 글자 그대로 찾으려면 이스케이프해야 한다.

### 7. scope 를 넓게 잡아 테스트끼리 물든다
`module` · `session` scope 의 값을 한 테스트가 바꾸면 다음 테스트가 그것을 받는다.
그러면 테스트 결과가 실행 순서에 따라 달라지는 의존성이 생긴다.
값을 바꾸는 준비물은 기본(`function`) scope 로 둔다.

### 8. `autouse=True` 를 남발한다
편하지만 테스트 코드에 보이지 않는 준비가 끼어든다.
꼭 모든 테스트에 필요한 정리(상태 초기화 등)에만 쓴다.

### 9. `xfail` 을 「통과」로 오해한다
원본의 주장 → 「실패해도 통과로 처리」.
왜 의심스러운가 → 전체 실행을 실패로 만들지 않는다는 점은 맞지만, pytest 는 이를 통과(passed)와 따로 「예상된 실패」로 센다.
반대로 `xfail` 테스트가 성공하는 경우의 표시는 별도이며 설정에 따라 다르다(확인 필요).

### 10. 플러그인 옵션을 기본 기능으로 안다
`-n 4` 는 `pytest-xdist`, `--cov` 는 `pytest-cov` 를 설치해야 쓸 수 있다.

### 11. mock 은 보통 `unittest.mock` 이다
원본은 `monkeypatch` 를 mock 대안으로 보였지만, 원본의 함정 메모대로 mock 객체가 필요하면 `unittest.mock` 을 쓰는 것이 더 일반적이다.

### 12. `readouterr()` 를 두 번 부른다
한 번 부르면 버퍼가 비워진다.
두 번째 호출은 그 사이에 새로 찍힌 것만 돌려준다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `assert` 가 거짓이면 `AssertionError` | 파이썬 언어 |
| 실패한 `assert` 의 상세 비교 표시 | pytest (assert 문 가공 — 원본의 「어셈블리 분석」 표현은 의심, 확인 필요) |
| `10 / 2` 가 `5.0` (float) | 파이썬 언어 (`/` 는 참나눗셈) |
| `10 / 3` 이 `3.333` 과 정확히 같지 않음 | 파이썬 float 표현 — 보통 IEEE 754 배정밀도 (구현이 따르는 표준, 확인 필요) |
| `len("안녕하세요") == 5` | 파이썬 언어 (`str` 은 유니코드 코드 포인트 단위) |
| `match` 가 `re.search` 로 찾음 | pytest (원본 주석) |
| fixture 기본 scope 가 `function` | pytest |
| `monkeypatch` 가 테스트 뒤 자동 복원 | pytest (원본 주석) |
| `readouterr()` 가 버퍼를 비움 | pytest (원본 주석) |
| `xfail` 실패가 전체 실패로 세지지 않음 | pytest — 「통과로 처리」라는 원본 표현은 의심 |
| `-n` · `--cov` | pytest 본체가 아니라 `pytest-xdist` · `pytest-cov` 플러그인 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 값 비교 | `assert a == b` | `assertEqual` 류 메서드 흉내 |
| 부동소수 비교 | `pytest.approx` | `==` 그대로 |
| 예외 확인 | `with pytest.raises(E, match=...)` | `try/except` 로 직접 잡고 플래그 세우기 |
| 준비 + 정리 | `yield` fixture | 테스트마다 같은 준비 코드 복사 |
| 비싼 읽기 전용 준비물 | `scope='session'` · `'module'` | 바뀌는 객체를 넓은 scope 로 |
| 입력만 다른 반복 검사 | `parametrize` (+ `pytest.param(id=...)`) | 테스트 함수 복사 |
| 여러 파일의 공용 fixture | `conftest.py` | 테스트 파일마다 import |
| 환경 변수 · 함수 잠시 바꾸기 | `monkeypatch` | 전역을 직접 바꾸고 되돌리기를 잊기 |
| 임시 파일 | `tmp_path` | 고정 경로에 파일 쓰기 |
| print 확인 | `capsys` | 표준 출력을 손으로 바꿔 끼우기 |

## 핵심 문장

1. **pytest 의 테스트는 `assert` 한 줄이다** — 예외는 `pytest.raises`, 부동소수는 `pytest.approx` 로 확인한다.
2. **fixture 는 인자 이름으로 주입되고, `yield` 앞이 setup · 뒤가 teardown 이다** — fixture 끼리도 인자로 이어진다.
3. **scope 는 fixture 값의 수명이다** — 기본은 테스트마다 새로, 넓힐수록 테스트끼리 상태를 나눈다.
4. **`parametrize` 는 한 함수를 여러 케이스로 늘린다** — 튜플 하나가 테스트 하나다.
5. **mark 로 고르고(`-m`) 건너뛰고(`skip` · `skipif`) 예상된 실패를 표시하며(`xfail`), `conftest.py` 로 fixture 를 공유한다.**

## 관련 자료

- [unittest](../14-unittest/2-summary.md)
- `dataclasses-advanced` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `typing-advanced` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/stdlib.json` 의 `pytest-basics`

## 용어 풀이

- **pytest** — 파이썬 테스트 프레임워크. 표준 라이브러리가 아니라 따로 설치한다.
- **assert** — 식이 거짓이면 `AssertionError` 를 던지는 문.
- **diff** — 기대값과 실제값의 차이를 보여 주는 표시.
- **pytest.raises** — `with` 블록에서 지정한 예외가 나는지 확인하는 컨텍스트 매니저.
- **pytest.approx** — 허용 오차를 둔 근사 비교 도우미.
- **rel** — `approx` 의 상대 허용 오차.
- **fixture** — 테스트 준비물을 만들어 건네는 함수.
- **의존성 주입** — 필요한 것을 바깥에서 받아 쓰는 방식.
- **setup / teardown** — 테스트 전 준비 / 테스트 뒤 정리.
- **scope** — fixture 값이 살아 있는 범위(function · class · module · session).
- **parametrize** — 한 테스트를 여러 입력 케이스로 늘리는 mark.
- **테이블 드리븐 테스트** — 입력 · 기대값 표로 같은 검사를 반복하는 방식.
- **pytest.param / id** — parametrize 케이스 하나와 그 이름.
- **mark** — 테스트에 붙이는 꼬리표.
- **skip / skipif** — 무조건 / 조건부로 건너뛰기.
- **xfail** — 실패가 예상된 테스트 표시.
- **conftest.py** — pytest 가 자동으로 읽는 공용 fixture 파일.
- **autouse** — 요청하지 않아도 모든 테스트에 적용되는 fixture 옵션.
- **monkeypatch** — 환경 변수 · 속성을 테스트 동안만 바꾸는 내장 fixture.
- **tmp_path** — 테스트마다 주어지는 임시 디렉터리(`Path`) 내장 fixture.
- **capsys** — stdout · stderr 를 가로채는 내장 fixture.
- **플러그인** — pytest 에 기능을 더하는 별도 패키지(`pytest-xdist`, `pytest-cov`).

## 더 들어가면

- pytest 는 기본 설정에서 `test_*.py` 또는 `*_test.py` 파일과 `test` 로 시작하는 함수를 테스트로 모은다(확인 필요).
- `@pytest.mark.slow` 같은 사용자 mark 는 `pytest.ini` 등의 `markers` 설정에 등록하지 않으면 경고가 날 수 있다(확인 필요).
- `pytest.approx` 는 상대 오차 말고 절대 오차(`abs`)도 받으며, 둘 중 큰 쪽을 허용 범위로 쓴다고 알려져 있다(확인 필요).
- `xfail(strict=True)` 로 두면 예상 밖으로 성공한 것을 실패로 셀 수 있다(확인 필요).
- 모듈 맨 위의 `print` 는 pytest 가 파일을 모으는(import 하는) 시점에 실행되며, 보통 출력 가로채기 때문에 화면에 바로 보이지 않을 수 있다(확인 필요).
- fixture 의 teardown 은 테스트가 실패해도 실행된다(확인 필요).
- `capsys` 말고 파일 기술자 수준에서 가로채는 `capfd` 도 있다(확인 필요).
