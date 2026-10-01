# database/25-data-source-patterns — 데이터 소스 패턴: 누가 SQL을 아는가 — 정리 (힌트)

## 해결하는 문제

SQL을 코드 어디에 둘지 정하지 않으면, SQL이 비즈니스 규칙 사이에 흩어진다.

```text
  class OrderService {
     void cancel(long id) {
        ResultSet rs = conn.prepareStatement("SELECT status, paid_at FROM orders WHERE id=?")...
        if (rs.getString("status").equals("SHIPPED")) throw ...;     ← 규칙
        if (Duration.between(paidAt, now).toDays() > 7) refundFee();  ← 규칙
        conn.prepareStatement("UPDATE orders SET status='CANCELED' WHERE id=?")...
     }
  }
  → 규칙을 테스트하려면 DB가 필요하다
  → 스키마가 바뀌면 서비스 곳곳을 고친다
  → DBA가 튜닝할 SQL을 찾기 어렵다
```

- Fowler 『PoEAA』의 Table Data Gateway 설명: SQL을 앱 로직에 섞으면 문제가 생긴다. SQL에 익숙하지 않은 개발자가 많고, DBA는 SQL을 쉽게 찾아 튜닝·진화시킬 수 있어야 한다.
- 데이터 소스 패턴은 이 질문에 대한 답의 목록이다. **"누가 SQL을 아는가, 도메인 객체는 DB를 아는가."**

쉬운 예: 회사의 서류 창고다.
- 창고 담당자 한 명이 모든 서류 출납을 맡는다(게이트웨이).
- 직원이 자기 서류를 직접 창고에 넣고 뺀다(Active Record).
- 직원은 창고가 어디 있는지도 모르고, 중간 운반 팀이 옮긴다(Data Mapper).
- 직원은 "서류함"에 넣고 뺄 뿐이다. 서류함 뒤에 운반 팀이 있다(Repository).

똑같은 구조다.\
패턴의 차이는 **SQL과 매핑 지식이 어디에 있고, 도메인 객체가 그것에 얼마나 의존하나**다.

실무 예:
- Rails의 ActiveRecord는 Active Record 패턴이다. Rails 가이드가 Fowler가 책에서 설명한 패턴이라고 밝힌다. TypeORM은 두 방식(Active Record·Data Mapper)을 모두 지원한다고 문서에 적는다.
- JPA/Hibernate는 Data Mapper + Metadata Mapping(어노테이션)이다. Spring Data의 `Repository` 인터페이스가 그 앞에 선다.
- 조건 조합 검색 화면은 Query Object(JPA Criteria, Spring Data `Specification`, QueryDSL)로 만든다.

## 동작·원리

### 1. 네 가지 데이터 소스 아키텍처 패턴 (PoEAA 10장)

```text
                      SQL을 아는 자        한 인스턴스 = ?       도메인 로직이 어디에?
  Table Data Gateway  게이트웨이           테이블(또는 뷰) 전체   바깥(서비스·트랜잭션 스크립트)
  Row Data Gateway    게이트웨이           행 하나              바깥
  Active Record       도메인 객체 자신       행 하나              그 객체 안 (데이터 + 로직 + SQL)
  Data Mapper         매퍼(별도 층)         (매퍼는 객체와 무관)    보통 도메인 객체 안(Domain Model과 짝) — DB를 모름
```

**Table Data Gateway** — "DB 테이블의 관문 역할을 하는 객체. 인스턴스 하나가 테이블의 모든 행을 다룬다." 한 테이블의 SELECT·INSERT·UPDATE·DELETE SQL을 전부 가진다.

```java
class OrderGateway {                               // 테이블 하나에 하나
    List<Map<String, Object>> findByCustomer(long cid) { return jdbc.queryForList("SELECT ... WHERE customer_id=?", cid); }
    int updateStatus(long id, String s)            { return jdbc.update("UPDATE orders SET status=? WHERE id=?", s, id); }
}
```

**Row Data Gateway** — "데이터 소스의 레코드 하나에 대한 관문. 행마다 인스턴스가 하나." 레코드와 똑같이 생긴 객체에 `insert()`·`update()`가 있다. 비즈니스 로직은 넣지 않는다.

**Active Record** — "테이블·뷰의 행 하나를 감싸고, DB 접근을 캡슐화하며, 그 데이터에 도메인 로직을 더한 객체." 가장 직관적인 방식이다: 데이터 접근 로직을 도메인 객체에 넣는다.

