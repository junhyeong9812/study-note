# sel_set_rec_lock

상위: [레코드 잠금과 교착](../README.md)

**잠금 읽기가 잠금 계층으로 들어가는 문이다.** `row_search_mvcc` 가 "이 레코드에 어떤 종류(next-key, 레코드만, gap 만)를 걸지" 정해서 넘기면, 이 함수는 인덱스 종류(클러스터드, 보조, 공간)에 맞는 잠금 함수를 고른다. 볼거리는 호출하는 쪽에서 `lock_type` 을 고르는 규칙과, 잠금 개수가 너무 많을 때의 비상 탈출이다.

## 위치

`storage` / `innobase` / `row` / `row0sel.cc` L1138-L1180 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L1138-L1180))

## 실제 코드

`storage` / `innobase` / `row` / `row0sel.cc` L1138-L1180 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L1138-L1180))

```cpp
// row0sel.cc L1138-L1180
static inline dberr_t sel_set_rec_lock(btr_pcur_t *pcur, const rec_t *rec,
                                       dict_index_t *index,
                                       const ulint *offsets,
                                       select_mode sel_mode, ulint mode,
                                       ulint type, que_thr_t *thr, mtr_t *mtr) {
  trx_t *trx;
  dberr_t err = DB_SUCCESS;
  const buf_block_t *block;

  block = pcur->get_block();

  trx = thr_get_trx(thr);
  ut_ad(trx_can_be_handled_by_current_thread(trx));

  if (UT_LIST_GET_LEN(trx->lock.trx_locks) > 10000) {
    if (buf_LRU_buf_pool_running_out()) {
      return (DB_LOCK_TABLE_FULL);
    }
  }

  if (index->is_clustered()) {
    err = lock_clust_rec_read_check_and_lock(
        lock_duration_t::REGULAR, block, rec, index, offsets, sel_mode,
        static_cast<lock_mode>(mode), type, thr);
  } else {
    if (dict_index_is_spatial(index)) {
      if (type == LOCK_GAP || type == LOCK_ORDINARY) {
        ib::error(ER_IB_MSG_1026) << "Incorrectly request GAP lock "
                                     "on RTree";
        ut_d(ut_error);
        ut_o(return (DB_SUCCESS));
      }
      err = sel_set_rtr_rec_lock(pcur, rec, index, offsets, sel_mode, mode,
                                 type, thr, mtr);
    } else {
      err = lock_sec_rec_read_check_and_lock(
          lock_duration_t::REGULAR, block, rec, index, offsets, sel_mode,
          static_cast<lock_mode>(mode), type, thr);
    }
  }

  return (err);
}
```

호출하는 쪽이다. 레코드가 검색 범위에 들 수 있는지, 레코드 앞 gap 이 범위와 겹치는지 두 질문으로 잠금 종류를 정한다.

`storage` / `innobase` / `row` / `row0sel.cc` L5226-L5254 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L5226-L5254))

```cpp
// row0sel.cc L5226-L5254
  if (prebuilt->select_lock_type != LOCK_NONE) {
    auto row_to_range_relation = row_compare_row_to_range(
        set_also_gap_locks, trx, unique_search, index, clust_index, rec, comp,
        mode, direction, search_tuple, offsets, moves_up, prebuilt);

    ulint lock_type;
    if (row_to_range_relation.row_can_be_in_range) {
      if (row_to_range_relation.gap_can_intersect_range) {
        lock_type = LOCK_ORDINARY;
      } else {
        lock_type = LOCK_REC_NOT_GAP;
      }
    } else {
      if (row_to_range_relation.gap_can_intersect_range) {
        lock_type = LOCK_GAP;
      } else {
        err = DB_RECORD_NOT_FOUND;
        goto normal_return;
      }
    }
    /* in case of semi-consistent read, we use SELECT_SKIP_LOCKED, so we don't
    waste time on creating a WAITING lock, as we won't wait on it anyway */
    const bool use_semi_consistent =
        prebuilt->row_read_type == ROW_READ_TRY_SEMI_CONSISTENT &&
        !unique_search && index == clust_index && !trx_is_high_priority(trx);
    err = sel_set_rec_lock(
        pcur, rec, index, offsets,
        use_semi_consistent ? SELECT_SKIP_LOCKED : prebuilt->select_mode,
        prebuilt->select_lock_type, lock_type, thr, &mtr);
```

잠금을 기다려야 하면 `row_search_mvcc` 는 mtr 를 커밋해 페이지 래치를 놓은 뒤에 재운다.

`storage` / `innobase` / `row` / `row0sel.cc` L5914-L5944 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0sel.cc#L5914-L5944))

