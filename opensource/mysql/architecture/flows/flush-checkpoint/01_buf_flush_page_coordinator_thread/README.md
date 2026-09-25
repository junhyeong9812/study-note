# buf_flush_page_coordinator_thread

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**page cleaner 의 지휘자다.** 워커 스레드를 만들고, 1초 박자로 "이번에 몇 장을, 어느 lsn 아래까지 쓸지"를 정해 슬롯에 적은 뒤 워커를 깨우고, 자신도 슬롯을 하나씩 처리하고, 모두 끝나기를 기다린다. 모드는 둘이다. 평소에는 adaptive flushing 이 쓸 양을 정하고(`lsn_limit = LSN_MAX`), redo 공간이 모자라 checkpointer 가 동기 flush 를 요청하면 `log_sync_flush_lsn` 이 돌려준 lsn 까지 쓰는 sync flush 로 바뀐다.

## 위치

`storage` / `innobase` / `buf` / `buf0flu.cc` L2875-L3295 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L2875-L3295))

## 실제 코드

시작부다. 워커를 만든다. 0 번 워커 자리는 코디네이터 자신이다(L2896-L2897 주석).

`storage` / `innobase` / `buf` / `buf0flu.cc` L2875-L2903 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L2875-L2903))

```cpp
// buf0flu.cc L2875-L2903
static void buf_flush_page_coordinator_thread() {
  auto loop_start_time = std::chrono::steady_clock::now();
  ulint n_flushed = 0;
  ulint last_activity = srv_get_activity_count();
  ulint last_pages = 0;

  THD *thd = create_internal_thd();

#ifdef UNIV_LINUX
  /* linux might be able to set different setting for each thread.
  worth to try to set high priority for page cleaner threads */
  if (buf_flush_page_cleaner_set_priority(buf_flush_page_cleaner_priority)) {
    ib::info(ER_IB_MSG_126) << "page_cleaner coordinator priority: "
                            << buf_flush_page_cleaner_priority;
  } else {
    ib::info(ER_IB_MSG_127) << "If the mysqld execution user is authorized,"
                               " page cleaner thread priority can be changed."
                               " See the man page of setpriority().";
  }
#endif /* UNIV_LINUX */

  /* We start from 1 because the coordinator thread is part of the
  same set */
  for (size_t i = 1; i < srv_threads.m_page_cleaner_workers_n; ++i) {
    srv_threads.m_page_cleaner_workers[i] = os_thread_create(
        page_flush_thread_key, i, buf_flush_page_cleaner_thread);

    srv_threads.m_page_cleaner_workers[i].start();
  }
```

본 루프의 앞쪽이다. 잘지 말지, sync flush 인지 정하고, 1초가 지났으면 redo 를 먼저 내려 둔다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L2945-L2984 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L2945-L2984))

```cpp
// buf0flu.cc L2945-L2984
  os_event_wait(buf_flush_event);

  ulint ret_sleep = 0;
  ulint n_evicted = 0;
  ulint n_flushed_last = 0;
  ulint warn_interval = 1;
  ulint warn_count = 0;
  bool is_sync_flush = false;
  bool was_server_active = true;
  int64_t sig_count = os_event_reset(buf_flush_event);

  while (srv_shutdown_state.load() < SRV_SHUTDOWN_CLEANUP) {
    /* We consider server active if either we have just discovered a first
    activity after a period of inactive server, or we are after the period
    of active server in which case, it could be just the beginning of the
    next period, so there is no reason to consider it idle yet.
    The withdrawing blocks process when shrinking the buffer pool always
    needs the page_cleaner activity. So, we consider server is active
    during the withdrawing blocks process also. */

    bool is_withdrawing = false;
    for (ulint i = 0; i < srv_buf_pool_instances; i++) {
      buf_pool_t *buf_pool = buf_pool_from_array(i);
      if (buf_get_withdraw_depth(buf_pool) > 0) {
        is_withdrawing = true;
        break;
      }
    }

    const bool is_server_active = is_withdrawing || was_server_active ||
                                  srv_check_activity(last_activity);

    /* The page_cleaner skips sleep if the server is
    idle and there are no pending IOs in the buffer pool
    and there is work to do. */
    if ((is_server_active || buf_get_n_pending_read_ios() || n_flushed == 0) &&
        !is_sync_flush) {
      ret_sleep = pc_sleep_if_needed(loop_start_time + std::chrono::seconds{1},
                                     sig_count);

```

