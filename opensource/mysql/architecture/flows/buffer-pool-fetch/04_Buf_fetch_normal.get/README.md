# Buf_fetch_normal::get

상위: [버퍼 풀 페이지 획득](../README.md)

**NORMAL 모드 전용의 "찾을 때까지 되풀이" 루프다.** 적중하면 hash 락 안에서 buf-fix 를 걸고 끝, 미적중이면 [05] 로 읽고 **처음부터 다시 찾는다.** 읽은 결과를 직접 받지 않고 다시 찾는 것이 볼거리다. 읽기 함수는 블록을 page hash 에 올려 두기만 하고, 그 블록을 가져오는 일은 언제나 lookup 이 한다. 소스 주석대로 "이 경로는 가능한 한 단순하게" 둔 판이고, 모드별 곁가지는 `Buf_fetch_other::get` 에 몰려 있다.

## 위치

`storage` / `innobase` / `buf` / `buf0buf.cc` L3713-L3749 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3713-L3749))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0buf.cc` L3713-L3749 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3713-L3749))

```cpp
// buf0buf.cc L3713-L3749
dberr_t Buf_fetch_normal::get(buf_block_t *&block) noexcept {
  /* Keep this path as simple as possible. */
  for (;;) {
    /* Lookup the page in the page hash. If it doesn't exist in the
    buffer pool then try and read it in from disk. */

    ut_ad(
        !rw_lock_own(buf_page_hash_lock_get(m_buf_pool, m_page_id), RW_LOCK_S));

    block = lookup();

    if (block != nullptr) {
      if (block->page.was_stale()) {
        if (!buf_page_free_stale(m_buf_pool, &block->page, m_hash_lock)) {
          /* The page is during IO and can't be released. We wait some to not go
           into loop that would consume CPU. This is not something that will be
           hit frequently. */
          std::this_thread::sleep_for(std::chrono::microseconds(100));
        }
        /* The hash lock was released, we should try again lookup for the page
         until it's gone - it should disappear eventually when the IO ends. */
        continue;
      }

      buf_block_fix(block);

      /* Now safe to release page_hash S lock. */
      rw_lock_s_unlock(m_hash_lock);
      break;
    }

    /* Page not in buf_pool: needs to be read from file */
    read_page();
  }

  return DB_SUCCESS;
}
```

비교를 위해 그 밖의 모드가 타는 쪽이다. 같은 뼈대에 임시 공간, watch, optimistic 처리가 붙는다.

`storage` / `innobase` / `buf` / `buf0buf.cc` L3764-L3823 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3764-L3823))

```cpp
// buf0buf.cc L3764-L3823
dberr_t Buf_fetch_other::get(buf_block_t *&block) noexcept {
  for (;;) {
    /* Lookup the page in the page hash. If it doesn't exist in the
    buffer pool then try and read it in from disk. */

    ut_ad(
        !rw_lock_own(buf_page_hash_lock_get(m_buf_pool, m_page_id), RW_LOCK_S));

    block = lookup();

    if (block != nullptr) {
      /* Here we have MDL latches making the stale status to not change. */
      if (block->page.was_stale()) {
        if (!buf_page_free_stale(m_buf_pool, &block->page, m_hash_lock)) {
          /* The page is during IO and can't be released. We wait some to not go
          into loop that would consume CPU. This is not something that will be
          hit frequently. */
          std::this_thread::sleep_for(std::chrono::microseconds(100));
        }
        /* The hash lock was released, we should try again lookup for the page
        until it's gone - it should disappear eventually when the IO ends. */
        continue;
      }

      if (m_is_temp_space) {
        temp_space_page_handler(block);
      } else {
        buf_block_fix(block);
      }

      /* Now safe to release page_hash S lock. */
      rw_lock_s_unlock(m_hash_lock);
      break;
    }

    if (m_mode == Page_fetch::IF_IN_POOL_OR_WATCH) {
      block = is_on_watch();
    }

    if (block != nullptr) {
      break;
    }

    if (is_optimistic() || m_mode == Page_fetch::IF_IN_POOL_OR_WATCH) {
      /* If it was an optimistic request, return the page only if it was
      found in the buffer pool and we haven't been able to find it then
      return nullptr (not found). */

      ut_ad(!rw_lock_own(m_hash_lock, RW_LOCK_X));
      ut_ad(!rw_lock_own(m_hash_lock, RW_LOCK_S));

      return (DB_NOT_FOUND);
    }

    /* Page not in buf_pool: needs to be read from file */
    read_page();
  }

  return (DB_SUCCESS);
}
```

## 동작 흐름

```text
 L3715  for (;;)
 L3722    block = [03] lookup()          찾으면 hash S 락을 쥔 채
 L3724    찾음
 L3725      stale 인가 (테이블스페이스가 삭제되거나 잘린 뒤 남은 블록, buf0buf.h L1255)
 L3726        buf_page_free_stale 이 락을 풀고 블록을 치운다
 L3730        I/O 중이라 못 치우면 100us 쉰다
 L3734        continue                        없어질 때까지 다시 찾는다
 L3737      buf_block_fix(block)              buf_fix_count++
 L3740      rw_lock_s_unlock(m_hash_lock)
 L3741      break
 L3745    못 찾음 -> [05] read_page()         그리고 다시 L3715
 L3748  return DB_SUCCESS                     NORMAL 은 DB_NOT_FOUND 를 돌려주지 않는다
```

```text
 normal 과 other 의 차이 (왼쪽 normal L3713, 오른쪽 other L3764)

 hit
   normal  buf_block_fix
   other   temp 공간이면 temp_space_page_handler, 아니면 buf_block_fix
 miss, IF_IN_POOL_OR_WATCH
   normal  해당 없음
   other   is_on_watch 로 watch 설정 (L3800)
 miss, optimistic (IF_IN_POOL, PEEK_IF_IN_POOL)
   normal  해당 없음
   other   DB_NOT_FOUND (L3815)
 miss, 그 밖
   둘 다   read_page

 temp 공간 페이지는 redo 가 기록되지 않아 래치 규칙이 다르다 (L3648-L3649 선언 주석)
 fix 도 block mutex 안에서 건다. 플러시 스레드와 이 mutex 로 맞춘다 (L4199-L4210)
```

이 루프가 한 바퀴 이상 도는 경우는 미적중 뒤의 재시도다. 읽기가 실패하면 [05] 가 `m_retries` 를 올리며 다시 돌고, `BUF_PAGE_READ_MAX_RETRIES`(100, L298) 를 넘으면 `ib::fatal` 로 서버를 멈춘다(L4127, L4133). stale 블록을 만나면 사라질 때까지 다시 찾는다(L3734).

## 결과가 쓰이는 곳

```text
 buf-fix 가 걸린 block
      --> [02] single_page 가 check_state 와 래치를 이어서 한다
 read_page 가 page hash 에 올린 블록
      --> 다음 바퀴의 lookup 이 찾는다. 찾은 블록이 아직 IO_READ 면
          [02] 의 buf_wait_for_read 가 기다린다
```

## 다루지 않는 것

stale 판정(`was_stale`, 테이블스페이스 드롭 뒤 버퍼 풀에 남은 블록을 게으르게 치우는 방식), `is_on_watch` 와 `buf_pool_watch_set`, `temp_space_page_handler` 의 fix 규칙은 이 함수의 곁가지라 요약만 했다.
