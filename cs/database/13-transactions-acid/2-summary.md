# database/13-transactions-acid — 트랜잭션과 ACID의 정확한 뜻, 직렬화 가능성 — 정리 (힌트)

## 해결하는 문제

계좌 이체는 SQL 두 문장이다.

```sql
UPDATE account SET balance = balance - 100 WHERE id = 1;   -- 출금
UPDATE account SET balance = balance + 100 WHERE id = 2;   -- 입금
```

두 문장 사이에 세 가지 일이 끼어들 수 있다.

```text
  ① 서버가 죽는다          → 출금만 되고 입금은 안 된 상태가 남는다
  ② 두 번째 문장이 실패한다  → 역시 반쪽 상태
  ③ 다른 요청이 동시에 온다  → 출금만 된 중간 상태를 읽는다. 잔액을 SELECT로 읽고 계산값을
                               SET balance = ? 로 덮어쓰는 코드라면 한쪽 출금이 사라진다
```

트랜잭션은 이 세 가지를 DB가 대신 막아 주는 약속이다.\
여러 문장을 하나로 묶고, "전부 되거나 전부 안 되거나"와 "혼자 실행한 것처럼"을 보장한다.

쉬운 예: 은행 창구 직원이 전표 한 장에 출금과 입금을 같이 쓰고, 도장(커밋)을 찍어야 처리된다.

- 도장 전에 정전이 나면 전표는 없던 일이 된다.
- 다른 직원은 도장 찍힌 전표만 본다.

똑같은 구조다.\
실무 예: 주문 생성(주문 행 INSERT + 재고 UPDATE + 포인트 차감)을 한 트랜잭션에 넣는다. 셋 중 하나라도 실패해 롤백하면 셋 다 취소된다(MySQL InnoDB는 애플리케이션이 `ROLLBACK`을 불러야 한다 — 아래 3절).

그런데 이 약속에는 **경계**가 있다.

- 트랜잭션은 DB 안의 변경만 되돌린다. 이미 보낸 이메일, 이미 호출한 결제 API는 되돌리지 못한다(CMU 15-445 L16).
- ACID의 네 글자는 각각 뜻이 좁고 정확하다. 이 노트는 그 정확한 뜻과, 제품마다 다른 경계를 다룬다.

## 동작·원리

### 1. 트랜잭션의 경계 — 누가 BEGIN을 하나

```text
  명시적 트랜잭션                          자동 커밋(autocommit)
  BEGIN;                                  UPDATE ...;   ← 끝나는 순간 커밋
  UPDATE ...;                             UPDATE ...;   ← 또 따로 커밋
  UPDATE ...;
  COMMIT;   (또는 ROLLBACK;)               문장 하나 = 트랜잭션 하나
```

- *자동 커밋*: `BEGIN` 없이 보낸 문장을 각각 하나의 트랜잭션으로 보고, 끝나면 바로 커밋하는 모드다.
- MySQL 8.4: 세션 변수 `autocommit` 기본값이 1(켜짐)이다(로컬 재현 `@@autocommit = 1`, 17.7.2.2).
- PostgreSQL 17: `BEGIN`이 없으면 문장마다 자기 트랜잭션에서 실행되고 끝에서 암묵적으로 커밋된다(BEGIN 문서의 "autocommit" 모드). psql의 `\set AUTOCOMMIT off`는 **클라이언트**가 몰래 `BEGIN`을 보내 주는 기능이다.
- JDBC: `Connection`은 만들어질 때 자동 커밋 모드다. `setAutoCommit(false)`를 해야 여러 문장이 묶인다(`java.sql.Connection` 문서).

### 2. A — 원자성: "전부 아니면 전무"

```text
  BEGIN
    W(A)  출금 ─────┐
    W(B)  입금 ─────┤  COMMIT  → 둘 다 남는다
                    └  ABORT   → 둘 다 없던 일 (undo)
  중간에 서버가 죽으면 → 재시작 때 커밋 안 된 것은 없던 일
```

