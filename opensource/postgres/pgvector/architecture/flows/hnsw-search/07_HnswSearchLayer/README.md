# HnswSearchLayer

상위: [HNSW 검색](../README.md)

**한 층 안에서 검색 벡터에 가까운 원소를 최대 `ef` 개 찾는 함수, 논문의 Algorithm 2 다.** 두 개의 힙을 쓴다. 후보 힙 C 는 "다음에 이웃을 펼쳐 볼 원소"를 가까운 순으로, 결과 힙 W 는 "지금까지 찾은 가장 가까운 ef 개"를 먼 순으로 꺼내 준다. C 에서 가장 가까운 원소가 W 의 가장 먼 원소보다도 멀면 더 펼쳐 봐야 W 가 나아질 수 없으므로 멈춘다. 빌드(메모리 모드)와 검색·삽입(디스크 모드)이 모두 이 함수를 쓰고, 검색의 반복 스캔에서는 W 에서 밀려난 후보를 버리지 않고 `discarded` 힙에 모은다.

## 위치

`src` / `hnswutils.c` L827-L990 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L827-L990))

## 실제 코드

두 힙의 비교 함수, 방문 집합, ef 에 세는 규칙이다.

`src` / `hnswutils.c` L631-L731 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L631-L731))

```c
// hnswutils.c L628-L731
/*
 * Compare candidate distances
 */
static int
CompareNearestCandidates(const pairingheap_node *a, const pairingheap_node *b, void *arg)
{
	if (HnswGetSearchCandidateConst(c_node, a)->distance < HnswGetSearchCandidateConst(c_node, b)->distance)
		return 1;

	if (HnswGetSearchCandidateConst(c_node, a)->distance > HnswGetSearchCandidateConst(c_node, b)->distance)
		return -1;

	return 0;
}

/*
 * Compare discarded candidate distances
 */
static int
CompareNearestDiscardedCandidates(const pairingheap_node *a, const pairingheap_node *b, void *arg)
{
	if (HnswGetSearchCandidateConst(w_node, a)->distance < HnswGetSearchCandidateConst(w_node, b)->distance)
		return 1;

	if (HnswGetSearchCandidateConst(w_node, a)->distance > HnswGetSearchCandidateConst(w_node, b)->distance)
		return -1;

	return 0;
}

/*
 * Compare candidate distances
 */
static int
CompareFurthestCandidates(const pairingheap_node *a, const pairingheap_node *b, void *arg)
{
	if (HnswGetSearchCandidateConst(w_node, a)->distance < HnswGetSearchCandidateConst(w_node, b)->distance)
		return -1;

	if (HnswGetSearchCandidateConst(w_node, a)->distance > HnswGetSearchCandidateConst(w_node, b)->distance)
		return 1;

	return 0;
}

/*
 * Init visited
 */
static inline void
InitVisited(char *base, visited_hash * v, bool inMemory, int ef, int m)
{
	if (!inMemory)
		v->tids = tidhash_create(CurrentMemoryContext, ef * m * 2, NULL);
	else if (base != NULL)
		v->offsets = offsethash_create(CurrentMemoryContext, ef * m * 2, NULL);
	else
		v->pointers = pointerhash_create(CurrentMemoryContext, ef * m * 2, NULL);
}

/*
 * Add to visited
 */
static inline void
AddToVisited(char *base, visited_hash * v, HnswElementPtr elementPtr, bool inMemory, bool *found)
{
	if (!inMemory)
	{
		HnswElement element = HnswPtrAccess(base, elementPtr);
		ItemPointerData indextid;

		ItemPointerSet(&indextid, element->blkno, element->offno);
		tidhash_insert(v->tids, indextid, found);
	}
	else if (base != NULL)
	{
		HnswElement element = HnswPtrAccess(base, elementPtr);

		offsethash_insert_hash(v->offsets, HnswPtrOffset(elementPtr), element->hash, found);
	}
	else
	{
		HnswElement element = HnswPtrAccess(base, elementPtr);

		pointerhash_insert_hash(v->pointers, (uintptr_t) HnswPtrPointer(elementPtr), element->hash, found);
	}
}

/*
 * Count element towards ef
 */
static inline bool
CountElement(HnswElement skipElement, HnswElement e)
{
	if (skipElement == NULL)
		return true;

	/* Ensure does not access heaptidsLength during in-memory build */
	pg_memory_barrier();

	/* Keep scan-build happy on Mac x86-64 */
	Assert(e);

	return e->heaptidsLength != 0;
}
```

