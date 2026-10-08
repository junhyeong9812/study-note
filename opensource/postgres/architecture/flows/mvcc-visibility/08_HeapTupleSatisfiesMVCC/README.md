# HeapTupleSatisfiesMVCC

상위: [MVCC 가시성과 스냅샷](../README.md)

**튜플 하나가 이 스냅샷에 보이는지를 정하는 규칙 전체다.** 앞 절반은 "넣은 쪽(`t_xmin`)이 나에게 커밋된 것으로 보이는가", 뒤 절반은 "지운 쪽(`t_xmax`)이 나에게 커밋된 것으로 보이는가"를 묻는다. 넣은 쪽은 커밋으로 보이고 지운 쪽은 커밋으로 보이지 않을 때만 `true` 다. 판정 중에 실제 커밋 여부를 pg_xact 에서 확인했으면 그 결과를 힌트 비트로 튜플에 적는다.

## 위치

`access/heap` / `heapam_visibility.c` L960-L1154 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_visibility.c#L960-L1154))

## 실제 코드

머리 주석은 "스냅샷 기준으로 아직 진행 중이면 힌트 비트를 적지 않는다"고 못 박는다. 이유도 적혀 있다.

```c
// heapam_visibility.c L937-L976
/*
 * HeapTupleSatisfiesMVCC
 *		True iff heap tuple is valid for the given MVCC snapshot.
 *
 * See SNAPSHOT_MVCC's definition for the intended behaviour.
 *
 * Notice that here, we will not update the tuple status hint bits if the
 * inserting/deleting transaction is still running according to our snapshot,
 * even if in reality it's committed or aborted by now.  This is intentional.
 * Checking the true transaction state would require access to high-traffic
 * shared data structures, creating contention we'd rather do without, and it
 * would not change the result of our visibility check anyway.  The hint bits
 * will be updated by the first visitor that has a snapshot new enough to see
 * the inserting/deleting transaction as done.  In the meantime, the cost of
 * leaving the hint bits unset is basically that each HeapTupleSatisfiesMVCC
 * call will need to run TransactionIdIsCurrentTransactionId in addition to
 * XidInMVCCSnapshot (but it would have to do the latter anyway).  In the old
 * coding where we tried to set the hint bits as soon as possible, we instead
 * did TransactionIdIsInProgress in each call --- to no avail, as long as the
 * inserting/deleting transaction was still running --- which was more cycles
 * and more contention on ProcArrayLock.
 */
static bool
HeapTupleSatisfiesMVCC(HeapTuple htup, Snapshot snapshot,
					   Buffer buffer)
{
	HeapTupleHeader tuple = htup->t_data;

	/*
	 * Assert that the caller has registered the snapshot.  This function
	 * doesn't care about the registration as such, but in general you
	 * shouldn't try to use a snapshot without registration because it might
	 * get invalidated while it's still in use, and this is a convenient place
	 * to check for that.
	 */
	Assert(snapshot->regd_count > 0 || snapshot->active_count > 0);

	Assert(ItemPointerIsValid(&htup->t_self));
	Assert(htup->t_tableOid != InvalidOid);

```

앞 절반, `t_xmin` 쪽이다. pre-9.0 `VACUUM FULL` 이 남긴 `HEAP_MOVED_*` 처리는 줄였다.

