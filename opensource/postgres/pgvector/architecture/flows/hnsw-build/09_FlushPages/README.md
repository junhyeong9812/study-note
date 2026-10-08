# FlushPages

상위: [HNSW 빌드](../README.md)

**메모리 그래프를 인덱스 페이지로 옮겨 적는 함수다.** 세 번에 나눠 쓴다. 메타 페이지를 만들고, 원소 목록을 따라가며 원소 튜플과 빈 이웃 튜플을 나란히 놓아 모든 원소의 디스크 주소(블록, 오프셋)를 정하고, 그 주소가 다 정해진 뒤에 목록을 한 번 더 돌며 이웃 튜플을 실제 이웃 주소로 덮어쓴다. 다 쓰면 `flushed = true` 로 두고 그래프 메모리를 통째로 비운다.

## 위치

`src` / `hnswbuild.c` L303-L316 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L303-L316))

## 실제 코드

```c
// hnswbuild.c L300-L316
/*
 * Flush pages
 */
static void
FlushPages(HnswBuildState * buildstate)
{
#ifdef HNSW_MEMORY
	elog(INFO, "memory: %zu MB", buildstate->graph->memoryUsed / (1024 * 1024));
#endif

	CreateMetaPage(buildstate);
	CreateGraphPages(buildstate);
	WriteNeighborTuples(buildstate);

	buildstate->graph->flushed = true;
	MemoryContextReset(buildstate->graphCtx);
}
```

디스크 위의 세 가지 튜플 모양이다.

`src` / `hnsw.h` L349-L395 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.h#L349-L395))

```c
// hnsw.h L349-L395
typedef struct HnswMetaPageData
{
	uint32		magicNumber;
	uint32		version;
	uint32		dimensions;
	uint16		m;
	uint16		efConstruction;
	BlockNumber entryBlkno;
	OffsetNumber entryOffno;
	int16		entryLevel;
	BlockNumber insertPage;
}			HnswMetaPageData;

typedef HnswMetaPageData * HnswMetaPage;

typedef struct HnswPageOpaqueData
{
	BlockNumber nextblkno;
	uint16		unused;
	uint16		page_id;		/* for identification of HNSW indexes */
}			HnswPageOpaqueData;

typedef HnswPageOpaqueData * HnswPageOpaque;

typedef struct HnswElementTupleData
{
	uint8		type;
	uint8		level;
	uint8		deleted;
	uint8		version;
	ItemPointerData heaptids[HNSW_HEAPTIDS];
	ItemPointerData neighbortid;
	uint16		unused;
	Vector		data;
}			HnswElementTupleData;

typedef HnswElementTupleData * HnswElementTuple;

typedef struct HnswNeighborTupleData
{
	uint8		type;
	uint8		version;
	uint16		count;
	ItemPointerData indextids[FLEXIBLE_ARRAY_MEMBER];
}			HnswNeighborTupleData;

typedef HnswNeighborTupleData * HnswNeighborTuple;
```

메타 페이지를 만든다.

`src` / `hnswbuild.c` L88-L117 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L88-L117))

```c
// hnswbuild.c L85-L145
/*
 * Create the metapage
 */
static void
CreateMetaPage(HnswBuildState * buildstate)
{
	Relation	index = buildstate->index;
	ForkNumber	forkNum = buildstate->forkNum;
	Buffer		buf;
	Page		page;
	HnswMetaPage metap;

	buf = HnswNewBuffer(index, forkNum);
	page = BufferGetPage(buf);
	HnswInitPage(buf, page);

	/* Set metapage data */
	metap = HnswPageGetMeta(page);
	metap->magicNumber = HNSW_MAGIC_NUMBER;
	metap->version = HNSW_VERSION;
	metap->dimensions = buildstate->dimensions;
	metap->m = buildstate->m;
	metap->efConstruction = buildstate->efConstruction;
	metap->entryBlkno = InvalidBlockNumber;
	metap->entryOffno = InvalidOffsetNumber;
	metap->entryLevel = -1;
	metap->insertPage = InvalidBlockNumber;
	((PageHeader) page)->pd_lower =
		((char *) metap + sizeof(HnswMetaPageData)) - (char *) page;

	MarkBufferDirty(buf);
	UnlockReleaseBuffer(buf);
}

/*
 * Add a new page
 */
static void
HnswBuildAppendPage(Relation index, Buffer *buf, Page *page, ForkNumber forkNum)
{
	/* Add a new page */
	Buffer		newbuf = HnswNewBuffer(index, forkNum);

	/* Update previous page */
	HnswPageGetOpaque(*page)->nextblkno = BufferGetBlockNumber(newbuf);

	/* Commit */
	MarkBufferDirty(*buf);
	UnlockReleaseBuffer(*buf);

	/* Can take a while, so ensure we can interrupt */
	/* Needs to be called when no buffer locks are held */
	LockBuffer(newbuf, BUFFER_LOCK_UNLOCK);
	CHECK_FOR_INTERRUPTS();
	LockBuffer(newbuf, BUFFER_LOCK_EXCLUSIVE);

	/* Prepare new page */
	*buf = newbuf;
	*page = BufferGetPage(*buf);
	HnswInitPage(*buf, *page);
}
```

