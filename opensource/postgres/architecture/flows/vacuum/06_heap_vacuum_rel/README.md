# heap_vacuum_rel

상위: [vacuum](../README.md)

**힙 테이블 하나에 대한 lazy vacuum 의 지휘자다.** 인덱스를 열고, [07] 로 OldestXmin·FreezeLimit 과 aggressive 여부를 정하고, 죽은 TID 를 담을 저장소(dead_items)를 만든 뒤 [08] `lazy_scan_heap` 에 일을 넘긴다. 돌아오면 인덱스 통계를 고치고, 끝의 빈 페이지를 잘라내고, 이번 VACUUM 이 실제로 본 가장 오래된 XID 를 새 `relfrozenxid` 로 [13] `vac_update_relstats` 에 넘긴다. 단, 일반 VACUUM 이 all-visible 페이지를 건너뛰었다면 그 안의 XID 를 못 봤으므로 `relfrozenxid` 를 올리지 않는다.

## 위치

`access` / `heap` / `vacuumlazy.c` L614-L1161 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L614-L1161))

## 실제 코드

`access` / `heap` / `vacuumlazy.c` L614-L1161 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L614-L1161))

```c
// vacuumlazy.c L614-L1161
void
// ... (L615-L679 생략: 지역 변수, 계측, 오류 문맥 콜백 설정)
	/* Set up high level stuff about rel and its indexes */
	vacrel->rel = rel;
	vac_open_indexes(vacrel->rel, RowExclusiveLock, &vacrel->nindexes,
					 &vacrel->indrels);
	vacrel->bstrategy = bstrategy;
	// ... (L685-L709 생략: 계측용 인덱스 이름 복사와 옵션 Assert)
	VacuumFailsafeActive = false;
	vacrel->consider_bypass_optimization = true;
	vacrel->do_index_vacuuming = true;
	vacrel->do_index_cleanup = true;
	vacrel->do_rel_truncate = (params->truncate != VACOPTVALUE_DISABLED);
	if (params->index_cleanup == VACOPTVALUE_DISABLED)
	{
		/* Force disable index vacuuming up-front */
		vacrel->do_index_vacuuming = false;
		vacrel->do_index_cleanup = false;
	}
	else if (params->index_cleanup == VACOPTVALUE_ENABLED)
	{
		/* Force index vacuuming.  Note that failsafe can still bypass. */
		vacrel->consider_bypass_optimization = false;
	}
	else
	{
		/* Default/auto, make all decisions dynamically */
		Assert(params->index_cleanup == VACOPTVALUE_AUTO);
	}

	// ... (L732-L760 생략: 카운터 초기화)
	/*
	 * Get cutoffs that determine which deleted tuples are considered DEAD,
	 * not just RECENTLY_DEAD, and which XIDs/MXIDs to freeze.  Then determine
	 * the extent of the blocks that we'll scan in lazy_scan_heap.  It has to
	 * happen in this order to ensure that the OldestXmin cutoff field works
	 * as an upper bound on the XIDs stored in the pages we'll actually scan
	 * (NewRelfrozenXid tracking must never be allowed to miss unfrozen XIDs).
	 *
	 * Next acquire vistest, a related cutoff that's used in pruning.  We use
	 * vistest in combination with OldestXmin to ensure that
	 * heap_page_prune_and_freeze() always removes any deleted tuple whose
	 * xmax is < OldestXmin.  lazy_scan_prune must never become confused about
	 * whether a tuple should be frozen or removed.  (In the future we might
	 * want to teach lazy_scan_prune to recompute vistest from time to time,
	 * to increase the number of dead tuples it can prune away.)
	 */
	vacrel->aggressive = vacuum_get_cutoffs(rel, params, &vacrel->cutoffs);
	vacrel->rel_pages = orig_rel_pages = RelationGetNumberOfBlocks(rel);
	vacrel->vistest = GlobalVisTestFor(rel);

	/* Initialize state used to track oldest extant XID/MXID */
	vacrel->NewRelfrozenXid = vacrel->cutoffs.OldestXmin;
	vacrel->NewRelminMxid = vacrel->cutoffs.OldestMxact;

	/*
	 * Initialize state related to tracking all-visible page skipping. This is
	 * very important to determine whether or not it is safe to advance the
	 * relfrozenxid/relminmxid.
	 */
	vacrel->skippedallvis = false;
	skipwithvm = true;
	if (params->options & VACOPT_DISABLE_PAGE_SKIPPING)
	{
		/*
		 * Force aggressive mode, and disable skipping blocks using the
		 * visibility map (even those set all-frozen)
		 */
		vacrel->aggressive = true;
		skipwithvm = false;
	}

	vacrel->skipwithvm = skipwithvm;

	/*
	 * Set up eager scan tracking state. This must happen after determining
	 * whether or not the vacuum must be aggressive, because only normal
	 * vacuums use the eager scan algorithm.
	 */
	heap_vacuum_eager_scan_setup(vacrel, params);

	// ... (L811-L823 생략: VERBOSE 면 aggressive 여부를 INFO 로)

	/*
	 * Allocate dead_items memory using dead_items_alloc.  This handles
	 * parallel VACUUM initialization as part of allocating shared memory
	 * space used for dead_items.  (But do a failsafe precheck first, to
	 * ensure that parallel VACUUM won't be attempted at all when relfrozenxid
	 * is already dangerously old.)
	 */
	lazy_check_wraparound_failsafe(vacrel);
	dead_items_alloc(vacrel, params->nworkers);

	/*
	 * Call lazy_scan_heap to perform all required heap pruning, index
	 * vacuuming, and heap vacuuming (plus related processing)
	 */
	lazy_scan_heap(vacrel);

	/*
	 * Free resources managed by dead_items_alloc.  This ends parallel mode in
	 * passing when necessary.
	 */
	dead_items_cleanup(vacrel);
	Assert(!IsInParallelMode());

	/*
	 * Update pg_class entries for each of rel's indexes where appropriate.
	 *
	 * Unlike the later update to rel's pg_class entry, this is not critical.
	 * Maintains relpages/reltuples statistics used by the planner only.
	 */
	if (vacrel->do_index_cleanup)
		update_relstats_all_indexes(vacrel);

	/* Done with rel's indexes */
	vac_close_indexes(vacrel->nindexes, vacrel->indrels, NoLock);

	/* Optionally truncate rel */
	if (should_attempt_truncation(vacrel))
		lazy_truncate_heap(vacrel);

	// ... (L864-L885 생략: 진행 상태 보고와 relfrozenxid 범위 Assert)
	if (vacrel->skippedallvis)
	{
		/*
		 * Must keep original relfrozenxid in a non-aggressive VACUUM that
		 * chose to skip an all-visible page range.  The state that tracks new
		 * values will have missed unfrozen XIDs from the pages we skipped.
		 */
		Assert(!vacrel->aggressive);
		vacrel->NewRelfrozenXid = InvalidTransactionId;
		vacrel->NewRelminMxid = InvalidMultiXactId;
	}

	/*
	 * For safety, clamp relallvisible to be not more than what we're setting
	 * pg_class.relpages to
	 */
	new_rel_pages = vacrel->rel_pages;	/* After possible rel truncation */
	visibilitymap_count(rel, &new_rel_allvisible, &new_rel_allfrozen);
	if (new_rel_allvisible > new_rel_pages)
		new_rel_allvisible = new_rel_pages;

	/*
	 * An all-frozen block _must_ be all-visible. As such, clamp the count of
	 * all-frozen blocks to the count of all-visible blocks. This matches the
	 * clamping of relallvisible above.
	 */
	if (new_rel_allfrozen > new_rel_allvisible)
		new_rel_allfrozen = new_rel_allvisible;

	/*
	 * Now actually update rel's pg_class entry.
	 *
	 * In principle new_live_tuples could be -1 indicating that we (still)
	 * don't know the tuple count.  In practice that can't happen, since we
	 * scan every page that isn't skipped using the visibility map.
	 */
	vac_update_relstats(rel, new_rel_pages, vacrel->new_live_tuples,
						new_rel_allvisible, new_rel_allfrozen,
						vacrel->nindexes > 0,
						vacrel->NewRelfrozenXid, vacrel->NewRelminMxid,
						&frozenxid_updated, &minmulti_updated, false);

	// ... (L928-L1160 생략: 통계 보고와 log_autovacuum_min_duration 로그 메시지)
}
```

