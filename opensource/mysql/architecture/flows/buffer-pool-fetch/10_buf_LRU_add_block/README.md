# buf_LRU_add_block

상위: [버퍼 풀 페이지 획득](../README.md)

**블록을 LRU 리스트에 넣는 함수다.** 공개 함수는 `buf_LRU_add_block_low` 를 부르기만 하고, 본체는 두 가지 자리 중 하나를 고른다. `old=false` 면 리스트 머리, `old=true` 면 `LRU_old` 가 가리키는 **old 구간의 첫 블록 바로 뒤**다. 넣은 뒤에는 old 구간의 길이가 목표 비율에서 허용 오차(20장)를 넘게 벗어났는지 보고 `LRU_old` 포인터를 한 칸씩 옮긴다. 이것이 midpoint insertion 의 구현이다.

## 위치

`storage` / `innobase` / `buf` / `buf0lru.cc` L1714-L1722 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1714-L1722))

## 실제 코드

`storage` / `innobase` / `buf` / `buf0lru.cc` L1648-L1722 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1648-L1722))

```cpp
// buf0lru.cc L1648-L1722
/** Adds a block to the LRU list. Please make sure that the page_size is
already set when invoking the function, so that we can get correct
page_size from the buffer page when adding a block into LRU
@param[in]      bpage   control block
@param[in]      old     true if should be put to the old blocks in the LRU list,
                        else put to the start; if the LRU list is very short,
                        the block is added to the start, regardless of this
                        parameter */
static inline void buf_LRU_add_block_low(buf_page_t *bpage, bool old) {
  buf_pool_t *buf_pool = buf_pool_from_bpage(bpage);

  ut_ad(mutex_own(&buf_pool->LRU_list_mutex));

  ut_a(buf_page_in_file(bpage));
  ut_ad(!bpage->in_LRU_list);

  if (!old || (UT_LIST_GET_LEN(buf_pool->LRU) < BUF_LRU_OLD_MIN_LEN)) {
    UT_LIST_ADD_FIRST(buf_pool->LRU, bpage);

    bpage->freed_page_clock = buf_pool->freed_page_clock;
  } else {
#ifdef UNIV_LRU_DEBUG
    /* buf_pool->LRU_old must be the first item in the LRU list
    whose "old" flag is set. */
    ut_a(buf_pool->LRU_old->old);
    ut_a(!UT_LIST_GET_PREV(LRU, buf_pool->LRU_old) ||
         !UT_LIST_GET_PREV(LRU, buf_pool->LRU_old)->old);
    ut_a(!UT_LIST_GET_NEXT(LRU, buf_pool->LRU_old) ||
         UT_LIST_GET_NEXT(LRU, buf_pool->LRU_old)->old);
#endif /* UNIV_LRU_DEBUG */
    UT_LIST_INSERT_AFTER(buf_pool->LRU, buf_pool->LRU_old, bpage);

    buf_pool->LRU_old_len++;
  }

  ut_d(bpage->in_LRU_list = true);

  incr_LRU_size_in_bytes(bpage, buf_pool);

  if (UT_LIST_GET_LEN(buf_pool->LRU) > BUF_LRU_OLD_MIN_LEN) {
    ut_ad(buf_pool->LRU_old);

    /* Adjust the length of the old block list if necessary */

    buf_page_set_old(bpage, old);
    buf_LRU_old_adjust_len(buf_pool);

  } else if (UT_LIST_GET_LEN(buf_pool->LRU) == BUF_LRU_OLD_MIN_LEN) {
    /* The LRU list is now long enough for LRU_old to become
    defined: init it */

    buf_LRU_old_init(buf_pool);
  } else {
    buf_page_set_old(bpage, buf_pool->LRU_old != nullptr);
  }

  /* If this is a zipped block with decompressed frame as well
  then put it on the unzip_LRU list */
  if (buf_page_belongs_to_unzip_LRU(bpage)) {
    buf_unzip_LRU_add_block((buf_block_t *)bpage, old);
  }
}

/** Adds a block to the LRU list. Please make sure that the page_size is
 already set when invoking the function, so that we can get correct
 page_size from the buffer page when adding a block into LRU */
void buf_LRU_add_block(buf_page_t *bpage, /*!< in: control block */
                       bool old) /*!< in: true if should be put to the old
                                  blocks in the LRU list, else put to the start;
                                  if the LRU list is very short, the block is
                                  added to the start, regardless of this
                                  parameter */
{
  buf_LRU_add_block_low(bpage, old);
}
```

