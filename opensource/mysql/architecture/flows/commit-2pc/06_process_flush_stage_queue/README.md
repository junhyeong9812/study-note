# process_flush_stage_queue

상위: [커밋과 binlog 2PC](../README.md)

**FLUSH 스테이지 리더가 하는 일 전부다.** 두 가지를 이 순서로 한다. 먼저 큐를 통째로 떼어 내고 `ha_flush_logs(true)` 로 엔진 redo 를 한 번 내린다. 그다음 떼어 낸 무리의 THD 마다 binlog 캐시를 binlog 파일 버퍼로 옮긴다. 순서가 핵심이고 이유는 주석에 있다. prepare 기록이 binlog 보다 먼저 디스크에 있어야 크래시 복구가 성립한다(binlog.cc L7451-L7454). 그룹의 모든 prepare 가 redo 한 번으로 내려가는 것이 [03] 에서 `HA_IGNORE_DURABILITY` 로 미뤄 둔 몫이다.

## 위치

`sql` / `binlog.cc` L7490-L7532 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7490-L7532))

## 실제 코드

`sql` / `binlog.cc` L7490-L7532 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7490-L7532))

```cpp
// binlog.cc L7490-L7532
int MYSQL_BIN_LOG::process_flush_stage_queue(my_off_t *total_bytes_var,
                                             THD **out_queue_var) {
  DBUG_TRACE;
#ifndef NDEBUG
  // number of flushes per group.
  int no_flushes = 0;
#endif
  assert(total_bytes_var && out_queue_var);
  my_off_t total_bytes = 0;
  int flush_error = 1;
  mysql_mutex_assert_owner(&LOCK_log);

  THD *first_seen = fetch_and_process_flush_stage_queue();
  DBUG_EXECUTE_IF("crash_after_flush_engine_log", DBUG_SUICIDE(););
  CONDITIONAL_SYNC_POINT_FOR_TIMESTAMP("before_write_binlog");
  assign_automatic_gtids_to_flush_group(first_seen);
  // Flush thread caches to binary log.
  for (THD *head = first_seen; head; head = head->next_to_commit) {
    // signal_done() owns the final transition to false. After the special
    // commit-order/binlog leader handoff, binlog queue members must still be
    // pending before they enter the remaining group commit stages.
    assert(head->tx_commit_pending);
    Thd_backup_and_restore switch_thd(current_thd, head);
    const auto [error, flushed_bytes] = flush_thread_caches(head);
    total_bytes += flushed_bytes;
    if (flush_error == 1) flush_error = error;
#ifndef NDEBUG
    no_flushes++;
#endif
  }

  *out_queue_var = first_seen;
  *total_bytes_var = total_bytes;

  first_seen->rpl_thd_ctx.binlog_group_commit_ctx().set_max_size_exceeded(
      total_bytes > 0 &&
      (m_binlog_file->get_real_file_size() >= (my_off_t)max_size ||
       DBUG_EVALUATE_IF("simulate_max_binlog_size", true, false)));
#ifndef NDEBUG
  DBUG_PRINT("info", ("no_flushes:= %d", no_flushes));
#endif
  return flush_error;
}
```

큐를 떼어 내고 엔진 로그를 내린다.

`sql` / `binlog.cc` L7447-L7488 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7447-L7488))

```cpp
// binlog.cc L7447-L7488

THD *MYSQL_BIN_LOG::fetch_and_process_flush_stage_queue(
    const bool check_and_skip_flush_logs) {
  /*
    Fetch the entire flush queue and empty it, so that the next batch
    has a leader. We must do this before invoking ha_flush_logs(...)
    for guaranteeing to flush prepared records of transactions before
    flushing them to binary log, which is required by crash recovery.
  */
  Commit_stage_manager::get_instance().lock_queue(
      Commit_stage_manager::BINLOG_FLUSH_STAGE);

  THD *first_seen =
      Commit_stage_manager::get_instance().fetch_queue_skip_acquire_lock(
          Commit_stage_manager::BINLOG_FLUSH_STAGE);
  assert(first_seen != nullptr);

  THD *commit_order_thd =
      Commit_stage_manager::get_instance().fetch_queue_skip_acquire_lock(
          Commit_stage_manager::COMMIT_ORDER_FLUSH_STAGE);

  Commit_stage_manager::get_instance().unlock_queue(
      Commit_stage_manager::BINLOG_FLUSH_STAGE);

  if (!check_and_skip_flush_logs ||
      (check_and_skip_flush_logs && commit_order_thd != nullptr)) {
    /*
      We flush prepared records of transactions to the log of storage
      engine (for example, InnoDB redo log) in a group right before
      flushing them to binary log.
    */
    ha_flush_logs(true);
  }

  /*
    The transactions are flushed to the disk and so threads
    executing slave preserve commit order can be unblocked.
  */
  Commit_stage_manager::get_instance()
      .process_final_stage_for_ordered_commit_group(commit_order_thd);
  return first_seen;
}
```

