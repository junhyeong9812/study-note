# btr_cur_optimistic_insert

상위: [B+Tree 삽입과 분할](../README.md)

**트리 구조를 건드리지 않고 커서가 선 페이지 하나 안에서만 삽입을 끝내려는 시도다.** 먼저 레코드 크기와 페이지의 남은 공간을 비교해 들어갈 수 없으면 아무것도 바꾸지 않고 `DB_FAIL` 을 돌려준다. 들어갈 수 있으면 [04] 로 잠금과 undo 를 처리하고 [05] 로 레코드를 넣는다. 첫 삽입이 실패하면 페이지를 재구성(`btr_page_reorganize`)해 흩어진 빈 공간을 모은 뒤 한 번 더 넣는다. 볼거리는 **"공간이 있는데도 일부러 실패하는" 경우**다. 클러스터드 리프에서 순차 삽입이 이어지면 나중의 UPDATE 를 위해 페이지의 1/16 을 남겨 두고 분할로 넘긴다.

## 위치

`storage` / `innobase` / `btr` / `btr0cur.cc` L2662-L2923 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2662-L2923))

## 실제 코드

레코드 크기를 재고, 너무 크면 긴 열을 페이지 밖(외부 저장)으로 뺀다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L2717-L2733 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2717-L2733))

```cpp
// btr0cur.cc L2717-L2733
  auto leaf = page_is_leaf(page);

  /* Calculate the record size when entry is converted to a record */
  rec_size = rec_get_converted_size(index, entry);

  if (page_zip_rec_needs_ext(rec_size, page_is_comp(page),
                             dtuple_get_n_fields(entry), page_size)) {
    /* The record is so big that we have to store some fields
    externally on separate database pages */
    big_rec_vec = dtuple_convert_big_rec(index, nullptr, entry);

    if (UNIV_UNLIKELY(big_rec_vec == nullptr)) {
      return (DB_TOO_BIG_RECORD);
    }

    rec_size = rec_get_converted_size(index, entry);
  }
```

넣을 수 없는 조건들이다. 모두 `fail` 로 가서 `DB_FAIL` 을 돌려준다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L2743-L2792 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2743-L2792))

```cpp
// btr0cur.cc L2743-L2792
  LIMIT_OPTIMISTIC_INSERT_DEBUG(page_get_n_recs(page), goto fail);

  if (leaf && page_size.is_compressed() &&
      (page_get_data_size(page) + rec_size >=
       dict_index_zip_pad_optimal_page_size(index))) {
    /* If compression padding tells us that insertion will
    result in too packed up page i.e.: which is likely to
    cause compression failure then don't do an optimistic
    insertion. */
  fail:
    err = DB_FAIL;

    /* prefetch siblings of the leaf for the pessimistic
    operation, if the page is leaf. */
    if (page_is_leaf(page)) {
      btr_cur_prefetch_siblings(block);
    }
  fail_err:

    if (big_rec_vec) {
      dtuple_convert_back_big_rec(entry, big_rec_vec);
    }

    return (err);
  }

  ulint max_size = page_get_max_insert_size_after_reorganize(page, 1);

  if (page_has_garbage(page)) {
    if ((max_size < rec_size || max_size < BTR_CUR_PAGE_REORGANIZE_LIMIT) &&
        page_get_n_recs(page) > 1 &&
        page_get_max_insert_size(page, 1) < rec_size) {
      goto fail;
    }
  } else if (max_size < rec_size) {
    goto fail;
  }

  /* If there have been many consecutive inserts to the
  clustered index leaf page of an uncompressed table, check if
  we have to split the page to reserve enough free space for
  future updates of records. */

  if (leaf && !page_size.is_compressed() && index->is_clustered() &&
      page_get_n_recs(page) >= 2 &&
      dict_index_get_space_reserve() + rec_size > max_size &&
      (btr_page_get_split_rec_to_right(cursor, &dummy) ||
       btr_page_get_split_rec_to_left(cursor, &dummy))) {
    goto fail;
  }
```

실제 삽입이다. 잠금과 undo 가 먼저이고, 그다음 페이지에 쓴다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L2805-L2842 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2805-L2842))

