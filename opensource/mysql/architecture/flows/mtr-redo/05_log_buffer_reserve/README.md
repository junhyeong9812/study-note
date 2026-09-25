# log_buffer_reserve

상위: [mini-transaction과 redo 기록](../README.md)

**여러 사용자 스레드가 mutex 없이 log buffer 에 동시에 쓸 수 있게 만드는 한 줄이 여기 있다.** `log.sn.fetch_add(len)` 이 원자적으로 데이터 바이트 범위를 나눠 주고, 그 범위를 lsn 으로 바꾸면 log buffer 와 redo 파일 양쪽의 자리가 정해진다. 기다림은 두 경우뿐이다. log buffer 를 x-lock 한 스레드가 있을 때(`SN_LOCKED` 비트), 그리고 log buffer 가 아직 디스크로 안 나가 자리가 없을 때.

## 위치

`storage` / `innobase` / `log` / `log0buf.cc` L884-L932 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L884-L932))

## 실제 코드

`storage` / `innobase` / `log` / `log0buf.cc` L884-L932 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L884-L932))

```cpp
// log0buf.cc L884-L932
Log_handle log_buffer_reserve(log_t &log, size_t len) {
  Log_handle handle;

  /* In 5.7, we incremented log_write_requests for each single
  write to log buffer in commit of mini-transaction.

  However, writes which were solved by log_reserve_and_write_fast
  that missed to increment the counter. Therefore, it wasn't reliable.

  We changed meaning of the counter to reflect mtr commit rate. */
  srv_stats.log_write_requests.inc();

  ut_ad(srv_shutdown_state_matches([](auto state) {
    return state <= SRV_SHUTDOWN_FLUSH_PHASE ||
           state == SRV_SHUTDOWN_EXIT_THREADS;
  }));

  ut_a(len > 0);

  /* Reserve space in sequence of data bytes: */
  const sn_t start_sn = log_buffer_s_lock_enter_reserve(log, len);

  /* Ensure that redo log has been initialized properly. */
  ut_a(start_sn > 0);

#ifdef UNIV_DEBUG
  if (!recv_recovery_is_on()) {
    log_background_threads_active_validate(log);
  }
#endif

  /* Headers in redo blocks are not calculated to sn values: */
  const sn_t end_sn = start_sn + len;

  log_sync_point("log_buffer_reserve_before_buf_limit_sn");

  /* Translate sn to lsn (which includes also headers in redo blocks): */
  handle.start_lsn = log_translate_sn_to_lsn(start_sn);
  handle.end_lsn = log_translate_sn_to_lsn(end_sn);

  if (unlikely(end_sn > log.buf_limit_sn.load())) {
    log_wait_for_space_after_reserving(log, handle);
  }

  ut_a(log_is_data_lsn(handle.start_lsn));
  ut_a(log_is_data_lsn(handle.end_lsn));

  return handle;
}
```

예약의 실체다. s-lock 은 이름뿐이고 실제 동기화는 `fetch_add` 와 `SN_LOCKED` 비트가 한다(주석 L527-L541).

`storage` / `innobase` / `log` / `log0buf.cc` L527-L575 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L527-L575))