- 원자성은 동시성과 상관없다. "실패하면 **되돌릴 수 있다**"는 뜻이다. DDIA 1판 7장(2판 8장)은 "abortability(중단 가능성)가 더 나은 이름이었을 것"이라고 쓴다.
- 구현은 두 갈래다(CMU L16).
  - *로그*: 바꾸기 전 값을 undo 기록으로 남겨, 중단 시 되돌린다. 거의 모든 현대 시스템이 이 방식이다.
  - *섀도 페이징*: 바뀐 페이지의 복사본에 쓰고, 커밋 때 바꿔 끼운다. 드물다.
- MySQL 8.4 InnoDB는 undo 로그로 되돌린다. PostgreSQL은 새 버전 행을 쓰고, 중단된 트랜잭션이 만든 버전을 **보이지 않게** 처리한다(16번 MVCC).

**문장 하나가 실패했을 때 — 두 제품이 다르다** (로컬 재현)

```text
  CREATE TABLE acc2(id int PRIMARY KEY, bal int CHECK (bal >= 0));  -- (1,100), (2,0)

  BEGIN;
  UPDATE acc2 SET bal = bal + 50  WHERE id = 2;    -- 성공
  UPDATE acc2 SET bal = bal - 150 WHERE id = 1;    -- CHECK 위반으로 실패
  COMMIT;

  PostgreSQL 17.11                              MySQL 8.4.10 (InnoDB)
  ERROR: new row ... violates check constraint  ERROR 3819: Check constraint 'acc2_chk_1' is violated.
  (다음 문장) ERROR: current transaction is      (트랜잭션은 계속 열려 있다)
    aborted, commands ignored until end of
    transaction block   (SQLSTATE 25P02)
  COMMIT → ROLLBACK 으로 처리                    COMMIT → 성공한 첫 문장이 커밋됨
  결과: (1,100), (2,0)                           결과: (1,100), (2,50)   ← 50원이 생겼다
```

- PostgreSQL은 오류가 난 트랜잭션 전체를 실패 상태로 만든다. 이후 문장은 거부되고, `COMMIT`은 롤백으로 끝난다.
- MySQL InnoDB는 대부분의 오류에서 **실패한 문장만** 되돌린다. 문장 롤백으로는 그 문장이 잡은 락도 풀리지 않는다(17.20.5 InnoDB Error Handling). 트랜잭션을 끝낼지는 애플리케이션이 정한다. 오류를 무시하고 `COMMIT`하면 반쪽이 커밋된다. 교착(1213)처럼 트랜잭션 전체를 롤백하는 오류도 있다(15번).
- 그래서 "원자성"은 "DB가 알아서 전부 되돌린다"가 아니다. **롤백을 부르는 것은 애플리케이션 몫**일 때가 있다.

### 3. C — 일관성: 제약은 DB가, 규칙은 애플리케이션이

```text
  DB가 지켜 주는 것 (선언한 것만)            애플리케이션이 지켜야 하는 것
  NOT NULL, UNIQUE, PRIMARY KEY            "출금 합 = 입금 합"
  FOREIGN KEY, CHECK (bal >= 0)            "당직자는 항상 1명 이상"
  트리거                                    "하루 한도 100만 원"
```

- CMU L16은 둘을 나눈다. *데이터베이스 일관성*은 무결성 제약을 지키는 것이다. *트랜잭션 일관성*("시작 때 일관적이면 끝날 때도 일관적")은 **애플리케이션의 책임**이다.
- DDIA 1판 7장은 C가 사실 DB의 성질이 아니라 애플리케이션의 성질이라서 "ACID에 속하지 않는다"고까지 쓴다. DB는 A·I·D를 제공하고, 애플리케이션은 그것을 이용해 C를 만든다.
  - 2판(8장 "Transactions")은 표현을 누그러뜨렸다. "C는 애플리케이션이 DB를 어떻게 쓰느냐에 달린 경우가 많고, DB 혼자의 성질이 아니다"라고 쓴다.
- 즉 C를 지키는 가장 확실한 방법은 **규칙을 제약으로 선언**하는 것이다. 선언하지 않은 규칙은 격리 수준에 따라 동시 요청에 깨진다(14번 write skew).

### 4. I — 격리: 동시에 돌아도 혼자 돈 것처럼

```text
  직렬 실행 (정답의 기준)               끼어든 실행 (실제)
  T1: R(A) W(A)                        T1: R(A)            W(A)
  T2:            R(A) W(A)             T2:       R(A) W(A)
                                       → 결과가 어떤 직렬 순서와 같으면 "직렬화 가능"
```

