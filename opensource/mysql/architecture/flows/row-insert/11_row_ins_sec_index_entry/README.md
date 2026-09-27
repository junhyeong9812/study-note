# row_ins_sec_index_entry

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**세컨더리 인덱스에 엔트리를 넣는 두 번의 시도를 감싼다.** 모양은 [10] 과 같다. LEAF 로 해 보고 `DB_FAIL` 이면 TREE 로 다시 한다. 다른 점은 그 아래 `row_ins_sec_index_entry_low` 에 있다. 세컨더리는 **undo 를 쓰지 않고**, 리프 페이지가 버퍼 풀에 없으면 **change buffer 에 넣고 끝낼 수 있으며**, 유니크 인덱스는 중복 검사를 위해 mtr 을 한 번 끊고 다시 내려간다. 이 문서는 `_low` 의 그 세 자리를 함께 본다.

## 위치

`storage` / `innobase` / `row` / `row0ins.cc` L3204-L3290 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3204-L3290))

## 실제 코드

`storage` / `innobase` / `row` / `row0ins.cc` L3204-L3290 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3204-L3290))

```cpp
// row0ins.cc L3204-L3290
dberr_t row_ins_sec_index_entry(
    dict_index_t *index, /*!< in: secondary index */
    dtuple_t *entry,     /*!< in/out: index entry to insert */
    que_thr_t *thr,      /*!< in: query thread */
    bool dup_chk_only)
/*!< in: if true, just do duplicate check
and return. don't execute actual insert. */
{
  dberr_t err;
  mem_heap_t *offsets_heap;
  mem_heap_t *heap;
  trx_id_t trx_id = 0;

  // ... (L3217-L3231 생략: 디버그용 잠금 대기 주입)

  if (!thd_is_sql_fk_checks_enabled() && !index->table->foreign_set.empty()) {
    DBUG_PRINT("fk", ("InnoDB FK on table %s", index->table->name.m_name));

    err = row_ins_check_foreign_constraints(index->table, index, entry, thr);
    if (err != DB_SUCCESS) {
      return (err);
    }
  }

  offsets_heap = mem_heap_create(1024, UT_LOCATION_HERE);
  heap = mem_heap_create(1024, UT_LOCATION_HERE);

  /* Try first optimistic descent to the B-tree */

  uint32_t flags;

  if (!index->table->is_intrinsic()) {
    log_free_check();
    ut_ad(thr_get_trx(thr)->id != 0);

    flags = index->table->is_temporary() ? BTR_NO_LOCKING_FLAG : 0;
    /* For intermediate table during copy alter table,
    skip the undo log and record lock checking for
    insertion operation. */
    if (index->table->skip_alter_undo) {
      trx_id = thr_get_trx(thr)->id;
      flags |= BTR_NO_UNDO_LOG_FLAG | BTR_NO_LOCKING_FLAG;
    }

  } else {
    flags = BTR_NO_LOCKING_FLAG | BTR_NO_UNDO_LOG_FLAG;
  }

  err = row_ins_sec_index_entry_low(flags, BTR_MODIFY_LEAF, index, offsets_heap,
                                    heap, entry, trx_id, thr, dup_chk_only);
  if (err == DB_FAIL) {
    mem_heap_empty(heap);

    /* Try then pessimistic descent to the B-tree */

    if (!index->table->is_intrinsic()) {
      log_free_check();
    } else if (!index->last_sel_cur) {
      dict_allocate_mem_intrinsic_cache(index);
      index->last_sel_cur->invalid = true;
    } else {
      index->last_sel_cur->invalid = true;
    }

    err =
        row_ins_sec_index_entry_low(flags, BTR_MODIFY_TREE, index, offsets_heap,
                                    heap, entry, 0, thr, dup_chk_only);
  }

  mem_heap_free(heap);
  mem_heap_free(offsets_heap);
  return (err);
}
```

아래는 L3266 과 L3283 이 부르는 `row_ins_sec_index_entry_low` 의 세 자리다. 먼저 mtr 을 시작하고 change buffer 를 허락한다.

`storage` / `innobase` / `row` / `row0ins.cc` L2859-L2875 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2859-L2875))

```cpp
// row0ins.cc L2859-L2875
  mtr_start(&mtr);

  if (index->table->is_temporary()) {
    /* Disable REDO logging as the lifetime of temp-tables is
    limited to server or connection lifetime and so REDO
    information is not needed on restart for recovery.
    Disable locking as temp-tables are local to a connection. */

    ut_ad(flags & BTR_NO_LOCKING_FLAG);
    ut_ad(!index->table->is_intrinsic() || (flags & BTR_NO_UNDO_LOG_FLAG));

    mtr.set_log_mode(MTR_LOG_NO_REDO);
  } else if (!dict_index_is_spatial(index)) {
    /* Enable insert buffering if it's neither temp-table
    nor spatial index. */
    search_mode |= BTR_INSERT;
  }
```

