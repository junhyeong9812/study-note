# MYSQL_BIN_LOG::prepare

상위: [커밋과 binlog 2PC](../README.md)

**2PC 의 첫 단계를 엔진들에게 시키되, redo 를 디스크에 내리지는 말라고 표시하는 곳이다.** 함수 자체는 두 줄이 핵심이다. `durability_property = HA_IGNORE_DURABILITY` 로 표시하고 `ha_prepare_low` 로 엔진마다 `prepare` 를 부른다. InnoDB 쪽(`innobase_xa_prepare` -> `trx_prepare`)은 undo 로그 헤더를 `TRX_UNDO_PREPARED` 로 바꾸는 mtr 하나를 커밋하고, 원래라면 그 LSN 까지 redo 를 내리지만 이 표시를 보고 건너뛴다. 그 redo 는 [06] FLUSH 스테이지가 그룹 전체 몫으로 한 번에 내린다. 주석이 이 설계를 그대로 적어 두었다(binlog.cc L7059-L7067).

## 위치

`sql` / `binlog.cc` L7054-L7079 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7054-L7079))

## 실제 코드

`sql` / `binlog.cc` L7054-L7079 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L7054-L7079))

```cpp
// binlog.cc L7054-L7079
int MYSQL_BIN_LOG::prepare(THD *thd, bool all) {
  DBUG_TRACE;

  assert(opt_bin_log);

  /*
    Set HA_IGNORE_DURABILITY to not flush the prepared record of the
    transaction to the log of storage engine (for example, InnoDB
    redo log) during the prepare phase. So that we can flush prepared
    records of transactions to the log of storage engine in a group
    right before flushing them to binary log during binlog group
    commit flush stage. Reset to HA_REGULAR_DURABILITY at the
    beginning of parsing next command.
  */
  thd->durability_property = HA_IGNORE_DURABILITY;

  CONDITIONAL_SYNC_POINT_FOR_TIMESTAMP("before_prepare_in_engines");
  int error = ha_prepare_low(thd, all);

  CONDITIONAL_SYNC_POINT_FOR_TIMESTAMP("after_ha_prepare_low");
  // Invoke `commit` if we're dealing with `XA PREPARE` in order to use BCG
  // to write the event to file.
  if (!error && all && is_xa_prepare(thd)) return this->commit(thd, true);

  return error;
}
```

엔진마다 prepare 를 부른다. 읽기만 한 엔진은 건너뛴다.

`sql` / `handler.cc` L2373-L2409 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L2373-L2409))

```cpp
// handler.cc L2373-L2409
int ha_prepare_low(THD *thd, bool all) {
  DBUG_TRACE;
  int error = 0;
  const Transaction_ctx::enum_trx_scope trx_scope =
      all ? Transaction_ctx::SESSION : Transaction_ctx::STMT;
  auto ha_list = thd->get_transaction()->ha_trx_info(trx_scope);

  if (ha_list) {
    for (auto const &ha_info : ha_list) {
      if (!ha_info.is_trx_read_write() &&  // Do not call two-phase commit if
                                           // transaction is read-only
          !thd_holds_xa_transaction(thd))  // but only if is not an XA
                                           // transaction
        continue;

      auto ht = ha_info.ht();
      const int err = ht->prepare(ht, thd, all);
      if (err) {
        if (!thd_holds_xa_transaction(
                thd)) {  // If XA PREPARE, let error be handled by caller
          char errbuf[MYSQL_ERRMSG_SIZE];
          my_error(ER_ERROR_DURING_COMMIT, MYF(0), err,
                   my_strerror(errbuf, MYSQL_ERRMSG_SIZE, err));
        }
        error = 1;
      }
      assert(!thd->status_var_aggregated);
      thd->status_var.ha_prepare_count++;
      global_aggregated_stats.get_shard(thd->thread_id()).ha_prepare_count++;

      if (error) break;
    }
    DBUG_EXECUTE_IF("crash_commit_after_prepare", DBUG_SUICIDE(););
  }

  return error;
}
```

InnoDB 의 prepare 콜백이다(`innobase_hton->prepare = innobase_xa_prepare`, ha_innodb.cc L5384). XID 를 trx 에 복사하고, 트랜잭션 전체를 prepare 하는 경우에만 `trx_prepare_for_mysql` 로 간다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L20277-L20337 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L20277-L20337))

