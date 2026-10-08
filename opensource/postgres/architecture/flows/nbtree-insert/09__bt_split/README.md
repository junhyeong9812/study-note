# _bt_split

상위: [nbtree 삽입과 분할](../README.md)

**꽉 찬 페이지 하나를 왼쪽과 오른쪽 둘로 나누고, 새 튜플을 알맞은 쪽에 함께 넣는다.** 왼쪽은 원래 블록 번호를 그대로 쓰고(임시 페이지에 만들어 덮어쓴다), 오른쪽은 새 블록이다. 왼쪽에는 새 high key 와 `INCOMPLETE_SPLIT` 표시가 붙는다. 부모에 오른쪽 페이지의 downlink 가 들어가기 전까지 오른쪽 페이지는 왼쪽의 right link 로만 닿을 수 있고, 이 표시가 그 상태를 기록한다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L1467-L2080 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1467-L2080))

## 실제 코드

분할 지점을 고르고([10]), 왼쪽이 될 임시 페이지를 만든다. 원래 페이지는 크리티컬 섹션 전까지 건드리지 않는다.

`access` / `nbtree` / `nbtinsert.c` L1511-L1561 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1511-L1561))

```c
// nbtinsert.c L1511-L1561
	origpage = BufferGetPage(buf);
	oopaque = BTPageGetOpaque(origpage);
	isleaf = P_ISLEAF(oopaque);
	isrightmost = P_RIGHTMOST(oopaque);
	maxoff = PageGetMaxOffsetNumber(origpage);
	origpagenumber = BufferGetBlockNumber(buf);

	// ... (L1518-L1541 생략: 주석: 분할 지점은 lastleft 와 firstright 사이)
	firstrightoff = _bt_findsplitloc(rel, origpage, newitemoff, newitemsz,
									 newitem, &newitemonleft);

	/* Allocate temp buffer for leftpage */
	leftpage = PageGetTempPage(origpage);
	_bt_pageinit(leftpage, BufferGetPageSize(buf));
	lopaque = BTPageGetOpaque(leftpage);

	/*
	 * leftpage won't be the root when we're done.  Also, clear the SPLIT_END
	 * and HAS_GARBAGE flags.
	 */
	lopaque->btpo_flags = oopaque->btpo_flags;
	lopaque->btpo_flags &= ~(BTP_ROOT | BTP_SPLIT_END | BTP_HAS_GARBAGE);
	/* set flag in leftpage indicating that rightpage has no downlink yet */
	lopaque->btpo_flags |= BTP_INCOMPLETE_SPLIT;
	lopaque->btpo_prev = oopaque->btpo_prev;
	/* handle btpo_next after rightpage buffer acquired */
	lopaque->btpo_level = oopaque->btpo_level;
	/* handle btpo_cycleid after rightpage buffer acquired */
```

왼쪽 페이지의 새 high key 를 만든다. 리프에서는 `lastleft` 와 `firstright` 를 구분하는 데 필요한 열만 남기고 자른다(suffix truncation). 내부 페이지에서는 `firstright` 를 그대로 쓴다.

`access` / `nbtree` / `nbtinsert.c` L1618-L1705 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1618-L1705))

