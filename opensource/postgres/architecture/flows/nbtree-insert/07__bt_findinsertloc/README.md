# _bt_findinsertloc

상위: [nbtree 삽입과 분할](../README.md)

**넣을 페이지와 오프셋을 확정하고, 공간이 모자라면 분할을 피할 방법을 먼저 시도한다.** 유일성 검사 뒤에는 힙 TID 까지 넣은 키로 자리를 다시 보므로 오른쪽 페이지로 옮겨야 할 수 있다(`_bt_stepright`). 페이지가 꽉 찼으면 `_bt_delete_or_dedup_one_page` 가 죽은 항목 지우기, bottom-up 삭제, 중복 합치기(deduplication) 순서로 공간을 만든다. 그래도 모자라면 [08] 에서 분할이 일어난다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L815-L1012 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L815-L1012))

함께 다루는 함수:

- `_bt_stepright`: `access` / `nbtree` / `nbtinsert.c` L1027-L1072 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1027-L1072))
- `_bt_delete_or_dedup_one_page`: `access` / `nbtree` / `nbtinsert.c` L2683-L2782 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2683-L2782))

## 실제 코드

heapkeyspace(버전 4 이상) 인덱스의 경로다. 유일성 검사를 했으면 high key 와 비교해 오른쪽으로 걷고, 그 다음 공간이 모자라면 분할 회피를 시도한다.

`access` / `nbtree` / `nbtinsert.c` L815-L907 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L815-L907))

```c
// nbtinsert.c L815-L907
_bt_findinsertloc(Relation rel,
				  BTInsertState insertstate,
				  bool checkingunique,
				  bool indexUnchanged,
				  BTStack stack,
				  Relation heapRel)
{
	BTScanInsert itup_key = insertstate->itup_key;
	Page		page = BufferGetPage(insertstate->buf);
	BTPageOpaque opaque;
	OffsetNumber newitemoff;

	opaque = BTPageGetOpaque(page);

	/* Check 1/3 of a page restriction */
	if (unlikely(insertstate->itemsz > BTMaxItemSize))
		_bt_check_third_page(rel, heapRel, itup_key->heapkeyspace, page,
							 insertstate->itup);

	Assert(P_ISLEAF(opaque) && !P_INCOMPLETE_SPLIT(opaque));
	Assert(!insertstate->bounds_valid || checkingunique);
	Assert(!itup_key->heapkeyspace || itup_key->scantid != NULL);
	Assert(itup_key->heapkeyspace || itup_key->scantid == NULL);
	Assert(!itup_key->allequalimage || itup_key->heapkeyspace);

	if (itup_key->heapkeyspace)
	{
		/* Keep track of whether checkingunique duplicate seen */
		bool		uniquedup = indexUnchanged;

		// ... (L845-L858 생략: 주석: 유일 인덱스는 오른쪽으로 걸어야 할 수 있다)
		if (checkingunique)
		{
			if (insertstate->low < insertstate->stricthigh)
			{
				/* Encountered a duplicate in _bt_check_unique() */
				Assert(insertstate->bounds_valid);
				uniquedup = true;
			}

			for (;;)
			{
				// ... (L870-L879 생략: 주석: 캐시한 상한이 페이지 안이면 high key 비교 생략)
				if (insertstate->bounds_valid &&
					insertstate->low <= insertstate->stricthigh &&
					insertstate->stricthigh <= PageGetMaxOffsetNumber(page))
					break;

				/* Test '<=', not '!=', since scantid is set now */
				if (P_RIGHTMOST(opaque) ||
					_bt_compare(rel, itup_key, page, P_HIKEY) <= 0)
					break;

				_bt_stepright(rel, heapRel, insertstate, stack);
				/* Update local state after stepping right */
				page = BufferGetPage(insertstate->buf);
				opaque = BTPageGetOpaque(page);
				/* Assume duplicates (if checkingunique) */
				uniquedup = true;
			}
		}

		/*
		 * If the target page cannot fit newitem, try to avoid splitting the
		 * page on insert by performing deletion or deduplication now
		 */
		if (PageGetFreeSpace(page) < insertstate->itemsz)
			_bt_delete_or_dedup_one_page(rel, heapRel, insertstate, false,
										 checkingunique, uniquedup,
										 indexUnchanged);
	}
```

pg_upgrade 로 남은 버전 2, 3 인덱스는 같은 키가 여러 페이지에 정당하게 놓일 수 있어서, 1% 확률로 "지쳐서" 멈추는 오른쪽 걷기를 한다.

