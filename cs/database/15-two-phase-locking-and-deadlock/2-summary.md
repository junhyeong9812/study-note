# database/15-two-phase-locking-and-deadlock — 2단계 락킹, 락 모드, DB 교착 탐지 — 정리 (힌트)

## 해결하는 문제

트랜잭션 두 개가 같은 데이터를 동시에 만지면 결과가 "하나씩 차례로 돌린 것"과 달라질 수 있다(13·14번).\
락을 쓰면 막을 수 있을 것 같지만, **락을 걸기만 해서는 부족하다.**

```text
  T1: lock(A) read A  unlock(A)                 lock(A) write A=A+1 unlock(A)
  T2:                          lock(A) write A=A+1 unlock(A)
  → T1은 A를 읽은 뒤 락을 풀었다. 그 사이 T2가 A를 바꿨다.
    T1이 옛 값으로 다시 쓰면 T2의 변경이 사라진다(lost update).
```

- 락을 "쓸 때만 잠깐" 쥐면 안 된다. **언제 풀어도 되는가**를 정한 규칙이 필요하다.
- 그 규칙이 **2단계 락킹(2PL)**이다.
  - *2PL(Two-Phase Locking)*: 트랜잭션이 락을 **얻기만 하는 단계**와 **풀기만 하는 단계**로 나뉘는 규약. 한 번 풀기 시작하면 다시 얻지 못한다.

쉬운 예: 도서관에서 여러 권을 대출해 보고서를 쓴다.
- 필요한 책을 다 빌리기 전에는 한 권도 반납하지 않는다.
- 한 권이라도 반납했으면 더 빌리지 않는다.
- 그러면 내가 읽은 책을 남이 중간에 고쳐 끼우는 일이 없다.

똑같은 구조다.\
그런데 이 규칙은 "서로 상대 책을 기다리는" 상황, 즉 **교착(deadlock)**을 막지 못한다. 그래서 DB는 교착을 **탐지해서 한쪽을 죽인다.**

실무 예:
- 이체 A→B와 B→A가 동시에 들어오면 MySQL은 `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction`, PostgreSQL은 `ERROR: deadlock detected`(SQLSTATE `40P01`)를 낸다.
- 한 트랜잭션이 오래 쥐고 있으면 MySQL은 기본 설정(`innodb_lock_wait_timeout=50`)에서 50초 뒤 `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`을 낸다.

## 동작·원리

### 1. 2PL — 성장 단계와 축소 단계

```text
  쥔 락 개수
    ^
    |          ┌──── 락 지점(lock point): 가장 많이 쥔 순간
    |        ┌─┘└─┐
    |      ┌─┘    └─┐
    |    ┌─┘        └─┐
    |  ┌─┘            └─┐
    +──┴────────────────┴──────> 시간
       성장(growing)      축소(shrinking)
       얻기만 한다          풀기만 한다
```

- 2PL만으로 **충돌 직렬화 가능성**이 보장된다. 선행 그래프에 사이클이 생기지 않는다(CMU 15-445 L17).
  - *충돌 직렬화 가능(conflict serializable)*: 충돌하는 연산(같은 데이터에 대한 읽기-쓰기, 쓰기-쓰기)의 순서를 유지한 채 어떤 직렬 실행으로 바꿀 수 있는 스케줄. 13번 참고.
- 기본 2PL의 약점 두 가지
  - **연쇄 중단(cascading abort)**: 축소 단계에서 푼 쓰기 락 뒤의 값을 남이 읽었다. 그런데 원래 트랜잭션이 중단되면, 읽은 쪽도 같이 되돌려야 한다.
  - **교착**: 성장 단계에서 서로의 락을 기다리면 멈춘다. 2PL은 이것을 막지 않는다.

### 2. 엄격(strict) 2PL — 커밋까지 쥔다

```text
  기본 2PL     락 ▁▂▃▅▇▇▅▃▂▁ ... 커밋       (중간에 풀기 시작)
  강한 엄격 2PL 락 ▁▂▃▅▇▇▇▇▇▇▇ 커밋 → 전부 해제 (끝에 한꺼번에)
```

- CMU L17은 "쓴 값은 그 트랜잭션이 커밋할 때까지 남이 읽거나 덮어쓰지 못한다"를 **strict 스케줄**로 정의한다.
- 커밋할 때만 락을 푸는 변형을 **강한 엄격 2PL(Strong Strict 2PL, Rigorous 2PL)**이라 부른다(CMU L17).
  - 연쇄 중단이 없다. 중단 시 원래 값으로 되돌리기만 하면 된다.
  - 대신 동시성이 줄어든다.
