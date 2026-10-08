# ha_innobase::inplace_alter_table

상위: [온라인 DDL](../README.md)

**MDL 이 SU 로 내려가 있는 동안 도는 무거운 단계의 입구다.** 실제 일은 `ddl::Context` 에 넘기고, 이 함수는 그 전후를 정리한다. 앞에서는 할 일이 없는 경우(INSTANT, 데이터를 건드리지 않는 변경)를 걸러 내고 스캔의 격리 수준을 REPEATABLE READ 로 맞춘다. 뒤에서는 재구성이라면 쌓인 row log 를 한 번 적용하고, 오류를 MySQL 오류로 바꾼다.

## 위치

`storage` / `innobase` / `handler` / `handler0alter.cc` L1566-L1581 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L1566-L1581))

## 실제 코드

공개 함수는 백업(clone)에 "지금 inplace DDL 중" 이라고 알리고 구현으로 넘긴다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L1566-L1581 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L1566-L1581))

```cpp
// handler0alter.cc L1566-L1581
bool ha_innobase::inplace_alter_table(TABLE *altered_table,
                                      Alter_inplace_info *ha_alter_info,
                                      const dd::Table *old_dd_tab
                                      [[maybe_unused]],
                                      dd::Table *new_dd_tab [[maybe_unused]]) {
  DBUG_TRACE;
  ut_ad(old_dd_tab != nullptr);
  ut_ad(new_dd_tab != nullptr);

  /* Notify clone during in place operations */
  Clone_notify notifier(Clone_notify::Type::SPACE_ALTER_INPLACE,
                        dict_sys_t::s_invalid_space_id, false);
  ut_ad(!notifier.failed());

  return inplace_alter_table_impl<dd::Table>(altered_table, ha_alter_info);
}
```

구현이다. 할 일이 없으면 바로 돌아간다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L6138-L6380 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L6138-L6380))

`storage` / `innobase` / `handler` / `handler0alter.cc` L6138-L6198 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L6138-L6198))

```cpp
// handler0alter.cc L6138-L6198
bool ha_innobase::inplace_alter_table_impl(TABLE *altered_table,
                                           Alter_inplace_info *ha_alter_info) {
  dict_add_v_col_t *add_v = nullptr;
  dict_vcol_templ_t *s_templ = nullptr;
  dict_vcol_templ_t *old_templ = nullptr;
  struct TABLE *eval_table = altered_table;
  bool rebuild_templ = false;
  DBUG_TRACE;
  assert(!srv_read_only_mode);

  // ... (L6148-L6166 생략: 래치 단정과 반환용 람다)

  if (!(ha_alter_info->handler_flags & INNOBASE_ALTER_DATA) ||
      is_instant(ha_alter_info)) {
    return all_ok();
  }

  if (((ha_alter_info->handler_flags & ~INNOBASE_INPLACE_IGNORE) ==
           Alter_inplace_info::CHANGE_CREATE_OPTION &&
       !innobase_need_rebuild(ha_alter_info))) {
    return all_ok();
  }

  ha_innobase_inplace_ctx *ctx =
      static_cast<ha_innobase_inplace_ctx *>(ha_alter_info->handler_ctx);

  assert(ctx);
  assert(ctx->trx);
  assert(ctx->prebuilt == m_prebuilt);

  dict_index_t *pk = m_prebuilt->table->first_index();
  ut_ad(pk != nullptr);

  /* For partitioned tables this could be already allocated from a
  previous partition invocation. For normal tables this is NULL. */
  ut::delete_(ctx->m_stage);

  ctx->m_stage = ut::new_withkey<Alter_stage>(UT_NEW_THIS_FILE_PSI_KEY, pk);

  if (m_prebuilt->table->ibd_file_missing ||
      dict_table_is_discarded(m_prebuilt->table)) {
    return success();
  }
```

빌드가 끝난 뒤의 정리를 람다로 먼저 정의한다. 재구성이면 여기서 row log 를 적용한다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L6257-L6336 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L6257-L6336))

