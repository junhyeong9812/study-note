# _bt_insertonpg

상위: [nbtree 삽입과 분할](../README.md)

**정해진 페이지에 튜플 하나를 넣는다. 공간이 없으면 페이지를 쪼개고 부모에 downlink 를 넣는 재귀의 시작점이 된다.** 리프 삽입에서 처음 불리고, 분할이 나면 `_bt_insert_parent` 를 거쳐 부모 페이지에 대해 다시 불린다. 그래서 한 번의 `INSERT` 가 루트까지 분할을 올릴 수 있다. 공간이 있으면 크리티컬 섹션 안에서 `PageAddItem` 과 WAL 기록을 함께 한다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L1105-L1437 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1105-L1437))

## 실제 코드

페이지의 성질을 먼저 읽어 둔다. `isroot`, `isonly` 는 분할 뒤 부모를 어떻게 만들지 정하고, `isrightmost` 는 fastpath 캐시를 정한다.

`access` / `nbtree` / `nbtinsert.c` L1105-L1132 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1105-L1132))

```c
// nbtinsert.c L1105-L1132
_bt_insertonpg(Relation rel,
			   Relation heaprel,
			   BTScanInsert itup_key,
			   Buffer buf,
			   Buffer cbuf,
			   BTStack stack,
			   IndexTuple itup,
			   Size itemsz,
			   OffsetNumber newitemoff,
			   int postingoff,
			   bool split_only_page)
{
	Page		page;
	BTPageOpaque opaque;
	bool		isleaf,
				isroot,
				isrightmost,
				isonly;
	IndexTuple	oposting = NULL;
	IndexTuple	origitup = NULL;
	IndexTuple	nposting = NULL;

	page = BufferGetPage(buf);
	opaque = BTPageGetOpaque(page);
	isleaf = P_ISLEAF(opaque);
	isroot = P_ISROOT(opaque);
	isrightmost = P_RIGHTMOST(opaque);
	isonly = P_LEFTMOST(opaque) && P_RIGHTMOST(opaque);
```

새 튜플의 힙 TID 가 기존 posting list 의 TID 범위 안에 떨어지면, 그 posting list 를 먼저 둘로 바꿔 끼운다.

`access` / `nbtree` / `nbtinsert.c` L1159-L1201 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1159-L1201))

```c
// nbtinsert.c L1159-L1201
	if (postingoff != 0)
	{
		// ... (L1161-L1195 생략: posting list 복사와 손상 검사)
		nposting = _bt_swap_posting(itup, oposting, postingoff);
		/* itup now contains rightmost/max TID from oposting */

		/* Alter offset so that newitem goes after posting list */
		newitemoff = OffsetNumberNext(newitemoff);
	}
```

공간이 없으면 쪼갠다. 왼쪽 페이지는 쓰기 잠금을 쥔 채 부모 삽입으로 간다.

`access` / `nbtree` / `nbtinsert.c` L1210-L1242 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1210-L1242))

```c
// nbtinsert.c L1210-L1242
	if (PageGetFreeSpace(page) < itemsz)
	{
		Buffer		rbuf;

		Assert(!split_only_page);

		/* split the buffer into left and right halves */
		rbuf = _bt_split(rel, heaprel, itup_key, buf, cbuf, newitemoff, itemsz,
						 itup, origitup, nposting, postingoff);
		PredicateLockPageSplit(rel,
							   BufferGetBlockNumber(buf),
							   BufferGetBlockNumber(rbuf));

		// ... (L1223-L1240 생략: 주석: 이 시점의 상태(아래 그림))
		_bt_insert_parent(rel, heaprel, buf, rbuf, stack, isroot, isonly);
	}
```

공간이 있으면 넣는다. 부모에 넣는 경우라면 같은 크리티컬 섹션에서 자식의 `INCOMPLETE_SPLIT` 을 지운다.

`access` / `nbtree` / `nbtinsert.c` L1243-L1310 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1243-L1310))

