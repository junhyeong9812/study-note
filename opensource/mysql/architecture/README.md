# MySQL 아키텍처 지도

소스를 **직접 읽어서** 그리는 탑다운 지도다. 흐름 열세 편(함수 문서 129편)과 구조 여섯 편으로 되어 있고, 모든 코드 인용과 줄 번호는 작성과 별도로 소스와 대조해 검증했다.

기준 태그: `mysql-9.7.2` [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다. 범위는 **InnoDB(`storage/innobase`) 중심**이고, 서버 계층(`sql/`)은 InnoDB와 만나는 자리까지만 본다.

SQL 문이나 시스템 변수에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 상위: [MySQL](../README.md)

## 두 갈래로 읽는다

```text
 구조  무엇이 있는가          6편
       테이블스페이스·레코드 포맷·redo 파일처럼 자리에 관한 것

 흐름  무엇이 일어나는가      13편, 함수 문서 129편
       요청 하나가 지나는 길을 함수 단위로 따라간다
       폴더 하나 = 함수 하나
```

## 흐름 열세 편

오른쪽 칸은 같은 문제를 [db-engine](https://github.com/junhyeong9812/db-engine)(직접 만든 교육용 DB 엔진)에서 다루는 챕터다. 일치하는 흐름에만 적었다.

| 흐름 | 진입점 | 문서 | db-engine 대응 |
|---|---|---|---|
| [연결과 스레드](flows/connection-thread/README.md) | `handle_connection` `sql/conn_handler/connection_handler_per_thread.cc` L246 | 8 | [13-01-connection-pool](../../../project/db-engine/13-01-connection-pool/) · [14-01-protocol-handler](../../../project/db-engine/14-01-protocol-handler/) · [15-01-auth](../../../project/db-engine/15-01-auth/) |
| [명령 디스패치](flows/command-dispatch/README.md) | `dispatch_command` `sql/sql_parse.cc` L1752 | 9 | [12-01-sql-parser](../../../project/db-engine/12-01-sql-parser/) · [13-02-sql-translator](../../../project/db-engine/13-02-sql-translator/) · [14-00-db-engine](../../../project/db-engine/14-00-db-engine/) |
| [행 쓰기 (handler -> row0ins)](flows/row-insert/README.md) | `ha_innobase::write_row` `storage/innobase/handler/ha_innodb.cc` L9256 | 11 | [06-01-table-seqscan](../../../project/db-engine/06-01-table-seqscan/) · [06-04-indexed-table-heap](../../../project/db-engine/06-04-indexed-table-heap/) |
| [B+Tree 삽입과 분할](flows/btree-insert/README.md) | `row_ins_clust_index_entry_low` `storage/innobase/row/row0ins.cc` L2399 | 9 | [03-01-btree-leaf-only](../../../project/db-engine/03-01-btree-leaf-only/) · [03-02-btree-split](../../../project/db-engine/03-02-btree-split/) |
| [mini-transaction과 redo 기록](flows/mtr-redo/README.md) | `mtr_t::commit` `storage/innobase/mtr/mtr0mtr.cc` L662 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [08-02-lsn-checkpoint](../../../project/db-engine/08-02-lsn-checkpoint/) |
| [버퍼 풀 페이지 획득](flows/buffer-pool-fetch/README.md) | `buf_page_get_gen` `storage/innobase/buf/buf0buf.cc` L4449 | 10 | [02-01-page-pagedfile](../../../project/db-engine/02-01-page-pagedfile/) · [02-02-buffer-pool](../../../project/db-engine/02-02-buffer-pool/) |
| [일관 읽기(MVCC)와 undo 체인](flows/mvcc-read/README.md) | `row_search_mvcc` `storage/innobase/row/row0sel.cc` L4431 | 10 | [10-01-mvcc](../../../project/db-engine/10-01-mvcc/) · [10-02-isolation-anomaly](../../../project/db-engine/10-02-isolation-anomaly/) · [10-03-mvcc-table-heap](../../../project/db-engine/10-03-mvcc-table-heap/) |
| [레코드 잠금과 교착](flows/record-lock/README.md) | `lock_rec_lock` `storage/innobase/lock/lock0lock.cc` L1864 | 11 | [09-01-lock-manager](../../../project/db-engine/09-01-lock-manager/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| [커밋과 binlog 2PC](flows/commit-2pc/README.md) | `ha_commit_trans` `sql/handler.cc` L1686 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| [purge](flows/purge/README.md) | `srv_purge_coordinator_thread` `storage/innobase/srv/srv0srv.cc` L3032 | 10 | 없음 - db-engine 에는 정리 기능이 없다 ([10-01](../../../project/db-engine/10-01-mvcc/) 과제 3 답, [10-03](../../../project/db-engine/10-03-mvcc-table-heap/) MVCCTableHeap 주석) |
| [페이지 플러시, doublewrite, 체크포인트](flows/flush-checkpoint/README.md) | `buf_flush_page_coordinator_thread` `storage/innobase/buf/buf0flu.cc` L2875 | 10 | [08-02-lsn-checkpoint](../../../project/db-engine/08-02-lsn-checkpoint/) |
| [크래시 복구](flows/crash-recovery/README.md) | `recv_recovery_from_checkpoint_start` `storage/innobase/log/log0recv.cc` L3766 | 12 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [08-03-crash-simulation](../../../project/db-engine/08-03-crash-simulation/) |
| [온라인 DDL](flows/online-ddl/README.md) | `mysql_inplace_alter_table` `sql/sql_table.cc` L14394 | 9 | [19-01-online-ddl](../../../project/db-engine/19-01-online-ddl/) · [19-02-schema-version](../../../project/db-engine/19-02-schema-version/) |


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

## 구조 여섯 편

| 편 | 대표 자리 |
|---|---|
| [테이블스페이스와 페이지 레이아웃](structure/tablespace-page/README.md) | `include/fil0types.h` (`FIL_PAGE_LSN` L67), `include/fsp0fsp.h`, `include/page0types.h` |
| [레코드 포맷](structure/record-format/README.md) | `rem/rec.h`, `include/rem0rec.h`, `include/rem0wrec.h` |
| [redo 로그 파일과 mlog 타입](structure/redo-log-files/README.md) | `include/log0sys.h` (`struct log_t` L77), `include/mtr0types.h` (`enum mlog_id_t` L63) |
| [undo 테이블스페이스와 롤백 세그먼트](structure/undo-segments/README.md) | `include/trx0types.h` (`trx_rseg_t` L214), `include/trx0undo.h` (`trx_undo_t` L340) |
| [메모리 구조](structure/memory-structures/README.md) | `include/buf0buf.h` (`buf_pool_t` L2293), `include/lock0priv.h` (`lock_t` L137), `include/read0types.h` (`ReadView` L48), `include/trx0trx.h` (`trx_t` L675) |
| [스레드 구성](structure/threads/README.md) | `include/srv0srv.h` (`Srv_threads` L165), `sql/conn_handler/connection_handler_impl.h` L42 |

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

 버전과 정리가 궁금하면
   [구조: undo 테이블스페이스와 롤백 세그먼트] -> [일관 읽기(MVCC)] -> [purge]

 스키마 변경이 궁금하면
   [레코드 잠금과 교착] -> [온라인 DDL]
```

## 흐름별 함수 문서

폴더 하나가 함수 하나다. 곁가지 함수는 가까운 함수 문서 안에서 함께 다룬다.

### [연결과 스레드](flows/connection-thread/README.md)

- [01_Connection_handler_manager.process_new_connection](flows/connection-thread/01_Connection_handler_manager.process_new_connection/README.md)
- [02_Per_thread_connection_handler.add_connection](flows/connection-thread/02_Per_thread_connection_handler.add_connection/README.md)
- [03_handle_connection](flows/connection-thread/03_handle_connection/README.md)
- [04_thd_prepare_connection](flows/connection-thread/04_thd_prepare_connection/README.md)
- [05_login_connection](flows/connection-thread/05_login_connection/README.md)
- [06_prepare_new_connection_state](flows/connection-thread/06_prepare_new_connection_state/README.md)
- [07_end_connection](flows/connection-thread/07_end_connection/README.md)
- [08_close_connection](flows/connection-thread/08_close_connection/README.md)

### [명령 디스패치](flows/command-dispatch/README.md)

- [01_do_command](flows/command-dispatch/01_do_command/README.md)
- [02_dispatch_command](flows/command-dispatch/02_dispatch_command/README.md)
- [03_dispatch_sql_command](flows/command-dispatch/03_dispatch_sql_command/README.md)
- [04_parse_sql](flows/command-dispatch/04_parse_sql/README.md)
- [05_mysql_execute_command](flows/command-dispatch/05_mysql_execute_command/README.md)
- [06_Sql_cmd_dml.execute](flows/command-dispatch/06_Sql_cmd_dml.execute/README.md)
- [07_lock_tables](flows/command-dispatch/07_lock_tables/README.md)
- [08_ha_innobase.external_lock](flows/command-dispatch/08_ha_innobase.external_lock/README.md)
- [09_Sql_cmd_dml.execute_inner](flows/command-dispatch/09_Sql_cmd_dml.execute_inner/README.md)

### [행 쓰기 (handler -> row0ins)](flows/row-insert/README.md)

- [01_Sql_cmd_insert_values.execute_inner](flows/row-insert/01_Sql_cmd_insert_values.execute_inner/README.md)
- [02_write_record](flows/row-insert/02_write_record/README.md)
- [03_handler.ha_write_row](flows/row-insert/03_handler.ha_write_row/README.md)
- [04_ha_innobase.write_row](flows/row-insert/04_ha_innobase.write_row/README.md)
- [05_row_insert_for_mysql](flows/row-insert/05_row_insert_for_mysql/README.md)
- [06_row_insert_for_mysql_using_ins_graph](flows/row-insert/06_row_insert_for_mysql_using_ins_graph/README.md)
- [07_row_ins_step](flows/row-insert/07_row_ins_step/README.md)
- [08_row_ins](flows/row-insert/08_row_ins/README.md)
- [09_row_ins_index_entry_step](flows/row-insert/09_row_ins_index_entry_step/README.md)
- [10_row_ins_clust_index_entry](flows/row-insert/10_row_ins_clust_index_entry/README.md)
- [11_row_ins_sec_index_entry](flows/row-insert/11_row_ins_sec_index_entry/README.md)

### [B+Tree 삽입과 분할](flows/btree-insert/README.md)

- [01_row_ins_clust_index_entry_low](flows/btree-insert/01_row_ins_clust_index_entry_low/README.md)
- [02_btr_cur_search_to_nth_level](flows/btree-insert/02_btr_cur_search_to_nth_level/README.md)
- [03_btr_cur_optimistic_insert](flows/btree-insert/03_btr_cur_optimistic_insert/README.md)
- [04_btr_cur_ins_lock_and_undo](flows/btree-insert/04_btr_cur_ins_lock_and_undo/README.md)
- [05_page_cur_tuple_insert](flows/btree-insert/05_page_cur_tuple_insert/README.md)
- [06_page_cur_insert_rec_low](flows/btree-insert/06_page_cur_insert_rec_low/README.md)
- [07_btr_cur_pessimistic_insert](flows/btree-insert/07_btr_cur_pessimistic_insert/README.md)
- [08_btr_page_split_and_insert](flows/btree-insert/08_btr_page_split_and_insert/README.md)
- [09_btr_root_raise_and_insert](flows/btree-insert/09_btr_root_raise_and_insert/README.md)

### [mini-transaction과 redo 기록](flows/mtr-redo/README.md)

- [01_mtr_t.start](flows/mtr-redo/01_mtr_t.start/README.md)
- [02_mtr_t.commit](flows/mtr-redo/02_mtr_t.commit/README.md)
- [03_mtr_t.Command.prepare_write](flows/mtr-redo/03_mtr_t.Command.prepare_write/README.md)
- [04_mtr_t.Command.execute](flows/mtr-redo/04_mtr_t.Command.execute/README.md)
- [05_log_buffer_reserve](flows/mtr-redo/05_log_buffer_reserve/README.md)
- [06_log_buffer_write](flows/mtr-redo/06_log_buffer_write/README.md)
- [07_log_buffer_write_completed](flows/mtr-redo/07_log_buffer_write_completed/README.md)
- [08_mtr_t.Command.add_dirty_blocks_to_flush_list](flows/mtr-redo/08_mtr_t.Command.add_dirty_blocks_to_flush_list/README.md)
- [09_log_writer](flows/mtr-redo/09_log_writer/README.md)
- [10_log_flusher](flows/mtr-redo/10_log_flusher/README.md)

### [버퍼 풀 페이지 획득](flows/buffer-pool-fetch/README.md)

- [01_buf_page_get_gen](flows/buffer-pool-fetch/01_buf_page_get_gen/README.md)
- [02_Buf_fetch.single_page](flows/buffer-pool-fetch/02_Buf_fetch.single_page/README.md)
- [03_Buf_fetch.lookup](flows/buffer-pool-fetch/03_Buf_fetch.lookup/README.md)
- [04_Buf_fetch_normal.get](flows/buffer-pool-fetch/04_Buf_fetch_normal.get/README.md)
- [05_Buf_fetch.read_page](flows/buffer-pool-fetch/05_Buf_fetch.read_page/README.md)
- [06_buf_read_page_low](flows/buffer-pool-fetch/06_buf_read_page_low/README.md)
- [07_buf_page_init_for_read](flows/buffer-pool-fetch/07_buf_page_init_for_read/README.md)
- [08_buf_LRU_get_free_block](flows/buffer-pool-fetch/08_buf_LRU_get_free_block/README.md)
- [09_buf_page_make_young_if_needed](flows/buffer-pool-fetch/09_buf_page_make_young_if_needed/README.md)
- [10_buf_LRU_add_block](flows/buffer-pool-fetch/10_buf_LRU_add_block/README.md)

### [일관 읽기(MVCC)와 undo 체인](flows/mvcc-read/README.md)

- [01_ha_innobase.index_read](flows/mvcc-read/01_ha_innobase.index_read/README.md)
- [02_row_search_mvcc](flows/mvcc-read/02_row_search_mvcc/README.md)
- [03_trx_assign_read_view](flows/mvcc-read/03_trx_assign_read_view/README.md)
- [04_ReadView.prepare](flows/mvcc-read/04_ReadView.prepare/README.md)
- [05_lock_clust_rec_cons_read_sees](flows/mvcc-read/05_lock_clust_rec_cons_read_sees/README.md)
- [06_ReadView.changes_visible](flows/mvcc-read/06_ReadView.changes_visible/README.md)
- [07_row_sel_build_prev_vers_for_mysql](flows/mvcc-read/07_row_sel_build_prev_vers_for_mysql/README.md)
- [08_row_vers_build_for_consistent_read](flows/mvcc-read/08_row_vers_build_for_consistent_read/README.md)
- [09_trx_undo_prev_version_build](flows/mvcc-read/09_trx_undo_prev_version_build/README.md)
- [10_trx_undo_get_undo_rec](flows/mvcc-read/10_trx_undo_get_undo_rec/README.md)

### [레코드 잠금과 교착](flows/record-lock/README.md)

- [01_sel_set_rec_lock](flows/record-lock/01_sel_set_rec_lock/README.md)
- [02_lock_clust_rec_read_check_and_lock](flows/record-lock/02_lock_clust_rec_read_check_and_lock/README.md)
- [03_lock_rec_lock](flows/record-lock/03_lock_rec_lock/README.md)
- [04_lock_rec_lock_fast](flows/record-lock/04_lock_rec_lock_fast/README.md)
- [05_lock_rec_lock_slow](flows/record-lock/05_lock_rec_lock_slow/README.md)
- [06_lock_rec_other_has_conflicting](flows/record-lock/06_lock_rec_other_has_conflicting/README.md)
- [07_RecLock.add_to_waitq](flows/record-lock/07_RecLock.add_to_waitq/README.md)
- [08_lock_wait_suspend_thread](flows/record-lock/08_lock_wait_suspend_thread/README.md)
- [09_lock_wait_timeout_thread](flows/record-lock/09_lock_wait_timeout_thread/README.md)
- [10_lock_wait_find_and_handle_deadlocks](flows/record-lock/10_lock_wait_find_and_handle_deadlocks/README.md)
- [11_lock_rec_grant_by_heap_no](flows/record-lock/11_lock_rec_grant_by_heap_no/README.md)

### [커밋과 binlog 2PC](flows/commit-2pc/README.md)

- [01_trans_commit](flows/commit-2pc/01_trans_commit/README.md)
- [02_ha_commit_trans](flows/commit-2pc/02_ha_commit_trans/README.md)
- [03_MYSQL_BIN_LOG.prepare](flows/commit-2pc/03_MYSQL_BIN_LOG.prepare/README.md)
- [04_MYSQL_BIN_LOG.commit](flows/commit-2pc/04_MYSQL_BIN_LOG.commit/README.md)
- [05_MYSQL_BIN_LOG.ordered_commit](flows/commit-2pc/05_MYSQL_BIN_LOG.ordered_commit/README.md)
- [06_process_flush_stage_queue](flows/commit-2pc/06_process_flush_stage_queue/README.md)
- [07_sync_binlog_file](flows/commit-2pc/07_sync_binlog_file/README.md)
- [08_process_commit_stage_queue](flows/commit-2pc/08_process_commit_stage_queue/README.md)
- [09_innobase_commit](flows/commit-2pc/09_innobase_commit/README.md)
- [10_trx_commit_low](flows/commit-2pc/10_trx_commit_low/README.md)

### [purge](flows/purge/README.md)

- [01_srv_purge_coordinator_thread](flows/purge/01_srv_purge_coordinator_thread/README.md)
- [02_srv_do_purge](flows/purge/02_srv_do_purge/README.md)
- [03_trx_purge](flows/purge/03_trx_purge/README.md)
- [04_trx_purge_update_oldest_needed](flows/purge/04_trx_purge_update_oldest_needed/README.md)
- [05_trx_purge_attach_undo_recs](flows/purge/05_trx_purge_attach_undo_recs/README.md)
- [06_srv_worker_thread](flows/purge/06_srv_worker_thread/README.md)
- [07_row_purge_step](flows/purge/07_row_purge_step/README.md)
- [08_row_purge_record_func](flows/purge/08_row_purge_record_func/README.md)
- [09_row_purge_del_mark](flows/purge/09_row_purge_del_mark/README.md)
- [10_trx_purge_truncate](flows/purge/10_trx_purge_truncate/README.md)

### [페이지 플러시, doublewrite, 체크포인트](flows/flush-checkpoint/README.md)

- [01_buf_flush_page_coordinator_thread](flows/flush-checkpoint/01_buf_flush_page_coordinator_thread/README.md)
- [02_pc_flush_slot](flows/flush-checkpoint/02_pc_flush_slot/README.md)
- [03_buf_flush_do_batch](flows/flush-checkpoint/03_buf_flush_do_batch/README.md)
- [04_buf_flush_page](flows/flush-checkpoint/04_buf_flush_page/README.md)
- [05_buf_flush_write_block_low](flows/flush-checkpoint/05_buf_flush_write_block_low/README.md)
- [06_dblwr.write](flows/flush-checkpoint/06_dblwr.write/README.md)
- [07_Double_write.submit](flows/flush-checkpoint/07_Double_write.submit/README.md)
- [08_log_checkpointer](flows/flush-checkpoint/08_log_checkpointer/README.md)
- [09_log_checkpoint](flows/flush-checkpoint/09_log_checkpoint/README.md)
- [10_log_files_next_checkpoint](flows/flush-checkpoint/10_log_files_next_checkpoint/README.md)

### [크래시 복구](flows/crash-recovery/README.md)

- [01_srv_start](flows/crash-recovery/01_srv_start/README.md)
- [02_recv_recovery_from_checkpoint_start](flows/crash-recovery/02_recv_recovery_from_checkpoint_start/README.md)
- [03_recv_find_max_checkpoint](flows/crash-recovery/03_recv_find_max_checkpoint/README.md)
- [04_recv_recovery_begin](flows/crash-recovery/04_recv_recovery_begin/README.md)
- [05_recv_scan_log_recs](flows/crash-recovery/05_recv_scan_log_recs/README.md)
- [06_recv_parse_log_recs](flows/crash-recovery/06_recv_parse_log_recs/README.md)
- [07_recv_init_crash_recovery](flows/crash-recovery/07_recv_init_crash_recovery/README.md)
- [08_recv_apply_hashed_log_recs](flows/crash-recovery/08_recv_apply_hashed_log_recs/README.md)
- [09_recv_recover_page_func](flows/crash-recovery/09_recv_recover_page_func/README.md)
- [10_recv_recovery_from_checkpoint_finish](flows/crash-recovery/10_recv_recovery_from_checkpoint_finish/README.md)
- [11_Binlog_recovery.recover](flows/crash-recovery/11_Binlog_recovery.recover/README.md)
- [12_trx_rollback_or_clean_recovered](flows/crash-recovery/12_trx_rollback_or_clean_recovered/README.md)

### [온라인 DDL](flows/online-ddl/README.md)

- [01_mysql_inplace_alter_table](flows/online-ddl/01_mysql_inplace_alter_table/README.md)
- [02_ha_innobase.check_if_supported_inplace_alter](flows/online-ddl/02_ha_innobase.check_if_supported_inplace_alter/README.md)
- [03_ha_innobase.prepare_inplace_alter_table](flows/online-ddl/03_ha_innobase.prepare_inplace_alter_table/README.md)
- [04_ha_innobase.inplace_alter_table](flows/online-ddl/04_ha_innobase.inplace_alter_table/README.md)
- [05_ddl.Context.build](flows/online-ddl/05_ddl.Context.build/README.md)
- [06_ddl.Loader.build_all](flows/online-ddl/06_ddl.Loader.build_all/README.md)
- [07_row_log_online_op](flows/online-ddl/07_row_log_online_op/README.md)
- [08_row_log_apply](flows/online-ddl/08_row_log_apply/README.md)
- [09_ha_innobase.commit_inplace_alter_table](flows/online-ddl/09_ha_innobase.commit_inplace_alter_table/README.md)
