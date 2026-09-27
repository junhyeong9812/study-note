# btr_page_split_and_insert

상위: [B+Tree 삽입과 분할](../README.md)

**가득 찬 페이지를 둘로 나누고 튜플을 넣는 함수다.** 주석이 1 부터 8 까지 단계를 적어 두었다. 분할 전에 먼저 **오른쪽 형제에 넣어 볼 수 있으면** 분할하지 않는다. 분할한다면 (1) 자를 레코드를 고르고, (2) 새 페이지를 받고, (3) 윗쪽 절반의 첫 레코드를 정하고, (4) **트리 구조부터** 고친다(부모에 노드 포인터, 형제 링크). 그다음 (5) 레코드를 옮기고, (6) (7) 알맞은 절반에 튜플을 넣고, (8) 그래도 안 들어가면 처음으로 돌아가 다시 나눈다. 볼거리는 분할 지점을 고르는 규칙과, 리프에서 들어갈 자리가 확실하면 **레코드를 옮기기 전에 index->lock 을 먼저 놓는다**는 점이다.

## 위치

`storage` / `innobase` / `btr` / `btr0btr.cc` L2305-L2682 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L2305-L2682))

## 실제 코드

오른쪽 형제 시도와 분할 지점 결정이다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L2351-L2421 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L2351-L2421))

```cpp
// btr0btr.cc L2351-L2421
func_start:
  ut_ad(tuple->m_heap != *heap);
  mem_heap_empty(*heap);
  *offsets = nullptr;

  // ... (L2356-L2371 생략: 래치 소유 assert 와 블록 변수 준비)

  /* try to insert to the next page if possible before split */
  rec =
      btr_insert_into_right_sibling(flags, cursor, offsets, *heap, tuple, mtr);

  if (rec != nullptr) {
    return (rec);
  }

  page_no = block->page.id.page_no();

  /* 1. Decide the split record; split_rec == NULL means that the
  tuple to be inserted should be the first record on the upper
  half-page */
  insert_left = false;

  if (n_iterations > 0) {
    direction = FSP_UP;
    hint_page_no = page_no + 1;
    split_rec = btr_page_get_split_rec(cursor, tuple);

    if (split_rec == nullptr) {
      insert_left =
          btr_page_tuple_smaller(cursor, tuple, offsets, n_uniq, heap);
    }
  } else if (btr_page_get_split_rec_to_right(cursor, &split_rec)) {
    direction = FSP_UP;
    hint_page_no = page_no + 1;

  } else if (btr_page_get_split_rec_to_left(cursor, &split_rec)) {
    direction = FSP_DOWN;
    hint_page_no = page_no - 1;
    ut_ad(split_rec);
  } else {
    direction = FSP_UP;
    hint_page_no = page_no + 1;

    /* If there is only one record in the index page, we
    can't split the node in the middle by default. We need
    to determine whether the new record will be inserted
    to the left or right. */

    if (page_get_n_recs(page) > 1) {
      split_rec = page_get_middle_rec(page);
    } else if (btr_page_tuple_smaller(cursor, tuple, offsets, n_uniq, heap)) {
      split_rec = page_rec_get_next(page_get_infimum_rec(page));
    } else {
      split_rec = nullptr;
    }
  }
```

새 페이지를 받고, 트리 구조를 먼저 고치고, 조건이 맞으면 트리 래치를 놓는다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L2423-L2505 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L2423-L2505))

