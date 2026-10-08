# InsertTuples

상위: [IVFFlat 빌드와 검색](../README.md)

**리스트 번호 순으로 정렬된 행을 꺼내, 리스트마다 항목 페이지 체인을 새로 만들어 채우는 함수다.** 리스트 0 부터 차례로 새 페이지를 하나 열고, 정렬기에서 나오는 행의 리스트 번호가 지금 리스트와 같은 동안 그 페이지에 `IndexTuple` 을 붙인다(차면 다음 페이지). 리스트가 끝나면 그 리스트 튜플에 첫 페이지와 마지막 페이지 번호를 적는다. 행이 없는 리스트도 빈 페이지 하나를 받는다.

## 위치

`src` / `ivfbuild.c` L277-L337 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L277-L337))

## 실제 코드

```c
// ivfbuild.c L252-L337
/*
 * Get index tuple from sort state
 */
static inline void
GetNextTuple(Tuplesortstate *sortstate, TupleDesc tupdesc, TupleTableSlot *slot, IndexTuple *itup, int *list)
{
	if (tuplesort_gettupleslot(sortstate, true, false, slot, NULL))
	{
		Datum		value;
		bool		isnull;

		*list = DatumGetInt32(slot_getattr(slot, 1, &isnull));
		value = slot_getattr(slot, 3, &isnull);

		/* Form the index tuple */
		*itup = index_form_tuple(tupdesc, &value, &isnull);
		(*itup)->t_tid = *((ItemPointer) DatumGetPointer(slot_getattr(slot, 2, &isnull)));
	}
	else
		*list = -1;
}

/*
 * Create initial entry pages
 */
static void
InsertTuples(Relation index, IvfflatBuildState * buildstate, ForkNumber forkNum)
{
	int			list;
	IndexTuple	itup = NULL;	/* silence compiler warning */
	int64		inserted = 0;

	TupleTableSlot *slot = MakeSingleTupleTableSlot(buildstate->sortdesc, &TTSOpsMinimalTuple);
	TupleDesc	tupdesc = buildstate->tupdesc;

	pgstat_progress_update_param(PROGRESS_CREATEIDX_SUBPHASE, PROGRESS_IVFFLAT_PHASE_LOAD);

	pgstat_progress_update_param(PROGRESS_CREATEIDX_TUPLES_TOTAL, buildstate->indtuples);

	GetNextTuple(buildstate->sortstate, tupdesc, slot, &itup, &list);

	for (int i = 0; i < buildstate->centers->length; i++)
	{
		Buffer		buf;
		Page		page;
		GenericXLogState *state;
		BlockNumber startPage;
		BlockNumber insertPage;

		/* Can take a while, so ensure we can interrupt */
		/* Needs to be called when no buffer locks are held */
		CHECK_FOR_INTERRUPTS();

		buf = IvfflatNewBuffer(index, forkNum);
		IvfflatInitRegisterPage(index, &buf, &page, &state);

		startPage = BufferGetBlockNumber(buf);

		/* Get all tuples for list */
		while (list == i)
		{
			/* Check for free space */
			Size		itemsz = MAXALIGN(IndexTupleSize(itup));

			if (PageGetFreeSpace(page) < itemsz)
				IvfflatAppendPage(index, &buf, &page, &state, forkNum);

			/* Add the item */
			if (PageAddItem(page, (Item) itup, itemsz, InvalidOffsetNumber, false, false) == InvalidOffsetNumber)
				elog(ERROR, "failed to add index item to \"%s\"", RelationGetRelationName(index));

			pfree(itup);

			pgstat_progress_update_param(PROGRESS_CREATEIDX_TUPLES_DONE, ++inserted);

			GetNextTuple(buildstate->sortstate, tupdesc, slot, &itup, &list);
		}

		insertPage = BufferGetBlockNumber(buf);

		IvfflatCommitBuffer(buf, state);

		/* Set the start and insert pages */
		IvfflatUpdateList(index, buildstate->listInfo[i], insertPage, InvalidBlockNumber, startPage, forkNum);
	}
}
```

리스트 튜플의 두 번호를 고치는 함수다. INSERT 와 VACUUM 도 이것을 쓴다.

`src` / `ivfutils.c` L239-L281 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfutils.c#L239-L281))

