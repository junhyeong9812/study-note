# Buf_fetch::single_page

상위: [버퍼 풀 페이지 획득](../README.md)

**블록을 "찾은 뒤"에 해야 할 일을 한 곳에 모은 함수다.** 앞 절반의 `for (;;)` 는 buf-fix 가 걸린 쓸 만한 블록을 얻을 때까지 `get()` 과 `check_state()` 를 되풀이하고, 뒤 절반은 첫 접근 시각을 적고, LRU 에서 올릴지 정하고, 남이 읽는 중이면 기다리고, 래치를 걸어 mtr 에 올리고, 첫 접근이면 linear read-ahead 를 건다. 순서가 볼거리다. **LRU 조정은 래치 전에, 읽기 대기는 래치 바로 전에** 한다.

## 위치

`storage` / `innobase` / `buf` / `buf0buf.cc` L4299-L4447 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4299-L4447))

## 실제 코드

앞 절반, 쓸 만한 블록을 얻는 루프다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L4298-L4370 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4298-L4370))

```cpp
// buf0buf.cc L4298-L4370
template <typename T>
buf_block_t *Buf_fetch<T>::single_page() {
  buf_block_t *block;

  Counter::inc(m_buf_pool->stat.m_n_page_gets, m_page_id.page_no());

  for (;;) {
    if (static_cast<T *>(this)->get(block) == DB_NOT_FOUND) {
      return (nullptr);
    }
    ut_a(!block->page.was_stale());

    if (is_optimistic()) {
      const auto bpage = &block->page;
      auto block_mutex = buf_page_get_mutex(bpage);

      mutex_enter(block_mutex);

      const auto state = buf_page_get_io_fix(bpage);

      mutex_exit(block_mutex);

      if (state == BUF_IO_READ) {
        /* The page is being read to buffer pool, but we cannot wait around for
        the read to complete. */

        buf_block_unfix(block);

        return (nullptr);
      }
    }

    switch (check_state(block)) {
      case DB_NOT_FOUND:
        return (nullptr);
      case DB_FAIL:
        /* Restart the outer for(;;) loop. */
        continue;
      case DB_SUCCESS:
        break;
      default:
        ut_error;
        break;
    }

    ut_ad(block->page.buf_fix_count > 0);

    ut_ad(!rw_lock_own(m_hash_lock, RW_LOCK_X));

    ut_ad(!rw_lock_own(m_hash_lock, RW_LOCK_S));

    ut_ad(buf_block_get_state(block) == BUF_BLOCK_FILE_PAGE);
    // ... (L4350-L4365 생략: UNIV_DEBUG 의 debug_check 재시도 분기)
    /* Break out of the outer for (;;) loop. */
    break;
  }

  ut_ad(block->page.buf_fix_count > 0);
```

뒤 절반, 블록을 호출자에게 넘기기 전의 처리다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L4386-L4447 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4386-L4447))

```cpp
// buf0buf.cc L4386-L4447
  ut_ad(is_possibly_freed() || !block->page.file_page_was_freed);

  /* Check if this is the first access to the page */
  const auto access_time = buf_page_is_accessed(&block->page);

  /* This is a heuristic and we don't care about ordering issues. */
  if (access_time == std::chrono::steady_clock::time_point{}) {
    buf_page_mutex_enter(block);

    buf_page_set_accessed(&block->page);

    buf_page_mutex_exit(block);
  }

  /* Don't move the page to the head of the LRU list so that the
  page can be discarded quickly if it is not accessed again. */
  if (m_mode != Page_fetch::PEEK_IF_IN_POOL && m_mode != Page_fetch::SCAN) {
    buf_page_make_young_if_needed(&block->page);
  }

// ... (L4406-L4410 생략: 디버그 검증과 단언)

  /* We have to wait here because the IO_READ state was set under the protection
  of the hash_lock and not the block->mutex and block->lock. */
  buf_wait_for_read(block);

  /* Mark block as dirty if requested by caller. If not requested (false)
  then we avoid updating the dirty state of the block and retain the
  original one. This is reason why ?
  Same block can be shared/pinned by 2 different mtrs. If first mtr
  set the dirty state to true and second mtr mark it as false the last
  updated dirty state is retained. Which means we can loose flushing of
  a modified block. */
  if (m_dirty_with_no_latch) {
    block->made_dirty_with_no_latch = m_dirty_with_no_latch;
  }

  mtr_add_page(block);

  if (m_mode != Page_fetch::PEEK_IF_IN_POOL &&
      m_mode != Page_fetch::POSSIBLY_FREED_NO_READ_AHEAD &&
      access_time == std::chrono::steady_clock::time_point{}) {
    /* In the case of a first access, try to apply linear read-ahead */

    buf_read_ahead_linear(m_page_id, m_page_size, ibuf_inside(m_mtr));
  }

  // ... (L4437-L4445 생략: 디버그 검증과 단언)
  return (block);
}
```

