# testing/12-test-smells-and-xunit-patterns — 테스트 스멜과 처방 패턴 — 정리 (힌트)

## 해결하는 문제

테스트 코드도 코드다. 운영 코드처럼 냄새가 나고, 그 냄새는 **실패했을 때** 비용으로 돌아온다.

```text
  CI 빨강
    │
    ├─ 무엇을 검증하는 테스트지?      ── 준비가 200줄, 데이터는 외부 파일   (Obscure Test, Mystery Guest)
    ├─ 단언 10개 중 어느 것이 실패?   ── expected: <true> but was: <false> (Assertion Roulette)
    ├─ 다른 단언도 틀렸나?            ── 첫 실패에서 멈춰서 모른다
    └─ 이 테스트는 왜 늘 초록이지?    ── if (x != null) { assert... }     (Conditional Test Logic)
  → 원인 파악에 30분(예시), 고친 뒤에도 또 다른 실패가 숨어 있다
```

- Gerard Meszaros 『xUnit Test Patterns: Refactoring Test Code』(Addison-Wesley, 2007)는 이런 증상을 **테스트 스멜**로 이름 붙이고, 고치는 방법을 **패턴**으로 정리했다. 같은 내용의 초고가 xunitpatterns.com에 있다(페이지마다 "책 N쪽을 보라"는 안내가 붙어 있다).
  - *테스트 스멜(test smell)*: 테스트 코드나 테스트 실행에서 보이는, 더 깊은 문제의 증상.

쉬운 예: 요리 레시피에 "적당량의 소스(냉장고 두 번째 칸 참고)"라고 적혀 있다.\
레시피만 봐서는 맛이 왜 이상한지 알 수 없다. 냉장고를 열어 봐야 한다.\
똑같은 구조다.\
테스트가 준비 데이터를 테스트 밖(공용 파일·DB·상위 클래스)에 숨기면, 실패 원인을 테스트만 읽어서는 못 찾는다(Mystery Guest).

실무 예
- 주문 테스트 하나가 `fixtures/orders.json`을 읽는다. 누군가 그 파일에 다른 테스트용 행을 추가하자 테스트 세 개(예시)가 깨졌다(General Fixture → Fragile Test).
- 영수증 테스트의 단언이 네 줄인데, 둘째 줄(세금)에서 실패해 멈추는 바람에 넷째 줄의 통화 결함은 세금을 고친 다음 CI 실행에서야 드러났다(아래 실험).

## 동작·원리

### 1. 스멜의 세 갈래 — Meszaros의 분류

xunitpatterns.com "Test Smells" 목록의 분류다.

```text
  코드 스멜 (테스트를 읽을 때 보인다)        행동 스멜 (테스트를 돌릴 때 보인다)      프로젝트 스멜 (팀 지표로 보인다)
  - Obscure Test                           - Assertion Roulette                  - Buggy Tests
  - Conditional Test Logic                 - Erratic Test                        - Developers Not Writing Tests
  - Hard-to-Test Code                      - Fragile Test                        - High Test Maintenance Cost
  - Test Code Duplication                  - Frequent Debugging                  - Production Bugs
  - Test Logic in Production               - Manual Intervention
                                           - Slow Tests
```

- 스멜은 원인(cause)을 여럿 가진다. 예: Obscure Test의 원인 중 하나가 Mystery Guest, Erratic Test의 원인 중 하나가 Interacting Tests다.

### 2. 이 노트에서 다루는 스멜

