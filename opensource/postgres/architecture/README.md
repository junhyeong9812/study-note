# PostgreSQL 아키텍처 지도

소스를 **직접 읽어서** 그리는 탑다운 지도다. 흐름 열세 편(함수 문서 137편)과 구조 여섯 편으로 되어 있고, 모든 코드 인용과 줄 번호는 작성과 별도로 소스와 대조해 검증했다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

SQL 문이나 설정 이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 상위: [PostgreSQL](../README.md)

## 두 갈래로 읽는다

```text
 구조  무엇이 있는가          6편
       프로세스·공유 메모리·페이지처럼 자리에 관한 것

 흐름  무엇이 일어나는가      13편, 함수 문서 137편
       요청 하나가 지나는 길을 함수 단위로 따라간다
       폴더 하나 = 함수 하나
```

## 흐름 열세 편

오른쪽 칸은 같은 문제를 [db-engine](https://github.com/junhyeong9812/db-engine)(직접 만든 교육용 DB 엔진)에서 다루는 챕터다. 일치하는 흐름에만 적었다.

| 흐름 | 진입점 | 문서 | db-engine 대응 |
|---|---|---|---|
| [연결과 backend 기동](flows/connection-startup/README.md) | `ServerLoop` `postmaster/postmaster.c` L1653 | 9 | [13-01-connection-pool](../../../project/db-engine/13-01-connection-pool/) · [14-01-protocol-handler](../../../project/db-engine/14-01-protocol-handler/) · [15-01-auth](../../../project/db-engine/15-01-auth/) |
| [쿼리 실행 파이프라인](flows/query-pipeline/README.md) | `exec_simple_query` `tcop/postgres.c` L1012 | 10 | [12-01-sql-parser](../../../project/db-engine/12-01-sql-parser/) · [13-02-sql-translator](../../../project/db-engine/13-02-sql-translator/) · [14-00-db-engine](../../../project/db-engine/14-00-db-engine/) |
| [executor](flows/executor/README.md) | `standard_ExecutorRun` `executor/execMain.c` L307 | 10 | [06-01-table-seqscan](../../../project/db-engine/06-01-table-seqscan/) · [06-02-filter-project-expression](../../../project/db-engine/06-02-filter-project-expression/) |
| [행 쓰기와 WAL 기록](flows/heap-insert-wal/README.md) | `heap_insert` `access/heap/heapam.c` L2081 | 10 | [06-01-table-seqscan](../../../project/db-engine/06-01-table-seqscan/) · [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) |
| [버퍼 관리](flows/buffer-manager/README.md) | `ReadBufferExtended` `storage/buffer/bufmgr.c` L805 | 11 | [02-01-page-pagedfile](../../../project/db-engine/02-01-page-pagedfile/) · [02-02-buffer-pool](../../../project/db-engine/02-02-buffer-pool/) |
| [MVCC 가시성과 스냅샷](flows/mvcc-visibility/README.md) | `GetTransactionSnapshot` `utils/time/snapmgr.c` L271 | 10 | [10-01-mvcc](../../../project/db-engine/10-01-mvcc/) · [10-02-isolation-anomaly](../../../project/db-engine/10-02-isolation-anomaly/) · [10-03-mvcc-table-heap](../../../project/db-engine/10-03-mvcc-table-heap/) |
| [nbtree 삽입과 분할](flows/nbtree-insert/README.md) | `btinsert` `access/nbtree/nbtree.c` L202 | 12 | [03-01-btree-leaf-only](../../../project/db-engine/03-01-btree-leaf-only/) · [03-02-btree-split](../../../project/db-engine/03-02-btree-split/) · [06-04-indexed-table-heap](../../../project/db-engine/06-04-indexed-table-heap/) |
| [heavyweight lock](flows/heavyweight-lock/README.md) | `LockAcquireExtended` `storage/lmgr/lock.c` L835 | 11 | [09-01-lock-manager](../../../project/db-engine/09-01-lock-manager/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| [커밋](flows/commit/README.md) | `CommitTransaction` `access/transam/xact.c` L2228 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| [vacuum](flows/vacuum/README.md) | `ExecVacuum` `commands/vacuum.c` L162 | 13 | 없음 - db-engine 에는 정리 기능이 없다 ([10-01](../../../project/db-engine/10-01-mvcc/) 과제 3 답, [10-03](../../../project/db-engine/10-03-mvcc-table-heap/) MVCCTableHeap 주석) |
| [체크포인트](flows/checkpoint/README.md) | `CheckpointerMain` `postmaster/checkpointer.c` L182 | 9 | [08-02-lsn-checkpoint](../../../project/db-engine/08-02-lsn-checkpoint/) |
| [WAL redo (복구)](flows/wal-redo/README.md) | `StartupXLOG` `access/transam/xlog.c` L5467 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [08-03-crash-simulation](../../../project/db-engine/08-03-crash-simulation/) |
| [스트리밍 복제](flows/streaming-replication/README.md) | `StartReplication` `replication/walsender.c` L809 | 12 | [18-01-replication](../../../project/db-engine/18-01-replication/) |

## 흐름이 이어지는 자리

```text
 한 backend 안 - SQL 하나가 지나는 길

 [연결과 backend 기동]  PostgresMain 이 메시지를 읽는다 (postgres.c L4754)
      |  'Q' 메시지
      v
 [쿼리 실행 파이프라인]  start_xact_command ... finish_xact_command
      |  parse -> analyze -> rewrite -> plan -> Portal
      v
 [executor]
      +-- ExecInsert  -> table_tuple_insert    -> [행 쓰기와 WAL 기록]
      |               -> ExecInsertIndexTuples -> [nbtree 삽입과 분할]
      +-- SeqNext     -> table_scan_getnextslot -> [MVCC 가시성과 스냅샷]
      v
 [커밋]  RecordTransactionCommit -> XLogFlush (xact.c L1502)
```

```text
 모두의 바닥

 [행 쓰기] [MVCC] [nbtree] [vacuum] 은 전부
 [버퍼 관리] 의 ReadBuffer 계열과 LockBuffer 위에서 돈다

 [버퍼 관리] FlushBuffer 는 페이지를 쓰기 전에 XLogFlush 를 먼저 부른다
   (bufmgr.c L4371)  -  WAL 이 데이터보다 먼저 디스크에 간다
```

```text
 backend 밖 - 백그라운드 프로세스

 [체크포인트]   checkpointer 가 BufferSync 로 더러운 페이지를 내려 쓴다
 [vacuum]      autovacuum launcher/worker 가 죽은 튜플을 치운다
 [WAL redo]    startup 프로세스가 rm_redo 로 레코드를 되감는다 (xlogrecovery.c L2020)
                 heap 레코드면 heap_redo 로 간다
 [스트리밍 복제] walsender 가 WAL 을 보내고 standby 의 walreceiver 가 받는다
                 동기 복제면 [커밋] 의 SyncRepWaitForLSN 을 walsender 가 깨운다
```

## 구조 여섯 편

| 편 | 대표 자리 |
|---|---|
| [프로세스 모델](structure/process-model/README.md) | `postmaster/launch_backend.c` L179 `child_process_kinds[]`, `postmaster.c` L2865 `PostmasterStateMachine` |
| [공유 메모리](structure/shared-memory/README.md) | `storage/ipc/ipci.c` L200 `CreateSharedMemoryAndSemaphores`, `src/include/storage/proc.h` L176 `PGPROC` |
| [페이지와 튜플 레이아웃](structure/page-tuple-layout/README.md) | `src/include/storage/bufpage.h` L159 `PageHeaderData`, `src/include/access/htup_details.h` L153 `HeapTupleHeaderData` |
| [디스크 배치](structure/disk-layout/README.md) | `src/common/relpath.c` L143 `GetRelationPath`, `src/include/catalog/pg_control.h` L104 `ControlFileData` |
| [WAL 레코드 형식](structure/wal-record-format/README.md) | `src/include/access/xlogrecord.h` L41 `XLogRecord`, L103 `XLogRecordBlockHeader` |
| [버퍼 디스크립터와 스냅샷](structure/buffer-descriptor-snapshot/README.md) | `src/include/storage/buf_internals.h` L258 `BufferDesc`, `src/include/utils/snapshot.h` L138 `SnapshotData` |

## 읽는 순서

```text
 처음이면
   [구조: 프로세스 모델] -> [연결과 backend 기동] -> [쿼리 실행 파이프라인]

 쓰기를 알고 싶으면
   [executor] -> [행 쓰기와 WAL 기록] -> [nbtree 삽입과 분할] -> [커밋]

 읽기를 알고 싶으면
   [executor] -> [MVCC 가시성과 스냅샷] -> [버퍼 관리]

 장애와 복구가 궁금하면
   [체크포인트] -> [WAL redo] -> [스트리밍 복제]
```

## 흐름별 함수 문서

폴더 하나가 함수 하나다. 곁가지 함수는 가까운 함수 문서 안에서 함께 다룬다. pgvector 확장은 [따로 지도](../pgvector/architecture/README.md)가 있다.

### [연결과 backend 기동](flows/connection-startup/README.md)

- [01_ServerLoop](flows/connection-startup/01_ServerLoop/README.md)
- [02_BackendStartup](flows/connection-startup/02_BackendStartup/README.md)
- [03_postmaster_child_launch](flows/connection-startup/03_postmaster_child_launch/README.md)
- [04_BackendMain](flows/connection-startup/04_BackendMain/README.md)
- [05_BackendInitialize](flows/connection-startup/05_BackendInitialize/README.md)
- [06_ProcessStartupPacket](flows/connection-startup/06_ProcessStartupPacket/README.md)
- [07_PostgresMain](flows/connection-startup/07_PostgresMain/README.md)
- [08_InitPostgres](flows/connection-startup/08_InitPostgres/README.md)
- [09_PerformAuthentication](flows/connection-startup/09_PerformAuthentication/README.md)

### [쿼리 실행 파이프라인](flows/query-pipeline/README.md)

- [01_exec_simple_query](flows/query-pipeline/01_exec_simple_query/README.md)
- [02_pg_parse_query](flows/query-pipeline/02_pg_parse_query/README.md)
- [03_pg_analyze_and_rewrite_fixedparams](flows/query-pipeline/03_pg_analyze_and_rewrite_fixedparams/README.md)
- [04_parse_analyze_fixedparams](flows/query-pipeline/04_parse_analyze_fixedparams/README.md)
- [05_pg_rewrite_query](flows/query-pipeline/05_pg_rewrite_query/README.md)
- [06_pg_plan_query](flows/query-pipeline/06_pg_plan_query/README.md)
- [07_standard_planner](flows/query-pipeline/07_standard_planner/README.md)
- [08_grouping_planner](flows/query-pipeline/08_grouping_planner/README.md)
- [09_PortalStart](flows/query-pipeline/09_PortalStart/README.md)
- [10_PortalRun](flows/query-pipeline/10_PortalRun/README.md)

### [executor](flows/executor/README.md)

- [01_standard_ExecutorStart](flows/executor/01_standard_ExecutorStart/README.md)
- [02_InitPlan](flows/executor/02_InitPlan/README.md)
- [03_ExecInitNode](flows/executor/03_ExecInitNode/README.md)
- [04_standard_ExecutorRun](flows/executor/04_standard_ExecutorRun/README.md)
- [05_ExecutePlan](flows/executor/05_ExecutePlan/README.md)
- [06_ExecProcNodeFirst](flows/executor/06_ExecProcNodeFirst/README.md)
- [07_ExecSeqScan](flows/executor/07_ExecSeqScan/README.md)
- [08_ExecModifyTable](flows/executor/08_ExecModifyTable/README.md)
- [09_ExecInsert](flows/executor/09_ExecInsert/README.md)
- [10_standard_ExecutorFinish](flows/executor/10_standard_ExecutorFinish/README.md)

### [행 쓰기와 WAL 기록](flows/heap-insert-wal/README.md)

- [01_heapam_tuple_insert](flows/heap-insert-wal/01_heapam_tuple_insert/README.md)
- [02_heap_insert](flows/heap-insert-wal/02_heap_insert/README.md)
- [03_heap_prepare_insert](flows/heap-insert-wal/03_heap_prepare_insert/README.md)
- [04_RelationGetBufferForTuple](flows/heap-insert-wal/04_RelationGetBufferForTuple/README.md)
- [05_RelationPutHeapTuple](flows/heap-insert-wal/05_RelationPutHeapTuple/README.md)
- [06_XLogInsert](flows/heap-insert-wal/06_XLogInsert/README.md)
- [07_XLogRecordAssemble](flows/heap-insert-wal/07_XLogRecordAssemble/README.md)
- [08_XLogInsertRecord](flows/heap-insert-wal/08_XLogInsertRecord/README.md)
- [09_ReserveXLogInsertLocation](flows/heap-insert-wal/09_ReserveXLogInsertLocation/README.md)
- [10_XLogFlush](flows/heap-insert-wal/10_XLogFlush/README.md)

### [버퍼 관리](flows/buffer-manager/README.md)

- [01_ReadBufferExtended](flows/buffer-manager/01_ReadBufferExtended/README.md)
- [02_ReadBuffer_common](flows/buffer-manager/02_ReadBuffer_common/README.md)
- [03_StartReadBuffersImpl](flows/buffer-manager/03_StartReadBuffersImpl/README.md)
- [04_PinBufferForBlock](flows/buffer-manager/04_PinBufferForBlock/README.md)
- [05_BufferAlloc](flows/buffer-manager/05_BufferAlloc/README.md)
- [06_PinBuffer](flows/buffer-manager/06_PinBuffer/README.md)
- [07_GetVictimBuffer](flows/buffer-manager/07_GetVictimBuffer/README.md)
- [08_StrategyGetBuffer](flows/buffer-manager/08_StrategyGetBuffer/README.md)
- [09_FlushBuffer](flows/buffer-manager/09_FlushBuffer/README.md)
- [10_AsyncReadBuffers](flows/buffer-manager/10_AsyncReadBuffers/README.md)
- [11_WaitReadBuffers](flows/buffer-manager/11_WaitReadBuffers/README.md)

### [MVCC 가시성과 스냅샷](flows/mvcc-visibility/README.md)

- [01_GetTransactionSnapshot](flows/mvcc-visibility/01_GetTransactionSnapshot/README.md)
- [02_GetSnapshotData](flows/mvcc-visibility/02_GetSnapshotData/README.md)
- [03_heap_getnextslot](flows/mvcc-visibility/03_heap_getnextslot/README.md)
- [04_heapgettup_pagemode](flows/mvcc-visibility/04_heapgettup_pagemode/README.md)
- [05_heap_prepare_pagescan](flows/mvcc-visibility/05_heap_prepare_pagescan/README.md)
- [06_page_collect_tuples](flows/mvcc-visibility/06_page_collect_tuples/README.md)
- [07_HeapTupleSatisfiesVisibility](flows/mvcc-visibility/07_HeapTupleSatisfiesVisibility/README.md)
- [08_HeapTupleSatisfiesMVCC](flows/mvcc-visibility/08_HeapTupleSatisfiesMVCC/README.md)
- [09_XidInMVCCSnapshot](flows/mvcc-visibility/09_XidInMVCCSnapshot/README.md)
- [10_TransactionIdDidCommit](flows/mvcc-visibility/10_TransactionIdDidCommit/README.md)

### [nbtree 삽입과 분할](flows/nbtree-insert/README.md)

- [01_ExecInsertIndexTuples](flows/nbtree-insert/01_ExecInsertIndexTuples/README.md)
- [02_index_insert](flows/nbtree-insert/02_index_insert/README.md)
- [03_btinsert](flows/nbtree-insert/03_btinsert/README.md)
- [04__bt_doinsert](flows/nbtree-insert/04__bt_doinsert/README.md)
- [05__bt_search_insert](flows/nbtree-insert/05__bt_search_insert/README.md)
- [06__bt_check_unique](flows/nbtree-insert/06__bt_check_unique/README.md)
- [07__bt_findinsertloc](flows/nbtree-insert/07__bt_findinsertloc/README.md)
- [08__bt_insertonpg](flows/nbtree-insert/08__bt_insertonpg/README.md)
- [09__bt_split](flows/nbtree-insert/09__bt_split/README.md)
- [10__bt_findsplitloc](flows/nbtree-insert/10__bt_findsplitloc/README.md)
- [11__bt_insert_parent](flows/nbtree-insert/11__bt_insert_parent/README.md)
- [12__bt_newlevel](flows/nbtree-insert/12__bt_newlevel/README.md)

### [heavyweight lock](flows/heavyweight-lock/README.md)

- [01_LockRelationOid](flows/heavyweight-lock/01_LockRelationOid/README.md)
- [02_LockAcquireExtended](flows/heavyweight-lock/02_LockAcquireExtended/README.md)
- [03_FastPathGrantRelationLock](flows/heavyweight-lock/03_FastPathGrantRelationLock/README.md)
- [04_FastPathTransferRelationLocks](flows/heavyweight-lock/04_FastPathTransferRelationLocks/README.md)
- [05_SetupLockInTable](flows/heavyweight-lock/05_SetupLockInTable/README.md)
- [06_LockCheckConflicts](flows/heavyweight-lock/06_LockCheckConflicts/README.md)
- [07_GrantLock](flows/heavyweight-lock/07_GrantLock/README.md)
- [08_JoinWaitQueue](flows/heavyweight-lock/08_JoinWaitQueue/README.md)
- [09_ProcSleep](flows/heavyweight-lock/09_ProcSleep/README.md)
- [10_CheckDeadLock](flows/heavyweight-lock/10_CheckDeadLock/README.md)
- [11_LockReleaseAll](flows/heavyweight-lock/11_LockReleaseAll/README.md)

### [커밋](flows/commit/README.md)

- [01_StartTransactionCommand](flows/commit/01_StartTransactionCommand/README.md)
- [02_StartTransaction](flows/commit/02_StartTransaction/README.md)
- [03_AssignTransactionId](flows/commit/03_AssignTransactionId/README.md)
- [04_CommitTransactionCommandInternal](flows/commit/04_CommitTransactionCommandInternal/README.md)
- [05_CommitTransaction](flows/commit/05_CommitTransaction/README.md)
- [06_RecordTransactionCommit](flows/commit/06_RecordTransactionCommit/README.md)
- [07_XactLogCommitRecord](flows/commit/07_XactLogCommitRecord/README.md)
- [08_TransactionIdCommitTree](flows/commit/08_TransactionIdCommitTree/README.md)
- [09_SyncRepWaitForLSN](flows/commit/09_SyncRepWaitForLSN/README.md)
- [10_ProcArrayEndTransaction](flows/commit/10_ProcArrayEndTransaction/README.md)

### [vacuum](flows/vacuum/README.md)

- [01_ExecVacuum](flows/vacuum/01_ExecVacuum/README.md)
- [02_vacuum](flows/vacuum/02_vacuum/README.md)
- [03_AutoVacLauncherMain](flows/vacuum/03_AutoVacLauncherMain/README.md)
- [04_do_autovacuum](flows/vacuum/04_do_autovacuum/README.md)
- [05_vacuum_rel](flows/vacuum/05_vacuum_rel/README.md)
- [06_heap_vacuum_rel](flows/vacuum/06_heap_vacuum_rel/README.md)
- [07_vacuum_get_cutoffs](flows/vacuum/07_vacuum_get_cutoffs/README.md)
- [08_lazy_scan_heap](flows/vacuum/08_lazy_scan_heap/README.md)
- [09_lazy_scan_prune](flows/vacuum/09_lazy_scan_prune/README.md)
- [10_heap_page_prune_and_freeze](flows/vacuum/10_heap_page_prune_and_freeze/README.md)
- [11_lazy_vacuum](flows/vacuum/11_lazy_vacuum/README.md)
- [12_lazy_vacuum_heap_rel](flows/vacuum/12_lazy_vacuum_heap_rel/README.md)
- [13_vac_update_relstats](flows/vacuum/13_vac_update_relstats/README.md)

### [체크포인트](flows/checkpoint/README.md)

- [01_CheckpointerMain](flows/checkpoint/01_CheckpointerMain/README.md)
- [02_RequestCheckpoint](flows/checkpoint/02_RequestCheckpoint/README.md)
- [03_CreateCheckPoint](flows/checkpoint/03_CreateCheckPoint/README.md)
- [04_CheckPointGuts](flows/checkpoint/04_CheckPointGuts/README.md)
- [05_BufferSync](flows/checkpoint/05_BufferSync/README.md)
- [06_SyncOneBuffer](flows/checkpoint/06_SyncOneBuffer/README.md)
- [07_CheckpointWriteDelay](flows/checkpoint/07_CheckpointWriteDelay/README.md)
- [08_ProcessSyncRequests](flows/checkpoint/08_ProcessSyncRequests/README.md)
- [09_RemoveOldXlogFiles](flows/checkpoint/09_RemoveOldXlogFiles/README.md)

### [WAL redo (복구)](flows/wal-redo/README.md)

- [01_StartupProcessMain](flows/wal-redo/01_StartupProcessMain/README.md)
- [02_StartupXLOG](flows/wal-redo/02_StartupXLOG/README.md)
- [03_InitWalRecovery](flows/wal-redo/03_InitWalRecovery/README.md)
- [04_PerformWalRecovery](flows/wal-redo/04_PerformWalRecovery/README.md)
- [05_ReadRecord](flows/wal-redo/05_ReadRecord/README.md)
- [06_ApplyWalRecord](flows/wal-redo/06_ApplyWalRecord/README.md)
- [07_heap_redo](flows/wal-redo/07_heap_redo/README.md)
- [08_heap_xlog_insert](flows/wal-redo/08_heap_xlog_insert/README.md)
- [09_XLogReadBufferForRedoExtended](flows/wal-redo/09_XLogReadBufferForRedoExtended/README.md)
- [10_WaitForWALToBecomeAvailable](flows/wal-redo/10_WaitForWALToBecomeAvailable/README.md)

### [스트리밍 복제](flows/streaming-replication/README.md)

- [01_RequestXLogStreaming](flows/streaming-replication/01_RequestXLogStreaming/README.md)
- [02_WalReceiverMain](flows/streaming-replication/02_WalReceiverMain/README.md)
- [03_exec_replication_command](flows/streaming-replication/03_exec_replication_command/README.md)
- [04_StartReplication](flows/streaming-replication/04_StartReplication/README.md)
- [05_WalSndLoop](flows/streaming-replication/05_WalSndLoop/README.md)
- [06_XLogSendPhysical](flows/streaming-replication/06_XLogSendPhysical/README.md)
- [07_XLogWalRcvProcessMsg](flows/streaming-replication/07_XLogWalRcvProcessMsg/README.md)
- [08_XLogWalRcvWrite](flows/streaming-replication/08_XLogWalRcvWrite/README.md)
- [09_XLogWalRcvFlush](flows/streaming-replication/09_XLogWalRcvFlush/README.md)
- [10_XLogWalRcvSendReply](flows/streaming-replication/10_XLogWalRcvSendReply/README.md)
- [11_ProcessStandbyReplyMessage](flows/streaming-replication/11_ProcessStandbyReplyMessage/README.md)
- [12_SyncRepReleaseWaiters](flows/streaming-replication/12_SyncRepReleaseWaiters/README.md)
