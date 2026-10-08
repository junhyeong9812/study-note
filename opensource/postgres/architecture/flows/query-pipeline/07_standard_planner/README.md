# standard_planner

상위: [쿼리 실행 파이프라인](../README.md)

플래너의 **바깥 틀**이다. 계획 전체가 공유하는 `PlannerGlobal` 을 만들고, `subquery_planner` 로 가능한 실행 경로(`Path`)들을 만든 뒤, **가장 싼 `Path` 하나를 골라 `create_plan` 으로 `Plan` 트리로 바꾸고**, 참조를 정리해 `PlannedStmt` 로 포장한다. "무엇이 가장 싼가"를 정하는 일은 안쪽([08] 과 그 아래)이 하고, 이 함수는 고르고 굳히는 일을 한다.

## 위치

`optimizer` / `plan` / `planner.c` L316-L628 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L316-L628))

## 실제 코드

전역 상태를 만들고, 병렬 가능 여부와 가져올 행 비율을 정한 뒤, 경로를 만들고 고른다.

`optimizer` / `plan` / `planner.c` L316-L454 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L316-L454))

```c
// plan/planner.c L316-L454
standard_planner(Query *parse, const char *query_string, int cursorOptions,
				 ParamListInfo boundParams)
{
	PlannedStmt *result;
	PlannerGlobal *glob;
	double		tuple_fraction;
	PlannerInfo *root;
	RelOptInfo *final_rel;
	Path	   *best_path;
	Plan	   *top_plan;
	ListCell   *lp,
			   *lr;

	/*
	 * Set up global state for this planner invocation.  This data is needed
	 * across all levels of sub-Query that might exist in the given command,
	 * so we keep it in a separate struct that's linked to by each per-Query
	 * PlannerInfo.
	 */
	glob = makeNode(PlannerGlobal);

// ... (L337-L358 생략: PlannerGlobal 필드 초기화)

// ... (L360-L380 생략: 주석)
	if ((cursorOptions & CURSOR_OPT_PARALLEL_OK) != 0 &&
		IsUnderPostmaster &&
		parse->commandType == CMD_SELECT &&
		!parse->hasModifyingCTE &&
		max_parallel_workers_per_gather > 0 &&
		!IsParallelWorker())
	{
		/* all the cheap tests pass, so scan the query tree */
		glob->maxParallelHazard = max_parallel_hazard(parse);
		glob->parallelModeOK = (glob->maxParallelHazard != PROPARALLEL_UNSAFE);
	}
	else
	{
		/* skip the query tree scan, just assume it's unsafe */
		glob->maxParallelHazard = PROPARALLEL_UNSAFE;
		glob->parallelModeOK = false;
	}

// ... (L399-L418 생략: 주석과 debug parallel query)
	/* Determine what fraction of the plan is likely to be scanned */
// ... (L420-L440 생략: 커서의 cursor tuple fraction)
	else
	{
		/* Default assumption is we need all the tuples */
		tuple_fraction = 0.0;
	}

	/* primary planning entry point (may recurse for subqueries) */
	root = subquery_planner(glob, parse, NULL, false, tuple_fraction, NULL);

	/* Select best Path and turn it into a Plan */
	final_rel = fetch_upper_rel(root, UPPERREL_FINAL, NULL);
	best_path = get_cheapest_fractional_path(final_rel, tuple_fraction);

	top_plan = create_plan(root, best_path);
```

고른 계획을 다듬고 `PlannedStmt` 를 채운다.

`optimizer` / `plan` / `planner.c` L456-L628 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L456-L628))