```java
class Order {                                      // 데이터 + 규칙 + SQL이 한 클래스
    long id; String status; Instant paidAt;
    static Order find(long id) { /* SELECT ... */ }
    void cancel(Clock c) {
        if (status.equals("SHIPPED")) throw new IllegalStateException();
        status = "CANCELED";
        save();                                    // UPDATE orders SET ...
    }
    void save() { /* UPDATE ... */ }
}
```

**Data Mapper** — "객체와 DB 사이에서 데이터를 옮기되, 둘을 서로에게서 그리고 매퍼 자신에게서 독립시키는 매퍼들의 층." 도메인 객체는 DB가 있다는 것조차 몰라도 된다. SQL 인터페이스 코드도, 스키마 지식도 필요 없다(Fowler 카탈로그).

```java
final class Order {                                // 순수 도메인 — DB 모름
    private final long id; private Status status; private final Instant paidAt;
    void cancel(Instant now) { if (status == Status.SHIPPED) throw new IllegalStateException(); status = Status.CANCELED; }
}
class OrderMapper {                                // SQL과 매핑은 여기만
    Order find(long id) { return jdbc.queryForObject("SELECT id, status, paid_at FROM orders WHERE id=?", this::toOrder, id); }
    void update(Order o) { jdbc.update("UPDATE orders SET status=? WHERE id=?", o.status().name(), o.id()); }
}
```

- 객체 쪽에는 컬렉션·상속이 있고 관계형 쪽에는 없다. 도메인 로직이 많을수록 두 스키마가 어긋난다. 도메인 객체가 테이블 구조를 알면 한쪽 변경이 다른 쪽으로 번진다(Fowler Data Mapper). 원고 [jpa.md](../../engineering/data-access/jpa.md) §1도 이 불일치에서 출발한다.

### 2. 매퍼를 받치는 패턴들 (PoEAA 11장·13장)

```text
  [Repository]  ← 도메인이 보는 것: "메모리 안 컬렉션처럼"  (13장)
       │ 조건(Query Object)을 넘김                        (13장)
       ▼
  [Data Mapper] ── [Metadata Mapping: 필드 ↔ 컬럼 표]     (13장)
       │           ── [Identity Map] [Unit of Work] [Lazy Load]   (11장, 23번)
       ▼
      DB
```

**Metadata Mapping** — "객체–관계 매핑의 세부를 메타데이터로 둔다." 필드↔컬럼 대응을 표 형태로 선언하고, 범용 코드가 그 표를 읽어 읽기·삽입·갱신을 수행한다. 손으로 쓴 매퍼의 반복 코드가 사라진다.
  - JPA의 `@Entity`·`@Column`·`@OneToMany` 어노테이션, 또는 `orm.xml`(Jakarta Persistence 3.1 12장)이 이 메타데이터다.

**Query Object** — "DB 쿼리를 표현하는 객체." Fowler는 이것을 **인터프리터**라고 부른다. 객체 구조가 스스로 SQL로 바뀐다. 테이블·컬럼 대신 클래스·필드로 쿼리를 쓰므로 스키마 변경을 한곳에서 흡수한다.
  - JPA Criteria API(Jakarta Persistence 3.1 6장), Spring Data JPA `Specification`, QueryDSL이 이 모양이다.

**Repository** — "도메인과 데이터 매핑 층 사이를 중재하며, 메모리 안 도메인 객체 컬렉션처럼 동작한다." 클라이언트는 쿼리 명세를 선언적으로 만들어 넘긴다. 객체를 컬렉션처럼 더하고 뺀다. 도메인 층과 데이터 매핑 층을 깨끗이 분리하고, **한 방향 의존**을 만든다(Fowler 카탈로그).
  - Fowler는 이 패턴의 좋은 설명이 『Domain-Driven Design』에도 있다고 덧붙인다(카탈로그 Note). DDD 쪽 설명은 domain-modeling/10-repositories-and-factories(미작성, [domain-modeling 영역 표](../../domain-modeling/curriculum.md)).

### 3. "누가 SQL을 아는가"로 다시 보기

```text
                  도메인 객체가 아는 것          SQL 작성 위치              DB 없이 규칙 테스트
  TDG / RDG       (도메인 객체 없음 또는 빈약)     게이트웨이                  스크립트를 목(mock)으로
  Active Record   자기 테이블·SQL               도메인 클래스 안             규칙이 DB 접근과 섞이면 어렵다
  Data Mapper     아무것도                     매퍼(손으로·메타데이터로)      쉽다
  + Repository    컬렉션 인터페이스               매퍼 뒤                    쉽다(가짜 저장소)
```

