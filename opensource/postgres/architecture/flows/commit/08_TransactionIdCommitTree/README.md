# TransactionIdCommitTree

상위: [커밋](../README.md)

**pg_xact(CLOG)에서 이 트랜잭션과 서브트랜잭션들의 칸을 COMMITTED 로 바꾼다.** pg_xact 는 XID 하나당 2 비트짜리 배열이고, SLRU 라는 작은 전용 버퍼 풀을 거쳐 공유 메모리의 페이지를 고친다. 동기 커밋은 이미 WAL 을 flush 했으므로 LSN 없이 부르고, 비동기 커밋은 `TransactionIdAsyncCommitTree` 로 commit 레코드의 LSN 을 함께 넘겨 "이 LSN 까지 WAL 이 flush 되기 전에는 이 CLOG 페이지를 디스크에 쓰지 말라"는 표시(`group_lsn`)를 남긴다. 서브 XID 가 다른 페이지에 걸치면 SUB_COMMITTED 를 거쳐 두 단계로 바꿔서, 읽는 쪽이 반쯤 커밋된 트리를 보지 않게 한다.

## 위치

`access` / `transam` / `transam.c` L239-L245 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/transam.c#L239-L245))

## 실제 코드

`access` / `transam` / `transam.c` L228-L257 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/transam.c#L228-L257))

```c
// transam.c L228-L257

/*
 * TransactionIdCommitTree
 *		Marks the given transaction and children as committed
 *
 * "xid" is a toplevel transaction commit, and the xids array contains its
 * committed subtransactions.
 *
 * This commit operation is not guaranteed to be atomic, but if not, subxids
 * are correctly marked subcommit first.
 */
void
TransactionIdCommitTree(TransactionId xid, int nxids, TransactionId *xids)
{
	TransactionIdSetTreeStatus(xid, nxids, xids,
							   TRANSACTION_STATUS_COMMITTED,
							   InvalidXLogRecPtr);
}

/*
 * TransactionIdAsyncCommitTree
 *		Same as above, but for async commits.  The commit record LSN is needed.
 */
void
TransactionIdAsyncCommitTree(TransactionId xid, int nxids, TransactionId *xids,
							 XLogRecPtr lsn)
{
	TransactionIdSetTreeStatus(xid, nxids, xids,
							   TRANSACTION_STATUS_COMMITTED, lsn);
}
```

실제 일은 `clog.c` 가 한다. 서브 XID 가 모두 부모와 같은 페이지면 한 번에, 아니면 세 단계로 나눈다.

`access` / `transam` / `clog.c` L182-L248 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/clog.c#L182-L248))

```c
// clog.c L182-L248
void
TransactionIdSetTreeStatus(TransactionId xid, int nsubxids,
						   TransactionId *subxids, XidStatus status, XLogRecPtr lsn)
{
	int64		pageno = TransactionIdToPage(xid);	/* get page of parent */
	int			i;

	Assert(status == TRANSACTION_STATUS_COMMITTED ||
		   status == TRANSACTION_STATUS_ABORTED);

	/*
	 * See how many subxids, if any, are on the same page as the parent, if
	 * any.
	 */
	for (i = 0; i < nsubxids; i++)
	{
		if (TransactionIdToPage(subxids[i]) != pageno)
			break;
	}

	/*
	 * Do all items fit on a single page?
	 */
	if (i == nsubxids)
	{
		/*
		 * Set the parent and all subtransactions in a single call
		 */
		TransactionIdSetPageStatus(xid, nsubxids, subxids, status, lsn,
								   pageno, true);
	}
	else
	{
		int			nsubxids_on_first_page = i;

		/*
		 * If this is a commit then we care about doing this correctly (i.e.
		 * using the subcommitted intermediate status).  By here, we know
		 * we're updating more than one page of clog, so we must mark entries
		 * that are *not* on the first page so that they show as subcommitted
		 * before we then return to update the status to fully committed.
		 *
		 * To avoid touching the first page twice, skip marking subcommitted
		 * for the subxids on that first page.
		 */
		if (status == TRANSACTION_STATUS_COMMITTED)
			set_status_by_pages(nsubxids - nsubxids_on_first_page,
								subxids + nsubxids_on_first_page,
								TRANSACTION_STATUS_SUB_COMMITTED, lsn);

		/*
		 * Now set the parent and subtransactions on same page as the parent,
		 * if any
		 */
		pageno = TransactionIdToPage(xid);
		TransactionIdSetPageStatus(xid, nsubxids_on_first_page, subxids, status,
								   lsn, pageno, false);

		/*
		 * Now work through the rest of the subxids one clog page at a time,
		 * starting from the second page onwards, like we did above.
		 */
		set_status_by_pages(nsubxids - nsubxids_on_first_page,
							subxids + nsubxids_on_first_page,
							status, lsn);
	}
}
```

페이지 하나 안에서 2 비트를 바꾸는 가장 안쪽 함수다.

`access` / `transam` / `clog.c` L660-L717 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/clog.c#L660-L717))

