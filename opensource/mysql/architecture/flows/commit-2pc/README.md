# 커밋과 binlog 2PC

상위: [MySQL 아키텍처 지도](../../README.md)

`COMMIT`(또는 autocommit 문장의 끝)이 **InnoDB 와 binlog 두 곳에 같은 결과를 남기기까지**의 흐름이다. 서버의 `ha_commit_trans` 가 코디네이터이고, binlog(`MYSQL_BIN_LOG`)가 트랜잭션 코디네이터 로그(`tc_log`)를 맡는다. 순서는 두 단계다. 먼저 InnoDB 가 prepare 해서 undo 를 `TRX_UNDO_PREPARED` 로 바꾸고, 그다음 binlog 그룹 커밋(`ordered_commit`)이 FLUSH -> SYNC -> COMMIT 세 스테이지로 여러 트랜잭션을 한 번에 처리한다. FLUSH 에서 InnoDB redo 를 한 번에 내리고 binlog 캐시들을 파일에 쓰고, SYNC 에서 binlog 를 fsync 하고, COMMIT 에서 엔진 커밋을 순서대로 부른다. **스레드 경계가 있다.** 스테이지마다 먼저 들어온 스레드가 리더가 되어 뒤따라온 스레드(팔로워)들의 일까지 대신하고, 팔로워는 끝날 때까지 잠든다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 사용자 스레드 (COMMIT 을 보낸 연결)

 [01] trans_commit                                       transaction.cc L233
      +-- [02] ha_commit_trans(thd, all=true)            handler.cc L1686
            +-- rw_ha_count 세기                         L1804  binlog + InnoDB = 2
            +-- MDL COMMIT 잠금 (FTWRL 과 배제)          L1823-L1835
            +-- [03] tc_log->prepare = MYSQL_BIN_LOG::prepare     L1845  (rw_ha_count > 1 일 때)
            |     +-- durability_property = HA_IGNORE_DURABILITY   binlog.cc L7068
            |     +-- ha_prepare_low -> innobase_xa_prepare -> trx_prepare
            |           undo 상태 ACTIVE -> PREPARED, mtr_commit (redo 는 아직 buffer)
            +-- [04] tc_log->commit = MYSQL_BIN_LOG::commit        L1860
                  +-- trx_cache.finalize(Xid_log_event)            binlog.cc L7272
                  +-- [05] ordered_commit                          binlog.cc L7346
 ----------------------------------------------------------------------------------
                  스테이지마다 리더 1 명이 큐 전체를 처리한다 (나머지는 잠든다)
 ----------------------------------------------------------------------------------
                        FLUSH   (LOCK_log)
                        [06] process_flush_stage_queue             L7970
                              +-- ha_flush_logs -> innobase_flush_logs
                              |     redo 를 log_write_up_to 로 (prepare 기록이 디스크로)
                              +-- 큐의 THD 마다 binlog 캐시를 파일 버퍼로
                        flush_cache_to_file                        L7973  write()
                        SYNC    (LOCK_sync)
                        [07] sync_binlog_file                      L8040  fsync (sync_binlog 주기)
                        COMMIT  (LOCK_commit)
                        [08] process_commit_stage_queue            L8115
                              +-- 큐의 THD 마다 ha_commit_low
                                    +-- [09] innobase_commit
                                          +-- [10] trx_commit_low
                                                undo 를 history 로, 잠금 해제, mtr_commit
                        signal_done                                L8154  팔로워를 깨운다

 [01] 은 transaction.cc, [02] 는 handler.cc, [03]-[08] 은 binlog.cc,
 [09] 는 storage/innobase/handler/ha_innodb.cc, [10] 은 storage/innobase/trx/trx0trx.cc
