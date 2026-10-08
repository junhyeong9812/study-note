# RelationPutHeapTuple

상위: [행 쓰기와 WAL 기록](../README.md)

**잠긴 페이지에 튜플 바이트를 붙이고, 그 위치를 튜플에 적는다.** 실제 배치는 `PageAddItem` 이 한다. 줄 포인터 배열(pd_lower 쪽)은 앞에서 자라고 튜플 데이터(pd_upper 쪽)는 뒤에서 자라며, 둘 사이가 빈 공간이다. 이 함수는 크리티컬 섹션 안에서 불리므로 실패를 ERROR 가 아니라 PANIC 으로 낸다. 공간은 [04] 가 이미 확인했으니, 여기서 실패한다는 것은 무언가 깨졌다는 뜻이다.

## 위치

`access` / `heap` / `hio.c` L35-L82 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/hio.c#L35-L82))

## 실제 코드

`access` / `heap` / `hio.c` L27-L82 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/hio.c#L27-L82))

```c
// hio.c L27-L82
/*
 * RelationPutHeapTuple - place tuple at specified page
 *
 * !!! EREPORT(ERROR) IS DISALLOWED HERE !!!  Must PANIC on failure!!!
 *
 * Note - caller must hold BUFFER_LOCK_EXCLUSIVE on the buffer.
 */
void
RelationPutHeapTuple(Relation relation,
					 Buffer buffer,
					 HeapTuple tuple,
					 bool token)
{
	Page		pageHeader;
	OffsetNumber offnum;

	/*
	 * A tuple that's being inserted speculatively should already have its
	 * token set.
	 */
	Assert(!token || HeapTupleHeaderIsSpeculative(tuple->t_data));

	/*
	 * Do not allow tuples with invalid combinations of hint bits to be placed
	 * on a page.  This combination is detected as corruption by the
	 * contrib/amcheck logic, so if you disable this assertion, make
	 * corresponding changes there.
	 */
	Assert(!((tuple->t_data->t_infomask & HEAP_XMAX_COMMITTED) &&
			 (tuple->t_data->t_infomask & HEAP_XMAX_IS_MULTI)));

	/* Add the tuple to the page */
	pageHeader = BufferGetPage(buffer);

	offnum = PageAddItem(pageHeader, (Item) tuple->t_data,
						 tuple->t_len, InvalidOffsetNumber, false, true);

	if (offnum == InvalidOffsetNumber)
		elog(PANIC, "failed to add tuple to page");

	/* Update tuple->t_self to the actual position where it was stored */
	ItemPointerSet(&(tuple->t_self), BufferGetBlockNumber(buffer), offnum);

	/*
	 * Insert the correct position into CTID of the stored tuple, too (unless
	 * this is a speculative insertion, in which case the token is held in
	 * CTID field instead)
	 */
	if (!token)
	{
		ItemId		itemId = PageGetItemId(pageHeader, offnum);
		HeapTupleHeader item = (HeapTupleHeader) PageGetItem(pageHeader, itemId);

		item->t_ctid = tuple->t_self;
	}
}
```

`PageAddItem` 은 플래그를 붙여 `PageAddItemExtended` 를 부르는 매크로다.

`src` / `include` / `storage` / `bufpage.h` L473-L476 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/bufpage.h#L473-L476))

```c
// bufpage.h L473-L476
#define PageAddItem(page, item, size, offsetNumber, overwrite, is_heap) \
	PageAddItemExtended(page, item, size, offsetNumber, \
						((overwrite) ? PAI_OVERWRITE : 0) | \
						((is_heap) ? PAI_IS_HEAP : 0))
```

줄 번호를 고르고, 새 `pd_lower` 와 `pd_upper` 를 계산해 복사한다. 손상 검사와 덮어쓰기 갈래는 줄였다.

`storage` / `page` / `bufpage.c` L193-L355 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/page/bufpage.c#L193-L355))

