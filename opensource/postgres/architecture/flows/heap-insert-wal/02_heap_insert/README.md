# heap_insert

상위: [행 쓰기와 WAL 기록](../README.md)

**힙에 행 하나를 넣는 전 과정을 지휘한다.** 실패할 수 있는 일(헤더 준비, TOAST, 페이지 찾기, 직렬화 충돌 검사)은 전부 크리티컬 섹션 밖에서 먼저 끝낸다. 그다음 크리티컬 섹션 안에서 페이지에 행을 붙이고, 버퍼를 더럽히고, WAL 레코드를 넣고, 받은 LSN 을 페이지에 찍는다. 크리티컬 섹션 안의 ERROR 는 PANIC 이 되므로, 이 함수의 구조 자체가 "실패할 일은 앞에, 되돌릴 수 없는 일은 뒤에"로 짜여 있다.

## 위치

`access` / `heap` / `heapam.c` L2081-L2289 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2081-L2289))

## 실제 코드

크리티컬 섹션 앞부분이다. 실패할 수 있는 준비를 모두 여기서 한다.

`access` / `heap` / `heapam.c` L2080-L2139 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2080-L2139))

```c
// heapam.c L2080-L2139
void
heap_insert(Relation relation, HeapTuple tup, CommandId cid,
			int options, BulkInsertState bistate)
{
	TransactionId xid = GetCurrentTransactionId();
	HeapTuple	heaptup;
	Buffer		buffer;
	Page		page;
	Buffer		vmbuffer = InvalidBuffer;
	bool		clear_all_visible = false;
	bool		vmbuffer_modified = false;

	/* Cheap, simplistic check that the tuple matches the rel's rowtype. */
	Assert(HeapTupleHeaderGetNatts(tup->t_data) <=
		   RelationGetNumberOfAttributes(relation));

	AssertHasSnapshotForToast(relation);

	/*
	 * Fill in tuple header fields and toast the tuple if necessary.
	 *
	 * Note: below this point, heaptup is the data we actually intend to store
	 * into the relation; tup is the caller's original untoasted data.
	 */
	heaptup = heap_prepare_insert(relation, tup, xid, cid, options);

	/*
	 * Find buffer to insert this tuple into.  If the page is all visible,
	 * this will also pin the requisite visibility map page.
	 */
	buffer = RelationGetBufferForTuple(relation, heaptup->t_len,
									   InvalidBuffer, options, bistate,
									   &vmbuffer, NULL,
									   0);
	page = BufferGetPage(buffer);

	/*
	 * We're about to do the actual insert -- but check for conflict first, to
	 * avoid possibly having to roll back work we've just done.
	 *
	 * This is safe without a recheck as long as there is no possibility of
	 * another process scanning the page between this check and the insert
	 * being visible to the scan (i.e., an exclusive buffer content lock is
	 * continuously held from this point until the tuple insert is visible).
	 *
	 * For a heap insert, we only need to check for table-level SSI locks. Our
	 * new tuple can't possibly conflict with existing tuple locks, and heap
	 * page locks are only consolidated versions of tuple locks; they do not
	 * lock "gaps" as index page locks do.  So we don't need to specify a
	 * buffer when making the call, which makes for a faster check.
	 */
	CheckForSerializableConflictIn(relation, NULL, InvalidBlockNumber);

	/* Lock the vmbuffer before the critical section */
	if (PageIsAllVisible(page))
	{
		LockBuffer(vmbuffer, BUFFER_LOCK_EXCLUSIVE);
		clear_all_visible = true;
	}

```

크리티컬 섹션이다. 페이지 변경, `MarkBufferDirty`, WAL 레코드 등록과 삽입, `PageSetLSN` 이 이 순서로 온다.

`access` / `heap` / `heapam.c` L2140-L2256 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2140-L2256))