```c
// nbtinsert.c L1618-L1705
	if (!newitemonleft && newitemoff == firstrightoff)
	{
		/* incoming tuple becomes firstright */
		itemsz = newitemsz;
		firstright = newitem;
	}
	else
	{
		/* existing item at firstrightoff becomes firstright */
		itemid = PageGetItemId(origpage, firstrightoff);
		itemsz = ItemIdGetLength(itemid);
		firstright = (IndexTuple) PageGetItem(origpage, itemid);
		if (firstrightoff == origpagepostingoff)
			firstright = nposting;
	}

	if (isleaf)
	{
		IndexTuple	lastleft;

		/* Attempt suffix truncation for leaf page splits */
		if (newitemonleft && newitemoff == firstrightoff)
		{
			/* incoming tuple becomes lastleft */
			lastleft = newitem;
		}
		else
		{
			OffsetNumber lastleftoff;

			/* existing item before firstrightoff becomes lastleft */
			lastleftoff = OffsetNumberPrev(firstrightoff);
			Assert(lastleftoff >= P_FIRSTDATAKEY(oopaque));
			itemid = PageGetItemId(origpage, lastleftoff);
			lastleft = (IndexTuple) PageGetItem(origpage, itemid);
			if (lastleftoff == origpagepostingoff)
				lastleft = nposting;
		}

		lefthighkey = _bt_truncate(rel, lastleft, firstright, itup_key);
		itemsz = IndexTupleSize(lefthighkey);
	}
	else
	{
		// ... (L1662-L1687 생략: 주석: 내부 페이지에서 자르지 않는 이유(구분 키의 이음매))
		lefthighkey = firstright;
	}

	/*
	 * Add new high key to leftpage
	 */
	afterleftoff = P_HIKEY;

	Assert(BTreeTupleGetNAtts(lefthighkey, rel) > 0);
	Assert(BTreeTupleGetNAtts(lefthighkey, rel) <=
		   IndexRelationGetNumberOfKeyAttributes(rel));
	Assert(itemsz == MAXALIGN(IndexTupleSize(lefthighkey)));
	if (PageAddItem(leftpage, (Item) lefthighkey, itemsz, afterleftoff, false,
					false) == InvalidOffsetNumber)
		elog(ERROR, "failed to add high key to the left sibling"
			 " while splitting block %u of index \"%s\"",
			 origpagenumber, RelationGetRelationName(rel));
	afterleftoff = OffsetNumberNext(afterleftoff);
```

오른쪽 페이지를 받고 형제 링크를 잇는다. 원래 페이지가 오른쪽 끝이 아니면 원래의 high key 가 오른쪽 페이지의 high key 가 된다.

`access` / `nbtree` / `nbtinsert.c` L1720-L1784 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1720-L1784))

```c
// nbtinsert.c L1720-L1784
	rbuf = _bt_allocbuf(rel, heaprel);
	rightpage = BufferGetPage(rbuf);
	rightpagenumber = BufferGetBlockNumber(rbuf);
	/* rightpage was initialized by _bt_allocbuf */
	ropaque = BTPageGetOpaque(rightpage);

	// ... (L1726-L1733 생략: 주석: 두 버퍼를 다 잡은 뒤에야 채우는 필드)
	lopaque->btpo_next = rightpagenumber;
	lopaque->btpo_cycleid = _bt_vacuum_cycleid(rel);

	/*
	 * rightpage won't be the root when we're done.  Also, clear the SPLIT_END
	 * and HAS_GARBAGE flags.
	 */
	ropaque->btpo_flags = oopaque->btpo_flags;
	ropaque->btpo_flags &= ~(BTP_ROOT | BTP_SPLIT_END | BTP_HAS_GARBAGE);
	ropaque->btpo_prev = origpagenumber;
	ropaque->btpo_next = oopaque->btpo_next;
	ropaque->btpo_level = oopaque->btpo_level;
	ropaque->btpo_cycleid = lopaque->btpo_cycleid;

	/*
	 * Add new high key to rightpage where necessary.
	 *
	 * If the page we're splitting is not the rightmost page at its level in
	 * the tree, then the first entry on the page is the high key from
	 * origpage.
	 */
	afterrightoff = P_HIKEY;

	if (!isrightmost)
	{
		IndexTuple	righthighkey;

		itemid = PageGetItemId(origpage, P_HIKEY);
		itemsz = ItemIdGetLength(itemid);
		righthighkey = (IndexTuple) PageGetItem(origpage, itemid);
		Assert(BTreeTupleGetNAtts(righthighkey, rel) > 0);
		Assert(BTreeTupleGetNAtts(righthighkey, rel) <=
			   IndexRelationGetNumberOfKeyAttributes(rel));
		if (PageAddItem(rightpage, (Item) righthighkey, itemsz, afterrightoff,
						false, false) == InvalidOffsetNumber)
		{
			memset(rightpage, 0, BufferGetPageSize(rbuf));
			elog(ERROR, "failed to add high key to the right sibling"
				 " while splitting block %u of index \"%s\"",
				 origpagenumber, RelationGetRelationName(rel));
		}
		afterrightoff = OffsetNumberNext(afterrightoff);
	}

	/*
	 * Internal page splits truncate first data item on right page -- it
	 * becomes "minus infinity" item for the page.  Set this up here.
	 */
	minusinfoff = InvalidOffsetNumber;
	if (!isleaf)
		minusinfoff = afterrightoff;
```

