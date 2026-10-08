# row_insert_for_mysql

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**InnoDB 의 삽입 입구이자, 삽입 경로를 두 갈래로 가르는 분기점이다.** 함수 자체는 열 줄이지만, 여기서 고르는 쪽 [06] 이 처음 부르는 `row_get_prebuilt_insert_row` 가 **테이블 핸들마다 한 번 insert 쿼리 그래프를 만들어 `m_prebuilt` 에 캐시한다.** 이 문서는 분기와 함께 그 그래프가 어떤 모양인지를 본다.

## 위치

`storage` / `innobase` / `row` / `row0mysql.cc` L1704-L1713 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L1704-L1713))

## 실제 코드

`storage` / `innobase` / `row` / `row0mysql.cc` L1704-L1713 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L1704-L1713))

```cpp
// row0mysql.cc L1704-L1713
dberr_t row_insert_for_mysql(const byte *mysql_rec, row_prebuilt_t *prebuilt) {
  /* For intrinsic tables there a lot of restrictions that can be
  relaxed including locking of table, transaction handling, etc.
  Use direct cursor interface for inserting to intrinsic tables. */
  if (prebuilt->table->is_intrinsic()) {
    return (row_insert_for_mysql_using_cursor(mysql_rec, prebuilt));
  } else {
    return (row_insert_for_mysql_using_ins_graph(mysql_rec, prebuilt));
  }
}
```

[06] 이 L1559 에서 부르는 그래프 준비 함수다. 이미 만든 그래프가 있고 인덱스 구성이 그대로면 재사용한다.

`storage` / `innobase` / `row` / `row0mysql.cc` L1025-L1093 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0mysql.cc#L1025-L1093))

```cpp
// row0mysql.cc L1025-L1093
static dtuple_t *row_get_prebuilt_insert_row(
    row_prebuilt_t *prebuilt) /*!< in: prebuilt struct in MySQL
                              handle */
{
  dict_table_t *table = prebuilt->table;

  ut_ad(prebuilt && table && prebuilt->trx);

  if (prebuilt->ins_node != nullptr) {
    prebuilt->ins_node->ins_multi_val_pos = 0;

    /* Check if indexes have been dropped or added and we
    may need to rebuild the row insert template. */

    if (prebuilt->trx_id == table->def_trx_id &&
        UT_LIST_GET_LEN(prebuilt->ins_node->entry_list) ==
            UT_LIST_GET_LEN(table->indexes)) {
      return (prebuilt->ins_node->row);
    }

    ut_ad(prebuilt->trx_id < table->def_trx_id);

    que_graph_free_recursive(prebuilt->ins_graph);

    prebuilt->ins_graph = nullptr;
  }

  /* Create an insert node and query graph to the prebuilt struct */

  ins_node_t *node;

  node = ins_node_create(INS_DIRECT, table, prebuilt->heap);

  prebuilt->ins_node = node;

  if (prebuilt->ins_upd_rec_buff == nullptr) {
    prebuilt->ins_upd_rec_buff = static_cast<byte *>(
        mem_heap_alloc(prebuilt->heap, prebuilt->mysql_row_len));
  }

  // ... (L1065-L1072 생략: multi-value 열 버퍼 할당)

  /* option 1 : HERE create the insert node as per row version now on disk */
  dtuple_t *row;

  row = dtuple_create_with_vcol(prebuilt->heap, table->get_n_cols(),
                                dict_table_get_n_v_cols(table));

  dict_table_copy_types(row, table);

  ins_node_set_new_row(node, row);

  prebuilt->ins_graph = static_cast<que_fork_t *>(
      que_node_get_parent(pars_complete_graph_for_exec(
          node, prebuilt->trx, prebuilt->heap, prebuilt)));

  prebuilt->ins_graph->state = QUE_FORK_ACTIVE;

  prebuilt->trx_id = table->def_trx_id;

  return (prebuilt->ins_node->row);
}
```

insert 노드의 초기값이다. 처음 상태는 `INS_NODE_SET_IX_LOCK` 이다.

`storage` / `innobase` / `row` / `row0ins.cc` L81-L110 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L81-L110))

