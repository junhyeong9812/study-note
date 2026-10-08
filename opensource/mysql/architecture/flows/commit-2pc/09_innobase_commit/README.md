# innobase_commit

상위: [커밋과 binlog 2PC](../README.md)

**InnoDB 의 `commit` 콜백이고, 서버가 트랜잭션 끝과 문장 끝 양쪽에서 부른다.** 실제로 커밋할지(`will_commit`)는 인자 `commit_trx` 와 autocommit 상태로 정한다. 커밋할 때는 binlog 위치를 trx 에 적고, `flush_log_later = true` 로 "redo 를 지금 내리지 말라"고 표시한 채 [10] `trx_commit_low` 까지 내려갔다가, 돌아와서 `trx_commit_complete_for_mysql` 로 미뤄 둔 redo 내리기를 한다. binlog 2PC 경로에서는 이 마지막 단계도 `HA_IGNORE_DURABILITY` 때문에 건너뛴다. 커밋 기록의 redo 는 이후 누군가의 `log_write_up_to` 나 백그라운드 스레드가 내린다.

## 위치

`storage` / `innobase` / `handler` / `ha_innodb.cc` L5955-L6109 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L5955-L6109))

## 실제 코드

진짜 커밋인지 정한다. `commit_trx=false`(문장 끝)여도 autocommit 이고 `BEGIN` 밖이면 커밋이다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L5982-L5991 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L5982-L5991))

```cpp
// ha_innodb.cc L5982-L5991
  bool will_commit =
      commit_trx ||
      (!thd_test_options(thd, OPTION_NOT_AUTOCOMMIT | OPTION_BEGIN));
  TrxInInnoDB trx_in_innodb(trx, will_commit);

  if (trx_in_innodb.is_aborted()) {
    innobase_rollback(hton, thd, commit_trx);

    return convert_error_code_to_mysql(DB_FORCED_ABORT, 0, thd);
  }
```

커밋 경로다. binlog 위치를 읽어 두고, redo 내리기를 뒤로 미룬 채 커밋한다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L6004-L6080 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L6004-L6080))

```cpp
// ha_innodb.cc L6004-L6080
  bool read_only = trx->read_only || trx->id == 0;

  if (will_commit) {
    /* We were instructed to commit the whole transaction, or
    this is an SQL statement end and autocommit is on */

    /* We need current binlog position for mysqlbackup to work. */

    if (!read_only) {
      while (innobase_commit_concurrency > 0) {
        mysql_mutex_lock(&commit_cond_m);

        ++commit_threads;

        if (commit_threads <= innobase_commit_concurrency) {
          mysql_mutex_unlock(&commit_cond_m);
          break;
        }

        --commit_threads;

        mysql_cond_wait(&commit_cond, &commit_cond_m);

        mysql_mutex_unlock(&commit_cond_m);
      }

      /* The following call reads the binary log position of
      the transaction being committed.

      Binary logging of other engines is not relevant to
      InnoDB as all InnoDB requires is that committing
      InnoDB transactions appear in the same order in the
      MySQL binary log as they appear in InnoDB logs, which
      is guaranteed by the server.

      If the binary log is not enabled, or the transaction
      is not written to the binary log, the file name will
      be a NULL pointer. */
      ulonglong pos;

      thd_binlog_pos(thd, &trx->mysql_log_file_name, &pos);

      trx->mysql_log_offset = static_cast<uint64_t>(pos);

      /* Don't do write + flush right now. For group commit
      to work we want to do the flush later. */
      trx->flush_log_later = true;
    }

    /* If SE needs to persist GTID we must have a transaction. */
    if (thd->se_persists_gtid_explicit()) {
      trx_start_if_not_started(trx, true, UT_LOCATION_HERE);
    }

    innobase_commit_low(trx);

    if (!read_only) {
      trx->flush_log_later = false;

      if (innobase_commit_concurrency > 0) {
        mysql_mutex_lock(&commit_cond_m);

        ut_ad(commit_threads > 0);
        --commit_threads;

        mysql_cond_signal(&commit_cond);

        mysql_mutex_unlock(&commit_cond_m);
      }
    }

    trx_deregister_from_2pc(trx);

    /* Now do a write + flush of logs. */
    if (!read_only) {
      trx_commit_complete_for_mysql(trx);
    }
```

커밋이 아니면 문장 끝 표시만 한다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L6082-L6098 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L6082-L6098))