```cpp
// btr0cur.cc L2805-L2842
  /* Now, try the insert */
  {
    const rec_t *page_cursor_rec = page_cur_get_rec(page_cursor);

    if (index->table->is_intrinsic()) {
      *rec = page_cur_tuple_direct_insert(page_cursor, entry, index, mtr,
                                          rec_size);
    } else {
      /* Check locks and write to the undo log,
      if specified */
      err = btr_cur_ins_lock_and_undo(flags, cursor, entry, thr, mtr, &inherit);

      if (err != DB_SUCCESS) {
        goto fail_err;
      }

      // ... (L2821-L2835 생략: 디버그 동기화 지점)

      *rec =
          page_cur_tuple_insert(page_cursor, entry, index, offsets, heap, mtr);
    }

    reorg = page_cursor_rec != page_cur_get_rec(page_cursor);
  }
```

첫 시도가 실패하면 재구성하고 다시 넣는다. 끝에서 AHI 와 잠금 표를 고친다.

`storage` / `innobase` / `btr` / `btr0cur.cc` L2844-L2893 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/btr/btr0cur.cc#L2844-L2893))

```cpp
// btr0cur.cc L2844-L2893
  if (*rec) {
  } else if (page_size.is_compressed()) {
    ut_ad(!index->table->is_temporary());
    /* Reset the IBUF_BITMAP_FREE bits, because
    page_cur_tuple_insert() will have attempted page
    reorganize before failing. */
    if (leaf && !index->is_clustered()) {
      ibuf_reset_free_bits(block);
    }

    goto fail;
  } else {
    /* For intrinsic table we take a consistent path
    to re-organize using pessimistic path. */
    if (index->table->is_intrinsic()) {
      goto fail;
    }

    ut_ad(!reorg);

    /* If the record did not fit, reorganize */
    if (!btr_page_reorganize(page_cursor, index, mtr)) {
      ut_d(ut_error);
      ut_o(goto fail);
    }

    ut_ad(page_get_max_insert_size(page, 1) == max_size);

    reorg = true;

    *rec = page_cur_tuple_insert(page_cursor, entry, index, offsets, heap, mtr);

    if (UNIV_UNLIKELY(!*rec)) {
      ib::fatal(UT_LOCATION_HERE, ER_IB_MSG_44)
          << "Cannot insert tuple " << *entry << "into index " << index->name
          << " of table " << index->table->name << ". Max size: " << max_size;
    }
  }

  if (!index->disable_ahi) {
    if (!reorg && leaf && (cursor->flag == BTR_CUR_HASH)) {
      btr_search_update_hash_node_on_insert(cursor);
    } else {
      btr_search_update_hash_on_insert(cursor);
    }
  }

  if (!(flags & BTR_NO_LOCKING_FLAG) && inherit) {
    lock_update_insert(block, *rec);
  }
```

## 동작 흐름