```cpp
// handler0alter.cc L6257-L6336
  auto clean_up = [&](dberr_t err) -> bool {
    DEBUG_SYNC_C("alter_table_update_log");

    if (err == DB_SUCCESS && ctx->online && ctx->need_rebuild()) {
      DEBUG_SYNC_C("row_log_table_apply1_before");
      err = row_log_table_apply(ctx->thr, m_prebuilt->table, altered_table,
                                ctx->m_stage);
    }

    // ... (L6266-L6282 생략: 가상 열 템플릿 해제와 디버그 주입)
    switch (err) {
      case DB_SUCCESS:
        return success();
      case DB_DUPLICATE_KEY: {
        // ... (L6287-L6312 생략: 중복 키 오류에 쓸 KEY 고르기)
      }
      case DB_ONLINE_LOG_TOO_BIG:
        assert(ctx->online);
        my_error(ER_INNODB_ONLINE_LOG_TOO_BIG, MYF(0),
                 get_error_key_name(m_prebuilt->trx->error_key_num,
                                    ha_alter_info, m_prebuilt->table));
        break;
      case DB_INDEX_CORRUPT:
        my_error(ER_INDEX_CORRUPT, MYF(0),
                 get_error_key_name(m_prebuilt->trx->error_key_num,
                                    ha_alter_info, m_prebuilt->table));
        break;
      default:
        my_error_innodb(err, table_share->table_name.str,
                        m_prebuilt->table->flags);
    }

    /* prebuilt->table->n_ref_count can be anything here, given
    that we hold at most a shared lock on the table. */
    m_prebuilt->trx->error_index = nullptr;
    ctx->trx->error_state = DB_SUCCESS;

    return true;
  };
```

격리 수준을 맞추고 `ddl::Context` 를 만들어 빌드한다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L6338-L6380 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L6338-L6380))

```cpp
// handler0alter.cc L6338-L6380
  /* Read the clustered index of the table and build
  indexes based on this information using temporary
  files and merge sort. */
  DBUG_EXECUTE_IF("innodb_OOM_inplace_alter",
                  return clean_up(DB_OUT_OF_MEMORY););

  const auto trx = m_prebuilt->trx;
  const auto old_isolation_level = trx->isolation_level;

  if (ctx->online &&
      trx->isolation_level != trx_t::isolation_level_t::REPEATABLE_READ) {
    /* We must scan the index at an isolation level >= READ COMMITTED, because
    a dirty read will see half written blob references.

    ** Perform a REPEATABLE READ.
    When rebuilding the table online, row_log_table_apply() must not see
    a newer state of the table when applying the log. This is mainly to
    prevent false duplicate key errors, because the log will identify records
    by the PRIMARY KEY, and also to prevent unsafe BLOB access.

    When creating a secondary index online, this table scan must not see
    records that have only been inserted to the clustered index, but have
    not been written to the online_log of index[]. If we performed
    READ UNCOMMITTED, it could happen that the ADD INDEX reaches
    ONLINE_INDEX_COMPLETE state between the time the DML thread has updated
    the clustered index but has not yet accessed secondary index. */

    trx->isolation_level = trx_t::isolation_level_t::REPEATABLE_READ;
  }

  ddl::Context ddl(trx, m_prebuilt->table, ctx->new_table, ctx->online,
                   ctx->add_index, ctx->add_key_numbers, ctx->num_to_add_index,
                   altered_table, ctx->add_cols, ctx->col_map, ctx->add_autoinc,
                   ctx->sequence, ctx->skip_pk_sort, ctx->m_stage, add_v,
                   eval_table, thd_ddl_buffer_size(m_prebuilt->trx->mysql_thd),
                   thd_ddl_threads(m_prebuilt->trx->mysql_thd));

  const auto err = clean_up(ddl.build());

  trx->isolation_level = old_isolation_level;

  return err;
}
```

## 동작 흐름

