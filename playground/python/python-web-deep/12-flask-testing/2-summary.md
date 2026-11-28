# python/python-web-deep/12 — Flask 테스팅: pytest와 fixture — 정리 (힌트)

> 출처 — study-site 항목 `python/flask-testing`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/flask-testing.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Flask 테스트는 「무대 리허설」이다.**
진짜 관객(브라우저 · 네트워크) 없이 무대 위에서 대사(요청)를 던지고 배우(라우트 핸들러)가 제대로 받아치는지(응답) 확인한다.
소품(앱 · DB · 로그인한 사용자)은 무대 담당(fixture)이 매 장면 전에 깔아 주고, 장면이 끝나면 치운다.
진짜 불을 쓰는 장면(외부 결제 API)은 가짜 불(Mock)로 바꿔서 안전하게 연습한다.
Flask 의 `test_client()` · pytest 의 fixture · `unittest.mock` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 리허설 무대 | 테스트 함수 하나 |
| 무대 위에서 던지는 대사 | `client.get(...)` · `client.post(...)` |
| 배우의 받아치기 | 라우트 핸들러가 돌려주는 상태 코드와 JSON |
| 무대 담당이 까는 소품 | fixture(`app` · `client` · `db` · `user`) |
| 장면 끝나고 치우기 | DB 롤백 |
| 가짜 불 | `patch.object(...)` 로 바꿔 끼운 Mock |
| 대본의 「상황 · 행동 · 결과」 | Given-When-Then |

```text
  fixture 가 준비 ──▶  테스트 함수  ──▶  client.post(...)  ──▶  핸들러
   (app, db, user)        │                                      │
                          │◀──────── 응답(상태 코드, JSON) ◀──────┘
                          ▼
                    assert 로 확인
                          │
  fixture 가 정리 ◀───────┘  (롤백 · drop_all)
```

## 이 주제가 답하려는 질문

1. 서버를 띄우지 않고 HTTP 요청과 응답을 어떻게 확인하나?
2. 테스트마다 쓰는 앱 · 클라이언트 · DB · 사용자를 어떻게 한 번만 정의하고 다시 쓰나?
3. 테스트끼리 데이터가 섞이지 않게(독립성) 하려면 어떻게 하나?
4. 진짜 외부 서비스(결제 API)를 부르지 않고 그 서비스를 쓰는 코드를 어떻게 검증하나?

## 동작 방식

### (1) test_client — 요청을 흉내 내는 클라이언트

**언제 쓰나** — 라우트가 상태 코드와 JSON 을 맞게 돌려주는지 볼 때 쓴다.
네트워크 · 실제 서버 없이 앱 안으로 바로 요청을 밀어 넣는다.

원본 예제는 Flask 없이 돌도록 `TestClient` 라는 흉내 클래스를 직접 만든다.
라우트 표는 `(메서드, 경로)` 를 키로, 핸들러 함수를 값으로 가진 딕셔너리다.

```text
client.get('/api/items')
   │
   ▼
_request('GET', '/api/items', headers=None)
   │
   ▼
routes.get(('GET', '/api/items'))  ──▶ 찾음 ──▶ list_items(json=None, headers={})
   │                                                   │
   └──▶ 못 찾음 ──▶ {'status_code': 404,               ▼
                     'json': {'error': 'Not Found'}}  {'status_code': 200, 'json': {...}}
```

- `get` · `post` · `put` · `delete` 는 모두 `_request` 로 넘기는 얇은 헬퍼다.
- `post` · `put` 만 `json` 인자를 받고, `get` · `delete` 는 경로와 헤더만 받는다.
- `_request` 는 `(method, path)` 튜플로 라우트 표를 찾는다.
- 표에 없으면 핸들러를 부르지 않고 404 딕셔너리를 바로 돌려준다.
- 있으면 `handler(json=json, headers=headers or {})` 를 부른다 — 헤더가 `None` 이면 빈 딕셔너리로 바꿔 넘긴다.
- 생성자는 `self.cookies = {}` 도 만든다 — 실제 test_client 가 쿠키 저장소(cookie jar)를 가진 것을 흉내 낸 자리다(이 예제에서 쓰지는 않는다).

