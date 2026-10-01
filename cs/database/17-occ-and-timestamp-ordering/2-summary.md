# database/17-occ-and-timestamp-ordering — 낙관적 동시성, 타임스탬프 순서, 버전 컬럼 — 정리 (힌트)

## 해결하는 문제

락(15번)은 "충돌할지도 모른다"는 가정으로 **미리** 막는다. 충돌이 드물면 이것은 낭비다.

```text
  비관적(락)                          낙관적(검증)
  잠근다 → 읽는다 → 고친다 → 푼다        읽는다 → (로컬에서) 고친다 → 커밋 직전에 "그사이 누가 바꿨나?" 확인
  충돌이 없어도 락 비용·대기            충돌이 없으면 재시작 비용 없음(복사·검증 비용은 듦), 있으면 버리고 다시
```

- *낙관적 동시성 제어(OCC)*: 락 없이 진행하고, 끝에서 충돌을 **검증**한다. 충돌하면 중단하고 재시작한다(Kung·Robinson 1981).
- *타임스탬프 순서(T/O)*: 트랜잭션마다 증가하는 타임스탬프를 주고, 실행 결과가 "타임스탬프 순서대로 하나씩 돌린 것"과 같도록 강제한다(CMU 15-445 L18).

쉬운 예: 위키 문서 편집이다.
- 편집 화면을 열 때 "판 번호 7"을 기억한다.
- 저장할 때 "아직 7이면 저장, 아니면 거부"한다.
- 거부되면 최신 판을 다시 불러와 고친다.

똑같은 구조다.\
실무에서는 테이블에 **버전 컬럼**을 두고 `UPDATE ... WHERE id = ? AND version = ?`로 같은 검증을 한다. JPA의 `@Version`이 이것이다.

실무 예:
- 관리자 두 명이 같은 상품 정보를 동시에 고쳐서 한쪽 수정이 사라진다(lost update). 버전 컬럼이 이것을 잡는다.
- 반대로 인기 상품 재고를 `@Version`으로 차감했더니 `OptimisticLockException`과 재시도가 폭증한다.

## 동작·원리

### 1. OCC 세 단계 (Kung·Robinson 1981)

```text
  ┌─ 읽기 단계 ──────────────────┐┌ 검증 ┐┌ 쓰기 ┐
  │ 읽은 것 = read set            ││ 충돌? ││ 반영 │
  │ 쓸 것은 개인 작업 공간에만     ││      ││      │
  └───────────────────────────────┘└──┬───┘└──────┘
                                       └─ 충돌 → 중단, 처음부터 재시작
```

- 읽기 단계: 전역 DB에는 쓰지 않는다. 쓰기는 개인 작업 공간(로컬 사본)에만 한다.
- 검증 단계: 이 트랜잭션에 타임스탬프를 주고(CMU L18), 다른 트랜잭션과 충돌했는지 본다.
- 쓰기 단계: 검증에 통과하면 로컬 사본을 전역으로 반영한다.

검증 규칙: TS(Ti) < TS(Tj)이면 셋 중 하나가 성립해야 한다(Kung·Robinson 3절, CMU L18).

```text
  (1) Ti가 Tj 시작 전에 완전히 끝남                    Ti ■■■■■|        
                                                        Tj           ■■■■■
  (2) Ti 쓰기가 Tj 쓰기 전에 끝남 + WS(Ti) ∩ RS(Tj) = ∅
  (3) Ti 읽기가 Tj 읽기보다 먼저 끝남 + WS(Ti) ∩ (RS(Tj) ∪ WS(Tj)) = ∅
```

- *read set(RS)·write set(WS)*: 트랜잭션이 읽은·쓴 객체 집합.
- 핵심은 "내가 읽은 것을, 나보다 먼저 검증된 누군가가 그사이 썼나?"다.
- 약점(CMU L18): 로컬 복사 비용, 검증·쓰기 단계의 병목, 그리고 **다 실행한 뒤에 중단**하므로 중단이 비싸다.

### 2. 기본 타임스탬프 순서(Basic T/O)

