# InitWalRecovery

상위: [WAL redo (복구)](../README.md)

**어느 체크포인트에서 재생을 시작할지, 그리고 재생이 필요한지를 정하는 함수다.** `backup_label` 파일이 있으면 그 안의 체크포인트 위치를 쓰고 무조건 복구에 들어간다. 없으면 `pg_control.checkPoint` 를 쓴다. 어느 쪽이든 체크포인트 레코드를 실제로 읽어 그 안의 `redo` 위치를 꺼내고, 그 위치의 레코드가 존재하는지까지 확인한다. 복구가 필요하면 메모리의 `pg_control` 을 `DB_IN_CRASH_RECOVERY` 또는 `DB_IN_ARCHIVE_RECOVERY` 로 바꿔 두지만, 디스크에 쓰는 것은 호출자 `StartupXLOG` 다(머리 주석 L507-L513).

## 위치

`src/backend/access/transam` / `xlogrecovery.c` L518-L1045 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L518-L1045))

## 실제 코드

```c
// transam/xlogrecovery.c L518-L1045
void
InitWalRecovery(ControlFileData *ControlFile, bool *wasShutdown_ptr,
				bool *haveBackupLabel_ptr, bool *haveTblspcMap_ptr)
{
	XLogPageReadPrivate *private;
	struct stat st;
	bool		wasShutdown;
	XLogRecord *record;
	DBState		dbstate_at_startup;
	bool		haveTblspcMap = false;
	bool		haveBackupLabel = false;
	CheckPoint	checkPoint;
	bool		backupFromStandby = false;

	dbstate_at_startup = ControlFile->state;

	/*
	 * A startup process always starts with an inconsistent database. Set the
	 * flag accordingly, even if it was inherited from a postmaster that had
	 * already marked the database as consistent. This keeps the invariant
	 * local to the startup process without requiring every fork path to clear
	 * the flag.
	 */
	reachedConsistency = false;

	/*
	 * Initialize on the assumption we want to recover to the latest timeline
	 * that's active according to pg_control.
	 */
	if (ControlFile->minRecoveryPointTLI >
		ControlFile->checkPointCopy.ThisTimeLineID)
		recoveryTargetTLI = ControlFile->minRecoveryPointTLI;
	else
		recoveryTargetTLI = ControlFile->checkPointCopy.ThisTimeLineID;

	/*
	 * Check for signal files, and if so set up state for offline recovery
	 */
	readRecoverySignalFile();
	validateRecoveryParameters();

	// ... (L559-L602 생략: recovery latch, xlogreader 와 prefetcher 할당, consistency check 버퍼)
	/*
	 * Read the backup_label file.  We want to run this part of the recovery
	 * process after checking for signal files and after performing validation
	 * of the recovery parameters.
	 */
	if (read_backup_label(&CheckPointLoc, &CheckPointTLI, &backupEndRequired,
						  &backupFromStandby))
	{
		List	   *tablespaces = NIL;

		/*
		 * Archive recovery was requested, and thanks to the backup label
		 * file, we know how far we need to replay to reach consistency. Enter
		 * archive recovery directly.
		 */
		InArchiveRecovery = true;
		if (StandbyModeRequested)
			EnableStandbyMode();

		/*
		 * Omitting backup_label when creating a new replica, PITR node etc.
		 * unfortunately is a common cause of corruption.  Logging that
		 * backup_label was used makes it a bit easier to exclude that as the
		 * cause of observed corruption.
		 *
		 * Do so before we try to read the checkpoint record (which can fail),
		 * as otherwise it can be hard to understand why a checkpoint other
		 * than ControlFile->checkPoint is used.
		 */
		ereport(LOG,
				(errmsg("starting backup recovery with redo LSN %X/%X, checkpoint LSN %X/%X, on timeline ID %u",
						LSN_FORMAT_ARGS(RedoStartLSN),
						LSN_FORMAT_ARGS(CheckPointLoc),
						CheckPointTLI)));

		/*
		 * When a backup_label file is present, we want to roll forward from
		 * the checkpoint it identifies, rather than using pg_control.
		 */
		record = ReadCheckpointRecord(xlogprefetcher, CheckPointLoc,
									  CheckPointTLI);
		if (record != NULL)
		{
			memcpy(&checkPoint, XLogRecGetData(xlogreader), sizeof(CheckPoint));
			wasShutdown = ((record->xl_info & ~XLR_INFO_MASK) == XLOG_CHECKPOINT_SHUTDOWN);
			ereport(DEBUG1,
					(errmsg_internal("checkpoint record is at %X/%X",
									 LSN_FORMAT_ARGS(CheckPointLoc))));
			InRecovery = true;	/* force recovery even if SHUTDOWNED */

			// ... (L653-L671 생략: backup_label 이 가리킨 redo 위치가 실제로 있는지 확인)
		}
		else
		{
			ereport(FATAL,
					(errmsg("could not locate required checkpoint record at %X/%X",
							LSN_FORMAT_ARGS(CheckPointLoc)),
					 errhint("If you are restoring from a backup, touch \"%s/recovery.signal\" or \"%s/standby.signal\" and add required recovery options.\n"
							 "If you are not restoring from a backup, try removing the file \"%s/backup_label\".\n"
							 "Be careful: removing \"%s/backup_label\" will result in a corrupt cluster if restoring from a backup.",
							 DataDir, DataDir, DataDir, DataDir)));
			wasShutdown = false;	/* keep compiler quiet */
		}

		// ... (L685-L716 생략: tablespace_map 으로 symlink 생성)
		/* tell the caller to delete it later */
		haveBackupLabel = true;
	}
	else
	{
		/* No backup_label file has been found if we are here. */

		// ... (L724-L750 생략: backup_label 없이 tablespace_map 만 있으면 이름을 바꿔 무시)
		/*
		 * It's possible that archive recovery was requested, but we don't
		 * know how far we need to replay the WAL before we reach consistency.
		 * This can happen for example if a base backup is taken from a
		 * running server using an atomic filesystem snapshot, without calling
		 * pg_backup_start/stop. Or if you just kill a running primary server
		 * and put it into archive recovery by creating a recovery signal
		 * file.
		 *
		 * Our strategy in that case is to perform crash recovery first,
		 * replaying all the WAL present in pg_wal, and only enter archive
		 * recovery after that.
		 *
		 * But usually we already know how far we need to replay the WAL (up
		 * to minRecoveryPoint, up to backupEndPoint, or until we see an
		 * end-of-backup record), and we can enter archive recovery directly.
		 */
		if (ArchiveRecoveryRequested &&
			(ControlFile->minRecoveryPoint != InvalidXLogRecPtr ||
			 ControlFile->backupEndRequired ||
			 ControlFile->backupEndPoint != InvalidXLogRecPtr ||
			 ControlFile->state == DB_SHUTDOWNED))
		{
			InArchiveRecovery = true;
			if (StandbyModeRequested)
				EnableStandbyMode();
		}

		/*
		 * For the same reason as when starting up with backup_label present,
		 * emit a log message when we continue initializing from a base
		 * backup.
		 */
		if (!XLogRecPtrIsInvalid(ControlFile->backupStartPoint))
			ereport(LOG,
					(errmsg("restarting backup recovery with redo LSN %X/%X",
							LSN_FORMAT_ARGS(ControlFile->backupStartPoint))));

		/* Get the last valid checkpoint record. */
		CheckPointLoc = ControlFile->checkPoint;
		CheckPointTLI = ControlFile->checkPointCopy.ThisTimeLineID;
		RedoStartLSN = ControlFile->checkPointCopy.redo;
		RedoStartTLI = ControlFile->checkPointCopy.ThisTimeLineID;
		record = ReadCheckpointRecord(xlogprefetcher, CheckPointLoc,
									  CheckPointTLI);
		if (record != NULL)
		{
			ereport(DEBUG1,
					(errmsg_internal("checkpoint record is at %X/%X",
									 LSN_FORMAT_ARGS(CheckPointLoc))));
		}
		else
		{
			/*
			 * We used to attempt to go back to a secondary checkpoint record
			 * here, but only when not in standby mode. We now just fail if we
			 * can't read the last checkpoint because this allows us to
			 * simplify processing around checkpoints.
			 */
			ereport(PANIC,
					(errmsg("could not locate a valid checkpoint record at %X/%X",
							LSN_FORMAT_ARGS(CheckPointLoc))));
		}
		memcpy(&checkPoint, XLogRecGetData(xlogreader), sizeof(CheckPoint));
		wasShutdown = ((record->xl_info & ~XLR_INFO_MASK) == XLOG_CHECKPOINT_SHUTDOWN);

		/* Make sure that REDO location exists. */
		if (checkPoint.redo < CheckPointLoc)
		{
			XLogPrefetcherBeginRead(xlogprefetcher, checkPoint.redo);
			if (!ReadRecord(xlogprefetcher, LOG, false, checkPoint.ThisTimeLineID))
				ereport(PANIC,
						errmsg("could not find redo location %X/%08X referenced by checkpoint record at %X/%08X",
							   LSN_FORMAT_ARGS(checkPoint.redo), LSN_FORMAT_ARGS(CheckPointLoc)));
		}
	}

	// ... (L828-L922 생략: recovery target 종류별 LOG, timeline 이력 검사, DEBUG 로그, nextXid 검사)
	/* sanity check */
	if (checkPoint.redo > CheckPointLoc)
		ereport(PANIC,
				(errmsg("invalid redo in checkpoint record")));

	/*
	 * Check whether we need to force recovery from WAL.  If it appears to
	 * have been a clean shutdown and we did not have a recovery signal file,
	 * then assume no recovery needed.
	 */
	if (checkPoint.redo < CheckPointLoc)
	{
		if (wasShutdown)
			ereport(PANIC,
					(errmsg("invalid redo record in shutdown checkpoint")));
		InRecovery = true;
	}
	else if (ControlFile->state != DB_SHUTDOWNED)
		InRecovery = true;
	else if (ArchiveRecoveryRequested)
	{
		/* force recovery due to presence of recovery signal file */
		InRecovery = true;
	}

	/*
	 * If recovery is needed, update our in-memory copy of pg_control to show
	 * that we are recovering and to show the selected checkpoint as the place
	 * we are starting from. We also mark pg_control with any minimum recovery
	 * stop point obtained from a backup history file.
	 *
	 * We don't write the changes to disk yet, though. Only do that after
	 * initializing various subsystems.
	 */
	if (InRecovery)
	{
		if (InArchiveRecovery)
		{
			ControlFile->state = DB_IN_ARCHIVE_RECOVERY;
		}
		else
		{
			ereport(LOG,
					(errmsg("database system was not properly shut down; "
							"automatic recovery in progress")));
			if (recoveryTargetTLI > ControlFile->checkPointCopy.ThisTimeLineID)
				ereport(LOG,
						(errmsg("crash recovery starts in timeline %u "
								"and has target timeline %u",
								ControlFile->checkPointCopy.ThisTimeLineID,
								recoveryTargetTLI)));
			ControlFile->state = DB_IN_CRASH_RECOVERY;
		}
		ControlFile->checkPoint = CheckPointLoc;
		ControlFile->checkPointCopy = checkPoint;
		if (InArchiveRecovery)
		{
			/* initialize minRecoveryPoint if not set yet */
			if (ControlFile->minRecoveryPoint < checkPoint.redo)
			{
				ControlFile->minRecoveryPoint = checkPoint.redo;
				ControlFile->minRecoveryPointTLI = checkPoint.ThisTimeLineID;
			}
		}

		/*
		 * Set backupStartPoint if we're starting recovery from a base backup.
		 *
		 * Also set backupEndPoint and use minRecoveryPoint as the backup end
		 * location if we're starting recovery from a base backup which was
		 * taken from a standby. In this case, the database system status in
		 * pg_control must indicate that the database was already in recovery.
		 * Usually that will be DB_IN_ARCHIVE_RECOVERY but also can be
		 * DB_SHUTDOWNED_IN_RECOVERY if recovery previously was interrupted
		 * before reaching this point; e.g. because restore_command or
		 * primary_conninfo were faulty.
		 *
		 * Any other state indicates that the backup somehow became corrupted
		 * and we can't sensibly continue with recovery.
		 */
		if (haveBackupLabel)
		{
			ControlFile->backupStartPoint = checkPoint.redo;
			ControlFile->backupEndRequired = backupEndRequired;

			if (backupFromStandby)
			{
				if (dbstate_at_startup != DB_IN_ARCHIVE_RECOVERY &&
					dbstate_at_startup != DB_SHUTDOWNED_IN_RECOVERY)
					ereport(FATAL,
							(errmsg("backup_label contains data inconsistent with control file"),
							 errhint("This means that the backup is corrupted and you will "
									 "have to use another backup for recovery.")));
				ControlFile->backupEndPoint = ControlFile->minRecoveryPoint;
			}
		}
	}

	/* remember these, so that we know when we have reached consistency */
	backupStartPoint = ControlFile->backupStartPoint;
	backupEndRequired = ControlFile->backupEndRequired;
	backupEndPoint = ControlFile->backupEndPoint;
	if (InArchiveRecovery)
	{
		minRecoveryPoint = ControlFile->minRecoveryPoint;
		minRecoveryPointTLI = ControlFile->minRecoveryPointTLI;
	}
	else
	{
		minRecoveryPoint = InvalidXLogRecPtr;
		minRecoveryPointTLI = 0;
	}

	/*
	 * Start recovery assuming that the final record isn't lost.
	 */
	abortedRecPtr = InvalidXLogRecPtr;
	missingContrecPtr = InvalidXLogRecPtr;

	*wasShutdown_ptr = wasShutdown;
	*haveBackupLabel_ptr = haveBackupLabel;
	*haveTblspcMap_ptr = haveTblspcMap;
}
```

