# XLogInsertRecord

상위: [행 쓰기와 WAL 기록](../README.md)

**조립된 레코드를 공유 WAL 버퍼에 넣는다.** 넣는 일은 두 단계다. 위치 예약은 spinlock 하나로 직렬화하되 덧셈 몇 번으로 끝내고([09]), 바이트 복사는 여러 백엔드가 동시에 한다. 동시 복사를 추적하는 장치가 WAL 삽입 잠금(`WALInsertLocks`, 8개)이다. 삽입하는 백엔드는 그중 하나를 쥐고, 잠금마다 "어디까지 복사했는지"(`insertingAt`)를 적을 수 있다. WAL 을 디스크로 쓰려는 쪽은 이 잠금들을 훑어 아직 복사 중인 구간을 기다린다([10]). 잠금을 쥔 동안 체크포인트 위치(RedoRecPtr)와 full_page_writes 가 바뀌지 않으므로, 조립 때의 FPI 판정이 여전히 맞는지 여기서 다시 확인한다.

## 위치

`access` / `transam` / `xlog.c` L748-L1090 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L748-L1090))

## 실제 코드

앞부분이다. 주석이 두 단계 삽입과 삽입 잠금의 역할을 설명한다.

`access` / `transam` / `xlog.c` L747-L819 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L747-L819))

```c
// xlog.c L747-L819
XLogRecPtr
XLogInsertRecord(XLogRecData *rdata,
				 XLogRecPtr fpw_lsn,
				 uint8 flags,
				 int num_fpi,
				 bool topxid_included)
{
	XLogCtlInsert *Insert = &XLogCtl->Insert;
	pg_crc32c	rdata_crc;
	bool		inserted;
	XLogRecord *rechdr = (XLogRecord *) rdata->data;
	uint8		info = rechdr->xl_info & ~XLR_INFO_MASK;
	WalInsertClass class = WALINSERT_NORMAL;
	XLogRecPtr	StartPos;
	XLogRecPtr	EndPos;
	bool		prevDoPageWrites = doPageWrites;
	TimeLineID	insertTLI;

	// ... (L765-L772 생략: XLOG_SWITCH, CHECKPOINT_REDO 레코드면 특별 취급 표시)

	/* we assume that all of the record header is in the first chunk */
	Assert(rdata->len >= SizeOfXLogRecord);

	/* cross-check on whether we should be here or not */
	if (!XLogInsertAllowed())
		elog(ERROR, "cannot make new WAL entries during recovery");

	/*
	 * Given that we're not in recovery, InsertTimeLineID is set and can't
	 * change, so we can read it without a lock.
	 */
	insertTLI = XLogCtl->InsertTimeLineID;

	/*----------
	 *
	 * We have now done all the preparatory work we can without holding a
	 * lock or modifying shared state. From here on, inserting the new WAL
	 * record to the shared WAL buffer cache is a two-step process:
	 *
	 * 1. Reserve the right amount of space from the WAL. The current head of
	 *	  reserved space is kept in Insert->CurrBytePos, and is protected by
	 *	  insertpos_lck.
	 *
	 * 2. Copy the record to the reserved WAL space. This involves finding the
	 *	  correct WAL buffer containing the reserved space, and copying the
	 *	  record in place. This can be done concurrently in multiple processes.
	 *
	 * To keep track of which insertions are still in-progress, each concurrent
	 * inserter acquires an insertion lock. In addition to just indicating that
	 * an insertion is in progress, the lock tells others how far the inserter
	 * has progressed. There is a small fixed number of insertion locks,
	 * determined by NUM_XLOGINSERT_LOCKS. When an inserter crosses a page
	 * boundary, it updates the value stored in the lock to the how far it has
	 * inserted, to allow the previous buffer to be flushed.
	 *
	 * Holding onto an insertion lock also protects RedoRecPtr and
	 * fullPageWrites from changing until the insertion is finished.
	 *
	 * Step 2 can usually be done completely in parallel. If the required WAL
	 * page is not initialized yet, you have to grab WALBufMappingLock to
	 * initialize it, but the WAL writer tries to do that ahead of insertions
	 * to avoid that from happening in the critical path.
	 *
	 *----------
	 */
	START_CRIT_SECTION();
```

일반 레코드 갈래다. 잠금 하나를 쥐고, FPI 판정이 낡았는지 보고, 위치를 예약한다.

`access` / `transam` / `xlog.c` L821-L870 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L821-L870))

