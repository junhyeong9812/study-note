# recv_recovery_from_checkpoint_start

상위: [크래시 복구](../README.md)

**redo 복구의 본 함수다.** 가장 큰 체크포인트를 찾아 그 헤더를 다시 읽고, 체크포인트 LSN 이 시스템 테이블스페이스에 적힌 flushed_lsn 과 다르면 "크래시 복구가 필요하다"고 판정해 [07] 을 부른다. 그런 다음 [04] 로 체크포인트부터 로그 끝까지 스캔하고 적용한 뒤, 복구한 끝 LSN 이 말이 되는지 확인하고 `log_start` 로 redo 쓰기를 다시 연다. 정상 종료였어도 이 함수는 지나간다. 그때는 스캔할 로그가 없어 곧바로 끝난다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L3766-L3921 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3766-L3921))

## 실제 코드

체크포인트를 찾고 헤더를 읽는 앞부분이다.

`storage` / `innobase` / `log` / `log0recv.cc` L3766-L3827 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3766-L3827))

```cpp
// log0recv.cc L3766-L3827
dberr_t recv_recovery_from_checkpoint_start(log_t &log, lsn_t flush_lsn) {
  if (srv_force_recovery >= SRV_FORCE_NO_LOG_REDO) {
    ib::info(ER_IB_MSG_728);

    /* We leave redo log not started and this is read-only mode. */
    ut_a(log.sn == 0);
    ut_a(srv_read_only_mode);

    return DB_SUCCESS;
  }

  recv_recovery_on = true;

  ut_a(log.m_format == Log_format::CURRENT);

  /* Look for the latest checkpoint */
  Log_checkpoint_location checkpoint;
  if (!recv_find_max_checkpoint(log, checkpoint)) {
    ib::error(ER_IB_MSG_RECOVERY_CHECKPOINT_NOT_FOUND);
    return DB_ERROR;
  }

  const auto checkpoint_file = log.m_files.find(checkpoint.m_checkpoint_lsn);

  /* When reading checkpoints from redo log files, error would be reported
  if checkpoint_lsn was outside the redo log file from which it was read,
  and such file would be skipped. If no checkpoint was found because of that,
  then recv_find_max_checkpoint would return false. Therefore here we know
  that InnoDB found a valid checkpoint (for which there is a redo log file
  which contains the checkpoint_lsn). */
  if (checkpoint_file == log.m_files.end()) {
    ut_d(ut_error);
    ut_o(return DB_ERROR);
  }

  log.last_checkpoint_lsn.store(checkpoint.m_checkpoint_lsn);

  const auto file_path = log_file_path(log.m_files_ctx, checkpoint_file->m_id);
  ib::info(ER_IB_MSG_LOG_CHECKPOINT_FOUND,
           ulonglong{checkpoint.m_checkpoint_lsn}, file_path.c_str());

  Log_checkpoint_header checkpoint_header;

  auto checkpoint_file_handle =
      checkpoint_file->open(Log_file_access_mode::READ_ONLY);

  if (!checkpoint_file_handle.is_open()) {
    return DB_CANNOT_OPEN_FILE;
  }

  dberr_t err = log_checkpoint_header_read(checkpoint_file_handle,
                                           checkpoint.m_checkpoint_header_no,
                                           checkpoint_header);
  if (err != DB_SUCCESS) {
    return err;
  }

  checkpoint_file_handle.close();

  const lsn_t checkpoint_lsn = checkpoint.m_checkpoint_lsn;

  ut_a(checkpoint_lsn == checkpoint_header.m_checkpoint_lsn);
```

복구가 필요한지 판정하고 스캔을 부른다.

`storage` / `innobase` / `log` / `log0recv.cc` L3829-L3862 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3829-L3862))

