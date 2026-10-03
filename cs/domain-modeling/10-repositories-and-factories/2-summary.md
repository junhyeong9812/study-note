# domain-modeling/10-repositories-and-factories — 리포지토리와 팩토리: 영속성 추상과 생성 캡슐화 — 정리 (힌트)

## 해결하는 문제

애그리거트는 언젠가 만들어지고, 저장되고, 다시 꺼내진다. 이 세 순간을 아무 데서나 처리하면 도메인 규칙이 SQL과 생성 코드 속으로 흩어진다.

```text
  수명 주기          문제가 생기는 자리
  생성      new Order(...) + 줄 추가 + 할인 계산 + 검증을 호출하는 쪽이 매번 조립 → 조립 순서·검증 누락
  저장      서비스가 INSERT/UPDATE를 직접 → 루트를 건너뛰고 내부 행만 고침
  조회      findOverdueVipOrdersNotNotifiedSince(...) → "연체"의 정의가 SQL에 복제
  재구성    DB 행 → 객체로 되살릴 때 "생성 규칙"을 다시 적용 → 과거 데이터가 로딩 실패
```

- *리포지토리(repository)*: 한 애그리거트 타입 전체를 메모리 안 컬렉션처럼 보이게 하는 객체. 넣기·빼기·조건으로 고르기를 제공하고 저장 기술을 숨긴다.
- *팩토리(factory)*: 복잡한 애그리거트나 큰 값 객체를 불변식을 지킨 완성품으로 만들어 주는 객체·메서드.
- *재구성(reconstitution)*: 저장된 데이터에서 이미 존재하던 객체를 되살리는 것. 새로 만드는 "생성"과 다르다.

쉬운 예: 도서관.
- 사서(리포지토리)에게 "이 회원의 연체 도서"를 물으면 책을 가져다준다. 이용자는 서고 배치(저장 방식)를 모른다.
- 신규 회원 등록(팩토리)은 신분 확인·회원 번호 발급·대출 한도 설정을 한 번에 한다.
- 다른 지점에서 옮겨 온 회원 기록(재구성)에는 새 번호를 주지 않고, 가입 당시 규칙을 다시 따지지 않는다.

똑같은 구조다.\
실무 예: Spring Data `OrderRepository`, `Order.place(...)` 정적 팩토리, 주문서 → 주문 변환기, 이벤트 소싱의 스냅숏 복원.

## 동작·원리

### 1. 리포지토리 — 컬렉션의 착각

```text
  도메인 계층                                 인프라 계층
  ┌────────────────────────────┐            ┌─────────────────────────────┐
  │ interface Orders {         │  구현 ◀────│ JpaOrders / JdbcOrders /     │
  │   Order byId(OrderId)      │            │ InMemoryOrders(테스트)       │
  │   void add(Order)          │            └─────────────────────────────┘
  │   List<Order> satisfying(  │
  │       Spec<Order>)         │   ← 도메인 전문가에게 의미 있는 조건으로 고른다
  │ }                          │
  └────────────────────────────┘
  애그리거트 "루트"마다 하나. 내부 엔티티(OrderLine)용 리포지토리는 두지 않는다.
```

- Evans 『DDD Reference』(2015) Repositories 항목
  - 전역 접근이 필요한 애그리거트 타입마다, 그 루트 타입 객체 전체의 **메모리 안 컬렉션이라는 착각**을 주는 서비스를 만든다.
  - 추가·제거 메서드가 실제 삽입·삭제를 감싼다. 도메인 전문가에게 의미 있는 기준으로 객체를 고르는 메서드를 둔다.
  - 완전히 만들어진 객체(또는 그렇게 보이는 지연 프록시)를 돌려준다.
  - **실제로 직접 접근이 필요한 애그리거트 루트에만** 리포지토리를 둔다.
  - 제약 없는 쿼리는 객체의 특정 필드만 뽑거나 애그리거트 내부 객체를 직접 만들어 **루트를 건너뛴다**. 그러면 도메인 로직이 쿼리와 애플리케이션 계층으로 옮겨 가고, 엔티티·값 객체는 데이터 그릇이 된다고 적는다.
