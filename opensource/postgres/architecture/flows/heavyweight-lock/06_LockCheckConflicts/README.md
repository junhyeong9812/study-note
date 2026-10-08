# LockCheckConflicts

상위: [heavyweight lock](../README.md)

**요청 모드가 이미 승인된 잠금과 충돌하는지 판정한다.** 비트마스크 AND 한 번으로 대부분 끝나고, 걸렸을 때만 "내가 쥔 몫"과 "같은 lock group 이 쥔 몫"을 빼고 다시 센다. 한 proc 의 잠금끼리는 충돌하지 않는다는 규칙이 이 뺄셈이다. 기다리는 요청과의 충돌은 여기서 보지 않고 호출자가 `waitMask` 로 먼저 본다.

## 위치

`storage` / `lmgr` / `lock.c` L1527-L1643 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1527-L1643))

## 실제 코드

`storage` / `lmgr` / `lock.c` L1527-L1643 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1527-L1643))

```c
// lock.c L1527-L1643
bool
LockCheckConflicts(LockMethod lockMethodTable,
				   LOCKMODE lockmode,
				   LOCK *lock,
				   PROCLOCK *proclock)
{
	int			numLockModes = lockMethodTable->numLockModes;
	LOCKMASK	myLocks;
	int			conflictMask = lockMethodTable->conflictTab[lockmode];
	int			conflictsRemaining[MAX_LOCKMODES];
	int			totalConflictsRemaining = 0;
	dlist_iter	proclock_iter;
	int			i;

	/*
	 * first check for global conflicts: If no locks conflict with my request,
	 * then I get the lock.
	 *
	 * Checking for conflict: lock->grantMask represents the types of
	 * currently held locks.  conflictTable[lockmode] has a bit set for each
	 * type of lock that conflicts with request.   Bitwise compare tells if
	 * there is a conflict.
	 */
	if (!(conflictMask & lock->grantMask))
	{
		PROCLOCK_PRINT("LockCheckConflicts: no conflict", proclock);
		return false;
	}

	/*
	 * Rats.  Something conflicts.  But it could still be my own lock, or a
	 * lock held by another member of my locking group.  First, figure out how
	 * many conflicts remain after subtracting out any locks I hold myself.
	 */
	myLocks = proclock->holdMask;
	for (i = 1; i <= numLockModes; i++)
	{
		if ((conflictMask & LOCKBIT_ON(i)) == 0)
		{
			conflictsRemaining[i] = 0;
			continue;
		}
		conflictsRemaining[i] = lock->granted[i];
		if (myLocks & LOCKBIT_ON(i))
			--conflictsRemaining[i];
		totalConflictsRemaining += conflictsRemaining[i];
	}

	/* If no conflicts remain, we get the lock. */
	if (totalConflictsRemaining == 0)
	{
		PROCLOCK_PRINT("LockCheckConflicts: resolved (simple)", proclock);
		return false;
	}

	/* If no group locking, it's definitely a conflict. */
	if (proclock->groupLeader == MyProc && MyProc->lockGroupLeader == NULL)
	{
		Assert(proclock->tag.myProc == MyProc);
		PROCLOCK_PRINT("LockCheckConflicts: conflicting (simple)",
					   proclock);
		return true;
	}

	/*
	 * The relation extension lock conflict even between the group members.
	 */
	if (LOCK_LOCKTAG(*lock) == LOCKTAG_RELATION_EXTEND)
	{
		PROCLOCK_PRINT("LockCheckConflicts: conflicting (group)",
					   proclock);
		return true;
	}

	/*
	 * Locks held in conflicting modes by members of our own lock group are
	 * not real conflicts; we can subtract those out and see if we still have
	 * a conflict.  This is O(N) in the number of processes holding or
	 * awaiting locks on this object.  We could improve that by making the
	 * shared memory state more complex (and larger) but it doesn't seem worth
	 * it.
	 */
	dlist_foreach(proclock_iter, &lock->procLocks)
	{
		PROCLOCK   *otherproclock =
			dlist_container(PROCLOCK, lockLink, proclock_iter.cur);

		if (proclock != otherproclock &&
			proclock->groupLeader == otherproclock->groupLeader &&
			(otherproclock->holdMask & conflictMask) != 0)
		{
			int			intersectMask = otherproclock->holdMask & conflictMask;

			for (i = 1; i <= numLockModes; i++)
			{
				if ((intersectMask & LOCKBIT_ON(i)) != 0)
				{
					if (conflictsRemaining[i] <= 0)
						elog(PANIC, "proclocks held do not match lock");
					conflictsRemaining[i]--;
					totalConflictsRemaining--;
				}
			}

			if (totalConflictsRemaining == 0)
			{
				PROCLOCK_PRINT("LockCheckConflicts: resolved (group)",
							   proclock);
				return false;
			}
		}
	}

	/* Nope, it's a real conflict. */
	PROCLOCK_PRINT("LockCheckConflicts: conflicting (group)", proclock);
	return true;
}
```

