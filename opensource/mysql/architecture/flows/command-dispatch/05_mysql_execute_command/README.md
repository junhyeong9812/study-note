# mysql_execute_command

상위: [명령 디스패치](../README.md)

**파싱된 문장 하나를 실행하고 문장 트랜잭션을 끝내는 곳이다.** 2000줄이 넘는 함수지만 모양은 셋으로 나뉜다. 앞의 공통 검사(암묵 커밋, 읽기 전용, GTID), 가운데의 `switch (lex->sql_command)`, 뒤의 `finish:` 이다. DML 과 SELECT 는 거의 전부 `lex->m_sql_cmd->execute(thd)` 한 줄로 [06] 에 위임되고, 이 함수가 직접 쥐는 것은 문장의 앞뒤다. 특히 `finish:` 의 `trans_commit_stmt` 가 autocommit 모드에서 실제 커밋이 일어나는 자리다.

## 위치

`sql` / `sql_parse.cc` L3031-L5119 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L3031-L5119))

## 실제 코드

DDL 처럼 암묵 커밋을 일으키는 문장은 실행 전에 열린 트랜잭션을 커밋한다.

`sql` / `sql_parse.cc` L3346-L3371 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L3346-L3371))

```cpp
// sql_parse.cc L3346-L3371
  /*
    End a active transaction so that this command will have it's
    own transaction and will also sync the binary log. If a DDL is
    not run in it's own transaction it may simply never appear on
    the slave in case the outside transaction rolls back.
  */
  if (stmt_causes_implicit_commit(thd, CF_IMPLICIT_COMMIT_BEGIN)) {
    /*
      Note that this should never happen inside of stored functions
      or triggers as all such statements prohibited there.
    */
    assert(!thd->in_sub_stmt);
    /* Statement transaction still should not be started. */
    assert(thd->get_transaction()->is_empty(Transaction_ctx::STMT));

    /*
      Implicit commit is not allowed with an active XA transaction.
      In this case we should not release metadata locks as the XA transaction
      will not be rolled back. Therefore we simply return here.
    */
    if (trans_check_state(thd)) return -1;

    /* Commit the normal transaction if one is active. */
    if (trans_commit_implicit(thd)) return -1;
    /* Release metadata locks acquired in this transaction. */
    thd->mdl_context.release_transactional_locks();
```

본 switch 의 DML 갈래다. 권한 검사부터 실행까지 전부 `Sql_cmd` 객체가 한다.

`sql` / `sql_parse.cc` L3787-L3805 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L3787-L3805))

```cpp
// sql_parse.cc L3787-L3805
    case SQLCOM_REPLACE:
    case SQLCOM_INSERT:
    case SQLCOM_REPLACE_SELECT:
    case SQLCOM_INSERT_SELECT:
    case SQLCOM_DELETE:
    case SQLCOM_DELETE_MULTI:
    case SQLCOM_UPDATE:
    case SQLCOM_UPDATE_MULTI:
    case SQLCOM_CREATE_TABLE:
    case SQLCOM_CREATE_INDEX:
    case SQLCOM_DROP_INDEX:
    case SQLCOM_ASSIGN_TO_KEYCACHE:
    case SQLCOM_PRELOAD_KEYS:
    case SQLCOM_LOAD: {
      assert(first_table == all_tables && first_table != nullptr);
      assert(lex->m_sql_cmd != nullptr);
      res = lex->m_sql_cmd->execute(thd);
      break;
    }
```

`BEGIN` 과 `COMMIT` 은 이 switch 에서 직접 처리한다.

`sql` / `sql_parse.cc` L4337-L4364 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L4337-L4364))

```cpp
// sql_parse.cc L4337-L4364
    case SQLCOM_BEGIN:
      if (trans_begin(thd, lex->start_transaction_opt)) goto error;
      my_ok(thd);
      break;
    case SQLCOM_COMMIT: {
      assert(thd->lock == nullptr ||
             thd->locked_tables_mode == LTM_LOCK_TABLES);
      const bool tx_chain =
          (lex->tx_chain == TVL_YES ||
           (thd->variables.completion_type == 1 && lex->tx_chain != TVL_NO));
      const bool tx_release =
          (lex->tx_release == TVL_YES ||
           (thd->variables.completion_type == 2 && lex->tx_release != TVL_NO));
      if (trans_commit(thd)) goto error;
      thd->mdl_context.release_transactional_locks();
      /* Begin transaction with the same isolation level. */
      if (tx_chain) {
        if (trans_begin(thd)) goto error;
      } else {
        /* Reset the isolation level and access mode if no chaining
         * transaction.*/
        trans_reset_one_shot_chistics(thd);
      }
      /* Disconnect the current client connection. */
      if (tx_release) thd->killed = THD::KILL_CONNECTION;
      my_ok(thd);
      break;
    }
```

