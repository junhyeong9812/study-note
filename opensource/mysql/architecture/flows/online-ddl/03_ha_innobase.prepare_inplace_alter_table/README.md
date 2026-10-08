# ha_innobase::prepare_inplace_alter_table

상위: [온라인 DDL](../README.md)

**MDL X 아래에서 "빌드할 자리"를 만드는 단계다.** 새 인덱스(또는 재구성할 새 테이블)를 InnoDB 사전 캐시에 아직 공개되지 않은 상태로 만들고, 온라인이면 거기에 row log 를 붙이고, 빌드 스캔이 쓸 읽기 뷰를 잡는다. 이 일이 X 잠금 안에서 끝나야 하는 이유는 [01] 이 잠금을 SU 로 내리는 순간부터 다른 연결의 DML 이 새 인덱스의 row log 에 기록을 남기기 시작하기 때문이다. INSTANT 이면 할 일이 없어 바로 돌아간다.

## 위치

`storage` / `innobase` / `handler` / `handler0alter.cc` L1442-L1466 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L1442-L1466))

## 실제 코드

공개 함수는 DD 테이블 재구성을 막고 AUTO_INCREMENT 값을 옮긴 뒤 템플릿 구현으로 넘긴다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L1442-L1466 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L1442-L1466))

```cpp
// handler0alter.cc L1442-L1466
bool ha_innobase::prepare_inplace_alter_table(TABLE *altered_table,
                                              Alter_inplace_info *ha_alter_info,
                                              const dd::Table *old_dd_tab,
                                              dd::Table *new_dd_tab) {
  DBUG_TRACE;
  ut_ad(old_dd_tab != nullptr);
  ut_ad(new_dd_tab != nullptr);

  if (dict_sys_t::is_dd_table_id(m_prebuilt->table->id) &&
      innobase_need_rebuild(ha_alter_info)) {
    ut_ad(!m_prebuilt->table->is_temporary());
    my_error(ER_NOT_ALLOWED_COMMAND, MYF(0));
    return true;
  }

  if (altered_table->found_next_number_field != nullptr) {
    dd_copy_autoinc(old_dd_tab->se_private_data(),
                    new_dd_tab->se_private_data());
    dd_set_autoinc(new_dd_tab->se_private_data(),
                   ha_alter_info->create_info->auto_increment_value);
  }

  return prepare_inplace_alter_table_impl<dd::Table>(
      altered_table, ha_alter_info, old_dd_tab, new_dd_tab);
}
```

구현의 앞부분이다. 바뀌는 것이 없거나 INSTANT 이면 여기서 끝난다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L5505-L5521 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L5505-L5521))

```cpp
// handler0alter.cc L5505-L5521
  if (!(ha_alter_info->handler_flags & ~INNOBASE_INPLACE_IGNORE)) {
    /* Nothing to do. Since there is no MDL protected, don't
    try to drop aborted indexes here. */
    assert(m_prebuilt->trx->dict_operation_lock_mode == 0);
    return false;
  }

  if (is_instant(ha_alter_info)) {
    Instant_Type type = innobase_support_instant(ha_alter_info, indexed_table,
                                                 this->table, altered_table);

    if (type == Instant_Type::INSTANT_ADD_DROP_COLUMN) {
      ut_a(is_valid_row_version(indexed_table->current_row_version + 1));
    }

    return false;
  }
```

구현의 끝이다. 여기까지 모은 정보로 `ha_innobase_inplace_ctx` 를 만들고 사전 작업으로 넘어간다. `online` 은 서버가 [01] 에서 정한 `ha_alter_info->online` 이다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L5442-L6065 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L5442-L6065))

`storage` / `innobase` / `handler` / `handler0alter.cc` L6049-L6065 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L6049-L6065))

