# python/python-testing-deep/07 — 테스트 더블 (Stub, Mock, Spy, Fake) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 합계 21000, 결제 ID "PAY-777" — 결과만 본다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `result["total"]` 은 `21000` 이다.
- `result["payment_id"]` 는 `"PAY-777"` 이다.
- Stub 방식이면 이 두 값만 `assert` 하고, `check_stock` · `charge` 등이 어떤 인자로 몇 번 불렸는지는 `assert` 하지 않는다.

**왜 그런가**
- `check_stock` 이 `True` 라 예외 없이 지나가고, `get_price` 가 `7000` 을 돌려주어 `total = 7000 × 3 = 21000` 이다.
- `charge` 의 `return_value` 가 `"PAY-777"` 이고, 그 값이 그대로 `payment_id` 자리에 들어간다.
- Stub 은 간접 입력을 주고 결과(상태)로 판정한다 — 2-summary 「동작 방식 (3)」, 「어디서 틀리나 1」.

### 2. 아무것도 불리지 않는다 — 첫 단계에서 예외

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `get_price` · `charge` · `reduce_stock` · `send` 넷 다 불리지 않는다.
- 알림 객체는 손도 대지 않으므로 `send` 가 없는 빈 객체여도 문제가 없다.

**왜 그런가**
- `place_order` 는 `check_stock` 결과가 거짓이면 바로 `ValueError("재고 부족")` 를 내고, 그 아래 줄은 실행되지 않는다.
- `pytest.raises(ValueError)` 가 그 예외를 받아 테스트는 통과한다.
- Dummy 는 불리지 않을 때만 안전하다 — 경로가 바뀌어 `send` 가 불리면 `AttributeError` 가 난다.
- 근거: 2-summary 「동작 방식 (1)」「(2)」, 「어디서 틀리나 4」.

### 3. 7 → 예외 → 여전히 7

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- 첫 주문 뒤 재고는 `7` 이다.
- 두 번째 주문은 `ValueError("재고 부족")` 로 끝난다.
- 두 번째 주문 뒤에도 재고는 `7` 이다.

**왜 그런가**
- 첫 주문: `check_stock` 이 `10 >= 3` 으로 참, `reduce_stock` 이 `10 - 3` 으로 재고를 7 로 바꾼다.
- 두 번째 주문: `check_stock` 이 `7 >= 8` 로 거짓이라 첫 단계에서 예외가 난다.
- 예외가 `reduce_stock` 보다 먼저 나므로 재고는 줄지 않는다.
- Fake 는 상태가 호출 사이에 이어진다 — Stub 이라면 매번 정한 같은 값만 돌려줄 것이다.
- 근거: 2-summary 「동작 방식 (6)」.

### 4. 진짜 결과 20, 기록은 add 2번 · multiply 1번

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `r1` 은 `20` 이다.
- `spy.add.call_count` 는 `2`, `spy.multiply.call_count` 는 `1` 이다.
- `spy.add.assert_called_once_with(2, 2)` 는 통과하지 않는다 — `AssertionError` 가 난다.

**왜 그런가**
- `wraps` 는 호출을 기록한 뒤 진짜 `RealCalculator` 의 같은 이름 메서드로 넘기므로 `multiply(4, 5)` 는 진짜로 `20` 이다.
- 기록은 메서드마다 따로 쌓여 `add` 는 두 번, `multiply` 는 한 번이다.
- `assert_called_once_with` 는 「마지막 호출이 이 인자인가」가 아니라 「정확히 한 번, 이 인자로」를 묻는다 — `add` 는 두 번 불렸다.
- 근거: 2-summary 「동작 방식 (5)」, 「문법」, 「어디서 틀리나 7」.

### 5. 행동 검증은 내부 절차에 묶인다

