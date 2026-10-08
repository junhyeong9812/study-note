# HnswEntryCandidate

상위: [HNSW 검색](../README.md)

**진입점 원소를 탐색 후보 하나로 만드는 함수이고, 그 아래의 `HnswLoadElementImpl` 은 원소 튜플 하나를 읽어 거리를 재는 이 흐름의 기본 동작이다.** 디스크 모드에서는 원소의 블록을 공유 잠금으로 읽어, 페이지 위의 벡터와 검색 벡터의 거리를 바로 계산한다. 거리가 기준보다 멀면 원소를 메모리로 옮기지도 않고 버퍼를 놓는다.

## 위치

`src` / `hnswutils.c` L614-L626 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L614-L626))

## 실제 코드

```c
// hnswutils.c L598-L626
/*
 * Allocate a search candidate
 */
static HnswSearchCandidate *
HnswInitSearchCandidate(char *base, HnswElement element, double distance)
{
	HnswSearchCandidate *sc = palloc_object(HnswSearchCandidate);

	HnswPtrStore(base, sc->element, element);
	sc->distance = distance;
	return sc;
}

/*
 * Create a candidate for the entry point
 */
HnswSearchCandidate *
HnswEntryCandidate(char *base, HnswElement entryPoint, HnswQuery * q, Relation index, HnswSupport * support, bool loadVec)
{
	bool		inMemory = index == NULL;
	double		distance;

	if (inMemory)
		distance = GetElementDistance(base, entryPoint, q, support);
	else
		HnswLoadElement(entryPoint, &distance, q, index, support, loadVec, NULL);

	return HnswInitSearchCandidate(base, entryPoint, distance);
}
```

원소 튜플을 읽고 거리를 재는 함수다.

`src` / `hnswutils.c` L538-L585 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L538-L585))

```c
// hnswutils.c L526-L585
/*
 * Calculate the distance between values
 */
static inline double
HnswGetDistance(Datum a, Datum b, HnswSupport * support)
{
	return DatumGetFloat8(FunctionCall2Coll(support->procinfo, support->collation, a, b));
}

/*
 * Load an element and optionally get its distance from q
 */
static void
HnswLoadElementImpl(BlockNumber blkno, OffsetNumber offno, double *distance, HnswQuery * q, Relation index, HnswSupport * support, bool loadVec, double *maxDistance, HnswElement * element)
{
	Buffer		buf;
	Page		page;
	HnswElementTuple etup;

	/* Read vector */
	buf = ReadBuffer(index, blkno);
	LockBuffer(buf, BUFFER_LOCK_SHARE);
	page = BufferGetPage(buf);

	etup = (HnswElementTuple) PageGetItem(page, PageGetItemId(page, offno));

	Assert(HnswIsElementTuple(etup));

	if (unlikely(etup->deleted))
		elog(ERROR, "cannot load deleted element");

	/* Calculate distance */
	if (distance != NULL)
	{
		if (DatumGetPointer(q->value) == NULL)
			*distance = 0;
		else
			*distance = HnswGetDistance(q->value, PointerGetDatum(&etup->data), support);
	}

	/* Load element */
	if (distance == NULL || maxDistance == NULL || *distance < *maxDistance)
	{
		if (*element == NULL)
			*element = HnswInitElementFromBlock(blkno, offno);

		HnswLoadElementFromTuple(*element, etup, true, loadVec);
	}

	UnlockReleaseBuffer(buf);
}

/*
 * Load an element and optionally get its distance from q
 */
void
HnswLoadElement(HnswElement element, double *distance, HnswQuery * q, Relation index, HnswSupport * support, bool loadVec, double *maxDistance)
{
	HnswLoadElementImpl(element->blkno, element->offno, distance, q, index, support, loadVec, maxDistance, &element);
}
```

튜플의 칸을 메모리 원소로 옮긴다.

`src` / `hnswutils.c` L495-L524 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L495-L524))

