# python/python-testing-deep/08 — 테스트 패턴 (AAA, Given-When-Then) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 수량 합 5, 합계 49000

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`item_count()` 는 `2 + 3 = 5`, `total()` 은 `20000 × 2 + 3000 × 3 = 40000 + 9000 = 49000` 이다.
`print` 는 두 값을 빈칸으로 이어 `5 49000` 꼴로 찍는다고 추론한다.

**왜 그런가**

`item_count` 는 담긴 항목의 줄 수(2)가 아니라 각 항목의 `qty` 를 더한다.
`total` 은 `price * qty` 를 더한다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 0 과 100 은 값, 150 과 -5 는 `ValueError` — 값은 `float`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `0` → 예외 없음, 합계 그대로(`float`).
- `100` → 예외 없음, `0.0`.
- `150` → `ValueError("할인율은 0~100%")`.
- `-5` → `ValueError("할인율은 0~100%")`.

**왜 그런가**

검사가 `0 <= percent <= 100` 이라 양 끝이 포함된다.
`percent / 100` 이 나눗셈이므로 `1 - percent/100` 이 `float` 이고, 곱한 결과도 `float` 이다.
근거: 2-summary 「동작 방식 (1)」.

### 3. 차례대로면 `test_second` 가 실패하고, 혼자면 통과한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 차례대로: `test_first` 통과, `test_second` 는 `shared` 에 `X` 가 남아 있어 `item_count()` 가 1 이라 실패.
- `test_second` 만: 빈 `shared` 라 통과.

**왜 그런가**

전역 객체 하나를 두 테스트가 나눠 쓰므로 앞 테스트의 변경이 뒤 테스트에 남는다.
결과가 실행 순서에 따라 바뀌는 것이 바로 격리가 깨진 증상이다.
fixture 를 쓰면 테스트마다 새 객체를 받아 이 문제가 없다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 3」.

### 4. 예외가 호출하는 순간 흐름을 끊기 때문이다

`apply_discount(150)` 을 그냥 부르면 그 자리에서 `ValueError` 가 나 테스트가 실패로 끝나고, 다음 줄의 확인까지 가지 못한다.
그래서 「이 블록 안에서 예외가 나야 통과」라는 검증 틀(`with pytest.raises`)을 먼저 열고 그 안에서 호출한다.
결과적으로 Act 와 Assert 가 한 칸에 겹친다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 4」.

### 5. 나머지는 실행되지 않고, 어디가 깨졌는지 이름으로 알 수 없다

`assert` 가 실패하면 테스트 함수는 그 자리에서 멈추므로 합계 · 할인 · 제거 검증은 돌지 않는다.
보고서에는 「`test_bad_multiple_concepts` 실패」만 남아 네 개념 중 무엇이 문제인지 바로 모르고, 다른 결함이 있어도 가려진다.
개념별로 나누면 실패한 테스트의 이름이 원인을 말해 준다.
근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 2」.

### 6. 칸 나누기는 같고, 말하는 관점이 다르다

Given=Arrange, When=Act, Then=Assert 로 세 칸이 그대로 대응한다.
다른 점은 어휘다 — Given-When-Then 은 코드 동작 대신 「상황 → 행동 → 결과」라는 비즈니스 시나리오로 서술하고(BDD 스타일), 예제처럼 독스트링에 시나리오 문장을 적는다.
근거: 2-summary 「동작 방식 (4)」.

### 7. 어기지 않는다 — 두 `assert` 가 「추가」라는 한 개념의 결과다

「하나의 개념」은 `assert` 의 개수가 아니라 검증하는 동작의 개수다.
`test_add_item` 의 Act 는 `add_item` 한 번이고, 수량 합과 합계는 둘 다 그 추가의 결과를 본다.
`test_bad_multiple_concepts` 처럼 동작(추가 · 할인 · 제거)이 여럿 섞일 때가 문제다.
근거: 2-summary 「동작 방식 (6)」 마지막 불릿.

