# software-design/38-layered-hexagonal-clean — 계층형·헥사고날·클린 아키텍처: 의존 방향 규칙 — 정리 (힌트)

## 해결하는 문제

업무 규칙이 DB·프레임워크 코드를 직접 알면, 규칙 하나를 시험하려 해도 DB가 필요하고 DB를 바꾸면 규칙 코드도 바뀐다.

```text
 계층형(전통)                                 헥사고날·클린
 Controller ──> Service ──> JdbcRepository    Controller ──> PlaceOrder ──> «port» OrderRepository
                  │              │                               │                 ▲
             업무 규칙이     DB 드라이버                      업무 규칙          │ implements
             DB 구현을 안다                                                JdbcOrderRepository (바깥)
   → "금액은 양수" 시험에도 DB 연결 필요        → 규칙은 포트(인터페이스)만 안다. DB는 바깥에서 꽂는다
```

- *계층형 아키텍처(layered)*: 표현 → 업무 → 영속처럼 기술 역할로 층을 나누고 위층이 아래층을 부르는 구조.
- *헥사고날 아키텍처(포트와 어댑터)*: 애플리케이션 안쪽은 포트(인터페이스)만 정의하고, 바깥의 어댑터가 포트를 구현하거나 호출한다. Cockburn 2005.
- *클린 아키텍처*: 동심원(엔티티 → 유스케이스 → 인터페이스 어댑터 → 프레임워크·드라이버)과 **의존 규칙**. Martin 2012 블로그·『Clean Architecture』 22장.

쉬운 예: 노트북의 USB-C 포트는 규격만 정한다. 충전기·모니터·저장 장치 제조사가 그 규격에 맞춘다. 노트북 설계는 어떤 충전기가 꽂힐지 모른다.\
똑같은 구조다.\
실무 예: 결제 도메인을 PG사 SDK·JPA 엔티티와 분리해 두면, PG사를 바꾸거나 DB를 바꿔도 도메인 테스트는 그대로 돈다.

계층형 자체의 모양(엄격/완화 층, 싱크홀)과 "의존이 뒤집힌다"는 큰 그림은 [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) 1.1에 있다. 이 노트는 방향 규칙을 **도구로 재고 강제하는 법**을 다룬다.

## 동작·원리

### 1. 세 모양의 의존 그래프

```text
 (a) 계층형: 위 → 아래                (b) 헥사고날: 바깥 → 안             (c) 클린: 동심원, 안쪽으로만
 ┌────────────┐                       어댑터(in)  어댑터(out)          ┌───────────────────────────┐
 │ Controller │                         web        jdbc                │ 프레임워크·드라이버 (DB,Web)│
 └─────┬──────┘                          │           │ implements      │ ┌───────────────────────┐ │
 ┌─────▼──────┐                          ▼           ▼                 │ │ 인터페이스 어댑터      │ │
 │  Service   │                     ┌──────────────────────┐           │ │ ┌───────────────────┐ │ │
 └─────┬──────┘                     │ 애플리케이션(유스케이스)│           │ │ │ 유스케이스         │ │ │
 ┌─────▼──────┐                     │  «port» OrderRepository│          │ │ │ ┌───────────────┐ │ │ │
 │ Persistence│ ── DB               │      도메인 모델       │           │ │ │ │  엔티티        │ │ │ │
 └────────────┘                     └──────────────────────┘           │ │ │ └───────────────┘ │ │ │
 업무가 영속을 안다                    안쪽은 바깥 이름을 모른다            └─┴─┴───────────────────┴─┴─┘
                                                                         소스 의존은 안쪽으로만
```

- *의존 규칙(Dependency Rule)*: Martin 블로그 "The Clean Architecture"(2012-08-13): "source code dependencies can only point inwards." 안쪽 원은 바깥 원의 이름(함수·클래스·변수)을 언급하지 않는다.
- *포트(port)*: 안쪽이 소유하는 인터페이스. 들어오는 쪽(입력 포트, 유스케이스)과 나가는 쪽(출력 포트, 저장소·외부 호출)이 있다.
- *어댑터(adapter)*: 포트와 바깥 기술을 잇는 코드. 웹 컨트롤러(입력), JDBC 저장소(출력).
- Cockburn 원문(2005, v0.9)의 의도: 애플리케이션이 사용자·프로그램·자동 테스트·배치에 의해 똑같이 구동되고, 실행 시 장치·DB와 **떨어져 개발·시험**될 수 있게 한다.

