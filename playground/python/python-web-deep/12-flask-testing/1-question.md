# python/python-web-deep/12 — Flask 테스팅: pytest와 fixture — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 빈 JSON 으로 POST 한 뒤 목록을 다시 보면 (예측)

```python
# 질문용 발췌 — items_db 에는 'Python 책' 아이템 하나가 이미 들어 있다
response = client.post('/api/items', json={})
print(f"  POST (invalid) -> {response['status_code']}, error={response['json']['error']}")

response = client.get('/api/items')
print(f"  GET /api/items -> count={response['json']['count']}")
```

- 두 `print` 는 각각 무엇을 찍나?

### 2. 빈 저장소에 첫 아이템을 만들면 (예측)

```python
# 질문용 발췌 — 바로 앞에서 items_db.clear() 를 했다
response = client.post('/api/items', json={'name': 'Python 책', 'price': 30000})
print(f"  POST /api/items -> {response['status_code']}, item={response['json']}")
```

- 이 `print` 는 무엇을 찍나?

### 3. 결제 API 를 패치하고 결제 로직을 부르면 (예측)

```python
# 질문용 발췌
with patch.object(ExternalPaymentAPI, 'charge') as mock_charge:
    mock_charge.return_value = {'ok': True, 'transaction_id': 'tx_123'}
    result = process_payment(50000, 'tok_test')
    print(f"  결제 결과: {result}")
    print(f"  mock 호출: {mock_charge.call_args}")
```

- 두 `print` 는 각각 무엇을 찍나?

### 4. 흉내 클라이언트로 표에 없는 요청을 보내면 (예측)

- 원본의 `routes` 그대로 `client.delete('/api/items')` 를 부르면 무엇이 돌아오나?
- `client.get('/api/items/2')` 는 무엇이 돌아오나?

### 5. `app` 은 session, `db` 는 function 인 까닭 (왜)

- 앱과 테이블은 한 번만 만들면서 데이터 변경은 테스트마다 되돌리도록 나눈 이유는 무엇인가?

### 6. 결제 API 를 진짜로 부르지 않고 패치하는 까닭 (왜)

- 외부 결제 API 를 Mock 으로 바꿔서 테스트하는 이유는 무엇인가?

### 7. `items_db.clear()` 를 빼고 기본 테스트를 두 번 돌리면 (경계)

- 두 번째 실행에서 어느 단언이 먼저 깨지고, 새 아이템의 `id` 는 어떻게 되나?

### 8. 이름 키는 있는데 값이 빈 문자열이면 (경계)

- 흉내 `create_item` 에 `{'name': ''}` 를 보내면 검사를 통과하나, 그리고 실제 API 테스트의 기대와는 어떻게 다른가?

### 9. 정상 가격 POST 의 기대 코드 (경계)

- `test_price_validation` 의 `(1000, 200)` 묶음은 `test_create_product` 와 나란히 놓으면 어디서 깨질 수 있나?

### 10. 테스트가 `auth_client` 를 요청할 때 만들어지는 차례 (연결)

- `auth_client` 하나를 요청하면 어떤 fixture 들이 어떤 차례로 준비되고, 이것이 Given-When-Then 의 어느 칸을 대신하나?

## 실습

### 실습 1. 흉내 test_client 로 API 를 테스트하고 Mock 으로 결제를 격리하기

**만들 것** — Flask 없이 표준 라이브러리만으로 test_client 를 흉내 낸 클래스와 아이템 API 를 만들고, `assert` 로 테스트한다.
이어서 pytest fixture · API 테스트 패턴을 문자열로 보여 주고, `patch.object` 로 외부 결제 API 를 가짜로 바꿔 검증한다.

**준비물** — Flask · pytest 는 필요 없다 — `TestClient` 는 Flask 의 `test_client()` 를 흉내 낸 것이고, `conftest.py` · `test_products.py` 는 실행하지 않고 문자열로 출력만 한다. `unittest.mock` 은 표준 라이브러리다.

**요구 조건**

1단계 — 흉내 클라이언트
1. `TestClient(routes)` 는 `(메서드, 경로)` → 핸들러 딕셔너리를 `self.routes` 에 담고, 빈 `self.cookies` 딕셔너리를 만든다.
2. `get(path, headers)` · `delete(path, headers)` 와 `post(path, json, headers)` · `put(path, json, headers)` 는 모두 `_request` 에 메서드 이름 문자열을 붙여 넘긴다.
3. `_request` 는 `(method, path)` 로 핸들러를 찾고, 없으면 `{'status_code': 404, 'json': {'error': 'Not Found'}}` 를, 있으면 `handler(json=json, headers=headers or {})` 의 결과를 돌려준다.

2단계 — 핸들러와 라우트
4. 전역 리스트 `items_db` 를 둔다.
5. `list_items` 는 200 과 `{'items': items_db, 'count': 개수}` 를 돌려준다.
6. `create_item` 은 JSON 이 비었거나 `'name'` 키가 없으면 400 과 `{'error': 'name is required'}` 를, 아니면 `id` 를 「현재 개수 + 1」로 붙인 아이템을 저장하고 201 과 그 아이템을 돌려준다.
7. `get_item` 은 200 과 첫 아이템(없으면 `{}`)을 돌려준다.
8. `routes` 에 `GET /api/items` · `POST /api/items` · `GET /api/items/1` 세 라우트를 등록한다.