- Fowler 『PoEAA』 Repository(Edward Hieatt·Rob Mee 기고): 컬렉션 같은 인터페이스로 도메인과 데이터 매핑 계층 사이를 중재한다. 클라이언트가 **쿼리 명세를 선언적으로 만들어** 리포지토리에 넘긴다. 데이터 소스 패턴 전체는 [database/25](../../database/25-data-source-patterns/2-summary.md).
- Spring Data JDBC 문서: 리포지토리는 특정 타입의 모든 애그리거트의 컬렉션처럼 보이는 영속 저장소 추상이며, Spring Data에서는 **애그리거트 루트마다 리포지토리 하나**를 둔다.

### 2. 컬렉션 지향 vs 영속 지향 (Vernon 『IDDD』 12장)

```text
  컬렉션 지향                                   영속 지향
  orders.add(order)  (처음 한 번)               orders.save(order)  (바꿀 때마다)
  order.ship()       → 변경 추적이 알아서 저장     order.ship(); orders.save(order)  ← 빠뜨리면 저장 안 됨
  예: JPA/Hibernate 영속성 컨텍스트             예: Spring Data JDBC, 키-값 저장소, MongoDB
```

- Vernon 『IDDD』(2013) 12장은 두 스타일을 나눈다(목차와 출판사 발췌로 확인). 컬렉션 지향은 저장을 암시하지 않고 변경을 자동으로 반영한다. 영속 지향은 저장 장치가 변경을 추적하지 않을 때 쓰고, 만들거나 바꿀 때마다 `save()`한다.
- Spring Data JDBC 문서 "Why Spring Data JDBC?": "엔티티를 저장하면 저장되고, 안 하면 안 된다. 더티 추적도 세션도 없다." 엔티티를 읽으면 SQL이 실행되고 완전히 로드된 엔티티를 받는다(지연 로딩·캐시 없음).

### 3. 쿼리 메서드 폭증과 명세(Specification)

```text
  조건 3개(상태·VIP·연체)의 조합을 메서드 이름으로 파생하면 (계산)
   findByStatus / findByVip / findByOverdue / findByStatusAndVip / findByStatusAndOverdue /
   findByVipAndOverdue / findByStatusAndVipAndOverdue     → 2³ − 1 = 7개, 조건이 n개면 2ⁿ − 1개(하나 추가마다 대략 두 배)

  명세로 바꾸면
   Spec<Order> status(s), vip(), overdue(today)   +   orders.satisfying(spec)
   status(PAID).and(vip()).and(overdue(today))   → 조건 3개 + 메서드 1개
```