```cpp
// log0buf.cc L527-L575

/** Acquires an s-lock on the log buffer and reserves @p len bytes in it.
The corresponding unlock operation is log_buffer_s_lock_exit() which is
called during the log_buffer_write_completed(..) for the last fragment of
data copied to the reserved buffer - to be specific it happens after the
data is already copied to the log buffer, but right before the last missing
link is added to log.recent_written. The current implementation pretends
rw_lock_s_lock() is taken, while actually only the debug info and PSI info
typical for rw_lock_t are maintained, but no actual rw_lock_t is being used
for synchronization - that is achieved by using
log_t::sn (to inform s-locking threads about x-locker) and
log_t::recently_written (to inform x-locking thread when s-lockers have
finished). The resize does not use a read/write lock (rw_lock_t) due to
performance impact it would cause.
@param[in,out] log     redo log
@param[in]     len     number of data bytes to reserve for write
@return start sn of reserved */
static inline sn_t log_buffer_s_lock_enter_reserve(log_t &log, size_t len) {
#ifdef UNIV_PFS_RWLOCK
  PSI_rwlock_locker *locker = nullptr;
  PSI_rwlock_locker_state state;
  if (log.pfs_psi != nullptr) {
    if (log.pfs_psi->m_enabled) {
      /* Instrumented to inform we are acquiring a shared rwlock */
      locker = PSI_RWLOCK_CALL(start_rwlock_rdwait)(
          &state, log.pfs_psi, PSI_RWLOCK_SHAREDLOCK, __FILE__,
          static_cast<uint>(__LINE__));
    }
  }
#endif /* UNIV_PFS_RWLOCK */

  /* Reserve space in sequence of data bytes: */
  sn_t start_sn = log.sn.fetch_add(len);
  if (UNIV_UNLIKELY((start_sn & SN_LOCKED) != 0)) {
    start_sn &= ~SN_LOCKED;
    /* log.sn is locked. Should wait for unlocked. */
    log_buffer_s_lock_wait(log, start_sn);
  }

  ut_d(
      rw_lock_add_debug_info(log.sn_lock_inst, 0, RW_LOCK_S, UT_LOCATION_HERE));
#ifdef UNIV_PFS_RWLOCK
  if (locker != nullptr) {
    PSI_RWLOCK_CALL(end_rwlock_rdwait)(locker, 0);
  }
#endif /* UNIV_PFS_RWLOCK */

  return start_sn;
}
```

sn 은 블록 헤더와 트레일러를 뺀 순수 데이터 바이트 수이고, lsn 은 그것을 포함한 위치다.

`storage` / `innobase` / `include` / `log0log.h` L85-L88 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/log0log.h#L85-L88))

```cpp
// log0log.h L85-L88
constexpr inline lsn_t log_translate_sn_to_lsn(sn_t sn) {
  return sn / LOG_BLOCK_DATA_SIZE * OS_FILE_LOG_BLOCK_SIZE +
         sn % LOG_BLOCK_DATA_SIZE + LOG_BLOCK_HDR_SIZE;
}
```

log buffer 에 자리가 없으면 log writer 가 앞쪽을 써 줄 때까지 기다린다.

`storage` / `innobase` / `log` / `log0buf.cc` L857-L882 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L857-L882))

```cpp
// log0buf.cc L857-L882
static void log_wait_for_space_in_log_buf(log_t &log, sn_t end_sn) {
  lsn_t lsn;
  Wait_stats wait_stats;

  const sn_t write_sn = log_translate_lsn_to_sn(log.write_lsn.load());

  log_sync_point("log_wait_for_space_in_buf_middle");

  const sn_t buf_size_sn = log.buf_size_sn.load();

  if (end_sn + OS_FILE_LOG_BLOCK_SIZE <= write_sn + buf_size_sn) {
    return;
  }

  /* We preserve this counter for backward compatibility with 5.7. */
  srv_stats.log_waits.inc();

  lsn = log_translate_sn_to_lsn(end_sn + OS_FILE_LOG_BLOCK_SIZE - buf_size_sn);

  wait_stats = log_write_up_to(log, lsn, false);

  MONITOR_INC_WAIT_STATS(MONITOR_LOG_ON_BUFFER_SPACE_, wait_stats);

  ut_a(end_sn + OS_FILE_LOG_BLOCK_SIZE <=
       log_translate_lsn_to_sn(log.write_lsn.load()) + buf_size_sn);
}
```

## 동작 흐름

