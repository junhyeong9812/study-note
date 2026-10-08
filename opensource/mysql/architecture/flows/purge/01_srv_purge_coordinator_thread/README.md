# srv_purge_coordinator_thread

상위: [purge](../README.md)

**purge 코디네이터 스레드의 본체다.** 서버가 켜질 때 하나 뜨고, 종료할 때까지 "할 일이 없으면 자고, 깨면 [02] `srv_do_purge` 를 돌린다"를 반복한다. 자는 조건은 단순하다. 직전 반복에서 처리한 undo 페이지가 0 이었거나 purge 가 중지 상태면 잔다. 깨우는 쪽은 둘이다. 커밋하는 사용자 스레드가 history 가 길어졌을 때 `srv_wake_purge_thread_if_not_active` 로 깨우고, 그렇지 않아도 먼저 최대 10ms 를 기다린 뒤 스스로 깨어 history 길이를 다시 본다. 길이가 그대로이고 5000 보다 짧으면 그다음에는 깨워 줄 때까지 시간 제한 없이 잔다. 종료할 때는 느린 종료(`innodb_fast_shutdown=0`)면 history 를 끝까지 비우고 나간다. 코디네이터는 워커이기도 하다. 워커 배열의 0 번 자리가 코디네이터다(srv0start.cc L2178).

## 위치

`storage` / `innobase` / `srv` / `srv0srv.cc` L3032-L3146 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L3032-L3146))

## 실제 코드

시작과 주 루프다. 상태를 `PURGE_STATE_RUN` 으로 바꾸고, 자거나 [02] 를 돌리기를 종료 조건이 될 때까지 반복한다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L3032-L3079 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L3032-L3079))

```cpp
// srv0srv.cc L3032-L3079
void srv_purge_coordinator_thread() {
  srv_slot_t *slot;

  THD *thd = create_internal_thd();

  // Allow purge in read only mode as well.
  thd->set_skip_readonly_check();

  purge_sys->is_this_a_purge_thread = true;

  ulint n_total_purged = ULINT_UNDEFINED;

  ut_ad(!srv_read_only_mode);
  ut_a(srv_n_purge_threads >= 1);
  ut_a(trx_purge_state() == PURGE_STATE_INIT);
  ut_a(srv_force_recovery < SRV_FORCE_NO_BACKGROUND);

  rw_lock_x_lock(&purge_sys->latch, UT_LOCATION_HERE);

  purge_sys->running = true;
  purge_sys->state = PURGE_STATE_RUN;

  rw_lock_x_unlock(&purge_sys->latch);

  slot = srv_reserve_slot(SRV_PURGE);

  ulint rseg_history_len = trx_sys->rseg_history_len;

  do {
    /* If there are no records to purge or the last
    purge didn't purge any records then wait for activity. */

    if (srv_shutdown_state.load() < SRV_SHUTDOWN_PURGE &&
        (purge_sys->state == PURGE_STATE_STOP || n_total_purged == 0)) {
      srv_purge_coordinator_suspend(slot, rseg_history_len);
    }

    if (srv_purge_should_exit(n_total_purged)) {
      ut_a(!slot->suspended);
      break;
    }

    n_total_purged = 0;

    rseg_history_len = srv_do_purge(&n_total_purged);

  } while (!srv_purge_should_exit(n_total_purged));

```

종료 쪽이다(바로 앞 L3080-L3086 의 테스트용 지연 호출은 뺐다). 느린 종료면 남은 것을 배치 크기 그대로 끝까지 purge 하고, 빠른 종료여도 배치 20 으로 한 번 더 돌린다. 그 뒤 상태를 `PURGE_STATE_EXIT` 로 바꾸고 워커를 깨워 내보낸다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L3088-L3146 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L3088-L3146))

```cpp
// srv0srv.cc L3088-L3146
  /* Ensure that we don't jump out of the loop unless the
  exit condition is satisfied. */

  ut_a(srv_purge_should_exit(n_total_purged));

  ulint n_pages_purged = ULINT_MAX;

  /* Ensure that all records are purged if it is not a fast shutdown.
  This covers the case where a record can be added after we exit the
  loop above. */
  while (srv_fast_shutdown == 0 && n_pages_purged > 0) {
    n_pages_purged = trx_purge(1, srv_purge_batch_size, false);
  }

  /* This trx_purge is called to remove any undo records (added by
  background threads) after completion of the above loop. When
  srv_fast_shutdown != 0, a large batch size can cause significant
  delay in shutdown, so reducing the batch size to magic number 20
  (which was default in 5.5), which we hope will be sufficient to
  remove all the undo records */
  const uint temp_batch_size = 20;

  n_pages_purged =
      trx_purge(1,
                srv_purge_batch_size <= temp_batch_size ? srv_purge_batch_size
                                                        : temp_batch_size,
                true);
  ut_a(n_pages_purged == 0 || srv_fast_shutdown != 0);

  /* The task queue should always be empty, independent of fast
  shutdown state. */
  ut_a(srv_get_task_queue_length() == 0);

  srv_free_slot(slot);

  /* Note that we are shutting down. */
  rw_lock_x_lock(&purge_sys->latch, UT_LOCATION_HERE);

  purge_sys->state = PURGE_STATE_EXIT;

  /* Clear out any pending undo-tablespaces to truncate and reset
  the list as we plan to shutdown the purge thread. */
  purge_sys->undo_trunc.reset();

  purge_sys->running = false;

  rw_lock_x_unlock(&purge_sys->latch);

  /* Ensure that all the worker threads quit. */
  if (srv_n_purge_threads > 1) {
    srv_release_threads(SRV_WORKER, srv_n_purge_threads - 1);
  }

  /* This is just for test scenarios. Do not pass thd here.
  For explanation look at comment for similar usage above. */
  srv_thread_delay_cleanup_if_needed(false);

  destroy_internal_thd(thd);
}
```

