# recv_init_crash_recovery

상위: [크래시 복구](../README.md)

**"이번 기동은 크래시 복구다"를 확정하는 함수다.** `recv_needed_recovery` 를 켜고, doublewrite 복사본으로 **찢어진 페이지(torn page)** 를 고치고, 복구 중 dirty 페이지를 내보낼 recv_writer 스레드를 띄운다. 함수 자체는 짧고, 볼거리는 doublewrite 복원의 판정이다. 데이터 파일의 페이지가 체크섬으로 깨져 있으면 doublewrite 에 있던 온전한 사본으로 덮어쓴다. 이 복원은 페이지를 읽어 redo 를 적용하는 [08] 보다 먼저 일어난다. 깨진 채로 읽히면 읽기 완료가 그 페이지를 손상으로 처리하기 때문이다(buf0buf.cc L5942-L5950).

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L3744-L3764 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3744-L3764))

## 실제 코드

`storage` / `innobase` / `log` / `log0recv.cc` L3742-L3764 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3742-L3764))

```cpp
// log0recv.cc L3742-L3764
/** Initialize crash recovery environment. Can be called iff
recv_needed_recovery == false. */
static void recv_init_crash_recovery() {
  ut_ad(!srv_read_only_mode);
  ut_a(!recv_needed_recovery);

  recv_needed_recovery = true;

  ib::info(ER_IB_MSG_726);
  ib::info(ER_IB_MSG_727);

  recv_sys->dblwr->recover();

  if (srv_force_recovery < SRV_FORCE_NO_LOG_REDO) {
    /* Spawn the background thread to flush dirty pages
    from the buffer pools. */

    srv_threads.m_recv_writer =
        os_thread_create(recv_writer_thread_key, 0, recv_writer_thread);

    srv_threads.m_recv_writer.start();
  }
}
```

doublewrite 에서 읽어 둔 페이지들을 돌며 복원한다. `space` 가 `nullptr` 이면 지금 열려 있는 테이블스페이스 전부가 대상이다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L3162-L3205 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L3162-L3205))

```cpp
// buf0dblwr.cc L3162-L3205
void recv::Pages::recover(fil_space_t *space) noexcept {
#ifndef UNIV_HOTBACKUP
  /* For cloned database double write pages should be ignored. However,
  given the control flow, we read the pages in anyway but don't recover
  from the pages we read in. */

  if (!dblwr::is_enabled() || recv_sys->is_cloned_db) {
    return;
  }

  auto recover_all = (space == nullptr);

  for (const auto &page : m_pages) {
    if (page->m_recovered) {
      continue;
    }

    auto ptr = page->m_buffer.begin();
    auto page_no = page_get_page_no(ptr);
    auto space_id = page_get_space_id(ptr);

    if (recover_all) {
      space = fil_space_get(space_id);

      if (space == nullptr) {
        /* Maybe we have dropped the tablespace
        and this page once belonged to it: do nothing. */
        continue;
      }

    } else if (space->id != space_id) {
      continue;
    }

    fil_space_open_if_needed(space);

    page->m_recovered =
        dblwr_recover_page(page->m_no, space, page_no, page->m_buffer.begin());
  }

  reduced_recover(space);
  fil_flush_file_spaces();
#endif /* !UNIV_HOTBACKUP */
}
```

페이지 하나의 판정과 복원이다.

`storage` / `innobase` / `buf` / `buf0dblwr.cc` L3016-L3146 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0dblwr.cc#L3016-L3146))

```cpp
// buf0dblwr.cc L3016-L3146
/** Recover a page from the doublewrite buffer.
@param[in]      dblwr_page_no         Page number if the doublewrite buffer
@param[in]      space                       Tablespace the page belongs to
@param[in]      page_no                   Page number in the tablespace
@param[in]      page                        Data to write to <space, page_no>
@return true if page was restored to the tablespace */
bool dblwr::recv::Pages::dblwr_recover_page(page_no_t dblwr_page_no,
                                            fil_space_t *space,
                                            page_no_t page_no,
                                            byte *page) noexcept {
  /* For cloned database double write pages should be ignored. However,
  given the control flow, we read the pages in anyway but don't recover
  from the pages we read in. */
  ut_a(!recv_sys->is_cloned_db);

  Buffer buffer{1};

  if (page_no >= space->size) {
    /* Do not report the warning if the tablespace is going to be truncated. */
    if (!undo::is_active(space->id)) {
      ib::warn(ER_IB_MSG_DBLWR_1313)
          << "Page# " << dblwr_page_no
          << " stored in the doublewrite file is"
             " not within data file space bounds "
          << space->size << " bytes:  page : " << page_id_t(space->id, page_no);
    }

    return false;
  }

  const page_size_t page_size(space->flags);
  const page_id_t page_id(space->id, page_no);

  /* We want to ensure that for partial reads the
  unread portion of the page is NUL. */
  memset(buffer.begin(), 0x0, page_size.physical());

  IORequest request;

  request.dblwr();

  /* Read in the page from the data file to compare. */
  auto err = fil_io(request, true, page_id, page_size, 0, page_size.physical(),
                    buffer.begin(), nullptr);

  if (err != DB_SUCCESS) {
    ib::warn(ER_IB_MSG_DBLWR_1314)
        << "Double write file recovery: " << page_id << " read failed with "
        << "error: " << ut_strerr(err);
  }

  /* Is the page read from the data file corrupt? */
  BlockReporter data_file_page(true, buffer.begin(), page_size,
                               fsp_is_checksum_disabled(space->id));

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
  }

  ut_ad(!Encryption::is_encrypted_page(page));

  bool found = false;
  lsn_t reduced_lsn = LSN_MAX;
  std::tie(found, reduced_lsn) = find_entry(page_id);
  lsn_t dblwr_lsn = mach_read_from_8(page + FIL_PAGE_LSN);

  /* If we find a newer version of page that is in reduced dblwr, we
  shouldn't restore the old/stale page from regular dblwr. We should
  abort */
  if (found && reduced_lsn != LSN_MAX && reduced_lsn > dblwr_lsn) {
    ib::fatal(UT_LOCATION_HERE, ER_REDUCED_DBLWR_PAGE_FOUND,
              space->files.front().name, page_id.space(), page_id.page_no());
  }

  /* Recovered data file pages are written out as uncompressed. */
  IORequest write_request(IORequest::WRITE);
  write_request.disable_compression();

  /* Write the good page from the doublewrite buffer to the
  intended position. */

  err = fil_io(write_request, true, page_id, page_size, 0, page_size.physical(),
               const_cast<byte *>(page), nullptr);

  ut_a(err == DB_SUCCESS || err == DB_TABLESPACE_DELETED);

  ib::info(ER_IB_MSG_DBLWR_1308)
      << "Recovered page " << page_id << " from the doublewrite buffer.";

  return true;
}
```

