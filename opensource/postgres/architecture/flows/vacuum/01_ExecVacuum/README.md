# ExecVacuum

상위: [vacuum](../README.md)

**수동 `VACUUM` / `ANALYZE` 문장의 입구다.** 문장의 옵션 목록을 하나씩 읽어 `VacuumParams` 의 비트(`VACOPT_*`)와 값으로 바꾸고, 옵션끼리 모순이 없는지 검사하고, 여러 트랜잭션에 걸쳐 살아남을 메모리 문맥과 ring buffer 전략을 만든 뒤 공통 루틴 [02] `vacuum()` 에 넘긴다. autovacuum 은 이 함수를 거치지 않고 같은 `VacuumParams` 를 직접 채운다.

## 위치

`commands` / `vacuum.c` L161-L475 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L161-L475))

## 실제 코드

`commands` / `vacuum.c` L161-L475 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L161-L475))

```c
// vacuum.c L161-L475
void
ExecVacuum(ParseState *pstate, VacuumStmt *vacstmt, bool isTopLevel)
// ... (L163-L195 생략: 지역 변수와 params 기본값 (index_cleanup, truncate 는 UNSPECIFIED, nworkers 0))
	/* Parse options list */
	foreach(lc, vacstmt->options)
	{
		DefElem    *opt = (DefElem *) lfirst(lc);

		/* Parse common options for VACUUM and ANALYZE */
		if (strcmp(opt->defname, "verbose") == 0)
			verbose = defGetBoolean(opt);
		// ... (L204-L237 생략: skip_locked, buffer_usage_limit 파싱과 ANALYZE 전용 오류)
		/* Parse options available on VACUUM */
		else if (strcmp(opt->defname, "analyze") == 0)
			analyze = defGetBoolean(opt);
		else if (strcmp(opt->defname, "freeze") == 0)
			freeze = defGetBoolean(opt);
		else if (strcmp(opt->defname, "full") == 0)
			full = defGetBoolean(opt);
		else if (strcmp(opt->defname, "disable_page_skipping") == 0)
			disable_page_skipping = defGetBoolean(opt);
		// ... (L247-L300 생략: index_cleanup, process_main/toast, truncate, parallel)
		else if (strcmp(opt->defname, "skip_database_stats") == 0)
			skip_database_stats = defGetBoolean(opt);
		else if (strcmp(opt->defname, "only_database_stats") == 0)
			only_database_stats = defGetBoolean(opt);
		else
			ereport(ERROR,
					(errcode(ERRCODE_SYNTAX_ERROR),
					 errmsg("unrecognized %s option \"%s\"",
							"VACUUM", opt->defname),
					 parser_errposition(pstate, opt->location)));
	}

	/* Set vacuum options */
	params.options =
		(vacstmt->is_vacuumcmd ? VACOPT_VACUUM : VACOPT_ANALYZE) |
		(verbose ? VACOPT_VERBOSE : 0) |
		(skip_locked ? VACOPT_SKIP_LOCKED : 0) |
		(analyze ? VACOPT_ANALYZE : 0) |
		(freeze ? VACOPT_FREEZE : 0) |
		(full ? VACOPT_FULL : 0) |
		(disable_page_skipping ? VACOPT_DISABLE_PAGE_SKIPPING : 0) |
		(process_main ? VACOPT_PROCESS_MAIN : 0) |
		(process_toast ? VACOPT_PROCESS_TOAST : 0) |
		(skip_database_stats ? VACOPT_SKIP_DATABASE_STATS : 0) |
		(only_database_stats ? VACOPT_ONLY_DATABASE_STATS : 0);

	// ... (L327-L398 생략: 옵션 조합 검사 (FULL 과 parallel, FULL 과 DISABLE_PAGE_SKIPPING 등))

	/*
	 * All freeze ages are zero if the FREEZE option is given; otherwise pass
	 * them as -1 which means to use the default values.
	 */
	if (params.options & VACOPT_FREEZE)
	{
		params.freeze_min_age = 0;
		params.freeze_table_age = 0;
		params.multixact_freeze_min_age = 0;
		params.multixact_freeze_table_age = 0;
	}
	else
	{
		params.freeze_min_age = -1;
		params.freeze_table_age = -1;
		params.multixact_freeze_min_age = -1;
		params.multixact_freeze_table_age = -1;
	}

	/* user-invoked vacuum is never "for wraparound" */
	params.is_wraparound = false;

	/* user-invoked vacuum uses VACOPT_VERBOSE instead of log_min_duration */
	params.log_min_duration = -1;

	/*
	 * Later, in vacuum_rel(), we check if a reloption override was specified.
	 */
	params.max_eager_freeze_failure_rate = vacuum_max_eager_freeze_failure_rate;

	/*
	 * Create special memory context for cross-transaction storage.
	 *
	 * Since it is a child of PortalContext, it will go away eventually even
	 * if we suffer an error; there's no need for special abort cleanup logic.
	 */
	vac_context = AllocSetContextCreate(PortalContext,
										"Vacuum",
										ALLOCSET_DEFAULT_SIZES);

	/*
	 * Make a buffer strategy object in the cross-transaction memory context.
	 * We needn't bother making this for VACUUM (FULL) or VACUUM
	 * (ONLY_DATABASE_STATS) as they'll not make use of it.  VACUUM (FULL,
	 * ANALYZE) is possible, so we'd better ensure that we make a strategy
	 * when we see ANALYZE.
	 */
	if ((params.options & (VACOPT_ONLY_DATABASE_STATS |
						   VACOPT_FULL)) == 0 ||
		(params.options & VACOPT_ANALYZE) != 0)
	{

		MemoryContext old_context = MemoryContextSwitchTo(vac_context);

		Assert(ring_size >= -1);

		/*
		 * If BUFFER_USAGE_LIMIT was specified by the VACUUM or ANALYZE
		 * command, it overrides the value of VacuumBufferUsageLimit.  Either
		 * value may be 0, in which case GetAccessStrategyWithSize() will
		 * return NULL, effectively allowing full use of shared buffers.
		 */
		if (ring_size == -1)
			ring_size = VacuumBufferUsageLimit;

		bstrategy = GetAccessStrategyWithSize(BAS_VACUUM, ring_size);

		MemoryContextSwitchTo(old_context);
	}

	/* Now go through the common routine */
	vacuum(vacstmt->rels, &params, bstrategy, vac_context, isTopLevel);

	/* Finally, clean up the vacuum memory context */
	MemoryContextDelete(vac_context);
}
```

