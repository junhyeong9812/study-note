# standard_ExecutorStart

상위: [executor](../README.md)

**실행 한 번에 쓸 상태 그릇(`EState`)을 만들고, 이 실행이 지킬 세 가지 값(스냅샷, 새 행에 찍을 command id, AFTER 트리거 층)을 정한 뒤 `InitPlan` 으로 넘긴다.** 확장이 끼어들 수 있게 `ExecutorStart` 는 훅이 있으면 훅을, 없으면 이 함수를 부르는 얇은 껍데기다.

## 위치

`executor` / `execMain.c` L141-L264 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L141-L264))

## 실제 코드

진입점은 훅을 확인하는 껍데기다. `pg_stat_statements` 같은 확장이 `ExecutorStart_hook` 을 걸고 안에서 다시 `standard_ExecutorStart` 를 부른다.

`executor` / `execMain.c` L121-L138 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L121-L138))

```c
// execMain.c L121-L138
void
ExecutorStart(QueryDesc *queryDesc, int eflags)
{
	// ... (L124-L131 생략: query_id 보고에 관한 주석)
	pgstat_report_query_id(queryDesc->plannedstmt->queryId, false);

	if (ExecutorStart_hook)
		(*ExecutorStart_hook) (queryDesc, eflags);
	else
		standard_ExecutorStart(queryDesc, eflags);
}
```

본체다. 상태 그릇을 만들고 per-query 메모리 컨텍스트로 들어간 뒤, 명령 종류에 따라 `es_output_cid` 를 정한다.

`executor` / `execMain.c` L140-L264 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L140-L264))

```c
// execMain.c L140-L264
void
standard_ExecutorStart(QueryDesc *queryDesc, int eflags)
{
	EState	   *estate;
	MemoryContext oldcontext;

	/* sanity checks: queryDesc must not be started already */
	Assert(queryDesc != NULL);
	Assert(queryDesc->estate == NULL);

	/* caller must ensure the query's snapshot is active */
	Assert(GetActiveSnapshot() == queryDesc->snapshot);

	// ... (L153-L167 생략: 읽기 전용, 병렬 모드에서 쓰기를 막는 이유 주석)
	if ((XactReadOnly || IsInParallelMode()) &&
		!(eflags & EXEC_FLAG_EXPLAIN_ONLY))
		ExecCheckXactReadOnly(queryDesc->plannedstmt);

	/*
	 * Build EState, switch into per-query memory context for startup.
	 */
	estate = CreateExecutorState();
	queryDesc->estate = estate;

	oldcontext = MemoryContextSwitchTo(estate->es_query_cxt);

	/*
	 * Fill in external parameters, if any, from queryDesc; and allocate
	 * workspace for internal parameters
	 */
	estate->es_param_list_info = queryDesc->params;

	if (queryDesc->plannedstmt->paramExecTypes != NIL)
	{
		int			nParamExec;

		nParamExec = list_length(queryDesc->plannedstmt->paramExecTypes);
		estate->es_param_exec_vals = (ParamExecData *)
			palloc0(nParamExec * sizeof(ParamExecData));
	}

	/* We now require all callers to provide sourceText */
	Assert(queryDesc->sourceText != NULL);
	estate->es_sourceText = queryDesc->sourceText;

	/*
	 * Fill in the query environment, if any, from queryDesc.
	 */
	estate->es_queryEnv = queryDesc->queryEnv;

	/*
	 * If non-read-only query, set the command ID to mark output tuples with
	 */
	switch (queryDesc->operation)
	{
		case CMD_SELECT:

			/*
			 * SELECT FOR [KEY] UPDATE/SHARE and modifying CTEs need to mark
			 * tuples
			 */
			if (queryDesc->plannedstmt->rowMarks != NIL ||
				queryDesc->plannedstmt->hasModifyingCTE)
				estate->es_output_cid = GetCurrentCommandId(true);

			/*
			 * A SELECT without modifying CTEs can't possibly queue triggers,
			 * so force skip-triggers mode. This is just a marginal efficiency
			 * hack, since AfterTriggerBeginQuery/AfterTriggerEndQuery aren't
			 * all that expensive, but we might as well do it.
			 */
			if (!queryDesc->plannedstmt->hasModifyingCTE)
				eflags |= EXEC_FLAG_SKIP_TRIGGERS;
			break;

		case CMD_INSERT:
		case CMD_DELETE:
		case CMD_UPDATE:
		case CMD_MERGE:
			estate->es_output_cid = GetCurrentCommandId(true);
			break;

		default:
			elog(ERROR, "unrecognized operation code: %d",
				 (int) queryDesc->operation);
			break;
	}

	/*
	 * Copy other important information into the EState
	 */
	estate->es_snapshot = RegisterSnapshot(queryDesc->snapshot);
	estate->es_crosscheck_snapshot = RegisterSnapshot(queryDesc->crosscheck_snapshot);
	estate->es_top_eflags = eflags;
	estate->es_instrument = queryDesc->instrument_options;
	estate->es_jit_flags = queryDesc->plannedstmt->jitFlags;

	/*
	 * Set up an AFTER-trigger statement context, unless told not to, or
	 * unless it's EXPLAIN-only mode (when ExecutorFinish won't be called).
	 */
	if (!(eflags & (EXEC_FLAG_SKIP_TRIGGERS | EXEC_FLAG_EXPLAIN_ONLY)))
		AfterTriggerBeginQuery();

	/*
	 * Initialize the plan state tree
	 */
	InitPlan(queryDesc, eflags);

	MemoryContextSwitchTo(oldcontext);
}
```

