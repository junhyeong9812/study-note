# _bt_search_insert

상위: [nbtree 삽입과 분할](../README.md)

**넣을 리프 페이지를 찾아 쓰기 잠금을 잡는다.** 먼저 "지난번에 넣은 가장 오른쪽 리프" 캐시를 시험해 보고, 쓸 수 없으면 루트부터 내려가는 `_bt_search` 를 부른다. 내려가는 길에 페이지가 그 사이 쪼개졌으면 `_bt_moveright` 가 high key 를 보고 오른쪽 링크를 따라간다. 이것이 Lehman-Yao 알고리즘의 핵심이고, 이 문서는 `_bt_search` 와 `_bt_moveright` 를 함께 다룬다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L317-L382 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L317-L382))

함께 다루는 함수:

- `_bt_search`: `access` / `nbtree` / `nbtsearch.c` L107-L212 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsearch.c#L107-L212))
- `_bt_moveright`: `access` / `nbtree` / `nbtsearch.c` L246-L326 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsearch.c#L246-L326))

## 실제 코드

오른쪽 끝 리프 캐시(fastpath)를 먼저 본다. 잠금은 조건부로만 잡고, 기다려야 하면 포기한다.

`access` / `nbtree` / `nbtinsert.c` L317-L382 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L317-L382))

```c
// nbtinsert.c L317-L382
_bt_search_insert(Relation rel, Relation heaprel, BTInsertState insertstate)
{
	Assert(insertstate->buf == InvalidBuffer);
	Assert(!insertstate->bounds_valid);
	Assert(insertstate->postingoff == 0);

	if (RelationGetTargetBlock(rel) != InvalidBlockNumber)
	{
		/* Simulate a _bt_getbuf() call with conditional locking */
		insertstate->buf = ReadBuffer(rel, RelationGetTargetBlock(rel));
		if (_bt_conditionallockbuf(rel, insertstate->buf))
		{
			Page		page;
			BTPageOpaque opaque;

			_bt_checkpage(rel, insertstate->buf);
			page = BufferGetPage(insertstate->buf);
			opaque = BTPageGetOpaque(page);

			/*
			 * Check if the page is still the rightmost leaf page and has
			 * enough free space to accommodate the new tuple.  Also check
			 * that the insertion scan key is strictly greater than the first
			 * non-pivot tuple on the page.  (Note that we expect itup_key's
			 * scantid to be unset when our caller is a checkingunique
			 * inserter.)
			 */
			if (P_RIGHTMOST(opaque) &&
				P_ISLEAF(opaque) &&
				!P_IGNORE(opaque) &&
				PageGetFreeSpace(page) > insertstate->itemsz &&
				PageGetMaxOffsetNumber(page) >= P_HIKEY &&
				_bt_compare(rel, insertstate->itup_key, page, P_HIKEY) > 0)
			{
				// ... (L351-L362 생략: 주석: fastpath 에서는 NULL stack 을 돌려준다)
				return NULL;
			}

			/* Page unsuitable for caller, drop lock and pin */
			_bt_relbuf(rel, insertstate->buf);
		}
		else
		{
			/* Lock unavailable, drop pin */
			ReleaseBuffer(insertstate->buf);
		}

		/* Forget block, since cache doesn't appear to be useful */
		RelationSetTargetBlock(rel, InvalidBlockNumber);
	}

	/* Cannot use optimization -- descend tree, return proper descent stack */
	return _bt_search(rel, heaprel, insertstate->itup_key, &insertstate->buf,
					  BT_WRITE);
}
```

`_bt_search` 는 루트에서 시작해 레벨마다 `_bt_moveright` 로 high key 를 확인하고, 이진 탐색으로 내려갈 자식을 고르고, 스택에 지나온 자리를 쌓는다.

`access` / `nbtree` / `nbtsearch.c` L107-L212 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsearch.c#L107-L212))

