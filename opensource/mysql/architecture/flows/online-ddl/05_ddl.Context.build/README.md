# ddl::Context::build

상위: [온라인 DDL](../README.md)

**인덱스 빌드 한 번을 감싸는 껍데기다.** `Loader` 를 만들어 [06] `build_all` 을 돌리고, 결과를 `cleanup` 으로 넘긴다. 볼거리는 `cleanup` 쪽이다. 빌드가 실패하면 온라인으로 만들던 보조 인덱스를 전부 "중단됨" 으로 표시해 다른 연결이 더는 row log 에 쓰지 않게 하고, 성공이든 실패든 redo 없이 쓴 페이지를 디스크로 밀어낸다. 9.x 에서 인덱스 빌드는 `row0merge.cc` 가 아니라 이 `storage/innobase/ddl/` 디렉터리에 있다.

## 위치

`storage` / `innobase` / `ddl` / `ddl0ctx.cc` L516-L526 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0ctx.cc#L516-L526))

## 실제 코드

`storage` / `innobase` / `ddl` / `ddl0ctx.cc` L516-L526 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0ctx.cc#L516-L526))

```cpp
// ddl0ctx.cc L516-L526
dberr_t Context::build() noexcept {
  Loader loader{*this};

  const auto err = cleanup(loader.build_all());

  /* Validate the indexes  after the pages have been flushed to disk.
  Otherwise we can deadlock between flushing and is_free page check. */
  ut_ad(err != DB_SUCCESS || loader.validate_indexes());

  return err;
}
```

`cleanup` 이다. 앞쪽은 실패한 온라인 인덱스의 정리, 뒤쪽은 flush observer 로 빌드한 페이지를 내보내는 부분이다.

`storage` / `innobase` / `ddl` / `ddl0ctx.cc` L305-L390 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0ctx.cc#L305-L390))

```cpp
// ddl0ctx.cc L305-L390
dberr_t Context::cleanup(dberr_t err) noexcept {
  ut_a(err == m_err);

  if (m_err != DB_SUCCESS &&
      m_err_key_number != std::numeric_limits<size_t>::max()) {
    m_trx->error_key_num = m_err_key_number;
  }

  if (m_online && m_old_table == m_new_table && err != DB_SUCCESS) {
    /* On error, flag all online secondary index creation as aborted. */
    for (auto index : m_indexes) {
      ut_a(!index->is_committed());
      ut_a(!index->is_clustered());
      ut_a(!(index->type & DICT_FTS));

      /* Completed indexes should be dropped as well, and indexes whose
      creation was aborted should be dropped from the persistent storage.
      However, at this point we can only set some flags in the
      not-yet-published indexes. These indexes will be dropped later in
      drop_indexes(), called by rollback_inplace_alter_table(). */

      auto latch = dict_index_get_lock(index);

      switch (dict_index_get_online_status(index)) {
        case ONLINE_INDEX_COMPLETE:
          break;
        case ONLINE_INDEX_CREATION:
          rw_lock_x_lock(latch, UT_LOCATION_HERE);
          row_log_abort_sec(index);
          index->type |= DICT_CORRUPT;
          rw_lock_x_unlock(latch);
          m_new_table->drop_aborted = true;
          [[fallthrough]];
        case ONLINE_INDEX_ABORTED:
        case ONLINE_INDEX_ABORTED_DROPPED:
          break;
      }
    }
  }

  DBUG_EXECUTE_IF("ib_index_crash_after_bulk_load", DBUG_SUICIDE(););

  auto observer = m_trx->flush_observer;

  if (observer != nullptr) {
    ut_a(m_need_observer);

    DBUG_EXECUTE_IF("ib_index_build_fail_before_flush", err = DB_FAIL;);

    if (err != DB_SUCCESS) {
      observer->interrupted();
    }

    observer->flush();

    ut::delete_(observer);

    m_trx->flush_observer = nullptr;

    auto space_id = m_new_table != nullptr ? m_new_table->space
                                           : dict_sys_t::s_invalid_space_id;

    /* Notify clone after flushing all pages. */
    Clone_notify notifier(Clone_notify::Type::SPACE_ALTER_INPLACE_BULK,
                          space_id, false);

    if (notifier.failed()) {
      err = DB_ERROR;

    } else if (is_interrupted()) {
      err = DB_INTERRUPTED;
    }

    if (err == DB_SUCCESS) {
      auto first_index = m_new_table->first_index();

      for (auto index = first_index; index != nullptr; index = index->next()) {
        if (m_old_table != m_new_table) {
          Builder::write_redo(index);
        }
      }
    }
  }

  return err;
}
```

빌드 중에 재구성 row log 가 이미 오류를 냈는지 보는 함수다. 다른 연결의 DML 이 row log 에 쓰다가 실패하면 그 오류는 log 에 남고, 빌드 쪽이 여기서 꺼내 본다.

`storage` / `innobase` / `ddl` / `ddl0ctx.cc` L466-L497 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0ctx.cc#L466-L497))