`storage` / `innobase` / `buf` / `buf0flu.cc` L3031-L3060 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L3031-L3060))

```cpp
// buf0flu.cc L3031-L3060

    lsn_t lsn_limit;
    if (srv_flush_sync && !srv_read_only_mode) {
      /* lsn_limit!=0 means there are requests. needs to check the lsn. */
      lsn_limit = log_sync_flush_lsn(*log_sys);
      if (lsn_limit != 0) {
        /* Avoid aggressive sync flush beyond limit when redo is disabled. */
        if (mtr_t::s_logging.is_enabled()) {
          lsn_limit += Adaptive_flush::lsn_avg_rate * buf_flush_lsn_scan_factor;
        }
        is_sync_flush = true;
      } else {
        /* Stop the sync flush. */
        is_sync_flush = false;
      }
    } else {
      is_sync_flush = false;
      lsn_limit = LSN_MAX;
    }

    if (!srv_read_only_mode && mtr_t::s_logging.is_enabled() &&
        ret_sleep == OS_SYNC_TIME_EXCEEDED) {
      /* For smooth page flushing along with WAL,
      flushes log as much as possible. */
      log_sys->recent_written.advance_tail();
      auto wait_stats = log_write_up_to(
          *log_sys, log_buffer_ready_for_write_lsn(*log_sys), true);
      MONITOR_INC_WAIT_STATS_EX(MONITOR_ON_LOG_, _PAGE_WRITTEN, wait_stats);
    }

```

본 루프의 뒤쪽이다. 요청하고, 처리하고, 기다린다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L3061-L3118 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L3061-L3118))

```cpp
// buf0flu.cc L3061-L3118
    if (is_sync_flush || is_server_active) {
      ulint n_to_flush;

      /* Estimate pages from flush_list to be flushed */
      if (is_sync_flush) {
        ut_a(lsn_limit > 0);
        ut_a(lsn_limit < LSN_MAX);
        n_to_flush =
            Adaptive_flush::page_recommendation(last_pages, true, lsn_limit);
        last_pages = 0;
        /* Flush n_to_flush pages or stop if you reach lsn_limit earlier.
        This is because in sync-flush mode we want finer granularity of
        flushes through all BP instances. */
      } else if (ret_sleep == OS_SYNC_TIME_EXCEEDED) {
        n_to_flush =
            Adaptive_flush::page_recommendation(last_pages, false, LSN_MAX);
        lsn_limit = LSN_MAX;
        last_pages = 0;
      } else {
        n_to_flush = 0;
        lsn_limit = 0;
      }

      /* Request flushing for threads */
      pc_request(n_to_flush, lsn_limit);

      const auto flush_start = std::chrono::steady_clock::now();

      /* Coordinator also treats requests */
      while (pc_flush_slot() > 0) {
        /* No op */
      }

      /* only coordinator is using these counters,
      so no need to protect by lock. */
      page_cleaner->flush_time +=
          std::chrono::duration_cast<std::chrono::milliseconds>(
              std::chrono::steady_clock::now() - flush_start);
      page_cleaner->flush_pass++;

      /* Wait for all slots to be finished */
      ulint n_flushed_lru = 0;
      ulint n_flushed_list = 0;

      pc_wait_finished(&n_flushed_lru, &n_flushed_list);

      if (n_flushed_list > 0 || n_flushed_lru > 0) {
        buf_flush_stats(n_flushed_list, n_flushed_lru);
      }

      if (n_to_flush != 0) {
        last_pages = n_flushed_list;
      }

      n_evicted += n_flushed_lru;
      n_flushed_last += n_flushed_list;

      n_flushed = n_flushed_lru + n_flushed_list;
```

