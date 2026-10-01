# database/23-orm-and-n-plus-one — ORM의 영속성 컨텍스트와 N+1 — 정리 (힌트)

## 해결하는 문제

객체는 참조로 이어진 그래프이고, 테이블은 외래키 값으로 이어진 행이다(원고 §1).\
ORM은 그 사이의 변환과 "무엇을 읽었고 무엇을 바꿨나"라는 부기를 대신한다.

```text
  손으로 매핑                           ORM (JPA/Hibernate)
  SELECT → ResultSet → new Order(...)   em.find(Order.class, 1)
  바뀐 필드를 기억해 UPDATE 작성          필드만 바꾸면 커밋 때 UPDATE
  연관은 필요할 때 따로 SELECT            order.getLines() 를 만지면 SELECT
```

- 대가는 **SQL이 코드에서 사라진다**는 것이다. 어떤 SQL이 몇 번, 언제 나가는지 코드만 봐서는 모른다.

쉬운 예: 도서관 사서에게 "이 책들의 저자 정보도 줘"라고 한다.
- 사서가 책 목록을 한 번 가져온다(1).
- 그 다음 책마다 저자 서가에 **따로** 다녀온다(N).
- 처음에 "저자 정보도 같이"라고 말했으면 한 번에 가져올 수 있었다.

똑같은 구조다.\
ORM이 연관을 "만질 때 가져오기"로 두면, 목록을 도는 반복문이 쿼리를 N번 낳는다. 이것이 N+1이다.

실무 예:
- 주문 목록 API가 개발 DB(주문 10건)에서는 빠른데, 운영(1000건)에서는 쿼리 1001번으로 느리다. 쿼리 하나하나는 1ms라 슬로 쿼리 로그에 안 걸린다.
- 컨트롤러에서 `order.getLines()`를 부르자 `LazyInitializationException: ... could not initialize proxy - no Session`.
- 화면 표시용으로 엔티티의 이름을 마스킹했더니 DB 값까지 마스킹된 채 저장됐다.

## 동작·원리

### 1. 영속성 컨텍스트 = 식별자 맵 + 로드 시점 상태

```text
  Session (영속성 컨텍스트)
  ┌────────────────────────────────────────────────────────────┐
  │ entitiesByKey : HashMap<EntityKey(엔티티 이름, id), 엔티티>   │ ← 식별자 맵
  │   (Order,1) → Order@a1   (Order,2) → Order@b2              │
  │ 엔티티마다 loaded state (마지막으로 DB와 맞춘 값의 복사)       │ ← 더티 체킹 기준
  │ 행동 큐: INSERT / UPDATE / DELETE (flush 때 SQL로)           │ ← 작업 단위
  └────────────────────────────────────────────────────────────┘
       │ em.find(Order,1) → 맵에 있으면 SQL 없이 같은 객체 반환
       │ flush → 엔티티마다 현재 값 vs loaded state 비교 → 바뀐 것만 UPDATE
```

- Hibernate 6.6 소스 `StatefulPersistenceContext`는 `HashMap<EntityKey, EntityHolderImpl> entitiesByKey`를 가진다. PoEAA의 **Identity Map**이다(원고 §2).
- 더티 체킹은 기본이 **비교 방식**이다. Hibernate 사용자 가이드 6.2.2: 마지막으로 알려진 DB 상태를 들고 있다가, flush 때 컨텍스트의 (변경 가능한) **모든 엔티티**를 돌며 현재 상태와 비교한다. 읽기 전용으로 읽은 엔티티는 더티 체킹에서 빠진다(가이드 16.3.7).
  - 엔티티가 많은 컨텍스트에서는 이 비교가 느려질 수 있다고 가이드가 적는다. 대안은 바이트코드 강화로 엔티티가 스스로 바뀐 속성을 기록하는 방식이다.
- 로컬 재현(예시, PostgreSQL 17.11, Hibernate 6.6.29): 같은 트랜잭션에서 `find(PurchaseOrder, 2)`를 두 번 부르자 SQL은 한 번, `same instance: true`.

### 2. flush 시점 — "쿼리 직전"은 겹칠 때만

