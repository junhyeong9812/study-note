# FastPathGrantRelationLock

상위: [heavyweight lock](../README.md)

**약한 테이블 잠금(모드 1~3)을 공유 해시 대신 내 PGPROC 의 슬롯 배열에 적는다.** 테이블 OID 로 그룹을 정하고, 그룹의 16 슬롯 중 같은 OID 가 있으면 모드 비트만 더 세우고, 없으면 빈 슬롯을 쓴다. 쥐는 LWLock 은 내 `fpInfoLock` 하나뿐이라 파티션 LWLock 경합이 없다.

## 위치

`storage` / `lmgr` / `lock.c` L2749-L2785 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L2749-L2785))

## 실제 코드

슬롯 주소와 비트 위치를 계산하는 매크로다. 그룹은 OID 에 소수를 곱해 흩고, 슬롯 하나는 모드 1~3 을 위한 3 비트를 차지한다.

`storage` / `lmgr` / `lock.c` L204-L257 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L204-L257))

```c
// lock.c L204-L257
/*
 * Macros to calculate the fast-path group and index for a relation.
 *
 * The formula is a simple hash function, designed to spread the OIDs a bit,
 * so that even contiguous values end up in different groups. In most cases
 * there will be gaps anyway, but the multiplication should help a bit.
 *
 * The selected constant (49157) is a prime not too close to 2^k, and it's
 * small enough to not cause overflows (in 64-bit).
 *
 * We can assume that FastPathLockGroupsPerBackend is a power-of-two per
 * InitializeFastPathLocks().
 */
#define FAST_PATH_REL_GROUP(rel) \
	(((uint64) (rel) * 49157) & (FastPathLockGroupsPerBackend - 1))

/*
 * Given the group/slot indexes, calculate the slot index in the whole array
 * of fast-path lock slots.
 */
#define FAST_PATH_SLOT(group, index) \
	(AssertMacro((uint32) (group) < FastPathLockGroupsPerBackend), \
	 AssertMacro((uint32) (index) < FP_LOCK_SLOTS_PER_GROUP), \
	 ((group) * FP_LOCK_SLOTS_PER_GROUP + (index)))

/*
 * Given a slot index (into the whole per-backend array), calculated using
 * the FAST_PATH_SLOT macro, split it into group and index (in the group).
 */
#define FAST_PATH_GROUP(index)	\
	(AssertMacro((uint32) (index) < FastPathLockSlotsPerBackend()), \
	 ((index) / FP_LOCK_SLOTS_PER_GROUP))
#define FAST_PATH_INDEX(index)	\
	(AssertMacro((uint32) (index) < FastPathLockSlotsPerBackend()), \
	 ((index) % FP_LOCK_SLOTS_PER_GROUP))

/* Macros for manipulating proc->fpLockBits */
#define FAST_PATH_BITS_PER_SLOT			3
#define FAST_PATH_LOCKNUMBER_OFFSET		1
#define FAST_PATH_MASK					((1 << FAST_PATH_BITS_PER_SLOT) - 1)
#define FAST_PATH_BITS(proc, n)			(proc)->fpLockBits[FAST_PATH_GROUP(n)]
#define FAST_PATH_GET_BITS(proc, n) \
	((FAST_PATH_BITS(proc, n) >> (FAST_PATH_BITS_PER_SLOT * FAST_PATH_INDEX(n))) & FAST_PATH_MASK)
#define FAST_PATH_BIT_POSITION(n, l) \
	(AssertMacro((l) >= FAST_PATH_LOCKNUMBER_OFFSET), \
	 AssertMacro((l) < FAST_PATH_BITS_PER_SLOT+FAST_PATH_LOCKNUMBER_OFFSET), \
	 AssertMacro((n) < FastPathLockSlotsPerBackend()), \
	 ((l) - FAST_PATH_LOCKNUMBER_OFFSET + FAST_PATH_BITS_PER_SLOT * (FAST_PATH_INDEX(n))))
#define FAST_PATH_SET_LOCKMODE(proc, n, l) \
	 FAST_PATH_BITS(proc, n) |= UINT64CONST(1) << FAST_PATH_BIT_POSITION(n, l)
#define FAST_PATH_CLEAR_LOCKMODE(proc, n, l) \
	 FAST_PATH_BITS(proc, n) &= ~(UINT64CONST(1) << FAST_PATH_BIT_POSITION(n, l))
#define FAST_PATH_CHECK_LOCKMODE(proc, n, l) \
	 (FAST_PATH_BITS(proc, n) & (UINT64CONST(1) << FAST_PATH_BIT_POSITION(n, l)))
```

어떤 요청이 fast-path 를 쓸 수 있고, 어떤 요청이 fast-path 를 막아야 하는지의 정의다.

`storage` / `lmgr` / `lock.c` L259-L277 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L259-L277))

