# CheckpointerMain

상위: [체크포인트](../README.md)

**checkpointer 프로세스의 본체이고, 요청 플래그와 `checkpoint_timeout` 두 가지만 보고 체크포인트를 시작하는 무한 루프다.** WAL 양(`max_wal_size`)은 직접 보지 않는다. 그 조건은 backend 가 세그먼트를 채울 때 판단해 플래그로 넘겨준다(파일 머리 주석 L8-L11). 복구 중이면 같은 자리에서 체크포인트 대신 restartpoint 를 만든다.

## 위치

`src/backend/postmaster` / `checkpointer.c` L181-L636 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/checkpointer.c#L181-L636))

## 실제 코드

```c
// postmaster/checkpointer.c L181-L636
void
CheckpointerMain(const void *startup_data, size_t startup_data_len)
{
	sigjmp_buf	local_sigjmp_buf;
	MemoryContext checkpointer_context;

	Assert(startup_data_len == 0);

	MyBackendType = B_CHECKPOINTER;
	AuxiliaryProcessMainCommon();

	CheckpointerShmem->checkpointer_pid = MyProcPid;

	// ... (L194-L343 생략: 시그널 설정, 메모리 컨텍스트, sigsetjmp 에러 복구 블록)

	/*
	 * Loop until we've been asked to write the shutdown checkpoint or
	 * terminate.
	 */
	for (;;)
	{
		bool		do_checkpoint = false;
		int			flags = 0;
		pg_time_t	now;
		int			elapsed_secs;
		int			cur_timeout;
		bool		chkpt_or_rstpt_requested = false;
		bool		chkpt_or_rstpt_timed = false;

		/* Clear any already-pending wakeups */
		ResetLatch(MyLatch);

		/*
		 * Process any requests or signals received recently.
		 */
		AbsorbSyncRequests();

		ProcessCheckpointerInterrupts();
		if (ShutdownXLOGPending || ShutdownRequestPending)
			break;

		/*
		 * Detect a pending checkpoint request by checking whether the flags
		 * word in shared memory is nonzero.  We shouldn't need to acquire the
		 * ckpt_lck for this.
		 */
		if (((volatile CheckpointerShmemStruct *) CheckpointerShmem)->ckpt_flags)
		{
			do_checkpoint = true;
			chkpt_or_rstpt_requested = true;
		}

		/*
		 * Force a checkpoint if too much time has elapsed since the last one.
		 * Note that we count a timed checkpoint in stats only when this
		 * occurs without an external request, but we set the CAUSE_TIME flag
		 * bit even if there is also an external request.
		 */
		now = (pg_time_t) time(NULL);
		elapsed_secs = now - last_checkpoint_time;
		if (elapsed_secs >= CheckPointTimeout)
		{
			if (!do_checkpoint)
				chkpt_or_rstpt_timed = true;
			do_checkpoint = true;
			flags |= CHECKPOINT_CAUSE_TIME;
		}

		/*
		 * Do a checkpoint if requested.
		 */
		if (do_checkpoint)
		{
			bool		ckpt_performed = false;
			bool		do_restartpoint;

			/* Check if we should perform a checkpoint or a restartpoint. */
			do_restartpoint = RecoveryInProgress();

			/*
			 * Atomically fetch the request flags to figure out what kind of a
			 * checkpoint we should perform, and increase the started-counter
			 * to acknowledge that we've started a new checkpoint.
			 */
			SpinLockAcquire(&CheckpointerShmem->ckpt_lck);
			flags |= CheckpointerShmem->ckpt_flags;
			CheckpointerShmem->ckpt_flags = 0;
			CheckpointerShmem->ckpt_started++;
			SpinLockRelease(&CheckpointerShmem->ckpt_lck);

			ConditionVariableBroadcast(&CheckpointerShmem->start_cv);

			/*
			 * The end-of-recovery checkpoint is a real checkpoint that's
			 * performed while we're still in recovery.
			 */
			if (flags & CHECKPOINT_END_OF_RECOVERY)
				do_restartpoint = false;

			// ... (L429-L462 생략: timed/requested 통계와 "too frequently" 경고)

			/*
			 * Initialize checkpointer-private variables used during
			 * checkpoint.
			 */
			ckpt_active = true;
			if (do_restartpoint)
				ckpt_start_recptr = GetXLogReplayRecPtr(NULL);
			else
				ckpt_start_recptr = GetInsertRecPtr();
			ckpt_start_time = now;
			ckpt_cached_elapsed = 0;

			/*
			 * Do the checkpoint.
			 */
			if (!do_restartpoint)
				ckpt_performed = CreateCheckPoint(flags);
			else
				ckpt_performed = CreateRestartPoint(flags);

			/*
			 * After any checkpoint, free all smgr objects.  Otherwise we
			 * would never do so for dropped relations, as the checkpointer
			 * does not process shared invalidation messages or call
			 * AtEOXact_SMgr().
			 */
			smgrdestroyall();

			/*
			 * Indicate checkpoint completion to any waiting backends.
			 */
			SpinLockAcquire(&CheckpointerShmem->ckpt_lck);
			CheckpointerShmem->ckpt_done = CheckpointerShmem->ckpt_started;
			SpinLockRelease(&CheckpointerShmem->ckpt_lck);

			ConditionVariableBroadcast(&CheckpointerShmem->done_cv);

			if (!do_restartpoint)
			{
				/*
				 * Note we record the checkpoint start time not end time as
				 * last_checkpoint_time.  This is so that time-driven
				 * checkpoints happen at a predictable spacing.
				 */
				last_checkpoint_time = now;

				if (ckpt_performed)
					PendingCheckpointerStats.num_performed++;
			}
			else
			{
				if (ckpt_performed)
				{
					/*
					 * The same as for checkpoint. Please see the
					 * corresponding comment.
					 */
					last_checkpoint_time = now;

					PendingCheckpointerStats.restartpoints_performed++;
				}
				else
				{
					/*
					 * We were not able to perform the restartpoint
					 * (checkpoints throw an ERROR in case of error).  Most
					 * likely because we have not received any new checkpoint
					 * WAL records since the last restartpoint. Try again in
					 * 15 s.
					 */
					last_checkpoint_time = now - CheckPointTimeout + 15;
				}
			}

			ckpt_active = false;

			/*
			 * We may have received an interrupt during the checkpoint and the
			 * latch might have been reset (e.g. in CheckpointWriteDelay).
			 */
			ProcessCheckpointerInterrupts();
			if (ShutdownXLOGPending || ShutdownRequestPending)
				break;
		}

		/* Check for archive_timeout and switch xlog files if necessary. */
		CheckArchiveTimeout();

		/* Report pending statistics to the cumulative stats system */
		pgstat_report_checkpointer();
		pgstat_report_wal(true);

		/*
		 * If any checkpoint flags have been set, redo the loop to handle the
		 * checkpoint without sleeping.
		 */
		if (((volatile CheckpointerShmemStruct *) CheckpointerShmem)->ckpt_flags)
			continue;

		/*
		 * Sleep until we are signaled or it's time for another checkpoint or
		 * xlog file switch.
		 */
		now = (pg_time_t) time(NULL);
		elapsed_secs = now - last_checkpoint_time;
		if (elapsed_secs >= CheckPointTimeout)
			continue;			/* no sleep for us ... */
		cur_timeout = CheckPointTimeout - elapsed_secs;
		if (XLogArchiveTimeout > 0 && !RecoveryInProgress())
		{
			elapsed_secs = now - last_xlog_switch_time;
			if (elapsed_secs >= XLogArchiveTimeout)
				continue;		/* no sleep for us ... */
			cur_timeout = Min(cur_timeout, XLogArchiveTimeout - elapsed_secs);
		}

		(void) WaitLatch(MyLatch,
						 WL_LATCH_SET | WL_TIMEOUT | WL_EXIT_ON_PM_DEATH,
						 cur_timeout * 1000L /* convert to ms */ ,
						 WAIT_EVENT_CHECKPOINTER_MAIN);
	}

	// ... (L586-L635 생략: shutdown 체크포인트(ShutdownXLOG)와 종료 대기 루프)
}
```

