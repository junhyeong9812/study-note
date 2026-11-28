# python/python-web-deep/06 — Django 테스팅: TestCase와 pytest — 정리 (힌트)

> 출처 — study-site 항목 `python/django-testing`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/django-testing.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Django 테스트는 「매번 새로 깔아 주는 시험장」이다.**
시험(테스트) 하나가 시작될 때마다 감독관이 책상을 똑같이 차려 놓는다.
시험이 끝나면 수험생이 무엇을 낙서했든 책상을 통째로 처음 상태로 되돌린다.
문제지는 인쇄소(factory)가 찍어 내고, 시험장 바깥에 전화를 걸어야 하는 문제는 가짜 전화기(Mock)로 받는다.
Django `TestCase` · `factory_boy` · pytest fixture · `Mock` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 시험 하나 | 테스트 메서드 · 테스트 함수 하나 |
| 책상 차리기 | `setUp` · pytest fixture |
| 책상 되돌리기 | 트랜잭션 rollback |
| 문제지 인쇄소 | `factory_boy` 의 Factory 클래스 |
| 같은 문제를 숫자만 바꿔 여러 번 | `@pytest.mark.parametrize` |
| 가짜 전화기 | `MagicMock` |
| 시험장 안 모의 창구 | Django `Client` |

```text
 [setUp / fixture]  →  [테스트 본문]  →  [ROLLBACK]
   데이터 준비          요청·검증          DB 원상복구
        ↑                                      │
        └────────── 다음 테스트 ←───────────────┘
```

## 이 주제가 답하려는 질문

1. 테스트끼리 DB 를 함께 쓰는데 어떻게 서로 영향을 주지 않나?
2. 실제 서버를 띄우지 않고 API(URL · 상태 코드 · 응답 JSON)를 어떻게 검사하나?
3. 테스트 데이터와 준비 코드를 어떻게 짧게, 다시 쓸 수 있게 만드나?
4. 결제 API 같은 바깥 서비스에 기대는 코드를 어떻게 바깥 없이 검사하나?

## 동작 방식

### (1) `TestCase` — 테스트마다 트랜잭션을 열고 되돌린다

**언제 쓰나** — 모델(`Product`)의 필드 · 메서드 · `__str__` 처럼 DB 에 저장되는 대상을 검사할 때 쓴다.

```text
class ProductTestCase(TestCase)
   │
   ├─ test_product_creation   : BEGIN → setUp() → 본문 → ROLLBACK
   ├─ test_product_str        : BEGIN → setUp() → 본문 → ROLLBACK
   ├─ test_product_discount   : BEGIN → setUp() → 본문 → ROLLBACK
   └─ test_out_of_stock       : BEGIN → setUp() → stock=0, save() → ROLLBACK
                                                          │
                                 다음 테스트는 stock=50 짜리 새 상품에서 시작
```

- 테스트 메서드 하나가 시작될 때 트랜잭션이 열린다.
- `setUp` 이 그 안에서 `User` 와 `Product(name='테스트 상품', price=10000, stock=50)` 를 만든다.
- 본문이 `assertEqual` · `assertTrue` · `assertFalse` 로 값을 확인한다.
- 본문이 끝나면 트랜잭션이 ROLLBACK 되어 그 테스트가 만든 행과 바꾼 값이 모두 사라진다.
- 그래서 `tearDown` 에서 지우는 코드를 쓸 필요가 보통 없다(원본의 `tearDown` 은 `pass` 다).

> **트랜잭션** — DB 작업 여러 개를 「모두 반영하거나 모두 취소하는」 한 덩어리로 묶은 것.\
> 예: 상품 생성과 재고 수정을 묶었다가 ROLLBACK 하면 둘 다 없던 일이 된다.

> **rollback** — 트랜잭션 안에서 한 변경을 취소해 시작 전 상태로 되돌리는 일.\
> 예: `test_out_of_stock` 이 `stock=0` 으로 저장해도 테스트가 끝나면 그 저장이 취소된다.

### (2) `Client` — 네트워크 없이 HTTP 요청을 흉내 낸다