```cpp
// ha_innodb.cc L20277-L20337
static int innobase_xa_prepare(handlerton *hton, /*!< in: InnoDB handlerton */
                               THD *thd, /*!< in: handle to the MySQL thread of
                                         the user whose XA transaction should
                                         be prepared */
                               bool prepare_trx) /*!< in: true - prepare
                                                 transaction false - the current
                                                 SQL statement ended */
{
  trx_t *trx = check_trx_exists(thd);

  assert(hton == innodb_hton_ptr);

  thd_get_xid(thd, (MYSQL_XID *)trx->xid);

  innobase_srv_conc_force_exit_innodb(trx);

  TrxInInnoDB trx_in_innodb(trx);

  if (trx_in_innodb.is_aborted() ||
      DBUG_EVALUATE_IF("simulate_xa_failure_prepare_in_engine", 1, 0)) {
    innobase_rollback(hton, thd, prepare_trx);

    return (convert_error_code_to_mysql(DB_FORCED_ABORT, 0, thd));
  }

  if (!trx_is_registered_for_2pc(trx) && trx_is_started(trx)) {
    log_errlog(ERROR_LEVEL, ER_INNODB_UNREGISTERED_TRX_ACTIVE);
  }

  if (prepare_trx ||
      (!thd_test_options(thd, OPTION_NOT_AUTOCOMMIT | OPTION_BEGIN))) {
    /* We were instructed to prepare the whole transaction, or
    this is an SQL statement end and autocommit is on */

    ut_ad(trx_is_registered_for_2pc(trx));

    dberr_t err = trx_prepare_for_mysql(trx);

    ut_ad(err == DB_SUCCESS || err == DB_FORCED_ABORT);

    if (err == DB_FORCED_ABORT) {
      innobase_rollback(hton, thd, prepare_trx);

      return (convert_error_code_to_mysql(DB_FORCED_ABORT, 0, thd));
    }

  } else {
    /* We just mark the SQL statement ended and do not do a
    transaction prepare */

    /* If we had reserved the auto-inc lock for some
    table in this SQL statement we release it now */

    lock_unlock_table_autoinc(trx);

    /* Store the current undo_no of the transaction so that we
    know where to roll back if we have to roll back the next
    SQL statement */

    trx_mark_sql_stat_end(trx);
  }
```

`trx_prepare` 가 롤백 세그먼트마다 prepare mtr 을 커밋하고 상태를 `TRX_STATE_PREPARED` 로 바꾼다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L2961-L3009 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2961-L3009))

```cpp
// trx0trx.cc L2961-L3009
static void trx_prepare(trx_t *trx) {
  ut_ad(trx_can_be_handled_by_current_thread_or_is_hp_victim(trx));

  /* This transaction has crossed the point of no return and cannot
  be rolled back asynchronously now. It must commit or rollback
  synchronously. */

  lsn_t lsn = 0;

  /* Only fresh user transactions can be prepared.
  Recovered transactions cannot. */
  ut_a(!trx->is_recovered);

  DBUG_EXECUTE_IF("ib_trx_crash_during_xa_prepare_step", DBUG_SUICIDE(););

  if (trx->rsegs.m_redo.rseg != nullptr && trx_is_redo_rseg_updated(trx)) {
    lsn = trx_prepare_low(trx, &trx->rsegs.m_redo, false);
  }

  if (trx->rsegs.m_noredo.rseg != nullptr && trx_is_temp_rseg_updated(trx)) {
    trx_prepare_low(trx, &trx->rsegs.m_noredo, true);
  }

  ut_a(trx->state.load(std::memory_order_relaxed) == TRX_STATE_ACTIVE);

  trx_sys_mutex_enter();
  trx->state.store(TRX_STATE_PREPARED, std::memory_order_relaxed);
  trx_sys->n_prepared_trx++;
  trx_sys_mutex_exit();

  /* Force isolation level to RC and release GAP locks
  for test purpose. */
  DBUG_EXECUTE_IF("ib_force_release_gap_lock_prepare",
                  trx->isolation_level = TRX_ISO_READ_COMMITTED;);

  /* Release read locks after PREPARE for READ COMMITTED
  and lower isolation. */
  if (trx->releases_gap_locks_at_prepare()) {
    /* Stop inheriting GAP locks. */
    trx->skip_lock_inheritance = true;

    /* Release only GAP locks for now. */
    lock_trx_release_read_locks(trx, true);
  }

  if (lsn > 0) {
    trx_flush_logs(trx, lsn);
  }
}
```

