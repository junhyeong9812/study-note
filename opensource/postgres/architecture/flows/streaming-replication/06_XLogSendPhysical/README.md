# XLogSendPhysical

상위: [스트리밍 복제](../README.md)

**보낼 끝(`SendRqstPtr`)을 정하고, `sentPtr` 부터 최대 128KB 를 읽어 `'w'` 메시지 하나로 출력 버퍼에 넣는 함수다.** primary 에서 보낼 끝은 `GetFlushRecPtr`, 곧 이 서버가 **fsync 까지 끝낸 위치**다. 주석은 이유를 둘 든다. `WALRead` 가 쓰인 곳 너머를 읽지 못하고, primary 가 죽었다 살아나면 사라질 WAL 을 standby 가 먼저 적용해서는 안 된다. 메시지 끝은 WAL 페이지 경계로 자르는데, walreceiver 가 레코드 하나가 두 메시지로 쪼개지지 않는다고 기대하기 때문이다.

## 위치

`replication` / `walsender.c` L3140-L3444 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L3140-L3444))

## 실제 코드

보낼 끝을 정한다. 지난 타임라인, cascade standby, primary 세 경우다.

`replication` / `walsender.c` L3140-L3245 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L3140-L3245))

```c
// replication/walsender.c L3140-L3245
XLogSendPhysical(void)
{
	XLogRecPtr	SendRqstPtr;
	XLogRecPtr	startptr;
	XLogRecPtr	endptr;
	Size		nbytes;
	XLogSegNo	segno;
	WALReadError errinfo;
	Size		rbytes;

	/* If requested switch the WAL sender to the stopping state. */
	if (got_STOPPING)
		WalSndSetState(WALSNDSTATE_STOPPING);

	if (streamingDoneSending)
	{
		WalSndCaughtUp = true;
		return;
	}

	/* Figure out how far we can safely send the WAL. */
	if (sendTimeLineIsHistoric)
// ... (L3162-L3167 생략: 주석)
		SendRqstPtr = sendTimeLineValidUpto;
	}
	else if (am_cascading_walsender)
	{
		TimeLineID	SendRqstTLI;

// ... (L3174-L3190 생략: 주석)
// ... (L3191-L3231 생략: cascade standby 의 승격과 타임라인 전환 감지)
	else
	{
		/*
		 * Streaming the current timeline on a primary.
		 *
		 * Attempt to send all data that's already been written out and
		 * fsync'd to disk.  We cannot go further than what's been written out
		 * given the current implementation of WALRead().  And in any case
		 * it's unsafe to send WAL that is not securely down to disk on the
		 * primary: if the primary subsequently crashes and restarts, standbys
		 * must not have applied any WAL that got lost on the primary.
		 */
		SendRqstPtr = GetFlushRecPtr(NULL);
	}
```

보낼 양을 정한다. 128KB 를 넘으면 페이지 경계로 내려 자른다.

`replication` / `walsender.c` L3271-L3345 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L3271-L3345))

```c
// replication/walsender.c L3271-L3345
	LagTrackerWrite(SendRqstPtr, GetCurrentTimestamp());

// ... (L3273-L3286 생략: 주석)
	if (sendTimeLineIsHistoric && sendTimeLineValidUpto <= sentPtr)
	{
		/* close the current file. */
		if (xlogreader->seg.ws_file >= 0)
			wal_segment_close(xlogreader);

		/* Send CopyDone */
		pq_putmessage_noblock('c', NULL, 0);
		streamingDoneSending = true;

		WalSndCaughtUp = true;

		elog(DEBUG1, "walsender reached end of timeline at %X/%X (sent up to %X/%X)",
			 LSN_FORMAT_ARGS(sendTimeLineValidUpto),
			 LSN_FORMAT_ARGS(sentPtr));
		return;
	}

	/* Do we have any work to do? */
	Assert(sentPtr <= SendRqstPtr);
	if (SendRqstPtr <= sentPtr)
	{
		WalSndCaughtUp = true;
		return;
	}

// ... (L3313-L3323 생략: 주석)
	startptr = sentPtr;
	endptr = startptr;
	endptr += MAX_SEND_SIZE;

	/* if we went beyond SendRqstPtr, back off */
	if (SendRqstPtr <= endptr)
	{
		endptr = SendRqstPtr;
		if (sendTimeLineIsHistoric)
			WalSndCaughtUp = false;
		else
			WalSndCaughtUp = true;
	}
	else
	{
		/* round down to page boundary. */
		endptr -= (endptr % XLOG_BLCKSZ);
		WalSndCaughtUp = false;
	}

	nbytes = endptr - startptr;
	Assert(nbytes <= MAX_SEND_SIZE);
```

