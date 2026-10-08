# LockAcquireExtended

상위: [heavyweight lock](../README.md)

**heavyweight lock 을 얻는 유일한 본체이자 이 흐름의 지휘자다.** 지역 해시에서 이미 가진 잠금인지 보고, 약한 테이블 잠금이면 fast-path 로 끝내고, 아니면 파티션 LWLock 아래에서 공유 해시를 고친다. 충돌하면 대기 큐에 넣고 잠들게 하며, 깨어난 뒤에는 공유 상태를 더 고치지 않고 지역 기록만 남긴다.

## 위치

`storage` / `lmgr` / `lock.c` L834-L1269 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L834-L1269))

## 실제 코드

앞부분이다. 인자를 검사하고, LOCALLOCK 을 찾거나 만들고, 이미 가진 잠금이면 여기서 끝난다.

`storage` / `lmgr` / `lock.c` L834-L946 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L834-L946))

```c
// lock.c L834-L946
LockAcquireResult
LockAcquireExtended(const LOCKTAG *locktag,
					LOCKMODE lockmode,
					bool sessionLock,
					bool dontWait,
					bool reportMemoryError,
					LOCALLOCK **locallockp,
					bool logLockFailure)
{
	LOCKMETHODID lockmethodid = locktag->locktag_lockmethodid;
	LockMethod	lockMethodTable;
	LOCALLOCKTAG localtag;
	LOCALLOCK  *locallock;
	LOCK	   *lock;
	PROCLOCK   *proclock;
	bool		found;
	ResourceOwner owner;
	uint32		hashcode;
	LWLock	   *partitionLock;
	bool		found_conflict;
	ProcWaitStatus waitResult;
	bool		log_lock = false;

	if (lockmethodid <= 0 || lockmethodid >= lengthof(LockMethods))
		elog(ERROR, "unrecognized lock method: %d", lockmethodid);
	lockMethodTable = LockMethods[lockmethodid];
	if (lockmode <= 0 || lockmode > lockMethodTable->numLockModes)
		elog(ERROR, "unrecognized lock mode: %d", lockmode);

	if (RecoveryInProgress() && !InRecovery &&
		(locktag->locktag_type == LOCKTAG_OBJECT ||
		 locktag->locktag_type == LOCKTAG_RELATION) &&
		lockmode > RowExclusiveLock)
		ereport(ERROR,
				(errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
				 errmsg("cannot acquire lock mode %s on database objects while recovery is in progress",
						lockMethodTable->lockModeNames[lockmode]),
				 errhint("Only RowExclusiveLock or less can be acquired on database objects during recovery.")));

// ... (L873-L878 생략: LOCK_DEBUG 추적 출력)

	/* Identify owner for lock */
	if (sessionLock)
		owner = NULL;
	else
		owner = CurrentResourceOwner;

	/*
	 * Find or create a LOCALLOCK entry for this lock and lockmode
	 */
	MemSet(&localtag, 0, sizeof(localtag)); /* must clear padding */
	localtag.lock = *locktag;
	localtag.mode = lockmode;

	locallock = (LOCALLOCK *) hash_search(LockMethodLocalHash,
										  &localtag,
										  HASH_ENTER, &found);

	/*
	 * if it's a new locallock object, initialize it
	 */
	if (!found)
	{
		locallock->lock = NULL;
		locallock->proclock = NULL;
		locallock->hashcode = LockTagHashCode(&(localtag.lock));
		locallock->nLocks = 0;
		locallock->holdsStrongLockCount = false;
		locallock->lockCleared = false;
		locallock->numLockOwners = 0;
		locallock->maxLockOwners = 8;
		locallock->lockOwners = NULL;	/* in case next line fails */
		locallock->lockOwners = (LOCALLOCKOWNER *)
			MemoryContextAlloc(TopMemoryContext,
							   locallock->maxLockOwners * sizeof(LOCALLOCKOWNER));
	}
	else
	{
		/* Make sure there will be room to remember the lock */
		if (locallock->numLockOwners >= locallock->maxLockOwners)
		{
			int			newsize = locallock->maxLockOwners * 2;

			locallock->lockOwners = (LOCALLOCKOWNER *)
				repalloc(locallock->lockOwners,
						 newsize * sizeof(LOCALLOCKOWNER));
			locallock->maxLockOwners = newsize;
		}
	}
	hashcode = locallock->hashcode;

	if (locallockp)
		*locallockp = locallock;

	/*
	 * If we already hold the lock, we can just increase the count locally.
	 *
	 * If lockCleared is already set, caller need not worry about absorbing
	 * sinval messages related to the lock's object.
	 */
	if (locallock->nLocks > 0)
	{
		GrantLockLocal(locallock, owner);
		if (locallock->lockCleared)
			return LOCKACQUIRE_ALREADY_CLEAR;
		else
			return LOCKACQUIRE_ALREADY_HELD;
	}
```