원소 튜플과 빈 이웃 튜플을 놓는다.

`src` / `hnswbuild.c` L150-L248 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L150-L248))

```c
// hnswbuild.c L147-L248
/*
 * Create graph pages
 */
static void
CreateGraphPages(HnswBuildState * buildstate)
{
	Relation	index = buildstate->index;
	ForkNumber	forkNum = buildstate->forkNum;
	Size		maxSize;
	HnswElementTuple etup;
	HnswNeighborTuple ntup;
	BlockNumber insertPage;
	HnswElement entryPoint;
	Buffer		buf;
	Page		page;
	HnswElementPtr iter = buildstate->graph->head;
	char	   *base = buildstate->hnswarea;

	/* Calculate sizes */
	maxSize = HNSW_MAX_SIZE;

	/* Allocate once */
	etup = palloc0(HNSW_TUPLE_ALLOC_SIZE);
	ntup = palloc0(HNSW_TUPLE_ALLOC_SIZE);

	/* Prepare first page */
	buf = HnswNewBuffer(index, forkNum);
	page = BufferGetPage(buf);
	HnswInitPage(buf, page);

	while (!HnswPtrIsNull(base, iter))
	{
		HnswElement element = HnswPtrAccess(base, iter);
		Size		etupSize;
		Size		ntupSize;
		Size		combinedSize;
		Pointer		valuePtr = HnswPtrAccess(base, element->value);

		/* Update iterator */
		iter = element->next;

		/* Zero memory for each element */
		MemSet(etup, 0, HNSW_TUPLE_ALLOC_SIZE);

		/* Calculate sizes */
		etupSize = HNSW_ELEMENT_TUPLE_SIZE(VARSIZE_ANY(valuePtr));
		ntupSize = HNSW_NEIGHBOR_TUPLE_SIZE(element->level, buildstate->m);
		combinedSize = etupSize + ntupSize + sizeof(ItemIdData);

		/* Initial size check */
		if (etupSize > HNSW_TUPLE_ALLOC_SIZE)
			ereport(ERROR,
					(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
					 errmsg("index tuple too large")));

		HnswSetElementTuple(base, etup, element);

		/* Keep element and neighbors on the same page if possible */
		if (PageGetFreeSpace(page) < etupSize || (combinedSize <= maxSize && PageGetFreeSpace(page) < combinedSize))
			HnswBuildAppendPage(index, &buf, &page, forkNum);

		/* Calculate offsets */
		element->blkno = BufferGetBlockNumber(buf);
		element->offno = OffsetNumberNext(PageGetMaxOffsetNumber(page));
		if (combinedSize <= maxSize)
		{
			element->neighborPage = element->blkno;
			element->neighborOffno = OffsetNumberNext(element->offno);
		}
		else
		{
			element->neighborPage = element->blkno + 1;
			element->neighborOffno = FirstOffsetNumber;
		}

		ItemPointerSet(&etup->neighbortid, element->neighborPage, element->neighborOffno);

		/* Add element */
		if (PageAddItem(page, (Item) etup, etupSize, InvalidOffsetNumber, false, false) != element->offno)
			elog(ERROR, "failed to add index item to \"%s\"", RelationGetRelationName(index));

		/* Add new page if needed */
		if (PageGetFreeSpace(page) < ntupSize)
			HnswBuildAppendPage(index, &buf, &page, forkNum);

		/* Add placeholder for neighbors */
		if (PageAddItem(page, (Item) ntup, ntupSize, InvalidOffsetNumber, false, false) != element->neighborOffno)
			elog(ERROR, "failed to add index item to \"%s\"", RelationGetRelationName(index));
	}

	insertPage = BufferGetBlockNumber(buf);

	/* Commit */
	MarkBufferDirty(buf);
	UnlockReleaseBuffer(buf);

	entryPoint = HnswPtrAccess(base, buildstate->graph->entryPoint);
	HnswUpdateMetaPage(index, HNSW_UPDATE_ENTRY_ALWAYS, entryPoint, insertPage, forkNum, true);

	pfree(etup);
	pfree(ntup);
}
```

