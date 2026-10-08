# heap_prepare_pagescan

상위: [MVCC 가시성과 스냅샷](../README.md)

**페이지 한 장의 가시성을 한꺼번에 판정해 두는 함수다.** 먼저 기회가 되면 죽은 튜플을 치우고(prune), 버퍼 share 잠금을 잡은 채 [06] `page_collect_tuples` 로 보이는 줄 번호를 모은 다음 잠금을 푼다. 페이지에 `PD_ALL_VISIBLE` 이 서 있으면 튜플마다 판정하지 않는다.

## 위치

`access/heap` / `heapam.c` L556-L638 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L556-L638))

## 실제 코드

```c
// heapam.c L549-L638
/*
 * heap_prepare_pagescan - Prepare current scan page to be scanned in pagemode
 *
 * Preparation currently consists of 1. prune the scan's rs_cbuf page, and 2.
 * fill the rs_vistuples[] array with the OffsetNumbers of visible tuples.
 */
void
heap_prepare_pagescan(TableScanDesc sscan)
{
	HeapScanDesc scan = (HeapScanDesc) sscan;
	Buffer		buffer = scan->rs_cbuf;
	BlockNumber block = scan->rs_cblock;
	Snapshot	snapshot;
	Page		page;
	int			lines;
	bool		all_visible;
	bool		check_serializable;

	Assert(BufferGetBlockNumber(buffer) == block);

	/* ensure we're not accidentally being used when not in pagemode */
	Assert(scan->rs_base.rs_flags & SO_ALLOW_PAGEMODE);
	snapshot = scan->rs_base.rs_snapshot;

	/*
	 * Prune and repair fragmentation for the whole page, if possible.
	 */
	heap_page_prune_opt(scan->rs_base.rs_rd, buffer);

	/*
	 * We must hold share lock on the buffer content while examining tuple
	 * visibility.  Afterwards, however, the tuples we have found to be
	 * visible are guaranteed good as long as we hold the buffer pin.
	 */
	LockBuffer(buffer, BUFFER_LOCK_SHARE);

	page = BufferGetPage(buffer);
	lines = PageGetMaxOffsetNumber(page);

	/*
	 * If the all-visible flag indicates that all tuples on the page are
	 * visible to everyone, we can skip the per-tuple visibility tests.
	 *
// ... (L592-L607 생략: hot standby 에서 all-visible 을 믿지 않는 이유 (아래 그림))
	all_visible = PageIsAllVisible(page) && !snapshot->takenDuringRecovery;
	check_serializable =
		CheckForSerializableConflictOutNeeded(scan->rs_base.rs_rd, snapshot);

// ... (L612-L617 생략: 상수 인자로 부르는 이유 (컴파일러 상수 접기))
	if (likely(all_visible))
	{
		if (likely(!check_serializable))
			scan->rs_ntuples = page_collect_tuples(scan, snapshot, page, buffer,
												   block, lines, true, false);
		else
			scan->rs_ntuples = page_collect_tuples(scan, snapshot, page, buffer,
												   block, lines, true, true);
	}
	else
	{
		if (likely(!check_serializable))
			scan->rs_ntuples = page_collect_tuples(scan, snapshot, page, buffer,
												   block, lines, false, false);
		else
			scan->rs_ntuples = page_collect_tuples(scan, snapshot, page, buffer,
												   block, lines, false, true);
	}

	LockBuffer(buffer, BUFFER_LOCK_UNLOCK);
}
```

prune 은 조건이 맞을 때만, 그리고 잠금을 기다리지 않고 얻을 수 있을 때만 한다.

`access/heap` / `pruneheap.c` L193-L246 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/pruneheap.c#L193-L246))

```c
// pruneheap.c L192-L246
void
heap_page_prune_opt(Relation relation, Buffer buffer)
{
	Page		page = BufferGetPage(buffer);
	TransactionId prune_xid;
	GlobalVisState *vistest;
	Size		minfree;

// ... (L200-L204 생략: recovery 주석)
	if (RecoveryInProgress())
		return;

// ... (L208-L212 생략: 주석)
	prune_xid = ((PageHeader) page)->pd_prune_xid;
	if (!TransactionIdIsValid(prune_xid))
		return;

// ... (L217-L220 생략: 주석)
	vistest = GlobalVisTestFor(relation);

	if (!GlobalVisTestIsRemovableXid(vistest, prune_xid))
		return;

// ... (L226-L237 생략: 여유 공간을 잠금 없이 보는 이유 (주석))
	minfree = RelationGetTargetPageFreeSpace(relation,
											 HEAP_DEFAULT_FILLFACTOR);
	minfree = Max(minfree, BLCKSZ / 10);

	if (PageIsFull(page) || PageGetHeapFreeSpace(page) < minfree)
	{
		/* OK, try to get exclusive buffer lock */
		if (!ConditionalLockBufferForCleanup(buffer))
			return;
```

