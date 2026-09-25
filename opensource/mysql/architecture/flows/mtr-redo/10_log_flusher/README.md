# log_flusher

상위: [mini-transaction과 redo 기록](../README.md)

**redo 파일을 fsync 하고 `flushed_to_disk_lsn` 을 올리는 전용 스레드다.** 이 값이 이 흐름의 끝이다. 커밋은 이 값이 자기 lsn 을 넘기를 기다리고, 페이지 쓰기는 이 값이 페이지의 newest_modification 을 넘기를 기다리고, checkpoint 는 이 값을 넘지 못한다. 돌아가는 박자는 `innodb_flush_log_at_trx_commit` 이 정한다. 1 이면 log writer 가 쓸 때마다 깨우고, 아니면 `innodb_flush_log_at_timeout` 간격으로 스스로 돈다.

## 위치

`storage` / `innobase` / `log` / `log0write.cc` L2495-L2620 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L2495-L2620))

## 실제 코드

스레드 본체다.

`storage` / `innobase` / `log` / `log0write.cc` L2495-L2620 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L2495-L2620))

```cpp
// log0write.cc L2495-L2620
void log_flusher(log_t *log_ptr) {
  ut_a(log_ptr != nullptr);

  log_t &log = *log_ptr;

  Log_thread_waiting waiting{log, log.flusher_event, srv_log_flusher_spin_delay,
                             get_srv_log_flusher_timeout()};

  log_flusher_mutex_enter(log);

  for (uint64_t step = 0;; ++step) {
    if (log.should_stop_threads.load()) {
      if (!log_writer_is_active()) {
        /* If write_lsn > flushed_to_disk_lsn, we are going to execute
        one more fsync just after the for-loop and before this thread
        exits (inside log_flush_low at the very end of function def.). */
        break;
      }
    }

    if (UNIV_UNLIKELY(
            log.writer_threads_paused.load(std::memory_order_acquire))) {
      log_flusher_mutex_exit(log);

      os_event_wait(log.writer_threads_resume_event);

      log_flusher_mutex_enter(log);
    }

    bool released = false;

    auto stop_condition = [&log, &released, step](bool wait) {
      if (released) {
        log_flusher_mutex_enter(log);
        released = false;
      }

      log_sync_point("log_flusher_before_should_flush");

      const lsn_t last_flush_lsn = log.flushed_to_disk_lsn.load();

      ut_a(last_flush_lsn <= log.write_lsn.load());

      if (last_flush_lsn < log.write_lsn.load()) {
        /* Flush and stop waiting. */
        log_flush_low(log);

        if (step % 1024 == 0) {
          log_flusher_mutex_exit(log);

          std::this_thread::yield();

          log_flusher_mutex_enter(log);
        }

        return true;
      }

      /* Stop waiting if writer thread is dead. */
      if (log.should_stop_threads.load()) {
        if (!log_writer_is_active()) {
          return true;
        }
      }

      if (UNIV_UNLIKELY(
              log.writer_threads_paused.load(std::memory_order_acquire))) {
        return true;
      }

      if (wait) {
        log_flusher_mutex_exit(log);
        released = true;
      }

      return false;
    };

    if (srv_flush_log_at_trx_commit != 1) {
      const auto current_time = Log_clock::now();

      ut_ad(log.last_flush_end_time >= log.last_flush_start_time);

      if (current_time < log.last_flush_end_time) {
        /* Time was moved backward, possibly by a lot, so we need to
        adjust the last_flush times, because otherwise we could stop
        flushing every innodb_flush_log_at_timeout for a while. */
        log.last_flush_start_time = current_time;
        log.last_flush_end_time = current_time;
      }

      const auto time_elapsed =
          std::chrono::duration_cast<std::chrono::milliseconds>(
              current_time - log.last_flush_start_time);

      ut_a(time_elapsed >= std::chrono::seconds::zero());

      const auto flush_every = get_srv_flush_log_at_timeout();

      if (time_elapsed < flush_every) {
        log_flusher_mutex_exit(log);

        /* When we are asked to stop threads, do not respect the limit
        for flushes per second. */
        if (!log.should_stop_threads.load()) {
          os_event_wait_time_low(log.flusher_event, flush_every - time_elapsed,
                                 0);
        }

        log_flusher_mutex_enter(log);
      }
    }

    const auto wait_stats = waiting.wait(stop_condition);

    MONITOR_INC_WAIT_STATS(MONITOR_LOG_FLUSHER_, wait_stats);
  }

  if (log.write_lsn.load() > log.flushed_to_disk_lsn.load()) {
    log_flush_low(log);
  }

  ut_a(log.write_lsn.load() == log.flushed_to_disk_lsn.load());

  log_flusher_mutex_exit(log);
}
```

fsync 한 번과 알림이다.

`storage` / `innobase` / `log` / `log0write.cc` L2421-L2493 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L2421-L2493))

