# heap_page_prune_and_freeze

상위: [vacuum](../README.md)

**힙 페이지 하나에서 죽은 튜플을 걷어내고, 필요하면 남은 튜플을 얼린다.** 먼저 페이지의 모든 튜플에 대해 가시성 판정(HTSV)을 한 번씩만 해서 배열에 적고, HOT 체인마다 운명을 정해 "redirect 할 것, LP_DEAD 로 만들 것, LP_UNUSED 로 만들 것, 얼릴 것" 목록을 만든다. 페이지는 그동안 건드리지 않는다. 그다음 freeze 를 할지 결정하고, critical section 안에서 목록을 한꺼번에 적용하고 WAL 레코드 하나를 남긴다. 레코드 이름은 호출 이유에 따라 `XLOG_HEAP2_PRUNE_VACUUM_SCAN`·`PRUNE_ON_ACCESS` 등으로 갈린다(pruneheap.c L2156-L2164). VACUUM 은 `HEAP_PAGE_PRUNE_FREEZE` 로 부르고, 일반 읽기의 `heap_page_prune_opt` 는 freeze 없이(options = 0) 부른다.

## 위치

`access` / `heap` / `pruneheap.c` L349-L910 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/pruneheap.c#L349-L910))

## 실제 코드

`access` / `heap` / `pruneheap.c` L349-L910 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/pruneheap.c#L349-L910))