헤더를 쓰고 WAL 바이트를 버퍼에 바로 읽어 넣은 뒤, 송신 시각을 맨 마지막에 채운다.

`replication` / `walsender.c` L3347-L3433 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L3347-L3433))

```c
// replication/walsender.c L3347-L3433
	/*
	 * OK to read and send the slice.
	 */
	resetStringInfo(&output_message);
	pq_sendbyte(&output_message, 'w');

	pq_sendint64(&output_message, startptr);	/* dataStart */
	pq_sendint64(&output_message, SendRqstPtr); /* walEnd */
	pq_sendint64(&output_message, 0);	/* sendtime, filled in last */

// ... (L3357-L3360 생략: 주석)
	enlargeStringInfo(&output_message, nbytes);

retry:
	/* attempt to read WAL from WAL buffers first */
	rbytes = WALReadFromBuffers(&output_message.data[output_message.len],
								startptr, nbytes, xlogreader->seg.ws_tli);
	output_message.len += rbytes;
	startptr += rbytes;
	nbytes -= rbytes;

	/* now read the remaining WAL from WAL file */
	if (nbytes > 0 &&
		!WALRead(xlogreader,
				 &output_message.data[output_message.len],
				 startptr,
				 nbytes,
				 xlogreader->seg.ws_tli,	/* Pass the current TLI because
											 * only WalSndSegmentOpen controls
											 * whether new TLI is needed. */
				 &errinfo))
		WALReadRaiseError(&errinfo);

// ... (L3383-L3409 생략: 읽은 세그먼트가 지워지지 않았는지 확인, cascade 면 다시 읽기)

	output_message.len += nbytes;
	output_message.data[output_message.len] = '\0';

	/*
	 * Fill the send timestamp last, so that it is taken as late as possible.
	 */
	resetStringInfo(&tmpbuf);
	pq_sendint64(&tmpbuf, GetCurrentTimestamp());
	memcpy(&output_message.data[1 + sizeof(int64) + sizeof(int64)],
		   tmpbuf.data, sizeof(int64));

	pq_putmessage_noblock('d', output_message.data, output_message.len);

	sentPtr = endptr;

	/* Update shared memory status */
	{
		WalSnd	   *walsnd = MyWalSnd;

		SpinLockAcquire(&walsnd->mutex);
		walsnd->sentPtr = sentPtr;
		SpinLockRelease(&walsnd->mutex);
	}
```

## 동작 흐름

```text
 L3154  streamingDoneSending 이면 CaughtUp, 끝
 L3161  SendRqstPtr 정하기
          지난 타임라인      sendTimeLineValidUpto            L3168
          cascade standby   GetStandbyFlushRecPtr            L3193  받아서 flush 한 끝 또는 replay 끝
          primary           GetFlushRecPtr                   L3244  fsync 한 끝
 L3271  LagTrackerWrite(SendRqstPtr, now)       나중에 'r' 이 이 위치를 넘으면 지연을 잰다
 L3287  지난 타임라인 끝까지 보냈으면 CopyDone ('c') 보내고 끝
 L3307  SendRqstPtr <= sentPtr 면 CaughtUp, 끝   보낼 게 없다
 L3324  startptr = sentPtr
 L3326  endptr = startptr + MAX_SEND_SIZE        XLOG_BLCKSZ * 16 = 8192 * 16 = 128KB
 L3329  SendRqstPtr <= endptr 면 endptr = SendRqstPtr, CaughtUp = true
 L3340  아니면 endptr 을 XLOG_BLCKSZ 경계로 내림, CaughtUp = false
 L3351  'w'
 L3353    dataStart = startptr
 L3354    walEnd    = SendRqstPtr                 standby 는 이걸로 primary 의 끝을 안다
 L3355    sendTime  = 0                           자리만 잡고 L3418 에서 채운다
 L3365  WALReadFromBuffers                        아직 WAL 버퍼에 있으면 메모리에서
 L3373  WALRead                                   나머지는 pg_wal 의 세그먼트 파일에서
 L3385  CheckXLogRemoved                          읽는 사이 세그먼트가 지워졌으면 ERROR
 L3418  sendTime 을 지금 시각으로 덮어쓴다
 L3422  pq_putmessage_noblock('d', ...)           출력 버퍼에만. 소켓 쓰기는 [05] L2882
 L3424  sentPtr = endptr
 L3431  MyWalSnd->sentPtr = sentPtr               pg_stat_replication.sent_lsn
```