```c
// nbtsearch.c L107-L212
_bt_search(Relation rel, Relation heaprel, BTScanInsert key, Buffer *bufP,
		   int access)
{
	BTStack		stack_in = NULL;
	int			page_access = BT_READ;

	/* heaprel must be set whenever _bt_allocbuf is reachable */
	Assert(access == BT_READ || access == BT_WRITE);
	Assert(access == BT_READ || heaprel != NULL);

	/* Get the root page to start with */
	*bufP = _bt_getroot(rel, heaprel, access);

	/* If index is empty and access = BT_READ, no root page is created. */
	if (!BufferIsValid(*bufP))
		return (BTStack) NULL;

	/* Loop iterates once per level descended in the tree */
	for (;;)
	{
		Page		page;
		BTPageOpaque opaque;
		OffsetNumber offnum;
		ItemId		itemid;
		IndexTuple	itup;
		BlockNumber child;
		BTStack		new_stack;

		// ... (L135-L146 생략: 주석: 그 사이 페이지가 쪼개졌으면 오른쪽으로)
		*bufP = _bt_moveright(rel, heaprel, key, *bufP, (access == BT_WRITE),
							  stack_in, page_access);

		/* if this is a leaf page, we're done */
		page = BufferGetPage(*bufP);
		opaque = BTPageGetOpaque(page);
		if (P_ISLEAF(opaque))
			break;

		/*
		 * Find the appropriate pivot tuple on this page.  Its downlink points
		 * to the child page that we're about to descend to.
		 */
		offnum = _bt_binsrch(rel, key, *bufP);
		itemid = PageGetItemId(page, offnum);
		itup = (IndexTuple) PageGetItem(page, itemid);
		Assert(BTreeTupleIsPivot(itup) || !key->heapkeyspace);
		child = BTreeTupleGetDownLink(itup);

		/*
		 * We need to save the location of the pivot tuple we chose in a new
		 * stack entry for this page/level.  If caller ends up splitting a
		 * page one level down, it usually ends up inserting a new pivot
		 * tuple/downlink immediately after the location recorded here.
		 */
		new_stack = (BTStack) palloc(sizeof(BTStackData));
		new_stack->bts_blkno = BufferGetBlockNumber(*bufP);
		new_stack->bts_offset = offnum;
		new_stack->bts_parent = stack_in;

		/*
		 * Page level 1 is lowest non-leaf page level prior to leaves.  So, if
		 * we're on the level 1 and asked to lock leaf page in write mode,
		 * then lock next page in write mode, because it must be a leaf.
		 */
		if (opaque->btpo_level == 1 && access == BT_WRITE)
			page_access = BT_WRITE;

		/* drop the read lock on the page, then acquire one on its child */
		*bufP = _bt_relandgetbuf(rel, *bufP, child, page_access);

		/* okay, all set to move down a level */
		stack_in = new_stack;
	}

	/*
	 * If we're asked to lock leaf in write mode, but didn't manage to, then
	 * relock.  This should only happen when the root page is a leaf page (and
	 * the only page in the index other than the metapage).
	 */
	if (access == BT_WRITE && page_access == BT_READ)
	{
		/* trade in our read lock for a write lock */
		_bt_unlockbuf(rel, *bufP);
		_bt_lockbuf(rel, *bufP, BT_WRITE);

		/*
		 * Race -- the leaf page may have split after we dropped the read lock
		 * but before we acquired a write lock.  If it has, we may need to
		 * move right to its new sibling.  Do that.
		 */
		*bufP = _bt_moveright(rel, heaprel, key, *bufP, true, stack_in, BT_WRITE);
	}

	return stack_in;
}
```

`_bt_moveright` 는 찾는 키가 페이지의 high key 보다 크면 오른쪽 형제로 옮긴다. 쓰기 모드면 가는 길에 마무리되지 않은 분할도 끝낸다.

`access` / `nbtree` / `nbtsearch.c` L246-L326 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsearch.c#L246-L326))