## 동작 흐름

```text
 루프 한 바퀴 (L349-L584)

 L360  ResetLatch
 L365  AbsorbSyncRequests             backend 가 보낸 fsync 요청을 내 해시 테이블로 옮긴다
 L367  설정 reload, shutdown 요청 확인 -> 있으면 루프 탈출
 L376  ckpt_flags != 0 ?              누가 RequestCheckpoint 를 불렀다
         yes -> do_checkpoint
 L390  now - last_checkpoint_time >= CheckPointTimeout ?
         yes -> do_checkpoint, flags |= CHECKPOINT_CAUSE_TIME
 L401  do_checkpoint 면
 L407    do_restartpoint = RecoveryInProgress()
 L414-L418  spinlock 안에서 flags |= ckpt_flags, ckpt_flags = 0, ckpt_started++
 L420    start_cv 브로드캐스트        "네 요청이 시작됐다"
 L426    END_OF_RECOVERY 면 복구 중이라도 진짜 체크포인트
 L469-L474  ckpt_start_recptr, ckpt_start_time 기록   CheckpointWriteDelay 의 기준점
 L480    CreateCheckPoint(flags)  또는  L482 CreateRestartPoint(flags)
 L490    smgrdestroyall
 L495-L499  ckpt_done = ckpt_started, done_cv 브로드캐스트   "끝났다"
 L508    last_checkpoint_time = now   끝난 시각이 아니라 시작 시각
 L560  그새 플래그가 또 섰으면 자지 않고 다시
 L571  cur_timeout = CheckPointTimeout - elapsed (archive_timeout 이 더 짧으면 그것)
 L580  WaitLatch(cur_timeout 초)      RequestCheckpoint 의 SetLatch 가 깨운다
```