`backup_label` 의 앞 두 줄이 시작점을 준다. `START WAL LOCATION` 이 REDO 지점, `CHECKPOINT LOCATION` 이 체크포인트 레코드 위치다.

`src/backend/access/transam` / `xlogrecovery.c` L1257-L1289 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L1257-L1289))

```c
// transam/xlogrecovery.c L1257-L1289
	/*
	 * See if label file is present
	 */
	lfp = AllocateFile(BACKUP_LABEL_FILE, "r");
	if (!lfp)
	{
		if (errno != ENOENT)
			ereport(FATAL,
					(errcode_for_file_access(),
					 errmsg("could not read file \"%s\": %m",
							BACKUP_LABEL_FILE)));
		return false;			/* it's not there, all is fine */
	}

	/*
	 * Read and parse the START WAL LOCATION and CHECKPOINT lines (this code
	 * is pretty crude, but we are not expecting any variability in the file
	 * format).
	 */
	if (fscanf(lfp, "START WAL LOCATION: %X/%X (file %08X%16s)%c",
			   &hi, &lo, &tli_from_walseg, startxlogfilename, &ch) != 5 || ch != '\n')
		ereport(FATAL,
				(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
				 errmsg("invalid data in file \"%s\"", BACKUP_LABEL_FILE)));
	RedoStartLSN = ((uint64) hi) << 32 | lo;
	RedoStartTLI = tli_from_walseg;
	if (fscanf(lfp, "CHECKPOINT LOCATION: %X/%X%c",
			   &hi, &lo, &ch) != 3 || ch != '\n')
		ereport(FATAL,
				(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
				 errmsg("invalid data in file \"%s\"", BACKUP_LABEL_FILE)));
	*checkPointLoc = ((uint64) hi) << 32 | lo;
	*backupLabelTLI = tli_from_walseg;
```

