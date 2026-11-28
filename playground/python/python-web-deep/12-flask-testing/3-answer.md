# python/python-web-deep/12 — Flask 테스팅: pytest와 fixture — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 빈 JSON 은 400, 목록은 여전히 1개

**출력**

```text
  POST (invalid) -> 400, error=name is required
  GET /api/items -> count=1
```

**왜 그런가**

`{}` 는 빈 딕셔너리라 `not json` 이 참이다.
그래서 `create_item` 은 저장하지 않고 400 과 `name is required` 를 돌려준다.
저장이 일어나지 않았으니 목록에는 앞서 만든 'Python 책' 하나만 남아 count 는 1 이다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 201 과 `id` 1 이 붙은 아이템

**출력**

```text
  POST /api/items -> 201, item={'id': 1, 'name': 'Python 책', 'price': 30000}
```

**왜 그런가**

`name` 키가 있으니 검사를 통과한다.
`id` 는 「현재 개수 + 1」 = 0 + 1 = 1 이다.
`{'id': ..., **json}` 이라 `id` 가 먼저 놓이고 받은 키(`name` · `price`)가 그 뒤에 펼쳐진다.
생성 성공이라 201 이다.
근거: 2-summary 「동작 방식 (2)」 · 「구현 세부사항 대 언어 보장」.

### 3. 성공 결과와 호출 인자 기록

**출력**

```text
  결제 결과: {'success': True}
  mock 호출: call(50000, 'tok_test')
```

**왜 그런가**

`patch.object` 가 클래스의 `charge` 를 Mock 으로 바꿨으므로, `process_payment` 안에서 새로 만든 인스턴스의 `charge` 도 Mock 이다.
Mock 은 `RuntimeError` 를 던지지 않고 `return_value` 인 `{'ok': True, ...}` 를 돌려주고, `get('ok', False)` 가 `True` 라서 `success` 가 `True` 다.
`call_args` 는 Mock 이 받은 인자 `(50000, 'tok_test')` 를 기록해 둔 것이다.
근거: 2-summary 「동작 방식 (6)」.

### 4. 둘 다 404 응답 딕셔너리

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

두 호출 모두 `{'status_code': 404, 'json': {'error': 'Not Found'}}` 를 돌려줄 것이다.

**왜 그런가**

`delete` 헬퍼는 있지만 `routes` 에 `('DELETE', '/api/items')` 키가 없다.
`'/api/items/2'` 도 표에는 `'/api/items/1'` 만 박혀 있어서 키가 맞지 않는다.
`_request` 는 정확히 같은 `(메서드, 경로)` 튜플만 찾으므로, 못 찾으면 핸들러를 부르지 않고 404 를 돌려준다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 6」.

### 5. 비싼 준비는 한 번, 더러워지는 데이터는 매번 되돌리려고

앱 생성과 테이블 생성(`create_all`)은 비싸지만 테스트 사이에 바뀌지 않으니 session 범위로 한 번만 한다.
데이터는 테스트가 쓰면서 더러워지니 function 범위의 `db` 가 매 테스트 SAVEPOINT 를 열고 끝에 롤백해 다음 테스트를 깨끗하게 둔다.
재사용(속도)과 격리(독립성)를 함께 얻는 배치다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 6. 느리고 결과가 바뀌고 부작용이 있는 진짜 호출을 떼어 내려고

진짜 외부 API 는 네트워크를 타서 느리고, 그때그때 결과가 달라 테스트가 결정적이지 않으며, 결제라면 실제 돈이 나갈 수 있다.
예제에서도 진짜 `charge` 는 `RuntimeError` 를 던진다.
Mock 으로 바꾸면 응답을 정해 둘 수 있고, `assert_called_once_with` 로 우리 코드가 올바른 인자로 불렀는지까지 확인할 수 있다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 7. 첫 GET 의 `count == 0` 단언이 먼저 깨진다

`items_db` 는 모듈 전역이라 첫 실행에서 넣은 아이템이 남는다.
두 번째 실행의 첫 GET 은 count 가 0 이 아니어서 `assert response['json']['count'] == 0` 에서 `AssertionError` 가 난다.
그 단언을 건너뛴다고 해도 새 아이템의 `id` 는 「현재 개수 + 1」이라 1 이 아니라 그보다 큰 값이 된다.
근거: 2-summary 「어디서 틀리나 1」 · 「동작 방식 (2)」.