```cpp
// ha_innodb.cc L6082-L6098
  } else {
    /* We just mark the SQL statement ended and do not do a
    transaction commit */

    /* If we had reserved the auto-inc lock for some
    table in this SQL statement we release it now */

    if (!read_only) {
      lock_unlock_table_autoinc(trx);
    }

    /* Store the current undo_no of the transaction so that we
    know where to roll back if we have to roll back the next
    SQL statement */

    trx_mark_sql_stat_end(trx);
  }
```

`innobase_commit_low` -> `trx_commit_for_mysql` -> `trx_commit` 으로 내려간다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L5887-L5900 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L5887-L5900))

```cpp
// ha_innodb.cc L5887-L5900
/** Commits a transaction in an InnoDB database. */
void innobase_commit_low(trx_t *trx) /*!< in: transaction handle */
{
  if (trx_is_started(trx)) {
    const dberr_t error [[maybe_unused]] = trx_commit_for_mysql(trx);
    // This is ut_ad not ut_a, because previously we did not have an assert
    // and nobody has noticed for a long time, so probably there is no much
    // harm in silencing this error. OTOH we believe it should no longer happen
    // after adding `true` as a second argument to TrxInInnoDB constructor call,
    // so we'd like to learn if the error can still happen.
    ut_ad(DB_SUCCESS == error);
  }
  trx->will_lock = 0;
}
```

`storage` / `innobase` / `trx` / `trx0trx.cc` L2415-L2466 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2415-L2466))

```cpp
// trx0trx.cc L2415-L2466
dberr_t trx_commit_for_mysql(trx_t *trx) /*!< in/out: transaction */
{
  DEBUG_SYNC_C("trx_commit_for_mysql_checks_for_aborted");
  TrxInInnoDB trx_in_innodb(trx, true);

  if (trx_in_innodb.is_aborted() &&
      trx->killed_by != std::this_thread::get_id()) {
    return (DB_FORCED_ABORT);
  }

  /* Because we do not do the commit by sending an Innobase
  sig to the transaction, we must here make sure that trx has been
  started. */

  dberr_t db_err = DB_SUCCESS;

  ut_ad(trx_can_be_handled_by_current_thread_or_is_hp_victim(trx));

  switch (trx->state.load(std::memory_order_relaxed)) {
    case TRX_STATE_NOT_STARTED:
    case TRX_STATE_FORCED_ROLLBACK:

      ut_d(trx->start_file = __FILE__);
      ut_d(trx->start_line = __LINE__);

      trx_start_low(trx, true);
      [[fallthrough]];
    case TRX_STATE_ACTIVE:
    case TRX_STATE_PREPARED:
      trx->op_info = "committing";

      /* For GTID persistence we need update undo segment. */
      db_err = trx_undo_gtid_add_update_undo(trx, false, false);
      if (db_err != DB_SUCCESS) {
        return (db_err);
      }

      if (trx->id != 0) {
        trx_update_mod_tables_timestamp(trx);
      }

      trx_commit(trx);

      MONITOR_DEC(MONITOR_TRX_ACTIVE);
      trx->op_info = "";
      return (DB_SUCCESS);
    case TRX_STATE_COMMITTED_IN_MEMORY:
      break;
  }
  ut_error;
  return (DB_CORRUPTION);
}
```

미뤄 둔 redo 내리기다. 조건 셋 중 하나라도 맞으면 그냥 돌아간다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L2468-L2485 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2468-L2485))

```cpp
// trx0trx.cc L2468-L2485
/** If required, flushes the log to disk if we called trx_commit_for_mysql()
 with trx->flush_log_later == true. */
void trx_commit_complete_for_mysql(trx_t *trx) /*!< in/out: transaction */
{
  if (trx->id != 0 || !trx->must_flush_log_later ||
      (thd_requested_durability(trx->mysql_thd) == HA_IGNORE_DURABILITY &&
       !trx->ddl_must_flush)) {
    /* If we removed trx->ddl_must_flush from condition above, we would
    need to take care of fixing innobase_flush_logs for a scenario in
    which srv_flush_log_at_trx_commit == 0. */
    return;
  }

  trx_flush_log_if_needed(trx->commit_lsn, trx);

  trx->must_flush_log_later = false;
  trx->ddl_must_flush = false;
}
```

## 동작 흐름

