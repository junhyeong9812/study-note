# lazy_vacuum

상위: [vacuum](../README.md)

**모아 둔 dead TID 로 인덱스를 정리하고, 이어서 힙 2 차 정리를 부른다.** 먼저 인덱스 정리를 아예 건너뛸지 본다. 죽은 항목이 있는 페이지가 테이블의 2 % 미만이고 TID 저장소가 32 MB 미만이면 "없는 것과 같다"고 보고 인덱스와 힙 2 차를 모두 건너뛴다. 아니면 `lazy_vacuum_all_indexes` 가 인덱스마다 AM 의 `ambulkdelete` 를 부르고, 인덱스 AM 은 자기 항목을 전부 훑으며 콜백 `vac_tid_reaped` 로 "이 TID 가 dead_items 에 있나"를 물어 지운다. 모든 인덱스가 끝나야 [12] 가 힙의 LP_DEAD 를 LP_UNUSED 로 바꿀 수 있다. 끝으로 dead_items 를 비운다.

## 위치

`access` / `heap` / `vacuumlazy.c` L2463-L2578 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L2463-L2578))

## 실제 코드

`access` / `heap` / `vacuumlazy.c` L2463-L2578 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L2463-L2578))

```c
// vacuumlazy.c L2463-L2578
static void
lazy_vacuum(LVRelState *vacrel)
{
	bool		bypass;

	/* Should not end up here with no indexes */
	Assert(vacrel->nindexes > 0);
	Assert(vacrel->lpdead_item_pages > 0);

	if (!vacrel->do_index_vacuuming)
	{
		Assert(!vacrel->do_index_cleanup);
		dead_items_reset(vacrel);
		return;
	}

	// ... (L2479-L2497 생략: 건너뛰기 최적화의 동기 (HOT 이 거의 다 먹히는 테이블))
	bypass = false;
	if (vacrel->consider_bypass_optimization && vacrel->rel_pages > 0)
	{
		BlockNumber threshold;

		Assert(vacrel->num_index_scans == 0);
		Assert(vacrel->lpdead_items == vacrel->dead_items_info->num_items);
		Assert(vacrel->do_index_vacuuming);
		Assert(vacrel->do_index_cleanup);

		// ... (L2508-L2529 생략: 2 % 기준과 32 MB 상한의 이유)
		threshold = (double) vacrel->rel_pages * BYPASS_THRESHOLD_PAGES;
		bypass = (vacrel->lpdead_item_pages < threshold &&
				  TidStoreMemoryUsage(vacrel->dead_items) < 32 * 1024 * 1024);
	}

	if (bypass)
	{
		// ... (L2537-L2546 생략: 건너뛸 때의 설명)
		vacrel->do_index_vacuuming = false;
	}
	else if (lazy_vacuum_all_indexes(vacrel))
	{
		/*
		 * We successfully completed a round of index vacuuming.  Do related
		 * heap vacuuming now.
		 */
		lazy_vacuum_heap_rel(vacrel);
	}
	else
	{
		// ... (L2559-L2569 생략: failsafe 로 중단된 경우의 설명)
		Assert(VacuumFailsafeActive);
	}

	/*
	 * Forget the LP_DEAD items that we just vacuumed (or just decided to not
	 * vacuum)
	 */
	dead_items_reset(vacrel);
}
```

인덱스 정리의 본체다. failsafe 가 켜지면 중간에 멈춘다.

`access` / `heap` / `vacuumlazy.c` L2588-L2686 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L2588-L2686))

