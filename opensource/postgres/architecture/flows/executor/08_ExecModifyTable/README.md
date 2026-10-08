# ExecModifyTable

상위: [executor](../README.md)

**쓰기 문장의 꼭대기 노드다.** 첫 호출에서 BEFORE STATEMENT 트리거를 쏘고, 자식 노드에서 행을 하나씩 당겨 명령 종류(INSERT, UPDATE, DELETE, MERGE)에 맞는 함수로 보낸다. RETURNING 결과가 생기면 그 행을 들고 바로 돌아가고, 없으면 자식이 빌 때까지 루프를 돈 뒤 AFTER STATEMENT 트리거를 큐에 올리고 `NULL` 을 돌려준다. 이 노드도 `ExecProcNode` 로 불리는 평범한 노드라서, 쓰기 문장도 SELECT 와 같은 demand-pull 틀 안에서 돈다.

## 위치

`executor` / `nodeModifyTable.c` L4175-L4594 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4175-L4594))

## 실제 코드

앞부분이다. 이미 끝났으면 바로 돌아가고, 첫 호출이면 BEFORE STATEMENT 트리거를 쏜다.

`executor` / `nodeModifyTable.c` L4174-L4231 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4174-L4231))

```c
// nodeModifyTable.c L4174-L4231
static TupleTableSlot *
ExecModifyTable(PlanState *pstate)
{
	ModifyTableState *node = castNode(ModifyTableState, pstate);
	ModifyTableContext context;
	EState	   *estate = node->ps.state;
	CmdType		operation = node->operation;
	ResultRelInfo *resultRelInfo;
	PlanState  *subplanstate;
	TupleTableSlot *slot;
	TupleTableSlot *oldSlot;
	ItemPointerData tuple_ctid;
	HeapTupleData oldtupdata;
	HeapTuple	oldtuple;
	ItemPointer tupleid;
	bool		tuplock;

	CHECK_FOR_INTERRUPTS();

	/*
	 * This should NOT get called during EvalPlanQual; we should have passed a
	 * subplan tree to EvalPlanQual, instead.  Use a runtime test not just
	 * Assert because this condition is easy to miss in testing.  (Note:
	 * although ModifyTable should not get executed within an EvalPlanQual
	 * operation, we do have to allow it to be initialized and shut down in
	 * case it is within a CTE subplan.  Hence this test must be here, not in
	 * ExecInitModifyTable.)
	 */
	if (estate->es_epq_active != NULL)
		elog(ERROR, "ModifyTable should not be called during EvalPlanQual");

	/*
	 * If we've already completed processing, don't try to do more.  We need
	 * this test because ExecPostprocessPlan might call us an extra time, and
	 * our subplan's nodes aren't necessarily robust against being called
	 * extra times.
	 */
	if (node->mt_done)
		return NULL;

	/*
	 * On first call, fire BEFORE STATEMENT triggers before proceeding.
	 */
	if (node->fireBSTriggers)
	{
		fireBSTriggers(node);
		node->fireBSTriggers = false;
	}

	/* Preload local variables */
	resultRelInfo = node->resultRelInfo + node->mt_lastResultIndex;
	subplanstate = outerPlanState(node);

	/* Set global context */
	context.mtstate = node;
	context.epqstate = &node->mt_epqstate;
	context.estate = estate;

```

루프의 몸통이다. 자식에게서 행을 당기는 줄(L4280)이 이 노드의 demand-pull 이다. UPDATE/DELETE/MERGE 가 지울 행의 위치(ctid)를 꺼내는 부분은 INSERT 경로에 없어 줄였다.

`executor` / `nodeModifyTable.c` L4232-L4594 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4232-L4594))