- 실제 DB도 이 방식에 가깝다.
  - PostgreSQL 17: "한 번 얻은 락은 보통 트랜잭션 끝까지 쥔다." 단 세이브포인트 뒤에 얻은 락은 그 세이브포인트로 롤백하면 바로 풀린다(13.3.1).
  - MySQL 8.4 InnoDB: 행 락은 트랜잭션 끝까지 간다. 예외로 READ COMMITTED에서는 WHERE에 맞지 않은 행의 레코드 락을 조건 평가 뒤 푼다(17.7.1 Gap Locks 절).
- 교재마다 이름이 다르다. "쓰기(배타) 락만 끝까지"를 strict 2PL(S2PL), "읽기·쓰기 락 모두 끝까지"를 strong strict 2PL(SS2PL, rigorous)로 나누는 분류도 있다(Wikipedia "Two-phase locking" §Strict two-phase locking). CMU L17은 후자를 가리켜 strict라는 말을 섞어 쓴다. 이름보다 "무엇을 언제까지 쥐나"로 기억한다.

### 3. 락 모드와 호환 행렬

```text
  기본 두 모드                     요청 →   S     X
    S(공유): 읽기용, 여럿 동시 가능       쥠 S   ✓     ✗
    X(배타): 쓰기용, 혼자만              쥠 X   ✗     ✗
```

- **다중 단위 락(multiple granularity)**: 테이블 하나에 X를 걸지, 행 10억 개에 하나씩 걸지의 절충이다. 상위 객체에 **의도 락(intention lock)**을 먼저 건다(CMU L17).
  - *의도 락*: "아래 단계(행)에 S나 X를 걸 생각이다"라는 표시. 테이블 전체를 잠그려는 쪽이 행을 하나하나 뒤지지 않고도 충돌을 안다.

```text
  MySQL 8.4 InnoDB 테이블 수준 호환 (17.7.1)
           X     IX    S     IS
    X      ✗     ✗     ✗     ✗
    IX     ✗     ✓     ✗     ✓
    S      ✗     ✗     ✓     ✓
    IS     ✗     ✓     ✓     ✓
```

- InnoDB: `SELECT ... FOR SHARE`는 테이블에 IS, `SELECT ... FOR UPDATE`는 IX를 먼저 건다. 의도 락은 `LOCK TABLES ... WRITE` 같은 **테이블 전체 요청만** 막는다(17.7.1).
- PostgreSQL 17은 테이블 락 모드가 8개다. 이름에 "ROW"가 들어가도 전부 **테이블 락**이다(13.3.1).

```text
  PostgreSQL 17 테이블 락 (약한 것 → 강한 것, 누가 거나)
  ACCESS SHARE           SELECT                          ← ACCESS EXCLUSIVE하고만 충돌
  ROW SHARE              SELECT ... FOR UPDATE/SHARE
  ROW EXCLUSIVE          INSERT·UPDATE·DELETE·MERGE
  SHARE UPDATE EXCLUSIVE VACUUM(FULL 아님)·ANALYZE·CREATE INDEX CONCURRENTLY
  SHARE                  CREATE INDEX(CONCURRENTLY 아님)
  SHARE ROW EXCLUSIVE    CREATE TRIGGER, 일부 ALTER TABLE
  EXCLUSIVE              REFRESH MATERIALIZED VIEW CONCURRENTLY
  ACCESS EXCLUSIVE       DROP·TRUNCATE·VACUUM FULL·많은 ALTER TABLE 형태  ← 모두와 충돌
```

- 일반 `SELECT`를 막는 것은 ACCESS EXCLUSIVE뿐이다(13.3.1 Tip).
- PostgreSQL 행 락은 4개다: `FOR KEY SHARE` < `FOR SHARE` < `FOR NO KEY UPDATE` < `FOR UPDATE`(13.3.2).
  - 키 컬럼을 바꾸지 않는 보통 `UPDATE`는 `FOR NO KEY UPDATE`를 건다. 그래서 외래 키 검사가 거는 `FOR KEY SHARE`와 충돌하지 않는다.
  - 행 락은 **읽기를 막지 않는다.** 같은 행의 쓰기와 락 요청만 막는다.

### 4. 락은 어디에 저장되나 — 두 엔진의 차이

```text
  PostgreSQL 17                                   MySQL 8.4 InnoDB
  ┌ 공유 메모리 락 테이블(해시, 16 파티션) ┐         ┌ lock_sys.rec_hash (해시) ┐
  │ 키 = LOCKTAG(관계·트랜잭션ID·튜플 …)  │         │ 키 = 페이지(space, page)  │
  │ 테이블 락, 트랜잭션 ID 락, 튜플 락      │         │ 값 = 트랜잭션별 비트맵     │
  └──────────────────────────────────────┘         │     (페이지 안 레코드 번호) │
  행 락 자체는 행 헤더의 xmax에 적는다              └──────────────────────────┘
  (메모리에 행 개수만큼 두지 않는다)                  행 락 = 인덱스 레코드 락
```

