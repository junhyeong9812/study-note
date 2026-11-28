# python/python-web-deep/06 — Django 테스팅: TestCase와 pytest — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 결제가 성공하는 Mock 으로 주문하면 (예측)

```python
# 질문용 발췌
mock_payment = MagicMock(spec=PaymentService)
mock_payment.charge.return_value = {'success': True, 'transaction_id': 'tx123'}
service = OrderService(mock_payment)
result = service.place_order(50000, 'tok_test')
print(f"  결과: {result}")
print(f"  charge 호출: {mock_payment.charge.call_args}")
```

- 두 `print` 는 각각 무엇을 찍는가?

### 2. 결제가 거절되는 Mock 으로 주문하면 (예측)

```python
# 질문용 발췌
mock_payment.charge.return_value = {'success': False, 'error': 'declined'}
service = OrderService(mock_payment)
result = service.place_order(50000, 'tok_bad')
print(f"  결과: {result}")
```

- 이 `print` 는 무엇을 찍는가?

### 3. 사용자 이름만 바꿔 Factory 를 부르면 (예측)

```python
# 질문용 발췌
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')

admin = UserFactory(username='admin')
```

- `admin.email` 은 무엇인가?

### 4. `test_out_of_stock` 다음에 도는 테스트의 상품 (예측)
- `ProductTestCase` 에서 `test_out_of_stock` 이 `stock = 0` 으로 저장한 직후 `test_product_creation` 이 돈다면, 그 테스트가 보는 `self.product.stock` 은 얼마인가?

### 5. `TestCase` 에서 `tearDown` 이 보통 비어 있는 까닭 (왜)
- 테스트가 만든 사용자 · 상품을 지우는 코드가 없는데도 다음 테스트에 남지 않는 까닭은 무엇인가?

### 6. `OrderService` 가 결제 서비스를 생성자로 받는 까닭 (왜)
- `OrderService` 가 `__init__` 안에서 `PaymentService()` 를 직접 만들었다면 테스트에서 무엇이 어려워지는가?

### 7. `spec=PaymentService` 가 막아 주는 범위 (경계)
- `mock_payment.chrage(...)` 처럼 이름을 잘못 쓰면 어떻게 되는가?
- `charge` 를 인자 개수가 틀리게 부르는 것도 `spec` 만으로 막히는가?

### 8. 가격 경계값 parametrize 표 (경계)
- 4행짜리 parametrize 표를 붙인 `test_product_price_validation` 은 몇 번의 테스트로 도는가?
- 유효한 가격 행의 기대값 `200` 은 같은 원본의 다른 생성 테스트와 비교해 어디서 어긋나는가?

### 9. fixture 가 fixture 를 요구하는 사슬 (연결)
- `test_product_list(auth_client, products)` 가 로그인된 클라이언트를 받기까지 pytest 는 어떤 fixture 들을 어떤 관계로 준비하는가?

### 10. `Client` 와 `MagicMock` 이 대신하는 것 (연결)
- `Client` 가 흉내 내는 것과 `MagicMock` 이 바꿔 끼우는 것은 각각 무엇이며, 둘이 바깥 세계를 차단하는 방식은 어떻게 다른가?

## 실습

### 실습 1. Django 테스트 패턴 모음과 Mock 결제 테스트 만들기

**만들 것** — Django 테스트 패턴 네 가지(`TestCase` · `Client` · `factory_boy` · pytest-django)를 코드 예시 문자열로 출력하고, 이어서 바깥 결제 서비스를 `MagicMock` 으로 바꿔 끼운 주문 테스트 두 개를 실제로 돌리는 스크립트를 만든다.

**준비물** — 파이썬 표준 라이브러리(`json` · `typing` · `unittest.mock`)만 있으면 된다. Django · `factory_boy` · pytest-django 코드는 실행하지 않고 문자열로 출력하는 흉내다.

**요구 조건**