원래 페이지의 항목을 순서대로 나눠 담고, 새 튜플은 제 자리에 끼운다. 내부 페이지면 오른쪽 첫 항목의 키를 지워 "음의 무한대"로 만든다(`_bt_pgaddtup` 의 마지막 인자).

`access` / `nbtree` / `nbtinsert.c` L1793-L1884 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1793-L1884))

```c
// nbtinsert.c L1793-L1884
	for (i = P_FIRSTDATAKEY(oopaque); i <= maxoff; i = OffsetNumberNext(i))
	{
		IndexTuple	dataitem;

		itemid = PageGetItemId(origpage, i);
		itemsz = ItemIdGetLength(itemid);
		dataitem = (IndexTuple) PageGetItem(origpage, itemid);

		/* replace original item with nposting due to posting split? */
		if (i == origpagepostingoff)
		{
			Assert(BTreeTupleIsPosting(dataitem));
			Assert(itemsz == MAXALIGN(IndexTupleSize(nposting)));
			dataitem = nposting;
		}

		/* does new item belong before this one? */
		else if (i == newitemoff)
		{
			if (newitemonleft)
			{
				Assert(newitemoff <= firstrightoff);
				if (!_bt_pgaddtup(leftpage, newitemsz, newitem, afterleftoff,
								  false))
				{
					memset(rightpage, 0, BufferGetPageSize(rbuf));
					elog(ERROR, "failed to add new item to the left sibling"
						 " while splitting block %u of index \"%s\"",
						 origpagenumber, RelationGetRelationName(rel));
				}
				afterleftoff = OffsetNumberNext(afterleftoff);
			}
			else
			{
				Assert(newitemoff >= firstrightoff);
				if (!_bt_pgaddtup(rightpage, newitemsz, newitem, afterrightoff,
								  afterrightoff == minusinfoff))
				{
					memset(rightpage, 0, BufferGetPageSize(rbuf));
					elog(ERROR, "failed to add new item to the right sibling"
						 " while splitting block %u of index \"%s\"",
						 origpagenumber, RelationGetRelationName(rel));
				}
				afterrightoff = OffsetNumberNext(afterrightoff);
			}
		}

		/* decide which page to put it on */
		if (i < firstrightoff)
		{
			if (!_bt_pgaddtup(leftpage, itemsz, dataitem, afterleftoff, false))
			{
				memset(rightpage, 0, BufferGetPageSize(rbuf));
				elog(ERROR, "failed to add old item to the left sibling"
					 " while splitting block %u of index \"%s\"",
					 origpagenumber, RelationGetRelationName(rel));
			}
			afterleftoff = OffsetNumberNext(afterleftoff);
		}
		else
		{
			if (!_bt_pgaddtup(rightpage, itemsz, dataitem, afterrightoff,
							  afterrightoff == minusinfoff))
			{
				memset(rightpage, 0, BufferGetPageSize(rbuf));
				elog(ERROR, "failed to add old item to the right sibling"
					 " while splitting block %u of index \"%s\"",
					 origpagenumber, RelationGetRelationName(rel));
			}
			afterrightoff = OffsetNumberNext(afterrightoff);
		}
	}

	/* Handle case where newitem goes at the end of rightpage */
	if (i <= newitemoff)
	{
		/*
		 * Can't have newitemonleft here; that would imply we were told to put
		 * *everything* on the left page, which cannot fit (if it could, we'd
		 * not be splitting the page).
		 */
		Assert(!newitemonleft && newitemoff == maxoff + 1);
		if (!_bt_pgaddtup(rightpage, newitemsz, newitem, afterrightoff,
						  afterrightoff == minusinfoff))
		{
			memset(rightpage, 0, BufferGetPageSize(rbuf));
			elog(ERROR, "failed to add new item to the right sibling"
				 " while splitting block %u of index \"%s\"",
				 origpagenumber, RelationGetRelationName(rel));
		}
		afterrightoff = OffsetNumberNext(afterrightoff);
	}
```

