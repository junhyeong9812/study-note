# mysql_inplace_alter_table

상위: [온라인 DDL](../README.md)

**서버 계층에서 INPLACE 와 INSTANT ALTER 를 지휘하는 함수다.** 엔진이 돌려준 `enum_alter_inplace_result` 에 맞춰 MDL 을 올리고 내리면서 엔진의 세 단계 `prepare -> inplace -> commit` 을 차례로 부르고, 끝나면 데이터 사전(DD)에 새 정의를 저장하고 binlog 를 쓴 뒤 커밋한다. 이 함수에 "온라인" 의 정체가 적혀 있다. 무거운 [04] 를 부르는 동안만 잠금을 SU 로 내려 두고, 그 앞뒤는 X 로 묶는다.

## 위치

`sql` / `sql_table.cc` L14394-L14988 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L14394-L14988))

## 실제 코드

호출하는 쪽이다. `mysql_alter_table` 이 엔진에 물어 알고리즘을 고르고, 사용자가 쓴 `ALGORITHM=` / `LOCK=` 과 맞지 않으면 여기서 오류를 낸다.

`sql` / `sql_table.cc` L18374-L18548 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L18374-L18548))

```cpp
// sql_table.cc L18374-L18548
  if (alter_info->requested_algorithm !=
      Alter_info::ALTER_TABLE_ALGORITHM_COPY) {
    Alter_inplace_info ha_alter_info(create_info, alter_info,
                                     alter_ctx.error_if_not_empty, key_info,
                                     key_count, thd->work_part_info);
    TABLE *altered_table = nullptr;
    bool use_inplace = true;

    /* Fill the Alter_inplace_info structure. */
    if (fill_alter_inplace_info(thd, table, &ha_alter_info))
      goto err_new_table_cleanup;

    // ... (L18386-L18401 생략: 디버그 주입)
    // ... (L18402-L18422 생략: altered_table 열기와 표시)
    // ... (L18423-L18447 생략: handler_flags == 0 이면 아무 일 없는 ALTER)

    // Ask storage engine whether to use copy or in-place
    enum_alter_inplace_result inplace_supported =
        table->file->check_if_supported_inplace_alter(altered_table,
                                                      &ha_alter_info);

    // If INSTANT was requested but it is not supported, report error.
    if (alter_info->requested_algorithm ==
            Alter_info::ALTER_TABLE_ALGORITHM_INSTANT &&
        inplace_supported != HA_ALTER_INPLACE_INSTANT &&
        inplace_supported != HA_ALTER_ERROR) {
      ha_alter_info.report_unsupported_error("ALGORITHM=INSTANT",
                                             "ALGORITHM=COPY/INPLACE");
      close_temporary_table(thd, altered_table, true, false);
      goto err_new_table_cleanup;
    }

    switch (inplace_supported) {
      case HA_ALTER_INPLACE_EXCLUSIVE_LOCK:
        // If SHARED lock and no particular algorithm was requested, use COPY.
        if (alter_info->requested_lock == Alter_info::ALTER_TABLE_LOCK_SHARED &&
            alter_info->requested_algorithm ==
                Alter_info::ALTER_TABLE_ALGORITHM_DEFAULT) {
          use_inplace = false;
        }
        // Otherwise, if weaker lock was requested, report error.
        else if (alter_info->requested_lock ==
                     Alter_info::ALTER_TABLE_LOCK_NONE ||
                 alter_info->requested_lock ==
                     Alter_info::ALTER_TABLE_LOCK_SHARED) {
          ha_alter_info.report_unsupported_error("LOCK=NONE/SHARED",
                                                 "LOCK=EXCLUSIVE");
          close_temporary_table(thd, altered_table, true, false);
          goto err_new_table_cleanup;
        }
        break;
      case HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE:
      case HA_ALTER_INPLACE_SHARED_LOCK:
        // If weaker lock was requested, report error.
        if (alter_info->requested_lock == Alter_info::ALTER_TABLE_LOCK_NONE) {
          ha_alter_info.report_unsupported_error("LOCK=NONE", "LOCK=SHARED");
          close_temporary_table(thd, altered_table, true, false);
          goto err_new_table_cleanup;
        }
        break;
      case HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE:
      case HA_ALTER_INPLACE_NO_LOCK:
      case HA_ALTER_INPLACE_INSTANT:
        /*
          Note that any instant operation is also in fact in-place operation.

          It is totally safe to execute operation using instant algorithm if it
          has no drawbacks as compared to in-place algorithm even if user
          explicitly asked for ALGORITHM=INPLACE. Doing so, also allows to
          keep code in engines which support only limited subset of in-place
          ALTER TABLE operations as instant metadata only changes simple.

          If instant algorithm has some downsides to in-place algorithm and user
          explicitly asks for ALGORITHM=INPLACE it is responsibility of storage
          engine to fallback to in-place algorithm execution by returning
          HA_ALTER_INPLACE_NO_LOCK or HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE.
        */
        break;
      case HA_ALTER_INPLACE_NOT_SUPPORTED:
        // If INPLACE was requested, report error.
        if (alter_info->requested_algorithm ==
            Alter_info::ALTER_TABLE_ALGORITHM_INPLACE) {
          ha_alter_info.report_unsupported_error("ALGORITHM=INPLACE",
                                                 "ALGORITHM=COPY");
          close_temporary_table(thd, altered_table, true, false);
          goto err_new_table_cleanup;
        }
        // COPY with LOCK=NONE is not supported, no point in trying.
        if (alter_info->requested_lock == Alter_info::ALTER_TABLE_LOCK_NONE) {
          ha_alter_info.report_unsupported_error("LOCK=NONE", "LOCK=SHARED");
          close_temporary_table(thd, altered_table, true, false);
          goto err_new_table_cleanup;
        }
        // Otherwise use COPY
        use_inplace = false;
        break;
      case HA_ALTER_ERROR:
      default:
        close_temporary_table(thd, altered_table, true, false);
        goto err_new_table_cleanup;
    }

    if (use_inplace) {
      if (mysql_inplace_alter_table(thd, *schema, *new_schema, old_table_def,
                                    table_def, table_list, table, altered_table,
                                    &ha_alter_info, inplace_supported,
                                    &alter_ctx, columns, fk_key_info,
                                    fk_key_count, &fk_invalidator)) {
        return true;
      }

      goto end_inplace;
    } else {
      close_temporary_table(thd, altered_table, true, false);
    }
  }
```

