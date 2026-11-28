# python/python-testing-deep/03 — Mock과 Patch — 정리 (힌트)

> 출처 — study-site 항목 `python/pytest-mock`(항목 데이터 `data/python/testing-deep.json`) · 정답 코드 study-practice `python/python-testing-deep/reference/pytest-mock.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**mock 은 「촬영장의 스턴트 대역」이다.**
위험하거나 비싼 장면(진짜 DB 쓰기, 진짜 네트워크 호출)에는 배우 대신 대역을 세운다.
대역은 감독이 정해 준 대사만 하고, 몇 번 무슨 동작을 했는지는 촬영 기록에 남는다.
`patch` 는 「이 장면을 찍는 동안만 배우를 대역으로 바꿔 두고, 끝나면 원래 배우를 돌려놓는」 조감독이다.
테스트도 똑같은 구조다.
테스트 대상 함수(주연)는 그대로 두고, 그 함수가 부르는 바깥 의존성(조연)만 대역으로 바꾼다.
그 뒤 주연이 조연에게 무엇을 시켰는지 기록을 확인한다.

> **mock** — 진짜 객체 대신 끼워 넣어, 정해 둔 값을 돌려주고 호출을 기록하는 가짜 객체.\
> 예: 진짜 DB 대신 `MagicMock()` 을 서비스에 넘긴다.

| 비유 | 실체 |
|---|---|
| 주연 배우 | 테스트 대상 코드(`UserService.register`, `fetch_weather`) |
| 스턴트 대역 | `MagicMock()` 객체 |
| 감독이 정해 준 대사 | `return_value` · `side_effect` |
| 촬영 기록 | `call_count` · `assert_called_once_with` · `assert_has_calls` |
| 장면 동안만 대역으로 바꾸는 조감독 | `patch` (데코레이터 · `with` · `patch.object`) |

```text
 테스트 ──부름──▶ UserService.register("Alice", "a@b.com")
                        │
            ┌───────────┴────────────┐
            ▼                        ▼
      mock_db (대역)           mock_email (대역)
   find_by_email → None       send_welcome 호출만 기록
   create_user  → {"id": 1}
            │                        │
            └──── 테스트가 기록을 확인 ┘
```

## 이 주제가 답하려는 질문

1. 진짜 DB · 진짜 네트워크 없이 그것에 기대는 코드를 어떻게 테스트하나?
2. 대역이 원하는 값 · 예외 · 차례대로 다른 값을 돌려주게 하려면 무엇을 설정하나?
3. 무엇이 어떤 인자로 몇 번, 어떤 차례로 불렸는지를 어떻게 확인하나?
4. 코드 안에 이미 박혀 있는 의존성(모듈 함수, `@property`)은 어떻게 바꿔 끼우나?

## 동작 방식

### (1) `MagicMock` — 무엇이든 받아 주는 대역

**언제 쓰나** — 협력 객체의 모양(메서드 이름)만 맞으면 되는 대역이 필요할 때 쓴다.
미리 메서드를 정의하지 않아도 된다.

```text
mock = MagicMock()
mock.some_method(1, 2, 3)          ─▶ some_method 라는 자식 mock 이 그 자리에서 생기고 호출이 기록된다
mock.nested.deep.call("hello")     ─▶ nested → deep → call 이 줄줄이 자동으로 생긴다
mock.get_data.return_value = {...} ─▶ 이후 mock.get_data() 는 그 dict 를 돌려준다
```

- 처음 보는 속성 이름에 접근하면 `MagicMock` 이 그 이름의 자식 mock 을 만들어 돌려준다.
- 자식 mock 도 `MagicMock` 이므로 `.nested.deep.call` 처럼 체이닝이 끝없이 이어진다.
- 어느 mock 이든 호출되면 그 호출(인자 포함)이 기록에 남는다.
- `return_value` 를 정해 두면 호출했을 때 그 값이 돌아온다.

> **MagicMock** — 속성 · 메서드 접근에 자동으로 자식 mock 을 만들어 주는 `unittest.mock` 의 mock 클래스.\
> 예: `MagicMock().아무이름(1)` 이 오류 없이 불린다.

> **return_value** — mock 을 호출했을 때 돌려줄 값을 정하는 속성.\
> 예: `mock.get_data.return_value = {"key": "value"}`.

### (2) `side_effect` — 고정 값보다 강한 대사

**언제 쓰나** — 호출할 때마다 값이 달라야 하거나, 예외가 나야 하거나, 인자에 따라 답이 바뀌어야 할 때 쓴다.

```text
mock.dangerous.side_effect = ValueError("에러!")   ─▶ 부르면 ValueError 가 던져진다
mock.next_item.side_effect = [1, 2, 3]             ─▶ 첫 호출 1, 둘째 2, 셋째 3
mock.compute.side_effect = lambda x: x * 2         ─▶ compute(5) → 10, compute(3) → 6
```

- 예외 객체를 넣으면 호출 순간 그 예외가 발생한다 — 실패 경로를 시험할 때 쓴다.
- 리스트를 넣으면 호출할 때마다 다음 원소를 하나씩 돌려준다.
- 함수를 넣으면 mock 이 받은 인자로 그 함수를 불러 그 반환값을 돌려준다.
- `return_value` 는 「항상 같은 값」, `side_effect` 는 「호출마다 정해지는 동작」이라고 기억하면 된다.

> **side_effect** — mock 이 호출될 때 일어날 일(예외 · 차례대로 꺼낼 값 · 대신 부를 함수)을 정하는 속성.\
> 예: `mock.next_item.side_effect = [1, 2, 3]`.

### (3) 호출 검증 — 촬영 기록 읽기

**언제 쓰나** — 대상 코드가 협력자를 「올바른 인자로 · 올바른 횟수만큼 · 올바른 차례로」 불렀는지 확인할 때 쓴다.

```text
mock.process(1); mock.process(2); mock.process(3)
        │
        ▼  기록: [call(1), call(2), call(3)]
