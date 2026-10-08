# WaitForWALToBecomeAvailable

상위: [WAL redo (복구)](../README.md)

**다음에 읽을 WAL 이 든 세그먼트 파일을 열어 주는 함수이고, standby 에서는 그 파일이 생길 때까지 기다리는 상태 기계다.** 소스는 셋이다. 아카이브(`restore_command`), `pg_wal` 디렉터리, primary 에서 스트리밍 받는 walreceiver 다. 크래시 복구는 `pg_wal` 만 보고, 없으면 바로 실패를 돌려 복구를 끝낸다. standby 는 아카이브 또는 `pg_wal` 에서 실패하면 promote 요청을 확인하고, walreceiver 를 띄워 스트림으로 넘어가고, 스트림도 끊기면 `wal_retrieve_retry_interval`(기본 5초)을 기다렸다 아카이브부터 다시 돈다(주석 L3595-L3619).

## 위치

`src/backend/access/transam` / `xlogrecovery.c` L3585-L4063 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L3585-L4063))

## 실제 코드

```c
// transam/xlogrecovery.c L3585-L4063
static XLogPageReadResult
WaitForWALToBecomeAvailable(XLogRecPtr RecPtr, bool randAccess,
							bool fetching_ckpt, XLogRecPtr tliRecPtr,
							TimeLineID replayTLI, XLogRecPtr replayLSN,
							bool nonblocking)
{
	static TimestampTz last_fail_time = 0;
	TimestampTz now;
	bool		streaming_reply_sent = false;

	/*-------
	 * Standby mode is implemented by a state machine:
	 *
	 * 1. Read from either archive or pg_wal (XLOG_FROM_ARCHIVE), or just
	 *	  pg_wal (XLOG_FROM_PG_WAL)
	 * 2. Check for promotion trigger request
	 * 3. Read from primary server via walreceiver (XLOG_FROM_STREAM)
	 * 4. Rescan timelines
	 * 5. Sleep wal_retrieve_retry_interval milliseconds, and loop back to 1.
	 *
	 * Failure to read from the current source advances the state machine to
	 * the next state.
	 *
	 * 'currentSource' indicates the current state. There are no currentSource
	 * values for "check trigger", "rescan timelines", and "sleep" states,
	 * those actions are taken when reading from the previous source fails, as
	 * part of advancing to the next state.
	 *
	 * If standby mode is turned off while reading WAL from stream, we move
	 * to XLOG_FROM_ARCHIVE and reset lastSourceFailed, to force fetching
	 * the files (which would be required at end of recovery, e.g., timeline
	 * history file) from archive or pg_wal. We don't need to kill WAL receiver
	 * here because it's already stopped when standby mode is turned off at
	 * the end of recovery.
	 *-------
	 */
	if (!InArchiveRecovery)
		currentSource = XLOG_FROM_PG_WAL;
	else if (currentSource == XLOG_FROM_ANY ||
			 (!StandbyMode && currentSource == XLOG_FROM_STREAM))
	{
		lastSourceFailed = false;
		currentSource = XLOG_FROM_ARCHIVE;
	}

	for (;;)
	{
		XLogSource	oldSource = currentSource;
		bool		startWalReceiver = false;

		/*
		 * First check if we failed to read from the current source, and
		 * advance the state machine if so. The failure to read might've
		 * happened outside this function, e.g when a CRC check fails on a
		 * record, or within this loop.
		 */
		if (lastSourceFailed)
		{
			/*
			 * Don't allow any retry loops to occur during nonblocking
			 * readahead.  Let the caller process everything that has been
			 * decoded already first.
			 */
			if (nonblocking)
				return XLREAD_WOULDBLOCK;

			switch (currentSource)
			{
				case XLOG_FROM_ARCHIVE:
				case XLOG_FROM_PG_WAL:

					/*
					 * Check to see if promotion is requested. Note that we do
					 * this only after failure, so when you promote, we still
					 * finish replaying as much as we can from archive and
					 * pg_wal before failover.
					 */
					if (StandbyMode && CheckForStandbyTrigger())
					{
						XLogShutdownWalRcv();
						return XLREAD_FAIL;
					}

					/*
					 * Not in standby mode, and we've now tried the archive
					 * and pg_wal.
					 */
					if (!StandbyMode)
						return XLREAD_FAIL;

					/*
					 * Move to XLOG_FROM_STREAM state, and set to start a
					 * walreceiver if necessary.
					 */
					currentSource = XLOG_FROM_STREAM;
					startWalReceiver = true;
					break;

				case XLOG_FROM_STREAM:
					// ... (L3684-L3744 생략: walreceiver 종료, latest timeline 재탐색)
					now = GetCurrentTimestamp();
					if (!TimestampDifferenceExceeds(last_fail_time, now,
													wal_retrieve_retry_interval))
					{
						long		wait_time;

						wait_time = wal_retrieve_retry_interval -
							TimestampDifferenceMilliseconds(last_fail_time, now);

						elog(LOG, "waiting for WAL to become available at %X/%X",
							 LSN_FORMAT_ARGS(RecPtr));

						/* Do background tasks that might benefit us later. */
						KnownAssignedTransactionIdsIdleMaintenance();

						(void) WaitLatch(&XLogRecoveryCtl->recoveryWakeupLatch,
										 WL_LATCH_SET | WL_TIMEOUT |
										 WL_EXIT_ON_PM_DEATH,
										 wait_time,
										 WAIT_EVENT_RECOVERY_RETRIEVE_RETRY_INTERVAL);
						ResetLatch(&XLogRecoveryCtl->recoveryWakeupLatch);
						now = GetCurrentTimestamp();

						/* Handle interrupt signals of startup process */
						ProcessStartupProcInterrupts();
					}
					last_fail_time = now;
					currentSource = XLOG_FROM_ARCHIVE;
					break;

				default:
					elog(ERROR, "unexpected WAL source %d", currentSource);
			}
		}
		else if (currentSource == XLOG_FROM_PG_WAL)
		{
			/*
			 * We just successfully read a file in pg_wal. We prefer files in
			 * the archive over ones in pg_wal, so try the next file again
			 * from the archive first.
			 */
			if (InArchiveRecovery)
				currentSource = XLOG_FROM_ARCHIVE;
		}

		if (currentSource != oldSource)
			elog(DEBUG2, "switched WAL source from %s to %s after %s",
				 xlogSourceNames[oldSource], xlogSourceNames[currentSource],
				 lastSourceFailed ? "failure" : "success");

		/*
		 * We've now handled possible failure. Try to read from the chosen
		 * source.
		 */
		lastSourceFailed = false;

		switch (currentSource)
		{
			case XLOG_FROM_ARCHIVE:
			case XLOG_FROM_PG_WAL:

				/*
				 * WAL receiver must not be running when reading WAL from
				 * archive or pg_wal.
				 */
				Assert(!WalRcvStreaming());

				// ... (L3812-L3821 생략: 열린 파일 닫기, randAccess 면 curFileTLI 초기화)
				/*
				 * Try to restore the file from archive, or read an existing
				 * file from pg_wal.
				 */
				readFile = XLogFileReadAnyTLI(readSegNo,
											  currentSource == XLOG_FROM_ARCHIVE ? XLOG_FROM_ANY :
											  currentSource);
				if (readFile >= 0)
					return XLREAD_SUCCESS;	/* success! */

				/*
				 * Nope, not found in archive or pg_wal.
				 */
				lastSourceFailed = true;
				break;

			case XLOG_FROM_STREAM:
				{
					bool		havedata;

					/*
					 * We should be able to move to XLOG_FROM_STREAM only in
					 * standby mode.
					 */
					Assert(StandbyMode);

					// ... (L3848-L3877 생략: walreceiver 재시작 요청 처리, 시작 위치 주석)
					if (startWalReceiver &&
						PrimaryConnInfo && strcmp(PrimaryConnInfo, "") != 0)
					{
						XLogRecPtr	ptr;
						TimeLineID	tli;

						if (fetching_ckpt)
						{
							ptr = RedoStartLSN;
							tli = RedoStartTLI;
						}
						else
						{
							ptr = RecPtr;

							/*
							 * Use the record begin position to determine the
							 * TLI, rather than the position we're reading.
							 */
							tli = tliOfPointInHistory(tliRecPtr, expectedTLEs);

							if (curFileTLI > 0 && tli < curFileTLI)
								elog(ERROR, "according to history file, WAL location %X/%X belongs to timeline %u, but previous recovered WAL file came from timeline %u",
									 LSN_FORMAT_ARGS(tliRecPtr),
									 tli, curFileTLI);
						}
						curFileTLI = tli;
						SetInstallXLogFileSegmentActive();
						RequestXLogStreaming(tli, ptr, PrimaryConnInfo,
											 PrimarySlotName,
											 wal_receiver_create_temp_slot);
						flushedUpto = 0;
					}

					/*
					 * Check if WAL receiver is active or wait to start up.
					 */
					if (!WalRcvStreaming())
					{
						lastSourceFailed = true;
						break;
					}

					// ... (L3921-L3932 생략: XLogReceiptTime 설명 주석)
					if (RecPtr < flushedUpto)
						havedata = true;
					else
					{
						XLogRecPtr	latestChunkStart;

						flushedUpto = GetWalRcvFlushRecPtr(&latestChunkStart, &receiveTLI);
						if (RecPtr < flushedUpto && receiveTLI == curFileTLI)
						{
							havedata = true;
							if (latestChunkStart <= RecPtr)
							{
								XLogReceiptTime = GetCurrentTimestamp();
								SetCurrentChunkStartTime(XLogReceiptTime);
							}
						}
						else
							havedata = false;
					}
					if (havedata)
					// ... (L3953-L3970 생략: timeline history 관련 주석)
						if (readFile < 0)
						{
							if (!expectedTLEs)
								expectedTLEs = readTimeLineHistory(recoveryTargetTLI);
							readFile = XLogFileRead(readSegNo, receiveTLI,
													XLOG_FROM_STREAM, false);
							Assert(readFile >= 0);
						}
						else
						{
							/* just make sure source info is correct... */
							readSource = XLOG_FROM_STREAM;
							XLogReceiptSource = XLOG_FROM_STREAM;
							return XLREAD_SUCCESS;
						}
						break;
					}

					/* In nonblocking mode, return rather than sleeping. */
					if (nonblocking)
						return XLREAD_WOULDBLOCK;

					/*
					 * Data not here yet. Check for trigger, then wait for
					 * walreceiver to wake us up when new WAL arrives.
					 */
					if (CheckForStandbyTrigger())
					{
						/*
						 * Note that we don't return XLREAD_FAIL immediately
						 * here. After being triggered, we still want to
						 * replay all the WAL that was already streamed. It's
						 * in pg_wal now, so we just treat this as a failure,
						 * and the state machine will move on to replay the
						 * streamed WAL from pg_wal, and then recheck the
						 * trigger and exit replay.
						 */
						lastSourceFailed = true;
						break;
					}

					// ... (L4012-L4029 생략: primary 에 reply, KnownAssignedXids 정리, prefetch 통계)

					/*
					 * Wait for more WAL to arrive, when we will be woken
					 * immediately by the WAL receiver.
					 */
					(void) WaitLatch(&XLogRecoveryCtl->recoveryWakeupLatch,
									 WL_LATCH_SET | WL_EXIT_ON_PM_DEATH,
									 -1L,
									 WAIT_EVENT_RECOVERY_WAL_STREAM);
					ResetLatch(&XLogRecoveryCtl->recoveryWakeupLatch);
					break;
				}

			default:
				elog(ERROR, "unexpected WAL source %d", currentSource);
		}

		// ... (L4047-L4059 생략: pause 확인, 인터럽트 처리)
	}

	return XLREAD_FAIL;			/* not reached */
}
```