`last_checkpoint_time` 을 시작 시각으로 잡는 이유는 주석 L503-L506 에 있다. 시간 기반 체크포인트 간격을 일정하게 하려는 것이다. 기본값 300초로 그리면 이렇다.

```text
 시간 (초) ->

 0          270    300          570    600
 |==========|------|============|------|-----
 체크포인트 1        체크포인트 2
 시작                시작

 ===  BufferSync 가 쓰기를 퍼뜨리는 구간. 0.9 * 300 = 270 초 안에 끝내도록 [07] 이 속도를 맞춘다

 last_checkpoint_time = 0 -> 다음 기상 300 -> last_checkpoint_time = 300 -> 다음 600
 쓰기가 270 초에 끝났든 120 초에 끝났든 다음 시작은 300 이다
```

중간에 `max_wal_size` 요청이 들어오면 ckpt_flags 가 서서 L376 에서 바로 시작하고, `last_checkpoint_time` 도 그 시작 시각으로 옮겨진다. restartpoint 를 만들지 못했으면(새 체크포인트 레코드를 아직 못 받음) 15초 뒤 다시 시도하도록 시각을 당겨 둔다(L534).

```text
 요청한 backend 와의 약속 (머리 주석 L72-L95, 카운터 셋)

 시각  누가          하는 일
 t1    backend       old_failed, old_started 를 읽고 ckpt_flags 를 OR 한다   (L1037-L1039)
 t2    backend       SetLatch(checkpointer)                                    (L1070)
 t3    backend       start_cv 에서 ckpt_started != old_started 까지 잔다       (L1090-L1101)
 t4    checkpointer  L376 플래그 발견, L417 ckpt_started++, start_cv 브로드캐스트
 t5    backend       깨어나 new_started 를 기억, done_cv 에서 잔다             (L1108-L1122)
 t6    checkpointer  CreateCheckPoint ...
 t7    checkpointer  L496 ckpt_done = ckpt_started, done_cv 브로드캐스트
 t8    backend       ckpt_done - new_started >= 0 이면 깨어남
                     ckpt_failed != old_failed 면 ERROR "checkpoint request failed"

 실패하면 sigsetjmp 블록이 ckpt_failed++ 하고 ckpt_done 을 맞춘다 (L292-L302)
```

## 결과가 쓰이는 곳

```text
 ckpt_started, ckpt_done, ckpt_failed
      --> [02] RequestCheckpoint 의 CHECKPOINT_WAIT 대기 (checkpointer.c L1088-L1128)
 ckpt_start_recptr, ckpt_start_time
      --> [07] IsCheckpointOnSchedule 이 진행률을 비교하는 기준 (L887, L900)
 last_checkpoint_time
      --> 다음 시간 기반 체크포인트의 기상 시각
```

## 다루지 않는 것

시그널 처리(`SIGINT` = shutdown 체크포인트 요청, `SIGUSR2` = 종료), 에러 뒤 1초 대기(L322), `CheckArchiveTimeout` 의 `archive_timeout` 세그먼트 전환, `pgstat_report_checkpointer` 통계, shutdown 경로의 `ShutdownXLOG` 는 요약만 했다.
