# database/15-two-phase-locking-and-deadlock — 정답

## 정답

### 1. 락만으로는 부족하고, 2PL이 "푸는 시점"을 정한다

```text
  T1: lock(A) read A=100 unlock(A)                    lock(A) write A=101 unlock(A)
  T2:                            lock(A) write A=101 unlock(A)
  결과 A=101. 두 번 더했는데 한 번만 반영 → lost update
```

- 락을 걸었어도 T1이 읽기와 쓰기 **사이에 풀었다.** 그 틈에 T2가 끼어들었다.
- 2PL 규칙: 한 번 풀기 시작하면(축소 단계) 더는 얻지 못한다(CMU 15-445 L17).
  - T1은 A를 쓸 계획이 있으면 읽은 뒤에도 A를 쥐고 있어야 한다. T2는 T1이 풀 때까지 기다린다.
- 그 결과 선행 그래프에 사이클이 생기지 않는다. 즉 충돌 직렬화 가능한 스케줄만 나온다.

### 2. 기본 2PL vs 강한 엄격 2PL

| | 푸는 시점 | 연쇄 중단 | 교착 |
|---|---|---|---|
| 기본 2PL | 락 지점 이후 아무 때나(축소 단계) | 생길 수 있다 | 생길 수 있다 |
| 강한 엄격 2PL(rigorous) | 커밋·중단할 때 한꺼번에 | 없다 | **여전히 생길 수 있다** |

- 기본 2PL은 축소 단계에서 쓰기 락을 풀 수 있다. 남이 그 값을 읽었는데 원래 트랜잭션이 중단되면 읽은 쪽도 되돌려야 한다(cascading abort, CMU L17).
- 엄격 2PL은 쓴 값을 커밋 전에 아무도 못 보게 해서 연쇄 중단을 없앤다. 대신 동시성이 줄어든다.
- 교착은 성장 단계의 문제라 어느 쪽도 막지 못한다. 탐지(또는 wait-die·wound-wait 같은 예방)가 따로 필요하다.
- 실제 엔진: PostgreSQL 17은 락을 보통 트랜잭션 끝까지 쥔다(세이브포인트 롤백 예외, 13.3.1). InnoDB도 행 락을 끝까지 쥔다(READ COMMITTED에서 조건에 안 맞는 행의 락은 조건 평가 뒤 풀림, 17.7.1).

### 3. 의도 락

- 문제: 누가 "테이블 전체를 X로" 잠그려 할 때, 행 락이 하나라도 있는지 행을 전부 뒤질 수는 없다.
- 해결: 행을 잠그기 전에 테이블에 "아래에 락을 걸 거다" 표시(IS·IX)를 먼저 건다(CMU L17, MySQL 17.7.1).
- MySQL 8.4 InnoDB의 `SELECT ... FOR UPDATE`
  - 테이블: `IX`
  - 행: 인덱스 레코드에 `X` 레코드 락(PK 동등 조건이면 `X,REC_NOT_GAP`, 범위 스캔이면 REPEATABLE READ에서 next-key 락)
  - 로컬 재현(예시, MySQL 8.4.10): `data_locks`에 `TABLE IX GRANTED` 한 줄 + `RECORD X,REC_NOT_GAP` 행마다 한 줄.
- 의도 락끼리(IX–IX, IS–IX)는 서로 호환이다. 각자 **다른 행**을 잠글 수도 있기 때문이다. 같은 행의 충돌은 행 수준 락이 가린다.
- 의도 락은 `LOCK TABLES ... WRITE` 같은 테이블 전체 요청만 막는다.

### 4. PostgreSQL 17 락 모드 이름의 함정

- `ROW EXCLUSIVE`는 **테이블 락**이다. `INSERT`·`UPDATE`·`DELETE`·`MERGE`가 대상 테이블에 건다. 이름에 ROW가 들어가도 8개 모드 전부 테이블 락이다(13.3.1).
- 보통 `SELECT`(ACCESS SHARE)와 충돌하는 모드는 **ACCESS EXCLUSIVE** 하나뿐이다. `DROP`·`TRUNCATE`·`VACUUM FULL`·많은 형태의 `ALTER TABLE`이 건다.
- 행 락은 4단계다: `FOR KEY SHARE` < `FOR SHARE` < `FOR NO KEY UPDATE` < `FOR UPDATE`(13.3.2).
  - 키 컬럼을 바꾸지 않는 `UPDATE`는 `FOR NO KEY UPDATE`를 건다.
  - 자식 행 INSERT의 외래 키 검사는 부모 행에 `FOR KEY SHARE`를 건다.
  - 두 모드는 호환이다. 그래서 부모의 비키 컬럼 UPDATE와 자식 INSERT가 서로 막지 않는다.