```

트랜잭션 하나가 어느 순간 크래시를 만나면 재시작 후 어떻게 되는지가 이 흐름의 핵심이다. 판정 규칙은 하나다. InnoDB 에 PREPARED 로 남은 트랜잭션은 그 XID 가 binlog 에 있으면 커밋, 없으면 롤백한다(`recover_one_internal_trx`, xa/recovery.cc L245).

```text
 크래시 창 (innodb_flush_log_at_trx_commit=1, sync_binlog=1 일 때)

 A  [03] prepare 직후. prepare 기록은 log buffer 에만
      redo    디스크에 있다는 보장 없음
      binlog  없음
      ->      롤백 (ACTIVE 면 trx0roll.cc L689-L695, PREPARED 여도 XID 가 없다)
 B  [06] ha_flush_logs 뒤, binlog 쓰기 전
      redo    PREPARED
      binlog  없음
      ->      XID 가 없어 롤백
 C  [06] binlog write 뒤, [07] fsync 전
      redo    PREPARED
      binlog  OS 캐시에만
      ->      mysqld 만 죽었으면 OS 캐시의 binlog 가 남아 커밋
              OS 나 전원이 나가 그 부분이 디스크에 못 닿았으면 롤백
 D  [07] fsync 뒤, [08] 엔진 커밋 전
      redo    PREPARED
      binlog  있음
      ->      XID 가 있어 커밋
 E  [10] 엔진 커밋 뒤
      redo    커밋 기록 (디스크에 닿았다면)
      binlog  있음
      ->      커밋

 D 에서 클라이언트는 아직 OK 를 못 받았지만 재시작하면 커밋되어 있다
 B 와 D 를 가르는 것이 binlog 의 XID 이고, 그래서 binlog 가 코디네이터 로그다
```

두 시스템 변수의 조합이 [06] 과 [07] 에서 무엇을 건너뛰는지를 함께 보면 위 표가 어떻게 달라지는지 보인다.

```text
 innodb_flush_log_at_trx_commit x sync_binlog (binlog 를 켠 경우)

 innodb_flush_log_at_trx_commit  ->  [06] innobase_flush_logs (ha_innodb.cc L5848)
   0   (L5859)                        아무것도 안 한다 (주석 L5860-L5861 "once per second")
   1   log_write_up_to(lsn, true)     write + fsync  (L5881 log_buffer_flush_to_disk)
   2   log_write_up_to(lsn, false)    write 만, fsync 없음

   어느 값이든 백그라운드의 log_writer 는 log buffer 를 요청 없이 계속 파일에 쓰고
   (log0write.cc L2264), log_flusher 는 1 이 아니면 innodb_flush_log_at_timeout(기본 1초)
   간격으로 fsync 한다 (log0write.cc L2573-L2592). 그래서 0 과 2 에서 크래시 순간에
   무엇이 파일과 디스크에 있었는지는 이 두 스레드의 타이밍에 달렸다

 sync_binlog  ->  [07] sync_binlog_file (binlog.cc L7700)
   0                                  fsync 안 한다. OS 에 맡긴다
   1                                  그룹마다 fsync
   N   sync_counter                   N 번째 그룹마다 fsync

 아래는 코드 경로에서 따라 나오는 가능성이다. 실제로 몇 개를 잃는지는 크래시 시점에 달렸다
 복구 규칙: PREPARED 트랜잭션만 XID 로 판정한다 (xa/recovery.cc L245, 없으면 rollback_by_xid)
            ACTIVE 로 남은 것은 롤백한다 (trx0roll.cc L689-L695)
            커밋 기록이 디스크에 있는 트랜잭션은 판정 대상이 아니다

 1 / 1   : 위 크래시 창 표 그대로. 커밋 OK 를 받은 트랜잭션은 prepare redo 와 binlog XID 가
           둘 다 fsync 된 뒤라 전원이 나가도 커밋으로 복원된다
 1 / 0   : OS 나 전원이 나가면 fsync 안 된 binlog 끝부분이 사라질 수 있다. 사라진 경우
           그 XID 의 트랜잭션이 redo 에 PREPARED 로 남았다면 롤백된다 (OK 를 받았어도)
           커밋 기록까지 디스크에 있었다면 InnoDB 에는 커밋, binlog 에는 없다
 0 / 1   : FLUSH 가 redo 를 내리지 않으므로 binlog 는 fsync 됐는데 prepare 기록이 아직
           디스크에 없을 수 있다. 그런 트랜잭션은 InnoDB 에서 ACTIVE 로 롤백되거나 아예 없고
           binlog 에만 남는다. binlog 가 엔진보다 앞선다
 2 / 1   : FLUSH 에서 redo 를 write 까지 했으므로 mysqld 만 죽으면 OS 캐시의 redo 가 남아
           1 / 1 과 같다. OS 나 전원이 나가면 아직 fsync 안 된 redo 가 사라져 0 / 1 처럼 될 수 있다

 어느 조합이든 [09] 커밋 시점에는 redo 를 내리지 않는다 (DDL 트랜잭션은 예외, ddl_must_flush)
   binlog 경로에서는 HA_IGNORE_DURABILITY 라 trx_commit_complete_for_mysql 이 그냥 돌아간다 (trx0trx.cc L2472)
