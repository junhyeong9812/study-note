# database/52-offline-concurrency-patterns — 정답

## 정답

### 1. ACID인데 lost update

```text
  A: [Tx1: 읽기]  ........ 편집 10분 ........  [Tx3: 쓰기(A 값)]
  B:      [Tx: 읽기] ... 편집 ... [Tx2: 쓰기(B 값)]
  → Tx3이 Tx2의 결과를 모른 채 덮는다
```

- 각 DB 트랜잭션은 한 요청 안에서 끝났다. 사람의 작업(비즈니스 트랜잭션)은 여러 트랜잭션에 걸친다. 그 사이는 DB가 보호하지 않는다.
- 트랜잭션을 편집 내내 열어 두면 안 되는 이유
  - 락과 커넥션을 사람의 시간(분 단위) 동안 쥔다.
  - 사용자가 창을 닫으면 끝나지 않는다.
  - 트랜잭션 시스템은 긴 트랜잭션에 맞지 않는다(PoEAA Pessimistic Offline Lock 요약).

### 2. 버전 조건 UPDATE

- B: `UPDATE 1`(version 0 → 1). A: `UPDATE 0`(version이 이미 1).
- 최종 상태: body = B의 값, version 1(로컬 재현, PostgreSQL 17.11).
- A의 앱은 영향 행 수 0을 충돌로 해석해 사용자에게 알린다. 행이 지워져도 0이므로, 필요하면 존재 여부를 다시 확인해 "삭제됨"과 구분한다.
- SELECT로 버전을 확인하고 UPDATE를 따로 하면, 두 문장 사이에 다른 저장이 끼어들 수 있다. 그러면 그 틈으로 다시 lost update가 난다. 검사와 쓰기는 **한 문장**(DB 행 위의 compare-and-swap)이어야 한다.

### 3. `@Version`이 있는데 lost update

- 저장 요청에서 엔티티를 **새로 읽었다**. 그러면 비교 기준 버전은 "방금 읽은 최신 버전"이다. 그래서 `WHERE version = ?`가 항상 참이고, 폼 값이 남의 수정을 덮는다.
- 비교해야 하는 것은 **사용자가 편집 화면을 열 때 읽은 버전**이다.
- 고침
  - 편집 화면에 버전을 hidden 필드나 `ETag`로 보낸다.
  - 저장 때 `if (entity.getVersion() != form.version()) throw …`로 거부한다. 앱이 버전 값을 직접 바꾸지 않는다(Jakarta Persistence 3.1 3.4.2).
  - 또는 detached 엔티티를 `merge`하면 공급자가 stale 여부를 검사한다(같은 절).
  - 커밋 시점의 `WHERE version = ?`는 비교와 커밋 사이의 경쟁을 잡는다.

### 4. 락 테이블

```sql
CREATE TABLE edit_lock(resource text PRIMARY KEY, owner text NOT NULL, expires_at timestamptz NOT NULL);

-- 획득
INSERT INTO edit_lock VALUES ($1, $2, now() + interval '10 minutes')
ON CONFLICT (resource) DO UPDATE SET owner = EXCLUDED.owner, expires_at = EXCLUDED.expires_at
 WHERE edit_lock.expires_at < now() OR edit_lock.owner = EXCLUDED.owner
RETURNING owner;             -- 1행 = 획득, 0행 = 남이 쥐고 있음
                             -- now() = 트랜잭션 시작 시각. 짧은 단독 트랜잭션으로 실행한다

-- 해제 (내 것만)
DELETE FROM edit_lock WHERE resource = $1 AND owner = $2;
```

- 한 명만 이기는 근거
  - `resource` PK가 자원당 한 행을 보장한다.
  - `ON CONFLICT DO UPDATE`는 동시성이 높아도 INSERT나 UPDATE 중 하나를 원자적으로 보장한다(PostgreSQL 17 INSERT 문서).
- 로컬 재현: alice 획득 → bob 0행 → 만료 후 bob 획득 → alice 해제 `DELETE 0` → bob 해제 `DELETE 1`.

### 5. 락 해제 누락

- 원인
  - 해제는 저장·취소 요청에서만 일어난다. 창 닫기·세션 만료·네트워크 끊김에서는 요청이 오지 않는다.
  - 만료 없는 락이 영원히 남는다.
- 대처
  - `expires_at`(TTL)을 두고 획득 조건에 "만료되면 뺏는다"를 넣는다.
  - 편집 중에는 heartbeat로 연장한다.
  - 관리자 강제 해제와 이력을 둔다.
