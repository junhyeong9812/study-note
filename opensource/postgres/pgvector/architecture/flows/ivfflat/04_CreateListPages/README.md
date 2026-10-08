# CreateListPages

상위: [IVFFlat 빌드와 검색](../README.md)

**중심점마다 리스트 튜플 하나를 리스트 페이지에 차례로 적는 함수다.** 리스트 튜플은 중심점 벡터와 두 블록 번호(항목 체인의 첫 페이지 `startPage`, 새 항목을 넣을 페이지 `insertPage`)로 되어 있다. 이 시점에는 항목 페이지가 아직 없으므로 두 번호를 무효로 두고, 각 리스트 튜플이 놓인 (블록, 오프셋)을 `listInfo` 에 기억해 두었다가 [06] 에서 채운다.

## 위치

`src` / `ivfbuild.c` L517-L562 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L517-L562))

## 실제 코드

리스트 튜플과 페이지 꼬리(opaque)다.

`src` / `ivfflat.h` L252-L278 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfflat.h#L252-L278))

```c
// ivfflat.h L252-L278
typedef struct IvfflatMetaPageData
{
	uint32		magicNumber;
	uint32		version;
	uint16		dimensions;
	uint16		lists;
}			IvfflatMetaPageData;

typedef IvfflatMetaPageData * IvfflatMetaPage;

typedef struct IvfflatPageOpaqueData
{
	BlockNumber nextblkno;
	uint16		unused;
	uint16		page_id;		/* for identification of IVFFlat indexes */
}			IvfflatPageOpaqueData;

typedef IvfflatPageOpaqueData * IvfflatPageOpaque;

typedef struct IvfflatListData
{
	BlockNumber startPage;
	BlockNumber insertPage;
	Vector		center;
}			IvfflatListData;

typedef IvfflatListData * IvfflatList;
```

```c
// ivfbuild.c L514-L562
/*
 * Create list pages
 */
static void
CreateListPages(Relation index, VectorArray centers, int lists,
				ForkNumber forkNum, ListInfo * *listInfo)
{
	Buffer		buf;
	Page		page;
	GenericXLogState *state;
	Size		listSize;
	IvfflatList list;

	listSize = MAXALIGN(IVFFLAT_LIST_SIZE(centers->itemsize));
	list = palloc0(listSize);

	buf = IvfflatNewBuffer(index, forkNum);
	IvfflatInitRegisterPage(index, &buf, &page, &state);

	for (int i = 0; i < lists; i++)
	{
		OffsetNumber offno;

		/* Zero memory for each list */
		MemSet(list, 0, listSize);

		/* Load list */
		list->startPage = InvalidBlockNumber;
		list->insertPage = InvalidBlockNumber;
		memcpy(&list->center, VectorArrayGet(centers, i), VARSIZE_ANY(VectorArrayGet(centers, i)));

		/* Ensure free space */
		if (PageGetFreeSpace(page) < listSize)
			IvfflatAppendPage(index, &buf, &page, &state, forkNum);

		/* Add the item */
		offno = PageAddItem(page, (Item) list, listSize, InvalidOffsetNumber, false, false);
		if (offno == InvalidOffsetNumber)
			elog(ERROR, "failed to add index item to \"%s\"", RelationGetRelationName(index));

		/* Save location info */
		(*listInfo)[i].blkno = BufferGetBlockNumber(buf);
		(*listInfo)[i].offno = offno;
	}

	IvfflatCommitBuffer(buf, state);

	pfree(list);
}
```

페이지가 차면 다음 페이지를 붙인다. 순서가 중요하다고 주석이 강조한다.

`src` / `ivfutils.c` L185-L207 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfutils.c#L185-L207))

```c
// ivfutils.c L180-L207
/*
 * Add a new page
 *
 * The order is very important!!
 */
void
IvfflatAppendPage(Relation index, Buffer *buf, Page *page, GenericXLogState **state, ForkNumber forkNum)
{
	/* Get new buffer */
	Buffer		newbuf = IvfflatNewBuffer(index, forkNum);
	Page		newpage = GenericXLogRegisterBuffer(*state, newbuf, GENERIC_XLOG_FULL_IMAGE);

	/* Update the previous buffer */
	IvfflatPageGetOpaque(*page)->nextblkno = BufferGetBlockNumber(newbuf);

	/* Init new page */
	IvfflatInitPage(newbuf, newpage);

	/* Commit */
	GenericXLogFinish(*state);

	/* Unlock */
	UnlockReleaseBuffer(*buf);

	*state = GenericXLogStart(index);
	*page = GenericXLogRegisterBuffer(*state, newbuf, GENERIC_XLOG_FULL_IMAGE);
	*buf = newbuf;
}
```

## 동작 흐름

```text
 CreateListPages(index, centers, lists, forkNum, &listInfo)    L517
   L527  listSize = MAXALIGN(8 + 중심점 크기)       startPage 4 + insertPage 4 + Vector
   L530  새 버퍼 (블록 1) + GenericXLog 전체 이미지 등록
   L533  i = 0 .. lists-1
           startPage = insertPage = 무효
           center = centers[i] 복사
           L546  자리가 없으면 IvfflatAppendPage
                   새 버퍼를 같은 state 에 등록, 이전 페이지 nextblkno = 새 블록
                   GenericXLogFinish -> 이전 버퍼 해제 -> 새 state 로 새 페이지 등록
           L550  PageAddItem
           L555  listInfo[i] = (블록, 오프셋)
   L559  마지막 페이지 GenericXLogFinish
```

```text
 vector(768), lists = 100 일 때 리스트 페이지

 리스트 튜플 = MAXALIGN(8 + 8 + 4*768) = 3088 바이트
 페이지 자리 8192 - 헤더 24 - opaque 8 = 8160
   1 개째  3088 + 줄 포인터 4  -> 남은 5068
   2 개째  3088 + 4            -> 남은 1976, 다음 것은 PageGetFreeSpace 1972 < 3088
 페이지당 2 개 -> 블록 1 .. 50 이 리스트 페이지, 항목 페이지는 블록 51 부터

 블록 1  [L0 (1,1)] [L1 (1,2)]
 블록 2  [L2 (2,1)] [L3 (2,2)]
 ...
 블록 50 [L98] [L99]
```

`IvfflatAppendPage` 는 새 페이지를 이전 페이지와 같은 GenericXLog 상태에 등록하고(L190), 이전 페이지의 `nextblkno` 를 고치고(L193), 새 페이지를 초기화한 뒤 한 번의 `GenericXLogFinish` 로 둘을 함께 기록한다(L199). 그다음에야 이전 버퍼를 놓고 새 state 를 연다. 주석은 이유를 적지 않고 "The order is very important!!"(L183)라고만 한다.

## 결과가 쓰이는 곳

```text
 listInfo[i] (리스트 튜플의 위치)
      --> [06] InsertTuples 가 IvfflatUpdateList 로 startPage, insertPage 를 채운다
 리스트 페이지 체인 (블록 1 부터)
      --> 검색 [08] GetScanLists 와 INSERT 의 FindInsertPage 가 처음부터 끝까지 훑는다
```

## 다루지 않는 것

`halfvec` 과 `bit` 의 중심점 크기(`HalfvecItemSize`, `BitItemSize`, ivfutils.c L315-L325)에 따른 페이지당 리스트 수는 따로 계산하지 않았다.