```c
// xlog.c L821-L870
	if (likely(class == WALINSERT_NORMAL))
	{
		WALInsertLockAcquire();

		/*
		 * Check to see if my copy of RedoRecPtr is out of date. If so, may
		 * have to go back and have the caller recompute everything. This can
		 * only happen just after a checkpoint, so it's better to be slow in
		 * this case and fast otherwise.
		 *
		 * Also check to see if fullPageWrites was just turned on or there's a
		 * running backup (which forces full-page writes); if we weren't
		 * already doing full-page writes then go back and recompute.
		 *
		 * If we aren't doing full-page writes then RedoRecPtr doesn't
		 * actually affect the contents of the XLOG record, so we'll update
		 * our local copy but not force a recomputation.  (If doPageWrites was
		 * just turned off, we could recompute the record without full pages,
		 * but we choose not to bother.)
		 */
		if (RedoRecPtr != Insert->RedoRecPtr)
		{
			Assert(RedoRecPtr < Insert->RedoRecPtr);
			RedoRecPtr = Insert->RedoRecPtr;
		}
		doPageWrites = (Insert->fullPageWrites || Insert->runningBackups > 0);

		if (doPageWrites &&
			(!prevDoPageWrites ||
			 (fpw_lsn != InvalidXLogRecPtr && fpw_lsn <= RedoRecPtr)))
		{
			/*
			 * Oops, some buffer now needs to be backed up that the caller
			 * didn't back up.  Start over.
			 */
			WALInsertLockRelease();
			END_CRIT_SECTION();
			return InvalidXLogRecPtr;
		}

		/*
		 * Reserve space for the record in the WAL. This also sets the xl_prev
		 * pointer.
		 */
		ReserveXLogInsertLocation(rechdr->xl_tot_len, &StartPos, &EndPos,
								  &rechdr->xl_prev);

		/* Normal records are always inserted. */
		inserted = true;
	}
```

복사와 마무리다. XLOG_SWITCH 와 체크포인트 레코드 갈래, WAL_DEBUG 출력은 줄였다.

`access` / `transam` / `xlog.c` L907-L1090 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L907-L1090))

```c
// xlog.c L907-L1090
	if (inserted)
	{
		/*
		 * Now that xl_prev has been filled in, calculate CRC of the record
		 * header.
		 */
		rdata_crc = rechdr->xl_crc;
		COMP_CRC32C(rdata_crc, rechdr, offsetof(XLogRecord, xl_crc));
		FIN_CRC32C(rdata_crc);
		rechdr->xl_crc = rdata_crc;

		/*
		 * All the record data, including the header, is now ready to be
		 * inserted. Copy the record in the space reserved.
		 */
		CopyXLogRecordToWAL(rechdr->xl_tot_len,
							class == WALINSERT_SPECIAL_SWITCH, rdata,
							StartPos, EndPos, insertTLI);

		/*
		 * Unless record is flagged as not important, update LSN of last
		 * important record in the current slot. When holding all locks, just
		 * update the first one.
		 */
		if ((flags & XLOG_MARK_UNIMPORTANT) == 0)
		{
			int			lockno = holdingAllLocks ? 0 : MyLockNo;

			WALInsertLocks[lockno].l.lastImportantAt = StartPos;
		}
	}
	// ... (L938-L945 생략: XLOG_SWITCH 인데 이미 세그먼트 시작이라 할 일이 없는 경우)

	/*
	 * Done! Let others know that we're finished.
	 */
	WALInsertLockRelease();

	END_CRIT_SECTION();

	MarkCurrentTransactionIdLoggedIfAny();

	/*
	 * Mark top transaction id is logged (if needed) so that we should not try
	 * to log it again with the next WAL record in the current subtransaction.
	 */
	if (topxid_included)
		MarkSubxactTopXidLogged();

	/*
	 * Update shared LogwrtRqst.Write, if we crossed page boundary.
	 */
	if (StartPos / XLOG_BLCKSZ != EndPos / XLOG_BLCKSZ)
	{
		SpinLockAcquire(&XLogCtl->info_lck);
		/* advance global request to include new block(s) */
		if (XLogCtl->LogwrtRqst.Write < EndPos)
			XLogCtl->LogwrtRqst.Write = EndPos;
		SpinLockRelease(&XLogCtl->info_lck);
		RefreshXLogWriteResult(LogwrtResult);
	}

	// ... (L976-L1070 생략: XLOG_SWITCH 의 flush 와 WAL_DEBUG 출력)

	/*
	 * Update our global variables
	 */
	ProcLastRecPtr = StartPos;
	XactLastRecEnd = EndPos;

	/* Report WAL traffic to the instrumentation. */
	if (inserted)
	{
		pgWalUsage.wal_bytes += rechdr->xl_tot_len;
		pgWalUsage.wal_records++;
		pgWalUsage.wal_fpi += num_fpi;

		/* Required for the flush of pending stats WAL data */
		pgstat_report_fixed = true;
	}

	return EndPos;
}
```