이웃 튜플을 채운다.

`src` / `hnswbuild.c` L253-L298 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L253-L298))

```c
// hnswbuild.c L250-L298
/*
 * Write neighbor tuples
 */
static void
WriteNeighborTuples(HnswBuildState * buildstate)
{
	Relation	index = buildstate->index;
	ForkNumber	forkNum = buildstate->forkNum;
	int			m = buildstate->m;
	HnswElementPtr iter = buildstate->graph->head;
	char	   *base = buildstate->hnswarea;
	HnswNeighborTuple ntup;

	/* Allocate once */
	ntup = palloc0(HNSW_TUPLE_ALLOC_SIZE);

	while (!HnswPtrIsNull(base, iter))
	{
		HnswElement element = HnswPtrAccess(base, iter);
		Buffer		buf;
		Page		page;
		Size		ntupSize = HNSW_NEIGHBOR_TUPLE_SIZE(element->level, m);

		/* Update iterator */
		iter = element->next;

		/* Zero memory for each element */
		MemSet(ntup, 0, HNSW_TUPLE_ALLOC_SIZE);

		/* Can take a while, so ensure we can interrupt */
		/* Needs to be called when no buffer locks are held */
		CHECK_FOR_INTERRUPTS();

		buf = ReadBufferExtended(index, forkNum, element->neighborPage, RBM_NORMAL, NULL);
		LockBuffer(buf, BUFFER_LOCK_EXCLUSIVE);
		page = BufferGetPage(buf);

		HnswSetNeighborTuple(base, ntup, element, m);

		if (!PageIndexTupleOverwrite(page, element->neighborOffno, (Item) ntup, ntupSize))
			elog(ERROR, "failed to add index item to \"%s\"", RelationGetRelationName(index));

		/* Commit */
		MarkBufferDirty(buf);
		UnlockReleaseBuffer(buf);
	}

	pfree(ntup);
}
```

메모리 원소를 튜플로 바꾸는 두 함수다.

`src` / `hnswutils.c` L438-L490 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L438-L490))

```c
// hnswutils.c L435-L490
/*
 * Set element tuple, except for neighbor info
 */
void
HnswSetElementTuple(char *base, HnswElementTuple etup, HnswElement element)
{
	Pointer		valuePtr = HnswPtrAccess(base, element->value);

	etup->type = HNSW_ELEMENT_TUPLE_TYPE;
	etup->level = element->level;
	etup->deleted = 0;
	etup->version = element->version;
	for (int i = 0; i < HNSW_HEAPTIDS; i++)
	{
		if (i < element->heaptidsLength)
			etup->heaptids[i] = element->heaptids[i];
		else
			ItemPointerSetInvalid(&etup->heaptids[i]);
	}
	memcpy(&etup->data, valuePtr, VARSIZE_ANY(valuePtr));
}

/*
 * Set neighbor tuple
 */
void
HnswSetNeighborTuple(char *base, HnswNeighborTuple ntup, HnswElement e, int m)
{
	int			idx = 0;

	ntup->type = HNSW_NEIGHBOR_TUPLE_TYPE;

	for (int lc = e->level; lc >= 0; lc--)
	{
		HnswNeighborArray *neighbors = HnswGetNeighbors(base, e, lc);
		int			lm = HnswGetLayerM(m, lc);

		for (int i = 0; i < lm; i++)
		{
			ItemPointer indextid = &ntup->indextids[idx++];

			if (i < neighbors->length)
			{
				HnswCandidate *hc = &neighbors->items[i];
				HnswElement hce = HnswPtrAccess(base, hc->element);

				ItemPointerSet(indextid, hce->blkno, hce->offno);
			}
			else
				ItemPointerSetInvalid(indextid);
		}
	}

	ntup->count = idx;
	ntup->version = e->version;
}
```

## 동작 흐름

