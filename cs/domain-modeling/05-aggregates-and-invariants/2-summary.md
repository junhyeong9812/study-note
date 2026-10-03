# domain-modeling/05-aggregates-and-invariants — 애그리거트: 일관성 경계·불변식·Vernon 4규칙 — 정리 (힌트)

## 해결하는 문제

객체 여러 개에 걸친 규칙을 동시 요청 속에서 지키려면, **무엇을 한 덩어리로 잠그고 함께 커밋할지** 정해야 한다.

```text
  규칙: "스프린트에 넣은 항목 포인트 합 ≤ 용량 10"

  요청 A: 합 6 읽음 → 6+3=9 OK → 항목 7 추가 ┐
  요청 B: 합 6 읽음 → 6+3=9 OK → 항목 8 추가 ┘ 둘 다 커밋 → 합 12  ← 규칙 깨짐

  덩어리를 너무 크게 잡으면?
  Product 하나에 백로그 항목 수백 개 → 서로 다른 항목을 고쳐도 같은 버전을 다툼 → 충돌·재시도 폭증
```

- 덩어리가 작으면 여러 객체에 걸친 규칙이 동시성에 깨진다.
- 덩어리가 크면 상관없는 수정끼리 서로 막는다.
- *애그리거트(aggregate)*: 엔티티와 값 객체를 묶은 일관성 경계. 바깥은 루트를 통해서만 안을 바꾸고, 경계 안의 불변식은 한 트랜잭션 안에서 지킨다.
  - *불변식(invariant)*: 언제나 성립해야 하는 업무 규칙. Vernon(2011)은 "항상 일관돼야 하는 업무 규칙"이라고 정의하고, 여기서 말하는 일관성은 즉시·원자적인 **트랜잭션 일관성**이라고 적는다.

쉬운 예: 은행 공동 계좌의 통장.
- 통장 하나에 입출금 줄이 쌓인다. "잔액 ≥ 0"은 통장 단위 규칙이다. 창구 두 곳이 동시에 출금하면 통장을 한 번에 한 창구만 처리해야 한다.
- 그렇다고 은행 전체를 한 덩어리로 잠그면 다른 손님의 통장끼리도 서로 기다린다.

똑같은 구조다.\
실무 예: 주문(주문 줄 합계 ≤ 한도), 재고 예약(남은 수량 ≥ 0), 좌석 예매(한 좌석 한 예약), 스프린트 계획(용량 제한).

## 동작·원리

### 1. 애그리거트의 모양 — 루트, 경계, 바깥 참조

```text
        ┌──────────────── Sprint 애그리거트 (경계) ─────────────────┐
        │  Sprint (루트, id, version, capacity=10)                   │
        │    ├─ CommittedItem(itemId=7, points=3)   ← 내부 엔티티/값  │
        │    └─ CommittedItem(itemId=9, points=3)                    │
        │  불변식: Σ points ≤ capacity   ← 루트가 검사한다            │
        └──────────────────────────────────────────────────────────┘
               ▲  바깥은 루트만 참조한다
               │
   BacklogItem#7 ──(sprintId 로 참조)──>  Sprint#1      다른 애그리거트는 객체가 아니라 ID로
```

- Evans 『DDD Reference』(2015) Aggregates 항목
  - 엔티티와 값 객체를 애그리거트로 묶고 각각 경계를 정한다.
  - 엔티티 하나를 **루트**로 고른다. 바깥 객체는 루트만 참조한다(내부 객체 참조는 한 연산 안에서만 쓰도록 넘긴다).
  - 애그리거트 전체의 속성과 불변식을 정의하고, 지키는 책임은 루트(또는 지정한 프레임워크 장치)에 준다.
  - **같은 경계로 트랜잭션과 분산을 다스린다.** 경계 안에서는 일관성 규칙을 동기적으로, 경계 사이는 비동기로 갱신한다.
- *루트(aggregate root)*: 애그리거트의 유일한 출입구 엔티티. 전역 식별자를 가진다.
- Spring Data 문서(Spring Data JDBC "Domain Driven Design and Relational Databases")도 같은 정의를 쓴다: 애그리거트는 원자적 변경 사이에 일관성이 보장되는 엔티티 묶음이고, 루트의 메서드로만 조작하며, 리포지토리는 루트마다 하나 둔다.

