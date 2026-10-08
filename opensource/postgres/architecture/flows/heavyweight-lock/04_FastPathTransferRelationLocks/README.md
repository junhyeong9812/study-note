# FastPathTransferRelationLocks

상위: [heavyweight lock](../README.md)

**강한 테이블 잠금(모드 5~8)을 잡기 직전에, 모든 backend 의 fast-path 슬롯에 흩어진 같은 테이블의 약한 잠금을 공유 해시로 옮긴다.** 옮기기 전에 호출자가 strong count 를 올려 두므로 이후 누구도 그 파티션에서 fast-path 를 새로 쓰지 못한다. 옮긴 뒤에는 강한 잠금이 공유 해시만 보고도 모든 보유자와의 충돌을 판정할 수 있다.

## 위치

`storage` / `lmgr` / `lock.c` L2828-L2916 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L2828-L2916))

## 실제 코드

strong count 의 정의다. LOCKTAG 해시를 1024 칸으로 나누어 칸마다 "강한 잠금을 쥐었거나 잡는 중인 수"를 센다.

`storage` / `lmgr` / `lock.c` L285-L312 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L285-L312))

```c
// lock.c L285-L312
/*
 * To make the fast-path lock mechanism work, we must have some way of
 * preventing the use of the fast-path when a conflicting lock might be present.
 * We partition* the locktag space into FAST_PATH_STRONG_LOCK_HASH_PARTITIONS,
 * and maintain an integer count of the number of "strong" lockers
 * in each partition.  When any "strong" lockers are present (which is
 * hopefully not very often), the fast-path mechanism can't be used, and we
 * must fall back to the slower method of pushing matching locks directly
 * into the main lock tables.
 *
 * The deadlock detector does not know anything about the fast path mechanism,
 * so any locks that might be involved in a deadlock must be transferred from
 * the fast-path queues to the main lock table.
 */

#define FAST_PATH_STRONG_LOCK_HASH_BITS			10
#define FAST_PATH_STRONG_LOCK_HASH_PARTITIONS \
	(1 << FAST_PATH_STRONG_LOCK_HASH_BITS)
#define FastPathStrongLockHashPartition(hashcode) \
	((hashcode) % FAST_PATH_STRONG_LOCK_HASH_PARTITIONS)

typedef struct
{
	slock_t		mutex;
	uint32		count[FAST_PATH_STRONG_LOCK_HASH_PARTITIONS];
} FastPathStrongRelationLockData;

static volatile FastPathStrongRelationLockData *FastPathStrongRelationLocks;
```

호출자가 옮기기 전에 부르는 짝이다. spinlock 아래에서 칸을 하나 올리고, 실패하면 되돌릴 수 있게 기억해 둔다.

`storage` / `lmgr` / `lock.c` L1822-L1842 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1822-L1842))

```c
// lock.c L1822-L1842
static void
BeginStrongLockAcquire(LOCALLOCK *locallock, uint32 fasthashcode)
{
	Assert(StrongLockInProgress == NULL);
	Assert(locallock->holdsStrongLockCount == false);

	/*
	 * Adding to a memory location is not atomic, so we take a spinlock to
	 * ensure we don't collide with someone else trying to bump the count at
	 * the same time.
	 *
	 * XXX: It might be worth considering using an atomic fetch-and-add
	 * instruction here, on architectures where that is supported.
	 */

	SpinLockAcquire(&FastPathStrongRelationLocks->mutex);
	FastPathStrongRelationLocks->count[fasthashcode]++;
	locallock->holdsStrongLockCount = true;
	StrongLockInProgress = locallock;
	SpinLockRelease(&FastPathStrongRelationLocks->mutex);
}
```

`storage` / `lmgr` / `lock.c` L1858-L1875 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1858-L1875))

```c
// lock.c L1858-L1875
void
AbortStrongLockAcquire(void)
{
	uint32		fasthashcode;
	LOCALLOCK  *locallock = StrongLockInProgress;

	if (locallock == NULL)
		return;

	fasthashcode = FastPathStrongLockHashPartition(locallock->hashcode);
	Assert(locallock->holdsStrongLockCount == true);
	SpinLockAcquire(&FastPathStrongRelationLocks->mutex);
	Assert(FastPathStrongRelationLocks->count[fasthashcode] > 0);
	FastPathStrongRelationLocks->count[fasthashcode]--;
	locallock->holdsStrongLockCount = false;
	StrongLockInProgress = NULL;
	SpinLockRelease(&FastPathStrongRelationLocks->mutex);
}
```

