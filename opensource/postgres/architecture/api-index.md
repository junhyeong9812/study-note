# API 역인덱스

상위: [PostgreSQL 아키텍처 지도](README.md)

"이 SQL 문·설정을 쓰면 어느 흐름들을 지나는가"를 뒤에서부터 찾는 표다. 흐름 문서가 함수에서 출발한다면 이 표는 **SQL 문과 GUC 이름에서 출발한다.**

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 범위를 먼저 밝힌다

```text
 이 표는 SQL 문과 GUC 를 전부 담지 않는다
 흐름 열세 편이 실제로 덮는 길만 적었다

 안 덮는 API 도 아래에 따로 적어 두었다 - 없는 것을 있는 척하지 않으려고
```

표의 흐름 이름은 [지도의 흐름 표](README.md#흐름-열세-편)에서 각 흐름 문서로 이어진다.

## 모든 SQL 이 공유하는 앞단

```text
 클라이언트
   |
   v
 [연결과 backend 기동]   ServerLoop -> BackendStartup -> PostgresMain (postgres.c L4188)
   |  ReadCommand (L4702), 'Q' 메시지 (L4754)
   v
 [쿼리 실행 파이프라인]  exec_simple_query (L1012)
   |  parse -> analyze -> rewrite -> plan -> PortalStart -> PortalRun (pquery.c L685)
   |
   +-- 최적화 가능한 문장   ProcessQuery / PortalRunSelect -> [executor]
   +-- utility 문장        PortalRunUtility (pquery.c L1122)
   |                        -> standard_ProcessUtility (utility.c L543) 의 case 로 갈린다
   v
 finish_xact_command -> [커밋]
```

## 읽기와 쓰기 (DML)

| SQL | 진입 자리 | 뒤이어 지나는 흐름 |
|---|---|---|
| `SELECT` | `analyze.c` L367 `T_SelectStmt` -> `PortalRunSelect` (pquery.c L765) | executor -> MVCC 가시성과 스냅샷 -> 버퍼 관리 |
| `INSERT` | `analyze.c` L351 -> `ExecModifyTable` (nodeModifyTable.c L4509) -> `ExecInsert` | executor -> 행 쓰기와 WAL 기록 -> nbtree 삽입과 분할 -> 커밋 |
| `UPDATE` | `analyze.c` L359 -> `ExecUpdate` (nodeModifyTable.c L2461) -> `heap_update` (heapam.c L3321) | executor -> 행 쓰기와 WAL 기록(변형) -> MVCC -> nbtree |
| `DELETE` | `analyze.c` L355 -> `ExecDelete` (nodeModifyTable.c L1572) -> `heap_delete` (heapam.c L2828) | executor -> 행 쓰기와 WAL 기록(변형) -> MVCC |
| `MERGE` | `analyze.c` L363 -> `ExecMerge` (nodeModifyTable.c L2950) | INSERT·UPDATE·DELETE 와 같다 |
| `COPY FROM` | `utility.c` L734 -> `DoCopy` (commands/copy.c L62) -> `CopyFrom` -> `heap_multi_insert` (heapam.c L2378) | 행 쓰기와 WAL 기록(`heap_insert` 가 아니라 `heap_multi_insert`) -> nbtree |

```text
 COPY 는 한 줄씩 넣지 않는다

 CopyFrom 은 행을 버퍼에 모았다가 CopyMultiInsertBufferFlush 로 한 번에 넣는다
 그래서 [행 쓰기와 WAL 기록] 의 heap_insert 가 아니라 heap_multi_insert 를 탄다
 흐름 문서의 02_heap_insert 와 나란히 볼 곁가지다
```

## 트랜잭션

| SQL | 진입 자리 | 뒤이어 지나는 흐름 |
|---|---|---|
| `BEGIN` | `utility.c` L607 -> `BeginTransactionBlock` (xact.c L3924) | 커밋 (블록 상태만 바뀐다) |
| `COMMIT` | `utility.c` L633 -> `EndTransactionBlock` (xact.c L4044) | 커밋 -> WAL(`XLogFlush`) -> 스트리밍 복제(동기일 때) -> heavyweight lock(`LockReleaseAll`) |
| `ROLLBACK` | `utility.c` L661 -> `UserAbortTransactionBlock` (xact.c L4204) | 커밋의 abort 갈래 |
| `LOCK TABLE` | `utility.c` L930 -> `LockTableCommand` (commands/lockcmds.c L41) | heavyweight lock |

```text
 COMMIT 문은 커밋을 하지 않는다

 EndTransactionBlock 은 블록 상태를 "끝낼 것" 으로 바꿀 뿐이다
 실제 커밋은 문장이 끝난 뒤 finish_xact_command (postgres.c L2826)
   -> CommitTransactionCommandInternal -> CommitTransaction (xact.c L2228) 에서 일어난다
 BEGIN 없이 보낸 문장 하나도 같은 길로 커밋된다
```

## 유지보수와 DDL

| SQL | 진입 자리 | 뒤이어 지나는 흐름 |
|---|---|---|
| `VACUUM` / `ANALYZE` | `utility.c` L861 -> `ExecVacuum` (commands/vacuum.c L162) | vacuum -> 버퍼 관리 -> WAL -> MVCC |
| `CHECKPOINT` | `utility.c` L945 -> `RequestCheckpoint` (checkpointer.c L1003) | 체크포인트 |
| `CREATE INDEX` | `utility.c` L1456 -> `DefineIndex` (commands/indexcmds.c L542) -> `btbuild` (nbtsort.c L295) | heavyweight lock. 정렬 빌드라 nbtree 삽입 흐름은 타지 않는다 |
| `ALTER TABLE` | `utility.c` L1271 -> `AlterTable` (commands/tablecmds.c L4543) | heavyweight lock(AccessExclusive) -> 필요하면 행 쓰기 |
| `EXPLAIN` | `utility.c` L865 -> `ExplainQuery` (commands/explain.c L176) | 쿼리 실행 파이프라인(plan) -> executor(ANALYZE 일 때) |

## 복제 프로토콜

| 명령 | 진입 자리 | 뒤이어 지나는 흐름 |
|---|---|---|
| `START_REPLICATION` | `postgres.c` L4766 -> `exec_replication_command` (replication/walsender.c L2012) | 스트리밍 복제 |

## GUC

정의는 모두 `utils/misc/guc_tables.c` 에 있다.

| GUC | 정의 | 읽는 자리 | 흐름 |
|---|---|---|---|
| `shared_buffers` | L2379 | `NBuffers` - `buf_init.c` `BufferManagerShmemInit` | 버퍼 관리 |
| `wal_level` | L5250 | `src/include/access/xlog.h` L109 `XLogIsNeeded` | 행 쓰기와 WAL 기록, 스트리밍 복제 |
| `synchronous_commit` | L5189 | `RecordTransactionCommit` xact.c L1499 | 커밋, 스트리밍 복제 |
| `fsync` | L1136 | `enableFsync` - xlog.c L8757 `issue_xlog_fsync` | 행 쓰기와 WAL 기록, 체크포인트 |
| `full_page_writes` | L1196 | `GetFullPageWriteInfo` xloginsert.c L518 -> `XLogRecordAssemble` L592 | 행 쓰기와 WAL 기록, WAL redo |
| `wal_buffers` | L3020 | `XLOGbuffers` xlog.c L118 | 행 쓰기와 WAL 기록 |
| `commit_delay` | L3121 | xlog.c L2881 (`XLogFlush` 안) | 커밋 |
| `checkpoint_timeout` | L2983 | `CheckPointTimeout` checkpointer.c L390 | 체크포인트 |
| `max_wal_size` | L2971 | `max_wal_size_mb` xlog.c L115 | 체크포인트 |
| `autovacuum` | L1542 | `AutoVacuumingActive` autovacuum.c L3283 | vacuum |
| `autovacuum_naptime` | L3530 | autovacuum.c L668 | vacuum |
| `deadlock_timeout` | L2266 | `ProcSleep` proc.c L1393 | heavyweight lock |
| `synchronous_standby_names` | L4801 | `SyncRepStandbyNames` syncrep.c L90 | 커밋, 스트리밍 복제 |
| `io_method` | L5444 | `WaitReadBuffers` bufmgr.c L1669 | 버퍼 관리 |

`checkpoint_completion_target`(L4124)·`hot_standby`(L1896)·`max_connections`(L2332)·`work_mem`(L2576)·`wal_sync_method`(L5300)는 정의만 확인했고 읽는 자리는 아직 확인하지 않았다.

## 흐름이 덮지 않는 것

```text
 트리거 · 사용자 함수 · PL/pgSQL · CALL · DO
 논리 복제와 logical decoding (CREATE PUBLICATION / SUBSCRIPTION)
 PREPARE TRANSACTION (2PC)        LISTEN / NOTIFY
 SERIALIZABLE (SSI, storage/lmgr/predicate.c)
 parallel query · JIT · FDW · 파티션 라우팅
 GIN / GiST / BRIN / Hash 인덱스 · TOAST
 VACUUM FULL · CLUSTER · REINDEX · CREATE TABLE AS · REFRESH MATERIALIZED VIEW
 CREATE / DROP 일반 DDL (카탈로그) · CREATE DATABASE · ALTER SYSTEM · SET
 PREPARE / EXECUTE 와 plan cache · 커서 DECLARE / FETCH
 relcache / syscache · pgstat · base backup · archiver · bgwriter
```