```c
// nbtsearch.c L246-L326
_bt_moveright(Relation rel,
			  Relation heaprel,
			  BTScanInsert key,
			  Buffer buf,
			  bool forupdate,
			  BTStack stack,
			  int access)
{
	Page		page;
	BTPageOpaque opaque;
	int32		cmpval;

	Assert(!forupdate || heaprel != NULL);

	// ... (L260-L276 생략: 주석: nextkey 와 죽은 페이지)
	cmpval = key->nextkey ? 0 : 1;

	for (;;)
	{
		page = BufferGetPage(buf);
		opaque = BTPageGetOpaque(page);

		if (P_RIGHTMOST(opaque))
			break;

		/*
		 * Finish any incomplete splits we encounter along the way.
		 */
		if (forupdate && P_INCOMPLETE_SPLIT(opaque))
		{
			BlockNumber blkno = BufferGetBlockNumber(buf);

			/* upgrade our lock if necessary */
			if (access == BT_READ)
			{
				_bt_unlockbuf(rel, buf);
				_bt_lockbuf(rel, buf, BT_WRITE);
			}

			if (P_INCOMPLETE_SPLIT(opaque))
				_bt_finish_split(rel, heaprel, buf, stack);
			else
				_bt_relbuf(rel, buf);

			/* re-acquire the lock in the right mode, and re-check */
			buf = _bt_getbuf(rel, blkno, access);
			continue;
		}

		if (P_IGNORE(opaque) || _bt_compare(rel, key, page, P_HIKEY) >= cmpval)
		{
			/* step right one page */
			buf = _bt_relandgetbuf(rel, buf, opaque->btpo_next, access);
			continue;
		}
		else
			break;
	}

	if (P_IGNORE(opaque))
		elog(ERROR, "fell off the end of index \"%s\"",
			 RelationGetRelationName(rel));

	return buf;
}
```

## 동작 흐름

```text
 _bt_search_insert
 L323  RelationGetTargetBlock(rel) 이 있으면                fastpath 후보
 L327    _bt_conditionallockbuf                            기다리지 않는 쓰기 잠금
 L344    오른쪽 끝 리프이고, 무시할 페이지가 아니고,
         새 튜플이 들어갈 공간이 있고, 새 키 > 첫 키       -> L363 return NULL (스택 없음)
         아니면 버퍼를 놓고 L376 캐시를 지운다
 L380  _bt_search(rel, heaprel, key, &buf, BT_WRITE)

 _bt_search
 L118  _bt_getroot                                         메타페이지 -> (fast)root. 비어 있으면 만든다
 L125  for (;;)  레벨마다
 L147    _bt_moveright                                     high key < key 면 오른쪽으로
 L153    리프면 break
 L160    offnum = _bt_binsrch                              "key 보다 작은 마지막 pivot"
 L164    child = 그 pivot 의 downlink
 L173    stack 에 (이 블록, offnum) push                   분할 때 부모를 찾는 단서
 L182    레벨 1 이고 쓰기 모드면 다음(리프)은 BT_WRITE 로
 L186    _bt_relandgetbuf(child)                           부모를 놓고 자식을 잡는다
 L197  루트가 곧 리프였으면 읽기 잠금을 쓰기로 바꾸고 L208 다시 moveright
 L211  return stack                                        리프 레벨 항목은 없다
```

`_bt_search` 는 부모 잠금을 놓은 뒤 자식을 잡는다(L186). 그 사이 자식이 쪼개질 수 있고, 그래서 자식에 도착할 때마다 high key 를 다시 본다. 아래 그림의 페이지 내용은 [10] 의 분할 규칙으로 계산한 것이다. `int4` 기본키에 1, 2, 3, ... 을 차례로 넣어 774 를 넣을 때 두 번째 분할이 일어난다.

