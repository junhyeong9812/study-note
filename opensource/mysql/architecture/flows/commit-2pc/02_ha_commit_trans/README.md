# ha_commit_trans

상위: [커밋과 binlog 2PC](../README.md)

**서버 계층의 2PC 코디네이터다.** 등록된 엔진 목록(`Ha_trx_info`)에서 실제로 데이터를 바꾼 엔진 수(`rw_ha_count`)를 세고, 둘 이상이면 `tc_log->prepare` 를 먼저 부른 뒤 `tc_log->commit` 을 부른다. binlog 를 켜면 binlog 자신도 엔진으로 등록되므로 InnoDB 한 개만 바꾼 트랜잭션도 `rw_ha_count` 가 2 가 되어 2PC 를 탄다. 볼거리는 이 함수가 "진짜 트랜잭션"(`is_real_trans`)인지 가리는 방식이다. autocommit 문장 끝(`all=false`)도 세션 목록이 비어 있으면 진짜 커밋이 된다.

## 위치

`sql` / `handler.cc` L1686-L1937 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L1686-L1937))

## 실제 코드

범위를 정하고 진짜 트랜잭션인지 가린다.

`sql` / `handler.cc` L1686-L1722 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L1686-L1722))

```cpp
// handler.cc L1686-L1722
int ha_commit_trans(THD *thd, bool all, bool ignore_global_read_lock) {
  int error = 0;
  THD_STAGE_INFO(thd, stage_waiting_for_handler_commit);
  bool run_slave_post_commit = false;
  bool need_clear_owned_gtid = false;
  /*
    Save transaction owned gtid into table before transaction prepare
    if binlog is disabled, or binlog is enabled and log_replica_updates
    is disabled with slave SQL thread or slave worker thread.
  */
  std::tie(error, need_clear_owned_gtid) = commit_owned_gtids(thd, all);

  /*
    'all' means that this is either an explicit commit issued by
    user, or an implicit commit issued by a DDL.
  */
  Transaction_ctx *trn_ctx = thd->get_transaction();
  const Transaction_ctx::enum_trx_scope trx_scope =
      all ? Transaction_ctx::SESSION : Transaction_ctx::STMT;

  /*
    "real" is a nick name for a transaction for which a commit will
    make persistent changes. E.g. a 'stmt' transaction inside a 'all'
    transaction is not 'real': even though it's possible to commit it,
    the changes are not durable as they might be rolled back if the
    enclosing 'all' transaction is rolled back.
  */
  const bool is_real_trans =
      all || !trn_ctx->is_active(Transaction_ctx::SESSION);
#ifndef NDEBUG
  bool transaction_to_skip = false;
  DBUG_EXECUTE_IF("replica_crash_after_commit", {
    transaction_to_skip = is_already_logged_transaction(thd);
  });
#endif  // NDEBUG
  auto ha_info = trn_ctx->ha_trx_info(trx_scope);
  XID_STATE *xid_state = trn_ctx->xid_state();
```

쓰기 엔진 수를 세고, COMMIT 잠금을 잡고, prepare 와 commit 을 부른다.

`sql` / `handler.cc` L1793-L1864 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L1793-L1864))

```cpp
// handler.cc L1793-L1864
  if (ha_info && !error) {
    uint rw_ha_count = 0;
    bool rw_trans;

    DBUG_EXECUTE_IF("crash_commit_before", DBUG_SUICIDE(););

    /*
     skip 2PC if the transaction is empty and it is not marked as started (which
     can happen when the slave's binlog is disabled)
    */
    if (ha_info->is_started())
      rw_ha_count = ha_check_and_coalesce_trx_read_only(thd, ha_info, all);
    trn_ctx->set_rw_ha_count(trx_scope, rw_ha_count);
    /* rw_trans is true when we in a transaction changing data */
    rw_trans = is_real_trans && (rw_ha_count > 0);

    DBUG_EXECUTE_IF("dbug.enabled_commit", {
      const char act[] = "now signal Reached wait_for signal.commit_continue";
      assert(!debug_sync_set_action(thd, STRING_WITH_LEN(act)));
    };);
    DEBUG_SYNC(thd, "ha_commit_trans_before_acquire_commit_lock");
    if (rw_trans && !ignore_global_read_lock) {
      /*
        Acquire a metadata lock which will ensure that COMMIT is blocked
        by an active FLUSH TABLES WITH READ LOCK (and vice versa:
        COMMIT in progress blocks FTWRL).

        We allow the owner of FTWRL to COMMIT; we assume that it knows
        what it does.
      */
      MDL_REQUEST_INIT(&mdl_request, MDL_key::COMMIT, "", "",
                       MDL_INTENTION_EXCLUSIVE, MDL_EXPLICIT);

      DBUG_PRINT("debug", ("Acquire MDL commit lock"));
      if (thd->mdl_context.acquire_lock(&mdl_request,
                                        thd->variables.lock_wait_timeout)) {
        ha_rollback_trans(thd, all);
        return 1;
      }
      release_mdl = true;

      DEBUG_SYNC(thd, "ha_commit_trans_after_acquire_commit_lock");
    }

    if (rw_trans && stmt_has_updated_trans_table(ha_info) &&
        check_readonly(thd, true)) {
      ha_rollback_trans(thd, all);
      error = 1;
      goto end;
    }

    if (!trn_ctx->no_2pc(trx_scope) && (trn_ctx->rw_ha_count(trx_scope) > 1))
      error = tc_log->prepare(thd, all);
  }
  /*
    The state of XA transaction is changed to Prepared, intermediately.
    It's going to change to the regular NOTR at the end.
    The fact of the Prepared state is of interest to binary logger.
  */
  if (!error && all && xid_state->has_state(XID_STATE::XA_IDLE)) {
    assert(
        thd->lex->sql_command == SQLCOM_XA_COMMIT &&
        static_cast<Sql_cmd_xa_commit *>(thd->lex->m_sql_cmd)->get_xa_opt() ==
            XA_ONE_PHASE);

    xid_state->set_state(XID_STATE::XA_PREPARED);
  }
  if (error || (error = tc_log->commit(thd, all))) {
    ha_rollback_trans(thd, all);
    error = 1;
    goto end;
  }
```

