# WalReceiverMain

상위: [스트리밍 복제](../README.md)

**standby 쪽 walreceiver 프로세스의 몸통이다.** primary 에 복제 연결을 열고, `IDENTIFY_SYSTEM` 으로 같은 클러스터인지 확인한 뒤 `START_REPLICATION` 을 보내 COPY 모드에 들어간다. 그 뒤로는 받을 수 있는 메시지를 모두 받아 쓰고([07]-[08]), 한 번에 fsync 하고([09]), 위치를 보고하는([10]) 루프를 연결이 끝날 때까지 돈다. 한 타임라인을 다 받으면 프로세스는 죽지 않고 startup 의 다음 지시를 기다린다.

## 위치

`replication` / `walreceiver.c` L159-L716 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L159-L716))

## 실제 코드

공유 메모리에서 자기 상태를 STREAMING 으로 바꾸고 startup 이 남긴 시작 위치를 읽는다.

`replication` / `walreceiver.c` L178-L250 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L178-L250))

```c
// replication/walreceiver.c L178-L250
	Assert(startup_data_len == 0);

	MyBackendType = B_WAL_RECEIVER;
	AuxiliaryProcessMainCommon();

// ... (L183-L186 생략: 주석)
	walrcv = WalRcv;
	Assert(walrcv != NULL);

// ... (L190-L196 생략: 주석)
	SpinLockAcquire(&walrcv->mutex);
	Assert(walrcv->pid == 0);
	switch (walrcv->walRcvState)
	{
		case WALRCV_STOPPING:
			/* If we've already been requested to stop, don't start up. */
			walrcv->walRcvState = WALRCV_STOPPED;
			/* fall through */

		case WALRCV_STOPPED:
			SpinLockRelease(&walrcv->mutex);
			ConditionVariableBroadcast(&walrcv->walRcvStoppedCV);
			proc_exit(1);
			break;

		case WALRCV_STARTING:
			/* The usual case */
			break;

		case WALRCV_WAITING:
		case WALRCV_STREAMING:
		case WALRCV_RESTARTING:
		default:
			/* Shouldn't happen */
			SpinLockRelease(&walrcv->mutex);
			elog(PANIC, "walreceiver still running according to shared memory state");
	}
	/* Advertise our PID so that the startup process can kill us */
	walrcv->pid = MyProcPid;
	walrcv->walRcvState = WALRCV_STREAMING;

	/* Fetch information required to start streaming */
	walrcv->ready_to_display = false;
	strlcpy(conninfo, walrcv->conninfo, MAXCONNINFO);
	strlcpy(slotname, walrcv->slotname, NAMEDATALEN);
	is_temp_slot = walrcv->is_temp_slot;
	startpoint = walrcv->receiveStart;
	startpointTLI = walrcv->receiveStartTLI;

	/*
	 * At most one of is_temp_slot and slotname can be set; otherwise,
	 * RequestXLogStreaming messed up.
	 */
	Assert(!is_temp_slot || (slotname[0] == '\0'));

	/* Initialise to a sanish value */
	now = GetCurrentTimestamp();
	walrcv->lastMsgSendTime =
		walrcv->lastMsgReceiptTime = walrcv->latestWalEndTime = now;

	/* Report our proc number so that others can wake us up */
	walrcv->procno = MyProcNumber;

	SpinLockRelease(&walrcv->mutex);
```

primary 에 붙는다. 두 번째 인자 `true` 가 복제 연결이라는 뜻이고, libpqwalreceiver 가 시작 패킷에 `replication=true` 를 넣는다(libpqwalreceiver.c L178-L179).

`replication` / `walreceiver.c` L279-L286 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L279-L286))

```c
// replication/walreceiver.c L279-L286
	/* Establish the connection to the primary for XLOG streaming */
	appname = cluster_name[0] ? cluster_name : "walreceiver";
	wrconn = walrcv_connect(conninfo, true, false, false, appname, &err);
	if (!wrconn)
		ereport(ERROR,
				(errcode(ERRCODE_CONNECTION_FAILURE),
				 errmsg("streaming replication receiver \"%s\" could not connect to the primary server: %s",
						appname, err)));
```

