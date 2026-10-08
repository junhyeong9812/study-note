# heavyweight lock

상위: [PostgreSQL 아키텍처 지도](../../README.md)

테이블·트랜잭션 ID·객체 같은 **이름 붙은 대상에 트랜잭션 끝까지 걸리는 잠금**이 잡히고, 기다리고, 풀리는 흐름이다. 페이지 내용을 잠깐 지키는 LWLock 이나 버퍼 content lock 과 달리, 이 잠금은 모드가 여덟 가지이고 충돌하면 잠들어 기다리며, 교착을 검사받고, 트랜잭션이 끝날 때 한꺼번에 풀린다. 입구는 [02] `LockAcquireExtended` 하나지만 안에서 길이 셋으로 갈린다. 이미 가진 잠금이면 backend 지역 해시만 보고 끝나고, 약한 테이블 잠금이면 공유 메모리 해시를 건드리지 않는 **fast-path** 로 끝나며, 그 밖에는 파티션 LWLock 을 잡고 공유 해시의 `LOCK`·`PROCLOCK` 을 고친다. 충돌하면 대기 큐에 들어가 잠들고, `deadlock_timeout`(기본 1000ms) 뒤에야 교착 검사를 한다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다. `lock.c`·`lmgr.c`·`proc.c`·`deadlock.c` 는 모두 `storage/lmgr/` 에 있다.

## 전체 그림

```text
 [01] LockRelationOid                                  lmgr.c L107
      +-- SetLocktagRelationOid                        L88   LOCKTAG = (dbOid, relOid)
      +-- [02] LockAcquireExtended                     lock.c L835
      |     +-- hash_search(LockMethodLocalHash)       L893  backend 지역 LOCALLOCK 을 찾거나 만든다
      |     +-- nLocks > 0 이면 GrantLockLocal, 끝     L939  (이미 가진 잠금)
      |     |
      |     +-- 갈래 1  fast-path (모드 1~3, 이 DB 의 테이블)
      |     |     +-- strong count 가 0 이면
      |     |     +-- [03] FastPathGrantRelationLock   L1002  내 PGPROC 슬롯에 비트 하나, 끝
      |     |
      |     +-- 갈래 2  강한 잠금 (모드 5~8, 테이블)
      |     |     +-- BeginStrongLockAcquire           L1029  strong count++ (이후 fast-path 금지)
      |     |     +-- [04] FastPathTransferRelationLocks L1030  남의 fast-path 잠금을 공유 해시로 옮긴다
      |     |
      |     +-- 공유 해시  (파티션 LWLock, 16 개 중 하나)  L1055
      |           +-- [05] SetupLockInTable            L1066  LOCK, PROCLOCK 을 찾거나 만든다
      |           +-- waitMask 와 충돌하면 바로 대기쪽  L1093
      |           +-- [06] LockCheckConflicts          L1096  grantMask, 내 몫, 그룹 몫을 뺀다
      |           +-- 충돌 없음 -> [07] GrantLock      L1102
      |           +-- 충돌      -> [08] JoinWaitQueue  L1112  (proc.c) 큐 자리를 정한다
      |                 +-- WaitOnLock                 L1220  파티션 LWLock 을 놓고
      |                       +-- [09] ProcSleep       proc.c L1342  latch 위에서 잠든다
      |                             +-- deadlock_timeout 이 울리면
      |                             +-- [10] CheckDeadLock  proc.c L1820
      |                                   +-- DeadLockCheck (deadlock.c L220)
      |     +-- GrantLockLocal, FinishStrongLockAcquire  L1245, L1251
      +-- AcceptInvalidationMessages                   lmgr.c L136  잠근 뒤 relcache 를 새로 맞춘다

 트랜잭션 끝
 ResourceOwnerRelease(RESOURCE_RELEASE_LOCKS) -> ProcReleaseLocks  proc.c L891
      +-- [11] LockReleaseAll                          lock.c L2275
            +-- LOCALLOCK 을 돌며 fast-path 는 비트만 지운다
            +-- 파티션마다 내 PROCLOCK 을 돌며 UnGrantLock, CleanUpLock
                  +-- 기다리던 이가 있으면 ProcLockWakeup  (proc.c L1772)
```

