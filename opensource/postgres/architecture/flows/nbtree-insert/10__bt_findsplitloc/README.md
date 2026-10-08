# _bt_findsplitloc

상위: [nbtree 삽입과 분할](../README.md)

**분할 지점을 고른다.** 새 튜플이 이미 페이지에 있다고 치고 항목 사이의 모든 지점을 후보로 적은 뒤, 양쪽 남는 공간이 얼마나 균형 잡혔는지로 정렬하고, 그 앞쪽 일부 안에서 왼쪽 high key 가 가장 짧아지는 지점을 고른다. 오른쪽 끝 페이지에서는 균형 대신 왼쪽을 fillfactor(기본 90%)만큼 채우도록 기울인다. 오름차순 키 삽입이 반쯤 빈 페이지를 남기지 않게 하기 위해서다(L94-L99 주석).

## 위치

`access` / `nbtree` / `nbtsplitloc.c` L129-L428 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L129-L428))

함께 다루는 함수 (같은 파일):

- `_bt_recsplitloc`: `access` / `nbtree` / `nbtsplitloc.c` L465-L559 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L465-L559))
- `_bt_deltasortsplits`: `access` / `nbtree` / `nbtsplitloc.c` L566-L588 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L566-L588))
- `_bt_bestsplitloc`: `access` / `nbtree` / `nbtsplitloc.c` L788-L847 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L788-L847))

## 실제 코드

페이지에서 항목이 쓸 수 있는 공간과 이미 쓴 공간을 센다. 오른쪽 페이지는 원래 high key 를 물려받으니 그만큼 덜 쓸 수 있다.

`access` / `nbtree` / `nbtsplitloc.c` L155-L198 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L155-L198))

```c
// nbtsplitloc.c L155-L198
	maxoff = PageGetMaxOffsetNumber(origpage);

	/* Total free space available on a btree page, after fixed overhead */
	leftspace = rightspace =
		PageGetPageSize(origpage) - SizeOfPageHeaderData -
		MAXALIGN(sizeof(BTPageOpaqueData));

	/* The right page will have the same high key as the old page */
	if (!P_RIGHTMOST(opaque))
	{
		itemid = PageGetItemId(origpage, P_HIKEY);
		rightspace -= (int) (MAXALIGN(ItemIdGetLength(itemid)) +
							 sizeof(ItemIdData));
	}

	/* Count up total space in data items before actually scanning 'em */
	olddataitemstotal = rightspace - (int) PageGetExactFreeSpace(origpage);
	leaffillfactor = BTGetFillFactor(rel);

	/* Passed-in newitemsz is MAXALIGNED but does not include line pointer */
	newitemsz += sizeof(ItemIdData);
	state.rel = rel;
	state.origpage = origpage;
	state.newitem = newitem;
	state.newitemsz = newitemsz;
	state.is_leaf = P_ISLEAF(opaque);
	state.is_rightmost = P_RIGHTMOST(opaque);
	state.leftspace = leftspace;
	state.rightspace = rightspace;
	state.olddataitemstotal = olddataitemstotal;
	state.minfirstrightsz = SIZE_MAX;
	state.newitemoff = newitemoff;

	/* newitem cannot be a posting list item */
	Assert(!BTreeTupleIsPosting(newitem));

	/*
	 * nsplits should never exceed maxoff because there will be at most as
	 * many candidate split points as there are points _between_ tuples, once
	 * you imagine that the new item is already on the original page (the
	 * final number of splits may be slightly lower because not all points
	 * between tuples will be legal).
	 */
	state.maxsplits = maxoff;
```

항목 사이마다 후보를 하나씩 기록한다. 새 튜플이 들어갈 자리에서는 "새 튜플 앞에서 자르기"와 "새 튜플 뒤에서 자르기" 두 후보가 생긴다.

`access` / `nbtree` / `nbtsplitloc.c` L200-L262 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L200-L262))

