# buf_flush_do_batch

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**배치 하나를 여닫는 틀이다.** 같은 종류(LRU 또는 LIST)의 배치가 이미 돌고 있으면 시작하지 않고 false 를 돌려준다. 가운데 `buf_flush_batch` 가 종류별 스캔을 부르고, 끝의 `buf_flush_end` 가 doublewrite 에 쌓인 나머지를 강제로 내보낸다. flush list 배치의 스캔 조건 한 줄(`count < min_n && oldest < lsn_limit`)이 sync flush 와 adaptive flush 를 같은 코드로 처리한다.

## 위치

`storage` / `innobase` / `buf` / `buf0flu.cc` L1787-L1808 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1787-L1808))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0flu.cc` L1787-L1808 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1787-L1808))

```cpp
// buf0flu.cc L1787-L1808
bool buf_flush_do_batch(buf_pool_t *buf_pool, buf_flush_t type, ulint min_n,
                        lsn_t lsn_limit, ulint *n_processed) {
  ut_ad(type == BUF_FLUSH_LRU || type == BUF_FLUSH_LIST);

  if (n_processed != nullptr) {
    *n_processed = 0;
  }

  if (!buf_flush_start(buf_pool, type)) {
    return (false);
  }

  ulint page_count = buf_flush_batch(buf_pool, type, min_n, lsn_limit);

  buf_flush_end(buf_pool, type);

  if (n_processed != nullptr) {
    *n_processed = page_count;
  }

  return (true);
}
```

시작과 끝이다. 끝에서 doublewrite 큐를 비우거나, doublewrite 가 꺼져 있으면 데이터 파일을 sync 한다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L1741-L1775 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1741-L1775))

```cpp
// buf0flu.cc L1741-L1775
static bool buf_flush_start(buf_pool_t *buf_pool, buf_flush_t flush_type) {
  ut_ad(flush_type == BUF_FLUSH_LRU || flush_type == BUF_FLUSH_LIST);
  bool started = false;
  buf_pool->change_flush_state(flush_type, [&]() {
    /* Can't start a new batch of the same type as one already running -
    various synchronization mechanisms/counters would not work. */
    if (!buf_pool->is_flushing(flush_type)) {
      buf_pool->init_flush[flush_type] = true;
      started = true;
    }
  });
  return started;
}

/** End a buffer flush batch for LRU or flush list
@param[in]      buf_pool        buffer pool instance
@param[in]      flush_type      BUF_FLUSH_LRU or BUF_FLUSH_LIST */
static void buf_flush_end(buf_pool_t *buf_pool, buf_flush_t flush_type) {
  buf_pool->change_flush_state(flush_type, [&]() {
    buf_pool->try_LRU_scan = true;
    buf_pool->init_flush[flush_type] = false;
  });

  if (!srv_read_only_mode) {
    if (dblwr::is_enabled()) {
      dblwr::force_flush(flush_type, buf_pool_index(buf_pool));
    } else {
      buf_flush_sync_datafiles();
    }
  } else {
    os_aio_simulated_wake_handler_threads();
  }
}

