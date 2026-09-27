# buf_page_init_for_read

상위: [버퍼 풀 페이지 획득](../README.md)

**읽기를 걸기 전에 블록을 버퍼 풀에 "먼저" 올리는 함수다.** 빈 블록을 얻고, LRU 뮤텍스와 hash 셀 X 락 안에서 **그 사이 누가 이미 올리지 않았는지 다시 확인한 뒤**, page hash 에 넣고 io_fix 를 READ 로 두고 LRU 의 old 구간에 넣는다. 그리고 frame 에 X 래치를 건다. 이 순서 덕분에 같은 페이지를 동시에 찾는 두 번째 스레드는 두 번째 읽기를 걸지 않고, 이미 등록된 블록을 찾아 X 래치가 풀리기를 기다린다.

## 위치

`storage` / `innobase` / `buf` / `buf0buf.cc` L4880-L5084 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4880-L5084))

## 실제 코드

앞부분이다. 블록을 얻고 락을 잡은 뒤 이미 있는지 다시 본다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L4880-L4959 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4880-L4959))

```cpp
// buf0buf.cc L4880-L4959
buf_page_t *buf_page_init_for_read(ulint mode, const page_id_t &page_id,
                                   const page_size_t &page_size, bool unzip) {
  buf_block_t *block;
  rw_lock_t *hash_lock;
  mtr_t mtr;
  void *data = nullptr;
  buf_pool_t *buf_pool = buf_pool_get(page_id);

  ut_ad(buf_pool);

  if (mode == BUF_READ_IBUF_PAGES_ONLY) {
    /* It is a read-ahead within an ibuf routine */

    ut_ad(!ibuf_bitmap_page(page_id, page_size));

    ibuf_mtr_start(&mtr);

    if (!recv_recovery_is_on() &&
        !ibuf_page(page_id, page_size, UT_LOCATION_HERE, &mtr)) {
      ibuf_mtr_commit(&mtr);

      return (nullptr);
    }
  } else {
    ut_ad(mode == BUF_READ_ANY_PAGE);
  }

  if (page_size.is_compressed() && !unzip && !recv_recovery_is_on()) {
    block = nullptr;
  } else {
    block = buf_LRU_get_free_block(buf_pool);
    ut_ad(block);
    ut_ad(!block->page.someone_has_io_responsibility());
    ut_ad(buf_pool_from_block(block) == buf_pool);
  }

  buf_page_t *bpage = nullptr;
  if (block == nullptr) {
    bpage = buf_page_alloc_descriptor();
  }

  if ((block != nullptr && page_size.is_compressed()) || block == nullptr) {
    data = buf_buddy_alloc(buf_pool, page_size.physical());
  }

  mutex_enter(&buf_pool->LRU_list_mutex);

  hash_lock = buf_page_hash_lock_get(buf_pool, page_id);

  rw_lock_x_lock(hash_lock, UT_LOCATION_HERE);

  buf_page_t *watch_page;

  watch_page = buf_page_hash_get_low(buf_pool, page_id);

  if (watch_page != nullptr &&
      !buf_pool_watch_is_sentinel(buf_pool, watch_page)) {
    /* The page is already in the buffer pool. */
    watch_page = nullptr;

    mutex_exit(&buf_pool->LRU_list_mutex);

    rw_lock_x_unlock(hash_lock);

    if (bpage != nullptr) {
      buf_page_free_descriptor(bpage);
    }

    if (data != nullptr) {
      buf_buddy_free(buf_pool, data, page_size.physical());
    }

    if (block != nullptr) {
      buf_LRU_block_free_non_file_page(block);
    }

    bpage = nullptr;

    goto func_exit;
  }
```

압축되지 않은 페이지(보통의 경우)의 등록이다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L4961-L5084 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4961-L5084))

```cpp
// buf0buf.cc L4961-L5084
  if (block != nullptr) {
    ut_ad(!bpage);
    bpage = &block->page;

    ut_ad(buf_pool_from_bpage(bpage) == buf_pool);

    buf_page_mutex_enter(block);

    buf_page_init(buf_pool, page_id, page_size, block);

    /* Note: We are using the hash_lock for protection. This is
    safe because no other thread can lookup the block from the
    page hashtable yet. */

    block->mark_for_read_io();
    buf_page_set_io_fix(bpage, BUF_IO_READ);

    /* The block must be put to the LRU list, to the old blocks */
    buf_LRU_add_block(bpage, true /* to old blocks */);

    if (page_size.is_compressed()) {
      block->page.zip.data = (page_zip_t *)data;

      /* To maintain the invariant
      block->in_unzip_LRU_list
      == buf_page_belongs_to_unzip_LRU(&block->page)
      we have to add this block to unzip_LRU
      after block->page.zip.data is set. */
      ut_ad(buf_page_belongs_to_unzip_LRU(&block->page));
      buf_unzip_LRU_add_block(block, true);
    }

    mutex_exit(&buf_pool->LRU_list_mutex);

    /* We set a pass-type x-lock on the frame because then
    the same thread which called for the read operation
    (and is running now at this point of code) can wait
    for the read to complete by waiting for the x-lock on
    the frame; if the x-lock were recursive, the same
    thread would illegally get the x-lock before the page
    read is completed.  The x-lock is cleared by the
    io-handler thread. */

    rw_lock_x_lock_gen(&block->lock, BUF_IO_READ, UT_LOCATION_HERE);

    rw_lock_x_unlock(hash_lock);

    buf_page_mutex_exit(block);
  } else {
  // ... (L5010-L5069 생략: 압축 전용 페이지를 descriptor 로만 올리는 else 가지)
  }

  buf_pool->n_pend_reads.fetch_add(1);
func_exit:

  if (mode == BUF_READ_IBUF_PAGES_ONLY) {
    ibuf_mtr_commit(&mtr);
  }

  ut_ad(!rw_lock_own(hash_lock, RW_LOCK_X));
  ut_ad(!rw_lock_own(hash_lock, RW_LOCK_S));
  ut_ad(!bpage || buf_page_in_file(bpage));

  return (bpage);
}
```

