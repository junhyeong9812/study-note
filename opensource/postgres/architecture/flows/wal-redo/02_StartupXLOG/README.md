# StartupXLOG

상위: [WAL redo (복구)](../README.md)

**서버 기동의 WAL 쪽 순서 전체를 쥐고 있는 함수다.** 크래시였는지 보고, `InitWalRecovery` 로 시작 체크포인트를 정하고, 그 체크포인트 값으로 XID, OID 같은 카운터를 되살리고, 복구가 필요하면 `PerformWalRecovery` 로 재생한다. 재생이 끝나면 WAL 이 끝난 자리(`EndOfLog`)를 새 삽입 위치로 잡고, end-of-recovery 체크포인트를 요청한 뒤 `pg_control` 을 `DB_IN_PRODUCTION` 으로 바꿔 쓰기를 연다(머리 주석 L5464: postmaster 기동마다 한 번).

## 위치

`src/backend/access/transam` / `xlog.c` L5466-L6242 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L5466-L6242))

## 실제 코드

```c
// transam/xlog.c L5466-L6242
void
StartupXLOG(void)
{
	XLogCtlInsert *Insert;
	CheckPoint	checkPoint;
	bool		wasShutdown;
	bool		didCrash;
	bool		haveTblspcMap;
	bool		haveBackupLabel;
	XLogRecPtr	EndOfLog;
	TimeLineID	EndOfLogTLI;
	TimeLineID	newTLI;
	bool		performedWalRecovery;
	EndOfWalRecoveryInfo *endOfRecoveryInfo;
	XLogRecPtr	abortedRecPtr;
	XLogRecPtr	missingContrecPtr;
	TransactionId oldestActiveXID;
	bool		promoted = false;

	/*
	 * We should have an aux process resource owner to use, and we should not
	 * be in a transaction that's installed some other resowner.
	 */
	Assert(AuxProcessResourceOwner != NULL);
	Assert(CurrentResourceOwner == NULL ||
		   CurrentResourceOwner == AuxProcessResourceOwner);
	CurrentResourceOwner = AuxProcessResourceOwner;

	/*
	 * Check that contents look valid.
	 */
	if (!XRecOffIsValid(ControlFile->checkPoint))
		ereport(FATAL,
				(errcode(ERRCODE_DATA_CORRUPTED),
				 errmsg("control file contains invalid checkpoint location")));

	// ... (L5502-L5572 생략: pg_control.state 별 LOG 메시지, pg_wal 디렉터리 확인, 진행 보고 타이머)
	/*----------
	 * If we previously crashed, perform a couple of actions:
	 *
	 * - The pg_wal directory may still include some temporary WAL segments
	 *   used when creating a new segment, so perform some clean up to not
	 *   bloat this path.  This is done first as there is no point to sync
	 *   this temporary data.
	 *
	 * - There might be data which we had written, intending to fsync it, but
	 *   which we had not actually fsync'd yet.  Therefore, a power failure in
	 *   the near future might cause earlier unflushed writes to be lost, even
	 *   though more recent data written to disk from here on would be
	 *   persisted.  To avoid that, fsync the entire data directory.
	 */
	if (ControlFile->state != DB_SHUTDOWNED &&
		ControlFile->state != DB_SHUTDOWNED_IN_RECOVERY)
	{
		RemoveTempXlogFiles();
		SyncDataDirectory();
		didCrash = true;
	}
	else
		didCrash = false;

	/*
	 * Prepare for WAL recovery if needed.
	 *
	 * InitWalRecovery analyzes the control file and the backup label file, if
	 * any.  It updates the in-memory ControlFile buffer according to the
	 * starting checkpoint, and sets InRecovery and ArchiveRecoveryRequested.
	 * It also applies the tablespace map file, if any.
	 */
	InitWalRecovery(ControlFile, &wasShutdown,
					&haveBackupLabel, &haveTblspcMap);
	checkPoint = ControlFile->checkPointCopy;

	/* initialize shared memory variables from the checkpoint record */
	TransamVariables->nextXid = checkPoint.nextXid;
	TransamVariables->nextOid = checkPoint.nextOid;
	TransamVariables->oidCount = 0;
	MultiXactSetNextMXact(checkPoint.nextMulti, checkPoint.nextMultiOffset);
	AdvanceOldestClogXid(checkPoint.oldestXid);
	SetTransactionIdLimit(checkPoint.oldestXid, checkPoint.oldestXidDB);
	SetMultiXactIdLimit(checkPoint.oldestMulti, checkPoint.oldestMultiDB, true);
	SetCommitTsLimit(checkPoint.oldestCommitTsXid,
					 checkPoint.newestCommitTsXid);
	XLogCtl->ckptFullXid = checkPoint.nextXid;

	// ... (L5621-L5724 생략: relcache 초기화 파일 삭제, 복제 슬롯, CLOG, MultiXact, CommitTs 기동, unlogged LSN, timeline history, 2PC, pgstat)
	lastFullPageWrites = checkPoint.fullPageWrites;

	RedoRecPtr = XLogCtl->RedoRecPtr = XLogCtl->Insert.RedoRecPtr = checkPoint.redo;
	doPageWrites = lastFullPageWrites;

	/* REDO */
	if (InRecovery)
	{
		/* Initialize state for RecoveryInProgress() */
		SpinLockAcquire(&XLogCtl->info_lck);
		if (InArchiveRecovery)
			XLogCtl->SharedRecoveryState = RECOVERY_STATE_ARCHIVE;
		else
			XLogCtl->SharedRecoveryState = RECOVERY_STATE_CRASH;
		SpinLockRelease(&XLogCtl->info_lck);

		/*
		 * Update pg_control to show that we are recovering and to show the
		 * selected checkpoint as the place we are starting from. We also mark
		 * pg_control with any minimum recovery stop point obtained from a
		 * backup history file.
		 *
		 * No need to hold ControlFileLock yet, we aren't up far enough.
		 */
		UpdateControlFile();

		/*
		 * If there was a backup label file, it's done its job and the info
		 * has now been propagated into pg_control.  We must get rid of the
		 * label file so that if we crash during recovery, we'll pick up at
		 * the latest recovery restartpoint instead of going all the way back
		 * to the backup start point.  It seems prudent though to just rename
		 * the file out of the way rather than delete it completely.
		 */
		if (haveBackupLabel)
		{
			unlink(BACKUP_LABEL_OLD);
			durable_rename(BACKUP_LABEL_FILE, BACKUP_LABEL_OLD, FATAL);
		}

		/*
		 * If there was a tablespace_map file, it's done its job and the
		 * symlinks have been created.  We must get rid of the map file so
		 * that if we crash during recovery, we don't create symlinks again.
		 * It seems prudent though to just rename the file out of the way
		 * rather than delete it completely.
		 */
		if (haveTblspcMap)
		{
			unlink(TABLESPACE_MAP_OLD);
			durable_rename(TABLESPACE_MAP, TABLESPACE_MAP_OLD, FATAL);
		}

		/*
		 * Initialize our local copy of minRecoveryPoint.  When doing crash
		 * recovery we want to replay up to the end of WAL.  Particularly, in
		 * the case of a promoted standby minRecoveryPoint value in the
		 * control file is only updated after the first checkpoint.  However,
		 * if the instance crashes before the first post-recovery checkpoint
		 * is completed then recovery will use a stale location causing the
		 * startup process to think that there are still invalid page
		 * references when checking for data consistency.
		 */
		if (InArchiveRecovery)
		{
			LocalMinRecoveryPoint = ControlFile->minRecoveryPoint;
			LocalMinRecoveryPointTLI = ControlFile->minRecoveryPointTLI;
		}
		else
		{
			LocalMinRecoveryPoint = InvalidXLogRecPtr;
			LocalMinRecoveryPointTLI = 0;
		}

		/* Check that the GUCs used to generate the WAL allow recovery */
		CheckRequiredParameterValues();

		// ... (L5802-L5881 생략: unlogged 릴레이션 정리, 스냅샷 파일 삭제, Hot Standby 초기화)

		/*
		 * We're all set for replaying the WAL now. Do it.
		 */
		PerformWalRecovery();
		performedWalRecovery = true;
	}
	else
		performedWalRecovery = false;

	/*
	 * Finish WAL recovery.
	 */
	endOfRecoveryInfo = FinishWalRecovery();
	EndOfLog = endOfRecoveryInfo->endOfLog;
	EndOfLogTLI = endOfRecoveryInfo->endOfLogTLI;
	abortedRecPtr = endOfRecoveryInfo->abortedRecPtr;
	missingContrecPtr = endOfRecoveryInfo->missingContrecPtr;

	// ... (L5901-L5906 생략: ps 표시 초기화)
	/*
	 * When recovering from a backup (we are in recovery, and archive recovery
	 * was requested), complain if we did not roll forward far enough to reach
	 * the point where the database is consistent.  For regular online
	 * backup-from-primary, that means reaching the end-of-backup WAL record
	 * (at which point we reset backupStartPoint to be Invalid), for
	 * backup-from-replica (which can't inject records into the WAL stream),
	 * that point is when we reach the minRecoveryPoint in pg_control (which
	 * we purposefully copy last when backing up from a replica).  For
	 * pg_rewind (which creates a backup_label with a method of "pg_rewind")
	 * or snapshot-style backups (which don't), backupEndRequired will be set
	 * to false.
	 *
	 * Note: it is indeed okay to look at the local variable
	 * LocalMinRecoveryPoint here, even though ControlFile->minRecoveryPoint
	 * might be further ahead --- ControlFile->minRecoveryPoint cannot have
	 * been advanced beyond the WAL we processed.
	 */
	if (InRecovery &&
		(EndOfLog < LocalMinRecoveryPoint ||
		 !XLogRecPtrIsInvalid(ControlFile->backupStartPoint)))
	{
		/*
		 * Ran off end of WAL before reaching end-of-backup WAL record, or
		 * minRecoveryPoint. That's a bad sign, indicating that you tried to
		 * recover from an online backup but never called pg_backup_stop(), or
		 * you didn't archive all the WAL needed.
		 */
		if (ArchiveRecoveryRequested || ControlFile->backupEndRequired)
		{
			if (!XLogRecPtrIsInvalid(ControlFile->backupStartPoint) || ControlFile->backupEndRequired)
				ereport(FATAL,
						(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
						 errmsg("WAL ends before end of online backup"),
						 errhint("All WAL generated while online backup was taken must be available at recovery.")));
			else
				ereport(FATAL,
						(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
						 errmsg("WAL ends before consistent recovery point")));
		}
	}

	// ... (L5949-L6026 생략: unlogged INIT fork 복원, 2PC 사전 조사, archive recovery 면 새 timeline ID 와 history 파일)
	/* Save the selected TimeLineID in shared memory, too */
	SpinLockAcquire(&XLogCtl->info_lck);
	XLogCtl->InsertTimeLineID = newTLI;
	XLogCtl->PrevTimeLineID = endOfRecoveryInfo->lastRecTLI;
	SpinLockRelease(&XLogCtl->info_lck);

	// ... (L6033-L6052 생략: 불완전한 마지막 레코드 처리 (missingContrecPtr))
	/*
	 * Prepare to write WAL starting at EndOfLog location, and init xlog
	 * buffer cache using the block containing the last record from the
	 * previous incarnation.
	 */
	Insert = &XLogCtl->Insert;
	Insert->PrevBytePos = XLogRecPtrToBytePos(endOfRecoveryInfo->lastRec);
	Insert->CurrBytePos = XLogRecPtrToBytePos(EndOfLog);

	// ... (L6062-L6094 생략: 마지막 WAL 페이지를 WAL 버퍼로 복사)
	/*
	 * Update local and shared status.  This is OK to do without any locks
	 * because no other process can be reading or writing WAL yet.
	 */
	LogwrtResult.Write = LogwrtResult.Flush = EndOfLog;
	pg_atomic_write_u64(&XLogCtl->logInsertResult, EndOfLog);
	pg_atomic_write_u64(&XLogCtl->logWriteResult, EndOfLog);
	pg_atomic_write_u64(&XLogCtl->logFlushResult, EndOfLog);
	XLogCtl->LogwrtRqst.Write = EndOfLog;
	XLogCtl->LogwrtRqst.Flush = EndOfLog;

	// ... (L6106-L6110 생략: 세그먼트 미리 만들기)
	/*
	 * Okay, we're officially UP.
	 */
	InRecovery = false;

	// ... (L6116-L6148 생략: archive_timeout 기준, latestCompletedXid, SUBTRANS, CLOG 와 MultiXact 정리, 2PC 복원, xlogreader 종료)
	/* Enable WAL writes for this backend only. */
	LocalSetXLogInsertAllowed();

	// ... (L6152-L6166 생략: overwrite-contrecord 레코드, full_page_writes 갱신)
	/*
	 * Emit checkpoint or end-of-recovery record in XLOG, if required.
	 */
	if (performedWalRecovery)
		promoted = PerformRecoveryXLogAction();

	// ... (L6173-L6190 생략: XLogReportParameters, archive recovery 뒤 정리, CommitTs)
	/*
	 * All done with end-of-recovery actions.
	 *
	 * Now allow backends to write WAL and update the control file status in
	 * consequence.  SharedRecoveryState, that controls if backends can write
	 * WAL, is updated while holding ControlFileLock to prevent other backends
	 * to look at an inconsistent state of the control file in shared memory.
	 * There is still a small window during which backends can write WAL and
	 * the control file is still referring to a system not in DB_IN_PRODUCTION
	 * state while looking at the on-disk control file.
	 *
	 * Also, we use info_lck to update SharedRecoveryState to ensure that
	 * there are no race conditions concerning visibility of other recent
	 * updates to shared memory.
	 */
	LWLockAcquire(ControlFileLock, LW_EXCLUSIVE);
	ControlFile->state = DB_IN_PRODUCTION;

	SpinLockAcquire(&XLogCtl->info_lck);
	XLogCtl->SharedRecoveryState = RECOVERY_STATE_DONE;
	SpinLockRelease(&XLogCtl->info_lck);

	UpdateControlFile();
	LWLockRelease(ControlFileLock);

	// ... (L6216-L6233 생략: standby 복구 환경 정리, walsender 깨우기)
	/*
	 * If this was a promotion, request an (online) checkpoint now. This isn't
	 * required for consistency, but the last restartpoint might be far back,
	 * and in case of a crash, recovering from it might take a longer than is
	 * appropriate now that we're not in standby mode anymore.
	 */
	if (promoted)
		RequestCheckpoint(CHECKPOINT_FORCE);
}
```