끝에서 COMMIT 잠금을 풀고 트랜잭션 문맥을 치운다.

`sql` / `handler.cc` L1878-L1893 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L1878-L1893))

```cpp
// handler.cc L1878-L1893
end:
  if (release_mdl && mdl_request.ticket) {
    /*
      We do not always immediately release transactional locks
      after ha_commit_trans() (see uses of ha_enable_transaction()),
      thus we release the commit blocker lock as soon as it's
      not needed.
    */
    DBUG_PRINT("debug", ("Releasing MDL commit lock"));
    thd->mdl_context.release_lock(mdl_request.ticket);
  }
  /* Free resources and perform other cleanup even for 'empty' transactions. */
  if (is_real_trans) {
    trn_ctx->cleanup();
    thd->tx_priority = 0;
  }
```

`tc_log` 가 무엇인지는 서버 시작 때 정해진다. 2PC 엔진 수(`total_ha_2pc`)가 조건을 넘을 때 binlog 가 켜져 있으면 binlog 가, 꺼져 있으면 `TC_LOG_MMAP` 이 코디네이터이고, 그 밖에는 앞서 넣어 둔 `TC_LOG_DUMMY`(mysqld.cc L8477)가 남는다.

`sql` / `mysqld.cc` L8836-L8841 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/mysqld.cc#L8836-L8841))

```cpp
// mysqld.cc L8836-L8841
  if (total_ha_2pc > 1 || (1 == total_ha_2pc && opt_bin_log)) {
    if (opt_bin_log)
      tc_log = &mysql_bin_log;
    else
      tc_log = &tc_log_mmap;
  }
```

binlog 는 트랜잭션 캐시를 처음 쓸 때 자신을 엔진으로 등록한다.

`sql` / `binlog.cc` L8439-L8474 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/binlog.cc#L8439-L8474))

```cpp
// binlog.cc L8439-L8474
static void register_binlog_handler(THD *thd, bool trx) {
  DBUG_TRACE;
  /*
    If this is the first call to this function while processing a statement,
    the transactional cache does not have a savepoint defined. So, in what
    follows:
      . an implicit savepoint is defined;
      . callbacks are registered;
      . binary log is set as read/write.

    The savepoint allows for truncating the trx-cache transactional changes
    fail. Callbacks are necessary to flush caches upon committing or rolling
    back a statement or a transaction. However, notifications do not happen
    if the binary log is set as read/write.
  */
  binlog_cache_mngr *cache_mngr = thd_get_cache_mngr(thd);
  if (cache_mngr->trx_cache.get_prev_position() == MY_OFF_T_UNDEF) {
    /*
      Set an implicit savepoint in order to be able to truncate a trx-cache.
    */
    my_off_t pos = 0;
    binlog_trans_log_savepos(thd, &pos);
    cache_mngr->trx_cache.set_prev_position(pos);

    /*
      Set callbacks in order to be able to call commit or rollback.
    */
    if (trx) trans_register_ha(thd, true, binlog_hton, nullptr);
    trans_register_ha(thd, false, binlog_hton, nullptr);

    /*
      Set the binary log as read/write otherwise callbacks are not called.
    */
    thd->get_ha_data(binlog_hton->slot)->ha_info[0].set_trx_read_write();
  }
}
```