assert_has_calls([call(1), call(2), call(3)])  ─▶ 이 차례로 불렸으면 통과
call_count                                     ─▶ 3
mock.save({"name": "Alice", "timestamp": 1234567890})
assert_called_with({"name": "Alice", "timestamp": ANY})  ─▶ timestamp 는 무엇이든 통과
```

- `assert_called_once_with(...)` 는 정확히 한 번 불렸고 그 인자가 이것인지 본다.
- `assert_called_with(...)` 는 마지막 호출의 인자가 이것인지 본다 — 횟수는 따지지 않는다.
- `assert_not_called()` 는 한 번도 불리지 않았는지 본다 — 「일어나면 안 되는 부작용」을 막는 검증이다.
- `call_count` 는 불린 횟수 숫자다.
- `assert_has_calls([...])` 는 `call(...)` 목록의 차례대로 불렸는지 본다.
- `ANY` 는 어떤 값과 비교해도 같다고 판정되는 특수 값이라, 인자 중 일부(타임스탬프처럼 매번 바뀌는 값)만 무시할 수 있다.
- 검증이 어긋나면 `AssertionError` 가 나서 테스트가 실패한다.

> **call** — 「이 인자로 한 번 불림」을 나타내는 비교용 객체.\
> 예: `call(1)` 은 `mock(1)` 한 번과 같다고 판정된다.

> **ANY** — 무엇과 비교해도 같다고 답하는 값, 인자 일부를 무시할 때 쓴다.\
> 예: `{"timestamp": ANY}` 는 타임스탬프가 무엇이든 맞는다.

### (4) 주입으로 격리 — `UserService`

**언제 쓰나** — 대상 클래스가 의존성을 생성자 인자로 받도록 짜여 있을 때 쓴다.
이때는 `patch` 가 필요 없다.

```text
mock_db.find_by_email.return_value = None        (stub: 중복 없음)
mock_db.create_user.return_value = {"id": 1, ...}
service = UserService(mock_db, mock_email)        ─▶ 진짜 대신 대역이 들어간다
service.register("Alice", "a@b.com")
   1) self.db.find_by_email("a@b.com") → None → 통과
   2) self.db.create_user("Alice", "a@b.com") → {"id": 1, ...}
   3) self.email_client.send_welcome("a@b.com", "Alice")
   4) user 반환
