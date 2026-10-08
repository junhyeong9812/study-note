# _bt_doinsert

상위: [nbtree 삽입과 분할](../README.md)

**B-tree 삽입의 지휘자다.** 리프를 찾고(`_bt_search_insert`), 유일 인덱스면 중복을 검사하고(`_bt_check_unique`), 다른 트랜잭션을 기다려야 하면 잠금을 풀고 기다린 뒤 처음부터 다시 찾는다. 통과하면 넣을 자리를 정하고(`_bt_findinsertloc`) 넣는다(`_bt_insertonpg`). 분할은 그 마지막 호출 안에서 일어난다.

## 위치

`access` / `nbtree` / `nbtinsert.c` L102-L276 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L102-L276))

## 실제 코드

준비 단계다. 유일성 검사를 할 때는 scankey 에서 힙 TID(`scantid`)를 일단 뺀다. 키가 NULL 을 포함하면 유일성 검사 자체를 건너뛴다.

`access` / `nbtree` / `nbtinsert.c` L102-L158 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L102-L158))

```c
// nbtinsert.c L102-L158
_bt_doinsert(Relation rel, IndexTuple itup,
			 IndexUniqueCheck checkUnique, bool indexUnchanged,
			 Relation heapRel)
{
	bool		is_unique = false;
	BTInsertStateData insertstate;
	BTScanInsert itup_key;
	BTStack		stack;
	bool		checkingunique = (checkUnique != UNIQUE_CHECK_NO);

	/* we need an insertion scan key to do our search, so build one */
	itup_key = _bt_mkscankey(rel, itup);

	if (checkingunique)
	{
		if (!itup_key->anynullkeys)
		{
			/* No (heapkeyspace) scantid until uniqueness established */
			itup_key->scantid = NULL;
		}
		else
		{
			/*
			 * Scan key for new tuple contains NULL key values.  Bypass
			 * checkingunique steps.  They are unnecessary because core code
			 * considers NULL unequal to every value, including NULL.
			 *
			 * This optimization avoids O(N^2) behavior within the
			 * _bt_findinsertloc() heapkeyspace path when a unique index has a
			 * large number of "duplicates" with NULL key values.
			 */
			checkingunique = false;
			/* Tuple is unique in the sense that core code cares about */
			Assert(checkUnique != UNIQUE_CHECK_EXISTING);
			is_unique = true;
		}
	}

	/*
	 * Fill in the BTInsertState working area, to track the current page and
	 * position within the page to insert on.
	 *
	 * Note that itemsz is passed down to lower level code that deals with
	 * inserting the item.  It must be MAXALIGN()'d.  This ensures that space
	 * accounting code consistently considers the alignment overhead that we
	 * expect PageAddItem() will add later.  (Actually, index_form_tuple() is
	 * already conservative about alignment, but we don't rely on that from
	 * this distance.  Besides, preserving the "true" tuple size in index
	 * tuple headers for the benefit of nbtsplitloc.c might happen someday.
	 * Note that heapam does not MAXALIGN() each heap tuple's lp_len field.)
	 */
	insertstate.itup = itup;
	insertstate.itemsz = MAXALIGN(IndexTupleSize(itup));
	insertstate.itup_key = itup_key;
	insertstate.bounds_valid = false;
	insertstate.buf = InvalidBuffer;
	insertstate.postingoff = 0;
```

리프를 찾고, 유일성을 검사하고, 기다려야 하면 버퍼를 놓고 기다린 뒤 `goto search` 로 처음부터 다시 한다.

`access` / `nbtree` / `nbtinsert.c` L160-L238 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L160-L238))