원래 오른쪽 형제의 왼쪽 링크를 고치기 위해 그 페이지도 쓰기 잠금으로 잡는다. 그 다음 크리티컬 섹션에서 임시 왼쪽 페이지를 원래 페이지 위에 덮어쓴다.

`access` / `nbtree` / `nbtinsert.c` L1891-L1964 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1891-L1964))

```c
// nbtinsert.c L1891-L1964
	if (!isrightmost)
	{
		sbuf = _bt_getbuf(rel, oopaque->btpo_next, BT_WRITE);
		spage = BufferGetPage(sbuf);
		sopaque = BTPageGetOpaque(spage);
		if (sopaque->btpo_prev != origpagenumber)
		{
			memset(rightpage, 0, BufferGetPageSize(rbuf));
			ereport(ERROR,
					(errcode(ERRCODE_INDEX_CORRUPTED),
					 errmsg_internal("right sibling's left-link doesn't match: "
									 "block %u links to %u instead of expected %u in index \"%s\"",
									 oopaque->btpo_next, sopaque->btpo_prev, origpagenumber,
									 RelationGetRelationName(rel))));
		}

		// ... (L1907-L1919 생략: 주석: SPLIT_END 와 vacuum 의 cycle id)
		if (sopaque->btpo_cycleid != ropaque->btpo_cycleid)
			ropaque->btpo_flags |= BTP_SPLIT_END;
	}

	/*
	 * Right sibling is locked, new siblings are prepared, but original page
	 * is not updated yet.
	 *
	 * NO EREPORT(ERROR) till right sibling is updated.  We can get away with
	 * not starting the critical section till here because we haven't been
	 * scribbling on the original page yet; see comments above.
	 */
	START_CRIT_SECTION();

	/*
	 * By here, the original data page has been split into two new halves, and
	 * these are correct.  The algorithm requires that the left page never
	 * move during a split, so we copy the new left page back on top of the
	 * original.  We need to do this before writing the WAL record, so that
	 * XLogInsert can WAL log an image of the page if necessary.
	 */
	PageRestoreTempPage(leftpage, origpage);
	/* leftpage, lopaque must not be used below here */

	MarkBufferDirty(buf);
	MarkBufferDirty(rbuf);

	if (!isrightmost)
	{
		sopaque->btpo_prev = rightpagenumber;
		MarkBufferDirty(sbuf);
	}

	/*
	 * Clear INCOMPLETE_SPLIT flag on child if inserting the new item finishes
	 * a split
	 */
	if (!isleaf)
	{
		Page		cpage = BufferGetPage(cbuf);
		BTPageOpaque cpageop = BTPageGetOpaque(cpage);

		cpageop->btpo_flags &= ~BTP_INCOMPLETE_SPLIT;
		MarkBufferDirty(cbuf);
	}
```

WAL 에는 오른쪽 페이지 전체와 왼쪽의 새 high key 를 남긴다. 새 튜플은 왼쪽에 들어갔을 때만 따로 남긴다.

`access` / `nbtree` / `nbtinsert.c` L1966-L2080 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1966-L2080))

