# 행 쓰기 (handler -> row0ins)

상위: [MySQL 아키텍처 지도](../../README.md)

`INSERT ... VALUES` 한 문장이 **서버 계층의 행 버퍼(`record[0]`)에서 출발해 InnoDB 의 인덱스마다 하나씩 들어갈 엔트리로 바뀌기까지**의 흐름이다. 서버 쪽은 행마다 `write_record` -> `handler::ha_write_row` 를 부르고, 그 아래는 스토리지 엔진 인터페이스라는 **콜백 경계**다. 경계 너머 `ha_innobase::write_row` 는 MySQL 형식의 행을 InnoDB 튜플(`dtuple_t`)로 바꾸고, 미리 만들어 둔 **쿼리 그래프(`que_fork_t` -> `que_thr_t` -> `ins_node_t`)** 를 한 번 돌린다. 그래프의 insert 노드는 테이블 IX 잠금을 잡은 뒤 **클러스터드 인덱스부터 세컨더리 인덱스 순서로** 엔트리를 하나씩 넣는데, 인덱스마다 먼저 리프 래치만으로(`BTR_MODIFY_LEAF`) 해 보고 페이지가 모자라면(`DB_FAIL`) 트리 래치를 잡고(`BTR_MODIFY_TREE`) 다시 한다. 스레드 경계는 없다. 전부 연결 스레드에서 돈다. 흐름은 [10] `row_ins_clust_index_entry` 와 [11] `row_ins_sec_index_entry` 가 `_low` 함수를 부르는 자리에서 [B+Tree 삽입과 분할](../btree-insert/README.md)로 넘어간다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 서버 계층 (sql/)
 ------------------------------------------------------------------
 [01] Sql_cmd_insert_values::execute_inner       sql_insert.cc L482
      +-- ha_start_bulk_insert                   L603   문장 단위 준비 한 번
      +-- for (values : insert_many_values)      L622   행 하나씩
      |     restore_record(default_values)       L626
      |     fill_record_n_invoke_before_triggers L635   값 채우기 + BEFORE 트리거
      |     CHECK 제약, SQL 계층 FK 검사          L663, L673
      |     +-- [02] write_record                L684
      |           +-- [03] handler::ha_write_row handler.cc L8198
      |                 +-- write_row(buf)       L8215  --> 엔진 (가상 함수)
      |                 +-- binlog_log_row       L8219  행 이벤트를 binlog 캐시에
      +-- ha_end_bulk_insert                     L706
      +-- binlog_query, my_ok                    L757, L796
 ------------------------------------------------------------------
                 콜백 경계 (handler 가상 함수 -> ha_innobase)
 ------------------------------------------------------------------
 InnoDB (storage/innobase/)
 [04] ha_innobase::write_row                     ha_innodb.cc L9256
      +-- update_auto_increment                  L9308  AUTO_INCREMENT 값 결정
      +-- build_template                         L9338  MySQL <-> InnoDB 열 변환표
      +-- [05] row_insert_for_mysql              L9348  row0mysql.cc L1704
            +-- [06] row_insert_for_mysql_using_ins_graph   L1500
                  +-- row_get_prebuilt_insert_row  L1559  그래프가 없으면 여기서 만든다
                  +-- row_mysql_convert_row_to_innobase L1562  record -> node->row
                  +-- trx_savept_take              L1564  이 행 하나의 되돌릴 지점
                  +-- run_again:
                  |   [07] row_ins_step            L1581  row0ins.cc L3655
                  |     +-- lock_table(LOCK_IX)    L3708  문장의 첫 행에서만
                  |     +-- [08] row_ins           L3741  row0ins.cc L3587
                  |           +-- row_ins_alloc_row_id_step L3598  PK 없으면 DB_ROW_ID
                  |           +-- while (node->index)       L3615  인덱스마다
                  |                 [09] row_ins_index_entry_step  L3617
                  |                   +-- set_vals          L3491  row -> 이 인덱스 엔트리
                  |                   +-- row_ins_index_entry L3499
                  |                         +-- [10] row_ins_clust_index_entry L3119  첫 인덱스
                  |                         +-- [11] row_ins_sec_index_entry   L3204  나머지
                  |                               LEAF 시도 -> DB_FAIL 이면 TREE 재시도
                  |                               --> [B+Tree 삽입과 분할]
                  +-- 오류면 row_mysql_handle_errors L1594
                        DB_LOCK_WAIT 는 잠든 뒤 goto run_again (L1601)
