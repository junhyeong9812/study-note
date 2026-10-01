# distributed/14-two-phase-commit — 2PC: 코디네이터, prepare, in-doubt와 블로킹 — 정리 (힌트)

## 해결하는 문제

계좌 A는 DB 서버 1에, 계좌 B는 DB 서버 2에 있다. 이체는 두 서버에 한 번씩 쓴다.

```text
  서버 1:  UPDATE A SET bal = bal - 100   COMMIT ✓
  서버 2:  UPDATE B SET bal = bal + 100   ✗ (제약 위반·크래시·네트워크 끊김)
  → 100원이 사라졌다. 서버 1은 이미 커밋해서 혼자서는 되돌릴 수 없다
```

- 한 DB 안에서는 트랜잭션이 "전부 아니면 전무"를 준다([database/13](../../database/13-transactions-acid/2-summary.md)).
- 서버가 둘이면 각자 자기 몫만 원자적이다. 둘을 묶어 줄 장치가 따로 필요하다.
  - *원자적 커밋(atomic commit)*: 여러 노드가 한 트랜잭션에 참여할 때, 모두 커밋하거나 모두 중단하게 하는 문제(6.5840 L11).
- 2PC(two-phase commit)는 이 문제의 고전적 해법이다. "먼저 다 같이 약속하고, 그다음 한꺼번에 확정한다."

쉬운 예: 결혼식 주례가 두 사람에게 차례로 묻는다(DDIA 9장도 같은 비유를 쓴다).

- "하겠습니까?" → 둘 다 "예"라고 답한다. 이 순간부터 누구도 혼자 물릴 수 없다.
- 주례가 "부부가 되었음을 선언합니다"라고 말해야 확정이다.
- 주례가 "예"를 다 들은 뒤 선언 전에 쓰러지면? 두 사람은 결혼한 것인지 아닌지 모른 채 기다린다.

똑같은 구조다. 주례가 *코디네이터*, 두 사람이 *참가자*다.
- *코디네이터(transaction coordinator, TC)*: 트랜잭션을 이끌고 커밋·중단을 결정하는 쪽.
- *참가자(participant)*: 데이터 일부를 가진 서버. 자기 몫의 락과 변경을 관리한다.

실무 예:
- 샤딩된 DB의 다중 샤드 트랜잭션. Spanner는 Paxos로 복제한 그룹들 사이에서 2PC를 돈다(6.5840 L11·L12).
- XA로 DB 두 개, 또는 DB와 메시지 큐를 묶는 Java EE(JTA) 애플리케이션.
- PostgreSQL `PREPARE TRANSACTION`, MySQL `XA PREPARE` — 외부 트랜잭션 관리자가 쓰라고 있는 명령이다.

## 동작·원리

### 1. 정상 흐름 — 두 단계

```text
   TC                         참가자 A                    참가자 B
   │  (UPDATE …)  ───────────>│ 락 획득, 임시 변경          │
   │  (UPDATE …)  ──────────────────────────────────────────>│ 락 획득, 임시 변경
   │                          │                            │
   │ ── 1단계: PREPARE ──────>│ 디스크에 기록 → "YES"       │
   │ ── PREPARE ──────────────────────────────────────────>│ 디스크에 기록 → "YES"
   │ <───────── YES ──────────│                            │
   │ <───────── YES ────────────────────────────────────────│
   │                          │                            │
   │ [결정 로그에 COMMIT 기록 + fsync]  ← 커밋 지점            │
   │                          │                            │
   │ ── 2단계: COMMIT ───────>│ 확정, 락 해제 → ACK         │
   │ ── COMMIT ───────────────────────────────────────────>│ 확정, 락 해제 → ACK
   │ (ACK 전부 받으면 이 트랜잭션을 잊어도 된다)                    │
```

- 1단계(prepare): TC가 "커밋할 수 있나?"를 묻는다. 참가자는 커밋에 필요한 것을 **디스크에 남긴 뒤** YES라고 답한다.
  - 하나라도 NO면 TC는 ABORT를 보낸다.
- 2단계(commit): 전원 YES면 TC가 결정을 자기 로그에 먼저 쓰고, 그다음 COMMIT을 보낸다.
- 6.5840 L11의 정리: 참가자는 TC의 COMMIT을 받아야만 커밋한다. 그래서 "모두 동의하지 않으면 아무도 커밋하지 않는다."

