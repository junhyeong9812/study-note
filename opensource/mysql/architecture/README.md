# MySQL 아키텍처 지도

소스를 **직접 읽어서** 그리는 탑다운 지도다. 지금은 **목록 단계**다 - 흐름 열두 편의 진입점과 흐름마다 거칠 함수 목록을 소스로 확인해 두었고, 흐름 문서 본문은 아직 없다.

기준 태그: `mysql-9.7.2` [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다. 범위는 **InnoDB(`storage/innobase`) 중심**이고, 서버 계층(`sql/`)은 InnoDB와 만나는 자리까지만 본다.

SQL 문이나 시스템 변수에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 상위: [MySQL](../README.md)

## 두 갈래로 읽는다

```text
 구조  무엇이 있는가          6편 (목록)
       테이블스페이스·레코드 포맷·redo 파일처럼 자리에 관한 것

 흐름  무엇이 일어나는가      12편, 116개 문서 예정
       요청 하나가 지나는 길을 함수 단위로 따라간다
       폴더 하나 = 함수 하나
```

## 흐름 열두 편

오른쪽 칸은 같은 문제를 [db-engine](https://github.com/junhyeong9812/db-engine)(직접 만든 교육용 DB 엔진)에서 다루는 챕터다. 일치하는 흐름에만 적었다.

| 흐름 | 진입점 | 문서 | db-engine 대응 |
|---|---|---|---|
| 연결과 스레드 | `handle_connection` `sql/conn_handler/connection_handler_per_thread.cc` L246 | 8 | [13-01-connection-pool](../../../project/db-engine/13-01-connection-pool/) · [14-01-protocol-handler](../../../project/db-engine/14-01-protocol-handler/) · [15-01-auth](../../../project/db-engine/15-01-auth/) |
| 명령 디스패치 | `dispatch_command` `sql/sql_parse.cc` L1752 | 9 | [12-01-sql-parser](../../../project/db-engine/12-01-sql-parser/) · [13-02-sql-translator](../../../project/db-engine/13-02-sql-translator/) · [14-00-db-engine](../../../project/db-engine/14-00-db-engine/) |
| 행 쓰기 (handler -> row0ins) | `ha_innobase::write_row` `storage/innobase/handler/ha_innodb.cc` L9256 | 10 | [06-01-table-seqscan](../../../project/db-engine/06-01-table-seqscan/) · [06-04-indexed-table-heap](../../../project/db-engine/06-04-indexed-table-heap/) |
| B+Tree 삽입과 분할 | `row_ins_clust_index_entry_low` `storage/innobase/row/row0ins.cc` L2399 | 9 | [03-01-btree-leaf-only](../../../project/db-engine/03-01-btree-leaf-only/) · [03-02-btree-split](../../../project/db-engine/03-02-btree-split/) |
| mini-transaction과 redo 기록 | `mtr_t::commit` `storage/innobase/mtr/mtr0mtr.cc` L662 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [08-02-lsn-checkpoint](../../../project/db-engine/08-02-lsn-checkpoint/) |
| 버퍼 풀 페이지 획득 | `buf_page_get_gen` `storage/innobase/buf/buf0buf.cc` L4449 | 10 | [02-01-page-pagedfile](../../../project/db-engine/02-01-page-pagedfile/) · [02-02-buffer-pool](../../../project/db-engine/02-02-buffer-pool/) |
| 일관 읽기(MVCC)와 undo 체인 | `row_search_mvcc` `storage/innobase/row/row0sel.cc` L4431 | 10 | [10-01-mvcc](../../../project/db-engine/10-01-mvcc/) · [10-02-isolation-anomaly](../../../project/db-engine/10-02-isolation-anomaly/) · [10-03-mvcc-table-heap](../../../project/db-engine/10-03-mvcc-table-heap/) |
| 레코드 잠금과 교착 | `lock_rec_lock` `storage/innobase/lock/lock0lock.cc` L1864 | 10 | [09-01-lock-manager](../../../project/db-engine/09-01-lock-manager/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| 커밋과 binlog 2PC | `ha_commit_trans` `sql/handler.cc` L1686 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| purge | `srv_purge_coordinator_thread` `storage/innobase/srv/srv0srv.cc` L3032 | 10 | 없음 - [10-01](../../../project/db-engine/10-01-mvcc/) · [10-03](../../../project/db-engine/10-03-mvcc-table-heap/) 이 "다음 한계"로 예고한 자리 |
| 페이지 플러시, doublewrite, 체크포인트 | `buf_flush_page_coordinator_thread` `storage/innobase/buf/buf0flu.cc` L2875 | 10 | [08-02-lsn-checkpoint](../../../project/db-engine/08-02-lsn-checkpoint/) |
| 크래시 복구 | `recv_recovery_from_checkpoint_start` `storage/innobase/log/log0recv.cc` L3766 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [08-03-crash-simulation](../../../project/db-engine/08-03-crash-simulation/) |

온라인 DDL(`mysql_inplace_alter_table` `sql/sql_table.cc` L14394 -> `ha_innobase::inplace_alter_table` `handler/handler0alter.cc` L1566)은 열세 번째 후보로 남겨 두었다. db-engine의 [19-01-online-ddl](../../../project/db-engine/19-01-online-ddl/)과 맞닿는다.

## 흐름이 이어지는 자리

```text
 서버 계층 - SQL 하나가 InnoDB 에 닿기까지

 [연결과 스레드]  handle_connection 의 while ... do_command 루프 (L304)
      v
 [명령 디스패치]  dispatch_command -> mysql_execute_command
      |  lock_tables -> ha_innobase::external_lock 에서
      |  InnoDB 트랜잭션이 등록된다 (innobase_register_trx)
      +-- 쓰기  ha_write_row  -> [행 쓰기]
      +-- 읽기  ha_rnd_next / ha_index_read_map -> [일관 읽기(MVCC)]
      v
 [커밋과 binlog 2PC]  prepare -> ordered_commit (FLUSH -> SYNC -> COMMIT)
```

```text
 InnoDB 안 - 한 번의 쓰기

 [행 쓰기] row_ins_clust_index_entry
      v
 [B+Tree 삽입과 분할]  mtr.start ... optimistic / pessimistic ... mtr.commit
      |  btr_cur_ins_lock_and_undo 에서 두 갈래
      |    lock_rec_insert_check_and_lock  -> [레코드 잠금]
      |    trx_undo_report_row_operation   -> undo 기록 (MVCC 와 purge 의 재료)
      |  페이지마다 buf_page_get_gen       -> [버퍼 풀 페이지 획득]
      v
 [mini-transaction과 redo 기록]  log buffer 에 쓰고 dirty 페이지를 flush list 에 붙인다
```

```text
 백그라운드 스레드

 [페이지 플러시, doublewrite, 체크포인트]
    buf_flush_write_block_low 가 먼저 log_write_up_to 로 redo 를 맞추고 (buf0flu.cc L966)
    doublewrite 를 거쳐 페이지를 쓴다. checkpoint LSN 이 전진하면 redo 가 재사용된다
 [purge]          커밋된 undo 가 history list 로 가고 purge 가 그것을 치운다
 [크래시 복구]    checkpoint 에서 redo 를 다시 적용하고
                  서버 쪽 Binlog_recovery 가 prepared XID 를 정리한다
```

## 구조 여섯 편 (목록)

| 편 | 대표 자리 |
|---|---|
| 테이블스페이스와 페이지 레이아웃 | `include/fil0types.h` (`FIL_PAGE_LSN` L67), `include/fsp0fsp.h`, `include/page0types.h` |
| 레코드 포맷 | `rem/rec.h`, `include/rem0rec.h`, `include/rem0wrec.h` |
| redo 로그 파일과 mlog 타입 | `include/log0sys.h` (`struct log_t` L77), `include/mtr0types.h` (`enum mlog_id_t` L63) |
| undo 테이블스페이스와 롤백 세그먼트 | `include/trx0types.h` (`trx_rseg_t` L214), `include/trx0undo.h` (`trx_undo_t` L340) |
| 메모리 구조 | `include/buf0buf.h` (`buf_pool_t` L2293), `include/lock0priv.h` (`lock_t` L137), `include/read0types.h` (`ReadView` L48), `include/trx0trx.h` (`trx_t` L675) |
| 스레드 구성 | `include/srv0srv.h` (`Srv_threads` L165), `sql/conn_handler/connection_handler_impl.h` L42 |

경로는 `sql/` 로 시작하지 않으면 `storage/innobase/` 아래다.

## 읽는 순서

```text
 처음이면
   [구조: 스레드 구성] -> [연결과 스레드] -> [명령 디스패치]

 쓰기를 알고 싶으면
   [행 쓰기] -> [B+Tree 삽입과 분할] -> [mini-transaction과 redo 기록] -> [커밋과 binlog 2PC]

 읽기를 알고 싶으면
   [일관 읽기(MVCC)] -> [버퍼 풀 페이지 획득] -> [레코드 잠금]

 장애와 복구가 궁금하면
   [페이지 플러시, doublewrite, 체크포인트] -> [크래시 복구]
```

## 흐름별 함수 목록

흐름 문서를 쓸 때 폴더가 될 함수들이다. `파일:줄`은 모두 정의 줄이다.

### 연결과 스레드 (`flows/connection-thread/`)

```text
 01_Connection_handler_manager::process_new_connection connection_handler_manager.cc:256
 02_Per_thread_connection_handler::add_connection connection_handler_per_thread.cc:404
 03_handle_connection connection_handler_per_thread.cc:246
 04_thd_prepare_connection sql_connect.cc:892
 05_login_connection sql_connect.cc:698
 06_prepare_new_connection_state sql_connect.cc:776
 07_end_connection sql_connect.cc:732
 08_close_connection sql_connect.cc:917
```

### 명령 디스패치 (`flows/command-dispatch/`)

```text
 01_do_command sql_parse.cc:1347
 02_dispatch_command sql_parse.cc:1752
 03_dispatch_sql_command sql_parse.cc:5307
 04_parse_sql sql_parse.cc:7208
 05_mysql_execute_command sql_parse.cc:3031
 06_Sql_cmd_dml::execute sql_select.cc:685
 07_lock_tables sql_base.cc:7293
 08_ha_innobase::external_lock ha_innodb.cc:18903
 09_Sql_cmd_dml::execute_inner sql_select.cc:1123
```

### 행 쓰기 (handler -> row0ins) (`flows/row-insert/`)

```text
 01_Sql_cmd_insert_values::execute_inner sql_insert.cc:482
 02_write_record sql_insert.cc:1801
 03_handler::ha_write_row handler.cc:8198
 04_ha_innobase::write_row ha_innodb.cc:9256
 05_row_insert_for_mysql row0mysql.cc:1704
 06_row_insert_for_mysql_using_ins_graph row0mysql.cc:1500
 07_row_ins_step row0ins.cc:3655
 08_row_ins row0ins.cc:3587
 09_row_ins_index_entry_step row0ins.cc:3481
 10_row_ins_clust_index_entry row0ins.cc:3119
```

### B+Tree 삽입과 분할 (`flows/btree-insert/`)

```text
 01_row_ins_clust_index_entry_low row0ins.cc:2399
 02_btr_cur_search_to_nth_level btr0cur.cc:619
 03_btr_cur_optimistic_insert btr0cur.cc:2662
 04_btr_cur_ins_lock_and_undo btr0cur.cc:2554
 05_page_cur_tuple_insert page0cur.ic:187
 06_page_cur_insert_rec_low page0cur.cc:1229
 07_btr_cur_pessimistic_insert btr0cur.cc:2930
 08_btr_page_split_and_insert btr0btr.cc:2305
 09_btr_root_raise_and_insert btr0btr.cc:1482
```

### mini-transaction과 redo 기록 (`flows/mtr-redo/`)

```text
 01_mtr_t::start mtr0mtr.cc:565
 02_mtr_t::commit mtr0mtr.cc:662
 03_mtr_t::Command::prepare_write mtr0mtr.cc:760
 04_mtr_t::Command::execute mtr0mtr.cc:840
 05_log_buffer_reserve log0buf.cc:884
 06_log_buffer_write log0buf.cc:944
 07_log_buffer_write_completed log0buf.cc:1083
 08_mtr_t::Command::add_dirty_blocks_to_flush_list mtr0mtr.cc:828
 09_log_writer log0write.cc:2230
 10_log_flusher log0write.cc:2495
```

### 버퍼 풀 페이지 획득 (`flows/buffer-pool-fetch/`)

```text
 01_buf_page_get_gen buf0buf.cc:4449
 02_Buf_fetch::single_page buf0buf.cc:4299
 03_Buf_fetch::lookup buf0buf.cc:3826
 04_Buf_fetch_normal::get buf0buf.cc:3713
 05_Buf_fetch::read_page buf0buf.cc:4117
 06_buf_read_page_low buf0rea.cc:66
 07_buf_page_init_for_read buf0buf.cc:4880
 08_buf_LRU_get_free_block buf0lru.cc:1311
 09_buf_page_make_young_if_needed buf0buf.cc:3212
 10_buf_LRU_add_block buf0lru.cc:1714
```

### 일관 읽기(MVCC)와 undo 체인 (`flows/mvcc-read/`)

```text
 01_ha_innobase::index_read ha_innodb.cc:10430
 02_row_search_mvcc row0sel.cc:4431
 03_trx_assign_read_view trx0trx.cc:2291
 04_ReadView::prepare read0read.cc:446
 05_lock_clust_rec_cons_read_sees lock0lock.cc:236
 06_ReadView::changes_visible read0types.h:163
 07_row_sel_build_prev_vers_for_mysql row0sel.cc:3079
 08_row_vers_build_for_consistent_read row0vers.cc:1249
 09_trx_undo_prev_version_build trx0rec.cc:2446
 10_trx_undo_get_undo_rec trx0rec.cc:2421
```

### 레코드 잠금과 교착 (`flows/record-lock/`)

```text
 01_sel_set_rec_lock row0sel.cc:1138
 02_lock_clust_rec_read_check_and_lock lock0lock.cc:5420
 03_lock_rec_lock lock0lock.cc:1864
 04_lock_rec_lock_fast lock0lock.cc:1617
 05_lock_rec_lock_slow lock0lock.cc:1749
 06_lock_rec_other_has_conflicting lock0lock.cc:903
 07_RecLock::add_to_waitq lock0lock.cc:1445
 08_lock_rec_insert_check_and_lock lock0lock.cc:5050
 09_lock_wait_suspend_thread lock0wait.cc:206
 10_lock_wait_timeout_thread lock0wait.cc:1432
```

### 커밋과 binlog 2PC (`flows/commit-2pc/`)

```text
 01_trans_commit transaction.cc:233
 02_ha_commit_trans handler.cc:1686
 03_MYSQL_BIN_LOG::prepare binlog.cc:7054
 04_MYSQL_BIN_LOG::commit binlog.cc:7107
 05_MYSQL_BIN_LOG::ordered_commit binlog.cc:7895
 06_process_flush_stage_queue binlog.cc:7490
 07_sync_binlog_file binlog.cc:7700
 08_process_commit_stage_queue binlog.cc:7550
 09_innobase_commit ha_innodb.cc:5955
 10_trx_commit_low trx0trx.cc:2137
```

### purge (`flows/purge/`)

```text
 01_srv_purge_coordinator_thread srv0srv.cc:3032
 02_srv_do_purge srv0srv.cc:2845
 03_trx_purge trx0purge.cc:2396
 04_trx_purge_update_oldest_needed trx0purge.cc:252
 05_trx_purge_attach_undo_recs trx0purge.cc:2243
 06_srv_worker_thread srv0srv.cc:2789
 07_row_purge_step row0purge.cc:1210
 08_row_purge_record_func row0purge.cc:1074
 09_row_purge_del_mark row0purge.cc:656
 10_trx_purge_truncate trx0purge.cc:2381
```

### 페이지 플러시, doublewrite, 체크포인트 (`flows/flush-checkpoint/`)

```text
 01_buf_flush_page_coordinator_thread buf0flu.cc:2875
 02_pc_flush_slot buf0flu.cc:2627
 03_buf_flush_do_batch buf0flu.cc:1787
 04_buf_flush_page buf0flu.cc:1027
 05_buf_flush_write_block_low buf0flu.cc:924
 06_dblwr::write buf0dblwr.cc:2481
 07_Double_write::submit buf0dblwr.cc:669
 08_log_checkpointer log0chkp.cc:904
 09_log_checkpoint log0chkp.cc:444
 10_log_files_next_checkpoint log0chkp.cc:337
```

### 크래시 복구 (`flows/crash-recovery/`)

```text
 01_srv_start srv0start.cc:1330
 02_recv_recovery_from_checkpoint_start log0recv.cc:3766
 03_recv_find_max_checkpoint log0recv.cc:973
 04_recv_recovery_begin log0recv.cc:3622
 05_recv_scan_log_recs log0recv.cc:3289
 06_recv_init_crash_recovery log0recv.cc:3744
 07_recv_apply_hashed_log_recs log0recv.cc:1173
 08_recv_recover_page_func log0recv.cc:2430
 09_recv_recovery_from_checkpoint_finish log0recv.cc:3950
 10_srv_dict_recover_on_restart srv0start.cc:2110
```