삽입 잠금은 8개 중 하나를 고른다. 지난번에 쓴 것을 먼저 시도하고, 기다려야 했으면 다음에는 옆 것을 쓴다.

`access` / `transam` / `xlog.c` L1370-L1412 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1370-L1412))

```c
// xlog.c L1370-L1412
/*
 * Acquire a WAL insertion lock, for inserting to WAL.
 */
static void
WALInsertLockAcquire(void)
{
	bool		immed;

	/*
	 * It doesn't matter which of the WAL insertion locks we acquire, so try
	 * the one we used last time.  If the system isn't particularly busy, it's
	 * a good bet that it's still available, and it's good to have some
	 * affinity to a particular lock so that you don't unnecessarily bounce
	 * cache lines between processes when there's no contention.
	 *
	 * If this is the first time through in this backend, pick a lock
	 * (semi-)randomly.  This allows the locks to be used evenly if you have a
	 * lot of very short connections.
	 */
	static int	lockToTry = -1;

	if (lockToTry == -1)
		lockToTry = MyProcNumber % NUM_XLOGINSERT_LOCKS;
	MyLockNo = lockToTry;

	/*
	 * The insertingAt value is initially set to 0, as we don't know our
	 * insert location yet.
	 */
	immed = LWLockAcquire(&WALInsertLocks[MyLockNo].l.lock, LW_EXCLUSIVE);
	if (!immed)
	{
		/*
		 * If we couldn't get the lock immediately, try another lock next
		 * time.  On a system with more insertion locks than concurrent
		 * inserters, this causes all the inserters to eventually migrate to a
		 * lock that no-one else is using.  On a system with more inserters
		 * than locks, it still helps to distribute the inserters evenly
		 * across the locks.
		 */
		lockToTry = (lockToTry + 1) % NUM_XLOGINSERT_LOCKS;
	}
}
```

`access` / `transam` / `xlog.c` L1441-L1467 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1441-L1467))

```c
// xlog.c L1441-L1467
/*
 * Release our insertion lock (or locks, if we're holding them all).
 *
 * NB: Reset all variables to 0, so they cause LWLockWaitForVar to block the
 * next time the lock is acquired.
 */
static void
WALInsertLockRelease(void)
{
	if (holdingAllLocks)
	{
		int			i;

		for (i = 0; i < NUM_XLOGINSERT_LOCKS; i++)
			LWLockReleaseClearVar(&WALInsertLocks[i].l.lock,
								  &WALInsertLocks[i].l.insertingAt,
								  0);

		holdingAllLocks = false;
	}
	else
	{
		LWLockReleaseClearVar(&WALInsertLocks[MyLockNo].l.lock,
							  &WALInsertLocks[MyLockNo].l.insertingAt,
							  0);
	}
}
```

예약한 자리로 복사한다. 레코드가 WAL 페이지 경계를 넘으면 다음 페이지 헤더를 건너뛰고 이어 쓴다.

`access` / `transam` / `xlog.c` L1223-L1308 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1223-L1308))

