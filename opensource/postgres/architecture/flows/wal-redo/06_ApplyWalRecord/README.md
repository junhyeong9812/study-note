# ApplyWalRecord

상위: [WAL redo (복구)](../README.md)

**레코드 하나를 적용하는 함수이고, 실제 적용은 레코드 헤더의 `xl_rmid` 로 resource manager 표를 찾아 `rm_redo` 를 부르는 한 줄(L2020)이다.** 그 앞뒤로 복구 상태를 관리한다. 적용 전에 `replayEndRecPtr` 를 올려 두고(이 사이에 데이터 페이지를 쓰면 `minRecoveryPoint` 가 이 값까지 오른다), 적용 뒤에 `lastReplayedEndRecPtr` 를 올려 "여기까지 재생했다"를 공개한다. timeline 을 바꾸는 체크포인트, end-of-recovery 레코드는 적용 전에 알아본다.

## 위치

`src/backend/access/transam` / `xlogrecovery.c` L1936-L2094 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L1936-L2094))

## 실제 코드

```c
// transam/xlogrecovery.c L1936-L2094
static void
ApplyWalRecord(XLogReaderState *xlogreader, XLogRecord *record, TimeLineID *replayTLI)
{
	ErrorContextCallback errcallback;
	bool		switchedTLI = false;

	/* Setup error traceback support for ereport() */
	errcallback.callback = rm_redo_error_callback;
	errcallback.arg = xlogreader;
	errcallback.previous = error_context_stack;
	error_context_stack = &errcallback;

	/*
	 * TransamVariables->nextXid must be beyond record's xid.
	 */
	AdvanceNextFullTransactionIdPastXid(record->xl_xid);

	/*
	 * Before replaying this record, check if this record causes the current
	 * timeline to change. The record is already considered to be part of the
	 * new timeline, so we update replayTLI before replaying it. That's
	 * important so that replayEndTLI, which is recorded as the minimum
	 * recovery point's TLI if recovery stops after this record, is set
	 * correctly.
	 */
	if (record->xl_rmid == RM_XLOG_ID)
	{
		TimeLineID	newReplayTLI = *replayTLI;
		TimeLineID	prevReplayTLI = *replayTLI;
		uint8		info = record->xl_info & ~XLR_INFO_MASK;

		if (info == XLOG_CHECKPOINT_SHUTDOWN)
		{
			CheckPoint	checkPoint;

			memcpy(&checkPoint, XLogRecGetData(xlogreader), sizeof(CheckPoint));
			newReplayTLI = checkPoint.ThisTimeLineID;
			prevReplayTLI = checkPoint.PrevTimeLineID;
		}
		else if (info == XLOG_END_OF_RECOVERY)
		{
			xl_end_of_recovery xlrec;

			memcpy(&xlrec, XLogRecGetData(xlogreader), sizeof(xl_end_of_recovery));
			newReplayTLI = xlrec.ThisTimeLineID;
			prevReplayTLI = xlrec.PrevTimeLineID;
		}

		if (newReplayTLI != *replayTLI)
		{
			/* Check that it's OK to switch to this TLI */
			checkTimeLineSwitch(xlogreader->EndRecPtr,
								newReplayTLI, prevReplayTLI, *replayTLI);

			/* Following WAL records should be run with new TLI */
			*replayTLI = newReplayTLI;
			switchedTLI = true;
		}
	}

	/*
	 * Update shared replayEndRecPtr before replaying this record, so that
	 * XLogFlush will update minRecoveryPoint correctly.
	 */
	SpinLockAcquire(&XLogRecoveryCtl->info_lck);
	XLogRecoveryCtl->replayEndRecPtr = xlogreader->EndRecPtr;
	XLogRecoveryCtl->replayEndTLI = *replayTLI;
	SpinLockRelease(&XLogRecoveryCtl->info_lck);

	/*
	 * If we are attempting to enter Hot Standby mode, process XIDs we see
	 */
	if (standbyState >= STANDBY_INITIALIZED &&
		TransactionIdIsValid(record->xl_xid))
		RecordKnownAssignedTransactionIds(record->xl_xid);

	/*
	 * Some XLOG record types that are related to recovery are processed
	 * directly here, rather than in xlog_redo()
	 */
	if (record->xl_rmid == RM_XLOG_ID)
		xlogrecovery_redo(xlogreader, *replayTLI);

	/* Now apply the WAL record itself */
	GetRmgr(record->xl_rmid).rm_redo(xlogreader);

	/*
	 * After redo, check whether the backup pages associated with the WAL
	 * record are consistent with the existing pages. This check is done only
	 * if consistency check is enabled for this record.
	 */
	if ((record->xl_info & XLR_CHECK_CONSISTENCY) != 0)
		verifyBackupPageConsistency(xlogreader);

	/* Pop the error context stack */
	error_context_stack = errcallback.previous;

	/*
	 * Update lastReplayedEndRecPtr after this record has been successfully
	 * replayed.
	 */
	SpinLockAcquire(&XLogRecoveryCtl->info_lck);
	XLogRecoveryCtl->lastReplayedReadRecPtr = xlogreader->ReadRecPtr;
	XLogRecoveryCtl->lastReplayedEndRecPtr = xlogreader->EndRecPtr;
	XLogRecoveryCtl->lastReplayedTLI = *replayTLI;
	SpinLockRelease(&XLogRecoveryCtl->info_lck);

	// ... (L2043-L2077 생략: walsender 와 walreceiver 깨우기 (cascading, reply 요청))

	/* Allow read-only connections if we're consistent now */
	CheckRecoveryConsistency();

	/* Is this a timeline switch? */
	if (switchedTLI)
	{
		/*
		 * Before we continue on the new timeline, clean up any (possibly
		 * bogus) future WAL segments on the old timeline.
		 */
		RemoveNonParentXlogFiles(xlogreader->EndRecPtr, *replayTLI);

		/* Reset the prefetcher. */
		XLogPrefetchReconfigure();
	}
}
```