- PostgreSQL
  - 테이블 락 등은 공유 메모리 해시 테이블에 둔다. 단 DML이 거는 약한 테이블 락(ACCESS SHARE·ROW SHARE·ROW EXCLUSIVE)은 보통 백엔드의 *fast path* 슬롯에 먼저 적고, 충돌할 강한 락이 오면 공유 테이블로 옮긴다(lmgr `README` Fast Path Locking). 해시는 `LOCKTAG` 값으로 16개 파티션에 나뉜다(`lwlock.h` `NUM_LOCK_PARTITIONS`, lmgr `README`).
  - 행 락은 **튜플 헤더에 기록**한다. 잠근 트랜잭션의 XID를 `xmax`에 적고 infomask 비트로 "삭제가 아니라 잠금"임을 표시한다. 여럿이 공유로 잠그면 MultiXact를 쓴다(`README.tuplock`).
  - 그래서 동시에 잠글 수 있는 행 수에 한도가 없다. 대신 `SELECT FOR UPDATE`가 디스크 쓰기를 일으킬 수 있다(13.3.2).
  - 행을 기다리는 쪽은 **그 행을 쥔 트랜잭션의 ID 락**을 기다린다. 대기 순서를 지키려고 튜플 락을 잠깐 함께 쥔다(`README.tuplock`).
- InnoDB
  - 행 락은 사실 **인덱스 레코드 락**이다. 인덱스가 없는 테이블도 숨은 클러스터드 인덱스에 건다(17.7.1 Record Locks).
  - 명시적 레코드 락은 페이지 단위 구조체 + 비트맵이다. (삽입·수정한 레코드에는 비트맵 없이 레코드의 트랜잭션 ID로 판별하는 *암묵적 X 락*이 있고, 누가 기다리면 명시적 락으로 바뀐다 — `lock0priv.h`.) 비트 하나가 페이지 안 레코드 하나다(`lock0priv.h` `lock_rec_t`의 `page_id`·`n_bits`). `SHOW ENGINE INNODB STATUS`의 `n bits 72`가 이 비트맵 크기다.
  - REPEATABLE READ(기본)에서는 잠금 검색·스캔에 보통 **next-key 락**(레코드 + 그 앞 갭)을 건다. 유니크 인덱스로 행 하나를 찾을 때는 갭 없이 레코드만 잠근다(`REC_NOT_GAP`). 새 행이 범위에 끼어드는 팬텀을 막는다(17.7.1).

로컬 재현(예시, PostgreSQL 17.11) — 세션 A가 `id=1`을 고친 채 멈춰 있고 세션 B가 같은 행을 고치려 한다.

```text
   pid  |   locktype    |     mode      | granted | xid |   rel   | page | tuple
  ------+---------------+---------------+---------+-----+---------+------+-------
   1684 | transactionid | ExclusiveLock | t       | 952 |         |      |          ← A 자기 XID
   1691 | transactionid | ExclusiveLock | t       | 954 |         |      |          ← B 자기 XID
   1691 | transactionid | ShareLock     | f       | 952 |         |      |          ← B가 A의 XID를 기다림
   1691 | tuple         | ExclusiveLock | t       |     | account |    0 |     5    ← 대기 순번 표시

  pg_stat_activity: 1691  blocked_by={1684}  wait_event_type=Lock  wait_event=transactionid
```

- `pg_locks`에서 행 락을 찾으면 안 보인다. 보이는 것은 **트랜잭션 ID 대기**다.

### 5. DB 교착 탐지 — wait-for 그래프

```text
  T1: UPDATE id=1 ─────── UPDATE id=2 (대기)
  T2:        UPDATE id=2 ─────── UPDATE id=1 (대기)

  wait-for 그래프:  T1 ──(id=2)──> T2 ──(id=1)──> T1   사이클 = 교착
```

- 노드는 트랜잭션, 간선 Ti → Tj는 "Ti가 Tj가 쥔 락을 기다린다"다. 사이클이 있으면 교착이다(CMU L17, os/19).
- 사이클을 끊으려면 **희생자(victim)** 하나를 중단한다. CMU L17은 나이·진행량·쥔 락 수·같이 롤백될 트랜잭션 수·재시작 횟수 같은 기준을 든다. "무엇이 최선"은 없다.

| | PostgreSQL 17 | MySQL 8.4 InnoDB |
|---|---|---|
| 검사 시점 | 락을 `deadlock_timeout`(기본 1s) 동안 기다린 뒤에만 | 지연 설정 없이 바로 (탐지 기본 켜짐, `innodb_deadlock_detect`). 로컬 재현에서 사이클을 닫은 문장이 곧바로 1213을 받았다 |
| 희생자 | 검사를 돌린 쪽. 문서는 "누가 중단될지 예측하기 어렵다"(13.3.4) | 작은 트랜잭션(삽입·갱신·삭제한 행 수 기준)을 고르려 한다(17.7.5.2) |
| 오류 | `ERROR: deadlock detected` / `40P01` | `ERROR 1213 (40001)` |
| 롤백 범위 | 트랜잭션 전체가 실패 상태(세이브포인트 뒤에서 났으면 `ROLLBACK TO SAVEPOINT`로 그 부분만 되돌릴 수 있다) | 트랜잭션 전체 |
| 한도 | — | wait-for 목록 200개 초과 또는 락 1,000,000개 초과 조사 → 교착으로 간주 |

