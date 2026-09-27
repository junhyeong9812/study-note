# recv_recovery_from_checkpoint_finish

상위: [크래시 복구](../README.md)

**redo 복구 단계를 닫는 함수다.** `recv_recovery_on` 을 끄고, recv_writer 스레드가 끝날 때까지 기다리고, 복구 중 모아 둔 동적 메타데이터를 호출자에게 넘긴 뒤 `recv_sys` 의 자원을 해제한다. 마지막으로 구버전이 초기화하지 않은 채 남겼을 수 있는 시스템 페이지 네 장의 타입을 확인한다. 이 함수 이후로 읽히는 페이지에는 더 이상 redo 가 적용되지 않는다. 호출자 [01] 은 이 직전에 `buf_flush_sync_all_buf_pools` 로 모든 dirty 페이지를 이미 내렸다.

## 위치

`storage` / `innobase` / `log` / `log0recv.cc` L3950-L4004 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3950-L4004))

## 실제 코드

`storage` / `innobase` / `log` / `log0recv.cc` L3950-L4004 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3950-L4004))

```cpp
// log0recv.cc L3950-L4004
MetadataRecover *recv_recovery_from_checkpoint_finish(bool aborting) {
  /* Make sure that the recv_writer thread is done. This is
  required because it grabs various mutexes and we want to
  ensure that when we enable sync_order_checks there is no
  mutex currently held by any thread. */
  mutex_enter(&recv_sys->writer_mutex);

  /* Restore state. */
  if (recv_sys->is_meb_db) dblwr::g_mode = recv_sys->dblwr_state;

  /* Free the resources of the recovery system */
  recv_recovery_on = false;

  /* By acquiring the mutex we ensure that the recv_writer thread won't trigger
  any more LRU batches. Now wait for currently in progress batches to finish.
  Note that BUF_FLUSH_LIST batches are awaited to finish before we get here.
  TBD: Why is it important to wait for BUF_FLUSH_LRU to finish here? */
  buf_flush_await_no_flushing(nullptr, BUF_FLUSH_LRU);

  mutex_exit(&recv_sys->writer_mutex);

  uint32_t count = 0;

  while (recv_writer_is_active()) {
    ++count;

    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    if (count >= 600) {
      ib::info(ER_IB_MSG_738);
      count = 0;
    }
  }

  MetadataRecover *metadata{};

  if (!aborting) {
    std::swap(metadata, recv_sys->metadata_recover);
  }

  recv_sys_free();

  if (!aborting) {
    /* Validate a few system page types that were left uninitialized
    by older versions of MySQL. */
    verify_page_type({IBUF_SPACE_ID, FSP_IBUF_HEADER_PAGE_NO},
                     FIL_PAGE_TYPE_SYS);
    verify_page_type({TRX_SYS_SPACE, FSP_FIRST_RSEG_PAGE_NO},
                     FIL_PAGE_TYPE_SYS);
    verify_page_type({TRX_SYS_SPACE, TRX_SYS_PAGE_NO}, FIL_PAGE_TYPE_TRX_SYS);
    verify_page_type({TRX_SYS_SPACE, FSP_DICT_HDR_PAGE_NO}, FIL_PAGE_TYPE_SYS);
  }

  return metadata;
}
```

타입 확인은 페이지를 버퍼 풀로 읽어 헤더를 본다.

`storage` / `innobase` / `log` / `log0recv.cc` L3924-L3948 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/log/log0recv.cc#L3924-L3948))

```cpp
// log0recv.cc L3924-L3948
/** Check the page type, if there is a mismatch then throw
fatal error. It may so happen that data file before 5.7 GA version
may contain uninitialized bytes in the FIL_PAGE_TYPE field.
@param[in]  page_id         Page id to verify
@param[in]  type            Expected page type
*/
static void verify_page_type(page_id_t page_id, page_type_t type) {
  mtr_t mtr;
  mtr_start(&mtr);
  /* We should not write to redo log before checkpointing is enabled as it risks
  running out of space, and we don't expect to write anything in this mtr.
  It should be read only */
  mtr_set_log_mode(&mtr, MTR_LOG_NO_REDO);

  const auto *block =
      buf_page_get(page_id, univ_page_size, RW_S_LATCH, UT_LOCATION_HERE, &mtr);

  const auto page_type = fil_page_get_type(block->frame);
  if (page_type != type) {
    ib::fatal(UT_LOCATION_HERE, ER_IB_MSG_INVALID_PAGE_TYPE, unsigned{type},
              unsigned{page_type}, ulong{page_id.space()},
              ulong{page_id.page_no()});
  }
  mtr_commit(&mtr);
}
```

## 동작 흐름

```text
 L3955  mutex_enter(writer_mutex)                recv_writer 가 새 배치를 걸지 못하게
 L3958  MEB 복원이면 dblwr 모드를 되돌린다
 L3961  recv_recovery_on = false                 이제 읽기 완료가 redo 를 적용하지 않는다
 L3967  buf_flush_await_no_flushing(LRU)         진행 중인 LRU 배치를 기다린다
 L3969  writer_mutex 해제
 L3973  while recv_writer_is_active              100ms 씩, 60초마다 안내 로그
          recv_writer 는 recv_recovery_on 이 꺼진 것을 보고 스스로 끝난다 (L736)
 L3986  aborting 이 아니면 metadata_recover 를 꺼내 호출자에게
 L3990  recv_sys_free                            recv_sys_finish 로 복구 자원 해제 (L762)
 L3992  aborting 이 아니면 verify_page_type 네 번
          (IBUF_SPACE_ID, FSP_IBUF_HEADER_PAGE_NO)  FIL_PAGE_TYPE_SYS
          (TRX_SYS_SPACE, FSP_FIRST_RSEG_PAGE_NO)   FIL_PAGE_TYPE_SYS
          (TRX_SYS_SPACE, TRX_SYS_PAGE_NO)          FIL_PAGE_TYPE_TRX_SYS
          (TRX_SYS_SPACE, FSP_DICT_HDR_PAGE_NO)     FIL_PAGE_TYPE_SYS
          다르면 ib::fatal
```

```text
 redo 복구 단계에서 켜진 것과 꺼지는 곳

 recv_writer 스레드
   켜는 곳  [07] L3759
   끄는 곳  이 함수 L3961 에서 recovery_on 을 끄면 스레드가 보고 스스로 끝난다
 읽기 완료에서의 redo 적용 (buf_page_io_complete)
   켜는 곳  [02] L3777 recv_recovery_on = true
   끄는 곳  이 함수 L3961
 체크포인트
   log_start 뒤에도 막혀 있다가 [01] srv0start.cc L1883 m_allow_checkpoints 로 풀린다
```

## 결과가 쓰이는 곳

```text
 MetadataRecover * (dict_metadata)
      --> [01] 이 dict_boot 뒤 dict_metadata->store() 로 DD 버퍼 테이블에 저장한다
          (srv0start.cc L1873)
 recv_sys 해제
      --> 이후 recv_recovery_is_on() 은 false. buf_page_io_complete 는 ibuf 병합 쪽으로 간다
 abort 경로 (aborting = true)
      --> 누락 테이블스페이스로 기동을 중단할 때 [01] L1794 가 부른다
```

## 다루지 않는 것

`recv_sys_free` 가 해제하는 항목의 목록, MEB 백업 복원의 dblwr 모드, 동적 메타데이터(`MetadataRecover`)의 내용과 저장 형식은 이 함수의 곁가지라 요약만 했다.
