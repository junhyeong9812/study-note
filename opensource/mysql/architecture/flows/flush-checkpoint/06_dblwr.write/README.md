# dblwr::write

상위: [페이지 플러시, doublewrite, 체크포인트](../README.md)

**페이지 쓰기가 doublewrite 를 탈지 정하는 갈림길이다.** 갈래는 셋이다. doublewrite 가 필요 없으면(읽기 전용, 임시 테이블스페이스, 꺼짐, redo 비활성 중) 데이터 파일에 바로 쓰고, 비동기 배치 flush(LRU, LIST)면 [07] `Double_write::submit` 으로 큐에 넣고, 단일 페이지나 동기 쓰기면 `sync_page_flush` 로 그 자리에서 doublewrite 파일에 쓰고 fsync 한 뒤 데이터 파일에 쓴다. doublewrite 의 목적은 코드 주석 한 줄에 있다. 임시 테이블스페이스를 건너뛰는 이유가 "복구되지 않으니 torn write 를 신경 쓰지 않는다"(L2505-L2506)이다. 반쯤 쓰인 페이지를 복구가 되살릴 사본이 doublewrite 파일이다.

## 위치

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L2481-L2556 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L2481-L2556))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L2481-L2556 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L2481-L2556))

```cpp
// buf0dblwr.cc L2481-L2556
dberr_t dblwr::write(buf_flush_t flush_type, buf_page_t *bpage,
                     bool sync) noexcept {
  dberr_t err;
  const space_id_t space_id = bpage->id.space();

  ut_ad(bpage->current_thread_has_io_responsibility());
  /* This is not required for correctness, but it aborts the processing early.
   */
  if (bpage->was_stale()) {
    /* Disable batch completion in write_complete(). */
    bpage->set_dblwr_batch_id(std::numeric_limits<uint16_t>::max());
    buf_page_free_stale_during_write(
        bpage, buf_page_get_state(bpage) == BUF_BLOCK_FILE_PAGE);
    /* We don't hold io_responsibility here no matter which path through ifs and
    elses we've got here, but we can't assert:
      ut_ad(!bpage->current_thread_has_io_responsibility());
    because bpage could be freed by the time we got here. */
    return DB_SUCCESS;
  }

  if (srv_read_only_mode || fsp_is_system_temporary(space_id) ||
      !dblwr::is_enabled() || Double_write::s_instances == nullptr ||
      mtr_t::s_logging.dblwr_disabled()) {
    /* Skip the double-write buffer since it is not needed. Temporary
    tablespaces are never recovered, therefore we don't care about
    torn writes. */
    bpage->set_dblwr_batch_id(std::numeric_limits<uint16_t>::max());
    err = Double_write::write_to_datafile(bpage, sync, nullptr);
    if (err == DB_PAGE_IS_STALE || err == DB_TABLESPACE_DELETED) {
      if (bpage->was_io_fixed()) {
        buf_page_free_stale_during_write(
            bpage, buf_page_get_state(bpage) == BUF_BLOCK_FILE_PAGE);
      }
      err = DB_SUCCESS;
    } else if (sync) {
      ut_ad(flush_type == BUF_FLUSH_LRU || flush_type == BUF_FLUSH_SINGLE_PAGE);

      if (err == DB_SUCCESS) {
        fil_flush(space_id);
      }
      /* true means we want to evict this page from the LRU list as well. */
      buf_page_io_complete(bpage, true);
    }

  } else {
    ut_d(auto page_id = bpage->id);

    /* Encrypt the page here, so that the same encrypted contents are written
    to the dblwr file and the data file. */
    IORequest type(IORequest::WRITE);
    file::Block *e_block = dblwr::get_encrypted_frame(bpage, type);

    if (!sync && flush_type != BUF_FLUSH_SINGLE_PAGE) {
      MONITOR_INC(MONITOR_DBLWR_ASYNC_REQUESTS);

      ut_d(bpage->release_io_responsibility());
      Double_write::submit(flush_type, bpage, e_block);
      err = DB_SUCCESS;
#ifdef UNIV_DEBUG
      if (dblwr::Force_crash == page_id) {
        force_flush(flush_type, buf_pool_index(buf_pool_from_bpage(bpage)));
      }
#endif /* UNIV_DEBUG */
    } else {
      MONITOR_INC(MONITOR_DBLWR_SYNC_REQUESTS);
      /* Disable batch completion in write_complete(). */
      bpage->set_dblwr_batch_id(std::numeric_limits<uint16_t>::max());
      err = Double_write::sync_page_flush(bpage, e_block);
    }
  }
  /* We don't hold io_responsibility here no matter which path through ifs and
  elses we've got here, but we can't assert:
    ut_ad(!bpage->current_thread_has_io_responsibility());
  because bpage could be freed by the time we got here. */
  return err;
}
```

