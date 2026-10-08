# XLogWalRcvSendReply

상위: [스트리밍 복제](../README.md)

**standby 의 세 위치(write, flush, apply)를 `'r'` 메시지 하나에 담아 primary 로 보내는 함수다.** write 와 flush 는 walreceiver 자신이 아는 값이고, apply 는 startup 이 공유 메모리에 남긴 마지막 replay 위치다. 바뀐 게 없으면 `wal_receiver_status_interval`(기본 10초)마다만 보낸다. primary 의 동기 복제는 이 세 값 가운데 하나를 기다린다.

## 위치

`replication` / `walreceiver.c` L1169-L1225 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L1169-L1225))

## 실제 코드

`replication` / `walreceiver.c` L1169-L1225 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L1169-L1225))

```c
// replication/walreceiver.c L1169-L1225
XLogWalRcvSendReply(bool force, bool requestReply)
{
	static XLogRecPtr writePtr = 0;
	static XLogRecPtr flushPtr = 0;
	XLogRecPtr	applyPtr;
	TimestampTz now;

// ... (L1176-L1179 생략: 주석)
	if (!force && wal_receiver_status_interval <= 0)
		return;

	/* Get current timestamp. */
	now = GetCurrentTimestamp();

// ... (L1186-L1194 생략: 주석)
	if (!force
		&& writePtr == LogstreamResult.Write
		&& flushPtr == LogstreamResult.Flush
		&& now < wakeup[WALRCV_WAKEUP_REPLY])
		return;

	/* Make sure we wake up when it's time to send another reply. */
	WalRcvComputeNextWakeup(WALRCV_WAKEUP_REPLY, now);

	/* Construct a new message */
	writePtr = LogstreamResult.Write;
	flushPtr = LogstreamResult.Flush;
	applyPtr = GetXLogReplayRecPtr(NULL);

	resetStringInfo(&reply_message);
	pq_sendbyte(&reply_message, 'r');
	pq_sendint64(&reply_message, writePtr);
	pq_sendint64(&reply_message, flushPtr);
	pq_sendint64(&reply_message, applyPtr);
	pq_sendint64(&reply_message, GetCurrentTimestamp());
	pq_sendbyte(&reply_message, requestReply ? 1 : 0);

	/* Send it */
	elog(DEBUG2, "sending write %X/%X flush %X/%X apply %X/%X%s",
		 LSN_FORMAT_ARGS(writePtr),
		 LSN_FORMAT_ARGS(flushPtr),
		 LSN_FORMAT_ARGS(applyPtr),
		 requestReply ? " (reply requested)" : "");

	walrcv_send(wrconn, reply_message.data, reply_message.len);
}
```

apply 위치는 startup 이 레코드마다 올리는 값을 읽어 온다.

`access/transam` / `xlogrecovery.c` L4592-L4605 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L4592-L4605))

```c
// access/transam/xlogrecovery.c L4592-L4605
GetXLogReplayRecPtr(TimeLineID *replayTLI)
{
	XLogRecPtr	recptr;
	TimeLineID	tli;

	SpinLockAcquire(&XLogRecoveryCtl->info_lck);
	recptr = XLogRecoveryCtl->lastReplayedEndRecPtr;
	tli = XLogRecoveryCtl->lastReplayedTLI;
	SpinLockRelease(&XLogRecoveryCtl->info_lck);

	if (replayTLI)
		*replayTLI = tli;
	return recptr;
}
```

`remote_apply` 로 커밋한 트랜잭션은 커밋 레코드에 "적용하면 바로 알려 달라"는 비트를 단다.

`access/transam` / `xact.c` L5855-L5860 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L5855-L5860))

```c
// access/transam/xact.c L5855-L5860
	/*
	 * Check if the caller would like to ask standbys for immediate feedback
	 * once this commit is applied.
	 */
	if (synchronous_commit >= SYNCHRONOUS_COMMIT_REMOTE_APPLY)
		xl_xinfo.xinfo |= XACT_COMPLETION_APPLY_FEEDBACK;
```

standby 의 startup 이 그 커밋 레코드를 적용하면 walreceiver 를 깨운다.

`access/transam` / `xact.c` L6265-L6271 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L6265-L6271))

```c
// access/transam/xact.c L6265-L6271
	/*
	 * If asked by the primary (because someone is waiting for a synchronous
	 * commit = remote_apply), we will need to ask walreceiver to send a reply
	 * immediately.
	 */
	if (XactCompletionApplyFeedback(parsed->xinfo))
		XLogRequestWalReceiverReply();
```

`access/transam` / `xlogrecovery.c` L2068-L2077 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L2068-L2077))

