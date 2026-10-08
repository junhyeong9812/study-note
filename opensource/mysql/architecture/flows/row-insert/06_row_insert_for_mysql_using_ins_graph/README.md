# row_insert_for_mysql_using_ins_graph

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**한 행을 InnoDB 쿼리 그래프로 실행하는 운전석이다.** 행을 InnoDB 튜플로 바꾸고, 되돌릴 지점(savepoint)을 잡고, [07] `row_ins_step` 을 부른다. 볼거리는 `run_again` 루프다. 잠금 대기가 나면 이 스레드가 여기서 잠들었다가 깨어나 **같은 노드 상태에서** 다시 돌고, 그 밖의 오류는 savepoint 로 이 행만 되돌린다.

## 위치

`storage` / `innobase` / `row` / `row0mysql.cc` L1500-L1698 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L1500-L1698))

## 실제 코드

테이블 상태 검사다. 이 네 가지 중 하나면 그래프를 돌리지도 않는다.

`storage` / `innobase` / `row` / `row0mysql.cc` L1516-L1551 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L1516-L1551))

```cpp
// row0mysql.cc L1516-L1551
  if (dict_table_is_discarded(prebuilt->table)) {
    ib::error(ER_IB_MSG_976)
        << "The table " << prebuilt->table->name
        << " doesn't have a corresponding tablespace, it was"
           " discarded.";

    return (DB_TABLESPACE_DELETED);

  } else if (prebuilt->table->ibd_file_missing) {
    ib::error(ER_IB_MSG_977)
        << ".ibd file is missing for table " << prebuilt->table->name;

    return (DB_TABLESPACE_NOT_FOUND);

  } else if (srv_force_recovery &&
             !(srv_force_recovery < SRV_FORCE_NO_UNDO_LOG_SCAN &&
               dict_sys_t::is_dd_table_id(prebuilt->table->id))) {
    /* Allow to modify hardcoded DD tables in some scenario to
    make DDL work */

    ib::error(ER_IB_MSG_978) << MODIFICATIONS_NOT_ALLOWED_MSG_FORCE_RECOVERY;

    return (DB_READ_ONLY);
  }

  // ... (L1541-L1546 생략: 디버그용 손상 표시 주입)

  if (table->is_corrupted()) {
    ib::error(ER_IB_MSG_979) << "Table " << table->name << " is corrupt.";
    return (DB_TABLE_CORRUPT);
  }
```

변환, savepoint, 그래프 실행, 오류 처리까지가 이 함수의 몸통이다.

`storage` / `innobase` / `row` / `row0mysql.cc` L1553-L1611 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L1553-L1611))

```cpp
// row0mysql.cc L1553-L1611
  trx->op_info = "inserting";

  row_mysql_delay_if_needed();

  trx_start_if_not_started_xa(trx, true, UT_LOCATION_HERE);

  row_get_prebuilt_insert_row(prebuilt);
  node = prebuilt->ins_node;

  row_mysql_convert_row_to_innobase(node->row, prebuilt, mysql_rec, &temp_heap);

  savept = trx_savept_take(trx);

  thr = que_fork_get_first_thr(prebuilt->ins_graph);

  if (prebuilt->sql_stat_start) {
    node->state = INS_NODE_SET_IX_LOCK;
    prebuilt->sql_stat_start = false;
  } else {
    node->state = INS_NODE_ALLOC_ROW_ID;
  }

  que_thr_move_to_run_state_for_mysql(thr, trx);

run_again:
  thr->run_node = node;
  thr->prev_node = node;

  row_ins_step(thr);

  DEBUG_SYNC_C("ib_after_row_insert_step");

  err = trx->error_state;

  if (err != DB_SUCCESS) {
  error_exit:
    que_thr_stop_for_mysql(thr);

    /* FIXME: What's this ? */
    thr->lock_state = QUE_THR_LOCK_ROW;

    auto was_lock_wait = row_mysql_handle_errors(&err, trx, thr, &savept);

    thr->lock_state = QUE_THR_LOCK_NOLOCK;

    if (was_lock_wait) {
      ut_ad(node->state == INS_NODE_INSERT_ENTRIES ||
            node->state == INS_NODE_ALLOC_ROW_ID);
      goto run_again;
    }

    trx->op_info = "";

    if (temp_heap != nullptr) {
      mem_heap_free(temp_heap);
    }

    return (err);
  }
```

