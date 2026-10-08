# lazy_scan_heap

상위: [vacuum](../README.md)

**힙을 앞에서부터 한 번 훑는 VACUUM 의 본 루프다.** 읽을 블록은 read stream 콜백이 visibility map 을 보고 고르므로, all-frozen 페이지와 (일반 VACUUM 이면) all-visible 페이지의 긴 구간은 읽지도 않는다. 읽은 페이지마다 cleanup lock 을 시도해 잡히면 [09] `lazy_scan_prune` 으로 prune·freeze 하고, 못 잡으면 `lazy_scan_noprune` 으로 죽은 TID 만 모은다. 모은 TID 가 dead_items 상한(`maintenance_work_mem`, autovacuum 이면 `autovacuum_work_mem`)을 넘으면 스캔을 멈추고 [11] `lazy_vacuum` 으로 인덱스와 힙 2 차 정리를 한 바퀴 돌린 뒤 이어 간다. 끝까지 읽으면 남은 TID 로 [11] 을 한 번 더 부르고 인덱스 cleanup 을 한다.

## 위치

`access` / `heap` / `vacuumlazy.c` L1199-L1559 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L1199-L1559))

## 실제 코드

`access` / `heap` / `vacuumlazy.c` L1199-L1559 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L1199-L1559))

```c
// vacuumlazy.c L1199-L1559
static void
lazy_scan_heap(LVRelState *vacrel)
{
	// ... (L1202-L1235 생략: 지역 변수, 진행 상태 초기화)
	stream = read_stream_begin_relation(READ_STREAM_MAINTENANCE,
										vacrel->bstrategy,
										vacrel->rel,
										MAIN_FORKNUM,
										heap_vac_scan_next_block,
										vacrel,
										sizeof(uint8));

	while (true)
	{
		Buffer		buf;
		Page		page;
		uint8		blk_info = 0;
		int			ndeleted = 0;
		bool		has_lpdead_items;
		void	   *per_buffer_data = NULL;
		bool		vm_page_frozen = false;
		bool		got_cleanup_lock = false;

		vacuum_delay_point(false);

		// ... (L1257-L1268 생략: 주기적 wraparound failsafe 검사)

		/*
		 * Consider if we definitely have enough space to process TIDs on page
		 * already.  If we are close to overrunning the available space for
		 * dead_items TIDs, pause and do a cycle of vacuuming before we tackle
		 * this page. However, let's force at least one page-worth of tuples
		 * to be stored as to ensure we do at least some work when the memory
		 * configured is so low that we run out before storing anything.
		 */
		if (vacrel->dead_items_info->num_items > 0 &&
			TidStoreMemoryUsage(vacrel->dead_items) > vacrel->dead_items_info->max_bytes)
		{
			// ... (L1281-L1291 생략: 긴 인덱스 정리 전에 VM 핀을 놓는다)

			/* Perform a round of index and heap vacuuming */
			vacrel->consider_bypass_optimization = false;
			lazy_vacuum(vacrel);

			// ... (L1297-L1322 생략: 한 바퀴 뒤 FSM 정리, failsafe 면 ring buffer 해제)

		buf = read_stream_next_buffer(stream, &per_buffer_data);

		/* The relation is exhausted. */
		if (!BufferIsValid(buf))
			break;

		blk_info = *((uint8 *) per_buffer_data);
		CheckBufferIsPinnedOnce(buf);
		page = BufferGetPage(buf);
		blkno = BufferGetBlockNumber(buf);

		vacrel->scanned_pages++;
		if (blk_info & VAC_BLK_WAS_EAGER_SCANNED)
			vacrel->eager_scanned_pages++;

		// ... (L1339-L1348 생략: 진행 상태와 오류 문맥)
		visibilitymap_pin(vacrel->rel, blkno, &vmbuffer);

		/*
		 * We need a buffer cleanup lock to prune HOT chains and defragment
		 * the page in lazy_scan_prune.  But when it's not possible to acquire
		 * a cleanup lock right away, we may be able to settle for reduced
		 * processing using lazy_scan_noprune.
		 */
		got_cleanup_lock = ConditionalLockBufferForCleanup(buf);

		if (!got_cleanup_lock)
			LockBuffer(buf, BUFFER_LOCK_SHARE);

		/* Check for new or empty pages before lazy_scan_[no]prune call */
		if (lazy_scan_new_or_empty(vacrel, buf, blkno, page, !got_cleanup_lock,
								   vmbuffer))
		{
			/* Processed as new/empty page (lock and pin released) */
			continue;
		}

		/*
		 * If we didn't get the cleanup lock, we can still collect LP_DEAD
		 * items in the dead_items area for later vacuuming, count live and
		 * recently dead tuples for vacuum logging, and determine if this
		 * block could later be truncated. If we encounter any xid/mxids that
		 * require advancing the relfrozenxid/relminxid, we'll have to wait
		 * for a cleanup lock and call lazy_scan_prune().
		 */
		if (!got_cleanup_lock &&
			!lazy_scan_noprune(vacrel, buf, blkno, page, &has_lpdead_items))
		{
			/*
			 * lazy_scan_noprune could not do all required processing.  Wait
			 * for a cleanup lock, and call lazy_scan_prune in the usual way.
			 */
			Assert(vacrel->aggressive);
			LockBuffer(buf, BUFFER_LOCK_UNLOCK);
			LockBufferForCleanup(buf);
			got_cleanup_lock = true;
		}

		/*
		 * If we have a cleanup lock, we must now prune, freeze, and count
		 * tuples. We may have acquired the cleanup lock originally, or we may
		 * have gone back and acquired it after lazy_scan_noprune() returned
		 * false. Either way, the page hasn't been processed yet.
		 *
		 * Like lazy_scan_noprune(), lazy_scan_prune() will count
		 * recently_dead_tuples and live tuples for vacuum logging, determine
		 * if the block can later be truncated, and accumulate the details of
		 * remaining LP_DEAD line pointers on the page into dead_items. These
		 * dead items include those pruned by lazy_scan_prune() as well as
		 * line pointers previously marked LP_DEAD.
		 */
		if (got_cleanup_lock)
			ndeleted = lazy_scan_prune(vacrel, buf, blkno, page,
									   vmbuffer,
									   blk_info & VAC_BLK_ALL_VISIBLE_ACCORDING_TO_VM,
									   &has_lpdead_items, &vm_page_frozen);

		// ... (L1410-L1463 생략: eager scan 성공·실패 계산)

		/*
		 * Now drop the buffer lock and, potentially, update the FSM.
		 *
		 * Our goal is to update the freespace map the last time we touch the
		 * page. If we'll process a block in the second pass, we may free up
		 * additional space on the page, so it is better to update the FSM
		 * after the second pass. If the relation has no indexes, or if index
		 * vacuuming is disabled, there will be no second heap pass; if this
		 * particular page has no dead items, the second heap pass will not
		 * touch this page. So, in those cases, update the FSM now.
		 *
		 * Note: In corner cases, it's possible to miss updating the FSM
		 * entirely. If index vacuuming is currently enabled, we'll skip the
		 * FSM update now. But if failsafe mode is later activated, or there
		 * are so few dead tuples that index vacuuming is bypassed, there will
		 * also be no opportunity to update the FSM later, because we'll never
		 * revisit this page. Since updating the FSM is desirable but not
		 * absolutely required, that's OK.
		 */
		if (vacrel->nindexes == 0
			|| !vacrel->do_index_vacuuming
			|| !has_lpdead_items)
		{
			Size		freespace = PageGetHeapFreeSpace(page);

			UnlockReleaseBuffer(buf);
			RecordPageWithFreeSpace(vacrel->rel, blkno, freespace);

			// ... (L1493-L1505 생략: 인덱스 없는 테이블의 주기적 FSM 정리)
		}
		else
			UnlockReleaseBuffer(buf);
	}

	vacrel->blkno = InvalidBlockNumber;
	if (BufferIsValid(vmbuffer))
		ReleaseBuffer(vmbuffer);

	// ... (L1515-L1533 생략: reltuples 추정)

	read_stream_end(stream);

	/*
	 * Do index vacuuming (call each index's ambulkdelete routine), then do
	 * related heap vacuuming
	 */
	if (vacrel->dead_items_info->num_items > 0)
		lazy_vacuum(vacrel);

	// ... (L1544-L1554 생략: 남은 FSM 정리)

	/* Do final index cleanup (call each index's amvacuumcleanup routine) */
	if (vacrel->nindexes > 0 && vacrel->do_index_cleanup)
		lazy_cleanup_all_indexes(vacrel);
}
```

