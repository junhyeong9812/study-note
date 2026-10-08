# GetTransactionSnapshot

상위: [MVCC 가시성과 스냅샷](../README.md)

**문장 하나가 쓸 스냅샷을 고르는 함수다.** 격리 수준이 갈리는 곳이 여기 한 군데뿐이다. READ COMMITTED 는 부를 때마다 [02] `GetSnapshotData` 로 새로 찍고, REPEATABLE READ 와 SERIALIZABLE 은 트랜잭션의 첫 호출에서 찍은 것을 복사해 두고 끝까지 같은 것을 돌려준다.

## 위치

`utils/time` / `snapmgr.c` L271-L345 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/time/snapmgr.c#L271-L345))

## 실제 코드

함수 전체다. `FirstSnapshotSet` 이 "이 트랜잭션에서 스냅샷을 이미 찍었는가"를 뜻한다.

```c
// snapmgr.c L261-L345
/*
 * GetTransactionSnapshot
 *		Get the appropriate snapshot for a new query in a transaction.
 *
 * Note that the return value points at static storage that will be modified
 * by future calls and by CommandCounterIncrement().  Callers must call
 * RegisterSnapshot or PushActiveSnapshot on the returned snap before doing
 * any other non-trivial work that could invalidate it.
 */
Snapshot
GetTransactionSnapshot(void)
{
	/*
	 * Return historic snapshot if doing logical decoding.
	 *
	 * Historic snapshots are only usable for catalog access, not for
	 * general-purpose queries.  The caller is responsible for ensuring that
	 * the snapshot is used correctly! (PostgreSQL code never calls this
	 * during logical decoding, but extensions can do it.)
	 */
	if (HistoricSnapshotActive())
	{
		/*
		 * We'll never need a non-historic transaction snapshot in this
		 * (sub-)transaction, so there's no need to be careful to set one up
		 * for later calls to GetTransactionSnapshot().
		 */
		Assert(!FirstSnapshotSet);
		return HistoricSnapshot;
	}

	/* First call in transaction? */
	if (!FirstSnapshotSet)
	{
		/*
		 * Don't allow catalog snapshot to be older than xact snapshot.  Must
		 * do this first to allow the empty-heap Assert to succeed.
		 */
		InvalidateCatalogSnapshot();

		Assert(pairingheap_is_empty(&RegisteredSnapshots));
		Assert(FirstXactSnapshot == NULL);

		if (IsInParallelMode())
			elog(ERROR,
				 "cannot take query snapshot during a parallel operation");

		/*
		 * In transaction-snapshot mode, the first snapshot must live until
		 * end of xact regardless of what the caller does with it, so we must
		 * make a copy of it rather than returning CurrentSnapshotData
		 * directly.  Furthermore, if we're running in serializable mode,
		 * predicate.c needs to wrap the snapshot fetch in its own processing.
		 */
		if (IsolationUsesXactSnapshot())
		{
			/* First, create the snapshot in CurrentSnapshotData */
			if (IsolationIsSerializable())
				CurrentSnapshot = GetSerializableTransactionSnapshot(&CurrentSnapshotData);
			else
				CurrentSnapshot = GetSnapshotData(&CurrentSnapshotData);
			/* Make a saved copy */
			CurrentSnapshot = CopySnapshot(CurrentSnapshot);
			FirstXactSnapshot = CurrentSnapshot;
			/* Mark it as "registered" in FirstXactSnapshot */
			FirstXactSnapshot->regd_count++;
			pairingheap_add(&RegisteredSnapshots, &FirstXactSnapshot->ph_node);
		}
		else
			CurrentSnapshot = GetSnapshotData(&CurrentSnapshotData);

		FirstSnapshotSet = true;
		return CurrentSnapshot;
	}

	if (IsolationUsesXactSnapshot())
		return CurrentSnapshot;

	/* Don't allow catalog snapshot to be older than xact snapshot. */
	InvalidateCatalogSnapshot();

	CurrentSnapshot = GetSnapshotData(&CurrentSnapshotData);

	return CurrentSnapshot;
}
```

격리 수준 판정은 매크로 두 개다. `>=` 비교라서 REPEATABLE READ 와 SERIALIZABLE 이 같은 길을 탄다.