### 2. 돌아올 수 없는 두 지점

```text
  참가자:  YES를 보낸 순간  → 이제 혼자 중단할 수 없다 (다른 참가자가 이미 커밋했을 수 있다)
                              혼자 커밋할 수도 없다   (다른 참가자가 NO였을 수 있다)
  TC:     결정을 로그에 쓴 순간 → 그 결정은 바뀌지 않는다. 재시작해도 그대로 다시 보낸다
```

- DDIA 9장은 이 둘을 2PC의 두 "돌아올 수 없는 지점(points of no return)"이라 부른다.
- 그래서 YES를 보낸 참가자는 TC의 결정이 올 때까지 **기다리는 것 말고 할 수 있는 게 없다**(6.5840 L11: "if B voted YES, it must block").
  - *in-doubt(불확실) 상태*: YES를 보냈지만 결과를 아직 모르는 참가자의 상태. 이 동안 그 트랜잭션의 락을 계속 쥔다.

### 3. 상태 기계

```text
  참가자                                  코디네이터
  ┌──────┐ PREPARE·불가 ┌─────────┐        ┌──────┐ 전원 YES ┌──────────────┐
  │ 작업중 │────────────>│ ABORTED │        │ 작업중 │────────>│ COMMIT 기록됨  │──> ACK 전부 → 잊음
  └──┬───┘             └─────────┘        └──┬───┘         └──────────────┘
     │ PREPARE·가능(디스크 기록)                 │ NO 하나 또는 타임아웃
     ▼                                        ▼
  ┌──────────┐ COMMIT  ┌───────────┐       ┌──────────────┐
  │ PREPARED │───────>│ COMMITTED │       │ ABORT(기록 생략 가능) │
  │(in-doubt)│ ABORT   ├───────────┤       └──────────────┘
  └──────────┘───────>│ ABORTED   │
                      └───────────┘
```

- 참가자가 PREPARE를 받기 **전**에 죽거나 타임아웃이면 혼자 중단해도 된다. TC가 아직 커밋을 결정할 수 없었기 때문이다(6.5840 L11).
- TC가 YES를 다 못 받았으면(누가 죽었거나 네트워크가 끊겼으면) 타임아웃 후 ABORT해도 된다. COMMIT을 보낸 적이 없기 때문이다.
- 위험한 칸은 하나다. **참가자 PREPARED + TC 결정 미도착.** 이 칸에서 블로킹이 생긴다.

### 4. 실패별로 무엇을 기억해야 하나 (6.5840 L11)

| 실패 | 필요한 것 |
|---|---|
| 참가자가 YES 뒤 크래시·재시작 | prepared 상태(락·임시 변경 포함)를 디스크에서 되살려 TC에 묻거나 재전송을 기다린다 |
| TC가 COMMIT 결정 뒤 크래시 | 결정을 디스크에 썼어야 한다. 재시작 후 COMMIT을 다시 보낸다. 참가자는 TID로 중복 COMMIT을 거른다 |
| TC가 결정 전 크래시 | 결정 기록이 없으니 중단해도 안전하다 |
| TC가 영영 안 돌아옴 | 참가자는 in-doubt로 계속 기다린다. 사람이 결정해야 한다 |

### 실험: prepare 뒤 코디네이터를 죽이면 참가자가 락을 쥐고 기다린다

- 환경: 전용 일회용 컨테이너 PostgreSQL 17.11 두 대(`max_prepared_transactions=20`, 기본값 0은 기능 꺼짐), Java 21 코디네이터. 2026-10-01.
- 코디네이터는 결정을 파일에 append + `SYNC`로 쓴다. `Runtime.halt()`로 프로세스를 즉시 죽인다.