## 동작 흐름

```text
 ExecVacuum(pstate, vacstmt, isTopLevel)
 L197  옵션 목록을 돌며 bool 변수와 params 필드를 채운다
 L314  params.options = VACOPT_VACUUM | VERBOSE | FREEZE | FULL | ...    비트 하나에 옵션 하나
 L327  옵션 조합 검사                                                      어긋나면 ERROR
 L404  FREEZE 면 freeze_min_age = freeze_table_age = 0                    "전부 지금 얼려라"
       아니면 -1                                                           [07] 이 GUC 값으로 바꾼다
 L420  is_wraparound = false                                               수동 VACUUM 은 wraparound 용이 아니다
 L436  vac_context = "Vacuum" 메모리 문맥 (PortalContext 의 자식)          트랜잭션을 넘어 살아남는다
 L465  bstrategy = GetAccessStrategyWithSize(BAS_VACUUM, ring_size)
 L471  [02] vacuum(vacstmt->rels, &params, bstrategy, vac_context, isTopLevel)
 L474  MemoryContextDelete(vac_context)
```

같은 VACUUM 이라도 옵션에 따라 [07] 이하로 내려가는 값이 달라진다. 자주 쓰는 네 가지를 나란히 놓았다.

```text
 statement                 params.options (main bits)              freeze_min_age  freeze_table_age  결과
 VACUUM t                  VACUUM | PROCESS_MAIN | PROCESS_TOAST   -1              -1                GUC 기본값 (50M, 150M)
 VACUUM (FREEZE) t         ... | FREEZE                            0               0                 aggressive, OldestXmin 보다 오래된 XID 를 모두 얼린다
 VACUUM (VERBOSE) t        ... | VERBOSE                           -1              -1                [06] 이 INFO 로 진행을 보고한다
 VACUUM (FULL) t           ... | FULL                              -1              -1                [05] 가 cluster_rel 로 간다 (이 흐름 밖)
```

ring buffer 는 VACUUM 이 테이블 전체를 읽으면서 shared buffers 를 밀어내지 않게 하는 장치다. 크기는 `BUFFER_USAGE_LIMIT` 옵션이 없으면 `vacuum_buffer_usage_limit`(기본 2048 kB, globals.c L149)다.

```text
 ring_size = 2048 kB -> 2048 / 8 = 256 개 버퍼를 돌려 쓴다 (BLCKSZ = 8 kB, storage/buffer/freelist.c L634)
 단 NBuffers / 8 을 넘지 않는다 (L641). shared_buffers 기본 128 MB = 16384 개면 상한 2048 이라 256 그대로
 0 이면 GetAccessStrategyWithSize 가 NULL -> shared buffers 를 제한 없이 쓴다 (L456-L461 주석)
```

## 결과가 쓰이는 곳

```text
 params (VacuumParams)
      --> [02] vacuum 이 테이블마다 복사해서 [05] vacuum_rel 에 넘긴다
      --> freeze_*_age 는 [07] vacuum_get_cutoffs 가 읽는다
 bstrategy
      --> [08] lazy_scan_heap, [12] 의 read stream 이 버퍼를 이 ring 안에서 돌려 쓴다
 vac_context
      --> [02] 가 테이블 목록을 여기 담는다. 테이블마다 트랜잭션이 끝나도 목록이 남는다
```

## 다루지 않는 것

ANALYZE 전용 옵션과 열 목록, `PARALLEL` 옵션이 여는 병렬 인덱스 vacuum, `ONLY_DATABASE_STATS` 의 짧은 길, ring buffer 의 교체 규칙(`freelist.c`)은 다루지 않았다.
