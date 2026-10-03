# testing/12-test-smells-and-xunit-patterns — 정답

## 정답

### 1. 스멜의 비용과 세 갈래

- 스멜이 있는 테스트는 실패했을 때 "무엇이 왜 틀렸나"를 알아내는 데 시간이 든다. 메시지가 모호하거나, 준비가 숨어 있거나, 다른 결함이 첫 실패 뒤에 숨는다.
- xunitpatterns.com "Test Smells" 분류
  - 코드 스멜(읽을 때): Obscure Test, Conditional Test Logic, Hard-to-Test Code, Test Code Duplication, Test Logic in Production.
  - 행동 스멜(돌릴 때): Assertion Roulette, Erratic Test, Fragile Test, Frequent Debugging, Manual Intervention, Slow Tests.
  - 프로젝트 스멜(팀 지표): Buggy Tests, Developers Not Writing Tests, High Test Maintenance Cost, Production Bugs.

### 2. Obscure Test · Mystery Guest · General Fixture

- Obscure Test("difficult to understand the test at a glance")가 스멜이고, Mystery Guest와 General Fixture는 그 **원인**이다.
- Mystery Guest: 준비와 검증의 인과가 테스트 밖에서 일어나 안 보인다. `fixtures/orders.json`을 읽는 것이 이것이다.
- General Fixture: 이 테스트에 필요한 것보다 큰 픽스처. 공용 JSON이 여러 테스트의 데이터를 다 담고 있으면 해당한다.
- Fragile Test로 이어지는 이유: 다른 테스트를 위해 그 파일에 행을 추가하면, 그 파일의 우연한 성질(전체 개수·첫 행)에 기대던 테스트가 깨진다(Data Sensitivity·Fragile Fixture).

### 3. 룰렛 vs `assertAll`

(실험, JDK 21.0.12 · JUnit Platform 1.13.4 · AssertJ 3.27.4, 2026-10-03)

```text
a1_룰렛() [X] expected: <1000> but was: <900>
a4_assertTrue만() [X] expected: <true> but was: <false>
a2_assertAll() [X] 영수증 r-1 (3 failures)
    세금 ==> expected: <1000> but was: <900>
    합계 ==> expected: <11000> but was: <10900>
    통화 ==> expected: <KRW> but was: <krw>
```

- 룰렛: 첫 실패(세금)에서 멈춰 **1개**만 보고한다. 메시지에 "무엇의" 값인지 없다. 통화 단언만 있었다면 `expected: <true> but was: <false>`뿐이다.
- `assertAll`: 모든 단언을 실행하고 실패 **3개**를 함께 보고한다(JUnit 문서: "all failures will be reported together"). 메시지("세금" 등)를 달아서 무엇이 틀렸는지 보인다.

### 4. 조건부 단언

```text
b1_조건부_단언() [OK]
b2_조건_없는_단언() [X] issue한 영수증을 id로 찾을 수 있어야 한다 ==> expected: not <null>
```

- `find`가 `null`이면 `if`가 거짓이라 단언이 실행되지 않는다. 결함이 있는데 **초록**이다.
- 고친 테스트: 조건 자체를 단언한다.

```java
Receipt found = billing.find("r-1");
assertNotNull(found, "issue한 영수증을 id로 찾을 수 있어야 한다");
assertEquals(11_000, found.total());
```

### 5. 반복문 vs Parameterized

```text
c1_반복문() [X] expected: <0> but was: <3000>
c2_파라미터화(long, long)
  금액 0 → 배송비 0 [X] expected: <0> but was: <3000>
  금액 30000 → 배송비 0 [X] expected: <0> but was: <3000>
  (나머지 3개 [OK])
```

- 반복문: 첫 실패(0원)에서 멈춘다. 30,000원 결함은 숨는다. 메시지에 어느 입력인지도 없다.
- Parameterized: 행마다 독립 테스트라 실패 2개를 모두 보고하고, 이름에 입력이 들어간다.

### 6. Custom Assertion

