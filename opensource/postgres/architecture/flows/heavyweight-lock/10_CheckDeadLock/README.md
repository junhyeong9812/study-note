# CheckDeadLock

상위: [heavyweight lock](../README.md)

**`deadlock_timeout` 이 지나도록 잠들어 있던 backend 가 교착인지 검사한다.** 잠금 파티션 16 개를 모두 잡아 잠금 세계를 멈춘 뒤, 자기에게서 출발하는 대기 그래프(waits-for graph)를 따라가 자기에게 돌아오는 순환을 찾는다. 순환이 대기 큐 순서 때문에 생긴 것(soft)뿐이면 큐를 재배치해 풀고, 이미 쥔 잠금 때문에 생긴 순환(hard)이면 자기 요청을 취소해 자기 트랜잭션이 ERROR 를 받게 한다. 검사는 [09] `ProcSleep` 루프 안에서, 시그널 핸들러가 아닌 일반 흐름에서 돈다.

## 위치

`storage` / `lmgr` / `proc.c` L1819-L1898 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1819-L1898))

## 실제 코드

`storage` / `lmgr` / `proc.c` L1810-L1898 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1810-L1898))

```c
// lmgr/proc.c L1810-L1898
/*
 * CheckDeadLock
 *
 * We only get to this routine, if DEADLOCK_TIMEOUT fired while waiting for a
 * lock to be released by some other process.  Check if there's a deadlock; if
 * not, just return.  (But signal ProcSleep to log a message, if
 * log_lock_waits is true.)  If we have a real deadlock, remove ourselves from
 * the lock's wait queue and signal an error to ProcSleep.
 */
static void
CheckDeadLock(void)
{
	int			i;

	/*
	 * Acquire exclusive lock on the entire shared lock data structures. Must
	 * grab LWLocks in partition-number order to avoid LWLock deadlock.
	 *
	 * Note that the deadlock check interrupt had better not be enabled
	 * anywhere that this process itself holds lock partition locks, else this
	 * will wait forever.  Also note that LWLockAcquire creates a critical
	 * section, so that this routine cannot be interrupted by cancel/die
	 * interrupts.
	 */
	for (i = 0; i < NUM_LOCK_PARTITIONS; i++)
		LWLockAcquire(LockHashPartitionLockByIndex(i), LW_EXCLUSIVE);

	/*
	 * Check to see if we've been awoken by anyone in the interim.
	 *
	 * If we have, we can return and resume our transaction -- happy day.
	 * Before we are awoken the process releasing the lock grants it to us so
	 * we know that we don't have to wait anymore.
	 *
	 * We check by looking to see if we've been unlinked from the wait queue.
	 * This is safe because we hold the lock partition lock.
	 */
	if (MyProc->links.prev == NULL ||
		MyProc->links.next == NULL)
		goto check_done;

#ifdef LOCK_DEBUG
	if (Debug_deadlocks)
		DumpAllLocks();
#endif

	/* Run the deadlock check, and set deadlock_state for use by ProcSleep */
	deadlock_state = DeadLockCheck(MyProc);

	if (deadlock_state == DS_HARD_DEADLOCK)
	{
		/*
		 * Oops.  We have a deadlock.
		 *
		 * Get this process out of wait state. (Note: we could do this more
		 * efficiently by relying on lockAwaited, but use this coding to
		 * preserve the flexibility to kill some other transaction than the
		 * one detecting the deadlock.)
		 *
		 * RemoveFromWaitQueue sets MyProc->waitStatus to
		 * PROC_WAIT_STATUS_ERROR, so ProcSleep will report an error after we
		 * return from the signal handler.
		 */
		Assert(MyProc->waitLock != NULL);
		RemoveFromWaitQueue(MyProc, LockTagHashCode(&(MyProc->waitLock->tag)));

		/*
		 * We're done here.  Transaction abort caused by the error that
		 * ProcSleep will raise will cause any other locks we hold to be
		 * released, thus allowing other processes to wake up; we don't need
		 * to do that here.  NOTE: an exception is that releasing locks we
		 * hold doesn't consider the possibility of waiters that were blocked
		 * behind us on the lock we just failed to get, and might now be
		 * wakable because we're not in front of them anymore.  However,
		 * RemoveFromWaitQueue took care of waking up any such processes.
		 */
	}

	/*
	 * And release locks.  We do this in reverse order for two reasons: (1)
	 * Anyone else who needs more than one of the locks will be trying to lock
	 * them in increasing order; we don't want to release the other process
	 * until it can get all the locks it needs. (2) This avoids O(N^2)
	 * behavior inside LWLockRelease.
	 */
check_done:
	for (i = NUM_LOCK_PARTITIONS; --i >= 0;)
		LWLockRelease(LockHashPartitionLockByIndex(i));
}
```

