# RecordTransactionCommit

상위: [커밋](../README.md)

**커밋을 내구성 있게 기록하는 곳이다.** XID 가 있으면 critical section 에 들어가 체크포인트를 붙잡아 두고(`DELAY_CHKPT_START`), [07] 로 commit 레코드를 WAL 에 넣는다. 그다음 `synchronous_commit` 과 상황에 따라 길이 둘로 갈린다. 동기면 `XLogFlush` 로 레코드를 디스크에 내린 뒤 [08] 로 pg_xact 를 COMMITTED 로 바꾸고, 비동기면 flush 를 walwriter 에 맡기고 pg_xact 에 "이 LSN 까지 flush 되기 전에는 CLOG 페이지를 디스크에 쓰지 말라"는 표시를 함께 남긴다. 마지막으로 동기 복제면 [09] 에서 standby 를 기다린다. 이 시점에도 이 트랜잭션은 ProcArray 에 남아 있고 잠금도 쥐고 있다(L1553-L1554 주석).

## 위치

`access` / `transam` / `xact.c` L1314-L1572 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L1314-L1572))

## 실제 코드

`access` / `transam` / `xact.c` L1314-L1572 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L1314-L1572))

```c
// xact.c L1314-L1572
static TransactionId
RecordTransactionCommit(void)
{
	TransactionId xid = GetTopTransactionIdIfAny();
	bool		markXidCommitted = TransactionIdIsValid(xid);
	TransactionId latestXid = InvalidTransactionId;
	int			nrels;
	RelFileLocator *rels;
	int			nchildren;
	TransactionId *children;
	int			ndroppedstats = 0;
	xl_xact_stats_item *droppedstats = NULL;
	int			nmsgs = 0;
	SharedInvalidationMessage *invalMessages = NULL;
	bool		RelcacheInitFileInval = false;
	bool		wrote_xlog;

	// ... (L1331-L1340 생략: 논리 디코딩용 무효화 기록)
	/* Get data needed for commit record */
	nrels = smgrGetPendingDeletes(true, &rels);
	nchildren = xactGetCommittedChildren(&children);
	ndroppedstats = pgstat_get_transactional_drops(true, &droppedstats);
	if (XLogStandbyInfoActive())
		nmsgs = xactGetCommittedInvalidationMessages(&invalMessages,
													 &RelcacheInitFileInval);
	wrote_xlog = (XactLastRecEnd != 0);

	/*
	 * If we haven't been assigned an XID yet, we neither can, nor do we want
	 * to write a COMMIT record.
	 */
	if (!markXidCommitted)
	{
		// ... (L1356-L1396 생략: XID 없는 트랜잭션의 검사와 standby 용 무효화 레코드)

		/*
		 * If we didn't create XLOG entries, we're done here; otherwise we
		 * should trigger flushing those entries the same as a commit record
		 * would.  This will primarily happen for HOT pruning and the like; we
		 * want these to be flushed to disk in due time.
		 */
		if (!wrote_xlog)
			goto cleanup;
	}
	else
	{
		// ... (L1409-L1417 생략: 복제 origin 판정)
		/*
		 * Mark ourselves as within our "commit critical section".  This
		 * forces any concurrent checkpoint to wait until we've updated
		 * pg_xact.  Without this, it is possible for the checkpoint to set
		 * REDO after the XLOG record but fail to flush the pg_xact update to
		 * disk, leading to loss of the transaction commit if the system
		 * crashes a little later.
		 *
		 * Note: we could, but don't bother to, set this flag in
		 * RecordTransactionAbort.  That's because loss of a transaction abort
		 * is noncritical; the presumption would be that it aborted, anyway.
		 *
		 * It's safe to change the delayChkptFlags flag of our own backend
		 * without holding the ProcArrayLock, since we're the only one
		 * modifying it.  This makes checkpoint's determination of which xacts
		 * are delaying the checkpoint a bit fuzzy, but it doesn't matter.
		 */
		Assert((MyProc->delayChkptFlags & DELAY_CHKPT_START) == 0);
		START_CRIT_SECTION();
		MyProc->delayChkptFlags |= DELAY_CHKPT_START;

		/*
		 * Insert the commit XLOG record.
		 */
		XactLogCommitRecord(GetCurrentTransactionStopTimestamp(),
							nchildren, children, nrels, rels,
							ndroppedstats, droppedstats,
							nmsgs, invalMessages,
							RelcacheInitFileInval,
							MyXactFlags,
							InvalidTransactionId, NULL /* plain commit */ );

		// ... (L1450-L1470 생략: 복제 origin LSN 전진과 커밋 타임스탬프 기록)
	}

	/*
	 * Check if we want to commit asynchronously.  We can allow the XLOG flush
	 * to happen asynchronously if synchronous_commit=off, or if the current
	 * transaction has not performed any WAL-logged operation or didn't assign
	 * an xid.  The transaction can end up not writing any WAL, even if it has
	 * an xid, if it only wrote to temporary and/or unlogged tables.  It can
	 * end up having written WAL without an xid if it did HOT pruning.  In
	 * case of a crash, the loss of such a transaction will be irrelevant;
	 * temp tables will be lost anyway, unlogged tables will be truncated and
	 * HOT pruning will be done again later. (Given the foregoing, you might
	 * think that it would be unnecessary to emit the XLOG record at all in
	 * this case, but we don't currently try to do that.  It would certainly
	 * cause problems at least in Hot Standby mode, where the
	 * KnownAssignedXids machinery requires tracking every XID assignment.  It
	 * might be OK to skip it only when wal_level < replica, but for now we
	 * don't.)
	 *
	 * However, if we're doing cleanup of any non-temp rels or committing any
	 * command that wanted to force sync commit, then we must flush XLOG
	 * immediately.  (We must not allow asynchronous commit if there are any
	 * non-temp tables to be deleted, because we might delete the files before
	 * the COMMIT record is flushed to disk.  We do allow asynchronous commit
	 * if all to-be-deleted tables are temporary though, since they are lost
	 * anyway if we crash.)
	 */
	if ((wrote_xlog && markXidCommitted &&
		 synchronous_commit > SYNCHRONOUS_COMMIT_OFF) ||
		forceSyncCommit || nrels > 0)
	{
		XLogFlush(XactLastRecEnd);

		/*
		 * Now we may update the CLOG, if we wrote a COMMIT record above
		 */
		if (markXidCommitted)
			TransactionIdCommitTree(xid, nchildren, children);
	}
	else
	{
		/*
		 * Asynchronous commit case:
		 *
		 * This enables possible committed transaction loss in the case of a
		 * postmaster crash because WAL buffers are left unwritten. Ideally we
		 * could issue the WAL write without the fsync, but some
		 * wal_sync_methods do not allow separate write/fsync.
		 *
		 * Report the latest async commit LSN, so that the WAL writer knows to
		 * flush this commit.
		 */
		XLogSetAsyncXactLSN(XactLastRecEnd);

		/*
		 * We must not immediately update the CLOG, since we didn't flush the
		 * XLOG. Instead, we store the LSN up to which the XLOG must be
		 * flushed before the CLOG may be updated.
		 */
		if (markXidCommitted)
			TransactionIdAsyncCommitTree(xid, nchildren, children, XactLastRecEnd);
	}

	/*
	 * If we entered a commit critical section, leave it now, and let
	 * checkpoints proceed.
	 */
	if (markXidCommitted)
	{
		MyProc->delayChkptFlags &= ~DELAY_CHKPT_START;
		END_CRIT_SECTION();
	}

	/* Compute latestXid while we have the child XIDs handy */
	latestXid = TransactionIdLatest(xid, nchildren, children);

	/*
	 * Wait for synchronous replication, if required. Similar to the decision
	 * above about using committing asynchronously we only want to wait if
	 * this backend assigned an xid and wrote WAL.  No need to wait if an xid
	 * was assigned due to temporary/unlogged tables or due to HOT pruning.
	 *
	 * Note that at this stage we have marked clog, but still show as running
	 * in the procarray and continue to hold locks.
	 */
	if (wrote_xlog && markXidCommitted)
		SyncRepWaitForLSN(XactLastRecEnd, true);

	/* remember end of last commit record */
	XactLastCommitEnd = XactLastRecEnd;

	/* Reset XactLastRecEnd until the next transaction writes something */
	XactLastRecEnd = 0;
cleanup:
	/* Clean up local data */
	if (rels)
		pfree(rels);
	if (ndroppedstats)
		pfree(droppedstats);

	return latestXid;
}
```