fast-path 와 강한 잠금 준비다. 약한 잠금은 내 PGPROC 슬롯에 적고 끝나며, 강한 잠금은 strong count 를 올린 뒤 남들의 fast-path 잠금을 공유 해시로 옮긴다.

`storage` / `lmgr` / `lock.c` L948-L1046 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L948-L1046))

```c
// lock.c L948-L1046
	/*
	 * We don't acquire any other heavyweight lock while holding the relation
	 * extension lock.  We do allow to acquire the same relation extension
	 * lock more than once but that case won't reach here.
	 */
	Assert(!IsRelationExtensionLockHeld);

	/*
	 * Prepare to emit a WAL record if acquisition of this lock needs to be
	 * replayed in a standby server.
	 *
	 * Here we prepare to log; after lock is acquired we'll issue log record.
	 * This arrangement simplifies error recovery in case the preparation step
	 * fails.
	 *
	 * Only AccessExclusiveLocks can conflict with lock types that read-only
	 * transactions can acquire in a standby server. Make sure this definition
	 * matches the one in GetRunningTransactionLocks().
	 */
	if (lockmode >= AccessExclusiveLock &&
		locktag->locktag_type == LOCKTAG_RELATION &&
		!RecoveryInProgress() &&
		XLogStandbyInfoActive())
	{
		LogAccessExclusiveLockPrepare();
		log_lock = true;
	}

	/*
	 * Attempt to take lock via fast path, if eligible.  But if we remember
	 * having filled up the fast path array, we don't attempt to make any
	 * further use of it until we release some locks.  It's possible that some
	 * other backend has transferred some of those locks to the shared hash
	 * table, leaving space free, but it's not worth acquiring the LWLock just
	 * to check.  It's also possible that we're acquiring a second or third
	 * lock type on a relation we have already locked using the fast-path, but
	 * for now we don't worry about that case either.
	 */
	if (EligibleForRelationFastPath(locktag, lockmode) &&
		FastPathLocalUseCounts[FAST_PATH_REL_GROUP(locktag->locktag_field2)] < FP_LOCK_SLOTS_PER_GROUP)
	{
		uint32		fasthashcode = FastPathStrongLockHashPartition(hashcode);
		bool		acquired;

		/*
		 * LWLockAcquire acts as a memory sequencing point, so it's safe to
		 * assume that any strong locker whose increment to
		 * FastPathStrongRelationLocks->counts becomes visible after we test
		 * it has yet to begin to transfer fast-path locks.
		 */
		LWLockAcquire(&MyProc->fpInfoLock, LW_EXCLUSIVE);
		if (FastPathStrongRelationLocks->count[fasthashcode] != 0)
			acquired = false;
		else
			acquired = FastPathGrantRelationLock(locktag->locktag_field2,
												 lockmode);
		LWLockRelease(&MyProc->fpInfoLock);
		if (acquired)
		{
			/*
			 * The locallock might contain stale pointers to some old shared
			 * objects; we MUST reset these to null before considering the
			 * lock to be acquired via fast-path.
			 */
			locallock->lock = NULL;
			locallock->proclock = NULL;
			GrantLockLocal(locallock, owner);
			return LOCKACQUIRE_OK;
		}
	}

	/*
	 * If this lock could potentially have been taken via the fast-path by
	 * some other backend, we must (temporarily) disable further use of the
	 * fast-path for this lock tag, and migrate any locks already taken via
	 * this method to the main lock table.
	 */
	if (ConflictsWithRelationFastPath(locktag, lockmode))
	{
		uint32		fasthashcode = FastPathStrongLockHashPartition(hashcode);

		BeginStrongLockAcquire(locallock, fasthashcode);
		if (!FastPathTransferRelationLocks(lockMethodTable, locktag,
										   hashcode))
		{
			AbortStrongLockAcquire();
			if (locallock->nLocks == 0)
				RemoveLocalLock(locallock);
			if (locallockp)
				*locallockp = NULL;
			if (reportMemoryError)
				ereport(ERROR,
						(errcode(ERRCODE_OUT_OF_MEMORY),
						 errmsg("out of shared memory"),
						 errhint("You might need to increase \"%s\".", "max_locks_per_transaction")));
			else
				return LOCKACQUIRE_NOT_AVAIL;
		}
	}
```