```c
// hnswutils.c L824-L990
/*
 * Algorithm 2 from paper
 */
List *
HnswSearchLayer(char *base, HnswQuery * q, List *ep, int ef, int lc, Relation index, HnswSupport * support, int m, bool inserting, HnswElement skipElement, visited_hash * v, pairingheap **discarded, bool initVisited, int64 *tuples)
{
	List	   *w = NIL;
	pairingheap *C = pairingheap_allocate(CompareNearestCandidates, NULL);
	pairingheap *W = pairingheap_allocate(CompareFurthestCandidates, NULL);
	int			wlen = 0;
	visited_hash vh;
	ListCell   *lc2;
	HnswNeighborArray *localNeighborhood = NULL;
	Size		neighborhoodSize = 0;
	int			lm = HnswGetLayerM(m, lc);
	HnswUnvisited *unvisited = palloc_array_checked(HnswUnvisited, lm);
	int			unvisitedLength;
	bool		inMemory = index == NULL;

	if (v == NULL)
	{
		v = &vh;
		initVisited = true;
	}

	if (initVisited)
	{
		InitVisited(base, v, inMemory, ef, m);

		if (discarded != NULL)
			*discarded = pairingheap_allocate(CompareNearestDiscardedCandidates, NULL);
	}

	/* Create local memory for neighborhood if needed */
	if (inMemory)
	{
		neighborhoodSize = HNSW_NEIGHBOR_ARRAY_SIZE(lm);
		localNeighborhood = palloc(neighborhoodSize);
	}

	/* Add entry points to v, C, and W */
	foreach(lc2, ep)
	{
		HnswSearchCandidate *sc = (HnswSearchCandidate *) lfirst(lc2);
		bool		found;

		if (initVisited)
		{
			AddToVisited(base, v, sc->element, inMemory, &found);

			/* OK to count elements instead of tuples */
			if (tuples != NULL)
				(*tuples)++;
		}

		pairingheap_add(C, &sc->c_node);
		pairingheap_add(W, &sc->w_node);

		/*
		 * Do not count elements being deleted towards ef when vacuuming. It
		 * would be ideal to do this for inserts as well, but this could
		 * affect insert performance.
		 */
		if (CountElement(skipElement, HnswPtrAccess(base, sc->element)))
			wlen++;
	}

	while (!pairingheap_is_empty(C))
	{
		HnswSearchCandidate *c = HnswGetSearchCandidate(c_node, pairingheap_remove_first(C));
		HnswSearchCandidate *f = HnswGetSearchCandidate(w_node, pairingheap_first(W));
		HnswElement cElement;

		if (c->distance > f->distance)
			break;

		cElement = HnswPtrAccess(base, c->element);

		if (inMemory)
			HnswLoadUnvisitedFromMemory(base, cElement, unvisited, &unvisitedLength, v, lc, localNeighborhood, neighborhoodSize);
		else
			HnswLoadUnvisitedFromDisk(cElement, unvisited, &unvisitedLength, v, index, m, lm, lc);

		/* OK to count elements instead of tuples */
		if (tuples != NULL)
			(*tuples) += unvisitedLength;

		for (int i = 0; i < unvisitedLength; i++)
		{
			HnswElement eElement;
			HnswSearchCandidate *e;
			double		eDistance;
			bool		alwaysAdd = wlen < ef;

			f = HnswGetSearchCandidate(w_node, pairingheap_first(W));

			if (inMemory)
			{
				eElement = unvisited[i].element;
				eDistance = GetElementDistance(base, eElement, q, support);
			}
			else
			{
				ItemPointer indextid = &unvisited[i].indextid;
				BlockNumber blkno = ItemPointerGetBlockNumber(indextid);
				OffsetNumber offno = ItemPointerGetOffsetNumber(indextid);

				/* Avoid any allocations if not adding */
				eElement = NULL;
				HnswLoadElementImpl(blkno, offno, &eDistance, q, index, support, inserting, alwaysAdd || discarded != NULL ? NULL : &f->distance, &eElement);

				if (eElement == NULL)
					continue;
			}

			if (!(eDistance < f->distance || alwaysAdd))
			{
				if (discarded != NULL)
				{
					/* Create a new candidate */
					e = HnswInitSearchCandidate(base, eElement, eDistance);
					pairingheap_add(*discarded, &e->w_node);
				}

				continue;
			}

			/* Make robust to issues */
			if (eElement->level < lc)
				continue;

			/* Create a new candidate */
			e = HnswInitSearchCandidate(base, eElement, eDistance);
			pairingheap_add(C, &e->c_node);
			pairingheap_add(W, &e->w_node);

			/*
			 * Do not count elements being deleted towards ef when vacuuming.
			 * It would be ideal to do this for inserts as well, but this
			 * could affect insert performance.
			 */
			if (CountElement(skipElement, eElement))
			{
				wlen++;

				/* No need to decrement wlen */
				if (wlen > ef)
				{
					HnswSearchCandidate *d = HnswGetSearchCandidate(w_node, pairingheap_remove_first(W));

					if (discarded != NULL)
						pairingheap_add(*discarded, &d->w_node);
				}
			}
		}
	}

	/* Add each element of W to w */
	while (!pairingheap_is_empty(W))
	{
		HnswSearchCandidate *sc = HnswGetSearchCandidate(w_node, pairingheap_remove_first(W));

		w = lappend(w, sc);
	}

	return w;
}
```

