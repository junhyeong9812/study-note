# StartReplication

상위: [스트리밍 복제](../README.md)

**물리 복제의 `START_REPLICATION` 을 처리하는 함수이고, 이 흐름의 primary 쪽 진입점이다.** 보낼 타임라인과 그 끝을 정하고, `CopyBothResponse` 로 연결을 양방향 COPY 모드로 바꾼 뒤, 시작 위치를 `sentPtr` 에 넣고 [05] `WalSndLoop(XLogSendPhysical)` 에 들어간다. 요청한 시작점이 이 서버가 디스크에 flush 한 위치를 넘으면(FlushPtr < startpoint) 거절한다. 아직 디스크에 없는 WAL 은 보내지 않는다는 규칙이 여기서 처음 나온다.

## 위치

`replication` / `walsender.c` L809-L1030 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L809-L1030))

## 실제 코드

WAL 을 읽을 xlogreader 를 만들고, 슬롯 이름이 있으면 슬롯을 잡는다.

`replication` / `walsender.c` L809-L850 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L809-L850))

```c
// replication/walsender.c L809-L850
StartReplication(StartReplicationCmd *cmd)
{
	StringInfoData buf;
	XLogRecPtr	FlushPtr;
	TimeLineID	FlushTLI;

	/* create xlogreader for physical replication */
	xlogreader =
		XLogReaderAllocate(wal_segment_size, NULL,
						   XL_ROUTINE(.segment_open = WalSndSegmentOpen,
									  .segment_close = wal_segment_close),
						   NULL);

	if (!xlogreader)
		ereport(ERROR,
				(errcode(ERRCODE_OUT_OF_MEMORY),
				 errmsg("out of memory"),
				 errdetail("Failed while allocating a WAL reading processor.")));

// ... (L828-L836 생략: 주석)
	if (cmd->slotname)
	{
		ReplicationSlotAcquire(cmd->slotname, true, true);
		if (SlotIsLogical(MyReplicationSlot))
			ereport(ERROR,
					(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
					 errmsg("cannot use a logical replication slot for physical replication")));

// ... (L845-L849 생략: 주석)
	}
```

보낼 타임라인을 정한다. 지금 타임라인이면 끝이 없고, 지난 타임라인이면 갈라진 지점이 끝이다.

`replication` / `walsender.c` L852-L924 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L852-L924))

```c
// replication/walsender.c L852-L924
	/*
	 * Select the timeline. If it was given explicitly by the client, use
	 * that. Otherwise use the timeline of the last replayed record.
	 */
	am_cascading_walsender = RecoveryInProgress();
	if (am_cascading_walsender)
		FlushPtr = GetStandbyFlushRecPtr(&FlushTLI);
	else
		FlushPtr = GetFlushRecPtr(&FlushTLI);

	if (cmd->timeline != 0)
	{
		XLogRecPtr	switchpoint;

		sendTimeLine = cmd->timeline;
		if (sendTimeLine == FlushTLI)
		{
			sendTimeLineIsHistoric = false;
			sendTimeLineValidUpto = InvalidXLogRecPtr;
		}
		else
		{
			List	   *timeLineHistory;

			sendTimeLineIsHistoric = true;

// ... (L878-L904 생략: 주석)
			if (!XLogRecPtrIsInvalid(switchpoint) &&
				switchpoint < cmd->startpoint)
			{
				ereport(ERROR,
						(errmsg("requested starting point %X/%X on timeline %u is not in this server's history",
								LSN_FORMAT_ARGS(cmd->startpoint),
								cmd->timeline),
						 errdetail("This server's history forked from timeline %u at %X/%X.",
								   cmd->timeline,
								   LSN_FORMAT_ARGS(switchpoint))));
			}
			sendTimeLineValidUpto = switchpoint;
		}
	}
	else
	{
		sendTimeLine = FlushTLI;
		sendTimeLineValidUpto = InvalidXLogRecPtr;
		sendTimeLineIsHistoric = false;
	}
```

COPY BOTH 모드로 들어가 루프를 돈다. 루프에서 나오면 다음 타임라인을 알리고 명령을 끝낸다.

`replication` / `walsender.c` L926-L1030 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L926-L1030))

```c
// replication/walsender.c L926-L1030
	streamingDoneSending = streamingDoneReceiving = false;

	/* If there is nothing to stream, don't even enter COPY mode */
	if (!sendTimeLineIsHistoric || cmd->startpoint < sendTimeLineValidUpto)
	{
// ... (L931-L939 생략: 주석)
		WalSndSetState(WALSNDSTATE_CATCHUP);

		/* Send a CopyBothResponse message, and start streaming */
		pq_beginmessage(&buf, PqMsg_CopyBothResponse);
		pq_sendbyte(&buf, 0);
		pq_sendint16(&buf, 0);
		pq_endmessage(&buf);
		pq_flush();

		/*
		 * Don't allow a request to stream from a future point in WAL that
		 * hasn't been flushed to disk in this server yet.
		 */
		if (FlushPtr < cmd->startpoint)
		{
			ereport(ERROR,
					(errmsg("requested starting point %X/%X is ahead of the WAL flush position of this server %X/%X",
							LSN_FORMAT_ARGS(cmd->startpoint),
							LSN_FORMAT_ARGS(FlushPtr))));
		}

		/* Start streaming from the requested point */
		sentPtr = cmd->startpoint;

		/* Initialize shared memory status, too */
		SpinLockAcquire(&MyWalSnd->mutex);
		MyWalSnd->sentPtr = sentPtr;
		SpinLockRelease(&MyWalSnd->mutex);

		SyncRepInitConfig();

		/* Main loop of walsender */
		replication_active = true;

		WalSndLoop(XLogSendPhysical);

		replication_active = false;
		if (got_STOPPING)
			proc_exit(0);
		WalSndSetState(WALSNDSTATE_STARTUP);

		Assert(streamingDoneSending && streamingDoneReceiving);
	}

	if (cmd->slotname)
		ReplicationSlotRelease();

	/*
	 * Copy is finished now. Send a single-row result set indicating the next
	 * timeline.
	 */
	if (sendTimeLineIsHistoric)
	{
// ... (L993-L1025 생략: 다음 타임라인 번호와 시작 위치를 한 행짜리 결과로 보낸다)
	}

	/* Send CommandComplete message */
	EndReplicationCommand("START_STREAMING");
}
```