InnoDB 의 `flush_logs` 콜백이다(`innobase_hton->flush_logs = innobase_flush_logs`, ha_innodb.cc L5403). `innodb_flush_log_at_trx_commit` 이 여기서 갈린다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L5848-L5885 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L5848-L5885))

```cpp
// ha_innodb.cc L5848-L5885
static bool innobase_flush_logs(handlerton *hton, bool binlog_group_flush) {
  DBUG_TRACE;
  assert(hton == innodb_hton_ptr);

  if (srv_read_only_mode) {
    return false;
  }

  /* If !binlog_group_flush, we got invoked by FLUSH LOGS or similar.
  Else, we got invoked by binlog group commit during flush stage. */

  if (binlog_group_flush && srv_flush_log_at_trx_commit == 0) {
    /* innodb_flush_log_at_trx_commit=0
    (write and sync once per second).
    Do not flush the redo log during binlog group commit. */

    /* This could be unsafe if we grouped at least one DDL transaction,
    and we removed !trx->ddl_must_flush from condition which is checked
    inside trx_commit_complete_for_mysql() when we decide if we could
    skip the flush. */
    return false;
  }

  /* Signal and wait for all GTIDs to persist on disk. */
  if (!binlog_group_flush) {
    auto &gtid_persistor = clone_sys->get_gtid_persistor();
    gtid_persistor.wait_flush(true, true, nullptr);
  }

  /* Flush the redo log buffer to the redo log file.
  Sync it to disc if we are in FLUSH LOGS, or if
  innodb_flush_log_at_trx_commit=1
  (write and sync at each commit). */
  log_buffer_flush_to_disk(!binlog_group_flush ||
                           srv_flush_log_at_trx_commit == 1);

  return false;
}
```

`sql` / `handler.cc` L2517-L2531 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L2517-L2531))

```cpp
// handler.cc L2517-L2531
static bool flush_handlerton(THD *, plugin_ref plugin, void *arg) {
  handlerton *hton = plugin_data<handlerton *>(plugin);
  if (hton->state == SHOW_OPTION_YES && hton->flush_logs &&
      hton->flush_logs(hton, *(static_cast<bool *>(arg))))
    return true;
  return false;
}

bool ha_flush_logs(bool binlog_group_flush) {
  if (plugin_foreach(nullptr, flush_handlerton, MYSQL_STORAGE_ENGINE_PLUGIN,
                     static_cast<void *>(&binlog_group_flush))) {
    return true;
  }
  return false;
}
```

THD 하나의 캐시를 binlog 로 옮긴다. XID 이벤트를 썼으면 prepared XID 수를 올린다.

`sql` / `binlog.cc` L7398-L7411 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7398-L7411))

```cpp
// binlog.cc L7398-L7411
  my_off_t bytes = 0;
  bool wrote_xid = false;
  int error = cache_mngr->flush(thd, &bytes, &wrote_xid);
  if (!error && bytes > 0) {
    /*
      Note that set_trans_pos does not copy the file name. See
      this function documentation for more info.
    */
    thd->set_trans_pos(log_file_name, m_binlog_file->position());
    if (wrote_xid) inc_prep_xids(thd);
  }
  DBUG_PRINT("debug", ("bytes: %llu", bytes));
  return std::make_pair(error, bytes);
}
```

`sql` / `binlog.cc` L1215-L1238 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L1215-L1238))

```cpp
// binlog.cc L1215-L1238
  int flush(THD *thd, my_off_t *bytes_written, bool *wrote_xid) {
    my_off_t stmt_bytes = 0;
    my_off_t trx_bytes = 0;
    assert(stmt_cache.has_xid() == 0);

    bool parallelization_barrier = false;
    if (has_incident()) {
      if (int error = handle_deferred_cache_write_incident(thd)) return error;
      // Request force rotate
      thd->rpl_thd_ctx.binlog_group_commit_ctx().set_force_rotate();
      // Set as parallelization_barrier so that dependency tracker marks all
      // subsequent transactions to depend on it.
      parallelization_barrier = true;
    }

    int error =
        stmt_cache.flush(thd, &stmt_bytes, wrote_xid, parallelization_barrier);
    if (error) return error;
    DEBUG_SYNC(thd, "after_flush_stm_cache_before_flush_trx_cache");
    error =
        trx_cache.flush(thd, &trx_bytes, wrote_xid, parallelization_barrier);
    if (error) return error;
    *bytes_written = stmt_bytes + trx_bytes;
    return 0;
```