```cpp
// btr0btr.cc L2423-L2505
  /* 2. Allocate a new page to the index */
  new_block = btr_page_alloc(cursor->index, hint_page_no, direction,
                             btr_page_get_level(page), mtr, mtr);

  /* New page could not be allocated */
  if (!new_block) {
    return nullptr;
  }

  new_page = buf_block_get_frame(new_block);
  new_page_zip = buf_block_get_page_zip(new_block);
  btr_page_create(new_block, new_page_zip, cursor->index,
                  btr_page_get_level(page), mtr);

  /* 3. Calculate the first record on the upper half-page, and the
  first record (move_limit) on original page which ends up on the
  upper half */

  if (split_rec) {
    first_rec = move_limit = split_rec;

    *offsets = rec_get_offsets(split_rec, cursor->index, *offsets, n_uniq,
                               UT_LOCATION_HERE, heap);

    insert_left = cmp_dtuple_rec(tuple, split_rec, cursor->index, *offsets) < 0;

    if (!insert_left && new_page_zip && n_iterations > 0) {
      /* If a compressed page has already been split,
      avoid further splits by inserting the record
      to an empty page. */
      split_rec = nullptr;
      goto insert_empty;
    }
  } else if (insert_left) {
    ut_a(n_iterations > 0);
    first_rec = page_rec_get_next(page_get_infimum_rec(page));
    move_limit = page_rec_get_next(btr_cur_get_rec(cursor));
  } else {
  insert_empty:
    ut_ad(!split_rec);
    ut_ad(!insert_left);
    buf = ut::new_arr_withkey<byte>(
        UT_NEW_THIS_FILE_PSI_KEY,
        ut::Count{rec_get_converted_size(cursor->index, tuple)});

    first_rec = rec_convert_dtuple_to_rec(buf, cursor->index, tuple);
    move_limit = page_rec_get_next(btr_cur_get_rec(cursor));
  }

  /* 4. Do first the modifications in the tree structure */

  btr_attach_half_pages(flags, cursor->index, block, first_rec, new_block,
                        direction, mtr);

  /* If the split is made on the leaf level and the insert will fit
  on the appropriate half-page, we may release the tree x-latch.
  We can then move the records after releasing the tree latch,
  thus reducing the tree latch contention. */

  if (split_rec) {
    insert_will_fit =
        !new_page_zip &&
        btr_page_insert_fits(cursor, split_rec, offsets, tuple, heap);
  } else {
    if (!insert_left) {
      ut::delete_arr(buf);
      buf = nullptr;
    }

    insert_will_fit =
        !new_page_zip &&
        btr_page_insert_fits(cursor, nullptr, offsets, tuple, heap);
  }

  if (!srv_read_only_mode && !cursor->index->table->is_intrinsic() &&
      insert_will_fit && page_is_leaf(page) &&
      !dict_index_is_online_ddl(cursor->index)) {
    mtr->memo_release(dict_index_get_lock(cursor->index),
                      MTR_MEMO_X_LOCK | MTR_MEMO_SX_LOCK);

    /* NOTE: We cannot release root block latch here, because it
    has segment header and already modified in most of cases.*/
  }
```

레코드를 옮긴다. 아래로(FSP_DOWN) 나누면 새 페이지가 왼쪽, 위로(FSP_UP) 나누면 새 페이지가 오른쪽이다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L2507-L2592 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L2507-L2592))

```cpp
// btr0btr.cc L2507-L2592
  /* 5. Move then the records to the new page */
  if (direction == FSP_DOWN) {
    /*          fputs("Split left\n", stderr); */

    if (false
#ifdef UNIV_ZIP_COPY
        || page_zip
#endif /* UNIV_ZIP_COPY */
        || !page_move_rec_list_start(new_block, block, move_limit,
                                     cursor->index, mtr)) {
      /* For some reason, compressing new_page failed,
      even though it should contain fewer records than
      the original page.  Copy the page byte for byte
      and then delete the records from both pages
      as appropriate.  Deleting will always succeed. */
      // ... (L2522-L2541 생략: 압축 페이지에서 옮기기 실패 시 바이트 복사 후 삭제)
    }

    left_block = new_block;
    right_block = block;

    if (!dict_table_is_locking_disabled(cursor->index->table)) {
      lock_update_split_left(right_block, left_block);
    }
  } else {
    /*          fputs("Split right\n", stderr); */

    if (false
#ifdef UNIV_ZIP_COPY
        || page_zip
#endif /* UNIV_ZIP_COPY */
        || !page_move_rec_list_end(new_block, block, move_limit, cursor->index,
                                   mtr)) {
      /* For some reason, compressing new_page failed,
      even though it should contain fewer records than
      the original page.  Copy the page byte for byte
      and then delete the records from both pages
      as appropriate.  Deleting will always succeed. */
      // ... (L2564-L2583 생략: 같은 처리)
    }

    left_block = block;
    right_block = new_block;

    if (!dict_table_is_locking_disabled(cursor->index->table)) {
      lock_update_split_right(right_block, left_block);
    }
  }
```

