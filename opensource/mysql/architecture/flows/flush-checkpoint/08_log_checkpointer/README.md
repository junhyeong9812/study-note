# log_checkpointer

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**checkpoint 를 쓰는 유일한 스레드다**(log0write.cc L401 주석 "it's the only thread allowed to do it!"). 한 바퀴에 두 가지를 본다. 첫째, redo 가 너무 차서 dirty 페이지를 서둘러 써야 하는가(`log_consider_sync_flush`) -- 그렇다면 page cleaner 를 깨워 sync flush 를 시키고 한 바퀴를 기다린다. 둘째, checkpoint 를 새로 적을 때인가(`log_consider_checkpoint`) -- 1초가 지났거나 checkpoint age 가 공격적 기준을 넘었거나 누가 요청했으면 [09] 로 간다. 바쁠 때는 주기를 7배로 늘린다.

## 위치

`storage` / `innobase` / `log` / `log0chkp.cc` L904-L1000 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L904-L1000))

## 실제 코드

`storage` / `innobase` / `log` / `log0chkp.cc` L904-L1000 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L904-L1000))

```cpp
// log0chkp.cc L904-L1000
void log_checkpointer(log_t *log_ptr) {
  ut_a(log_ptr != nullptr);

  log_t &log = *log_ptr;

  ut_d(log.m_checkpointer_thd = create_internal_thd());

  static const uint64_t log_busy_checkpoint_interval =
      7; /*SRV_MASTER_CHECKPOINT_INTERVAL*/
  auto old_activity_count = srv_get_activity_count();
  ulint error = OS_SYNC_TIME_EXCEEDED;

  for (;;) {
    log_checkpointer_mutex_enter(log);

    const auto sig_count = os_event_reset(log.checkpointer_event);
    const lsn_t requested_checkpoint_lsn = log.requested_checkpoint_lsn;

    bool system_is_busy = false;
    if (error == OS_SYNC_TIME_EXCEEDED &&
        srv_check_activity(old_activity_count)) {
      old_activity_count = srv_get_activity_count();
      /* system is busy. takes longer interval. */
      system_is_busy = true;
    }

    if (error != OS_SYNC_TIME_EXCEEDED || !system_is_busy ||
        requested_checkpoint_lsn >
            log.last_checkpoint_lsn.load(std::memory_order_acquire) ||
        log_checkpoint_time_elapsed(log) >=
            log_busy_checkpoint_interval * get_srv_log_checkpoint_every()) {
      /* Consider flushing some dirty pages. */
      log_consider_sync_flush(log);

      log_sync_point("log_checkpointer_before_consider_checkpoint");

      /* Consider writing checkpoint. */
      log_consider_checkpoint(log);
    }

    log_checkpointer_mutex_exit(log);

    if (requested_checkpoint_lsn >
        log.last_checkpoint_lsn.load(std::memory_order_relaxed)) {
      /* not satisfied. retry. */
      error = 0;
    } else {
      error = os_event_wait_time_low(log.checkpointer_event,
                                     get_srv_log_checkpoint_every(), sig_count);
    }

    /* Check if we should close the thread. */
    if (log.should_stop_threads.load()) {
      ut_ad(!log.writer_threads_paused.load());
      if (!log_flusher_is_active() && !log_writer_is_active()) {
        lsn_t end_lsn = log.write_lsn.load();

        ut_a(log_is_data_lsn(end_lsn));
        ut_a(end_lsn == log.flushed_to_disk_lsn.load());
        ut_a(end_lsn == log_buffer_ready_for_write_lsn(log));

        ut_a(end_lsn >= buf_flush_list_added->smallest_not_added_lsn());

        if (buf_flush_list_added->smallest_not_added_lsn() == end_lsn) {
          /* All confirmed reservations have been written
          to redo and all dirty pages related to those
          writes have been added to flush lists.

          However, there could be user threads, which are
          in the middle of log_buffer_reserve(), reserved
          range of sn values, but could not confirm.

          Note that because log_writer is already not alive,
          the only possible reason guaranteed by its death,
          is that there is x-lock at end_lsn, in which case
          end_lsn separates two regions in log buffer:
          completely full and completely empty. */
          const lsn_t ready_lsn = log_buffer_ready_for_write_lsn(log);

          const lsn_t current_lsn = log_get_lsn(log);

          if (current_lsn > ready_lsn) {
            log.recent_written.validate_no_links(ready_lsn, current_lsn);
            buf_flush_list_added->validate_not_added(ready_lsn, current_lsn);
          }

          break;
        }
        /* We need to wait until remaining dirty pages
        have been added. */
      }
      /* We prefer to wait until all writing is done. */
    }
  }

  ut_d(destroy_internal_thd(log.m_checkpointer_thd));
}
```