```text
 L2717  leaf = page_is_leaf(page)
 L2720  rec_size = 엔트리를 레코드로 바꾼 크기
 L2722  한 페이지에 넣기엔 크면 dtuple_convert_big_rec   긴 열을 외부 저장 대상으로 뺀다
 L2729    뺄 수도 없으면 DB_TOO_BIG_RECORD

 L2745  압축 리프이고 패딩 기준을 넘으면 fail
 L2752  fail:  err = DB_FAIL
 L2758         리프면 btr_cur_prefetch_siblings  좌우 형제를 미리 비동기로 읽어 둔다
                                                   (곧 올 pessimistic 삽입이 형제를 X 로 잡는다)
 L2769  max_size = 재구성하면 얻을 최대 삽입 크기
 L2771  페이지에 삭제된 레코드의 빈 공간(garbage)이 있으면
 L2772    재구성해도 모자라거나, 재구성 한계보다 작고 지금 당장도 모자라면 fail
 L2777  garbage 가 없으면 max_size < rec_size 일 때 fail
 L2786  클러스터드 리프, 레코드 2개 이상, 남은 공간 < 페이지/16 + rec_size,
        그리고 순차 삽입 모양(split_rec_to_right 또는 _left)이면 fail
                                                   (dict_index_get_space_reserve = UNIV_PAGE_SIZE / 16)

 L2812  보통 테이블 (내부 임시 테이블은 L2810 직접 삽입)
 L2815    [04] btr_cur_ins_lock_and_undo            DB_LOCK_WAIT 면 fail_err 로 (페이지 무변경)
 L2837    [05] page_cur_tuple_insert                --> [06]
 L2841  reorg = 커서가 움직였나 (압축 페이지에서 재구성이 일어났는지)
 L2844  성공
 L2845  압축 페이지 실패면 fail
 L2865  실패면 btr_page_reorganize (레코드를 새로 채워 garbage 제거)
 L2874    다시 page_cur_tuple_insert. 또 실패면 ib::fatal (L2877)
                                                   (앞의 max_size 검사로 들어갈 수 있어야 했다)
 L2883  AHI 갱신
 L2891  inherit 면 lock_update_insert(block, rec)   다음 레코드의 gap 잠금을 새 레코드가 물려받는다
 L2895  세컨더리 리프면 change buffer 비트맵의 여유 비트 갱신
 L2922  return DB_SUCCESS
```

`DB_FAIL` 은 오류가 아니라 신호다. 실패로 돌아가는 모든 경로는 [04] 보다 앞에 있으므로, 실패한 시도는 잠금도 undo 도 남기지 않는다.

```text
 fail 로 가는 곳과 [04] 의 위치

 L2729  DB_TOO_BIG_RECORD   오류
 L2745  fail                압축 패딩
 L2772  fail                garbage 있고 모자람
 L2778  fail                모자람
 L2791  fail                업데이트 여유 1/16
 ----------------------------------------------  여기까지 페이지, 잠금, undo 모두 그대로
 L2815  [04]                잠금 + undo. DB_LOCK_WAIT 면 fail_err (undo 전이라 아무것도 안 남음)
 L2837  [05]                삽입
 L2854  fail                압축 페이지 삽입 실패. [04] 뒤라 undo 는 이미 기록됨
```

마지막 줄만 [04] 뒤의 실패다. 압축 페이지가 아니면 L2865 의 재구성 뒤 재시도가 있고, 그것마저 실패하면 `ib::fatal` 이다.

```text
 순차 삽입 판정 (btr_page_get_split_rec_to_right, btr0btr.cc L1705)

 PAGE_LAST_INSERT == 커서 레코드   직전 삽입 바로 뒤에 또 넣는다 = 오른쪽으로 자라는 중

   infimum -> [1] -> [2] -> [3] -> supremum
                                ^ PAGE_LAST_INSERT, 커서
   다음 키 4 는 [3] 뒤에 들어간다

 이 모양에서 남은 공간이 페이지/16 보다 적으면 여기서 멈추고 분할로 보낸다
 분할([08])도 같은 판정으로 "새 레코드 자리에서 자르기"를 고른다
```

## 결과가 쓰이는 곳

```text
 *rec (새 레코드)
      --> [01] 이 mtr.commit 전에 온라인 DDL 로그를 쓰고(L2617) 커밋한다
 DB_FAIL
      --> LEAF 모드면 [행 쓰기] 10 이 TREE 로 재시도, TREE 모드면 [01] L2592 가 [07] 로
 *big_rec
      --> [01] 이 mtr 을 커밋한 뒤 외부 페이지에 긴 열을 쓴다
 lock_update_insert
      --> 레코드 잠금 표에서 새 레코드의 heap_no 에 gap 잠금이 복사된다 ([레코드 잠금과 교착])
```

## 다루지 않는 것

압축 페이지(`page_zip_*`, 압축 패딩 `dict_index_zip_pad_optimal_page_size`), 외부 저장 열 변환(`dtuple_convert_big_rec`), 내부 임시 테이블의 직접 삽입(`page_cur_tuple_direct_insert`), 적응형 해시 인덱스 갱신, change buffer 비트맵(`ibuf_update_free_bits_*`), 재구성(`btr_page_reorganize`)의 내부는 곁가지다.
