# do_autovacuum

상위: [vacuum](../README.md)

**autovacuum worker 가 DB 하나에 접속해서 하는 일 전부다.** pg_class 를 훑어 테이블마다 `relation_needs_vacanalyze` 로 "죽은 행이 임계값을 넘었나, wraparound 위험인가"를 판정해 목록을 만들고, 목록의 테이블마다 다른 worker 가 이미 잡지 않았는지 공유 메모리에서 확인한 뒤 자기 이름을 걸고, 통계를 한 번 더 확인하고, `autovacuum_do_vac_analyze` 로 수동 VACUUM 과 같은 [02] `vacuum()` 을 부른다. 테이블 하나에서 ERROR 가 나도 그 트랜잭션만 abort 하고 다음 테이블로 간다.

## 위치

`postmaster` / `autovacuum.c` L1884-L2599 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L1884-L2599))

## 실제 코드

첫 번째 pg_class 스캔이다. 보통 테이블과 materialized view 를 보고, TOAST 테이블은 두 번째 스캔(L2086-L2148)에서 따로 본다.

`postmaster` / `autovacuum.c` L1994-L2048 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L1994-L2048))

```c
// autovacuum.c L1994-L2048
	while ((tuple = heap_getnext(relScan, ForwardScanDirection)) != NULL)
	{
		Form_pg_class classForm = (Form_pg_class) GETSTRUCT(tuple);
		PgStat_StatTabEntry *tabentry;
		AutoVacOpts *relopts;
		Oid			relid;
		bool		dovacuum;
		bool		doanalyze;
		bool		wraparound;

		if (classForm->relkind != RELKIND_RELATION &&
			classForm->relkind != RELKIND_MATVIEW)
			continue;

		relid = classForm->oid;

		// ... (L2010-L2033 생략: 다른 backend 의 임시 테이블은 건너뛰고, 버려진 것은 따로 모아 지운다)

		/* Fetch reloptions and the pgstat entry for this table */
		relopts = extract_autovac_opts(tuple, pg_class_desc);
		tabentry = pgstat_fetch_stat_tabentry_ext(classForm->relisshared,
												  relid);

		/* Check if it needs vacuum or analyze */
		relation_needs_vacanalyze(relid, relopts, classForm, tabentry,
								  effective_multixact_freeze_max_age,
								  &dovacuum, &doanalyze, &wraparound);

		/* Relations that need work are added to table_oids */
		if (dovacuum || doanalyze)
			table_oids = lappend_oid(table_oids, relid);

```

목록의 테이블마다 다른 worker 와 겹치지 않게 자기 이름을 건다.

`postmaster` / `autovacuum.c` L2337-L2379 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L2337-L2379))

```c
// autovacuum.c L2337-L2379
		LWLockAcquire(AutovacuumScheduleLock, LW_EXCLUSIVE);
		LWLockAcquire(AutovacuumLock, LW_SHARED);

		/*
		 * Check whether the table is being vacuumed concurrently by another
		 * worker.
		 */
		skipit = false;
		dlist_foreach(iter, &AutoVacuumShmem->av_runningWorkers)
		{
			WorkerInfo	worker = dlist_container(WorkerInfoData, wi_links, iter.cur);

			/* ignore myself */
			if (worker == MyWorkerInfo)
				continue;

			/* ignore workers in other databases (unless table is shared) */
			if (!worker->wi_sharedrel && worker->wi_dboid != MyDatabaseId)
				continue;

			if (worker->wi_tableoid == relid)
			{
				skipit = true;
				found_concurrent_worker = true;
				break;
			}
		}
		LWLockRelease(AutovacuumLock);
		if (skipit)
		{
			LWLockRelease(AutovacuumScheduleLock);
			continue;
		}

		/*
		 * Store the table's OID in shared memory before releasing the
		 * schedule lock, so that other workers don't try to vacuum it
		 * concurrently.  (We claim it here so as not to hold
		 * AutovacuumScheduleLock while rechecking the stats.)
		 */
		MyWorkerInfo->wi_tableoid = relid;
		MyWorkerInfo->wi_sharedrel = isshared;
		LWLockRelease(AutovacuumScheduleLock);
```