탐색 중에 change buffer 에 들어갔으면 여기서 끝난다.

`storage` / `innobase` / `row` / `row0ins.cc` L2957-L2961 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2957-L2961))

```cpp
// row0ins.cc L2957-L2961
  if (cursor.flag == BTR_CUR_INSERT_TO_IBUF) {
    ut_ad(!dict_index_is_spatial(index));
    /* The insert was buffered during the search: we are done */
    goto func_exit;
  }
```

유니크 세컨더리는 mtr 을 끊고 중복을 따로 검사한 뒤 다시 내려간다.

`storage` / `innobase` / `row` / `row0ins.cc` L2973-L2990 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L2973-L2990))

```cpp
// row0ins.cc L2973-L2990
  n_unique = dict_index_get_n_unique(index);

  if (dict_index_is_unique(index) &&
      (cursor.low_match >= n_unique || cursor.up_match >= n_unique)) {
    mtr_commit(&mtr);

    DEBUG_SYNC_C("row_ins_sec_index_unique");

    if (row_ins_sec_mtr_start_and_check_if_aborted(&mtr, index, check,
                                                   search_mode)) {
      goto func_exit;
    }

    err = row_ins_scan_sec_index_for_duplicate(flags, index, entry, thr, check,
                                               &mtr, offsets_heap);

    mtr_commit(&mtr);

```

실제 삽입이다. 클러스터드와 같은 optimistic / pessimistic 함수를 부른다.

`storage` / `innobase` / `row` / `row0ins.cc` L3066-L3103 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3066-L3103))

```cpp
// row0ins.cc L3066-L3103
  } else {
    rec_t *insert_rec;
    big_rec_t *big_rec;

    if (mode == BTR_MODIFY_LEAF) {
      err = btr_cur_optimistic_insert(flags, &cursor, &offsets, &offsets_heap,
                                      entry, &insert_rec, &big_rec, thr, &mtr);
      if (err == DB_SUCCESS && dict_index_is_spatial(index) &&
          rtr_info.mbr_adj) {
        err = rtr_ins_enlarge_mbr(&cursor, &mtr);
      }
    } else {
      ut_ad(mode == BTR_MODIFY_TREE);
      if (buf_LRU_buf_pool_running_out()) {
        err = DB_LOCK_TABLE_FULL;
        goto func_exit;
      }

      err = btr_cur_optimistic_insert(flags, &cursor, &offsets, &offsets_heap,
                                      entry, &insert_rec, &big_rec, thr, &mtr);
      if (err == DB_FAIL) {
        err =
            btr_cur_pessimistic_insert(flags, &cursor, &offsets, &offsets_heap,
                                       entry, &insert_rec, &big_rec, thr, &mtr);
      }
      if (err == DB_SUCCESS && dict_index_is_spatial(index) &&
          rtr_info.mbr_adj) {
        err = rtr_ins_enlarge_mbr(&cursor, &mtr);
      }
    }

    if (err == DB_SUCCESS && trx_id) {
      page_update_max_trx_id(btr_cur_get_block(&cursor),
                             btr_cur_get_page_zip(&cursor), trx_id, &mtr);
    }

    ut_ad(!big_rec);
  }
```

## 동작 흐름

```text
 row_ins_sec_index_entry (L3204)
 L3233  SQL 계층 FK 검사를 안 쓰고 FK 가 있으면 row_ins_check_foreign_constraints
 L3250  log_free_check()
 L3253  임시 테이블이면 BTR_NO_LOCKING_FLAG
 L3257  복사식 ALTER 중간 테이블이면 undo, 잠금 생략 + trx_id 기억
 1차   L3266  row_ins_sec_index_entry_low(flags, BTR_MODIFY_LEAF, ...)
 L3268  DB_FAIL 이면
 L3274    log_free_check()
 2차   L3283  row_ins_sec_index_entry_low(flags, BTR_MODIFY_TREE, ...)

 row_ins_sec_index_entry_low (L2835)
 L2859  mtr_start
 L2861  임시 테이블이면 redo 끔
 L2874  아니고 공간 인덱스도 아니면 search_mode |= BTR_INSERT        change buffer 허락
 L2883  아직 커밋되지 않은 인덱스(온라인 DDL 중)면 index->lock 을 잡고
 L2899    row_log_online_op_try 로 DDL 로그에 넣고 끝날 수 있다
 L2909  check_unique_secondary 가 꺼져 있으면 BTR_IGNORE_SEC_UNIQUE
 L2952  btr_cur_search_to_nth_level(index, 0, entry, PAGE_CUR_LE, search_mode)
 L2957  cursor.flag == BTR_CUR_INSERT_TO_IBUF  -> 페이지를 읽지 않고 끝
 L2975  유니크 인덱스이고 같은 키 후보가 있으면
 L2977    mtr_commit
 L2986    row_ins_scan_sec_index_for_duplicate   다른 mtr 에서 S 잠금을 걸며 중복 검사
 L3035    다시 탐색 (BTR_INSERT, BTR_IGNORE_SEC_UNIQUE 는 뺀다)
 L3045  row_ins_must_modify_rec          같은 값의 delete-mark 레코드가 있으면 되살린다
 L3070  LEAF   btr_cur_optimistic_insert                     --> [B+Tree 03]
 L3084  TREE   btr_cur_optimistic_insert, DB_FAIL 이면
 L3088         btr_cur_pessimistic_insert                    --> [B+Tree 07]
 L3110  mtr_commit
```

