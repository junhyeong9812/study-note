# GetSnapshotData

상위: [MVCC 가시성과 스냅샷](../README.md)

**스냅샷의 세 값 `xmin`, `xmax`, `xip[]` 를 실제로 만드는 함수다.** `ProcArrayLock` 을 공유 모드로 잡고 모든 backend 의 xid 슬롯을 한 번 훑어, 그 순간 진행 중인 트랜잭션 목록을 복사한다. 그 사이에 끝난 트랜잭션이 하나도 없으면 훑지 않고 이전 결과를 그대로 쓴다.

## 위치

`storage/ipc` / `procarray.c` L2175-L2519 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L2175-L2519))

## 실제 코드

머리 주석이 세 값의 뜻을 정의한다. 이 흐름의 판정 규칙은 전부 이 정의에서 나온다.

```c
// procarray.c L2142-L2175
/*
 * GetSnapshotData -- returns information about running transactions.
 *
 * The returned snapshot includes xmin (lowest still-running xact ID),
 * xmax (highest completed xact ID + 1), and a list of running xact IDs
 * in the range xmin <= xid < xmax.  It is used as follows:
 *		All xact IDs < xmin are considered finished.
 *		All xact IDs >= xmax are considered still running.
 *		For an xact ID xmin <= xid < xmax, consult list to see whether
 *		it is considered running or not.
 * This ensures that the set of transactions seen as "running" by the
 * current xact will not change after it takes the snapshot.
 *
 * All running top-level XIDs are included in the snapshot, except for lazy
 * VACUUM processes.  We also try to include running subtransaction XIDs,
 * but since PGPROC has only a limited cache area for subxact XIDs, full
 * information may not be available.  If we find any overflowed subxid arrays,
 * we have to mark the snapshot's subxid data as overflowed, and extra work
 * *may* need to be done to determine what's running (see XidInMVCCSnapshot()).
 *
 * We also update the following backend-global variables:
 *		TransactionXmin: the oldest xmin of any snapshot in use in the
 *			current transaction (this is the same as MyProc->xmin).
 *		RecentXmin: the xmin computed for the most recent snapshot.  XIDs
 *			older than this are known not running any more.
 *
 * And try to advance the bounds of GlobalVis{Shared,Catalog,Data,Temp}Rels
 * for the benefit of the GlobalVisTest* family of functions.
 *
 * Note: this function should probably not be called with an argument that's
 * not statically allocated (see xip allocation below).
 */
Snapshot
GetSnapshotData(Snapshot snapshot)
```

잠금을 잡고, 재사용을 시도하고, `xmax` 와 `xmin` 의 시작값을 정한다.

```c
// procarray.c L2227-L2259
	/*
	 * It is sufficient to get shared lock on ProcArrayLock, even if we are
	 * going to set MyProc->xmin.
	 */
	LWLockAcquire(ProcArrayLock, LW_SHARED);

	if (GetSnapshotDataReuse(snapshot))
	{
		LWLockRelease(ProcArrayLock);
		return snapshot;
	}

	latest_completed = TransamVariables->latestCompletedXid;
	mypgxactoff = MyProc->pgxactoff;
	myxid = other_xids[mypgxactoff];
	Assert(myxid == MyProc->xid);

	oldestxid = TransamVariables->oldestXid;
	curXactCompletionCount = TransamVariables->xactCompletionCount;

	/* xmax is always latestCompletedXid + 1 */
	xmax = XidFromFullTransactionId(latest_completed);
	TransactionIdAdvance(xmax);
	Assert(TransactionIdIsNormal(xmax));

	/* initialize xmin calculation with xmax */
	xmin = xmax;

	/* take own xid into account, saves a check inside the loop */
	if (TransactionIdIsNormal(myxid) && NormalTransactionIdPrecedes(myxid, xmin))
		xmin = myxid;

	snapshot->takenDuringRecovery = RecoveryInProgress();
```

PGPROC 배열을 한 바퀴 돈다. 주석은 줄였다.