## 동작 흐름

```text
 InitWalRecovery

 L541  reachedConsistency = false
 L547  recoveryTargetTLI = max(minRecoveryPointTLI, 체크포인트의 TLI)
 L556  readRecoverySignalFile                  standby.signal / recovery.signal -> ArchiveRecoveryRequested
 L608  read_backup_label 이 true 면           -- 베이스 백업에서 기동
 L618    InArchiveRecovery = true
 L642    ReadCheckpointRecord(CheckPointLoc)   backup_label 의 CHECKPOINT LOCATION
 L651    InRecovery = true                     SHUTDOWNED 여도 강제
 L718    haveBackupLabel = true                StartupXLOG 가 나중에 backup_label.old 로 바꾼다
 L720  아니면                                  -- 평소 기동
 L768    아카이브 복구 요청 + 어디까지 가야 할지 알면 InArchiveRecovery = true
         (모르면 먼저 pg_wal 로 크래시 복구, 그 뒤 아카이브로. 주석 L751-L766)
 L790    CheckPointLoc = pg_control.checkPoint
 L792    RedoStartLSN  = pg_control.checkPointCopy.redo
 L794    ReadCheckpointRecord                  못 읽으면 PANIC (예전처럼 이전 체크포인트로 물러나지 않는다)
 L818    redo < 체크포인트 위치면 redo 의 레코드를 한 번 읽어 본다. 없으면 PANIC
 L924  redo > 체크포인트 위치면 PANIC
 L933  복구가 필요한가
         redo < 체크포인트 (온라인 체크포인트)  -> 필요. 단 SHUTDOWN 레코드인데 그러면 PANIC
         pg_control.state != DB_SHUTDOWNED       -> 필요
         신호 파일 있음                          -> 필요
 L957  필요하면 메모리의 ControlFile 을
         state = DB_IN_ARCHIVE_RECOVERY 또는 DB_IN_CRASH_RECOVERY
         checkPoint, checkPointCopy = 고른 체크포인트
         아카이브 복구면 minRecoveryPoint 를 적어도 redo 로
         backup_label 이면 backupStartPoint = redo, backupEndRequired
 L1022-L1034  일관성 판정용 전역 변수 (backupStartPoint, minRecoveryPoint ...)
```