1단계 — 패턴 예시 출력
1. `=== 1. Django TestCase 패턴 ===` 머리줄 뒤에, `TestCase` 를 상속한 `ProductTestCase` 예시를 여러 줄 문자열로 출력한다 — `setUp` 이 사용자와 상품(`테스트 상품`, 가격 10000, 재고 50)을 만들고, `tearDown` 은 `pass`, 테스트는 생성 값 확인 · `__str__` · 10% 할인 · 재고 0 일 때 판매 불가를 검사한다.
2. `=== 2. API 테스트 (Client) ===` 머리줄 뒤에 `ProductAPITest` 예시를 출력한다 — `setUp` 에서 `Client` 로 로그인하고, 목록 조회 `200`(결과 2개), JSON 생성 `201`(DB 에 1개 · 이름 `New`), 빈 이름 생성 `400`, 로그아웃 뒤 조회 `401` 을 검사한다.
3. `=== 3. factory_boy 패턴 ===` 머리줄 뒤에 `UserFactory`(`Sequence` 이름 · `LazyAttribute` 이메일 · `set_password` 비밀번호) · `ProductFactory`(`Faker` 값 · `SubFactory` 카테고리) · `OrderFactory`(`SubFactory` 주문자 · `post_generation` 상품 목록)와 사용 예 네 줄을 출력한다.
4. `=== 4. pytest-django 패턴 ===` 머리줄 뒤에 fixture 셋(`user` · `auth_client` · `products`)과 테스트 함수 셋(목록 5개 확인 · 생성 `201` · 가격 4행 parametrize)을 출력한다.

2단계 — Mock 테스트
5. `PaymentService.charge(amount, token)` 는 바깥 API 자리를 흉내 내 `NotImplementedError` 를 던진다.
6. `OrderService` 는 결제 서비스를 생성자로 받고, `place_order` 는 `charge` 결과의 `'success'` 가 참이면 `{'order_id': 1, 'status': 'completed'}`, 아니면 `{'order_id': None, 'status': 'failed'}` 를 돌려준다.
7. `test_place_order_success` 는 `spec` 을 준 `MagicMock` 의 `charge` 가 성공 사전을 돌려주게 하고, 상태가 `completed` 인지와 `charge` 가 `(50000, 'tok_test')` 로 정확히 한 번 불렸는지 검사한 뒤 결과와 `call_args` 를 출력한다.
8. `test_place_order_failure` 는 `charge` 가 거절 사전을 돌려주게 하고 상태가 `failed` 인지 검사한 뒤 결과를 출력한다.
9. `=== 5. Mock 활용 ===` 머리줄과 `Mock 테스트 실행:` 줄 뒤에 두 테스트 함수를 차례로 부른다.

3단계 — 정리
10. `=== 핵심 정리 ===` 아래에 다섯 도구(TestCase · Client · factory_boy · pytest-django · Mock)의 한 줄 요약과 실행 명령 `pytest --reuse-db -x -v` 를 출력한다.

**시작 코드**

```python
"""Django 테스팅: TestCase, Client, factory_boy, pytest"""
import json
from typing import Any, Dict
from unittest.mock import patch, MagicMock

print("=== 1. Django TestCase 패턴 ===")
print("""
# TODO: ProductTestCase 예시 (setUp · tearDown · 테스트 4개)
""")

print("=== 2. API 테스트 (Client) ===")
print("""
# TODO: ProductAPITest 예시 (로그인 · 200 · 201 · 400 · 401)
""")

print("=== 3. factory_boy 패턴 ===")
print("""
# TODO: UserFactory · ProductFactory · OrderFactory · 사용 예
""")

print("=== 4. pytest-django 패턴 ===")
print("""
# TODO: fixture 셋 · 테스트 함수 셋 (parametrize 포함)
""")

print("=== 5. Mock 활용 ===")

class PaymentService:
    def charge(self, amount: int, token: str) -> dict:
        """실제로는 외부 API 호출"""
        # TODO: 바깥 API 자리 — 예외를 던진다

class OrderService:
    def __init__(self, payment: PaymentService):
        # TODO: 결제 서비스를 받아 둔다
        pass

    def place_order(self, amount: int, token: str) -> dict:
        # TODO: charge 결과에 따라 completed / failed 사전을 돌려준다
        pass

def test_place_order_success():
    # TODO: spec 을 준 MagicMock · return_value · assert 두 개
    print(f"  결과: {result}")
    print(f"  charge 호출: {mock_payment.charge.call_args}")

def test_place_order_failure():
    # TODO: 거절 사전 · assert
    print(f"  결과: {result}")

print("Mock 테스트 실행:")
# TODO: 두 테스트 호출

print("\n=== 핵심 정리 ===")
print("TestCase: Django 내장, DB 자동 rollback")
print("Client: HTTP 요청 시뮬레이션")
print("factory_boy: 테스트 데이터 팩토리")
print("pytest-django: fixture 기반, parametrize")
print("Mock: 외부 서비스/API 격리")
print("\n실행: pytest --reuse-db -x -v")
```

**확인 방법** — `python django-testing.py` 로 돌려, 섹션 1~4 의 예시 코드가 찍히고 `=== 5. Mock 활용 ===` 아래에 성공 결과 · `charge` 호출 · 실패 결과 세 줄이 `AssertionError` 없이 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