로컬 재현(예시, PostgreSQL 17.11): A가 `id=1` → 1초 쉼 → `id=2`, B가 0.3초 늦게 `id=2` → 1.5초 쉼 → `id=1`.

```text
  A: UPDATE ... id=2   → ERROR:  deadlock detected           Time: 1000.538 ms
     DETAIL:  Process 1395 waits for ShareLock on transaction 923; blocked by process 1416.
              Process 1416 waits for ShareLock on transaction 920; blocked by process 1395.
     CONTEXT:  while updating tuple (0,2) in relation "account"
  B: UPDATE ... id=1   → UPDATE 1                            Time: 190.654 ms
```

- A가 먼저 기다리기 시작했으므로 A의 `deadlock_timeout`이 먼저 끝났다. 검사를 돌린 A가 중단됐다.
- 오류가 **약 1초 뒤**에 났다. 교착인데도 1초는 그냥 기다린다.

로컬 재현(예시, MySQL 8.4.10): 같은 순서를 InnoDB에서 돌렸다.

```text
  B: UPDATE account SET balance=balance+100 WHERE id=1
     ERROR 1213 (40001) at line 4: Deadlock found when trying to get lock; try restarting transaction

  SHOW ENGINE INNODB STATUS → LATEST DETECTED DEADLOCK
    *** (1) TRANSACTION: TRANSACTION 2648 ... UPDATE ... WHERE id=2
    *** (1) HOLDS THE LOCK(S): ... index PRIMARY ... lock_mode X locks rec but not gap
    *** (1) WAITING FOR THIS LOCK TO BE GRANTED: ... lock_mode X locks rec but not gap waiting
    *** (2) TRANSACTION: TRANSACTION 2649 ... UPDATE ... WHERE id=1
    ...
    *** WE ROLL BACK TRANSACTION (2)
```

- 두 트랜잭션이 바꾼 행 수가 같았고, 사이클을 닫은 요청을 한 (2)가 롤백됐다. 이 결과 하나로 "요청한 쪽이 항상 희생된다"고 일반화하지는 않는다.

### 6. 교착 예방 — 탐지 대신 규칙으로

- **wait-die**: 요청자가 우선순위(보통 오래된 쪽)가 높으면 기다리고, 낮으면 스스로 중단한다.
- **wound-wait**: 요청자가 우선순위가 높으면 쥔 쪽을 중단시키고(wound), 낮으면 기다린다.
- 두 방식 모두 대기 방향이 한쪽뿐이라 사이클이 생기지 않는다. 재시작해도 **원래 타임스탬프를 유지**해서 기아를 막는다(CMU L17).
- PostgreSQL·InnoDB의 일반 행 락은 이 방식이 아니라 **탐지**를 쓴다(위 표).

## 쓰이는 자료구조·알고리즘

