# InsertTuple

상위: [HNSW 빌드](../README.md)

**빌드 중 힙 행 하나를 그래프에 넣는 갈림길이다.** 값을 인덱스용으로 다듬고 차원을 검사한 뒤, 그래프가 이미 디스크로 쏟아졌으면 디스크 삽입으로, 메모리가 다 찼으면 지금 쏟아 내고 디스크 삽입으로, 그렇지 않으면 원소를 할당해 메모리 그래프에 넣는다. 두 개의 잠금(flushLock, allocatorLock)이 병렬 일꾼 사이에서 "flush 중에는 아무도 넣지 않는다"와 "공유 영역 할당은 한 번에 하나"를 지킨다.

## 위치

`src` / `hnswbuild.c` L485-L580 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L485-L580))

## 실제 코드

`table_index_build_scan` 이 행마다 부르는 콜백이 먼저다.

`src` / `hnswbuild.c` L585-L612 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L585-L612))

```c
// hnswbuild.c L582-L612
/*
 * Callback for table_index_build_scan
 */
static void
BuildCallback(Relation index, ItemPointer tid, Datum *values,
			  bool *isnull, bool tupleIsAlive, void *state)
{
	HnswBuildState *buildstate = (HnswBuildState *) state;
	HnswGraph  *graph = buildstate->graph;
	MemoryContext oldCtx;

	/* Skip nulls */
	if (isnull[0])
		return;

	/* Use memory context */
	oldCtx = MemoryContextSwitchTo(buildstate->tmpCtx);

	/* Insert tuple */
	if (InsertTuple(index, values, isnull, tid, buildstate))
	{
		/* Update progress */
		SpinLockAcquire(&graph->lock);
		pgstat_progress_update_param(PROGRESS_CREATEIDX_TUPLES_DONE, ++graph->indtuples);
		SpinLockRelease(&graph->lock);
	}

	/* Reset memory context */
	MemoryContextSwitchTo(oldCtx);
	MemoryContextReset(buildstate->tmpCtx);
}
```

```c
// hnswbuild.c L482-L580
/*
 * Insert tuple
 */
static bool
InsertTuple(Relation index, Datum *values, bool *isnull, ItemPointer heaptid, HnswBuildState * buildstate)
{
	HnswGraph  *graph = buildstate->graph;
	HnswElement element;
	HnswAllocator *allocator = &buildstate->allocator;
	HnswSupport *support = &buildstate->support;
	Size		valueSize;
	Pointer		valuePtr;
	LWLock	   *flushLock = &graph->flushLock;
	char	   *base = buildstate->hnswarea;
	Datum		value;
	Size		memoryMargin;

	/* Form index value */
	if (!HnswFormIndexValue(&value, values, isnull, buildstate->typeInfo, support))
		return false;

	/* Check dimensions match index */
	HnswCheckDim(buildstate->dimensions, buildstate->typeInfo, support->collation, value);

	/* Get datum size */
	valueSize = VARSIZE_ANY(DatumGetPointer(value));

	/* In a parallel build, add a margin so allocations never fail */
	memoryMargin = base == NULL ? 0 : 1024 * 1024;

	/* Ensure graph not flushed when inserting */
	LWLockAcquire(flushLock, LW_SHARED);

	/* Are we in the on-disk phase? */
	if (graph->flushed)
	{
		LWLockRelease(flushLock);

		return HnswInsertTupleOnDisk(index, buildstate->typeInfo, support, value, heaptid, true);
	}

	/*
	 * In a parallel build, the HnswElement is allocated from the shared
	 * memory area, so we need to coordinate with other processes.
	 */
	LWLockAcquire(&graph->allocatorLock, LW_EXCLUSIVE);

	/*
	 * Check that we have enough memory available for the new element now that
	 * we have the allocator lock, and flush pages if needed.
	 */
	if (add_size(graph->memoryUsed, memoryMargin) >= graph->memoryTotal)
	{
		LWLockRelease(&graph->allocatorLock);

		LWLockRelease(flushLock);
		LWLockAcquire(flushLock, LW_EXCLUSIVE);

		if (!graph->flushed)
		{
			ereport(NOTICE,
					(errmsg("hnsw graph no longer fits into maintenance_work_mem after " INT64_FORMAT " tuples", (int64) graph->indtuples),
					 errdetail("Building will take significantly more time."),
					 errhint("Increase maintenance_work_mem to speed up builds.")));

			FlushPages(buildstate);
		}

		LWLockRelease(flushLock);

		return HnswInsertTupleOnDisk(index, buildstate->typeInfo, support, value, heaptid, true);
	}

	/* Ok, we can proceed to allocate the element */
	element = HnswInitElement(base, heaptid, buildstate->m, buildstate->ml, buildstate->maxLevel, allocator);
	valuePtr = HnswAlloc(allocator, valueSize);

	/*
	 * We have now allocated the space needed for the element, so we don't
	 * need the allocator lock anymore. Release it and initialize the rest of
	 * the element.
	 */
	LWLockRelease(&graph->allocatorLock);

	/* Copy the datum */
	memcpy(valuePtr, DatumGetPointer(value), valueSize);
	HnswPtrStore(base, element->value, (char *) valuePtr);

	/* Create a lock for the element */
	LWLockInitialize(&element->lock, hnsw_lock_tranche_id);

	/* Insert tuple */
	InsertTupleInMemory(buildstate, element);

	/* Release flush lock */
	LWLockRelease(flushLock);

	return true;
}
```

