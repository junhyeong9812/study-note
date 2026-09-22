# Spring Data JDBC — 애그리게이트 경계를 저장 경계로 삼는 도구

> 이 컬렉션의 인덱스는 [README.md](./README.md)에서 시작한다. 반대편 도구는 [jpa.md](./jpa.md), 둘의 축별 비교는 [comparison.md](./comparison.md)에 있다.\
> 출처: `jun-bank/docs/study/tech/data-access/spring-data-jdbc.md` · 이관일 2026-09-16.\
> 본문 절은 **원고**를 고쳐 쓴 것이다(문체·순서 유지, 특정 프로젝트 고유 상황을 일반 상황으로 — 도메인 고유 리스 예제는 일반 「잡 리스」 예제로 바꿨다). 「한눈에」·「전체 흐름」의 비유·그림과 맨 끝 `[Claude 추가]`는 **Claude가 원고 이해를 돕기 위해 보탠 것**이다. 인용은 Spring Data Relational 공식 레퍼런스와 저자 Jens Schauder의 spring.io 블로그 원문 기준이다.

**한 줄로**: 이 도구는 "JPA에서 기능을 뺀 가벼운 버전"이 아니라 **뺀 것 자체가 설계 목표인 도구**다. 애그리게이트 경계를 저장 경계로 삼고, 그 밖은 전부 명시 SQL로 남긴다.

---

## 한눈에 — 쉽게 말하면

**택배를 상자 단위로만 부치는 규칙**이라고 생각하면 된다. *(Claude 보강 — 원고에 없는 비유)*

```text
[JPA — 비서가 알아서]              [Spring Data JDBC — 상자 단위]
낱개로 아무 때나 부쳐 준다          부치는 단위는 "상자 하나(애그리게이트)"로 고정
  (더티체킹·프록시가 대신)           save(상자)  →  상자 통째로 나간다
언제 나갔는지는 비서만 안다          안 부치면 안 나간다. 그게 전부다
                                    상자 밖의 물건은 송장 번호(id)로만 가리킨다
```

**코드도 똑같은 구조다.** 저장 단위를 애그리게이트(상자)로 고정하면 "무엇을 언제 저장하나"가 사라진다 — `save()`를 부른 그 자리에서, 그 상자만 나간다.\
대신 상자로 안 담기는 일(조건부 갱신·목록 조회)은 **내가 직접 SQL로** 써야 한다. 감춰진 게 없는 만큼, 대신 해 주는 것도 없다.

---

## 이 개념이 답하려는 질문

[jpa.md](./jpa.md)에서 본 세 가지 청구서(숨은 쓰기 지점·flush 타이밍·숨은 읽기)를 **한꺼번에 없애면** 무엇으로 그 빈자리를 지탱하는가.

각 절이 답하는 질문을 미리 늘어놓으면 이렇다.

```text
§1  무엇을 왜 뺐나                    → 지연 로딩·캐싱·더티 트래킹 셋
§2  뺀 자리를 무엇으로 지탱하나        → 애그리게이트 = 저장 단위
§3  코드에선 그 경계가 어떻게 보이나    → 안쪽은 객체, 바깥쪽은 식별자
§4  저장은 어떻게 하나                → save() 하나, 그 안은 delete 후 insert
§5  "조건 참일 때만 바꿔라"는          → @Modifying 명시 쿼리로 직접
§6  목록·집계 조회는                  → 애그리게이트 재구성 안 함, JdbcClient로 직접
§7  경쟁은 어떻게 막나                → 낙관적 잠금은 기본, 그 이상은 SQL
§8  무엇을 직접 써야 하나              → 고르기 전에 알고 고른다
```

---

## 전체 흐름

이 도구는 "뺀다"에서 출발해 "그 자리를 애그리게이트로 채운다"로 이어진다.

