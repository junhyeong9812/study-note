# BufferSync

상위: [체크포인트](../README.md)

**체크포인트가 시작될 때 더러웠던 공유 버퍼만 골라, 파일 순서로 정렬하고, 테이블스페이스 사이에 번갈아 가며 쓰는 함수다.** 시작 순간에 대상에 `BM_CHECKPOINT_NEEDED` 를 찍어 두기 때문에 도중에 새로 더러워진 버퍼는 쓰지 않는다. 정렬은 랜덤 I/O 를 줄이려는 것이고, 테이블스페이스 균형은 정렬 때문에 한 디스크에만 몰리는 쓰기를 퍼뜨리려는 것이다(주석 L3446-L3452). 버퍼 하나를 처리할 때마다 `CheckpointWriteDelay` 를 불러 속도를 맞춘다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L3366-L3629 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L3366-L3629))

## 실제 코드

```c
// buffer/bufmgr.c L3366-L3629
static void
BufferSync(int flags)
{
	uint32		buf_state;
	int			buf_id;
	int			num_to_scan;
	int			num_spaces;
	int			num_processed;
	int			num_written;
	CkptTsStatus *per_ts_stat = NULL;
	Oid			last_tsid;
	binaryheap *ts_heap;
	int			i;
	int			mask = BM_DIRTY;
	WritebackContext wb_context;

	/*
	 * Unless this is a shutdown checkpoint or we have been explicitly told,
	 * we write only permanent, dirty buffers.  But at shutdown or end of
	 * recovery, we write all dirty buffers.
	 */
	if (!((flags & (CHECKPOINT_IS_SHUTDOWN | CHECKPOINT_END_OF_RECOVERY |
					CHECKPOINT_FLUSH_ALL))))
		mask |= BM_PERMANENT;

	/*
	 * Loop over all buffers, and mark the ones that need to be written with
	 * BM_CHECKPOINT_NEEDED.  Count them as we go (num_to_scan), so that we
	 * can estimate how much work needs to be done.
	 *
	 * This allows us to write only those pages that were dirty when the
	 * checkpoint began, and not those that get dirtied while it proceeds.
	 * Whenever a page with BM_CHECKPOINT_NEEDED is written out, either by us
	 * later in this function, or by normal backends or the bgwriter cleaning
	 * scan, the flag is cleared.  Any buffer dirtied after this point won't
	 * have the flag set.
	 *
	 * Note that if we fail to write some buffer, we may leave buffers with
	 * BM_CHECKPOINT_NEEDED still set.  This is OK since any such buffer would
	 * certainly need to be written for the next checkpoint attempt, too.
	 */
	num_to_scan = 0;
	for (buf_id = 0; buf_id < NBuffers; buf_id++)
	{
		BufferDesc *bufHdr = GetBufferDescriptor(buf_id);

		/*
		 * Header spinlock is enough to examine BM_DIRTY, see comment in
		 * SyncOneBuffer.
		 */
		buf_state = LockBufHdr(bufHdr);

		if ((buf_state & mask) == mask)
		{
			CkptSortItem *item;

			buf_state |= BM_CHECKPOINT_NEEDED;

			item = &CkptBufferIds[num_to_scan++];
			item->buf_id = buf_id;
			item->tsId = bufHdr->tag.spcOid;
			item->relNumber = BufTagGetRelNumber(&bufHdr->tag);
			item->forkNum = BufTagGetForkNum(&bufHdr->tag);
			item->blockNum = bufHdr->tag.blockNum;
		}

		UnlockBufHdr(bufHdr, buf_state);

		/* Check for barrier events in case NBuffers is large. */
		if (ProcSignalBarrierPending)
			ProcessProcSignalBarrier();
	}

	if (num_to_scan == 0)
		return;					/* nothing to do */

	// ... (L3442-L3444 생략: writeback 문맥 초기화, dtrace)

	/*
	 * Sort buffers that need to be written to reduce the likelihood of random
	 * IO. The sorting is also important for the implementation of balancing
	 * writes between tablespaces. Without balancing writes we'd potentially
	 * end up writing to the tablespaces one-by-one; possibly overloading the
	 * underlying system.
	 */
	sort_checkpoint_bufferids(CkptBufferIds, num_to_scan);

	num_spaces = 0;

	/*
	 * Allocate progress status for each tablespace with buffers that need to
	 * be flushed. This requires the to-be-flushed array to be sorted.
	 */
	last_tsid = InvalidOid;
	for (i = 0; i < num_to_scan; i++)
	{
		CkptTsStatus *s;
		Oid			cur_tsid;

		cur_tsid = CkptBufferIds[i].tsId;

		/*
		 * Grow array of per-tablespace status structs, every time a new
		 * tablespace is found.
		 */
		if (last_tsid == InvalidOid || last_tsid != cur_tsid)
		{
			Size		sz;

			num_spaces++;

			/*
			 * Not worth adding grow-by-power-of-2 logic here - even with a
			 * few hundred tablespaces this should be fine.
			 */
			sz = sizeof(CkptTsStatus) * num_spaces;

			if (per_ts_stat == NULL)
				per_ts_stat = (CkptTsStatus *) palloc(sz);
			else
				per_ts_stat = (CkptTsStatus *) repalloc(per_ts_stat, sz);

			s = &per_ts_stat[num_spaces - 1];
			memset(s, 0, sizeof(*s));
			s->tsId = cur_tsid;

			/*
			 * The first buffer in this tablespace. As CkptBufferIds is sorted
			 * by tablespace all (s->num_to_scan) buffers in this tablespace
			 * will follow afterwards.
			 */
			s->index = i;

			/*
			 * progress_slice will be determined once we know how many buffers
			 * are in each tablespace, i.e. after this loop.
			 */

			last_tsid = cur_tsid;
		}
		else
		{
			s = &per_ts_stat[num_spaces - 1];
		}

		s->num_to_scan++;

		/* Check for barrier events. */
		if (ProcSignalBarrierPending)
			ProcessProcSignalBarrier();
	}

	Assert(num_spaces > 0);

	/*
	 * Build a min-heap over the write-progress in the individual tablespaces,
	 * and compute how large a portion of the total progress a single
	 * processed buffer is.
	 */
	ts_heap = binaryheap_allocate(num_spaces,
								  ts_ckpt_progress_comparator,
								  NULL);

	for (i = 0; i < num_spaces; i++)
	{
		CkptTsStatus *ts_stat = &per_ts_stat[i];

		ts_stat->progress_slice = (float8) num_to_scan / ts_stat->num_to_scan;

		binaryheap_add_unordered(ts_heap, PointerGetDatum(ts_stat));
	}

	binaryheap_build(ts_heap);

	/*
	 * Iterate through to-be-checkpointed buffers and write the ones (still)
	 * marked with BM_CHECKPOINT_NEEDED. The writes are balanced between
	 * tablespaces; otherwise the sorting would lead to only one tablespace
	 * receiving writes at a time, making inefficient use of the hardware.
	 */
	num_processed = 0;
	num_written = 0;
	while (!binaryheap_empty(ts_heap))
	{
		BufferDesc *bufHdr = NULL;
		CkptTsStatus *ts_stat = (CkptTsStatus *)
			DatumGetPointer(binaryheap_first(ts_heap));

		buf_id = CkptBufferIds[ts_stat->index].buf_id;
		Assert(buf_id != -1);

		bufHdr = GetBufferDescriptor(buf_id);

		num_processed++;

		/*
		 * We don't need to acquire the lock here, because we're only looking
		 * at a single bit. It's possible that someone else writes the buffer
		 * and clears the flag right after we check, but that doesn't matter
		 * since SyncOneBuffer will then do nothing.  However, there is a
		 * further race condition: it's conceivable that between the time we
		 * examine the bit here and the time SyncOneBuffer acquires the lock,
		 * someone else not only wrote the buffer but replaced it with another
		 * page and dirtied it.  In that improbable case, SyncOneBuffer will
		 * write the buffer though we didn't need to.  It doesn't seem worth
		 * guarding against this, though.
		 */
		if (pg_atomic_read_u32(&bufHdr->state) & BM_CHECKPOINT_NEEDED)
		{
			if (SyncOneBuffer(buf_id, false, &wb_context) & BUF_WRITTEN)
			{
				TRACE_POSTGRESQL_BUFFER_SYNC_WRITTEN(buf_id);
				PendingCheckpointerStats.buffers_written++;
				num_written++;
			}
		}

		/*
		 * Measure progress independent of actually having to flush the buffer
		 * - otherwise writing become unbalanced.
		 */
		ts_stat->progress += ts_stat->progress_slice;
		ts_stat->num_scanned++;
		ts_stat->index++;

		/* Have all the buffers from the tablespace been processed? */
		if (ts_stat->num_scanned == ts_stat->num_to_scan)
		{
			binaryheap_remove_first(ts_heap);
		}
		else
		{
			/* update heap with the new progress */
			binaryheap_replace_first(ts_heap, PointerGetDatum(ts_stat));
		}

		/*
		 * Sleep to throttle our I/O rate.
		 *
		 * (This will check for barrier events even if it doesn't sleep.)
		 */
		CheckpointWriteDelay(flags, (double) num_processed / num_to_scan);
	}

	// ... (L3612-L3628 생략: 남은 writeback 발행, 메모리 해제, 통계)
}
```