시작점을 고르는 두 길을 LSN 축에 같이 그리면 이렇다. 백업을 뜬 서버의 `pg_control` 은 백업이 진행되는 동안 더 뒤의 체크포인트로 바뀌었을 수 있다. 그래서 `backup_label` 이 있으면 그쪽을 믿는다.

```text
 WAL (LSN 증가 ->)

   0/20000028        0/20000080                         0/5A3F1E28
   |                 |                                  |
   R1                C1                                 C2

   R1  pg_backup_start 의 체크포인트 REDO       backup_label: START WAL LOCATION: 0/20000028
   C1  그 체크포인트 레코드                     backup_label: CHECKPOINT LOCATION: 0/20000080
   C2  백업 복사 중에 생긴 다음 체크포인트      복사된 pg_control.checkPoint 가 이것일 수 있다

   R1 이 세그먼트 첫머리 + 0x28 (긴 페이지 헤더 40바이트 뒤) 인 것은 pg_backup_start 가 체크포인트 전에
   세그먼트를 넘기기 때문이다 (xlog.c L8930). C1 은 그 사이에 다른 WAL 이 없을 때의 가장 이른 위치다
     0x28 .. 0x47   XLOG_CHECKPOINT_REDO   24 + 2 + 4  = 30 -> MAXALIGN 32
     0x48 .. 0x7F   XLOG_RUNNING_XACTS     24 + 2 + 24 = 50 -> MAXALIGN 56   (wal_level >= replica 라 항상 있다)
     0x80           XLOG_CHECKPOINT_ONLINE

 backup_label 이 있으면  C1 을 읽고 R1 부터 재생   (L608-L651)
                          backupStartPoint = R1, end-of-backup 레코드를 볼 때까지 일관성 없음
 backup_label 을 지우면  C2 를 읽고 C2 의 redo 부터 재생
                          백업 복사 초반에 복사된 파일은 R1 과 C2 의 redo 사이의 변경을 놓친다
                          -> 주석 L622-L626 이 말하는 "common cause of corruption"
```