- 상태 검증은 「무엇이 나왔나」만 보므로, 같은 결과를 내는 한 내부를 고쳐도 계속 통과한다.
- 행동 검증은 「무엇을 몇 번, 어떤 인자로 불렀나」라는 내부 절차를 받아 적으므로, 결과는 같고 호출 방식만 바꾼 리팩터링(호출 횟수 · 인자 모양 변경 등)에도 깨진다.
- 그래서 원본 팁은 상태 검증을 기본으로 하고, 결과에 흔적이 없는 부수 효과(이메일 발송 등)를 확인할 때만 행동 검증을 쓰라고 한다.
- 근거: 2-summary 「어디서 틀리나 2」. 리팩터링에 깨진다는 이유는 (원본에 근거 없음 — 추론).

### 6. `send` 의 효과는 반환값에 남지 않는다

- `place_order` 가 돌려주는 것은 `{"total", "payment_id"}` 뿐이고, `send` 의 결과는 어디에도 들어가지 않는다.
- 알림이 갔다는 사실은 바깥 세상의 변화(부수 효과)라서, 결과를 봐서는 알 수 없다.
- 그래서 `send` 를 Mock 으로 두고 `assert_called_once_with("user@test.com", "주문 완료: 15000원")` 처럼 호출 자체를 검사한다.
- 근거: 2-summary 「동작 방식 (4)」, 「언제 쓰고 언제 안 쓰나」.

### 7. `check_stock` 은 False, `get_price` 는 KeyError

- `check_stock("P9", 1)` 은 `False` 를 돌려준다 — `product is not None` 이 거짓이다.
- `get_price("P9")` 를 바로 부르면 딕셔너리에 키가 없어 `KeyError` 가 난다.
- `place_order("P9", 1, ...)` 는 첫 단계인 재고 확인에서 `ValueError("재고 부족")` 로 끝난다 — `get_price` 까지 가지 않으므로 `KeyError` 는 나지 않는다.
- Fake 도 코드이므로 메서드마다 경계 처리가 다를 수 있다는 것이 요점이다.
- 근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 5」.

### 8. Fake 는 진짜 로직과 상태를 가진다

- Stub 은 `return_value` 로 정한 값을 호출할 때마다 똑같이 돌려줄 뿐, 로직도 상태도 없다.
- Fake 는 진짜와 같은 메서드 이름을 갖추고 단순하지만 진짜 로직을 돌린다 — 재고를 줄이면 다음 확인 결과가 달라진다.
- 그래서 여러 호출이 맞물리는 흐름(주문 → 재고 감소 → 다음 주문 실패)을 진짜 DB 없이 메모리 안에서 시험할 수 있고, 이것이 통합 테스트에서 실제 DB 대신 인메모리 구현을 쓰는 까닭이다.
- 근거: 2-summary 「동작 방식 (3)」「(6)」, 「언제 쓰고 언제 안 쓰나」.

### 9. `"PAY"` 가 아니라 `MagicMock` 객체다 — 검사하지 않아서 통과한다

- `result["payment_id"]` 는 문자열 `"PAY"` 가 아니라, `charge(...)` 가 돌려준 새 `MagicMock` 객체다.
- `MagicMock(return_value="PAY")` 는 Mock 자체를 `payment(...)` 처럼 부를 때의 값을 정한다.
- `OrderService` 는 `payment.charge(...)` 를 부르고, `charge` 의 반환값은 정해 두지 않았다.
- 원본 `test_with_fake` 는 `total` 과 재고만 검사하고 `payment_id` 는 검사하지 않으므로 통과한다.
- `"PAY"` 를 얻으려면 `payment.charge.return_value = "PAY"` 로 써야 한다.
- 근거: 2-summary 「문법」, 「어디서 틀리나 3」.

### 10. 테스트는 안 돌고, 절 머리 다섯 묶음과 비교표가 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `test_` 함수 다섯 개는 정의만 되고 실행되지 않는다.
- 먼저 모듈 최상위의 절 머리가 1. Dummy → 2. Stub → 3. Mock → 4. Spy → 5. Fake 차례로 세 줄씩 찍힌다(각 묶음 끝의 `\n` 때문에 빈 줄이 하나씩 붙는다).
- 이어서 `__main__` 블록이 `=== 테스트 더블 비교 ===`, 다섯 종류의 비교표 다섯 줄, 빈 줄, 맺음 세 줄을 찍는다.
- 비교표의 칸 폭은 글자 수로 맞추므로 한글이 섞인 칸은 화면에서 세로줄이 어긋나 보일 수 있다.

