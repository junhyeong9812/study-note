# BuildGraph

상위: [HNSW 빌드](../README.md)

**힙을 훑어 행마다 `BuildCallback` 을 부르게 하고, 다 끝나면 아직 메모리에 있는 그래프를 페이지로 쏟아 내는 함수다.** 병렬 빌드가 가능하면 먼저 일꾼 프로세스를 띄워 같은 공유 메모리 그래프에 함께 넣게 한다. 리더도 일꾼처럼 힙의 일부를 맡고, 모두 끝나면 리더 혼자 flush 한다.

## 위치

`src` / `hnswbuild.c` L1091-L1125 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L1091-L1125))

## 실제 코드

```c
// hnswbuild.c L1067-L1125
/*
 * Compute parallel workers
 */
static int
ComputeParallelWorkers(Relation heap, Relation index)
{
	int			parallel_workers;

	/* Make sure it's safe to use parallel workers */
	parallel_workers = plan_create_index_workers(RelationGetRelid(heap), RelationGetRelid(index));
	if (parallel_workers == 0)
		return 0;

	/* Use parallel_workers storage parameter on table if set */
	parallel_workers = RelationGetParallelWorkers(heap, -1);
	if (parallel_workers != -1)
		return Min(parallel_workers, max_parallel_maintenance_workers);

	return max_parallel_maintenance_workers;
}

/*
 * Build graph
 */
static void
BuildGraph(HnswBuildState * buildstate)
{
	int			parallel_workers = 0;

	pgstat_progress_update_param(PROGRESS_CREATEIDX_SUBPHASE, PROGRESS_HNSW_PHASE_LOAD);

	/* Calculate parallel workers */
	if (buildstate->heap != NULL)
		parallel_workers = ComputeParallelWorkers(buildstate->heap, buildstate->index);

	/* Attempt to launch parallel worker scan when required */
	if (parallel_workers > 0)
		HnswBeginParallel(buildstate, buildstate->indexInfo->ii_Concurrent, parallel_workers);

	/* Add tuples to graph */
	if (buildstate->heap != NULL)
	{
		if (buildstate->hnswleader)
			buildstate->reltuples = ParallelHeapScan(buildstate);
		else
			buildstate->reltuples = table_index_build_scan(buildstate->heap, buildstate->index, buildstate->indexInfo,
														   true, true, BuildCallback, (void *) buildstate, NULL);

		buildstate->indtuples = buildstate->graph->indtuples;
	}

	/* Flush pages */
	if (!buildstate->graph->flushed)
		FlushPages(buildstate);

	/* End parallel build */
	if (buildstate->hnswleader)
		HnswEndParallel(buildstate->hnswleader);
}
```

병렬 빌드가 그래프를 둘 공유 메모리 크기를 정하는 부분과, 일꾼이 그 영역에 붙는 부분이다.

`src` / `hnswbuild.c` L957-L972 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L957-L972))

```c
// hnswbuild.c L957-L972
	/* Estimate size of workspaces */
	esthnswshared = ParallelEstimateShared(buildstate->heap, snapshot);
	shm_toc_estimate_chunk(&pcxt->estimator, esthnswshared);

	/* Leave space for other objects in shared memory */
	/* Docker has a default limit of 64 MB for shm_size */
	/* which happens to be the default value of maintenance_work_mem */
	esthnswarea = mul_size(maintenance_work_mem, 1024);
	estother = 3 * 1024 * 1024;
	if (esthnswarea > estother)
		esthnswarea -= estother;

	esthnswarea = Min(esthnswarea, HNSW_MAX_GRAPH_MEMORY);

	shm_toc_estimate_chunk(&pcxt->estimator, esthnswarea);
	shm_toc_estimate_keys(&pcxt->estimator, 2);
```

`src` / `hnswbuild.c` L795-L836 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L795-L836))

