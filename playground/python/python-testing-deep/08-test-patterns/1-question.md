# python/python-testing-deep/08 — 테스트 패턴 (AAA, Given-When-Then) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 책 두 권과 펜 세 자루를 담으면 (예측)

```python
# 질문용 발췌
cart = ShoppingCart()
cart.add_item("Book", 20000, quantity=2)
cart.add_item("Pen", 3000, quantity=3)
print(cart.item_count(), cart.total())
```

- 두 값은 각각 얼마인가?

### 2. 할인율의 경계값 넷 (예측)
- `apply_discount` 에 `0` · `100` · `150` · `-5` 를 넣으면 각각 예외가 나나 값이 나오나?
- 값이 나올 때 그 값의 자료형은 무엇인가?

### 3. fixture 를 전역 변수로 바꾸면 (예측)

```python
# 질문용 발췌 — fixture 대신 모듈 전역 하나를 공유한다
shared = ShoppingCart()

class TestShared:
    def test_first(self):
        shared.add_item("X", 1000)
        assert shared.item_count() == 1

    def test_second(self):
        assert shared.item_count() == 0
```

- 파일에 적힌 차례대로 돌면 두 테스트는 각각 어떻게 되나?
- `test_second` 만 따로 돌리면 어떻게 되나?

### 4. 예외 검증에서 Act 와 Assert 가 한 칸이 되는 까닭 (왜)
- `test_invalid_discount_raises` 는 왜 `apply_discount(150)` 을 먼저 부르고 다음 줄에서 확인하는 꼴로 쓸 수 없나?

### 5. 네 개념을 한 테스트에 담은 예가 나쁜 까닭 (왜)
- `test_bad_multiple_concepts` 의 첫 `assert` 가 실패하면 나머지 검증은 어떻게 되고, 그것이 왜 문제인가?

### 6. Given-When-Then 은 AAA 와 무엇이 다른가 (경계)
- 두 패턴은 테스트의 칸 나누기에서 다른가, 아니면 어디서 다른가?

### 7. 「하나의 개념」과 「assert 하나」 (경계)
- `test_add_item` 은 `assert` 가 둘인데 「한 테스트, 한 개념」을 어기는가?

### 8. 파일을 `python` 으로 직접 돌리면 (경계)
- `python test_patterns.py` 로 실행하면 테스트 클래스들의 검증이 실행되나?

### 9. fixture 와 FIRST 의 I (연결)
- `TestIsolation` 의 fixture 는 FIRST 원칙 중 어느 글자, 그리고 「좋은 테스트의 조건」 중 어느 항목과 이어지나?

### 10. 장바구니 테스트는 피라미드의 어느 층인가 (연결)
- 이 파일의 테스트들은 테스트 피라미드의 어느 층에 속하고, 그 층을 가장 많이 두는 까닭은 무엇인가?

## 실습

### 실습 1. 장바구니와 네 가지 테스트 패턴 모음

**만들 것** — `ShoppingCart` 클래스를 완성하고, AAA · Given-When-Then · 테스트 격리 · 「하나의 테스트, 하나의 개념」을 보이는 pytest 테스트 클래스 넷을 쓴다.

**준비물** — `pytest` 가 설치돼 있어야 한다(`pip install pytest`).

**요구 조건**

1단계 — 테스트 대상 `ShoppingCart`
1. 새 장바구니는 빈 항목 리스트 `items` 를 가진다.
2. `add_item(name, price, quantity=1)` 은 `{"name", "price", "qty"}` 꼴의 딕셔너리 하나를 `items` 끝에 붙인다.
3. `remove_item(name)` 은 그 이름의 항목을 모두 걸러 낸 새 리스트로 `items` 를 바꾼다.
4. `total()` 은 모든 항목의 가격 × 수량의 합을 돌려준다.
5. `apply_discount(percent)` 는 `percent` 가 0~100 밖이면 메시지 `"할인율은 0~100%"` 의 `ValueError` 를 던지고, 안이면 `total() × (1 - percent/100)` 을 돌려준다.
6. `item_count()` 는 모든 항목의 수량 합을 돌려준다.