## 동작 흐름

```text
 HnswSearchLayer(base, q, ep, ef, lc, index, support, m, inserting, skipElement,
                 v, discarded, initVisited, tuples)                 L827
   L831  C = 가까운 것이 먼저 나오는 힙 (CompareNearestCandidates)
   L832  W = 먼 것이 먼저 나오는 힙 (CompareFurthestCandidates)
   L839  unvisited 배열 lm 칸
   L843  v 가 없으면 지역 방문 집합, initVisited 면 새로 만든다
           디스크 모드: tidhash(ef * m * 2) 크기로 시작          L680
           반복 스캔이면 discarded 힙도 만든다                     L854
   L865  ep 원소마다  v 에 넣고, C 와 W 에 넣고, wlen++

   L891  while C 가 비지 않았다
     L893  c = C 에서 가장 가까운 것 (꺼낸다)
     L894  f = W 에서 가장 먼 것 (보기만)
     L897  c.distance > f.distance 이면 break      더 펼쳐도 W 가 나아질 수 없다
     L902  c 의 lc 층 이웃 중 v 에 없던 것 -> unvisited   (v 에 추가)     --> [08]
     L911  unvisited 의 e 마다
             alwaysAdd = wlen < ef                W 가 아직 덜 찼다
             L933  디스크: HnswLoadElementImpl
                     alwaysAdd 도 아니고 discarded 도 없으면 maxDistance = f.distance
                     -> f 보다 멀면 원소를 만들지 않는다 (eElement == NULL -> continue)
             L939  e 가 f 보다 멀고 alwaysAdd 도 아니면
                     discarded 가 있으면 거기에 넣고 continue
             L952  e 의 level < lc 면 건너뜀        (손상에 대비)
             L956  e 를 C 와 W 에 넣는다
             L965  wlen++, wlen > ef 면 W 에서 가장 먼 것을 빼서 discarded 로
   L982  W 를 먼 것부터 꺼내 목록 w 에 붙인다
   L989  return w                               끝이 가장 가깝다
```

작은 예로 따라가 본다. 0층 그래프가 1차원 점 여섯 개이고, 검색 값 q = 0, 거리는 L2 제곱, ef = 2 다.

```text
 점과 q 와의 거리        0층 이웃
 A =  5   25            A: B, E
 B =  3    9            B: A, C
 C =  1    1            C: B, D, F
 D = -2    4            D: C
 E =  8   64            E: A
 F = 0.5   0.25         F: C
 진입점 ep = [A]

 step  c      f      new    W after          discarded   note
 0     -      -      A      A25              -           진입점
 1     A25    A25    B      A25 B9           -           wlen 1 < ef 라 alwaysAdd
              A25    E      A25 B9           E64         64 > f 25
 2     B9     A25    C      B9 C1            A25         wlen 3 > 2, 가장 먼 A 가 밀려남
 3     C1     B9     D      C1 D4            B9          4 < 9
              D4     F      C1 F0.25         D4          0.25 < 4
 4     F0.25  C1     -      C1 F0.25                     F 의 이웃 C 는 이미 봄
 5     D4     C1     -                                   4 > 1 이라 break
 결과 w = [C1, F0.25]    hnswgettuple 은 F 부터 낸다
 discarded = {D4, B9, A25, E64}   반복 스캔일 때만 모은다. [09] 가 여기서 다시 시작한다
 반복 스캔이 아니면 E 처럼 f 보다 먼 원소는 L933 에서 원소를 만들지도 않는다
```

`CountElement`(L718)는 VACUUM 이 지워지는 원소를 건너뛸 때만(`skipElement` 가 있을 때) 힙 TID 가 없는 원소를 `wlen` 에 세지 않는다. 검색은 `skipElement = NULL` 이라 모든 원소를 센다.

## 결과가 쓰이는 곳

```text
 w (HnswSearchCandidate 목록, 먼 것 -> 가까운 것)
      --> 검색 0층: [03] hnswgettuple 의 so->w
      --> 검색 위층, 빌드 1단계: 다음 층의 ep (ef = 1 이라 하나)
      --> 빌드 2단계: SelectNeighbors 의 후보 (빌드 [07])
 v, discarded, tuples
      --> 반복 스캔이 이어 쓴다 ([09] 는 initVisited = false 로 같은 v 를 넘긴다)
```

## 다루지 않는 것

메모리 모드의 방문 집합(`pointerhash`, `offsethash`)과 원소별 LWLock 아래에서 이웃 배열을 복사하는 `HnswLoadUnvisitedFromMemory`(L736)는 빌드 쪽이라 요약만 했다. `pairingheap` 자체는 PostgreSQL 의 `lib/pairingheap.c` 다.