```

## 어디에서 쓰이는가

```text
 [명령 디스패치]              SQLCOM_COMMIT 의 trans_commit (sql_parse.cc L4350)
                              autocommit 문장 끝의 trans_commit_stmt (sql_parse.cc L4973)
 [연결과 스레드]              연결 종료 시 THD::cleanup 의 trans_rollback (sql_class.cc L1345)
 [mini-transaction과 redo 기록]  [06] 의 redo 내리기가 log_write_up_to 를 부른다
                              [03] [10] 의 mtr_commit 이 prepare, commit 기록을 log buffer 에 넣는다
 [크래시 복구]                재시작 때 Binlog_recovery::recover (binlog/recovery.cc L53) 가
                              binlog 의 XID 목록으로 PREPARED 트랜잭션을 커밋 또는 롤백한다
 [purge]                      [10] 이 update undo 를 history list 에 올린다
 [레코드 잠금]                [10] 의 trx_release_impl_and_expl_locks 가 잠금을 푼다
```

## db-engine 에서는

db-engine 의 WAL 트랜잭션은 로그가 하나라 2PC 가 필요 없다. 같은 "커밋 레코드가 디스크에 닿는 순간이 커밋"이라는 규칙을, MySQL 은 로그 두 개에 나눠 지킨다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 커밋 기록
   MySQL      InnoDB redo 에는 PREPARED, binlog 에는 Xid_log_event
              binlog 의 XID 가 디스크에 닿는 순간이 커밋점
   db-engine  Transaction.commit: logManager.append(CommitTx(id)) -> logManager.sync()
              COMMIT 레코드가 sync 된 순간이 커밋점 (impl 주석 "durability barrier")

 fsync 횟수
   MySQL      그룹 커밋. FLUSH 리더가 redo 한 번, SYNC 리더가 binlog 한 번을 큐 전체 몫으로
   db-engine  commit 마다 sync 한 번

 데이터 적용
   MySQL      행 변경은 이미 버퍼 풀에 있다. 커밋은 undo 상태만 바꾼다 (undo 로 되돌릴 수 있다)
   db-engine  deferred-apply. sync 뒤에 pending 을 heap 에 insert. undo 가 없다

 잠금 해제
   MySQL      [10] trx_commit_in_memory 의 trx_release_impl_and_expl_locks
   db-engine  TransactionWithLock.commit 끝의 lockManager.releaseAll(id)  (Strict 2PL)

 복구 판정
   MySQL      PREPARED + binlog 에 XID -> 커밋, 없으면 롤백
   db-engine  Recovery.recover: CommitTx 가 있는 txId 의 InsertRow 만 다시 적용
```

