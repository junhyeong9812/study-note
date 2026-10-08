# 커밋

상위: [PostgreSQL 아키텍처 지도](../../README.md)

트랜잭션 하나가 시작되고, XID 를 받고, **커밋되어 다른 세션에게 보이게 되기까지**의 흐름이다. 시작과 끝은 문장마다 도는 작은 상태 기계(`StartTransactionCommand` / `CommitTransactionCommand`)가 정하고, 실제 커밋은 [05] `CommitTransaction` 한 함수가 순서대로 처리한다. 핵심은 그 순서다. commit 레코드를 WAL 에 넣고 → `XLogFlush` 로 디스크에 내리고 → pg_xact 에 COMMITTED 비트를 쓰고 → (동기 복제면 standby 를 기다리고) → ProcArray 에서 자기 XID 를 지우고 → 마지막에 잠금을 푼다. 디스크에 남기는 것이 먼저이고, 남에게 끝났다고 알리는 것은 그 뒤이며, 기다리던 이를 놓아주는 것이 맨 끝이다. XID 를 받지 않은 읽기 전용 트랜잭션은 commit 레코드도 flush 도 없이 지나간다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다. `xact.c`·`transam.c`·`clog.c` 는 `access/transam/`, `procarray.c` 는 `storage/ipc/`, `syncrep.c` 는 `replication/` 에 있다.

## 전체 그림

```text
 exec_simple_query (tcop/postgres.c L1012)
 |
 +-- start_xact_command                             postgres.c L2787
 |     +-- [01] StartTransactionCommand             xact.c L3059   blockState 로 갈린다
 |           +-- TBLOCK_DEFAULT 이면
 |           +-- [02] StartTransaction              L3070          vxid 를 받고 TRANS_INPROGRESS
 |
 |   ... 문장 실행 ...
 |   첫 쓰기에서 GetCurrentTransactionId (L454)
 |     +-- [03] AssignTransactionId                 L635
 |           +-- GetNewTransactionId                varsup.c L77   XID 를 ProcGlobal->xids[] 에 싣는다
 |           +-- XactLockTableInsert                L729           자기 XID 에 ExclusiveLock
 |
 +-- finish_xact_command                            postgres.c L2826
       +-- CommitTransactionCommand                 xact.c L3157   (서브트랜잭션 반복 래퍼)
             +-- [04] CommitTransactionCommandInternal  L3175
                   +-- TBLOCK_STARTED / TBLOCK_END 이면
                   +-- [05] CommitTransaction       L3202 / L3232 -> L2228
                         +-- pre-commit             L2262-L2339   트리거, portal, PRE_COMMIT 콜백
                         +-- [06] RecordTransactionCommit          L2365 -> L1315
                         |     +-- [07] XactLogCommitRecord        L1442  commit 레코드를 WAL 버퍼에
                         |     +-- 동기: XLogFlush                  L1502  WAL 을 디스크로
                         |     |        [08] TransactionIdCommitTree L1508  pg_xact 비트
                         |     +-- 비동기: XLogSetAsyncXactLSN      L1523
                         |     |          TransactionIdAsyncCommitTree  L1531
                         |     +-- [09] SyncRepWaitForLSN          L1557  standby 확인까지 잠든다
                         +-- [10] ProcArrayEndTransaction          L2389  "실행 중" 집합에서 빠진다
                         +-- ResourceOwnerRelease(LOCKS)           L2437  잠금 해제
                         +-- AtCommit_Notify                       L2460
```

커밋 한 번이 시간 순서로 무엇을 바꾸는지가 이 흐름의 전부다. 아래 그림은 동기 커밋(`synchronous_commit = on`) 기준이다.

```text
 시간 -->   CommitTransaction (xact.c L2228)

 L2262-L2339  pre-commit         ERROR 가 나도 아직 abort 로 돌아갈 수 있다
 L2342        HOLD_INTERRUPTS
 L2351        s->state = TRANS_COMMIT
 L2365        RecordTransactionCommit
   L1436        START_CRIT_SECTION, delayChkptFlags |= DELAY_CHKPT_START
   L1442        commit 레코드 삽입            WAL 버퍼에 들어갔다
   L1502        XLogFlush(XactLastRecEnd)     디스크에 있다   <- 내구성이 확정되는 점
   L1508        pg_xact = COMMITTED           공유 메모리의 CLOG 페이지
   L1540-L1541  DELAY_CHKPT_START 해제, END_CRIT_SECTION
   L1557        SyncRepWaitForLSN             standby 가 확인할 때까지
 L2389        ProcArrayEndTransaction        ProcGlobal->xids[] 에서 내 XID 를 지운다
 L2411-L2442  ResourceOwnerRelease  BEFORE_LOCKS -> LOCKS -> AFTER_LOCKS
 L2460        AtCommit_Notify                LISTEN 하는 backend 에 신호
 L2505        RESUME_INTERRUPTS
```