`src/include/access` / `xact.h` L36-L52 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xact.h#L36-L52))

```c
// access/xact.h L36-L52
#define XACT_READ_UNCOMMITTED	0
#define XACT_READ_COMMITTED		1
#define XACT_REPEATABLE_READ	2
#define XACT_SERIALIZABLE		3

extern PGDLLIMPORT int DefaultXactIsoLevel;
extern PGDLLIMPORT int XactIsoLevel;

/*
 * We implement three isolation levels internally.
 * The two stronger ones use one snapshot per database transaction;
 * the others use one snapshot per statement.
 * Serializable uses predicate locks in addition to snapshots.
 * These macros should be used to check which isolation level is selected.
 */
#define IsolationUsesXactSnapshot() (XactIsoLevel >= XACT_REPEATABLE_READ)
#define IsolationIsSerializable() (XactIsoLevel == XACT_SERIALIZABLE)
```

`FirstSnapshotSet` 은 트랜잭션이 끝날 때 `AtEOXact_Snapshot` 이 내린다. 다음 트랜잭션의 첫 호출은 다시 L293 의 첫 갈래로 들어간다.

`utils/time` / `snapmgr.c` L1086-L1092 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/time/snapmgr.c#L1086-L1092))

```c
// snapmgr.c L1086-L1092
	ActiveSnapshot = NULL;
	pairingheap_reset(&RegisteredSnapshots);

	CurrentSnapshot = NULL;
	SecondarySnapshot = NULL;

	FirstSnapshotSet = false;
```

RR 이상에서 스냅샷을 다시 찍지 않아도 자기 트랜잭션의 앞선 명령은 보여야 한다. 그 일은 `CommandCounterIncrement` 가 고정된 스냅샷의 `curcid` 만 고쳐서 한다.

`utils/time` / `snapmgr.c` L483-L498 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/time/snapmgr.c#L483-L498))

```c
// snapmgr.c L483-L498
/*
 * SnapshotSetCommandId
 *		Propagate CommandCounterIncrement into the static snapshots, if set
 */
void
SnapshotSetCommandId(CommandId curcid)
{
	if (!FirstSnapshotSet)
		return;

	if (CurrentSnapshot)
		CurrentSnapshot->curcid = curcid;
	if (SecondarySnapshot)
		SecondarySnapshot->curcid = curcid;
	/* Should we do the same with CatalogSnapshot? */
}
```

## 동작 흐름

```text
 L281  HistoricSnapshotActive        논리 디코딩 중이면 HistoricSnapshot 을 그대로 돌려준다
 L293  if (!FirstSnapshotSet)        이 트랜잭션의 첫 호출
 L299    InvalidateCatalogSnapshot   카탈로그 스냅샷이 트랜잭션 스냅샷보다 오래되지 않게
 L304    병렬 모드면 ERROR
 L315    IsolationUsesXactSnapshot() (XactIsoLevel >= XACT_REPEATABLE_READ)
           L318  SERIALIZABLE    GetSerializableTransactionSnapshot (predicate.c 가 감싼다)
           L321  REPEATABLE READ [02] GetSnapshotData(&CurrentSnapshotData)
           L323  CopySnapshot    정적 영역 CurrentSnapshotData 를 복사한다
           L324  FirstXactSnapshot = 복사본
           L326  regd_count++    "등록된" 것으로 쳐서 트랜잭션 끝까지 살린다
           L327  RegisteredSnapshots 힙에 넣는다
 L330    else (READ COMMITTED)   [02] GetSnapshotData, 복사하지 않는다
 L332    FirstSnapshotSet = true
 L333    return

 두 번째 이후 호출
 L336  RR 이상               L337  같은 CurrentSnapshot 을 돌려준다
 L340  READ COMMITTED        InvalidateCatalogSnapshot
 L342                        [02] GetSnapshotData 로 다시 찍는다
```

같은 트랜잭션에서 문장 세 개를 실행하면 격리 수준에 따라 이렇게 갈린다. 다른 트랜잭션 T9 가 두 번째 문장 직전에 커밋했다고 두었다.

