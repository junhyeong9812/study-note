# CreateCheckPoint

상위: [체크포인트](../README.md)

**체크포인트 하나의 처음과 끝을 모두 맡는 함수다.** REDO 지점을 정하고(온라인이면 `XLOG_CHECKPOINT_REDO` 레코드를 넣어서), 실제 쓰기는 `CheckPointGuts` 에 맡기고, 체크포인트 레코드를 넣어 flush 한 뒤 `pg_control` 을 갱신하고, 마지막으로 필요 없어진 WAL 세그먼트를 치운다. 순서가 핵심이다. REDO 지점은 쓰기를 시작하기 **전에** 정해지고, `pg_control` 은 쓰기와 fsync 가 모두 끝난 **뒤에** 바뀐다(머리 주석 L6908-L6917).

## 위치

`src/backend/access/transam` / `xlog.c` L6928-L7406 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L6928-L7406))

## 실제 코드

```c
// transam/xlog.c L6928-L7406
bool
CreateCheckPoint(int flags)
{
	bool		shutdown;
	CheckPoint	checkPoint;
	XLogRecPtr	recptr;
	XLogSegNo	_logSegNo;
	XLogCtlInsert *Insert = &XLogCtl->Insert;
	uint32		freespace;
	XLogRecPtr	PriorRedoPtr;
	XLogRecPtr	last_important_lsn;
	VirtualTransactionId *vxids;
	int			nvxids;
	int			oldXLogAllowed = 0;

	/*
	 * An end-of-recovery checkpoint is really a shutdown checkpoint, just
	 * issued at a different time.
	 */
	if (flags & (CHECKPOINT_IS_SHUTDOWN | CHECKPOINT_END_OF_RECOVERY))
		shutdown = true;
	else
		shutdown = false;

	/* sanity check */
	if (RecoveryInProgress() && (flags & CHECKPOINT_END_OF_RECOVERY) == 0)
		elog(ERROR, "can't create a checkpoint during recovery");

	// ... (L6956-L6965 생략: CheckpointStats 초기화)
	/*
	 * Let smgr prepare for checkpoint; this has to happen outside the
	 * critical section and before we determine the REDO pointer.  Note that
	 * smgr must not do anything that'd have to be undone if we decide no
	 * checkpoint is needed.
	 */
	SyncPreCheckpoint();

	/*
	 * Use a critical section to force system panic if we have trouble.
	 */
	START_CRIT_SECTION();

	if (shutdown)
	{
		LWLockAcquire(ControlFileLock, LW_EXCLUSIVE);
		ControlFile->state = DB_SHUTDOWNING;
		UpdateControlFile();
		LWLockRelease(ControlFileLock);
	}

	/* Begin filling in the checkpoint WAL record */
	MemSet(&checkPoint, 0, sizeof(checkPoint));
	checkPoint.time = (pg_time_t) time(NULL);

	// ... (L6991-L6999 생략: Hot Standby 용 oldestActiveXid)

	/*
	 * Get location of last important record before acquiring insert locks (as
	 * GetLastImportantRecPtr() also locks WAL locks).
	 */
	last_important_lsn = GetLastImportantRecPtr();

	/*
	 * If this isn't a shutdown or forced checkpoint, and if there has been no
	 * WAL activity requiring a checkpoint, skip it.  The idea here is to
	 * avoid inserting duplicate checkpoints when the system is idle.
	 */
	if ((flags & (CHECKPOINT_IS_SHUTDOWN | CHECKPOINT_END_OF_RECOVERY |
				  CHECKPOINT_FORCE)) == 0)
	{
		if (last_important_lsn == ControlFile->checkPoint)
		{
			END_CRIT_SECTION();
			ereport(DEBUG1,
					(errmsg_internal("checkpoint skipped because system is idle")));
			return false;
		}
	}

	// ... (L7024-L7036 생략: end-of-recovery 때 WAL 쓰기 임시 허용, timeline ID 채우기)

	/*
	 * We must block concurrent insertions while examining insert state.
	 */
	WALInsertLockAcquireExclusive();

	checkPoint.fullPageWrites = Insert->fullPageWrites;
	checkPoint.wal_level = wal_level;

	if (shutdown)
	{
		XLogRecPtr	curInsert = XLogBytePosToRecPtr(Insert->CurrBytePos);

		/*
		 * Compute new REDO record ptr = location of next XLOG record.
		 *
		 * Since this is a shutdown checkpoint, there can't be any concurrent
		 * WAL insertion.
		 */
		freespace = INSERT_FREESPACE(curInsert);
		if (freespace == 0)
		{
			if (XLogSegmentOffset(curInsert, wal_segment_size) == 0)
				curInsert += SizeOfXLogLongPHD;
			else
				curInsert += SizeOfXLogShortPHD;
		}
		checkPoint.redo = curInsert;

		/*
		 * Here we update the shared RedoRecPtr for future XLogInsert calls;
		 * this must be done while holding all the insertion locks.
		 *
		 * Note: if we fail to complete the checkpoint, RedoRecPtr will be
		 * left pointing past where it really needs to point.  This is okay;
		 * the only consequence is that XLogInsert might back up whole buffers
		 * that it didn't really need to.  We can't postpone advancing
		 * RedoRecPtr because XLogInserts that happen while we are dumping
		 * buffers must assume that their buffer changes are not included in
		 * the checkpoint.
		 */
		RedoRecPtr = XLogCtl->Insert.RedoRecPtr = checkPoint.redo;
	}

	/*
	 * Now we can release the WAL insertion locks, allowing other xacts to
	 * proceed while we are flushing disk buffers.
	 */
	WALInsertLockRelease();

	/*
	 * If this is an online checkpoint, we have not yet determined the redo
	 * point. We do so now by inserting the special XLOG_CHECKPOINT_REDO
	 * record; the LSN at which it starts becomes the new redo pointer. We
	 * don't do this for a shutdown checkpoint, because in that case no WAL
	 * can be written between the redo point and the insertion of the
	 * checkpoint record itself, so the checkpoint record itself serves to
	 * mark the redo point.
	 */
	if (!shutdown)
	{
		/* Include WAL level in record for WAL summarizer's benefit. */
		XLogBeginInsert();
		XLogRegisterData(&wal_level, sizeof(wal_level));
		(void) XLogInsert(RM_XLOG_ID, XLOG_CHECKPOINT_REDO);

		/*
		 * XLogInsertRecord will have updated XLogCtl->Insert.RedoRecPtr in
		 * shared memory and RedoRecPtr in backend-local memory, but we need
		 * to copy that into the record that will be inserted when the
		 * checkpoint is complete.
		 */
		checkPoint.redo = RedoRecPtr;
	}

	/* Update the info_lck-protected copy of RedoRecPtr as well */
	SpinLockAcquire(&XLogCtl->info_lck);
	XLogCtl->RedoRecPtr = checkPoint.redo;
	SpinLockRelease(&XLogCtl->info_lck);

	// ... (L7117-L7158 생략: log_checkpoints 시작 로그, ps 표시, nextXid, nextOid, multixact 등 CheckPoint 필드 채우기)

	/*
	 * Having constructed the checkpoint record, ensure all shmem disk buffers
	 * and commit-log buffers are flushed to disk.
	 *
	 * This I/O could fail for various reasons.  If so, we will fail to
	 * complete the checkpoint, but there is no reason to force a system
	 * panic. Accordingly, exit critical section while doing it.
	 */
	END_CRIT_SECTION();

	/*
	 * In some cases there are groups of actions that must all occur on one
	 * side or the other of a checkpoint record. Before flushing the
	 * checkpoint record we must explicitly wait for any backend currently
	 * performing those groups of actions.
	 *
	 * One example is end of transaction, so we must wait for any transactions
	 * that are currently in commit critical sections.  If an xact inserted
	 * its commit record into XLOG just before the REDO point, then a crash
	 * restart from the REDO point would not replay that record, which means
	 * that our flushing had better include the xact's update of pg_xact.  So
	 * we wait till he's out of his commit critical section before proceeding.
	 * See notes in RecordTransactionCommit().
	 *
	 * Because we've already released the insertion locks, this test is a bit
	 * fuzzy: it is possible that we will wait for xacts we didn't really need
	 * to wait for.  But the delay should be short and it seems better to make
	 * checkpoint take a bit longer than to hold off insertions longer than
	 * necessary. (In fact, the whole reason we have this issue is that xact.c
	 * does commit record XLOG insertion and clog update as two separate steps
	 * protected by different locks, but again that seems best on grounds of
	 * minimizing lock contention.)
	 *
	 * A transaction that has not yet set delayChkptFlags when we look cannot
	 * be at risk, since it has not inserted its commit record yet; and one
	 * that's already cleared it is not at risk either, since it's done fixing
	 * clog and we will correctly flush the update below.  So we cannot miss
	 * any xacts we need to wait for.
	 */
	vxids = GetVirtualXIDsDelayingChkpt(&nvxids, DELAY_CHKPT_START);
	if (nvxids > 0)
	{
		do
		{
			/*
			 * Keep absorbing fsync requests while we wait. There could even
			 * be a deadlock if we don't, if the process that prevents the
			 * checkpoint is trying to add a request to the queue.
			 */
			AbsorbSyncRequests();

			pgstat_report_wait_start(WAIT_EVENT_CHECKPOINT_DELAY_START);
			pg_usleep(10000L);	/* wait for 10 msec */
			pgstat_report_wait_end();
		} while (HaveVirtualXIDsDelayingChkpt(vxids, nvxids,
											  DELAY_CHKPT_START));
	}
	pfree(vxids);

	CheckPointGuts(checkPoint.redo, flags);

	vxids = GetVirtualXIDsDelayingChkpt(&nvxids, DELAY_CHKPT_COMPLETE);
	if (nvxids > 0)
	{
		do
		{
			AbsorbSyncRequests();

			pgstat_report_wait_start(WAIT_EVENT_CHECKPOINT_DELAY_COMPLETE);
			pg_usleep(10000L);	/* wait for 10 msec */
			pgstat_report_wait_end();
		} while (HaveVirtualXIDsDelayingChkpt(vxids, nvxids,
											  DELAY_CHKPT_COMPLETE));
	}
	pfree(vxids);

	/*
	 * Take a snapshot of running transactions and write this to WAL. This
	 * allows us to reconstruct the state of running transactions during
	 * archive recovery, if required. Skip, if this info disabled.
	 *
	 * If we are shutting down, or Startup process is completing crash
	 * recovery we don't need to write running xact data.
	 */
	if (!shutdown && XLogStandbyInfoActive())
		LogStandbySnapshot();

	START_CRIT_SECTION();

	/*
	 * Now insert the checkpoint record into XLOG.
	 */
	XLogBeginInsert();
	XLogRegisterData(&checkPoint, sizeof(checkPoint));
	recptr = XLogInsert(RM_XLOG_ID,
						shutdown ? XLOG_CHECKPOINT_SHUTDOWN :
						XLOG_CHECKPOINT_ONLINE);

	XLogFlush(recptr);

	/*
	 * We mustn't write any new WAL after a shutdown checkpoint, or it will be
	 * overwritten at next startup.  No-one should even try, this just allows
	 * sanity-checking.  In the case of an end-of-recovery checkpoint, we want
	 * to just temporarily disable writing until the system has exited
	 * recovery.
	 */
	if (shutdown)
	{
		if (flags & CHECKPOINT_END_OF_RECOVERY)
			LocalXLogInsertAllowed = oldXLogAllowed;
		else
			LocalXLogInsertAllowed = 0; /* never again write WAL */
	}

	/*
	 * We now have ProcLastRecPtr = start of actual checkpoint record, recptr
	 * = end of actual checkpoint record.
	 */
	if (shutdown && checkPoint.redo != ProcLastRecPtr)
		ereport(PANIC,
				(errmsg("concurrent write-ahead log activity while database system is shutting down")));

	/*
	 * Remember the prior checkpoint's redo ptr for
	 * UpdateCheckPointDistanceEstimate()
	 */
	PriorRedoPtr = ControlFile->checkPointCopy.redo;

	/*
	 * Update the control file.
	 */
	LWLockAcquire(ControlFileLock, LW_EXCLUSIVE);
	if (shutdown)
		ControlFile->state = DB_SHUTDOWNED;
	ControlFile->checkPoint = ProcLastRecPtr;
	ControlFile->checkPointCopy = checkPoint;
	/* crash recovery should always recover to the end of WAL */
	ControlFile->minRecoveryPoint = InvalidXLogRecPtr;
	ControlFile->minRecoveryPointTLI = 0;

	/*
	 * Persist unloggedLSN value. It's reset on crash recovery, so this goes
	 * unused on non-shutdown checkpoints, but seems useful to store it always
	 * for debugging purposes.
	 */
	ControlFile->unloggedLSN = pg_atomic_read_membarrier_u64(&XLogCtl->unloggedLSN);

	UpdateControlFile();
	LWLockRelease(ControlFileLock);

	/* Update shared-memory copy of checkpoint XID/epoch */
	SpinLockAcquire(&XLogCtl->info_lck);
	XLogCtl->ckptFullXid = checkPoint.nextXid;
	SpinLockRelease(&XLogCtl->info_lck);

	/*
	 * We are now done with critical updates; no need for system panic if we
	 * have trouble while fooling with old log segments.
	 */
	END_CRIT_SECTION();

	// ... (L7322-L7339 생략: WAL summarizer 깨우기)

	/*
	 * Let smgr do post-checkpoint cleanup (eg, deleting old files).
	 */
	SyncPostCheckpoint();

	/*
	 * Update the average distance between checkpoints if the prior checkpoint
	 * exists.
	 */
	if (PriorRedoPtr != InvalidXLogRecPtr)
		UpdateCheckPointDistanceEstimate(RedoRecPtr - PriorRedoPtr);

	INJECTION_POINT("checkpoint-before-old-wal-removal", NULL);

	/*
	 * Delete old log files, those no longer needed for last checkpoint to
	 * prevent the disk holding the xlog from growing full.
	 */
	XLByteToSeg(RedoRecPtr, _logSegNo, wal_segment_size);
	KeepLogSeg(recptr, &_logSegNo);
	if (InvalidateObsoleteReplicationSlots(RS_INVAL_WAL_REMOVED | RS_INVAL_IDLE_TIMEOUT,
										   _logSegNo, InvalidOid,
										   InvalidTransactionId))
	{
		/*
		 * Some slots have been invalidated; recalculate the old-segment
		 * horizon, starting again from RedoRecPtr.
		 */
		XLByteToSeg(RedoRecPtr, _logSegNo, wal_segment_size);
		KeepLogSeg(recptr, &_logSegNo);
	}
	_logSegNo--;
	RemoveOldXlogFiles(_logSegNo, RedoRecPtr, recptr,
					   checkPoint.ThisTimeLineID);

	/*
	 * Make more log segments if needed.  (Do this after recycling old log
	 * segments, since that may supply some of the needed files.)
	 */
	if (!shutdown)
		PreallocXlogFiles(recptr, checkPoint.ThisTimeLineID);

	// ... (L7383-L7403 생략: pg_subtrans 정리, 완료 로그, ps 표시, dtrace)

	return true;
}
```

