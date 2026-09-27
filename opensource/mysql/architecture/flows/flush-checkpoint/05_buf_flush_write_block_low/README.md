# buf_flush_write_block_low

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**WAL 규칙이 코드로 적힌 곳이다.** 페이지를 쓰기 전에 그 페이지의 `newest_modification` 까지 redo 가 디스크에 있는지 보고, 없으면 `log_write_up_to(newest, true)` 로 기다린다(주석 "Force the log to the disk before writing the modified block", L954). 그다음 페이지 머리의 `FIL_PAGE_LSN` 에 newest 를 찍고 체크섬을 계산한 뒤 [06] `dblwr::write` 로 넘긴다. 이 함수 자체는 IO 를 내지 않는다.

## 위치

`storage` / `innobase` / `buf` / `buf0flu.cc` L924-L1014 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L924-L1014))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0flu.cc` L924-L1014 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L924-L1014))

```cpp
// buf0flu.cc L924-L1014
static void buf_flush_write_block_low(buf_page_t *bpage, buf_flush_t flush_type,
                                      bool sync) {
  page_t *frame = nullptr;

#ifdef UNIV_DEBUG
  buf_pool_t *buf_pool = buf_pool_from_bpage(bpage);
  ut_ad(!mutex_own(&buf_pool->LRU_list_mutex));
#endif /* UNIV_DEBUG */

  DBUG_PRINT("ib_buf", ("flush %s %u page " UINT32PF ":" UINT32PF,
                        sync ? "sync" : "async", (unsigned)flush_type,
                        bpage->id.space(), bpage->id.page_no()));

  ut_ad(buf_page_in_file(bpage));

  /* We are not holding block_mutex here. Nevertheless, it is safe to
  access bpage, because it is io_fixed and oldest_modification != 0.
  Thus, it cannot be relocated in the buffer pool or removed from
  flush_list or LRU_list. */
  ut_ad(!buf_flush_list_mutex_own(buf_pool));
  ut_ad(!buf_page_get_mutex(bpage)->is_owned());
  ut_ad(bpage->is_io_fix_write());
  ut_ad(bpage->is_dirty());

#ifdef UNIV_IBUF_COUNT_DEBUG
  ut_a(ibuf_count_get(bpage->id) == 0);
#endif /* UNIV_IBUF_COUNT_DEBUG */

  ut_ad(recv_recovery_is_on() || bpage->get_newest_lsn() != 0);

  /* Force the log to the disk before writing the modified block */
  if (!srv_read_only_mode) {
    const lsn_t flush_to_lsn = bpage->get_newest_lsn();

    /* Do the check before calling log_write_up_to() because in most
    cases it would allow to avoid call, and because of that we don't
    want those calls because they would have bad impact on the counter
    of calls, which is monitored to save CPU on spinning in log threads. */

    if (log_sys->flushed_to_disk_lsn.load() < flush_to_lsn) {
      Wait_stats wait_stats;

      wait_stats = log_write_up_to(*log_sys, flush_to_lsn, true);

      MONITOR_INC_WAIT_STATS_EX(MONITOR_ON_LOG_, _PAGE_WRITTEN, wait_stats);
    }
  }

  switch (buf_page_get_state(bpage)) {
    case BUF_BLOCK_POOL_WATCH:
    case BUF_BLOCK_ZIP_PAGE: /* The page should be dirty. */
    case BUF_BLOCK_NOT_USED:
    case BUF_BLOCK_READY_FOR_USE:
    case BUF_BLOCK_MEMORY:
    case BUF_BLOCK_REMOVE_HASH:
      ut_error;
      break;
    case BUF_BLOCK_ZIP_DIRTY: {
      frame = bpage->zip.data;
      BlockReporter reporter =
          BlockReporter(false, frame, bpage->size,
                        fsp_is_checksum_disabled(bpage->id.space()));

      mach_write_to_8(frame + FIL_PAGE_LSN, bpage->get_newest_lsn());

      ut_a(reporter.verify_zip_checksum());
      break;
    }
    case BUF_BLOCK_FILE_PAGE:
      frame = bpage->zip.data;
      if (!frame) {
        frame = ((buf_block_t *)bpage)->frame;
      }

      buf_flush_init_for_writing(
          reinterpret_cast<const buf_block_t *>(bpage),
          reinterpret_cast<const buf_block_t *>(bpage)->frame,
          bpage->zip.data ? &bpage->zip : nullptr, bpage->get_newest_lsn(),
          fsp_is_checksum_disabled(bpage->id.space()),
          false /* do not skip lsn check */);
      break;
  }

  dberr_t err = dblwr::write(flush_type, bpage, sync);

  ut_a(err == DB_SUCCESS || err == DB_TABLESPACE_DELETED);

  /* Increment the counter of I/O operations used
  for selecting LRU policy. */
  buf_LRU_stat_inc_io();
}
```

페이지에 LSN 을 찍는 곳이다. 머리의 `FIL_PAGE_LSN` 과 꼬리의 `FIL_PAGE_END_LSN_OLD_CHKSUM` 자리에 같은 lsn 을 쓴다. 꼬리 앞 4 바이트는 뒤에서 옛 체크섬으로 덮인다(L915, 주석 L902-L905).

`storage` / `innobase` / `buf` / `buf0flu.cc` L811-L815 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L811-L815))

```cpp
// buf0flu.cc L811-L815
  /* Write the newest modification lsn to the page header and trailer */
  mach_write_to_8(page + FIL_PAGE_LSN, newest_lsn);

  mach_write_to_8(page + UNIV_PAGE_SIZE - FIL_PAGE_END_LSN_OLD_CHKSUM,
                  newest_lsn);
