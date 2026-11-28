# python/python-testing-deep/07 — 테스트 더블 (Stub, Mock, Spy, Fake) — 정리 (힌트)

> 출처 — study-site 항목 `python/test-doubles`(항목 데이터 `data/python/testing-deep.json`) · 정답 코드 study-practice `python/python-testing-deep/reference/test-doubles.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**테스트 더블은 「영화 촬영장의 대역」이다.**
진짜 배우를 쓰기에 위험하거나 비싸거나 느린 장면에는 대역을 세운다.
대역은 하는 일에 따라 종류가 나뉜다.
뒷모습으로 자리만 채우는 엑스트라가 있다.
정해진 대사만 하는 대역도 있다.
감독이 동작 하나하나를 체크하는 대역도 있다.
진짜 배우가 연기하고 옆에서 기록원이 받아 적는 경우도 있다.
진짜처럼 지었지만 크기를 줄인 세트장도 있다.
테스트도 똑같은 구조다.
진짜 DB · 결제 서버 · 메일 서버 대신 대역을 세워 테스트 대상만 따로 시험한다.

> **테스트 더블** — 테스트에서 진짜 협력 객체 대신 넣는 대역 객체를 통틀어 부르는 말이다.\
> 예: 진짜 결제 서비스 대신 넣은 `MagicMock()`.

| 비유 | 실체 |
|---|---|
| 자리만 채우는 엑스트라 | Dummy — 불리지 않는 자리표시자 |
| 정해진 대사만 하는 대역 | Stub — 미리 정한 값을 돌려준다 |
| 동작을 체크받는 대역 | Mock — 어떻게 불렸는지를 검증받는다 |
| 진짜 배우 + 기록원 | Spy — 진짜를 실행하면서 호출을 기록한다 |
| 축소판 세트장 | Fake — 단순하지만 진짜로 동작하는 구현 |

```text
                 테스트
                   │ (대역을 골라 넣는다)
                   ▼
            OrderService ──► inventory     진짜: DB       대역: Stub · Fake
            (테스트 대상) ──► payment       진짜: 결제 서버  대역: Stub · Mock
                         ──► notification  진짜: 메일 발송  대역: Mock · Dummy
```

## 이 주제가 답하려는 질문

1. 진짜 DB · 결제 · 메일 없이 `OrderService` 하나만 따로 어떻게 시험하나?
2. Dummy · Stub · Mock · Spy · Fake 는 무엇이 다르고, 각각 언제 고르나?
3. 테스트는 「결과」를 봐야 하나, 「호출」을 봐야 하나?
4. 파이썬 표준 도구 `MagicMock` 하나로 어떻게 여러 종류를 만드나?

## 동작 방식

### (1) 협력자를 갈아 끼우는 자리 — 생성자 주입, 간접 입력, 부수 효과

**언제 쓰나** — 테스트 대상이 다른 객체(협력자)에 기대어 일할 때 쓴다.
협력자를 생성자로 받으면 테스트에서 그 자리에 대역을 넣을 수 있다.

> **협력자** — 테스트 대상이 일을 하려고 부르는 다른 객체다.\
> 예: `OrderService` 가 부르는 `inventory` · `payment` · `notification`.

> **격리** — 테스트 대상을 진짜 협력자에게서 떼어 내 그것만 시험하는 것이다.\
> 예: 진짜 DB 없이 `place_order` 의 계산만 확인한다.

```text
place_order("P1", 2, "u@test.com")
  │
  ├─ inventory.check_stock(P1, 2)   ── 간접 입력 (False 면 ValueError("재고 부족"))
  ├─ inventory.get_price(P1)        ── 간접 입력 → total = price × 2
  ├─ payment.charge(email, total)   ── 부수 효과 + 간접 입력 (결제 ID 를 돌려줌)
  ├─ inventory.reduce_stock(P1, 2)  ── 부수 효과
  ├─ notification.send(email, msg)  ── 부수 효과
  ▼
