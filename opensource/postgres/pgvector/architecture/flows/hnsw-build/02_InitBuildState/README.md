# InitBuildState

상위: [HNSW 빌드](../README.md)

**빌드 상태 `HnswBuildState` 를 채우고, 빌드를 시작할 수 있는 열인지 검사하는 함수다.** 차원 수는 열의 typmod 에서 오고, `m` 과 `ef_construction` 은 인덱스 옵션에서 온다. 여기서 층 확률의 배율 `ml = 1/ln(m)` 과 층 상한 `maxLevel`, 그래프에 쓸 메모리 상한(`maintenance_work_mem`)이 정해진다.

## 위치

`src` / `hnswbuild.c` L686-L747 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L686-L747))

## 실제 코드

```c
// hnswbuild.c L683-L747
/*
 * Initialize the build state
 */
static void
InitBuildState(HnswBuildState * buildstate, Relation heap, Relation index, IndexInfo *indexInfo, ForkNumber forkNum)
{
	buildstate->heap = heap;
	buildstate->index = index;
	buildstate->indexInfo = indexInfo;
	buildstate->forkNum = forkNum;
	buildstate->typeInfo = HnswGetTypeInfo(index);

	buildstate->m = HnswGetM(index);
	buildstate->efConstruction = HnswGetEfConstruction(index);
	buildstate->dimensions = TupleDescAttr(index->rd_att, 0)->atttypmod;

	/* Disallow varbit since require fixed dimensions */
	if (TupleDescAttr(index->rd_att, 0)->atttypid == VARBITOID)
		ereport(ERROR,
				(errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
				 errmsg("type not supported for hnsw index")));

	/* Require column to have dimensions to be indexed */
	if (buildstate->dimensions < 0)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("column does not have dimensions")));

	if (buildstate->dimensions > buildstate->typeInfo->maxDimensions)
		ereport(ERROR,
				(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
				 errmsg("column cannot have more than %d dimensions for hnsw index", buildstate->typeInfo->maxDimensions)));

	if (buildstate->efConstruction / 2 < buildstate->m)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("ef_construction must be greater than or equal to 2 * m")));

	buildstate->reltuples = 0;
	buildstate->indtuples = 0;

	/* Get support functions */
	HnswInitSupport(&buildstate->support, index);

	InitGraph(&buildstate->graphData, NULL, mul_size(maintenance_work_mem, 1024));
	buildstate->graph = &buildstate->graphData;
	buildstate->ml = HnswGetMl(buildstate->m);
	buildstate->maxLevel = HnswGetMaxLevel(buildstate->m);

	buildstate->graphCtx = GenerationContextCreate(CurrentMemoryContext,
												   "Hnsw build graph context",
#if PG_VERSION_NUM >= 150000
												   1024 * 1024, 1024 * 1024,
#endif
												   1024 * 1024);
	buildstate->tmpCtx = AllocSetContextCreate(CurrentMemoryContext,
											   "Hnsw build temporary context",
											   ALLOCSET_DEFAULT_SIZES);

	InitAllocator(&buildstate->allocator, &HnswMemoryContextAlloc, buildstate);

	buildstate->hnswleader = NULL;
	buildstate->hnswshared = NULL;
	buildstate->hnswarea = NULL;
}
```

그래프의 공유 상태를 초기화하는 함수와 비병렬 빌드의 할당기다.

`src` / `hnswbuild.c` L617-L658 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L617-L658))

```c
// hnswbuild.c L614-L658
/*
 * Initialize the graph
 */
static void
InitGraph(HnswGraph * graph, char *base, Size memoryTotal)
{
	/* Initialize the lock tranche if needed */
	HnswInitLockTranche();

	HnswPtrStore(base, graph->head, (HnswElement) NULL);
	HnswPtrStore(base, graph->entryPoint, (HnswElement) NULL);
	graph->memoryUsed = 0;
	graph->memoryTotal = Min(memoryTotal, HNSW_MAX_GRAPH_MEMORY);
	graph->flushed = false;
	graph->indtuples = 0;
	SpinLockInit(&graph->lock);
	LWLockInitialize(&graph->entryLock, hnsw_lock_tranche_id);
	LWLockInitialize(&graph->entryWaitLock, hnsw_lock_tranche_id);
	LWLockInitialize(&graph->allocatorLock, hnsw_lock_tranche_id);
	LWLockInitialize(&graph->flushLock, hnsw_lock_tranche_id);
}

/*
 * Initialize an allocator
 */
static void
InitAllocator(HnswAllocator * allocator, void *(*alloc) (Size size, void *state), void *state)
{
	allocator->alloc = alloc;
	allocator->state = state;
}

/*
 * Memory context allocator
 */
static void *
HnswMemoryContextAlloc(Size size, void *state)
{
	HnswBuildState *buildstate = (HnswBuildState *) state;
	void	   *chunk = MemoryContextAlloc(buildstate->graphCtx, size);

	buildstate->graphData.memoryUsed = MemoryContextMemAllocated(buildstate->graphCtx, false);

	return chunk;
}
```

