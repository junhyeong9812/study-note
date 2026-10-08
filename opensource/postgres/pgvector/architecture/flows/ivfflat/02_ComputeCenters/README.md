# ComputeCenters

상위: [IVFFlat 빌드와 검색](../README.md)

**k-means 에 넣을 표본을 뽑고 중심점 계산을 맡기는 함수다.** 표본 수는 리스트당 50 개를 목표로 하되 최소 1만 개이고, 테이블에 있을 수 있는 최대 행 수를 넘지 않는다. 표본은 `ANALYZE` 와 같은 방식으로 뽑는다. 블록을 무작위로 고르고(`BlockSampler`), 그 블록의 행을 저수지 표본(reservoir sampling)으로 받는다. 표본과 중심점을 담을 메모리는 미리 계산해 `maintenance_work_mem` 을 넘으면 오류를 낸다.

## 위치

`src` / `ivfbuild.c` L440-L486 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L440-L486))

## 실제 코드

```c
// ivfbuild.c L437-L486
/*
 * Compute centers
 */
static void
ComputeCenters(IvfflatBuildState * buildstate)
{
	int			numSamples;

	pgstat_progress_update_param(PROGRESS_CREATEIDX_SUBPHASE, PROGRESS_IVFFLAT_PHASE_KMEANS);

	/* Skip samples for unlogged table */
	if (buildstate->heap == NULL)
		numSamples = 1;
	else
	{
		int64		maxTuples = (int64) RelationGetNumberOfBlocks(buildstate->heap) * MaxHeapTuplesPerPage;

		/* Target 50 samples per list, with at least 10000 samples */
		/* The number of samples has a large effect on index build time */
		numSamples = buildstate->lists * 50;
		if (numSamples < 10000)
			numSamples = 10000;

		/* Save memory since will not have more than max tuples */
		numSamples = Max(Min(numSamples, maxTuples), 1);
	}

	/* Sample rows */
	buildstate->memoryUsed = add_size(buildstate->memoryUsed, VECTOR_ARRAY_SIZE(numSamples, buildstate->itemsize));
	IvfflatCheckMemoryUsage(buildstate->memoryUsed);
	buildstate->samples = VectorArrayInit(numSamples, buildstate->dimensions, buildstate->itemsize);
	if (buildstate->heap != NULL)
	{
		IvfflatBench("sample rows", SampleRows(buildstate));

		if (buildstate->samples->length < buildstate->lists)
		{
			ereport(NOTICE,
					(errmsg("ivfflat index created with little data"),
					 errdetail("This will cause low recall."),
					 errhint("Drop the index until the table has more data.")));
		}
	}

	/* Calculate centers */
	IvfflatBench("k-means", IvfflatKmeans(buildstate->index, buildstate->samples, buildstate->centers, buildstate->typeInfo, buildstate->memoryUsed));

	/* Free samples before we allocate more memory */
	VectorArrayFree(buildstate->samples);
}
```

표본을 뽑는 함수와, 행마다 불리는 콜백이다.

`src` / `ivfbuild.c` L56-L159 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L56-L159))

```c
// ivfbuild.c L53-L159
/*
 * Add sample
 */
static void
AddSample(Datum *values, IvfflatBuildState * buildstate)
{
	VectorArray samples = buildstate->samples;
	int			targsamples = samples->maxlen;

	/* Detoast once for all calls */
	Datum		value = PointerGetDatum(PG_DETOAST_DATUM(values[0]));

	/* Check dimensions match index */
	IvfflatCheckDim(buildstate->dimensions, buildstate->typeInfo, buildstate->collation, value);

	/*
	 * Check with KMEANS_NORM_PROC that the value can be normalized since
	 * spherical distance function expects unit vectors
	 */
	if (buildstate->kmeansnormprocinfo != NULL)
	{
		if (!IvfflatCheckNorm(buildstate->kmeansnormprocinfo, buildstate->collation, value))
			return;
	}

	if (samples->length < targsamples)
	{
		VectorArraySet(samples, samples->length, DatumGetPointer(value));
		samples->length++;
	}
	else
	{
		if (buildstate->rowstoskip < 0)
			buildstate->rowstoskip = reservoir_get_next_S(&buildstate->rstate, buildstate->samplerows, targsamples);

		if (buildstate->rowstoskip <= 0)
		{
#if PG_VERSION_NUM >= 150000
			int			k = (int) (targsamples * sampler_random_fract(&buildstate->rstate.randstate));
#else
			int			k = (int) (targsamples * sampler_random_fract(buildstate->rstate.randstate));
#endif

			Assert(k >= 0 && k < targsamples);
			VectorArraySet(samples, k, DatumGetPointer(value));
		}

		buildstate->rowstoskip -= 1;
	}

	/* Increment after reservoir_get_next_S */
	buildstate->samplerows += 1;
}

/*
 * Callback for sampling
 */
static void
SampleCallback(Relation index, ItemPointer tid, Datum *values,
			   bool *isnull, bool tupleIsAlive, void *state)
{
	IvfflatBuildState *buildstate = (IvfflatBuildState *) state;
	MemoryContext oldCtx;

	/* Skip nulls */
	if (isnull[0])
		return;

	/* Use memory context since detoast can allocate */
	oldCtx = MemoryContextSwitchTo(buildstate->tmpCtx);

	/* Add sample */
	AddSample(values, buildstate);

	/* Reset memory context */
	MemoryContextSwitchTo(oldCtx);
	MemoryContextReset(buildstate->tmpCtx);
}

/*
 * Sample rows with same logic as ANALYZE
 */
static void
SampleRows(IvfflatBuildState * buildstate)
{
	int			targsamples = buildstate->samples->maxlen;
	BlockNumber totalblocks = RelationGetNumberOfBlocks(buildstate->heap);

	buildstate->samplerows = 0;
	buildstate->rowstoskip = -1;

	BlockSampler_Init(&buildstate->bs, totalblocks, targsamples, RandomInt());

	reservoir_init_selection_state(&buildstate->rstate, targsamples);
	while (BlockSampler_HasMore(&buildstate->bs))
	{
		BlockNumber targblock = BlockSampler_Next(&buildstate->bs);

		/* Set anyvisible to false like table_index_build_scan */
		table_index_build_range_scan(buildstate->heap, buildstate->index, buildstate->indexInfo,
									 false, false, false, targblock, 1, SampleCallback, (void *) buildstate, NULL);
	}

	/* Normalize if needed */
	if (buildstate->kmeansnormprocinfo != NULL)
		IvfflatNormVectors(buildstate->typeInfo, buildstate->collation, buildstate->samples, buildstate->tmpCtx);
}
```

