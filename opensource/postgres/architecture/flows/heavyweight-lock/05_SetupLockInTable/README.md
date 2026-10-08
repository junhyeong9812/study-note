# SetupLockInTable

상위: [heavyweight lock](../README.md)

**공유 해시에서 대상의 LOCK 과 (대상, proc) 쌍의 PROCLOCK 을 찾거나 만들고, 요청 수를 하나 올린다.** 승인 여부는 여기서 정하지 않는다. `requested[]` 는 승인과 대기를 모두 세므로 여기서 바로 올리고, `granted[]` 는 [07] `GrantLock` 이 올린다. 호출자는 파티션 LWLock 을 쥐고 부른다.

## 위치

`storage` / `lmgr` / `lock.c` L1281-L1452 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1281-L1452))

## 실제 코드

공유 해시 두 개의 항목 모양이다.

`src` / `include` / `storage` / `lock.h` L309-L323 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/lock.h#L309-L323))

```c
// lock.h L309-L323
typedef struct LOCK
{
	/* hash key */
	LOCKTAG		tag;			/* unique identifier of lockable object */

	/* data */
	LOCKMASK	grantMask;		/* bitmask for lock types already granted */
	LOCKMASK	waitMask;		/* bitmask for lock types awaited */
	dlist_head	procLocks;		/* list of PROCLOCK objects assoc. with lock */
	dclist_head waitProcs;		/* list of PGPROC objects waiting on lock */
	int			requested[MAX_LOCKMODES];	/* counts of requested locks */
	int			nRequested;		/* total of requested[] array */
	int			granted[MAX_LOCKMODES]; /* counts of granted locks */
	int			nGranted;		/* total of granted[] array */
} LOCK;
```

`src` / `include` / `storage` / `lock.h` L363-L381 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/lock.h#L363-L381))

```c
// lock.h L363-L381
typedef struct PROCLOCKTAG
{
	/* NB: we assume this struct contains no padding! */
	LOCK	   *myLock;			/* link to per-lockable-object information */
	PGPROC	   *myProc;			/* link to PGPROC of owning backend */
} PROCLOCKTAG;

typedef struct PROCLOCK
{
	/* tag */
	PROCLOCKTAG tag;			/* unique identifier of proclock object */

	/* data */
	PGPROC	   *groupLeader;	/* proc's lock group leader, or proc itself */
	LOCKMASK	holdMask;		/* bitmask for lock types currently held */
	LOCKMASK	releaseMask;	/* bitmask for lock types to be released */
	dlist_node	lockLink;		/* list link in LOCK's list of proclocks */
	dlist_node	procLink;		/* list link in PGPROC's list of proclocks */
} PROCLOCK;
```

PROCLOCK 의 해시값은 LOCK 의 해시값에 PGPROC 주소를 섞되, 아래 4 비트(파티션 번호)는 건드리지 않는다. 그래서 LOCK 과 그 PROCLOCK 이 늘 같은 파티션에 있고, 파티션 LWLock 하나로 둘을 함께 지킬 수 있다.

`storage` / `lmgr` / `lock.c` L603-L616 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L603-L616))

```c
// lock.c L603-L616
static inline uint32
ProcLockHashCode(const PROCLOCKTAG *proclocktag, uint32 hashcode)
{
	uint32		lockhash = hashcode;
	Datum		procptr;

	/*
	 * This must match proclock_hash()!
	 */
	procptr = PointerGetDatum(proclocktag->myProc);
	lockhash ^= ((uint32) procptr) << LOG2_NUM_LOCK_PARTITIONS;

	return lockhash;
}
```

본체다.

`storage` / `lmgr` / `lock.c` L1281-L1452 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1281-L1452))

