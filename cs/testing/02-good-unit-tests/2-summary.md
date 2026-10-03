# testing/02-good-unit-tests — 좋은 단위 테스트: 네 기둥과 AAA — 정리 (힌트)

## 해결하는 문제

테스트가 있다고 다 도움이 되지는 않는다.\
어떤 테스트는 버그는 못 잡으면서, 코드를 정리할 때마다 빨개져서 고치는 비용만 낸다.

```text
  리팩터링 커밋 (동작은 그대로)
        │
        v
  테스트 37개 빨강 ──> "테스트 고치느라 하루" ──> 다음엔 리팩터링을 안 한다
        │
        └── 그런데 그 37개 중 진짜 버그를 알려 준 것은 0개
```

- SWE@G 12장의 정의: *깨지기 쉬운 테스트(brittle test)*는 "fails in the face of an unrelated change to production code that does not introduce any real bugs".
- 팀이 이런 테스트를 계속 쓰면, 늘어나는 테스트 묶음의 실패를 훑느라 테스트 유지가 팀 시간의 점점 큰 몫을 먹는다. 변경마다 손으로 고쳐야 하는 묶음을 "자동" 테스트라 부르기는 어렵다고까지 적는다(12장 "Preventing Brittle Tests").

쉬운 예: 화재경보기가 토스트만 구워도 울린다.\
몇 번 겪으면 사람들은 경보가 울려도 창문만 연다. 진짜 불이 나도 마찬가지다.\
똑같은 구조다.\
거짓 경보가 잦은 테스트 묶음은 진짜 실패까지 무시하게 만든다.

실무 예: 서비스 테스트가 `verify(calc).total(lines)`, `inOrder.verify(repo).save(...)`로 내부 호출 순서를 고정해 두었다.\
누군가 계산을 다른 객체로 옮기는 리팩터링을 하자 테스트가 깨졌다. 동작은 그대로였다(아래 실험).

## 동작·원리

### 1. 네 기둥 — Khorikov의 평가 틀

Khorikov 『Unit Testing PPP』 4장 "The four pillars of a good unit test"(장 제목·절 목록은 livebook에서 확인).

| 기둥 | 묻는 것 | 실패하면 |
|---|---|---|
| 회귀 방지(protection against regressions) | 버그가 생기면 이 테스트가 잡나 | *거짓 음성* — 버그인데 초록 |
| 리팩터링 내성(resistance to refactoring) | 동작을 보존하는 내부 변경에도 초록을 유지하나 | *거짓 양성* — 버그 아닌데 빨강 |
| 빠른 피드백(fast feedback) | 얼마나 빨리 도나 | 덜 자주 돌리게 된다 |
| 유지보수성(maintainability) | 읽고 고치기 쉬운가, 준비(의존 설정)가 쉬운가 | 테스트 자체가 부채가 된다 |

- Khorikov 블로그(2020-02-11) 원문 정의(이 글은 책에서 "거짓 양성"을 **리팩터링이 일으킨 실패**로 한정했고, 외부 의존 때문에 흔들리는 실패(flaky)는 유지보수성 기둥으로 분류했다고 밝힌다)
  - *거짓 양성(false positive)*: "a false alarm, aka false failure". 리팩터링 뒤 실패하는 경우다.
  - 회귀 방지 = "Lack of false negatives, aka lack of false passes".
  - 리팩터링 내성 = "the degree to which a test can sustain a refactoring of the underlying application code without turning red".
- 가치 = 네 점수의 **곱**(각 0~1). 하나가 0이면 가치도 0이다. 이 정식화는 책 4장 내용을 요약한 2차 출처(talon.one 블로그)에서 확인했다. 책 본문 문장은 직접 확인하지 못했다 [?].

```text
                실제로 버그가 있나?
                  있음                 없음
  테스트   빨강 │ 참 양성(제 할 일)   │ 거짓 양성 ← 리팩터링 내성 부족
  결과     초록 │ 거짓 음성 ← 회귀 방지 부족 │ 참 음성
```