- **락 테이블 = 해시 테이블 + 대기 큐** — 객체 키(LOCKTAG, 페이지 ID)로 해시해서 "쥔 목록 + 기다리는 목록"을 찾는다. PostgreSQL은 해시를 16 파티션으로 나눠 파티션마다 LWLock을 둔다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **비트맵** — InnoDB 레코드 락은 페이지당 비트맵이다. 행 하나 = 비트 하나라서 한 페이지의 여러 행 락이 구조체 하나에 들어간다. [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- **wait-for 그래프 + DFS 사이클 탐지** — PostgreSQL `deadlock.c`의 `FindLockCycleRecurse`가 간선을 따라 재귀로 나가 출발점으로 돌아오는지 본다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **대기 큐 재배열** — PostgreSQL은 "먼저 온 요청이 앞"이라는 **soft edge**만으로 생긴 사이클은 대기 큐 순서를 바꿔 풀어 본다. **hard edge**(실제로 쥔 락) 사이클이거나, 재배열로도 풀 수 없는 사이클이면 교착 오류가 된다(lmgr `README`).
- **선행 그래프** — 2PL이 만든 스케줄은 선행 그래프에 사이클이 없다. 이것이 직렬화 가능성의 증명 도구다(13번).

## 적용 — 풀어나가는 법

### 1. 잠그는 순서를 통일한다

```sql
-- PostgreSQL 17 / MySQL 8.4 공통: 여러 행을 한 트랜잭션에서 고칠 때
BEGIN;
SELECT id FROM account WHERE id IN (2, 1) ORDER BY id FOR UPDATE;  -- 항상 id 오름차순으로 잠근다
UPDATE account SET balance = balance - 100 WHERE id = 2;
UPDATE account SET balance = balance + 100 WHERE id = 1;
COMMIT;
```

- PostgreSQL 문서: 여러 객체를 **같은 순서**로 잠그는 것이 최선의 방어다. 한 객체에는 처음부터 필요한 **가장 강한 모드**로 잠근다(13.3.4).
  - 예: 같은 행을 `FOR SHARE`로 읽고 나중에 `UPDATE`하면, 두 트랜잭션이 공유 락을 쥔 채 서로의 업그레이드를 기다린다. 로컬 재현(예시, PostgreSQL 17.11)에서 두 세션이 같은 행을 `FOR SHARE` → `UPDATE` 하자 한쪽이 `deadlock detected`를 받았다. 처음부터 `FOR UPDATE`로 읽는다.
- 트랜잭션을 짧게 한다. 락은 커밋까지 가므로 트랜잭션 길이 = 락 보유 시간이다.

### 2. 재시도를 준비한다 — 트랜잭션 전체를

```java
// Spring: 교착·락 획득 실패는 PessimisticLockingFailureException 계열로 번역된다
for (int attempt = 1; ; attempt++) {
    try {
        transferService.transfer(from, to, amount);   // @Transactional 경계 전체를 다시 돈다
        break;
    } catch (PessimisticLockingFailureException e) {  // MySQL 1213·1205, PG 40P01·40001 (Spring 6.x 기본 경로)
        if (attempt >= 3) throw e;
        Thread.sleep(ThreadLocalRandom.current().nextLong(20, 100) * attempt);  // 지터 백오프 (예시 값)
    }
}
```

- Spring 6.x 기본 번역 경로(사용자 `sql-error-codes.xml`이 없을 때): `SQLExceptionSubclassTranslator` → `SQLStateSQLExceptionTranslator`(56번 §2).
  - MySQL: Connector/J가 1213과 1205의 SQLSTATE를 `40001`로 준다 → 둘 다 `CannotAcquireLockException`. 3572(NOWAIT)는 `HY000`이라 이 계열이 아니다.
  - PostgreSQL: `40001` → `CannotAcquireLockException`, `40P01` → `PessimisticLockingFailureException`. `55P03`은 SQLSTATE 표에 없어 `JdbcTemplate`에서는 `UncategorizedSQLException`이 된다.
- 사용자 `sql-error-codes.xml`을 두면 구형 에러 코드 표 경로다.
  - MySQL: 1213 → `deadlockLoserCodes`, 1205·3572 → `cannotAcquireLockCodes`.
  - PostgreSQL: 40P01 → `deadlockLoserCodes`, 55P03 → `cannotAcquireLockCodes`, 40001 → `cannotSerializeTransactionCodes`.
  - `DeadlockLoserDataAccessException`·`CannotSerializeTransactionException`은 6.0.3부터 deprecated다. 부모인 `PessimisticLockingFailureException`으로 잡는다.
- 재시도는 **트랜잭션 바깥**에서 한다. 트랜잭션 안에서 문장만 다시 돌리면 PostgreSQL은 `current transaction is aborted`로 거부한다.

### 3. 기다림에 상한을 둔다

```sql
-- PostgreSQL 17: 세션·트랜잭션 단위로 (postgresql.conf 전역 설정은 문서가 권하지 않는다)
SET lock_timeout = '3s';        -- 기본 0 = 꺼짐. 넘으면 55P03 "canceling statement due to lock timeout"
SELECT ... FOR UPDATE NOWAIT;   -- 못 잡으면 즉시 55P03

-- MySQL 8.4
SET SESSION innodb_lock_wait_timeout = 3;   -- 기본 50초. 넘으면 1205
SELECT ... FOR UPDATE NOWAIT;               -- 즉시 오류 3572
```

- PostgreSQL은 교착이 아니면 락을 **무한정** 기다린다(13.3.4). 상한은 직접 건다.
- 서버 측 시간 한도 전체는 22번 `database-side-timeouts`가 다룬다.

### 4. 진단 쿼리

```sql
-- PostgreSQL 17: 누가 누구를 막나
SELECT pid, pg_blocking_pids(pid) AS blocked_by, wait_event_type, wait_event,
       now() - xact_start AS xact_age, left(query, 60)
FROM pg_stat_activity WHERE wait_event_type = 'Lock';
SELECT locktype, relation::regclass, mode, granted, pid FROM pg_locks WHERE NOT granted;
-- log_lock_waits = on 이면 deadlock_timeout 넘게 기다린 대기가 서버 로그에 남는다 (19.8.3, 19.12)

-- MySQL 8.4
SELECT ENGINE_TRANSACTION_ID, OBJECT_NAME, INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_STATUS, LOCK_DATA
FROM performance_schema.data_locks;
SELECT * FROM performance_schema.data_lock_waits;
SELECT wait_age, locked_index, waiting_query, blocking_trx_id FROM sys.innodb_lock_waits\G
SHOW ENGINE INNODB STATUS\G                  -- LATEST DETECTED DEADLOCK 절 (마지막 1건만)
SET GLOBAL innodb_print_all_deadlocks = ON;  -- 모든 교착을 에러 로그에 (운영자 작업)
```

로컬 재현(예시, MySQL 8.4.10) — 한 트랜잭션이 `id=1`, `id=2`를 고친 뒤의 `data_locks`:

```text
  | trx  | OBJECT_NAME | INDEX_NAME | LOCK_TYPE | LOCK_MODE     | LOCK_STATUS | LOCK_DATA |
  | 2648 | account     | NULL       | TABLE     | IX            | GRANTED     | NULL      |  ← 의도 락
  | 2648 | account     | PRIMARY    | RECORD    | X,REC_NOT_GAP | GRANTED     | 2         |  ← PK 레코드 락
  | 2648 | account     | PRIMARY    | RECORD    | X,REC_NOT_GAP | GRANTED     | 1         |
```

- PK 동등 조건이라 갭 없이 레코드만 잠갔다(`REC_NOT_GAP`). 유니크 인덱스로 한 행을 찾는 경우다(17.7.1).

## 장애 시나리오와 대처

### 1. `deadlock detected`(PG 40P01) / `ERROR 1213`(MySQL) → 요청 일부가 실패한다

- **현상**: 동시 이체·재고 차감 중 일부 요청이 500으로 떨어진다.
- **보이는 형태**
  - PostgreSQL 17: `ERROR: deadlock detected`, `DETAIL: Process N waits for ShareLock on transaction X; blocked by process M.` 그리고 **약 1초 지연**.
  - MySQL 8.4: `ERROR 1213 (40001)`. Spring에서는 `PessimisticLockingFailureException` 계열.
- **원인**: 두 트랜잭션이 같은 행들을 **반대 순서**로 잠갔다. MySQL은 인덱스 범위 락(next-key) 때문에 SQL만 봐서는 순서가 안 보이기도 한다.
- **대처**
  - 잠그는 순서를 통일한다(`ORDER BY id FOR UPDATE`).
  - 트랜잭션 전체를 재시도한다(횟수 제한 + 지터).
  - 원인 추적: PG는 서버 로그의 교착 상세, MySQL은 `LATEST DETECTED DEADLOCK`·`innodb_print_all_deadlocks`.

### 2. `Lock wait timeout exceeded`(MySQL 1205) → 반쪽 트랜잭션이 커밋된다

- **현상**: 한 요청이 50초 멈췄다가 실패한다. 이후 데이터가 반만 반영된 것이 발견된다.
- **보이는 형태**: `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`. Spring에서는 `CannotAcquireLockException`.
- **원인**
  - 다른 트랜잭션이 행 락을 `innodb_lock_wait_timeout`(8.4 기본 50초) 넘게 쥐었다.
  - 1205는 기본 설정(`innodb_rollback_on_timeout=OFF`)에서 **마지막 문장만** 롤백한다. 트랜잭션은 열린 채다.
  - 로컬 재현(예시, MySQL 8.4.10): `id=5` 갱신 성공 → `id=1` 갱신이 1205 → 그대로 `COMMIT`하니 `id=5`의 변경만 남았다(1000 → 1001, `id=1`은 그대로).
- **대처**
  - 1205를 받으면 **명시적으로 ROLLBACK** 한 뒤 트랜잭션 전체를 재시도한다. 드라이버·프레임워크가 롤백하는지 확인한다.
  - 오래 쥔 쪽을 찾는다: `sys.innodb_lock_waits`, `information_schema.INNODB_TRX`의 `trx_started`.
  - `innodb_rollback_on_timeout`은 동적 변수가 아니다(서버 시작 옵션). 켜려면 재시작이 필요하다.

### 3. `ALTER TABLE` 하나가 테이블 전체를 멈춘다 (PostgreSQL 락 큐)

- **현상**: 배포 중 마이그레이션이 돌자 해당 테이블의 모든 조회가 멈춘다. 마이그레이션 자체는 "빠른 DDL"이었다.
- **보이는 형태**: `pg_stat_activity`에 `wait_event_type=Lock`, `wait_event=relation`이 줄줄이 쌓인다. 커넥션 풀이 고갈된다.
- **원인**: `ALTER TABLE … ADD COLUMN`은 ACCESS EXCLUSIVE를 요청한다(`ALTER TABLE`의 락 수준은 하위 명령마다 다르고, 따로 적지 않은 것은 ACCESS EXCLUSIVE다). 앞에 긴 트랜잭션이 ACCESS SHARE를 쥐고 있으면 ALTER가 기다린다. 뒤에 온 평범한 `SELECT`는 **대기 중인 ALTER와 충돌**하므로 그 뒤에 줄을 선다.
  - 로컬 재현(예시, PostgreSQL 17.11):

```text
   pid  | blocked_by |  wtype  | wait_event |  q
   2080 | {}         | Timeout | PgSleep    | SELECT pg_sleep(4);                       ← 긴 트랜잭션 (ACCESS SHARE 보유)
   2087 | {2080}     | Lock    | relation   | ALTER TABLE account ADD COLUMN memo text  ← ACCESS EXCLUSIVE 대기
   2121 | {2087}     | Lock    | relation   | SELECT count(*) FROM account;             ← SELECT가 ALTER 뒤에 막힘
```

- **대처**
  - 마이그레이션 세션에 `SET lock_timeout = '2s'`를 걸고 실패하면 재시도한다. 줄을 오래 막지 않게 한다.
  - 실행 전에 긴 트랜잭션(`xact_start`가 오래된 세션)을 확인한다.
  - 무중단 마이그레이션 전략은 26번 `schema-migration`.

### 4. 교착 탐지를 껐더니 교착이 50초짜리 대기가 됐다 (MySQL)

- **현상**: 교착이 나면 에러가 즉시 나던 것이 50초 멈춘 뒤 1205로 바뀌었다.
- **보이는 형태**: 1213이 사라지고 1205가 늘었다. `SHOW VARIABLES LIKE 'innodb_deadlock_detect'` = `OFF`.
- **원인**: 동시성이 매우 높을 때 탐지 비용을 줄이려고 `innodb_deadlock_detect`를 껐다. 그러면 교착은 `innodb_lock_wait_timeout`으로만 풀린다(17.7.5.2).
- **대처**: 끌 때는 `innodb_lock_wait_timeout`을 짧게 함께 줄인다. 근본은 핫 행 경합을 줄이는 것이다(18번).

### 5. 탐지기 밖의 교착 — 앱 락과 DB 락이 섞였다

- **현상**: JVM도 DB도 아무 말 없이 멈춘다.
- **원인**: 스레드 1은 앱 락을 쥐고 DB 행 락을 기다린다. 스레드 2의 트랜잭션은 그 행 락을 쥐고 앱 락을 기다린다. DB 탐지기는 DB 안의 그래프만 본다.
  - InnoDB도 `LOCK TABLES`나 다른 스토리지 엔진의 락이 낀 교착은 `innodb_table_locks=1`이고 `autocommit=0`일 때가 아니면 탐지하지 못한다(17.7.5.2).
- **대처**: 앱 락을 쥔 채 DB를 부르지 않는다. 모든 대기에 상한(`lock_timeout`, `innodb_lock_wait_timeout`, `tryLock(timeout)`)을 둔다. [os/19-deadlock](../../os/19-deadlock/2-summary.md) 시나리오 5.

## 핵심 문장

- 락을 거는 것만으로는 직렬화 가능성이 안 나온다. "풀기 시작하면 더 얻지 않는다"는 2PL 규약이 충돌 직렬화 가능성을 보장한다.
- 기본 2PL은 연쇄 중단과 교착에 약하다. 실제 DB는 락을 트랜잭션 끝까지 쥐는 엄격 2PL에 가깝게 동작해 연쇄 중단을 없앤다.
- 의도 락(IS·IX) 덕분에 테이블 락과 행 락이 공존한다. PostgreSQL의 "ROW" 모드 이름들도 전부 테이블 락이다.
- PostgreSQL 행 락은 튜플 `xmax`에 적히고, 대기는 쥔 트랜잭션의 ID 락 대기로 보인다. InnoDB 행 락은 인덱스 레코드 락이며 명시적 락은 페이지당 비트맵이다.
- 교착은 wait-for 그래프의 사이클이다. PostgreSQL은 `deadlock_timeout`(1초) 뒤 검사하고, InnoDB는 지연 설정 없이 검사해 작은 트랜잭션을 롤백하려 한다.
- 1213은 트랜잭션 전체가 롤백된다. 40P01은 트랜잭션 전체가 실패 상태가 된다(세이브포인트가 있으면 그 뒤만 되돌릴 수 있다). 1205는 기본 설정에서 문장만 죽으므로 반드시 명시적으로 롤백한다.

## 관련 주제·근거

- 선행
  - database [14-isolation-levels-and-anomalies](../14-isolation-levels-and-anomalies/2-summary.md) — 이상 현상과 격리 수준.
  - [os/19-deadlock](../../os/19-deadlock/2-summary.md) — 교착 네 조건, 예방·회피·탐지, 락 순서
- 후속·연결
  - [16-mvcc](../16-mvcc/2-summary.md) — 읽기는 락 대신 스냅샷으로
  - [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md) — 락 없이 검증으로
  - [18-app-level-concurrency-patterns](../18-app-level-concurrency-patterns/2-summary.md) — `FOR UPDATE`·조건부 UPDATE 실전
  - database [13-transactions-acid](../13-transactions-acid/2-summary.md)(직렬화 가능성·선행 그래프), [22-database-side-timeouts](../22-database-side-timeouts/2-summary.md)(`lock_timeout`·`innodb_lock_wait_timeout`), [26-schema-migration](../26-schema-migration/2-summary.md), [53-index-concurrency-control](../53-index-concurrency-control/2-summary.md)(래치 vs 락)
  - [languages/sql/syntax/57](../../../languages/sql/syntax/57-explicit-locking-and-deadlock/2-summary.md) — `FOR UPDATE`·`NOWAIT`·`SKIP LOCKED`·갭 락 문법과 재현
  - [ops-patterns/failure-modes](../../ops-patterns/failure-modes/2-summary.md) — F-02 데드락
  - [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- 강의
  - CMU 15-445/645 Fall 2024 Lecture #17 Two-Phase Locking — 성장/축소, strong strict(rigorous) 2PL, 스케줄 포함 관계, wait-for 그래프, 희생자 기준, wait-die·wound-wait, 락 계층·IS/IX/SIX <https://15445.courses.cs.cmu.edu/fall2024/notes/17-twophaselocking.pdf>
- PostgreSQL 17
  - 13.3 Explicit Locking — 13.3.1 테이블 락 8모드·표 13.2, 13.3.2 행 락 4모드·표 13.3, 13.3.4 Deadlocks <https://www.postgresql.org/docs/17/explicit-locking.html>
  - 19.12 Lock Management — `deadlock_timeout`(1s), `max_locks_per_transaction`(64) <https://www.postgresql.org/docs/17/runtime-config-locks.html>
  - 66.3 Subtransactions(세이브포인트로 하위 트랜잭션만 중단) <https://www.postgresql.org/docs/17/subxacts.html> · `ALTER TABLE` 하위 명령별 락 수준 <https://www.postgresql.org/docs/17/sql-altertable.html>
  - 19.11 `lock_timeout`(0 = 꺼짐) <https://www.postgresql.org/docs/17/runtime-config-client.html> · 부록 A `40P01`·`55P03`·`40001`
  - 소스: `src/backend/storage/lmgr/README`(LOCK·PROCLOCK, 파티션, soft/hard edge), `src/backend/access/heap/README.tuplock`(xmax·MultiXact, 튜플 락 대기 프로토콜), `src/include/storage/lwlock.h`(`NUM_LOCK_PARTITIONS` = 16), `src/backend/storage/lmgr/deadlock.c`, `src/backend/tcop/postgres.c`("canceling statement due to lock timeout", `ERRCODE_LOCK_NOT_AVAILABLE`) — REL_17_STABLE
- MySQL 8.4
  - 17.7.1 InnoDB Locking — S/X, 의도 락·호환 행렬, 레코드·갭·next-key 락 <https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html>
  - 17.7.5.2 Deadlock Detection — 작은 트랜잭션 롤백, 200·1,000,000 한도, 탐지 비활성화 <https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-detection.html>
  - 17.14 InnoDB 시스템 변수 — `innodb_lock_wait_timeout`(50), `innodb_rollback_on_timeout`(OFF, 비동적), `innodb_deadlock_detect`(ON), `innodb_print_all_deadlocks`(OFF) <https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html>
  - 소스: `storage/innobase/include/lock0priv.h`(`lock_rec_t`), `lock0lock.h`(`rec_hash`) — mysql-server 8.4 브랜치
- Wikipedia "Two-phase locking" §Strict two-phase locking / §Strong strict two-phase locking — S2PL vs SS2PL(rigorous) 용어 <https://en.wikipedia.org/wiki/Two-phase_locking>
- Spring Framework 6.2.x `spring-jdbc`: `JdbcAccessor`·`SQLExceptionSubclassTranslator`·`SQLStateSQLExceptionTranslator`(기본 경로), `sql-error-codes.xml`(사용자 파일을 둘 때의 MySQL·PostgreSQL 코드 매핑), `DeadlockLoserDataAccessException`·`CannotSerializeTransactionException`(6.0.3 deprecated) <https://github.com/spring-projects/spring-framework/tree/6.2.x/spring-jdbc/src/main/java/org/springframework/jdbc/support> · Connector/J `MysqlErrorNumbers`(1205 → 40001, Bug#16634180) <https://github.com/mysql/mysql-connector-j>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): PG 행 대기의 `pg_locks`(transactionid ShareLock + tuple 락), PG 교착 1초 지연과 DETAIL, InnoDB 교착과 `LATEST DETECTED DEADLOCK`, PG `FOR SHARE` → `UPDATE` 업그레이드 교착, MySQL `NOWAIT` 3572·`sys.innodb_lock_waits`, `data_locks`의 IX + `X,REC_NOT_GAP`, 1205 뒤 COMMIT으로 반쪽 반영, PG `ALTER TABLE` 락 큐 뒤에 막힌 `SELECT`
