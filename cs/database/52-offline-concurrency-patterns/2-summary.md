# database/52-offline-concurrency-patterns — 여러 요청에 걸친 비즈니스 트랜잭션의 동시성 — 정리 (힌트)

## 해결하는 문제

DB 트랜잭션은 **한 요청 안**에서 끝난다. 사람의 작업은 **여러 요청**에 걸친다.

```text
  시간 →
  A:  GET /docs/1 (편집 화면 열기)  ....... 10분 동안 편집 .......  PUT /docs/1 (저장)
        [DB 트랜잭션 1: 읽고 끝]                                    [DB 트랜잭션 3: 쓰고 끝]
  B:          GET /docs/1  ... 2분 편집 ...  PUT /docs/1
                [DB 트랜잭션]                  [DB 트랜잭션 2]

  결과: B의 수정이 A의 저장에 덮여 사라진다 (lost update)
       세 DB 트랜잭션은 각각 완벽하게 ACID였다. 그런데도 보호받지 못했다.
```

- *비즈니스 트랜잭션*: 사용자 입장에서 하나인 작업(편집 화면 열기 → 저장). 여러 *시스템 트랜잭션*(DB 트랜잭션)으로 쪼개진다.
- *오프라인 동시성(offline concurrency)*: 비즈니스 트랜잭션 사이의 충돌을 관리하는 일이다. "오프라인"은 DB 트랜잭션 밖이라는 뜻이다(PoEAA 16장).
- DB 트랜잭션을 사람이 편집하는 10분 동안 열어 둘 수는 없다. 락을 오래 쥐고, 커넥션을 잡고, 사용자가 창을 닫으면 끝나지 않는다.

쉬운 예: 공유 문서의 "체크아웃"이다.
- 도서관 방식: 한 사람이 빌려 가면 다른 사람은 못 빌린다(비관적).
- 위키 방식: 아무나 편집하되, 저장할 때 "그사이 누가 고쳤나"를 보고 충돌을 알린다(낙관적).

똑같은 구조다.\
DB가 대신 막아 주지 못하는 구간을 애플리케이션이 버전 번호나 락 테이블로 지킨다.

실무 예:
- 관리자 두 명이 같은 상품 정보를 편집한다.
- 주문서의 줄을 두 사람이 각자 고친다. 주문 전체의 한도 규칙이 깨진다.
- REST API의 `ETag` + `If-Match` → `412 Precondition Failed`(RFC 9110)는 같은 문제를 HTTP 층에서 푼다.

## 동작·원리

### 1. Optimistic Offline Lock — 버전 번호로 저장 시점에 충돌 검출

```text
  doc(id=1, body, version=0)

  A: 읽기 → version 0 을 화면(폼)에 숨겨 둔다
  B: 읽기 → version 0
  B: UPDATE doc SET body='B', version=version+1 WHERE id=1 AND version=0   → UPDATE 1  (version 1)
  A: UPDATE doc SET body='A', version=version+1 WHERE id=1 AND version=0   → UPDATE 0  ← 충돌!
     영향 행 0 = "그사이 누가 고쳤다(또는 지웠다)" → A에게 알리고 다시 읽게 한다
```

- 로컬 재현(예시, PostgreSQL 17.11): 위 두 UPDATE가 각각 `UPDATE 1`, `UPDATE 0`이었고 본문은 `B의 본문`, version 1로 남았다.
- 핵심은 **검사와 쓰기가 한 문장**이라는 점이다. `WHERE version = :읽은버전`을 붙인 UPDATE는 원자적이다. "SELECT로 버전 확인 → UPDATE"로 나누면 그 틈으로 다시 lost update가 들어온다.
- 버전은 **사용자가 읽은 시점의 값**이어야 한다. 저장 요청에서 엔티티를 새로 읽어 그 버전으로 비교하면 항상 통과한다(장애 시나리오 1).
- PoEAA: 충돌 가능성이 낮다고 가정한다. 여러 사람이 동시에 일할 수 있다. 대신 패자는 **작업을 다 한 뒤에** 실패를 안다.

### 2. Pessimistic Offline Lock — 시작할 때 락을 잡는다