return {"total": total, "payment_id": 결제 ID}
```

- 테스트는 `OrderService(inventory, payment, notification)` 에 대역 셋을 넣는다.
- 협력자가 돌려주는 값(재고 여부 · 가격 · 결제 ID)이 `place_order` 의 계산에 들어간다 — 이것이 간접 입력이다.
- 결제 · 재고 차감 · 알림은 바깥 세상을 바꾸는 일이다 — 이것이 부수 효과다.
- 부르는 순서는 재고 확인 → 가격 조회 → 결제 → 재고 차감 → 알림이다.
- 재고 확인이 `False` 면 첫 단계에서 예외가 나고 뒤 단계는 하나도 불리지 않는다.

> **간접 입력** — 인자가 아니라 협력자의 반환값으로 테스트 대상에 들어오는 값이다.\
> 예: `get_price` 가 돌려준 가격.

> **부수 효과** — 반환값 말고 바깥 상태를 바꾸는 일이다.\
> 예: 이메일 발송, 재고 차감.

### (2) Dummy — 자리만 채운다

**언제 쓰나** — 생성자나 함수가 인자를 요구하지만 그 테스트 경로에서는 전혀 쓰이지 않을 때 쓴다.

```text
inventory.check_stock → False (Stub)
OrderService(inventory, MagicMock(), DummyNotification())
  place_order(...)
    check_stock → False → raise ValueError   ← 여기서 끝
    (get_price · charge · reduce_stock · send 는 불리지 않음)
pytest.raises(ValueError) 가 예외를 받아 테스트 통과
```

- 재고 확인을 `False` 로 정해 두어 예외 경로로 보낸다.
- 알림 자리에는 메서드가 하나도 없는 빈 클래스 `DummyNotification()` 을 넣는다.
- 예외가 먼저 나므로 알림은 손도 대지 않고, 빈 객체로 충분하다.
- 원본은 `None` 도 「가장 단순한 Dummy」라고 적지만, 실제로 넘긴 것은 빈 클래스 객체다.

> **Dummy** — 인자 자리만 채우고 실제로는 불리지 않는 객체다.\
> 예: `class DummyNotification: pass` 의 인스턴스.

### (3) Stub — 정한 값을 돌려주고, 결과만 본다

**언제 쓰나** — 테스트 대상에 원하는 간접 입력을 넣어 주고, 그 입력으로 나온 결과(상태)를 확인할 때 쓴다.

```text
stub_inventory.check_stock.return_value = True
stub_inventory.get_price.return_value   = 10000
stub_payment.charge.return_value        = "PAY-001"
        │
        ▼ place_order("P1", 2, ...)
total = 10000 × 2 = 20000
return {"total": 20000, "payment_id": "PAY-001"}
        │
        ▼
assert result["total"] == 20000         ← 결과(상태)만 검사
assert result["payment_id"] == "PAY-001"
```

- `메서드.return_value = 값` 으로 그 메서드가 늘 돌려줄 값을 정한다.
- 테스트는 반환된 딕셔너리만 본다.
- 협력자가 몇 번, 어떤 인자로 불렸는지는 묻지 않는다.
- 원본 팁의 말로 하면 「Stub 은 결과를 검증한다」이다.

> **Stub** — 미리 정한 값을 돌려주어 간접 입력을 주는 대역이다. 호출은 검증하지 않는다.\
> 예: `get_price.return_value = 10000`.

> **상태 검증** — 테스트 대상이 내놓은 결과나 바뀐 상태를 보고 판정하는 방식이다.\
> 예: `assert result["total"] == 20000`.

### (4) Mock — 어떻게 불렸는지를 검증한다

**언제 쓰나** — 결과에 흔적이 남지 않는 부수 효과(이메일 발송 등)가 제대로 일어났는지 확인할 때 쓴다.

```text
place_order("P1", 3, "user@test.com")   (가격 5000)
        │
        ▼ Mock 들이 호출을 기록
check_stock("P1", 3) · reduce_stock("P1", 3)
charge("user@test.com", 15000)
send("user@test.com", "주문 완료: 15000원")
        │
        ▼
mock.메서드.assert_called_once_with(인자...)   ← 행동(상호작용) 검사
```

- `MagicMock` 은 불린 메서드와 인자를 모두 기록해 둔다.
- `assert_called_once_with(...)` 는 「정확히 한 번, 바로 이 인자로」 불렸는지 검사한다.
- 두 번 불렸거나 인자가 다르면 `AssertionError` 가 난다.
- `send` 는 `place_order` 의 반환값에 아무 흔적도 남기지 않는다 — 그래서 결과만 봐서는 알림이 갔는지 알 수 없고, 호출을 봐야 한다.

> **Mock** — 테스트 대상이 자기를 어떻게 불렀는지 기록하고 그 호출을 검증받는 대역이다.\
> 예: `mock_notification.send.assert_called_once_with(...)`.

> **행동 검증** — 결과 대신 협력자와 주고받은 호출(상호작용)을 보고 판정하는 방식이다.\
> 예: `charge` 가 `15000` 으로 한 번 불렸는지 본다.

### (5) Spy — 진짜를 실행하면서 기록한다

**언제 쓰나** — 진짜 동작 결과도 필요하고, 그 호출이 일어났는지도 확인하고 싶을 때 쓴다.

```text
calc     = RealCalculator()
spy_calc = MagicMock(wraps=calc)
        │
