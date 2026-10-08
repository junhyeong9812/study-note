# RelationGetBufferForTuple

상위: [행 쓰기와 WAL 기록](../README.md)

**새 행이 들어갈 자리가 있는 힙 페이지를 찾아, pin 과 배타 content lock 을 건 채 돌려준다.** 후보는 싼 순서로 본다. 이 백엔드가 마지막으로 넣은 블록, FSM(free space map)이 추천하는 블록, 릴레이션의 마지막 블록, 그래도 없으면 릴레이션을 늘린다. ERROR 를 낼 수 있는 일(행 크기 초과, 디스크 읽기, 확장)은 전부 여기서 끝나므로, 호출자는 이 함수가 돌아온 뒤 바로 크리티컬 섹션에 들어갈 수 있다.

## 위치

`access` / `heap` / `hio.c` L502-L885 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/hio.c#L502-L885))

## 실제 코드

필요한 공간을 계산하고 첫 후보 블록을 고르는 앞부분이다. fillfactor 로 남겨 둘 공간을 더한다.

`access` / `heap` / `hio.c` L501-L598 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/hio.c#L501-L598))

```c
// hio.c L501-L598
Buffer
RelationGetBufferForTuple(Relation relation, Size len,
						  Buffer otherBuffer, int options,
						  BulkInsertState bistate,
						  Buffer *vmbuffer, Buffer *vmbuffer_other,
						  int num_pages)
{
	bool		use_fsm = !(options & HEAP_INSERT_SKIP_FSM);
	Buffer		buffer = InvalidBuffer;
	Page		page;
	Size		nearlyEmptyFreeSpace,
				pageFreeSpace = 0,
				saveFreeSpace = 0,
				targetFreeSpace = 0;
	BlockNumber targetBlock,
				otherBlock;
	bool		unlockedTargetBuffer;
	bool		recheckVmPins;

	len = MAXALIGN(len);		/* be conservative */

	/* if the caller doesn't know by how many pages to extend, extend by 1 */
	if (num_pages <= 0)
		num_pages = 1;

	/* Bulk insert is not supported for updates, only inserts. */
	Assert(otherBuffer == InvalidBuffer || !bistate);

	/*
	 * If we're gonna fail for oversize tuple, do it right away
	 */
	if (len > MaxHeapTupleSize)
		ereport(ERROR,
				(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
				 errmsg("row is too big: size %zu, maximum size %zu",
						len, MaxHeapTupleSize)));

	/* Compute desired extra freespace due to fillfactor option */
	saveFreeSpace = RelationGetTargetPageFreeSpace(relation,
												   HEAP_DEFAULT_FILLFACTOR);

	/*
	 * Since pages without tuples can still have line pointers, we consider
	 * pages "empty" when the unavailable space is slight.  This threshold is
	 * somewhat arbitrary, but it should prevent most unnecessary relation
	 * extensions while inserting large tuples into low-fillfactor tables.
	 */
	nearlyEmptyFreeSpace = MaxHeapTupleSize -
		(MaxHeapTuplesPerPage / 8 * sizeof(ItemIdData));
	if (len + saveFreeSpace > nearlyEmptyFreeSpace)
		targetFreeSpace = Max(len, nearlyEmptyFreeSpace);
	else
		targetFreeSpace = len + saveFreeSpace;

	if (otherBuffer != InvalidBuffer)
		otherBlock = BufferGetBlockNumber(otherBuffer);
	else
		otherBlock = InvalidBlockNumber;	/* just to keep compiler quiet */

	/*
	 * We first try to put the tuple on the same page we last inserted a tuple
	 * on, as cached in the BulkInsertState or relcache entry.  If that
	 * doesn't work, we ask the Free Space Map to locate a suitable page.
	 * Since the FSM's info might be out of date, we have to be prepared to
	 * loop around and retry multiple times. (To ensure this isn't an infinite
	 * loop, we must update the FSM with the correct amount of free space on
	 * each page that proves not to be suitable.)  If the FSM has no record of
	 * a page with enough free space, we give up and extend the relation.
	 *
	 * When use_fsm is false, we either put the tuple onto the existing target
	 * page or extend the relation.
	 */
	if (bistate && bistate->current_buf != InvalidBuffer)
		targetBlock = BufferGetBlockNumber(bistate->current_buf);
	else
		targetBlock = RelationGetTargetBlock(relation);

	if (targetBlock == InvalidBlockNumber && use_fsm)
	{
		/*
		 * We have no cached target page, so ask the FSM for an initial
		 * target.
		 */
		targetBlock = GetPageWithFreeSpace(relation, targetFreeSpace);
	}

	/*
	 * If the FSM knows nothing of the rel, try the last page before we give
	 * up and extend.  This avoids one-tuple-per-page syndrome during
	 * bootstrapping or in a recently-started system.
	 */
	if (targetBlock == InvalidBlockNumber)
	{
		BlockNumber nblocks = RelationGetNumberOfBlocks(relation);

		if (nblocks > 0)
			targetBlock = nblocks - 1;
	}
```