같은 순간에 다른 세션이 새로 스냅샷을 잡으면 이 트랜잭션이 어떻게 보이는지를 줄마다 적으면 순서의 의미가 드러난다. 스냅샷은 ProcArray 에 있는 XID 를 진행 중(xip)으로 담고, 가시성 판정은 스냅샷에서 진행 중이 아닐 때만 pg_xact 를 본다([MVCC 가시성](../mvcc-visibility/README.md)의 [09]·[10]).

```text
 after   WAL      pg_xact       ProcGlobal->xids  locks  새 스냅샷에게 나는
 L1442   buffer   IN_PROGRESS   in                held   진행 중 - 안 보인다
 L1502   flushed  IN_PROGRESS   in                held   진행 중 - 크래시 나도 redo 가 커밋으로 복구
 L1508   flushed  COMMITTED     in                held   진행 중 - xip 에 남아 있다
 L1557   flushed  COMMITTED     in                held   진행 중 - standby 응답을 기다리는 동안도
 L2389   flushed  COMMITTED     out               held   커밋됨 - 보인다
 L2437   flushed  COMMITTED     out               free   커밋됨 - 행 잠금 대기자가 깨어난다
```

## 어디에서 쓰이는가

```text
 문장 하나가 트랜잭션 하나 (자동 커밋)
   exec_simple_query 의 start_xact_command      postgres.c L1046
   마지막 문장 뒤 finish_xact_command            postgres.c L1298
     CommandComplete 를 보내기 전에 커밋한다 - 커밋 중 ERROR 가 완료 응답 뒤에 오지 않게 (L1286-L1293 주석)

 BEGIN ... COMMIT 블록
   BeginTransactionBlock  STARTED -> BEGIN       xact.c L3934
   EndTransactionBlock    INPROGRESS -> END      xact.c L4056
   COMMIT 문장의 finish_xact_command 에서 TBLOCK_END 갈래가 CommitTransaction 을 부른다

 트랜잭션을 스스로 끊어 가며 도는 유틸리티
   vacuum() 이 바깥 트랜잭션을 먼저 커밋하고 테이블마다 새로 연다   commands/vacuum.c L616
   autovacuum worker 의 do_autovacuum                               postmaster/autovacuum.c L1915
```

## db-engine 에서는

같은 문제(언제 디스크에 남기고, 언제 남에게 보이게 하고, 언제 잠금을 푸나)를 db-engine 은 지연 적용(deferred apply)으로 풀었다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 행이 테이블에 닿는 때
   PostgreSQL  문장 실행 중 heap_insert 가 페이지에 바로 쓴다 (xmin = 내 XID)
               커밋 전까지는 스냅샷 규칙이 남에게서 가린다
   db-engine   insert 는 InsertRow 로그 append + pending 목록만. heap 은 commit 에서 한꺼번에

 커밋 순서
   PostgreSQL  commit 레코드 -> XLogFlush -> pg_xact -> (SyncRep 대기) -> ProcArray 에서 빠짐 -> 잠금 해제
   db-engine   CommitTx append -> logManager.sync() -> pending 을 heap 에 적용 -> releaseAll(id)

 flush 를 미룰 수 있나
   PostgreSQL  synchronous_commit = off 면 XLogFlush 를 건너뛰고 walwriter 에 맡긴다
   db-engine   commit 은 항상 sync() 한다

 "커밋됐다"의 기준
   PostgreSQL  WAL 의 commit 레코드 + 실행 중에는 pg_xact 비트와 ProcArray
   db-engine   로그에 CommitTx(txId) 가 있는가 (recovery 의 committed 집합)
