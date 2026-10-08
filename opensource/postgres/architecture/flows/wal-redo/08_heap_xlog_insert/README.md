# heap_xlog_insert

상위: [WAL redo (복구)](../README.md)

**`XLOG_HEAP_INSERT` 레코드 하나로 heap 페이지에 튜플을 다시 넣는 함수다.** 레코드에는 튜플 헤더 전체가 아니라 `xl_heap_header`(5바이트: infomask 둘과 t_hoff)와 그 뒤의 null 비트맵, 데이터만 있다. 나머지 헤더 필드는 재생 쪽이 채운다. xmin 은 레코드의 xid, cmin 은 `FirstCommandId`, t_ctid 는 자기 위치다. 페이지를 받는 일은 `XLogReadBufferForRedo` 에 맡기고, 그 결과가 `BLK_NEEDS_REDO` 일 때만 튜플을 넣는다. FPI 로 복원됐거나 이미 반영돼 있으면 아무것도 하지 않는다.

## 위치

`src/backend/access/heap` / `heapam_xlog.c` L476-L586 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_xlog.c#L476-L586))

## 실제 코드

```c
// heap/heapam_xlog.c L476-L586
static void
heap_xlog_insert(XLogReaderState *record)
{
	XLogRecPtr	lsn = record->EndRecPtr;
	xl_heap_insert *xlrec = (xl_heap_insert *) XLogRecGetData(record);
	Buffer		buffer;
	Page		page;
	union
	{
		HeapTupleHeaderData hdr;
		char		data[MaxHeapTupleSize];
	}			tbuf;
	HeapTupleHeader htup;
	xl_heap_header xlhdr;
	uint32		newlen;
	Size		freespace = 0;
	RelFileLocator target_locator;
	BlockNumber blkno;
	ItemPointerData target_tid;
	XLogRedoAction action;

	XLogRecGetBlockTag(record, HEAP_INSERT_BLKREF_HEAP, &target_locator, NULL,
					   &blkno);
	ItemPointerSetBlockNumber(&target_tid, blkno);
	ItemPointerSetOffsetNumber(&target_tid, xlrec->offnum);

	/* No freezing in the heap_insert() code path */
	Assert(!(xlrec->flags & XLH_INSERT_ALL_FROZEN_SET));

	/*
	 * The visibility map may need to be fixed even if the heap page is
	 * already up-to-date.
	 */
	if (xlrec->flags & XLH_INSERT_ALL_VISIBLE_CLEARED)
		heap_xlog_vm_clear(record, target_locator,
						   blkno, HEAP_INSERT_BLKREF_VM,
						   VISIBILITYMAP_VALID_BITS);

	/*
	 * If we inserted the first and only tuple on the page, re-initialize the
	 * page from scratch.
	 */
	if (XLogRecGetInfo(record) & XLOG_HEAP_INIT_PAGE)
	{
		buffer = XLogInitBufferForRedo(record, HEAP_INSERT_BLKREF_HEAP);
		page = BufferGetPage(buffer);
		PageInit(page, BufferGetPageSize(buffer), 0);
		action = BLK_NEEDS_REDO;
	}
	else
		action = XLogReadBufferForRedo(record, HEAP_INSERT_BLKREF_HEAP,
									   &buffer);
	if (action == BLK_NEEDS_REDO)
	{
		Size		datalen;
		char	   *data;

		page = BufferGetPage(buffer);

		if (PageGetMaxOffsetNumber(page) + 1 < xlrec->offnum)
			elog(PANIC, "invalid max offset number");

		data = XLogRecGetBlockData(record, HEAP_INSERT_BLKREF_HEAP, &datalen);

		newlen = datalen - SizeOfHeapHeader;
		Assert(datalen > SizeOfHeapHeader && newlen <= MaxHeapTupleSize);
		memcpy(&xlhdr, data, SizeOfHeapHeader);
		data += SizeOfHeapHeader;

		htup = &tbuf.hdr;
		MemSet(htup, 0, SizeofHeapTupleHeader);
		/* PG73FORMAT: get bitmap [+ padding] [+ oid] + data */
		memcpy((char *) htup + SizeofHeapTupleHeader,
			   data,
			   newlen);
		newlen += SizeofHeapTupleHeader;
		htup->t_infomask2 = xlhdr.t_infomask2;
		htup->t_infomask = xlhdr.t_infomask;
		htup->t_hoff = xlhdr.t_hoff;
		HeapTupleHeaderSetXmin(htup, XLogRecGetXid(record));
		HeapTupleHeaderSetCmin(htup, FirstCommandId);
		htup->t_ctid = target_tid;

		if (PageAddItem(page, (Item) htup, newlen, xlrec->offnum,
						true, true) == InvalidOffsetNumber)
			elog(PANIC, "failed to add tuple");

		freespace = PageGetHeapFreeSpace(page); /* needed to update FSM below */

		PageSetLSN(page, lsn);

		if (xlrec->flags & XLH_INSERT_ALL_VISIBLE_CLEARED)
			PageClearAllVisible(page);

		MarkBufferDirty(buffer);
	}
	if (BufferIsValid(buffer))
		UnlockReleaseBuffer(buffer);

	/*
	 * If the page is running low on free space, update the FSM as well.
	 * Arbitrarily, our definition of "low" is less than 20%. We can't do much
	 * better than that without knowing the fill-factor for the table.
	 *
	 * XXX: Don't do this if the page was restored from full page image. We
	 * don't bother to update the FSM in that case, it doesn't need to be
	 * totally accurate anyway.
	 */
	if (action == BLK_NEEDS_REDO && freespace < BLCKSZ / 5)
		XLogRecordPageWithFreeSpace(target_locator, blkno, freespace);
}
```