```cpp
// row0ins.cc L81-L110
ins_node_t *ins_node_create(
    ulint ins_type,      /*!< in: INS_VALUES, ... */
    dict_table_t *table, /*!< in: table where to insert */
    mem_heap_t *heap)    /*!< in: mem heap where created */
{
  ins_node_t *node;

  node = static_cast<ins_node_t *>(mem_heap_alloc(heap, sizeof(ins_node_t)));

  node->common.type = QUE_NODE_INSERT;

  node->ins_type = ins_type;

  node->state = INS_NODE_SET_IX_LOCK;
  node->table = table;
  node->index = nullptr;
  node->entry = nullptr;

  node->select = nullptr;

  node->trx_id = 0;

  node->entry_sys_heap = mem_heap_create(128, UT_LOCATION_HERE);

  node->magic_n = INS_NODE_MAGIC_N;

  node->ins_multi_val_pos = 0;

  return (node);
}
```

노드에 행 틀을 붙이면서 인덱스마다 엔트리 틀을 만들고, 숨은 시스템 열 자리를 잡는다.

`storage` / `innobase` / `row` / `row0ins.cc` L113-L134 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L113-L134))

```cpp
// row0ins.cc L113-L134
static void ins_node_create_entry_list(
    ins_node_t *node) /*!< in: row insert node */
{
  dict_index_t *index;
  dtuple_t *entry;

  ut_ad(node->entry_sys_heap);

  UT_LIST_INIT(node->entry_list);

  /* We will include all indexes (include those corrupted
  secondary indexes) in the entry list. Filteration of
  these corrupted index will be done in row_ins() */

  for (index = node->table->first_index(); index != nullptr;
       index = index->next()) {
    entry = row_build_index_entry_low(
        node->row, nullptr, index, node->entry_sys_heap, ROW_BUILD_FOR_INSERT);

    UT_LIST_ADD_LAST(node->entry_list, entry);
  }
}
```

`storage` / `innobase` / `row` / `row0ins.cc` L194-L218 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L194-L218))

```cpp
// row0ins.cc L194-L218
void ins_node_set_new_row(
    ins_node_t *node, /*!< in: insert node */
    dtuple_t *row)    /*!< in: new row (or first row) for the node */
{
  node->state = INS_NODE_SET_IX_LOCK;
  node->index = nullptr;
  node->entry = nullptr;

  node->row = row;

  mem_heap_empty(node->entry_sys_heap);

  /* Create templates for index entries */

  ins_node_create_entry_list(node);

  /* Allocate from entry_sys_heap buffers for sys fields */

  row_ins_alloc_sys_fields(node);

  /* As we allocated a new trx id buf, the trx id should be written
  there again: */

  node->trx_id = 0;
}
```

그래프의 뼈대는 fork 하나, thr 하나, 그 아래 insert 노드 하나다.

`storage` / `innobase` / `pars` / `pars0pars.cc` L1734-L1754 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/pars/pars0pars.cc#L1734-L1754))

```cpp
// pars0pars.cc L1734-L1754
que_thr_t *pars_complete_graph_for_exec(que_node_t *node, trx_t *trx,
                                        mem_heap_t *heap,
                                        row_prebuilt_t *prebuilt) {
  que_fork_t *fork;
  que_thr_t *thr;

  fork = que_fork_create(nullptr, nullptr, QUE_FORK_MYSQL_INTERFACE, heap);
  fork->trx = trx;

  thr = que_thr_create(fork, heap, prebuilt);

  thr->child = node;

  if (node) {
    que_node_set_parent(node, thr);
  }

  trx->graph = nullptr;

  return (thr);
}
```

## 동작 흐름

```text
 L1708  prebuilt->table->is_intrinsic()   (내부 임시 테이블)
          yes  L1709  row_insert_for_mysql_using_cursor     그래프 없이 커서로 바로
          no   L1711  [06] row_insert_for_mysql_using_ins_graph

 [06] L1559 -> row_get_prebuilt_insert_row (row0mysql.cc)
   L1033  ins_node 가 이미 있으면
   L1039    prebuilt->trx_id == table->def_trx_id 이고 엔트리 수 == 인덱스 수
              -> 그대로 재사용, return (L1042)
   L1047    아니면 (DDL 로 인덱스가 바뀜) 그래프를 버리고 새로 만든다
   L1056  ins_node_create(INS_DIRECT, ...)       row0ins.cc L81
   L1077  dtuple_create_with_vcol(열 수, 가상 열 수)   행 틀
   L1080  dict_table_copy_types                  열 타입을 틀에 복사
   L1082  ins_node_set_new_row(node, row)        row0ins.cc L194
            L208  ins_node_create_entry_list     인덱스마다 row_build_index_entry_low
            L212  row_ins_alloc_sys_fields       DB_ROW_ID, DB_TRX_ID, DB_ROLL_PTR 자리
   L1084  pars_complete_graph_for_exec           fork 와 thr 를 만들고 노드를 매단다
   L1088  ins_graph->state = QUE_FORK_ACTIVE
   L1090  prebuilt->trx_id = table->def_trx_id   이 그래프가 만들어진 테이블 정의 버전
```