```text
 BEGIN; 문장1; (T9 COMMIT) 문장2; 문장3; COMMIT;

 READ COMMITTED
   문장1   L330  GetSnapshotData -> S1
   (T9 커밋)
   문장2   L342  GetSnapshotData -> S2     T9 보임
   문장3   L342  GetSnapshotData -> S3
   COMMIT        AtEOXact_Snapshot, FirstSnapshotSet = false

 REPEATABLE READ / SERIALIZABLE
   문장1   L321  GetSnapshotData -> S1, L323 CopySnapshot, L324 FirstXactSnapshot = S1, L326 regd_count++
   (T9 커밋)
   문장2   L337  S1 그대로                  T9 안 보임
   문장3   L337  S1 그대로
   COMMIT        AtEOXact_Snapshot, FirstSnapshotSet = false

 두 경우 모두 문장 사이 CommandCounterIncrement 는 curcid 만 바꾼다 (SnapshotSetCommandId)
```

스냅샷을 "찍는" 시점은 BEGIN 이 아니다. 이 함수의 첫 호출 시점이다. 그래서 RR 트랜잭션도 BEGIN 직후에 다른 트랜잭션이 커밋한 것은 첫 문장에서 보인다.

```text
 RR 트랜잭션의 스냅샷 시점

 BEGIN ISOLATION LEVEL REPEATABLE READ;   스냅샷 없음 (FirstSnapshotSet = false)
      (T9 COMMIT)
 SELECT ...;                              여기서 첫 GetTransactionSnapshot -> T9 보임
      (T10 COMMIT)
 SELECT ...;                              L337 같은 스냅샷 -> T10 안 보임
```

`exec_simple_query` 는 한 문장에 이 함수를 두 번 부를 수 있다. 분석과 계획에 쓸 스냅샷을 L1163 에서 잡았다가 L1207 에서 내리고, 실행용은 `PortalStart` 가 L481 에서 다시 받는다. postgres.c L1199-L1204 주석은 계획용 스냅샷을 실행에 재사용하면 테이블 잠금 전에 찍은 스냅샷으로 실행하게 되어 이상 현상이 보인다고 적었다. RC 에서는 두 호출이 서로 다른 스냅샷을 만들고, RR 에서는 같은 것을 돌려준다.

```text
 exec_simple_query 의 한 문장 (tcop/postgres.c, tcop/pquery.c)

 postgres.c L1161  analyze_requires_snapshot 이면
 postgres.c L1163    PushActiveSnapshot(GetTransactionSnapshot())   분석, 재작성, 계획용
 postgres.c L1207  PopActiveSnapshot
 postgres.c L1235  PortalStart
 pquery.c   L481     PushActiveSnapshot(GetTransactionSnapshot())   실행용 (PORTAL_ONE_SELECT)
 pquery.c   L496     CreateQueryDesc(..., GetActiveSnapshot(), ...)
 execMain.c L245     estate->es_snapshot = RegisterSnapshot(queryDesc->snapshot)
```

## 결과가 쓰이는 곳

```text
 돌려준 Snapshot
      --> 호출자가 PushActiveSnapshot 이나 RegisterSnapshot 으로 붙잡는다 (주석 L265-L268)
      --> executor 의 es_snapshot 이 되어 [03] heap_getnextslot 까지 내려간다

 FirstXactSnapshot (RR 이상)
      --> RegisteredSnapshots 에 남아 있으므로 SnapshotResetXmin 이 MyProc->xmin 을
          이 스냅샷의 xmin 보다 앞으로 올리지 못한다 (snapmgr.c L942-L952)
      --> vacuum 의 기준선 계산 ComputeXidHorizons 가 그 proc->xmin 을 읽는다 (procarray.c L1802)
          RC 는 문장이 끝나 스냅샷을 놓으면 xmin 이 비거나 앞으로 간다
```

## 다루지 않는 것

SERIALIZABLE 의 `GetSerializableTransactionSnapshot` 과 predicate lock(SSI), 다른 트랜잭션의 스냅샷을 가져오는 `SET TRANSACTION SNAPSHOT` 의 `SetTransactionSnapshot`, 논리 디코딩의 historic snapshot, 카탈로그 스냅샷(`GetCatalogSnapshot`), 활성 스냅샷 스택(`PushActiveSnapshot`)과 `RegisteredSnapshots` 페어링 힙의 내부, `AtEOXact_Snapshot` 의 나머지 정리는 이 흐름의 곁가지라 요약만 했다.
