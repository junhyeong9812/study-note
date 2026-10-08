# ivfflatgettuple

상위: [IVFFlat 빌드와 검색](../README.md)

**IVFFlat 인덱스 스캔의 `amgettuple` 이다.** 첫 호출에서 검색 값을 준비하고, 가까운 리스트를 고르고([08]), 그 리스트들의 항목을 모두 거리와 함께 정렬기에 넣어 정렬한다([09]). 이후 호출은 정렬기에서 다음 행을 꺼낼 뿐이다. 정렬기가 바닥났을 때 아직 훑지 않은 후보 리스트가 남아 있으면(반복 스캔에서만 생긴다) 다음 묶음을 훑어 이어 간다. 스캔 상태를 만드는 `ivfflatbeginscan` 이 `probes` 와 `maxProbes` 를 정하므로 함께 본다.

## 위치

`src` / `ivfscan.c` L363-L417 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfscan.c#L363-L417))

## 실제 코드

```c
// ivfscan.c L252-L333
/*
 * Prepare for an index scan
 */
IndexScanDesc
ivfflatbeginscan(Relation index, int nkeys, int norderbys)
{
	IndexScanDesc scan;
	IvfflatScanOpaque so;
	int			lists;
	int			dimensions;
	int			probes = ivfflat_probes;
	int			maxProbes;
	MemoryContext oldCtx;

	scan = RelationGetIndexScan(index, nkeys, norderbys);

	/* Get lists and dimensions from metapage */
	IvfflatGetMetaPageInfo(index, &lists, &dimensions);

	if (ivfflat_iterative_scan != IVFFLAT_ITERATIVE_SCAN_OFF)
		maxProbes = Max(ivfflat_max_probes, probes);
	else
		maxProbes = probes;

	if (probes > lists)
		probes = lists;

	if (maxProbes > lists)
		maxProbes = lists;

	so = palloc_object(IvfflatScanOpaqueData);
	so->typeInfo = IvfflatGetTypeInfo(index);
	so->first = true;
	so->probes = probes;
	so->maxProbes = maxProbes;
	so->dimensions = dimensions;
	so->value = PointerGetDatum(NULL);

	/* Set support functions */
	so->procinfo = index_getprocinfo(index, 1, IVFFLAT_DISTANCE_PROC);
	so->normprocinfo = IvfflatOptionalProcInfo(index, IVFFLAT_NORM_PROC);
	so->collation = index->rd_indcollation[0];

	so->tmpCtx = AllocSetContextCreate(CurrentMemoryContext,
									   "Ivfflat scan temporary context",
									   ALLOCSET_DEFAULT_SIZES);

	oldCtx = MemoryContextSwitchTo(so->tmpCtx);

	/* Create tuple description for sorting */
	so->tupdesc = CreateTemplateTupleDesc(2);
	TupleDescInitEntry(so->tupdesc, (AttrNumber) 1, "distance", FLOAT8OID, -1, 0);
	TupleDescInitEntry(so->tupdesc, (AttrNumber) 2, "heaptid", TIDOID, -1, 0);
#if PG_VERSION_NUM >= 190000
	TupleDescFinalize(so->tupdesc);
#endif

	/* Prep sort */
	so->sortstate = InitScanSortState(so->tupdesc);

	/* Need separate slots for puttuple and gettuple */
	so->vslot = MakeSingleTupleTableSlot(so->tupdesc, &TTSOpsVirtual);
	so->mslot = MakeSingleTupleTableSlot(so->tupdesc, &TTSOpsMinimalTuple);

	/*
	 * Reuse same set of shared buffers for scan
	 *
	 * See postgres/src/backend/storage/buffer/README for description
	 */
	so->bas = GetAccessStrategy(BAS_BULKREAD);

	so->listQueue = pairingheap_allocate(CompareLists, scan);
	so->listPages = palloc_array_checked(BlockNumber, maxProbes);
	so->listIndex = 0;
	so->lists = palloc_array_checked(IvfflatScanList, maxProbes);

	MemoryContextSwitchTo(oldCtx);

	scan->opaque = so;

	return scan;
}
```

```c
// ivfscan.c L360-L417
/*
 * Fetch the next tuple in the given scan
 */
bool
ivfflatgettuple(IndexScanDesc scan, ScanDirection dir)
{
	IvfflatScanOpaque so = (IvfflatScanOpaque) scan->opaque;
	ItemPointer heaptid;
	bool		isnull;

	/*
	 * Index can be used to scan backward, but Postgres doesn't support
	 * backward scan on operators
	 */
	Assert(ScanDirectionIsForward(dir));

	if (so->first)
	{
		Datum		value;

		/* Count index scan for stats */
		pgstat_count_index_scan(scan->indexRelation);
#if PG_VERSION_NUM >= 180000
		if (scan->instrument)
			scan->instrument->nsearches++;
#endif

		/* Safety check */
		if (scan->orderByData == NULL)
			elog(ERROR, "cannot scan ivfflat index without order");

		/* Requires MVCC-compliant snapshot as not able to pin during sorting */
		/* https://www.postgresql.org/docs/current/index-locking.html */
		if (!IsMVCCSnapshot(scan->xs_snapshot))
			elog(ERROR, "non-MVCC snapshots are not supported with ivfflat");

		value = GetScanValue(scan);
		IvfflatBench("GetScanLists", GetScanLists(scan, value));
		IvfflatBench("GetScanItems", GetScanItems(scan, value));
		so->first = false;
		so->value = value;
	}

	while (!tuplesort_gettupleslot(so->sortstate, true, false, so->mslot, NULL))
	{
		if (so->listIndex == so->maxProbes)
			return false;

		IvfflatBench("GetScanItems", GetScanItems(scan, so->value));
	}

	heaptid = (ItemPointer) DatumGetPointer(slot_getattr(so->mslot, 2, &isnull));

	scan->xs_heaptid = *heaptid;
	scan->xs_recheck = false;
	scan->xs_recheckorderby = false;
	return true;
}
```

