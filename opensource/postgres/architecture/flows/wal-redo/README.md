# WAL redo (복구)

상위: [PostgreSQL 아키텍처 지도](../../README.md)

서버가 기동할 때 startup 프로세스가 **마지막 체크포인트의 REDO 지점부터 WAL 레코드를 하나씩 읽어 해당 resource manager 의 `rm_redo` 로 다시 적용하는** 흐름이다. 어디서 시작할지는 `pg_control` 이 정하고, 베이스 백업에서 띄웠으면 `backup_label` 이 그보다 우선한다. 레코드 하나를 적용할 때 각 페이지는 두 규칙으로 판단한다. 레코드에 full-page image(FPI)가 붙어 있으면 디스크 페이지를 믿지 않고 이미지로 덮어쓴다. 아니면 페이지 LSN 과 레코드 끝 LSN 을 비교해 이미 반영된 변경은 건너뛴다. 크래시 복구는 WAL 끝에 닿으면 끝나고, 그 뒤 end-of-recovery 체크포인트를 요청한 다음 쓰기를 연다. standby 는 WAL 끝에서 멈추지 않고 아카이브, `pg_wal`, walreceiver 스트림을 돌아가며 다음 WAL 을 기다린다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 postmaster -> StartChildProcess(B_STARTUP)            postmaster/postmaster.c L1394
 ------------------------------------------------------------------
 startup 프로세스
 [01] StartupProcessMain                               postmaster/startup.c L216
      +-- [02] StartupXLOG                             access/transam/xlog.c L5467
            +-- pg_control.state 가 정상 종료가 아니면 SyncDataDirectory   L5587-L5593
            +-- [03] InitWalRecovery                   L5605
            |     +-- read_backup_label 이 있으면 그 체크포인트   xlogrecovery.c L608
            |     +-- 없으면 pg_control.checkPoint                 L790
            |     +-- ReadCheckpointRecord, redo 위치 확인         L794-L825
            |     +-- redo < 체크포인트 위치 이거나 비정상 종료면 InRecovery = true   L933-L946
            +-- nextXid, nextOid ... 를 체크포인트 값으로      xlog.c L5610-L5619
            +-- InRecovery 면
            |     +-- pg_control 갱신 (DB_IN_CRASH_RECOVERY 등)  L5749
            |     +-- [04] PerformWalRecovery              L5886
            |           +-- RedoStartLSN 으로 이동, 첫 레코드 = XLOG_CHECKPOINT_REDO   xlogrecovery.c L1734-L1746
            |           +-- do {                           L1778
            |           |     recoveryStopsBefore          L1824  PITR 목표
            |           |     [06] ApplyWalRecord          L1850
            |           |       +-- GetRmgr(xl_rmid).rm_redo(record)   L2020
            |           |             heap 레코드면 [07] heap_redo
            |           |               +-- [08] heap_xlog_insert      heapam_xlog.c L477
            |           |                     +-- [09] XLogReadBufferForRedoExtended   xlogutils.c L362
            |           |                           FPI 면 복원, 아니면 page LSN 비교
            |           |     [05] ReadRecord              L1860
            |           |       +-- XLogPageRead -> [10] WaitForWALToBecomeAvailable   L3383
            |           |             아카이브 / pg_wal / walreceiver 스트림
            |           +-- } while (record != NULL)       L1861
            +-- FinishWalRecovery                      xlog.c L5895
            +-- EndOfLog 에서 WAL 삽입 위치를 잡는다    L6058-L6104
            +-- InRecovery = false                     L6114
            +-- PerformRecoveryXLogAction              L6171
            |     promote 면 END_OF_RECOVERY 레코드, 아니면
            |     RequestCheckpoint(END_OF_RECOVERY | IMMEDIATE | WAIT)   L6359
            +-- pg_control.state = DB_IN_PRODUCTION    L6207
            +-- SharedRecoveryState = RECOVERY_STATE_DONE   L6210  backend 가 WAL 을 쓸 수 있다
      +-- proc_exit(0)                                 startup.c L264