같은 클러스터인지, 타임라인이 뒤처지지 않았는지 본다.

`replication` / `walreceiver.c` L314-L348 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L314-L348))

```c
// replication/walreceiver.c L314-L348
	first_stream = true;
	for (;;)
	{
		char	   *primary_sysid;
		char		standby_sysid[32];
		WalRcvStreamOptions options;

		/*
		 * Check that we're connected to a valid server using the
		 * IDENTIFY_SYSTEM replication command.  Reset the global LSN
		 * first so we don't act on a stale value if the call fails.
		 */
		WalRcvIdentifySystemLsn = InvalidXLogRecPtr;
		primary_sysid = walrcv_identify_system(wrconn, &primaryTLI);

		snprintf(standby_sysid, sizeof(standby_sysid), UINT64_FORMAT,
				 GetSystemIdentifier());
		if (strcmp(primary_sysid, standby_sysid) != 0)
		{
			ereport(ERROR,
					(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
					 errmsg("database system identifier differs between the primary and standby"),
					 errdetail("The primary's identifier is %s, the standby's identifier is %s.",
							   primary_sysid, standby_sysid)));
		}

		/*
		 * Confirm that the current timeline of the primary is the same or
		 * ahead of ours.
		 */
		if (primaryTLI < startpointTLI)
			ereport(ERROR,
					(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
					 errmsg("highest timeline %u of the primary is behind recovery timeline %u",
							primaryTLI, startpointTLI)));
```

`START_REPLICATION` 을 보내고, 처음 위치 보고를 한 번 강제로 보낸다.

`replication` / `walreceiver.c` L446-L486 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L446-L486))

```c
// replication/walreceiver.c L446-L486
		/*
// ... (L447-L457 생략: 주석)
		options.logical = false;
		options.startpoint = startpoint;
		options.slotname = slotname[0] != '\0' ? slotname : NULL;
		options.proto.physical.startpointTLI = startpointTLI;
		if (walrcv_startstreaming(wrconn, &options))
		{
			if (first_stream)
				ereport(LOG,
						(errmsg("started streaming WAL from primary at %X/%X on timeline %u",
								LSN_FORMAT_ARGS(startpoint), startpointTLI)));
			else
				ereport(LOG,
						(errmsg("restarted WAL streaming at %X/%X on timeline %u",
								LSN_FORMAT_ARGS(startpoint), startpointTLI)));
			first_stream = false;

			/* Initialize LogstreamResult and buffers for processing messages */
			LogstreamResult.Write = LogstreamResult.Flush = GetXLogReplayRecPtr(NULL);
			initStringInfo(&reply_message);

			/* Initialize nap wakeup times. */
			now = GetCurrentTimestamp();
			for (int i = 0; i < NUM_WALRCV_WAKEUPS; ++i)
				WalRcvComputeNextWakeup(i, now);

			/* Send initial reply/feedback messages. */
			XLogWalRcvSendReply(true, false);
			XLogWalRcvSendHSFeedback(true);

```

안쪽 루프다. 읽을 수 있는 만큼 읽어 처리하고, 한 번 보고하고, 한 번 flush 한다.

`replication` / `walreceiver.c` L487-L572 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L487-L572))

