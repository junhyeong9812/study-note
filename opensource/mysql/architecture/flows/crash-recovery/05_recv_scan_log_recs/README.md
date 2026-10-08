# recv_scan_log_recs

상위: [크래시 복구](../README.md)

**읽어 온 로그 구간을 512 바이트 블록 단위로 검사해 "로그가 어디서 끝나는가"를 정하는 함수다.** 블록 번호가 LSN 에서 계산한 값과 다르거나, 블록 체크섬이 틀리거나, epoch 가 맞지 않거나, 블록이 꽉 차 있지 않으면 거기가 끝이다. 크래시로 반쯤 쓰인 블록은 이 검사에서 걸러지고 **에러가 아니라 로그의 끝**으로 취급된다. 유효한 블록의 데이터는 파싱 버퍼로 옮기고, 새 데이터가 있으면 [06] 으로 파싱한다. 체크포인트 뒤에 로그가 더 있음을 처음 발견하면 여기서 [07] 을 부른다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L3289-L3517 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3289-L3517))

## 실제 코드

블록 하나의 유효성 검사다.

`storage` / `innobase` / `log` / `log0recv.cc` L3289-L3355 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3289-L3355))

```cpp
// log0recv.cc L3289-L3355
static bool recv_scan_log_recs(log_t &log,
#else  /* !UNIV_HOTBACKUP */
bool meb_scan_log_recs(
#endif /* !UNIV_HOTBACKUP */
                               size_t max_memory, const byte *buf, size_t len,
                               lsn_t start_lsn, lsn_t *read_upto_lsn) {
  const byte *log_block = buf;
  lsn_t scanned_lsn = start_lsn;
  bool finished = false;
  bool more_data = false;

  ut_ad(start_lsn % OS_FILE_LOG_BLOCK_SIZE == 0);
  ut_ad(len % OS_FILE_LOG_BLOCK_SIZE == 0);
  ut_ad(len >= OS_FILE_LOG_BLOCK_SIZE);

  do {
    ut_ad(!finished);

    Log_data_block_header block_header;
    log_data_block_header_deserialize(log_block, block_header);

    const uint32_t expected_hdr_no =
        log_block_convert_lsn_to_hdr_no(scanned_lsn);

    if (block_header.m_hdr_no != expected_hdr_no) {
      /* Garbage or an incompletely written log block.

      We will not report any error, because this can
      happen when InnoDB was killed while it was
      writing redo log. We simply treat this as an
      abrupt end of the redo log. */

      finished = true;

      break;
    }

    if (!log_block_checksum_is_ok(log_block)) {
      uint32_t checksum1 = log_block_get_checksum(log_block);
      uint32_t checksum2 = log_block_calc_checksum(log_block);
      ib::error(ER_IB_MSG_720, ulong{block_header.m_hdr_no},
                ulonglong{scanned_lsn}, ulong{checksum1}, ulong{checksum2});

      /* Garbage or an incompletely written log block.

      This could be the result of killing the server
      while it was writing this log block. We treat
      this as an abrupt end of the redo log. */

      finished = true;

      break;
    }

    const auto data_len = block_header.m_data_len;

    if (scanned_lsn + data_len > recv_sys->scanned_lsn &&
        recv_sys->scanned_epoch_no > 0 &&
        !log_block_epoch_no_is_valid(block_header.m_epoch_no,
                                     recv_sys->scanned_epoch_no)) {
      /* Garbage from a log buffer flush which was made
      before the most recent database recovery */

      finished = true;

      break;
    }
```

첫 mtr 경계를 찾고, 새 데이터를 파싱 버퍼로 옮긴다.

`storage` / `innobase` / `log` / `log0recv.cc` L3357-L3485 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3357-L3485))