```text
  edit_lock(resource PK, owner, expires_at)

  alice: 획득 시도 → 행 없음 → INSERT                    → 성공 (owner alice)
  bob:   획득 시도 → alice 소유, 만료 전                  → 실패 ("alice가 편집 중")
  (10분 경과 또는 만료)
  bob:   획득 시도 → 만료됨 → 소유자를 bob으로 교체        → 성공
  alice: 저장·해제 시도 → owner가 bob                     → 실패 (락을 잃었다)
```

```sql
-- PostgreSQL 17: 획득 = 없으면 넣고, 만료됐거나 내 것이면 갱신 (한 문장, 원자적)
INSERT INTO edit_lock VALUES ($1, $2, now() + interval '10 minutes')
ON CONFLICT (resource) DO UPDATE
   SET owner = EXCLUDED.owner, expires_at = EXCLUDED.expires_at
 WHERE edit_lock.expires_at < now() OR edit_lock.owner = EXCLUDED.owner
RETURNING owner;                        -- 행이 돌아오면 획득, 0행이면 남이 쥐고 있다

-- 해제 = 내 것만 지운다
DELETE FROM edit_lock WHERE resource = $1 AND owner = $2;
```

- 로컬 재현(PostgreSQL 17.11): alice 획득 → bob `0 rows` → 만료 후 bob 획득 → alice 해제 `DELETE 0` → bob 해제 `DELETE 1`.
- `now()`는 트랜잭션 **시작** 시각이다(PostgreSQL 17 9.9.5). 획득 문장은 짧은 단독 트랜잭션으로 실행한다. 긴 트랜잭션 안에서 부르면 이미 지난 시각으로 만료를 판정하므로 `clock_timestamp()`를 쓴다.
- `ON CONFLICT DO UPDATE`는 동시성이 높아도 INSERT나 UPDATE 중 하나의 결과를 원자적으로 보장한다(PostgreSQL 17 INSERT 문서). 그래서 두 사람이 동시에 획득해도 한 명만 이긴다.
- PoEAA: 충돌 가능성이 높거나 충돌 비용이 클 때 쓴다. 비즈니스 트랜잭션을 시작하면 대개 끝까지 간다. 대신 동시성이 줄고 **락 관리**(해제·만료·교착)가 생긴다.
- **만료(TTL)**가 필수다. 사용자는 창을 닫고 사라진다. 해제 요청은 오지 않을 수 있다.
  - *TTL(time to live)*: 락이 스스로 무효가 되는 시각. 위 `expires_at`.
- 만료된 락을 뺏긴 원래 주인은 저장 전에 **자기 락이 아직 유효한지** 다시 확인해야 한다. 확인은 문서 쓰기와 **같은 DB 트랜잭션**에서 락 행을 잠그며 한다(`SELECT … FROM edit_lock WHERE resource = $1 AND owner = $2 AND expires_at > now() FOR UPDATE` → 0행이면 거부). 따로 조회하면 그 틈에 남이 락을 가져간다.
- 버전 검사만으로는 부족하다. bob이 락을 가져갔지만 아직 저장하지 않았다면 버전은 그대로라 alice의 저장이 통과한다. 그래서 소유자 확인과 버전 검사(낙관적)를 **둘 다** 둔다.

### 3. Coarse-Grained Lock — 묶음 전체에 락 하나

```text
  Order(id=10, version)  ← aggregate 루트. 불변식: 줄 수량 합계 ≤ 10
    ├─ Line 1 (qty 4)
    └─ Line 2 (qty 4)

  줄마다 버전만 있을 때                         루트 버전 하나로 묶을 때
  A: Line1 4→6  (합계 8 읽음, 8-4+6=10 OK)       A: Order v0→v1, Line1 4→6  커밋
  B: Line2 4→6  (합계 8 읽음, 8-4+6=10 OK)       B: Order v0→v1 시도 → UPDATE 0 → 충돌
  둘 다 성공 → 합계 12  ← 불변식 파괴             합계 10 유지
```