### 2. 제어 흐름과 의존 방향이 갈리는 지점 — DIP

```text
 실행 흐름:   Controller → PlaceOrder → JdbcOrderRepository → DB      (안 → 바깥으로 호출)
 소스 의존:   Controller → PlaceOrder → «OrderRepository» ← JdbcOrderRepository
                                         (안쪽 소유)          (바깥이 안을 향해 의존)
 조립:        Wiring(컴포지션 루트)이 new JdbcOrderRepository()를 만들어 PlaceOrder에 넣는다
```

- 호출은 안에서 바깥으로 가지만, 인터페이스를 안쪽에 두어 **소스 의존만** 뒤집는다(DIP). 클린 아키텍처 블로그의 "Use Case Output Port"가 같은 기법이다.
- *컴포지션 루트*: 구현을 골라 조립하는 단 한 곳. 『Clean Architecture』 26장 "The Main Component"가 이 자리를 다룬다(장 제목만 확인). 조립하려면 모든 구현을 알아야 하므로 가장 바깥에 둔다. 상세는 [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md).

### 실험 A: 같은 주문 기능 — 단위 테스트, 의존 그래프, DB 교체

v1(계층형, 업무 서비스가 `JdbcOrderRepository`를 직접 생성하고 컨트롤러가 저장소를 직접 부름)과 v2(헥사고날)를 같은 동작으로 만들었다. `Db.connect`는 환경 변수 `DB_URL`이 없으면 실패하는 드라이버 흉내다.

```java
// v1 업무 계층
public class OrderService {
    private final JdbcOrderRepository repo = new JdbcOrderRepository();   // 구현을 직접 생성
    public String place(String id, long amount) {
        if (amount <= 0) throw new IllegalArgumentException("금액은 양수");
        repo.save(id, amount);
        return "placed " + id;
    }
}
// v2 유스케이스 — 포트만 안다
public interface OrderRepository { void save(Order o); long count(); }   // 출력 포트: 안쪽이 소유
public class PlaceOrder {
    private final OrderRepository repo;
    public PlaceOrder(OrderRepository repo) { this.repo = repo; }
    public String place(String id, long amount) { repo.save(new Order(id, amount)); return "placed " + id; }
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e38/run.sh`, 2026-10-02)

업무 규칙 단위 테스트(DB 없음):

```text
== 단위 테스트 (DB_URL 없음)
v1 단위 테스트 실패: java.lang.IllegalStateException: DB 연결 실패: jdbc:postgresql://db/shop
placed o1, 저장 수=1
규칙 확인: 금액은 양수
```

`jdeps -verbose:package`(패키지 의존 그래프):

```text
== jdeps v1
   shop.controller   -> shop.persistence
   shop.controller   -> shop.service
   shop.service      -> shop.persistence
== jdeps v2
   shop.adapter.in   -> shop.application
   shop.adapter.out  -> shop.application
   shop.adapter.out  -> shop.domain
   shop.application  -> shop.domain
   shop.config       -> shop.adapter.in
   shop.config       -> shop.adapter.out
   shop.config       -> shop.application
```

(jdeps 출력의 열 정렬 공백과 `out` 꼬리표는 줄였다. 전체는 `e38/run-output.txt`)

DB를 Mongo 구현으로 바꾸는 변경(`git diff --stat`, 호스트 git 2.43.0, `scratchpad/sd/35/e38/g/`):

```text
== v1 DB 교체
 src/shop/controller/OrderController.java       | 4 ++--
 src/shop/persistence/MongoOrderRepository.java | 5 +++++
 src/shop/service/OrderService.java             | 4 ++--
 3 files changed, 9 insertions(+), 4 deletions(-)
== v2 DB 교체
 src/shop/adapter/out/MongoOrderRepository.java | 7 +++++++
 src/shop/config/Wiring.java                    | 4 ++--
 2 files changed, 9 insertions(+), 2 deletions(-)
```

- 관찰 1 — v1은 업무 규칙("금액은 양수")을 시험하려다 **생성자에서 DB 연결로 실패**했다. v2는 메모리 어댑터를 꽂아 규칙을 확인했다.
- 관찰 2 — v1 그래프에는 `service → persistence`가 있다. v2에서 `application`·`domain`에서 나가는 화살표는 `application → domain`뿐이다. 바깥을 향한 화살표가 없다.
- 관찰 3 — DB 교체 시 v1은 업무 서비스와 컨트롤러를 고쳤다. v2는 새 어댑터 + 조립 한 곳만 고쳤고, 도메인·유스케이스는 그대로였다.
- 반대 비용 — 같은 기능에 v1은 Java 파일 4개·33줄, v2는 7개·45줄이었다(`find … | wc`). 포트·조립 코드만큼 간접층이 늘었다. 기술 교체·격리 시험이 필요 없는 단순 CRUD라면 이 비용이 이득보다 클 수 있다.