```

두 구현 모두 "commit 레코드가 디스크에 닿은 순간이 커밋"이라는 규칙을 지킨다. db-engine 의 `commit()` 은 sync 직후 주석으로 이것을 "durability barrier"라고 적었다(impl/08-01-wal-recovery.md L419-L431). db-engine 은 heap 을 커밋 때만 만지므로 미커밋 행을 남에게서 가릴 장치가 필요 없고, PostgreSQL 은 행을 먼저 쓰기 때문에 pg_xact 와 ProcArray 두 곳을 순서대로 바꿔야 한다. 잠금은 둘 다 마지막에 푼다(impl/09-02-transaction-lock-integration.md L92-L101). 챕터: [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [09-02-transaction-lock-integration](../../../../../project/db-engine/09-02-transaction-lock-integration/).

## 단계

1. [StartTransactionCommand](01_StartTransactionCommand/README.md)가 문장 시작마다 blockState 를 보고, 트랜잭션 밖이면 새로 연다.
2. [StartTransaction](02_StartTransaction/README.md)이 가상 트랜잭션 ID 를 받아 ProcArray 에 알리고 상태를 TRANS_INPROGRESS 로 만든다.
3. [AssignTransactionId](03_AssignTransactionId/README.md)가 첫 쓰기에서 진짜 XID 를 받아 ProcArray 에 싣고 자기 XID 를 잠근다.
4. [CommitTransactionCommandInternal](04_CommitTransactionCommandInternal/README.md)이 문장 끝마다 blockState 로 커밋, 명령 카운터 증가, abort 정리 중 하나를 고른다.
5. [CommitTransaction](05_CommitTransaction/README.md)이 pre-commit, 기록, ProcArray 이탈, 잠금 해제를 순서대로 지휘한다.
6. [RecordTransactionCommit](06_RecordTransactionCommit/README.md)이 commit 레코드를 쓰고 동기/비동기를 갈라 flush 와 pg_xact 기록을 한다.
7. [XactLogCommitRecord](07_XactLogCommitRecord/README.md)가 commit 레코드의 본문(서브 XID, 지울 파일, 무효화 메시지)을 조립한다.
8. [TransactionIdCommitTree](08_TransactionIdCommitTree/README.md)가 pg_xact 의 2 비트를 COMMITTED 로 바꾼다.
9. [SyncRepWaitForLSN](09_SyncRepWaitForLSN/README.md)이 동기 복제 대기 큐에 들어가 walsender 가 깨울 때까지 잠든다.
10. [ProcArrayEndTransaction](10_ProcArrayEndTransaction/README.md)이 ProcArrayLock 아래에서 내 XID 를 지우고 latestCompletedXid 를 올린다.

## 결과가 쓰이는 곳

```text
 WAL 의 commit 레코드 (XLOG_XACT_COMMIT)
      --> 크래시 복구와 standby 가 xact_redo 로 pg_xact 를 다시 세운다
      --> 논리 디코딩이 트랜잭션 경계로 쓴다

 pg_xact 비트
      --> TransactionIdDidCommit 이 읽는다 ([MVCC 가시성 10](../mvcc-visibility/10_TransactionIdDidCommit/README.md))
      --> 힌트 비트(HEAP_XMIN_COMMITTED)를 세우는 근거가 된다

 ProcGlobal->xids[] 에서 빠짐, latestCompletedXid
      --> 다음 GetSnapshotData 의 xip, xmax 계산 ([MVCC 가시성 02](../mvcc-visibility/02_GetSnapshotData/README.md))

 잠금 해제
      --> 이 XID 에 XactLockTableWait 로 걸려 있던 행 잠금 대기자가 깨어난다
          ([heavyweight lock 11](../heavyweight-lock/11_LockReleaseAll/README.md))
```

## 다루지 않는 것

abort 경로(`AbortTransaction`, `RecordTransactionAbort`), 서브트랜잭션(`CommitSubTransaction`, SAVEPOINT), 2PC(`PrepareTransaction`, `FinishPreparedTransaction`), 병렬 worker 의 커밋 분기, 커밋 타임스탬프(`TransactionTreeSetCommitTsData`), 복제 origin 은 분기 이름만 짚었다. commit 레코드가 WAL 버퍼에 들어가고 디스크로 가는 과정 자체는 [행 쓰기와 WAL 기록](../heap-insert-wal/README.md)의 `XLogInsert`·`XLogFlush` 를, standby 응답을 받은 walsender 가 대기자를 깨우는 과정은 [스트리밍 복제](../streaming-replication/README.md)의 [12 SyncRepReleaseWaiters](../streaming-replication/12_SyncRepReleaseWaiters/README.md)를 본다.

## 하위 메서드

- [01 StartTransactionCommand](01_StartTransactionCommand/README.md)
- [02 StartTransaction](02_StartTransaction/README.md)
- [03 AssignTransactionId](03_AssignTransactionId/README.md)
- [04 CommitTransactionCommandInternal](04_CommitTransactionCommandInternal/README.md)
- [05 CommitTransaction](05_CommitTransaction/README.md)
- [06 RecordTransactionCommit](06_RecordTransactionCommit/README.md)
- [07 XactLogCommitRecord](07_XactLogCommitRecord/README.md)
- [08 TransactionIdCommitTree](08_TransactionIdCommitTree/README.md)
- [09 SyncRepWaitForLSN](09_SyncRepWaitForLSN/README.md)
- [10 ProcArrayEndTransaction](10_ProcArrayEndTransaction/README.md)
