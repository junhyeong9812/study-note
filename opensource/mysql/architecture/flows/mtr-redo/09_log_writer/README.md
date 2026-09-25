# log_writer

상위: [mini-transaction과 redo 기록](../README.md)

**log buffer 를 redo 파일로 옮기는 전용 스레드다.** 사용자 스레드가 건 `recent_written` 링크를 따라가 구멍 없는 끝(`ready_for_write_lsn`)을 찾고, `write_lsn` 부터 거기까지를 OS 버퍼로 write 한 뒤 `write_lsn` 을 올린다. fsync 는 하지 않는다(그것은 [10] log_flusher). 쓰기 전에 한 가지를 더 확인한다. redo 파일에 자리가 없으면, 즉 checkpoint 가 충분히 앞으로 가지 않았으면 쓰지 않고 기다린다. 이 대기가 redo 공간과 [페이지 플러시...](../../flush-checkpoint/README.md)를 잇는 고리다.

## 위치

`storage` / `innobase` / `log` / `log0write.cc` L2230-L2320 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L2230-L2320))

## 실제 코드

스레드 본체다. `stop_condition` 람다가 "쓸 것이 생겼나"를 보고, 그동안은 spin 뒤 `writer_event` 로 잔다.

`storage` / `innobase` / `log` / `log0write.cc` L2230-L2320 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L2230-L2320))

```cpp
// log0write.cc L2230-L2320
void log_writer(log_t *log_ptr) {
  ut_a(log_ptr != nullptr);

  log_t &log = *log_ptr;
  lsn_t ready_lsn = 0;

  ut_d(log.m_writer_thd = create_internal_thd());

  log_writer_mutex_enter(log);

  Log_thread_waiting waiting{log, log.writer_event, srv_log_writer_spin_delay,
                             get_srv_log_writer_timeout()};

  Log_write_to_file_requests_monitor write_to_file_requests_monitor{log};

  for (uint64_t step = 0;; ++step) {
    bool released = false;

    auto stop_condition = [&ready_lsn, &log, &released,
                           &write_to_file_requests_monitor](bool wait) {
      if (released) {
        log_writer_mutex_enter(log);
        released = false;
      }

      /* Advance lsn up to which data is ready in log buffer. */
      log_advance_ready_for_write_lsn(log);

      ready_lsn = log_buffer_ready_for_write_lsn(log);

      /* Wait until any of following conditions holds:
              1) There is some unwritten data in log buffer
              2) We should close threads. */

      if (log.write_lsn.load() < ready_lsn || log.should_stop_threads.load()) {
        return true;
      }

      if (UNIV_UNLIKELY(
              log.writer_threads_paused.load(std::memory_order_acquire))) {
        return true;
      }

      if (wait) {
        write_to_file_requests_monitor.update();
        log_writer_mutex_exit(log);
        released = true;
      }

      return false;
    };

    const auto wait_stats = waiting.wait(stop_condition);

    MONITOR_INC_WAIT_STATS(MONITOR_LOG_WRITER_, wait_stats);

    if (UNIV_UNLIKELY(
            log.writer_threads_paused.load(std::memory_order_acquire) &&
            !log.should_stop_threads.load())) {
      log_writer_mutex_exit(log);

      os_event_wait(log.writer_threads_resume_event);

      log_writer_mutex_enter(log);
      ready_lsn = log_buffer_ready_for_write_lsn(log);
    }

    /* Do the actual work. */
    if (log.write_lsn.load() < ready_lsn) {
      log_writer_write_buffer(log, ready_lsn);

      if (step % 1024 == 0) {
        write_to_file_requests_monitor.update();

        log_writer_mutex_exit(log);

        std::this_thread::yield();

        log_writer_mutex_enter(log);
      }

    } else if (log.should_stop_threads.load() &&
               log_writer_is_allowed_to_stop(log)) {
      break;
    }
  }

  log_writer_mutex_exit(log);

  ut_d(destroy_internal_thd(log.m_writer_thd));
}
```

링크를 따라가는 곳이다. 한 번에 `srv_log_write_max_size` 만큼만 전진한다.

`storage` / `innobase` / `log` / `log0buf.cc` L1267-L1311 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L1267-L1311))