db-engine 의 impl 문서는 `commit` 에서 `sync` 를 지우면 테스트가 통과해도 "커밋했다는 응답이 거짓말이 된다"고 적었다. MySQL 에서 그 자리가 `innodb_flush_log_at_trx_commit` 과 `sync_binlog` 이고, 기본값 1 / 1 이 그 거짓말을 막는다. 챕터: [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [09-02-transaction-lock-integration](../../../../../project/db-engine/09-02-transaction-lock-integration/).

## 단계

1. [trans_commit](01_trans_commit/README.md)이 `COMMIT` 문의 입구로, 세션 트랜잭션 전체를 `ha_commit_trans` 에 넘긴다.
2. [ha_commit_trans](02_ha_commit_trans/README.md)가 2PC 가 필요한지 세고 prepare 와 commit 을 순서대로 부른다.
3. [MYSQL_BIN_LOG.prepare](03_MYSQL_BIN_LOG.prepare/README.md)가 엔진들을 prepare 하되 redo 는 내리지 않게 한다.
4. [MYSQL_BIN_LOG.commit](04_MYSQL_BIN_LOG.commit/README.md)이 binlog 캐시를 마감하고 그룹 커밋에 들어간다.
5. [MYSQL_BIN_LOG.ordered_commit](05_MYSQL_BIN_LOG.ordered_commit/README.md)이 FLUSH, SYNC, COMMIT 스테이지를 리더와 팔로워로 돈다.
6. [process_flush_stage_queue](06_process_flush_stage_queue/README.md)가 redo 를 한 번에 내리고 binlog 캐시들을 쓴다.
7. [sync_binlog_file](07_sync_binlog_file/README.md)이 `sync_binlog` 주기에 맞춰 binlog 를 fsync 한다.
8. [process_commit_stage_queue](08_process_commit_stage_queue/README.md)가 큐 순서대로 엔진 커밋을 부른다.
9. [innobase_commit](09_innobase_commit/README.md)이 InnoDB 쪽 커밋의 입구로, redo 내리기를 뒤로 미룬다.
10. [trx_commit_low](10_trx_commit_low/README.md)가 undo 를 커밋 상태로 바꾸는 mtr 을 커밋하고 잠금을 푼다.

## 결과가 쓰이는 곳

```text
 binlog 파일의 트랜잭션 (GTID, 행 이벤트, Xid_log_event)
      --> 복제본의 I/O 스레드, mysqlbinlog, 크래시 복구의 XID 목록

 InnoDB undo 상태 (PREPARED -> 커밋 뒤 history list 또는 삭제)
      --> [크래시 복구] 가 PREPARED 를 찾는다, [purge] 가 history 를 치운다

 gtid_executed
      --> [08] 의 update_commit_group 이 그룹 순서대로 올린다

 클라이언트 OK
      --> [08] 이 끝나고 signal_done 뒤, [명령 디스패치] 의 send_statement_status 에서
```

## 다루지 않는 것

XA 트랜잭션(`XA PREPARE`, `XA COMMIT ONE PHASE`, detached XA), 복제 적용 스레드의 커밋 순서 보장(`Commit_order_manager`, `COMMIT_ORDER_FLUSH_STAGE`), GTID 할당과 `gtid_executed` 테이블 저장, semi-sync 의 `after_sync` / `after_commit` 훅, binlog 로테이션과 purge, `binlog_error_action`, 롤백 경로(`ha_rollback_trans`), binlog 를 끈 경우의 `TC_LOG_MMAP`, `binlog_group_commit_sync_delay` 는 이 흐름의 곁가지라 줄만 적었다.

## 하위 메서드

- [01 trans_commit](01_trans_commit/README.md)
- [02 ha_commit_trans](02_ha_commit_trans/README.md)
- [03 MYSQL_BIN_LOG.prepare](03_MYSQL_BIN_LOG.prepare/README.md)
- [04 MYSQL_BIN_LOG.commit](04_MYSQL_BIN_LOG.commit/README.md)
- [05 MYSQL_BIN_LOG.ordered_commit](05_MYSQL_BIN_LOG.ordered_commit/README.md)
- [06 process_flush_stage_queue](06_process_flush_stage_queue/README.md)
- [07 sync_binlog_file](07_sync_binlog_file/README.md)
- [08 process_commit_stage_queue](08_process_commit_stage_queue/README.md)
- [09 innobase_commit](09_innobase_commit/README.md)
- [10 trx_commit_low](10_trx_commit_low/README.md)
