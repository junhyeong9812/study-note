# InitPlan

상위: [executor](../README.md)

**계획을 실행할 수 있는 상태로 바꾸는 준비 단계다.** 권한을 먼저 검사하고, range table 을 실행기 쪽 배열로 옮기고, 서브플랜과 메인 계획 트리에 `ExecInitNode` 를 불러 `PlanState` 트리를 만든다. 끝나면 `queryDesc->planstate` 와 결과 행 모양(`tupDesc`)이 채워진다.

## 위치

`executor` / `execMain.c` L836-L1035 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L836-L1035))

## 실제 코드

앞부분이다. 권한 검사, range table 초기화, 초기 파티션 가지치기를 한다.

`executor` / `execMain.c` L835-L872 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L835-L872))

```c
// execMain.c L835-L872
static void
InitPlan(QueryDesc *queryDesc, int eflags)
{
	CmdType		operation = queryDesc->operation;
	PlannedStmt *plannedstmt = queryDesc->plannedstmt;
	Plan	   *plan = plannedstmt->planTree;
	List	   *rangeTable = plannedstmt->rtable;
	EState	   *estate = queryDesc->estate;
	PlanState  *planstate;
	TupleDesc	tupType;
	ListCell   *l;
	int			i;

	/*
	 * Do permissions checks
	 */
	ExecCheckPermissions(rangeTable, plannedstmt->permInfos, true);

	/*
	 * initialize the node's execution state
	 */
	ExecInitRangeTable(estate, rangeTable, plannedstmt->permInfos,
					   bms_copy(plannedstmt->unprunableRelids));

	estate->es_plannedstmt = plannedstmt;
	estate->es_part_prune_infos = plannedstmt->partPruneInfos;

	/*
	 * Perform runtime "initial" pruning to identify which child subplans,
	 * corresponding to the children of plan nodes that contain
	 * PartitionPruneInfo such as Append, will not be executed. The results,
	 * which are bitmapsets of indexes of the child subplans that will be
	 * executed, are saved in es_part_prune_results.  These results correspond
	 * to each PartitionPruneInfo entry, and the es_part_prune_results list is
	 * parallel to es_part_prune_infos.
	 */
	ExecDoInitialPruning(estate);

```

행 잠금(`FOR UPDATE` 류) 정보를 실행기 배열로 옮기는 부분은 이 흐름의 INSERT 와 관계가 없어 줄였다.

`executor` / `execMain.c` L873-L946 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L873-L946))

```c
// execMain.c L873-L946
	/*
	 * Next, build the ExecRowMark array from the PlanRowMark(s), if any.
	 */
	if (plannedstmt->rowMarks)
	// ... (L877-L944 생략: PlanRowMark 마다 ExecRowMark 를 만들어 es_rowmarks 에 넣는다)
	}

```

서브플랜을 먼저, 메인 트리를 나중에 초기화한다. 순서에는 이유가 주석으로 적혀 있다.

`executor` / `execMain.c` L947-L1035 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L947-L1035))

```c
// execMain.c L947-L1035
	/*
	 * Initialize the executor's tuple table to empty.
	 */
	estate->es_tupleTable = NIL;

	/* signal that this EState is not used for EPQ */
	estate->es_epq_active = NULL;

	/*
	 * Initialize private state information for each SubPlan.  We must do this
	 * before running ExecInitNode on the main query tree, since
	 * ExecInitSubPlan expects to be able to find these entries.
	 */
	Assert(estate->es_subplanstates == NIL);
	i = 1;						/* subplan indices count from 1 */
	foreach(l, plannedstmt->subplans)
	{
		Plan	   *subplan = (Plan *) lfirst(l);
		PlanState  *subplanstate;
		int			sp_eflags;

		/*
		 * A subplan will never need to do BACKWARD scan nor MARK/RESTORE. If
		 * it is a parameterless subplan (not initplan), we suggest that it be
		 * prepared to handle REWIND efficiently; otherwise there is no need.
		 */
		sp_eflags = eflags
			& ~(EXEC_FLAG_REWIND | EXEC_FLAG_BACKWARD | EXEC_FLAG_MARK);
		if (bms_is_member(i, plannedstmt->rewindPlanIDs))
			sp_eflags |= EXEC_FLAG_REWIND;

		subplanstate = ExecInitNode(subplan, estate, sp_eflags);

		estate->es_subplanstates = lappend(estate->es_subplanstates,
										   subplanstate);

		i++;
	}

	/*
	 * Initialize the private state information for all the nodes in the query
	 * tree.  This opens files, allocates storage and leaves us ready to start
	 * processing tuples.
	 */
	planstate = ExecInitNode(plan, estate, eflags);

	/*
	 * Get the tuple descriptor describing the type of tuples to return.
	 */
	tupType = ExecGetResultType(planstate);

	/*
	 * Initialize the junk filter if needed.  SELECT queries need a filter if
	 * there are any junk attrs in the top-level tlist.
	 */
	if (operation == CMD_SELECT)
	{
		bool		junk_filter_needed = false;
		ListCell   *tlist;

		foreach(tlist, plan->targetlist)
		{
			TargetEntry *tle = (TargetEntry *) lfirst(tlist);

			if (tle->resjunk)
			{
				junk_filter_needed = true;
				break;
			}
		}

		if (junk_filter_needed)
		{
			JunkFilter *j;
			TupleTableSlot *slot;

			slot = ExecInitExtraTupleSlot(estate, NULL, &TTSOpsVirtual);
			j = ExecInitJunkFilter(planstate->plan->targetlist,
								   slot);
			estate->es_junkFilter = j;

			/* Want to return the cleaned tuple type */
			tupType = j->jf_cleanTupType;
		}
	}

	queryDesc->tupDesc = tupType;
	queryDesc->planstate = planstate;
}
```

