# log_checkpoint

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**checkpoint LSN 을 정하고, 그 앞의 페이지가 정말 디스크에 있게 한 뒤 [10] 으로 넘긴다.** 값 자체는 미리 계산된 `available_for_checkpoint_lsn` 을 읽는 것이고, 그 계산이 이 흐름의 핵심이다. 세 상한의 최솟값이다. flush list 에 남은 가장 오래된 변경(느슨한 순서만큼 `order_lag` 를 빼서), 아직 flush list 에 붙지 못한 mtr 의 시작(`smallest_not_added_lsn`), 디스크에 있는 redo 의 끝(`flushed_to_disk_lsn`). 그리고 적기 직전 `buf_flush_fsync` 로 데이터 파일을 fsync 한다.

## 위치

`storage` / `innobase` / `log` / `log0chkp.cc` L444-L504 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L444-L504))

## 실제 코드

`storage` / `innobase` / `log` / `log0chkp.cc` L444-L504 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L444-L504))

```cpp
// log0chkp.cc L444-L504
static void log_checkpoint(log_t &log) {
  ut_ad(log_checkpointer_mutex_own(log));
  ut_a(!srv_read_only_mode);
  ut_ad(!srv_checkpoint_disabled);
  ut_ad(log.m_allow_checkpoints.load());

  /* Read the comment from log_should_checkpoint() from just before
  acquiring the limits mutex. It is ok if available_for_checkpoint_lsn
  is advanced just after we released limits_mutex here. It can only be
  increased. Also, if the value for which we will write checkpoint is
  higher than the value for which we decided that it is worth to write
  checkpoint (in log_should_checkpoint) - it is even better for us. */

  const lsn_t checkpoint_lsn = log_determine_checkpoint_lsn(log);

  if (arch_page_sys != nullptr) {
    arch_page_sys->flush_at_checkpoint(checkpoint_lsn);
  }

  log_sync_point("log_before_checkpoint_data_flush");

  buf_flush_fsync();

  if (log_test != nullptr) {
    log_test->fsync_written_pages();
  }

  ut_a(checkpoint_lsn >= log.last_checkpoint_lsn.load());

  ut_a(checkpoint_lsn <= buf_flush_list_added->smallest_not_added_lsn());

#ifdef UNIV_DEBUG
  if (checkpoint_lsn > log.flushed_to_disk_lsn.load()) {
    /* We need log_flusher, because we need redo flushed up
    to the oldest_lsn, and it's not been flushed yet. */

    log_background_threads_active_validate(log);
  }
#endif

  ut_a(log.flushed_to_disk_lsn.load() >= checkpoint_lsn);

  const auto current_time = std::chrono::high_resolution_clock::now();

  log.last_checkpoint_time = current_time;

  DBUG_PRINT("ib_log", ("Starting checkpoint at " LSN_PF, checkpoint_lsn));

  const dberr_t err = log_files_next_checkpoint(log, checkpoint_lsn);
  if (err != DB_SUCCESS) {
    return;
  }

  DBUG_PRINT("ib_log",
             ("checkpoint ended at " LSN_PF ", log flushed to " LSN_PF,
              log.last_checkpoint_lsn.load(), log.flushed_to_disk_lsn.load()));

  MONITOR_INC(MONITOR_LOG_CHECKPOINTS);

  DBUG_EXECUTE_IF("crash_after_checkpoint", DBUG_SUICIDE(););
}
```

값을 읽는 곳이다. dict 쪽 제한이 있으면 그보다 앞으로 가지 않는다.

`storage` / `innobase` / `log` / `log0chkp.cc` L316-L335 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L316-L335))

```cpp
// log0chkp.cc L316-L335
static lsn_t log_determine_checkpoint_lsn(log_t &log) {
  ut_ad(log_checkpointer_mutex_own(log));
  ut_ad(log.m_allow_checkpoints.load());

  log_limits_mutex_enter(log);

  const lsn_t oldest_lsn = log.available_for_checkpoint_lsn;

  const lsn_t dict_lsn = log.dict_max_allowed_checkpoint_lsn;

  log_limits_mutex_exit(log);

  ut_a(dict_lsn == 0 || dict_lsn >= log.last_checkpoint_lsn.load());

  if (dict_lsn == 0) {
    return oldest_lsn;
  } else {
    return std::min(oldest_lsn, dict_lsn);
  }
}
```

