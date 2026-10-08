# row_search_mvcc

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**InnoDB 의 모든 일반 테이블 읽기가 지나는 1,600줄짜리 함수다.** 커서를 열거나 복원하고, 레코드를 하나 집을 때마다 두 갈래로 나뉜다. 잠금 읽기(`select_lock_type != LOCK_NONE`)는 레코드에 잠금을 걸고 최신 버전을 읽는다. 잠금 없는 읽기는 레코드를 잠그지 않고 read view 로 버전을 고른다. 이 흐름이 보는 것은 뒤쪽이다. 문장의 첫 호출에서 read view 를 받고([03]), 레코드마다 [05] 로 보이는지 묻고, 안 보이면 [07] 로 옛 버전을 만들어 그 버전을 결과로 쓴다. 옛 버전이 delete-mark 되어 있거나 아예 없으면(그 시점에 행이 없었으면) 그 레코드를 건너뛴다.

## 위치

`storage` / `innobase` / `row` / `row0sel.cc` L4431-L6077 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L4431-L6077))

## 실제 코드

함수 머리다. `direction` 이 0 이면 새 검색, `ROW_SEL_NEXT` / `ROW_SEL_PREV` 면 이어 읽기다.

`storage` / `innobase` / `row` / `row0sel.cc` L4431-L4440 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L4431-L4440))

```cpp
// row0sel.cc L4431-L4440
dberr_t row_search_mvcc(byte *buf, page_cur_mode_t mode,
                        row_prebuilt_t *prebuilt, ulint match_mode,
                        const ulint direction) {
  DBUG_TRACE;

  dict_index_t *index = prebuilt->index;
  bool comp = dict_table_is_comp(index->table);
  const dtuple_t *search_tuple = prebuilt->search_tuple;
  btr_pcur_t *pcur = prebuilt->pcur;
  trx_t *trx = prebuilt->trx;
```

문장의 첫 호출에서만 하는 준비다. 잠금 없는 읽기는 read view 를, 잠금 읽기는 테이블 의도 잠금을 받는다. 두 번째 호출부터는 이미 받은 것을 그대로 쓴다.

`storage` / `innobase` / `row` / `row0sel.cc` L4819-L4854 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L4819-L4854))

```cpp
// row0sel.cc L4819-L4854
  /* Do some start-of-statement preparations */

  if (!prebuilt->sql_stat_start) {
    /* No need to set an intention lock or assign a read view */

    if (!MVCC::is_view_active(trx->read_view) && !srv_read_only_mode &&
        prebuilt->select_lock_type == LOCK_NONE) {
      ib::error(ER_IB_MSG_1031) << "MySQL is trying to perform a"
                                   " consistent read but the read view is not"
                                   " assigned!";
      trx_print(stderr, trx, 600);
      fputc('\n', stderr);
      ut_error;
    }
  } else if (prebuilt->select_lock_type == LOCK_NONE) {
    /* This is a consistent read */
    /* Assign a read view for the query */

    if (!srv_read_only_mode) {
      trx_assign_read_view(trx);
      DEBUG_SYNC_C("after_mvcc_assign_read_view");
    }

    prebuilt->sql_stat_start = false;
  } else {
  wait_table_again:
    err = lock_table(0, index->table,
                     prebuilt->select_lock_type == LOCK_S ? LOCK_IS : LOCK_IX,
                     thr);

    if (err != DB_SUCCESS) {
      table_lock_waited = true;
      goto lock_table_wait;
    }
    prebuilt->sql_stat_start = false;
  }
```

레코드 하나를 집은 뒤 잠금 없는 읽기의 갈래다. 클러스터드 인덱스는 레코드에 `DB_TRX_ID` 가 있으니 바로 판정하고, 세컨더리 인덱스는 페이지 단위 값으로 대충 보고 모르면 클러스터드 레코드로 넘긴다.

`storage` / `innobase` / `row` / `row0sel.cc` L5322-L5391 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L5322-L5391))