```c
// replication/walreceiver.c L487-L572
			/* Loop until end-of-streaming or error */
			for (;;)
			{
				char	   *buf;
				int			len;
				bool		endofwal = false;
				pgsocket	wait_fd = PGINVALID_SOCKET;
				int			rc;
				TimestampTz nextWakeup;
				long		nap;

// ... (L498-L500 생략: 주석)
				 */
				if (!RecoveryInProgress())
					ereport(FATAL,
							(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
							 errmsg("cannot continue WAL streaming, recovery has already ended")));

				/* Process any requests or signals received recently */
				CHECK_FOR_INTERRUPTS();

				if (ConfigReloadPending)
				{
					ConfigReloadPending = false;
					ProcessConfigFile(PGC_SIGHUP);
					/* recompute wakeup times */
					now = GetCurrentTimestamp();
					for (int i = 0; i < NUM_WALRCV_WAKEUPS; ++i)
						WalRcvComputeNextWakeup(i, now);
					XLogWalRcvSendHSFeedback(true);
				}

				/* See if we can read data immediately */
				len = walrcv_receive(wrconn, &buf, &wait_fd);
				if (len != 0)
				{
					/*
					 * Process the received data, and any subsequent data we
					 * can read without blocking.
					 */
					for (;;)
					{
						if (len > 0)
						{
							/*
							 * Something was received from primary, so adjust
							 * the ping and terminate wakeup times.
							 */
							now = GetCurrentTimestamp();
							WalRcvComputeNextWakeup(WALRCV_WAKEUP_TERMINATE,
													now);
							WalRcvComputeNextWakeup(WALRCV_WAKEUP_PING, now);
							XLogWalRcvProcessMsg(buf[0], &buf[1], len - 1,
												 startpointTLI);
						}
						else if (len == 0)
							break;
						else if (len < 0)
						{
							ereport(LOG,
									(errmsg("replication terminated by primary server"),
									 errdetail("End of WAL reached on timeline %u at %X/%X.",
											   startpointTLI,
											   LSN_FORMAT_ARGS(LogstreamResult.Write))));
							endofwal = true;
							break;
						}
						len = walrcv_receive(wrconn, &buf, &wait_fd);
					}

					/* Let the primary know that we received some data. */
					XLogWalRcvSendReply(false, false);

					/*
					 * If we've written some records, flush them to disk and
					 * let the startup process and primary server know about
					 * them.
					 */
					XLogWalRcvFlush(false, startpointTLI);
				}

				/* Check if we need to exit the streaming loop. */
				if (endofwal)
					break;
```

받을 것이 없으면 소켓과 latch 를 함께 기다린다. 깨어난 이유에 따라 보고를 보낸다.

`replication` / `walreceiver.c` L595-L665 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L595-L665))

```c
// replication/walreceiver.c L595-L665
				rc = WaitLatchOrSocket(MyLatch,
									   WL_EXIT_ON_PM_DEATH | WL_SOCKET_READABLE |
									   WL_TIMEOUT | WL_LATCH_SET,
									   wait_fd,
									   nap,
									   WAIT_EVENT_WAL_RECEIVER_MAIN);
				if (rc & WL_LATCH_SET)
				{
					ResetLatch(MyLatch);
					CHECK_FOR_INTERRUPTS();

					if (walrcv->force_reply)
					{
						/*
						 * The recovery process has asked us to send apply
						 * feedback now.  Make sure the flag is really set to
						 * false in shared memory before sending the reply, so
						 * we don't miss a new request for a reply.
						 */
						walrcv->force_reply = false;
						pg_memory_barrier();
						XLogWalRcvSendReply(true, false);
					}
				}
				if (rc & WL_TIMEOUT)
				{
					/*
					 * We didn't receive anything new. If we haven't heard
					 * anything from the server for more than
					 * wal_receiver_timeout / 2, ping the server. Also, if
					 * it's been longer than wal_receiver_status_interval
					 * since the last update we sent, send a status update to
					 * the primary anyway, to report any progress in applying
					 * WAL.
					 */
					bool		requestReply = false;

// ... (L632-L639 생략: 주석)
					pgstat_report_wal(false);

					/*
					 * Check if time since last receive from primary has
					 * reached the configured limit.
					 */
					now = GetCurrentTimestamp();
					if (now >= wakeup[WALRCV_WAKEUP_TERMINATE])
						ereport(ERROR,
								(errcode(ERRCODE_CONNECTION_FAILURE),
								 errmsg("terminating walreceiver due to timeout")));

					/*
					 * If we didn't receive anything new for half of receiver
					 * replication timeout, then ping the server.
					 */
					if (now >= wakeup[WALRCV_WAKEUP_PING])
					{
						requestReply = true;
						wakeup[WALRCV_WAKEUP_PING] = TIMESTAMP_INFINITY;
					}

					XLogWalRcvSendReply(requestReply, requestReply);
					XLogWalRcvSendHSFeedback(false);
				}
			}
```

