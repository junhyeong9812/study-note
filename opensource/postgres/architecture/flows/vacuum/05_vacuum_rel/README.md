# vacuum_rel

상위: [vacuum](../README.md)

**테이블 하나를 트랜잭션 하나로 vacuum 한다.** 트랜잭션을 열고, lazy vacuum 이면 자기 PGPROC 에 `PROC_IN_VACUUM` 을 세워 다른 VACUUM 의 OldestXmin 계산에서 빠지고, `ShareUpdateExclusiveLock` 으로 테이블을 잠근다. 이 잠금은 SELECT·INSERT·UPDATE·DELETE 와는 충돌하지 않고 다른 VACUUM·DDL 과만 충돌한다. 그 뒤 세션 잠금을 하나 더 걸고 테이블 AM 의 vacuum([06] `heap_vacuum_rel`)을 부르고, 커밋하고, 같은 세션 잠금을 쥔 채로 TOAST 테이블에 대해 자기 자신을 다시 부른다.

## 위치

`commands` / `vacuum.c` L2017-L2364 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L2017-L2364))

## 실제 코드

`commands` / `vacuum.c` L2017-L2364 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L2017-L2364))

```c
// vacuum.c L2017-L2364
static bool
// ... (L2018-L2030 생략: 지역 변수)
	Assert(params != NULL);

	/*
	 * This function scribbles on the parameters, so make a copy early to
	 * avoid affecting the TOAST table (if we do end up recursing to it).
	 */
	memcpy(&toast_vacuum_params, params, sizeof(VacuumParams));

	/* Begin a transaction for vacuuming this relation */
	StartTransactionCommand();

	if (!(params->options & VACOPT_FULL))
	{
		/*
		 * In lazy vacuum, we can set the PROC_IN_VACUUM flag, which lets
		 * other concurrent VACUUMs know that they can ignore this one while
		 * determining their OldestXmin.  (The reason we don't set it during a
		 * full VACUUM is exactly that we may have to run user-defined
		 * functions for functional indexes, and we want to make sure that if
		 * they use the snapshot set above, any tuples it requires can't get
		 * removed from other tables.  An index function that depends on the
		 * contents of other tables is arguably broken, but we won't break it
		 * here by violating transaction semantics.)
		 *
		 * We also set the VACUUM_FOR_WRAPAROUND flag, which is passed down by
		 * autovacuum; it's used to avoid canceling a vacuum that was invoked
		 * in an emergency.
		 *
		 * Note: these flags remain set until CommitTransaction or
		 * AbortTransaction.  We don't want to clear them until we reset
		 * MyProc->xid/xmin, otherwise GetOldestNonRemovableTransactionId()
		 * might appear to go backwards, which is probably Not Good.  (We also
		 * set PROC_IN_VACUUM *before* taking our own snapshot, so that our
		 * xmin doesn't become visible ahead of setting the flag.)
		 */
		LWLockAcquire(ProcArrayLock, LW_EXCLUSIVE);
		MyProc->statusFlags |= PROC_IN_VACUUM;
		if (params->is_wraparound)
			MyProc->statusFlags |= PROC_VACUUM_FOR_WRAPAROUND;
		ProcGlobal->statusFlags[MyProc->pgxactoff] = MyProc->statusFlags;
		LWLockRelease(ProcArrayLock);
	}

	/*
	 * Need to acquire a snapshot to prevent pg_subtrans from being truncated,
	 * cutoff xids in local memory wrapping around, and to have updated xmin
	 * horizons.
	 */
	PushActiveSnapshot(GetTransactionSnapshot());

	/*
	 * Check for user-requested abort.  Note we want this to be inside a
	 * transaction, so xact.c doesn't issue useless WARNING.
	 */
	CHECK_FOR_INTERRUPTS();

	/*
	 * Determine the type of lock we want --- hard exclusive lock for a FULL
	 * vacuum, but just ShareUpdateExclusiveLock for concurrent vacuum. Either
	 * way, we can be sure that no other backend is vacuuming the same table.
	 */
	lmode = (params->options & VACOPT_FULL) ?
		AccessExclusiveLock : ShareUpdateExclusiveLock;

	/* open the relation and get the appropriate lock on it */
	rel = vacuum_open_relation(relid, relation, params->options,
							   params->log_min_duration >= 0, lmode);

	/* leave if relation could not be opened or locked */
	if (!rel)
	{
		PopActiveSnapshot();
		CommitTransactionCommand();
		return false;
	}

	// ... (L2107-L2178 생략: 권한, relkind, 남의 임시 테이블, 파티션 부모 검사 (해당하면 커밋하고 return))

	/*
	 * Get a session-level lock too. This will protect our access to the
	 * relation across multiple transactions, so that we can vacuum the
	 * relation's TOAST table (if any) secure in the knowledge that no one is
	 * deleting the parent relation.
	 *
	 * NOTE: this cannot block, even if someone else is waiting for access,
	 * because the lock manager knows that both lock requests are from the
	 * same process.
	 */
	lockrelid = rel->rd_lockInfo.lockRelId;
	LockRelationIdForSession(&lockrelid, lmode);

	// ... (L2193-L2265 생략: index_cleanup, truncate 옵션을 reloption 과 GUC 로 채운다)

	/*
	 * Remember the relation's TOAST relation for later, if the caller asked
	 * us to process it.  In VACUUM FULL, though, the toast table is
	 * automatically rebuilt by cluster_rel so we shouldn't recurse to it,
	 * unless PROCESS_MAIN is disabled.
	 */
	if ((params->options & VACOPT_PROCESS_TOAST) != 0 &&
		((params->options & VACOPT_FULL) == 0 ||
		 (params->options & VACOPT_PROCESS_MAIN) == 0))
		toast_relid = rel->rd_rel->reltoastrelid;
	else
		toast_relid = InvalidOid;

	/*
	 * Switch to the table owner's userid, so that any index functions are run
	 * as that user.  Also lock down security-restricted operations and
	 * arrange to make GUC variable changes local to this command. (This is
	 * unnecessary, but harmless, for lazy VACUUM.)
	 */
	GetUserIdAndSecContext(&save_userid, &save_sec_context);
	SetUserIdAndSecContext(rel->rd_rel->relowner,
						   save_sec_context | SECURITY_RESTRICTED_OPERATION);
	save_nestlevel = NewGUCNestLevel();
	RestrictSearchPath();

	/*
	 * If PROCESS_MAIN is set (the default), it's time to vacuum the main
	 * relation.  Otherwise, we can skip this part.  If processing the TOAST
	 * table is required (e.g., PROCESS_TOAST is set), we force PROCESS_MAIN
	 * to be set when we recurse to the TOAST table.
	 */
	if (params->options & VACOPT_PROCESS_MAIN)
	{
		/*
		 * Do the actual work --- either FULL or "lazy" vacuum
		 */
		if (params->options & VACOPT_FULL)
		{
			ClusterParams cluster_params = {0};

			if ((params->options & VACOPT_VERBOSE) != 0)
				cluster_params.options |= CLUOPT_VERBOSE;

			/* VACUUM FULL is now a variant of CLUSTER; see cluster.c */
			cluster_rel(rel, InvalidOid, &cluster_params);
			/* cluster_rel closes the relation, but keeps lock */

			rel = NULL;
		}
		else
			table_relation_vacuum(rel, params, bstrategy);
	}

	/* Roll back any GUC changes executed by index functions */
	AtEOXact_GUC(false, save_nestlevel);

	/* Restore userid and security context */
	SetUserIdAndSecContext(save_userid, save_sec_context);

	/* all done with this class, but hold lock until commit */
	if (rel)
		relation_close(rel, NoLock);

	/*
	 * Complete the transaction and free all temporary memory used.
	 */
	PopActiveSnapshot();
	CommitTransactionCommand();

	/*
	 * If the relation has a secondary toast rel, vacuum that too while we
	 * still hold the session lock on the main table.  Note however that
	 * "analyze" will not get done on the toast table.  This is good, because
	 * the toaster always uses hardcoded index access and statistics are
	 * totally unimportant for toast relations.
	 */
	if (toast_relid != InvalidOid)
	{
		/*
		 * Force VACOPT_PROCESS_MAIN so vacuum_rel() processes it.  Likewise,
		 * set toast_parent so that the privilege checks are done on the main
		 * relation.  NB: This is only safe to do because we hold a session
		 * lock on the main relation that prevents concurrent deletion.
		 */
		toast_vacuum_params.options |= VACOPT_PROCESS_MAIN;
		toast_vacuum_params.toast_parent = relid;

		vacuum_rel(toast_relid, NULL, &toast_vacuum_params, bstrategy);
	}

	/*
	 * Now release the session-level lock on the main table.
	 */
	UnlockRelationIdForSession(&lockrelid, lmode);

	/* Report that we really did it. */
	return true;
}
```