- Evans 『DDD』(2003) 9장 SPECIFICATION: 참/거짓 판정 규칙을 독립된 객체로 꺼내, 검증·선택(조회)·생성 요구에 같은 규칙을 쓰는 패턴(InformIT 목차로 절 이름 확인, 세부는 Evans·Fowler "Specifications" 논문 <https://martinfowler.com/apsupp/spec.pdf>).
- 핵심은 개수가 아니라 **규칙의 단일 출처**다. "연체"의 정의가 엔티티 메서드와 SQL에 각각 있으면 한쪽만 바뀐다.

### 실험 A: 규칙이 리포지토리 SQL에 복제됐을 때 (PostgreSQL 17)

```java
record Loan(long id, String grade, LocalDate due, boolean returned) {
    // 도메인 규칙 v2: 연체 = 미반납 && 오늘 > 반납일 + 유예일 (NORMAL 3일, VIP 7일)  ← v1은 유예 0일
    boolean isOverdue(LocalDate today) { return !returned && today.isAfter(due.plusDays(grace(grade))); }
    static int grace(String g) { return g.equals("VIP") ? 7 : 3; }
}
// A. 리포지토리가 규칙을 SQL로 따로 들고 있다 (v1 규칙이 그대로 남음)
"SELECT id FROM loan WHERE NOT returned AND due_date < ? ORDER BY id"
// B. 명세 하나가 메모리 판정과 SQL 술어를 함께 낸다
record OverdueSpec(LocalDate today) {
    boolean isSatisfiedBy(Loan l) { return l.isOverdue(today); }
    String sqlWhere() { return "NOT returned AND ? > due_date + (CASE grade WHEN 'VIP' THEN 7 ELSE 3 END)"; }
}
// 데이터: 대출 20건, 반납일 = 2026-10-03 − 0…9일, 등급 교대, 5의 배수 id는 반납됨
```

(실험, PostgreSQL 17.11 일회용 컨테이너 + JDK 21.0.12 eclipse-temurin, pgJDBC 42.7.4, 둘 다 `--cpus=2`, 기준일 2026-10-03, 3회 같은 결과)

```text
엔티티 규칙(메모리)    연체 id = [7, 9, 17, 19]
A 리포지토리 SQL(복제) 연체 id = [2, 3, 4, 6, 7, 8, 9, 12, 13, 14, 16, 17, 18, 19]  불일치 10건
B 명세 객체 SQL        연체 id = [7, 9, 17, 19]  불일치 0건
```

- 관찰
  - 유예 기간을 엔티티에만 넣었더니, 리포지토리 쿼리는 옛 규칙으로 14건을 연체로 돌려줬다. 메모리 규칙과 10건이 어긋난다. 연체 안내 배치가 이 쿼리를 쓰면 10명에게 잘못된 연체 통지가 간다(예시 해석).
  - 명세 객체는 규칙(유예일)을 한 곳에 두고 두 표현을 함께 내므로 0건이었다.
- 한계: B도 SQL 문자열과 Java 식을 **두 번** 쓴다. 단일 출처는 같은 클래스 안에 둔 것까지다. 둘이 같은지 확인하는 테스트(모든 행에 대해 `isSatisfiedBy` 결과 = SQL 결과)를 함께 둔다 — 위 실험의 "불일치 0건" 계산이 그 테스트다. JPA Criteria·Querydsl로 술어를 객체로 만들면 문자열 중복은 줄지만 메모리 판정과의 중복은 남는다.

### 4. 팩토리 — 생성과 재구성

```text
  생성(create)                                   재구성(reconstitute)
  입력: 업무 의도 (상품·수량·고객)                  입력: 저장된 상태 전체 (id 포함)
  새 식별자 부여                                   저장된 식별자 유지 — 새 id를 주면 연속성이 끊긴다
  생성 시점 규칙 검사 (시작일 ≥ 오늘 등)             생성 규칙은 다시 묻지 않음, 구조적 무결성만 확인
  위반 → 거절                                      위반 → 더 유연한 대응(로그·격리·보정)이 필요할 수 있음
```

- Evans 『DDD Reference』 Factories 항목
  - 내부적으로 일관된 애그리거트 전체나 큰 값 객체의 생성이 복잡해지거나 내부 구조를 너무 드러내면, 생성 책임을 별도 객체로 옮긴다. 그 객체는 도메인 모델의 책임은 없어도 도메인 설계의 일부다.
  - 클라이언트가 구체 클래스를 몰라도 되는 인터페이스를 준다.
  - **애그리거트 전체를 한 조각으로, 불변식을 지키며 만든다.** 복잡한 값 객체는 필요하면 빌더로 조립한 뒤 한 조각으로 만든다.
- Evans 『DDD』 6장: "When a Constructor Is All You Need"·"Where Does Invariant Logic Go?"·"Reconstituting Stored Objects" 절(InformIT 목차). 재구성용 엔티티 팩토리는 새 추적 ID를 부여하지 않고, 불변식 위반을 생성 때와 다르게 다룰 수 있다(새 객체면 그냥 거절하지만 재구성에서는 더 유연한 대응이 필요할 수 있다)는 대목은 Goodreads 독자 발췌로 확인했다(본문 미열람).
- 팩토리 자리는 여러 곳이다.
  - 생성자 하나로 충분하면 생성자(Evans 6장 절 제목 그대로).
  - 루트의 메서드가 다른 애그리거트를 만드는 팩토리 메서드: Vernon(2011) 1부의 `product.planBacklogItem(...)`은 새 `BacklogItem`을 만들어 돌려주는 팩토리 역할을 한다고 적는다.
  - 별도 팩토리 클래스: 외부 정보(요율표·번호 발급기)가 필요할 때.

### 실험 B: 재구성을 생성 경로로 하면

```java
static final class Subscription {
    final UUID id; final LocalDate start; final String status;
    private Subscription(UUID id, LocalDate start, String status) { ... }
    static Subscription create(LocalDate start, LocalDate today) {          // 생성: 새 ID + 생성 규칙
        if (start.isBefore(today)) throw new IllegalArgumentException("시작일이 과거: " + start);
        return new Subscription(UUID.randomUUID(), start, "ACTIVE");
    }
    static Subscription reconstitute(UUID id, LocalDate start, String status) { // 재구성: ID 유지, 구조만 확인
        if (id == null || start == null || status == null) throw new IllegalStateException("손상된 행");
        return new Subscription(id, start, status);
    }
}
// DB의 2025-01-01 시작 구독 행을 두 경로로 되살리고, 새 구독을 과거 시작일로 create 해 본다
```

(실험, 같은 환경)

```text
== 팩토리: 저장된 과거 구독 재구성
create 경로로 재구성 → 시작일이 과거: 2025-01-01
reconstitute 경로 → id 00000000-0000-0000-0000-000000000001 (저장된 ID 유지), start 2025-01-01
새 구독을 과거 시작일로 create → 시작일이 과거: 2026-09-01
```

- 관찰: 생성 규칙("시작일 ≥ 오늘")은 새 구독에는 맞지만, 1년 전에 정상 생성된 구독을 읽을 때 적용하면 로딩이 실패한다. 생성 경로를 통과했다면 ID도 새로 받았을 것이다. 재구성 경로는 ID를 유지하고 구조만 확인한다.
- JPA에서는 공급자가 기본 생성자와 필드 접근으로 재구성을 대신한다(Jakarta Persistence 3.1 §2.1: 엔티티 클래스는 public 또는 protected 무인자 생성자를 가져야 한다). 그래서 생성 규칙은 **공개 생성자·팩토리에** 두고, 무인자 생성자는 `protected`로 숨기는 경우가 많다.

## 쓰이는 자료구조·알고리즘

- **컬렉션 추상(Map/Set)**: 리포지토리 인터페이스는 `Map<Id, Aggregate>`처럼 생겼다. 테스트용 메모리 구현은 실제로 `HashMap`이다.
- **명세 = 술어 트리**: `and`·`or`·`not`으로 조합한 판정식(Composite). 메모리에서는 트리를 평가하고, 조회에서는 트리를 SQL `WHERE`로 번역한다(Query Object, [database/25](../../database/25-data-source-patterns/2-summary.md)).
- **식별자 맵(Identity Map)**: JPA 영속성 컨텍스트가 같은 id에 같은 인스턴스를 돌려주는 장치 — 컬렉션 지향 리포지토리의 바탕.
- **변경 추적(dirty checking)**: 스냅숏과 현재 값을 비교해 바뀐 엔티티를 찾아 UPDATE를 낸다. Hibernate 6.6 기본 UPDATE는 갱신 가능한 모든 컬럼을 SET하고, `@DynamicUpdate`를 붙이면 바뀐 컬럼만 SET한다(가이드 Dynamic updates 절, 실험 C). Spring Data JDBC에는 변경 추적이 없다.
  - 실험 C(Hibernate 6.6.29 + H2 2.3.232, JDK 21, 1회): 열 셋(`title`·`author`·`price`) 중 `title`만 바꾸고 커밋했을 때 찍힌 SQL.

```text
기본:           update book_a set author=?,price=?,title=? where id=?
@DynamicUpdate: update book_b set title=? where id=?
```

- **빌더**: 큰 값 객체를 단계별로 조립한 뒤 마지막에 불변식을 한 번에 검사한다.

## 적용 — 풀어나가는 법

### 1. 실무 순서

```text
  1) 애그리거트 루트 목록을 적는다 → 루트마다 리포지토리 하나, 내부 엔티티용은 없음
  2) 리포지토리 인터페이스를 도메인 패키지에, 이름·메서드는 유비쿼터스 언어로(byId, add, satisfying)
  3) 조회 조건이 조합되기 시작하면 명세(Spec) 또는 Query Object로
  4) 화면용 목록·통계는 리포지토리가 아니라 별도 조회 모델(DTO 프로젝션)로 — 애그리거트를 재구성하지 않는다
  5) 생성이 여러 단계·외부 정보면 팩토리, 아니면 생성자. 재구성 경로는 생성 경로와 분리
  6) 영속 지향 저장소(Spring Data JDBC 등)라면 유스케이스 끝에서 save를 빠뜨리지 않게 애플리케이션 서비스 틀을 정한다
```

### 2. 코드 (Java 21 + Spring Data JPA)

```java
// 도메인 패키지: 컬렉션처럼
public interface Orders {
    Optional<Order> byId(OrderId id);
    void add(Order order);
    List<Order> satisfying(Specification<Order> spec);   // Spring Data JPA의 Specification 인터페이스 사용
}

// 인프라 패키지: Spring Data로 구현
interface OrderJpaRepository extends JpaRepository<Order, OrderId>, JpaSpecificationExecutor<Order> {}
@Repository class JpaOrders implements Orders {
    private final OrderJpaRepository jpa;
    JpaOrders(OrderJpaRepository jpa) { this.jpa = jpa; }
    public Optional<Order> byId(OrderId id) { return jpa.findById(id); }
    public void add(Order o) { jpa.save(o); }
    public List<Order> satisfying(Specification<Order> s) { return jpa.findAll(s); }
}

// 팩토리: 애그리거트를 한 조각으로
public class Order {
    protected Order() {}                                           // JPA 재구성용, 생성 규칙 없음
    public static Order place(CustomerId c, List<LineRequest> lines, Clock clock) {
        if (lines.isEmpty()) throw new IllegalArgumentException("주문 줄 없음");
        Order o = new Order();
        o.id = OrderId.newId(); o.customerId = c; o.placedAt = Instant.now(clock);
        lines.forEach(l -> o.addLine(l.sku(), l.qty(), l.price()));   // 줄 추가 규칙은 루트 메서드가
        return o;
    }
}
```

- 도메인 인터페이스가 Spring Data의 `Specification`을 쓰면 도메인이 Spring에 의존한다. 이를 피하려면 자체 `Spec<T>` 인터페이스를 두고 인프라에서 번역한다. 어느 쪽이든 의존 방향을 팀이 정해 기록한다.
- 쿼리 메서드 이름이 길어지면 Spring Data JPA 문서도 `@Query`·이름 있는 쿼리로 넘어가라고 안내한다([database/25](../../database/25-data-source-patterns/2-summary.md) §2).

### 3. 진단

```bash
# 리포지토리별 쿼리 메서드 수 (폭증 신호)
grep -rn --include=*Repository.java -E '^\s+\S+ (find|count|exists|delete)By\w+\(' src | cut -d: -f1 | sort | uniq -c | sort -rn
# 내부 엔티티용 리포지토리 (루트 우회 후보)
grep -rln --include=*.java -E 'interface \w*(Line|Item|Detail)\w*Repository' src
```

```java
// 명세 정합성 테스트: 메모리 판정과 쿼리 결과가 같은가 (실험 A의 불일치 계산)
var mem = all().stream().filter(spec::isSatisfiedBy).map(Loan::id).toList();
assertEquals(mem, repo.satisfying(spec).stream().map(Loan::id).toList());
// 재구성 회귀 테스트: 과거 데이터 픽스처(생성 규칙에 어긋나는 옛 행)를 로드할 수 있다
```

## 장애 시나리오와 대처

### 1. 리포지토리 쿼리 메서드 폭증 → 도메인 로직 누출 (⚠ 커리큘럼)

- **현상**: 연체 기준을 "반납일 다음 날"에서 "3일 유예"로 바꿨는데, 연체 안내 문자는 여전히 옛 기준으로 나간다.
- **보이는 형태**: 오류 없음. 화면(엔티티 규칙)과 배치(리포지토리 쿼리)의 연체 건수가 다르다(실험 A: 4건 vs 14건, 불일치 10건). 리포지토리에 `findOverdue…`·`findOverdueVip…`·`countOverdue…`가 수십 개.
- **원인**: 도메인 규칙이 엔티티 메서드와 쿼리 메서드 이름·JPQL에 각각 복제됐다. 규칙 변경이 한쪽에만 들어갔다.
- **대처**: 규칙을 명세 객체 하나로 모으고 메모리 판정·쿼리 술어를 함께 내게 한다. 둘의 결과를 비교하는 테스트를 둔다. 화면용 복합 조회는 별도 조회 모델로 뺀다.

### 2. 내부 엔티티용 리포지토리 → 루트 우회, 불변식 파괴

- **현상**: 주문 줄을 `OrderLineRepository`로 직접 수정했더니 주문 합계 한도가 깨졌다.
- **보이는 형태**: 예외 없음. 루트 버전이 오르지 않는다([05](../05-aggregates-and-invariants/2-summary.md) 실험 C).
- **원인**: Evans가 경고한 "애그리거트 내부 객체를 직접 만들어 루트를 건너뛰는" 쿼리·저장 경로다.
- **대처**: 리포지토리는 루트에만 둔다. 줄은 루트를 로드해 루트 메서드로 고친다. 조회만 필요하면 읽기 전용 프로젝션을 쓴다.

### 3. 재구성에 생성 규칙 적용 → 과거 데이터 로딩 실패 또는 ID 재발급

- **현상**: 생성 규칙을 강화한 배포 뒤 오래된 구독 상세 화면이 500 에러.
- **보이는 형태**: `IllegalArgumentException: 시작일이 과거: 2025-01-01`(실험 B)이 조회 경로에서 난다. 또는 재구성 때 새 UUID가 생겨 다른 객체처럼 취급된다.
- **원인**: 행 → 객체 변환이 공개 생성 팩토리를 탄다. 생성 시점 규칙과 저장 데이터의 구조 규칙을 구분하지 않았다.
- **대처**: 재구성 경로(`reconstitute`, JPA 무인자 생성자)를 분리하고 ID를 유지한다. 규칙 강화가 기존 데이터를 어떻게 다룰지(그대로 둠·마이그레이션·격리) 따로 결정한다.

### 4. 영속 지향 저장소에서 save 누락 → 변경이 조용히 사라짐

- **현상**: JPA에서 Spring Data JDBC로 옮긴 뒤 "배송 시작" 버튼을 눌러도 상태가 안 바뀐다.
- **보이는 형태**: 오류 없음. 메모리 객체는 바뀌었지만 DB에는 UPDATE가 없다.
- **원인**: JPA는 영속성 컨텍스트의 변경 추적이 커밋 때 UPDATE를 낸다(컬렉션 지향). Spring Data JDBC는 "저장하면 저장되고, 안 하면 안 된다. 더티 추적도 세션도 없다"(공식 문서).
- **대처**: 유스케이스 끝에서 `save`를 부르는 틀을 정한다. 저장소 스타일을 바꿀 때 모든 쓰기 경로를 점검한다. 통합 테스트는 다시 읽어 확인한다.

## 핵심 문장

- 리포지토리는 애그리거트 루트마다 하나, 메모리 컬렉션처럼 보이게 하고 저장 기술을 숨긴다. 내부 엔티티용 리포지토리는 루트를 건너뛰는 길이 된다.
- 쿼리 메서드가 늘어나는 것보다 위험한 것은 도메인 규칙이 쿼리에 복제되는 것이다(실험: 규칙 변경 뒤 불일치 10건). 명세 객체로 규칙의 출처를 하나로 모은다.
- 팩토리는 애그리거트를 불변식을 지킨 완성품으로 만든다. 생성자로 충분하면 생성자다.
- 생성과 재구성은 다르다. 재구성은 ID를 유지하고 생성 규칙을 다시 묻지 않는다(실험: 생성 경로로 옛 행을 읽으면 실패).
- 컬렉션 지향(JPA)과 영속 지향(Spring Data JDBC) 저장소는 save의 의미가 다르다.

## 관련 주제·근거

- 선행
  - [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md)
  - [02-pojo-and-persistence-ignorance](../02-pojo-and-persistence-ignorance/2-summary.md) · 원고 [pojo](../pojo/2-summary.md)
- 후속·연결
  - [database/25-data-source-patterns](../../database/25-data-source-patterns/2-summary.md) — Repository·Query Object·Data Mapper
  - [database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md) · [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md)
  - [08-domain-services-and-policies](../08-domain-services-and-policies/2-summary.md) · [21-cqrs](../21-cqrs/2-summary.md)(조회 모델 분리) · [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)(이벤트로 재구성)
  - [software-design/38-layered-hexagonal-clean](../../software-design/38-layered-hexagonal-clean/2-summary.md) — 포트(리포지토리 인터페이스)와 어댑터
  - 연습: [advanced/16-audit-replay](../advanced/16-audit-replay/2-summary.md)(저장된 기록으로 되살리기) · [advanced/10-price-history](../advanced/10-price-history/2-summary.md)
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015) "Repositories"·"Factories" 항목 <https://www.domainlanguage.com/ddd/reference/>
  - Eric Evans, 『Domain-Driven Design』(2003) 6장 FACTORIES·REPOSITORIES 절, 9장 SPECIFICATION — InformIT 목차 <https://www.informit.com/store/domain-driven-design-tackling-complexity-in-the-heart-9780321125217>; 재구성 팩토리 대목은 Goodreads 독자 발췌로 확인, 본문 미열람
  - Eric Evans·Martin Fowler, "Specifications" <https://martinfowler.com/apsupp/spec.pdf>
  - Martin Fowler 『PoEAA』 Repository(Edward Hieatt·Rob Mee) <https://martinfowler.com/eaaCatalog/repository.html>
  - Vaughn Vernon, 『Implementing Domain-Driven Design』(2013) 11장 Factories·12장 Repositories(Collection-Oriented / Persistence-Oriented, 목차·출판사 발췌로 확인) · "Effective Aggregate Design" Part I(2011) — 팩토리 역할의 루트 메서드
  - Spring Data JDBC Reference — "Domain Driven Design and Relational Databases"·"Why Spring Data JDBC?" <https://docs.spring.io/spring-data/relational/reference/jdbc/why.html>
  - Hibernate ORM 6.6 User Guide — Dynamic updates("The default UPDATE statement containing all columns…", `@DynamicUpdate`) <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
  - Jakarta Persistence 3.1 §2.1 The Entity Class(무인자 생성자) <https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>
- 실험 목록 (코드: scratchpad `dm/04/e10/Repo.java`, PostgreSQL 17.11 컨테이너 `sn-dm-w04-pg` + JDK 21.0.12 eclipse-temurin, 네트워크 `sn-dm-w04-net`, `--cpus=2`, `java -cp postgresql-42.7.4.jar Repo.java`, 3회, 실행 후 컨테이너 삭제)
  - A 규칙이 리포지토리 SQL에 복제 vs 명세 객체 — 불일치 10건 vs 0건
  - B 재구성을 생성 경로로 vs 재구성 경로 — 로딩 실패 vs ID 유지
  - C Hibernate 기본 UPDATE vs `@DynamicUpdate` — scratchpad `dm/04/adj/Adj.java`, Hibernate 6.6.29 + H2 2.3.232 메모리 DB, JDK 21 eclipse-temurin `--cpus=2`, `javac -cp '../libs/*' -d out Adj.java && java -Dhibernate.show_sql=true -cp 'out:../libs/*' Adj`, 1회: 모든 열 SET vs `title`만 SET