- 앞의 세 기둥은 서로 당긴다. 4.4절 제목이 "In search of an ideal test"이고, 2차 요약들은 이 절의 논지를 "네 기둥을 모두 최대로 할 수는 없다"로 전한다. 책 본문의 예시 문장은 확인하지 못했다 [?]. 아래는 그 논지를 보이는 예다.
  - E2E 테스트: 회귀 방지·리팩터링 내성 높음, 느림.
  - 하찮은 테스트(getter 확인 등): 빠르고 안 깨지지만 잡는 버그가 거의 없음.
  - 깨지기 쉬운 테스트(내부 호출 고정): 빠르고 버그도 잡지만 리팩터링마다 빨강.
- Khorikov의 주장: 리팩터링 내성은 양보하지 않는다("non-negotiable"). 남은 둘(회귀 방지 vs 빠른 피드백) 사이에서 고른다. 2차 요약(binaryphile 2026, gniemann 리뷰)에서 확인했고 책 쪽수는 확인하지 못했다 [?].

### 2. 관찰 가능한 동작 vs 구현 세부

```text
          호출자(클라이언트)
              │  공개 API: place(id, lines) → Order
              v
   ┌──────────────────────── OrderService ────────────────────────┐
   │  calc.total(lines)  →  new Order(...)  →  repo.save  →  notify │  ← 구현 세부
   └──────────────────────────────────────────────────────────────┘
              │                                      │
     반환값·저장된 상태                      밖으로 나가는 부수효과(메일)
     = 관찰 가능한 결과                      = 관찰 가능한 결과
```

- *관찰 가능한 동작(observable behavior)*: 호출자의 목표와 바로 연결되는 결과. 반환값, 외부에서 볼 수 있는 상태, 프로세스 밖으로 나가는 부수효과.
- *구현 세부(implementation detail)*: 그 결과를 **어떻게** 만들었나. 내부 도우미, 내부 협력 객체 호출 순서·횟수.
- 테스트를 구현 세부에 묶을수록 거짓 양성이 는다. 책 4장의 문장으로 2차 요약(olano.dev)이 인용한다: "The more the test is coupled to the implementation details of the system under test (SUT), the more false alarms it generates." 책 본문 쪽은 직접 확인하지 못했다.
- SWE@G 12장의 같은 원칙
  - "Test via Public APIs" — 호출자가 쓰는 방식으로 테스트한다.
  - "Test State, Not Interactions" — 상호작용 검증은 "how a system arrived at its result"를 확인해서 깨지기 쉽다.
- SWE@G 12장의 변경 네 종류와 테스트의 기대 반응

| 변경 | 기존 테스트를 고쳐야 하나 |
|---|---|
| 순수 리팩터링 | 아니다. 고쳐야 했다면 동작이 바뀌었거나 테스트의 추상 수준이 틀렸다 |
| 새 기능 | 아니다. 새 테스트만 추가한다 |
| 버그 수정 | 대개 아니다(원문 "typically"). 빠졌던 테스트 케이스를 추가한다 |
| 동작 변경 | 그렇다. 유일하게 기존 테스트를 고치는 경우다 |

### 3. 테스트 하나의 구조 — AAA

```text
  Arrange (준비)   ── SUT와 입력을 만든다
  Act     (실행)   ── 검증할 동작 한 번
  Assert  (확인)   ── 결과를 단언
```

- *SUT(system under test)*: 지금 테스트하는 대상.
- 같은 구조의 다른 이름
  - Meszaros "Four-Phase Test": fixture setup → exercise SUT → result verification → fixture teardown(xunitpatterns.com, 책 358쪽).
  - BDD의 Given-When-Then. SWE@G 12장 각주도 이 세 부분을 "arrange," "act," "assert"라고도 부른다고 적는다.
