# row_log_apply

상위: [온라인 DDL](../README.md)

**빌드가 끝난 새 보조 인덱스에, 빌드하는 동안 쌓인 row log 를 따라잡게 하는 함수다.** 쓰는 쪽([07])을 막지 않은 채 파일에 넘어간 블록부터 차례로 적용하고, 마지막으로 메모리의 꼬리 블록만 남았을 때 `index->lock` 을 X 로 쥐어 새로 쌓이는 것을 멈춘 뒤 나머지를 적용한다. 그 상태로 `online_status` 를 `ONLINE_INDEX_COMPLETE` 로 바꾸므로, 락을 놓는 순간부터 다른 연결은 row log 대신 트리에 직접 쓴다. MDL 은 SU 그대로다. 테이블 단위의 독점 없이 인덱스 래치 하나로 "따라잡기 -> 전환" 을 끝낸다는 점이 이 함수의 요점이다.

## 위치

`storage` / `innobase` / `row` / `row0log.cc` L3816-L3859 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L3816-L3859))

## 실제 코드

`storage` / `innobase` / `row` / `row0log.cc` L3816-L3859 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L3816-L3859))

```cpp
// row0log.cc L3816-L3859
dberr_t row_log_apply(const trx_t *trx, dict_index_t *index,
                      struct TABLE *table, Alter_stage *stage) {
  dberr_t error;
  row_log_t *log;
  ddl::Dup dup = {index, table, nullptr, 0};
  DBUG_TRACE;

  ut_ad(dict_index_is_online_ddl(index));
  ut_ad(!index->is_clustered());

  stage->begin_phase_log_index();

  log_free_check();

  rw_lock_x_lock(dict_index_get_lock(index), UT_LOCATION_HERE);

  if (!index->table->is_corrupted()) {
    error = row_log_apply_ops(trx, index, &dup, stage);
  } else {
    error = DB_SUCCESS;
  }

  if (error != DB_SUCCESS) {
    ut_a(!dict_table_is_discarded(index->table));
    /* We set the flag directly instead of
    invoking dict_set_corrupted() here,
    because the index is not "public" yet. */
    index->type |= DICT_CORRUPT;
    index->table->drop_aborted = true;

    dict_index_set_online_status(index, ONLINE_INDEX_ABORTED);
  } else {
    ut_ad(dup.m_n_dup == 0);
    dict_index_set_online_status(index, ONLINE_INDEX_COMPLETE);
  }

  log = index->online_log;
  index->online_log = nullptr;
  rw_lock_x_unlock(dict_index_get_lock(index));

  row_log_free(log);

  return error;
}
```

`row_log_apply_ops` 의 블록 고르기다. 파일에 블록이 남아 있으면 `index->lock` 을 놓고 읽고, 남은 것이 꼬리 블록뿐이면 락을 쥔 채로 읽는다.

`storage` / `innobase` / `row` / `row0log.cc` L3515-L3805 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L3515-L3805))

`storage` / `innobase` / `row` / `row0log.cc` L3543-L3635 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L3543-L3635))

```cpp
// row0log.cc L3543-L3635
next_block:
  ut_ad(has_index_lock);
  ut_ad(rw_lock_own(dict_index_get_lock(index), RW_LOCK_X));
  ut_ad(index->online_log->head.bytes == 0);

  stage->inc(row_log_progress_inc_per_block());

  if (trx_is_interrupted(trx)) {
    goto interrupted;
  }

  error = index->online_log->error;
  if (error != DB_SUCCESS) {
    goto func_exit;
  }

  if (index->is_corrupted()) {
    error = DB_INDEX_CORRUPT;
    goto func_exit;
  }

  // ... (L3564-L3573 생략: head 가 tail 을 앞지르면 손상)

  if (index->online_log->head.blocks == index->online_log->tail.blocks) {
    // ... (L3576-L3586 생략: 파일을 0 으로 자른다)
    next_mrec = index->online_log->tail.block;
    next_mrec_end = next_mrec + index->online_log->tail.bytes;

    if (next_mrec_end == next_mrec) {
      /* End of log reached. */
    all_done:
      ut_ad(has_index_lock);
      ut_ad(index->online_log->head.blocks == 0);
      ut_ad(index->online_log->tail.blocks == 0);
      error = DB_SUCCESS;
      goto func_exit;
    }
  } else {
    os_offset_t ofs;

    ofs = (os_offset_t)index->online_log->head.blocks * srv_sort_buf_size;

    ut_ad(has_index_lock);
    has_index_lock = false;
    rw_lock_x_unlock(dict_index_get_lock(index));

    log_free_check();

    // ... (L3610-L3631 생략: head 블록 할당, 파일 읽기, fadvise)

    next_mrec = index->online_log->head.block;
    next_mrec_end = next_mrec + srv_sort_buf_size;
  }
```

