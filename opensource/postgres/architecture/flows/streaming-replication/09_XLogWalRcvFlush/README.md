# XLogWalRcvFlush

상위: [스트리밍 복제](../README.md)

**지금까지 쓴 WAL 을 fsync 하고, 그 사실을 세 곳에 알리는 함수다.** 공유 메모리의 `flushedUpto` 를 올려 startup 프로세스가 거기까지 읽게 하고, startup 의 latch 를 깨우고, primary 에 새 flush 위치를 보고한다. standby 의 startup(redo)이 스트리밍된 WAL 을 만지는 문은 이 함수가 연다.

## 위치

`replication` / `walreceiver.c` L1062-L1106 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L1062-L1106))

## 실제 코드

`replication` / `walreceiver.c` L1062-L1106 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L1062-L1106))

```c
// replication/walreceiver.c L1062-L1106
XLogWalRcvFlush(bool dying, TimeLineID tli)
{
	Assert(tli != 0);

	if (LogstreamResult.Flush < LogstreamResult.Write)
	{
		WalRcvData *walrcv = WalRcv;

		issue_xlog_fsync(recvFile, recvSegNo, tli);

		LogstreamResult.Flush = LogstreamResult.Write;

		/* Update shared-memory status */
		SpinLockAcquire(&walrcv->mutex);
		if (walrcv->flushedUpto < LogstreamResult.Flush)
		{
			walrcv->latestChunkStart = walrcv->flushedUpto;
			walrcv->flushedUpto = LogstreamResult.Flush;
			walrcv->receivedTLI = tli;
		}
		SpinLockRelease(&walrcv->mutex);

		/* Signal the startup process and walsender that new WAL has arrived */
		WakeupRecovery();
		if (AllowCascadeReplication())
			WalSndWakeup(true, false);

		/* Report XLOG streaming progress in PS display */
		if (update_process_title)
		{
			char		activitymsg[50];

			snprintf(activitymsg, sizeof(activitymsg), "streaming %X/%X",
					 LSN_FORMAT_ARGS(LogstreamResult.Write));
			set_ps_display(activitymsg);
		}

		/* Also let the primary know that we made some progress */
		if (!dying)
		{
			XLogWalRcvSendReply(false, false);
			XLogWalRcvSendHSFeedback(false);
		}
	}
}
```

startup 쪽에서 보면 이렇다. `flushedUpto` 를 읽어 그 아래면 세그먼트를 연다.

`access/transam` / `xlogrecovery.c` L3933-L3951 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L3933-L3951))

```c
// access/transam/xlogrecovery.c L3933-L3951
					if (RecPtr < flushedUpto)
						havedata = true;
					else
					{
						XLogRecPtr	latestChunkStart;

						flushedUpto = GetWalRcvFlushRecPtr(&latestChunkStart, &receiveTLI);
						if (RecPtr < flushedUpto && receiveTLI == curFileTLI)
						{
							havedata = true;
// ... (L3943-L3947 생략: XLogReceiptTime 갱신)
						}
						else
							havedata = false;
					}
```

데이터가 아직 없으면 startup 은 latch 에서 잔다. 이 함수의 `WakeupRecovery` 가 그 latch 를 깨운다.

`access/transam` / `xlogrecovery.c` L4530-L4534 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L4530-L4534))

```c
// access/transam/xlogrecovery.c L4530-L4534
void
WakeupRecovery(void)
{
	SetLatch(&XLogRecoveryCtl->recoveryWakeupLatch);
}
```

## 동작 흐름

```text
 L1066  Flush < Write 일 때만 (새로 쓴 게 없으면 아무것도 안 한다)
 L1070    issue_xlog_fsync(recvFile)          wal_sync_method 대로 fsync / fdatasync / ...
 L1072    LogstreamResult.Flush = Write
 L1075    WalRcv->mutex 아래
 L1078      latestChunkStart = 이전 flushedUpto
 L1079      flushedUpto = Flush
 L1080      receivedTLI = tli
 L1085    WakeupRecovery                      startup 의 recoveryWakeupLatch
 L1086    cascade 허용이면 WalSndWakeup(true, false)   이 standby 에 붙은 하위 walsender
 L1100    죽는 중이 아니면
 L1102      [10] XLogWalRcvSendReply(false, false)   flush 가 바뀌었으니 보낸다
 L1103      XLogWalRcvSendHSFeedback(false)
```

스트리밍 중 walreceiver 가 받은 WAL 을 startup 에게 넘기는 길은 이 함수 하나다. walreceiver 안에서 `flushedUpto` 를 올리는 곳은 L1079 뿐이다(그 밖에는 [01] RequestXLogStreaming 이 시작 위치로 초기화할 때). 넘기는 쪽 방향으로는 파일과 공유 메모리 한 칸(`flushedUpto`)과 latch 하나로 이어지고, 거꾸로 startup 이 walreceiver 를 부르는 길은 [01] 의 시작 요청과 `WalRcvForceReply` 다.

```text
 standby 안의 두 프로세스

 walreceiver                                     startup (redo)
 [08] pwrite -> pg_wal/0000...03                 ReadRecord -> XLogPageRead
 [09] fsync                                        -> WaitForWALToBecomeAvailable
      WalRcv->flushedUpto = 0/3050000                  L3939 GetWalRcvFlushRecPtr -> 0/3050000
      WakeupRecovery  ---- latch ---->                  L3933 RecPtr < flushedUpto 면 읽는다
                                                        L3975 XLogFileRead(XLOG_FROM_STREAM)
                                                    ApplyWalRecord -> rm_redo
                                                      lastReplayedEndRecPtr 를 올린다 (xlogrecovery.c L2039)
 [10] 'r' 의 apply = GetXLogReplayRecPtr  <---- 공유 메모리에서 읽는다 (walreceiver.c L1207)

 다 따라잡으면 startup 은 WalRcvForceReply 로 walreceiver 를 깨워 apply 를 보고시키고
 (xlogrecovery.c L4021) recoveryWakeupLatch 에서 다음 WakeupRecovery 를 기다린다
```

```text
 flushedUpto 와 latestChunkStart 의 예

 바퀴 1 끝  flushedUpto 0/3000000 -> 0/3050000,  latestChunkStart = 0/3000000
 바퀴 2 끝  flushedUpto 0/3050000 -> 0/3080000,  latestChunkStart = 0/3050000

 startup 이 RecPtr = 0/3052000 을 읽으려 할 때
   0/3052000 < 0/3080000 -> havedata
   latestChunkStart 0/3050000 <= RecPtr -> XLogReceiptTime = now   (L3943-L3946)
     따라잡고 있다는 뜻이다. 뒤처져 있으면 XLogReceiptTime 이 멈춰 hot standby 쿼리 충돌 유예가 준다
```

## 결과가 쓰이는 곳

```text
 WalRcv->flushedUpto
      --> startup 의 WaitForWALToBecomeAvailable 이 읽을 한계 (xlogrecovery.c L3939)
          --> [WAL redo] ApplyWalRecord 가 레코드를 적용한다

 LogstreamResult.Flush
      --> [10] 'r' 의 flush. 동기 복제 on (remote_flush) 이 이 값을 기다린다

 WakeupRecovery
      --> startup 이 recoveryWakeupLatch 에서 깨어난다
```

## 다루지 않는 것

`issue_xlog_fsync` 의 `wal_sync_method` 별 분기, cascade 복제에서 하위 walsender 가 보내는 범위(`GetStandbyFlushRecPtr`), startup 쪽 WAL 출처 상태 기계 전체는 [WAL redo](../../wal-redo/README.md) 몫이라 만나는 자리만 보였다.