- 푸는 스멜(xunitpatterns 질문 요지): 테스트 특유의 같음 판단이 필요할 때, 같은 단언 논리가 여러 테스트에 반복될 때(Test Code Duplication), 단언을 위한 조건 논리가 생길 때(Conditional Test Logic).
- `hasVatOf(10)`은 "세금 = 소계 × 10%"를 먼저, "합계 = 소계 + 세금"을 다음에 검사한다. `failWithMessage`가 예외를 던지므로 이 실험에서는 세금 검사에서 멈춰 합계 검사는 실행되지 않았다. 실행됐더라도 합계 10,900은 틀린 세금과 일관되어(10,000 + 900) 통과한다. 그래서 원인인 세금만 보고된다.

```text
-- failure 1 --영수증 r-1: 소계 10000의 부가세 10%는 1000여야 하는데 900다
-- failure 2 --영수증 r-1: 통화는 <KRW>여야 하는데 <krw>다
```

### 7. Humble Object

- 질문: "How can we make code testable when it is too closely coupled to its environment?" 답: "We extract the logic into a separate easy-to-test component that is decoupled from its environment."

```text
  @Scheduled expireCoupons()          ── 겸손한 껍질: 조회 → 정책 호출 → 저장 (분기 없음)
        │
        v
  CouponExpiryPolicy.expired(active, now)  ── 로직: 프레임워크 없이 small 테스트
```

- 함수형 코어·명령형 셸과 같은 점: 판단(순수 로직)과 I/O·프레임워크 접착을 분리해, 판단을 빠르고 결정적인 테스트로 덮는다. 껍질은 얇아서 중간 테스트 몇 개로 조립만 확인한다.

### 8. Test-Specific Subclass · Delegated Setup

- Test-Specific Subclass: SUT의 private 상태·동작에 접근해야 하는데 SUT를 바꾸기 어려울 때(레거시). 하위 클래스에 테스트용 메서드를 추가하거나 오버라이드한다.
- Delegated Setup: 테스트마다 Fresh Fixture를 만들되 준비 중복을 줄이고 싶을 때. 테스트 안에서 Creation Method(`aPaidOrder()` 등)를 부른다.
- 시간 고정

```java
class InvoiceSender {
    protected Instant now() { return Instant.now(); }   // Instant.now() 호출을 이음새로 감쌈
}
class FixedTimeInvoiceSender extends InvoiceSender {
    @Override protected Instant now() { return FIXED; }
}
```

- 의존 주입이 가능하면 `Clock`을 생성자로 받는 편이 낫다. 상속 구조에 묶이지 않고, 운영 코드에 테스트용 확장점을 남기지 않는다([10](../10-testing-time-and-concurrency/2-summary.md)).

### 9. 무엇을 검증하는지 안 보이는 테스트

- 의심할 스멜: Obscure Test — 원인으로 Mystery Guest(데이터가 밖에), General Fixture(과한 픽스처), Irrelevant Information(무관한 값이 가득), Eager Test(여러 동작).
- 고치는 순서
  1. 테스트 이름을 동작 한 문장으로 바꾼다. 문장이 둘이면 테스트를 쪼갠다.
  2. 결과에 영향을 주는 값을 테스트 안으로 옮긴다. 외부 파일·공용 시드 의존을 끊는다.
  3. 나머지 준비는 이름 있는 Creation Method로 숨긴다(Delegated Setup).
  4. 단언에 메시지를 달거나 Custom Assertion으로 바꿔, 실패 메시지만으로 원인이 보이게 한다.

### 10. 기본 실행 순서

- JUnit 5.13.4 User Guide 2.11: "By default, test classes and methods will be ordered using an algorithm that is deterministic but intentionally nonobvious." 실험에서도 실행 순서가 소스 순서와 달랐다(b2, a3, c1, a2, a4, a1, c2, b1).
- 경고: 결정적이라 늘 같은 순서로 돌아서, 순서에 기대는 공유 픽스처 테스트가 우연히 통과할 수 있다. 메서드를 추가하거나 이름을 바꾸거나 순서 설정(`MethodOrderer`)을 바꾸면 순서가 달라져 갑자기 깨질 수 있다. 테스트는 순서와 무관하게 Fresh Fixture로 독립시킨다(Interacting Tests → [11](../11-test-data-and-fixtures/2-summary.md)).
