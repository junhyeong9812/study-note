# XLogReadBufferForRedoExtended

상위: [WAL redo (복구)](../README.md)

**redo 함수가 고칠 페이지를 받는 단일 창구이고, "이 레코드를 이 페이지에 적용해야 하는가"를 정하는 함수다.** 규칙은 둘이다. 레코드에 적용할 full-page image(FPI)가 있으면 디스크 페이지를 읽지 않고 이미지로 덮어쓴 뒤 `BLK_RESTORED` 를 돌려준다. 없으면 페이지를 읽어 exclusive lock 을 잡고, 레코드 끝 LSN 이 페이지 LSN 이하이면 `BLK_DONE`(이미 반영됨), 아니면 `BLK_NEEDS_REDO` 다. FPI 를 페이지 LSN 과 상관없이 덮어쓰는 이유는 크래시 때 반쯤 쓰인 페이지를 믿을 수 없어서다(주석 L293-L300).

## 위치

`src/backend/access/transam` / `xlogutils.c` L361-L452 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogutils.c#L361-L452))

## 실제 코드

```c
// transam/xlogutils.c L361-L452
XLogRedoAction
XLogReadBufferForRedoExtended(XLogReaderState *record,
							  uint8 block_id,
							  ReadBufferMode mode, bool get_cleanup_lock,
							  Buffer *buf)
{
	XLogRecPtr	lsn = record->EndRecPtr;
	RelFileLocator rlocator;
	ForkNumber	forknum;
	BlockNumber blkno;
	Buffer		prefetch_buffer;
	Page		page;
	bool		zeromode;
	bool		willinit;

	if (!XLogRecGetBlockTagExtended(record, block_id, &rlocator, &forknum, &blkno,
									&prefetch_buffer))
	{
		/* Caller specified a bogus block_id */
		elog(PANIC, "failed to locate backup block with ID %d in WAL record",
			 block_id);
	}

	/*
	 * Make sure that if the block is marked with WILL_INIT, the caller is
	 * going to initialize it. And vice versa.
	 */
	zeromode = (mode == RBM_ZERO_AND_LOCK || mode == RBM_ZERO_AND_CLEANUP_LOCK);
	willinit = (XLogRecGetBlock(record, block_id)->flags & BKPBLOCK_WILL_INIT) != 0;
	if (willinit && !zeromode)
		elog(PANIC, "block with WILL_INIT flag in WAL record must be zeroed by redo routine");
	if (!willinit && zeromode)
		elog(PANIC, "block to be initialized in redo routine must be marked with WILL_INIT flag in the WAL record");

	/* If it has a full-page image and it should be restored, do it. */
	if (XLogRecBlockImageApply(record, block_id))
	{
		Assert(XLogRecHasBlockImage(record, block_id));
		*buf = XLogReadBufferExtended(rlocator, forknum, blkno,
									  get_cleanup_lock ? RBM_ZERO_AND_CLEANUP_LOCK : RBM_ZERO_AND_LOCK,
									  prefetch_buffer);
		page = BufferGetPage(*buf);
		if (!RestoreBlockImage(record, block_id, page))
			ereport(ERROR,
					(errcode(ERRCODE_INTERNAL_ERROR),
					 errmsg_internal("%s", record->errormsg_buf)));

		/*
		 * The page may be uninitialized. If so, we can't set the LSN because
		 * that would corrupt the page.
		 */
		if (!PageIsNew(page))
		{
			PageSetLSN(page, lsn);
		}

		MarkBufferDirty(*buf);

		/*
		 * At the end of crash recovery the init forks of unlogged relations
		 * are copied, without going through shared buffers. So we need to
		 * force the on-disk state of init forks to always be in sync with the
		 * state in shared buffers. Use XLogFlushBufferForRedoIfInit() for
		 * redo routines that dirty init-fork buffers without restoring a
		 * full-page image.
		 */
		if (forknum == INIT_FORKNUM)
			FlushOneBuffer(*buf);

		return BLK_RESTORED;
	}
	else
	{
		*buf = XLogReadBufferExtended(rlocator, forknum, blkno, mode, prefetch_buffer);
		if (BufferIsValid(*buf))
		{
			if (mode != RBM_ZERO_AND_LOCK && mode != RBM_ZERO_AND_CLEANUP_LOCK)
			{
				if (get_cleanup_lock)
					LockBufferForCleanup(*buf);
				else
					LockBuffer(*buf, BUFFER_LOCK_EXCLUSIVE);
			}
			if (lsn <= PageGetLSN(BufferGetPage(*buf)))
				return BLK_DONE;
			else
				return BLK_NEEDS_REDO;
		}
		else
			return BLK_NOTFOUND;
	}
}
```

