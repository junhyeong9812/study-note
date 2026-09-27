# recv_recovery_begin

상위: [크래시 복구](../README.md)

**redo 스캔과 적용의 바깥 루프다.** `recv_sys` 의 LSN 들을 체크포인트로 맞추고, 해시 테이블이 쓸 수 있는 메모리 한도를 버퍼 풀 크기에서 계산한 뒤, 체크포인트가 든 블록부터 `RECV_SCAN_SIZE` 씩 읽어 [05] 에 넘긴다. 로그의 끝에 닿으면 남은 해시를 [08] 로 한 번 적용한다. 요점은 **메모리 한도**다. 해시가 한도를 넘으면 [05] 가 스캔 도중에 적용을 끼워 넣으므로, redo 가 버퍼 풀보다 커도 여러 배치로 나누어 복구된다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L3622-L3740 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3622-L3740))

## 실제 코드

`storage` / `innobase` / `log` / `log0recv.cc` L3622-L3740 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3622-L3740))

```cpp
// log0recv.cc L3622-L3740
static dberr_t recv_recovery_begin(log_t &log, const lsn_t checkpoint_lsn) {
  mutex_enter(&recv_sys->mutex);
  recv_sys->len = 0;
  recv_sys->recovered_offset = 0;
  recv_sys_empty_hash();

  /* Since 8.0, we can start recovery at checkpoint_lsn which points
  to the middle of log record. In such case we first to need to find
  the beginning of the first group of log records, which is at lsn
  greater than the checkpoint_lsn. */
  recv_sys->parse_start_lsn = 0;

  /* This is updated when we find value for parse_start_lsn. */
  recv_sys->bytes_to_ignore_before_checkpoint = 0;

  recv_sys->checkpoint_lsn = checkpoint_lsn;
  recv_sys->scanned_lsn = checkpoint_lsn;
  recv_sys->recovered_lsn = checkpoint_lsn;

  /* We have to trust that the first_rec_group in the first block is
  correct as we can't start parsing earlier to check it ourselves. */
  recv_sys->previous_recovered_lsn = checkpoint_lsn;
  recv_sys->last_block_first_mtr_boundary = 0;

  recv_sys->scanned_epoch_no = 0;
  recv_previous_parsed_rec_type = MLOG_SINGLE_REC_FLAG;
  recv_previous_parsed_rec_offset = 0;
  recv_previous_parsed_rec_is_multi = 0;
  ut_ad(recv_max_page_lsn == 0);

  const auto pages_to_be_kept_free = std::min(
      size_t{buf_pool_get_n_pages()} / 2,
      /* This value should be greater than the number of pages we want
      to apply redo records for concurrently. This should be greater
      than number of concurrent IOs we want to sustain. We should also keep in
      mind that the limit for the deltas hashmap is not strictly enforced and
      this number includes the not-well specified safety margin. */
      size_t{256} * srv_buf_pool_instances);
  const size_t delta_hashmap_max_mem =
      UNIV_PAGE_SIZE * (buf_pool_get_n_pages() - pages_to_be_kept_free);

    // ... (L3663-L3687 생략: 메모리 한도 단언과 그 설명 주석)
    recv_n_frames_for_pages_per_pool_instance = 0;
  }

  mutex_exit(&recv_sys->mutex);

  lsn_t start_lsn =
      ut_uint64_align_down(checkpoint_lsn, OS_FILE_LOG_BLOCK_SIZE);

  bool finished = false;

  while (!finished && !recv_sys->found_corrupt_log) {
    const lsn_t end_lsn =
        recv_read_log_seg(log, log.buf, start_lsn, start_lsn + RECV_SCAN_SIZE);

    if (end_lsn == 0) {
      return DB_ERROR;
    }

    if (end_lsn == start_lsn) {
      /* This could happen if we crashed just after completing file,
      and before next file has been successfully created. */
      break;
    }

    finished =
        recv_scan_log_recs(log, delta_hashmap_max_mem, log.buf,
                           end_lsn - start_lsn, start_lsn, &log.m_scanned_lsn);
    start_lsn = end_lsn;
  }

  if (!recv_sys->found_corrupt_log) {
    if (srv_read_only_mode) {
      ut_a_eq(recv_sys->n_pages_to_recover.value(), 0);
      ut_a(recv_sys->spaces->empty());
    } else {
      recv_apply_hashed_log_recs(log);
    }
  }

  DBUG_PRINT("ib_log", ("scan " LSN_PF " completed", log.m_scanned_lsn));
  DBUG_EXECUTE_IF("stop_scan_on_corrupt_log", {
    if (recv_sys->found_corrupt_log) {
      lsn_t recv_start_lsn =
          ut_uint64_align_down(checkpoint_lsn, OS_FILE_LOG_BLOCK_SIZE);
      ib::info(ER_IB_MSG_725, ulonglong(log.m_scanned_lsn))
          << " start_lsn:" << recv_start_lsn
          << " end_lsn:" << start_lsn /* end_lsn after procesing each segment */
          << " log_segments_read:"
          << (start_lsn - recv_start_lsn + RECV_SCAN_SIZE - 1) / RECV_SCAN_SIZE;
    }
  });
  return DB_SUCCESS;
}
```