- 로컬 재현(PostgreSQL 17.11): 줄 버전만 쓴 경우 두 UPDATE가 모두 성공해 합계 12가 되었다. 루트 버전을 먼저 올리게 하자 두 번째가 `UPDATE 0`으로 막혔고 합계 10, 루트 version 1로 남았다.
- PoEAA: 관련 객체 묶음을 락 **하나**로 잠근다. 묶음 전체를 로드하지 않고도 잠글 수 있다.
- 묶음의 경계 = DDD의 *aggregate*(일관성 경계)다. 불변식이 묶음 전체에 걸려 있으면 락도 묶음 전체에 걸어야 한다. aggregate 설계는 domain-modeling `05-aggregates-and-invariants`에서 다룬다.
- JPA에서 조심할 점
  - 버전 검사에는 그 엔티티의 비관계 필드와 **그 엔티티가 소유한 관계**만 들어간다(Jakarta Persistence 3.1 3.4.2).
  - `@OneToMany(mappedBy = …)`는 부모가 소유한 관계가 아니다. 그래서 자식 줄만 바꾸면 부모 버전이 오르지 않는다.
  - 루트 버전을 강제로 올리려면 `LockModeType.OPTIMISTIC_FORCE_INCREMENT`로 루트를 잠근다(3.4.4.1).

### 4. Implicit Lock — 락을 개발자 손에 맡기지 않는다

- PoEAA: 어떤 락 방식이든 **빈틈이 없어야** 한다. 한 곳에서 락 코드 한 줄을 빠뜨리면 전체가 무너진다. 그래서 프레임워크·레이어 상위 타입이 락을 대신 잡게 한다.
- "어딘가에서 잠글 수 있는 대상이면 모든 곳에서 잠가야 한다"(PoEAA Implicit Lock 요약).
- 예
  - JPA `@Version`: 관리 엔티티를 쓸 때 공급자가 자동으로 `WHERE version = ?`를 붙인다. 단 JPQL·Criteria 벌크 UPDATE는 버전 검사를 건너뛴다. 버전 조건과 증가를 직접 써야 한다(Jakarta Persistence 3.1 4.10).
  - 저장소(repository) 기반 클래스의 `save(entity, expectedVersion)`만 공개한다.
  - 편집 API의 공통 필터가 `If-Match`를 요구한다(없으면 `428 Precondition Required`, RFC 6585).

## 쓰이는 자료구조·알고리즘

- **버전 번호 비교(compare-and-swap)**: `UPDATE … WHERE version = v` + `version = v + 1`은 DB 행 위의 CAS다. 영향 행 수 1 = 성공, 0 = 실패다. 낙관적 동시성의 기본형은 [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md)에서 다룬다.
- **락 테이블(소유자·만료 TTL)**: 키 = 자원 id, 값 = (소유자, 만료 시각)인 사전이다. 획득은 "없거나 만료됐거나 내 것이면 쓰기"의 원자적 조건부 쓰기다. PK 유일 제약이 "한 자원에 한 소유자"를 보장한다.
- **aggregate = 락 단위 트리**: 루트 하나에 버전을 두면, 트리 전체의 변경이 루트의 CAS 하나로 직렬화된다.
- **리스(lease)**: 만료가 있는 락이다. 주인이 사라져도 시간이 지나면 풀린다. 대신 주인은 자기 리스가 아직 유효한지 확인해야 한다. 분산 락과 같은 문제다.

## 적용 — 풀어나가는 법

### 1. 고르는 법

```text
  충돌 드묾, 재작업 비용 작음 (상품 설명 편집)          → Optimistic Offline Lock (기본값)
  충돌 잦음, 재작업 비용 큼 (긴 심사 양식, 계약서)        → Pessimistic Offline Lock + TTL + 낙관적 검사 병행
  불변식이 여러 행에 걸림 (주문 + 줄, 고객 + 주소들)     → Coarse-Grained Lock (루트 버전)
  위 셋을 개발자마다 다르게 쓰고 있음                   → Implicit Lock (프레임워크·공통 코드로 강제)
```

### 2. JPA + Spring — 낙관적 오프라인 락

```java
@Entity
public class Doc {
    @Id Long id;
    String body;
    @Version int version;                         // 공급자가 WHERE version = ? 를 붙인다
}

// 1) 편집 화면: 버전을 폼(또는 ETag)에 실어 보낸다
record DocForm(String body, int version) {}

// 2) 저장: "사용자가 읽은 버전"과 현재 버전을 비교한다
@Transactional
public void save(long id, DocForm form) {
    Doc doc = em.find(Doc.class, id);
    if (doc.getVersion() != form.version()) {     // 앱이 version 값을 직접 바꾸지 않는다(명세 3.4.2) → 비교해서 거부
        throw new OptimisticLockException(doc);
    }
    doc.setBody(form.body());                     // 커밋 시 UPDATE … WHERE id=? AND version=? (그 사이 경쟁도 여기서 잡힌다)
}
```

