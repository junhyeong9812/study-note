# AddTupleToSort

상위: [IVFFlat 빌드와 검색](../README.md)

**힙 행 하나를 가장 가까운 리스트에 배정해 정렬기에 넣는 함수다.** 모든 중심점과의 거리를 재서(인덱스 거리 함수 FUNCTION 1) 가장 작은 쪽의 리스트 번호를 고르고, `(리스트 번호, 힙 TID, 벡터)` 세 열짜리 가상 튜플을 만들어 `tuplesort` 에 넣는다. 정렬기는 리스트 번호 하나만 키로 삼으므로, 다 넣고 정렬하면 같은 리스트의 행이 한데 모인다. 이것이 [06] 에서 리스트별로 연속된 페이지를 쓸 수 있게 하는 준비다.

## 위치

`src` / `ivfbuild.c` L164-L225 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L164-L225))

## 실제 코드

배정 단계 전체를 묶는 함수들이다.

`src` / `ivfbuild.c` L977-L1041 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L977-L1041))

```c
// ivfbuild.c L974-L1041
/*
 * Scan table for tuples to index
 */
static void
AssignTuples(IvfflatBuildState * buildstate)
{
	int			parallel_workers = 0;
	SortCoordinate coordinate = NULL;

	pgstat_progress_update_param(PROGRESS_CREATEIDX_SUBPHASE, PROGRESS_IVFFLAT_PHASE_ASSIGN);

	/* Calculate parallel workers */
	if (buildstate->heap != NULL)
		parallel_workers = plan_create_index_workers(RelationGetRelid(buildstate->heap), RelationGetRelid(buildstate->index));

	/* Attempt to launch parallel worker scan when required */
	if (parallel_workers > 0)
		IvfflatBeginParallel(buildstate, buildstate->indexInfo->ii_Concurrent, parallel_workers);

	/* Set up coordination state if at least one worker launched */
	if (buildstate->ivfleader)
	{
		coordinate = palloc0_object(SortCoordinateData);
		coordinate->isWorker = false;
		coordinate->nParticipants = buildstate->ivfleader->nparticipanttuplesorts;
		coordinate->sharedsort = buildstate->ivfleader->sharedsort;
	}

	/* Begin serial/leader tuplesort */
	buildstate->sortstate = InitBuildSortState(buildstate->sortdesc, maintenance_work_mem, coordinate);

	/* Add tuples to sort */
	if (buildstate->heap != NULL)
	{
		if (buildstate->ivfleader)
			buildstate->reltuples = ParallelHeapScan(buildstate);
		else
			buildstate->reltuples = table_index_build_scan(buildstate->heap, buildstate->index, buildstate->indexInfo,
														   true, true, BuildCallback, (void *) buildstate, NULL);

#ifdef IVFFLAT_KMEANS_DEBUG
		PrintKmeansMetrics(buildstate);
#endif
	}
}

/*
 * Create entry pages
 */
static void
CreateEntryPages(IvfflatBuildState * buildstate, ForkNumber forkNum)
{
	/* Assign */
	IvfflatBench("assign tuples", AssignTuples(buildstate));

	/* Sort */
	IvfflatBench("sort tuples", tuplesort_performsort(buildstate->sortstate));

	/* Load */
	IvfflatBench("load tuples", InsertTuples(buildstate->index, buildstate, forkNum));

	/* End sort */
	tuplesort_end(buildstate->sortstate);

	/* End parallel build */
	if (buildstate->ivfleader)
		IvfflatEndParallel(buildstate->ivfleader);
}
```

리스트 번호로만 정렬하는 정렬기를 만든다.

`src` / `ivfbuild.c` L612-L621 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L612-L621))

```c
// ivfbuild.c L609-L621
/*
 * Initialize build sort state
 */
static Tuplesortstate *
InitBuildSortState(TupleDesc tupdesc, int memory, SortCoordinate coordinate)
{
	AttrNumber	attNums[] = {1};
	Oid			sortOperators[] = {Int4LessOperator};
	Oid			sortCollations[] = {InvalidOid};
	bool		nullsFirstFlags[] = {false};

	return tuplesort_begin_heap(tupdesc, 1, attNums, sortOperators, sortCollations, nullsFirstFlags, memory, coordinate, false);
}
```

