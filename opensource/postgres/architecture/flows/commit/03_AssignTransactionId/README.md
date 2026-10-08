# AssignTransactionId

상위: [커밋](../README.md)

**트랜잭션이 처음 무언가를 쓰려 할 때 진짜 XID 를 붙인다.** `heap_insert` 같은 쓰기 경로가 `GetCurrentTransactionId` 를 부르고, 아직 XID 가 없으면 이 함수가 `GetNewTransactionId` 로 번호를 받는다. 번호를 받는 순간 그 XID 는 `ProcGlobal->xids[]` 에 실려 다른 세션의 스냅샷에서 "진행 중"이 되고, 자기 XID 에 ExclusiveLock 을 걸어 둬서 이 행을 기다릴 사람이 잠들 자리를 만든다. 읽기만 하는 트랜잭션은 끝까지 여기에 오지 않는다.

## 위치

`access` / `transam` / `xact.c` L634-L785 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L634-L785))

## 실제 코드

`access` / `transam` / `xact.c` L634-L785 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L634-L785))

```c
// xact.c L634-L785
static void
AssignTransactionId(TransactionState s)
{
	bool		isSubXact = (s->parent != NULL);
	ResourceOwner currentOwner;
	bool		log_unknown_top = false;

	/* Assert that caller didn't screw up */
	Assert(!FullTransactionIdIsValid(s->fullTransactionId));
	Assert(s->state == TRANS_INPROGRESS);

	// ... (L645-L652 생략: 병렬 모드에서는 XID 를 줄 수 없다)

	// ... (L654-L681 생략: 부모 서브트랜잭션부터 XID 를 받는다 (부모 < 자식))

	// ... (L683-L695 생략: wal_level=logical 의 서브 XID 기록 준비)

	/*
	 * Generate a new FullTransactionId and record its xid in PGPROC and
	 * pg_subtrans.
	 *
	 * NB: we must make the subtrans entry BEFORE the Xid appears anywhere in
	 * shared storage other than PGPROC; because if there's no room for it in
	 * PGPROC, the subtrans entry is needed to ensure that other backends see
	 * the Xid as "running".  See GetNewTransactionId.
	 */
	s->fullTransactionId = GetNewTransactionId(isSubXact);
	if (!isSubXact)
		XactTopFullTransactionId = s->fullTransactionId;

	if (isSubXact)
		SubTransSetParent(XidFromFullTransactionId(s->fullTransactionId),
						  XidFromFullTransactionId(s->parent->fullTransactionId));

	/*
	 * If it's a top-level transaction, the predicate locking system needs to
	 * be told about it too.
	 */
	if (!isSubXact)
		RegisterPredicateLockingXid(XidFromFullTransactionId(s->fullTransactionId));

	/*
	 * Acquire lock on the transaction XID.  (We assume this cannot block.) We
	 * have to ensure that the lock is assigned to the transaction's own
	 * ResourceOwner.
	 */
	currentOwner = CurrentResourceOwner;
	CurrentResourceOwner = s->curTransactionOwner;

	XactLockTableInsert(XidFromFullTransactionId(s->fullTransactionId));

	CurrentResourceOwner = currentOwner;

	// ... (L733-L784 생략: 서브 XID 가 64 개 쌓이면 XLOG_XACT_ASSIGNMENT 레코드)
}
```

번호를 실제로 만드는 쪽이다. `XidGenLock` 을 쥔 채로 pg_xact 를 늘리고, 카운터를 올리고, **잠금을 놓기 전에** 자기 PGPROC 에 XID 를 싣는다.

`access` / `transam` / `varsup.c` L195-L282 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/varsup.c#L195-L282))