- **공급자가** 이 예외를 던질 때는 트랜잭션을 롤백 대상으로 표시한다(Jakarta Persistence 3.1 3.4.5). 위처럼 앱이 직접 던지면 공급자가 표시하지 않는다. 예외가 `@Transactional` 밖으로 나가면 Spring 기본 규칙(RuntimeException → 롤백)으로 롤백된다. 안에서 잡아 삼키면 롤백되지 않는다.
- 쓰기가 커밋 때로 미뤄지면 예외도 커밋 때 나온다. 서비스 안에서 잡아 처리하려면 `flush()`로 쓰기를 앞당긴다(같은 절).
- Spring의 JPA 예외 번역(저장소 프록시·트랜잭션 커밋)을 거치면 JPA `OptimisticLockException`은 `JpaOptimisticLockingFailureException`(→ `ObjectOptimisticLockingFailureException` → `OptimisticLockingFailureException`의 하위)으로 바뀐다(`EntityManagerFactoryUtils`). 번역 경로를 거치지 않고 서비스에서 직접 던진 JPA 예외는 그대로 올라온다. 그래서 잡는 쪽(예: 컨트롤러 예외 처리기)은 Spring `OptimisticLockingFailureException`과 JPA `OptimisticLockException`을 둘 다 잡는다. 또는 서비스에서 처음부터 Spring 예외를 던진다. API는 이것을 `409 Conflict`나 `412 Precondition Failed`로 번역한다.

### 3. HTTP — 같은 패턴을 API 계약으로

```text
  GET /docs/1            → 200, ETag: "v7"
  PUT /docs/1            If-Match: "v7"
     서버: 현재 버전이 v7이면 저장 → 200, ETag: "v8"
           아니면                → 412 Precondition Failed (보통의 선택. 같은 변경이 이미 적용돼 있으면 2xx도 허용된다)
  PUT /docs/1 (If-Match 없음) → 428 Precondition Required (조건부 요청을 강제할 때, RFC 6585)
```

- RFC 9110은 `If-Match`를 "lost update" 문제를 막는 수단으로 설명한다(13.1.1). API 설계 쪽은 api-design `11-concurrency-control-in-apis` — 미작성, [api-design/curriculum](../../api-design/curriculum.md).

### 4. 진단

```sql
-- 낙관적 충돌 빈도: 앱 로그의 OptimisticLock 예외 수 / 저장 수
-- 비관적 락 현황
SELECT resource, owner, expires_at, expires_at < now() AS expired FROM edit_lock ORDER BY expires_at;
-- 만료된 락 청소 (획득 쿼리가 만료 락을 덮어쓰므로 필수는 아니다. 표 크기 관리용)
DELETE FROM edit_lock WHERE expires_at < now() - interval '1 day';
```

- DB 락과 헷갈리지 않는다. `pg_locks`·`performance_schema.data_locks`에는 오프라인 락이 나오지 않는다. 오프라인 락은 **애플리케이션 테이블의 행**이다.
- PostgreSQL 세션 수준 advisory lock은 세션이 끝나거나 명시 해제할 때까지 유지된다(PostgreSQL 17 13.3.5). 커넥션 풀에서는 세션 ≠ 사용자다. 그래서 요청 사이의 오프라인 락으로 쓰면 다른 사용자의 요청이 같은 커넥션으로 그 락을 "이미 쥔 상태"가 된다. 오프라인 락은 테이블로 만든다.

## 장애 시나리오와 대처

### 1. 편집 화면을 오래 연 사이 다른 사용자가 저장 → lost update

- **현상**: 관리자 B가 고친 가격이 몇 분 뒤 원래대로 돌아가 있다. 누구도 오류를 보지 못했다.
- **보이는 형태**: 오류 없음. 감사 로그에 A의 저장이 B의 저장 **뒤에** 있고, A의 값이 B가 읽기 전 값이다.
- **원인**
  - 세 DB 트랜잭션은 각각 정상이었다. 비즈니스 트랜잭션 사이에는 보호가 없었다.
  - 흔한 변형: `@Version`을 달았지만 저장 요청에서 엔티티를 **새로 읽고** 폼 값을 덮어썼다. 비교되는 버전이 "방금 읽은 버전"이라 충돌이 절대 안 난다.
