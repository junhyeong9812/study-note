# lazy_vacuum_heap_rel

상위: [vacuum](../README.md)

**힙의 두 번째 패스다.** 인덱스에서 dead TID 를 모두 지운 뒤에만 불린다. TidStore 를 블록 순으로 순회하며 dead TID 가 있는 페이지만 읽고, 페이지마다 `lazy_vacuum_heap_page` 가 그 LP_DEAD 줄 포인터를 LP_UNUSED 로 바꾸고, 줄 포인터 배열 끝의 빈칸을 잘라내고, WAL 을 남긴다. 그러고 나서 페이지가 모두에게 보이게 됐는지 다시 확인해 visibility map 을 켠다. 첫 번째 패스와 달리 cleanup lock 이 아니라 보통 배타 잠금이면 된다(L2805 주석). 여기서 만지는 줄 포인터는 이미 저장 공간이 없는 LP_DEAD 뿐이다(L2881 Assert).

## 위치

`access` / `heap` / `vacuumlazy.c` L2733-L2841 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L2733-L2841))

## 실제 코드

`access` / `heap` / `vacuumlazy.c` L2716-L2841 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L2716-L2841))

```c
// vacuumlazy.c L2716-L2841
/*
 *	lazy_vacuum_heap_rel() -- second pass over the heap for two pass strategy
 *
 * This routine marks LP_DEAD items in vacrel->dead_items as LP_UNUSED. Pages
 * that never had lazy_scan_prune record LP_DEAD items are not visited at all.
 *
 * We may also be able to truncate the line pointer array of the heap pages we
 * visit.  If there is a contiguous group of LP_UNUSED items at the end of the
 * array, it can be reclaimed as free space.  These LP_UNUSED items usually
 * start out as LP_DEAD items recorded by lazy_scan_prune (we set items from
 * each page to LP_UNUSED, and then consider if it's possible to truncate the
 * page's line pointer array).
 *
 * Note: the reason for doing this as a second pass is we cannot remove the
 * tuples until we've removed their index entries, and we want to process
 * index entry removal in batches as large as possible.
 */
static void
lazy_vacuum_heap_rel(LVRelState *vacrel)
{
	ReadStream *stream;
	BlockNumber vacuumed_pages = 0;
	Buffer		vmbuffer = InvalidBuffer;
	LVSavedErrInfo saved_err_info;
	TidStoreIter *iter;

	Assert(vacrel->do_index_vacuuming);
	Assert(vacrel->do_index_cleanup);
	Assert(vacrel->num_index_scans > 0);

	// ... (L2746-L2753 생략: 진행 상태와 오류 문맥)

	iter = TidStoreBeginIterate(vacrel->dead_items);

	// ... (L2757-L2764 생략: read stream 의 배치 모드 설명)
	stream = read_stream_begin_relation(READ_STREAM_MAINTENANCE |
										READ_STREAM_USE_BATCHING,
										vacrel->bstrategy,
										vacrel->rel,
										MAIN_FORKNUM,
										vacuum_reap_lp_read_stream_next,
										iter,
										sizeof(TidStoreIterResult));

	while (true)
	{
		BlockNumber blkno;
		Buffer		buf;
		Page		page;
		TidStoreIterResult *iter_result;
		Size		freespace;
		OffsetNumber offsets[MaxOffsetNumber];
		int			num_offsets;

		vacuum_delay_point(false);

		buf = read_stream_next_buffer(stream, (void **) &iter_result);

		/* The relation is exhausted */
		if (!BufferIsValid(buf))
			break;

		vacrel->blkno = blkno = BufferGetBlockNumber(buf);

		Assert(iter_result);
		num_offsets = TidStoreGetBlockOffsets(iter_result, offsets, lengthof(offsets));
		Assert(num_offsets <= lengthof(offsets));

		/*
		 * Pin the visibility map page in case we need to mark the page
		 * all-visible.  In most cases this will be very cheap, because we'll
		 * already have the correct page pinned anyway.
		 */
		visibilitymap_pin(vacrel->rel, blkno, &vmbuffer);

		/* We need a non-cleanup exclusive lock to mark dead_items unused */
		LockBuffer(buf, BUFFER_LOCK_EXCLUSIVE);
		lazy_vacuum_heap_page(vacrel, blkno, buf, offsets,
							  num_offsets, vmbuffer);

		/* Now that we've vacuumed the page, record its available space */
		page = BufferGetPage(buf);
		freespace = PageGetHeapFreeSpace(page);

		UnlockReleaseBuffer(buf);
		RecordPageWithFreeSpace(vacrel->rel, blkno, freespace);
		vacuumed_pages++;
	}

	read_stream_end(stream);
	TidStoreEndIterate(iter);

	// ... (L2822-L2840 생략: VM 핀 해제, 일관성 Assert, DEBUG2 로그, 오류 문맥 복원)
}
```