- *스케줄*: 여러 트랜잭션의 연산이 실제로 실행된 순서다.
- *직렬화 가능(serializable)*: 그 스케줄의 결과가 **어떤** 직렬 순서의 결과와 같다. 어느 순서인지는 상관없다(CMU L16).
- *충돌*: 서로 다른 트랜잭션이 **같은 대상**에 접근하고, **적어도 하나가 쓰기**인 두 연산이다. 읽기-읽기는 충돌이 아니다.

**충돌 그래프(선행 그래프)로 판정한다**

```text
  스케줄:  R1(A)  R2(A)  W1(A)  W2(A)          ← 재고 10을 둘 다 읽고 각자 9로 씀

  간선 규칙: Ti의 연산이 Tj의 충돌 연산보다 먼저면  Ti → Tj
     R1(A) … W2(A)  →  T1 → T2
     R2(A) … W1(A)  →  T2 → T1
     W1(A) … W2(A)  →  T1 → T2

        T1 ⇄ T2      사이클 있음 → 충돌 직렬화 불가능  (= 갱신 손실)

  비교: R1(A) W1(A) R2(A) W2(A)  → 간선 T1 → T2 뿐 → 사이클 없음 → T1, T2 순서와 같다
```

- 규칙: 충돌 그래프에 **사이클이 없으면, 그리고 그때만** 충돌 직렬화 가능이다(CMU L16).
- 실제 DB는 매번 그래프를 그리지 않는다. 대신 락(15번), 버전(16번), 검증(17번) 같은 프로토콜로 사이클이 생기지 않게 막는다.
- 격리를 얼마나 강하게 할지는 **격리 수준**으로 고른다. 대부분의 DB 기본값은 직렬화 가능보다 약하다(PostgreSQL 17 기본 `read committed`, MySQL 8.4 InnoDB 기본 `REPEATABLE READ`, 로컬 재현). 어떤 이상 현상을 허용하는지는 14번이 다룬다.

### 5. D — 지속성: 커밋했다고 답했으면 살아남는다

```text
  COMMIT 요청
     │
     ▼  WAL(redo 로그)에 커밋 기록을 쓴다
     ▼  fsync — 디스크까지 내려보낸다          ← 여기가 지속성의 근거
     ▼  클라이언트에 "COMMIT" 응답
  (데이터 페이지 자체는 나중에 천천히 쓴다 → 19번 WAL)

  서버 재시작 → 로그를 다시 재생 → 커밋된 것은 복구, 안 된 것은 버림
```

| 설정 (기본값) | 뜻 |
|---|---|
| PostgreSQL 17 `synchronous_commit = on` | 커밋 응답 전에 WAL을 디스크로 내린다 |
| PostgreSQL `fsync = on` | 끄면 OS·하드웨어 장애 때 **임의의 손상**까지 가능하다 |
| MySQL 8.4 `innodb_flush_log_at_trx_commit = 1` | 커밋마다 redo 로그를 쓰고 플러시한다. "완전한 ACID에 필요" |
| MySQL 8.4 `sync_binlog = 1` | 커밋 전에 바이너리 로그를 디스크로 동기화한다 |

- `synchronous_commit = off`(비동기 커밋)는 "최근 트랜잭션 몇 개를 잃을 수 있다"와 맞바꾼 속도다. 손상은 아니고 **유실**이다. 위험 구간은 최대 `wal_writer_delay`의 3배다(PostgreSQL 28.4).
- `innodb_flush_log_at_trx_commit = 0 또는 2`는 대략 1초에 한 번 플러시한다. 충돌 시 약 1초분의 트랜잭션을 잃을 수 있다(0은 mysqld 크래시에도, 2는 OS 크래시·정전 때만 — 19번). 1초 주기도 정확히 보장되지는 않고, 주기는 `innodb_flush_log_at_timeout`(기본 1초)으로 바뀐다(17.14).
- 지속성은 "그 서버의 디스크"까지다. 디스크가 통째로 사라지는 것은 복제·백업(20·32번)의 몫이다. `fsync`가 정말 디스크까지 가는지는 OS·장치에 달렸다([os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md)).