### 8. 흉내 핸들러는 통과시키고, 실제 API 테스트는 400 을 기대한다

`create_item` 은 `'name'` 키가 있는지만 보므로 `{'name': ''}` 는 검사를 통과해 저장되고 201 이 돌아온다(코드를 읽어 추론한 것).
반면 원본의 `test_create_product_validation_error` 는 빈 이름에 400 과 `errors` 안의 `name` 을 기대한다.
흉내 핸들러의 검사가 실제 API 의 규칙보다 느슨하다.
근거: 2-summary 「어디서 틀리나 2」.

### 9. 같은 엔드포인트의 성공 코드를 200 과 201 로 다르게 기대한다

`test_create_product` 는 POST `/api/products` 성공에 201 을, `test_price_validation` 의 `(1000, 200)` 은 같은 POST 성공에 200 을 기대한다.
API 가 201 을 돌려주면 `(1000, 200)` 묶음 하나가 실패하고, 200 을 돌려주면 `test_create_product` 가 실패한다.
둘 중 하나는 원본의 오류로 보인다.
근거: 2-summary 「어디서 틀리나 3」.

### 10. app → _database → db → user · client → auth_client, 그리고 Given 칸

pytest 는 요청된 fixture 가 요구하는 fixture 부터 만든다.
`app`(session)이 먼저, 그 위에 `_database`(session, `create_all`)가, 그 위에 `db`(function, `begin_nested`)가 선다.
`user` 가 `db` 를 받아 사용자를 저장하고, `client` 가 `app` 에서 test_client 를 꺼낸다.
마지막으로 `auth_client` 가 `client` · `user` 를 받아 로그인하고 토큰을 헤더에 심는다.
이 준비 전체가 Given(상황)의 일부 — 「로그인한 사용자가 있다」 — 를 테스트 본문 밖으로 꺼내 준 것이고, 본문에는 그 테스트만의 Given 과 When · Then 이 남는다(원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (5)」.

## 실습 정답

### 실습 1. 흉내 test_client 로 API 를 테스트하고 Mock 으로 결제를 격리하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 라우트 · 쿠키 보관 | `TestClient.__init__` 의 `self.routes` · `self.cookies` |
| 2. 메서드별 헬퍼 | `get` · `post` · `put` · `delete` → `self._request('GET', ...)` 등 |
| 3. 디스패치와 404 | `_request` 의 `self.routes.get((method, path))` · `headers or {}` |
| 4. 전역 저장소 | `items_db = []` |
| 5. 목록 | `list_items` |
| 6. 생성 · 검사 | `create_item` 의 `not json or 'name' not in json` · `{'id': len(items_db) + 1, **json}` |
| 7. 단건 | `get_item` |
| 8. 라우트 등록 | `routes = {('GET', '/api/items'): ..., ...}` |
| 9~12. 기본 테스트 | `client = TestClient(routes)` · `items_db.clear()` · 각 `assert` · `"모든 테스트 통과!"` |
| 13. fixture 문자열 | `=== 2. pytest fixture 패턴 ===` 아래 `conftest.py` 문자열 |
| 14. API 테스트 문자열 | `=== 3. API 테스트 패턴 ===` 아래 `TestProductAPI` 문자열 |
| 15. 진짜 결제 | `ExternalPaymentAPI.charge` 의 `raise RuntimeError(...)` |
| 16. 결제 로직 | `process_payment` 의 `result.get('ok', False)` |
| 17. Mock 검증 | `patch.object(ExternalPaymentAPI, 'charge')` · `return_value` · `assert_called_once_with(50000, 'tok_test')` · `call_args` |
| 18. 마무리 출력 | `=== 5. pytest 실행 명령 ===` · `=== 핵심 정리 ===` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/flask-testing.py`

```python
# [웹 프레임워크 심화] Flask 테스팅: pytest와 fixture
# 설명: pytest + Flask test_client, fixture, Mock, API 테스트
# 팁: Flask test_client()로 HTTP 요청을 시뮬레이션하고, pytest fixture로 app/client/db를 재사용한다. 각 테스트는 DB를 롤백하여 독립성을 보장하며, Mock으로 외부 서비스를 격리한다. Given-When-Then 패턴으로 테스트를 구조화하면 가독성이 좋다.

"""Flask 테스팅: pytest, test_client, fixture"""
# json: 요청 본문 직렬화
import json
# 타입 힌트
from typing import Any, Dict
# Mock: 외부 서비스 격리용
from unittest.mock import patch, MagicMock

# === Flask 테스트 시뮬레이션 ===

# 간단한 앱과 테스트 클라이언트
class TestClient:
    """Flask test_client 시뮬레이션"""
    def __init__(self, routes: dict):
        # (method, path) → handler 매핑
        self.routes = routes  # {(method, path): handler}
        # 세션 쿠키 저장 (실제 test_client는 cookie jar 보유)
        self.cookies = {}

    # HTTP 메서드별 헬퍼
    def get(self, path: str, headers: dict = None) -> dict:
        return self._request('GET', path, headers=headers)

    def post(self, path: str, json: dict = None, headers: dict = None) -> dict:
        return self._request('POST', path, json=json, headers=headers)

    def put(self, path: str, json: dict = None, headers: dict = None) -> dict:
        return self._request('PUT', path, json=json, headers=headers)

    def delete(self, path: str, headers: dict = None) -> dict:
        return self._request('DELETE', path, headers=headers)

    # 내부 디스패처: 라우트 매칭 후 핸들러 호출
    def _request(self, method, path, json=None, headers=None):
        handler = self.routes.get((method, path))
        if not handler:
            # 라우트 없으면 404
            return {'status_code': 404, 'json': {'error': 'Not Found'}}
        return handler(json=json, headers=headers or {})

# 인메모리 데이터 저장소 (각 테스트 간 격리하려면 매번 clear 필요)
items_db = []

# GET /api/items: 전체 목록
def list_items(json=None, headers=None):
    return {'status_code': 200, 'json': {'items': items_db, 'count': len(items_db)}}

# POST /api/items: 생성 (유효성 검사 포함)
def create_item(json=None, headers=None):
    if not json or 'name' not in json:
        # 400 Bad Request
        return {'status_code': 400, 'json': {'error': 'name is required'}}
    item = {'id': len(items_db) + 1, **json}
    items_db.append(item)
    # 201 Created
    return {'status_code': 201, 'json': item}

# GET /api/items/1: 단건 조회
def get_item(json=None, headers=None):
    return {'status_code': 200, 'json': items_db[0] if items_db else {}}

# 라우트 매핑 등록
routes = {
    ('GET', '/api/items'): list_items,
    ('POST', '/api/items'): create_item,
    ('GET', '/api/items/1'): get_item,
}

# === 1. 기본 테스트 ===
print("=== 1. Flask 테스트 기본 ===")

# 클라이언트 생성 + DB 초기화
client = TestClient(routes)
items_db.clear()

# GET 테스트: 빈 목록
response = client.get('/api/items')
assert response['status_code'] == 200
assert response['json']['count'] == 0
print(f"  GET /api/items -> {response['status_code']}, count={response['json']['count']}")

# POST 테스트: 정상 생성
response = client.post('/api/items', json={'name': 'Python 책', 'price': 30000})
assert response['status_code'] == 201
assert response['json']['name'] == 'Python 책'
print(f"  POST /api/items -> {response['status_code']}, item={response['json']}")

# 유효성 검사 실패: name 누락 → 400
response = client.post('/api/items', json={})
assert response['status_code'] == 400
print(f"  POST (invalid) -> {response['status_code']}, error={response['json']['error']}")

# 다시 GET: 1개 추가됨
response = client.get('/api/items')
assert response['json']['count'] == 1
print(f"  GET /api/items -> count={response['json']['count']}")

print("\n모든 테스트 통과!")

# === 2. pytest fixture 패턴 ===
print("\n=== 2. pytest fixture 패턴 ===")
# fixture scope: session(전체 1회), function(매 테스트) — 재사용 vs 격리 트레이드오프
# session.begin_nested(): SAVEPOINT로 중첩 트랜잭션 → 테스트 종료 시 ROLLBACK으로 격리
print("""
# conftest.py
import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope='session')
def app():
    '''테스트용 앱 생성'''
    app = create_app('testing')
    yield app

@pytest.fixture(scope='session')
def _database(app):
    '''테스트 DB 초기화'''
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def db(_database):
    '''각 테스트 후 롤백'''
    _database.session.begin_nested()
    yield _database
    _database.session.rollback()

@pytest.fixture
def client(app):
    '''테스트 클라이언트'''
    return app.test_client()

@pytest.fixture
def auth_client(client, user):
    '''인증된 테스트 클라이언트'''
    response = client.post('/auth/login', json={
        'username': user.username,
        'password': 'testpass'
    })
    token = response.json['access_token']
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client

@pytest.fixture
def user(db):
    '''테스트 사용자'''
    from app.models import User
    user = User(username='testuser', email='test@ex.com')
    user.set_password('testpass')
    db.session.add(user)
    db.session.commit()
    return user
""")

# === 3. API 테스트 패턴 ===
print("=== 3. API 테스트 패턴 ===")
# Given-When-Then: 테스트 가독성을 높이는 BDD 스타일 구조화
print("""
# test_products.py
import pytest

class TestProductAPI:
    def test_list_products(self, auth_client, db):
        # Given: 상품 3개 존재
        for i in range(3):
            Product.create(name=f'Product {i}', price=1000 * (i+1))

        # When: 목록 요청
        response = auth_client.get('/api/products')

        # Then: 200 + 3개 반환
        assert response.status_code == 200
        assert len(response.json['items']) == 3

    def test_create_product(self, auth_client):
        response = auth_client.post('/api/products', json={
            'name': 'New Product',
            'price': 15000,
            'stock': 100
        })

        assert response.status_code == 201
        assert response.json['name'] == 'New Product'
        assert Product.query.count() == 1

    def test_create_product_validation_error(self, auth_client):
        response = auth_client.post('/api/products', json={
            'name': '',  # 빈 이름
            'price': -100  # 음수 가격
        })

        assert response.status_code == 400
        assert 'name' in response.json['errors']

    def test_unauthorized_access(self, client):
        response = client.get('/api/products')  # 토큰 없이
        assert response.status_code == 401

    @pytest.mark.parametrize('price,expected', [
        (1000, 200),
        (0, 400),
        (-1, 400),
    ])
    def test_price_validation(self, auth_client, price, expected):
        response = auth_client.post('/api/products', json={
            'name': 'Test', 'price': price
        })
        assert response.status_code == expected
""")

# === 4. Mock 활용 ===
print("=== 4. Mock 활용 ===")

# 외부 결제 API를 흉내내는 클래스 (실제로는 네트워크 호출)
class ExternalPaymentAPI:
    def charge(self, amount, token):
        raise RuntimeError("실제 API 호출")

# 비즈니스 로직: 외부 API 호출하여 처리
def process_payment(amount, token):
    api = ExternalPaymentAPI()
    result = api.charge(amount, token)
    return {'success': result.get('ok', False)}

# patch.object: 컨텍스트 매니저로 메서드를 임시 교체
# 외부 API를 격리하여 테스트 결정성/속도 보장
with patch.object(ExternalPaymentAPI, 'charge') as mock_charge:
    # 반환값 지정
    mock_charge.return_value = {'ok': True, 'transaction_id': 'tx_123'}

    # 비즈니스 로직 실행 (내부에서 mock이 실제 charge 대체)
    result = process_payment(50000, 'tok_test')

    # 결과 검증 + 호출 검증
    assert result['success'] == True
    mock_charge.assert_called_once_with(50000, 'tok_test')
    print(f"  결제 결과: {result}")
    print(f"  mock 호출: {mock_charge.call_args}")

print("\n=== 5. pytest 실행 명령 ===")
# 실무 자주 쓰는 옵션 모음
print("""
pytest                          # 전체 실행
pytest tests/test_products.py   # 특정 파일
pytest -k 'test_create'         # 이름 매칭
pytest -x                       # 첫 실패에서 중단
pytest -v                       # 상세 출력
pytest --cov=app                # 커버리지
pytest --cov=app --cov-report=html  # HTML 리포트
""")

print("=== 핵심 정리 ===")
print("test_client(): HTTP 요청 시뮬레이션")
print("fixture: app, client, db, user 등 재사용")
print("scope: session(1회), function(매 테스트)")
print("parametrize: 경계값/다양한 입력 테스트")
print("Mock/patch: 외부 서비스 격리")
print("Given-When-Then: 테스트 구조 패턴")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. Flask 테스트 기본 ===
  GET /api/items -> 200, count=0
  POST /api/items -> 201, item={'id': 1, 'name': 'Python 책', 'price': 30000}
  POST (invalid) -> 400, error=name is required
  GET /api/items -> count=1

모든 테스트 통과!

=== 2. pytest fixture 패턴 ===

# conftest.py
import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope='session')
def app():
    '''테스트용 앱 생성'''
    app = create_app('testing')
    yield app

