# XLogInsert

상위: [행 쓰기와 WAL 기록](../README.md)

**호출자가 `XLogRegister*` 로 등록해 둔 조각들을 레코드 하나로 만들어 WAL 에 넣고, 레코드 끝 위치(LSN)를 돌려준다.** 일은 두 함수에 나눠 맡긴다. [07] 이 백엔드 지역 메모리에서 레코드를 조립하고, [08] 이 공유 WAL 버퍼에 넣는다. 조립할 때 쓴 "지금 체크포인트 위치"가 넣는 순간 이미 낡았다면 [08] 이 거절하고, 이 함수가 다시 조립한다. 그래서 본문이 `do ... while` 이다.

## 위치

`access` / `transam` / `xloginsert.c` L474-L530 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L474-L530))

## 실제 코드

등록은 백엔드 지역 배열에 포인터를 적어 두는 일이다. 데이터를 복사하지 않는다. 그래서 호출자의 지역 변수(`xlrec`, `xlhdr`)는 `XLogInsert` 가 돌아올 때까지 살아 있어야 한다.

`access` / `transam` / `xloginsert.c` L144-L163 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L144-L163))

```c
// xloginsert.c L144-L163
/*
 * Begin constructing a WAL record. This must be called before the
 * XLogRegister* functions and XLogInsert().
 */
void
XLogBeginInsert(void)
{
	Assert(max_registered_block_id == 0);
	Assert(mainrdata_last == (XLogRecData *) &mainrdata_head);
	Assert(mainrdata_len == 0);

	/* cross-check on whether we should be here or not */
	if (!XLogInsertAllowed())
		elog(ERROR, "cannot make new WAL entries during recovery");

	if (begininsert_called)
		elog(ERROR, "XLogBeginInsert was already called");

	begininsert_called = true;
}
```

`access` / `transam` / `xloginsert.c` L237-L302 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L237-L302))

```c
// xloginsert.c L237-L302
/*
 * Register a reference to a buffer with the WAL record being constructed.
 * This must be called for every page that the WAL-logged operation modifies.
 */
void
XLogRegisterBuffer(uint8 block_id, Buffer buffer, uint8 flags)
{
	registered_buffer *regbuf;

	/* NO_IMAGE doesn't make sense with FORCE_IMAGE */
	Assert(!((flags & REGBUF_FORCE_IMAGE) && (flags & (REGBUF_NO_IMAGE))));
	Assert(begininsert_called);

	/*
	 * Ordinarily, buffer should be exclusive-locked and marked dirty before
	 * we get here, otherwise we could end up violating one of the rules in
	 * access/transam/README.
	 *
	 * Some callers intentionally register a clean page and never update that
	 * page's LSN; in that case they can pass the flag REGBUF_NO_CHANGE to
	 * bypass these checks.
	 */
#ifdef USE_ASSERT_CHECKING
	if (!(flags & REGBUF_NO_CHANGE))
		Assert(BufferIsExclusiveLocked(buffer) && BufferIsDirty(buffer));
#endif

	if (block_id >= max_registered_block_id)
	{
		if (block_id >= max_registered_buffers)
			elog(ERROR, "too many registered buffers");
		max_registered_block_id = block_id + 1;
	}

	regbuf = &registered_buffers[block_id];

	BufferGetTag(buffer, &regbuf->rlocator, &regbuf->forkno, &regbuf->block);
	regbuf->page = BufferGetPage(buffer);
	regbuf->flags = flags;
	regbuf->rdata_tail = (XLogRecData *) &regbuf->rdata_head;
	regbuf->rdata_len = 0;

	// ... (L279-L299 생략: 같은 페이지가 다른 block_id 로 이미 등록되지 않았는지 확인 (assert 빌드))

	regbuf->in_use = true;
}
```

`access` / `transam` / `xloginsert.c` L357-L389 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L357-L389))

```c
// xloginsert.c L357-L389
/*
 * Add data to the WAL record that's being constructed.
 *
 * The data is appended to the "main chunk", available at replay with
 * XLogRecGetData().
 */
void
XLogRegisterData(const void *data, uint32 len)
{
	XLogRecData *rdata;

	Assert(begininsert_called);

	if (num_rdatas >= max_rdatas)
		ereport(ERROR,
				(errmsg_internal("too much WAL data"),
				 errdetail_internal("%d out of %d data segments are already in use.",
									num_rdatas, max_rdatas)));
	rdata = &rdatas[num_rdatas++];

	rdata->data = data;
	rdata->len = len;

	/*
	 * we use the mainrdata_last pointer to track the end of the chain, so no
	 * need to clear 'next' here.
	 */

	mainrdata_last->next = rdata;
	mainrdata_last = rdata;

	mainrdata_len += len;
}
```

`access` / `transam` / `xloginsert.c` L391-L443 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L391-L443))