**언제 쓰나** — URL 에 요청을 보내 상태 코드와 응답 본문을 검사하는 API 테스트에 쓴다.

```text
self.client.post('/api/products/', data=json.dumps({...}),
                 content_type='application/json')
        │  (같은 프로세스 안에서 — 실제 네트워크 X)
        ▼
  URL 라우팅 → 뷰 → (DB 저장)
        │
        ▼
  response.status_code == 201 ?   response.json()['results'] ?
```

- `Client()` 로 만든 객체가 `get` · `post` 로 요청을 만든다.
- 요청은 소켓을 거치지 않고 같은 프로세스 안에서 Django 에 바로 전달된다.
- 응답 객체의 `status_code` 와 `json()` 으로 결과를 확인한다.
- `client.login(...)` 으로 로그인한 상태를 만들고 `client.logout()` 으로 되돌린다.
- 원본이 기대하는 상태 코드는 목록 조회 `200`, 생성 `201`, 잘못된 입력(`name` 이 빈 문자열) `400`, 로그아웃 뒤 조회 `401` 이다.
- 생성 테스트는 응답만이 아니라 `Product.objects.count()` 와 `first().name` 으로 DB 에 실제로 들어갔는지도 본다.

> **상태 코드** — HTTP 응답이 성공 · 실패를 알리는 세 자리 숫자.\
> 예: `201` 은 「만들었다」, `400` 은 「요청이 잘못됐다」.

### (3) `factory_boy` — 테스트 데이터를 선언으로 찍어 낸다

**언제 쓰나** — 테스트마다 `objects.create(...)` 에 필드를 전부 적기 번거로울 때, 「기본값은 Factory 가, 바꿀 것만 테스트가」 정하게 한다.

```text
UserFactory(username='admin')
   │
   ├─ username : 넘긴 값 'admin' (없으면 Sequence → user_<n>)
   ├─ email    : LazyAttribute → 방금 정한 username 으로 '<username>@example.com'
   └─ password : 생성 뒤 set_password('testpass') 호출
   ▼
 DB 에 저장된 User 객체
```

- `factory.Sequence(lambda n: ...)` 는 만들 때마다 늘어나는 번호 `n` 으로 값을 만든다 — 사용자 이름이 겹치지 않는다.
- `factory.LazyAttribute(lambda o: ...)` 는 같은 객체의 다른 필드(`o.username`)를 읽어 값을 만든다.
- `factory.PostGenerationMethodCall('set_password', 'testpass')` 는 객체를 만든 뒤 그 메서드를 부른다 — 비밀번호가 해시로 저장된다.
- `factory.Faker('word')` · `factory.Faker('random_int', min=..., max=...)` 는 그럴듯한 무작위 값을 넣는다.
- `factory.SubFactory(...)` 는 외래 키 대상(카테고리 · 주문자)을 다른 Factory 로 함께 만든다.
- `@factory.post_generation` 함수는 생성 뒤에 실행되며, 호출 때 넘긴 값(`items=[...]`)을 `extracted` 로 받아 다대다 관계를 붙인다.
- `create_batch(10)` 은 한 번에 10개를 만든다.

> **Factory** — 모델 객체를 만드는 방법을 클래스로 선언해 둔 것.\
> 예: `ProductFactory()` 한 줄이 이름 · 가격 · 재고 · 카테고리를 모두 채운 상품을 만든다.

### (4) pytest-django — fixture 로 준비를 나누고 parametrize 로 반복한다

**언제 쓰나** — 클래스 없이 함수로 테스트를 쓰고, 준비 단계를 조각내 여러 테스트가 나눠 쓰게 할 때 쓴다.

```text
def test_product_list(auth_client, products):
                         │            │
          auth_client(client, user)   products(db)
                  │          │              │
          pytest 내장   user(db) → UserFactory()   ProductFactory.create_batch(5)
                  ▼
     client.login(username=user.username, password='testpass')
```