`storage` / `innobase` / `buf` / `buf0flu.cc` L3137-L3155 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L3137-L3155))

```cpp
// buf0flu.cc L3137-L3155
    } else if (ret_sleep == OS_SYNC_TIME_EXCEEDED && srv_idle_flush_pct) {
      /* no activity, slept enough */
      buf_flush_lists(PCT_IO(srv_idle_flush_pct), LSN_MAX, &n_flushed);

      n_flushed_last += n_flushed;

      if (n_flushed) {
        MONITOR_INC_VALUE_CUMULATIVE(MONITOR_FLUSH_BACKGROUND_TOTAL_PAGE,
                                     MONITOR_FLUSH_BACKGROUND_COUNT,
                                     MONITOR_FLUSH_BACKGROUND_PAGES, n_flushed);
      }

    } else {
      /* no activity, but woken up by event */
      n_flushed = 0;
    }

    ut_d(buf_flush_page_cleaner_disabled_loop());
  }
```

요청은 슬롯마다 상태를 `REQUESTED` 로 바꾸고 워커를 깨우는 것이다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L2580-L2622 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L2580-L2622))

```cpp
// buf0flu.cc L2580-L2622
static void pc_request(ulint min_n, lsn_t lsn_limit) {
  if (min_n != ULINT_MAX) {
    /* Ensure that flushing is spread evenly amongst the
    buffer pool instances. When min_n is ULINT_MAX
    we need to flush everything up to the lsn limit
    so no limit here. */
    min_n = ut::div_ceil(min_n, ulint{srv_buf_pool_instances});
  }

  mutex_enter(&page_cleaner->mutex);

  ut_ad(page_cleaner->n_slots_requested == 0);
  ut_ad(page_cleaner->n_slots_flushing == 0);
  ut_ad(page_cleaner->n_slots_finished == 0);

  page_cleaner->requested = (min_n > 0);
  page_cleaner->lsn_limit = lsn_limit;

  for (ulint i = 0; i < page_cleaner->n_slots; i++) {
    page_cleaner_slot_t *slot = &page_cleaner->slots[i];

    ut_ad(slot->state == PAGE_CLEANER_STATE_NONE);

    if (min_n == ULINT_MAX) {
      slot->n_pages_requested = ULINT_MAX;
    } else if (min_n == 0) {
      slot->n_pages_requested = 0;
    }

    /* slot->n_pages_requested was already set by
    Adaptive_flush::page_recommendation() */

    slot->state = PAGE_CLEANER_STATE_REQUESTED;
  }

  page_cleaner->n_slots_requested = page_cleaner->n_slots;
  page_cleaner->n_slots_flushing = 0;
  page_cleaner->n_slots_finished = 0;

  os_event_set(page_cleaner->is_requested);

  mutex_exit(&page_cleaner->mutex);
}
```

워커는 깨어나 슬롯을 하나 처리하는 것뿐이다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L3298-L3319 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L3298-L3319))

```cpp
// buf0flu.cc L3298-L3319
static void buf_flush_page_cleaner_thread() {
#ifdef UNIV_LINUX
  /* linux might be able to set different setting for each thread
  worth to try to set high priority for page cleaner threads */
  if (buf_flush_page_cleaner_set_priority(buf_flush_page_cleaner_priority)) {
    ib::info(ER_IB_MSG_129)
        << "page_cleaner worker priority: " << buf_flush_page_cleaner_priority;
  }
#endif /* UNIV_LINUX */

  for (;;) {
    os_event_wait(page_cleaner->is_requested);

    ut_d(buf_flush_page_cleaner_disabled_loop());

    if (!page_cleaner->is_running) {
      break;
    }

    pc_flush_slot();
  }
}
```

## 동작 흐름