### 6. 네 글자의 한 줄 요약

```text
  A  실패하면 되돌릴 수 있다          (동시성 얘기가 아니다)
  C  선언한 제약은 DB가, 나머지는 앱이   (DB 혼자 보장 못 한다)
  I  동시에 돌아도 어떤 직렬 순서와 같게  (강도는 격리 수준으로 조절 → 14번)
  D  커밋 응답 = 로그가 디스크에 있다    (설정으로 약해질 수 있다)
```

## 쓰이는 자료구조·알고리즘

- **충돌 그래프 + 사이클 탐지** — 트랜잭션이 노드, 충돌 순서가 간선이다. 사이클이 없으면 위상 정렬 순서가 곧 동등한 직렬 순서다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **undo 로그** — 바꾸기 전 값을 쌓아 두는 로그. 중단 시 역순으로 되돌린다. InnoDB는 이것을 MVCC의 옛 버전으로도 쓴다(16번).
- **WAL(선행 기록 로그)** — 추가만 하는 순차 로그. 커밋 = 로그 한 줄이 디스크에 닿은 것. 19번에서 다룬다.
- **트랜잭션 상태 기계** — 활성 → (부분 커밋) → 커밋 / 실패 → 중단. PostgreSQL의 "aborted" 상태가 `25P02`로 드러난다.

## 적용 — 풀어나가는 법

### 1. 경계를 코드에서 명시한다 (JDBC)

```java
try (Connection con = dataSource.getConnection()) {
    con.setAutoCommit(false);                        // 기본값은 true
    try (PreparedStatement out = con.prepareStatement(
             "UPDATE account SET balance = balance - ? WHERE id = ? AND balance >= ?");
         PreparedStatement in = con.prepareStatement(
             "UPDATE account SET balance = balance + ? WHERE id = ?")) {
        out.setLong(1, 100); out.setLong(2, 1); out.setLong(3, 100);
        if (out.executeUpdate() != 1) throw new IllegalStateException("잔액 부족");
        in.setLong(1, 100); in.setLong(2, 2);
        in.executeUpdate();
        con.commit();
    } catch (Exception e) {
        con.rollback();                               // MySQL에서는 이것이 없으면 반쪽이 남을 수 있다
        throw e;
    }
}
```

- 오류가 나면 **항상** 명시적으로 `rollback()`한다. PostgreSQL은 어차피 커밋을 거부하지만, MySQL은 실패한 문장만 되돌리고 트랜잭션을 열어 둔다.
- 풀에서 꺼낸 커넥션은 반납 전에 자동 커밋 상태를 되돌려야 한다. HikariCP는 반납(`close()`) 때 커밋 안 된 작업이 있으면 롤백하고, 바뀐 자동 커밋·격리 수준·읽기 전용 설정을 풀 기본값으로 되돌린다(`ProxyConnection.close()`, `PoolBase.resetConnectionState()`). 다른 풀은 그 풀의 문서로 확인한다.

### 2. Spring `@Transactional`

```java
@Transactional
public void placeOrder(OrderCommand cmd) {
    orderRepository.save(Order.from(cmd));
    stockRepository.decrease(cmd.itemId(), cmd.qty());
    // 메일은 여기서 보내지 않는다 → 커밋 뒤 이벤트로
    events.publishEvent(new OrderPlaced(cmd.orderId()));
}

@TransactionalEventListener   // 기본 phase = AFTER_COMMIT
public void sendMail(OrderPlaced e) { mailer.send(e.orderId()); }
```

- 기본 롤백 규칙: 언체크 예외(`RuntimeException`)와 `Error`면 롤백, 체크 예외면 **커밋**한다(Spring 문서 "Rolling Back a Declarative Transaction"). 자세한 함정은 24번.
- 트랜잭션 안에서 외부 부수 효과를 일으키지 않는다. 커밋 뒤 훅(`AFTER_COMMIT`)이나 아웃박스 테이블로 옮긴다. [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md)

### 3. 지금 열려 있는 트랜잭션 보기

```sql
-- PostgreSQL: BEGIN 해 놓고 아무것도 안 하는 세션
SELECT pid, state, xact_start, now() - xact_start AS age, query
FROM pg_stat_activity WHERE state LIKE 'idle in transaction%';

-- MySQL 8.4 InnoDB
SELECT trx_id, trx_state, trx_started, trx_mysql_thread_id, trx_query
FROM information_schema.innodb_trx ORDER BY trx_started;
```

