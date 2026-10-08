# ExecInitNode

상위: [executor](../README.md)

**계획 노드 하나를 받아 같은 종류의 상태 노드 하나를 만들어 돌려주는 분배기다.** 노드 태그로 `switch` 해서 `ExecInitXxx` 를 부르고, 자식 노드는 각 `ExecInitXxx` 가 안에서 다시 `ExecInitNode` 를 불러 만든다. 그래서 이 함수 자체에는 재귀 호출이 보이지 않지만, 결과는 계획 트리와 같은 모양의 `PlanState` 트리다. 끝에서 노드의 실행 함수를 `ExecProcNodeFirst` 로 감싸 둔다.

## 위치

`executor` / `execProcnode.c` L142-L420 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execProcnode.c#L142-L420))

## 실제 코드

노드 태그로 가르는 `switch` 다. 이 흐름에 나오는 `ModifyTable`, `SeqScan` 두 갈래만 남기고 나머지 노드는 줄였다.

`executor` / `execProcnode.c` L141-L420 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execProcnode.c#L141-L420))

```c
// execProcnode.c L141-L420
PlanState *
ExecInitNode(Plan *node, EState *estate, int eflags)
{
	PlanState  *result;
	List	   *subps;
	ListCell   *l;

	/*
	 * do nothing when we get to the end of a leaf on tree.
	 */
	if (node == NULL)
		return NULL;

	/*
	 * Make sure there's enough stack available. Need to check here, in
	 * addition to ExecProcNode() (via ExecProcNodeFirst()), to ensure the
	 * stack isn't overrun while initializing the node tree.
	 */
	check_stack_depth();

	switch (nodeTag(node))
	{
			/*
			 * control nodes
			 */
		case T_Result:
			result = (PlanState *) ExecInitResult((Result *) node,
												  estate, eflags);
			break;

		case T_ProjectSet:
			result = (PlanState *) ExecInitProjectSet((ProjectSet *) node,
													  estate, eflags);
			break;

		case T_ModifyTable:
			result = (PlanState *) ExecInitModifyTable((ModifyTable *) node,
													   estate, eflags);
			break;

		// ... (L181-L205 생략: Append, MergeAppend, RecursiveUnion, BitmapAnd, BitmapOr)
			/*
			 * scan nodes
			 */
		case T_SeqScan:
			result = (PlanState *) ExecInitSeqScan((SeqScan *) node,
												   estate, eflags);
			break;

		// ... (L214-L293 생략: SampleScan ~ CustomScan 의 스캔 노드 열여섯 개)
			// ... (L294-L384 생략: 조인, 정렬, 집계, Gather, Limit 등 열일곱 개)
		default:
			elog(ERROR, "unrecognized node type: %d", (int) nodeTag(node));
			result = NULL;		/* keep compiler quiet */
			break;
	}

	ExecSetExecProcNode(result, result->ExecProcNode);

	/*
	 * Initialize any initPlans present in this node.  The planner put them in
	 * a separate list for us.
	 *
	 * The defining characteristic of initplans is that they don't have
	 * arguments, so we don't need to evaluate them (in contrast to
	 * ExecInitSubPlanExpr()).
	 */
	subps = NIL;
	foreach(l, node->initPlan)
	{
		SubPlan    *subplan = (SubPlan *) lfirst(l);
		SubPlanState *sstate;

		Assert(IsA(subplan, SubPlan));
		Assert(subplan->args == NIL);
		sstate = ExecInitSubPlan(subplan, result);
		subps = lappend(subps, sstate);
	}
	result->initPlan = subps;

	/* Set up instrumentation for this node if requested */
	if (estate->es_instrument)
		result->instrument = InstrAlloc(1, estate->es_instrument,
										result->async_capable);

	return result;
}
```

`ExecSetExecProcNode` 는 노드가 고른 실행 함수를 `ExecProcNodeReal` 에 옮겨 두고, 호출 입구는 `ExecProcNodeFirst` 로 바꿔 끼운다.

`executor` / `execProcnode.c` L429-L440 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execProcnode.c#L429-L440))

```c
// execProcnode.c L429-L440
void
ExecSetExecProcNode(PlanState *node, ExecProcNodeMtd function)
{
	/*
	 * Add a wrapper around the ExecProcNode callback that checks stack depth
	 * during the first execution and maybe adds an instrumentation wrapper.
	 * When the callback is changed after execution has already begun that
	 * means we'll superfluously execute ExecProcNodeFirst, but that seems ok.
	 */
	node->ExecProcNodeReal = function;
	node->ExecProcNode = ExecProcNodeFirst;
}
```

`ModifyTable` 의 초기화가 자식을 부르는 자리다. 자기 실행 함수를 `ExecModifyTable` 로 정하고, 결과 테이블을 연 뒤에야 자식(스캔)을 초기화한다.

`executor` / `nodeModifyTable.c` L4769-L4779 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4769-L4779))

```c
// nodeModifyTable.c L4769-L4779
	/*
	 * create state structure
	 */
	mtstate = makeNode(ModifyTableState);
	mtstate->ps.plan = (Plan *) node;
	mtstate->ps.state = estate;
	mtstate->ps.ExecProcNode = ExecModifyTable;

	mtstate->operation = operation;
	mtstate->canSetTag = node->canSetTag;
	mtstate->mt_done = false;
```

`executor` / `nodeModifyTable.c` L4824-L4827 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4824-L4827))