## 동작 흐름

```text
 RecordTransactionCommit
 L1317  xid = GetTopTransactionIdIfAny()          [03] 을 거쳤으면 유효
 L1342  nrels = smgrGetPendingDeletes             커밋하면 지울 파일 (DROP TABLE)
 L1343  nchildren = 커밋된 서브 XID
 L1348  wrote_xlog = (XactLastRecEnd != 0)        이 트랜잭션이 WAL 을 썼나
 L1354  XID 없음
          WAL 을 안 썼으면 L1405 goto cleanup       읽기 전용: 아무것도 안 남긴다
          HOT pruning 등으로 WAL 을 썼으면 아래 비동기 갈래로 (commit 레코드는 없음)
 L1407  XID 있음
          L1436  START_CRIT_SECTION
          L1437  delayChkptFlags |= DELAY_CHKPT_START
          L1442  [07] XactLogCommitRecord          XactLastRecEnd = 레코드 끝 LSN
 L1498  동기 조건이면
          L1502  XLogFlush(XactLastRecEnd)
          L1508  [08] TransactionIdCommitTree
        아니면
          L1523  XLogSetAsyncXactLSN               walwriter 에게 이 LSN 까지 flush 하라고 알린다
          L1531  TransactionIdAsyncCommitTree      pg_xact 비트 + group_lsn
 L1540  DELAY_CHKPT_START 해제, END_CRIT_SECTION
 L1545  latestXid = TransactionIdLatest(xid, children)
 L1557  [09] SyncRepWaitForLSN                    WAL 을 썼고 XID 가 있을 때만
 L1560  XactLastCommitEnd = XactLastRecEnd
```

