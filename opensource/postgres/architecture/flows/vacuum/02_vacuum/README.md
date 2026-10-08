# vacuum

상위: [vacuum](../README.md)

**수동 VACUUM 과 autovacuum 이 함께 쓰는 공통 루틴이다.** 처리할 테이블 목록을 만들고(이름을 줬으면 그 테이블과 파티션, 안 줬으면 DB 의 모든 테이블), **호출자가 열어 둔 트랜잭션을 먼저 커밋해 버린 뒤** 테이블마다 [05] `vacuum_rel` 이 트랜잭션을 새로 열고 닫게 한다. 잠금을 가능한 한 빨리 풀기 위해서다(L573-L576 주석). 한 트랜잭션으로 모든 테이블을 돌면 2PL 때문에 끝날 때까지 DB 전체를 잠근 셈이 된다(`vacuum_rel` 머리 주석 L2010-L2013). 그래서 VACUUM 은 트랜잭션 블록 안에서 실행할 수 없다(L513-L516 주석). 다 끝나면 [13] 의 `vac_update_datfrozenxid` 로 DB 단위 `datfrozenxid` 를 올린다.

## 위치

`commands` / `vacuum.c` L499-L726 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L499-L726))

## 실제 코드

`commands` / `vacuum.c` L499-L726 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L499-L726))

```c
// vacuum.c L499-L726
void
vacuum(List *relations, VacuumParams *params, BufferAccessStrategy bstrategy,
	   MemoryContext vac_context, bool isTopLevel)
{
	static bool in_vacuum = false;

	const char *stmttype;
	volatile bool in_outer_xact,
				use_own_xacts;

	Assert(params != NULL);

	stmttype = (params->options & VACOPT_VACUUM) ? "VACUUM" : "ANALYZE";

	/*
	 * We cannot run VACUUM inside a user transaction block; if we were inside
	 * a transaction, then our commit- and start-transaction-command calls
	 * would not have the intended effect!	There are numerous other subtle
	 * dependencies on this, too.
	 *
	 * ANALYZE (without VACUUM) can run either way.
	 */
	if (params->options & VACOPT_VACUUM)
	{
		PreventInTransactionBlock(isTopLevel, stmttype);
		in_outer_xact = false;
	}
	else
		in_outer_xact = IsInTransactionBlock(isTopLevel);

	// ... (L529-L538 생략: VACUUM 안에서 VACUUM 을 다시 부르는 재귀 금지)

	/*
	 * Build list of relation(s) to process, putting any new data in
	 * vac_context for safekeeping.
	 */
	if (params->options & VACOPT_ONLY_DATABASE_STATS)
	{
		/* We don't process any tables in this case */
		Assert(relations == NIL);
	}
	else if (relations != NIL)
	{
		List	   *newrels = NIL;
		ListCell   *lc;

		foreach(lc, relations)
		{
			VacuumRelation *vrel = lfirst_node(VacuumRelation, lc);
			List	   *sublist;
			MemoryContext old_context;

			sublist = expand_vacuum_rel(vrel, vac_context, params->options);
			old_context = MemoryContextSwitchTo(vac_context);
			newrels = list_concat(newrels, sublist);
			MemoryContextSwitchTo(old_context);
		}
		relations = newrels;
	}
	else
		relations = get_all_vacuum_rels(vac_context, params->options);

	/*
	 * Decide whether we need to start/commit our own transactions.
	 *
	 * For VACUUM (with or without ANALYZE): always do so, so that we can
	 * release locks as soon as possible.  (We could possibly use the outer
	 * transaction for a one-table VACUUM, but handling TOAST tables would be
	 * problematic.)
	 *
	 * For ANALYZE (no VACUUM): if inside a transaction block, we cannot
	 * start/commit our own transactions.  Also, there's no need to do so if
	 * only processing one relation.  For multiple relations when not within a
	 * transaction block, and also in an autovacuum worker, use own
	 * transactions so we can release locks sooner.
	 */
	if (params->options & VACOPT_VACUUM)
		use_own_xacts = true;
	else
	{
		// ... (L588-L596 생략: ANALYZE 만 할 때 자체 트랜잭션을 쓸지 정하는 분기)
	}

	/*
	 * vacuum_rel expects to be entered with no transaction active; it will
	 * start and commit its own transaction.  But we are called by an SQL
	 * command, and so we are executing inside a transaction already. We
	 * commit the transaction started in PostgresMain() here, and start
	 * another one before exiting to match the commit waiting for us back in
	 * PostgresMain().
	 */
	if (use_own_xacts)
	{
		Assert(!in_outer_xact);

		/* ActiveSnapshot is not set by autovacuum */
		if (ActiveSnapshotSet())
			PopActiveSnapshot();

		/* matches the StartTransaction in PostgresMain() */
		CommitTransactionCommand();
	}

	/* Turn vacuum cost accounting on or off, and set/clear in_vacuum */
	PG_TRY();
	{
		ListCell   *cur;

		// ... (L624-L630 생략: 비용 기반 지연 상태 초기화)

		/*
		 * Loop to process each selected relation.
		 */
		foreach(cur, relations)
		{
			VacuumRelation *vrel = lfirst_node(VacuumRelation, cur);

			if (params->options & VACOPT_VACUUM)
			{
				VacuumParams params_copy;

				/*
				 * vacuum_rel() scribbles on the parameters, so give it a copy
				 * to avoid affecting other relations.
				 */
				memcpy(&params_copy, params, sizeof(VacuumParams));

				if (!vacuum_rel(vrel->oid, vrel->relation, &params_copy, bstrategy))
					continue;
			}

			// ... (L653-L685 생략: ANALYZE (자체 트랜잭션이면 열고 닫는다))

			// ... (L687-L691 생략: failsafe 플래그를 테이블마다 다시 내린다)
		}
	}
	PG_FINALLY();
	{
		in_vacuum = false;
		VacuumCostActive = false;
		VacuumFailsafeActive = false;
		VacuumCostBalance = 0;
	}
	PG_END_TRY();

	/*
	 * Finish up processing.
	 */
	if (use_own_xacts)
	{
		/* here, we are not in a transaction */

		/*
		 * This matches the CommitTransaction waiting for us in
		 * PostgresMain().
		 */
		StartTransactionCommand();
	}

	if ((params->options & VACOPT_VACUUM) &&
		!(params->options & VACOPT_SKIP_DATABASE_STATS))
	{
		/*
		 * Update pg_database.datfrozenxid, and truncate pg_xact if possible.
		 */
		vac_update_datfrozenxid();
	}

}
```