아직 열리지 않았던 테이블스페이스는 [08] 에서 열 때 같은 복원을 한 번 더 거친다.

`storage` / `innobase` / `fil` / `fil0fil.cc` L9875-L9880 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/fil/fil0fil.cc#L9875-L9880))

```cpp
// fil/fil0fil.cc L9875-L9880
    if (!recv_sys->dblwr->empty()) {
      recv_sys->dblwr->recover(space);
    } else {
      ib::info(ER_IB_MSG_DBLWR_1317) << "DBLWR recovery skipped for "
                                     << space->name << " ID: " << space->id;
    }
```

## 동작 흐름

```text
 recv_init_crash_recovery (L3744)
 L3748  recv_needed_recovery = true
 L3750  ER_IB_MSG_726 "Database was not shutdown normally!", 727 "Starting crash recovery."
 L3753  recv_sys->dblwr->recover()                 열린 테이블스페이스 전부
 L3755  force_recovery < SRV_FORCE_NO_LOG_REDO 면
 L3759    recv_writer 스레드 생성, 시작

 recv::Pages::recover (buf0dblwr.cc L3162)
 L3168  dblwr 가 꺼져 있거나 클론이면 아무것도 안 함
 L3174  dblwr 파일에서 읽어 둔 페이지마다
 L3175    이미 복원했으면 건너뜀
 L3184    space = fil_space_get(space_id)          없으면 건너뜀 (아직 안 열렸거나 드롭됨)
 L3198    m_recovered = dblwr_recover_page(...)
 L3202  reduced_recover, L3203 fil_flush_file_spaces
```

한 페이지의 판정은 "데이터 파일 쪽이 깨졌는가"가 먼저다. 데이터 파일 쪽이 멀쩡하면 doublewrite 사본은 쓰지 않는다.

```text
 dblwr_recover_page 의 판정 (buf0dblwr.cc L3022)

 L3033  page_no >= space->size                            범위 밖, 복원 안 함
 L3058  데이터 파일에서 같은 페이지를 동기로 읽는다
 L3071  데이터 파일 페이지가 깨졌는가 (BlockReporter)
          예   L3080  dblwr 사본도 깨졌는가
                        예   두 사본을 덤프하고 ib::fatal (L3096)  복구 불가
                        아니오 -> 복원으로
          아니오 L3106 데이터 페이지가 전부 0 이고 dblwr 사본이 멀쩡하면 -> 복원으로
                 그 밖                                      L3111 복원 안 함
 L3119  reduced dblwr 에 더 새로운 LSN 이 있으면 ib::fatal (L3126)
 L3137  dblwr 사본을 데이터 파일 제자리에 동기로 쓴다
 L3145  return true
```

```text
 찢어진 페이지가 생기고 고쳐지는 시간축

 크래시 전, 페이지 클리너 ([페이지 플러시, doublewrite] 흐름)
   1. dblwr 파일에 페이지 사본을 먼저 쓴다
   2. 데이터 파일 제자리에 쓰는 도중 크래시 (예: 16KB 중 앞부분만 새 내용)
 재시작
   3. fsp0sysspace.cc L529 dblwr->load: dblwr 파일의 사본을 메모리로
   4. 이 함수 L3753 recover(): 데이터 파일 페이지 체크섬 실패 -> dblwr 사본으로 덮어쓰기
      "Write the good page from the doublewrite buffer" (L3134 주석)
   5. [09] redo 적용: page LSN 이후의 변경만 다시
```

## 결과가 쓰이는 곳

```text
 온전해진 데이터 파일 페이지
      --> [08] 이 읽어 [09] 가 redo 를 적용한다
          깨진 채였다면 buf_page_io_complete 가 손상으로 처리했을 페이지다
 recv_needed_recovery
      --> [09] 가 적용 전에 단언한다 (log0recv.cc L2640)
 recv_writer 스레드
      --> 100ms 마다 BUF_FLUSH_LRU 요청을 페이지 클리너에 보낸다 (log0recv.cc L727-L752)
          함수 주석: "flushing dirty pages from the buffer pools" (L704-L705)
```

## 다루지 않는 것

doublewrite 파일의 형식과 `dblwr::recv::load`, reduced doublewrite(`innodb_doublewrite=DETECT_ONLY` 류)의 `reduced_recover`, 구식 시스템 테이블스페이스 dblwr 영역(`dblwr::v1`), 암호화된 페이지의 dblwr 사본은 이 함수의 곁가지라 요약만 했다. doublewrite 에 쓰는 쪽은 [페이지 플러시, doublewrite, 체크포인트](../../flush-checkpoint/README.md)에 있다.
