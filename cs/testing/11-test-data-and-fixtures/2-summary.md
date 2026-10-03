# testing/11-test-data-and-fixtures — 픽스처·빌더·오브젝트 마더·격리 — 정리 (힌트)

## 해결하는 문제

테스트는 "알려진 상태"에서 시작해야 결과를 판정할 수 있다. 그 상태를 만드는 코드가 테스트의 절반을 차지하고, 잘못 만들면 테스트끼리 얽힌다.

```text
  문제 1: 준비가 길다         new Order(new Customer(..., new Address(...)), List.of(new Line(...), ...), ...)
                               → 이 테스트가 무엇을 보는지 묻힌다
  문제 2: 같이 쓰면 얽힌다    테스트 A가 재고 4개 예약 → 테스트 B는 "재고 10개"를 기대
                               → 실행 순서에 따라 B가 통과·실패
  문제 3: 바꾸면 번진다       생성자에 인자 하나 추가 → 테스트 수십 개 컴파일 오류
```

- *픽스처(test fixture)*: 테스트를 실행하기 전의 환경 상태. Meszaros: "This defines the state of the test environment before the test."(xunitpatterns.com "Fresh Fixture"). 객체·DB 행·파일·설정을 모두 포함한다.
- *SUT*: 시험 대상. 픽스처는 SUT와 그 주변을 준비한다.

쉬운 예: 요리 실습실.
- 조마다 깨끗한 도마·새 재료를 받으면(새 픽스처) 앞 조가 뭘 했든 상관없다.
- 냉장고 하나를 다 같이 쓰면(공유 픽스처) 앞 조가 달걀을 다 쓴 날 뒤 조가 실패한다. 순서가 바뀌면 실패하는 조도 바뀐다.

똑같은 구조다.\
테스트마다 새 상태를 만드는 비용과, 상태를 공유해 얽히는 위험 사이에서 고른다.

실무 예:
- 통합 테스트들이 같은 DB 스키마를 쓰는데, 한 테스트가 남긴 행 때문에 다른 테스트의 `count()` 단언이 가끔 깨진다.
- `TestFixtures.standardOrder()`를 50개 테스트가 쓰는데, 한 테스트 때문에 그 값을 바꿨더니 다른 테스트가 깨진다.
- 엔티티에 필수 필드가 생겨 테스트 파일 수십 개를 고친다.

## 동작·원리

### 1. 네 단계 테스트와 픽스처의 수명

```text
   준비(setup) ──▶ 실행(exercise) ──▶ 검증(verify) ──▶ 정리(teardown)
   └ 픽스처를 만든다                                   └ 픽스처를 치운다(필요하면)
```

- Meszaros는 이 네 단계를 *Four-Phase Test*라 부른다. 픽스처는 1단계에서 만들고 4단계에서 치운다.
- 픽스처가 어디에 사느냐가 수명을 정한다(xunitpatterns.com "Fresh Fixture").
  - 지역 변수: 테스트가 끝나면 사라진다.
  - 인스턴스 필드: xUnit 대부분은 테스트 메서드마다 테스트 객체를 새로 만들어 안전하다.
  - 클래스(static) 변수·DB·파일: 테스트가 끝나도 남는다. 다른 테스트가 볼 수 있다.

JUnit 5(Jupiter)의 경우(User Guide 5.13.4 "Test Instance Lifecycle"):
- 기본은 **테스트 메서드마다 테스트 클래스 인스턴스를 새로 만든다**("per-method"). 인스턴스 필드는 테스트마다 새것이다.
- `@TestInstance(Lifecycle.PER_CLASS)`를 붙이면 클래스당 인스턴스 하나다. 테스트가 인스턴스 필드의 바뀌는 상태에 기대면, 그 상태를 `@BeforeEach`나 `@AfterEach`에서 되돌려야 할 수 있다(User Guide 2.12 "you may need to reset that state").
- `@BeforeAll`(기본 모드에서는 `static`)로 만든 객체는 그 클래스의 모든 테스트가 공유한다.
- 메서드 실행 순서의 기본값은 "deterministic but intentionally nonobvious"다(User Guide "Test Execution Order"). 매번 같지만 예측하기 어렵다. `MethodOrderer.Random`과 시드(`junit.jupiter.execution.order.random.seed`)로 순서를 섞을 수 있다.

