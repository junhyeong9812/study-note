# row_ins_clust_index_entry_low

상위: [B+Tree 삽입과 분할](../README.md)

**클러스터드 인덱스에 엔트리 하나를 넣는 한 번의 시도이자, mtr 하나의 수명이다.** `mtr.start` 로 열고, 커서를 삽입 자리에 세우고, 그 자리를 보고 네 갈래(중복 오류, 기존 레코드 갱신, optimistic 삽입, pessimistic 삽입) 중 하나로 간 뒤 `mtr.commit` 으로 닫는다. 같은 함수가 `BTR_MODIFY_LEAF` 와 `BTR_MODIFY_TREE` 두 모드로 불리며, 모드에 따라 쓰는 삽입 함수가 달라진다.

## 위치

`storage` / `innobase` / `row` / `row0ins.cc` L2399-L2645 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2399-L2645))

## 실제 코드

mtr 을 열고 커서를 세운다. 삽입 탐색은 언제나 `PAGE_CUR_LE` 다.

`storage` / `innobase` / `row` / `row0ins.cc` L2439-L2464 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2439-L2464))

```cpp
// row0ins.cc L2439-L2464
  mtr.start();

  if (index->table->is_temporary()) {
    /* Disable REDO logging as the lifetime of temp-tables is
    limited to server or connection lifetime and so REDO
    information is not needed on restart for recovery.
    Disable locking as temp-tables are local to a connection. */

    ut_ad(flags & BTR_NO_LOCKING_FLAG);
    ut_ad(!index->table->is_intrinsic() || (flags & BTR_NO_UNDO_LOG_FLAG));

    mtr.set_log_mode(MTR_LOG_NO_REDO);
  }

  if (mode == BTR_MODIFY_LEAF && dict_index_is_online_ddl(index)) {
    mode = BTR_MODIFY_LEAF | BTR_ALREADY_S_LATCHED;
    mtr_s_lock(dict_index_get_lock(index), &mtr, UT_LOCATION_HERE);
  }

  /* Note that we use PAGE_CUR_LE as the search mode, because then
  the function will return in both low_match and up_match of the
  cursor sensible values */
  pcur.open(index, 0, entry, PAGE_CUR_LE, mode, &mtr, UT_LOCATION_HERE);
  cursor = pcur.get_btr_cur();
  cursor->thr = thr;

```

커서 옆 레코드가 같은 키를 가질 수 있으면 중복 검사를 한다.

`storage` / `innobase` / `row` / `row0ins.cc` L2503-L2545 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2503-L2545))

```cpp
// row0ins.cc L2503-L2545
        (index->allow_duplicates && index->table->is_intrinsic()));

  if (!index->allow_duplicates && n_uniq &&
      (cursor->up_match >= n_uniq || cursor->low_match >= n_uniq)) {
    // ... (L2507-L2527 생략: 온라인 테이블 재빌드의 로그 적용 경로)
      DB_LOCK_WAIT */

      err = row_ins_duplicate_error_in_clust(flags, cursor, entry, thr, &mtr);
    }

    if (err != DB_SUCCESS) {
    err_exit:
      mtr.commit();
      goto func_exit;
    }
  }

  if (dup_chk_only) {
    mtr.commit();
    goto func_exit;
  }
  /* Note: Allowing duplicates would qualify for modification of
  an existing record as the new entry is exactly same as old entry.
```

삽입 본체다. 같은 키의 레코드가 이미 있으면 갱신으로 바꾸고, 아니면 모드에 맞는 삽입 함수를 부른다.

`storage` / `innobase` / `row` / `row0ins.cc` L2547-L2622 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2547-L2622))