```c
// heapam_visibility.c L977-L1084
	if (!HeapTupleHeaderXminCommitted(tuple))
	{
		if (HeapTupleHeaderXminInvalid(tuple))
			return false;

// ... (L982-L1020 생략: HEAP_MOVED_OFF, HEAP_MOVED_IN (pre-9.0 binary upgrade 전용))
		else if (TransactionIdIsCurrentTransactionId(HeapTupleHeaderGetRawXmin(tuple)))
		{
			if (HeapTupleHeaderGetCmin(tuple) >= snapshot->curcid)
				return false;	/* inserted after scan started */

			if (tuple->t_infomask & HEAP_XMAX_INVALID)	/* xid invalid */
				return true;

			if (HEAP_XMAX_IS_LOCKED_ONLY(tuple->t_infomask))	/* not deleter */
				return true;

			if (tuple->t_infomask & HEAP_XMAX_IS_MULTI)
			{
				TransactionId xmax;

				xmax = HeapTupleGetUpdateXid(tuple);

				/* not LOCKED_ONLY, so it has to have an xmax */
				Assert(TransactionIdIsValid(xmax));

				/* updating subtransaction must have aborted */
				if (!TransactionIdIsCurrentTransactionId(xmax))
					return true;
				else if (HeapTupleHeaderGetCmax(tuple) >= snapshot->curcid)
					return true;	/* updated after scan started */
				else
					return false;	/* updated before scan started */
			}

			if (!TransactionIdIsCurrentTransactionId(HeapTupleHeaderGetRawXmax(tuple)))
			{
				/* deleting subtransaction must have aborted */
				SetHintBits(tuple, buffer, HEAP_XMAX_INVALID,
							InvalidTransactionId);
				return true;
			}

			if (HeapTupleHeaderGetCmax(tuple) >= snapshot->curcid)
				return true;	/* deleted after scan started */
			else
				return false;	/* deleted before scan started */
		}
		else if (XidInMVCCSnapshot(HeapTupleHeaderGetRawXmin(tuple), snapshot))
			return false;
		else if (TransactionIdDidCommit(HeapTupleHeaderGetRawXmin(tuple)))
			SetHintBits(tuple, buffer, HEAP_XMIN_COMMITTED,
						HeapTupleHeaderGetRawXmin(tuple));
		else
		{
			/* it must have aborted or crashed */
			SetHintBits(tuple, buffer, HEAP_XMIN_INVALID,
						InvalidTransactionId);
			return false;
		}
	}
	else
	{
		/* xmin is committed, but maybe not according to our snapshot */
		if (!HeapTupleHeaderXminFrozen(tuple) &&
			XidInMVCCSnapshot(HeapTupleHeaderGetRawXmin(tuple), snapshot))
			return false;		/* treat as still in progress */
	}

	/* by here, the inserting transaction has committed */
```

뒤 절반, `t_xmax` 쪽이다.

```c
// heapam_visibility.c L1086-L1154
	if (tuple->t_infomask & HEAP_XMAX_INVALID)	/* xid invalid or aborted */
		return true;

	if (HEAP_XMAX_IS_LOCKED_ONLY(tuple->t_infomask))
		return true;

	if (tuple->t_infomask & HEAP_XMAX_IS_MULTI)
	{
		TransactionId xmax;

		/* already checked above */
		Assert(!HEAP_XMAX_IS_LOCKED_ONLY(tuple->t_infomask));

		xmax = HeapTupleGetUpdateXid(tuple);

		/* not LOCKED_ONLY, so it has to have an xmax */
		Assert(TransactionIdIsValid(xmax));

		if (TransactionIdIsCurrentTransactionId(xmax))
		{
			if (HeapTupleHeaderGetCmax(tuple) >= snapshot->curcid)
				return true;	/* deleted after scan started */
			else
				return false;	/* deleted before scan started */
		}
		if (XidInMVCCSnapshot(xmax, snapshot))
			return true;
		if (TransactionIdDidCommit(xmax))
			return false;		/* updating transaction committed */
		/* it must have aborted or crashed */
		return true;
	}

	if (!(tuple->t_infomask & HEAP_XMAX_COMMITTED))
	{
		if (TransactionIdIsCurrentTransactionId(HeapTupleHeaderGetRawXmax(tuple)))
		{
			if (HeapTupleHeaderGetCmax(tuple) >= snapshot->curcid)
				return true;	/* deleted after scan started */
			else
				return false;	/* deleted before scan started */
		}

		if (XidInMVCCSnapshot(HeapTupleHeaderGetRawXmax(tuple), snapshot))
			return true;

		if (!TransactionIdDidCommit(HeapTupleHeaderGetRawXmax(tuple)))
		{
			/* it must have aborted or crashed */
			SetHintBits(tuple, buffer, HEAP_XMAX_INVALID,
						InvalidTransactionId);
			return true;
		}

		/* xmax transaction committed */
		SetHintBits(tuple, buffer, HEAP_XMAX_COMMITTED,
					HeapTupleHeaderGetRawXmax(tuple));
	}
	else
	{
		/* xmax is committed, but maybe not according to our snapshot */
		if (XidInMVCCSnapshot(HeapTupleHeaderGetRawXmax(tuple), snapshot))
			return true;		/* treat as still in progress */
	}

	/* xmax transaction committed */

	return false;
}
```