```c
// nbtinsert.c L160-L238
search:

	/*
	 * Find and lock the leaf page that the tuple should be added to by
	 * searching from the root page.  insertstate.buf will hold a buffer that
	 * is locked in exclusive mode afterwards.
	 */
	stack = _bt_search_insert(rel, heapRel, &insertstate);

	// ... (L169-L204 생략: 주석: 첫 페이지의 쓰기 잠금이 동시 삽입을 막는 이유)
	if (checkingunique)
	{
		TransactionId xwait;
		uint32		speculativeToken;

		xwait = _bt_check_unique(rel, &insertstate, heapRel, checkUnique,
								 &is_unique, &speculativeToken);

		if (unlikely(TransactionIdIsValid(xwait)))
		{
			/* Have to wait for the other guy ... */
			_bt_relbuf(rel, insertstate.buf);
			insertstate.buf = InvalidBuffer;

			/*
			 * If it's a speculative insertion, wait for it to finish (ie. to
			 * go ahead with the insertion, or kill the tuple).  Otherwise
			 * wait for the transaction to finish as usual.
			 */
			if (speculativeToken)
				SpeculativeInsertionWait(xwait, speculativeToken);
			else
				XactLockTableWait(xwait, rel, &itup->t_tid, XLTW_InsertIndex);

			/* start over... */
			if (stack)
				_bt_freestack(stack);
			goto search;
		}

		/* Uniqueness is established -- restore heap tid as scantid */
		if (itup_key->heapkeyspace)
			itup_key->scantid = &itup->t_tid;
	}
```

넣을 자리를 정하고 넣는다. `UNIQUE_CHECK_EXISTING`(지연 제약의 재검사)은 검사만 하고 넣지 않는다.

`access` / `nbtree` / `nbtinsert.c` L240-L276 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtinsert.c#L240-L276))

```c
// nbtinsert.c L240-L276
	if (checkUnique != UNIQUE_CHECK_EXISTING)
	{
		OffsetNumber newitemoff;

		/*
		 * The only conflict predicate locking cares about for indexes is when
		 * an index tuple insert conflicts with an existing lock.  We don't
		 * know the actual page we're going to insert on for sure just yet in
		 * checkingunique and !heapkeyspace cases, but it's okay to use the
		 * first page the value could be on (with scantid omitted) instead.
		 */
		CheckForSerializableConflictIn(rel, NULL, BufferGetBlockNumber(insertstate.buf));

		/*
		 * Do the insertion.  Note that insertstate contains cached binary
		 * search bounds established within _bt_check_unique when insertion is
		 * checkingunique.
		 */
		newitemoff = _bt_findinsertloc(rel, &insertstate, checkingunique,
									   indexUnchanged, stack, heapRel);
		_bt_insertonpg(rel, heapRel, itup_key, insertstate.buf, InvalidBuffer,
					   stack, itup, insertstate.itemsz, newitemoff,
					   insertstate.postingoff, false);
	}
	else
	{
		/* just release the buffer */
		_bt_relbuf(rel, insertstate.buf);
	}

	/* be tidy */
	if (stack)
		_bt_freestack(stack);
	pfree(itup_key);

	return is_unique;
}
```

## 동작 흐름

```text
 L113  itup_key = _bt_mkscankey(rel, itup)           키 값 + scantid(힙 TID) 로 비교용 키를 만든다
 L115  checkingunique (UNIQUE_CHECK_NO 가 아님)
         NULL 없음  L120  scantid = NULL              "이 키 값이 처음 나올 수 있는 페이지"를 찾게 한다
         NULL 있음  L133  checkingunique = false      NULL 은 서로 같지 않으니 검사할 것이 없다
 L153  insertstate 초기화  itemsz = MAXALIGN(튜플 크기)

 L160  search:
 L167    stack = [05] _bt_search_insert               리프를 찾아 쓰기 잠금. stack 은 내려온 길
 L205    checkingunique 면
 L210      xwait = [06] _bt_check_unique
           xwait 유효 (진행 중인 트랜잭션이 같은 키를 넣거나 지우는 중)
 L216        리프 버퍼를 놓는다                        잠금을 쥔 채 기다리지 않는다
 L225        투기적 삽입이면 SpeculativeInsertionWait
 L227        아니면 XactLockTableWait(xwait)          상대 xid 잠금을 ShareLock 으로 요청
 L232        goto search                              트리가 바뀌었을 수 있어 처음부터
 L237      통과하면 scantid = &itup->t_tid            이제 힙 TID 까지 넣어 정확한 자리를 찾는다

 L240  UNIQUE_CHECK_EXISTING 이 아니면
 L251    CheckForSerializableConflictIn(리프 블록)    SSI 충돌 검사
 L258    newitemoff = [07] _bt_findinsertloc         필요하면 오른쪽으로 걷고, dedup 으로 공간 확보
 L260    [08] _bt_insertonpg                          넣는다. 공간이 없으면 여기서 분할
 L267  EXISTING 이면 버퍼만 놓는다
 L275  return is_unique
```

