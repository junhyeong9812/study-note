# ProcSleep

상위: [heavyweight lock](../README.md)

**대기 큐에 들어간 backend 가 잠금을 받을 때까지 잠들어 있는 루프다.** 들어가기 전에 `deadlock_timeout` 타이머(와 설정했다면 `lock_timeout`)를 걸고, latch 위에서 잠들었다가 깨어날 때마다 `MyProc->waitStatus` 를 읽는다. 잠금을 주는 일은 깨우는 쪽이 이미 끝내 두므로, 이 함수는 상태가 WAITING 에서 바뀌기를 기다릴 뿐 공유 자료를 고치지 않는다. 타이머가 울린 뒤 첫 깨어남에서만 [10] `CheckDeadLock` 을 부른다. 호출은 `lock.c` 의 얇은 감싸개 `WaitOnLock` 을 거친다.

## 위치

`storage` / `lmgr` / `proc.c` L1341-L1728 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1341-L1728))

## 실제 코드

감싸개다. 오류 정리 장치(`awaitedLock`)를 걸고, 프로세스 제목에 "waiting" 을 붙인 채 `ProcSleep` 을 부른다.

`storage` / `lmgr` / `lock.c` L1930-L2001 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1930-L2001))

```c
// lock.c L1930-L2001
static ProcWaitStatus
WaitOnLock(LOCALLOCK *locallock, ResourceOwner owner)
{
	ProcWaitStatus result;

	TRACE_POSTGRESQL_LOCK_WAIT_START(locallock->tag.lock.locktag_field1,
									 locallock->tag.lock.locktag_field2,
									 locallock->tag.lock.locktag_field3,
									 locallock->tag.lock.locktag_field4,
									 locallock->tag.lock.locktag_type,
									 locallock->tag.mode);

	/* adjust the process title to indicate that it's waiting */
	set_ps_display_suffix("waiting");

	/*
	 * Record the fact that we are waiting for a lock, so that
	 * LockErrorCleanup will clean up if cancel/die happens.
	 */
	awaitedLock = locallock;
	awaitedOwner = owner;

	/*
	 * NOTE: Think not to put any shared-state cleanup after the call to
	 * ProcSleep, in either the normal or failure path.  The lock state must
	 * be fully set by the lock grantor, or by CheckDeadLock if we give up
	 * waiting for the lock.  This is necessary because of the possibility
	 * that a cancel/die interrupt will interrupt ProcSleep after someone else
	 * grants us the lock, but before we've noticed it. Hence, after granting,
	 * the locktable state must fully reflect the fact that we own the lock;
	 * we can't do additional work on return.
	 *
	 * We can and do use a PG_TRY block to try to clean up after failure, but
	 * this still has a major limitation: elog(FATAL) can occur while waiting
	 * (eg, a "die" interrupt), and then control won't come back here. So all
	 * cleanup of essential state should happen in LockErrorCleanup, not here.
	 * We can use PG_TRY to clear the "waiting" status flags, since doing that
	 * is unimportant if the process exits.
	 */
	PG_TRY();
	{
		result = ProcSleep(locallock);
	}
	PG_CATCH();
	{
		/* In this path, awaitedLock remains set until LockErrorCleanup */

		/* reset ps display to remove the suffix */
		set_ps_display_remove_suffix();

		/* and propagate the error */
		PG_RE_THROW();
	}
	PG_END_TRY();

	/*
	 * We no longer want LockErrorCleanup to do anything.
	 */
	awaitedLock = NULL;

	/* reset ps display to remove the suffix */
	set_ps_display_remove_suffix();

	TRACE_POSTGRESQL_LOCK_WAIT_DONE(locallock->tag.lock.locktag_field1,
									locallock->tag.lock.locktag_field2,
									locallock->tag.lock.locktag_field3,
									locallock->tag.lock.locktag_field4,
									locallock->tag.lock.locktag_type,
									locallock->tag.mode);

	return result;
}
```

본체다. hot standby 쪽 대기, autovacuum 취소, `log_lock_waits` 로그는 줄였다.

`storage` / `lmgr` / `proc.c` L1341-L1728 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1341-L1728))

