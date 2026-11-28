# python/python-web-deep/06 — Django 테스팅: TestCase와 pytest — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 주문은 `completed`, 호출 기록은 `call(50000, 'tok_test')`

**출력**

```text
  결과: {'order_id': 1, 'status': 'completed'}
  charge 호출: call(50000, 'tok_test')
```

**왜 그런가**

`charge` 의 `return_value` 가 `'success': True` 인 사전이라 `place_order` 가 완료 사전을 돌려준다.
`call_args` 는 마지막 호출의 인자를 `call(...)` 꼴로 담는다 — `place_order` 가 받은 `50000` 과 `'tok_test'` 를 그대로 넘겼다.
근거: 2-summary 「동작 방식 (5)」.

### 2. 주문은 `failed`, `order_id` 는 `None`

**출력**

```text
  결과: {'order_id': None, 'status': 'failed'}
```

**왜 그런가**

`return_value` 의 `'success'` 가 `False` 라 `if` 를 지나치고 실패 사전을 돌려준다.
사전에 함께 든 `'error': 'declined'` 는 `place_order` 가 읽지 않으므로 결과에 나타나지 않는다.
근거: 2-summary 「동작 방식 (5)」.

### 3. `admin@example.com` — `LazyAttribute` 가 덮어쓴 이름을 읽는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`admin.email` 은 `'admin@example.com'` 이다.

**왜 그런가**

`username` 을 넘겼으므로 `Sequence` 값(`user_<n>`)은 쓰이지 않는다.
`LazyAttribute` 는 같은 객체에서 정해진 `o.username`, 곧 `'admin'` 을 읽어 이메일을 만든다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」.

### 4. 재고는 다시 50 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`self.product.stock` 은 `50` 이고, `test_product_creation` 의 검사는 그대로 통과한다.

**왜 그런가**

`test_out_of_stock` 의 `save()` 는 그 테스트의 트랜잭션 안에서 일어났고 테스트가 끝날 때 ROLLBACK 되었다.
다음 테스트는 새 트랜잭션에서 `setUp` 이 다시 `stock=50` 짜리 상품을 만든 채로 시작한다.
근거: 2-summary 「동작 방식 (1)」 그림.

### 5. 테스트마다 트랜잭션을 열고 끝에 ROLLBACK 하기 때문이다

`TestCase` 는 각 테스트 메서드를 트랜잭션으로 감싸고, 끝나면 ROLLBACK 한다.
`setUp` 이 만든 행도, 본문이 바꾼 값도 그 트랜잭션 안의 변경이라 함께 취소된다.
그래서 지우는 코드를 `tearDown` 에 쓸 필요가 보통 없다 — 단 DB 밖에 남긴 흔적은 rollback 이 되돌리지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 5」.

### 6. 가짜 결제 서비스를 끼울 자리가 없어진다

`OrderService` 가 안에서 `PaymentService()` 를 만들면 테스트는 그 진짜 객체를 바꿀 방법이 없다.
그러면 `place_order` 가 진짜 `charge` 를 불러 `NotImplementedError`(실제라면 바깥 API 호출)를 만난다.
생성자로 받으면 테스트가 `OrderService(mock_payment)` 처럼 Mock 을 넘겨 반환값을 정하고 호출을 검사할 수 있다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 7. 이름 오타는 막지만 인자 개수는 `spec` 만으로 막지 못한다

`PaymentService` 에 없는 이름 `chrage` 를 부르면 `AttributeError` 가 난다.
`spec` 은 속성 이름만 따지므로 `charge` 를 인자 개수가 틀리게 불러도 막지 않는다 — 원본 주석의 「시그니처 변경 감지」는 의심스러운 주장이다 (확인 필요).
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 8. 네 번 돌고, 성공 기대값이 `201` 과 어긋난다

표가 4행이므로 같은 함수가 `price` · `expected_status` 를 바꿔 4번 돈다.
`-1` 과 `0` 은 무효 쪽, `1000` 과 `999999` 는 유효 쪽 경계를 찍는다.
그런데 같은 엔드포인트에 같은 POST 를 하는 `test_product_create` 는 성공에 `201` 을 기대하므로, 유효 가격 행의 `200` 과 둘 중 하나는 실패한다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

