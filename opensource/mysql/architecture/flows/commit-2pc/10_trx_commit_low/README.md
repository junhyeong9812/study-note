# trx_commit_low

상위: [커밋과 binlog 2PC](../README.md)

**InnoDB 트랜잭션이 파일 세계와 메모리 세계에서 커밋되는 자리다.** 두 단계다. 먼저 `trx_write_serialisation_history` 가 트랜잭션 번호(`trx->no`)를 받고 undo 로그 헤더를 커밋 상태로 바꾸고 update undo 를 history list 에 올린 뒤, 그 mtr 을 `mtr_commit` 한다. 주석이 이 순간을 "파일 기반 자료구조에서 커밋이 일어나는 시점"이라고 부른다(L2174-L2179). 그다음 `trx_commit_in_memory` 가 잠금을 풀고 트랜잭션을 활성 목록에서 빼고, redo 를 지금 내릴지 미룰지 정한다. 내구성은 이 mtr 의 redo 가 디스크에 닿을 때 생긴다.

## 위치

`storage` / `innobase` / `trx` / `trx0trx.cc` L2137-L2226 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2137-L2226))

## 실제 코드

`storage` / `innobase` / `trx` / `trx0trx.cc` L2137-L2226 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2137-L2226))

```cpp
// trx0trx.cc L2137-L2226
void trx_commit_low(trx_t *trx, mtr_t *mtr) {
  assert_trx_nonlocking_or_in_list(trx);
  ut_ad(!trx_state_eq(trx, TRX_STATE_COMMITTED_IN_MEMORY));
  ut_ad(!mtr || mtr->is_active());
  /* undo_no is non-zero if we're doing the final commit. */
  if (trx->fts_trx != nullptr && trx->undo_no != 0 &&
      trx->lock.que_state != TRX_QUE_ROLLING_BACK) {
    dberr_t error;

    ut_a(!trx_is_autocommit_non_locking(trx));

    error = fts_commit(trx);

    /* FTS-FIXME: Temporarily tolerate DB_DUPLICATE_KEY
    instead of dying. This is a possible scenario if there
    is a crash between insert to DELETED table committing
    and transaction committing. The fix would be able to
    return error from this function */
    if (error != DB_SUCCESS && error != DB_DUPLICATE_KEY) {
      /* FTS-FIXME: once we can return values from this
      function, we should do so and signal an error
      instead of just dying. */

      ut_error;
    }
  }

  bool serialised;

  if (mtr != nullptr) {
    mtr->set_sync();

    DEBUG_SYNC_C("trx_sys_before_assign_no");

    serialised = trx_write_serialisation_history(trx, mtr);

    /* The following call commits the mini-transaction, making the
    whole transaction committed in the file-based world, at this
    log sequence number. The transaction becomes 'durable' when
    we write the log to disk, but in the logical sense the commit
    in the file-based data structures (undo logs etc.) happens
    here.

    NOTE that transaction numbers, which are assigned only to
    transactions with an update undo log, do not necessarily come
    in exactly the same order as commit lsn's, if the transactions
    have different rollback segments. To get exactly the same
    order we should hold the kernel mutex up to this point,
    adding to the contention of the kernel mutex. However, if
    a transaction T2 is able to see modifications made by
    a transaction T1, T2 will always get a bigger transaction
    number and a bigger commit lsn than T1. */

    /*--------------*/

    DBUG_EXECUTE_IF("trx_commit_to_the_end_of_log_block", {
      const size_t space_left = mtr->get_expected_log_size();
      mtr_commit_mlog_test_filling_block(*log_sys, space_left);
    });

    mtr_commit(mtr);

    DBUG_PRINT("trx_commit", ("commit lsn at " LSN_PF, mtr->commit_lsn()));

    DBUG_EXECUTE_IF(
        "ib_crash_during_trx_commit_in_mem", if (trx_is_rseg_updated(trx)) {
          log_make_latest_checkpoint();
          DBUG_SUICIDE();
        });
    /*--------------*/

  } else {
    serialised = false;
  }
#ifdef UNIV_DEBUG
  /* In case of this function is called from a stack executing
     THD::release_resources -> ...
        innobase_connection_close() ->
               trx_rollback_for_mysql... -> .
     mysql's thd does not seem to have
     thd->debug_sync_control defined any longer. However the stack
     is possible only with a prepared trx not updating any data.
  */
  if (trx->mysql_thd != nullptr && trx_is_redo_rseg_updated(trx)) {
    DEBUG_SYNC_C("before_trx_state_committed_in_memory");
  }
#endif

  trx_commit_in_memory(trx, mtr, serialised);
}
```

부르는 쪽 `trx_commit` 이다. 롤백 세그먼트를 쓴 트랜잭션에만 mtr 을 연다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L2229-L2249 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2229-L2249))