```text
  객체 X마다:  W-TS(X) = X를 마지막으로 쓴 트랜잭션의 TS
               R-TS(X) = X를 읽은 트랜잭션 중 가장 큰 TS

  Ti가 X를 읽으려 함:  TS(Ti) < W-TS(X) ?  → 중단(미래에 쓰인 값을 읽으려 함)
                       아니면 읽고 R-TS(X) = max(R-TS(X), TS(Ti))
  Ti가 X를 쓰려 함:    TS(Ti) < R-TS(X) 또는 TS(Ti) < W-TS(X) ? → 중단
                       아니면 쓰고 W-TS(X) = TS(Ti)
```

- 근거: CMU 15-445 Fall 2023 L17 노트 "Basic T/O". Fall 2024 L18은 같은 T/O 틀 위에서 OCC를 다룬다.
- 아무도 기다리지 않으므로 교착이 없다. 대신 긴 트랜잭션은 새 트랜잭션이 쓴 값을 만나 자주 중단된다(기아).
- *토머스 쓰기 규칙(Thomas Write Rule)*: `TS(Ti) < W-TS(X)`인 쓰기는 중단 대신 **무시**한다. 단 `TS(Ti) < R-TS(X)`이면 여전히 중단이다. 그래서 무시되는 것은 `R-TS(X) ≤ TS(Ti) < W-TS(X)`인 쓰기다. 더 새 값이 이미 있으니 이 쓰기를 읽을 트랜잭션이 없다는 논리다. 기본형은 충돌 직렬화 가능한 스케줄을 만든다. 이 규칙을 쓰면 그 보장이 빠진다(CMU Fall 2023 L17).
- 교재 프로토콜이다. PostgreSQL 17·InnoDB는 행 쓰기 충돌을 행 락(15번)과 MVCC(16번)로 다룬다.

### 3. 앱의 OCC — 버전 컬럼

```text
  T1                                   T2
  SELECT qty, version → (10, 7)
                                       SELECT qty, version → (10, 7)
                                       UPDATE ... SET qty=9, version=8
                                         WHERE id=1 AND version=7   → 1행
  UPDATE ... SET qty=9, version=8
    WHERE id=1 AND version=7           → 0행  ← 충돌 감지. 다시 읽고 재시도
```

- DB 트랜잭션 안의 "검증 + 쓰기"를 `UPDATE` **한 문장**이 원자적으로 한다.
  - PostgreSQL 17 READ COMMITTED: 두 번째 UPDATE는 첫 번째가 커밋(또는 롤백)할 때까지 행 락을 기다린다. 첫 번째가 커밋했으면 **새 버전으로 WHERE를 다시 평가**한다. `version = 7`이 거짓이 되어 0행이다(13.2.1).
  - MySQL 8.4 InnoDB: `UPDATE`는 최신 커밋 버전을 잠그고 조건을 본다(16번). 결과는 같다.
- 검증이 "읽을 때"가 아니라 "쓸 때" 일어나므로, 두 요청 사이에 DB 트랜잭션이 끝나도 된다. 그래서 편집 화면처럼 **여러 요청에 걸친** 작업에 맞는다(52번 오프라인 동시성).

### 4. JPA/Hibernate `@Version`

```java
@Entity
class Product {
    @Id Long id;
    String name;
    int stock;
    @Version long version;   // 엔티티 변경을 flush하는 UPDATE마다 +1, WHERE에 version 조건
                             // (HQL 벌크 UPDATE는 기본적으로 안 올림, @OptimisticLock(excluded) 필드만 바뀌어도 안 올림)
}
```

- Hibernate 6.6 사용자 가이드 11.1이 보여 주는 SQL 모양

```sql
update Phone set callCount = 0, "number" = '+123-456-7890', version = 1
where id = 1 and version = 0
```

- 영향받은 행이 0이면 Hibernate는 `StaleObjectStateException`(네이티브) 또는 Jakarta Persistence `OptimisticLockException` 계열을 던진다(가이드 6장·11장).
- Spring은 이를 `OptimisticLockingFailureException` 계열로 번역한다.
  - Hibernate `StaleObjectStateException`·`StaleStateException` → `ObjectOptimisticLockingFailureException`(Spring 6.2 `HibernateJpaDialect`)
  - `jakarta.persistence.OptimisticLockException` → `JpaOptimisticLockingFailureException`(`EntityManagerFactoryUtils`)
