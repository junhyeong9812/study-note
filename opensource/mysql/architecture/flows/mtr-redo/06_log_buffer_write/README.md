# log_buffer_write

상위: [mini-transaction과 redo 기록](../README.md)

**예약한 자리에 mtr 의 바이트를 memcpy 하는 함수다.** log buffer 는 lsn 으로 직접 주소를 매기는 링 버퍼라서(`ptr = log.buf + start_lsn % buf_size`) 옮기거나 당길 일이 없고, 서로 다른 범위를 받은 스레드들은 아무 동기화 없이 동시에 복사한다(log0buf.cc L210-L225 주석). 이 함수의 일은 512 바이트 블록의 헤더 12 바이트와 트레일러 4 바이트를 **건너뛰며** 쓰는 것과 링 끝에서 되감는 것이다. 완성된 블록의 헤더는 나중에 log writer 가 채운다.

## 위치

`storage` / `innobase` / `log` / `log0buf.cc` L944-L1081 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L944-L1081))

## 실제 코드

앞쪽은 전제 조건이다. 이미 쓰인 곳이나 구멍 뒤쪽에 쓰는 일이 없음을 확인한다.

`storage` / `innobase` / `log` / `log0buf.cc` L944-L975 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L944-L975))

```cpp
// log0buf.cc L944-L975
lsn_t log_buffer_write(log_t &log, const byte *str, size_t str_len,
                       lsn_t start_lsn) {
  ut_ad(rw_lock_own(log.sn_lock_inst, RW_LOCK_S));

  ut_a(log.buf != nullptr);
  ut_a(log.buf_size > 0);
  ut_a(log.buf_size % OS_FILE_LOG_BLOCK_SIZE == 0);
  ut_a(str != nullptr);
  ut_a(str_len > 0);

  /* We should first resize the log buffer, if str_len is that big. */
  ut_a(str_len < log.buf_size_sn.load());

  /* The start_lsn points a data byte (not a header of log block). */
  ut_a(log_is_data_lsn(start_lsn));

  /* We neither write with holes, nor overwrite any fragments of data. */
  ut_ad(log.write_lsn.load() <= start_lsn);
  ut_ad(log_buffer_ready_for_write_lsn(log) <= start_lsn);

  /* That's only used in the assertion at the very end. */
  const sn_t end_sn = log_translate_lsn_to_sn(start_lsn) + sn_t{str_len};

  /* A guard used to detect when we should wrap (to avoid overflowing
  outside the log buffer). */
  byte *buf_end = log.buf + log.buf_size;

  /* Pointer to next data byte to set within the log buffer. */
  byte *ptr = log.buf + (start_lsn % log.buf_size);

  /* Lsn value for the next byte to copy. */
  lsn_t lsn = start_lsn;
```

복사 루프다. 한 바퀴가 블록 하나 안의 조각 하나다.

`storage` / `innobase` / `log` / `log0buf.cc` L980-L1081 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0buf.cc#L980-L1081))

```cpp
// log0buf.cc L980-L1081
  while (true) {
    /* Calculate offset from the beginning of log block. */
    const auto offset = lsn % OS_FILE_LOG_BLOCK_SIZE;

    ut_a(offset >= LOG_BLOCK_HDR_SIZE);
    ut_a(offset < OS_FILE_LOG_BLOCK_SIZE - LOG_BLOCK_TRL_SIZE);

    /* Calculate how many free data bytes are available
    within current log block. */
    const auto left = OS_FILE_LOG_BLOCK_SIZE - LOG_BLOCK_TRL_SIZE - offset;

    ut_a(left > 0);
    ut_a(left < OS_FILE_LOG_BLOCK_SIZE);

    size_t len, lsn_diff;

    if (left > str_len) {
      /* There are enough free bytes to finish copying
      the remaining part, leaving at least single free
      data byte in the log block. */

      len = str_len;

      lsn_diff = str_len;

    } else {
      /* We have more to copy than the current log block
      has remaining data bytes, or exactly the same.

      In both cases, next lsn value will belong to the
      next log block. Copy data up to the end of the
      current log block and start a next iteration if
      there is more to copy. */

      len = left;

      lsn_diff = left + LOG_BLOCK_TRL_SIZE + LOG_BLOCK_HDR_SIZE;
    }

    ut_a(len > 0);
    ut_a(ptr + len <= buf_end);

    log_sync_point("log_buffer_write_before_memcpy");

    /* This is the critical memcpy operation, which copies data
    from internal mtr's buffer to the shared log buffer. */
    std::memcpy(ptr, str, len);

    ut_a(len <= str_len);

    str_len -= len;
    str += len;
    lsn += lsn_diff;
    ptr += lsn_diff;

    ut_a(log_is_data_lsn(lsn));

    if (ptr >= buf_end) {
      /* Wrap - next copy operation will write at the
      beginning of the log buffer. */

      ptr -= log.buf_size;
    }

    if (lsn_diff > left) {
      /* We have crossed boundaries between consecutive log
      blocks. Either we finish in next block, in which case
      user will set the proper first_rec_group field after
      this function is finished, or we finish even further,
      in which case next block should have 0. In both cases,
      we reset next block's value to 0 now, and in the first
      case, user will simply overwrite it afterwards. */

      ut_a((uintptr_t(ptr) % OS_FILE_LOG_BLOCK_SIZE) == LOG_BLOCK_HDR_SIZE);

      ut_a((uintptr_t(ptr) & ~uintptr_t(LOG_BLOCK_HDR_SIZE)) %
               OS_FILE_LOG_BLOCK_SIZE ==
           0);

      log_block_set_first_rec_group(
          reinterpret_cast<byte *>(uintptr_t(ptr) &
                                   ~uintptr_t(LOG_BLOCK_HDR_SIZE)),
          0);

      if (str_len == 0) {
        /* We have finished at the boundary. */
        break;
      }

    } else {
      /* Nothing more to copy - we have finished! */
      break;
    }
  }

  ut_a(ptr >= log.buf);
  ut_a(ptr <= buf_end);
  ut_a(buf_end == log.buf + log.buf_size);
  ut_a(log_translate_lsn_to_sn(lsn) == end_sn);

  return lsn;
}
```