```java
// TwoPC.java 핵심 (참가자 = PostgreSQL 두 대)
p1.createStatement().executeUpdate("UPDATE account SET bal = bal - 100 WHERE id = 'A'");
p2.createStatement().executeUpdate("UPDATE account SET bal = bal + 100 WHERE id = 'B'");
p1.createStatement().execute("PREPARE TRANSACTION '" + gid + "'");      // 1단계
p2.createStatement().execute("PREPARE TRANSACTION '" + gid + "'");
if (crash.equals("after-prepare")) Runtime.getRuntime().halt(1);         // ← 결정 전 죽음
log("COMMIT " + gid);                                                    // 커밋 지점(fsync)
if (crash.equals("after-decision")) Runtime.getRuntime().halt(1);        // ← 결정 후, 통지 전 죽음
p1.createStatement().execute("COMMIT PREPARED '" + gid + "'");           // 2단계
p2.createStatement().execute("COMMIT PREPARED '" + gid + "'");
```

(실험, PostgreSQL 17.11 2대 + Java 21, 2026-10-01) prepare 뒤 코디네이터 정지 — 다른 세션에서 본 참가자 1:

```text
 gid  |           prepared            |  owner
------+-------------------------------+----------
 tx-2 | 2026-10-01 00:56:56.320375+00 | postgres          ← pg_prepared_xacts: 주인 세션은 없는데 남아 있다

--- 다른 세션의 읽기 (MVCC: 막히지 않음, 옛 값)
 A  | 900

--- 다른 세션의 같은 행 쓰기 (lock_timeout 3s)
ERROR:  canceling statement due to lock timeout
CONTEXT:  while updating tuple (0,2) in relation "account"
real	0m3.113s

--- 락 보유자
 relation | RowExclusiveLock | t | 5/2 |        ← pid가 비어 있다: 연결된 세션이 아니라 prepared 트랜잭션이 쥐고 있다

--- 참가자 컨테이너 재시작 후
 tx-2 | 2026-10-01 00:56:56.320375+00          ← 재시작해도 그대로. 같은 행 쓰기도 다시 lock timeout
```

- 시각·`real` 시간·`virtualtransaction`·XID(`removable cutoff` 값)는 실행마다 다르다. 같은 날 다시 돌렸을 때 lock timeout까지 3.205초, 또 한 번은 3.198초였고, 나머지 결과(잔존·pid 없는 락·복구 결정·잔액)는 같았다.
- 관찰 1: **읽기는 막히지 않는다.** PostgreSQL은 MVCC라 옛 버전(900)을 읽는다([database/16](../../database/16-mvcc/2-summary.md)). 막히는 것은 같은 행을 **쓰는** 쪽이다. `lock_timeout`이 없으면 끝없이 기다린다.
- 관찰 2: prepared 상태는 **재시작을 견딘다.** 6.5840 L11이 말한 "YES 뒤에는 크래시 후에도 기억해야 한다"를 PostgreSQL이 그대로 구현한다.
- 관찰 3: 코디네이터가 돌아와야 풀린다. 재시작한 코디네이터의 복구 루틴이 결정 로그를 읽는다.

```text
--- 코디네이터 복구 (결정 기록 없음 → 중단)
recover sn-dw-w14-pg1: ROLLBACK PREPARED tx-2
recover sn-dw-w14-pg2: ROLLBACK PREPARED tx-2        → A 900, B 1100 (이체 전 값 유지)

=== 결정 기록 뒤 코디네이터 정지
[coord-log] COMMIT tx-3
!! coordinator halt (결정 후, 통지 전)
--- 복구 (결정 기록 COMMIT → 커밋)
recover sn-dw-w14-pg1: COMMIT PREPARED tx-3
recover sn-dw-w14-pg2: COMMIT PREPARED tx-3          → A 800, B 1200
```

- 결정 로그에 `COMMIT`이 **있으면** 커밋, **없으면** 중단했다. 결정 기록이 없는 경우를 중단으로 보는 방식이 *presumed abort*다(R* 시스템, Mohan·Lindsay·Obermarck 1986).
- 이 실험의 코디네이터 로그는 컨테이너에 마운트한 파일 하나다. 이 파일이 사라지면 tx-3 같은 in-doubt 트랜잭션을 누구도 올바르게 끝낼 수 없다.

### 5. 3PC는 왜 답이 아닌가, 그리고 합의로 감싸기

- *3PC(three-phase commit)*: 블로킹을 없애려고 단계를 하나 더 둔 변형. DDIA 9장에 따르면 3PC는 **지연 상한이 있는 네트워크와 응답 시간 상한이 있는 노드**를 가정한다.
  - 실제 네트워크는 지연 상한이 없다(비동기·부분동기 모델, [02](../02-system-and-failure-models/2-summary.md)). 그래서 실무에서는 거의 쓰지 않는다.