값을 계산하는 곳이다. 주석이 순서(1~4)와 이유를 적어 두었다.

`storage` / `innobase` / `log` / `log0chkp.cc` L181-L268 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L181-L268))

```cpp
// log0chkp.cc L181-L268
static lsn_t log_compute_available_for_checkpoint_lsn(const log_t &log) {
  /* The buf_flush_list_added->smallest_not_added_lsn() can only increase,
  and that happens only after all related dirty pages have been added
  to the flush lists.

  Hence, to avoid issues related to race conditions, we follow order:

          1. Note lsn up to which all dirty pages have already been
             added to flush lists.

          2. Check buffer pool to get LWM lsn for unflushed dirty pages
             added to flush lists.

          3. Flush lists were empty (no LWM) => use [1] as LWM.

          4. Checkpoint LSN could be min(LWM, flushed_to_disk_lsn). */

  log_sync_point("log_get_available_for_chkp_lsn_before_dpa");

  const lsn_t dpa_lsn = buf_flush_list_added->smallest_not_added_lsn();

  ut_ad(dpa_lsn >= log.last_checkpoint_lsn.load() ||
        !log_checkpointer_mutex_own(log));

  log_sync_point("log_get_available_for_chkp_lsn_before_buf_pool");

  lsn_t lwm_lsn = buf_pool_get_oldest_modification_lwm();

  /* We cannot return lsn larger than dpa_lsn,
  because some mtr's commit could be in the middle, after
  its log records have been written to log buffer, but before
  its dirty pages have been added to flush lists. */

  if (lwm_lsn == 0) {
    /* Empty flush list. */
    lwm_lsn = dpa_lsn;
  } else {
    lwm_lsn = std::min(lwm_lsn, dpa_lsn);
  }

  /* Cannot go beyond flushed lsn.

  We cannot write checkpoint at higher lsn than lsn up to which
  redo is flushed to disk. We must not wait for log writer/flusher
  in log_checkpoint(). Therefore we need to limit lsn for checkpoint.
  That's because we would risk a deadlock otherwise - because writer
  waits for advanced checkpoint, when it detected that there is no
  free space in log files.

  However, note that the deadlock would happen only if we created
  log records without dirty pages (during page flush we anyway wait
  for redo flushed up to page's newest_modification). */

  const lsn_t flushed_lsn = log.flushed_to_disk_lsn.load();

  lsn_t lsn = std::min(lwm_lsn, flushed_lsn);

  /* We expect in recovery that checkpoint_lsn is within data area
  of log block. In future we could get rid of this assumption, but
  we would need to ensure that recovery handles that properly.

  For that, we would better refactor log0recv.cc and separate two
  phases:
          1. Looking for the proper mtr boundary to start at (only parse).
          2. Actual parsing and applying changes. */

  if (lsn % OS_FILE_LOG_BLOCK_SIZE == 0) {
    /* Do not make checkpoints at block boundary.

    We hopefully will get rid of this exception and allow
    recovery to start at arbitrary checkpoint value. */
    lsn = lsn - OS_FILE_LOG_BLOCK_SIZE + LOG_BLOCK_HDR_SIZE;
  }

  ut_a(lsn % OS_FILE_LOG_BLOCK_SIZE >= LOG_BLOCK_HDR_SIZE);

  ut_a(lsn % OS_FILE_LOG_BLOCK_SIZE <
       OS_FILE_LOG_BLOCK_SIZE - LOG_BLOCK_TRL_SIZE);

  lsn = std::max(lsn, log.last_checkpoint_lsn.load());

  ut_ad(lsn >= log.last_checkpoint_lsn.load() ||
        !log_checkpointer_mutex_own(log));

  ut_a(lsn <= log.flushed_to_disk_lsn.load());

  return lsn;
}
```

