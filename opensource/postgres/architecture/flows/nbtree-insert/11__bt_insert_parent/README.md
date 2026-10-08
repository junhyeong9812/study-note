# _bt_insert_parent

상위: [nbtree 삽입과 분할](../README.md)

**분할을 마무리한다. 왼쪽 페이지의 high key 를 복사해 오른쪽 페이지를 가리키는 downlink 로 만들고, 부모 페이지에 넣는다.** 쪼갠 것이 루트였으면 `_bt_newlevel` 로 새 루트를 만든다. 부모는 내려올 때 쌓은 스택으로 찾되, 그 사이 부모도 쪼개졌을 수 있으므로 `_bt_getstackbuf` 가 downlink 의 블록 번호로 다시 찾는다. 이 문서는 `_bt_getstackbuf` 와, 끊긴 분할을 이어 주는 `_bt_finish_split` 을 함께 다룬다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L2099-L2225 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2099-L2225))

함께 다루는 함수 (같은 파일):

- `_bt_getstackbuf`: `access` / `nbtree` / `nbtinsert.c` L2319-L2423 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2319-L2423))
- `_bt_finish_split`: `access` / `nbtree` / `nbtinsert.c` L2241-L2285 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2241-L2285))

## 실제 코드

루트를 쪼갰으면 새 레벨을 만들고 끝이다. 아니면 downlink 를 만들어 부모에 재귀 삽입한다.

`access` / `nbtree` / `nbtinsert.c` L2099-L2225 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2099-L2225))

```c
// nbtinsert.c L2099-L2225
_bt_insert_parent(Relation rel,
				  Relation heaprel,
				  Buffer buf,
				  Buffer rbuf,
				  BTStack stack,
				  bool isroot,
				  bool isonly)
{
	Assert(heaprel != NULL);

	// ... (L2109-L2121 생략: 주석: Lehman-Yao 가 말하지 않은 루트 분할)
	if (isroot)
	{
		Buffer		rootbuf;

		Assert(stack == NULL);
		Assert(isonly);
		/* create a new root node one level up and update the metapage */
		rootbuf = _bt_newlevel(rel, heaprel, buf, rbuf);
		/* release the split buffers */
		_bt_relbuf(rel, rootbuf);
		_bt_relbuf(rel, rbuf);
		_bt_relbuf(rel, buf);
	}
	else
	{
		BlockNumber bknum = BufferGetBlockNumber(buf);
		BlockNumber rbknum = BufferGetBlockNumber(rbuf);
		Page		page = BufferGetPage(buf);
		IndexTuple	new_item;
		BTStackData fakestack;
		IndexTuple	ritem;
		Buffer		pbuf;

		if (stack == NULL)
		{
			BTPageOpaque opaque;

			elog(DEBUG2, "concurrent ROOT page split");
			opaque = BTPageGetOpaque(page);

			// ... (L2152-L2163 생략: 주석: fastpath 뒤에는 여기 오면 안 된다)
			Assert(!(P_ISLEAF(opaque) &&
					 BlockNumberIsValid(RelationGetTargetBlock(rel))));

			/* Find the leftmost page at the next level up */
			pbuf = _bt_get_endpoint(rel, opaque->btpo_level + 1, false);
			/* Set up a phony stack entry pointing there */
			stack = &fakestack;
			stack->bts_blkno = BufferGetBlockNumber(pbuf);
			stack->bts_offset = InvalidOffsetNumber;
			stack->bts_parent = NULL;
			_bt_relbuf(rel, pbuf);
		}

		/* get high key from left, a strict lower bound for new right page */
		ritem = (IndexTuple) PageGetItem(page,
										 PageGetItemId(page, P_HIKEY));

		/* form an index tuple that points at the new right page */
		new_item = CopyIndexTuple(ritem);
		BTreeTupleSetDownLink(new_item, rbknum);

		// ... (L2185-L2193 생략: 주석)
		pbuf = _bt_getstackbuf(rel, heaprel, stack, bknum);

		// ... (L2196-L2208 생략: 주석: 오른쪽 자식 잠금을 여기까지 쥐는 이유)
		_bt_relbuf(rel, rbuf);

		if (pbuf == InvalidBuffer)
			ereport(ERROR,
					(errcode(ERRCODE_INDEX_CORRUPTED),
					 errmsg_internal("failed to re-find parent key in index \"%s\" for split pages %u/%u",
									 RelationGetRelationName(rel), bknum, rbknum)));

		/* Recursively insert into the parent */
		_bt_insertonpg(rel, heaprel, NULL, pbuf, buf, stack->bts_parent,
					   new_item, MAXALIGN(IndexTupleSize(new_item)),
					   stack->bts_offset + 1, 0, isonly);

		/* be tidy */
		pfree(new_item);
	}
}
```

