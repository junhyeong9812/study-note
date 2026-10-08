# _bt_check_unique

상위: [nbtree 삽입과 분할](../README.md)

**같은 키를 가진 인덱스 항목을 하나씩 따라가 힙 튜플이 살아 있는지 확인한다.** 살아 있는 중복이 커밋되어 있으면 에러, 아직 진행 중인 트랜잭션의 것이면 그 xid 를 돌려주어 호출자가 기다리게 한다. 가는 길에 모두에게 죽은 항목은 `LP_DEAD` 로 표시해 두어, 뒤에서 분할 대신 지울 수 있게 한다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L408-L772 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L408-L772))

## 실제 코드

준비와 첫 위치 찾기다. `SnapshotDirty` 는 커밋되지 않은 변경도 보이게 해서 "누가 지금 이 키를 쓰고 있는가"를 알려 준다. 이진 탐색 범위는 `insertstate` 에 저장되어 [07] 이 다시 쓴다.

`access` / `nbtree` / `nbtinsert.c` L408-L443 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L408-L443))

```c
// nbtinsert.c L408-L443
_bt_check_unique(Relation rel, BTInsertState insertstate, Relation heapRel,
				 IndexUniqueCheck checkUnique, bool *is_unique,
				 uint32 *speculativeToken)
{
	IndexTuple	itup = insertstate->itup;
	IndexTuple	curitup = NULL;
	ItemId		curitemid = NULL;
	BTScanInsert itup_key = insertstate->itup_key;
	SnapshotData SnapshotDirty;
	OffsetNumber offset;
	OffsetNumber maxoff;
	Page		page;
	BTPageOpaque opaque;
	Buffer		nbuf = InvalidBuffer;
	bool		found = false;
	bool		inposting = false;
	bool		prevalldead = true;
	int			curposti = 0;

	/* Assume unique until we find a duplicate */
	*is_unique = true;

	InitDirtySnapshot(SnapshotDirty);

	page = BufferGetPage(insertstate->buf);
	opaque = BTPageGetOpaque(page);
	maxoff = PageGetMaxOffsetNumber(page);

	/*
	 * Find the first tuple with the same key.
	 *
	 * This also saves the binary search bounds in insertstate.  We use them
	 * in the fastpath below, but also in the _bt_findinsertloc() call later.
	 */
	Assert(!insertstate->bounds_valid);
	offset = _bt_binsrch_insert(rel, insertstate);
```

같은 키 항목마다 힙 TID 를 꺼내 힙에서 확인한다. posting list 튜플이면 그 안의 TID 를 하나씩 본다.

`access` / `nbtree` / `nbtinsert.c` L451-L599 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L451-L599))

