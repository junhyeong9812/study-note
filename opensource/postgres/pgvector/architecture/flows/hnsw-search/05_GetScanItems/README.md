# GetScanItems

상위: [HNSW 검색](../README.md)

**검색 벡터 하나로 그래프를 위에서 아래까지 탐색해 0층의 가까운 후보 목록을 돌려주는 함수, 논문의 Algorithm 5 다.** 메타 페이지에서 `m`, 차원, 진입점을 읽고, 진입점의 층에서 1층까지는 폭 1 로 가장 가까운 원소 하나만 들고 내려온다. 0층에서는 폭 `hnsw.ef_search` 로 탐색하고, 반복 스캔이 켜져 있으면 버린 후보를 모아 둘 힙을 넘긴다.

## 위치

`src` / `hnswscan.c` L25-L61 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswscan.c#L25-L61))

## 실제 코드

```c
// hnswscan.c L22-L61
/*
 * Algorithm 5 from paper
 */
static List *
GetScanItems(IndexScanDesc scan, Datum value)
{
	HnswScanOpaque so = (HnswScanOpaque) scan->opaque;
	Relation	index = scan->indexRelation;
	HnswSupport *support = &so->support;
	List	   *ep;
	List	   *w;
	int			m;
	int			dimensions;
	HnswElement entryPoint;
	char	   *base = NULL;
	HnswQuery  *q = &so->q;

	/* Get m, dimensions, and entry point */
	HnswGetMetaPageInfo(index, &m, &dimensions, &entryPoint);

	/* Check dimensions match index */
	if (DatumGetPointer(value) != NULL)
		HnswCheckDim(dimensions, so->typeInfo, support->collation, value);

	q->value = value;
	so->m = m;

	if (entryPoint == NULL)
		return NIL;

	ep = list_make1(HnswEntryCandidate(base, entryPoint, q, index, support, false));

	for (int lc = entryPoint->level; lc >= 1; lc--)
	{
		w = HnswSearchLayer(base, q, ep, 1, lc, index, support, m, false, NULL, NULL, NULL, true, NULL);
		ep = w;
	}

	return HnswSearchLayer(base, q, ep, hnsw_ef_search, 0, index, support, m, false, NULL, &so->v, hnsw_iterative_scan != HNSW_ITERATIVE_SCAN_OFF ? &so->discarded : NULL, true, &so->tuples);
}
```

메타 페이지에서 세 값을 읽는 함수다.

`src` / `hnswutils.c` L300-L333 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L300-L333))

```c
// hnswutils.c L297-L333
/*
 * Get the metapage info
 */
void
HnswGetMetaPageInfo(Relation index, int *m, int *dimensions, HnswElement * entryPoint)
{
	Buffer		buf;
	Page		page;
	HnswMetaPage metap;

	buf = ReadBuffer(index, HNSW_METAPAGE_BLKNO);
	LockBuffer(buf, BUFFER_LOCK_SHARE);
	page = BufferGetPage(buf);
	metap = HnswPageGetMeta(page);

	if (unlikely(metap->magicNumber != HNSW_MAGIC_NUMBER))
		elog(ERROR, "hnsw index is not valid");

	if (m != NULL)
		*m = metap->m;

	if (dimensions != NULL)
		*dimensions = metap->dimensions;

	if (entryPoint != NULL)
	{
		if (BlockNumberIsValid(metap->entryBlkno))
		{
			*entryPoint = HnswInitElementFromBlock(metap->entryBlkno, metap->entryOffno);
			(*entryPoint)->level = metap->entryLevel;
		}
		else
			*entryPoint = NULL;
	}

	UnlockReleaseBuffer(buf);
}
```

## 동작 흐름

```text
 GetScanItems(scan, value)                           L25
   L40   HnswGetMetaPageInfo(index, &m, &dimensions, &entryPoint)
           블록 0 을 SHARE 로 읽어
           magic 이 다르면 "hnsw index is not valid"
           entryBlkno 가 유효하면 HnswInitElementFromBlock(entryBlkno, entryOffno), level = entryLevel
   L43   value 가 있으면 HnswCheckDim(dimensions, ...)   다르면 오류
   L46   q->value = value,  so->m = m
   L49   진입점이 없으면 (빈 인덱스) NIL
   L52   ep = [ [06] HnswEntryCandidate(진입점, loadVec = false) ]
   L54   lc = entryPoint->level .. 1
           w  = [07] HnswSearchLayer(ep, ef = 1, lc, v = NULL)    층마다 새 방문 집합
           ep = w
   L60   return [07] HnswSearchLayer(ep, ef = hnsw_ef_search, lc = 0,
                    v = &so->v, discarded = 반복 스캔이면 &so->discarded,
                    initVisited = true, tuples = &so->tuples)
```

```text
 진입점 level 3, ef_search 40 일 때 읽는 양 (m = 16)

 층 3   ef 1   확장할 때마다 이웃 튜플 1 + 안 본 이웃 원소 최대 16
 층 2   ef 1   같은 방식
 층 1   ef 1   같은 방식
 층 0   ef 40  확장할 때마다 이웃 튜플 1 + 안 본 이웃 원소 최대 32
               결과 W 는 최대 40 개
 위층은 층마다 방문 집합을 새로 만들고 (v = NULL), 0층만 so->v 에 남긴다
 so->v 는 반복 스캔에서 이미 본 원소를 다시 보지 않게 한다
```

`m` 은 인덱스 옵션이 아니라 메타 페이지에서 읽는다. 이웃 튜플의 칸 배치는 빌드 때의 `m` 으로 정해졌고(`HnswSetNeighborTuple`), 이웃 튜플을 읽는 `HnswLoadNeighborTids` 는 칸 수가 `(level + 2) * m` 인지 이 `m` 으로 확인한다(hnswutils.c L782).

## 결과가 쓰이는 곳

```text
 List of HnswSearchCandidate (먼 것부터, 끝이 가장 가깝다)
      --> [03] hnswgettuple 의 so->w
 so->v (방문 TID 해시), so->discarded (버린 후보 힙), so->tuples (본 원소 수)
      --> [09] ResumeScanItems 와 hnswgettuple 의 중단 조건
```

## 다루지 않는 것

`HnswInitElementFromBlock`(L284)이 만드는 원소는 블록과 오프셋만 가진 껍데기이고, 나머지는 [06] 에서 원소 튜플을 읽을 때 채워진다.
