# Buf_fetch::lookup

상위: [버퍼 풀 페이지 획득](../README.md)

**page hash 에서 블록을 찾는 함수다.** 찾으면 hash 셀의 S 락을 **쥔 채로** 돌려주고, 못 찾으면 락을 풀고 `nullptr` 을 돌려준다. 락을 쥔 채 돌려주는 것이 요점이다. 호출자 [04] 가 그 락 안에서 buf-fix 를 걸어야, 락을 놓은 뒤에도 블록이 다른 페이지로 바뀌지 않는다. 호출자가 넘긴 guess 블록은 hash 를 찾기 전에 먼저 검증해 본다.

## 위치

`storage` / `innobase` / `buf` / `buf0buf.cc` L3826-L3875 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3826-L3875))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0buf.cc` L3825-L3875 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3825-L3875))

```cpp
// buf0buf.cc L3825-L3875
template <typename T>
buf_block_t *Buf_fetch<T>::lookup() {
  m_hash_lock = buf_page_hash_lock_get(m_buf_pool, m_page_id);

  auto block = m_guess;

  rw_lock_s_lock(m_hash_lock, UT_LOCATION_HERE);

  /* If not own LRU_list_mutex, page_hash can be changed. */
  m_hash_lock =
      buf_page_hash_lock_s_confirm(m_hash_lock, m_buf_pool, m_page_id);

  if (block != nullptr) {
    /* If the m_guess is a compressed page descriptor that has been allocated
    by buf_page_alloc_descriptor(), it may have been freed by buf_relocate().
    Also, the buffer pool could get resized and m_guess's chunk could get freed,
    so we need to check the `block` pointer is still within one of the chunks
    before dereferencing it to verify it still contains the same m_page_id */

    if (!buf_is_block_in_instance(m_buf_pool, block) ||
        m_page_id != block->page.id ||
        buf_block_get_state(block) != BUF_BLOCK_FILE_PAGE) {
      /* Our m_guess was bogus or things have changed since. */
      block = m_guess = nullptr;

    } else {
      ut_ad(!block->page.in_zip_hash);
    }
  }

  if (block == nullptr) {
    block = reinterpret_cast<buf_block_t *>(
        buf_page_hash_get_low(m_buf_pool, m_page_id));
  }

  if (block == nullptr) {
    rw_lock_s_unlock(m_hash_lock);

    return (nullptr);
  }

  const auto bpage = &block->page;

  if (buf_pool_watch_is_sentinel(m_buf_pool, bpage)) {
    rw_lock_s_unlock(m_hash_lock);

    return (nullptr);
  }

  return (block);
}
```

버퍼 풀 인스턴스는 page_no 의 하위 6비트를 버린 id 의 해시로 고른다. 64 페이지 묶음이 같은 인스턴스에 모인다.

`storage` / `innobase` / `include` / `buf0buf.ic` L820-L831 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.ic#L820-L831))

```cpp
// buf0buf.ic L820-L831
/** Returns the buffer pool instance given a page id.
@param[in]      page_id page id
@return buffer pool */
static inline buf_pool_t *buf_pool_get(const page_id_t &page_id) {
  /* 2log of BUF_READ_AHEAD_AREA (64) */
  page_no_t ignored_page_no = page_id.page_no() >> 6;

  page_id_t id(page_id.space(), ignored_page_no);

  ulint i = id.hash() % srv_buf_pool_instances;

  return (&buf_pool_ptr[i]);
```

page hash 조회 자체는 체인을 따라가며 `page_id` 가 같은 것을 찾는다.

`storage` / `innobase` / `include` / `buf0buf.ic` L849-L873 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.ic#L849-L873))

```cpp
// buf0buf.ic L849-L873
static inline buf_page_t *buf_page_hash_get_low(buf_pool_t *buf_pool,
                                                const page_id_t &page_id) {
  buf_page_t *bpage;

#ifdef UNIV_DEBUG
  rw_lock_t *hash_lock;

  hash_lock = hash_get_lock(buf_pool->page_hash, page_id.hash());
  ut_ad(rw_lock_own(hash_lock, RW_LOCK_X) || rw_lock_own(hash_lock, RW_LOCK_S));
#endif /* UNIV_DEBUG */

  /* Look for the page in the hash table */

  HASH_SEARCH(hash, buf_pool->page_hash, page_id.hash(), buf_page_t *, bpage,
              ut_ad(bpage->in_page_hash && !bpage->in_zip_hash &&
                    buf_page_in_file(bpage)),
              page_id == bpage->id);
  if (bpage) {
    ut_a(buf_page_in_file(bpage));
    ut_ad(bpage->in_page_hash);
    ut_ad(!bpage->in_zip_hash);
    ut_ad(buf_pool_from_bpage(bpage) == buf_pool);
  }

  return (bpage);
```

## 동작 흐름

```text
 L3827  m_hash_lock = buf_page_hash_lock_get(m_buf_pool, m_page_id)
 L3829  block = m_guess
 L3831  rw_lock_s_lock(m_hash_lock)
 L3834  buf_page_hash_lock_s_confirm           락을 잡는 사이 hash 표가 바뀌었으면 새 락으로

 L3837  guess 가 있으면 검증
 L3844    인스턴스의 chunk 안에 있는 포인터인가   (크기 조정으로 chunk 가 사라졌을 수 있다)
 L3845    block->page.id == m_page_id 인가       (그 사이 다른 페이지가 들어왔을 수 있다)
 L3846    state == BUF_BLOCK_FILE_PAGE 인가
          하나라도 아니면 L3848 guess 버림

 L3855  guess 가 없으면 buf_page_hash_get_low   HASH_SEARCH (buf0buf.ic L862)
 L3860  못 찾음 -> S 락 해제, nullptr
 L3868  찾았는데 watch sentinel 이면 -> S 락 해제, nullptr
          (change buffer 가 "읽히면 알려 달라"고 걸어 둔 가짜 블록)
 L3874  찾음 -> S 락을 쥔 채로 반환
```

```text
 page hash 의 모양 (인스턴스마다 하나)

 buf_pool_get(page_id)                         buf0buf.ic L823
   id(space, page_no >> 6).hash() % srv_buf_pool_instances

 buf_pool->page_hash
   cell[0]  -> bpage -> bpage -> ...           체인은 buf_page_t::hash 로 잇는다
   cell[1]  -> bpage
   ...
   셀 묶음마다 rw_lock 하나                    buf_page_hash_lock_get (buf0buf.h L2616)

 lookup 은 S, 삽입과 삭제는 X
   삽입   [07] buf_page_init_for_read  (X, L4929)
   삭제   buf_LRU_block_remove_hashed   (교체할 때, X)
```

## 결과가 쓰이는 곳

```text
 block + 쥔 S 락
      --> [04] 가 buf_block_fix 뒤 rw_lock_s_unlock (L3737, L3740)
      --> stale 이면 buf_page_free_stale 이 락을 넘겨받아 푼다 (L3726)
 nullptr
      --> [04] 가 [05] read_page 로 읽고 다시 lookup
```

## 다루지 않는 것

`buf_page_hash_lock_s_confirm` 이 버퍼 풀 크기 조정 중 hash 표 교체를 따라가는 방식, watch sentinel(`buf_pool->watch[]`)을 쓰는 change buffer 경로, 압축 페이지의 `zip_hash` 는 이 함수의 곁가지라 요약만 했다.
