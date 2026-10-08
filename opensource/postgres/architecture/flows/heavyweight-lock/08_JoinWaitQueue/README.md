# JoinWaitQueue

상위: [heavyweight lock](../README.md)

**충돌한 요청이 대기 큐의 어디에 설지 정하고 큐에 넣는다.** 보통은 맨 뒤지만, 이미 쥔 잠금 때문에 앞의 대기자가 어차피 나를 기다려야 한다면 그 대기자 앞에 선다. 그 자리에서 바로 승인할 수 있으면 잠들지 않고 승인하고, 앞의 대기자와 내가 서로를 기다리는 모양이면 `deadlock_timeout` 을 기다리지 않고 바로 교착으로 끝낸다. 파티션 LWLock 을 쥔 채 불리고, 쥔 채 돌아간다.

## 위치

`storage` / `lmgr` / `proc.c` L1172-L1326 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1172-L1326))

## 실제 코드

`storage` / `lmgr` / `proc.c` L1146-L1326 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L1146-L1326))

```c
// lmgr/proc.c L1146-L1326
/*
 * JoinWaitQueue -- join the wait queue on the specified lock
 *
 * It's not actually guaranteed that we need to wait when this function is
 * called, because it could be that when we try to find a position at which
 * to insert ourself into the wait queue, we discover that we must be inserted
 * ahead of everyone who wants a lock that conflict with ours. In that case,
 * we get the lock immediately. Because of this, it's sensible for this function
 * to have a dontWait argument, despite the name.
 *
 * On entry, the caller has already set up LOCK and PROCLOCK entries to
 * reflect that we have "requested" the lock.  The caller is responsible for
 * cleaning that up, if we end up not joining the queue after all.
 *
 * The lock table's partition lock must be held at entry, and is still held
 * at exit.  The caller must release it before calling ProcSleep().
 *
 * Result is one of the following:
 *
 *  PROC_WAIT_STATUS_OK       - lock was immediately granted
 *  PROC_WAIT_STATUS_WAITING  - joined the wait queue; call ProcSleep()
 *  PROC_WAIT_STATUS_ERROR    - immediate deadlock was detected, or would
 *                              need to wait and dontWait == true
 *
 * NOTES: The process queue is now a priority queue for locking.
 */
ProcWaitStatus
JoinWaitQueue(LOCALLOCK *locallock, LockMethod lockMethodTable, bool dontWait)
{
	LOCKMODE	lockmode = locallock->tag.mode;
	LOCK	   *lock = locallock->lock;
	PROCLOCK   *proclock = locallock->proclock;
	uint32		hashcode = locallock->hashcode;
	LWLock	   *partitionLock PG_USED_FOR_ASSERTS_ONLY = LockHashPartitionLock(hashcode);
	dclist_head *waitQueue = &lock->waitProcs;
	PGPROC	   *insert_before = NULL;
	LOCKMASK	myProcHeldLocks;
	LOCKMASK	myHeldLocks;
	bool		early_deadlock = false;
	PGPROC	   *leader = MyProc->lockGroupLeader;

	Assert(LWLockHeldByMeInMode(partitionLock, LW_EXCLUSIVE));

	/*
	 * Set bitmask of locks this process already holds on this object.
	 */
	myHeldLocks = MyProc->heldLocks = proclock->holdMask;

	/*
	 * Determine which locks we're already holding.
	 *
	 * If group locking is in use, locks held by members of my locking group
	 * need to be included in myHeldLocks.  This is not required for relation
	 * extension lock which conflict among group members. However, including
	 * them in myHeldLocks will give group members the priority to get those
	 * locks as compared to other backends which are also trying to acquire
	 * those locks.  OTOH, we can avoid giving priority to group members for
	 * that kind of locks, but there doesn't appear to be a clear advantage of
	 * the same.
	 */
	myProcHeldLocks = proclock->holdMask;
	myHeldLocks = myProcHeldLocks;
	if (leader != NULL)
	{
		dlist_iter	iter;

		dlist_foreach(iter, &lock->procLocks)
		{
			PROCLOCK   *otherproclock;

			otherproclock = dlist_container(PROCLOCK, lockLink, iter.cur);

			if (otherproclock->groupLeader == leader)
				myHeldLocks |= otherproclock->holdMask;
		}
	}

	/*
	 * Determine where to add myself in the wait queue.
	 *
	 * Normally I should go at the end of the queue.  However, if I already
	 * hold locks that conflict with the request of any previous waiter, put
	 * myself in the queue just in front of the first such waiter. This is not
	 * a necessary step, since deadlock detection would move me to before that
	 * waiter anyway; but it's relatively cheap to detect such a conflict
	 * immediately, and avoid delaying till deadlock timeout.
	 *
	 * Special case: if I find I should go in front of some waiter, check to
	 * see if I conflict with already-held locks or the requests before that
	 * waiter.  If not, then just grant myself the requested lock immediately.
	 * This is the same as the test for immediate grant in LockAcquire, except
	 * we are only considering the part of the wait queue before my insertion
	 * point.
	 */
	if (myHeldLocks != 0 && !dclist_is_empty(waitQueue))
	{
		LOCKMASK	aheadRequests = 0;
		dlist_iter	iter;

		dclist_foreach(iter, waitQueue)
		{
			PGPROC	   *proc = dlist_container(PGPROC, links, iter.cur);

			/*
			 * If we're part of the same locking group as this waiter, its
			 * locks neither conflict with ours nor contribute to
			 * aheadRequests.
			 */
			if (leader != NULL && leader == proc->lockGroupLeader)
				continue;

			/* Must he wait for me? */
			if (lockMethodTable->conflictTab[proc->waitLockMode] & myHeldLocks)
			{
				/* Must I wait for him ? */
				if (lockMethodTable->conflictTab[lockmode] & proc->heldLocks)
				{
					/*
					 * Yes, so we have a deadlock.  Easiest way to clean up
					 * correctly is to call RemoveFromWaitQueue(), but we
					 * can't do that until we are *on* the wait queue. So, set
					 * a flag to check below, and break out of loop.  Also,
					 * record deadlock info for later message.
					 */
					RememberSimpleDeadLock(MyProc, lockmode, lock, proc);
					early_deadlock = true;
					break;
				}
				/* I must go before this waiter.  Check special case. */
				if ((lockMethodTable->conflictTab[lockmode] & aheadRequests) == 0 &&
					!LockCheckConflicts(lockMethodTable, lockmode, lock,
										proclock))
				{
					/* Skip the wait and just grant myself the lock. */
					GrantLock(lock, proclock, lockmode);
					return PROC_WAIT_STATUS_OK;
				}

				/* Put myself into wait queue before conflicting process */
				insert_before = proc;
				break;
			}
			/* Nope, so advance to next waiter */
			aheadRequests |= LOCKBIT_ON(proc->waitLockMode);
		}
	}

	/*
	 * If we detected deadlock, give up without waiting.  This must agree with
	 * CheckDeadLock's recovery code.
	 */
	if (early_deadlock)
		return PROC_WAIT_STATUS_ERROR;

	/*
	 * At this point we know that we'd really need to sleep. If we've been
	 * commanded not to do that, bail out.
	 */
	if (dontWait)
		return PROC_WAIT_STATUS_ERROR;

	/*
	 * Insert self into queue, at the position determined above.
	 */
	if (insert_before)
		dclist_insert_before(waitQueue, &insert_before->links, &MyProc->links);
	else
		dclist_push_tail(waitQueue, &MyProc->links);

	lock->waitMask |= LOCKBIT_ON(lockmode);

	/* Set up wait information in PGPROC object, too */
	MyProc->heldLocks = myProcHeldLocks;
	MyProc->waitLock = lock;
	MyProc->waitProcLock = proclock;
	MyProc->waitLockMode = lockmode;

	MyProc->waitStatus = PROC_WAIT_STATUS_WAITING;

	return PROC_WAIT_STATUS_WAITING;
}
```