- 오래 열린 트랜잭션은 락을 쥐고, 옛 버전 정리(vacuum·purge)를 막는다(16번). PostgreSQL은 `idle_in_transaction_session_timeout`으로 끊을 수 있다(22번).

### 4. 설정 확인

```sql
-- PostgreSQL
SHOW default_transaction_isolation;   -- read committed
SHOW synchronous_commit;              -- on
-- MySQL
SELECT @@autocommit, @@transaction_isolation, @@innodb_flush_log_at_trx_commit, @@sync_binlog;
-- 로컬 재현(8.4.10): 1, REPEATABLE-READ, 1, 1
```

## 장애 시나리오와 대처

### 1. 롤백됐는데 메일은 나갔다 (⚠ 트랜잭션 경계 밖 외부 호출)

- **현상**: 주문 실패 알림을 받은 고객이 "주문 완료" 메일도 받았다. 또는 결제 API는 승인됐는데 주문 행은 없다.
- **보이는 형태**: 애플리케이션 로그에 메일 발송 성공 → 이어서 `DataIntegrityViolationException` 등으로 롤백. DB에는 주문이 없다.
- **원인**: 트랜잭션 안에서 메일·HTTP를 호출했다. DB는 자기 변경만 되돌린다. 바깥 세계에 나간 효과는 되돌릴 수 없다(CMU L16).
- **대처**
  - 부수 효과를 커밋 **뒤**로 옮긴다: `@TransactionalEventListener(AFTER_COMMIT)`, 아웃박스 테이블 + 별도 발송기.
  - 결제처럼 먼저 불러야 하는 외부 호출은 멱등 키와 보상 트랜잭션(취소 API)을 설계한다. 분산 쪽 주제다.
  - 트랜잭션 안의 외부 호출은 커넥션과 락을 그 시간만큼 쥐게 만든다. 풀 고갈로도 번진다(21·24번).

### 2. "트랜잭션인 줄 알았다" — 자동 커밋 가정 (⚠ autocommit 가정)

- **현상**: 두 번째 UPDATE가 실패했는데 첫 번째는 이미 반영돼 있다.
- **보이는 형태**: 오류 로그는 두 번째 문장 하나뿐인데 첫 번째 변경은 남아 있다. 직접 JDBC를 쓴 코드라면 예외 처리에서 부른 `rollback()`이 오히려 `SQLException`을 던진다. `Connection.rollback()` 명세가 자동 커밋 모드에서 호출하면 예외라고 정한다.
- **원인**: 커넥션이 자동 커밋 모드였다. 문장마다 이미 커밋됐다. `setAutoCommit(false)` 누락, 또는 `@Transactional`이 프록시를 안 거쳐 적용되지 않았다(24번: 자기 호출).
- **대처**: 경계를 코드에서 명시한다. 통합 테스트에서 "두 번째 문장 실패 시 첫 번째가 없어야 한다"를 직접 검증한다. 반대 방향 사고도 있다. MySQL에서 `autocommit=0` 세션이 커밋을 잊으면 트랜잭션이 끝없이 열려 락을 쥔다.

### 3. MySQL에서 오류를 삼키고 커밋 → 반쪽 커밋

- **현상**: 잔액 합계가 맞지 않는다. 돈이 생기거나 사라졌다.
- **보이는 형태** (로컬 재현, MySQL 8.4.10): `ERROR 3819 … Check constraint 'acc2_chk_1' is violated.` 뒤 `COMMIT`이 성공하고, 성공한 첫 문장만 반영됐다.
- **원인**: InnoDB는 오류 난 **문장만** 롤백한다. 애플리케이션이 예외를 잡아 로그만 남기고 커밋했다.
- **대처**: 예외 경로는 반드시 `ROLLBACK`. 일부 실패를 허용해야 하면 `SAVEPOINT`로 범위를 명시한다. 락 대기 시간 초과(1205)도 기본 설정에서는 문장만 롤백된다(`innodb_rollback_on_timeout = OFF` 기본, 17.14).