## 동작 흐름

```text
 vacuum(relations, params, bstrategy, vac_context, isTopLevel)
 L523  VACUUM 이면 PreventInTransactionBlock                BEGIN 안에서 VACUUM 은 ERROR
 L560  이름이 있으면 expand_vacuum_rel                      파티션 테이블이면 파티션들까지 펼친다
 L568  없으면 get_all_vacuum_rels                            pg_class 에서 vacuum 가능한 relkind 전부
 L585  VACUUM 이면 use_own_xacts = true
 L616  CommitTransactionCommand()                           PostgresMain 이 연 트랜잭션을 여기서 끝낸다
 L635  foreach (relations)
         L649  [05] vacuum_rel(vrel->oid, ...)             안에서 Start/CommitTransactionCommand
 L714  StartTransactionCommand()                            PostgresMain 의 finish_xact_command 짝을 맞춘다
 L723  vac_update_datfrozenxid()                            SKIP_DATABASE_STATS 가 아니면
```

트랜잭션 경계가 어떻게 이어지는지가 이 함수의 핵심이다. `VACUUM a, b;` 한 문장에서 트랜잭션이 네 번 열리고 닫힌다(a, b 에 TOAST 테이블이 없을 때. 있으면 [05] 가 TOAST 테이블마다 트랜잭션을 하나 더 연다).

```text
 PostgresMain / exec_simple_query
   start_xact_command                  T0 시작
   ExecVacuum -> vacuum
     L616  CommitTransactionCommand     T0 커밋 (아무것도 안 했다)
     vacuum_rel(a)
       L2040 StartTransactionCommand    T1 시작   a 를 ShareUpdateExclusiveLock
       ...
       L2334 CommitTransactionCommand   T1 커밋   트랜잭션 잠금, PROC_IN_VACUUM 해제
       L2360 UnlockRelationIdForSession          L2191 에서 잡은 a 의 세션 잠금 해제
     vacuum_rel(b)                      T2 시작 ... T2 커밋
     L714  StartTransactionCommand      T3 시작
     L723  vac_update_datfrozenxid      T3 안에서 pg_database 를 제자리 갱신
   finish_xact_command                 T3 커밋
```

## 결과가 쓰이는 곳

```text
 테이블마다 끝나는 트랜잭션
      --> 잠금과 스냅샷이 테이블 단위로 풀린다. a 를 끝낸 뒤 b 를 하는 동안 a 는 막지 않는다
      --> PROC_IN_VACUUM 과 xmin 이 테이블마다 다시 잡힌다 -> 뒤 테이블의 OldestXmin 이 더 새롭다
 vac_update_datfrozenxid
      --> pg_database.datfrozenxid, pg_xact 잘라내기 ([13] 참고)
```

## 다루지 않는 것

ANALYZE(`analyze_rel`)와 그 트랜잭션 분기, 비용 기반 지연 계산(`VacuumUpdateCosts`), 파티션 펼치기와 권한 검사(`expand_vacuum_rel`, `vacuum_is_permitted_for_relation`)의 세부는 다루지 않았다.
