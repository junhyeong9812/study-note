# row_vers_build_for_consistent_read

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**undo 체인을 거슬러 오르는 루프 그 자체다.** 시작점은 페이지 위의 최신 버전이고, 한 바퀴마다 [09] 로 undo 레코드 하나를 적용해 바로 앞 버전을 만들고, 그 버전의 `DB_TRX_ID` 를 [06] 에 묻는다. 보이면 그 버전을 호출자의 힙으로 복사하고 끝낸다. 앞 버전이 없으면(처음 넣은 버전에 닿으면) nullptr 로 끝낸다. 중간에 purge 가 이미 지웠을 수 있는 undo 를 만나면 `DB_MISSING_HISTORY` 로 끝낸다. 루프 내내 호출자의 mtr 이 최신 버전이 있는 페이지의 래치를 쥐고 있어서, 체인의 꼭대기가 그동안 바뀌지 않는다.

## 위치

`storage` / `innobase` / `row` / `row0vers.cc` L1249-L1342 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0vers.cc#L1249-L1342))

## 실제 코드

머리 주석이 전제를 적었다. 호출자는 이미 "최신 버전은 안 보인다"고 판정했고, 페이지 래치가 버전 스택의 꼭대기를 고정한다.

`storage` / `innobase` / `row` / `row0vers.cc` L1227-L1342 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0vers.cc#L1227-L1342))

```cpp
// row0vers.cc L1227-L1342
/** Constructs the version of a clustered index record which a consistent
 read should see. We assume that the trx id stored in rec is such that
 the consistent read should not see rec in its present version.
 @param[in]   rec   record in a clustered index; the caller must have a latch
                    on the page; this latch locks the top of the stack of
                    versions of this records
 @param[in]   mtr   mtr holding the latch on rec; it will also hold the latch
                    on purge_view
 @param[in]   index   the clustered index
 @param[in]   offsets   offsets returned by rec_get_offsets(rec, index)
 @param[in]   view   the consistent read view
 @param[in,out]   offset_heap   memory heap from which the offsets are
                                allocated
 @param[in]   in_heap   memory heap from which the memory for *old_vers is
                        allocated; memory for possible intermediate versions
                        is allocated and freed locally within the function
 @param[out]   old_vers   old version, or NULL if the history is missing or
                          the record does not exist in the view, that is, it
                          was freshly inserted afterwards.
 @param[out]   vrow   reports virtual column info if any
 @param[in]   lob_undo   undo log to be applied to blobs.
 @return DB_SUCCESS or DB_MISSING_HISTORY */
dberr_t row_vers_build_for_consistent_read(
    const rec_t *rec, mtr_t *mtr, dict_index_t *index, ulint **offsets,
    ReadView *view, mem_heap_t **offset_heap, mem_heap_t *in_heap,
    rec_t **old_vers, const dtuple_t **vrow, lob::undo_vers_t *lob_undo) {
  DBUG_TRACE;
  const rec_t *version;
  rec_t *prev_version;
  trx_id_t trx_id;
  mem_heap_t *heap = nullptr;
  byte *buf;
  dberr_t err;

  ut_ad(index->is_clustered());
  ut_ad(mtr_memo_contains_page(mtr, rec, MTR_MEMO_PAGE_X_FIX) ||
        mtr_memo_contains_page(mtr, rec, MTR_MEMO_PAGE_S_FIX));
  ut_ad(!rw_lock_own(&(purge_sys->latch), RW_LOCK_S));

  ut_ad(rec_offs_validate(rec, index, *offsets));

  trx_id = row_get_rec_trx_id(rec, index, *offsets);

  /* Reset the collected LOB undo information. */
  if (lob_undo != nullptr) {
    lob_undo->reset();
  }

  ut_ad(!view->changes_visible(trx_id, index->table->name));

  ut_ad(!vrow || !(*vrow));

  version = rec;

  for (;;) {
    mem_heap_t *prev_heap = heap;

    heap = mem_heap_create(1024, UT_LOCATION_HERE);

    if (vrow) {
      *vrow = nullptr;
    }

    /* If purge can't see the record then we can't rely on
    the UNDO log record. */

    bool purge_sees =
        trx_undo_prev_version_build(rec, mtr, version, index, *offsets, heap,
                                    &prev_version, nullptr, vrow, 0, lob_undo);

    err = (purge_sees) ? DB_SUCCESS : DB_MISSING_HISTORY;

    if (prev_heap != nullptr) {
      mem_heap_free(prev_heap);
    }

    if (prev_version == nullptr) {
      /* It was a freshly inserted version */
      *old_vers = nullptr;
      ut_ad(!vrow || !(*vrow));
      break;
    }

    *offsets = rec_get_offsets(prev_version, index, *offsets, ULINT_UNDEFINED,
                               UT_LOCATION_HERE, offset_heap);

#if defined UNIV_DEBUG || defined UNIV_BLOB_LIGHT_DEBUG
    ut_a(!rec_offs_any_null_extern(index, prev_version, *offsets));
#endif /* UNIV_DEBUG || UNIV_BLOB_LIGHT_DEBUG */

    trx_id = row_get_rec_trx_id(prev_version, index, *offsets);

    if (view->changes_visible(trx_id, index->table->name)) {
      /* The view already sees this version: we can copy
      it to in_heap and return */

      buf =
          static_cast<byte *>(mem_heap_alloc(in_heap, rec_offs_size(*offsets)));

      *old_vers = rec_copy(buf, prev_version, *offsets);
      rec_offs_make_valid(*old_vers, index, *offsets);

      if (vrow && *vrow) {
        *vrow = dtuple_copy(*vrow, in_heap);
        dtuple_dup_v_fld(*vrow, in_heap);
      }
      break;
    }

    version = prev_version;
  }

  mem_heap_free(heap);

  return err;
}
```