- 테스트 함수의 **인자 이름**이 곧 요청하는 fixture 이름이다.
- pytest 가 그 이름의 fixture 를 찾아 먼저 실행하고, 반환값을 인자로 넣어 준다.
- fixture 도 다른 fixture 를 인자로 요구할 수 있다 — `auth_client` 는 `client` 와 `user` 를 받는다.
- 그래서 `test_product_list` 는 로그인된 클라이언트와 상품 5개를 받은 채로 시작한다.
- `@pytest.mark.parametrize('price,expected_status', [...])` 는 표의 행마다 같은 테스트를 한 번씩 돌린다 — 표가 4행이면 4번이다.
- 원본 표는 `1000 → 200`, `-1 → 400`(음수), `0 → 400`(0원), `999999 → 200`(큰 금액)으로, 「유효 · 무효가 갈리는 경계」의 양쪽을 찍는다.

> **fixture** — 테스트가 인자 이름으로 요청하면 pytest 가 미리 만들어 넣어 주는 준비물.\
> 예: `def user(db): return UserFactory()` 를 정의하면 `user` 인자를 가진 테스트마다 사용자가 하나 생긴다.

> **parametrize** — 같은 테스트 본문을 여러 입력값 묶음으로 반복하게 하는 표시.\
> 예: 가격 `-1` · `0` · `1000` 을 한 함수로 각각 검사한다.

### (5) `MagicMock` — 바깥 서비스를 가짜로 바꿔 끼운다

**언제 쓰나** — 결제 API 처럼 진짜로 부르면 돈 · 시간이 들거나 결과가 들쭉날쭉한 바깥 서비스에 기대는 코드를 검사할 때 쓴다.

```text
OrderService(payment)          ← 생성자로 결제 서비스를 받는다 (의존성 주입)
     │
     │  테스트에서는 진짜 PaymentService 대신
     ▼
mock_payment = MagicMock(spec=PaymentService)
mock_payment.charge.return_value = {'success': True, ...}
     │
service.place_order(50000, 'tok_test')
     │   → self.payment.charge(50000, 'tok_test')   (가짜가 return_value 를 돌려줌)
     │   → result['success'] 가 참 → {'order_id': 1, 'status': 'completed'}
     ▼
assert result['status'] == 'completed'
mock_payment.charge.assert_called_once_with(50000, 'tok_test')
```

- 진짜 `PaymentService.charge` 는 `NotImplementedError` 를 던진다 — 바깥 API 를 부르는 자리를 흉내 낸 것이다.
- `OrderService` 가 결제 서비스를 안에서 만들지 않고 **생성자 인자로 받기** 때문에 테스트가 가짜를 끼울 수 있다.
- `return_value` 에 넣은 사전이 `charge(...)` 호출의 결과가 된다.
- 성공 사전(`'success': True`)이면 `completed`, 실패 사전(`'success': False`)이면 `{'order_id': None, 'status': 'failed'}` 가 나온다.
- `assert_called_once_with(...)` 는 「정확히 한 번, 이 인자로 불렸나」를 검사하고, 아니면 `AssertionError` 를 낸다.
- `call_args` 는 마지막 호출의 인자를 `call(...)` 꼴로 담는다.
- `spec=PaymentService` 를 주면 `PaymentService` 에 없는 이름(오타)을 부를 때 `AttributeError` 가 난다.

> **Mock** — 진짜 객체 자리에 끼워 넣어, 돌려줄 값을 정하고 어떻게 불렸는지 기록하는 가짜 객체.\
> 예: `mock.charge.return_value = {...}` 로 결제 결과를 정해 둔다.

> **의존성 주입** — 객체가 쓸 다른 객체를 스스로 만들지 않고 바깥에서 받아 쓰는 방식.\
> 예: `OrderService(mock_payment)`.

## 문법 — 형태와 규칙

```python
from unittest.mock import MagicMock

class Mailer:
    def send(self, to: str) -> bool:
        raise NotImplementedError

class Signup:
    def __init__(self, mailer: Mailer):
        self.mailer = mailer
    def register(self, email: str) -> str:
        return 'ok' if self.mailer.send(email) else 'retry'

m = MagicMock(spec=Mailer)
m.send.return_value = False
assert Signup(m).register('a@b.c') == 'retry'
m.send.assert_called_once_with('a@b.c')
```