```c
// nbtinsert.c L1243-L1310
	else
	{
		Buffer		metabuf = InvalidBuffer;
		Page		metapg = NULL;
		BTMetaPageData *metad = NULL;
		BlockNumber blockcache;

		// ... (L1250-L1256 생략: 주석: 레벨에 혼자 남은 페이지는 fast root 였을 수 있다)
		if (unlikely(split_only_page))
		{
			Assert(!isleaf);
			Assert(BufferIsValid(cbuf));

			metabuf = _bt_getbuf(rel, BTREE_METAPAGE, BT_WRITE);
			metapg = BufferGetPage(metabuf);
			metad = BTPageGetMeta(metapg);

			if (metad->btm_fastlevel >= opaque->btpo_level)
			{
				/* no update wanted */
				_bt_relbuf(rel, metabuf);
				metabuf = InvalidBuffer;
			}
		}

		/* Do the update.  No ereport(ERROR) until changes are logged */
		START_CRIT_SECTION();

		if (postingoff != 0)
			memcpy(oposting, nposting, MAXALIGN(IndexTupleSize(nposting)));

		if (PageAddItem(page, (Item) itup, itemsz, newitemoff, false,
						false) == InvalidOffsetNumber)
			elog(PANIC, "failed to add new item to block %u in index \"%s\"",
				 BufferGetBlockNumber(buf), RelationGetRelationName(rel));

		MarkBufferDirty(buf);

		if (BufferIsValid(metabuf))
		{
			/* upgrade meta-page if needed */
			if (metad->btm_version < BTREE_NOVAC_VERSION)
				_bt_upgrademetapage(metapg);
			metad->btm_fastroot = BufferGetBlockNumber(buf);
			metad->btm_fastlevel = opaque->btpo_level;
			MarkBufferDirty(metabuf);
		}

		/*
		 * Clear INCOMPLETE_SPLIT flag on child if inserting the new item
		 * finishes a split
		 */
		if (!isleaf)
		{
			Page		cpage = BufferGetPage(cbuf);
			BTPageOpaque cpageop = BTPageGetOpaque(cpage);

			Assert(P_INCOMPLETE_SPLIT(cpageop));
			cpageop->btpo_flags &= ~BTP_INCOMPLETE_SPLIT;
			MarkBufferDirty(cbuf);
		}

```

WAL 레코드 종류를 고르고 기록한 뒤, 오른쪽 끝 리프면 다음 삽입을 위해 블록 번호를 캐시한다.

`access` / `nbtree` / `nbtinsert.c` L1311-L1437 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L1311-L1437))

```c
// nbtinsert.c L1311-L1437
		/* XLOG stuff */
		if (RelationNeedsWAL(rel))
		{
			xl_btree_insert xlrec;
			xl_btree_metadata xlmeta;
			uint8		xlinfo;
			XLogRecPtr	recptr;
			uint16		upostingoff;

			xlrec.offnum = newitemoff;

			XLogBeginInsert();
			XLogRegisterData(&xlrec, SizeOfBtreeInsert);

			if (isleaf && postingoff == 0)
			{
				/* Simple leaf insert */
				xlinfo = XLOG_BTREE_INSERT_LEAF;
			}
			else if (postingoff != 0)
			{
				/*
				 * Leaf insert with posting list split.  Must include
				 * postingoff field before newitem/orignewitem.
				 */
				Assert(isleaf);
				xlinfo = XLOG_BTREE_INSERT_POST;
			}
			else
			{
				/* Internal page insert, which finishes a split on cbuf */
				xlinfo = XLOG_BTREE_INSERT_UPPER;
				XLogRegisterBuffer(1, cbuf, REGBUF_STANDARD);

				if (BufferIsValid(metabuf))
				{
					/* Actually, it's an internal page insert + meta update */
					xlinfo = XLOG_BTREE_INSERT_META;

				// ... (L1350-L1362 생략: 메타페이지 필드 복사)
				}
			}

			XLogRegisterBuffer(0, buf, REGBUF_STANDARD);
			if (postingoff == 0)
			{
				/* Just log itup from caller */
				XLogRegisterBufData(0, itup, IndexTupleSize(itup));
			}
			else
// ... (L1373-L1387 생략: posting 분할 때는 원래 튜플과 postingoff 를 기록)

			recptr = XLogInsert(RM_BTREE_ID, xlinfo);

			if (BufferIsValid(metabuf))
				PageSetLSN(metapg, recptr);
			if (!isleaf)
				PageSetLSN(BufferGetPage(cbuf), recptr);

			PageSetLSN(page, recptr);
		}

		END_CRIT_SECTION();

		/* Release subsidiary buffers */
		if (BufferIsValid(metabuf))
			_bt_relbuf(rel, metabuf);
		if (!isleaf)
			_bt_relbuf(rel, cbuf);

		/*
		 * Cache the block number if this is the rightmost leaf page.  Cache
		 * may be used by a future inserter within _bt_search_insert().
		 */
		blockcache = InvalidBlockNumber;
		if (isrightmost && isleaf && !isroot)
			blockcache = BufferGetBlockNumber(buf);

		/* Release buffer for insertion target block */
		_bt_relbuf(rel, buf);

		/*
		 * If we decided to cache the insertion target block before releasing
		 * its buffer lock, then cache it now.  Check the height of the tree
		 * first, though.  We don't go for the optimization with small
		 * indexes.  Defer final check to this point to ensure that we don't
		 * call _bt_getrootheight while holding a buffer lock.
		 */
		if (BlockNumberIsValid(blockcache) &&
			_bt_getrootheight(rel) >= BTREE_FASTPATH_MIN_LEVEL)
			RelationSetTargetBlock(rel, blockcache);
	}

	/* be tidy */
	if (postingoff != 0)
	{
		/* itup is actually a modified copy of caller's original */
		pfree(nposting);
		pfree(itup);
	}
}
```

## 동작 흐름