```c
// ivfutils.c L236-L281
/*
 * Update the start or insert page of a list
 */
void
IvfflatUpdateList(Relation index, ListInfo listInfo,
				  BlockNumber insertPage, BlockNumber originalInsertPage,
				  BlockNumber startPage, ForkNumber forkNum)
{
	Buffer		buf;
	Page		page;
	GenericXLogState *state;
	IvfflatList list;
	bool		changed = false;

	buf = ReadBufferExtended(index, forkNum, listInfo.blkno, RBM_NORMAL, NULL);
	LockBuffer(buf, BUFFER_LOCK_EXCLUSIVE);
	state = GenericXLogStart(index);
	page = GenericXLogRegisterBuffer(state, buf, 0);
	list = (IvfflatList) PageGetItem(page, PageGetItemId(page, listInfo.offno));

	if (BlockNumberIsValid(insertPage) && insertPage != list->insertPage)
	{
		/* Skip update if insert page is lower than original insert page  */
		/* This is needed to prevent insert from overwriting vacuum */
		if (!BlockNumberIsValid(originalInsertPage) || insertPage >= originalInsertPage)
		{
			list->insertPage = insertPage;
			changed = true;
		}
	}

	if (BlockNumberIsValid(startPage) && startPage != list->startPage)
	{
		list->startPage = startPage;
		changed = true;
	}

	/* Only commit if changed */
	if (changed)
		IvfflatCommitBuffer(buf, state);
	else
	{
		GenericXLogAbort(state);
		UnlockReleaseBuffer(buf);
	}
}
```

## 동작 흐름

```text
 InsertTuples(index, buildstate, forkNum)            L277
   L287  진행 단계 "loading tuples", 전체 = indtuples
   L291  GetNextTuple -> (list, itup)               L255
           정렬기에서 하나 -> index_form_tuple(vector), t_tid = 힙 TID
           더 없으면 list = -1
   L293  i = 0 .. lists-1
           L305  새 버퍼 + GenericXLog 전체 이미지 등록
           L308  startPage = 이 블록
           L311  while list == i
                   자리가 없으면 IvfflatAppendPage (WAL 기록하고 다음 페이지)
                   PageAddItem(itup)
                   GetNextTuple
           L330  insertPage = 지금 블록 (마지막 페이지)
           L332  IvfflatCommitBuffer              GenericXLogFinish
           L335  IvfflatUpdateList(listInfo[i], insertPage, 무효, startPage)
                   리스트 튜플을 플래그 0 으로 등록해 두 칸을 고치고 기록
```

[05] 의 예(lists = 3, 다섯 행)를 이어 본다. 리스트 페이지가 블록 1 하나라고 한다.

```text
 정렬 뒤  (0,t2) (0,t4) (1,t3) (2,t1) (2,t5)

 i = 0   블록 2 새로   t2, t4      startPage 2, insertPage 2
 i = 1   블록 3 새로   t3          startPage 3, insertPage 3
 i = 2   블록 4 새로   t1, t5      startPage 4, insertPage 4
 정렬기 끝 (list = -1)

 블록 1 리스트 페이지
   L0 { startPage 2, insertPage 2, c0 }
   L1 { startPage 3, insertPage 3, c1 }
   L2 { startPage 4, insertPage 4, c2 }
```

`IvfflatUpdateList` 의 `originalInsertPage` 인자는 빌드에서는 무효다. INSERT 가 이 함수를 부를 때는 처음 본 `insertPage` 를 넘겨, 그보다 낮은 번호로 되돌리는 갱신은 하지 않는다(ivfutils.c L258-L264, 주석: VACUUM 의 갱신을 INSERT 가 덮어쓰지 않게).

## 결과가 쓰이는 곳

```text
 리스트별 항목 페이지 체인 (startPage -> nextblkno -> ... -> insertPage)
      --> 검색 [09] GetScanItems 가 startPage 부터 nextblkno 를 따라 끝까지 읽는다
      --> INSERT 가 insertPage 에 붙이고, 차면 새 페이지를 이어 붙인다
```

## 다루지 않는 것

항목 튜플 하나가 페이지를 넘는 경우(INSERT 쪽의 `Assert`, ivfinsert.c), 진행률 보고 세부는 다루지 않았다.