checkpoint 를 쓸지 정하는 조건 세 가지다.

`storage` / `innobase` / `log` / `log0chkp.cc` L789-L870 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L789-L870))

```cpp
// log0chkp.cc L789-L870
static bool log_should_checkpoint(log_t &log) {
  lsn_t last_checkpoint_lsn;
  lsn_t oldest_lsn;
  lsn_t current_lsn;
  lsn_t requested_checkpoint_lsn;
  lsn_t checkpoint_age;
  bool periodical_checkpoints_enabled;

  ut_ad(log_checkpointer_mutex_own(log));

#ifdef UNIV_DEBUG
  if (srv_checkpoint_disabled) {
    return false;
  }
#endif /* UNIV_DEBUG */

  /* Note: log.allow_checkpoints is set to true after recovery is finished,
  and changes gathered in recv_sys->metadata_recover are applied to dict_table_t
  objects; or in log_start() if recovery was not needed. We can't reclaim
  free space in redo log until DD dynamic metadata records are safe. */
  if (!log.m_allow_checkpoints.load(std::memory_order_acquire)) {
    return false;
  }

  last_checkpoint_lsn = log.last_checkpoint_lsn.load();

  /* We read the values under log_limits_mutex and release the mutex.
  The values might be changed just afterwards and that's fine. Note,
  they can only become increased. Either we decided to write chkp on
  too small value or we did not decide and we could decide in next
  iteration of the thread's loop. The only risk is that checkpointer
  could go waiting on event and miss the signaled requirement to write
  checkpoint at higher lsn, which was requested just after we released
  the mutex. This is impossible, because we read sig_count of the event
  when we reset the event which happens before this point and then pass
  the sig_count to the function responsible for waiting. If sig_count
  is changed it means new notifications are there and we instantly start
  next iteration. The event is signaled under the limits_mutex in the
  same critical section in which requirements are updated. */

  log_limits_mutex_enter(log);
  oldest_lsn = log.available_for_checkpoint_lsn;
  requested_checkpoint_lsn = log.requested_checkpoint_lsn;
  periodical_checkpoints_enabled = log.periodical_checkpoints_enabled;
  log_limits_mutex_exit(log);

  if (oldest_lsn <= last_checkpoint_lsn) {
    return false;
  }

  current_lsn = log_get_lsn(log);

  ut_a(last_checkpoint_lsn <= oldest_lsn);
  ut_a(oldest_lsn <= current_lsn);

  const lsn_t margin = log_free_check_margin(log);

  checkpoint_age = current_lsn + margin - last_checkpoint_lsn;

  /* Update checkpoint_lsn stored in header of log files if:

          a) periodical checkpoints are enabled and more than 1s
             elapsed since the last checkpoint,
          b) or checkpoint age is greater than aggressive_checkpoint_min_age,
          c) or it was requested to have greater checkpoint_lsn,
             and oldest_lsn allows to satisfy the request. */

  if ((last_checkpoint_lsn < requested_checkpoint_lsn &&
       requested_checkpoint_lsn <= oldest_lsn) ||
      checkpoint_age >= log.m_capacity.aggressive_checkpoint_min_age()) {
    return true;
  }

  DBUG_EXECUTE_IF("periodical_checkpoint_disabled",
                  periodical_checkpoints_enabled = false;);

  if (!periodical_checkpoints_enabled) {
    return false;
  }

  return get_srv_log_checkpoint_every() <= log_checkpoint_time_elapsed(log);
}
```