```cpp
// log0buf.cc L1267-L1311
void log_advance_ready_for_write_lsn(log_t &log) {
  ut_ad(log_writer_mutex_own(log));
  ut_d(log_writer_thread_active_validate());

  const lsn_t write_lsn = log.write_lsn.load();

  const auto write_max_size = srv_log_write_max_size;

  ut_a(write_max_size > 0);

  auto stop_condition = [&](lsn_t prev_lsn, lsn_t next_lsn) {
    ut_a(log_is_data_lsn(prev_lsn));
    ut_a(log_is_data_lsn(next_lsn));

    ut_a(next_lsn > prev_lsn);
    ut_a(prev_lsn >= write_lsn);

    log_sync_point("log_advance_ready_for_write_before_reclaim");

    return prev_lsn - write_lsn >= write_max_size;
  };

  const lsn_t previous_lsn = log_buffer_ready_for_write_lsn(log);

  ut_a(previous_lsn >= write_lsn);

  if (log.recent_written.advance_tail_until(stop_condition)) {
    log_sync_point("log_advance_ready_for_write_before_update");

    /* Validation of recent_written is optional because
    it takes significant time (delaying the log writer). */
    if (log_test != nullptr &&
        log_test->enabled(Log_test::Options::VALIDATE_RECENT_WRITTEN)) {
      /* All links between ready_lsn and lsn have
      been traversed. The slots can't be re-used
      before we updated the tail. */
      log.recent_written.validate_no_links(previous_lsn,
                                           log_buffer_ready_for_write_lsn(log));
    }

    ut_a(log_buffer_ready_for_write_lsn(log) > previous_lsn);

    std::atomic_thread_fence(std::memory_order_acquire);
  }
}
```

한 번의 write 를 준비한다. 링 끝에서 자르고, checkpoint 가 허락하는 만큼으로 자른다.

`storage` / `innobase` / `log` / `log0write.cc` L2116-L2212 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L2116-L2212))

```cpp
// log0write.cc L2116-L2212
static void log_writer_write_buffer(log_t &log, lsn_t next_write_lsn) {
  ut_ad(log_writer_mutex_own(log));

  log_sync_point("log_writer_write_begin");

  const lsn_t last_write_lsn = log.write_lsn.load();

  ut_a(log_is_data_lsn(last_write_lsn) ||
       last_write_lsn % OS_FILE_LOG_BLOCK_SIZE == 0);

  ut_a(log_is_data_lsn(next_write_lsn) ||
       next_write_lsn % OS_FILE_LOG_BLOCK_SIZE == 0);

  ut_a(next_write_lsn - last_write_lsn <= log.buf_size);
  ut_a(next_write_lsn > last_write_lsn);

  size_t start_offset = last_write_lsn % log.buf_size;
  size_t end_offset = next_write_lsn % log.buf_size;

  if (start_offset >= end_offset) {
    ut_a(next_write_lsn - last_write_lsn >= log.buf_size - start_offset);

    end_offset = log.buf_size;
    next_write_lsn = last_write_lsn + (end_offset - start_offset);
  }
  ut_a(start_offset < end_offset);

  ut_a(end_offset % OS_FILE_LOG_BLOCK_SIZE == 0 ||
       end_offset % OS_FILE_LOG_BLOCK_SIZE >= LOG_BLOCK_HDR_SIZE);

  /* Wait until there is free space in log files.*/

  const lsn_t checkpoint_limited_lsn =
      log_writer_wait_on_checkpoint(log, last_write_lsn, next_write_lsn);

  ut_ad(log_writer_mutex_own(log));
  ut_a(checkpoint_limited_lsn > last_write_lsn);

  log_sync_point("log_writer_after_checkpoint_check");

  if (arch_log_sys != nullptr) {
    log_writer_wait_on_archiver(log, next_write_lsn);
  }

  ut_ad(log_writer_mutex_own(log));

  log_sync_point("log_writer_after_archiver_check");

  const lsn_t limit_for_next_write_lsn = checkpoint_limited_lsn;

  if (limit_for_next_write_lsn < next_write_lsn) {
    end_offset -= next_write_lsn - limit_for_next_write_lsn;
    next_write_lsn = limit_for_next_write_lsn;

    ut_a(end_offset > start_offset);
    ut_a(end_offset % OS_FILE_LOG_BLOCK_SIZE == 0 ||
         end_offset % OS_FILE_LOG_BLOCK_SIZE >= LOG_BLOCK_HDR_SIZE);

    ut_a(log_is_data_lsn(next_write_lsn) ||
         next_write_lsn % OS_FILE_LOG_BLOCK_SIZE == 0);
  }

  log_writer_wait_on_consumers(log, next_write_lsn);
  ut_ad(log_writer_mutex_own(log));
  /* We do hold the log->writer_mutex now, but log_writer_wait_on_checkpoint(),
  log_writer_wait_on_archiver(), or log_writer_wait_on_consumers() could have
  released it for a moment. So, in case --innodb_log_writer_threads=OFF, another
  thread could have already performed a write to the redo log, in which case we
  should not even try to (over)write it again. In extreme case, the log buffer
  already contains a different range of lsns, we might have moved to another
  file, or even removed the old one, etc. If we detect that any write has
  happened, we let the caller retry.*/
  if (last_write_lsn != log.write_lsn.load()) {
    return;
  }

  DBUG_PRINT("ib_log",
             ("write " LSN_PF " to " LSN_PF, last_write_lsn, next_write_lsn));

  byte *buf_begin =
      log.buf + ut_uint64_align_down(start_offset, OS_FILE_LOG_BLOCK_SIZE);

  byte *buf_end = log.buf + end_offset;

  /* Do the write to the log files */

  const dberr_t err = log_write_buffer(
      log, buf_begin, buf_end - buf_begin,
      ut_uint64_align_down(last_write_lsn, OS_FILE_LOG_BLOCK_SIZE));

  if (UNIV_UNLIKELY(err != DB_SUCCESS)) {
    ut_a(log.write_lsn.load() == last_write_lsn);
    log_writer_write_failed(log, err);
  }

  log_sync_point("log_writer_write_end");
}
```

