# ProcessSyncRequests

상위: [체크포인트](../README.md)

**체크포인트의 write 단계 동안 쌓인 "이 파일을 fsync 하라"는 요청을 파일마다 한 번씩 실행하는 함수다.** 요청은 `pendingOps` 해시에 `FileTag` 를 키로 모여 있다. 이번 체크포인트가 시작한 뒤 들어온 요청은 다음 체크포인트로 미루는데, 그 구분을 카운터 하나(`sync_cycle_ctr`)로 한다. fsync 실패는 기본 설정(`data_sync_retry = off`)에서 PANIC 이다.

## 위치

`src/backend/storage/sync` / `sync.c` L285-L475 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/sync/sync.c#L285-L475))

## 실제 코드

```c
// sync/sync.c L285-L475
void
ProcessSyncRequests(void)
{
	static bool sync_in_progress = false;

	HASH_SEQ_STATUS hstat;
	PendingFsyncEntry *entry;
	int			absorb_counter;

	/* Statistics on sync times */
	int			processed = 0;
	instr_time	sync_start,
				sync_end,
				sync_diff;
	uint64		elapsed;
	uint64		longest = 0;
	uint64		total_elapsed = 0;

	/*
	 * This is only called during checkpoints, and checkpoints should only
	 * occur in processes that have created a pendingOps.
	 */
	if (!pendingOps)
		elog(ERROR, "cannot sync without a pendingOps table");

	/*
	 * If we are in the checkpointer, the sync had better include all fsync
	 * requests that were queued by backends up to this point.  The tightest
	 * race condition that could occur is that a buffer that must be written
	 * and fsync'd for the checkpoint could have been dumped by a backend just
	 * before it was visited by BufferSync().  We know the backend will have
	 * queued an fsync request before clearing the buffer's dirtybit, so we
	 * are safe as long as we do an Absorb after completing BufferSync().
	 */
	AbsorbSyncRequests();

	/*
	 * To avoid excess fsync'ing (in the worst case, maybe a never-terminating
	 * checkpoint), we want to ignore fsync requests that are entered into the
	 * hashtable after this point --- they should be processed next time,
	 * instead.  We use sync_cycle_ctr to tell old entries apart from new
	 * ones: new ones will have cycle_ctr equal to the incremented value of
	 * sync_cycle_ctr.
	 *
	 * In normal circumstances, all entries present in the table at this point
	 * will have cycle_ctr exactly equal to the current (about to be old)
	 * value of sync_cycle_ctr.  However, if we fail partway through the
	 * fsync'ing loop, then older values of cycle_ctr might remain when we
	 * come back here to try again.  Repeated checkpoint failures would
	 * eventually wrap the counter around to the point where an old entry
	 * might appear new, causing us to skip it, possibly allowing a checkpoint
	 * to succeed that should not have.  To forestall wraparound, any time the
	 * previous ProcessSyncRequests() failed to complete, run through the
	 * table and forcibly set cycle_ctr = sync_cycle_ctr.
	 *
	 * Think not to merge this loop with the main loop, as the problem is
	 * exactly that that loop may fail before having visited all the entries.
	 * From a performance point of view it doesn't matter anyway, as this path
	 * will never be taken in a system that's functioning normally.
	 */
	if (sync_in_progress)
	{
		/* prior try failed, so update any stale cycle_ctr values */
		hash_seq_init(&hstat, pendingOps);
		while ((entry = (PendingFsyncEntry *) hash_seq_search(&hstat)) != NULL)
		{
			entry->cycle_ctr = sync_cycle_ctr;
		}
	}

	/* Advance counter so that new hashtable entries are distinguishable */
	sync_cycle_ctr++;

	/* Set flag to detect failure if we don't reach the end of the loop */
	sync_in_progress = true;

	/* Now scan the hashtable for fsync requests to process */
	absorb_counter = FSYNCS_PER_ABSORB;
	hash_seq_init(&hstat, pendingOps);
	while ((entry = (PendingFsyncEntry *) hash_seq_search(&hstat)) != NULL)
	{
		int			failures;

		/*
		 * If the entry is new then don't process it this time; it is new.
		 * Note "continue" bypasses the hash-remove call at the bottom of the
		 * loop.
		 */
		if (entry->cycle_ctr == sync_cycle_ctr)
			continue;

		/* Else assert we haven't missed it */
		Assert((CycleCtr) (entry->cycle_ctr + 1) == sync_cycle_ctr);

		/*
		 * If fsync is off then we don't have to bother opening the file at
		 * all.  (We delay checking until this point so that changing fsync on
		 * the fly behaves sensibly.)
		 */
		if (enableFsync)
		{
			/*
			 * If in checkpointer, we want to absorb pending requests every so
			 * often to prevent overflow of the fsync request queue.  It is
			 * unspecified whether newly-added entries will be visited by
			 * hash_seq_search, but we don't care since we don't need to
			 * process them anyway.
			 */
			if (--absorb_counter <= 0)
			{
				AbsorbSyncRequests();
				absorb_counter = FSYNCS_PER_ABSORB;
			}

			/*
			 * The fsync table could contain requests to fsync segments that
			 * have been deleted (unlinked) by the time we get to them. Rather
			 * than just hoping an ENOENT (or EACCES on Windows) error can be
			 * ignored, what we do on error is absorb pending requests and
			 * then retry. Since mdunlink() queues a "cancel" message before
			 * actually unlinking, the fsync request is guaranteed to be
			 * marked canceled after the absorb if it really was this case.
			 * DROP DATABASE likewise has to tell us to forget fsync requests
			 * before it starts deletions.
			 */
			for (failures = 0; !entry->canceled; failures++)
			{
				char		path[MAXPGPATH];

				INSTR_TIME_SET_CURRENT(sync_start);
				if (syncsw[entry->tag.handler].sync_syncfiletag(&entry->tag,
																path) == 0)
				{
					/* Success; update statistics about sync timing */
					INSTR_TIME_SET_CURRENT(sync_end);
					sync_diff = sync_end;
					INSTR_TIME_SUBTRACT(sync_diff, sync_start);
					elapsed = INSTR_TIME_GET_MICROSEC(sync_diff);
					if (elapsed > longest)
						longest = elapsed;
					total_elapsed += elapsed;
					processed++;

					if (log_checkpoints)
						elog(DEBUG1, "checkpoint sync: number=%d file=%s time=%.3f ms",
							 processed,
							 path,
							 (double) elapsed / 1000);

					break;		/* out of retry loop */
				}

				/*
				 * It is possible that the relation has been dropped or
				 * truncated since the fsync request was entered. Therefore,
				 * allow ENOENT, but only if we didn't fail already on this
				 * file.
				 */
				if (!FILE_POSSIBLY_DELETED(errno) || failures > 0)
					ereport(data_sync_elevel(ERROR),
							(errcode_for_file_access(),
							 errmsg("could not fsync file \"%s\": %m",
									path)));
				else
					ereport(DEBUG1,
							(errcode_for_file_access(),
							 errmsg_internal("could not fsync file \"%s\" but retrying: %m",
											 path)));

				/*
				 * Absorb incoming requests and check to see if a cancel
				 * arrived for this relation fork.
				 */
				AbsorbSyncRequests();
				absorb_counter = FSYNCS_PER_ABSORB; /* might as well... */
			}					/* end retry loop */
		}

		/* We are done with this entry, remove it */
		if (hash_search(pendingOps, &entry->tag, HASH_REMOVE, NULL) == NULL)
			elog(ERROR, "pendingOps corrupted");
	}							/* end loop over hashtable entries */

	/* Return sync performance metrics for report at checkpoint end */
	CheckpointStats.ckpt_sync_rels = processed;
	CheckpointStats.ckpt_longest_sync = longest;
	CheckpointStats.ckpt_agg_sync_time = total_elapsed;

	/* Flag successful completion of ProcessSyncRequests */
	sync_in_progress = false;
}
```