page hash 삽입은 `buf_page_init` 안에서 한다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L4866-L4878 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4866-L4878))

```cpp
// buf0buf.cc L4866-L4878
  ut_ad(!block->page.in_page_hash);
  ut_d(block->page.in_page_hash = true);

  ut_a(block->page.id == page_id);
  block->page.size.copy_from(page_size);

  HASH_INSERT(buf_page_t, hash, buf_pool->page_hash, page_id.hash(),
              &block->page);

  if (page_size.is_compressed()) {
    page_zip_set_size(&block->page.zip, page_size.physical());
  }
}
```

## 동작 흐름

```text
 L4890  BUF_READ_IBUF_PAGES_ONLY 면 ibuf 페이지인지 확인 (아니면 nullptr)
 L4907  압축 페이지이고 unzip 이 아니며 복구 중이 아니면 block 없이 descriptor 만
 L4910  아니면 [08] buf_LRU_get_free_block      락을 잡기 전에 얻는다 (오래 걸릴 수 있다)
 L4921  압축이면 buf_buddy_alloc 으로 zip 데이터 공간

 L4925  mutex_enter(LRU_list_mutex)
 L4929  rw_lock_x_lock(hash_lock)
 L4933  buf_page_hash_get_low 로 다시 확인
 L4935    이미 있고 watch sentinel 이 아니면     누가 먼저 올렸다
 L4940-L4954  락을 풀고 얻은 블록과 메모리를 되돌린다 (buf_LRU_block_free_non_file_page)
 L4958    goto func_exit, nullptr

 L4969  buf_page_init                          buf_page_init_low (L4834), HASH_INSERT (L4872)
 L4975  mark_for_read_io
 L4976  io_fix = BUF_IO_READ
 L4979  [10] buf_LRU_add_block(bpage, true)    old 구간 머리에
 L4993  LRU_list_mutex 해제
 L5004  rw_lock_x_lock_gen(&block->lock, BUF_IO_READ)   pass 값이 있는 X 래치
 L5006  hash X 락 해제                         이제 남이 lookup 으로 찾을 수 있다
 L5072  n_pend_reads++
```

X 래치는 hash 락을 풀기 **전에** 건다. hash X 락을 쥐고 있는 동안은 다른 스레드가 이 블록을 lookup 으로 찾을 수 없으므로, io_fix 설정도 이 락의 보호 아래에서 한다는 것이 소스 주석이다(L4971-L4973). pass 값을 쓰는 이유는 소스 주석에 있다(L4995-L5002). 읽기를 건 이 스레드도 같은 X 래치를 기다려 완료를 알아야 하는데, 재귀 X 래치면 이 스레드가 완료 전에 래치를 얻어 버린다. 그래서 풀기는 I/O 를 마친 쪽(io 핸들러 스레드 또는 동기 경로)이 pass 값으로 한다.

```text
 등록 직후 블록의 상태

 field                       value
 page.id                     (space, page_no)
 page.state                  BUF_BLOCK_FILE_PAGE
 page.io_fix                 BUF_IO_READ
 page.old                    true (LRU_old 가 있을 때, buf0lru.cc L1692)
 page.access_time            0 (buf_page_init_low L4794)
 page.buf_fix_count          0 (L4792)
 block->lock                 X (pass = BUF_IO_READ)
 LRU position                LRU_old 바로 뒤
 page_hash                   등록됨
 frame                       아직 쓰레기. fil_io 가 채운다
```

## 결과가 쓰이는 곳

```text
 bpage
      --> [06] 이 frame 을 fil_io 의 목적지로 쓴다
 page_hash 등록
      --> 동시에 같은 페이지를 찾는 스레드의 [03] lookup 이 적중한다
          그 스레드는 [02] buf_wait_for_read 에서 X 래치 해제를 기다린다
 LRU old 구간
      --> 첫 get 뒤에도 innodb_old_blocks_time 이 지나야 young 으로 간다 ([09])
```

## 다루지 않는 것

압축 전용 페이지를 `buf_page_alloc_descriptor` 로 올리는 else 가지와 zip_mutex, watch sentinel 의 `buf_fix_count` 를 옮겨 받는 부분(L5042-L5054), `buf_buddy_alloc`, `buf_page_init` 이 초기화하는 나머지 필드는 이 함수의 곁가지라 요약만 했다.