```cpp
// trx0trx.cc L2229-L2249
void trx_commit(trx_t *trx) /*!< in/out: transaction */
{
  mtr_t *mtr;
  mtr_t local_mtr;

  DBUG_EXECUTE_IF("ib_trx_commit_crash_before_trx_commit_start",
                  DBUG_SUICIDE(););

  if (trx_is_rseg_updated(trx)) {
    mtr = &local_mtr;

    DBUG_EXECUTE_IF("ib_trx_commit_crash_rseg_updated", DBUG_SUICIDE(););

    mtr_start_sync(mtr);

  } else {
    mtr = nullptr;
  }

  trx_commit_low(trx, mtr);
}
```

update undo 를 history list 로 보내는 부분이다(`trx_write_serialisation_history` 안).

`storage` / `innobase` / `trx` / `trx0trx.cc` L1596-L1621 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L1596-L1621))

```cpp
// trx0trx.cc L1596-L1621
    /* Will set trx->no and will add rseg to purge queue. */
    serialised = trx_serialisation_number_get(trx, redo_rseg_undo_ptr,
                                              temp_rseg_undo_ptr);

    /* It is not necessary to obtain trx->undo_mutex here because
    only a single OS thread is allowed to do the transaction commit
    for this transaction. */
    if (trx->rsegs.m_redo.update_undo != nullptr) {
      page_t *undo_hdr_page;

      undo_hdr_page =
          trx_undo_set_state_at_finish(trx->rsegs.m_redo.update_undo, mtr);

      /* Delay update of rseg_history_len if we plan to add
      non-redo update_undo too. This is to avoid immediate
      invocation of purge as we need to club these 2 segments
      with same trx-no as single unit. */
      bool update_rseg_len = !(trx->rsegs.m_noredo.update_undo != nullptr);

      /* Set flag if GTID information need to persist. */
      auto undo_ptr = &trx->rsegs.m_redo;
      trx_undo_gtid_set(trx, undo_ptr->update_undo, false);

      trx_undo_update_cleanup(trx, undo_ptr, undo_hdr_page, update_rseg_len,
                              (update_rseg_len ? 1 : 0), mtr);
    }
```

`trx_commit_in_memory` 에서 잠금을 풀고 redo 를 어떻게 할지 정하는 부분이다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L1983-L1990 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L1983-L1990))

```cpp
// trx0trx.cc L1983-L1990

  } else {
    trx_release_impl_and_expl_locks(trx, serialised);

    /* Removed the transaction from the list of active transactions.
    It no longer holds any user locks. */

    ut_ad(trx_state_eq(trx, TRX_STATE_COMMITTED_IN_MEMORY));
```

`storage` / `innobase` / `trx` / `trx0trx.cc` L2046-L2067 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2046-L2067))

```cpp
// trx0trx.cc L2046-L2067
    lsn_t lsn = mtr->commit_lsn();

    if (lsn == 0) {
      /* Nothing to be done. */
    } else if (trx->flush_log_later) {
      /* Do nothing yet */
      trx->must_flush_log_later = true;

      /* Remember current ddl_operation, because trx_init()
      later will set ddl_operation to false. And the final
      flush is even later. */
      trx->ddl_must_flush = trx->ddl_operation;
    } else if ((srv_flush_log_at_trx_commit == 0 ||
                thd_requested_durability(trx->mysql_thd) ==
                    HA_IGNORE_DURABILITY) &&
               (!trx->ddl_operation)) {
      /* Do nothing */
    } else {
      trx_flush_log_if_needed(lsn, trx);
    }

    trx->commit_lsn = lsn;
```

미루지 않을 때 쓰는 `innodb_flush_log_at_trx_commit` 분기다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L1722-L1771 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L1722-L1771))

```cpp
// trx0trx.cc L1722-L1771
/** If required, flushes the log to disk based on the value of
 innodb_flush_log_at_trx_commit. */
static void trx_flush_log_if_needed_low(lsn_t lsn) /*!< in: lsn up to which logs
                                                   are to be flushed. */
{
#ifdef _WIN32
  bool flush = true;
#else
  bool flush = srv_unix_file_flush_method != SRV_UNIX_NOSYNC;
#endif /* _WIN32 */

  Wait_stats wait_stats;

  switch (srv_flush_log_at_trx_commit) {
    case 2:
      /* Write the log but do not flush it to disk */
      flush = false;
      [[fallthrough]];
    case 1:
      /* Write the log and optionally flush it to disk */
      wait_stats = log_write_up_to(*log_sys, lsn, flush);

      MONITOR_INC_WAIT_STATS(MONITOR_TRX_ON_LOG_, wait_stats);

      return;
    case 0:
      /* Do nothing */
      return;
  }
}

/** If required, flushes the log to disk based on the value of
 innodb_flush_log_at_trx_commit. */
static void trx_flush_log_if_needed(lsn_t lsn, /*!< in: lsn up to which logs are
                                               to be flushed. */
                                    trx_t *trx) /*!< in/out: transaction */
{
  trx->op_info = "flushing log";

  DEBUG_SYNC_C("trx_flush_log_if_needed");

  if (trx->ddl_operation || trx->ddl_must_flush) {
    auto wait_stats = log_write_up_to(*log_sys, lsn, true);
    MONITOR_INC_WAIT_STATS(MONITOR_TRX_ON_LOG_, wait_stats);
  } else {
    trx_flush_log_if_needed_low(lsn);
  }

  trx->op_info = "";
}
```