검색 값을 꺼내는 함수다. NULL 이면 거리 함수를 0 을 돌려주는 함수로 바꾼다.

`src` / `ivfscan.c` L192-L236 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfscan.c#L192-L236))

```c
// ivfscan.c L189-L236
/*
 * Zero distance
 */
static Datum
ZeroDistance(FmgrInfo *flinfo, Oid collation, Datum arg1, Datum arg2)
{
	return Float8GetDatum(0.0);
}

/*
 * Get scan value
 */
static Datum
GetScanValue(IndexScanDesc scan)
{
	IvfflatScanOpaque so = (IvfflatScanOpaque) scan->opaque;
	Datum		value;

	if (scan->orderByData->sk_flags & SK_ISNULL)
	{
		value = PointerGetDatum(NULL);
		so->distfunc = ZeroDistance;
	}
	else
	{
		value = scan->orderByData->sk_argument;
		so->distfunc = FunctionCall2Coll;

		/* Value should not be compressed or toasted */
		Assert(!VARATT_IS_COMPRESSED(DatumGetPointer(value)));
		Assert(!VARATT_IS_EXTENDED(DatumGetPointer(value)));

		/* Normalize if needed */
		if (so->normprocinfo != NULL)
		{
			MemoryContext oldCtx = MemoryContextSwitchTo(so->tmpCtx);

			value = IvfflatNormValue(so->typeInfo, so->collation, value);

			MemoryContextSwitchTo(oldCtx);
		}

		/* Check dimensions match index */
		IvfflatCheckDim(so->dimensions, so->typeInfo, so->collation, value);
	}

	return value;
}
```

## 동작 흐름

```text
 ivfflatbeginscan(index, nkeys, norderbys)           L255
   L262  probes = ivfflat.probes                  기본 1
   L269  IvfflatGetMetaPageInfo -> lists, dimensions
   L271  maxProbes = 반복 스캔이면 Max(ivfflat.max_probes, probes), 아니면 probes
   L276  probes, maxProbes 를 lists 로 자른다
   L291  procinfo = FUNCTION 1, normprocinfo = FUNCTION 2
   L302  정렬 튜플 모양 (distance float8, heaptid tid)
   L310  sortstate: 1열을 Float8LessOperator 로, 메모리 work_mem
   L321  bas = BAS_BULKREAD                      항목 페이지 읽기에 링 버퍼
   L323  listQueue (리스트 힙), listPages[maxProbes], lists[maxProbes]

 ivfflatgettuple(scan, dir)                          L363
   L376  first 이면
           orderByData 없으면 오류, MVCC 스냅샷 아니면 오류   (정렬 중 핀을 쥘 수 없다, 주석 L391)
           L396  GetScanValue      NULL 이면 ZeroDistance, 정규화, 차원 검사
           L397  [08] GetScanLists
           L398  [09] GetScanItems
   L403  while 정렬기에서 못 꺼냈다
           listIndex == maxProbes -> return false
           [09] GetScanItems (다음 probes 개 리스트)
   L411  heaptid = 슬롯 2열
   L413  xs_heaptid, recheck 없음 -> return true
```

```text
 설정에 따른 probes, maxProbes (lists = 100)

 ivfflat.probes   iterative_scan   max_probes   probes   maxProbes   훑는 리스트
 1 (기본)         off (기본)       -            1        1           1 개, 그리고 끝
 10               off              -            10       10          10 개, 그리고 끝
 10               relaxed_order    32768 (기본) 10       100         10 개씩, 최대 100 개
 10               relaxed_order    20           10       20          10 개씩, 최대 20 개
 200              off              -            100      100         전부 = 정확한 검색
```

반복 스캔을 켜면 묶음마다 정렬기를 비우고 새로 채우므로(`tuplesort_reset`, [09] L131), 결과는 묶음 안에서만 거리 순이다. IVFFlat 의 반복 스캔 모드는 `off` 와 `relaxed_order` 둘뿐이다(ivfflat.c L29-L33).

## 결과가 쓰이는 곳

```text
 scan->xs_heaptid
      --> 실행기가 힙 튜플을 읽고 가시성을 본다
 xs_recheck = false, xs_recheckorderby = false
      --> 반환 순서가 곧 결과 순서다
```

## 다루지 않는 것

`ivfflatrescan`(L338)은 리스트 힙과 `listIndex` 를 초기화하고 정규화한 이전 검색 값을 해제한다. `ivfflatendscan`(L422)은 정렬기를 끝내 임시 파일을 지운다. 둘 다 요약만 했다.