부모 페이지에서 자식 블록 번호를 가진 pivot 을 찾는다. 스택이 기억한 오프셋부터 오른쪽, 그 다음 왼쪽을 본다. 없으면 오른쪽 형제로 간다.

`access` / `nbtree` / `nbtinsert.c` L2319-L2423 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2319-L2423))

```c
// nbtinsert.c L2319-L2423
_bt_getstackbuf(Relation rel, Relation heaprel, BTStack stack, BlockNumber child)
{
	BlockNumber blkno;
	OffsetNumber start;

	blkno = stack->bts_blkno;
	start = stack->bts_offset;

	for (;;)
	{
		Buffer		buf;
		Page		page;
		BTPageOpaque opaque;

		buf = _bt_getbuf(rel, blkno, BT_WRITE);
		page = BufferGetPage(buf);
		opaque = BTPageGetOpaque(page);

		Assert(heaprel != NULL);
		if (P_INCOMPLETE_SPLIT(opaque))
		{
			_bt_finish_split(rel, heaprel, buf, stack->bts_parent);
			continue;
		}

		if (!P_IGNORE(opaque))
		{
			OffsetNumber offnum,
						minoff,
						maxoff;
			ItemId		itemid;
			IndexTuple	item;

			minoff = P_FIRSTDATAKEY(opaque);
			maxoff = PageGetMaxOffsetNumber(page);

			// ... (L2355-L2359 생략: 주석)
			if (start < minoff)
				start = minoff;

			// ... (L2363-L2366 생략: 주석)
			if (start > maxoff)
				start = OffsetNumberNext(maxoff);

			// ... (L2370-L2374 생략: 주석)
			for (offnum = start;
				 offnum <= maxoff;
				 offnum = OffsetNumberNext(offnum))
			{
				itemid = PageGetItemId(page, offnum);
				item = (IndexTuple) PageGetItem(page, itemid);

				if (BTreeTupleGetDownLink(item) == child)
				{
					/* Return accurate pointer to where link is now */
					stack->bts_blkno = blkno;
					stack->bts_offset = offnum;
					return buf;
				}
			}

			for (offnum = OffsetNumberPrev(start);
				 offnum >= minoff;
				 offnum = OffsetNumberPrev(offnum))
			{
				itemid = PageGetItemId(page, offnum);
				item = (IndexTuple) PageGetItem(page, itemid);

				if (BTreeTupleGetDownLink(item) == child)
				{
					/* Return accurate pointer to where link is now */
					stack->bts_blkno = blkno;
					stack->bts_offset = offnum;
					return buf;
				}
			}
		}

		// ... (L2408-L2413 생략: 주석: Lehman-Yao 와 달리 잠금을 엮지 않는다)
		if (P_RIGHTMOST(opaque))
		{
			_bt_relbuf(rel, buf);
			return InvalidBuffer;
		}
		blkno = opaque->btpo_next;
		start = InvalidOffsetNumber;
		_bt_relbuf(rel, buf);
	}
}
```

