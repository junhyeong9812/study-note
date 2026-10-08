# GetScanItems

상위: [IVFFlat 빌드와 검색](../README.md)

**고른 리스트의 항목 페이지를 끝까지 읽어, 항목마다 검색 벡터와의 거리를 재서 `(거리, 힙 TID)` 를 정렬기에 넣고 정렬하는 함수다.** 한 번 부를 때 최대 `probes` 개 리스트를 읽는다. 리스트 안의 모든 항목과 거리를 재므로 IVFFlat 의 검색 비용은 "고른 리스트에 든 행 수"에 비례한다. 결과는 근사 최근접이 아니라 "고른 리스트 안에서는 정확한" 순서다.

## 위치

`src` / `ivfscan.c` L123-L187 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfscan.c#L123-L187))

## 실제 코드

```c
// ivfscan.c L120-L187
/*
 * Get items
 */
static void
GetScanItems(IndexScanDesc scan, Datum value)
{
	IvfflatScanOpaque so = (IvfflatScanOpaque) scan->opaque;
	TupleDesc	tupdesc = RelationGetDescr(scan->indexRelation);
	TupleTableSlot *slot = so->vslot;
	int			batchProbes = 0;

	tuplesort_reset(so->sortstate);

	/* Search closest probes lists */
	while (so->listIndex < so->maxProbes && (++batchProbes) <= so->probes)
	{
		BlockNumber searchPage = so->listPages[so->listIndex++];

		/* Search all entry pages for list */
		while (BlockNumberIsValid(searchPage))
		{
			Buffer		buf;
			Page		page;
			OffsetNumber maxoffno;

			buf = ReadBufferExtended(scan->indexRelation, MAIN_FORKNUM, searchPage, RBM_NORMAL, so->bas);
			LockBuffer(buf, BUFFER_LOCK_SHARE);
			page = BufferGetPage(buf);
			maxoffno = PageGetMaxOffsetNumber(page);

			for (OffsetNumber offno = FirstOffsetNumber; offno <= maxoffno; offno = OffsetNumberNext(offno))
			{
				IndexTuple	itup;
				Datum		datum;
				bool		isnull;
				ItemId		itemid = PageGetItemId(page, offno);

				itup = (IndexTuple) PageGetItem(page, itemid);
				datum = index_getattr(itup, 1, tupdesc, &isnull);

				/*
				 * Add virtual tuple
				 *
				 * Use procinfo from the index instead of scan key for
				 * performance
				 */
				ExecClearTuple(slot);
				slot->tts_values[0] = so->distfunc(so->procinfo, so->collation, datum, value);
				slot->tts_isnull[0] = false;
				slot->tts_values[1] = PointerGetDatum(&itup->t_tid);
				slot->tts_isnull[1] = false;
				ExecStoreVirtualTuple(slot);

				tuplesort_puttupleslot(so->sortstate, slot);
			}

			searchPage = IvfflatPageGetOpaque(page)->nextblkno;

			UnlockReleaseBuffer(buf);
		}
	}

	tuplesort_performsort(so->sortstate);

#if defined(IVFFLAT_MEMORY)
	elog(INFO, "memory: %zu MB", MemoryContextMemAllocated(CurrentMemoryContext, true) / (1024 * 1024));
#endif
}
```

거리 하나를 키로 하는 정렬기다.

`src` / `ivfscan.c` L241-L250 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfscan.c#L241-L250))

```c
// ivfscan.c L238-L250
/*
 * Initialize scan sort state
 */
static Tuplesortstate *
InitScanSortState(TupleDesc tupdesc)
{
	AttrNumber	attNums[] = {1};
	Oid			sortOperators[] = {Float8LessOperator};
	Oid			sortCollations[] = {InvalidOid};
	bool		nullsFirstFlags[] = {false};

	return tuplesort_begin_heap(tupdesc, 1, attNums, sortOperators, sortCollations, nullsFirstFlags, work_mem, NULL, false);
}
```

## 동작 흐름

```text
 GetScanItems(scan, value)                           L123
   L131  tuplesort_reset                   이전 묶음을 비운다
   L134  listIndex < maxProbes 이고 이번 묶음이 probes 개 이하인 동안
           searchPage = listPages[listIndex++]
           L139 항목 페이지 체인을 nextblkno 로 끝까지
                  ReadBufferExtended(..., so->bas)    BAS_BULKREAD 링 버퍼, SHARE 잠금
                  항목마다
                    datum = index_getattr(itup, 1)
                    slot = (distfunc(FUNCTION 1, datum, value), &itup->t_tid)
                    tuplesort_puttupleslot
   L182  tuplesort_performsort              거리 오름차순 (Float8LessOperator)
```

[08] 의 예를 이어 본다. `probes = 1`, `maxProbes = 2`(반복 스캔), c3 리스트에 항목 셋, c1 리스트에 둘이 있다.

```text
 첫 호출 (ivfflatgettuple L398)
   listIndex 0 -> c3 의 항목 페이지
     a 0.8, b 0.3, c 1.5   -> 정렬 [b 0.3, a 0.8, c 1.5]
   listIndex = 1
 행 3 개를 낸 뒤 정렬기가 비었다
   listIndex 1 != maxProbes 2 -> 다시 GetScanItems
   c1 의 항목 페이지
     d 0.5, e 2.1          -> 정렬 [d 0.5, e 2.1]
   listIndex = 2
 행 2 개를 더 낸다:  b 0.3, a 0.8, c 1.5, d 0.5, e 2.1
                    d 가 c 보다 가깝지만 뒤에 나온다 (relaxed_order)
 다시 비었고 listIndex == maxProbes -> false
```

정렬기는 `work_mem` 안에서 정렬한다(L249). 고른 리스트의 행이 많으면 정렬 데이터가 커진다.

## 결과가 쓰이는 곳

```text
 정렬된 tuplesort (distance, heaptid)
      --> [07] ivfflatgettuple 이 tuplesort_gettupleslot 으로 하나씩 꺼낸다
```

## 다루지 않는 것

항목 페이지를 읽는 동안 동시에 INSERT 가 같은 리스트에 붙이는 경우의 가시성(힙 TID 는 실행기가 스냅샷으로 다시 판단한다), `IVFFLAT_MEMORY` 빌드의 메모리 로그는 다루지 않았다.