```cpp
// log0recv.cc L3829-L3862
  /* Start reading the log from the checkpoint LSN up. */

  ut_ad(RECV_SCAN_SIZE <= log.buf_size);

  ut_ad(recv_sys->n_pages_to_recover.value() == 0);

  /* NOTE: we always do a 'recovery' at startup, but only if
  there is something wrong we will print a message to the
  user about recovery: */

  if (checkpoint_lsn != flush_lsn) {
    if (checkpoint_lsn < flush_lsn) {
      ib::warn(ER_IB_MSG_RECOVERY_CHECKPOINT_FROM_BEFORE_CLEAN_SHUTDOWN,
               ulonglong{checkpoint_lsn}, ulonglong{flush_lsn});
    }

    if (!recv_needed_recovery) {
      ib::info(ER_IB_MSG_RECOVERY_IS_NEEDED, ulonglong{flush_lsn},
               ulonglong{checkpoint_lsn});

      if (srv_read_only_mode) {
        ib::error(ER_IB_MSG_RECOVERY_IN_READ_ONLY);

        return DB_ERROR;
      }

      recv_init_crash_recovery();
    }
  }

  err = recv_recovery_begin(log, checkpoint_lsn);
  if (err != DB_SUCCESS) {
    return err;
  }
```

결과를 검증하고 redo 를 다시 연다.

`storage` / `innobase` / `log` / `log0recv.cc` L3864-L3921 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3864-L3921))

```cpp
// log0recv.cc L3864-L3921
  if (srv_read_only_mode && log.m_scanned_lsn > checkpoint_lsn) {
    ib::error(ER_IB_MSG_RECOVERY_IN_READ_ONLY);
    return DB_ERROR;
  }

  lsn_t recovered_lsn;

  recovered_lsn = recv_sys->recovered_lsn;

  ut_a(recv_needed_recovery || checkpoint_lsn == recovered_lsn);

  ut_a(!srv_read_only_mode || !recv_needed_recovery);
  ut_a(!srv_read_only_mode || checkpoint_lsn == recovered_lsn);

  log.recovered_lsn = recovered_lsn;

  ut_a(log.m_files.find(recovered_lsn) != log.m_files.end());

  /* If it is at block boundary, add header size. */
  auto check_scanned_lsn = log.m_scanned_lsn;
  if (check_scanned_lsn % OS_FILE_LOG_BLOCK_SIZE == 0) {
    check_scanned_lsn += LOG_BLOCK_HDR_SIZE;
  }

  if (check_scanned_lsn < checkpoint_lsn ||
      check_scanned_lsn < recv_max_page_lsn) {
    ib::error(ER_IB_MSG_737, ulonglong{log.m_scanned_lsn},
              ulonglong{checkpoint_lsn}, ulonglong{recv_max_page_lsn});
  }

  if (recovered_lsn < checkpoint_lsn) {
    /* No harm in trying to do RO access. */
    if (!srv_read_only_mode) {
      ut_error;
    }

    return DB_ERROR;
  }

  if (recv_sys->found_corrupt_log || recv_sys->found_corrupt_fs) {
    return DB_ERROR;
  }

  /* Disallow checkpoints until recovery is finished, and changes gathered
  in recv_sys->metadata_recover (dict_metadata) are transferred to
  dict_table_t objects (happens in srv0start.cc). */

  err = log_start(log, checkpoint_lsn, recovered_lsn, false);
  if (err != DB_SUCCESS) {
    return err;
  }

  ut_a(recv_sys->spaces->empty());

  /* The database is now ready to start almost normal processing of user
  transactions: transaction rollbacks can be run in background. */

  return DB_SUCCESS;
```

## 동작 흐름