- Khorikov 3장 3.1 "How to structure a unit test"가 AAA를 다룬다(절 제목 확인).
- 실천 지침(원칙, 저자들의 주장)
  - Act는 한 번. Act가 여러 번이면 여러 동작을 한 테스트에 섞은 것이다(Meszaros의 Eager Test → [12](../12-test-smells-and-xunit-patterns/2-summary.md)).
  - 테스트 안에 `if`·반복문을 두지 않는다. SWE@G 12장 "Don't Put Logic in Tests".
  - 이름은 메서드가 아니라 동작으로 짓는다. SWE@G 12장 "Test Behaviors, Not Methods", "Name tests after the behavior being tested".
  - 실패 메시지가 원인을 말하게 한다. SWE@G 12장 "Write Clear Failure Messages".
  - 중복을 다 없애기보다 읽히게 둔다. SWE@G 12장 "DAMP, Not DRY"(Descriptive And Meaningful Phrases).

### 실험: 구현 세부 테스트 vs 관찰 가능한 결과 테스트

같은 주문 코드에 두 테스트 묶음을 붙였다. 각 6개다.
- **D(구현 세부)**: package-private 도우미 `subtotal()`을 직접 부르고, mock으로 내부 호출 횟수·순서를 `verify`·`inOrder`·`verifyNoMoreInteractions`로 고정.
- **C(관찰 가능한 결과)**: 진짜 `DiscountPolicy`·`PriceCalculator`를 쓰고, 프로세스 밖 의존(저장소·알림)만 인메모리 Fake·기록용 대역으로 바꿔 반환값·저장 상태·보낸 알림을 확인.
- 두 묶음 모두 `DiscountPolicyTest` 2개는 같다(협력 객체가 없는 클래스).

```java
// 운영 코드(기준)
public long total(List<OrderLine> lines) {             // PriceCalculator
    long sub = subtotal(lines);
    return sub - sub * policy.discountRate(sub) / 100;  // DiscountPolicy: 소계 >= 100,000이면 10(%)
}
public Order place(String id, List<OrderLine> lines) { // OrderService
    long total = calc.total(lines);
    Order order = new Order(id, List.copyOf(lines), total);
    repo.save(order);
    notifier.orderPlaced(id, total);
    return order;
}

// D — 구현 세부
@Test void subtotal_도우미가_수량을_곱한다() {
    assertThat(new PriceCalculator(new DiscountPolicy())
        .subtotal(List.of(new OrderLine("A", 3, 20_000)))).isEqualTo(60_000);
}
@Test void 저장한_뒤_통지한다() {
    when(calc.total(lines)).thenReturn(90_000L);
    service.place("o-1", lines);
    InOrder o = inOrder(repo, notifier);
    o.verify(repo).save(new Order("o-1", lines, 90_000));
    o.verify(notifier).orderPlaced("o-1", 90_000);
    verifyNoMoreInteractions(repo, notifier);
}

// C — 관찰 가능한 결과
@Test void 주문이_할인된_총액으로_저장된다() {
    service.place("o-1", lines);                                   // 2 × 50,000
    assertThat(repo.findById("o-1")).map(Order::total).contains(90_000L);
}
```

변경 여섯 가지를 하나씩 넣고 두 묶음을 돌렸다.
- 리팩터링(동작 보존)
  - R1: `subtotal()` 도우미를 지우고 스트림 합으로 인라인.
  - R2: 할인 적용을 `DiscountPolicy.apply(subtotal)`로 옮김(`discountRate`는 그대로 둠).
- 버그
  - B1: 경계 `>=` → `>`.
  - B2: 소계에서 수량 누락.
  - B3: `repo.save` 누락.
  - B4: 정책 담당자가 할인율 단위를 %에서 ‰(퍼밀)로 바꾸고 자기 테스트(`DiscountPolicyTest`)도 새 단위로 고쳤다. `PriceCalculator`는 여전히 `/100`.