해시 항목은 파일 하나와 그 파일의 가장 오래된 요청이 들어온 주기를 기억한다.

`src/backend/storage/sync` / `sync.c` L56-L61 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/sync/sync.c#L56-L61))

```c
// sync/sync.c L56-L61
typedef struct
{
	FileTag		tag;			/* identifies handler and file */
	CycleCtr	cycle_ctr;		/* sync_cycle_ctr of oldest request */
	bool		canceled;		/* canceled is true if we canceled "recently" */
} PendingFsyncEntry;
```

## 동작 흐름

```text
 ProcessSyncRequests()

 L307  pendingOps 가 없으면 ERROR                 checkpointer (또는 단일 사용자 backend) 만 갖는다
 L319  AbsorbSyncRequests                         BufferSync 직후 backend 가 보낸 요청까지 흡수
 L345  지난번이 중간에 실패했으면 모든 항목의 cycle_ctr 를 현재 값으로 맞춤
 L356  sync_cycle_ctr++                           이제부터 들어오는 항목은 새 값을 단다
 L359  sync_in_progress = true
 L364  해시를 훑으며
 L373    entry->cycle_ctr == sync_cycle_ctr 면 continue    이번 주기 시작 뒤 들어온 것
 L384    enableFsync (fsync = on) 면
 L393      10개(FSYNCS_PER_ABSORB)마다 AbsorbSyncRequests
 L410      canceled 가 아닌 동안
 L415        sync_syncfiletag (md 의 경우 그 세그먼트 파일 fsync)
             성공 -> 통계, break
 L443        실패: 파일이 지워졌을 수 있는 errno 이고 첫 실패면 DEBUG1, Absorb 후 재시도
                   그 밖이면 ereport(data_sync_elevel(ERROR))  기본 PANIC
 L464    항목을 해시에서 제거
 L469  ckpt_sync_rels, longest, agg_sync_time 통계
 L474  sync_in_progress = false
```