@pytest.fixture(scope='session')
def _database(app):
    '''테스트 DB 초기화'''
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def db(_database):
    '''각 테스트 후 롤백'''
    _database.session.begin_nested()
    yield _database
    _database.session.rollback()

@pytest.fixture
def client(app):
    '''테스트 클라이언트'''
    return app.test_client()

@pytest.fixture
def auth_client(client, user):
    '''인증된 테스트 클라이언트'''
    response = client.post('/auth/login', json={
        'username': user.username,
        'password': 'testpass'
    })
    token = response.json['access_token']
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client

@pytest.fixture
def user(db):
    '''테스트 사용자'''
    from app.models import User
    user = User(username='testuser', email='test@ex.com')
    user.set_password('testpass')
    db.session.add(user)
    db.session.commit()
    return user

=== 3. API 테스트 패턴 ===

# test_products.py
import pytest

class TestProductAPI:
    def test_list_products(self, auth_client, db):
        # Given: 상품 3개 존재
        for i in range(3):
            Product.create(name=f'Product {i}', price=1000 * (i+1))

        # When: 목록 요청
        response = auth_client.get('/api/products')

        # Then: 200 + 3개 반환
        assert response.status_code == 200
        assert len(response.json['items']) == 3

    def test_create_product(self, auth_client):
        response = auth_client.post('/api/products', json={
            'name': 'New Product',
            'price': 15000,
            'stock': 100
        })

        assert response.status_code == 201
        assert response.json['name'] == 'New Product'
        assert Product.query.count() == 1

    def test_create_product_validation_error(self, auth_client):
        response = auth_client.post('/api/products', json={
            'name': '',  # 빈 이름
            'price': -100  # 음수 가격
        })

        assert response.status_code == 400
        assert 'name' in response.json['errors']

    def test_unauthorized_access(self, client):
        response = client.get('/api/products')  # 토큰 없이
        assert response.status_code == 401

    @pytest.mark.parametrize('price,expected', [
        (1000, 200),
        (0, 400),
        (-1, 400),
    ])
    def test_price_validation(self, auth_client, price, expected):
        response = auth_client.post('/api/products', json={
            'name': 'Test', 'price': price
        })
        assert response.status_code == expected