(실험, JDK 21.0.12 temurin · JUnit Platform 1.13.4 · AssertJ 3.27.4 · Mockito 5.18.0, 테스트 파일마다 따로 컴파일해 컴파일 실패도 셈, 2026-10-03)

```text
base D 전체=6 통과=6 실패=0 |
base C 전체=6 통과=6 실패=0 |
R1 D 전체=6 통과=4 실패=0 |  PriceCalculatorDetailTest[컴파일 실패 2개: cannot find symbol]
R1 C 전체=6 통과=6 실패=0 |
R2 D 전체=6 통과=5 실패=1 | PriceCalculatorDetailTest:소계로_discountRate를_한번_묻는다()
R2 C 전체=6 통과=6 실패=0 |
B1 D 전체=6 통과=5 실패=1 | DiscountPolicyTest:소계_100000부터_10퍼센트()
B1 C 전체=6 통과=2 실패=4 | OrderServiceTest:… ×2  PriceCalculatorTest:경계에서_할인이_적용된다()  DiscountPolicyTest:소계_100000부터_10퍼센트()
B2 D 전체=6 통과=4 실패=2 | PriceCalculatorDetailTest:subtotal_도우미가_수량을_곱한다()  PriceCalculatorDetailTest:소계로_discountRate를_한번_묻는다()
B2 C 전체=6 통과=2 실패=4 | OrderServiceTest:… ×2  PriceCalculatorTest:수량을_곱한다()  PriceCalculatorTest:경계에서_할인이_적용된다()
B3 D 전체=6 통과=5 실패=1 | OrderServiceDetailTest:저장한_뒤_통지한다()
B3 C 전체=6 통과=5 실패=1 | OrderServiceTest:주문이_할인된_총액으로_저장된다()
B4 D 통과=6 실패=0 |
B4 C 통과=3 실패=3 | OrderServiceTest:주문이_할인된_총액으로_저장된다()  OrderServiceTest:고객에게_총액이_통지된다()  PriceCalculatorTest:경계에서_할인이_적용된다()
```

R2에서 D가 낸 메시지, B4에서 C가 낸 메시지:

```text
R2 D  소계로_discountRate를_한번_묻는다() ✘
        Wanted but not invoked:
        -> at shop.DiscountPolicy.discountRate(DiscountPolicy.java:4)
B4 C  경계에서_할인이_적용된다() ✘
        expected: 90000L
         but was: 0L
```

| | D(구현 세부) | C(관찰 가능한 결과) |
|---|---|---|
| 리팩터링 2건에서 깨진 테스트(거짓 양성) | 3개(R1 컴파일 2 + R2 1) | 0개 |
| 버그 4건 중 잡은 버그 | 3건(B4 놓침) | 4건 |

- 관찰
  - D는 동작이 같은데도 3개가 깨졌다. "Wanted but not invoked"는 버그가 아니라 **호출 경로가 바뀌었다**는 뜻이다.
  - D는 B4를 놓쳤다. D의 계산기 테스트는 정책을 mock으로 바꿔 두어, 두 클래스가 단위를 다르게 이해해도 모른다. C에서는 100,000원 주문이 **0원**이 되는 것이 바로 드러났다.
  - C는 버그 하나에 테스트 여러 개가 함께 빨개졌다(B1·B2에서 4개). 원인 찾기는 조금 더 걸릴 수 있다. 이 맞교환은 [04](../04-classical-vs-london/2-summary.md)에서 다룬다.
- 한계: 내가 만든 작은 코드·테스트 6개씩이다. 수치는 기제를 보이는 예이지 통계가 아니다. 테스트 묶음을 다르게 짜면 숫자가 달라진다.

## 쓰이는 자료구조·알고리즘

