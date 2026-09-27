# buf_page_make_young_if_needed

상위: [버퍼 풀 페이지 획득](../README.md)

**적중한 페이지를 LRU 머리로 올릴지 정하는 함수다.** 몸체는 `buf_page_peek_if_too_old` 가 참이면 `buf_page_make_young` 을 부르는 두 줄이고, 판정이 전부 `peek_if_too_old` 에 있다. 판정은 세 갈래다. 아직 한 장도 쫓겨난 적이 없으면 아무것도 옮기지 않는다. old 구간의 페이지는 **첫 접근에서 `innodb_old_blocks_time` 이 지난 뒤에만** 올린다. young 구간의 페이지는 머리에서 충분히 멀어졌을 때만 올린다. 매 적중마다 LRU 뮤텍스를 잡지 않으려는 장치다.

## 위치

`storage` / `innobase` / `buf` / `buf0buf.cc` L3212-L3220 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3212-L3220))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0buf.cc` L3180-L3220 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0buf.cc#L3180-L3220))

```cpp
// buf0buf.cc L3180-L3220
/** Moves a page to the start of the buffer pool LRU list. This high-level
function can be used to prevent an important page from slipping out of
the buffer pool.
@param[in,out]  bpage   buffer block of a file page */
void buf_page_make_young(buf_page_t *bpage) {
  buf_pool_t *buf_pool = buf_pool_from_bpage(bpage);

  mutex_enter(&buf_pool->LRU_list_mutex);

  ut_a(buf_page_in_file(bpage));

  buf_LRU_make_block_young(bpage);

  mutex_exit(&buf_pool->LRU_list_mutex);
}

void buf_page_make_old(buf_page_t *bpage) {
  buf_pool_t *buf_pool = buf_pool_from_bpage(bpage);

  mutex_enter(&buf_pool->LRU_list_mutex);

  ut_a(buf_page_in_file(bpage));

  buf_LRU_make_block_old(bpage);

  mutex_exit(&buf_pool->LRU_list_mutex);
}

/** Moves a page to the start of the buffer pool LRU list if it is too old.
This high-level function can be used to prevent an important page from
slipping out of the buffer pool. The page must be fixed to the buffer pool.
@param[in,out]  bpage   buffer block of a file page */
static void buf_page_make_young_if_needed(buf_page_t *bpage) {
  ut_ad(!mutex_own(&buf_pool_from_bpage(bpage)->LRU_list_mutex));
  ut_ad(bpage->buf_fix_count > 0);
  ut_a(buf_page_in_file(bpage));

  if (buf_page_peek_if_too_old(bpage)) {
    buf_page_make_young(bpage);
  }
}
```

판정 두 함수다.

`storage` / `innobase` / `include` / `buf0buf.ic` L155-L203 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.ic#L155-L203))

```cpp
// buf0buf.ic L155-L203
/** Tells, for heuristics, if a block is still close enough to the MRU end of
the LRU list meaning that it is not in danger of getting evicted and also
implying that it has been accessed recently.
The page must be either buffer-fixed, either its page hash must be locked.
@param[in]      bpage   block
@return true if block is close to MRU end of LRU */
static inline bool buf_page_peek_if_young(const buf_page_t *bpage) {
  buf_pool_t *buf_pool = buf_pool_from_bpage(bpage);

  ut_ad(bpage->buf_fix_count > 0 ||
        buf_page_hash_lock_held_s_or_x(buf_pool, bpage));

  /* FIXME: bpage->freed_page_clock is 31 bits */
  return ((buf_pool->freed_page_clock & ((1UL << 31) - 1)) <
          ((ulint)bpage->freed_page_clock +
           (buf_pool->curr_size *
            (BUF_LRU_OLD_RATIO_DIV - buf_pool->LRU_old_ratio) /
            (BUF_LRU_OLD_RATIO_DIV * 4))));
}

/** Recommends a move of a block to the start of the LRU list if there is
danger of dropping from the buffer pool.
NOTE: does not reserve the LRU list mutex.
@param[in]      bpage   block to make younger
@return true if should be made younger */
static inline bool buf_page_peek_if_too_old(const buf_page_t *bpage) {
  buf_pool_t *buf_pool = buf_pool_from_bpage(bpage);

  if (buf_pool->freed_page_clock == 0) {
    /* If eviction has not started yet, do not update the
    statistics or move blocks in the LRU list.  This is
    either the warm-up phase or an in-memory workload. */
    return false;
  } else if (get_buf_LRU_old_threshold() != std::chrono::seconds::zero() &&
             bpage->old) {
    const auto access_time = buf_page_is_accessed(bpage);

    if (access_time != std::chrono::steady_clock::time_point{} &&
        (std::chrono::steady_clock::now() - access_time) >=
            get_buf_LRU_old_threshold()) {
      return true;
    }

    buf_pool->stat.n_pages_not_made_young++;
    return false;
  } else {
    return (!buf_page_peek_if_young(bpage));
  }
}
```

두 설정값의 정의다. `innodb_old_blocks_pct` 기본값은 `100 * 3 / 8`(정수 나눗셈으로 37), `innodb_old_blocks_time` 기본값은 1000(ms)이다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L23111-L23121 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L23111-L23121))

```cpp
// ha_innodb.cc L23111-L23121
static MYSQL_SYSVAR_UINT(
    old_blocks_pct, innobase_old_blocks_pct, PLUGIN_VAR_RQCMDARG,
    "Percentage of the buffer pool to reserve for 'old' blocks.", nullptr,
    innodb_old_blocks_pct_update, 100 * 3 / 8, 5, 95, 0);