```c
// nbtsplitloc.c L200-L262
	state.nsplits = 0;

	/*
	 * Scan through the data items and calculate space usage for a split at
	 * each possible position
	 */
	olddataitemstoleft = 0;

	for (offnum = P_FIRSTDATAKEY(opaque);
		 offnum <= maxoff;
		 offnum = OffsetNumberNext(offnum))
	{
		Size		itemsz;

		itemid = PageGetItemId(origpage, offnum);
		itemsz = MAXALIGN(ItemIdGetLength(itemid)) + sizeof(ItemIdData);

		/*
		 * When item offset number is not newitemoff, neither side of the
		 * split can be newitem.  Record a split after the previous data item
		 * from original page, but before the current data item from original
		 * page. (_bt_recsplitloc() will reject the split when there are no
		 * previous items, which we rely on.)
		 */
		if (offnum < newitemoff)
			_bt_recsplitloc(&state, offnum, false, olddataitemstoleft, itemsz);
		else if (offnum > newitemoff)
			_bt_recsplitloc(&state, offnum, true, olddataitemstoleft, itemsz);
		else
		{
			/*
			 * Record a split after all "offnum < newitemoff" original page
			 * data items, but before newitem
			 */
			_bt_recsplitloc(&state, offnum, false, olddataitemstoleft, itemsz);

			/*
			 * Record a split after newitem, but before data item from
			 * original page at offset newitemoff/current offset
			 */
			_bt_recsplitloc(&state, offnum, true, olddataitemstoleft, itemsz);
		}

		olddataitemstoleft += itemsz;
	}

	/*
	 * Record a split after all original page data items, but before newitem.
	 * (Though only when it's possible that newitem will end up alone on new
	 * right page.)
	 */
	Assert(olddataitemstoleft == olddataitemstotal);
	if (newitemoff > maxoff)
		_bt_recsplitloc(&state, newitemoff, false, olddataitemstotal, 0);

	/*
	 * I believe it is not possible to fail to find a feasible split, but just
	 * in case ...
	 */
	if (state.nsplits == 0)
		elog(ERROR, "could not find a feasible split point for index \"%s\"",
			 RelationGetRelationName(rel));

```

페이지 종류에 따라 fillfactor 를 정한다.

`access` / `nbtree` / `nbtsplitloc.c` L263-L345 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L263-L345))

```c
// nbtsplitloc.c L263-L345
	// ... (L263-L279 생략: 주석: 기본 전략은 균형 우선, suffix truncation 은 그 다음)
	if (!state.is_leaf)
	{
		/* fillfactormult only used on rightmost page */
		usemult = state.is_rightmost;
		fillfactormult = BTREE_NONLEAF_FILLFACTOR / 100.0;
	}
	else if (state.is_rightmost)
	{
		/* Rightmost leaf page --  fillfactormult always used */
		usemult = true;
		fillfactormult = leaffillfactor / 100.0;
	}
	else if (_bt_afternewitemoff(&state, maxoff, leaffillfactor, &usemult))
	{
		/*
		 * New item inserted at rightmost point among a localized grouping on
		 * a leaf page -- apply "split after new item" optimization, either by
		 * applying leaf fillfactor multiplier, or by choosing the exact split
		 * point that leaves newitem as lastleft. (usemult is set for us.)
		 */
		if (usemult)
		{
			/* fillfactormult should be set based on leaf fillfactor */
			fillfactormult = leaffillfactor / 100.0;
		}
		else
		{
			/* find precise split point after newitemoff */
			for (int i = 0; i < state.nsplits; i++)
			{
				SplitPoint *split = state.splits + i;

				if (split->newitemonleft &&
					newitemoff == split->firstrightoff)
				{
					pfree(state.splits);
					*newitemonleft = true;
					return newitemoff;
				}
			}

			/*
			 * Cannot legally split after newitemoff; proceed with split
			 * without using fillfactor multiplier.  This is defensive, and
			 * should never be needed in practice.
			 */
			fillfactormult = 0.50;
		}
	}
	else
	{
		/* Other leaf page.  50:50 page split. */
		usemult = false;
		/* fillfactormult not used, but be tidy */
		fillfactormult = 0.50;
	}

	/*
	 * Save leftmost and rightmost splits for page before original ordinal
	 * sort order is lost by delta/fillfactormult sort
	 */
	leftpage = state.splits[0];
	rightpage = state.splits[state.nsplits - 1];

	/* Give split points a fillfactormult-wise delta, and sort on deltas */
	_bt_deltasortsplits(&state, fillfactormult, usemult);
```

정렬된 후보 앞쪽 몇 개(interval) 안에서 벌점이 가장 낮은 지점을 고른다. 중복이 많으면 전략을 바꾼다.

