# _bt_newlevel

상위: [nbtree 삽입과 분할](../README.md)

**루트가 쪼개졌을 때 그 위에 새 루트 페이지를 만들어 트리를 한 층 높인다.** 새 루트에는 항목이 둘이다. 왼쪽(옛 루트)을 가리키는 "음의 무한대" 항목과, 왼쪽의 high key 를 복사해 오른쪽을 가리키는 항목. 그리고 메타페이지의 루트 포인터를 새 블록으로 바꾼다. 옛 루트는 블록 번호를 그대로 지닌 채 한 레벨 아래의 왼쪽 끝 페이지가 된다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L2444-L2609 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2444-L2609))

## 실제 코드

머리 주석이 잠금 순서를 설명한다. 읽는 쪽은 메타페이지를 놓은 뒤 루트를 잡고, 쓰는 쪽은 루트를 잡은 뒤 메타페이지를 잡으므로 대기 그래프에 고리가 생기지 않는다.

`access` / `nbtree` / `nbtinsert.c` L2425-L2443 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2425-L2443))

```c
// nbtinsert.c L2425-L2443
/*
 *	_bt_newlevel() -- Create a new level above root page.
 *
 *		We've just split the old root page and need to create a new one.
 *		In order to do this, we add a new root page to the file, then lock
 *		the metadata page and update it.  This is guaranteed to be deadlock-
 *		free, because all readers release their locks on the metadata page
 *		before trying to lock the root, and all writers lock the root before
 *		trying to lock the metadata page.  We have a write lock on the old
 *		root page, so we have not introduced any cycles into the waits-for
 *		graph.
 *
 *		On entry, lbuf (the old root) and rbuf (its new peer) are write-
 *		locked. On exit, a new root page exists with entries for the
 *		two new children, metapage is updated and unlocked/unpinned.
 *		The new root buffer is returned to caller which has to unlock/unpin
 *		lbuf, rbuf & rootbuf.
 */
static Buffer
```

새 루트 블록과 메타페이지를 잡고, 두 항목을 만든다.

`access` / `nbtree` / `nbtinsert.c` L2444-L2498 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2444-L2498))

```c
// nbtinsert.c L2444-L2498
_bt_newlevel(Relation rel, Relation heaprel, Buffer lbuf, Buffer rbuf)
{
	Buffer		rootbuf;
	Page		lpage,
				rootpage;
	BlockNumber lbkno,
				rbkno;
	BlockNumber rootblknum;
	BTPageOpaque rootopaque;
	BTPageOpaque lopaque;
	ItemId		itemid;
	IndexTuple	item;
	IndexTuple	left_item;
	Size		left_item_sz;
	IndexTuple	right_item;
	Size		right_item_sz;
	Buffer		metabuf;
	Page		metapg;
	BTMetaPageData *metad;

	lbkno = BufferGetBlockNumber(lbuf);
	rbkno = BufferGetBlockNumber(rbuf);
	lpage = BufferGetPage(lbuf);
	lopaque = BTPageGetOpaque(lpage);

	/* get a new root page */
	rootbuf = _bt_allocbuf(rel, heaprel);
	rootpage = BufferGetPage(rootbuf);
	rootblknum = BufferGetBlockNumber(rootbuf);

	/* acquire lock on the metapage */
	metabuf = _bt_getbuf(rel, BTREE_METAPAGE, BT_WRITE);
	metapg = BufferGetPage(metabuf);
	metad = BTPageGetMeta(metapg);

	/*
	 * Create downlink item for left page (old root).  The key value used is
	 * "minus infinity", a sentinel value that's reliably less than any real
	 * key value that could appear in the left page.
	 */
	left_item_sz = sizeof(IndexTupleData);
	left_item = (IndexTuple) palloc(left_item_sz);
	left_item->t_info = left_item_sz;
	BTreeTupleSetDownLink(left_item, lbkno);
	BTreeTupleSetNAtts(left_item, 0, false);

	/*
	 * Create downlink item for right page.  The key for it is obtained from
	 * the "high key" position in the left page.
	 */
	itemid = PageGetItemId(lpage, P_HIKEY);
	right_item_sz = ItemIdGetLength(itemid);
	item = (IndexTuple) PageGetItem(lpage, itemid);
	right_item = CopyIndexTuple(item);
	BTreeTupleSetDownLink(right_item, rbkno);
```

크리티컬 섹션에서 루트를 채우고, 메타페이지를 바꾸고, 왼쪽 자식의 `INCOMPLETE_SPLIT` 을 지운 뒤 한 WAL 레코드로 남긴다.

`access` / `nbtree` / `nbtinsert.c` L2500-L2609 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2500-L2609))