## 동작 흐름

```text
 L147-L151  queryDesc 가 아직 시작 전이고, 호출자가 스냅샷을 활성화해 두었는지 확인

 L168  읽기 전용 트랜잭션이거나 병렬 모드이고, EXPLAIN 만이 아니면
 L170    ExecCheckXactReadOnly(plannedstmt)
           영구 테이블에 쓰는 계획이면 여기서 ERROR. 임시 테이블은 허용

 L175  estate = CreateExecutorState()        es_query_cxt (per-query 메모리) 가 여기서 생긴다
 L178  그 컨텍스트로 전환                     이후 L261 InitPlan 이 만드는 모든 것이 여기 붙는다

 L184-L193  외부 파라미터($1 ...)를 연결하고, 내부 파라미터 칸을 0 으로 할당
 L197, L202 sourceText, queryEnv 를 옮긴다

 L207  switch (operation)
         CMD_SELECT  행 잠금(FOR UPDATE)이나 쓰는 CTE 가 있을 때만 es_output_cid
                     쓰는 CTE 가 없으면 EXEC_FLAG_SKIP_TRIGGERS 를 켠다 (L226)
         CMD_INSERT / DELETE / UPDATE / MERGE
                     es_output_cid = GetCurrentCommandId(true)   L233

 L245  es_snapshot = RegisterSnapshot(queryDesc->snapshot)
 L246  es_crosscheck_snapshot 도 등록 (보통 InvalidSnapshot)
 L247-L249  eflags, 계측 옵션, JIT 플래그를 EState 에

 L255  SKIP_TRIGGERS 도 EXPLAIN_ONLY 도 아니면
 L256    AfterTriggerBeginQuery()             AFTER 트리거 큐의 query_depth++

 L261  InitPlan(queryDesc, eflags)            --> [02]
 L263  원래 메모리 컨텍스트로 복귀
```

`es_output_cid` 는 이 실행이 만든 행을 같은 트랜잭션의 다른 명령과 구별하는 번호다. `GetCurrentCommandId(true)` 의 `true` 는 `currentCommandIdUsed` 를 켠다(access/transam/xact.c L845). `CommandCounterIncrement` 는 이 표시가 켜져 있을 때만 번호를 올린다(xact.c L1108). SELECT 는 보통 쓰지 않으니 이 값을 받지 않는다.

```text
 EState 에 이 함수가 채우는 칸 (src/include/nodes/execnodes.h 의 EState)

 칸                   누가 읽는가                     값
 es_query_cxt         ExecInit*, FreeExecutorState    CreateExecutorState 가 만든 컨텍스트
 es_param_list_info   Param 식 평가                   queryDesc->params
 es_output_cid        heap_insert (새 행의 cmin)      GetCurrentCommandId(true)
 es_snapshot          SeqNext 의 table_beginscan      등록한 스냅샷
 es_top_eflags        ExecutorFinish, ExecutePlan     eflags (+ SKIP_TRIGGERS)
 es_instrument        ExecInitNode 의 InstrAlloc      EXPLAIN ANALYZE 옵션
```

AFTER 트리거 큐는 문장마다 층(query level)을 하나 쌓는다. 시작에서 층을 열고 [10] 의 `AfterTriggerEndQuery` 가 닫으므로, 그 사이 `ExecInsert` 가 쌓은 AFTER ROW 이벤트는 이 문장의 층에 들어간다.

```text
 afterTriggers.query_depth (commands/trigger.c)

 함수                     위치               값                  언제
 AfterTriggerBeginXact    trigger.c L5095    -1                  트랜잭션 시작
 AfterTriggerBeginQuery   execMain.c L256    -1 -> 0             문장 시작 (trigger.c L5124)
 ExecARInsertTriggers     [09]               (그대로)            행마다. 이 층의 events 에 쌓는다
 AfterTriggerEndQuery     [10]               0 -> -1             문장 끝. 쌓인 IMMEDIATE 이벤트를 실행

 트리거 함수 안에서 다른 SQL 을 실행하면 그 SQL 의 ExecutorStart 가 층을 하나 더 쌓는다
 SELECT (쓰는 CTE 없음) 는 SKIP_TRIGGERS 라 층을 열지 않는다
```

## 결과가 쓰이는 곳

```text
 queryDesc->estate
      --> [04] standard_ExecutorRun 이 es_query_cxt 로 다시 들어가 실행한다
 estate->es_output_cid
      --> [09] ExecInsert -> table_tuple_insert(..., estate->es_output_cid, ...)  nodeModifyTable.c L1235
 estate->es_snapshot
      --> [07] SeqNext -> table_beginscan(rel, estate->es_snapshot, ...)          nodeSeqscan.c L73
 query_depth
      --> [10] AfterTriggerEndQuery 가 짝을 맞춰 닫는다
```

## 다루지 않는 것

`ExecCheckXactReadOnly` 가 거부하는 명령 목록, `CreateExecutorState` 가 초기화하는 `EState` 의 나머지 칸, 파라미터 종류(`ParamListInfo` 와 `ParamExecData`), JIT 플래그의 의미, 스냅샷 등록(`RegisterSnapshot`)과 resource owner 의 관계는 시작 단계의 곁가지라 요약만 했다.