REDO 레코드를 넣을 때 공유 `RedoRecPtr` 가 바뀌는 곳은 `XLogInsertRecord` 의 특별 분기다. 모든 WAL 삽입 lock 을 잡은 채 자리를 예약하고, 그 시작 위치를 그대로 `RedoRecPtr` 로 삼는다.

`src/backend/access/transam` / `xlog.c` L888-L905 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L888-L905))

```c
// transam/xlog.c L888-L905
	else
	{
		Assert(class == WALINSERT_SPECIAL_CHECKPOINT);

		/*
		 * We need to update both the local and shared copies of RedoRecPtr,
		 * which means that we need to hold all the WAL insertion locks.
		 * However, there can't be any buffer references, so as above, we need
		 * not check RedoRecPtr before inserting the record; we just need to
		 * update it afterwards.
		 */
		Assert(fpw_lsn == InvalidXLogRecPtr);
		WALInsertLockAcquireExclusive();
		ReserveXLogInsertLocation(rechdr->xl_tot_len, &StartPos, &EndPos,
								  &rechdr->xl_prev);
		RedoRecPtr = Insert->RedoRecPtr = StartPos;
		inserted = true;
	}
```

## 동작 흐름

```text
 L6947  IS_SHUTDOWN | END_OF_RECOVERY 면 shutdown = true
 L6972  SyncPreCheckpoint                         smgr 준비
 L6977  START_CRIT_SECTION                        여기서 실패하면 PANIC
 L6982  shutdown 이면 pg_control.state = DB_SHUTDOWNING
 L7005  last_important_lsn = GetLastImportantRecPtr()
 L7015  FORCE 류가 아니고 last_important_lsn == pg_control.checkPoint 면
          "checkpoint skipped because system is idle" -> return false
 L7041  WALInsertLockAcquireExclusive             모든 삽입을 잠깐 막는다
 L7043    fullPageWrites, wal_level 기록
 L7046    shutdown 이면 redo = 현재 삽입 위치 (페이지 머리 건너뜀), RedoRecPtr 갱신
 L7085  WALInsertLockRelease
 L7096  온라인이면 XLogInsert(XLOG_CHECKPOINT_REDO)
          XLogInsertRecord L903 에서 RedoRecPtr = 이 레코드의 시작
 L7109    checkPoint.redo = RedoRecPtr
 L7113  XLogCtl->RedoRecPtr 도 갱신 (info_lck)
        (생략 구간) nextXid, nextOid, nextMulti, oldestXid ... 를 CheckPoint 에 채운다
 L7168  END_CRIT_SECTION                          쓰기 실패는 PANIC 이 아니라 ERROR 로
 L7199  DELAY_CHKPT_START 인 backend 가 빠질 때까지 10ms 씩 대기
 L7219  CheckPointGuts(redo, flags)               [04] 오래 걸리는 부분
 L7221  DELAY_CHKPT_COMPLETE 대기
 L7244  LogStandbySnapshot                        온라인이고 wal_level >= replica 면
 L7247  START_CRIT_SECTION
 L7254  XLogInsert(SHUTDOWN 또는 ONLINE, CheckPoint 구조체)
 L7258  XLogFlush(recptr)                         체크포인트 레코드까지 디스크로
 L7292-L7309  pg_control 갱신 후 UpdateControlFile (fsync 포함)
          checkPoint = ProcLastRecPtr (체크포인트 레코드의 시작)
          checkPointCopy = checkPoint 구조체
          minRecoveryPoint = 0
 L7320  END_CRIT_SECTION
 L7344  SyncPostCheckpoint                        지연된 unlink 처리
 L7351  UpdateCheckPointDistanceEstimate(이번 redo - 앞 redo)
 L7359  _logSegNo = REDO 가 든 세그먼트
 L7360  KeepLogSeg                                슬롯, wal_keep_size, summarizer 몫만큼 뒤로
 L7361  슬롯을 무효화했으면 다시 계산
 L7372  _logSegNo--                               REDO 세그먼트 자체는 남긴다
 L7373  RemoveOldXlogFiles                        [09]
 L7381  PreallocXlogFiles                         온라인이면 미래 세그먼트 미리 만들기
```