`access` / `nbtree` / `nbtinsert.c` L908-L979 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L908-L979))

```c
// nbtinsert.c L908-L979
	else
	{
		// ... (L910-L937 생략: 주석: getting tired 설명)
		while (PageGetFreeSpace(page) < insertstate->itemsz)
		{
			/*
			 * Before considering moving right, see if we can obtain enough
			 * space by erasing LP_DEAD items
			 */
			if (P_HAS_GARBAGE(opaque))
			{
				/* Perform simple deletion */
				_bt_delete_or_dedup_one_page(rel, heapRel, insertstate, true,
											 false, false, false);

				if (PageGetFreeSpace(page) >= insertstate->itemsz)
					break;		/* OK, now we have enough space */
			}

			/*
			 * Nope, so check conditions (b) and (c) enumerated above
			 *
			 * The earlier _bt_check_unique() call may well have established a
			 * strict upper bound on the offset for the new item.  If it's not
			 * the last item of the page (i.e. if there is at least one tuple
			 * on the page that's greater than the tuple we're inserting to)
			 * then we know that the tuple belongs on this page.  We can skip
			 * the high key check.
			 */
			if (insertstate->bounds_valid &&
				insertstate->low <= insertstate->stricthigh &&
				insertstate->stricthigh <= PageGetMaxOffsetNumber(page))
				break;

			if (P_RIGHTMOST(opaque) ||
				_bt_compare(rel, itup_key, page, P_HIKEY) != 0 ||
				pg_prng_uint32(&pg_global_prng_state) <= (PG_UINT32_MAX / 100))
				break;

			_bt_stepright(rel, heapRel, insertstate, stack);
			/* Update local state after stepping right */
			page = BufferGetPage(insertstate->buf);
			opaque = BTPageGetOpaque(page);
		}
	}
```

마지막으로 페이지 안의 오프셋을 정한다. 새 튜플이 `LP_DEAD` 인 posting list 와 겹치면 먼저 지우고 다시 찾는다.

`access` / `nbtree` / `nbtinsert.c` L981-L1012 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L981-L1012))

```c
// nbtinsert.c L981-L1012
	/*
	 * We should now be on the correct page.  Find the offset within the page
	 * for the new tuple. (Possibly reusing earlier search bounds.)
	 */
	Assert(P_RIGHTMOST(opaque) ||
		   _bt_compare(rel, itup_key, page, P_HIKEY) <= 0);

	newitemoff = _bt_binsrch_insert(rel, insertstate);

	if (insertstate->postingoff == -1)
	{
		/*
		 * There is an overlapping posting list tuple with its LP_DEAD bit
		 * set.  We don't want to unnecessarily unset its LP_DEAD bit while
		 * performing a posting list split, so perform simple index tuple
		 * deletion early.
		 */
		_bt_delete_or_dedup_one_page(rel, heapRel, insertstate, true,
									 false, false, false);

		/*
		 * Do new binary search.  New insert location cannot overlap with any
		 * posting list now.
		 */
		Assert(!insertstate->bounds_valid);
		insertstate->postingoff = 0;
		newitemoff = _bt_binsrch_insert(rel, insertstate);
		Assert(insertstate->postingoff == 0);
	}

	return newitemoff;
}
```

`_bt_stepright` 는 오른쪽 페이지를 쓰기 잠금으로 잡은 뒤에야 지금 페이지를 놓는다. 다른 백엔드의 유일성 검사가 이 삽입을 놓치지 않게 하기 위해서다(L1017-L1020 주석).

`access` / `nbtree` / `nbtinsert.c` L1027-L1072 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1027-L1072))

```c
// nbtinsert.c L1027-L1072
_bt_stepright(Relation rel, Relation heaprel, BTInsertState insertstate,
			  BTStack stack)
{
	Page		page;
	BTPageOpaque opaque;
	Buffer		rbuf;
	BlockNumber rblkno;

	Assert(heaprel != NULL);
	page = BufferGetPage(insertstate->buf);
	opaque = BTPageGetOpaque(page);

	rbuf = InvalidBuffer;
	rblkno = opaque->btpo_next;
	for (;;)
	{
		rbuf = _bt_relandgetbuf(rel, rbuf, rblkno, BT_WRITE);
		page = BufferGetPage(rbuf);
		opaque = BTPageGetOpaque(page);

		/*
		 * If this page was incompletely split, finish the split now.  We do
		 * this while holding a lock on the left sibling, which is not good
		 * because finishing the split could be a fairly lengthy operation.
		 * But this should happen very seldom.
		 */
		if (P_INCOMPLETE_SPLIT(opaque))
		{
			_bt_finish_split(rel, heaprel, rbuf, stack);
			rbuf = InvalidBuffer;
			continue;
		}

		if (!P_IGNORE(opaque))
			break;
		if (P_RIGHTMOST(opaque))
			elog(ERROR, "fell off the end of index \"%s\"",
				 RelationGetRelationName(rel));

		rblkno = opaque->btpo_next;
	}
	/* rbuf locked; unlock buf, update state for caller */
	_bt_relbuf(rel, insertstate->buf);
	insertstate->buf = rbuf;
	insertstate->bounds_valid = false;
}
```