> **test_client** — Flask 앱 객체에서 꺼내는, 서버 없이 요청을 보내 보는 클라이언트.\
> 예: `app.test_client().get('/api/products')`.

### (2) 핸들러 · 상태 코드 · 인메모리 저장소

**언제 쓰나** — 테스트 대상이 되는 API 의 동작을 정할 때다.
테스트는 이 동작을 `assert` 로 못 박는다.

```text
items_db = []                          (모듈 전역 리스트)

POST json={'name':..., 'price':...}
   │
   ▼
create_item ── json 이 비었거나 'name' 키가 없나? ── 예 ──▶ 400 {'error': 'name is required'}
   │ 아니오
   ▼
item = {'id': len(items_db)+1, **json}
items_db.append(item)  ──▶ 201 item
```

- `list_items` 는 200 과 `{'items': items_db, 'count': len(items_db)}` 를 돌려준다.
- `create_item` 은 `not json` 이거나 `'name' not in json` 이면 400 이다 — 빈 딕셔너리 `{}` 도 `not json` 이 참이라 400 이다.
- 통과하면 `id` 를 「현재 개수 + 1」로 붙이고, 받은 JSON 의 키를 그 뒤에 펼친다.
- 생성 성공은 201(Created), 입력 오류는 400(Bad Request), 없는 경로는 404 다.
- `get_item` 은 경로가 `'/api/items/1'` 로 박혀 있고, 첫 아이템(없으면 `{}`)을 200 으로 돌려준다.
- `items_db` 는 모듈 전역이라 테스트 사이에 남는다 — 원본은 시작할 때 `items_db.clear()` 로 비운다.

> **상태 코드** — 요청이 어떻게 처리됐는지 알리는 세 자리 숫자.\
> 예: 200 성공 · 201 생성됨 · 400 잘못된 요청 · 401 인증 안 됨 · 404 없음.

### (3) fixture 와 scope — 준비물을 이름으로 받아 쓰기

**언제 쓰나** — 여러 테스트가 같은 준비물(앱 · 클라이언트 · DB · 로그인 사용자)을 쓸 때 쓴다.
테스트 함수가 매개변수 이름으로 fixture 를 적으면 pytest 가 그 fixture 를 만들어 넘긴다.
fixture 끼리도 매개변수로 서로를 요청해 사슬을 만든다.

```text
app (session)                ← create_app('testing') 한 번
 ├─▶ _database (session)     ← app_context 안에서 create_all … 끝에 drop_all
 │     └─▶ db (function)     ← 테스트마다 begin_nested … 끝에 rollback
 │           └─▶ user        ← User 를 만들어 add · commit
 └─▶ client                  ← app.test_client()
          └─▶ auth_client (client, user)
                 ← /auth/login 으로 토큰을 받아
                   environ_base['HTTP_AUTHORIZATION'] = 'Bearer <토큰>'
```

- `scope='session'` 은 테스트 묶음 전체에서 한 번만 만든다 — `app` · `_database` 가 그렇다.
- `scope='function'` 은 테스트 함수마다 새로 만든다 — `db` 가 그렇다.
- 재사용(session)은 빠르고, 격리(function)는 안전하다 — 이 둘을 저울질하는 것이 scope 다.
- `yield` 앞은 준비, `yield` 뒤는 정리다 — `_database` 는 `yield` 뒤에서 `drop_all()` 한다.
- `auth_client` 를 요청하면 `client` 와 `user` 가 먼저 만들어지고, `user` 는 `db` 를, `db` 는 `_database` 를, 그 둘은 `app` 을 먼저 요구한다.
- `auth_client` 는 로그인 응답의 `access_token` 을 꺼내 이후 모든 요청 헤더에 `Bearer` 토큰이 붙게 한다.
- 이 fixture 들은 보통 `conftest.py` 에 모아 둔다.

> **fixture** — 테스트가 쓸 준비물을 만들고(필요하면 정리하는) pytest 의 함수.\
> 예: `@pytest.fixture` 를 붙인 `def client(app): return app.test_client()`.