```

InnoDB 안쪽에서 한 행이 지나는 상태는 `ins_node_t::state` 세 값이다. 이 값이 "어디부터 다시 할지"를 기억하므로 잠금 대기 뒤에 같은 행을 처음부터 다시 하지 않는다.

```text
 ins_node_t::state (한 행 기준)

   INS_NODE_SET_IX_LOCK         문장의 첫 행이면 [06] L1569 에서 이 값으로 시작
        |  [07] L3697  테이블 IX 잠금 (같은 트랜잭션이 이미 잡았으면 건너뜀 L3702)
        v
   INS_NODE_ALLOC_ROW_ID        두 번째 행부터는 [06] L1572 에서 바로 이 값
        |  [08] L3598  DB_ROW_ID 발급, node->index = 첫 인덱스 (L3600)
        v
   INS_NODE_INSERT_ENTRIES      [08] L3610
        |  인덱스마다 엔트리 삽입. 실패하면 node->index 가 실패한 인덱스에 멈춰 있다
        |  잠금 대기 뒤 run_again 은 그 인덱스부터 이어서 한다
        v
   INS_NODE_ALLOC_ROW_ID        [08] L3647  다음 행을 위해 되돌린다
```

```text
 인덱스를 넣는 순서와 부분 실패

 table->indexes 목록의 첫 원소가 클러스터드다 (first_index, dict0mem.h L2491)
 [08] row_ins 의 while (L3615)

   PRIMARY   [10] row_ins_clust_index_entry   undo 기록 + 레코드 삽입
   idx_a     [11] row_ins_sec_index_entry
   idx_b     [11] row_ins_sec_index_entry      <- 여기서 DB_DUPLICATE_KEY 라면
   (FTS 인덱스는 건너뛴다 L3616, 손상된 세컨더리도 건너뛴다 L3638)

 idx_b 에서 실패하면 PRIMARY 와 idx_a 는 이미 들어가 있다
   [06] L1594 row_mysql_handle_errors -> DB_DUPLICATE_KEY 이면
   trx_rollback_to_savepoint(trx, savept) (row0mysql.cc L702)
   L1564 에서 잡은 savept 까지 되돌려 이 행의 앞선 인덱스 삽입을 undo 로 지운다
```

## 어디에서 쓰이는가

```text
 [명령 디스패치]        Sql_cmd_dml::execute 가 가상 함수 execute_inner 로 [01] 을 부른다 (sql_select.cc L798).
                        그 전에 lock_tables (L794) -> ha_innobase::external_lock 이 InnoDB 트랜잭션을 등록해 둔다
 [B+Tree 삽입과 분할]   [10] [11] 이 부르는 row_ins_clust_index_entry_low / row_ins_sec_index_entry_low
 [레코드 잠금과 교착]   DB_LOCK_WAIT 를 받은 [06] 이 row_mysql_handle_errors -> lock_wait_suspend_thread 로 잠든다
 [커밋과 binlog 2PC]    [03] 의 binlog_log_row 가 쌓은 행 이벤트가 커밋 때 binlog 로 나간다
```

## db-engine 에서는

같은 문제(행을 저장소에 넣고, 인덱스를 함께 맞추고, 실패하면 반쯤 들어간 것을 없애기)를 db-engine 은 heap 과 인덱스 두 개로 나눠 풀었다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 행이 사는 곳
   MySQL      클러스터드 인덱스 자체가 테이블이다. 행 전체가 PRIMARY 의 리프에 들어간다
              PK 가 없으면 6바이트 DB_ROW_ID 를 발급해 그것이 키가 된다 ([08] L3523)
   db-engine  TableHeap.insert 가 마지막 page 의 freeOffset 에 이어 붙인다 (06-01)
              page 가 차면 bufferPool.newPage(). 정렬도 slot directory 도 없다

 인덱스 유지
   MySQL      ins_node_t 의 entry_list 가 인덱스마다 엔트리 틀을 들고 있고
              [08] 이 클러스터드 -> 세컨더리 순서로 모두 넣는다
   db-engine  IndexedTableHeap.insert = index.search(key) 로 중복 검사
              -> heap.insert(tuple) -> index.insert(key, heap.rowCount()) (06-04)

 중복 검사
   MySQL      삽입할 자리로 커서를 내린 뒤 그 자리의 이웃 레코드와 비교한다
              (row_ins_duplicate_error_in_clust, 다음 흐름)
   db-engine  insert 전에 index.search 로 따로 한 번 찾는다

 반쯤 들어간 행
   MySQL      행마다 savept 를 잡고 실패하면 undo 로 그 지점까지 되돌린다 ([06] L1564)
   db-engine  검증을 heap 보다 먼저 해서 실패하면 아무것도 바뀌지 않게 한다
              heap 과 index 사이에서 죽는 경우는 WAL(단계 8) 몫으로 남겼다
```

db-engine 의 `InsertOp` 은 `heap.insert` 를 그대로 부르는 얇은 층이고, MySQL 의 서버 계층과 엔진 사이에 놓인 handler 인터페이스와 쿼리 그래프 같은 번역 층이 없다. 대신 MySQL 은 그 번역 층에서 AUTO_INCREMENT, 트리거, binlog 행 이벤트, 잠금 대기 재시도를 처리한다. 챕터: [06-01-table-seqscan](../../../../../project/db-engine/06-01-table-seqscan/), [06-04-indexed-table-heap](../../../../../project/db-engine/06-04-indexed-table-heap/).