타임라인 끝에 닿으면 마지막 세그먼트를 닫고 startup 의 지시를 기다린다.

`replication` / `walreceiver.c` L667-L716 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L667-L716))

```c
// replication/walreceiver.c L667-L716
			/*
			 * The backend finished streaming. Exit streaming COPY-mode from
			 * our side, too.
			 */
			walrcv_endstreaming(wrconn, &primaryTLI);

			/*
			 * If the server had switched to a new timeline that we didn't
			 * know about when we began streaming, fetch its timeline history
			 * file now.
			 */
			WalRcvFetchTimeLineHistoryFiles(startpointTLI, primaryTLI);
		}
		else
			ereport(LOG,
					(errmsg("primary server contains no more WAL on requested timeline %u",
							startpointTLI)));

		/*
		 * End of WAL reached on the requested timeline. Close the last
		 * segment, and await for new orders from the startup process.
		 */
		if (recvFile >= 0)
		{
			char		xlogfname[MAXFNAMELEN];

			XLogWalRcvFlush(false, startpointTLI);
			XLogFileName(xlogfname, recvFileTLI, recvSegNo, wal_segment_size);
			if (close(recvFile) != 0)
				ereport(PANIC,
						(errcode_for_file_access(),
						 errmsg("could not close WAL segment %s: %m",
								xlogfname)));

			/*
			 * Create .done file forcibly to prevent the streamed segment from
			 * being archived later.
			 */
			if (XLogArchiveMode != ARCHIVE_MODE_ALWAYS)
				XLogArchiveForceDone(xlogfname);
			else
				XLogArchiveNotify(xlogfname);
		}
		recvFile = -1;

		elog(DEBUG1, "walreceiver ended streaming and awaits new instructions");
		WalRcvWaitForStartPosition(&startpoint, &startpointTLI);
	}
	/* not reached */
}
```

## 동작 흐름

```text
 L180  MyBackendType = B_WAL_RECEIVER, AuxiliaryProcessMainCommon
 L197  WalRcv->mutex 아래
 L199    walRcvState 가 STARTING 이 아니면 종료 또는 PANIC
 L225    pid 를 알린다 (startup 이 죽일 수 있게)
 L226    walRcvState = STREAMING
 L230-L234  conninfo, slotname, receiveStart(startpoint), receiveStartTLI 복사
 L248    procno 를 알린다 (startup 이 WalRcvForceReply 로 깨울 수 있게)
 L272  load_file("libpqwalreceiver")     walrcv_* 함수 포인터가 여기서 채워진다
 L281  walrcv_connect(conninfo, true, ...)   --> primary 의 postmaster 가 backend 를 fork
                                                 replication=true 라 그 backend 는 walsender
 L315  for (;;)                                   타임라인 하나에 한 바퀴
 L327    walrcv_identify_system                   --> primary [03] IDENTIFY_SYSTEM
 L331    system identifier 가 다르면 ERROR
 L344    primary 타임라인 < 내 타임라인이면 ERROR
 L378    (cascade) 시작점이 upstream flush 보다 한 세그먼트 안쪽으로 앞서면 기다렸다 다시
 L426    WalRcvFetchTimeLineHistoryFiles
 L433    임시 슬롯이면 walrcv_create_slot
 L462    walrcv_startstreaming                    --> "START_REPLICATION [SLOT s] X/X TIMELINE n"
           true 면 COPY BOTH 모드 진입             primary [04] StartReplication
 L475      LogstreamResult.Write = Flush = GetXLogReplayRecPtr
 L484      XLogWalRcvSendReply(true, false)        첫 보고는 강제
 L488      for (;;)                                메시지 루프
 L502        복구가 끝났으면 FATAL
 L522        len = walrcv_receive                  CopyData 하나 (없으면 0, 끝이면 -1)
 L529        for (;;)  읽을 수 있는 동안
 L541          [07] XLogWalRcvProcessMsg           'w' 면 [08] XLogWalRcvWrite 까지
 L556          len = walrcv_receive
 L560        [10] XLogWalRcvSendReply(false, false)   write 위치가 바뀌었으면 보고
 L567        [09] XLogWalRcvFlush                  fsync, startup 깨우기, 다시 보고
 L595        WaitLatchOrSocket(소켓 | latch | timeout)
 L606        latch 이고 force_reply 면 보고        startup 이 apply 를 알리러 깨운 경우
 L619        timeout 이면
 L647          wal_receiver_timeout 동안 아무것도 못 받았으면 ERROR
 L656          그 절반이 지났으면 requestReply 로 ping
 L662          XLogWalRcvSendReply, HS feedback
 L671    walrcv_endstreaming                      primary 가 타임라인 끝을 알린 경우
 L689    열린 세그먼트를 flush, close, .done 또는 .ready
 L713    WalRcvWaitForStartPosition                startup 이 RequestXLogStreaming 을 다시 부를 때까지
```

