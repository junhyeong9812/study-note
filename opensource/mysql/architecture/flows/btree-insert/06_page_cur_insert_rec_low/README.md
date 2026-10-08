# page_cur_insert_rec_low

상위: [B+Tree 삽입과 분할](../README.md)

**레코드 하나를 비압축 인덱스 페이지에 실제로 써 넣는 함수다.** 주석이 1 부터 9 까지 번호를 매겨 둔 그대로 읽으면 된다. 공간을 얻고(삭제된 레코드의 free list 먼저, 없으면 heap 꼭대기), 바이트를 복사하고, next 포인터로 연결 리스트에 끼우고, 페이지 헤더와 **page directory** 를 고치고, 마지막으로 redo 로그를 mtr 에 쌓는다. 레코드는 페이지 안에서 **키 순서로 놓이지 않는다.** 키 순서는 next 포인터 연결 리스트가 만들고, page directory 는 그 리스트 위의 이정표다.

## 위치

`storage` / `innobase` / `page` / `page0cur.cc` L1229-L1417 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/page/page0cur.cc#L1229-L1417))

## 실제 코드

`storage` / `innobase` / `page` / `page0cur.cc` L1229-L1417 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/page/page0cur.cc#L1229-L1417))

```cpp
// page0cur.cc L1229-L1417
rec_t *page_cur_insert_rec_low(
    rec_t *current_rec,  /*!< in: pointer to current record after
                     which the new record is inserted */
    dict_index_t *index, /*!< in: record descriptor */
    const rec_t *rec,    /*!< in: pointer to a physical record */
    ulint *offsets,      /*!< in/out: rec_get_offsets(rec, index) */
    mtr_t *mtr)          /*!< in: mini-transaction handle, or NULL */
{
  byte *insert_buf;
  ulint rec_size;
  page_t *page;       /*!< the relevant page */
  rec_t *last_insert; /*!< cursor position at previous
                      insert */
  rec_t *free_rec;    /*!< a free record that was reused,
                      or NULL */
  rec_t *insert_rec;  /*!< inserted record */
  ulint heap_no;      /*!< heap number of the inserted
                      record */

  ut_ad(rec_offs_validate(rec, index, offsets));

  page = page_align(current_rec);
  // ... (L1251-L1257 생략: 페이지 형식과 인덱스 id 검사 assert)

  /* 1. Get the size of the physical record in the page */
  rec_size = rec_offs_size(offsets);

// ... (L1262-L1274 생략: Valgrind 검사)

  /* 2. Try to find suitable space from page memory management */

  free_rec = page_header_get_ptr(page, PAGE_FREE);
  if (UNIV_LIKELY_NULL(free_rec)) {
    /* Try to allocate from the head of the free list. */
    ulint foffsets_[REC_OFFS_NORMAL_SIZE];
    ulint *foffsets = foffsets_;
    mem_heap_t *heap = nullptr;

    rec_offs_init(foffsets_);

    foffsets = rec_get_offsets(free_rec, index, foffsets, ULINT_UNDEFINED,
                               UT_LOCATION_HERE, &heap);

    if (rec_offs_size(foffsets) < rec_size) {
      if (UNIV_LIKELY_NULL(heap)) {
        mem_heap_free(heap);
      }

      goto use_heap;
    }

    insert_buf = free_rec - rec_offs_extra_size(foffsets);

    if (page_is_comp(page)) {
      heap_no = rec_get_heap_no_new(free_rec);
      page_mem_alloc_free(page, nullptr, rec_get_next_ptr(free_rec, true),
                          rec_size);
    } else {
      heap_no = rec_get_heap_no_old(free_rec);
      page_mem_alloc_free(page, nullptr, rec_get_next_ptr(free_rec, false),
                          rec_size);
    }

    if (UNIV_LIKELY_NULL(heap)) {
      mem_heap_free(heap);
    }
  } else {
  use_heap:
    free_rec = nullptr;
    insert_buf = page_mem_alloc_heap(page, nullptr, rec_size, &heap_no);

    if (UNIV_UNLIKELY(insert_buf == nullptr)) {
      return (nullptr);
    }
  }

  /* 3. Create the record */
  insert_rec = rec_copy(insert_buf, rec, offsets);
  rec_offs_make_valid(insert_rec, index, offsets);

  /* 4. Insert the record in the linked list of records */
  ut_ad(current_rec != insert_rec);

  {
    /* next record after current before the insertion */
    rec_t *next_rec = page_rec_get_next(current_rec);
// ... (L1333-L1339 생략: 디버그 상태 검사)
    page_rec_set_next(insert_rec, next_rec);
    page_rec_set_next(current_rec, insert_rec);
  }

  page_header_set_field(page, nullptr, PAGE_N_RECS, 1 + page_get_n_recs(page));

  /* 5. Set the n_owned field in the inserted record to zero,
  and set the heap_no field */
  if (page_is_comp(page)) {
    rec_set_n_owned_new(insert_rec, nullptr, 0);
    rec_set_heap_no_new(insert_rec, heap_no);
  } else {
    rec_set_n_owned_old(insert_rec, 0);
    rec_set_heap_no_old(insert_rec, heap_no);
  }

  UNIV_MEM_ASSERT_RW(rec_get_start(insert_rec, offsets),
                     rec_offs_size(offsets));
  /* 6. Update the last insertion info in page header */

  last_insert = page_header_get_ptr(page, PAGE_LAST_INSERT);
  ut_ad(!last_insert || !page_is_comp(page) ||
        rec_get_node_ptr_flag(last_insert) ==
            rec_get_node_ptr_flag(insert_rec));

  if (!dict_index_is_spatial(index)) {
    if (UNIV_UNLIKELY(last_insert == nullptr)) {
      page_header_set_field(page, nullptr, PAGE_DIRECTION, PAGE_NO_DIRECTION);
      page_header_set_field(page, nullptr, PAGE_N_DIRECTION, 0);

    } else if ((last_insert == current_rec) &&
               (page_header_get_field(page, PAGE_DIRECTION) != PAGE_LEFT)) {
      page_header_set_field(page, nullptr, PAGE_DIRECTION, PAGE_RIGHT);
      page_header_set_field(page, nullptr, PAGE_N_DIRECTION,
                            page_header_get_field(page, PAGE_N_DIRECTION) + 1);

    } else if ((page_rec_get_next(insert_rec) == last_insert) &&
               (page_header_get_field(page, PAGE_DIRECTION) != PAGE_RIGHT)) {
      page_header_set_field(page, nullptr, PAGE_DIRECTION, PAGE_LEFT);
      page_header_set_field(page, nullptr, PAGE_N_DIRECTION,
                            page_header_get_field(page, PAGE_N_DIRECTION) + 1);
    } else {
      page_header_set_field(page, nullptr, PAGE_DIRECTION, PAGE_NO_DIRECTION);
      page_header_set_field(page, nullptr, PAGE_N_DIRECTION, 0);
    }
  }

  page_header_set_ptr(page, nullptr, PAGE_LAST_INSERT, insert_rec);

  /* 7. It remains to update the owner record. */
  {
    rec_t *owner_rec = page_rec_find_owner_rec(insert_rec);
    ulint n_owned;
    if (page_is_comp(page)) {
      n_owned = rec_get_n_owned_new(owner_rec);
      rec_set_n_owned_new(owner_rec, nullptr, n_owned + 1);
    } else {
      n_owned = rec_get_n_owned_old(owner_rec);
      rec_set_n_owned_old(owner_rec, n_owned + 1);
    }

    /* 8. Now we have incremented the n_owned field of the owner
    record. If the number exceeds PAGE_DIR_SLOT_MAX_N_OWNED,
    we have to split the corresponding directory slot in two. */

    if (UNIV_UNLIKELY(n_owned == PAGE_DIR_SLOT_MAX_N_OWNED)) {
      page_dir_split_slot(page, nullptr, page_dir_find_owner_slot(owner_rec));
    }
  }

  /* 9. Write log record of the insert */
  if (UNIV_LIKELY(mtr != nullptr)) {
    page_cur_insert_rec_write_log(insert_rec, rec_size, current_rec, index,
                                  mtr);
  }

  return (insert_rec);
}
```

