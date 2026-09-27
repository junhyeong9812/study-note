# btr_cur_pessimistic_insert

상위: [B+Tree 삽입과 분할](../README.md)

**페이지 하나로는 안 될 때 트리 구조를 바꿔서라도 넣는 삽입이다.** 호출자가 `BTR_MODIFY_TREE` 로 index->lock(SX)과 리프, 좌우 형제의 X 래치를 이미 쥐고 있어야 한다. 잠금과 undo([04])를 먼저 처리하고, 분할에 쓸 **파일 공간(extent)을 미리 예약**한 뒤, 커서 페이지가 루트면 [09] 루트 승격, 아니면 [08] 페이지 분할로 간다. 분할은 되돌릴 수 없는 연산이라 공간 예약이 앞에 온다.

## 위치

`storage` / `innobase` / `btr` / `btr0cur.cc` L2930-L3070 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2930-L3070))

## 실제 코드

`storage` / `innobase` / `btr` / `btr0cur.cc` L2951-L3070 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2951-L3070))

```cpp
// btr0cur.cc L2951-L3070
  dict_index_t *index = cursor->index;
  big_rec_t *big_rec_vec = nullptr;
  dberr_t err;
  bool inherit = false;
  bool success;
  ulint n_reserved = 0;

  ut_ad(dtuple_check_typed(entry));

  *big_rec = nullptr;

  ut_ad(mtr_memo_contains_flagged(mtr, dict_index_get_lock(cursor->index),
                                  MTR_MEMO_X_LOCK | MTR_MEMO_SX_LOCK) ||
        cursor->index->table->is_intrinsic());
  ut_ad(mtr_is_block_fix(mtr, btr_cur_get_block(cursor), MTR_MEMO_PAGE_X_FIX,
                         cursor->index->table));
  ut_ad(!dict_index_is_online_ddl(index) || index->is_clustered() ||
        (flags & BTR_CREATE_FLAG));

  cursor->flag = BTR_CUR_BINARY;

  /* Check locks and write to undo log, if specified */

  err = btr_cur_ins_lock_and_undo(flags, cursor, entry, thr, mtr, &inherit);

  if (err != DB_SUCCESS) {
    return (err);
  }

  if (!(flags & BTR_NO_UNDO_LOG_FLAG) || index->table->is_intrinsic()) {
    /* First reserve enough free space for the file segments
    of the index tree, so that the insert will not fail because
    of lack of space */

    ulint n_extents = cursor->tree_height / 16 + 3;

    success = fsp_reserve_free_extents(&n_reserved, index->space, n_extents,
                                       FSP_NORMAL, mtr);
    if (!success) {
      return (DB_OUT_OF_FILE_SPACE);
    }
  }

  if (page_zip_rec_needs_ext(rec_get_converted_size(index, entry),
                             dict_table_is_comp(index->table),
                             dtuple_get_n_fields(entry),
                             // ... (L2997-L3016 생략: 외부 저장 열 변환과 실패 처리)

  if (dict_index_get_page(index) ==
      btr_cur_get_block(cursor)->page.id.page_no()) {
    /* The page is the root page */
    *rec = btr_root_raise_and_insert(flags, cursor, offsets, heap, entry, mtr);
  } else {
    *rec = btr_page_split_and_insert(flags, cursor, offsets, heap, entry, mtr);
  }

  if (!*rec) {
    return DB_OUT_OF_FILE_SPACE;
  }

  ut_ad(page_rec_get_next(btr_cur_get_rec(cursor)) == *rec ||
        dict_index_is_spatial(index));

  if (!(flags & BTR_NO_LOCKING_FLAG)) {
    ut_ad(!index->table->is_temporary());
    if (dict_index_is_spatial(index)) {
      /* Do nothing */
    } else {
      /* The cursor might be moved to the other page
      and the max trx id field should be updated after
      the cursor was fixed. */
      if (!index->is_clustered()) {
        page_update_max_trx_id(btr_cur_get_block(cursor),
                               btr_cur_get_page_zip(cursor),
                               thr_get_trx(thr)->id, mtr);
      }
      if (!page_rec_is_infimum(btr_cur_get_rec(cursor)) ||
          btr_page_get_prev(buf_block_get_frame(btr_cur_get_block(cursor)),
                            mtr) == FIL_NULL) {
        /* split and inserted need to call
        lock_update_insert() always. */
        inherit = true;
      }
    }
  }

  if (!index->disable_ahi) {
    btr_search_update_hash_on_insert(cursor);
  }
  if (inherit && !(flags & BTR_NO_LOCKING_FLAG)) {
    lock_update_insert(btr_cur_get_block(cursor), *rec);
  }

  if (n_reserved > 0) {
    fil_space_release_free_extents(index->space, n_reserved);
  }

  *big_rec = big_rec_vec;

  return (DB_SUCCESS);
}
```

