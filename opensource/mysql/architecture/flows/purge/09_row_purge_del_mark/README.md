# row_purge_del_mark

상위: [purge](../README.md)

**DELETE 가 비트만 켜 두고 간 행을 B+Tree 에서 실제로 지우는 자리다.** 순서가 정해져 있다. 세컨더리 인덱스의 엔트리를 하나씩 먼저 지우고, 마지막에 클러스터드 레코드를 지운다. 세컨더리 엔트리는 "지워도 되는지"를 한 번 더 확인한다(`row_purge_poss_sec`). 같은 키 값으로 다른 트랜잭션이 다시 넣었거나, 클러스터드 쪽에 이 엔트리를 아직 필요로 하는 버전이 남아 있으면 지우지 않는다. 클러스터드 레코드는 **지금 레코드의 `DB_ROLL_PTR` 이 이 undo 레코드를 가리킬 때만** 지운다. 다르면 그 사이에 누가 같은 키로 다시 넣거나 고친 것이다. 지우기는 먼저 리프 하나만 래치하는 optimistic 삭제를 시도하고, 페이지가 너무 비게 되면 트리 래치를 잡고 pessimistic 삭제로 다시 한다.

## 위치

`storage` / `innobase` / `row` / `row0purge.cc` L656-L691 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L656-L691))

## 실제 코드

함수 전체다. 세컨더리를 다 돌고 나서 클러스터드로 간다.

`storage` / `innobase` / `row` / `row0purge.cc` L652-L691 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L652-L691))

```cpp
// row0purge.cc L652-L691
/** Purges a delete marking of a record.
 @retval true if the row was not found, or it was successfully removed
 @retval false the purge needs to be suspended because of
 running out of file space */
[[nodiscard]] static bool row_purge_del_mark(
    purge_node_t *node) /*!< in/out: row purge node */
{
  mem_heap_t *heap;

  heap = mem_heap_create(1024, UT_LOCATION_HERE);

  while (node->index != nullptr) {
    /* skip corrupted secondary index */
    dict_table_skip_corrupt_index(node->index);

    row_purge_skip_uncommitted_virtual_index(node->index);

    if (!node->index) {
      break;
    }

    if (node->index->type != DICT_FTS) {
      if (node->index->is_multi_value()) {
        row_purge_remove_multi_sec_if_poss(node, heap, false);
      } else {
        dtuple_t *entry = row_build_index_entry_low(
            node->row, nullptr, node->index, heap, ROW_BUILD_FOR_PURGE);
        row_purge_remove_sec_if_poss(node, node->index, entry);
      }

      mem_heap_empty(heap);
    }

    node->index = node->index->next();
  }

  mem_heap_free(heap);

  return (row_purge_remove_clust_if_poss(node));
}
```

세컨더리 엔트리 하나를 지우는 쪽이다. 리프 래치만으로 먼저 해 보고, 안 되면 트리를 고칠 수 있는 모드로 몇 번 다시 한다.

`storage` / `innobase` / `row` / `row0purge.cc` L578-L614 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L578-L614))

```cpp
// row0purge.cc L578-L614
/** Removes a secondary index entry if possible. */
static inline void row_purge_remove_sec_if_poss(
    purge_node_t *node,    /*!< in: row purge node */
    dict_index_t *index,   /*!< in: index */
    const dtuple_t *entry) /*!< in: index entry */
{
  ulint n_tries = 0;

  /*    fputs("Purge: Removing secondary record\n", stderr); */

  if (!entry) {
    /* The node->row must have lacked some fields of this
    index. This is possible when the undo log record was
    written before this index was created. */
    return;
  }

  if (row_purge_remove_sec_if_poss_leaf(node, index, entry)) {
    return;
  }
retry:
  auto success = row_purge_remove_sec_if_poss_tree(node, index, entry);
  /* The delete operation may fail if we have little
  file space left: TODO: easiest to crash the database
  and restart with more file space */

  if (!success && n_tries < BTR_CUR_RETRY_DELETE_N_TIMES) {
    n_tries++;

    std::this_thread::sleep_for(
        std::chrono::milliseconds(BTR_CUR_RETRY_SLEEP_TIME_MS));

    goto retry;
  }

  ut_a(success);
}
```