- `TestCase` 를 상속한 클래스에서 `test_` 로 시작하는 메서드가 테스트다.
- `setUp` 은 각 테스트 **전**, `tearDown` 은 각 테스트 **후**에 실행된다(클래스당 한 번이 아니다).
- 검사는 `self.assertEqual(a, b)` · `self.assertTrue(x)` · `self.assertFalse(x)` 로 한다.
- `Client` 로 JSON 을 보낼 때는 `data=json.dumps({...})` 와 `content_type='application/json'` 을 함께 쓴다(원본의 `TestCase` 절).
- 원본의 pytest 절은 `data` 에 사전을 그대로 넘기고 `content_type='application/json'` 을 준다.
- Factory 는 `class Meta: model = 모델` 로 어떤 모델을 만들지 정한다.
- Factory 호출에 키워드 인자를 주면 그 필드만 덮어쓴다 — `UserFactory(username='admin')`.
- fixture 는 `@pytest.fixture` 로 표시한 함수이고, 테스트 함수의 인자 이름으로 요청한다.
- `@pytest.mark.parametrize('이름1,이름2', [(값, 값), ...])` 에서 쉼표로 나눈 이름이 테스트 함수의 인자가 된다.
- pytest 에서는 `self.assertEqual` 대신 그냥 `assert 식` 을 쓴다.
- 원본이 제시한 실행 명령은 `pytest --reuse-db -x -v` 다.

## 어디서 틀리나

### 1. 같은 「생성 성공」인데 기대 코드가 다르다

원본의 `test_product_create` 는 성공 생성에 `201` 을 기대한다.
그런데 `test_product_price_validation` 의 parametrize 표는 유효한 가격(`1000` · `999999`)의 생성 요청에 `200` 을 기대한다.
같은 엔드포인트 · 같은 POST 이므로 둘 중 하나는 실패한다(원본에 근거 없음 — 추론).
경계값 표를 만들 때는 「성공」 행의 기대값이 다른 테스트와 맞는지 확인한다.

### 2. 로그인 안 한 요청이 `401` 이라는 가정

원본의 `test_unauthenticated_access` 는 로그아웃 뒤 조회에 `401` 을 기대한다.
원본의 주장 → 로그아웃 뒤 응답이 `401` 이다.
왜 의심스러운가 → 어떤 상태 코드가 나올지는 프로젝트의 인증 설정이 정하며, 세션 인증에서는 `403` 이 나올 수 있다 (확인 필요).

### 3. `spec` 이 시그니처까지 잡아 준다는 주석

원본 주석은 `spec=PaymentService` 가 「오타/시그니처 변경 감지」를 한다고 적는다.
원본의 주장 → 시그니처 변경도 잡는다.
왜 의심스러운가 → `spec` 은 **속성 이름**이 있는지만 따지고, `charge` 를 인자 개수가 틀리게 불러도 막지 않는 것으로 알려져 있다 — 인자까지 따지려면 `create_autospec` 류를 쓴다 (확인 필요).
오타(`chrage`)는 `AttributeError` 로 잡힌다.

### 4. 바깥 서비스를 Mock 하지 않음

원본 팁: 외부 서비스는 **반드시** Mock 으로 격리한다.
이 예제의 진짜 `charge` 는 `NotImplementedError` 를 던지므로, Mock 없이 `OrderService(PaymentService())` 를 테스트하면 바로 터진다.
진짜 API 였다면 테스트가 돈을 쓰거나 네트워크 상태에 따라 붙었다 떨어졌다 한다.

### 5. 「자동 rollback」의 근거를 잘못 이해함

원본 주석은 테스트 간 격리가 「트랜잭션 격리 수준 레벨에서 보장」된다고 적는다.
원본의 주장 → 격리 수준이 테스트를 격리한다.
왜 의심스러운가 → 테스트 사이 격리는 「각 테스트를 트랜잭션으로 감싸고 끝에 ROLLBACK 한다」는 데서 온다 — 격리 수준은 동시에 도는 트랜잭션끼리의 문제다 (원본에 근거 없음 — 추론).
또 rollback 은 DB 만 되돌린다 — 파일 · 캐시처럼 DB 밖에 남긴 흔적은 남는다 (원본에 근거 없음 — 추론).

