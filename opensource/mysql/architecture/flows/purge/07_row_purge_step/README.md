# row_purge_step

상위: [purge](../README.md)

**purge 그룹 하나를 query graph 의 한 걸음씩 처리하는 자리다.** 한 번 불릴 때마다 노드의 레코드 목록(`node->recs`)에서 undo 레코드 하나를 꺼내 `row_purge` 로 처리하고, 목록이 남았으면 다음 걸음에서 다시 자기를 부르도록 `run_node` 를 그대로 둔다. 목록이 비면 `row_purge_end` 로 노드를 정리하고 부모로 돌아간다. 실제 해석은 `row_purge_parse_undo_rec` 가 한다. undo 레코드에서 종류와 테이블 id 를 읽고, 테이블을 열고(MDL 포함), 클러스터드 키(`node->ref`)와 갱신 벡터, 인덱스에 필요한 열만 담은 부분 행(`node->row`)을 만든다. 테이블이 이미 지워졌거나, 임시 테이블이거나, 인덱스를 고칠 일이 없는 갱신이면 여기서 false 를 돌려주고 그 레코드는 끝난다.

## 위치

`storage` / `innobase` / `row` / `row0purge.cc` L1210-L1250 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L1210-L1250))

## 실제 코드

한 걸음이다. 노드의 상태를 초기화하고 레코드 하나를 처리한다.

`storage` / `innobase` / `row` / `row0purge.cc` L1206-L1250 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L1206-L1250))

```cpp
// row0purge.cc L1206-L1250
/** Does the purge operation for a single undo log record. This is a high-level
function used in an SQL execution graph.
@param[in,out]  thr             The query thread to execute
@return query thread to run next or nullptr */
que_thr_t *row_purge_step(que_thr_t *thr) {
  purge_node_t *node;

  node = static_cast<purge_node_t *>(thr->run_node);

  node->table = nullptr;
  node->row = nullptr;
  node->ref = nullptr;
  node->index = nullptr;
  node->update = nullptr;
  node->found_clust = false;
  node->rec_type = ULINT_UNDEFINED;
  node->cmpl_info = ULINT_UNDEFINED;

  ut_a(!node->done);

  ut_ad(que_node_get_type(node) == QUE_NODE_PURGE);

  if (node->recs != nullptr && !node->recs->empty()) {
    purge_node_t::rec_t rec;

    rec = node->recs->front();
    node->recs->pop_front();

    node->roll_ptr = rec.roll_ptr;
    node->modifier_trx_id = rec.modifier_trx_id;

    row_purge(node, rec.undo_rec, thr);

    if (node->recs->empty()) {
      row_purge_end(thr);
    } else {
      thr->run_node = node;
    }

  } else {
    row_purge_end(thr);
  }

  return (thr);
}
```

레코드 하나의 처리다. 해석이 true 면 [08] 로 지우고, 공간 부족 등으로 못 지웠으면 1초 뒤 다시 해석부터 한다.

`storage` / `innobase` / `row` / `row0purge.cc` L1146-L1174 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L1146-L1174))

```cpp
// row0purge.cc L1146-L1174
/** Fetches an undo log record and does the purge for the recorded operation.
 If none left, or the current purge completed, returns the control to the
 parent node, which is always a query thread node. */
static void row_purge(purge_node_t *node,       /*!< in: row purge node */
                      trx_undo_rec_t *undo_rec, /*!< in: record to purge */
                      que_thr_t *thr)           /*!< in: query thread */
{
  bool updated_extern;
  THD *thd = current_thd;

  DBUG_EXECUTE_IF(
      "do_not_meta_lock_in_background",
      while (srv_shutdown_state.load() < SRV_SHUTDOWN_PURGE) {
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
      } return;);

  while (row_purge_parse_undo_rec(node, undo_rec, &updated_extern, thd, thr)) {
    bool purged;

    purged = row_purge_record(node, undo_rec, thr, updated_extern, thd);

    if (purged || srv_shutdown_state.load() >= SRV_SHUTDOWN_PURGE) {
      return;
    }

    /* Retry the purge in a second. */
    std::this_thread::sleep_for(std::chrono::seconds(1));
  }
}
```

해석의 앞부분이다. 갱신으로 되살린 delete-mark 레코드(`TRX_UNDO_UPD_DEL_REC`)는 외부 저장 열이 바뀌지 않았으면 할 일이 없다.

`storage` / `innobase` / `row` / `row0purge.cc` L843-L871 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L843-L871))

```cpp
// row0purge.cc L843-L871
static bool row_purge_parse_undo_rec(purge_node_t *node,
                                     trx_undo_rec_t *undo_rec,
                                     bool *updated_extern, THD *thd,
                                     que_thr_t *thr) {
  dict_index_t *clust_index;
  const byte *ptr;
  undo_no_t undo_no;
  table_id_t table_id;
  trx_id_t trx_id;
  roll_ptr_t roll_ptr;
  ulint info_bits;
  ulint type;
  type_cmpl_t type_cmpl;

  ut_ad(node != nullptr);
  ut_ad(thr != nullptr);

  ptr = trx_undo_rec_get_pars(undo_rec, &type, &node->cmpl_info, updated_extern,
                              &undo_no, &table_id, type_cmpl);

  node->rec_type = type;

  if (type == TRX_UNDO_UPD_DEL_REC && !*updated_extern) {
    return (false);
  }

  ptr = trx_undo_update_rec_get_sys_cols(ptr, &trx_id, &roll_ptr, &info_bits);
  node->table = nullptr;
  node->trx_id = trx_id;
```