```c
// vacuumlazy.c L2588-L2686
static bool
lazy_vacuum_all_indexes(LVRelState *vacrel)
{
	bool		allindexes = true;
	double		old_live_tuples = vacrel->rel->rd_rel->reltuples;
	// ... (L2593-L2603 생략: 진행 상태 배열)

	Assert(vacrel->nindexes > 0);
	Assert(vacrel->do_index_vacuuming);
	Assert(vacrel->do_index_cleanup);

	/* Precheck for XID wraparound emergencies */
	if (lazy_check_wraparound_failsafe(vacrel))
	{
		/* Wraparound emergency -- don't even start an index scan */
		return false;
	}

	// ... (L2616-L2622 생략: 진행 상태 보고)

	if (!ParallelVacuumIsActive(vacrel))
	{
		for (int idx = 0; idx < vacrel->nindexes; idx++)
		{
			Relation	indrel = vacrel->indrels[idx];
			IndexBulkDeleteResult *istat = vacrel->indstats[idx];

			vacrel->indstats[idx] = lazy_vacuum_one_index(indrel, istat,
														  old_live_tuples,
														  vacrel);

			/* Report the number of indexes vacuumed */
			pgstat_progress_update_param(PROGRESS_VACUUM_INDEXES_PROCESSED,
										 idx + 1);

			if (lazy_check_wraparound_failsafe(vacrel))
			{
				/* Wraparound emergency -- end current index scan */
				allindexes = false;
				break;
			}
		}
	}
	else
	{
		/* Outsource everything to parallel variant */
		parallel_vacuum_bulkdel_all_indexes(vacrel->pvs, old_live_tuples,
											vacrel->num_index_scans);

		/*
		 * Do a postcheck to consider applying wraparound failsafe now.  Note
		 * that parallel VACUUM only gets the precheck and this postcheck.
		 */
		if (lazy_check_wraparound_failsafe(vacrel))
			allindexes = false;
	}

	// ... (L2661-L2678 생략: 일관성 Assert 와 진행 상태 설명)
	vacrel->num_index_scans++;
	// ... (L2680-L2683 생략: 진행 상태 보고)

	return allindexes;
}
```

인덱스 AM 에 넘기는 콜백이다. 인덱스 항목 하나마다 한 번씩 불린다.

`commands` / `vacuum.c` L2645-L2703 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L2645-L2703))

```c
// vacuum.c L2645-L2703
/*
 *	vac_bulkdel_one_index() -- bulk-deletion for index relation.
 *
 * Returns bulk delete stats derived from input stats
 */
IndexBulkDeleteResult *
vac_bulkdel_one_index(IndexVacuumInfo *ivinfo, IndexBulkDeleteResult *istat,
					  TidStore *dead_items, VacDeadItemsInfo *dead_items_info)
{
	/* Do bulk deletion */
	istat = index_bulk_delete(ivinfo, istat, vac_tid_reaped,
							  dead_items);

	ereport(ivinfo->message_level,
			(errmsg("scanned index \"%s\" to remove %" PRId64 " row versions",
					RelationGetRelationName(ivinfo->index),
					dead_items_info->num_items)));

	return istat;
}
// ... (L2665-L2691 생략: amvacuumcleanup 쪽 (vac_cleanup_one_index))
/*
 *	vac_tid_reaped() -- is a particular tid deletable?
 *
 *		This has the right signature to be an IndexBulkDeleteCallback.
 */
static bool
vac_tid_reaped(ItemPointer itemptr, void *state)
{
	TidStore   *dead_items = (TidStore *) state;

	return TidStoreIsMember(dead_items, itemptr);
}
```

dead_items 의 크기 상한은 `maintenance_work_mem`(autovacuum worker 면 `autovacuum_work_mem` 이 -1 이 아닐 때 그 값)이다.

`access` / `heap` / `vacuumlazy.c` L3496-L3556 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L3496-L3556))

```c
// vacuumlazy.c L3496-L3556
static void
dead_items_alloc(LVRelState *vacrel, int nworkers)
{
	VacDeadItemsInfo *dead_items_info;
	int			vac_work_mem = AmAutoVacuumWorkerProcess() &&
		autovacuum_work_mem != -1 ?
		autovacuum_work_mem : maintenance_work_mem;

	// ... (L3504-L3544 생략: 병렬 vacuum 이면 동적 공유 메모리에 만든다)
	/*
	 * Serial VACUUM case. Allocate both dead_items and dead_items_info
	 * locally.
	 */

	dead_items_info = (VacDeadItemsInfo *) palloc(sizeof(VacDeadItemsInfo));
	dead_items_info->max_bytes = vac_work_mem * (Size) 1024;
	dead_items_info->num_items = 0;
	vacrel->dead_items_info = dead_items_info;

	vacrel->dead_items = TidStoreCreateLocal(dead_items_info->max_bytes, true);
}
```

