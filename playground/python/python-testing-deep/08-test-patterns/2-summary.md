# python/python-testing-deep/08 — 테스트 패턴 (AAA, Given-When-Then) — 정리 (힌트)

> 출처 — study-site 항목 `python/test-patterns`(항목 데이터 `data/python/testing-deep.json`) · 정답 코드 study-practice `python/python-testing-deep/reference/test-patterns.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**테스트 하나는 「요리 시연 한 번」이다.**
재료를 늘어놓고(준비), 딱 한 가지 요리 동작을 하고(실행), 완성된 접시를 확인한다(검증).
시연마다 새 도마와 새 재료를 쓴다.
앞 시연에서 남은 양파가 다음 시연에 섞이면 맛이 왜 이상한지 아무도 모른다.
테스트도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 재료 늘어놓기 | Arrange / Given — 테스트 대상 객체와 입력을 만든다 |
| 요리 동작 한 번 | Act / When — 검증할 동작을 한 번 부른다 |
| 접시 확인 | Assert / Then — `assert` 로 결과를 확인한다 |
| 시연마다 새 도마 | 테스트 격리 — `fixture` 가 테스트마다 새 객체를 준다 |
| 시연 하나에 요리 하나 | 하나의 테스트, 하나의 개념 |

```text
 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 │  Arrange    │ →  │    Act      │ →  │   Assert    │
 │  (Given)    │    │   (When)    │    │   (Then)    │
 │ cart 만들기  │    │ add_item()  │    │ assert ...  │
 └─────────────┘    └─────────────┘    └─────────────┘
       테스트 하나 = 이 세 칸 한 벌
```

## 이 주제가 답하려는 질문

1. 테스트 함수 안의 줄들을 어떤 차례로 놓아야 읽기 쉽고 실패 원인이 잘 드러나나?
2. 테스트끼리 서로 영향을 주지 않게 하려면 무엇을 써야 하나?
3. 한 테스트에 무엇을 얼마나 담아야 하나?
4. 단위 · 통합 · E2E 테스트를 어떤 비율로 쓰나?

## 동작 방식

### (1) 테스트 대상 — `ShoppingCart`

**언제 쓰나** — 패턴을 보이기 위한 단순한 도메인 객체다.
패턴을 익히기 전에 대상이 무엇을 하는지부터 정확히 알아야 기대값을 맞게 쓸 수 있다.

```text
add_item("Book", 20000, quantity=2)
  → items 에 {"name": "Book", "price": 20000, "qty": 2} 하나가 붙는다

item_count()        → 모든 항목의 qty 를 더한다 (항목 개수가 아니다)
total()             → 모든 항목의 price × qty 를 더한다 (빈 장바구니면 0)
remove_item("A")    → 이름이 "A" 인 항목을 전부 걸러 낸다
apply_discount(p)   → p 가 0~100 밖이면 ValueError
                      안이면 total() × (1 - p/100) 을 돌려준다 (items 는 그대로)
```

- `add_item` 은 `quantity` 를 생략하면 1 로 넣는다.
- `item_count` 는 「담긴 줄 수」가 아니라 「수량의 합」이다.
- `total` 은 빈 목록의 `sum` 이라 항목이 없으면 `0` 이다.
- `remove_item` 은 리스트 컴프리헨션으로 같은 이름을 모두 거른다 — 같은 이름이 둘이면 둘 다 사라진다.
- `apply_discount` 는 `0 <= percent <= 100` 을 검사하므로 0 과 100 은 통과하고, 그 밖은 `ValueError("할인율은 0~100%")` 를 던진다.
- `apply_discount` 는 할인된 값을 **돌려줄 뿐** 장바구니를 바꾸지 않는다.
- `percent / 100` 은 나눗셈이라 반환값은 `float` 이다(예: `900000.0`).

### (2) AAA — Arrange · Act · Assert

**언제 쓰나** — 거의 모든 단위 테스트의 기본 꼴이다.
테스트를 세 단계로 나눠 각 단계가 무엇을 하는지 한눈에 보이게 한다.

```text
def test_apply_discount(self):
    cart = ShoppingCart()               ┐ Arrange: 대상과 사전 데이터
    cart.add_item("Laptop", 1000000)    ┘
    discounted = cart.apply_discount(10)  ─ Act: 검증할 동작 1회
    assert discounted == 900000           ─ Assert: 결과 확인
                     │
                     ▼
     통과 — 1000000 × (1 - 10/100) 이 900000 과 같다
