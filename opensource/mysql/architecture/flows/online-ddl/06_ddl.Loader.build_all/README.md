# ddl::Loader::build_all

상위: [온라인 DDL](../README.md)

**인덱스를 행 단위 삽입이 아니라 "읽고, 정렬하고, 아래에서 위로 쌓는" 방식으로 만든다.** 클러스터드 인덱스를 한 번 훑으면서 새 인덱스마다 키를 뽑아 정렬 버퍼와 임시 파일에 모으고, 다 모이면 작업 큐에 넣어 병합 정렬과 B+Tree 적재를 돌린다. 인덱스 하나를 맡은 `Builder` 가 상태 기계로 움직이며, 마지막 상태 `FINISH` 에서 온라인 ADD INDEX 라면 [08] row log 적용을 부른다.

## 위치

`storage` / `innobase` / `ddl` / `ddl0loader.cc` L477-L506 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0loader.cc#L477-L506))

## 실제 코드

`storage` / `innobase` / `ddl` / `ddl0loader.cc` L477-L506 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0loader.cc#L477-L506))

```cpp
// ddl0loader.cc L477-L506
dberr_t Loader::build_all() noexcept {
  auto err = prepare();

  if (err == DB_SUCCESS) {
    err = scan_and_build_indexes();
  }

  DBUG_EXECUTE_IF("ib_build_indexes_too_many_concurrent_trxs",
                  err = DB_TOO_MANY_CONCURRENT_TRXS;
                  m_ctx.m_trx->error_state = err;);

  if (m_ctx.m_fts.m_ptr != nullptr) {
    /* Clean up FTS psort related resource */
    ut::delete_(m_ctx.m_fts.m_ptr);
    m_ctx.m_fts.m_ptr = nullptr;
  }

  DICT_TF2_FLAG_UNSET(m_ctx.m_new_table, DICT_TF2_FTS_ADD_DOC_ID);

  if (err == DB_AUTOINC_READ_ERROR) {
    auto trx = m_ctx.m_trx;
    ib_senderrf(trx->mysql_thd, IB_LOG_LEVEL_ERROR, ER_AUTOINC_READ_FAILED);
  }

  if (err != DB_SUCCESS) {
    m_ctx.set_error(err);
  }

  return err;
}
```

스캔과 빌드다. 커서가 클러스터드 인덱스를 훑어 `Builder` 들에 행을 나눠 주고, 끝나면 `load` 로 정렬과 적재를 돌린다.

`storage` / `innobase` / `ddl` / `ddl0loader.cc` L398-L475 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0loader.cc#L398-L475))

```cpp
// ddl0loader.cc L398-L475
dberr_t Loader::scan_and_build_indexes() noexcept {
// ... (L399-L425 생략: 디버그 동기화 지점)

  auto cursor = Cursor::create_cursor(m_ctx);

  if (cursor == nullptr) {
    ut_d(cleanup());
    return DB_OUT_OF_MEMORY;
  }

  auto err = m_ctx.read_init(cursor);

  if (err == DB_SUCCESS) {
    cursor->open();

    /* Reset the MySQL row buffer that is used when reporting duplicate keys.
    Return needs to be checked since innobase_rec_reset tries to evaluate
    set_default() which can also be a function and might return errors */
    innobase_rec_reset(m_ctx.m_table);

    if (m_ctx.m_table->in_use->is_error()) {
      err = DB_COMPUTE_VALUE_FAILED;
    } else {
      /* Read clustered index of the table and create files for secondary
      index entries for merge sort and bulk build of the indexes. */
      err = cursor->scan(m_builders);
    }

    /* Close the mtr and release any locks, wait for FTS etc. */
    err = cursor->finish(err);

    DBUG_EXECUTE_IF("force_virtual_col_build_fail",
                    err = DB_COMPUTE_VALUE_FAILED;);

    DEBUG_SYNC_C("ddl_after_scan");

    if (err == DB_SUCCESS) {
      err = load();
    }

    DBUG_EXECUTE_IF("ddl_insert_big_row", err = DB_TOO_BIG_RECORD;);
  }

  if (cursor != nullptr) {
    ut::delete_(cursor);
    cursor = nullptr;
  }

  ut_d(cleanup());

  return err;
}
```

`load` 는 작업 큐를 만들고 `innodb_ddl_threads` 만큼 스레드를 띄워 함께 큐를 비운다.

`storage` / `innobase` / `ddl` / `ddl0loader.cc` L289-L364 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0loader.cc#L289-L364))