잠금 모드는 여덟 가지이고, 누가 누구와 충돌하는지는 `LockConflicts` 배열 한 장이 정한다. 아래 표는 그 배열을 그대로 펼친 것이다. 행이 요청, 열이 이미 잡힌 모드이며 `X` 가 충돌이다. 배열은 대칭이다.

```text
 LockConflicts (lock.c L65-L105), 모드 번호는 lockdefs.h L36-L45

         1    2    3    4    5    6    7    8     conflictTab   대표 명령 (lockdefs.h 주석)
 1 AS    .    .    .    .    .    .    .    X     0x100         SELECT
 2 RS    .    .    .    .    .    .    X    X     0x180         SELECT FOR UPDATE/FOR SHARE
 3 RX    .    .    .    .    X    X    X    X     0x1e0         INSERT, UPDATE, DELETE
 4 SUX   .    .    .    X    X    X    X    X     0x1f0         VACUUM (non-FULL), ANALYZE, CREATE INDEX CONCURRENTLY
 5 S     .    .    X    X    .    X    X    X     0x1d8         CREATE INDEX
 6 SRX   .    .    X    X    X    X    X    X     0x1f8
 7 X     .    X    X    X    X    X    X    X     0x1fc
 8 AX    X    X    X    X    X    X    X    X     0x1fe         ALTER TABLE, DROP TABLE, VACUUM FULL, LOCK TABLE

 AS=AccessShare RS=RowShare RX=RowExclusive SUX=ShareUpdateExclusive
 S=Share SRX=ShareRowExclusive X=Exclusive AX=AccessExclusive
 conflictTab 값은 LOCKBIT_ON(m) = 1 << m 의 합 (비트 0 은 쓰지 않는다)

 fast-path 의 경계가 이 표에서 나온다 (lock.c L259-L277)
   1~3 끼리는 서로 충돌하지 않는다           -> 1~3 은 fast-path 로 잡을 수 있다
   4 (SUX) 는 자기 자신과 충돌하지만 1~3 과는 충돌하지 않는다 -> 어느 쪽에도 끼지 않는다
   5~8 은 1~3 중 하나 이상과 충돌한다        -> "강한" 잠금, 잡기 전에 fast-path 를 막고 옮긴다
```

잠금 하나는 세 층의 자료에 나뉘어 기록된다. backend 지역 해시가 "몇 번 잡았나"를 세고, 공유 해시가 "누가 무엇을 들고 무엇을 기다리나"를 적는다. fast-path 로 잡은 잠금은 공유 해시에 없고 자기 `PGPROC` 슬롯에만 있다.

```text
 backend 지역 - LockMethodLocalHash (lock.c L323)
   LOCALLOCK   key = LOCKTAG + mode                      lock.h L427
     nLocks                  이 backend 가 잡은 횟수
     lockOwners[]            ResourceOwner 별 횟수 (owner NULL = 세션 잠금)
     lock, proclock          공유 해시의 LOCK, PROCLOCK 을 가리킨다 (fast-path 면 NULL)
     holdsStrongLockCount    strong count 를 올려 둔 잠금인가

 공유 메모리 - 파티션 16 개 (LockHashPartition = hashcode % 16, lock.h L525)
   LOCK        key = LOCKTAG                             lock.h L309
     grantMask, waitMask     잡힌 모드, 기다리는 모드의 비트
     granted[], requested[]  모드별 수 (requested 는 대기 포함)
     procLocks               이 대상의 PROCLOCK 목록
     waitProcs               기다리는 PGPROC 큐
   PROCLOCK    key = (LOCK*, PGPROC*)                    lock.h L370
     holdMask                이 proc 이 쥔 모드
     releaseMask             LockReleaseAll 이 풀 모드를 적는 작업 칸
     lockLink, procLink      LOCK.procLocks 와 PGPROC.myProcLocks[파티션] 양쪽에 걸린다

 fast-path - 공유 해시에 없고 내 PGPROC 에만 있다 (proc.h L308-L310)
   fpRelId[slot]             테이블 OID
   fpLockBits[group]         슬롯마다 3 비트 (모드 1, 2, 3), 그룹 하나에 16 슬롯
   FastPathStrongRelationLocks->count[1024]
                             강한 잠금을 쥐었거나 잡는 중인 수 (hashcode % 1024)
```