### 2. Vernon "Effective Aggregate Design"(2011)의 4규칙

```text
  규칙                                     한 줄 요지
  1 Model True Invariants In Consistency    정말 즉시 일관돼야 하는 규칙만 경계 안에
    Boundaries
  2 Design Small Aggregates                 루트 + 값 객체 몇 개가 기본. 크면 충돌·메모리·확장성 손해
  3 Reference Other Aggregates By Identity  다른 애그리거트는 객체 참조 대신 ID로
  4 Use Eventual Consistency Outside the    경계 밖 규칙은 이벤트 등으로 나중에 맞춘다
    Boundary                                ("누구의 일인가?"를 먼저 묻는다)
```

- 1부: 처음 설계는 `Product`가 백로그 항목·릴리스·스프린트를 모두 품은 거대 애그리거트였다. Bill이 항목을 추가해 `Product` 버전이 2가 되자, 동시에 릴리스를 만든 Joe의 커밋이 버전 1 기준이라 실패했다(Vernon 1부의 시나리오).
- 1부: "잘 설계된 애그리거트는 업무가 요구하는 어떤 수정에도 한 트랜잭션 안에서 불변식을 완전히 지킬 수 있다. 그리고 잘 설계된 바운디드 컨텍스트는 모든 경우에 트랜잭션당 애그리거트 인스턴스 하나만 수정한다."
- 1부: Niclas Hedhman의 금융 파생상품 프로젝트에서 애그리거트의 약 70%가 루트 엔티티 + 값 속성만으로, 나머지 30%가 엔티티 2~3개로 설계됐다는 보고를 인용한다. Vernon 스스로 모든 모델이 70/30이라는 뜻은 아니라고 덧붙인다.
- 2부 "Reasons To Break the Rules": 한 트랜잭션에서 여러 애그리거트를 고쳐도 되는 이유 네 가지 — 사용자 인터페이스 편의(일괄 생성), 기술 장치 부족(메시징·타이머 없음), 전역(2PC) 트랜잭션 정책, 조회 성능(ID 대신 직접 참조). 사용자–애그리거트 친화성(한 사람만 그 인스턴스들을 다룸)이 있으면 그 결정이 더 건전하다고 적는다.
- **저자마다 강조가 다르다.**
  - Evans(『DDD Reference』 2015 Aggregates 항목): 경계를 불변식과 트랜잭션·분산 단위로 정하라고 하고, 크기 수치는 제시하지 않는다. 경계가 잘 안 맞으면 모델을 다시 보라고 한다. 2003년 책 본문은 열지 못해, 책 안에 크기 권고가 있는지는 확인하지 않았다 [?].
  - Vernon(2011): "작게"를 규칙으로 올리고, 트랜잭션당 애그리거트 하나를 기본으로 둔다. 단 위 네 가지 예외를 인정한다.

### 3. 낙관적 잠금과 애그리거트 크기

```text
  버전 단위 = 애그리거트 루트
  읽기:  SELECT version FROM <root> WHERE id=?            → v
  쓰기:  UPDATE <root> SET version=v+1 WHERE id=? AND version=v
         1행이면 성공, 0행이면 그 사이 누군가 고침 → 충돌(재시도 또는 사용자에게 알림)

  거대 애그리거트(Product가 버전 단위)          작은 애그리거트(BacklogItem이 버전 단위)
  사용자1: 항목1 수정 ─┐                       사용자1: 항목1 v → 다툼 없음
  사용자2: 항목2 수정 ─┼─ 모두 Product#1 버전   사용자2: 항목2 v → 다툼 없음
  사용자8: 항목8 수정 ─┘  하나를 다툼           …
```

- 낙관적 잠금 자체는 [database/17](../../database/17-occ-and-timestamp-ordering/2-summary.md)·[database/52](../../database/52-offline-concurrency-patterns/2-summary.md)(Coarse-Grained Lock = 애그리거트 단위 버전)에서 다룬다.
- 버전의 단위가 곧 "함께 다투는 범위"다. 애그리거트를 키우면 그 범위가 커진다.

### 실험 A: 애그리거트 크기와 충돌 수 (PostgreSQL 17)