```text
  코드                                        실제 SQL (로컬 재현)
  o = s.find(PurchaseOrder, 2)                select ... from purchase_order where id=?
  o.customer = o.customer + "!"               (없음)
  s.createSelectionQuery(                     update purchase_order set customer=? where id=?  ← 먼저 flush
     "select count(o) from PurchaseOrder o    select count(po1_0.id) from purchase_order ...
      where o.customer like 'c%'")
  (트랜잭션 끝)                                (commit)
```

- save() 호출이 없는데 UPDATE가 나갔다. 그것도 **조회 한 줄 앞에서** 나갔다.
- Hibernate 사용자 가이드 7.1 AUTO flush: flush가 일어나는 때는 셋이다.
  - 트랜잭션 커밋 직전.
  - 밀린 엔티티 작업과 **겹치는** JPQL/HQL 쿼리 직전.
  - 네이티브 SQL 쿼리 직전 — API에 따라 다르다. JPA `EntityManager`로 실행하면 항상 flush한다. Hibernate를 네이티브로 부트스트랩한 `Session`에서는 `addSynchronizedEntityClass` 같은 동기화 정보를 등록해야 flush한다(가이드 7.1.3 예제 441~443).
  - 겹치지 않는 테이블을 조회하면 flush하지 않는다(가이드 예제 "no overlapping").
- > 참고: 원본 [jpa.md](../../engineering/data-access/jpa.md) §5의 "쿼리를 실행하기 직전에 밀린 변경을 먼저 내보낸다"는 Hibernate 기준으로 "밀린 변경과 **겹치는** 쿼리 직전"이 정확하다(Hibernate 6.6 User Guide 7.1).

### 3. 지연 로딩과 N+1 — 실제 SQL

엔티티: `PurchaseOrder 1 ─< OrderLine N`, `@OneToMany(mappedBy="order", fetch=LAZY)`. 주문 5건, 주문마다 항목 3개.

```text
  (a) 기본 — 목록 1번 + 주문마다 1번                    prepared statements = 6
  select ... from purchase_order order by id
  select ... from order_line where order_id=?     × 5

  (b) hibernate.default_batch_fetch_size=10          prepared statements = 2
  select ... from purchase_order order by id
  select ... from order_line where order_id = any (?)     ← id 배열 하나로 묶음(PostgreSQL)

  (c) JPQL select distinct o ... join fetch o.lines  prepared statements = 1
  select distinct po.id, po.customer, l.order_id, l.id, l.product
  from purchase_order po join order_line l on po.id = l.order_id order by po.id
```

- 로컬 재현(예시, PostgreSQL 17.11, Hibernate 6.6.29)에서 Hibernate 통계의 문장 수가 6 → 2 → 1로 줄었다.
- 기본값 확인(Jakarta Persistence 3.1 API): `@OneToMany`·`@ManyToMany`의 `fetch` 기본은 **LAZY**, `@ManyToOne`·`@OneToOne`은 **EAGER**다.
- EAGER도 N+1을 막지 못한다. JPQL은 쿼리에 쓴 대로 SQL을 만들고, EAGER 연관은 **그 뒤에 따로** 채운다.

```text
  @ManyToOne(기본 EAGER) OrderLine.order, JPQL "from Line order by id"  (로컬 재현)
  select ... from order_line order by id                    ← 15행
  select ... from purchase_order where id=?   × 5            ← 서로 다른 주문 5개만
  prepared statements = 6
```

- 추가 쿼리는 행 수(15)가 아니라 **서로 다른 부모 수(5)** 만큼이다. 식별자 맵이 이미 읽은 주문을 다시 읽지 않기 때문이다. 부모가 모두 다르면 행 수만큼 나간다.

### 4. 컬렉션 fetch join + 페이징 = 메모리에서 자른다

```text
  "select o from PurchaseOrder o join fetch o.lines order by o.id"  + setMaxResults(2)
  WARN: HHH90003004: firstResult/maxResults specified with collection fetch; applying in memory
  SQL: select ... from purchase_order po join order_line l ... order by po.id    ← LIMIT 없음!
```

