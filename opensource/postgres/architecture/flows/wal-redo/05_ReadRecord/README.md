# ReadRecord

상위: [WAL redo (복구)](../README.md)

**다음 WAL 레코드 하나를 읽어 돌려주고, 못 읽으면 지금 모드에 맞게 다음 행동을 고르는 함수다.** 레코드 디코딩과 CRC 검사는 `XLogPrefetcherReadRecord` 아래의 xlogreader 가 하고, 페이지가 없을 때 파일을 구해 오는 일은 page_read 콜백 `XLogPageRead` 가 한다. 이 함수의 몫은 실패 뒤의 판단이다. 크래시 복구면 NULL 을 돌려줘 루프를 끝내고, 아카이브 복구가 요청된 채 아직 크래시 복구 단계였으면 아카이브 복구로 갈아타 다시 시도하고, standby 면 promote 요청이 올 때까지 계속 다시 시도한다.

## 위치

`src/backend/access/transam` / `xlogrecovery.c` L3161-L3298 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogrecovery.c#L3161-L3298))

## 실제 코드

```c
// transam/xlogrecovery.c L3161-L3298
static XLogRecord *
ReadRecord(XLogPrefetcher *xlogprefetcher, int emode,
		   bool fetching_ckpt, TimeLineID replayTLI)
{
	XLogRecord *record;
	XLogReaderState *xlogreader = XLogPrefetcherGetReader(xlogprefetcher);
	XLogPageReadPrivate *private = (XLogPageReadPrivate *) xlogreader->private_data;

	/* Pass through parameters to XLogPageRead */
	private->fetching_ckpt = fetching_ckpt;
	private->emode = emode;
	private->randAccess = (xlogreader->ReadRecPtr == InvalidXLogRecPtr);
	private->replayTLI = replayTLI;

	/* This is the first attempt to read this page. */
	lastSourceFailed = false;

	for (;;)
	{
		char	   *errormsg;

		record = XLogPrefetcherReadRecord(xlogprefetcher, &errormsg);
		if (record == NULL)
		{
			/*
			 * When we find that WAL ends in an incomplete record, keep track
			 * of that record.  After recovery is done, we'll write a record
			 * to indicate to downstream WAL readers that that portion is to
			 * be ignored.
			 *
			 * However, when ArchiveRecoveryRequested = true, we're going to
			 * switch to a new timeline at the end of recovery. We will only
			 * copy WAL over to the new timeline up to the end of the last
			 * complete record, so if we did this, we would later create an
			 * overwrite contrecord in the wrong place, breaking everything.
			 */
			if (!ArchiveRecoveryRequested &&
				!XLogRecPtrIsInvalid(xlogreader->abortedRecPtr))
			{
				abortedRecPtr = xlogreader->abortedRecPtr;
				missingContrecPtr = xlogreader->missingContrecPtr;
			}

			if (readFile >= 0)
			{
				close(readFile);
				readFile = -1;
			}

			/*
			 * We only end up here without a message when XLogPageRead()
			 * failed - in that case we already logged something. In
			 * StandbyMode that only happens if we have been triggered, so we
			 * shouldn't loop anymore in that case.
			 */
			if (errormsg)
				ereport(emode_for_corrupt_record(emode, xlogreader->EndRecPtr),
						(errmsg_internal("%s", errormsg) /* already translated */ ));
		}

		/*
		 * Check page TLI is one of the expected values.
		 */
		else if (!tliInHistory(xlogreader->latestPageTLI, expectedTLEs))
		{
			char		fname[MAXFNAMELEN];
			XLogSegNo	segno;
			int32		offset;

			XLByteToSeg(xlogreader->latestPagePtr, segno, wal_segment_size);
			offset = XLogSegmentOffset(xlogreader->latestPagePtr,
									   wal_segment_size);
			XLogFileName(fname, xlogreader->seg.ws_tli, segno,
						 wal_segment_size);
			ereport(emode_for_corrupt_record(emode, xlogreader->EndRecPtr),
					(errmsg("unexpected timeline ID %u in WAL segment %s, LSN %X/%X, offset %u",
							xlogreader->latestPageTLI,
							fname,
							LSN_FORMAT_ARGS(xlogreader->latestPagePtr),
							offset)));
			record = NULL;
		}

		if (record)
		{
			/* Great, got a record */
			return record;
		}
		else
		{
			/* No valid record available from this source */
			lastSourceFailed = true;

			/*
			 * If archive recovery was requested, but we were still doing
			 * crash recovery, switch to archive recovery and retry using the
			 * offline archive. We have now replayed all the valid WAL in
			 * pg_wal, so we are presumably now consistent.
			 *
			 * We require that there's at least some valid WAL present in
			 * pg_wal, however (!fetching_ckpt).  We could recover using the
			 * WAL from the archive, even if pg_wal is completely empty, but
			 * we'd have no idea how far we'd have to replay to reach
			 * consistency.  So err on the safe side and give up.
			 */
			if (!InArchiveRecovery && ArchiveRecoveryRequested &&
				!fetching_ckpt)
			{
				ereport(DEBUG1,
						(errmsg_internal("reached end of WAL in pg_wal, entering archive recovery")));
				InArchiveRecovery = true;
				if (StandbyModeRequested)
					EnableStandbyMode();

				SwitchIntoArchiveRecovery(xlogreader->EndRecPtr, replayTLI);
				minRecoveryPoint = xlogreader->EndRecPtr;
				minRecoveryPointTLI = replayTLI;

				CheckRecoveryConsistency();

				/*
				 * Before we retry, reset lastSourceFailed and currentSource
				 * so that we will check the archive next.
				 */
				lastSourceFailed = false;
				currentSource = XLOG_FROM_ANY;

				continue;
			}

			/* In standby mode, loop back to retry. Otherwise, give up. */
			if (StandbyMode && !CheckForStandbyTrigger())
				continue;
			else
				return NULL;
		}
	}
}
```