## 단계

1. [Sql_cmd_insert_values.execute_inner](01_Sql_cmd_insert_values.execute_inner/README.md)가 VALUES 목록을 한 행씩 채워 `write_record` 에 넘긴다.
2. [write_record](02_write_record/README.md)가 `ha_write_row` 를 부르고, REPLACE 와 ON DUPLICATE KEY UPDATE 면 중복 오류를 받아 갱신이나 삭제 후 재시도로 바꾼다.
3. [handler.ha_write_row](03_handler.ha_write_row/README.md)가 엔진의 `write_row` 를 부르고 성공하면 binlog 행 이벤트를 만든다.
4. [ha_innobase.write_row](04_ha_innobase.write_row/README.md)가 AUTO_INCREMENT 를 정하고 InnoDB 의 삽입 경로로 들어간다.
5. [row_insert_for_mysql](05_row_insert_for_mysql/README.md)이 삽입 방식을 고르고, 테이블마다 한 번 insert 그래프를 만든다.
6. [row_insert_for_mysql_using_ins_graph](06_row_insert_for_mysql_using_ins_graph/README.md)가 행을 변환하고 그래프를 돌리며 잠금 대기와 오류를 처리한다.
7. [row_ins_step](07_row_ins_step/README.md)이 그래프의 insert 노드로서 테이블 IX 잠금을 잡는다.
8. [row_ins](08_row_ins/README.md)가 인덱스 목록을 돌며 엔트리를 하나씩 넣는다.
9. [row_ins_index_entry_step](09_row_ins_index_entry_step/README.md)이 엔트리에 값을 채우고 클러스터드와 세컨더리로 가른다.
10. [row_ins_clust_index_entry](10_row_ins_clust_index_entry/README.md)가 클러스터드 인덱스에 LEAF 먼저, 실패하면 TREE 로 넣는다.
11. [row_ins_sec_index_entry](11_row_ins_sec_index_entry/README.md)가 세컨더리 인덱스에 같은 두 단계로 넣는다.

## 결과가 쓰이는 곳

```text
 클러스터드 인덱스 리프의 새 레코드 (DB_TRX_ID, DB_ROLL_PTR 포함)
      --> 다른 트랜잭션의 [일관 읽기(MVCC)] 가 DB_TRX_ID 로 보일지 가리고
          DB_ROLL_PTR 을 따라 insert undo 로 간다
      --> 커밋 전까지 암묵적 잠금 역할을 한다 ([레코드 잠금과 교착])

 insert undo 레코드
      --> 롤백과 [06] 의 savept 되돌리기가 쓴다
      --> 커밋 때 trx_undo_set_state_at_finish 로 상태가 정해진다 (trx0trx.cc L1571, [커밋과 binlog 2PC])

 binlog 행 이벤트 (Write_rows_log_event)
      --> [커밋과 binlog 2PC] 의 flush 단계에서 binlog 파일로 나간다

 info.stats (records, copied, deleted, updated)
      --> my_ok 의 영향 받은 행 수와 "Records: Duplicates: Warnings:" 문구
```

## 다루지 않는 것

`INSERT ... SELECT`(`Query_result_insert`)와 `LOAD DATA`, JSON duality view 삽입(`jdv::jdv_insert`), 파티션 가지치기(`prune_partitions`), 트리거 본문 실행, 생성 열과 multi-value 인덱스의 값 계산, FTS 문서 ID 처리(`fts_trx_add_op`), 내부 임시 테이블의 커서 경로(`row_insert_for_mysql_using_cursor`, `row_ins_sorted_clust_index_entry`), InnoDB FK 검사(`row_ins_check_foreign_constraints`), 동시성 제한(`innobase_srv_conc_enter_innodb`)은 이 흐름의 곁가지라 이름과 줄만 적었다. 트리 안의 탐색과 분할, 잠금과 undo 기록은 [B+Tree 삽입과 분할](../btree-insert/README.md)에서 다룬다.

## 하위 메서드

- [01 Sql_cmd_insert_values.execute_inner](01_Sql_cmd_insert_values.execute_inner/README.md)
- [02 write_record](02_write_record/README.md)
- [03 handler.ha_write_row](03_handler.ha_write_row/README.md)
- [04 ha_innobase.write_row](04_ha_innobase.write_row/README.md)
- [05 row_insert_for_mysql](05_row_insert_for_mysql/README.md)
- [06 row_insert_for_mysql_using_ins_graph](06_row_insert_for_mysql_using_ins_graph/README.md)
- [07 row_ins_step](07_row_ins_step/README.md)
- [08 row_ins](08_row_ins/README.md)
- [09 row_ins_index_entry_step](09_row_ins_index_entry_step/README.md)
- [10 row_ins_clust_index_entry](10_row_ins_clust_index_entry/README.md)
- [11 row_ins_sec_index_entry](11_row_ins_sec_index_entry/README.md)
