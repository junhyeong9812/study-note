# PerformWalRecovery

상위: [WAL redo (복구)](../README.md)

**REDO 지점으로 이동해 첫 레코드를 읽고, 레코드가 없을 때까지 "적용하고 다음을 읽는" 루프를 도는 함수다.** 온라인 체크포인트에서 시작하면 첫 레코드는 반드시 `XLOG_CHECKPOINT_REDO` 여야 한다. 루프 안에서는 레코드마다 PITR 목표에 닿았는지, 일시 정지 요청이 있는지를 보고 `ApplyWalRecord` 를 부른다. 크래시 복구에서 `ReadRecord` 가 NULL 을 돌려주는 것은 오류가 아니라 WAL 의 끝이다.

## 위치

`src/backend/access/transam` / `xlogrecovery.c` L1679-L1931 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L1679-L1931))

## 실제 코드

```c
// transam/xlogrecovery.c L1679-L1931
void
PerformWalRecovery(void)
{
	XLogRecord *record;
	bool		reachedRecoveryTarget = false;
	TimeLineID	replayTLI;

	/*
	 * Initialize shared variables for tracking progress of WAL replay, as if
	 * we had just replayed the record before the REDO location (or the
	 * checkpoint record itself, if it's a shutdown checkpoint).
	 */
	SpinLockAcquire(&XLogRecoveryCtl->info_lck);
	if (RedoStartLSN < CheckPointLoc)
	{
		XLogRecoveryCtl->lastReplayedReadRecPtr = InvalidXLogRecPtr;
		XLogRecoveryCtl->lastReplayedEndRecPtr = RedoStartLSN;
		XLogRecoveryCtl->lastReplayedTLI = RedoStartTLI;
	}
	else
	{
		XLogRecoveryCtl->lastReplayedReadRecPtr = xlogreader->ReadRecPtr;
		XLogRecoveryCtl->lastReplayedEndRecPtr = xlogreader->EndRecPtr;
		XLogRecoveryCtl->lastReplayedTLI = CheckPointTLI;
	}
	XLogRecoveryCtl->replayEndRecPtr = XLogRecoveryCtl->lastReplayedEndRecPtr;
	XLogRecoveryCtl->replayEndTLI = XLogRecoveryCtl->lastReplayedTLI;
	XLogRecoveryCtl->recoveryLastXTime = 0;
	XLogRecoveryCtl->currentChunkStartTime = 0;
	XLogRecoveryCtl->recoveryPauseState = RECOVERY_NOT_PAUSED;
	SpinLockRelease(&XLogRecoveryCtl->info_lck);

	/* Also ensure XLogReceiptTime has a sane value */
	XLogReceiptTime = GetCurrentTimestamp();

	/*
	 * Let postmaster know we've started redo now, so that it can launch the
	 * archiver if necessary.
	 */
	if (IsUnderPostmaster)
		SendPostmasterSignal(PMSIGNAL_RECOVERY_STARTED);

	/*
	 * Allow read-only connections immediately if we're consistent already.
	 */
	CheckRecoveryConsistency();

	/*
	 * Find the first record that logically follows the checkpoint --- it
	 * might physically precede it, though.
	 */
	if (RedoStartLSN < CheckPointLoc)
	{
		/* back up to find the record */
		replayTLI = RedoStartTLI;
		XLogPrefetcherBeginRead(xlogprefetcher, RedoStartLSN);
		record = ReadRecord(xlogprefetcher, PANIC, false, replayTLI);

		/*
		 * If a checkpoint record's redo pointer points back to an earlier
		 * LSN, the record at that LSN should be an XLOG_CHECKPOINT_REDO
		 * record.
		 */
		if (record->xl_rmid != RM_XLOG_ID ||
			(record->xl_info & ~XLR_INFO_MASK) != XLOG_CHECKPOINT_REDO)
			ereport(FATAL,
					(errmsg("unexpected record type found at redo point %X/%X",
							LSN_FORMAT_ARGS(xlogreader->ReadRecPtr))));
	}
	else
	{
		/* just have to read next record after CheckPoint */
		Assert(xlogreader->ReadRecPtr == CheckPointLoc);
		replayTLI = CheckPointTLI;
		record = ReadRecord(xlogprefetcher, LOG, false, replayTLI);
	}

	if (record != NULL)
	{
		TimestampTz xtime;
		PGRUsage	ru0;

		pg_rusage_init(&ru0);

		InRedo = true;

		RmgrStartup();

		ereport(LOG,
				(errmsg("redo starts at %X/%X",
						LSN_FORMAT_ARGS(xlogreader->ReadRecPtr))));

		/* Prepare to report progress of the redo phase. */
		if (!StandbyMode)
			begin_startup_progress_phase();

		/*
		 * main redo apply loop
		 */
		do
		{
			if (!StandbyMode)
				ereport_startup_progress("redo in progress, elapsed time: %ld.%02d s, current LSN: %X/%X",
										 LSN_FORMAT_ARGS(xlogreader->ReadRecPtr));

// ... (L1784-L1799 생략: WAL_DEBUG 출력)

			/* Handle interrupt signals of startup process */
			ProcessStartupProcInterrupts();

			// ... (L1804-L1819 생략: hot standby 세션의 pause 요청 처리)

			/*
			 * Have we reached our recovery target?
			 */
			if (recoveryStopsBefore(xlogreader))
			{
				reachedRecoveryTarget = true;
				break;
			}

			// ... (L1830-L1845 생략: recovery_min_apply_delay 대기)

			/*
			 * Apply the record
			 */
			ApplyWalRecord(xlogreader, record, &replayTLI);

			/* Exit loop if we reached inclusive recovery target */
			if (recoveryStopsAfter(xlogreader))
			{
				reachedRecoveryTarget = true;
				break;
			}

			/* Else, try to fetch the next WAL record */
			record = ReadRecord(xlogprefetcher, LOG, false, replayTLI);
		} while (record != NULL);

		/*
		 * end of main redo apply loop
		 */

		// ... (L1867-L1898 생략: recovery_target_action (shutdown, pause, promote))

		RmgrCleanup();

		ereport(LOG,
				(errmsg("redo done at %X/%X system usage: %s",
						LSN_FORMAT_ARGS(xlogreader->ReadRecPtr),
						pg_rusage_show(&ru0))));
		// ... (L1906-L1910 생략: 마지막 커밋 시각 로그)

		InRedo = false;
	}
	else
	{
		/* there are no WAL records following the checkpoint */
		ereport(LOG,
				(errmsg("redo is not required")));
	}

	/*
	 * This check is intentionally after the above log messages that indicate
	 * how far recovery went.
	 */
	if (ArchiveRecoveryRequested &&
		recoveryTarget != RECOVERY_TARGET_UNSET &&
		!reachedRecoveryTarget)
		ereport(FATAL,
				(errcode(ERRCODE_CONFIG_FILE_ERROR),
				 errmsg("recovery ended before configured recovery target was reached")));
}
```