힌트 비트를 적는 함수다. 커밋 힌트만 조건이 붙는다.

`access/heap` / `heapam_visibility.c` L82-L132 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_visibility.c#L82-L132))

```c
// heapam_visibility.c L82-L132
/*
 * SetHintBits()
 *
 * Set commit/abort hint bits on a tuple, if appropriate at this time.
 *
 * It is only safe to set a transaction-committed hint bit if we know the
 * transaction's commit record is guaranteed to be flushed to disk before the
 * buffer, or if the table is temporary or unlogged and will be obliterated by
 * a crash anyway.  We cannot change the LSN of the page here, because we may
 * hold only a share lock on the buffer, so we can only use the LSN to
 * interlock this if the buffer's LSN already is newer than the commit LSN;
 * otherwise we have to just refrain from setting the hint bit until some
 * future re-examination of the tuple.
 *
 * We can always set hint bits when marking a transaction aborted.  (Some
 * code in heapam.c relies on that!)
 *
// ... (L99-L106 생략: HEAP_MOVED 정리 주석)
 * Normal commits may be asynchronous, so for those we need to get the LSN
 * of the transaction and then check whether this is flushed.
 *
 * The caller should pass xid as the XID of the transaction to check, or
 * InvalidTransactionId if no check is needed.
 */
static inline void
SetHintBits(HeapTupleHeader tuple, Buffer buffer,
			uint16 infomask, TransactionId xid)
{
	if (TransactionIdIsValid(xid))
	{
		/* NB: xid must be known committed here! */
		XLogRecPtr	commitLSN = TransactionIdGetCommitLSN(xid);

		if (BufferIsPermanent(buffer) && XLogNeedsFlush(commitLSN) &&
			BufferGetLSNAtomic(buffer) < commitLSN)
		{
			/* not flushed and no LSN interlock, so don't set hint */
			return;
		}
	}

	tuple->t_infomask |= infomask;
	MarkBufferDirtyHint(buffer, true);
}
```

튜플 헤더에서 이 함수가 읽는 필드다.

`src/include/access` / `htup_details.h` L122-L209 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L122-L209))

```c
// htup_details.h L122-L132
typedef struct HeapTupleFields
{
	TransactionId t_xmin;		/* inserting xact ID */
	TransactionId t_xmax;		/* deleting or locking xact ID */

	union
	{
		CommandId	t_cid;		/* inserting or deleting command ID, or both */
		TransactionId t_xvac;	/* old-style VACUUM FULL xact ID */
	}			t_field3;
} HeapTupleFields;
```

```c
// htup_details.h L153-L181
struct HeapTupleHeaderData
{
	union
	{
		HeapTupleFields t_heap;
		DatumTupleFields t_datum;
	}			t_choice;

	ItemPointerData t_ctid;		/* current TID of this or newer tuple (or a
								 * speculative insertion token) */

	/* Fields below here must match MinimalTupleData! */

#define FIELDNO_HEAPTUPLEHEADERDATA_INFOMASK2 2
	uint16		t_infomask2;	/* number of attributes + various flags */

#define FIELDNO_HEAPTUPLEHEADERDATA_INFOMASK 3
	uint16		t_infomask;		/* various flag bits, see below */

#define FIELDNO_HEAPTUPLEHEADERDATA_HOFF 4
	uint8		t_hoff;			/* sizeof header incl. bitmap, padding */

	/* ^ - 23 bytes - ^ */

#define FIELDNO_HEAPTUPLEHEADERDATA_BITS 5
	bits8		t_bits[FLEXIBLE_ARRAY_MEMBER];	/* bitmap of NULLs */

	/* MORE DATA FOLLOWS AT END OF STRUCT */
};
```

