# testing/04-classical-vs-london — 고전파 vs 런던파: 상태 검증과 상호작용 검증 — 정리 (힌트)

## 해결하는 문제

"단위 테스트"라는 같은 말을 두 팀이 다르게 쓴다.\
한 팀은 클래스마다 협력 객체를 전부 mock으로 바꾸고, 다른 팀은 진짜 객체를 묶어서 결과만 본다.\
두 방식은 **어떤 결함을 잡고, 어떤 변경에 깨지는지**가 다르다. 기준 없이 섞으면 두 단점을 다 얻는다.

```text
  같은 OrderService를 테스트한다

  고전파(Detroit)                         런던파(London, mockist)
  OrderService ──> PriceCalculator(진짜)   OrderService ──> PriceCalculator(mock)
                   └─> DiscountPolicy(진짜)                 (계산은 stub이 대답)
               ──> OrderRepository(Fake)               ──> OrderRepository(mock)
               ──> Notifier(기록용 대역)                ──> Notifier(mock)
  확인: 저장된 주문의 총액 = 90,000        확인: repo.save(Order(…, 90,000))가 호출됐다
```

쉬운 예: 식당 주방 점검.
- 한 점검관은 완성된 요리의 맛과 온도를 본다(결과).
- 다른 점검관은 요리사가 "소금 → 후추 → 불 줄이기" 순서로 했는지 체크리스트로 본다(과정).
- 레시피를 바꿔 같은 맛을 내면, 두 번째 점검관만 "불합격"을 준다. 반대로 소금 업체가 짠맛 단위를 바꾸면, 체크리스트는 통과하는데 요리는 짜다.

똑같은 구조다.\
결과를 보는 쪽이 고전파(상태 검증), 과정을 보는 쪽이 런던파(상호작용 검증)다.

## 동작·원리

### 1. 이름과 정의 — 출처별로

- Fowler "Mocks Aren't Stubs"(마지막 큰 개정 2007-01-02)
  - *상태 검증(state verification)*: 실행 뒤 SUT와 협력 객체의 상태를 보고 맞는지 판단한다.
  - *행위 검증(behavior verification)*: SUT가 협력 객체를 올바르게 호출했는지 확인한다.
  - *고전파(classical) TDD*: "use real objects if possible and a double if it's awkward to use the real thing."
  - *mockist TDD*: "will always use a mock for any object with interesting behavior."
  - 이름의 유래(원문 요지): XP가 Detroit의 C3 프로젝트에서 시작돼 고전파를 "Detroit", mockist 스타일이 London의 초기 XP 실천가들에게서 나와 "London"이라 부른다.
- Khorikov 『Unit Testing PPP』 2장 "What is a unit test?"
  - 단위 테스트의 세 속성(2.1 원문): "Verifies a small piece of code (also known as a unit), Does it quickly, And does it in an isolated manner."
  - 두 학파의 차이는 **"격리"를 무엇으로 읽느냐**에서 나온다(2.2·2.3 절 제목 확인, 표 내용은 2차 요약 srikanth.sastry.name·dzx.fr로 확인 — dzx.fr: 런던파는 "mutable dependencies, including classes of your own"을 mock으로 바꾼다).

| | 고전파 | 런던파 |
|---|---|---|
| 무엇을 격리하나 | 테스트끼리(서로 영향 없게) | 단위끼리(SUT를 협력 객체에서) |
| 단위는 | 동작 단위(클래스 여럿일 수 있음) | 클래스 하나(때로 메서드) |
| 대역을 쓰는 곳 | 공유 의존(DB·파일 시스템 등 테스트끼리 공유하는 것) | 변경 가능한 의존 전부 |

- *공유 의존(shared dependency)*: 여러 테스트가 함께 접근해 서로의 결과에 영향을 줄 수 있는 의존. 예: 데이터베이스, 파일 시스템, 정적 가변 필드.
- 용어 주의: "mock"의 뜻이 저자마다 다르다. Fowler·Meszaros의 Mock은 "기대 호출을 미리 프로그램한 대역"이고, mock 프레임워크(Mockito)의 `mock()`은 stub·spy 용도로도 쓰인다. 자세한 분류는 [03](../03-test-doubles/2-summary.md).