## 동작 흐름

```text
 L576  heap_page_prune_opt(rel, buffer)                 pin 만 있고 잠금은 없는 상태
         pruneheap.c L205  recovery 중이면 안 한다
                     L214  pd_prune_xid 가 없으면 안 한다 (UPDATE/DELETE 흔적이 없다)
                     L223  그 xid 가 아직 누군가에게 필요하면 안 한다 (GlobalVis)
                     L242  페이지가 가득 찼거나 여유 < max(fillfactor 목표, BLCKSZ/10)
                     L245  ConditionalLockBufferForCleanup 실패면 안 한다 (기다리지 않음)
 L583  LockBuffer(buffer, BUFFER_LOCK_SHARE)
 L586  lines = PageGetMaxOffsetNumber(page)             줄 포인터 개수
 L608  all_visible = PageIsAllVisible(page) && !snapshot->takenDuringRecovery
 L609  check_serializable = CheckForSerializableConflictOutNeeded(rel, snapshot)
 L618  네 조합 중 하나로 [06] page_collect_tuples       -> rs_ntuples, rs_vistuples[]
 L637  LockBuffer(buffer, BUFFER_LOCK_UNLOCK)
```

all-visible 지름길은 스냅샷이 복구 중에 찍혔으면 쓰지 않는다. L592-L607 주석의 요지를 그림으로 옮긴다.

```text
 PD_ALL_VISIBLE 을 믿는가

 PD_ALL_VISIBLE  takenDuringRecovery  all_visible (L608)  결과
 0               false                false               튜플마다 판정
 0               true                 false               튜플마다 판정
 1               false                true                판정 생략, 전부 보임
 1               true                 false               튜플마다 판정

 standby 에서 primary 기준으로는 모두에게 보이는 튜플이 아직 안 보여야 하는 읽기 트랜잭션이 있을 수 있다
 index-only scan 은 visibility map 을 쓰고 그 갱신은 WAL 에 cutoff xid 와 함께 남지만,
 페이지 플래그는 full page write 등으로 따로 퍼질 수 있어 확신할 수 없다고 주석이 적었다
```

잠금의 범위가 [08] 의 힌트 비트 쓰기를 허락한다. 힌트 비트는 share 잠금만으로 적는다.

```text
 이 함수가 잡는 것과 그 안에서 일어나는 쓰기

 pin             [04] 가 read stream 에서 받을 때 이미 있음
 share 잠금      L583 - L637
   안에서        [08] SetHintBits -> t_infomask |= ...       share 잠금으로 튜플 헤더를 고친다
                         MarkBufferDirtyHint                 bufmgr.c L5453
                 [06] HeapCheckForSerializableConflictOut   SERIALIZABLE 일 때만
 exclusive       prune 이 cleanup 잠금을 얻었을 때만. L583 보다 앞에서 잡고
                 pruneheap.c L286 에서 놓는다
```

## 결과가 쓰이는 곳

```text
 scan->rs_ntuples, scan->rs_vistuples[]
      --> [04] heapgettup_pagemode 가 이 목록만 돈다
 prune 결과
      --> 줄 포인터가 LP_DEAD, LP_REDIRECT, LP_UNUSED 로 바뀌면 [06] 의 ItemIdIsNormal 에서 걸러진다
```

## 다루지 않는 것

prune 본체(`heap_page_prune_and_freeze`, HOT 체인 정리)와 `GlobalVisTestIsRemovableXid` 의 경계 계산은 [vacuum](../../vacuum/README.md)에 가깝다. visibility map 과 `PD_ALL_VISIBLE` 을 켜는 쪽, SERIALIZABLE 의 rw-conflict 검사(`CheckForSerializableConflictOutNeeded`)는 요약만 했다.