쓰기로 했으면 dict 메타데이터를 먼저 내리고, 조건을 다시 본 뒤 [09] 를 부른다.

`storage` / `innobase` / `log` / `log0chkp.cc` L872-L902 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L872-L902))

```cpp
// log0chkp.cc L872-L902
static void log_consider_checkpoint(log_t &log) {
  ut_ad(log_checkpointer_mutex_own(log));

  if (!log_should_checkpoint(log)) {
    return;
  }

  /* It's clear that a new checkpoint should be written.
  So do write back the dynamic metadata. Since the checkpointer
  mutex is low-level one, it has to be released first. */
  log_checkpointer_mutex_exit(log);

  if (log_test == nullptr) {
    dict_persist_to_dd_table_buffer();
  }

  log_checkpointer_mutex_enter(log);

  /* We need to re-check if checkpoint should really be
  written, because we re-acquired the checkpointer_mutex.
  Some conditions could have changed - e.g. user could
  acquire the mutex and specify srv_checkpoint_disabled=T.
  Instead of trying to figure out which conditions could
  have changed, we follow a simple way and perform a full
  re-check of all conditions. */
  if (!log_should_checkpoint(log)) {
    return;
  }

  log_checkpoint(log);
}
```

sync flush 가 필요한 lsn 을 계산한다. 0 이면 필요 없다.

`storage` / `innobase` / `log` / `log0chkp.cc` L700-L780 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L700-L780))

```cpp
// log0chkp.cc L700-L780
lsn_t log_sync_flush_lsn(log_t &log) {
  /* Note: log.m_allow_checkpoints is set to true after recovery is finished,
  and changes gathered in recv_sys->metadata_recover are applied to dict_table_t
  objects; or in log_start() if recovery was not needed. Until that happens
  checkpoints are disallowed, so sync flush decisions (based on checkpoint age)
  should be postponed. */
  if (!log.m_allow_checkpoints.load(std::memory_order_acquire)) {
    return 0;
  }

  log_update_available_for_checkpoint_lsn(log);

  /* We acquire limits mutex only for a short period. Afterwards these
  values might be changed (advanced to higher values). However, in the
  worst case we would request sync flush for too small value, and the
  function which requests the sync flush is safe to be used with any
  lsn value. It ensures itself that maximum of all requested lsn values
  is taken. In next iteration of log_checkpointer we would notice the
  higher values and re-request the sync flush if needed (or user threads
  waiting in log_free_check() would request it themselves meanwhile). */

  log_limits_mutex_enter(log);
  const lsn_t oldest_lsn = log.available_for_checkpoint_lsn;
  const lsn_t requested_checkpoint_lsn = log.requested_checkpoint_lsn;
  log_limits_mutex_exit(log);

  lsn_t flush_up_to = oldest_lsn;

  lsn_t current_lsn = log_get_lsn(log);

  ut_a(flush_up_to <= current_lsn);

  if (current_lsn == flush_up_to) {
    return 0;
  }

  const lsn_t margin = log_free_check_margin(log);

  const lsn_t adaptive_flush_max_age = log.m_capacity.adaptive_flush_max_age();

  if (current_lsn + margin - oldest_lsn > adaptive_flush_max_age) {
    ut_a(current_lsn + margin > adaptive_flush_max_age);

    flush_up_to = current_lsn + margin - adaptive_flush_max_age;
  }

  if (requested_checkpoint_lsn > flush_up_to) {
    flush_up_to = requested_checkpoint_lsn;
  }

  if (flush_up_to > current_lsn) {
    flush_up_to = current_lsn;
  }

  if (flush_up_to > oldest_lsn) {
    flush_up_to += buf_flush_list_added->order_lag();

    return flush_up_to;
  }

  return 0;
}

static void log_consider_sync_flush(log_t &log) {
  ut_ad(log_checkpointer_mutex_own(log));

  const auto flush_up_to = log_sync_flush_lsn(log);

  if (flush_up_to != 0) {
    log_checkpointer_mutex_exit(log);

    log_request_sync_flush(log, flush_up_to);

    log_checkpointer_mutex_enter(log);

    /* It's very probable that forced flush will result in maximum
    lsn available for creating a new checkpoint, just try to update
    it to not wait for next checkpointer loop. */
    log_update_available_for_checkpoint_lsn(log);
  }
}
```