```c
// nodeModifyTable.c L4232-L4594
	/*
	 * Fetch rows from subplan, and execute the required table modification
	 * for each row.
	 */
	for (;;)
	{
		/*
		 * Reset the per-output-tuple exprcontext.  This is needed because
		 * triggers expect to use that context as workspace.  It's a bit ugly
		 * to do this below the top level of the plan, however.  We might need
		 * to rethink this later.
		 */
		ResetPerTupleExprContext(estate);

		/*
		 * Reset per-tuple memory context used for processing on conflict and
		 * returning clauses, to free any expression evaluation storage
		 * allocated in the previous cycle.
		 */
		if (pstate->ps_ExprContext)
			ResetExprContext(pstate->ps_ExprContext);

		// ... (L4254-L4277 생략: MERGE 의 미뤄 둔 NOT MATCHED 처리)

		/* Fetch the next row from subplan */
		context.planSlot = ExecProcNode(subplanstate);
		context.cpDeletedSlot = NULL;

		/* No more tuples to process? */
		if (TupIsNull(context.planSlot))
			break;

		// ... (L4287-L4335 생략: 결과 테이블이 여럿일 때 junk 열 tableoid 로 대상 고르기)

		// ... (L4337-L4360 생략: FDW 직접 수정이면 RETURNING 만 계산)

		EvalPlanQualSetSlot(&node->mt_epqstate, context.planSlot);
		slot = context.planSlot;

		tupleid = NULL;
		oldtuple = NULL;

		// ... (L4368-L4500 생략: UPDATE/DELETE/MERGE 의 ctid 또는 wholerow 꺼내기)

		switch (operation)
		{
			case CMD_INSERT:
				/* Initialize projection info if first time for this table */
				if (unlikely(!resultRelInfo->ri_projectNewInfoValid))
					ExecInitInsertProjection(node, resultRelInfo);
				slot = ExecGetInsertNewTuple(resultRelInfo, context.planSlot);
				slot = ExecInsert(&context, resultRelInfo, slot,
								  node->canSetTag, NULL, NULL);
				break;

			// ... (L4513-L4565 생략: UPDATE, DELETE, MERGE 갈래)

			default:
				elog(ERROR, "unknown operation");
				break;
		}

		/*
		 * If we got a RETURNING result, return it to caller.  We'll continue
		 * the work on next call.
		 */
		if (slot)
			return slot;
	}

	/*
	 * Insert remaining tuples for batch insert.
	 */
	if (estate->es_insert_pending_result_relations != NIL)
		ExecPendingInserts(estate);

	/*
	 * We're done, but fire AFTER STATEMENT triggers before exiting.
	 */
	fireASTriggers(node);

	node->mt_done = true;

	return NULL;
}
```

문장 트리거 두 함수 중 INSERT 갈래다. BEFORE 는 그 자리에서 실행하고, AFTER 는 큐에 쌓는다.

`executor` / `nodeModifyTable.c` L4003-L4016 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4003-L4016))

```c
// nodeModifyTable.c L4003-L4016
static void
fireBSTriggers(ModifyTableState *node)
{
	ModifyTable *plan = (ModifyTable *) node->ps.plan;
	ResultRelInfo *resultRelInfo = node->rootResultRelInfo;

	switch (node->operation)
	{
		case CMD_INSERT:
			ExecBSInsertTriggers(node->ps.state, resultRelInfo);
			// ... (L4013-L4015 생략: ON CONFLICT DO UPDATE 면 UPDATE 문장 트리거도)
			break;
```

`executor` / `nodeModifyTable.c` L4040-L4055 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4040-L4055))

```c
// nodeModifyTable.c L4040-L4055
static void
fireASTriggers(ModifyTableState *node)
{
	ModifyTable *plan = (ModifyTable *) node->ps.plan;
	ResultRelInfo *resultRelInfo = node->rootResultRelInfo;

	switch (node->operation)
	{
		case CMD_INSERT:
			// ... (L4049-L4052 생략: ON CONFLICT DO UPDATE 면 UPDATE 문장 트리거도)
			ExecASInsertTriggers(node->ps.state, resultRelInfo,
								 node->mt_transition_capture);
			break;
```

`commands` / `trigger.c` L2457-L2468 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/trigger.c#L2457-L2468))

```c
// trigger.c L2457-L2468
void
ExecASInsertTriggers(EState *estate, ResultRelInfo *relinfo,
					 TransitionCaptureState *transition_capture)
{
	TriggerDesc *trigdesc = relinfo->ri_TrigDesc;

	if (trigdesc && trigdesc->trig_insert_after_statement)
		AfterTriggerSaveEvent(estate, relinfo, NULL, NULL,
							  TRIGGER_EVENT_INSERT,
							  false, NULL, NULL, NIL, NULL, transition_capture,
							  false);
}
```

## 동작 흐름