```c
// nbtinsert.c L2500-L2609
	/* NO EREPORT(ERROR) from here till newroot op is logged */
	START_CRIT_SECTION();

	/* upgrade metapage if needed */
	if (metad->btm_version < BTREE_NOVAC_VERSION)
		_bt_upgrademetapage(metapg);

	/* set btree special data */
	rootopaque = BTPageGetOpaque(rootpage);
	rootopaque->btpo_prev = rootopaque->btpo_next = P_NONE;
	rootopaque->btpo_flags = BTP_ROOT;
	rootopaque->btpo_level =
		(BTPageGetOpaque(lpage))->btpo_level + 1;
	rootopaque->btpo_cycleid = 0;

	/* update metapage data */
	metad->btm_root = rootblknum;
	metad->btm_level = rootopaque->btpo_level;
	metad->btm_fastroot = rootblknum;
	metad->btm_fastlevel = rootopaque->btpo_level;

	// ... (L2521-L2528 생략: 주석: 루트는 오른쪽 끝이라 high key 가 없다)
	Assert(BTreeTupleGetNAtts(left_item, rel) == 0);
	if (PageAddItem(rootpage, (Item) left_item, left_item_sz, P_HIKEY,
					false, false) == InvalidOffsetNumber)
		elog(PANIC, "failed to add leftkey to new root page"
			 " while splitting block %u of index \"%s\"",
			 BufferGetBlockNumber(lbuf), RelationGetRelationName(rel));

	/*
	 * insert the right page pointer into the new root page.
	 */
	Assert(BTreeTupleGetNAtts(right_item, rel) > 0);
	Assert(BTreeTupleGetNAtts(right_item, rel) <=
		   IndexRelationGetNumberOfKeyAttributes(rel));
	if (PageAddItem(rootpage, (Item) right_item, right_item_sz, P_FIRSTKEY,
					false, false) == InvalidOffsetNumber)
		elog(PANIC, "failed to add rightkey to new root page"
			 " while splitting block %u of index \"%s\"",
			 BufferGetBlockNumber(lbuf), RelationGetRelationName(rel));

	/* Clear the incomplete-split flag in the left child */
	Assert(P_INCOMPLETE_SPLIT(lopaque));
	lopaque->btpo_flags &= ~BTP_INCOMPLETE_SPLIT;
	MarkBufferDirty(lbuf);

	MarkBufferDirty(rootbuf);
	MarkBufferDirty(metabuf);

	/* XLOG stuff */
	if (RelationNeedsWAL(rel))
	{
		xl_btree_newroot xlrec;
		XLogRecPtr	recptr;
		xl_btree_metadata md;

		xlrec.rootblk = rootblknum;
		xlrec.level = metad->btm_level;

		XLogBeginInsert();
		XLogRegisterData(&xlrec, SizeOfBtreeNewroot);

		XLogRegisterBuffer(0, rootbuf, REGBUF_WILL_INIT);
		XLogRegisterBuffer(1, lbuf, REGBUF_STANDARD);
		XLogRegisterBuffer(2, metabuf, REGBUF_WILL_INIT | REGBUF_STANDARD);

		Assert(metad->btm_version >= BTREE_NOVAC_VERSION);
		md.version = metad->btm_version;
		md.root = rootblknum;
		md.level = metad->btm_level;
		md.fastroot = rootblknum;
		md.fastlevel = metad->btm_level;
		md.last_cleanup_num_delpages = metad->btm_last_cleanup_num_delpages;
		md.allequalimage = metad->btm_allequalimage;

		XLogRegisterBufData(2, &md, sizeof(xl_btree_metadata));

		// ... (L2584-L2587 생략: 주석)
		XLogRegisterBufData(0,
							(char *) rootpage + ((PageHeader) rootpage)->pd_upper,
							((PageHeader) rootpage)->pd_special -
							((PageHeader) rootpage)->pd_upper);

		recptr = XLogInsert(RM_BTREE_ID, XLOG_BTREE_NEWROOT);

		PageSetLSN(lpage, recptr);
		PageSetLSN(rootpage, recptr);
		PageSetLSN(metapg, recptr);
	}

	END_CRIT_SECTION();

	/* done with metapage */
	_bt_relbuf(rel, metabuf);

	pfree(left_item);
	pfree(right_item);

	return rootbuf;
}
```

[11] 에서 불린 뒤 세 버퍼를 놓는 곳이다.

`access` / `nbtree` / `nbtinsert.c` L2122-L2134 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L2122-L2134))

```c
// nbtinsert.c L2122-L2134
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
```

## 동작 흐름