알맞은 절반에 넣고, 안 되면 재구성, 그래도 안 되면 처음부터 다시 나눈다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L2604-L2682 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L2604-L2682))

```cpp
// btr0btr.cc L2604-L2682
  /* 6. The split and the tree modification is now completed. Decide the
  page where the tuple should be inserted */

  if (insert_left) {
    insert_block = left_block;
  } else {
    insert_block = right_block;
  }

  /* 7. Reposition the cursor for insert and try insertion */
  page_cursor = btr_cur_get_page_cur(cursor);

  page_cur_search(insert_block, cursor->index, tuple, page_cursor);

  rec = page_cur_tuple_insert(page_cursor, tuple, cursor->index, offsets, heap,
                              mtr);

// ... (L2621-L2630 생략: 압축 페이지 검증)

  if (rec != nullptr) {
    goto func_exit;
  }

  /* 8. If insert did not fit, try page reorganization.
  For compressed pages, page_cur_tuple_insert() will have
  attempted this already. */

  if (page_cur_get_page_zip(page_cursor) ||
      !btr_page_reorganize(page_cursor, cursor->index, mtr)) {
    goto insert_failed;
  }

  rec = page_cur_tuple_insert(page_cursor, tuple, cursor->index, offsets, heap,
                              mtr);

  if (rec == nullptr) {
    /* The insert did not fit on the page: loop back to the
    start of the function for a new split */
  insert_failed:
    /* We play safe and reset the free bits for new_page */
    if (!cursor->index->is_clustered() &&
        !cursor->index->table->is_temporary()) {
      ibuf_reset_free_bits(new_block);
      ibuf_reset_free_bits(block);
    }

    n_iterations++;
    ut_ad(n_iterations < 2 || buf_block_get_page_zip(insert_block));
    ut_ad(!insert_will_fit);

    goto func_start;
  }

func_exit:
  /* Insert fit on the page: update the free bits for the
  left and right pages in the same mtr */

  if (!cursor->index->is_clustered() && !cursor->index->table->is_temporary() &&
      page_is_leaf(page)) {
    ibuf_update_free_bits_for_two_pages_low(left_block, right_block, mtr);
  }

  MONITOR_INC(MONITOR_INDEX_SPLIT);

  ut_ad(page_validate(buf_block_get_frame(left_block), cursor->index));
  ut_ad(page_validate(buf_block_get_frame(right_block), cursor->index));

  ut_ad(!rec || rec_offs_validate(rec, cursor->index, *offsets));
  return (rec);
}
```

순차 삽입을 알아채는 규칙이다. 직전 삽입 바로 뒤에 또 넣으면 오른쪽으로 자라는 중이라고 본다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L1705-L1749 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L1705-L1749))