```

- Arrange 에서 장바구니를 만들고 노트북 하나를 담는다.
- Act 에서 검증하려는 동작 `apply_discount(10)` 을 한 번만 부르고 결과를 변수에 받는다.
- Assert 에서 그 변수를 기대값과 비교한다.
- 세 단계 사이에 빈 줄과 주석을 두면 읽는 사람이 「무엇을 시험하는가(Act)」를 바로 찾는다.

> **AAA** — Arrange(준비) · Act(실행) · Assert(검증) 세 단계로 테스트를 짜는 패턴.\
> 예: 장바구니 만들기 → 상품 담기 → 수량이 1 인지 확인.

### (3) 예외를 검증할 때 — Act 와 Assert 가 한 칸에

**언제 쓰나** — 「이 입력이면 예외가 나야 한다」를 시험할 때.

```text
with pytest.raises(ValueError, match="0~100%"):   ─ Assert 의 틀을 먼저 연다
    cart.apply_discount(150)                       ─ 그 안에서 Act
                     │
                     ▼
  ValueError 가 나고 메시지에 "0~100%" 가 있으면 → 통과
  예외가 안 나면 → 실패
```

- `pytest.raises` 는 블록 안에서 지정한 예외가 **나야** 통과한다.
- 예외는 호출하는 순간 함수 흐름을 끊으므로 「먼저 호출하고 나중에 확인」이 안 된다.
- 그래서 검증의 틀(`with`)을 먼저 열고 그 안에서 실행한다 — 주석도 `# Act & Assert` 로 한 칸에 적는다.
- `match` 는 예외 메시지에 그 문자열(정규식)이 들어 있는지까지 본다.

### (4) Given-When-Then — 같은 구조, 다른 말

**언제 쓰나** — 테스트를 비즈니스 시나리오 문장처럼 읽히게 하고 싶을 때(BDD 스타일).

```text
"""Given 상품이 담긴 장바구니에서,      ← 상황
   When 상품을 제거하면,               ← 행동
   Then 합계가 줄어든다"""              ← 결과
        │
        ▼
# Given  cart.add_item("A", 10000); cart.add_item("B", 20000)
# When   cart.remove_item("A")
# Then   assert cart.total() == 20000
```

- 독스트링에 시나리오를 한 문장으로 쓴다.
- 본문은 `# Given` · `# When` · `# Then` 주석으로 나눈다.
- 칸 나누기는 AAA 와 똑같다 — Given=Arrange, When=Act, Then=Assert.
- 다른 점은 어휘다: 코드 동작이 아니라 「사용자 관점의 상황 → 행동 → 결과」로 말한다.

> **Given-When-Then** — 상황(Given) → 행동(When) → 결과(Then) 로 테스트를 서술하는 BDD 스타일 패턴.\
> 예: 빈 장바구니가 있을 때 → 합계를 조회하면 → 0 이다.

> **BDD** — 행위 주도 개발. 테스트를 비즈니스 행위 시나리오로 표현하는 방식.\
> 예: 「Given … When … Then …」 문장으로 테스트 이름이나 독스트링을 쓴다.

### (5) 테스트 격리 — fixture 가 매번 새 객체를 준다

**언제 쓰나** — 여러 테스트가 같은 준비물을 쓰면서도 서로 영향을 주면 안 될 때.

```text
@pytest.fixture
def cart(self): return ShoppingCart()

test_first(cart)   ← 새 ShoppingCart #1 → X 추가 → count 1 ✔
test_second(cart)  ← 새 ShoppingCart #2 → 비어 있음 → count 0 ✔
                     (#1 에 넣은 X 는 여기 없다)
```

- 테스트 함수의 매개변수 이름 `cart` 가 같은 이름의 fixture 를 가리킨다.
- pytest 는 테스트마다 fixture 함수를 새로 불러 그 반환값을 넘긴다(기본 범위가 테스트 하나다).
- 그래서 `test_first` 가 담은 `X` 는 `test_second` 의 장바구니에 없다.
- 만약 장바구니를 모듈 전역 변수 하나로 두고 함께 썼다면, `test_first` 다음에 돈 `test_second` 는 `1` 을 보고 실패한다 — 그리고 순서를 바꾸면 통과한다.
- 이것이 「전역 상태 변경을 피한다」의 뜻이다: 결과가 실행 순서에 따라 달라지면 안 된다.