```

복구 한 번을 시간축으로 그리면 이렇다. LSN 은 [체크포인트](../checkpoint/README.md) 흐름의 예와 이어지는 예시다.

```text
 시간 ->

 t0  크래시. pg_control: state = DB_IN_PRODUCTION
                         checkPoint = 0/5A3F1E28, checkPointCopy.redo = 0/3D000100
     WAL 은 0/5B012340 까지 디스크에 있다 (마지막 완전한 레코드의 끝)

 t1  postmaster 가 checkpointer, bgwriter 를 띄우고 startup 을 띄운다   (postmaster.c L1387-L1394)
 t2  StartupXLOG: 정상 종료가 아니므로 데이터 디렉터리 전체 fsync    (L5587-L5593)
 t3  InitWalRecovery: 0/5A3F1E28 의 체크포인트 레코드를 읽음 -> redo = 0/3D000100
     redo < 체크포인트 위치 -> InRecovery = true, state = DB_IN_CRASH_RECOVERY
 t4  PerformWalRecovery: 0/3D000100 의 REDO 레코드부터
       "redo starts at 0/3D000100"
       레코드마다 rm_redo -> 페이지를 고쳐 MarkBufferDirty (아직 디스크에는 안 씀)
 t5  0/5B012340 다음을 읽으려다 실패 (빈 공간 또는 CRC 불일치) -> ReadRecord = NULL
       "redo done at ..."
 t6  StartupXLOG: 삽입 위치 = 0/5B012340, InRecovery = false
     RequestCheckpoint(END_OF_RECOVERY | IMMEDIATE | WAIT)
       checkpointer 가 복구로 더러워진 버퍼를 모두 내리고 SHUTDOWN 형 체크포인트 레코드를 쓴다
 t7  state = DB_IN_PRODUCTION, RECOVERY_STATE_DONE -> 연결을 받는다
```

## 어디에서 쓰이는가

```text
 startup 프로세스를 띄우는 곳
   postmaster 기동                                   postmaster/postmaster.c L1394
   backend 크래시 뒤 재시작                          postmaster/postmaster.c L3209

 같은 경로를 다른 목적으로 타는 경우
   크래시 복구        backup_label, 신호 파일 없음. WAL 끝까지
   아카이브 복구(PITR) recovery.signal. restore_command 로 WAL 을 받고 recovery_target 에서 멈춤
   standby            standby.signal. 끝없이 재생, primary_conninfo 로 스트리밍
                      checkpointer 는 같은 시간에 restartpoint 를 만든다 (CreateRestartPoint)
```

체크포인트가 정한 REDO 지점이 이 흐름의 출발점이고, 그 REDO 지점 뒤 첫 수정에 붙은 FPI 를 만드는 쪽은 [행 쓰기와 WAL 기록](../heap-insert-wal/README.md)의 [XLogRecordAssemble](../heap-insert-wal/07_XLogRecordAssemble/README.md)이다. standby 에 WAL 을 보내는 쪽은 [스트리밍 복제](../streaming-replication/README.md)다.

## db-engine 에서는

db-engine 의 `Recovery.recover` 와 `IdempotentRecovery.recover` 는 로그 전체를 처음부터 읽어 커밋된 트랜잭션의 삽입만 다시 넣는 redo-only 복구다. "이미 반영되었는가"를 묻는 단위가 다르다.

```text
 같은 문제 "무엇을 다시 적용할까", 두 구현 (위 PostgreSQL / 아래 db-engine)

 시작점
   PostgreSQL  pg_control 또는 backup_label 의 체크포인트 -> redo LSN
   db-engine   로그 파일의 처음 (replayWithLsn 이 seek(0))

 무엇을 적용하나
   PostgreSQL  REDO 뒤의 모든 레코드. 커밋 여부와 무관하게 페이지 변경을 그대로 재생
               (커밋 레코드가 없던 트랜잭션의 행도 들어가지만 pg_xact 에 committed 가 남지 않는다)
   db-engine   커밋된 txId 의 InsertRow 만. 로그를 끝까지 읽은 뒤 committed 집합으로 거른다

 이미 반영되었는가
   PostgreSQL  페이지마다: 레코드 끝 LSN <= 페이지 LSN 이면 건너뜀 (XLogReadBufferForRedoExtended)
   db-engine   전체에 하나: lsn <= recovery.meta 의 lastAppliedLsn 이면 건너뜀

 찢어진 페이지
   PostgreSQL  REDO 뒤 첫 수정에 FPI 를 붙이고 복구 때 무조건 덮어쓴다
   db-engine   해당 없음 (heap 을 commit 때 쓰고 복구는 다시 insert)

 WAL 끝 판단
   PostgreSQL  다음 레코드의 헤더, xl_prev, CRC 검증 실패 (access/transam/xlogreader.c L1138-L1226)
   db-engine   readInt / readFully 의 EOFException (08-03 CI-2 가 잘린 꼬리를 검증)