`INCOMPLETE_SPLIT` 이 남은 페이지를 만나면 이 함수로 분할의 뒷부분만 다시 한다.

`access` / `nbtree` / `nbtinsert.c` L2241-L2285 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2241-L2285))

```c
// nbtinsert.c L2241-L2285
_bt_finish_split(Relation rel, Relation heaprel, Buffer lbuf, BTStack stack)
{
	Page		lpage = BufferGetPage(lbuf);
	BTPageOpaque lpageop = BTPageGetOpaque(lpage);
	Buffer		rbuf;
	Page		rpage;
	BTPageOpaque rpageop;
	bool		wasroot;
	bool		wasonly;

	Assert(P_INCOMPLETE_SPLIT(lpageop));
	Assert(heaprel != NULL);

	/* Lock right sibling, the one missing the downlink */
	rbuf = _bt_getbuf(rel, lpageop->btpo_next, BT_WRITE);
	rpage = BufferGetPage(rbuf);
	rpageop = BTPageGetOpaque(rpage);

	/* Could this be a root split? */
	if (!stack)
	{
		Buffer		metabuf;
		Page		metapg;
		BTMetaPageData *metad;

		/* acquire lock on the metapage */
		metabuf = _bt_getbuf(rel, BTREE_METAPAGE, BT_WRITE);
		metapg = BufferGetPage(metabuf);
		metad = BTPageGetMeta(metapg);

		wasroot = (metad->btm_root == BufferGetBlockNumber(lbuf));

		_bt_relbuf(rel, metabuf);
	}
	else
		wasroot = false;

	/* Was this the only page on the level before split? */
	wasonly = (P_LEFTMOST(lpageop) && P_RIGHTMOST(rpageop));

	elog(DEBUG1, "finishing incomplete split of %u/%u",
		 BufferGetBlockNumber(lbuf), BufferGetBlockNumber(rbuf));

	_bt_insert_parent(rel, heaprel, lbuf, rbuf, stack, wasroot, wasonly);
}
```

## 동작 흐름

```text
 L2122 isroot (쪼갠 페이지가 루트였다)
 L2129   rootbuf = [12] _bt_newlevel(buf, rbuf)
 L2131   rootbuf, rbuf, buf 해제                             끝
 L2135 아니면
 L2145   stack == NULL (루트를 읽은 뒤 누가 루트를 쪼갰다)
 L2168     _bt_get_endpoint(레벨 + 1) 로 그 레벨 왼쪽 끝을 찾아 가짜 스택을 만든다
 L2178   ritem = 왼쪽 페이지의 P_HIKEY                       오른쪽 페이지 키의 하한
 L2182   new_item = 복사, L2183 downlink = 오른쪽 블록
 L2194   pbuf = _bt_getstackbuf(stack, 왼쪽 블록)            부모 쓰기 잠금
 L2209   오른쪽 자식 해제                                    왼쪽 자식은 아직 쥔다
 L2218   [08] _bt_insertonpg(pbuf, cbuf = 왼쪽, stack->bts_parent,
                             new_item, newitemoff = bts_offset + 1, split_only_page = isonly)

 _bt_getstackbuf (부모 찾기)
 L2333   스택의 블록을 BT_WRITE 로
 L2338   INCOMPLETE_SPLIT 이면 _bt_finish_split 후 다시
 L2344   죽은 페이지가 아니면
 L2375     start 부터 오른쪽으로, downlink == child 면 스택을 고쳐 return
 L2391     start 앞에서 왼쪽으로
 L2414   오른쪽 끝이면 InvalidBuffer (손상)
 L2419   다음 형제로, start = 처음부터
```

아래는 [05] 그림의 두 번째 분할이 부모에 반영되는 과정이다. 774 를 넣던 백엔드가 블록 2 를 쪼갠 직후다. 숫자는 [10] 의 규칙으로 계산했다.