**왜 그런가**
- 함수 밖의 `print` 는 파일을 불러올 때 실행되지만, `def` 안의 내용은 누가 불러야 실행된다.
- `test_` 함수를 찾아 부르는 것은 pytest 의 일이고, 직접 실행에서는 아무도 부르지 않는다.
- `if __name__ == '__main__':` 블록은 직접 실행할 때만 돈다.
- 근거: 2-summary 「동작 방식 (7)」.

## 실습 정답

### 실습 1. 주문 서비스 하나에 다섯 가지 테스트 더블 세우기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 협력자 셋을 속성으로 | `OrderService.__init__` 의 `self.inventory` · `self.payment` · `self.notification` |
| 2. 재고 없으면 `ValueError` | `place_order` 의 `if not self.inventory.check_stock(...)` → `raise ValueError("재고 부족")` |
| 3. 가격 · 결제 · 차감 · 알림 · 반환 | `get_price` → `total = price * quantity` → `charge` → `reduce_stock` → `send` → `return {"total": ..., "payment_id": ...}` |
| 4. 재고 없음 Stub + 빈 클래스 Dummy | `test_with_dummy` 의 `inventory.check_stock.return_value = False`, `class DummyNotification: pass` |
| 5. 예외 확인 | `with pytest.raises(ValueError):` |
| 6. 재고 · 가격 · 결제 ID 고정, 수량 2 | `test_with_stub` 의 `return_value = True` · `10000` · `"PAY-001"`, `place_order("P1", 2, ...)` |
| 7. 결과만 검사 | `assert result["total"] == 20000`, `assert result["payment_id"] == "PAY-001"` |
| 8. 가격 5000 · `"PAY-002"`, 수량 3 | `test_with_mock` 의 `get_price.return_value = 5000`, `charge.return_value = "PAY-002"` |
| 9. 호출 넷 검사 | `assert_called_once_with` 네 줄(`check_stock` · `reduce_stock` · `charge` · `send`) |
| 10. 진짜 계산기 | `RealCalculator.add` · `multiply` |
| 11. `wraps` Spy | `test_with_spy` 의 `MagicMock(wraps=calc)`, `assert result == 5`, `assert_called_once_with(2, 3)`, `call_count == 1` |
| 12. Fake 저장소 | `FakeInventoryDB._products`, `check_stock` · `get_price` · `reduce_stock` |
| 13. Fake 로 주문 흐름 | `test_with_fake` 의 `total == 10000`, `_products["P1"]["stock"] == 8`, `"P2"` 주문의 `pytest.raises(ValueError)` |
| 14. 화면 출력 | 모듈 최상위 `print` 다섯 묶음, `if __name__ == '__main__':` 비교표 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-testing-deep/reference/test-doubles.py`

```python
# [테스팅 심화] 테스트 더블 (Stub, Mock, Spy, Fake)
# 설명: Stub, Mock, Spy, Fake, Dummy의 차이와 각각의 구현 방법 및 적절한 사용 시나리오
# 팁: Stub은 결과를 검증하고, Mock은 행동을 검증한다. 가능하면 상태 검증(Stub)을 선호하고, 부작용(이메일 발송 등)을 확인할 때만 행동 검증(Mock)을 사용한다. Fake는 통합 테스트에서 실제 DB 대신 인메모리 구현을 사용할 때 유용하다. MagicMock(wraps=obj)로 Spy를 쉽게 만들 수 있다.

# unittest.mock: 표준 mock 도구 - 모든 더블 종류 구현 가능
from unittest.mock import MagicMock, patch, call
# pytest: 예외 검증 등
import pytest

