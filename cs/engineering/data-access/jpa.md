# JPA와 Hibernate — 영속성 컨텍스트라는 아이디어와 그 청구서

> 이 컬렉션의 인덱스는 [README.md](./README.md)에서 시작한다. 반대편 도구는 [spring-data-jdbc.md](./spring-data-jdbc.md), 둘의 축별 비교는 [comparison.md](./comparison.md)에 있다.\
> 출처: `jun-bank/docs/study/tech/data-access/jpa.md` · 이관일 2026-09-16.\
> 본문 절은 **원고**를 고쳐 쓴 것이다(문체·순서 유지, 특정 프로젝트 고유 상황을 일반 상황으로). 「한눈에」·「전체 흐름」의 비유·그림과 맨 끝 `[Claude 추가]`는 **Claude가 원고 이해를 돕기 위해 보탠 것**이다. 인용한 스펙 문장은 Jakarta Persistence 3.1, Hibernate 문장은 ORM 6.6 문서 기준이다.

**한 줄로**: JPA는 "객체 그래프를 통째로 다루고 싶다"는 요구를 **영속성 컨텍스트** 하나로 풀었고, 더티체킹·flush·지연 로딩·N+1은 전부 그 하나의 결정에서 갈라져 나온 청구서다.

---

## 한눈에 — 쉽게 말하면

**개인 비서를 한 명 붙인 것**이라고 생각하면 된다. *(Claude 보강 — 원고에 없는 비유)*

```text
[비서 없음 — 직접 매핑]              [비서 있음 — 영속성 컨텍스트]
서류를 꺼내 오라고 시킴               "1번 서류 줘"  → 비서가 갖고 있으면 그대로 줌
  → SELECT 직접                       (같은 서류는 두 번 안 꺼냄 = 동일성 보장)
고친 곳을 내가 적어 둠                내가 서류에 낙서만 하면
  → UPDATE 문 직접 고름                 비서가 퇴근길(커밋)에 알아서 정서한다
언제 제출할지 내가 정함               제출 시점도 비서가 규칙대로 정한다
```

**코드도 똑같은 구조다.** JPA를 쓰면 "꺼내 와라·바뀐 걸 적어라·언제 제출해라"를 프레임워크(비서)가 대신한다.\
편해지는 대신, **비서가 언제 무엇을 했는지 내 코드만 봐서는 알 수 없게 된다.** 이 맞교환이 이 문서 전체의 줄거리다.

---

## 이 개념이 답하려는 질문

메모리 위 객체는 **참조로 연결된 그래프**이고, 관계형 DB는 **값(외래키)으로 연결된 행의 집합**이다.\
이 둘은 모양이 다르다. JPA는 그 사이를 오가는 부담을 어디까지 대신 져 줄 수 있는가에 답한다.

각 절이 답하는 질문을 미리 늘어놓으면 이렇다.

```text
§1  왜 손으로 매핑하면 힘든가            → 변환 코드가 아니라 그 주변의 "부기"가 문제다
§2  그 부기를 어디에 맡기나              → 트랜잭션 동안 "관리되는 객체 집합" 하나
§3  객체가 저장되나 안 되나 어떻게 아나   → 객체가 아니라 객체의 "상태"를 본다
§4  save()도 안 불렀는데 왜 UPDATE가?    → 더티체킹 (스냅샷 비교)
§5  그 UPDATE는 정확히 언제 나가나        → flush (별도 개념으로 승격)
§6  그래프를 다 안 읽으려면              → 지연 로딩 (프록시)
§7~8 그 대가는                          → N+1, 그리고 "숨은 SQL"
```

---

## 전체 흐름

더티체킹·flush·지연 로딩·N+1은 따로 있는 기능이 아니라, **하나의 결정에서 세로로 갈라져 나온다.**