- 도메인 로직이 단순하고 테이블과 1:1이면 Active Record가 가장 짧다.
- 도메인 로직이 크고 객체 구조가 테이블과 달라질수록 Data Mapper가 값을 낸다.
- 선택 기준은 우열이 아니라 **도메인 로직의 복잡도와 스키마 불일치의 크기**다. 원고 [comparison.md](../../engineering/data-access/comparison.md)는 JPA와 Spring Data JDBC(둘 다 Data Mapper 계열)를 "쓰기가 그래프 저장이냐 상태 전이냐"로 가른다.

## 쓰이는 자료구조·알고리즘

- **메타데이터 매핑 표**: 엔티티마다 (필드 이름, 컬럼 이름, 타입 변환기, 식별자 여부, 연관 종류)의 목록이다. 범용 매퍼가 이 표를 순회해 `INSERT INTO t (c1, c2) VALUES (?, ?)`를 조립하고, 결과 행을 필드에 채운다.

```text
  Order ─ table "orders"
  ┌─────────┬───────────┬──────────────┬──────┐
  │ field   │ column    │ converter    │ id?  │
  │ id      │ id        │ long         │ yes  │
  │ status  │ status    │ enum→String  │      │
  │ paidAt  │ paid_at   │ Instant→ts   │      │
  └─────────┴───────────┴──────────────┴──────┘
  → 순회: "INSERT INTO orders (id, status, paid_at) VALUES (?, ?, ?)"
```

- **쿼리 객체 = 조건 AST(인터프리터 패턴)**: 조건을 트리로 만들고, 방문하며 SQL 조각과 바인딩 값을 만든다.

```text
         AND
        /    \
   EQ(status,'PAID')   OR
                      /   \
          GT(amount,1000)  EQ(vip,true)
  → 재귀 방문(왼쪽 → 연산자 → 오른쪽): "status = ? AND (amount > ? OR vip = ?)"   binds: [PAID, 1000, true]
```

```java
sealed interface Cond permits Eq, Gt, And, Or {}
record Eq(String col, Object v) implements Cond {}
record Gt(String col, Object v) implements Cond {}
record And(Cond l, Cond r) implements Cond {}
record Or(Cond l, Cond r) implements Cond {}

static String toSql(Cond c, List<Object> binds) {
    return switch (c) {
        case Eq e  -> { binds.add(e.v()); yield e.col() + " = ?"; }
        case Gt g  -> { binds.add(g.v()); yield g.col() + " > ?"; }
        case And a -> toSql(a.l(), binds) + " AND " + toSql(a.r(), binds);
        case Or o  -> "(" + toSql(o.l(), binds) + " OR " + toSql(o.r(), binds) + ")";
    };
}
```

  - 컬럼 이름은 코드가 정한 값만 쓰고, 사용자 입력은 바인딩(`?`)으로만 넣는다. 그래야 SQL 주입이 막힌다.