그 전에, 엔진에 묻지도 않고 COPY 로 정해 버리는 조건이 있다.

`sql` / `sql_table.cc` L17987-L18020 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L17987-L18020))

```cpp
// sql_table.cc L17987-L18020
  /*
    Use copy algorithm if:
    - old_alter_table system variable is set without in-place requested using
      the ALGORITHM clause.
    - Or if in-place is impossible for given operation.
    - Changes to partitioning needs to be handled using table copying
      algorithm unless the engine supports partitioning changes using
      in-place API (because it supports auto-partitioning or simply
      can do partitioning changes using in-place using mark-up in
      partition_info object).
  */
  if ((thd->variables.old_alter_table &&
       alter_info->requested_algorithm !=
           Alter_info::ALTER_TABLE_ALGORITHM_INPLACE &&
       alter_info->requested_algorithm !=
           Alter_info::ALTER_TABLE_ALGORITHM_INSTANT) ||
      is_inplace_alter_impossible(table, create_info, alter_info) ||
      (partition_changed &&
       !(table->s->db_type()->partition_flags() & HA_USE_AUTO_PARTITION) &&
       !new_part_info)) {
    if (alter_info->requested_algorithm ==
        Alter_info::ALTER_TABLE_ALGORITHM_INPLACE) {
      my_error(ER_ALTER_OPERATION_NOT_SUPPORTED, MYF(0), "ALGORITHM=INPLACE",
               "ALGORITHM=COPY");
      return true;
    }
    if (alter_info->requested_algorithm ==
        Alter_info::ALTER_TABLE_ALGORITHM_INSTANT) {
      my_error(ER_ALTER_OPERATION_NOT_SUPPORTED, MYF(0), "ALGORITHM=INSTANT",
               "ALGORITHM=COPY");
      return true;
    }
    alter_info->requested_algorithm = Alter_info::ALTER_TABLE_ALGORITHM_COPY;
  }
```