```c
// lock.c L1281-L1452
static PROCLOCK *
SetupLockInTable(LockMethod lockMethodTable, PGPROC *proc,
				 const LOCKTAG *locktag, uint32 hashcode, LOCKMODE lockmode)
{
	LOCK	   *lock;
	PROCLOCK   *proclock;
	PROCLOCKTAG proclocktag;
	uint32		proclock_hashcode;
	bool		found;

	/*
	 * Find or create a lock with this tag.
	 */
	lock = (LOCK *) hash_search_with_hash_value(LockMethodLockHash,
												locktag,
												hashcode,
												HASH_ENTER_NULL,
												&found);
	if (!lock)
		return NULL;

	/*
	 * if it's a new lock object, initialize it
	 */
	if (!found)
	{
		lock->grantMask = 0;
		lock->waitMask = 0;
		dlist_init(&lock->procLocks);
		dclist_init(&lock->waitProcs);
		lock->nRequested = 0;
		lock->nGranted = 0;
		MemSet(lock->requested, 0, sizeof(int) * MAX_LOCKMODES);
		MemSet(lock->granted, 0, sizeof(int) * MAX_LOCKMODES);
		LOCK_PRINT("LockAcquire: new", lock, lockmode);
	}
	else
	{
		LOCK_PRINT("LockAcquire: found", lock, lockmode);
		Assert((lock->nRequested >= 0) && (lock->requested[lockmode] >= 0));
		Assert((lock->nGranted >= 0) && (lock->granted[lockmode] >= 0));
		Assert(lock->nGranted <= lock->nRequested);
	}

	/*
	 * Create the hash key for the proclock table.
	 */
	proclocktag.myLock = lock;
	proclocktag.myProc = proc;

	proclock_hashcode = ProcLockHashCode(&proclocktag, hashcode);

	/*
	 * Find or create a proclock entry with this tag
	 */
	proclock = (PROCLOCK *) hash_search_with_hash_value(LockMethodProcLockHash,
														&proclocktag,
														proclock_hashcode,
														HASH_ENTER_NULL,
														&found);
	if (!proclock)
	{
		/* Oops, not enough shmem for the proclock */
		if (lock->nRequested == 0)
		{
			/*
			 * There are no other requestors of this lock, so garbage-collect
			 * the lock object.  We *must* do this to avoid a permanent leak
			 * of shared memory, because there won't be anything to cause
			 * anyone to release the lock object later.
			 */
			Assert(dlist_is_empty(&(lock->procLocks)));
			if (!hash_search_with_hash_value(LockMethodLockHash,
											 &(lock->tag),
											 hashcode,
											 HASH_REMOVE,
											 NULL))
				elog(PANIC, "lock table corrupted");
		}
		return NULL;
	}

	/*
	 * If new, initialize the new entry
	 */
	if (!found)
	{
		uint32		partition = LockHashPartition(hashcode);

		/*
		 * It might seem unsafe to access proclock->groupLeader without a
		 * lock, but it's not really.  Either we are initializing a proclock
		 * on our own behalf, in which case our group leader isn't changing
		 * because the group leader for a process can only ever be changed by
		 * the process itself; or else we are transferring a fast-path lock to
		 * the main lock table, in which case that process can't change its
		 * lock group leader without first releasing all of its locks (and in
		 * particular the one we are currently transferring).
		 */
		proclock->groupLeader = proc->lockGroupLeader != NULL ?
			proc->lockGroupLeader : proc;
		proclock->holdMask = 0;
		proclock->releaseMask = 0;
		/* Add proclock to appropriate lists */
		dlist_push_tail(&lock->procLocks, &proclock->lockLink);
		dlist_push_tail(&proc->myProcLocks[partition], &proclock->procLink);
		PROCLOCK_PRINT("LockAcquire: new", proclock);
	}
	else
	{
		PROCLOCK_PRINT("LockAcquire: found", proclock);
		Assert((proclock->holdMask & ~lock->grantMask) == 0);

// ... (L1394-L1429 생략: CHECK_DEADLOCK_RISK 빌드에서만 켜지는 경고)
	}

	/*
	 * lock->nRequested and lock->requested[] count the total number of
	 * requests, whether granted or waiting, so increment those immediately.
	 * The other counts don't increment till we get the lock.
	 */
	lock->nRequested++;
	lock->requested[lockmode]++;
	Assert((lock->nRequested > 0) && (lock->requested[lockmode] > 0));

	/*
	 * We shouldn't already hold the desired lock; else locallock table is
	 * broken.
	 */
	if (proclock->holdMask & LOCKBIT_ON(lockmode))
		elog(ERROR, "lock %s on object %u/%u/%u is already held",
			 lockMethodTable->lockModeNames[lockmode],
			 lock->tag.locktag_field1, lock->tag.locktag_field2,
			 lock->tag.locktag_field3);

	return proclock;
}
```