static MYSQL_SYSVAR_UINT(
    old_blocks_time, buf_LRU_old_threshold, PLUGIN_VAR_RQCMDARG,
    "Move blocks to the 'new' end of the buffer pool if the first access"
    " was at least this many milliseconds ago."
    " The timeout is disabled if 0.",
    nullptr, nullptr, 1000, 0, UINT32_MAX, 0);
```

## 동작 흐름

```text
 buf_page_peek_if_too_old (buf0buf.ic L180)

 L183  buf_pool->freed_page_clock == 0            아직 축출이 한 번도 없었다
         false                                    워밍업 중이거나 전부 메모리에 들어가는 부하
 L188  old_blocks_time != 0 이고 bpage->old       old 구간
 L190    access_time = 첫 접근 시각
 L192    접근 기록이 있고 now - access_time >= old_blocks_time
 L195      true                                   --> make_young
 L198    n_pages_not_made_young++, false
 L201  그 밖 (young 구간, 또는 old_blocks_time = 0)
         !buf_page_peek_if_young(bpage)

 true 면 buf_page_make_young (L3184)
   L3187  LRU_list_mutex
   L3191  buf_LRU_make_block_young
            old 였으면 n_pages_made_young++       (buf0lru.cc L1731)
            buf_LRU_remove_block -> buf_LRU_add_block_low(bpage, false)   머리로
```

young 판정은 "이 블록이 마지막으로 머리에 놓인 뒤 몇 장이 쫓겨났는가"로 거리를 잰다. 블록마다 머리에 놓일 때의 `freed_page_clock` 을 적어 두고(buf0lru.cc L1667), 교체될 때마다 전역 값이 1씩 는다(buf0lru.cc L2104).

```text
 buf_page_peek_if_young (buf0buf.ic L161)

 young  <=>  pool.freed_page_clock < bpage.freed_page_clock
                                     + curr_size * (1024 - LRU_old_ratio) / (1024 * 4)

 LRU_old_ratio = old_blocks_pct * 1024 / 100 (buf0lru.cc L2353). 기본 37 이면 378
 curr_size = 16384 장 (256MB, 16KB 페이지) 이라 치면
   16384 * (1024 - 378) / 4096 = 2584

 곧 블록이 머리에 놓인 뒤 2584 장이 쫓겨나기 전까지는 다시 올리지 않는다
 young 구간 길이(약 5/8)의 1/4 만큼 밀려나야 올린다는 뜻이다
```

```text
 판정 요약

 축출이 아직 없음
   -> 안 옮김
 old, 첫 접근 뒤 old_blocks_time 미만
   -> 안 옮김, n_pages_not_made_young++
 old, 첫 접근 뒤 old_blocks_time 이상
   -> 머리로, n_pages_made_young++
 young, 머리에서 충분히 가까움
   -> 안 옮김
 young, young 구간 길이의 1/4 이상 밀려남
   -> 머리로

 old_blocks_time = 0 으로 두면 old 페이지도 young 규칙(거리)을 따른다
```

## 결과가 쓰이는 곳

```text
 LRU 순서
      --> [08] 의 꼬리 스캔이 교체 대상을 고르는 순서
 n_pages_made_young / n_pages_not_made_young
      --> SHOW ENGINE INNODB STATUS 의 "Pages made young ..., not young ..."
          큰 스캔이 old 구간 안에서만 돌고 있는지를 여기서 본다
```

## 다루지 않는 것

`buf_page_make_old`(명시적으로 old 구간으로 보내는 경로, buf0lru.cc L1747 에서 add_block_low(true)), `buf_page_get_known_nowait` 의 `Cache_hint::MAKE_YOUNG`, `freed_page_clock` 이 31비트로 잘리는 문제(buf0buf.ic L167 의 FIXME)는 이 함수의 곁가지라 요약만 했다. 목록 조작 자체는 [10 buf_LRU_add_block](../10_buf_LRU_add_block/README.md)에 있다.
