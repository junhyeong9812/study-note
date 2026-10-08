# XidInMVCCSnapshot

상위: [MVCC 가시성과 스냅샷](../README.md)

**"이 xid 가 내 스냅샷 기준으로 아직 진행 중인가"에 답하는 함수다.** `xmin` 보다 작으면 바로 `false`, `xmax` 이상이면 바로 `true`, 그 사이면 `subxip[]` 와 `xip[]` 를 선형 검색한다. 자기 트랜잭션의 xid 는 스냅샷에 들어 있지 않으므로 이 함수는 그것을 진행 중이라고 답하지 않는다. 호출자가 먼저 `TransactionIdIsCurrentTransactionId` 로 걸러야 한다.

## 위치

`utils/time` / `snapmgr.c` L1870-L1964 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/time/snapmgr.c#L1870-L1964))

## 실제 코드

```c
// snapmgr.c L1859-L1964
/*
 * XidInMVCCSnapshot
 *		Is the given XID still-in-progress according to the snapshot?
 *
 * Note: GetSnapshotData never stores either top xid or subxids of our own
 * backend into a snapshot, so these xids will not be reported as "running"
 * by this function.  This is OK for current uses, because we always check
 * TransactionIdIsCurrentTransactionId first, except when it's known the
 * XID could not be ours anyway.
 */
bool
XidInMVCCSnapshot(TransactionId xid, Snapshot snapshot)
{
	/*
	 * Make a quick range check to eliminate most XIDs without looking at the
	 * xip arrays.  Note that this is OK even if we convert a subxact XID to
	 * its parent below, because a subxact with XID < xmin has surely also got
	 * a parent with XID < xmin, while one with XID >= xmax must belong to a
	 * parent that was not yet committed at the time of this snapshot.
	 */

	/* Any xid < xmin is not in-progress */
	if (TransactionIdPrecedes(xid, snapshot->xmin))
		return false;
	/* Any xid >= xmax is in-progress */
	if (TransactionIdFollowsOrEquals(xid, snapshot->xmax))
		return true;

	/*
	 * Snapshot information is stored slightly differently in snapshots taken
	 * during recovery.
	 */
	if (!snapshot->takenDuringRecovery)
	{
		/*
		 * If the snapshot contains full subxact data, the fastest way to
		 * check things is just to compare the given XID against both subxact
		 * XIDs and top-level XIDs.  If the snapshot overflowed, we have to
		 * use pg_subtrans to convert a subxact XID to its parent XID, but
		 * then we need only look at top-level XIDs not subxacts.
		 */
		if (!snapshot->suboverflowed)
		{
			/* we have full data, so search subxip */
			if (pg_lfind32(xid, snapshot->subxip, snapshot->subxcnt))
				return true;

			/* not there, fall through to search xip[] */
		}
		else
		{
			/*
			 * Snapshot overflowed, so convert xid to top-level.  This is safe
			 * because we eliminated too-old XIDs above.
			 */
			xid = SubTransGetTopmostTransaction(xid);

			/*
			 * If xid was indeed a subxact, we might now have an xid < xmin,
			 * so recheck to avoid an array scan.  No point in rechecking
			 * xmax.
			 */
			if (TransactionIdPrecedes(xid, snapshot->xmin))
				return false;
		}

		if (pg_lfind32(xid, snapshot->xip, snapshot->xcnt))
			return true;
	}
	else
	{
		/*
		 * In recovery we store all xids in the subxip array because it is by
		 * far the bigger array, and we mostly don't know which xids are
		 * top-level and which are subxacts. The xip array is empty.
		 *
		 * We start by searching subtrans, if we overflowed.
		 */
		if (snapshot->suboverflowed)
		{
			/*
			 * Snapshot overflowed, so convert xid to top-level.  This is safe
			 * because we eliminated too-old XIDs above.
			 */
			xid = SubTransGetTopmostTransaction(xid);

			/*
			 * If xid was indeed a subxact, we might now have an xid < xmin,
			 * so recheck to avoid an array scan.  No point in rechecking
			 * xmax.
			 */
			if (TransactionIdPrecedes(xid, snapshot->xmin))
				return false;
		}

		/*
		 * We now have either a top-level xid higher than xmin or an
		 * indeterminate xid. We don't know whether it's top level or subxact
		 * but it doesn't matter. If it's present, the xid is visible.
		 */
		if (pg_lfind32(xid, snapshot->subxip, snapshot->subxcnt))
			return true;
	}

	return false;
}
```

