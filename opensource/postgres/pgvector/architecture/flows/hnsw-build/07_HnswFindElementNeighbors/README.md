# HnswFindElementNeighbors

상위: [HNSW 빌드](../README.md)

**새 원소가 층마다 연결될 이웃을 고르는 함수, HNSW 논문의 Algorithm 1 이다.** 진입점의 층에서 새 원소의 층 바로 위까지는 폭 1 로 탐색해 가장 가까운 하나만 들고 내려온다. 새 원소의 층부터 0층까지는 폭 `ef_construction` 으로 후보를 모으고, 그중 `lm`(0층 2m, 위층 m) 개를 `SelectNeighbors`(Algorithm 4)로 고른다. 고르는 기준은 단순히 가까운 순이 아니다. 이미 고른 이웃보다 새 원소에 더 가까운 후보만 먼저 받아 이웃이 한쪽으로 몰리지 않게 하고, 자리가 남으면 버린 후보로 채운다.

## 위치

`src` / `hnswutils.c` L1283-L1360 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L1283-L1360))

## 실제 코드

```c
// hnswutils.c L1280-L1360
/*
 * Algorithm 1 from paper
 */
void
HnswFindElementNeighbors(char *base, HnswElement element, HnswElement entryPoint, Relation index, HnswSupport * support, int m, int efConstruction, bool existing)
{
	List	   *ep;
	List	   *w;
	int			level = element->level;
	int			entryLevel;
	HnswQuery	q;
	HnswElement skipElement = existing ? element : NULL;
	bool		inMemory = index == NULL;

	q.value = HnswGetValue(base, element);

	/* Precompute hash */
	if (inMemory)
		PrecomputeHash(base, element);

	/* No neighbors if no entry point */
	if (entryPoint == NULL)
		return;

	/* Get entry point and level */
	ep = list_make1(HnswEntryCandidate(base, entryPoint, &q, index, support, true));
	entryLevel = entryPoint->level;

	/* 1st phase: greedy search to insert level */
	for (int lc = entryLevel; lc >= level + 1; lc--)
	{
		w = HnswSearchLayer(base, &q, ep, 1, lc, index, support, m, true, skipElement, NULL, NULL, true, NULL);
		ep = w;
	}

	if (level > entryLevel)
		level = entryLevel;

	/* Add one for existing element */
	if (existing)
		efConstruction++;

	/* 2nd phase */
	for (int lc = level; lc >= 0; lc--)
	{
		int			lm = HnswGetLayerM(m, lc);
		List	   *neighbors;
		List	   *lw = NIL;
		ListCell   *lc2;

		w = HnswSearchLayer(base, &q, ep, efConstruction, lc, index, support, m, true, skipElement, NULL, NULL, true, NULL);

		/* Convert search candidates to candidates */
		foreach(lc2, w)
		{
			HnswSearchCandidate *sc = lfirst(lc2);
			HnswCandidate *hc = palloc_object(HnswCandidate);

			hc->element = sc->element;
			hc->distance = sc->distance;

			lw = lappend(lw, hc);
		}

		/* Elements being deleted or skipped can help with search */
		/* but should be removed before selecting neighbors */
		if (!inMemory)
			lw = RemoveElements(base, lw, skipElement);

		/*
		 * Candidates are sorted, but not deterministically. Could set
		 * sortCandidates to true for in-memory builds to enable closer
		 * caching, but there does not seem to be a difference in performance.
		 */
		neighbors = SelectNeighbors(base, lw, lm, support, &HnswGetNeighbors(base, element, lc)->closerSet, NULL, NULL, false);

		AddConnections(base, element, neighbors, lc);

		ep = w;
	}
}
```

이웃 고르기와 그 판정 함수다.

`src` / `hnswutils.c` L1040-L1181 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L1040-L1181))

