# MVCC 가시성과 스냅샷

상위: [PostgreSQL 아키텍처 지도](../../README.md)

읽는 쪽이 **"지금 진행 중인 트랜잭션 목록"을 스냅샷으로 한 번 찍어 두고, 힙 튜플마다 헤더의 `t_xmin` 과 `t_xmax` 를 그 목록에 대어 보아 보일지를 정하는** 흐름이다. 흐름은 두 반쪽으로 나뉜다. 스냅샷을 만드는 쪽은 `ProcArrayLock` 공유 잠금 아래에서 모든 backend 의 xid 슬롯을 한 바퀴 돌아 `xmin`, `xmax`, `xip[]` 세 값을 만든다. 판정하는 쪽은 페이지 한 장씩 버퍼 share 잠금을 잡고, 튜플마다 "스냅샷이 끝났다고 하는가"를 먼저 묻고 끝났다고 할 때만 pg_xact 에서 커밋인지 abort 인지 읽는다. 읽은 결과는 튜플의 힌트 비트에 적어 다음 방문자가 pg_xact 를 건너뛰게 한다. 격리 수준은 판정 규칙을 바꾸지 않는다. **스냅샷을 언제 다시 찍는가**만 바꾼다. READ COMMITTED 는 문장마다, REPEATABLE READ 와 SERIALIZABLE 은 트랜잭션의 첫 스냅샷 하나를 끝까지 쓴다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 스냅샷 만들기 (문장 시작)
 ------------------------------------------------------------------
 exec_simple_query -> PortalStart                      tcop/pquery.c L481
 [01] GetTransactionSnapshot                           utils/time/snapmgr.c L271
      +-- 트랜잭션 첫 호출 (!FirstSnapshotSet)         L293
      |     +-- RR 이상 (IsolationUsesXactSnapshot)    L315
      |     |     [02] 로 찍고 CopySnapshot             L321-L323  FirstXactSnapshot 으로 고정
      |     +-- READ COMMITTED                         L330  [02] 로 찍는다
      +-- 두 번째부터: RR 이상이면 같은 스냅샷         L336-L337
      +--             READ COMMITTED 면 다시 찍는다     L342
 [02] GetSnapshotData                                  storage/ipc/procarray.c L2175
      +-- LWLockAcquire(ProcArrayLock, LW_SHARED)      L2231
      +-- GetSnapshotDataReuse                         L2233  그새 끝난 트랜잭션이 없으면 재사용
      +-- xmax = latestCompletedXid + 1                L2248-L2249
      +-- PGPROC xid 슬롯을 훑어 xip[], subxip[], xmin  L2273-L2364
      +-- MyProc->xmin 이 비었으면 건다                L2413-L2414
 ------------------------------------------------------------------
      executor 가 RegisterSnapshot 해서 es_snapshot 으로 들고 내려간다 (executor/execMain.c L245)
 ------------------------------------------------------------------
 판정 (SeqScan 이 다음 행을 달라고 할 때)
 SeqNext -> table_scan_getnextslot                     executor/nodeSeqscan.c L81
 [03] heap_getnextslot                                 access/heap/heapam.c L1388
      +-- [04] heapgettup_pagemode                     L1395  MVCC 스냅샷이면 page 모드
            +-- heap_fetch_next_buffer                 L1041  --> [버퍼 관리] read stream, pin
            +-- [05] heap_prepare_pagescan             L1050
            |     +-- heap_page_prune_opt              L576   기회가 되면 죽은 튜플 정리
            |     +-- LockBuffer(SHARE)                L583
            |     +-- [06] page_collect_tuples         L621-L634  보이는 줄 번호 -> rs_vistuples[]
            |     |     +-- [07] HeapTupleSatisfiesVisibility       L531
            |     |           +-- [08] HeapTupleSatisfiesMVCC        heapam_visibility.c L960
            |     |                 +-- [09] XidInMVCCSnapshot       snapmgr.c L1870
            |     |                 +-- [10] TransactionIdDidCommit  access/transam/transam.c L126
            |     |                 +-- SetHintBits                  heapam_visibility.c L114
            |     +-- LockBuffer(UNLOCK)               L637
            +-- rs_vistuples[] 를 하나씩 돌려준다       L1061-L1082