공유 해시 구간이다. 파티션 LWLock 을 잡고 LOCK, PROCLOCK 을 준비한 뒤 충돌을 판정한다.

`storage` / `lmgr` / `lock.c` L1048-L1113 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1048-L1113))

```c
// lock.c L1048-L1113
	/*
	 * We didn't find the lock in our LOCALLOCK table, and we didn't manage to
	 * take it via the fast-path, either, so we've got to mess with the shared
	 * lock table.
	 */
	partitionLock = LockHashPartitionLock(hashcode);

	LWLockAcquire(partitionLock, LW_EXCLUSIVE);

	/*
	 * Find or create lock and proclock entries with this tag
	 *
	 * Note: if the locallock object already existed, it might have a pointer
	 * to the lock already ... but we should not assume that that pointer is
	 * valid, since a lock object with zero hold and request counts can go
	 * away anytime.  So we have to use SetupLockInTable() to recompute the
	 * lock and proclock pointers, even if they're already set.
	 */
	proclock = SetupLockInTable(lockMethodTable, MyProc, locktag,
								hashcode, lockmode);
	if (!proclock)
	{
		AbortStrongLockAcquire();
		LWLockRelease(partitionLock);
		if (locallock->nLocks == 0)
			RemoveLocalLock(locallock);
		if (locallockp)
			*locallockp = NULL;
		if (reportMemoryError)
			ereport(ERROR,
					(errcode(ERRCODE_OUT_OF_MEMORY),
					 errmsg("out of shared memory"),
					 errhint("You might need to increase \"%s\".", "max_locks_per_transaction")));
		else
			return LOCKACQUIRE_NOT_AVAIL;
	}
	locallock->proclock = proclock;
	lock = proclock->tag.myLock;
	locallock->lock = lock;

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

	if (!found_conflict)
	{
		/* No conflict with held or previously requested locks */
		GrantLock(lock, proclock, lockmode);
		waitResult = PROC_WAIT_STATUS_OK;
	}
	else
	{
		/*
		 * Join the lock's wait queue.  We call this even in the dontWait
		 * case, because JoinWaitQueue() may discover that we can acquire the
		 * lock immediately after all.
		 */
		waitResult = JoinWaitQueue(locallock, lockMethodTable, dontWait);
	}
```

대기 큐에 들어가지 못한 경우(즉시 보인 교착, 또는 `dontWait`)의 되돌리기다.

`storage` / `lmgr` / `lock.c` L1115-L1207 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1115-L1207))

```c
// lock.c L1115-L1207
	if (waitResult == PROC_WAIT_STATUS_ERROR)
	{
		/*
		 * We're not getting the lock because a deadlock was detected already
		 * while trying to join the wait queue, or because we would have to
		 * wait but the caller requested no blocking.
		 *
		 * Undo the changes to shared entries before releasing the partition
		 * lock.
		 */
		AbortStrongLockAcquire();

		if (proclock->holdMask == 0)
		{
			uint32		proclock_hashcode;

			proclock_hashcode = ProcLockHashCode(&proclock->tag,
												 hashcode);
			dlist_delete(&proclock->lockLink);
			dlist_delete(&proclock->procLink);
			if (!hash_search_with_hash_value(LockMethodProcLockHash,
											 &(proclock->tag),
											 proclock_hashcode,
											 HASH_REMOVE,
											 NULL))
				elog(PANIC, "proclock table corrupted");
		}
		else
			PROCLOCK_PRINT("LockAcquire: did not join wait queue", proclock);
		lock->nRequested--;
		lock->requested[lockmode]--;
		LOCK_PRINT("LockAcquire: did not join wait queue",
				   lock, lockmode);
		Assert((lock->nRequested > 0) &&
			   (lock->requested[lockmode] >= 0));
		Assert(lock->nGranted <= lock->nRequested);
		LWLockRelease(partitionLock);
		if (locallock->nLocks == 0)
			RemoveLocalLock(locallock);

		if (dontWait)
		{
			// ... (L1157-L1197 생략: logLockFailure 일 때 보유자와 대기자를 로그로 남기는 부분)
			if (locallockp)
				*locallockp = NULL;
			return LOCKACQUIRE_NOT_AVAIL;
		}
		else
		{
			DeadLockReport();
			/* DeadLockReport() will not return */
		}
	}
```