> **fixture** — pytest 가 테스트에 준비물을 넣어 주는 함수. `@pytest.fixture` 를 붙인다.\
> 예: `def cart(self): return ShoppingCart()` 를 두면 `test_first(self, cart)` 가 새 장바구니를 받는다.

> **테스트 격리** — 각 테스트가 다른 테스트의 결과나 순서와 무관하게 같은 결과를 내는 성질.\
> 예: `test_second` 만 돌려도, 다른 테스트 뒤에 돌려도 통과한다.

### (6) 하나의 테스트, 하나의 개념

**언제 쓰나** — 테스트를 쪼갤지 합칠지 고민될 때 늘.

```text
나쁜 예 test_bad_multiple_concepts
  추가 assert → 합계 assert → 할인 assert → 제거 assert
       ✘ 여기서 실패하면
       └─ 뒤의 세 assert 는 실행조차 안 된다
          보고서: "test_bad_multiple_concepts 실패" — 무엇이 문제인지 모름

좋은 예
  test_add_increases_count     ✘ ← 추가가 깨졌다고 이름이 말해 준다
  test_total_sums_prices       ✔
  test_discount_reduces_total  ✔
```

- `assert` 가 하나 실패하면 그 테스트 함수는 거기서 멈춘다.
- 네 개념을 한 함수에 몰면 첫 실패가 나머지를 가려서, 몇 개가 깨졌는지조차 모른다.
- 개념마다 테스트를 나누면 실패한 테스트의 **이름**이 곧 원인이다.
- 「하나의 개념」은 「`assert` 하나」와 다르다 — `test_add_item` 은 `item_count` 와 `total` 을 함께 보지만 「추가」라는 한 개념의 결과다.

### (7) 큰 그림 — FIRST · 테스트 피라미드 · 좋은 테스트의 조건 · 두 가지 실행

**언제 쓰나** — 테스트 스위트 전체를 설계하거나 리뷰할 때.

```text
FIRST                          테스트 피라미드
F Fast       빠르게 실행              /  E2E  \     적게 · 느림 · 사용자 관점
I Independent 테스트 간 독립          /  통합   \    중간 · 모듈 간 연동
R Repeatable 환경 무관 동일 결과     / 단위 테스트\   많이 · 빠름 · 격리됨
S Self-validating 자동 판정
T Timely     코드와 함께 작성
```

- FIRST 의 I(Independent)는 (5) 격리, S(Self-validating)는 `assert` 가 사람 눈 없이 성공/실패를 가르는 것이다.
- 피라미드 아래일수록 많이 쓴다 — 단위 테스트는 빠르고 격리돼 있어 많이 돌려도 부담이 적다.
- 위로 갈수록 느리고 깨지기 쉽지만 실제 사용자 흐름을 본다 — 그래서 적게 둔다.
- 원본이 꼽는 좋은 테스트의 조건은 다섯이다: ① 테스트당 하나의 개념 ② 이름이 의도를 설명 ③ 외부 의존성(DB · 네트워크) 격리 ④ 실행 순서에 무관 ⑤ 실패 시 원인을 즉시 파악.
- 예제 파일은 두 방식으로 쓴다: `pytest test_patterns.py -v` 로 돌리면 `Test` 로 시작하는 클래스의 `test_` 메서드가 테스트로 돈다.
- `python` 으로 파일을 직접 돌리면 `if __name__ == '__main__':` 블록만 실행되어 위 요약표를 찍을 뿐 테스트는 돌지 않는다.
- pytest 가 파일을 불러올 때는 `__name__` 이 `'__main__'` 이 아니라 그 블록은 실행되지 않는다.

> **테스트 피라미드** — 단위 테스트를 가장 많이, 통합을 중간, E2E 를 가장 적게 두는 비율 지침.\
> 예: 장바구니 계산은 단위 테스트로, 결제 화면 전체 흐름은 E2E 몇 개로.

## 문법 — 형태와 규칙