두 범위 검사의 비교 함수다. 32비트 xid 는 감싸 돌기 때문에 정상 xid 끼리는 차이를 `int32` 로 보고 부호로 앞뒤를 정한다.

`access/transam` / `transam.c` L276-L338 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/transam.c#L276-L338))

```c
// transam.c L276-L293
/*
 * TransactionIdPrecedes --- is id1 logically < id2?
 */
bool
TransactionIdPrecedes(TransactionId id1, TransactionId id2)
{
	/*
	 * If either ID is a permanent XID then we can just do unsigned
	 * comparison.  If both are normal, do a modulo-2^32 comparison.
	 */
	int32		diff;

	if (!TransactionIdIsNormal(id1) || !TransactionIdIsNormal(id2))
		return (id1 < id2);

	diff = (int32) (id1 - id2);
	return (diff < 0);
}
```

```c
// transam.c L325-L338
/*
 * TransactionIdFollowsOrEquals --- is id1 logically >= id2?
 */
bool
TransactionIdFollowsOrEquals(TransactionId id1, TransactionId id2)
{
	int32		diff;

	if (!TransactionIdIsNormal(id1) || !TransactionIdIsNormal(id2))
		return (id1 >= id2);

	diff = (int32) (id1 - id2);
	return (diff >= 0);
}
```

`SnapshotData` 의 필드 주석이 같은 경계를 적어 둔다.

`src/include/utils` / `snapshot.h` L148-L183 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/utils/snapshot.h#L148-L183))

```c
// snapshot.h L148-L183
	 * An MVCC snapshot can never see the effects of XIDs >= xmax. It can see
	 * the effects of all older XIDs except those listed in the snapshot. xmin
	 * is stored as an optimization to avoid needing to search the XID arrays
	 * for most tuples.
	 */
	TransactionId xmin;			/* all XID < xmin are visible to me */
	TransactionId xmax;			/* all XID >= xmax are invisible to me */

	/*
	 * For normal MVCC snapshot this contains the all xact IDs that are in
	 * progress, unless the snapshot was taken during recovery in which case
	 * it's empty. For historic MVCC snapshots, the meaning is inverted, i.e.
	 * it contains *committed* transactions between xmin and xmax.
	 *
	 * note: all ids in xip[] satisfy xmin <= xip[i] < xmax
	 */
	TransactionId *xip;
	uint32		xcnt;			/* # of xact ids in xip[] */

	/*
	 * For non-historic MVCC snapshots, this contains subxact IDs that are in
	 * progress (and other transactions that are in progress if taken during
	 * recovery). For historic snapshot it contains *all* xids assigned to the
	 * replayed transaction, including the toplevel xid.
	 *
	 * note: all ids in subxip[] are >= xmin, but we don't bother filtering
	 * out any that are >= xmax
	 */
	TransactionId *subxip;
	int32		subxcnt;		/* # of xact ids in subxip[] */
	bool		suboverflowed;	/* has the subxip array overflowed? */

	bool		takenDuringRecovery;	/* recovery-shaped snapshot? */
	bool		copied;			/* false if it's a static snapshot */

	CommandId	curcid;			/* in my xact, CID < curcid are visible */
```

## 동작 흐름