- **대처**
  - 사용자가 읽은 버전을 클라이언트에 보내고(폼 hidden, `ETag`), 저장 때 그 값과 비교한다.
  - 영향 행 수 0(행이 지워졌을 수도 있으니 필요하면 존재를 다시 확인) 또는 `OptimisticLockException` → 사용자에게 "다른 사람이 먼저 저장했습니다"와 최신 값을 보여 준다. 자동 재시도는 **하지 않는다**. 재시도는 상대의 수정을 다시 덮는다.

### 2. 비관적 오프라인 락 해제 누락 → "다른 사용자가 편집 중" 영구 표시

- **현상**: 퇴근한 직원의 이름으로 "편집 중" 표시가 다음 날까지 남아 아무도 문서를 못 연다.
- **보이는 형태**: `edit_lock`에 오래된 행. 획득 쿼리가 계속 `0 rows`.
- **원인**
  - 해제는 사용자가 "저장" 또는 "취소"를 눌러야 일어난다. 창 닫기·세션 만료·네트워크 끊김에서는 해제 요청이 오지 않는다.
  - 만료 없는 락 설계가 문제다.
- **대처**
  - `expires_at`을 두고 획득 조건에 "만료됐으면 뺏는다"를 넣는다(동작·원리 2).
  - 편집 중이면 주기적으로 연장(heartbeat)한다.
  - 관리자용 강제 해제 기능과, 해제 이력 로그를 둔다.
  - 락을 뺏긴 원래 주인의 저장은 거부한다. 같은 트랜잭션에서 락 행을 `FOR UPDATE`로 잠가 `owner`·만료를 확인하고, 버전 검사도 함께 둔다(동작·원리 2).

### 3. 자식만 수정해 루트 버전이 안 올라 aggregate 불변식 파괴

- **현상**: "주문당 수량 합계 ≤ 10" 규칙이 있는데 합계 12인 주문이 생겼다.
- **보이는 형태** (로컬 재현, PostgreSQL 17.11): 두 요청이 서로 다른 줄을 각자 고쳤다. 각자 줄 버전 검사는 통과했고, 둘 다 커밋되어 `sum(qty) = 12`.
- **원인**
  - 락(버전)의 단위가 줄인데, 불변식의 단위는 주문 전체다.
  - JPA에서는 부모의 `mappedBy` 컬렉션이 부모 버전 검사에 들어가지 않는다(3.4.2). 그래서 줄만 바꾸면 주문 버전은 그대로다.
- **대처**
  - Coarse-Grained Lock: 줄을 바꾸는 모든 경로가 루트 버전을 올리게 한다.
  - JPA: `em.lock(order, LockModeType.OPTIMISTIC_FORCE_INCREMENT)`.
  - SQL: 먼저 `UPDATE purchase_order SET version = version + 1 WHERE id = ? AND version = ?`.
  - 로컬 재현에서 두 번째 요청이 `UPDATE 0`으로 막혔다.
  - 줄을 aggregate 루트를 통해서만 수정하게 저장소를 루트 단위로 둔다(Implicit Lock).

### 4. 자동 재시도가 충돌을 덮어쓴다

- **현상**: 낙관적 락 예외를 공통 재시도 로직(예: 3회 재시도)이 잡아, 결국 A의 저장이 성공한다. B의 수정은 사라진다.
- **보이는 형태**: 로그에 `OptimisticLockingFailureException` 뒤 재시도 성공. 사용자에게는 오류가 보이지 않는다.
- **원인**
  - 재시도가 "다시 읽기 → 사용자의 옛 폼 값 덮어쓰기"를 한다. 그러면 사실상 버전 검사를 끈 것과 같다.
  - DB 교착(40P01·1213)처럼 **시스템이 만든** 충돌은 재시도해도 되지만, 오프라인 충돌은 **사람의 판단**이 필요한 충돌이다.
- **대처**
  - 오프라인 락 예외는 재시도 대상에서 뺀다. 사용자에게 돌려보낸다.
  - 자동 병합이 안전한 경우(서로 다른 필드만 바뀜)에만 필드 단위 병합을 설계해서 쓴다.

## 핵심 문장