본체의 앞부분이다. 엔진이 준비 단계에서 독점을 원하면 X 로 올린다.

`sql` / `sql_table.cc` L14394-L14470 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L14394-L14470))

```cpp
// sql_table.cc L14394-L14470
static bool mysql_inplace_alter_table(
    THD *thd, const dd::Schema &schema, const dd::Schema &new_schema,
    const dd::Table *table_def, dd::Table *altered_table_def,
    Table_ref *table_list, TABLE *table, TABLE *altered_table,
    Alter_inplace_info *ha_alter_info,
    enum_alter_inplace_result inplace_supported, Alter_table_ctx *alter_ctx,
    histograms::columns_set &columns, FOREIGN_KEY *fk_key_info,
    uint fk_key_count, Foreign_key_parents_invalidator *fk_invalidator) {
  handlerton *db_type = table->s->db_type();
  MDL_ticket *mdl_ticket = table->mdl_ticket;
  Alter_info *alter_info = ha_alter_info->alter_info;
  bool reopen_tables = false;
  bool rollback_needs_dict_cache_reset = false;
  MDL_request_list mdl_requests;

  DBUG_TRACE;

  /*
    Upgrade to EXCLUSIVE lock if:
    - This is requested by the storage engine
    - Or the storage engine needs exclusive lock for just the prepare
      phase
    - Or requested by the user

    Note that we handle situation when storage engine needs exclusive
    lock for prepare phase under LOCK TABLES in the same way as when
    exclusive lock is required for duration of the whole statement.
  */
  if (inplace_supported == HA_ALTER_INPLACE_EXCLUSIVE_LOCK ||
      ((inplace_supported == HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE ||
        inplace_supported == HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE) &&
       (thd->locked_tables_mode == LTM_LOCK_TABLES ||
        thd->locked_tables_mode == LTM_PRELOCKED_UNDER_LOCK_TABLES)) ||
      alter_info->requested_lock == Alter_info::ALTER_TABLE_LOCK_EXCLUSIVE) {
    if (wait_while_table_is_used(thd, table, HA_EXTRA_FORCE_REOPEN))
      goto cleanup;
    /*
      Get rid of all TABLE instances belonging to this thread
      except one to be used for in-place ALTER TABLE.

      This is mostly needed to satisfy InnoDB assumptions/asserts.
    */
    close_all_tables_for_name(thd, table->s, false, table);
    /*
      If we are under LOCK TABLES we will need to reopen tables which we
      just have closed in case of error.
    */
    reopen_tables = true;
  } else if (inplace_supported == HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE ||
             inplace_supported == HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE) {
    /*
      Storage engine has requested exclusive lock only for prepare phase
      and we are not under LOCK TABLES.
      Don't mark TABLE_SHARE as old in this case, as this won't allow opening
      of table by other threads during main phase of in-place ALTER TABLE.
    */
    if (thd->mdl_context.upgrade_shared_lock(table->mdl_ticket, MDL_EXCLUSIVE,
                                             thd->variables.lock_wait_timeout))
      goto cleanup;

    tdc_remove_table(thd, TDC_RT_REMOVE_NOT_OWN_KEEP_SHARE, table->s->db.str,
                     table->s->table_name.str, false);
  }

  /*
    Upgrade to SHARED_NO_WRITE lock if:
    - The storage engine needs writes blocked for the whole duration
    - Or this is requested by the user
    Note that under LOCK TABLES, we will already have SHARED_NO_READ_WRITE.
  */
  if ((inplace_supported == HA_ALTER_INPLACE_SHARED_LOCK ||
       alter_info->requested_lock == Alter_info::ALTER_TABLE_LOCK_SHARED) &&
      thd->mdl_context.upgrade_shared_lock(table->mdl_ticket,
                                           MDL_SHARED_NO_WRITE,
                                           thd->variables.lock_wait_timeout)) {
    goto cleanup;
  }
```