계산 결과는 커지기만 한다.

`storage` / `innobase` / `log` / `log0chkp.cc` L270-L298 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L270-L298))

```cpp
// log0chkp.cc L270-L298
static void log_update_available_for_checkpoint_lsn(log_t &log) {
  /* Note: log.m_allow_checkpoints is set to true after recovery is finished,
  and changes gathered in recv_sys->metadata_recover are applied to dict_table_t
  objects; or in log_start() if recovery was not needed. We can't trust
  flush lists until recovery is finished, so we must not update lsn available
  for checkpoint (as update would be based on what we can see inside them). */
  if (!log.m_allow_checkpoints.load(std::memory_order_acquire)) {
    return;
  }

  /* Update lsn available for checkpoint. */
  const lsn_t oldest_lsn = log_compute_available_for_checkpoint_lsn(log);

  log_limits_mutex_enter(log);

  /* 1. The oldest_lsn can decrease in case previously buffer pool flush
        lists were empty and now a new dirty page appeared, which causes
        a maximum delay of buf_flush_list_added->order_lag() being suddenly
        subtracted.

     2. Race between concurrent log_update_available_for_checkpoint_lsn is
        also possible. */

  if (oldest_lsn > log.available_for_checkpoint_lsn) {
    log.available_for_checkpoint_lsn = oldest_lsn;
  }

  log_limits_mutex_exit(log);
}
```

flush list 쪽 값이다. 인스턴스마다 꼬리 쪽에서 임시 테이블스페이스가 아닌 첫 페이지의 oldest 를 읽고, 최솟값에서 `order_lag` 를 뺀다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L435-L513 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L435-L513))

```cpp
// buf0buf.cc L435-L513
lsn_t buf_pool_get_oldest_modification_approx(void) {
  lsn_t lsn = 0;
  lsn_t oldest_lsn = 0;

  /* When we traverse all the flush lists we don't care if previous
  flush lists changed. We do not require consistent result. */

  for (ulint i = 0; i < srv_buf_pool_instances; i++) {
    buf_pool_t *buf_pool;

    buf_pool = buf_pool_from_array(i);

    buf_flush_list_mutex_enter(buf_pool);

    buf_page_t *bpage;

    /* We don't let log-checkpoint halt because pages from system
    temporary are not yet flushed to the disk. Anyway, object
    residing in system temporary doesn't generate REDO logging. */
    bpage = buf_pool->oldest_hp.get();
    if (bpage != nullptr) {
      ut_ad(bpage->in_flush_list);
    } else {
      bpage = UT_LIST_GET_LAST(buf_pool->flush_list);
    }

    for (; bpage != nullptr && fsp_is_system_temporary(bpage->id.space());
         bpage = UT_LIST_GET_PREV(list, bpage)) {
      /* Do nothing. */
    }

    if (bpage != nullptr) {
      ut_ad(bpage->in_flush_list);
      lsn = bpage->get_oldest_lsn();
      buf_pool->oldest_hp.set(bpage);
    } else {
      /* The last scanned page as entry point, or nullptr. */
      buf_pool->oldest_hp.set(UT_LIST_GET_FIRST(buf_pool->flush_list));
    }

    buf_flush_list_mutex_exit(buf_pool);

    if (!oldest_lsn || oldest_lsn > lsn) {
      oldest_lsn = lsn;
    }
  }

  /* The returned answer may be out of date: the flush_list can
  change after the mutex has been released. */

  return (oldest_lsn);
}

lsn_t buf_pool_get_oldest_modification_lwm(void) {
  const lsn_t lsn = buf_pool_get_oldest_modification_approx();

  if (lsn == 0) {
    return (0);
  }

  ut_a(lsn % OS_FILE_LOG_BLOCK_SIZE >= LOG_BLOCK_HDR_SIZE);

  const log_t &log = *log_sys;

  const lsn_t lag = buf_flush_list_added->order_lag();

  ut_a(lag % OS_FILE_LOG_BLOCK_SIZE == 0);

  const lsn_t checkpoint_lsn = log_get_checkpoint_lsn(log);

  ut_a(checkpoint_lsn != 0);

  if (lsn > lag) {
    return (std::max(checkpoint_lsn, lsn - lag));

  } else {
    return (checkpoint_lsn);
  }
}
```