```c
// xlog.c L1223-L1308
/*
 * Subroutine of XLogInsertRecord.  Copies a WAL record to an already-reserved
 * area in the WAL.
 */
static void
CopyXLogRecordToWAL(int write_len, bool isLogSwitch, XLogRecData *rdata,
					XLogRecPtr StartPos, XLogRecPtr EndPos, TimeLineID tli)
{
	char	   *currpos;
	int			freespace;
	int			written;
	XLogRecPtr	CurrPos;
	XLogPageHeader pagehdr;

	/*
	 * Get a pointer to the right place in the right WAL buffer to start
	 * inserting to.
	 */
	CurrPos = StartPos;
	currpos = GetXLogBuffer(CurrPos, tli);
	freespace = INSERT_FREESPACE(CurrPos);

	/*
	 * there should be enough space for at least the first field (xl_tot_len)
	 * on this page.
	 */
	Assert(freespace >= sizeof(uint32));

	/* Copy record data */
	written = 0;
	while (rdata != NULL)
	{
		const char *rdata_data = rdata->data;
		int			rdata_len = rdata->len;

		while (rdata_len > freespace)
		{
			/*
			 * Write what fits on this page, and continue on the next page.
			 */
			Assert(CurrPos % XLOG_BLCKSZ >= SizeOfXLogShortPHD || freespace == 0);
			memcpy(currpos, rdata_data, freespace);
			rdata_data += freespace;
			rdata_len -= freespace;
			written += freespace;
			CurrPos += freespace;

			/*
			 * Get pointer to beginning of next page, and set the xlp_rem_len
			 * in the page header. Set XLP_FIRST_IS_CONTRECORD.
			 *
			 * It's safe to set the contrecord flag and xlp_rem_len without a
			 * lock on the page. All the other flags were already set when the
			 * page was initialized, in AdvanceXLInsertBuffer, and we're the
			 * only backend that needs to set the contrecord flag.
			 */
			currpos = GetXLogBuffer(CurrPos, tli);
			pagehdr = (XLogPageHeader) currpos;
			pagehdr->xlp_rem_len = write_len - written;
			pagehdr->xlp_info |= XLP_FIRST_IS_CONTRECORD;

			/* skip over the page header */
			if (XLogSegmentOffset(CurrPos, wal_segment_size) == 0)
			{
				CurrPos += SizeOfXLogLongPHD;
				currpos += SizeOfXLogLongPHD;
			}
			else
			{
				CurrPos += SizeOfXLogShortPHD;
				currpos += SizeOfXLogShortPHD;
			}
			freespace = INSERT_FREESPACE(CurrPos);
		}

		Assert(CurrPos % XLOG_BLCKSZ >= SizeOfXLogShortPHD || rdata_len == 0);
		memcpy(currpos, rdata_data, rdata_len);
		currpos += rdata_len;
		CurrPos += rdata_len;
		freespace -= rdata_len;
		written += rdata_len;

		rdata = rdata->next;
	}
	Assert(written == write_len);

```

`access` / `transam` / `xlog.c` L1358-L1368 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1358-L1368))

```c
// xlog.c L1358-L1368
	else
	{
		/* Align the end position, so that the next record starts aligned */
		CurrPos = MAXALIGN64(CurrPos);
	}

	if (CurrPos != EndPos)
		ereport(PANIC,
				errcode(ERRCODE_DATA_CORRUPTED),
				errmsg_internal("space reserved for WAL record does not match what was written"));
}
```

## 동작 흐름

```text
 L778  복구 중이면 ERROR
 L785  insertTLI = 현재 타임라인
 L819  START_CRIT_SECTION

 L821  일반 레코드면
 L823    WALInsertLockAcquire()
           L1391  처음이면 MyProcNumber % 8 로 고른다
           L1399  LWLockAcquire(&WALInsertLocks[n].l.lock, LW_EXCLUSIVE)
           L1410  바로 못 잡았으면 다음에는 (n + 1) % 8
 L841    지역 RedoRecPtr 가 공유 값과 다르면 갱신
 L846    doPageWrites = fullPageWrites 또는 진행 중인 백업
 L848    FPI 가 필요해졌는데 조립 때 안 실었으면
 L856      잠금 해제, L858 return InvalidXLogRecPtr      --> [06] 이 다시 조립
 L865    ReserveXLogInsertLocation(xl_tot_len, &StartPos, &EndPos, &rechdr->xl_prev)   --> [09]

 L913  CRC 마무리: 중간 CRC 에 레코드 헤더(xl_crc 앞까지)를 더하고 FIN
 L922  CopyXLogRecordToWAL(xl_tot_len, ..., rdata, StartPos, EndPos, tli)
         L1242  currpos = GetXLogBuffer(StartPos)          WAL 버퍼 안의 주소
         L1253  체인의 조각마다
         L1258    이 페이지에 안 들어가면 들어가는 만큼 쓰고
         L1279    다음 페이지로. xlp_rem_len = 남은 길이, XLP_FIRST_IS_CONTRECORD
         L1285    세그먼트 첫 페이지면 긴 헤더(40), 아니면 짧은 헤더(24)를 건너뛴다
         L1299    memcpy
         L1361  CurrPos = MAXALIGN64(CurrPos)
         L1364  CurrPos != EndPos 면 PANIC                 예약과 복사가 어긋났다
 L931  중요한 레코드면 lastImportantAt = StartPos
 L950  WALInsertLockRelease()                           insertingAt 을 0 으로
 L952  END_CRIT_SECTION

 L954  이 트랜잭션의 XID 가 WAL 에 남았다고 표시
 L966  레코드가 WAL 페이지 경계를 넘었으면
 L971    LogwrtRqst.Write = EndPos                     "여기까지 써 달라" 는 요청을 올린다
 L1075 ProcLastRecPtr = StartPos, L1076 XactLastRecEnd = EndPos
 L1081 pgWalUsage 에 바이트, 레코드 수, FPI 수
 L1089 return EndPos
```