page cleaner 에게 sync flush 를 요청하는 쪽이다.

`storage` / `innobase` / `log` / `log0chkp.cc` L643-L698 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L643-L698))

```cpp
// log0chkp.cc L643-L698
static bool log_request_sync_flush(const log_t &log, lsn_t new_oldest) {
  if (log_test != nullptr) {
    return false;
  }

  /* A flush is urgent: we have to do a synchronous flush,
  because the oldest dirty page is too old.

  Note, that this could fire even if we did not run out
  of space in log files (users still may write to redo). */

  if (new_oldest == LSN_MAX
      /* Forced flush request is processed by page_cleaner, if
      it's not active, then we must do flush ourselves. */
      || !buf_flush_page_cleaner_is_active()
      /* Reason unknown. */
      || srv_is_being_started) {
    buf_flush_sync_all_buf_pools();

    return true;

  } else if (srv_flush_sync) {
    /* Wake up page cleaner asking to perform sync flush
    (unless user explicitly disabled sync-flushes). */

    int64_t sig_count = os_event_reset(buf_flush_tick_event);

    os_event_set(buf_flush_event);

    /* Wait until flush is finished or timeout happens. This is to delay
    furious checkpoint writing when sync flush is active. However, if the
    log_writer entered its extra_margin, it's better to be more aggressive
    with checkpoint writing, because the problem very likely is related to
    missing log_free_check() calls and oldest dirt page being also the newest
    page that was modified and can't be flushed due to missing space in redo.
    In such case, it is very desired to move checkpoint forward even a little
    bit. If there is a sequence of such pages, then it becomes problematic and
    we would better not delay the checkpointing that much.

    The log.m_writer_inside_extra_margin is read without mutex protection for
    performance reasons (not to keep the mutex acquired when waiting below).
    In case of torn read or race, in the worst case we would use different
    timeout than the desired one. It doesn't affect correctness. */

    const auto time_to_wait_ms = log.m_writer_inside_extra_margin ? 1 : 1000;

    os_event_wait_time_low(buf_flush_tick_event,
                           std::chrono::milliseconds{time_to_wait_ms},
                           sig_count);

    return true;

  } else {
    return false;
  }
}
```

## 동작 흐름

```text
 L911  log_busy_checkpoint_interval = 7
 L916  for (;;)
 L917    checkpointer_mutex
 L919    sig_count = reset(checkpointer_event)
 L927    직전 대기가 timeout 이고 활동이 있었으면 system_is_busy
 L930    바쁘지 않거나, 요청이 있거나, 7 * checkpoint_every 가 지났으면
 L936      log_consider_sync_flush
             L766  flush_up_to = log_sync_flush_lsn
                     L710  available_for_checkpoint_lsn 을 새로 계산 ([09] 의 식)
                     L740  current + margin - oldest > adaptive_flush_max_age 면
                     L743    flush_up_to = current + margin - max_age
                     L747  요청된 checkpoint lsn 이 더 크면 그것
                     L755  oldest 보다 크면 + order_lag 해서 돌려준다, 아니면 0
             L771  0 이 아니면 mutex 를 놓고 log_request_sync_flush
                     L654  LSN_MAX 이거나 page cleaner 가 없으면 직접 buf_flush_sync_all_buf_pools
                     L664  srv_flush_sync 면 buf_flush_event set, buf_flush_tick_event 를 최대 1초 기다림
             L778  available_for_checkpoint_lsn 을 다시 갱신
 L941      log_consider_checkpoint
             L875  log_should_checkpoint 아니면 return
             L885  dict_persist_to_dd_table_buffer        (mutex 를 놓고)
             L897  다시 확인
             L901  [09] log_checkpoint
 L946    요청이 아직 안 채워졌으면 바로 다시, 아니면 checkpoint_every 동안 잔다
 L956    종료 요청이고 writer, flusher 가 끝났고 모든 mtr 이 flush list 에 붙었으면 break
```