```text
문제: 객체 그래프 ≠ 테이블 행 (§1)
        ↓
결정: 트랜잭션 동안 "관리되는 객체 집합"을 하나 둔다 = 영속성 컨텍스트 (§2)
        ↓
   ├─ 그 집합 안에 있나 없나로 객체의 성질이 갈린다 → 생명주기 4상태 (§3)
   ├─ 집합이 로드 시점 스냅샷을 들고 있다        → 더티체킹: save() 없이 UPDATE (§4)
   ├─ 모아 둔 변경을 언제 내보내나              → flush: 실행 시점이 코드와 어긋남 (§5)
   └─ 그래프를 다 읽지는 않으려고 프록시를 심는다 → 지연 로딩 (§6)
        ↓
청구서: 반복문이 SQL을 낳고(N+1, §7), 실행 시점이 코드에 없다(숨은 SQL, §8)
```

---

## 1. 문제 — 객체 그래프와 테이블 행은 같은 모양이 아니다

> 출처: 원고 §1

메모리 위의 객체는 참조로 연결된 그래프이고, 관계형 DB는 값(외래키)으로 연결된 행의 집합이다.\
Martin Fowler는 이 둘을 "데이터의 서로 꽤 다른 두 표현(two quite different representations of data)"이라 부르며, 메모리 구조가 훨씬 자유롭기 때문에 사람들이 그쪽으로 프로그래밍하고 싶어 한다고 정리한다([OrmHate](https://martinfowler.com/bliki/OrmHate.html)).\
두 표현 사이를 오가는 층을 따로 두자는 것이 Data Mapper 패턴이다 — "객체와 DB 사이에서 데이터를 옮기되 서로를, 그리고 매퍼 자신을 모르게 유지하는 매퍼들의 층"([P of EAA: Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html)).

손으로 매핑하던 시절의 부담은 변환 코드 자체가 아니라 그 주변의 **부기(bookkeeping)**였다.

> **부기(bookkeeping)** — 무엇을 읽었고 무엇을 바꿨는지 장부처럼 계속 기록·대조하는 뒤치다꺼리.\
> 예: "이 행은 아까 읽었으니 또 읽지 말자", "이 필드가 바뀌었으니 UPDATE 대상이다"를 사람이 손으로 챙기는 일.

같은 행을 두 경로에서 읽으면 서로 다른 객체 두 개가 생겨 한쪽 수정이 다른 쪽에서 보이지 않았고, 무엇이 바뀌었는지를 개발자가 기억해 UPDATE 문을 골라 써야 했으며, 그 순서와 시점도 사람이 정해야 했다.\
이 부기를 라이브러리가 대신 하려면 **트랜잭션 동안 어떤 객체를 읽고 무엇을 바꿨는지 기억하는 자리**가 필요하다.

---

## 2. 아이디어 — 트랜잭션 동안 "관리되는 객체 집합"을 하나 둔다

> 출처: 원고 §2

그 자리가 **영속성 컨텍스트(persistence context)**이고, 개념적으로는 두 고전 패턴의 결합이다.

> **영속성 컨텍스트(persistence context)** — 트랜잭션이 사는 동안, 읽고 고친 엔티티를 붙들어 두고 관리하는 메모리 위의 집합.\
> 예: 한 요청 안에서 계좌 객체를 꺼내 잔액을 고치면, 커밋될 때까지 그 객체는 이 집합 안에서 추적된다.

- **Identity Map**은 "각 객체가 한 번만 로드되도록 로드된 객체를 맵에 담아 두고, 참조할 때 그 맵을 먼저 본다"([P of EAA](https://martinfowler.com/eaaCatalog/identityMap.html)).
- **Unit of Work**는 "비즈니스 트랜잭션의 영향을 받은 객체 목록을 유지하고 변경분 기록과 동시성 문제 해결을 조율한다"([P of EAA](https://martinfowler.com/eaaCatalog/unitOfWork.html)).

스펙의 정의도 같은 말을 한다. Jakarta Persistence는 §7.1에서 영속성 컨텍스트를 "어떤 영속 엔티티 식별자에 대해서도 엔티티 인스턴스가 오직 하나만 존재하는 엔티티 인스턴스들의 집합"으로 규정한다([Jakarta Persistence 3.1](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html)).\
Hibernate는 이 집합을 Session이 들고 있는 **1차 캐시**라고 부른다 — "Session은 JDBC Connection을 감싸며 애플리케이션 도메인 모델의 대체로 'repeatable read'인 영속성 컨텍스트(1차 캐시)를 유지한다"([Hibernate User Guide 2.1](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html)).

여기서 나오는 보장이 **동일성 보장**이다. 같은 트랜잭션 안에서 같은 행을 두 번 조회하면 같은 자바 객체가 돌아온다.\
1차 캐시는 성능 기능이기 이전에 **"한 행 = 한 객체"라는 규칙을 지키기 위한 장치**이고, 뒤에 나오는 기능 대부분이 이 규칙 위에 서 있다.

---

## 3. 생명주기 — 관리 대상은 객체가 아니라 객체의 상태다

> 출처: 원고 §3

영속성 컨텍스트가 생기면 객체는 "그 집합 안에 있는가"에 따라 성질이 달라진다. 스펙은 네 상태를 정의한다(§3.2).

```text
       new 연산자로 막 생성                         DB에서 제거 표시
            │                                            ▲
            ▼         persist()                          │ remove()
        ┌────────┐  ─────────────►  ┌──────────┐  ───────┴──►  ┌─────────┐
        │  new   │                  │ managed  │              │ removed │
        └────────┘  ◄─────────────  └──────────┘
                        (재부착)          │
                                          │ 컨텍스트가 닫힘
                                          ▼
                                     ┌──────────┐
                                     │ detached │  ← 더 이상 추적 안 됨
                                     └──────────┘
```

- **new** — "new 연산자로 막 생성되어 아직 영속성 컨텍스트와 연결되지 않은" 상태
- **managed** — "영속성 컨텍스트와 연결된" 상태 (여기 있는 동안만 더티체킹·지연 로딩이 동작한다)
- **detached** — "관리하던 영속성 컨텍스트가 닫혀 분리된" 상태
- **removed** — "DB에서 제거되도록 표시된" 상태

Hibernate 입문 가이드는 이 흐름을 "persist()와 remove()는 엔티티 생명주기의 시작과 끝을 긋는 것으로 볼 수 있다"고 요약한다([Hibernate Introduction](https://docs.hibernate.org/orm/6.6/introduction/html_single/Hibernate_Introduction.html)).

```kotlin
@Entity
class AccountEntity(
    @Id val id: Long,
    var balance: Long,
)

val fresh = AccountEntity(id = 1, balance = 0)   // new — DB와 무관한 객체
em.persist(fresh)                                // managed — 이제 컨텍스트가 추적한다
val found = em.find(AccountEntity::class.java, 1) // managed — fresh와 같은 인스턴스다 (동일성 보장)
```

실무에서 헷갈리는 지점은 대부분 이 상태 축에 있다.\
"왜 저장이 안 되지"는 대개 detached 객체를 고친 것이고, "왜 저장했는데 값이 다르지"는 managed 객체를 나중에 또 고친 것이다.\
객체를 보고 판단할 수 없고 **그 객체가 지금 어떤 컨텍스트 안에 있는지를 알아야** 판단할 수 있다는 점이, JPA를 처음 배울 때 가장 낯선 부분이다.

---

## 4. 더티체킹 — save()를 부르지 않았는데 UPDATE가 나가는 이유

> 출처: 원고 §4

**언제 쓰나** — managed 상태 객체의 필드를 바꾸기만 하면, 별도 저장 호출 없이 UPDATE가 실행된다.

> **더티체킹(dirty checking)** — 컨텍스트가 로드 시점의 값(스냅샷)을 갖고 있다가, 커밋 직전에 현재 값과 비교해 달라진 컬럼을 찾아 UPDATE 하는 것.\
> 예: 잔액을 읽어서 `-= 6000` 하고 아무것도 안 불러도, 커밋 때 `balance`만 바뀐 걸 알아채고 그 컬럼만 UPDATE 한다.

```text
로드 시점 스냅샷:  balance = 10000        (컨텍스트가 몰래 복사해 둠)
필드 대입:         balance = 4000         (내 코드는 이 한 줄뿐)
        ↓  커밋 직전 비교
바뀐 컬럼: balance   → UPDATE account SET balance = 4000 WHERE id = ?
```

스펙은 결과만 규정한다: "flush 시점에 영속성 제공자는 영속 엔티티에 대한 모든 변경을 DB에 적용한다"(§3.2.4).

```kotlin
@Transactional
fun withdraw(id: Long, amount: Long) {
    val account = em.find(AccountEntity::class.java, id)
    account.balance -= amount     // 저장 호출 없음
}                                 // 커밋 시점에 UPDATE account SET balance = ? WHERE id = ?
```

**비용** — 이것이 Unit of Work가 약속한 편의의 실체이고, 동시에 첫 번째 청구서다.\
저장 코드가 사라지면 **"어디서 DB에 쓰는가"라는 질문에 코드가 답하지 못한다** — 답은 "managed 객체를 만진 모든 곳"이 된다.\
반대편 도구를 만든 팀이 이 기능을 뺀 이유로 든 것도 정확히 그 점이다("dirty tracking... obscures the single point where persistence operations execute", [Introducing Spring Data JDBC](https://spring.io/blog/2018/09/17/introducing-spring-data-jdbc)).

---

## 5. flush — "언제 SQL이 나가는가"가 별도 개념이 된다

> 출처: 원고 §5

**언제 쓰나** — 변경을 모아 두었다가 나중에 쓰기로 한 순간, "모아 둔 것을 실제로 내보내는 시점"이 개념으로 승격된다. 그것이 flush다.

> **flush** — 컨텍스트에 쌓인 변경을 실제 SQL로 DB에 내보내는 동기화 동작.\
> 예: 필드를 세 번 고쳐도 DB엔 아무 일이 없다가, flush가 일어나는 순간 밀린 UPDATE들이 한꺼번에 나간다.

JPA는 두 모드를 정의한다(§3.3.1) — **AUTO**는 트랜잭션 중 필요 시점마다 동기화하고, **COMMIT**은 커밋 때만 동기화한다.\
Hibernate는 여기에 ALWAYS와 MANUAL을 더해 네 가지를 제공한다([Hibernate User Guide 7. Flushing](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html)).

기본값 AUTO의 핵심 규칙은 하나다 — 커밋할 때, 그리고 **쿼리를 실행하기 직전에** 밀린 변경을 먼저 내보낸다.\
이유는 정합성이다. 방금 메모리에서 바꾼 값을 반영하지 않은 채 JPQL을 실행하면 같은 트랜잭션 안에서 자기 변경을 못 보는 결과가 나오기 때문이다.

```text
코드 줄 순서                    실제 SQL 순서 (AUTO)
account.balance -= 6000    →    (아직 아무 일 없음)
val list = query(...)      →    ① 밀린 UPDATE account ... 를 먼저 내보내고
                                ② 그다음 SELECT
```

**비용** — 대가는 SQL 실행 순서가 코드 줄 순서와 일치하지 않는다는 것이다 — 조회 한 줄이 앞선 여러 UPDATE를 촉발할 수 있다.\
이 타이밍은 성능 문제가 아니라 **동시성·잠금 문제**로 나타날 때 더 아프다.\
어떤 행에 언제 잠금이 걸리는지가 flush 시점에 달려 있는데, 그 시점을 결정하는 것은 개발자가 쓴 문장이 아니라 프레임워크의 규칙이기 때문이다.\
잠금 순서가 불변식의 일부인 도메인에서는 이 간접성이 그대로 위험이 된다.

---

## 6. 지연 로딩 — 그래프를 다 읽지 않으려는 프록시

> 출처: 원고 §6

**언제 쓰나** — 애그리게이트를 통째로 다루려면 연관 객체도 함께 있어야 하는데, 참조를 따라 전부 읽으면 주문 하나 조회에 DB 절반이 딸려 온다. 그걸 막으려는 게 지연 로딩이다.

> **지연 로딩(lazy loading)** — 연관 필드에 **프록시**(대역 객체)를 심어 두고, 실제로 그 필드를 건드리는 순간에야 SELECT를 실행하는 것.\
> 예: 주문을 읽을 때 주문 항목은 안 읽고, `order.lines`를 처음 만질 때 그제서야 항목 SELECT가 나간다.

```kotlin
@Entity
class OrderEntity(
    @Id val id: Long,
    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
    val lines: MutableList<OrderLineEntity> = mutableListOf(),
)
```

**비용** — 프록시는 **살아 있는 컨텍스트를 전제**하므로, 컨텍스트가 닫힌 뒤 그 필드를 만지면 `LazyInitializationException`("could not initialize proxy - no Session")이 난다.\
흔한 회피책인 Open Session in View에 대해 Vlad Mihalcea는 "DB 관점에서 매우 비효율적이므로 엔터프라이즈 애플리케이션에서 절대 쓰지 말라"고 못박고, 정석은 필요한 연관을 쿼리에서 명시적으로 가져오는 것(JOIN FETCH)이나 DTO 프로젝션이라고 말한다([The best way to handle the LazyInitializationException](https://vladmihalcea.com/the-best-way-to-handle-the-lazyinitializationexception/)). `[실무 의견]`

---

## 7. 비용 ① N+1 — 반복문이 SQL을 낳는다

> 출처: 원고 §7

지연 로딩의 대가가 가장 자주 드러나는 형태가 N+1이다.

> **N+1 문제** — 주 쿼리 한 번(1)으로 목록을 읽은 뒤, 각 항목의 연관을 채우느라 항목 수만큼(N) 추가 쿼리가 나가는 것.\
> 예: 주문 100건을 SELECT 한 번으로 읽고, 각 주문의 항목을 만지느라 SELECT가 100번 더 나가 총 101번.

정의는 "데이터 접근 프레임워크가, 주 쿼리 실행 시 함께 가져올 수 있었던 데이터를 위해 N개의 추가 SQL을 실행하는" 상황이다([Vlad Mihalcea, N+1 query problem](https://vladmihalcea.com/n-plus-1-query-problem/)).\
각 쿼리는 빨라서 슬로우 쿼리 로그에 걸리지 않고, **합계만 느려진다는 점**이 이 결함의 성질을 말해 준다.

```kotlin
val orders = em.createQuery("select o from OrderEntity o", OrderEntity::class.java).resultList
orders.forEach { it.lines.size }   // 주문 한 건마다 SELECT — 총 1 + N회
```

**비용** — 고치는 방법은 "가져올 것을 쿼리에서 말한다"로 수렴한다 — JPQL의 `join fetch`, 엔티티 그래프, 배치 페치, 그리고 애초에 엔티티가 아니라 필요한 컬럼만 뽑는 DTO 프로젝션이다(Hibernate User Guide의 association fetching·batch fetching·join fetching 절).\
여기서 드러나는 구조가 중요하다 — **자동 로딩이 만든 문제를 수동 지시로 되돌리는 것**이 정석 해법이고, 그 지시가 늘어날수록 "SQL을 안 쓰기 위해 도입한 도구로 SQL 계획을 짜는" 상태에 가까워진다.

---

## 8. 비용 ② 숨은 SQL — 실행 시점이 코드에 없다

> 출처: 원고 §8

앞의 세 절은 서로 다른 결함이 아니라 **한 설계의 세 얼굴**이다.

```text
더티체킹   →  쓰기 지점을 감춘다   ("어디서 DB에 쓰나")
flush      →  실행 시점을 감춘다   ("언제 SQL이 나가나")
지연 로딩   →  읽기 지점을 감춘다   ("어디서 SELECT가 나가나")
```

감춘 대가로 얻은 것은 진짜다 — 그래프 저장 코드와 부기가 사라진다.\
Fowler의 균형 잡힌 평가가 이 지점을 잘 요약한다: "ORM은 매핑 문제의 80~90%를 처리할 수 있지만, 마지막 덩어리는 관계형 DB를 정말 이해하는 누군가의 조심스러운 작업이 늘 필요하다"([OrmHate](https://martinfowler.com/bliki/OrmHate.html)).

문제는 나머지 10~20%가 균등하게 흩어져 있지 않다는 것이다.\
그 구간은 대체로 **동시성·잠금·조건부 갱신·대량 조회**에 몰려 있다 — 멱등 판정, 배포 창 잠금, fencing token, 전표의 한 커밋 원자성 같은 것들이다. *(원고의 특정 프로젝트 쓰기 경로 예시를 일반 상황으로 옮김)*

> **fencing token** — 잠금을 잡을 때마다 커지는 번호. 뒤늦게 깨어난 옛 소유자의 쓰기를 "번호가 더 작다"는 이유로 거부해 밀어낸다.\
> 예: 리스 번호 7을 든 작업자가 멈췄다 되살아나 쓰려 해도, 이미 번호 8이 나갔으면 그 쓰기는 막힌다.

낙관적 잠금(`@Version`)처럼 JPA가 표준으로 제공하는 통제 수단도 있지만, "이 UPDATE가 이 조건에서만 성립해야 한다"를 표현하려면 결국 명시 쿼리로 내려가게 된다.

---

## 9. 정리 — JPA가 값을 내는 자리와 어긋나는 자리

> 출처: 원고 §9

JPA는 "객체 그래프를 통째로 다루고 싶다"는 요구에 맞춰 설계된 도구다.\
그래프가 깊고, 화면·유스케이스마다 다른 부분을 오가며 고치고, 각 쓰기가 특별한 동시성 조건을 요구하지 않는 도메인에서 더티체킹과 지연 로딩은 실제로 코드를 크게 줄인다.\
**이때 감춰진 SQL은 비용이 아니라 목적이다.**

반대로 쓰기 하나하나가 "이 조건이 참일 때만 이 행을 이렇게 바꾼다"인 도메인에서는 얻는 것이 적고 감춰진 축만 늘어난다.\
그런 도메인은 이 판단으로 반대편 도구(Spring Data JDBC)를 고르고, JPA는 도입 조건과 함께 잠가 둔다 — 복잡한 객체 그래프의 자동 영속이 실증적으로 필요해질 때 해당 애그리게이트만 교체하는 식이다. *(원고의 특정 프로젝트 결정을 일반 판단으로 옮김)*

그다음 문서인 [`spring-data-jdbc.md`](./spring-data-jdbc.md)는 같은 문제를 정반대 방향에서 푼 도구를 다루고, [`comparison.md`](./comparison.md)가 둘을 축별로 비교한다.

---

## 핵심 문장

- **더티체킹·flush·지연 로딩·N+1은 네 개의 기능이 아니라, "영속성 컨텍스트"라는 하나의 결정에서 갈라져 나온 결과다.**
- **1차 캐시는 성능 기능이기 이전에 "한 행 = 한 객체"(동일성 보장)를 지키는 장치다.**
- **JPA에서 객체의 성질은 객체가 아니라 "지금 어떤 컨텍스트 안에 있는가"(생명주기 상태)가 정한다.**
- **더티체킹은 쓰기 지점을, flush는 실행 시점을, 지연 로딩은 읽기 지점을 감춘다 — 감춘 것이 목적인 도메인에선 이득, 그것이 불변식인 도메인에선 위험.**
- **N+1의 정석 해법은 "가져올 것을 쿼리에서 말한다"로 수렴한다 — 자동 로딩이 만든 문제를 수동 지시로 되돌리는 구조.**

---

## 관련 자료

- 반대편 도구: [`./spring-data-jdbc.md`](./spring-data-jdbc.md) — JPA가 감춘 세 가지를 도로 드러낸 도구. "왜 뺐는가"가 이 문서의 개념 위에서 읽힌다.
- 축별 비교와 선택 기준: [`./comparison.md`](./comparison.md)
- 개념의 뿌리(패턴 정의): [Unit of Work](https://martinfowler.com/eaaCatalog/unitOfWork.html) · [Identity Map](https://martinfowler.com/eaaCatalog/identityMap.html) · [Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html) — 영속성 컨텍스트가 무엇의 구현인지 알려 준다.
- 균형 잡힌 ORM 비판: [OrmHate](https://martinfowler.com/bliki/OrmHate.html)
- 스펙·구현 문서: [Jakarta Persistence 3.1 스펙](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html) (§3 생명주기·flush, §7 컨텍스트) · [Hibernate Introduction](https://docs.hibernate.org/orm/6.6/introduction/html_single/Hibernate_Introduction.html) · [Hibernate User Guide](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html)
- 성능·함정: [N+1 query problem](https://vladmihalcea.com/n-plus-1-query-problem/) · [LazyInitializationException 다루기](https://vladmihalcea.com/the-best-way-to-handle-the-lazyinitializationexception/) (Vlad Mihalcea)

---

## 용어 풀이

- **영속성 컨텍스트(Persistence Context)** — 트랜잭션 동안 읽고 고친 엔티티를 붙들어 관리하는 메모리 집합. JPA의 거의 모든 기능이 여기서 나온다.
- **1차 캐시(First-level Cache)** — 영속성 컨텍스트가 들고 있는 엔티티 맵. "한 행 = 한 객체"(동일성)를 지킨다.
- **동일성 보장(Identity Guarantee)** — 같은 트랜잭션에서 같은 행을 두 번 읽으면 같은 자바 객체가 돌아오는 성질.
- **생명주기 4상태(new·managed·detached·removed)** — 엔티티가 컨텍스트와 맺은 관계. managed일 때만 더티체킹·지연 로딩이 동작한다.
- **더티체킹(Dirty Checking)** — 로드 시점 스냅샷과 현재 값을 비교해 바뀐 컬럼만 자동 UPDATE 하는 것. `save()` 호출이 필요 없다.
- **flush** — 컨텍스트에 쌓인 변경을 실제 SQL로 내보내는 동기화. AUTO 모드는 커밋 시점과 쿼리 실행 직전에 일어난다.
- **지연 로딩(Lazy Loading)** — 연관을 프록시로 두고, 그 필드를 건드릴 때 SELECT 하는 것.
- **프록시(Proxy)** — 실제 엔티티 대신 심어 두는 대역 객체. 접근하는 순간 진짜를 로드한다. 컨텍스트가 닫히면 초기화에 실패한다.
- **N+1 문제** — 목록 조회 1번 + 항목 수 N번의 추가 쿼리가 나가는 것. 각 쿼리는 빠르고 합계만 느리다.
- **DTO 프로젝션** — 엔티티가 아니라 화면에 필요한 컬럼만 뽑아 별도 객체로 받는 조회. N+1·LazyInitializationException의 정석 회피책.
- **JOIN FETCH** — JPQL에서 연관을 조인으로 함께 가져오라고 명시하는 것.
- **낙관적 잠금(Optimistic Locking)** — 버전 컬럼(`@Version`)을 UPDATE의 where 절로 검사해, 그사이 남이 바꿨으면 실패시키는 방식.
- **fencing token** — 잠금마다 커지는 번호로 뒤늦은 옛 소유자의 쓰기를 밀어내는 장치.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **왜 "영속성 컨텍스트"부터 이해해야 잘 읽히나.** 이 문서의 구성이 곧 학습 순서다 — 개별 기능(더티체킹·flush·N+1)을 각각 암기하면 서로 안 이어지지만, "관리되는 객체 집합 하나를 두기로 했다"는 결정 하나에서 전부 파생됨을 잡으면 새로 만나는 증상도 "이건 컨텍스트의 어느 성질인가"로 되짚을 수 있다.
- **2차 캐시(Second-level Cache)는 다른 층이다.** 본문의 1차 캐시는 트랜잭션(Session) 수명만큼 사는 반면, 2차 캐시는 SessionFactory 수준에서 여러 트랜잭션·여러 요청에 걸쳐 산다. 1차 캐시는 정확성(동일성)을 위한 장치이고 2차 캐시는 성능을 위한 선택 기능이라, 목적이 다르다.
- **`merge` vs `persist`.** detached 객체를 다시 managed로 만들려면 `merge`를 쓰는데, `merge`는 인자 객체를 managed로 만드는 게 아니라 **managed 복사본을 새로 반환**한다. "왜 저장이 안 되지"의 흔한 원인 하나가 `merge` 반환값을 안 쓰고 원래 detached 객체를 계속 만지는 것이다.
- **낙관적 잠금과 조건부 UPDATE는 겹치지만 다르다.** `@Version`은 "그사이 아무도 안 바꿨는가"만 검사한다. "점유자가 없을 때만", "토큰이 최대값 미만일 때만" 같은 **도메인 조건**은 버전으로 표현할 수 없어 결국 명시 쿼리의 WHERE 절로 내려간다 — 이 지점이 다음 문서의 출발점이다.