| 스멜 | xunitpatterns 정의(요지) | 주요 원인(사이트의 Cause 목록) |
|---|---|---|
| Obscure Test (책 186쪽) | "It is difficult to understand the test at a glance." | Eager Test, **Mystery Guest**, General Fixture, Irrelevant Information, Hard-Coded Test Data, Indirect Testing |
| Fragile Test (239쪽) | SUT가 테스트가 다루지 않는 부분에서 바뀌었는데 컴파일·실행이 실패한다 | Interface Sensitivity, Behavior Sensitivity, Data Sensitivity, Context Sensitivity, Overspecified Software, Sensitive Equality, Fragile Fixture |
| Slow Tests (253쪽) | "The tests take too long to run." | Slow Component Usage(가장 흔한 원인은 DB), General Fixture, Asynchronous Test(명시적 지연), Too Many Tests |
| Assertion Roulette (224쪽) | 여러 단언 중 어느 것이 실패했는지 알기 어렵다 | Eager Test, Missing Assertion Message |
| Conditional Test Logic (200쪽) | "A test contains code that may or may not be executed" | Flexible Test, Conditional Verification Logic, Production Logic in Test, Complex Teardown, Multiple Test Conditions |
| Test Code Duplication (213쪽) | "The same test code is repeated many times." | Cut-and-Paste Code Reuse, Reinventing the Wheel |

- 용어
  - *Mystery Guest*: 준비와 검증 사이의 인과가 안 보인다. 그 일부가 테스트 메서드 밖에서 일어나기 때문이다(외부 파일·공용 DB 행 등).
  - *General Fixture*: 이 테스트에 필요한 것보다 큰 픽스처를 만들거나 참조한다. 읽기 어렵고(Obscure), 느리고(Slow), 깨지기 쉽다(Fragile).
  - *Eager Test*: 한 테스트 메서드가 너무 많은 기능을 검증한다.
  - *Overspecified Software*: 테스트가 소프트웨어의 구조·동작을 필요 이상으로 말한다. 행위 검증(mock) 스타일과 관련된 Behavior Sensitivity의 한 형태라고 사이트가 적는다([02](../02-good-unit-tests/2-summary.md), [04](../04-classical-vs-london/2-summary.md)).
- Conditional Test Logic이 나쁜 이유(사이트 "Impact" 요지): 실행 경로가 여럿인 코드는 믿기 어렵다. 테스트는 테스트가 필요 없을 만큼 단순해야 한다. 그렇지 않으면 "테스트의 테스트"가 필요해진다.

### 3. 처방 패턴 — 스멜에서 패턴으로

```text
  스멜                          처방 패턴
  Assertion Roulette   ──────> 단언 메시지 · 한 조건 한 테스트 · Custom Assertion
  Conditional Test Logic ────> Custom Assertion(조건을 단언 안으로) · Parameterized Test(반복문 대신)
  Test Code Duplication ─────> Delegated Setup(생성 메서드) · Custom Assertion · Parameterized Test
  Obscure Test / Mystery Guest > Fresh Fixture를 테스트 안에서 보이게 · Delegated Setup
  Hard-to-Test Code(UI·프레임워크) > Humble Object
  private 상태 접근 필요(레거시) > Test-Specific Subclass
```

| 패턴 | xunitpatterns의 질문 → 답(요지) |
|---|---|
| Custom Assertion (474쪽) | 테스트 특유의 같음 판단·반복되는 단언 논리·조건 논리를 어떻게? → "Create a purpose-built Assertion Method that compares only those attributes of the object that define test-specific equality." |
| Parameterized Test (607쪽) | 같은 테스트 논리가 여러 테스트에 반복되면? → 준비·검증에 필요한 정보를 받아 테스트 수명 전체를 수행하는 유틸리티에 넘긴다. JUnit 5에서는 `@ParameterizedTest`가 이 역할이다 |
| Delegated Setup (411쪽) | Fresh Fixture를 어떻게 만드나? → "Each test creates its own Fresh Fixture by calling Creation Methods from within the Test Methods." |
| Humble Object (695쪽) | 환경과 너무 단단히 묶인 코드를 어떻게 테스트하나? → "We extract the logic into a separate easy-to-test component that is decoupled from its environment." 변형: Humble Dialog(원 작성: Michael Feathers "The Humble Dialog Box"), Humble Executable, Humble Transaction Controller |
| Test-Specific Subclass | SUT의 private 상태에 접근해야 하면? → "Add methods that expose the state or behavior needed by the test to a subclass of the SUT." |