## 동작 흐름

```text
 L3624  recv_sys->len = 0, recovered_offset = 0      파싱 버퍼를 비운다
 L3626  recv_sys_empty_hash                         페이지별 해시를 비운다
 L3632  parse_start_lsn = 0                         아직 mtr 경계를 모른다
 L3637  checkpoint_lsn = scanned_lsn = recovered_lsn = checkpoint_lsn

 L3652  pages_to_be_kept_free = min(버퍼 풀 페이지 수 / 2, 256 * 인스턴스 수)
 L3660  delta_hashmap_max_mem = 페이지 크기 * (버퍼 풀 페이지 수 - pages_to_be_kept_free)
          해시 테이블(redo 조각)은 버퍼 풀 메모리에서 자란다 (log0recv.cc L2337-L2339 주석)
          나머지는 적용할 페이지를 읽어 들일 frame 몫이다

 L3693  start_lsn = checkpoint_lsn 을 512 바이트 블록 경계로 내림
 L3698  while (!finished && !found_corrupt_log)
 L3700    end_lsn = recv_read_log_seg(start_lsn, start_lsn + RECV_SCAN_SIZE)
 L3702    0 이면 DB_ERROR
 L3706    end_lsn == start_lsn 이면 break          (파일을 막 채우고 다음 파일을 만들기 전에 죽은 경우)
 L3712    finished = [05] recv_scan_log_recs(log, max_mem, buf, len, start_lsn, &scanned_lsn)
 L3715    start_lsn = end_lsn

 L3718  손상이 없으면
 L3723    [08] recv_apply_hashed_log_recs           마지막 배치
```

```text
 메모리 한도의 예 (버퍼 풀 16384 장, 인스턴스 1개, 16KB 페이지)

 pages_to_be_kept_free   min(16384 / 2, 256 * 1) = 256
 delta_hashmap_max_mem   16KB * (16384 - 256) = 약 252MB

 redo 가 1GB 라면
   스캔 --> 해시 252MB 초과 --> [05] 안에서 [08] 적용 (배치 1)
   스캔 계속 --> 다시 초과 --> 적용 (배치 2) ...
   로그 끝 --> L3723 적용 (마지막 배치)
 배치마다 [08] 끝에서 flush list 를 비우고 버퍼 풀을 무효화한다
```

## 결과가 쓰이는 곳

```text
 recv_sys->recovered_lsn, log.m_scanned_lsn
      --> [02] 의 검증과 log_start 인자
 recv_n_frames_for_pages_per_pool_instance
      --> 적용할 페이지를 읽을 때 인스턴스마다 남겨 둘 frame 수 (buf_read_recv_pages)
```

## 다루지 않는 것

`recv_read_log_seg` 가 파일 경계를 넘어 읽는 방식(L3520), `log_test` 단위 테스트 모드, 읽기 전용 모드에서 해시가 비어 있어야 한다는 단언, 디버그 옵션 `stop_scan_on_corrupt_log` 는 이 함수의 곁가지라 요약만 했다.