redo 함수들이 보통 부르는 쪽은 기본 인자를 채운 이 포장이다.

`src/backend/access/transam` / `xlogutils.c` L302-L308 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogutils.c#L302-L308))

```c
// transam/xlogutils.c L302-L308
XLogRedoAction
XLogReadBufferForRedo(XLogReaderState *record, uint8 block_id,
					  Buffer *buf)
{
	return XLogReadBufferForRedoExtended(record, block_id, RBM_NORMAL,
										 false, buf);
}
```

FPI 는 페이지 가운데의 빈 공간(hole)을 빼고 저장되므로, 복원할 때 그 자리를 0 으로 채운다.

`src/backend/access/transam` / `xlogreader.c` L2165-L2180 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogreader.c#L2165-L2180))

```c
// transam/xlogreader.c L2165-L2180
	/* generate page, taking into account hole if necessary */
	if (bkpb->hole_length == 0)
	{
		memcpy(page, ptr, BLCKSZ);
	}
	else
	{
		memcpy(page, ptr, bkpb->hole_offset);
		/* must zero-fill the hole */
		MemSet(page + bkpb->hole_offset, 0, bkpb->hole_length);
		memcpy(page + (bkpb->hole_offset + bkpb->hole_length),
			   ptr + bkpb->hole_offset,
			   BLCKSZ - (bkpb->hole_offset + bkpb->hole_length));
	}

	return true;
```

## 동작 흐름

```text
 XLogReadBufferForRedoExtended(record, block_id, mode, get_cleanup_lock, &buf)

 L367  lsn = record->EndRecPtr
 L376  block_id 의 (rlocator, forknum, blkno) 와 prefetch 가 찾아 둔 버퍼
 L388-L393  WILL_INIT 표시와 ZERO 모드가 서로 맞지 않으면 PANIC
 L396  XLogRecBlockImageApply ?   (BKPIMAGE_APPLY 가 켜진 FPI)
 L399    yes: XLogReadBufferExtended(RBM_ZERO_AND_LOCK)   디스크를 읽지 않고 0 페이지 + lock
 L403         RestoreBlockImage -> 이미지 복사, hole 은 0
 L414         PageSetLSN(page, lsn)                       새 페이지가 아니면
 L417         MarkBufferDirty
 L427         init fork 면 바로 FlushOneBuffer
 L430         return BLK_RESTORED
 L434    no:  XLogReadBufferExtended(mode)                디스크에서 읽는다
 L435         Invalid 면 return BLK_NOTFOUND              릴레이션이 뒤에서 잘렸다
 L437-L443    ZERO 모드가 아니면 LockBuffer(EXCLUSIVE) 또는 cleanup lock
 L444         lsn <= PageGetLSN(page) ? BLK_DONE : BLK_NEEDS_REDO
```

FPI 가 왜 필요한지는 "찢어진 페이지"에서 드러난다. PostgreSQL 페이지는 8KB 이고, OS 와 디스크가 그보다 작은 단위로 쓰다 전원이 나가면 앞쪽 반만 새 내용인 페이지가 남을 수 있다.