실제 write 뒤 `write_lsn` 을 올리고 알린다.

`storage` / `innobase` / `log` / `log0write.cc` L1778-L1800 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L1778-L1800))

```cpp
// log0write.cc L1778-L1800
  srv_stats.os_log_pending_writes.inc();

  /* Now, we know, that we are going to write completed
  blocks only (originally or copied and completed). */
  const dberr_t err = write_blocks(log, write_buf, write_size, real_offset);
  if (UNIV_UNLIKELY(err != DB_SUCCESS)) {
    return err;
  }

  log_sync_point("log_writer_before_lsn_update");

  const lsn_t old_write_lsn = log.write_lsn.load();

  const lsn_t new_write_lsn = start_lsn + lsn_advance;
  ut_a(new_write_lsn > log.write_lsn.load());

  log.write_lsn.store(new_write_lsn);

  notify_about_advanced_write_lsn(log, old_write_lsn, new_write_lsn);

  log_sync_point("log_writer_before_buf_limit_update");

  log_update_buf_limit(log, new_write_lsn);
```

`innodb_flush_log_at_trx_commit=1` 일 때만 flusher 를 바로 깨운다.

`storage` / `innobase` / `log` / `log0write.cc` L1558-L1564 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0write.cc#L1558-L1564))

```cpp
// log0write.cc L1558-L1564
static inline void notify_about_advanced_write_lsn(log_t &log,
                                                   lsn_t old_write_lsn,
                                                   lsn_t new_write_lsn) {
  if (!log.writer_threads_paused.load(std::memory_order_acquire)) {
    if (srv_flush_log_at_trx_commit == 1) {
      os_event_set(log.flusher_event);
    }
```

## 동작 흐름

```text
 log0write.cc
 L2238  writer_mutex 를 쥐고 시작한다 (기다릴 때만 놓는다)
 L2245  for (step = 0;; ++step)
 L2282    waiting.wait(stop_condition)                spin -> writer_event (timeout 있음)
            L2256  log_advance_ready_for_write_lsn      --> log0buf.cc L1293 advance_tail_until
                     L1286 ready - write_lsn >= write_max_size 면 멈춘다
            L2258  ready_lsn = ready_for_write_lsn
            L2264  write_lsn < ready_lsn 또는 종료 요청이면 깨어난다
 L2286    writer_threads_paused 면 resume 을 기다린다
 L2298    write_lsn < ready_lsn
 L2299      log_writer_write_buffer(ready_lsn)
              L2132  start_offset = write_lsn % buf_size, end_offset = ready % buf_size
              L2135  링을 넘으면 buf 끝까지만 (다음 바퀴에 나머지)
              L2148  checkpoint_limited_lsn = log_writer_wait_on_checkpoint(...)
              L2166  그보다 멀면 거기까지만 쓴다
              L2178  log_writer_wait_on_consumers
              L2188  그 사이 누가 먼저 썼으면 return (호출한 쪽이 다시 돈다)
              L2202  log_write_buffer(buf_begin, len, write_lsn 을 블록 경계로 내림)
                       L1733  prepare_full_blocks   완성 블록 헤더 채우기
                       L1782  write_blocks          OS 버퍼로 write
                       L1794  write_lsn.store(new_write_lsn)
                       L1796  notify_about_advanced_write_lsn
                                L1562 flush_log_at_trx_commit == 1 이면 flusher_event
                                L1593 슬롯 하나면 직접 write_events[slot], 아니면 write_notifier
                       L1800  log_update_buf_limit    [05] 의 buf_limit_sn 을 넓힌다
 L2301      1024 바퀴마다 mutex 를 놓고 yield
 L2311    종료 요청이고 다 썼으면 break
```