## 동작 흐름

```text
 WaitForWALToBecomeAvailable(RecPtr, randAccess, fetching_ckpt, tliRecPtr, replayTLI, replayLSN, nonblocking)

 L3621  크래시 복구 (!InArchiveRecovery)  -> currentSource = PG_WAL
 L3623  아카이브 복구, 처음이거나 standby 가 아닌데 STREAM 이면 -> ARCHIVE
 L3630  for (;;)
 L3641    lastSourceFailed 면 다음 상태로
            ARCHIVE / PG_WAL 실패
 L3662        standby 이고 promote 요청 -> walreceiver 종료, return FAIL
 L3672        standby 가 아님           -> return FAIL        크래시/아카이브 복구는 여기서 끝
 L3679        STREAM 으로, startWalReceiver = true
            STREAM 실패 (생략 구간 L3684-L3744: walreceiver 정리, timeline 재탐색)
 L3746        마지막 실패 뒤 wal_retrieve_retry_interval 이 안 지났으면
 L3760          recoveryWakeupLatch 에서 남은 시간만큼 잔다
 L3772        ARCHIVE 로
 L3779    방금 PG_WAL 에서 성공했고 아카이브 복구면 다음은 ARCHIVE 먼저
 L3801    지금 소스로 시도
            ARCHIVE / PG_WAL
 L3826        XLogFileReadAnyTLI           restore_command 로 받거나 pg_wal 에서 연다
 L3830        열렸으면 return SUCCESS, 아니면 lastSourceFailed = true
            STREAM
 L3878        startWalReceiver 면 RequestXLogStreaming(tli, ptr)   walreceiver 를 띄운다
 L3915        walreceiver 가 안 돌면 lastSourceFailed = true
 L3933        RecPtr < flushedUpto ?      walreceiver 가 이미 받아 flush 한 위치
 L3939          아니면 GetWalRcvFlushRecPtr 로 새로 확인
 L3952        havedata 면 파일을 열고 return SUCCESS
 L3990        nonblocking 이면 WOULDBLOCK
 L3997        promote 요청 -> lastSourceFailed = true   (받은 것까지는 pg_wal 에서 마저 재생)
 L4035        recoveryWakeupLatch 에서 기한 없이 잔다   walreceiver 가 flush 하면 WakeupRecovery
                                                   (replication/walreceiver.c L1085)
```