### 9. `auth_client` 가 `client` 와 `user` 를, `user` 가 Factory 를 부른다

pytest 는 테스트의 인자 이름 `auth_client` · `products` 를 보고 같은 이름의 fixture 를 찾는다.
`auth_client` 는 다시 `client`(pytest-django 가 주는 것)와 `user` 를 요구하므로 그 둘이 먼저 준비된다.
`user` 는 `UserFactory()` 로 비밀번호 `testpass` 인 사용자를 만들고, `auth_client` 가 그 이름과 비밀번호로 `client.login` 한 뒤 클라이언트를 돌려준다.
`products` 는 따로 `ProductFactory.create_batch(5)` 로 상품 5개를 만든다.
근거: 2-summary 「동작 방식 (4)」 그림 · 「동작 방식 (3)」.

### 10. `Client` 는 우리 앱으로 가는 HTTP 를, Mock 은 바깥 서비스를 대신한다

`Client` 는 **우리 Django 앱**에 보내는 HTTP 요청을 흉내 낸다 — 앱의 라우팅 · 뷰 · DB 는 진짜로 돌고, 네트워크만 건너뛴다.
`MagicMock` 은 **바깥 서비스 객체 자체**를 가짜로 바꿔 끼운다 — 진짜 `charge` 는 아예 불리지 않고 정해 둔 `return_value` 가 돌아온다.
곧 `Client` 는 「검사 대상을 진짜로 돌리는 통로」이고, Mock 은 「검사 대상이 아닌 의존을 잘라 내는 칸막이」다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (5)」.

## 실습 정답

### 실습 1. Django 테스트 패턴 모음과 Mock 결제 테스트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `TestCase` 예시 출력 | `=== 1. Django TestCase 패턴 ===` 뒤 `print("""...class ProductTestCase(TestCase)...""")` |
| 2. `Client` API 테스트 예시 출력 | `=== 2. API 테스트 (Client) ===` 뒤 `class ProductAPITest(TestCase)` 문자열 |
| 3. `factory_boy` 예시 출력 | `=== 3. factory_boy 패턴 ===` 뒤 `UserFactory` · `ProductFactory` · `OrderFactory` · `# 사용` 문자열 |
| 4. pytest-django 예시 출력 | `=== 4. pytest-django 패턴 ===` 뒤 `user` · `auth_client` · `products` fixture 와 `test_product_price_validation` 문자열 |
| 5. 바깥 API 자리 | `PaymentService.charge` 의 `raise NotImplementedError("실제 API 호출")` |
| 6. 생성자 주입 · 결과 분기 | `OrderService.__init__` 의 `self.payment = payment`, `place_order` 의 `if result['success']:` |
| 7. 성공 테스트 | `test_place_order_success` — `MagicMock(spec=PaymentService)` · `return_value` · `assert_called_once_with(50000, 'tok_test')` · `call_args` 출력 |
| 8. 실패 테스트 | `test_place_order_failure` — `{'success': False, 'error': 'declined'}` · `assert result['status'] == 'failed'` |
| 9. 두 테스트 호출 | `print("Mock 테스트 실행:")` 뒤 `test_place_order_success()` · `test_place_order_failure()` |
| 10. 정리 출력 | `=== 핵심 정리 ===` 아래 다섯 줄과 `실행: pytest --reuse-db -x -v` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/django-testing.py`

```python
# [웹 프레임워크 심화] Django 테스팅: TestCase와 pytest
# 설명: Django TestCase, Client, factory_boy, pytest-django 활용
# 팁: Django TestCase는 각 테스트를 트랜잭션으로 감싸 자동 rollback한다. factory_boy로 테스트 데이터를 선언적으로 생성하고, pytest-django의 fixture로 재사용한다. 외부 서비스는 반드시 Mock으로 격리하며, parametrize로 경계값을 테스트한다.