즉시 교착을 만났을 때 오류 메시지용으로 두 proc 을 기록해 둔다.

`storage` / `lmgr` / `deadlock.c` L1146-L1162 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/deadlock.c#L1146-L1162))

```c
// deadlock.c L1146-L1162
void
RememberSimpleDeadLock(PGPROC *proc1,
					   LOCKMODE lockmode,
					   LOCK *lock,
					   PGPROC *proc2)
{
	DEADLOCK_INFO *info = &deadlockDetails[0];

	info->locktag = lock->tag;
	info->lockmode = lockmode;
	info->pid = proc1->pid;
	info++;
	info->locktag = proc2->waitLock->tag;
	info->lockmode = proc2->waitLockMode;
	info->pid = proc2->pid;
	nDeadlockDetails = 2;
}
```

## 동작 흐름

```text
 L1192  myHeldLocks = MyProc->heldLocks = proclock->holdMask    이 대상에서 이미 쥔 모드
 L1208  lock group 이면 같은 그룹 PROCLOCK 의 holdMask 도 더한다

 L1240  쥔 것이 있고 큐가 비어 있지 않을 때만 자리를 찾는다
 L1245  for 큐의 proc (앞에서부터)
 L1254    같은 그룹이면 건너뜀
 L1258    그가 원하는 모드가 내가 쥔 것과 충돌 (그가 나를 기다려야 한다)
 L1261      내가 원하는 모드가 그가 쥔 것과도 충돌 -> 서로 기다림
 L1270        RememberSimpleDeadLock, early_deadlock = true, break
 L1275      앞쪽 요청(aheadRequests)과도, 승인된 잠금과도 충돌하지 않으면
 L1280        GrantLock, OK 반환                  큐에 서지 않고 바로 승인
 L1285      아니면 insert_before = 그, break
 L1289    충돌 없으면 aheadRequests |= 그의 모드, 다음으로

 L1297  early_deadlock -> ERROR
 L1304  dontWait       -> ERROR
 L1310  insert_before 앞에, 없으면 L1313 맨 뒤에
 L1315  lock->waitMask |= bit(lockmode)
 L1318  MyProc 에 heldLocks, waitLock, waitProcLock, waitLockMode 기록
 L1323  waitStatus = WAITING, WAITING 반환
```