```cpp
// row0ins.cc L2547-L2622
  if (!index->allow_duplicates && row_ins_must_modify_rec(cursor)) {
    /* There is already an index entry with a long enough common
    prefix, we must convert the insert into a modify of an
    existing record */
    mem_heap_t *entry_heap = mem_heap_create(1024, UT_LOCATION_HERE);

    /* If the existing record is being modified and the new record
    doesn't fit the provided slot then existing record is added
    to free list and new record is inserted. This also means
    cursor that we have cached for SELECT is now invalid. */
    if (index->last_sel_cur) {
      index->last_sel_cur->invalid = true;
    }

    ut_ad(thr != nullptr);
    err = row_ins_clust_index_entry_by_modify(&pcur, flags, mode, &offsets,
                                              &offsets_heap, entry_heap, entry,
                                              thr, &mtr);

    if (err == DB_SUCCESS && dict_index_is_online_ddl(index)) {
      row_log_table_insert(btr_cur_get_rec(cursor), entry, index, offsets);
    }

    mtr.commit();
    mem_heap_free(entry_heap);
  } else {
    rec_t *insert_rec;

    if (mode != BTR_MODIFY_TREE) {
      ut_ad((mode & ~BTR_ALREADY_S_LATCHED) == BTR_MODIFY_LEAF);
      err = btr_cur_optimistic_insert(flags, cursor, &offsets, &offsets_heap,
                                      entry, &insert_rec, &big_rec, thr, &mtr);
    } else {
      if (buf_LRU_buf_pool_running_out()) {
        err = DB_LOCK_TABLE_FULL;
        goto err_exit;
      }

      DEBUG_SYNC_C("before_insert_pessimitic_row_ins_clust");

      err = btr_cur_optimistic_insert(flags, cursor, &offsets, &offsets_heap,
                                      entry, &insert_rec, &big_rec, thr, &mtr);

      if (err == DB_FAIL) {
        err =
            btr_cur_pessimistic_insert(flags, cursor, &offsets, &offsets_heap,
                                       entry, &insert_rec, &big_rec, thr, &mtr);

        if (index->table->is_intrinsic() && err == DB_SUCCESS) {
          row_ins_temp_prebuilt_tree_modified(index->table);
        }
      }
    }

    if (big_rec != nullptr) {
      mtr.commit();

      /* Online table rebuild could read (and
      ignore) the incomplete record at this point.
      If online rebuild is in progress, the
      row_ins_index_entry_big_rec() will write log. */

      DBUG_EXECUTE_IF("row_ins_extern_checkpoint",
                      log_make_latest_checkpoint(););
      err = row_ins_index_entry_big_rec(thr_get_trx(thr), entry, big_rec,
                                        offsets, &offsets_heap, index,
                                        thr_get_trx(thr)->mysql_thd);
      dtuple_convert_back_big_rec(entry, big_rec);
    } else {
      if (err == DB_SUCCESS && dict_index_is_online_ddl(index)) {
        row_log_table_insert(insert_rec, entry, index, offsets);
      }

      mtr.commit();
    }
  }
```

"같은 키가 이미 있다"의 판정이다. 커서가 가리키는 레코드가 유니크 필드 수만큼 일치해야 한다.

`storage` / `innobase` / `row` / `row0ins.cc` L2308-L2320 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2308-L2320))

```cpp
// row0ins.cc L2308-L2320
static inline bool row_ins_must_modify_rec(
    const btr_cur_t *cursor) /*!< in: B-tree cursor */
{
  /* NOTE: (compare to the note in row_ins_duplicate_error_in_clust)
  Because node pointers on upper levels of the B-tree may match more
  to entry than to actual user records on the leaf level, we
  have to check if the candidate record is actually a user record.
  A clustered index node pointer contains index->n_unique first fields,
  and a secondary index node pointer contains all index fields. */

  return (cursor->low_match >= dict_index_get_n_unique_in_tree(cursor->index) &&
          !page_rec_is_infimum(btr_cur_get_rec(cursor)));
}
```

중복 검사가 가능한 중복 레코드에 잠금을 거는 자리다.

`storage` / `innobase` / `row` / `row0ins.cc` L2212-L2255 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2212-L2255))

```cpp
// row0ins.cc L2212-L2255
  n_unique = dict_index_get_n_unique(cursor->index);

  if (cursor->low_match >= n_unique) {
    rec = btr_cur_get_rec(cursor);

    if (!page_rec_is_infimum(rec)) {
      offsets = rec_get_offsets(rec, cursor->index, offsets, ULINT_UNDEFINED,
                                UT_LOCATION_HERE, &heap);

      /* We set a lock on the possible duplicate: this
      is needed in logical logging of MySQL to make
      sure that in roll-forward we get the same duplicate
      errors as in original execution */

      if (flags & BTR_NO_LOCKING_FLAG) {
        /* Do nothing if no-locking is set */
        err = DB_SUCCESS;
      } else {
        /* If the SQL-query will update or replace
        duplicate key we will take X-lock for
        duplicates ( REPLACE, LOAD DATAFILE REPLACE,
        INSERT ON DUPLICATE KEY UPDATE). */

        err = row_ins_set_rec_lock(row_allow_duplicates(thr) ? LOCK_X : LOCK_S,
                                   LOCK_REC_NOT_GAP, btr_cur_get_block(cursor),
                                   rec, cursor->index, offsets, thr);
      }

      switch (err) {
        case DB_SUCCESS_LOCKED_REC:
        case DB_SUCCESS:
          break;
        default:
          goto func_exit;
      }

      if (row_ins_dupl_error_with_rec(rec, entry, cursor->index, offsets)) {
      duplicate:
        trx->error_index = cursor->index;
        err = DB_DUPLICATE_KEY;
        goto func_exit;
      }
    }
  }
```

## 동작 흐름