```c
// lock.c L259-L277
/*
 * The fast-path lock mechanism is concerned only with relation locks on
 * unshared relations by backends bound to a database.  The fast-path
 * mechanism exists mostly to accelerate acquisition and release of locks
 * that rarely conflict.  Because ShareUpdateExclusiveLock is
 * self-conflicting, it can't use the fast-path mechanism; but it also does
 * not conflict with any of the locks that do, so we can ignore it completely.
 */
#define EligibleForRelationFastPath(locktag, mode) \
	((locktag)->locktag_lockmethodid == DEFAULT_LOCKMETHOD && \
	(locktag)->locktag_type == LOCKTAG_RELATION && \
	(locktag)->locktag_field1 == MyDatabaseId && \
	MyDatabaseId != InvalidOid && \
	(mode) < ShareUpdateExclusiveLock)
#define ConflictsWithRelationFastPath(locktag, mode) \
	((locktag)->locktag_lockmethodid == DEFAULT_LOCKMETHOD && \
	(locktag)->locktag_type == LOCKTAG_RELATION && \
	(locktag)->locktag_field1 != InvalidOid && \
	(mode) > ShareUpdateExclusiveLock)
```

그룹 수는 기동할 때 `max_locks_per_transaction` 에서 정한다.

`utils` / `init` / `postinit.c` L579-L601 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L579-L601))

```c
// postinit.c L579-L601
void
InitializeFastPathLocks(void)
{
	/* Should be initialized only once. */
	Assert(FastPathLockGroupsPerBackend == 0);

	/*
	 * Based on the max_locks_per_transaction GUC, as that's a good indicator
	 * of the expected number of locks, figure out the value for
	 * FastPathLockGroupsPerBackend.  This must be a power-of-two.  We cap the
	 * value at FP_LOCK_GROUPS_PER_BACKEND_MAX and insist the value is at
	 * least 1.
	 *
	 * The default max_locks_per_transaction = 64 means 4 groups by default.
	 */
	FastPathLockGroupsPerBackend =
		Max(Min(pg_nextpower2_32(max_locks_per_xact) / FP_LOCK_SLOTS_PER_GROUP,
				FP_LOCK_GROUPS_PER_BACKEND_MAX), 1);

	/* Validate we did get a power-of-two */
	Assert(FastPathLockGroupsPerBackend ==
		   pg_nextpower2_32(FastPathLockGroupsPerBackend));
}
```

본체다.

`storage` / `lmgr` / `lock.c` L2749-L2785 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L2749-L2785))

```c
// lock.c L2749-L2785
static bool
FastPathGrantRelationLock(Oid relid, LOCKMODE lockmode)
{
	uint32		i;
	uint32		unused_slot = FastPathLockSlotsPerBackend();

	/* fast-path group the lock belongs to */
	uint32		group = FAST_PATH_REL_GROUP(relid);

	/* Scan for existing entry for this relid, remembering empty slot. */
	for (i = 0; i < FP_LOCK_SLOTS_PER_GROUP; i++)
	{
		/* index into the whole per-backend array */
		uint32		f = FAST_PATH_SLOT(group, i);

		if (FAST_PATH_GET_BITS(MyProc, f) == 0)
			unused_slot = f;
		else if (MyProc->fpRelId[f] == relid)
		{
			Assert(!FAST_PATH_CHECK_LOCKMODE(MyProc, f, lockmode));
			FAST_PATH_SET_LOCKMODE(MyProc, f, lockmode);
			return true;
		}
	}

	/* If no existing entry, use any empty slot. */
	if (unused_slot < FastPathLockSlotsPerBackend())
	{
		MyProc->fpRelId[unused_slot] = relid;
		FAST_PATH_SET_LOCKMODE(MyProc, unused_slot, lockmode);
		++FastPathLocalUseCounts[group];
		return true;
	}

	/* No existing entry, and no empty slot. */
	return false;
}
```

해제 짝이다. 비트를 지우면서 그룹의 지역 사용 수를 다시 센다.

`storage` / `lmgr` / `lock.c` L2792-L2819 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L2792-L2819))

```c
// lock.c L2792-L2819
static bool
FastPathUnGrantRelationLock(Oid relid, LOCKMODE lockmode)
{
	uint32		i;
	bool		result = false;

	/* fast-path group the lock belongs to */
	uint32		group = FAST_PATH_REL_GROUP(relid);

	FastPathLocalUseCounts[group] = 0;
	for (i = 0; i < FP_LOCK_SLOTS_PER_GROUP; i++)
	{
		/* index into the whole per-backend array */
		uint32		f = FAST_PATH_SLOT(group, i);

		if (MyProc->fpRelId[f] == relid
			&& FAST_PATH_CHECK_LOCKMODE(MyProc, f, lockmode))
		{
			Assert(!result);
			FAST_PATH_CLEAR_LOCKMODE(MyProc, f, lockmode);
			result = true;
			/* we continue iterating so as to update FastPathLocalUseCount */
		}
		if (FAST_PATH_GET_BITS(MyProc, f) != 0)
			++FastPathLocalUseCounts[group];
	}
	return result;
}
```