```cpp
// btr0btr.cc L1705-L1749
    rec_t **split_rec) /*!< out: if split recommended,
                    the first record on upper half page,
                    or NULL if tuple to be inserted should
                    be first */
{
  page_t *page;
  rec_t *insert_point;

  page = btr_cur_get_page(cursor);
  insert_point = btr_cur_get_rec(cursor);

  /* We use eager heuristics: if the new insert would be right after
  the previous insert on the same page, we assume that there is a
  pattern of sequential inserts here. */

  if (page_header_get_ptr(page, PAGE_LAST_INSERT) == insert_point) {
    rec_t *next_rec;

    next_rec = page_rec_get_next(insert_point);

    if (page_rec_is_supremum(next_rec)) {
    split_at_new:
      /* Split at the new record to insert */
      *split_rec = nullptr;
    } else {
      rec_t *next_next_rec = page_rec_get_next(next_rec);
      if (page_rec_is_supremum(next_next_rec)) {
        goto split_at_new;
      }

      /* If there are >= 2 user records up from the insert
      point, split all but 1 off. We want to keep one because
      then sequential inserts can use the adaptive hash
      index, as they can do the necessary checks of the right
      search position just by looking at the records on this
      page. */

      *split_rec = next_next_rec;
    }

    return true;
  }

  return false;
}
```

트리 구조를 고치는 부분이다. 부모에 윗쪽 절반을 가리키는 노드 포인터를 넣고, 형제 링크를 다시 잇는다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L2096-L2152 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L2096-L2152))

```cpp
// btr0btr.cc L2096-L2152
  level = btr_page_get_level(buf_block_get_frame(block));
  ut_ad(level == btr_page_get_level(buf_block_get_frame(new_block)));

  /* Build the node pointer (= node key and page address) for the upper
  half */

  node_ptr_upper =
      dict_index_build_node_ptr(index, split_rec, upper_page_no, heap, level);

  /* Insert it next to the pointer to the lower half. Note that this
  may generate recursion leading to a split on the higher level. */

  btr_insert_on_non_leaf_level(flags, index, level + 1, node_ptr_upper,
                               UT_LOCATION_HERE, mtr);

  /* Free the memory heap */
  mem_heap_free(heap);

  /* Update page links of the level */

  if (prev_block) {
// ... (L2117-L2120 생략: 디버그 검증)

    btr_page_set_next(buf_block_get_frame(prev_block),
                      buf_block_get_page_zip(prev_block), lower_page_no, mtr);
  }

  if (next_block) {
// ... (L2127-L2130 생략: 디버그 검증)

    btr_page_set_prev(buf_block_get_frame(next_block),
                      buf_block_get_page_zip(next_block), upper_page_no, mtr);
  }

  if (direction == FSP_DOWN) {
    /* lower_page is new */
    btr_page_set_prev(lower_page, lower_page_zip, prev_page_no, mtr);
  } else {
    ut_ad(btr_page_get_prev(lower_page, mtr) == prev_page_no);
  }

  btr_page_set_next(lower_page, lower_page_zip, upper_page_no, mtr);
  btr_page_set_prev(upper_page, upper_page_zip, lower_page_no, mtr);

  if (direction != FSP_DOWN) {
    /* upper_page is new */
    btr_page_set_next(upper_page, upper_page_zip, next_page_no, mtr);
  } else {
    ut_ad(btr_page_get_next(upper_page, mtr) == next_page_no);
  }
}
```

부모에 넣는 일은 부모 층에서의 일반 삽입이다. 부모도 가득 차면 여기서 다시 분할이 일어난다.

`storage` / `innobase` / `btr` / `btr0btr.cc` L1967-L2000 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0btr.cc#L1967-L2000))

```cpp
// btr0btr.cc L1967-L2000
  if (!dict_index_is_spatial(index)) {
    if (index->table->is_intrinsic()) {
      btr_cur_search_to_nth_level_with_no_latch(
          index, level, tuple, PAGE_CUR_LE, &cursor, __FILE__, __LINE__, mtr);
    } else {
      btr_cur_search_to_nth_level(index, level, tuple, PAGE_CUR_LE,
                                  BTR_CONT_MODIFY_TREE, &cursor, 0,
                                  location.filename, location.line, mtr);
    }
  // ... (L1976-L1985 생략: 공간 인덱스 분기)
  }

  ut_ad(cursor.flag == BTR_CUR_BINARY);

  err = btr_cur_optimistic_insert(
      flags | BTR_NO_LOCKING_FLAG | BTR_KEEP_SYS_FLAG | BTR_NO_UNDO_LOG_FLAG,
      &cursor, &offsets, &heap, tuple, &rec, &dummy_big_rec, nullptr, mtr);

  if (err == DB_FAIL) {
    err = btr_cur_pessimistic_insert(
        flags | BTR_NO_LOCKING_FLAG | BTR_KEEP_SYS_FLAG | BTR_NO_UNDO_LOG_FLAG,
        &cursor, &offsets, &heap, tuple, &rec, &dummy_big_rec, nullptr, mtr);
    ut_a(err == DB_SUCCESS);
  }

```