> **scope** — fixture 를 얼마 동안 한 번 만들어 다시 쓸지 정하는 범위.\
> 예: `scope='session'` 은 전체에서 1회, `scope='function'` 은 매 테스트.

### (4) 롤백으로 테스트를 서로 떼어 놓기

**언제 쓰나** — 테스트가 DB 에 쓴 것이 다음 테스트에 남으면 안 될 때다.

```text
_database (session) : create_all ─────────────────────────────── drop_all
                              │                         │
db (function)       :   begin_nested ─ 테스트 A ─ rollback
                                        begin_nested ─ 테스트 B ─ rollback
```

- `db` fixture 는 테스트 직전에 `session.begin_nested()` 로 SAVEPOINT(중첩 트랜잭션)를 연다.
- 테스트가 끝나면 `session.rollback()` 으로 그 안에서 한 변경을 되돌린다.
- 그래서 테이블은 한 번만 만들고(session), 데이터는 매 테스트 깨끗하게(function) 쓴다.
- 원본 팁의 「각 테스트는 DB 를 롤백하여 독립성을 보장한다」가 이 자리다.

> **SAVEPOINT** — 트랜잭션 안에 찍는 중간 저장 지점. 그 지점까지만 되돌릴 수 있다.\
> 예: `begin_nested()` 가 찍고 `rollback()` 이 그 지점으로 되돌린다.

### (5) Given-When-Then 과 parametrize

**언제 쓰나** — 테스트 본문을 읽기 쉽게 나눌 때(Given-When-Then), 같은 테스트를 입력만 바꿔 여러 번 돌릴 때(parametrize)다.

```text
Given : 상품 3개를 만들어 둔다          (상황)
When  : auth_client.get('/api/products') (행동)
Then  : status_code == 200, items 3개     (결과 확인)

@pytest.mark.parametrize('price,expected', [(1000,200),(0,400),(-1,400)])
   └─▶ 같은 테스트가 3번 돈다: price=1000 · 0 · -1
```

- Given-When-Then 은 테스트를 상황 · 행동 · 결과 세 덩어리로 주석을 달아 나누는 구조 패턴이다.
- 실제 Flask 응답은 `response.status_code` · `response.json` 처럼 속성으로 읽는다.
- `test_unauthorized_access` 는 `auth_client` 가 아닌 `client` 를 받아 토큰 없이 요청하고 401 을 기대한다.
- `parametrize` 는 경계값(0, -1)과 정상값(1000)을 한 테스트로 덮는다.

> **parametrize** — 하나의 테스트 함수를 여러 입력 묶음으로 되풀이해 돌리는 pytest 표지.\
> 예: `@pytest.mark.parametrize('price,expected', [...])`.

### (6) Mock 과 patch — 외부 서비스를 가짜로 바꾸기

**언제 쓰나** — 테스트 대상이 네트워크 · 결제 같은 외부 서비스를 부를 때다.
진짜로 부르면 느리고, 결과가 그때그때 달라지고, 돈이 나갈 수 있다.

```text
with patch.object(ExternalPaymentAPI, 'charge') as mock_charge:
        │  (with 안에서만 클래스의 charge 가 Mock 으로 바뀐다)
        ▼
mock_charge.return_value = {'ok': True, 'transaction_id': 'tx_123'}
        ▼
process_payment(50000, 'tok_test')
   └─ api = ExternalPaymentAPI()    ← 새 인스턴스지만 클래스의 charge 가 Mock
   └─ api.charge(50000, 'tok_test') ← RuntimeError 대신 return_value
   └─ {'success': result.get('ok', False)}
        ▼
assert result['success'] == True
mock_charge.assert_called_once_with(50000, 'tok_test')
mock_charge.call_args  ──▶ 어떤 인자로 불렸는지 기록
```

- 진짜 `charge` 는 `RuntimeError("실제 API 호출")` 을 던진다 — 패치하지 않으면 테스트가 터진다.
- `patch.object(클래스, '메서드')` 는 `with` 블록 동안만 그 메서드를 Mock 으로 바꾼다.
- 패치 대상이 인스턴스가 아니라 클래스라서, 함수 안에서 새로 만든 인스턴스도 Mock 을 쓴다.
- `return_value` 로 가짜 응답을 정한다.
- 결과 검증(반환값)과 호출 검증(`assert_called_once_with` — 정확히 한 번, 정확히 이 인자로)을 둘 다 한다.