```cpp
// log0recv.cc L3357-L3485
    if (!recv_sys->parse_start_lsn && block_header.m_first_rec_group > 0) {
      /* We found a point from which to start the parsing of log records */

      recv_sys->parse_start_lsn = scanned_lsn + block_header.m_first_rec_group;

      ib::info(ER_IB_MSG_1261)
          << "Starting to parse redo log at lsn = " << recv_sys->parse_start_lsn
          << ", whereas checkpoint_lsn = " << recv_sys->checkpoint_lsn
          << " and start_lsn = " << start_lsn;

      // ... (L3367-L3400 생략: 체크포인트 이전 바이트를 건너뛰는 계산의 설명, 파싱 버퍼 확장)
      recv_sys->scanned_lsn = recv_sys->parse_start_lsn;
      recv_sys->recovered_lsn = recv_sys->parse_start_lsn;

      recv_track_changes_of_recovered_lsn();
    }

    scanned_lsn += data_len;

    if (scanned_lsn > recv_sys->scanned_lsn) {
#ifndef UNIV_HOTBACKUP
      if (!recv_needed_recovery && scanned_lsn > recv_sys->checkpoint_lsn) {
        if (srv_read_only_mode) {
          ut_a(srv_force_recovery < SRV_FORCE_NO_LOG_REDO);
          ib::warn(ER_IB_MSG_RECOVERY_SKIPPED_IN_READ_ONLY_MODE);
          *read_upto_lsn = scanned_lsn;
          return true;
        }

        ib::info(ER_IB_MSG_722, ulonglong{recv_sys->scanned_lsn});

        recv_init_crash_recovery();
      }
#endif /* !UNIV_HOTBACKUP */
      // ... (L3424-L3453 생략: 체크포인트 이전 바이트를 건너뛰는 계산의 설명, 파싱 버퍼 확장)
      if (!recv_sys->found_corrupt_log) {
        /* Since the recv_sys_add_to_parsing_buf is "idempotent" if the
        scanned_lsn is not larger than the one already processed. Therefore,
        it is fine to call recv_sys_add_to_parsing_buf after the
        recv_sys_parse_byte_by_byte. Latter is  properly updating
        the recv_sys->scanned_lsn */
#if defined(UNIV_DEBUG) && defined(HAVE_ASAN)
        if (DBUG_EVALUATE_IF("innodb_recover_byte_by_byte", true, false)) {
          more_data =
              recv_sys_parse_byte_by_byte(log_block, scanned_lsn) || more_data;
        }
#endif /* UNIV_DEBUG && HAVE_ASAN */
        more_data =
            recv_sys_add_to_parsing_buf(log_block, scanned_lsn) || more_data;
      }

      recv_sys->scanned_lsn = scanned_lsn;

      recv_sys->scanned_epoch_no = block_header.m_epoch_no;
    }

    if (data_len < OS_FILE_LOG_BLOCK_SIZE) {
      /* Log data for this group ends here */
      finished = true;

      break;

    } else {
      log_block += OS_FILE_LOG_BLOCK_SIZE;
    }

  } while (log_block < buf + len);
```

파싱과 중간 적용이다.

`storage` / `innobase` / `log` / `log0recv.cc` L3487-L3517 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3487-L3517))

```cpp
// log0recv.cc L3487-L3517
  *read_upto_lsn = scanned_lsn;

  if (recv_needed_recovery ||
      (recv_is_from_backup && !recv_is_making_a_backup)) {
    ++recv_scan_print_counter;

    if (finished || (recv_scan_print_counter % 80) == 0) {
      ib::info(ER_IB_MSG_725, ulonglong{scanned_lsn});
    }
  }

  if (more_data && !recv_sys->found_corrupt_log) {
    /* Try to parse more log records */

    recv_parse_log_recs();

#ifndef UNIV_HOTBACKUP
    if (recv_heap_used() > max_memory) {
      recv_apply_hashed_log_recs(log);
    }
#endif /* !UNIV_HOTBACKUP */

    if (recv_sys->recovered_offset > recv_sys->buf_len / 4) {
      /* Move parsing buffer data to the buffer start */

      recv_reset_buffer();
    }
  }

  return finished;
}
```

## 동작 흐름