엔진의 세 단계를 부르는 부분이다. prepare 뒤에 잠금을 내리고, inplace 뒤에 다시 올린다.

`sql` / `sql_table.cc` L14571-L14677 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L14571-L14677))

```cpp
// sql_table.cc L14571-L14677
  switch (inplace_supported) {
    case HA_ALTER_ERROR:
    case HA_ALTER_INPLACE_NOT_SUPPORTED:
      assert(0);
      [[fallthrough]];
    case HA_ALTER_INPLACE_NO_LOCK:
    case HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE:
      switch (alter_info->requested_lock) {
        case Alter_info::ALTER_TABLE_LOCK_DEFAULT:
        case Alter_info::ALTER_TABLE_LOCK_NONE:
          ha_alter_info->online = true;
          break;
        case Alter_info::ALTER_TABLE_LOCK_SHARED:
        case Alter_info::ALTER_TABLE_LOCK_EXCLUSIVE:
          break;
      }
      break;
    case HA_ALTER_INPLACE_EXCLUSIVE_LOCK:
    case HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE:
    case HA_ALTER_INPLACE_SHARED_LOCK:
    case HA_ALTER_INPLACE_INSTANT:
      break;
  }

  {
    /*
      We want warnings/errors about data truncation emitted when
      values of virtual columns are evaluated in INPLACE algorithm.
    */
    thd->check_for_truncated_fields = CHECK_FIELD_WARN;
    thd->num_truncated_fields = 0L;

    if (table->file->ha_prepare_inplace_alter_table(
            altered_table, ha_alter_info, table_def, altered_table_def)) {
      goto rollback;
    }

    /*
      Downgrade the lock if storage engine has told us that exclusive lock was
      necessary only for prepare phase (unless we are not under LOCK TABLES) and
      user has not explicitly requested exclusive lock.
    */
    if ((inplace_supported == HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE ||
         inplace_supported == HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE) &&
        !(thd->locked_tables_mode == LTM_LOCK_TABLES ||
          thd->locked_tables_mode == LTM_PRELOCKED_UNDER_LOCK_TABLES) &&
        (alter_info->requested_lock !=
         Alter_info::ALTER_TABLE_LOCK_EXCLUSIVE)) {
      /* If storage engine or user requested shared lock downgrade to SNW. */
      if (inplace_supported == HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE ||
          alter_info->requested_lock == Alter_info::ALTER_TABLE_LOCK_SHARED)
        table->mdl_ticket->downgrade_lock(MDL_SHARED_NO_WRITE);
      else {
        assert(inplace_supported == HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE);
        table->mdl_ticket->downgrade_lock(MDL_SHARED_UPGRADABLE);
      }
    }

    DEBUG_SYNC(thd, "alter_table_inplace_after_lock_downgrade");
    THD_STAGE_INFO(thd, stage_alter_inplace);

    if (table->file->ha_inplace_alter_table(altered_table, ha_alter_info,
                                            table_def, altered_table_def)) {
      goto rollback;
    }

    // Upgrade to EXCLUSIVE before commit.
    if (wait_while_table_is_used(thd, table, HA_EXTRA_PREPARE_FOR_RENAME))
      goto rollback;

    // ... (L14641-L14669 생략: 외래 키 테이블 잠금, 히스토그램 삭제, 디버그 주입)

    DEBUG_SYNC(thd, "alter_table_inplace_before_commit");
    THD_STAGE_INFO(thd, stage_alter_inplace_commit);

    if (table->file->ha_commit_inplace_alter_table(
            altered_table, ha_alter_info, true, table_def, altered_table_def)) {
      goto rollback;
    }
```