```c
// clog.c L660-L717
static void
TransactionIdSetStatusBit(TransactionId xid, XidStatus status, XLogRecPtr lsn, int slotno)
{
	int			byteno = TransactionIdToByte(xid);
	int			bshift = TransactionIdToBIndex(xid) * CLOG_BITS_PER_XACT;
	char	   *byteptr;
	char		byteval;
	char		curval;

	Assert(XactCtl->shared->page_number[slotno] == TransactionIdToPage(xid));
	Assert(LWLockHeldByMeInMode(SimpleLruGetBankLock(XactCtl,
													 XactCtl->shared->page_number[slotno]),
								LW_EXCLUSIVE));

	byteptr = XactCtl->shared->page_buffer[slotno] + byteno;
	curval = (*byteptr >> bshift) & CLOG_XACT_BITMASK;

	// ... (L677-L694 생략: 복구 중 재생과 상태 전이 Assert)

	/* note this assumes exclusive access to the clog page */
	byteval = *byteptr;
	byteval &= ~(((1 << CLOG_BITS_PER_XACT) - 1) << bshift);
	byteval |= (status << bshift);
	*byteptr = byteval;

	/*
	 * Update the group LSN if the transaction completion LSN is higher.
	 *
	 * Note: lsn will be invalid when supplied during InRecovery processing,
	 * so we don't need to do anything special to avoid LSN updates during
	 * recovery. After recovery completes the next clog change will set the
	 * LSN correctly.
	 */
	if (!XLogRecPtrIsInvalid(lsn))
	{
		int			lsnindex = GetLSNIndex(slotno, xid);

		if (XactCtl->shared->group_lsn[lsnindex] < lsn)
			XactCtl->shared->group_lsn[lsnindex] = lsn;
	}
}
```

## 동작 흐름

```text
 TransactionIdCommitTree(xid, nchildren, children)              transam.c L240
   +-- TransactionIdSetTreeStatus(..., COMMITTED, InvalidXLogRecPtr)   clog.c L183
         L196  서브 XID 중 부모와 같은 페이지인 것의 수를 센다
         모두 같은 페이지
           L210  TransactionIdSetPageStatus(all_xact_same_page = true)
         일부가 다른 페이지
           L228  다른 페이지 것들을 SUB_COMMITTED 로              set_status_by_pages
           L237  부모 + 같은 페이지 것들을 COMMITTED 로
           L244  다른 페이지 것들을 COMMITTED 로

 TransactionIdSetPageStatus                                     clog.c L293
   L321  같은 페이지이고 서브 XID 가 5 개 이하면 (THRESHOLD_SUBTRANS_CLOG_OPT)
           L334  bank lock 을 기다리지 않고 잡히면 바로 고친다
           L342  못 잡으면 그룹 갱신: 리더 하나가 여러 backend 몫을 한 번에
   L352  아니면 bank lock 을 기다려 잡고 고친다
     TransactionIdSetPageStatusInternal (L364)
       SimpleLruReadPage, 서브 XID 를 SUB_COMMITTED -> 부모 COMMITTED -> 서브 COMMITTED
       page_dirty[slotno] = true
```

CLOG 페이지 안에서 XID 가 차지하는 자리는 나눗셈 세 번으로 정해진다(clog.c L62-L89). XID 1003 을 커밋할 때 바뀌는 바이트는 이렇다.

```text
 CLOG_XACTS_PER_PAGE = 32768, CLOG_XACTS_PER_BYTE = 4, CLOG_BITS_PER_XACT = 2

 xid 1003
   TransactionIdToPage   1003 / 32768        = 0
   TransactionIdToByte   (1003 % 32768) / 4  = 250
   TransactionIdToBIndex 1003 % 4            = 3   -> bshift = 3 * 2 = 6

 status 값 (clog.h L27-L30)  00 IN_PROGRESS  01 COMMITTED  10 ABORTED  11 SUB_COMMITTED

 byte 250 (xid 1000~1003, 낮은 비트가 1000)
                      bits 7-6   5-4    3-2    1-0
                      xid  1003  1002   1001   1000
 before  0x15 =       00         01     01     01      1000~1002 는 커밋, 1003 은 진행 중
 after   0x55 =       01         01     01     01      L697-L700  byteval &= ~(3 << 6); byteval |= (1 << 6)
```

서브 XID 가 다른 페이지에 있을 때 SUB_COMMITTED 를 먼저 세우는 이유는 L163-L173 주석의 예와 같다. 페이지마다 따로 잠그므로, 중간에 누가 읽어도 "부모는 커밋, 자식은 진행 중"인 상태가 보이면 안 된다.

```text
 t 가 p1, t1 이 p1, t2 와 t3 이 p2, t4 가 p3 에 있을 때

 step  p1            p2              p3           읽는 쪽이 보는 트리
 0     t=0  t1=0     t2=0  t3=0      t4=0         진행 중
 1     t=0  t1=0     t2=11 t3=11     t4=11        SUB_COMMITTED 는 부모를 따라간다 -> 진행 중
 2     t=01 t1=01    t2=11 t3=11     t4=11        부모가 커밋 -> 전부 커밋
 3     t=01 t1=01    t2=01 t3=01     t4=01        커밋
```

## 결과가 쓰이는 곳

```text
 CLOG 페이지의 비트 (공유 메모리)
      --> TransactionIdDidCommit -> TransactionLogFetch (transam.c L52)
          ([MVCC 가시성 10](../../mvcc-visibility/10_TransactionIdDidCommit/README.md))
      --> SUB_COMMITTED 를 만나면 pg_subtrans 로 부모를 찾아 다시 본다
 group_lsn (비동기 커밋일 때)
      --> CLOG 페이지를 디스크에 쓰기 전 XLogFlush(max_lsn)  (slru.c L893-L925)
      --> 힌트 비트를 세우기 전 XLogNeedsFlush(commitLSN) 검사  (heapam_visibility.c L120-L127)
 page_dirty
      --> 체크포인트의 CheckPointCLOG 가 디스크로 내린다
```

## 다루지 않는 것

그룹 갱신(`TransactionGroupUpdateXidStatus`)의 리더 선출과 대기, SLRU 버퍼 교체와 bank lock 구조(`slru.c`), CLOG 페이지 확장과 잘라내기(`ExtendCLOG`, `TruncateCLOG`), abort 쪽 `TransactionIdAbortTree` 는 다루지 않았다.