```cpp
// ddl0loader.cc L289-L364
dberr_t Loader::load() noexcept {
  ut_a(m_taskq == nullptr);

  const bool sync = m_ctx.m_max_threads <= 1;

  m_taskq = ut::new_withkey<Task_queue>(ut::make_psi_memory_key(mem_key_ddl),
                                        m_ctx, sync);

  if (m_taskq == nullptr) {
    return DB_OUT_OF_MEMORY;
  }

  for (auto builder : m_builders) {
    ut_a(builder->get_state() == Builder::State::ADD);
    /* RTrees are built during the scan phase, using row by row insert. */
    if (!builder->is_spatial_index()) {
      builder->set_next_state();
      add_task(Task{builder});
    }
  }

  std::vector<std::thread> threads{};

  if (!sync) {
    auto fn = [this](PSI_thread_seqnum seqnum) -> dberr_t {
#ifdef UNIV_PFS_THREAD
      Runnable runnable{ddl_thread_key, seqnum};
#else
      Runnable runnable{PSI_NOT_INSTRUMENTED, seqnum};
#endif /* UNIV_PFS_THREAD */

      current_thd = nullptr;

      const auto err = runnable(&Task_queue::execute, m_taskq);

      if (err != DB_SUCCESS) {
        m_taskq->signal();
      }

      return err;
    };

    for (size_t i = 1; i < m_ctx.m_max_threads; ++i) {
      try {
        threads.push_back(std::thread{fn, i});
      } catch (...) {
        ib::warn(ER_DDL_MSG_1);
        m_taskq->thread_create_failed();
        break;
      }
    }
  }

  auto err = m_taskq->execute();

  if (!sync) {
    if (err != DB_SUCCESS) {
      m_taskq->signal();
    }

    for (auto &thread : threads) {
      thread.join();
    }
  }

  if (err == DB_SUCCESS) {
    err = m_ctx.get_error();
  }

  ut_ad(m_taskq->validate() || err != DB_SUCCESS);

  ut::delete_(m_taskq);
  m_taskq = nullptr;

  return err;
}
```

`Builder` 의 마지막 두 단계다. 온라인이고 같은 테이블(ADD INDEX)이면 `finalize` 에서 페이지를 플러시하고 row log 를 적용한다.

`storage` / `innobase` / `ddl` / `ddl0builder.cc` L2061-L2096 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0builder.cc#L2061-L2096))

```cpp
// ddl0builder.cc L2061-L2096
dberr_t Builder::finish() noexcept {
  if (get_error() != DB_SUCCESS) {
    set_next_state();
    return get_error();
  }

  ut_a(m_n_sort_tasks == 0);
  ut_a(get_state() == State::FINISH);

  for (auto thread_ctx : m_thread_ctxs) {
    thread_ctx->m_file.m_file.close();
  }

  dberr_t err{DB_SUCCESS};

  if (get_error() != DB_SUCCESS || !m_ctx.m_online) {
    /* Do not apply any online log. */
  } else if (m_ctx.m_old_table != m_ctx.m_new_table) {
    ut_a(!m_index->online_log);
    ut_a(m_index->online_status == ONLINE_INDEX_COMPLETE);

    auto observer = m_ctx.m_trx->flush_observer;
    observer->flush();

  } else {
    err = finalize();

    if (err != DB_SUCCESS) {
      set_error(err);
    }
  }

  set_next_state();

  return get_error();
}
```

`storage` / `innobase` / `ddl` / `ddl0builder.cc` L1972-L2006 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/ddl/ddl0builder.cc#L1972-L2006))

```cpp
// ddl0builder.cc L1972-L2006
dberr_t Builder::finalize() noexcept {
  ut_a(m_ctx.m_need_observer);
  ut_a(get_state() == State::FINISH);

  auto observer = m_ctx.m_trx->flush_observer;

  observer->flush();

  dberr_t err = DB_SUCCESS;
  auto new_table = m_ctx.m_new_table;
  auto space_id =
      new_table != nullptr ? new_table->space : dict_sys_t::s_invalid_space_id;

  Clone_notify notifier(Clone_notify::Type::SPACE_ALTER_INPLACE_BULK, space_id,
                        false);
  if (notifier.failed()) {
    err = DB_ERROR;
  }

  if (err == DB_SUCCESS) {
    write_redo(m_index);

    DEBUG_SYNC(m_ctx.thd(), "row_log_apply_before");

    err = row_log_apply(m_ctx.m_trx, m_index, m_ctx.m_table, m_local_stage);

    DEBUG_SYNC(m_ctx.thd(), "row_log_apply_after");
  }

  if (err != DB_SUCCESS) {
    set_error(err);
  }

  return err;
}
```

`Builder` 의 상태 목록이다.

`storage` / `innobase` / `include` / `ddl0impl-builder.h` L48-L79 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/ddl0impl-builder.h#L48-L79))

```cpp
// ddl0impl-builder.h L48-L79
struct Builder {
  /** Build phase/states. */
  enum class State : uint8_t {
    /** Initial phase. */
    INIT,

    /** Collect the rows for the index to build. */
    ADD,

    /** Setup the merge sort and add the tasks to the task queue. */
    SETUP_SORT,

    /** Sort the collected rows, if required. The builder moves to state
    BTREE_BUILD after all sort tasks are completed successfully or there
    was an error during the sort phase. */
    SORT,

    /** Build the btree. */
    BTREE_BUILD,

    /** FTS sort and build, this is done in one "step" */
    FTS_SORT_AND_BUILD,

    /** Finish the loading of the index. */
    FINISH,

    /** Stop on success. */
    STOP,

    /** Stop on error. */
    ERROR
  };
```