```c
// heapam.c L2140-L2256
	/* NO EREPORT(ERROR) from here till changes are logged */
	START_CRIT_SECTION();

	RelationPutHeapTuple(relation, buffer, heaptup,
						 (options & HEAP_INSERT_SPECULATIVE) != 0);

	if (clear_all_visible)
	{
		/* It's possible the VM bits were already clear */
		if (visibilitymap_clear_locked(relation,
									   ItemPointerGetBlockNumber(&(heaptup->t_self)),
									   vmbuffer, VISIBILITYMAP_VALID_BITS))
			vmbuffer_modified = true;

		PageClearAllVisible(page);
	}

	/*
	 * XXX Should we set PageSetPrunable on this page ?
	 *
	 * The inserting transaction may eventually abort thus making this tuple
	 * DEAD and hence available for pruning. Though we don't want to optimize
	 * for aborts, if no other tuple in this page is UPDATEd/DELETEd, the
	 * aborted tuple will never be pruned until next vacuum is triggered.
	 *
	 * If you do add PageSetPrunable here, add it in heap_xlog_insert too.
	 */

	MarkBufferDirty(buffer);

	/* XLOG stuff */
	if (RelationNeedsWAL(relation))
	{
		xl_heap_insert xlrec;
		xl_heap_header xlhdr;
		XLogRecPtr	recptr;
		uint8		info = XLOG_HEAP_INSERT;
		int			bufflags = 0;

		/*
		 * If this is a catalog, we need to transmit combo CIDs to properly
		 * decode, so log that as well.
		 */
		if (RelationIsAccessibleInLogicalDecoding(relation))
			log_heap_new_cid(relation, heaptup);

		/*
		 * If this is the single and first tuple on page, we can reinit the
		 * page instead of restoring the whole thing.  Set flag, and hide
		 * buffer references from XLogInsert.
		 */
		if (ItemPointerGetOffsetNumber(&(heaptup->t_self)) == FirstOffsetNumber &&
			PageGetMaxOffsetNumber(page) == FirstOffsetNumber)
		{
			info |= XLOG_HEAP_INIT_PAGE;
			bufflags |= REGBUF_WILL_INIT;
		}

		xlrec.offnum = ItemPointerGetOffsetNumber(&heaptup->t_self);
		xlrec.flags = 0;
		if (clear_all_visible)
			xlrec.flags |= XLH_INSERT_ALL_VISIBLE_CLEARED;
		if (options & HEAP_INSERT_SPECULATIVE)
			xlrec.flags |= XLH_INSERT_IS_SPECULATIVE;
		Assert(ItemPointerGetBlockNumber(&heaptup->t_self) == BufferGetBlockNumber(buffer));

		/*
		 * For logical decoding, we need the tuple even if we're doing a full
		 * page write, so make sure it's included even if we take a full-page
		 * image. (XXX We could alternatively store a pointer into the FPW).
		 */
		if (RelationIsLogicallyLogged(relation) &&
			!(options & HEAP_INSERT_NO_LOGICAL))
		{
			xlrec.flags |= XLH_INSERT_CONTAINS_NEW_TUPLE;
			bufflags |= REGBUF_KEEP_DATA;

			if (IsToastRelation(relation))
				xlrec.flags |= XLH_INSERT_ON_TOAST_RELATION;
		}

		XLogBeginInsert();
		XLogRegisterData(&xlrec, SizeOfHeapInsert);

		xlhdr.t_infomask2 = heaptup->t_data->t_infomask2;
		xlhdr.t_infomask = heaptup->t_data->t_infomask;
		xlhdr.t_hoff = heaptup->t_data->t_hoff;

		/*
		 * note we mark xlhdr as belonging to buffer; if XLogInsert decides to
		 * write the whole page to the xlog, we don't need to store
		 * xl_heap_header in the xlog.
		 */
		XLogRegisterBuffer(HEAP_INSERT_BLKREF_HEAP, buffer,
						   REGBUF_STANDARD | bufflags);
		XLogRegisterBufData(HEAP_INSERT_BLKREF_HEAP, &xlhdr,
							SizeOfHeapHeader);
		/* PG73FORMAT: write bitmap [+ padding] [+ oid] + data */
		XLogRegisterBufData(HEAP_INSERT_BLKREF_HEAP,
							(char *) heaptup->t_data + SizeofHeapTupleHeader,
							heaptup->t_len - SizeofHeapTupleHeader);

		/* filtering by origin on a row level is much more efficient */
		XLogSetRecordFlags(XLOG_INCLUDE_ORIGIN);

		if (vmbuffer_modified)
			XLogRegisterBuffer(HEAP_INSERT_BLKREF_VM, vmbuffer, 0);

		recptr = XLogInsert(RM_HEAP_ID, info);

		PageSetLSN(page, recptr);

		if (vmbuffer_modified)
			PageSetLSN(BufferGetPage(vmbuffer), recptr);
	}

	END_CRIT_SECTION();
```