```text
 체크포인트 REDO = 0/3D000100 이후 페이지 P 를 처음 고치는 레코드 R1

 쓰는 쪽 (XLogRecordAssemble, xloginsert.c L618-L621)
   P 의 page LSN (0/3C8F0010) <= RedoRecPtr (0/3D000100) -> needs_backup -> FPI 를 붙인다
   BKPIMAGE_APPLY 켬 (L720-L721)

 R1 끝 0/3D2A2F30 (FPI 포함), R2 끝 0/3E001A40 (FPI 없음, P 를 또 고침)

 디스크의 P: bgwriter 가 R2 뒤의 P 를 쓰다가 크래시 -> 앞 4KB 는 R2 뒤, 뒤 4KB 는 R1 전
             page LSN 필드(앞쪽에 있다)는 0/3E001A40 처럼 보인다

 FPI 가 없다면
   R1: 0/3D2A2F30 <= 0/3E001A40 -> BLK_DONE    건너뜀
   R2: 0/3E001A40 <= 0/3E001A40 -> BLK_DONE    건너뜀
   -> 뒤 4KB 의 옛 내용이 그대로 남는다. 페이지가 깨진 채 복구 완료

 실제 (FPI 있음)
   R1: L396 yes -> 디스크 P 를 읽지 않고 이미지로 덮어씀, page LSN = 0/3D2A2F30   BLK_RESTORED
   R2: 0/3E001A40 > 0/3D2A2F30 -> BLK_NEEDS_REDO -> 다시 적용, page LSN = 0/3E001A40
   -> 온전한 페이지
```

FPI 가 없는 블록(체크포인트 뒤 두 번째 수정부터, 또는 `full_page_writes = off`)에서는 LSN 비교만으로 판단한다. 같은 페이지를 고친 레코드 셋을 디스크 상태 하나로 재생하면 이렇다.

```text
 디스크의 페이지 Q: page LSN = 0/3E001A40 (R2 까지 반영된 채 쓰였다)

 record  EndRecPtr     L444 비교                      결과
 R1      0/3D200050    0/3D200050 <= 0/3E001A40      BLK_DONE
 R2      0/3E001A40    0/3E001A40 <= 0/3E001A40      BLK_DONE        같으면 이미 반영된 것
 R3      0/3F000088    0/3F000088 >  0/3E001A40      BLK_NEEDS_REDO  적용 후 page LSN = 0/3F000088

 page LSN 은 "이 페이지를 마지막으로 바꾼 레코드의 끝"이다. 재생도 PageSetLSN(EndRecPtr) 로 같은 규칙을 지킨다
```

FPI 의 hole 은 페이지 헤더의 `pd_lower` 와 `pd_upper` 사이 빈 공간이다.

```text
 8192 바이트 heap 페이지, 튜플 4개 (각 t_len 72, MAXALIGN 72), pd_lower = 40, pd_upper = 7904 (예)
   pd_lower = 헤더 24 + 라인 포인터 4 * 4 = 40
   pd_upper = 8192 - 4 * 72 = 7904      PageAddItem 이 MAXALIGN 크기만큼 내려가므로 8 의 배수다

 0        40                                   7904              8192
 +--------+------------------------------------+-----------------+
 | header |            hole (0)                | 튜플들          |
 | + lp   |                                    |                 |
 +--------+------------------------------------+-----------------+
 WAL 에는 0..40 과 7904..8192 만 (328 바이트). hole_offset = 40, hole_length = 7864
 RestoreBlockImage L2172-L2177: 앞 40 복사, 7864 바이트 0, 뒤 288 복사
```

## 결과가 쓰이는 곳

```text
 BLK_NEEDS_REDO + exclusive lock 이 걸린 buffer
      --> [08] heap_xlog_insert 가 튜플을 넣고 PageSetLSN, MarkBufferDirty
 BLK_RESTORED
      --> 호출자는 아무것도 안 하고 UnlockReleaseBuffer. 이미지가 곧 결과다
 BLK_DONE
      --> 호출자는 unlock 만. 단 heap_xlog_insert 는 그 전에 VM 비트를 따로 고친다 (L509)
 BLK_NOTFOUND
      --> 호출자는 건너뛴다. XLogReadBufferExtended 가 log_invalid_page 로 기록해 둔다 (xlogutils.c L529, L560)
          일관 지점에 닿았는데도 뒤의 drop, truncate 레코드로 지워지지 않았으면
          XLogCheckInvalidPages 가 PANIC (L234-L258, ignore_invalid_pages 면 WARNING)
```

## 다루지 않는 것

`XLogReadBufferExtended` 의 릴레이션 확장과 invalid page 추적, FPI 압축 해제(pglz, lz4, zstd), WAL prefetch 의 `prefetch_buffer` 힌트, cleanup lock 이 필요한 경우(`heap2` 의 prune), `XLogRecordAssemble` 의 FPI 결정 자세한 내용([행 쓰기와 WAL 기록](../../heap-insert-wal/07_XLogRecordAssemble/README.md))은 요약만 했다.