3단계 — 기본 테스트
9. 클라이언트를 만들고 `items_db` 를 비운 뒤, GET 이 200 · count 0 인지 단언한다.
10. `{'name': 'Python 책', 'price': 30000}` POST 가 201 이고 이름이 맞는지 단언한다.
11. `{}` POST 가 400 인지 단언한다.
12. 다시 GET 해 count 가 1 인지 단언하고, 모두 통과하면 「모든 테스트 통과!」를 찍는다.

4단계 — 패턴 문자열 출력
13. `conftest.py` 문자열에 fixture 여섯 개를 적어 출력한다: `app`(session, `create_app('testing')` 을 yield) · `_database`(session, `app_context` 안에서 `create_all` → yield → `drop_all`) · `db`(function, `begin_nested` → yield → `rollback`) · `client`(`app.test_client()`) · `auth_client`(`client` · `user` 를 받아 `/auth/login` 으로 토큰을 받고 `environ_base['HTTP_AUTHORIZATION']` 에 `Bearer` 토큰을 넣음) · `user`(`db` 를 받아 `User` 를 만들고 비밀번호를 정해 add · commit).
14. `test_products.py` 문자열에 `TestProductAPI` 클래스를 적어 출력한다: Given-When-Then 주석이 달린 목록 테스트(상품 3개 → 200 · 3개) · 생성 테스트(201 · 이름 · 개수 1) · 유효성 오류 테스트(400 · `errors` 에 `name`) · 토큰 없는 접근(401) · 가격 parametrize(`1000→200` · `0→400` · `-1→400`).

5단계 — Mock
15. `ExternalPaymentAPI.charge(amount, token)` 는 `RuntimeError("실제 API 호출")` 을 던진다.
16. `process_payment(amount, token)` 는 새 `ExternalPaymentAPI` 로 `charge` 를 불러 `{'success': 결과의 'ok'(없으면 False)}` 를 돌려준다.
17. `with patch.object(...)` 안에서 `return_value` 를 `{'ok': True, 'transaction_id': 'tx_123'}` 로 정하고, `process_payment(50000, 'tok_test')` 의 성공과 `assert_called_once_with(50000, 'tok_test')` 를 단언한 뒤 결과와 `call_args` 를 찍는다.

6단계 — 마무리
18. pytest 실행 명령 모음과 핵심 정리를 찍는다(시작 코드에 채워 둔 문자열을 그대로 쓴다).

**시작 코드**

```python
"""Flask 테스팅: pytest, test_client, fixture"""
import json
from typing import Any, Dict
from unittest.mock import patch, MagicMock

# === Flask 테스트 시뮬레이션 ===

class TestClient:
    """Flask test_client 시뮬레이션"""
    def __init__(self, routes: dict):
        # TODO: routes 를 보관하고 빈 cookies 딕셔너리를 만든다
        pass

    def get(self, path: str, headers: dict = None) -> dict:
        # TODO: _request 로 넘긴다
        pass

    def post(self, path: str, json: dict = None, headers: dict = None) -> dict:
        # TODO
        pass

    def put(self, path: str, json: dict = None, headers: dict = None) -> dict:
        # TODO
        pass

    def delete(self, path: str, headers: dict = None) -> dict:
        # TODO
        pass

    def _request(self, method, path, json=None, headers=None):
        # TODO: (method, path) 로 핸들러 찾기 → 없으면 404 딕셔너리
        # TODO: 있으면 handler(json=..., headers=...) 결과 (headers 가 None 이면 {})
        pass

items_db = []

def list_items(json=None, headers=None):
    # TODO: 200 + items · count
    pass

def create_item(json=None, headers=None):
    # TODO: 검사 실패면 400, 아니면 id 붙여 저장하고 201
    pass

def get_item(json=None, headers=None):
    # TODO: 200 + 첫 아이템 (없으면 {})
    pass

routes = {
    # TODO: 세 라우트
}

# === 1. 기본 테스트 ===
print("=== 1. Flask 테스트 기본 ===")

# TODO: 클라이언트 생성 + items_db 비우기

# TODO: GET 하고 200 · count 0 단언
print(f"  GET /api/items -> {response['status_code']}, count={response['json']['count']}")

# TODO: 정상 POST 하고 201 · 이름 단언
print(f"  POST /api/items -> {response['status_code']}, item={response['json']}")

# TODO: 빈 JSON POST 하고 400 단언
print(f"  POST (invalid) -> {response['status_code']}, error={response['json']['error']}")

# TODO: 다시 GET 하고 count 1 단언
print(f"  GET /api/items -> count={response['json']['count']}")

print("\n모든 테스트 통과!")

# === 2. pytest fixture 패턴 ===
print("\n=== 2. pytest fixture 패턴 ===")
print("""
# conftest.py
# TODO: fixture 여섯 개 (요구 조건 13)
""")

# === 3. API 테스트 패턴 ===
print("=== 3. API 테스트 패턴 ===")
print("""
# test_products.py
# TODO: TestProductAPI (요구 조건 14)
""")

# === 4. Mock 활용 ===
print("=== 4. Mock 활용 ===")

class ExternalPaymentAPI:
    def charge(self, amount, token):
        # TODO: 진짜 호출을 상징하는 예외
        pass

def process_payment(amount, token):
    # TODO
    pass

# TODO: patch.object 로 charge 를 바꾸고 return_value 지정 → 호출 → 단언
#     print(f"  결제 결과: {result}")
#     print(f"  mock 호출: {mock_charge.call_args}")

print("\n=== 5. pytest 실행 명령 ===")
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

**확인 방법** — `python flask-testing.py` 로 돌려 `AssertionError` 없이 「모든 테스트 통과!」와 「결제 결과: {'success': True}」가 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