```c
// nbtinsert.c L451-L599
	for (;;)
	{
		// ... (L453-L468 생략: 주석: 한 바퀴는 TID 하나)
		if (offset <= maxoff)
		{
			// ... (L471-L482 생략: 주석: 캐시한 탐색 범위로 끝을 안다)
			if (nbuf == InvalidBuffer && offset == insertstate->stricthigh)
			{
				Assert(insertstate->bounds_valid);
				Assert(insertstate->low >= P_FIRSTDATAKEY(opaque));
				Assert(insertstate->low <= insertstate->stricthigh);
				Assert(_bt_compare(rel, itup_key, page, offset) < 0);
				break;
			}

			// ... (L492-L502 생략: 주석: 죽은 항목은 비교 없이 건너뜀)
			if (!inposting)
				curitemid = PageGetItemId(page, offset);
			if (inposting || !ItemIdIsDead(curitemid))
			{
				ItemPointerData htid;
				bool		all_dead = false;

				if (!inposting)
				{
					/* Plain tuple, or first TID in posting list tuple */
					if (_bt_compare(rel, itup_key, page, offset) != 0)
						break;	/* we're past all the equal tuples */

					/* Advanced curitup */
					curitup = (IndexTuple) PageGetItem(page, curitemid);
					Assert(!BTreeTupleIsPivot(curitup));
				}

				/* okay, we gotta fetch the heap tuple using htid ... */
				if (!BTreeTupleIsPosting(curitup))
				{
					/* ... htid is from simple non-pivot tuple */
					Assert(!inposting);
					htid = curitup->t_tid;
				}
				else if (!inposting)
				{
					/* ... htid is first TID in new posting list */
					inposting = true;
					prevalldead = true;
					curposti = 0;
					htid = *BTreeTupleGetPostingN(curitup, 0);
				}
				else
				{
					/* ... htid is second or subsequent TID in posting list */
					Assert(curposti > 0);
					htid = *BTreeTupleGetPostingN(curitup, curposti);
				}

				/*
				 * If we are doing a recheck, we expect to find the tuple we
				 * are rechecking.  It's not a duplicate, but we have to keep
				 * scanning.
				 */
				if (checkUnique == UNIQUE_CHECK_EXISTING &&
					ItemPointerCompare(&htid, &itup->t_tid) == 0)
				{
					found = true;
				}

				/*
				 * Check if there's any table tuples for this index entry
				 * satisfying SnapshotDirty. This is necessary because for AMs
				 * with optimizations like heap's HOT, we have just a single
				 * index entry for the entire chain.
				 */
				else if (table_index_fetch_tuple_check(heapRel, &htid,
													   &SnapshotDirty,
													   &all_dead))
				{
					TransactionId xwait;

					// ... (L566-L573 생략: 주석: PARTIAL 은 기다리지 않는다)
					if (checkUnique == UNIQUE_CHECK_PARTIAL)
					{
						if (nbuf != InvalidBuffer)
							_bt_relbuf(rel, nbuf);
						*is_unique = false;
						return InvalidTransactionId;
					}

					/*
					 * If this tuple is being updated by other transaction
					 * then we have to wait for its commit/abort.
					 */
					xwait = (TransactionIdIsValid(SnapshotDirty.xmin)) ?
						SnapshotDirty.xmin : SnapshotDirty.xmax;

					if (TransactionIdIsValid(xwait))
					{
						if (nbuf != InvalidBuffer)
							_bt_relbuf(rel, nbuf);
						/* Tell _bt_doinsert to wait... */
						*speculativeToken = SnapshotDirty.speculativeToken;
						/* Caller releases lock on buf immediately */
						insertstate->bounds_valid = false;
						return xwait;
					}

```

확정된 충돌이면 에러를 내기 전에 넣으려는 튜플 자신이 이미 죽었는지 본다(CREATE INDEX CONCURRENTLY 대비). 모두에게 죽은 중복이면 `LP_DEAD` 를 켠다.

`access` / `nbtree` / `nbtinsert.c` L600-L705 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L600-L705))

```c
// nbtinsert.c L600-L705
					// ... (L600-L616 생략: 주석: 넣으려는 튜플이 죽었으면 충돌이 아니다)
					htid = itup->t_tid;
					if (table_index_fetch_tuple_check(heapRel, &htid,
													  SnapshotSelf, NULL))
					{
						/* Normal case --- it's still live */
					}
					else
					{
						// ... (L625-L628 생략: 주석)
						break;
					}

					// ... (L632-L638 생략: 주석: SSI 충돌을 먼저 보고)
					CheckForSerializableConflictIn(rel, NULL, BufferGetBlockNumber(insertstate->buf));

					// ... (L641-L648 생략: 주석: 에러 전에 버퍼 잠금을 놓는 이유)
					if (nbuf != InvalidBuffer)
						_bt_relbuf(rel, nbuf);
					_bt_relbuf(rel, insertstate->buf);
					insertstate->buf = InvalidBuffer;
					insertstate->bounds_valid = false;

					{
						Datum		values[INDEX_MAX_KEYS];
						bool		isnull[INDEX_MAX_KEYS];
						char	   *key_desc;

						index_deform_tuple(itup, RelationGetDescr(rel),
										   values, isnull);

						key_desc = BuildIndexValueDescription(rel, values,
															  isnull);

						ereport(ERROR,
								(errcode(ERRCODE_UNIQUE_VIOLATION),
								 errmsg("duplicate key value violates unique constraint \"%s\"",
										RelationGetRelationName(rel)),
								 key_desc ? errdetail("Key %s already exists.",
													  key_desc) : 0,
								 errtableconstraint(heapRel,
													RelationGetRelationName(rel))));
					}
				}
				else if (all_dead && (!inposting ||
									  (prevalldead &&
									   curposti == BTreeTupleGetNPosting(curitup) - 1)))
				{
					/*
					 * The conflicting tuple (or all HOT chains pointed to by
					 * all posting list TIDs) is dead to everyone, so mark the
					 * index entry killed.
					 */
					ItemIdMarkDead(curitemid);
					opaque->btpo_flags |= BTP_HAS_GARBAGE;

					/*
					 * Mark buffer with a dirty hint, since state is not
					 * crucial. Be sure to mark the proper buffer dirty.
					 */
					if (nbuf != InvalidBuffer)
						MarkBufferDirtyHint(nbuf, true);
					else
						MarkBufferDirtyHint(insertstate->buf, true);
				}

				/*
				 * Remember if posting list tuple has even a single HOT chain
				 * whose members are not all dead
				 */
				if (!all_dead && inposting)
					prevalldead = false;
			}
		}
```

