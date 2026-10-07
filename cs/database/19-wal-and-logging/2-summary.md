# database/19-wal-and-logging — WAL: 로그 먼저 쓰기, group commit, no-force/steal — 정리 (힌트)

## 해결하는 문제

DB는 페이지를 메모리(버퍼 풀)에서 고치고 나중에 디스크에 쓴다. 그 사이에 전원이 나가면 두 가지가 깨질 수 있다.

```text
  메모리(버퍼 풀)              디스크(데이터 파일)
  [페이지 A: 커밋된 변경]   ──X  아직 안 씀   → 커밋했다고 답했는데 사라짐 (지속성 위반)
  [페이지 B: 미커밋 변경]   ───> 이미 씀      → 중단된 트랜잭션의 흔적이 남음 (원자성 위반)
```

- 가장 단순한 해법은 "커밋할 때 바뀐 페이지를 전부 디스크에 쓰고(force), 미커밋 페이지는 절대 쓰지 않는다(no-steal)"이다. 느리다. 흩어진 페이지를 커밋마다 무작위로 써야 한다.
- 실제 DB의 해법: 바뀐 **내용을 로그에 먼저** 순차로 쓰고, 페이지는 나중에 아무 때나 쓴다.
  - *WAL(Write-Ahead Logging)*: 데이터 파일을 바꾸기 **전에**, 그 변경을 설명하는 로그 레코드를 영구 저장소에 먼저 기록하는 규칙.

쉬운 예: 가계부다.
- 지갑(데이터 파일)을 매번 정리하지 않는다.
- 대신 쓴 돈을 공책(로그)에 **먼저** 적는다. 공책은 한 줄씩 뒤에 붙이기만 하니 빠르다.
- 지갑을 잃어버려도(크래시) 공책을 처음부터 따라 하면 지금 상태를 되살린다.

똑같은 구조다.\
PostgreSQL은 이 로그를 WAL(`pg_wal/`), MySQL InnoDB는 redo log(`#innodb_redo/`)라 부른다.

실무 예:
- 벤치마크를 빠르게 하려고 PostgreSQL `fsync = off`로 운영했다가 정전 뒤 DB가 깨졌다.
- 복제 슬롯을 방치해 `pg_wal`이 디스크를 채우고 DB가 멈췄다.
- MySQL `innodb_flush_log_at_trx_commit = 2`로 바꾼 뒤 OS 크래시에서 마지막 약 1초의 커밋이 사라졌다.

## 동작·원리

### 1. WAL 규칙 두 개

```text
  시간 →
  UPDATE  ─ ① 로그 레코드를 로그 버퍼에 추가 (LSN 부여)
          ─ ② 버퍼 풀의 페이지를 고치고, 페이지 헤더에 그 LSN을 적는다
  COMMIT  ─ ③ COMMIT 레코드까지 로그를 디스크에 flush(fsync)   ← 여기서 "커밋 성공" 응답
  나중에  ─ ④ 페이지를 디스크에 쓰기 전에: 로그가 그 페이지 LSN까지 flush됐는지 확인 → 아니면 먼저 flush
```

- 규칙 1(커밋): 트랜잭션의 로그 레코드가 모두 영구 저장소에 있어야 커밋을 알린다(CMU 15-445 L20). 동기 커밋 기준이다. PostgreSQL `synchronous_commit = off`·MySQL `innodb_flush_log_at_trx_commit = 0/2`는 flush 전에 응답한다(4절). 규칙 2는 그때도 지킨다(28.4).
- 규칙 2(페이지 쓰기): 페이지를 디스크에 쓰기 전에 그 페이지를 바꾼 로그가 먼저 디스크에 있어야 한다.
  - PostgreSQL 17 소스 `bufmgr.c`의 `FlushBuffer`가 `XLogFlush(페이지 LSN)`를 먼저 부른다. 주석: "the basic WAL rule that log updates must hit disk before any of the data-file changes they describe do".