온라인 체크포인트와 shutdown 체크포인트는 LSN 축에 남기는 레코드 수가 다르다. 온라인이면 쓰는 동안 다른 WAL 이 끼므로 시작 표시와 완료 표시가 따로 필요하다.

```text
 온라인 (shutdown = false)

   ... | REDO 레코드 | 다른 backend 의 WAL ...................... | ONLINE 레코드 |
       B                                                          C
       checkPoint.redo = B                                        pg_control.checkPoint = C
       RedoRecPtr = B (L903)                                      CheckPoint{redo = B, ...}

   복구는 C 를 읽어 redo = B 를 알아내고 B 부터 재생한다
   B 와 C 사이의 레코드는 쓰기가 진행되는 동안 생긴 것이라 다시 재생해야 한다

 shutdown (shutdown = true)

   ... | SHUTDOWN 레코드 |
       C = checkPoint.redo
       WAL 삽입이 없으므로 레코드 하나가 시작 표시와 완료 표시를 겸한다 (주석 L6919-L6923)
       L7279: 레코드 시작이 redo 와 다르면 PANIC "concurrent write-ahead log activity"
```

L7199 의 대기는 커밋 레코드와 `pg_xact` 갱신 사이에 체크포인트가 끼는 경우를 막는다(주석 L7170-L7182).