```c
// xloginsert.c L391-L443
/*
 * Add buffer-specific data to the WAL record that's being constructed.
 *
 * Block_id must reference a block previously registered with
 * XLogRegisterBuffer(). If this is called more than once for the same
 * block_id, the data is appended.
 *
 * The maximum amount of data that can be registered per block is 65535
 * bytes. That should be plenty; if you need more than BLCKSZ bytes to
 * reconstruct the changes to the page, you might as well just log a full
 * copy of it. (the "main data" that's not associated with a block is not
 * limited)
 */
void
XLogRegisterBufData(uint8 block_id, const void *data, uint32 len)
{
	registered_buffer *regbuf;
	XLogRecData *rdata;

	Assert(begininsert_called);

	/* find the registered buffer struct */
	regbuf = &registered_buffers[block_id];
	if (!regbuf->in_use)
		elog(ERROR, "no block with id %d registered with WAL insertion",
			 block_id);

	/*
	 * Check against max_rdatas and ensure we do not register more data per
	 * buffer than can be handled by the physical data format; i.e. that
	 * regbuf->rdata_len does not grow beyond what
	 * XLogRecordBlockHeader->data_length can hold.
	 */
	if (num_rdatas >= max_rdatas)
		ereport(ERROR,
				(errmsg_internal("too much WAL data"),
				 errdetail_internal("%d out of %d data segments are already in use.",
									num_rdatas, max_rdatas)));
	if (regbuf->rdata_len + len > UINT16_MAX || len > UINT16_MAX)
		ereport(ERROR,
				(errmsg_internal("too much WAL data"),
				 errdetail_internal("Registering more than maximum %u bytes allowed to block %u: current %u bytes, adding %u bytes.",
									UINT16_MAX, block_id, regbuf->rdata_len, len)));

	rdata = &rdatas[num_rdatas++];

	rdata->data = data;
	rdata->len = len;

	regbuf->rdata_tail->next = rdata;
	regbuf->rdata_tail = rdata;
	regbuf->rdata_len += len;
}
```

본체다.

`access` / `transam` / `xloginsert.c` L462-L530 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L462-L530))

```c
// xloginsert.c L462-L530
/*
 * Insert an XLOG record having the specified RMID and info bytes, with the
 * body of the record being the data and buffer references registered earlier
 * with XLogRegister* calls.
 *
 * Returns XLOG pointer to end of record (beginning of next record).
 * This can be used as LSN for data pages affected by the logged action.
 * (LSN is the XLOG point up to which the XLOG must be flushed to disk
 * before the data page can be written out.  This implements the basic
 * WAL rule "write the log before the data".)
 */
XLogRecPtr
XLogInsert(RmgrId rmid, uint8 info)
{
	XLogRecPtr	EndPos;

	/* XLogBeginInsert() must have been called. */
	if (!begininsert_called)
		elog(ERROR, "XLogBeginInsert was not called");

	/*
	 * The caller can set rmgr bits, XLR_SPECIAL_REL_UPDATE and
	 * XLR_CHECK_CONSISTENCY; the rest are reserved for use by me.
	 */
	if ((info & ~(XLR_RMGR_INFO_MASK |
				  XLR_SPECIAL_REL_UPDATE |
				  XLR_CHECK_CONSISTENCY)) != 0)
		elog(PANIC, "invalid xlog info mask %02X", info);

	TRACE_POSTGRESQL_WAL_INSERT(rmid, info);

	/*
	 * In bootstrap mode, we don't actually log anything but XLOG resources;
	 * return a phony record pointer.
	 */
	if (IsBootstrapProcessingMode() && rmid != RM_XLOG_ID)
	{
		XLogResetInsertion();
		EndPos = SizeOfXLogLongPHD; /* start of 1st chkpt record */
		return EndPos;
	}

	do
	{
		XLogRecPtr	RedoRecPtr;
		bool		doPageWrites;
		bool		topxid_included = false;
		XLogRecPtr	fpw_lsn;
		XLogRecData *rdt;
		int			num_fpi = 0;

		/*
		 * Get values needed to decide whether to do full-page writes. Since
		 * we don't yet have an insertion lock, these could change under us,
		 * but XLogInsertRecord will recheck them once it has a lock.
		 */
		GetFullPageWriteInfo(&RedoRecPtr, &doPageWrites);

		rdt = XLogRecordAssemble(rmid, info, RedoRecPtr, doPageWrites,
								 &fpw_lsn, &num_fpi, &topxid_included);

		EndPos = XLogInsertRecord(rdt, fpw_lsn, curinsert_flags, num_fpi,
								  topxid_included);
	} while (EndPos == InvalidXLogRecPtr);

	XLogResetInsertion();

	return EndPos;
}
```

끝나면 등록 상태를 비운다.

`access` / `transam` / `xloginsert.c` L218-L235 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L218-L235))

```c
// xloginsert.c L218-L235
/*
 * Reset WAL record construction buffers.
 */
void
XLogResetInsertion(void)
{
	int			i;

	for (i = 0; i < max_registered_block_id; i++)
		registered_buffers[i].in_use = false;

	num_rdatas = 0;
	max_registered_block_id = 0;
	mainrdata_len = 0;
	mainrdata_last = (XLogRecData *) &mainrdata_head;
	curinsert_flags = 0;
	begininsert_called = false;
}
```