```cpp
// row0sel.cc L5322-L5391
  } else {
    /* This is a non-locking consistent read: if necessary, fetch
    a previous version of the record */

    if (trx->isolation_level == TRX_ISO_READ_UNCOMMITTED) {
      /* Do nothing: we let a non-locking SELECT read the
      latest version of the record */

    } else if (index == clust_index) {
      /* Fetch a previous version of the row if the current
      one is not visible in the snapshot; if we have a very
      high force recovery level set, we try to avoid crashes
      by skipping this lookup */

      if (srv_force_recovery < 5 &&
          !lock_clust_rec_cons_read_sees(rec, index, offsets,
                                         trx_get_read_view(trx))) {
        rec_t *old_vers;
        /* The following call returns 'offsets' associated with 'old_vers' */
        err = row_sel_build_prev_vers_for_mysql(
            trx->read_view, clust_index, prebuilt, rec, &offsets, &heap,
            &old_vers, need_vrow ? &vrow : nullptr, &mtr,
            prebuilt->get_lob_undo());

        if (err != DB_SUCCESS) {
          goto lock_wait_or_error;
        }

        if (old_vers == nullptr) {
          /* The row did not exist yet in
          the read view */

          goto next_rec;
        }

        rec = old_vers;
        prev_rec = rec;
        ut_d(prev_rec_debug = row_search_debug_copy_rec_order_prefix(
                 pcur, index, prev_rec, &prev_rec_debug_n_fields,
                 &prev_rec_debug_buf, &prev_rec_debug_buf_size));
      }
    } else {
      /* We are looking into a non-clustered index,
      and to get the right version of the record we
      have to look also into the clustered index: this
      is necessary, because we can only get the undo
      information via the clustered index record. */

      ut_ad(!index->is_clustered());

      if (!srv_read_only_mode &&
          !lock_sec_rec_cons_read_sees(rec, index, trx->read_view)) {
        /* We should look at the clustered index.
        However, as this is a non-locking read,
        we can skip the clustered index lookup if
        the condition does not match the secondary
        index entry. */
        switch (row_search_idx_cond_check(buf, prebuilt, rec, offsets)) {
          case ICP_NO_MATCH:
            goto next_rec;
          case ICP_OUT_OF_RANGE:
            err = DB_RECORD_NOT_FOUND;
            goto idx_cond_failed;
          case ICP_MATCH:
            goto requires_clust_rec;
        }

        ut_error;
      }
    }
```

판정이 끝난 버전이 delete-mark 되어 있으면 결과에서 뺀다. 이 시점의 `rec` 는 버퍼 풀 페이지가 아니라 힙에 만든 옛 버전일 수 있다는 주석이 붙어 있다.

`storage` / `innobase` / `row` / `row0sel.cc` L5404-L5437 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L5404-L5437))

```cpp
// row0sel.cc L5404-L5437
  /* NOTE that at this point rec can be an old version of a clustered
  index record built for a consistent read. We cannot assume after this
  point that rec is on a buffer pool page. Functions like
  page_rec_is_comp() cannot be used! */

  if (rec_get_deleted_flag(rec, comp)) {
    /* The record is delete-marked: we can skip it */

    /* No need to keep a lock on a delete-marked record in lower isolation
    levels - it's similar to when Server sees the WHERE condition doesn't match
    and calls unlock_row(). */
    prebuilt->try_unlock(true);

    /* This is an optimization to skip setting the next key lock
    on the record that follows this delete-marked record. This
    optimization works because of the unique search criteria
    which precludes the presence of a range lock between this
    delete marked record and the record following it.

    For now this is applicable only to clustered indexes while
    doing a unique search except for HANDLER queries because
    HANDLER allows NEXT and PREV even in unique search on
    clustered index. There is scope for further optimization
    applicable to unique secondary indexes. Current behaviour is
    to widen the scope of a lock on an already delete marked record
    if the same record is deleted twice by the same transaction */
    if (index == clust_index && unique_search && !prebuilt->used_in_HANDLER) {
      err = DB_RECORD_NOT_FOUND;

      goto normal_return;
    }

    goto next_rec;
  }
```

## 동작 흐름

```text
 L4431  row_search_mvcc(buf, mode, prebuilt, match_mode, direction)

 PHASE 1  L4528  prefetch 캐시에 남은 행이 있으면 꺼내서 돌려준다
 PHASE 2  L4650  direction == 0, 유일 검색, 클러스터드 인덱스이고
                 read view 가 이미 활성이면 AHI 로 지름길 (L4658-L4669)
 PHASE 3  L4765
   L4783  trx_start_if_not_started              트랜잭션이 여기서 시작될 수 있다
   L4785  gap 잠금을 뺄지 (RC 이하의 잠금 SELECT)
   L4821  sql_stat_start 가 false              -> 이미 받은 view 를 쓴다
                                                  잠금 없는 읽기인데 view 가 없으면 ut_error
   L4833  잠금 없는 읽기의 첫 호출             -> [03] trx_assign_read_view  (L4838)
   L4843  잠금 읽기의 첫 호출                  -> lock_table(IS 또는 IX)      (L4845)
   L4858  direction != 0 이면 sel_restore_position_for_mysql 로 커서 복원
          아니면 pcur->open_no_init(search_tuple, BTR_SEARCH_LEAF) (L4909)

 PHASE 4  L4947 rec_loop:  레코드 하나
   infimum / supremum, 범위 끝 검사
   L5226  잠금 읽기   sel_set_rec_lock -> [레코드 잠금과 교착]
   L5322  잠금 없는 읽기  (아래 그림)
   L5409  delete-mark 버전이면 건너뛴다. 클러스터드 유일 검색이면 바로 RECORD_NOT_FOUND (L5430)
   L5440  ICP 조건
   L5455  세컨더리 인덱스이고 클러스터드 열이 필요하면 requires_clust_rec: (L5456)
            row_sel_get_clust_rec_for_mysql 이 클러스터드 레코드를 찾아
            그쪽에서 다시 [05] -> [07] (row0sel.cc L3312)
   행을 MySQL 형식으로 buf 에 복사

 PHASE 5  L5805  커서를 다음 레코드로. 페이지 끝이면 다음 페이지로
 L5914 lock_wait_or_error:   잠금 대기면 커서를 저장하고 기다린 뒤 다시
 L5989 normal_return:        mtr_commit 으로 페이지 래치를 푼다
```