```

스냅샷 하나가 XID 축을 세 구간으로 나눈다. 판정 규칙의 부등호는 전부 이 그림에서 나온다. 예는 [02] 에서 계산한 스냅샷이다.

```text
 스냅샷 {xmin 100, xmax 105, xip [100, 103]}, 내 xid 102

        99   | 100  101  102  103  104 | 105  106 ...
   ---------+--------------------------+--------------
   xid < xmin        xmin <= xid < xmax       xid >= xmax
   끝남              xip 에 있으면 진행 중     진행 중
                     없으면 끝남

   경계  xid == xmin(100)  배열을 본다 -> xip 에 있으면 진행 중
         xid == xmax(105)  진행 중 (snapmgr.c L1884 의 >=)
   끝남 = 커밋 또는 abort. 어느 쪽인지는 pg_xact 를 봐야 안다
```

튜플이 보이는 조건은 한 줄로 줄일 수 있다. 넣은 쪽이 나에게 커밋으로 보이고, 지운 쪽은 없거나 나에게 커밋으로 보이지 않아야 한다.

```text
 보인다 = xmin 이 "나에게 커밋" 이고 xmax 가 "나에게 커밋이 아님"

 "나에게 커밋" (xid 가 내 것이 아닐 때)
     = XidInMVCCSnapshot(xid) == false        스냅샷이 끝났다고 한다   [09]
       그리고 TransactionIdDidCommit(xid)     pg_xact 가 커밋이라 한다 [10]
       (힌트 비트가 이미 커밋이면 두 번째는 건너뛴다)

 xid 가 내 것이면 스냅샷 대신 command id 로 본다
     cmin >= curcid  이면 넣은 것이 아직 안 보인다
     cmax >= curcid  이면 지운 것이 아직 안 보인다 (행이 보인다)
```

격리 수준은 [01] 의 갈래 하나로만 갈린다. 같은 트랜잭션에서 문장 둘 사이에 남의 커밋이 끼면 이렇게 된다.

```text
 BEGIN; SELECT (A); -- T9 COMMIT --; SELECT (B); COMMIT;

 READ COMMITTED
   SELECT A    [02] 로 S1
   SELECT B    [02] 로 S2                        T9 보임

 REPEATABLE READ, SERIALIZABLE
   SELECT A    [02] 로 S1, 복사해 FirstXactSnapshot
   SELECT B    S1 그대로                         T9 안 보임

 둘 다  문장 사이 CommandCounterIncrement 는 curcid 만 바꾼다 (SnapshotSetCommandId)
        COMMIT 에서 FirstSnapshotSet = false

 스냅샷 시점은 BEGIN 이 아니라 첫 GetTransactionSnapshot 호출이다
 SERIALIZABLE 은 첫 스냅샷을 GetSerializableTransactionSnapshot 으로 찍는다 (snapmgr.c L319)
```

## 어디에서 쓰이는가

```text
 [executor]            SeqNext 가 table_scan_getnextslot 으로 이 흐름의 [03] 에 들어온다
                       인덱스 스캔은 heap_hot_search_buffer 에서 같은 [07] 을 부른다 (heapam.c L1806)
 [쿼리 실행 파이프라인] exec_simple_query 와 PortalStart 가 [01] 을 부르고 활성 스냅샷으로 민다
 [커밋]                pg_xact 에 COMMITTED 를 적고(TransactionIdCommitTree) ProcArray 에서 빠지는
                       (ProcArrayEndTransaction) 순서가 [09] 와 [10] 의 호출 순서를 정한다
 [vacuum]              판정 함수는 HeapTupleSatisfiesVacuum 으로 다르지만,
                       어디까지 지울지는 [02] 가 건 PGPROC xmin 들로 정한다 (ComputeXidHorizons)
 [버퍼 관리]           [05] 가 share 잠금 아래서 힌트 비트를 적고 MarkBufferDirtyHint 로 dirty 표시
