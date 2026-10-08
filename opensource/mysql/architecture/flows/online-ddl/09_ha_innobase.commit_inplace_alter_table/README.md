# ha_innobase::commit_inplace_alter_table

상위: [온라인 DDL](../README.md)

**MDL X 아래에서 새 정의로 갈아 끼우는 단계이자, INSTANT 가 실제로 일을 하는 자리다.** 서버는 이 함수를 두 번 부를 수 있다. 성공 경로에서는 `commit=true` 로, 실패하면 `commit=false` 로 만든 것을 되돌린다. `commit=true` 일 때 INSTANT 는 `Instant_ddl_impl::commit_instant_ddl` 로 DD 의 메타데이터만 바꾸고 끝난다. INPLACE 는 InnoDB 테이블 잠금과 사전 래치를 잡은 뒤, 재구성이라면 마지막 row log 를 적용하고 테이블을 바꿔 끼우며, ADD INDEX 라면 새 인덱스를 사전에 공개한다. 여기서 바뀐 DD 객체는 [01] 이 문장 커밋으로 확정한다.

## 위치

`storage` / `innobase` / `handler` / `handler0alter.cc` L1602-L1672 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L1602-L1672))

## 실제 코드

공개 함수다. 구현이 사전 캐시를 고친 뒤, 종류에 따라 DD 객체(`new_dd_tab`)를 고친다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L1602-L1672 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L1602-L1672))

```cpp
// handler0alter.cc L1602-L1672
bool ha_innobase::commit_inplace_alter_table(TABLE *altered_table,
                                             Alter_inplace_info *ha_alter_info,
                                             bool commit,
                                             const dd::Table *old_dd_tab,
                                             dd::Table *new_dd_tab) {
  DBUG_TRACE;
  ut_ad(old_dd_tab != nullptr);
  ut_ad(new_dd_tab != nullptr);

  ha_innobase_inplace_ctx *ctx =
      static_cast<ha_innobase_inplace_ctx *>(ha_alter_info->handler_ctx);

  alter_table_old_info_t old_info;
  ut_d(bool old_info_updated = false);
  if (commit && ctx != nullptr) {
    ut_ad(!!(ha_alter_info->handler_flags & ~INNOBASE_INPLACE_IGNORE));
    old_info.update(ctx->old_table, ctx->need_rebuild());
    ut_d(old_info_updated = true);
  }

  bool res = commit_inplace_alter_table_impl<dd::Table>(
      altered_table, ha_alter_info, commit, new_dd_tab);

  if (res || !commit) {
    return true;
  }

  ut_ad(ctx == nullptr || !(ctx->need_rebuild() && is_instant(ha_alter_info)));

  if (is_instant(ha_alter_info)) {
    ut_ad(!res);

    Instant_ddl_impl<dd::Table> executor(
        ha_alter_info, m_user_thd, m_prebuilt->trx, m_prebuilt->table, table,
        altered_table, old_dd_tab, new_dd_tab,
        altered_table->found_next_number_field != nullptr
            ? &m_prebuilt->table->autoinc
            : nullptr);

    /* Execute Instant DDL */
    if (executor.commit_instant_ddl()) return true;
  } else if (!(ha_alter_info->handler_flags & ~INNOBASE_INPLACE_IGNORE) ||
             ctx == nullptr) {
    ut_ad(!res);
    dd_commit_inplace_no_change(ha_alter_info, old_dd_tab, new_dd_tab, false);
  } else {
    ut_ad(old_info_updated);
    if (!ctx->need_rebuild() && !dict_table_has_fts_index(m_prebuilt->table)) {
      /* Table is not rebuilt so copy instant metadata. */
      dd_inplace_alter_copy_instant_metadata(ha_alter_info, old_dd_tab,
                                             new_dd_tab);
    }

    dd_commit_inplace_alter_table<dd::Table>(old_info, ctx->new_table,
                                             old_dd_tab, new_dd_tab);
    if (!ctx->need_rebuild()) {
      dd_commit_inplace_update_instant_meta(ctx->new_table, old_dd_tab,
                                            new_dd_tab);
    }
    ut_ad(dd_table_match(ctx->new_table, new_dd_tab));
  }

// ... (L1664-L1669 생략: 디버그 단정)

  return res;
}
```

