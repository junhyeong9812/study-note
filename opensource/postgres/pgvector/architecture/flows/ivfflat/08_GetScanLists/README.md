# GetScanLists

상위: [IVFFlat 빌드와 검색](../README.md)

**리스트 페이지를 처음부터 끝까지 읽어 모든 중심점과 검색 벡터의 거리를 재고, 가장 가까운 `maxProbes` 개 리스트의 첫 항목 페이지 번호를 가까운 순으로 늘어놓는 함수다.** 크기 `maxProbes` 의 최대 힙(가장 먼 것이 맨 위)을 쓴다. 힙이 차면 맨 위보다 가까운 리스트가 나올 때만 맨 위를 빼고 그것을 넣는다. 리스트 수만큼 거리를 계산하므로 `lists` 가 클수록 이 단계가 길다.

## 위치

`src` / `ivfscan.c` L47-L118 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfscan.c#L47-L118))

## 실제 코드

```c
// ivfscan.c L26-L118
#define GetScanList(ptr) pairingheap_container(IvfflatScanList, ph_node, ptr)
#define GetScanListConst(ptr) pairingheap_const_container(IvfflatScanList, ph_node, ptr)

/*
 * Compare list distances
 */
static int
CompareLists(const pairingheap_node *a, const pairingheap_node *b, void *arg)
{
	if (GetScanListConst(a)->distance > GetScanListConst(b)->distance)
		return 1;

	if (GetScanListConst(a)->distance < GetScanListConst(b)->distance)
		return -1;

	return 0;
}

/*
 * Get lists and sort by distance
 */
static void
GetScanLists(IndexScanDesc scan, Datum value)
{
	IvfflatScanOpaque so = (IvfflatScanOpaque) scan->opaque;
	BlockNumber nextblkno = IVFFLAT_HEAD_BLKNO;
	int			listCount = 0;
	double		maxDistance = DBL_MAX;

	/* Search all list pages */
	while (BlockNumberIsValid(nextblkno))
	{
		Buffer		cbuf;
		Page		cpage;
		OffsetNumber maxoffno;

		cbuf = ReadBuffer(scan->indexRelation, nextblkno);
		LockBuffer(cbuf, BUFFER_LOCK_SHARE);
		cpage = BufferGetPage(cbuf);

		maxoffno = PageGetMaxOffsetNumber(cpage);

		for (OffsetNumber offno = FirstOffsetNumber; offno <= maxoffno; offno = OffsetNumberNext(offno))
		{
			IvfflatList list = (IvfflatList) PageGetItem(cpage, PageGetItemId(cpage, offno));
			double		distance;

			/* Use procinfo from the index instead of scan key for performance */
			distance = DatumGetFloat8(so->distfunc(so->procinfo, so->collation, PointerGetDatum(&list->center), value));

			if (listCount < so->maxProbes)
			{
				IvfflatScanList *scanlist;

				scanlist = &so->lists[listCount];
				scanlist->startPage = list->startPage;
				scanlist->distance = distance;
				listCount++;

				/* Add to heap */
				pairingheap_add(so->listQueue, &scanlist->ph_node);

				/* Calculate max distance */
				if (listCount == so->maxProbes)
					maxDistance = GetScanList(pairingheap_first(so->listQueue))->distance;
			}
			else if (distance < maxDistance)
			{
				IvfflatScanList *scanlist;

				/* Remove */
				scanlist = GetScanList(pairingheap_remove_first(so->listQueue));

				/* Reuse */
				scanlist->startPage = list->startPage;
				scanlist->distance = distance;
				pairingheap_add(so->listQueue, &scanlist->ph_node);

				/* Update max distance */
				maxDistance = GetScanList(pairingheap_first(so->listQueue))->distance;
			}
		}

		nextblkno = IvfflatPageGetOpaque(cpage)->nextblkno;

		UnlockReleaseBuffer(cbuf);
	}

	for (int i = listCount - 1; i >= 0; i--)
		so->listPages[i] = GetScanList(pairingheap_remove_first(so->listQueue))->startPage;

	Assert(pairingheap_is_empty(so->listQueue));
}
```

## 동작 흐름

```text
 GetScanLists(scan, value)                           L47
   L51   nextblkno = 블록 1 (IVFFLAT_HEAD_BLKNO)
   L56   리스트 페이지마다 (SHARE 잠금)
           L68  리스트 튜플마다
                  distance = distfunc(FUNCTION 1, center, value)
                  L76  힙이 덜 찼으면 넣는다. 다 차는 순간 maxDistance = 맨 위
                  L92  찼고 distance < maxDistance 면
                         맨 위를 빼서 그 자리를 재사용해 넣고, maxDistance 갱신
           L109 nextblkno
   L114  i = listCount-1 .. 0
           listPages[i] = 힙에서 뺀 것의 startPage     먼 것부터 빼므로 [0] 이 가장 가깝다
```

```text
 lists = 5, maxProbes = 2

 list   dist   heap after         maxDistance   note
 c0     7      [c0 7]             -
 c1     2      [c0 7, c1 2]       7             힙이 찼다
 c2     9      [c0 7, c1 2]       7             9 < 7 아님
 c3     1      [c1 2, c3 1]       2             맨 위 c0 를 빼고 c3
 c4     5      [c1 2, c3 1]       2             5 < 2 아님

 L114  listPages[1] = c1 (2),  listPages[0] = c3 (1)
 [09] 는 listPages[0] 부터 훑는다
```

리스트 페이지를 모두 읽는 일은 `probes` 와 상관없다. `probes = 1` 이어도 중심점 거리는 `lists` 번 계산한다.

## 결과가 쓰이는 곳

```text
 so->listPages[0 .. maxProbes-1] (가까운 순의 startPage)
      --> [09] GetScanItems 가 listIndex 로 차례로 읽는다
```

## 다루지 않는 것

리스트 힙의 비교 함수 `CompareLists`(L32)는 거리가 큰 쪽을 앞에 둔다. `pairingheap` 자체는 PostgreSQL 쪽이다.