분할 회피의 순서가 이 함수에 있다.

`access` / `nbtree` / `nbtinsert.c` L2683-L2782 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2683-L2782))

```c
// nbtinsert.c L2683-L2782
_bt_delete_or_dedup_one_page(Relation rel, Relation heapRel,
							 BTInsertState insertstate,
							 bool simpleonly, bool checkingunique,
							 bool uniquedup, bool indexUnchanged)
{
	OffsetNumber deletable[MaxIndexTuplesPerPage];
	int			ndeletable = 0;
	OffsetNumber offnum,
				minoff,
				maxoff;
	Buffer		buffer = insertstate->buf;
	BTScanInsert itup_key = insertstate->itup_key;
	Page		page = BufferGetPage(buffer);
	BTPageOpaque opaque = BTPageGetOpaque(page);

	Assert(P_ISLEAF(opaque));
	Assert(simpleonly || itup_key->heapkeyspace);
	Assert(!simpleonly || (!checkingunique && !uniquedup && !indexUnchanged));

	// ... (L2702-L2708 생략: 주석: LP_DEAD 외에 덤으로 지워지는 항목)
	minoff = P_FIRSTDATAKEY(opaque);
	maxoff = PageGetMaxOffsetNumber(page);
	for (offnum = minoff;
		 offnum <= maxoff;
		 offnum = OffsetNumberNext(offnum))
	{
		ItemId		itemId = PageGetItemId(page, offnum);

		if (ItemIdIsDead(itemId))
			deletable[ndeletable++] = offnum;
	}

	if (ndeletable > 0)
	{
		_bt_simpledel_pass(rel, buffer, heapRel, deletable, ndeletable,
						   insertstate->itup, minoff, maxoff);
		insertstate->bounds_valid = false;

		/* Return when a page split has already been avoided */
		if (PageGetFreeSpace(page) >= insertstate->itemsz)
			return;

		/* Might as well assume duplicates (if checkingunique) */
		uniquedup = true;
	}

	// ... (L2735-L2747 생략: 주석: 유일 검사인데 중복을 못 봤으면 여기서 끝)
	if (simpleonly || (checkingunique && !uniquedup))
	{
		Assert(!indexUnchanged);
		return;
	}

	/* Assume bounds about to be invalidated (this is almost certain now) */
	insertstate->bounds_valid = false;

	// ... (L2757-L2773 생략: 주석: bottom-up 을 먼저 하는 조건)
	if ((indexUnchanged || uniquedup) &&
		_bt_bottomupdel_pass(rel, buffer, heapRel, insertstate->itemsz))
		return;

	/* Perform deduplication pass (when enabled and index-is-allequalimage) */
	if (BTGetDeduplicateItems(rel) && itup_key->allequalimage)
		_bt_dedup_pass(rel, buffer, insertstate->itup, insertstate->itemsz,
					   (indexUnchanged || uniquedup));
}
```

## 동작 흐름

```text
 L830  itemsz > BTMaxItemSize   -> _bt_check_third_page (너무 크면 에러)
 L840  heapkeyspace 인덱스
         uniquedup = indexUnchanged
 L859    checkingunique 면
 L861      low < stricthigh (검사 중 중복을 봤다)   -> uniquedup = true
 L868      for (;;)
 L880        캐시한 stricthigh 가 페이지 안         -> 이 페이지다. break
 L886        오른쪽 끝이거나 key <= high key        -> 이 페이지다. break
 L890        _bt_stepright                          오른쪽으로 한 칸, uniquedup = true
 L903    PageGetFreeSpace < itemsz
 L904      _bt_delete_or_dedup_one_page              분할 회피 시도
 L908  (버전 2, 3 인덱스면 L938-L978 의 지치는 걷기)
 L988  newitemoff = _bt_binsrch_insert              페이지 안 오프셋. postingoff 도 정해진다
 L990  postingoff == -1 (LP_DEAD posting 과 겹침) -> 지우고 L1007 다시 찾기
 L1011 return newitemoff
```