> **Mock** — 진짜 객체 대신 넣는 가짜 객체. 반환값을 정할 수 있고 어떻게 불렸는지 기록한다.\
> 예: `mock_charge.return_value = {...}` · `mock_charge.call_args`.

> **patch** — 어떤 이름이 가리키는 대상을 잠시 Mock 으로 바꿔 끼우는 `unittest.mock` 의 도구.\
> 예: `with patch.object(ExternalPaymentAPI, 'charge') as m:`.

## 문법 — 형태와 규칙

```python
# 최소 예제 (직접 쓴 것) — fixture 와 test_client 와 Mock 한 자리에
import pytest
from unittest.mock import patch

@pytest.fixture
def client(app):
    return app.test_client()

def test_create(client):
    # Given / When
    res = client.post('/api/items', json={'name': 'A'})
    # Then
    assert res.status_code == 201

def test_pay():
    with patch.object(PaymentAPI, 'charge') as m:
        m.return_value = {'ok': True}
        assert pay(100)['success'] is True
        m.assert_called_once_with(100)
```

- fixture 는 `@pytest.fixture` 를 붙인 함수이고, 테스트는 매개변수 이름으로 받는다.
- 정리가 필요하면 `return` 대신 `yield` 를 쓰고 `yield` 뒤에 정리 코드를 둔다.
- `scope=` 를 주면 만드는 횟수를 바꾼다 — `'session'` · `'function'`.
- `@pytest.mark.parametrize('이름1,이름2', [(값, 값), ...])` 는 묶음마다 테스트를 한 번 돌린다.
- `patch.object(대상, '속성이름')` 은 `with` 와 함께 쓰면 블록이 끝날 때 원래대로 돌아온다.

pytest 실행 명령(원본의 모음):

| 명령 | 하는 일 |
|---|---|
| `pytest` | 전체 실행 |
| `pytest tests/test_products.py` | 특정 파일만 |
| `pytest -k 'test_create'` | 이름이 맞는 테스트만 |
| `pytest -x` | 첫 실패에서 중단 |
| `pytest -v` | 상세 출력 |
| `pytest --cov=app` | 커버리지 |
| `pytest --cov=app --cov-report=html` | 커버리지 HTML 리포트 |

## 어디서 틀리나

### 1. 전역 저장소를 비우지 않으면 테스트가 순서에 묶인다

`items_db` 는 모듈 전역 리스트다.
원본은 맨 앞에서 `items_db.clear()` 를 부르고 첫 GET 이 `count == 0` 이라고 단언한다.
비우지 않고 같은 단언을 다시 돌리면 앞에서 넣은 아이템이 남아 `count == 0` 단언이 깨지고, 새 아이템의 `id` 도 1 이 아니게 된다.
진짜 DB 에서 이 문제를 푸는 것이 `db` fixture 의 롤백이다.

### 2. 유효성 검사는 「키가 있나」만 본다

`create_item` 은 `not json or 'name' not in json` 만 검사한다.
`{}` 는 400 이지만, `{'name': ''}` 처럼 키는 있고 값이 빈 문자열이면 이 검사를 통과한다.
원본의 실제 API 테스트(`test_create_product_validation_error`)는 빈 이름에 400 을 기대한다 — 흉내 핸들러와 실제 API 의 규칙이 다르다는 점을 기억한다.

### 3. parametrize 의 기대값과 생성 테스트의 기대값이 어긋난다

원본의 주장: `test_price_validation` 은 `(1000, 200)` 으로 정상 가격의 POST 에 200 을 기대한다.
왜 의심스러운가: 같은 클래스의 `test_create_product` 는 같은 POST `/api/products` 의 성공에 201 을 기대한다.
같은 엔드포인트의 성공 코드가 둘 중 하나는 틀렸다 — API 가 201 을 돌려주면 `(1000, 200)` 묶음이 실패한다.

### 4. 롤백 격리와 `commit()` 의 만남