층 관련 매크로다.

`src` / `hnsw.h` L126-L133 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.h#L126-L133))

```c
// hnsw.h L126-L133
/* 2 * M connections for ground layer */
#define HnswGetLayerM(m, layer) (layer == 0 ? (m) * 2 : (m))

/* Optimal ML from paper */
#define HnswGetMl(m) (1 / log(m))

/* Ensure fits on page and in uint8 */
#define HnswGetMaxLevel(m) Min(((BLCKSZ - MAXALIGN(SizeOfPageHeaderData) - MAXALIGN(sizeof(HnswPageOpaqueData)) - offsetof(HnswNeighborTupleData, indextids) - sizeof(ItemIdData)) / (sizeof(ItemPointerData)) / (m)) - 2, 63)
```

## 동작 흐름

```text
 InitBuildState(buildstate, heap, index, indexInfo, forkNum)     L686
   L693  typeInfo  = HnswGetTypeInfo(index)          vector 면 기본값 (maxDimensions 2000)
   L695  m         = HnswGetM(index)                 옵션 없으면 16
   L696  efConstruction = HnswGetEfConstruction      옵션 없으면 64
   L697  dimensions = atttypmod                       vector(768) -> 768
   검사
     L700  열 타입이 varbit        -> "type not supported for hnsw index"
     L706  dimensions < 0          -> "column does not have dimensions"
     L711  dimensions > maxDimensions -> "cannot have more than 2000 dimensions"
     L716  efConstruction / 2 < m  -> "ef_construction must be >= 2 * m"
   L725  HnswInitSupport             --> [거리 연산자와 Index AM] 05
   L727  InitGraph(graphData, NULL, maintenance_work_mem * 1024)
           head = NULL, entryPoint = NULL, memoryUsed = 0, flushed = false
           LWLock 네 개 초기화 (entry, entryWait, allocator, flush)
   L729  ml       = 1 / ln(m)
   L730  maxLevel = HnswGetMaxLevel(m)
   L732  graphCtx = GenerationContext (1MB 블록)   원소와 이웃 배열이 여기 산다
   L738  tmpCtx   = AllocSetContext                행 하나 처리하고 비운다
   L742  allocator = HnswMemoryContextAlloc        할당마다 memoryUsed 를 갱신
```

`ml` 과 `maxLevel` 을 기본값 `m = 16` 으로 계산하면 다음과 같다.

```text
 ml = 1 / ln(16) = 0.3607

 maxLevel = Min( (BLCKSZ - 24 - 8 - 4 - 4) / 6 / m - 2 , 63 )      hnsw.h L133
          8192 - MAXALIGN(페이지 헤더 24) - MAXALIGN(opaque 8)
               - offsetof(HnswNeighborTupleData, indextids) 4 - ItemIdData 4 = 8152
          8152 / sizeof(ItemPointerData) 6 = 1358
          1358 / 16 = 84,  84 - 2 = 82
          Min(82, 63) = 63
   m = 100 이면  1358 / 100 = 13, 13 - 2 = 11  -> 층 상한 11

 뜻: 층 L 원소의 이웃 튜플은 (L + 2) * m 칸이다 (0층 2m + 위층 L*m)
     그 튜플이 한 페이지를 넘지 않을 L 의 최댓값, 그리고 uint8 로 63 까지 (주석 L132)
```

```text
 ef_construction 과 m 의 관계 (L716)

 m = 16, ef_construction = 64   64 / 2 = 32 >= 16   통과
 m = 16, ef_construction = 30   30 / 2 = 15 <  16   거절
 오류 문구 그대로 ef_construction >= 2 * m 을 요구한다. 0층 이웃 상한도 2m 이다 (HnswGetLayerM)
```

## 결과가 쓰이는 곳

```text
 buildstate->m, efConstruction, dimensions
      --> [09] CreateMetaPage 가 메타 페이지에 적는다
 buildstate->ml, maxLevel
      --> [05] HnswInitElement 의 층 뽑기
 graph->memoryTotal
      --> [04] InsertTuple 의 flush 판정
 allocator
      --> 원소, 이웃 배열, 값 복사가 모두 이것으로 할당된다
```

## 다루지 않는 것

병렬 빌드에서 일꾼마다 같은 함수를 부른 뒤 `graph` 와 `hnswarea` 를 공유 메모리 쪽으로 바꾸고 `HnswSharedMemoryAlloc` 을 꽂는 부분(L806-L809)은 [BuildGraph](../03_BuildGraph/README.md)에서 요약한다.