본체다.

`storage` / `lmgr` / `lock.c` L2828-L2916 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L2828-L2916))

```c
// lock.c L2828-L2916
static bool
FastPathTransferRelationLocks(LockMethod lockMethodTable, const LOCKTAG *locktag,
							  uint32 hashcode)
{
	LWLock	   *partitionLock = LockHashPartitionLock(hashcode);
	Oid			relid = locktag->locktag_field2;
	uint32		i;

	/* fast-path group the lock belongs to */
	uint32		group = FAST_PATH_REL_GROUP(relid);

	/*
	 * Every PGPROC that can potentially hold a fast-path lock is present in
	 * ProcGlobal->allProcs.  Prepared transactions are not, but any
	 * outstanding fast-path locks held by prepared transactions are
	 * transferred to the main lock table.
	 */
	for (i = 0; i < ProcGlobal->allProcCount; i++)
	{
		PGPROC	   *proc = &ProcGlobal->allProcs[i];
		uint32		j;

		LWLockAcquire(&proc->fpInfoLock, LW_EXCLUSIVE);

		/*
		 * If the target backend isn't referencing the same database as the
		 * lock, then we needn't examine the individual relation IDs at all;
		 * none of them can be relevant.
		 *
		 * proc->databaseId is set at backend startup time and never changes
		 * thereafter, so it might be safe to perform this test before
		 * acquiring &proc->fpInfoLock.  In particular, it's certainly safe to
		 * assume that if the target backend holds any fast-path locks, it
		 * must have performed a memory-fencing operation (in particular, an
		 * LWLock acquisition) since setting proc->databaseId.  However, it's
		 * less clear that our backend is certain to have performed a memory
		 * fencing operation since the other backend set proc->databaseId.  So
		 * for now, we test it after acquiring the LWLock just to be safe.
		 *
		 * Also skip groups without any registered fast-path locks.
		 */
		if (proc->databaseId != locktag->locktag_field1 ||
			proc->fpLockBits[group] == 0)
		{
			LWLockRelease(&proc->fpInfoLock);
			continue;
		}

		for (j = 0; j < FP_LOCK_SLOTS_PER_GROUP; j++)
		{
			uint32		lockmode;

			/* index into the whole per-backend array */
			uint32		f = FAST_PATH_SLOT(group, j);

			/* Look for an allocated slot matching the given relid. */
			if (relid != proc->fpRelId[f] || FAST_PATH_GET_BITS(proc, f) == 0)
				continue;

			/* Find or create lock object. */
			LWLockAcquire(partitionLock, LW_EXCLUSIVE);
			for (lockmode = FAST_PATH_LOCKNUMBER_OFFSET;
				 lockmode < FAST_PATH_LOCKNUMBER_OFFSET + FAST_PATH_BITS_PER_SLOT;
				 ++lockmode)
			{
				PROCLOCK   *proclock;

				if (!FAST_PATH_CHECK_LOCKMODE(proc, f, lockmode))
					continue;
				proclock = SetupLockInTable(lockMethodTable, proc, locktag,
											hashcode, lockmode);
				if (!proclock)
				{
					LWLockRelease(partitionLock);
					LWLockRelease(&proc->fpInfoLock);
					return false;
				}
				GrantLock(proclock->tag.myLock, proclock, lockmode);
				FAST_PATH_CLEAR_LOCKMODE(proc, f, lockmode);
			}
			LWLockRelease(partitionLock);

			/* No need to examine remaining slots. */
			break;
		}
		LWLockRelease(&proc->fpInfoLock);
	}
	return true;
}
```

## 동작 흐름

```text
 호출 전 (LockAcquireExtended L1025-L1031)
   ConflictsWithRelationFastPath  -> RELATION, field1 != InvalidOid, 모드 > 4
   BeginStrongLockAcquire         count[hashcode % 1024]++, StrongLockInProgress = locallock

 L2837  group = FAST_PATH_REL_GROUP(relid)
 L2845  for 모든 PGPROC (ProcGlobal->allProcs)
 L2850    LWLockAcquire(proc->fpInfoLock)
 L2869    다른 DB 이거나 이 그룹 비트가 전부 0 -> 건너뜀
 L2876    for j in 0..15  (그 그룹의 슬롯)
 L2884      fpRelId != relid 또는 비트 0 -> 건너뜀
 L2888      LWLockAcquire(partitionLock)
 L2889      for 모드 1..3
 L2895        비트가 서 있으면
 L2897          [05] SetupLockInTable(lockMethodTable, proc, ...)   그 proc 이름으로 PROCLOCK
 L2903          공간 없음 -> false (호출자가 out of shared memory)
 L2905          [07] GrantLock                      공유 해시에 "이미 승인됨"으로 적는다
 L2906          FAST_PATH_CLEAR_LOCKMODE            슬롯에서는 지운다
 L2908      partitionLock 해제
 L2911      break   한 proc 에 같은 relid 슬롯은 하나뿐
 L2913    fpInfoLock 해제
 L2915  true
```

