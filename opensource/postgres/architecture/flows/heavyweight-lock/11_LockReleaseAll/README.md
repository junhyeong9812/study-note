# LockReleaseAll

상위: [heavyweight lock](../README.md)

**트랜잭션이 끝날 때 이 backend 의 잠금을 한꺼번에 푼다.** 두 바퀴를 돈다. 첫 바퀴는 지역 해시(LOCALLOCK)를 돌며 fast-path 잠금은 슬롯 비트만 지우고, 공유 해시 잠금은 PROCLOCK 의 `releaseMask` 에 "풀 모드"를 적어 둔다. 둘째 바퀴는 파티션 16 개마다 내 PROCLOCK 목록을 돌며 적어 둔 모드를 `UnGrantLock` 하고, 빈 항목을 치우고, 기다리던 이가 있으면 `ProcLockWakeup` 으로 승인까지 해 준다. 커밋이면 세션 잠금은 남기고, abort 면 세션 잠금까지 푼다.

## 위치

`storage` / `lmgr` / `lock.c` L2266-L2542 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L2266-L2542))

## 실제 코드

트랜잭션 끝에서 부르는 자리다. `ResourceOwnerRelease` 의 `RESOURCE_RELEASE_LOCKS` 단계에서 최상위 owner 일 때 불린다(utils/resowner/resowner.c L767).

`storage` / `lmgr` / `proc.c` L874-L901 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L874-L901))

```c
// lmgr/proc.c L874-L901
/*
 * ProcReleaseLocks() -- release locks associated with current transaction
 *			at main transaction commit or abort
 *
 * At main transaction commit, we release standard locks except session locks.
 * At main transaction abort, we release all locks including session locks.
 *
 * Advisory locks are released only if they are transaction-level;
 * session-level holds remain, whether this is a commit or not.
 *
 * At subtransaction commit, we don't release any locks (so this func is not
 * needed at all); we will defer the releasing to the parent transaction.
 * At subtransaction abort, we release all locks held by the subtransaction;
 * this is implemented by retail releasing of the locks under control of
 * the ResourceOwner mechanism.
 */
void
ProcReleaseLocks(bool isCommit)
{
	if (!MyProc)
		return;
	/* If waiting, get off wait queue (should only be needed after error) */
	LockErrorCleanup();
	/* Release standard locks, including session-level if aborting */
	LockReleaseAll(DEFAULT_LOCKMETHOD, !isCommit);
	/* Release transaction-level advisory locks */
	LockReleaseAll(USER_LOCKMETHOD, false);
}
```

본체다.

`storage` / `lmgr` / `lock.c` L2266-L2542 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L2266-L2542))