한 블록 안에서 레코드를 하나씩 적용하는 반복이다. 블록 끝에 닿으면 X 락을 다시 잡고 다음 블록으로 간다.

`storage` / `innobase` / `row` / `row0log.cc` L3703-L3773 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L3703-L3773))

```cpp
// row0log.cc L3703-L3773
  mrec_end = next_mrec_end;

  while (!trx_is_interrupted(trx)) {
    mrec = next_mrec;
    ut_ad(mrec < mrec_end);

    if (!has_index_lock) {
      /* We are applying operations from a different
      block than the one that is being written to.
      We do not hold index->lock in order to
      allow other threads to concurrently buffer
      modifications. */
      ut_ad(mrec >= index->online_log->head.block);
      ut_ad(mrec_end == index->online_log->head.block + srv_sort_buf_size);
      ut_ad(index->online_log->head.bytes < srv_sort_buf_size);

      // ... (L3719-L3721 생략: redo 체크포인트 기회)
    } else {
      /* We are applying operations from the last block.
      // ... (L3724-L3730 생략: 단정)
    }

    next_mrec = row_log_apply_op(index, dup, &error, offsets_heap, heap,
                                 has_index_lock, mrec, mrec_end, offsets);

    if (error != DB_SUCCESS) {
      goto func_exit;
    } else if (next_mrec == next_mrec_end) {
      /* The record happened to end on a block boundary.
      Do we have more blocks left? */
      if (has_index_lock) {
        /* The index will be locked while
        applying the last block. */
        goto all_done;
      }

      mrec = nullptr;
    process_next_block:
      rw_lock_x_lock(dict_index_get_lock(index), UT_LOCATION_HERE);
      has_index_lock = true;

      index->online_log->head.bytes = 0;
      index->online_log->head.blocks++;
      goto next_block;
    } else if (next_mrec != nullptr) {
      ut_ad(next_mrec < next_mrec_end);
      index->online_log->head.bytes += next_mrec - mrec;
    } else if (has_index_lock) {
      /* When mrec is within tail.block, it should
      be a complete record, because we are holding
      index->lock and thus excluding the writer. */
      ut_ad(index->online_log->tail.blocks == 0);
      ut_ad(mrec_end ==
            index->online_log->tail.block + index->online_log->tail.bytes);
      ut_d(ut_error);
      ut_o(goto unexpected_eof);
    } else {
      memcpy(index->online_log->head.buf, mrec, mrec_end - mrec);
      mrec_end += index->online_log->head.buf - mrec;
      mrec = index->online_log->head.buf;
      goto process_next_block;
    }
  }
```

레코드 하나를 적용할 때는 먼저 찾아 본다. 스캔이 이미 반영한 연산일 수 있기 때문이다.

`storage` / `innobase` / `row` / `row0log.cc` L3221-L3237 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0log.cc#L3221-L3237))

```cpp
// row0log.cc L3221-L3237
  /* We perform the pessimistic variant of the operations if we
  already hold index->lock exclusively. First, search the
  record. The operation may already have been performed,
  depending on when the row in the clustered index was
  scanned. */
  btr_cur_search_to_nth_level(
      index, 0, entry, PAGE_CUR_LE,
      has_index_lock ? BTR_MODIFY_TREE : BTR_MODIFY_LEAF, &cursor, 0, __FILE__,
      __LINE__, &mtr);

  ut_ad(dict_index_get_n_unique(index) > 0);
  /* This test is somewhat similar to row_ins_must_modify_rec(),
  but not identical for unique secondary indexes. */
  if (cursor.low_match >= dict_index_get_n_unique(index) &&
      !page_rec_is_infimum(btr_cur_get_rec(&cursor))) {
    /* We have a matching record. */
    bool exists = (cursor.low_match == dict_index_get_n_fields(index));
```

