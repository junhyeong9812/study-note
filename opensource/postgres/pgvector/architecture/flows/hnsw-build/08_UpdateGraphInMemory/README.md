# UpdateGraphInMemory

상위: [HNSW 빌드](../README.md)

**이웃을 고른 새 원소를 그래프에 실제로 붙이는 함수다.** 먼저 0층 이웃 중 값이 똑같은 원소가 있으면 새 원소는 버리고 그 원소에 힙 TID 만 붙인다. 아니면 원소를 전역 목록 맨 앞에 연결하고, 자기가 고른 이웃들 각각의 이웃 목록에 자기를 넣는다(역방향 연결). 이웃의 목록이 꽉 차 있으면 새 원소를 포함한 `lm + 1` 개 중에서 다시 골라 하나를 뺀다. 마지막으로 층이 더 높으면 진입점을 바꾼다.

## 위치

`src` / `hnswbuild.c` L413-L432 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L413-L432))

## 실제 코드

```c
// hnswbuild.c L318-L432
/*
 * Add a heap TID to an existing element
 */
static bool
AddDuplicateInMemory(HnswElement element, HnswElement dup)
{
	LWLockAcquire(&dup->lock, LW_EXCLUSIVE);

	if (dup->heaptidsLength == HNSW_HEAPTIDS)
	{
		LWLockRelease(&dup->lock);
		return false;
	}

	HnswAddHeapTid(dup, &element->heaptids[0]);

	LWLockRelease(&dup->lock);

	return true;
}

/*
 * Find duplicate element
 */
static bool
FindDuplicateInMemory(char *base, HnswElement element)
{
	HnswNeighborArray *neighbors = HnswGetNeighbors(base, element, 0);
	Datum		value = HnswGetValue(base, element);

	for (int i = 0; i < neighbors->length; i++)
	{
		HnswCandidate *neighbor = &neighbors->items[i];
		HnswElement neighborElement = HnswPtrAccess(base, neighbor->element);
		Datum		neighborValue = HnswGetValue(base, neighborElement);

		/* Exit early since ordered by distance */
		if (!datumIsEqual(value, neighborValue, false, -1))
			return false;

		/* Check for space */
		if (AddDuplicateInMemory(element, neighborElement))
			return true;
	}

	return false;
}

/*
 * Add to element list
 */
static void
AddElementInMemory(char *base, HnswGraph * graph, HnswElement element)
{
	SpinLockAcquire(&graph->lock);
	element->next = graph->head;
	HnswPtrStore(base, graph->head, element);
	SpinLockRelease(&graph->lock);
}

/*
 * Update neighbors
 */
static void
UpdateNeighborsInMemory(char *base, HnswSupport * support, HnswElement e, int m)
{
	for (int lc = e->level; lc >= 0; lc--)
	{
		int			lm = HnswGetLayerM(m, lc);
		Size		neighborsSize = HNSW_NEIGHBOR_ARRAY_SIZE(lm);
		HnswNeighborArray *neighbors = palloc(neighborsSize);

		/* Copy neighbors to local memory */
		LWLockAcquire(&e->lock, LW_SHARED);
		memcpy(neighbors, HnswGetNeighbors(base, e, lc), neighborsSize);
		LWLockRelease(&e->lock);

		for (int i = 0; i < neighbors->length; i++)
		{
			HnswCandidate *hc = &neighbors->items[i];
			HnswElement neighborElement = HnswPtrAccess(base, hc->element);

			/* Keep scan-build happy on Mac x86-64 */
			Assert(neighborElement);

			LWLockAcquire(&neighborElement->lock, LW_EXCLUSIVE);
			HnswUpdateConnection(base, HnswGetNeighbors(base, neighborElement, lc), e, hc->distance, lm, NULL, NULL, support);
			LWLockRelease(&neighborElement->lock);
		}
	}
}

/*
 * Update graph in memory
 */
static void
UpdateGraphInMemory(HnswSupport * support, HnswElement element, int m, HnswElement entryPoint, HnswBuildState * buildstate)
{
	HnswGraph  *graph = buildstate->graph;
	char	   *base = buildstate->hnswarea;

	/* Look for duplicate */
	if (FindDuplicateInMemory(base, element))
		return;

	/* Add element */
	AddElementInMemory(base, graph, element);

	/* Update neighbors */
	UpdateNeighborsInMemory(base, support, element, m);

	/* Update entry point if needed (already have lock) */
	if (entryPoint == NULL || element->level > entryPoint->level)
		HnswPtrStore(base, graph->entryPoint, element);
}
```

꽉 찬 이웃 목록에 새 연결을 넣는 함수다. INSERT 의 디스크 경로도 같은 함수를 쓴다.

`src` / `hnswutils.c` L1186-L1234 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L1186-L1234))