성공 꼬리다. 통계 카운터를 올린다.

`storage` / `innobase` / `row` / `row0mysql.cc` L1676-L1698 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L1676-L1698))

```cpp
// row0mysql.cc L1676-L1698
  que_thr_stop_for_mysql_no_error(thr, trx);

  if (table->is_system_table) {
    srv_stats.n_system_rows_inserted.inc();
  } else {
    srv_stats.n_rows_inserted.inc();
  }

  /* Not protected by dict_table_stats_lock() for performance
  reasons, we would rather get garbage in stat_n_rows (which is
  just an estimate anyway) than protecting the following code
  with a latch. */
  dict_table_n_rows_inc(table);

  row_update_statistics_if_needed(table);
  trx->op_info = "";

  if (temp_heap != nullptr) {
    mem_heap_free(temp_heap);
  }

  return (err);
}
```

L1594 가 부르는 오류 처리기다. 반환값 `true` 는 "잠금을 기다렸고 다시 돌려라"라는 뜻이다.

`storage` / `innobase` / `row` / `row0mysql.cc` L653-L729 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L653-L729))

```cpp
// row0mysql.cc L653-L729
bool row_mysql_handle_errors(
    dberr_t *new_err,     /*!< out: possible new error encountered in
                          lock wait, or if no new error, the value
                          of trx->error_state at the entry of this
                          function */
    trx_t *trx,           /*!< in: transaction */
    que_thr_t *thr,       /*!< in: query thread, or NULL */
    trx_savept_t *savept) /*!< in: savepoint, or NULL */
{
  dberr_t err;

handle_new_error:
  err = trx->error_state;

  ut_a(err != DB_SUCCESS);

  trx->error_state = DB_SUCCESS;

  switch (err) {
    case DB_LOCK_WAIT_TIMEOUT:
      if (row_rollback_on_timeout) {
        trx_rollback_to_savepoint(trx, nullptr);
        break;
      }
      [[fallthrough]];
    case DB_DUPLICATE_KEY:
    // ... (L679-L697 생략: 같은 처리(savepoint 롤백)를 받는 나머지 오류 코드와 디버그 훅)
      if (savept) {
        /* Roll back the latest, possibly incomplete insertion
        or update */

        trx_rollback_to_savepoint(trx, savept);
      }
      /* MySQL will roll back the latest SQL statement */
      break;
    case DB_LOCK_WAIT:

      trx_kill_blocking(trx);
      DEBUG_SYNC_C("before_lock_wait_suspend");

      lock_wait_suspend_thread(thr);

      if (trx->error_state != DB_SUCCESS) {
        que_thr_stop_for_mysql(thr);

        goto handle_new_error;
      }

      *new_err = err;

      return (true);

    case DB_DEADLOCK:
    case DB_LOCK_TABLE_FULL:
      /* Roll back the whole transaction; this resolution was added
      to version 3.23.43 */

      trx_rollback_to_savepoint(trx, nullptr);
      break;
```

## 동작 흐름

```text
 L1516  DB_TABLESPACE_DELETED     discard 된 테이블스페이스
 L1524  DB_TABLESPACE_NOT_FOUND   .ibd 파일 없음
 L1530  DB_READ_ONLY              innodb_force_recovery 중 (일부 DD 테이블 예외)
 L1548  DB_TABLE_CORRUPT          손상된 테이블

 L1553  trx->op_info = "inserting"    트랜잭션 출력에 찍히는 문구 (trx0trx.cc L2558)
 L1555  row_mysql_delay_if_needed     srv_dml_needed_delay 가 0 이 아니면 그만큼 잔다 (L141)
 L1557  trx_start_if_not_started_xa   트랜잭션을 여기서 시작할 수도 있다
 L1559  row_get_prebuilt_insert_row   그래프 준비 ([05])
 L1562  row_mysql_convert_row_to_innobase(node->row, prebuilt, mysql_rec)
 L1564  savept = trx_savept_take(trx) 이 행을 넣기 직전의 undo 번호
 L1566  thr = 그래프의 첫 thr
 L1568  문장의 첫 행이면 state = INS_NODE_SET_IX_LOCK, 아니면 INS_NODE_ALLOC_ROW_ID
 L1575  que_thr_move_to_run_state_for_mysql

 L1577  run_again:
 L1578    thr->run_node = node, prev_node = node
 L1581    [07] row_ins_step(thr)
 L1585    err = trx->error_state
 L1587    err != DB_SUCCESS
 L1589      que_thr_stop_for_mysql
 L1594      was_lock_wait = row_mysql_handle_errors(&err, trx, thr, &savept)
 L1598      잠금 대기였으면 goto run_again
 L1610      아니면 err 를 돌려준다

 L1613  FTS 인덱스가 있으면 문서 ID 검사와 fts_trx_add_op
 L1676  que_thr_stop_for_mysql_no_error
 L1681  srv_stats.n_rows_inserted++      상태 변수 rows_inserted (ha_innodb.cc L1286)
        (L1679 시스템 테이블이면 n_system_rows_inserted 쪽)
 L1688  dict_table_n_rows_inc           통계용 행 수 추정치
 L1690  row_update_statistics_if_needed  바뀐 행이 많으면 통계 재계산 예약
```