```text
 L894  log_write_requests++           (mtr commit 횟수, 주석 L887-L892)
 L901  len > 0
 L904  start_sn = log_buffer_s_lock_enter_reserve(len)
         L559  start_sn = log.sn.fetch_add(len)          원자적 예약, 여기서 범위가 확정된다
         L560  SN_LOCKED 비트가 서 있으면 (log_buffer_x_lock 중, log0constants.h L162)
         L561    비트를 떼고
         L563    log_buffer_s_lock_wait(start_sn)        x-lock 이 풀리거나 잠긴 지점 sn_locked 가 start_sn 뒤면 통과
 L916  end_sn    = start_sn + len
 L921  start_lsn = log_translate_sn_to_lsn(start_sn)
 L922  end_lsn   = log_translate_sn_to_lsn(end_sn)
 L924  end_sn > log.buf_limit_sn 이면
 L925    log_wait_for_space_after_reserving(handle)
           L857 log_wait_for_space_in_log_buf
             L867  end_sn + 512 <= write_sn + buf_size_sn 이면 통과
             L874  아니면 log_write_up_to(그 차이만큼, flush=false)   --> log_writer 를 기다린다
 L928  start_lsn, end_lsn 은 둘 다 블록의 데이터 영역을 가리킨다 (ut_a)
 L931  return handle                   s-lock 은 쥔 채로 나간다 ([07] 의 마지막 블록에서 푼다)
```

sn 과 lsn 의 관계는 한 줄 공식이다. 블록 크기가 512 바이트, 헤더 12, 트레일러 4 이므로 블록마다 데이터는 496 바이트다(log0constants.h L297, L306, L312, os0file.h L192).

```text
 sn -> lsn (log0log.h L85-L88)

   lsn = sn / 496 * 512 + sn % 496 + 12

 sn  (데이터 바이트만 센다)
   0                      496                    992
   |----------------------|----------------------|------
 lsn (블록 헤더 12 와 트레일러 4 를 포함한 위치)
   |hdr|<---- 496 ---->|trl|hdr|<---- 496 ---->|trl|hdr|
   0   12              508 512 524             1020 1024
       ^ sn 0 = lsn 12     ^ sn 496 = lsn 524

 그래서 mtr 이 len 바이트를 예약하면 end_lsn - start_lsn 은
 블록 경계를 몇 번 넘느냐에 따라 len, len + 16, len + 32 ... 이 된다
```

```text
 commit 동안 사용자 스레드가 멈출 수 있는 네 곳

 where   condition                  wait                    기다리는 대상
 L560    SN_LOCKED bit              spin, sn_lock_event     log_buffer_x_lock 을 쥔 스레드
 L924    end_sn > buf_limit_sn      log_write_up_to         log_writer 가 write_lsn 을 올리기
 [07]    recent_written no space    sleep 20us loop         log_writer 가 링크를 치우기
 [04]    wait_to_add                sleep 20us loop         앞선 mtr 들의 report_added
```

설계 주석(L161-L190)은 redo 파일 공간 부족도 예약 단계의 대기로 적어 두었지만, 이 함수 본문에는 그 검사가 없다. 파일 공간은 사용자 스레드가 래치를 쥐지 않은 때 부르는 `log_free_check`(주석 L186-L190)와 log writer 의 `log_writer_wait_on_checkpoint` 가 맡는다([09]).

## 결과가 쓰이는 곳

```text
 handle (start_lsn, end_lsn)
      --> [06] log_buffer_write 가 log.buf + start_lsn % buf_size 부터 복사한다
      --> [08] 에서 페이지의 oldest / newest_modification 이 된다
      --> end_lsn 은 mtr 의 commit_lsn 이 된다

 쥔 채로 나간 s-lock
      --> [07] log_buffer_write_completed 가 마지막 조각에서 log_buffer_s_lock_exit 로 푼다
```

## 다루지 않는 것

log buffer 크기 변경(`log_buffer_x_lock_enter`, `log_wait_for_space_after_reserving` 의 resize 분기), Performance Schema rwlock 계측, `log_free_check` 의 여유 공간 계산(`log_free_check_margin`, `log_concurrency_margin`)은 요약만 했다.