`access` / `nbtree` / `nbtsplitloc.c` L347-L428 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L347-L428))

```c
// nbtsplitloc.c L347-L428
	/* Determine split interval for default strategy */
	state.interval = _bt_defaultinterval(&state);

	// ... (L350-L363 생략: 주석)
	perfectpenalty = _bt_strategy(&state, &leftpage, &rightpage, &strategy);

	if (strategy == SPLIT_DEFAULT)
	{
		/*
		 * Default strategy worked out (always works out with internal page).
		 * Original split interval still stands.
		 */
	}

	// ... (L374-L396 생략: 주석: many duplicates 와 single value 전략)
	else if (strategy == SPLIT_MANY_DUPLICATES)
	{
		Assert(state.is_leaf);
		/* Shouldn't try to truncate away extra user attributes */
		Assert(perfectpenalty ==
			   IndexRelationGetNumberOfKeyAttributes(state.rel));
		/* No need to resort splits -- no change in fillfactormult/deltas */
		state.interval = state.nsplits;
	}
	else if (strategy == SPLIT_SINGLE_VALUE)
	{
		Assert(state.is_leaf);
		/* Split near the end of the page */
		usemult = true;
		fillfactormult = BTREE_SINGLEVAL_FILLFACTOR / 100.0;
		/* Resort split points with new delta */
		_bt_deltasortsplits(&state, fillfactormult, usemult);
		/* Appending a heap TID is unavoidable, so interval of 1 is fine */
		state.interval = 1;
	}

	/*
	 * Search among acceptable split points (using final split interval) for
	 * the entry that has the lowest penalty, and is therefore expected to
	 * maximize fan-out.  Sets *newitemonleft for us.
	 */
	firstrightoff = _bt_bestsplitloc(&state, perfectpenalty, newitemonleft,
									 strategy);
	pfree(state.splits);

	return firstrightoff;
}
```

후보 하나의 양쪽 남는 공간을 계산하는 곳이다. 리프에서는 왼쪽 high key 에 힙 TID 가 붙는다고 비관적으로 가정한다(L500-L522 주석).

`access` / `nbtree` / `nbtsplitloc.c` L465-L559 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L465-L559))

```c
// nbtsplitloc.c L465-L559
	if (newitemisfirstright)
		firstrightsz = state->newitemsz;
	else
	{
		firstrightsz = firstrightofforigpagetuplesz;

		// ... (L471-L480 생략: 주석: posting list 크기 보정)
		if (state->is_leaf && firstrightsz > 64)
		{
			ItemId		itemid;
			IndexTuple	newhighkey;

			itemid = PageGetItemId(state->origpage, firstrightoff);
			newhighkey = (IndexTuple) PageGetItem(state->origpage, itemid);

			if (BTreeTupleIsPosting(newhighkey))
				postingsz = IndexTupleSize(newhighkey) -
					BTreeTupleGetPostingOffset(newhighkey);
		}
	}

	/* Account for all the old tuples */
	leftfree = state->leftspace - olddataitemstoleft;
	rightfree = state->rightspace -
		(state->olddataitemstotal - olddataitemstoleft);

	// ... (L500-L522 생략: 주석: 왼쪽 high key 를 비관적으로 센다)
	if (state->is_leaf)
		leftfree -= (int16) (firstrightsz +
							 MAXALIGN(sizeof(ItemPointerData)) -
							 postingsz);
	else
		leftfree -= (int16) firstrightsz;

	/* account for the new item */
	if (newitemonleft)
		leftfree -= (int16) state->newitemsz;
	else
		rightfree -= (int16) state->newitemsz;

	/*
	 * If we are not on the leaf level, we will be able to discard the key
	 * data from the first item that winds up on the right page.
	 */
	if (!state->is_leaf)
		rightfree += (int16) firstrightsz -
			(int16) (MAXALIGN(sizeof(IndexTupleData)) + sizeof(ItemIdData));

	/* Record split if legal */
	if (leftfree >= 0 && rightfree >= 0)
	{
		Assert(state->nsplits < state->maxsplits);

		/* Determine smallest firstright tuple size among legal splits */
		state->minfirstrightsz = Min(state->minfirstrightsz, firstrightsz);

		state->splits[state->nsplits].curdelta = 0;
		state->splits[state->nsplits].leftfree = leftfree;
		state->splits[state->nsplits].rightfree = rightfree;
		state->splits[state->nsplits].firstrightoff = firstrightoff;
		state->splits[state->nsplits].newitemonleft = newitemonleft;
		state->nsplits++;
	}
}
```

