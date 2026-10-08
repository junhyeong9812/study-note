# CheckpointWriteDelay

상위: [체크포인트](../README.md)

**`BufferSync` 가 버퍼 하나를 처리할 때마다 불리고, 진행률이 일정보다 앞서 있으면 100ms 를 자는 함수다.** 일정은 둘이다. 다음 시간 기반 체크포인트까지 남은 시간과, 다음 WAL 기반 체크포인트까지 남은 WAL 양이다. 진행률에 `checkpoint_completion_target` 을 곱해 둘과 비교하므로, 기본값 0.9 면 쓰기가 다음 체크포인트 예정 시점의 90% 지점에서 끝나도록 퍼진다. `CHECKPOINT_IMMEDIATE` 이거나 뒤에 즉시 요청이 기다리고 있으면 자지 않는다.

## 위치

`src/backend/postmaster` / `checkpointer.c` L771-L831 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/checkpointer.c#L771-L831))

## 실제 코드

```c
// postmaster/checkpointer.c L771-L831
void
CheckpointWriteDelay(int flags, double progress)
{
	static int	absorb_counter = WRITES_PER_ABSORB;

	/* Do nothing if checkpoint is being executed by non-checkpointer process */
	if (!AmCheckpointerProcess())
		return;

	/*
	 * Perform the usual duties and take a nap, unless we're behind schedule,
	 * in which case we just try to catch up as quickly as possible.
	 */
	if (!(flags & CHECKPOINT_IMMEDIATE) &&
		!ShutdownXLOGPending &&
		!ShutdownRequestPending &&
		!ImmediateCheckpointRequested() &&
		IsCheckpointOnSchedule(progress))
	{
		if (ConfigReloadPending)
		{
			ConfigReloadPending = false;
			ProcessConfigFile(PGC_SIGHUP);
			/* update shmem copies of config variables */
			UpdateSharedMemoryConfig();
		}

		AbsorbSyncRequests();
		absorb_counter = WRITES_PER_ABSORB;

		CheckArchiveTimeout();

		/* Report interim statistics to the cumulative stats system */
		pgstat_report_checkpointer();

		/*
		 * This sleep used to be connected to bgwriter_delay, typically 200ms.
		 * That resulted in more frequent wakeups if not much work to do.
		 * Checkpointer and bgwriter are no longer related so take the Big
		 * Sleep.
		 */
		WaitLatch(MyLatch, WL_LATCH_SET | WL_EXIT_ON_PM_DEATH | WL_TIMEOUT,
				  100,
				  WAIT_EVENT_CHECKPOINT_WRITE_DELAY);
		ResetLatch(MyLatch);
	}
	else if (--absorb_counter <= 0)
	{
		/*
		 * Absorb pending fsync requests after each WRITES_PER_ABSORB write
		 * operations even when we don't sleep, to prevent overflow of the
		 * fsync request queue.
		 */
		AbsorbSyncRequests();
		absorb_counter = WRITES_PER_ABSORB;
	}

	/* Check for barrier events. */
	if (ProcSignalBarrierPending)
		ProcessProcSignalBarrier();
}
```

일정 판단은 이 함수가 한다. 앞서 계산한 "따라잡아야 할 값"을 캐시해 두고, 진행률이 그 값을 넘기 전에는 시간과 WAL 위치를 다시 읽지 않는다(주석 L854-L858).

`src/backend/postmaster` / `checkpointer.c` L841-L911 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/checkpointer.c#L841-L911))

```c
// postmaster/checkpointer.c L841-L911
static bool
IsCheckpointOnSchedule(double progress)
{
	XLogRecPtr	recptr;
	struct timeval now;
	double		elapsed_xlogs,
				elapsed_time;

	Assert(ckpt_active);

	/* Scale progress according to checkpoint_completion_target. */
	progress *= CheckPointCompletionTarget;

	/*
	 * Check against the cached value first. Only do the more expensive
	 * calculations once we reach the target previously calculated. Since
	 * neither time or WAL insert pointer moves backwards, a freshly
	 * calculated value can only be greater than or equal to the cached value.
	 */
	if (progress < ckpt_cached_elapsed)
		return false;

	/*
	 * Check progress against WAL segments written and CheckPointSegments.
	 *
	 * We compare the current WAL insert location against the location
	 * computed before calling CreateCheckPoint. The code in XLogInsert that
	 * actually triggers a checkpoint when CheckPointSegments is exceeded
	 * compares against RedoRecPtr, so this is not completely accurate.
	 * However, it's good enough for our purposes, we're only calculating an
	 * estimate anyway.
	 *
	 * During recovery, we compare last replayed WAL record's location with
	 * the location computed before calling CreateRestartPoint. That maintains
	 * the same pacing as we have during checkpoints in normal operation, but
	 * we might exceed max_wal_size by a fair amount. That's because there can
	 * be a large gap between a checkpoint's redo-pointer and the checkpoint
	 * record itself, and we only start the restartpoint after we've seen the
	 * checkpoint record. (The gap is typically up to CheckPointSegments *
	 * checkpoint_completion_target where checkpoint_completion_target is the
	 * value that was in effect when the WAL was generated).
	 */
	if (RecoveryInProgress())
		recptr = GetXLogReplayRecPtr(NULL);
	else
		recptr = GetInsertRecPtr();
	elapsed_xlogs = (((double) (recptr - ckpt_start_recptr)) /
					 wal_segment_size) / CheckPointSegments;

	if (progress < elapsed_xlogs)
	{
		ckpt_cached_elapsed = elapsed_xlogs;
		return false;
	}

	/*
	 * Check progress against time elapsed and checkpoint_timeout.
	 */
	gettimeofday(&now, NULL);
	elapsed_time = ((double) ((pg_time_t) now.tv_sec - ckpt_start_time) +
					now.tv_usec / 1000000.0) / CheckPointTimeout;

	if (progress < elapsed_time)
	{
		ckpt_cached_elapsed = elapsed_time;
		return false;
	}

	/* It looks like we're on schedule. */
	return true;
}
```