### 8. 실행되지 않는다 — 요약표만 찍힌다

`python` 으로 직접 돌리면 클래스와 함수가 정의만 되고, `if __name__ == '__main__':` 블록만 실행된다.
테스트 메서드를 찾아 부르는 것은 pytest 의 일이다.
거꾸로 pytest 로 돌리면 `__name__` 이 `'__main__'` 이 아니라 요약표 블록이 돌지 않는다.
근거: 2-summary 「동작 방식 (7)」 마지막 세 불릿, 「구현 세부사항 대 언어 보장」.

### 9. FIRST 의 I(Independent), 조건 4 「실행 순서에 무관」

fixture 가 테스트마다 새 `ShoppingCart` 를 주므로 각 테스트가 다른 테스트와 독립이다(Independent).
그래서 어떤 순서로 돌려도 같은 결과가 나온다 — 좋은 테스트의 조건 ④ 「실행 순서에 무관」이다.
같은 결과가 늘 되풀이되니 R(Repeatable)에도 기여한다.
근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (7)」.

### 10. 단위 테스트 — 빠르고 격리돼 있어서

장바구니 클래스 하나를 DB · 네트워크 없이 시험하므로 피라미드 맨 아래 단위 테스트다.
단위 테스트는 빠르고 격리돼 있어 많이 돌려도 부담이 적으므로 가장 많이 둔다.
통합 · E2E 는 위로 갈수록 느리지만 모듈 간 연동이나 사용자 관점을 보므로 적게 둔다.
근거: 2-summary 「동작 방식 (7)」.

## 실습 정답

### 실습 1. 장바구니와 네 가지 테스트 패턴 모음

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 빈 항목 리스트 | `ShoppingCart.__init__` 의 `self.items = []` |
| 2. 항목 붙이기 | `add_item` 의 `self.items.append({...})` |
| 3. 같은 이름 모두 걸러 내기 | `remove_item` 의 리스트 컴프리헨션 |
| 4. 가격 × 수량 합 | `total` 의 `sum(item["price"] * item["qty"] ...)` |
| 5. 범위 검사 · 할인 | `apply_discount` 의 `if not 0 <= percent <= 100: raise ValueError(...)` |
| 6. 수량 합 | `item_count` 의 `sum(item["qty"] ...)` |
| 7~9. AAA | `TestAAAPattern` 의 `test_add_item` · `test_apply_discount` · `test_invalid_discount_raises` |
| 9. 예외 검증 | `with pytest.raises(ValueError, match="0~100%")` |
| 10~12. Given-When-Then | `TestGivenWhenThen` 의 세 메서드와 독스트링 |
| 13. 테스트마다 새 장바구니 | `TestIsolation.cart` (`@pytest.fixture`) |
| 14. 격리 확인 | `test_first` · `test_second` |
| 15. 나쁜 예 | `TestOneConcept.test_bad_multiple_concepts` |
| 16. 좋은 예 | `test_add_increases_count` · `test_total_sums_prices` · `test_discount_reduces_total` |
| 17. 요약표 | `if __name__ == '__main__':` 블록 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-testing-deep/reference/test-patterns.py`

```python
# [테스팅 심화] 테스트 패턴 (AAA, Given-When-Then)
# 설명: AAA, Given-When-Then, 테스트 격리, 테스트 피라미드 등 테스트 설계 패턴
# 팁: AAA 패턴은 테스트의 가독성을 높이고, 각 단계가 명확히 구분된다. 하나의 테스트에서 하나의 개념만 검증하면 실패 원인을 빠르게 파악할 수 있다. 테스트 격리는 fixture로 보장하며, 전역 상태 변경을 피한다. 테스트 피라미드에 따라 단위 테스트를 가장 많이 작성한다.