```

PostgreSQL 은 "페이지 하나가 어느 LSN 까지 반영되었나"를 페이지 머리의 `pd_lsn` 에 갖고 있어서, 일부 페이지만 디스크에 내려간 상태에서도 레코드 단위로 정확히 이어 붙인다. db-engine 은 [08-02-lsn-checkpoint](../../../../../project/db-engine/08-02-lsn-checkpoint/) 가 적었듯 그 단계를 건너뛰고 `lastAppliedLsn` 하나로 멱등성을 지킨다. 그래서 복구 도중 일부 행만 heap 에 들어간 채 죽으면 그 행들을 다시 넣는다. 챕터: [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [08-03-crash-simulation](../../../../../project/db-engine/08-03-crash-simulation/).

## 단계

1. [StartupProcessMain](01_StartupProcessMain/README.md)이 시그널을 설정하고 `StartupXLOG` 를 부른다.
2. [StartupXLOG](02_StartupXLOG/README.md)가 기동 순서 전체를 맡는다. 복구 준비, 재생, 끝내기, 쓰기 열기.
3. [InitWalRecovery](03_InitWalRecovery/README.md)가 `backup_label` 과 `pg_control` 로 시작 체크포인트를 정하고 복구가 필요한지 판단한다.
4. [PerformWalRecovery](04_PerformWalRecovery/README.md)가 REDO 지점부터 읽고 적용하는 루프를 돈다.
5. [ReadRecord](05_ReadRecord/README.md)가 다음 레코드를 읽고, 실패하면 아카이브 복구로 넘어가거나 standby 면 다시 시도한다.
6. [ApplyWalRecord](06_ApplyWalRecord/README.md)가 timeline 전환을 확인하고 `rm_redo` 로 디스패치한다.
7. [heap_redo](07_heap_redo/README.md)가 heap 레코드의 opcode 로 갈라진다.
8. [heap_xlog_insert](08_heap_xlog_insert/README.md)가 레코드에서 튜플을 다시 만들어 페이지에 넣는다.
9. [XLogReadBufferForRedoExtended](09_XLogReadBufferForRedoExtended/README.md)가 FPI 를 복원하거나 페이지 LSN 을 비교한다.
10. [WaitForWALToBecomeAvailable](10_WaitForWALToBecomeAvailable/README.md)이 다음 WAL 이 든 파일을 아카이브, `pg_wal`, 스트림에서 찾고 없으면 기다린다.

## 결과가 쓰이는 곳

```text
 복구로 더러워진 공유 버퍼
      --> end-of-recovery 체크포인트의 BufferSync 가 unlogged 까지 모두 내려 쓴다 (bufmgr.c L3387-L3389)
 EndOfLog
      --> WAL 삽입 위치 Insert->CurrBytePos (xlog.c L6060). 새 WAL 은 여기 이어서 쓴다
 SharedRecoveryState = RECOVERY_STATE_DONE
      --> RecoveryInProgress() 가 false. backend 의 XLogInsertAllowed 가 참이 된다 (xlog.c L6442-L6450)
 lastReplayedEndRecPtr (standby)
      --> GetXLogReplayRecPtr (xlogrecovery.c L4598) -> pg_last_wal_replay_lsn() (xlogfuncs.c)
```

## 다루지 않는 것

PITR 목표 판정(`recoveryStopsBefore`, `recoveryStopsAfter`), `recovery_min_apply_delay`, hot standby 의 스냅샷과 충돌 처리(`KnownAssignedXids`, `ResolveRecoveryConflictWithSnapshot`), WAL prefetch(`XLogPrefetcher`), `xlogreader.c` 의 레코드 디코딩과 CRC 검사, timeline history 파일, `FinishWalRecovery`, promote 과정, heap 외 resource manager 의 redo 는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 StartupProcessMain](01_StartupProcessMain/README.md)
- [02 StartupXLOG](02_StartupXLOG/README.md)
- [03 InitWalRecovery](03_InitWalRecovery/README.md)
- [04 PerformWalRecovery](04_PerformWalRecovery/README.md)
- [05 ReadRecord](05_ReadRecord/README.md)
- [06 ApplyWalRecord](06_ApplyWalRecord/README.md)
- [07 heap_redo](07_heap_redo/README.md)
- [08 heap_xlog_insert](08_heap_xlog_insert/README.md)
- [09 XLogReadBufferForRedoExtended](09_XLogReadBufferForRedoExtended/README.md)
- [10 WaitForWALToBecomeAvailable](10_WaitForWALToBecomeAvailable/README.md)
