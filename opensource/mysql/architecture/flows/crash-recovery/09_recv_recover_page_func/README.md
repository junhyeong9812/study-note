# recv_recover_page_func

상위: [크래시 복구](../README.md)

**페이지 하나에 쌓인 redo 레코드를 적용하는 함수다.** 페이지의 LSN 을 읽고, 레코드 목록을 앞에서부터 보며 **그 레코드를 만든 mtr 의 시작 LSN 이 page LSN 이상인 것만** 적용한다. 이미 디스크에 반영된 변경은 건너뛰므로 같은 페이지에 몇 번을 돌려도 결과가 같다. 적용은 redo 를 쓰지 않는 mtr(`MTR_LOG_NONE`) 안에서 하고, 끝나면 `buf_flush_note_modification` 으로 페이지를 dirty 로 만들어 flush list 에 붙인다. 대부분은 I/O 핸들러 스레드가 페이지를 막 읽어 들인 순간 `buf_page_io_complete` 에서 부른다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L2430-L2717 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2430-L2717))

## 실제 코드

적용할 레코드가 있는 페이지인지 본다.

`storage` / `innobase` / `log` / `log0recv.cc` L2430-L2490 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2430-L2490))

```cpp
// log0recv.cc L2430-L2490
void recv_recover_page_func(
#ifndef UNIV_HOTBACKUP
    bool just_read_in,
#endif /* !UNIV_HOTBACKUP */
    buf_block_t *block) {
  ut_ad(recv_recovery_is_on());
  mutex_enter(&recv_sys->mutex);

  if (recv_sys->apply_log_recs == false) {
    /* Log records should not be applied now */

    mutex_exit(&recv_sys->mutex);

    return;
  }

  recv_addr_t *recv_addr = recv_get_rec(block->page.id);

  if (recv_addr == nullptr || recv_addr->state == RECV_BEING_PROCESSED ||
      recv_addr->state == RECV_PROCESSED) {
// ... (L2450-L2484 생략: 이미 처리된 페이지가 다시 오는 경우를 설명하는 주석과 단언)
#endif /* !UNIV_HOTBACKUP */

    mutex_exit(&recv_sys->mutex);

    return;
  }
```

X 래치를 넘겨받고 page LSN 을 읽는다.

`storage` / `innobase` / `log` / `log0recv.cc` L2528-L2584 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2528-L2584))

```cpp
// log0recv.cc L2528-L2584
  recv_addr->state = RECV_BEING_PROCESSED;

  mutex_exit(&recv_sys->mutex);

  mtr_t mtr;

  mtr_start(&mtr);

  mtr_set_log_mode(&mtr, MTR_LOG_NONE);

  page_t *page = block->frame;

  page_zip_des_t *page_zip = buf_block_get_page_zip(block);

#ifndef UNIV_HOTBACKUP
  if (just_read_in) {
    /* Move the ownership of the x-latch on the page to
    this OS thread, so that we can acquire a second
    x-latch on it.  This is needed for the operations to
    the page to pass the debug checks. */

    rw_lock_x_lock_move_ownership(&block->lock);
  }

  bool success = buf_page_get_known_nowait(
      RW_X_LATCH, block, Cache_hint::KEEP_OLD, __FILE__, __LINE__, &mtr);
  ut_a(success);

  buf_block_dbg_add_level(block, SYNC_NO_ORDER_CHECK);
#endif /* !UNIV_HOTBACKUP */

  /* Read the newest modification lsn from the page */
  lsn_t page_lsn = mach_read_from_8(page + FIL_PAGE_LSN);

#ifndef UNIV_HOTBACKUP

  /* It may be that the page has been modified in the buffer
  pool: read the newest modification LSN there */

  lsn_t page_newest_lsn;

  page_newest_lsn = buf_page_get_newest_modification(&block->page);

  if (page_newest_lsn) {
    page_lsn = page_newest_lsn;
  }
  // ... (L2574-L2581 생략: 백업(MEB) 빌드 전용 변수)
  lsn_t end_lsn = 0;
  lsn_t start_lsn = 0;
  bool modification_to_page = false;
```

레코드를 적용한다.

`storage` / `innobase` / `log` / `log0recv.cc` L2586-L2672 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2586-L2672))

