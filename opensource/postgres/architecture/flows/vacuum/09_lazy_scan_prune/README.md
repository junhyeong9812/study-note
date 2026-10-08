# lazy_scan_prune

상위: [vacuum](../README.md)

**힙 페이지 하나를 VACUUM 의 첫 번째 패스로 처리한다.** 실제 prune 과 freeze 는 [10] `heap_page_prune_and_freeze` 에 `HEAP_PAGE_PRUNE_FREEZE` 옵션으로 맡기고(인덱스가 없으면 죽은 항목을 바로 UNUSED 로 만들라는 옵션도 함께), 돌아온 결과로 세 가지를 한다. 남은 LP_DEAD 줄 포인터의 TID 를 dead_items 에 넣고, 통계를 더하고, 페이지가 모두에게 보이게 됐으면 visibility map 에 all-visible(그리고 다 얼었으면 all-frozen) 비트를 켠다.

## 위치

`access` / `heap` / `vacuumlazy.c` L1957-L2230 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L1957-L2230))

## 실제 코드

`access` / `heap` / `vacuumlazy.c` L1957-L2230 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L1957-L2230))

```c
// vacuumlazy.c L1957-L2230
static int
lazy_scan_prune(LVRelState *vacrel,
				Buffer buf,
				BlockNumber blkno,
				Page page,
				Buffer vmbuffer,
				bool all_visible_according_to_vm,
				bool *has_lpdead_items,
				bool *vm_page_frozen)
{
	Relation	rel = vacrel->rel;
	PruneFreezeResult presult;
	int			prune_options = 0;

	Assert(BufferGetBlockNumber(buf) == blkno);

	/*
	 * Prune all HOT-update chains and potentially freeze tuples on this page.
	 *
	 * If the relation has no indexes, we can immediately mark would-be dead
	 * items LP_UNUSED.
	 *
	 * The number of tuples removed from the page is returned in
	 * presult.ndeleted.  It should not be confused with presult.lpdead_items;
	 * presult.lpdead_items's final value can be thought of as the number of
	 * tuples that were deleted from indexes.
	 *
	 * We will update the VM after collecting LP_DEAD items and freezing
	 * tuples. Pruning will have determined whether or not the page is
	 * all-visible.
	 */
	prune_options = HEAP_PAGE_PRUNE_FREEZE;
	if (vacrel->nindexes == 0)
		prune_options |= HEAP_PAGE_PRUNE_MARK_UNUSED_NOW;

	heap_page_prune_and_freeze(rel, buf, vacrel->vistest, prune_options,
							   &vacrel->cutoffs, &presult, PRUNE_VACUUM_SCAN,
							   &vacrel->offnum,
							   &vacrel->NewRelfrozenXid, &vacrel->NewRelminMxid);

	Assert(MultiXactIdIsValid(vacrel->NewRelminMxid));
	Assert(TransactionIdIsValid(vacrel->NewRelfrozenXid));

	// ... (L2000-L2036 생략: 새로 얼린 페이지 수 세기와 heap_page_is_all_visible 과의 일치 Assert)

	/*
	 * Now save details of the LP_DEAD items from the page in vacrel
	 */
	if (presult.lpdead_items > 0)
	{
		vacrel->lpdead_item_pages++;

		/*
		 * deadoffsets are collected incrementally in
		 * heap_page_prune_and_freeze() as each dead line pointer is recorded,
		 * with an indeterminate order, but dead_items_add requires them to be
		 * sorted.
		 */
		qsort(presult.deadoffsets, presult.lpdead_items, sizeof(OffsetNumber),
			  cmpOffsetNumbers);

		dead_items_add(vacrel, blkno, presult.deadoffsets, presult.lpdead_items);
	}

	/* Finally, add page-local counts to whole-VACUUM counts */
	vacrel->tuples_deleted += presult.ndeleted;
	vacrel->tuples_frozen += presult.nfrozen;
	vacrel->lpdead_items += presult.lpdead_items;
	vacrel->live_tuples += presult.live_tuples;
	vacrel->recently_dead_tuples += presult.recently_dead_tuples;

	/* Can't truncate this page */
	if (presult.hastup)
		vacrel->nonempty_pages = blkno + 1;

	/* Did we find LP_DEAD items? */
	*has_lpdead_items = (presult.lpdead_items > 0);

	Assert(!presult.all_visible || !(*has_lpdead_items));

	/*
	 * Handle setting visibility map bit based on information from the VM (as
	 * of last heap_vac_scan_next_block() call), and from all_visible and
	 * all_frozen variables
	 */
	if (!all_visible_according_to_vm && presult.all_visible)
	{
		uint8		old_vmbits;
		uint8		flags = VISIBILITYMAP_ALL_VISIBLE;

		if (presult.all_frozen)
		{
			Assert(!TransactionIdIsValid(presult.vm_conflict_horizon));
			flags |= VISIBILITYMAP_ALL_FROZEN;
		}

		// ... (L2089-L2101 생략: 페이지 비트와 VM 비트를 함께 세우는 이유)
		PageSetAllVisible(page);
		MarkBufferDirty(buf);
		old_vmbits = visibilitymap_set(vacrel->rel, blkno, buf,
									   InvalidXLogRecPtr,
									   vmbuffer, presult.vm_conflict_horizon,
									   flags);

		/*
		 * If the page wasn't already set all-visible and/or all-frozen in the
		 * VM, count it as newly set for logging.
		 */
		if ((old_vmbits & VISIBILITYMAP_ALL_VISIBLE) == 0)
		{
			vacrel->vm_new_visible_pages++;
			if (presult.all_frozen)
			{
				vacrel->vm_new_visible_frozen_pages++;
				*vm_page_frozen = true;
			}
		}
		else if ((old_vmbits & VISIBILITYMAP_ALL_FROZEN) == 0 &&
				 presult.all_frozen)
		{
			vacrel->vm_new_frozen_pages++;
			*vm_page_frozen = true;
		}
	}

	// ... (L2130-L2228 생략: VM 과 페이지 비트가 어긋난 경우의 수리, 이미 all-visible 인 페이지를 all-frozen 으로 올리는 경우)
	return presult.ndeleted;
}
```