# pytest: 테스트 프레임워크
import pytest
# MagicMock: (현재 미사용이지만 패턴 비교용 임포트 유지)
from unittest.mock import MagicMock

# === 테스트 대상 ===
# ShoppingCart: 패턴 시연용 단순 도메인 객체
class ShoppingCart:
    def __init__(self):
        # 장바구니 항목 리스트
        self.items = []

    # 항목 추가
    def add_item(self, name, price, quantity=1):
        self.items.append({"name": name, "price": price, "qty": quantity})

    # 이름으로 항목 제거 (필터링)
    def remove_item(self, name):
        self.items = [item for item in self.items if item["name"] != name]

    # 합계 계산
    def total(self):
        return sum(item["price"] * item["qty"] for item in self.items)

    # 할인 적용 (도메인 규칙: 0~100%)
    def apply_discount(self, percent):
        if not 0 <= percent <= 100:
            raise ValueError("할인율은 0~100%")
        return self.total() * (1 - percent / 100)

    # 총 수량
    def item_count(self):
        return sum(item["qty"] for item in self.items)

# === 패턴 1: AAA (Arrange-Act-Assert) ===
# AAA: 가장 일반적인 테스트 구조 - 3단계 명확히 구분
class TestAAAPattern:
    def test_add_item(self):
        # Arrange (준비) - 테스트 대상과 입력 준비
        cart = ShoppingCart()

        # Act (실행) - 검증할 동작 1회 실행
        cart.add_item("Python Book", 30000)

        # Assert (검증) - 결과 확인
        assert cart.item_count() == 1
        assert cart.total() == 30000

    def test_apply_discount(self):
        # Arrange - 사전 데이터 세팅
        cart = ShoppingCart()
        cart.add_item("Laptop", 1000000)

        # Act
        discounted = cart.apply_discount(10)

        # Assert
        assert discounted == 900000

    def test_invalid_discount_raises(self):
        # Arrange
        cart = ShoppingCart()
        cart.add_item("Item", 10000)

        # Act & Assert - 예외는 with 블록 안에서 검증
        with pytest.raises(ValueError, match="0~100%"):
            cart.apply_discount(150)

# === 패턴 2: Given-When-Then (BDD 스타일) ===
# Given-When-Then: AAA와 동일하지만 비즈니스 시나리오 표현
class TestGivenWhenThen:
    def test_empty_cart_has_zero_total(self):
        """Given 빈 장바구니가 있을 때, When 합계를 조회하면, Then 0이다"""
        # Given - 초기 상황
        cart = ShoppingCart()

        # When - 행위
        total = cart.total()

        # Then - 기대 결과
        assert total == 0

    def test_multiple_items_total(self):
        """Given 여러 상품이 담긴 장바구니가 있을 때, When 합계를 조회하면, Then 모든 상품의 합이다"""
        # Given - 여러 상품 추가
        cart = ShoppingCart()
        cart.add_item("Book", 20000, quantity=2)
        cart.add_item("Pen", 3000, quantity=3)

        # When
        total = cart.total()

        # Then - 가격×수량의 합
        assert total == 20000 * 2 + 3000 * 3

    def test_remove_item_from_cart(self):
        """Given 상품이 담긴 장바구니에서, When 상품을 제거하면, Then 합계가 줄어든다"""
        # Given
        cart = ShoppingCart()
        cart.add_item("A", 10000)
        cart.add_item("B", 20000)

        # When
        cart.remove_item("A")

        # Then
        assert cart.total() == 20000
        assert cart.item_count() == 1

# === 테스트 격리 ===
# 격리: 각 테스트는 독립적으로 실행되어야 함 (실행 순서 무관)
class TestIsolation:
    """각 테스트는 독립적이어야 한다"""

    # fixture로 격리 보장 - 매 테스트마다 새 객체
    @pytest.fixture
    def cart(self):
        """각 테스트마다 새 장바구니 (격리 보장)"""
        return ShoppingCart()

    def test_first(self, cart):
        cart.add_item("X", 1000)
        assert cart.item_count() == 1

    # test_first에서 추가한 항목은 영향 없음 - 새 cart 인스턴스
    def test_second(self, cart):  # 이전 테스트의 영향 없음
        assert cart.item_count() == 0