```text
 A = 커밋하는 backend, CK = checkpointer

 시각  누가  하는 일
 t1    A     delayChkptFlags |= DELAY_CHKPT_START (xact.c L1437), 커밋 레코드를 WAL 에 넣음 (0/3D0000C0)
 t2    CK    REDO 레코드 = 0/3D000100. 커밋 레코드는 REDO 앞이다
 t3    CK    L7199 GetVirtualXIDsDelayingChkpt -> A 가 보인다 -> 10ms 씩 대기
 t4    A     pg_xact 에 committed 기록, DELAY_CHKPT_START 해제 (xact.c L1540)
 t5    CK    대기 끝 -> CheckPointGuts 가 CLOG 를 쓴다 (A 의 committed 포함)

 대기가 없으면: t5 의 CLOG 쓰기가 A 의 갱신보다 먼저 일어날 수 있다
 그 직후 크래시 -> 복구는 REDO(0/3D000100) 부터라 A 의 커밋 레코드를 재생하지 않는다
 -> A 의 커밋이 pg_xact 에서 사라진다
```

체크포인트가 끝난 뒤 `pg_control` 의 해당 필드는 이렇게 된다.

```text
 ControlFileData (include/catalog/pg_control.h L104-L239 일부)

 field                value (예)         line    뜻
 state                DB_IN_PRODUCTION   L7294   온라인이면 그대로. shutdown 이면 DB_SHUTDOWNED
 checkPoint           0/5A3F1E28         L7295   ONLINE 레코드의 시작 (ProcLastRecPtr)
 checkPointCopy.redo  0/3D000100         L7296   REDO 레코드의 시작
 minRecoveryPoint     0/0                L7298   크래시 복구는 WAL 끝까지 간다
 unloggedLSN          unloggedLSN        L7306   unlogged 릴레이션용 가짜 LSN 카운터
```

## 결과가 쓰이는 곳

```text
 pg_control.checkPoint, checkPointCopy
      --> 다음 기동의 InitWalRecovery (xlogrecovery.c L790-L815)
 RedoRecPtr = B
      --> 이후 XLogRecordAssemble 이 page LSN <= B 인 페이지를 처음 고칠 때 full-page image
          (xloginsert.c L620)
      --> XLogCheckpointNeeded 의 다음 트리거 기준
 CheckPointDistanceEstimate
      --> XLOGfileslop 이 재활용할 세그먼트 수를 추정 (xlog.c L2255)
 반환값 true / false (idle skip)
      --> [01] 의 num_performed 통계
```

## 다루지 않는 것

end-of-recovery 체크포인트의 timeline 처리, `LogStandbySnapshot`, `InvalidateObsoleteReplicationSlots`, `TruncateSUBTRANS`, `LogCheckpointEnd` 의 통계 로그, `UpdateCheckPointDistanceEstimate` 의 이동 평균 계산은 요약만 했다. REDO 레코드 삽입의 나머지(`ReserveXLogInsertLocation`, CRC, 복사)는 [행 쓰기와 WAL 기록](../../heap-insert-wal/README.md) 흐름이다.
