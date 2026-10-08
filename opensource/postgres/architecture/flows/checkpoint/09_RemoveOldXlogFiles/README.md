# RemoveOldXlogFiles

상위: [체크포인트](../README.md)

**체크포인트가 끝난 뒤 `pg_wal` 디렉터리를 훑어, 경계 세그먼트 이하의 WAL 파일을 미래 세그먼트 이름으로 바꿔 재활용하거나 지우는 함수다.** 경계는 호출자 `CreateCheckPoint` 가 정한다. REDO 지점이 든 세그먼트에서 시작해 `KeepLogSeg` 가 복제 슬롯, `wal_keep_size`, WAL summarizer 가 아직 필요로 하는 만큼 뒤로 당기고, 마지막에 하나를 뺀다. 아카이빙 중이면 아직 아카이브되지 않은 파일은 남긴다. 재활용할지 지울지는 `XLOGfileslop` 이 `min_wal_size`, `max_wal_size`, 체크포인트 간 거리 추정치로 정한 상한까지 빈 이름이 있는가로 갈린다.

## 위치

`src/backend/access/transam` / `xlog.c` L3860-L3917 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L3860-L3917))

## 실제 코드

```c
// transam/xlog.c L3860-L3917
static void
RemoveOldXlogFiles(XLogSegNo segno, XLogRecPtr lastredoptr, XLogRecPtr endptr,
				   TimeLineID insertTLI)
{
	DIR		   *xldir;
	struct dirent *xlde;
	char		lastoff[MAXFNAMELEN];
	XLogSegNo	endlogSegNo;
	XLogSegNo	recycleSegNo;

	/* Initialize info about where to try to recycle to */
	XLByteToSeg(endptr, endlogSegNo, wal_segment_size);
	recycleSegNo = XLOGfileslop(lastredoptr);

	/*
	 * Construct a filename of the last segment to be kept. The timeline ID
	 * doesn't matter, we ignore that in the comparison. (During recovery,
	 * InsertTimeLineID isn't set, so we can't use that.)
	 */
	XLogFileName(lastoff, 0, segno, wal_segment_size);

	elog(DEBUG2, "attempting to remove WAL segments older than log file %s",
		 lastoff);

	xldir = AllocateDir(XLOGDIR);

	while ((xlde = ReadDir(xldir, XLOGDIR)) != NULL)
	{
		/* Ignore files that are not XLOG segments */
		if (!IsXLogFileName(xlde->d_name) &&
			!IsPartialXLogFileName(xlde->d_name))
			continue;

		/*
		 * We ignore the timeline part of the XLOG segment identifiers in
		 * deciding whether a segment is still needed.  This ensures that we
		 * won't prematurely remove a segment from a parent timeline. We could
		 * probably be a little more proactive about removing segments of
		 * non-parent timelines, but that would be a whole lot more
		 * complicated.
		 *
		 * We use the alphanumeric sorting property of the filenames to decide
		 * which ones are earlier than the lastoff segment.
		 */
		if (strcmp(xlde->d_name + 8, lastoff + 8) <= 0)
		{
			if (XLogArchiveCheckDone(xlde->d_name))
			{
				/* Update the last removed location in shared memory first */
				UpdateLastRemovedPtr(xlde->d_name);

				RemoveXlogFile(xlde, recycleSegNo, &endlogSegNo, insertTLI);
			}
		}
	}

	FreeDir(xldir);
}
```

경계를 정하는 호출자 쪽 줄이다(`CreateCheckPoint`).

`src/backend/access/transam` / `xlog.c` L7355-L7374 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L7355-L7374))

```c
// transam/xlog.c L7355-L7374
	/*
	 * Delete old log files, those no longer needed for last checkpoint to
	 * prevent the disk holding the xlog from growing full.
	 */
	XLByteToSeg(RedoRecPtr, _logSegNo, wal_segment_size);
	KeepLogSeg(recptr, &_logSegNo);
	if (InvalidateObsoleteReplicationSlots(RS_INVAL_WAL_REMOVED | RS_INVAL_IDLE_TIMEOUT,
										   _logSegNo, InvalidOid,
										   InvalidTransactionId))
	{
		/*
		 * Some slots have been invalidated; recalculate the old-segment
		 * horizon, starting again from RedoRecPtr.
		 */
		XLByteToSeg(RedoRecPtr, _logSegNo, wal_segment_size);
		KeepLogSeg(recptr, &_logSegNo);
	}
	_logSegNo--;
	RemoveOldXlogFiles(_logSegNo, RedoRecPtr, recptr,
					   checkPoint.ThisTimeLineID);
```