```cpp
// ddl0ctx.cc L466-L497
dberr_t Context::check_state_of_online_build_log() noexcept {
  if (m_online && m_old_table != m_new_table) {
    const auto err = row_log_table_get_error(index());

    if (err != DB_SUCCESS) {
      m_trx->error_key_num = SERVER_CLUSTER_INDEX_ID;
      return err;
    }
  }

  return DB_SUCCESS;
}

void Context::note_max_trx_id(dict_index_t *index) noexcept {
  if (!m_online || m_new_table != m_old_table) {
    return;
  }

  auto rw_latch = dict_index_get_lock(index);

  rw_lock_x_lock(rw_latch, UT_LOCATION_HERE);

  ut_a(dict_index_get_online_status(index) == ONLINE_INDEX_CREATION);

  const auto max_trx_id = row_log_get_max_trx(index);

  if (max_trx_id > index->trx_id) {
    index->trx_id = max_trx_id;
  }

  rw_lock_x_unlock(rw_latch);
}
```

## 동작 흐름

```text
 L517  Loader loader{*this}
 L519  cleanup(loader.build_all())                  --> [06]
         L308  오류 키 번호를 trx->error_key_num 에 (중복 키 메시지용)
         L313  온라인 ADD INDEX 이고 실패면, 만들던 인덱스마다
                 COMPLETE                 그대로 (나중에 drop_indexes 가 지운다)
                 CREATION   L333  row_log_abort_sec  online_status = ABORTED, row log 해제
                            L334  DICT_CORRUPT 표시
                            L336  new_table->drop_aborted = true
                 ABORTED(_DROPPED)        그대로
         L349  flush_observer 가 있으면
                 L355  실패면 interrupted()  flush 가 페이지를 쓰지 않고 버린다
                                             (buf0flu.cc L3537-L3538 BUF_REMOVE_FLUSH_NO_WRITE)
                 L358  observer->flush()       빌드한 페이지를 디스크로
                 L368  Clone_notify(SPACE_ALTER_INPLACE_BULK)
                 L374  중단 요청(KILL) 이면 DB_INTERRUPTED
                 L378  성공이고 재구성이면 새 테이블의 인덱스마다 Builder::write_redo
 L523  (디버그) 플러시 뒤에 인덱스 검증
```

이 함수가 redo 대신 플러시로 내구성을 맞추는 이유는 빌드가 페이지를 redo 없이 쓰기 때문이다. 아래는 그 짝이다.

```text
 빌드 페이지의 내구성 (redo 를 건너뛴 대가)

 쓰기       btr0load.cc L317, L834  mtr->set_log_mode(MTR_LOG_NO_REDO)
            정렬된 레코드로 페이지를 채우지만 redo 를 남기지 않는다
 플러시     ddl0ctx.cc L358         observer->flush()  이 테이블스페이스의 더티 페이지를 전부 쓴다
 표시       ddl0builder.cc L1937    MLOG_INDEX_LOAD (space, page, index id) 를 redo 에 한 줄

 ADD INDEX 는 같은 일을 [06] 의 Builder::finalize 가 인덱스마다 한다 (ddl0builder.cc L1972-L1999)
   flush -> write_redo -> row_log_apply 순서
 재구성은 여기 cleanup 의 L378 에서 새 테이블 인덱스 전부에 write_redo
```

```text
 실패한 온라인 인덱스가 지나는 상태 (dict_index_t::online_status)

 ONLINE_INDEX_CREATION  [03] row_log_allocate 가 둔다. 다른 연결은 [07] 로 row log 에 쓴다
        |
        +-- 빌드 성공 -> [08] row_log_apply 끝  --> ONLINE_INDEX_COMPLETE  트리에 직접 쓴다
        |
        +-- 빌드 실패 -> cleanup L333          --> ONLINE_INDEX_ABORTED   쓰지도 로그하지도 않는다
                                                    (row_log_online_op_try 가 true 를 돌려 건너뛴다)
                         [09] commit=false 의 정리가 ddl::drop_indexes (ddl0ddl.cc L474) 로 치운다
                                                --> ONLINE_INDEX_ABORTED_DROPPED
                                                    (index_build_failed, ddl0ddl.cc L323)
```

## 결과가 쓰이는 곳

```text
 반환값 dberr_t
      --> [04] 의 clean_up 람다가 MySQL 오류로 바꾼다
 ONLINE_INDEX_ABORTED
      --> 다른 연결의 [07] 경로가 이 인덱스를 무시한다
 drop_aborted
      --> [09] commit=false 의 rollback_inplace_alter_table 에서 인덱스를 지운다
```

## 다루지 않는 것

`Context` 생성자(ddl0ctx.cc L46)의 버퍼 크기와 스레드 수 계산, FULLTEXT 인덱스 준비(`setup_fts_build`), AUTO_INCREMENT 열 채우기(`handle_autoinc`, `Sequence`), NOT NULL 으로 바뀐 열의 검사(`setup_nonnull`, `check_null_constraints`)는 이 흐름의 곁가지라 요약만 했다.