undo 헤더를 PREPARED 로 바꾸는 mtr 이다. 이 mtr 의 커밋이 "파일 세계에서 prepare 된 순간"이다(주석 L2939-L2940).

`storage` / `innobase` / `trx` / `trx0trx.cc` L2899-L2952 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2899-L2952))

```cpp
// trx0trx.cc L2899-L2952
static lsn_t trx_prepare_low(
    trx_t *trx,               /*!< in/out: transaction */
    trx_undo_ptr_t *undo_ptr, /*!< in/out: pointer to rollback
                              segment scheduled for prepare. */
    bool noredo_logging)      /*!< in: turn-off redo logging. */
{
  if (undo_ptr->insert_undo != nullptr || undo_ptr->update_undo != nullptr) {
    mtr_t mtr;
    trx_rseg_t *rseg = undo_ptr->rseg;

    mtr_start_sync(&mtr);

    if (noredo_logging) {
      mtr_set_log_mode(&mtr, MTR_LOG_NO_REDO);
    }

    /* Change the undo log segment states from TRX_UNDO_ACTIVE to
    TRX_UNDO_PREPARED: these modifications to the file data
    structure define the transaction as prepared in the file-based
    world, at the serialization point of lsn. */

    rseg->latch();

    if (undo_ptr->insert_undo != nullptr) {
      /* It is not necessary to obtain trx->undo_mutex here
      because only a single OS thread is allowed to do the
      transaction prepare for this transaction. */
      trx_undo_set_state_at_prepare(trx, undo_ptr->insert_undo, false, &mtr);
    }

    if (undo_ptr->update_undo != nullptr) {
      if (!noredo_logging) {
        trx_undo_gtid_set(trx, undo_ptr->update_undo, true);
      }
      trx_undo_set_state_at_prepare(trx, undo_ptr->update_undo, false, &mtr);
    }

    rseg->unlatch();

    /*--------------*/
    /* This mtr commit makes the transaction prepared in
    file-based world. */
    mtr_commit(&mtr);
    /*--------------*/

    if (!noredo_logging) {
      const lsn_t lsn = mtr.commit_lsn();
      ut_ad(lsn > 0 || !mtr_t::s_logging.is_enabled());
      return lsn;
    }
  }

  return 0;
}
```

redo 를 내릴지 말지는 여기서 갈린다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L3643-L3677 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L3643-L3677))

```cpp
// trx0trx.cc L3643-L3677
static void trx_flush_logs(trx_t *trx, lsn_t lsn) {
  if (lsn == 0) {
    return;
  }
  switch (thd_requested_durability(trx->mysql_thd)) {
    case HA_IGNORE_DURABILITY:
      /* We set the HA_IGNORE_DURABILITY during prepare phase of
      binlog group commit to not flush redo log for every transaction
      here. So that we can flush prepared records of transactions to
      redo log in a group right before writing them to binary log
      during flush stage of binlog group commit. */
      break;
    case HA_REGULAR_DURABILITY:
      /* Depending on the my.cnf options, we may now write the log
      buffer to the log files, making the prepared state of the
      transaction durable if the OS does not crash. We may also
      flush the log files to disk, making the prepared state of the
      transaction durable also at an OS crash or a power outage.

      The idea in InnoDB's group prepare is that a group of
      transactions gather behind a trx doing a physical disk write
      to log files, and when that physical write has been completed,
      one of those transactions does a write which prepares the whole
      group. Note that this group prepare will only bring benefit if
      there are > 2 users in the database. Then at least 2 users can
      gather behind one doing the physical log write to disk.

      We must not be holding any mutexes or latches here. */

      /* We should trust trx->ddl_operation instead of
      ddl_must_flush here */
      trx->ddl_must_flush = false;
      trx_flush_log_if_needed(lsn, trx);
  }
}
```

## 동작 흐름