## 동작 흐름

```text
 L2341  공간 인덱스면 rtr_page_split_and_insert 로
 L2350  n_uniq = 트리 안에서의 유니크 필드 수
 L2351  func_start:
 L2375  btr_insert_into_right_sibling           커서가 페이지 마지막 레코드이고 오른쪽 형제가 있으면
          L2238  형제의 맨 앞에 넣어 본다
          L2264  성공하면 부모의 형제 노드 포인터를 지우고
          L2277  새 첫 키로 다시 넣는다 -> return (분할 없음)

 1. 자를 곳 (split_rec = 윗쪽 절반의 첫 레코드, nullptr 이면 튜플이 윗쪽 첫 레코드)
 L2388  btr_page_get_split_rec   FSP_UP     두 번째 이상 시도. 튜플이 확실히 들어가는 곳
 L2397  split_rec_to_right       FSP_UP     오른쪽 순차 삽입. hint = page_no + 1
 L2401  split_rec_to_left        FSP_DOWN   왼쪽 순차 삽입. hint = page_no - 1
 L2405  page_get_middle_rec      FSP_UP     그 밖. 가운데
 L2416    레코드가 하나뿐이면 튜플이 더 작은지로 결정

 2. L2424  btr_page_alloc(hint_page_no, direction, level)   같은 level 의 새 페이지
    L2434  btr_page_create
 3. L2442  first_rec = move_limit = split_rec
    L2447  insert_left = 튜플 < split_rec
    L2461  split_rec 가 없으면 튜플 자체를 레코드로 만들어 first_rec 로 쓴다
 4. L2474  btr_attach_half_pages                           트리 구조 먼저
          L2103  node_ptr = (first_rec 의 키, 윗쪽 페이지 번호)
          L2108  btr_insert_on_non_leaf_level(level + 1)  --> 부모에 [03], 안 되면 [07]
          L2122-L2148  prev.next, next.prev, lower <-> upper 링크
    L2483  insert_will_fit = 넣을 절반에 튜플이 들어가는가
    L2497  리프이고 들어가면 index->lock 해제 (L2500)
 5. L2508  FSP_DOWN  page_move_rec_list_start(새 페이지 <- move_limit 앞쪽)
                     left = 새 페이지, right = 원래 페이지, lock_update_split_left
    L2550  FSP_UP    page_move_rec_list_end(새 페이지 <- move_limit 부터 끝)
                     left = 원래 페이지, right = 새 페이지, lock_update_split_right
 6. L2607  insert_block = insert_left ? left : right
 7. L2616  page_cur_search(insert_block, tuple)     커서 다시 세우기
    L2618  page_cur_tuple_insert                    --> [05] [06]
 8. L2641  실패면 재구성 후 다시 (L2645)
    L2651  그래도 실패면 insert_failed: n_iterations++, goto func_start (L2663)
 L2675  MONITOR_INC(MONITOR_INDEX_SPLIT)
```

분할 지점을 고르는 세 규칙이 트리 모양을 결정한다. 순차 삽입에서 가운데를 자르면 왼쪽 절반은 영영 반만 찬 채로 남는다. 그래서 새 레코드 자리에서 자른다.

