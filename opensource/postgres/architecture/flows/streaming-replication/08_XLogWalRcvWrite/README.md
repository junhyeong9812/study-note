# XLogWalRcvWrite

상위: [스트리밍 복제](../README.md)

**받은 WAL 바이트를 standby 의 `pg_wal` 세그먼트 파일에, primary 와 같은 LSN 자리에 `pwrite` 하는 함수다.** 여기서는 fsync 하지 않는다. 그래서 이 함수가 올리는 것은 **write 위치**(`LogstreamResult.Write`) 하나다. 조각이 세그먼트 경계를 넘으면 앞 세그먼트를 닫고(닫기 전에 fsync) 다음 세그먼트를 연다.

## 위치

`replication` / `walreceiver.c` L967-L1053 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L967-L1053))

## 실제 코드

`replication` / `walreceiver.c` L967-L1053 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L967-L1053))

```c
// replication/walreceiver.c L967-L1053
XLogWalRcvWrite(char *buf, Size nbytes, XLogRecPtr recptr, TimeLineID tli)
{
	int			startoff;
	int			byteswritten;
	instr_time	start;

	Assert(tli != 0);

	while (nbytes > 0)
	{
		int			segbytes;

		/* Close the current segment if it's completed */
		if (recvFile >= 0 && !XLByteInSeg(recptr, recvSegNo, wal_segment_size))
			XLogWalRcvClose(recptr, tli);

		if (recvFile < 0)
		{
			/* Create/use new log file */
			XLByteToSeg(recptr, recvSegNo, wal_segment_size);
			recvFile = XLogFileInit(recvSegNo, tli);
			recvFileTLI = tli;
		}

		/* Calculate the start offset of the received logs */
		startoff = XLogSegmentOffset(recptr, wal_segment_size);

		if (startoff + nbytes > wal_segment_size)
			segbytes = wal_segment_size - startoff;
		else
			segbytes = nbytes;

		/* OK to write the logs */
		errno = 0;

// ... (L1002-L1004 생략: 주석)
		start = pgstat_prepare_io_time(track_wal_io_timing);

		pgstat_report_wait_start(WAIT_EVENT_WAL_WRITE);
		byteswritten = pg_pwrite(recvFile, buf, segbytes, (off_t) startoff);
		pgstat_report_wait_end();

// ... (L1011-L1028 생략: 쓰기 실패면 PANIC)

		pgstat_count_io_op_time(IOOBJECT_WAL, IOCONTEXT_NORMAL,
								IOOP_WRITE, start, 1, byteswritten);

		/* Update state for write */
		recptr += byteswritten;

		nbytes -= byteswritten;
		buf += byteswritten;

		LogstreamResult.Write = recptr;
	}

	/* Update shared-memory status */
	pg_atomic_write_u64(&WalRcv->writtenUpto, LogstreamResult.Write);

// ... (L1045-L1050 생략: 주석)
	if (recvFile >= 0 && !XLByteInSeg(recptr, recvSegNo, wal_segment_size))
		XLogWalRcvClose(recptr, tli);
}
```

세그먼트를 닫는 함수다. 닫기 전에 [09] 로 fsync 하므로, 세그먼트가 바뀌는 순간에는 이 함수 안에서도 flush 위치가 오른다.

`replication` / `walreceiver.c` L1117-L1153 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/replication/walreceiver.c#L1117-L1153))

```c
// replication/walreceiver.c L1117-L1153
XLogWalRcvClose(XLogRecPtr recptr, TimeLineID tli)
{
	char		xlogfname[MAXFNAMELEN];

	Assert(recvFile >= 0 && !XLByteInSeg(recptr, recvSegNo, wal_segment_size));
	Assert(tli != 0);

// ... (L1124-L1127 생략: 주석)
	XLogWalRcvFlush(false, tli);

	XLogFileName(xlogfname, recvFileTLI, recvSegNo, wal_segment_size);

// ... (L1132-L1136 생략: 주석)
	if (close(recvFile) != 0)
		ereport(PANIC,
				(errcode_for_file_access(),
				 errmsg("could not close WAL segment %s: %m",
						xlogfname)));

	/*
	 * Create .done file forcibly to prevent the streamed segment from being
	 * archived later.
	 */
	if (XLogArchiveMode != ARCHIVE_MODE_ALWAYS)
		XLogArchiveForceDone(xlogfname);
	else
		XLogArchiveNotify(xlogfname);

	recvFile = -1;
}
```

