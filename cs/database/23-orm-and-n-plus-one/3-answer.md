# database/23-orm-and-n-plus-one — 정답

## 정답

### 1. 영속성 컨텍스트의 속

- **식별자 맵**: `HashMap<EntityKey(엔티티 이름, id), 엔티티>`. Hibernate 6.6 `StatefulPersistenceContext.entitiesByKey`다.
- **엔티티별 로드 시점 상태**: 더티 체킹의 비교 기준.
- **작업 큐**: INSERT·UPDATE·DELETE 행동을 모았다가 flush 때 SQL로 내보낸다(Unit of Work).
- 같은 id를 두 번 `find` → SQL은 **한 번**. 두 번째는 맵에서 꺼낸다. **같은 객체**(`==`가 true)가 돌아온다(로컬 재현 `same instance: true`).

### 2. AUTO flush

- 커밋 직전에 나간다. 또는 그보다 먼저, **밀린 변경과 겹치는** JPQL 쿼리 직전에 나간다.
  - 로컬 재현: `update purchase_order ...`가 같은 테이블을 읽는 `select count(...)` **바로 앞**에 나갔다.
- 조회 대상이 겹치지 않는 테이블이면 Hibernate는 그 쿼리 앞에서 flush하지 않는다. UPDATE는 커밋 때 나간다(Hibernate User Guide 7.1.2).
- 네이티브 SQL 쿼리: JPA `EntityManager`로 실행하면 항상 그 앞에서 flush한다. 네이티브 부트스트랩 `Session`은 동기화 정보(`addSynchronizedEntityClass` 등)를 등록해야 flush한다(7.1.3).

### 3. 쿼리 수

- LAZY + 반복문: 1(주문 목록) + 100(주문마다 항목) = **101번**.
- `default_batch_fetch_size=30`: 1 + ⌈100 / 30⌉ = 1 + 4 = **5번**. 초기화할 id를 모아 `where order_id = any(?)`(PostgreSQL)로 묶는다.
- fetch join: **1번**. 다만 결과 행은 주문 × 항목 = 500행이다.
- 로컬 재현(주문 5건): 기본 6 → 배치 10일 때 2 → fetch join 1문장. 배치 크기를 2로 줄이면 1 + ⌈5/2⌉ = 4문장이었다(`any (?)` 두 번 + 남은 1건은 `order_id=?`).

### 4. `@ManyToOne` 기본값

- Jakarta Persistence 3.1 기본은 **EAGER**다(`@OneToMany`는 LAZY).
- EAGER로 두어도 N+1은 사라지지 않는다. JPQL은 쓴 대로 SQL을 만들고, EAGER 연관은 **그 뒤에 따로** SELECT로 채운다.
  - 로컬 재현: 항목 15행 조회 뒤 `select ... from purchase_order where id=?`가 5번 더 나갔다.
- 추가 쿼리 수는 행 수가 아니라 **서로 다른 부모 수**에 비례한다. 식별자 맵이 이미 읽은 부모를 다시 읽지 않는다.
- 권장: `@ManyToOne(fetch = LAZY)`로 두고, 필요한 쿼리에서 fetch join한다.

### 5. 컬렉션 fetch join + 페이징

- SQL에 LIMIT이 **붙지 않는다**. 조인 결과가 주문×항목 행이라, SQL에서 주문 20건 단위로 자를 수 없기 때문이다.
- 경고: `HHH90003004: firstResult/maxResults specified with collection fetch; applying in memory`. 전부 읽고 메모리에서 자른다.
- 고치기:
  - 주문 id 20개를 먼저 페이징 조회한다. 항목은 그 id들로 fetch하거나 batch fetch로 가져온다.
  - `hibernate.query.fail_on_pagination_over_collection_fetch=true`로 이런 쿼리를 예외로 막는다.

### 6. `LazyInitializationException`

- 원인: Session(EntityManager)이 닫힌 뒤 초기화되지 않은 지연 연관을 만졌다. OSIV가 꺼진 Spring에서는 트랜잭션이 끝날 때 EntityManager도 닫히므로 둘이 겹친다. 트랜잭션 종료 자체가 원인은 아니다(OSIV면 트랜잭션 뒤에도 Session이 열려 있다). 직렬화기가 getter를 따라가며 프록시를 건드린 것이다.
- 대처:
  - 트랜잭션 안에서 필요한 연관을 fetch join·엔티티 그래프로 가져온다.
  - DTO로 바꿔 돌려준다. 엔티티를 그대로 JSON으로 내보내지 않는다.
- OSIV(Spring Boot `spring.jpa.open-in-view` 기본 true)의 대가:
  - 요청이 끝날 때까지 EntityManager가 살아 있어, 뷰·직렬화 단계에서도 지연 로딩 SQL이 나간다. N+1이 숨는다.
  - 그 동안 커넥션을 쥐어 풀 고갈이 빨라진다. Spring 리소스 로컬 기본 연결 처리 모드(`DELAYED_ACQUISITION_AND_HOLD`)에서 처음 DB를 쓴 시점부터 요청이 끝날 때까지다.

### 7. 의도치 않은 UPDATE

- managed 엔티티의 `name` 필드를 표시용으로 마스킹했다. flush 때 더티 체킹이 로드 시점 상태와 비교해 "바뀌었다"고 판단했다. save() 호출 없이 UPDATE가 나갔다.
- 막는 법:
  - 표시용 가공은 DTO 복사본에 한다.
  - 조회 경로는 읽기 전용 트랜잭션으로 연다. Spring + Hibernate에서 `readOnly = true`면 flush 모드가 MANUAL이 된다([24](../24-transaction-boundaries-in-app-code/2-summary.md)).
  - 엔티티 setter를 공개하지 않고, 상태 변경은 도메인 메서드로만 한다.

### 8. N+1 잡기

- 슬로 로그에 안 걸리는 이유: 쿼리 하나하나는 인덱스를 타 1ms 안팎으로 빠르다. 느린 것은 **호출 수와 왕복의 합**이다.
- 운영: `pg_stat_statements`에서 `calls`가 요청 수의 수십 배인 짧은 쿼리를 찾는다. APM의 요청당 쿼리 수 지표도 쓴다.
- 테스트: `hibernate.generate_statistics=true`로 문장 수를 세고, API별 상한을 단언한다(`getPrepareStatementCount()`).

### 9. 벌크 UPDATE 뒤의 옛 값

- 이미 컨텍스트에 Order 1이 있었다면 `find`는 **옛 status**를 돌려줄 수 있다.
- 이유: 벌크 update·delete의 효과는 영속성 컨텍스트와 메모리의 엔티티에 반영되지 않는다. 동기화는 애플리케이션 책임이다(Hibernate User Guide). `find`는 식별자 맵에서 옛 객체를 꺼내 준다.
- 대처: 벌크 작업을 트랜잭션 앞쪽에서 한다. 또는 벌크 뒤에 `em.clear()`나 `refresh()`를 부른다.
