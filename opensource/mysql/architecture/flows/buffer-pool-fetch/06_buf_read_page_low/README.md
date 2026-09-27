# buf_read_page_low

상위: [버퍼 풀 페이지 획득](../README.md)

**페이지 한 장의 디스크 읽기를 거는 함수다.** 먼저 [07] 로 블록을 준비해 page hash 와 LRU 에 올리고, 그 frame 을 목적지로 `fil_io` 를 부른다. 동기 요청이면 이 스레드가 I/O 완료까지 기다렸다가 `buf_page_io_complete` 를 **직접** 부르고, 비동기면 I/O 핸들러 스레드가 나중에 부른다. 준비 단계에서 이미 버퍼 풀에 있다는 것이 밝혀지면 아무것도 읽지 않고 0을 돌려준다.

## 위치

`storage` / `innobase` / `buf` / `buf0rea.cc` L66-L151 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0rea.cc#L66-L151))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0rea.cc` L66-L151 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0rea.cc#L66-L151))

```cpp
// buf0rea.cc L66-L151
ulint buf_read_page_low(dberr_t *err, bool sync, ulint type, ulint mode,
                        const page_id_t &page_id, const page_size_t &page_size,
                        bool unzip) {
  buf_page_t *bpage;

  *err = DB_SUCCESS;

  if (page_id.space() == TRX_SYS_SPACE &&
      dblwr::v1::is_inside(page_id.page_no())) {
    ib::error(ER_IB_MSG_139)
        << "Trying to read legacy doublewrite buffer page " << page_id;

    return (0);
  }

  if (ibuf_bitmap_page(page_id, page_size) || trx_sys_hdr_page(page_id)) {
    /* Trx sys header is so low in the latching order that we play
    safe and do not leave the i/o-completion to an asynchronous
    i/o-thread. Ibuf bitmap pages must always be read with
    synchronous i/o, to make sure they do not get involved in
    thread deadlocks. */

    sync = true;
  }

  /* The following call will also check if the tablespace does not exist
  or is being dropped; if we succeed in initing the page in the buffer
  pool for read, then DISCARD cannot proceed until the read has
  completed */
  bpage = buf_page_init_for_read(mode, page_id, page_size, unzip);

  ut_a(bpage == nullptr || bpage->get_space()->id == page_id.space());

  if (bpage == nullptr) {
    return (0);
  }

  DBUG_PRINT("ib_buf",
             ("read page %u:%u size=%u unzip=%u,%s", (unsigned)page_id.space(),
              (unsigned)page_id.page_no(), (unsigned)page_size.physical(),
              (unsigned)unzip, sync ? "sync" : "async"));

  ut_ad(buf_page_in_file(bpage));
  ut_ad(!mutex_own(&buf_pool_from_bpage(bpage)->LRU_list_mutex));

  if (sync) {
    thd_wait_begin(nullptr, THD_WAIT_DISKIO);
  }

  void *dst;

  if (page_size.is_compressed()) {
    dst = bpage->zip.data;
  } else {
    ut_a(buf_page_get_state(bpage) == BUF_BLOCK_FILE_PAGE);

    dst = ((buf_block_t *)bpage)->frame;
  }

  IORequest request(type | IORequest::READ);

  *err = fil_io(request, sync, page_id, page_size, 0, page_size.physical(), dst,
                bpage);

  if (sync) {
    thd_wait_end(nullptr);
  }

  if (*err != DB_SUCCESS) {
    if (IORequest::ignore_missing(type) || *err == DB_TABLESPACE_DELETED) {
      buf_read_page_handle_error(bpage);
      return (0);
    }

    ut_error;
  }

  if (sync) {
    /* The i/o is already completed when we arrive from fil_read */
    if (!buf_page_io_complete(bpage, false)) {
      return (0);
    }
  }

  return (1);
}
```

## 동작 흐름

```text
 L73   시스템 테이블스페이스의 구식 doublewrite 영역이면 에러, 0
 L81   ibuf bitmap 페이지나 trx sys 헤더면 sync = true 로 강제
         (주석: 래치 순서가 낮아 비동기 완료에 맡기지 않는다)
 L95   bpage = [07] buf_page_init_for_read(mode, page_id, page_size, unzip)
 L99     nullptr -> 0   이미 있거나, 공간이 없거나 드롭 중
         이 순간부터 블록은 page hash 에 있고 io_fix = BUF_IO_READ

 L111  sync 면 thd_wait_begin(THD_WAIT_DISKIO)
 L117  목적지: 압축이면 bpage->zip.data, 아니면 block->frame
 L125  IORequest(type | READ)
 L127  fil_io(request, sync, page_id, page_size, 0, physical, dst, bpage)
 L134  실패
         IGNORE_MISSING 이거나 DB_TABLESPACE_DELETED -> buf_read_page_handle_error, 0
         그 밖 -> ut_error
 L143  sync 면
 L145    buf_page_io_complete(bpage, false)   이 스레드가 직접 완료 처리
           false (손상 등) -> 0
 L150  return 1
```

완료 처리는 동기든 비동기든 같은 함수를 지난다. 그 안에서 페이지 번호와 체크섬을 확인하고, 복구 중이면 redo 를 적용한 뒤 io-fix 와 X 래치를 푼다.

```text
 buf_page_io_complete 의 읽기 쪽 (buf0buf.cc L5795)

 L5840  frame 의 FIL_PAGE_OFFSET, FIL_PAGE_SPACE_ID 를 읽는다
 L5863  블록의 page_id 와 다르면 sync_read_page_verify_pageid 로 한 번 더 읽는다
 L5896  BlockReporter(...).is_corrupted()       체크섬
 L5905  복구 중이고 손상인데 recv_page_is_brand_new 면 0 으로 채우고 통과
 L5949  손상이면 (force_recovery 가 IGNORE_CORRUPT 미만일 때) handle_error, false
 L5957  recv_recovery_is_on() 이면 recv_recover_page(true, block)   --> [크래시 복구]
        아니면 조건이 맞는 leaf 인덱스 페이지에 ibuf_merge_or_delete_for_page
 L6028  io_fix = BUF_IO_NONE
 L6035  X 래치 해제 (pass = BUF_IO_READ)        기다리던 스레드가 깨어난다
 L6041  n_pend_reads--, n_pages_read++
```

```text
 누가 완료를 부르는가

 buf_read_page ([05])               sync   호출자 스레드가 L145 에서
 ibuf bitmap, trx sys header page   sync   호출자 스레드 (L81 에서 강제)
 read-ahead random / linear         async  I/O 핸들러 스레드
 buf_read_recv_pages (recovery)     async  I/O 핸들러 스레드. 그 안에서 redo 적용 (L697)
```

## 결과가 쓰이는 곳

```text
 반환값 1 / 0
      --> [05] 의 재시도 판정, Innodb_buffer_pool_reads
 읽힌 frame
      --> page hash 의 블록 안에 있다. [04] 의 다음 lookup 이 찾는다
 buf_page_io_complete 의 recv_recover_page
      --> [크래시 복구] 의 페이지별 redo 적용이 이 자리에서 일어난다
```

## 다루지 않는 것

`fil_io` 아래의 파일 노드 선택과 `os_aio`, 비동기 I/O 핸들러 스레드의 루프, `sync_read_page_verify_pageid` 가 막으려는 AIO 이상 동작, 페이지 압축(`Compression::is_compressed_page`)과 암호화 해제, change buffer 병합(`ibuf_merge_or_delete_for_page`)은 이 함수의 곁가지라 요약만 했다. 복구 중 적용은 [크래시 복구](../../crash-recovery/README.md)에 있다.