```c
// procarray.c L2261-L2365
	if (!snapshot->takenDuringRecovery)
	{
		int			numProcs = arrayP->numProcs;
		TransactionId *xip = snapshot->xip;
		int		   *pgprocnos = arrayP->pgprocnos;
		XidCacheStatus *subxidStates = ProcGlobal->subxidStates;
		uint8	   *allStatusFlags = ProcGlobal->statusFlags;

// ... (L2269-L2272 생략: 주석)
		for (int pgxactoff = 0; pgxactoff < numProcs; pgxactoff++)
		{
			/* Fetch xid just once - see GetNewTransactionId */
			TransactionId xid = UINT32_ACCESS_ONCE(other_xids[pgxactoff]);
			uint8		statusFlags;

			Assert(allProcs[arrayP->pgprocnos[pgxactoff]].pgxactoff == pgxactoff);

// ... (L2281-L2284 생략: 주석)
			if (likely(xid == InvalidTransactionId))
				continue;

// ... (L2288-L2292 생략: 주석)
			if (pgxactoff == mypgxactoff)
				continue;

// ... (L2296-L2302 생략: 주석과 Assert)

// ... (L2304-L2308 생략: 주석)
			if (!NormalTransactionIdPrecedes(xid, xmax))
				continue;

// ... (L2312-L2315 생략: 주석)
			statusFlags = allStatusFlags[pgxactoff];
			if (statusFlags & (PROC_IN_LOGICAL_DECODING | PROC_IN_VACUUM))
				continue;

			if (NormalTransactionIdPrecedes(xid, xmin))
				xmin = xid;

			/* Add XID to snapshot. */
			xip[count++] = xid;

// ... (L2326-L2340 생략: 주석)
			if (!suboverflowed)
			{

				if (subxidStates[pgxactoff].overflowed)
					suboverflowed = true;
				else
				{
					int			nsubxids = subxidStates[pgxactoff].count;

					if (nsubxids > 0)
					{
						int			pgprocno = pgprocnos[pgxactoff];
						PGPROC	   *proc = &allProcs[pgprocno];

						pg_read_barrier();	/* pairs with GetNewTransactionId */

						memcpy(snapshot->subxip + subcount,
							   proc->subxids.xids,
							   nsubxids * sizeof(TransactionId));
						subcount += nsubxids;
					}
				}
			}
		}
	}
```

자기 `xmin` 을 PGPROC 에 걸고 잠금을 푼 뒤, 결과를 스냅샷에 적는다.

```c
// procarray.c L2405-L2416
	/*
	 * Fetch into local variable while ProcArrayLock is held - the
	 * LWLockRelease below is a barrier, ensuring this happens inside the
	 * lock.
	 */
	replication_slot_xmin = procArray->replication_slot_xmin;
	replication_slot_catalog_xmin = procArray->replication_slot_catalog_xmin;

	if (!TransactionIdIsValid(MyProc->xmin))
		MyProc->xmin = TransactionXmin = xmin;

	LWLockRelease(ProcArrayLock);
```

L2418-L2496 은 `GlobalVis*` 경계 갱신이라 건너뛴다.

```c
// procarray.c L2498-L2519
	RecentXmin = xmin;
	Assert(TransactionIdPrecedesOrEquals(TransactionXmin, RecentXmin));

	snapshot->xmin = xmin;
	snapshot->xmax = xmax;
	snapshot->xcnt = count;
	snapshot->subxcnt = subcount;
	snapshot->suboverflowed = suboverflowed;
	snapshot->snapXactCompletionCount = curXactCompletionCount;

	snapshot->curcid = GetCurrentCommandId(false);

	/*
	 * This is a new snapshot, so set both refcounts are zero, and mark it as
	 * not copied in persistent memory.
	 */
	snapshot->active_count = 0;
	snapshot->regd_count = 0;
	snapshot->copied = false;

	return snapshot;
}
```

재사용 판정이다. 트랜잭션이 끝날 때마다 오르는 `xactCompletionCount` 가 그대로면 스냅샷 내용도 같다.