```c
// pruneheap.c L349-L910
void
heap_page_prune_and_freeze(Relation relation, Buffer buffer,
						   GlobalVisState *vistest,
						   int options,
						   struct VacuumCutoffs *cutoffs,
						   PruneFreezeResult *presult,
						   PruneReason reason,
						   OffsetNumber *off_loc,
						   TransactionId *new_relfrozen_xid,
						   MultiXactId *new_relmin_mxid)
{
	Page		page = BufferGetPage(buffer);
	BlockNumber blockno = BufferGetBlockNumber(buffer);
	// ... (L362-L470 생략: prstate 초기화 (옵션 복사, 카운터, freeze 추적 시작값, all_visible 가정))

	// ... (L472-L491 생략: 한 번만 판정하는 이유와 역순 순회 설명)
	for (offnum = maxoff;
		 offnum >= FirstOffsetNumber;
		 offnum = OffsetNumberPrev(offnum))
	{
		ItemId		itemid = PageGetItemId(page, offnum);
		HeapTupleHeader htup;

		/*
		 * Set the offset number so that we can display it along with any
		 * error that occurred while processing this tuple.
		 */
		*off_loc = offnum;

		prstate.processed[offnum] = false;
		prstate.htsv[offnum] = -1;

		/* Nothing to do if slot doesn't contain a tuple */
		if (!ItemIdIsUsed(itemid))
		{
			heap_prune_record_unchanged_lp_unused(page, &prstate, offnum);
			continue;
		}

		if (ItemIdIsDead(itemid))
		{
			/*
			 * If the caller set mark_unused_now true, we can set dead line
			 * pointers LP_UNUSED now.
			 */
			if (unlikely(prstate.mark_unused_now))
				heap_prune_record_unused(&prstate, offnum, false);
			else
				heap_prune_record_unchanged_lp_dead(page, &prstate, offnum);
			continue;
		}

		if (ItemIdIsRedirected(itemid))
		{
			/* This is the start of a HOT chain */
			prstate.root_items[prstate.nroot_items++] = offnum;
			continue;
		}

		Assert(ItemIdIsNormal(itemid));

		/*
		 * Get the tuple's visibility status and queue it up for processing.
		 */
		htup = (HeapTupleHeader) PageGetItem(page, itemid);
		tup.t_data = htup;
		tup.t_len = ItemIdGetLength(itemid);
		ItemPointerSet(&tup.t_self, blockno, offnum);

		prstate.htsv[offnum] = heap_prune_satisfies_vacuum(&prstate, &tup,
														   buffer);

		if (!HeapTupleHeaderIsHeapOnly(htup))
			prstate.root_items[prstate.nroot_items++] = offnum;
		else
			prstate.heaponly_items[prstate.nheaponly_items++] = offnum;
	}

	// ... (L554-L559 생략: 힌트 비트가 FPI 를 냈는지 기록)
	/*
	 * Process HOT chains.
	 *
	 * We added the items to the array starting from 'maxoff', so by
	 * processing the array in reverse order, we process the items in
	 * ascending offset number order.  The order doesn't matter for
	 * correctness, but some quick micro-benchmarking suggests that this is
	 * faster.  (Earlier PostgreSQL versions, which scanned all the items on
	 * the page instead of using the root_items array, also did it in
	 * ascending offset number order.)
	 */
	for (int i = prstate.nroot_items - 1; i >= 0; i--)
	{
		offnum = prstate.root_items[i];

		/* Ignore items already processed as part of an earlier chain */
		if (prstate.processed[offnum])
			continue;

		/* see preceding loop */
		*off_loc = offnum;

		/* Process this item or chain of items */
		heap_prune_chain(page, blockno, maxoff, offnum, &prstate);
	}

	// ... (L586-L640 생략: 체인에 속하지 않은 heap-only 튜플 (abort 된 HOT 갱신) 처리)

	// ... (L642-L655 생략: 모든 항목을 한 번씩 처리했는지 Assert)

	do_prune = prstate.nredirected > 0 ||
		prstate.ndead > 0 ||
		prstate.nunused > 0;

	/*
	 * Even if we don't prune anything, if we found a new value for the
	 * pd_prune_xid field or the page was marked full, we will update the hint
	 * bit.
	 */
	do_hint = ((PageHeader) page)->pd_prune_xid != prstate.new_prune_xid ||
		PageIsFull(page);

	/*
	 * Decide if we want to go ahead with freezing according to the freeze
	 * plans we prepared, or not.
	 */
	do_freeze = false;
	if (prstate.freeze)
	{
		if (prstate.pagefrz.freeze_required)
		{
			/*
			 * heap_prepare_freeze_tuple indicated that at least one XID/MXID
			 * from before FreezeLimit/MultiXactCutoff is present.  Must
			 * freeze to advance relfrozenxid/relminmxid.
			 */
			do_freeze = true;
		}
		// ... (L685-L721 생략: 기회적 freeze (FPI 를 어차피 쓰고 페이지가 all-frozen 이 될 때))
	}

	if (do_freeze)
	{
		/*
		 * Validate the tuples we will be freezing before entering the
		 * critical section.
		 */
		heap_pre_freeze_checks(buffer, prstate.frozen, prstate.nfrozen);
	}
	// ... (L732-L751 생략: 얼리지 않기로 했을 때 all_frozen 을 내린다)

	/* Any error while applying the changes is critical */
	START_CRIT_SECTION();

	// ... (L756-L778 생략: pd_prune_xid 힌트 갱신)

	if (do_prune || do_freeze)
	{
		/* Apply the planned item changes and repair page fragmentation. */
		if (do_prune)
		{
			heap_page_prune_execute(buffer, false,
									prstate.redirected, prstate.nredirected,
									prstate.nowdead, prstate.ndead,
									prstate.nowunused, prstate.nunused);
		}

		if (do_freeze)
			heap_freeze_prepared_tuples(buffer, prstate.frozen, prstate.nfrozen);

		MarkBufferDirty(buffer);

		/*
		 * Emit a WAL XLOG_HEAP2_PRUNE_FREEZE record showing what we did
		 */
		// ... (L799-L844 생략: WAL 레코드와 standby 충돌 지평)
	}

	END_CRIT_SECTION();

	/* Copy information back for caller */
	presult->ndeleted = prstate.ndeleted;
	presult->nnewlpdead = prstate.ndead;
	presult->nfrozen = prstate.nfrozen;
	presult->live_tuples = prstate.live_tuples;
	presult->recently_dead_tuples = prstate.recently_dead_tuples;

	// ... (L856-L895 생략: all_visible, all_frozen, vm_conflict_horizon 을 호출자에게)

	if (prstate.freeze)
	{
		if (presult->nfrozen > 0)
		{
			*new_relfrozen_xid = prstate.pagefrz.FreezePageRelfrozenXid;
			*new_relmin_mxid = prstate.pagefrz.FreezePageRelminMxid;
		}
		else
		{
			*new_relfrozen_xid = prstate.pagefrz.NoFreezePageRelfrozenXid;
			*new_relmin_mxid = prstate.pagefrz.NoFreezePageRelminMxid;
		}
	}
}
```

튜플 하나의 판정이다. `HeapTupleSatisfiesVacuumHorizon` 이 RECENTLY_DEAD 라고 해도 xmax 가 OldestXmin 보다 오래됐으면 DEAD 로 바꾼다.

`access` / `heap` / `pruneheap.c` L916-L950 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/pruneheap.c#L916-L950))

