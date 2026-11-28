# python/python-testing-deep/07 — 테스트 더블 (Stub, Mock, Spy, Fake) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 가격 7000 · 결제 ID "PAY-777" 을 돌려주는 Stub 으로 수량 3 주문 (예측)

```python
# 질문용 발췌
inv = MagicMock()
inv.check_stock.return_value = True
inv.get_price.return_value = 7000
pay = MagicMock()
pay.charge.return_value = "PAY-777"
result = OrderService(inv, pay, MagicMock()).place_order("P1", 3, "u@test.com")
```

- `result["total"]` 은 무엇인가?
- `result["payment_id"]` 는 무엇인가?
- 이 테스트가 Stub 방식이라면 무엇을 `assert` 하고 무엇을 `assert` 하지 않나?

### 2. 재고 확인이 `False` 인 주문 (예측)

- `check_stock` 이 `False` 를 돌려주도록 정하고 `place_order` 를 부르면 `get_price` · `charge` · `reduce_stock` · `send` 중 불리는 것은 무엇인가?
- 그렇다면 알림 자리에 메서드 없는 빈 클래스 객체를 넣어도 테스트가 깨지지 않는 까닭은 무엇인가?

### 3. Fake 재고로 두 번 주문 (예측)

```python
# 질문용 발췌
fake = FakeInventoryDB()          # P1: 재고 10 · 5000원
service = OrderService(fake, MagicMock(), MagicMock())
service.place_order("P1", 3, "a@test.com")
service.place_order("P1", 8, "a@test.com")
```

- 첫 주문 뒤 `fake._products["P1"]["stock"]` 은 몇인가?
- 두 번째 주문은 어떻게 끝나나?
- 두 번째 주문 뒤 재고는 몇인가?

### 4. `wraps` 로 감싼 계산기 (예측)

```python
# 질문용 발췌
spy = MagicMock(wraps=RealCalculator())
r1 = spy.multiply(4, 5)
r2 = spy.add(1, 1)
r3 = spy.add(2, 2)
```

- `r1` 은 무엇인가?
- `spy.add.call_count` 와 `spy.multiply.call_count` 는 각각 몇인가?
- 여기서 `spy.add.assert_called_once_with(2, 2)` 를 부르면 통과하나?

### 5. 상태 검증을 먼저 권하는 팁 (왜)

- 원본 팁은 왜 Stub(상태 검증)을 먼저 고르고 Mock(행동 검증)은 꼭 필요할 때만 쓰라고 하나?
- 행동 검증 테스트는 어떤 종류의 코드 변경에 깨지기 쉬운가?

### 6. 알림 발송은 호출로 확인한다 (왜)

- `notification.send` 가 제대로 불렸는지는 왜 `place_order` 의 반환값만 봐서는 확인할 수 없나?

### 7. Fake 에 없는 상품 `"P9"` (경계)

- `FakeInventoryDB` 의 `check_stock("P9", 1)` 은 무엇을 돌려주나?
- `get_price("P9")` 를 바로 부르면 어떻게 되나?
- `place_order("P9", 1, ...)` 는 어느 단계에서 어떤 예외로 끝나나?

### 8. Fake 와 Stub, 그리고 통합 테스트 (연결)

- Fake 와 Stub 은 둘 다 간접 입력을 주는데, 무엇이 다른가?
- 원본 팁이 Fake 를 통합 테스트의 인메모리 DB 와 잇는 까닭은 무엇인가?

### 9. Fake 테스트의 결제 자리 `MagicMock(return_value="PAY")` (경계)

- 그 테스트에서 `result["payment_id"]` 는 문자열 `"PAY"` 인가?
- 그런데도 원본의 `test_with_fake` 가 통과하는 까닭은 무엇인가?

### 10. 예제 파일을 `python` 으로 직접 실행하면 (예측)

- `test_` 로 시작하는 함수 다섯 개는 실행되나?
- 화면에는 어떤 내용이 어떤 차례로 찍히나?

## 실습

### 실습 1. 주문 서비스 하나에 다섯 가지 테스트 더블 세우기

**만들 것** — 재고 · 결제 · 알림 협력자에 기대는 `OrderService` 를 만들고, Dummy · Stub · Mock · Spy · Fake 를 하나씩 쓰는 pytest 테스트 다섯 개를 쓴다.

**준비물** — pytest 가 필요하다(`pip install pytest`). `unittest.mock` 은 표준 라이브러리라 따로 설치하지 않는다. 파일 이름은 `test_doubles.py` 로 둔다.

**요구 조건**

1단계 — 테스트 대상
1. `OrderService` 는 생성자에서 `inventory` · `payment` · `notification` 셋을 받아 같은 이름의 속성으로 둔다.
2. `place_order(product_id, quantity, user_email)` 는 재고 확인(`check_stock`)이 거짓이면 `ValueError("재고 부족")` 를 낸다.
3. 이어서 가격을 조회(`get_price`)해 합계 = 가격 × 수량을 구하고, `payment.charge(user_email, total)` → `inventory.reduce_stock(product_id, quantity)` → `notification.send(user_email, f"주문 완료: {total}원")` 차례로 부른 뒤 `{"total": 합계, "payment_id": 결제 반환값}` 을 돌려준다.