```c
// plan/planner.c L456-L628
	/*
	 * If creating a plan for a scrollable cursor, make sure it can run
	 * backwards on demand.  Add a Material node at the top at need.
	 */
	if (cursorOptions & CURSOR_OPT_SCROLL)
	{
		if (!ExecSupportsBackwardScan(top_plan))
			top_plan = materialize_finished_plan(top_plan);
	}

// ... (L466-L531 생략: debug parallel query 의 Gather 덧붙이기)

// ... (L533-L550 생략: 서브플랜의 Param 정리)

	/* final cleanup of the plan */
	Assert(glob->finalrtable == NIL);
	Assert(glob->finalrteperminfos == NIL);
	Assert(glob->finalrowmarks == NIL);
	Assert(glob->resultRelations == NIL);
	Assert(glob->appendRelations == NIL);
	top_plan = set_plan_references(root, top_plan);
	/* ... and the subplans (both regular subplans and initplans) */
	Assert(list_length(glob->subplans) == list_length(glob->subroots));
	forboth(lp, glob->subplans, lr, glob->subroots)
	{
		Plan	   *subplan = (Plan *) lfirst(lp);
		PlannerInfo *subroot = lfirst_node(PlannerInfo, lr);

		lfirst(lp) = set_plan_references(subroot, subplan);
	}

	/* build the PlannedStmt result */
	result = makeNode(PlannedStmt);

	result->commandType = parse->commandType;
	result->queryId = parse->queryId;
	result->hasReturning = (parse->returningList != NIL);
	result->hasModifyingCTE = parse->hasModifyingCTE;
	result->canSetTag = parse->canSetTag;
	result->transientPlan = glob->transientPlan;
	result->dependsOnRole = glob->dependsOnRole;
	result->parallelModeNeeded = glob->parallelModeNeeded;
	result->planTree = top_plan;
	result->partPruneInfos = glob->partPruneInfos;
	result->rtable = glob->finalrtable;
	result->unprunableRelids = bms_difference(glob->allRelids,
											  glob->prunableRelids);
	result->permInfos = glob->finalrteperminfos;
	result->resultRelations = glob->resultRelations;
	result->appendRelations = glob->appendRelations;
	result->subplans = glob->subplans;
	result->rewindPlanIDs = glob->rewindPlanIDs;
	result->rowMarks = glob->finalrowmarks;
	result->relationOids = glob->relationOids;
	result->invalItems = glob->invalItems;
	result->paramExecTypes = glob->paramExecTypes;
	/* utilityStmt should be null, but we might as well copy it */
	result->utilityStmt = parse->utilityStmt;
	result->stmt_location = parse->stmt_location;
	result->stmt_len = parse->stmt_len;

// ... (L599-L622 생략: JIT 플래그)

	if (glob->partition_directory != NULL)
		DestroyPartitionDirectory(glob->partition_directory);

	return result;
}
```

`subquery_planner` 의 끝이다. [08] 을 부르고 최종 relation 의 가장 싼 경로를 정해 둔다.

`optimizer` / `plan` / `planner.c` L1255-L1283 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L1255-L1283))

```c
// plan/planner.c L1255-L1283
	/*
	 * Do the main planning.
	 */
	grouping_planner(root, tuple_fraction, setops);

	/*
	 * Capture the set of outer-level param IDs we have access to, for use in
	 * extParam/allParam calculations later.
	 */
	SS_identify_outer_params(root);

	/*
	 * If any initPlans were created in this query level, adjust the surviving
	 * Paths' costs and parallel-safety flags to account for them.  The
	 * initPlans won't actually get attached to the plan tree till
	 * create_plan() runs, but we must include their effects now.
	 */
	final_rel = fetch_upper_rel(root, UPPERREL_FINAL, NULL);
	SS_charge_for_initplans(root, final_rel);

	/*
	 * Make sure we've identified the cheapest Path for the final rel.  (By
	 * doing this here not in grouping_planner, we include initPlan costs in
	 * the decision, though it's unlikely that will change anything.)
	 */
	set_cheapest(final_rel);

	return root;
}
```

결과 구조체의 주요 필드다.

`src` / `include` / `nodes` / `plannodes.h` L46-L139 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/nodes/plannodes.h#L46-L139))

```c
// nodes/plannodes.h L46-L92
typedef struct PlannedStmt
{
	pg_node_attr(no_equal, no_query_jumble)

	NodeTag		type;

	/* select|insert|update|delete|merge|utility */
	CmdType		commandType;

	/* query identifier (copied from Query) */
	int64		queryId;

	/* plan identifier (can be set by plugins) */
	int64		planId;

	/* is it insert|update|delete|merge RETURNING? */
	bool		hasReturning;

	/* has insert|update|delete|merge in WITH? */
	bool		hasModifyingCTE;

	/* do I set the command result tag? */
	bool		canSetTag;

	/* redo plan when TransactionXmin changes? */
	bool		transientPlan;

	/* is plan specific to current role? */
	bool		dependsOnRole;

	/* parallel mode required to execute? */
	bool		parallelModeNeeded;

	/* which forms of JIT should be performed */
	int			jitFlags;

	/* tree of Plan nodes */
	struct Plan *planTree;

	/*
	 * List of PartitionPruneInfo contained in the plan
	 */
	List	   *partPruneInfos;

	/* list of RangeTblEntry nodes */
	List	   *rtable;

```

## 동작 흐름