- 허용 타입: Jakarta Persistence 기준 `int`·`Integer`·`short`·`Short`·`long`·`Long`·`java.sql.Timestamp`. Hibernate는 `Instant` 같은 날짜 타입도 허용한다. 가이드는 타임스탬프 버전이 "버전 번호보다 덜 믿을 만하다"고 적는다.
- 앱이 버전 값을 직접 고치면 안 된다(가이드 "forbidden"). 강제로 올리려면 `LockModeType.OPTIMISTIC_FORCE_INCREMENT`.

### 5. 충돌률이 성능을 가른다

로컬 재현(예시, PostgreSQL 17.11) — 행 1개(재고 100,000)를 여러 세션이 "읽기 → 1ms 계산(예시) → 쓰기 → 커밋"으로 각 200번 차감했다.

```text
  방식                               세션  성공   재시도   세션당 평균 시간   실제 차감
  버전 조건 UPDATE (OCC)               1    200       0        0.9 s          200
  버전 조건 UPDATE (OCC)               8   1600    6605       17.4 s         1600
  검증 없이 읽은 값으로 SET qty = q-1    8   1600       0        4.0 s          202   ← 1398건 소실
  조건부 원자 UPDATE qty = qty-1         8   1600       0        4.1 s         1600
```

- OCC는 **정확**했다(1600 = 1600). 하지만 경합 8에서 성공 1건당 약 4번 재시도했고, 같은 경합의 원자 UPDATE(4.1 s)보다 약 4배 느렸다.
- 검증 없는 "읽고-계산-쓰기"는 빨랐지만 차감의 약 87%가 사라졌다(lost update).
- 같은 행에 몰리는 쓰기에는 DB가 계산하는 원자 UPDATE가 맞다(18번).

## 쓰이는 자료구조·알고리즘