```text
 L1576  Clone_notify(SPACE_ALTER_INPLACE)     진행 중인 clone 과 조율한다
 L1580  inplace_alter_table_impl<dd::Table>

 _impl
 L6168  INNOBASE_ALTER_DATA 비트가 없거나 INSTANT     --> 할 일 없음
 L6173  CHANGE_CREATE_OPTION 뿐이고 재구성 아님        --> 할 일 없음
 L6193  Alter_stage 생성 (performance_schema 진행률)
 L6195  ibd 가 없거나 DISCARD                          --> 성공으로 끝
 L6208-L6255  가상 열 계산 템플릿 준비

 L6347  online 이고 격리 수준이 REPEATABLE READ 가 아니면 RR 로 바꾼다
 L6368  ddl::Context ddl(trx, old_table, new_table, online, add_index, ...,
                         ddl_buffer_size, ddl_threads)
 L6375  clean_up(ddl.build())                         --> [05]
          L6260  재구성 + 온라인이면 row_log_table_apply  (아직 SU, DML 은 계속 들어온다)
          L6283  오류를 MySQL 오류로: 중복 키, ONLINE_LOG_TOO_BIG, INDEX_CORRUPT
 L6377  격리 수준을 되돌린다
```

격리 수준을 올리는 이유가 소스 주석에 적혀 있다. 아래 그림은 READ UNCOMMITTED 로 스캔했을 때 생기는 틈이다.

```text
 왜 RR 로 스캔하는가 (주석 L6349-L6363)

 DML 연결 B                                   빌드 스캔 (ALTER 연결 A)
 클러스터드 인덱스에 행 r 삽입 (미커밋)
                                              RU 라면 r 을 읽어 새 인덱스 정렬 파일에 넣는다
 보조 인덱스로 가기 전
                                              빌드 완료 -> [08] 적용 -> ONLINE_INDEX_COMPLETE
 보조 인덱스 차례: 상태가 COMPLETE 라
 트리에 직접 넣는다
                                              r 의 키가 두 경로로 들어온다

 RR 이면 스캔은 [03] 에서 잡은 읽기 뷰로 커밋된 것만 본다
 B 의 변경은 전부 row log 쪽으로만 들어온다
 재구성에서는 row log 가 PK 로 행을 찾으므로, 스캔이 더 새 상태를 보면 거짓 중복 키가 난다
```

```text
 ddl::Context 로 넘어가는 것 (L6368-L6373)

 인자                      출처                                쓰임
 trx                       m_prebuilt->trx                     스캔의 읽기 뷰, 중단 검사
 old_table, new_table      m_prebuilt->table, ctx->new_table   같으면 ADD INDEX, 다르면 재구성
 online                    ctx->online                          row log 적용 여부 [06]
 add_index, add_key_numbers ctx                                 만들 인덱스 목록
 col_map, add_cols         ctx                                  재구성 때 옛 열 -> 새 열
 skip_pk_sort              ctx                                  PK 순서가 그대로면 정렬 생략
 ddl_buffer_size           innodb_ddl_buffer_size               정렬 버퍼
 ddl_threads               innodb_ddl_threads                   [06] 의 작업 스레드 수
```

## 결과가 쓰이는 곳

```text
 반환값 false
      --> [01] 이 MDL 을 X 로 올리고 [09] 로 간다
 반환값 true (오류)
      --> [01] 의 rollback: 이 [09] 를 commit=false 로 불러 만든 인덱스를 치운다
 새 인덱스 (ONLINE_INDEX_COMPLETE)
      --> 이때부터 다른 연결의 DML 은 row log 를 거치지 않고 트리에 바로 쓴다
```

## 다루지 않는 것

가상 열 계산 템플릿(`innobase_build_v_templ`)과 가상 열 인덱스, 재구성 row log 의 적용(`row_log_table_apply`)의 세부, `Alter_stage` 의 진행률 계산, clone 과의 조율(`Clone_notify`)은 이 흐름의 곁가지라 요약만 했다.