원본의 주장: `begin_nested()` 로 SAVEPOINT 를 열고 끝에 `rollback()` 하면 테스트가 격리된다.
왜 의심스러운가: `user` fixture 는 그 안에서 `db.session.commit()` 을 부른다.
`commit()` 이 SAVEPOINT 만 닫는지, 바깥 트랜잭션까지 확정해 롤백으로 되돌릴 수 없게 하는지는 SQLAlchemy 버전 · 설정에 달려 있다(확인 필요).
격리가 깨지면 `user` 가 다음 테스트에 남는다.

### 5. 패치하지 않으면 진짜를 부른다

`ExternalPaymentAPI.charge` 는 진짜 호출을 상징해 `RuntimeError` 를 던진다.
`with patch.object(...)` 블록 밖에서 `process_payment` 를 부르면 그대로 터진다.
결과만 보고 호출 인자를 안 보면 「엉뚱한 금액으로 결제를 불렀다」는 버그를 놓친다 — `assert_called_once_with` 로 인자까지 확인한다.

### 6. 흉내 클라이언트와 실제 클라이언트는 응답 꼴이 다르다

흉내 `TestClient` 는 딕셔너리를 돌려줘서 `response['status_code']` 로 읽는다.
실제 Flask test_client 의 응답은 `response.status_code` · `response.json` 처럼 속성으로 읽는다.
흉내 라우팅은 `(메서드, 경로)` 정확 일치라서 `'/api/items/2'` 처럼 표에 없는 경로는 모두 404 다.

### 7. 인증 상태를 바꾸는 fixture 는 scope 를 조심한다

