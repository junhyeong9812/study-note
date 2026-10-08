# buf_LRU_get_free_block

상위: [버퍼 풀 페이지 획득](../README.md)

**읽어 들일 자리, 곧 비어 있는 블록 하나를 만들어 내는 함수다.** 규칙은 "블록은 언제나 free list 에서만 가져간다"이다. free list 가 비면 LRU 꼬리를 훑어 깨끗한 블록을 풀어 free list 로 보내고, 그것도 안 되면 LRU 꼬리의 dirty 블록 한 장을 **이 스레드가 직접 써서** 비운다. 어느 쪽이든 결과는 free list 로 가고, `goto loop` 로 처음부터 free list 를 다시 본다. 바퀴가 늘수록 더 깊이 훑고, 셋째 바퀴부터는 10ms 씩 쉰다.

## 위치

`storage` / `innobase` / `buf` / `buf0lru.cc` L1311-L1434 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1311-L1434))

## 실제 코드

함수 앞 주석이 바퀴별 전략을 요약해 둔다.

`storage` / `innobase` / `buf` / `buf0lru.cc` L1287-L1434 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1287-L1434))

```cpp
// buf0lru.cc L1287-L1434
/** Returns a free block from the buf_pool. The block is taken off the
free list. If free list is empty, blocks are moved from the end of the
LRU list to the free list.
This function is called from a user thread when it needs a clean
block to read in a page. Note that we only ever get a block from
the free list. Even when we flush a page or find a page in LRU scan
we put it to free list to be used.
* iteration 0:
  * get a block from free list, success:done
  * if buf_pool->try_LRU_scan is set
    * scan LRU up to srv_LRU_scan_depth to find a clean block
    * the above will put the block on free list
    * success:retry the free list
  * flush one dirty page from tail of LRU to disk
    * the above will put the block on free list
    * success: retry the free list
* iteration 1:
  * same as iteration 0 except:
    * scan whole LRU list
    * scan LRU list even if buf_pool->try_LRU_scan is not set
* iteration > 1:
  * same as iteration 1 but sleep 10ms
@param[in,out]  buf_pool        buffer pool instance
@return the free control block, in state BUF_BLOCK_READY_FOR_USE */
buf_block_t *buf_LRU_get_free_block(buf_pool_t *buf_pool) {
  buf_block_t *block = nullptr;
  bool freed = false;
  ulint n_iterations = 0;
  ulint flush_failures = 0;
  bool started_monitor = false;

  ut_ad(!mutex_own(&buf_pool->LRU_list_mutex));

  MONITOR_INC(MONITOR_LRU_GET_FREE_SEARCH);
loop:
  buf_LRU_check_size_of_non_data_objects(buf_pool);

  /* If there is a block in the free list, take it */
  block = buf_LRU_get_free_only(buf_pool);

  if (block != nullptr) {
    ut_ad(!block->page.someone_has_io_responsibility());
    ut_ad(buf_pool_from_block(block) == buf_pool);
    memset(&block->page.zip, 0, sizeof block->page.zip);

    if (started_monitor) {
      srv_innodb_needs_monitoring--;
    }

    block->page.reset_flush_observer();
    return block;
  }

  /* No free blocks found on the free list, we need to run a LRU scan to find a
  block. In meantime, we wake up simulated AIO threads that may have requests
  queued with IOREquest::DO_NOT_WAKE waiting for them to wake up. If one of
  threads that are requesting the new IOs waits for a new block to place the
  read IO for that block, this would deadlock. Waking up the simulated AIO
  threads may cause some blocks to be IO_FIX unfixed and become available to
  evict. */
  os_aio_simulated_wake_handler_threads();

  MONITOR_INC(MONITOR_LRU_GET_FREE_LOOPS);

  freed = false;
  os_rmb;
  if (buf_pool->try_LRU_scan || n_iterations > 0) {
    /* If no block was in the free list, search from the
    end of the LRU list and try to free a block there.
    If we are doing for the first time we'll scan only
    tail of the LRU list otherwise we scan the whole LRU
    list. */
    freed = buf_LRU_scan_and_free_block(buf_pool, n_iterations > 0);

    if (!freed && n_iterations == 0) {
      /* Tell other threads that there is no point
      in scanning the LRU list. This flag is set to
      true again when we flush a batch from this
      buffer pool. */
      buf_pool->try_LRU_scan = false;
      os_wmb;
    }
  }

  if (freed) {
    goto loop;
  }

  if (n_iterations > 20 && srv_buf_pool_old_size == srv_buf_pool_size) {
    ib::warn(ER_IB_MSG_134)
        << "Difficult to find free blocks in the buffer pool"
           " ("
        << n_iterations << " search iterations)! " << flush_failures
        << " failed attempts to"
           " flush a page! Consider increasing the buffer pool"
           " size. It is also possible that in your Unix version"
           " fsync is very slow, or completely frozen inside"
           " the OS kernel. Then upgrading to a newer version"
           " of your operating system may help. Look at the"
           " number of fsyncs in diagnostic info below."
           " Pending flushes (fsync) log: "
        << log_pending_flushes()
        << "; buffer pool: " << fil_n_pending_tablespace_flushes << ". "
        << os_n_file_reads << " OS file reads, " << os_n_file_writes
        << " OS file writes, " << os_n_fsyncs
        << " OS fsyncs. Starting InnoDB Monitor to print"
           " further diagnostics to the standard output.";
    if (!started_monitor) {
      started_monitor = true;
      srv_innodb_needs_monitoring++;
    }
  }

  /* If we have scanned the whole LRU and still are unable to
  find a free block then we should sleep here to let the
  page_cleaner do an LRU batch for us. */

  if (!srv_read_only_mode) {
    os_event_set(buf_flush_event);
  }

  if (n_iterations > 1) {
    MONITOR_INC(MONITOR_LRU_GET_FREE_WAITS);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }

  /* No free block was found: try to flush the LRU list.
  This call will flush one page from the LRU and put it on the
  free list. That means that the free block is up for grabs for
  all user threads.

  TODO: A more elegant way would have been to return the freed
  up block to the caller here but the code that deals with
  removing the block from page_hash and LRU_list is fairly
  involved (particularly in case of compressed pages). We
  can do that in a separate patch sometime in future. */

  if (!buf_flush_single_page_from_LRU(buf_pool)) {
    MONITOR_INC(MONITOR_LRU_SINGLE_FLUSH_FAILURE_COUNT);
    ++flush_failures;
  }

  srv_stats.buf_pool_wait_free.add(n_iterations, 1);

  n_iterations++;

  goto loop;
}
```