## 동작 흐름

```text
 호출 전 (LockAcquireExtended L986-L1004)
   EligibleForRelationFastPath  -> DEFAULT 메서드, RELATION, field1 == MyDatabaseId, 모드 < 4
   FastPathLocalUseCounts[group] < 16       지역 사용 수로 "꽉 찼음"을 먼저 거른다
   LWLockAcquire(MyProc->fpInfoLock)
   strong count[hashcode % 1024] == 0 일 때만 부른다

 L2756  group = FAST_PATH_REL_GROUP(relid)
 L2759  for i in 0..15
          f = group * 16 + i
 L2764    비트가 0 인 슬롯          unused_slot = f   (덮어쓰므로 마지막 빈 슬롯이 남는다)
 L2766    fpRelId[f] == relid       같은 테이블의 다른 모드를 이미 쥐었다
 L2769      FAST_PATH_SET_LOCKMODE, true
 L2775  빈 슬롯이 있었으면
 L2777    fpRelId[unused_slot] = relid
 L2778    FAST_PATH_SET_LOCKMODE
 L2779    FastPathLocalUseCounts[group]++
 L2780    true
 L2784  없으면 false -> 호출자는 공유 해시 길로 간다
```

기본 설정에서 숫자를 따라가 보면 슬롯과 비트가 어디에 놓이는지 정확히 나온다. 기본 `max_locks_per_transaction = 64` 이므로 그룹은 `pg_nextpower2_32(64) / 16 = 4` 개, 슬롯은 64 개다. `49157` 을 4 로 나눈 나머지가 1 이라, 그룹 4 개일 때 그룹 번호는 OID 를 4 로 나눈 나머지와 같다.

```text
 예: 같은 트랜잭션에서 OID 16385 테이블에 SELECT 뒤 INSERT (그룹이 비어 있던 상태)

 group = (16385 * 49157) & 3 = 1

 1) AccessShareLock (모드 1)
      i = 0..15 모두 비어 있다 -> unused_slot 이 매번 덮여 f = 1*16 + 15 = 31
      fpRelId[31] = 16385
      비트 위치 = (1 - 1) + 3 * (31 % 16) = 45
      fpLockBits[1] = 1<<45                       = 0x200000000000
      FastPathLocalUseCounts[1] = 1

 2) RowExclusiveLock (모드 3), LOCALLOCK 은 새 항목 (모드가 다르다)
      i = 15 에서 fpRelId[31] == 16385 -> 같은 슬롯
      비트 위치 = (3 - 1) + 3 * 15 = 47
      fpLockBits[1] = 1<<45 | 1<<47               = 0xa00000000000
      사용 수는 그대로 1

 fpLockBits[1] (uint64) 의 슬롯 15 자리
   bit 47 46 45
        1  0  1     모드 3(RX) 과 모드 1(AS) 을 쥐었고, 모드 2(RS) 는 아니다
   슬롯 16 개 x 3 비트 = 48 비트만 쓴다
```

```text
 이 길이 공유 해시보다 싼 이유와 그 대가

                fast-path                         공유 해시
 쥐는 LWLock    내 fpInfoLock 하나                파티션 LWLock (16 개를 모두가 나눠 쓴다)
 기록           내 PGPROC 의 슬롯                 LOCK, PROCLOCK 해시 항목
 남이 보려면    모든 PGPROC 의 슬롯을 훑어야 함   해시 조회 한 번

 그래서 "남이 볼 필요가 없는" 잠금만 이 길로 간다
   모드 1~3 끼리는 충돌하지 않으므로, 강한 잠금(5~8)이 없으면 아무도 이 슬롯을 볼 필요가 없다
   강한 잠금이 오면 [04] 가 슬롯을 훑어 공유 해시로 옮긴다
```

## 결과가 쓰이는 곳

```text
 fpRelId, fpLockBits
      --> [04] FastPathTransferRelationLocks 가 강한 잠금 앞에서 읽어 공유 해시로 옮긴다
      --> [11] LockReleaseAll 이 FastPathUnGrantRelationLock 으로 비트를 지운다
      --> pg_locks 뷰는 GetLockStatusData 가 모든 PGPROC 의 슬롯을 읽어 fastpath = true 로 보인다

 FastPathLocalUseCounts[group]
      --> 다음 요청이 L987 에서 16 이면 fast-path 를 시도조차 하지 않는다
```

## 다루지 않는 것

가상 트랜잭션 ID 의 fast-path 잠금(`fpVXIDLock`, `VirtualXactLockTableInsert` L4590), fast-path 로 잡았다가 옮겨진 잠금의 PROCLOCK 을 다시 찾는 `FastPathGetRelationLockEntry`(L2926)는 같은 슬롯 구조의 곁가지라 다루지 않았다.
