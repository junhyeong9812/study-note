# TransactionIdDidCommit

상위: [MVCC 가시성과 스냅샷](../README.md)

**스냅샷이 "끝났다"고 답한 xid 가 커밋인지 abort 인지를 pg_xact(clog)에서 읽는 함수다.** 한 칸짜리 캐시를 먼저 보고, 특수 xid 는 상수로 답하고, 나머지는 clog 페이지를 읽는다. 하위 트랜잭션이 "sub-committed" 로 남아 있으면 부모를 따라 올라간다.

## 위치

`access/transam` / `transam.c` L126-L172 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/transam.c#L126-L172))

## 실제 코드

```c
// transam.c L118-L172
/*
 * TransactionIdDidCommit
 *		True iff transaction associated with the identifier did commit.
 *
 * Note:
 *		Assumes transaction identifier is valid and exists in clog.
 */
bool							/* true if given transaction committed */
TransactionIdDidCommit(TransactionId transactionId)
{
	XidStatus	xidstatus;

	xidstatus = TransactionLogFetch(transactionId);

	/*
	 * If it's marked committed, it's committed.
	 */
	if (xidstatus == TRANSACTION_STATUS_COMMITTED)
		return true;

	/*
	 * If it's marked subcommitted, we have to check the parent recursively.
	 * However, if it's older than TransactionXmin, we can't look at
	 * pg_subtrans; instead assume that the parent crashed without cleaning up
	 * its children.
	 *
// ... (L144-L151 생략: prepared transaction 직후 pg_subtrans 공백에 대한 주석)
	if (xidstatus == TRANSACTION_STATUS_SUB_COMMITTED)
	{
		TransactionId parentXid;

		if (TransactionIdPrecedes(transactionId, TransactionXmin))
			return false;
		parentXid = SubTransGetParent(transactionId);
		if (!TransactionIdIsValid(parentXid))
		{
			elog(WARNING, "no pg_subtrans entry for subcommitted XID %u",
				 transactionId);
			return false;
		}
		return TransactionIdDidCommit(parentXid);
	}

	/*
	 * It's not committed.
	 */
	return false;
}
```

clog 를 읽기 전에 한 칸 캐시를 본다. 끝난 상태만 캐시한다.

`access/transam` / `transam.c` L48-L94 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/transam.c#L48-L94))

```c
// transam.c L48-L94
/*
 * TransactionLogFetch --- fetch commit status of specified transaction id
 */
static XidStatus
TransactionLogFetch(TransactionId transactionId)
{
	XidStatus	xidstatus;
	XLogRecPtr	xidlsn;

	/*
	 * Before going to the commit log manager, check our single item cache to
	 * see if we didn't just check the transaction status a moment ago.
	 */
	if (TransactionIdEquals(transactionId, cachedFetchXid))
		return cachedFetchXidStatus;

	/*
	 * Also, check to see if the transaction ID is a permanent one.
	 */
	if (!TransactionIdIsNormal(transactionId))
	{
		if (TransactionIdEquals(transactionId, BootstrapTransactionId))
			return TRANSACTION_STATUS_COMMITTED;
		if (TransactionIdEquals(transactionId, FrozenTransactionId))
			return TRANSACTION_STATUS_COMMITTED;
		return TRANSACTION_STATUS_ABORTED;
	}

	/*
	 * Get the transaction status.
	 */
	xidstatus = TransactionIdGetStatus(transactionId, &xidlsn);

	/*
	 * Cache it, but DO NOT cache status for unfinished or sub-committed
	 * transactions!  We only cache status that is guaranteed not to change.
	 */
	if (xidstatus != TRANSACTION_STATUS_IN_PROGRESS &&
		xidstatus != TRANSACTION_STATUS_SUB_COMMITTED)
	{
		cachedFetchXid = transactionId;
		cachedFetchXidStatus = xidstatus;
		cachedCommitLSN = xidlsn;
	}

	return xidstatus;
}
```

판정 함수들이 "스냅샷 먼저, pg_xact 나중" 순서를 지키는 이유는 파일 머리 주석에 있다.

`access/heap` / `heapam_visibility.c` L13-L35 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_visibility.c#L13-L35))