## 동작 흐름

```text
 row_vers_build_for_consistent_read(rec, mtr, index, offsets, view, offset_heap, in_heap, old_vers)

 L1262  rec 페이지의 S 또는 X 래치를 mtr 이 쥐고 있어야 한다
 L1264  purge_sys->latch 는 쥐고 있으면 안 된다 ([10] 이 S 로 잡는다)
 L1268  trx_id = rec 의 DB_TRX_ID
 L1275  ut_ad(!view->changes_visible(trx_id))           호출자가 이미 판정했다
 L1279  version = rec

 L1281  for (;;)
 L1284    heap = 새 힙 (1024)
 L1293    purge_sees = [09] trx_undo_prev_version_build(rec, mtr, version, ..., &prev_version)
 L1297    err = purge_sees ? DB_SUCCESS : DB_MISSING_HISTORY
 L1299    이전 바퀴의 힙을 버린다 (version 이 거기 있었다. prev_version 은 새 힙에 있다)
 L1303    prev_version == nullptr  -> *old_vers = nullptr, break
            처음 넣은 버전이었거나, undo 가 이미 없어졌다 (err 가 둘을 가른다)
 L1310    prev_version 의 offsets 를 다시 계산 (열 길이가 바뀌었을 수 있다)
 L1317    trx_id = prev_version 의 DB_TRX_ID     (undo 가 되돌려 놓은 옛 값)
 L1319    view->changes_visible(trx_id)  -> in_heap 에 rec_copy 해서 *old_vers, break
 L1336    아니면 version = prev_version, 다음 바퀴

 L1339  마지막 힙을 버리고 err 를 돌려준다
```

체인이 세 칸일 때의 걸음이다. trx 102 의 read view 가 `m_ids = [100, 104]`, `m_low_limit_id = 107` 이라고 하자.

```text
 id=1 의 체인 (최신이 위)               [08] 의 바퀴

 페이지  DB_TRX_ID=104  v=40            시작  104 는 m_ids 에 있다 -> 안 보임 (호출자 판정)
   | roll_ptr                             1   [09] -> (DB_TRX_ID=103, v=30)
   v                                          103 은 m_ids 에 없고 107 보다 작다 -> 보인다
 undo  옛 DB_TRX_ID=103  v=30                 rec_copy -> *old_vers = (103, v=30), break
   | 옛 roll_ptr
   v
 undo  옛 DB_TRX_ID=90   v=10           (여기까지 갈 일은 없다)
   | 옛 roll_ptr (insert)
   v
 insert undo (읽지 않는다)

 만약 103 도 안 보였다면 2 바퀴째에 (90, v=10) 을 만들고, 90 < m_up_limit_id(100) 이라 보인다
 보이는 버전 없이 체인 바닥에 닿으면 [09] 가 insert roll_ptr 을 보고 nullptr -> 이 행은 결과에서 빠진다
 (활성 trx 100 이 넣은 행을 103 이 고칠 수는 없다. 넣은 trx 가 커밋할 때까지 행이 잠겨 있다.
  그래서 바닥 버전을 끝난 trx 90 으로 두었다)
```

```text
 힙의 이어달리기 (중간 버전은 한 바퀴만 산다)

 바퀴    version 이 사는 곳       새로 만드는 heap     L1299 에서 버리는 것
 1       페이지 (rec)            H1 에 prev1          (없음)
 2       H1 (prev1)              H2 에 prev2          H1
 3       H2 (prev2)              H3 에 prev3          H2
 끝      보이는 prevN 을 in_heap 으로 rec_copy, L1339 에서 마지막 heap 해제

 긴 체인 하나를 읽는 비용 = 바퀴 수 x (undo 페이지 하나 읽기 + 레코드 복사 + 갱신 적용)
 오래 열린 view 일수록, 같은 행이 자주 바뀔수록 바퀴가 늘어난다
```

## 결과가 쓰이는 곳

```text
 *old_vers   --> [07] 을 거쳐 [02] 의 rec 가 된다. nullptr 이면 그 행은 건너뛴다
 err         --> DB_MISSING_HISTORY 면 [02] 가 문장을 오류로 끝낸다
 *offsets    --> old_vers 에 맞게 다시 계산된 열 위치표. [02] 가 행을 복사할 때 쓴다
```

## 다루지 않는 것

semi-consistent read 가 쓰는 짝 함수 `row_vers_build_for_semi_consistent_read`(row0vers.cc L1359, read view 대신 `trx_rw_is_active` 로 "마지막 커밋 버전"을 찾는다), 가상 열 `vrow` 의 복사(L1329-L1332), LOB undo 수집(`lob_undo->reset`)은 이 흐름의 곁가지라 줄만 적었다.