`finish:` 의 앞쪽이다. 진단 영역에 오류가 있으면 문장 롤백, 아니면 문장 커밋을 한다.

`sql` / `sql_parse.cc` L4917-L4984 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L4917-L4984))

```cpp
// sql_parse.cc L4917-L4984
error:
  res = true;

finish:
  /* Restore system variables which were changed by SET_VAR hint. */
  if (lex->opt_hints_global && lex->opt_hints_global->sys_var_hint)
    lex->opt_hints_global->sys_var_hint->restore_vars(thd);

  THD_STAGE_INFO(thd, stage_query_end);

  // Check for receiving a recent kill signal
  if (thd->killed) {
    thd->send_kill_message();
    res = thd->is_error();
  }
  if (res) {
    if (thd->get_reprepare_observer() != nullptr &&
        thd->get_reprepare_observer()->is_invalidated() &&
        thd->get_reprepare_observer()->can_retry())
      thd->skip_gtid_rollback = true;
  } else {
    lex->set_exec_started();
  }

  // Cleanup EXPLAIN info
  if (!thd->in_sub_stmt) {
    if (is_explainable_query(lex->sql_command)) {
      DEBUG_SYNC(thd, "before_reset_query_plan");
      /*
        We want EXPLAIN CONNECTION to work until the explained statement ends,
        thus it is only now that we may fully clean up any unit of this
        statement.
      */
      lex->unit->assert_not_fully_clean();
    }
    thd->query_plan.set_query_plan(SQLCOM_END, nullptr, false);
  }

  assert(!thd->in_active_multi_stmt_transaction() ||
         thd->in_multi_stmt_transaction_mode());

  if (!thd->in_sub_stmt) {
    mysql_event_tracking_query_notify(
        thd,
        first_level ? EVENT_TRACKING_QUERY_STATUS_END
                    : EVENT_TRACKING_QUERY_NESTED_STATUS_END,
        first_level ? "EVENT_TRACKING_QUERY_STATUS_END"
                    : "EVENT_TRACKING_QUERY_NESTED_STATUS_END");

    /* report error issued during command execution */
    if ((thd->is_error() && !early_error_on_rep_command) ||
        (thd->variables.option_bits & OPTION_MASTER_SQL_ERROR))
      trans_rollback_stmt(thd);
    else {
      /* If commit fails, we should be able to reset the OK status. */
      thd->get_stmt_da()->set_overwrite_status(true);
      trans_commit_stmt(thd);
      thd->get_stmt_da()->set_overwrite_status(false);
    }
    /*
      Reset thd killed flag during cleanup so that commands which are
      dispatched using service session API's start with a clean state.
    */
    if (thd->killed == THD::KILL_QUERY || thd->killed == THD::KILL_TIMEOUT) {
      thd->killed = THD::NOT_KILLED;
      thd->reset_query_for_display();
    }
  }
```

`finish:` 의 뒤쪽이다. 테이블을 닫고, 트랜잭션 상태에 따라 MDL 을 푼다.

`sql` / `sql_parse.cc` L4999-L5045 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L4999-L5045))