## 동작 흐름

```text
 BuildCallback(index, tid, values, isnull, ...)      L586
   L594  NULL 이면 건너뜀
   L598  tmpCtx 로 전환
   L601  InsertTuple 이 true 면 graph->indtuples++, 진행률 갱신
   L611  tmpCtx 비우기          detoast, 정규화 복사본이 여기서 사라진다

 InsertTuple(index, values, isnull, heaptid, buildstate)   L485
   L500  HnswFormIndexValue     false(크기 0) 면 return false
   L504  HnswCheckDim           값의 차원 != 인덱스 차원이면 오류
   L507  valueSize = VARSIZE_ANY(value)
   L510  memoryMargin = 병렬이면 1MB, 아니면 0
   L513  flushLock 공유
   L516  graph->flushed ?
           예  -> 잠금 풀고 HnswInsertTupleOnDisk(..., building=true)      디스크 단계
   L527  allocatorLock 배타
   L533  memoryUsed + margin >= memoryTotal ?
           예  -> 잠금 둘 다 풀고 flushLock 배타로 다시
                  L540  아직 아무도 flush 안 했으면
                          NOTICE "hnsw graph no longer fits into maintenance_work_mem after N tuples"
                          [09] FlushPages
                  L552  HnswInsertTupleOnDisk(..., true)
   L556  [05] HnswInitElement   원소 + 층 + 이웃 배열 할당
   L557  HnswAlloc(valueSize)   값 자리 할당
   L564  allocatorLock 해제     할당은 끝났으니 나머지는 잠금 없이
   L567  값 복사, element->value 에 연결
   L571  원소의 LWLock 초기화
   L574  [06] InsertTupleInMemory
   L577  flushLock 해제
```

```text
 flush 를 둘러싼 잠금 (병렬 일꾼 A, B)

 A: flushLock S --- allocatorLock X --- 할당 --- allocatorLock 해제 --- 삽입 --- flushLock 해제
 B:     flushLock S --- allocatorLock X (A 해제 기다림) --- 메모리 부족 발견
                    --- allocatorLock 해제, flushLock S 해제 --- flushLock X (A 의 S 해제 기다림)
                    --- flushed 다시 확인 -> FlushPages --- flushLock 해제 --- 디스크 삽입
 A 가 다음 행에서 flushLock S 를 잡으면 flushed = true 를 보고 바로 디스크 삽입으로 간다
```

메모리 판정은 할당하기 전에 한다. `memoryUsed` 는 비병렬에서 `MemoryContextMemAllocated(graphCtx)`(L655), 병렬에서 공유 영역에 쌓인 바이트 수(L679)다. 병렬에서는 영역이 고정 크기라 넘치면 할당이 실패하므로 1MB 여유(`memoryMargin`)를 두고 판정한다(주석 L509).

## 결과가 쓰이는 곳

```text
 true
      --> BuildCallback 이 graph->indtuples 를 1 올린다 -> index_tuples
 메모리 그래프의 새 원소
      --> 이후 행의 이웃 후보가 되고, 마지막에 [09] FlushPages 로 페이지가 된다
 디스크 단계로 간 행
      --> HnswInsertTupleOnDisk 가 곧바로 인덱스 페이지를 고친다 (WAL 없이)
```

## 다루지 않는 것

`HnswInsertTupleOnDisk`(hnswinsert.c L695)의 본문은 `INSERT` 경로와 같다. 메타 페이지에서 진입점을 읽고, 같은 `HnswFindElementNeighbors` 를 `index` 를 넘겨 디스크 모드로 부르고, `AddElementOnDisk` 로 빈자리에 튜플을 넣은 뒤 이웃들의 이웃 튜플을 고친다. 그 세부는 이 지도 범위 밖이다.