`buf_wait_for_read` 는 읽기를 맡은 스레드가 들고 있는 X 래치를 이용해 기다린다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L3594-L3609 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3594-L3609))

```cpp
// buf0buf.cc L3594-L3609
static void buf_wait_for_read(buf_block_t *block) {
  /* Note:
  This unlocked read of IO fix is safe as we have the block buf-fixed. The page
  can only transition away from the IO_READ state, and once this is done, it
  will not be IO_READ again as long as we have it buf-fixed.

  The repeated reads of io_fix will not be optimized out because it's an atomic
  variable.*/
  while (block->page.was_io_fix_read()) {
    /* Page is X-latched on block->lock until the read is completed.
    Let's just wait for S-lock on block->lock, it will be granted as soon as the
    read completes. */
    rw_lock_s_lock(&block->lock, UT_LOCATION_HERE);
    rw_lock_s_unlock(&block->lock);
  }
}
```

`mtr_add_page` 가 요청한 래치를 걸고 memo 에 올린다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L4152-L4184 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L4152-L4184))

```cpp
// buf0buf.cc L4152-L4184
template <typename T>
void Buf_fetch<T>::mtr_add_page(buf_block_t *block) {
  mtr_memo_type_t fix_type;

  ut::Location loc{m_file, m_line};

  switch (m_rw_latch) {
    case RW_NO_LATCH:

      fix_type = MTR_MEMO_BUF_FIX;
      break;

    case RW_S_LATCH:
      rw_lock_s_lock_gen(&block->lock, 0, loc);
      fix_type = MTR_MEMO_PAGE_S_FIX;
      break;

    case RW_SX_LATCH:
      rw_lock_sx_lock_gen(&block->lock, 0, loc);

      fix_type = MTR_MEMO_PAGE_SX_FIX;
      break;

    default:
      ut_ad(m_rw_latch == RW_X_LATCH);
      rw_lock_x_lock_gen(&block->lock, 0, loc);

      fix_type = MTR_MEMO_PAGE_X_FIX;
      break;
  }

  mtr_memo_push(m_mtr, block, fix_type);
}
```

## 동작 흐름

```text
 L4302  m_n_page_gets++                         Innodb_buffer_pool_read_requests 의 재료

 L4304  for (;;)
 L4305    get(block) == DB_NOT_FOUND -> return nullptr       ([04] 또는 Buf_fetch_other::get)
          여기서 block 은 buf-fix 가 걸려 있고 hash 락은 풀려 있다
 L4310    is_optimistic() 이고 io_fix == BUF_IO_READ
 L4324      buf_block_unfix, return nullptr     기다리지 않는다
 L4330    check_state(block)
            FILE_PAGE              -> DB_SUCCESS
                                      (임시 테이블스페이스이고 io-fix 중이면 DB_FAIL, L4083)
            ZIP_PAGE / ZIP_DIRTY   -> zip_page_handler: 새 블록에 옮기고 풀어서 DB_SUCCESS
                                      다른 스레드가 fix 중이거나 io-fix 중이면 DB_FAIL
                                      PEEK_IF_IN_POOL 이면 DB_NOT_FOUND (L3911)
            그 밖의 상태           -> ut_error
 L4335      DB_FAIL -> continue (처음부터 다시 get)
 L4367    break

 L4389  access_time = buf_page_is_accessed      0 이면 처음 접근
 L4392    처음이면 block mutex 안에서 buf_page_set_accessed (지금 시각 기록)
 L4402  mode 가 PEEK_IF_IN_POOL, SCAN 이 아니면
 L4403    [09] buf_page_make_young_if_needed
 L4414  buf_wait_for_read                       IO_READ 가 풀릴 때까지 S 래치를 잡았다 놓기
 L4423  m_dirty_with_no_latch 면 block 에 표시
 L4427  mtr_add_page                            래치 + mtr memo push
 L4429  처음 접근이고 PEEK, POSSIBLY_FREED_NO_READ_AHEAD 가 아니면
 L4434    buf_read_ahead_linear
 L4446  return block
```