```text
JPA의 세 가지를 뺀다 (지연 로딩·캐싱·더티 트래킹) (§1)
        ↓
얻는 성질: "SQL은 리포지토리 메서드를 호출할 때, 오직 그때만 실행된다"
        ↓
뺀 자리를 무엇이 지탱하나? → 애그리게이트가 곧 저장 단위 (§2)
        ↓
   ├─ 도달 가능성 = 저장 범위     → 안은 객체, 밖은 id (§3)
   ├─ save() 하나로 통째 반영     → 기존 것은 delete 후 insert (§4)
   ├─ 상자로 안 담기는 쓰기       → @Modifying 조건부 UPDATE (§5)
   ├─ 목록·집계 조회             → JdbcClient로 직접 (§6)
   └─ 경쟁                       → @Version, 그 이상은 SQL (§7)
        ↓
그래서 무엇을 직접 써야 하는지 알고 고른다 (§8)
```

---

## 1. 출발점 — JPA의 세 가지를 의도적으로 뺀다

> 출처: 원고 §1

Schauder는 도입 글에서 목적을 한 문장으로 밝힌다: "Spring Data JDBC의 아이디어는 JPA의 복잡성에 굴복하지 않으면서 관계형 DB에 접근하는 것"이다([Introducing Spring Data JDBC](https://spring.io/blog/2018/09/17/introducing-spring-data-jdbc)).

뺀 것은 세 가지다.

```text
① 지연 로딩    — 예상치 못한 비싼 쿼리나 예외를 유발한다
② 캐싱         — 같은 엔티티의 여러 버전 비교를 어렵게 만든다
③ 더티 트래킹  — 영속 연산이 일어나는 "단일 지점"을 흐린다
```

세션과 엔티티 프록시라는 개념 자체도 없앴다.\
공식 레퍼런스의 "Why Spring Data JDBC?"는 같은 내용을 사용자 관점의 두 문장으로 요약한다.

> "엔티티를 로드하면 SQL이 실행된다. 그것이 끝나면 완전히 로드된 엔티티를 갖는다. 지연 로딩도 캐싱도 없다."\
> "엔티티를 저장하면 저장된다. 저장하지 않으면 저장되지 않는다. 더티 트래킹도 세션도 없다." ([Why Spring Data JDBC?](https://docs.spring.io/spring-data/relational/reference/jdbc/why.html))

**비용** — 편의를 잃는 대신 얻는 것은 "**SQL은 리포지토리 메서드를 호출할 때, 오직 그때만 실행된다**"는 성질이고([Introducing Spring Data JDBC](https://spring.io/blog/2018/09/17/introducing-spring-data-jdbc)), 그래서 코드를 읽는 것과 DB에 무슨 일이 일어나는지 아는 것이 같은 일이 된다.\
jpa.md에서 본 세 가지 청구서가 한꺼번에 사라지는 대신, §8의 비용이 생긴다.

---

## 2. 경계 — 애그리게이트가 곧 저장 단위다

> 출처: 원고 §2

기능을 뺀 자리를 무엇으로 지탱하는가가 이 도구의 본론이고, 답은 DDD의 **애그리게이트**다.

> **애그리게이트(aggregate)** — 하나의 단위로 저장·로드·삭제되는 도메인 객체들의 묶음.\
> 예: 주문(루트)과 그에 딸린 주문 항목들을 한 덩어리로 보고, 항상 통째로 읽고 통째로 저장한다.

Fowler의 정의는 "단일 단위로 다룰 수 있는 도메인 객체들의 묶음"이며, 핵심은 두 문장이다 — "애그리게이트는 데이터 저장 전송의 기본 단위다. 로드하거나 저장할 때 애그리게이트 전체를 요청한다"와 "트랜잭션은 애그리게이트 경계를 넘지 않아야 한다"([DDD_Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html)).\
Vaughn Vernon은 여기에 설계 규칙을 더한다 — 진짜 불변식을 일관성 경계 안에 모델링할 것, **애그리게이트를 작게 유지할 것**, 다른 애그리게이트는 식별자로 참조할 것, 애그리게이트 간 갱신은 최종 일관성으로 처리할 것([Effective Aggregate Design Part I](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf)).

Spring Data JDBC는 이 개념을 문서가 아니라 **런타임 규칙**으로 채택했다.\
레퍼런스는 "각 애그리게이트는 정확히 하나의 애그리게이트 루트를 가지며, 애그리게이트는 그 루트의 메서드를 통해서만 조작된다"고 못박고, 저장 측 규칙은 더 직접적이다 — "애그리게이트 루트로부터 도달 가능한 모든 엔티티는 그 애그리게이트 루트의 일부로 간주된다"([Domain-Driven Design and Relational Databases](https://docs.spring.io/spring-data/relational/reference/jdbc/domain-driven-design.html)).

그래서 이 도구에서 "무엇을 하나의 클래스 그래프로 묶을 것인가"는 매핑 취향이 아니라 **트랜잭션 설계**다.\
도달 가능성이 곧 저장 범위이므로, 애그리게이트를 크게 잡으면 매번 그만큼을 통째로 쓰게 되고, 작게 잡으면 그 경계 밖의 일관성은 다른 수단으로 지켜야 한다.\
리포지토리는 애그리게이트 루트마다 하나 둔다.

---

## 3. 참조는 두 종류 — 안쪽은 객체, 바깥쪽은 식별자

> 출처: 원고 §3

경계 규칙이 코드에 나타나는 형태는 **참조의 이분법**이다.

```text
애그리게이트 "주문"
+------------------------------------------+
|  Order (루트)                             |
|    lines: Set<OrderLine>  ← 객체 참조      |   같은 상자 안 → 함께 저장·삭제
|                                          |
|    cardId: Long          ── 식별자만 ──┐  |   다른 상자 → id로만 가리킴
+---------------------------------------|--+
                                        ▼
                              애그리게이트 "카드"(별도 상자, 안 건드림)
```

Schauder는 "애그리게이트 루트에서 비-transient 참조를 따라 도달할 수 있는 모든 것은 애그리게이트의 일부"라고 정의한 뒤 결론을 낸다 — "여러 애그리게이트가 같은 엔티티를 참조한다면 그 엔티티는 그것들을 참조하는 애그리게이트의 일부일 수 없다."\
따라서 "모든 Many-to-One과 Many-to-Many 관계는 id를 참조하는 것만으로 모델링되어야 한다"([Spring Data JDBC, References, and Aggregates](https://spring.io/blog/2018/09/24/spring-data-jdbc-references-and-aggregates)).

```kotlin
// 애그리게이트 루트 — 내부 엔티티는 객체로 들고 있다
data class Order(
    @Id val id: Long? = null,
    val status: String,
    val lines: Set<OrderLine> = emptySet(),   // order_line 테이블, Order와 함께 저장·삭제된다
    val cardId: Long,                          // 다른 애그리게이트 — 식별자만 (객체 참조 금지)
)

data class OrderLine(val sku: String, val quantity: Int)

interface OrderRepository : CrudRepository<Order, Long>
```

이 규칙의 결과는 **삭제 동작에서 가장 선명하다.** 애그리게이트를 지우면 도달 가능한 것들이 함께 지워지고, id로만 참조된 것은 남는다.\
애그리게이트 간 참조에 대해 레퍼런스가 붙이는 단서도 같은 맥락이다 — "애그리게이트를 가로지르는 참조는 항상 일관적임이 보장되지 않는다. 결국에는 일관되어짐이 보장될 뿐이다"([Domain-Driven Design and Relational Databases](https://docs.spring.io/spring-data/relational/reference/jdbc/domain-driven-design.html)).

> **결과적 일관성(eventual consistency)** — 지금 당장은 두 쪽 데이터가 달라도, 시간이 지나면 결국 같아지는 것.\
> 예: 주문 상자와 카드 상자를 각각 저장하면 그사이 잠깐은 어긋날 수 있어도, 후속 처리로 결국 맞춰진다.

---

## 4. 사용 모습 ① 저장 — save()가 전부이고, 그 안은 delete 후 insert다

> 출처: 원고 §4

**언제 쓰나** — 애그리게이트를 새로 만들거나 통째로 고쳐 저장할 때. `save()`를 부르면 애그리게이트 전체가 DB에 반영되고, 부르지 않으면 아무 일도 일어나지 않는다.

레퍼런스가 밝히는 내부 동작은 다음과 같다([Persisting Entities](https://docs.spring.io/spring-data/relational/reference/jdbc/entity-persistence.html)).

```text
새 애그리게이트 (id 비어 있음)          기존 애그리게이트 (id 있음)
  ① 루트 insert                          ① 참조된 엔티티 전부 delete
  ② 참조된 엔티티 전부 insert             ② 루트 update
                                         ③ 참조된 엔티티 전부 다시 insert
```

```kotlin
@Transactional
fun addLine(orderId: Long, line: OrderLine) {
    val order = orders.findById(orderId).orElseThrow()
    orders.save(order.copy(lines = order.lines + line))   // 이 호출에서만 SQL이 나간다
}
```

**비용** — 이 구현은 문서가 스스로 인정하는 낭비를 동반한다.\
"참조된 엔티티 중 실제로 바뀐 것이 몇 개뿐이라면 삭제 후 삽입은 낭비다. 개선될 수 있고 아마 개선되겠지만 한계가 있다 — Spring Data JDBC는 애그리게이트의 이전 상태를 알지 못한다"(같은 문서).\
이전 상태를 기억하지 않기로 한 결정(세션·캐시 없음)의 직접적인 대가이고, **애그리게이트를 작게 잡으라는 Vernon의 규칙이 여기서는 성능 규칙이 된다.**

새 것인지 기존 것인지의 판정은 `@Id` 속성으로 한다. 식별자가 비어 있으면 새 애그리게이트로 보므로, Kotlin에서는 위 예시처럼 `val id: Long? = null`을 두는 형태가 기본이다.\
레퍼런스는 제약 하나를 덧붙인다 — "엔티티를 저장한 뒤에는 그 엔티티가 더 이상 새 것이어서는 안 된다".

---

## 5. 사용 모습 ② 조건부 상태 전이 — 쿼리를 직접 쓴다

> 출처: 원고 §5

**언제 쓰나** — "점유자가 없을 때만 내 것으로 바꾼다", "이미 처리했으면 다시 처리하지 않는다" 같은 **조건부 전이**. 애그리게이트 통째 저장으로는 표현되지 않는 쓰기다.

이런 쓰기는 읽고-판단하고-저장하는 사이에 경쟁이 끼어들 수 있어, **단일 UPDATE 문의 WHERE 절**로 표현해야 원자성이 성립한다.

> **조건부 UPDATE(원자적 상태 전이)** — 조건을 코드가 아니라 UPDATE의 WHERE 절에 넣고, 영향 행 수(0이냐 1이냐)로 성패를 판정하는 것.\
> 예: `UPDATE ... WHERE owner IS NULL` 이 1행을 바꿨으면 내가 점유에 성공한 것, 0행이면 남이 먼저 잡은 것 — 읽기·판단·쓰기가 한 문장에서 원자적으로 끝난다.

Spring Data JDBC에서는 `@Query`에 `@Modifying`을 붙여 쓰고, 반환 타입은 `void`·`int`(영향 행 수)·`boolean`(갱신 여부) 중 고른다([Query Methods](https://docs.spring.io/spring-data/relational/reference/jdbc/query-methods.html)).

```kotlin
// 일반화한 예 — "잡 리스" 획득: 점유자가 없거나 리스가 만료됐을 때만 내가 잡는다
interface JobLeaseRepository : CrudRepository<JobLeaseRow, Long> {

    @Modifying
    @Query("""
        UPDATE job_lease SET owner = :owner, leased_until = :until
        WHERE id = :id AND (owner IS NULL OR leased_until < :now)
    """)
    fun acquireLease(id: Long, owner: String, until: Instant, now: Instant): Boolean
}
```

메서드 이름으로 쿼리를 파생하는 기능도 있지만 범위가 좁다 — 애그리게이트 루트에 직접 있는 단순 속성에 한정되고, 조인이 필요한 조회나 update·delete는 파생되지 않는다(같은 문서).\
즉 이 도구에서 이름 기반 파생은 편의 기능이고, **쓰기의 본체는 사람이 쓴 SQL이 맡는다.** 조건부 UPDATE가 코드에 그대로 보이는 것이, 쓰기가 상태 전이인 도메인에서는 오히려 요구사항이다.

**비용** — `@Modifying` 쿼리에는 단서가 하나 붙는다. 엔티티 콜백과 생명주기 이벤트를 건너뛰므로 감사(auditing) 애노테이션이 자동 갱신되지 않는다(같은 문서) — 명시 쿼리로 내려간 경로에서는 그런 부가 기능도 함께 내려놓는다고 이해하면 된다.

---

## 6. 사용 모습 ③ 조회 — 애그리게이트를 재구성하지 않는다

> 출처: 원고 §6

**언제 쓰나** — 목록·집계·커서 조회. 애그리게이트를 통째로 읽어 화면 모양으로 접는 방식과 맞지 않는다.

필요한 것은 여러 테이블에서 몇 개 컬럼만 뽑은 **평평한 행**이지 도메인 객체가 아니기 때문이다.\
Spring Data JDBC는 이 층을 자기가 대신 해 주려 하지 않으므로, 조회는 `JdbcClient`(Spring Framework 6.1부터의 통합 클라이언트)나 `JdbcTemplate`으로 직접 쓴다([Spring Framework — JDBC core](https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html)).

```kotlin
data class OrderSummary(val id: Long, val status: String, val lineCount: Int)

fun page(afterId: Long, size: Int): List<OrderSummary> =
    jdbcClient.sql("""
        SELECT o.id, o.status, count(l.order) AS line_count
        FROM "order" o LEFT JOIN order_line l ON l.order = o.id
        WHERE o.id > :afterId GROUP BY o.id, o.status ORDER BY o.id LIMIT :size
    """)
        .param("afterId", afterId).param("size", size)
        .query(OrderSummary::class.java).list()
```

이 분리는 JPA 진영에서도 최종적으로 권장되는 형태와 같다 — 앞 문서에서 본 DTO 프로젝션이 그것이다.\
**차이는 시점이다.** JPA에서는 성능 문제가 드러난 뒤 엔티티 조회에서 프로젝션으로 내려가지만, 여기서는 조회가 처음부터 별도 층이다.

```text
JPA:              엔티티 조회로 시작  →  (성능 문제)  →  DTO 프로젝션으로 내려감
Spring Data JDBC: 처음부터 조회 전용 층 (JdbcClient)   ← "내려간다"가 아니라 시작점
```

---

## 7. 동시성 — 낙관적 잠금은 있고, 그 이상은 SQL로 쓴다

> 출처: 원고 §7

애그리게이트 단위 저장에도 경쟁은 있다. 읽어서 고친 뒤 저장하는 사이에 다른 트랜잭션이 같은 애그리게이트를 바꿨다면 마지막 쓰기가 앞의 변경을 덮는다.

Spring Data JDBC는 숫자형 `@Version` 속성으로 이를 막는다.

> **낙관적 잠금(optimistic locking)** — "그사이 아무도 안 바꿨겠지"를 전제로 진행하되, 저장할 때 버전이 그대로인지 검사해 어긋나면 실패시키는 방식.\
> 예: 버전 3으로 읽어 고친 뒤 저장할 때 DB 버전이 여전히 3이어야 성공하고, 4가 됐으면 남이 먼저 바꾼 것이라 예외가 난다.

"애그리게이트 루트에 대한 update 문은 DB에 저장된 버전이 실제로 변하지 않았음을 검사하는 where 절을 포함하고", 그렇지 않으면 `OptimisticLockingFailureException`이 발생하며, 버전 값은 엔티티와 DB 양쪽에서 증가한다([Persisting Entities](https://docs.spring.io/spring-data/relational/reference/jdbc/entity-persistence.html)).

비관적 잠금(`SELECT ... FOR UPDATE`)이나 fencing token 검사처럼 조건이 더 구체적인 통제는 프레임워크 기능이 아니라 명시 쿼리로 쓴다.

> **비관적 잠금(pessimistic locking)** — "충돌이 날 것"을 전제로, 읽을 때부터 행에 잠금을 걸어(`SELECT ... FOR UPDATE`) 남이 못 건드리게 하는 방식.\
> 예: 재고 행을 `FOR UPDATE`로 읽으면, 내 트랜잭션이 끝날 때까지 다른 트랜잭션은 그 행 앞에서 기다린다.

이것이 이 도구의 일관된 태도다 — **동시성 통제를 프레임워크가 추상화하지 않고 SQL 표면에 남겨 둔다.**\
통제 수단이 적은 것이 아니라, 통제가 코드에 드러나 있어야 리뷰와 실험(잠금 실험 같은)이 가능하다는 쪽에 선 것이다.

---

## 8. 한계 — 무엇을 직접 써야 하는지 알고 고른다

> 출처: 원고 §8

- **첫째, 깊은 객체 그래프의 자동 영속이 필요하면 이 도구는 맞지 않는다.**\
  애그리게이트가 커질수록 매번 delete 후 insert하는 비용과 매핑 코드가 함께 늘고, 그 지점이 바로 JPA가 값을 내기 시작하는 지점이다. 그래서 그런 상황을 "JPA 도입 조건"으로 미리 잠가 두는 팀이 많다.
- **둘째, 매핑 커스터마이징 여지가 작다.**\
  레퍼런스가 직접 말한다 — "엔티티를 테이블에 매핑하는 단순한 모델이 있다. 아마 꽤 단순한 경우에만 통할 것이다. 마음에 들지 않으면 자신의 전략을 코딩해야 한다. Spring Data JDBC는 애노테이션으로 전략을 커스터마이징하는 지원을 아주 제한적으로만 제공한다"([Why Spring Data JDBC?](https://docs.spring.io/spring-data/relational/reference/jdbc/why.html)).
- **셋째, 조회 모델과 그 매핑 코드는 전부 직접 쓴다**(§6).
- **넷째, 애그리게이트 간 참조를 id로만 두므로 여러 애그리게이트를 걸친 일관성은 도구가 아니라 설계로 지켜야 한다** — 트랜잭션 경계를 어디에 그을지, 어디를 최종 일관성으로 둘지를 사람이 정해야 한다.

`[실무 의견]` 자료·튜토리얼·스택오버플로 축적량이 JPA에 비해 훨씬 적어서, 낯선 문제를 만났을 때 검색으로 해결되는 비율이 낮다는 점도 실제로는 비용이다.

---

## 9. 정리 — 규칙이 적고, 그 규칙이 도메인 개념과 같다

> 출처: 원고 §9

Spring Data JDBC를 한 문장으로 줄이면 "애그리게이트 경계를 저장 경계로 삼고, 그 밖의 모든 것은 명시 SQL로 남긴 도구"다.\
배울 개념은 세 개뿐이다 — 애그리게이트 루트, `save()`가 하는 일, 그리고 나머지는 직접 쓴다는 것.\
감춰진 동작이 없으므로 코드를 읽으면 SQL이 보이고, 그 대신 편의는 없다.

이 성질이 어떤 도메인에서 유리하고 어떤 도메인에서 불리한지는 [`comparison.md`](./comparison.md)에서 축별로 비교한다.\
JPA 쪽 개념이 아직 흐리면 [`jpa.md`](./jpa.md)를 먼저 읽는 편이 낫다 — 이 도구의 설계는 그쪽 개념을 알아야 "왜 뺐는가"가 읽힌다.

---

## 핵심 문장

- **이 도구는 "JPA에서 뺀 것"이 아니라 "뺀 것 자체가 목적"이다 — 지연 로딩·캐싱·더티 트래킹을 없애 "SQL은 리포지토리 호출 시점에만 실행된다"를 얻는다.**
- **애그리게이트가 곧 저장 단위다 — "무엇을 한 그래프로 묶나"는 매핑 취향이 아니라 트랜잭션 설계다.**
- **참조는 둘로 갈린다: 애그리게이트 안쪽은 객체, 바깥쪽은 식별자만.**
- **기존 애그리게이트 저장은 delete 후 insert다 — 그래서 "애그리게이트를 작게"가 여기서는 성능 규칙이 된다.**
- **조건부 전이·목록 조회·비관적 잠금은 프레임워크가 감추지 않고 SQL 표면에 남긴다 — 그래야 리뷰·실험이 된다.**

---

## 관련 자료

- 반대편 도구: [`./jpa.md`](./jpa.md) — 이 도구가 "왜 뺐는가"를 알려면 먼저 읽는 편이 낫다.
- 축별 비교와 선택 기준: [`./comparison.md`](./comparison.md)
- 설계 철학 원문: [Introducing Spring Data JDBC](https://spring.io/blog/2018/09/17/introducing-spring-data-jdbc) · [Why Spring Data JDBC?](https://docs.spring.io/spring-data/relational/reference/jdbc/why.html) · [References and Aggregates](https://spring.io/blog/2018/09/24/spring-data-jdbc-references-and-aggregates) (Jens Schauder)
- 애그리게이트 개념 원문: [DDD_Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html) (Fowler) · [Effective Aggregate Design Part I](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf) (Vernon)
- 공식 레퍼런스: [Domain-Driven Design and Relational Databases](https://docs.spring.io/spring-data/relational/reference/jdbc/domain-driven-design.html) · [Persisting Entities](https://docs.spring.io/spring-data/relational/reference/jdbc/entity-persistence.html) · [Query Methods](https://docs.spring.io/spring-data/relational/reference/jdbc/query-methods.html) · [Spring Framework JDBC core](https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html)

---

## 용어 풀이

- **애그리게이트(Aggregate)** — 하나의 단위로 저장·로드·삭제되는 도메인 객체 묶음. 이 도구에서는 곧 저장 단위다.
- **애그리게이트 루트(Aggregate Root)** — 애그리게이트의 유일한 진입점. 애그리게이트는 루트의 메서드로만 조작된다. 리포지토리는 루트마다 하나.
- **도달 가능성 = 저장 범위** — 루트에서 (비-transient) 참조로 닿는 모든 엔티티가 저장·삭제에 함께 딸려간다.
- **참조의 이분법** — 애그리게이트 안쪽 엔티티는 객체로, 바깥 애그리게이트는 식별자(id)로만 참조한다.
- **save()의 delete-후-insert** — 기존 애그리게이트 저장 시 참조 엔티티를 전부 지우고 다시 넣는 것. 이전 상태를 모르기 때문이다.
- **@Modifying + @Query** — 조건부 UPDATE/DELETE를 명시 SQL로 쓰는 방법. 반환은 void·int(영향 행 수)·boolean.
- **조건부 UPDATE(원자적 상태 전이)** — 조건을 WHERE 절에 넣고 영향 행 수로 성패를 판정하는 쓰기. 읽기·판단·쓰기가 한 문장에서 원자적.
- **JdbcClient / JdbcTemplate** — 조회 전용 층을 직접 쓰는 클라이언트. 애그리게이트를 재구성하지 않는다.
- **낙관적 잠금(Optimistic Locking)** — 저장 시 `@Version`이 그대로인지 검사해 어긋나면 실패시키는 방식.
- **비관적 잠금(Pessimistic Locking)** — 읽을 때부터 행에 잠금을 걸어(`SELECT ... FOR UPDATE`) 경쟁을 막는 방식.
- **결과적 일관성(Eventual Consistency)** — 지금은 달라도 시간이 지나면 결국 같아지는 상태. 애그리게이트 간 참조가 이렇다.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **"JPA를 뺀 게 아니라 JDBC에 애그리게이트를 더한 것"으로 읽는 게 정확하다.** 이름 때문에 `JdbcTemplate`의 상위 호환처럼 보이지만, 핵심은 저수준 JDBC가 아니라 DDD 애그리게이트를 저장 규칙으로 삼은 지점이다. 그래서 "가벼운 JPA"가 아니라 "규칙이 다른 도구"다.
- **Spring Data JDBC vs Spring Data R2DBC.** 둘 다 같은 애그리게이트 철학을 공유하지만, JDBC는 블로킹, R2DBC는 리액티브(논블로킹)다. 개념 골격이 같아 이 문서의 애그리게이트·참조·save() 이해가 R2DBC에도 대부분 옮겨간다.
- **delete-후-insert가 실무에서 무는 함정 하나.** 자식 행에 다른 테이블이 FK로 매달려 있거나, 자식 행 자체에 감사 컬럼(생성시각 등)이 있으면, 매 저장마다 지웠다 다시 넣는 통에 그 값이 리셋되거나 FK가 깨질 수 있다. 그래서 "애그리게이트를 작게"가 성능뿐 아니라 안전 규칙이기도 하다.
- **왜 조회를 처음부터 나누는 게 이득인가(CQRS의 축소판).** 쓰기 모델(애그리게이트)과 읽기 모델(평평한 DTO)을 분리하면, 화면이 늘어도 애그리게이트를 오염시키지 않고 읽기 쿼리만 추가하면 된다. 명령과 조회 모델을 나누는 CQRS의 가벼운 형태이고, 이 도구는 그 분리를 사실상 강제한다.