## 동작 흐름

```text
 L975  while (nbytes > 0)
 L980    열린 파일이 있는데 recptr 이 그 세그먼트 밖이면
           XLogWalRcvClose                    fsync, close, .done 표시
 L983    열린 파일이 없으면
 L986      recvSegNo = recptr / wal_segment_size
 L987      XLogFileInit(recvSegNo, tli)        없으면 만들고 있으면 연다
 L992    startoff = recptr % wal_segment_size
 L994    이 세그먼트에 들어가는 만큼만 segbytes
 L1008   pg_pwrite(recvFile, buf, segbytes, startoff)
 L1011   실패면 PANIC                         (errno 가 없으면 ENOSPC 로 본다)
 L1034   recptr += 쓴 만큼
 L1039   LogstreamResult.Write = recptr
 L1043 WalRcv->writtenUpto = Write             pg_stat_wal_receiver.written_lsn
 L1051 이번 조각으로 세그먼트를 꽉 채웠으면 바로 닫는다   다음 조각을 기다리지 않고 아카이브 표시
```

```text
 세그먼트 경계를 넘는 조각 하나 (wal_segment_size 16MB = 0x1000000)

 dataStart = 0/3FF0000, nbytes = 0x20000 (128KB)

 1 바퀴  recvSegNo = 3, startoff = 0xFF0000
         0xFF0000 + 0x20000 > 0x1000000 -> segbytes = 0x10000
         pwrite(000000010000000000000003, 64KB, off 0xFF0000)
         recptr = 0/4000000,  Write = 0/4000000
 2 바퀴  L980 0/4000000 은 3 번 세그먼트 밖 -> XLogWalRcvClose
           [09] XLogWalRcvFlush -> fsync, Flush = 0/4000000, startup 깨움, 보고
         XLogFileInit(4) -> 000000010000000000000004
         pwrite(..., 64KB, off 0) -> recptr = 0/4010000, Write = 0/4010000
 L1051   0/4010000 은 4 번 세그먼트 안 -> 닫지 않는다

 파일 이름의 타임라인은 1 이라고 놓았다
```

```text
 standby 쪽 위치 셋과 이 함수의 자리

 LogstreamResult.Write   이 함수가 올린다       pwrite 까지       ('r' 의 write)
 LogstreamResult.Flush   [09] 가 올린다         fsync 까지        ('r' 의 flush)
 lastReplayedEndRecPtr   startup 이 올린다      redo 까지         ('r' 의 apply)

 Flush <= Write 는 스트리밍을 (다시) 시작한 직후만 빼면 성립한다 ([09] 가 Flush = Write 로만 올린다)
   예외: [02] L475 가 시작할 때 Write = Flush = replay 끝 (예 0/3800000) 으로 놓는데
   받기는 세그먼트 머리 (0/3000000) 부터 다시 하므로, 첫 조각 뒤 Write = 0/3020000 < Flush.
   Write 가 Flush 를 넘을 때까지 [09] 는 fsync 를 건너뛴다 (L1066 Flush < Write 검사)
 스트리밍으로 읽는 동안 startup 은 WalRcv->flushedUpto 아래까지만 읽는다 (xlogrecovery.c L3939-L3940)
```

## 결과가 쓰이는 곳

```text
 LogstreamResult.Write
      --> [09] XLogWalRcvFlush 가 Flush < Write 일 때만 fsync 한다
      --> [10] XLogWalRcvSendReply 가 write 위치로 보고한다
          동기 복제 remote_write 가 이 값을 기다린다

 WalRcv->writtenUpto
      --> pg_stat_wal_receiver.written_lsn

 닫힌 세그먼트의 .done (archive_mode 가 always 가 아니면)
      --> 스트리밍으로 받은 세그먼트를 standby 가 나중에 아카이브하지 않게 한다 (L1143-L1146 주석)
```

## 다루지 않는 것

`XLogFileInit` 의 세그먼트 생성과 재활용, I/O 통계(`pgstat_count_io_op_time`), 아카이브 표시 파일(`XLogArchiveForceDone`, `XLogArchiveNotify`)의 내부는 요약만 했다.