```java
// 8명이 각자 다른 백로그 항목을 50번씩 수정. 버전 충돌이면 다시 읽고 재시도.
String vt = large ? "product" : "backlog_item";   // 버전을 어디에 두나
int vid   = large ? 1 : item;
v = SELECT version FROM vt WHERE id = vid;  commit;  Thread.sleep(1);   // 읽고 1ms 작업(예시)
upd = UPDATE vt SET version = version + 1 WHERE id = vid AND version = v;
if (upd == 1) { UPDATE backlog_item SET title = ? WHERE id = item; commit; } else { rollback; conflicts++; }
```

(실험, PostgreSQL 17.11 일회용 컨테이너 + JDK 21.0.12 eclipse-temurin, pgJDBC 42.7.4, 둘 다 `--cpus=2`, READ COMMITTED(PG 기본), 2026-10-03)

```text
== A. 애그리거트 크기와 낙관적 잠금 충돌 (8명 × 50회, 각자 다른 항목)
large  성공 커밋=400, 버전 충돌(재시도)=2242, 소요=4671ms
small  성공 커밋=400, 버전 충돌(재시도)=0, 소요=828ms
large  성공 커밋=400, 버전 충돌(재시도)=2053, 소요=3368ms
small  성공 커밋=400, 버전 충돌(재시도)=0, 소요=497ms
large  성공 커밋=400, 버전 충돌(재시도)=1976, 소요=3227ms
small  성공 커밋=400, 버전 충돌(재시도)=0, 소요=435ms
```

- 관찰
  - 사용자들은 서로 다른 항목을 고쳤다. 업무상 다툴 이유가 없다.
  - 거대 애그리거트에서는 400번 커밋하는 동안 충돌이 1938~2313번 났다(집필 2회 실행 + 사실 점검 2회 실행, 각 3측정 = 12측정, 실행마다 다르다). 작은 애그리거트는 12측정 모두 0번.
  - 소요 시간은 거대 쪽이 2426~9781ms, 작은 쪽이 384~987ms였다(같은 12측정, 제한 환경 값). 매 측정에서 거대 쪽이 더 오래 걸렸다.
- 해석: 충돌 수는 사용자 수·작업 시간에 따라 달라진다. 그러나 "서로 상관없는 수정이 같은 버전을 다툰다"는 구조는 크기와 무관하게 남는다. Vernon 1부의 Bill·Joe 시나리오가 이것이다.

### 실험 B: 경계 밖 불변식은 동시성에 깨진다

```java
// 8명이 동시에 3점 항목을 스프린트 1(capacity 10)에 넣는다. 첫 시도는 8명이 모두 읽은 뒤 쓰게 강제(최악 인터리빙).
cap, sv = SELECT capacity, version FROM sprint WHERE id = 1;
sum     = SELECT coalesce(sum(points),0) FROM sprint_commit WHERE sprint_id = 1;
if (sum + 3 > cap) { reject; return; }
if (inside) {   // 불변식이 경계 안: 루트 Sprint의 버전을 올리며 기록
    if (UPDATE sprint SET version = version + 1 WHERE id = 1 AND version = sv) == 0 → rollback, 다시 읽기
}
INSERT INTO sprint_commit VALUES (1, item, 3);  commit;
// outside: 앱 서비스가 합을 읽어 검사만 하고 INSERT (루트 버전을 쓰지 않음)
```

(실험, 같은 환경)

```text
== B. 경계 밖 불변식 (8명이 동시에 3점 항목을 스프린트에 커밋)
outside 커밋 성공=8, 용량 초과로 거절=0, 버전 충돌 재시도=0 → 스프린트 포인트 합=24 (capacity 10)
inside  커밋 성공=3, 용량 초과로 거절=5, 버전 충돌 재시도=18 → 스프린트 포인트 합=9 (capacity 10)
outside 커밋 성공=8, 용량 초과로 거절=0, 버전 충돌 재시도=0 → 스프린트 포인트 합=24 (capacity 10)
inside  커밋 성공=3, 용량 초과로 거절=5, 버전 충돌 재시도=17 → 스프린트 포인트 합=9 (capacity 10)
outside 커밋 성공=8, 용량 초과로 거절=0, 버전 충돌 재시도=0 → 스프린트 포인트 합=24 (capacity 10)
inside  커밋 성공=3, 용량 초과로 거절=5, 버전 충돌 재시도=18 → 스프린트 포인트 합=9 (capacity 10)
```