## 동작 흐름

```text
 PerformWalRecovery

 L1692  공유 진행 변수 초기화
          RedoStartLSN < CheckPointLoc (온라인)  -> lastReplayedEndRecPtr = RedoStartLSN
          아니면 (shutdown 체크포인트)           -> 체크포인트 레코드 자체를 재생한 것으로
 L1719  postmaster 에 PMSIGNAL_RECOVERY_STARTED  archiver 를 띄울 수 있게
 L1724  CheckRecoveryConsistency                 이미 일관이면 읽기 전용 연결 허용
 L1730  RedoStartLSN < CheckPointLoc 면
 L1734    XLogPrefetcherBeginRead(RedoStartLSN)  뒤로 돌아간다
 L1735    ReadRecord(PANIC)                      못 읽으면 PANIC
 L1742    XLOG_CHECKPOINT_REDO 가 아니면 FATAL "unexpected record type found at redo point"
 L1748  아니면 체크포인트 레코드 다음 레코드
 L1763  InRedo = true, RmgrStartup                rm_startup 이 있는 rmgr (btree, gin ...) 준비
 L1767  "redo starts at %X/%X"
 L1778  do {
 L1802    ProcessStartupProcInterrupts           SIGHUP, 종료 요청, postmaster 사망
 L1824    recoveryStopsBefore -> 목표면 break
 L1850    [06] ApplyWalRecord(xlogreader, record, &replayTLI)
 L1853    recoveryStopsAfter -> 목표면 break
 L1860    record = [05] ReadRecord(LOG)
 L1861  } while (record != NULL)
 L1900  RmgrCleanup
 L1902  "redo done at %X/%X"
 L1925  목표를 정했는데 못 닿았으면 FATAL
```

온라인 체크포인트에서 시작하면 읽기 위치가 한 번 뒤로 간다. `InitWalRecovery` 가 체크포인트 레코드를 읽느라 앞으로 갔다가, 여기서 REDO 지점으로 돌아온다.

```text
 WAL (LSN 증가 ->)

   0/3D000100              ...                        0/5A3F1E28          0/5B012340
   |                                                  |                   |
   B  REDO 레코드                                      C  ONLINE 레코드    WAL 끝

 InitWalRecovery    읽기 위치 C (L794)
 PerformWalRecovery L1734 에서 B 로 이동
                    L1735 B 를 읽음. XLOG_CHECKPOINT_REDO 인지 확인
                    루프: B 다음 레코드 ... C 도 다시 만난다 (xlog_redo 가 체크포인트 레코드를 처리)
                    ... 0/5B012340 에서 끝
```

루프 한 바퀴를 시간축으로 그리면, 레코드 하나가 "읽기 -> 판정 -> 적용 -> 진행 공개" 순서를 거친다.

```text
 레코드 R (ReadRecPtr = 0/3D2A0F10, EndRecPtr = 0/3D2A0F68, rmid = Heap, info = INSERT)

 L1802  인터럽트 확인
 L1817  pause 요청? (생략 구간)
 L1824  recoveryStopsBefore(R)       크래시 복구면 목표가 없으니 false
 L1834  apply delay? (생략 구간)
 L1850  ApplyWalRecord
          replayEndRecPtr = 0/3D2A0F68  (적용 전)
          heap_redo -> heap_xlog_insert -> 페이지 갱신, PageSetLSN(0/3D2A0F68)
          lastReplayedEndRecPtr = 0/3D2A0F68  (적용 후)
 L1853  recoveryStopsAfter(R)        false
 L1860  ReadRecord -> 다음 레코드 (ReadRecPtr = 0/3D2A0F68)
```

## 결과가 쓰이는 곳

```text
 루프 종료 (record == NULL 또는 목표 도달)
      --> [02] StartupXLOG 의 FinishWalRecovery 가 xlogreader 의 위치로 EndOfLog 를 정한다
 XLogRecoveryCtl->lastReplayedEndRecPtr
      --> CheckRecoveryConsistency, GetXLogReplayRecPtr, restartpoint 위치
 reachedRecoveryTarget
      --> recovery_target_action (생략 구간 L1879-L1897)
```

## 다루지 않는 것

PITR 목표 판정(`recoveryStopsBefore`, `recoveryStopsAfter` 의 xid, 시각, 이름, LSN 비교), `recoveryPausesHere`, `recoveryApplyDelay`, `RmgrStartup`/`RmgrCleanup`, 시작 진행 보고(`ereport_startup_progress`)는 요약만 했다.