2단계 — Dummy
4. `test_with_dummy` 는 재고 확인이 `False` 를 돌려주는 `MagicMock` 을 만들고, 알림 자리에는 메서드가 없는 빈 클래스 `DummyNotification` 의 객체를 넣는다.
5. `pytest.raises(ValueError)` 로 `place_order` 가 예외를 내는지 확인한다.

3단계 — Stub
6. `test_with_stub` 는 재고 확인 `True` · 가격 `10000` · 결제 ID `"PAY-001"` 을 `return_value` 로 정하고 수량 2 로 주문한다.
7. 반환된 딕셔너리의 `total` 과 `payment_id` 만 `assert` 하고, 호출은 검사하지 않는다.

4단계 — Mock
8. `test_with_mock` 은 가격 `5000` · 결제 ID `"PAY-002"` 로 정하고 수량 3 으로 주문한다.
9. `check_stock` · `reduce_stock` · `charge` · `send` 넷을 `assert_called_once_with` 로 각각 정확한 인자와 함께 검사한다.

5단계 — Spy
10. `RealCalculator` 는 `add(a, b)` 와 `multiply(a, b)` 를 진짜로 계산한다.
11. `test_with_spy` 는 `MagicMock(wraps=...)` 로 계산기를 감싸 `add(2, 3)` 의 진짜 결과를 확인하고, `assert_called_once_with` 와 `call_count` 로 호출 기록도 확인한다.

6단계 — Fake
12. `FakeInventoryDB` 는 시드 딕셔너리(`_products`)를 두고 `check_stock` (없거나 모자라면 거짓) · `get_price` · `reduce_stock` (재고를 진짜로 줄임) 을 구현한다.
13. `test_with_fake` 는 결제 · 알림 자리에 `MagicMock` 을 넣고, `"P1"` 2개 주문의 합계와 주문 뒤 재고를 확인한 다음, 재고 0 인 `"P2"` 주문이 `ValueError` 를 내는지 확인한다.

7단계 — 화면 출력
14. 모듈 최상위의 절 머리 출력과 `__main__` 의 비교표 출력은 시작 코드에 채워 둔 그대로 둔다.

**시작 코드**

```python
from unittest.mock import MagicMock, patch, call
import pytest


class OrderService:
    def __init__(self, inventory, payment, notification):
        # TODO: 협력자 셋을 속성으로 둔다
        pass

    def place_order(self, product_id, quantity, user_email):
        # TODO: 재고 확인 → 없으면 ValueError("재고 부족")
        # TODO: 가격 조회 → 합계
        # TODO: 결제 → 재고 차감 → 알림
        # TODO: {"total": ..., "payment_id": ...} 반환
        pass


print("=== 1. Dummy ===")
print("목적: 파라미터를 채우기 위한 자리표시자")
print("실제로 호출되지 않음\n")

def test_with_dummy():
    dummy_notification = None  # 가장 단순한 Dummy

    class DummyNotification:
        pass

    # TODO: 재고 확인이 False 인 inventory 를 만들고
    # TODO: 알림 자리에 DummyNotification() 을 넣어 ValueError 를 확인한다


print("=== 2. Stub ===")
print("목적: 테스트에 필요한 간접 입력 제공")
print("호출 검증 안 함, 값만 반환\n")

def test_with_stub():
    # TODO: return_value 로 재고 · 가격 · 결제 ID 를 정한다
    # TODO: 수량 2 로 주문하고 결과만 assert 한다
    pass


print("=== 3. Mock ===")
print("목적: 올바른 메서드가 올바른 인자로 호출되었는지 검증")
print("상호작용(행동) 검증\n")

def test_with_mock():
    # TODO: 가격 5000 · 결제 ID "PAY-002" 로 정하고 수량 3 으로 주문한다
    # TODO: 협력자 호출 넷을 assert_called_once_with 로 검사한다
    pass


print("=== 4. Spy ===")
print("목적: 실제 로직을 실행하되 호출을 기록")
print("실제 구현 + 검증\n")

class RealCalculator:
    def add(self, a, b):
        pass  # TODO

    def multiply(self, a, b):
        pass  # TODO

def test_with_spy():
    calc = RealCalculator()
    # TODO: wraps 로 감싼 spy 를 만들고 add(2, 3) 의 결과와 호출 기록을 검사한다


print("=== 5. Fake ===")
print("목적: 실제와 유사하지만 단순화된 구현")
print("예: 인메모리 DB, 로컬 파일 캐시\n")

class FakeInventoryDB:
    def __init__(self):
        self._products = {
            "P1": {"stock": 10, "price": 5000},
            "P2": {"stock": 0, "price": 3000},
        }

    def check_stock(self, product_id, quantity):
        pass  # TODO: 상품이 있고 재고가 충분한가

    def get_price(self, product_id):
        pass  # TODO

    def reduce_stock(self, product_id, quantity):
        pass  # TODO: 재고를 진짜로 줄인다

def test_with_fake():
    fake_inventory = FakeInventoryDB()
    # TODO: 서비스를 만들고 P1 2개 주문 → 합계 · 남은 재고 확인
    # TODO: P2 1개 주문 → ValueError 확인


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

**확인 방법** — `pytest test_doubles.py -v` 로 돌려 `test_with_dummy` · `test_with_stub` · `test_with_mock` · `test_with_spy` · `test_with_fake` 다섯이 모두 통과하는지 본다. `python test_doubles.py` 로도 직접 실행해 찍히는 내용을 퀴즈 10 의 답과 견준다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
