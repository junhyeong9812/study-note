# CheckPointGuts

상위: [체크포인트](../README.md)

**공유 메모리에 있는 모든 더러운 상태를 디스크로 내리고 fsync 까지 끝내는 함수다.** 체크포인트와 restartpoint 가 함께 쓰는 공통 부분이라(머리 주석 L7548-L7549) REDO 지점을 정하는 일도, 레코드를 쓰는 일도 하지 않는다. 순서는 셋으로 나뉜다. 작은 상태 파일들, SLRU 와 공유 버퍼 쓰기(`write` 까지), 그다음 모아 둔 fsync 를 한꺼번에 실행한다.

## 위치

`src/backend/access/transam` / `xlog.c` L7551-L7579 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L7551-L7579))

## 실제 코드

```c
// transam/xlog.c L7551-L7579
static void
CheckPointGuts(XLogRecPtr checkPointRedo, int flags)
{
	CheckPointRelationMap();
	CheckPointReplicationSlots(flags & CHECKPOINT_IS_SHUTDOWN);
	CheckPointSnapBuild();
	CheckPointLogicalRewriteHeap();
	CheckPointReplicationOrigin();

	/* Write out all dirty data in SLRUs and the main buffer pool */
	TRACE_POSTGRESQL_BUFFER_CHECKPOINT_START(flags);
	CheckpointStats.ckpt_write_t = GetCurrentTimestamp();
	CheckPointCLOG();
	CheckPointCommitTs();
	CheckPointSUBTRANS();
	CheckPointMultiXact();
	CheckPointPredicate();
	CheckPointBuffers(flags);

	/* Perform all queued up fsyncs */
	TRACE_POSTGRESQL_BUFFER_CHECKPOINT_SYNC_START();
	CheckpointStats.ckpt_sync_t = GetCurrentTimestamp();
	ProcessSyncRequests();
	CheckpointStats.ckpt_sync_end_t = GetCurrentTimestamp();
	TRACE_POSTGRESQL_BUFFER_CHECKPOINT_DONE();

	/* We deliberately delay 2PC checkpointing as long as possible */
	CheckPointTwoPhase(checkPointRedo);
}
```

공유 버퍼 쪽 진입점은 한 줄짜리 포장이다. 임시 테이블은 체크포인트에 참여하지 않는다(주석 L4229-L4230).

`src/backend/storage/buffer` / `bufmgr.c` L4232-L4236 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L4232-L4236))

```c
// buffer/bufmgr.c L4232-L4236
void
CheckPointBuffers(int flags)
{
	BufferSync(flags);
}
```

## 동작 흐름

```text
 CheckPointGuts(checkPointRedo, flags)

 1. 작은 상태 파일                                    대부분 각자 파일을 쓰고 fsync
    L7554  CheckPointRelationMap        pg_filenode.map   lock 을 잡았다 놓기만 한다. 진행 중인 map 갱신(쓰기+fsync)이 끝나길 기다리는 것
    L7555  CheckPointReplicationSlots   pg_replslot/*/state
    L7556  CheckPointSnapBuild          pg_logical/snapshots   쓰지 않고 필요 없어진 스냅숏 파일을 지운다
    L7557  CheckPointLogicalRewriteHeap pg_logical/mappings    옛 mapping 삭제 + 남은 것 fsync
    L7558  CheckPointReplicationOrigin  pg_logical/replorigin_checkpoint

 2. write 단계                                        ckpt_write_t (L7562)
    L7563  CheckPointCLOG               pg_xact         SLRU 버퍼
    L7564  CheckPointCommitTs           pg_commit_ts
    L7565  CheckPointSUBTRANS           pg_subtrans
    L7566  CheckPointMultiXact          pg_multixact
    L7567  CheckPointPredicate          pg_serial
    L7568  CheckPointBuffers -> [05] BufferSync      shared_buffers. 시간 대부분이 여기
           여기까지의 쓰기는 OS page cache 에 들어가고, fsync 요청만 쌓인다

 3. sync 단계                                         ckpt_sync_t (L7572)
    L7573  [08] ProcessSyncRequests     쌓인 요청 파일마다 fsync

 4. L7578  CheckPointTwoPhase(redo)     최대한 늦게 (주석 L7577)
```

write 단계는 fsync 를 하지 않고 "이 파일을 fsync 해야 한다"는 요청만 남긴다. 요청은 `FileTag` 를 키로 한 해시(`pendingOps`)에 모이므로 같은 세그먼트 파일에 버퍼 여러 개를 써도 fsync 는 한 번이다. 중복은 checkpointer 가 해시에서 걸러낸다는 것이 `ForwardSyncRequest` 주석(checkpointer.c L1142-L1145)의 설명이다.

```text
 write 단계에서 쌓이는 fsync 요청 (예: 같은 테이블 세그먼트 파일 16384 에 버퍼 3개)

   SyncOneBuffer(buf 7)   -> FlushBuffer -> smgrwrite -> mdwritev -> register_dirty_segment (md.c L1149)
   SyncOneBuffer(buf 12)  -> ...                                    -> 같은 FileTag
   SyncOneBuffer(buf 40)  -> ...                                    -> 같은 FileTag
                                                    |
                                                    v
                         pendingOps 해시 (FileTag 가 키) 에 항목 1개
                                                    |
                                                    v
   ProcessSyncRequests   -> 그 파일에 fsync 1번

 checkpointer 가 아닌 backend 가 쓴 페이지도 ForwardSyncRequest 로 큐에 넣고,
 checkpointer 가 AbsorbSyncRequests 로 같은 해시에 합친다
```

## 결과가 쓰이는 곳

```text
 데이터 파일과 SLRU 가 fsync 된 상태
      --> [03] CreateCheckPoint 가 그제서야 체크포인트 레코드와 pg_control 을 쓴다 (xlog.c L7254, L7308)
          "REDO 지점 앞의 변경은 모두 디스크에 있다" 가 이 순간 참이 된다
 CheckpointStats.ckpt_write_t, ckpt_sync_t, ckpt_sync_end_t
      --> LogCheckpointEnd 의 "write=... s, sync=... s" 로그 (xlog.c L6773-L6774)
```

## 다루지 않는 것

각 `CheckPoint*` 함수의 내부(SLRU 의 `SimpleLruWriteAll`, 복제 슬롯 상태 파일 형식, 2PC 상태 파일), `mdwritev` 가 fsync 요청을 등록하는 `register_dirty_segment` 경로는 요약만 했다.