보낼 끝이 **flush 한 곳**이라는 점이 primary 와 standby 사이의 순서를 정한다. 커밋 레코드가 primary 디스크에 닿기 전에는 standby 로 한 바이트도 가지 않는다.

```text
 primary 의 WAL 위치 셋 (왼쪽이 작다)

   sentPtr          GetFlushRecPtr        insert 끝
      |   보낼 수 있음   |   아직 못 보냄      |
 -----+-----------------+-------------------+------->  LSN
      0/3000F38         0/3100000           0/3104000
                        = SendRqstPtr

 XLogInsert 로 WAL 버퍼에만 있는 0/3100000 ~ 0/3104000 은
 누군가 fsync 할 때까지 보내지 않는다
 (커밋의 XLogFlush, WAL writer 의 XLogBackgroundFlush, 더러운 버퍼를 쓰기 전의 XLogFlush)
```

```text
 한 번에 보낼 양 계산 (XLOG_BLCKSZ 8192 = 0x2000, MAX_SEND_SIZE 0x20000)

 sentPtr = 0/3000F38, SendRqstPtr = 0/3100000

 L3326  endptr = 0x3000F38 + 0x20000 = 0x3020F38
 L3329  0x3100000 <= 0x3020F38 ? 아니다
 L3340  endptr -= 0x3020F38 % 0x2000 (= 0xF38)  -> 0x3020000
        nbytes = 0x3020000 - 0x3000F38 = 0x1F0C8 (127176 바이트)

 다음 호출: sentPtr = 0/3020000 부터 정확히 128KB 씩
          0/30E0000 다음 조각에서 endptr = 0x3100000 >= SendRqstPtr
          -> endptr = 0/3100000, CaughtUp = true

 SendRqstPtr 에서 끊는 경우만 페이지 중간에서 끝날 수 있다.
 그 위치는 레코드 중간이 아니라고 가정한다 (L3321-L3322 주석)
```

```text
 'w' 메시지 바이트 배치 (CopyData 'd' 안쪽)

 off  0     1 byte   'w'
 off  1     8 bytes  dataStart   이 조각의 첫 LSN
 off  9     8 bytes  walEnd      보낸 시점의 SendRqstPtr
 off 17     8 bytes  sendTime    L3419 의 memcpy 가 1 + 8 + 8 = 17 에 덮어쓴다
 off 25     nbytes   WAL 바이트 그대로 (디스크의 페이지 헤더 포함)
```

## 결과가 쓰이는 곳

```text
 출력 버퍼의 'w' 메시지
      --> [05] L2882 pq_flush_if_writable 이 소켓에 쓴다
      --> standby [07] XLogWalRcvProcessMsg 가 헤더를 읽고 [08] 이 바이트를 같은 LSN 자리에 쓴다

 WalSndCaughtUp
      --> [05] 가 STREAMING 으로 바꿀지, 잠들지 정한다

 MyWalSnd->sentPtr
      --> pg_stat_replication.sent_lsn

 lag_tracker 에 남긴 (SendRqstPtr, 시각)
      --> [11] 이 'r' 을 받을 때 write_lag, flush_lag, replay_lag 를 잰다
```

## 다루지 않는 것

`WALRead` 와 `WALReadFromBuffers` 의 내부, 세그먼트 파일 열기(`WalSndSegmentOpen`), cascade standby 의 타임라인 전환 감지(L3191-L3231), 지연 측정 링 버퍼(`LagTrackerWrite`)는 요약만 했다.