동기 경로다. 슬롯 하나짜리 세그먼트에 쓰고 fsync 한 다음에야 데이터 파일에 쓴다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L1651-L1704 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L1651-L1704))

```cpp
// buf0dblwr.cc L1651-L1704
dberr_t Double_write::sync_page_flush(buf_page_t *bpage,
                                      file::Block *e_block) noexcept {
#ifdef UNIV_DEBUG
  ut_d(auto page_id = bpage->id);

  if (dblwr::Force_crash == page_id) {
    auto frame = reinterpret_cast<const buf_block_t *>(bpage)->frame;
    const auto p = reinterpret_cast<byte *>(frame);

    ut_ad(page_get_space_id(p) == dblwr::Force_crash.space());
    ut_ad(page_get_page_no(p) == dblwr::Force_crash.page_no());
  }
#endif /* UNIV_DEBUG */

  Segment *segment{};

  while (!s_single_segments->dequeue(segment)) {
    std::this_thread::yield();
  }

  single_write(segment, bpage, e_block);

#ifndef _WIN32
  if (is_fsync_required()) {
    segment->flush();
  }
#endif /* !_WIN32 */

#ifdef UNIV_DEBUG
  if (dblwr::Force_crash == page_id) {
    DBUG_SUICIDE();
  }
#endif /* UNIV_DEBUG */

  auto err = write_to_datafile(bpage, true, e_block);

  if (err == DB_SUCCESS) {
    fil_flush(bpage->id.space());
  } else {
    /* This block is not freed if the write_to_datafile doesn't succeed. */
    if (e_block != nullptr) {
      os_free_block(e_block);
    }
  }

  while (!s_single_segments->enqueue(segment)) {
    UT_RELAX_CPU();
  }

  /* true means we want to evict this page from the LRU list as well. */
  buf_page_io_complete(bpage, true);

  return DB_SUCCESS;
}
```

복구 쪽에서 사본을 쓰는 조건이다. 데이터 파일의 페이지가 손상되었거나 전부 0 일 때만 사본으로 덮고(L3134-L3135 이후), 사본까지 손상이면 멈춘다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L3071-L3112 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L3071-L3112))

```cpp
// buf0dblwr.cc L3071-L3112
  if (data_file_page.is_corrupted()) {
    ib::info(ER_IB_MSG_DBLWR_1315) << "Database page corruption or"
                                   << " a failed file read of page " << page_id
                                   << ". Trying to recover it from the"
                                   << " doublewrite file.";

    dberr_t dblwr_err;

    const bool dblwr_corrupted =
        is_dblwr_page_corrupted(page, space, page_no, &dblwr_err);

    if (dblwr_corrupted) {
      std::ostringstream out;

      out << "Dumping the data file page (page_id=" << page_id << "):";
      ib::error(ER_IB_MSG_DBLWR_1304, out.str().c_str());

      buf_page_print(buffer.begin(), page_size, BUF_PAGE_PRINT_NO_CRASH);

      out.str("");
      out << "Dumping the DBLWR page (dblwr_page_no=" << dblwr_page_no << "):";
      ib::error(ER_IB_MSG_DBLWR_1295, out.str().c_str());

      buf_page_print(page, page_size, BUF_PAGE_PRINT_NO_CRASH);

      ib::fatal(UT_LOCATION_HERE, ER_IB_MSG_DBLWR_1306);
    }

  } else {
    bool data_page_zeroes = buf_page_is_zeroes(buffer.begin(), page_size);
    bool dblwr_zeroes = buf_page_is_zeroes(page, page_size);
    dberr_t dblwr_err;
    const bool dblwr_corrupted =
        is_dblwr_page_corrupted(page, space, page_no, &dblwr_err);

    if (data_page_zeroes && !dblwr_zeroes && !dblwr_corrupted) {
      /* Database page contained only zeroes, while a valid copy is
      available in dblwr buffer. */
    } else {
      /* Database page is fine.  No need to restore from dblwr. */
      return false;
    }
```

