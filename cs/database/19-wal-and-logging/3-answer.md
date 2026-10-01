# database/19-wal-and-logging — 정답

## 정답

### 1. force 방식이 느린 이유와 WAL

- 한 트랜잭션이 바꾼 페이지는 디스크 여기저기에 흩어져 있다. 커밋마다 그 페이지들을 모두 무작위로 쓰고 기다려야 한다.
- WAL은 변경 **내용**을 로그에 먼저 순차로 쓴다. 커밋 때는 로그만 flush하면 된다. 데이터 페이지는 나중에 모아서 쓴다(PostgreSQL 28.3, CMU L20). (예외: PostgreSQL `wal_level = minimal`에서 테이블을 만들거나 다시 쓴 트랜잭션은 데이터가 `wal_skip_threshold`(기본 2MB) 이상이면 WAL 대신 그 파일을 커밋 때 fsync한다, 19.5.)
- 크래시하면 로그를 다시 재생해(redo) 데이터 페이지에 반영되지 않은 변경을 되살린다.

### 2. UPDATE부터 페이지 기록까지

```text
  ① 로그 레코드 → 로그 버퍼 (LSN = 100)
  ② 페이지 수정, 페이지 헤더 LSN = 100
  ③ COMMIT: 로그를 COMMIT 레코드(LSN 120)까지 flush → "성공" 응답
  ④ (나중) 페이지 쓰기 전: flush된 LSN ≥ 페이지 LSN(100)? 아니면 로그부터 flush
```

- 규칙 1: 커밋 응답 전에 그 트랜잭션의 로그(커밋 레코드 포함)가 영구 저장소에 있어야 한다. 동기 커밋 기준이다(`synchronous_commit = off`는 flush 전에 응답한다, 5번).
- 규칙 2: 페이지를 쓰기 전에, 그 페이지 LSN까지의 로그가 영구 저장소에 있어야 한다.
- PostgreSQL 17 `src/backend/storage/buffer/bufmgr.c`의 `FlushBuffer`가 버퍼 LSN을 읽어 `XLogFlush(recptr)`를 먼저 부른다. 주석이 "the basic WAL rule"이라고 적는다. (로그를 남기지 않는 unlogged 테이블 페이지는 예외다.)
- 로컬 재현(예시, PostgreSQL 17.11): `pg_waldump`에 `Heap HOT_UPDATE` 레코드와 `Transaction COMMIT` 레코드가 차례로 보였다.

### 3. steal / force

| | 뜻 | 복구 때 필요 |
|---|---|---|
| STEAL | 미커밋 트랜잭션의 dirty 페이지를 디스크에 써도 됨 | undo(흔적 되돌리기) |
| NO-STEAL | 커밋 전에는 쓰면 안 됨 | — |
| FORCE | 커밋 때 바뀐 페이지를 모두 써야 함 | — |
| NO-FORCE | 커밋 때 안 써도 됨 | redo(다시 하기) |

- STEAL + NO-FORCE는 undo와 redo가 모두 필요하다. 복구는 가장 느리다.
- 그래도 쓰는 이유(CMU L20)
  - 버퍼 풀이 모자라면 미커밋 페이지도 내보낼 수 있다(큰 트랜잭션 가능).
  - 커밋 때 무작위 페이지 쓰기가 없고 순차 로그 flush만 있다. 런타임이 가장 빠르다.
- 엔진별 undo 방식은 다르다. PostgreSQL은 xmin·xmax 가시성으로 미커밋 튜플을 안 보이게 하고 WAL로는 redo만 한다(28.3 "roll-forward recovery"). InnoDB는 redo 적용 뒤 불완전한 트랜잭션을 롤백한다(17.18.2).

### 4. 클라이언트 수와 group commit