## 동작 흐름

```text
 heap_vacuum_rel(rel, params, bstrategy)
 L682  vac_open_indexes(RowExclusiveLock)
 L712  do_index_vacuuming = do_index_cleanup = true      index_cleanup = off 면 둘 다 false
 L777  aggressive = [07] vacuum_get_cutoffs(rel, params, &cutoffs)
 L778  rel_pages = RelationGetNumberOfBlocks(rel)         이 시점의 크기까지만 본다
 L779  vistest = GlobalVisTestFor(rel)                     prune 이 쓰는 가시성 지평
 L782  NewRelfrozenXid = OldestXmin                       "본 것 중 가장 오래된 XID" 의 시작값
 L792  DISABLE_PAGE_SKIPPING 이면 aggressive, VM 건너뛰기 끔
 L833  dead_items_alloc                                    TidStore, 상한 maintenance_work_mem KB * 1024 바이트
                                                            (autovacuum worker 는 autovacuum_work_mem 이 -1 이 아니면 그 값, L3500-L3502, L3551)
 L839  [08] lazy_scan_heap                                 prune, freeze, 인덱스, 힙 2 차
 L855  update_relstats_all_indexes
 L862  lazy_truncate_heap                                  끝의 빈 페이지 (AccessExclusiveLock 을 잠깐 시도)
 L886  skippedallvis 면 NewRelfrozenXid = Invalid           relfrozenxid 를 올리지 않는다
 L903  visibilitymap_count -> relallvisible, relallfrozen
 L922  [13] vac_update_relstats(..., NewRelfrozenXid, ...)
```