```text
 L5968  trx = check_trx_exists(thd)
 L5982  will_commit = commit_trx || autocommit 이고 BEGIN 밖
 L5985  TrxInInnoDB(trx, will_commit)         커밋할 거면 높은 우선순위 트랜잭션이 죽이지 못하게
 L5987  이미 강제 중단됐으면 롤백, DB_FORCED_ABORT
 L6004  read_only = trx->read_only || trx->id == 0

 L6006  will_commit
 L6013    innodb_commit_concurrency > 0 이면 동시 커밋 수 제한
 L6044    thd_binlog_pos -> trx->mysql_log_file_name, L6046 mysql_log_offset
 L6050    flush_log_later = true              "redo 는 나중에"
 L6058    innobase_commit_low(trx)
            L5891  trx_commit_for_mysql
                     trx0trx.cc L2443  PREPARED 또는 ACTIVE (시작 전이면 L2440 에서 시작부터)
                     L2447  GTID 용 update undo 확보
                     L2453  수정한 테이블의 update_time 갱신
                     L2456  trx_commit(trx)
                              L2237  rseg 를 썼으면 mtr_start_sync
                              L2248  [10] trx_commit_low(trx, mtr)
 L6061    flush_log_later = false
 L6075    trx_deregister_from_2pc
 L6079    trx_commit_complete_for_mysql(trx)
            trx0trx.cc L2472  아래 셋 중 하나면 return
              trx->id != 0                 (커밋이 끝나면 trx_init 이 0 으로 만든다)
              !must_flush_log_later        ([10] 에서 lsn 이 0 이었으면)
              HA_IGNORE_DURABILITY 이고 DDL 아님   <-- binlog 2PC 경로는 여기서 돌아간다
            L2481  trx_flush_log_if_needed(commit_lsn, trx)   <-- binlog 없는 경로

 L6082  !will_commit (BEGIN 안의 문장 끝)
 L6090    AUTO-INC 테이블 잠금 해제
 L6097    trx_mark_sql_stat_end                 문장 롤백 지점(undo_no)을 기록
 L6108  return 0
```

같은 함수가 binlog 유무에 따라 redo 를 언제 누가 내리는지가 갈린다.

```text
 커밋 기록의 redo 는 누가 내리나 (innodb_flush_log_at_trx_commit=1)

 binlog 켬 (MYSQL_BIN_LOG, 2PC)
   prepare 기록   [06] FLUSH 스테이지의 ha_flush_logs 가 내린다
   commit 기록    이 함수에서는 안 내린다 (HA_IGNORE_DURABILITY)
                  log_writer 가 log buffer 에 준비된 만큼을 요청 없이 파일에 쓰고
                    (log0write.cc L2264, L2299), log_flusher 가 write_lsn 이 앞서 있으면
                    fsync 한다 (L2538). 이 설정(=1)이면 곧바로, 다른 값이면
                    innodb_flush_log_at_timeout 간격으로 (L2573, L2592).
                    뒤 그룹의 FLUSH 스테이지 log_write_up_to 도 이 lsn 을 넘겨 내린다
   크래시 후      PREPARED + binlog XID 로 커밋이 복원된다

 binlog 끔 (TC_LOG_DUMMY)
   prepare 기록   prepare 를 안 한다
   commit 기록    trx_commit_complete_for_mysql -> trx_flush_log_if_needed -> log_write_up_to
   크래시 후      commit 기록이 디스크에 있으니 커밋

 binlog 경로에서 commit 기록을 기다리지 않아도 되는 것은
 prepare 기록과 binlog XID 만으로 크래시 뒤 커밋을 되살릴 수 있어서다
```

## 결과가 쓰이는 곳

```text
 trx->mysql_log_file_name, mysql_log_offset
      --> 커밋하는 트랜잭션의 binlog 위치. 주석은 mysqlbackup 을 위해서라고 적었다 (L6010)
 flush_log_later / must_flush_log_later
      --> [10] trx_commit_in_memory 가 redo 를 바로 내릴지 미룰지 본다
 trx_deregister_from_2pc
      --> 다음 트랜잭션에서 innobase_register_trx 가 다시 등록한다
```

## 다루지 않는 것

`innodb_commit_concurrency`, 높은 우선순위 트랜잭션(`TrxInInnoDB`, `TRX_FORCE_ROLLBACK_DISABLE`), 강제 중단된 트랜잭션의 롤백, 전문 검색 인덱스 커밋(`fts_commit`), 수정 테이블 타임스탬프, GTID 를 undo 에 적는 경로(`trx_undo_gtid_add_update_undo`), AUTO-INC 잠금은 이 흐름의 곁가지라 줄만 적었다.
