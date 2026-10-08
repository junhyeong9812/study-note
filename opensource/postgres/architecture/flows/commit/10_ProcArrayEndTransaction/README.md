# ProcArrayEndTransaction

상위: [커밋](../README.md)

**"실행 중인 트랜잭션" 집합에서 자기를 뺀다.** XID 가 있으면 `ProcArrayLock` 을 배타로 잡고 `ProcGlobal->xids[]` 의 자기 칸과 `MyProc->xid`, `xmin` 을 지우고, `latestCompletedXid` 를 올리고, `xactCompletionCount` 를 하나 늘린다. 이 순간부터 새로 잡히는 스냅샷은 이 트랜잭션을 커밋된 것으로 본다. 배타 잠금이 필요한 이유는 스냅샷을 만드는 중에는 누구도 실행 중 집합에서 빠지지 못하게 하려는 것이고(transam README L246-L257), 잠금이 붐비면 리더 하나가 여러 backend 의 XID 를 한꺼번에 지우는 그룹 정리로 넘어간다. XID 가 없는 읽기 전용 트랜잭션은 남의 스냅샷에 영향이 없으므로 잠금 없이 `xmin` 만 지운다.

## 위치

`storage` / `ipc` / `procarray.c` L666-L723 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L666-L723))

## 실제 코드

`storage` / `ipc` / `procarray.c` L653-L723 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L653-L723))

```c
// procarray.c L653-L723
/*
 * ProcArrayEndTransaction -- mark a transaction as no longer running
 *
 * This is used interchangeably for commit and abort cases.  The transaction
 * commit/abort must already be reported to WAL and pg_xact.
 *
 * proc is currently always MyProc, but we pass it explicitly for flexibility.
 * latestXid is the latest Xid among the transaction's main XID and
 * subtransactions, or InvalidTransactionId if it has no XID.  (We must ask
 * the caller to pass latestXid, instead of computing it from the PGPROC's
 * contents, because the subxid information in the PGPROC might be
 * incomplete.)
 */
void
ProcArrayEndTransaction(PGPROC *proc, TransactionId latestXid)
{
	if (TransactionIdIsValid(latestXid))
	{
		/*
		 * We must lock ProcArrayLock while clearing our advertised XID, so
		 * that we do not exit the set of "running" transactions while someone
		 * else is taking a snapshot.  See discussion in
		 * src/backend/access/transam/README.
		 */
		Assert(TransactionIdIsValid(proc->xid));

		/*
		 * If we can immediately acquire ProcArrayLock, we clear our own XID
		 * and release the lock.  If not, use group XID clearing to improve
		 * efficiency.
		 */
		if (LWLockConditionalAcquire(ProcArrayLock, LW_EXCLUSIVE))
		{
			ProcArrayEndTransactionInternal(proc, latestXid);
			LWLockRelease(ProcArrayLock);
		}
		else
			ProcArrayGroupClearXid(proc, latestXid);
	}
	else
	{
		/*
		 * If we have no XID, we don't need to lock, since we won't affect
		 * anyone else's calculation of a snapshot.  We might change their
		 * estimate of global xmin, but that's OK.
		 */
		Assert(!TransactionIdIsValid(proc->xid));
		Assert(proc->subxidStatus.count == 0);
		Assert(!proc->subxidStatus.overflowed);

		proc->vxid.lxid = InvalidLocalTransactionId;
		proc->xmin = InvalidTransactionId;

		/* be sure this is cleared in abort */
		proc->delayChkptFlags = 0;

		proc->recoveryConflictPending = false;

		/* must be cleared with xid/xmin: */
		/* avoid unnecessarily dirtying shared cachelines */
		if (proc->statusFlags & PROC_VACUUM_STATE_MASK)
		{
			Assert(!LWLockHeldByMe(ProcArrayLock));
			LWLockAcquire(ProcArrayLock, LW_EXCLUSIVE);
			Assert(proc->statusFlags == ProcGlobal->statusFlags[proc->pgxactoff]);
			proc->statusFlags &= ~PROC_VACUUM_STATE_MASK;
			ProcGlobal->statusFlags[proc->pgxactoff] = proc->statusFlags;
			LWLockRelease(ProcArrayLock);
		}
	}
}
```

실제로 지우는 부분이다. 호출자가 `ProcArrayLock` 을 배타로 쥐고 있다.

`storage` / `ipc` / `procarray.c` L725-L777 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L725-L777))

```c
// procarray.c L725-L777
/*
 * Mark a write transaction as no longer running.
 *
 * We don't do any locking here; caller must handle that.
 */
static inline void
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

	/* be sure this is cleared in abort */
	proc->delayChkptFlags = 0;

	proc->recoveryConflictPending = false;

	/* must be cleared with xid/xmin: */
	/* avoid unnecessarily dirtying shared cachelines */
	if (proc->statusFlags & PROC_VACUUM_STATE_MASK)
	{
		proc->statusFlags &= ~PROC_VACUUM_STATE_MASK;
		ProcGlobal->statusFlags[proc->pgxactoff] = proc->statusFlags;
	}

	/* Clear the subtransaction-XID cache too while holding the lock */
	Assert(ProcGlobal->subxidStates[pgxactoff].count == proc->subxidStatus.count &&
		   ProcGlobal->subxidStates[pgxactoff].overflowed == proc->subxidStatus.overflowed);
	if (proc->subxidStatus.count > 0 || proc->subxidStatus.overflowed)
	{
		ProcGlobal->subxidStates[pgxactoff].count = 0;
		ProcGlobal->subxidStates[pgxactoff].overflowed = false;
		proc->subxidStatus.count = 0;
		proc->subxidStatus.overflowed = false;
	}

	/* Also advance global latestCompletedXid while holding the lock */
	MaintainLatestCompletedXid(latestXid);

	/* Same with xactCompletionCount  */
	TransamVariables->xactCompletionCount++;
}
```

