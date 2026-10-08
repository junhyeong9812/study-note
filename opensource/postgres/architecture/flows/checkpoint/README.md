# 체크포인트

상위: [PostgreSQL 아키텍처 지도](../../README.md)

checkpointer 프로세스가 **"이 LSN 이전의 WAL 은 다시 읽지 않아도 된다"는 지점(REDO 지점)을 정하고, 그 지점 이전에 더러워진 페이지를 전부 디스크에 내려 fsync 한 뒤, 그 사실을 체크포인트 레코드와 `pg_control` 에 남기는** 흐름이다. 시작 계기는 둘이다. `checkpoint_timeout`(기본 300초)이 지나거나, backend 가 WAL 세그먼트를 채우다 `max_wal_size` 로 계산한 거리(`CheckPointSegments`)를 넘었다고 알려 올 때다. 온라인 체크포인트는 다른 backend 가 계속 WAL 을 쓰는 중에 돌기 때문에 REDO 지점과 완료 지점이 다르다. 시작할 때 `XLOG_CHECKPOINT_REDO` 레코드를 하나 넣어 그 시작 LSN 을 REDO 지점으로 삼고, 쓰기를 다 마친 뒤 `XLOG_CHECKPOINT_ONLINE` 레코드에 그 REDO 지점을 담아 넣는다. 더러운 버퍼 쓰기는 `checkpoint_completion_target`(기본 0.9)에 맞춰 다음 체크포인트 예정 시점의 90% 까지 퍼뜨린다. 흐름은 REDO 지점보다 앞선 WAL 세그먼트를 지우거나 재활용하는 데서 끝난다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 계기 (다른 프로세스)
 ------------------------------------------------------------------
 backend 의 XLogWrite 가 세그먼트 하나를 다 채움          xlog.c L2477
      +-- XLogCheckpointNeeded(openLogSegNo)             L2499  REDO 세그먼트 + CheckPointSegments - 1 이상?
      +-- [02] RequestCheckpoint(CHECKPOINT_CAUSE_XLOG)  L2503
            +-- ckpt_flags |= flags                      checkpointer.c L1039
            +-- SetLatch(checkpointer)                   L1070
 CHECKPOINT 명령, CREATE DATABASE, pg_backup_start 도 [02] 를 부른다
 ------------------------------------------------------------------
 checkpointer 프로세스
 [01] CheckpointerMain                                   checkpointer.c L182
      +-- for (;;)                                       L349
            +-- ckpt_flags != 0 이면 요청 있음           L376
            +-- now - last_checkpoint_time >= checkpoint_timeout  L390  CAUSE_TIME
            +-- [03] CreateCheckPoint(flags)             L480   (standby 면 CreateRestartPoint L482)
            |     +-- 직전 체크포인트 이후 중요한 WAL 이 없으면 건너뜀   xlog.c L7012-L7022
            |     +-- XLogInsert(XLOG_CHECKPOINT_REDO)  L7101  이 레코드의 시작 = REDO 지점
            |     +-- nextXid, nextOid, multixact 수집   L7137-L7158
            |     +-- DELAY_CHKPT_START 인 backend 대기  L7199-L7216  커밋 중간에 끼지 않게
            |     +-- [04] CheckPointGuts(redo, flags)   L7219
            |     |     +-- CLOG, SUBTRANS, MultiXact 등 SLRU 쓰기   L7563-L7567
            |     |     +-- CheckPointBuffers -> [05] BufferSync      L7568, bufmgr.c L4235
            |     |     |     +-- 더러운 버퍼에 BM_CHECKPOINT_NEEDED  bufmgr.c L3408-L3437
            |     |     |     +-- (tablespace, rel, fork, block) 정렬  L3453
            |     |     |     +-- tablespace 별 진행률 min-heap       L3527-L3540
            |     |     |     +-- 버퍼마다 [06] SyncOneBuffer         L3577
            |     |     |     |     +-- FlushBuffer                   L3989  WAL 먼저, 그다음 write
            |     |     |     +-- 버퍼마다 [07] CheckpointWriteDelay  L3609  일정보다 앞서면 100ms 잔다
            |     |     +-- [08] ProcessSyncRequests                  xlog.c L7573  쌓인 fsync 를 실행
            |     +-- XLogInsert(XLOG_CHECKPOINT_ONLINE) L7254  CheckPoint 구조체 전체를 싣는다
            |     +-- XLogFlush(recptr)                  L7258
            |     +-- pg_control 갱신 + fsync            L7292-L7309
            |     +-- KeepLogSeg                         L7360  복제 슬롯, wal_keep_size 몫을 남긴다
            |     +-- [09] RemoveOldXlogFiles            L7373  REDO 세그먼트 앞을 지우거나 재활용
            +-- ckpt_done = ckpt_started, done_cv 깨움   checkpointer.c L496-L499
            +-- WaitLatch(남은 checkpoint_timeout)       L580

 [01] [02] [07] 은 postmaster/checkpointer.c, [05] [06] 은 storage/buffer/bufmgr.c,
 [08] 은 storage/sync/sync.c, 나머지는 access/transam/xlog.c 의 줄이다