- **2×2 혼동 행렬.** 테스트 결과(빨강/초록) × 실제(버그 있음/없음). 거짓 양성은 리팩터링 내성, 거짓 음성은 회귀 방지 기둥에 대응한다.
- **곱셈 가치 모델.** 가치 = 회귀 방지 × 리팩터링 내성 × 빠른 피드백 × 유지보수성. 합이 아니라 곱이라서 한 축이 0이면 다른 축이 아무리 높아도 0이다(2차 출처 요약).
- **공개 API = 테스트가 의존하는 인터페이스.** 테스트도 코드의 클라이언트다. 테스트가 의존하는 표면이 좁고 안정적일수록 내부 변경에 덜 흔들린다([software-design/02](../../software-design/02-modularity-coupling-cohesion/2-summary.md)의 결합도와 같은 이야기).
- **Fake = 인메모리 맵.** 실험의 `FakeOrderRepository`는 `HashMap<String, Order>`다([03](../03-test-doubles/2-summary.md)).

## 적용 — 풀어나가는 법

1. **검증할 동작을 한 문장으로 쓴다.** "10만 원 이상 주문은 10% 할인된 총액으로 저장된다." 메서드 이름이 아니라 동작이다.
2. **그 동작을 관찰할 수 있는 지점을 고른다.** 반환값 → 공개 상태 → 프로세스 밖으로 나가는 호출 순으로.
3. **AAA로 쓴다.** 준비는 필요한 것만, 실행은 한 번, 단언은 그 동작에 관한 것만.

```java
@Test
void 십만원_이상_주문은_할인된_총액으로_저장된다() {
    // Arrange
    var repo = new FakeOrderRepository();
    var service = new OrderService(new PriceCalculator(new DiscountPolicy()), repo, new RecordingNotifier());
    var lines = List.of(new OrderLine("A", 2, 50_000));

    // Act
    service.place("o-1", lines);

    // Assert
    assertThat(repo.findById("o-1")).map(Order::total).contains(90_000L);
}
```

4. **대역은 프로세스 밖 의존에만.** 같은 프로세스의 도메인 객체는 진짜를 쓴다(Khorikov·SWE@G 13장 "Prefer Realism Over Isolation". 학파 논쟁은 [04](../04-classical-vs-london/2-summary.md)). 메일·외부 API는 Fake·Spy로 바꾼다. 저장소는 단위 테스트에서 Fake로 둘 수 있지만, Khorikov "When to Mock"은 앱 전용 DB 같은 관리형 의존을 통합 테스트에서 실제 인스턴스로 시험하라고 한다([03](../03-test-doubles/2-summary.md)·[08](../08-integration-tests-real-dependencies/2-summary.md)).
5. **스스로 점검한다.**
   - 이 테스트가 깨지는 경우를 상상한다. 동작이 바뀔 때만인가, 내부를 정리해도 깨지나?
   - 버그를 일부러 넣어 본다(변이). 이 테스트가 빨개지나? → 체계적으로는 변이 테스트([15](../15-mutation-testing/2-summary.md)).
6. **진단: 리팩터링 커밋이 테스트를 얼마나 건드렸나.** 동작 보존 커밋에서 테스트 파일이 많이 바뀌었다면 거짓 양성 신호다.

```bash
# 최근 100개 커밋 중 "refactor"가 들어간 커밋마다 바뀐 테스트 파일 수
for c in $(git log -100 --grep=refactor --format=%h); do
  echo "$c $(git show --name-only --format= "$c" | grep -c 'src/test/')"
done
```

## 장애 시나리오와 대처

### 1. 리팩터링마다 대량 실패 — 구현 세부 검증 (⚠)