spy_calc.add(2, 3) ──► 기록: add(2, 3) ──► calc.add(2, 3) 실행 ──► 5
        │
assert result == 5                         ← 진짜 결과
spy_calc.add.assert_called_once_with(2, 3) ← 호출 기록
spy_calc.add.call_count == 1
```

- `MagicMock(wraps=obj)` 는 호출을 기록한 뒤 진짜 `obj` 의 같은 이름 메서드로 넘긴다.
- 돌아오는 값은 가짜가 아니라 진짜 계산 결과다.
- 호출 기록은 일반 Mock 처럼 `assert_called_once_with` · `call_count` 로 본다.
- 감싸지 않은 메서드(`multiply`)도 같은 방식으로 진짜에 넘어가고, 메서드마다 따로 기록된다.
- 원본 팁: 「`MagicMock(wraps=obj)` 로 Spy 를 쉽게 만들 수 있다.」

> **Spy** — 진짜 구현을 실행하면서 호출을 기록하는 대역이다.\
> 예: `MagicMock(wraps=RealCalculator())`.

### (6) Fake — 단순하지만 진짜로 동작하는 구현

**언제 쓰나** — 진짜 DB 같은 무거운 협력자 대신, 같은 메서드 이름을 갖고 메모리에서 진짜 로직을 돌리는 구현이 필요할 때 쓴다.
원본 팁은 「통합 테스트에서 실제 DB 대신 인메모리 구현을 쓸 때 유용하다」고 한다.

```text
FakeInventoryDB._products = {P1: 재고 10 · 5000원, P2: 재고 0 · 3000원}
        │
place_order("P1", 2)
  check_stock: P1 있고 10 >= 2 → True
  get_price:   5000 → total 10000
  reduce_stock: 10 - 2 → 8          ← 상태가 진짜로 바뀐다
        │
place_order("P2", 1)
  check_stock: 0 >= 1 → False → ValueError
```

- `check_stock` 은 상품이 없거나 재고가 모자라면 `False` 를 돌려준다.
- `get_price` 는 딕셔너리에서 꺼내므로, 없는 상품이면 `KeyError` 가 난다.
- `reduce_stock` 은 딕셔너리의 재고 숫자를 진짜로 줄인다.
- 그래서 Fake 는 여러 번 호출 사이에 상태가 이어진다 — Stub 처럼 늘 같은 값을 돌려주지 않는다.
- 테스트는 주문 뒤에 `fake_inventory._products["P1"]["stock"]` 을 읽어 상태를 확인한다.
- 원본 주석은 「Mock 보다 신뢰성 높음」이라고 적는다 — 진짜에 가까운 로직이 돌기 때문이지만, Fake 자신도 코드라서 진짜 DB 와 다르게 동작할 수 있다는 점은 남는다.

> **Fake** — 진짜와 같은 메서드를 갖춘, 단순화된 실제 구현이다.\
> 예: 딕셔너리로 재고를 다루는 `FakeInventoryDB`.

> **인메모리 구현** — 디스크나 서버 대신 프로그램 메모리 안의 자료구조로 저장소를 흉내 낸 것이다.\
> 예: `self._products = {...}`.

### (7) 파일 하나에 테스트와 화면 출력이 함께 있다 — 누가 무엇을 돌리나

**언제 쓰나** — 이 예제 파일을 어떻게 실행하느냐에 따라 무엇이 돌아가는지 가를 때 본다.

```text
python 파일.py                       pytest 파일.py
  모듈 최상위 print 5묶음 실행          모듈을 불러옴 → 최상위 print 실행
  test_ 함수는 정의만 됨 (호출 X)       test_ 함수 5개를 찾아 각각 실행
  __main__ 블록 → 비교표 출력          __main__ 블록은 실행 안 됨