상태 기계를 그림으로 그리면 이렇다. 화살표 옆은 넘어가는 조건이다.

```text
                 +-------------------------------+
                 |                               |
                 v                               |
         +---------------+   실패               |
  시작 ->| ARCHIVE       |--------+              |
         | (또는 PG_WAL) |        |              |
         +---------------+        v              |
                 |         promote 요청?         |
                 | 성공      | yes -> FAIL (복구 끝, promote)
                 v           | no
            파일을 열고      v                   |
            SUCCESS     +-----------+  실패     |
                        | STREAM    |-----------+  timeline 재탐색,
                        | walrcv    |              wal_retrieve_retry_interval 대기
                        +-----------+
                          |       |
                 데이터 있음     없음 -> recoveryWakeupLatch 대기 -> 다시 STREAM
                          v
                     SUCCESS
```

standby 하나가 primary 를 따라가는 모습을 시간축으로 그리면 이렇다. LSN 과 시각은 예시다.

```text
 시간 ->   (wal_retrieve_retry_interval = 5000ms, xlog.c L135)

 t0   standby 기동. 아카이브에서 seg 3D .. 41 을 restore_command 로 받아 재생
 t1   seg 42 가 아카이브에 아직 없음 -> ARCHIVE 실패
      promote 요청 없음 -> STREAM, RequestXLogStreaming(tli 1, 0/42000200)
      시작 위치는 세그먼트 처음 0/42000000 으로 내려간다 (replication/walreceiverfuncs.c L255-L261)
 t2   walreceiver 가 primary 에 붙어 받기 시작. flushedUpto = 0/42003A10
      RecPtr 0/42000200 < flushedUpto -> SUCCESS, 재생 계속
 t3   재생이 flushedUpto 를 따라잡음 -> WalRcvForceReply 로 재생 위치를 primary 에 알림
      recoveryWakeupLatch 대기 (L4035)
 t4   walreceiver 가 새 WAL 을 flush 하고 latch 를 세움 -> 깨어나 재생
 ...
 t5   primary 가 죽어 스트림이 끊김 -> STREAM 실패
      마지막 실패가 5초 이내면 남은 시간만큼 대기 -> ARCHIVE 부터 다시
 t6   pg_ctl promote -> 다음 실패 지점에서 CheckForStandbyTrigger 가 참 -> FAIL
      ReadRecord 가 NULL 을 돌려 PerformWalRecovery 루프가 끝나고 promote 된다
```

## 결과가 쓰이는 곳

```text
 XLREAD_SUCCESS + readFile 이 열림
      --> XLogPageRead 가 그 파일에서 페이지를 읽는다 (L3383 의 호출자)
 XLREAD_FAIL
      --> XLogPageRead 실패 -> [05] ReadRecord 가 NULL 또는 재시도
 RequestXLogStreaming
      --> PMSIGNAL_START_WALRECEIVER 로 postmaster 가 walreceiver 를 띄운다 (walreceiverfuncs.c L322). 받는 쪽은 [스트리밍 복제](../../streaming-replication/README.md) 흐름
 XLogReceiptTime
      --> standby 쿼리 충돌의 유예 시간 계산 (storage/ipc/standby.c L210, max_standby_streaming_delay)
```

## 다루지 않는 것

`XLogFileReadAnyTLI` 의 timeline 별 파일 찾기와 `restore_command` 실행, `rescanLatestTimeLine`, walreceiver 프로세스 내부, `CheckForStandbyTrigger` 의 promote 처리, nonblocking 모드의 WAL prefetch 연동은 요약만 했다.
