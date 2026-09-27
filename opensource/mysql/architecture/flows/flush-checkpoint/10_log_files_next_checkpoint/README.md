# log_files_next_checkpoint

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**checkpoint 를 실제로 적고, 그 결과로 redo 공간을 돌려주는 곳이다.** checkpoint LSN 이 속한 redo 파일의 헤더에 적고 fsync 한 뒤에야 `last_checkpoint_lsn` 을 올린다. 헤더에는 checkpoint 칸이 둘 있어 번갈아 쓴다. 이 값이 오르면 세 곳이 풀린다. log writer 의 쓰기 상한(`checkpoint + hard_logical_capacity`), 사용자 스레드의 `log_free_check` 상한(`free_check_limit_lsn`), 그리고 checkpoint 앞쪽의 redo 파일이다. 파일은 `log_files_governor` 스레드가 소비됨(consumed)으로 표시한 뒤 재활용하거나 지운다.

## 위치

`storage` / `innobase` / `log` / `log0chkp.cc` L337-L413 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L337-L413))

## 실제 코드

`storage` / `innobase` / `log` / `log0chkp.cc` L337-L413 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L337-L413))

```cpp
// log0chkp.cc L337-L413
dberr_t log_files_next_checkpoint(log_t &log, lsn_t next_checkpoint_lsn) {
  ut_ad(log_checkpointer_mutex_own(log));
  ut_a(!srv_read_only_mode);

  IB_mutex_guard writer_latch{&(log.writer_mutex), UT_LOCATION_HERE};
  IB_mutex_guard files_latch{&(log.m_files_mutex), UT_LOCATION_HERE};

  const auto next_file = log.m_files.find(next_checkpoint_lsn);
  ut_a(next_file != log.m_files.end());

  auto next_file_handle = next_file->open(Log_file_access_mode::WRITE_ONLY);
  if (!next_file_handle.is_open()) {
    return DB_CANNOT_OPEN_FILE;
  }

  log_sync_point("log_before_checkpoint_write");

  const lsn_t prev_checkpoint_lsn = log.last_checkpoint_lsn.load();
  if (prev_checkpoint_lsn != 0) {
    const auto prev_file = log.m_files.find(prev_checkpoint_lsn);
    ut_a(prev_file != log.m_files.end());

    if (prev_file->m_id != next_file->m_id) {
      /* Checkpoint is moved to the next log file. */
      if (log_can_encrypt(*log_sys)) {
        /* Write the encryption header to the new checkpoint file. */
        const dberr_t err =
            log_encryption_header_write(next_file_handle, log.m_encryption_buf);
        if (err != DB_SUCCESS) {
          return err;
        }
      }
      /* Wake up log_files_governor because it potentially might consume
      the previous log file (once we release the files_mutex). */
      os_event_set(log.m_files_governor_event);
    }
  }

  const dberr_t err = log_files_write_checkpoint_low(
      log, next_file_handle, log.next_checkpoint_header_no,
      next_checkpoint_lsn);

  if (err != DB_SUCCESS) {
    return err;
  }

  log_sync_point("log_before_checkpoint_flush");

  next_file_handle.fsync();

  DBUG_PRINT("ib_log", ("checkpoint info written"));

  log.next_checkpoint_header_no =
      log_next_checkpoint_header(log.next_checkpoint_header_no);

  log_sync_point("log_before_checkpoint_lsn_update");

  log.last_checkpoint_lsn.store(next_checkpoint_lsn);

  ut_a(!next_file->m_consumed);

  log_sync_point("log_before_checkpoint_limits_update");

  log_limits_mutex_enter(log);
  log_update_limits_low(log);
  log_update_exported_variables(log);
  log.dict_max_allowed_checkpoint_lsn = 0;
  log_limits_mutex_exit(log);

  if (log.m_writer_inside_extra_margin) {
    log_writer_check_if_exited_extra_margin(log);
  }

  os_event_set(log.next_checkpoint_event);

  return DB_SUCCESS;
}
```

헤더의 checkpoint 칸 둘을 번갈아 쓴다.

`storage` / `innobase` / `log` / `log0chkp.cc` L415-L425 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L415-L425))

```cpp
// log0chkp.cc L415-L425
Log_checkpoint_header_no log_next_checkpoint_header(
    Log_checkpoint_header_no checkpoint_header_no) {
  switch (checkpoint_header_no) {
    case Log_checkpoint_header_no::HEADER_1:
      return Log_checkpoint_header_no::HEADER_2;
    case Log_checkpoint_header_no::HEADER_2:
      return Log_checkpoint_header_no::HEADER_1;
    default:
      ut_error;
  }
}
```