호출자 쪽에서 이 함수보다 먼저 보는 조건이다. 같은 모드를 기다리는 이가 있으면, 지금 승인된 잠금과 충돌하지 않아도 기다린다.

`storage` / `lmgr` / `lock.c` L1088-L1097 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1088-L1097))

```c
// lock.c L1088-L1097
	/*
	 * If lock requested conflicts with locks requested by waiters, must join
	 * wait queue.  Otherwise, check for conflict with already-held locks.
	 * (That's last because most complex check.)
	 */
	if (lockMethodTable->conflictTab[lockmode] & lock->waitMask)
		found_conflict = true;
	else
		found_conflict = LockCheckConflicts(lockMethodTable, lockmode,
											lock, proclock);
```

## 동작 흐름

```text
 L1535  conflictMask = conflictTab[lockmode]

 L1550  conflictMask & lock->grantMask == 0         -> false (충돌 없음)   대부분 여기서 끝
 L1561  myLocks = proclock->holdMask
 L1562  for 모드 i = 1..8 중 conflictMask 에 든 것
 L1569    conflictsRemaining[i] = granted[i] - (내가 i 를 쥐었으면 1)
 L1576  합이 0                                       -> false   남은 충돌은 모두 내 것
 L1583  lock group 이 아니다                         -> true
 L1594  relation extension lock                     -> true    그룹 안에서도 충돌한다
 L1609  procLocks 를 돌며 같은 groupLeader 의 PROCLOCK 이 쥔 충돌 모드를 뺀다
 L1631    합이 0 이 되면                              -> false
 L1642  -> true
```

granted[] 는 proc 당 1 로 센다(lock.h L305-L307). 그래서 "내 몫 1 을 빼면 남는 수"가 곧 다른 proc 의 수다. 아래는 같은 테이블에 INSERT 를 한 트랜잭션이 이어서 `CREATE INDEX` 를 하는 경우다.

```text
 conflictTab[5 ShareLock] = 0x1d8 = 모드 {3, 4, 6, 7, 8}

 경우 1  A 만 RX 를 쥐고 있다, A 가 S 를 요청
   grantMask = {3}        0x1d8 & (1<<3) != 0       L1550 통과 못 함
   i=3  remaining = granted[3] 1 - A 의 몫 1 = 0
   i=4,6,7,8  granted 0  -> 0
   합 0                    -> false, A 는 RX 와 S 를 함께 쥔다 (holdMask = {3, 5})

 경우 2  A 와 B 가 RX 를 쥐고 있다, A 가 S 를 요청
   i=3  remaining = 2 - 1 = 1
   합 1, lock group 아님   -> true, A 는 B 의 RX 가 풀리기를 기다린다

 경우 3  A 가 AS 를 쥐고 있다, B 가 AS 를 요청
   conflictTab[1] = 0x100 = {8}, grantMask = {1}     -> L1550 에서 바로 false
```

```text
 충돌 판정의 두 단계 (호출 순서)

 LockAcquireExtended L1093   conflictTab[mode] & lock->waitMask    기다리는 요청과 충돌?
                              yes -> LockCheckConflicts 를 부르지 않고 대기 쪽으로
 LockAcquireExtended L1096   LockCheckConflicts                     승인된 잠금과 충돌?

 첫 단계가 있어서 AX 를 기다리는 이 뒤로 AS 요청이 새치기하지 못한다
   B 가 AX 대기 중 (waitMask = {8}), C 가 AS 요청
   conflictTab[1] & waitMask = {8} -> C 도 대기. B 가 굶지 않는다
 단, 이미 쥔 잠금이 있으면 JoinWaitQueue 가 앞자리를 줄 수 있다 ([08])
```

## 결과가 쓰이는 곳

```text
 false
      --> [07] GrantLock 으로 바로 승인 (LockAcquireExtended L1102)
      --> JoinWaitQueue 가 큐 앞자리에 끼면서 즉시 승인할 때 (proc.c L1276)
      --> ProcLockWakeup 이 대기자를 깨울지 정할 때 (proc.c L1790-L1792)
 true
      --> [08] JoinWaitQueue 로 대기
```

## 다루지 않는 것

lock group(병렬 쿼리의 leader 와 worker 가 잠금을 나눠 쓰는 묶음)을 만드는 `BecomeLockGroupLeader`·`BecomeLockGroupMember`(proc.c L2034, L2064)와 그 목록 관리는 판정 분기에서 이름만 짚었다.