```cpp
// log0write.cc L2421-L2493
static void log_flush_low(log_t &log) {
  ut_ad(log_flusher_mutex_own(log));

#ifndef _WIN32
  bool do_flush = srv_unix_file_flush_method != SRV_UNIX_O_DSYNC;
#else
  bool do_flush = true;
#endif

  if (!log.writer_threads_paused.load(std::memory_order_acquire)) {
    os_event_reset(log.flusher_event);
  }

  const lsn_t last_flush_lsn = log.flushed_to_disk_lsn.load();

  const lsn_t flush_up_to_lsn = log.write_lsn.load();

  if (flush_up_to_lsn == last_flush_lsn) {
    os_event_set(log.old_flush_event);
    return;
  }

  log.last_flush_start_time = Log_clock::now();

  ut_a(flush_up_to_lsn > last_flush_lsn);

  if (do_flush) {
    log_sync_point("log_flush_before_fsync");
    log.m_current_file_handle.fsync();
  }

  log.last_flush_end_time = Log_clock::now();

  if (log.last_flush_end_time < log.last_flush_start_time) {
    /* Time was moved backward after we set start_time.
    Let assume that the fsync operation was instant.

    We move start_time backward, because we don't want
    it to remain in the future. */
    log.last_flush_start_time = log.last_flush_end_time;
  }

  log_sync_point("log_flush_before_flushed_to_disk_lsn");

  log.flushed_to_disk_lsn.store(flush_up_to_lsn);

  /* Notify other thread(s). */

  DBUG_PRINT("ib_log", ("Flushed to disk up to " LSN_PF, flush_up_to_lsn));

  if (!log.writer_threads_paused.load(std::memory_order_acquire)) {
    const auto first_slot =
        log_compute_flush_event_slot(log, last_flush_lsn + 1);

    const auto last_slot = log_compute_flush_event_slot(log, flush_up_to_lsn);

    if (first_slot == last_slot) {
      log_sync_point("log_flush_before_users_notify");
      os_event_set(log.flush_events[first_slot]);
    } else {
      log_sync_point("log_flush_before_notifier_notify");
      os_event_set(log.flush_notifier_event);
    }
  } else {
    log_sync_point("log_flush_before_users_notify");
    log_sync_point("log_flush_before_notifier_notify");
    os_event_set(log.old_flush_event);
  }

  /* Update stats. */

  log_flush_update_stats(log);
}
```

커밋 쪽에서 이 스레드를 기다리는 방식이 설정값으로 갈린다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L1724-L1750 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L1724-L1750))

```cpp
// trx0trx.cc L1724-L1750
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
```

## 동작 흐름

```text
 L2503  flusher_mutex 를 쥐고 시작
 L2505  for (step = 0;; ++step)
 L2506    종료 요청이고 writer 가 죽었으면 break      (마지막 fsync 는 L2613)
 L2515    paused 면 resume 을 기다린다
 L2573    flush_log_at_trx_commit != 1 이면
 L2586      지난 fsync 시작부터 흐른 시간
 L2594      flush_every 보다 짧으면 남은 시간만큼 flusher_event 로 잔다
 L2608    waiting.wait(stop_condition)
            L2538  flushed_to_disk_lsn < write_lsn 이면
            L2540    log_flush_low
                       L2436  flush_up_to_lsn = write_lsn          읽은 순간의 값까지만
                       L2447  do_flush 면 fsync                 (L2425, O_DSYNC 이면 fsync 하지 않는다)
                       L2465  flushed_to_disk_lsn.store(flush_up_to_lsn)
                       L2477  슬롯 하나면 flush_events[slot] 직접, 아니면 flush_notifier
 L2613  끝나기 전 남은 것 fsync
 L2617  write_lsn == flushed_to_disk_lsn 으로 끝난다
```

```text
 innodb_flush_log_at_trx_commit 에 따른 커밋의 대기 (trx0trx.cc L1735-L1749)

 value   commit calls                      log_flusher 를 깨우는 것
 1       log_write_up_to(lsn, true)        log_writer 가 write 마다 flusher_event (L1562)
 2       log_write_up_to(lsn, false)       flush_log_at_timeout 주기 (L2573-L2605)
 0       (none)                            flush_log_at_timeout 주기

 1 만 커밋 응답 전에 fsync 를 기다린다
 2 는 OS 버퍼(write_lsn)까지만 기다린다
 NOSYNC 파일 모드면 1 이어도 flush = false 로 시작한다 (L1730)
```

```text
 한 트랜잭션 커밋의 시간축 (flush_log_at_trx_commit = 1)

 사용자 스레드            log_writer                 log_flusher
 ----------------------   ------------------------   ---------------------------
 mtr.commit
   recent_written 링크
 log_write_up_to(L, true)
   flush_events[slot(L)]
   에서 잔다              ready_lsn >= L
                          write -> write_lsn >= L
                          flusher_event set   -->    fsync
                                                     flushed_to_disk_lsn >= L
                             <----------------------  flush_events[slot] set
 깨어나 응답
```

## 결과가 쓰이는 곳

```text
 flushed_to_disk_lsn
      --> 커밋 대기자 (log_write_up_to(lsn, true))                  [커밋과 binlog 2PC]
      --> buf_flush_write_block_low 가 newest_modification 과 비교  [페이지 플러시...]
      --> log_compute_available_for_checkpoint_lsn 이 checkpoint 상한으로 쓴다
      --> NO_REDO 로 더럽힌 페이지의 newest_modification 하한 (buf0flu.cc L420-L421)
```

## 다루지 않는 것

`log_flush_notifier` 스레드가 여러 슬롯을 깨우는 과정, `log_flush_update_stats` 의 통계, `writer_threads_paused` 일 때의 `old_flush_event` 경로, Windows 분기는 요약만 했다.