```c
// bufpage.c L193-L355
PageAddItemExtended(Page page,
					Item item,
					Size size,
					OffsetNumber offsetNumber,
					int flags)
{
	PageHeader	phdr = (PageHeader) page;
	Size		alignedSize;
	int			lower;
	int			upper;
	ItemId		itemId;
	OffsetNumber limit;
	bool		needshuffle = false;

	// ... (L207-L217 생략: 페이지 포인터가 깨졌으면 PANIC)

	/*
	 * Select offsetNumber to place the new item at
	 */
	limit = OffsetNumberNext(PageGetMaxOffsetNumber(page));

	// ... (L224-L245 생략: 호출자가 줄 번호를 지정한 경우 (힙 삽입은 InvalidOffsetNumber 를 넘긴다))
	else
	{
		/* offsetNumber was not passed in, so find a free slot */
		/* if no free slot, we'll put it at limit (1st open slot) */
		if (PageHasFreeLinePointers(page))
		{
			/*
			 * Scan line pointer array to locate a "recyclable" (unused)
			 * ItemId.
			 *
			 * Always use earlier items first.  PageTruncateLinePointerArray
			 * can only truncate unused items when they appear as a contiguous
			 * group at the end of the line pointer array.
			 */
			for (offsetNumber = FirstOffsetNumber;
				 offsetNumber < limit;	/* limit is maxoff+1 */
				 offsetNumber++)
			{
				itemId = PageGetItemId(page, offsetNumber);

				/*
				 * We check for no storage as well, just to be paranoid;
				 * unused items should never have storage.  Assert() that the
				 * invariant is respected too.
				 */
				Assert(ItemIdIsUsed(itemId) || !ItemIdHasStorage(itemId));

				if (!ItemIdIsUsed(itemId) && !ItemIdHasStorage(itemId))
					break;
			}
			if (offsetNumber >= limit)
			{
				/* the hint is wrong, so reset it */
				PageClearHasFreeLinePointers(page);
			}
		}
		else
		{
			/* don't bother searching if hint says there's no free slot */
			offsetNumber = limit;
		}
	}

	/* Reject placing items beyond the first unused line pointer */
	if (offsetNumber > limit)
	{
		elog(WARNING, "specified item offset is too large");
		return InvalidOffsetNumber;
	}

	/* Reject placing items beyond heap boundary, if heap */
	if ((flags & PAI_IS_HEAP) != 0 && offsetNumber > MaxHeapTuplesPerPage)
	{
		elog(WARNING, "can't put more than MaxHeapTuplesPerPage items in a heap page");
		return InvalidOffsetNumber;
	}

	/*
	 * Compute new lower and upper pointers for page, see if it'll fit.
	 *
	 * Note: do arithmetic as signed ints, to avoid mistakes if, say,
	 * alignedSize > pd_upper.
	 */
	if (offsetNumber == limit || needshuffle)
		lower = phdr->pd_lower + sizeof(ItemIdData);
	else
		lower = phdr->pd_lower;

	alignedSize = MAXALIGN(size);

	upper = (int) phdr->pd_upper - (int) alignedSize;

	if (lower > upper)
		return InvalidOffsetNumber;

	/*
	 * OK to insert the item.  First, shuffle the existing pointers if needed.
	 */
	itemId = PageGetItemId(page, offsetNumber);

	if (needshuffle)
		memmove(itemId + 1, itemId,
				(limit - offsetNumber) * sizeof(ItemIdData));

	/* set the line pointer */
	ItemIdSetNormal(itemId, upper, size);

	// ... (L333-L344 생략: 초기화 안 된 바이트 검사에 관한 주석)
	VALGRIND_CHECK_MEM_IS_DEFINED(item, size);

	/* copy the item's data onto the page */
	memcpy((char *) page + upper, item, size);

	/* adjust page header */
	phdr->pd_lower = (LocationIndex) lower;
	phdr->pd_upper = (LocationIndex) upper;

	return offsetNumber;
}
```