건너뛸 수 있는 블록을 visibility map 으로 찾는 부분이다. read stream 콜백 `heap_vac_scan_next_block` 이 부른다.

`access` / `heap` / `vacuumlazy.c` L1690-L1786 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/vacuumlazy.c#L1690-L1786))

```c
// vacuumlazy.c L1690-L1786
static void
find_next_unskippable_block(LVRelState *vacrel, bool *skipsallvis)
{
	BlockNumber rel_pages = vacrel->rel_pages;
	BlockNumber next_unskippable_block = vacrel->next_unskippable_block + 1;
	Buffer		next_unskippable_vmbuffer = vacrel->next_unskippable_vmbuffer;
	bool		next_unskippable_eager_scanned = false;
	bool		next_unskippable_allvis;

	*skipsallvis = false;

	for (;; next_unskippable_block++)
	{
		uint8		mapbits = visibilitymap_get_status(vacrel->rel,
													   next_unskippable_block,
													   &next_unskippable_vmbuffer);

		next_unskippable_allvis = (mapbits & VISIBILITYMAP_ALL_VISIBLE) != 0;

		// ... (L1709-L1720 생략: eager scan 구역마다 실패 한도 재설정)

		/*
		 * A block is unskippable if it is not all visible according to the
		 * visibility map.
		 */
		if (!next_unskippable_allvis)
		{
			Assert((mapbits & VISIBILITYMAP_ALL_FROZEN) == 0);
			break;
		}

		/*
		 * Caller must scan the last page to determine whether it has tuples
		 * (caller must have the opportunity to set vacrel->nonempty_pages).
		 * This rule avoids having lazy_truncate_heap() take access-exclusive
		 * lock on rel to attempt a truncation that fails anyway, just because
		 * there are tuples on the last page (it is likely that there will be
		 * tuples on other nearby pages as well, but those can be skipped).
		 *
		 * Implement this by always treating the last block as unsafe to skip.
		 */
		if (next_unskippable_block == rel_pages - 1)
			break;

		/* DISABLE_PAGE_SKIPPING makes all skipping unsafe */
		if (!vacrel->skipwithvm)
			break;

		/*
		 * All-frozen pages cannot contain XIDs < OldestXmin (XIDs that aren't
		 * already frozen by now), so this page can be skipped.
		 */
		if ((mapbits & VISIBILITYMAP_ALL_FROZEN) != 0)
			continue;

		/*
		 * Aggressive vacuums cannot skip any all-visible pages that are not
		 * also all-frozen.
		 */
		if (vacrel->aggressive)
			break;

		/*
		 * Normal vacuums with eager scanning enabled only skip all-visible
		 * but not all-frozen pages if they have hit the failure limit for the
		 * current eager scan region.
		 */
		if (vacrel->eager_scan_remaining_fails > 0)
		{
			next_unskippable_eager_scanned = true;
			break;
		}

		/*
		 * All-visible blocks are safe to skip in a normal vacuum. But
		 * remember that the final range contains such a block for later.
		 */
		*skipsallvis = true;
	}

	/* write the local variables back to vacrel */
	vacrel->next_unskippable_block = next_unskippable_block;
	vacrel->next_unskippable_allvis = next_unskippable_allvis;
	vacrel->next_unskippable_eager_scanned = next_unskippable_eager_scanned;
	vacrel->next_unskippable_vmbuffer = next_unskippable_vmbuffer;
}
```