```c
// lmgr/proc.c L1341-L1728
ProcWaitStatus
ProcSleep(LOCALLOCK *locallock)
{
	LOCKMODE	lockmode = locallock->tag.mode;
	LOCK	   *lock = locallock->lock;
	uint32		hashcode = locallock->hashcode;
	LWLock	   *partitionLock = LockHashPartitionLock(hashcode);
	TimestampTz standbyWaitStart = 0;
	bool		allow_autovacuum_cancel = true;
	bool		logged_recovery_conflict = false;
	ProcWaitStatus myWaitStatus;

	/* The caller must've armed the on-error cleanup mechanism */
	Assert(GetAwaitedLock() == locallock);
	Assert(!LWLockHeldByMe(partitionLock));

	/*
	 * Now that we will successfully clean up after an ereport, it's safe to
	 * check to see if there's a buffer pin deadlock against the Startup
	 * process.  Of course, that's only necessary if we're doing Hot Standby
	 * and are not the Startup process ourselves.
	 */
	if (RecoveryInProgress() && !InRecovery)
		CheckRecoveryConflictDeadlock();

	/* Reset deadlock_state before enabling the timeout handler */
	deadlock_state = DS_NOT_YET_CHECKED;
	got_deadlock_timeout = false;

	/*
	 * Set timer so we can wake up after awhile and check for a deadlock. If a
	 * deadlock is detected, the handler sets MyProc->waitStatus =
	 * PROC_WAIT_STATUS_ERROR, allowing us to know that we must report failure
	 * rather than success.
	 *
	 * By delaying the check until we've waited for a bit, we can avoid
	 * running the rather expensive deadlock-check code in most cases.
	 *
	 * If LockTimeout is set, also enable the timeout for that.  We can save a
	 * few cycles by enabling both timeout sources in one call.
	 *
	 * If InHotStandby we set lock waits slightly later for clarity with other
	 * code.
	 */
	if (!InHotStandby)
	{
		if (LockTimeout > 0)
		{
			EnableTimeoutParams timeouts[2];

			timeouts[0].id = DEADLOCK_TIMEOUT;
			timeouts[0].type = TMPARAM_AFTER;
			timeouts[0].delay_ms = DeadlockTimeout;
			timeouts[1].id = LOCK_TIMEOUT;
			timeouts[1].type = TMPARAM_AFTER;
			timeouts[1].delay_ms = LockTimeout;
			enable_timeouts(timeouts, 2);
		}
		else
			enable_timeout_after(DEADLOCK_TIMEOUT, DeadlockTimeout);

		/*
		 * Use the current time obtained for the deadlock timeout timer as
		 * waitStart (i.e., the time when this process started waiting for the
		 * lock). Since getting the current time newly can cause overhead, we
		 * reuse the already-obtained time to avoid that overhead.
		 *
		 * Note that waitStart is updated without holding the lock table's
		 * partition lock, to avoid the overhead by additional lock
		 * acquisition. This can cause "waitstart" in pg_locks to become NULL
		 * for a very short period of time after the wait started even though
		 * "granted" is false. This is OK in practice because we can assume
		 * that users are likely to look at "waitstart" when waiting for the
		 * lock for a long time.
		 */
		pg_atomic_write_u64(&MyProc->waitStart,
							get_timeout_start_time(DEADLOCK_TIMEOUT));
	}
	else if (log_recovery_conflict_waits)
	{
		/*
		 * Set the wait start timestamp if logging is enabled and in hot
		 * standby.
		 */
		standbyWaitStart = GetCurrentTimestamp();
	}

	/*
	 * If somebody wakes us between LWLockRelease and WaitLatch, the latch
	 * will not wait. But a set latch does not necessarily mean that the lock
	 * is free now, as there are many other sources for latch sets than
	 * somebody releasing the lock.
	 *
	 * We process interrupts whenever the latch has been set, so cancel/die
	 * interrupts are processed quickly. This means we must not mind losing
	 * control to a cancel/die interrupt here.  We don't, because we have no
	 * shared-state-change work to do after being granted the lock (the
	 * grantor did it all).  We do have to worry about canceling the deadlock
	 * timeout and updating the locallock table, but if we lose control to an
	 * error, LockErrorCleanup will fix that up.
	 */
	do
	{
		if (InHotStandby)
		// ... (L1445-L1483 생략: hot standby 에서 startup 프로세스와의 잠금 충돌을 푸는 대기)
		else
		{
			(void) WaitLatch(MyLatch, WL_LATCH_SET | WL_EXIT_ON_PM_DEATH, 0,
							 PG_WAIT_LOCK | locallock->tag.lock.locktag_type);
			ResetLatch(MyLatch);
			/* check for deadlocks first, as that's probably log-worthy */
			if (got_deadlock_timeout)
			{
				CheckDeadLock();
				got_deadlock_timeout = false;
			}
			CHECK_FOR_INTERRUPTS();
		}

		/*
		 * waitStatus could change from PROC_WAIT_STATUS_WAITING to something
		 * else asynchronously.  Read it just once per loop to prevent
		 * surprising behavior (such as missing log messages).
		 */
		myWaitStatus = *((volatile ProcWaitStatus *) &MyProc->waitStatus);

		/*
		 * If we are not deadlocked, but are waiting on an autovacuum-induced
		 * task, send a signal to interrupt it.
		 */
		if (deadlock_state == DS_BLOCKED_BY_AUTOVACUUM && allow_autovacuum_cancel)
		// ... (L1510-L1586 생략: autovacuum 이 막고 있으면 SIGINT 로 취소하는 부분)

		/*
		 * If awoken after the deadlock check interrupt has run, and
		 * log_lock_waits is on, then report about the wait.
		 */
		if (log_lock_waits && deadlock_state != DS_NOT_YET_CHECKED)
		// ... (L1593-L1688 생략: log_lock_waits 가 켜졌을 때 대기 경과를 로그로 남기는 부분)
	} while (myWaitStatus == PROC_WAIT_STATUS_WAITING);

	/*
	 * Disable the timers, if they are still running.  As in LockErrorCleanup,
	 * we must preserve the LOCK_TIMEOUT indicator flag: if a lock timeout has
	 * already caused QueryCancelPending to become set, we want the cancel to
	 * be reported as a lock timeout, not a user cancel.
	 */
	if (!InHotStandby)
	{
		if (LockTimeout > 0)
		{
			DisableTimeoutParams timeouts[2];

			timeouts[0].id = DEADLOCK_TIMEOUT;
			timeouts[0].keep_indicator = false;
			timeouts[1].id = LOCK_TIMEOUT;
			timeouts[1].keep_indicator = true;
			disable_timeouts(timeouts, 2);
		}
		else
			disable_timeout(DEADLOCK_TIMEOUT, false);
	}

	/*
	 * Emit the log message if recovery conflict on lock was resolved but the
	 * startup process waited longer than deadlock_timeout for it.
	 */
	if (InHotStandby && logged_recovery_conflict)
		LogRecoveryConflict(PROCSIG_RECOVERY_CONFLICT_LOCK,
							standbyWaitStart, GetCurrentTimestamp(),
							NULL, false);

	/*
	 * We don't have to do anything else, because the awaker did all the
	 * necessary updates of the lock table and MyProc. (The caller is
	 * responsible for updating the local lock table.)
	 */
	return myWaitStatus;
}
```