```c
// hnswutils.c L1040-L1181
/*
 * Check if an element is closer to q than any element from R
 */
static bool
CheckElementCloser(char *base, HnswCandidate * e, List *r, HnswSupport * support)
{
	HnswElement eElement = HnswPtrAccess(base, e->element);
	Datum		eValue = HnswGetValue(base, eElement);
	ListCell   *lc2;

	foreach(lc2, r)
	{
		HnswCandidate *ri = lfirst(lc2);
		HnswElement riElement = HnswPtrAccess(base, ri->element);
		Datum		riValue = HnswGetValue(base, riElement);
		float		distance = HnswGetDistance(eValue, riValue, support);

		if (distance <= e->distance)
			return false;
	}

	return true;
}

/*
 * Algorithm 4 from paper
 */
static List *
SelectNeighbors(char *base, List *c, int lm, HnswSupport * support, bool *closerSet, HnswCandidate * newCandidate, HnswCandidate * *pruned, bool sortCandidates)
{
	List	   *r = NIL;
	List	   *w = list_copy(c);
	HnswCandidate **wd;
	int			wdlen = 0;
	int			wdoff = 0;
	bool		mustCalculate = !(*closerSet);
	List	   *added = NIL;
	bool		removedAny = false;

	if (list_length(w) <= lm)
		return w;

	wd = palloc_array_checked(HnswCandidate *, list_length(w));

	/* Ensure order of candidates is deterministic for closer caching */
	if (sortCandidates)
	{
		if (base == NULL)
			list_sort(w, CompareCandidateDistances);
		else
			list_sort(w, CompareCandidateDistancesOffset);
	}

	while (list_length(w) > 0 && list_length(r) < lm)
	{
		/* Assumes w is already ordered desc */
		HnswCandidate *e = llast(w);

		w = list_delete_last(w);

		/* Use previous state of r and wd to skip work when possible */
		if (mustCalculate)
			e->closer = CheckElementCloser(base, e, r, support);
		else if (list_length(added) > 0)
		{
			/* Keep Valgrind happy for in-memory, parallel builds */
			if (base != NULL)
				VALGRIND_MAKE_MEM_DEFINED(&e->closer, 1);

			/*
			 * If the current candidate was closer, we only need to compare it
			 * with the other candidates that we have added.
			 */
			if (e->closer)
			{
				e->closer = CheckElementCloser(base, e, added, support);

				if (!e->closer)
					removedAny = true;
			}
			else
			{
				/*
				 * If we have removed any candidates from closer, a candidate
				 * that was not closer earlier might now be.
				 */
				if (removedAny)
				{
					e->closer = CheckElementCloser(base, e, r, support);
					if (e->closer)
						added = lappend(added, e);
				}
			}
		}
		else if (e == newCandidate)
		{
			e->closer = CheckElementCloser(base, e, r, support);
			if (e->closer)
				added = lappend(added, e);
		}

		/* Keep Valgrind happy for in-memory, parallel builds */
		if (base != NULL)
			VALGRIND_MAKE_MEM_DEFINED(&e->closer, 1);

		if (e->closer)
			r = lappend(r, e);
		else
			wd[wdlen++] = e;
	}

	/* Cached value can only be used in future if sorted deterministically */
	*closerSet = sortCandidates;

	/* Keep pruned connections */
	while (wdoff < wdlen && list_length(r) < lm)
		r = lappend(r, wd[wdoff++]);

	/* Return pruned for update connections */
	if (pruned != NULL)
	{
		if (wdoff < wdlen)
			*pruned = wd[wdoff];
		else
			*pruned = linitial(w);
	}

	return r;
}

/*
 * Add connections
 */
static void
AddConnections(char *base, HnswElement element, List *neighbors, int lc)
{
	ListCell   *lc2;
	HnswNeighborArray *a = HnswGetNeighbors(base, element, lc);

	foreach(lc2, neighbors)
		a->items[a->length++] = *((HnswCandidate *) lfirst(lc2));
}
```

## 동작 흐름