## 동작 흐름

```text
 StartupXLOG

 L5497  pg_control.checkPoint 오프셋이 이상하면 FATAL
 L5587  state 가 DB_SHUTDOWNED / DB_SHUTDOWNED_IN_RECOVERY 가 아니면
          RemoveTempXlogFiles, SyncDataDirectory, didCrash = true
 L5605  [03] InitWalRecovery(ControlFile, ...)   시작 체크포인트 결정, InRecovery 결정
 L5607  checkPoint = ControlFile->checkPointCopy
 L5610-L5619  nextXid, nextOid, nextMulti, oldestXid ... 를 체크포인트 값으로
 L5727  RedoRecPtr = checkPoint.redo
 L5731  InRecovery 면
 L5734-L5739  SharedRecoveryState = ARCHIVE 또는 CRASH
 L5749    UpdateControlFile                     DB_IN_CRASH_RECOVERY 등을 디스크에
 L5759    backup_label -> backup_label.old      다시 크래시해도 백업 시작점으로 돌아가지 않게
 L5788    아카이브 복구면 LocalMinRecoveryPoint = pg_control 값
 L5800    CheckRequiredParameterValues          아카이브 복구인데 wal_level=minimal 이면 FATAL
                                                hot standby 면 backend 슬롯 수도 primary 이상이어야 한다 (L5438-L5460)
 L5886    [04] PerformWalRecovery
 L5895  FinishWalRecovery                       EndOfLog, 마지막 레코드, 중단 사유
 L5925  아카이브 복구인데 일관성 지점 전에 WAL 이 끝났으면 FATAL
 L6058-L6060  Insert->PrevBytePos, CurrBytePos = EndOfLog
 L6099-L6104  write, flush 결과도 EndOfLog 로
 L6114  InRecovery = false
 L6150  LocalSetXLogInsertAllowed               이 프로세스만 먼저 WAL 을 쓸 수 있다
 L6171  재생을 했으면 PerformRecoveryXLogAction
          promote 면 END_OF_RECOVERY 레코드만, 아니면 end-of-recovery 체크포인트 (L6341-L6362)
 L6206-L6214  ControlFileLock 안에서
          state = DB_IN_PRODUCTION, SharedRecoveryState = RECOVERY_STATE_DONE, UpdateControlFile
 L6240  promote 였으면 RequestCheckpoint(FORCE)
```