## 동작 흐름

```text
 L2962  assert: index->lock 을 X 또는 SX 로 쥐고 있다
 L2965  assert: 커서 페이지를 X 로 쥐고 있다
 L2970  cursor->flag = BTR_CUR_BINARY
 L2974  [04] btr_cur_ins_lock_and_undo           DB_LOCK_WAIT 등이면 그대로 반환

 L2980  undo 를 쓰는 삽입이면 (또는 내부 임시 테이블)
 L2985    n_extents = tree_height / 16 + 3
 L2987    fsp_reserve_free_extents               실패면 DB_OUT_OF_FILE_SPACE (L2990)
 L2994  레코드가 너무 크면 dtuple_convert_big_rec

 L3018  커서 페이지 == 인덱스 루트 페이지
 L3021    yes  [09] btr_root_raise_and_insert
 L3023    no   [08] btr_page_split_and_insert
 L3026  nullptr 이면 DB_OUT_OF_FILE_SPACE      새 페이지를 얻지 못함

 L3033  잠금을 쓰는 삽입이면
 L3041    세컨더리면 page_update_max_trx_id     커서가 다른 페이지로 옮겨졌을 수 있다
 L3046    커서가 infimum 이 아니거나 왼쪽 형제가 없으면 inherit = true
 L3056  AHI 갱신
 L3059  inherit 면 lock_update_insert
 L3063  예약한 extent 반납
 L3069  return DB_SUCCESS
```

루트 판단은 페이지 번호 하나로 한다. 커서 페이지 번호를 인덱스 객체가 들고 있는 루트 페이지 번호(`dict_index_get_page`)와 비교하고, [09] 의 루트 승격도 그 번호를 바꾸지 않는다.

```text
 어느 쪽으로 가나

 dict_index_get_page(index) == 커서 페이지 번호 (L3018)
   yes  [09] 루트 승격 + 분할. 트리 높이 +1
   no   [08] 분할. 부모에 노드 포인터를 넣는다
        부모도 차면 btr_insert_on_non_leaf_level 이 부모 층에서 다시 [03] -> [07]
        그 재귀가 루트까지 올라가면 거기서 yes 쪽이 되어 높이가 +1
```

```text
 extent 예약 (L2985)

 tree_height  n_extents
 1            3
 2            3
 3            3
 16           4
```

## 결과가 쓰이는 곳

```text
 *rec
      --> [01] 이 mtr.commit (L2620). index->lock 은 [08] 에서 먼저 풀렸을 수 있다
 DB_OUT_OF_FILE_SPACE
      --> [행 쓰기] 06 row_mysql_handle_errors 가 이 행을 savepoint 로 되돌린다
 lock_update_insert
      --> 새 레코드가 다음 레코드의 gap 잠금을 물려받는다 ([레코드 잠금과 교착])
```

## 다루지 않는 것

extent 예약의 내부(`fsp_reserve_free_extents`, `FSP_NORMAL`), 외부 저장 열 변환, 공간 인덱스의 분할(`rtr_page_split_and_insert`), 적응형 해시 갱신은 곁가지다. 파일 공간 관리는 [테이블스페이스와 페이지 레이아웃](../../../structure/tablespace-page/README.md) 쪽이다.