뒷정리다. 버퍼 잠금을 풀고, 캐시 무효화를 예약하고, 통계를 센다.

`access` / `heap` / `heapam.c` L2258-L2289 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2258-L2289))

```c
// heapam.c L2258-L2289
	UnlockReleaseBuffer(buffer);

	/*
	 * We locked vmbuffer if clear_all_visible was true regardless of whether
	 * or not we ended up modifying the vmbuffer.
	 */
	if (clear_all_visible)
		LockBuffer(vmbuffer, BUFFER_LOCK_UNLOCK);
	if (BufferIsValid(vmbuffer))
		ReleaseBuffer(vmbuffer);

	/*
	 * If tuple is cachable, mark it for invalidation from the caches in case
	 * we abort.  Note it is OK to do this after releasing the buffer, because
	 * the heaptup data structure is all in local memory, not in the shared
	 * buffer.
	 */
	CacheInvalidateHeapTuple(relation, heaptup, NULL);

	/* Note: speculative insertions are counted too, even if aborted later */
	pgstat_count_heap_insert(relation, 1);

	/*
	 * If heaptup is a private copy, release it.  Don't forget to copy t_self
	 * back to the caller's image, too.
	 */
	if (heaptup != tup)
	{
		tup->t_self = heaptup->t_self;
		heap_freetuple(heaptup);
	}
}
```

## 동작 흐름

```text
 크리티컬 섹션 밖 (ERROR 가 나도 버퍼에 남은 변경이 없다)
 L2084  xid = GetCurrentTransactionId()            첫 쓰기면 여기서 XID 를 받는다
 L2104  heaptup = heap_prepare_insert(...)         --> [03] 헤더 채우기, 필요하면 TOAST
 L2110  buffer = RelationGetBufferForTuple(...)    --> [04] pin + BUFFER_LOCK_EXCLUSIVE 로 돌아온다
 L2131  CheckForSerializableConflictIn             SERIALIZABLE 의 테이블 단위 충돌 검사
 L2134  페이지가 all-visible 이면
 L2136    VM 페이지를 배타 잠금 (크리티컬 섹션 전에)

 L2141  START_CRIT_SECTION()  ---------------------------------------------------
 L2143    RelationPutHeapTuple(relation, buffer, heaptup, ...)   --> [05]
 L2146    all-visible 이었으면
 L2149      visibilitymap_clear_locked             비트가 실제로 바뀌었으면 vmbuffer_modified
 L2154      PageClearAllVisible(page)
 L2168    MarkBufferDirty(buffer)
 L2171    RelationNeedsWAL 이면 (UNLOGGED, 임시 테이블은 아니다)
 L2183      논리 디코딩 대상 카탈로그면 log_heap_new_cid
 L2191      이 행이 페이지의 첫 행이자 유일한 행이면
 L2194        info |= XLOG_HEAP_INIT_PAGE, bufflags |= REGBUF_WILL_INIT
 L2198      xlrec.offnum = 줄 번호, flags
 L2221      XLogBeginInsert()
 L2222      XLogRegisterData(&xlrec, SizeOfHeapInsert)         주 데이터
 L2233      XLogRegisterBuffer(0, buffer, REGBUF_STANDARD | bufflags)
 L2235      XLogRegisterBufData(0, &xlhdr, SizeOfHeapHeader)   블록 0 의 데이터 1
 L2238      XLogRegisterBufData(0, 튜플 본문, t_len - 23)       블록 0 의 데이터 2
 L2243      XLogSetRecordFlags(XLOG_INCLUDE_ORIGIN)
 L2245      VM 을 바꿨으면 XLogRegisterBuffer(1, vmbuffer, 0)
 L2248      recptr = XLogInsert(RM_HEAP_ID, info)              --> [06]
 L2250      PageSetLSN(page, recptr)
 L2253      VM 페이지에도 PageSetLSN
 L2256  END_CRIT_SECTION()  -----------------------------------------------------

 L2258  UnlockReleaseBuffer(buffer)               다른 백엔드가 이제 이 페이지를 본다
 L2264  VM 잠금 해제, L2267 VM pin 해제
 L2275  CacheInvalidateHeapTuple                  카탈로그 행이면 abort 대비 무효화 예약
 L2278  pgstat_count_heap_insert
 L2284  TOAST 사본이었으면 t_self 를 원본에 복사하고 사본을 버린다
```