```cpp
// sql_parse.cc L4999-L5045

  /* Free tables */
  THD_STAGE_INFO(thd, stage_closing_tables);
  close_thread_tables(thd);

  // Rollback any item transformations made during optimization and execution
  thd->rollback_item_tree_changes();

#ifndef NDEBUG
  if (lex->sql_command != SQLCOM_SET_OPTION && !thd->in_sub_stmt)
    DEBUG_SYNC(thd, "execute_command_after_close_tables");
#endif

  if (!thd->in_sub_stmt && thd->transaction_rollback_request) {
    /*
      We are not in sub-statement and transaction rollback was requested by
      one of storage engines (e.g. due to deadlock). Rollback transaction in
      all storage engines including binary log.
    */
    trans_rollback_implicit(thd);
    thd->mdl_context.release_transactional_locks();
  } else if (stmt_causes_implicit_commit(thd, CF_IMPLICIT_COMMIT_END)) {
    /* No transaction control allowed in sub-statements. */
    assert(!thd->in_sub_stmt);
    /* If commit fails, we should be able to reset the OK status. */
    thd->get_stmt_da()->set_overwrite_status(true);
    /* Commit the normal transaction if one is active. */
    trans_commit_implicit(thd);
    thd->get_stmt_da()->set_overwrite_status(false);
    thd->mdl_context.release_transactional_locks();
  } else if (!thd->in_sub_stmt && !thd->in_multi_stmt_transaction_mode()) {
    /*
      - If inside a multi-statement transaction,
      defer the release of metadata locks until the current
      transaction is either committed or rolled back. This prevents
      other statements from modifying the table for the entire
      duration of this transaction.  This provides commit ordering
      and guarantees serializability across multiple transactions.
      - If in autocommit mode, or outside a transactional context,
      automatically release metadata locks of the current statement.
    */
    thd->mdl_context.release_transactional_locks();
  } else if (!thd->in_sub_stmt &&
             (thd->lex->sql_command != SQLCOM_CREATE_TABLE ||
              !thd->lex->create_info->m_transactional_ddl)) {
    thd->mdl_context.release_statement_locks();
  }
```

암묵 커밋 여부는 문장 종류별 플래그와 몇 가지 예외로 정해진다.

`sql` / `sql_parse.cc` L406-L438 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_parse.cc#L406-L438))

```cpp
// sql_parse.cc L406-L438
bool stmt_causes_implicit_commit(const THD *thd, uint mask) {
  DBUG_TRACE;
  const LEX *lex = thd->lex;

  /* LOAD DATA ALGORITHM=BULK need to commit implicitly. */
  if (lex->sql_command == SQLCOM_LOAD && lex->m_sql_cmd->is_bulk_load()) {
    return true;
  }

  if ((sql_command_flags[lex->sql_command] & mask) == 0 ||
      thd->is_plugin_fake_ddl())
    return false;

  switch (lex->sql_command) {
    case SQLCOM_DROP_TABLE:
      return !lex->drop_temporary;
    case SQLCOM_ALTER_TABLE:
    case SQLCOM_CREATE_TABLE:
      /* If CREATE TABLE of non-temporary table or without
        START TRANSACTION, do implicit commit */
      return (lex->create_info->options & HA_LEX_CREATE_TMP_TABLE ||
              lex->create_info->m_transactional_ddl) == 0;
    case SQLCOM_SET_OPTION:
      /* Implicitly commit a transaction started by a SET statement */
      return lex->autocommit;
    case SQLCOM_RESET:
      return lex->option_type != OPT_PERSIST;
    case SQLCOM_STOP_GROUP_REPLICATION:
      return lex->was_replication_command_executed();
    default:
      return true;
  }
}
```

## 동작 흐름

