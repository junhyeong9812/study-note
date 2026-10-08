# XLogWalRcvProcessMsg

상위: [스트리밍 복제](../README.md)

**walreceiver 가 받은 CopyData 하나를 첫 바이트로 가르는 함수다.** `'w'` 면 24바이트 헤더를 떼어 primary 의 끝 위치와 송신 시각을 공유 메모리에 적고, 나머지 WAL 바이트를 [08] `XLogWalRcvWrite` 에 넘긴다. `'k'` 면 같은 두 값만 적고, primary 가 답장을 원하면 즉시 [10] 으로 보고한다.

## 위치

`replication` / `walreceiver.c` L896-L961 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L896-L961))

## 실제 코드

`replication` / `walreceiver.c` L896-L961 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L896-L961))

```c
// replication/walreceiver.c L896-L961
XLogWalRcvProcessMsg(unsigned char type, char *buf, Size len, TimeLineID tli)
{
	int			hdrlen;
	XLogRecPtr	dataStart;
	XLogRecPtr	walEnd;
	TimestampTz sendTime;
	bool		replyRequested;

	switch (type)
	{
		case 'w':				/* WAL records */
			{
				StringInfoData incoming_message;

				hdrlen = sizeof(int64) + sizeof(int64) + sizeof(int64);
				if (len < hdrlen)
					ereport(ERROR,
							(errcode(ERRCODE_PROTOCOL_VIOLATION),
							 errmsg_internal("invalid WAL message received from primary")));

				/* initialize a StringInfo with the given buffer */
				initReadOnlyStringInfo(&incoming_message, buf, hdrlen);

				/* read the fields */
				dataStart = pq_getmsgint64(&incoming_message);
				walEnd = pq_getmsgint64(&incoming_message);
				sendTime = pq_getmsgint64(&incoming_message);
				ProcessWalSndrMessage(walEnd, sendTime);

				buf += hdrlen;
				len -= hdrlen;
				XLogWalRcvWrite(buf, len, dataStart, tli);
				break;
			}
		case 'k':				/* Keepalive */
			{
				StringInfoData incoming_message;

				hdrlen = sizeof(int64) + sizeof(int64) + sizeof(char);
				if (len != hdrlen)
					ereport(ERROR,
							(errcode(ERRCODE_PROTOCOL_VIOLATION),
							 errmsg_internal("invalid keepalive message received from primary")));

				/* initialize a StringInfo with the given buffer */
				initReadOnlyStringInfo(&incoming_message, buf, hdrlen);

				/* read the fields */
				walEnd = pq_getmsgint64(&incoming_message);
				sendTime = pq_getmsgint64(&incoming_message);
				replyRequested = pq_getmsgbyte(&incoming_message);

				ProcessWalSndrMessage(walEnd, sendTime);

				/* If the primary requested a reply, send one immediately */
				if (replyRequested)
					XLogWalRcvSendReply(true, false);
				break;
			}
		default:
			ereport(ERROR,
					(errcode(ERRCODE_PROTOCOL_VIOLATION),
					 errmsg_internal("invalid replication message type %d",
									 type)));
	}
}
```

헤더의 두 값은 공유 메모리에만 남는다. 데이터 흐름에는 영향이 없고 감시용이다.

`replication` / `walreceiver.c` L1334-L1346 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L1334-L1346))

```c
// replication/walreceiver.c L1334-L1346
ProcessWalSndrMessage(XLogRecPtr walEnd, TimestampTz sendTime)
{
	WalRcvData *walrcv = WalRcv;
	TimestampTz lastMsgReceiptTime = GetCurrentTimestamp();

	/* Update shared-memory status */
	SpinLockAcquire(&walrcv->mutex);
	if (walrcv->latestWalEnd < walEnd)
		walrcv->latestWalEndTime = sendTime;
	walrcv->latestWalEnd = walEnd;
	walrcv->lastMsgSendTime = sendTime;
	walrcv->lastMsgReceiptTime = lastMsgReceiptTime;
	SpinLockRelease(&walrcv->mutex);
```

## 동작 흐름

```text
 [02] L541  XLogWalRcvProcessMsg(buf[0], &buf[1], len - 1, startpointTLI)
                                 첫 바이트가 type, 나머지가 본문

 L906  'w'
 L910    hdrlen = 8 + 8 + 8 = 24
 L911    len < 24 면 ERROR (protocol violation)
 L920    dataStart  이 조각의 첫 LSN        --> XLogWalRcvWrite 의 recptr
 L921    walEnd     primary 의 SendRqstPtr
 L922    sendTime
 L923    ProcessWalSndrMessage(walEnd, sendTime)
           WalRcv->latestWalEnd, lastMsgSendTime, lastMsgReceiptTime
 L925    buf += 24, len -= 24
 L927    [08] XLogWalRcvWrite(buf, len, dataStart, tli)

 L930  'k'
 L934    hdrlen = 8 + 8 + 1 = 17, 정확히 17 이어야 한다
 L944    walEnd, sendTime, replyRequested
 L948    ProcessWalSndrMessage
 L951    replyRequested 면 [10] XLogWalRcvSendReply(true, false)   force 라 바뀐 게 없어도 보낸다

 그 밖   ERROR "invalid replication message type"
```

```text
 primary 가 보낸 바이트와 이 함수의 대응

 primary XLogSendPhysical            standby XLogWalRcvProcessMsg
 L3351 'w'                     -->   type = buf[0]                 (walreceiver.c L541)
 L3353 startptr                -->   dataStart  L920
 L3354 SendRqstPtr             -->   walEnd     L921
 L3418 GetCurrentTimestamp     -->   sendTime   L922
 WAL bytes (nbytes)            -->   buf, len   L925-L927

 primary WalSndKeepalive
 L4122 'k'                     -->   type
 L4123 sentPtr                 -->   walEnd     L944
 L4124 now                     -->   sendTime   L945
 L4125 requestReply            -->   replyRequested  L946
```

## 결과가 쓰이는 곳

```text
 WAL 바이트와 dataStart
      --> [08] XLogWalRcvWrite 가 같은 LSN 자리의 세그먼트 파일에 쓴다

 WalRcv->latestWalEnd, lastMsgSendTime, lastMsgReceiptTime
      --> pg_stat_wal_receiver 의 latest_end_lsn, last_msg_send_time, last_msg_receipt_time

 keepalive 의 replyRequested
      --> primary [05] 의 ping 에 대한 즉시 답장. primary 의 wal_sender_timeout 을 막는다
```

## 다루지 않는 것

`ProcessWalSndrMessage` 의 DEBUG2 로그(전송 지연과 적용 지연 계산, L1348-L1374)는 요약만 했다.