레코드 본문과 블록 데이터 앞머리의 구조체다. block 0 이 heap 페이지, block 1 이 visibility map 페이지다.

`src/include/access` / `heapam_xlog.h` L153-L174 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/heapam_xlog.h#L153-L174))

```c
// access/heapam_xlog.h L153-L174
typedef struct xl_heap_header
{
	uint16		t_infomask2;
	uint16		t_infomask;
	uint8		t_hoff;
} xl_heap_header;

#define SizeOfHeapHeader	(offsetof(xl_heap_header, t_hoff) + sizeof(uint8))

/* This is what we need to know about insert */
#define HEAP_INSERT_BLKREF_HEAP		0
#define HEAP_INSERT_BLKREF_VM		1

typedef struct xl_heap_insert
{
	OffsetNumber offnum;		/* inserted tuple's offset */
	uint8		flags;

	/* xl_heap_header & TUPLE DATA in HEAP_INSERT_BLKREF_HEAP */
} xl_heap_insert;

#define SizeOfHeapInsert	(offsetof(xl_heap_insert, flags) + sizeof(uint8))
```

## 동작 흐름

```text
 heap_xlog_insert(record)

 L479  lsn = record->EndRecPtr                     페이지에 찍을 LSN = 레코드의 끝
 L497  block 0 의 (rlocator, blkno), target_tid = (blkno, xlrec->offnum)
 L509  ALL_VISIBLE_CLEARED 면 heap_xlog_vm_clear    heap 페이지가 최신이어도 VM 은 고쳐야 할 수 있다
 L518  INIT_PAGE 면 XLogInitBufferForRedo + PageInit   읽지 않고 0 에서 시작, 무조건 NEEDS_REDO
 L526  아니면 [09] XLogReadBufferForRedo(block 0)
 L528  BLK_NEEDS_REDO 면
 L535    max offset + 1 < offnum 이면 PANIC
 L538    data = block 0 의 데이터 (xl_heap_header + 튜플 본문)
 L542    xl_heap_header 5바이트를 떼어 낸다
 L546-L557  HeapTupleHeader 를 다시 만든다
            본문 복사, infomask2, infomask, t_hoff
            xmin = XLogRecGetXid(record), cmin = FirstCommandId, t_ctid = target_tid
 L559    PageAddItem(page, htup, newlen, offnum, overwrite = true, is_heap = true)
 L563    freespace = PageGetHeapFreeSpace
 L565    PageSetLSN(page, lsn)
 L567    PageClearAllVisible (필요하면)
 L570    MarkBufferDirty
 L572  UnlockReleaseBuffer
 L584  NEEDS_REDO 였고 freespace < BLCKSZ / 5 면 FSM 갱신
```