## 동작 흐름

```text
 log_checkpoint
 L457  checkpoint_lsn = log_determine_checkpoint_lsn
         L322  oldest = available_for_checkpoint_lsn     (limits_mutex 아래)
         L333  dict_max_allowed_checkpoint_lsn 이 있으면 min
 L460  페이지 아카이브가 있으면 flush_at_checkpoint
 L465  buf_flush_fsync                                   데이터 파일 fsync (fil_flush_file_spaces, NOSYNC 면 건너뜀)
 L471  checkpoint_lsn >= last_checkpoint_lsn
 L473  checkpoint_lsn <= smallest_not_added_lsn
 L484  flushed_to_disk_lsn >= checkpoint_lsn
 L488  last_checkpoint_time = now
 L492  [10] log_files_next_checkpoint(checkpoint_lsn)

 log_compute_available_for_checkpoint_lsn (그 값을 만드는 곳)
 L200  dpa_lsn = smallest_not_added_lsn          1. 먼저 읽는다 (주석 L186-L196)
 L207  lwm_lsn = buf_pool_get_oldest_modification_lwm
         buf0buf.cc L447  인스턴스마다 flush_list_mutex
                    L454  oldest_hp 또는 LAST(flush_list) 에서 시작
                    L461  임시 테이블스페이스 페이지는 건너뛴다 (redo 가 없으므로, 주석 L451-L453)
                    L477  최솟값
                    L507  lsn > lag 면 max(checkpoint_lsn, lsn - order_lag)
 L214  flush list 가 비었으면 lwm = dpa
 L218  아니면 min(lwm, dpa)
 L236  lsn = min(lwm, flushed_to_disk_lsn)
 L247  블록 경계면 앞 블록의 데이터 영역으로 당긴다
 L260  max(lsn, last_checkpoint_lsn)
```

```text
 세 상한이 각각 막는 사고

 bound                     없으면 생기는 일
 oldest_lwm                디스크에 없는 페이지 변경의 redo 를 버린다
 smallest_not_added_lsn    log buffer 에는 썼지만 flush list 에 아직 안 붙은 mtr 의
                           페이지가 oldest 계산에서 빠진다 (log0buf.cc L430-L443 주석)
 flushed_to_disk_lsn       디스크에 없는 redo 위치를 checkpoint 로 적는다
                           checkpoint 가 log writer 를 기다리지 않게 하려는 상한 (주석 L221-L232)
```

```text
 order_lag 를 빼는 이유 (flush list 꼬리 = LAST)

 flush list  head [520] [500] [510] [300] [180] [ 95]  tail   (lag = 10 이라고 하자)
                                                 ^ LAST 의 oldest 는 95
 진짜 최솟값은 95 보다 작을 수 있다. 순서가 느슨해 꼬리가 최솟값이라는 보장이 없고,
 보장되는 것은 "최솟값보다 lag 이상 크지 않다" 뿐이다 (log0buf.cc L452-L457 주석)
   --> 95 - 10 = 85 를 이 flush list 의 안전한 값으로 쓴다
```

## 결과가 쓰이는 곳

```text
 checkpoint_lsn
      --> [10] 이 redo 파일 헤더에 적고 last_checkpoint_lsn 으로 저장한다

 available_for_checkpoint_lsn
      --> [08] log_sync_flush_lsn 이 sync flush 필요 여부를 이 값으로 잰다
      --> log_should_checkpoint 가 last_checkpoint 보다 큰지 본다
```

## 다루지 않는 것

`dict_max_allowed_checkpoint_lsn` 이 설정되는 경우(DD 메타데이터 기록 중), 페이지 아카이브(`arch_page_sys`), `buf_flush_fsync` 의 flush 방식별 분기(buf0flu.cc L3321-L3344), `oldest_hp` 해저드 포인터의 재사용 규칙은 요약만 했다.