## 동작 흐름

```text
 L851  ExecCheckPermissions(rangeTable, permInfos, true)
         쓰려는 테이블에 INSERT 권한이 없으면 여기서 ERROR. 실행 전에 막는다

 L856  ExecInitRangeTable
         es_range_table, es_relations[] (아직 다 NULL, 필요할 때 연다)
 L871  ExecDoInitialPruning                 실행 전에 알 수 있는 파티션을 미리 뺀다

 L876  rowMarks 가 있으면 es_rowmarks[] 를 채운다 (SELECT FOR UPDATE 류)

 L950  es_tupleTable = NIL                  이후 ExecInit* 가 만드는 슬롯이 전부 여기 등록된다
 L953  es_epq_active = NULL                 이 EState 는 EvalPlanQual 용이 아니다

 L962  foreach subplans                     서브쿼리 (WHERE x IN (SELECT ...)) 의 계획들
 L973    BACKWARD, MARK 를 빼고 REWIND 는 필요할 때만
 L978    ExecInitNode(subplan)              --> [03]
 L980    es_subplanstates 에 덧붙인다

 L991  planstate = ExecInitNode(plan)       --> [03]  메인 트리. 여기서 재귀가 시작된다
 L996  tupType = ExecGetResultType(planstate)

 L1002 SELECT 이고 targetlist 에 resjunk 열이 있으면
 L1024   ExecInitJunkFilter                  ORDER BY 에만 쓰인 열 같은 숨은 열을 결과에서 뺀다
 L1029   tupType = 걸러낸 뒤의 모양

 L1033 queryDesc->tupDesc = tupType
 L1034 queryDesc->planstate = planstate
```

서브플랜을 먼저 초기화하는 이유는 L955-L959 주석에 있다. 메인 트리의 식 안에 있는 `SubPlan` 을 초기화하는 `ExecInitSubPlan` 이 `es_subplanstates` 에서 자기 상태를 찾기 때문이다.

```text
 InitPlan 이 만드는 것 (INSERT INTO t2 SELECT * FROM t1 WHERE a > 10, 서브플랜 없음)

 queryDesc
   |
   +-- estate (EState)
   |     es_range_table      [ RTE(t2), RTE(t1) ]          순서는 planner 가 정한다
   |     es_relations        [ NULL, NULL ]                 palloc0 (execUtils.c L799), 열 때 채운다
   |     es_subplanstates    NIL
   |     es_tupleTable       [ ... ExecInit* 가 만든 슬롯들 ... ]
   |
   +-- planstate  -->  ModifyTableState
   |                     outerPlanState --> SeqScanState
   +-- tupDesc     ModifyTableState 의 결과 모양 (ExecGetResultType)
```

권한 검사가 노드 초기화보다 앞에 있으므로, 권한 없는 사용자는 테이블을 열거나 잠그기 전에 거절된다. 테이블을 실제로 여는 일은 노드 초기화가 각자 한다. `ExecInitSeqScan` 은 `ExecOpenScanRelation`(execUtils.c L747), `ExecInitModifyTable` 은 `ExecInitResultRelation`(execUtils.c L885)을 거쳐 둘 다 `ExecGetRangeTableRelation` 에 닿는다.

## 결과가 쓰이는 곳

```text
 queryDesc->planstate
      --> [05] ExecutePlan 이 ExecProcNode(planstate) 를 반복한다
      --> [10] ExecEndPlan 이 같은 트리를 내려가며 정리한다
 queryDesc->tupDesc
      --> [04] standard_ExecutorRun 의 dest->rStartup(dest, operation, tupDesc)
 estate->es_junkFilter
      --> [05] ExecutePlan 이 슬롯마다 ExecFilterJunk
 estate->es_subplanstates
      --> ExecInitSubPlan 이 찾아 쓰고, ExecEndPlan 이 따로 정리한다
```

## 다루지 않는 것

권한 검사의 세부(`ExecCheckOneRelPerms`, 열 단위 권한, `ExecutorCheckPerms_hook`), 실행 시점 파티션 가지치기(`ExecDoInitialPruning`, `PartitionPruneInfo`), 행 잠금 배열(`ExecRowMark`, `CheckValidRowMarkRel`), junk filter 의 내부(`ExecInitJunkFilter`)는 준비 단계의 곁가지라 요약만 했다.