```c
// procarray.c L2095-L2140
GetSnapshotDataReuse(Snapshot snapshot)
{
	uint64		curXactCompletionCount;

	Assert(LWLockHeldByMe(ProcArrayLock));

	if (unlikely(snapshot->snapXactCompletionCount == 0))
		return false;

	curXactCompletionCount = TransamVariables->xactCompletionCount;
	if (curXactCompletionCount != snapshot->snapXactCompletionCount)
		return false;

// ... (L2108-L2127 생략: 재사용이 안전한 이유 (주석))
	if (!TransactionIdIsValid(MyProc->xmin))
		MyProc->xmin = TransactionXmin = snapshot->xmin;

	RecentXmin = snapshot->xmin;
	Assert(TransactionIdPrecedesOrEquals(TransactionXmin, RecentXmin));

	snapshot->curcid = GetCurrentCommandId(false);
	snapshot->active_count = 0;
	snapshot->regd_count = 0;
	snapshot->copied = false;

	return true;
}
```

그 카운터와 `latestCompletedXid` 는 트랜잭션이 끝날 때 `ProcArrayLock` 을 배타로 잡은 채 함께 바뀐다.

`storage/ipc` / `procarray.c` L731-L777 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L731-L777))

```c
// procarray.c L731-L777
ProcArrayEndTransactionInternal(PGPROC *proc, TransactionId latestXid)
{
	int			pgxactoff = proc->pgxactoff;

	/*
	 * Note: we need exclusive lock here because we're going to change other
	 * processes' PGPROC entries.
	 */
	Assert(LWLockHeldByMeInMode(ProcArrayLock, LW_EXCLUSIVE));
	Assert(TransactionIdIsValid(ProcGlobal->xids[pgxactoff]));
	Assert(ProcGlobal->xids[pgxactoff] == proc->xid);

	ProcGlobal->xids[pgxactoff] = InvalidTransactionId;
	proc->xid = InvalidTransactionId;
	proc->vxid.lxid = InvalidLocalTransactionId;
	proc->xmin = InvalidTransactionId;
// ... (L747-L770 생략: vacuum 플래그와 subxid 캐시 정리)

	/* Also advance global latestCompletedXid while holding the lock */
	MaintainLatestCompletedXid(latestXid);

	/* Same with xactCompletionCount  */
	TransamVariables->xactCompletionCount++;
}
```

## 동작 흐름

```text
 L2206  xip, subxip 배열이 아직 없으면 malloc
          크기는 GetMaxSnapshotXidCount, GetMaxSnapshotSubxidCount (잠금 밖에서 미리)
 L2231  LWLockAcquire(ProcArrayLock, LW_SHARED)
 L2233  GetSnapshotDataReuse         xactCompletionCount 가 같으면 RecentXmin, curcid (비었으면 MyProc->xmin) 만 갱신하고 끝
 L2239  latest_completed = TransamVariables->latestCompletedXid
 L2241  myxid = 내 xid 슬롯 (없으면 InvalidTransactionId)
 L2248  xmax = latestCompletedXid + 1           (TransactionIdAdvance)
 L2253  xmin = xmax                             시작값
 L2256  myxid 가 있고 xmin 보다 작으면 xmin = myxid
 L2259  takenDuringRecovery = RecoveryInProgress()

 L2273  for pgxactoff in 0 .. numProcs-1
 L2276    xid = other_xids[pgxactoff]            한 번만 읽는다 (UINT32_ACCESS_ONCE)
 L2285    xid 없음                    -> 건너뜀   (읽기 전용 트랜잭션은 xid 가 없다)
 L2293    내 슬롯                     -> 건너뜀   xip 에 넣지 않는다 (xmin 에는 L2256 에서 반영)
 L2309    !(xid < xmax)  즉 xid >= xmax -> 건너뜀   어차피 "진행 중"으로 판정된다
 L2317    logical decoding, lazy VACUUM 중 -> 건너뜀
 L2320    xid < xmin 이면 xmin = xid
 L2324    xip[count++] = xid
 L2341    subxid 캐시: 하나라도 overflowed 면 suboverflowed = true
          아니면 그 backend 의 subxids 를 subxip 뒤에 memcpy

 L2366  핫 스탠바이면 KnownAssignedXids 를 전부 subxip 에 넣는다 (xip 은 비운다)
 L2413  MyProc->xmin 이 비었으면 MyProc->xmin = TransactionXmin = xmin
 L2416  LWLockRelease
 L2418  GlobalVis* 경계 갱신 (잠금 밖)
 L2498  RecentXmin = xmin
 L2501  xmin, xmax, xcnt, subxcnt, suboverflowed, snapXactCompletionCount 를 적는다
 L2508  curcid = GetCurrentCommandId(false)
```