```text
 L3070  CREATE TABLE ... START TRANSACTION 뒤라면 COMMIT / ROLLBACK 등만 허용
 L3120  lex->first_lists_tables_same, L3122 all_tables = lex->query_tables
 L3194  복제 적용 스레드면 복제 필터 검사
 L3308  read_only / super_read_only 면 갱신 문장 거부
 L3314  Com_<종류> +1
 L3331  gtid_pre_statement_checks                  EXECUTE / CANCEL / SKIP
 L3352  stmt_causes_implicit_commit(BEGIN 쪽)
          L3366 trans_check_state  L3369 trans_commit_implicit  L3371 MDL 해제
 L3378  감사 QUERY_START
 L3407  Disable_autocommit_guard                    DD 테이블을 갱신하는 문장용
 L3417  읽기 전용 트랜잭션에서 금지된 문장이면 오류
 L3452  CF_PREOPEN_TMP_TABLES 면 임시 테이블을 먼저 연다

 L3486  switch (lex->sql_command)
          INSERT / UPDATE / DELETE / REPLACE / LOAD, CREATE TABLE, CREATE INDEX ...
                         L3803  m_sql_cmd->execute(thd)    --> [06] Sql_cmd_dml::execute
          SELECT, SHOW *, CALL, DO ...
                         L4766  m_sql_cmd->execute(thd)
          BEGIN          L4338  trans_begin
          COMMIT         L4350  trans_commit              --> [커밋과 binlog 2PC]
                         L4351  MDL 해제, L4353 AND CHAIN 이면 trans_begin
                         L4361  RELEASE 면 KILL_CONNECTION
          ROLLBACK       L4374  trans_rollback
          default        L4910  assert(0)

 L4917  error: res = true
 L4920  finish:
 L4928  killed 면 kill 메시지
 L4959  감사 QUERY_STATUS_END (하위 문장이 아닐 때)
 L4967  오류가 있으면 L4969 trans_rollback_stmt
        없으면       L4973 trans_commit_stmt         --> [커밋과 binlog 2PC]
 L4998  lex->cleanup(true)
 L5002  close_thread_tables                          external_lock(F_UNLCK) 이 여기서
 L5012  엔진이 롤백을 요청했으면 (교착 희생자)      L5018 trans_rollback_implicit
 L5020  암묵 커밋 문장(END 쪽)이면                  L5026 trans_commit_implicit
 L5029  autocommit 이거나 트랜잭션 밖이면            L5040 트랜잭션 MDL 까지 해제
 L5041  아니면                                      L5044 문장 MDL 만 해제
 L5118  return
```

같은 `INSERT` 한 문장이라도 autocommit 설정에 따라 이 함수의 어느 줄에서 커밋이 끝나는지가 다르다.

```text
 커밋이 일어나는 줄 (INSERT 한 문장)

 autocommit=1
   [08] 2PC 등록          trans_register_ha(stmt) 만 (ha_innodb.cc L3045-L3050)
   L4973                  ha_commit_trans(all=false)
                          SESSION 이 비어 있어 is_real_trans = true -> 진짜 커밋 (handler.cc L1713)
   L5040                  트랜잭션 MDL 까지 해제
   COMMIT 문              필요 없음

 autocommit=0 또는 BEGIN 뒤
   [08] 2PC 등록          stmt 와 all 둘 다
   L4973                  ha_commit_trans(all=false)
                          is_real_trans = false -> 문장 끝 표시만
   L5044                  문장 MDL 만 해제, 테이블 MDL 은 트랜잭션 끝까지
   COMMIT 문              L4350 trans_commit -> ha_commit_trans(all=true) 에서 진짜 커밋
```

```text
 오류가 났을 때의 갈래 (finish: 이후)

 L 줄    호출                      조건과 범위
 L4969   trans_rollback_stmt       thd->is_error() (엔진 오류를 포함한 진단 영역의 오류). 문장만 롤백
 L5018   trans_rollback_implicit   transaction_rollback_request. 트랜잭션 전체
                                   (교착, 또는 innodb_rollback_on_timeout=ON 일 때의 잠금 대기
                                    시간 초과로 엔진이 롤백을 요청한 경우. ha_innodb.cc L2178)
 L5026   trans_commit_implicit     CF_IMPLICIT_COMMIT_END 문장 (DDL). 문장 뒤 한 번 더 커밋

 DDL 은 앞(L3369)과 뒤(L5026) 두 번 커밋해서 자기만의 트랜잭션에 갇힌다 (주석 L3346-L3351)
```

## 결과가 쓰이는 곳

```text
 res
      --> [03] 이 받지만 결과 패킷은 진단 영역(thd->get_stmt_da()) 상태로 [02] done: 에서 나간다

 trans_commit_stmt / trans_commit
      --> [커밋과 binlog 2PC] 의 [01] trans_commit, [02] ha_commit_trans

 close_thread_tables
      --> 테이블마다 ha_external_lock(F_UNLCK), [08] 의 뒤쪽 분기
```

## 다루지 않는 것

DDL, 계정, 복제, 플러그인 명령 등 switch 안의 수백 개 case, 복제 적용 스레드 전용 분기(필터, deferred events, `launch_hook_trans_begin`), GTID 사전 검사의 내부, EXPLAIN FOR CONNECTION 용 `query_plan`, SET_VAR 힌트, `LOCK TABLES` 모드와 prelocking 은 이 흐름의 곁가지라 줄만 적었다. 커밋 자체는 [커밋과 binlog 2PC](../../commit-2pc/README.md)에서 다룬다.