테스트: result["id"] == 1, 세 협력자 각각 assert_called_once_with
```

- `register` 는 협력자를 세 번 부른다 — 중복 검사 → 생성 → 환영 메일.
- 중복 검사가 참(예: `{"id": 1}`)이면 `ValueError("이미 존재하는 이메일")` 을 던지고 그 아래 두 호출은 일어나지 않는다.
- 그래서 실패 경로 테스트는 `pytest.raises(ValueError, match=...)` 로 예외를 확인한 뒤 `send_welcome.assert_not_called()` 로 「메일이 나가지 않았음」까지 확인한다.
- `return_value` 로 정해진 값만 돌려주게 하는 쪽을 stub, 호출 기록을 검증하는 쪽을 mock(행동 검증)이라 부른다 — 같은 `MagicMock` 객체가 두 역할을 함께 한다.

> **의존성 주입(DI)** — 객체가 쓸 협력자를 안에서 만들지 않고 바깥에서 넘겨받게 짜는 방식.\
> 예: `UserService(db, email_client)`.

> **stub** — 정해진 값만 돌려주는 대역, 상태를 꾸미는 데 쓴다.\
> 예: `find_by_email.return_value = None`.

> **pytest.raises** — 블록 안에서 특정 예외가 나야 통과하는 pytest 도구, `match=` 로 메시지도 맞춘다.\
> 예: `with pytest.raises(ValueError, match="이미 존재하는 이메일"):`.

### (5) `patch` — 이름을 잠시 바꿔 끼우기

**언제 쓰나** — 대상 코드가 의존성을 인자로 받지 않고 모듈 이름으로 직접 부를 때 쓴다(`fetch_weather` 안의 `urllib.request.urlopen`).

```text
@patch('urllib.request.urlopen')
def test_fetch_weather(mock_urlopen):        ◀ 교체된 mock 이 인자로 들어온다
    mock_urlopen.return_value = mock_response
    mock_response.read.return_value = b'{"city": "Seoul", "temp": 20}'
    fetch_weather("Seoul")
        └ urllib.request.urlopen(url)   ─▶ 진짜 대신 mock_urlopen 이 불린다
        └ response.read()               ─▶ JSON 바이트
        └ json.loads(...)               ─▶ {"city": "Seoul", "temp": 20}
테스트 함수가 끝나면 urllib.request.urlopen 은 원래대로 돌아온다
```

- `patch('모듈.이름')` 은 그 모듈의 그 이름을 mock 으로 바꿔 둔다.
- 데코레이터로 쓰면 테스트 함수가 도는 동안만 바뀌고, 교체된 mock 이 함수의 인자로 들어온다.
- `with patch(...) as m:` 으로 쓰면 `with` 블록 안에서만 바뀐다 — 테스트 일부만 격리할 때 좋다.
- `patch.object(대상객체, '속성이름', ...)` 는 문자열 경로 대신 객체를 직접 지정한다.
- mock 이 돌려줄 값이 또 객체라면(`urlopen` → 응답 객체), 그 객체도 `MagicMock` 으로 만들어 `return_value` 로 이어 준다.
- 진짜 네트워크에 닿지 않으므로 테스트가 빠르고, 바깥 서버 상태에 좌우되지 않는다.

> **patch** — 지정한 경로의 객체를 테스트 동안 mock 으로 바꾸고 끝나면 되돌리는 `unittest.mock` 의 도구.\
> 예: `@patch('urllib.request.urlopen')`.

> **컨텍스트 매니저** — `with` 문에 쓰여 블록에 들어갈 때와 나올 때 할 일을 정하는 객체.\
> 예: `with patch('os.path.exists') as m:`.

### (6) `patch` 경로 — 「정의된 곳」이 아니라 「사용되는 곳」

**언제 쓰나** — `patch` 할 문자열 경로를 정할 때마다 따진다.

```text
 (가) mymodule 안:  import os.path
                    os.path.exists(p)        ← 부를 때마다 os.path 에서 exists 를 찾는다
      → patch('os.path.exists')  : 먹힌다

 (나) mymodule 안:  from os.path import exists
                    exists(p)                ← import 순간 mymodule 에 exists 라는 이름이 따로 생겼다
      → patch('os.path.exists')  : mymodule.exists 는 여전히 진짜를 가리킨다
      → patch('mymodule.exists') : 먹힌다
```

- `patch` 는 「어떤 이름표가 가리키는 대상」을 바꾼다.
- `from A import x` 는 그 모듈 안에 `x` 라는 이름표를 새로 붙인다 — 원래 자리(`A.x`)를 바꿔도 이 이름표는 옛 대상을 그대로 가리킨다.
- 그래서 대상 코드가 실제로 찾아 쓰는 이름표, 곧 「사용되는 곳」을 바꿔야 한다.
- `fetch_weather` 는 `import urllib.request` 뒤 `urllib.request.urlopen(url)` 으로 부르므로 호출 순간 `urllib.request` 모듈에서 `urlopen` 을 찾는다 — 그래서 `patch('urllib.request.urlopen')` 이 먹힌다.
- `test_patch_context_manager` 도 같은 꼴이다 — `os.path.exists(...)` 로 부르므로 `patch('os.path.exists')` 가 먹힌다.

### (7) `PropertyMock` — `@property` 바꿔 끼우기

**언제 쓰나** — 대상이 메서드가 아니라 `@property` 일 때 쓴다.

```text
class Config:
    @property
    def debug_mode(self): return False      ← 프로퍼티는 클래스에 붙어 있다