타이머가 울리면 시그널 핸들러 안에서 이것만 한다. 실제 검사는 루프가 깨어난 뒤 한다.

`storage` / `lmgr` / `proc.c` L1900-L1922 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1900-L1922))

```c
// lmgr/proc.c L1900-L1922
/*
 * CheckDeadLockAlert - Handle the expiry of deadlock_timeout.
 *
 * NB: Runs inside a signal handler, be careful.
 */
void
CheckDeadLockAlert(void)
{
	int			save_errno = errno;

	got_deadlock_timeout = true;

	/*
	 * Have to set the latch again, even if handle_sig_alarm already did. Back
	 * then got_deadlock_timeout wasn't yet set... It's unlikely that this
	 * ever would be a problem, but setting a set latch again is cheap.
	 *
	 * Note that, when this function runs inside procsignal_sigusr1_handler(),
	 * the handler function sets the latch again after the latch is set here.
	 */
	SetLatch(MyLatch);
	errno = save_errno;
}
```

## 동작 흐름

```text
 WaitOnLock (lock.c)
 L1935  TRACE LOCK_WAIT_START
 L1943  ps 제목에 " waiting"
 L1949  awaitedLock = locallock, awaitedOwner = owner    cancel/die 가 오면 LockErrorCleanup 이 쓴다
 L1971  ProcSleep(locallock)
 L1988  awaitedLock = NULL, ps 제목 원복

 ProcSleep (proc.c)
 L1363  hot standby 면 startup 과의 버퍼 핀 교착부터 확인
 L1367  deadlock_state = DS_NOT_YET_CHECKED, got_deadlock_timeout = false
 L1385  hot standby 가 아니면
 L1387    lock_timeout > 0  -> DEADLOCK_TIMEOUT 과 LOCK_TIMEOUT 을 한 번에
 L1400    아니면            -> DEADLOCK_TIMEOUT 만 (DeadlockTimeout ms 뒤)
 L1416    waitStart = 타이머 시작 시각   (pg_locks.waitstart)

 L1442  do
 L1486    WaitLatch(MyLatch)     잠든다. 깨우는 이: ProcWakeup 의 SetLatch, 타이머, 시그널
 L1488    ResetLatch
 L1490    got_deadlock_timeout 이면 [10] CheckDeadLock, 플래그 내림
 L1495    CHECK_FOR_INTERRUPTS   lock_timeout, cancel 이면 여기서 ERROR 로 빠져나간다
 L1503    myWaitStatus = MyProc->waitStatus   (한 바퀴에 한 번만 읽는다)
 L1509    DS_BLOCKED_BY_AUTOVACUUM 이면 그 autovacuum 에 SIGINT (한 번만)
 L1592    log_lock_waits 이고 검사가 한 번 돌았으면 로그
 L1689  while (myWaitStatus == WAITING)

 L1697  타이머 끄기 (LOCK_TIMEOUT 표시는 남겨 cancel 사유를 lock timeout 으로 보고)
 L1727  myWaitStatus 반환     OK 또는 ERROR (교착)
```

