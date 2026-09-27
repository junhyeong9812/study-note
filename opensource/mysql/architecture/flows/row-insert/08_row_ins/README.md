# row_ins

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**한 행을 테이블의 모든 인덱스에 넣는 루프다.** 필요하면 DB_ROW_ID 를 발급하고, `table->indexes` 를 첫 원소(클러스터드)부터 끝까지 돌며 인덱스마다 [09] 를 부른다. 볼거리는 **실패했을 때 `node->index` 를 앞으로 옮기지 않는다**는 점이다. 그래서 잠금 대기 뒤 다시 들어오면 멈췄던 인덱스부터 이어서 한다.

## 위치

`storage` / `innobase` / `row` / `row0ins.cc` L3587-L3650 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3587-L3650))

## 실제 코드

`storage` / `innobase` / `row` / `row0ins.cc` L3587-L3650 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3587-L3650))

```cpp
// row0ins.cc L3587-L3650
[[nodiscard]] static dberr_t row_ins(
    ins_node_t *node, /*!< in: row insert node */
    que_thr_t *thr)   /*!< in: query thread */
{
  dberr_t err;

  DBUG_TRACE;

  DBUG_PRINT("row_ins", ("table: %s", node->table->name.m_name));

  if (node->state == INS_NODE_ALLOC_ROW_ID) {
    row_ins_alloc_row_id_step(node);

    node->index = node->table->first_index();
    node->entry = UT_LIST_GET_FIRST(node->entry_list);

    if (node->ins_type == INS_SEARCHED) {
      row_ins_get_row_from_query_block(node);

    } else if (node->ins_type == INS_VALUES) {
      row_ins_get_row_from_values(node);
    }

    node->state = INS_NODE_INSERT_ENTRIES;
  }

  ut_ad(node->state == INS_NODE_INSERT_ENTRIES);

  while (node->index != nullptr) {
    if (node->index->type != DICT_FTS) {
      err = row_ins_index_entry_step(node, thr);

      switch (err) {
        case DB_SUCCESS:
          break;
        case DB_DUPLICATE_KEY:
          thr_get_trx(thr)->error_state = DB_DUPLICATE_KEY;
          thr_get_trx(thr)->error_index = node->index;
          [[fallthrough]];
        default:
          return err;
      }
    }

    node->index = node->index->next();
    node->entry = UT_LIST_GET_NEXT(tuple_list, node->entry);

    DBUG_EXECUTE_IF("row_ins_skip_sec", node->index = nullptr;
                    node->entry = nullptr; break;);

    /* Skip corrupted secondary index and its entry */
    while (node->index && node->index->is_corrupted()) {
      node->index = node->index->next();
      node->entry = UT_LIST_GET_NEXT(tuple_list, node->entry);
    }
  }

  ut_ad(node->entry == nullptr);

  thr_get_trx(thr)->error_index = nullptr;
  node->state = INS_NODE_ALLOC_ROW_ID;

  return DB_SUCCESS;
}
```

L3598 이 부르는 row id 발급이다. 클러스터드 인덱스가 유니크(= 사용자 PK 가 있음)면 아무것도 하지 않는다.

`storage` / `innobase` / `row` / `row0ins.cc` L3508-L3526 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3508-L3526))

```cpp
// row0ins.cc L3508-L3526
static inline void row_ins_alloc_row_id_step(
    ins_node_t *node) /*!< in: row insert node */
{
  row_id_t row_id;

  ut_ad(node->state == INS_NODE_ALLOC_ROW_ID);

  if (dict_index_is_unique(node->table->first_index())) {
    /* No row id is stored if the clustered index is unique */

    return;
  }

  /* Fill in row id value to row */

  row_id = dict_sys_get_new_row_id();

  dict_sys_write_row_id(node->row_id_buf, row_id);
}
```

## 동작 흐름

```text
 L3597  state == INS_NODE_ALLOC_ROW_ID          새 행의 첫 진입
 L3598    row_ins_alloc_row_id_step
            L3515  클러스터드가 유니크면 return   (PK 가 있는 테이블)
            L3523  row_id = dict_sys_get_new_row_id()     전역 카운터에서 하나
            L3525  node->row_id_buf 에 기록                행의 DB_ROW_ID 칸
 L3600    node->index = first_index()           클러스터드
 L3601    node->entry = entry_list 의 첫 원소
 L3603    INS_SEARCHED / INS_VALUES 면 행을 가져온다 (MySQL 의 INS_DIRECT 는 둘 다 아님)
 L3610    state = INS_NODE_INSERT_ENTRIES

 L3615  while (node->index != nullptr)
 L3616    FTS 인덱스가 아니면
 L3617      err = [09] row_ins_index_entry_step(node, thr)
 L3619      DB_SUCCESS 가 아니면
 L3622        DB_DUPLICATE_KEY 면 trx->error_state, trx->error_index = 이 인덱스
 L3627        return err          node->index 는 이 인덱스에 멈춘 채
 L3631    node->index = 다음 인덱스, node->entry = 다음 엔트리
 L3638    손상된 세컨더리는 엔트리와 함께 건너뛴다

 L3646  error_index = nullptr
 L3647  state = INS_NODE_ALLOC_ROW_ID           다음 행을 위해
 L3649  return DB_SUCCESS
```

인덱스 목록과 엔트리 목록은 같은 순서로 나란히 움직인다. 두 포인터를 한 칸씩 함께 옮기는 것이 이 루프의 전부다.

```text
 PK(id), idx_a(a), idx_b(b) 를 가진 테이블에 (id=7, a=3, b=9) 한 행

 table->indexes     node->entry_list        이 인덱스에 들어가는 엔트리
 PRIMARY    <-----> entry0                  (7, DB_TRX_ID, DB_ROLL_PTR, a=3, b=9)
 idx_a      <-----> entry1                  (a=3, id=7)
 idx_b      <-----> entry2                  (b=9, id=7)
    ^                  ^
    node->index        node->entry          L3631-L3632 에서 함께 다음으로

 클러스터드: 키 열 -> (유니크가 아니면 DB_ROW_ID) -> DB_TRX_ID -> DB_ROLL_PTR -> 나머지 열
             (dict0dict.cc L3032, L3040)
 세컨더리:   자기 열 뒤에 클러스터드 키 n_uniq 개 중 아직 없는 열을 붙인다 (dict0dict.cc L3209-L3215)
```

```text
 PK 유무에 따른 클러스터드 키

 dict_index_is_unique(first_index)
   true   클러스터드 키 = 사용자 키 (예: PRIMARY KEY (id))   L3515 에서 return
   false  클러스터드 키 = DB_ROW_ID                          L3523 에서 발급
```

## 결과가 쓰이는 곳

```text
 node->row_id_buf (DB_ROW_ID)
      --> PK 없는 테이블에서 클러스터드 엔트리의 키가 된다

 trx->error_index
      --> [04] 다음 [02] write_record 의 get_dup_key 가 이 인덱스 번호로 REPLACE / UPDATE 할 행을 찾는다

 node->index 가 멈춘 자리
      --> [06] 의 run_again 이 [07] -> [08] 로 돌아왔을 때 L3615 루프가 여기서 다시 시작한다
```

## 다루지 않는 것

`INS_SEARCHED`, `INS_VALUES` 노드가 쓰는 `row_ins_get_row_from_query_block`, `row_ins_get_row_from_values`, FTS 인덱스 갱신(삽입은 [06] 의 `fts_trx_add_op` 에서 따로 한다), 손상 인덱스 표시(`dict_set_corrupted`)는 곁가지다. `dict_sys_get_new_row_id` 의 카운터 영속화는 이 흐름 밖이다.