- 조인 결과는 "주문 × 항목" 행이라 LIMIT 2를 SQL에 붙이면 주문 단위로 자를 수 없다. 그래서 Hibernate는 **전부 읽고 메모리에서** 자른다(User Guide: "must retrieve all matching results ... apply the limit in memory").
- 주문 100만 건이면 100만 건을 읽는다. `hibernate.query.fail_on_pagination_over_collection_fetch=true`로 두면 경고 대신 예외를 던진다(기본 false).
- 해법: 부모 id만 페이징으로 먼저 조회한 뒤 → 그 id들로 자식을 fetch(또는 batch fetch).

### 5. `LazyInitializationException` — 세션이 닫힌 뒤의 프록시

```text
  트랜잭션 안: o = find(PurchaseOrder, 1)   → o.lines = 초기화 안 된 컬렉션 래퍼
  트랜잭션 끝: Session 닫힘
  밖에서:      o.lines.size()
  → org.hibernate.LazyInitializationException: failed to lazily initialize a collection of role:
    OrmRepro$PurchaseOrder.lines: could not initialize proxy - no Session      (로컬 재현)
```

- 지연 연관은 **살아 있는 Session(과 그 커넥션)**이 있어야 채울 수 있다.
- 회피책 Open Session in View(OSIV)는 요청이 끝날 때까지 EntityManager를 스레드에 붙여 둔다. Spring Boot의 `spring.jpa.open-in-view` 기본값은 **true**다(Spring Boot 속성 부록).
  - 대가: 뷰 렌더링 중에도 지연 로딩 SQL이 나가고, 그동안 커넥션을 쥔다. Spring의 `HibernateJpaVendorAdapter`는 리소스 로컬 기본에서 연결 처리 모드를 `DELAYED_ACQUISITION_AND_HOLD`로 둔다. 처음 DB를 쓸 때 커넥션을 얻고, EntityManager가 닫힐 때(OSIV면 요청 끝)까지 쥔다. 풀이 더 빨리 마른다([21](../21-connection-pooling/2-summary.md)).
- 정석은 트랜잭션 안에서 필요한 연관을 **쿼리로 말해 가져오는** 것이다. fetch join, 엔티티 그래프, DTO 프로젝션이다(Hibernate User Guide: "fetch all the required associations prior to closing the Persistence Context").

## 쓰이는 자료구조·알고리즘