### 5. 행 락의 저장 위치

```text
  PostgreSQL 17: 행 헤더 xmax = 잠근 XID (+ infomask "잠금 전용" 비트), 여럿이면 MultiXact
  InnoDB 8.4   : lock_sys 해시(키 = 페이지) → 트랜잭션별 레코드 락 + 페이지 안 레코드 비트맵 (명시적 락 기준)
```

- PostgreSQL은 행 락을 메모리 락 테이블에 행마다 두지 않는다(`README.tuplock`). 그래서 잠글 수 있는 행 수에 한도가 없고, 대신 `FOR UPDATE`가 페이지를 더럽힌다(13.3.2).
- 기다리는 쪽은 "그 행을 쥔 **트랜잭션 ID** 락"에 `ShareLock`을 요청한다. 대기 순서를 위해 `tuple` 락도 잠깐 쥔다.
- 로컬 재현(예시, PostgreSQL 17.11):

```text
  1691 | transactionid | ShareLock     | f | 952      ← B가 A(XID 952)의 끝을 기다림
  1691 | tuple         | ExclusiveLock | t | account (0,5)
```

- 그래서 `pg_locks`에 `locktype = 'tuple'`로 "행이 잠겼다"는 줄이 모든 행마다 나오지 않는다. 대기는 `transactionid` 줄로 보인다.

### 6. 반대 순서 갱신의 결과

- PostgreSQL 17
  - 먼저 기다리기 시작한 쪽이 `deadlock_timeout`(기본 1s)을 채우면 교착 검사를 돈다.
  - 사이클을 찾으면 **검사를 돈 쪽**이 `ERROR: deadlock detected`, SQLSTATE `40P01`로 실패한다. 문서는 누가 실패할지 "예측하기 어렵다"고 한다(13.3.4).
  - 로컬 재현(예시, PostgreSQL 17.11): 먼저 기다린 A가 약 1000ms 뒤 실패했고, B는 이어서 `UPDATE 1` 후 커밋했다.
- MySQL 8.4 InnoDB
  - `deadlock_timeout` 같은 지연이 없다. 로컬 재현에서는 사이클을 닫은 문장이 곧바로 `ERROR 1213 (40001)`을 받았다.
  - 희생자는 삽입·갱신·삭제한 행 수가 적은 "작은" 트랜잭션을 고르려 한다(17.7.5.2).
  - MySQL은 희생자의 **트랜잭션 전체**가 롤백된다. PostgreSQL은 트랜잭션 전체가 실패 상태가 된다. 단 세이브포인트 뒤에서 교착이 났으면 `ROLLBACK TO SAVEPOINT`로 그 부분만 되돌리고 계속할 수 있다(PostgreSQL 17 66.3).

### 7. 1205의 반쪽 커밋

- `innodb_lock_wait_timeout`(MySQL 8.4 기본 50초)을 넘기면 1205다.
- 기본 `innodb_rollback_on_timeout=OFF`에서 1205는 **마지막 문장만** 롤백한다. 트랜잭션은 열린 채 남는다(17.14).
- 앱이 예외를 잡고 계속 진행해 `COMMIT`하면 앞 문장들만 커밋된다.
  - 로컬 재현(예시, MySQL 8.4.10): `id=5` 갱신 성공 → `id=1` 갱신이 1205 → `COMMIT` → `id=5`만 1000 → 1001.
- 1213(교착)은 트랜잭션 **전체**를 롤백한다.
- 대처: 1205를 받으면 명시적 `ROLLBACK` 후 트랜잭션 전체를 재시도한다. `innodb_rollback_on_timeout`은 동적 변수가 아니라 켜려면 재시작이 필요하다.

### 8. `ALTER TABLE` 뒤에 줄 선 `SELECT`

```text
  긴 트랜잭션(ACCESS SHARE 보유) ← ALTER(ACCESS EXCLUSIVE 대기) ← SELECT들(ACCESS SHARE 대기)
```