```c
// hnswutils.c L1183-L1234
/*
 * Update connections
 */
void
HnswUpdateConnection(char *base, HnswNeighborArray * neighbors, HnswElement newElement, float distance, int lm, int *updateIdx, Relation index, HnswSupport * support)
{
	HnswCandidate newHc;

	HnswPtrStore(base, newHc.element, newElement);
	newHc.distance = distance;

	if (neighbors->length < lm)
	{
		neighbors->items[neighbors->length++] = newHc;

		/* Track update */
		if (updateIdx != NULL)
			*updateIdx = -2;
	}
	else
	{
		/* Shrink connections */
		List	   *c = NIL;
		HnswCandidate *pruned = NULL;

		/* Add candidates */
		for (int i = 0; i < neighbors->length; i++)
			c = lappend(c, &neighbors->items[i]);
		c = lappend(c, &newHc);

		SelectNeighbors(base, c, lm, support, &neighbors->closerSet, &newHc, &pruned, true);

		/* Should not happen */
		if (pruned == NULL)
			return;

		/* Find and replace the pruned element */
		for (int i = 0; i < neighbors->length; i++)
		{
			if (HnswPtrEqual(base, neighbors->items[i].element, pruned->element))
			{
				neighbors->items[i] = newHc;

				/* Track update */
				if (updateIdx != NULL)
					*updateIdx = i;

				break;
			}
		}
	}
}
```

## 동작 흐름

```text
 UpdateGraphInMemory(support, element, m, entryPoint, buildstate)   L413
   L420  FindDuplicateInMemory                       L342
           0층 이웃을 가까운 순으로
             값이 다르면 바로 false                   L355 (가까운 순이라 더 볼 필요 없다)
             같으면 AddDuplicateInMemory              L322
               dup->lock X, heaptids 가 10 개면 false (다음 이웃으로)
               아니면 heaptids 에 추가 -> true
           true 면 return     새 원소는 그래프에 붙지 않는다
   L424  AddElementInMemory                          L369
           graph->lock (스핀락) 아래 element->next = head, head = element
   L427  UpdateNeighborsInMemory                     L381
           lc = level .. 0
             e 의 lc 층 이웃 배열을 e->lock S 로 지역 메모리에 복사
             이웃 n 마다
               n->lock X
               HnswUpdateConnection(n 의 lc 층 배열, e, 거리, lm)
               n->lock 해제
   L430  entryPoint == NULL 또는 element->level > entryPoint->level
           graph->entryPoint = element      (entryLock X 를 이미 쥐고 있다)
```

```text
 HnswUpdateConnection(neighbors, newElement, distance, lm)      L1186

 neighbors->length < lm
   items[length++] = 새 후보                   빈칸이 있으면 그냥 붙인다

 꽉 찼으면 (length == lm)
   c = items 전부 + 새 후보                     lm + 1 개
   SelectNeighbors(c, lm, closerSet, newCandidate, &pruned, sortCandidates = true)
     -> 고르지 못한 하나 = pruned
   items 에서 pruned 를 찾아 그 자리에 새 후보
   pruned 가 새 후보 자신이면 items 에 없으므로 아무것도 바뀌지 않는다
```

```text
 0층 이웃이 꽉 찬 원소 n (m = 16, lm = 32) 에 새 원소 e 가 연결을 요청할 때

 n.items  [x1 x2 ... x32]   closerSet = true (꽉 찬 뒤 이미 한 번 이 함수로 갱신됐다)
 c        [x1 ... x32, e]   거리 순으로 정렬 (L1085, 동점은 포인터 순)
 SelectNeighbors
   closer 를 처음부터 다시 계산하지 않는다 (mustCalculate = false)
   e 차례가 되면 e 만 r 과 비교 (L1134)
   e 가 closer 면 added 에 넣고, 이후 closer 였던 후보는 added 하고만 비교 (L1113)
 pruned = 버림 목록의 첫 후보, 버림 목록이 다 쓰였으면 남은 것 중 가장 먼 것
 e -> n.items 의 pruned 자리
```

방향 그래프로 보면 새 원소는 자기 이웃 모두를 가리키지만, 이웃은 이 과정을 거쳐 남을 때만 새 원소를 가리킨다. 그래서 연결이 항상 양방향은 아니다.

## 결과가 쓰이는 곳

```text
 graph->head 목록
      --> [09] CreateGraphPages, WriteNeighborTuples 가 이 목록을 처음부터 따라간다
          (맨 앞에 붙이므로 페이지에는 나중에 넣은 원소가 먼저 놓인다)
 이웃 배열
      --> 다음 원소들의 HnswSearchLayer 가 메모리 모드로 읽는다 (HnswLoadUnvisitedFromMemory)
 graph->entryPoint
      --> 다음 원소의 탐색 시작점, [09] 에서 메타 페이지의 진입점
```

## 다루지 않는 것

INSERT 의 디스크 판은 `UpdateGraphOnDisk`(hnswinsert.c L668)다. 같은 순서(중복 확인, 원소 추가, 이웃 갱신, 진입점 갱신)를 페이지 위에서 하고, 이웃 갱신은 `GetUpdateIndex` 로 바꿀 칸을 정한 뒤 이웃 튜플의 그 칸 하나만 고친다(`UpdateNeighborOnDisk` L473). 그 세부는 범위 밖이다.
