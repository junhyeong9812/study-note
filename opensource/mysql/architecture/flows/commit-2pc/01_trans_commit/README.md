# trans_commit

상위: [커밋과 binlog 2PC](../README.md)

**`COMMIT` 문이 들어오는 서버 쪽 입구다.** 트랜잭션 상태를 검사하고 `ha_commit_trans(thd, all=true)` 로 세션 트랜잭션 전체를 넘긴 뒤, 결과에 따라 THD 의 트랜잭션 표시(`SERVER_STATUS_IN_TRANS`, `OPTION_BEGIN`)를 지우고 데이터 사전 캐시를 확정하거나 되돌린다. autocommit 문장의 끝은 이 함수가 아니라 짝인 `trans_commit_stmt` 로 들어오고, 거기서는 `all=false` 로 같은 [02] 를 부른다.

## 위치

`sql` / `transaction.cc` L233-L300 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/transaction.cc#L233-L300))

## 실제 코드

`sql` / `transaction.cc` L233-L300 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/transaction.cc#L233-L300))

```cpp
// transaction.cc L233-L300
bool trans_commit(THD *thd, bool ignore_global_read_lock) {
  int res;
  DBUG_TRACE;

  DBUG_EXECUTE_IF(
      "crash_on_transactional_ddl_commit",
      if (thd->m_transactional_ddl.inited() &&
          thd->lex->sql_command == SQLCOM_COMMIT) { DBUG_SUICIDE(); });

  if (trans_check_state(thd)) return true;

  thd->server_status &=
      ~(SERVER_STATUS_IN_TRANS | SERVER_STATUS_IN_TRANS_READONLY);
  DBUG_PRINT("info", ("clearing SERVER_STATUS_IN_TRANS"));
  res = ha_commit_trans(thd, true, ignore_global_read_lock);
  if (res == false)
    if (thd->rpl_thd_ctx.session_gtids_ctx().notify_after_transaction_commit(
            thd))
      LogErr(WARNING_LEVEL, ER_TRX_GTID_COLLECT_REJECT);
  /*
    When gtid mode is enabled, a transaction may cause binlog
    rotation, which inserts a record into the gtid system table
    (which is probably a transactional table). Thence, the flag
    SERVER_STATUS_IN_TRANS may be set again while calling
    ha_commit_trans(...) Consequently, we need to reset it back,
    much like we are doing before calling ha_commit_trans(...).

    We would really only need to do this when gtid_mode=on.  However,
    checking gtid_mode requires holding a lock, which is costly.  So
    we clear the bit unconditionally.  This has no side effects since
    if gtid_mode=off the bit is already cleared.
  */
  thd->server_status &= ~SERVER_STATUS_IN_TRANS;
  thd->variables.option_bits &= ~OPTION_BEGIN;
  thd->get_transaction()->reset_unsafe_rollback_flags(Transaction_ctx::SESSION);
  thd->lex->start_transaction_opt = 0;

  /* The transaction should be marked as complete in P_S. */
  assert(thd->m_transaction_psi == nullptr);

  thd->tx_priority = 0;

  trans_track_end_trx(thd);

  /*
    Avoid updating modified uncommitted objects when committing attachable
    read-write transaction. This is required to allow I_S queries to update
    table statistics during CREATE TABLE ... SELECT, otherwise the
    uncommitted object added by DDL would be removed by I_S query.
  */
  if (!thd->is_attachable_rw_transaction_active()) {
    /*
      If the SE failed to commit the transaction, we must rollback the
      modified dictionary objects to make sure the DD cache, the DD
      tables and the state in the SE stay in sync.
    */
    if (res)
      thd->dd_client()->rollback_modified_objects();
    else
      thd->dd_client()->commit_modified_objects();
  }

  thd->locked_tables_list.adjust_renamed_tablespace_mdls(&thd->mdl_context);

  thd->m_transactional_ddl.post_ddl();

  return res;
}
```

문장 끝의 짝이다. 문장 트랜잭션이 활성일 때만 `ha_commit_trans(thd, false)` 를 부른다.

`sql` / `transaction.cc` L513-L549 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/transaction.cc#L513-L549))