WAL 레코드의 재료는 세 갈래로 등록된다. 블록에 묶인 데이터(`XLogRegisterBufData`)는 그 블록의 전체 이미지가 실리면 빠질 수 있고, 주 데이터(`XLogRegisterData`)는 늘 실린다. 튜플 헤더를 블록 쪽에 둔 이유는 L2228-L2231 주석에 있다. 페이지 전체가 실리면 헤더를 따로 실을 필요가 없다.

```text
 XLOG_HEAP_INSERT 레코드에 등록되는 것 (행 = int4 열 두 개, NULL 없음)

 행 모양 (메모리, heaptup)
   t_data: HeapTupleHeaderData 23바이트 + 패딩 1 (t_hoff = 24) + 데이터 8바이트   t_len = 32

 등록               크기   위치와 FPI 가 실릴 때
 xl_heap_insert     3      주 데이터. FPI 여도 그대로 실린다
   offnum (2), flags (1)
 xl_heap_header     5      블록 0 의 데이터. FPI 면 빠진다 (REGBUF_KEEP_DATA 가 없으면)
   t_infomask2, t_infomask, t_hoff
 tuple data         9      튜플 본문, 블록 0 의 데이터. FPI 면 빠진다
   (char *) t_data + 23 부터 t_len - 23 바이트 = 패딩 1 + 데이터 8
 block 0 ref        -      XLogRegisterBuffer. 이 페이지 (t2, 블록 7)

 SizeOfHeapInsert = offsetof(flags) + 1 = 3        heapam_xlog.h L174
 SizeOfHeapHeader = offsetof(t_hoff) + 1 = 5       heapam_xlog.h L160
```

redo 쪽은 이 9바이트 앞에 `xl_heap_header` 의 세 필드를 붙이고, xmin 같은 나머지 헤더 필드는 레코드의 `xl_xid` 등으로 다시 만든다(include/access/heapam_xlog.h L147-L150 주석은 "we can save a few bytes by reconstructing the fields that are available elsewhere in the WAL record" 라고 적는다 — 레코드의 다른 곳에서 얻을 수 있는 필드는 다시 만든다는 뜻이고, heap_xlog_insert 가 xmin 을 XLogRecGetXid 로 채운다. access/heap/heapam_xlog.c L555).

`XLOG_HEAP_INIT_PAGE` 는 페이지를 통째로 다시 만들 수 있다는 표시다. 이 행이 1번 줄이자 페이지의 유일한 줄이면, redo 는 디스크의 페이지 내용을 볼 필요 없이 빈 페이지를 만들고 이 행 하나를 넣으면 된다. `REGBUF_WILL_INIT` 은 그래서 이 블록에 대해 페이지 이미지를 찍지 않게 한다(L2187-L2189 주석, [07] 의 판정).

```text
 INIT_PAGE 판정 (L2191-L2192)

 offnum   MaxOffset   INIT_PAGE   페이지 상태 (넣은 뒤)
 1        1           O           확장으로 새로 만든 빈 페이지에 첫 행. redo 가 빈 페이지부터 다시 만든다
 11       11          X           행 10개가 있는 페이지에 추가
 1        5           X           줄 1 이 비어 재사용됐다 (다른 줄 있음)
```

## 결과가 쓰이는 곳

```text
 tup->t_self (= heaptup->t_self)
      --> [01] heapam_tuple_insert 가 slot->tts_tid 로 복사한다
 페이지 LSN
      --> 버퍼를 디스크에 쓰기 전 FlushBuffer 의 XLogFlush(recptr) (bufmgr.c L4371)
 recptr / XactLastRecEnd
      --> 커밋이 XLogFlush 로 기다릴 위치 ([08] 이 XactLastRecEnd = EndPos 로 둔다)
 VM 비트 해제
      --> VM 페이지를 블록 1 로 등록해 같은 레코드에 싣는다 (L2246). redo 도 VM 비트를 지운다
```

## 다루지 않는 것

TOAST(`heap_toast_insert_or_update`), SSI 충돌 검사(`CheckForSerializableConflictIn`), 논리 디코딩용 기록(`log_heap_new_cid`, `XLH_INSERT_CONTAINS_NEW_TUPLE`), visibility map 의 비트 의미(`visibilitymap_clear_locked`), 카탈로그 캐시 무효화(`CacheInvalidateHeapTuple`), 대량 삽입(`heap_multi_insert`, `BulkInsertState`)은 힙 삽입의 곁가지라 요약만 했다.