# === 하나의 테스트, 하나의 개념 ===
# 한 테스트에 한 개념: 실패 시 원인 즉시 파악
class TestOneConcept:
    """나쁜 예: 하나의 테스트에서 여러 개념을 테스트"""
    # 안티 패턴: 4개 동작이 한 테스트에 - 실패 시 어디가 문제인지 불명확
    def test_bad_multiple_concepts(self):
        cart = ShoppingCart()
        # 추가 테스트
        cart.add_item("A", 1000)
        assert cart.item_count() == 1
        # 합계 테스트
        assert cart.total() == 1000
        # 할인 테스트
        assert cart.apply_discount(50) == 500
        # 제거 테스트
        cart.remove_item("A")
        assert cart.item_count() == 0

    """좋은 예: 각 개념을 분리"""
    # 추가 동작만 검증
    def test_add_increases_count(self):
        cart = ShoppingCart()
        cart.add_item("A", 1000)
        assert cart.item_count() == 1

    # 합계 동작만 검증
    def test_total_sums_prices(self):
        cart = ShoppingCart()
        cart.add_item("A", 1000, 2)
        assert cart.total() == 2000

    # 할인 동작만 검증
    def test_discount_reduces_total(self):
        cart = ShoppingCart()
        cart.add_item("A", 1000)
        assert cart.apply_discount(50) == 500

# 실행: pytest test_patterns.py -v

if __name__ == '__main__':
    print("=== 테스트 패턴 ===")
    print("AAA:              Arrange(준비) → Act(실행) → Assert(검증)")
    print("Given-When-Then:  상황 → 행동 → 결과 (BDD 스타일)")
    print()
    print("=== FIRST 원칙 ===")
    print("Fast:        빠르게 실행")
    print("Independent: 테스트 간 독립")
    print("Repeatable:  환경에 무관하게 동일 결과")
    print("Self-validating: 자동으로 성공/실패 판단")
    print("Timely:      코드와 함께 작성")
    print()
    print("=== 테스트 피라미드 ===")
    print("        /  E2E  \\        ← 적게, 느리지만 사용자 관점")
    print("       /  통합   \\       ← 중간, 모듈 간 연동")
    print("      / 단위 테스트\\      ← 많이, 빠르고 격리됨")
    print()
    print("=== 좋은 테스트의 조건 ===")
    print("1. 테스트당 하나의 개념만 검증")
    print("2. 테스트 이름이 의도를 설명")
    print("3. 외부 의존성 격리 (DB, 네트워크)")
    print("4. 실행 순서에 무관")
    print("5. 실패 시 원인을 즉시 파악 가능")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- 테스트를 쓰기 전에 대상의 의미를 확정한다 — `item_count` 는 수량 합, `apply_discount` 는 값을 돌려줄 뿐 장바구니를 바꾸지 않는다.
- AAA · Given-When-Then 은 문법이 아니라 주석과 빈 줄로 칸을 드러내는 배치 규약이다.
- 예외 검증은 `with pytest.raises` 블록 **안**에서 호출해야 한다.
- fixture 의 이름과 테스트 매개변수 이름이 같아야 주입된다 — 이것이 `test_second` 가 빈 장바구니를 받는 까닭이다.
- 나쁜 예도 지금은 통과하지만, 하나가 깨지는 순간 원인이 흐려진다는 점을 좋은 예와 나란히 두어 비교한다.
- `test_apply_discount` 는 `float` 을 `==` 로 비교한다 — 이 값에서는 맞는다고 추론하지만 일반적으로는 조심해야 한다. (원본에 근거 없음 — 추론)

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