```text
 L335   glob = makeNode(PlannerGlobal)             하위 질의까지 공유하는 상태
 L381   병렬 가능한가
          CURSOR_OPT_PARALLEL_OK 이고, postmaster 아래이고, SELECT 이고,
          쓰기 CTE 가 없고, max_parallel_workers_per_gather > 0 이고, 병렬 워커가 아니면
 L389     max_parallel_hazard(parse) 로 트리를 훑는다 -> parallelModeOK
 L395   아니면 PROPARALLEL_UNSAFE, parallelModeOK = false
 L420   커서(FAST_PLAN) 면 tuple_fraction = cursor_tuple_fraction
 L444   아니면 0.0                                   "전부 가져온다"

 L448   root = subquery_planner(glob, parse, NULL, false, tuple_fraction, NULL)
          ... 전처리 (서브쿼리 끌어올리기, 식 정리, 외부 조인 줄이기)
 L1258    [08] grouping_planner                    Path 들을 만든다
 L1280    set_cheapest(final_rel)
 L451   final_rel = fetch_upper_rel(root, UPPERREL_FINAL, NULL)
 L452   best_path = get_cheapest_fractional_path(final_rel, tuple_fraction)
 L454   top_plan = create_plan(root, best_path)      Path 트리 -> Plan 트리

 L460   스크롤 커서인데 역방향을 못 하면 Material 을 위에 얹는다
 L478   debug_parallel_query 면 Gather 를 위에 얹는다 (테스트용)
 L558   top_plan = set_plan_references(root, top_plan)   range table 을 평평하게, Var 를 실행용으로
 L561   서브플랜들도 같은 처리
 L570   result = makeNode(PlannedStmt)
 L572-L597  commandType, queryId, canSetTag, planTree, rtable, resultRelations, subplans,
            relationOids, invalItems ... 를 glob 과 parse 에서 옮긴다
 L600   jit_above_cost 를 넘으면 JIT 플래그
 L627   return result
```

플래너 안에서는 `Path` 와 `Plan` 이 따로 있다. 후보를 비교할 때는 가벼운 `Path` 를 쓰고, 이긴 하나만 실행용 `Plan` 으로 만든다.

```text
 Query 에서 PlannedStmt 까지 (standard_planner 안)

 Query
   |  subquery_planner              L448
   v
 PlannerInfo root
   upper_rels[UPPERREL_FINAL]
     RelOptInfo final_rel
       pathlist   [ Path A (cost 35.5), Path B (cost 8.3), ... ]   후보들
   |  get_cheapest_fractional_path L452   tuple_fraction <= 0 이면 cheapest_total_path (L6752-L6756)
   v
 Path B
   |  create_plan                   L454   이긴 경로만 Plan 노드로
   v
 Plan 트리 (top_plan)
   |  set_plan_references           L558   rtable 을 하나로, Var 번호를 실행용으로
   v
 PlannedStmt
   planTree = top_plan,  rtable = glob->finalrtable,  relationOids, ...

 cost 숫자는 그림을 위한 예시다. 실제 값은 cost_* 함수와 통계가 정한다
```

```text
 PlannedStmt 가 Query 에서 이어받는 것과 새로 갖는 것 (L572-L597)

 Query 에서 그대로
   commandType, queryId, canSetTag, hasModifyingCTE, utilityStmt, stmt_location, stmt_len
 플래너가 새로 만든 것
   planTree, rtable (glob->finalrtable, 평평해진 것), subplans, resultRelations,
   relationOids, invalItems, paramExecTypes, jitFlags,
   parallelModeNeeded, transientPlan, dependsOnRole

 relationOids, invalItems 는 이 계획이 기대는 객체 목록이다
   계획 캐시의 무효화 콜백이 relationOids 에 바뀐 테이블이 있는지 본다
   (utils/cache/plancache.c L2151-L2152)
```

## 결과가 쓰이는 곳

```text
 PlannedStmt
      --> [06] pg_plan_query 를 거쳐 [01] 의 plantree_list 에 담긴다
      --> [executor] ExecutorStart 의 InitPlan 이 planTree 를 PlanState 트리로 만든다
      --> parallelModeNeeded 면 실행 중 병렬 모드에 들어간다
      --> jitFlags 가 실행 시 식 컴파일 여부를 정한다
```

## 다루지 않는 것

`subquery_planner` 의 전처리 단계 전체(`pull_up_sublinks`, `pull_up_subqueries`, `preprocess_expression`, `reduce_outer_joins`), `create_plan` 의 노드별 변환, `set_plan_references` 의 세부, 비용 모델(`costsize.c`), 병렬 안전성 판정(`max_parallel_hazard`), JIT 비용 기준은 이 흐름의 곁가지라 요약만 했다.