구현의 앞부분이다. 되돌리기와 할 일 없는 경우를 먼저 처리하고, 테이블에 InnoDB X 잠금을 건다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L7429-L7998 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L7429-L7998))

`storage` / `innobase` / `handler` / `handler0alter.cc` L7457-L7513 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L7457-L7513))

```cpp
// handler0alter.cc L7457-L7513
  if (!commit) {
    /* A rollback is being requested. So far we may at
    most have created some indexes. If any indexes were to
    be dropped, they would actually be dropped in this
    method if commit=true. */
    const bool ret =
        rollback_inplace_alter_table(ha_alter_info, table, m_prebuilt);
    return ret;
  }

  if (!(ha_alter_info->handler_flags & ~INNOBASE_INPLACE_IGNORE) ||
      is_instant(ha_alter_info)) {
    assert(!ctx0);
    MONITOR_ATOMIC_DEC(MONITOR_PENDING_ALTER_TABLE);
    ha_alter_info->group_commit_ctx = nullptr;
    return false;
  }

  assert(ctx0);

  inplace_alter_handler_ctx **ctx_array;
  inplace_alter_handler_ctx *ctx_single[2];

  if (ha_alter_info->group_commit_ctx) {
    ctx_array = ha_alter_info->group_commit_ctx;
  } else {
    ctx_single[0] = ctx0;
    ctx_single[1] = nullptr;
    ctx_array = ctx_single;
  }

  assert(ctx0 == ctx_array[0]);
  ut_ad(m_prebuilt->table == ctx0->old_table);
  ha_alter_info->group_commit_ctx = nullptr;

  trx_start_if_not_started_xa(m_prebuilt->trx, true, UT_LOCATION_HERE);

  for (inplace_alter_handler_ctx **pctx = ctx_array; *pctx; pctx++) {
    ha_innobase_inplace_ctx *ctx =
        static_cast<ha_innobase_inplace_ctx *>(*pctx);
    assert(ctx->prebuilt->trx == m_prebuilt->trx);

    /* Exclusively lock the table, to ensure that no other
    transaction is holding locks on the table while we
    change the table definition. The MySQL meta-data lock
    should normally guarantee that no conflicting locks
    exist. However, FOREIGN KEY constraints checks and any
    transactions collected during crash recovery could be
    holding InnoDB locks only, not MySQL locks. */

    error = ddl::lock_table(m_prebuilt->trx, ctx->old_table, LOCK_X);

    if (error != DB_SUCCESS) {
      my_error_innodb(error, table_share->table_name.str, 0);
      return true;
    }
  }
```

사전 래치를 잡고, 재구성과 비재구성으로 갈라 사전 테이블을 고친다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L7569-L7624 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L7569-L7624))

```cpp
// handler0alter.cc L7569-L7624
  /* Latch the InnoDB data dictionary exclusively so that no deadlocks
  or lock waits can happen in it during the data dictionary operation. */
  row_mysql_lock_data_dictionary(trx, UT_LOCATION_HERE);
  // ... (L7572-L7599 생략: 통계 백그라운드 중지 대기)
  /* Apply the changes to the data dictionary tables, for all partitions.*/

  for (inplace_alter_handler_ctx **pctx = ctx_array; *pctx && !fail; pctx++) {
    ha_innobase_inplace_ctx *ctx =
        static_cast<ha_innobase_inplace_ctx *>(*pctx);

    assert(new_clustered == ctx->need_rebuild());

    // ... (L7608-L7613 생략: AUTO_INCREMENT 확인)
    if (ctx->need_rebuild()) {
      fail = commit_try_rebuild(ha_alter_info, ctx, altered_table, table, trx,
                                table_share->table_name.str);

      if (!fail) {
        log_ddl->write_drop_log(trx, ctx->old_table->id);
      }
    } else {
      fail = commit_try_norebuild(ha_alter_info, ctx, trx,
                                  table_share->table_name.str);
    }
```

재구성이면 `commit_try_rebuild` 에서 마지막 row log 를 적용한다. [04] 에서 SU 아래 한 번 적용한 뒤 그 사이 쌓인 몫이다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L6969-L6990 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L6969-L6990))