## 동작 흐름

```text
 L7500  LOCK_log 를 쥐고 있어야 한다
 L7502  first_seen = fetch_and_process_flush_stage_queue()
          L7456  큐 잠금
          L7459  BINLOG_FLUSH_STAGE 큐 전체를 떼어 낸다   다음 스레드는 빈 큐에서 새 리더가 된다
          L7464  COMMIT_ORDER_FLUSH_STAGE 큐도
          L7468  큐 잠금 해제
          L7478  ha_flush_logs(true)
                   handler.cc L2526  모든 엔진의 flush_handlerton
                   ha_innodb.cc      innobase_flush_logs(hton, binlog_group_flush=true)
                     L5852  read only 면 끝
                     L5859  innodb_flush_log_at_trx_commit == 0 이면 끝 (아무것도 안 한다)
                     L5881  log_buffer_flush_to_disk(sync = (flush_log_at_trx_commit == 1))
                              log0buf.h L191 -> log0buf.cc L1181
                              log0buf.cc L1185  lsn = 현재 LSN
                              log0buf.cc L1189  log_write_up_to(log, lsn, sync)   --> [mini-transaction과 redo 기록]
 L7503  디버그 크래시 지점 crash_after_flush_engine_log        <-- 크래시 창 B
 L7505  assign_automatic_gtids_to_flush_group                   GTID 를 이 그룹에 할당
 L7507  for (head = first_seen; head; head = head->next_to_commit)
 L7512    Thd_backup_and_restore                                 잠시 그 THD 로 바꿔 입는다
 L7513    flush_thread_caches(head)
            L7400  cache_mngr->flush      stmt_cache 다음 trx_cache 를 binlog 로
            L7406  set_trans_pos           이 트랜잭션의 binlog 파일, 위치
            L7407  wrote_xid 면 inc_prep_xids
 L7521  wait_queue = first_seen, total_bytes
 L7524  binlog 파일이 max_binlog_size 를 넘었으면 로테이션 표시
 L7531  return flush_error
```

`log_buffer_flush_to_disk` 가 LSN 인자를 따로 받지 않고 **호출 시점의 현재 LSN** 까지 내린다는 점이 그룹 커밋의 몫을 키운다. 이 그룹의 prepare 뿐 아니라 그때까지 log buffer 에 들어온 모든 redo 가 함께 내려간다.

```text
 FLUSH 한 번이 내리는 redo 범위 (log0buf.cc L1181-L1190)

 LSN  ------------------------------------------------------------>
      [ 이미 디스크 ]  [ T1 prepare ][ 다른 trx 의 mtr ][ T2 prepare ][ ... ]
                      ^ flushed_to_disk_lsn                           ^ log_get_lsn(log) 호출 시점
                      |<------------ log_write_up_to 한 번 ----------->|

 innodb_flush_log_at_trx_commit = 1  write + fsync
                                = 2  write 만 (OS 캐시까지)
                                = 0  이 호출 자체를 건너뛴다 (L5859)
```

```text
 FLUSH 스테이지가 끝났을 때 (그룹 [T1, T2], sync_binlog=1)

 InnoDB redo file      prepare 기록까지 디스크 (flush_log_at_trx_commit=1 일 때)
 binlog IO cache       두 트랜잭션의 이벤트, Xid 이벤트까지. write 는 [05] 의 flush_cache_to_file 에서
 binlog file (disk)    아직 아님. [07] 에서 fsync
 prep_xids             +2
```

## 결과가 쓰이는 곳

```text
 wait_queue (out_queue_var)
      --> [05] 가 SYNC 스테이지 큐로 넘긴다
 total_bytes
      --> [05] 가 0 보다 크면 flush_cache_to_file, [07] sync 를 한다
 set_trans_pos 의 위치
      --> [09] innobase_commit 이 thd_binlog_pos 로 읽어 trx->mysql_log_offset 에 적는다
 prep_xids
      --> [08] 의 dec_prep_xids 가 내린다 (binlog.cc L7612)
```

## 다루지 않는 것

GTID 자동 할당(`assign_automatic_gtids_to_flush_group`), 복제 적용 스레드의 커밋 순서 큐(`COMMIT_ORDER_FLUSH_STAGE`, `process_final_stage_for_ordered_commit_group`), incident 이벤트, binlog 캐시의 임시 파일과 `binlog_cache_size`, `FLUSH LOGS` 경로의 `ha_flush_logs(false)` 와 GTID 영속화 대기는 이 흐름의 곁가지라 줄만 적었다. `log_write_up_to` 의 내부는 [mini-transaction과 redo 기록](../../mtr-redo/README.md)에 있다.