```text
 L2898  워커 i = 1 .. m_page_cleaner_workers_n - 1 을 만든다  (buf_flush_page_cleaner_thread)
 L2905  복구 중이면 recv_sys->flush_start 에 맞춰 LRU 또는 전체 flush (L2905-L2943)
 L2945  buf_flush_event 를 기다린다 (시작 신호)
 L2956  while (shutdown < CLEANUP)
 L2974    is_server_active = withdraw 중 || 직전 활동 || 새 활동
 L2980    active, 읽기 IO 대기, 지난번 0 장 중 하나이고 sync 가 아니면
 L2982      pc_sleep_if_needed(1초 경계, sig_count)   buf_flush_event 로 일찍 깨어날 수 있다
 L3033    srv_flush_sync 면
 L3035      lsn_limit = log_sync_flush_lsn             0 이 아니면 L3041 is_sync_flush = true
 L3039      lsn_avg_rate * scan_factor 만큼 더 잡는다
 L3052    1초가 지났으면
 L3055      recent_written.advance_tail
 L3056      log_write_up_to(ready_for_write_lsn, true)  "flushes log as much as possible"
 L3061    sync 이거나 active 면
 L3068      sync            n = page_recommendation(last, true, lsn_limit)
 L3075      1초 지남        n = page_recommendation(last, false, LSN_MAX)
 L3080      그 밖           n = 0, lsn_limit = 0      LRU 만 돈다
 L3085      pc_request(n, lsn_limit)
 L3090      while (pc_flush_slot() > 0)               코디네이터도 슬롯을 가져간다
 L3105      pc_wait_finished                          is_finished 이벤트
 L3137    idle 이고 1초 지났으면 buf_flush_lists(idle_flush_pct)
```

```text
 코디네이터와 워커 (슬롯 = 버퍼 풀 인스턴스, n_slots = srv_buf_pool_instances, L2533)

 코디네이터                     워커 1                       워커 2
 -----------------------------  ---------------------------  ---------------------------
 pc_request(n, lsn_limit)
   slot[0..k].state = REQUESTED
   is_requested set  ---------> 깨어남                       깨어남
 pc_flush_slot                  pc_flush_slot                pc_flush_slot
   slot 0 가져감 (FLUSHING)       slot 1 가져감                slot 2 가져감
   LRU 배치, flush list 배치      LRU 배치, flush list 배치    ...
   slot 0 FINISHED                slot 1 FINISHED
 pc_flush_slot 이 0 을 돌려줄
 때까지 남은 슬롯을 더 가져간다
 pc_wait_finished                                             마지막 슬롯 FINISHED
   is_finished 를 기다림  <-----------------------------------  is_finished set (L2708)
   합계를 모으고 NONE 으로
   buf_flush_tick_event set (L2759)
```

```text
 이번 바퀴에 무엇을 할까 (L3061-L3083)

 is_sync_flush  ret_sleep       lsn_limit                  n_to_flush
 true           any             log_sync_flush_lsn + a     page_recommendation(.., true)
 false          TIME_EXCEEDED   LSN_MAX                    page_recommendation(.., false)
 false          other           0                          0, flush list 는 건너뛰고 LRU 만

 server 가 idle 이면 위 대신 buf_flush_lists(PCT_IO(idle_flush_pct))  (L3137-L3139)
```

`buf_flush_event` 를 set 하는 곳은 여럿이다. 그중 이 흐름에 걸리는 것은 checkpointer 의 `log_request_sync_flush`(log0chkp.cc L670)와 free 블록이 모자란 사용자 스레드(buf0lru.cc L1405)다.

## 결과가 쓰이는 곳

```text
 슬롯의 n_pages_requested, page_cleaner->lsn_limit
      --> [02] pc_flush_slot 이 buf_flush_do_batch 에 넘긴다

 buf_flush_tick_event
      --> log_request_sync_flush 가 sync flush 한 바퀴가 끝나기를 기다린다 (log0chkp.cc L689-L691)

 L3056 의 log_write_up_to
      --> 이후 페이지 쓰기의 WAL 검사([05])가 대부분 기다리지 않고 통과한다
```

## 다루지 않는 것

`Adaptive_flush` 의 계산(io_capacity, dirty 비율, redo 생성 속도), `pc_sleep_if_needed`, 경고 로그 간격, 버퍼 풀 축소(withdraw), 종료 단계(L3157 이후)의 flush 반복과 `buf_flush_await_no_flushing` 은 요약만 했다.
