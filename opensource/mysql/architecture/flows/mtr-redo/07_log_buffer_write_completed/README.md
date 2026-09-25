# log_buffer_write_completed

상위: [mini-transaction과 redo 기록](../README.md)

**"이 범위는 다 복사했다"를 log writer 에게 알리는 방법이다.** 알림은 메시지가 아니라 `log.recent_written` 링 버퍼의 슬롯 하나에 `start_lsn -> end_lsn` 링크를 거는 것이다. log writer 는 링크를 따라가다 끊긴 곳에서 멈추므로, 먼저 끝난 스레드가 뒤쪽 범위에 링크를 걸어도 앞쪽 구멍이 메워지기 전에는 파일로 나가지 않는다. 링크를 걸기 전의 release 펜스가 "복사가 링크보다 먼저 보인다"를 보장한다(log0buf.cc L299-L302 주석).

## 위치

`storage` / `innobase` / `log` / `log0buf.cc` L1083-L1147 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L1083-L1147))

## 실제 코드

`storage` / `innobase` / `log` / `log0buf.cc` L1083-L1147 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L1083-L1147))

```cpp
// log0buf.cc L1083-L1147
void log_buffer_write_completed(log_t &log, lsn_t start_lsn, lsn_t end_lsn,
                                bool is_last_block) {
  ut_ad(rw_lock_own(log.sn_lock_inst, RW_LOCK_S));

  ut_a(log_is_data_lsn(start_lsn));
  ut_a(log_is_data_lsn(end_lsn));
  ut_a(end_lsn > start_lsn);

  /* Wait for start_lsn to fit in the window, so we can add the edge into its
  corresponding slot. */

  uint64_t wait_loops = 0;

  while (!log.recent_written.has_space(start_lsn)) {
    os_event_set(log.writer_event);
    ++wait_loops;
    std::this_thread::sleep_for(std::chrono::microseconds(20));
  }

  if (unlikely(wait_loops != 0)) {
    MONITOR_INC_VALUE(MONITOR_LOG_ON_RECENT_WRITTEN_WAIT_LOOPS, wait_loops);
  }

  /* Disallow reordering of writes to log buffer after this point.
  This is actually redundant, because we use seq_cst inside the
  log.recent_written.add_link(). However, we've decided to leave
  the separate acq-rel synchronization between user threads and
  log writer. Reasons:
          1. Not to rely on internals of Link_buf::add_link.
          2. Stress that this synchronization is required in
             case someone decided to weaken memory ordering
             inside Link_buf. */
  std::atomic_thread_fence(std::memory_order_release);

  log_sync_point("log_buffer_write_completed_before_store");

  ut_ad(log.write_lsn.load() <= start_lsn);
  ut_ad(log_buffer_ready_for_write_lsn(log) <= start_lsn);

  /*
   This may release the s-latch on the log_buffer as we add the link for
   the last fragment of the reserved range of the log_buffer.
  */
  if (is_last_block) log_buffer_s_lock_exit(log);

  /* Note that end_lsn will not point to just before footer,
  because we have already validated that end_lsn is valid. */
  log.recent_written.add_link_advance_tail(start_lsn, end_lsn);

  /* if someone is waiting for, set the event. (if possible) */
  lsn_t ready_lsn = log_buffer_ready_for_write_lsn(log);

  if (log.current_ready_waiting_lsn > 0 &&
      log.current_ready_waiting_lsn <= ready_lsn &&
      !os_event_is_set(log.closer_event) &&
      log_closer_mutex_enter_nowait(log) == 0) {
    if (log.current_ready_waiting_lsn > 0 &&
        log.current_ready_waiting_lsn <= ready_lsn &&
        !os_event_is_set(log.closer_event)) {
      log.current_ready_waiting_lsn = 0;
      os_event_set(log.closer_event);
    }
    log_closer_mutex_exit(log);
  }
}
```

## 동작 흐름

```text
 L1085  log buffer s-lock 을 쥐고 있다
 L1096  while (!recent_written.has_space(start_lsn))
 L1097    writer_event 를 깨우고            log_writer 가 앞쪽 링크를 치워 줘야 자리가 난다
 L1099    20us sleep
 L1102  기다렸으면 MONITOR_LOG_ON_RECENT_WRITTEN_WAIT_LOOPS 에 더한다
 L1115  atomic_thread_fence(release)        log buffer 쓰기가 링크보다 먼저 보이게
 L1126  is_last_block 이면 log_buffer_s_lock_exit   [05] 에서 잡은 s-lock 을 여기서 푼다
 L1130  recent_written.add_link_advance_tail(start_lsn, end_lsn)
          slot[start_lsn % S] = end_lsn 을 걸고, 이어지면 tail 도 밀어 본다
 L1133  ready_lsn = ready_for_write_lsn
 L1135  current_ready_waiting_lsn 을 기다리는 쪽이 있고 이제 ready 가 넘었으면
 L1143    closer_event 를 set                (L1138 nowait mutex 로 한 스레드만)
```

`recent_written` 은 lsn 으로 직접 주소를 매기는 링크 버퍼다. 슬롯 값은 "여기서 시작한 쓰기가 어디서 끝났는가" 이고, tail 은 "여기까지는 구멍이 없다" 이다.

```text
 recent_written (크기 S, 기본 1MB, log0constants.h L494)

 lsn    100        180        260        340        420
         |          |          |          |          |
 slot   [180]      [ 0 ]      [340]      [420]      [ 0 ]
         A 가 걸었음 B 아직     C 가 걸었음 D 가 걸었음
         ^
         tail = ready_for_write_lsn

 log_writer 가 따라가면  100 -> 180 -> (slot[180] = 0, 끊김)  멈춤
   ready_for_write_lsn = 180. C, D 가 먼저 끝났어도 B 가 끝나기 전에는 파일로 못 간다
 B 가 slot[180] = 260 을 걸면
   100 -> 180 -> 260 -> 340 -> 420   ready_for_write_lsn = 420
 지나간 슬롯은 0 으로 지워져 lsn + S 에서 다시 쓰인다
```

```text
 has_space(start_lsn) 의 뜻

   start_lsn - ready_for_write_lsn <= S       (log0buf.cc L279 주석)

 한 스레드가 복사 중에 멈추면 그 뒤로 S 바이트까지만 다른 스레드가 앞서갈 수 있다
 그 너머의 스레드는 여기서 20us 씩 잔다
```

## 결과가 쓰이는 곳

```text
 recent_written 링크
      --> [09] log_writer 의 log_advance_ready_for_write_lsn 이 advance_tail_until 로 따라간다
          (한 번에 srv_log_write_max_size 까지만, log0buf.cc L1286)

 s-lock 해제 (마지막 블록)
      --> log_buffer_x_lock_enter 를 기다리는 쪽이 이 lsn 까지 tail 이 오면 진행한다
          (log0buf.cc L312-L316 주석)

 closer_event
      --> log_buffer_wait_for_ready_for_write_lsn 으로 기다리던 스레드를 깨운다
```

## 다루지 않는 것

`Link_buf` 의 구현(슬롯 원자 연산, `advance_tail_until` 의 정지 조건)과 `closer_event` 를 기다리는 호출처(`log_buffer_wait_for_ready_for_write_lsn` 를 부르는 곳)는 요약만 했다.