```c
// lock.c L2266-L2542
/*
 * LockReleaseAll -- Release all locks of the specified lock method that
 *		are held by the current process.
 *
 * Well, not necessarily *all* locks.  The available behaviors are:
 *		allLocks == true: release all locks including session locks.
 *		allLocks == false: release all non-session locks.
 */
void
LockReleaseAll(LOCKMETHODID lockmethodid, bool allLocks)
{
	HASH_SEQ_STATUS status;
	LockMethod	lockMethodTable;
	int			i,
				numLockModes;
	LOCALLOCK  *locallock;
	LOCK	   *lock;
	int			partition;
	bool		have_fast_path_lwlock = false;

	if (lockmethodid <= 0 || lockmethodid >= lengthof(LockMethods))
		elog(ERROR, "unrecognized lock method: %d", lockmethodid);
	lockMethodTable = LockMethods[lockmethodid];

// ... (L2290-L2293 생략: LOCK_DEBUG 추적 출력)

	/*
	 * Get rid of our fast-path VXID lock, if appropriate.  Note that this is
	 * the only way that the lock we hold on our own VXID can ever get
	 * released: it is always and only released when a toplevel transaction
	 * ends.
	 */
	if (lockmethodid == DEFAULT_LOCKMETHOD)
		VirtualXactLockTableCleanup();

	numLockModes = lockMethodTable->numLockModes;

	/*
	 * First we run through the locallock table and get rid of unwanted
	 * entries, then we scan the process's proclocks and get rid of those. We
	 * do this separately because we may have multiple locallock entries
	 * pointing to the same proclock, and we daren't end up with any dangling
	 * pointers.  Fast-path locks are cleaned up during the locallock table
	 * scan, though.
	 */
	hash_seq_init(&status, LockMethodLocalHash);

	while ((locallock = (LOCALLOCK *) hash_seq_search(&status)) != NULL)
	{
		/*
		 * If the LOCALLOCK entry is unused, something must've gone wrong
		 * while trying to acquire this lock.  Just forget the local entry.
		 */
		if (locallock->nLocks == 0)
		{
			RemoveLocalLock(locallock);
			continue;
		}

		/* Ignore items that are not of the lockmethod to be removed */
		if (LOCALLOCK_LOCKMETHOD(*locallock) != lockmethodid)
			continue;

		/*
		 * If we are asked to release all locks, we can just zap the entry.
		 * Otherwise, must scan to see if there are session locks. We assume
		 * there is at most one lockOwners entry for session locks.
		 */
		if (!allLocks)
		{
			LOCALLOCKOWNER *lockOwners = locallock->lockOwners;

			/* If session lock is above array position 0, move it down to 0 */
			for (i = 0; i < locallock->numLockOwners; i++)
			{
				if (lockOwners[i].owner == NULL)
					lockOwners[0] = lockOwners[i];
				else
					ResourceOwnerForgetLock(lockOwners[i].owner, locallock);
			}

			if (locallock->numLockOwners > 0 &&
				lockOwners[0].owner == NULL &&
				lockOwners[0].nLocks > 0)
			{
				/* Fix the locallock to show just the session locks */
				locallock->nLocks = lockOwners[0].nLocks;
				locallock->numLockOwners = 1;
				/* We aren't deleting this locallock, so done */
				continue;
			}
			else
				locallock->numLockOwners = 0;
		}

// ... (L2364-L2372 생략: assert 빌드에서 튜플 잠금이 남았는지 경고)

		/*
		 * If the lock or proclock pointers are NULL, this lock was taken via
		 * the relation fast-path (and is not known to have been transferred).
		 */
		if (locallock->proclock == NULL || locallock->lock == NULL)
		{
			LOCKMODE	lockmode = locallock->tag.mode;
			Oid			relid;

			/* Verify that a fast-path lock is what we've got. */
			if (!EligibleForRelationFastPath(&locallock->tag.lock, lockmode))
				elog(PANIC, "locallock table corrupted");

			/*
			 * If we don't currently hold the LWLock that protects our
			 * fast-path data structures, we must acquire it before attempting
			 * to release the lock via the fast-path.  We will continue to
			 * hold the LWLock until we're done scanning the locallock table,
			 * unless we hit a transferred fast-path lock.  (XXX is this
			 * really such a good idea?  There could be a lot of entries ...)
			 */
			if (!have_fast_path_lwlock)
			{
				LWLockAcquire(&MyProc->fpInfoLock, LW_EXCLUSIVE);
				have_fast_path_lwlock = true;
			}

			/* Attempt fast-path release. */
			relid = locallock->tag.lock.locktag_field2;
			if (FastPathUnGrantRelationLock(relid, lockmode))
			{
				RemoveLocalLock(locallock);
				continue;
			}

			/*
			 * Our lock, originally taken via the fast path, has been
			 * transferred to the main lock table.  That's going to require
			 * some extra work, so release our fast-path lock before starting.
			 */
			LWLockRelease(&MyProc->fpInfoLock);
			have_fast_path_lwlock = false;

			/*
			 * Now dump the lock.  We haven't got a pointer to the LOCK or
			 * PROCLOCK in this case, so we have to handle this a bit
			 * differently than a normal lock release.  Unfortunately, this
			 * requires an extra LWLock acquire-and-release cycle on the
			 * partitionLock, but hopefully it shouldn't happen often.
			 */
			LockRefindAndRelease(lockMethodTable, MyProc,
								 &locallock->tag.lock, lockmode, false);
			RemoveLocalLock(locallock);
			continue;
		}

		/* Mark the proclock to show we need to release this lockmode */
		if (locallock->nLocks > 0)
			locallock->proclock->releaseMask |= LOCKBIT_ON(locallock->tag.mode);

		/* And remove the locallock hashtable entry */
		RemoveLocalLock(locallock);
	}

	/* Done with the fast-path data structures */
	if (have_fast_path_lwlock)
		LWLockRelease(&MyProc->fpInfoLock);

	/*
	 * Now, scan each lock partition separately.
	 */
	for (partition = 0; partition < NUM_LOCK_PARTITIONS; partition++)
	{
		LWLock	   *partitionLock;
		dlist_head *procLocks = &MyProc->myProcLocks[partition];
		dlist_mutable_iter proclock_iter;

		partitionLock = LockHashPartitionLockByIndex(partition);

		/*
		 * If the proclock list for this partition is empty, we can skip
		 * acquiring the partition lock.  This optimization is trickier than
		 * it looks, because another backend could be in process of adding
		 * something to our proclock list due to promoting one of our
		 * fast-path locks.  However, any such lock must be one that we
		 * decided not to delete above, so it's okay to skip it again now;
		 * we'd just decide not to delete it again.  We must, however, be
		 * careful to re-fetch the list header once we've acquired the
		 * partition lock, to be sure we have a valid, up-to-date pointer.
		 * (There is probably no significant risk if pointer fetch/store is
		 * atomic, but we don't wish to assume that.)
		 *
		 * XXX This argument assumes that the locallock table correctly
		 * represents all of our fast-path locks.  While allLocks mode
		 * guarantees to clean up all of our normal locks regardless of the
		 * locallock situation, we lose that guarantee for fast-path locks.
		 * This is not ideal.
		 */
		if (dlist_is_empty(procLocks))
			continue;			/* needn't examine this partition */

		LWLockAcquire(partitionLock, LW_EXCLUSIVE);

		dlist_foreach_modify(proclock_iter, procLocks)
		{
			PROCLOCK   *proclock = dlist_container(PROCLOCK, procLink, proclock_iter.cur);
			bool		wakeupNeeded = false;

			Assert(proclock->tag.myProc == MyProc);

			lock = proclock->tag.myLock;

			/* Ignore items that are not of the lockmethod to be removed */
			if (LOCK_LOCKMETHOD(*lock) != lockmethodid)
				continue;

			/*
			 * In allLocks mode, force release of all locks even if locallock
			 * table had problems
			 */
			if (allLocks)
				proclock->releaseMask = proclock->holdMask;
			else
				Assert((proclock->releaseMask & ~proclock->holdMask) == 0);

			/*
			 * Ignore items that have nothing to be released, unless they have
			 * holdMask == 0 and are therefore recyclable
			 */
			if (proclock->releaseMask == 0 && proclock->holdMask != 0)
				continue;

			PROCLOCK_PRINT("LockReleaseAll", proclock);
			LOCK_PRINT("LockReleaseAll", lock, 0);
			Assert(lock->nRequested >= 0);
			Assert(lock->nGranted >= 0);
			Assert(lock->nGranted <= lock->nRequested);
			Assert((proclock->holdMask & ~lock->grantMask) == 0);

			/*
			 * Release the previously-marked lock modes
			 */
			for (i = 1; i <= numLockModes; i++)
			{
				if (proclock->releaseMask & LOCKBIT_ON(i))
					wakeupNeeded |= UnGrantLock(lock, i, proclock,
												lockMethodTable);
			}
			Assert((lock->nRequested >= 0) && (lock->nGranted >= 0));
			Assert(lock->nGranted <= lock->nRequested);
			LOCK_PRINT("LockReleaseAll: updated", lock, 0);

			proclock->releaseMask = 0;

			/* CleanUpLock will wake up waiters if needed. */
			CleanUpLock(lock, proclock,
						lockMethodTable,
						LockTagHashCode(&lock->tag),
						wakeupNeeded);
		}						/* loop over PROCLOCKs within this partition */

		LWLockRelease(partitionLock);
	}							/* loop over partitions */

// ... (L2538-L2541 생략: LOCK_DEBUG 추적 출력)
}
```