## 동작 흐름

```text
 L478  prepare()                      인덱스마다 Builder 하나 (L380-L389)
 L481  scan_and_build_indexes()
         L427  Cursor::create_cursor   클러스터드 인덱스를 읽을 커서
         L434  m_ctx.read_init          NOT NULL 검사 목록, PK 정렬 생략 설정
         L449  cursor->scan(m_builders) 행마다 Builder 들이 키를 뽑아 버퍼에 넣고
                                        버퍼가 차면 정렬해 임시 파일에 쓴다
         L453  cursor->finish           mtr 를 닫고 래치를 놓는다
         L461  load()
                 L301  Builder 마다 ADD -> 다음 상태, 작업 큐에 넣는다 (R-Tree 는 스캔 중 이미 삽입)
                 L331  m_max_threads - 1 개 스레드 생성, L342 자신도 execute
                 L349  join
 L488  FULLTEXT 정렬 자원 해제
 L501  오류면 m_ctx.set_error
```

```text
 Builder 상태 기계 (ddl0impl-builder.h L50-L79)

 INIT
   v
 ADD            스캔 중. 키를 정렬 버퍼에 모은다 (스캔 스레드)
   v  load() 가 작업 큐에 넣는다
 SETUP_SORT     병합 정렬 작업을 만든다 (setup_sort, L2045)
   v
 SORT           임시 파일의 정렬된 덩어리들을 병합 (merge_sort, L2008)
   v            모든 정렬 작업이 끝나면 다음 상태로 큐에 다시 들어간다 (L2037-L2039)
 BTREE_BUILD    정렬된 순서로 리프부터 페이지를 채워 올라간다 (btree_build, L1776)
   v            redo 없이 쓴다 (btr0load.cc L317)
 FINISH         finish (L2061)
   |              온라인 ADD INDEX  -> finalize: flush, write_redo, row_log_apply [08]
   |              온라인 재구성     -> flush 만 (row log 는 [04] 와 [09] 가 적용)
   |              온라인 아님       -> 할 일 없음
   v
 STOP / ERROR

 전이는 set_next_state (ddl0builder.cc L2108-L2154). 오류가 있으면 어느 상태에서든 ERROR
 FULLTEXT 인덱스는 ADD 에서 FTS_SORT_AND_BUILD 로 간다 (L2120)
 is_skip_file_sort 면 ADD 에서 바로 FINISH 로 간다 (L2122-L2126)
```

빌드가 도는 시간 동안 다른 연결이 무엇을 하는지 같이 놓고 보면, row log 가 왜 필요한지 보인다.

```text
 ADD INDEX 의 시간축 (ALTER 연결 A 의 MDL = SU, 다른 연결 B 의 INSERT)

 A                                          B                      row log
 [03] 읽기 뷰 T0 를 잡는다 (X 아래)
 [01] SU 로 내림
 scan  T0 시점 행을 읽어 정렬 파일로                                 []
                                            INSERT k1 (커밋)
                                              새 인덱스 CREATION
                                              --> [07] INSERT k1      [+k1]
 SORT  병합 정렬
                                            DELETE k0               [+k1 -k0]
 BTREE_BUILD  k0 가 든 정렬 결과로 적재
 FINISH -> finalize
   flush, MLOG_INDEX_LOAD
   [08] row_log_apply 로 블록을 읽어 적용   INSERT k2 -> [07]       [+k1 -k0 +k2]
     마지막 블록은 index->lock X 를 쥐고                              B 는 lock 대기
     적용 -> ONLINE_INDEX_COMPLETE                                   해제
                                            INSERT k3 -> 트리에 직접
 [01] X 로 올림 -> [09]
```

## 결과가 쓰이는 곳

```text
 새 인덱스 트리
      --> 온라인 ADD INDEX 면 [08] 뒤 ONLINE_INDEX_COMPLETE 로 다른 연결에 열린다
      --> [09] 에서 사전에 커밋된다
 m_ctx 의 오류
      --> [05] cleanup 이 실패한 온라인 인덱스를 ABORTED 로 바꾼다
 중복 키
      --> 정렬 중 Dup 으로 찾아 trx->error_key_num 과 함께 [04] 가 메시지를 만든다
```

## 다루지 않는 것

`Cursor` 와 `Parallel_cursor` 의 병렬 스캔, 정렬 버퍼 인코딩(`ddl::buf_encode`)과 임시 파일 형식, `Merge_file_sort` 의 다단계 병합, `Btree_load` 의 페이지 채우기와 fill factor, FULLTEXT 빌드(`FTS_SORT_AND_BUILD`), 공간 인덱스의 행 단위 삽입, 재구성 때 열 매핑과 기본값 채우기(`copy_row`, `create_add_cols`)는 이 흐름의 곁가지라 요약만 했다.