### 2. 픽스처 전략 — 새것이냐 공유냐, 최소냐 표준이냐

```text
                    테스트마다 새로                 여러 테스트가 공유
                ┌──────────────────────────┬──────────────────────────────┐
   이 테스트에    │ Fresh + Minimal           │ (드묾)                        │
   필요한 만큼만  │ 가장 읽기 쉽고 얽히지 않음  │                              │
                ├──────────────────────────┼──────────────────────────────┤
   모든 테스트용  │ Fresh + Standard          │ Shared + Standard             │
   표준 세트     │ 안 얽히지만 무엇을 보는지   │ 빠르지만 얽힌다(Interacting    │
                │ 흐려진다(General Fixture)  │ Tests), 고치기 무섭다          │
                └──────────────────────────┴──────────────────────────────┘
```

- *Fresh Fixture*: "Each test constructs its own brand-new test fixture for its own private use."
- *Shared Fixture*: "We reuse the same instance of the test fixture across many tests." 느린 준비(DB 등)를 아끼려고 쓴다.
  - 가장 큰 문제(Meszaros): 테스트 간 "collisions" → *Erratic Test*. 하위 원인이 *Interacting Tests*(한 테스트가 다른 테스트의 결과에 기댄다)다.
  - 완화책: 공유하되 아무도 고치지 않는 *Immutable Shared Fixture*. Meszaros는 Fresh가 너무 느릴 때 Shared보다 이것을 먼저 고려하라고 한다.
- *Minimal Fixture*: "Use the smallest and simplest fixture possible for each test."
- *Standard Fixture*: 여러 테스트가 같은 설계의 픽스처를 쓴다. 많은 테스트를 섬기다 보면 한 테스트에 필요한 것보다 커지고, 그 테스트가 무엇에 기대는지 안 보인다(*General Fixture*·*Obscure Test* 스멜, 12번 노트).

### 실험 A: 공유 픽스처 → 순서에 따라 통과·실패

```java
/** 공유 픽스처: @BeforeAll로 클래스당 한 번 만든 static 객체를 모든 테스트가 같이 쓴다 */
class SharedFixtureSpec {
    static Inventory INV;
    @BeforeAll static void setUpOnce() { INV = new Inventory(10); }
    @Test void reserveFour()        { assertThat(INV.reserve(4)).isTrue(); }
    @Test void reserveFive()        { assertThat(INV.reserve(5)).isTrue(); }
    @Test void nothingReservedYet() { assertThat(INV.available()).isEqualTo(10); }
}
/** 새 픽스처: 인스턴스 필드 — 테스트 메서드마다 새 인스턴스 */
class FreshFixtureSpec {
    final Inventory inv = new Inventory(10);
    // 같은 세 테스트, INV 대신 inv
}
```

JUnit Platform Launcher로 두 클래스를 기본 순서 1회, `MethodOrderer.Random` 시드 1~20으로 20회씩 돌렸다.

(실험, maven:3.9-eclipse-temurin-21 이미지 — Maven 3.9.16 · JDK 21.0.11 · JUnit 5.13.4 · junit-platform-launcher 1.13.4 · AssertJ 3.27.3, 2026-10-03)

```text
DEFAULT SharedFixtureSpec: reserveFive → reserveFour → nothingReservedYet✗
SWEEP SharedFixtureSpec: 20회 중 실패한 실행 12
  4회  nothingReservedYet → reserveFive → reserveFour
  4회  nothingReservedYet → reserveFour → reserveFive
  2회  reserveFive → nothingReservedYet✗ → reserveFour
  5회  reserveFive → reserveFour → nothingReservedYet✗
  3회  reserveFour → nothingReservedYet✗ → reserveFive
  2회  reserveFour → reserveFive → nothingReservedYet✗
DEFAULT FreshFixtureSpec: reserveFive → reserveFour → nothingReservedYet
SWEEP FreshFixtureSpec: 20회 중 실패한 실행 0
  4회  nothingReservedYet → reserveFive → reserveFour
  4회  nothingReservedYet → reserveFour → reserveFive
  2회  reserveFive → nothingReservedYet → reserveFour
  5회  reserveFive → reserveFour → nothingReservedYet
  3회  reserveFour → nothingReservedYet → reserveFive
  2회  reserveFour → reserveFive → nothingReservedYet
```

