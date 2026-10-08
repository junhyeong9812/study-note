# RequestXLogStreaming

상위: [스트리밍 복제](../README.md)

**standby 의 startup 프로세스가 "이 위치부터 WAL 을 받아 와 달라"고 공유 메모리 `WalRcv` 에 적고 postmaster 에 신호를 보내는 함수다.** walreceiver 는 startup 이 직접 fork 하지 않는다. startup 은 요청만 남기고, postmaster 가 다음 상태 점검에서 walreceiver 를 띄운다. 시작 위치는 언제나 세그먼트 머리로 내려 잡는다.

## 위치

`replication` / `walreceiverfuncs.c` L246-L325 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiverfuncs.c#L246-L325))

## 실제 코드

startup 프로세스가 WAL 을 기다리다 스트리밍으로 넘어가는 자리다. 이 함수의 유일한 호출처다.

`access/transam` / `xlogrecovery.c` L3878-L3910 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L3878-L3910))

```c
// access/transam/xlogrecovery.c L3878-L3910
					if (startWalReceiver &&
						PrimaryConnInfo && strcmp(PrimaryConnInfo, "") != 0)
					{
						XLogRecPtr	ptr;
						TimeLineID	tli;

// ... (L3884-L3903 생략: 체크포인트를 읽는 중이면 RedoStartLSN, 아니면 RecPtr 와 그 타임라인을 고른다)
						curFileTLI = tli;
						SetInstallXLogFileSegmentActive();
						RequestXLogStreaming(tli, ptr, PrimaryConnInfo,
											 PrimarySlotName,
											 wal_receiver_create_temp_slot);
						flushedUpto = 0;
					}
```

요청을 공유 메모리에 적고 postmaster 를 깨운다.

`replication` / `walreceiverfuncs.c` L246-L325 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiverfuncs.c#L246-L325))

```c
// replication/walreceiverfuncs.c L246-L325
RequestXLogStreaming(TimeLineID tli, XLogRecPtr recptr, const char *conninfo,
					 const char *slotname, bool create_temp_slot)
{
	WalRcvData *walrcv = WalRcv;
	bool		launch = false;
	pg_time_t	now = (pg_time_t) time(NULL);
	ProcNumber	walrcv_proc;

	/*
	 * We always start at the beginning of the segment. That prevents a broken
	 * segment (i.e., with no records in the first half of a segment) from
	 * being created by XLOG streaming, which might cause trouble later on if
	 * the segment is e.g archived.
	 */
	if (XLogSegmentOffset(recptr, wal_segment_size) != 0)
		recptr -= XLogSegmentOffset(recptr, wal_segment_size);

	SpinLockAcquire(&walrcv->mutex);

	/* It better be stopped if we try to restart it */
	Assert(walrcv->walRcvState == WALRCV_STOPPED ||
		   walrcv->walRcvState == WALRCV_WAITING);

// ... (L269-L274 생략: 주석)
	if (slotname != NULL && slotname[0] != '\0')
	{
		strlcpy(walrcv->slotname, slotname, NAMEDATALEN);
		walrcv->is_temp_slot = false;
	}
	else
	{
		walrcv->slotname[0] = '\0';
		walrcv->is_temp_slot = create_temp_slot;
	}

// ... (L286-L289 생략: 주석)
	if (walrcv->walRcvState == WALRCV_STOPPED)
	{
		launch = true;
		walrcv->walRcvState = WALRCV_STARTING;

		if (conninfo != NULL)
			strlcpy(walrcv->conninfo, conninfo, MAXCONNINFO);
		else
			walrcv->conninfo[0] = '\0';
	}
	else
		walrcv->walRcvState = WALRCV_RESTARTING;
	walrcv->startTime = now;

// ... (L304-L307 생략: 주석)
	if (walrcv->receiveStart == 0 || walrcv->receivedTLI != tli)
	{
		walrcv->flushedUpto = recptr;
		walrcv->receivedTLI = tli;
		walrcv->latestChunkStart = recptr;
	}
	walrcv->receiveStart = recptr;
	walrcv->receiveStartTLI = tli;

	walrcv_proc = walrcv->procno;

	SpinLockRelease(&walrcv->mutex);

	if (launch)
		SendPostmasterSignal(PMSIGNAL_START_WALRECEIVER);
	else if (walrcv_proc != INVALID_PROC_NUMBER)
		SetLatch(&GetPGProcByNumber(walrcv_proc)->procLatch);
}
```

postmaster 는 신호를 받아 깃발만 세우고, 상태 점검 함수에서 walreceiver 를 띄운다.

`postmaster` / `postmaster.c` L3786-L3790 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L3786-L3790))

```c
// postmaster/postmaster.c L3786-L3790
	if (CheckPostmasterSignal(PMSIGNAL_START_WALRECEIVER))
	{
		/* Startup Process wants us to start the walreceiver process. */
		WalReceiverRequested = true;
	}
```

`postmaster` / `postmaster.c` L3357-L3369 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L3357-L3369))