## 동작 흐름

```text
 lazy_vacuum(vacrel)
 L2472  do_index_vacuuming = false (INDEX_CLEANUP off) -> dead_items_reset, return
 L2530  threshold = rel_pages * 0.02                      BYPASS_THRESHOLD_PAGES (L187)
 L2531  bypass = lpdead_item_pages < threshold && TidStore < 32 MB
          첫 번째 lazy_vacuum 이고 consider_bypass_optimization 일 때만
 L2535  bypass -> do_index_vacuuming = false               LP_DEAD 는 힙에 남는다
 L2549  lazy_vacuum_all_indexes
          L2610  failsafe 면 바로 false
          L2631  인덱스마다 lazy_vacuum_one_index -> vac_bulkdel_one_index
                   index_bulk_delete(ivinfo, istat, vac_tid_reaped, dead_items)  (indexam.c L795)
                     btree 면 btbulkdelete -> btvacuumscan: 모든 leaf 를 읽으며 callback(&itup->t_tid)
          L2679  num_index_scans++
 L2555  성공하면 [12] lazy_vacuum_heap_rel
 L2577  dead_items_reset                                   TidStore 를 새로 만든다
```

건너뛰기 기준을 숫자로 보면 이렇다.

```text
 rel_pages = 10,000   threshold = 10,000 * 0.02 = 200 pages

 lpdead_item_pages   TidStoreMemoryUsage   bypass   결과
 150                 1 MB                  true     인덱스, 힙 2 차 모두 건너뜀. LP_DEAD 150 페이지는 다음 VACUUM 까지 남는다
 150                 40 MB                 false    32 MB 이상이면 건너뛰지 않는다
 450                 3 MB                  false    인덱스 정리 -> 힙 2 차
```

인덱스 쪽에서 일어나는 일은 TID 대조다. 인덱스 AM 은 힙을 읽지 않고, 자기 항목의 TID 가 dead_items 에 있는지만 묻는다.

```text
 dead_items:  7 -> {1, 2}, 12 -> {3}

 btvacuumscan (nbtree.c L1186) 이 leaf 를 처음부터 끝까지
   leaf A   (key 10, tid (3,4))    vac_tid_reaped -> TidStoreIsMember -> false   남긴다
            (key 11, tid (7,1))                                    -> true    지운다
            (key 11, tid (7,3))                                    -> false   남긴다
   leaf B   (key 20, tid (7,2))                                    -> true    지운다
            (key 25, tid (12,3))                                   -> true    지운다
   (nbtree.c L1525 의 callback(&itup->t_tid, callback_state))

 인덱스가 여러 개면 각 인덱스를 이렇게 한 번씩 전부 읽는다
 dead_items 가 중간에 차서 lazy_vacuum 이 두 번 불리면 인덱스도 두 번 전부 읽는다
```

`maintenance_work_mem` 기본값 64 MB(guc_tables.c L2600)면 `max_bytes = 65536 * 1024 = 67,108,864` 바이트다(L3551). TidStore 는 블록마다 offset 비트맵을 두므로, 같은 페이지에 죽은 항목이 몰릴수록 같은 메모리로 더 많은 TID 를 담는다.

## 결과가 쓰이는 곳

```text
 인덱스에서 지워진 항목
      --> 이제 dead TID 를 가리키는 인덱스 항목이 없다 -> [12] 가 LP_UNUSED 로 바꿔도 안전
 vacrel->indstats[]
      --> lazy_cleanup_all_indexes (amvacuumcleanup), update_relstats_all_indexes
 bypass 로 남은 LP_DEAD
      --> 그 페이지는 all-visible 이 될 수 없다 (LP_DEAD 가 있으면 [10] 이 all_visible 을 false 로 돌려준다)
```

## 다루지 않는 것

병렬 인덱스 vacuum(`parallel_vacuum_bulkdel_all_indexes`), B-tree 의 `btvacuumscan` 내부(페이지 삭제, posting list, 재활용 가능한 페이지), 인덱스 cleanup 단계(`amvacuumcleanup`), wraparound failsafe(`lazy_check_wraparound_failsafe`), TidStore 의 radix tree 구조는 다루지 않았다.