```cpp
// handler0alter.cc L6969-L6990
  /* We copied the table. Any indexes that were requested to be
  dropped were not created in the copy of the table. Apply any
  last bit of the rebuild log and then rename the tables. */

  if (ctx->online) {
    DEBUG_SYNC_C("row_log_table_apply2_before");

    dict_vcol_templ_t *s_templ = nullptr;

    if (ctx->new_table->n_v_cols > 0) {
      s_templ = ut::new_withkey<dict_vcol_templ_t>(UT_NEW_THIS_FILE_PSI_KEY);
      s_templ->vtempl = nullptr;

      innobase_build_v_templ(altered_table, ctx->new_table, s_templ, nullptr,
                             true, nullptr);
      ctx->new_table->vc_templ = s_templ;
    }

    error = row_log_table_apply(
        ctx->thr, user_table, altered_table,
        static_cast<ha_innobase_inplace_ctx *>(ha_alter_info->handler_ctx)
            ->m_stage);
```

INSTANT 의 커밋이다. 열을 더하거나 빼는 경우 테이블의 row version 을 하나 올린다.

`storage` / `innobase` / `dict` / `dict0inst.cc` L198-L285 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/dict/dict0inst.cc#L198-L285))

```cpp
// dict0inst.cc L198-L285
bool Instant_ddl_impl<Table>::commit_instant_ddl() {
  Instant_Type type =
      static_cast<Instant_Type>(m_ha_alter_info->handler_trivial_ctx);

  switch (type) {
    // ... (L203-L237 생략: NO_CHANGE, COLUMN_RENAME, VIRTUAL_ONLY 는 DD 정리와 캐시 비우기)
    case Instant_Type::INSTANT_ADD_DROP_COLUMN:
      trx_start_if_not_started(m_trx, true, UT_LOCATION_HERE);
      dd_copy_private(*m_new_dd_tab, *m_old_dd_tab);

      /* Fetch the columns which are to be added or dropped */
      populate_to_be_instant_columns();

      ut_ad(!m_cols_to_add.empty() || !m_cols_to_drop.empty());

      if (!m_cols_to_drop.empty()) {
        /* INSTANT DROP */
        if (commit_instant_drop_col()) return true;
      }

      if (!m_cols_to_add.empty()) {
        /* INSTANT ADD */
        if (commit_instant_add_col()) return true;
      }

      /* Update the current row version in dictionary cache */
      m_dict_table->current_row_version++;

      ut_ad(dd_table_has_instant_cols(m_new_dd_tab->table()));

      for (auto dd_index : *m_new_dd_tab->indexes()) {
        dd::Properties &p = dd_index->se_private_data();
        p.set(dd_index_key_strings[DD_INDEX_TRX_ID], m_trx->id);
      }

      row_mysql_lock_data_dictionary(m_trx, UT_LOCATION_HERE);
      innobase_discard_table(m_thd, m_dict_table);
      row_mysql_unlock_data_dictionary(m_trx);

      break;
    case Instant_Type::INSTANT_IMPOSSIBLE:
    default:
      ut_ad(0);
  }

  // ... (L277-L283 생략: AUTO_INCREMENT 값 기록)
  return false;
}
```

## 동작 흐름