`auth_client` 는 `client.environ_base` 에 토큰 헤더를 심는다.
`client` 가 매 테스트 새로 만들어지니 괜찮지만, 그 클라이언트를 여러 테스트가 함께 쓰게 되면 토큰이 다른 테스트로 새어 「토큰 없이」 테스트(401 기대)가 깨질 수 있다(원본에 근거 없음 — 추론).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 응답이 `{'status_code': ..., 'json': ...}` 딕셔너리다 | 이 예제의 흉내 구현일 뿐 — 실제 Flask 는 응답 객체(`.status_code` · `.json`) |
| 표에 없는 `(메서드, 경로)` 는 404 다 | 흉내 구현의 `_request` — 실제 Flask 의 404 처리와 같다고 보장하지 않음 |
| `{'id': ..., **json}` 의 키가 `id` 부터 차례로 놓인다 | 언어 보장(딕셔너리는 넣은 순서를 지킨다) |
| fixture 를 매개변수 이름으로 받고 scope 대로 만든다 | pytest 가 보장 |
| `begin_nested()` 가 SAVEPOINT 를 연다 | SQLAlchemy 와 DB 엔진 — DB 가 SAVEPOINT 를 지원해야 한다(확인 필요) |
| `with patch.object(...)` 가 끝나면 원래 메서드로 돌아온다 | `unittest.mock`(표준 라이브러리)이 보장 |
| `call_args` 가 `call(50000, 'tok_test')` 꼴로 찍힌다 | `unittest.mock` 의 표시 형식 — 검증은 문자열 대신 `assert_called_once_with` 로 한다 |
| `environ_base` 에 넣은 값이 이후 요청에 붙는다 | Flask/Werkzeug 의 test client 동작(확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 라우트의 상태 코드 · JSON 확인 | `app.test_client()` | 실제 서버를 띄우고 네트워크로 요청 |
| 여러 테스트가 같은 앱 · 클라이언트를 씀 | fixture(`conftest.py`) | 테스트마다 복사한 준비 코드 |
| 앱 · 테이블 생성처럼 비싼 준비 | `scope='session'` | 매 테스트 새로 생성 |
| 테스트마다 데이터가 깨끗해야 함 | `scope='function'` + 롤백 | session 범위로 데이터 공유 |
| 같은 검사를 입력만 바꿔 여러 번 | `parametrize` | 거의 같은 테스트 함수 여러 개 |
| 결제 · 외부 API 호출이 끼어 있음 | `patch.object` + `return_value` | 진짜 외부 호출 |
| 테스트 본문이 길고 읽기 어려움 | Given-When-Then 주석 | 준비 · 행동 · 확인이 뒤섞인 본문 |

## 핵심 문장

1. **`test_client()` 는 서버 없이 요청을 앱 안으로 밀어 넣는다** — 상태 코드와 JSON 을 `assert` 로 못 박는다.
2. **fixture 는 준비물을 이름으로 받아 쓰게 하고, 서로를 요청해 사슬을 만든다** — `auth_client` → `client` · `user` → `db` → `_database` → `app`.
3. **scope 는 재사용과 격리의 저울이다** — 비싼 것은 session, 더러워지는 것은 function.
4. **테스트는 서로 몰라야 한다** — DB 는 매 테스트 롤백하고, 전역 저장소는 비운다.
5. **외부 서비스는 Mock 으로 바꾸고, 결과와 호출 인자를 둘 다 검증한다.**

## 관련 자료

- [flask-blueprint](../09-flask-blueprint/2-summary.md)
- [flask-auth](../11-flask-auth/2-summary.md)
- [django-testing](../06-django-testing/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `flask-testing`

## 용어 풀이

- **test_client** — 서버 없이 Flask 앱에 요청을 보내 보는 클라이언트.
- **라우트 핸들러** — 특정 메서드 · 경로의 요청을 받아 응답을 만드는 함수.
- **상태 코드** — 요청 처리 결과를 알리는 숫자(200 · 201 · 400 · 401 · 404).
- **fixture** — 테스트 준비물을 만들고 정리하는 pytest 함수.
- **conftest.py** — 여러 테스트 파일이 함께 쓰는 fixture 를 모아 두는 파일.
- **scope** — fixture 를 한 번 만들어 다시 쓰는 범위(session · function).
- **yield fixture** — `yield` 앞은 준비, 뒤는 정리를 하는 fixture.
- **SAVEPOINT** — 트랜잭션 안의 중간 저장 지점.
- **롤백** — 트랜잭션에서 한 변경을 되돌리기.
- **Mock** — 반환값을 정할 수 있고 호출을 기록하는 가짜 객체.
- **patch / patch.object** — 대상을 잠시 Mock 으로 바꿔 끼우는 도구.
- **return_value** — Mock 을 불렀을 때 돌려줄 값.
- **assert_called_once_with** — Mock 이 정확히 한 번, 정확히 그 인자로 불렸는지 확인하는 메서드.
- **call_args** — Mock 이 마지막으로 불린 인자 기록.
- **parametrize** — 한 테스트를 여러 입력 묶음으로 되풀이하는 표지.
- **Given-When-Then** — 테스트를 상황 · 행동 · 결과로 나누는 구조 패턴.
- **커버리지** — 테스트가 코드의 어느 줄을 지나갔는지의 비율.
- **Bearer 토큰** — `Authorization` 헤더에 `Bearer <토큰>` 꼴로 싣는 인증 값.

## 더 들어가면

- `@pytest.fixture` 에 `scope` 를 주지 않으면 기본은 `'function'` 이다(확인 필요).
- scope 에는 `session` · `function` 말고도 `module` · `class` · `package` 가 있다(확인 필요).
- pytest 는 이름이 `Test` 로 시작하는 클래스를 테스트로 모으려 하는데, `__init__` 이 있는 클래스는 모으지 못하고 경고를 낸다 — 흉내 클래스 이름이 `TestClient` 이므로 테스트 파일 안에 두면 이 경고를 볼 수 있다(확인 필요).
- `patch` 는 「정의된 곳」이 아니라 「쓰이는 곳」의 이름을 바꿔야 한다는 규칙이 있다 — `from x import f` 로 가져다 쓴 모듈에서는 그 모듈의 `f` 를 패치한다(확인 필요).
- 원본은 `MagicMock` 을 가져오지만 쓰지 않는다 — `patch.object` 가 기본으로 만들어 주는 Mock 이 `MagicMock` 이다(확인 필요).
- `--cov` 옵션은 pytest 본체가 아니라 `pytest-cov` 플러그인이 준다(확인 필요).
- Flask 테스트 설정(`create_app('testing')`)에서는 보통 `TESTING = True` 와 별도 테스트 DB 주소를 쓴다(확인 필요).