## 동작 흐름

```text
 lazy_scan_heap
 L1236  read_stream_begin_relation(heap_vac_scan_next_block)    VM 으로 다음 블록을 고르는 콜백
 L1244  while (true)
          L1278  dead_items 가 max_bytes 를 넘었으면
                   L1295  [11] lazy_vacuum                     인덱스 + 힙 2 차 한 바퀴, dead_items 비움
          L1324  buf = read_stream_next_buffer                 고른 블록, pin 만 잡힌 상태
          L1349  visibilitymap_pin
          L1357  ConditionalLockBufferForCleanup               배타 잠금 + 핀이 나 하나뿐일 때만 성공
          L1360    실패하면 LockBuffer(SHARE)
          L1363  lazy_scan_new_or_empty                        새 페이지, 빈 페이지 처리
          L1378  cleanup lock 없음 -> lazy_scan_noprune         prune 없이 이미 LP_DEAD 인 것만 수집
                   false (aggressive 이고 얼려야 할 XID 가 있음) -> L1387 LockBufferForCleanup 대기
          L1404  cleanup lock 있음 -> [09] lazy_scan_prune
          L1484  인덱스 없음 / 인덱스 정리 안 함 / LP_DEAD 없음 -> 지금 FSM 에 빈 공간 기록
                 아니면 [12] 가 2 차로 올 때 기록
 L1541  남은 dead_items 가 있으면 [11] lazy_vacuum
 L1558  lazy_cleanup_all_indexes                              amvacuumcleanup
```