`pg_control.state` 가 기동 때 무엇이었는지에 따라 같은 함수가 세 갈래로 간다.

```text
 state at startup          redo vs ckpt     signal file       결과
 DB_SHUTDOWNED             redo == ckpt     none              InRecovery = false. 재생 없이 바로 쓰기 열기
 DB_SHUTDOWNED             redo == ckpt     recovery.signal   아카이브 복구 (InitWalRecovery L942)
 DB_IN_PRODUCTION          -                none              크래시 복구. 데이터 디렉터리 fsync 후 재생
 DB_SHUTDOWNING            -                none              shutdown 체크포인트 도중 죽음 -> 크래시 복구
 DB_IN_ARCHIVE_RECOVERY    -                standby.signal    standby 재기동. minRecoveryPoint 까지는 일관성 없음
```

`pg_control` 은 이 함수 안에서 세 번 디스크에 쓰인다. 각 시점에 다시 죽으면 다음 기동이 무엇을 보는지가 다르다.

```text
 when                       line          state                   다음 기동이 보는 것
 after InitWalRecovery      L5749         DB_IN_*_RECOVERY        "interrupted while in recovery", 같은 체크포인트에서 다시
 end-of-recovery checkpoint xlog.c L7308  DB_SHUTDOWNED (L7294)   새 shutdown 체크포인트. redo == ckpt 라 재생할 것 없음
 open for writes            L6213         DB_IN_PRODUCTION        정상 운영 중 크래시와 같다
```

## 결과가 쓰이는 곳

```text
 TransamVariables (nextXid, nextOid ...)
      --> 재생이 진행되며 ApplyWalRecord 의 AdvanceNextFullTransactionIdPastXid 가 더 올린다
 Insert->CurrBytePos = EndOfLog
      --> 기동 뒤 첫 XLogInsert 가 여기서부터 자리를 예약한다
 SharedRecoveryState = RECOVERY_STATE_DONE
      --> 모든 프로세스의 RecoveryInProgress() 가 false
 RequestCheckpoint(END_OF_RECOVERY | IMMEDIATE | WAIT)
      --> [체크포인트](../../checkpoint/README.md) 흐름의 CreateCheckPoint 가 shutdown 형 체크포인트를 쓴다
```

## 다루지 않는 것

timeline 선택과 history 파일(`findNewestTimeLine`, `writeTimeLineHistory`, `XLogInitNewTimeline`), 불완전한 마지막 레코드의 `XLOG_OVERWRITE_CONTRECORD`, Hot Standby 초기화(`ProcArrayApplyRecoveryInfo`), unlogged 릴레이션 리셋, SLRU 기동과 정리, 2PC 복원, `FinishWalRecovery` 내부는 요약만 했다.