```c
// nbtinsert.c L1966-L2080
	/* XLOG stuff */
	if (RelationNeedsWAL(rel))
	{
		xl_btree_split xlrec;
		uint8		xlinfo;
		XLogRecPtr	recptr;

		xlrec.level = ropaque->btpo_level;
		/* See comments below on newitem, orignewitem, and posting lists */
		xlrec.firstrightoff = firstrightoff;
		xlrec.newitemoff = newitemoff;
		xlrec.postingoff = 0;
		if (postingoff != 0 && origpagepostingoff < firstrightoff)
			xlrec.postingoff = postingoff;

		XLogBeginInsert();
		XLogRegisterData(&xlrec, SizeOfBtreeSplit);

		XLogRegisterBuffer(0, buf, REGBUF_STANDARD);
		XLogRegisterBuffer(1, rbuf, REGBUF_WILL_INIT);
		/* Log original right sibling, since we've changed its prev-pointer */
		if (!isrightmost)
			XLogRegisterBuffer(2, sbuf, REGBUF_STANDARD);
		if (!isleaf)
			XLogRegisterBuffer(3, cbuf, REGBUF_STANDARD);

		// ... (L1992-L2018 생략: 주석: posting 분할과 겹칠 때 무엇을 기록하나)
		if (newitemonleft && xlrec.postingoff == 0)
			XLogRegisterBufData(0, newitem, newitemsz);
		else if (xlrec.postingoff != 0)
		{
			Assert(isleaf);
			Assert(newitemonleft || firstrightoff == newitemoff);
			Assert(newitemsz == IndexTupleSize(orignewitem));
			XLogRegisterBufData(0, orignewitem, newitemsz);
		}

		/* Log the left page's new high key */
		if (!isleaf)
		{
			/* lefthighkey isn't local copy, get current pointer */
			itemid = PageGetItemId(origpage, P_HIKEY);
			lefthighkey = (IndexTuple) PageGetItem(origpage, itemid);
		}
		XLogRegisterBufData(0, lefthighkey,
							MAXALIGN(IndexTupleSize(lefthighkey)));

		// ... (L2039-L2048 생략: 주석: 오른쪽 페이지는 튜플만 기록하고 라인 포인터는 복구 때 다시 만든다)
		XLogRegisterBufData(1,
							(char *) rightpage + ((PageHeader) rightpage)->pd_upper,
							((PageHeader) rightpage)->pd_special - ((PageHeader) rightpage)->pd_upper);

		xlinfo = newitemonleft ? XLOG_BTREE_SPLIT_L : XLOG_BTREE_SPLIT_R;
		recptr = XLogInsert(RM_BTREE_ID, xlinfo);

		PageSetLSN(origpage, recptr);
		PageSetLSN(rightpage, recptr);
		if (!isrightmost)
			PageSetLSN(spage, recptr);
		if (!isleaf)
			PageSetLSN(BufferGetPage(cbuf), recptr);
	}

	END_CRIT_SECTION();

	/* release the old right sibling */
	if (!isrightmost)
		_bt_relbuf(rel, sbuf);

	/* release the child */
	if (!isleaf)
		_bt_relbuf(rel, cbuf);

	/* be tidy */
	if (isleaf)
		pfree(lefthighkey);

	/* split's done */
	return rbuf;
}
```

## 동작 흐름

```text
 L1542 firstrightoff = [10] _bt_findsplitloc(..., &newitemonleft)
 L1546 leftpage = PageGetTempPage                       작업용 사본
 L1554 lopaque 플래그 = 원래 & ~(ROOT | SPLIT_END | HAS_GARBAGE) | INCOMPLETE_SPLIT
 L1618 firstright = 새 튜플 또는 원래 페이지의 firstrightoff 항목
 L1634 리프면 lastleft 를 찾고 L1657 lefthighkey = _bt_truncate(lastleft, firstright)
       내부면 L1688 lefthighkey = firstright
 L1700 왼쪽 P_HIKEY 에 lefthighkey
 L1720 rbuf = _bt_allocbuf                              FSM 의 재사용 페이지, 없으면 relation 확장
 L1734 왼쪽 next = 오른쪽,  L1743 오른쪽 prev = 원래 블록, next = 원래 next
 L1757 원래가 오른쪽 끝이 아니면 원래 high key 를 오른쪽 P_HIKEY 에
 L1793 원래 항목 i 마다
         i == newitemoff 면 새 튜플을 먼저 (newitemonleft 로 쪽 결정)
         i < firstrightoff 면 왼쪽, 아니면 오른쪽
 L1867 새 튜플이 맨 끝이면 오른쪽 끝에 붙인다
 L1891 원래 오른쪽 형제 S 를 BT_WRITE 로, prev 가 원래 블록인지 확인
 L1932 START_CRIT_SECTION
 L1941   PageRestoreTempPage(leftpage -> origpage)      왼쪽은 같은 블록 번호에 남는다
 L1949   S.prev = 오른쪽
 L1957   내부 분할이면 자식(cbuf) 의 INCOMPLETE_SPLIT 해제
 L2054   XLogInsert(XLOG_BTREE_SPLIT_L 또는 _R)
 L2064 END_CRIT_SECTION
 L2079 return rbuf                                      왼쪽, 오른쪽 둘 다 쓰기 잠금 상태
```