```cpp
// row0sel.cc L5914-L5944
lock_wait_or_error:
  /* Reset the old and new "did semi-consistent read" flags. */
  if (UNIV_UNLIKELY(prebuilt->row_read_type == ROW_READ_DID_SEMI_CONSISTENT)) {
    prebuilt->row_read_type = ROW_READ_TRY_SEMI_CONSISTENT;
  }
  did_semi_consistent_read = false;

  /*-------------------------------------------------------------*/
  if (!dict_index_is_spatial(index)) {
    pcur->store_position(&mtr);
  }

lock_table_wait:
  mtr_commit(&mtr);
  mtr_has_extra_clust_latch = false;

  trx->error_state = err;

  /* The following is a patch for MySQL */

  if (thr->is_active) {
    que_thr_stop_for_mysql(thr);
  }

  thr->lock_state = QUE_THR_LOCK_ROW;

  if (row_mysql_handle_errors(&err, trx, thr, nullptr)) {
    /* It was a lock wait, and it ended */

    thr->lock_state = QUE_THR_LOCK_NOLOCK;
    mtr_start(&mtr);
```

## 동작 흐름

```text
 L1152  trx->lock.trx_locks 가 10000 개를 넘고
 L1153    버퍼 풀이 모자라면 (buf_LRU_buf_pool_running_out)
 L1154    DB_LOCK_TABLE_FULL          잠금 구조체도 버퍼 풀 메모리를 쓰기 때문
                                      --> row_mysql_handle_errors 가 트랜잭션 전체 롤백

 L1158  클러스터드 인덱스   -> [02] lock_clust_rec_read_check_and_lock
 L1163  공간 인덱스         -> GAP / ORDINARY 를 요청하면 오류 (L1164)
                               sel_set_rtr_rec_lock (predicate 잠금, 이 흐름 밖)
 L1172  보조 인덱스         -> lock_sec_rec_read_check_and_lock (lock0lock.cc L5371)
                               [02] 와 같은 모양이고 마지막에 lock_rec_lock 을 부른다
```

`mode` 는 `prebuilt->select_lock_type` 이다. `FOR SHARE` 면 `LOCK_S`, `FOR UPDATE` 와 UPDATE/DELETE 의 스캔이면 `LOCK_X` 가 온다. `type` 은 아래 표로 정해진다.

```text
 row_search_mvcc 가 lock_type 을 고르는 표 (row0sel.cc L5231-L5245)

 row_can_be_in_range  gap_can_intersect_range  lock_type
 true                 true                     LOCK_ORDINARY     next-key
 true                 false                    LOCK_REC_NOT_GAP  레코드만
 false                true                     LOCK_GAP          gap 만
 false                false                    잠그지 않고 DB_RECORD_NOT_FOUND

 예) id 가 유일 키이고 WHERE id = 5 로 정확히 찾으면 gap 이 범위와 안 겹친다
       -> 레코드만 잠근다
     WHERE id BETWEEN 5 AND 9 로 훑으면 레코드와 그 앞 gap 을 같이 잠근다
       -> 범위를 벗어난 첫 레코드에는 gap 만 남는다
```

```text
 sel_mode (row0sel.cc L5248-L5253)

 prebuilt->select_mode        SKIP LOCKED / NOWAIT / 보통
 semi-consistent 읽기이면     SELECT_SKIP_LOCKED 로 바꿔 넘긴다 (L5248-L5253)
                              기다리지 않고 마지막 커밋 버전을 읽으려고
                              (READ COMMITTED 의 UPDATE 스캔, 클러스터드, 유일 검색 아님)
```

```text
 반환값을 받은 뒤 (row0sel.cc L5256 이후)

 DB_SUCCESS_LOCKED_REC  새 잠금을 만들었다. RC 에서는 new_rec_lock 표시 -> 조건 불일치면 나중에 푼다
 DB_SUCCESS             이미 가진 잠금으로 충분했다
 DB_SKIP_LOCKED         SKIP LOCKED 면 다음 레코드로, semi-consistent 면 커밋된 옛 버전을 만든다
 DB_LOCK_WAIT           L5306 goto lock_wait_or_error -> L5927 mtr_commit -> L5940 row_mysql_handle_errors
                        --> [08] 에서 잠든다
```

## 결과가 쓰이는 곳

```text
 반환값
      --> row_search_mvcc 의 switch 가 레코드를 쓸지, 건너뛸지, 기다릴지 정한다
 DB_LOCK_WAIT
      --> 페이지 래치를 놓은 상태로 잠든다. 깨어나면 저장한 커서 위치로 복원해 다시 찾는다
```

## 다루지 않는 것

`row_compare_row_to_range` 의 범위 판정 세부, `set_also_gap_locks` 와 격리 수준에 따른 gap 생략(`trx->skip_gap_locks`), semi-consistent read 의 옛 버전 구성(`row_sel_build_committed_vers_for_mysql`), 공간 인덱스의 `sel_set_rtr_rec_lock`, 커서 복원(`sel_restore_position_for_mysql`)은 이 흐름의 곁가지라 요약만 했다. 잠금 없는 읽기는 [일관 읽기(MVCC)](../../mvcc-read/README.md)에서 다룬다.