```c
// heapam_visibility.c L13-L35
 * NOTE: When using a non-MVCC snapshot, we must check
 * TransactionIdIsInProgress (which looks in the PGPROC array) before
 * TransactionIdDidCommit (which look in pg_xact).  Otherwise we have a race
 * condition: we might decide that a just-committed transaction crashed,
 * because none of the tests succeed.  xact.c is careful to record
 * commit/abort in pg_xact before it unsets MyProc->xid in the PGPROC array.
 * That fixes that problem, but it also means there is a window where
 * TransactionIdIsInProgress and TransactionIdDidCommit will both return true.
 * If we check only TransactionIdDidCommit, we could consider a tuple
 * committed when a later GetSnapshotData call will still think the
 * originating transaction is in progress, which leads to application-level
 * inconsistency.  The upshot is that we gotta check TransactionIdIsInProgress
 * first in all code paths, except for a few cases where we are looking at
 * subtransactions of our own main transaction and so there can't be any race
 * condition.
 *
 * We can't use TransactionIdDidAbort here because it won't treat transactions
 * that were in progress during a crash as aborted.  We determine that
 * transactions aborted/crashed through process of elimination instead.
 *
 * When using an MVCC snapshot, we rely on XidInMVCCSnapshot rather than
 * TransactionIdIsInProgress, but the logic is otherwise the same: do not
 * check pg_xact until after deciding that the xact is no longer in progress.
```

## 동작 흐름

```text
 TransactionIdDidCommit(xid)
 L130  TransactionLogFetch(xid)
         L61  xid == cachedFetchXid          -> 캐시된 상태
         L67  특수 xid
                Bootstrap(1), Frozen(2)      -> COMMITTED
                그 밖 (Invalid 0)            -> ABORTED
         L79  TransactionIdGetStatus         clog.c L735, pg_xact 의 2비트 상태
         L85  IN_PROGRESS, SUB_COMMITTED 가 아니면 캐시에 넣는다
 L135  COMMITTED                             -> true
 L152  SUB_COMMITTED
 L156    xid < TransactionXmin               -> false  (pg_subtrans 를 볼 수 없다, 부모가 crash 했다고 본다)
 L158    parent = SubTransGetParent(xid)
 L159    parent 없음                         -> WARNING, false
 L165    TransactionIdDidCommit(parent)      재귀
 L171  그 밖 (IN_PROGRESS, ABORTED)          -> false
```

[08] 은 이 함수가 `false` 를 주면 "abort 또는 crash"로 결론 낸다. `TransactionIdDidAbort` 를 쓰지 않는 이유는 머리 주석 L29-L31 에 있다. crash 때 진행 중이던 트랜잭션은 abort 로 기록되지 않기 때문이다.

```text
 pg_xact 상태와 이 함수, [08] 의 결론

 pg_xact        DidCommit   [08] 의 결론 (스냅샷은 이미 "끝남"이라 했다)
 COMMITTED      true        커밋 -> 커밋 힌트 (LSN 조건 통과 시)
 ABORTED        false       abort -> INVALID 힌트
 IN_PROGRESS    false       crash 로 남은 것 -> INVALID 힌트
 SUB_COMMITTED  parent      부모를 따라간 결과
```

커밋하는 쪽은 pg_xact 를 먼저 쓰고 ProcArray 에서 나중에 빠진다. 그 사이의 창에서 두 질문이 서로 다르게 답할 수 있어서 순서가 중요하다.

```text
 커밋하는 backend (access/transam/xact.c)          읽는 backend

 CommitTransaction
   L2365  RecordTransactionCommit
            L1502  XLogFlush(XactLastRecEnd)       동기 커밋 경로 (L1498 조건, 비동기면 L1510 이하)
            L1508  TransactionIdCommitTree         pg_xact = COMMITTED
                                                   <- 이 창에서 DidCommit 은 true
                                                      ProcArray 에는 아직 xid 가 있다
   L2389  ProcArrayEndTransaction                  ProcArray 에서 xid 가 빠진다
                                                   latestCompletedXid 전진

 창 안에서 찍힌 스냅샷은 이 xid 를 xip 에 넣었다 (진행 중)
 만약 DidCommit 을 먼저 보면 이 스냅샷의 독자가 커밋으로 판정해 버린다
 그래서 [08] 은 XidInMVCCSnapshot 이 false 일 때만 이 함수를 부른다 (머리 주석 L19-L24, L33-L35)
```

## 결과가 쓰이는 곳

```text
 bool
      --> [08] 의 L1065, L1113, L1132 에서 커밋 힌트를 적을지 abort 힌트를 적을지 정한다
 cachedFetchXid, cachedFetchXidStatus, cachedCommitLSN
      --> 같은 xid 를 연달아 물을 때 clog 를 다시 읽지 않는다
      --> cachedCommitLSN 은 SetHintBits 의 TransactionIdGetCommitLSN 이 쓴다
```

## 다루지 않는 것

clog 페이지를 SLRU 버퍼로 읽는 `TransactionIdGetStatus`(clog.c)와 그룹 상태 갱신, 상태를 쓰는 쪽 `TransactionIdCommitTree` 와 `TransactionIdAsyncCommitTree` 는 [커밋](../../commit/README.md)에서 다룬다. pg_subtrans 는 요약만 했다.