heap 에서 공간을 받는 쪽이다. heap 꼭대기를 올리고 다음 heap 번호를 돌려준다.

`storage` / `innobase` / `page` / `page0page.cc` L223-L252 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/page/page0page.cc#L223-L252))

```cpp
// page0page.cc L223-L252
byte *page_mem_alloc_heap(
    page_t *page,             /*!< in/out: index page */
    page_zip_des_t *page_zip, /*!< in/out: compressed page with enough
                             space available for inserting the record,
                             or NULL */
    ulint need,               /*!< in: total number of bytes needed */
    ulint *heap_no)           /*!< out: this contains the heap number
                              of the allocated record
                              if allocation succeeds */
{
  byte *block;
  ulint avl_space;

  ut_ad(page && heap_no);

  avl_space = page_get_max_insert_size(page, 1);

  if (avl_space >= need) {
    block = page_header_get_ptr(page, PAGE_HEAP_TOP);

    page_header_set_ptr(page, page_zip, PAGE_HEAP_TOP, block + need);
    *heap_no = page_dir_get_n_heap(page);

    page_dir_set_n_heap(page, page_zip, 1 + *heap_no);

    return (block);
  }

  return (nullptr);
}
```

8 개를 넘게 소유한 슬롯은 반으로 나눈다.

