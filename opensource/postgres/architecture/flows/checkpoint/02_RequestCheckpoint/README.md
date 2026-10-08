# RequestCheckpoint

상위: [체크포인트](../README.md)

**체크포인트를 원하는 쪽이 부르는 함수이고, 공유 메모리의 `ckpt_flags` 에 요청 플래그를 OR 한 뒤 checkpointer 의 latch 를 세우는 것이 전부다.** `CHECKPOINT_WAIT` 가 있으면 시작과 완료를 condition variable 로 기다린다. `max_wal_size` 트리거는 이 함수의 호출자인 `XLogWrite` 쪽에서 판단하므로 그 계산(`XLogCheckpointNeeded`, `CalculateCheckpointSegments`)도 여기서 같이 본다.

## 위치

`src/backend/postmaster` / `checkpointer.c` L1002-L1130 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/checkpointer.c#L1002-L1130))

## 실제 코드

```c
// postmaster/checkpointer.c L1002-L1130
void
RequestCheckpoint(int flags)
{
	int			ntries;
	int			old_failed,
				old_started;

	/*
	 * If in a standalone backend, just do it ourselves.
	 */
	if (!IsPostmasterEnvironment)
	{
		/*
		 * There's no point in doing slow checkpoints in a standalone backend,
		 * because there's no other backends the checkpoint could disrupt.
		 */
		CreateCheckPoint(flags | CHECKPOINT_IMMEDIATE);

		/* Free all smgr objects, as CheckpointerMain() normally would. */
		smgrdestroyall();

		return;
	}

	/*
	 * Atomically set the request flags, and take a snapshot of the counters.
	 * When we see ckpt_started > old_started, we know the flags we set here
	 * have been seen by checkpointer.
	 *
	 * Note that we OR the flags with any existing flags, to avoid overriding
	 * a "stronger" request by another backend.  The flag senses must be
	 * chosen to make this work!
	 */
	SpinLockAcquire(&CheckpointerShmem->ckpt_lck);

	old_failed = CheckpointerShmem->ckpt_failed;
	old_started = CheckpointerShmem->ckpt_started;
	CheckpointerShmem->ckpt_flags |= (flags | CHECKPOINT_REQUESTED);

	SpinLockRelease(&CheckpointerShmem->ckpt_lck);

	/*
	 * Set checkpointer's latch to request checkpoint.  It's possible that the
	 * checkpointer hasn't started yet, so we will retry a few times if
	 * needed.  (Actually, more than a few times, since on slow or overloaded
	 * buildfarm machines, it's been observed that the checkpointer can take
	 * several seconds to start.)  However, if not told to wait for the
	 * checkpoint to occur, we consider failure to set the latch to be
	 * nonfatal and merely LOG it.  The checkpointer should see the request
	 * when it does start, with or without the SetLatch().
	 */
#define MAX_SIGNAL_TRIES 600	/* max wait 60.0 sec */
	for (ntries = 0;; ntries++)
	{
		volatile PROC_HDR *procglobal = ProcGlobal;
		ProcNumber	checkpointerProc = procglobal->checkpointerProc;

		if (checkpointerProc == INVALID_PROC_NUMBER)
		{
			if (ntries >= MAX_SIGNAL_TRIES || !(flags & CHECKPOINT_WAIT))
			{
				elog((flags & CHECKPOINT_WAIT) ? ERROR : LOG,
					 "could not notify checkpoint: checkpointer is not running");
				break;
			}
		}
		else
		{
			SetLatch(&GetPGProcByNumber(checkpointerProc)->procLatch);
			/* notified successfully */
			break;
		}

		CHECK_FOR_INTERRUPTS();
		pg_usleep(100000L);		/* wait 0.1 sec, then retry */
	}

	/*
	 * If requested, wait for completion.  We detect completion according to
	 * the algorithm given above.
	 */
	if (flags & CHECKPOINT_WAIT)
	{
		int			new_started,
					new_failed;

		/* Wait for a new checkpoint to start. */
		ConditionVariablePrepareToSleep(&CheckpointerShmem->start_cv);
		for (;;)
		{
			SpinLockAcquire(&CheckpointerShmem->ckpt_lck);
			new_started = CheckpointerShmem->ckpt_started;
			SpinLockRelease(&CheckpointerShmem->ckpt_lck);

			if (new_started != old_started)
				break;

			ConditionVariableSleep(&CheckpointerShmem->start_cv,
								   WAIT_EVENT_CHECKPOINT_START);
		}
		ConditionVariableCancelSleep();

		/*
		 * We are waiting for ckpt_done >= new_started, in a modulo sense.
		 */
		ConditionVariablePrepareToSleep(&CheckpointerShmem->done_cv);
		for (;;)
		{
			int			new_done;

			SpinLockAcquire(&CheckpointerShmem->ckpt_lck);
			new_done = CheckpointerShmem->ckpt_done;
			new_failed = CheckpointerShmem->ckpt_failed;
			SpinLockRelease(&CheckpointerShmem->ckpt_lck);

			if (new_done - new_started >= 0)
				break;

			ConditionVariableSleep(&CheckpointerShmem->done_cv,
								   WAIT_EVENT_CHECKPOINT_DONE);
		}
		ConditionVariableCancelSleep();

		if (new_failed != old_failed)
			ereport(ERROR,
					(errmsg("checkpoint request failed"),
					 errhint("Consult recent messages in the server log for details.")));
	}
}
```