검사기 본체다. 순환을 풀 큐 순서를 찾으면 적용하고 깨울 수 있는 대기자를 깨운다.

`storage` / `lmgr` / `deadlock.c` L204-L282 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/deadlock.c#L204-L282))

```c
// deadlock.c L204-L282
/*
 * DeadLockCheck -- Checks for deadlocks for a given process
 *
 * This code looks for deadlocks involving the given process.  If any
 * are found, it tries to rearrange lock wait queues to resolve the
 * deadlock.  If resolution is impossible, return DS_HARD_DEADLOCK ---
 * the caller is then expected to abort the given proc's transaction.
 *
 * Caller must already have locked all partitions of the lock tables.
 *
 * On failure, deadlock details are recorded in deadlockDetails[] for
 * subsequent printing by DeadLockReport().  That activity is separate
 * because (a) we don't want to do it while holding all those LWLocks,
 * and (b) we are typically invoked inside a signal handler.
 */
DeadLockState
DeadLockCheck(PGPROC *proc)
{
	/* Initialize to "no constraints" */
	nCurConstraints = 0;
	nPossibleConstraints = 0;
	nWaitOrders = 0;

	/* Initialize to not blocked by an autovacuum worker */
	blocking_autovacuum_proc = NULL;

	/* Search for deadlocks and possible fixes */
	if (DeadLockCheckRecurse(proc))
	{
		/*
		 * Call FindLockCycle one more time, to record the correct
		 * deadlockDetails[] for the basic state with no rearrangements.
		 */
		int			nSoftEdges;

		TRACE_POSTGRESQL_DEADLOCK_FOUND();

		nWaitOrders = 0;
		if (!FindLockCycle(proc, possibleConstraints, &nSoftEdges))
			elog(FATAL, "deadlock seems to have disappeared");

		return DS_HARD_DEADLOCK;	/* cannot find a non-deadlocked state */
	}

	/* Apply any needed rearrangements of wait queues */
	for (int i = 0; i < nWaitOrders; i++)
	{
		LOCK	   *lock = waitOrders[i].lock;
		PGPROC	  **procs = waitOrders[i].procs;
		int			nProcs = waitOrders[i].nProcs;
		dclist_head *waitQueue = &lock->waitProcs;

		Assert(nProcs == dclist_count(waitQueue));

#ifdef DEBUG_DEADLOCK
		PrintLockQueue(lock, "DeadLockCheck:");
#endif

		/* Reset the queue and re-add procs in the desired order */
		dclist_init(waitQueue);
		for (int j = 0; j < nProcs; j++)
			dclist_push_tail(waitQueue, &procs[j]->links);

#ifdef DEBUG_DEADLOCK
		PrintLockQueue(lock, "rearranged to:");
#endif

		/* See if any waiters for the lock can be woken up now */
		ProcLockWakeup(GetLocksMethodTable(lock), lock);
	}

	/* Return code tells caller if we had to escape a deadlock or not */
	if (nWaitOrders > 0)
		return DS_SOFT_DEADLOCK;
	else if (blocking_autovacuum_proc != NULL)
		return DS_BLOCKED_BY_AUTOVACUUM;
	else
		return DS_NO_DEADLOCK;
}
```

soft 간선 하나씩을 "뒤집기 제약"으로 더해 보며 순환 없는 배치를 찾는 재귀다.

`storage` / `lmgr` / `deadlock.c` L300-L358 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/deadlock.c#L300-L358))

```c
// deadlock.c L300-L358
/*
 * DeadLockCheckRecurse -- recursively search for valid orderings
 *
 * curConstraints[] holds the current set of constraints being considered
 * by an outer level of recursion.  Add to this each possible solution
 * constraint for any cycle detected at this level.
 *
 * Returns true if no solution exists.  Returns false if a deadlock-free
 * state is attainable, in which case waitOrders[] shows the required
 * rearrangements of lock wait queues (if any).
 */
static bool
DeadLockCheckRecurse(PGPROC *proc)
{
	int			nEdges;
	int			oldPossibleConstraints;
	bool		savedList;
	int			i;

	nEdges = TestConfiguration(proc);
	if (nEdges < 0)
		return true;			/* hard deadlock --- no solution */
	if (nEdges == 0)
		return false;			/* good configuration found */
	if (nCurConstraints >= maxCurConstraints)
		return true;			/* out of room for active constraints? */
	oldPossibleConstraints = nPossibleConstraints;
	if (nPossibleConstraints + nEdges + MaxBackends <= maxPossibleConstraints)
	{
		/* We can save the edge list in possibleConstraints[] */
		nPossibleConstraints += nEdges;
		savedList = true;
	}
	else
	{
		/* Not room; will need to regenerate the edges on-the-fly */
		savedList = false;
	}

	/*
	 * Try each available soft edge as an addition to the configuration.
	 */
	for (i = 0; i < nEdges; i++)
	{
		if (!savedList && i > 0)
		{
			/* Regenerate the list of possible added constraints */
			if (nEdges != TestConfiguration(proc))
				elog(FATAL, "inconsistent results during deadlock check");
		}
		curConstraints[nCurConstraints] =
			possibleConstraints[oldPossibleConstraints + i];
		nCurConstraints++;
		if (!DeadLockCheckRecurse(proc))
			return false;		/* found a valid solution! */
		/* give up on that added constraint, try again */
		nCurConstraints--;
	}
	nPossibleConstraints = oldPossibleConstraints;
```

