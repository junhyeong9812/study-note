# pg_plan_query

상위: [쿼리 실행 파이프라인](../README.md)

`Query` 하나를 플래너에 넘겨 **`PlannedStmt` 하나를 받는** 얇은 감싸개다. 유틸리티 문장이면 계획하지 않고 `NULL` 을 돌려준다. 실제로 [01] 이 부르는 것은 목록 버전 `pg_plan_queries` 이고, 그쪽이 유틸리티 문장에는 계획 대신 `utilityStmt` 만 실은 껍데기 `PlannedStmt` 를 만들어 준다. 그래서 다음 단계는 언제나 `PlannedStmt` 목록을 받는다. 짧은 `pg_plan_queries` 와 `planner` 를 이 문서에 함께 담았다.

## 위치

`tcop` / `postgres.c` L883-L960 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L883-L960))

## 실제 코드

`tcop` / `postgres.c` L883-L960 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L883-L960))

```c
// tcop/postgres.c L883-L960
pg_plan_query(Query *querytree, const char *query_string, int cursorOptions,
			  ParamListInfo boundParams)
{
	PlannedStmt *plan;

	/* Utility commands have no plans. */
	if (querytree->commandType == CMD_UTILITY)
		return NULL;

	/* Planner must have a snapshot in case it calls user-defined functions. */
	Assert(ActiveSnapshotSet());

	TRACE_POSTGRESQL_QUERY_PLAN_START();

	if (log_planner_stats)
		ResetUsage();

	/* call the optimizer */
	plan = planner(querytree, query_string, cursorOptions, boundParams);

	if (log_planner_stats)
		ShowUsage("PLANNER STATISTICS");

// ... (L906-L949 생략: 디버그 빌드의 복사와 직렬화 왕복 점검)

	/*
	 * Print plan if debugging.
	 */
	if (Debug_print_plan)
		elog_node_display(LOG, "plan", plan, Debug_pretty_print);

	TRACE_POSTGRESQL_QUERY_PLAN_DONE();

	return plan;
}
```

[01] 이 실제로 부르는 목록 버전이다.

`tcop` / `postgres.c` L970-L1003 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L970-L1003))

```c
// tcop/postgres.c L970-L1003
List *
pg_plan_queries(List *querytrees, const char *query_string, int cursorOptions,
				ParamListInfo boundParams)
{
	List	   *stmt_list = NIL;
	ListCell   *query_list;

	foreach(query_list, querytrees)
	{
		Query	   *query = lfirst_node(Query, query_list);
		PlannedStmt *stmt;

		if (query->commandType == CMD_UTILITY)
		{
			/* Utility commands require no planning. */
			stmt = makeNode(PlannedStmt);
			stmt->commandType = CMD_UTILITY;
			stmt->canSetTag = query->canSetTag;
			stmt->utilityStmt = query->utilityStmt;
			stmt->stmt_location = query->stmt_location;
			stmt->stmt_len = query->stmt_len;
			stmt->queryId = query->queryId;
		}
		else
		{
			stmt = pg_plan_query(query, query_string, cursorOptions,
								 boundParams);
		}

		stmt_list = lappend(stmt_list, stmt);
	}

	return stmt_list;
}
```

플래너 훅이 끼어드는 자리다. 훅이 없으면 [07] 로 간다.

`optimizer` / `plan` / `planner.c` L299-L313 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L299-L313))

```c
// plan/planner.c L299-L313
PlannedStmt *
planner(Query *parse, const char *query_string, int cursorOptions,
		ParamListInfo boundParams)
{
	PlannedStmt *result;

	if (planner_hook)
		result = (*planner_hook) (parse, query_string, cursorOptions, boundParams);
	else
		result = standard_planner(parse, query_string, cursorOptions, boundParams);

	pgstat_report_plan_id(result->planId, false);

	return result;
}
```

## 동작 흐름

```text
 pg_plan_queries (L971)                    [01] L1193 에서 CURSOR_OPT_PARALLEL_OK 로 불린다
 L977  foreach Query
 L982    CMD_UTILITY 면
 L985-L991  makeNode(PlannedStmt)
              commandType = CMD_UTILITY, canSetTag, utilityStmt, 위치, queryId 만 복사
 L995    아니면 pg_plan_query
 L999    stmt_list 에 붙인다

 pg_plan_query (L883)
 L889  CMD_UTILITY 면 NULL                 (pg_plan_queries 를 거치면 여기 오지 않는다)
 L893  Assert(ActiveSnapshotSet())          사용자 함수를 부를 수 있으니 스냅샷이 있어야 한다
                                             ([01] L1163 이 걸어 둔 것)
 L897  log_planner_stats 면 ResetUsage
 L901  plan = planner(querytree, query_string, cursorOptions, boundParams)
 L954  debug_print_plan 이면 계획 트리를 로그에
 L959  return plan

 planner (planner.c L300)
 L305  planner_hook 이 있으면 그것을, 없으면 [07] standard_planner
 L310  pgstat_report_plan_id
```

`Query` 목록과 `PlannedStmt` 목록은 늘 같은 길이다. 유틸리티 문장도 자리를 하나 차지한다.

```text
 Query 목록 -> PlannedStmt 목록 (pg_plan_queries)

 Query                               PlannedStmt
 CMD_SELECT                    -->   planTree = Plan 트리 (planner 가 만든 것)
                                     rtable, relationOids, ...
 CMD_INSERT                    -->   planTree = ModifyTable 이 꼭대기인 Plan 트리
 CMD_UTILITY (CREATE TABLE)    -->   planTree = NULL
                                     utilityStmt = CreateStmt (원시 트리 그대로)

 [09] ChoosePortalStrategy 는 commandType 으로, [10] PortalRunMulti 는 utilityStmt 가
 NULL 인지로 두 갈래를 가른다 (pquery.c L231-L244, L1221)
```

```text
 플래너 훅의 연결 (planner.c L305-L308)

 pg_plan_query --> planner --+-- planner_hook (확장이 설치했으면)
                             |     보통 안에서 standard_planner 를 부른다 (주석 L290-L293)
                             +-- standard_planner (없으면)

 standard_planner 는 입력 Query 를 고쳐 쓴다 (주석 L295-L296)
   같은 Query 로 여러 번 계획하려면 미리 복사해야 한다
```

## 결과가 쓰이는 곳

```text
 List of PlannedStmt
      --> [01] PortalDefineQuery 가 포털의 stmts 에 담는다 (postgres.c L1225-L1230)
      --> [09] ChoosePortalStrategy 가 이 목록의 모양으로 실행 전략을 정한다

 planId
      --> pg_stat_activity 의 plan_id 보고 (planner.c L310)
```

## 다루지 않는 것

`log_planner_stats` 자원 보고, `debug_print_plan` 의 노드 출력 형식, 디버그 빌드의 `copyObject` / `nodeToString` 왕복 점검, 확장 프로토콜에서 `boundParams` 로 사용자 정의 계획을 만드는 경로(`plancache.c`)는 곁가지라 요약만 했다.
