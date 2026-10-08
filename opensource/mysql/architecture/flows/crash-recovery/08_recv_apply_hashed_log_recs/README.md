# recv_apply_hashed_log_recs

상위: [크래시 복구](../README.md)

**해시에 모인 redo 한 배치를 페이지들에 적용하고, 그 결과를 디스크까지 내리는 함수다.** 테이블스페이스마다 파일을 열고(이때 doublewrite 복원이 한 번 더 일어난다), 페이지마다 버퍼 풀에 있으면 그 자리에서 적용하고 없으면 이웃 페이지와 묶어 **비동기 읽기**를 건다. 실제 적용 대부분은 읽기를 마친 I/O 핸들러 스레드가 [09] 로 한다. 이 함수는 `n_pages_to_recover` 가 0 이 되기를 기다린 뒤, 페이지 클리너에 flush list 배치를 시키고 버퍼 풀을 통째로 무효화한다. 다음 배치가 빈 버퍼 풀에서 시작하게 하는 것이다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L1173-L1309 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L1173-L1309))

## 실제 코드

페이지마다 적용을 건다.

`storage` / `innobase` / `log` / `log0recv.cc` L1173-L1248 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L1173-L1248))

```cpp
// log0recv.cc L1173-L1248
void recv_apply_hashed_log_recs(log_t &log) {
  mutex_enter(&recv_sys->mutex);
  ut_a(!srv_read_only_mode);

  recv_sys->apply_log_recs = true;

  const auto batch_size = recv_sys->n_pages_to_recover.value();

  ib::info(ER_IB_MSG_707, ulonglong{batch_size});

  static const size_t PCT = 10;

  size_t pct = PCT;
  size_t applied = 0;
  auto unit = batch_size / PCT;

  if (unit <= PCT) {
    pct = 100;
    unit = batch_size;
  }

  auto start_time = std::chrono::steady_clock::now();

  for (const auto &space : *recv_sys->spaces) {
    bool dropped = false;

    if (space.first != TRX_SYS_SPACE) {
      dberr_t err = fil_tablespace_open_for_recovery(space.first);
      if (err == DB_CORRUPTION) {
        /* Page couldn't be recovered from double-write, we cannot proceed
        with recovery. Skip applying redos and abort the startup. */
        mutex_exit(&recv_sys->mutex);
        ib::fatal(UT_LOCATION_HERE, ER_IB_ERR_CORRUPT_TABLESPACE_UNRECOVERABLE,
                  space.first);
      } else if (err != DB_SUCCESS) {
        ut_a_eq(err, DB_FAIL);

        /* Tablespace was dropped. It should not have been scanned unless it
        is an undo space that was under construction. */

        if (fil_tablespace_lookup_for_recovery(space.first)) {
          ut_ad(fsp_is_undo_tablespace(space.first));
        }
        dropped = true;
      }
    }

    for (auto pages : space.second.m_pages) {
      ut_ad(pages.second->space == space.first);

      if (dropped) {
        pages.second->state = RECV_DISCARDED;
        one_less_page_to_recover();
      } else {
        recv_apply_log_rec(pages.second);
      }

      ++applied;

      if (unit == 0 || (applied % unit) == 0) {
        ib::info(ER_IB_MSG_708) << pct << "%";

        pct += PCT;

        start_time = std::chrono::steady_clock::now();

      } else if (std::chrono::steady_clock::now() - start_time >=
                 PRINT_INTERVAL) {
        start_time = std::chrono::steady_clock::now();

        ib::info(ER_IB_MSG_709)
            << std::setprecision(2)
            << ((double)applied * 100) / (double)batch_size << "%";
      }
    }
  }
```

기다리고, 내리고, 무효화한다.

`storage` / `innobase` / `log` / `log0recv.cc` L1250-L1309 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L1250-L1309))