다음 항목, 다음 TID, 또는 다음 페이지로 간다. 키가 페이지의 high key 와 같을 때만 오른쪽 페이지를 본다.

`access` / `nbtree` / `nbtinsert.c` L706-L772 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L706-L772))

```c
// nbtinsert.c L706-L772

		if (inposting && curposti < BTreeTupleGetNPosting(curitup) - 1)
		{
			/* Advance to next TID in same posting list */
			curposti++;
			continue;
		}
		else if (offset < maxoff)
		{
			/* Advance to next tuple */
			curposti = 0;
			inposting = false;
			offset = OffsetNumberNext(offset);
		}
		else
		{
			int			highkeycmp;

			/* If scankey == hikey we gotta check the next page too */
			if (P_RIGHTMOST(opaque))
				break;
			highkeycmp = _bt_compare(rel, itup_key, page, P_HIKEY);
			Assert(highkeycmp <= 0);
			if (highkeycmp != 0)
				break;
			/* Advance to next non-dead page --- there must be one */
			for (;;)
			{
				BlockNumber nblkno = opaque->btpo_next;

				nbuf = _bt_relandgetbuf(rel, nbuf, nblkno, BT_READ);
				page = BufferGetPage(nbuf);
				opaque = BTPageGetOpaque(page);
				if (!P_IGNORE(opaque))
					break;
				if (P_RIGHTMOST(opaque))
					elog(ERROR, "fell off the end of index \"%s\"",
						 RelationGetRelationName(rel));
			}
			/* Will also advance to next tuple */
			curposti = 0;
			inposting = false;
			maxoff = PageGetMaxOffsetNumber(page);
			offset = P_FIRSTDATAKEY(opaque);
			/* Don't invalidate binary search bounds */
		}
	}

	/*
	 * If we are doing a recheck then we should have found the tuple we are
	 * checking.  Otherwise there's something very wrong --- probably, the
	 * index is on a non-immutable expression.
	 */
	if (checkUnique == UNIQUE_CHECK_EXISTING && !found)
		ereport(ERROR,
				(errcode(ERRCODE_INTERNAL_ERROR),
				 errmsg("failed to re-find tuple within index \"%s\"",
						RelationGetRelationName(rel)),
				 errhint("This may be because of a non-immutable index expression."),
				 errtableconstraint(heapRel,
									RelationGetRelationName(rel))));

	if (nbuf != InvalidBuffer)
		_bt_relbuf(rel, nbuf);

	return InvalidTransactionId;
}
```

## 동작 흐름

```text
 L430  InitDirtySnapshot
 L443  offset = _bt_binsrch_insert            키(scantid 없이)의 첫 자리. low/stricthigh 를 저장
 L451  for (;;)   한 바퀴 = 힙 TID 하나
 L469    offset <= maxoff 이면
 L483      offset == stricthigh 이고 첫 페이지   -> 중복 끝. break (비교 없이)
 L505      죽은(LP_DEAD) 항목이 아니면
 L513        _bt_compare != 0                    -> 같은 키가 끝났다. break
 L522        htid 를 꺼낸다 (일반 / posting 첫 TID / posting 다음 TID)
 L548        EXISTING 재검사이고 내 TID 면       -> found = true
 L560        table_index_fetch_tuple_check(SnapshotDirty) 로 HOT 체인에 보이는 버전이 있나
               있음 -> 아래 "중복을 찾았을 때"
 L676          없음, 체인 전체가 모두에게 죽음     -> ItemIdMarkDead + BTP_HAS_GARBAGE
 L707    posting 안이면 curposti++ (같은 오프셋)
 L713    아니면 offset++
 L720    페이지 끝이면
 L725      오른쪽 끝 페이지                      -> break
 L727      key 와 high key 비교, 같지 않으면     -> break
 L732      같으면 다음 살아 있는 페이지로 (읽기 잠금, nbuf)
 L759  EXISTING 인데 못 찾았으면 에러 (불변이 아닌 표현식 인덱스 의심)
 L771  return InvalidTransactionId               통과
```