## 어디에서 쓰이는가

```text
 테이블을 여는 모든 길
   relation_open -> LockRelationOid               access/common/relation.c L55
   이름으로 찾을 때 RangeVarGetRelidExtended       catalog/namespace.c L592
   캐시된 계획을 실행하기 전 AcquireExecutorLocks  utils/cache/plancache.c L1935

 트랜잭션 ID 잠금 (행 잠금 대기의 실체)
   XID 를 받을 때 XactLockTableInsert             lmgr.c L628  자기 XID 에 ExclusiveLock
   행 충돌 시 XactLockTableWait                   lmgr.c L697  상대 XID 에 ShareLock 을 걸고 기다린다
     heap_update 가 부르는 곳 access/heap/heapam.c L3714
   행 자체의 잠금은 튜플 헤더(xmax)에 있고, 기다림만 이 흐름을 탄다

 그 밖의 LOCKTAG 종류 (lmgr.c)
   페이지 LockPage L507, 튜플 LockTuple L562, 확장 LockRelationForExtension L424,
   객체 LockDatabaseObject L1008, advisory lock (USER_LOCKMETHOD)
```

## db-engine 에서는

같은 문제(누가 무엇을 쥐었나, 충돌하면 어떻게 하나, 언제 푸나)를 db-engine 은 모드 두 개와 즉시 실패로 풀었다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 모드
   PostgreSQL  8 개, 충돌은 LockConflicts 비트마스크 표 한 장
   db-engine   SHARED, EXCLUSIVE 두 개. 충돌 규칙은 acquire 안의 when 분기

 기록
   PostgreSQL  LOCALLOCK(지역) + LOCK, PROCLOCK(공유 해시 16 파티션) + fast-path 슬롯
               같은 대상의 두 모드는 holdMask 의 비트 두 개로 따로 쥔다
   db-engine   MutableMap<String, MutableList<Holder>>, @Synchronized 하나
               S -> X upgrade 는 Holder 를 바꿔 끼운다 (다른 보유자가 없을 때만)

 충돌하면
   PostgreSQL  대기 큐에 들어가 잠들고, deadlock_timeout 뒤 대기 그래프에서 순환을 찾는다
               soft 순환은 큐 순서를 바꿔 풀고, hard 순환이면 자신을 ERROR 로 끝낸다
   db-engine   LockConflict 예외로 즉시 실패. 기다림이 없으니 교착도 없다

 해제
   PostgreSQL  트랜잭션 끝 ResourceOwnerRelease -> ProcReleaseLocks -> LockReleaseAll
               풀면서 ProcLockWakeup 이 깨울 수 있는 대기자에게 GrantLock 까지 해 준다
   db-engine   TransactionWithLock.commit / abort 의 마지막에 releaseAll(txId)