처음 접근 시각을 적는 자리와 make_young 을 부르는 자리가 같은 함수 안에 붙어 있다. 그래서 **디스크에서 막 읽은 페이지는 첫 get 에서 시각만 적히고 old 구간에 남는다.** 두 번째 get 부터 [09] 가 그 시각을 보고 올릴지 정한다.

```text
 한 페이지의 LRU 수명 (innodb_old_blocks_time = 1000ms, 축출이 이미 시작된 버퍼 풀)

 t=0     미적중, [07] 이 old 머리에 넣는다
           -> old=true, access_time=0
 t=0     같은 single_page 안 L4395
           -> access_time=t0
         L4403 make_young 판정: now - t0 < 1000ms
           -> 올리지 않음, n_pages_not_made_young++
 t=0.3s  다시 get
           -> 여전히 1000ms 미만, old 에 머문다
 t=1.5s  다시 get
           -> 1000ms 이상, buf_page_make_young 으로 young 머리에, n_pages_made_young++
 이후    young 구간에서는 buf_page_peek_if_young 이 거짓일 때만 다시 머리로

 한 번 훑고 지나가는 스캔은 1초 안에 같은 페이지를 여러 번 읽고 끝나므로
 old 구간을 벗어나지 못하고 꼬리에서 먼저 교체된다
```

읽기 대기가 성립하는 이유는 읽기를 맡은 쪽이 frame 에 **X 래치를 건 채로** I/O 를 걸기 때문이다.

```text
 같은 페이지를 두 스레드가 거의 동시에 찾을 때 (A 가 먼저 미적중, 시간 순)

 A  [07] page hash 에 등록, io_fix=READ
 A       X 래치 (pass=BUF_IO_READ)  L5004
 A  fil_io 시작
 B  [03] lookup 적중 (이미 hash 에 있다)
 B  [04] buf_block_fix, hash S 락 해제
 B  L4414 buf_wait_for_read
 B    was_io_fix_read() 참
 B    rw_lock_s_lock(&block->lock)  -- 막힌다
 A  I/O 끝, buf_page_io_complete
 A    io_fix=NONE, X 래치 해제 (L6028, L6035)
 B    S 래치 획득 -> 곧바로 해제
 B    was_io_fix_read() 거짓, 대기 끝
 B  L4427 mtr_add_page 로 요청한 래치를 건다
 A  자기 get 루프에서 다시 lookup 해 같은 블록을 얻는다
```

## 결과가 쓰이는 곳

```text
 buf_block_t (buf-fix + 래치 + mtr memo)
      --> [01] 을 거쳐 호출자에게
      --> mtr_t::commit 이 memo 를 거꾸로 돌며 래치를 풀고 buf-fix 를 내린다

 access_time
      --> [09] 의 innodb_old_blocks_time 판정
      --> LRU 스캔이 "한 번도 접근되지 않고 쫓겨난" read-ahead 페이지를 센다
          (n_ra_pages_evicted, buf0lru.cc L1134)
```

## 다루지 않는 것

`zip_page_handler` 의 압축 해제와 relocate, `debug_check` 가 change buffer 디버그 옵션에서 페이지를 일부러 쫓아내는 경로, `buf_read_ahead_linear` 의 경계 판정, `made_dirty_with_no_latch` 가 flush list 등록에 미치는 영향, `mtr_memo_push` 이후 memo 의 자료구조([mini-transaction과 redo 기록](../../mtr-redo/README.md))는 이 함수의 곁가지라 요약만 했다.