그다음 통계를 다시 확인하고(`table_recheck_autovac`, L2388) 수동 VACUUM 과 같은 길로 넘긴다.

`postmaster` / `autovacuum.c` L2451-L2458 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L2451-L2458))

```c
// autovacuum.c L2451-L2458
		PG_TRY();
		{
			/* Use PortalContext for any per-table allocations */
			MemoryContextSwitchTo(PortalContext);

			/* have at it */
			autovacuum_do_vac_analyze(tab, bstrategy);

```

`postmaster` / `autovacuum.c` L3172-L3199 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L3172-L3199))

```c
// autovacuum.c L3172-L3199
static void
autovacuum_do_vac_analyze(autovac_table *tab, BufferAccessStrategy bstrategy)
{
	RangeVar   *rangevar;
	VacuumRelation *rel;
	List	   *rel_list;
	MemoryContext vac_context;
	MemoryContext old_context;

	/* Let pgstat know what we're doing */
	autovac_report_activity(tab);

	/* Create a context that vacuum() can use as cross-transaction storage */
	vac_context = AllocSetContextCreate(CurrentMemoryContext,
										"Vacuum",
										ALLOCSET_DEFAULT_SIZES);

	/* Set up one VacuumRelation target, identified by OID, for vacuum() */
	old_context = MemoryContextSwitchTo(vac_context);
	rangevar = makeRangeVar(tab->at_nspname, tab->at_relname, -1);
	rel = makeVacuumRelation(rangevar, tab->at_relid, NIL);
	rel_list = list_make1(rel);
	MemoryContextSwitchTo(old_context);

	vacuum(rel_list, &tab->at_params, bstrategy, vac_context, true);

	MemoryContextDelete(vac_context);
}
```

판정의 핵심인 임계값 계산이다.

`postmaster` / `autovacuum.c` L3056-L3148 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L3056-L3148))

```c
// autovacuum.c L3056-L3148
	/* Force vacuum if table is at risk of wraparound */
	xidForceLimit = recentXid - freeze_max_age;
	if (xidForceLimit < FirstNormalTransactionId)
		xidForceLimit -= FirstNormalTransactionId;
	relfrozenxid = classForm->relfrozenxid;
	force_vacuum = (TransactionIdIsNormal(relfrozenxid) &&
					TransactionIdPrecedes(relfrozenxid, xidForceLimit));
	// ... (L3063-L3072 생략: MultiXact 기준의 강제 vacuum)
	// ... (L3073-L3089 생략: autovacuum_enabled = off 인 테이블과 판정 조건 설명)
	if (PointerIsValid(tabentry) && AutoVacuumingActive())
	{
		float4		pcnt_unfrozen = 1;
		float4		reltuples = classForm->reltuples;
		int32		relpages = classForm->relpages;
		int32		relallfrozen = classForm->relallfrozen;

		vactuples = tabentry->dead_tuples;
		instuples = tabentry->ins_since_vacuum;
		anltuples = tabentry->mod_since_analyze;

		/* If the table hasn't yet been vacuumed, take reltuples as zero */
		if (reltuples < 0)
			reltuples = 0;
// ... (L3104-L3121 생략: insert 기준 임계값에 쓰는 얼지 않은 비율 계산)
		vacthresh = (float4) vac_base_thresh + vac_scale_factor * reltuples;
		if (vac_max_thresh >= 0 && vacthresh > (float4) vac_max_thresh)
			vacthresh = (float4) vac_max_thresh;

		// ... (L3126-L3143 생략: insert, analyze 임계값과 DEBUG3 로그)
		/* Determine if this table needs vacuum or analyze. */
		*dovacuum = force_vacuum || (vactuples > vacthresh) ||
			(vac_ins_base_thresh >= 0 && instuples > vacinsthresh);
		*doanalyze = (anltuples > anlthresh);
	}
```

## 동작 흐름