블록을 고르는 규칙은 VM 비트 두 개와 `SKIP_PAGES_THRESHOLD`(32, L209) 로 정해진다. 건너뛸 수 있는 구간이 32 블록보다 짧으면 OS readahead 를 깨지 않으려고 그냥 읽는다(L1624-L1636 주석).

```text
 rel_pages = 100, VM 비트 (AV = all-visible, AF = all-frozen)
   0-4    none
   5-54   AV|AF   (50 블록)
   55-59  none
   60-69  AV      (10 블록, 얼지 않음)
   70-99  none    (99 는 마지막 블록)

 일반 VACUUM, eager scan 꺼짐
   (rel_pages 100 < 2 * EAGER_SCAN_REGION_SIZE(4096) 이라 heap_vacuum_eager_scan_setup 이 끈다, L527.
    vacuum_max_eager_freeze_failure_rate = 0 이어도 L507 에서 꺼진다)
   0-4    읽는다
   5      find_next_unskippable_block: 5-54 AF 는 continue, 55 에서 멈춤
          55 - 5 = 50 >= 32 -> 55 로 건너뛴다. skipsallvis = false (AF 만 건너뜀)
   55-59  읽는다
   60     find_next_unskippable_block: 60-69 AV 는 skipsallvis = true 로 continue, 70 에서 멈춤
          70 - 60 = 10 < 32 -> 건너뛰지 않는다. 60-69 를 "VM 상 all-visible" 표시로 읽는다
          vacrel->skippedallvis 는 false 그대로 -> relfrozenxid 를 올릴 수 있다
   70-99  읽는다 (99 는 마지막 블록이라 어차피 건너뛰지 않는다, L1742)
   읽은 블록 50 개, 건너뛴 블록 50 개

 aggressive VACUUM
   60 에서 AV 지만 AF 아님 -> L1760-L1761 에서 바로 멈춤 (aggressive 는 AV 만으로는 못 건너뛴다)
   5-54 는 여전히 건너뛴다 (AF 에는 OldestXmin 보다 오래된 미동결 XID 가 없다, L1750-L1754)

 eager scan 이 켜진 일반 VACUUM (8192 블록 이상, relfrozenxid < FreezeLimit 또는 relminmxid < MultiXactCutoff, 기본 rate 0.03, L527-L555)
   AV 이고 AF 아닌 블록에서 eager_scan_remaining_fails > 0 이면 멈추고 eager 로 읽는다 (L1768-L1772)
   구역(4096 블록)마다 실패 허용 수 = 0.03 * 4096 = 122 (L587-L589)
```

cleanup lock 은 배타 잠금에 "이 페이지를 pin 한 것이 나 하나뿐"이라는 조건을 더한 것이다. HOT 체인을 prune 하고 페이지 조각 모음을 하려면 이것이 필요하다(L1351-L1355 주석).

```text
 no other pin on the page
   ConditionalLockBufferForCleanup 성공 -> lazy_scan_prune: prune + freeze + LP_DEAD 수집 + VM
 another backend holds a pin
   실패 -> LockBuffer(SHARE) -> lazy_scan_noprune: 이미 LP_DEAD 인 것만 수집하고 센다
   aggressive 이고 얼려야 할 XID 가 있으면 noprune 이 false -> L1387 에서 기다려 cleanup lock
```

## 결과가 쓰이는 곳

```text
 dead_items (TidStore)
      --> [11] lazy_vacuum 이 인덱스에 넘긴다
 vacrel->skippedallvis
      --> [06] 이 relfrozenxid 를 올릴지 정한다
 vacrel->new_live_tuples, scanned_pages
      --> [13] 이 pg_class.reltuples 로 쓴다 (안 읽은 페이지는 예전 밀도로 추정, vac_estimate_reltuples)
 FSM
      --> INSERT 가 빈 공간이 있는 페이지를 찾는다
```

## 다루지 않는 것

`lazy_scan_new_or_empty`, `lazy_scan_noprune` 의 세부, eager scan 의 성공·실패 한도와 구역(`EAGER_SCAN_REGION_SIZE` 4096), read stream 의 선읽기, FSM 정리 주기(`VACUUM_FSM_EVERY_PAGES`), wraparound failsafe 는 다루지 않았다.