resource manager 표는 `rmgrlist.h` 를 매크로로 펼쳐 만든다. 배열 첨자가 `xl_rmid` 다.

`src/backend/access/transam` / `rmgr.c` L46-L52 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/rmgr.c#L46-L52))

```c
// transam/rmgr.c L46-L52
/* must be kept in sync with RmgrData definition in xlog_internal.h */
#define PG_RMGR(symname,name,redo,desc,identify,startup,cleanup,mask,decode) \
	{ name, redo, desc, identify, startup, cleanup, mask, decode },

RmgrData	RmgrTable[RM_MAX_ID + 1] = {
#include "access/rmgrlist.h"
};
```

`src/include/access` / `rmgrlist.h` L27-L38 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/rmgrlist.h#L27-L38))

```c
// access/rmgrlist.h L27-L38
/* symbol name, textual name, redo, desc, identify, startup, cleanup, mask, decode */
PG_RMGR(RM_XLOG_ID, "XLOG", xlog_redo, xlog_desc, xlog_identify, NULL, NULL, NULL, xlog_decode)
PG_RMGR(RM_XACT_ID, "Transaction", xact_redo, xact_desc, xact_identify, NULL, NULL, NULL, xact_decode)
PG_RMGR(RM_SMGR_ID, "Storage", smgr_redo, smgr_desc, smgr_identify, NULL, NULL, NULL, NULL)
PG_RMGR(RM_CLOG_ID, "CLOG", clog_redo, clog_desc, clog_identify, NULL, NULL, NULL, NULL)
PG_RMGR(RM_DBASE_ID, "Database", dbase_redo, dbase_desc, dbase_identify, NULL, NULL, NULL, NULL)
PG_RMGR(RM_TBLSPC_ID, "Tablespace", tblspc_redo, tblspc_desc, tblspc_identify, NULL, NULL, NULL, NULL)
PG_RMGR(RM_MULTIXACT_ID, "MultiXact", multixact_redo, multixact_desc, multixact_identify, NULL, NULL, NULL, NULL)
PG_RMGR(RM_RELMAP_ID, "RelMap", relmap_redo, relmap_desc, relmap_identify, NULL, NULL, NULL, NULL)
PG_RMGR(RM_STANDBY_ID, "Standby", standby_redo, standby_desc, standby_identify, NULL, NULL, NULL, standby_decode)
PG_RMGR(RM_HEAP2_ID, "Heap2", heap2_redo, heap2_desc, heap2_identify, NULL, NULL, heap_mask, heap2_decode)
PG_RMGR(RM_HEAP_ID, "Heap", heap_redo, heap_desc, heap_identify, NULL, NULL, heap_mask, heap_decode)
```

## 동작 흐름