"""Django 테스팅: TestCase, Client, factory_boy, pytest"""
# json: 요청/응답 본문 직렬화
import json
# 타입 힌트
from typing import Any, Dict
# Mock: 외부 의존성 격리
from unittest.mock import patch, MagicMock

# === 테스팅 프레임워크 시뮬레이션 ===

# === 1. Django TestCase 패턴 ===
print("=== 1. Django TestCase 패턴 ===")
# TestCase는 각 테스트 메서드 시작 시 트랜잭션을 열고 끝나면 ROLLBACK
# → 테스트 간 DB 격리(트랜잭션 격리 수준 레벨에서 보장)
print("""
from django.test import TestCase, Client
from django.urls import reverse
from .models import Product, User

class ProductTestCase(TestCase):
    '''모델 테스트'''

    def setUp(self):
        '''각 테스트 전 실행'''
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.product = Product.objects.create(
            name='테스트 상품', price=10000, stock=50
        )

    def tearDown(self):
        '''각 테스트 후 실행 (자동 rollback되므로 보통 불필요)'''
        pass

    def test_product_creation(self):
        self.assertEqual(self.product.name, '테스트 상품')
        self.assertEqual(self.product.price, 10000)
        self.assertTrue(self.product.is_available)

    def test_product_str(self):
        self.assertEqual(str(self.product), '테스트 상품 (10,000원)')

    def test_product_discount(self):
        discounted = self.product.apply_discount(0.1)
        self.assertEqual(discounted, 9000)

    def test_out_of_stock(self):
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_available)
""")

# === 2. Django Client (API 테스트) ===
print("=== 2. API 테스트 (Client) ===")
# Client: HTTP 요청을 in-process로 시뮬레이션 (실제 네트워크 X)
print("""
class ProductAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123'
        )
        self.client.login(username='testuser', password='pass123')

    def test_product_list(self):
        Product.objects.create(name='A', price=1000)
        Product.objects.create(name='B', price=2000)

        response = self.client.get('/api/products/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_product_create(self):
        response = self.client.post(
            '/api/products/',
            data=json.dumps({'name': 'New', 'price': 5000}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().name, 'New')

    def test_product_create_invalid(self):
        response = self.client.post(
            '/api/products/',
            data=json.dumps({'name': ''}),  # 유효하지 않은 데이터
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 401)
""")

# === 3. factory_boy 패턴 ===
print("=== 3. factory_boy 패턴 ===")
# factory_boy: 선언적 테스트 데이터 빌더 (Sequence/LazyAttribute/SubFactory)
print("""
import factory
from factory.django import DjangoModelFactory
from .models import User, Product, Order

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass')

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    price = factory.Faker('random_int', min=1000, max=100000)
    stock = factory.Faker('random_int', min=0, max=100)
    category = factory.SubFactory('myapp.factories.CategoryFactory')

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(UserFactory)
    status = 'pending'

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        if extracted:
            for item in extracted:
                self.items.add(item)

# 사용
user = UserFactory()                    # 기본 사용자
admin = UserFactory(username='admin')   # 커스텀
products = ProductFactory.create_batch(10)  # 10개 생성
order = OrderFactory(items=[products[0], products[1]])  # 관계 포함
""")

# === 4. pytest-django 패턴 ===
print("=== 4. pytest-django 패턴 ===")
# pytest fixture: 함수 인자로 의존성 주입, scope로 재사용 범위 제어
# parametrize: 같은 테스트를 여러 입력으로 반복 (경계값 검증)
print("""
import pytest
from .factories import UserFactory, ProductFactory

# pytest fixture
@pytest.fixture
def user(db):
    return UserFactory()

@pytest.fixture
def auth_client(client, user):
    client.login(username=user.username, password='testpass')
    return client

@pytest.fixture
def products(db):
    return ProductFactory.create_batch(5)

# 테스트 함수
def test_product_list(auth_client, products):
    response = auth_client.get('/api/products/')
    assert response.status_code == 200
    assert len(response.json()['results']) == 5

def test_product_create(auth_client):
    response = auth_client.post(
        '/api/products/',
        data={'name': 'Test', 'price': 5000},
        content_type='application/json'
    )
    assert response.status_code == 201

@pytest.mark.parametrize('price,expected_status', [
    (1000, 200),
    (-1, 400),      # 음수 가격
    (0, 400),       # 0원
    (999999, 200),  # 큰 금액
])
def test_product_price_validation(auth_client, price, expected_status):
    response = auth_client.post(
        '/api/products/',
        data={'name': 'Test', 'price': price},
        content_type='application/json'
    )
    assert response.status_code == expected_status
""")