# === 테스트 대상 시스템 ===
# OrderService: 3개의 협력자(재고/결제/알림)에 의존
class OrderService:
    def __init__(self, inventory, payment, notification):
        self.inventory = inventory
        self.payment = payment
        self.notification = notification

    # 주문 처리 - 4개 협력자 호출이 순서대로 발생
    def place_order(self, product_id, quantity, user_email):
        # 재고 확인 (간접 입력)
        if not self.inventory.check_stock(product_id, quantity):
            raise ValueError("재고 부족")

        # 가격 조회 (간접 입력)
        price = self.inventory.get_price(product_id)
        total = price * quantity

        # 결제 (부수 효과 + 간접 입력)
        payment_result = self.payment.charge(user_email, total)

        # 재고 차감 (부수 효과)
        self.inventory.reduce_stock(product_id, quantity)

        # 알림 발송 (부수 효과)
        self.notification.send(user_email, f"주문 완료: {total}원")

        return {"total": total, "payment_id": payment_result}

# === 1. Dummy: 사용되지 않는 객체 ===
print("=== 1. Dummy ===")
print("목적: 파라미터를 채우기 위한 자리표시자")
print("실제로 호출되지 않음\n")

# Dummy 시연: notification은 호출되지 않으므로 빈 객체로 충분
def test_with_dummy():
    """notification은 이 테스트에서 사용되지 않지만 생성자에 필요"""
    dummy_notification = None  # 가장 단순한 Dummy

    # 또는: 빈 클래스를 Dummy로 사용
    class DummyNotification:
        pass

    inventory = MagicMock()
    inventory.check_stock.return_value = False  # 재고 없음으로 설정

    service = OrderService(inventory, MagicMock(), DummyNotification())
    with pytest.raises(ValueError):
        service.place_order("P1", 1, "test@test.com")
    # notification은 호출되지 않으므로 Dummy로 충분

# === 2. Stub: 미리 정한 값을 반환 ===
print("=== 2. Stub ===")
print("목적: 테스트에 필요한 간접 입력 제공")
print("호출 검증 안 함, 값만 반환\n")

# Stub 시연: 결과(상태)를 검증, 호출 방법은 무관심
def test_with_stub():
    """Stub: inventory가 정해진 값을 반환하도록 설정"""
    # Stub 설정 - 정해진 값만 반환
    stub_inventory = MagicMock()
    stub_inventory.check_stock.return_value = True   # 항상 재고 있음
    stub_inventory.get_price.return_value = 10000    # 가격 고정

    stub_payment = MagicMock()
    stub_payment.charge.return_value = "PAY-001"     # 결제 ID 고정

    service = OrderService(stub_inventory, stub_payment, MagicMock())
    result = service.place_order("P1", 2, "user@test.com")

    # Stub 검증: 반환값(결과)만 확인, 호출 방법은 확인 안 함 - 상태 기반 검증
    assert result["total"] == 20000
    assert result["payment_id"] == "PAY-001"

# === 3. Mock: 행동을 검증 ===
print("=== 3. Mock ===")
print("목적: 올바른 메서드가 올바른 인자로 호출되었는지 검증")
print("상호작용(행동) 검증\n")

# Mock 시연: 호출 여부와 인자를 검증 - 행동 기반 검증
def test_with_mock():
    """Mock: 호출 여부와 인자를 검증"""
    mock_inventory = MagicMock()
    mock_inventory.check_stock.return_value = True
    mock_inventory.get_price.return_value = 5000

    mock_payment = MagicMock()
    mock_payment.charge.return_value = "PAY-002"

    mock_notification = MagicMock()

    service = OrderService(mock_inventory, mock_payment, mock_notification)
    service.place_order("P1", 3, "user@test.com")

    # Mock 검증: 모든 협력자가 올바른 인자로 호출되었는지
    mock_inventory.check_stock.assert_called_once_with("P1", 3)
    mock_inventory.reduce_stock.assert_called_once_with("P1", 3)
    mock_payment.charge.assert_called_once_with("user@test.com", 15000)
    mock_notification.send.assert_called_once_with(
        "user@test.com", "주문 완료: 15000원"
    )

# === 4. Spy: 실제 동작 + 호출 기록 ===
print("=== 4. Spy ===")
print("목적: 실제 로직을 실행하되 호출을 기록")
print("실제 구현 + 검증\n")

# 실제 구현 클래스
class RealCalculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