```text
 L1881  TransactionIdPrecedes(xid, snapshot->xmin)        xid <  xmin  -> false (끝남)
 L1884  TransactionIdFollowsOrEquals(xid, snapshot->xmax) xid >= xmax  -> true  (진행 중)
        여기부터 xmin <= xid < xmax
 L1891  일반 스냅샷 (복구 중에 찍지 않음)
 L1900    suboverflowed 아님
 L1903      subxip[] 에 있으면                                       -> true
 L1908    suboverflowed
 L1914      xid = SubTransGetTopmostTransaction(xid)   pg_subtrans 로 최상위 xid 로 바꾼다
 L1921      바꾼 xid < xmin 이면                                     -> false
 L1925    xip[] 에 있으면                                            -> true
 L1928  복구 중 스냅샷 (xip 은 비어 있고 전부 subxip 에)
 L1937    suboverflowed 면 최상위로 바꾸고 xmin 재검사
 L1959    subxip[] 에 있으면                                         -> true
 L1963  return false                                                 (끝남)
```

경계값은 이렇다. 두 범위 검사가 한쪽은 `<`, 한쪽은 `>=` 라서 `xmin` 자신은 배열 검색으로, `xmax` 자신은 진행 중으로 떨어진다.

```text
 스냅샷 {xmin 100, xmax 105, xip [100, 103], subxip [], suboverflowed false}

 xid   L1881 xid<100   L1884 xid>=105   xip 검색   반환   뜻
 99    Y               -                -          false  끝남
 100   N               N                hit        true   진행 중 (xid == xmin)
 101   N               N                miss       false  끝남
 102   N               N                miss       false  끝남으로 답한다 (나. 호출자가 먼저 거른다)
 103   N               N                hit        true   진행 중
 104   N               N                miss       false  끝남 (xid == xmax - 1)
 105   N               Y                -          true   진행 중 (xid == xmax)
 106   N               Y                -          true   진행 중
```

비교는 감싸 도는 32비트 공간에서 한다. 정상 xid 두 개는 차이가 2^31 미만일 때만 앞뒤가 의미 있다.

```text
 TransactionIdPrecedes(id1, id2)   transam.c L280

 둘 중 하나라도 특수 xid (0 Invalid, 1 Bootstrap, 2 Frozen)   -> id1 < id2  (부호 없는 비교)
 둘 다 정상 (>= 3)                                             -> (int32)(id1 - id2) < 0

 예  id1 = 4294967290, id2 = 5
     id1 - id2 = 4294967285 -> int32 로 -11  -> 4294967290 이 5 보다 "앞"
     감싸 돈 직후의 5 가 더 새 xid 로 읽힌다
```

subxid 가 넘친 스냅샷은 하위 트랜잭션 xid 를 부모로 바꿔서 본다. 그래서 넘친 뒤에는 이 함수가 pg_subtrans 를 읽는다.

```text
 다른 스냅샷 {xmin 100, xmax 130, xip [110]} 에서 하위 트랜잭션 xid 120 을 판정, 부모는 110 (진행 중)

 suboverflowed = false   subxip 에 120 이 있다 -> L1903 true          subxip 검색 한 번
 suboverflowed = true    L1914 SubTransGetTopmostTransaction(120) = 110
                         L1921 110 >= xmin, L1925 xip 에 110 -> true   pg_subtrans 읽기 한 번 + 검색
 넘침 판정은 [02] GetSnapshotData L2344 에서 어느 backend 하나라도 캐시가 넘쳤는지로 정한다
```

## 결과가 쓰이는 곳

```text
 bool
      --> [08] HeapTupleSatisfiesMVCC 의 L1063, L1079, L1111, L1129, L1147
          true 면 그 트랜잭션의 실제 상태(pg_xact)를 보지 않고 "진행 중"으로 처리한다
          false 일 때만 [10] TransactionIdDidCommit 으로 넘어간다
```

## 다루지 않는 것

pg_subtrans 의 저장 구조(`SubTransGetTopmostTransaction`, `access/transam/subtrans.c`), 배열 검색 `pg_lfind32` 의 SIMD 구현, historic MVCC 스냅샷에서 `xip` 의 뜻이 뒤집히는 경우(snapshot.h L158-L160)는 요약만 했다.
