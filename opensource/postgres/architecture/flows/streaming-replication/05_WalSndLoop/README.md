# WalSndLoop

상위: [스트리밍 복제](../README.md)

**walsender 의 메인 루프다.** 한 바퀴마다 standby 의 답장을 먼저 읽고(`ProcessRepliesIfAny`), 출력 버퍼가 비었으면 [06] `XLogSendPhysical` 로 다음 조각을 채워 보내고, 보낼 것이 없으면 잠든다. 잠을 깨우는 것은 셋이다. 소켓에 standby 의 답장이 오거나, 이 서버의 WAL 이 더 flush 되었다는 broadcast 가 오거나, `wal_sender_timeout` 의 절반이 지나 keepalive 를 보낼 때가 되거나다.

## 위치

`replication` / `walsender.c` L2828-L2966 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2828-L2966))

## 실제 코드

`replication` / `walsender.c` L2828-L2966 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2828-L2966))

```c
// replication/walsender.c L2828-L2966
WalSndLoop(WalSndSendDataCallback send_data)
{
	TimestampTz last_flush = 0;

// ... (L2832-L2835 생략: 주석)
	last_reply_timestamp = GetCurrentTimestamp();
	waiting_for_ping_response = false;

// ... (L2839-L2842 생략: 주석)
	for (;;)
	{
		/* Clear any already-pending wakeups */
		ResetLatch(MyLatch);

		CHECK_FOR_INTERRUPTS();

		/* Process any requests or signals received recently */
		if (ConfigReloadPending)
		{
			ConfigReloadPending = false;
			ProcessConfigFile(PGC_SIGHUP);
			SyncRepInitConfig();
		}

		/* Check for input from the client */
		ProcessRepliesIfAny();

// ... (L2861-L2865 생략: 주석)
		if (streamingDoneReceiving && streamingDoneSending &&
			!pq_is_send_pending())
			break;

// ... (L2870-L2875 생략: 주석)
		if (!pq_is_send_pending())
			send_data();
		else
			WalSndCaughtUp = false;

		/* Try to flush pending output to the client */
		if (pq_flush_if_writable() != 0)
			WalSndShutdown();

		/* If nothing remains to be sent right now ... */
		if (WalSndCaughtUp && !pq_is_send_pending())
		{
			/*
			 * If we're in catchup state, move to streaming.  This is an
			 * important state change for users to know about, since before
			 * this point data loss might occur if the primary dies and we
			 * need to failover to the standby. The state change is also
			 * important for synchronous replication, since commits that
			 * started to wait at that point might wait for some time.
			 */
			if (MyWalSnd->state == WALSNDSTATE_CATCHUP)
			{
				ereport(DEBUG1,
						(errmsg_internal("\"%s\" has now caught up with upstream server",
										 application_name)));
				WalSndSetState(WALSNDSTATE_STREAMING);
			}

// ... (L2904-L2910 생략: 주석)
			if (got_SIGUSR2)
				WalSndDone(send_data);
		}

		/* Check for replication timeout. */
		WalSndCheckTimeOut();

		/* Send keepalive if the time has come */
		WalSndKeepaliveIfNecessary();

// ... (L2921-L2929 생략: 주석)
		if ((WalSndCaughtUp && send_data != XLogSendLogical &&
			 !streamingDoneSending) ||
			pq_is_send_pending())
		{
			long		sleeptime;
			int			wakeEvents;
			TimestampTz now;

			if (!streamingDoneReceiving)
				wakeEvents = WL_SOCKET_READABLE;
			else
				wakeEvents = 0;

// ... (L2943-L2946 생략: 주석)
			now = GetCurrentTimestamp();
			sleeptime = WalSndComputeSleeptime(now);

			if (pq_is_send_pending())
				wakeEvents |= WL_SOCKET_WRITEABLE;

// ... (L2953-L2960 생략: IO 통계 보고)

			/* Sleep until something happens or we time out */
			WalSndWait(wakeEvents, sleeptime, WAIT_EVENT_WAL_SENDER_MAIN);
		}
	}
}
```

잠드는 자리다. 물리 walsender 는 `wal_flush_cv` 의 대기 목록에 이름만 올리고, 실제로는 소켓과 latch 를 기다린다.

`replication` / `walsender.c` L3803-L3817 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L3803-L3817))

```c
// replication/walsender.c L3803-L3817
	if (wait_event == WAIT_EVENT_WAIT_FOR_STANDBY_CONFIRMATION)
		ConditionVariablePrepareToSleep(&WalSndCtl->wal_confirm_rcv_cv);
	else if (MyWalSnd->kind == REPLICATION_KIND_PHYSICAL)
		ConditionVariablePrepareToSleep(&WalSndCtl->wal_flush_cv);
	else if (MyWalSnd->kind == REPLICATION_KIND_LOGICAL)
		ConditionVariablePrepareToSleep(&WalSndCtl->wal_replay_cv);

	if (WaitEventSetWait(FeBeWaitSet, timeout, &event, 1, wait_event) == 1 &&
		(event.events & WL_POSTMASTER_DEATH))
	{
		ConditionVariableCancelSleep();
		proc_exit(1);
	}

	ConditionVariableCancelSleep();
```

깨우는 쪽이다. primary 에서 WAL 을 fsync 한 `XLogWrite` 가 깨울 일을 적어 두고, 잠금을 놓은 뒤 `XLogFlush` 가 broadcast 한다.

`access/transam` / `xlog.c` L2550-L2556 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2550-L2556))