정렬 키는 테이블스페이스가 먼저다. 균형 로직이 "같은 테이블스페이스의 버퍼가 배열에서 붙어 있다"에 기대기 때문이다(주석 L6359-L6360).

`src/backend/storage/buffer` / `bufmgr.c` L6362-L6406 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L6362-L6406))

```c
// buffer/bufmgr.c L6362-L6406
static inline int
ckpt_buforder_comparator(const CkptSortItem *a, const CkptSortItem *b)
{
	/* compare tablespace */
	if (a->tsId < b->tsId)
		return -1;
	else if (a->tsId > b->tsId)
		return 1;
	/* compare relation */
	if (a->relNumber < b->relNumber)
		return -1;
	else if (a->relNumber > b->relNumber)
		return 1;
	/* compare fork */
	else if (a->forkNum < b->forkNum)
		return -1;
	else if (a->forkNum > b->forkNum)
		return 1;
	/* compare block number */
	else if (a->blockNum < b->blockNum)
		return -1;
	else if (a->blockNum > b->blockNum)
		return 1;
	/* equal page IDs are unlikely, but not impossible */
	return 0;
}

/*
 * Comparator for a Min-Heap over the per-tablespace checkpoint completion
 * progress.
 */
static int
ts_ckpt_progress_comparator(Datum a, Datum b, void *arg)
{
	CkptTsStatus *sa = (CkptTsStatus *) a;
	CkptTsStatus *sb = (CkptTsStatus *) b;

	/* we want a min-heap, so return 1 for the a < b */
	if (sa->progress < sb->progress)
		return 1;
	else if (sa->progress == sb->progress)
		return 0;
	else
		return -1;
}
```