```text
 do (블록마다)
 L3308  블록 헤더 역직렬화
 L3313  hdr_no != LSN 에서 계산한 번호     finished (쓰레기 또는 덜 쓰인 블록)
 L3326  블록 체크섬 불일치                  에러 로그 후 finished (쓰다가 죽은 블록)
 L3345  epoch 가 이전 블록과 이어지지 않음  finished (이전 복구 전의 낡은 블록)
 L3357  parse_start_lsn 이 아직 0 이고 first_rec_group > 0
 L3360    parse_start_lsn = 블록 시작 + first_rec_group      첫 mtr 경계
 L3367    그것이 checkpoint_lsn 보다 앞이면
          bytes_to_ignore_before_checkpoint 를 둔다        (체크포인트 앞 레코드는 파싱만)
 L3407  scanned_lsn += data_len
 L3409  새로 본 데이터면
 L3411    체크포인트 뒤인데 아직 복구 모드가 아니면
 L3421      [07] recv_init_crash_recovery
 L3467    recv_sys_add_to_parsing_buf      블록의 데이터 부분만 recv_sys->buf 에 붙인다
 L3470    recv_sys->scanned_lsn = scanned_lsn
 L3475  data_len < 512                     꽉 차지 않은 블록 = 로그의 끝, finished
 L3482  다음 블록
 while (log_block < buf + len)

 L3498  새 데이터가 있고 손상이 없으면
 L3501    [06] recv_parse_log_recs
 L3504    recv_heap_used() > max_memory 면 [08] recv_apply_hashed_log_recs   중간 배치
 L3509    파싱이 버퍼의 1/4 을 넘게 소비했으면 recv_reset_buffer (앞으로 당긴다)
 L3516  return finished
```

로그의 끝을 정하는 네 가지 조건이 모두 에러가 아니라 `finished = true` 인 점이 이 함수의 성격이다. 소스 주석도 "InnoDB 가 redo 를 쓰는 중에 죽으면 생길 수 있으므로 에러를 보고하지 않는다"고 적는다(L3314-L3319).

```text
 로그 블록 하나 (OS_FILE_LOG_BLOCK_SIZE = 512)

 +--------+----------------------------------------------+---------+
 | header | data: mtr records, may continue in next block | trailer |
 +--------+----------------------------------------------+---------+

 헤더 필드 (Log_data_block_header, log0types.h L242)
   m_epoch_no         m_hdr_no 와 함께 블록을 유일하게 식별한다
   m_hdr_no           다음 블록마다 1씩 는다. LSN 으로 계산한 값과 같아야 한다 (L3313)
   m_data_len         블록 시작부터 데이터가 있는 곳까지. 512 미만이면 마지막 블록 (L3475)
   m_first_rec_group  이 블록에서 처음 시작하는 mtr 의 오프셋, 없으면 0
 체크섬은 log_block_checksum_is_ok 로 본다 (L3326)

 checkpoint_lsn 은 mtr 한가운데를 가리킬 수 있다 (L3628-L3631 주석)
 그래서 그 블록의 first_rec_group 부터 파싱하고, 체크포인트 앞 바이트는 적용하지 않는다
```

```text
 어디서 끝났는가에 따른 결과

 로그가 깔끔하게 끝남 (짧은 블록)
   scanned_lsn    그 블록의 데이터 끝
   recovered_lsn  마지막 완전한 mtr 의 끝
 쓰다 죽은 블록 (체크섬 틀림)
   scanned_lsn    그 앞 블록의 끝
   recovered_lsn  그 앞의 마지막 완전한 mtr 의 끝
 mtr 이 잘림 (끝 레코드가 scanned_lsn 을 넘는다)
   recovered_lsn  잘린 mtr 의 시작. 다음 블록을 기다리다 로그가 끝나 해시에 들어가지 않는다 ([06] L2902, L3040)

 recovered_lsn 뒤의 조각은 [02] 의 log_start 이후 새 로그로 덮인다
```

## 결과가 쓰이는 곳

```text
 recv_sys->buf (파싱 버퍼)
      --> [06] recv_parse_log_recs 가 recovered_offset 부터 읽는다
 recv_sys->scanned_lsn, read_upto_lsn
      --> [04] 루프의 종료, [02] 의 검증
 recv_needed_recovery
      --> 여기서 켜지면 [07] 의 doublewrite 복원과 recv_writer 가 시작된다
```

## 다루지 않는 것

`recv_sys_add_to_parsing_buf` 가 헤더와 트레일러를 떼어 내는 계산, 파싱 버퍼 크기 조정(`recv_sys_resize_buf`), MEB 백업용 `meb_scan_log_recs` 판, ASAN 디버그의 byte-by-byte 파싱, 블록 헤더의 바이트 배치([redo 로그 파일과 mlog 타입](../../../structure/redo-log-files/README.md))는 이 함수의 곁가지라 요약만 했다.