- **식별자 맵·작업 단위**: Data Mapper를 쓰면 곧 필요해진다(같은 행 = 같은 객체, 변경 추적). 자세한 동작은 [23](../23-orm-and-n-plus-one/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 고르는 순서

1. 도메인 로직이 얼마나 되나? 단순 CRUD·보고서 위주면 게이트웨이나 Active Record로 충분하다.
2. 도메인 객체의 모양이 테이블과 다른가(값 객체·컬렉션·상속)? 다르면 Data Mapper다.
3. 규칙을 DB 없이 테스트해야 하나? 그렇다면 Active Record는 피한다.
4. 조회 조건 조합이 많은가? Query Object를 둔다. 이름 파생 메서드로 버티지 않는다.
5. 도메인 층이 저장 기술에서 독립해야 하나? Repository 인터페이스를 도메인 쪽에 두고, 구현을 인프라 쪽에 둔다.

### 2. Spring Data 리포지토리를 비대하게 만들지 않기

```java
interface OrderRepository extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {
    // 이름 파생은 짧은 것만
    List<Order> findByCustomerId(long customerId);
    // findByStatusAndPaidAtBetweenAndCustomerVipOrAmountGreaterThan...  ← 이렇게 가지 않는다
}

// 조건 조합은 Query Object(Specification)로
static Specification<Order> status(Status s)       { return (r, q, cb) -> cb.equal(r.get("status"), s); }
static Specification<Order> amountOver(long a)      { return (r, q, cb) -> cb.gt(r.get("amount"), a); }
static Specification<Order> vip()                    { return (r, q, cb) -> cb.isTrue(r.get("customer").get("vip")); }

List<Order> hits = repo.findAll(status(PAID).and(amountOver(1000).or(vip())));
```

- Spring Data JPA 문서: 메서드 이름에서 쿼리를 파생하는 것은 편하지만, 이름 파서가 원하는 키워드를 지원하지 않거나 **메서드 이름이 불필요하게 흉해지는** 상황이 온다. 그때는 이름 있는 쿼리나 `@Query`를 쓰라고 적는다.
- 화면용 복잡 조회는 리포지토리가 아니라 별도 조회 층(`JdbcClient`·DTO 프로젝션)으로 뺀다. 원고 [spring-data-jdbc.md](../../engineering/data-access/spring-data-jdbc.md) §6의 "조회는 애그리게이트를 재구성하지 않는다"와 같다.

### 3. Data Mapper인데 도메인이 ORM에 묶였을 때

```text
  (a) 어노테이션을 도메인 클래스에 그대로 — 가장 흔함, 실용적
       @Entity class Order { @Id Long id; @Enumerated ... }   → 도메인이 jakarta.persistence에 의존
  (b) 매핑을 XML로 — orm.xml (Jakarta Persistence 3.1 12장)  → 도메인 클래스는 어노테이션 없음
  (c) 영속 모델 분리 — OrderEntity(어노테이션) ↔ Order(도메인), 매퍼로 변환
       → 순수하지만 변환 코드와 이중 모델 유지비
```

- 어느 쪽이든 **의존 방향**을 확인한다. 도메인 규칙 코드가 `EntityManager`·`Session`·지연 로딩 프록시 동작에 기대면, 이미 Data Mapper의 "서로 모른다"가 깨진 것이다.

### 4. TS의 모습

```ts
// Active Record 스타일 (예: TypeORM의 BaseEntity 상속)
const o = await Order.findOneBy({ id });
o.cancel();          // 규칙
await o.save();      // SQL — 같은 객체

// Data Mapper + Repository 스타일 (예: TypeORM DataSource.getRepository, Prisma client를 감싼 저장소)
const o = await orders.findById(id);   // 저장소가 SQL을 안다
o.cancel();                             // 순수 도메인
await orders.save(o);
```

## 장애 시나리오와 대처

### 1. Active Record로 복잡한 도메인 → DB 없이 테스트 불가

- 현상: 할인·환불 규칙 테스트가 느리고 불안정하다. 테스트마다 DB를 띄워 행을 넣어야 한다.
- 보이는 형태: 단위 테스트 실행 시간이 수 분이다. 규칙 테스트가 DB 연결 실패로 깨진다. 한 클래스가 수천 줄이고, 규칙 메서드 안에서 `save()`·`find()`가 불린다.
- 원인: 데이터·규칙·SQL이 한 클래스에 있고, 규칙 메서드가 `find()`·`save()`를 직접 부른다(규칙과 저장을 나눠 두면 Active Record여도 규칙만 테스트할 수 있다). Fowler Row Data Gateway 설명 그대로다: 인메모리 객체가 DB에 묶이면 테스트가 느리고 불편하다.
- 대처: 규칙을 DB 접근 없는 메서드로 먼저 뽑는다(값을 인자로 받고 결과를 돌려주는 함수). 규칙이 커진 애그리게이트부터 Data Mapper + Repository로 옮긴다.

### 2. Data Mapper인데 도메인이 ORM 어노테이션·동작에 의존

- 현상: 도메인 모듈만 따로 빌드·테스트할 수 없다. 규칙이 프록시 초기화 여부에 따라 다르게 동작한다.
- 보이는 형태: 도메인 패키지에 `import jakarta.persistence.*`와 `org.hibernate.*`. 테스트에서 `LazyInitializationException`. `equals`·`hashCode`가 프록시 클래스 때문에 틀린다.
- 원인: 메타데이터(어노테이션)와 ORM 런타임 동작(지연 로딩·더티 체킹)이 도메인 클래스에 스며들었다.
- 대처: 최소한 규칙 코드가 ORM 런타임에 기대지 않게 한다(연관을 규칙 메서드의 인자로 받는다). 순수성이 필요하면 `orm.xml`이나 영속 모델 분리를 쓴다. 비용과 이득을 비교해 애그리게이트 단위로 정한다.

### 3. 리포지토리가 `findByAAndBOrC…` 메서드 수십 개로 비대

- 현상: 새 검색 조건이 생길 때마다 리포지토리 메서드가 는다. 이름이 한 줄을 넘는다.
- 보이는 형태: `findByStatusAndCreatedAtBetweenAndCustomerGradeInOrAmountGreaterThanOrderByIdDesc` 같은 메서드. 조건 조합마다 메서드가 중복된다.
- 원인: 이름 파생 쿼리로 조건 조합을 표현했다. 조합 수만큼 메서드가 필요하다. Spring Data 문서도 이름이 흉해지는 경우를 한계로 적는다.
- 대처: 조건은 Query Object(`Specification`·Criteria·QueryDSL)로 조립한다. 화면 조회는 별도 조회 층으로 뺀다. 리포지토리는 애그리게이트 단위의 저장·로드만 둔다.

### 4. 게이트웨이·스크립트가 커져 규칙이 SQL에 숨는다

- 현상: 같은 규칙("취소 가능 여부")이 서비스 세 곳의 SQL WHERE 절에 조금씩 다르게 있다.
- 보이는 형태: 버그 수정 뒤에도 다른 화면에서 같은 버그가 재발한다. 조건 문자열 grep으로만 찾을 수 있다.
- 원인: Table Data Gateway + 트랜잭션 스크립트 구조에서 규칙이 쿼리 조건으로 흩어졌다.
- 대처: 규칙을 이름 있는 한 곳으로 모은다. 도메인 메서드로 모으거나, 이름 있는 Query Object 조각(`cancellable()`)으로 모은다. DB 제약으로 표현할 수 있는 불변식은 제약으로 옮긴다([02-keys-and-constraints](../02-keys-and-constraints/2-summary.md)).

## 핵심 문장

- 데이터 소스 패턴의 차이는 "누가 SQL을 아는가, 도메인 객체가 DB를 아는가"다.
- Table/Row Data Gateway는 SQL을 관문 객체에 모으고, Active Record는 행 + 규칙 + DB 접근을 한 객체에 둔다(SQL은 손으로 쓰거나 Rails처럼 프레임워크가 만든다).
- Data Mapper는 도메인 객체와 DB를 서로 모르게 하는 별도 층이다. JPA/Hibernate는 Data Mapper + Metadata Mapping이다.
- Repository는 매퍼 앞의 "메모리 안 컬렉션" 인터페이스로, 도메인과 매핑 층 사이에 한 방향 의존을 만든다. 매핑 층(구현)이 도메인을 알고, 도메인은 매핑 층을 모른다.
- Query Object는 조건을 객체 트리(AST)로 만들고 SQL로 해석하는 인터프리터다. 이름 파생 메서드 폭증의 해법이다.
- 도메인이 단순하면 Active Record가 가장 짧고, 규칙이 크고 스키마와 어긋날수록 Data Mapper가 값을 낸다.

## 관련 주제·근거

- 선행
  - [23-orm-and-n-plus-one](../23-orm-and-n-plus-one/2-summary.md) — Identity Map·Unit of Work·Lazy Load가 실제로 도는 모습
  - domain-modeling/10-repositories-and-factories — 미작성([domain-modeling 영역 표](../../domain-modeling/curriculum.md))
- 연결
  - 원고 [engineering/data-access/comparison.md](../../engineering/data-access/comparison.md) — Data Mapper 계열 두 도구의 선택 기준(원고에 "Data Mapper 절"이 따로 있지는 않고, Data Mapper 정의는 [jpa.md](../../engineering/data-access/jpa.md) §1에 있다)
  - [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md) — 리포지토리 호출을 감싸는 트랜잭션 경계
  - [51-object-relational-structural-mapping](../51-object-relational-structural-mapping/2-summary.md) · [52-offline-concurrency-patterns](../52-offline-concurrency-patterns/2-summary.md)
- 문서
  - Fowler 『Patterns of Enterprise Application Architecture』(2002) 10장 Data Source Architectural Patterns(Table Data Gateway·Row Data Gateway·Active Record·Data Mapper), 11장(Identity Map·Unit of Work·Lazy Load), 13장 Object-Relational Metadata Mapping Patterns(Metadata Mapping·Query Object·Repository) — 카탈로그 요약 <https://martinfowler.com/eaaCatalog/>
  - Jakarta Persistence 3.1 명세 6장 Criteria API, 12장 XML Object/Relational Mapping Descriptor <https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>
  - Spring Data JPA 레퍼런스 "Query Methods"(이름 파생의 한계·`@Query`) <https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html> · "Specifications" <https://docs.spring.io/spring-data/jpa/reference/jpa/specifications.html>
  - Rails Guides "Active Record Basics" 1.1(Fowler의 Active Record 패턴) <https://guides.rubyonrails.org/active_record_basics.html>
  - TypeORM "Active Record vs Data Mapper" <https://typeorm.io/docs/guides/active-record-data-mapper/>