LRU 꼬리 스캔은 첫 바퀴에 100장까지만 본다.

`storage` / `innobase` / `buf` / `buf0lru.cc` L1094-L1154 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1094-L1154))

```cpp
// buf0lru.cc L1094-L1154
static bool buf_LRU_free_from_common_LRU_list(buf_pool_t *buf_pool,
                                              bool scan_all) {
  ut_ad(mutex_own(&buf_pool->LRU_list_mutex));

  bool freed{};
  ulint scanned{};

  for (buf_page_t *bpage = buf_pool->lru_scan_itr.start();
       bpage != nullptr && !freed &&
       (scan_all || scanned < BUF_LRU_SEARCH_SCAN_THRESHOLD);
       ++scanned, bpage = buf_pool->lru_scan_itr.get()) {
    ut_ad(mutex_own(&buf_pool->LRU_list_mutex));
    auto prev = UT_LIST_GET_PREV(LRU, bpage);
    auto block_mutex = buf_page_get_mutex(bpage);

    buf_pool->lru_scan_itr.set(prev);

    ut_ad(bpage->in_LRU_list);
    ut_ad(buf_page_in_file(bpage));

    const auto accessed = buf_page_is_accessed(bpage);

    if (bpage->was_stale()) {
      freed = buf_page_free_stale(buf_pool, bpage);
    } else {
      mutex_enter(block_mutex);

      if (buf_flush_ready_for_replace(bpage)) {
        freed = buf_LRU_free_page(bpage, true);
      }

      if (!freed) {
        mutex_exit(block_mutex);
      }
    }

    if (freed && accessed == std::chrono::steady_clock::time_point{}) {
      /* Keep track of pages that are evicted without
      ever being accessed. This gives us a measure of
      the effectiveness of readahead */
      ++buf_pool->stat.n_ra_pages_evicted;
    }

    ut_ad(!mutex_own(block_mutex));

    if (freed) {
      break;
    }
  }

  if (scanned) {
    MONITOR_INC_VALUE_CUMULATIVE(MONITOR_LRU_SEARCH_SCANNED,
                                 MONITOR_LRU_SEARCH_SCANNED_NUM_CALL,
                                 MONITOR_LRU_SEARCH_SCANNED_PER_CALL, scanned);
  }

  ut_ad(freed ? !mutex_own(&buf_pool->LRU_list_mutex)
              : mutex_own(&buf_pool->LRU_list_mutex));

  return (freed);
}
```

free list 에서 꺼내는 쪽이다.

`storage` / `innobase` / `buf` / `buf0lru.cc` L1205-L1248 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1205-L1248))

```cpp
// buf0lru.cc L1205-L1248
buf_block_t *buf_LRU_get_free_only(buf_pool_t *buf_pool) {
  buf_block_t *block;

  mutex_enter(&buf_pool->free_list_mutex);

  block = reinterpret_cast<buf_block_t *>(UT_LIST_GET_FIRST(buf_pool->free));

  while (block != nullptr) {
    ut_ad(block->page.in_free_list);
    ut_d(block->page.in_free_list = false);
    ut_ad(!block->page.in_flush_list);
    ut_ad(!block->page.in_LRU_list);
    ut_a(!buf_page_in_file(&block->page));
    UT_LIST_REMOVE(buf_pool->free, &block->page);
    mutex_exit(&buf_pool->free_list_mutex);

    if (!buf_get_withdraw_depth(buf_pool) ||
        !buf_block_will_withdrawn(buf_pool, block)) {
      /* found valid free block */
      /* No adaptive hash index entries may point to
      a free block. */
      block->ahi.assert_empty();

      buf_block_set_state(block, BUF_BLOCK_READY_FOR_USE);

      UNIV_MEM_ALLOC(block->frame, UNIV_PAGE_SIZE);

      ut_ad(buf_pool_from_block(block) == buf_pool);

      return (block);
    }

    /* This should be withdrawn */
    mutex_enter(&buf_pool->free_list_mutex);
    UT_LIST_ADD_LAST(buf_pool->withdraw, &block->page);
    ut_d(block->in_withdraw_list = true);

    block = reinterpret_cast<buf_block_t *>(UT_LIST_GET_FIRST(buf_pool->free));
  }

  mutex_exit(&buf_pool->free_list_mutex);

  return (block);
}
```