### 2. 호출 그림 — 무엇이 진짜이고 무엇이 대역인가

```text
  의존 그래프                        고전파 테스트가 실행하는 것     런던파 테스트가 실행하는 것
  OrderService                      OrderServiceTest:              OrderServiceLondonTest:
    ├─> PriceCalculator               Service + Calculator +         Service 만
    │     └─> DiscountPolicy          Policy (Fake 저장소)           (나머지는 mock)
    ├─> OrderRepository  [밖]       PriceCalculatorTest:           PriceCalculatorLondonTest:
    └─> Notifier         [밖]         Calculator + Policy            Calculator 만
                                    DiscountPolicyTest: Policy     DiscountPolicyTest: Policy
```

- 고전파에서 `DiscountPolicy`의 결함은 그 정책을 **실행하는 모든 테스트**에서 빨강이 된다(파급, ripple).
- 런던파에서는 **그 클래스의 테스트만** 빨강이 된다(국소화).
- 런던파에서 클래스 사이의 "약속"(정책이 무엇을 돌려주나)은 stub의 반환값으로 테스트 코드에 새겨진다. 실제 클래스가 약속을 바꾸면 테스트는 모른다.

### 3. 논쟁의 축 — Fowler의 정리

| 축 | 런던파(mockist) 쪽 | 고전파 쪽 |
|---|---|---|
| TDD 진행 | 바깥(UI·인터페이스 객체)부터 안으로. 협력 객체에 대한 기대를 적으며 그 인터페이스를 설계("need-driven development", outside-in) | 도메인 모델부터 바깥으로(middle-out) |
| 픽스처 | 협력 객체를 다 만들 필요가 없다 | 진짜 객체 그래프를 만들어야 한다. Object Mother 등으로 재사용 |
| 실패 격리 | 결함이 그 클래스 테스트에만 나타난다 | 많이 쓰이는 객체의 결함은 "a ripple of failing tests"를 만든다. 고전파의 답: 자주 돌리면 방금 고친 곳이 원인이라 찾기 어렵지 않다 |
| 구현 결합 | "Mockist tests are thus more coupled to the implementation of a method." 협력 객체 호출 방식이 바뀌면 깨진다 | 최종 상태만 보므로 리팩터링에 강하다 |
| 설계 경향 | Tell Don't Ask, role interface, collecting parameter를 선호 | 상태 확인용 질의 메서드를 허용 |

- 저자들의 입장(주장)
  - Fowler: "Personally I've always been a old fashioned classic TDDer and thus far I don't see any reason to change."
  - SWE@G 13장: mockist 스타일은 Google에서 "difficult to scale"했다. 대부분의 엔지니어가 고전파에 맞는 방식으로 코드를 쓴다. "Prefer Realism Over Isolation".
  - Khorikov: 고전파 편이다. mock은 관리하지 않는(unmanaged) 프로세스 밖 의존에만 쓰라고 한다(2차 요약: "You should replace unmanaged dependencies by mocks").
  - 런던파의 대표 논문: Freeman·Pryce·Mackinnon·Walnes, "Mock Roles, not Objects"(OOPSLA 2004). mock 객체를 처음 소개한 원 논문은 그 앞의 Mackinnon·Freeman·Craig, "Endo-Testing: Unit Testing with Mock Objects"(XP2000)다(이 논문의 참고문헌 [10]). mock은 객체가 맡는 **역할**을 찾아내 타입을 설계하는 기법이라고 본다. GOOS(Freeman·Pryce 2009) 8장 "Building on Third-Party Code"는 "자기가 소유한 타입만 mock하라"고 하며, 외부 라이브러리는 어댑터로 감싸라고 한다.

### 실험: 같은 코드, 두 학파의 테스트 묶음

[02](../02-good-unit-tests/2-summary.md)와 같은 주문 코드와 변경 6종이다. 여기서는 L(런던파)과 C(고전파)를 비교한다. 각 6개.