## 동작 흐름

```text
 vacuum_rel(relid, relation, params, bstrategy)
 L2037  toast 용 params 사본
 L2040  StartTransactionCommand                         테이블마다 새 트랜잭션
 L2042  FULL 이 아니면 (lazy vacuum)
          L2066  ProcArrayLock EXCLUSIVE
          L2067  MyProc->statusFlags |= PROC_IN_VACUUM
          L2069  wraparound 용이면 PROC_VACUUM_FOR_WRAPAROUND
 L2079  PushActiveSnapshot(GetTransactionSnapshot())    PROC_IN_VACUUM 을 세운 "뒤"에 스냅샷
 L2092  lmode = FULL ? AccessExclusiveLock : ShareUpdateExclusiveLock
 L2096  vacuum_open_relation(..., lmode)                SKIP_LOCKED 면 못 잡을 때 건너뛴다
 L2191  LockRelationIdForSession(lmode)                 트랜잭션을 넘어 유지되는 잠금
 L2286  테이블 소유자로 userid 전환, SECURITY_RESTRICTED_OPERATION
 L2303  FULL 이면 cluster_rel                          (이 흐름 밖)
 L2317  아니면 table_relation_vacuum -> [06] heap_vacuum_rel   (heapam_handler.c L2656)
 L2334  CommitTransactionCommand                        PROC_IN_VACUUM 도 여기서 내려간다
 L2354  TOAST 테이블이 있으면 vacuum_rel(toast_relid)   세션 잠금이 부모를 지킨다
 L2360  UnlockRelationIdForSession
```