```

체크포인트 하나가 LSN 축 위에 남기는 표시는 셋이다. 숫자는 기본 설정(`max_wal_size` 1GB, 세그먼트 16MB, `checkpoint_completion_target` 0.9)으로 계산한 예시다.

```text
 CheckPointSegments = floor((1024MB / 16MB) / (1 + 0.9)) = floor(64 / 1.9) = 33   (xlog.c L2189-L2193)

 WAL (LSN 증가 ->, 세그먼트 번호는 16진수)

   seg 1C            seg 3C   seg 3D                                 seg 5A
   |-----------------|--------|--------------------------------------|----
   A                          B                                      C

   A  0/1C000060   앞 체크포인트의 REDO 지점
   B  0/3D000100   이번 REDO 레코드의 시작 = checkPoint.redo
   C  0/5A3F1E28   이번 ONLINE 레코드의 시작 = ControlFile->checkPoint

 1) backend 가 seg 3C 를 다 채움: 3C >= 1C + (33 - 1) 이므로 RequestCheckpoint   (L2286)
 2) checkpointer 가 REDO 레코드를 넣는다. 이후 WAL 은 "체크포인트 이후" 로 친다
 3) BufferSync 가 쓰는 동안 다른 backend 는 계속 WAL 을 쓴다
    on schedule 이면 33 * 0.9 = 29.7 세그먼트쯤 지나 쓰기가 끝난다   (3D + 29 = 5A)
 4) ONLINE 레코드 + pg_control 갱신. 다음 복구는 0/3D000100 에서 시작한다
 5) seg 1C .. 3C 는 더 필요 없다 -> 지우거나 미래 세그먼트 이름으로 재활용
    남는 것은 3D .. 5A 의 30개 + 재활용분. 합이 64 안쪽에 머문다 = max_wal_size 의 뜻
```

## 어디에서 쓰이는가

```text
 checkpointer 를 띄우는 곳
   postmaster 가 기동 직후 startup 보다 먼저 띄운다       postmaster/postmaster.c L1387
   복구 중(standby)에도 살아서 CreateRestartPoint 를 돈다  checkpointer.c L407, L482

 [02] RequestCheckpoint 를 부르는 곳
   XLogWrite (WAL 이 CheckPointSegments 만큼 쌓임)         access/transam/xlog.c L2503
   XLogPageRead (standby 가 그만큼 재생함 -> restartpoint)  access/transam/xlogrecovery.c L3360
   CHECKPOINT 명령 (IMMEDIATE | WAIT | FORCE)              tcop/utility.c L955
   pg_backup_start (FORCE | WAIT)                          access/transam/xlog.c L8954
   CREATE DATABASE, DROP DATABASE, DROP TABLESPACE         commands/dbcommands.c L573 외, commands/tablespace.c L503
   복구 끝 (END_OF_RECOVERY | IMMEDIATE | WAIT)            access/transam/xlog.c L6359
   promote 뒤 (FORCE)                                      access/transam/xlog.c L6241
```

[버퍼 관리](../buffer-manager/README.md)의 희생자 쓰기와 이 흐름의 `BufferSync` 는 같은 [FlushBuffer](../buffer-manager/09_FlushBuffer/README.md)를 거친다. 체크포인트가 남긴 REDO 지점에서 다시 시작하는 쪽은 [WAL redo (복구)](../wal-redo/README.md)다.

## db-engine 에서는

db-engine 의 `CheckpointManager.checkpoint` 는 체크포인트 레코드 하나를 붙이고 sync 하는 데서 끝난다. PostgreSQL 체크포인트의 본체인 "더러운 페이지 내리기"와 "옛 로그 지우기"가 없다.

```text
 같은 문제 "어디서부터 다시 읽을까", 두 구현 (위 PostgreSQL / 아래 db-engine)

 기록하는 것
   PostgreSQL  CheckPoint{redo, nextXid, nextOid, ...} 를 WAL 과 pg_control 둘 다에
   db-engine   LogRecord.Checkpoint(checkpointLsn = currentLsn(), activeTxs) 를 WAL 에만

 REDO 지점
   PostgreSQL  XLOG_CHECKPOINT_REDO 레코드의 시작 LSN (바이트 위치)
   db-engine   그 순간 마지막 레코드의 순번 (LSN = 레코드 개수)

 페이지 내리기
   PostgreSQL  BufferSync 가 BM_CHECKPOINT_NEEDED 버퍼를 정렬해 퍼뜨려 쓰고 fsync
   db-engine   없다. heap 은 commit 때 바로 apply 된다 (deferred-apply)

 복구 시작점
   PostgreSQL  pg_control -> 체크포인트 레코드 -> redo 에서 재생 시작
   db-engine   Recovery, IdempotentRecovery 모두 로그 처음부터 읽고 Checkpoint 는 무시한다
               멱등성은 recovery.meta 의 lastAppliedLsn 으로 따로 지킨다

 옛 로그
   PostgreSQL  REDO 세그먼트 앞을 지우거나 재활용 (RemoveOldXlogFiles)
   db-engine   로그 파일 하나가 계속 자란다