flush 를 할지는 L1498-L1500 의 조건 하나가 정한다. 설정만이 아니라 "지울 파일이 있나"와 "강제 동기 요청이 있나"도 함께 본다.

```text
 (wrote_xlog && markXidCommitted && synchronous_commit > OFF) || forceSyncCommit || nrels > 0

 case                          wrote_xlog  xid  sync_commit  nrels  result  이유 (L1473-L1497 주석)
 INSERT, sync_commit=on        true        yes  on           0      flush   기본
 INSERT, sync_commit=off       true        yes  off          0      async   크래시 때 잃을 수 있음을 받아들인다
 DROP TABLE, sync_commit=off   true        yes  off          1      flush   flush 전에 파일을 지우면 안 된다
 temp/unlogged tables only     false       yes  on           0      async   잃어도 상관없는 데이터
 HOT prune during SELECT       true        no   on           0      async   다시 pruning 하면 된다

 wrote_xlog 는 commit 레코드를 넣기 전(L1348)에 정해진다
```

`synchronous_commit` 값은 이 함수에서는 OFF 냐 아니냐만 보고, 나머지 단계는 [09] 가 쓰는 `SyncRepWaitMode` 로 바뀐다(syncrep.c L1123-L1141).

```text
 setting       SyncCommitLevel (xact.h L68-L77)   local XLogFlush   SyncRepWaitMode       client 가 응답 받기 전 기다리는 것
 off           OFF (0)                            no                NO_WAIT (-1)          없음
 local         LOCAL_FLUSH (1)                    yes               NO_WAIT               로컬 디스크
 remote_write  REMOTE_WRITE (2)                   yes               WAIT_WRITE (0)        로컬 디스크 + standby 의 write
 on (default)  REMOTE_FLUSH (3)                   yes               WAIT_FLUSH (1)        로컬 디스크 + standby 의 flush
 remote_apply  REMOTE_APPLY (4)                   yes               WAIT_APPLY (2)        로컬 디스크 + standby 의 적용

 standby 대기는 synchronous_standby_names 가 설정됐을 때만 일어난다. 없으면 on 도 local 과 같다
```

`DELAY_CHKPT_START` 를 세우는 이유는 L1418-L1434 주석에 있다. 이게 없으면 체크포인트가 REDO 지점을 commit 레코드 뒤로 잡고도 pg_xact 갱신은 디스크에 못 내린 채 끝날 수 있다.

```text
 DELAY_CHKPT_START 가 없다면

 backend       L1442 commit 레코드를 쓴다 (LSN 1000)
 checkpointer  REDO = 1010 으로 잡는다 (commit 레코드 뒤)
 checkpointer  CLOG 를 flush 한다 - 아직 COMMITTED 비트가 없다
 checkpointer  체크포인트 완료
 backend       L1508 pg_xact = COMMITTED (메모리만)
 --- 크래시 ---
 복구는 REDO 1010 부터 재생 -> commit 레코드(1000)를 다시 읽지 않는다
 pg_xact 에는 COMMITTED 가 없다 -> 커밋이 사라진다

 DELAY_CHKPT_START 가 있으면 체크포인트는 이 플래그가 내려갈 때(L1540)까지 기다린다
```

## 결과가 쓰이는 곳

```text
 XactLastRecEnd (commit 레코드 끝 LSN)
      --> [09] SyncRepWaitForLSN 의 대기 기준
      --> 비동기면 XLogSetAsyncXactLSN 으로 walwriter 가 flush 할 목표
 pg_xact 비트
      --> TransactionIdDidCommit ([MVCC 가시성 10](../../mvcc-visibility/10_TransactionIdDidCommit/README.md))
 latestXid
      --> [05] 를 거쳐 [10] ProcArrayEndTransaction 의 latestCompletedXid 갱신
```

## 다루지 않는 것

XID 없는 트랜잭션의 standby 무효화 레코드(`LogStandbyInvalidations`), 복제 origin(`replorigin_session_advance`), 커밋 타임스탬프(`TransactionTreeSetCommitTsData`, `track_commit_timestamp`), 체크포인트가 `DELAY_CHKPT_START` 를 기다리는 쪽(`GetVirtualXIDsDelayingChkpt`)은 다루지 않았다. `XLogFlush` 자체는 [행 쓰기와 WAL 기록 10](../../heap-insert-wal/10_XLogFlush/README.md)에 있다.