`max_wal_size` 트리거는 backend 가 WAL 세그먼트 하나를 다 쓰고 fsync 한 직후에 판단한다. 로컬 `RedoRecPtr` 가 낡았을 수 있어 한 번 갱신하고 다시 본다.

`src/backend/access/transam` / `xlog.c` L2492-L2504 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2492-L2504))

```c
// transam/xlog.c L2492-L2504
				/*
				 * Request a checkpoint if we've consumed too much xlog since
				 * the last one.  For speed, we first check using the local
				 * copy of RedoRecPtr, which might be out of date; if it looks
				 * like a checkpoint is needed, forcibly update RedoRecPtr and
				 * recheck.
				 */
				if (IsUnderPostmaster && XLogCheckpointNeeded(openLogSegNo))
				{
					(void) GetRedoRecPtr();
					if (XLogCheckpointNeeded(openLogSegNo))
						RequestCheckpoint(CHECKPOINT_CAUSE_XLOG);
				}
```

판단식은 "REDO 지점이 든 세그먼트에서 `CheckPointSegments - 1` 개 이상 지났는가"다.

`src/backend/access/transam` / `xlog.c` L2279-L2289 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2279-L2289))

```c
// transam/xlog.c L2279-L2289
bool
XLogCheckpointNeeded(XLogSegNo new_segno)
{
	XLogSegNo	old_segno;

	XLByteToSeg(RedoRecPtr, old_segno, wal_segment_size);

	if (new_segno >= old_segno + (uint64) (CheckPointSegments - 1))
		return true;
	return false;
}
```

`CheckPointSegments` 는 `max_wal_size` 와 `checkpoint_completion_target` 이 바뀔 때마다 다시 계산된다(assign 훅 L2200-L2211).

`src/backend/access/transam` / `xlog.c` L2170-L2197 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2170-L2197))

```c
// transam/xlog.c L2170-L2197
static void
CalculateCheckpointSegments(void)
{
	double		target;

	/*-------
	 * Calculate the distance at which to trigger a checkpoint, to avoid
	 * exceeding max_wal_size_mb. This is based on two assumptions:
	 *
	 * a) we keep WAL for only one checkpoint cycle (prior to PG11 we kept
	 *    WAL for two checkpoint cycles to allow us to recover from the
	 *    secondary checkpoint if the first checkpoint failed, though we
	 *    only did this on the primary anyway, not on standby. Keeping just
	 *    one checkpoint simplifies processing and reduces disk space in
	 *    many smaller databases.)
	 * b) during checkpoint, we consume checkpoint_completion_target *
	 *	  number of segments consumed between checkpoints.
	 *-------
	 */
	target = (double) ConvertToXSegs(max_wal_size_mb, wal_segment_size) /
		(1.0 + CheckPointCompletionTarget);

	/* round down */
	CheckPointSegments = (int) target;

	if (CheckPointSegments < 1)
		CheckPointSegments = 1;
}
```

## 동작 흐름