잠금 없는 읽기의 판정은 인덱스 종류에 따라 깊이가 다르다. 세컨더리 인덱스 레코드에는 `DB_TRX_ID` 가 없기 때문이다.

```text
 잠금 없는 읽기의 갈래 (L5322-L5391)

 isolation_level == READ_UNCOMMITTED  (L5326)
      아무것도 안 한다. 페이지의 최신 버전이 곧 결과
      (커밋 안 된 변경도 보인다 = dirty read)

 클러스터드 인덱스  (L5330)
      [05] lock_clust_rec_cons_read_sees(rec, view)
         true   -> rec 를 그대로 쓴다
         false  -> [07] row_sel_build_prev_vers_for_mysql
                     err != DB_SUCCESS     -> lock_wait_or_error  (DB_MISSING_HISTORY 등)
                     old_vers == nullptr   -> next_rec  (그 시점에 행이 없었다)
                     아니면 rec = old_vers  (힙에 만든 옛 버전)

 세컨더리 인덱스  (L5363)
      lock_sec_rec_cons_read_sees  (lock0lock.cc L273)
         페이지 헤더의 PAGE_MAX_TRX_ID 가 view 의 m_up_limit_id 보다 작은가 (view->sees)
         true   -> 이 페이지의 모든 변경이 보인다. 세컨더리 레코드를 그대로 믿는다
         false  -> 모른다. ICP 가 맞으면 requires_clust_rec 로 가서
                   클러스터드 레코드에서 [05] [07] 을 한다
```

세컨더리 인덱스 쪽은 한 단계가 더 있다. 클러스터드 레코드의 옛 버전을 만들었으면, 그 옛 버전이 지금 읽은 세컨더리 레코드와 같은 키인지 다시 본다. 다르면 그 세컨더리 레코드는 내 시점에 없던 것이다.

```text
 세컨더리 인덱스로 읽을 때 (Row_sel_get_clust_rec_for_mysql, row0sel.cc L3298-L3380)

 세컨더리 (k=7, pk=1)  ---- pk 로 클러스터드 검색 ---->  클러스터드 (pk=1, k=7, trx 300)
                                                              trx 300 이 안 보인다
                                                              [07] 로 옛 버전 (pk=1, k=5)
 L3367  옛 버전을 만들었거나 세컨더리 레코드가 delete-mark 면
        row_sel_sec_rec_is_for_clust_rec 로 (k=7) 과 옛 버전의 (k=5) 를 비교
        다르다 -> clust_rec = nullptr -> 이 세컨더리 레코드는 결과에서 빠진다
        (내 시점에서 이 행은 k=5 의 자리에서 따로 읽힌다)
```

```text
 래치와 메모리

 페이지 래치   pcur 가 BTR_SEARCH_LEAF 로 리프 페이지 S 래치를 쥔 mtr 안에서 판정한다
               [08] 의 주석: 이 래치가 "버전 스택의 꼭대기"를 고정한다 (row0vers.cc L1230-L1232)
 옛 버전       prebuilt->old_vers_heap 에 만든다. 페이지는 바꾸지 않는다
 잠금          잠금 없는 읽기는 레코드 잠금을 하나도 만들지 않는다
               문장 첫머리의 테이블 IS 잠금도 잠금 읽기에서만 잡는다 (L4843)
```

## 결과가 쓰이는 곳

```text
 buf                     --> [01] index_read 가 서버에 돌려준다
 prebuilt->pcur 위치     --> 다음 general_fetch 가 sel_restore_position_for_mysql 로 이어 읽는다
 trx->read_view          --> 같은 문장(RC)이나 같은 트랜잭션(RR)의 다음 호출이 그대로 쓴다
 DB_MISSING_HISTORY      --> 서버 오류로 바뀌어 문장이 실패한다
```

## 다루지 않는 것

잠금 읽기 갈래(`sel_set_rec_lock`, `row_compare_row_to_range`, semi-consistent read)는 [레코드 잠금과 교착](../../record-lock/README.md)에서 다룬다. PHASE 1 의 prefetch 캐시, PHASE 2 의 적응형 해시 인덱스, 커서 복원(`sel_restore_position_for_mysql`), 범위 끝 판정(`m_stop_tuple`), ICP, 행 형식 변환(`row_sel_store_mysql_rec`), 공간 인덱스, 잠금 대기 처리(`row_mysql_handle_errors`)는 이 흐름의 곁가지라 줄만 적었다.