```c
// hnswbuild.c L795-L836
static void
HnswParallelScanAndInsert(Relation heapRel, Relation indexRel, HnswShared * hnswshared, char *hnswarea, bool progress)
{
	HnswBuildState buildstate;
	TableScanDesc scan;
	double		reltuples;
	IndexInfo  *indexInfo;

	/* Join parallel scan */
	indexInfo = BuildIndexInfo(indexRel);
	indexInfo->ii_Concurrent = hnswshared->isconcurrent;
	InitBuildState(&buildstate, heapRel, indexRel, indexInfo, MAIN_FORKNUM);
	buildstate.graph = &hnswshared->graphData;
	buildstate.hnswarea = hnswarea;
	InitAllocator(&buildstate.allocator, &HnswSharedMemoryAlloc, &buildstate);
	scan = table_beginscan_parallel(heapRel,
									ParallelTableScanFromHnswShared(hnswshared)
#if PG_VERSION_NUM >= 190000
									,SO_NONE
#endif
		);
	reltuples = table_index_build_scan(heapRel, indexRel, indexInfo,
									   true, progress, BuildCallback,
									   (void *) &buildstate, scan);

	/* Record statistics */
	SpinLockAcquire(&hnswshared->mutex);
	hnswshared->nparticipantsdone++;
	hnswshared->reltuples += reltuples;
	SpinLockRelease(&hnswshared->mutex);

	/* Log statistics */
	if (progress)
		ereport(DEBUG1, (errmsg("leader processed " INT64_FORMAT " tuples", (int64) reltuples)));
	else
		ereport(DEBUG1, (errmsg("worker processed " INT64_FORMAT " tuples", (int64) reltuples)));

	/* Notify leader */
	ConditionVariableSignal(&hnswshared->workersdonecv);

	FreeBuildState(&buildstate);
}
```

## 동작 흐름

```text
 BuildGraph(buildstate)                              L1091
   L1096 진행 단계 = PROGRESS_HNSW_PHASE_LOAD ("loading tuples")
   L1100 ComputeParallelWorkers                      L1070
           plan_create_index_workers 가 0 이면 0
           테이블의 parallel_workers 옵션이 있으면 Min(그것, max_parallel_maintenance_workers)
           없으면 max_parallel_maintenance_workers
   L1104 > 0 이면 HnswBeginParallel
   L1107 heap 이 있으면
           병렬    ParallelHeapScan       모든 참가자가 끝날 때까지 조건 변수로 대기 (L762)
           비병렬  table_index_build_scan(heap, index, ..., BuildCallback)   L1112
   L1115 indtuples = graph->indtuples
   L1119 아직 flush 안 됐으면 [09] FlushPages
   L1123 병렬이면 HnswEndParallel          일꾼 종료 대기, DSM 해제
```

```text
 병렬 빌드의 메모리 (HnswBeginParallel L928)

 리더 프로세스                          공유 메모리 (DSM)
 +---------------------+               +---------------------------------------+
 | HnswBuildState      |               | HnswShared                            |
 |   graph  ----------------------->   |   graphData (HnswGraph)               |
 |   hnswarea ------------------+      |   병렬 테이블 스캔 상태                 |
 +---------------------+        |      +---------------------------------------+
                                +--->  | hnswarea  maintenance_work_mem - 3MB   |
 일꾼 프로세스 (HnswParallelBuildMain)  |   원소, 이웃 배열, 값이 차례로 쌓인다   |
 +---------------------+               |   포인터는 hnswarea 기준 오프셋(relptr) |
 | HnswBuildState      |  같은 영역 -> +---------------------------------------+
 |   allocator = HnswSharedMemoryAlloc |
 +---------------------+

 esthnswarea = maintenance_work_mem * 1024 - 3MB   (3MB 보다 클 때, L964-L968)
 주석 L962-L963: Docker 기본 shm 64MB 가 maintenance_work_mem 기본값과 같아서 여유를 둔다
```

비병렬 빌드는 그래프를 백엔드 사설 메모리 `graphCtx` 에 두고 보통 포인터를 쓴다. 병렬 빌드는 프로세스마다 공유 영역이 다른 주소에 매핑되므로 포인터 대신 영역 시작점 기준 오프셋을 쓴다(머리 주석 L11-L18). `HnswPtrAccess(base, hp)` 매크로가 `base == NULL` 이면 보통 포인터로, 아니면 상대 포인터로 읽는다(hnsw.h L145).

## 결과가 쓰이는 곳

```text
 buildstate->reltuples   --> hnswbuild 의 heap_tuples
 buildstate->indtuples   --> hnswbuild 의 index_tuples
 flush 된 인덱스 페이지   --> BuildIndex 가 log_newpage_range 로 WAL 에 남긴다
```

## 다루지 않는 것

`HnswBeginParallel` 의 DSM 키 등록과 스냅샷 처리(`CREATE INDEX CONCURRENTLY` 면 MVCC 스냅샷, 아니면 `SnapshotAny`, L952-L955), 일꾼 수를 정하는 `plan_create_index_workers`(PostgreSQL 플래너)의 기준은 다루지 않았다.