- *LSN(Log Sequence Number)*: 로그 안의 위치. 단조 증가하는 바이트 오프셋이다(PostgreSQL 28.6, MySQL 17.6.5).

로컬 재현(예시, PostgreSQL 17.11) — `UPDATE` 한 번의 WAL 레코드를 `pg_waldump`로 봤다.

```text
  rmgr: Heap        tx: 310942, lsn: 1/2C227A90, desc: HOT_UPDATE old_off: 5, new_off: 6, blkref #0: rel 1663/26080/...
  rmgr: Transaction tx: 310942, lsn: 1/2C227AD8, desc: COMMIT 2026-09-30 22:36:46 UTC
```

- 변경 레코드 하나, 커밋 레코드 하나. 페이지 헤더의 `lsn`(`pageinspect`의 `page_header`)은 마지막으로 이 페이지를 바꾼 레코드 위치를 가리켰다.

### 2. steal / no-force — 버퍼 풀 정책

```text
                 FORCE (커밋 때 페이지 강제 기록)      NO-FORCE (커밋 때 안 씀)
  NO-STEAL       가장 단순. undo·redo 불필요            redo 필요
  (미커밋 페이지   느림, 트랜잭션이 메모리에 다 들어가야
   못 씀)
  STEAL          undo 필요                              undo + redo 필요  ← 대부분의 DB (WAL)
  (미커밋 페이지                                         런타임 가장 빠름, 복구는 가장 느림
   써도 됨)
```

- *steal*: 커밋 전인 트랜잭션의 더러운 페이지를 디스크에 써도 된다. 버퍼 풀이 모자랄 때 필요하다. 크래시하면 그 흔적을 **되돌려야(undo)** 한다.
- *force*: 커밋할 때 바뀐 페이지를 모두 디스크에 써야 한다. no-force면 크래시 뒤 로그로 **다시 해야(redo)** 한다.
- 대부분의 DB는 STEAL + NO-FORCE를 쓴다(CMU L20).
  - PostgreSQL은 튜플에 xmin·xmax가 있어서, 크래시 때 진행 중이던 트랜잭션은 "커밋 안 됨"으로 판정돼 안 보인다. 그래서 WAL로 redo만 한다("roll-forward recovery", 28.3). 미커밋 튜플 정리는 vacuum 몫이다(16번).
  - InnoDB 크래시 복구는 연결을 받기 전에 redo log를 적용하고, 크래시 때 진행 중이던 불완전한 트랜잭션을 롤백한다(17.18.2). 롤백은 트랜잭션이 돌던 시간의 3~4배가 걸릴 수 있고 취소할 수 없다.
- 복구 알고리즘(ARIES의 분석·재실행·취소)은 [42번 recovery-aries-checkpoints](../42-recovery-aries-checkpoints/2-summary.md)에서 다룬다.

### 3. group commit — fsync 한 번에 여러 커밋

```text
  fsync 한 번 ≈ 수 ms (저장장치 의존)
  T1 COMMIT ─┐
  T2 COMMIT ─┼─> 로그 flush 1회 ─> T1·T2·T3 모두 "커밋 성공"
  T3 COMMIT ─┘
```

- 커밋 비용의 대부분은 로그 fsync다. 동시에 커밋하려는 트랜잭션들의 로그를 한 번의 fsync로 묶는다(CMU L20, PostgreSQL 28.3 "one fsync of the WAL file may suffice to commit many transactions").
- PostgreSQL `commit_delay`(기본 0)는 flush 직전 잠깐 기다려 묶음을 키운다. 지연을 늘리는 대신 처리량을 올린다. `commit_siblings`만큼 다른 트랜잭션이 활성일 때만 기다린다(19.5).

로컬 재현(예시, PostgreSQL 17.11) — `pgbench -N`(단순 갱신) 5초, `pg_stat_wal`의 `wal_sync` 증가량. 같은 클러스터를 다른 작업도 쓰고 있어 fsync 수는 근사치다.