- 예상: 클라이언트 1이면 커밋 1번에 fsync 1번. 클라이언트가 늘면 동시에 커밋하려는 트랜잭션들이 fsync 한 번을 나눠 타므로 **커밋/fsync 비율이 오른다**.
- 로컬 재현(예시, PostgreSQL 17.11, `pgbench -N` 5초)
  - 1클라이언트: 1,737커밋, `wal_sync` +1,738 → 약 1
  - 8클라이언트: 7,312커밋, `wal_sync` +1,830 → 약 4
  - 같은 클러스터를 다른 작업도 써서 fsync 수는 근사치다.
- TPS도 348 → 1,461로 올랐다. 커밋 비용의 대부분이 fsync이기 때문이다.

### 5. `synchronous_commit = off` vs `fsync = off`

| | 크래시 때 | 일관성 | 범위 |
|---|---|---|---|
| `synchronous_commit = off` | 최근 커밋 일부 유실(최대 `wal_writer_delay` 200ms의 3배) | 유지 — WAL을 커밋 순서대로 재생 | 트랜잭션·세션 단위로 설정 가능 |
| `fsync = off` | OS·하드웨어 크래시 때 무엇이든 | **복구 불가능한 손상 가능** | 서버 전체 |

- 비동기 커밋은 "커밋 응답을 fsync 전에 준다"일 뿐, 쓰기 순서는 지킨다. 그래서 잃는 것은 "끝부분 몇 개"다. B가 A에 의존하면 A가 사라지고 B만 남는 일은 없다(28.4).
- `fsync = off`는 WAL 규칙의 전제(먼저 쓴 것이 먼저 영구화)를 없앤다. 데이터 파일이 WAL보다 먼저 디스크에 닿을 수 있다.
- 로컬 재현에서 `synchronous_commit = off`는 8클라이언트 TPS를 1,461 → 35,411로 올렸다. 로그성 데이터에만 `SET LOCAL`로 쓴다.

### 6. MySQL 8.4 `innodb_flush_log_at_trx_commit`

| 값 | write | flush | 잃을 수 있는 것 |
|---|---|---|---|
| 1(기본) | 커밋마다 | 커밋마다 | 없음 — ACID에 필요 |
| 2 | 커밋마다 | 약 1초마다(`innodb_flush_log_at_timeout` 기본 1) | OS·전원 크래시 때 약 1초 |
| 0 | 약 1초마다 | 약 1초마다 | mysqld 크래시에도 약 1초 |

- "약 1초"는 100% 보장이 아니다. DDL 등으로 더 자주, 스케줄링으로 덜 자주 flush될 수 있다(17.14).
- 어느 값이든 크래시 복구 뒤 트랜잭션은 "전부 적용 또는 전부 제거"다. 손상이 아니라 유실이다.
- `sync_binlog = 1`(기본): 커밋 전에 binlog를 fsync한다. 크래시 때 binlog에 없는 트랜잭션은 prepared 상태로만 남아 복구가 롤백한다. 그래서 `innodb_flush_log_at_trx_commit = 1`과 함께면 binlog(복제·PITR의 원천)와 엔진이 어긋나지 않는다(19.1.6.4). 0·2면 binlog에는 있는데 InnoDB redo에서는 사라진 트랜잭션이 생길 수 있다. 복제 환경의 지속성에는 둘 다 1이 필요하다.

### 7. fsync가 거짓말할 때, 찢어진 페이지

- fsync는 OS가 저장장치에 "써라, 캐시도 비워라"라고 요청하는 것이다. 컨트롤러·디스크·SSD에 휘발성 write-back 캐시가 있고 flush 명령을 무시하면, "썼다"는 응답 뒤에도 정전에 사라진다(PostgreSQL 28.1 — 많은 SSD가 기본적으로 캐시 flush 명령을 존중하지 않는다).
- 대처: BBU 있는 컨트롤러, 드라이브 write-back 캐시 끄기, `diskchecker.pl` 같은 전원 차단 시험.
- 찢어진 페이지: 8KB 페이지(512B 섹터 16개)를 쓰는 도중 전원이 나가 일부 섹터만 새 값인 페이지. 행 단위 로그만으로는 원래 페이지를 복원할 수 없다.
  - PostgreSQL: 체크포인트 뒤 첫 수정 때 전체 페이지 이미지를 WAL에 쓴다(`full_page_writes`, 기본 on).
  - InnoDB: 데이터 파일에 쓰기 전에 doublewrite 버퍼에 먼저 쓴다(`innodb_doublewrite`, 8.4 기본 ON). 복구 때 그 사본으로 찢어진 페이지를 고친다.