void buf_flush_await_no_flushing(buf_pool_t *buf_pool, buf_flush_t flush_type) {
```

종류별로 가른다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L1690-L1730 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1690-L1730))

```cpp
// buf0flu.cc L1690-L1730
static ulint buf_flush_batch(buf_pool_t *buf_pool, buf_flush_t flush_type,
                             ulint min_n, lsn_t lsn_limit) {
  ut_ad(flush_type == BUF_FLUSH_LRU || flush_type == BUF_FLUSH_LIST);

#ifdef UNIV_DEBUG
  {
    dict_sync_check check(true);

    ut_ad(flush_type != BUF_FLUSH_LIST || !sync_check_iterate(check));
  }
#endif /* UNIV_DEBUG */

  ulint count = 0;

  /* Note: The buffer pool mutexes is released and reacquired within
  the flush functions. */
  switch (flush_type) {
    case BUF_FLUSH_LRU:
      mutex_enter(&buf_pool->LRU_list_mutex);
      count = buf_do_LRU_batch(buf_pool, min_n);
      mutex_exit(&buf_pool->LRU_list_mutex);
      break;
    case BUF_FLUSH_LIST:
      count = buf_do_flush_list_batch(buf_pool, min_n, lsn_limit);
      break;
    default:
      ut_error;
  }

  DBUG_PRINT("ib_buf", ("flush %u completed, %u pages", unsigned(flush_type),
                        unsigned(count)));

  return (count);
}

/** Gather the aggregated stats for both flush list and LRU list flushing.
 @param page_count_flush        number of pages flushed from the end of the
 flush_list
 @param page_count_LRU  number of pages flushed from the end of the LRU list
 */
static void buf_flush_stats(ulint page_count_flush, ulint page_count_LRU) {
```

flush list 배치다. 꼬리에서 머리 쪽으로 간다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L1620-L1672 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1620-L1672))

```cpp
// buf0flu.cc L1620-L1672
static ulint buf_do_flush_list_batch(buf_pool_t *buf_pool, ulint min_n,
                                     lsn_t lsn_limit) {
  ulint count = 0;
  ulint scanned = 0;

  /* Start from the end of the list looking for a suitable
  block to be flushed. */
  buf_flush_list_mutex_enter(buf_pool);
  ulint len = UT_LIST_GET_LEN(buf_pool->flush_list);

  /* In order not to degenerate this scan to O(n*n) we attempt
  to preserve pointer of previous block in the flush list. To do
  so we declare it a hazard pointer. Any thread working on the
  flush list must check the hazard pointer and if it is removing
  the same block then it must reset it. */
  for (buf_page_t *bpage = UT_LIST_GET_LAST(buf_pool->flush_list);
       count < min_n && bpage != nullptr && len > 0 &&
       bpage->get_oldest_lsn() < lsn_limit;
       bpage = buf_pool->flush_hp.get(), ++scanned) {
    buf_page_t *prev;

    ut_a(bpage->is_dirty());
    ut_ad(bpage->in_flush_list);

    prev = UT_LIST_GET_PREV(list, bpage);
    buf_pool->flush_hp.set(prev);

#ifdef UNIV_DEBUG
    bool flushed =
#endif /* UNIV_DEBUG */
        buf_flush_page_and_try_neighbors(bpage, BUF_FLUSH_LIST, min_n, &count);

    ut_ad(flushed || buf_pool->flush_hp.is_hp(prev));

    --len;
  }

  buf_pool->flush_hp.set(nullptr);
  buf_flush_list_mutex_exit(buf_pool);

  if (scanned) {
    MONITOR_INC_VALUE_CUMULATIVE(MONITOR_FLUSH_BATCH_SCANNED,
                                 MONITOR_FLUSH_BATCH_SCANNED_NUM_CALL,
                                 MONITOR_FLUSH_BATCH_SCANNED_PER_CALL, scanned);
  }

  if (count) {
    MONITOR_INC_VALUE_CUMULATIVE(MONITOR_FLUSH_BATCH_TOTAL_PAGE,
                                 MONITOR_FLUSH_BATCH_COUNT,
                                 MONITOR_FLUSH_BATCH_PAGES, count);
  }

  return (count);
```

## 동작 흐름

```text
 L1792  n_processed = 0
 L1795  buf_flush_start(type)              is_flushing(type) 면 false  (L1747-L1750)
                                           = init_flush[type] 이거나 n_flush[type] > 0 (buf0buf.h L2547)
                                           앞 배치의 쓰기 IO 가 다 끝나지 않아도 새 배치는 못 연다
          실패 -> return false             ([02] 의 succeeded_list = false)
 L1799  page_count = buf_flush_batch(type, min_n, lsn_limit)
          LRU   L1708  LRU_list_mutex 아래 buf_do_LRU_batch(min_n)
          LIST  L1713  buf_do_flush_list_batch(min_n, lsn_limit)
                  L1627  flush_list_mutex
                  L1635  bpage = LAST(flush_list)
                  L1636  count < min_n && bpage && len > 0 && oldest < lsn_limit 인 동안
                  L1645    flush_hp = prev                       해저드 포인터 (주석 L1630-L1634)
                  L1650    buf_flush_page_and_try_neighbors      mutex 를 놓고 쓰고 다시 잡는다
                  L1638    다음 = flush_hp.get()
 L1801  buf_flush_end(type)
          L1760  init_flush[type] = false, try_LRU_scan = true
          L1765  dblwr 켜짐   dblwr::force_flush(type, pool)   배치에 남은 페이지를 지금 쓴다
          L1768  dblwr 꺼짐   buf_flush_sync_datafiles
 L1804  n_processed = page_count, return true
```

```text
 min_n 과 lsn_limit 의 조합이 곧 flush 의 종류다

 min_n                 lsn_limit                 caller
 page_recommendation   LSN_MAX                   adaptive, 1초 주기
 page_recommendation   log_sync_flush_lsn + a    sync flush, redo 부족
 ULINT_MAX             LSN_MAX                   복구 중, 종료 때 전체 flush ([01] L2931, L3190)
 lru_scan_depth        0                         LRU 배치 (lsn_limit 무시)

 스캔은 둘 중 먼저 걸리는 쪽에서 멈춘다
   n 장을 채웠거나, 꼬리 페이지의 oldest 가 lsn_limit 이상이거나
```

```text
 flush list 배치가 꼬리에서 무엇을 남기는가 (lsn_limit = 400)

 head [520] [500] [510] [300] [180] [100]  tail
                         |     |     |
                         |     |     +-- 1 번째로 쓴다
                         |     +-------- 2 번째
                         +-------------- 3 번째
      [510] 에서 멈춤 (510 >= 400)

 쓰기를 낸 순간이 아니라 IO 가 끝나야 flush list 에서 빠진다
 그때까지 이 페이지들의 oldest 가 checkpoint 를 붙잡는다
```

## 결과가 쓰이는 곳

```text
 반환값 true / false, n_processed
      --> [02] slot->succeeded_list, n_flushed_list
      --> buf_flush_lists 는 false 인 인스턴스를 건너뛰고 success = false (L1833-L1847)

 force_flush
      --> [07] 의 Double_write::force_flush -> flush_to_disk -> write_pages
```

## 다루지 않는 것

`buf_do_LRU_batch` 안의 `unzip_LRU` 분기, 이웃 페이지 flush(`buf_flush_try_neighbors` 와 `innodb_flush_neighbors`), `buf_flush_lists` 와 `buf_flush_sync_all_buf_pools` 의 호출처는 요약만 했다.