```text
  클라이언트  synchronous_commit   커밋 수     wal_sync 증가   커밋/ fsync    TPS
      1          on               1,737         1,738          ≈1          348
      8          on               7,312         1,830          ≈4        1,461
      8          off            176,862            49            —       35,411
```

- 클라이언트가 늘자 fsync 한 번이 약 4개의 커밋을 실어 날랐다(group commit).
- `synchronous_commit = off`는 fsync를 기다리지 않아 TPS가 약 24배 올랐다. 대가는 아래 4절.
- MySQL 8.4에서도 같은 경향이었다(예시, MySQL 8.4.10, 자동 커밋 UPDATE): 1클라이언트 200커밋에 `Innodb_os_log_fsyncs` +272, 8클라이언트 1,600커밋에 +624. 서버 공유로 근사치다.

### 4. 지속성 설정 — 무엇을 잃을 수 있나

| 설정 (버전 기준 기본값) | 크래시 때 | 손상 위험 |
|---|---|---|
| PostgreSQL 17 `synchronous_commit = on`(기본) | 커밋 응답 = 로컬 WAL flush 완료(동기 대기 서버를 지정했으면 그쪽 flush까지) → 잃지 않음 | 없음 |
| PostgreSQL 17 `synchronous_commit = off` | 최근 커밋 일부 유실. 최대 `wal_writer_delay`(200ms)의 3배 | **없음** — 커밋 순서대로 재생해 일관된 상태 |
| PostgreSQL 17 `fsync = off` | OS·하드웨어 크래시 때 | **복구 불가능한 손상 가능** |
| MySQL 8.4 `innodb_flush_log_at_trx_commit = 1`(기본) | 커밋마다 write + flush | 없음(ACID에 필요) |
| MySQL 8.4 `innodb_flush_log_at_trx_commit = 2` | 커밋마다 write, flush는 약 1초마다(`innodb_flush_log_at_timeout` 기본 1초 기준) → OS 크래시 때 약 1초 유실 | 없음 |
| MySQL 8.4 `innodb_flush_log_at_trx_commit = 0` | write·flush 약 1초마다(같은 기준) → mysqld 크래시에도 유실 가능 | 없음 |
| MySQL 8.4 `sync_binlog = 1`(기본) | 커밋 전 binlog fsync | `innodb_flush_log_at_trx_commit = 1`과 함께일 때 binlog와 엔진이 어긋나지 않음 |

- `synchronous_commit = off`와 `fsync = off`는 전혀 다르다(PostgreSQL 28.4).
  - 전자는 "최근 몇 개를 잃을 수 있지만 DB는 일관된다". 트랜잭션·세션 단위로 켤 수 있다.
  - 후자는 "쓰기 순서 보장을 모두 끈다". 전체 서버 설정이고, 문서는 전체 DB를 외부 데이터로 쉽게 다시 만들 수 있을 때만 끄라고 한다(19.5).
- MySQL 문서: 0·2의 "초당 flush"는 100% 보장이 아니다. 복제 환경에서 지속성·일관성을 원하면 `sync_binlog=1`, `innodb_flush_log_at_trx_commit=1`.

### 5. 거짓말하는 저장장치와 찢어진 페이지

```text
  앱 → DB fsync() → OS 페이지 캐시 → 컨트롤러 캐시 → 디스크 캐시 → 매체
                                     └ 휘발성 write-back 캐시면 "썼다"고 거짓 응답 가능
```

- PostgreSQL 28.1: RAID 컨트롤러·디스크·SSD의 휘발성 write-back 캐시는 정전 때 내용을 잃는다. 배터리 백업(BBU) 없는 컨트롤러 캐시는 피하고, 드라이브의 write-back 캐시를 끄거나 캐시 flush 명령을 존중하는 장치를 쓰라고 한다. "많은 SSD가 기본적으로 캐시 flush 명령을 존중하지 않는다."
- *찢어진 페이지(torn page)*: 8KB 페이지를 쓰는 도중 전원이 나가 일부 섹터만 새 값인 상태. 행 단위 로그만으로는 복구할 수 없다.
  - PostgreSQL: 체크포인트 뒤 페이지를 **처음** 고칠 때 페이지 전체 이미지를 WAL에 쓴다(`full_page_writes`, 기본 on, 19.5).
  - InnoDB: 페이지를 데이터 파일에 쓰기 전에 **doublewrite 버퍼**에 먼저 쓴다(`innodb_doublewrite`, 8.4 기본 ON, 17.6.4).