```c
// pruneheap.c L916-L950
static HTSV_Result
heap_prune_satisfies_vacuum(PruneState *prstate, HeapTuple tup, Buffer buffer)
{
	HTSV_Result res;
	TransactionId dead_after;

	res = HeapTupleSatisfiesVacuumHorizon(tup, buffer, &dead_after);

	if (res != HEAPTUPLE_RECENTLY_DEAD)
		return res;

	/*
	 * For VACUUM, we must be sure to prune tuples with xmax older than
	 * OldestXmin -- a visibility cutoff determined at the beginning of
	 * vacuuming the relation. OldestXmin is used for freezing determination
	 * and we cannot freeze dead tuples' xmaxes.
	 */
	if (prstate->cutoffs &&
		TransactionIdIsValid(prstate->cutoffs->OldestXmin) &&
		NormalTransactionIdPrecedes(dead_after, prstate->cutoffs->OldestXmin))
		return HEAPTUPLE_DEAD;

	/*
	 * Determine whether or not the tuple is considered dead when compared
	 * with the provided GlobalVisState. On-access pruning does not provide
	 * VacuumCutoffs. And for vacuum, even if the tuple's xmax is not older
	 * than OldestXmin, GlobalVisTestIsRemovableXid() could find the row dead
	 * if the GlobalVisState has been updated since the beginning of vacuuming
	 * the relation.
	 */
	if (GlobalVisTestIsRemovableXid(prstate->vistest, dead_after))
		return HEAPTUPLE_DEAD;

	return res;
}
```

HOT 체인 하나의 끝맺음이다. 체인 앞쪽의 DEAD 개수(`ndeadchain`)로 세 갈래가 갈린다.

`access` / `heap` / `pruneheap.c` L1153-L1196 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/pruneheap.c#L1153-L1196))

```c
// pruneheap.c L1153-L1196
process_chain:

	if (ndeadchain == 0)
	{
		/*
		 * No DEAD tuple was found, so the chain is entirely composed of
		 * normal, unchanged tuples.  Leave it alone.
		 */
		int			i = 0;

		if (ItemIdIsRedirected(rootlp))
		{
			heap_prune_record_unchanged_lp_redirect(prstate, rootoffnum);
			i++;
		}
		for (; i < nchain; i++)
			heap_prune_record_unchanged_lp_normal(page, prstate, chainitems[i]);
	}
	else if (ndeadchain == nchain)
	{
		/*
		 * The entire chain is dead.  Mark the root line pointer LP_DEAD, and
		 * fully remove the other tuples in the chain.
		 */
		heap_prune_record_dead_or_unused(prstate, rootoffnum, ItemIdIsNormal(rootlp));
		for (int i = 1; i < nchain; i++)
			heap_prune_record_unused(prstate, chainitems[i], true);
	}
	else
	{
		/*
		 * We found a DEAD tuple in the chain.  Redirect the root line pointer
		 * to the first non-DEAD tuple, and mark as unused each intermediate
		 * item that we are able to remove from the chain.
		 */
		heap_prune_record_redirect(prstate, rootoffnum, chainitems[ndeadchain],
								   ItemIdIsNormal(rootlp));
		for (int i = 1; i < ndeadchain; i++)
			heap_prune_record_unused(prstate, chainitems[i], true);

		/* the rest of tuples in the chain are normal, unchanged tuples */
		for (int i = ndeadchain; i < nchain; i++)
			heap_prune_record_unchanged_lp_normal(page, prstate, chainitems[i]);
	}
```

## 동작 흐름

```text
 heap_page_prune_and_freeze(rel, buf, vistest, options, cutoffs, presult, ...)
 L492  for offnum = maxoff .. 1                       1 차: 항목마다 판정만
         UNUSED          -> 그대로
         LP_DEAD         -> MARK_UNUSED_NOW 면 unused, 아니면 그대로 (deadoffsets 에 다시 들어간다)
         LP_REDIRECT     -> root_items 에
         NORMAL          -> L545 htsv[offnum] = heap_prune_satisfies_vacuum
                            heap-only 가 아니면 root_items, 맞으면 heaponly_items
 L571  root 마다 heap_prune_chain                      2 차: 체인 운명을 정해 목록에
 L590  체인에 안 걸린 heap-only 처리
 L657  do_prune = redirect, dead, unused 중 하나라도 있나
 L676  freeze_required (FreezeLimit 이전 XID 가 있었다) -> do_freeze
 L754  START_CRIT_SECTION
 L785  heap_page_prune_execute                         줄 포인터 변경 + 페이지 조각 모음
 L792  heap_freeze_prepared_tuples                     xmin 에 HEAP_XMIN_FROZEN 등
 L794  MarkBufferDirty, L799 WAL (VACUUM 이면 XLOG_HEAP2_PRUNE_VACUUM_SCAN)
 L847  END_CRIT_SECTION
 L897  NewRelfrozenXid = 얼렸으면 FreezePage 쪽, 아니면 NoFreezePage 쪽 추적값
```

