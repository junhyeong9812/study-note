# ProcessStandbyReplyMessage

상위: [스트리밍 복제](../README.md)

**standby 가 보낸 `'r'` 메시지에서 write, flush, apply 세 위치를 꺼내 이 walsender 의 공유 메모리 칸(`WalSnd`)에 적는 함수다.** 그 다음 일이 둘이다. 이 서버가 primary 면 [12] `SyncRepReleaseWaiters` 를 불러 커밋을 기다리던 backend 를 깨우고, 슬롯을 쓰는 연결이면 슬롯의 `restart_lsn` 을 flush 위치로 맞춰(L2419 값이 다르기만 하면 덮어쓴다) 그 앞의 WAL 을 지워도 되게 한다.

## 위치

`replication` / `walsender.c` L2445-L2549 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2445-L2549))

## 실제 코드

[05] 의 `ProcessRepliesIfAny` 가 CopyData 를 읽으면 첫 바이트로 가른다.

`replication` / `walsender.c` L2381-L2406 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2381-L2406))

```c
// replication/walsender.c L2381-L2406
ProcessStandbyMessage(void)
{
	char		msgtype;

// ... (L2385-L2387 생략: 주석)
	msgtype = pq_getmsgbyte(&reply_message);

	switch (msgtype)
	{
		case 'r':
			ProcessStandbyReplyMessage();
			break;

		case 'h':
			ProcessStandbyHSFeedbackMessage();
			break;

		default:
			ereport(COMMERROR,
					(errcode(ERRCODE_PROTOCOL_VIOLATION),
					 errmsg("unexpected message type \"%c\"", msgtype)));
			proc_exit(0);
	}
}
```

`replication` / `walsender.c` L2445-L2549 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2445-L2549))

```c
// replication/walsender.c L2445-L2549
ProcessStandbyReplyMessage(void)
{
	XLogRecPtr	writePtr,
				flushPtr,
				applyPtr;
	bool		replyRequested;
	TimeOffset	writeLag,
				flushLag,
				applyLag;
	bool		clearLagTimes;
	TimestampTz now;
	TimestampTz replyTime;

	static XLogRecPtr prevWritePtr = InvalidXLogRecPtr;
	static XLogRecPtr prevFlushPtr = InvalidXLogRecPtr;
	static XLogRecPtr prevApplyPtr = InvalidXLogRecPtr;

	/* the caller already consumed the msgtype byte */
	writePtr = pq_getmsgint64(&reply_message);
	flushPtr = pq_getmsgint64(&reply_message);
	applyPtr = pq_getmsgint64(&reply_message);
	replyTime = pq_getmsgint64(&reply_message);
	replyRequested = pq_getmsgbyte(&reply_message);

// ... (L2469-L2484 생략: DEBUG2 로그)

	/* See if we can compute the round-trip lag for these positions. */
	now = GetCurrentTimestamp();
	writeLag = LagTrackerRead(SYNC_REP_WAIT_WRITE, writePtr, now);
	flushLag = LagTrackerRead(SYNC_REP_WAIT_FLUSH, flushPtr, now);
	applyLag = LagTrackerRead(SYNC_REP_WAIT_APPLY, applyPtr, now);

// ... (L2492-L2502 생략: 주석)
	clearLagTimes = (applyPtr == sentPtr && flushPtr == sentPtr &&
					 writePtr == prevWritePtr && flushPtr == prevFlushPtr &&
					 applyPtr == prevApplyPtr);

	prevWritePtr = writePtr;
	prevFlushPtr = flushPtr;
	prevApplyPtr = applyPtr;

	/* Send a reply if the standby requested one. */
	if (replyRequested)
		WalSndKeepalive(false, InvalidXLogRecPtr);

// ... (L2515-L2518 생략: 주석)
	{
		WalSnd	   *walsnd = MyWalSnd;

		SpinLockAcquire(&walsnd->mutex);
		walsnd->write = writePtr;
		walsnd->flush = flushPtr;
		walsnd->apply = applyPtr;
		if (writeLag != -1 || clearLagTimes)
			walsnd->writeLag = writeLag;
		if (flushLag != -1 || clearLagTimes)
			walsnd->flushLag = flushLag;
		if (applyLag != -1 || clearLagTimes)
			walsnd->applyLag = applyLag;
		walsnd->replyTime = replyTime;
		SpinLockRelease(&walsnd->mutex);
	}

	if (!am_cascading_walsender)
		SyncRepReleaseWaiters();

	/*
	 * Advance our local xmin horizon when the client confirmed a flush.
	 */
	if (MyReplicationSlot && flushPtr != InvalidXLogRecPtr)
	{
		if (SlotIsLogical(MyReplicationSlot))
			LogicalConfirmReceivedLocation(flushPtr);
		else
			PhysicalConfirmReceivedLocation(flushPtr);
	}
}
```