모드 하나를 내리는 짝이다. 내린 모드가 기다리는 요청과 충돌하던 모드였으면 깨울 필요가 있다고 알린다.

`storage` / `lmgr` / `lock.c` L1670-L1724 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1670-L1724))

```c
// lock.c L1670-L1724
/*
 * UnGrantLock -- opposite of GrantLock.
 *
 * Updates the lock and proclock data structures to show that the lock
 * is no longer held nor requested by the current holder.
 *
 * Returns true if there were any waiters waiting on the lock that
 * should now be woken up with ProcLockWakeup.
 */
static bool
UnGrantLock(LOCK *lock, LOCKMODE lockmode,
			PROCLOCK *proclock, LockMethod lockMethodTable)
{
	bool		wakeupNeeded = false;

	Assert((lock->nRequested > 0) && (lock->requested[lockmode] > 0));
	Assert((lock->nGranted > 0) && (lock->granted[lockmode] > 0));
	Assert(lock->nGranted <= lock->nRequested);

	/*
	 * fix the general lock stats
	 */
	lock->nRequested--;
	lock->requested[lockmode]--;
	lock->nGranted--;
	lock->granted[lockmode]--;

	if (lock->granted[lockmode] == 0)
	{
		/* change the conflict mask.  No more of this lock type. */
		lock->grantMask &= LOCKBIT_OFF(lockmode);
	}

	LOCK_PRINT("UnGrantLock: updated", lock, lockmode);

	/*
	 * We need only run ProcLockWakeup if the released lock conflicts with at
	 * least one of the lock types requested by waiter(s).  Otherwise whatever
	 * conflict made them wait must still exist.  NOTE: before MVCC, we could
	 * skip wakeup if lock->granted[lockmode] was still positive. But that's
	 * not true anymore, because the remaining granted locks might belong to
	 * some waiter, who could now be awakened because he doesn't conflict with
	 * his own locks.
	 */
	if (lockMethodTable->conflictTab[lockmode] & lock->waitMask)
		wakeupNeeded = true;

	/*
	 * Now fix the per-proclock state.
	 */
	proclock->holdMask &= LOCKBIT_OFF(lockmode);
	PROCLOCK_PRINT("UnGrantLock: updated", proclock);

	return wakeupNeeded;
}
```