```c
// hnswutils.c L492-L524
/*
 * Load an element from a tuple
 */
void
HnswLoadElementFromTuple(HnswElement element, HnswElementTuple etup, bool loadHeaptids, bool loadVec)
{
	element->level = etup->level;
	element->deleted = etup->deleted;
	element->version = etup->version;
	element->neighborPage = ItemPointerGetBlockNumber(&etup->neighbortid);
	element->neighborOffno = ItemPointerGetOffsetNumber(&etup->neighbortid);
	element->heaptidsLength = 0;

	if (loadHeaptids)
	{
		for (int i = 0; i < HNSW_HEAPTIDS; i++)
		{
			/* Can stop at first invalid */
			if (!ItemPointerIsValid(&etup->heaptids[i]))
				break;

			HnswAddHeapTid(element, &etup->heaptids[i]);
		}
	}

	if (loadVec)
	{
		char	   *base = NULL;
		Datum		value = datumCopy(PointerGetDatum(&etup->data), false, -1);

		HnswPtrStore(base, element->value, (char *) DatumGetPointer(value));
	}
}
```

## 동작 흐름

```text
 HnswEntryCandidate(base, entryPoint, q, index, support, loadVec)   L614
   L617  inMemory = index == NULL
   L620  메모리면 GetElementDistance     값 포인터로 바로 거리
   L623  디스크면 HnswLoadElement(entryPoint, &distance, q, ..., maxDistance = NULL)
   L625  HnswInitSearchCandidate(entryPoint, distance)

 HnswLoadElementImpl(blkno, offno, &distance, q, index, support, loadVec, maxDistance, &element)   L538
   L546  ReadBuffer(index, blkno), LockBuffer SHARE
   L550  etup = PageGetItem(offno)
   L554  etup->deleted 면 "cannot load deleted element"
   L558  distance 를 원하면
           q->value == NULL -> 0
           아니면 HnswGetDistance(q->value, &etup->data)   페이지 위의 벡터와 바로 비교
   L567  maxDistance 가 없거나 distance < *maxDistance 일 때만
           element 가 없으면 HnswInitElementFromBlock
           HnswLoadElementFromTuple(element, etup, loadHeaptids = true, loadVec)
             level, deleted, version, neighborPage/Offno, heaptids
             loadVec 이면 값을 datumCopy
   L575  UnlockReleaseBuffer
```

```text
 원소 튜플에서 무엇을 가져오는가 (HnswElementTupleData, hnsw.h L373-L383)

 +------+-------+---------+---------+---------------+-------------+--------+----------+
 | type | level | deleted | version | heaptids[10]  | neighbortid | unused | data     |
 | 1    | 1     | 1       | 1       | 6 * 10 = 60   | 6           | 2      | Vector   |
 +------+-------+---------+---------+---------------+-------------+--------+----------+
   0      1       2         3         4               64            70       72

 거리 계산    data 를 페이지 위에서 바로 읽는다 (복사 없음)
 원소로 복사  level, deleted, version, neighbortid, 유효한 heaptids
 loadVec      검색은 false (값이 필요 없다), 삽입은 true (이웃 선택에 값이 필요)
```

스캔에서 `loadVec = false` 인 까닭은 코드에서 드러난다. 검색은 거리만 비교하므로 원소의 값을 메모리에 들고 있을 필요가 없다. 삽입 쪽의 `SelectNeighbors` 는 후보끼리의 거리(`CheckElementCloser`)를 재야 해서 값을 복사한다(`HnswSearchLayer` 가 `inserting` 을 `loadVec` 으로 넘긴다, L933).

## 결과가 쓰이는 곳

```text
 HnswSearchCandidate { element, distance }
      --> [07] HnswSearchLayer 의 첫 ep 목록
 HnswLoadElementImpl
      --> [07] 에서 이웃 원소마다 같은 함수로 거리를 재고, 멀면 원소를 만들지 않는다
 element->heaptids
      --> [03] hnswgettuple 이 여기서 힙 TID 를 꺼낸다
```

## 다루지 않는 것

메모리 모드의 `GetElementDistance`(L590)는 빌드 쪽이라 요약만 했다. 지워지는 중인 원소(`heaptidsLength == 0`)를 탐색에서 어떻게 다루는지는 VACUUM 과 얽혀 있어 다루지 않았다.