옮기는 동안 fast-path 를 새로 쓰려는 쪽과 엇갈리지 않는 이유는 두 쪽이 같은 `fpInfoLock` 과 같은 count 칸을 보기 때문이다. 아래는 backend A 가 SELECT 중인 테이블에 backend B 가 `ALTER TABLE` 을 거는 순서다.

```text
 A = SELECT ... FROM t   (AccessShareLock, 모드 1)
 B = ALTER TABLE t       (AccessExclusiveLock, 모드 8)
 c = t 의 hashcode % 1024

 순서  누가  함수                       일어나는 일
 1     A     LockAcquireExtended L999   count[c] == 0, 슬롯에 AS 비트 (fpInfoLock(A) 아래)
 2     B     BeginStrongLockAcquire     count[c] = 1
 3     B     Transfer L2850             fpInfoLock(A) 획득, A 의 슬롯에서 t 의 AS 를 찾는다
 4     B     Transfer L2897-L2906       PROCLOCK(t, A).holdMask = AS, LOCK(t).grantMask = AS, A 의 비트를 지운다
 5     B     LockCheckConflicts         conflictTab[8] & grantMask 에 AS 가 걸린다 -> 충돌
 6     B     JoinWaitQueue, ProcSleep   LOCK(t).waitProcs 에 들어가 잠든다
 7     A     LockAcquireExtended L939   같은 트랜잭션에서 t 를 또 열면 지역 해시 지름길
 8     A     LockAcquireExtended L999   같은 칸 c 에 걸리는 다른 테이블은 fast-path 를 포기한다
 9     A     LockReleaseAll L2403       커밋. 슬롯에 비트가 없으니 FastPathUnGrant 가 false
 10    A     LockRefindAndRelease       공유 해시에서 AS 를 풀고 CleanUpLock -> ProcLockWakeup
 11    B     ProcSleep                  깨어 보니 이미 GrantLock 되어 있다. AX 획득
 12    B     RemoveLocalLock L1497      B 의 트랜잭션이 끝나 잠금을 풀 때 count[c] = 0
```

```text
 strong count 의 수명 (lock.c)

 올림    BeginStrongLockAcquire                L1838  옮기기 전
 성공    FinishStrongLockAcquire               L1849  되돌림 표시만 지운다. 칸은 그대로
 실패    AbortStrongLockAcquire                L1871  칸을 내린다 (대기 거절, 메모리 부족)
 해제    RemoveLocalLock                       L1497  잠금을 풀 때 holdsStrongLockCount 면 내린다

 강한 잠금을 쥐고 있는 내내 칸이 0 이 아니므로
 같은 칸에 걸리는 모든 테이블(서로 다른 테이블이어도)의 약한 잠금이 공유 해시로 간다
```

## 결과가 쓰이는 곳

```text
 공유 해시의 LOCK / PROCLOCK (원래 주인 proc 의 이름으로)
      --> 호출자의 [06] LockCheckConflicts 가 이 grantMask 와 granted[] 를 보고 판정한다
      --> 교착 검사기가 이 PROCLOCK 을 대기 그래프의 간선으로 본다
          fast-path 에 남아 있으면 검사기는 볼 수 없다 (lock.c L295-L297 주석)

 원래 주인의 LOCALLOCK 은 그대로 lock == NULL
      --> [11] LockReleaseAll 의 FastPathUnGrantRelationLock 이 false 를 내면
          LockRefindAndRelease 로 공유 해시에서 찾아 푼다
```

## 다루지 않는 것

`allProcs` 에 없는 prepared transaction 의 fast-path 잠금(주석 L2840-L2843), fast-path 슬롯의 메모리 순서 논증(L2852-L2867 주석의 memory fence), 강한 잠금이 아닌 쪽에서 남의 잠금 목록을 모으는 `GetLockConflicts`(L3037)는 다루지 않았다.