공간이 모자랄 때 시도하는 세 가지는 비용이 싼 것부터다. 하나라도 새 튜플 자리를 만들면 거기서 멈춘다.

```text
 _bt_delete_or_dedup_one_page (리프, 쓰기 잠금 쥔 채)

 1. simple deletion     L2711-L2733
      LP_DEAD 표시된 항목을 모아 _bt_simpledel_pass        [06] 이 켜 둔 표시를 여기서 거둔다
      공간이 생기면 return (L2729)
      지운 것이 있었으면 uniquedup = true
          |
          v  simpleonly 이거나 (유일 검사인데 중복을 못 봤으면) 여기서 끝 (L2748)
 2. bottom-up deletion  L2774
      조건: indexUnchanged (UPDATE 인데 키 불변) 또는 uniquedup
      같은 키의 옛 버전들이 가리키는 힙 블록을 직접 확인해 죽은 버전을 지운다
      충분히 비우면 return (L2776)
          |
          v
 3. deduplication       L2779
      조건: deduplicate_items 옵션 (기본 켜짐, nbtree.h L1166-L1170)
            그리고 allequalimage (같은 값이면 바이트도 같은 타입)
      같은 키의 튜플들을 posting list 튜플 하나로 합친다
          |
          v
 그래도 PageGetFreeSpace < itemsz 이면 [08] 에서 분할
```

```text
 deduplication 이 공간을 만드는 모양 (키 7 이 세 번)

 전   [7, tid a] [7, tid b] [7, tid c]          키 값이 세 번, 튜플 헤더도 세 번
 후   [7, posting: a b c]                      키 값 한 번, TID 는 배열로

 posting list 하나의 상한은 BTMaxItemSize / 2 (nbtdedup.c L87)
 BTMaxItemSize 는 8KB 페이지에서
   MAXALIGN_DOWN((8192 - MAXALIGN(24 + 3*4) - MAXALIGN(16)) / 3) - MAXALIGN(6)
 = MAXALIGN_DOWN((8192 - 40 - 16) / 3) - 8 = 2712 - 8 = 2704 바이트   (nbtree.h L165-L169)
```

유일 인덱스에서도 dedup 이 돌 수 있다. 같은 키의 옛 버전(UPDATE 로 생긴 것)이 페이지에 쌓이기 때문이다. 다만 유일성 검사에서 중복을 하나도 보지 못했으면(`checkingunique && !uniquedup`) 1단계 뒤에 바로 돌아간다(L2748). 오름차순 기본키 삽입처럼 중복이 없는 경우는 그래서 dedup 없이 곧장 분할로 간다.

```text
 _bt_stepright (L1027-L1072)

 현재 buf (쓰기 잠금) --btpo_next--> rbuf 를 BT_WRITE 로 잡는다     L1043
   rbuf 가 INCOMPLETE_SPLIT  -> _bt_finish_split 후 다시           L1053-L1057
   rbuf 가 죽은 페이지       -> 그 다음 오른쪽으로                   L1060-L1066
 그 다음에야 buf 를 놓는다                                          L1069
 bounds_valid = false (캐시한 탐색 범위는 이전 페이지의 것)          L1071
```

## 결과가 쓰이는 곳

```text
 newitemoff
      --> [08] _bt_insertonpg 가 이 오프셋에 PageAddItem 하거나, [10] 이 분할 지점을 고를 때
          "새 튜플이 원래 페이지에 있다고 치면 어디인가"로 쓴다
 insertstate->postingoff
      --> 0 이 아니면 [08] 이 기존 posting list 를 쪼갠다 (_bt_swap_posting)
 insertstate->buf
      --> 오른쪽으로 걸었으면 바뀐 페이지. 쓰기 잠금 그대로 [08] 로 간다
```

## 다루지 않는 것

`_bt_simpledel_pass` 와 `_bt_bottomupdel_pass` 가 힙을 확인하는 절차(`table_index_delete_tuples`), `_bt_dedup_pass` 의 single value 전략과 WAL 기록, posting list 분할(`_bt_swap_posting`), 너무 큰 튜플의 에러 메시지(`_bt_check_third_page`)는 다루지 않는다.