```text
 L2439  mtr.start()                               이 시도의 mini-transaction
 L2441  임시 테이블이면 MTR_LOG_NO_REDO              redo 를 남기지 않는다
 L2453  LEAF 인데 온라인 DDL 중이면 index->lock 을 S 로 먼저 잡는다
 L2461  pcur.open(index, 0, entry, PAGE_CUR_LE, mode)   --> [02]
          커서 = 엔트리 이하인 마지막 레코드 (없으면 infimum)
          low_match / up_match = 앞 레코드 / 뒤 레코드와 맞은 필드 수
 L2483  AUTO_INCREMENT 열이 있으면 dict_table_autoinc_log 로 카운터를 먼저 redo 에 남긴다

 L2505  n_uniq 가 있고 low_match 나 up_match >= n_uniq     같은 키 후보가 이웃에 있다
 L2530    row_ins_duplicate_error_in_clust
            L2214  앞 레코드가 후보면
            L2235    잠금: REPLACE / ON DUPLICATE 면 LOCK_X, 아니면 LOCK_S (LOCK_REC_NOT_GAP)
            L2248    delete-mark 가 아니면 DB_DUPLICATE_KEY (row0ins.cc L1906)
            L2257  뒤 레코드도 같은 식으로
 L2533    오류면 mtr.commit, func_exit
 L2540  dup_chk_only 면 여기서 끝

 L2547  row_ins_must_modify_rec(cursor)       커서 레코드가 유니크 필드 전부 일치 (delete-mark 뿐)
 L2562    row_ins_clust_index_entry_by_modify  지워진 표시의 레코드를 새 값으로 되살린다
 L2570    mtr.commit
 L2572  아니면 삽입
 L2575    LEAF   [03] btr_cur_optimistic_insert             자리가 없으면 DB_FAIL
 L2580    TREE   버퍼 풀이 바닥나면 DB_LOCK_TABLE_FULL
 L2587           [03] 을 먼저 다시 해 보고
 L2592           DB_FAIL 이면 [07] btr_cur_pessimistic_insert
 L2601    big_rec 가 있으면 mtr.commit 후 외부 저장 열을 따로 쓴다 (L2611)
 L2620    아니면 mtr.commit                               --> [mini-transaction과 redo 기록]
 L2629  pcur.close
 L2640  AUTO_INCREMENT 를 DD 버퍼 테이블에 반영 (mtr 밖에서)
```

커서가 서는 자리와 두 match 값이 이 함수의 모든 판단 재료다. 삽입은 언제나 커서 레코드의 **바로 뒤**에 한다.

```text
 PAGE_CUR_LE 커서 (키 하나짜리 PK, 페이지에 10, 20, 30 이 있을 때)

 infimum -> [10] -> [20] -> [30] -> supremum

 key      cursor          low_match  up_match  판정
 25       [20]            0          0         보통 삽입, [20] 과 [30] 사이
 20       [20]            1          0         low_match >= n_uniq -> 중복 검사 (L2505)
 5        infimum         0          0         맨 앞 삽입
 35       [30]            0          0         맨 뒤 삽입, 뒤가 supremum

 match 는 "몇 번째 필드까지 같았나" 이다. 키가 하나면 0 또는 1
```

```text
 한 번의 시도가 끝나는 네 갈래 (모두 mtr.commit 으로 닫힌다)

 duplicate     DB_DUPLICATE_KEY / DB_LOCK_WAIT   이웃 레코드가 같은 키이고 살아 있다
 by_modify     DB_SUCCESS                        같은 키의 delete-mark 레코드가 커서에 있어 그것을 갱신
 optimistic    DB_SUCCESS / DB_FAIL              LEAF, 또는 TREE 의 첫 시도
 pessimistic   DB_SUCCESS                        TREE 에서 optimistic 이 DB_FAIL 이라 분할 / 루트 승격
```

## 결과가 쓰이는 곳

```text
 DB_FAIL (LEAF 모드에서)
      --> [행 쓰기] 10 row_ins_clust_index_entry 가 log_free_check 뒤 TREE 모드로 다시 부른다

 DB_DUPLICATE_KEY 와 trx->error_index
      --> [행 쓰기] 08 row_ins -> 06 의 savepoint 롤백 -> 02 write_record 의 REPLACE / UPDATE

 중복 후보에 건 S / X 레코드 잠금 (L2235)
      --> 같은 키로 들어오는 다른 트랜잭션은 이 잠금 때문에 [레코드 잠금과 교착] 에서 기다릴 수 있다

 mtr.commit
      --> 이 시도에서 바뀐 모든 페이지의 redo 와 dirty 표시가 [mini-transaction과 redo 기록] 으로
```

## 다루지 않는 것

온라인 테이블 재빌드의 로그 적용(`row_ins_duplicate_error_in_clust_online`, `row_log_table_insert`), delete-mark 레코드 갱신의 세부(`row_ins_clust_index_entry_by_modify`), 외부 저장 열(`row_ins_index_entry_big_rec`), AUTO_INCREMENT 영속화(`dict_table_autoinc_log`), 디버그 빌드의 높이 제한 검사(L2415-L2429)는 곁가지라 줄만 적었다.