아래는 `int4` 기본키에 1 부터 차례로 넣다가 408 을 넣는 순간, 루트이자 유일한 리프인 블록 1 이 쪼개지는 모습이다. 분할 지점 367 은 [10] 에서 소스 규칙으로 계산한 값이다.

```text
 전   블록 1  (LEAF | ROOT, prev 0, next 0)  오른쪽 끝이라 high key 없음
      off   1    2    3   ...  366   367   368  ...  407
      key   1    2    3   ...  366   367   368  ...  407         + 새 튜플 408 (newitemoff 408)
      PageGetFreeSpace = 8  <  16

 [10] 결과   firstrightoff = 367, newitemonleft = false

 후   블록 1  (LEAF | INCOMPLETE_SPLIT, prev 0, next 2)
      off   1           2    3   ...  367
      key   hikey 367   1    2   ...  366                         366 개
            (lastleft 366, firstright 367 -> _bt_truncate 가 키 열만 남김)

      블록 2  (LEAF, prev 1, next 0)  새로 받은 블록. 오른쪽 끝이라 high key 없음
      off   1     2    ...  41    42
      key   367   368  ...  407   408                             42 개

 남는 공간 (항목 20 바이트, high key 16 + 4)
      블록 1   8152 - 20 - 366*20 = 812 바이트    약 90% 참
      블록 2   8152 - 42*20      = 7312 바이트
 이 시점에 블록 1 의 high key 367 보다 큰 키를 찾는 탐색은 next 로 블록 2 에 닿는다
 루트 블록 3 은 [12] _bt_newlevel 이 만든다
```

```text
 리프 분할과 내부 분할의 차이 (같은 함수, isleaf 로 갈린다)

 item              isleaf                               !isleaf
 left high key     _bt_truncate(lastleft, firstright)   firstright (L1688)
 right first item  as is                                key stripped, downlink only
 cbuf              none                                 child, INCOMPLETE_SPLIT cleared (L1957)
 WAL buffers       0 left, 1 right, 2 old sibling       + 3 child

 리프의 왼쪽 high key 는 구분에 필요한 열만 남기고 힙 TID 는 대개 떨어진다
 내부 분할의 오른쪽 첫 항목은 _bt_pgaddtup(..., afterrightoff == minusinfoff) 로 키를 지워 음의 무한대가 된다
```

분할에서 잠그는 페이지와 순서다. 왼쪽에서 오른쪽으로만 잠그므로 교착이 없다고 소스가 적는다(L1887-L1889).

```text
 잠금 (모두 쓰기 잠금)

 원래 페이지 buf      [04] 부터 쥐고 있다 -> 분할 뒤에도 유지, [11] 의 부모 삽입이 끝날 때 해제
 새 오른쪽 rbuf       L1720 에서 잡는다  -> [11] 이 부모를 잡은 뒤 해제
 원래 오른쪽 형제 S   L1893 에서 잡는다  -> L2068 에서 해제
 내부 분할의 cbuf     호출자가 쥐고 옴   -> L2072 에서 해제
```

## 결과가 쓰이는 곳

```text
 rbuf (오른쪽 페이지, 쓰기 잠금)
      --> [11] _bt_insert_parent 가 왼쪽 high key 를 복사해 rbuf 를 가리키는 downlink 를 만든다
 왼쪽 페이지의 INCOMPLETE_SPLIT
      --> 부모 삽입이 같은 WAL 레코드 안에서 지운다 ([08] L1307 또는 [12])
      --> 그 전에 죽으면 다음 쓰기 탐색이 _bt_finish_split 으로 마무리한다 ([05])
 XLOG_BTREE_SPLIT_L / _R
      --> 복구 때 btree_xlog_split 이 오른쪽 페이지를 기록된 튜플로 다시 만든다
```

## 다루지 않는 것

suffix truncation 의 세부(`_bt_truncate`, `_bt_keep_natts`), posting list 분할이 페이지 분할과 겹치는 경우(`origpagepostingoff`), vacuum 의 cycle id 와 `BTP_SPLIT_END`, 술어 잠금 이전(`PredicateLockPageSplit`), 복구 함수 `btree_xlog_split` 은 다루지 않는다.