change buffer 는 세컨더리 리프를 디스크에서 읽는 대신 변경을 따로 적어 두는 자리다. 탐색 함수가 리프를 가져올 때 "버퍼 풀에 있을 때만"으로 요청하고, 없으면 `ibuf_insert` 로 돌린다.

```text
 세컨더리 삽입이 change buffer 로 가는 길 (btr0cur.cc)

 L2874  search_mode |= BTR_INSERT                    (row0ins.cc)
 L727   btr_op = BTR_INSERT_OP  (BTR_IGNORE_SEC_UNIQUE 면 BTR_INSERT_IGNORE_UNIQUE_OP)
 L942   리프 차례이고 latch_mode 가 BTR_MODIFY_LEAF 이하일 때만 (TREE 재시도에서는 안 간다)
 L945     ibuf_should_try(index, btr_op != BTR_INSERT_OP) 이면
 L950     fetch = Page_fetch::IF_IN_POOL              버퍼 풀에 있을 때만 준다
 L958   buf_page_get_gen(...) 가 nullptr              페이지가 풀에 없음
 L978   ibuf_insert(IBUF_OP_INSERT, tuple, ...)       성공하면
 L980     cursor->flag = BTR_CUR_INSERT_TO_IBUF      [11] 은 L2957 에서 끝낸다
 L1026  실패하면 fetch 를 원래대로 돌려 페이지를 읽는다

 ibuf_should_try 가 거짓인 경우 (ibuf0ibuf.ic L123-L129)
   innodb_change_buffering = none, 클러스터드, 공간 인덱스, 내림차순 인덱스,
   유니크 인덱스인데 유니크 검사를 무시하지 않을 때 (L128),
   그 밖에 시스템 테이블스페이스의 DD 인덱스, quiesce 중, 높은 innodb_force_recovery
```

```text
 클러스터드 [10] 과 세컨더리 [11] 의 차이

 undo 기록
   클러스터드  btr_cur_ins_lock_and_undo 가 trx_undo_report_row_operation 을 부른다
   세컨더리    같은 함수가 !index->is_clustered() 면 잠금 검사만 하고 돌아간다 (btr0cur.cc L2602)
               세컨더리 엔트리를 되돌리는 정보가 없다는 뜻은 아니다. 롤백 때 row_undo_ins 는
               클러스터드용 insert undo 레코드 한 건에서 행을 다시 만들고, 세컨더리마다
               row_build_index_entry 로 엔트리를 재구성해 지운 뒤 (row0uins.cc L427, L492)
               마지막에 클러스터드 레코드를 지운다 (row0uins.cc L499)
 change buffer
   클러스터드  불가 (btr0cur.cc L747 assert)
   세컨더리    가능 (위 그림)
 중복 검사
   클러스터드  같은 mtr 안에서 row_ins_duplicate_error_in_clust
   세컨더리    유니크면 mtr 을 끊고 row_ins_scan_sec_index_for_duplicate 로 따로
 페이지 최대 trx id
   세컨더리    잠금 검사가 통과하면 lock_rec_insert_check_and_lock 안에서 (lock0lock.cc L5139),
               pessimistic 삽입 뒤 커서가 옮겨 간 페이지에 다시 (btr0cur.cc L3042)
               page_update_max_trx_id 로 올린다
```

## 결과가 쓰이는 곳

```text
 반환값
      --> [08] 이 다음 세컨더리로 가거나, 실패면 멈춘다
      --> DB_DUPLICATE_KEY 면 [06] 이 savepoint 로 클러스터드와 앞선 세컨더리 삽입을 되돌린다

 change buffer 레코드
      --> 나중에 그 리프 페이지가 버퍼 풀로 읽힐 때 ibuf_merge_or_delete_for_page 로 병합된다 (buf0buf.cc L4049, [버퍼 풀 페이지 획득] 의 곁가지)
```

## 다루지 않는 것

온라인 DDL 로그(`row_log_online_op_try`), 공간 인덱스의 MBR 확장(`rtr_ins_enlarge_mbr`), multi-value 인덱스, 유니크 중복 검사가 거는 S 잠금의 범위(`row_ins_scan_sec_index_for_duplicate`), delete-mark 레코드를 되살리는 `row_ins_sec_index_entry_by_modify`, change buffer 의 병합과 비트맵은 곁가지라 줄만 적었다.