```cpp
// log0recv.cc L2586-L2672
  for (auto recv : recv_addr->rec_list) {
    end_lsn = recv->end_lsn;
#ifndef UNIV_HOTBACKUP
    ut_ad(end_lsn <= log_sys->m_scanned_lsn);
#endif /* !UNIV_HOTBACKUP */

    byte *buf = nullptr;

    if (recv->len > RECV_DATA_BLOCK_SIZE) {
      /* We have to copy the record body to a separate
      buffer */

      buf = static_cast<byte *>(
          ut::malloc_withkey(UT_NEW_THIS_FILE_PSI_KEY, recv->len));

      recv_data_copy_to_buf(buf, recv);
    } else if (recv->data != nullptr) {
      buf = ((byte *)(recv->data)) + sizeof(recv_data_t);
    } else {
      /* Redo record that does not have a payload, such as
       MLOG_UNDO_ERASE_END, MLOG_COMP_PAGE_CREATE, MLOG_INIT_FILE_PAGE2 etc.
     */
      ut_ad(recv->data == nullptr);
      ut_ad(recv->len == 0);
    }

    if (recv->type == MLOG_INIT_FILE_PAGE) {
      page_lsn = page_newest_lsn;

      memset(FIL_PAGE_LSN + page, 0, 8);
      memset(UNIV_PAGE_SIZE - FIL_PAGE_END_LSN_OLD_CHKSUM + page, 0, 8);

      if (page_zip) {
        memset(FIL_PAGE_LSN + page_zip->data, 0, 8);
      }
    }

    /* Ignore applying the redo logs for tablespace that is
    truncated. Truncated tablespaces are handled explicitly
    post-recovery, where we will restore the tablespace back
    to a normal state.

    Applying redo at this stage will cause problems because the
    redo will have action recorded on page before tablespace
    was re-inited and that would lead to a problem later. */

    if (recv->start_lsn >= page_lsn
#ifndef UNIV_HOTBACKUP
        && undo::is_active(recv_addr->space)
#endif /* !UNIV_HOTBACKUP */
    ) {

      if (!modification_to_page) {
#ifndef UNIV_HOTBACKUP
        ut_a(recv_needed_recovery);
#endif /* !UNIV_HOTBACKUP */
        modification_to_page = true;
        start_lsn = recv->start_lsn;
      }

      DBUG_PRINT("ib_log", ("apply " LSN_PF ":"
                            " %s len " ULINTPF " page %u:%u",
                            recv->start_lsn, get_mlog_string(recv->type),
                            recv->len, recv_addr->space, recv_addr->page_no));
      /* Since buf can be a nullptr for record types without a payload we can
      end up with nullptr + 0 if we calc buf + recv->len. This is undefined
      behaviour. Avoid this by only calculating the end_ptr when there's
      actual data to work with, otherwise set it to nullptr. */
      unsigned char *buf_end = nullptr;
      if (buf != nullptr) {
        buf_end = buf + recv->len;
      }
      recv_parse_or_apply_log_rec_body(recv->type, buf, buf_end,
                                       recv_addr->space, recv_addr->page_no,
                                       block, &mtr, ULINT_UNDEFINED, LSN_MAX);

    // ... (L2662-L2666 생략: 백업 빌드 전용 카운터)
    }

    if (recv->len > RECV_DATA_BLOCK_SIZE) {
      ut::free(buf);
    }
  }
```

페이지를 dirty 로 만들고 상태를 바꾼다.

`storage` / `innobase` / `log` / `log0recv.cc` L2682-L2717 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L2682-L2717))

```cpp
// log0recv.cc L2682-L2717
  if (modification_to_page) {
    /* page lsn must be less than the lsn of a log record here. Otherwise,
    it would mean we are moving the page back in time. Also, indirectly this
    verifies the end_lsn is not 0. */
    ut_a(page_lsn < end_lsn);
#ifdef UNIV_HOTBACKUP
    UT_NOT_USED(start_lsn);
    /* MEB uses this PAGE_LSN to init page for writing in the
    meb_apply_log_record() */
    mach_write_to_8(FIL_PAGE_LSN + page, end_lsn);
#else  /* !UNIV_HOTBACKUP */
    buf_flush_note_modification(block, start_lsn, end_lsn, nullptr);
#endif /* !UNIV_HOTBACKUP */
  }

  /* Make sure that committing mtr does not change the modification
  LSN values of page */
  ut_a(mtr.get_log_mode() == MTR_LOG_NONE);

  mtr_commit(&mtr);

  mutex_enter(&recv_sys->mutex);

  if (recv_max_page_lsn < page_lsn) {
    recv_max_page_lsn = page_lsn;
  }

  recv_addr->state = RECV_PROCESSED;
  one_less_page_to_recover();

  mutex_exit(&recv_sys->mutex);

#ifdef UNIV_HOTBACKUP
  ib::trace_2() << "Applied " << applied_recs << " Skipped " << skipped_recs;
#endif /* UNIV_HOTBACKUP */
}
```

읽기 완료 쪽의 호출 자리다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L5957-L5968 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L5957-L5968))