## 동작 흐름

```text
 L2486  이 스레드가 IO 책임을 쥐고 있어야 한다 (debug)
 L2489  stale 페이지면 해제하고 끝
 L2501  srv_read_only || 임시 테이블스페이스 || dblwr 꺼짐 || 인스턴스 없음 || redo 비활성 dblwr off
 L2507    batch_id = MAX (배치 완료 처리에서 빠진다)
 L2508    Double_write::write_to_datafile(bpage, sync)     바로 데이터 파일 AIO
 L2515    sync 면 fil_flush, buf_page_io_complete
       else
 L2531    e_block = get_encrypted_frame                    한 번 암호화한 내용을 두 곳에 똑같이
 L2533    !sync && type != SINGLE_PAGE (배치 flush)
 L2537      [07] Double_write::submit(type, bpage, e_block)   큐에 넣고 바로 돌아온다
          else (단일 페이지, 동기)
 L2548      Double_write::sync_page_flush(bpage, e_block)
              L1667  s_single_segments 에서 세그먼트 하나를 뺀다
              L1671  single_write                          doublewrite 파일에 쓴다
              L1675  fsync (O_DIRECT 계열이 아니면)
              L1685  write_to_datafile(sync = true)        데이터 파일에 쓴다
              L1688  fil_flush                             데이터 파일 fsync
              L1696  세그먼트 반납
              L1701  buf_page_io_complete(bpage, evict = true)
```

```text
 세 갈래 (L2501-L2549)

 condition                                       path             doublewrite
 read-only, temp space, dblwr off, redo off      write_to_datafile  none
 flush_type LRU / LIST, !sync                    submit (queue)     batch, async
 flush_type SINGLE_PAGE or sync                  sync_page_flush    single slot, sync
```

doublewrite 가 막는 것은 페이지 한 장이 반만 쓰인 상태(torn write)다. doublewrite 파일 쓰기를 끝낸 뒤(fsync 는 `innodb_flush_method` 가 O_DIRECT 계열이 아닐 때만 한다, `is_fsync_required` L805-L808) 데이터 파일에 쓰므로, 두 곳이 동시에 찢어지는 순간은 없다.

```text
 쓰는 도중 죽었을 때 (doublewrite ON, 순서: dblwr 파일 -> fsync -> 데이터 파일)

 1) dblwr 파일에 쓰는 도중
      dblwr 사본: 찢어짐    데이터 파일: 옛 버전, 온전
      --> 데이터 페이지가 멀쩡하므로 사본을 쓰지 않는다 (L3110-L3111)
 2) dblwr fsync 뒤, 데이터 파일에 쓰는 도중
      dblwr 사본: 온전      데이터 파일: 찢어짐
      --> is_corrupted 이므로 사본으로 덮는다 (L3071, L3134)
 3) 데이터 파일 쓰기 뒤
      dblwr 사본: 온전      데이터 파일: 새 버전, 온전
      --> 사본을 쓰지 않는다

 데이터 파일 페이지가 손상인데 사본도 손상이면 ib::fatal (L3082-L3096)
 사본 복구와 redo 적용이 어떤 순서로 이어지는지는 [크래시 복구] 에서 본다
```

## 결과가 쓰이는 곳

```text
 submit 한 페이지
      --> [07] 배치가 차거나 force_flush 에서 doublewrite 파일과 데이터 파일로 나간다

 write_to_datafile 의 AIO
      --> 완료 콜백 buf_page_io_complete -> buf_flush_write_complete -> dblwr::write_complete

 doublewrite 파일의 사본
      --> 복구 초기 recv::Pages::recover 가 읽는다   [크래시 복구]
```

## 다루지 않는 것

암호화와 투명 압축(`get_encrypted_frame`, `os_file_compress_page`), reduced 모드(`DETECT_ONLY`)의 페이지 번호만 적는 `.bdblwr` 파일, stale 페이지 처리(`buf_page_free_stale_during_write`), doublewrite 파일 개수와 세그먼트 크기 설정(`innodb_doublewrite_files`, `innodb_doublewrite_pages`)은 요약만 했다.