레코드의 블록 데이터가 튜플로 다시 조립되는 모습이다. 숫자는 null 이 없는 `int4` 두 열짜리 튜플의 예다(SizeofHeapTupleHeader = `offsetof(HeapTupleHeaderData, t_bits)` = 23, include/access/htup_details.h L185).

```text
 WAL 레코드 (Heap/INSERT, xid = 812)
 +-----------------+-----------------+---------------------------------------------+
 | XLogRecord 헤더 | block 0 참조     | 본문 xl_heap_insert {offnum = 3, flags}     |
 +-----------------+-----------------+---------------------------------------------+
   block 0 데이터 = xl_heap_header {t_infomask2 = 2, t_infomask, t_hoff = 24} (5 바이트)
                    + 튜플의 23 바이트 이후 전부 = 패딩 1 + 열 데이터 8 = 9 바이트
                      (heap_insert 가 t_data + SizeofHeapTupleHeader 부터 싣는다, heapam.c L2239-L2240)
   datalen = 14 -> newlen = 14 - 5 = 9 (L540)

 재생이 만드는 튜플 (헤더 23 바이트를 0 으로 채운 뒤 L546, 그 뒤에 9 바이트 복사 L548)
 +--------------------------------------------------------------+---+-----------------+
 | t_xmin = 812     t_xmax = 0       t_cid = 0 (FirstCommandId) |pad| 데이터 8 바이트 |
 | t_ctid = (blkno, 3)                                          |   |                 |
 | t_infomask2 = 2  t_infomask       t_hoff = 24                |   |                 |
 +--------------------------------------------------------------+---+-----------------+
 0                                                              23  24                32
   newlen = 9 + 23 = 32 (L551) -> PageAddItem 이 라인 포인터 3 에 32 바이트로 넣는다
```

`BLK_NEEDS_REDO` 가 아니면 이 함수는 페이지를 건드리지 않는다. 세 경우를 한 페이지로 그리면 이렇다.

```text
 action          condition (in [09])          이 함수가 하는 일
 BLK_NEEDS_REDO  record end > page LSN        튜플을 넣고 PageSetLSN
 BLK_DONE        record end <= page LSN       없음 (unlock 만). 이미 디스크에 반영돼 있다
 BLK_RESTORED    record has FPI to apply      없음. [09] 가 덮어쓴 이미지에 이 튜플이 이미 들어 있다
 BLK_NOTFOUND    page does not exist          없음. buffer 가 Invalid (뒤에서 truncate 된 릴레이션)
```

## 결과가 쓰이는 곳

```text
 페이지 LSN = 레코드 끝
      --> 같은 페이지를 고친 다음 레코드가 [09] 에서 비교하는 기준
 MarkBufferDirty
      --> restartpoint 또는 end-of-recovery 체크포인트가 내려 쓴다
 xmin = 812 인 튜플
      --> 기동 뒤 가시성은 pg_xact 의 812 상태로 정해진다 (같은 WAL 의 commit 레코드를 xact_redo 가 반영)
 FSM
      --> 빈 공간이 20% 미만이면 기록. FPI 로 복원된 경우는 건너뛴다 (주석 L575-L583)
```

## 다루지 않는 것

`heap_xlog_vm_clear` 의 visibility map 처리, `PageAddItem` 의 라인 포인터 배치, `XLogRecordPageWithFreeSpace`, `heap_insert` 쪽에서 이 레코드를 만드는 과정([행 쓰기와 WAL 기록](../../heap-insert-wal/02_heap_insert/README.md))은 요약만 했다.
