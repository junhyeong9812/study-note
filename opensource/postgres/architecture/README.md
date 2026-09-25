# PostgreSQL 아키텍처 지도

소스를 **직접 읽어서** 그리는 탑다운 지도다. 지금은 **목록 단계**다 - 흐름 열세 편의 진입점과 흐름마다 거칠 메서드 목록을 소스로 확인해 두었고, 흐름 문서 본문은 아직 없다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

SQL 문이나 설정 이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 상위: [PostgreSQL](../README.md)

## 두 갈래로 읽는다

```text
 구조  무엇이 있는가          6편 (목록)
       프로세스·공유 메모리·페이지처럼 자리에 관한 것

 흐름  무엇이 일어나는가      13편, 129개 문서 예정
       요청 하나가 지나는 길을 함수 단위로 따라간다
       폴더 하나 = 함수 하나
```

## 흐름 열세 편

오른쪽 칸은 같은 문제를 [db-engine](https://github.com/junhyeong9812/db-engine)(직접 만든 교육용 DB 엔진)에서 다루는 챕터다. 일치하는 흐름에만 적었다.

| 흐름 | 진입점 | 문서 | db-engine 대응 |
|---|---|---|---|
| 연결과 backend 기동 | `ServerLoop` `postmaster/postmaster.c` L1653 | 9 | [13-01-connection-pool](../../../project/db-engine/13-01-connection-pool/) · [14-01-protocol-handler](../../../project/db-engine/14-01-protocol-handler/) · [15-01-auth](../../../project/db-engine/15-01-auth/) |
| 쿼리 실행 파이프라인 | `exec_simple_query` `tcop/postgres.c` L1012 | 10 | [12-01-sql-parser](../../../project/db-engine/12-01-sql-parser/) · [13-02-sql-translator](../../../project/db-engine/13-02-sql-translator/) · [14-00-db-engine](../../../project/db-engine/14-00-db-engine/) |
| executor | `standard_ExecutorRun` `executor/execMain.c` L307 | 10 | [06-01-table-seqscan](../../../project/db-engine/06-01-table-seqscan/) · [06-02-filter-project-expression](../../../project/db-engine/06-02-filter-project-expression/) |
| 행 쓰기와 WAL 기록 | `heap_insert` `access/heap/heapam.c` L2081 | 10 | [06-01-table-seqscan](../../../project/db-engine/06-01-table-seqscan/) · [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) |
| 버퍼 관리 | `ReadBufferExtended` `storage/buffer/bufmgr.c` L805 | 10 | [02-01-page-pagedfile](../../../project/db-engine/02-01-page-pagedfile/) · [02-02-buffer-pool](../../../project/db-engine/02-02-buffer-pool/) |
| MVCC 가시성과 스냅샷 | `GetTransactionSnapshot` `utils/time/snapmgr.c` L271 | 10 | [10-01-mvcc](../../../project/db-engine/10-01-mvcc/) · [10-02-isolation-anomaly](../../../project/db-engine/10-02-isolation-anomaly/) · [10-03-mvcc-table-heap](../../../project/db-engine/10-03-mvcc-table-heap/) |
| nbtree 삽입과 분할 | `btinsert` `access/nbtree/nbtree.c` L202 | 10 | [03-01-btree-leaf-only](../../../project/db-engine/03-01-btree-leaf-only/) · [03-02-btree-split](../../../project/db-engine/03-02-btree-split/) · [06-04-indexed-table-heap](../../../project/db-engine/06-04-indexed-table-heap/) |
| heavyweight lock | `LockAcquireExtended` `storage/lmgr/lock.c` L835 | 10 | [09-01-lock-manager](../../../project/db-engine/09-01-lock-manager/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| 커밋 | `CommitTransaction` `access/transam/xact.c` L2228 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [09-02-transaction-lock-integration](../../../project/db-engine/09-02-transaction-lock-integration/) |
| vacuum | `ExecVacuum` `commands/vacuum.c` L162 | 10 | 없음 - [10-03](../../../project/db-engine/10-03-mvcc-table-heap/) 이 "다음 한계"로 예고한 자리 |
| 체크포인트 | `CheckpointerMain` `postmaster/checkpointer.c` L182 | 10 | [08-02-lsn-checkpoint](../../../project/db-engine/08-02-lsn-checkpoint/) |
| WAL redo (복구) | `StartupXLOG` `access/transam/xlog.c` L5467 | 10 | [08-01-wal-recovery](../../../project/db-engine/08-01-wal-recovery/) · [08-03-crash-simulation](../../../project/db-engine/08-03-crash-simulation/) |
| 스트리밍 복제 | `StartReplication` `replication/walsender.c` L809 | 10 | [18-01-replication](../../../project/db-engine/18-01-replication/) |

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

## 구조 여섯 편 (목록)

| 편 | 대표 자리 |
|---|---|
| 프로세스 모델 | `postmaster/launch_backend.c` L179 `child_process_kinds[]`, `postmaster.c` L2865 `PostmasterStateMachine` |
| 공유 메모리 | `storage/ipc/ipci.c` L200 `CreateSharedMemoryAndSemaphores`, `src/include/storage/proc.h` L176 `PGPROC` |
| 페이지와 튜플 레이아웃 | `src/include/storage/bufpage.h` L159 `PageHeaderData`, `src/include/access/htup_details.h` L153 `HeapTupleHeaderData` |
| 디스크 배치 | `src/common/relpath.c` L143 `GetRelationPath`, `src/include/catalog/pg_control.h` L104 `ControlFileData` |
| WAL 레코드 형식 | `src/include/access/xlogrecord.h` L41 `XLogRecord`, L103 `XLogRecordBlockHeader` |
| 버퍼 디스크립터와 스냅샷 | `src/include/storage/buf_internals.h` L258 `BufferDesc`, `src/include/utils/snapshot.h` L138 `SnapshotData` |

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

## 흐름별 함수 목록

흐름 문서를 쓸 때 폴더가 될 함수들이다. `파일:줄`은 모두 정의 줄이다.

### 연결과 backend 기동 (`flows/connection-startup/`)

```text
 01_ServerLoop postmaster.c:1653
 02_BackendStartup postmaster.c:3518
 03_postmaster_child_launch launch_backend.c:229
 04_BackendMain backend_startup.c:76
 05_BackendInitialize backend_startup.c:141
 06_ProcessStartupPacket backend_startup.c:492
 07_PostgresMain postgres.c:4188
 08_InitPostgres postinit.c:712
 09_PerformAuthentication postinit.c:194
```

### 쿼리 실행 파이프라인 (`flows/query-pipeline/`)

```text
 01_exec_simple_query postgres.c:1012
 02_pg_parse_query postgres.c:604
 03_pg_analyze_and_rewrite_fixedparams postgres.c:666
 04_parse_analyze_fixedparams analyze.c:105
 05_pg_rewrite_query postgres.c:799
 06_pg_plan_query postgres.c:883
 07_standard_planner planner.c:316
 08_grouping_planner planner.c:1567
 09_PortalStart pquery.c:434
 10_PortalRun pquery.c:685
```

### executor (`flows/executor/`)

```text
 01_standard_ExecutorStart execMain.c:141
 02_InitPlan execMain.c:836
 03_ExecInitNode execProcnode.c:142
 04_standard_ExecutorRun execMain.c:307
 05_ExecutePlan execMain.c:1660
 06_ExecProcNodeFirst execProcnode.c:448
 07_ExecSeqScan nodeSeqscan.c:110
 08_ExecModifyTable nodeModifyTable.c:4175
 09_ExecInsert nodeModifyTable.c:850
 10_ExecutorEnd execMain.c:466
```

### 행 쓰기와 WAL 기록 (`flows/heap-insert-wal/`)

```text
 01_heapam_tuple_insert heapam_handler.c:244
 02_heap_insert heapam.c:2081
 03_heap_prepare_insert heapam.c:2298
 04_RelationGetBufferForTuple hio.c:502
 05_RelationPutHeapTuple hio.c:35
 06_XLogInsert xloginsert.c:474
 07_XLogRecordAssemble xloginsert.c:548
 08_XLogInsertRecord xlog.c:748
 09_ReserveXLogInsertLocation xlog.c:1111
 10_XLogFlush xlog.c:2780
```

### 버퍼 관리 (`flows/buffer-manager/`)

```text
 01_ReadBufferExtended bufmgr.c:805
 02_ReadBuffer_common bufmgr.c:1184
 03_PinBufferForBlock bufmgr.c:1101
 04_BufferAlloc bufmgr.c:2009
 05_GetVictimBuffer bufmgr.c:2354
 06_StrategyGetBuffer freelist.c:196
 07_FlushBuffer bufmgr.c:4307
 08_WaitReadBuffers bufmgr.c:1641
 09_PinBuffer bufmgr.c:3090
 10_LockBuffer bufmgr.c:5623
```

### MVCC 가시성과 스냅샷 (`flows/mvcc-visibility/`)

```text
 01_GetTransactionSnapshot snapmgr.c:271
 02_GetSnapshotData procarray.c:2175
 03_heap_getnextslot heapam.c:1388
 04_heapgettup_pagemode heapam.c:1010
 05_heap_prepare_pagescan heapam.c:556
 06_page_collect_tuples heapam.c:506
 07_HeapTupleSatisfiesVisibility heapam_visibility.c:1776
 08_HeapTupleSatisfiesMVCC heapam_visibility.c:960
 09_XidInMVCCSnapshot snapmgr.c:1870
 10_TransactionIdDidCommit transam.c:126
```

### nbtree 삽입과 분할 (`flows/nbtree-insert/`)

```text
 01_ExecInsertIndexTuples execIndexing.c:310
 02_index_insert indexam.c:213
 03_btinsert nbtree.c:202
 04__bt_doinsert nbtinsert.c:102
 05__bt_search_insert nbtinsert.c:317
 06__bt_check_unique nbtinsert.c:408
 07__bt_findinsertloc nbtinsert.c:815
 08__bt_insertonpg nbtinsert.c:1105
 09__bt_split nbtinsert.c:1467
 10__bt_insert_parent nbtinsert.c:2099
```

### heavyweight lock (`flows/heavyweight-lock/`)

```text
 01_LockRelationOid lmgr.c:107
 02_LockAcquireExtended lock.c:835
 03_FastPathGrantRelationLock lock.c:2750
 04_SetupLockInTable lock.c:1282
 05_LockCheckConflicts lock.c:1528
 06_GrantLock lock.c:1657
 07_WaitOnLock lock.c:1931
 08_ProcSleep proc.c:1342
 09_CheckDeadLock proc.c:1820
 10_LockReleaseAll lock.c:2275
```

### 커밋 (`flows/commit/`)

```text
 01_finish_xact_command postgres.c:2826
 02_CommitTransactionCommandInternal xact.c:3175
 03_StartTransaction xact.c:2064
 04_CommitTransaction xact.c:2228
 05_RecordTransactionCommit xact.c:1315
 06_XactLogCommitRecord xact.c:5814
 07_TransactionIdCommitTree transam.c:240
 08_ProcArrayEndTransaction procarray.c:667
 09_SyncRepWaitForLSN syncrep.c:148
 10_AssignTransactionId xact.c:635
```

### vacuum (`flows/vacuum/`)

```text
 01_ExecVacuum vacuum.c:162
 02_vacuum vacuum.c:500
 03_vacuum_rel vacuum.c:2018
 04_heap_vacuum_rel vacuumlazy.c:615
 05_lazy_scan_heap vacuumlazy.c:1200
 06_lazy_scan_prune vacuumlazy.c:1958
 07_lazy_vacuum vacuumlazy.c:2464
 08_lazy_vacuum_all_indexes vacuumlazy.c:2589
 09_lazy_vacuum_heap_rel vacuumlazy.c:2734
 10_vac_update_relstats vacuum.c:1442
```

### 체크포인트 (`flows/checkpoint/`)

```text
 01_CheckpointerMain checkpointer.c:182
 02_RequestCheckpoint checkpointer.c:1003
 03_CreateCheckPoint xlog.c:6929
 04_CheckPointGuts xlog.c:7552
 05_CheckPointBuffers bufmgr.c:4233
 06_BufferSync bufmgr.c:3367
 07_SyncOneBuffer bufmgr.c:3941
 08_CheckpointWriteDelay checkpointer.c:772
 09_ProcessSyncRequests sync.c:286
 10_RemoveOldXlogFiles xlog.c:3861
```

### WAL redo (복구) (`flows/wal-redo/`)

```text
 01_StartupProcessMain startup.c:216
 02_StartupXLOG xlog.c:5467
 03_InitWalRecovery xlogrecovery.c:519
 04_PerformWalRecovery xlogrecovery.c:1680
 05_ReadRecord xlogrecovery.c:3162
 06_ApplyWalRecord xlogrecovery.c:1937
 07_heap_redo heapam_xlog.c:1307
 08_heap_xlog_insert heapam_xlog.c:477
 09_XLogReadBufferForRedoExtended xlogutils.c:362
 10_WaitForWALToBecomeAvailable xlogrecovery.c:3586
```

### 스트리밍 복제 (`flows/streaming-replication/`)

```text
 01_exec_replication_command walsender.c:2012
 02_StartReplication walsender.c:809
 03_WalSndLoop walsender.c:2828
 04_XLogSendPhysical walsender.c:3140
 05_ProcessStandbyReplyMessage walsender.c:2445
 06_WalReceiverMain walreceiver.c:159
 07_XLogWalRcvProcessMsg walreceiver.c:896
 08_XLogWalRcvWrite walreceiver.c:967
 09_XLogWalRcvFlush walreceiver.c:1062
 10_XLogWalRcvSendReply walreceiver.c:1169
```