`latestCompletedXid` 는 앞으로만 간다.

`storage` / `ipc` / `procarray.c` L962-L983 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L962-L983))

```c
// procarray.c L962-L983
/*
 * Update TransamVariables->latestCompletedXid to point to latestXid if
 * currently older.
 */
static void
MaintainLatestCompletedXid(TransactionId latestXid)
{
	FullTransactionId cur_latest = TransamVariables->latestCompletedXid;

	Assert(FullTransactionIdIsValid(cur_latest));
	Assert(!RecoveryInProgress());
	Assert(LWLockHeldByMe(ProcArrayLock));

	if (TransactionIdPrecedes(XidFromFullTransactionId(cur_latest), latestXid))
	{
		TransamVariables->latestCompletedXid =
			FullXidRelativeTo(cur_latest, latestXid);
	}

	Assert(IsBootstrapProcessingMode() ||
		   FullTransactionIdIsNormal(TransamVariables->latestCompletedXid));
}
```

## 동작 흐름

```text
 ProcArrayEndTransaction(MyProc, latestXid)
 L669  latestXid 가 유효 (XID 가 있던 트랜잭션)
         L684  LWLockConditionalAcquire(ProcArrayLock, EXCLUSIVE)
                 잡히면 L686 ProcArrayEndTransactionInternal, 해제
                 못 잡으면 L690 ProcArrayGroupClearXid      (리더가 대신 지운다)
 L692  latestXid 무효 (읽기 전용)
         L703  vxid.lxid = Invalid
         L704  xmin = Invalid                     잠금 없이 - 남의 스냅샷 내용은 안 바뀐다

 ProcArrayEndTransactionInternal  (ProcArrayLock EXCLUSIVE 아래)
 L743  ProcGlobal->xids[pgxactoff] = Invalid    GetSnapshotData 가 훑는 밀집 배열
 L744  proc->xid = Invalid
 L746  proc->xmin = Invalid                      이 backend 가 막던 vacuum 지평이 풀린다
 L764-L770  서브 XID 캐시 비우기
 L773  MaintainLatestCompletedXid(latestXid)    새 스냅샷의 xmax = 이 값 + 1
 L776  xactCompletionCount++                     캐시된 스냅샷을 다시 만들게 한다
```

같은 순간 두 backend 가 커밋하면 잠금을 넘겨주는 대신 한 번에 처리한다. B2 가 잠금을 못 잡았을 때의 그룹 정리다(L791-L896).

```text
 B1  L684 ProcArrayLock 을 잡고 Internal(B1) 진행 중
 B2  L684 실패 -> ProcArrayGroupClearXid
 B2  procArrayGroupFirst 에 자기를 CAS 로 push. 목록이 비어 있었으므로 B2 가 리더
 B2  LWLockAcquire(ProcArrayLock) 에서 기다린다
 B3  L684 실패 -> 목록에 push. 목록이 비어 있지 않았으므로 follower, 세마포어에서 잠든다
 B1  L687 해제
 B2  잠금 획득, 목록을 통째로 떼어 내고 B3, B2 순으로 Internal
 B2  잠금 해제 후 B3 를 PGSemaphoreUnlock 으로 깨운다
```

이 함수가 바꾼 값이 다음 스냅샷을 어떻게 바꾸는지는 숫자로 볼 수 있다. XID 100 과 102 가 실행 중이고 101 은 이미 커밋되어 `latestCompletedXid = 101` 일 때 100 이 커밋하는 경우다. 스냅샷은 `xmax = latestCompletedXid + 1` 로 잡고(procarray.c L2248-L2249), xmax 이상인 XID 는 xip 에 담지 않는다(L2309-L2310).

```text
                          before 100 commit        after 100 commit
 ProcGlobal->xids[]       {100, 102}               {102}
 latestCompletedXid       101                      101   (100 < 101 이라 그대로, L975)
 xactCompletionCount      N                        N + 1

 new snapshot
   xmax                   102                      102
   xip                    {100}                    {}
   XID 100                in xip -> 진행 중         xmax 미만, xip 에 없음 -> pg_xact 확인 -> 커밋
   XID 102                xmax 이상 -> 진행 중      xmax 이상 -> 진행 중
```

`latestCompletedXid` 가 그대로여도 xip 에서 빠지는 것만으로 보이게 된다. 반대로 가장 큰 XID 가 커밋하면 xmax 가 올라가서 보이게 된다.

## 결과가 쓰이는 곳

```text
 ProcGlobal->xids[], latestCompletedXid
      --> GetSnapshotData 의 xip, xmax ([MVCC 가시성 02](../../mvcc-visibility/02_GetSnapshotData/README.md))
 proc->xmin = Invalid
      --> ComputeXidHorizons 가 계산하는 OldestXmin 이 앞으로 갈 수 있다 -> vacuum 이 더 치운다
 xactCompletionCount
      --> GetSnapshotDataReuse (procarray.c L2095) 가 값이 같으면 이전 스냅샷을 그대로 쓴다
 PROC_VACUUM_STATE_MASK 해제
      --> vacuum_rel 이 세운 PROC_IN_VACUUM 이 이 시점에 내려간다
```

## 다루지 않는 것

2PC 의 `ProcArrayRemove`, 복구 중 `KnownAssignedXids` 정리(`ExpireTreeKnownAssignedTransactionIds`), 그룹 정리의 메모리 배리어와 세마포어 보정, abort 시의 같은 경로(이 함수는 커밋과 abort 에 공통이다)는 다루지 않았다.