### 8. WAL 볼륨 풀

- 보이는 형태: WAL 쓰기 실패는 `PANIC: could not write to log file "..." at offset ..., length ...: No space left on device`(소스 `xlog.c` `XLogWrite`의 PANIC). 새 세그먼트 생성 중이면 `could not write to file "pg_wal/xlogtemp.…"` 형태일 수도 있다. 문서: "database server panic and consequent shutdown might occur"(27.6.2).
- 흔한 원인
  1. 비활성 복제 슬롯(멈춘 대기 서버·CDC 커넥터)이 `restart_lsn` 이후 WAL을 붙잡음
  2. `archive_command` 실패 반복
  3. 대량 배치로 `max_wal_size`를 크게 넘는 WAL 생성
- 확인

```sql
SELECT slot_name, active, wal_status,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
FROM pg_replication_slots;
SELECT pg_size_pretty(sum(size)) FROM pg_ls_waldir();
SELECT * FROM pg_stat_archiver;   -- failed_count, last_failed_wal
```

- 대처: 공간 확보(다른 파일·볼륨 확장) → 버려진 슬롯 `pg_drop_replication_slot()` → 아카이브 복구. `pg_wal` 파일을 손으로 지우지 않는다 [?] — 서머리와 같이 1차 문서 문구는 확인하지 못했다.
- 예방: WAL 볼륨·슬롯 보존량 알람, `max_slot_wal_keep_size`(17 기본 −1 = 무제한)로 상한 설정. 상한을 넘은 슬롯의 소비자는 복제를 이어 갈 수 없게 될 수 있으니 "디스크 보호 vs 복제 유지"를 정한다.

### 9. 체크포인트 빈도

- 자주: 크래시 복구 때 재생할 WAL이 적어 복구가 빠르다. 대신 dirty 페이지를 자주 써 런타임 I/O가 늘고, 체크포인트 뒤 첫 수정마다 full page write가 생겨 WAL이 커진다.
- 드물게: 런타임은 가볍지만 복구가 길어진다(CMU L20, PostgreSQL 19.5).
- `max_wal_size`(17 기본 1GB)는 체크포인트를 부르는 기준일 뿐 절대 상한이 아니다. 부하가 크거나, 아카이브가 실패하거나, `wal_keep_size`가 크면 넘을 수 있다(19.5).

### 10. 쓰기 p99 급증과 WAL

- 확인
  - PostgreSQL: `pg_stat_activity`에서 `wait_event_type = IO`, `wait_event = WalSync`·`WalWrite`가 많은지(27.2). `track_wal_io_timing`을 켜고 `pg_stat_wal.wal_sync_time`의 증가 속도를 본다. `pg_stat_wal.wal_fpi`가 체크포인트 직후 튀는지 본다.
  - MySQL: `SHOW ENGINE INNODB STATUS` LOG 절의 `Log sequence number`와 `Log flushed up to` 차이, `Innodb_os_log_fsyncs` 대비 지연.
  - 저장장치 지표: 디스크 지연(`iostat -x`의 await), 클라우드 디스크 IOPS 한도·버스트 크레딧.
- 대처
  - WAL을 빠른 전용 볼륨에 둔다.
  - 체크포인트 간격을 늘려 full page write를 줄인다(복구 시간과 교환).
  - 작은 커밋 여러 개를 한 트랜잭션으로 묶거나 동시성을 두어 group commit 효과를 키운다.
  - 유실을 감수할 수 있는 쓰기만 `synchronous_commit = off`.
