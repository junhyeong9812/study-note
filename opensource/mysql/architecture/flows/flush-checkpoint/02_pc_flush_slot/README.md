# pc_flush_slot

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**슬롯 하나, 곧 버퍼 풀 인스턴스 하나의 flush 를 맡는다.** 코디네이터와 워커가 같은 함수를 부르고, mutex 아래에서 `REQUESTED` 슬롯을 하나 집어 `FLUSHING` 으로 바꾼 뒤 mutex 를 놓고 일한다. 일은 두 배치를 차례로 도는 것이다. 먼저 LRU 꼬리를 훑어 clean 페이지는 free list 로 돌려보내고 dirty 페이지는 쓰고, 그다음 요청이 있으면 flush list 꼬리부터 쓴다. 앞의 것은 빈 블록을, 뒤의 것은 checkpoint 전진을 위한 것이다.

## 위치

`storage` / `innobase` / `buf` / `buf0flu.cc` L2627-L2717 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L2627-L2717))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0flu.cc` L2627-L2717 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L2627-L2717))

```cpp
// buf0flu.cc L2627-L2717
static ulint pc_flush_slot(void) {
  std::chrono::steady_clock::duration lru_time;
  std::chrono::steady_clock::duration flush_list_time{};
  int lru_pass = 0;
  int list_pass = 0;

  mutex_enter(&page_cleaner->mutex);

  if (page_cleaner->n_slots_requested > 0) {
    page_cleaner_slot_t *slot = nullptr;
    ulint i;

    for (i = 0; i < page_cleaner->n_slots; i++) {
      slot = &page_cleaner->slots[i];

      if (slot->state == PAGE_CLEANER_STATE_REQUESTED) {
        break;
      }
    }

    /* slot should be found because
    page_cleaner->n_slots_requested > 0 */
    ut_a(i < page_cleaner->n_slots);

    buf_pool_t *buf_pool = buf_pool_from_array(i);

    page_cleaner->n_slots_requested--;
    page_cleaner->n_slots_flushing++;
    slot->state = PAGE_CLEANER_STATE_FLUSHING;

    if (page_cleaner->n_slots_requested == 0) {
      os_event_reset(page_cleaner->is_requested);
    }

    if (!page_cleaner->is_running) {
      slot->n_flushed_lru = 0;
      slot->n_flushed_list = 0;
    } else {
      mutex_exit(&page_cleaner->mutex);

      const auto lru_start = std::chrono::steady_clock::now();

      /* Flush pages from end of LRU if required */
      slot->n_flushed_lru = buf_flush_LRU_list(buf_pool);

      lru_time = std::chrono::steady_clock::now() - lru_start;
      lru_pass = 1;

      if (!page_cleaner->is_running) {
        slot->n_flushed_list = 0;
      } else {
        /* Flush pages from flush_list if required */
        if (page_cleaner->requested) {
          const auto flush_list_start = std::chrono::steady_clock::now();

          slot->succeeded_list = buf_flush_do_batch(
              buf_pool, BUF_FLUSH_LIST, slot->n_pages_requested,
              page_cleaner->lsn_limit, &slot->n_flushed_list);

          flush_list_time = std::chrono::steady_clock::now() - flush_list_start;
          list_pass = 1;
        } else {
          slot->n_flushed_list = 0;
          slot->succeeded_list = true;
        }
      }
      mutex_enter(&page_cleaner->mutex);
    }
    page_cleaner->n_slots_flushing--;
    page_cleaner->n_slots_finished++;
    slot->state = PAGE_CLEANER_STATE_FINISHED;

    slot->flush_lru_time +=
        std::chrono::duration_cast<std::chrono::milliseconds>(lru_time);
    slot->flush_list_time +=
        std::chrono::duration_cast<std::chrono::milliseconds>(flush_list_time);
    slot->flush_lru_pass += lru_pass;
    slot->flush_list_pass += list_pass;

    if (page_cleaner->n_slots_requested == 0 &&
        page_cleaner->n_slots_flushing == 0) {
      os_event_set(page_cleaner->is_finished);
    }
  }

  ulint ret = page_cleaner->n_slots_requested;

  mutex_exit(&page_cleaner->mutex);

  return (ret);
}
```

LRU 배치의 깊이는 `innodb_lru_scan_depth` 로 정한다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L1957-L1981 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1957-L1981))

```cpp
// buf0flu.cc L1957-L1981
static ulint buf_flush_LRU_list(buf_pool_t *buf_pool) {
  ulint scan_depth, withdraw_depth;
  ulint n_flushed = 0;

  ut_ad(buf_pool);

  /* srv_LRU_scan_depth can be arbitrarily large value.
  We cap it with current LRU size. */
  scan_depth = UT_LIST_GET_LEN(buf_pool->LRU);
  withdraw_depth = buf_get_withdraw_depth(buf_pool);

  if (withdraw_depth > srv_LRU_scan_depth) {
    scan_depth = std::min(withdraw_depth, scan_depth);
  } else {
    scan_depth = std::min(static_cast<ulint>(srv_LRU_scan_depth), scan_depth);
  }

  /* Currently one of page_cleaners is the only thread
  that can trigger an LRU flush at the same time.
  So, it is not possible that a batch triggered during
  last iteration is still running, */
  buf_flush_do_batch(buf_pool, BUF_FLUSH_LRU, scan_depth, 0, &n_flushed);

  return (n_flushed);
}
```

LRU 꼬리 한 장마다 세 갈래다. 교체 가능하면 free 로, flush 가능하면 쓰기, 둘 다 아니면 건너뛴다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L1517-L1560 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1517-L1560))

```cpp
// buf0flu.cc L1517-L1560
  for (bpage = UT_LIST_GET_LAST(buf_pool->LRU);
       bpage != nullptr && count + evict_count < max &&
       free_len < srv_LRU_scan_depth + withdraw_depth &&
       lru_len > BUF_LRU_MIN_LEN;
       ++scanned, bpage = buf_pool->lru_hp.get()) {
    ut_ad(mutex_own(&buf_pool->LRU_list_mutex));

    auto prev = UT_LIST_GET_PREV(LRU, bpage);
    buf_pool->lru_hp.set(prev);

    auto block_mutex = buf_page_get_mutex(bpage);

    if (bpage->was_stale()) {
      if (buf_page_free_stale(buf_pool, bpage)) {
        ++evict_count;
        mutex_enter(&buf_pool->LRU_list_mutex);
      }
    } else {
      auto acquired = mutex_enter_nowait(block_mutex) == 0;

      if (acquired && buf_flush_ready_for_replace(bpage)) {
        /* block is ready for eviction i.e., it is
        clean and is not IO-fixed or buffer fixed. */
        if (buf_LRU_free_page(bpage, true)) {
          ++evict_count;
          mutex_enter(&buf_pool->LRU_list_mutex);
        } else {
          mutex_exit(block_mutex);
        }
      } else if (acquired && buf_flush_ready_for_flush(bpage, BUF_FLUSH_LRU)) {
        /* Block is ready for flush. Dispatch an IO request. The IO helper
        thread will put it on the free list in the IO completion routine. */
        mutex_exit(block_mutex);
        buf_flush_page_and_try_neighbors(bpage, BUF_FLUSH_LRU, max, &count);
      } else if (!acquired) {
        ut_ad(buf_pool->lru_hp.is_hp(prev));
      } else {
        /* Can't evict or dispatch this block. Go to previous. */
        mutex_exit(block_mutex);
        ut_ad(buf_pool->lru_hp.is_hp(prev));
      }
    }

    ut_ad(!mutex_own(block_mutex));
```

## 동작 흐름

```text
 L2633  page_cleaner->mutex
 L2635  n_slots_requested > 0 이면
 L2639    첫 REQUESTED 슬롯 i 를 찾는다
 L2651    buf_pool = buf_pool_from_array(i)          슬롯 번호 = 버퍼 풀 번호
 L2653    requested--, flushing++, L2655 state = FLUSHING
 L2658    requested 가 0 이면 is_requested reset      다른 워커가 헛돌지 않게
 L2665    mutex 를 놓는다
 L2670    n_flushed_lru = buf_flush_LRU_list(buf_pool)
            L1971  scan_depth = min(lru_scan_depth, LRU 길이)  (withdraw 중이면 더 깊게)
            L1978  buf_flush_do_batch(BUF_FLUSH_LRU, scan_depth, 0)
 L2679    page_cleaner->requested (min_n > 0) 면
 L2682      succeeded_list = [03] buf_flush_do_batch(BUF_FLUSH_LIST, n_pages_requested, lsn_limit)
 L2693    mutex 를 다시 잡고
 L2695    flushing--, L2696 finished++, L2697 state = FINISHED
 L2706    requested == 0 && flushing == 0 이면 is_finished set
 L2716  return n_slots_requested                     0 이 될 때까지 호출한 쪽이 반복
```

```text
 슬롯 상태 (page_cleaner_slot_t.state)

   NONE --pc_request--> REQUESTED --pc_flush_slot--> FLUSHING --> FINISHED --pc_wait_finished--> NONE
                         L2612                        L2655        L2697       L2748
```

```text
 한 버퍼 풀 인스턴스의 두 리스트와 두 배치

 LRU list (접근 순서, 꼬리가 오래 안 쓴 것)
   head ... [clean] [dirty] [clean] [fixed] [dirty]  tail
                                                ^ 여기서부터 scan_depth 장
   clean, 고정 없음 -> buf_LRU_free_page -> free list        (L1537-L1541)
   dirty, flush 가능 -> buf_flush_page_and_try_neighbors     (L1546-L1550)
   목적: free list 가 lru_scan_depth 만큼 차게 (L1519)

 flush list (처음 더럽혀진 순서, 꼬리 쪽이 oldest 가 작다. 순서는 order_lag 안에서 느슨하다)
   head [520] [500] [510] [300] [180] [100]  tail
                                       ^ 여기서부터 oldest < lsn_limit 이고 n 장까지
   목적: 가장 오래된 변경을 디스크로 보내 checkpoint 를 앞으로

 dirty 페이지는 LRU 에도 flush list 에도 있다. 어느 쪽 배치가 쓰든 IO 완료에서
 flush list 에서 빠진다 (buf_flush_write_complete, buf0flu.cc L668)
```

## 결과가 쓰이는 곳

```text
 slot->n_flushed_lru, n_flushed_list, succeeded_list
      --> [01] pc_wait_finished 가 합산하고, 모두 성공했는지 본다
      --> 코디네이터가 다음 바퀴 page_recommendation 의 last_pages 로 쓴다

 free list 로 돌아간 블록
      --> buf_LRU_get_free_block 이 가져간다   [버퍼 풀 페이지 획득]
```

## 다루지 않는 것

`unzip_LRU` 배치(`buf_free_from_unzip_LRU_list_batch`), stale 페이지 해제(`buf_page_free_stale`), 해저드 포인터(`lru_hp`, `flush_hp`)가 O(n^2) 재탐색을 막는 방식, 시간 통계는 요약만 했다.
