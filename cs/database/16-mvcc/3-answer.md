# database/16-mvcc — 정답

## 정답

### 1. MVCC가 푸는 것과 못 푸는 것

- 락만 쓰면 읽기는 S 락, 쓰기는 X 락이 필요하다. 둘은 충돌한다.
  - 긴 `SELECT sum(...)`이 S 락을 쥐면 이체의 `UPDATE`가 기다린다. 반대로 이체가 X 락을 쥐면 보고서가 기다린다.
- MVCC는 쓰는 쪽이 새 버전을 만들고, 읽는 쪽은 자기 스냅샷에 맞는 옛 버전을 읽게 한다.
  - 쓰기가 읽기를, 읽기가 쓰기를 막지 않는다(CMU L19).
- 같은 행을 둘이 **쓰면** 여전히 막는다. 행 락(15번)이 그대로 있다.

### 2. 버전 저장 위치

```text
  PostgreSQL 17 (같은 힙, 옛 → 새)
   lp1 [xmin=1574 xmax=1575 bal=100] ── t_ctid ──> lp3 [xmin=1575 xmax=0 bal=110]

  MySQL 8.4 InnoDB (레코드는 최신, 옛 모습은 undo)
   [id=1 bal=110 DB_TRX_ID=T2 DB_ROLL_PTR] ──> undo: [bal=100, 이전 ROLL_PTR]
```

- PostgreSQL: 갱신 = 옛 튜플의 `xmax`에 내 XID를 적고, 새 튜플(`xmin` = 내 XID)을 추가한다. 로컬 재현(예시, PostgreSQL 17.11)의 `pageinspect` 결과가 위 그림이다.
- InnoDB: 레코드를 제자리에서 고치고, 이전 값을 되살릴 정보를 update undo에 쓴다. `DB_ROLL_PTR`이 그 undo 레코드를 가리킨다(17.3).

### 3. 스냅샷 `100:105:101,103` 판정

| XID | 판정 | 이유 |
|---|---|---|
| 99 | 커밋이면 보임 | `xmin`(100)보다 작다 → 스냅샷 시점에 이미 끝남 |
| 101 | 안 보임 | `xip_list`에 있다 → 진행 중이었음 |
| 102 | 보임 | 구간 안, 목록에 없음 → 끝남 + 커밋 |
| 104 | 안 보임 | 구간 안, 목록에 없음 → 끝났지만 중단 |
| 105 | 안 보임 | `xmax` 이상 → 스냅샷 시점에 안 끝남 |

- 근거: PostgreSQL 17 9.27 표 9.83. 끝났는지는 스냅샷이, 커밋인지 중단인지는 `pg_xact`가 알려 준다.

### 4. RR 동시 갱신 — 두 엔진이 갈린다

- PostgreSQL 17: `ERROR: could not serialize access due to concurrent update`(40001). 트랜잭션 전체를 재시도해야 한다(13.2.2).
- MySQL 8.4: `UPDATE`는 스냅샷이 아니라 **최신 커밋 버전**(250)을 잠그고 고친다 → 251. 이어서 `SELECT`하면 자기가 고친 행이라 251이 보인다(17.7.2.3).
- 로컬 재현(예시, PostgreSQL 17.11 / MySQL 8.4.10)에서 둘 다 이렇게 나왔다.
- MySQL에서 lost update가 생기는 모양

```java
int bal = jdbc.queryForObject("SELECT bal FROM acc WHERE id = 2", Integer.class);  // 스냅샷: 200
jdbc.update("UPDATE acc SET bal = ? WHERE id = 2", bal + 1);                       // 201 → T2의 +50 소실
```

- 대처: `SET bal = bal + 1`처럼 DB에서 계산하거나, `SELECT ... FOR UPDATE`로 최신 값을 잠그며 읽는다(18번).

### 5. `VACUUM` vs `VACUUM FULL`

| | 일반 `VACUUM` | `VACUUM FULL` |
|---|---|---|
| 하는 일 | 죽은 버전 제거, 자리를 재사용 가능으로 표시 | 테이블을 새 파일로 다시 씀 |
| 파일 크기 | 보통 그대로(끝쪽 빈 페이지만 예외적으로 반납) | 최소 크기로 줄어듦 |
| 락 | 일반 읽기·쓰기와 공존(SHARE UPDATE EXCLUSIVE) | ACCESS EXCLUSIVE — 조회도 막힘 |
| 추가 디스크 | 없음 | 테이블 크기만큼 |

- 크기가 그대로인 것은 정상이다(24.1.2). 로컬 재현(예시, PostgreSQL 17.11)에서도 1만 행 제거 후 712 kB 그대로였다. 목표는 최소 크기가 아니라 "빈자리를 재사용하는 안정 상태"다.

### 6. `dead but not yet removable`