엔진 커밋 뒤 DD 에 새 정의를 넣고, binlog 를 쓰고, 문장을 커밋한다.

`sql` / `sql_table.cc` L14703-L14748 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L14703-L14748))

```cpp
// sql_table.cc L14703-L14748
    altered_table_def->set_schema_id(table_def->schema_id());
    altered_table_def->set_name(alter_ctx->alias);
    // ... (L14705-L14715 생략: 이름과 트리거 복사)
    if (thd->dd_client()->drop(table_def)) goto cleanup2;
    table_def = nullptr;

    DEBUG_SYNC_C("alter_table_after_dd_client_drop");

    // Reset check constraint's mode.
    reset_check_constraints_alter_mode(altered_table_def);

    if ((db_type->flags & HTON_SUPPORTS_ATOMIC_DDL)) {
      /*
        For engines supporting atomic DDL we have delayed storing new
        table definition in the data-dictionary so far in order to avoid
        conflicts between old and new definitions on foreign key names.
        Since the old table definition is gone we can safely store new
        definition now.
      */
      if (thd->dd_client()->store(altered_table_def)) goto cleanup2;
    } else {
      if (thd->dd_client()->update(altered_table_def)) goto cleanup2;

      /*
        Persist changes to data-dictionary for storage engines which don't
        support atomic DDL. Such SEs can't rollback in-place changes if error
        or crash happens after this point, so we are better to have
        data-dictionary in sync with SE.

        Prevent intermediate commits to invoke commit order
      */
      const Implicit_substatement_state_guard substatement_guard(thd);

      if (trans_commit_stmt(thd) || trans_commit_implicit(thd)) goto cleanup2;
    }
  }
```

`sql` / `sql_table.cc` L14822-L14886 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L14822-L14886))

```cpp
// sql_table.cc L14822-L14886
  ha_binlog_log_query(thd, ha_alter_info->create_info->db_type,
                      LOGCOM_ALTER_TABLE, thd->query().str, thd->query().length,
                      alter_ctx->db, alter_ctx->table_name);

  assert(!(mysql_bin_log.is_open() &&
           thd->is_current_stmt_binlog_format_row() &&
           (ha_alter_info->create_info->options & HA_LEX_CREATE_TMP_TABLE)));

  if (write_bin_log(thd, true, thd->query().str, thd->query().length,
                    (db_type->flags & HTON_SUPPORTS_ATOMIC_DDL)))
    goto cleanup2;

  // ... (L14834-L14876 생략: 참조 뷰 메타데이터 갱신과 GTID 가드 설정)
    const Implicit_substatement_state_guard guard(thd, mode);

    /*
      Commit ALTER TABLE. Needs to be done here and not in the callers
      (which do it anyway) to be able notify SE about changed table.
    */
    if (trans_commit_stmt(thd) || trans_commit_implicit(thd)) goto cleanup2;

    /* Call SE DDL post-commit hook. */
    if (db_type->post_ddl) db_type->post_ddl(thd);
```

실패하면 `rollback:` 에서 엔진에 `commit=false` 로 다시 알린다.

`sql` / `sql_table.cc` L14914-L14933 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_table.cc#L14914-L14933))