old 구간 길이의 목표와 조정이다.

`storage` / `innobase` / `buf` / `buf0lru.cc` L1436-L1501 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1436-L1501))

```cpp
// buf0lru.cc L1436-L1501
/** Calculates the desired number for the old blocks list.
@param[in]      buf_pool        buffer pool instance */
static size_t calculate_desired_LRU_old_size(const buf_pool_t *buf_pool) {
  return std::min(UT_LIST_GET_LEN(buf_pool->LRU) *
                      static_cast<size_t>(buf_pool->LRU_old_ratio) /
                      BUF_LRU_OLD_RATIO_DIV,
                  UT_LIST_GET_LEN(buf_pool->LRU) -
                      (BUF_LRU_OLD_TOLERANCE + BUF_LRU_NON_OLD_MIN_LEN));
}

/** Moves the LRU_old pointer so that the length of the old blocks list
is inside the allowed limits.
@param[in]      buf_pool        buffer pool instance */
static inline void buf_LRU_old_adjust_len(buf_pool_t *buf_pool) {
  ulint old_len;
  ulint new_len;

// ... (L1453-L1469 생략: 단언과 UNIV_LRU_DEBUG 검사)

  old_len = buf_pool->LRU_old_len;
  new_len = calculate_desired_LRU_old_size(buf_pool);

  for (;;) {
    buf_page_t *LRU_old = buf_pool->LRU_old;

// ... (L1477-L1481 생략: 단언과 UNIV_LRU_DEBUG 검사)

    /* Update the LRU_old pointer if necessary */

    if (old_len + BUF_LRU_OLD_TOLERANCE < new_len) {
      buf_pool->LRU_old = LRU_old = UT_LIST_GET_PREV(LRU, LRU_old);
#ifdef UNIV_LRU_DEBUG
      ut_a(!LRU_old->old);
#endif /* UNIV_LRU_DEBUG */
      old_len = ++buf_pool->LRU_old_len;
      buf_page_set_old(LRU_old, true);

    } else if (old_len > new_len + BUF_LRU_OLD_TOLERANCE) {
      buf_pool->LRU_old = UT_LIST_GET_NEXT(LRU, LRU_old);
      old_len = --buf_pool->LRU_old_len;
      buf_page_set_old(LRU_old, false);
    } else {
      return;
    }
  }
}
```

리스트가 처음 512장이 될 때 old 구간이 생긴다.

`storage` / `innobase` / `buf` / `buf0lru.cc` L1503-L1528 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L1503-L1528))

```cpp
// buf0lru.cc L1503-L1528
/** Initializes the old blocks pointer in the LRU list. This function should be
called when the LRU list grows to BUF_LRU_OLD_MIN_LEN length.
@param[in,out]  buf_pool        buffer pool instance */
static void buf_LRU_old_init(buf_pool_t *buf_pool) {
  ut_ad(mutex_own(&buf_pool->LRU_list_mutex));
  ut_a(UT_LIST_GET_LEN(buf_pool->LRU) == BUF_LRU_OLD_MIN_LEN);

  /* We first initialize all blocks in the LRU list as old and then use
  the adjust function to move the LRU_old pointer to the right
  position */

  for (buf_page_t *bpage = UT_LIST_GET_LAST(buf_pool->LRU); bpage != nullptr;
       bpage = UT_LIST_GET_PREV(LRU, bpage)) {
    ut_ad(bpage->in_LRU_list);
    ut_ad(buf_page_in_file(bpage));

    /* This loop temporarily violates the
    assertions of buf_page_set_old(). */
    bpage->old = true;
  }

  buf_pool->LRU_old = UT_LIST_GET_FIRST(buf_pool->LRU);
  buf_pool->LRU_old_len = UT_LIST_GET_LEN(buf_pool->LRU);

  buf_LRU_old_adjust_len(buf_pool);
}
```

상수들이다.

`storage` / `innobase` / `buf` / `buf0lru.cc` L60-L74 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0lru.cc#L60-L74))