```text
 AutoVacWorkerMain (L1376)  launcher 가 정한 DB 에 InitPostgres  -> do_autovacuum (L1590)

 do_autovacuum
 L1915  StartTransactionCommand
 L1994  pg_class 1 차 스캔 (RELATION, MATVIEW)
          L2041  relation_needs_vacanalyze -> dovacuum, doanalyze, wraparound
          L2047  필요하면 table_oids 에 추가
 L2093  pg_class 2 차 스캔 (TOASTVALUE)                    TOAST 는 부모와 따로 판정한다
 L2278  bstrategy = ring buffer (vacuum_buffer_usage_limit)  worker 의 모든 테이블이 같은 ring
 L2291  foreach (table_oids)
          L2337  AutovacuumScheduleLock
          L2357  다른 worker 의 wi_tableoid 가 같으면 건너뛴다
          L2377  MyWorkerInfo->wi_tableoid = relid           자기 이름을 건다
          L2388  table_recheck_autovac                       통계를 다시 읽어 아직 필요한지
                   L2839  options = VACUUM | PROCESS_MAIN | SKIP_DATABASE_STATS | ANALYZE?
                          wraparound 가 아니면 SKIP_LOCKED
          L2457  autovacuum_do_vac_analyze -> [02] vacuum(rel_list, ...)   (L3196)
          L2467  ERROR 면 PG_CATCH: AbortOutOfAnyTransaction, 다음 테이블
 L2595  vac_update_datfrozenxid                              테이블마다 하지 않고 끝에 한 번
 L2598  CommitTransactionCommand
```

죽은 행 기준의 임계값은 `base + scale * reltuples` 이고 상한이 있다(L3122-L3124). 기본값은 base 50, scale 0.2, 상한 1 억이다(guc_tables.c L3545, L4099, L3554).

```text
 vacthresh = autovacuum_vacuum_threshold + autovacuum_vacuum_scale_factor * reltuples
           = 50 + 0.2 * reltuples, 단 autovacuum_vacuum_max_threshold (100,000,000) 를 넘지 않는다

 table   reltuples       vacthresh                        dead_tuples (pgstat)   dovacuum
 t_s     10,000          50 + 2,000 = 2,050               2,100                  true  (2,100 > 2,050)
 t_m     1,000,000       50 + 200,000 = 200,050           150,000                false
 t_l     1,000,000,000   50 + 200,000,000 -> 100,000,000  120,000,000            true  (상한에 걸림)

 wraparound 이면 임계값과 무관하게 dovacuum = true (L3145 의 force_vacuum)
   force_vacuum = relfrozenxid < recentXid - autovacuum_freeze_max_age   (L3057-L3062)
```

같은 테이블에 worker 둘이 붙지 않게 하는 장치가 `AutovacuumScheduleLock` 과 `wi_tableoid` 다.

```text
 W1  L2337 ScheduleLock 획득
 W1  running workers 중 t 를 잡은 worker 가 없다
 W1  L2377 W1.wi_tableoid = t
 W1  L2379 ScheduleLock 해제
 W2  L2337 ScheduleLock 획득
 W2  L2357 W1.wi_tableoid == t -> skipit, found_concurrent_worker = true, 다음 테이블
 W1  L2457 vacuum(t) ...
```

## 결과가 쓰이는 곳

```text
 vacuum(rel_list, &tab->at_params, ...)
      --> [02] 이하 수동 VACUUM 과 같은 길. 다른 점은 SKIP_DATABASE_STATS 와 SKIP_LOCKED
 wi_tableoid
      --> 다른 worker 의 L2357 검사
 did_vacuum, found_concurrent_worker
      --> L2594 끝의 vac_update_datfrozenxid 를 할지 정한다
```

## 다루지 않는 것

TOAST 테이블의 reloptions 상속, 버려진 임시 테이블 삭제(L2151-L2261), worker 사이 비용 한도 분배(`autovac_recalculate_workers_for_balance`), insert 기준 vacuum 과 ANALYZE 의 임계값, `table_recheck_autovac` 가 freeze 나이를 고르는 규칙은 다루지 않았다.