```c
// postmaster/postmaster.c L3357-L3369
	if (WalReceiverRequested)
	{
		if (WalReceiverPMChild == NULL &&
			(pmState == PM_STARTUP || pmState == PM_RECOVERY ||
			 pmState == PM_HOT_STANDBY) &&
			Shutdown <= SmartShutdown)
		{
			WalReceiverPMChild = StartChildProcess(B_WAL_RECEIVER);
			if (WalReceiverPMChild != 0)
				WalReceiverRequested = false;
			/* else leave the flag set, so we'll try again later */
		}
	}
```

## 동작 흐름

```text
 standby 안, 세 프로세스가 공유 메모리 WalRcv 하나로 말을 주고받는다

 startup                          postmaster                    walreceiver
 WaitForWALToBecomeAvailable
   xlogrecovery.c L3906
   RequestXLogStreaming
     L260  시작 위치를 세그먼트 머리로
     L263  SpinLockAcquire(walrcv->mutex)
     L290  STOPPED 면 launch = true
           walRcvState = STARTING
           conninfo 복사 (primary_conninfo)
     L300  아니면 (WAITING) RESTARTING
     L308  처음이거나 타임라인이 바뀌었으면
           flushedUpto = latestChunkStart = recptr
     L314  receiveStart = recptr
     L322  SendPostmasterSignal ---------> L3786 PMSIGNAL_START_WALRECEIVER
           (START_WALRECEIVER)                  WalReceiverRequested = true
                                          L3357 다음 점검에서
                                          L3364 StartChildProcess(B_WAL_RECEIVER)
                                                     | fork
                                                     v
                                                                [02] WalReceiverMain
                                                                  walrcv->receiveStart 를 읽는다
     L324  이미 떠 있으면 (RESTARTING)
           walreceiver 의 latch 만 깨운다 ------------------------> WalRcvWaitForStartPosition 이 깨어난다
```

시작 위치를 세그먼트 머리로 내리는 이유는 L254-L258 주석에 있다. 앞 절반에 레코드가 없는 깨진 세그먼트가 스트리밍으로 만들어져 나중에 아카이브되는 일을 막는다.

```text
 시작 위치 내리기 (wal_segment_size 기본 16MB = 0x1000000)

 startup 이 필요한 위치   RecPtr = 0/3000060
 XLogSegmentOffset        0x3000060 % 0x1000000 = 0x60
 recptr                   0x3000060 - 0x60     = 0/3000000

 walreceiver 는 0/3000000 부터 START_REPLICATION 을 보내고
 앞부분 0x60 바이트도 받아 그 세그먼트 파일의 오프셋 0 부터 쓴다
   walsender 는 sentPtr = startpoint 에서 보내기 시작하고 (walsender.c L962)
   XLogWalRcvWrite 는 startoff = XLogSegmentOffset(dataStart) 자리에 pwrite 한다 (walreceiver.c L992, L1008)
 같은 타임라인의 그 세그먼트 파일이 pg_wal 에 이미 있으면 XLogFileInit 이 그 파일을 그대로 열므로
 (access/transam/xlog.c L3207-L3217) 이미 있던 0x60 바이트를 같은 자리에 다시 쓰는 셈이 된다
```

```text
 WalRcv->walRcvState 의 전이 (이 함수가 쓰는 두 칸)

 STOPPED  --RequestXLogStreaming L293-->  STARTING  --WalReceiverMain L226-->  STREAMING
 WAITING  --RequestXLogStreaming L301-->  RESTARTING --WalRcvWaitForStartPosition L768-->  STREAMING

 WAITING 은 walreceiver 가 한 타임라인 끝까지 받고 다음 지시를 기다리는 상태다
 (walreceiver.c L713 에서 WalRcvWaitForStartPosition 을 불러 L737 에서 WAITING 으로 바꾼다)
```

## 결과가 쓰이는 곳

```text
 walrcv->receiveStart, receiveStartTLI
      --> [02] WalReceiverMain 이 startpoint 로 읽어 START_REPLICATION 의 시작점으로 쓴다 (walreceiver.c L233)

 walrcv->flushedUpto
      --> startup 이 GetWalRcvFlushRecPtr 로 읽는다. 여기까지는 디스크에 있다는 뜻이다 (xlogrecovery.c L3939)
          이후로는 [09] XLogWalRcvFlush 가 올린다

 walrcv->conninfo, slotname
      --> walrcv_connect 와 START_REPLICATION SLOT 에 쓰인다
```

## 다루지 않는 것

`WaitForWALToBecomeAvailable` 의 WAL 출처 상태 기계(아카이브, `pg_wal`, 스트리밍 사이의 전환)는 [WAL redo](../../wal-redo/README.md) 흐름의 몫이라 호출 자리만 보였다. `ShutdownWalRcv`, `primary_conninfo` 변경 시 재시작(`pendingWalRcvRestart`), 임시 슬롯 생성 옵션(`wal_receiver_create_temp_slot`)은 요약만 했다.