- fsync의 OS 쪽 의미와 실패 처리는 [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md).

### 6. 체크포인트 — 로그를 언제 버릴 수 있나

```text
  WAL: ─────────[redo 시작점]──────────────────────────> 현재 LSN
        이전 = 페이지에 이미 반영됨 → 재활용·삭제 가능     이후 = 크래시 때 재생
        (단, 아카이브 대기·복제 슬롯이 붙잡으면 못 지움)
```

- 체크포인트: 그 시점까지의 변경을 데이터 파일에 모두 반영하고 체크포인트 레코드를 남긴다. 크래시 복구는 마지막 체크포인트의 redo 지점부터 시작한다(PostgreSQL 28.5).
- PostgreSQL 17 기본: `checkpoint_timeout` 5min, `max_wal_size` 1GB(소프트 한도 — 부하, 아카이브 실패, 큰 `wal_keep_size`로 넘을 수 있다), `checkpoint_completion_target` 0.9.
- MySQL 8.4: `innodb_redo_log_capacity` 기본 100MB(104857600). 체크포인트가 진행되면 가장 오래된 redo부터 잘라 낸다(17.6.5).
- 트레이드오프: 체크포인트가 잦으면 런타임 I/O와 full page write가 늘고, 드물면 복구 시간이 길어진다(CMU L20, 19.5).

## 쓰이는 자료구조·알고리즘