`KeepLogSeg` 는 경계를 뒤로만 당긴다. 복제 슬롯은 `max_slot_wal_keep_size` 로 상한을 받는다.

`src/backend/access/transam` / `xlog.c` L7997-L8064 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L7997-L8064))

```c
// transam/xlog.c L7997-L8064
static void
KeepLogSeg(XLogRecPtr recptr, XLogSegNo *logSegNo)
{
	XLogSegNo	currSegNo;
	XLogSegNo	segno;
	XLogRecPtr	keep;

	XLByteToSeg(recptr, currSegNo, wal_segment_size);
	segno = currSegNo;

	/* Calculate how many segments are kept by slots. */
	keep = XLogGetReplicationSlotMinimumLSN();
	if (keep != InvalidXLogRecPtr && keep < recptr)
	{
		XLByteToSeg(keep, segno, wal_segment_size);

		/*
		 * Account for max_slot_wal_keep_size to avoid keeping more than
		 * configured.  However, don't do that during a binary upgrade: if
		 * slots were to be invalidated because of this, it would not be
		 * possible to preserve logical ones during the upgrade.
		 */
		if (max_slot_wal_keep_size_mb >= 0 && !IsBinaryUpgrade)
		{
			uint64		slot_keep_segs;

			slot_keep_segs =
				ConvertToXSegs(max_slot_wal_keep_size_mb, wal_segment_size);

			if (currSegNo - segno > slot_keep_segs)
				segno = currSegNo - slot_keep_segs;
		}
	}

	/*
	 * If WAL summarization is in use, don't remove WAL that has yet to be
	 * summarized.
	 */
	keep = GetOldestUnsummarizedLSN(NULL, NULL);
	if (keep != InvalidXLogRecPtr)
	{
		XLogSegNo	unsummarized_segno;

		XLByteToSeg(keep, unsummarized_segno, wal_segment_size);
		if (unsummarized_segno < segno)
			segno = unsummarized_segno;
	}

	/* but, keep at least wal_keep_size if that's set */
	if (wal_keep_size_mb > 0)
	{
		uint64		keep_segs;

		keep_segs = ConvertToXSegs(wal_keep_size_mb, wal_segment_size);
		if (currSegNo - segno < keep_segs)
		{
			/* avoid underflow, don't go below 1 */
			if (currSegNo <= keep_segs)
				segno = 1;
			else
				segno = currSegNo - keep_segs;
		}
	}

	/* don't delete WAL segments newer than the calculated segment */
	if (segno < *logSegNo)
		*logSegNo = segno;
}
```

파일 하나의 운명은 `RemoveXlogFile` 이 정한다. 재활용은 `InstallXLogFileSegment` 로 이름만 바꾼다.

`src/backend/access/transam` / `xlog.c` L4004-L4079 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L4004-L4079))