## 동작 흐름

```text
 XLogBeginInsert                     L149
   L156  복구 중이면 ERROR
   L159  이미 시작했으면 ERROR           레코드는 한 번에 하나
   L162  begininsert_called = true

 XLogRegisterData(data, len)         L364   주 데이터 체인 (mainrdata_head ... mainrdata_last) 에 덧붙임
 XLogRegisterBuffer(id, buf, flags)  L242
   L261  (assert) 버퍼가 배타 잠금이고 dirty 여야 한다
   L273  BufferGetTag -> rlocator, forkno, block
   L274  page = BufferGetPage(buffer)         FPI 판정 때 이 페이지의 LSN 을 본다
 XLogRegisterBufData(id, data, len)  L405   그 블록의 데이터 체인에 덧붙임 (블록당 최대 65535)

 XLogInsert(rmid, info)              L474
   L479  XLogBeginInsert 없이 오면 ERROR
   L486  호출자가 쓸 수 없는 info 비트면 PANIC
   L497  부트스트랩 중이고 XLOG rmgr 가 아니면 가짜 위치를 돌려준다
   L504  do
   L518    GetFullPageWriteInfo(&RedoRecPtr, &doPageWrites)    잠금 없이 읽은 사본
   L520    rdt = XLogRecordAssemble(...)                        --> [07]
   L523    EndPos = XLogInsertRecord(rdt, fpw_lsn, ...)         --> [08]
   L525  while (EndPos == InvalidXLogRecPtr)                    낡은 RedoRecPtr 로 조립했으면 다시
   L527  XLogResetInsertion()
   L529  return EndPos
```

`heap_insert` 한 번이 남기는 등록 상태는 아래와 같다. 이 시점까지 공유 메모리는 건드리지 않았다.

```text
 XLogInsert 직전의 백엔드 지역 상태 (heap_insert, VM 안 바뀜, int4 두 열 행)

 begininsert_called = true      curinsert_flags = XLOG_INCLUDE_ORIGIN

 mainrdata_head --> rdatas[0] { data = &xlrec, len = 3 }     mainrdata_len = 3

 registered_buffers[0]   (max_registered_block_id = 1)
   in_use = true
   flags  = REGBUF_STANDARD (+ REGBUF_WILL_INIT 이면 INIT_PAGE)
   rlocator = (spcOid, dbOid, relNumber of t2), forkno = MAIN, block = 7
   page   --> shared buffer 의 그 페이지 (복사본이 아니다)
   rdata_head --> rdatas[1] { &xlhdr, 5 } --> rdatas[2] { t_data + 23, 9 }
   rdata_len = 14
```

`do ... while` 이 다시 도는 경우는 체크포인트가 그 사이에 시작된 경우다. 조립 때는 "이 페이지는 이미 체크포인트 뒤에 바뀌었으니 FPI 불필요"라고 판단했는데, 넣으려는 순간 새 체크포인트가 RedoRecPtr 를 앞으로 옮겼다면 그 판단이 틀린다.

```text
 재시도가 일어나는 순서 (페이지 LSN = 0/5000100)

 시각  이 백엔드                                       checkpointer
 t1    L518  RedoRecPtr 사본 = 0/5000028
 t2    [07]  page_lsn 0/5000100 > 0/5000028 -> FPI 없음
             fpw_lsn = 0/5000100
 t3                                                    새 체크포인트 시작. Insert->RedoRecPtr = 0/6000028
 t4    [08]  삽입 잠금을 쥐고 보니 RedoRecPtr 가 바뀜
             fpw_lsn 0/5000100 <= 0/6000028 -> InvalidXLogRecPtr  (xlog.c L848-L858)
 t5    L525  다시 돈다. 이번에는 [07] 이 FPI 를 싣는다

 RedoRecPtr 는 redo 레코드의 시작 위치라 세그먼트 첫머리(0/5000000, 0/6000000)일 수 없다.
 세그먼트 첫 페이지의 긴 페이지 헤더 40바이트(0x28) 뒤가 가장 이른 레코드 시작이다 ([09] 의 XLogBytePosToRecPtr)
```

## 결과가 쓰이는 곳

```text
 EndPos (돌려준 LSN)
      --> [02] heap_insert 의 PageSetLSN(page, recptr)
      --> [08] 이 남긴 XactLastRecEnd 와 같은 값. [커밋] 이 flush 할 위치
 XLogResetInsertion
      --> 다음 XLogBeginInsert 가 다시 쓸 수 있게 등록 배열을 비운다
```

## 다루지 않는 것

등록 공간 늘리기(`XLogEnsureRecordSpace`), 공유 버퍼 밖의 블록 등록(`XLogRegisterBlock`), 레코드 플래그(`XLOG_MARK_UNIMPORTANT`), 부트스트랩 모드, 힌트 비트용 FPI(`XLogSaveBufferForHint`)와 페이지 전체 기록(`log_newpage`)은 레코드 만들기의 곁가지라 요약만 했다.