```text
 log_should_checkpoint 의 판정 (L835-L869)

 위에서부터 먼저 걸리는 줄이 답이다

 line    result   condition
 L835    false    oldest_lsn <= last_checkpoint_lsn, 앞으로 갈 곳이 없다
 L856    true     요청(requested)이 있고 requested <= oldest_lsn
 L858    true     checkpoint_age >= aggressive_checkpoint_min_age
 L865    false    주기 checkpoint 가 꺼져 있다
 L869    true     마지막 checkpoint 뒤 checkpoint_every 가 지났다 (주석 L850 은 1s)

 checkpoint_age = current_lsn + margin - last_checkpoint_lsn  (L846)
```

redo 가 차는 정도를 보는 문턱은 셋이고, 누가 무엇을 하는지가 다르다.

```text
 checkpoint age 로 걸리는 세 문턱

 age = current_lsn + margin - last_checkpoint_lsn

 threshold                       who            where                넘으면
 aggressive_checkpoint_min_age   checkpointer   L858                 1초를 기다리지 않고 checkpoint
 adaptive_flush_max_age          checkpointer   L740                 page cleaner 에 sync flush 요청
 hard_logical_capacity           log_writer     log0write.cc L1893   넘는 만큼은 쓰지 않고 기다린다

 hard_logical_capacity 안쪽에 soft_logical_capacity 가 있고, log writer 가 아닌
 스레드는 soft 쪽을 본다 (log0files_capacity.cc L55-L63 트리 주석)

 L740 이 빼는 값은 last_checkpoint_lsn 이 아니라 available_for_checkpoint_lsn 이다
 (L722, L726)

 세 문턱의 크기 (update_exposed, log0files_capacity.cc L475-L499)
   soft                          = hard * (1 - 5/100)       L433, log0constants.h L352
   adaptive_flush_max_age        = soft * (1 - 1/16)        L449, L487-L488, log0constants.h L396
   aggressive_checkpoint_min_age = soft - soft / 32         L495-L497, log0constants.h L392

   0 ---- adaptive_flush_max_age ---- aggressive_checkpoint_min_age ---- soft ---- hard
          (soft 의 15/16)              (soft 의 31/32)
   RATIO_MIN(32) 이 RATIO_MAX(16) 보다 커야 한다는 주석(log0constants.h L391)이 이 순서를 정한다
   (단 L740 은 available_for_checkpoint_lsn 기준, L858 은 last_checkpoint_lsn 기준이라 비교 대상이 다르다)
```

## 결과가 쓰이는 곳

```text
 buf_flush_event, lsn_limit
      --> [01] 코디네이터가 log_sync_flush_lsn 을 직접 다시 읽어 sync flush 모드로 간다 (buf0flu.cc L3035)

 available_for_checkpoint_lsn
      --> [09] log_determine_checkpoint_lsn 이 읽는다

 log_checkpoint 호출
      --> [09] -> [10] 에서 last_checkpoint_lsn 이 오른다
```

## 다루지 않는 것

`dict_persist_to_dd_table_buffer` 와 `dict_max_allowed_checkpoint_lsn`, 용량 문턱들의 계산(`Log_files_capacity`), `log_request_checkpoint` 와 `log_make_latest_checkpoint` 로 checkpoint 를 요청하는 호출처, 종료 판정의 세부(L956-L994)는 요약만 했다.