- ALTER가 요청하는 ACCESS EXCLUSIVE는 앞의 긴 트랜잭션이 쥔 ACCESS SHARE와 충돌해 기다린다.
- 뒤에 온 `SELECT`의 ACCESS SHARE는 이미 쥔 락과는 호환이지만, **대기 중인 ALTER**와 충돌하므로 ALTER 뒤에 줄을 선다.
  - 로컬 재현(예시, PostgreSQL 17.11): `SELECT count(*)`의 `pg_blocking_pids`가 ALTER의 pid였다.
- 대처
  - 마이그레이션 세션에 `SET lock_timeout = '2s'`(예시 값)를 걸고, 실패하면 잠시 뒤 재시도한다.
  - 실행 전에 `pg_stat_activity`에서 `xact_start`가 오래된 세션을 확인한다.

### 9. 이체 교착 고치기

```sql
BEGIN;
SELECT id FROM account WHERE id IN (:from, :to) ORDER BY id FOR UPDATE;  -- 항상 id 오름차순
UPDATE account SET balance = balance - :amt WHERE id = :from;
UPDATE account SET balance = balance + :amt WHERE id = :to;
COMMIT;
```

```java
for (int attempt = 1; ; attempt++) {
    try {
        transferService.transfer(from, to, amount);   // @Transactional 메서드 전체
        break;
    } catch (PessimisticLockingFailureException e) {  // MySQL 1213·1205, PG 40P01·40001 (Spring 6.x 기본 경로)
        if (attempt >= 3) throw e;
        Thread.sleep(ThreadLocalRandom.current().nextLong(20, 100) * attempt);  // 예시 값
    }
}
```

- 잠그는 순서를 통일하면 원형 대기가 사라진다(PostgreSQL 13.3.4의 권고, os/19의 락 순서).
- 재시도가 트랜잭션 바깥이어야 하는 이유
  - 교착 희생자는 트랜잭션 전체가 롤백됐다(PostgreSQL은 실패 상태, 세이브포인트를 쓰지 않은 경우). 앞에서 한 변경도 사라졌으니 처음부터 다시 해야 한다.
  - PostgreSQL은 오류 뒤 같은 트랜잭션의 명령을 `current transaction is aborted, commands ignored until end of transaction block`으로 거부한다(로컬 재현).
- Spring 6.x 기본 번역 경로(사용자 `sql-error-codes.xml` 없음)에서는 `40001`(PG 직렬화 실패, Connector/J가 바꾼 MySQL 1213·1205)이 `CannotAcquireLockException`, PG `40P01`이 `PessimisticLockingFailureException`이다. 사용자 `sql-error-codes.xml`을 두면 교착이 `DeadlockLoserDataAccessException`(6.0.3부터 deprecated)이 된다. 어느 쪽이든 부모 `PessimisticLockingFailureException`으로 잡는다. PG `55P03`(NOWAIT·lock_timeout)은 기본 경로에서 이 계열이 아니다(56번 §2).

### 10. 예방(wait-die·wound-wait) vs 탐지, 그리고 탐지기 밖의 교착

- 탐지: 그래프를 만들고 사이클이 생기면 희생자를 고른다. PostgreSQL·InnoDB의 행 락이 이 방식이다.
- 예방: 타임스탬프로 우선순위를 정해 **대기 방향을 한쪽으로만** 허용한다. 사이클이 처음부터 생기지 않는다(CMU L17).
  - wait-die: 요청자가 우선순위가 높으면(오래됐으면) 기다리고, 낮으면 스스로 중단한다.
  - wound-wait: 요청자가 우선순위가 높으면 쥔 쪽을 중단시키고, 낮으면 기다린다.
  - 재시작해도 원래 타임스탬프를 유지해 기아를 막는다.
- 탐지기가 못 보는 교착
  - 앱 락(Java `synchronized`·분산 락)과 DB 행 락이 섞인 사이클. DB는 자기 그래프만 본다.
  - InnoDB에서 `LOCK TABLES`나 다른 스토리지 엔진의 락이 낀 사이클(InnoDB가 테이블 락을 아는 조건 — `innodb_table_locks=1`이면서 `autocommit=0` — 이 아니면 못 찾는다, 17.7.5.2).
  - 대처: 모든 대기에 상한(`lock_timeout`, `innodb_lock_wait_timeout`, `tryLock(timeout)`)을 두고, 앱 락을 쥔 채 DB를 부르지 않는다.