`log_update_limits_low` 가 사용자 스레드의 상한을 다시 계산한다. 기준은 가장 오래 필요한 소비자의 lsn 이다.

`storage` / `innobase` / `log` / `log0chkp.cc` L1101-L1135 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0chkp.cc#L1101-L1135))

```cpp
// log0chkp.cc L1101-L1135
void log_update_limits_low(log_t &log) {
  ut_ad(srv_is_being_started ||
        (log_files_mutex_own(log) && log_limits_mutex_own(log)));

  log_update_concurrency_margin(log);

  if (log.m_writer_inside_extra_margin) {
    /* Stop all new incoming user threads at safe place. */
    log.free_check_limit_lsn.store(0);
    return;
  }

  const lsn_t current_lsn = log_get_lsn(log);
  const lsn_t log_capacity = log_free_check_capacity(log);
  lsn_t oldest_needed_lsn;
  auto consumer = log_consumer_get_oldest(log, oldest_needed_lsn);

  const lsn_t limit_lsn = oldest_needed_lsn + log_capacity;

  log.free_check_limit_lsn.store(limit_lsn);

  /* During the server start, we do not own the limits mutex and the only
  consumer here is checkpointer thread. We can't call consumption_requested()
  without the mutex, and even if we could, it is not permitted to advance the
  checkpoint during recovery. So we skip the consumption_requested() in the
  recovery part. */
  if (!srv_is_being_started && current_lsn > log.free_check_limit_lsn.load()) {
    consumer->consumption_requested(current_lsn - log_capacity);
    if (log.m_THREADS_WAITING_FOR_REDO_throttler.apply()) {
      ib::log_warn(ER_IB_MSG_WAITING_ON_LAGGING_REDO_LOG_CONSUMER,
                   consumer->get_name().c_str(), ulonglong{oldest_needed_lsn});
      log_sync_point("threads_waiting_on_lagging_consumer");
    }
  }
}
```

checkpointer 도 소비자 중 하나이고, 그 소비 지점은 checkpoint lsn 이다.

`storage` / `innobase` / `log` / `log0consumer.cc` L65-L67 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0consumer.cc#L65-L67))

```cpp
// log0consumer.cc L65-L67
lsn_t Log_checkpoint_consumer::get_consumed_lsn() const {
  return log_get_checkpoint_lsn(m_log);
}
```

governor 가 파일을 소비됨으로 표시하는 조건이다. 파일의 끝 lsn 이 가장 오래 필요한 lsn 이하이면 된다.

`storage` / `innobase` / `log` / `log0files_governor.cc` L795-L805 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0files_governor.cc#L795-L805))

```cpp
// log0files_governor.cc L795-L805
static void log_files_mark_consumed_files(log_t &log) {
  log_files_access_allowed_validate(log);

  const lsn_t oldest_lsn = log_files_oldest_needed_lsn(log);

  log_files_validate_current_file(log);

  log_files_for_each(log.m_files, [&](const Log_file &file) {
    if (!file.m_consumed && file.m_end_lsn <= oldest_lsn) {
      log_files_mark_consumed_file(log, file.m_id);
    }
```

`storage` / `innobase` / `log` / `log0files_governor.cc` L981-L996 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0files_governor.cc#L981-L996))

```cpp
// log0files_governor.cc L981-L996
static bool log_files_process_consumed_file(log_t &log, Log_file_id file_id) {
  log_files_write_allowed_validate(log);
  const auto file = log.m_files.file(file_id);
  ut_a(file != log.m_files.end());
  ut_a(file->m_consumed);
  log_files_validate_current_file(log);

  const os_offset_t unused_file_size = log.m_capacity.next_file_size();

  if (log_files::might_recycle_file(log, file->m_size_in_bytes,
                                    unused_file_size)) {
    return log_files_recycle_file(log, file_id, unused_file_size);
  } else {
    return log_files_remove_consumed_file(log, file_id);
  }
}
```

## 동작 흐름