## 동작 흐름

```text
 lazy_scan_prune(vacrel, buf, blkno, page, vmbuffer, all_visible_according_to_vm, ...)
 L1988  prune_options = HEAP_PAGE_PRUNE_FREEZE
 L1989  인덱스가 없으면 | HEAP_PAGE_PRUNE_MARK_UNUSED_NOW       2 차 패스가 필요 없다
 L1992  [10] heap_page_prune_and_freeze(..., &NewRelfrozenXid, &NewRelminMxid)
 L2041  presult.lpdead_items > 0 이면
          L2051  deadoffsets 를 정렬 (TidStore 는 정렬된 offset 을 받는다)
          L2054  dead_items_add(blkno, offsets)              TidStoreSetBlockOffsets
 L2058  tuples_deleted, tuples_frozen, live_tuples ... 누적
 L2065  hastup 이면 nonempty_pages = blkno + 1               잘라내기 상한
 L2069  *has_lpdead_items                                    [08] 이 FSM 기록 시점을 정한다
 L2078  VM 에 all-visible 이 아니었고 지금 all_visible 이면
          L2086  all_frozen 이면 flags |= ALL_FROZEN
          L2102  PageSetAllVisible(page)                      페이지 헤더의 PD_ALL_VISIBLE
          L2104  visibilitymap_set(..., flags)
 L2229  return presult.ndeleted
```

dead_items 에 들어가는 것은 TID 그 자체가 아니라 "블록 번호 → 그 블록의 offset 비트맵"이다(`tidstore.c` 머리 주석 L6-L8). 그래서 한 페이지의 죽은 항목은 한 번에 들어간다.

```text
 page 7 에서 lpdead offsets = {5, 2, 9}
 L2051  qsort -> {2, 5, 9}
 L2054  dead_items_add(vacrel, 7, {2, 5, 9}, 3)
          TidStoreSetBlockOffsets(ts, 7, {2,5,9})       radix tree 의 key 7 -> offset bitmap
          num_items += 3

 TidStore (key = BlockNumber, value = offset bitmap)
   3   -> {1, 4}
   7   -> {2, 5, 9}
   12  -> {3}
 [11] 의 vac_tid_reaped(itemptr) = TidStoreIsMember -> 인덱스 항목 하나당 한 번 조회
```

visibility map 은 힙 블록 하나당 2 비트이고, VM 페이지 하나가 힙 블록 32672 개를 덮는다(visibilitymap.c L108-L121). 힙 블록 100000 의 비트가 어디 있는지 계산하면 이렇다.

```text
 MAPSIZE             = BLCKSZ - MAXALIGN(SizeOfPageHeaderData) = 8192 - 24 = 8168 bytes
 HEAPBLOCKS_PER_BYTE = 8 / BITS_PER_HEAPBLOCK(2) = 4
 HEAPBLOCKS_PER_PAGE = 8168 * 4 = 32672

 heap block 100000
   HEAPBLK_TO_MAPBLOCK  100000 / 32672           = 3      VM fork 의 4 번째 페이지
   HEAPBLK_TO_MAPBYTE   (100000 % 32672) / 4     = 1984 / 4 = 496
   HEAPBLK_TO_OFFSET    (100000 % 4) * 2         = 0

   byte 496 의 bit 0 = ALL_VISIBLE (0x01), bit 1 = ALL_FROZEN (0x02)  (visibilitymapdefs.h L20-L21)
```

VM 비트는 VACUUM 이 켜고, 페이지를 고치는 쪽이 끈다. 그래서 "켜져 있으면 확실히 모두에게 보인다"는 한 방향 보장만 있다.

```text
 set    VACUUM           lazy_scan_prune L2102-L2104, lazy_vacuum_heap_page L2936
 clear  heap_insert      access/heap/heapam.c L2146-L2155
        heap_delete      access/heap/heapam.c L3116
        heap_update      access/heap/heapam.c L3966, L4275
 read   index-only scan  executor/nodeIndexonlyscan.c L162     VM_ALL_VISIBLE 이면 힙을 읽지 않는다
        VACUUM           [08] find_next_unskippable_block       건너뛸 블록을 고른다
```

## 결과가 쓰이는 곳

```text
 dead_items
      --> [11] lazy_vacuum -> 인덱스 bulk delete, [12] 힙 2 차 패스
 VM all-visible / all-frozen
      --> 다음 VACUUM 의 [08] 건너뛰기, index-only scan
      --> [06] 의 visibilitymap_count -> pg_class.relallvisible, relallfrozen
 NewRelfrozenXid (포인터로 넘겨 [10] 이 갱신)
      --> [06] -> [13] relfrozenxid
```

## 다루지 않는 것

VM 비트와 페이지 비트가 어긋났을 때의 WARNING 과 수리, eager scan 용 `vm_page_frozen`, VM 갱신의 WAL 기록과 standby 충돌 지평(`vm_conflict_horizon`)은 다루지 않았다.