```c
// access/transam/xlog.c L2550-L2556
			issue_xlog_fsync(openLogFile, openLogSegNo, tli);
		}

		/* signal that we need to wakeup walsenders later */
		WalSndWakeupRequest();

		LogwrtResult.Flush = LogwrtResult.Write;
```

`access/transam` / `xlog.c` L2910-L2913 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2910-L2913))

```c
// access/transam/xlog.c L2910-L2913
	END_CRIT_SECTION();

	/* wake up walsenders now that we've released heavily contended locks */
	WalSndWakeupProcessRequests(true, !RecoveryInProgress());
```

`replication` / `walsender.c` L3748-L3761 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L3748-L3761))

```c
// replication/walsender.c L3748-L3761
WalSndWakeup(bool physical, bool logical)
{
// ... (L3750-L3755 생략: 주석)
	if (physical)
		ConditionVariableBroadcast(&WalSndCtl->wal_flush_cv);

	if (logical)
		ConditionVariableBroadcast(&WalSndCtl->wal_replay_cv);
}
```

## 동작 흐름

```text
 L2836  last_reply_timestamp = now               여기서부터 timeout 이 켜진다
 L2843  for (;;)
 L2846    ResetLatch
 L2851    SIGHUP 이면 설정 다시 읽기 + SyncRepInitConfig
 L2859    ProcessRepliesIfAny                    소켓에 온 것을 막지 않고 전부 읽는다
            'd' 'r' -> [11] ProcessStandbyReplyMessage
            'd' 'h' -> ProcessStandbyHSFeedbackMessage
            'c'     -> streamingDoneReceiving
            'X'/EOF -> proc_exit(0)
 L2866    양쪽 CopyDone 이고 버퍼가 비면 break    --> [04] 로 돌아간다
 L2876    출력 버퍼가 비었으면 [06] send_data()   = XLogSendPhysical
 L2879    아니면 WalSndCaughtUp = false
 L2882    pq_flush_if_writable                   막히지 않는 만큼만 소켓에 쓴다
 L2886    다 따라잡았고 버퍼도 비었으면
 L2896      CATCHUP 이면 STREAMING 으로           동기 복제의 자격이 여기서 생긴다
 L2911      SIGUSR2 면 WalSndDone                 종료 체크포인트까지 보내고 끝
 L2916    WalSndCheckTimeOut                     답장이 wal_sender_timeout 동안 없으면 종료
 L2919    WalSndKeepaliveIfNecessary             절반이 지났으면 'k' + replyRequested
 L2930    (따라잡았거나 보낼 게 남았으면)
 L2939      WL_SOCKET_READABLE                   답장을 기다린다
 L2951      버퍼가 남았으면 WL_SOCKET_WRITEABLE   소켓이 비기를 기다린다
 L2963      WalSndWait(..., sleeptime)
```

이 루프는 standby 쪽 [02] 의 루프와 짝을 이룬다. 한쪽의 송신이 다른 쪽의 수신을 깨운다.

```text
 primary 에서 커밋 하나가 standby 로 가는 길 (비동기, 둘 다 STREAMING 상태)

 backend                         walsender                       walreceiver (standby)
 RecordTransactionCommit
   XLogFlush(commit 끝)
     XLogWrite -> fsync
       L2554 WalSndWakeupRequest
     L2913 WalSndWakeupProcessRequests
       WalSndWakeup
         wal_flush_cv broadcast  --->  L2963 WalSndWait 에서 깬다
                                       L2876 [06] XLogSendPhysical
                                         SendRqstPtr = GetFlushRecPtr
                                         'w' 메시지를 버퍼에
                                       L2882 pq_flush_if_writable  --->  [02] L522 walrcv_receive
                                       L2963 다시 잔다                     [07] [08] pwrite
                                                                           [09] fsync
                                                                           [10] 'r' 보고
                                       L2859 ProcessRepliesIfAny  <---
                                         [11] write/flush/apply 갱신
```

```text
 잠자는 시간 (WalSndComputeSleeptime L2757, 기본 wal_sender_timeout 60s)

 last_reply_timestamp = T 라 하면
   아직 ping 을 안 보냈으면   T + 30s 에 깬다    -> WalSndKeepaliveIfNecessary 가 'k' (replyRequested=1)
   ping 을 보냈으면          T + 60s 에 깬다    -> WalSndCheckTimeOut 이 "replication timeout" 으로 종료
   timeout 이 0 이면         10s 마다 깬다       (L2759)

 standby 는 기본 10s 마다 스스로 보고하므로 (wal_receiver_status_interval)
 정상이면 ping 까지 가지 않는다 (L2795-L2796 주석)
```

## 결과가 쓰이는 곳

```text
 MyWalSnd->state  CATCHUP -> STREAMING
      --> pg_stat_replication.state
      --> [12] SyncRepReleaseWaiters 가 STREAMING 인 walsender 만 대기자를 깨운다

 소켓으로 나간 'w' 와 'k'
      --> standby [07] XLogWalRcvProcessMsg

 ProcessRepliesIfAny 가 읽은 'r'
      --> [11] ProcessStandbyReplyMessage
```

## 다루지 않는 것

종료 순서(`WalSndDone`, `got_STOPPING`, `got_SIGUSR2`), 논리 복제의 `XLogSendLogical` 과 `WalSndWaitForWal`, hot standby feedback 처리(`ProcessStandbyHSFeedbackMessage`), 지연 측정(`LagTrackerWrite`, `LagTrackerRead`)의 내부는 요약만 했다.