`storage` / `innobase` / `page` / `page0page.cc` L1283-L1333 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/page/page0page.cc#L1283-L1333))

```cpp
// page0page.cc L1283-L1333
void page_dir_split_slot(page_t *page, page_zip_des_t *page_zip,
                         ulint slot_no) {
  rec_t *rec;
  page_dir_slot_t *new_slot;
  page_dir_slot_t *prev_slot;
  page_dir_slot_t *slot;
  ulint i;
  ulint n_owned;

  ut_ad(page);
  ut_ad(!page_zip || page_is_comp(page));
  ut_ad(slot_no > 0);

  slot = page_dir_get_nth_slot(page, slot_no);

  n_owned = page_dir_slot_get_n_owned(slot);
  ut_ad(n_owned == PAGE_DIR_SLOT_MAX_N_OWNED + 1);

  /* 1. We loop to find a record approximately in the middle of the
  records owned by the slot. */

  prev_slot = page_dir_get_nth_slot(page, slot_no - 1);
  rec = (rec_t *)page_dir_slot_get_rec(prev_slot);

  for (i = 0; i < n_owned / 2; i++) {
    rec = page_rec_get_next(rec);
  }

  ut_ad(n_owned / 2 >= PAGE_DIR_SLOT_MIN_N_OWNED);

  /* 2. We add one directory slot immediately below the slot to be
  split. */

  page_dir_add_slot(page, page_zip, slot_no - 1);

  /* The added slot is now number slot_no, and the old slot is
  now number slot_no + 1 */

  new_slot = page_dir_get_nth_slot(page, slot_no);
  slot = page_dir_get_nth_slot(page, slot_no + 1);

  /* 3. We store the appropriate values to the new slot. */

  page_dir_slot_set_rec(new_slot, rec);
  page_dir_slot_set_n_owned(new_slot, page_zip, n_owned / 2);

  /* 4. Finally, we update the number of records field of the
  original slot */

  page_dir_slot_set_n_owned(slot, page_zip, n_owned - (n_owned / 2));
}
```

## 동작 흐름

```text
 L1260  1. rec_size = rec_offs_size(offsets)               헤더 + 데이터
 L1278  2. free_rec = PAGE_FREE 리스트의 머리               삭제된 레코드가 남긴 자리
 L1290     그 자리가 작으면 use_heap
 L1298     크면 그 자리를 쓰고 heap_no 도 물려받는다 (page_mem_alloc_free)
 L1314     use_heap: page_mem_alloc_heap                  PAGE_HEAP_TOP += rec_size,
                                                          heap_no = PAGE_N_HEAP, N_HEAP++
 L1319     공간이 없으면 nullptr                            ([03] 이 재구성 후 재시도)
 L1324  3. rec_copy(insert_buf, rec, offsets)              [05] 가 만든 바이트를 복사
 L1340  4. insert_rec->next = current_rec->next
 L1341     current_rec->next = insert_rec                   연결 리스트에 끼운다
 L1344     PAGE_N_RECS++
 L1349  5. n_owned = 0, heap_no 기록
 L1360  6. PAGE_LAST_INSERT 와 PAGE_DIRECTION 갱신
 L1370     PAGE_RIGHT, N_DIRECTION++           직전 삽입 바로 뒤
 L1376     PAGE_LEFT, N_DIRECTION++            직전 삽입 바로 앞
 L1382     NO_DIRECTION, N_DIRECTION = 0       그 밖
 L1391  7. owner = page_rec_find_owner_rec(insert_rec)    n_owned != 0 인 다음 레코드
 L1395     owner.n_owned++
 L1405  8. 올리기 전 n_owned 가 8 (PAGE_DIR_SLOT_MAX_N_OWNED) 이었으면
 L1406     page_dir_split_slot                            슬롯 하나를 둘로
 L1412  9. page_cur_insert_rec_write_log                  mtr 에 MLOG_REC_INSERT
```

페이지 안의 배치다. 레코드 바이트는 heap 에 들어온 순서대로 높은 주소 쪽으로 쌓이고, page directory 는 페이지 끝에서 낮은 주소 쪽으로 자란다.