- **append-only 로그** — 뒤에만 붙이는 순차 쓰기라 무작위 페이지 쓰기보다 싸다. [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md) · [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)(같은 발상의 저장 엔진)
- **LSN = 단조 증가 오프셋** — 페이지 LSN과 flush된 LSN을 비교해 WAL 규칙을 지킨다. 복제 지연도 LSN 차이(바이트)로 잰다(28.6).
- **배치(batching)** — group commit은 여러 요청을 한 번의 비싼 I/O로 묶는 배치다.
- **파일시스템 저널링과 같은 구조** — 로그 먼저, 제자리 쓰기는 나중. [os/23-crash-consistency-and-journaling](../../os/23-crash-consistency-and-journaling/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 설정 점검 (PostgreSQL 17)

```sql
SELECT name, setting, unit FROM pg_settings
WHERE name IN ('fsync','synchronous_commit','full_page_writes','wal_level',
               'max_wal_size','checkpoint_timeout','max_slot_wal_keep_size','commit_delay');

SELECT * FROM pg_stat_wal;              -- wal_records, wal_fpi, wal_bytes, wal_sync ...
SELECT pg_current_wal_lsn(), pg_walfile_name(pg_current_wal_lsn());
```

- 이 재현 서버의 값(예시, PostgreSQL 17.11): `fsync=on`, `synchronous_commit=on`, `full_page_writes=on`, `wal_level=replica`, `max_wal_size=1GB`, `checkpoint_timeout=5min`, WAL 세그먼트 16MB.

### 2. 설정 점검 (MySQL 8.4)

```sql
SELECT @@innodb_flush_log_at_trx_commit, @@sync_binlog, @@innodb_doublewrite,
       @@innodb_redo_log_capacity, @@innodb_flush_method;
SHOW ENGINE INNODB STATUS\G   -- LOG 절: Log sequence number / Log flushed up to / Last checkpoint at
SHOW GLOBAL STATUS LIKE 'Innodb_os_log_fsyncs';
```

- 이 재현 서버의 값(예시, MySQL 8.4.10): `1`, `1`, `ON`, `104857600`, `O_DIRECT`.

### 3. 덜 중요한 쓰기만 골라서 빠르게

```sql
-- PostgreSQL: 이벤트 로그 같은 트랜잭션만 비동기 커밋
BEGIN;
SET LOCAL synchronous_commit = off;
INSERT INTO access_log ...;
COMMIT;
```

- 돈·재고처럼 "커밋했다"는 응답을 믿고 외부 행동을 하는 트랜잭션에는 쓰지 않는다(28.4의 ATM 예).
- `fsync = off`는 버릴 DB(초기 적재, 일회성 배치)에만.

### 4. WAL 디스크 감시

```sql
-- PostgreSQL 17: WAL을 붙잡는 슬롯
SELECT slot_name, active, wal_status, safe_wal_size,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
FROM pg_replication_slots;
SELECT pg_size_pretty(sum(size)) FROM pg_ls_waldir();
```

- `max_slot_wal_keep_size`(PostgreSQL 17 기본 −1 = 무제한)를 정하면 슬롯이 붙잡을 수 있는 WAL에 상한이 생긴다. 넘으면 그 슬롯을 쓰는 대기 서버·CDC가 복제를 이어 갈 수 없게 될 수 있다(19.6). 디스크 풀과 복제 끊김 중 무엇을 택할지 정하는 설정이다.
- 아카이브(`archive_command`) 실패도 WAL을 쌓는다.

## 장애 시나리오와 대처

### 1. `fsync=off`·휘발성 쓰기 캐시 → 크래시 후 커밋된 데이터 유실·손상

- **현상**: 정전·커널 패닉 뒤 재시작했더니 방금 커밋된 주문이 없거나, DB가 기동하지 못한다.
- **보이는 형태**: 문서 표현으로는 "unrecoverable data corruption"(19.5 `fsync`). 기동 실패, 커밋된 행 누락, 인덱스와 테이블 불일치 같은 모습으로 나타날 수 있다 [?] — 구체 오류 메시지는 재현하지 않았다.
- **원인**
  - `fsync = off`는 WAL 규칙의 "먼저 디스크에"를 무력화한다. OS가 순서를 바꿔 쓴다.
  - `fsync`가 켜져 있어도 저장장치가 휘발성 캐시에 두고 "썼다"고 답하면 같은 일이 난다(28.1).
- **대처**
  - `fsync = on`, `full_page_writes = on`(PostgreSQL), `innodb_flush_log_at_trx_commit = 1`·`sync_binlog = 1`·doublewrite ON(MySQL)을 유지한다.
  - 저장장치를 검증한다: PostgreSQL `pg_test_fsync`로 fsync 속도를 잰다. 회전 디스크인데 fsync가 비정상적으로 빠르면 캐시가 거짓말하는 것을 의심한다 [?]. 문서가 권하는 `diskchecker.pl`로 전원 차단 시험을 한다.
  - 복구 불가면 백업 + WAL 아카이브로 복원한다([20번](../20-backup-and-pitr/2-summary.md)).

### 2. WAL 디스크 풀 → DB 정지

- **현상**: 모든 쓰기가 멈추고 DB 프로세스가 내려간다.
- **보이는 형태**
  - PostgreSQL 17: WAL 디스크가 가득 차면 "database server panic and consequent shutdown might occur"(27.6.2). WAL 쓰기 실패는 `PANIC: could not write to log file "..." at offset ..., length ...: No space left on device` 형태다(소스 REL_17_STABLE `xlog.c` `XLogWrite`의 `ereport(PANIC, ... "could not write to log file ...")`). 새 WAL 세그먼트를 만들다 공간이 없으면 `could not write to file "pg_wal/xlogtemp.…": No space left on device`(`XLogFileInitInternal`의 ERROR — WAL 삽입 중 임계 구역이면 PANIC으로 승격)로 보일 수도 있다.
  - 데이터 디스크만 찬 경우는 손상 없이 작업만 실패한다(27.6.2).
- **원인**
  - 비활성 복제 슬롯이 WAL을 붙잡는다(`pg_replication_slots.active = f`, `restart_lsn`이 멀리 뒤처짐). CDC 커넥터가 멈춘 경우가 흔하다.
  - `archive_command` 실패가 계속된다.
  - 큰 배치가 `max_wal_size`를 크게 넘는 WAL을 만든다.
- **대처**
  - 다른 파일을 지우거나 볼륨을 늘려 공간을 확보한다. `pg_wal` 안의 파일을 **손으로 지우지 않는다** — 복구에 필요한 WAL이 사라진다 [?].
  - 버려진 슬롯을 `pg_drop_replication_slot()`으로 지운다. 그 슬롯을 쓰던 대기 서버는 다시 만들어야 할 수 있다.
  - 예방: WAL 볼륨 사용률·슬롯 보존량 알람, `max_slot_wal_keep_size` 설정.

### 3. `innodb_flush_log_at_trx_commit=2`로 바꾼 뒤 결제 기록 유실 (MySQL)

- **현상**: 호스트 재부팅 뒤 결제사에는 승인이 있는데 DB에 해당 주문의 PAID 기록이 없다.
- **보이는 형태**: 에러는 없다. 대사(reconciliation)에서 불일치로 드러난다.
- **원인**: 2는 커밋마다 OS에 write만 하고 flush는 약 1초마다(`innodb_flush_log_at_timeout` 기본 1) 한다. OS·전원 크래시에서 마지막 약 1초의 커밋을 잃는다(17.14). 앱은 "커밋 성공"을 믿고 외부에 알렸다.
- **대처**: 돈이 걸린 서버는 1을 유지한다. 처리량이 필요하면 group commit이 효과를 내도록 동시성을 두고, 배치 커밋(여러 행을 한 트랜잭션에)을 쓴다.

### 4. 커밋 지연이 갑자기 늘었다 — fsync가 느려짐

- **현상**: 코드 변경 없이 모든 쓰기 API의 p99가 수 배로 늘었다.
- **보이는 형태**: PostgreSQL `pg_stat_wal.wal_sync_time`(`track_wal_io_timing` 켰을 때) 증가, `pg_stat_activity`에 `wait_event_type = IO`, `wait_event = WalSync`(WAL이 영구 저장소에 닿기를 기다림)·`WalWrite`(27.2 표 27.9). MySQL `Innodb_os_log_fsyncs` 대비 지연 증가.
- **원인**: 저장장치 지연(다른 볼륨 부하, 클라우드 디스크 버스트 크레딧 소진 등), 또는 체크포인트 직후 full page write 폭증.
- **대처**: WAL을 빠른 전용 볼륨에 둔다. 체크포인트 간격(`max_wal_size`·`checkpoint_timeout`)을 늘려 FPW를 줄인다(복구 시간과 교환). 커밋 수를 줄이도록 작은 트랜잭션을 묶는다.

## 핵심 문장

- WAL 규칙: 데이터 페이지를 쓰기 전에 그 변경의 로그를, 커밋을 알리기 전에 커밋 레코드까지의 로그를 영구 저장소에 둔다.
- 로그는 순차 append라 싸고, 페이지는 나중에 아무 때나 쓸 수 있다(STEAL + NO-FORCE). 대가는 복구 때 redo·undo다.
- 커밋 비용의 핵심은 로그 fsync이고, group commit이 fsync 한 번에 여러 커밋을 싣는다.
- `synchronous_commit=off`·`innodb_flush_log_at_trx_commit=2`는 최근 커밋 유실만 감수한다. `fsync=off`와 휘발성 쓰기 캐시는 손상까지 부를 수 있다.
- 찢어진 페이지는 full page write(PostgreSQL)·doublewrite(InnoDB)로 막는다.
- WAL은 체크포인트 뒤에야 버릴 수 있다. 복제 슬롯·아카이브 실패가 WAL을 붙잡아 디스크를 채우면 DB가 멈춘다.

## 관련 주제·근거

- 선행
  - [16-mvcc](../16-mvcc/2-summary.md) — undo 로그와 튜플 버전
  - [os/24-fsync-and-durability](../../os/24-fsync-and-durability/2-summary.md) — fsync의 의미와 실패
- 연결
  - [os/23-crash-consistency-and-journaling](../../os/23-crash-consistency-and-journaling/2-summary.md) — 파일시스템 저널링
  - database [07-buffer-pool](../07-buffer-pool/2-summary.md)(dirty 페이지·교체), [20-backup-and-pitr](../20-backup-and-pitr/2-summary.md)(WAL 아카이브·PITR), [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md)(WAL 전송), [42-recovery-aries-checkpoints](../42-recovery-aries-checkpoints/2-summary.md)(ARIES)
  - [data-engineering/05-change-data-capture](../../data-engineering/05-change-data-capture/2-summary.md) — WAL·binlog 구독과 슬롯 방치
  - [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md) · [data-structure/24-lsm-tree](../../data-structure/24-lsm-tree/2-summary.md)
- 강의
  - CMU 15-445/645 Fall 2024 Lecture #20 Database Logging — UNDO·REDO, STEAL/FORCE 정책, shadow paging, WAL 구현·group commit, 물리·논리·physiological 로깅, 체크포인트 <https://15445.courses.cs.cmu.edu/fall2024/notes/20-logging.pdf>
- PostgreSQL 17
  - 28.1 Reliability(쓰기 캐시·BBU·찢어진 페이지), 28.3 Write-Ahead Logging, 28.4 Asynchronous Commit, 28.5 WAL Configuration(체크포인트), 28.6 WAL Internals(LSN, 16MB 세그먼트) <https://www.postgresql.org/docs/17/wal-intro.html>
  - 19.5 Write Ahead Log — `fsync`, `synchronous_commit`, `full_page_writes`, `wal_writer_delay`(200ms), `commit_delay`, `max_wal_size`(1GB), `checkpoint_timeout`(5min), `wal_skip_threshold`(2MB, `wal_level = minimal`에서 커밋 시 파일 fsync) <https://www.postgresql.org/docs/17/runtime-config-wal.html>
  - 19.6 Replication — `max_slot_wal_keep_size`(−1) · 27.2 표 27.9 IO 대기 이벤트(`WalSync`·`WalWrite`), `pg_stat_wal.wal_sync_time`(`track_wal_io_timing` 필요) · 27.6.2 Disk Full <https://www.postgresql.org/docs/17/diskusage.html>
  - 소스(REL_17_STABLE): `src/backend/storage/buffer/bufmgr.c`(`FlushBuffer`의 `XLogFlush` — WAL 규칙), `src/backend/access/transam/xlog.c`("could not write to log file" PANIC)
- MySQL 8.4
  - 17.6.5 Redo Log(LSN, 용량, 체크포인트에 따른 절단) <https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html> · 17.6.4 Doublewrite Buffer · 17.18.2 InnoDB Recovery(redo 적용, 불완전 트랜잭션 롤백, redo 삭제 비권장) <https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html>
  - 17.14 InnoDB 시스템 변수 — `innodb_flush_log_at_trx_commit`(1), `innodb_flush_log_at_timeout`(1초), `innodb_redo_log_capacity`(104857600), `innodb_doublewrite`(ON) <https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html>
  - 19.1.6.4 Binary Logging Options — `sync_binlog`(1) <https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `pg_waldump`로 본 HOT_UPDATE·COMMIT 레코드와 페이지 LSN, `pgbench -N` 1·8 클라이언트 × `synchronous_commit` on/off의 TPS와 `pg_stat_wal.wal_sync` 증가량, MySQL 1·8 클라이언트 자동 커밋의 `Innodb_os_log_fsyncs` 증가량, 두 서버의 지속성 설정값과 `SHOW ENGINE INNODB STATUS` LOG 절