### 4. PostgreSQL에서 모든 쿼리가 `25P02`로 실패한다

- **현상**: 한 요청에서 오류가 난 뒤, 같은 트랜잭션의 이후 쿼리가 전부 실패한다.
- **보이는 형태**: `ERROR: current transaction is aborted, commands ignored until end of transaction block` (SQLSTATE `25P02`, 로컬 재현).
- **원인**: 트랜잭션 안에서 한 문장이 실패했다. PostgreSQL은 그 트랜잭션을 실패 상태로 두고, `ROLLBACK`(또는 `ROLLBACK TO SAVEPOINT`) 전까지 모든 명령을 거부한다. 애플리케이션이 첫 예외를 잡아 삼키고 계속 쿼리했다.
- **대처**: 첫 예외에서 트랜잭션을 롤백한다. "없으면 INSERT, 중복이면 무시"처럼 실패를 예상하는 문장은 `SAVEPOINT`로 감싸거나 `INSERT … ON CONFLICT DO NOTHING`으로 실패 자체를 없앤다.

### 5. 정전 뒤 "커밋 완료"였던 주문이 사라졌다

- **현상**: 서버가 비정상 종료된 뒤, 클라이언트는 성공 응답을 받았는데 DB에 없는 트랜잭션이 몇 건 있다.
- **보이는 형태**: 재시작 로그는 정상 복구로 끝난다. 손상 경고는 없다. 마지막 1초 안팎의 커밋만 없다.
- **원인**: 지속성을 약하게 설정했다. PostgreSQL `synchronous_commit = off`, MySQL `innodb_flush_log_at_trx_commit = 0 또는 2`. 또는 저장장치가 쓰기 캐시를 거짓으로 비웠다고 보고했다.
- **대처**: 돈·주문 같은 테이블은 기본값(on / 1 / 1)을 유지한다. 필요하면 PostgreSQL은 `SET LOCAL synchronous_commit = off`로 **덜 중요한 트랜잭션만** 약하게 한다(문서가 트랜잭션 단위 설정을 허용한다). 저장장치는 쓰기 캐시의 전원 보호 여부를 확인한다. MySQL `sync_binlog = 0`은 이와 별개다. 커밋됐지만 바이너리 로그에 없는 트랜잭션이 생겨 복제본·binlog 기반 복구와 어긋날 수 있다(19.1.6.4).

## 핵심 문장

- 트랜잭션은 여러 문장을 "전부 아니면 전무"로 묶고, 동시에 돌아도 혼자 돈 것처럼 보이게 하는 약속이다. 범위는 DB 안의 변경뿐이다.
- A는 동시성이 아니라 "실패하면 되돌릴 수 있음"이다. 다만 MySQL InnoDB는 실패한 문장만 되돌리므로 롤백은 애플리케이션이 부른다.
- C는 DB 혼자 보장하지 못한다. 선언한 제약만 DB가 지키고, 나머지 규칙은 애플리케이션이 A·I를 이용해 지킨다.
- I의 기준은 직렬화 가능성이다. 충돌 그래프에 사이클이 없으면 충돌 직렬화 가능이다. 실제 기본 격리 수준은 이보다 약하다.
- D는 "커밋 응답 = 로그가 디스크에 있음"이다. `synchronous_commit`·`innodb_flush_log_at_trx_commit`로 약해질 수 있다. `sync_binlog`는 바이너리 로그 쪽 지속성이다.
- 자동 커밋은 MySQL과 JDBC의 기본값이다. 경계를 코드에서 명시하지 않으면 문장마다 커밋된다.

## 관련 주제·근거