후보 블록을 읽어 잠그고 공간을 재는 루프다. 다른 버퍼(`otherBuffer`)는 `heap_update` 가 쓰는 경우라 INSERT 에서는 첫 갈래만 탄다.

`access` / `heap` / `hio.c` L600-L708 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/hio.c#L600-L708))

```c
// hio.c L600-L708
loop:
	while (targetBlock != InvalidBlockNumber)
	{
		/*
		 * Read and exclusive-lock the target block, as well as the other
		 * block if one was given, taking suitable care with lock ordering and
		 * the possibility they are the same block.
		 *
		 * If the page-level all-visible flag is set, caller will need to
		 * clear both that and the corresponding visibility map bit.  However,
		 * by the time we return, we'll have x-locked the buffer, and we don't
		 * want to do any I/O while in that state.  So we check the bit here
		 * before taking the lock, and pin the page if it appears necessary.
		 * Checking without the lock creates a risk of getting the wrong
		 * answer, so we'll have to recheck after acquiring the lock.
		 */
		if (otherBuffer == InvalidBuffer)
		{
			/* easy case */
			buffer = ReadBufferBI(relation, targetBlock, RBM_NORMAL, bistate);
			if (PageIsAllVisible(BufferGetPage(buffer)))
				visibilitymap_pin(relation, targetBlock, vmbuffer);

			/*
			 * If the page is empty, pin vmbuffer to set all_frozen bit later.
			 */
			if ((options & HEAP_INSERT_FROZEN) &&
				(PageGetMaxOffsetNumber(BufferGetPage(buffer)) == 0))
				visibilitymap_pin(relation, targetBlock, vmbuffer);

			LockBuffer(buffer, BUFFER_LOCK_EXCLUSIVE);
		}
		// ... (L632-L657 생략: otherBuffer 가 있을 때 (heap_update) 두 버퍼를 블록 번호 순서로 잠근다)

		// ... (L659-L679 생략: 잠금 뒤 all-visible 상태가 바뀌었을 수 있다는 주석)
		GetVisibilityMapPins(relation, buffer, otherBuffer,
							 targetBlock, otherBlock, vmbuffer,
							 vmbuffer_other);

		/*
		 * Now we can check to see if there's enough free space here. If so,
		 * we're done.
		 */
		page = BufferGetPage(buffer);

		/*
		 * If necessary initialize page, it'll be used soon.  We could avoid
		 * dirtying the buffer here, and rely on the caller to do so whenever
		 * it puts a tuple onto the page, but there seems not much benefit in
		 * doing so.
		 */
		if (PageIsNew(page))
		{
			PageInit(page, BufferGetPageSize(buffer), 0);
			MarkBufferDirty(buffer);
		}

		pageFreeSpace = PageGetHeapFreeSpace(page);
		if (targetFreeSpace <= pageFreeSpace)
		{
			/* use this page as future insert target, too */
			RelationSetTargetBlock(relation, targetBlock);
			return buffer;
		}
```

공간이 모자라면 잠금을 풀고 다음 후보를 FSM 에 묻는다.

`access` / `heap` / `hio.c` L710-L764 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/hio.c#L710-L764))

```c
// hio.c L710-L764
		/*
		 * Not enough space, so we must give up our page locks and pin (if
		 * any) and prepare to look elsewhere.  We don't care which order we
		 * unlock the two buffers in, so this can be slightly simpler than the
		 * code above.
		 */
		LockBuffer(buffer, BUFFER_LOCK_UNLOCK);
		if (otherBuffer == InvalidBuffer)
			ReleaseBuffer(buffer);
		else if (otherBlock != targetBlock)
		{
			LockBuffer(otherBuffer, BUFFER_LOCK_UNLOCK);
			ReleaseBuffer(buffer);
		}

		/* Is there an ongoing bulk extension? */
		if (bistate && bistate->next_free != InvalidBlockNumber)
		{
			Assert(bistate->next_free <= bistate->last_free);

			/*
			 * We bulk extended the relation before, and there are still some
			 * unused pages from that extension, so we don't need to look in
			 * the FSM for a new page. But do record the free space from the
			 * last page, somebody might insert narrower tuples later.
			 */
			if (use_fsm)
				RecordPageWithFreeSpace(relation, targetBlock, pageFreeSpace);

			targetBlock = bistate->next_free;
			if (bistate->next_free >= bistate->last_free)
			{
				bistate->next_free = InvalidBlockNumber;
				bistate->last_free = InvalidBlockNumber;
			}
			else
				bistate->next_free++;
		}
		else if (!use_fsm)
		{
			/* Without FSM, always fall out of the loop and extend */
			break;
		}
		else
		{
			/*
			 * Update FSM as to condition of this page, and ask for another
			 * page to try.
			 */
			targetBlock = RecordAndGetPageWithFreeSpace(relation,
														targetBlock,
														pageFreeSpace,
														targetFreeSpace);
		}
	}
```