```

다음 흐름은 [executor](../executor/README.md)로 돌아가 보이는 행을 위로 올리는 쪽이다. 페이지를 읽어 오는 과정은 [버퍼 관리](../buffer-manager/README.md), pg_xact 를 쓰는 쪽은 [커밋](../commit/README.md)에 있다.

## db-engine 에서는

같은 문제(덮어쓰지 않고 버전을 쌓고, 읽는 쪽이 자기 시점의 버전을 고르기)를 db-engine 은 키별 버전 체인과 "내 xid + 활성 집합" 스냅샷으로 풀었다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 버전이 사는 곳
   PostgreSQL  힙 페이지의 튜플. UPDATE 는 새 튜플을 넣고 옛 튜플의 t_xmax 를 채운다
   db-engine   MVCCStore 의 메모리 체인 List<Version(value, xidStart, xidEnd)>
               10-03 MVCCTableHeap 도 체인은 메모리, 디스크 heap 에는 버전 정보가 없다

 스냅샷
   PostgreSQL  {xmin, xmax = latestCompletedXid + 1, xip[]}  읽기 전용이면 xid 없이도 찍는다
   db-engine   Snapshot(xid, active)  begin() 이 xid 를 받고 그 순간 활성 집합을 복사한다
               내 xid 가 상한 역할을 한다 (xidStart > xid 면 안 보임)

 판정
   PostgreSQL  xmin 쪽, xmax 쪽 각각 [09] 스냅샷 -> [10] pg_xact, 자기 것은 curcid 로
   db-engine   isVisible 여섯 줄. xidStart 가 내 뒤이거나 활성이면 안 보임,
               xidEnd 가 없거나 내 뒤이거나 활성이면 보임

 abort
   PostgreSQL  pg_xact 의 ABORTED 와 INVALID 힌트로 거른다
   db-engine   commit 만 있다. 활성 집합에서 빠진 xid 는 모두 커밋으로 취급된다

 격리 수준
   PostgreSQL  RC 는 문장마다 새 스냅샷, RR 이상은 첫 스냅샷 고정
               같은 행의 동시 갱신 충돌은 UPDATE 경로(HeapTupleSatisfiesUpdate)가 다룬다 (이 흐름 밖)
   db-engine   begin() 한 번에 스냅샷 고정 (RR 꼴). lost update 를 막지 못함을 10-02 테스트가
               고정해 두고, write skew 도 못 막는다고 10-02 본문이 적었다
```

db-engine 은 판정 규칙을 한 함수에 모아 이해하기 쉽지만, abort 와 자기 트랜잭션 안의 명령 순서(curcid)를 다루지 않는다. PostgreSQL 은 버전의 xid 를 힙 튜플 헤더에, 커밋 여부를 pg_xact 에 따로 둔다. 그래서 판정이 pg_xact 를 읽어야 할 때가 있고, 그 비용을 힌트 비트가 줄인다. 아무에게도 안 보이게 된 버전은 vacuum 이 치운다. 10-03 문서가 "디스크의 행에 버전을 붙이려면 원래는 tuple마다 `xmin`/`xmax`를 저장해야 한다(PostgreSQL이 그렇게 한다)"고 짚은 자리가 이 흐름이다. 챕터: [10-01-mvcc](../../../../../project/db-engine/10-01-mvcc/), [10-02-isolation-anomaly](../../../../../project/db-engine/10-02-isolation-anomaly/), [10-03-mvcc-table-heap](../../../../../project/db-engine/10-03-mvcc-table-heap/).

## 단계