```

db-engine 의 impl 문서(09-01 과제 3번)는 대기 모델을 도입하면 교착이 생기고, 그 짝으로 타임아웃, 대기 그래프 순환 탐지, 락 순서 강제 중 하나가 필요하다고 정리했다. PostgreSQL 은 그중 대기 그래프 탐지를 쓰되, 매번 검사하지 않고 `deadlock_timeout` 만큼 기다린 뒤에만 검사한다(proc.c L1370-L1377 주석). 두 구현 모두 Strict 2PL 이라 트랜잭션 끝에서 한꺼번에 푼다. 챕터: [09-01-lock-manager](../../../../../project/db-engine/09-01-lock-manager/), [09-02-transaction-lock-integration](../../../../../project/db-engine/09-02-transaction-lock-integration/).

## 단계

1. [LockRelationOid](01_LockRelationOid/README.md)가 테이블 OID 로 LOCKTAG 를 만들고, 잠근 뒤 무효화 메시지를 받는다.
2. [LockAcquireExtended](02_LockAcquireExtended/README.md)가 지역 해시, fast-path, 공유 해시 세 갈래를 고르고 대기까지 지휘한다.
3. [FastPathGrantRelationLock](03_FastPathGrantRelationLock/README.md)이 내 PGPROC 슬롯에 모드 비트를 세운다.
4. [FastPathTransferRelationLocks](04_FastPathTransferRelationLocks/README.md)가 강한 잠금 앞에서 모든 backend 의 fast-path 잠금을 공유 해시로 옮긴다.
5. [SetupLockInTable](05_SetupLockInTable/README.md)이 LOCK 과 PROCLOCK 을 찾거나 만들고 요청 수를 올린다.
6. [LockCheckConflicts](06_LockCheckConflicts/README.md)가 이미 잡힌 잠금과의 충돌을 내 몫과 그룹 몫을 빼고 판정한다.
7. [GrantLock](07_GrantLock/README.md)이 공유 자료에 승인을 기록하고, `GrantLockLocal` 이 지역 횟수를 센다.
8. [JoinWaitQueue](08_JoinWaitQueue/README.md)가 대기 큐의 자리를 정하고, 즉시 보이는 교착을 잡는다.
9. [ProcSleep](09_ProcSleep/README.md)이 타이머를 걸고 latch 위에서 잠들었다 깨기를 반복한다.
10. [CheckDeadLock](10_CheckDeadLock/README.md)이 모든 파티션을 잠그고 대기 그래프에서 순환을 찾는다.
11. [LockReleaseAll](11_LockReleaseAll/README.md)이 트랜잭션 끝에 잠금을 전부 풀고 기다리던 이를 깨운다.

## 결과가 쓰이는 곳

```text
 LOCALLOCK (nLocks, lockOwners)
      --> 같은 잠금 재요청은 공유 메모리를 보지 않고 L939 에서 끝난다
      --> ResourceOwner 가 서브트랜잭션 단위 해제(LockReleaseCurrentOwner)에 쓴다

 LOCK / PROCLOCK
      --> pg_locks 뷰가 GetLockStatusData (lock.c L3763) 로 읽는다
      --> 교착 검사기가 holdMask 와 waitProcs 로 대기 그래프를 만든다

 대기 중인 PGPROC (waitLock, waitLockMode, waitStart)
      --> pg_locks.waitstart, log_lock_waits 메시지

 AccessExclusiveLock 획득
      --> wal_level 이 replica 이상이면 LogAccessExclusiveLock 으로 WAL 에 남아 (lock.c L1264)
          standby 가 같은 잠금을 재현한다
```

## 다루지 않는 것

LWLock 과 spinlock 자체(`storage/lmgr/lwlock.c`, `s_lock.c`), 직렬화 이상을 막는 predicate lock(`predicate.c`, SSI), 행 잠금의 튜플 헤더 쪽 처리(`heap_lock_tuple`, MultiXact), 가상 트랜잭션 ID 잠금(`VirtualXactLock`), 2PC 로 잠금을 넘기는 `AtPrepare_Locks`·`PostPrepare_Locks`, 병렬 쿼리의 lock group(`BecomeLockGroupLeader`)은 판정 분기에서 이름만 짚었다. 교착 검사의 큐 재배치 알고리즘(`TopoSort`, `ExpandConstraints`)과 hot standby 의 잠금 충돌 해결(`ResolveRecoveryConflictWithLock`)도 요약만 했다.

## 하위 메서드

- [01 LockRelationOid](01_LockRelationOid/README.md)
- [02 LockAcquireExtended](02_LockAcquireExtended/README.md)
- [03 FastPathGrantRelationLock](03_FastPathGrantRelationLock/README.md)
- [04 FastPathTransferRelationLocks](04_FastPathTransferRelationLocks/README.md)
- [05 SetupLockInTable](05_SetupLockInTable/README.md)
- [06 LockCheckConflicts](06_LockCheckConflicts/README.md)
- [07 GrantLock](07_GrantLock/README.md)
- [08 JoinWaitQueue](08_JoinWaitQueue/README.md)
- [09 ProcSleep](09_ProcSleep/README.md)
- [10 CheckDeadLock](10_CheckDeadLock/README.md)
- [11 LockReleaseAll](11_LockReleaseAll/README.md)