자는 쪽이다. 넘겨받은 길이(`rseg_history_len`)가 지금 길이 이하면, 곧 history 가 그대로이거나 늘었으면 최대 10ms 를 기다리고, 지금 길이가 더 작으면 기다리지 않는다. 소스 주석은 "늘었으면 기다리지 않는다"고 적었지만 조건식은 반대 방향이다. 10ms 를 다 기다렸는데 길이가 그대로이고 5000 보다 짧으면 다음에는 시간 제한 없이 잔다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L2923-L3029 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2923-L3029))

```cpp
// srv0srv.cc L2923-L3029
static void srv_purge_coordinator_suspend(
    srv_slot_t *slot,       /*!< in/out: Purge coordinator
                            thread slot */
    ulint rseg_history_len) /*!< in: history list length
                            before last purge */
{
  ut_ad(!srv_read_only_mode);
  ut_a(slot->type == SRV_PURGE);

  bool stop = false;

  /** Maximum wait time on the purge event. */
  constexpr std::chrono::milliseconds SRV_PURGE_MAX_TIMEOUT{10};

  int64_t sig_count = srv_suspend_thread(slot);

  do {
    ulint ret;

    rw_lock_x_lock(&purge_sys->latch, UT_LOCATION_HERE);

    purge_sys->running = false;

    rw_lock_x_unlock(&purge_sys->latch);

    /* We don't wait right away on the the non-timed wait because
    we want to signal the thread that wants to suspend purge. */

    if (stop) {
      os_event_wait_low(slot->event, sig_count);
      ret = 0;
    } else if (rseg_history_len <= trx_sys->rseg_history_len.load()) {
      ret =
          os_event_wait_time_low(slot->event, SRV_PURGE_MAX_TIMEOUT, sig_count);
    } else {
      /* We don't want to waste time waiting, if the
      history list increased by the time we got here,
      unless purge has been stopped. */
      ret = 0;
    }

    srv_sys_mutex_enter();

    /* The thread can be in state !suspended after the timeout
    but before this check if another thread sent a wakeup signal. */

    if (slot->suspended) {
      slot->suspended = false;
      ++srv_sys->n_threads_active[slot->type];
      ut_a(srv_sys->n_threads_active[slot->type] == 1);
    }

    srv_sys_mutex_exit();

    sig_count = srv_suspend_thread(slot);

    rw_lock_x_lock(&purge_sys->latch, UT_LOCATION_HERE);

    stop = (srv_shutdown_state.load() < SRV_SHUTDOWN_PURGE &&
            purge_sys->state == PURGE_STATE_STOP);

    if (!stop) {
      // ... (L2985-L2994 생략: 디버그 빌드의 중지 상태 검사)
      purge_sys->running = true;
    } else {
      ut_a(purge_sys->n_stop > 0);

      /* Signal that we are suspended. */
      os_event_set(purge_sys->event);
    }

    rw_lock_x_unlock(&purge_sys->latch);

    if (ret == OS_SYNC_TIME_EXCEEDED) {
      /* No new records added since wait started then simply
      wait for new records. The magic number 5000 is an
      approximation for the case where we have cached UNDO
      log records which prevent truncate of the UNDO
      segments. */

      if (rseg_history_len == trx_sys->rseg_history_len &&
          trx_sys->rseg_history_len < 5000) {
        stop = true;
      }
    }

  } while (stop);

  srv_sys_mutex_enter();

  if (slot->suspended) {
    slot->suspended = false;
    ++srv_sys->n_threads_active[slot->type];
    ut_a(srv_sys->n_threads_active[slot->type] == 1);
  }

  srv_sys_mutex_exit();
}
```

종료해야 하는지 묻는 함수다. 종료 단계가 `SRV_SHUTDOWN_PURGE` 에 오면, 빠른 종료이거나 직전 배치가 0 페이지였을 때 나간다.

`storage` / `innobase` / `srv` / `srv0srv.cc` L2727-L2753 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/srv/srv0srv.cc#L2727-L2753))