페이지 하나를 고치는 부분이다.

`access` / `heap` / `vacuumlazy.c` L2843-L2949 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L2843-L2949))

```c
// vacuumlazy.c L2843-L2949
/*
 *	lazy_vacuum_heap_page() -- free page's LP_DEAD items listed in the
 *						  vacrel->dead_items store.
 *
 * Caller must have an exclusive buffer lock on the buffer (though a full
 * cleanup lock is also acceptable).  vmbuffer must be valid and already have
 * a pin on blkno's visibility map page.
 */
static void
lazy_vacuum_heap_page(LVRelState *vacrel, BlockNumber blkno, Buffer buffer,
					  OffsetNumber *deadoffsets, int num_offsets,
					  Buffer vmbuffer)
{
	Page		page = BufferGetPage(buffer);
	OffsetNumber unused[MaxHeapTuplesPerPage];
	int			nunused = 0;
	TransactionId visibility_cutoff_xid;
	bool		all_frozen;
	LVSavedErrInfo saved_err_info;

	Assert(vacrel->do_index_vacuuming);

	// ... (L2865-L2870 생략: 진행 상태와 오류 문맥)

	START_CRIT_SECTION();

	for (int i = 0; i < num_offsets; i++)
	{
		ItemId		itemid;
		OffsetNumber toff = deadoffsets[i];

		itemid = PageGetItemId(page, toff);

		Assert(ItemIdIsDead(itemid) && !ItemIdHasStorage(itemid));
		ItemIdSetUnused(itemid);
		unused[nunused++] = toff;
	}

	Assert(nunused > 0);

	/* Attempt to truncate line pointer array now */
	PageTruncateLinePointerArray(page);

	/*
	 * Mark buffer dirty before we write WAL.
	 */
	MarkBufferDirty(buffer);

	/* XLOG stuff */
	if (RelationNeedsWAL(vacrel->rel))
	{
		log_heap_prune_and_freeze(vacrel->rel, buffer,
								  InvalidTransactionId,
								  false,	/* no cleanup lock required */
								  PRUNE_VACUUM_CLEANUP,
								  NULL, 0,	/* frozen */
								  NULL, 0,	/* redirected */
								  NULL, 0,	/* dead */
								  unused, nunused);
	}

	/*
	 * End critical section, so we safely can do visibility tests (which
	 * possibly need to perform IO and allocate memory!). If we crash now the
	 * page (including the corresponding vm bit) might not be marked all
	 * visible, but that's fine. A later vacuum will fix that.
	 */
	END_CRIT_SECTION();

	// ... (L2917-L2922 생략: critical section 밖에서 가시성을 다시 보는 이유)
	Assert(!PageIsAllVisible(page));
	if (heap_page_is_all_visible(vacrel, buffer, &visibility_cutoff_xid,
								 &all_frozen))
	{
		uint8		flags = VISIBILITYMAP_ALL_VISIBLE;

		if (all_frozen)
		{
			Assert(!TransactionIdIsValid(visibility_cutoff_xid));
			flags |= VISIBILITYMAP_ALL_FROZEN;
		}

		PageSetAllVisible(page);
		visibilitymap_set(vacrel->rel, blkno, buffer,
						  InvalidXLogRecPtr,
						  vmbuffer, visibility_cutoff_xid,
						  flags);

		/* Count the newly set VM page for logging */
		vacrel->vm_new_visible_pages++;
		if (all_frozen)
			vacrel->vm_new_visible_frozen_pages++;
	}

	/* Revert to the previous phase information for error traceback */
	restore_vacuum_error_info(vacrel, &saved_err_info);
}
```

## 동작 흐름