후보가 다 떨어지면 릴레이션을 늘린다.

`access` / `heap` / `hio.c` L766-L885 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/hio.c#L766-L885))

```c
// hio.c L766-L885
	/* Have to extend the relation */
	buffer = RelationAddBlocks(relation, bistate, num_pages, use_fsm,
							   &unlockedTargetBuffer);

	targetBlock = BufferGetBlockNumber(buffer);
	page = BufferGetPage(buffer);

	// ... (L773-L850 생략: FROZEN 삽입의 VM pin, otherBuffer 재잠금, VM pin 재확인)

	/*
	 * If the target buffer was temporarily unlocked since the relation
	 * extension, it's possible, although unlikely, that all the space on the
	 * page was already used. If so, we just retry from the start.  If we
	 * didn't unlock, something has gone wrong if there's not enough space -
	 * the test at the top should have prevented reaching this case.
	 */
	pageFreeSpace = PageGetHeapFreeSpace(page);
	if (len > pageFreeSpace)
	{
		if (unlockedTargetBuffer)
		{
			if (otherBuffer != InvalidBuffer)
				LockBuffer(otherBuffer, BUFFER_LOCK_UNLOCK);
			UnlockReleaseBuffer(buffer);

			goto loop;
		}
		elog(PANIC, "tuple is too big: size %zu", len);
	}

	/*
	 * Remember the new page as our target for future insertions.
	 *
	 * XXX should we enter the new page into the free space map immediately,
	 * or just keep it for this backend's exclusive use in the short run
	 * (until VACUUM sees it)?	Seems to depend on whether you expect the
	 * current backend to make more insertions or not, which is probably a
	 * good bet most of the time.  So for now, don't add it to FSM yet.
	 */
	RelationSetTargetBlock(relation, targetBlock);

	return buffer;
}
```

## 동작 흐름

```text
 L520  len = MAXALIGN(len)
 L532  len > MaxHeapTupleSize 면 ERROR "row is too big"
 L539  saveFreeSpace = BLCKSZ * (100 - fillfactor) / 100         fillfactor 100 이면 0
 L548  nearlyEmptyFreeSpace = MaxHeapTupleSize - (MaxHeapTuplesPerPage / 8 * 4)
 L550  len + saveFreeSpace 가 그보다 크면 targetFreeSpace = Max(len, nearlyEmpty)
 L553  아니면 targetFreeSpace = len + saveFreeSpace

 첫 후보
 L573  bistate 가 잡고 있는 블록, 없으면 L576 RelationGetTargetBlock (relcache 의 마지막 삽입 블록)
 L578  그래도 없고 FSM 을 쓰면 GetPageWithFreeSpace(targetFreeSpace)
 L592  FSM 도 모르면 마지막 블록 (nblocks - 1)

 L601  while (targetBlock 이 있으면)
 L619    ReadBufferBI                         --> [버퍼 관리] pin
 L620    all-visible 이면 visibilitymap_pin    잠그기 전에 VM 페이지를 pin (잠금 중 I/O 를 피한다)
 L630    LockBuffer(buffer, EXCLUSIVE)
 L680    GetVisibilityMapPins                  잠근 뒤 상태가 바뀌었으면 다시 맞춘다
 L696    새 페이지(PageIsNew)면 PageInit + MarkBufferDirty
 L702    pageFreeSpace = PageGetHeapFreeSpace(page)
 L703    targetFreeSpace <= pageFreeSpace 면
 L706      RelationSetTargetBlock, L707 return buffer       (pin + 배타 잠금 상태)
 L716    아니면 잠금 해제, L718 pin 해제
 L759    FSM 에 이 페이지의 실제 여유를 기록하고 다음 후보를 받는다
           FSM 이 오래된 정보를 줘도 매번 고쳐 적으므로 무한 루프가 되지 않는다 (L565-L568 주석)

 L767  RelationAddBlocks                       릴레이션 확장. 새 페이지를 잠근 채 받는다
 L859  다시 잰 공간이 len 보다 작으면
         잠금을 놓은 적이 있으면 L868 goto loop, 아니면 L870 PANIC
 L882  RelationSetTargetBlock(새 블록)         FSM 에는 아직 넣지 않는다 (L876-L880 주석)
 L884  return buffer
```