```text
 L3767  innodb_force_recovery >= SRV_FORCE_NO_LOG_REDO(6)   redo 를 아예 보지 않는다 (읽기 전용)
 L3777  recv_recovery_on = true                  이제부터 읽는 페이지는 io 완료에서 redo 적용 대상
 L3783  [03] recv_find_max_checkpoint            없으면 DB_ERROR
 L3788  체크포인트 LSN 을 담은 redo 파일을 찾는다
 L3801  log.last_checkpoint_lsn = checkpoint_lsn
 L3816  log_checkpoint_header_read               같은 헤더를 다시 읽는다
 L3827  두 값이 같아야 한다

 L3839  checkpoint_lsn != flush_lsn
 L3840    checkpoint 가 더 작으면 경고           (정상 종료 기록보다 앞선 체크포인트)
 L3845    아직 recv_needed_recovery 가 아니면
 L3849      읽기 전용이면 DB_ERROR
 L3855      [07] recv_init_crash_recovery        doublewrite 복원, recv_writer 시작
 L3859  [04] recv_recovery_begin(log, checkpoint_lsn)   스캔 + 적용

 L3871  recovered_lsn = recv_sys->recovered_lsn        파싱이 끝난 마지막 mtr 의 끝
 L3873  복구가 필요 없었다면 recovered_lsn == checkpoint_lsn 이어야 한다
 L3888  scanned_lsn 이 checkpoint 보다, 또는 페이지에서 본 최대 LSN 보다 작으면 에러 로그
          ER_IB_MSG_737 "... It is possible that the database is now corrupt!"
 L3894  recovered_lsn < checkpoint_lsn 이면 ut_error
 L3903  로그나 파일 시스템 손상 표시가 있으면 DB_ERROR
 L3911  log_start(log, checkpoint_lsn, recovered_lsn)   새 redo 는 recovered_lsn 뒤에
```

복구가 필요하다는 판정은 두 곳에서 날 수 있다. 여기서 LSN 비교로 먼저 나거나, 비교로는 같았는데 스캔해 보니 체크포인트 뒤에 로그가 있으면 [05] 에서 난다.

```text
 "크래시 복구가 필요하다" 가 켜지는 두 자리

 L3839 -> L3855   이 함수. checkpoint_lsn != flushed_lsn
 L3411 -> L3421   [05] 스캔 중. scanned_lsn > checkpoint_lsn (체크포인트 뒤에 로그가 더 있다)

 flushed_lsn 은 정상 종료 때 시스템 테이블스페이스 첫 페이지에 적힌다
 크래시면 보통 이 값이 체크포인트와 다르다
 켜지는 순간 [07] 이 ER_IB_MSG_726 "Database was not shutdown normally!"
 와 ER_IB_MSG_727 "Starting crash recovery." 를 찍는다 (share/messages_to_error_log.txt L7713)
```

```text
 이 함수가 다루는 LSN 들 (이름, 출처, 뜻)

 flush_lsn          인자. 시스템 테이블스페이스 첫 페이지, 마지막 정상 종료 시점
 checkpoint_lsn     [03] redo 파일 헤더. 이 LSN 이전 변경은 모두 디스크에 있다
 parse_start_lsn    [05] 첫 블록의 first_rec_group. 실제 파싱 시작점 (mtr 경계)
 scanned_lsn        [05] 유효한 로그 블록의 끝
 recovered_lsn      [06] 완전한 mtr 로 파싱된 끝
 recv_max_page_lsn  [09] 적용하며 본 page LSN 의 최댓값
```

## 결과가 쓰이는 곳

```text
 log.recovered_lsn, log_start
      --> 새 mtr 은 recovered_lsn 뒤에 쓴다. 불완전한 마지막 mtr 은 버려진 채 덮인다
 recv_needed_recovery
      --> [07] 이 이미 켰다. 이후 [09] 가 적용하려면 이 값이 참이어야 한다 (L2640 ut_a)
 last_checkpoint_lsn
      --> srv_start 가 복구 전후로 이 값이 바뀌지 않았는지 단언한다 (srv0start.cc L1812)
```

## 다루지 않는 것

`log_files_for_each` 와 redo 파일 목록(`log.m_files`), 체크포인트 헤더의 바이트 배치([redo 로그 파일과 mlog 타입](../../../structure/redo-log-files/README.md)), 읽기 전용 모드에서 로그가 남아 있을 때의 처리, `log_start` 가 log buffer 와 LSN 을 초기화하는 세부는 이 함수의 곁가지라 요약만 했다.