```text
 분할 직후 (블록 2 와 4 는 쓰기 잠금, 블록 2 는 INCOMPLETE_SPLIT)

 루트 3 (레벨 1, 오른쪽 끝이라 데이터는 오프셋 1 부터)
   off 1 [ -inf -> 1 ]
   off 2 [ 367  -> 2 ]          774 를 찾아 내려올 때 고른 pivot. stack = (블록 3, off 2)

 [블록 1] 1..366 hikey 367  ->  [블록 2] 367..732 hikey 733  ->  [블록 4] 733..774

 _bt_insert_parent
   ritem = 블록 2 의 high key (733)
   new_item = (733 -> 4)
   _bt_getstackbuf: 블록 3 을 잡고 off 2 부터 본다 -> downlink 2 를 바로 찾는다
   _bt_insertonpg(블록 3, cbuf = 블록 2, newitemoff = 2 + 1 = 3)

 후
 루트 3
   off 1 [ -inf -> 1 ]
   off 2 [ 367  -> 2 ]
   off 3 [ 733  -> 4 ]          새 downlink. 같은 WAL 레코드 (XLOG_BTREE_INSERT_UPPER) 에서
                                블록 2 의 INCOMPLETE_SPLIT 이 지워진다
```

부모 쪽 자리가 내려올 때와 달라졌을 수 있다. 그 사이 다른 백엔드가 부모에 항목을 넣었거나 부모를 쪼갰으면 스택의 오프셋이나 블록이 낡는다. `_bt_getstackbuf` 는 키가 아니라 downlink 의 블록 번호로 찾으므로 키 비교 없이 확실히 찾는다(nbtree/README L139-L157).

```text
 _bt_getstackbuf 의 탐색 순서 (start = 스택의 오프셋)

 부모 페이지 P (스택의 블록)
   off  minoff ... start-1   start ... maxoff

   1  start 부터 오른쪽     삽입으로 pivot 이 오른쪽으로 밀렸을 가능성이 크다
   2  start 앞에서 왼쪽     삭제로 왼쪽으로 당겨졌을 수 있다
   3  못 찾으면 P 의 오른쪽 형제로 가서 처음부터   P 가 쪼개져 pivot 이 옮겨갔다
```

```text
 끊긴 분할의 복구 (서버가 [09] 와 부모 삽입 사이에 죽은 경우)

 WAL 에는 SPLIT 레코드만 있고 INSERT_UPPER 레코드는 없다
   -> 복구 뒤 왼쪽 페이지에 INCOMPLETE_SPLIT 이 남는다
   -> 오른쪽 페이지는 right link 로만 닿는다 (검색은 문제없다, [05])
 다음 쓰기 탐색이 그 페이지를 지날 때
   _bt_moveright 또는 _bt_getstackbuf 또는 _bt_stepright 가 발견
   -> _bt_finish_split(lbuf, stack)
        오른쪽 형제를 쓰기 잠금 (L2255)
        stack 이 없으면 메타페이지로 루트였는지 판단 (L2260-L2277)
        _bt_insert_parent(lbuf, rbuf, stack, wasroot, wasonly)  (L2284)
```

## 결과가 쓰이는 곳

```text
 부모 페이지의 새 pivot (high key 복사 + 오른쪽 downlink)
      --> 이후 탐색이 루트에서 바로 오른쪽 페이지로 내려간다. right link 우회가 없어진다
 부모가 꽉 찼으면
      --> [08] -> [09] 로 부모가 쪼개지고 이 함수가 한 레벨 위에서 다시 불린다
 루트였으면
      --> [12] _bt_newlevel 이 트리 높이를 하나 늘린다
```

## 다루지 않는 것

`_bt_get_endpoint` 로 레벨의 왼쪽 끝을 찾는 절차, 페이지 삭제(vacuum 의 `_bt_pagedel`)와 부모 탐색의 상호작용, 복구 코드가 끊긴 분할을 남기는 방식은 다루지 않는다.