슬롯이 있으면 flush 위치가 슬롯의 `restart_lsn` 이 된다.

`replication` / `walsender.c` L2412-L2439 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walsender.c#L2412-L2439))

```c
// replication/walsender.c L2412-L2439
PhysicalConfirmReceivedLocation(XLogRecPtr lsn)
{
	bool		changed = false;
	ReplicationSlot *slot = MyReplicationSlot;

	Assert(lsn != InvalidXLogRecPtr);
	SpinLockAcquire(&slot->mutex);
	if (slot->data.restart_lsn != lsn)
	{
		changed = true;
		slot->data.restart_lsn = lsn;
	}
	SpinLockRelease(&slot->mutex);

	if (changed)
	{
		ReplicationSlotMarkDirty();
		ReplicationSlotsComputeRequiredLSN();
		PhysicalWakeupLogicalWalSnd();
	}

// ... (L2433-L2438 생략: 주석)
}
```

## 동작 흐름

```text
 L2463  writePtr  = int64                 standby LogstreamResult.Write
 L2464  flushPtr  = int64                 standby LogstreamResult.Flush
 L2465  applyPtr  = int64                 standby lastReplayedEndRecPtr
 L2466  replyTime = int64
 L2467  replyRequested = byte
 L2487  지연 계산
          LagTrackerRead(WRITE, writePtr)   [06] 이 남긴 (LSN, 시각) 중
          LagTrackerRead(FLUSH, flushPtr)   이 위치를 넘은 가장 최근 표본과의 시간 차
          LagTrackerRead(APPLY, applyPtr)
 L2503  apply, flush 가 sentPtr 에 닿았고 세 값이 지난번과 같으면 지연 값을 지운다
 L2512  replyRequested 면 keepalive 로 즉시 답
 L2522  MyWalSnd->mutex 아래
 L2523    write, flush, apply                pg_stat_replication 의 write_lsn, flush_lsn, replay_lsn
 L2526    writeLag, flushLag, applyLag       (-1 이면 이번엔 모름, 이전 값 유지)
 L2536  cascade walsender 가 아니면
 L2537    [12] SyncRepReleaseWaiters
 L2542  슬롯이 있고 flushPtr 가 유효하면
 L2547    PhysicalConfirmReceivedLocation(flushPtr)
            L2422 slot->data.restart_lsn = flushPtr
            L2429 ReplicationSlotsComputeRequiredLSN   체크포인트가 지울 수 있는 WAL 의 하한
```

```text
 'r' 메시지 바이트 배치 (standby XLogWalRcvSendReply L1210-L1215 와 짝)

 off  0   1 byte   'r'
 off  1   8 bytes  write     L2463
 off  9   8 bytes  flush     L2464
 off 17   8 bytes  apply     L2465
 off 25   8 bytes  sendTime  L2466
 off 33   1 byte   replyRequested  L2467
```

```text
 한 standby 의 보고가 시간에 따라 바뀌는 모습 (primary 의 sentPtr = 0/3050000 까지 보냄)

 write      flush      apply      standby 에서 일어난 일
 0/3050000  0/3000000  0/3000000  메시지 셋을 pwrite 한 뒤. write 만 앞선다
 0/3050000  0/3050000  0/3000000  fsync 뒤. flush 가 따라온다
 0/3050000  0/3050000  0/3048000  startup 이 적용한 뒤. apply 는 레코드 끝 단위로 오른다

 커밋 레코드 끝이 0/3048000 인 backend 가 기다린다면 ([12] 가 waitLSN <= 위치일 때 깨운다)
   remote_write 는 첫 줄에서, on (remote_flush) 은 둘째 줄에서, remote_apply 는 셋째 줄에서 풀린다
```

## 결과가 쓰이는 곳

```text
 MyWalSnd->write, flush, apply
      --> [12] SyncRepReleaseWaiters -> SyncRepGetCandidateStandbys 가 모든 동기 후보의 값을 모은다
      --> pg_stat_replication

 slot->data.restart_lsn
      --> ReplicationSlotsComputeRequiredLSN -> XLogSetReplicationSlotMinimumLSN (slot.c L1281)
          --> 체크포인트의 KeepLogSeg 가 이 값 앞 세그먼트만 지운다 (access/transam/xlog.c L8008)

 writeLag, flushLag, applyLag
      --> pg_stat_replication 의 write_lag, flush_lag, replay_lag
```

## 다루지 않는 것

지연 측정 링 버퍼(`LagTrackerRead`), 논리 슬롯의 `LogicalConfirmReceivedLocation`, 논리 walsender 깨우기(`PhysicalWakeupLogicalWalSnd`), hot standby feedback(`ProcessStandbyHSFeedbackMessage`)의 xmin 처리는 요약만 했다.