```java
// L — 런던파: 협력 객체 DiscountPolicy를 mock으로
DiscountPolicy policy = mock(DiscountPolicy.class);
PriceCalculator calc = new PriceCalculator(policy);
@Test void 할인율을_적용한다() {
    when(policy.discountRate(100_000)).thenReturn(10L);
    assertThat(calc.total(List.of(new OrderLine("A", 5, 20_000)))).isEqualTo(90_000);
}
// L — OrderService: 모든 협력 객체를 mock으로, 프로세스 밖으로 나가는 명령만 verify
@Test void 계산된_총액으로_저장한다() {
    when(calc.total(lines)).thenReturn(90_000L);
    service.place("o-1", lines);
    verify(repo).save(new Order("o-1", lines, 90_000));
}

// C — 고전파: 진짜 정책·계산기, 저장소는 인메모리 Fake
PriceCalculator calc = new PriceCalculator(new DiscountPolicy());
@Test void 경계에서_할인이_적용된다() {
    assertThat(calc.total(List.of(new OrderLine("A", 5, 20_000)))).isEqualTo(90_000);
}
```

(실험, JDK 21.0.12 temurin · JUnit Platform 1.13.4 · AssertJ 3.27.4 · Mockito 5.18.0 `mock()` 기본 설정, 2026-10-03)

```text
R1 L 전체=6 통과=6 실패=0 |
R1 C 전체=6 통과=6 실패=0 |
R2 L 전체=6 통과=4 실패=2 | PriceCalculatorLondonTest:할인율을_적용한다() PriceCalculatorLondonTest:수량을_곱한다()
R2 C 전체=6 통과=6 실패=0 |
B1 L 전체=6 통과=5 실패=1 | DiscountPolicyTest:소계_100000부터_10퍼센트()
B1 C 전체=6 통과=2 실패=4 | OrderServiceTest:주문이_할인된_총액으로_저장된다() OrderServiceTest:고객에게_총액이_통지된다() PriceCalculatorTest:경계에서_할인이_적용된다() DiscountPolicyTest:소계_100000부터_10퍼센트()
B2 L 전체=6 통과=4 실패=2 | PriceCalculatorLondonTest:할인율을_적용한다() PriceCalculatorLondonTest:수량을_곱한다()
B2 C 전체=6 통과=2 실패=4 | OrderServiceTest:… ×2  PriceCalculatorTest:수량을_곱한다() PriceCalculatorTest:경계에서_할인이_적용된다()
B3 L 전체=6 통과=5 실패=1 | OrderServiceLondonTest:계산된_총액으로_저장한다()
B3 C 전체=6 통과=5 실패=1 | OrderServiceTest:주문이_할인된_총액으로_저장된다()
B4 L 통과=6 실패=0 |
B4 C 통과=3 실패=3 | OrderServiceTest:… ×2  PriceCalculatorTest:경계에서_할인이_적용된다()
```

R2(할인 적용을 `DiscountPolicy.apply`로 위임)에서 L이 낸 메시지:

```text
PriceCalculatorLondonTest ✔
   ├─ 할인율을_적용한다() ✘   expected: 90000L  but was: 0L
   └─ 수량을_곱한다() ✘       expected: 60000L  but was: 0L
```

- 변경 요약: R1 = `subtotal()` 도우미 인라인, R2 = 할인 적용을 `apply`로 위임(리팩터링). B1 = 경계 `>=`→`>`, B2 = 수량 누락, B3 = 저장 누락, B4 = 정책이 할인율을 ‰로 바꾸고 자기 테스트도 고침(계산기는 `/100` 그대로).

| | L(런던파) | C(고전파) |
|---|---|---|
| 리팩터링 2건의 거짓 양성 | 2개(R2) | 0개 |
| 버그 4건 중 잡은 것 | 3건(B4 놓침) | 4건 |
| 버그 1건당 빨강 개수 | 1~2개 — 결함 클래스의 테스트만 | 1~4개 — 결함을 실행하는 테스트 전부 |