## 동작 흐름

```text
 L946  log buffer s-lock 을 쥐고 있어야 한다 ([05] 에서 잡음)
 L955  str_len < buf_size_sn            한 번에 log buffer 보다 큰 것은 못 쓴다
 L961  write_lsn <= start_lsn           이미 디스크로 나간 자리에 덮어쓰지 않는다
 L962  ready_for_write_lsn <= start_lsn
 L972  ptr = log.buf + start_lsn % buf_size
 L980  while (true)
 L982    offset = lsn % 512                        12 <= offset < 508
 L989    left   = 512 - 4 - offset                 이 블록에 남은 데이터 칸
 L996    left > str_len
           L1001  len = str_len,  lsn_diff = str_len             이 블록 안에서 끝난다
         else
           L1014  len = left,     lsn_diff = left + 4 + 12       트레일러와 다음 헤더를 건너뛴다
 L1026   memcpy(ptr, str, len)                     "the critical memcpy" (주석 L1024-L1025)
 L1030   str_len -= len, str += len, lsn += lsn_diff, ptr += lsn_diff
 L1037   ptr >= buf_end 이면 ptr -= buf_size        링 되감기
 L1044   블록을 넘었으면
 L1059     다음 블록 헤더의 first_rec_group = 0     끝이 그 블록이면 호출한 쪽이 덮어쓴다
 L1064     str_len == 0 이면 break
         넘지 않았으면 break
 L1080 return lsn                                   다음 조각의 시작 lsn
```

```text
 한 조각이 블록 경계를 넘는 모양 (str_len = 30, 시작 offset = 490)

 블록 n                                            블록 n+1
 +-----+--------------------------------+---+     +-----+-----------------------
 | hdr |  ... 앞선 mtr ...  | 18 bytes  |trl|     | hdr | 12 bytes | ...
 +-----+--------------------------------+---+     +-----+-----------------------
 0     12                   490        508 512    512   524       536
                            ^ start_lsn                           ^ return lsn

 1 바퀴  left = 512-4-490 = 18 <= 30  -> len 18, lsn_diff = 18+4+12 = 34
 2 바퀴  offset = 12, left = 496 > 12 -> len 12, lsn_diff 12, break
 블록 n+1 의 first_rec_group 은 L1059 에서 0 으로 초기화된다
```

```text
 링 버퍼 위치 (buf_size 는 기본 64MB, log0constants.h L485)

 log.buf
 +-----------------------------------------------------------+
 |  ...  | write_lsn % S       ready % S        sn 의 lsn % S |
 +-----------------------------------------------------------+
         ^ 여기 앞은 이미 파일로 나감, 덮어써도 된다
           (단 end_sn + 512 <= write_sn + buf_size 일 때만 예약이 통과, [05] L867)
```

## 결과가 쓰이는 곳

```text
 반환한 lsn
      --> mtr_write_log_t 가 이 조각의 end_lsn 으로 [07] 에 넘기고 다음 블록의 시작으로 쓴다

 log buffer 의 바이트
      --> [09] log_writer 가 recent_written 으로 구멍이 없음을 확인한 뒤 파일에 쓴다
      --> 완성된 블록의 헤더는 log_writer 의 prepare_full_blocks 가 채운다 (log0write.cc L1502)
```

## 다루지 않는 것

블록 헤더 필드(블록 번호, data_len, first_rec_group, epoch)와 트레일러 체크섬의 배치는 [redo 로그 파일과 mlog 타입](../../../structure/redo-log-files/README.md)에 둔다. 같은 캐시 라인에 두 스레드가 쓰는 경우의 숨은 동기화(주석 L227-L231)는 다루지 않는다.