빈 PROCLOCK, 빈 LOCK 을 해시에서 치우고, 남은 요청이 있으면 깨운다.

`storage` / `lmgr` / `lock.c` L1726-L1781 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1726-L1781))

```c
// lock.c L1726-L1781
/*
 * CleanUpLock -- clean up after releasing a lock.  We garbage-collect the
 * proclock and lock objects if possible, and call ProcLockWakeup if there
 * are remaining requests and the caller says it's OK.  (Normally, this
 * should be called after UnGrantLock, and wakeupNeeded is the result from
 * UnGrantLock.)
 *
 * The appropriate partition lock must be held at entry, and will be
 * held at exit.
 */
static void
CleanUpLock(LOCK *lock, PROCLOCK *proclock,
			LockMethod lockMethodTable, uint32 hashcode,
			bool wakeupNeeded)
{
	/*
	 * If this was my last hold on this lock, delete my entry in the proclock
	 * table.
	 */
	if (proclock->holdMask == 0)
	{
		uint32		proclock_hashcode;

		PROCLOCK_PRINT("CleanUpLock: deleting", proclock);
		dlist_delete(&proclock->lockLink);
		dlist_delete(&proclock->procLink);
		proclock_hashcode = ProcLockHashCode(&proclock->tag, hashcode);
		if (!hash_search_with_hash_value(LockMethodProcLockHash,
										 &(proclock->tag),
										 proclock_hashcode,
										 HASH_REMOVE,
										 NULL))
			elog(PANIC, "proclock table corrupted");
	}

	if (lock->nRequested == 0)
	{
		/*
		 * The caller just released the last lock, so garbage-collect the lock
		 * object.
		 */
		LOCK_PRINT("CleanUpLock: deleting", lock, 0);
		Assert(dlist_is_empty(&lock->procLocks));
		if (!hash_search_with_hash_value(LockMethodLockHash,
										 &(lock->tag),
										 hashcode,
										 HASH_REMOVE,
										 NULL))
			elog(PANIC, "lock table corrupted");
	}
	else if (wakeupNeeded)
	{
		/* There are waiters on this lock, so wake them up. */
		ProcLockWakeup(lockMethodTable, lock);
	}
}
```