```text
 비압축 인덱스 페이지 (위가 낮은 주소, 아래가 높은 주소)

 +----------------------------------------------
 | FIL header (38 B)                              FIL_PAGE_DATA = 38
 | page header  PAGE_N_HEAP, PAGE_HEAP_TOP,
 |              PAGE_FREE, PAGE_LAST_INSERT,
 |              PAGE_DIRECTION, PAGE_N_RECS ...
 | infimum | supremum                             heap_no 0, 1 (page0types.h L131-L133)
 | [rec 10] [rec 30] [rec 20] [rec 25]            heap_no 2, 3, 4, 5  들어온 순서
 |                     ^ PAGE_HEAP_TOP            여기서 아래(높은 주소)로 자란다
 |
 |                  free space
 |
 |           ... slot2 slot1 slot0                page directory, 슬롯 2 B, 위로 자란다
 | FIL trailer (8 B)                              PAGE_DIR = FIL_PAGE_DATA_END (page0page.h L61)
 +----------------------------------------------

 키 순서는 next 포인터가 만든다
   infimum -> 10 -> 20 -> 25 -> 30 -> supremum
```

page directory 의 슬롯은 연결 리스트의 몇몇 레코드("owner")를 가리키고, owner 의 n_owned 는 자기 앞쪽 그룹의 레코드 수다. 탐색은 슬롯으로 이진 탐색해 그룹을 고른 뒤 그룹 안을 따라간다. 삽입은 그룹 하나를 키우고, 8 을 넘으면 그룹을 가른다.

```text
 레코드 삽입 시 page directory 변화 (n_owned 는 owner 레코드에만 0 이 아닌 값)

 삽입 전: 그룹 B 가 8 개를 소유
   infimum(1) | a b c d e f g h(8) | ... supremum(k)
   slot0 -> infimum     slot1 -> h (n_owned 8)      slot2 -> supremum

 새 레코드 x 를 c 와 d 사이에 넣는다
   L1341  a b c x d e f g h            x.n_owned = 0 (L1349)
   L1391  owner = x 에서 next 를 따라 n_owned != 0 인 첫 레코드 = h
   L1395  h.n_owned = 9
   L1405  올리기 전 값이 8 -> page_dir_split_slot(slot1)

 page_dir_split_slot (page0page.cc L1283)
   L1307  앞 슬롯(slot0)의 레코드에서 n_owned / 2 = 4 칸 전진 -> a, b, c, x 로 x
   L1316  page_dir_add_slot 로 slot1 자리에 새 슬롯을 끼운다 (기존 slot1 은 slot2 로 밀림)
   L1327  새 slot1 -> 그 레코드, n_owned = 4
   L1332  slot2 (h) n_owned = 9 - 4 = 5

 삽입 후
   infimum(1) | a b c x(4) | d e f g h(5) | ... supremum(k)
   slot0 -> infimum     slot1 -> x (4)    slot2 -> h (5)    slot3 -> supremum

 슬롯은 4 ~ 8 개를 소유한다 (PAGE_DIR_SLOT_MIN / MAX_N_OWNED, page0page.h L73-L74)
 첫 슬롯과 마지막 슬롯은 예외로 더 적을 수 있다 (L70-L72 주석)
```

```text
 PAGE_LAST_INSERT 와 PAGE_DIRECTION 이 쓰이는 곳

 [06] L1360-L1385  삽입할 때마다 방향과 연속 횟수를 적는다 (L1387 PAGE_LAST_INSERT = 새 레코드)
 [03] L2789 / [08] btr_page_get_split_rec_to_right / _left
                    PAGE_LAST_INSERT 만 읽어 순차 삽입을 알아채고 분할 지점을 고른다
 PAGE_DIRECTION, PAGE_N_DIRECTION 은 이 태그에서 다음 삽입의 [06] L1370, L1376 과
 page_header_print (page0page.cc L1649) 만 읽는다. 분할 판정은 이 값을 보지 않는다
```

## 결과가 쓰이는 곳

```text
 insert_rec
      --> [03] 이 lock_update_insert(block, rec) 로 잠금 표에 heap_no 를 알린다
      --> [01] 로 돌아가 커서가 이 레코드를 가리킨다
 MLOG_REC_INSERT 로그
      --> mtr.commit 때 log buffer 로 ([mini-transaction과 redo 기록])
      --> 크래시 뒤 [크래시 복구] 가 page_cur_parse_insert_rec 로 같은 삽입을 다시 한다
 PAGE_LAST_INSERT, PAGE_DIRECTION
      --> 다음 삽입의 순차 판정
```

## 다루지 않는 것

압축 페이지(`page_cur_insert_rec_zip`), REDUNDANT 형식(`rec_set_n_owned_old` 등 `_old` 함수), free list 에서 자리를 받는 `page_mem_alloc_free` 의 세부, redo 로그 레코드의 바이트 형식(`page_cur_insert_rec_write_log`), 슬롯이 너무 적어졌을 때의 `page_dir_balance_slot` 은 곁가지다. 페이지 헤더 필드의 자리는 [테이블스페이스와 페이지 레이아웃](../../../structure/tablespace-page/README.md)에서 다룬다.