```c
// transam/xlog.c L4004-L4079
static void
RemoveXlogFile(const struct dirent *segment_de,
			   XLogSegNo recycleSegNo, XLogSegNo *endlogSegNo,
			   TimeLineID insertTLI)
{
	char		path[MAXPGPATH];
// ... (L4010-L4012 생략: WIN32 변수)
	const char *segname = segment_de->d_name;

	snprintf(path, MAXPGPATH, XLOGDIR "/%s", segname);

	/*
	 * Before deleting the file, see if it can be recycled as a future log
	 * segment. Only recycle normal files, because we don't want to recycle
	 * symbolic links pointing to a separate archive directory.
	 */
	if (wal_recycle &&
		*endlogSegNo <= recycleSegNo &&
		XLogCtl->InstallXLogFileSegmentActive &&	/* callee rechecks this */
		get_dirent_type(path, segment_de, false, DEBUG2) == PGFILETYPE_REG &&
		InstallXLogFileSegment(endlogSegNo, path,
							   true, recycleSegNo, insertTLI))
	{
		ereport(DEBUG2,
				(errmsg_internal("recycled write-ahead log file \"%s\"",
								 segname)));
		CheckpointStats.ckpt_segs_recycled++;
		/* Needn't recheck that slot on future iterations */
		(*endlogSegNo)++;
	}
	else
	{
		/* No need for any more future segments, or recycling failed ... */
		int			rc;

		ereport(DEBUG2,
				(errmsg_internal("removing write-ahead log file \"%s\"",
								 segname)));

// ... (L4045-L4067 생략: WIN32 의 rename 후 삭제)
		rc = durable_unlink(path, LOG);
// ... (L4069-L4069 생략: #endif)
		if (rc != 0)
		{
			/* Message already logged by durable_unlink() */
			return;
		}
		CheckpointStats.ckpt_segs_removed++;
	}

	XLogArchiveCleanup(segname);
}
```

재활용 상한은 다음 체크포인트가 끝날 지점까지 쓸 만큼이다.

`src/backend/access/transam` / `xlog.c` L2229-L2268 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2229-L2268))

```c
// transam/xlog.c L2229-L2268
static XLogSegNo
XLOGfileslop(XLogRecPtr lastredoptr)
{
	XLogSegNo	minSegNo;
	XLogSegNo	maxSegNo;
	double		distance;
	XLogSegNo	recycleSegNo;

	/*
	 * Calculate the segment numbers that min_wal_size_mb and max_wal_size_mb
	 * correspond to. Always recycle enough segments to meet the minimum, and
	 * remove enough segments to stay below the maximum.
	 */
	minSegNo = lastredoptr / wal_segment_size +
		ConvertToXSegs(min_wal_size_mb, wal_segment_size) - 1;
	maxSegNo = lastredoptr / wal_segment_size +
		ConvertToXSegs(max_wal_size_mb, wal_segment_size) - 1;

	/*
	 * Between those limits, recycle enough segments to get us through to the
	 * estimated end of next checkpoint.
	 *
	 * To estimate where the next checkpoint will finish, assume that the
	 * system runs steadily consuming CheckPointDistanceEstimate bytes between
	 * every checkpoint.
	 */
	distance = (1.0 + CheckPointCompletionTarget) * CheckPointDistanceEstimate;
	/* add 10% for good measure. */
	distance *= 1.10;

	recycleSegNo = (XLogSegNo) ceil(((double) lastredoptr + distance) /
									wal_segment_size);

	if (recycleSegNo < minSegNo)
		recycleSegNo = minSegNo;
	if (recycleSegNo > maxSegNo)
		recycleSegNo = maxSegNo;

	return recycleSegNo;
}
```

## 동작 흐름

```text
 CreateCheckPoint 쪽
 L7359  _logSegNo = REDO 가 든 세그먼트
 L7360  KeepLogSeg(recptr, &_logSegNo)          더 앞이 필요하면 당긴다
 L7361  슬롯을 무효화했으면 L7369-L7370 다시
 L7372  _logSegNo--                             REDO 세그먼트는 남긴다
 L7373  RemoveOldXlogFiles(_logSegNo, RedoRecPtr, recptr, tli)

 RemoveOldXlogFiles
 L3871  endlogSegNo = 지금 WAL 끝 세그먼트
 L3872  recycleSegNo = XLOGfileslop(RedoRecPtr)
 L3879  lastoff = 경계 세그먼트의 파일 이름 (timeline 은 0 으로)
 L3886  pg_wal 의 파일마다
 L3889    WAL 세그먼트 이름이 아니면 건너뜀
 L3904    이름의 9번째 글자부터 (timeline 을 빼고) lastoff 와 문자열 비교, <= 면
 L3906      XLogArchiveCheckDone                 아카이빙 중이면 .done 이 있어야 true
 L3909      UpdateLastRemovedPtr
 L3911      RemoveXlogFile
 L4022        wal_recycle && endlogSegNo <= recycleSegNo && 일반 파일이면
                InstallXLogFileSegment(&endlogSegNo, path, find_free = true, recycleSegNo)
                성공 -> 재활용, endlogSegNo++
 L4036        아니면 durable_unlink                삭제
 L4078      XLogArchiveCleanup                  .ready/.done 상태 파일 정리
```