```text
 HnswFindElementNeighbors(base, element, entryPoint, index, support, m, efC, existing)   L1283
   L1294 q.value = 원소의 값
   L1297 메모리 모드면 PrecomputeHash          방문 집합 해시를 미리
   L1301 entryPoint == NULL 이면 return        첫 원소: 이웃 없음
   L1305 ep = [HnswEntryCandidate(진입점)]     진입점과 q 의 거리
   1단계  L1309 lc = entryLevel .. level+1
            w = HnswSearchLayer(q, ep, ef = 1, lc)     --> [HNSW 검색] 07
            ep = w                                      가장 가까운 하나
   L1315 level = Min(level, entryLevel)
   L1319 existing(VACUUM 의 재연결)이면 efC + 1
   2단계  L1323 lc = level .. 0
            lm = HnswGetLayerM(m, lc)
            w  = HnswSearchLayer(q, ep, ef = efC, lc)    후보 최대 efC 개, 먼 것부터
            L1333 HnswCandidate 목록 lw 로 바꾼다
            L1346 디스크 모드면 RemoveElements      지워지는 원소, 자기 자신 제외
            L1354 neighbors = SelectNeighbors(lw, lm)
            L1356 AddConnections -> element 의 lc 층 이웃 배열에 복사
            L1358 ep = w                             다음 층의 출발점은 후보 전체
```

```text
 level 1 원소를 진입점 level 3 그래프에 넣을 때 (m = 16, ef_construction = 64)

 층 3   ep(진입점) --ef 1--> 가장 가까운 p3
 층 2   [p3]      --ef 1--> 가장 가까운 p2
 층 1   [p2]      --ef 64--> 후보 W1 (<= 64 개) -> SelectNeighbors(lm 16) -> 이웃 <= 16 개
 층 0   W1 전체   --ef 64--> 후보 W0 (<= 64 개) -> SelectNeighbors(lm 32) -> 이웃 <= 32 개
```

`SelectNeighbors` 는 후보를 가까운 것부터 하나씩 꺼내, 이미 고른 이웃 r 중 하나라도 그 후보와 더 가까우면(거리 <= 후보와 q 의 거리) 그 후보를 버림 목록 wd 에 넣는다.

```text
 SelectNeighbors 예 (2차원, 거리 = L2 제곱, lm = 2)

 q = (0,0)   후보 a = (1,0)   b = (1.2,0.1)   c = (0,2)
 q 와의 거리   a 1             b 1.45           c 4
 lw 순서 (먼 것부터) [c, b, a]  -> llast 부터 꺼낸다

 e = a   r 가 비어 있음                  closer       r = [a]
 e = b   d(b,a) = 0.04 + 0.01 = 0.05 <= 1.45   아님   wd = [b]
 e = c   d(c,a) = 1 + 4 = 5 > 4          closer       r = [a, c]
 r 이 lm 에 찼으니 끝.  결과 [a, c]

 가까운 순으로만 골랐다면 [a, b] 였다
 r 이 lm 보다 적게 끝나면 wd 에서 앞에서부터 채운다 (L1155)
```

`closer` 결과는 후보 구조체에 남겨 두었다가(`closerSet`), 이웃 목록이 꽉 찬 원소에 새 이웃을 넣을 때(`HnswUpdateConnection`) 다시 계산하지 않고 재사용한다. 재사용은 후보 순서가 결정적일 때만 안전하므로 `sortCandidates` 가 참일 때만 `closerSet` 을 켠다(L1151-L1152). 이 함수의 2단계는 `sortCandidates = false` 로 부른다(L1354, 주석 L1349-L1353).

## 결과가 쓰이는 곳

```text
 element 의 층별 이웃 배열 (AddConnections)
      --> [08] UpdateGraphInMemory 가 이 이웃들에게 역방향 연결을 만든다
      --> [09] HnswSetNeighborTuple 이 이웃 튜플로 옮긴다
 같은 함수가 index 를 받으면
      --> INSERT 와 디스크 단계 (hnswinsert.c L738), VACUUM 의 재연결 (existing = true)
```

## 다루지 않는 것

`HnswSearchLayer` 의 본문은 [HNSW 검색 의 HnswSearchLayer](../../hnsw-search/07_HnswSearchLayer/README.md)에 있다. `RemoveElements`(L1239)의 메모리 장벽, 정렬 비교 함수(`CompareCandidateDistances`, L995)의 동점 처리는 요약만 했다.