```text
 binlog.cc
 L7057  assert(opt_bin_log)
 L7068  thd->durability_property = HA_IGNORE_DURABILITY
 L7071  ha_prepare_low(thd, all)
          handler.cc L2381  엔진 목록을 돈다
          L2382  읽기 전용 엔진이고 XA 가 아니면 건너뜀
          L2389  ht->prepare(ht, thd, all)
                   binlog 의 prepare  binlog_prepare (binlog.cc L2534)  all=true 면 할 일 없음
                   InnoDB 의 prepare  innobase_xa_prepare
          L2405  디버그 크래시 지점 crash_commit_after_prepare
 L7076  XA PREPARE 면 바로 commit 으로 (binlog 에 XA 이벤트를 쓰기 위해)

 ha_innodb.cc (innobase_xa_prepare)
 L20289  thd_get_xid -> trx->xid
 L20295  이미 강제 중단된 trx 면 롤백, 오류
 L20306  prepare_trx 이거나 autocommit 문장 끝이면
 L20313    trx_prepare_for_mysql -> trx0trx.cc L3102 trx_prepare
 L20323  아니면 문장 끝 표시만 (L20336 trx_mark_sql_stat_end)

 trx0trx.cc (trx_prepare)
 L2976  redo 롤백 세그먼트를 썼으면 L2977 lsn = trx_prepare_low(redo)
          L2909  mtr_start_sync
          L2920  rseg latch
          L2926  insert undo  trx_undo_set_state_at_prepare
          L2931  update undo  GTID 기록 후 L2933 set_state_at_prepare
          L2941  mtr_commit     prepare 기록이 log buffer 에 들어간다
          L2945  lsn = mtr.commit_lsn()
 L2980  임시 테이블 세그먼트는 redo 없이 (MTR_LOG_NO_REDO)
 L2987  state = TRX_STATE_PREPARED, L2988 n_prepared_trx++
 L2998  READ COMMITTED 이하면 gap 잠금을 여기서 푼다
 L3007  trx_flush_logs(trx, lsn)
          L3647  durability 가 HA_IGNORE_DURABILITY 면 아무것도 안 한다   <-- binlog 경로
                 HA_REGULAR_DURABILITY 면 trx_flush_log_if_needed        <-- binlog 없는 2PC
```

prepare 가 끝난 순간 트랜잭션이 어디에 어떻게 남아 있는지를 그리면 크래시 창 A 와 B 의 차이가 보인다.

```text
 prepare 직후의 흔적 (binlog 켬)

 undo log header page    TRX_UNDO_ACTIVE -> TRX_UNDO_PREPARED, XID
                         (XID 는 trx_undo_write_xid, trx0undo.cc L1879)
                         버퍼 풀의 dirty 페이지. 디스크에 쓰였다는 보장은 없다
 redo log buffer         위 변경의 redo, commit_lsn = L
                         이 트랜잭션은 내리지 않는다 (HA_IGNORE_DURABILITY). 디스크에 있다는 보장이 없다
                         (백그라운드 log_writer 가 먼저 write 할 수는 있다, log0write.cc L2230)
 trx_t                   state = TRX_STATE_PREPARED. 메모리
 binlog trx_cache        문장마다 쌓인 이벤트들. Xid 이벤트는 아직 없다

 [06] FLUSH 스테이지의 ha_flush_logs 가 L 까지 redo 를 내리면 창 B 로 넘어간다
```

## 결과가 쓰이는 곳

```text
 TRX_UNDO_PREPARED + XID (undo 헤더)
      --> [크래시 복구] 가 재시작 때 PREPARED 트랜잭션과 XID 를 찾아 binlog 와 대조한다
 durability_property = HA_IGNORE_DURABILITY
      --> [09] innobase_commit 이후 trx_commit_complete_for_mysql 도 redo 를 내리지 않는다
      --> 다음 문장의 reset_for_next_command 가 HA_REGULAR_DURABILITY 로 되돌린다 (sql_parse.cc L5253)
 prepare mtr 의 commit_lsn
      --> [06] 의 innobase_flush_logs 가 그 LSN 을 포함해 log_write_up_to 한다
```

## 다루지 않는 것

XA PREPARE 경로(`is_xa_prepare`, `XA_prepare_log_event`), `binlog_prepare` 의 commit parent 기록(병렬 복제용), GTID 를 undo 에 적는 `trx_undo_gtid_set`, READ COMMITTED 의 gap 잠금 조기 해제(`lock_trx_release_read_locks`), 임시 테이블 롤백 세그먼트, `set_prepared_in_tc` 단계(`trx_set_prepared_in_tc`)는 이 흐름의 곁가지라 줄만 적었다.