깨우는 쪽이다. 큐를 앞에서부터 보며 앞 요청과도, 승인된 잠금과도 충돌하지 않는 대기자에게 그 자리에서 `GrantLock` 을 해 주고 latch 를 울린다.

`storage` / `lmgr` / `proc.c` L1764-L1808 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1764-L1808))

```c
// lmgr/proc.c L1764-L1808
/*
 * ProcLockWakeup -- routine for waking up processes when a lock is
 *		released (or a prior waiter is aborted).  Scan all waiters
 *		for lock, waken any that are no longer blocked.
 *
 * The appropriate lock partition lock must be held by caller.
 */
void
ProcLockWakeup(LockMethod lockMethodTable, LOCK *lock)
{
	dclist_head *waitQueue = &lock->waitProcs;
	LOCKMASK	aheadRequests = 0;
	dlist_mutable_iter miter;

	if (dclist_is_empty(waitQueue))
		return;

	dclist_foreach_modify(miter, waitQueue)
	{
		PGPROC	   *proc = dlist_container(PGPROC, links, miter.cur);
		LOCKMODE	lockmode = proc->waitLockMode;

		/*
		 * Waken if (a) doesn't conflict with requests of earlier waiters, and
		 * (b) doesn't conflict with already-held locks.
		 */
		if ((lockMethodTable->conflictTab[lockmode] & aheadRequests) == 0 &&
			!LockCheckConflicts(lockMethodTable, lockmode, lock,
								proc->waitProcLock))
		{
			/* OK to waken */
			GrantLock(lock, proc->waitProcLock, lockmode);
			/* removes proc from the lock's waiting process queue */
			ProcWakeup(proc, PROC_WAIT_STATUS_OK);
		}
		else
		{
			/*
			 * Lock conflicts: Don't wake, but remember requested mode for
			 * later checks.
			 */
			aheadRequests |= LOCKBIT_ON(lockmode);
		}
	}
}
```

## 동작 흐름

```text
 ProcReleaseLocks(isCommit)                          proc.c
 L896  LockErrorCleanup                              아직 큐에 있으면 빠진다 (오류 뒤에만 해당)
 L898  LockReleaseAll(DEFAULT_LOCKMETHOD, allLocks = !isCommit)
 L900  LockReleaseAll(USER_LOCKMETHOD, false)        트랜잭션 수준 advisory lock

 LockReleaseAll                                      lock.c
 L2302 VirtualXactLockTableCleanup                   내 VXID 잠금 (L2301 기본 잠금 방식일 때)

 첫 바퀴  LockMethodLocalHash 전체
 L2322   nLocks == 0           실패한 획득의 잔해 -> RemoveLocalLock
 L2337   !allLocks 이고 세션 잠금(owner NULL)이 있으면 그 몫만 남기고 continue
 L2378   lock == NULL           fast-path 로 잡았던 잠금
 L2397     fpInfoLock 을 (한 번만) 잡고
 L2403     FastPathUnGrantRelationLock 성공 -> RemoveLocalLock
 L2424     실패 (누가 공유 해시로 옮겼다) -> LockRefindAndRelease
 L2432   그 밖                  proclock->releaseMask |= bit(mode)
 L2435   RemoveLocalLock        strong count 를 쥐었으면 여기서 내린다 (L1489)

 둘째 바퀴  partition = 0..15
 L2472   내 myProcLocks[partition] 이 비었으면 LWLock 도 잡지 않는다
 L2475   LWLockAcquire(partitionLock)
 L2477   for 내 PROCLOCK
 L2494     allLocks 면 releaseMask = holdMask
 L2503     풀 것도 없고 쥔 것이 있으면 건너뜀
 L2516     releaseMask 의 모드마다 UnGrantLock -> wakeupNeeded |=
 L2529     CleanUpLock
             holdMask == 0     PROCLOCK 을 두 목록과 해시에서 지운다   L1745
             nRequested == 0   LOCK 도 해시에서 지운다                L1761
             아니고 wakeupNeeded  ProcLockWakeup                      L1779
 L2535   LWLockRelease
```