## 동작 흐름

```text
 RelationPutHeapTuple
 L47   추측 삽입이면 헤더에 토큰이 있어야 한다
 L55   XMAX_COMMITTED 와 XMAX_IS_MULTI 가 같이 켜진 튜플은 넣지 않는다 (amcheck 가 손상으로 본다)
 L61   offnum = PageAddItem(page, t_data, t_len, InvalidOffsetNumber, false, true)
         PageAddItemExtended (bufpage.c L193)
         L222  limit = 마지막 줄 번호 + 1
         L250  비어 있는 줄 포인터가 있다는 힌트가 있으면 앞에서부터 찾는다
         L285  없으면 offsetNumber = limit                     맨 뒤에 하나 추가
         L297  힙인데 MaxHeapTuplesPerPage 를 넘으면 실패
         L309  새 줄 포인터를 쓰면 lower = pd_lower + 4          재사용이면 그대로
         L314  alignedSize = MAXALIGN(size)
         L316  upper = pd_upper - alignedSize
         L318  lower > upper 면 실패
         L331  ItemIdSetNormal(itemId, upper, size)             줄 포인터 = (위치, 길이)
         L348  memcpy(page + upper, item, size)
         L351  pd_lower, pd_upper 갱신
 L64   실패면 PANIC "failed to add tuple to page"
 L68   tuple->t_self = (이 버퍼의 블록 번호, offnum)
 L75   추측 삽입이 아니면
 L80     페이지 위 튜플의 t_ctid = t_self                    새 행은 자기 자신을 가리킨다
```

[04] 의 예에서 이어 가면, 32바이트 행이 94개 있는 블록 3 에 95번째 행이 들어간다.

```text
 블록 3 (BLCKSZ 8192), 넣기 전과 후

 0        24                    400 404                  5152 5184                     8192
 +--------+---------------------+---+----------------------+----+--------------------------+
 | header | lp[1] ... lp[94]    |lp | 빈 공간               |new | 행 94개 (32바이트씩)       |
 |  24B   | 94 * 4 = 376B       |95 |                       |32B |  94 * 32 = 3008B          |
 +--------+---------------------+---+----------------------+----+--------------------------+
                         pd_lower 400 -> 404       pd_upper 5184 -> 5152

 lp[95] = (lp_off 5152, lp_flags NORMAL, lp_len 32)
 t_self = t_ctid = (3, 95)
 빈 공간 = 5152 - 404 = 4748
```

`t_ctid` 가 자기 자신을 가리키는 것은 "이 행이 최신판"이라는 표시다. 나중에 UPDATE 가 새 판을 만들면 옛 행의 `t_ctid` 가 새 판의 위치로 바뀐다. 추측 삽입일 때는 이 자리에 토큰이 들어 있어 덮어쓰지 않는다(L70-L74 주석).

## 결과가 쓰이는 곳

```text
 tuple->t_self
      --> [02] 의 xlrec.offnum = ItemPointerGetOffsetNumber(&heaptup->t_self)  heapam.c L2198
      --> [02] 의 INIT_PAGE 판정 (offnum == 1 이고 MaxOffset == 1)
      --> [01] 이 slot->tts_tid 로 복사한다
 바뀐 페이지 (pd_lower, pd_upper, lp, 튜플 바이트)
      --> [02] 가 MarkBufferDirty 하고, [07] 이 FPI 를 찍으면 이 상태가 통째로 WAL 에 들어간다
```

## 다루지 않는 것

줄 포인터의 상태(`LP_UNUSED`, `LP_NORMAL`, `LP_REDIRECT`, `LP_DEAD`)와 HOT 체인, 페이지 정리로 빈 줄 포인터가 생기는 과정(`heap_page_prune`), 페이지 헤더 필드 전체(`PageHeaderData`)는 다른 곳의 주제라 요약만 했다.