```text
 (가) 가운데 분할 (무작위 삽입)          page_get_middle_rec (L2415)

   [10 20 30 40 50 60]  + 35
   ->  [10 20 30 35]  [40 50 60]         (자르는 자리는 예시)
        원래 페이지    새 페이지 (FSP_UP)

 (나) 오른쪽 순차 삽입                   split_rec_to_right (L1705)
      PAGE_LAST_INSERT == 커서 레코드이고, 뒤로 사용자 레코드가 1개 이하

   [1 2 3 4 5 6]  + 7   (6 이 직전 삽입)
   ->  [1 2 3 4 5 6]  [7]                split_rec = nullptr, 튜플이 새 페이지의 첫 레코드
        원래 페이지는 꽉 찬 채로 두고 새 페이지를 비워 다음 8, 9, ... 를 받는다

      뒤로 2개 이상 남아 있으면 (L1729-L1743)
   [1 2 3 4 5 8 9]  + 6  (5 가 직전 삽입)
   ->  [1 2 3 4 5 6 8]  [9]              next_next_rec 부터 옮긴다. 하나는 남겨 둔다
                                          (주석: 남은 하나로 AHI 가 다음 순차 삽입을 확인한다)

 (다) 왼쪽 순차 삽입 (키가 줄어드는 방향) split_rec_to_left (L1668)
      PAGE_LAST_INSERT == 커서 다음 레코드
   FSP_DOWN: 새 페이지가 왼쪽에 생기고, 원래 페이지의 앞쪽 레코드가 그리로 간다
```

```text
 트리 구조 변경 (FSP_UP, 리프 P5 를 나눠 새 페이지 P9 를 만들 때)

 전                                        후
   부모  ... (10, P5) (50, P6) ...           부모  ... (10, P5) (30, P9) (50, P6) ...
                                                          ^ L2108 btr_insert_on_non_leaf_level
   P4 <-> P5 <-> P6                           P4 <-> P5 <-> P9 <-> P6
                                                     L2143 P5.next = P9
                                                     L2144 P9.prev = P5
                                                     L2148 P9.next = P6
                                                     L2132 P6.prev = P9

 이 모든 변경과 레코드 이동이 mtr 하나에 들어간다. 부모 쪽 변경이 먼저(4), 레코드 이동이 나중(5)
```

```text
 래치를 일찍 놓는 조건 (L2497-L2501)

 읽기 전용 모드가 아님, 내부 임시 테이블이 아님, 온라인 DDL 중이 아님
 그리고 리프 페이지이고 insert_will_fit
   -> mtr->memo_release(index->lock)
      부모 수정(4)은 이미 끝났고, 남은 레코드 이동(5)과 삽입(7)은 두 리프 안의 일이다
      루트 블록 래치는 놓지 않는다 (L2503-L2504 주석: 세그먼트 헤더가 있고 이미 고쳤다)
```

## 결과가 쓰이는 곳

```text
 반환한 rec
      --> [07] 이 lock_update_insert 와 AHI 를 고치고 [01] 로
 lock_update_split_left / _right, lock_update_split_point
      --> 옮겨진 레코드의 잠금과 gap 잠금이 새 페이지로 따라간다 ([레코드 잠금과 교착])
 부모의 새 노드 포인터와 형제 링크
      --> 다음 [02] 탐색이 새 페이지로 내려가고, 범위 스캔이 FIL_PAGE_NEXT 로 넘어간다
 MONITOR_INDEX_SPLIT
      --> INNODB_METRICS 의 index_page_splits (srv0mon.cc L1063)
```

## 다루지 않는 것

압축 페이지의 바이트 복사 경로와 반복 분할(`n_iterations`, `page_zip_copy_recs`), `btr_page_get_split_rec` 의 크기 계산, `btr_page_alloc` 의 extent 와 hint 처리, 오른쪽 형제 삽입 뒤 부모 정리(`btr_cur_pessimistic_delete`, `btr_cur_compress_if_useful`), 공간 인덱스 분할은 곁가지라 줄만 적었다.