판정은 다섯 결과 중 하나이고(heapam.h L124-L128), VACUUM 이 지울 수 있는 것은 DEAD 뿐이다. RECENTLY_DEAD 가 DEAD 로 바뀌는 조건이 OldestXmin 이다.

```text
 OldestXmin = 1000, 모든 xmin 은 커밋됨

 tuple  xmax               HTSV (horizon)                      after L933-L947              prune
 t1     none               LIVE                                LIVE                         남긴다
 t2     990 committed      RECENTLY_DEAD, dead_after = 990     DEAD (990 < OldestXmin)      지운다
 t3     1005 committed     RECENTLY_DEAD, dead_after = 1005    vistest 가 1005 를 지나쳤으면 DEAD, 아니면 RECENTLY_DEAD
 t4     1010 in progress   DELETE_IN_PROGRESS                  DELETE_IN_PROGRESS           남긴다
 t5     (xmin aborted)     DEAD                                DEAD                         지운다
```

HOT 체인이 있으면 인덱스 항목 하나가 체인의 머리(root)만 가리키므로, 머리 줄 포인터는 남기고 가운데를 걷어낸다. 한 행을 HOT 으로 두 번 고친 페이지다(L1153-L1196).

```text
 index -> (7,1)

 before   lp1 NORMAL  v1  HOT_UPDATED  DEAD   xmax 가 OldestXmin 전에 커밋
          lp2 NORMAL  v2  HEAP_ONLY    DEAD   xmax 가 OldestXmin 전에 커밋
          lp3 NORMAL  v3  HEAP_ONLY    LIVE
          chain = [lp1, lp2, lp3], ndeadchain = 2

 ndeadchain (2) < nchain (3) -> 세 번째 갈래 (L1182-L1196)
          lp1  REDIRECT -> 3        heap_prune_record_redirect
          lp2  UNUSED               heap_prune_record_unused (heap-only 라 인덱스가 가리키지 않는다)
          lp3  NORMAL  v3           그대로

 after    index -> (7,1) -> redirect -> lp3 (v3)
          LP_DEAD 가 없으니 dead_items 에 들어갈 것도, 인덱스에서 지울 것도 없다

 v3 까지 죽었다면 ndeadchain == nchain -> lp1 LP_DEAD (dead_items 로), lp2, lp3 UNUSED (L1171-L1180)
```

freeze 는 "이 페이지를 얼린다/안 얼린다"를 페이지 단위로 정한다. 튜플마다 준비만 해 두고(`heap_prepare_freeze_tuple`), FreezeLimit 이전 XID 가 하나라도 있으면 페이지 전체의 준비분을 적용한다.

```text
 FreezeLimit = 950, OldestXmin = 1000

 tuple   xmin   can freeze (xmin < OldestXmin)   must freeze (xmin < FreezeLimit)
 t1      920    yes                              yes   -> freeze_required = true
 t2      980    yes                              no
 t3      1003   no                               no

 do_freeze = true -> t1, t2 의 infomask 에 HEAP_XMIN_FROZEN (heapam.c L7513-L7518)
 t3 은 얼리지 않는다 -> 페이지는 all_frozen 이 아니다
```

## 결과가 쓰이는 곳

```text
 presult->deadoffsets, lpdead_items
      --> [09] 가 dead_items 에 넣는다
 presult->all_visible, all_frozen
      --> [09] 가 visibility map 비트를 정한다
 presult->ndeleted, live_tuples, recently_dead_tuples
      --> [06] 의 통계와 pg_class.reltuples
 *new_relfrozen_xid
      --> [06] 의 NewRelfrozenXid
 XLOG_HEAP2_PRUNE_VACUUM_SCAN 레코드
      --> 복구와 standby 가 같은 변경을 재생하고, 그 레코드의 충돌 지평으로 standby 쿼리를 취소할 수 있다
```

## 다루지 않는 것

`heap_prune_chain` 의 체인 따라가기 전체, abort 된 HOT 갱신의 고아 heap-only 튜플, 기회적 freeze 의 FPI 판정, MultiXact xmax 의 freeze(`FreezeMultiXactId`), `heap_page_prune_execute` 의 조각 모음, WAL 레코드 형식과 standby 충돌 지평 계산은 다루지 않았다.