- 관찰
  - **R2의 "but was: 0L"**: mock `DiscountPolicy`의 `apply`는 stub하지 않았다. Mockito 5.18의 `mock()` 기본 응답(`RETURNS_DEFAULTS` → 전역 설정 기본값 `ReturnsEmptyValues`, `DefaultMockitoConfiguration` 소스)은 원시 타입 메서드에 0을 돌려준다(소스 javadoc: "Returns appropriate primitive for primitive-returning methods"). 계산기가 새 메서드를 부르자 0이 나왔다. 동작은 그대로인데 테스트가 깨졌다.
  - **B1의 국소화**: L은 `DiscountPolicyTest` 하나만 빨개져 원인이 바로 보인다. C는 4개가 빨개졌지만, 모두 `DiscountPolicy`를 실행한다는 공통점을 따라가면 같은 곳에 닿는다(Fowler가 전하는 고전파의 반론).
  - **B4의 초록**: L에서 계산기 테스트는 "정책은 10을 준다"는 stub을 믿는다. 정책이 100을 주도록 바뀌어도 모른다. C는 10만 원 주문이 0원이 되는 것을 잡았다.
  - B3(저장 누락)은 둘 다 잡았다. 저장소는 프로세스 밖 의존이라 두 학파 모두 대역(L은 mock `verify`, C는 Fake 상태 확인)으로 검증한다.