```

## 동작 흐름

```text
 L945  io_fix 가 WRITE 이고 dirty 여야 한다 (block_mutex 는 없다, L939-L942 주석)
 L955  읽기 전용이 아니면
 L956    flush_to_lsn = newest_modification
 L963    flushed_to_disk_lsn < flush_to_lsn 이면
 L966      log_write_up_to(flush_to_lsn, true)        --> log_writer, log_flusher 를 기다린다
           (먼저 비교하는 이유: 호출 횟수가 log 스레드의 spin 조절에 쓰이는 카운터라서, 주석 L958-L962)
 L972  switch (page state)
         ZIP_DIRTY  L987  zip 프레임의 FIL_PAGE_LSN = newest, 압축 체크섬 검사
         FILE_PAGE  L998  buf_flush_init_for_writing(frame, zip, newest, ...)
                            L812  FIL_PAGE_LSN = newest
                            L814  꼬리 FIL_PAGE_END_LSN_OLD_CHKSUM 자리에도 lsn
                            L884  체크섬 (crc32 등) 을 계산해 기록
 L1007 err = [06] dblwr::write(flush_type, bpage, sync)
 L1009 DB_SUCCESS 또는 DB_TABLESPACE_DELETED 만 허용
 L1013 LRU 정책용 IO 카운터 ++
```

이 함수가 지키는 순서는 LSN 축 위의 부등식 하나다.

```text
 페이지 P 를 쓰는 순간의 조건 (WAL)

   P.newest_modification <= flushed_to_disk_lsn

 ------+----------------------+---------------------+----------> lsn
       |                      |                     |
   P.oldest               P.newest            flushed_to_disk_lsn
       |<-- P 에 반영된, 아직 데이터 파일에 없는 변경 -->|
                              ^ 이 변경들의 redo 가 모두 디스크에 있어야
                                P 를 써도 복구가 P 를 설명할 수 있다

 newest > flushed 면 L966 에서 기다린다
 코디네이터가 1초마다 log_write_up_to(ready, true) 를 해 두므로 ([01] L3056)
 대부분 L963 비교에서 바로 통과한다
```

```text
 쓰기 직전 페이지의 머리와 꼬리 (16KB 기준)

 offset 0                                                        16384
 +----------+-----+------------------------------------+----------+
 | checksum | ... | FIL_PAGE_LSN (8)   ... 본문 ...    | old chk  |
 |   (4)    |     | = newest_modification              | + lsn(4) |
 +----------+-----+------------------------------------+----------+
                   L812                                  L814, L915
 복구는 이 FIL_PAGE_LSN 과 redo 레코드의 lsn 을 비교한다 (log0recv.cc L2632)
```

## 결과가 쓰이는 곳

```text
 FIL_PAGE_LSN 이 찍힌 프레임
      --> [06] dblwr::write 가 암호화, 압축 뒤 doublewrite 와 데이터 파일로 보낸다
      --> 복구가 페이지 lsn 으로 적용 여부를 가른다   [크래시 복구]

 log_write_up_to 대기
      --> 이 스레드(page cleaner)가 redo flush 를 기다리는 동안 다른 페이지는 못 쓴다
```

## 다루지 않는 것

`buf_flush_init_for_writing` 의 페이지 타입별 처리(압축 페이지 `page_zip`, 체크섬 알고리즘 선택 `innodb_checksum_algorithm`), `BlockReporter` 의 검증, 읽기 전용 모드는 요약만 했다. 페이지 헤더 레이아웃 전체는 [테이블스페이스와 페이지 레이아웃](../../../structure/tablespace-page/README.md)에 둔다.
