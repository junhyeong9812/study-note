# hnswbuild

상위: [HNSW 빌드](../README.md)

**HNSW 의 `ambuild` 이다.** 본문은 `BuildIndex` 하나를 부르고 행 수 두 개를 돌려주는 것뿐이다. `BuildIndex` 가 상태를 준비하고(`InitBuildState`), 그래프를 짓고(`BuildGraph`), 테이블이 WAL 을 남기는 종류면 인덱스의 모든 블록을 페이지째 WAL 에 기록한 뒤 메모리를 정리한다. UNLOGGED 테이블용 `hnswbuildempty` 도 같은 `BuildIndex` 를 힙 없이, init fork 를 대상으로 부른다.

## 위치

`src` / `hnswbuild.c` L1151-L1164 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L1151-L1164))

## 실제 코드

파일 머리 주석이 빌드의 두 단계를 설명한다.

`src` / `hnswbuild.c` L1-L36 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L1-L36))

```c
// hnswbuild.c L1-L36
/*
 * The HNSW build happens in two phases:
 *
 * 1. In-memory phase
 *
 * In this first phase, the graph is held completely in memory. When the graph
 * is fully built, or we run out of memory reserved for the build (determined
 * by maintenance_work_mem), we materialize the graph to disk (see
 * FlushPages()), and switch to the on-disk phase.
 *
 * In a parallel build, a large contiguous chunk of shared memory is allocated
 * to hold the graph. Each worker process has its own HnswBuildState struct in
 * private memory, which contains information that doesn't change throughout
 * the build, and pointers to the shared structs in shared memory. The shared
 * memory area is mapped to a different address in each worker process, and
 * 'HnswBuildState.hnswarea' points to the beginning of the shared area in the
 * worker process's address space. All pointers used in the graph are
 * "relative pointers", stored as an offset from 'hnswarea'.
 *
 * Each element is protected by an LWLock. It must be held when reading or
 * modifying the element's neighbors or 'heaptids'.
 *
 * In a non-parallel build, the graph is held in backend-private memory. All
 * the elements are allocated in a dedicated memory context, 'graphCtx', and
 * the pointers used in the graph are regular pointers.
 *
 * 2. On-disk phase
 *
 * In the on-disk phase, the index is built by inserting each vector to the
 * index one by one, just like on INSERT. The only difference is that we don't
 * WAL-log the individual inserts. If the graph fit completely in memory and
 * was fully built in the in-memory phase, the on-disk phase is skipped.
 *
 * After we have finished building the graph, we perform one more scan through
 * the index and write all the pages to the WAL.
 */
```

```c
// hnswbuild.c L1127-L1176
/*
 * Build the index
 */
static void
BuildIndex(Relation heap, Relation index, IndexInfo *indexInfo,
		   HnswBuildState * buildstate, ForkNumber forkNum)
{
#ifdef HNSW_MEMORY
	SeedRandom(42);
#endif

	InitBuildState(buildstate, heap, index, indexInfo, forkNum);

	BuildGraph(buildstate);

	if (RelationNeedsWAL(index) || forkNum == INIT_FORKNUM)
		log_newpage_range(index, forkNum, 0, RelationGetNumberOfBlocksInFork(index, forkNum), true);

	FreeBuildState(buildstate);
}

/*
 * Build the index for a logged table
 */
IndexBuildResult *
hnswbuild(Relation heap, Relation index, IndexInfo *indexInfo)
{
	IndexBuildResult *result;
	HnswBuildState buildstate;

	BuildIndex(heap, index, indexInfo, &buildstate, MAIN_FORKNUM);

	result = palloc_object(IndexBuildResult);
	result->heap_tuples = buildstate.reltuples;
	result->index_tuples = buildstate.indtuples;

	return result;
}

/*
 * Build the index for an unlogged table
 */
void
hnswbuildempty(Relation index)
{
	IndexInfo  *indexInfo = BuildIndexInfo(index);
	HnswBuildState buildstate;

	BuildIndex(NULL, index, indexInfo, &buildstate, INIT_FORKNUM);
}
```

## 동작 흐름

```text
 hnswbuild(heap, index, indexInfo)                   L1151
   L1157 BuildIndex(heap, index, indexInfo, &buildstate, MAIN_FORKNUM)
           L1138 [02] InitBuildState
           L1140 [03] BuildGraph
           L1142 RelationNeedsWAL(index) || INIT_FORKNUM 이면
                   log_newpage_range(index, forkNum, 0, nblocks, true)
           L1145 FreeBuildState              graphCtx, tmpCtx 삭제
   L1160 result->heap_tuples  = reltuples    힙에서 본 행 수
   L1161 result->index_tuples = indtuples    인덱스에 들어간 행 수

 hnswbuildempty(index)                               L1170
   L1175 BuildIndex(NULL, index, ..., INIT_FORKNUM)
           heap 이 NULL 이라 BuildGraph 가 스캔을 건너뛴다
           -> 빈 그래프를 flush: 메타 페이지 + 빈 원소 페이지 하나
           INIT_FORKNUM 이라 log_newpage_range 는 늘 한다
```

WAL 을 언제 쓰는지가 HNSW 빌드와 INSERT 의 큰 차이다.

```text
 빌드 중 페이지 쓰기와 WAL

 빌드 (building = true)
   CreateMetaPage, CreateGraphPages, WriteNeighborTuples   MarkBufferDirty 만
   디스크 단계 HnswInsertTupleOnDisk(..., true)              GenericXLog 를 쓰지 않음
   마지막에 log_newpage_range 로 블록 0 .. N-1 전부        (머리 주석 L34-L35)

 INSERT (building = false)
   AddElementOnDisk, UpdateNeighborOnDisk, HnswUpdateMetaPage
   GenericXLogStart -> GenericXLogRegisterBuffer -> GenericXLogFinish  (hnswinsert.c L194 등)
```

`heap_tuples` 와 `index_tuples` 가 다를 수 있다. NULL 행은 `BuildCallback` 이 건너뛰고(L594), 코사인 계열에서 크기가 0 인 벡터는 `HnswFormIndexValue` 가 버린다. 같은 값의 행이 여러 개면 원소 하나에 힙 TID 가 붙어도(최대 10개) 행마다 `indtuples` 가 하나씩 늘어난다.

## 결과가 쓰이는 곳

```text
 IndexBuildResult
      --> index_build 가 pg_class 통계를 갱신한다
 인덱스 블록 0 .. N-1 과 그 WAL 레코드
      --> 복구와 복제 대기 서버가 같은 인덱스를 갖는다
```

## 다루지 않는 것

`log_newpage_range` 의 레코드 모양(PostgreSQL `xloginsert.c`)과 `HNSW_MEMORY` 빌드의 `SeedRandom(42)`(L1134-L1136)는 다루지 않았다.