해석의 끝부분이다. 키 열을 바꾸지 않은 갱신은 인덱스를 고칠 일이 없으니 테이블을 닫고 끝낸다. 나머지는 클러스터드 키, 갱신 벡터, 부분 행을 읽는다.

`storage` / `innobase` / `row` / `row0purge.cc` L1045-L1065 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0purge.cc#L1045-L1065))

```cpp
// row0purge.cc L1045-L1065
  if (type == TRX_UNDO_UPD_EXIST_REC &&
      (node->cmpl_info & UPD_NODE_NO_ORD_CHANGE) && !*updated_extern) {
    /* Purge requires no changes to indexes: we may return */
    goto close_exit;
  }

  ptr = trx_undo_rec_get_row_ref(ptr, clust_index, &(node->ref), node->heap);

  ptr = trx_undo_update_rec_get_update(ptr, clust_index, type, trx_id, roll_ptr,
                                       info_bits, node->heap, &(node->update),
                                       nullptr, type_cmpl);

  /* Read to the partial row the fields that occur in indexes */

  if (!(node->cmpl_info & UPD_NODE_NO_ORD_CHANGE)) {
    ptr = trx_undo_rec_get_partial_row(
        ptr, clust_index, &node->row, type == TRX_UNDO_UPD_DEL_REC, node->heap);
  }

  return (true);
}
```

## 동작 흐름

```text
 row_purge_step(thr)
 L1215  node 의 table, row, ref, index, update, found_clust, rec_type 초기화
 L1228  recs 가 남았으면
 L1231    rec = recs.front(), pop_front
 L1234    node->roll_ptr = rec.roll_ptr          이 undo 레코드의 위치 ([09] 가 레코드와 비교한다)
 L1235    node->modifier_trx_id
 L1237    row_purge(node, rec.undo_rec, thr)
 L1239    비었으면 row_purge_end, 아니면 run_node = node (다음 걸음도 여기로)
 L1246  처음부터 비어 있었으면 row_purge_end
 L1249  return thr

 row_purge(node, undo_rec, thr)
 L1162  while (row_purge_parse_undo_rec(...))
 L1165    purged = [08] row_purge_record
 L1167    purged 이거나 종료 중이면 return
 L1172    아니면 1초 자고 다시 해석부터
```

해석 함수가 false 를 돌려주는 길이 여럿이다. 그 길들이 "purge 할 것이 없는 undo" 를 거른다.

```text
 row_purge_parse_undo_rec (L843) 의 길

 L860   trx_undo_rec_get_pars                type, cmpl_info, updated_extern, undo_no, table_id
 L865   UPD_DEL_REC 이고 외부 저장 변경 없음          -> false
 L869   옛 DB_TRX_ID, 옛 DB_ROLL_PTR, info_bits
 L880   서버가 다 뜨기 전이면 1초씩 기다린다 (데이터 사전을 못 연다)
 L892   SDI 테이블이면 SDI 용 MDL 로 연다
 L912   아니면 dd_table_open_on_id 를 MDL 과 함께 (L917)
 L919     임시 테이블                                -> false (임시 테이블은 purge 하지 않는다)
 L952   테이블이 이미 DROP 됐다                      -> false
 L996   임시 테이블 (두 번째 확인)                    -> false
 L1000  .ibd 파일이 없다                             -> false
 L1021  클러스터드 인덱스가 없거나 손상               -> false
 L1045  UPD_EXIST_REC 이고 키 열 변경 없음, 외부 저장 변경 없음  -> false
 L1051  node->ref    = 클러스터드 키 (undo 의 PK 열)
 L1053  node->update = 갱신 벡터
 L1059  키 열이 바뀌었으면 node->row = 인덱스에 쓰이는 열만 담은 부분 행
 L1064  true
```

```text
 노드에 남는 것 (한 레코드 동안)

 node->table, node->mdl     열린 테이블과 MDL. [08] 끝에서 닫는다
 node->ref                  어느 클러스터드 레코드인가 (PK)
 node->roll_ptr             이 undo 레코드의 위치. 레코드의 DB_ROLL_PTR 과 같아야 지운다 ([09])
 node->trx_id               옛 DB_TRX_ID
 node->row                  세컨더리 엔트리를 다시 만들 재료 ([09] 의 row_build_index_entry_low)
 node->rec_type             DEL_MARK_REC / UPD_EXIST_REC / UPD_DEL_REC
```

## 결과가 쓰이는 곳

```text
 해석이 끝난 node
      --> [08] row_purge_record_func 가 rec_type 으로 갈래를 고른다
 row_purge_end
      --> node->done = true. [05] 가 다음 배치에서 이 노드를 다시 쓴다 (ut_a(node->done))
```

## 다루지 않는 것

SDI 테이블과 전문 검색 보조 테이블(FTS aux)을 여는 분기, `INNODB_DD_VC_SUPPORT` 의 가상 열 템플릿, `trx_undo_rec_get_partial_row` 가 어떤 열을 담는지, MDL 의 종류는 이 흐름의 곁가지라 줄만 적었다.