```c
// htup_details.h L204-L209
#define HEAP_XMIN_COMMITTED		0x0100	/* t_xmin committed */
#define HEAP_XMIN_INVALID		0x0200	/* t_xmin invalid/aborted */
#define HEAP_XMIN_FROZEN		(HEAP_XMIN_COMMITTED|HEAP_XMIN_INVALID)
#define HEAP_XMAX_COMMITTED		0x0400	/* t_xmax committed */
#define HEAP_XMAX_INVALID		0x0800	/* t_xmax invalid/aborted */
#define HEAP_XMAX_IS_MULTI		0x1000	/* t_xmax is a MultiXactId */
```

```c
// htup_details.h L341-L358
static inline bool
HeapTupleHeaderXminCommitted(const HeapTupleHeaderData *tup)
{
	return (tup->t_infomask & HEAP_XMIN_COMMITTED) != 0;
}

static inline bool
HeapTupleHeaderXminInvalid(const HeapTupleHeaderData *tup) \
{
	return (tup->t_infomask & (HEAP_XMIN_COMMITTED | HEAP_XMIN_INVALID)) ==
		HEAP_XMIN_INVALID;
}

static inline bool
HeapTupleHeaderXminFrozen(const HeapTupleHeaderData *tup)
{
	return (tup->t_infomask & HEAP_XMIN_FROZEN) == HEAP_XMIN_FROZEN;
}
```

새 튜플의 헤더는 `heap_prepare_insert` 가 이렇게 채운다. 처음에는 xmax 무효 힌트만 서 있다.

`access/heap` / `heapam.c` L2312-L2320 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2312-L2320))

```c
// heapam.c L2312-L2320
	tup->t_data->t_infomask &= ~(HEAP_XACT_MASK);
	tup->t_data->t_infomask2 &= ~(HEAP2_XACT_MASK);
	tup->t_data->t_infomask |= HEAP_XMAX_INVALID;
	HeapTupleHeaderSetXmin(tup->t_data, xid);
	if (options & HEAP_INSERT_FROZEN)
		HeapTupleHeaderSetXminFrozen(tup->t_data);

	HeapTupleHeaderSetCmin(tup->t_data, cid);
	HeapTupleHeaderSetXmax(tup->t_data, 0); /* for cleanliness */
```

## 동작 흐름

헤더 23바이트 중 이 판정이 보는 자리는 셋이다. `t_xmin`, `t_xmax`, 그리고 `t_infomask` 의 힌트 비트 네 개다. 자기 트랜잭션 튜플이면 `t_cid` 도 본다.

```text
 HeapTupleHeaderData (htup_details.h L153, "23 bytes" L175)

 오프셋  크기  필드                         이 판정에서
 0       4     t_xmin                       넣은 트랜잭션
 4       4     t_xmax                       지운(또는 잠근) 트랜잭션, 0 이면 없음
 8       4     t_cid  (t_xvac 와 공용)       자기 트랜잭션일 때 cmin / cmax (combo CID 일 수 있음)
 12      6     t_ctid                       (이 판정에서는 안 봄)
 18      2     t_infomask2
 20      2     t_infomask                   힌트 비트 0x0100 0x0200 0x0400 0x0800
 22      1     t_hoff
```

```text
 t_infomask 의 힌트 비트 (L204-L209)

 xmin 쪽  COMMITTED 0x0100  INVALID 0x0200   뜻
          0                 0                모름 -> 스냅샷과 pg_xact 로 판정해야 한다
          1                 0                커밋됨
          0                 1                abort 됨 (HeapTupleHeaderXminInvalid)
          1                 1                FROZEN, 누구에게나 커밋 (HEAP_XMIN_FROZEN)

 xmax 쪽  COMMITTED 0x0400  INVALID 0x0800
          0                 1                지운 쪽 없음 또는 abort  (insert 직후 상태, heapam.c L2314)
          0                 0                모름
          1                 0                지운 트랜잭션 커밋됨

 주의  HeapTupleHeaderXminCommitted 는 0x0100 만 본다 (L344). FROZEN 도 "커밋"으로 들어간다
```