- 관찰: 공유 픽스처는 `nothingReservedYet`이 맨 앞일 때(8회)만 통과했고, 나머지 12회는 실패했다. 새 픽스처는 같은 순서들에서 0회 실패.
- 기본 순서에서는 공유 판이 실패했다. 기본 순서는 결정적이라 매번 같은 결과가 나온다. 그래서 **테스트 이름을 바꾸거나 테스트를 하나 추가해 순서가 바뀌는 순간** 갑자기 통과·실패가 뒤집힐 수 있다(기본 순서 알고리즘은 문서가 명시하지 않는다).
- 해석: 실패한 테스트(`nothingReservedYet`) 자체에는 잘못이 없다. 원인은 **앞서 실행된 다른 테스트**다. 실패 위치와 원인 위치가 다르다는 점이 공유 픽스처 장애를 디버깅하기 어렵게 만든다.

### 3. 테스트 데이터를 만드는 세 방법

```text
   Creation Method (Meszaros)       Object Mother (Fowler 2006)       Test Data Builder (Pryce 2007)
   newOrderWithVip()                Orders.regular()                  anOrder().vip().withLines(1000, 1000).build()
   의도를 드러내는 이름의 생성 함수   이름 붙은 표준 객체 모음            안전한 기본값 + 바꿀 것만 with*
                                   변형이 필요할 때마다 메서드 추가     변형은 그 테스트 안에서
```

- *Creation Method*: "Set up the test fixture by calling methods that hide the mechanics of building ready-to-use objects behind Intent Revealing Names."(xunitpatterns.com)
- *Object Mother*: "a kind of class used in testing to help create example objects that you use for testing."(Fowler bliki, 2006-10-24). ThoughtWorks 프로젝트에서 나온 이름이고, Schuh·Punke가 XP Universe 논문으로 썼다.
  - Fowler가 든 약점: "many tests will depend on the exact data in the mothers."
- *Test Data Builder*: Nat Pryce, "Test Data Builders: an alternative to the Object Mother pattern"(2007-08-27). GOOS 22장 "Constructing Complex Test Data"에도 같은 패턴이 있다. 빌더는
  - 생성자 인자마다 필드를 하나씩 갖고,
  - 그 필드를 "commonly used or safe values"로 초기화하고,
  - `build()`로 객체를 만들고,
  - 값을 덮어쓰는 연쇄 가능한 `with*` 메서드를 둔다.
  - Pryce가 든 이점: "You can add constructor arguments without breaking tests at all." Object Mother는 "does not cope at all well with variation in the test data"라고 썼다.
- SWE@G 12장 "Shared Values"도 같은 방향이다. 테스트 작성자가 신경 쓰는 값만 지정하고 나머지는 합리적인 기본값을 주는 헬퍼를 쓰라고 하고, 이름 있는 인자가 없는 언어에서는 빌더로 흉내 내라고 한다. 같은 장의 원칙은 "DAMP, Not DRY" — 테스트에서는 약간의 중복이 읽기 쉬움을 위해 괜찮다.

### 실험 B: 생성자에 인자를 하나 더하면 — 세 방식의 고칠 자리

같은 테스트 6개를 세 방식(생성자 직접 호출·Object Mother·Test Data Builder)으로 썼다. `Order`에 `String currency` 인자를 추가하고 각 방식을 `javac`로 컴파일했다.

```java
// 변경: record Order(String customerId, Grade grade, List<Long> linePrices)
//   →   record Order(String customerId, Grade grade, List<Long> linePrices, String currency)

class OrderBuilder {  // Test Data Builder: 안전한 기본값 + with* + build
    private String customerId = "c1";
    private Order.Grade grade = REGULAR;
    private List<Long> lines = List.of(1000L);
    static OrderBuilder anOrder() { return new OrderBuilder(); }
    OrderBuilder withCustomer(String id) { customerId = id; return this; }
    OrderBuilder vip() { grade = VIP; return this; }
    OrderBuilder withLines(Long... prices) { lines = List.of(prices); return this; }
    Order build() { return new Order(customerId, grade, lines); }
}
```