```cpp
// sql_table.cc L14914-L14933
rollback:
  table->file->ha_commit_inplace_alter_table(
      altered_table, ha_alter_info, false, table_def, altered_table_def);
  thd->check_for_truncated_fields = CHECK_FIELD_IGNORE;

cleanup:
  close_temporary_table(thd, altered_table, true, false);

cleanup2:

  (void)trans_rollback_stmt(thd);
  /*
    Full rollback in case we have THD::transaction_rollback_request
    and to synchronize DD state in cache and on disk (as statement
    rollback doesn't clear DD cache of modified uncommitted objects).
  */
  (void)trans_rollback(thd);

  if ((db_type->flags & HTON_SUPPORTS_ATOMIC_DDL) && db_type->post_ddl)
    db_type->post_ddl(thd);
```

ALTER 는 파서에서 이미 `MDL_SHARED_UPGRADABLE` 로 테이블을 연다. 위의 업그레이드와 다운그레이드는 모두 이 표에서 출발한다.

`sql` / `parse_tree_nodes.cc` L3720-L3729 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/parse_tree_nodes.cc#L3720-L3729))

```cpp
// parse_tree_nodes.cc L3720-L3729
static bool init_alter_table_stmt(Table_ddl_parse_context *pc,
                                  Table_ident *table_name,
                                  Alter_info::enum_alter_table_algorithm algo,
                                  Alter_info::enum_alter_table_lock lock,
                                  Alter_info::enum_with_validation validation) {
  LEX *lex = pc->thd->lex;
  if (!lex->query_block->add_table_to_list(
          pc->thd, table_name, nullptr, TL_OPTION_UPDATING, TL_READ_NO_INSERT,
          MDL_SHARED_UPGRADABLE))
    return true;
```

## 동작 흐름

```text
 mysql_alter_table 의 고르기 (sql_table.cc)

 L17998  old_alter_table=ON (ALGORITHM 명시 없음)              --> COPY
 L18003  is_inplace_alter_impossible                            --> COPY
 L18004  파티션 변경인데 엔진이 자동 파티션을 모름              --> COPY
           ALGORITHM=INPLACE/INSTANT 를 명시했으면 오류 (L18007, L18013)

 L18374  COPY 가 아니면
 L18383    fill_alter_inplace_info     handler_flags 를 채운다 (무엇이 바뀌는가)
 L18423    handler_flags == 0          아무것도 안 바뀜 -> end_inplace_noop
 L18450    [02] check_if_supported_inplace_alter
 L18455    INSTANT 를 요청했는데 INSTANT 가 아니면 오류
 L18465    switch
             EXCLUSIVE_LOCK            LOCK=SHARED 이고 ALGORITHM 명시 없으면 COPY,
                                       LOCK=NONE 이거나 LOCK=SHARED+ALGORITHM 명시면 오류
             SHARED_LOCK(_AFTER_PREPARE)  LOCK=NONE 이면 오류
             NO_LOCK(_AFTER_PREPARE), INSTANT   그대로
             NOT_SUPPORTED             INPLACE 요청이면 오류, LOCK=NONE 이면 오류, 아니면 COPY
 L18535  use_inplace -> [01] 이 함수
 L18550  아니면 COPY 로 내려간다
```

아래는 이 함수가 MDL 을 다루는 순서다. 기본값(`LOCK=DEFAULT`, LOCK TABLES 아님)에서 InnoDB 가 `NO_LOCK_AFTER_PREPARE` 를 준 경우를 기준으로 그렸다.

```text
 MDL 시간축 (ALTER 연결 A, 다른 연결 B)

 줄       A 의 MDL  A 가 하는 일                          B 의 DML
 -------  --------  ------------------------------------  ----------------------------
 파서     SU        테이블 열기, [02] 판정                 된다
 L14450   SU -> X   upgrade_shared_lock(MDL_EXCLUSIVE)     A 는 B 의 트랜잭션이 끝나길 기다린다
                    tdc_remove_table (공유 TABLE_SHARE 는 유지)
 L14518   X         lock_tables -> external_lock
 L14603   X         [03] ha_prepare_inplace_alter_table     B 는 대기
 L14625   X -> SU   downgrade_lock(MDL_SHARED_UPGRADABLE)
 L14632   SU        [04] ha_inplace_alter_table (빌드)      된다 -> [07] row log 로 기록
 L14638   SU -> X   wait_while_table_is_used               A 는 다시 B 가 끝나길 기다린다
 L14674   X         [09] ha_commit_inplace_alter_table      B 는 대기
 L14716   X         DD drop 옛 정의 / L14732 store 새 정의
 L14830   X         write_bin_log
 L14883   X         trans_commit_stmt, trans_commit_implicit
 L14886             post_ddl (InnoDB 의 DDL 로그 후처리)
 문장 끝  해제                                            새 정의로 테이블을 다시 연다
```