- 실무의 길: **코디네이터와 참가자를 합의로 복제한다.**
  - 6.5840 L11: TC와 각 서버를 Raft로 복제하고, 그 복제된 서비스들 사이에서 2PC를 돈다. 그러면 일부가 죽어도 진행할 수 있다. Spanner가 이 구조다.
  - 핵심: 2PC는 **모두가 각자 다른 일을 해야 할 때** 쓴다. Raft는 **모두가 같은 일을 해서 가용성을 높일 때** 쓴다. 2PC 자체는 가용성을 높이지 않는다. 참가자 전원이 살아 있어야 진행한다(6.5840 L11).

### 6. XA — 이기종 자원을 묶는 표준

- *XA*: X/Open이 정한, 트랜잭션 관리자와 자원(DB·메시지 큐) 사이의 2PC 인터페이스. Java에서는 JTA가 이것을 쓴다.
  - PostgreSQL 17: `PREPARE TRANSACTION` / `COMMIT PREPARED` / `ROLLBACK PREPARED`, 목록은 `pg_prepared_xacts`.
  - MySQL 8.4: `XA START` / `XA END` / `XA PREPARE` / `XA COMMIT`, 목록은 `XA RECOVER`(15.3.8.1).
- 계층을 구분한다.
  - 프로토콜(2PC)이 주는 보장: 결정이 나면 모두 같은 결정을 따른다.
  - 트랜잭션 관리자(Atomikos·Narayana 등)의 책임: 결정 로그를 안전하게 보관하고, 재시작 시 복구한다.
  - 애플리케이션 책임: 방치된 prepared 트랜잭션을 감시하고, 사람이 개입하는 절차를 둔다.
- Kafka 4.1 프로듀서 트랜잭션은 Kafka 안(여러 파티션·컨슈머 오프셋)의 원자성이다. DB와 함께 XA 2PC에 참가하는 자원이 아니다.
  - Kafka가 외부 2PC에 참가하게 하는 KIP-939는 상태가 "Accepted"다. kafka-clients 4.1.0에는 설정 `transaction.two.phase.commit.enable`과 `PreparedTxnState` 클래스가 들어 있다. 그러나 4.1.0의 공개 `KafkaProducer`에는 트랜잭션 메서드가 `initTransactions()`·`beginTransaction()`·`sendOffsetsToTransaction()`·`commitTransaction()`·`abortTransaction()`뿐이다. KIP가 정의한 `prepareTransaction()`·`completeTransaction()`이 없다(4.1.0 태그 소스 `KafkaProducer.java`). 그래서 4.1.0 클라이언트로는 애플리케이션이 Kafka를 외부 2PC 참가자로 쓸 수 없다.

## 쓰이는 자료구조·알고리즘