- 선행
  - database `04-sql-joins-and-aggregation` — SQL 기본 → [../04-sql-joins-and-aggregation/2-summary.md](../04-sql-joins-and-aggregation/2-summary.md)
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) — 읽고-고치고-쓰기 경합과 임계 구역
- 후속·연결
  - database `14-isolation-levels-and-anomalies` — 격리 수준과 이상 현상 → [../14-isolation-levels-and-anomalies/2-summary.md](../14-isolation-levels-and-anomalies/2-summary.md)
  - database `15-two-phase-locking-and-deadlock` → [../15-two-phase-locking-and-deadlock/2-summary.md](../15-two-phase-locking-and-deadlock/2-summary.md)
  - database `16-mvcc` → [../16-mvcc/2-summary.md](../16-mvcc/2-summary.md)
  - database `19-wal-and-logging` → [../19-wal-and-logging/2-summary.md](../19-wal-and-logging/2-summary.md)
  - database `24-transaction-boundaries-in-app-code` → [../24-transaction-boundaries-in-app-code/2-summary.md](../24-transaction-boundaries-in-app-code/2-summary.md)
  - [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md) · [os/23-crash-consistency-and-journaling](../../os/23-crash-consistency-and-journaling/2-summary.md)
  - [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md) — 커밋과 메시지 발행을 묶는 법
  - 문법 쪽: [sql/55 트랜잭션 경계·SAVEPOINT](../../../languages/sql/syntax/55-transaction-boundaries-commit-rollback-savepoint/2-summary.md)
- 교재
  - CMU 15-445/645 Fall 2024 Lecture #16 "Concurrency Control Theory" — ACID 정의, 로그 vs 섀도 페이징, 데이터베이스 일관성 vs 트랜잭션 일관성(앱 책임), 충돌·충돌 직렬화·선행 그래프, "이메일은 되돌릴 수 없다" <https://15445.courses.cs.cmu.edu/fall2024/>
  - M. Kleppmann, 『Designing Data-Intensive Applications』 1판 7장 "Transactions" — ACID의 의미(abortability, C는 앱의 성질이라 "ACID에 속하지 않는다"). 1판 문구는 1판 번역본(Vonng/ddia `content/v1/ch7.md`: "或许 可中止性（abortability） 是更好的术语", "因此，字母 C 不属于 ACID")으로, 영어 원문 표현은 2판 8장(`content/en/ch8.md`: "Perhaps *abortability* would have been a better term than *atomicity*")으로 확인했다. 2판은 C에 대해 "not a property of the database alone"으로 완화했다. <https://github.com/Vonng/ddia>
  - HikariCP 소스 `ProxyConnection.java`(`close()`에서 커밋 안 된 작업 롤백)·`PoolBase.java`(`resetConnectionState`) <https://github.com/brettwooldridge/HikariCP>
- PostgreSQL 17 문서
  - 3.4 Transactions <https://www.postgresql.org/docs/17/tutorial-transactions.html> · BEGIN <https://www.postgresql.org/docs/17/sql-begin.html> · 13.2 Transaction Isolation(기본 read committed, 시퀀스는 롤백되지 않음) <https://www.postgresql.org/docs/17/transaction-iso.html>
  - 28.4 Asynchronous Commit(유실 vs 손상, 위험 구간 3 × `wal_writer_delay`) <https://www.postgresql.org/docs/17/wal-async-commit.html>
  - 부록 A 오류 코드(`25P02 in_failed_sql_transaction`, `23514 check_violation`) <https://www.postgresql.org/docs/17/errcodes-appendix.html>
- MySQL 8.4 Reference Manual
  - 17.20.5 InnoDB Error Handling(오류는 대개 문장만 롤백, 문장 롤백은 락을 풀지 않음) <https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html>
  - 15.3.1 START TRANSACTION, COMMIT, and ROLLBACK <https://dev.mysql.com/doc/refman/8.4/en/commit.html> · 17.7.2.2 autocommit, Commit, and Rollback <https://dev.mysql.com/doc/refman/8.4/en/innodb-autocommit-commit-rollback.html>
  - 17.14 InnoDB System Variables(`innodb_flush_log_at_trx_commit` 기본 1 "required for full ACID compliance", `innodb_rollback_on_timeout` 기본 OFF) <https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html>
  - 19.1.6.4 Binary Logging Options(`sync_binlog` 기본 1) <https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html>
- Java·Spring
  - Java SE `java.sql.Connection`(기본 자동 커밋 모드, `setAutoCommit`) <https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/Connection.html>
  - Spring Framework 문서 "Rolling Back a Declarative Transaction", `@TransactionalEventListener`(기본 `AFTER_COMMIT`)
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10, 전용 DB `w12`): CHECK 위반 뒤 COMMIT — PostgreSQL은 25P02·전체 롤백, MySQL은 첫 문장만 커밋, 두 제품의 기본 격리 수준·지속성 설정값