```text
 lazy_vacuum_heap_rel
 L2755  iter = TidStoreBeginIterate(dead_items)       블록 번호 오름차순
 L2765  read stream: 콜백 vacuum_reap_lp_read_stream_next 가 다음 블록을 TidStore 에서 꺼낸다
 L2786  buf = read_stream_next_buffer
 L2795  num_offsets = TidStoreGetBlockOffsets(iter_result, offsets)
 L2806  LockBuffer(EXCLUSIVE)                         cleanup lock 이 아니어도 된다
 L2807  lazy_vacuum_heap_page(blkno, buf, offsets)
 L2815  RecordPageWithFreeSpace                       이 페이지의 FSM 은 여기서 기록한다

 lazy_vacuum_heap_page
 L2872  START_CRIT_SECTION
 L2882  offset 마다 ItemIdSetUnused                    Assert: LP_DEAD 이고 저장 공간이 없다
 L2889  PageTruncateLinePointerArray                   끝의 UNUSED 를 잘라 pd_lower 를 줄인다
 L2894  MarkBufferDirty
 L2899  log_heap_prune_and_freeze(PRUNE_VACUUM_CLEANUP, unused[])
 L2915  END_CRIT_SECTION
 L2924  heap_page_is_all_visible -> PageSetAllVisible, visibilitymap_set
```

줄 포인터 배열이 실제로 어떻게 바뀌는지 한 페이지로 본다. 첫 패스에서 lp2, lp5, lp6 이 LP_DEAD 가 되었고 dead_items 에 (7,2), (7,5), (7,6) 이 있다. 줄 포인터 하나는 4 바이트(`ItemIdData`), 페이지 헤더는 24 바이트다.

```text
 before   lp1 NORMAL  lp2 DEAD  lp3 NORMAL  lp4 NORMAL  lp5 DEAD  lp6 DEAD
          pd_lower = 24 + 6 * 4 = 48

 L2882    lp1 NORMAL  lp2 UNUSED  lp3 NORMAL  lp4 NORMAL  lp5 UNUSED  lp6 UNUSED

 L2889    PageTruncateLinePointerArray (storage/page/bufpage.c L834)
            뒤에서부터: lp6 UNUSED, lp5 UNUSED -> nunusedend = 2, lp4 사용 중 -> 멈춤
            pd_lower -= 4 * 2  ->  40
            lp2 가 UNUSED 라 PD_HAS_FREE_LINES 힌트를 세운다
 after    lp1 NORMAL  lp2 UNUSED  lp3 NORMAL  lp4 NORMAL
          다음 INSERT 는 lp2 를 다시 쓰거나 lp5 부터 새로 붙인다
```

첫 패스와 두 번째 패스가 페이지에 하는 일과 필요한 잠금을 나란히 놓으면 이렇다.

```text
 pass 1  lazy_scan_prune -> heap_page_prune_and_freeze
           lock     cleanup lock (배타 + 다른 pin 없음)
           changes  NORMAL -> DEAD / REDIRECT / UNUSED, 튜플 공간 회수와 조각 모음, freeze
           WAL      XLOG_HEAP2_PRUNE_VACUUM_SCAN

 pass 2  lazy_vacuum_heap_page
           lock     exclusive (L2805 "non-cleanup exclusive lock")
           changes  DEAD -> UNUSED, 줄 포인터 배열 끝 자르기
           WAL      XLOG_HEAP2_PRUNE_VACUUM_CLEANUP

 두 레코드는 이름만 다르고 형식과 재생이 같다 (src/include/access/heapam_xlog.h L54-L62)
```

## 결과가 쓰이는 곳

```text
 LP_UNUSED 줄 포인터, pd_lower
      --> PageAddItemExtended 가 PD_HAS_FREE_LINES 를 보고 빈 줄 포인터를 재사용한다
 FSM (RecordPageWithFreeSpace)
      --> 다음 INSERT 의 RelationGetBufferForTuple
 VM all-visible / all-frozen
      --> index-only scan, 다음 VACUUM 의 건너뛰기
```

## 다루지 않는 것

read stream 의 배치 모드, `heap_page_is_all_visible` 의 판정 세부, WAL 레코드의 형식과 redo(`heap_xlog_prune_freeze`), 힙 끝 페이지 잘라내기(`lazy_truncate_heap`)는 다루지 않았다.