```c
// nodeModifyTable.c L4824-L4827
	/* set up epqstate with dummy subplan data for the moment */
	EvalPlanQualInit(&mtstate->mt_epqstate, estate, NULL, NIL,
					 node->epqParam, resultRelations);
	mtstate->fireBSTriggers = true;
```

`executor` / `nodeModifyTable.c` L4869-L4882 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L4869-L4882))

```c
// nodeModifyTable.c L4869-L4882
		/*
		 * Verify result relation is a valid target for the current operation
		 */
		CheckValidResultRel(resultRelInfo, operation, node->onConflictAction,
							mergeActions);

		resultRelInfo++;
		i++;
	}

	/*
	 * Now we may initialize the subplan.
	 */
	outerPlanState(mtstate) = ExecInitNode(subplan, estate, eflags);
```

## 동작 흐름

```text
 L151  node == NULL 이면 NULL                    자식이 없는 쪽 (leaf 의 outerPlan 등)
 L159  check_stack_depth()                        트리가 깊으면 초기화 중에도 스택이 넘칠 수 있다

 L161  switch (nodeTag(node))
         T_ModifyTable   L176  ExecInitModifyTable    --> 안에서 ExecInitNode(subplan)
         T_SeqScan       L209  ExecInitSeqScan        --> 자식 없음 (Assert, nodeSeqscan.c L215)
         ...             노드 종류마다 한 갈래, 모르는 태그면 L386 ERROR

 L391  ExecSetExecProcNode(result, result->ExecProcNode)
         L438  ExecProcNodeReal = ExecInitXxx 가 고른 함수
         L439  ExecProcNode     = ExecProcNodeFirst

 L402  node->initPlan 의 SubPlan 마다 ExecInitSubPlan     인자 없는 서브쿼리 (initplan)
 L415  EXPLAIN ANALYZE 면 InstrAlloc                        노드별 시간, 행 수 계측
 L419  return result
```

재귀는 이 함수가 아니라 노드별 초기화 함수 안에서 일어난다. 그래서 초기화 순서는 "부모 시작 -> 자식 전부 -> 부모 마무리"가 되고, 부모는 자식이 다 만들어진 뒤에 자기 결과 모양 같은 나머지를 정할 수 있다.

```text
 ExecInitNode(ModifyTable)                         execProcnode.c L177
   ExecInitModifyTable                             nodeModifyTable.c L4656
     L4772  makeNode(ModifyTableState)
     L4775  ps.ExecProcNode = ExecModifyTable
     L4779  mt_done = false
     L4820  ExecInitResultRelation(t2)             결과 테이블을 연다 (ResultRelInfo)
     L4827  fireBSTriggers = true                  첫 ExecModifyTable 호출에서 BEFORE STATEMENT
     L4872  CheckValidResultRel                    뷰, 외래 테이블 등 대상이 맞는지
     L4882  ExecInitNode(SeqScan)  ------------+
                                               |
            ExecInitNode(SeqScan)              v   execProcnode.c L210
              ExecInitSeqScan                      nodeSeqscan.c L207
                ExecOpenScanRelation(t1)           t1 을 연다
                ExecInitScanTupleSlot              t1 모양의 슬롯
                ExecInitQual(a > 10)               조건을 ExprState 로 컴파일
                ExecProcNode = ExecSeqScanWithQual 계열   (qual, projection 유무로 고름)
              ExecSetExecProcNode                  Real = ExecSeqScanWithQual..., 입구 = First
            <-- SeqScanState ------------------+
     ... 결과 테이블별 나머지 초기화 (RETURNING, ON CONFLICT 등)
   ExecSetExecProcNode                             Real = ExecModifyTable, 입구 = First
 <-- ModifyTableState
```

```text
 ExecSetExecProcNode 이 남긴 두 칸 (PlanState)

 ExecProcNode         ExecProcNodeReal     시점
 ExecProcNodeFirst    fn                   첫 호출 전
 fn                   fn                   첫 호출 뒤, 계측 없음
 ExecProcNodeInstr    fn                   첫 호출 뒤, EXPLAIN ANALYZE

 fn = ExecInitXxx 가 고른 노드의 실행 함수 (예: ExecSeqScanWithQual)
 바꿔 끼우는 일은 [06] ExecProcNodeFirst 가 한다
```

## 결과가 쓰이는 곳

```text
 PlanState 트리
      --> [02] InitPlan 이 queryDesc->planstate 로 보관한다
      --> outerPlanState(node), innerPlanState(node) 로 부모가 자식을 찾는다
 ExecProcNode 칸 (= ExecProcNodeFirst)
      --> [05] ExecutePlan 과 부모 노드의 ExecProcNode(child) 가 처음 부를 때 [06] 으로 간다
 ResultRelInfo (ModifyTable 이 연 결과 테이블)
      --> [09] ExecInsert 가 인덱스 목록, 트리거, 제약을 여기서 읽는다
```

## 다루지 않는 것

노드별 초기화 함수 각각(`ExecInitHashJoin`, `ExecInitAgg` 등), 식 컴파일(`ExecInitQual`, `ExecInitExpr` 이 만드는 `ExprState` 단계 배열), `ExecInitModifyTable` 의 나머지(전이 테이블, `ON CONFLICT`, `RETURNING`, MERGE 액션, FDW 초기화), initplan 과 `SubPlan` 의 차이는 이 흐름의 곁가지라 요약만 했다.