```text
 750 을 찾는 백엔드 R 과 774 를 넣는 백엔드 W

 R 이 루트를 읽은 순간 (루트 3, 레벨 1)
   [ -inf -> 1 | 367 -> 2 ]          367 <= 750 이라 블록 2 를 고르고 루트 잠금을 놓는다 (L186)

 R 이 블록 2 의 잠금을 기다리는 동안 W 가 블록 2 를 쪼갠다 ([09] [10] [11])

 메타페이지(0) -> 루트 3
                  [ -inf -> 1 | 367 -> 2 | 733 -> 4 ]
                      |            |            |
                      v            v            v
 레벨 0   [블록 1]           [블록 2]               [블록 4]
          1 .. 366           367 .. 732             733 .. 774
          hikey 367          hikey 733              hikey 없음 (오른쪽 끝)
          next -> 2          next -> 4  -------->   prev -> 2

 R: 블록 2 를 잡는다. 가지고 내려온 정보는 낡은 루트에서 온 것이다
 R: 블록 2 의 high key 733 과 비교 -> 750 > 733                     (L311, cmpval = 1)
 R: btpo_next 로 블록 4 로 옮긴다                                    (L314)
 R: 블록 4 는 오른쪽 끝 -> 멈춘다                                    (L284)
 R 은 루트를 다시 읽지 않고도 750 이 있을 페이지에 닿는다
```

```text
 Lehman-Yao 가 페이지마다 더한 두 가지 (nbtree/README L17-L22)

 high key    그 페이지에 올 수 있는 키의 상한. 오른쪽 끝 페이지에는 없다
             P_HIKEY(오프셋 1) 자리에 둔다. 그래서 데이터는 P_FIRSTKEY(2) 부터
             오른쪽 끝 페이지는 P_HIKEY 부터 (nbtree.h L368-L370)
 right link  btpo_next. 쪼개진 오른쪽 형제로 가는 길

 분할은 항상 "오른쪽으로" 일어나므로, 원래 페이지에 있던 키는
 그 페이지에 남거나 오른쪽 어딘가에 있다 -> high key 만 보면 따라갈 수 있다
```

쓰기 모드 탐색은 길에서 마무리되지 않은 분할(`INCOMPLETE_SPLIT`)을 만나면 먼저 끝낸다(L290-L307). 분할과 부모 삽입 사이에 서버가 죽으면 이 플래그가 남는데, 다음 삽입자가 이렇게 복구한다.

```text
 _bt_moveright 한 바퀴 (L279-L318)

 오른쪽 끝?                         -> 멈춤
 forupdate 이고 INCOMPLETE_SPLIT?   -> 읽기 잠금이면 쓰기로 올리고
                                       _bt_finish_split (부모에 downlink 를 넣는다)
                                       같은 블록을 다시 잡고 처음부터
 죽은 페이지이거나 _bt_compare(key, high key) >= cmpval?
   nextkey = false (삽입)  cmpval 1  -> key > high key 면 오른쪽
   nextkey = true          cmpval 0  -> key >= high key 면 오른쪽
 그 밖                               -> 멈춤
```

## 결과가 쓰이는 곳

```text
 insertstate->buf (쓰기 잠금, 핀)
      --> [06] _bt_check_unique 와 [07] _bt_findinsertloc 가 이 페이지에서 일한다
 stack (BTStack: bts_blkno, bts_offset, bts_parent)
      --> 분할이 나면 [11] _bt_insert_parent 가 _bt_getstackbuf 로 부모를 다시 찾는다
      --> fastpath 면 NULL. 그래서 fastpath 는 분할이 없을 만큼 공간이 있을 때만 쓴다 (L347)
 RelationGetTargetBlock 캐시
      --> [08] _bt_insertonpg 가 오른쪽 끝 리프에 넣고 트리 높이가 2 이상이면 채운다
```

## 다루지 않는 것

`_bt_getroot` 의 메타페이지 캐시와 fast root, 이진 탐색(`_bt_binsrch`, `_bt_compare`)의 비교 규칙, 읽기 전용 스캔의 `_bt_first`, 페이지 삭제로 생기는 죽은 페이지(`P_IGNORE`) 처리는 다루지 않는다.