```text
 L2470 rootbuf = _bt_allocbuf                        새 블록 (FSM 재사용 또는 relation 확장)
 L2475 메타페이지 BT_WRITE                            옛 루트(lbuf)는 이미 쓰기 잠금
 L2484 left_item = 헤더만 있는 튜플, downlink = 옛 루트, 키 열 0 개 (음의 무한대)
 L2497 right_item = 옛 루트의 high key 복사, downlink = 새 오른쪽 페이지
 L2501 START_CRIT_SECTION
 L2509   루트: prev = next = P_NONE, flags = BTP_ROOT, level = 옛 루트 레벨 + 1
 L2516   메타: btm_root = btm_fastroot = 새 블록, btm_level = btm_fastlevel = 새 레벨
 L2530   left_item  -> P_HIKEY(1)
 L2542   right_item -> P_FIRSTKEY(2)
 L2550   옛 루트의 INCOMPLETE_SPLIT 해제
 L2593   XLogInsert(XLOG_BTREE_NEWROOT)               새 루트 내용 + 메타 + 옛 루트 참조
 L2600 END_CRIT_SECTION
 L2603 메타페이지 해제, L2608 return rootbuf          [11] 이 루트, 오른쪽, 왼쪽 순으로 놓는다
```

아래는 [09] 의 그림에 이어지는 루트 승격이다. 빈 테이블에 만든 `int4` 기본키 인덱스는 첫 삽입 때 `_bt_getroot` 가 블록 1 을 루트이자 리프로 만든다(nbtpage.c L443-L463). 키 408 이 그 페이지를 쪼개면 블록 2 가 오른쪽이 되고, 여기서 블록 3 이 새 루트가 된다. 새 인덱스라 FSM 이 비어 있으면 `_bt_allocbuf` 는 relation 을 한 블록씩 늘린다(nbtpage.c L978).

```text
 전 (408 을 넣기 직전)

 메타(0)  btm_root = 1, btm_level = 0
            |
            v
          [블록 1  LEAF | ROOT]   1 .. 407                 오른쪽 끝, high key 없음

 [09] _bt_split 직후 (아직 루트 없음, 블록 1 은 ROOT 플래그가 빠지고 INCOMPLETE_SPLIT)

 메타(0)  btm_root = 1  (아직 옛 값)
            |
            v
          [블록 1  LEAF]  hikey 367 | 1 .. 366   --next-->   [블록 2  LEAF]  367 .. 408

 _bt_newlevel 후

 메타(0)  btm_root = 3, btm_level = 1, btm_fastroot = 3, btm_fastlevel = 1
            |
            v
          [블록 3  ROOT, level 1]                          오른쪽 끝, high key 없음
            off 1  ( -inf ) -> 1                           키 열 0 개
            off 2  ( 367  ) -> 2                           블록 1 의 high key 복사
             |              |
             v              v
          [블록 1  LEAF]  --next-->  [블록 2  LEAF]
          hikey 367                  hikey 없음
          1 .. 366                   367 .. 408
```

이 순간 메타페이지를 아직 옛 값(루트 = 1)으로 읽은 백엔드도 길을 잃지 않는다. 옛 루트 블록 1 은 이제 리프지만 high key 와 right link 를 가지므로, 367 이상을 찾는 탐색은 [05] 의 `_bt_moveright` 로 블록 2 에 간다. 소스 README 가 "루트는 다른 방식으로 특별하지 않다"고 적은 이유다(nbtree/README L112-L124).

```text
 높이가 늘어나는 순서 (오름차순 int4 기본키, 분할 규칙대로라면)

 키 수  높이  루트  사건
 1      0     1     _bt_getroot 가 블록 1 을 리프이자 루트로 생성
 408    1     3     블록 1 분할, 블록 3 이 새 루트
 774    1     3     블록 2 분할, 루트에 (733 -> 4)

 그 뒤로도 오른쪽 끝 리프가 찰 때마다 같은 계산으로 366 개를 왼쪽에 남기고 쪼개진다
 루트에 downlink 가 쌓여 루트 자신이 꽉 차면 [08] -> [09] -> [11] -> [12] 로 높이 2 가 된다
```

## 결과가 쓰이는 곳

```text
 메타페이지 btm_root, btm_level
      --> 이후 모든 _bt_getroot 가 새 루트에서 출발한다 (백엔드는 메타 내용을 relcache 에 캐시)
 btm_fastroot
      --> 탐색 시작점. 위 레벨들이 한 페이지씩뿐이면 아래 레벨을 가리키도록 [08] 이 고친다
 트리 높이
      --> 2 이상이 되면 [08] 이 오른쪽 끝 리프를 RelationSetTargetBlock 으로 캐시해 fastpath 가 켜진다
```

## 다루지 않는 것

메타페이지 구조(`BTMetaPageData`)와 버전 업그레이드(`_bt_upgrademetapage`), relcache 의 메타 캐시(`rd_amcache`), fast root 가 진짜 루트와 갈라지는 경우, 복구 쪽 `btree_xlog_newroot` 는 다루지 않는다.