=== 4. Mock 활용 ===
  결제 결과: {'success': True}
  mock 호출: call(50000, 'tok_test')

=== 5. pytest 실행 명령 ===

pytest                          # 전체 실행
pytest tests/test_products.py   # 특정 파일
pytest -k 'test_create'         # 이름 매칭
pytest -x                       # 첫 실패에서 중단
pytest -v                       # 상세 출력
pytest --cov=app                # 커버리지
pytest --cov=app --cov-report=html  # HTML 리포트

=== 핵심 정리 ===
test_client(): HTTP 요청 시뮬레이션
fixture: app, client, db, user 등 재사용
scope: session(1회), function(매 테스트)
parametrize: 경계값/다양한 입력 테스트
Mock/patch: 외부 서비스 격리
Given-When-Then: 테스트 구조 패턴
````

**풀이 요점**

- 흉내 클라이언트의 핵심은 `_request` 한 곳이다 — 헬퍼 넷은 메서드 이름만 붙여 넘긴다.
- 400 검사는 `not json` 이 빈 딕셔너리도 잡는다는 점을 이용한다.
- 기본 테스트 맨 앞의 `items_db.clear()` 가 없으면 `count == 0` 단언이 실행 순서에 묶인다.
- fixture 문자열에서는 scope(session · function)와 `yield` 앞뒤의 준비 · 정리, 그리고 fixture 끼리의 의존 사슬을 정확히 적는다.
- 패치 대상을 인스턴스가 아니라 클래스(`ExternalPaymentAPI`)로 잡아야 `process_payment` 안에서 새로 만든 인스턴스도 Mock 을 쓴다.
- Mock 은 결과(`success`)와 호출 인자(`assert_called_once_with`)를 둘 다 검증한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