필요한 공간 계산은 숫자로 따라갈 수 있다. 기본 빌드(BLCKSZ 8192, MAXALIGN 8)에서 상수는 다음과 같다.

```text
 MaxHeapTupleSize     = 8192 - MAXALIGN(24 + 4) = 8192 - 32 = 8160      htup_details.h L615
 MaxHeapTuplesPerPage = (8192 - 24) / (MAXALIGN(23) + 4) = 8168 / 28 = 291   htup_details.h L629
 nearlyEmptyFreeSpace = 8160 - (291 / 8) * 4 = 8160 - 36 * 4 = 8016    L548

 행 길이 32 (int4 두 개)
   fillfactor 100   saveFreeSpace = 0      targetFreeSpace = 32
   fillfactor 90    saveFreeSpace = 819    targetFreeSpace = 32 + 819 = 851
                    (8192 * 10 / 100 = 819, 정수 나눗셈)

 행 길이 7900, fillfactor 90
   7900 + 819 = 8719 > 8016  ->  targetFreeSpace = Max(7900, 8016) = 8016
   거의 빈 페이지면 fillfactor 를 무시하고 받아 준다 (L493-L496 주석)
```

공간 비교는 `PageGetHeapFreeSpace`(storage/page/bufpage.c L990-L1040)의 값과 한다. 이 값은 `PageGetFreeSpace` 가 주는 `pd_upper - pd_lower` 에서 새 줄 포인터 4바이트를 뺀 것이고(같은 파일 L915-L919), 줄 포인터가 이미 `MaxHeapTuplesPerPage`(291)개 이상인데 빈 줄 포인터가 없으면 0 이 된다(L1004-L1035).

```text
 후보 페이지 셋을 차례로 보는 경우 (행 길이 32, fillfactor 100, targetFreeSpace = 32)

 블록  pd_lower  pd_upper  여유   출처와 판정
 7     928       960       28     마지막 삽입 블록. 모자람 -> 잠금, pin 해제, FSM 에 28 기록
 3     400       5184      4780   FSM 이 준 블록. 충분 -> 이 블록을 잠근 채 반환

 두 페이지 모두 32바이트 행만 있다고 하면 숫자가 맞는다
   블록 7: 행 226개  lower = 24 + 4 * 226 = 928   upper = 8192 - 32 * 226 = 960
   블록 3: 행 94개   lower = 24 + 4 * 94  = 400   upper = 8192 - 32 * 94  = 5184
   여유 = upper - lower - 4

 블록 3 에 행을 넣으면 ([05])
   pd_lower 400 -> 404 (줄 포인터 하나), pd_upper 5184 -> 5152 (행 32바이트)
   다음 삽입의 첫 후보는 RelationSetTargetBlock 으로 기억한 블록 3
```

## 결과가 쓰이는 곳

```text
 돌려준 buffer (pin + BUFFER_LOCK_EXCLUSIVE)
      --> [02] 가 크리티컬 섹션 안에서 [05] RelationPutHeapTuple 로 행을 넣는다
      --> [02] 의 UnlockReleaseBuffer 가 잠금과 pin 을 푼다
 *vmbuffer (all-visible 페이지면 pin 된 VM 페이지)
      --> [02] 가 크리티컬 섹션 전에 잠그고, 안에서 비트를 지운다
 RelationSetTargetBlock
      --> 같은 백엔드의 다음 삽입이 이 블록부터 본다
 RecordAndGetPageWithFreeSpace 로 고친 FSM
      --> 다른 백엔드의 다음 삽입이 덜 헤맨다
```

## 다루지 않는 것

FSM 의 트리 구조와 갱신(`GetPageWithFreeSpace`, `RecordAndGetPageWithFreeSpace`), 릴레이션 확장(`RelationAddBlocks`, `ExtendBufferedRelBy`, 확장 잠금), `heap_update` 의 두 버퍼 잠금 순서, visibility map pin 재조정(`GetVisibilityMapPins`), 대량 삽입 상태(`BulkInsertState` 의 `next_free`, `last_free`)는 페이지 고르기의 곁가지라 요약만 했다.