삽입 잠금이 하나가 아니라 여덟 개인 이유는 복사를 병렬로 하기 위해서다. 위치 예약만 짧게 직렬화하고, 각자 다른 구간을 동시에 복사한다.

```text
 WAL 버퍼 위의 동시 삽입 세 개 (NUM_XLOGINSERT_LOCKS = 8, xlog.c L151)

 lock             [0]      [1]      [2]      [3]      [4]      [5]      [6]      [7]
 holder           -        A        -        B        -        -        C        -

 WAL              ... | A: 64 B           | B: 3504 B (FPI)                  | C: 64 B     | ...
                      ^0/6001000          ^0/6001040                         ^0/6001DF0    ^0/6001E30
 reserve          A -> B -> C  (spinlock 아래, [09])
 copy             A 끝남 (잠금 [1] 해제), B 복사 중, C 끝남 (잠금 [6] 해제)   (서로 기다리지 않는다)

 [10] XLogFlush(0/6001E30) 를 부른 쪽은
   잠금 [1] 은 풀렸고, [3] 은 B 가 쥐고 있고, [6] 은 풀렸다
   -> B 가 끝날 때까지 기다린다 (WaitXLogInsertionsToFinish)
```

위 그림의 위치는 같은 WAL 페이지 안이라 페이지 헤더 없이 바이트 위치가 그대로 이어진다(0x1000 + 64 = 0x1040, 0x1040 + 3504 = 0x1DF0, 0x1DF0 + 64 = 0x1E30, 모두 0x2000 = 8192 미만). 페이지 경계를 넘는 레코드는 복사 중간에 다음 페이지의 헤더를 건너뛴다.

```text
 63바이트 레코드가 WAL 페이지 경계를 넘는 경우 (XLOG_BLCKSZ 8192, 짧은 헤더 24)

 StartPos = 0/6001FD8      (페이지 0/6000000 의 오프셋 8152, 남은 자리 40)

 0/6001FD8           0/6002000                          0/6002018           0/6002030
 +-------------------+----------------------------------+-------------------+---+
 | 레코드 앞 40바이트 | 다음 페이지 헤더 24               | 레코드 뒤 23바이트 |패딩|
 +-------------------+----------------------------------+-------------------+---+
                       xlp_rem_len = 63 - 40 = 23
                       xlp_info |= XLP_FIRST_IS_CONTRECORD
                                                         CurrPos = 0/600202F -> MAXALIGN -> 0/6002030
 EndPos = 0/6002030     [09] 의 예약 결과와 같아야 한다 (L1364)
 StartPos / 8192 != EndPos / 8192 이므로 L966 에서 LogwrtRqst.Write 를 올린다
```

## 결과가 쓰이는 곳

```text
 EndPos
      --> [06] 을 거쳐 [02] 의 PageSetLSN
      --> XactLastRecEnd: [커밋] 의 RecordTransactionCommit 이 XLogFlush(XactLastRecEnd)
 WAL 버퍼의 레코드 바이트
      --> [10] XLogWrite 가 파일로 쓴다
 WALInsertLocks[n].insertingAt
      (GetXLogBuffer 가 옛 WAL 버퍼 페이지를 내보내야 할 때 갱신한다, L1628-L1629 주석)
      --> [10] WaitXLogInsertionsToFinish 가 "어디까지 복사가 끝났나" 를 판단한다
 XLogCtl->LogwrtRqst.Write
      --> WAL writer 나 다음 XLogFlush 가 쓸 목표
```

## 다루지 않는 것

WAL 버퍼 페이지를 준비하고 교체하는 일(`GetXLogBuffer`, `AdvanceXLInsertBuffer`, `WALBufMappingLock`), XLOG_SWITCH 와 체크포인트 레코드의 전체 잠금 갈래(`WALInsertLockAcquireExclusive`, `ReserveXLogSwitch`), `WAL_DEBUG` 출력, 타임라인은 삽입의 곁가지라 요약만 했다.