```text
(실험, eclipse-temurin:21-jdk 이미지 — JDK 21.0.12 javac, JUnit 5.13.4 · AssertJ 3.27.3 클래스패스, 2026-10-03)
## 변경 1: 생성자 인자 currency 추가 직후
direct: 컴파일 오류 6개  [direct/DirectTest.java ]
mother: 컴파일 오류 3개  [mother/Orders.java ]
builder: 컴파일 오류 1개  [builder/OrderBuilder.java ]
## 빌더 1곳·마더 3곳 고친 뒤
direct: 컴파일 오류 6개  [direct/DirectTest.java ]
mother: 컴파일 오류 0개  []
builder: 컴파일 오류 0개  []
```

- 직접 호출은 테스트마다 1곳씩 6곳, 마더는 팩터리 메서드 수만큼 3곳, 빌더는 `build()` 1곳이었다. 테스트 본문은 마더·빌더 모두 0곳.
- 테스트 수가 늘면 직접 호출의 고칠 자리는 테스트 수에 비례한다. 빌더는 그대로 1곳이다(이 6개 예시에서의 측정).

### 실험 C: 마더의 표준 데이터를 바꾸면

새 테스트가 "3줄짜리 일반 주문"을 필요로 해서, 개발자가 `Orders.regular()`에 한 줄(500원)을 더했다. 빌더 쪽은 새 테스트 안에서 `withLines(1000L, 2000L, 500L)`로 썼다.

```text
(실험, maven:3.9-eclipse-temurin-21 이미지 — 같은 버전들, 2026-10-03)
[INFO] Tests run: 6, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.277 s -- in fx.BuilderTest
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.006 s -- in fx.BuilderNewTest
[ERROR] Tests run: 6, Failures: 2, Errors: 0, Skipped: 0, Time elapsed: 0.212 s <<< FAILURE! -- in fx.MotherTest
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.058 s -- in fx.MotherNewTest
[ERROR]   MotherTest.regularHasTwoLines:9 
[ERROR]   MotherTest.sumsLines:5 
[ERROR] Tests run: 14, Failures: 2, Errors: 0, Skipped: 0
```

- 마더를 쓰던 기존 테스트 6개 중 `regular()`의 정확한 값(합계 3000·2줄)에 기대던 2개가 깨졌다. Fowler가 말한 결합("depend on the exact data in the mothers")이 그대로 나왔다.
- 빌더 쪽 기존 테스트는 0개 깨졌다. 변형이 그 테스트 안에만 있기 때문이다.
- 반대 상황(공정하게): 마더도 고칠 자리를 모은다(실험 B에서 3곳). 변형이 거의 없고 이름 붙은 "대표 객체"가 업무 대화에 쓰인다면 마더가 읽기 쉽다. 손해가 나는 쪽은 변형이 자주 생기는 경우다.

### 4. 영속 픽스처의 격리 — DB를 쓰는 테스트

```text
   방법                         되돌리는 방식                        주의
   ───────────────────────────────────────────────────────────────────────────────
   트랜잭션 롤백                 테스트 끝에 rollback                 SUT가 자기 트랜잭션을 커밋하면 안 됨
   테스트별 고유 키              주문번호·이메일에 고유 접미사          남은 행은 쌓인다(주기 정리)
   테이블 비우기(TRUNCATE·DELETE) 테스트 전·후에 지움                  병렬 실행이면 서로 지운다
   테스트별 DB·스키마·컨테이너    통째로 새로                           느리다
```

- Meszaros는 DB에 들어간 픽스처는 테스트가 끝나도 "hang around"해서, 같은 테스트의 다음 실행(*Unrepeatable Test*)이나 다른 테스트(*Interacting Tests*, *Test Run War*)와 충돌할 수 있다고 쓴다(xunitpatterns.com "Fresh Fixture").
  - *Test Run War*: 같은 공유 자원을 쓰는 여러 사람·여러 CI 작업의 테스트 실행이 서로를 깨는 것.