판정 순서 전체다. 왼쪽 줄 번호가 분기, 오른쪽이 결과다. 줄마다 "스냅샷으로 먼저 보고, 끝났다고 나올 때만 pg_xact 를 본다"는 순서를 지킨다.

```text
 [xmin 단계]
 L977  XMIN_COMMITTED 비트 없음
 L979    XminInvalid (abort 힌트)                                    -> false
 L1021   xmin == 내 트랜잭션 (TransactionIdIsCurrentTransactionId)
 L1023     cmin >= curcid                                             -> false  이번 스캔 시작 뒤 삽입
 L1026     XMAX_INVALID                                               -> true
 L1029     xmax 가 잠금 전용                                          -> true
 L1032     xmax 가 MultiXact  -> 갱신 xid 가 내 것이 아니면          -> true
                                 cmax >= curcid                       -> true   / 아니면 false
 L1050     raw xmax 가 내 트랜잭션이 아님 (지운 하위 트랜잭션 abort)  -> XMAX_INVALID 힌트, true
 L1058     cmax >= curcid                                             -> true   스캔 시작 뒤 삭제
           그 밖                                                      -> false  스캔 시작 전 삭제
 L1063   XidInMVCCSnapshot(xmin)                                      -> false  나에게는 아직 진행 중
 L1065   TransactionIdDidCommit(xmin)                                 -> XMIN_COMMITTED 힌트, 계속
 L1068   그 밖 (abort 또는 crash)                                     -> XMIN_INVALID 힌트, false
 L1076 XMIN_COMMITTED 비트 있음
 L1079   FROZEN 이 아니고 XidInMVCCSnapshot(xmin)                     -> false  커밋됐지만 내 스냅샷 뒤

 [xmax 단계]  여기 오면 넣은 쪽은 나에게 커밋으로 보인다
 L1086 XMAX_INVALID                                                   -> true
 L1089 잠금 전용 xmax                                                 -> true
 L1092 MultiXact   갱신 xid 가 내 것    cmax >= curcid ? true : false
                   XidInMVCCSnapshot    -> true
                   DidCommit            -> false
                   그 밖                -> true   (힌트 없음)
 L1119 XMAX_COMMITTED 비트 없음
 L1121   xmax == 내 트랜잭션           cmax >= curcid ? true : false
 L1129   XidInMVCCSnapshot(xmax)                                      -> true   지우는 쪽이 아직 진행 중
 L1132   !DidCommit(xmax)                                             -> XMAX_INVALID 힌트, true
 L1141   커밋                                                         -> XMAX_COMMITTED 힌트, 아래로
 L1144 XMAX_COMMITTED 비트 있음
 L1147   XidInMVCCSnapshot(xmax)                                      -> true   커밋됐지만 내 스냅샷 뒤
 L1153 return false                                                            지운 쪽이 나에게 커밋됨
```

`curcid` 비교는 모두 `>=` 다. 같은 명령 안에서 넣은 행은 그 명령의 스캔에 보이지 않고, 같은 명령 안에서 지운 행은 그 스캔에 여전히 보인다.

```text
 자기 트랜잭션 튜플과 curcid 의 경계 (스냅샷 curcid = 3)

 cmin   L1023 cmin >= curcid   visible   뜻
 2      N                      O         앞선 명령이 넣음
 3      Y                      X         지금 명령이 넣음
 4      Y                      X         스냅샷의 curcid 보다 뒤 명령이 넣음

 cmax   L1058 cmax >= curcid   visible   뜻 (xmin 도 나, xmax 도 나)
 2      N                      X         앞선 명령이 지움
 3      Y                      O         지금 명령이 지움. 스캔은 지우기 전 상태를 본다
```