```python
import pytest

class Counter:
    def __init__(self): self.n = 0
    def inc(self): self.n += 1

class TestCounter:
    @pytest.fixture
    def counter(self):
        return Counter()           # 테스트마다 새로

    def test_inc_adds_one(self, counter):
        # Arrange — fixture 가 준비했다
        # Act
        counter.inc()
        # Assert
        assert counter.n == 1

    def test_starts_at_zero(self, counter):
        """Given 새 카운터 When 아무것도 안 하면 Then 0"""
        assert counter.n == 0
```

- 테스트 클래스 이름은 `Test` 로, 테스트 메서드 이름은 `test_` 로 시작한다 — pytest 는 이 이름으로 테스트를 찾는다.
- 검증은 평범한 `assert 식` 이다.
- 예외 검증은 `with pytest.raises(예외형, match="메시지 일부"):` 블록 안에서 호출한다.
- fixture 는 `@pytest.fixture` 를 붙인 함수이고, 테스트의 매개변수 이름으로 받는다.
- AAA / Given-When-Then 은 문법이 아니라 **배치 규약**이다 — 주석과 빈 줄로 칸을 드러낸다.
- 테스트 이름은 의도를 말하게 짓는다: `test_empty_cart_has_zero_total` 처럼 「상황 + 기대」.

## 어디서 틀리나

### 1. 칸이 섞인 테스트
Arrange 중간에 `assert` 를 끼우거나 Act 를 여러 번 하면 「무엇을 시험하는가」가 흐려진다.
AAA 의 장점은 각 단계가 명확히 구분된다는 것이다 — 칸을 섞으면 그 장점이 사라진다.

### 2. 한 테스트에 여러 개념
`test_bad_multiple_concepts` 처럼 추가 · 합계 · 할인 · 제거를 한 함수에 담으면, 하나가 깨질 때 어디가 문제인지 바로 모른다.
첫 `assert` 실패 뒤의 검증은 실행되지 않아 다른 결함도 가려진다.

### 3. 전역 상태를 공유하는 테스트
테스트끼리 객체나 전역 변수를 나눠 쓰면 결과가 실행 순서에 따라 바뀐다.
격리는 fixture 로 보장하고 전역 상태 변경을 피한다.

### 4. 예외 검증을 `with` 밖에서 하는 실수
`cart.apply_discount(150)` 을 `with pytest.raises` 블록 **밖**에서 부르면 예외가 그대로 테스트를 깨뜨린다.
호출은 반드시 블록 안에 둔다.

### 5. 대상의 의미를 잘못 알고 쓴 기대값
`item_count` 는 수량의 합이지 항목 개수가 아니고, `apply_discount` 는 장바구니를 바꾸지 않는다.
대상의 동작을 잘못 알면 테스트가 틀린 기대를 「검증」하게 된다.

### 6. 실수(`float`)를 `==` 로 비교하기
`apply_discount` 는 `float` 을 돌려준다.
`1000000 * (1 - 10/100) == 900000` 은 이 값에서는 맞아떨어진다고 추론하지만 (확인 필요), 실수 연산은 일반적으로 반올림 오차가 있어 다른 값에서는 `==` 가 어긋날 수 있다. (원본에 근거 없음 — 추론)

### 7. 쓰지 않는 임포트와 독스트링 아닌 문자열
원본은 `MagicMock` 을 임포트하지만 쓰지 않는다(비교용으로 남겨 둔 것).
`TestOneConcept` 안의 두 번째 `"""좋은 예: 각 개념을 분리"""` 는 클래스 몸통 가운데에 놓인 문자열 식일 뿐 독스트링이 아니다 — 클래스 독스트링은 첫 문자열 하나뿐이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `Test*` 클래스의 `test_*` 메서드를 테스트로 모은다 | pytest 의 기본 수집 규칙(설정으로 바꿀 수 있다) |
| fixture 는 테스트마다 새로 불린다 | pytest — 기본 범위가 `function` 일 때. 범위를 넓히면 공유된다 |
| `pytest.raises(..., match=...)` 가 메시지를 검사한다 | pytest — 메시지를 정규식으로 검색 |
| 빈 목록의 `sum` 은 `0` | Python 언어(내장 함수) |
| `__main__` 블록은 직접 실행할 때만 돈다 | Python 언어(`__name__` 규칙) |
| `1000000 * (1 - 10/100)` 이 정확히 `900000.0` | 언어가 아니라 부동소수점 산술(CPython 은 C `double`) — 값마다 다르다 (확인 필요) |
| 한 파일 안의 테스트가 정의 순서대로 돈다 | pytest 의 현재 동작일 뿐 — 테스트는 여기에 기대면 안 된다(Independent) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 코드 동작 하나를 시험 | AAA 세 칸 | 칸 없이 줄을 뒤섞기 |
| 기획자와 함께 읽을 시나리오 | Given-When-Then 독스트링 | 구현 용어만으로 된 이름 |
| 여러 테스트가 같은 준비물 | `@pytest.fixture` | 모듈 전역 객체 공유 |
| 예외가 나야 하는 입력 | `with pytest.raises(...)` | `try/except` 로 직접 잡아 넘기기 |
| 기능 넷을 검증 | 테스트 넷 | 테스트 하나에 넷 |
| 스위트 구성 | 단위 테스트를 가장 많이 | E2E 위주 |