- 관찰
  - outside: 8명 모두 "합 0"을 읽고 통과했다. 합 24 — 용량의 2.4배. 예외는 하나도 없다.
  - inside: 루트 버전을 먼저 올린 3명만 성공하고 나머지는 다시 읽어 용량 초과로 거절됐다. 합 9. 재시도 수는 실행마다 14~18(집필·점검 12측정). 합 24·9는 12측정 모두 같았다.
- 해석: 불변식이 걸친 범위(스프린트 전체)와 잠금 범위(행 하나, 또는 없음)가 다르면, 검사 코드가 있어도 동시성에 뚫린다. 규칙 1 "진짜 불변식은 경계 안에"가 이것이다. PostgreSQL 기본 격리 수준(READ COMMITTED)은 이 쓰기 왜곡을 막지 않는다 — [database/14](../../database/14-isolation-levels-and-anomalies/2-summary.md).

### 4. 경계 밖은 결과적 일관성

```text
  한 트랜잭션                          다음 트랜잭션(들)
  BacklogItem#7.commitTo(sprint 1) ──> 이벤트 BacklogItemCommitted ──> Sprint#1에 반영
  (BacklogItem 하나만 수정)              (outbox·메시지)                  (Sprint 하나만 수정)
```

- 규칙 4의 질문: "이 규칙을 지키는 것이 이 요청을 한 사용자의 일인가?" 그렇다면 같은 트랜잭션, 아니라면 결과적 일관성이 후보다(Vernon 2부·3부).
- 결과적 일관성을 쓰면 **잠깐 어긋난 상태가 보인다.** 업무가 그 어긋남을 견딜 수 있을 때만 쓴다. "스프린트 용량"처럼 넘으면 안 되는 규칙이면 경계 안(실험 B의 inside)에 둔다.
- 이벤트 발행·outbox는 [09-domain-events](../09-domain-events/2-summary.md)·[distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **트리(루트 경유 접근)**: 애그리거트는 루트에서 내려가는 트리다. 바깥에서 내부 노드로 들어오는 간선이 없다. 다른 애그리거트로 가는 간선은 객체 포인터가 아니라 ID(키)다.
- **버전 번호 + 비교 후 갱신(compare-and-set)**: `UPDATE … WHERE version = ?`의 갱신 행 수로 충돌을 판정한다. 메모리의 CAS 루프와 같은 모양이다 — [database/17](../../database/17-occ-and-timestamp-ordering/2-summary.md).
- **재시도 루프**: 충돌하면 다시 읽고 다시 판단한다. 판단에 쓴 값이 바뀌었으니 같은 쓰기를 그대로 반복하면 안 된다(실험 B: 다시 읽은 뒤 5명이 거절됨).
- **이벤트 큐·outbox**: 경계 밖 갱신을 다음 트랜잭션으로 넘긴다.

## 적용 — 풀어나가는 법

### 1. 경계를 정하는 순서

```text
  1) 규칙을 문장으로 적는다: "스프린트 포인트 합 ≤ 용량"
  2) 각 규칙이 즉시 성립해야 하나, 잠깐 어긋나도 되나?      → 즉시면 진짜 불변식
  3) 진짜 불변식이 걸친 객체들 = 애그리거트 후보            → 그 밖은 ID 참조
  4) 동시에 고칠 사용자·작업을 그려 본다                    → 상관없는 수정이 같은 루트를 다투면 쪼갠다
  5) 한 유스케이스가 애그리거트 두 개를 고치나?             → 이벤트로 나누거나, 예외 사유(Vernon 4가지)를 기록
```

### 2. 코드 (Java 21 + JPA)

```java
@Entity
public class Sprint {                                   // 루트
    @Id private Long id;
    @Version private long version;                      // 애그리거트 단위 버전
    private int capacity;
    @ElementCollection                                  // 내부 값: 루트의 값 필드
    private Set<CommittedItem> items = new HashSet<>();

    public void commit(BacklogItemId itemId, int points) {   // 불변식은 루트가 검사
        int sum = items.stream().mapToInt(CommittedItem::points).sum();
        if (sum + points > capacity) throw new CapacityExceeded(id, sum, points, capacity);
        items.add(new CommittedItem(itemId.value(), points));
    }
}
@Embeddable public record CommittedItem(long itemId, int points) {}

@Entity
public class BacklogItem {                              // 별도 애그리거트
    @Id private Long id;
    @Version private long version;
    private Long sprintId;                              // 다른 애그리거트는 ID로 참조
}
```

- 애플리케이션 서비스는 루트를 하나 꺼내 메서드를 부르고 저장한다. 스프린트 쪽 반영은 `BacklogItem` 쪽 이벤트로 다음 트랜잭션에서 한다(또는 반대 방향).
- **JPA 버전 검사 범위**: Jakarta Persistence 3.1 §3.4.2 — 버전 검사에는 그 엔티티의 비관계 필드와 **그 엔티티가 소유한 관계**만 들어간다. 소유한 관계라도 들어가는 것은 연관 자체(어떤 자식을 가리키는가)이지 자식 엔티티의 필드가 아니다. `@ElementCollection`의 원소는 루트의 비관계 필드(값)라서 원소를 추가하면 루트 버전이 오른다(Hibernate 6.6.29에서 `version 0 → 1` 확인, 실험 C-2). 반면 자식 엔티티의 필드만 바꾸면 루트 버전이 오르지 않는다. `@OneToMany(mappedBy=…)`(실험 C)든, 루트가 소유한 단방향 `@OneToMany @JoinColumn`(실험 C-3)이든 같다.

### 실험 C: Hibernate 6.6에서 자식만 고치면 루트 버전은 그대로

```java
@Entity class Product { @Id Long id; @Version int version;
    @OneToMany(mappedBy = "product", cascade = ALL) List<Item> items; }
@Entity class Item { @Id Long id; String title; @ManyToOne Product product; }

// 1) 두 EntityManager가 같은 Product를 읽고 각자 다른 Item을 고친 뒤 루트를 OPTIMISTIC_FORCE_INCREMENT로 잠금
// 2) 강제 증가 없이 자식만 수정 → 루트 version 확인
```

(실험, Hibernate ORM 6.6.29.Final 네이티브 부트스트랩 + PostgreSQL 17.11, 같은 환경, 1회 — 로그 줄은 뺐다)

```text
세션1 커밋 OK, 루트 version → 1
세션2 → org.hibernate.StaleObjectStateException: Row was updated or deleted by another transaction (or unsaved-value mapping was incorrect): [Hib05$Product#1]
자식만 수정 후 루트 version = 1
```

- `OPTIMISTIC_FORCE_INCREMENT`로 루트를 잠그면 서로 다른 자식을 고친 두 번째 세션이 실패한다. 강제 증가 없이 자식만 고치면 루트 버전이 1 그대로다.
- C-2(같은 환경, `Hib05b.java`): 위 `Sprint`처럼 `@ElementCollection Set<CommittedItem>`에 원소 하나를 추가하고 커밋했다.

```text
생성 직후 version = 0
@ElementCollection에 원소 추가 후 version = 1
```

- C-3(Hibernate 6.6.29 + H2 2.3.232 메모리 DB, JDK 21, `Adj.java`): 루트가 소유한 단방향 `@OneToMany(cascade = ALL) @JoinColumn(name = "ord_id")`로 바꿔, 기존 자식의 `qty`만 고친 뒤와 자식을 하나 추가한 뒤의 루트 버전을 봤다.

```text
생성 직후 version = 0
소유 단방향 @OneToMany 자식 필드 수정 후 version = 0
소유 단방향 @OneToMany 자식 추가 후 version = 1
```

- 소유 관계로 바꿔도 자식 필드 수정은 루트 버전을 올리지 않는다. 컬렉션에 원소를 넣거나 빼서 연관이 바뀔 때만 오른다. 그래서 대처는 매핑 변경이 아니라 루트 버전 강제 증가다.

- 예외 이름은 부트스트랩 방식에 따라 다르다. 네이티브 부트스트랩에서는 `org.hibernate.StaleObjectStateException`(또는 `LockModeType.OPTIMISTIC` 검증 실패 시 Hibernate 클래스 `org.hibernate.dialect.lock.OptimisticEntityLockException`)이 난다. JPA 부트스트랩에서는 Hibernate 6.6.29 `ExceptionConverterImpl`이 둘 다 `jakarta.persistence.OptimisticLockException`으로 감싼다(jar 바이트코드 `javap`로 확인, 실행은 안 함). JPA 명세가 API 쪽 예외로 정한 것도 이것이다(3.1 §3.4.2·§3.4.5). 가이드의 "Jakarta Persistence `OptimisticEntityLockException`"이라는 표현은 패키지를 잘못 적은 것으로 보인다(해석). 이 실험은 네이티브 방식이라 `StaleObjectStateException`이 나왔다.

### 3. 진단

```sql
-- PostgreSQL 17: 같은 루트 행에 갱신이 몰리는가 (pg_stat_statements가 켜져 있을 때)
SELECT calls, rows, query FROM pg_stat_statements
 WHERE query ILIKE 'update % set version%' ORDER BY calls DESC LIMIT 10;

-- 루트별 자식 수 분포: 수백~수천 개면 거대 애그리거트 후보
SELECT product_id, count(*) FROM backlog_item GROUP BY product_id ORDER BY 2 DESC LIMIT 10;

-- 불변식 위반 데이터 찾기 (실험 B의 규칙)
SELECT s.id, s.capacity, sum(c.points) FROM sprint s JOIN sprint_commit c ON c.sprint_id = s.id
 GROUP BY s.id, s.capacity HAVING sum(c.points) > s.capacity;
```

- Hibernate 6.6 `Statistics.getOptimisticFailureCount()`는 `StaleObjectStateException`·`OptimisticEntityLockException` 발생 수를 센다(가이드 27.1.7). 엔티티별로 쪼개 보려면 예외 로그에 엔티티 이름을 남긴다.
- 동시성 테스트: 실험 B처럼 배리어로 "모두 읽은 뒤 쓰기"를 강제하면 우연에 기대지 않고 재현된다.

## 장애 시나리오와 대처

### 1. 거대 애그리거트 → 락 경합·`OptimisticLockException` 폭증 (⚠ 커리큘럼)

- **현상**: 사용자가 늘자 "다른 사용자가 먼저 수정했습니다" 오류가 잦아진다. 서로 다른 항목을 고치는데도 그렇다.
- **보이는 형태**: JPA API 쪽에서는 `jakarta.persistence.OptimisticLockException`(Spring의 예외 변환을 거치면 `ObjectOptimisticLockingFailureException` 계열로 보인다 — Spring Framework 6.2.x 소스 `EntityManagerFactoryUtils`가 `OptimisticLockException`을 하위 클래스 `JpaOptimisticLockingFailureException`으로, `HibernateJpaDialect`가 `StaleObjectStateException`·`OptimisticEntityLockException`을 `ObjectOptimisticLockingFailureException`으로 바꾼다. 소스로 확인했고 실행하지는 않았다), 네이티브면 `StaleObjectStateException`. 재시도 로그 급증, 응답 시간 증가(실험 A: 충돌 1938~2313회, 소요 시간 수 배). 비관적 잠금이면 `FOR UPDATE` 대기와 락 대기 타임아웃.
- **원인**: 버전(또는 락)의 단위가 업무상 독립적인 수정까지 묶는다. 루트 하나에 자식이 수백 개.
- **대처**: 진짜 불변식을 다시 적고, 그 불변식이 걸치지 않는 자식을 별도 애그리거트로 떼어 ID로 참조한다(Vernon의 Product → BacklogItem·Release·Sprint 분리). 쪼갠 뒤 같은 시나리오로 충돌 수를 다시 잰다.

### 2. 경계 밖 불변식 → 동시성에 깨짐 (⚠ 커리큘럼)

- **현상**: 용량 10인 스프린트에 24점이 들어가 있다. 재고가 음수다. 한 좌석에 예약이 둘이다.
- **보이는 형태**: 예외 없음. 위반 데이터 조회 쿼리(진단 절)나 고객 문의로 발견된다(실험 B outside: 합 24).
- **원인**: 검사(합 읽기)와 쓰기가 서로 다른 행에 있고, 그 사이를 잠그는 공통 지점이 없다. READ COMMITTED는 이것을 막지 않는다.
- **대처**: 그 불변식이 걸친 범위를 한 애그리거트로 묶고 루트 버전을 올린다(inside: 합 9). 묶을 수 없으면 DB 제약(UNIQUE·EXCLUDE·CHECK)이나 SERIALIZABLE, 또는 규칙을 결과적 일관성 + 보상으로 바꾸는 것을 업무와 합의한다.

### 3. 자식만 수정해 루트 버전이 안 오름

- **현상**: 주문 줄 수량 합 한도가 있는데, 서로 다른 줄을 고친 두 요청이 모두 성공해 한도를 넘었다.
- **보이는 형태**: 실험 C — 자식만 고친 뒤 루트 `version = 1` 그대로. 예외 없음.
- **원인**: 버전 검사에는 루트의 비관계 필드와 루트가 소유한 연관 자체만 들어간다(JPA 3.1 §3.4.2). 자식 엔티티의 필드 변경은 자식만 dirty하게 만든다. `mappedBy`든 소유 단방향이든 같다(실험 C·C-3).
- **대처**: 자식을 바꾸는 모든 경로가 루트 메서드를 거치게 하고, 그 안에서 `OPTIMISTIC_FORCE_INCREMENT`로 루트를 잠근다. 자세한 재현은 [database/52](../../database/52-offline-concurrency-patterns/2-summary.md) 장애 3.

### 4. 한 트랜잭션에서 여러 애그리거트 수정 → 트랜잭션이 길어지고 실패 범위가 커짐

- **현상**: "주문 + 재고 + 포인트 + 쿠폰"을 한 트랜잭션에서 고치는 결제 API가 피크 때 자주 실패한다.
- **보이는 형태**: 어느 하나의 버전 충돌·락 대기로 전체 롤백. 락 순서가 요청마다 다르면 교착(PostgreSQL `deadlock detected`, SQLSTATE 40P01)도 가능하다.
- **원인**: 경계 밖 갱신까지 한 트랜잭션에 넣었다. Vernon 1부의 "트랜잭션당 애그리거트 하나" 기본값을 어겼다.
- **대처**: 사용자에게 즉시 보여야 하는 하나만 트랜잭션에 남기고 나머지는 이벤트로 넘긴다. 예외 사유(UI 일괄 생성 등)로 묶는다면 그 사유와 사용자–애그리거트 친화성을 기록한다.

### 5. 너무 잘게 쪼갬 → 진짜 불변식을 못 지킴

- **현상**: "작은 애그리거트" 방침에 따라 주문 줄을 별도 애그리거트로 뺐더니 주문 한도 검사가 깨진다.
- **보이는 형태**: 장애 2와 같다 — 예외 없는 위반 데이터.
- **원인**: Vernon도 경고한 반대쪽 극단 — 애그리거트를 앙상하게 벗겨 진짜 불변식을 보호하지 못한다(1부). Evans 『DDD』의 애그리거트 예(구매 주문의 최대 허용 총액과 줄 합계, Vernon 1부가 인용)는 엔티티 여러 개가 한 애그리거트에 들어가는 경우다.
- **대처**: 크기가 아니라 불변식에서 출발한다. 규칙 문장 하나마다 "이 규칙이 즉시 성립해야 하나"를 업무 담당자와 확인한다.

## 핵심 문장

- 애그리거트는 불변식을 한 트랜잭션 안에서 지키는 일관성 경계다. 바깥은 루트만 참조하고, 루트가 불변식을 검사한다.
- 버전·락의 단위가 곧 다투는 범위다. 거대 애그리거트는 상관없는 수정까지 충돌시킨다(실험: 400 커밋에 충돌 약 2천 회 vs 0회).
- 불변식이 걸친 범위가 잠금 범위 밖이면 검사 코드가 있어도 동시성에 깨진다(실험: 용량 10에 24점).
- Vernon의 4규칙은 진짜 불변식은 경계 안에, 작게, ID로 참조, 경계 밖은 결과적 일관성이다. 예외 네 가지를 인정한다.
- JPA에서 자식 엔티티의 필드만 고치면(`mappedBy`든 소유 단방향이든) 루트 버전이 오르지 않는다. 자식 변경 경로는 루트를 거치고 루트 버전을 강제로 올린다.

## 관련 주제·근거

- 선행
  - [04-entities-and-value-objects](../04-entities-and-value-objects/2-summary.md)
  - [database/13-transactions-acid](../../database/13-transactions-acid/2-summary.md) · [database/14-isolation-levels-and-anomalies](../../database/14-isolation-levels-and-anomalies/2-summary.md)
- 후속·연결
  - [08-domain-services-and-policies](../08-domain-services-and-policies/2-summary.md) · [09-domain-events](../09-domain-events/2-summary.md) · [10-repositories-and-factories](../10-repositories-and-factories/2-summary.md)
  - [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md) · [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md) · [database/52-offline-concurrency-patterns](../../database/52-offline-concurrency-patterns/2-summary.md)
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [distributed/15-saga](../../distributed/15-saga/2-summary.md)
  - 연습: [basic/13-inventory](../basic/13-inventory/2-summary.md) · [advanced/11-stock-reservation](../advanced/11-stock-reservation/2-summary.md) · [advanced/12-seat-hold](../advanced/12-seat-hold/2-summary.md)
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015) "Aggregates" 항목 <https://www.domainlanguage.com/ddd/reference/>
  - Eric Evans, 『Domain-Driven Design』(2003) 6장 "The Life Cycle of a Domain Object" — AGGREGATES 절(InformIT 목차로 확인, 본문 미열람)
  - Vaughn Vernon, "Effective Aggregate Design" Part I~III(2011) <https://www.dddcommunity.org/library/vernon_2011/> — PDF 본문 확인(1부: 불변식 정의·Bill/Joe·70%; 2부: Reasons To Break the Rules; 3부: 4규칙 목록)
  - Vaughn Vernon, 『Implementing Domain-Driven Design』(2013) 10장 Aggregates(목차 확인, 본문 미열람)
  - Spring Data JDBC Reference "Domain Driven Design and Relational Databases" <https://docs.spring.io/spring-data/relational/reference/jdbc/domain-driven-design.html>
  - Jakarta Persistence 3.1 §3.4.2 Version Attributes, §3.4.4 Lock Modes <https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>
  - Hibernate ORM 6.6 User Guide — 예외 종류(부트스트랩 방식별), 27.1.7 `getOptimisticFailureCount` <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
  - Spring Framework 6.2.x 소스 `spring-orm/.../orm/jpa/EntityManagerFactoryUtils.java`·`orm/jpa/vendor/HibernateJpaDialect.java` — 낙관적 잠금 예외 변환 <https://github.com/spring-projects/spring-framework/tree/6.2.x/spring-orm/src/main/java/org/springframework/orm/jpa>