```

- `print("=== 1. Dummy ===")` 같은 줄은 함수 밖(모듈 최상위)에 있어서 파일을 불러오기만 해도 실행된다.
- `def test_...` 는 함수를 정의할 뿐이고, 누가 부르지 않으면 실행되지 않는다.
- `test_` 로 시작하는 함수를 찾아 부르는 일은 pytest 가 한다.
- `if __name__ == '__main__':` 블록은 파일을 직접 실행할 때만 돈다.
- 비교표 줄은 `f"  {name:6s}: {behavior:20s} | {purpose}"` 로 칸을 맞춘다 — 폭은 글자 수로 세므로, 한글처럼 화면에서 두 칸을 차지하는 글자가 섞이면 세로줄이 어긋나 보일 수 있다.

## 문법 — 형태와 규칙

```python
from unittest.mock import MagicMock

stub = MagicMock()
stub.get_price.return_value = 3000        # Stub: get_price 가 늘 3000 을 돌려주게 한다

mock = MagicMock()
mock.send("a@b.c", "hi")
mock.send.assert_called_once_with("a@b.c", "hi")   # Mock: 정확히 한 번, 이 인자로

spy = MagicMock(wraps=RealCalculator())   # Spy: 진짜로 넘기며 기록
spy.add(1, 2)
assert spy.add.call_count == 1

class FakeStore:                          # Fake: 같은 메서드 이름 + 단순한 진짜 로직
    def __init__(self): self._d = {}
    def get(self, k): return self._d.get(k)