```cpp
// srv0srv.cc L2727-L2753
static bool srv_purge_should_exit(
    ulint n_purged) /*!< in: pages purged in last batch */
{
  switch (srv_shutdown_state.load()) {
    case SRV_SHUTDOWN_NONE:
    case SRV_SHUTDOWN_RECOVERY_ROLLBACK:
    case SRV_SHUTDOWN_PRE_DD_AND_SYSTEM_TRANSACTIONS:
      /* Normal operation. */
      break;

    case SRV_SHUTDOWN_PURGE:
      /* Exit unless slow shutdown requested or all done. */
      return (srv_fast_shutdown != 0 || n_purged == 0);

    case SRV_SHUTDOWN_EXIT_THREADS:
      return (true);

    case SRV_SHUTDOWN_LAST_PHASE:
    case SRV_SHUTDOWN_FLUSH_PHASE:
    case SRV_SHUTDOWN_MASTER_STOP:
    case SRV_SHUTDOWN_CLEANUP:
    case SRV_SHUTDOWN_DD:
      ut_error;
  }

  return (false);
}
```

## 동작 흐름

```text
 srv_purge_coordinator_thread
 L3035  create_internal_thd                       purge 도 THD 를 가진다 (테이블을 열고 MDL 을 잡는다)
 L3040  purge_sys->is_this_a_purge_thread = true
 L3051  purge_sys->running = true, state = PURGE_STATE_RUN
 L3056  srv_reserve_slot(SRV_PURGE)               깨우는 쪽이 이 슬롯의 이벤트를 쓴다
 L3058  rseg_history_len = 현재 history 길이

 L3060  do
 L3065    종료 중이 아니고 (중지 상태이거나 직전에 0 페이지였으면)
 L3066      srv_purge_coordinator_suspend(slot, rseg_history_len)
 L3069    srv_purge_should_exit 면 break
 L3074    n_total_purged = 0
 L3076    rseg_history_len = [02] srv_do_purge(&n_total_purged)
 L3078  while (!srv_purge_should_exit(n_total_purged))

 L3098  느린 종료면  while (n_pages_purged > 0) trx_purge(1, batch_size, false)
 L3110  한 번 더  trx_purge(1, min(batch_size, 20), true)
 L3119  작업 큐가 비었는지 확인
 L3126  state = PURGE_STATE_EXIT, undo_trunc.reset, running = false
 L3137  워커가 있으면 srv_release_threads(SRV_WORKER, n - 1)
```

```text
 코디네이터가 자고 깨는 길 (srv_purge_coordinator_suspend, srv0srv.cc L2923)

      +----------------------------------------------------------+
      |                                                          |
      v                                                          |
 running = false                                                 |
      |                                                          |
      +-- stop (중지 요청)         -> 시간 제한 없이 기다린다    |
      +-- 그대로이거나 늘었다       -> 최대 10ms 기다린다         |
      |   (rseg_history_len <= 현재 길이)                        |
      +-- 현재 길이가 더 작다       -> 기다리지 않는다            |
      |   (주석은 "늘었으면"이라 적었지만 조건식은 이 경우다)     |
      |                                                          |
 깨어남 (시간 초과, 또는 커밋 쪽의 srv_wake_purge_thread_if_not_active)
      |
 중지 상태면 stop = true, purge_sys->event 를 set (중지 요청자에게 "멈췄다")
 아니면 running = true
      |
 시간 초과였고 길이가 그대로이며 < 5000 이면 stop = true   (주석: 캐시된 undo 때문에
      |                                                         truncate 못 하는 경우의 근사치)
 stop 이면 다시 위로 --------------------------------------------+
 아니면 주 루프로 돌아가 [02]
```

```text
 커밋 쪽에서 깨우는 조건 (trx0purge.cc L405-L410)

 update undo 를 history 에 올린 뒤
   rseg_history_len > innodb_purge_threads x innodb_purge_batch_size 이면
     srv_wake_purge_thread_if_not_active (srv0srv.cc L1946)
       purge 상태가 RUN 이고 활성 코디네이터가 0 개일 때만 SRV_PURGE 슬롯을 깨운다
```

## 결과가 쓰이는 곳

```text
 rseg_history_len (주 루프의 지역 변수)
      --> 다음 suspend 가 지금 길이와 비교한다 (L2954)
 purge_sys->running, purge_sys->state
      --> trx_purge_stop / trx_purge_run 이 이 값으로 중지와 재개를 맞춘다
      --> 워커는 state == PURGE_STATE_EXIT 를 보고 끝난다 ([06])
```

## 다루지 않는 것

purge 중지와 재개(`trx_purge_stop`, `trx_purge_run`, `purge_sys->n_stop`), 슬롯과 이벤트의 관리(`srv_reserve_slot`, `srv_suspend_thread`, `srv_release_threads`), 종료 단계의 순서(`srv_shutdown_state`), 테스트용 지연(`srv_thread_delay_cleanup_if_needed`)은 이 흐름의 곁가지라 줄만 적었다. 스레드를 띄우는 `srv_start_purge_threads` 는 [스레드 구성](../../../structure/threads/README.md)에 둔다.