- 실험 목록 (코드: scratchpad `dm/04/e05/Agg.java`·`Hib05.java`, PostgreSQL 17.11 컨테이너 `sn-dm-w04-pg` + JDK 21.0.12 eclipse-temurin, 네트워크 `sn-dm-w04-net`, 모두 `--cpus=2`, 실행 후 삭제)
  - A 거대 vs 작은 애그리거트 버전 충돌 — `java -cp postgresql-42.7.4.jar Agg.java`, 집필 2회 실행 × 3측정 + 사실 점검 재실행 2회 × 3측정: 충돌 1938~2313 vs 0
  - B 경계 밖 vs 안 불변식 — 같은 실행: 합 24 vs 9, 재시도 14~18
  - C Hibernate 6.6.29 `mappedBy` 자식 수정 시 루트 버전, `OPTIMISTIC_FORCE_INCREMENT` 충돌 — `javac -cp 'libs/*' -d out Hib05.java && java -cp 'out:libs/*' Hib05`
  - C-2 `@ElementCollection` 원소 추가 시 루트 버전 0 → 1 — `Hib05b.java`
  - C-3 소유 단방향 `@OneToMany @JoinColumn` 자식 필드 수정 시 0 그대로, 자식 추가 시 0 → 1 — scratchpad `dm/04/adj/Adj.java`, Hibernate 6.6.29 + H2 2.3.232 메모리 DB, JDK 21 eclipse-temurin `--cpus=2`, `javac -cp '../libs/*' -d out Adj.java && java -cp 'out:../libs/*' Adj`, 1회