중복을 찾았을 때 무엇을 하는지는 `SnapshotDirty` 가 채워 준 xmin, xmax 로 정해진다.

```text
 중복을 찾았을 때 (L560 이 true)

 checkUnique == PARTIAL                 L574  *is_unique = false, InvalidTransactionId
                                              기다리지 않고 "중복일 수 있음"만 알린다
 SnapshotDirty.xmin 유효                L586  그 튜플을 넣은 트랜잭션이 진행 중 -> xwait = xmin
 SnapshotDirty.xmax 유효                L587  그 튜플을 지우는 트랜잭션이 진행 중 -> xwait = xmax
   xwait 유효                           L597  return xwait  (투기적 삽입이면 토큰도 함께)
 둘 다 없음 = 커밋된 살아 있는 중복
   내 튜플이 SnapshotSelf 로 안 보임    L618  break. 내 튜플이 이미 죽었으니 충돌 아님
   보임                                 L651  버퍼를 다 놓고
                                        L666  ereport(ERROR, "duplicate key value violates ...")
```

```text
 xmax 쪽을 기다리는 이유: 지우는 중인 행

 T1: DELETE FROM t WHERE id = 5;   (커밋 전)
 T2: INSERT INTO t VALUES (5);
       _bt_check_unique -> id 5 의 힙 튜플: xmin 커밋됨, xmax = T1 (진행 중)
       -> xwait = T1, 기다린다
 T1 COMMIT   -> T2 재시도: 튜플이 죽었으므로 통과하고 넣는다
 T1 ROLLBACK -> T2 재시도: 튜플이 살아 있으므로 duplicate key 에러
```

posting list 튜플은 같은 키의 힙 TID 여러 개를 한 인덱스 튜플에 모은 것이다(dedup 의 결과). 이 함수는 인덱스 튜플이 아니라 TID 단위로 돈다. `LP_DEAD` 는 인덱스 튜플 단위 표시라서, posting list 는 모든 TID 의 체인이 다 죽었을 때만 켠다(L676-L678).

```text
 오프셋 o 의 posting list 튜플 (키 5, TID 3 개) 를 지나는 순서

 바퀴  inposting  curposti  htid            다음 동작
 1     false->true  0       postings[0]     curposti < 2 -> curposti++ (L710)
 2     true         1       postings[1]     curposti < 2 -> curposti++
 3     true         2       postings[2]     마지막 -> offset++ , inposting = false (L715-L718)

 prevalldead: 하나라도 살아 있으면 false (L703)
 세 번째 바퀴에서 prevalldead 이고 all_dead 이면 그 튜플에 LP_DEAD
```

## 결과가 쓰이는 곳

```text
 반환 xid
      --> [04] 가 버퍼를 놓고 XactLockTableWait (또는 SpeculativeInsertionWait) 후 처음부터
 *is_unique
      --> PARTIAL 이면 [01] 이 재검사 목록에 넣는다
 insertstate->low / stricthigh / bounds_valid
      --> [07] _bt_findinsertloc 가 이진 탐색을 다시 하지 않고 쓴다
 LP_DEAD 와 BTP_HAS_GARBAGE
      --> 공간이 모자랄 때 [07] 의 _bt_delete_or_dedup_one_page 가 먼저 지운다
```

## 다루지 않는 것

`table_index_fetch_tuple_check` 가 HOT 체인을 따라가는 힙 쪽 절차, 스냅샷 종류(`SnapshotDirty`, `SnapshotSelf`)의 가시성 규칙(MVCC 흐름), 투기적 삽입 토큰, 에러 메시지의 키 값 문자열을 만드는 `BuildIndexValueDescription` 은 다루지 않는다.