```c
// ivfbuild.c L161-L250
/*
 * Add tuple to sort
 */
static void
AddTupleToSort(ItemPointer tid, Datum *values, IvfflatBuildState * buildstate)
{
	double		distance;
	double		minDistance = DBL_MAX;
	int			closestCenter = 0;
	VectorArray centers = buildstate->centers;
	TupleTableSlot *slot = buildstate->slot;

	/* Detoast once for all calls */
	Datum		value = PointerGetDatum(PG_DETOAST_DATUM(values[0]));

	/* Normalize if needed */
	if (buildstate->normprocinfo != NULL)
	{
		if (!IvfflatCheckNorm(buildstate->normprocinfo, buildstate->collation, value))
			return;

		value = IvfflatNormValue(buildstate->typeInfo, buildstate->collation, value);
	}

	/* Check dimensions match index */
	IvfflatCheckDim(buildstate->dimensions, buildstate->typeInfo, buildstate->collation, value);

	/* Find the list that minimizes the distance */
	for (int i = 0; i < centers->length; i++)
	{
		distance = DatumGetFloat8(FunctionCall2Coll(buildstate->procinfo, buildstate->collation, value, PointerGetDatum(VectorArrayGet(centers, i))));

		if (distance < minDistance)
		{
			minDistance = distance;
			closestCenter = i;
		}
	}

#ifdef IVFFLAT_KMEANS_DEBUG
	buildstate->inertia += minDistance;
	buildstate->listSums[closestCenter] += minDistance;
	buildstate->listCounts[closestCenter]++;
#endif

	/* Create a virtual tuple */
	ExecClearTuple(slot);
	slot->tts_values[0] = Int32GetDatum(closestCenter);
	slot->tts_isnull[0] = false;
	slot->tts_values[1] = PointerGetDatum(tid);
	slot->tts_isnull[1] = false;
	slot->tts_values[2] = value;
	slot->tts_isnull[2] = false;
	ExecStoreVirtualTuple(slot);

	/*
	 * Add tuple to sort
	 *
	 * tuplesort_puttupleslot comment: Input data is always copied; the caller
	 * need not save it.
	 */
	tuplesort_puttupleslot(buildstate->sortstate, slot);

	buildstate->indtuples++;
}

/*
 * Callback for table_index_build_scan
 */
static void
BuildCallback(Relation index, ItemPointer tid, Datum *values,
			  bool *isnull, bool tupleIsAlive, void *state)
{
	IvfflatBuildState *buildstate = (IvfflatBuildState *) state;
	MemoryContext oldCtx;

	/* Skip nulls */
	if (isnull[0])
		return;

	/* Use memory context since detoast can allocate */
	oldCtx = MemoryContextSwitchTo(buildstate->tmpCtx);

	/* Add tuple to sort */
	AddTupleToSort(tid, values, buildstate);

	/* Reset memory context */
	MemoryContextSwitchTo(oldCtx);
	MemoryContextReset(buildstate->tmpCtx);
}
```

## 동작 흐름

```text
 CreateEntryPages(buildstate, forkNum)               L1023
   L1027 AssignTuples                                L977
           진행 단계 "assigning tuples"
           병렬 일꾼 수 > 0 이면 IvfflatBeginParallel (일꾼들도 같은 중심점으로 배정)
           L1003 sortstate = InitBuildSortState(sortdesc, maintenance_work_mem, coordinate)
                   키 = 1열(list), 연산자 Int4LessOperator
           L1011 table_index_build_scan(heap, index, ..., BuildCallback)
                   행마다 BuildCallback -> AddTupleToSort
   L1030 tuplesort_performsort                       리스트 번호 순
   L1033 [06] InsertTuples
   L1036 tuplesort_end

 AddTupleToSort(tid, values, buildstate)             L164
   L174  detoast
   L177  normprocinfo(FUNCTION 2) 가 있으면 노름 0 은 버리고, 아니면 정규화
   L186  차원 검사
   L189  i = 0 .. lists-1
           distance = FUNCTION 1 (value, centers[i])
           가장 작으면 closestCenter = i
   L207  slot = (closestCenter, tid, value)  가상 튜플
   L222  tuplesort_puttupleslot              값을 복사해 넣는다 (주석 L219-L220)
   L224  indtuples++
```

```text
 lists = 3 인 인덱스에 다섯 행

 힙 순서     가장 가까운 리스트     정렬기에 들어간 순서    정렬 뒤
 t1          2                      (2, t1, v1)            (0, t2, v2)
 t2          0                      (0, t2, v2)            (0, t4, v4)
 t3          1                      (1, t3, v3)            (1, t3, v3)
 t4          0                      (0, t4, v4)            (2, t1, v1)
 t5          2                      (2, t5, v5)            (2, t5, v5)

 같은 리스트 안의 순서는 키가 같으므로 정해지지 않는다 (정렬 키가 1열뿐)
 행 하나당 거리 계산 lists 번 -> 전체 N * lists 번
```

정렬기의 메모리 한도는 `maintenance_work_mem` 이고(L1003), 정렬 튜플에 벡터 열이 통째로 실린다(L212).

## 결과가 쓰이는 곳

```text
 정렬된 tuplesort
      --> [06] InsertTuples 가 GetNextTuple 로 하나씩 꺼낸다
 buildstate->indtuples
      --> ivfflatbuild 의 index_tuples
```

## 다루지 않는 것

병렬 배정(`IvfflatParallelScanAndSort`, 일꾼마다 `sortmem = maintenance_work_mem / 참가자 수`, L777, L826)과 공유 정렬기 병합(`tuplesort_initialize_shared`)은 요약만 했다.
