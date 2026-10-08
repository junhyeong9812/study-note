# LockRelationOid

상위: [heavyweight lock](../README.md)

**테이블을 OID 만으로 잠그는 가장 흔한 입구다.** relcache 항목을 열기 전에 부르며, LOCKTAG 를 만들어 [02] `LockAcquireExtended` 에 넘기고, 잠금을 얻은 뒤에는 그동안 쌓인 무효화 메시지를 받아 relcache 를 최신으로 맞춘다.

## 위치

`storage` / `lmgr` / `lmgr.c` L106-L139 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lmgr.c#L106-L139))

## 실제 코드

잠금 대상의 이름표다. 공유 카탈로그면 DB OID 자리에 0 을 넣어 모든 DB 가 같은 이름표를 보게 한다.

`storage` / `lmgr` / `lmgr.c` L87-L98 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lmgr.c#L87-L98))

```c
// lmgr.c L87-L98
static inline void
SetLocktagRelationOid(LOCKTAG *tag, Oid relid)
{
	Oid			dbid;

	if (IsSharedRelation(relid))
		dbid = InvalidOid;
	else
		dbid = MyDatabaseId;

	SET_LOCKTAG_RELATION(*tag, dbid, relid);
}
```

이름표를 채우는 매크로와 이름표의 모양이다.

`src` / `include` / `storage` / `lock.h` L165-L173 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/lock.h#L165-L173))

```c
// lock.h L165-L173
typedef struct LOCKTAG
{
	uint32		locktag_field1; /* a 32-bit ID field */
	uint32		locktag_field2; /* a 32-bit ID field */
	uint32		locktag_field3; /* a 32-bit ID field */
	uint16		locktag_field4; /* a 16-bit ID field */
	uint8		locktag_type;	/* see enum LockTagType */
	uint8		locktag_lockmethodid;	/* lockmethod indicator */
} LOCKTAG;
```

`src` / `include` / `storage` / `lock.h` L182-L188 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/lock.h#L182-L188))

```c
// lock.h L182-L188
#define SET_LOCKTAG_RELATION(locktag,dboid,reloid) \
	((locktag).locktag_field1 = (dboid), \
	 (locktag).locktag_field2 = (reloid), \
	 (locktag).locktag_field3 = 0, \
	 (locktag).locktag_field4 = 0, \
	 (locktag).locktag_type = LOCKTAG_RELATION, \
	 (locktag).locktag_lockmethodid = DEFAULT_LOCKMETHOD)
```

본체다. `sessionLock=false`, `dontWait=false`, `reportMemoryError=true` 로 부르고 LOCALLOCK 포인터를 받아 둔다.

`storage` / `lmgr` / `lmgr.c` L106-L139 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lmgr.c#L106-L139))

```c
// lmgr.c L106-L139
void
LockRelationOid(Oid relid, LOCKMODE lockmode)
{
	LOCKTAG		tag;
	LOCALLOCK  *locallock;
	LockAcquireResult res;

	SetLocktagRelationOid(&tag, relid);

	res = LockAcquireExtended(&tag, lockmode, false, false, true, &locallock,
							  false);

	/*
	 * Now that we have the lock, check for invalidation messages, so that we
	 * will update or flush any stale relcache entry before we try to use it.
	 * RangeVarGetRelid() specifically relies on us for this.  We can skip
	 * this in the not-uncommon case that we already had the same type of lock
	 * being requested, since then no one else could have modified the
	 * relcache entry in an undesirable way.  (In the case where our own xact
	 * modifies the rel, the relcache update happens via
	 * CommandCounterIncrement, not here.)
	 *
	 * However, in corner cases where code acts on tables (usually catalogs)
	 * recursively, we might get here while still processing invalidation
	 * messages in some outer execution of this function or a sibling.  The
	 * "cleared" status of the lock tells us whether we really are done
	 * absorbing relevant inval messages.
	 */
	if (res != LOCKACQUIRE_ALREADY_CLEAR)
	{
		AcceptInvalidationMessages();
		MarkLockClear(locallock);
	}
}
```

## 동작 흐름

```text
 L113  SetLocktagRelationOid(&tag, relid)
         L92  공유 카탈로그(pg_database 등)면 dbid = InvalidOid
         L95  아니면 dbid = MyDatabaseId
         L97  SET_LOCKTAG_RELATION -> field1=dbid field2=relid type=RELATION method=DEFAULT

 L115  LockAcquireExtended(&tag, lockmode,
                           sessionLock=false,      트랜잭션 잠금 (ResourceOwner 에 붙는다)
                           dontWait=false,         충돌하면 기다린다
                           reportMemoryError=true, 잠금 테이블이 차면 ERROR
                           &locallock,
                           logLockFailure=false)
         결과  LOCKACQUIRE_OK             처음 얻었다
               LOCKACQUIRE_ALREADY_HELD   이미 가졌지만 무효화 흡수가 끝났는지 모른다
               LOCKACQUIRE_ALREADY_CLEAR  이미 가졌고 흡수도 끝났다

 L134  res != ALREADY_CLEAR 이면
 L136    AcceptInvalidationMessages()   다른 backend 가 커밋한 카탈로그 변경을 반영
 L137    MarkLockClear(locallock)       lockCleared = true (lock.c L1919)
```

잠근 뒤에 무효화 메시지를 받는 순서가 핵심이다. 잠금을 쥔 다음에는 이 테이블의 정의를 바꾸려는 쪽(AccessExclusiveLock 등)이 들어올 수 없으므로, 그 시점에 흡수한 메시지가 마지막 변경까지 다 담고 있다(L118-L133 주석).

```text
 같은 트랜잭션에서 같은 테이블을 두 번 여는 경우

 1 번째  relation_open(t, AccessShareLock)
           LockAcquireExtended -> fast-path 로 얻음, LOCKACQUIRE_OK
           AcceptInvalidationMessages, MarkLockClear
 2 번째  relation_open(t, AccessShareLock)
           LockAcquireExtended L939  nLocks > 0 -> GrantLockLocal, ALREADY_CLEAR
           무효화 흡수를 건너뛴다 (공유 메모리도 보지 않는다)
```

## 결과가 쓰이는 곳

```text
 잡힌 잠금
      --> relation_open 이 바로 RelationIdGetRelation 으로 relcache 를 연다 (access/common/relation.c L58)
      --> 트랜잭션 끝까지 남고 [11] LockReleaseAll 이 푼다

 locallock->lockCleared
      --> 다음 같은 요청이 ALREADY_CLEAR 를 받아 무효화 흡수를 건너뛰게 한다
```

## 다루지 않는 것

`ConditionalLockRelationOid`(L151, `dontWait=true`), 이미 열린 `Relation` 으로 잠그는 `LockRelation`(L246), 세션 잠금 `LockRelationIdForSession`(L391), 무효화 메시지 처리 자체(`utils/cache/inval.c`)는 같은 모양의 곁가지라 다루지 않았다.