- **버전 번호 비교(CAS)** — "기대한 버전이면 바꾼다"는 compare-and-swap과 같은 구조다. `UPDATE ... WHERE version = ?`가 DB 수준의 CAS다. [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)
- **read set·write set 교집합 검사** — 집합 교집합으로 충돌을 판정한다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **단조 증가 타임스탬프** — 벽시계·논리 카운터·혼합 방식이 있다. 벽시계는 서머타임 같은 경계에서, 카운터는 오버플로·분산 환경에서 문제가 된다(CMU L18). [ops-patterns/14-logical-clock](../../ops-patterns/14-logical-clock/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 언제 OCC를 고르나

| 상황 | 고를 것 |
|---|---|
| 충돌이 드묾, 사람이 오래 보는 편집 화면 | 버전 컬럼(OCC) |
| 요청 사이에 DB 트랜잭션을 열어 둘 수 없음 | 버전 컬럼(OCC) — 락은 트랜잭션이 끝나면 풀린다 |
| 같은 행에 쓰기가 몰림(재고·카운터·잔액) | 원자 UPDATE(`SET qty = qty - 1 WHERE id = ? AND qty > 0`) 또는 `FOR UPDATE`(18번) |
| 여러 행을 함께 검증해야 함 | aggregate 루트 버전을 함께 올리기(52번) |

### 2. 순수 SQL로

```sql
-- PostgreSQL 17 / MySQL 8.4 공통
SELECT id, name, price, version FROM product WHERE id = 42;          -- version = 7
UPDATE product SET price = 1200, version = version + 1
WHERE id = 42 AND version = 7;
-- 영향받은 행 수 확인: 0이면 그사이 바뀌었거나 행이 지워졌다 → 다시 읽어 구분하고, 충돌이면 사용자에게 알리거나 재시도
```

- PostgreSQL은 `UPDATE ... RETURNING version`으로 새 버전을 바로 받을 수 있다.

### 3. 재시도는 상한과 함께, 트랜잭션 바깥에서

```java
for (int attempt = 1; ; attempt++) {
    try {
        productService.changePrice(id, newPrice);          // @Transactional: 읽기부터 다시
        return;
    } catch (OptimisticLockingFailureException e) {
        if (attempt >= 3) throw new ConflictException(e);  // 사람이 결정할 충돌이면 409로
        Thread.sleep(ThreadLocalRandom.current().nextLong(10, 50) * attempt);  // 예시 값
    }
}
```

- 재시도할 때는 **다시 읽어야** 한다. 같은 영속성 컨텍스트의 낡은 엔티티로 다시 저장하면 또 실패한다.
- 사람이 편집한 내용의 충돌은 자동 재시도하면 안 된다. 한쪽 수정을 덮어쓰게 된다. HTTP에서는 `If-Match`·`412`(api-design 11번)나 `409`로 알린다.

### 4. 관측

- 재시도 횟수·최종 실패 수를 지표로 남긴다. 재시도율이 오르면 경합 증가 신호다.
- Hibernate 통계의 optimistic failure 수(`Statistics.getOptimisticFailureCount()` — 6.6 API 문서: Hibernate `StaleObjectStateException`·JPA `OptimisticLockException` 발생 수)를 볼 수 있다.
- PostgreSQL: `pg_stat_user_tables.n_tup_upd`와 앱 재시도 수를 비교해 헛돈 읽기 비율을 가늠한다.

## 장애 시나리오와 대처

### 1. 경합 높은 행에 OCC → `OptimisticLockException` 재시도 폭증

- **현상**: 이벤트 오픈 직후 재고 차감 API의 지연이 수 배로 늘고 일부가 실패한다. DB CPU도 오른다.
- **보이는 형태**: 로그에 `ObjectOptimisticLockingFailureException`·`StaleObjectStateException`(Hibernate 6.6 소스 메시지: `Row was updated or deleted by another transaction (or unsaved-value mapping was incorrect)`)이 쏟아진다. 재시도 상한을 넘은 요청은 500·409.
- **원인**: 한 행에 N명이 동시에 쓰면 각 라운드에 1명만 이긴다. 나머지는 읽기·계산·UPDATE를 모두 버린다. 로컬 재현에서는 경합 8에서 성공 1건당 재시도 약 4번, 시간 약 4배였다.
- **대처**
  - 쓰기가 몰리는 행은 OCC를 버리고 원자 조건부 UPDATE로 바꾼다(`SET stock = stock - ? WHERE id = ? AND stock >= ?`).
  - 순서 보장이 필요하면 `SELECT ... FOR UPDATE`로 줄을 세운다(15·18번).
  - 재시도는 상한 + 지터 백오프. 무한 재시도는 부하를 키운다.

### 2. 버전 없이 "읽고-계산-쓰기" → 조용한 lost update

- **현상**: 에러는 없는데 재고·포인트가 맞지 않는다.
- **보이는 형태**: 없음. 로컬 재현에서 1600번 "성공"했는데 실제 차감은 202였다.
- **원인**: 앱이 읽은 값으로 계산해 `SET qty = ?`로 덮어썼다. MySQL REPEATABLE READ도 이것을 막지 않는다(16번).
- **대처**: 버전 컬럼을 두거나, DB에서 계산하는 UPDATE로 바꾼다. 정기 대사(재고 = 입고 − 출고 합)로 탐지한다.

### 3. `@Version`이 있는데도 덮어쓰기가 일어난다

- **현상**: 편집 화면 A·B에서 저장했는데 충돌 오류 없이 마지막 저장만 남는다.
- **원인**
  - 저장 API가 매번 DB에서 엔티티를 **새로 읽고** 요청 값을 복사한다. 새로 읽은 엔티티의 버전은 항상 최신이라 검증이 무의미하다.
  - 화면이 들고 있던 버전을 요청에 담아 비교해야 한다.
- **대처**: 클라이언트가 받은 `version`(또는 ETag)을 요청에 싣고, 서버가 그 값과 비교한다. JPA에서는 받은 버전이 다르면 직접 예외를 던지거나 detached 엔티티를 `merge`해 Hibernate가 비교하게 한다.
- 관련: `@OptimisticLock(excluded = true)`로 뺀 필드는 바뀌어도 버전을 올리지 않는다. 그래서 그 필드의 변경은 다른 필드를 고치는 동시 UPDATE에도 덮어써질 수 있다(Hibernate 가이드 예 458: `callCount` 증가가 전화번호 UPDATE에 덮어써짐).

### 4. 자식만 고쳐 루트 버전이 안 올라 불변식이 깨진다

- **현상**: 주문 항목을 두 사용자가 동시에 추가해 "주문 총액 한도" 불변식이 깨졌다. 충돌 오류는 없었다.
- **원인**: 각자 **다른 자식 행**을 추가했다. 버전은 행마다라서 충돌로 보지 않는다.
- **대처**: 자식을 바꿀 때 루트 버전도 올린다(`OPTIMISTIC_FORCE_INCREMENT`로 루트 잠금). 자세한 것은 52번 `offline-concurrency-patterns`.

## 핵심 문장

- OCC는 락 없이 진행하고 커밋 직전에 "그사이 누가 내가 읽은 것을 바꿨나"를 검증한다. 충돌하면 버리고 다시 한다.
- 기본 T/O는 객체마다 R-TS·W-TS를 두고 타임스탬프 순서를 어기는 연산을 중단시킨다. 기다리지 않으니 교착은 없지만 긴 트랜잭션이 굶는다.
- 앱의 OCC는 버전 컬럼과 `UPDATE ... WHERE version = ?` 한 문장이다. 영향받은 행이 0이면 충돌이다(행이 지워진 경우도 0이니 필요하면 구분한다).
- OCC는 충돌이 드물 때만 싸다. 같은 행에 쓰기가 몰리면 재시도가 폭증하므로 원자 UPDATE나 비관적 락으로 바꾼다.
- 버전 검증은 "클라이언트가 처음 읽은 버전"과 비교해야 의미가 있다.

## 관련 주제·근거

- 선행
  - database [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md) — lost update의 정의.
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md) — 비관적 방식과의 비교
  - [16-mvcc](../16-mvcc/2-summary.md) — RR에서의 UPDATE 동작 차이