`relfrozenxid` 를 얼마나 올릴 수 있는지는 VACUUM 이 페이지를 돌며 `NewRelfrozenXid` 를 줄여 가는 방식으로 정해진다. 시작값은 OldestXmin 이고, 얼리지 않고 남긴 XID 를 볼 때마다 그보다 작으면 내려간다(`heap_tuple_should_freeze`, heapam.c L8141-L8142).

```text
 OldestXmin = 1,000,000   FreezeLimit = 950,000   예전 relfrozenxid = 900,000
 NewRelfrozenXid 시작값 = OldestXmin = 1,000,000

 page 0   xmin 920,000, 980,000
          920,000 < FreezeLimit -> freeze_required, 페이지를 얼린다
          둘 다 OldestXmin 미만이라 둘 다 얼고, 남은 XID 가 없다
          NewRelfrozenXid = 1,000,000

 page 1   xmin 960,000, 990,000
          둘 다 FreezeLimit 이상 -> 얼리지 않는다 (기회적 freeze 도 없다고 할 때)
          남긴 XID 중 가장 작은 것이 960,000
          NewRelfrozenXid = 960,000

 page 2   VM 에 all-frozen -> 건너뛴다. 얼지 않은 XID 가 없으니 추적에 영향 없다
          NewRelfrozenXid = 960,000

 끝       vac_update_relstats: relfrozenxid 900,000 -> 960,000

 page 2 가 all-frozen 이 아니라 all-visible 이었고 일반 VACUUM 이 건너뛰었다면
   skippedallvis = true -> NewRelfrozenXid = Invalid -> relfrozenxid 는 900,000 그대로 (L886-L896)
```

## 결과가 쓰이는 곳

```text
 vacrel->aggressive
      --> [08] 이 all-visible 페이지를 건너뛸 수 있는지 정한다
      --> [08] 이 cleanup lock 을 못 잡았을 때 기다릴지 정한다
 dead_items (TidStore)
      --> [09] 가 채우고 [11] 이 인덱스에 넘기고 [12] 가 비운다
 NewRelfrozenXid
      --> [13] 이 pg_class.relfrozenxid 로 쓴다
```

## 다루지 않는 것

병렬 vacuum 준비(`dead_items_alloc` 의 `parallel_vacuum_init`), wraparound failsafe, eager scan 설정, 힙 잘라내기(`lazy_truncate_heap`, `count_nondeletable_pages`), 인덱스 통계 갱신, VERBOSE·autovacuum 로그 메시지 조립은 다루지 않았다.