잠들고, 깨어나 지역 기록을 남기는 끝부분이다.

`storage` / `lmgr` / `lock.c` L1209-L1269 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1209-L1269))

```c
// lock.c L1209-L1269
	/*
	 * We are now in the lock queue, or the lock was already granted.  If
	 * queued, go to sleep.
	 */
	if (waitResult == PROC_WAIT_STATUS_WAITING)
	{
		Assert(!dontWait);
		PROCLOCK_PRINT("LockAcquire: sleeping on lock", proclock);
		LOCK_PRINT("LockAcquire: sleeping on lock", lock, lockmode);
		LWLockRelease(partitionLock);

		waitResult = WaitOnLock(locallock, owner);

		/*
		 * NOTE: do not do any material change of state between here and
		 * return.  All required changes in locktable state must have been
		 * done when the lock was granted to us --- see notes in WaitOnLock.
		 */

		if (waitResult == PROC_WAIT_STATUS_ERROR)
		{
			/*
			 * We failed as a result of a deadlock, see CheckDeadLock(). Quit
			 * now.
			 */
			Assert(!dontWait);
			DeadLockReport();
			/* DeadLockReport() will not return */
		}
	}
	else
		LWLockRelease(partitionLock);
	Assert(waitResult == PROC_WAIT_STATUS_OK);

	/* The lock was granted to us.  Update the local lock entry accordingly */
	Assert((proclock->holdMask & LOCKBIT_ON(lockmode)) != 0);
	GrantLockLocal(locallock, owner);

	/*
	 * Lock state is fully up-to-date now; if we error out after this, no
	 * special error cleanup is required.
	 */
	FinishStrongLockAcquire();

	/*
	 * Emit a WAL record if acquisition of this lock needs to be replayed in a
	 * standby server.
	 */
	if (log_lock)
	{
		/*
		 * Decode the locktag back to the original values, to avoid sending
		 * lots of empty bytes with every message.  See lock.h to check how a
		 * locktag is defined for LOCKTAG_RELATION
		 */
		LogAccessExclusiveLock(locktag->locktag_field1,
							   locktag->locktag_field2);
	}

	return LOCKACQUIRE_OK;
}
```

## 동작 흐름

```text
 L857  lockmethodid, lockmode 범위 검사
 L863  hot standby 에서 테이블/객체에 RowExclusiveLock 보다 강한 모드 -> ERROR
 L881  owner = sessionLock ? NULL : CurrentResourceOwner

 L890  localtag = (locktag, lockmode)          모드마다 LOCALLOCK 이 따로 있다
 L893  hash_search(LockMethodLocalHash, HASH_ENTER)
 L900    새 항목  hashcode = LockTagHashCode, nLocks = 0, lockOwners 8 칸
 L918    있던 항목  lockOwners 가 꽉 찼으면 두 배로
 L939  nLocks > 0                              이미 가진 잠금
 L941    GrantLockLocal -> ALREADY_CLEAR 또는 ALREADY_HELD 로 반환. 공유 메모리는 보지 않는다

 L967  AccessExclusiveLock + 테이블 + wal_level >= replica  -> log_lock = true

 L986  갈래 1  fast-path
         조건  EligibleForRelationFastPath (모드 < 4, 이 DB 의 테이블)
               이 그룹의 지역 사용 수 < 16
 L998    LWLockAcquire(MyProc->fpInfoLock)
 L999    strong count[hashcode % 1024] != 0 이면 포기
 L1002   [03] FastPathGrantRelationLock
 L1005   성공  lock = proclock = NULL, GrantLockLocal, OK 반환

 L1025 갈래 2  ConflictsWithRelationFastPath (모드 > 4, 테이블)
 L1029   BeginStrongLockAcquire     strong count++ (이 순간부터 이 파티션의 fast-path 가 막힌다)
 L1030   [04] FastPathTransferRelationLocks   실패면 공유 메모리 부족 ERROR

 L1053 partitionLock = LockHashPartitionLock(hashcode)   16 개 중 하나
 L1055 LWLockAcquire(partitionLock, EXCLUSIVE)
 L1066 [05] SetupLockInTable                LOCK, PROCLOCK 확보, requested++
 L1093 conflictTab[mode] & lock->waitMask   기다리는 이와 충돌 -> 충돌로 본다 (새치기 금지)
 L1096 아니면 [06] LockCheckConflicts
 L1102   충돌 없음  [07] GrantLock, waitResult = OK
 L1112   충돌       [08] JoinWaitQueue  -> OK / WAITING / ERROR

 L1115 ERROR  (즉시 교착 또는 dontWait)
 L1125   AbortStrongLockAcquire
 L1127   holdMask == 0 이면 PROCLOCK 을 목록과 해시에서 지운다
 L1144   requested-- 를 되돌리고 파티션 LWLock 해제
 L1155   dontWait  -> NOT_AVAIL 반환
 L1204   아니면    DeadLockReport (ERROR, 돌아오지 않는다)

 L1213 WAITING
 L1218   파티션 LWLock 해제
 L1220   WaitOnLock -> [09] ProcSleep       깨어나면 이미 GrantLock 이 끝나 있다
 L1228   ERROR 면 DeadLockReport
 L1240 OK 면 파티션 LWLock 해제

 L1245 GrantLockLocal(locallock, owner)     지역 횟수, ResourceOwner 기록
 L1251 FinishStrongLockAcquire              strong count 는 잠금을 풀 때까지 남긴다
 L1257 log_lock 이면 LogAccessExclusiveLock (WAL)
 L1268 LOCKACQUIRE_OK
```

