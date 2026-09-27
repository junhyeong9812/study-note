# row_ins_step

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**쿼리 그래프에서 insert 노드가 한 번 실행될 때 부르는 함수다.** 두 가지를 먼저 한다. 행의 DB_TRX_ID 칸에 이 트랜잭션의 id 를 적고, 문장의 첫 행이면 테이블에 IX 잠금을 건다. 그다음 [08] `row_ins` 로 인덱스 삽입을 맡기고, 결과를 `trx->error_state` 에 남긴 뒤 다음에 돌 노드를 돌려준다.

## 위치

`storage` / `innobase` / `row` / `row0ins.cc` L3655-L3762 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3655-L3762))

## 실제 코드

`storage` / `innobase` / `row` / `row0ins.cc` L3655-L3762 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3655-L3762))

```cpp
// row0ins.cc L3655-L3762
que_thr_t *row_ins_step(que_thr_t *thr) /*!< in: query thread */
{
  ins_node_t *node;
  que_node_t *parent;
  sel_node_t *sel_node;
  trx_t *trx;
  dberr_t err;

  ut_ad(thr);

  DEBUG_SYNC_C("innodb_row_ins_step_enter");

  trx = thr_get_trx(thr);

  trx_start_if_not_started_xa(trx, true, UT_LOCATION_HERE);

  node = static_cast<ins_node_t *>(thr->run_node);

  ut_ad(que_node_get_type(node) == QUE_NODE_INSERT);
  ut_ad(!node->table->is_intrinsic());

  parent = que_node_get_parent(node);
  sel_node = node->select;

  if (thr->prev_node == parent) {
    node->state = INS_NODE_SET_IX_LOCK;
  }

  /* If this is the first time this node is executed (or when
  execution resumes after wait for the table IX lock), set an
  IX lock on the table and reset the possible select node. MySQL's
  partitioned table code may also call an insert within the same
  SQL statement AFTER it has used this table handle to do a search.
  This happens, for example, when a row update moves it to another
  partition. In that case, we have already set the IX lock on the
  table during the search operation, and there is no need to set
  it again here. But we must write trx->id to node->trx_id_buf. */

  memset(node->trx_id_buf, 0, DATA_TRX_ID_LEN);
  trx_write_trx_id(node->trx_id_buf, trx->id);

  if (node->state == INS_NODE_SET_IX_LOCK) {
    node->state = INS_NODE_ALLOC_ROW_ID;

    /* It may be that the current session has not yet started
    its transaction, or it has been committed: */

    if (trx->id == node->trx_id) {
      /* No need to do IX-locking */

      goto same_trx;
    }

    err = lock_table(0, node->table, LOCK_IX, thr);

    DBUG_EXECUTE_IF("ib_row_ins_ix_lock_wait", err = DB_LOCK_WAIT;);

    if (err != DB_SUCCESS) {
      goto error_handling;
    }

    node->trx_id = trx->id;
  same_trx:
    if (node->ins_type == INS_SEARCHED) {
      /* Reset the cursor */
      sel_node->state = SEL_NODE_OPEN;

      /* Fetch a row to insert */

      thr->run_node = sel_node;

      return (thr);
    }
  }

  if ((node->ins_type == INS_SEARCHED) && (sel_node->state != SEL_NODE_FETCH)) {
    ut_ad(sel_node->state == SEL_NODE_NO_MORE_ROWS);

    /* No more rows to insert */
    thr->run_node = parent;

    return (thr);
  }

  /* DO THE CHECKS OF THE CONSISTENCY CONSTRAINTS HERE */

  err = row_ins(node, thr);

error_handling:
  trx->error_state = err;

  if (err != DB_SUCCESS) {
    /* err == DB_LOCK_WAIT or SQL error detected */
    return (nullptr);
  }

  /* DO THE TRIGGER ACTIONS HERE */

  if (node->ins_type == INS_SEARCHED) {
    /* Fetch a row to insert */

    thr->run_node = sel_node;
  } else {
    thr->run_node = que_node_get_parent(node);
  }

  return (thr);
}
```