fillfactor 를 쓸 때는 두 쪽 공간에 가중치를 주어 차이를 잰다.

`access` / `nbtree` / `nbtsplitloc.c` L566-L588 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L566-L588))

```c
// nbtsplitloc.c L566-L588
_bt_deltasortsplits(FindSplitData *state, double fillfactormult,
					bool usemult)
{
	for (int i = 0; i < state->nsplits; i++)
	{
		SplitPoint *split = state->splits + i;
		int16		delta;

		if (usemult)
			delta = fillfactormult * split->leftfree -
				(1.0 - fillfactormult) * split->rightfree;
		else
			delta = split->leftfree - split->rightfree;

		if (delta < 0)
			delta = -delta;

		/* Save delta */
		split->curdelta = delta;
	}

	qsort(state->splits, state->nsplits, sizeof(SplitPoint), _bt_splitcmp);
}
```

벌점 순회와, 내림차순 삽입이 같은 지점을 계속 쪼개는 병을 막는 예외다.

`access` / `nbtree` / `nbtsplitloc.c` L788-L847 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtsplitloc.c#L788-L847))

```c
// nbtsplitloc.c L788-L847
_bt_bestsplitloc(FindSplitData *state, int perfectpenalty,
				 bool *newitemonleft, FindSplitStrat strategy)
{
	int			bestpenalty,
				lowsplit;
	int			highsplit = Min(state->interval, state->nsplits);
	SplitPoint *final;

	bestpenalty = INT_MAX;
	lowsplit = 0;
	for (int i = lowsplit; i < highsplit; i++)
	{
		int			penalty;

		penalty = _bt_split_penalty(state, state->splits + i);

		if (penalty < bestpenalty)
		{
			bestpenalty = penalty;
			lowsplit = i;
		}

		if (penalty <= perfectpenalty)
			break;
	}

	final = &state->splits[lowsplit];

	// ... (L816-L831 생략: 주석: many duplicates 의 함정 예시)
	if (strategy == SPLIT_MANY_DUPLICATES && !state->is_rightmost &&
		!final->newitemonleft && final->firstrightoff >= state->newitemoff &&
		final->firstrightoff < state->newitemoff + 9)
	{
		/*
		 * Avoid the problem by performing a 50:50 split when the new item is
		 * just to the right of the would-be "many duplicates" split point.
		 * (Note that the test used for an insert that is "just to the right"
		 * of the split point is conservative.)
		 */
		final = &state->splits[0];
	}

	*newitemonleft = final->newitemonleft;
	return final->firstrightoff;
}
```

## 동작 흐름

```text
 L158  leftspace = rightspace = 페이지 - 헤더 - special
 L163  오른쪽 끝이 아니면 rightspace -= 원래 high key 크기
 L171  olddataitemstotal = rightspace - 남은 공간           항목들이 쓴 바이트
 L175  newitemsz += 라인 포인터 4
 L208  항목마다 _bt_recsplitloc (합법인 지점만 splits[] 에)
 L252  새 튜플이 맨 끝이면 "새 튜플 혼자 오른쪽" 후보도
 L280  fillfactor 선택
         내부 페이지         70% (BTREE_NONLEAF_FILLFACTOR), 오른쪽 끝일 때만 가중
         오른쪽 끝 리프       leaffillfactor (기본 90, BTREE_DEFAULT_FILLFACTOR)
         지역적 증가 패턴     _bt_afternewitemoff 가 참이면 새 튜플 바로 뒤 또는 fillfactor
         그 밖의 리프         50:50
 L345  _bt_deltasortsplits                                   균형 차이(delta)로 정렬
 L348  interval = _bt_defaultinterval                       허용 오차 안의 앞쪽 후보 수
 L364  perfectpenalty = _bt_strategy                        중복이 많으면 전략 변경
 L423  _bt_bestsplitloc                                     interval 안에서 벌점 최소
```

아래는 [09] 의 그림을 만든 계산이다. `int4` 기본키 루트 리프(블록 1)에 키 1..407 이 차 있고 408 을 넣는다. 오른쪽 끝 리프라 fillfactor 90 을 쓴다.

