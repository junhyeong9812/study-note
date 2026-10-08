# row_sel_build_prev_vers_for_mysql

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**옛 버전을 담을 힙을 비우고 [08] 로 넘기는 얇은 문이다.** 이 함수가 하는 일은 `prebuilt->old_vers_heap` 하나를 관리하는 것뿐이다. 레코드마다 새 힙을 만들지 않고, 있으면 `mem_heap_empty` 로 비워서 다시 쓴다. 그래서 [02] 가 받은 옛 버전(`old_vers`)은 **다음 레코드의 옛 버전을 만들 때까지만** 유효하다. 부르는 곳은 둘이다. 클러스터드 인덱스를 읽을 때 [02] 가 직접 부르고, 세컨더리 인덱스로 읽다가 클러스터드 레코드를 찾았을 때 `Row_sel_get_clust_rec_for_mysql` 이 부른다.

## 위치

`storage` / `innobase` / `row` / `row0sel.cc` L3079-L3099 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L3079-L3099))

## 실제 코드

함수 전체다. 반환값 `old_vers` 가 nullptr 이면 그 행은 read view 시점에 아직 없었다는 뜻이다.

`storage` / `innobase` / `row` / `row0sel.cc` L3063-L3099 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L3063-L3099))

```cpp
// row0sel.cc L3063-L3099
/** Builds a previous version of a clustered index record for a consistent read
@param[in]      read_view       read view
@param[in]      clust_index     clustered index
@param[in]      prebuilt        prebuilt struct
@param[in]      rec             record in clustered index
@param[in,out]  offsets         offsets returned by
                                rec_get_offsets(rec, clust_index)
@param[in,out]  offset_heap     memory heap from which the offsets are
                                allocated
@param[out]     old_vers        old version, or NULL if the record does not
                                exist in the view: i.e., it was freshly
                                inserted afterwards
@param[out]     vrow            dtuple to hold old virtual column data
@param[in]      mtr             the mini-transaction context.
@param[in,out]  lob_undo        Undo information for BLOBs.
@return DB_SUCCESS or error code */
[[nodiscard]] static dberr_t row_sel_build_prev_vers_for_mysql(
    ReadView *read_view, dict_index_t *clust_index, row_prebuilt_t *prebuilt,
    const rec_t *rec, ulint **offsets, mem_heap_t **offset_heap,
    rec_t **old_vers, const dtuple_t **vrow, mtr_t *mtr,
    lob::undo_vers_t *lob_undo) {
  DBUG_TRACE;

  dberr_t err;

  if (prebuilt->old_vers_heap) {
    mem_heap_empty(prebuilt->old_vers_heap);
  } else {
    prebuilt->old_vers_heap = mem_heap_create(200, UT_LOCATION_HERE);
  }

  err = row_vers_build_for_consistent_read(
      rec, mtr, clust_index, offsets, read_view, offset_heap,
      prebuilt->old_vers_heap, old_vers, vrow, lob_undo);

  return err;
}
```

두 번째 호출자다. 세컨더리 인덱스로 찾은 클러스터드 레코드를 판정하는데, 같은 클러스터드 레코드를 연달아 만나면 직전에 만든 옛 버전을 캐시에서 꺼내 쓴다.

`storage` / `innobase` / `row` / `row0sel.cc` L3298-L3350 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L3298-L3350))

```cpp
// row0sel.cc L3298-L3350
  } else {
    /* This is a non-locking consistent read: if necessary, fetch
    a previous version of the record */

    old_vers = nullptr;

    /* If the isolation level allows reading of uncommitted data,
    then we never look for an earlier version */

    if (trx->isolation_level > TRX_ISO_READ_UNCOMMITTED &&
        !lock_clust_rec_cons_read_sees(clust_rec, clust_index, *offsets,
                                       trx_get_read_view(trx))) {
      if (clust_rec != cached_clust_rec) {
        /* The following call returns 'offsets' associated with 'old_vers' */
        err = row_sel_build_prev_vers_for_mysql(
            trx->read_view, clust_index, prebuilt, clust_rec, offsets,
            offset_heap, &old_vers, vrow, mtr, lob_undo);

        if (err != DB_SUCCESS) {
          goto err_exit;
        }
        cached_clust_rec = clust_rec;
        cached_old_vers = old_vers;
      } else {
        err = DB_SUCCESS;
        old_vers = cached_old_vers;

        // ... (L3325-L3342 생략: 캐시 적중 시 디버그 검사와 offsets 재계산)
      }

      if (old_vers == nullptr) {
        goto err_exit;
      }

      clust_rec = old_vers;
    }
```

## 동작 흐름

```text
 row_sel_build_prev_vers_for_mysql(read_view, clust_index, prebuilt, rec, ...)

 L3088  prebuilt->old_vers_heap 이 있으면 mem_heap_empty   (이전 레코드의 옛 버전이 사라진다)
 L3091  없으면 mem_heap_create(200)
 L3094  [08] row_vers_build_for_consistent_read(rec, mtr, clust_index, offsets, read_view,
                                                offset_heap, old_vers_heap, old_vers, vrow, lob_undo)
 L3098  err 를 그대로 돌려준다
```

메모리는 세 힙에 나뉜다. 최종 옛 버전은 `old_vers_heap` 에, 그 열 위치표(`offsets`)는 호출자의 `offset_heap` 에, 중간 버전은 [08] 이 잠깐 만든 힙에 놓인다.

```text
 메모리의 주인

 prebuilt->old_vers_heap   [08] 이 최종 옛 버전을 rec_copy 하는 곳 (in_heap)
                           다음 호출의 L3089 에서 비워진다
 *offset_heap              old_vers 의 rec_get_offsets 결과. [02] 의 heap
 [08] 안의 heap            중간 버전들. [08] 이 버전 하나 넘어갈 때마다 만들고 버린다

 그래서 [02] 가 받은 old_vers 는 다음 옛 버전을 만들기 전까지만 쓸 수 있다
```

```text
 두 호출자

 호출 위치                 상황                                    캐시
 row0sel.cc L5341 ([02])   클러스터드 인덱스를 직접 읽는다          없음
 row0sel.cc L3312          세컨더리 -> 클러스터드 조회               cached_clust_rec / cached_old_vers
                           (Row_sel_get_clust_rec_for_mysql)        같은 클러스터드 레코드면 재사용 (L3321)
                           옛 버전이 nullptr 이면 이 세컨더리 행은 결과에서 빠진다 (L3345)
```

## 결과가 쓰이는 곳

```text
 old_vers
      --> nullptr        [02] 가 next_rec 로 건너뛴다 (그 시점에 행이 없었다)
      --> 옛 버전        [02] 의 rec 가 이것으로 바뀌고, delete-mark 검사와 행 복사가 이어진다
 err (DB_MISSING_HISTORY 등)
      --> [02] 가 lock_wait_or_error 로 간다
```

## 다루지 않는 것

가상 열 값(`vrow`)을 옛 버전에 맞추는 일과 LOB 의 부분 갱신 undo(`lob::undo_vers_t`)는 이 흐름의 곁가지라 매개변수 이름만 적었다. 세컨더리 레코드와 옛 클러스터드 버전의 키 비교(`row_sel_sec_rec_is_for_clust_rec`)는 [02](../02_row_search_mvcc/README.md)의 그림에 있다.