## 동작 흐름

```text
 L816  XLogReaderAllocate(WalSndSegmentOpen)     물리 복제는 레코드를 해석하지 않는다
                                                 파일을 열고 위치를 기억하는 용도다
 L837  slotname 이 있으면 ReplicationSlotAcquire  논리 슬롯이면 ERROR
 L856  am_cascading_walsender = RecoveryInProgress()
 L858    standby 면 FlushPtr = GetStandbyFlushRecPtr   받았거나 replay 한 끝
 L860    primary 면 FlushPtr = GetFlushRecPtr          이 서버가 fsync 한 끝
 L862  TIMELINE n 이 왔고
 L867    n == FlushTLI 면  현재 타임라인, 끝 없음 (ValidUpto = Invalid)
 L872    아니면           history 파일에서 n 이 갈라진 switchpoint 를 찾는다
 L905      switchpoint < startpoint 면 ERROR      그 타임라인에는 그 위치가 없다
 L916      sendTimeLineValidUpto = switchpoint
 L929  보낼 것이 있으면
 L940    WalSndSetState(CATCHUP)
 L943    CopyBothResponse ('W') 를 보내고 flush    --> walreceiver 의 PQexec 가 PGRES_COPY_BOTH 를 받는다
 L953    FlushPtr < startpoint 면 ERROR            "ahead of the WAL flush position"
 L962    sentPtr = startpoint
 L966    MyWalSnd->sentPtr = sentPtr               pg_stat_replication.sent_lsn
 L969    SyncRepInitConfig                         synchronous_standby_names 에서 내 우선순위
 L974    [05] WalSndLoop(XLogSendPhysical)         여기서 오래 머문다
 L979    루프를 나오면 STARTUP 상태로
 L991  지난 타임라인을 다 보냈으면 (next_tli, next_tli_startpos) 한 행
 L1029 CommandComplete "START_STREAMING"
```

COPY BOTH 모드에 들어간 뒤에는 한 연결 위로 두 방향의 CopyData(`'d'`) 가 동시에 흐른다. 그 안의 첫 바이트가 메시지 종류다.

```text
 primary walsender                                       standby walreceiver
 L943  CopyBothResponse 'W'  ------------------------->  PGRES_COPY_BOTH, [02] L462 true
        'd' + 'w' XLogData    ------------------------->  [07] XLogWalRcvProcessMsg 'w'
            dataStart, walEnd, sendTime, WAL 바이트         (walsender.c L3351-L3355)
        'd' + 'k' keepalive   ------------------------->  [07] 'k'
            walEnd, sendTime, replyRequested                (walsender.c L4122-L4125)
                              <-------------------------  'd' + 'r' 위치 보고  [10]
                                                             write, flush, apply, time, replyRequested
                              <-------------------------  'd' + 'h' hot standby feedback
        'c' CopyDone          <------------------------>  어느 쪽이든 끝내자고 할 때
```

```text
 타임라인 고르기 예 (standby 가 TLI 1 을 따라오다 primary 가 TLI 2 로 승격된 뒤라고 놓는다)

 primary 의 FlushTLI = 2, 00000002.history 에 "1  0/5000000" (TLI 1 은 0/5000000 에서 갈라짐)

 START_REPLICATION 0/4000000 TIMELINE 1
   L876  sendTimeLineIsHistoric = true
   L883  switchpoint = 0/5000000, sendTimeLineNextTLI = 2
   L905  0/5000000 < 0/4000000 ? 아니다 -> 통과
   L916  sendTimeLineValidUpto = 0/5000000
   -> 0/4000000 부터 0/5000000 까지 보내고 CopyDone (XLogSendPhysical L3287)
   -> L991 결과 행 (2, "0/5000000")
   -> walreceiver 는 startup 에게 돌아가고 TLI 2 로 다시 START_REPLICATION 한다

 START_REPLICATION 0/6000000 TIMELINE 1 이었다면
   L905  0/5000000 < 0/6000000 -> ERROR "not in this server's history"
```

## 결과가 쓰이는 곳

```text
 sentPtr, sendTimeLine, sendTimeLineValidUpto, sendTimeLineIsHistoric (파일 전역)
      --> [06] XLogSendPhysical 이 어디부터 어디까지 보낼지 정한다

 MyWalSnd->state = CATCHUP
      --> [05] 이 다 따라잡으면 STREAMING 으로 바꾼다
      --> SyncRepReleaseWaiters 는 STREAMING 이나 STOPPING 일 때만 대기자를 깨운다 (syncrep.c L493-L495)

 MyWalSnd->sync_standby_priority (SyncRepInitConfig)
      --> [12] SyncRepReleaseWaiters 가 이 walsender 가 동기 standby 후보인지 본다
```

## 다루지 않는 것

타임라인 history 파일 읽기(`readTimeLineHistory`, `tliSwitchPoint`), 슬롯 획득과 해제의 내부, cascade standby 에서의 `GetStandbyFlushRecPtr`, 논리 복제의 `StartLogicalReplication` 은 요약만 했다.