- **상태 기계** — 참가자(작업중 → PREPARED → COMMITTED/ABORTED)와 코디네이터(작업중 → 결정 기록 → 완료). 위 3절. 복구는 "지금 어느 상태인가"만 보고 다음 행동을 정한다.
- **append-only 결정 로그 + fsync** — 코디네이터의 커밋 지점은 "결정 로그가 디스크에 닿은 순간"이다. DB의 WAL과 같은 발상이다. [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)
- **2단계 락킹(strict 2PL)** — 참가자는 커밋·중단 뒤까지 락을 쥔다(6.5840 L11의 "strong strict two-phase locking"). 그래서 in-doubt 동안 락이 풀리지 않는다. 이름이 비슷한 2PL과 2PC는 다른 것이다. [database/15](../../database/15-two-phase-locking-and-deadlock/2-summary.md)
- **TID 기반 멱등** — 재시작한 TC가 COMMIT을 다시 보내도 참가자는 트랜잭션 ID(PostgreSQL의 `gid`)로 중복을 거른다.
- **presumed abort** — "결정 기록이 없으면 중단"이라는 규칙. ABORT를 로그에 쓰지 않아도 되고, 복구가 단순해진다. 위 실험의 `recover()`가 이 규칙이다.
- **합의(Raft·Paxos)로 복제한 코디네이터** — 블로킹을 줄이는 실무 해법. [11-consensus-raft](../11-consensus-raft/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 먼저 2PC가 꼭 필요한지 묻는다

```text
  같은 DB 안으로 모을 수 있나? ── 예 ──> 로컬 트랜잭션 하나 (가장 싸다)
          │ 아니오
  DB + 메시지 발행인가? ───────── 예 ──> outbox (16)
          │ 아니오
  서비스 경계를 넘는 업무 흐름인가? ─ 예 ──> 사가 (15)
          │ 아니오 (같은 팀이 운영하는 샤드·자원 사이, 짧은 트랜잭션)
  2PC (가능하면 합의로 복제한 코디네이터를 가진 DB 내장 기능: Spanner·CockroachDB 등)
```

- 6.5840 L11의 평가: 2PC는 느리고(왕복 여러 번·디스크 쓰기), prepare~commit 동안 락을 쥐며, TC가 죽으면 **락을 쥔 채** 무기한 블로킹할 수 있다. 그래서 보통 한 작은 영역 안에서만 쓴다. 은행 사이, 항공사 사이, 광역망 너머로는 쓰지 않는다.

### 2. XA를 쓴다면 — Java(JTA) 모양

```java
// Spring + JTA 트랜잭션 관리자(예: Atomikos·Narayana). 두 DataSource가 모두 XA DataSource여야 한다.
@Transactional   // JtaTransactionManager가 XA 2PC를 돈다
public void transfer(long from, long to, long amount) {
    shard1Jdbc.update("UPDATE account SET bal = bal - ? WHERE id = ?", amount, from);
    shard2Jdbc.update("UPDATE account SET bal = bal + ? WHERE id = ?", amount, to);
}   // 커밋 시: 두 자원에 prepare → 관리자 로그에 결정 기록 → commit
```

- 트랜잭션 관리자의 **로그 디렉터리를 영속 볼륨에** 둔다. 컨테이너 임시 디스크에 두면 재배포 한 번에 in-doubt를 풀 근거가 사라진다.
- PostgreSQL은 `max_prepared_transactions`를 0보다 크게 켜야 한다. 문서는 쓸 거라면 `max_connections` 이상으로 두라고 권한다(PostgreSQL 17 19.4).

### 3. 진단 명령

```sql
-- PostgreSQL 17: 방치된 prepared 트랜잭션
SELECT gid, prepared, owner, database, age(transaction) AS xid_age,
       now() - prepared AS waiting
FROM pg_prepared_xacts ORDER BY prepared;

-- 누가 기다리고 있나 (prepared가 쥔 락은 pid가 비어 있다)
SELECT pid, wait_event_type, wait_event, state, left(query, 60)
FROM pg_stat_activity WHERE wait_event_type = 'Lock';

-- 수동 해결 (결정 로그를 확인한 뒤에만!)
COMMIT PREPARED 'tx-3';     -- 또는 ROLLBACK PREPARED 'tx-2';
```

```sql
-- MySQL 8.4
XA RECOVER;                 -- prepared 상태의 XA 트랜잭션 목록
XA COMMIT 'xid';            -- 또는 XA ROLLBACK 'xid';
```

### 실험: 방치된 prepared 트랜잭션은 VACUUM도 막는다

(실험, PostgreSQL 17.11 전용 컨테이너, 2026-10-01) prepared 트랜잭션 하나를 둔 채 1,000행을 갱신하고 `VACUUM (VERBOSE)`:

```text
PREPARE TRANSACTION                       ← tx-held를 남겨 둔다
UPDATE 1000
tuples: 0 removed, 2000 remain, 1000 are dead but not yet removable
removable cutoff: 758, which was 2 XIDs old when operation ended
ROLLBACK PREPARED
tuples: 1000 removed, 1000 remain, 0 are dead but not yet removable
```

- prepared 트랜잭션도 오래 열린 트랜잭션처럼 vacuum cutoff를 붙잡는다. PostgreSQL 17 `PREPARE TRANSACTION` 문서의 Caution이 같은 경고를 한다. 오래 두면 VACUUM을 방해하고, 극단적으로는 XID wraparound를 막으려 DB가 멈출 수 있다.

## 장애 시나리오와 대처

### 1. 코디네이터 장애 → 참가자 블로킹 (커리큘럼 ⚠)

- **현상**: 특정 행을 갱신하는 요청만 전부 멈춘다. 같은 행을 읽는 요청은 정상이다.
- **보이는 형태**
  - 앱: 쓰기 요청 타임아웃. `lock_timeout`을 걸었다면 `ERROR: canceling statement due to lock timeout`.
  - DB: `pg_prepared_xacts`(MySQL은 `XA RECOVER`)에 오래된 항목. `pg_locks`에 pid 없는 락.
- **원인**: 참가자가 YES를 보낸 뒤 코디네이터가 죽었다. 참가자는 혼자 커밋도 중단도 할 수 없다(위 2절).
- **대처**
  - 1순위: 코디네이터(트랜잭션 관리자)를 살린다. 재시작하면 결정 로그대로 복구한다.
  - 코디네이터가 영영 못 돌아오면: 결정 로그나 다른 참가자의 결과를 확인해 사람이 `COMMIT PREPARED`/`ROLLBACK PREPARED`를 고른다. 어느 한 참가자라도 커밋됐다면 나머지도 커밋해야 한다.
  - 재발 방지: 코디네이터 로그를 영속·복제 저장소에 둔다. 가능하면 합의로 복제한 코디네이터를 가진 시스템을 쓴다.

### 2. 방치된 XA·prepared 트랜잭션 (커리큘럼 ⚠)

- **현상**: 몇 주 뒤 테이블이 부풀고, 특정 행 쓰기가 가끔 막힌다. 아무도 2PC를 쓴다고 기억하지 못한다.
- **보이는 형태**: `pg_prepared_xacts`의 `prepared`가 며칠 전. `VACUUM VERBOSE`에 `dead but not yet removable`. `age(datfrozenxid)`가 계속 오른다.
- **원인**: 트랜잭션 관리자 로그가 유실됐거나, 테스트 중 남긴 prepared 트랜잭션을 아무도 정리하지 않았다.
- **대처**: 확인 후 정리한다. 쓰지 않는다면 PostgreSQL 문서 권고대로 `max_prepared_transactions = 0`으로 꺼서 실수로 생기지 않게 한다. `pg_prepared_xacts` 건수와 나이에 알람을 건다.

### 3. 휴리스틱 결정으로 원자성이 깨진다

- **현상**: 급하게 락을 풀려고 DBA가 한 참가자에서 `ROLLBACK PREPARED`를 했다. 다른 참가자는 이미 커밋돼 있었다. 돈이 맞지 않는다.
- **보이는 형태**: JTA에서는 `HeuristicMixedException`·`HeuristicRollbackException` 같은 예외. 대사(reconciliation)에서 불일치.
- **원인**: in-doubt 참가자가 결정을 혼자 내렸다. DDIA 9장은 이런 "휴리스틱 결정"을 2PC의 약속을 깨는 비상구라고 설명한다.
- **대처**: 수동 결정 전에 결정 로그와 다른 참가자의 상태를 반드시 확인한다. 결정 절차를 런북으로 둔다. 깨졌다면 보상 거래로 맞춘다.

### 4. 참가자 하나가 느리거나 죽으면 전체가 멈춘다

- **현상**: 샤드 하나의 디스크가 느려지자 여러 샤드에 걸친 트랜잭션 전부의 지연이 늘었다.
- **보이는 형태**: prepare 응답 지연. 다른 샤드에서도 락 대기 증가.
- **원인**: 2PC는 **참가자 전원**의 YES가 필요하다. 가장 느린 참가자가 전체 지연을 정하고, 그동안 다른 참가자들은 락을 쥔다. 2PC는 가용성을 높이지 않는다(6.5840 L11).
- **대처**: 참가 범위를 줄인다(데이터 배치를 바꿔 단일 샤드 트랜잭션 비율을 높인다). TC가 PREPARE 응답 타임아웃 후 ABORT하게 한다. 그러면 결정 전 단계에서는 락이 풀린다.

## 핵심 문장

- 2PC는 "모두 YES면 커밋, 하나라도 NO면 중단"을 prepare·commit 두 단계로 보장한다.
- YES를 보낸 참가자는 혼자 커밋도 중단도 못 한다. 코디네이터의 결정이 올 때까지 락을 쥔 채 기다린다(in-doubt).
- 코디네이터의 커밋 지점은 결정을 디스크 로그에 쓴 순간이다. 그 로그가 사라지면 in-doubt를 바르게 끝낼 근거도 사라진다.
- prepared 상태는 재시작을 견딘다. 그래서 방치된 prepared 트랜잭션은 락과 vacuum cutoff를 계속 붙잡는다.
- 2PC는 원자성을 줄 뿐 가용성을 높이지 않는다. 블로킹은 3PC가 아니라 코디네이터를 합의로 복제해서 줄인다.

## 관련 주제·근거

- 선행
  - [database/13-transactions-acid](../../database/13-transactions-acid/2-summary.md) — 단일 DB 트랜잭션과 원자성
  - [database/15-two-phase-locking-and-deadlock](../../database/15-two-phase-locking-and-deadlock/2-summary.md) — 참가자가 쥐는 락
  - [03-partial-failure-and-timeouts](../03-partial-failure-and-timeouts/2-summary.md) — 타임아웃과 모호한 결과
- 후속·연결
  - [15-saga](../15-saga/2-summary.md) · [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 2PC를 피하는 두 길
  - [11-consensus-raft](../11-consensus-raft/2-summary.md) — 코디네이터 복제
  - [database/16-mvcc](../../database/16-mvcc/2-summary.md) — prepared 트랜잭션이 vacuum cutoff를 붙잡는 이유
  - [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md) — 결정 로그와 같은 발상
  - [systems/orchestration-choreography](../../systems/orchestration-choreography/2-summary.md) — 원고의 "2PC를 안 쓰는 이유" 절
- 강의·교재
  - MIT 6.5840 Spring 2026 Lecture 11 Distributed Transactions — 2PL, 2PC 정상 흐름, 참가자·TC 크래시별 기억할 것, "if B voted YES, it must block", 2PC vs Raft, Raft로 복제한 TC·서버 위의 2PC <https://pdos.csail.mit.edu/6.824/notes/l-2pc.txt> · 일정표 <https://pdos.csail.mit.edu/6.824/schedule.html>
  - DDIA 1판 9장 "Atomic Commit and Two-Phase Commit (2PC)" — 결혼식 비유, 두 개의 돌아올 수 없는 지점, 코디네이터 장애, 3PC의 가정 / "Distributed Transactions in Practice" — XA, in-doubt 동안의 락, 휴리스틱 결정
  - Mohan, Lindsay, Obermarck, "Transaction Management in the R* Distributed Database Management System", ACM TODS 1986 — presumed abort·presumed commit
- 제품 문서
  - PostgreSQL 17 `PREPARE TRANSACTION` — 외부 트랜잭션 관리자용, Caution(VACUUM 방해·락 유지·wraparound), 쓰지 않으면 `max_prepared_transactions=0` <https://www.postgresql.org/docs/17/sql-prepare-transaction.html>
  - PostgreSQL 17 19.4 Resource Consumption — `max_prepared_transactions` 기본 0, 쓸 거면 `max_connections` 이상 <https://www.postgresql.org/docs/17/runtime-config-resource.html>
  - MySQL 8.4 15.3.8.1 XA Transaction SQL Statements — `XA PREPARE`·`XA RECOVER` <https://dev.mysql.com/doc/refman/8.4/en/xa-statements.html>
  - KIP-939 Support Participation in 2PC (상태 Accepted) <https://cwiki.apache.org/confluence/display/KAFKA/KIP-939%3A+Support+Participation+in+2PC>
  - kafka-clients 4.1.0 `KafkaProducer.java` — 공개 트랜잭션 메서드 목록(`prepareTransaction` 없음) <https://raw.githubusercontent.com/apache/kafka/4.1.0/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java>
- 실험 목록
  - `TwoPC.java` + `exp14.sh` — 전용 PostgreSQL 17.11 컨테이너 2대, Java 21 코디네이터. 정상 2PC / prepare 뒤 halt(읽기 비차단·쓰기 lock timeout 3.1초·pid 없는 락·재시작 후 잔존·presumed abort 복구) / 결정 기록 뒤 halt(복구 시 COMMIT PREPARED)
  - `exp14b.sh` — 같은 환경. prepared 트랜잭션 하나가 1,000개 dead tuple 제거를 막고, `ROLLBACK PREPARED` 뒤 제거됨