세 갈래가 어떤 잠금에서 갈리는지를 모드로 세우면 아래와 같다. 갈래는 모드와 LOCKTAG 종류만으로 정해지고, 상대가 무엇을 쥐었는지는 공유 해시 구간에 들어가서야 본다.

```text
 요청 (LOCKTAG_RELATION, 이 DB 의 테이블이라고 할 때)

 모드  이름  EligibleFast  ConflictsFast  가는 길
 1     AS    yes           no             fast-path (strong count 0 이고 슬롯이 있으면)
 2     RS    yes           no             fast-path
 3     RX    yes           no             fast-path
 4     SUX   no            no             공유 해시 (strong count 를 건드리지 않는다)
 5     S     no            yes            strong count++, 옮기기, 공유 해시
 6     SRX   no            yes            "
 7     X     no            yes            "
 8     AX    no            yes            " + log_lock (wal_level >= replica)

 테이블이 아닌 LOCKTAG (트랜잭션 ID, 튜플, 객체 ...) 는 모드와 상관없이 공유 해시로만 간다
 공유 카탈로그(field1 = InvalidOid)는 EligibleFast 가 아니고 ConflictsFast 도 아니다 (lock.c L267-L277)
```

```text
 파티션 LWLock 을 쥐는 구간 (L1055 에서 잡는다)

 경로                          놓는 곳
 즉시 승인 (GrantLock)         L1240
 대기                          L1218  -> 잠든 동안에는 쥐지 않는다
 즉시 교착 / dontWait          L1151
 SetupLockInTable 실패         L1071

 잠든 뒤의 공유 상태 변경은 전부 남이 한다
   깨우는 쪽 ProcLockWakeup 이 GrantLock 까지 해 주고 (proc.c L1795)
   교착이면 CheckDeadLock 이 RemoveFromWaitQueue 로 되돌린다 (proc.c L1874)
   그래서 L1222-L1225 주석이 "여기서 상태를 바꾸지 말라"고 적는다
```

## 결과가 쓰이는 곳

```text
 LockAcquireResult
      --> [01] LockRelationOid 가 ALREADY_CLEAR 가 아니면 무효화 메시지를 흡수한다
      --> ConditionalLock* 계열은 NOT_AVAIL 로 "못 잡음"을 안다

 LOCALLOCK (nLocks, lockOwners, lock, proclock)
      --> 다음 같은 요청의 L939 지름길
      --> [11] LockReleaseAll 이 이 해시를 돌며 해제한다 (lock 이 NULL 이면 fast-path)

 holdsStrongLockCount
      --> RemoveLocalLock 이 풀 때 strong count 를 내린다 (lock.c L1489-L1500)
```

## 다루지 않는 것

hot standby 로 잠금을 넘기는 `LogAccessExclusiveLockPrepare`·`LogAccessExclusiveLock`(`storage/ipc/standby.c`), `logLockFailure` 로그의 내용(`GetLockHoldersAndWaiters`), 교착 메시지를 만드는 `DeadLockReport`(deadlock.c L1075), relation extension lock 을 쥔 채 다른 잠금을 못 잡게 하는 단언(L953)은 판정 분기에서 이름만 짚었다.