리프에서 찾은 엔트리를 지우기 직전의 확인이다. 지워도 된다는 판정이 나와야 하고, 엔트리가 실제로 delete-mark 되어 있어야 한다.

`storage` / `innobase` / `row` / `row0purge.cc` L499-L560 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L499-L560))

```cpp
// row0purge.cc L499-L560
  switch (search_result) {
    case ROW_FOUND:
      /* Before attempting to purge a record, check
      if it is safe to do so. */
      if (row_purge_poss_sec(node, index, entry)) {
        btr_cur_t *btr_cur = pcur.get_btr_cur();

        /* Only delete-marked records should be purged. */
        if (!rec_get_deleted_flag(btr_cur_get_rec(btr_cur),
                                  dict_table_is_comp(index->table))) {
          ib::error(ER_IB_MSG_1008)
              << "tried to purge non-delete-marked"
                 " record"
                 " in index "
              << index->name << " of table " << index->table->name
              << ": tuple: " << *entry << ", record: "
              << rec_index_print(btr_cur_get_rec(btr_cur), index);

          pcur.close();

          ut_d(ut_error);

          ut_o(goto func_exit_no_pcur);
        }

        // ... (L524-L552 생략: 공간 인덱스의 마지막 레코드 예외)

        if (!btr_cur_optimistic_delete(btr_cur, 0, &mtr)) {
          /* The index entry could not be deleted. */
          success = false;
        }
      }
      /* fall through (the index entry is still needed,
      or the deletion succeeded) */
```

지워도 되는지의 판정이다. 클러스터드 레코드를 다시 찾아, 그 레코드나 purge view 가 아직 볼 수 있는 옛 버전 중 이 세컨더리 엔트리에 해당하는 delete-mark 아닌 버전이 있는지 본다.

`storage` / `innobase` / `row` / `row0purge.cc` L262-L299 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L262-L299))

```cpp
// row0purge.cc L262-L299
/** Determines if it is possible to remove a secondary index entry.
 Removal is possible if the secondary index entry does not refer to any
 not delete marked version of a clustered index record where DB_TRX_ID
 is newer than the purge view.

 NOTE: This function should only be called by the purge thread, only
 while holding a latch on the leaf page of the secondary index entry
 (or keeping the buffer pool watch on the page).  It is possible that
 this function first returns true and then false, if a user transaction
 inserts a record that the secondary index entry would refer to.
 However, in that case, the user transaction would also re-insert the
 secondary index entry after purge has removed it and released the leaf
 page latch.
 @return true if the secondary index record can be purged */
bool row_purge_poss_sec(purge_node_t *node,    /*!< in/out: row purge node */
                        dict_index_t *index,   /*!< in: secondary index */
                        const dtuple_t *entry) /*!< in: secondary index entry */
{
  bool can_delete;
  mtr_t mtr;

  ut_ad(!index->is_clustered());
  mtr_start(&mtr);

  can_delete =
      !row_purge_reposition_pcur(BTR_SEARCH_LEAF, node, &mtr) ||
      !row_vers_old_has_index_entry(true, node->pcur.get_rec(), &mtr, index,
                                    entry, node->roll_ptr, node->trx_id);

  /* Persistent cursor is closed if reposition fails. */
  if (node->found_clust) {
    node->pcur.commit_specify_mtr(&mtr);
  } else {
    mtr_commit(&mtr);
  }

  return (can_delete);
}
```

클러스터드 레코드를 지우는 쪽이다. 핵심은 `node->roll_ptr` 비교다.

`storage` / `innobase` / `row` / `row0purge.cc` L133-L235 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L133-L235))