그래프가 만들어진 뒤의 모양이다. 엔트리 틀은 처음에 비어 있고, 행마다 [09] 의 `row_ins_index_entry_set_vals` 가 엔트리 필드의 데이터 포인터를 행 틀의 같은 열 데이터로 맞춘다(`dfield_set_data`, row0ins.cc L3468). 그래서 인덱스별로 값을 복사하지 않고 포인터만 연결한다.

```text
 m_prebuilt 에 붙는 insert 그래프

 prebuilt->ins_graph  que_fork_t (QUE_FORK_MYSQL_INTERFACE, pars0pars.cc L1740)
      |
      +-- que_thr_t   (L1743, 부모는 fork)
            |  child
            v
      prebuilt->ins_node  ins_node_t (QUE_NODE_INSERT, 부모는 thr, L1748)
            state      = INS_NODE_SET_IX_LOCK      (row0ins.cc L94)
            ins_type   = INS_DIRECT                (MySQL 이 행을 직접 만들어 준다)
            row        --> dtuple_t  사용자 열 + 시스템 열 (열 번호는 dict_col_get_no)
            |                시스템 열 DB_ROW_ID   -> node->row_id_buf 가 가리킴 (L167)
            |                시스템 열 DB_TRX_ID   -> node->trx_id_buf 가 가리킴 (L178)
            |                시스템 열 DB_ROLL_PTR -> 같은 버퍼의 뒤쪽 (L187)
            entry_list --> dtuple_t (PRIMARY 용)  -> dtuple_t (idx_a 용) -> ...
                           table->indexes 순서 그대로, 첫 원소가 클러스터드
            index, entry   [08] 이 지금 넣고 있는 인덱스와 엔트리
            entry_sys_heap entry_list 와 시스템 열 버퍼가 사는 곳
```

```text
 ins_type 세 가지 (include/row0ins.h L197-L203)

 INS_SEARCHED  0  INSERT INTO ... SELECT   [08] 이 select 노드에서 행을 얻는다 (row0ins.cc L3604)
 INS_VALUES    1  INSERT INTO ... VALUES   [08] 이 values_list 를 평가한다 (row0ins.cc L3607)
 INS_DIRECT    2  -                        행을 따로 만들어 붙인다
 헤더 주석(row0ins.h L202)은 INS_DIRECT 를 dict0crea 내부용이라 적었지만, 이 태그에서
 ins_node_create(INS_DIRECT, ...) 를 부르는 곳은 row0mysql.cc L1056(핸들러 경로)과
 api0api.cc L1084(InnoDB API) 둘뿐이고 dict0crea.cc 에는 없다
```

## 결과가 쓰이는 곳

```text
 prebuilt->ins_graph, prebuilt->ins_node
      --> [06] 이 que_fork_get_first_thr 로 thr 를 꺼내 row_ins_step 을 돌린다
      --> 같은 핸들로 들어오는 다음 행들이 모두 재사용한다

 node->row (행 틀)
      --> [06] row_mysql_convert_row_to_innobase 가 MySQL 행 값을 채운다
      --> [07] 이 DB_TRX_ID 자리에 trx->id 를, [08] 이 DB_ROW_ID 자리에 새 row id 를 쓴다

 node->entry_list
      --> [08] [09] 가 인덱스마다 하나씩 꺼내 값을 채우고 넣는다
```

## 다루지 않는 것

내부 임시 테이블의 커서 경로(`row_insert_for_mysql_using_cursor`, L1405), `row_build_index_entry_low` 가 인덱스 열과 접두 길이를 고르는 규칙, multi-value 인덱스용 버퍼(`mv_data`), 가상 열 필드, `que_fork_create` 와 `que_thr_create` 의 필드들은 곁가지라 줄만 적었다.