# Spy 시연: wraps로 실제 호출 + 추적
def test_with_spy():
    """Spy: 실제 메서드를 호출하되 호출을 추적"""
    calc = RealCalculator()

    # wraps=calc: 실제 메서드를 호출하면서 기록 (Mock과 다름)
    spy_calc = MagicMock(wraps=calc)

    result = spy_calc.add(2, 3)
    assert result == 5  # 실제 결과 (mock이 아닌 진짜 계산)

    # 호출 기록도 동시에 검증 가능
    spy_calc.add.assert_called_once_with(2, 3)  # 호출 검증
    assert spy_calc.add.call_count == 1

# === 5. Fake: 단순화된 실제 구현 ===
print("=== 5. Fake ===")
print("목적: 실제와 유사하지만 단순화된 구현")
print("예: 인메모리 DB, 로컬 파일 캐시\n")

# FakeInventoryDB: 실제 인터페이스를 만족하는 단순 구현
class FakeInventoryDB:
    """실제 DB 대신 메모리에서 동작하는 Fake"""
    def __init__(self):
        # 시드 데이터
        self._products = {
            "P1": {"stock": 10, "price": 5000},
            "P2": {"stock": 0, "price": 3000},
        }

    # 실제 동작 구현 - 단순화되었지만 진짜 로직이 있음
    def check_stock(self, product_id, quantity):
        product = self._products.get(product_id)
        return product is not None and product["stock"] >= quantity

    def get_price(self, product_id):
        return self._products[product_id]["price"]

    def reduce_stock(self, product_id, quantity):
        self._products[product_id]["stock"] -= quantity

# Fake 시연: 실제 비즈니스 로직이 동작 (Mock보다 신뢰성 높음)
def test_with_fake():
    """Fake: 실제와 동일한 인터페이스, 단순화된 구현"""
    fake_inventory = FakeInventoryDB()
    service = OrderService(fake_inventory, MagicMock(return_value="PAY"), MagicMock())

    # 재고가 있는 상품 - 정상 처리
    result = service.place_order("P1", 2, "user@test.com")
    assert result["total"] == 10000

    # 재고가 감소했는지 확인 (Fake의 상태 검증)
    assert fake_inventory._products["P1"]["stock"] == 8

    # 재고가 없는 상품 - 예외
    with pytest.raises(ValueError):
        service.place_order("P2", 1, "user@test.com")

if __name__ == '__main__':
    print("=== 테스트 더블 비교 ===")
    doubles = [
        ("Dummy",  "사용되지 않음",     "파라미터 채우기"),
        ("Stub",   "정해진 값 반환",    "간접 입력 제공"),
        ("Mock",   "호출 검증",         "상호작용(행동) 검증"),
        ("Spy",    "실제 실행 + 기록",  "실제 동작 확인 + 호출 추적"),
        ("Fake",   "단순화된 실제 구현", "인메모리 DB 등"),
    ]
    for name, behavior, purpose in doubles:
        print(f"  {name:6s}: {behavior:20s} | {purpose}")
    print()
    print("Stub → 상태(결과) 기반 테스트")
    print("Mock → 행동(상호작용) 기반 테스트")
    print("가능하면 Stub(상태 검증)을 선호, 꼭 필요할 때만 Mock(행동 검증)")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- Stub · Mock · Spy 는 모두 `MagicMock` 이고, 갈리는 곳은 「`return_value` 를 정하고 결과를 보나 · 호출을 검사하나 · `wraps` 로 진짜에 넘기나」다.
- Dummy 테스트는 재고 확인에서 예외가 먼저 나는 경로를 골랐기 때문에 빈 객체로 충분하다.
- Mock 테스트의 `charge` 인자 `15000` 과 알림 문구 `"주문 완료: 15000원"` 은 가격 5000 × 수량 3 에서 나온다.
- Fake 는 상태가 이어지므로 「주문 → 재고 감소」를 재고 숫자로 직접 확인할 수 있다.
- Fake 테스트의 결제 자리 `MagicMock(return_value="PAY")` 는 `charge` 의 반환값을 정하지 않는다 — 결제 ID 를 검사하려면 `charge.return_value` 를 써야 한다.
- `patch` · `call` 은 불러오기만 하고 쓰지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