- *Fresh Fixture*: 테스트마다 새로 만드는 픽스처. 테스트 사이 공유 상태가 없다.
- *Creation Method*: 픽스처 객체를 만드는 이름 있는 도우미(예: `aPaidOrder()`). 빌더·오브젝트 마더와의 비교는 [11](../11-test-data-and-fixtures/2-summary.md).

### 실험: 같은 결함, 네 가지 단언 스타일

영수증 발행 코드에 결함 다섯 개를 심었다.
- ① 부가세 9%(10%여야 함) ② 통화 `"krw"`(`"KRW"`여야 함) ③ 저장 키를 대문자로 해서 `find("r-1")`이 `null`
- 배송비 규칙 "0원은 0원, 3만 원 미만 3,000원, 3만 원 이상 무료"에 ④ `<=`(30,000에서 틀림) ⑤ 0원 처리 누락

```java
// a1 — Assertion Roulette: 메시지 없는 단언 여러 개
assertEquals(10_000, r.subtotal());
assertEquals(1_000, r.tax());
assertEquals(11_000, r.total());
assertTrue(r.currency().equals("KRW"));

// a2 — assertAll (JUnit 5 grouped assertions)
assertAll("영수증 r-1",
    () -> assertEquals(10_000, r.subtotal(), "소계"),
    () -> assertEquals(1_000, r.tax(), "세금"),
    () -> assertEquals(11_000, r.total(), "합계"),
    () -> assertEquals("KRW", r.currency(), "통화"));

// a3 — Custom Assertion(AssertJ AbstractAssert 상속) + SoftAssertions
SoftAssertions.assertSoftly(s -> {
    s.check(() -> assertThatReceipt(r).hasVatOf(10));
    s.check(() -> assertThatReceipt(r).isInCurrency("KRW"));
});

// b1 — Conditional Test Logic
Receipt found = billing.find("r-1");
if (found != null) { assertEquals(11_000, found.total()); }

// c1 — 반복문 안의 단언 vs c2 — @ParameterizedTest
for (long[] c : cases) assertEquals(c[1], billing.shippingFee(c[0]));
@ParameterizedTest(name = "금액 {0} → 배송비 {1}")
@CsvSource({ "0, 0", "10000, 3000", "29999, 3000", "30000, 0", "50000, 0" })
void c2_파라미터화(long amount, long fee) { assertEquals(fee, billing.shippingFee(amount)); }
```

Custom Assertion 본체(핵심):

```java
public ReceiptAssert hasVatOf(int percent) {
    isNotNull();
    long expected = actual.subtotal() * percent / 100;
    if (actual.tax() != expected)
        failWithMessage("영수증 %s: 소계 %d의 부가세 %d%%는 %d여야 하는데 %d다",
                actual.id(), actual.subtotal(), percent, expected, actual.tax());
    if (actual.total() != actual.subtotal() + actual.tax())           // 둘째 검사: 합계 일관성
        failWithMessage("영수증 %s: 합계 %d ≠ 소계 %d + 세금 %d", actual.id(), actual.total(), actual.subtotal(), actual.tax());
    return this;
}
```

(실험, JDK 21.0.12 temurin · JUnit Platform 1.13.4 / Jupiter 5.13.4 · AssertJ 3.27.4, Console Launcher `--details=tree`, 2026-10-03)