```cpp
// log0recv.cc L1250-L1309
  /* Wait until all the pages have been processed */
  mutex_exit(&recv_sys->mutex);
  recv_sys->n_pages_to_recover.await_zero();
  mutex_enter(&recv_sys->mutex);
  ut_a_eq(recv_sys->n_pages_to_recover.value(), 0);

  /* Flush all the file pages to disk and invalidate them in the buffer pool */
  ut_d(log.disable_redo_writes = true);
  ut_a(recv_sys->flush_end != nullptr);

  mutex_exit(&recv_sys->mutex);

  /* Stop the recv_writer thread from issuing any LRU
  flush batches. */
  mutex_enter(&recv_sys->writer_mutex);

  /* Wait for any currently run batch to end. Note that BUF_FLUSH_LIST could
  only be initiated by us in earlier call, but buf_pool_invalidate() waits for
  all batches to finish, so only BUF_FLUSH_LRU can be running.
  TBD: why is it important to wait for BUF_FLUSH_LRU to finish here? */
  buf_flush_await_no_flushing(nullptr, BUF_FLUSH_LRU);

  os_event_reset(recv_sys->flush_end);

  /* We are about to request BUF_FLUSH_LIST, in hope to write all dirty pages
  back to disc, so that we can then invalidate the BP, before next batch.
  However, buf_flush_page_and_try_neighbors() skips over io-fixed pages, so
  they would be left in BP even if dirty. We awaited for
  recv_sys->n_pages_to_recover to drop to zero, but this happens before io
  completer releases the latch and io-fix from the block.
  Therefore we wait for all read operations to finish here by using a method
  which looks at a counter which is decremented only after io completer
  io-unfixes the block. Also, this is important for the subsequent
  buf_pool_invalidate() that internally uses buf_LRU_scan_and_free_block()
  which has the same issue: skips over io-fixed pages. */
  buf_pool_wait_for_no_pending_io();

  recv_sys->flush_type = BUF_FLUSH_LIST;

  os_event_set(recv_sys->flush_start);

  os_event_wait(recv_sys->flush_end);

  buf_pool_invalidate();

  /* Allow batches from recv_writer thread. */
  mutex_exit(&recv_sys->writer_mutex);

  ut_d(log.disable_redo_writes = false);

  mutex_enter(&recv_sys->mutex);

  recv_sys->apply_log_recs = false;

  recv_sys_empty_hash();

  mutex_exit(&recv_sys->mutex);

  ib::info(ER_IB_MSG_710);
}
```

페이지 하나를 맡는 쪽이다.

`storage` / `innobase` / `log` / `log0recv.cc` L1116-L1171 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L1116-L1171))

```cpp
// log0recv.cc L1116-L1171
/** Apply the log records to a page
@param[in,out]  recv_addr       Redo log records to apply */
static void recv_apply_log_rec(recv_addr_t *recv_addr) {
  ut_ad(mutex_own(&recv_sys->mutex));
  ut_a(recv_addr->state != RECV_DISCARDED);

  bool found;
  const page_id_t page_id(recv_addr->space, recv_addr->page_no);

  const page_size_t page_size =
      fil_space_get_page_size(recv_addr->space, &found);
  ut_a(found);
  ut_a(!recv_sys->missing_ids.contains(recv_addr->space));
  ut_a(!recv_sys->deleted.contains(recv_addr->space));
  if (recv_addr->state == RECV_NOT_PROCESSED) {
    mutex_exit(&recv_sys->mutex);
    if (buf_page_peek(page_id)) {
      mtr_t mtr;

      mtr_start(&mtr);

      buf_block_t *block;

      block =
          buf_page_get(page_id, page_size, RW_X_LATCH, UT_LOCATION_HERE, &mtr);

      buf_block_dbg_add_level(block, SYNC_NO_ORDER_CHECK);
      /* TODO: when we start parsing a batch there's no page in BP, and we only
      add pages to BP once all deltas for a given batch are already in the
      hashmap. This can happen either during dict_boot() which reads a few pages
      before applying the last batch, or as part of applying a batch (which in
      case of last batch includes reading and applying changes from IBUF, too).
      In any case, if a page is in BP it must have been read after deltas meant
      for it were already added to the hashmap. This means io completer had to
      apply them. Therefore it makes no sense for us to try to apply anything,
      because it is guaranteed to be applied before we could get RW_X_LATCH on
      the block.

      We should simplify the code around here if below assert holds. */
#ifdef UNIV_DEBUG
      mutex_enter(&recv_sys->mutex);
      ut_a(recv_addr->state == RECV_PROCESSED);
      mutex_exit(&recv_sys->mutex);
#endif

      recv_recover_page(false, block);

      mtr_commit(&mtr);

    } else {
      recv_read_in_area(page_id, page_size);
    }

    mutex_enter(&recv_sys->mutex);
  }
}
```