앞자리를 주는 규칙은 "어차피 그가 나를 기다려야 하니 내가 먼저 받아도 손해가 없다"는 판단이다(L1224-L1238 주석). 아래 두 경우는 같은 시작 상태에서 A 가 다른 모드를 요청한 결과다.

```text
 시작 상태: 테이블 t
   A 가 AS 를 쥠, B 가 AX 를 요청해 대기 중
   LOCK(t)  grantMask = {1}  waitMask = {8}  waitProcs = [B]   B.heldLocks = {}

 경우 1  A 가 RX (모드 3) 요청   (같은 트랜잭션의 INSERT)
   L1093  conflictTab[3] {5,6,7,8} & waitMask {8} -> 충돌로 보고 JoinWaitQueue
   myHeldLocks = {1}
   큐의 B   conflictTab[8] & {1} != 0       B 는 A 를 기다려야 한다
            conflictTab[3] & B.heldLocks {} = 0   A 는 B 를 기다릴 필요가 없다
            aheadRequests = 0, LockCheckConflicts(3): grantMask {1} 과 충돌 없음
   -> GrantLock, OK. A 는 잠들지 않는다           LOCK(t).grantMask = {1, 3}

 경우 2  B 도 AS 를 쥔 채 AX 를 기다리는 중, A 가 AX 요청   (둘 다 SELECT 후 ALTER)
   B.heldLocks = {1}
   큐의 B   conflictTab[8] & {1} != 0       B 는 A 를 기다려야 한다
            conflictTab[8] & B.heldLocks {1} != 0   A 도 B 를 기다려야 한다
   -> RememberSimpleDeadLock(A, 8, t, B), ERROR
   -> LockAcquireExtended L1204 DeadLockReport -> "deadlock detected"
      deadlock_timeout 을 기다리지 않는다
```

```text
 큐 안의 자리 (insert_before 가 정해질 때)

 Q 가 X(7) 를 쥐고 있어 RS, AX 요청이 기다리는 중. 나는 AS 를 쥔 채 S(5) 를 요청
 (AS 는 X 와 충돌하지 않으므로 Q 와 함께 쥘 수 있었다)

 waitProcs   [ P1(RS) ]  [ P2(AX) ]  [ P3(RS) ]
             P1: conflictTab[2] {7,8} & {1} = 0  -> aheadRequests |= {2}
             P2: conflictTab[8] & {1} != 0, conflictTab[5] & P2.heldLocks = 0
                 conflictTab[5] {3,4,6,7,8} & aheadRequests {2} = 0 이고
                 L1276 LockCheckConflicts(5): Q 의 X 와 충돌 -> 바로 승인은 못 하고 P2 앞에 선다
 결과        [ P1(RS) ]  [ 나(S) ]  [ P2(AX) ]  [ P3(RS) ]
```

## 결과가 쓰이는 곳

```text
 WAITING
      --> LockAcquireExtended 가 파티션 LWLock 을 놓고 WaitOnLock -> [09] ProcSleep
 OK
      --> 바로 GrantLockLocal (L1245)
 ERROR
      --> dontWait 면 NOT_AVAIL, 아니면 DeadLockReport

 MyProc.waitLock, waitLockMode, heldLocks
      --> 다른 backend 의 JoinWaitQueue 가 L1258, L1261 에서 나를 볼 때 쓴다
      --> [10] 교착 검사와 ProcLockWakeup, pg_locks 가 읽는다
```

## 다루지 않는 것

lock group 의 대기 큐 처리(L1208-L1221, L1254), 오류 메시지의 문장(`DeadLockReport`)은 다루지 않았다.