```

- `MagicMock()` 은 처음 듣는 속성 이름을 꺼내도 그 자리에서 자식 Mock 을 만들어 준다 — 그래서 `stub.get_price` 를 미리 정의하지 않아도 된다.
- `m.메서드.return_value = v` 는 「`m.메서드(...)` 를 부르면 `v`」다.
- `MagicMock(return_value=v)` 는 「`m(...)` — Mock 자체를 부르면 `v`」다. `m.메서드(...)` 의 값은 바꾸지 않는다.
- 아무것도 정하지 않은 `m.메서드(...)` 는 새 `MagicMock` 객체를 돌려준다.
- `assert_called_once_with(*args)` — 정확히 한 번, 같은 인자로 불렸는지 검사한다. 아니면 `AssertionError`.
- `m.메서드.call_count` — 그 메서드가 불린 횟수다.
- `MagicMock(wraps=obj)` — 호출을 `obj` 의 같은 이름 메서드로 넘기고 그 진짜 반환값을 돌려준다.
- `with pytest.raises(ValueError):` — 블록 안에서 그 예외가 나야 통과, 안 나면 실패다.
- Dummy 는 문법이랄 것이 없다 — 빈 클래스 객체나 `None` 을 넘긴다.
- Fake 는 그냥 평범한 클래스다 — 진짜 협력자와 같은 메서드 이름과 인자를 갖추면 된다.
- 원본은 `patch` · `call` 도 불러오지만 예제에서 쓰지 않는다.

## 어디서 틀리나

### 1. Stub · Mock 은 도구 이름이 아니라 쓰임새다

예제의 Stub · Mock · Spy 는 모두 같은 `MagicMock` 으로 만들었다.
차이는 「무엇을 검증하느냐」에 있다.
`return_value` 만 정하고 결과를 보면 Stub 으로 쓴 것이다.
`assert_called_...` 로 호출을 보면 Mock 으로 쓴 것이다.
원본 팁: 「Stub 은 결과를 검증하고, Mock 은 행동을 검증한다.」

### 2. Mock 을 기본값으로 쓰면 테스트가 구현에 묶인다

원본 팁은 「가능하면 상태 검증(Stub)을 선호하고, 부작용(이메일 발송 등)을 확인할 때만 행동 검증(Mock)을 사용하라」고 한다.
행동 검증 테스트는 「무엇을 몇 번, 어떤 인자로 부르나」라는 내부 절차를 그대로 받아 적는다.
그래서 결과는 같은데 내부 호출만 바꾼 리팩터링(예: 재고 확인을 두 번 부르게 바꿈)에도 `assert_called_once_with` 가 깨진다(원본에 근거 없음 — 추론).
결과만 보는 테스트는 결과가 같으면 계속 통과한다.

### 3. `MagicMock(return_value=...)` 와 `.메서드.return_value` 를 헷갈린다

원본 Fake 테스트는 결제 자리에 `MagicMock(return_value="PAY")` 를 넣는다.
원본의 주장(의도) → 결제 ID 로 `"PAY"` 가 나오게 하려는 것으로 보인다.
왜 의심스러운가 → `OrderService` 는 `self.payment.charge(...)` 를 부르지, `self.payment(...)` 를 부르지 않는다.
`return_value="PAY"` 는 Mock 자체를 부를 때의 값이므로, `charge(...)` 는 정해지지 않은 새 `MagicMock` 객체를 돌려준다.
그래서 `result["payment_id"]` 는 `"PAY"` 가 아니라 `MagicMock` 객체다.
테스트가 통과하는 것은 `payment_id` 를 검사하지 않기 때문이다.
`"PAY"` 가 나오게 하려면 `payment.charge.return_value = "PAY"` 로 써야 한다.

### 4. Dummy 가 실제로 불리면 깨진다

Dummy 는 불리지 않는다는 전제에서만 쓸 수 있다.
빈 클래스 `DummyNotification` 에는 `send` 가 없으니, 경로가 바뀌어 `send` 가 불리면 `AttributeError` 가 난다.
`None` 을 넘겨도 `None.send` 는 `AttributeError` 다.
원본은 `dummy_notification = None` 을 만들어 두고 실제로는 쓰지 않는다 — 「이런 꼴도 Dummy 다」를 보여 주는 줄일 뿐이다.

### 5. Fake 도 코드다 — 경계와 비공개 속성

`check_stock` 은 없는 상품에 `False` 를 돌려주지만, `get_price` 는 없는 상품에 `KeyError` 를 낸다.
`place_order` 는 재고 확인을 먼저 하므로 없는 상품은 `ValueError` 로 끝나지만, `get_price` 를 바로 부르면 `KeyError` 다.
테스트가 `fake_inventory._products` 라는 비공개 속성을 직접 읽는 것은 Fake 의 내부 구조에 테스트를 묶는다.
Fake 가 진짜 DB 와 다르게 동작하면(예: 재고가 음수가 되는 것을 막지 않음) 그 차이는 테스트로 드러나지 않는다(원본에 근거 없음 — 추론).

### 6. Spy 는 진짜를 실행한다

Spy 는 결과가 진짜인 대신, 부수 효과도 진짜로 일어난다.
진짜 메일을 보내는 객체를 `wraps` 로 감싸면 메일이 진짜로 나간다(원본에 근거 없음 — 추론).
부수 효과를 막아야 하면 Spy 가 아니라 Mock 을 쓴다.

### 7. `assert_called_once_with` 는 「마지막 호출」이 아니라 「정확히 한 번」이다

같은 인자로 두 번 불려도 실패한다.
「몇 번이든 이 인자로 불린 적 있나」를 묻는 검사가 아니다.

### 8. 원본 주석의 「4개 협력자」

원본 정답 코드의 주석은 `place_order` 를 「4개 협력자 호출이 순서대로 발생」이라고 적는다.
원본의 주장 → 협력자 4개.
왜 의심스러운가 → 생성자가 받는 협력자는 `inventory` · `payment` · `notification` 셋이고, 호출은 `check_stock` · `get_price` · `charge` · `reduce_stock` · `send` 다섯 번이다.
네 개로 세는 기준은 코드에서 보이지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| Dummy · Stub · Mock · Spy · Fake 다섯 가지 구분 | 테스트 분야의 용어 관습 — 파이썬 언어도 `unittest.mock` 도 이 구분을 강제하지 않는다 |
| `MagicMock` 이 처음 듣는 속성을 자식 Mock 으로 만든다 | `unittest.mock` 표준 라이브러리의 문서화된 동작 |
| `wraps=obj` 가 호출을 진짜 객체로 넘긴다 | `unittest.mock` 표준 라이브러리의 문서화된 동작 |
| `pytest.raises` · `test_` 함수를 찾아 돌림 | 제3자 라이브러리 pytest (수집 규칙은 설정으로 바뀐다) |
| 모듈 최상위 `print` 는 불러올 때 실행, `def` 안은 불릴 때만 | 파이썬 언어 |
| `__main__` 블록은 직접 실행할 때만 돈다 | 파이썬 언어(`__name__` 규칙) |
| `{name:6s}` 의 폭은 글자 수로 센다 | 파이썬 언어(형식 명세) — 화면에서 몇 칸으로 보이나는 터미널과 글꼴 몫 |
| `unittest.mock` 이 표준 라이브러리에 들어 있다 | 파이썬 표준 라이브러리 — 들어온 버전은 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 인자 자리는 있는데 그 경로에서 안 불림 | Dummy | 설정까지 해 둔 Mock(불필요한 준비) |
| 협력자의 반환값으로 계산 결과가 달라짐 | Stub + 결과 검증 | 호출 인자까지 검사하는 Mock |
| 반환값에 흔적 없는 부수 효과(메일 · 결제 요청) | Mock + 호출 검증 | Stub(결과만 봐서는 확인 불가) |
| 진짜 결과도 필요하고 호출도 확인 | Spy(`wraps`) | 부수 효과가 진짜로 나가면 곤란한 객체에 Spy |
| 여러 호출에 걸쳐 상태가 이어져야 함(재고 차감 등) | Fake(인메모리) | 늘 같은 값만 돌려주는 Stub |
| 진짜 DB 대신 통합 테스트 | Fake | 진짜 운영 DB |

## 핵심 문장

1. **테스트 더블은 진짜 협력자 대신 세우는 대역이고, 생성자로 받는 자리에 갈아 끼운다.**
2. **Stub 은 값을 주고 결과를 보며, Mock 은 호출을 기록하고 행동을 본다 — 도구는 같은 `MagicMock` 이다.**
3. **결과 검증을 먼저 고르고, 결과에 흔적 없는 부수 효과에만 행동 검증을 쓴다.**
4. **Spy 는 `MagicMock(wraps=obj)` 로 진짜를 실행하며 기록하고, Fake 는 메모리에서 진짜 로직을 돌린다.**
5. **Dummy 는 불리지 않을 때만 안전하다.**

## 관련 자료

- [pytest-mock](../03-pytest-mock/2-summary.md)
- [test-patterns](../08-test-patterns/2-summary.md)
- `pytest-fixtures` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/testing-deep.json` 의 `test-doubles`