복구가 필요한지에 대한 결정표다. `backup_label` 이 없는 경우다(있으면 L651 에서 항상 true).

```text
 record type       redo vs loc   pg_control.state   signal file   InRecovery   mode
 SHUTDOWN          ==            DB_SHUTDOWNED      none          false        재생 없음
 SHUTDOWN          ==            DB_SHUTDOWNED      recovery      true         아카이브 복구
 ONLINE            <             any                none          true         크래시 복구 (L938)
 SHUTDOWN          ==            DB_SHUTDOWNING     none          true         크래시 복구 (L941)
 SHUTDOWN          <             -                  -             PANIC        "invalid redo record in shutdown checkpoint"
```

## 결과가 쓰이는 곳

```text
 InRecovery, InArchiveRecovery, ArchiveRecoveryRequested, StandbyModeRequested
      --> [02] StartupXLOG L5731 의 분기, [10] WaitForWALToBecomeAvailable 의 소스 선택
 CheckPointLoc, RedoStartLSN, RedoStartTLI
      --> [04] PerformWalRecovery 가 RedoStartLSN 으로 이동 (L1734)
 메모리의 ControlFile
      --> [02] StartupXLOG L5749 의 UpdateControlFile 로 디스크에
 backupStartPoint, backupEndPoint, minRecoveryPoint
      --> CheckRecoveryConsistency 가 "읽기 전용 연결을 받아도 되는가"를 판단 (L2205)
```

## 다루지 않는 것

`readRecoverySignalFile` 과 `validateRecoveryParameters`, `ReadCheckpointRecord` 의 레코드 검증, `tablespace_map` 처리, timeline 이력 검사(`tliOfPointInHistory`), WAL prefetcher 와 decode buffer 설정은 요약만 했다.