## 동작 흐름

```text
 trx_commit (L2229)
 L2237  롤백 세그먼트를 썼으면 (rseg updated)
 L2242    mtr_start_sync(mtr)                    없으면 mtr = nullptr (읽기 전용 등)
 L2248  trx_commit_low(trx, mtr)

 trx_commit_low
 L2142  FTS 가 있고 최종 커밋이면 L2148 fts_commit
 L2166  mtr 이 있으면
 L2167    mtr->set_sync()
 L2171    serialised = trx_write_serialisation_history(trx, mtr)
            L1571  insert undo 상태를 끝으로 (set_state_at_finish)
            L1597  trx_serialisation_number_get      trx->no 부여, rseg 를 purge 큐에
            L1607  update undo 상태를 끝으로
            L1617  GTID 영속화 표시
            L1619  trx_undo_update_cleanup -> trx_purge_add_update_undo_to_history (trx0undo.cc L1937)
 L2197    mtr_commit(mtr)                          커밋 기록이 log buffer 로. commit_lsn 확정
 L2225  trx_commit_in_memory(trx, mtr, serialised)

 trx_commit_in_memory (L1935)
 L1949  autocommit 비잠금 읽기 전용이면       read view 닫고 NOT_STARTED 로 끝
 L1984  아니면 trx_release_impl_and_expl_locks   활성 목록에서 빼고 잠금을 모두 푼다
 L2010  insert undo 는 바로 정리 (trx_undo_insert_cleanup)
 L2046  lsn = mtr->commit_lsn()
 L2048    0 이면                                   할 일 없음
 L2050    flush_log_later 이면                     must_flush_log_later = true  <-- [09] 에서 온 경로
 L2058    flush_log_at_trx_commit == 0 또는 HA_IGNORE_DURABILITY, DDL 아님   아무것도 안 함
 L2064    그 밖                                    trx_flush_log_if_needed(lsn, trx)
 L2067  commit_lsn = lsn
 L2114  abort 면 FORCED_ROLLBACK, 아니면 NOT_STARTED
 L2126  trx_init(trx)                              trx->id = 0 (L159)
```

undo 로그가 커밋에서 어디로 가는지가 [purge] 와 [일관 읽기(MVCC)] 의 출발점이다.

```text
 undo 의 행방 (trx_write_serialisation_history, trx_commit_in_memory)

 insert undo
   커밋 때   상태를 끝으로 (L1571)
   이후      L2010 trx_undo_insert_cleanup 으로 바로 정리
 update undo
   커밋 때   trx->no 부여 (L1597), 상태를 끝으로 (L1607)
   이후      history list 에 trx->no 순서로 (L1619). [purge] 가 치운다

 주석 (L1546-L1549): history list 에 trx 번호 순서로 올리기 위해 rseg 뮤텍스를 쥔다
```

```text
 innodb_flush_log_at_trx_commit 의 분기 (trx_flush_log_if_needed_low, L1724)

 값   L 줄    호출                                 동작
 2    L1736   log_write_up_to(lsn, flush=false)    flush = false 로 두고 1 로 떨어진다. write 만
 1    L1740   log_write_up_to(lsn, flush)          write + fsync (NOSYNC 가 아니면)
 0    L1747   (none)                               아무것도 안 한다

 DDL 트랜잭션이면 값과 무관하게 log_write_up_to(lsn, true) (L1763-L1764)
```

## 결과가 쓰이는 곳

```text
 commit_lsn
      --> [09] trx_commit_complete_for_mysql 이 must_flush_log_later 일 때 이 LSN 까지 내린다
      --> [mini-transaction과 redo 기록] 의 log_write_up_to
 history list 의 update undo
      --> [purge] 가 trx_purge 로 가져가 치운다
      --> [일관 읽기(MVCC)] 의 이전 버전 만들기가 purge 전까지 이 undo 를 읽는다
 trx_release_impl_and_expl_locks
      --> [레코드 잠금] 에서 이 트랜잭션이 쥔 잠금이 모두 풀린다 (주석 L1987-L1988)
```

## 다루지 않는 것

`trx_serialisation_number_get` 과 purge 큐, 전문 검색 커밋(`fts_commit`), 임시 테이블 롤백 세그먼트(`m_noredo`), GTID 영속화(`gtid_persistor`), 잠금 해제의 내부(`lock_trx_release_locks`), 수정 테이블 캐시 갱신, 디버그 크래시 지점은 이 흐름의 곁가지라 줄만 적었다.