## 동작 흐름

```text
 L1688  stage "waiting for handler commit"
 L1696  commit_owned_gtids                          binlog 를 안 쓰는 경우 GTID 를 테이블에 저장
 L1703  trx_scope = all ? SESSION : STMT
 L1713  is_real_trans = all || !SESSION.is_active()
 L1721  ha_info = 그 범위의 엔진 목록
 L1755  복제본의 원자적 DDL 이면 rli->pre_commit
 L1772  하위 문장(저장 함수, 트리거) 안이면 assert(0), ER_COMMIT_NOT_ALLOWED_IN_SF_OR_TRG

 L1793  엔진이 있고 오류가 없으면
 L1804    rw_ha_count = ha_check_and_coalesce_trx_read_only(...)   읽기만 한 엔진은 빼고 센다
 L1807    rw_trans = is_real_trans && rw_ha_count > 0
 L1823    쓰기 트랜잭션이면 MDL_key::COMMIT 을 INTENTION_EXCLUSIVE 로
 L1827      잡지 못하면 (FLUSH TABLES WITH READ LOCK 중) ha_rollback_trans, return 1
 L1837    super_read_only 등으로 막혔으면 롤백
 L1844    2PC 가능이고 rw_ha_count > 1 이면
 L1845      [03] error = tc_log->prepare(thd, all)
 L1852  XA COMMIT ONE PHASE 면 XA_PREPARED 로 잠깐 바꾼다
 L1860  [04] tc_log->commit(thd, all)
 L1861    prepare 또는 commit 실패면 ha_rollback_trans, error = 1

 L1878  end:
 L1879  COMMIT 잠금 해제
 L1890  진짜 트랜잭션이면 trn_ctx->cleanup()
 L1895  GTID 정리, 복제본 post_commit
 L1936  return error      0 성공, 1 롤백됨, 2 커밋 중 오류
```

2PC 를 탈지는 엔진 목록에 누가 올라 있느냐로 정해진다. 흔한 세 경우를 나란히 두면 이렇다.

```text
 SESSION 목록 (Ha_trx_info) 과 결과

 목록 (rw 여부)            rw_ha_count  tc_log                            경우와 결과
 binlog(rw), InnoDB(rw)    2            MYSQL_BIN_LOG                     binlog 켬, 행 변경. [03] prepare 후 commit
 InnoDB(ro)                0            MYSQL_BIN_LOG                     binlog 켬, 읽기만. prepare 없이 commit
 InnoDB(rw)                1            TC_LOG_DUMMY (mysqld.cc L8477)    binlog 끔. prepare 없이 commit

 binlog 의 등록: register_binlog_handler (binlog.cc L8466-L8467)
   호출자는 binlog_start_trans_and_stmt (L8526) 하나이고, 그것은 이벤트를 캐시에 쓸 때(write_event L6245)와
   ROW 형식의 첫 Table_map (binlog_write_table_map L8598)에서만 불린다. 읽기만 한 트랜잭션은 이벤트가 없어 목록에 없다
 InnoDB 의 등록: innobase_register_trx ([명령 디스패치] [08])
 rw_ha_count 는 L1845 조건과 [04] 에서 Xid_log_event 를 쓸지 (binlog.cc L7269) 둘 다에 쓰인다
```

```text
 반환값과 호출자가 받는 것

 반환  어디서                              의미
 0     L1860 성공                          커밋 성공
 1     L1829, L1839-L1840, L1861-L1862     롤백됨 (클라이언트는 오류를 받는다)
 2     L1788                               하위 문장 안에서 커밋 시도
 [04] 가 RESULT_INCONSISTENT (binlog 에는 썼는데 엔진 커밋 실패) 를 돌려줘도 여기서는 1 로 합쳐진다
```

## 결과가 쓰이는 곳

```text
 error
      --> [01] trans_commit 이 dd 캐시를 확정할지 되돌릴지, [명령 디스패치] 가 OK 를 보낼지
 MDL_key::COMMIT
      --> FLUSH TABLES WITH READ LOCK 이 진행 중인 커밋을 기다리고, 커밋이 FTWRL 을 기다리는 잠금
 trn_ctx->cleanup
      --> 다음 트랜잭션의 엔진 목록이 비어서 시작한다
```

## 다루지 않는 것

GTID 소유와 저장(`commit_owned_gtids`, `gtid_state->update_on_commit`), 복제본의 원자적 DDL 훅(`rli_slave->pre_commit`, `post_commit`), XA ONE PHASE 의 상태 전환, `ha_check_and_coalesce_trx_read_only` 의 읽기 전용 전파, `ha_rollback_trans` 의 롤백 경로, Performance Schema 트랜잭션 계측은 이 흐름의 곁가지라 줄만 적었다.