## 동작 흐름

```text
 CheckpointWriteDelay(flags, progress = num_processed / num_to_scan)

 L777  checkpointer 가 아니면 return       (단일 사용자 모드의 직접 체크포인트)
 L784  자도 되는가? 다섯 조건이 모두 참이어야 한다
         flags 에 IMMEDIATE 없음
         shutdown 요청 없음 (둘)
         뒤에 IMMEDIATE 요청 없음            ImmediateCheckpointRequested L753
         IsCheckpointOnSchedule(progress)
 L790    yes: 설정 reload, AbsorbSyncRequests, CheckArchiveTimeout, 통계
 L812         WaitLatch 100ms                  RequestCheckpoint 의 SetLatch 가 깨울 수 있다
 L817    no:  1000번(WRITES_PER_ABSORB)에 한 번 AbsorbSyncRequests 만
 L829  ProcSignalBarrier 처리
```

```text
 IsCheckpointOnSchedule(progress)

 L852  progress *= CheckPointCompletionTarget            0.9 를 곱한다
 L860  progress < ckpt_cached_elapsed 면 false            지난번에 본 뒤처짐을 아직 못 따라잡음
 L887  elapsed_xlogs = (지금 WAL 위치 - ckpt_start_recptr) / 세그먼트 크기 / CheckPointSegments
 L890  progress < elapsed_xlogs 면 캐시하고 false        WAL 일정보다 뒤처짐
 L900  elapsed_time  = (지금 - ckpt_start_time) / checkpoint_timeout
 L903  progress < elapsed_time  면 캐시하고 false        시간 일정보다 뒤처짐
 L910  true                                              둘 다 앞서 있다 -> 자도 된다
```

기본값(`checkpoint_timeout` 300초, 0.9, `CheckPointSegments` 33)에 버퍼 10000개짜리 체크포인트로 숫자를 넣으면 이렇다.

```text
 processed  progress  x0.9    elapsed  elapsed_time  WAL     elapsed_xlogs  판정
 5000       0.50      0.45    100 s    0.333         10 seg  0.303          둘 다 앞섬 -> 100ms 잔다
 5000       0.50      0.45    160 s    0.533         10 seg  0.303          시간에 뒤처짐 -> 안 잔다, cached = 0.533
 5500       0.55      0.495   -        -             -       -              0.495 < cached -> L860 에서 바로 false
 5926       0.5926    0.5333  -        -             -       -              cached 를 넘었다 -> L887 부터 다시 계산

 progress 1.0 은 0.9 로 줄어든다. 그래서 elapsed_time <= 0.9, 즉 270초 안에 끝나는 속도로 쓴다
 WAL 이 빨리 쌓이면 elapsed_xlogs 쪽이 먼저 앞서 가서 시간과 무관하게 속도를 올린다
```

복구 중(restartpoint)에는 WAL 위치 대신 마지막으로 재생한 위치를 쓴다(L883-L884). 주석 L873-L881 은 그 때문에 standby 에서 `max_wal_size` 를 꽤 넘길 수 있다고 적고 있다.

## 결과가 쓰이는 곳

```text
 100ms 잠
      --> [05] BufferSync 의 쓰기 속도가 일정에 맞춰진다
 AbsorbSyncRequests
      --> backend 가 보낸 fsync 요청이 pendingOps 로 옮겨져 큐가 넘치지 않는다 (주석 L820-L822)
 ckpt_cached_elapsed
      --> 다음 호출의 L860 빠른 판정
```

## 다루지 않는 것

`AbsorbSyncRequests` 의 큐 처리, `CheckArchiveTimeout`, `UpdateSharedMemoryConfig` 는 요약만 했다.