[체크포인트](../README.md) 개요의 예(REDO 0/3D000100, 체크포인트 레코드 0/5A3F1E28, 16MB 세그먼트, 슬롯과 `wal_keep_size` 없음)로 파일 이름을 따라가면 이렇다. 16MB 세그먼트면 이름의 가운데 8자리는 `segno / 256`, 끝 8자리는 `segno % 256` 이다.

```text
 경계
   _logSegNo = 0x3D  (0x3D000100 / 16MB)
   KeepLogSeg: 슬롯 없음, summarizer 없음, wal_keep_size = 0 -> 그대로
   _logSegNo-- = 0x3C
   lastoff = "00000000" "00000000" "0000003C"

 pg_wal file (TLI 1)                    d_name+8 vs lastoff+8      결과
 00000001000000000000001C               ...1C <= ...3C             재활용 또는 삭제
 ...
 00000001000000000000003C               ...3C <= ...3C             재활용 또는 삭제
 00000001000000000000003D               ...3D >  ...3C             남김 (REDO 가 여기 있다)
 ...
 00000001000000000000005A               ...5A >  ...3C             남김 (지금 쓰는 중)

 재활용 상한 XLOGfileslop(0/3D000100), 거리 추정치를 33 세그먼트로 가정하면
   minSegNo     = 0x3D + 5 - 1  = 0x41       min_wal_size 80MB = 5 세그먼트
   maxSegNo     = 0x3D + 64 - 1 = 0x7C       max_wal_size 1GB = 64 세그먼트
   distance     = (1 + 0.9) * 33 * 1.10 = 68.97 세그먼트
   recycleSegNo = ceil(0x3D + 68.97) = 130 = 0x82 -> maxSegNo 로 잘림 = 0x7C

 옛 파일 33개(1C..3C) 는 0x5A 이후 0x7C 까지의 빈 이름으로 차례로 rename 된다 (L4023-L4027)
 빈 이름이 0x7C 를 넘어 동나면 그때부터는 삭제
```

`KeepLogSeg` 가 경계를 당기는 경우다.

```text
 currSegNo = 체크포인트 레코드가 든 세그먼트 (0x5A). 각 행은 그 조건 하나만 있을 때다

 source                               values                          segno   결과
 slot restart_lsn (L8008-L8011)       0/2A000000                      0x2A    0x2A 부터 남김
   + max_slot_wal_keep_size (L8019)   512MB = 32 seg, 0x5A-0x2A = 48  0x3A    32 seg 로 상한. 슬롯은 무효화 대상
 wal_keep_size (L8046)                1GB = 64 seg                    0x1A    0x5A - 64 부터 남김
 WAL summarizer (L8035)               oldest unsummarized 0/30000000  0x30    아직 요약 안 된 0x30 부터 남김

 남길 경계는 REDO 세그먼트보다 앞으로만 움직인다 (L8062-L8063). 그 하나 앞까지만 지운다
```

## 결과가 쓰이는 곳

```text
 재활용된 파일
      --> 미래 세그먼트 이름으로 이미 존재하므로 XLogWrite 가 새 세그먼트를 0 으로 채워 만들 필요가 없다
 UpdateLastRemovedPtr
      --> XLogGetLastRemovedSegno 를 복제 슬롯 쪽이 읽는다 (replication/slot.c L1622, xlog.c L7944)
 지워진 파일
      --> standby 가 그 세그먼트를 요청하면 walsender 가 파일을 못 열고
          "requested WAL segment ... has already been removed" (replication/walsender.c L3119)
 CheckpointStats.ckpt_segs_removed, ckpt_segs_recycled
      --> log_checkpoints 의 "N removed, M recycled" (xlog.c L6773)
```

## 다루지 않는 것

`InvalidateObsoleteReplicationSlots` 의 슬롯 무효화, `PreallocXlogFiles`, timeline 전환 때의 `RemoveNonParentXlogFiles`, 아카이브 상태 파일(`.ready`, `.done`) 관리, Windows 의 rename 후 삭제는 요약만 했다.