- **현상**: 메서드 하나를 옮기는 커밋에 테스트 수십 개가 빨개진다. 다들 "테스트 고치기"에 시간을 쓰고, 리팩터링을 피한다.
- **보이는 형태**: Mockito `Wanted but not invoked`, `No interactions wanted here`(`verifyNoMoreInteractions` 위반 — Mockito 5.18 `Reporter` 소스의 문구), `cannot find symbol`(지운 도우미를 테스트가 직접 부름). 실험 R1·R2가 이 모양이다.
- **원인**: 테스트가 내부 협력 객체 호출·private 도우미 같은 구현 세부에 묶였다.
- **대처**
  - 단언을 관찰 가능한 결과로 옮긴다. 같은 프로세스의 도메인 객체는 진짜를 쓴다.
  - 상호작용 검증은 꼭 필요한 곳에만 남긴다. 기준은 출처마다 다르다. SWE@G 13장은 "상태를 바꾸는 함수"("Prefer to perform interaction testing only for state-changing functions"), Khorikov는 "관리하지 않는 프로세스 밖 의존으로 나가는 통신"(메일 발송·메시지 발행 등)이다. 둘 다 값을 돌려주기만 하는 조회 호출의 `verify`는 빼라는 점에서 같다.
  - private 도우미를 테스트하고 싶다면 그것이 따로 이름 붙일 만한 개념인지 본다. 그렇다면 공개 API를 가진 클래스로 뺀다.

### 2. 초록인데 운영 버그 — 대역이 진실을 가렸다

- **현상**: 단위 테스트는 다 통과하는데, 결합된 동작이 틀렸다(실험 B4: 10만 원 주문이 0원).
- **보이는 형태**: 각 클래스 테스트는 초록이다. 통합 경로를 실행하는 테스트가 없거나 그 테스트만 빨강이다.
- **원인**: 협력 객체를 stub으로 바꾸면서 "그 객체가 이렇게 답한다"는 가정을 테스트에 새겼다. 실제 객체가 다르게 답해도 모른다.
- **대처**: 같은 프로세스의 협력 객체는 진짜로 묶어 검증하는 테스트를 둔다. 경계의 대역은 실제 구현과 같은 계약 테스트를 돌린다([03](../03-test-doubles/2-summary.md), [13](../13-contract-testing/2-summary.md)).

### 3. 실패했는데 무엇이 틀렸는지 모른다

- **현상**: CI 실패 메시지가 `expected: <true> but was: <false>`뿐이다. 원인 파악에 한참 걸린다.
- **원인**: 단언 메시지가 없거나, 한 테스트에 단언이 너무 많거나(Assertion Roulette), 준비 데이터가 테스트 밖에 숨어 있다(Mystery Guest).
- **대처**: 동작 하나에 테스트 하나, 의미가 드러나는 단언(AssertJ·커스텀 단언), 준비를 테스트 안에서 보이게. 자세히는 [12](../12-test-smells-and-xunit-patterns/2-summary.md).

### 4. 느린 단위 테스트

- **현상**: "단위 테스트"인데 묶음이 수 분 걸린다. 개발자가 로컬에서 안 돌린다.
- **원인**: 단위 테스트가 DB·네트워크·`sleep`을 쓴다. SWE@G 기준으로는 small이 아니다([01](../01-why-test-and-pyramid/2-summary.md)).
- **대처**: 로직을 I/O에서 떼어 small로 만들고, I/O 경계는 중간 테스트로 따로 모은다. 시간 의존은 가짜 시계([10](../10-testing-time-and-concurrency/2-summary.md)).

## 핵심 문장

- 좋은 단위 테스트는 버그에는 빨개지고(회귀 방지), 동작을 보존하는 리팩터링에는 초록을 유지하고(리팩터링 내성), 빠르고, 읽고 고치기 쉽다.
- 거짓 양성(버그 아닌데 빨강)은 테스트 묶음 전체의 신뢰를 갉아먹는다. 경보를 무시하는 습관이 진짜 실패까지 덮는다.
- 테스트는 관찰 가능한 결과(반환값·상태·밖으로 나가는 부수효과)를 확인한다. 내부 호출 순서·private 도우미는 구현 세부다.
- 순수 리팩터링·새 기능·버그 수정에서는 기존 테스트를 고칠 일이 없어야 한다. 고쳐야 했다면 테스트의 추상 수준을 의심한다.
- AAA: 준비, 실행 한 번, 그 동작에 관한 단언. 테스트 안에 논리를 두지 않는다.