`ShareUpdateExclusiveLock` 은 heavyweight lock 의 4 번 모드다. 이 모드가 무엇과 부딪히는지가 "VACUUM 은 서비스를 멈추지 않는다"의 근거다([heavyweight lock](../../heavyweight-lock/README.md)의 `LockConflicts` 표).

```text
 held by others ->  AS   RS   RX   SUX  S    SRX  X    AX
 VACUUM (SUX=4)     .    .    .    X    X    X    X    X

 SELECT (AS), SELECT FOR UPDATE (RS), INSERT/UPDATE/DELETE (RX)  -> 같이 돈다
 다른 VACUUM, ANALYZE, CREATE INDEX CONCURRENTLY (SUX)            -> 기다리거나 SKIP_LOCKED 로 건너뛴다
 CREATE INDEX (S), ALTER TABLE, DROP TABLE (AX)                  -> 기다린다
```

`PROC_IN_VACUUM` 을 세우는 이유는 L2044-L2065 주석과 [07] 의 L1144-L1150 주석에 있다. OldestXmin 은 "어떤 튜플을 남겨야 하나"를 정하는 값인데, lazy vacuum 은 자기 XID 를 어디에도 쓰지 않으므로(보통 XID 가 없다) 무시해도 안전하다. `ComputeXidHorizons` 가 이 플래그가 선 backend 를 건너뛴다(procarray.c L1831).

```text
 backend   xmin   statusFlags        ComputeXidHorizons 에서
 B1        900    0                  포함 -> OldestXmin <= 900
 V1 (t1)   800    PROC_IN_VACUUM     무시
 V2 (t2)   -      PROC_IN_VACUUM     지금 OldestXmin 을 계산하는 쪽

 결과 OldestXmin 은 B1 의 900 이 정한다. V1 이 큰 테이블을 오래 vacuum 해도 800 으로 끌려 내려가지 않는다
```

## 결과가 쓰이는 곳

```text
 PROC_IN_VACUUM
      --> ComputeXidHorizons 가 건너뛴다 (procarray.c L1831)
      --> 커밋 때 [커밋 흐름 10](../../commit/10_ProcArrayEndTransaction/README.md) 이 PROC_VACUUM_STATE_MASK 를 지운다
 ShareUpdateExclusiveLock (트랜잭션 + 세션)
      --> 같은 테이블의 다른 VACUUM 을 막는다. [07] 의 주석이 "한 테이블에는 VACUUM 하나"를 전제한다
 테이블마다의 커밋
      --> 이 테이블의 [13] pg_class 제자리 갱신이 이 트랜잭션 안에서 일어난다
```

## 다루지 않는 것

`VACUUM FULL` 의 `cluster_rel`, 권한 검사(`vacuum_is_permitted_for_relation`), `vacuum_open_relation` 의 SKIP_LOCKED 처리, index_cleanup·truncate 의 reloption 해석, 보안 문맥 전환의 이유(인덱스 표현식 함수)는 다루지 않았다.