hard 간선을 찾는 부분이다. 내가 기다리는 LOCK 의 PROCLOCK 중 내 요청과 충돌하는 모드를 쥔 proc 으로 간선을 잇는다.

`storage` / `lmgr` / `deadlock.c` L535-L628 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/deadlock.c#L535-L628))

```c
// deadlock.c L535-L628
static bool
FindLockCycleRecurseMember(PGPROC *checkProc,
						   PGPROC *checkProcLeader,
						   int depth,
						   EDGE *softEdges, /* output argument */
						   int *nSoftEdges) /* output argument */
{
	PGPROC	   *proc;
	LOCK	   *lock = checkProc->waitLock;
	dlist_iter	proclock_iter;
	LockMethod	lockMethodTable;
	int			conflictMask;
	int			i;
	int			numLockModes,
				lm;

	/*
	 * The relation extension lock can never participate in actual deadlock
	 * cycle.  See Assert in LockAcquireExtended.  So, there is no advantage
	 * in checking wait edges from it.
	 */
	if (LOCK_LOCKTAG(*lock) == LOCKTAG_RELATION_EXTEND)
		return false;

	lockMethodTable = GetLocksMethodTable(lock);
	numLockModes = lockMethodTable->numLockModes;
	conflictMask = lockMethodTable->conflictTab[checkProc->waitLockMode];

	/*
	 * Scan for procs that already hold conflicting locks.  These are "hard"
	 * edges in the waits-for graph.
	 */
	dlist_foreach(proclock_iter, &lock->procLocks)
	{
		PROCLOCK   *proclock = dlist_container(PROCLOCK, lockLink, proclock_iter.cur);
		PGPROC	   *leader;

		proc = proclock->tag.myProc;
		leader = proc->lockGroupLeader == NULL ? proc : proc->lockGroupLeader;

		/* A proc never blocks itself or any other lock group member */
		if (leader != checkProcLeader)
		{
			for (lm = 1; lm <= numLockModes; lm++)
			{
				if ((proclock->holdMask & LOCKBIT_ON(lm)) &&
					(conflictMask & LOCKBIT_ON(lm)))
				{
					/* This proc hard-blocks checkProc */
					if (FindLockCycleRecurse(proc, depth + 1,
											 softEdges, nSoftEdges))
					{
						/* fill deadlockDetails[] */
						DEADLOCK_INFO *info = &deadlockDetails[depth];

						info->locktag = lock->tag;
						info->lockmode = checkProc->waitLockMode;
						info->pid = checkProc->pid;

						return true;
					}

					// ... (L597-L618 생략: autovacuum 이 직접 막고 있으면 기억해 두라는 설명 주석)
					if (checkProc == MyProc &&
						proc->statusFlags & PROC_IS_AUTOVACUUM)
						blocking_autovacuum_proc = proc;

					/* We're done looking at this proclock */
					break;
				}
			}
		}
	}
```

## 동작 흐름

```text
 CheckDeadLock (proc.c)
 L1834  파티션 LWLock 0..15 를 차례로 EXCLUSIVE  (번호 순서로 잡아 LWLock 끼리의 교착을 피한다)
 L1847  내가 이미 큐에서 빠졌다 (그사이 누가 승인했다) -> check_done
 L1857  deadlock_state = DeadLockCheck(MyProc)
 L1859  DS_HARD_DEADLOCK 이면
 L1874    RemoveFromWaitQueue(MyProc)    requested-- , waitStatus = ERROR, 뒤 대기자 깨우기
 L1896  파티션 LWLock 15..0 역순 해제

 DeadLockCheck (deadlock.c)
 L223   제약 0 개에서 시작
 L231   DeadLockCheckRecurse(proc) 가 true (해법 없음)
 L242     FindLockCycle 을 한 번 더 돌려 오류 메시지용 경로를 남긴다
 L245     DS_HARD_DEADLOCK
 L249   해법이 큐 재배치를 요구하면 (nWaitOrders > 0)
 L263     그 LOCK 의 waitProcs 를 새 순서로 다시 세우고
 L272     ProcLockWakeup                  이제 승인 가능한 대기자를 깨운다
 L276   DS_SOFT_DEADLOCK / DS_BLOCKED_BY_AUTOVACUUM / DS_NO_DEADLOCK
```