## 용어 풀이

- **테스트 더블** — 테스트에서 진짜 협력 객체 대신 넣는 대역 객체의 총칭이다.
- **협력자** — 테스트 대상이 일을 하려고 부르는 다른 객체다.
- **격리** — 테스트 대상을 진짜 협력자에게서 떼어 내 그것만 시험하는 것이다.
- **간접 입력** — 인자가 아니라 협력자의 반환값으로 들어오는 값이다.
- **부수 효과** — 반환값 말고 바깥 상태를 바꾸는 일이다.
- **Dummy** — 자리만 채우고 불리지 않는 객체다.
- **Stub** — 미리 정한 값을 돌려주는 대역이다.
- **Mock** — 호출을 기록하고 그 호출을 검증받는 대역이다.
- **Spy** — 진짜를 실행하면서 호출을 기록하는 대역이다.
- **Fake** — 단순화된 실제 구현이다.
- **상태 검증** — 결과나 바뀐 상태로 판정하는 방식이다.
- **행동 검증** — 주고받은 호출로 판정하는 방식이다.
- **인메모리 구현** — 메모리 안의 자료구조로 저장소를 흉내 낸 것이다.
- **`MagicMock`** — `unittest.mock` 의 만능 대역 클래스다.
- **`return_value`** — Mock 을 불렀을 때 돌려줄 값이다.
- **`wraps`** — 호출을 넘길 진짜 객체를 정하는 `MagicMock` 인자다.
- **`call_count`** — 불린 횟수다.
- **`assert_called_once_with`** — 정확히 한 번, 그 인자로 불렸는지 검사하는 메서드다.
- **`pytest.raises`** — 블록 안에서 특정 예외가 나는지 검사하는 pytest 도구다.

## 더 들어가면

- 다섯 가지 이름은 Gerard Meszaros 의 책 『xUnit Test Patterns』에서 널리 퍼진 분류로 알려져 있다 (확인 필요).
- `MagicMock(spec=진짜클래스)` 나 `create_autospec` 을 쓰면 진짜에 없는 메서드를 부를 때 오류가 나게 할 수 있다 — 아무 이름이나 받아 주는 `MagicMock` 의 약점을 줄인다 (확인 필요).
- `MagicMock` 은 `assert` 로 시작하는 오타 이름(`assret_called` 등)을 부르면 오류를 내 검사가 조용히 빠지는 것을 막는다 — 막는 이름의 범위는 버전마다 다르다 (확인 필요).
- `MagicMock` 인스턴스는 기본적으로 참으로 평가된다 — 그래서 `return_value` 를 깜빡한 Stub 의 `check_stock(...)` 도 `if not ...` 을 통과할 수 있다 (확인 필요).
- 생성자로 받지 않고 모듈 안에서 직접 만드는 협력자는 `patch` 로 그 이름을 잠시 바꿔치기한다 (확인 필요).
- pytest 는 기본으로 테스트 중 `print` 출력을 붙잡아 두고, `-s` 를 주면 그대로 보여 준다 (확인 필요).