정렬 항목과 테이블스페이스별 진행 상태는 이 두 구조체다. `CkptSortItem` 배열(`CkptBufferIds`)은 버퍼 수만큼 공유 메모리에 미리 잡혀 있다.

`src/include/storage` / `buf_internals.h` L391-L398 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf_internals.h#L391-L398))

```c
// storage/buf_internals.h L391-L398
typedef struct CkptSortItem
{
	Oid			tsId;
	RelFileNumber relNumber;
	ForkNumber	forkNum;
	BlockNumber blockNum;
	int			buf_id;
} CkptSortItem;
```

`src/backend/storage/buffer` / `bufmgr.c` L106-L128 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L106-L128))

```c
// buffer/bufmgr.c L106-L128
typedef struct CkptTsStatus
{
	/* oid of the tablespace */
	Oid			tsId;

	/*
	 * Checkpoint progress for this tablespace. To make progress comparable
	 * between tablespaces the progress is, for each tablespace, measured as a
	 * number between 0 and the total number of to-be-checkpointed pages. Each
	 * page checkpointed in this tablespace increments this space's progress
	 * by progress_slice.
	 */
	float8		progress;
	float8		progress_slice;

	/* number of to-be checkpointed pages in this tablespace */
	int			num_to_scan;
	/* already processed pages in this tablespace */
	int			num_scanned;

	/* current offset in CkptBufferIds for this tablespace */
	int			index;
} CkptTsStatus;
```

## 동작 흐름