```c
// varsup.c L195-L282
	/*
	 * If we are allocating the first XID of a new page of the commit log,
	 * zero out that commit-log page before returning. We must do this while
	 * holding XidGenLock, else another xact could acquire and commit a later
	 * XID before we zero the page.  Fortunately, a page of the commit log
	 * holds 32K or more transactions, so we don't have to do this very often.
	 *
	 * Extend pg_subtrans and pg_commit_ts too.
	 */
	ExtendCLOG(xid);
	ExtendCommitTs(xid);
	ExtendSUBTRANS(xid);

	/*
	 * Now advance the nextXid counter.  This must not happen until after we
	 * have successfully completed ExtendCLOG() --- if that routine fails, we
	 * want the next incoming transaction to try it again.  We cannot assign
	 * more XIDs until there is CLOG space for them.
	 */
	FullTransactionIdAdvance(&TransamVariables->nextXid);

	// ... (L216-L249 생략: ProcArray 에 먼저 싣는 이유 (아래 그림))
	if (!isSubXact)
	{
		Assert(ProcGlobal->subxidStates[MyProc->pgxactoff].count == 0);
		Assert(!ProcGlobal->subxidStates[MyProc->pgxactoff].overflowed);
		Assert(MyProc->subxidStatus.count == 0);
		Assert(!MyProc->subxidStatus.overflowed);

		/* LWLockRelease acts as barrier */
		MyProc->xid = xid;
		ProcGlobal->xids[MyProc->pgxactoff] = xid;
	}
	// ... (L261-L277 생략: 서브트랜잭션이면 subxids 캐시에 싣는다)

	LWLockRelease(XidGenLock);

	return full_xid;
}
```

## 동작 흐름

```text
 heap_insert (heapam.c L2084)  xid = GetCurrentTransactionId()
   +-- s->fullTransactionId 가 없으면 (xact.c L458)
   +-- AssignTransactionId (L635)
         L706  GetNewTransactionId(isSubXact)                 varsup.c L77
                 L105   LWLockAcquire(XidGenLock)
                 L204   ExtendCLOG(xid)                         새 CLOG 페이지의 첫 XID 면 페이지를 0 으로
                 L206   ExtendSUBTRANS(xid)
                 L214   nextXid++
                 L258   MyProc->xid = xid
                 L259   ProcGlobal->xids[pgxactoff] = xid       이제 남의 스냅샷에서 진행 중
                 L279   LWLockRelease(XidGenLock)
         L708  XactTopFullTransactionId = ...
         L719  RegisterPredicateLockingXid                    (SSI)
         L729  XactLockTableInsert(xid)                        lmgr.c, 자기 XID 에 ExclusiveLock
```

`ExtendCLOG` 가 페이지를 만드는 간격은 CLOG 의 칸 크기에서 나온다. XID 하나가 2 비트이므로 8 KB 페이지 하나에 32768 개가 들어간다.

```text
 CLOG_XACTS_PER_PAGE = BLCKSZ * CLOG_XACTS_PER_BYTE = 8192 * 4 = 32768   (clog.c L63-L64)

 xid        TransactionIdToPage   byte in page   bit shift
 32767      0                     8191           6           페이지 0 의 마지막 칸
 32768      1                     0              0           ExtendCLOG 가 페이지 1 을 0 으로 채운다
 32769      1                     0              2
```

XID 를 ProcArray 에 싣는 일을 `XidGenLock` 을 놓기 전에 끝내는 이유는 주석에 있다(varsup.c L216-L220, `access/transam/README` L272-L284). 놓은 뒤에 실으면 아래 순서가 가능해진다.

```text
 A  XidGenLock 아래에서 xid = 100 을 받는다
 A  XidGenLock 해제 (아직 ProcGlobal->xids[] 에 안 실었다)
 B  xid = 101 을 받고 바로 커밋 -> latestCompletedXid = 101
 C  스냅샷: xmax = 102, xip 에 100 이 없다 -> 100 을 "완료"로 본다. 하지만 A 는 아직 진행 중
 A  xids[] = 100 (너무 늦다)
```

## 결과가 쓰이는 곳

```text
 ProcGlobal->xids[] = xid
      --> GetSnapshotData 가 xip 에 담는다 ([MVCC 가시성 02](../../mvcc-visibility/02_GetSnapshotData/README.md))
      --> [10] ProcArrayEndTransaction 이 커밋 때 지운다
 s->fullTransactionId
      --> 행 헤더의 xmin / xmax
      --> [06] RecordTransactionCommit 의 markXidCommitted (XID 가 있어야 commit 레코드를 쓴다)
 자기 XID 의 ExclusiveLock
      --> 행 충돌 시 XactLockTableWait 가 이 잠금에 ShareLock 으로 줄을 선다
      --> [05] 의 ResourceOwnerRelease(LOCKS) 가 풀면서 대기자를 깨운다
```

## 다루지 않는 것

서브트랜잭션 XID 의 부모 연결(`SubTransSetParent`, pg_subtrans), standby 를 위한 `XLOG_XACT_ASSIGNMENT` 레코드, XID wraparound 경고와 거부(`GetNewTransactionId` 의 `xidVacLimit` 검사)는 다루지 않았다.