```cpp
// handler0alter.cc L6049-L6065
  assert(heap);
  assert(m_user_thd == m_prebuilt->trx->mysql_thd);
  assert(!ha_alter_info->handler_ctx);

  ha_alter_info->handler_ctx = new (m_user_thd->mem_root)
      ha_innobase_inplace_ctx(m_prebuilt, drop_index, n_drop_index,
                              rename_index, n_rename_index, drop_fk, n_drop_fk,
                              add_fk, n_add_fk, ha_alter_info->online, heap,
                              m_prebuilt->table, col_names, add_autoinc_col_no,
                              ha_alter_info->create_info->auto_increment_value,
                              autoinc_col_max_value);

  return prepare_inplace_alter_table_dict(
      ha_alter_info, altered_table, table, old_dd_tab, new_dd_tab,
      table_share->table_name.str, info.flags(), info.flags2(), fts_doc_col_no,
      add_fts_doc_id, add_fts_doc_id_idx);
}
```

`prepare_inplace_alter_table_dict` 안에서 row log 를 붙이는 부분이다. 보조 인덱스를 새로 만들 때는 그 인덱스에, 테이블을 재구성할 때는 옛 테이블의 클러스터드 인덱스에 붙인다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L4951-L5013 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L4951-L5013))

```cpp
// handler0alter.cc L4951-L5013
    /* If only online ALTER TABLE operations have been
    requested, allocate a modification log. If the table
    will be locked anyway, the modification
    log is unnecessary. When rebuilding the table
    (new_clustered), we will allocate the log for the
    clustered index of the old table, later. */
    if (new_clustered || !ctx->online || user_table->ibd_file_missing ||
        dict_table_is_discarded(user_table)) {
      /* No need to allocate a modification log. */
      ut_ad(!ctx->add_index[a]->online_log);
    } else if (ctx->add_index[a]->type & DICT_FTS) {
      /* Fulltext indexes are not covered
      by a modification log. */
    } else {
      // ... (L4965-L4967 생략: 디버그 주입)
      rw_lock_x_lock(&ctx->add_index[a]->lock, UT_LOCATION_HERE);
      bool ok = row_log_allocate(ctx->add_index[a], nullptr, true, nullptr,
                                 nullptr, path);
      rw_lock_x_unlock(&ctx->add_index[a]->lock);

      if (!ok) {
        error = DB_OUT_OF_MEMORY;
        goto error_handling;
      }
    }
  }

  ut_ad(new_clustered == ctx->need_rebuild());

  // ... (L4982-L4984 생략: 디버그 주입)
  if (new_clustered) {
    dict_index_t *clust_index = user_table->first_index();
    dict_index_t *new_clust_index = ctx->new_table->first_index();
    ctx->skip_pk_sort = innobase_pk_order_preserved(
        ctx->col_map, clust_index, new_clust_index, ctx->add_autoinc);

    // ... (L4991-L4993 생략: 디버그 단정)
    if (ctx->online) {
      /* Allocate a log for online table rebuild. */
      rw_lock_x_lock(&clust_index->lock, UT_LOCATION_HERE);
      bool ok = row_log_allocate(
          clust_index, ctx->new_table,
          !(ha_alter_info->handler_flags & Alter_inplace_info::ADD_PK_INDEX),
          ctx->add_cols, ctx->col_map, path);
      rw_lock_x_unlock(&clust_index->lock);

      if (!ok) {
        error = DB_OUT_OF_MEMORY;
        goto error_handling;
      }
    }
  }

  if (ctx->online) {
    /* Assign a consistent read view for the index build scan. */
    trx_assign_read_view(ctx->prebuilt->trx);
  }
```

## 동작 흐름