안쪽 루프 한 바퀴의 핵심은 **쓰기는 메시지마다, fsync 는 바퀴마다**라는 점이다. 그래서 primary 가 보는 write 위치와 flush 위치는 한 바퀴 안에서 잠깐 벌어진다.

```text
 안쪽 루프 한 바퀴 (메시지 셋이 소켓에 쌓여 있던 경우)

 L522  receive 'w' [0/3000000, +128KB)  -> [08] pwrite      LogstreamResult.Write = 0/3020000
 L556  receive 'w' [0/3020000, +128KB)  -> [08] pwrite      Write = 0/3040000
 L556  receive 'w' [0/3040000, +64KB)   -> [08] pwrite      Write = 0/3050000
 L556  receive -> 0                     -> 안쪽 for 탈출
 L560  [10] SendReply(false,false)   write 0/3050000  flush 0/3000000  apply ...
 L567  [09] Flush                    issue_xlog_fsync     Flush = 0/3050000
                                     WakeupRecovery       startup 이 0/3050000 까지 읽어도 된다
                                     [10] SendReply       write 0/3050000  flush 0/3050000

 메시지 크기 128KB 는 primary 의 MAX_SEND_SIZE = XLOG_BLCKSZ * 16 이다 (walsender.c L111)
 바퀴를 시작할 때 Write = Flush = 0/3000000 이었다고 놓았다
```

```text
 시간 제한 셋 (기본값 wal_receiver_timeout 60s, wal_receiver_status_interval 10s)

 wakeup                   line    deadline           지나면
 WALRCV_WAKEUP_TERMINATE  L647    last recv + 60s    ERROR, 프로세스 종료
 WALRCV_WAKEUP_PING       L656    last recv + 30s    requestReply 를 단 보고 (ping)
 WALRCV_WAKEUP_REPLY      L1198   last reply + 10s   바뀐 게 없어도 보고 (XLogWalRcvSendReply)

 무엇이든 받으면 TERMINATE 와 PING 을 다시 잰다 (L538-L540)
```

## 결과가 쓰이는 곳

```text
 pg_wal 의 세그먼트 파일
      --> standby startup 이 XLOG_FROM_STREAM 으로 열어 읽는다 (xlogrecovery.c L3975)

 WalRcv->flushedUpto
      --> startup 이 이 값 아래까지만 읽는다 (GetWalRcvFlushRecPtr, xlogrecovery.c L3939)

 primary 로 가는 'r' 메시지
      --> primary walsender 의 [11] ProcessStandbyReplyMessage

 walreceiver 가 끝나면 (ERROR, timeout)
      --> WalRcvDie 가 startup 을 깨우고, startup 은 다른 WAL 출처로 가거나 다시 요청한다
```

## 다루지 않는 것

`libpqwalreceiver` 의 libpq 호출 내부(`libpqrcv_connect`, `libpqrcv_receive` 의 `PQgetCopyData`), 타임라인 history 파일 받기(`WalRcvFetchTimeLineHistoryFiles`), hot standby feedback(`XLogWalRcvSendHSFeedback`), 임시 슬롯 생성, cascade standby 의 upstream 따라잡기 대기(L350-L414), 종료 처리(`WalRcvDie`)는 요약만 했다.