## 동작 흐름

```text
 ReadRecord(xlogprefetcher, emode, fetching_ckpt, replayTLI)

 L3170-L3173  XLogPageRead 에 넘길 값 (emode, randAccess, replayTLI)
 L3176  lastSourceFailed = false
 L3178  for (;;)
 L3182    record = XLogPrefetcherReadRecord
            -> XLogReadRecord -> 페이지가 필요하면 XLogPageRead
               -> 열린 파일이 없으면 [10] WaitForWALToBecomeAvailable
 L3183    NULL 이면
 L3197      크래시 복구에서 끝이 잘린 레코드면 abortedRecPtr, missingContrecPtr 기억
 L3216      errormsg 가 있으면 emode_for_corrupt_record 로 보고
 L3224    레코드는 있는데 페이지 TLI 가 기대 이력에 없으면 NULL 취급
 L3244    레코드면 return
 L3252    lastSourceFailed = true                 다음 XLogPageRead 가 소스를 바꾼다
 L3266    아카이브 복구 요청됨 && 아직 크래시 복구 && 체크포인트 읽기 중이 아님
            InArchiveRecovery = true, SwitchIntoArchiveRecovery, minRecoveryPoint = 지금 끝
            continue                               아카이브에서 이어서
 L3292    StandbyMode && promote 요청 없음 -> continue
 L3295    그 밖 -> return NULL                    WAL 의 끝
```

같은 "다음 레코드 없음"이 세 모드에서 다르게 끝난다.

```text
 mode                              L3266   L3292   결과
 crash recovery                    no      no      NULL -> PerformWalRecovery 루프 끝
 archive, first pass over pg_wal   yes     -       pg_wal 을 다 읽은 직후. 아카이브 복구로 전환해 restore_command 로 계속
 archive recovery                  no      no      아카이브에도 없으면 NULL -> 복구 끝
 standby                           no      yes     다시 시도 (WaitForWALToBecomeAvailable 가 기다린다)
 standby + promote                 no      no      NULL -> 복구 끝, promote
```

크래시 복구에서 WAL 의 끝은 "더 읽을 수 없는 첫 자리"다. 마지막 세그먼트의 남은 부분은 재활용된 옛 내용이거나 0 이므로, 헤더 검증이나 CRC 에서 걸린다.

```text
 seg 5B (16MB)

 0/5B000000                0/5B012340                                 0/5BFFFFFF
 |  유효한 레코드들 ...     |  옛 세그먼트 내용 또는 0 ...               |
                            R_next 를 읽으려 함
                              xl_tot_len 이 헤더보다 작거나 xl_prev 가 직전 레코드가 아님
                              또는 CRC 불일치 (xlogreader.c L1142-L1220) -> XLogReadRecord 가 NULL + errormsg
                            ReadRecord 는 emode = LOG 로 보고하고 NULL

 끝 레코드가 페이지 경계를 넘다 잘렸으면 (contrecord 일부만 기록됨)
   abortedRecPtr = 그 레코드 시작, missingContrecPtr = 잘린 자리   (L3200-L3201)
   기동 뒤 XLOG_OVERWRITE_CONTRECORD 를 먼저 써서 뒤쪽 읽는 쪽에 알린다 (xlog.c L6153-L6157)
```

## 결과가 쓰이는 곳

```text
 XLogRecord *
      --> [04] PerformWalRecovery 가 [06] ApplyWalRecord 에 넘긴다
 NULL
      --> [04] 의 루프 종료
 lastSourceFailed = true
      --> 다음 XLogPageRead 호출의 [10] WaitForWALToBecomeAvailable 가 다음 소스로 넘어간다 (L3641)
 InArchiveRecovery 전환
      --> SwitchIntoArchiveRecovery 가 pg_control 을 DB_IN_ARCHIVE_RECOVERY 로 (xlog.c L6249)
```

## 다루지 않는 것

`XLogReadRecord` 의 레코드 조립과 검증(`ValidXLogRecordHeader`, `ValidXLogRecord`), WAL prefetch, `XLogPageRead` 의 세그먼트 전환과 페이지 헤더 검사, `emode_for_corrupt_record` 의 반복 로그 억제는 요약만 했다.
