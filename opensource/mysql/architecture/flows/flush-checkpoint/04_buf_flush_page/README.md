# buf_flush_page

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**페이지 한 장을 "쓰는 중" 상태로 만든다.** 쓰기로 정하면 `io_fix = BUF_IO_WRITE` 를 걸고, 그 순간부터 페이지는 버퍼 풀 안에서 옮겨지거나 flush list, LRU 에서 빠지지 않는다(L1134-L1137 주석). 그다음 페이지 래치를 SX 로 잡아 다른 스레드가 쓰는 도중에 내용을 바꾸지 못하게 하고 [05] 로 넘긴다. 볼거리는 flush list 배치에서 SX 래치를 바로 못 잡을 때다. 그때는 곧장 기다리지 않고 doublewrite 큐에 쌓인 페이지를 먼저 내보낸 뒤(`dblwr::force_flush`) 래치를 기다린다.

## 위치

`storage` / `innobase` / `buf` / `buf0flu.cc` L1027-L1143 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1027-L1143))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0flu.cc` L1027-L1143 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L1027-L1143))

```cpp
// buf0flu.cc L1027-L1143
bool buf_flush_page(buf_pool_t *buf_pool, buf_page_t *bpage,
                    buf_flush_t flush_type, bool sync) {
  BPageMutex *block_mutex;

  ut_ad(flush_type < BUF_FLUSH_N_TYPES);
  /* Hold the LRU list mutex iff called for a single page LRU
  flush. A single page LRU flush is already non-performant, and holding
  the LRU list mutex allows us to avoid having to store the previous LRU
  list page or to restart the LRU scan in
  buf_flush_single_page_from_LRU(). */
  ut_ad(flush_type == BUF_FLUSH_SINGLE_PAGE ||
        !mutex_own(&buf_pool->LRU_list_mutex));
  ut_ad(flush_type != BUF_FLUSH_SINGLE_PAGE ||
        mutex_own(&buf_pool->LRU_list_mutex));
  ut_ad(buf_page_in_file(bpage));
  ut_ad(!sync || flush_type == BUF_FLUSH_SINGLE_PAGE);

  block_mutex = buf_page_get_mutex(bpage);
  ut_ad(mutex_own(block_mutex));

  ut_ad(buf_flush_ready_for_flush(bpage, flush_type));

  bool is_uncompressed;

  is_uncompressed = (buf_page_get_state(bpage) == BUF_BLOCK_FILE_PAGE);
  ut_ad(is_uncompressed == (block_mutex != &buf_pool->zip_mutex));

  bool flush;
  rw_lock_t *rw_lock = nullptr;
  bool no_fix_count = bpage->buf_fix_count == 0;

  if (!is_uncompressed) {
    flush = true;
    rw_lock = nullptr;
  } else if (!(no_fix_count || flush_type == BUF_FLUSH_LIST) ||
             (!no_fix_count &&
              srv_shutdown_state.load() < SRV_SHUTDOWN_FLUSH_PHASE &&
              fsp_is_system_temporary(bpage->id.space()))) {
    /* This is a heuristic, to avoid expensive SX attempts. */
    /* For table residing in temporary tablespace sync is done
    using IO_FIX and so before scheduling for flush ensure that
    page is not fixed. */
    flush = false;
  } else {
    rw_lock = &reinterpret_cast<buf_block_t *>(bpage)->lock;
    if (flush_type != BUF_FLUSH_LIST) {
      flush = rw_lock_sx_lock_nowait(rw_lock, BUF_IO_WRITE, UT_LOCATION_HERE);
    } else {
      /* Will SX lock later */
      flush = true;
    }
  }

  if (flush) {
    /* We are committed to flushing by the time we get here */

    buf_pool->change_flush_state(flush_type, [&] {
      buf_page_set_io_fix(bpage, BUF_IO_WRITE);

      buf_page_set_flush_type(bpage, flush_type);

      ++buf_pool->n_flush[flush_type];

      if (bpage->get_oldest_lsn() > buf_pool->max_lsn_io) {
        buf_pool->max_lsn_io = bpage->get_oldest_lsn();
      }

      if (!fsp_is_system_temporary(bpage->id.space()) &&
          buf_pool->track_page_lsn != LSN_MAX) {
        auto frame = bpage->zip.data;

        if (frame == nullptr) {
          frame = ((buf_block_t *)bpage)->frame;
        }
        const lsn_t frame_lsn = mach_read_from_8(frame + FIL_PAGE_LSN);

        arch_page_sys->track_page(bpage, buf_pool->track_page_lsn, frame_lsn,
                                  false);
      }
    });

    mutex_exit(block_mutex);

    if (flush_type == BUF_FLUSH_SINGLE_PAGE) {
      mutex_exit(&buf_pool->LRU_list_mutex);
    }

    if (flush_type == BUF_FLUSH_LIST && is_uncompressed &&
        !rw_lock_sx_lock_nowait(rw_lock, BUF_IO_WRITE, UT_LOCATION_HERE)) {
      if (!fsp_is_system_temporary(bpage->id.space()) && dblwr::is_enabled()) {
        dblwr::force_flush(flush_type, buf_pool_index(buf_pool));
      } else {
        buf_flush_sync_datafiles();
      }

      rw_lock_sx_lock_gen(rw_lock, BUF_IO_WRITE, UT_LOCATION_HERE);
    }

    /* If there is an observer that wants to know if the
    asynchronous flushing was sent then notify it.
    Note: we set flush observer to a page with x-latch, so we can
    guarantee that notify_flush and notify_remove are called in pair
    with s-latch on a uncompressed page. */
    if (bpage->get_flush_observer() != nullptr) {
      bpage->get_flush_observer()->notify_flush(buf_pool, bpage);
    }

    /* Even though bpage is not protected by any mutex at this
    point, it is safe to access bpage, because it is io_fixed and
    oldest_modification != 0.  Thus, it cannot be relocated in the
    buffer pool or removed from flush_list or LRU_list. */

    buf_flush_write_block_low(bpage, flush_type, sync);
  }

  return flush;
}
```

## 동작 흐름

```text
 L1045  block_mutex 를 쥔 채로 들어온다 (flush 하면 풀고 돌아간다)
 L1047  buf_flush_ready_for_flush(type)       (debug assert)
 L1056  no_fix_count = buf_fix_count == 0
 L1058  압축 전용 페이지 (FILE_PAGE 아님)   flush = true, 래치 없음
 L1061  고정돼 있고 LIST 가 아니면, 또는 고정된 임시 테이블스페이스 페이지
          flush = false                     비싼 SX 시도를 건너뛰는 휴리스틱 (L1065)
 L1070  그 밖
          LRU, SINGLE_PAGE  L1073  rw_lock_sx_lock_nowait    못 잡으면 flush = false
          LIST              L1076  flush = true              SX 는 나중에 (아래 L1114)
 L1080  flush
 L1083    change_flush_state 안에서
 L1084      io_fix = BUF_IO_WRITE
 L1086      flush_type 기록
 L1088      n_flush[type]++                  배치가 끝나기를 기다리는 쪽의 카운터
 L1090      max_lsn_io 갱신
 L1108    block_mutex 해제 (SINGLE_PAGE 면 LRU_list_mutex 도)
 L1114    LIST 이고 SX nowait 실패
 L1116      doublewrite 켜짐 -> dblwr::force_flush     큐를 먼저 비운다
            아니면          -> buf_flush_sync_datafiles
 L1122      rw_lock_sx_lock_gen                  이제 기다려서 잡는다
 L1130    flush observer 알림
 L1139    [05] buf_flush_write_block_low(bpage, type, sync)
 L1142  return flush