유일성 검사가 동시 삽입까지 막을 수 있는 이유는 잠금 순서에 있다. 소스 주석(L169-L204)은 "그 키가 있을 수 있는 첫 페이지"의 쓰기 잠금을 검사부터 삽입까지 놓지 않는다고 설명한다. 같은 키를 넣으려는 모든 백엔드가 같은 페이지의 쓰기 잠금을 먼저 잡아야 하므로, 검사는 한 번에 한 백엔드만 한다.

```text
 같은 키 5 를 넣는 두 백엔드 (A 의 트랜잭션은 아직 커밋 전)

 A                                       B
 _bt_search_insert -> 리프 P 쓰기 잠금
 _bt_check_unique : 5 없음
 _bt_insertonpg   : 5 를 넣고 잠금 해제
                                         _bt_search_insert -> 리프 P 쓰기 잠금
                                         _bt_check_unique : 5 발견
                                           SnapshotDirty 로 보니 xmin = A 의 xid (진행 중)
                                           -> xwait = A
                                         L216  P 를 놓는다
                                         L227  XactLockTableWait(A)  ---- 잠든다
 COMMIT  (A 의 xid 잠금이 풀린다)
                                         깨어나서 L232 goto search
                                         다시 _bt_check_unique : 5 가 살아 있다
                                           -> ereport(ERROR, duplicate key)

 A 가 ROLLBACK 했다면 B 는 다시 검사할 때 5 를 죽은 튜플로 보고 그대로 넣는다
```

`XactLockTableWait` 는 상대 트랜잭션 ID 를 잠금 태그로 삼아 heavyweight lock 을 `ShareLock` 으로 요청한다(`storage/lmgr/lmgr.c` L695-L697). 트랜잭션은 xid 를 받을 때(`AssignTransactionId`, `access/transam/xact.c` L729) 자기 xid 에 `ExclusiveLock` 을 잡고(`lmgr.c` L628) 끝날 때 놓으므로, 이 요청은 상대가 끝날 때까지 잠든다. 잠드는 과정은 [heavyweight lock](../../heavyweight-lock/README.md) 흐름이다.

```text
 scantid 를 두 번 바꾸는 이유

 1단계 (검사)   scantid = NULL
                 키 5 의 "가장 왼쪽" 자리를 찾는다. 같은 키가 여러 페이지에 걸쳐도
                 첫 페이지부터 모든 중복을 훑어야 하기 때문이다
 2단계 (삽입)   scantid = 내 힙 TID   (heapkeyspace 인덱스, 버전 4 이상)
                 힙 TID 를 마지막 키 열로 쳐서 중복 사이에서도 자리가 하나로 정해진다
                 그래서 [07] 이 오른쪽 페이지로 옮겨야 할 수도 있다
```

## 결과가 쓰이는 곳

```text
 리프 페이지의 새 인덱스 튜플
      --> 인덱스 스캔이 _bt_search 로 같은 리프를 찾아 읽는다
 is_unique
      --> btinsert 반환값 -> [01] 의 재검사 목록 판단
 stack
      --> [08] 에서 분할이 나면 [11] _bt_insert_parent 가 부모를 다시 찾는 데 쓴다
```

## 다루지 않는 것

insertion scankey 를 만드는 `_bt_mkscankey`, `!heapkeyspace`(pg_upgrade 로 남은 버전 2, 3) 인덱스의 차이, SSI 의 `CheckForSerializableConflictIn` 내부, 투기적 삽입 토큰(`SpeculativeInsertionWait`)의 구조는 다루지 않는다.