- 한계: 내가 만든 작은 코드·테스트 6개씩이다. 기제를 보이는 예이지 일반 비율이 아니다. 런던파 실천가는 B4 같은 틈을 인수 테스트(바깥 루프)로 메운다고 말한다([06](../06-outside-in-tdd-and-acceptance-tests/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **의존 그래프와 역방향 도달성.** 고전파에서 결함 노드 X가 있으면, 빨강이 될 수 있는 테스트 = "SUT에서 진짜 객체 간선을 따라 X에 도달하는 테스트"다. 그중 결함을 드러내는 입력을 실제로 지나는 테스트가 빨강이 된다.
  - 실험 B1: C의 6개 모두 `DiscountPolicy`에 도달한다. 그중 경계값 100,000을 지나는 4개가 빨강, 소계 99,999·60,000을 쓰는 2개는 초록이었다.
  - 런던파는 SUT에서 나가는 간선을 모두 대역으로 끊는다. 도달 집합이 SUT 자신뿐이라 빨강도 그 클래스 테스트뿐이다.
- **단위 경계 = 그래프 절단.** 고전파는 "프로세스 밖·공유 의존" 간선만 끊는다. 런던파는 "변경 가능한 의존" 간선을 전부 끊는다. 끊은 간선마다 stub 반환값이라는 **가정**이 테스트에 하나씩 생긴다.
- **stub = 조회 테이블.** `when(policy.discountRate(100_000)).thenReturn(10L)`은 입력→출력 맵이다. 맵에 없는 호출은 기본값(0·빈 컬렉션·null 등)을 돌려준다. 실제 구현과 맵이 어긋나도 테스트는 알 수 없다.

## 적용 — 풀어나가는 법

1. **기본은 고전파로 쓴다.** 같은 프로세스의 도메인 객체는 진짜를 쓰고 결과를 확인한다(SWE@G 13장 "Prefer Realism Over Isolation", Khorikov).
2. **대역은 이 경우에만.**
   - 느리거나 비결정적인 의존(DB·네트워크·시계) → Fake 또는 중간 테스트([08](../08-integration-tests-real-dependencies/2-summary.md), [10](../10-testing-time-and-concurrency/2-summary.md)).
   - 프로세스 밖으로 나가는 **명령**(메일 발송·결제 요청·메시지 발행) → mock/spy로 호출을 확인한다. 이것은 외부가 관찰하는 결과다.
3. **런던파 기법이 유용한 곳.** 아직 없는 협력 객체의 인터페이스를 바깥에서 안으로 설계할 때(outside-in, [06](../06-outside-in-tdd-and-acceptance-tests/2-summary.md)). 이때도 인수 테스트(바깥 루프)로 조립을 확인한다.
4. **자기가 소유한 타입만 mock한다.** 외부 라이브러리는 어댑터로 감싸고 어댑터를 mock하거나, 어댑터는 실제 의존으로 중간 테스트한다(GOOS).
5. **조회는 stub, 명령만 verify.** 값을 돌려주는 조회 호출을 `verify`하지 않는다. 결과가 이미 그 값을 반영한다.

```java
// 나쁨: 조회까지 verify — 계산 경로가 바뀌면 깨진다
verify(calc).total(lines);

// 좋음: 밖으로 나가는 명령만 verify — 외부가 관찰하는 결과
verify(notifier).orderPlaced("o-1", 90_000);
```

6. **진단: 학파가 섞인 테스트 묶음의 증상 읽기.**
   - 리팩터링마다 `Wanted but not invoked`·`but was: 0` → 내부 협력 객체 mock이 과하다.
   - 단위 테스트 전부 초록, 통합 경로에서만 틀림 → 클래스 사이 계약을 stub이 가리고 있다.

## 장애 시나리오와 대처

### 1. 런던파 과용 — 구현에 고착된 테스트 (⚠)

- **현상**: 메서드를 옮기거나 클래스를 합치는 리팩터링마다 테스트 다수를 다시 써야 한다.
- **보이는 형태**: `Wanted but not invoked`, `expected: 90000L but was: 0L`(stub하지 않은 새 메서드가 기본값 0을 돌려줌 — 실험 R2), `verifyNoMoreInteractions` 위반.
- **원인**: 같은 프로세스의 도메인 협력 객체까지 mock했다. 테스트가 "어떻게 계산하나"에 묶였다.
- **대처**: 도메인 협력 객체는 진짜로 바꾸고 결과를 확인한다. mock은 프로세스 밖 명령에만 남긴다. 한 번에 다 바꾸지 말고 리팩터링이 잦은 모듈부터.

### 2. 모든 단위 초록, 기능은 틀림 — 클래스 사이 계약 불일치

- **현상**: 10만 원 주문이 0원으로 결제됐다(실험 B4). 각 클래스의 테스트는 모두 초록이다.
- **보이는 형태**: 결함은 두 클래스의 **약속**(단위·형식·null 처리) 차이에서 생긴다. 어느 한 클래스만 보면 각자 맞다.
- **원인**: stub이 상대 클래스의 옛 약속을 기억하고 있다.
- **대처**: 실제 객체를 묶는 고전파 테스트 또는 인수 테스트를 둔다. 경계 객체의 대역이면 실제 구현과 같은 계약 테스트를 돌린다([03](../03-test-doubles/2-summary.md), [13](../13-contract-testing/2-summary.md)).

### 3. 고전파의 파급 — 빨강 수십 개에서 원인 찾기

- **현상**: 공용 값 객체(예: `Money`) 하나의 결함으로 테스트 수십 개가 동시에 빨개진다.
- **보이는 형태**: 실패 목록이 여러 모듈에 흩어져 있다.
- **원인**: 그 객체를 실행하는 모든 테스트가 결함을 본다(역방향 도달성).
- **대처**: 실패한 테스트들이 **공통으로 실행하는** 클래스를 찾는다. 가장 작은 범위의 실패(그 클래스 자체의 테스트)부터 본다. 자주 돌리면 방금 바꾼 곳이 원인이다(Fowler가 전하는 고전파의 반론). 이 비용이 크다고 실패를 국소화하려 mock을 늘리면 장애 1·2를 산다.

### 4. 외부 라이브러리를 직접 mock

- **현상**: HTTP 클라이언트·SDK 클래스를 mock했는데, 라이브러리 업그레이드 뒤 운영에서만 실패한다.
- **원인**: 남의 타입의 동작을 내가 추측해 stub에 적었다. 실제 동작이 다르거나 바뀌었다.
- **대처**: 어댑터로 감싸고(자기 소유 타입), 어댑터는 실제 의존 또는 녹화된 응답으로 중간 테스트한다(GOOS "Only mock types that you own").

## 핵심 문장

- 고전파는 결과(상태)를, 런던파는 협력 객체와의 상호작용을 확인한다. 차이는 "격리"를 테스트끼리로 읽느냐, 단위끼리로 읽느냐에서 나온다.
- 런던파는 결함 위치를 좁게 보여 주지만, 내부 호출 방식에 묶여 리팩터링에 깨지고, stub이 클래스 사이 계약 불일치를 가린다.
- 고전파는 리팩터링에 강하고 조립 결함을 잡지만, 결함 하나가 여러 테스트에 퍼진다.
- 실무 기본은 고전파 + 프로세스 밖 명령에만 mock이다. 런던파 기법은 바깥에서 안으로 인터페이스를 설계할 때 쓴다.
- mock은 자기가 소유한 타입에만, `verify`는 밖으로 나가는 명령에만.

## 관련 주제·근거

- 선행
  - [03-test-doubles](../03-test-doubles/2-summary.md) — Dummy·Fake·Stub·Spy·Mock
  - [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 같은 실험의 구현 세부 vs 관찰 가능한 결과 비교
- 후속
  - [05-tdd](../05-tdd/2-summary.md) · [06-outside-in-tdd-and-acceptance-tests](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) — need-driven / outside-in에서 mock의 쓰임
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) · [13-contract-testing](../13-contract-testing/2-summary.md)
  - [software-design/25](../../software-design/25-dependency-injection-and-composition-root/2-summary.md) — 의존 주입, [software-design/38](../../software-design/38-layered-hexagonal-clean/2-summary.md) — 포트와 어댑터
- 문서·논문·교재
  - Martin Fowler, "Mocks Aren't Stubs"(2007-01-02 개정) — 상태/행위 검증, classical vs mockist, Detroit/London 이름, Driving TDD·Fixture Setup·Test Isolation·Coupling Tests to Implementations·Design Style, 저자 입장 <https://martinfowler.com/articles/mocksArentStubs.html>
  - Vladimir Khorikov, 『Unit Testing Principles, Practices, and Patterns』(Manning 2020) 2장 "What is a unit test?" — 2.1 정의(원문 확인), 2.2·2.3 두 학파 비교(절 제목 확인) <https://livebook.manning.com/book/unit-testing/chapter-2/>
  - 2차 요약 — Srikanth Sastry "Defining unit tests: two schools of thought"(학파별 단위·대역 범위) <https://srikanth.sastry.name/defining-unit-tests-two-schools-of-thought/> · dzx.fr 요약("replace unmanaged dependencies by mocks") <https://dzx.fr/blog/unit-testing-principles-practices-patterns/>
  - 『Software Engineering at Google』 13장 "Test Doubles" — classical vs mockist("difficult to scale"), Prefer Realism Over Isolation, 상호작용 검증 지침 <https://abseil.io/resources/swe-book/html/ch13.html>
  - Freeman·Pryce·Mackinnon·Walnes, "Mock Roles, not Objects", OOPSLA 2004 Companion <https://jmock.org/oopsla2004.pdf>
  - Freeman·Pryce, 『Growing Object-Oriented Software, Guided by Tests』(2009) 8장 "Building on Third-Party Code"(절: Only Mock Types That You Own, Mock Application Objects in Integration Tests) — 자기 소유 타입만 mock, 어댑터 <https://growing-object-oriented-software.com/toc.html>
  - Mockito 5.18.0 소스 `ReturnsEmptyValues` javadoc — 기본 응답(원시 타입 0, 빈 컬렉션·Optional·Stream, 그 밖 null) <https://github.com/mockito/mockito/blob/v5.18.0/mockito-core/src/main/java/org/mockito/internal/stubbing/defaultanswers/ReturnsEmptyValues.java>
- 실험 목록
  - 같은 주문 코드에 L(런던파 6개)·C(고전파 6개) 묶음, 변경 6종(R1·R2 리팩터링, B1~B4 버그)에서 빨강 테스트 수와 위치 — eclipse-temurin:21-jdk(21.0.12) 컨테이너, 테스트 파일별 javac + JUnit Console Launcher 1.13.4, Mockito 5.18.0(`mock()` 기본 설정), AssertJ 3.27.4