```text
 L4191 CHECK_FOR_INTERRUPTS
 L4202 EvalPlanQual 중이면 ERROR             ModifyTable 은 EPQ 안에서 실행되지 않는다
 L4211 mt_done 이면 NULL                     ExecPostprocessPlan 이 한 번 더 부를 수 있어서 (L4205-L4210)
 L4217 fireBSTriggers 이면
 L4219   fireBSTriggers(node)                 INSERT -> ExecBSInsertTriggers. 그 자리에서 실행
 L4220   fireBSTriggers = false              다음 호출부터는 건너뛴다

 L4224 resultRelInfo = 마지막으로 쓴 결과 테이블    단일 테이블이면 늘 같은 것
 L4225 subplanstate = outerPlanState(node)

 L4236 for (;;)
 L4244   ResetPerTupleExprContext             트리거가 작업 공간으로 쓰는 컨텍스트를 비운다
 L4280   context.planSlot = ExecProcNode(subplanstate)     --> 자식 (예: [07] ExecSeqScan)
 L4284   빈 슬롯이면 break
 L4362   EvalPlanQualSetSlot
 L4502   switch (operation)
           CMD_INSERT
 L4506       첫 행이면 ExecInitInsertProjection     ri_newTupleSlot 준비
 L4508       slot = ExecGetInsertNewTuple(...)       슬롯 종류가 테이블과 다르면 ri_newTupleSlot 에 복사
                                                     (INSERT 는 junk 열이 없어 투영은 일어나지 않는다, L794-L795)
 L4509       slot = ExecInsert(&context, resultRelInfo, slot, canSetTag, NULL, NULL)   --> [09]
 L4576   slot 이 있으면 (RETURNING) return slot     다음 호출 때 루프를 이어서 돈다

 L4583 배치 삽입이 남았으면 ExecPendingInserts    FDW 배치
 L4589 fireASTriggers(node)                   INSERT -> ExecASInsertTriggers. 큐에만 쌓는다
 L4591 mt_done = true
 L4593 return NULL
```

문장 트리거 둘은 실행 시점이 다르다. BEFORE STATEMENT 는 첫 행을 당기기 전에 실행되고, AFTER STATEMENT 는 여기서 이벤트만 큐에 올라가 [10] 의 `AfterTriggerEndQuery` 에서 실행된다.

```text
 INSERT INTO t2 SELECT * FROM t1 WHERE a > 10   (통과 행 r1 r2 r3, t2 에 네 종류 트리거가 다 있다고 하자)

 위치                         트리거                                   언제 실행되는가
 [08] L4219                   BEFORE STATEMENT                         즉시
 [09] r1  L911                BEFORE ROW                               즉시
 [09] r1  L1277               AFTER ROW                                큐에 쌓음
 [09] r2                      BEFORE ROW, AFTER ROW                    즉시, 큐
 [09] r3                      BEFORE ROW, AFTER ROW                    즉시, 큐
 [08] L4589                   AFTER STATEMENT                          큐에 쌓음
 [10] AfterTriggerEndQuery    AFTER ROW r1 r2 r3, AFTER STATEMENT      여기서 큐 순서대로 실행

 BEFORE ROW 는 행이 테이블에 들어가기 전, AFTER ROW 는 문장 전체가 끝난 뒤에 돈다
```

RETURNING 이 있으면 이 노드가 행마다 돌아간다. 루프 상태는 지역 변수가 아니라 노드(자식의 스캔 위치, `mt_done`)에 있으므로, 다음 `ExecProcNode` 에서 이어서 돈다.

```text
 INSERT INTO t2 SELECT * FROM t1 WHERE a > 10 RETURNING id   (통과 행 r1 r2 r3)

 ExecutePlan 바퀴   돌려준 것      ExecModifyTable 안에서 일어난 일
 1                  slot(r1.id)    fireBS, 자식 -> r1, ExecInsert 가 RETURNING 슬롯을 돌려줌
 2                  slot(r2.id)    자식 -> r2, ExecInsert
 3                  slot(r3.id)    자식 -> r3, ExecInsert
 4                  NULL           자식 -> 빈 슬롯, fireAS, mt_done = true
```

## 결과가 쓰이는 곳

```text
 돌려준 슬롯 (RETURNING)
      --> [05] ExecutePlan 이 receiveSlot 으로 넘긴다
 NULL
      --> [05] 의 루프가 끝난다
 큐에 올린 AFTER STATEMENT 이벤트
      --> [10] AfterTriggerEndQuery 가 실행한다
 mt_done
      --> [10] ExecPostprocessPlan 이 CTE 안의 ModifyTable 을 다시 부를 때 바로 NULL
```

## 다루지 않는 것

UPDATE, DELETE, MERGE 의 행 식별(ctid, wholerow junk 열)과 각 실행 함수(`ExecUpdate`, `ExecDelete`, `ExecMerge`), 결과 테이블이 여럿인 상속, 파티션 갱신(`ExecLookupResultRelByOid`), FDW 직접 수정(`ri_usesFdwDirectModify`), 전이 테이블(`REFERENCING NEW TABLE`), `ExecInitInsertProjection` 이 만드는 투영은 쓰기 노드의 곁가지라 요약만 했다.