2단계 — `TestAAAPattern` (Arrange · Act · Assert 주석으로 칸을 나눈다)
7. `test_add_item` — 책 하나를 담은 뒤 수량 합이 1, 합계가 그 가격인지 본다.
8. `test_apply_discount` — 노트북 하나를 담고 10% 할인한 값이 90% 인지 본다.
9. `test_invalid_discount_raises` — 150% 할인이 `ValueError` 를 내고 메시지에 `"0~100%"` 가 있는지 `pytest.raises` 로 본다.

3단계 — `TestGivenWhenThen` (시나리오 독스트링 + Given · When · Then 주석)
10. `test_empty_cart_has_zero_total` — 빈 장바구니의 합계가 0.
11. `test_multiple_items_total` — 책 2권 · 펜 3자루의 합계가 가격 × 수량의 합.
12. `test_remove_item_from_cart` — A · B 를 담고 A 를 빼면 합계가 B 의 가격, 수량 합이 1.

4단계 — `TestIsolation`
13. 클래스 안에 테스트마다 새 `ShoppingCart` 를 돌려주는 fixture `cart` 를 둔다.
14. `test_first` 는 그 `cart` 에 하나를 담고 수량 합이 1 인지, `test_second` 는 받은 `cart` 의 수량 합이 0 인지 본다.

5단계 — `TestOneConcept`
15. 나쁜 예 `test_bad_multiple_concepts` 하나에 추가 · 합계 · 50% 할인 · 제거 검증을 몰아 둔다.
16. 좋은 예로 추가(`test_add_increases_count`) · 합계(`test_total_sums_prices`, 수량 2) · 할인(`test_discount_reduces_total`, 50%) 을 각각 따로 검증한다.

6단계 — 요약표
17. 파일을 직접 실행했을 때만 요약표를 찍는 `__main__` 블록을 남긴다(시작 코드에 채워져 있다).

**시작 코드**

```python
import pytest
from unittest.mock import MagicMock  # 비교용 임포트 — 쓰지 않는다


class ShoppingCart:
    def __init__(self):
        pass  # TODO: 빈 항목 리스트

    def add_item(self, name, price, quantity=1):
        pass  # TODO: name · price · qty 딕셔너리를 붙인다

    def remove_item(self, name):
        pass  # TODO: 같은 이름을 모두 걸러 낸다

    def total(self):
        pass  # TODO: 가격 × 수량의 합

    def apply_discount(self, percent):
        pass  # TODO: 0~100 검사 → ValueError / 할인된 합계

    def item_count(self):
        pass  # TODO: 수량의 합


class TestAAAPattern:
    def test_add_item(self):
        # Arrange
        # Act
        # Assert
        ...  # TODO

    def test_apply_discount(self):
        ...  # TODO

    def test_invalid_discount_raises(self):
        # Arrange
        # Act & Assert
        ...  # TODO: pytest.raises


class TestGivenWhenThen:
    def test_empty_cart_has_zero_total(self):
        """Given 빈 장바구니가 있을 때, When 합계를 조회하면, Then 0이다"""
        ...  # TODO

    def test_multiple_items_total(self):
        """Given 여러 상품이 담긴 장바구니가 있을 때, When 합계를 조회하면, Then 모든 상품의 합이다"""
        ...  # TODO

    def test_remove_item_from_cart(self):
        """Given 상품이 담긴 장바구니에서, When 상품을 제거하면, Then 합계가 줄어든다"""
        ...  # TODO


class TestIsolation:
    """각 테스트는 독립적이어야 한다"""

    # TODO: fixture cart

    def test_first(self, cart):
        ...  # TODO

    def test_second(self, cart):
        ...  # TODO


class TestOneConcept:
    """나쁜 예: 하나의 테스트에서 여러 개념을 테스트"""
    def test_bad_multiple_concepts(self):
        ...  # TODO: 추가 · 합계 · 할인 · 제거를 한 함수에

    """좋은 예: 각 개념을 분리"""
    def test_add_increases_count(self):
        ...  # TODO

    def test_total_sums_prices(self):
        ...  # TODO

    def test_discount_reduces_total(self):
        ...  # TODO


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

**확인 방법** — 파일 이름을 `test_patterns.py` 로 두고 `pytest test_patterns.py -v` 로 돌려 테스트 13개가 모두 통과하는지 본다.
`python test_patterns.py` 로 돌리면 요약표만 찍히는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