- 뜻: 이 버전들은 죽었지만, 아직 볼 수 있는 스냅샷이 있어서 못 지운다.
- 붙잡는 후보(24.1.5 복구 절차가 열거한 것 + 대기 서버)
  - 오래 열린 트랜잭션: `pg_stat_activity`의 `backend_xmin`·`backend_xid`(쓰기 트랜잭션은 xid만 있을 수 있다)·`xact_start`, `state = 'idle in transaction'`
  - 오래된 prepared transaction: `pg_prepared_xacts`
  - 오래된·버려진 복제 슬롯: `pg_replication_slots`의 `xmin`·`catalog_xmin`
  - `hot_standby_feedback=on`인 대기 서버의 긴 쿼리
- 로컬 재현(예시, PostgreSQL 17.11): RR 세션이 열려 있는 동안 `10000 are dead but not yet removable`, 닫은 뒤 `10000 removed`.
- 재발 방지: `idle_in_transaction_session_timeout`(17 기본 0 = 끔)을 역할 단위로 켜고, 트랜잭션 범위를 짧게 하고, 슬롯 지연에 알람을 건다.

### 7. HOT 조건과 효과

- 조건(65.7)
  1. 인덱스가 걸린 컬럼을 바꾸지 않는다(BRIN 같은 요약 인덱스는 예외).
  2. 옛 버전이 있는 페이지에 새 버전이 들어갈 자리가 있다.
- 효과
  - 새 인덱스 항목을 만들지 않는다. 인덱스는 원래 줄 번호를 계속 가리키고, 페이지 안 체인을 따라간다.
  - 중간 버전은 vacuum 없이 평소 조회 중에도 정리될 수 있다.
- 올리는 법: `fillfactor`를 낮춰 페이지에 빈자리를 남긴다. 확인은 `pg_stat_user_tables.n_tup_hot_upd`.

### 8. XID wraparound 거부

- XID는 32비트이고 2^32 모듈로로 비교한다. 어느 XID든 뒤로 약 20억은 과거, 앞으로 약 20억은 미래다(24.1.5).
- 20억 넘게 동결되지 않은 행은 갑자기 "미래에 만든 행"으로 보여 사라진다. 이를 막으려고 남은 XID가 약 4천만이면 경고, 약 3백만이면 새 XID 발급을 거부한다. 진행 중 트랜잭션과 읽기 전용 트랜잭션은 계속된다.
- 복구 순서(PostgreSQL 17 문서)
  1. 오래된 prepared transaction 정리
  2. 오래 열린 트랜잭션 종료
  3. 오래된 복제 슬롯 삭제
  4. 해당 DB에서 슈퍼유저로 `VACUUM`(시스템 카탈로그까지 처리해야 `datfrozenxid`가 전진한다. 가장 오래된 테이블부터 수동으로 해도 된다)
- 하지 말 것: `VACUUM FULL`(XID가 필요해 실패하고, 슈퍼유저면 XID를 소비해 위험을 키움), `VACUUM FREEZE`(필요 이상의 작업), 단일 사용자 모드로 내리기(보통 필요 없고 더 위험. 불필요한 테이블을 `TRUNCATE`·`DROP`하려는 경우만 예외).

### 9. InnoDB `History list length`

- 뜻: 커밋됐지만 아직 purge하지 못한 undo 로그 목록의 길이(17.8.9). 평소 수천 이하다.
- 원인: 오래된 read view가 update undo를 붙잡는다. 흔한 예는 `mysqldump --single-transaction` 중 대량 DML, 자동 커밋을 끄고 `SELECT` 후 커밋을 잊은 세션(17.8.9).
- 로컬 재현(예시, MySQL 8.4.10): read view 하나를 연 채 2,000번 갱신 → 6 → 2008, 닫은 뒤 10.
- 확인: `SHOW ENGINE INNODB STATUS`의 TRANSACTIONS 절, `information_schema.INNODB_TRX`의 `trx_started`, `INNODB_METRICS`의 `trx_rseg_history_len`.
- 해소: 오래된 트랜잭션을 끝낸다. `innodb_max_purge_lag`(기본 0)는 DML을 늦춰 purge가 따라잡게 하는 완화책일 뿐이다.

### 10. 앱 코드에 주는 교훈

- 트랜잭션이 스냅샷이나 XID를 쥐고 있는 동안 옛 버전이 붙잡힌다.
  - MySQL 기본 REPEATABLE READ·PostgreSQL REPEATABLE READ: 첫 읽기 스냅샷을 커밋까지 쥔다. 읽기 전용이어도 같다.
  - PostgreSQL 기본 READ COMMITTED: 문장이 끝나면 스냅샷을 놓는다. 다만 쓰기를 한 트랜잭션은 자기 XID가 cutoff를 붙잡고, 긴 문장 하나도 그동안 스냅샷을 쥔다.
- 그러므로
  - 트랜잭션 안에서 원격 호출·사용자 대기·긴 배치 루프를 하지 않는다([18번](../18-app-level-concurrency-patterns/2-summary.md), [24번](../24-transaction-boundaries-in-app-code/2-summary.md)).
  - 대량 처리는 짧은 트랜잭션 여러 개로 쪼갠다([34번](../34-large-backfill-and-batch-dml/2-summary.md)).
  - 커넥션 풀에서 `idle in transaction` 세션을 감시하고, 서버 측 상한(`idle_in_transaction_session_timeout`)을 둔다.