```cpp
// buf0lru.cc L60-L74
/** The number of blocks from the LRU_old pointer onward, including
the block pointed to, must be buf_pool->LRU_old_ratio/BUF_LRU_OLD_RATIO_DIV
of the whole LRU list length, except that the tolerance defined below
is allowed. Note that the tolerance must be small enough such that for
even the BUF_LRU_OLD_MIN_LEN long LRU list, the LRU_old pointer is not
allowed to point to either end of the LRU list. */

constexpr uint32_t BUF_LRU_OLD_TOLERANCE = 20;

/** The minimum amount of non-old blocks when the LRU_old list exists
(that is, when there are more than BUF_LRU_OLD_MIN_LEN blocks).
@see buf_LRU_old_adjust_len */
constexpr uint32_t BUF_LRU_NON_OLD_MIN_LEN = 5;
static_assert(BUF_LRU_NON_OLD_MIN_LEN < BUF_LRU_OLD_MIN_LEN,
              "BUF_LRU_NON_OLD_MIN_LEN >= BUF_LRU_OLD_MIN_LEN");
```

## 동작 흐름

```text
 buf_LRU_add_block_low(bpage, old)  (L1656)

 L1664  !old 이거나 LRU 길이 < 512 (BUF_LRU_OLD_MIN_LEN)
 L1665    UT_LIST_ADD_FIRST                    머리에
 L1667    bpage->freed_page_clock = pool 값    [09] 의 거리 재기 기준점
        아니면
 L1678    UT_LIST_INSERT_AFTER(LRU_old, bpage) old 구간 첫 블록 뒤에
 L1680    LRU_old_len++

 L1687  길이 > 512
 L1692    buf_page_set_old(bpage, old)
 L1693    buf_LRU_old_adjust_len
 L1695  길이 == 512                           buf_LRU_old_init: 전부 old 로 두고 조정
 L1701  길이 < 512                            old = (LRU_old != nullptr)
 L1706  압축본이 있으면 unzip_LRU 에도
```

`LRU_old` 는 old 구간의 첫 블록을 가리킨다. 그래서 `INSERT_AFTER(LRU_old)` 로 넣은 블록은 old 구간의 두 번째 자리에 들어간다.

```text
 old=true 로 넣을 때 (LRU 길이 >= 512)

 전   머리 [y][y][y][y][y][y][y][O1][o][o][o][o] 꼬리
                              ^ LRU_old = O1
 후   머리 [y][y][y][y][y][y][y][O1][N][o][o][o][o] 꼬리
                                    ^ 새 블록 N, old=true, LRU_old_len+1

 old=false 로 넣을 때 (make_young, 또는 짧은 리스트)
 후   머리 [N][y][y][y][y][y][y][y][O1][o][o][o][o] 꼬리
          ^ young 이 하나 늘었다. old 비율이 줄었으면 adjust 가 LRU_old 를 앞으로 당긴다
```

```text
 buf_LRU_old_adjust_len (L1449)

 L1438  new_len = min(LRU 길이 * LRU_old_ratio / 1024,  LRU 길이 - (20 + 5))
 되풀이
   L1485  old_len + 20 < new_len 이면 LRU_old 를 앞(머리 쪽)으로 한 칸, 그 블록을 old 로
   L1493  old_len > new_len + 20 이면 LRU_old 를 뒤로 한 칸, 이전 LRU_old 를 young 으로
          그 밖이면 멈춘다

 20 = BUF_LRU_OLD_TOLERANCE, 5 = BUF_LRU_NON_OLD_MIN_LEN (young 은 최소 5장)
 매 삽입마다 비율을 정확히 맞추지 않고, 오차 20장을 넘을 때만 포인터를 옮긴다
```

```text
 LRU 에 들어가는 자리 모음

 호출                                     old     자리
 buf_page_init_for_read         L4979     true    old 구간
 buf_LRU_make_block_young       L1736     false   머리
 buf_LRU_make_block_old         L1747     true    old 구간
```

## 결과가 쓰이는 곳

```text
 LRU 리스트와 LRU_old
      --> [08] 의 꼬리 스캔 순서
      --> [09] 가 bpage->old 로 old 구간 여부를 본다
 bpage->freed_page_clock
      --> [09] buf_page_peek_if_young 의 기준점
```

## 다루지 않는 것

`buf_LRU_remove_block` 이 LRU_old 를 옮기는 경우, unzip_LRU 의 별도 규칙, `innodb_old_blocks_pct` 를 바꿀 때의 `buf_LRU_old_ratio_update` 는 이 함수의 곁가지라 요약만 했다. 버퍼 풀 전체 자료구조(`buf_pool_t` 의 LRU, free, flush_list)는 [메모리 구조](../../structure/memory-structures/README.md)에서 다룬다.