- 실제 DB 컨테이너를 쓰는 통합 테스트는 08번 노트, 트랜잭션 경계는 database [24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **테스트 데이터 빌더 = 기본값 레코드 + 덮어쓰기**: 필드마다 기본값을 갖고, `with*`가 한 필드만 바꾼다. 결과 객체가 불변 값이면 빌더 하나에서 여러 변형을 안전하게 찍어 낼 수 있다. software-design [19-immutability-and-value-objects](../../software-design/19-immutability-and-value-objects/2-summary.md), Builder 패턴은 [27-design-patterns-gof](../../software-design/27-design-patterns-gof/2-summary.md).
- **픽스처 수명 = 범위(scope)의 중첩**: 클래스 범위(`@BeforeAll`) 안에 메서드 범위(`@BeforeEach`)가 들어 있다. 준비는 바깥에서 안으로, 정리는 안에서 바깥으로(스택 순서).
- **순서 섞기 = 무작위 순열 + 시드**: 같은 시드면 같은 순열이 나온다. 실패한 시드를 기록해 두면 그 순서를 재현할 수 있다.
- **DB 롤백 격리 = 트랜잭션의 원자성**: 테스트 하나를 트랜잭션 하나로 감싸고 되돌린다.

## 적용 — 풀어나가는 법

### 1. 실무 순서

1. 기본은 **Fresh + Minimal**: 테스트 안에서, 그 테스트에 필요한 것만 만든다.
2. 만드는 코드가 길면 빌더나 생성 함수로 뺀다. 테스트 본문에는 **이 테스트에 중요한 값만** 보이게 한다.
3. 공유가 꼭 필요하면(느린 준비) 아무도 고치지 않는 **불변 공유 픽스처**로 만든다. 고쳐야 하는 데이터는 테스트마다 따로 만든다.
4. DB 테스트는 롤백·고유 키·테스트별 스키마 중 하나로 테스트마다 격리한다.
5. CI에서 가끔 순서를 섞어 돌려 숨은 순서 의존을 찾는다.

### 2. 빌더를 쓰는 테스트

```java
@Test void vipGetsFivePercentOff() {
    Order order = anOrder().vip().withLines(1000L, 1000L).build();   // 중요한 값만 보인다
    assertThat(order.total()).isEqualTo(1900);
}
```

- `customerId` 같은 무관한 값은 빌더 기본값에 맡긴다. 반대로 결과를 좌우하는 값은 기본값에 기대지 말고 테스트에 적는다. SWE@G 12장: 특정 값에 기대는 테스트는 그 값을 직접 적어야 한다("should state those values directly").

### 3. 진단 — 숨은 순서 의존 찾기

```bash
# JUnit Jupiter: 메서드 순서를 섞어 돌린다(시드를 바꿔 여러 번)
mvn test -Djunit.jupiter.testmethod.order.default='org.junit.jupiter.api.MethodOrderer$Random' \
         -Djunit.jupiter.execution.order.random.seed=7
# Surefire: 테스트 클래스 순서를 섞는다(기본값 filesystem). 실패하면 출력된 시드로 재현
mvn test -Dsurefire.runOrder=random -Dsurefire.runOrder.random.seed=7
# 공유 상태 후보 찾기: 테스트 코드의 변경 가능한 static 필드
grep -rnE 'static [A-Z][A-Za-z<>]* [A-Za-z_]+ *(=|;)' src/test/java | grep -v final
```

- 첫 명령은 실험 A의 공유 픽스처 클래스(`-Dtest=SharedFixtureSpec`)에 직접 돌려 확인했다. 시드 2·6은 `Tests run: 3, Failures: 0`, 시드 1·3은 `Failures: 1`(`nothingReservedYet`)로, Launcher 실험의 같은 시드 결과와 일치했다(Maven 명령줄 `-D` 값이 포크된 테스트 JVM의 JUnit 설정으로 전달됐다).
- Surefire `runOrder`는 테스트 **클래스** 순서를 정한다. 값은 alphabetical·reversealphabetical·random·failedfirst·balanced·filesystem이고 기본은 filesystem이다(maven-surefire-plugin `test` 목표 문서). `runOrder.random.seed`는 3.0.0-M6부터.
- 혼자 돌리면 통과하고 전체로 돌리면 실패하면 순서 의존을 먼저 의심한다(반대로, 전체에선 통과하고 혼자 돌리면 실패하는 *Lonely Test*도 있다).

## 장애 시나리오와 대처

### 1. 공유 픽스처 → 테스트 순서 의존 (⚠ 커리큘럼)

- 현상: CI에서 가끔 실패하고 로컬 단독 실행에서는 통과한다. 테스트를 하나 추가했을 뿐인데 무관한 테스트가 깨지기 시작했다.
- 보이는 형태: 실험 A처럼 실패 위치(`nothingReservedYet: expected 10`)와 원인(앞서 실행된 `reserveFour`·`reserveFive` — 출력에서 어느 하나만 앞서도 실패했다)이 다르다. 순서를 섞으면 실패율이 드러난다(20회 중 12회).
- 원인: `static`·`@BeforeAll`·DB에 둔 변경 가능한 상태를 여러 테스트가 고친다(Interacting Tests).
- 대처
  - 고치는 상태는 테스트마다 새로 만든다(인스턴스 필드·`@BeforeEach`).
  - 공유해야 하면 불변으로 만들거나, 테스트마다 고유한 키를 쓴다.
  - CI에 순서 섞기 실행을 넣고, 실패 시드를 기록해 재현한다. 순서·시간·동시성 전반의 불안정성은 09번 노트.

### 2. 거대 픽스처 → 무엇을 검증하는지 불명 (⚠ 커리큘럼)

- 현상: 실패한 테스트를 열어 보면 `setUp()`이 100줄이고, 단언 `assertThat(report.total()).isEqualTo(48_300)`의 48,300이 어디서 왔는지 모른다.
- 보이는 형태: 테스트 본문에 입력이 안 보인다(*Mystery Guest*·*General Fixture*·*Obscure Test*, 12번 노트). 원인 파악에 시간이 오래 걸린다.
- 원인: 여러 테스트를 섬기는 표준 픽스처가 커졌고, 각 테스트가 그중 일부에 몰래 기댄다.
- 대처: Minimal Fixture로 줄이고, 결과를 좌우하는 값은 테스트 본문에 드러낸다(빌더의 `with*`). 기대값과 입력의 관계가 보이게 쓴다.

### 3. 오브젝트 마더 데이터 수정 → 무관한 테스트 파손

- 현상: 새 테스트 때문에 `Orders.regular()`를 바꿨더니 다른 테스트 2개가 깨졌다(실험 C).
- 원인: 기존 테스트가 마더의 **정확한 데이터**에 기대고 있었다.
- 대처: 변형은 새 팩터리 메서드나 빌더로 만든다. 마더의 기존 데이터는 고치지 않는다. 변형이 자주 생기면 빌더로 옮긴다.

### 4. 생성자 변경 → 테스트 수십 개 컴파일 오류

- 현상: 엔티티에 필수 필드를 추가하는 PR이 테스트 파일 수십 개를 건드린다.
- 보이는 형태: 실험 B — 직접 호출 방식은 테스트 수만큼 컴파일 오류(6개), 빌더는 1개.
- 원인: 테스트가 생성자를 직접 부른다. 생성자 모양이 테스트 전체에 복사돼 있다.
- 대처: 생성을 빌더 한 곳으로 모은다. 새 필드에는 빌더에서 안전한 기본값을 준다.

### 5. DB 픽스처 잔여 → 다음 실행·다른 작업과 충돌

- 현상: 두 번째 실행부터 `duplicate key value violates unique constraint`가 난다. 또는 두 CI 작업이 같은 테스트 DB를 쓰는 날만 실패한다.
- 보이는 형태: 첫 실행은 통과, 재실행은 실패(Unrepeatable Test). 병렬 작업 시간대에만 실패(Test Run War).
- 원인: 테스트가 만든 행이 남는다. 고정 키(`id=1`, `test@example.com`)를 모든 실행이 같이 쓴다.
- 대처: 트랜잭션 롤백, 실행·테스트마다 고유 키, 작업마다 별도 DB(컨테이너) 중 하나로 격리한다.

## 핵심 문장

- 픽스처는 테스트 실행 전의 환경 상태다. 테스트마다 새로 만들면(Fresh) 얽히지 않고, 공유하면(Shared) 빠르지만 순서에 따라 결과가 바뀐다.
- 실험에서 공유 픽스처는 무작위 순서 20회 중 12회 실패했고, 새 픽스처는 0회였다. 실패한 테스트가 아니라 앞서 실행된 테스트가 원인이었다.
- JUnit Jupiter는 기본적으로 테스트 메서드마다 인스턴스를 새로 만든다. `static`·`@BeforeAll`·DB에 둔 상태는 공유된다.
- 테스트 데이터 빌더는 안전한 기본값과 `with*`로, 테스트에 중요한 값만 드러내고 생성자 변경을 한 곳에 가둔다(실험: 고칠 자리 6 → 1).
- 오브젝트 마더는 이름 붙은 표준 객체를 모으지만, 테스트가 그 정확한 데이터에 기대면 마더 수정이 무관한 테스트를 깬다.

## 관련 주제·근거

- 선행
  - [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 좋은 테스트의 조건, AAA
- 후속·연결
  - [09-flaky-tests](../09-flaky-tests/2-summary.md) — 순서·공유 상태로 인한 불안정성 전반
  - [10-testing-time-and-concurrency](../10-testing-time-and-concurrency/2-summary.md) — 시간·동시성 픽스처
  - [12-test-smells-and-xunit-patterns](../12-test-smells-and-xunit-patterns/2-summary.md) — Mystery Guest·General Fixture·Obscure Test, Delegated Setup
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) — 실제 DB 픽스처
  - [03-test-doubles](../03-test-doubles/2-summary.md) — 더블도 픽스처의 일부
  - database [24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md) — 롤백 격리의 전제
  - software-design [19-immutability-and-value-objects](../../software-design/19-immutability-and-value-objects/2-summary.md) · [27-design-patterns-gof](../../software-design/27-design-patterns-gof/2-summary.md)(Builder)
- 문헌
  - Meszaros, 『xUnit Test Patterns』(2007) · xunitpatterns.com — "Fresh Fixture"(책 311쪽), "Shared Fixture"(317쪽), "Minimal Fixture"(302쪽), "Standard Fixture"(305쪽), "Creation Method"(415쪽), "Erratic Test"(Interacting Tests·Lonely Test·Test Run War) <http://xunitpatterns.com/Fresh%20Fixture.html>
  - Fowler, "ObjectMother"(bliki, 2006-10-24) <https://martinfowler.com/bliki/ObjectMother.html>
  - Nat Pryce, "Test Data Builders: an alternative to the Object Mother pattern"(2007-08-27) <http://www.natpryce.com/articles/000714.html>
  - Freeman·Pryce, 『GOOS』 22장 "Constructing Complex Test Data"(Test Data Builders, Creating Similar Objects, Combining Builders) — 목차 <https://growing-object-oriented-software.com/toc.html>
  - 『Software Engineering at Google』 12장 "Unit Testing" — Tests and Code Sharing: DAMP, Not DRY · Shared Values · Shared Setup · Defining Test Infrastructure <https://abseil.io/resources/swe-book/html/ch12.html>
- 제품 문서
  - JUnit 5.13.4 User Guide — 2.11 Test Execution Order("deterministic but intentionally nonobvious", `MethodOrderer.Random`), 2.12 Test Instance Lifecycle(per-method 기본) <https://docs.junit.org/5.13.4/user-guide/index.html> · `MethodOrderer$Random`의 설정 키 `junit.jupiter.execution.order.random.seed`(junit-jupiter-api 5.13.4 클래스 파일에서 확인)
  - maven-surefire-plugin `test` 목표 — `runOrder`(기본 filesystem), `runOrder.random.seed`(3.0.0-M6) <https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html>
- 실험 목록(코드는 scratchpad `ts/03/fixtures`, `ts/03/builder`, `ts/03/builder-run`)
  - A: `maven:3.9-eclipse-temurin-21`(Maven 3.9.16, JDK 21.0.11), JUnit Platform Launcher로 공유·새 픽스처 클래스를 기본 순서 + 시드 1~20 — 공유 12/20 실패·기본 순서 실패, 새 0/20
  - B: `eclipse-temurin:21-jdk`(JDK 21.0.12) `javac` — 생성자 인자 추가 시 컴파일 오류 직접 6·마더 3·빌더 1
  - C: 마더의 `regular()` 데이터 변경 — 마더 기존 테스트 6개 중 2개 실패, 빌더 기존 테스트 0개