```text
 commit_inplace_alter_table (L1602)
 L1616  commit 이고 ctx 가 있으면 옛 테이블 정보 저장
 L1622  commit_inplace_alter_table_impl
          L7457  commit=false -> rollback_inplace_alter_table  (만든 인덱스와 새 테이블을 치운다)
          L7467  바뀌는 것 없음 또는 INSTANT -> 그냥 false
          L7507  ddl::lock_table(old_table, LOCK_X)   InnoDB 테이블 X 잠금
                   MDL 이 막지 못하는 잠금(FK 검사, 복구된 트랜잭션)과 충돌하지 않게 (주석 L7499-L7505)
          L7552  재구성이면 옛 테이블용 임시 이름에도 MDL X
          L7571  row_mysql_lock_data_dictionary         사전 래치 X
          L7614  재구성     commit_try_rebuild
                              L6943  새 인덱스가 모두 COMPLETE 이고 깨지지 않았는지
                              L6973  온라인이면 row_log_table_apply (마지막 몫, 이제 DML 없음)
                 비재구성   commit_try_norebuild (L7142)  새 인덱스 검사와 사전 테이블 변경
          L7619  재구성 성공이면 DDL 로그에 옛 테이블 drop 기록
          L7690  재구성 row log 해제
          L7734  재구성이면 commit_cache_rebuild    테이블스페이스 파일 이름을 바꿔
                 새 테이블이 원래 이름을, 옛 테이블이 tmp_name 을 갖는다 (L7885 단정)
          L7763  비재구성이면 commit_cache_norebuild  새 인덱스 set_committed(true) (L7223),
                 지울 인덱스를 캐시에서 뺀다
          L7924  재구성이면 옛 테이블 drop
          L7938  사전 래치 해제
 L1631  INSTANT     Instant_ddl_impl::commit_instant_ddl
 L1643  변경 없음   dd_commit_inplace_no_change
 L1647  INPLACE     dd_commit_inplace_alter_table (새 dd::Table 에 InnoDB 사적 데이터 기록)
```

INSTANT ADD COLUMN 이 데이터를 안 건드리고도 옛 행을 읽을 수 있는 것은 행마다 어느 버전의 정의로 쓰였는지 남기기 때문이다. 아래는 그 버전이 움직이는 자리다.

```text
 INSTANT ADD/DROP COLUMN 과 row version

 [02] L1073  current_row_version + 1 이 MAX_ROW_VERSION(255) 를 넘으면 INSTANT 불가 -> INPLACE
 [03] L5517  INSTANT 면 같은 조건을 단정만 하고 돌아간다
 [04]        INSTANT 면 L6168 에서 바로 돌아간다
 [09] dict0inst.cc
        L249  INSTANT DROP  commit_instant_drop_col
        L254  INSTANT ADD   commit_instant_add_col
        L258  m_dict_table->current_row_version++
        L264  모든 인덱스의 DD_INDEX_TRX_ID 를 이 트랜잭션 id 로

 옛 행은 디스크에서 그대로이고, 바뀌는 것은 사전의 버전 번호와 DD 메타데이터뿐이다
 행에 버전이 어떻게 기록되고 읽히는지는 레코드 형식 쪽 이야기라 여기서 다루지 않는다
```

```text
 이 단계의 잠금 세 겹

 층          무엇                              누가 잡나
 서버 MDL    테이블 X                          [01] L14638 wait_while_table_is_used
 InnoDB      테이블 잠금 LOCK_X                L7507 ddl::lock_table
 InnoDB      사전 래치 dict_operation_lock X   L7571 row_mysql_lock_data_dictionary

 MDL 이 X 여도 InnoDB 테이블 잠금을 따로 거는 이유는 주석 L7499-L7505:
   FOREIGN KEY 검사와 크래시 복구로 되살아난 트랜잭션은 MDL 없이 InnoDB 잠금만 쥘 수 있다
```

## 결과가 쓰이는 곳

```text
 new_dd_tab (고쳐진 dd::Table)
      --> [01] 이 DD 에 store 하고 문장 커밋으로 확정한다 (sql_table.cc L14732, L14883)
 InnoDB 사전 캐시
      --> 새 인덱스가 공개되어 옵티마이저와 DML 이 쓴다
      --> 재구성이면 새 dict_table_t 가 원래 이름을 갖는다
 DDL 로그 (log_ddl)
      --> L7619 write_drop_log 로 적은 뒷정리를 커밋 뒤 post_ddl 이 처리한다 (sql_table.cc L14886)
```

## 다루지 않는 것

`rollback_inplace_alter_table`(L6437)의 되돌리기 세부, `commit_try_norebuild` 와 `commit_cache_norebuild` 의 인덱스 공개 절차, 외래 키 캐시 갱신(`innobase_update_foreign_try`), 통계 갱신(`alter_stats_rebuild`), 파티션 테이블의 `group_commit_ctx`, `commit_instant_add_col` / `commit_instant_drop_col` 이 DD 열에 남기는 기본값과 버전 정보는 이 흐름의 곁가지라 요약만 했다.