```text
 L1450  DD 테이블(mysql.*)을 재구성하려 하면 ER_NOT_ALLOWED_COMMAND
 L1457  AUTO_INCREMENT 열이 있으면 옛 DD 의 autoinc 를 새 DD 로 복사
 L1464  prepare_inplace_alter_table_impl<dd::Table>

 _impl
 L5486  클러스터드 인덱스가 깨져 있으면 오류
 L5492  DISCARD 된 테이블이면 재구성이나 INSTANT 열 변경 거부
 L5505  바뀌는 것 없음                    --> false (MDL 보호가 없으니 정리도 하지 않는다)
 L5512  INSTANT                           --> false. row version 이 남았는지만 단정 (L5517)
 L5523-L6047  테이블스페이스, 행 형식, 인덱스 정의, 삭제할 인덱스와 FK, AUTO_INCREMENT 열을 검사하고 모은다
 L6053  ctx = new ha_innobase_inplace_ctx(..., online, ...)
 L6061  prepare_inplace_alter_table_dict
          L4588  재구성이면 새 dict_table_t 를 임시 이름으로 만든다
          L4942  새 인덱스는 add_index[] 에 있고, 재구성이 아니면 아직 커밋되지 않은 상태다
          L4957  row log 가 필요 없는 경우: 재구성, 온라인 아님, ibd 없음, DISCARD
          L4961  FULLTEXT 는 row log 를 쓰지 않는다
          L4969  보조 인덱스마다 row_log_allocate(index, nullptr, ...)
                   row_log_allocate 가 online_status 를 ONLINE_INDEX_CREATION 으로 둔다 (row0log.cc L3149)
          L4997  재구성이면 옛 클러스터드 인덱스에 row_log_allocate(clust, new_table, same_pk, ...)
          L5012  온라인이면 trx_assign_read_view  빌드 스캔이 볼 시점을 여기서 고정
```

row log 는 두 종류이고, 어느 쪽인지는 무엇을 바꾸느냐로 정해진다. 이 흐름의 [07] [08] 은 왼쪽(보조 인덱스 추가)이다.

```text
 row log 가 붙는 자리 (row_log_t 는 row0log.cc L185)

 ADD INDEX (재구성 없음)                    재구성 (ADD PRIMARY KEY, 열 순서 변경, ROW_FORMAT 등)
 ---------------------------------------    ---------------------------------------------
 새 보조 인덱스 하나에 하나                 옛 테이블의 클러스터드 인덱스에 하나
 log->table = nullptr                       log->table = 새 테이블
 기록: row_log_online_op [07]               기록: row_log_table_insert / update / delete
 적용: row_log_apply [08]                   적용: row_log_table_apply
       인덱스 빌드가 끝나면 바로                  [04] 빌드 뒤 한 번 (SU 아래)
                                                  [09] commit_try_rebuild 에서 한 번 더 (X 아래)
```

```text
 이 단계가 X 아래에서 끝나야 하는 것

 시점               ALTER 연결                              다른 연결
 prepare (X)        add_index[] 생성, online_status 는     테이블을 못 연다
                    ONLINE_INDEX_CREATION
                    row_log_allocate
                    trx_assign_read_view    <-- 스캔 시점 T0
 다운그레이드 (SU)                                          INSERT 가 새 인덱스를 보고
                                                            online_status 가 CREATION 이므로
                                                            트리 대신 row log 에 쓴다 [07]

 T0 이전에 커밋된 행    --> [06] 의 스캔이 본다
 T0 이후의 변경         --> row log 에 있다 --> [08] 이 적용한다
 스캔이 이미 본 변경이 row log 에도 있을 수 있다. [08] 은 적용 전에 레코드를 먼저 찾아
 이미 반영된 INSERT 는 건너뛴다 (row0log.cc L3221-L3225 주석, L3293)
```

## 결과가 쓰이는 곳

```text
 ha_alter_info->handler_ctx (ha_innobase_inplace_ctx)
      --> [04] 가 add_index, new_table, col_map, online 을 꺼내 ddl::Context 를 만든다
      --> [09] 가 need_rebuild 와 add_index 로 커밋할 대상을 안다
 index->online_log
      --> [07] 이 다른 연결에서 여기에 쓴다
 읽기 뷰
      --> [06] 의 클러스터드 인덱스 스캔이 이 시점의 스냅숏을 읽는다
```

## 다루지 않는 것

`prepare_inplace_alter_table_impl` 의 검사 목록(L5523-L6047: 테이블스페이스 이동, 행 형식, 인덱스 이름 중복, 외래 키, 가상 열, FTS_DOC_ID), `prepare_inplace_alter_table_dict` 의 새 테이블 생성과 DDL 로그 기록, 재구성 row log 의 레코드 형식(`row_log_table_*`), 파티션 테이블의 `ha_innopart::prepare_inplace_alter_table` 은 이 흐름의 곁가지라 요약만 했다.