## 동작 흐름

```text
 L1321  loop:
 L1325    buf_LRU_get_free_only                 free list 머리에서 하나
 L1327      있으면 zip 초기화 후 반환            상태 BUF_BLOCK_READY_FOR_USE (L1228)
 L1347    os_aio_simulated_wake_handler_threads 멈춰 있는 AIO 를 깨워 io-fix 를 풀게 한다
 L1353    try_LRU_scan 이거나 두 번째 바퀴 이상
 L1359      buf_LRU_scan_and_free_block(scan_all = n_iterations > 0)
              unzip_LRU 가 있으면 압축 해제본부터 버린다 (L1163)
              buf_LRU_free_from_common_LRU_list  LRU 꼬리부터
                replace 가능하면 buf_LRU_free_page -> free list 로
 L1361      첫 바퀴에 실패하면 try_LRU_scan = false  (다른 스레드는 스캔을 건너뛴다)
 L1371    freed 면 goto loop
 L1375    20 바퀴가 넘으면 경고, InnoDB 모니터 켬
 L1405    buf_flush_event 를 set                페이지 클리너에게 LRU 배치를 재촉
 L1408    n_iterations > 1, 곧 셋째 바퀴부터 10ms sleep
 L1424    buf_flush_single_page_from_LRU        꼬리의 dirty 한 장을 이 스레드가 쓴다
 L1429    Innodb_buffer_pool_wait_free += n_iterations
 L1431    n_iterations++
 L1433    goto loop
```

바퀴별로 달라지는 것은 스캔의 깊이와 쉬는지 여부다.

```text
 바퀴(n_iterations)별 차이. free list 는 매 바퀴 먼저 본다

 0     LRU 스캔은 try_LRU_scan 일 때만, 꼬리에서 100장까지. sleep 없음
 1     LRU 스캔을 항상, 끝까지 (scan_all). sleep 없음
 2+    위와 같고 10ms sleep
 21+   위와 같고 경고와 InnoDB 모니터
 모든 바퀴에서 실패하면 buf_flush_single_page_from_LRU 로 한 장을 쓴다

 100 = BUF_LRU_SEARCH_SCAN_THRESHOLD (L86)
```

LRU 스캔이 무엇을 풀 수 있는지는 블록 상태로 정해진다. dirty 블록은 스캔이 풀지 않고, 한 장 플러시 경로나 페이지 클리너의 LRU 배치가 먼저 써야 한다.

```text
 LRU 꼬리 블록 하나의 판정 (buf_LRU_free_from_common_LRU_list L1094)

 L1116  stale                              buf_page_free_stale 로 바로 치운다
 L1121  buf_flush_ready_for_replace        fix 가 없고 (buf0flu.cc L470) dirty 가 아니어야 (L477)
                                           stale 블록은 dirty 여도 참 (L474)
 L1122    buf_LRU_free_page(bpage, true)   dirty 면 false (L1772-L1778)
            성공: page_hash 와 LRU 에서 빼고 freed_page_clock++ (L2104), free list 로
 L1130  접근 기록 없이 풀렸으면 n_ra_pages_evicted++   read-ahead 가 헛읽은 페이지
```

## 결과가 쓰이는 곳

```text
 BUF_BLOCK_READY_FOR_USE 블록
      --> [07] buf_page_init_for_read 가 page hash 와 LRU 에 올린다
      --> buf_page_create (새 페이지 할당, buf0buf.cc L5098) 도 같은 함수를 쓴다
 freed_page_clock
      --> 축출이 한 번이라도 있었는지, 그리고 얼마나 있었는지를 [09] 가 본다
 Innodb_buffer_pool_wait_free
      --> 사용자 스레드가 빈 블록을 기다린 정도. 크면 페이지 클리너가 못 따라가는 중이다
```

## 다루지 않는 것

`buf_LRU_check_size_of_non_data_objects`(잠금 표와 AHI 가 버퍼 풀을 너무 먹을 때의 경고), `buf_flush_single_page_from_LRU` 의 쓰기 과정([페이지 플러시, doublewrite, 체크포인트](../../flush-checkpoint/README.md)), unzip_LRU 에서 압축 해제본만 버리는 규칙, 버퍼 풀 축소 때의 withdraw 목록은 이 함수의 곁가지라 요약만 했다.