```text
 L1129 isleaf, isroot, isrightmost, isonly (왼쪽 끝이면서 오른쪽 끝)
 L1159 postingoff != 0 -> _bt_swap_posting (L1196), newitemoff++

 L1210 PageGetFreeSpace(page) < itemsz ?
   예  L1217  rbuf = [09] _bt_split(...)              새 튜플까지 넣고 둘로 나눈다
       L1219  PredicateLockPageSplit                  SSI 술어 잠금을 오른쪽에도 복사
       L1241  [11] _bt_insert_parent(buf, rbuf, stack, isroot, isonly)
   아니오
       L1257  split_only_page 면 메타페이지 쓰기 잠금 (fast root 갱신 후보)
       L1275  START_CRIT_SECTION
       L1280    PageAddItem(page, itup, newitemoff)    실패하면 PANIC
       L1292    필요하면 btm_fastroot 갱신
       L1301    내부 페이지 삽입이면 자식(cbuf)의 INCOMPLETE_SPLIT 해제
       L1312    WAL: XLogInsert(RM_BTREE_ID, xlinfo)   PageSetLSN
       L1399  END_CRIT_SECTION
       L1402  메타, 자식 버퍼 해제
       L1412  오른쪽 끝 리프이고 루트가 아니면 블록 번호를 기억
       L1416  대상 버퍼 해제
       L1425  트리 높이 >= 2 (BTREE_FASTPATH_MIN_LEVEL) 이면 RelationSetTargetBlock
```

공간 판정은 `PageGetFreeSpace` 가 라인 포인터 4바이트를 미리 빼 준 값과 MAXALIGN 된 튜플 크기를 비교한다(L1206-L1208 주석). `int4` 기본키 루트 리프에서 계산하면 407 개째까지 들어가고 408 번째에서 쪼개진다.

```text
 루트이자 리프인 블록 1, 오른쪽 끝이라 high key 없음
 (8KB 페이지, 헤더 24, special 16, 항목 하나 = 튜플 16 + 라인 포인터 4)

 항목 n 개일 때  pd_lower = 24 + 4n,  pd_upper = 8176 - 16n
 PageGetFreeSpace = (pd_upper - pd_lower) - 4 = 8148 - 20n     (bufpage.c L915-L919)

 n = 406   8148 - 8120 = 28  >= 16   들어간다 -> n = 407
 n = 407   8148 - 8140 =  8  <  16   408 번째 키는 L1217 _bt_split 으로
```

`xlinfo` 는 무엇을 넣었는가로 정해진다. 분할은 이 함수가 아니라 [09] 가 따로 `XLOG_BTREE_SPLIT_L` 또는 `_R` 로 기록한다.

```text
 WAL 레코드 (L1325-L1364)

 isleaf, postingoff == 0           XLOG_BTREE_INSERT_LEAF   buf 0 = 리프, 새 튜플
 postingoff != 0                   XLOG_BTREE_INSERT_POST   + postingoff, 원래 튜플
 내부 페이지                       XLOG_BTREE_INSERT_UPPER  + buf 1 = 자식 (플래그 해제)
 내부 페이지 + fast root 갱신      XLOG_BTREE_INSERT_META   + buf 2 = 메타페이지
```

분할이 위로 번지는 모양이다. 같은 함수가 레벨마다 다른 인자로 다시 불린다.

```text
 리프에서 시작한 분할이 루트까지 오르는 재귀

 [04] _bt_doinsert
   _bt_insertonpg(리프 L, cbuf = 없음, stack = 리프의 부모 자리)
     공간 없음 -> _bt_split(L) -> L', R
     _bt_insert_parent(L', R, stack)
       부모 P 를 찾아 쓰기 잠금 (_bt_getstackbuf)
       _bt_insertonpg(P, cbuf = L', itup = [L' 의 high key -> R], stack->bts_parent)
         공간 있음 -> P 에 넣고 L' 의 INCOMPLETE_SPLIT 해제, L' 와 P 해제   (끝)
         공간 없음 -> _bt_split(P) -> P', Q   (L' 의 플래그도 이 분할 안에서 해제)
                      _bt_insert_parent(P', Q, ...)
                        ... 루트였다면 _bt_newlevel 로 한 층 올린다
```

## 결과가 쓰이는 곳

```text
 페이지의 새 항목과 WAL 레코드
      --> 복구 때 btree_redo 가 같은 변경을 다시 한다
 RelationSetTargetBlock(blockcache)
      --> 다음 [05] _bt_search_insert 의 fastpath. 오름차순 키 삽입이 루트부터 내려가지 않는다
 메타페이지 btm_fastroot
      --> _bt_getroot 가 탐색을 시작할 페이지. 위 레벨들이 한 페이지씩뿐이면 아래쪽을 가리킨다
```

## 다루지 않는 것

posting list 분할(`_bt_swap_posting`)의 TID 재배치, SSI 의 `PredicateLockPageSplit`, fast root 의 정의와 갱신 규칙, 복구 쪽 `btree_redo` 는 다루지 않는다.