- DB 트랜잭션은 한 요청 안에서 끝나므로, 여러 요청에 걸친 비즈니스 트랜잭션은 애플리케이션이 따로 보호해야 한다.
- 낙관적 오프라인 락은 `UPDATE … WHERE version = 사용자가 읽은 버전`의 영향 행 수로 충돌을 잡는다. 비교 대상은 방금 읽은 버전이 아니라 사용자가 읽은 버전이다.
- 비관적 오프라인 락은 소유자·만료가 있는 락 테이블이다. 해제 요청은 오지 않을 수 있으므로 TTL이 필수다.
- 불변식이 aggregate 전체에 걸리면 락도 루트 하나에 건다(Coarse-Grained Lock). 자식만 바뀌어도 루트 버전을 올린다.
- 락은 한 곳만 빠져도 무너지므로 프레임워크·공통 코드가 대신 잡게 한다(Implicit Lock). 오프라인 충돌은 자동 재시도하지 않는다.

## 관련 주제·근거

- 선행
  - [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md) — 낙관적 동시성·버전 컬럼
  - domain-modeling `05-aggregates-and-invariants` — 일관성 경계. 미작성, [domain-modeling/curriculum](../../domain-modeling/curriculum.md)
- 연결
  - api-design `11-concurrency-control-in-apis` — ETag·`If-Match`. 미작성, [api-design/curriculum](../../api-design/curriculum.md)
  - [18-app-level-concurrency-patterns](../18-app-level-concurrency-patterns/2-summary.md) — 한 트랜잭션 안의 `FOR UPDATE`·조건부 UPDATE
  - [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md) — lost update의 DB 안 버전
  - [domain-modeling/advanced/12-seat-hold](../../domain-modeling/advanced/12-seat-hold/2-summary.md) — 만료가 있는 좌석 홀드(리스)
  - [api-design/03-stock-deduct](../../api-design/03-stock-deduct/2-summary.md) — 재고 차감의 동시성
- 책·명세·RFC
  - Martin Fowler, 『Patterns of Enterprise Application Architecture』(2002), 16장 Offline Concurrency Patterns — Optimistic Offline Lock, Pessimistic Offline Lock, Coarse-Grained Lock, Implicit Lock. 온라인 카탈로그 요약 <https://martinfowler.com/eaaCatalog/> (본문은 카탈로그 요약 경유로만 확인)
  - Jakarta Persistence 3.1 — 3.4.2 Version Attributes(버전 검사 대상 = 비관계 필드 + 소유한 관계, 앱은 버전을 수정하지 않는다), 3.4.4.1 `OPTIMISTIC_FORCE_INCREMENT`, 3.4.5 `OptimisticLockException`(롤백 표시, flush로 앞당김) <https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html>
  - RFC 9110 HTTP Semantics — 8.8.3 ETag, 13.1.1 If-Match("lost update" 방지), 15.5.13 412 Precondition Failed <https://www.rfc-editor.org/rfc/rfc9110>
  - RFC 6585 — 3. 428 Precondition Required <https://www.rfc-editor.org/rfc/rfc6585>
  - Jakarta Persistence 3.1 4.10 Bulk Update and Delete(벌크 UPDATE는 낙관적 락 검사를 건너뜀)
  - RFC 9110 13.1.1 — 조건 거짓이면 메서드를 수행하지 않는다(MUST NOT). 412로 알릴 수 있고(MAY), 같은 변경이 이미 적용된 것으로 보이면 2xx도 된다(MAY)
  - PostgreSQL 17 9.9.5 Current Date/Time(`now()` = 트랜잭션 시작 시각, `clock_timestamp()` = 실제 현재 시각)
  - PostgreSQL 17 INSERT(`ON CONFLICT DO UPDATE`의 원자적 결과 보장) <https://www.postgresql.org/docs/17/sql-insert.html> · 13.3.5 Advisory Locks(세션 수준 락의 수명) <https://www.postgresql.org/docs/17/explicit-locking.html>
  - Spring Framework 소스 — `EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible`(`OptimisticLockException` → `JpaOptimisticLockingFailureException`), `JpaOptimisticLockingFailureException extends ObjectOptimisticLockingFailureException extends OptimisticLockingFailureException`
- 로컬 재현(PostgreSQL 17.11): 버전 조건 UPDATE의 `UPDATE 1`/`UPDATE 0`, 락 테이블 획득·거부·만료 후 탈취·소유자 한정 해제, 줄 버전만으로 합계 12(불변식 파괴)와 루트 버전으로 차단