### 6. Faker 값은 매번 다르다

`ProductFactory` 의 `stock` 은 `0`~`100` 무작위다.
재고에 따라 `is_available` 이 바뀌는 모델이면, 같은 테스트가 어떤 날은 통과하고 어떤 날은 실패할 수 있다(원본에 근거 없음 — 추론).
결과에 영향을 주는 필드는 `ProductFactory(stock=10)` 처럼 테스트에서 직접 정한다.

### 7. 쓰지 않는 import

원본은 `patch` · `Any` · `Dict` 를 import 하지만 쓰지 않는다.
틀린 동작은 아니지만 읽는 사람이 「어디서 `patch` 를 쓰나」 찾게 만든다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `TestCase` 는 테스트마다 트랜잭션을 열고 ROLLBACK 한다 | Django 프레임워크(파이썬 언어가 아니다). 트랜잭션을 지원하는 DB 가 전제다 (확인 필요) |
| `Client` 요청은 실제 네트워크를 거치지 않는다 | Django 테스트 도구의 설계 |
| 로그아웃 뒤 응답이 `401` 이다 | 프로젝트의 인증 설정 (확인 필요) |
| fixture 를 인자 이름으로 주입한다 · parametrize 가 행마다 반복한다 | pytest(와 pytest-django) 라이브러리 |
| `Sequence` · `LazyAttribute` · `SubFactory` 의 동작 | `factory_boy` 라이브러리 |
| `spec` 이 없는 속성 접근을 막는다 · `call_args` 가 `call(50000, 'tok_test')` 꼴로 찍힌다 | 표준 라이브러리 `unittest.mock` 의 동작 · `repr` 형식 |
| 사전이 넣은 순서대로 찍힌다(`'order_id'` 다음 `'status'`) | 파이썬 언어 보장(3.7 이상 사전의 삽입 순서) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 모델 메서드 · `__str__` 검사 | `TestCase` + `setUp` | 테스트 끝에 손으로 지우는 `tearDown` |
| API 상태 코드 · 응답 JSON 검사 | `Client` (`login` · `get` · `post`) | 서버를 띄워 실제 HTTP 로 부르기 |
| 데이터가 여러 개 필요한 테스트 | `ProductFactory.create_batch(n)` | 필드를 전부 적은 `objects.create` 반복 |
| 여러 테스트가 같은 준비를 나눠 씀 | pytest fixture (`user` · `auth_client`) | 테스트마다 로그인 코드 복붙 |
| 입력값만 바꿔 경계 확인 | `@pytest.mark.parametrize` | 값마다 테스트 함수 따로 쓰기 |
| 결제 · 메일 같은 바깥 서비스 | `MagicMock(spec=...)` + 의존성 주입 | 진짜 서비스를 테스트에서 호출 |
| 결과를 좌우하는 필드 | 테스트에서 값을 직접 지정 | Faker 무작위 값에 맡기기 |

## 핵심 문장

1. **`TestCase` 는 테스트마다 트랜잭션을 열고 끝에 ROLLBACK 한다** — 그래서 테스트끼리 DB 흔적을 나누지 않고 `tearDown` 이 보통 필요 없다.
2. **`Client` 는 네트워크 없이 같은 프로세스 안에서 요청을 흉내 낸다** — 상태 코드 · JSON · DB 변화를 함께 확인한다.
3. **`factory_boy` 는 기본값을 선언해 두고 바꿀 것만 넘기게 한다** — `Sequence` 로 겹치지 않게, `LazyAttribute` 로 다른 필드에서 끌어온다.
4. **pytest 는 인자 이름으로 fixture 를 주입하고, parametrize 로 경계값을 행마다 돌린다.**
5. **바깥 서비스는 생성자로 받아 Mock 으로 바꿔 끼운다** — 돌려줄 값을 정하고, 어떻게 불렸는지 검사한다.