- **식별자 맵(Identity Map)**: `HashMap<EntityKey, 엔티티>`. 키는 (엔티티 이름, id)다. "한 행 = 한 객체"를 지키고, 같은 id의 두 번째 조회를 SQL 없이 끝낸다([해시맵](../../data-structure/05-hashmap/)).
- **작업 단위(Unit of Work)**: 삽입·갱신·삭제 행동을 모아 두었다가 flush 때 SQL 순서로 내보낸다.
- **스냅샷 비교(diff)**: 엔티티별 loaded state 배열과 현재 값을 속성마다 비교한다. 비용은 컨텍스트 안 엔티티 수 × 속성 수에 비례한다.
- **프록시(대리 객체)**: 지연 연관 자리에 실제 객체 대신 "처음 만질 때 로드하는" 객체를 둔다. PoEAA의 Lazy Load(가상 프록시)다.
- **배치 fetch = IN/ANY 묶기**: 초기화를 기다리는 id들을 모아 `where fk = any(?)` 한 번으로 가져온다. 쿼리 수가 N → ⌈N / 배치 크기⌉로 준다.
- 조인 자체의 알고리즘(중첩 루프·해시·병합)은 [11-join-algorithms](../11-join-algorithms/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 먼저 보이게 만든다

```properties
# 개발·테스트
hibernate.show_sql=true              # 또는 org.hibernate.SQL 로거 DEBUG
hibernate.generate_statistics=true   # 세션 끝에 "N JDBC statements" 요약
```

- 로컬 재현의 통계 출력 예(예시): `2686381 nanoseconds spent preparing 6 JDBC statements; ... 1 flushes (flushing a total of 20 entities and 5 collections)`.
- 테스트에서 "이 API는 문장 3개 이하"처럼 **쿼리 수를 단언**하면 N+1 회귀를 잡는다(`SessionFactory.getStatistics().getPrepareStatementCount()`).
- 운영에서는 `pg_stat_statements`의 `calls`가 요청 수보다 수십 배 많은 짧은 쿼리가 N+1의 흔적이다.

```sql
-- PostgreSQL: 호출 수가 많고 평균 시간이 짧은 쿼리 (pg_stat_statements 확장 필요)
SELECT calls, round(mean_exec_time::numeric, 2) AS mean_ms, left(query, 80)
FROM pg_stat_statements ORDER BY calls DESC LIMIT 10;
```

### 2. 고치는 순서 — "가져올 것을 쿼리에서 말한다"

```java
// (1) 목록 + 연관을 한 번에: fetch join (컬렉션이면 페이징과 함께 쓰지 않는다)
List<PurchaseOrder> os = em.createQuery(
    "select o from PurchaseOrder o join fetch o.lines where o.customer = :c", PurchaseOrder.class)
  .setParameter("c", c).getResultList();

// (2) 페이징이 필요하면: id 먼저, 자식은 batch fetch
List<Long> ids = em.createQuery("select o.id from PurchaseOrder o order by o.id", Long.class)
  .setFirstResult(0).setMaxResults(20).getResultList();
// + @BatchSize(size = 50) 또는 hibernate.default_batch_fetch_size=50

// (3) 화면용 조회는 엔티티가 아니라 DTO로 — 더티 체킹·지연 로딩 대상 자체가 없다
record OrderRow(long id, String customer, long lineCount) {}
List<OrderRow> rows = em.createQuery("""
    select new com.example.OrderRow(o.id, o.customer, count(l))
    from PurchaseOrder o left join o.lines l group by o.id, o.customer""", OrderRow.class)
  .getResultList();
```

- `@ManyToOne`은 `fetch = FetchType.LAZY`로 바꿔 두고, 필요한 곳에서 fetch join한다. EAGER 기본값은 쿼리마다 원하지 않는 추가 SELECT를 낳을 수 있다(§3).
- Hibernate 6부터 join fetch로 생긴 중복 부모는 Hibernate가 메모리에서 제거한다(User Guide). `distinct`를 쓰지 않아도 된다.
  - 쓰면 SQL에도 `select distinct`가 그대로 붙는다(§3 (c) 로컬 재현). DB가 중복 제거를 한 번 더 하는 셈이다.

### 3. 의도치 않은 UPDATE를 막는다

- 표시용 가공은 엔티티가 아니라 **복사본(DTO)**에 한다.
- 읽기 전용 조회는 읽기 전용 힌트나 읽기 전용 트랜잭션을 쓴다(Spring `@Transactional(readOnly = true)`의 효과는 [24](../24-transaction-boundaries-in-app-code/2-summary.md)).
- 엔티티를 바꾸는 코드는 도메인 메서드 한 곳으로 모은다. "어디서 DB에 쓰나"를 코드가 답하게 한다(원고 §4의 청구서).

### 4. TS에서도 같은 구조다

```ts
// TypeORM·Prisma 등도 "목록 뒤 반복문 안 연관 조회"를 쓰면 같은 N+1이 난다
const orders = await db.query("SELECT id FROM purchase_order");
for (const o of orders.rows) {
  await db.query("SELECT * FROM order_line WHERE order_id = $1", [o.id]); // N번
}
// 해법도 같다: 한 번에 묶는다
await db.query("SELECT * FROM order_line WHERE order_id = ANY($1)", [orders.rows.map(o => o.id)]);
```

## 장애 시나리오와 대처

### 1. N+1 쿼리 폭증

- 현상: 목록 API가 데이터가 늘수록 선형으로 느려진다. DB CPU와 네트워크 왕복이 는다.
- 보이는 형태: `show_sql` 로그에 같은 `where order_id=?`가 반복된다. `pg_stat_statements`에서 짧은 쿼리의 `calls`가 폭증한다. 슬로 쿼리 로그에는 아무것도 없다.
- 원인: 지연 연관을 반복문에서 만진다. 또는 EAGER `@ManyToOne`을 JPQL로 읽어 추가 SELECT가 붙는다(§3).
- 대처: fetch join·엔티티 그래프·batch fetch·DTO 프로젝션. 테스트에 쿼리 수 단언을 넣어 재발을 막는다.

### 2. `LazyInitializationException`

- 현상: 서비스 계층 테스트는 통과했는데, 컨트롤러·직렬화(JSON 변환) 단계에서 실패한다.
- 보이는 형태: `org.hibernate.LazyInitializationException: failed to lazily initialize a collection of role: ...: could not initialize proxy - no Session`.
- 원인: 트랜잭션(Session)이 닫힌 뒤 지연 연관을 만졌다. detached 엔티티를 그대로 응답으로 직렬화하는 경우가 흔하다.
- 대처: 트랜잭션 안에서 필요한 연관을 fetch하고 DTO로 바꿔 돌려준다. OSIV로 덮으면 커넥션 점유가 늘어난다. 엔티티를 직접 JSON으로 내보내지 않는다.

### 3. 더티 체킹으로 의도치 않은 UPDATE

- 현상: 조회 API를 호출했을 뿐인데 DB 값이 바뀌었다. 또는 조회 API에서 UPDATE 락 대기가 생긴다.
- 보이는 형태: SQL 로그에 조회 트랜잭션의 `update ... set ...`. 조회 쿼리 **앞**에 UPDATE가 끼어 있기도 하다(AUTO flush, §2).
- 원인: managed 엔티티의 필드를 표시용으로 바꿨다(마스킹·포맷·정렬용 가공). 커밋이나 겹치는 쿼리 직전에 flush된다.
- 대처: 표시용 가공은 DTO에서 한다. 읽기 전용 경로는 읽기 전용 트랜잭션·힌트로 연다. 엔티티 setter를 공개하지 않는다.

### 4. 컬렉션 fetch join + 페이징으로 메모리 폭증

- 현상: 20건짜리 페이지 조회인데 앱 메모리가 치솟고 느리다.
- 보이는 형태: `WARN: HHH90003004: firstResult/maxResults specified with collection fetch; applying in memory`. SQL에 LIMIT이 없다.
- 원인: 컬렉션 fetch join 결과는 부모×자식 행이라 SQL에서 부모 단위로 자를 수 없다. Hibernate가 전부 읽고 메모리에서 자른다.
- 대처: 부모 id를 먼저 페이징한 뒤 자식을 batch fetch한다. `hibernate.query.fail_on_pagination_over_collection_fetch=true`로 이런 쿼리를 막는다.

### 5. 벌크 UPDATE 뒤 컨텍스트와 DB가 어긋난다

- 현상: 같은 트랜잭션에서 벌크 UPDATE를 한 뒤 엔티티를 다시 읽었는데 옛 값이 보인다.
- 보이는 형태: 예외 없이 틀린 값이 나온다(조용한 불일치).
- 원인: Hibernate User Guide: update·delete 문의 효과는 영속성 컨텍스트와 메모리의 엔티티에 **반영되지 않는다**. 동기화는 애플리케이션 책임이다. 식별자 맵이 옛 객체를 그대로 돌려준다.
- 대처: 벌크 작업은 트랜잭션 앞쪽에서 하거나, 뒤에 `em.clear()`·`refresh()`로 컨텍스트를 비운다(원고 [comparison.md](../../engineering/data-access/comparison.md) §2의 "벌크 쿼리는 컨텍스트에 반영 안 됨").

## 핵심 문장

- 영속성 컨텍스트는 **식별자 맵 + 로드 시점 상태 + 작업 큐**다. 동일성 보장, 더티 체킹, flush가 모두 여기서 나온다.
- 더티 체킹은 flush 때 컨텍스트의 엔티티를 스냅샷과 비교한다. save() 없이도, 조회 쿼리 앞에서도 UPDATE가 나갈 수 있다.
- N+1은 "목록 1번 + 연관 N번"이다. 쿼리 하나하나는 빨라서 슬로 로그에 안 걸리고, 호출 수로 드러난다.
- EAGER는 N+1의 해법이 아니다. 해법은 가져올 것을 쿼리에서 말하는 것이다(fetch join·엔티티 그래프·batch fetch·DTO).
- 컬렉션 fetch join에 페이징을 붙이면 Hibernate는 LIMIT 없이 전부 읽고 메모리에서 자른다.
- 지연 연관은 살아 있는 Session이 있어야 채운다. OSIV로 덮으면 (Spring 기본 연결 처리에서) 첫 DB 접근부터 요청 끝까지 커넥션을 쥔다.

## 관련 주제·근거

기초 설명은 원고 [engineering/data-access/jpa.md](../../engineering/data-access/jpa.md)에 있다. §1 객체–테이블 불일치, §2 영속성 컨텍스트, §3 생명주기 4상태, §4 더티 체킹, §5 flush, §6 지연 로딩, §7 N+1, §8 숨은 SQL. 이 노트는 원고를 되풀이하지 않고 **DB에 실제로 나가는 SQL**, 내부 자료구조, 장애 진단을 채운다.

- 원고(기초 설명): [engineering/data-access/jpa.md](../../engineering/data-access/jpa.md) · [spring-data-jdbc.md](../../engineering/data-access/spring-data-jdbc.md) · [comparison.md](../../engineering/data-access/comparison.md) · [README.md](../../engineering/data-access/README.md)
- 선행
  - [21-connection-pooling](../21-connection-pooling/2-summary.md) — OSIV와 지연 로딩이 커넥션 점유를 늘리는 경로
- 후속·연결
  - [24-transaction-boundaries-in-app-code](../24-transaction-boundaries-in-app-code/2-summary.md) — Session 수명 = 트랜잭션 경계
  - [25-data-source-patterns](../25-data-source-patterns/2-summary.md) — Data Mapper·Identity Map·Unit of Work가 PoEAA 어디에 속하나
  - [11-join-algorithms](../11-join-algorithms/2-summary.md) · [12-query-optimizer-and-explain](../12-query-optimizer-and-explain/2-summary.md) · [51-object-relational-structural-mapping](../51-object-relational-structural-mapping/2-summary.md) · [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md)(`@Version`)
- 문서
  - Fowler 『Patterns of Enterprise Application Architecture』 11장 Identity Map · Unit of Work · Lazy Load <https://martinfowler.com/eaaCatalog/>
  - Hibernate ORM 6.6 User Guide — 6.2.2 In-line dirty tracking, 7.1 AUTO flush, fetch join과 페이징("apply the limit in memory"), 벌크 update·delete와 영속성 컨텍스트, LazyInitializationException, 부록 설정 `hibernate.default_batch_fetch_size`·`hibernate.query.fail_on_pagination_over_collection_fetch` <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
  - Hibernate ORM 소스(6.6 브랜치) `hibernate-core/.../engine/internal/StatefulPersistenceContext.java`(`entitiesByKey`)
  - Jakarta Persistence 3.1 API — `@ManyToOne`(fetch 기본 EAGER)·`@OneToMany`(fetch 기본 LAZY)
  - Spring Boot 공통 속성 부록 — `spring.jpa.open-in-view`(기본 true)
  - Spring Framework 소스 `spring-orm/.../orm/jpa/vendor/HibernateJpaVendorAdapter.java`(`DELAYED_ACQUISITION_AND_HOLD` 강제) · Hibernate User Guide 7.1.3(네이티브 SQL AUTO flush)·16.3.7(읽기 전용 엔티티)
- 로컬 재현(PostgreSQL 17.11 · Hibernate 6.6.29 · pgjdbc 42.7.8): N+1 6문장 → batch fetch 2문장(`= any (?)`) → join fetch 1문장, EAGER `@ManyToOne` N+1(부모 5개 → 추가 5문장), 컬렉션 fetch join 페이징 HHH90003004, `LazyInitializationException`, 동일성 보장, save() 없는 UPDATE와 겹치는 쿼리 직전 flush