- 원래 주인이 저장하면: 문서 쓰기와 같은 트랜잭션에서 락 행을 `FOR UPDATE`로 잠그고 `owner = 나`이고 만료 전인지 확인한다. 아니면 거부한다. 따로 조회하면 그 틈에 남이 락을 가져간다. 락을 뺏긴 사이 남이 저장했을 수 있으므로 **버전 검사(낙관적)도 함께** 둔다. 버전 검사만으로는 "뺏겼지만 상대가 아직 저장 안 함"을 못 잡는다.

### 6. 자식 버전만으로는 aggregate 불변식이 깨진다

- 결과
  - A·B 모두 "합계 8 → 8−4+6 = 10 ≤ 10"으로 검사를 통과한다.
  - 줄이 서로 달라 줄 버전도 충돌하지 않는다.
  - 둘 다 커밋되어 **합계 12**. 로컬 재현(PostgreSQL 17.11)에서 `sum(qty) = 12`.
- Coarse-Grained Lock
  - 줄을 바꾸는 모든 경로가 먼저 루트 버전을 올린다: `UPDATE purchase_order SET version = version + 1 WHERE id = 10 AND version = :read`.
  - 재현에서 두 번째 요청이 `UPDATE 0`으로 막혔고, 합계 10·루트 version 1이 유지되었다.
- JPA: `em.lock(order, LockModeType.OPTIMISTIC_FORCE_INCREMENT)`로 루트 버전을 강제로 올린다(3.4.4.1).
- 부모 버전이 오르지 않는 이유: 버전 검사 대상은 그 엔티티의 비관계 필드와 **그 엔티티가 소유한 관계**뿐이다(3.4.2). `mappedBy` 컬렉션은 자식이 소유한다. 줄의 `qty`는 줄 엔티티의 필드다.

### 7. Implicit Lock

- 막으려는 것: 락 코드 **한 줄 누락**이다. 어디서든 잠글 수 있는 대상은 모든 곳에서 잠가야 한다. 한 경로라도 빠지면 전체 방식이 무의미해진다(PoEAA Implicit Lock).
- 구현 형태
  - JPA `@Version`: 공급자가 관리 엔티티의 UPDATE에 버전 조건을 자동으로 붙인다. JPQL·Criteria 벌크 UPDATE는 예외다. 버전 검사를 건너뛰므로 직접 써야 한다(Jakarta Persistence 3.1 4.10).
  - 저장소: aggregate 루트 단위 저장소만 두고, `save(root, expectedVersion)`만 공개한다. 루트 버전 증가를 공통 코드가 한다.
  - HTTP API: 공통 필터가 수정 요청에 `If-Match`를 요구하고, 없으면 `428`으로 거부한다.

### 8. HTTP 계약

- `GET` 응답에 `ETag: "v7"`을 준다.
- 수정 요청은 `If-Match: "v7"`을 보낸다. 현재 태그가 다르면 서버는 메서드를 수행하면 안 된다(MUST NOT). 보통 `412 Precondition Failed`로 알린다(RFC 9110 13.1.1, 15.5.13). 같은 변경이 이미 적용된 것으로 보이면 2xx도 허용된다(MAY). RFC 9110은 `If-Match`를 lost update 방지 수단으로 설명한다.
- `If-Match` 없는 수정을 거부하려면 `428 Precondition Required`(RFC 6585 3절).

### 9. 재시도와 advisory lock

- DB 교착은 **시스템이 만든** 충돌이다. 희생자 트랜잭션을 처음부터 다시 실행하면 같은 의도가 올바르게 반영된다.
- 오프라인 충돌은 **사람이 옛 화면을 보고 내린 결정**과 남의 수정이 부딪힌 것이다. 자동 재시도는 "다시 읽기 → 옛 폼 값 덮어쓰기"가 되어 버전 검사를 끈 것과 같다. 그래서 사용자에게 돌려보내 최신 값을 보고 다시 결정하게 한다.
- 세션 수준 advisory lock은 명시 해제나 세션 종료까지 유지된다. 같은 세션의 추가 요청은 항상 성공한다(PostgreSQL 17 13.3.5).
  - 커넥션 풀에서는 세션 ≠ 사용자다. 그래서 다른 사용자의 요청이 같은 커넥션을 받으면 그 락을 이미 쥔 것처럼 통과한다.
  - 해제 요청이 다른 커넥션으로 가면 풀리지 않는다.
  - 오프라인 락은 테이블(소유자·만료)로 만든다.