```text
 엔진 반환값별로 이 함수가 하는 일

 inplace_supported            준비 전 (L14422-L14470)   prepare 뒤 (L14613-L14627)  online
 EXCLUSIVE_LOCK               X (wait_while_table_is_used)  X 유지                  false
 SHARED_LOCK_AFTER_PREPARE    X                         SNW 로 내림               false
 SHARED_LOCK                  SNW                       SNW 유지                  false
 NO_LOCK_AFTER_PREPARE        X                         SU 로 내림 (LOCK=SHARED 면 SNW)  true
 NO_LOCK                      SU 그대로                 SU 유지                   true
 INSTANT                      SU 그대로                 SU 유지                   false

 online 은 L14576-L14587 에서 ha_alter_info->online 에 들어가 [03] 의 ctx->online 이 된다
   NO_LOCK(_AFTER_PREPARE) 라도 LOCK=SHARED/EXCLUSIVE 면 false 로 남는다 (L14583-L14585)
 LOCK=SHARED 를 쓰면 L14464 에서 SNW 로 올리고 (이미 X 면 그대로), prepare 뒤에도 SNW 로 내린다 (L14621)
 LOCK=EXCLUSIVE 를 쓰면 모든 경우에 L14427 로 X 를 잡고 내리지 않는다 (L14617)
 커밋 전 X 업그레이드 (L14638) 는 모든 경우에 한다
```

```text
 실패 경로

 [03] [04] [09] 가 true                 --> rollback:  L14915 ha_commit_inplace_alter_table(commit=false)
 그 외 준비 단계 실패                   --> cleanup:   L14920 임시 TABLE 닫기
 DD 저장, binlog 실패 (엔진 커밋 뒤)    --> cleanup2:  L14924 trans_rollback_stmt, L14930 trans_rollback
                                           L14939 InnoDB 사전 캐시를 비운다 (dict_cache_reset)
 원자적 DDL 엔진(InnoDB)은 DD 롤백이 엔진 변경도 되돌린다 (주석 L14699-L14701)
```

## 결과가 쓰이는 곳

```text
 altered_table_def (새 dd::Table)
      --> L14732 store 후 L14883 커밋에서 DD 에 확정된다
      --> L14902 ha_notify_table_changed 로 엔진에 새 정의를 알린다
 binlog 의 ALTER 문장
      --> 복제본이 같은 경로를 처음부터 다시 돈다
 MDL X
      --> 문장이 끝날 때 풀리고, 기다리던 DML 이 새 정의로 테이블을 연다
```

## 다루지 않는 것

외래 키 이름 잠금과 검사(`collect_fk_names_for_new_fks`, `check_fk_names_before_rename`), `error_if_not_empty` 의 빈 테이블 검사(L14520-L14566), 원자적 DDL 을 지원하지 않는 엔진의 분기(L14733-L14747, L14765-L14788), 테이블 이름 변경(`mysql_rename_table`), 참조 뷰 갱신, LOCK TABLES 아래의 재열기는 이 흐름의 곁가지라 요약만 했다. COPY 의 행 복사는 다루지 않는다. L14518 의 `lock_tables` 가 InnoDB 에 닿는 자리는 [ha_innobase.external_lock](../../command-dispatch/08_ha_innobase.external_lock/README.md)에 있다.