```c
// access/transam/xlogrecovery.c L2068-L2077
	/*
	 * If rm_redo called XLogRequestWalReceiverReply, then we wake up the
	 * receiver so that it notices the updated lastReplayedEndRecPtr and sends
	 * a reply to the primary.
	 */
	if (doRequestWalReceiverReply)
	{
		doRequestWalReceiverReply = false;
		WalRcvForceReply();
	}
```

`replication` / `walreceiver.c` L1427-L1438 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L1427-L1438))

```c
// replication/walreceiver.c L1427-L1438
WalRcvForceReply(void)
{
	ProcNumber	procno;

	WalRcv->force_reply = true;
	/* fetching the proc number is probably atomic, but don't rely on it */
	SpinLockAcquire(&WalRcv->mutex);
	procno = WalRcv->procno;
	SpinLockRelease(&WalRcv->mutex);
	if (procno != INVALID_PROC_NUMBER)
		SetLatch(&GetPGProcByNumber(procno)->procLatch);
}
```

## 동작 흐름

```text
 L1180  force 가 아니고 status_interval <= 0 이면 아무것도 안 한다
 L1195  force 가 아니고 write, flush 가 지난번과 같고 아직 10초 전이면 안 보낸다
          apply 만 바뀐 경우는 여기서 걸러진다 (spinlock 을 아끼려고, L1186-L1194 주석)
 L1202  다음 REPLY 기상 시각 = now + wal_receiver_status_interval
 L1205  writePtr = LogstreamResult.Write
 L1206  flushPtr = LogstreamResult.Flush
 L1207  applyPtr = GetXLogReplayRecPtr         startup 의 lastReplayedEndRecPtr
 L1210  'r' write flush apply now requestReply
 L1224  walrcv_send                            CopyData 로 primary 에
```

부르는 자리는 여섯이다. 그중 apply 를 빨리 알리는 길은 startup 이 latch 로 walreceiver 를 깨우는 길 하나뿐이다.

```text
 caller       force    requestReply   언제
 [02] L484    true     false          스트리밍 시작, 첫 보고
 [02] L560    false    false          메시지를 받은 뒤. write 가 올랐으면 보낸다
 [09] L1102   false    false          fsync 뒤. flush 가 올랐으면 보낸다
 [02] L616    true     false          startup 이 force_reply 로 깨웠을 때 (apply 보고)
 [02] L662    ping     ping           timeout 기상. 10초 주기 또는 ping (wal_receiver_timeout 의 절반)
 [07] L952    true     false          primary keepalive 가 답장을 요청했을 때
```

```text
 remote_apply 커밋의 apply 보고가 빨리 가는 길

 primary backend
   XactLogCommitRecord  L5859 synchronous_commit >= REMOTE_APPLY
                              xinfo |= XACT_COMPLETION_APPLY_FEEDBACK
        |  ... 스트리밍 ...
        v
 standby startup
   ApplyWalRecord -> xact_redo -> xact_redo_commit
     xact.c L6270  비트가 있으면 XLogRequestWalReceiverReply   doRequestWalReceiverReply = true
   xlogrecovery.c L2039  lastReplayedEndRecPtr = 커밋 레코드 끝
   xlogrecovery.c L2073  doRequestWalReceiverReply 면 WalRcvForceReply
     walreceiver.c L1431  WalRcv->force_reply = true, walreceiver latch 를 깨움
        |
        v
 standby walreceiver
   [02] L601  WL_LATCH_SET
   [02] L606  force_reply -> XLogWalRcvSendReply(true, false)
   L1207      applyPtr = 방금 적용한 커밋 레코드 끝
        |
        v
 primary walsender  [11] ProcessStandbyReplyMessage -> [12] SyncRepReleaseWaiters
```

## 결과가 쓰이는 곳

```text
 'r' 메시지
      --> primary [11] ProcessStandbyReplyMessage 가 MyWalSnd->write/flush/apply 에 적는다
      --> [12] SyncRepReleaseWaiters 가 동기 복제 대기자를 깨운다
      --> pg_stat_replication 의 write_lsn, flush_lsn, replay_lsn 과 *_lag

 requestReply = true 인 'r'
      --> primary 가 즉시 keepalive 로 답한다 (walsender.c L2512-L2513)
```

## 다루지 않는 것

hot standby feedback 메시지(`'h'`, `XLogWalRcvSendHSFeedback`), `wal_receiver_status_interval = 0` 일 때의 동작 세부, `GetXLogReplayRecPtr` 와 `lastReplayedEndRecPtr` 를 올리는 redo 루프는 [WAL redo](../../wal-redo/README.md) 몫이라 요약만 했다.