## 동작 흐름

```text
 호출: Builder::finalize (ddl0builder.cc L1996), 온라인 ADD INDEX 의 FINISH 상태에서

 L3826  stage->begin_phase_log_index      진행률 단계 전환
 L3828  log_free_check
 L3830  rw_lock_x_lock(index->lock)
 L3833  row_log_apply_ops
          next_block: (항상 X 를 쥔 채 들어온다)
            L3550  KILL 이면 중단
            L3554  [07] 이 남긴 오류(메모리 부족 등) 또는 L3559 인덱스 손상이면 끝
            L3575  head.blocks == tail.blocks    파일은 다 읽었다
                     파일을 0 으로 자르고, tail.block 을 읽는다 (X 유지)
                     L3590  꼬리도 비었으면 all_done
            L3599  아니면 파일 블록이 남았다
                     L3605  X 해제              <-- [07] 이 계속 쓸 수 있다
                     L3616  head.blocks 번째 블록을 파일에서 읽는다
          레코드 반복 (L3705)
            L3733  row_log_apply_op -> row_log_apply_op_low
                     L3226  트리에서 그 키를 찾는다
                     INSERT 인데 이미 있으면 건너뛴다, DELETE 인데 없으면 건너뛴다
                     UNIQUE 충돌이면 중복 키 오류
            L3738  블록 끝 -> L3749 X 다시 잡고 head.blocks++ -> next_block
            L3767  레코드가 블록 경계에 걸침 -> head.buf 에 복사해 이어 붙인다
 L3846  실패면 DICT_CORRUPT, drop_aborted, ONLINE_INDEX_ABORTED
 L3849  성공이면 ONLINE_INDEX_COMPLETE      <-- X 를 쥔 채 바꾼다
 L3853  index->online_log = nullptr
 L3854  X 해제                               <-- 이후 DML 은 트리에 직접
 L3856  row_log_free                         임시 파일 닫기
```

따라잡기가 끝나는 이유는 마지막 구간에서만 쓰는 쪽을 막기 때문이다. 아래 그림이 그 경계다.

```text
 쓰는 쪽과 읽는 쪽의 경주 (index->lock 기준)

 구간              index->lock      [07] (다른 연결)                    [08]
 파일 블록 적용    놓음             S 로 잡고 tail 에 계속 쓴다          head 블록을 하나씩 소비
                                    tail 이 차면 파일 끝에 붙인다
 블록 경계         X 잠깐           대기                                head.blocks++ 후 다음 판단
 꼬리 블록 적용    X                대기 (row0ins.cc L2894 mtr_s_lock)  tail.block 을 끝까지 적용
 전환              X                대기                                ONLINE_INDEX_COMPLETE
 이후              놓음             상태가 COMPLETE -> 트리에 직접       끝

 쓰기 속도가 적용 속도보다 계속 빠르면 파일이 자라다가
 innodb_online_alter_log_max_size 에 닿아 실패한다 (row0log.cc L3786-L3790 DB_ONLINE_LOG_TOO_BIG)
```

## 결과가 쓰이는 곳

```text
 ONLINE_INDEX_COMPLETE
      --> [07] 의 row_log_online_op_try 가 false 를 돌려 DML 이 트리에 직접 쓴다
      --> [09] commit 이 이 상태를 전제로 인덱스를 사전에 커밋한다
 오류 (DB_DUPLICATE_KEY, DB_ONLINE_LOG_TOO_BIG, DB_INDEX_CORRUPT)
      --> Builder 오류 -> [05] cleanup -> [04] 가 MySQL 오류로 바꾼다
 row_log_free
      --> 임시 파일과 블록 메모리를 돌려준다
```

## 다루지 않는 것

`row_log_apply_op` 의 레코드 해석(`ROW_OP_INSERT` 의 trx_id 와 extra_size 파싱), 비관적 삽입과 삭제(`btr_cur_pessimistic_*`) 분기, 외부 저장 열이 있는 레코드, 재구성용 `row_log_table_apply` 와 그 레코드 형식은 이 흐름의 곁가지라 요약만 했다.