트랜잭션 끝은 행 잠금 대기를 풀어 주는 순간이기도 하다. 행 충돌로 기다리는 backend 는 상대 트랜잭션의 XID 잠금을 기다리고 있으므로, 그 XID 잠금이 여기서 풀리면서 깨어난다.

```text
 A 가 행을 UPDATE 한 채 커밋, B 는 같은 행을 UPDATE 하려다 A 의 XID 를 기다리는 중

 A 가 쥔 것
   LOCALLOCK (t, RX)          lock == NULL           fast-path 슬롯
   LOCALLOCK (xid_A, X)       lock = LOCK(xid_A)     XactLockTableInsert (lmgr.c L628)
 LOCK(xid_A)  grantMask = {7}  waitMask = {5}  granted[7]=1  requested[7]=1 [5]=1  waitProcs = [B]
   B 는 XactLockTableWait 의 ShareLock 을 기다린다 (lmgr.c L697)

 A: ProcReleaseLocks(isCommit = true) -> LockReleaseAll(DEFAULT, allLocks = false)
 첫 바퀴
   (t, RX)      FastPathUnGrantRelationLock -> 비트 지움, RemoveLocalLock
   (xid_A, X)   PROCLOCK(xid_A, A).releaseMask = {7}, RemoveLocalLock
 둘째 바퀴 (xid_A 의 파티션)
   UnGrantLock(7)
     nRequested 2 -> 1, granted[7] 1 -> 0, grantMask = {}
     conflictTab[7] 0x1fc & waitMask {5} != 0 -> wakeupNeeded
     PROCLOCK(xid_A, A).holdMask = {}
   CleanUpLock
     holdMask 0       -> PROCLOCK(xid_A, A) 삭제
     nRequested 1     -> LOCK 은 남기고 ProcLockWakeup
   ProcLockWakeup
     B: aheadRequests 0, LockCheckConflicts(5): grantMask {} -> 충돌 없음
     GrantLock(B 몫)  granted[5] = 1, waitMask = {} (granted == requested)
     ProcWakeup(B, OK)  큐에서 빼고 SetLatch
 B: ProcSleep 이 OK 로 끝나고, XactLockTableWait 가 곧바로 LockRelease 한 뒤 행을 다시 본다
```

```text
 깨울 때 큐를 보는 규칙 (ProcLockWakeup, proc.c L1781-L1806)

 waitProcs    [ P1(AX) ]  [ P2(AS) ]  [ P3(RX) ]      방금 모든 승인 잠금이 풀렸다고 할 때
 P1  aheadRequests {}       충돌 없음 -> 승인, aheadRequests 는 그대로 {}
 P2  conflictTab[1] {8} & aheadRequests {} = 0, LockCheckConflicts: P1 의 AX 와 충돌
     -> 깨우지 않고 aheadRequests |= {1}
 P3  conflictTab[3] {5,6,7,8} & {1} = 0, LockCheckConflicts: AX 와 충돌
     -> 깨우지 않고 aheadRequests |= {3}

 앞 요청과 충돌하는 뒤 대기자는 승인 잠금과 충돌하지 않아도 깨우지 않는다 (L1785-L1792)
 그래서 AX 대기자 뒤의 AS 가 새치기하지 못한다
```

## 결과가 쓰이는 곳

```text
 비워진 LOCALLOCK 해시, 지워진 LOCK / PROCLOCK
      --> 다음 트랜잭션이 같은 대상을 처음부터 다시 잡는다

 ProcLockWakeup 이 승인한 대기자
      --> [09] ProcSleep 이 OK 로 깨어나 LockAcquireExtended L1245 로 돌아간다

 내려간 strong count
      --> 같은 칸의 테이블들이 다시 fast-path 를 쓸 수 있다
```

## 다루지 않는 것

서브트랜잭션 단위 해제(`LockReleaseCurrentOwner` L2579, `LockReassignCurrentOwner` L2674), 잠금 하나를 푸는 `LockRelease`(L2070), 세션 잠금만 푸는 `LockReleaseSession`(L2549), 옮겨진 fast-path 잠금을 공유 해시에서 다시 찾는 `LockRefindAndRelease`(L3254)는 같은 재료를 쓰는 곁가지라 다루지 않았다.
