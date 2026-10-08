# GrantLock

상위: [heavyweight lock](../README.md)

**승인을 공유 자료에 기록한다.** LOCK 의 승인 수와 `grantMask`, PROCLOCK 의 `holdMask` 를 올리고, 이 모드를 기다리는 요청이 더 없으면 `waitMask` 에서 그 비트를 끈다. 지역 기록(`LOCALLOCK`)은 건드리지 않는데, 이 함수는 남을 깨우면서 그 사람 몫으로도 불리기 때문이다. 지역 쪽은 잠금을 얻은 본인이 `GrantLockLocal` 로 남긴다.

## 위치

`storage` / `lmgr` / `lock.c` L1656-L1668 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1656-L1668))

## 실제 코드

`storage` / `lmgr` / `lock.c` L1645-L1668 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1645-L1668))

```c
// lock.c L1645-L1668
/*
 * GrantLock -- update the lock and proclock data structures to show
 *		the lock request has been granted.
 *
 * NOTE: if proc was blocked, it also needs to be removed from the wait list
 * and have its waitLock/waitProcLock fields cleared.  That's not done here.
 *
 * NOTE: the lock grant also has to be recorded in the associated LOCALLOCK
 * table entry; but since we may be awaking some other process, we can't do
 * that here; it's done by GrantLockLocal, instead.
 */
void
GrantLock(LOCK *lock, PROCLOCK *proclock, LOCKMODE lockmode)
{
	lock->nGranted++;
	lock->granted[lockmode]++;
	lock->grantMask |= LOCKBIT_ON(lockmode);
	if (lock->granted[lockmode] == lock->requested[lockmode])
		lock->waitMask &= LOCKBIT_OFF(lockmode);
	proclock->holdMask |= LOCKBIT_ON(lockmode);
	LOCK_PRINT("GrantLock", lock, lockmode);
	Assert((lock->nGranted > 0) && (lock->granted[lockmode] > 0));
	Assert(lock->nGranted <= lock->nRequested);
}
```

본인 쪽 짝이다. LOCALLOCK 의 횟수를 올리고 ResourceOwner 에 잠금을 기억시킨다.

`storage` / `lmgr` / `lock.c` L1790-L1816 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L1790-L1816))

```c
// lock.c L1790-L1816
static void
GrantLockLocal(LOCALLOCK *locallock, ResourceOwner owner)
{
	LOCALLOCKOWNER *lockOwners = locallock->lockOwners;
	int			i;

	Assert(locallock->numLockOwners < locallock->maxLockOwners);
	/* Count the total */
	locallock->nLocks++;
	/* Count the per-owner lock */
	for (i = 0; i < locallock->numLockOwners; i++)
	{
		if (lockOwners[i].owner == owner)
		{
			lockOwners[i].nLocks++;
			return;
		}
	}
	lockOwners[i].owner = owner;
	lockOwners[i].nLocks = 1;
	locallock->numLockOwners++;
	if (owner != NULL)
		ResourceOwnerRememberLock(owner, locallock);

	/* Indicate that the lock is acquired for certain types of locks. */
	CheckAndSetLockHeld(locallock, true);
}
```

## 동작 흐름

```text
 GrantLock (파티션 LWLock 아래)
 L1659  lock->nGranted++
 L1660  lock->granted[lockmode]++
 L1661  lock->grantMask |= bit(lockmode)
 L1662  granted[lockmode] == requested[lockmode] 이면
 L1663    waitMask &= ~bit(lockmode)            이 모드로 기다리는 이가 더 없다
 L1664  proclock->holdMask |= bit(lockmode)

 GrantLockLocal (본인 backend, LWLock 없음)
 L1798  locallock->nLocks++
 L1800  lockOwners[] 에 같은 owner 가 있으면 그 nLocks++ 하고 끝
 L1808  없으면 새 칸 (owner, 1)
 L1811  owner 가 있으면 ResourceOwnerRememberLock
```

이 흐름에서 GrantLock 을 부르는 자리는 넷이고, 그중 둘은 요청자가 아닌 다른 backend 다(이 밖에 `FastPathGetRelationLockEntry` L2971, 2PC 복구의 `lock_twophase_recover` L4485, `VirtualXactLock` L4791 도 부른다). 그래서 공유 자료와 지역 자료를 나눠 고친다.

```text
 GrantLock 을 부르는 곳                  누가 부르나                    지역 기록은
 LockAcquireExtended  lock.c L1102       요청자 본인                    L1245 GrantLockLocal
 JoinWaitQueue        proc.c L1280       요청자 본인 (큐 앞자리 승인)    L1245 GrantLockLocal
 ProcLockWakeup       proc.c L1795       잠금을 푼 다른 backend          깨어난 본인이 L1245 에서
 FastPathTransfer     lock.c L2905       강한 잠금을 잡는 다른 backend   원래 주인의 LOCALLOCK 은 그대로 (lock == NULL)
```

```text
 같은 잠금을 두 번 얻을 때 어디가 바뀌는가 (SELECT 를 같은 트랜잭션에서 두 번, 공유 해시 길이라고 할 때)

                      1 번째                     2 번째
 LOCK.granted[1]      0 -> 1                     그대로 (L939 지름길, GrantLock 을 부르지 않는다)
 PROCLOCK.holdMask    {} -> {1}                  그대로
 LOCALLOCK.nLocks     0 -> 1                     1 -> 2
 lockOwners           (portal owner, 1)          같은 owner 면 (.., 2), 다르면 칸 하나 더

 공유 자료는 "누가 쥐었나"만, 지역 자료는 "몇 번, 누구 이름으로"를 센다
```

## 결과가 쓰이는 곳

```text
 grantMask, granted[]
      --> 다음 요청의 [06] LockCheckConflicts 가 본다
 waitMask
      --> 다음 요청의 L1093 새치기 금지 검사가 본다
 holdMask
      --> [11] LockReleaseAll 이 releaseMask 로 옮겨 하나씩 UnGrantLock 한다
 lockOwners, ResourceOwner
      --> 서브트랜잭션 abort 는 LockReleaseCurrentOwner 로 그 owner 의 잠금만 푼다
      --> 서브트랜잭션 commit 은 LockReassignCurrentOwner 로 부모 owner 에게 넘긴다
```

## 다루지 않는 것

ResourceOwner 의 잠금 캐시(`ResourceOwnerRememberLock`, `utils/resowner/resowner.c`)와 relation extension lock 표시(`CheckAndSetLockHeld` L1463)는 다루지 않았다.