## 관련 주제·근거

- 선행
  - [01-why-test-and-pyramid](../01-why-test-and-pyramid/2-summary.md) — 테스트의 목적·크기·범위
- 후속·연결
  - [03-test-doubles](../03-test-doubles/2-summary.md) — Fake·Stub·Mock의 차이와 남용
  - [04-classical-vs-london](../04-classical-vs-london/2-summary.md) — 같은 실험을 학파 관점에서
  - [05-tdd](../05-tdd/2-summary.md) — 테스트를 먼저 쓰는 흐름
  - [11-test-data-and-fixtures](../11-test-data-and-fixtures/2-summary.md) · [12-test-smells-and-xunit-patterns](../12-test-smells-and-xunit-patterns/2-summary.md) — 준비 코드와 스멜
  - [15-mutation-testing](../15-mutation-testing/2-summary.md) — 회귀 방지 기둥을 재는 방법
  - [software-design/13-refactoring](../../software-design/13-refactoring/2-summary.md) — 리팩터링의 안전망으로서의 테스트
  - [software-design/02](../../software-design/02-modularity-coupling-cohesion/2-summary.md) — 결합도
- 교재·문서
  - Vladimir Khorikov, 『Unit Testing Principles, Practices, and Patterns』(Manning, 2020) — 3장 "The anatomy of a unit test"(3.1 AAA, 3.4 naming, 3.5 parameterized), 4장 "The four pillars of a good unit test"(4.1~4.5 절 제목 확인), 5장 "Mocks and test fragility" <https://livebook.manning.com/book/unit-testing/chapter-4/>
  - Khorikov, "False positives vs. flaky tests"(2020-02-11) — 거짓 양성·거짓 음성과 기둥의 대응 <https://khorikov.org/posts/2020-02-11-false-positives-flaky-tests/>
  - talon.one 블로그 "How to assess the value of a unit test" — 네 기둥 곱셈 가치 모델 요약(2차 출처) <https://www.talon.one/blog/how-to-assess-the-value-of-a-unit-test>
  - 2차 요약: binaryphile "Khorikov Unit Testing Guide"(2026, 리팩터링 내성 "non-negotiable") <http://www.binaryphile.com/testing/go/software-engineering/2026/01/07/khorikov-unit-testing-guide.html> · gniemann 리뷰(네 기둥 정의) <https://gist.github.com/gniemann/adaf12895c22eb5c11c0591f8cb5952c> · dzx.fr 요약(관찰 가능한 동작 = "immediate connection to the client's goals") <https://dzx.fr/blog/unit-testing-principles-practices-patterns/>
  - 『Software Engineering at Google』 12장 "Unit Testing" — brittle test 정의, 변경 네 종류, Test via Public APIs, Test State Not Interactions, Test Behaviors Not Methods, Don't Put Logic in Tests, Write Clear Failure Messages, DAMP Not DRY, 각주 6(arrange·act·assert) <https://abseil.io/resources/swe-book/html/ch12.html>
  - 같은 책 13장 "Test Doubles" — Prefer Realism Over Isolation, 상호작용 검증은 상태 변경 함수에만 <https://abseil.io/resources/swe-book/html/ch13.html>
  - Gerard Meszaros, xunitpatterns.com "Four-Phase Test"(책 358쪽) <http://xunitpatterns.com/Four%20Phase%20Test.html>
- 실험 목록
  - 같은 주문 코드에 D(구현 세부 6개)·C(관찰 가능한 결과 6개) 묶음, 변경 6종(R1·R2 리팩터링, B1~B4 버그) 각각에서 깨진 테스트 수 — eclipse-temurin:21-jdk(21.0.12) 컨테이너, javac로 테스트 파일별 컴파일 + JUnit Console Launcher 1.13.4, Mockito 5.18.0, AssertJ 3.27.4