예를 하나 계산한다. 내 xid 가 102 이고, 가장 최근에 끝난 트랜잭션이 104 다. 105 와 106 은 xid 를 받았지만 아직 진행 중이다.

```text
 ProcArray 의 xid 슬롯 (pgxactoff 순서)          latestCompletedXid = 104

 off  xid   처리 (L2276-L2324)
 0    100   진행 중. xip 에 넣음, xmin = 100
 1    0     xid 없음 (읽기 전용). L2285 건너뜀
 2    102   나. L2293 건너뜀 (L2256 에서 xmin 후보로만)
 3    103   진행 중. xip 에 넣음
 4    105   진행 중. L2309 건너뜀 (105 >= xmax)
 5    106   진행 중. L2309 건너뜀

 xmax  = 104 + 1                   = 105
 xmin  = min(105, 102, 100, 103)   = 100
 xip[] = [100, 103]   xcnt = 2
 101, 104 는 이미 끝났다 (커밋이든 abort 든). 목록에 없으므로 "끝남"으로 읽힌다
```

이 스냅샷 하나가 XID 축을 세 구간으로 나눈다. [09] `XidInMVCCSnapshot` 이 이 그림을 그대로 코드로 옮긴 것이다.

```text
 스냅샷 {xmin 100, xmax 105, xip [100, 103]} 이 보는 XID 축

        99   | 100  101  102  103  104 | 105  106  107 ...
   ---------+--------------------------+-------------------
   xid < xmin        xmin <= xid < xmax        xid >= xmax
   전부 끝남         xip[] 에 있으면 진행 중    전부 진행 중
                     없으면 끝남                (스냅샷 뒤에 시작했거나
                                                 아직 안 끝났다고 친다)

   100 진행 중   101 끝남   102 나 (xip 에 없음, 호출자가 먼저 걸러야 한다)
   103 진행 중   104 끝남
```

"끝남"은 커밋과 abort 를 가리지 않는다. 어느 쪽인지는 [10] `TransactionIdDidCommit` 이 pg_xact 에서 읽는다.

```text
 트랜잭션이 끝날 때 바뀌는 값 (ProcArrayEndTransactionInternal, ProcArrayLock 배타)

 L743-L744  내 xid 슬롯 = InvalidTransactionId   다음 GetSnapshotData 의 xip 에서 빠진다
 L746       proc->xmin  = InvalidTransactionId
 L773       latestCompletedXid 를 latestXid 까지 올린다  -> 다음 스냅샷의 xmax 가 오른다
 L776       xactCompletionCount++                       -> 남들의 GetSnapshotDataReuse 가 실패한다

 GetSnapshotData 는 공유 모드로 읽으므로 이 갱신과 겹치지 않는다
   그래서 한 스냅샷 안의 xip 와 xmax 는 서로 어긋나지 않는다
```

## 결과가 쓰이는 곳

```text
 snapshot->xmin, xmax, xip[], subxip[], suboverflowed
      --> [09] XidInMVCCSnapshot 의 범위 검사와 배열 검색

 snapshot->curcid
      --> [08] HeapTupleSatisfiesMVCC 가 자기 트랜잭션 튜플의 cmin, cmax 와 비교한다

 MyProc->xmin (= TransactionXmin)
      --> 다른 backend 의 ComputeXidHorizons 가 읽어 vacuum 이 지울 수 있는 선을 정한다
      --> [10] TransactionIdDidCommit 이 subcommitted xid 를 pg_subtrans 로 따라갈지 정할 때 쓴다

 RecentXmin
      --> 이 값보다 작은 xid 는 진행 중이 아니라고 안다 (머리 주석 L2165-L2166)
```

## 다루지 않는 것

핫 스탠바이의 `KnownAssignedXidsGetAndSetXmin`, replication slot 의 xmin, `GlobalVis*` 경계(`GlobalVisTestFor` 계열이 prune 과 vacuum 에서 쓴다), xid 할당 `GetNewTransactionId` 와 subxid 캐시 채우기, 그룹 xid 정리(`ProcArrayGroupClearXid`)는 이 흐름의 곁가지라 요약만 했다.