```

db-engine 의 [08-02-lsn-checkpoint](../../../../../project/db-engine/08-02-lsn-checkpoint/) 는 "로그가 무한히 자란다"를 문제로 적고 체크포인트를 도입했지만, 체크포인트 레코드는 `PhysicalBackup` 쪽에서만 쓰이고 복구 범위를 줄이지는 않는다. PostgreSQL 에서 범위를 줄일 수 있는 근거는 "REDO 지점 앞의 변경은 이미 데이터 파일에 fsync 되었다"는 보장이고, 그 보장을 만드는 것이 `CheckPointGuts` 다. db-engine 에 페이지 LSN 이 없어서 이 보장을 세울 자리가 아직 없다.

## 단계

1. [CheckpointerMain](01_CheckpointerMain/README.md)이 요청 플래그와 `checkpoint_timeout` 을 보고 체크포인트를 시작하고, 끝나면 대기자를 깨운다.
2. [RequestCheckpoint](02_RequestCheckpoint/README.md)가 공유 메모리에 플래그를 OR 하고 checkpointer 를 깨운다. `max_wal_size` 트리거 계산도 여기서 본다.
3. [CreateCheckPoint](03_CreateCheckPoint/README.md)가 REDO 지점을 정하고, 쓰기를 맡기고, 체크포인트 레코드와 `pg_control` 을 쓰고, 옛 WAL 을 치운다.
4. [CheckPointGuts](04_CheckPointGuts/README.md)가 SLRU, 공유 버퍼, fsync 를 순서대로 부른다.
5. [BufferSync](05_BufferSync/README.md)가 더러운 버퍼를 표시하고 정렬해 tablespace 사이에 고르게 쓴다.
6. [SyncOneBuffer](06_SyncOneBuffer/README.md)가 버퍼 하나를 pin, share lock 하고 `FlushBuffer` 로 쓴다.
7. [CheckpointWriteDelay](07_CheckpointWriteDelay/README.md)가 진행률을 시간, WAL 양과 비교해 앞서 있으면 잔다.
8. [ProcessSyncRequests](08_ProcessSyncRequests/README.md)가 이번 체크포인트 전에 쌓인 fsync 요청을 실행한다.
9. [RemoveOldXlogFiles](09_RemoveOldXlogFiles/README.md)가 지울 경계를 넘은 세그먼트를 재활용하거나 지운다.

## 결과가 쓰이는 곳

```text
 pg_control.checkPoint, checkPointCopy.redo
      --> 다음 기동의 InitWalRecovery 가 읽어 재생 시작점으로 쓴다   (xlogrecovery.c L790-L792)
 RedoRecPtr (공유 Insert->RedoRecPtr)
      --> XLogRecordAssemble 이 page LSN <= RedoRecPtr 이면 full-page image 를 붙인다
          (xloginsert.c L618-L620)  체크포인트 직후 첫 수정이 페이지 전체를 싣는 이유
 ckpt_done, ckpt_failed
      --> CHECKPOINT_WAIT 로 기다리던 backend 가 깨어나 성공 여부를 안다   (checkpointer.c L1117, L1125)
 지워지거나 재활용된 세그먼트
      --> pg_wal 크기가 max_wal_size 근처에 머문다
```

## 다루지 않는 것

standby 의 `CreateRestartPoint`(xlog.c L7633), shutdown 체크포인트의 `ShutdownXLOG`, `LogCheckpointStart`/`LogCheckpointEnd` 의 로그 형식, `pg_stat_checkpointer` 통계, `CheckArchiveTimeout` 의 세그먼트 강제 전환, `LogStandbySnapshot`, 2PC 상태 파일(`CheckPointTwoPhase`), 복제 슬롯 무효화(`InvalidateObsoleteReplicationSlots`), writeback 제어(`checkpoint_flush_after`, `IssuePendingWritebacks`), backend 가 보낸 fsync 요청 큐(`ForwardSyncRequest`, `AbsorbSyncRequests`) 내부는 요약만 했다. `FlushBuffer` 자체는 [버퍼 관리](../buffer-manager/09_FlushBuffer/README.md)에 있다.

## 하위 메서드

- [01 CheckpointerMain](01_CheckpointerMain/README.md)
- [02 RequestCheckpoint](02_RequestCheckpoint/README.md)
- [03 CreateCheckPoint](03_CreateCheckPoint/README.md)
- [04 CheckPointGuts](04_CheckPointGuts/README.md)
- [05 BufferSync](05_BufferSync/README.md)
- [06 SyncOneBuffer](06_SyncOneBuffer/README.md)
- [07 CheckpointWriteDelay](07_CheckpointWriteDelay/README.md)
- [08 ProcessSyncRequests](08_ProcessSyncRequests/README.md)
- [09 RemoveOldXlogFiles](09_RemoveOldXlogFiles/README.md)