## 동작 흐름

```text
 L1294  hash_search_with_hash_value(LockMethodLockHash, locktag, hashcode, HASH_ENTER_NULL)
 L1299    NULL (공유 메모리 부족) -> NULL 반환
 L1305    새 LOCK  grantMask = waitMask = 0, procLocks, waitProcs 비움, 수 0

 L1328  proclocktag = (lock, proc)
 L1331  proclock_hashcode = ProcLockHashCode    hashcode ^ (proc 주소 << 4)
 L1336  hash_search_with_hash_value(LockMethodProcLockHash, HASH_ENTER_NULL)
 L1341    NULL -> 이 LOCK 을 요청한 이가 없으면(nRequested == 0) LOCK 도 지우고 NULL
 L1366    새 PROCLOCK
 L1380      groupLeader = proc->lockGroupLeader 또는 proc
 L1382      holdMask = releaseMask = 0
 L1385      LOCK.procLocks 끝에 붙인다
 L1386      PGPROC.myProcLocks[partition] 끝에 붙인다

 L1437  lock->nRequested++
 L1438  lock->requested[lockmode]++
 L1445  holdMask 에 이미 이 모드가 있으면 ERROR  (지역 해시가 깨졌다는 뜻)
 L1451  proclock 반환
```

LOCK 하나에 PROCLOCK 이 여럿 붙고, PGPROC 하나에도 PROCLOCK 이 여럿 붙는다. PROCLOCK 은 두 목록에 동시에 걸린 교차점이다.

```text
 테이블 t 를 A 가 RX 로 쥐고, B 가 AX 를 기다리는 상태 (L1385, L1386 의 두 목록)

                     LOCK(t)
                     grantMask = {RX}      waitMask = {AX}
                     requested[3]=1 [8]=1  nRequested = 2
                     granted[3]=1          nGranted   = 1
                     procLocks                         waitProcs
                       |                                 |
                       v                                 v
   PGPROC A  --->  PROCLOCK(t, A)  holdMask = {RX}      PGPROC B
   myProcLocks[p]      |
                       v
   PGPROC B  --->  PROCLOCK(t, B)  holdMask = {}   (기다리는 동안에도 항목은 있다)
   myProcLocks[p]

 p = hashcode % 16. 두 PROCLOCK 은 해시값이 달라도 같은 파티션 p 에 있다 (L613)
 B 의 PROCLOCK 은 waitProcs 와 별개로, 승인 전부터 procLocks 에 걸려 있다 (lock.h L357-L361)
```

```text
 requested 와 granted 의 차이 = 기다리는 수

 시점                    requested[8]  granted[8]  waitMask 의 AX
 B 의 SetupLockInTable   1             0           0
 B 의 JoinWaitQueue      1             0           1   (proc.c L1315)
 A 해제, B 승인 GrantLock 1             1           0   (granted == requested 라 끈다, L1662)
```

## 결과가 쓰이는 곳

```text
 proclock (호출자에게)
      --> LockAcquireExtended 가 locallock->proclock, locallock->lock 에 적는다 (L1084-L1086)
      --> [06] LockCheckConflicts, [07] GrantLock, [08] JoinWaitQueue 가 이 쌍을 받는다

 PGPROC.myProcLocks[partition]
      --> [11] LockReleaseAll 이 파티션별로 내 PROCLOCK 만 훑는 목록

 LOCK.procLocks
      --> 그룹 충돌 계산과 교착 검사의 hard 간선 탐색이 이 목록을 돈다
```

## 다루지 않는 것

해시 테이블 자체(`dynahash.c` 의 파티션 해시, `HASH_ENTER_NULL` 의 메모리 처리)와 공유 메모리 크기 계산(`LockManagerShmemSize` L3726, `NLOCKENTS`)은 다루지 않았다.