- 후속·연결
  - [18-app-level-concurrency-patterns](../18-app-level-concurrency-patterns/2-summary.md) — 조건부 UPDATE·`FOR UPDATE`·upsert
  - database [52-offline-concurrency-patterns](../52-offline-concurrency-patterns/2-summary.md)(여러 요청에 걸친 버전·aggregate 버전)
  - api-design `11-concurrency-control-in-apis`(ETag·`If-Match`·412) — 미작성, [api-design/curriculum](../../api-design/curriculum.md)
  - [ops-patterns/14-logical-clock](../../ops-patterns/14-logical-clock/2-summary.md) — 논리 시계
  - [api-design/03-stock-deduct](../../api-design/03-stock-deduct/2-summary.md) — 재고 차감의 방식 비교
- 논문·강의
  - H. T. Kung, J. T. Robinson, "On Optimistic Methods for Concurrency Control", ACM TODS 6(2), 1981 — 읽기·검증·쓰기 단계, 검증 조건 (1)~(3)
  - CMU 15-445/645 Fall 2024 Lecture #18 Timestamp Ordering Concurrency Control(OCC 세 단계, 전방·후방 검증, 약점) <https://15445.courses.cs.cmu.edu/fall2024/notes/18-timestampordering.pdf> · Fall 2023 Lecture #17 노트(Basic T/O, R-TS·W-TS, Thomas Write Rule) <https://15445.courses.cs.cmu.edu/fall2023/notes/17-timestampordering.pdf>
- PostgreSQL 17: 13.2.1 Read Committed — 동시 갱신 뒤 WHERE 재평가 <https://www.postgresql.org/docs/17/transaction-iso.html>
- Hibernate ORM 6.6 User Guide — 11.1 Optimistic(`@Version` 허용 타입, 버전 번호 vs 타임스탬프, 예 458 `@OptimisticLock(excluded)`), 표 LockModeType(`OPTIMISTIC_FORCE_INCREMENT`) <https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
- Hibernate ORM 6.6 소스 `hibernate-core/src/main/java/org/hibernate/StaleObjectStateException.java`(예외 메시지) · 가이드 HQL `update versioned`(벌크 UPDATE는 기본적으로 버전 불변) · 6.6 Javadoc `org.hibernate.stat.Statistics#getOptimisticFailureCount` <https://docs.hibernate.org/orm/6.6/javadocs/org/hibernate/stat/Statistics.html>
- Spring Framework 6.2: `spring-orm/.../vendor/HibernateJpaDialect.java`(StaleObjectStateException → `ObjectOptimisticLockingFailureException`), `EntityManagerFactoryUtils.java`(`OptimisticLockException` → `JpaOptimisticLockingFailureException`) <https://github.com/spring-projects/spring-framework>
- 로컬 재현(PostgreSQL 17.11): 한 행 차감을 1·8 세션으로 — 버전 조건 UPDATE(재시도 0 vs 6605, 0.9 s vs 17.4 s), 검증 없는 덮어쓰기(1600 중 202만 반영), 원자 UPDATE(1600 정확)