```text
 FlushPages(buildstate)                              L303
   L310  CreateMetaPage          블록 0
           magic 0xA953A953, version 1, dimensions, m, efConstruction
           entry = 없음 (entryLevel -1), insertPage = 없음
           MarkBufferDirty 만 (WAL 없음)
   L311  CreateGraphPages        블록 1 부터
           graph->head 부터 next 를 따라
             etupSize = MAXALIGN(72 + 값 크기)
             ntupSize = MAXALIGN(4 + 6 * (level + 2) * m)
             둘이 한 페이지(HNSW_MAX_SIZE 8156)에 들어가면 같은 페이지에 붙여 놓는다
               들어갈 자리가 없으면 HnswBuildAppendPage (nextblkno 로 연결)
             element->blkno, offno, neighborPage, neighborOffno 확정
             원소 튜플 PageAddItem, 0 으로 채운 이웃 튜플 PageAddItem (자리만)
           insertPage = 마지막 블록
           HnswUpdateMetaPage(ALWAYS, entryPoint, insertPage, building = true)
   L312  WriteNeighborTuples
           다시 head 부터
             HnswSetNeighborTuple -> 이웃마다 (blkno, offno) 를 indextids 에
             PageIndexTupleOverwrite(neighborOffno)    같은 크기로 덮어쓴다
   L314  graph->flushed = true
   L315  MemoryContextReset(graphCtx)    원소와 이웃 배열이 모두 사라진다
```

`vector(768)`, `m = 16` 에서 원소 셋이 놓이는 모습을 계산하면 다음과 같다. 원소 튜플은 MAXALIGN(72 + 8 + 4*768) = 3152 바이트, 이웃 튜플은 level 0 이면 MAXALIGN(4 + 6*32) = 200, level 1 이면 MAXALIGN(4 + 6*48) = 296 바이트다.

```text
 graph->head 순서: E1 (level 0), E2 (level 1), E3 (level 0)

 블록 0  메타 페이지
         m 16, ef_construction 64, dimensions 768
         entryBlkno 1, entryOffno 3, entryLevel 1      (E2 가 진입점)
         insertPage 2

 블록 1  남은 자리 8156 (= 8192 - 헤더 24 - opaque 8 - 줄 포인터 4)
   off 1  E1 원소 튜플  3152    neighbortid -> (1, 2)
   off 2  E1 이웃 튜플   200    0층 32칸
   off 3  E2 원소 튜플  3152    neighbortid -> (1, 4)
   off 4  E2 이웃 튜플   296    1층 16칸 + 0층 32칸
   남은 자리 1340 < 3152          -> E3 은 다음 페이지
   nextblkno = 2

 블록 2
   off 1  E3 원소 튜플  3152    neighbortid -> (2, 2)
   off 2  E3 이웃 튜플   200
   nextblkno = 없음
```

```text
 이웃 튜플의 칸 배치 (E2, level 1, m = 16)

 indextids [ 0 .. 15 ]  [ 16 .. 47 ]
             1층 16칸     0층 32칸           count = (1 + 2) * 16 = 48
 위층부터 적는다 (HnswSetNeighborTuple 의 lc = level .. 0, L467)
 이웃이 lm 보다 적으면 남은 칸은 무효 TID
 lc 층의 시작 칸 = (level - lc) * m        (검색의 HnswLoadNeighborTids L789)
```

원소 튜플과 이웃 튜플을 합쳐 한 페이지를 넘으면(큰 차원) 이웃 튜플은 다음 블록 첫 칸으로 간다(L218-L219). 예를 들어 `vector(2000)` 은 원소 튜플만 MAXALIGN(72 + 8 + 8000) = 8080 바이트라 합이 8156 을 넘는다.

이웃 튜플을 두 번에 나눠 쓰는 것은 코드 구조에서 드러난다. 이웃의 주소 `hce->blkno`, `hce->offno`(L481)는 `CreateGraphPages` 가 그 이웃 원소를 놓을 때 정해지므로, 모든 원소를 놓은 뒤에야 이웃 튜플을 채울 수 있다.

## 결과가 쓰이는 곳

```text
 메타 페이지
      --> [HNSW 검색] HnswGetMetaPageInfo 가 m, dimensions, 진입점을 읽는다
      --> INSERT 의 GetInsertPage 가 insertPage 를 읽는다
 원소 튜플 (type 1) / 이웃 튜플 (type 2)
      --> 검색의 HnswLoadElementImpl, HnswLoadNeighborTids
 flushed = true
      --> 이후 행은 [04] InsertTuple 에서 디스크 단계로 간다
```

## 다루지 않는 것

`version` 칸(지워진 원소 자리를 재사용할 때 이웃 튜플과 원소 튜플이 같은 세대인지 확인하는 값, 검색의 L782)과 `deleted` 칸의 VACUUM 쪽 사용, `HnswBuildAppendPage` 가 버퍼 잠금을 잠깐 풀고 `CHECK_FOR_INTERRUPTS` 를 하는 이유(주석 L135-L136)는 요약만 했다.