`log_writer_wait_on_checkpoint` 가 redo 파일의 논리 용량을 지킨다. checkpoint 가 앞으로 가지 않으면 log writer 가 멈추고, log writer 가 멈추면 [05] 에서 log buffer 자리를 기다리는 사용자 스레드도 멈춘다.

```text
 redo 파일 공간과 log writer (LSN 축)

  last_checkpoint_lsn                  write_lsn        ready_lsn
  |                                    |                |
  |<------ 복구에 필요한 redo -------->|<-- 쓸 차례 -->|
  +------------------------------------+----------------+---------> lsn
  |<----------------- hard_logical_capacity ------------------->|
                                                                ^ hard_limited_lsn
                                                                  (log0write.cc L1893-L1895)

 쓰는 범위는 hard_limited_lsn 에서 잘린다 (L2166-L2168)
 extra margin 검사(L1901)에 걸리면 pessimistic 으로 간다 (L1983, 함수 정의 L1904)
   L1925  checkpointer_event 를 깨운다
   L1927  한 블록이라도 쓸 자리가 있으면 그만큼 쓰고 돌아간다
          (주석: checkpoint 속도, 곧 page cleaner 속도에 맞춘다)
   L1963  아니면 log_request_checkpoint(log, false), 100us 씩 기다린다 (L1965-L1967)
   동기 checkpoint 를 요구하지 않는 이유는 주석 L1956-L1962:
   가장 오래된 dirty 페이지의 래치를 쥔 사용자 스레드가 log buffer 자리를
   기다리고 있을 수 있어서, 동기로 요구하면 교착이 된다
```

```text
 log_writer 와 사용자 스레드가 주고받는 것

 사용자 스레드                         log_writer
 ---------------------------------     ---------------------------------------
 [05] end_sn > buf_limit_sn 이면       write_lsn 을 올리고 L1800 에서
      log_write_up_to 로 기다린다  <--  buf_limit_sn 을 넓힌다
 [07] recent_written 자리 없으면       링크를 따라가며 슬롯을 비운다
      writer_event 를 깨우고 잔다  <--  (advance_tail_until)
 [07] 링크를 건다                 -->  L2256 에서 ready_lsn 이 오른다
 커밋 log_write_up_to(lsn, false) <--  write_events[slot] 또는 write_notifier
```

## 결과가 쓰이는 곳

```text
 write_lsn
      --> [10] log_flusher 가 flushed_to_disk_lsn < write_lsn 이면 fsync 한다
      --> log_files_governor 가 newest_needed_lsn 으로 쓴다 (log0files_governor.cc L606-L609)
      --> free_space 모니터 = soft_logical_capacity - (write_lsn - last_checkpoint_lsn)  (L1810-L1817)

 buf_limit_sn
      --> [05] log_buffer_reserve 가 이 값을 넘는 예약만 기다리게 한다
```

## 다루지 않는 것

write-ahead(`srv_log_write_ahead_size` 단위로 미리 써서 read-on-write 를 피하는 것, 주석 L231-L253)와 불완전 마지막 블록을 `write_ahead_buf` 에 복사해 쓰는 경로, 파일 경계에서 `start_next_file`, extra margin(`log_writer_enter_extra_margin`), redo 아카이버와 소비자 대기(`log_writer_wait_on_archiver`, `log_writer_wait_on_consumers`), `innodb_log_writer_threads=OFF` 에서 사용자 스레드가 직접 쓰는 `log_self_write_up_to` 는 요약만 했다.