patch.object(type(config), 'debug_mode', new_callable=PropertyMock) as mock_prop
mock_prop.return_value = True
config.debug_mode   ─▶ True      (괄호 없이 속성처럼 읽어도 mock 이 응답)
```

- 프로퍼티는 인스턴스가 아니라 클래스에 정의되어 있다 — 그래서 `type(config)` 로 클래스를 집어 거기에 `patch.object` 한다.
- 프로퍼티는 「호출」이 아니라 「속성 읽기」로 쓰인다 — 보통 mock 을 그 자리에 넣으면 읽었을 때 mock 객체 자체가 나올 뿐 `return_value` 가 쓰이지 않는다.
- `PropertyMock` 은 속성을 읽는 순간을 호출처럼 다뤄 `return_value` 를 돌려준다 (원본에 근거 없음 — 추론).
- `new_callable=PropertyMock` 은 「기본 `MagicMock` 대신 이 클래스로 대역을 만들라」는 뜻이다.

> **PropertyMock** — 속성 읽기에 `return_value` 로 답하는, `@property` 전용 mock.\
> 예: `config.debug_mode` 가 `True` 를 돌려준다.

## 문법 — 형태와 규칙

```python
from unittest.mock import MagicMock, patch, call, ANY

def test_mini():
    repo = MagicMock()
    repo.load.return_value = {"n": 1}        # 고정 반환
    repo.next.side_effect = ["a", "b"]       # 차례대로 반환
    assert repo.load("k") == {"n": 1}
    assert repo.next() == "a"
    repo.load.assert_called_once_with("k")   # 1번 + 인자
    repo.delete.assert_not_called()          # 부작용 없음

    with patch('os.getcwd') as fake:         # 블록 안에서만 교체
        fake.return_value = "/tmp"
        import os
        assert os.getcwd() == "/tmp"