이웃 페이지를 묶어 읽기를 건다.

`storage` / `innobase` / `log` / `log0recv.cc` L1027-L1114 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L1027-L1114))

```cpp
// log0recv.cc L1027-L1114
/** Reads in pages which have hashed log records, from an area around a given
page number.
@param[in]     requested_page_id
                   The page which has to be read in anyway, so we have an
                   opportunity to read pages nearby.
@param[in]     page_size
                   Size of pages in this page's space */
static void recv_read_in_area(const page_id_t &requested_page_id,
                              [[maybe_unused]] const page_size_t &page_size) {
  const page_no_t low_limit =
      ut_uint64_align_down(requested_page_id.page_no(), RECV_READ_AHEAD_AREA);

  size_t n = 0;

  std::array<page_no_t, RECV_READ_AHEAD_AREA> page_nos;

  for (page_no_t page_no = low_limit;
       page_no < low_limit + RECV_READ_AHEAD_AREA; ++page_no) {
    const page_id_t nearby_page_id(requested_page_id.space(), page_no);
    recv_addr_t *recv_addr = recv_get_rec(nearby_page_id);

    // ... (L1048-L1059 생략: 상태 전이가 어긋날 수 없는 이유를 적은 긴 주석과 단언)
    if (recv_addr != nullptr && !buf_page_peek(nearby_page_id)) {
      mutex_enter(&recv_sys->mutex);

      if (recv_addr->state == RECV_NOT_PROCESSED) {
        recv_addr->state = RECV_BEING_READ;

        page_nos[n++] = page_no;
      } else {
      // ... (L1068-L1102 생략: 상태 전이가 어긋날 수 없는 이유를 적은 긴 주석과 단언)
      }

      mutex_exit(&recv_sys->mutex);
    }
  }

  if (n > 0) {
    /* There are pages that need to be read. Go ahead and read them
    for recovery. */
    buf_read_recv_pages(requested_page_id.space(), page_nos.data(), n);
  }
}
```

## 동작 흐름

```text
 L1177  apply_log_recs = true                   이제 [09] 가 실제로 적용한다
 L1179  batch_size = n_pages_to_recover
 L1196  for space in recv_sys->spaces
 L1199    시스템 테이블스페이스가 아니면 fil_tablespace_open_for_recovery
            그 안에서 dblwr->recover(space)       (fil0fil.cc L9876)
 L1201      DB_CORRUPTION (dblwr 로도 못 고침) -> ib::fatal
 L1207      그 밖의 실패 = 드롭된 공간 -> dropped
 L1220    for page in space.m_pages
 L1223      dropped 면 RECV_DISCARDED, 남은 수 -1
 L1227      아니면 recv_apply_log_rec
 L1232      10% 마다 진행률 로그

 recv_apply_log_rec (L1118)
 L1130  RECV_NOT_PROCESSED 일 때만
 L1132    buf_page_peek: 이미 버퍼 풀에 있다
 L1140      buf_page_get(X 래치) -> L1161 recv_recover_page(false, block)
 L1166    없다 -> recv_read_in_area              같은 32 페이지 묶음(L94)을 비동기로

 L1252  n_pages_to_recover.await_zero()         모든 페이지가 [09] 를 마칠 때까지
 L1264  writer_mutex                            recv_writer 의 LRU 배치를 멈춘다
 L1270  진행 중인 LRU 배치를 기다린다
 L1285  buf_pool_wait_for_no_pending_io         io-fix 가 남은 페이지가 없을 때까지
 L1287  flush_type = BUF_FLUSH_LIST
 L1289  flush_start set, L1291 flush_end wait  페이지 클리너가 dirty 를 전부 쓴다
 L1293  buf_pool_invalidate                     버퍼 풀을 비운다
 L1302  apply_log_recs = false
 L1304  recv_sys_empty_hash                     다음 배치를 위해 해시를 비운다
```