```text
 BufferSync(flags)

 L3387  shutdown, end-of-recovery, FLUSH_ALL 이 아니면 mask = BM_DIRTY | BM_PERMANENT
          (unlogged 버퍼는 평소 체크포인트에서 건너뛴다)
 L3408  모든 버퍼 (0 .. NBuffers-1)
          LockBufHdr
          (state & mask) == mask 면 BM_CHECKPOINT_NEEDED 를 켜고 CkptBufferIds 에 추가
          UnlockBufHdr
 L3439  하나도 없으면 return
 L3453  sort_checkpoint_bufferids          (tsId, relNumber, forkNum, blockNum) 순
 L3461  정렬된 배열을 훑으며 테이블스페이스마다 CkptTsStatus 하나
          index = 그 테이블스페이스의 첫 위치, num_to_scan = 개수
 L3535  progress_slice = 전체 개수 / 그 테이블스페이스 개수
 L3527-L3540  진행률(progress) 기준 min-heap 을 만든다
 L3550  heap 이 빌 때까지
 L3553    진행률이 가장 낮은 테이블스페이스를 꺼낸다
 L3575    아직 BM_CHECKPOINT_NEEDED 면 [06] SyncOneBuffer
 L3589    progress += progress_slice           썼든 안 썼든 진행률은 오른다
 L3594    다 훑었으면 heap 에서 제거, 아니면 위치 갱신
 L3609    [07] CheckpointWriteDelay(flags, num_processed / num_to_scan)
```

시작 순간의 표시가 대상의 경계다. 도중에 더러워진 버퍼는 표시가 없으니 쓰지 않고, 도중에 남이 써 준 버퍼는 표시가 지워져 건너뛴다(주석 L3396-L3405).

```text
 버퍼 4개, 체크포인트 시작 t0

 buf  state at t0          L3418 mark   L3575    도중에 일어난 일
 b1   DIRTY | PERMANENT    NEEDED       write    없음
 b2   DIRTY | PERMANENT    NEEDED       skip     희생자로 뽑혀 FlushBuffer 가 먼저 씀
                                                 TerminateBufferIO 가 NEEDED 도 지운다 (L6132)
 b3   clean                -            skip     t0 뒤에 backend 가 고쳐 DIRTY. 다음 체크포인트 몫
 b4   DIRTY, unlogged      -            skip     mask 의 PERMANENT 에 걸려 처음부터 빠짐

 b3 를 건너뛰어도 되는 이유: b3 의 변경을 적은 WAL 레코드는 REDO 지점 뒤에 있다
 복구는 REDO 부터 재생하므로 b3 의 변경을 다시 만든다
```

테이블스페이스 균형을 버퍼 10개(테이블스페이스 A 에 8개, B 에 2개)로 그리면 이렇다. 진행률은 0 에서 10(전체 개수)까지 같은 눈금으로 오른다.

```text
 progress_slice   A = 10 / 8 = 1.25    B = 10 / 2 = 5      (L3535)

 step  pop   A after   B after   비고
 1     A     1.25      0         둘 다 0 이라 동률. 어느 쪽이든 먼저 나올 수 있다
 2     B     1.25      5
 3     A     2.50      5
 4     A     3.75      5
 5     A     5.00      5
 6     A     6.25      5         동률. B 가 먼저 나올 수도 있다
 7     B     6.25      10        B 끝 -> heap 에서 빠짐
 8     A     7.50      -
 9     A     8.75      -
 10    A     10.00     -         A 끝

 A 4번에 B 1번 꼴로 섞인다. 정렬만 하고 균형을 안 잡으면 A 8개를 다 쓴 뒤에야 B 로 넘어간다
 A 안에서는 여전히 (rel, fork, block) 오름차순이다
```

## 결과가 쓰이는 곳

```text
 OS page cache 로 들어간 데이터 페이지 + 쌓인 fsync 요청
      --> [04] CheckPointGuts 의 다음 줄 [08] ProcessSyncRequests 가 fsync
 BM_CHECKPOINT_NEEDED 해제
      --> FlushBuffer 의 TerminateBufferIO (bufmgr.c L6132)
 PendingCheckpointerStats.buffers_written, CheckpointStats.ckpt_bufs_written
      --> pg_stat_checkpointer, log_checkpoints 의 "wrote N buffers"
```

## 다루지 않는 것

writeback 제어(`WritebackContextInit`, `ScheduleBufferTagForWriteback`, `IssuePendingWritebacks`, `checkpoint_flush_after`), `binaryheap` 구현, `sort_template.h` 의 정렬 구현, bgwriter 의 `BgBufferSync` 는 요약만 했다.