메모리 검사다.

`src` / `ivfutils.c` L125-L134 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfutils.c#L125-L134))

```c
// ivfutils.c L122-L134
/*
 * Check memory usage
 */
void
IvfflatCheckMemoryUsage(Size totalSize)
{
	/* Add one to error message to ceil */
	if (totalSize / 1024 > (Size) maintenance_work_mem)
		ereport(ERROR,
				(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
				 errmsg("memory required is %zu MB, maintenance_work_mem is %d MB",
						totalSize / (1024 * 1024) + 1, maintenance_work_mem / 1024)));
}
```

## 동작 흐름

```text
 ComputeCenters(buildstate)                          L440
   L445  진행 단계 "performing k-means"
   L448  heap 이 없으면 (UNLOGGED 의 init fork) 표본 1 칸
   L452  maxTuples = 블록 수 * MaxHeapTuplesPerPage
   L456  numSamples = lists * 50, 1만보다 작으면 1만
   L461  Min(numSamples, maxTuples), 최소 1
   L465  memoryUsed += VECTOR_ARRAY_SIZE(numSamples, itemsize)
   L466  IvfflatCheckMemoryUsage            넘으면 "memory required is N MB, maintenance_work_mem is M MB"
   L467  samples = VectorArrayInit
   L470  SampleRows                         L135
           BlockSampler_Init(블록 수, numSamples, 난수)
           reservoir_init_selection_state
           고른 블록마다 table_index_build_range_scan(블록 하나, SampleCallback)
             AddSample                      L56
               detoast, 차원 검사
               kmeans 정규화(FUNCTION 4)가 있고 노름 0 이면 버림
               표본이 덜 찼으면 뒤에 붙이고
               찼으면 reservoir_get_next_S 만큼 건너뛰고 무작위 칸 k 를 덮어쓴다
           FUNCTION 4 가 있으면 표본 전체를 정규화
   L472  표본 수 < lists 면 NOTICE "ivfflat index created with little data"
   L482  [03] IvfflatKmeans(index, samples, centers, typeInfo, memoryUsed)
   L485  표본 해제
```

```text
 표본 수와 메모리 (vector(768), 항목 크기 MAXALIGN(8 + 4*768) = 3080 바이트)
 전제: 테이블이 충분히 커서 maxTuples = 블록 수 * MaxHeapTuplesPerPage (L452) 가
       numSamples 보다 크다 — 작으면 L461 에서 maxTuples 로 줄어 표의 값보다 작아진다

 lists   lists*50   numSamples   표본 배열          중심점 배열
 100     5,000      10,000       30,800,032 B       308,032 B
 1,000   50,000     50,000       154,000,032 B      3,080,032 B
 VECTOR_ARRAY_SIZE(n, size) = sizeof(VectorArrayData) 32 + n * MAXALIGN(size)

 maintenance_work_mem = 64MB (65,536 KB) 일 때
   lists 100    30.8MB + 0.3MB              통과
   lists 1000   154MB + 3MB = 157,080,064 B
                157,080,064 / 1024 = 153,398 KB > 65,536 KB
                -> "memory required is 150 MB, maintenance_work_mem is 64 MB"   (L466)
```

표본 크기를 정하는 주석(L454-L455)은 "리스트당 50 개, 최소 1만"을 목표로 적고, 표본 수가 빌드 시간에 큰 영향을 준다고 덧붙인다.

## 결과가 쓰이는 곳

```text
 buildstate->centers (lists 개의 중심점, k-means 결과)
      --> [04] CreateListPages 가 리스트 튜플의 center 로 쓴다
      --> [05] AddTupleToSort 가 행마다 가장 가까운 중심점을 찾는다
 buildstate->memoryUsed
      --> ElkanKmeans 가 자기 할당량을 더해 다시 검사한다
```

## 다루지 않는 것

`BlockSampler` 와 저수지 표본의 수학(PostgreSQL `utils/misc/sampling.c`), `table_index_build_range_scan` 의 가시성 처리(`anyvisible = false`, 주석 L151)는 다루지 않았다.