```cpp
// transaction.cc L513-L549
bool trans_commit_stmt(THD *thd, bool ignore_global_read_lock) {
  DBUG_TRACE;
  int res = false;
  /*
    We currently don't invoke commit/rollback at end of
    a sub-statement.  In future, we perhaps should take
    a savepoint for each nested statement, and release the
    savepoint when statement has succeeded.
  */
  assert(!thd->in_sub_stmt);

  /*
    Some code in MYSQL_BIN_LOG::commit and ha_commit_low() is not safe
    for attachable transactions.
  */
  assert(!thd->is_attachable_ro_transaction_active());

  thd->get_transaction()->merge_unsafe_rollback_flags();

  if (thd->get_transaction()->is_active(Transaction_ctx::STMT)) {
    res = ha_commit_trans(thd, false, ignore_global_read_lock);
    if (!thd->in_active_multi_stmt_transaction())
      trans_reset_one_shot_chistics(thd);
  } else if (tc_log)
    res = tc_log->commit(thd, false);
  if (res == false && !thd->in_active_multi_stmt_transaction())
    if (thd->rpl_thd_ctx.session_gtids_ctx().notify_after_transaction_commit(
            thd))
      LogErr(WARNING_LEVEL, ER_TRX_GTID_COLLECT_REJECT);
  /* In autocommit=1 mode the transaction should be marked as complete in P_S */
  assert(thd->in_active_multi_stmt_transaction() ||
         thd->m_transaction_psi == nullptr);

  thd->get_transaction()->reset(Transaction_ctx::STMT);

  return res;
}
```

## 동작 흐름

```text
 L237   디버그: 트랜잭션 DDL 커밋 전에 죽는 지점
 L242   trans_check_state                       저장 함수, 트리거 안이거나 XA 중이면 거부 (L93)
 L244   SERVER_STATUS_IN_TRANS, IN_TRANS_READONLY 를 먼저 지운다
 L247   [02] ha_commit_trans(thd, true, ignore_global_read_lock)
 L248   성공이면 session_gtids_ctx 에 커밋 알림
 L265   SERVER_STATUS_IN_TRANS 를 한 번 더 지운다   GTID 테이블 기록이 다시 켰을 수 있다 (주석 L252-L264)
 L266   option_bits 에서 OPTION_BEGIN 을 지운다    이제 BEGIN 밖이다
 L267   세션 unsafe rollback 표시 초기화
 L275   trans_track_end_trx
 L283   attachable rw 트랜잭션이 아니면
 L290     실패  dd_client()->rollback_modified_objects
 L292     성공  dd_client()->commit_modified_objects
 L299   return res
```

`COMMIT` 문과 autocommit 문장 끝은 같은 [02] 에 다른 `all` 로 들어간다. 무엇이 "진짜 커밋"이 되는지는 [02] 가 정한다.

```text
 두 입구 (sql_parse.cc 의 호출 줄)

 입구                   호출 줄               all     진짜 커밋이 되는 조건
 trans_commit           L4350 (COMMIT)        true    항상 (세션 트랜잭션 전체)
 trans_commit_stmt      L4973 (finish:)       false   SESSION 목록이 비어 있을 때 = autocommit 이고 BEGIN 밖
 trans_commit_implicit  L3369, L5026 (DDL)    true    트랜잭션 모드이거나 OPTION_TABLE_LOCK 일 때 (transaction.cc L332, L340)
                                                      아니면 ha_commit_trans 없이 tc_log->commit(thd, true) 만 (L342)

 trans_commit_stmt 는 STMT 가 비활성이면 ha_commit_trans 대신 tc_log->commit(thd, false) 를 부른다 (transaction.cc L536-L537)
```

## 결과가 쓰이는 곳

```text
 res
      --> [명령 디스패치] 의 mysql_execute_command 가 오류면 goto error, 아니면 my_ok
 SERVER_STATUS_IN_TRANS 해제
      --> 다음 OK 패킷의 상태 플래그. 클라이언트가 트랜잭션 밖임을 안다
 OPTION_BEGIN 해제
      --> 다음 문장에서 innobase_register_trx 가 SESSION 목록 등록을 할지 판단하는 재료
```

## 다루지 않는 것

`trans_check_state` 의 XA 상태 검사, GTID 수집(`session_gtids_ctx`), 세션 트랜잭션 상태 추적(`trans_track_end_trx`), 데이터 사전 캐시의 확정과 되돌리기, 원자적 DDL(`m_transactional_ddl.post_ddl`), `COMMIT AND CHAIN` 과 `RELEASE` 의 처리(호출하는 쪽 [명령 디스패치] 에 있다)는 이 흐름의 곁가지라 줄만 적었다.