잠금 대기는 오류가 아니라 대기다. 이 스레드가 잠드는 곳은 [07] 안이 아니라 여기서 부르는 처리기 안이고, 깨어난 뒤 같은 `thr` 와 같은 `node` 로 다시 들어간다.

```text
 잠금 대기 한 번 (연결 스레드 T 의 시간축)

 T  L1581  row_ins_step -> ... -> lock_rec_insert_check_and_lock 가 대기 요청을 큐에 넣음
           trx->error_state = DB_LOCK_WAIT, row_ins_step 이 nullptr 을 돌려준다
 T  L1594  row_mysql_handle_errors
             L706  case DB_LOCK_WAIT
             L708  trx_kill_blocking
             L711  lock_wait_suspend_thread(thr)     여기서 잠든다  --> [레코드 잠금과 교착]
                   (다른 트랜잭션이 커밋해 잠금을 풀면 깨어난다)
             L713  깨어난 뒤 error_state 가 또 오류면 (타임아웃, 교착 희생) handle_new_error 로
             L721  return true
 T  L1601  goto run_again
 T  L1581  row_ins_step 다시.
           node->state 는 INS_NODE_INSERT_ENTRIES, node->index 는 대기했던 인덱스 그대로
           그래서 이미 넣은 앞쪽 인덱스는 다시 넣지 않는다
           (L1599 assert 는 INS_NODE_ALLOC_ROW_ID 도 허용한다. 테이블 IX 잠금 대기면
            [07] L3697 이 lock_table 전에 state 를 이미 ALLOC_ROW_ID 로 바꿔 두기 때문이다)
```

```text
 오류별 되돌림 범위 (row_mysql_handle_errors)

 L706        DB_LOCK_WAIT                            되돌리지 않고 기다린 뒤 재실행
 L672-L674   DB_LOCK_WAIT_TIMEOUT                    innodb_rollback_on_timeout 이면 트랜잭션 전체,
                                                     아니면 아래 줄과 같다
 L678-L703   DB_DUPLICATE_KEY, DB_TOO_BIG_RECORD ... savept 까지 (이 행만)
 L723-L728   DB_DEADLOCK, DB_LOCK_TABLE_FULL         트랜잭션 전체
 L732        DB_MUST_GET_MORE_FILE_SPACE             ib::fatal
```

## 결과가 쓰이는 곳

```text
 반환값 dberr_t
      --> [04] ha_innobase::write_row 가 convert_error_code_to_mysql 로 바꾼다

 savept (trx_savept_t)
      --> 부분 실패 때 trx_rollback_to_savepoint 가 이 지점 이후의 undo 를 적용한다
          클러스터드에 들어간 레코드와 앞쪽 세컨더리 엔트리가 여기서 지워진다

 trx->op_info, srv_stats.n_rows_inserted
      --> 트랜잭션 출력(trx0trx.cc L2558)과 상태 변수 rows_inserted (ha_innodb.cc L1286)
```

## 다루지 않는 것

FTS 문서 ID 검사와 FTS 캐시 추가(L1613-L1674), `row_mysql_convert_row_to_innobase` 의 열 변환, `row_mysql_delay_if_needed` 의 지연 계산, `lock_wait_suspend_thread` 의 대기 슬롯과 타임아웃은 곁가지다. 잠금 대기는 [레코드 잠금과 교착](../../record-lock/README.md)에서 다룬다.