```

| 쓸 것 | 꼴 | 하는 일 |
|---|---|---|
| `MagicMock()` | `m = MagicMock()` | 무엇이든 받는 대역 |
| `return_value` | `m.f.return_value = v` | 호출하면 항상 `v` |
| `side_effect` (예외) | `m.f.side_effect = ValueError(...)` | 호출하면 예외 |
| `side_effect` (리스트) | `m.f.side_effect = [1, 2, 3]` | 호출마다 다음 값 |
| `side_effect` (함수) | `m.f.side_effect = lambda x: x * 2` | 인자로 함수를 부른 값 |
| `assert_called_once_with` | `m.f.assert_called_once_with(a)` | 정확히 1번 + 인자 |
| `assert_called_with` | `m.f.assert_called_with(a)` | 마지막 호출의 인자 |
| `assert_not_called` | `m.f.assert_not_called()` | 한 번도 안 불림 |
| `assert_has_calls` | `m.f.assert_has_calls([call(1), call(2)])` | 이 차례로 불림 |
| `call_count` | `m.f.call_count` | 불린 횟수 |
| `ANY` | `{"t": ANY}` | 그 자리는 무엇이든 |
| `@patch` | `@patch('모듈.이름')` | 함수 동안 교체, mock 이 인자로 |
| `with patch` | `with patch('모듈.이름') as m:` | 블록 동안 교체 |
| `patch.object` | `patch.object(객체, '이름', ...)` | 객체의 속성 교체 |
| `PropertyMock` | `new_callable=PropertyMock` | 프로퍼티 교체 |

- `patch` 경로 문자열은 「사용되는 곳」의 모듈 이름으로 쓴다.
- 프로퍼티는 `type(인스턴스)` — 클래스에 건다.
- 테스트 함수 이름은 `test_` 로 시작해야 pytest 가 모은다.
- 실행은 `pytest 파일이름.py -v` 로 한다.

## 어디서 틀리나

### 1. `patch` 경로를 정의된 곳으로 잡는다
`from os.path import exists` 로 가져온 모듈을 시험하면서 `patch('os.path.exists')` 를 걸면, 대상 코드는 여전히 진짜 `exists` 를 부른다.
원본의 규칙 그대로 — `from os.path import exists` 면 `patch('mymodule.exists')`, `import os.path` 면 `patch('os.path.exists')` 다.
증상은 「mock 을 설정했는데 진짜가 돈다」, 「mock 의 `call_count` 가 0 이다」로 나타난다.

### 2. `return_value` 로 차례값 · 예외를 내려 한다
`return_value = [1, 2, 3]` 은 호출마다 리스트 전체를 돌려줄 뿐이다.
차례대로 꺼내려면 `side_effect` 에 리스트를, 예외를 내려면 `side_effect` 에 예외를, 인자에 따라 바꾸려면 `side_effect` 에 함수를 준다.

### 3. 성공 경로만 시험하고 부작용을 놓친다
실패 경로에서는 「예외가 났다」만으로 부족하다.
예외가 나기 전에 메일이 나가 버렸을 수도 있다.
`assert_not_called()` 로 일어나면 안 되는 호출이 없었음을 함께 확인한다.

### 4. 매번 바뀌는 값 때문에 검증을 통째로 포기한다
타임스탬프 · 무작위 id 가 섞인 인자는 정확한 값으로 맞출 수 없다.
그렇다고 검증을 빼지 말고 그 자리에만 `ANY` 를 넣는다 — 나머지 값은 여전히 검사된다.

### 5. 프로퍼티를 인스턴스에 걸거나 보통 mock 으로 바꾼다
프로퍼티는 클래스에 붙어 있으므로 `type(config)` 에 걸어야 한다.
그리고 속성 읽기는 호출이 아니므로 `new_callable=PropertyMock` 을 줘야 `return_value` 가 쓰인다.

### 6. `assert_called_with` 를 「한 번 불렸다」로 읽는다
`assert_called_with` 는 마지막 호출의 인자만 본다.
횟수까지 고정하려면 `assert_called_once_with` 나 `call_count` 를 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `MagicMock` 이 처음 보는 속성에 자식 mock 을 만든다 | `unittest.mock` 표준 라이브러리의 동작 — 언어 문법이 아니다 |
| `patch` 가 테스트 · `with` 블록이 끝나면 원래 객체를 되돌린다 | `unittest.mock` 의 동작 |
| `from A import x` 가 대상 모듈에 따로 이름을 묶는다 | Python 언어의 `import` 의미 — 그래서 경로 규칙이 생긴다 |
| `urllib.request.urlopen` 처럼 점으로 부르면 호출 순간 모듈 속성을 찾는다 | Python 언어의 속성 조회 의미 |
| `test_` 함수를 모으고 `pytest.raises` 로 예외를 확인한다 | pytest 도구의 규약 — 언어 · 표준 라이브러리가 아니다 |
| 프로퍼티가 클래스에 정의되어 있다 | Python 언어의 디스크립터 규칙 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 의존성을 생성자로 받는 클래스 | `MagicMock` 을 주입 | `patch` (필요 없다) |
| 함수 안에서 모듈 함수를 직접 부름 | `patch('사용되는 곳.이름')` | 정의된 곳 경로 |
| 테스트 일부만 바꿔 끼움 | `with patch(...)` | 함수 전체 데코레이터 |
| 호출마다 다른 값 | `side_effect = [..]` | `return_value = [..]` |
| 실패 경로 시험 | `side_effect = 예외` + `pytest.raises` | 진짜 오류 상황 재현 |
| 바뀌면 안 되는 호출 확인 | `assert_not_called()` | 확인 생략 |
| 인자에 매번 바뀌는 값 | `ANY` | 검증 빼기 |
| `@property` 바꾸기 | `patch.object(type(o), ..., new_callable=PropertyMock)` | 인스턴스에 보통 mock |

## 핵심 문장

1. **mock 은 바깥 의존성의 대역이다** — `return_value` · `side_effect` 로 대사를 주고, `assert_called*` 로 기록을 확인한다.
2. **`side_effect` 는 예외 · 차례값 · 함수 셋을 받는다** — 고정 값이면 `return_value` 로 충분하다.
3. **주입받는 의존성은 mock 을 넘기기만 하면 되고, 박혀 있는 의존성은 `patch` 로 바꾼다.**
4. **`patch` 경로는 사용되는 곳 기준이다** — `from` 으로 가져왔으면 가져간 모듈의 이름을 바꾼다.
5. **실패 경로에서는 `assert_not_called()` 로 부작용이 없음까지 확인한다.**

## 관련 자료

- `pytest-fixtures` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [test-doubles](../07-test-doubles/2-summary.md)
- [test-patterns](../08-test-patterns/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/testing-deep.json` 의 `pytest-mock`