```text
|   +-- b2_조건_없는_단언() [X] issue한 영수증을 id로 찾을 수 있어야 한다 ==> expected: not <null>
|   +-- a3_커스텀_단언() [X]
|   |     Multiple Failures (2 failures)
|   |     -- failure 1 --영수증 r-1: 소계 10000의 부가세 10%는 1000여야 하는데 900다
|   |     -- failure 2 --영수증 r-1: 통화는 <KRW>여야 하는데 <krw>다
|   +-- c1_반복문() [X] expected: <0> but was: <3000>
|   +-- a2_assertAll() [X] 영수증 r-1 (3 failures)
|   |     	org.opentest4j.AssertionFailedError: 세금 ==> expected: <1000> but was: <900>
|   |     	org.opentest4j.AssertionFailedError: 합계 ==> expected: <11000> but was: <10900>
|   |     	org.opentest4j.AssertionFailedError: 통화 ==> expected: <KRW> but was: <krw>
|   +-- a4_assertTrue만() [X] expected: <true> but was: <false>
|   +-- a1_룰렛() [X] expected: <1000> but was: <900>
|   +-- c2_파라미터화(long, long) [OK]
|   | +-- 금액 0 → 배송비 0 [X] expected: <0> but was: <3000>
|   | +-- 금액 10000 → 배송비 3000 [OK]
|   | +-- 금액 29999 → 배송비 3000 [OK]
|   | +-- 금액 30000 → 배송비 0 [X] expected: <0> but was: <3000>
|   | '-- 금액 50000 → 배송비 0 [OK]
|   '-- b1_조건부_단언() [OK]
```

| 스타일 | 보고된 결함 | 메시지만으로 원인을 아나 |
|---|---|---|
| a1 룰렛 | 1개(세금). 합계·통화 결함은 숨음 | 무엇의 1000인지 모른다(줄 번호만) |
| a4 `assertTrue`만 | 1개(통화) | `expected: <true> but was: <false>` — 무엇이 틀렸는지 없다 |
| a2 `assertAll` | 3개(세금·합계·통화) | 단언 메시지("세금" 등)가 붙어 안다 |
| a3 Custom Assertion + Soft | 2개(세금 규칙·통화) | 도메인 말로 원인을 적는다 |
| b1 조건부 | **0개 — 초록** | 결함 ③(조회 실패)을 숨겼다 |
| b2 조건 없는 단언 | 1개 | 조회가 `null`임을 말한다 |
| c1 반복문 | 1개(0원). 30,000원 결함은 숨음 | 어느 입력인지 모른다 |
| c2 Parameterized | 2개(0원·30,000원) | 케이스 이름에 입력이 있다 |