```cpp
// buf0buf.cc L5957-L5968
    if (recv_recovery_is_on()) {
      /* Pages must be uncompressed for crash recovery. */
      ut_a(uncompressed);
      recv_recover_page(true, (buf_block_t *)bpage);
    } else if (uncompressed && !Compression::is_compressed_page(frame) &&
               fil_page_get_type(frame) == FIL_PAGE_INDEX &&
               page_is_leaf(frame) &&
               !fsp_is_system_temporary(bpage->id.space()) &&
               !fsp_is_undo_tablespace(bpage->id.space()) &&
               !bpage->was_stale()) {
      ibuf_merge_or_delete_for_page((buf_block_t *)bpage, bpage->id,
                                    &bpage->size, true);
```

## 동작 흐름

```text
 L2438  apply_log_recs == false 면 return        스캔 중이라 아직 적용할 때가 아니다
 L2446  recv_addr = recv_get_rec(page_id)
 L2448  없거나 BEING_PROCESSED / PROCESSED 면 return
 L2528  state = RECV_BEING_PROCESSED
 L2536  mtr_set_log_mode(MTR_LOG_NONE)           적용이 redo 를 만들지 않는다
 L2549  막 읽은 페이지면 X 래치 소유권을 이 스레드로 옮긴다
          (읽기를 건 스레드가 걸어 둔 pass X 래치, buffer-pool-fetch [07])
 L2552  buf_page_get_known_nowait(RW_X_LATCH)    두 번째 X 래치로 mtr 에 올린다
 L2560  page_lsn = FIL_PAGE_LSN
 L2569  버퍼 풀에서 이미 수정된 적이 있으면 newest_modification 으로

 L2586  for recv in rec_list
 L2594    본문을 연속 버퍼로 (RECV_DATA_BLOCK_SIZE 를 넘으면 malloc 해서 복사)
 L2612    MLOG_INIT_FILE_PAGE 면 page_lsn = page_newest_lsn, 프레임의 FIL_PAGE_LSN 을 0 으로 (L2613-L2616)
 L2632    recv->start_lsn >= page_lsn 이고 undo truncate 중인 공간이 아니면
 L2638      첫 적용이면 start_lsn 기록
 L2658      recv_parse_or_apply_log_rec_body(type, buf, ..., block, &mtr)   적용

 L2682  하나라도 적용했으면
 L2686    ut_a(page_lsn < end_lsn)                페이지를 과거로 돌리지 않는다
 L2693    buf_flush_note_modification(block, start_lsn, end_lsn)
            newest = end_lsn, 깨끗했으면 start_lsn 으로 flush list 에 (buf0flu.ic L76, L96)
 L2701  mtr_commit                                래치 해제, redo 는 쓰지 않는다
 L2705  recv_max_page_lsn 갱신
 L2709  state = RECV_PROCESSED, L2710 남은 페이지 수 -1
```

비교에 쓰는 값이 레코드 자신의 LSN 이 아니라 **그 레코드를 만든 mtr 의 시작 LSN** 이라는 점이 요점이다. mtr 은 페이지를 한꺼번에 바꾸고 page LSN 에는 mtr 의 끝 LSN 이 적힌다. 그래서 "이 mtr 이 시작된 뒤의 LSN 이 페이지에 적혀 있으면" 그 mtr 전체가 이미 반영된 것이다.

```text
 mtr 과 page LSN 의 관계

 mtr M1: start 1000, end 1100   페이지 P 수정 -> P.FIL_PAGE_LSN = 1100 (플러시되었다면)
 mtr M2: start 1100, end 1250   페이지 P 수정 -> 플러시 전 크래시

 복구 시 P 의 rec_list: [M1 의 레코드 start 1000] [M2 의 레코드 start 1100]
   page_lsn = 1100
   M1  1000 >= 1100 ?  아니오  건너뜀
   M2  1100 >= 1100 ?  예      적용
   적용 후 newest_modification = 1250
```

## 결과가 쓰이는 곳

```text
 적용된 frame (dirty, flush list)
      --> [08] 끝의 BUF_FLUSH_LIST 배치가 디스크에 쓴다
      --> 이때 페이지 끝의 FIL_PAGE_LSN 이 end_lsn 으로 적힌다
 n_pages_to_recover
      --> 0 이 되면 [08] 의 await_zero 가 풀린다
 recv_max_page_lsn
      --> [02] 가 scanned_lsn 과 비교해 "페이지가 로그보다 앞섰는가"를 본다
```

## 다루지 않는 것

`recv_parse_or_apply_log_rec_body` 의 mlog 타입별 적용 함수들(레코드 삽입, 삭제 표시, 페이지 생성 등), 페이지 추적(`arch_page_sys->track_page`, 클론용), 압축 페이지의 zip 사본 처리, MEB 백업 빌드(`UNIV_HOTBACKUP`)의 적용 경로는 이 함수의 곁가지라 요약만 했다.