```cpp
// row0purge.cc L133-L235
/** Removes a delete marked clustered index record if possible.
 @retval true if the row was not found, or it was successfully removed
 @retval false if the row was modified after the delete marking */
[[nodiscard]] static bool row_purge_remove_clust_if_poss_low(
    // ... (L137-L157 생략: 매개변수 주석과 지역 변수)

  index = node->table->first_index();

  fil_space_t *space = fil_space_acquire_silent(index->space);
  if (space == nullptr) {
    /* This can happen only for SDI in General Tablespaces.
     */
    ut_ad(dict_table_is_sdi(node->table->id));
    return (true);
  } else {
    fil_space_release(space);
  }

  log_free_check();
  mtr_start(&mtr);

  if (!row_purge_reposition_pcur(mode, node, &mtr)) {
    /* The record was already removed. */
    goto func_exit;
  }

  rec = node->pcur.get_rec();

  offsets = rec_get_offsets(rec, index, offsets_, ULINT_UNDEFINED,
                            UT_LOCATION_HERE, &heap);

  if (node->roll_ptr != row_get_rec_roll_ptr(rec, index, offsets)) {
    /* Someone else has modified the record later: do not remove */
    goto func_exit;
  }

  ut_ad(rec_get_deleted_flag(rec, rec_offs_comp(offsets)));

  if (mode == BTR_MODIFY_LEAF) {
    success = btr_cur_optimistic_delete(node->pcur.get_btr_cur(), 0, &mtr);
  } else {
    dberr_t err;
    ut_ad(mode == (BTR_MODIFY_TREE | BTR_LATCH_FOR_DELETE));

    // ... (L197-L205 생략: 디버그 동기화 지점)

    btr_cur_pessimistic_delete(&err, false, node->pcur.get_btr_cur(), 0, false,
                               node->trx_id, node->undo_no, node->rec_type,
                               &mtr, &node->pcur, node);

    switch (err) {
      case DB_SUCCESS:
        break;
      case DB_OUT_OF_FILE_SPACE:
        success = false;
        break;
      default:
        ut_error;
    }
  }

func_exit:
  if (heap) {
    mem_heap_free(heap);
  }

  /* Persistent cursor is closed if reposition fails. */
  if (node->found_clust) {
    node->pcur.commit_specify_mtr(&mtr);
  } else {
    mtr_commit(&mtr);
  }

  return (success);
}
```

`storage` / `innobase` / `row` / `row0purge.cc` L237-L260 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L237-L260))

```cpp
// row0purge.cc L237-L260
/** Removes a clustered index record if it has not been modified after the
 delete marking.
 @retval true if the row was not found, or it was successfully removed
 @retval false the purge needs to be suspended because of running out
 of file space. */
[[nodiscard]] static bool row_purge_remove_clust_if_poss(
    purge_node_t *node) /*!< in/out: row purge node */
{
  if (row_purge_remove_clust_if_poss_low(node, BTR_MODIFY_LEAF)) {
    return (true);
  }

  for (ulint n_tries = 0; n_tries < BTR_CUR_RETRY_DELETE_N_TIMES; n_tries++) {
    if (row_purge_remove_clust_if_poss_low(
            node, BTR_MODIFY_TREE | BTR_LATCH_FOR_DELETE)) {
      return (true);
    }

    std::this_thread::sleep_for(
        std::chrono::milliseconds(BTR_CUR_RETRY_SLEEP_TIME_MS));
  }

  return (false);
}
```

## 동작 흐름

```text
 row_purge_del_mark(node)        node->index = 첫 세컨더리 ([08] 이 맞춰 두었다)

 L663  while (node->index != nullptr)
 L665    손상된 인덱스, 커밋 안 된 가상 열 인덱스는 건너뛴다
 L673    FULLTEXT 가 아니면
           다중 값 인덱스   -> row_purge_remove_multi_sec_if_poss
           그 밖            -> entry = row_build_index_entry_low(node->row, index)
                               row_purge_remove_sec_if_poss(node, index, entry)
 L685    node->index = 다음 인덱스
 L690  return row_purge_remove_clust_if_poss(node)

 row_purge_remove_sec_if_poss (L579)
   L595  _leaf: BTR_MODIFY_LEAF 로 찾고 (L493 row_search_index_entry)
           찾았고 row_purge_poss_sec 가 true 이고 delete-mark 면 btr_cur_optimistic_delete
   L599  실패하면 _tree: BTR_MODIFY_TREE 로 pessimistic 삭제, 공간이 모자라면 잠깐 자고 재시도
   L613  끝내 실패하면 ut_a (서버를 멈춘다. 주석은 파일 공간 부족을 TODO 로 적었다)

 row_purge_remove_clust_if_poss (L242)
   L245  _low(BTR_MODIFY_LEAF)
           L171  log_free_check, mtr_start
           L174  node->ref 로 클러스터드 레코드를 다시 찾는다. 없으면 이미 지워졌다 -> 성공
           L184  레코드의 DB_ROLL_PTR != node->roll_ptr  -> 지우지 않는다 (누가 다시 고쳤다)
           L192  btr_cur_optimistic_delete
   L249  실패하면 BTR_MODIFY_TREE 로 BTR_CUR_RETRY_DELETE_N_TIMES 번까지
           L207  btr_cur_pessimistic_delete  -> 페이지가 비면 btr_cur_compress_if_useful
   L259  그래도 실패면 false -> [07] 의 row_purge 가 1초 뒤 다시
```