## 관련 자료

- `django-queryset` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [django-signals](../02-django-signals/2-summary.md)
- [flask-testing](../12-flask-testing/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `django-testing`

## 용어 풀이

- **테스트 격리** — 한 테스트의 결과가 다른 테스트에 영향을 주지 않는 성질.
- **트랜잭션** — 모두 반영하거나 모두 취소하는 DB 작업 묶음.
- **rollback** — 트랜잭션의 변경을 취소해 처음 상태로 되돌리는 일.
- **`TestCase`** — Django 가 주는 테스트 기반 클래스로, 테스트마다 트랜잭션을 감싼다.
- **`setUp` / `tearDown`** — 각 테스트 전 / 후에 실행되는 준비 · 정리 메서드.
- **`Client`** — HTTP 요청을 같은 프로세스 안에서 흉내 내는 Django 테스트 도구.
- **상태 코드** — HTTP 응답의 성공 · 실패를 알리는 세 자리 숫자.
- **Factory** — 모델 객체 만드는 법을 선언해 둔 클래스.
- **`Sequence`** — 만들 때마다 늘어나는 번호로 값을 만드는 선언.
- **`LazyAttribute`** — 같은 객체의 다른 필드를 읽어 값을 만드는 선언.
- **`SubFactory`** — 관계 대상 객체를 다른 Factory 로 함께 만드는 선언.
- **`Faker`** — 그럴듯한 무작위 값을 만드는 선언.
- **`create_batch`** — 객체를 여러 개 한 번에 만드는 Factory 메서드.
- **fixture** — 인자 이름으로 요청하면 pytest 가 만들어 넣어 주는 준비물.
- **parametrize** — 같은 테스트를 입력값 묶음마다 반복시키는 표시.
- **경계값** — 유효와 무효가 갈리는 지점 근처의 값.
- **Mock / `MagicMock`** — 진짜 객체 대신 끼워, 반환값을 정하고 호출을 기록하는 가짜 객체.
- **`spec`** — Mock 이 흉내 낼 클래스를 정해, 그 클래스에 없는 속성 접근을 막는 인자.
- **`return_value`** — Mock 을 불렀을 때 돌려줄 값.
- **`assert_called_once_with`** — 정확히 한 번, 주어진 인자로 불렸는지 검사하는 메서드.
- **`call_args`** — Mock 의 마지막 호출 인자.
- **의존성 주입** — 쓸 객체를 스스로 만들지 않고 바깥에서 받는 방식.

## 더 들어가면

- 원본 fixture 의 `db` 인자는 pytest-django 가 주는 fixture 로, 이것을 요구한 테스트만 DB 를 쓸 수 있게 한다 (확인 필요).
- `client` 도 pytest-django 가 주는 fixture 로 `django.test.Client` 객체를 넘긴다 (확인 필요).
- `--reuse-db` 는 테스트 DB 를 실행 사이에 지우지 않고 다시 써서 시작을 빠르게 한다 (확인 필요).
- `-x` 는 첫 실패에서 멈추고, `-v` 는 테스트 이름을 하나씩 자세히 보여 준다 (확인 필요).
- 테스트 안에서 커밋 후 동작(`on_commit` 등)이나 실제 트랜잭션 경계를 검사하려면 rollback 방식이 아닌 `TransactionTestCase` 를 쓴다 (확인 필요).
- Django `Client` 는 `content_type='application/json'` 일 때 사전 `data` 를 JSON 으로 바꿔 보낸다 — 그래서 pytest 절처럼 `json.dumps` 없이도 된다 (확인 필요).
- 클래스 수준에서 한 번만 데이터를 만들고 테스트마다 공유하려면 `setUpTestData` 를 쓴다 (확인 필요).
- `unittest.mock.patch` 는 모듈 안의 이름을 테스트 동안만 Mock 으로 바꿔치기한다 — 의존성 주입을 할 수 없는 코드에서 쓴다 (확인 필요).
- `factory_boy` 에서 `Factory.build()` 는 DB 에 저장하지 않은 객체를 만든다 (확인 필요).