```text
 1. 공간 (L158-L175)
    leftspace = rightspace = 8192 - 24 - 16 = 8152          오른쪽 끝이라 high key 차감 없음
    olddataitemstotal = 8152 - PageGetExactFreeSpace(12) = 8140 = 407 * 20
    newitemsz = 16 + 4 = 20
    newitemoff = 408 = maxoff + 1                            새 튜플은 맨 끝

 2. 후보 (L208-L253)  offnum = k 가 오른쪽 첫 항목, 모두 newitemoff 보다 작으니 newitemonleft = false
    olddataitemstoleft = 20 (k - 1)
    leftfree  = 8152 - 20(k-1) - (20 + MAXALIGN(6) = 8)  = 8144 - 20k     (L496, L524)
    rightfree = 8152 - (8140 - 20(k-1)) - 20             = 20k - 28       (L497, L534)
    합법 = 둘 다 >= 0 (L545)
      k = 1     rightfree = -8         버림 (왼쪽이 비는 분할)
      k = 2..407                       406 개 기록
      k = 408   (L253) leftfree = 8152 - 8140 - 28 = -16   버림

 3. delta (L566-L588, usemult = true, 0.9)
    delta = | 0.9 * leftfree - 0.1 * rightfree |   (int16 로 잘림)
          = | 7332.4 - 20k |
      k = 366   leftfree 824  rightfree 7292   741.6 - 729.2 =  12.4 -> 12
      k = 367   leftfree 804  rightfree 7312   723.6 - 731.2 =  -7.6 -> 7    가장 작다
      k = 368   leftfree 784  rightfree 7332   705.6 - 733.2 = -27.6 -> 27

 4. interval (L876-L920)  tolerance = 8140 * 0.05 = 407
    k = 367 기준으로 leftfree 804 +- 407, rightfree 7312 +- 407 안
      -> k = 347..387, 41 개

 5. 벌점 (L1131 _bt_split_penalty)  리프는 _bt_keep_natts_fast(lastleft, firstright)
    키가 모두 다르므로 첫 열에서 갈린다 -> 1 = perfectpenalty
    정렬 첫 후보 k = 367 에서 바로 멈춘다 (L810-L811)

 결과  firstrightoff = 367, newitemonleft = false
       왼쪽 1..366 (366 개), 오른쪽 367..407 + 408 (42 개)
```

`_bt_recsplitloc` 은 왼쪽 high key 를 `firstright` 크기 + 힙 TID 8 바이트로 셌지만, 실제로는 키가 모두 달라 [09] 의 `_bt_truncate` 가 힙 TID 를 붙이지 않으므로 high key 는 `firstright` 와 같은 16 바이트다. 그래서 계산상 왼쪽 남는 공간은 804 인데 실제 분할 뒤에는 812 다.

중복이 많아 interval 안에 키 열만으로 갈리는 지점(벌점 <= 키 열 수)이 없으면 전략이 바뀐다(L934 `_bt_strategy`).

```text
 전략 (FindSplitStrat, L20-L26)

 SPLIT_DEFAULT          interval 안에 키 열만으로 갈리는 지점이 있다
                        -> 그중 벌점(남겨야 할 열 수) 최소
 SPLIT_MANY_DUPLICATES  interval 안에는 없지만 페이지 전체에는 있다
                        -> interval = 전체, 중복 묶음의 바로 왼쪽이나 오른쪽에서 자른다 (L404)
 SPLIT_SINGLE_VALUE     페이지 전체가 같은 값
                        -> fillfactor 96 (BTREE_SINGLEVAL_FILLFACTOR) 로 왼쪽을 거의 채운다 (L411)
                           힙 TID 가 커지는 방향으로 같은 값이 계속 들어오리라 보고
```

## 결과가 쓰이는 곳

```text
 firstrightoff, newitemonleft
      --> [09] _bt_split 이 항목을 나눌 기준
      --> lastleft 와 firstright 가 정해져 왼쪽 high key (= 부모에 올라갈 구분 키) 가 정해진다
```

## 다루지 않는 것

`_bt_afternewitemoff` 의 "지역적 증가" 판정(복합 인덱스의 앞 열이 묶음을 이룰 때), `_bt_interval_edges`, 내부 페이지의 벌점(오른쪽 첫 튜플 크기), `!heapkeyspace` 인덱스에서의 차이는 다루지 않는다.