### 3. 규칙을 테스트로 강제 — ArchUnit

```java
// v1 — 계층 규칙
layeredArchitecture().consideringOnlyDependenciesInLayers()
    .layer("Controller").definedBy("shop.controller..")
    .layer("Service").definedBy("shop.service..")
    .layer("Persistence").definedBy("shop.persistence..")
    .whereLayer("Controller").mayNotBeAccessedByAnyLayer()
    .whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")
    .whereLayer("Persistence").mayOnlyBeAccessedByLayers("Service");
noClasses().that().resideInAPackage("shop.service..")
    .should().dependOnClassesThat().resideInAPackage("shop.persistence..");
// v2 — 양파(헥사고날) 규칙
onionArchitecture()
    .domainModels("shop.domain..")
    .applicationServices("shop.application..")
    .adapter("web", "shop.adapter.in..")
    .adapter("persistence", "shop.adapter.out..")
    .withOptionalLayers(true)
    .ignoreDependency(resideInAPackage("shop.config.."), DescribedPredicate.alwaysTrue());
```

### 실험 B: ArchUnit이 잡는 위반

(실험, ArchUnit 1.4.1(Maven Central), JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e38/test/ArchCheck.java`, 2026-10-02)

```text
== ArchUnit v1
-- 계층 규칙: 위반 3건
   Constructor <shop.controller.OrderController.<init>()> calls constructor <shop.persistence.JdbcOrderRepository.<init>()> in (OrderController.java:6)
   Field <shop.controller.OrderController.repo> has type <shop.persistence.JdbcOrderRepository> in (OrderController.java:0)
   Method <shop.controller.OrderController.count()> calls method <shop.persistence.JdbcOrderRepository.count()> in (OrderController.java:8)
-- 업무 계층은 영속 구현에 의존하지 않는다: 위반 3건
   Constructor <shop.service.OrderService.<init>()> calls constructor <shop.persistence.JdbcOrderRepository.<init>()> in (OrderService.java:4)
   Field <shop.service.OrderService.repo> has type <shop.persistence.JdbcOrderRepository> in (OrderService.java:0)
   Method <shop.service.OrderService.place(java.lang.String, long)> calls method <shop.persistence.JdbcOrderRepository.save(java.lang.String, long)> in (OrderService.java:7)
== ArchUnit v2
-- 양파 규칙(예외 없음): 위반 4건
   Method <shop.config.Wiring.controller()> calls constructor <shop.adapter.in.OrderController.<init>(shop.application.PlaceOrder)> in (Wiring.java:6)
   Method <shop.config.Wiring.controller()> calls constructor <shop.adapter.out.JdbcOrderRepository.<init>()> in (Wiring.java:6)
   Method <shop.config.Wiring.controller()> calls constructor <shop.application.PlaceOrder.<init>(shop.application.OrderRepository)> in (Wiring.java:6)
   Method <shop.config.Wiring.controller()> has return type <shop.adapter.in.OrderController> in (Wiring.java:0)
-- 양파 규칙(컴포지션 루트 shop.config 예외): 통과
== ArchUnit v2bad
-- 양파 규칙(컴포지션 루트 shop.config 예외): 위반 2건
   Method <shop.application.PlaceOrder.place(java.lang.String, long)> calls method <shop.adapter.out.Db.connect(java.lang.String)> in (PlaceOrder.java:8)
   Method <shop.application.PlaceOrder.place(java.lang.String, long)> calls method <shop.adapter.out.Db.exec(java.lang.String)> in (PlaceOrder.java:8)
```

- 관찰 1 — v1의 **계층 건너뛰기**(컨트롤러 → 저장소 직접)가 계층 규칙 위반 3건으로 잡혔다. 업무 → 영속 구현 의존도 3건.
- 관찰 2 — v2를 예외 없이 검사하면 조립 클래스 `Wiring`이 위반 4건이다. 이 실험(ArchUnit 1.4.1 `onionArchitecture`)에서는 층 밖 클래스가 어댑터·애플리케이션에 접근하는 것도 위반으로 셌다. 컴포지션 루트는 `ignoreDependency`로 명시해 빼야 통과했다.
- 관찰 3 — v2bad는 "급한 수정"으로 유스케이스가 어댑터의 `Db`를 직접 불렀다. 컴파일은 되지만 규칙이 줄 번호까지 짚어 위반 2건을 냈다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프와 방향(DAG)**: 모듈 = 정점, import·호출 = 간선. 계층형은 층 순서를 지키는 DAG, 클린은 "원 번호가 작아지는 쪽으로만" 간선. 규칙 검사는 간선마다 (출발 층, 도착 층)이 허용 표에 있는지 보는 것이다. `jdeps`가 간선 목록을 준다(실험 A).
- **위상 순서**: 의존이 DAG이면 안쪽(도메인)부터 바깥 순으로 빌드·시험할 수 있다. 순환이 생기면 위상 순서가 없다 — [39-component-principles](../39-component-principles/2-summary.md), 순환 탐지는 [algorithm/18-scc](../../algorithm/18-scc/2-summary.md).
- **어댑터 패턴·전략 패턴**: 포트 = 인터페이스, 어댑터 = 구현 교체. GoF는 원본 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md).

## 적용 — 풀어나가는 법

1. **지금 그래프를 본다.** `jdeps -verbose:package target/classes`로 업무 패키지에서 나가는 간선을 찾는다. `service → persistence`·`domain → jakarta.persistence`·`domain → org.springframework`가 있으면 의존 규칙 위반 후보다.
2. **출력 포트를 안쪽으로 옮긴다.** 저장소·외부 API·시계·메시지 발행을 인터페이스로 뽑아 애플리케이션 패키지에 둔다. 구현은 `adapter.out`으로 옮긴다.
3. **조립을 한 곳으로.** `new JdbcOrderRepository()`를 업무 코드에서 지우고 컴포지션 루트(`config`, Spring이면 `@Configuration`·컴포넌트 스캔)로 모은다.
4. **규칙을 테스트로 고정한다.** ArchUnit `layeredArchitecture()`·`onionArchitecture()`, 컴포지션 루트는 `ignoreDependency`로 명시 예외. 기존 위반이 많으면 동결(`FreezingArchRule`)부터 — [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md).
5. **도메인 단위 테스트를 메모리 어댑터로 쓴다**(실험 A의 `InMemoryOrders`). DB가 필요한 테스트는 어댑터 통합 테스트로 따로 둔다.
6. **간접층 비용을 의식한다.** 모든 CRUD를 포트로 감쌀 필요는 없다. 바뀔 가능성이 큰 바깥(외부 API·저장소)부터 포트화한다.

## 장애 시나리오와 대처

### 1. 도메인이 프레임워크·DB에 의존 → 교체·테스트 불가 (⚠ 커리큘럼)

- 현상: 업무 규칙 하나를 고쳐도 테스트에 DB·스프링 컨텍스트가 떠야 한다. DB 교체 견적이 업무 코드 전체에 걸친다.
- 보이는 형태: 단위 테스트가 연결 오류로 실패(실험 A `DB 연결 실패`), 테스트 스위트가 느림, `jdeps`에 `service -> persistence`.
- 원인: 업무 코드가 구현 클래스를 직접 생성·참조한다.
- 대처: 출력 포트 추출 + 컴포지션 루트 조립(실험 A v2: DB 교체가 어댑터 + 조립 한 곳). ArchUnit `noClasses().that().resideInAPackage("..domain..").should().dependOnClassesThat().resideInAPackage("..persistence..")`.

### 2. 계층 건너뛰기가 누적된다 (⚠ 커리큘럼)

- 현상: 컨트롤러가 저장소를 직접 부르는 "잠깐만" 코드가 쌓여, 업무 규칙(권한·검증)을 우회하는 경로가 생긴다.
- 보이는 형태: 같은 조회가 서비스 경유·직접 호출 두 경로로 존재. ArchUnit 계층 규칙 위반(실험 B v1 3건).
- 원인: 완화 층(open layer) 허용이 명시적 결정 없이 퍼졌다.
- 대처: 건너뛰기를 허용할 층을 명시적으로 정하고(`mayOnlyBeAccessedByLayers`), 나머지는 빌드에서 실패시킨다.

### 3. 조립 코드가 아키텍처 규칙 위반으로 걸려 규칙 자체를 끈다

- 현상: 규칙을 도입했더니 `config`·`Application` 클래스가 위반으로 쏟아져 팀이 규칙을 비활성화한다.
- 보이는 형태: 실험 B v2 "예외 없음" 위반 4건 — 모두 `Wiring`.
- 원인: 컴포지션 루트는 구현을 골라 조립하므로 모든 원을 안다(실험의 `Wiring`). 규칙에 그 예외를 표현하지 않았다.
- 대처: `ignoreDependency(resideInAPackage("..config.."), alwaysTrue())`처럼 **조립 패키지만** 예외로 둔다. 규칙 전체를 끄지 않는다.

### 4. 포트·어댑터 과잉으로 변경이 오히려 늘어난다

- 현상: 필드 하나를 추가하는데 도메인·포트·어댑터·DTO 매핑을 모두 고친다.
- 보이는 형태: 단순 변경 PR의 파일 수 증가. 실험 A에서 같은 기능의 파일이 4개 → 7개.
- 원인: 바뀌지 않을 바깥까지 포트로 감쌌다. 간접층마다 매핑이 생긴다.
- 대처: 바뀔 가능성이 있는 경계만 포트화한다(APOSD의 얕은 모듈 경고, [03-deep-modules-and-abstraction](../03-deep-modules-and-abstraction/2-summary.md)). 매핑은 생성 코드([35-annotation-and-metadata-programming](../35-annotation-and-metadata-programming/2-summary.md)의 MapStruct)로 줄인다.

## 핵심 문장

- 의존 규칙: 소스 의존은 안쪽(업무 규칙)으로만 향한다. 실행 흐름은 바깥으로 나가도, 포트를 안쪽에 두어 소스 의존만 뒤집는다.
- 실험에서 업무 서비스가 DB 구현을 직접 만든 계층형은 규칙 단위 테스트가 DB 연결 오류로 실패했고, 헥사고날은 메모리 어댑터로 통과했다.
- DB 교체는 계층형에서 업무 서비스·컨트롤러를 고쳤고, 헥사고날에서는 새 어댑터와 조립 한 곳만 고쳤다. 대신 같은 기능의 파일은 4개에서 7개로 늘었다.
- ArchUnit 계층·양파 규칙은 계층 건너뛰기와 안쪽 → 바깥 의존을 줄 번호까지 잡았다. 컴포지션 루트는 명시적 예외로 빼야 한다.

## 관련 주제·근거

- 선행
  - [37-architecture-styles](../37-architecture-styles/2-summary.md) — 원본 [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) 1.1 계층형·헥사고날과의 관계
  - [22-solid](../22-solid/2-summary.md)(DIP), 원본 [engineering/solid-principles](../../engineering/solid-principles/2-summary.md)
- 후속·연결
  - [39-component-principles](../39-component-principles/2-summary.md) — 컴포넌트 단위 의존 방향(ADP·SDP·SAP)
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md), [40-codebase-structure](../40-codebase-structure/2-summary.md), [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md)
  - [algorithm/18-scc](../../algorithm/18-scc/2-summary.md) — 순환 탐지
- 글·문서
  - Alistair Cockburn, "Hexagonal Architecture"(Ports and Adapters), 2005-09-04 v0.9 — 의도 문장 확인 <https://alistair.cockburn.us/hexagonal-architecture/>
  - Robert C. Martin, "The Clean Architecture", 2012-08-13 — Dependency Rule, Use Case Output Port <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>
  - Robert C. Martin, 『Clean Architecture』(Pearson, 2017) 5부 Architecture: 22장 The Clean Architecture, 25장 Layers and Boundaries, 26장 The Main Component, 28장 The Test Boundary — InformIT 목차로 장 제목만 확인, 본문 미열람 <https://www.informit.com/store/clean-architecture-a-craftsmans-guide-to-software-structure-9780134494166>
  - ArchUnit User Guide — `layeredArchitecture()`, `onionArchitecture()` <https://www.archunit.org/userguide/html/000_Index.html>
  - JDK 21 `jdeps` 도구 <https://docs.oracle.com/en/java/javase/21/docs/specs/man/jdeps.html>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02, 코드 scratchpad `sd/35/e38/`)
  - A `v1/`·`v2/` + `test/UnitV1.java`·`UnitV2.java` — DB 없는 단위 테스트, `jdeps -verbose:package`, `g/`에서 DB 교체 `git diff --stat`, 파일·줄 수
  - B `test/ArchCheck.java`(ArchUnit 1.4.1) — v1 계층 규칙, v2 양파 규칙 예외 유무, `v2bad` 안쪽 → 바깥 의존. 출력 전체 `run-output.txt`