적용은 이 함수가 건 비동기 읽기의 완료 처리에서 일어난다. 이미 버퍼 풀에 있던 페이지는 시작 스레드가 `recv_recover_page(false, block)` 를 부르지만, 소스 주석(L1143-L1154)은 그런 페이지는 읽힐 때 io completer 가 이미 적용했다고 보고, [09] 는 상태가 RECV_PROCESSED 면 곧바로 돌아간다(L2448-L2449).

```text
 적용 스레드 (S = 시작 스레드, 이 함수 / IO = I/O 핸들러 스레드 / PC = 페이지 클리너)

 S   page A 는 버퍼 풀에 있다 -> buf_page_get(X) -> recv_recover_page(false)
       (이미 PROCESSED 면 [09] 가 할 일 없이 돌아간다)
 S   page B 는 없다 -> recv_read_in_area
 S     B 와 이웃 C, D 를 RECV_BEING_READ 로 바꾸고 buf_read_recv_pages (비동기)
 IO  B 읽기 완료 buf_page_io_complete -> recovery 중이므로 [09] recv_recover_page(true)
 IO  C, D 도 같은 식으로. 페이지마다 남은 수 -1
 S   await_zero 에서 대기하다 0 이 되면 계속
 S   BUF_FLUSH_LIST 요청
 PC  dirty 페이지를 전부 쓴다
 S   buf_pool_invalidate
```

```text
 recv_read_in_area 의 묶음 (L1034)

 low_limit = page_no 를 RECV_READ_AHEAD_AREA 로 내림
 low_limit .. low_limit + AREA - 1 가운데
   해시에 레코드가 있고, 버퍼 풀에 없고, RECV_NOT_PROCESSED 인 것만
   RECV_BEING_READ 로 바꾸고 page_nos 에 모은다
 buf_read_recv_pages(space, page_nos, n)   한 번에 비동기 요청
 요청한 페이지만 버퍼 풀에 들어온다. 레코드가 없는 이웃은 읽지 않는다
```

## 결과가 쓰이는 곳

```text
 적용된 페이지
      --> BUF_FLUSH_LIST 배치로 데이터 파일에 쓰인다
      --> 체크포인트는 복구가 끝날 때까지 막혀 있다 (log0recv.cc L3907-L3909 주석)
 비워진 버퍼 풀과 해시
      --> [05] 가 스캔을 이어 가 다음 배치를 모은다
 RECV_DISCARDED
      --> 드롭된 테이블스페이스의 레코드는 적용하지 않고 버린다
```

## 다루지 않는 것

`buf_read_recv_pages` 가 인스턴스별 frame 여유를 기다리는 방식, 진행률 로그(ER_IB_MSG_708, 709), `fil_tablespace_open_for_recovery` 가 파일을 찾는 과정, undo 테이블스페이스 truncate 중의 예외, `recv_writer` 와 페이지 클리너 사이의 이벤트(`flush_start`, `flush_end`) 세부는 이 함수의 곁가지라 요약만 했다.