## 용어 풀이

- **mock** — 진짜 대신 끼워 넣어 값을 꾸미고 호출을 기록하는 가짜 객체.
- **MagicMock** — 속성 · 메서드를 자동으로 만들어 주는 mock 클래스.
- **return_value** — mock 호출 때 항상 돌려줄 값.
- **side_effect** — mock 호출 때 일어날 일(예외 · 차례값 · 함수).
- **stub** — 정해진 값만 돌려줘 상태를 꾸미는 대역.
- **행동 검증** — 무엇이 어떻게 불렸는지를 확인하는 검증.
- **assert_called_once_with** — 정확히 1번, 이 인자로 불렸는지 확인.
- **assert_called_with** — 마지막 호출이 이 인자였는지 확인.
- **assert_not_called** — 한 번도 안 불렸는지 확인.
- **assert_has_calls** — 주어진 `call` 목록 차례대로 불렸는지 확인.
- **call_count** — 불린 횟수.
- **call** — 한 번의 호출을 나타내는 비교용 객체.
- **ANY** — 무엇과도 같다고 판정되는 값.
- **patch** — 경로의 객체를 잠시 mock 으로 바꾸고 되돌리는 도구.
- **patch.object** — 객체를 직접 지정해 그 속성을 바꾸는 `patch`.
- **new_callable** — `patch` 가 대역을 만들 때 쓸 클래스를 정하는 인자.
- **PropertyMock** — `@property` 를 바꿀 때 쓰는 mock.
- **의존성 주입(DI)** — 협력자를 바깥에서 넘겨받게 짜는 방식.
- **컨텍스트 매니저** — `with` 블록의 들어감 · 나옴을 다루는 객체.
- **pytest.raises** — 블록 안에서 예외가 나야 통과하는 pytest 도구.
- **spy** — 진짜 동작은 그대로 하면서 호출을 기록하는 대역 (원본 키워드에만 있고 예제에는 없다 — 「더 들어가면」 참고).

## 더 들어가면

- `side_effect` 리스트를 다 쓴 뒤 한 번 더 부르면 `StopIteration` 이 난다고 알려져 있다 (확인 필요).
- `side_effect` 와 `return_value` 를 둘 다 설정하면 `side_effect` 가 우선한다; 다만 `side_effect` 함수가 `mock.DEFAULT` 를 돌려주면 `return_value` 가 쓰인다 (확인 필요).
- `return_value` 를 정하지 않은 `MagicMock` 호출은 새 `MagicMock` 을 돌려주고, 이것은 `if` 에서 참으로 판정된다 — 그래서 `find_by_email.return_value = None` 을 빠뜨리면 `register` 가 「중복」으로 빠진다 (확인 필요).
- `assert_has_calls` 는 앞뒤에 다른 호출이 더 있어도 지정한 호출들이 그 차례로 이어져 있으면 통과하며, `any_order=True` 로 차례를 무시할 수 있다 (확인 필요).
- `@patch` 를 여러 개 겹치면 아래(함수에 가까운) 데코레이터의 mock 이 첫 인자로 들어온다 (확인 필요).
- `MagicMock` 은 없는 메서드 이름도 받아 주므로 오타가 테스트를 통과시킬 수 있다; `create_autospec` 이나 `patch(..., autospec=True)` 로 진짜 시그니처에 맞추게 할 수 있다 (확인 필요).
- 최근 버전은 `assert` 로 시작하는 오타 이름(예: `assret_called`)에 `AttributeError` 를 낸다고 한다 — 어느 버전부터인지는 (확인 필요).
- spy 는 `MagicMock(wraps=진짜객체)` 처럼 진짜를 감싸 만들 수 있다; pytest-mock 플러그인의 `mocker.spy` 도 같은 목적이다 (확인 필요).
- 이 항목의 id 는 `pytest-mock` 이지만 예제는 pytest-mock 플러그인(`mocker` 픽스처)이 아니라 표준 `unittest.mock` 을 pytest 에서 쓰는 꼴이다.