`cycle_ctr` 로 "이번 체크포인트 몫"을 가르는 모습이다. 카운터 값은 예시다.

```text
 sync_cycle_ctr = 7 에서 시작. 항목은 FileTag: cycle_ctr

 when            pendingOps                     설명
 BufferSync      16384/seg0: 7, 16390/seg0: 7   write 단계에서 들어온 요청
 L319            + 16384/seg1: 7                backend 가 보낸 요청을 흡수
 L356            sync_cycle_ctr = 8
 L364 loop      + 16400/seg0: 8                새 항목이라 현재 값을 단다 (sync.c L557-L559)

 L373 판정
   16384/seg0 (7)   7 != 8  fsync 후 제거
   16390/seg0 (7)   7 != 8  fsync 후 제거
   16384/seg1 (7)   7 != 8  fsync 후 제거
   16400/seg0 (8)   8 == 8  건너뜀. 다음 체크포인트 몫

 이미 있는 항목에 요청이 또 오면 cycle_ctr 를 바꾸지 않는다. 가장 오래된 요청의 주기를 뜻해야 해서다
 (주석 L563-L566)

 새 요청까지 계속 쫓아가면 바쁜 시스템에서 체크포인트가 끝나지 않을 수 있다 (주석 L322-L325)
```

fsync 실패를 PANIC 으로 올리는 것은 `data_sync_elevel` 의 기본 동작이다.

```text
 storage/file/fd.c L4001-L4004   data_sync_retry ? elevel : PANIC
 storage/file/fd.c L162          data_sync_retry = false (기본)

 fsync 가 EIO 를 돌려줌 -> PANIC -> postmaster 가 backend 크래시와 같이 다뤄 복구 사이클을 돈다
   (checkpointer.c 머리 주석 L21-L26)
 복구는 마지막으로 성공한 체크포인트의 REDO 부터 재생해 그 페이지들을 다시 만든다
 (이번 체크포인트는 pg_control 을 갱신하기 전에 죽었으므로 이전 체크포인트가 기준이다)
```

## 결과가 쓰이는 곳

```text
 fsync 완료
      --> [04] CheckPointGuts 가 돌아가고 [03] CreateCheckPoint 가 체크포인트 레코드를 쓴다
 CheckpointStats.ckpt_sync_rels, ckpt_longest_sync, ckpt_agg_sync_time
      --> log_checkpoints 의 "sync files=..., longest=..., average=..."
```

## 다루지 않는 것

`RememberSyncRequest` 와 cancel 요청 처리, `SyncPostCheckpoint` 의 지연된 unlink, `mdsyncfiletag` 내부, `fsync = off` 일 때의 동작 차이는 요약만 했다.