## 동작 흐름

```text
 L3669  trx_start_if_not_started_xa     아직 시작 전이면 여기서 시작 (trx->id 가 생긴다)
 L3671  node = thr->run_node            [06] 이 L1578 에서 넣어 둔 insert 노드
 L3676  parent = 노드의 부모             MySQL 경로에서는 thr ([05] 의 그래프 그림)
 L3679  thr->prev_node == parent 면 state = INS_NODE_SET_IX_LOCK
          [06] 은 prev_node = node 로 부르므로 이 줄은 타지 않는다.
          MySQL 경로에서 첫 행 여부는 [06] L1568 이 state 로 정해서 넘긴다

 L3694  node->trx_id_buf = trx->id      행의 DB_TRX_ID 칸. 모든 인덱스 엔트리가 이 값을 본다
 L3696  state == INS_NODE_SET_IX_LOCK
 L3697    state = INS_NODE_ALLOC_ROW_ID
 L3702    trx->id == node->trx_id        이 트랜잭션이 이미 이 노드로 IX 를 잡았다
            -> same_trx 로 건너뜀
 L3708    lock_table(0, table, LOCK_IX, thr)       lock0lock.cc L3534
 L3712    실패 (DB_LOCK_WAIT 등) -> error_handling
 L3716    node->trx_id = trx->id
 L3718    INS_SEARCHED 면 select 노드로 가서 행을 가져온다 (MySQL 경로 아님)

 L3741  err = [08] row_ins(node, thr)
 L3744  trx->error_state = err
 L3746  실패면 return nullptr            [06] 이 error_state 를 읽고 처리한다
 L3758  성공이면 run_node = 부모 (thr),  return thr
```

`node->trx_id` 는 "이 노드로 IX 잠금을 잡은 마지막 트랜잭션"이다. 그래프는 핸들에 캐시되어 여러 트랜잭션이 이어서 쓰므로, 이 비교가 트랜잭션이 바뀌었는지를 알려 준다.

```text
 같은 핸들, 두 트랜잭션 (autocommit INSERT 두 번)

 stmt  row  trx->id  state from [06]  node->trx_id  결과
 1     1    100      SET_IX_LOCK      0             L3702 다름 -> L3708 IX 잡음, trx_id=100
 1     2    100      ALLOC_ROW_ID     100           L3696 조건 거짓, 그냥 진행
 2     1    101      SET_IX_LOCK      100           L3702 다름 -> L3708 IX 잡음, trx_id=101

 trx->id 가 바뀌면 L3702 비교가 거짓이 되어 새 트랜잭션이 lock_table 을 다시 부른다
```

```text
 이 함수가 돌려주는 것

 return          trx->error_state     [06] 의 해석
 thr             DB_SUCCESS           행 하나 끝, que_thr_stop_for_mysql_no_error
 nullptr         DB_LOCK_WAIT         lock_table 이나 레코드 잠금 대기 -> 잠들고 run_again
 nullptr         그 밖의 오류         row_mysql_handle_errors 가 되돌림 범위를 정한다
```

## 결과가 쓰이는 곳

```text
 node->trx_id_buf (행의 DB_TRX_ID)
      --> [09] 의 set_vals 가 클러스터드 엔트리에 연결하고
          레코드에 그대로 들어가 [일관 읽기(MVCC)] 의 가시성 판정 재료가 된다

 테이블 IX 잠금
      --> [B+Tree 삽입과 분할] 의 lock_rec_insert_check_and_lock 이 이것을 전제로 한다
          (lock0lock.cc L5085 의 assert lock_table_has(trx, index->table, LOCK_IX))

 trx->error_state
      --> [06] L1585
```

## 다루지 않는 것

`INS_SEARCHED` 노드의 select 노드 연동(MySQL 핸들러 경로는 `INS_DIRECT` 라 타지 않는다), `lock_table` 의 테이블 잠금 호환표와 대기는 이 흐름 밖이다. 테이블 잠금은 [레코드 잠금과 교착](../../record-lock/README.md)의 곁가지로 다룬다.