기다리는 동안 이 backend 를 깨울 수 있는 것은 셋이고, 어느 것이 깨웠는지는 latch 가 알려주지 않는다. 그래서 깨어날 때마다 `waitStatus` 를 다시 읽는다(L1428-L1441 주석).

```text
 기본 설정 (deadlock_timeout = 1000ms, lock_timeout = 0) 에서 B 가 A 의 잠금을 기다릴 때

 시각      일어나는 일                                    B 의 waitStatus   deadlock_state
 0ms       B: JoinWaitQueue, 파티션 LWLock 해제            WAITING
           B: enable_timeout_after(DEADLOCK_TIMEOUT, 1000)
           B: WaitLatch 로 잠든다
 1000ms    타이머 -> CheckDeadLockAlert                    WAITING
             got_deadlock_timeout = true, SetLatch
           B: 깨어나 CheckDeadLock
             순환 없음                                     WAITING          DS_NO_DEADLOCK
           B: 다시 WaitLatch
 2500ms    A: 커밋 -> LockReleaseAll -> ProcLockWakeup
             GrantLock(B 몫), ProcWakeup                   OK
             B 를 큐에서 빼고 waitStatus = OK, SetLatch
           B: 깨어나 myWaitStatus = OK, 루프 끝
           B: 타이머 해제, OK 반환 -> GrantLockLocal

 A 가 300ms 에 풀었다면 교착 검사는 한 번도 돌지 않는다
 deadlock_timeout 은 "교착 검사 비용을 낼 만큼 오래 기다렸나"의 문턱이다 (L1376-L1377 주석)
```

```text
 루프를 벗어나는 길

 waitStatus = OK      잠금을 푼 backend 의 ProcLockWakeup -> ProcWakeup     (proc.c L1757)
                      교착 검사기가 큐를 재배치한 뒤 ProcLockWakeup        (deadlock.c L272)
 waitStatus = ERROR   CheckDeadLock 이 hard deadlock 을 보고 RemoveFromWaitQueue (lock.c L2044)
 ERROR 로 튀어나감    CHECK_FOR_INTERRUPTS 에서 lock_timeout, statement_timeout, cancel, die
                      -> 트랜잭션 abort 경로의 LockErrorCleanup 이 큐에서 빼고 (proc.c L852)
                         그 사이 이미 승인됐으면 GrantAwaitedLock 으로 지역 기록만 맞춘다 (L863)
```

## 결과가 쓰이는 곳

```text
 반환값
      --> LockAcquireExtended L1228 이 ERROR 면 DeadLockReport, OK 면 GrantLockLocal

 MyProc->waitStart
      --> pg_locks.waitstart, log_lock_waits 의 경과 시간

 deadlock_state
      --> 다음 바퀴의 autovacuum 취소와 로그 문장을 고른다
```

## 다루지 않는 것

hot standby 의 잠금 충돌 해결(`ResolveRecoveryConflictWithLock`, `storage/ipc/standby.c`), autovacuum 취소의 조건(wraparound 방지 vacuum 은 취소하지 않는다, L1531-L1536), `log_lock_waits` 로그 문장, 타이머 장치 자체(`utils/misc/timeout.c`)는 다루지 않았다.