- 관찰
  - 단언 여러 개는 **첫 실패에서 멈춘다**. 남은 결함은 고친 뒤 다음 실행에서야 보인다. JUnit 5.13.4 User Guide 2.5의 예제 주석: "In a grouped assertion all assertions are executed, and all failures will be reported together."
  - a3은 합계를 따로 보고하지 않았다. `failWithMessage`는 예외를 던지므로, 이 실행에서는 첫 검사(세금)가 실패한 순간 둘째 검사(합계 일관성)는 **실행되지 않았다**. 설령 실행됐더라도 합계 10,900은 틀린 세금과 일관되어(10,000 + 900) 실패하지 않는다. `hasVatOf`는 "합계 = 11,000"이 아니라 "세금 = 소계 × 세율", "합계 = 소계 + 세금"이라는 규칙으로 판단하므로, 원인인 세금 하나만 보고된다.
  - b1은 결함 ③을 숨긴 채 **초록**이다. "결과가 있으면 확인한다"는 조건이 "결과가 없다"는 결함을 통과시켰다.
  - 실행 순서가 소스 순서(a1, a2 …)와 다르다. JUnit Jupiter 5.13 문서: 기본 순서는 "deterministic but intentionally nonobvious". 테스트가 순서에 기대면 안 되는 이유이기도 하다([11](../11-test-data-and-fixtures/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **파라미터 표 = 데이터 주도 테스트.** `(입력, 기대값)` 행의 목록이다. 행 하나가 독립된 테스트 케이스가 되어 따로 성공·실패한다. 표의 행은 동치 분할·경계값으로 고른다([07](../07-test-design-techniques/2-summary.md)).
- **오류 수집 리스트.** `assertAll`·`SoftAssertions`는 단언을 즉시 던지지 않고 실패를 리스트에 모은 뒤 끝에 한 번 던진다(실험 출력의 `Suppressed:`·`Multiple Failures`).
- **Humble Object = 로직/접착 분리.** 의존 그래프를 "환경에 묶인 얇은 껍질"과 "순수 로직"으로 자른다. 껍질에는 분기가 거의 없어 테스트하지 않아도 위험이 작고, 로직은 small 테스트로 덮는다([software-design/26](../../software-design/26-functional-core-imperative-shell/2-summary.md)).
- **Custom Assertion = 술어(predicate) + 설명.** "테스트 특유의 같음"을 함수 하나로 정의해 여러 테스트가 공유한다. 실패 메시지는 술어가 어긋난 이유를 도메인 말로 만든다.

## 적용 — 풀어나가는 법

1. **실패 메시지부터 본다.** 테스트를 일부러 깨뜨려(기대값을 바꿔) 메시지만으로 원인을 알 수 있는지 확인한다. 모르면 Assertion Roulette·Obscure Test다.
2. **한 테스트 = 한 동작.** 여러 동작을 검증하면 테스트를 쪼갠다. 한 동작의 여러 속성이면 `assertAll`이나 Custom Assertion으로 묶는다.
3. **테스트 안에서 `if`·`for`를 지운다.**
   - `if (x != null)` → 그 조건 자체를 단언한다(`assertNotNull`, `assertThat(x).isNotNull()`).
   - 입력별 반복 → `@ParameterizedTest` + `@CsvSource`·`@MethodSource`.
4. **준비를 보이게.** 이 테스트의 결과에 영향을 주는 값은 테스트 안에 둔다. 나머지는 Creation Method로 숨긴다(Delegated Setup).

```java
@Test void 결제된_주문은_취소하면_환불된다() {
    Order order = aPaidOrder().withAmount(30_000).build();   // 결과에 영향을 주는 값만 보인다
    order.cancel();
    assertThat(order.refundedAmount()).isEqualTo(30_000);
}
```

5. **Humble Object로 테스트하기 어려운 곳을 얇게.**

```java
// 겸손한 껍질 — 프레임워크에 묶임, 로직 없음
@Scheduled(cron = "0 0 * * * *")
public void expireCoupons() {
    repo.saveAll(policy.expired(repo.findActive(), clock.instant()));
}

// 로직 — 프레임워크 없이 small 테스트
class CouponExpiryPolicy {
    List<Coupon> expired(List<Coupon> active, Instant now) {
        return active.stream().filter(c -> !c.expiresAt().isAfter(now)).map(Coupon::expire).toList();
    }
}
```

6. **레거시에서 Test-Specific Subclass.** 생성자 주입을 넣기 어려운 클래스라면, 시간·외부 호출을 감싼 `protected` 메서드를 테스트용 하위 클래스에서 바꾼다. 의존 주입이 가능하면 그쪽이 낫다([10](../10-testing-time-and-concurrency/2-summary.md), [17](../17-characterization-tests-legacy/2-summary.md)).

```java
class InvoiceSender {
    protected Instant now() { return Instant.now(); }      // 이음새
    boolean isOverdue(Invoice inv) { return inv.dueAt().isBefore(now()); }
}
class FixedTimeInvoiceSender extends InvoiceSender {        // Test-Specific Subclass
    private final Instant fixed;
    FixedTimeInvoiceSender(Instant fixed) { this.fixed = fixed; }
    @Override protected Instant now() { return fixed; }
}
```

7. **Slow Tests 진단.** 테스트별 실행 시간을 정렬해 상위를 본다(Surefire XML 보고서의 `time` 속성 등). 원인 순서: DB·네트워크(Slow Component Usage) → 매번 큰 픽스처(General Fixture) → `sleep`(Asynchronous Test).

## 장애 시나리오와 대처

### 1. 무엇을 검증하는지 안 보인다 — 원인 파악 30분 (⚠)

- **현상**: CI 실패를 맡은 사람이 테스트를 읽고도 무엇을 확인하는지 모른다. 상위 클래스·공용 JSON·DB 시드를 열어 보며 30분(예시)을 쓴다.
- **보이는 형태**: 준비 코드가 길거나 테스트 밖에 있다. 단언의 기대값이 어디서 왔는지 안 보인다(Hard-Coded Test Data, Mystery Guest).
- **원인**: Obscure Test — General Fixture, Mystery Guest, Irrelevant Information.
- **대처**: 결과에 영향을 주는 값을 테스트 안으로 옮긴다. 나머지는 의미 있는 이름의 Creation Method로(Delegated Setup). 공유 픽스처를 테스트별 Fresh Fixture로 바꾼다([11](../11-test-data-and-fixtures/2-summary.md)).

### 2. 단언 10개 한 테스트 — 첫 실패가 나머지를 숨긴다 (⚠)

- **현상**: 결함 하나를 고치고 CI를 다시 돌리면 같은 테스트가 다른 줄에서 또 실패한다. 수정-실행이 여러 번 반복된다.
- **보이는 형태**: `expected: <1000> but was: <900>`처럼 무엇의 값인지 없는 메시지, `expected: <true> but was: <false>`(실험 a1·a4).
- **원인**: Assertion Roulette — Eager Test, Missing Assertion Message. 단언은 첫 실패에서 예외를 던져 멈춘다.
- **대처**: 동작별로 테스트를 쪼갠다. 한 동작의 여러 속성이면 `assertAll`·`SoftAssertions`. 단언에 메시지를 단다. 반복되는 판단은 Custom Assertion으로.

### 3. 테스트 안의 `if` — 분기 한쪽만 검증한다 (⚠)

- **현상**: 조회 결함으로 화면에 영수증이 안 나오는데, 그 기능의 테스트는 계속 초록이다.
- **보이는 형태**: `if (x != null) { assert... }`, `try { ... } catch (Exception e) { }`, 환경에 따라 다른 경로(Flexible Test).
- **원인**: Conditional Test Logic. 조건이 거짓이면 단언이 아예 실행되지 않는다(실험 b1).
- **대처**: 조건 자체를 단언한다. 여러 입력은 Parameterized Test로. 예외 기대는 `assertThrows`.

### 4. UI·프레임워크에 로직 — 테스트 불가 (⚠)

- **현상**: 쿠폰 만료 규칙이 스케줄러 메서드·컨트롤러 안에 있다. 테스트하려면 프레임워크 컨텍스트와 DB를 띄워야 해서 아무도 테스트를 안 쓴다.
- **보이는 형태**: 그 클래스의 테스트가 없거나, 있어도 느리고 불안정하다(Hard-to-Test Code, Slow Tests).
- **원인**: Humble Object 부재. 로직과 환경 접착 코드가 한 객체에 있다.
- **대처**: 로직을 프레임워크와 무관한 객체로 빼고(Humble Object), 껍질은 얇게 둔다. 껍질은 중간 테스트 몇 개로 조립만 확인한다.

### 5. 픽스처 한 줄 추가에 테스트 여럿이 깨진다

- **현상**: 공용 시드 데이터에 행 하나를 추가했더니 관계없는 테스트 세 개(예시)가 깨졌다. 마더 데이터를 바꾼 11 실험 C에서는 실제로 2개가 깨졌다([11](../11-test-data-and-fixtures/2-summary.md)).
- **원인**: Fragile Test — Data Sensitivity·Fragile Fixture. 테스트가 공유 픽스처의 "전체 개수"나 "첫 행" 같은 우연한 성질에 의존한다.
- **대처**: 테스트마다 필요한 데이터를 직접 만들고 그것만 단언한다. 공유가 꼭 필요하면 읽기 전용으로 두고, 단언은 자기가 만든 데이터로 범위를 좁힌다.

## 핵심 문장

- 테스트 스멜은 실패했을 때 원인 파악 비용으로 돌아온다. 실패 메시지만으로 무엇이 틀렸는지 알 수 있어야 한다.
- 단언 여러 개는 첫 실패에서 멈춘다. 한 동작의 여러 속성은 `assertAll`·Soft Assertions·Custom Assertion으로 함께 보고한다.
- 테스트 안의 `if`는 조건이 거짓일 때 아무것도 검증하지 않는다. 조건 자체를 단언하고, 입력별 반복은 Parameterized Test로 바꾼다.
- 결과에 영향을 주는 데이터는 테스트 안에서 보여야 한다. 나머지는 Creation Method로 숨긴다(Mystery Guest·General Fixture 처방).
- 프레임워크·UI에 묶인 코드는 Humble Object로 로직을 떼어 내야 small 테스트가 가능하다.

## 관련 주제·근거

- 선행
  - [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 좋은 테스트의 기준, AAA
  - [11-test-data-and-fixtures](../11-test-data-and-fixtures/2-summary.md) — 픽스처·빌더·오브젝트 마더·격리
- 연결
  - [04-classical-vs-london](../04-classical-vs-london/2-summary.md) — Overspecified Software와 mock 과용
  - [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — 파라미터 표의 행을 고르는 법
  - [09-flaky-tests](../09-flaky-tests/2-summary.md) · [10-testing-time-and-concurrency](../10-testing-time-and-concurrency/2-summary.md) — Erratic Test, Asynchronous Test
  - [17-characterization-tests-legacy](../17-characterization-tests-legacy/2-summary.md) — 레거시의 이음새, Test-Specific Subclass
  - [software-design/10-code-smells](../../software-design/10-code-smells/2-summary.md) — 운영 코드의 스멜
  - [software-design/26](../../software-design/26-functional-core-imperative-shell/2-summary.md) — 함수형 코어·명령형 셸, Humble Object
  - [software-design/42](../../software-design/42-ui-architecture-patterns/2-summary.md) — UI 구조 패턴
- 교재·문서
  - Gerard Meszaros, 『xUnit Test Patterns: Refactoring Test Code』(Addison-Wesley, 2007) — 초고 사이트 xunitpatterns.com
    - "Test Smells" 목록(코드·행동·프로젝트 스멜 분류) <http://xunitpatterns.com/Test%20Smells.html>
    - Obscure Test(186쪽, Mystery Guest·General Fixture 등) <http://xunitpatterns.com/Obscure%20Test.html> · Conditional Test Logic(200쪽) · Test Code Duplication(213쪽) · Assertion Roulette(224쪽) · Fragile Test(239쪽) · Slow Tests(253쪽) · Erratic Test(Interacting Tests 등)
    - Delegated Setup(411쪽) · Custom Assertion(474쪽) · Parameterized Test(607쪽) · Humble Object(695쪽, Humble Dialog·Executable·Transaction Controller) · Test-Specific Subclass · Four-Phase Test(358쪽)
  - Michael Feathers, "The Humble Dialog Box"(Humble Object 페이지가 원 작성으로 소개)
  - JUnit 5.13.4 User Guide — 2.5 Assertions(grouped assertions `assertAll`), 2.11 Test Execution Order("deterministic but intentionally nonobvious"), 2.17 Parameterized Classes and Tests <https://docs.junit.org/5.13.4/user-guide/index.html>
  - AssertJ 3.27 — `AbstractAssert`·`failWithMessage`(커스텀 단언), `SoftAssertions.assertSoftly`
  - 『Software Engineering at Google』 12장 — Don't Put Logic in Tests, Write Clear Failure Messages, DAMP Not DRY <https://abseil.io/resources/swe-book/html/ch12.html>
- 실험 목록
  - 결함 5개를 심은 영수증·배송비 코드에 단언 스타일 8가지(룰렛·`assertTrue`만·`assertAll`·Custom Assertion+Soft·조건부·조건 없음·반복문·Parameterized)를 적용해 보고된 결함 수와 메시지 비교 — eclipse-temurin:21-jdk(21.0.12) 컨테이너, JUnit Console Launcher 1.13.4(`--details=tree`), AssertJ 3.27.4