```text
 RequestCheckpoint(flags)

 L1012  postmaster 밑이 아니면 (단일 사용자 모드)
          CreateCheckPoint(flags | IMMEDIATE) 를 직접 부르고 끝
 L1035-L1041  spinlock 안에서
          old_failed, old_started 기억
          ckpt_flags |= flags | CHECKPOINT_REQUESTED     OR 이라 강한 요청이 약한 요청에 덮이지 않는다
 L1054-L1077  checkpointer 의 procLatch 를 SetLatch
          아직 안 떴으면 0.1초 간격으로 최대 600번 (60초) 다시 시도
          WAIT 가 아니면 한 번 실패로 LOG 만 남기고 포기
 L1083  CHECKPOINT_WAIT 면
          start_cv 에서 ckpt_started 가 바뀔 때까지
          done_cv  에서 ckpt_done - new_started >= 0 까지   (카운터가 돌아도 맞도록 뺄셈 비교)
          ckpt_failed 가 바뀌었으면 ERROR
```

요청 플래그는 비트 OR 로 합쳐진다. 여러 backend 가 동시에 요청해도 checkpointer 는 한 번에 모두를 만족시키는 체크포인트 하나를 돈다.

```text
 플래그 (include/access/xlog.h L139-L151)

 value   name                  효과
 0x0001  IS_SHUTDOWN           shutdown 체크포인트. REDO 레코드 없이 SHUTDOWN 레코드 하나
 0x0002  END_OF_RECOVERY       복구 끝. shutdown 처럼 다룬다
 0x0004  IMMEDIATE             CheckpointWriteDelay 가 자지 않는다
 0x0008  FORCE                 WAL 활동이 없어도 한다
 0x0010  FLUSH_ALL             unlogged 버퍼까지 쓴다
 0x0020  WAIT                  끝날 때까지 기다린다 (RequestCheckpoint 만 본다)
 0x0040  REQUESTED             요청이 있었다는 표시
 0x0080  CAUSE_XLOG            WAL 양 때문. "too frequently" 경고를 켠다
 0x0100  CAUSE_TIME            시간 때문 (checkpointer 가 스스로 붙인다)

 예: 복구 중이 아닐 때의 CHECKPOINT 명령(IMMEDIATE|WAIT|FORCE = 0x2C, tcop/utility.c L955) 과 XLogWrite(CAUSE_XLOG = 0x80) 이 겹치면
     ckpt_flags = 0x2C | 0x80 | 0x40 = 0xEC  -> 지연 없이, 활동이 없어도, WAL 원인으로 기록
```

`max_wal_size` 트리거를 세그먼트 번호로 그리면 이렇다. 기본값으로 `CheckPointSegments` = 33 이다.

```text
 CalculateCheckpointSegments (L2189-L2196)
   ConvertToXSegs(1024 MB, 16 MB) = 64
   target = 64 / (1.0 + 0.9) = 33.68 -> 33

 주석 L2179-L2186 의 두 가정
   a) WAL 은 체크포인트 한 주기 분만 남긴다
   b) 체크포인트 도중에 한 주기의 0.9 만큼이 더 쌓인다
   그래서 (1 + 0.9) 주기가 max_wal_size 안에 들어가도록 나눈다

 XLogCheckpointNeeded (L2284-L2287), RedoRecPtr = 0/1C000060 이면 old_segno = 0x1C

   new_segno   >= 0x1C + (33 - 1) = 0x3C ?   결과
   0x30        false                         계속 쓴다
   0x3B        false                         계속 쓴다
   0x3C        true                          RequestCheckpoint(CAUSE_XLOG)
```

트리거는 세그먼트를 다 채운 순간에만 검사된다. 그래서 요청은 세그먼트 경계에서만 나가고, 그 사이에는 `CheckpointWriteDelay` 쪽의 `IsCheckpointOnSchedule` 이 같은 `CheckPointSegments` 로 속도만 맞춘다.

## 결과가 쓰이는 곳

```text
 ckpt_flags
      --> [01] CheckpointerMain L376, L415 가 읽고 0 으로 지운다
      --> [07] ImmediateCheckpointRequested 가 IMMEDIATE 비트만 본다 (L753)
 SetLatch
      --> [01] 의 WaitLatch (L580) 가 깨어난다
 CheckPointSegments
      --> XLogCheckpointNeeded (xlog.c L2286), [07] IsCheckpointOnSchedule (checkpointer.c L888)
```

## 다루지 않는 것

`CHECKPOINT` 명령의 권한 검사(`pg_checkpoint` 역할), 단일 사용자 모드의 직접 실행, restartpoint 요청(standby 의 `XLogPageRead` L3354-L3362 도 같은 `XLogCheckpointNeeded` 로 판단한다), `ForwardSyncRequest` 의 fsync 요청 큐는 요약만 했다.