## 핵심 문장

1. **테스트 하나는 준비 → 실행 → 검증 세 칸이다** — AAA 와 Given-When-Then 은 같은 칸을 다른 말로 부른다.
2. **예외 검증에서는 Act 와 Assert 가 `with pytest.raises` 한 칸으로 합쳐진다.**
3. **테스트는 서로 독립이어야 한다** — fixture 로 테스트마다 새 객체를 주고 전역 상태를 피한다.
4. **한 테스트에 한 개념** — 실패한 테스트의 이름이 곧 원인이 된다.
5. **피라미드 아래(단위)를 가장 많이** — 빠르고 격리돼 있기 때문이다.

## 관련 자료

- [test-doubles](../07-test-doubles/2-summary.md)
- `pytest-fixtures` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `integration-test` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `tdd-practice` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/testing-deep.json` 의 `test-patterns`

## 용어 풀이

- **AAA** — Arrange · Act · Assert 세 단계 테스트 구조.
- **Arrange** — 테스트 대상과 입력을 준비하는 단계.
- **Act** — 검증할 동작을 한 번 실행하는 단계.
- **Assert** — 결과를 기대값과 비교하는 단계.
- **Given-When-Then** — 상황 · 행동 · 결과로 서술하는 BDD 스타일 테스트 구조.
- **BDD** — 행위 주도 개발. 테스트를 비즈니스 행위로 표현하는 방식.
- **fixture** — pytest 가 테스트에 준비물을 넣어 주는 함수.
- **테스트 격리** — 테스트끼리 서로 영향이 없어 순서와 무관하게 같은 결과를 내는 성질.
- **FIRST** — Fast · Independent · Repeatable · Self-validating · Timely, 좋은 단위 테스트의 다섯 성질.
- **테스트 피라미드** — 단위 > 통합 > E2E 순으로 수를 두는 지침.
- **단위 테스트** — 한 함수 · 클래스를 외부 의존 없이 시험하는 테스트.
- **통합 테스트** — 여러 모듈이 함께 동작하는지 보는 테스트.
- **E2E 테스트** — 사용자 관점에서 시스템 끝에서 끝까지 보는 테스트.
- **`pytest.raises`** — 블록 안에서 지정한 예외가 나는지 검증하는 컨텍스트 매니저.
- **안티 패턴** — 흔히 쓰이지만 피해야 할 설계.

## 더 들어가면

- 실수 비교에는 `pytest.approx` 를 쓸 수 있다 — `assert discounted == pytest.approx(900000)`. (확인 필요)
- 여러 입력을 같은 AAA 틀로 시험하려면 `@pytest.mark.parametrize` 로 한 함수를 입력마다 따로 돌릴 수 있다 — 실패도 입력별로 따로 보고된다. (확인 필요)
- fixture 의 범위는 `scope="class"` · `"module"` · `"session"` 으로 넓힐 수 있는데, 넓힐수록 격리가 약해진다. (확인 필요)
- `pytest -p no:randomly` 같은 플러그인 이름이나 `pytest-randomly` 는 테스트 순서를 섞어 순서 의존을 찾아낸다고 알려져 있다. (확인 필요)
- 외부 의존성(DB · 네트워크) 격리에는 원본이 임포트만 한 `MagicMock` 같은 대역 객체를 쓴다. (확인 필요)