```text
 L341  writer_mutex    L342  m_files_mutex        log writer 와 파일 목록을 잠시 멈춘다
 L344  next_file = checkpoint_lsn 이 속한 파일
 L347  WRITE_ONLY 로 연다
 L355  이전 checkpoint 가 있으면
 L359    다른 파일로 넘어갔으면
 L361      암호화 중이면 새 파일에 암호화 헤더
 L371      m_files_governor_event set               옛 파일을 소비할 수 있을지 보라
 L375  log_files_write_checkpoint_low(header_no, lsn)   칸 하나에 checkpoint_lsn
 L385  fsync
 L389  next_checkpoint_header_no = 다른 칸            (L415 HEADER_1 <-> HEADER_2)
 L394  last_checkpoint_lsn.store(lsn)               fsync 뒤에야 오른다
 L400  limits_mutex
 L401    log_update_limits_low
           L1116  oldest_needed = 소비자들의 최솟값 (checkpointer 는 checkpoint lsn)
           L1118  free_check_limit_lsn = oldest_needed + free_check_capacity
 L402    exported 변수 갱신, L403 dict_max_allowed = 0
 L406  writer 가 extra margin 안이면 빠져나왔는지 본다
 L410  next_checkpoint_event set                    [mtr-redo 09] 의 대기를 깨운다
```

```text
 checkpoint 헤더 두 칸 (redo 파일 하나)

 offset 0      512            1024          1536           2048
 +-------------+--------------+-------------+--------------+---------------------
 | file header | checkpoint 1 | encryption  | checkpoint 2 | data blocks ...
 +-------------+--------------+-------------+--------------+---------------------
                ^ LOG_CHECKPOINT_1           ^ LOG_CHECKPOINT_2
 (log0constants.h L167, L170, L173, L176 LOG_FILE_HDR_SIZE = 2048)
 이번에 1 에 쓰면 다음에는 2 에 쓴다 (L389, L415-L425)
```

checkpoint 가 오르면 redo 파일들의 역할이 바뀐다. 파일 단위로만 재사용되므로, checkpoint 가 한 파일의 끝을 넘어야 그 파일이 풀린다.

```text
 redo 파일과 LSN 축 (#ib_redoN, log0constants.h L76, 파일마다 [start_lsn, end_lsn))

   #ib_redo10          #ib_redo11          #ib_redo12          #ib_redo13 (current)
 [1000, 2000)        [2000, 3000)        [3000, 4000)        [4000, 5000)
 --------------------+-------------------+----------+--------+------------+----> lsn
                                                    ^                     ^
                                         last_checkpoint_lsn = 3500     write_lsn = 4700

 governor (log_files_mark_consumed_files, L795)
   file.end_lsn <= oldest_needed_lsn (= 3500) 인 파일 -> consumed
     #ib_redo10, #ib_redo11 -> consumed
     #ib_redo12 는 3500 을 품고 있으므로 남는다
   consumed 파일은 L981 log_files_process_consumed_file 에서
     재활용할 수 있으면 log_files_recycle_file
     아니면 log_files_remove_consumed_file
```

```text
 last_checkpoint_lsn 이 오르면 풀리는 세 가지

 who            where                        bound
 log_writer     log0write.cc L1893-L1895     checkpoint + hard_logical_capacity 까지 쓴다
 user threads   log0chkp.cc L1118-L1120      free_check_limit_lsn = oldest_needed + capacity
 governor       log0files_governor.cc L803   end_lsn <= oldest_needed 인 파일을 consumed 로
```

## 결과가 쓰이는 곳

```text
 redo 파일 헤더의 checkpoint_lsn
      --> 재시작 때 recv_find_max_checkpoint 가 읽어 복구의 출발점으로 삼는다  [크래시 복구]

 last_checkpoint_lsn
      --> [mtr-redo 09] log_writer 가 next_checkpoint_event 로 깨어나 다시 쓴다
      --> [08] 다음 바퀴의 checkpoint age 기준
      --> log_files_governor 가 옛 파일을 재활용하거나 지운다
```

## 다루지 않는 것

redo 파일 개수와 크기(`innodb_redo_log_capacity`, `LOG_N_FILES = 32`, log0constants.h L83), 헤더 칸의 바이트 배치와 체크섬(`log_checkpoint_header_write`), 암호화 헤더, redo 크기 변경 중의 dummy 레코드, clone 과 백업 같은 다른 소비자(`Log_consumer`), governor 의 파일 생성(`log_files_produce_file`)은 요약만 했다. 파일 구조는 [redo 로그 파일과 mlog 타입](../../../structure/redo-log-files/README.md)에 둔다.