```text
 ApplyWalRecord(xlogreader, record, &replayTLI)

 L1943-L1946  에러 문맥에 rm_redo_error_callback   에러 메시지에 "WAL redo at ... for Heap/INSERT" 를 붙인다
 L1951  AdvanceNextFullTransactionIdPastXid(xl_xid)  nextXid 가 이 레코드의 xid 를 넘도록
 L1961  RM_XLOG_ID 면 timeline 전환 확인
          CHECKPOINT_SHUTDOWN, END_OF_RECOVERY 레코드의 ThisTimeLineID 가 다르면
          checkTimeLineSwitch 후 replayTLI 교체
 L2000-L2003  replayEndRecPtr = EndRecPtr          ---- 적용 전 ----
 L2008  hot standby 준비 중이면 RecordKnownAssignedTransactionIds
 L2016  RM_XLOG_ID 면 xlogrecovery_redo            backup end, overwrite contrecord 등 복구 쪽 일
 L2020  GetRmgr(xl_rmid).rm_redo(xlogreader)       ---- 적용 ----
 L2027  XLR_CHECK_CONSISTENCY 면 verifyBackupPageConsistency   wal_consistency_checking
 L2037-L2041  lastReplayedEndRecPtr = EndRecPtr    ---- 적용 후 ----
 L2080  CheckRecoveryConsistency                   일관 지점을 넘었으면 읽기 전용 연결 허용
 L2083  timeline 이 바뀌었으면 옛 timeline 의 미래 세그먼트 정리
```

`rm_redo` 디스패치를 레코드 몇 개로 따라가면 이렇다. `xl_rmid` 는 `rmgrlist.h` 의 줄 순서(0 부터)다.

```text
 xl_rmid  rmgr         xl_info & ~XLR_INFO_MASK         rm_redo        다음
 0        XLOG         0x10 CHECKPOINT_ONLINE           xlog_redo      RecoveryRestartPoint 에 체크포인트 기록
 1        Transaction  0x00 XLOG_XACT_COMMIT            xact_redo      pg_xact 에 committed
 10       Heap         0x00 XLOG_HEAP_INSERT            heap_redo      [07] -> [08] heap_xlog_insert
 10       Heap         0x80 INSERT | INIT_PAGE          heap_redo      페이지를 새로 초기화하고 넣는다
 11       Btree        0x00 XLOG_BTREE_INSERT_LEAF      btree_redo     nbtree 리프에 다시 넣는다
```

적용 전후 두 변수가 따로 있는 이유는 주석 L1996-L1998 에 있다. 적용 도중에 버퍼가 디스크로 나가면 `XLogFlush` 가 `minRecoveryPoint` 를 올리는데, 그 기준이 "지금 재생 중인 레코드의 끝"이어야 하기 때문이다.

```text
 레코드 R (EndRecPtr = 0/3D2A0F68) 적용 중, 아카이브 복구 / standby

 시각  누가        하는 일
 t1    startup     replayEndRecPtr = 0/3D2A0F68
 t2    startup     heap_xlog_insert: 페이지 P 갱신, PageSetLSN(P, 0/3D2A0F68), MarkBufferDirty
 t3    checkpointer restartpoint 의 BufferSync 가 P 를 FlushBuffer
                   XLogFlush(0/3D2A0F68) 는 복구 중이라 WAL 대신 minRecoveryPoint 를 올린다 (xlog.c L2793)
                   새 값은 GetCurrentReplayRecPtr = replayEndRecPtr = 0/3D2A0F68 (xlog.c L2749)
 t4    startup     lastReplayedEndRecPtr = 0/3D2A0F68

 여기서 멈췄다 다시 기동하면 0/3D2A0F68 까지 재생하기 전에는 일관 상태가 아니다
 디스크의 P 가 이미 그 LSN 의 내용을 담고 있기 때문이다
```

## 결과가 쓰이는 곳

```text
 rm_redo 가 고친 페이지
      --> 공유 버퍼에 BM_DIRTY. restartpoint 나 end-of-recovery 체크포인트가 내려 쓴다
 lastReplayedEndRecPtr, lastReplayedTLI
      --> [04] 의 다음 반복, GetXLogReplayRecPtr, CheckRecoveryConsistency
 replayEndRecPtr
      --> 복구 중 XLogFlush 가 부르는 UpdateMinRecoveryPoint (xlog.c L2793-L2797, L2749)
 replayTLI
      --> 다음 [05] ReadRecord 의 기대 timeline
```

## 다루지 않는 것

`xlog_redo` 와 `xlogrecovery_redo` 의 레코드별 처리(backup end, parameter change, restore point), `RecordKnownAssignedTransactionIds`, `verifyBackupPageConsistency`, `checkTimeLineSwitch` 는 요약만 했다. heap 외 resource manager 의 redo 함수는 다루지 않는다.