1. [GetTransactionSnapshot](01_GetTransactionSnapshot/README.md)이 격리 수준에 따라 새로 찍을지, 트랜잭션 스냅샷을 돌려줄지 정한다.
2. [GetSnapshotData](02_GetSnapshotData/README.md)가 ProcArray 를 훑어 `xmin`, `xmax`, `xip[]` 를 만든다.
3. [heap_getnextslot](03_heap_getnextslot/README.md)이 executor 의 요청을 받아 page 모드 스캔으로 보낸다.
4. [heapgettup_pagemode](04_heapgettup_pagemode/README.md)가 페이지를 받아 보이는 튜플 목록을 하나씩 돌려준다.
5. [heap_prepare_pagescan](05_heap_prepare_pagescan/README.md)이 prune 하고 share 잠금 아래서 페이지 전체를 판정한다.
6. [page_collect_tuples](06_page_collect_tuples/README.md)가 줄 포인터를 돌며 보이는 줄 번호를 모은다.
7. [HeapTupleSatisfiesVisibility](07_HeapTupleSatisfiesVisibility/README.md)가 스냅샷 종류로 판정 함수를 고른다.
8. [HeapTupleSatisfiesMVCC](08_HeapTupleSatisfiesMVCC/README.md)가 xmin 쪽과 xmax 쪽을 차례로 판정하고 힌트 비트를 적는다.
9. [XidInMVCCSnapshot](09_XidInMVCCSnapshot/README.md)이 xid 가 스냅샷 기준으로 진행 중인지 답한다.
10. [TransactionIdDidCommit](10_TransactionIdDidCommit/README.md)이 끝난 xid 의 커밋 여부를 pg_xact 에서 읽는다.

## 결과가 쓰이는 곳

```text
 Snapshot (xmin, xmax, xip[], curcid)
      --> 활성 스냅샷 스택과 es_snapshot 으로 문장 내내 쓰인다
      --> RR 이상이면 FirstXactSnapshot 으로 트랜잭션 끝까지 남는다

 PGPROC->xmin
      --> 다른 backend 의 ComputeXidHorizons 가 읽는다 -> [vacuum] 과 prune 의 제거 기준

 rs_vistuples[] -> 슬롯
      --> executor 가 qual 과 projection 을 적용해 위로 올린다

 t_infomask 힌트 비트, dirty 페이지
      --> 다음 판정이 pg_xact 를 건너뛴다
      --> 읽기만 한 페이지도 dirty 가 되어 나중에 디스크에 쓰일 수 있다 [버퍼 관리] [체크포인트]
```

## 다루지 않는 것

SERIALIZABLE 의 SSI(predicate lock, `HeapCheckForSerializableConflictOut`), UPDATE 와 DELETE 가 쓰는 `HeapTupleSatisfiesUpdate` 와 동시 갱신 대기, MultiXact, 핫 스탠바이의 `KnownAssignedXids` 스냅샷, 논리 디코딩의 historic 스냅샷, 카탈로그 스냅샷, `SET TRANSACTION SNAPSHOT` 스냅샷 공유, index-only scan 의 visibility map 판정, 튜플 모드 `heapgettup` 은 이 흐름의 곁가지라 요약만 했다. 죽은 튜플을 치우는 쪽은 [vacuum](../vacuum/README.md)이다.

## 하위 메서드

- [01 GetTransactionSnapshot](01_GetTransactionSnapshot/README.md)
- [02 GetSnapshotData](02_GetSnapshotData/README.md)
- [03 heap_getnextslot](03_heap_getnextslot/README.md)
- [04 heapgettup_pagemode](04_heapgettup_pagemode/README.md)
- [05 heap_prepare_pagescan](05_heap_prepare_pagescan/README.md)
- [06 page_collect_tuples](06_page_collect_tuples/README.md)
- [07 HeapTupleSatisfiesVisibility](07_HeapTupleSatisfiesVisibility/README.md)
- [08 HeapTupleSatisfiesMVCC](08_HeapTupleSatisfiesMVCC/README.md)
- [09 XidInMVCCSnapshot](09_XidInMVCCSnapshot/README.md)
- [10 TransactionIdDidCommit](10_TransactionIdDidCommit/README.md)