# === 5. Mock 활용 ===
print("=== 5. Mock 활용 ===")

# 외부 서비스: 실제 API 호출 비용/불안정성 차단을 위해 Mock으로 대체
class PaymentService:
    def charge(self, amount: int, token: str) -> dict:
        """실제로는 외부 API 호출"""
        raise NotImplementedError("실제 API 호출")

# 의존성 주입 패턴: 테스트 가능성 향상
class OrderService:
    def __init__(self, payment: PaymentService):
        self.payment = payment

    def place_order(self, amount: int, token: str) -> dict:
        # 외부 결제 서비스 호출
        result = self.payment.charge(amount, token)
        if result['success']:
            return {'order_id': 1, 'status': 'completed'}
        return {'order_id': None, 'status': 'failed'}

# Mock으로 외부 서비스 테스트: 성공 케이스
def test_place_order_success():
    # spec=PaymentService: 인터페이스 일치 강제 (오타/시그니처 변경 감지)
    mock_payment = MagicMock(spec=PaymentService)
    # 반환값 지정
    mock_payment.charge.return_value = {'success': True, 'transaction_id': 'tx123'}

    service = OrderService(mock_payment)
    result = service.place_order(50000, 'tok_test')

    # assert: 결과 + 호출 검증
    assert result['status'] == 'completed'
    mock_payment.charge.assert_called_once_with(50000, 'tok_test')
    print(f"  결과: {result}")
    print(f"  charge 호출: {mock_payment.charge.call_args}")

# 실패 케이스: 결제 거절 시나리오
def test_place_order_failure():
    mock_payment = MagicMock(spec=PaymentService)
    mock_payment.charge.return_value = {'success': False, 'error': 'declined'}

    service = OrderService(mock_payment)
    result = service.place_order(50000, 'tok_bad')

    assert result['status'] == 'failed'
    print(f"  결과: {result}")

print("Mock 테스트 실행:")
test_place_order_success()
test_place_order_failure()

print("\n=== 핵심 정리 ===")
print("TestCase: Django 내장, DB 자동 rollback")
print("Client: HTTP 요청 시뮬레이션")
print("factory_boy: 테스트 데이터 팩토리")
print("pytest-django: fixture 기반, parametrize")
print("Mock: 외부 서비스/API 격리")
print("\n실행: pytest --reuse-db -x -v")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. Django TestCase 패턴 ===

from django.test import TestCase, Client
from django.urls import reverse
from .models import Product, User

class ProductTestCase(TestCase):
    '''모델 테스트'''

    def setUp(self):
        '''각 테스트 전 실행'''
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.product = Product.objects.create(
            name='테스트 상품', price=10000, stock=50
        )

    def tearDown(self):
        '''각 테스트 후 실행 (자동 rollback되므로 보통 불필요)'''
        pass

    def test_product_creation(self):
        self.assertEqual(self.product.name, '테스트 상품')
        self.assertEqual(self.product.price, 10000)
        self.assertTrue(self.product.is_available)

    def test_product_str(self):
        self.assertEqual(str(self.product), '테스트 상품 (10,000원)')

    def test_product_discount(self):
        discounted = self.product.apply_discount(0.1)
        self.assertEqual(discounted, 9000)

    def test_out_of_stock(self):
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_available)

=== 2. API 테스트 (Client) ===

class ProductAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='pass123'
        )
        self.client.login(username='testuser', password='pass123')

    def test_product_list(self):
        Product.objects.create(name='A', price=1000)
        Product.objects.create(name='B', price=2000)

        response = self.client.get('/api/products/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)

    def test_product_create(self):
        response = self.client.post(
            '/api/products/',
            data=json.dumps({'name': 'New', 'price': 5000}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().name, 'New')

    def test_product_create_invalid(self):
        response = self.client.post(
            '/api/products/',
            data=json.dumps({'name': ''}),  # 유효하지 않은 데이터
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_access(self):
        self.client.logout()
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 401)

=== 3. factory_boy 패턴 ===

import factory
from factory.django import DjangoModelFactory
from .models import User, Product, Order

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass')

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    price = factory.Faker('random_int', min=1000, max=100000)
    stock = factory.Faker('random_int', min=0, max=100)
    category = factory.SubFactory('myapp.factories.CategoryFactory')

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(UserFactory)
    status = 'pending'

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        if extracted:
            for item in extracted:
                self.items.add(item)

# 사용
user = UserFactory()                    # 기본 사용자
admin = UserFactory(username='admin')   # 커스텀
products = ProductFactory.create_batch(10)  # 10개 생성
order = OrderFactory(items=[products[0], products[1]])  # 관계 포함

=== 4. pytest-django 패턴 ===

import pytest
from .factories import UserFactory, ProductFactory

# pytest fixture
@pytest.fixture
def user(db):
    return UserFactory()

@pytest.fixture
def auth_client(client, user):
    client.login(username=user.username, password='testpass')
    return client

@pytest.fixture
def products(db):
    return ProductFactory.create_batch(5)

# 테스트 함수
def test_product_list(auth_client, products):
    response = auth_client.get('/api/products/')
    assert response.status_code == 200
    assert len(response.json()['results']) == 5

def test_product_create(auth_client):
    response = auth_client.post(
        '/api/products/',
        data={'name': 'Test', 'price': 5000},
        content_type='application/json'
    )
    assert response.status_code == 201

@pytest.mark.parametrize('price,expected_status', [
    (1000, 200),
    (-1, 400),      # 음수 가격
    (0, 400),       # 0원
    (999999, 200),  # 큰 금액
])
def test_product_price_validation(auth_client, price, expected_status):
    response = auth_client.post(
        '/api/products/',
        data={'name': 'Test', 'price': price},
        content_type='application/json'
    )
    assert response.status_code == expected_status

=== 5. Mock 활용 ===
Mock 테스트 실행:
  결과: {'order_id': 1, 'status': 'completed'}
  charge 호출: call(50000, 'tok_test')
  결과: {'order_id': None, 'status': 'failed'}

=== 핵심 정리 ===
TestCase: Django 내장, DB 자동 rollback
Client: HTTP 요청 시뮬레이션
factory_boy: 테스트 데이터 팩토리
pytest-django: fixture 기반, parametrize
Mock: 외부 서비스/API 격리

실행: pytest --reuse-db -x -v
````

**풀이 요점**

- 섹션 1~4 는 Django · `factory_boy` · pytest-django 코드를 **문자열로 출력만** 한다 — 실제로 도는 것은 섹션 5 의 Mock 테스트뿐이다.
- `OrderService` 가 결제 서비스를 생성자로 받기 때문에 테스트가 `MagicMock` 을 넘길 수 있다.
- `return_value` 하나만 바꿔 성공 · 실패 두 갈래를 모두 검사한다.
- `assert_called_once_with` 는 결과뿐 아니라 「바깥 서비스를 어떤 인자로 몇 번 불렀나」까지 확인한다.
- 테스트 함수를 직접 불렀으므로 `assert` 가 깨지면 `AssertionError` 로 스크립트가 멈춘다 — 세 줄이 모두 찍혔다면 두 테스트가 통과한 것이다.
- `patch` · `Any` · `Dict` 는 import 만 하고 쓰지 않는다 — 원본을 그대로 따른 것이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