대기 그래프의 간선은 두 종류다(storage/lmgr/README L428-L434). 이미 쥔 잠금 때문에 기다리면 hard, 같은 큐에서 앞에 선 충돌 요청 때문에 기다리면 soft 다. soft 간선은 큐 순서를 바꾸면 방향이 뒤집히므로 아무도 죽이지 않고 풀 수 있다.

```text
 간선 A -> B  "A 가 B 를 기다린다"  (A 는 LOCK L 을 waitLockMode m 으로 기다리는 중)

 hard  B 의 PROCLOCK(L).holdMask 에 conflictTab[m] 과 겹치는 비트가 있다   deadlock.c L567-L628
 soft  B 가 L 의 waitProcs 에서 A 보다 앞이고 B 의 요청이 m 과 충돌한다   deadlock.c L630-L769
       (B 가 hard 로도 막고 있으면 hard 로 친다)

 순환 판정 (FindLockCycleRecurse, deadlock.c L456)
   출발점(나)으로 돌아오면           교착
   나를 거치지 않는 순환에 닿으면     "교착 아님" 으로 본다 (그 순환의 당사자가 검사한다)
```

가장 흔한 hard 교착은 두 트랜잭션이 서로 상대가 쥔 대상을 엇갈린 순서로 요청하는 경우다. 먼저 잠든 쪽의 타이머가 먼저 울리므로, 대개 먼저 기다리기 시작한 쪽이 취소된다.

```text
 A: LOCK TABLE t1 IN ACCESS EXCLUSIVE MODE    B: LOCK TABLE t2 IN ACCESS EXCLUSIVE MODE
 A: SELECT * FROM t2   (AS 요청)              B: SELECT * FROM t1   (AS 요청)

 시각     일어나는 일
 0ms      A: t2 의 AS 가 B 의 AX 와 충돌. A.heldLocks(t2) = {} 라 즉시 교착은 아니다 -> 대기
 100ms    B: t1 의 AS 가 A 의 AX 와 충돌. B.heldLocks(t1) = {} -> 대기
 1000ms   A 의 타이머 -> A: CheckDeadLock
            A --hard(t2, B 가 AX)--> B --hard(t1, A 가 AX)--> A   출발점으로 돌아옴
            DS_HARD_DEADLOCK, RemoveFromWaitQueue(A)
          A: ProcSleep 이 ERROR 반환 -> DeadLockReport -> "deadlock detected"
          A: abort -> LockReleaseAll 이 t1 의 AX 를 푼다 -> B 를 깨운다
 1100ms   B 의 타이머는 이미 꺼졌다 (B 가 OK 로 깨어나 L1697 에서 해제)

 B 가 같은 대상에 이미 약한 잠금을 쥔 채 올리려 했다면
   [08] JoinWaitQueue 가 큐에 넣는 순간 잡는다 (deadlock_timeout 을 기다리지 않는다)
```

```text
 검사 중 잠금 세계가 멈추는 범위

 L1834-L1835  파티션 LWLock 16 개 전부  -> 그동안 모든 backend 의 공유 해시 경로가 막힌다
 fast-path    fpInfoLock 은 잡지 않는다 -> 약한 테이블 잠금의 fast-path 는 계속 돈다
              교착에 낄 수 있는 잠금은 [04] 가 이미 공유 해시로 옮겨 두었다 (lock.c L295-L297)
 그래서 매번 검사하지 않고 deadlock_timeout 뒤에만 한다
```

## 결과가 쓰이는 곳

```text
 deadlock_state (proc.c 의 정적 변수)
      --> ProcSleep 이 autovacuum 취소(DS_BLOCKED_BY_AUTOVACUUM)와 log_lock_waits 문장을 고른다

 MyProc->waitStatus = ERROR (RemoveFromWaitQueue, lock.c L2044)
      --> ProcSleep 루프가 끝나고 LockAcquireExtended L1235 의 DeadLockReport
      --> DeadLockReport 가 pg_stat_database.deadlocks 를 올리고 ERROR (deadlock.c L1131, L1133)

 재배치된 waitProcs
      --> 이후 ProcLockWakeup 이 새 순서대로 깨운다
```

## 다루지 않는 것

큐 재배치의 세부(`TestConfiguration` L378, `ExpandConstraints` L790, `TopoSort` L862), lock group 구성원을 한 노드로 묶는 처리(`FindLockCycleRecurseMember` 의 groupLeader 분기), 오류 메시지의 경로 출력(`DeadLockReport` L1075)은 요약만 했다.