[02] 의 스냅샷으로 튜플 여러 개를 판정해 본다. 스냅샷은 `{xmin 100, xmax 105, xip [100, 103]}`, 나는 102, `curcid = 3`. 90 은 오래전에, 101 과 104 는 스냅샷 전에 커밋했고, 105 는 스냅샷 뒤에 abort, 106 은 스냅샷 뒤에 커밋했다고 둔다.

```text
 t_xmin  xmin hint   t_xmax  xmax hint   visible  new hint             지나는 줄
 90      -           0       INVALID     O        XMIN_COMMITTED (*)   L1063 90<100 -> L1065 커밋
 100     -           0       INVALID     X        -                    L1063 xip 에 있음
 102 c1  -           0       INVALID     O        -                    L1021 나, L1023 1<3, L1026
 102 c3  -           0       INVALID     X        -                    L1021 나, L1023 3>=3
 101     COMMITTED   103     -           O        -                    L1079 통과, L1129 103 은 xip
 101     COMMITTED   104     -           X        XMAX_COMMITTED (*)   L1129 104 아님, L1132 커밋, L1141
 106     COMMITTED   0       INVALID     X        -                    L1079 106>=xmax 105
 105     -           0       INVALID     X        -                    L1063 105>=xmax (abort 인데도 힌트 없음)
 FROZEN  COMM|INV    0       INVALID     O        -                    L1079 FROZEN 이라 검사 생략

 102 c1 은 내 트랜잭션이 cmin 1 로 넣은 행

 (*) 커밋 힌트는 SetHintBits 의 LSN 조건을 통과해야 실제로 적힌다 (아래 그림)
 106 행의 XMIN_COMMITTED 는 더 새 스냅샷을 가진 다른 backend 가 적은 것이다
 105 행은 실제로 abort 됐지만 이 스냅샷에서는 "진행 중"이라 pg_xact 를 보지 않고 힌트도 안 적는다
```

커밋 힌트는 그 커밋 레코드가 디스크에 갔을 때만 적는다. 비동기 커밋이면 아직 안 갔을 수 있다.

```text
 SetHintBits(tuple, buffer, infomask, xid)      L114

 xid 가 Invalid (abort 힌트, XMAX_INVALID 등)  -> 무조건 적는다
 xid 가 있음 (커밋 힌트)
   commitLSN = TransactionIdGetCommitLSN(xid)
   permanent 버퍼 && XLogNeedsFlush(commitLSN) && 페이지 LSN < commitLSN
        -> 적지 않고 돌아간다 (L126)
           커밋 힌트는 커밋 레코드가 버퍼보다 먼저 디스크에 간다는 보장이 있을 때만
           안전하다. share 잠금이라 페이지 LSN 을 올릴 수도 없다 (주석 L87-L94)
   그 밖 -> t_infomask |= infomask, MarkBufferDirtyHint   (L130-L131)
```

## 결과가 쓰이는 곳

```text
 bool
      --> [07] 를 거쳐 [06] page_collect_tuples 의 valid
 t_infomask 의 힌트 비트
      --> 다음 판정이 L977, L1119 에서 XidInMVCCSnapshot 과 pg_xact 조회를 건너뛴다
          (xmin 커밋 힌트가 있어도 L1079 의 스냅샷 검사는 남는다)
      --> MarkBufferDirtyHint 로 페이지가 dirty 가 된다. 읽기만 해도 쓰기가 생기는 이유다
```

## 다루지 않는 것

MultiXact 의 구성원 해석(`HeapTupleGetUpdateXid`), combo CID 의 `GetRealCmin`, `GetRealCmax`(utils/time/combocid.c), 잠금 전용 xmax 판정 매크로 `HEAP_XMAX_IS_LOCKED_ONLY`, pre-9.0 `HEAP_MOVED_*`, `MarkBufferDirtyHint` 의 체크섬과 `XLOG_FPI_FOR_HINT` 처리는 요약만 했다.