```

```text
 쓰기로 정할지 (L1058-L1078)

 page state         buf_fix   flush_type      decision
 compressed only    any       any             write, no latch
 FILE_PAGE          0         LRU / SINGLE    write iff SX nowait succeeds
 FILE_PAGE          0         LIST            write, SX later (may wait)
 FILE_PAGE          > 0       LRU / SINGLE    skip
 FILE_PAGE          > 0       LIST            write, SX later (temp tablespace 면 skip)
```

```text
 페이지 한 장의 상태 변화 (쓰기 한 번)

 io_fix   latch   in_flush_list   oldest   시점
 NONE     -       yes             > 0      [04] L1084 전
 WRITE    -       yes             > 0      [04] L1084
 WRITE    SX      yes             > 0      [04] L1122 (LRU 는 L1073)
 WRITE    SX      yes             > 0      [05] -> [07] 쓰기 제출
 NONE     -       no              0        IO 완료, buf_flush_write_complete
 (buf0flu.cc L668-L682, SX 해제는 buf_page_io_complete 의 buf0buf.cc L6053)
```

## 결과가 쓰이는 곳

```text
 io_fix = BUF_IO_WRITE
      --> 이 페이지를 LRU 에서 내보내거나 옮기려는 쪽이 기다린다
      --> IO 완료 콜백의 buf_flush_write_complete 가 NONE 으로 되돌린다

 n_flush[type]
      --> 완료에서 --, 0 이 되면 no_flush[type] 이벤트 (buf_flush_await_no_flushing)

 SX 래치
      --> 쓰는 동안 페이지를 읽는 것(S)은 되고 바꾸는 것(X)은 막힌다
```

## 다루지 않는 것

`buf_flush_page_try`(debug 전용), 단일 페이지 LRU flush(`buf_flush_single_page_from_LRU`)가 `sync = true` 로 들어오는 경로, Flush_observer, 페이지 아카이브 추적(`arch_page_sys->track_page`)은 요약만 했다.