`DB_ROLL_PTR` 비교가 무엇을 막는지 시간으로 보자. 같은 PK 로 지웠다가 다시 넣는 경우다.

```text
 시간 ->

 trx 100  DELETE id=7        클러스터드 (id=7, TRX=100, ROLL=U1, delete-mark)
                             U1 = trx 100 의 DEL_MARK_REC undo
 trx 100  COMMIT             U1 이 history 로
 trx 200  INSERT id=7        delete-mark 레코드를 갱신해서 되살린다
                             (id=7, TRX=200, ROLL=U2, delete-mark 해제)   btree-insert 01 의 by_modify
 purge    U1 을 처리
          node->ref = (id=7) 로 찾았다. 레코드의 ROLL = U2, node->roll_ptr = U1
          L184  다르다 -> 지우지 않는다. trx 200 의 새 행이 살아남는다
```

세컨더리 쪽 판정이 필요한 이유도 같은 모양이다. 세컨더리 엔트리에는 `DB_TRX_ID` 가 없어서, 그 엔트리가 어느 버전의 것인지는 클러스터드 쪽을 봐야 안다.

```text
 row_purge_poss_sec (L276) 이 false 를 주는 경우 (= 세컨더리 엔트리를 남긴다)

 클러스터드 레코드를 찾았고 (row_purge_reposition_pcur)
 row_vers_old_has_index_entry(true, clust_rec, ..., entry, node->roll_ptr, node->trx_id) 가 true
   머리 주석 (row0vers.cc L968-L972): trx id 가 purge view 이상인 버전 (지금 버전 포함) 중에
   delete-mark 되지 않았고 세컨더리 엔트리가 entry 와 같은 버전이 있으면 true
 예) DELETE 로 (k=5, id=1) 이 delete-mark 된 뒤, 다른 trx 가 id=1 을 k=5 로 다시 넣었다
     -> 세컨더리 (k=5, id=1) 엔트리는 새 행의 것이기도 하다 -> 지우면 안 된다

 클러스터드 레코드가 아예 없으면 true (지운다)
```

## 결과가 쓰이는 곳

```text
 B+Tree 의 빈자리
      --> btr_cur_optimistic_delete / pessimistic_delete 가 레코드를 페이지에서 뺀다
      --> 지워지는 레코드의 잠금은 다음 레코드가 gap 잠금으로 물려받는다 (lock_update_delete)
      --> 페이지가 많이 비면 btr_cur_compress_if_useful 로 이웃과 합친다 (btr0cur.cc L4811)
 반환값 false
      --> [08] -> [07] row_purge 가 1초 자고 다시 시도
```

## 다루지 않는 것

B+Tree 삭제 자체(`btr_cur_optimistic_delete_func`, `btr_cur_pessimistic_delete`, 페이지 합치기 `btr_compress`)는 [B+Tree 삽입과 분할](../../btree-insert/README.md)의 반대 방향이라 줄만 적었다. `row_vers_old_has_index_entry` 의 버전 순회, 공간 인덱스의 마지막 레코드 예외(L524-L552), 온라인 DDL 중인 인덱스의 처리(`row_purge_remove_sec_if_poss_tree` 의 `dict_index_is_online_ddl`), change buffer 로 미루는 삭제(`BTR_DELETE`)는 이 흐름의 곁가지다.
