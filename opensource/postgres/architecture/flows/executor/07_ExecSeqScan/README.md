# ExecSeqScan

상위: [executor](../README.md)

**테이블을 처음부터 끝까지 읽는 스캔 노드의 실행 함수다.** 본문은 `ExecScanExtended` 한 줄이고, 실제 일은 세 겹으로 나뉜다. `SeqNext` 가 테이블 접근 방식(table AM)에서 행 하나를 꺼내고, `ExecScanFetch` 가 인터럽트를 확인하며 그것을 부르고, `ExecScanExtended` 가 조건(qual)을 통과할 때까지 반복한 뒤 투영(projection)을 한다. PG18 은 qual 과 projection 유무에 따라 실행 함수를 네 갈래로 나눠, 필요 없는 분기를 컴파일 시점에 지운다.

## 위치

`executor` / `nodeSeqscan.c` L110-L124 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeSeqscan.c#L110-L124))

## 실제 코드

초기화 때 qual 과 projection 유무로 실행 함수를 고른다. `ExecSeqScan` 은 둘 다 없을 때의 갈래다.

`executor` / `nodeSeqscan.c` L257-L277 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeSeqscan.c#L257-L277))

```c
// nodeSeqscan.c L257-L277
	/*
	 * When EvalPlanQual() is not in use, assign ExecProcNode for this node
	 * based on the presence of qual and projection. Each ExecSeqScan*()
	 * variant is optimized for the specific combination of these conditions.
	 */
	if (scanstate->ss.ps.state->es_epq_active != NULL)
		scanstate->ss.ps.ExecProcNode = ExecSeqScanEPQ;
	else if (scanstate->ss.ps.qual == NULL)
	{
		if (scanstate->ss.ps.ps_ProjInfo == NULL)
			scanstate->ss.ps.ExecProcNode = ExecSeqScan;
		else
			scanstate->ss.ps.ExecProcNode = ExecSeqScanWithProject;
	}
	else
	{
		if (scanstate->ss.ps.ps_ProjInfo == NULL)
			scanstate->ss.ps.ExecProcNode = ExecSeqScanWithQual;
		else
			scanstate->ss.ps.ExecProcNode = ExecSeqScanWithQualProject;
	}
```

네 갈래 중 둘이다. 남은 둘(`WithProject`, `WithQualProject`)은 넘기는 인자만 다르다.

`executor` / `nodeSeqscan.c` L99-L144 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeSeqscan.c#L99-L144))

```c
// nodeSeqscan.c L99-L144
/* ----------------------------------------------------------------
 *		ExecSeqScan(node)
 *
 *		Scans the relation sequentially and returns the next qualifying
 *		tuple. This variant is used when there is no es_epq_active, no qual
 *		and no projection.  Passing const-NULLs for these to ExecScanExtended
 *		allows the compiler to eliminate the additional code that would
 *		ordinarily be required for the evaluation of these.
 * ----------------------------------------------------------------
 */
static TupleTableSlot *
ExecSeqScan(PlanState *pstate)
{
	SeqScanState *node = castNode(SeqScanState, pstate);

	Assert(pstate->state->es_epq_active == NULL);
	Assert(pstate->qual == NULL);
	Assert(pstate->ps_ProjInfo == NULL);

	return ExecScanExtended(&node->ss,
							(ExecScanAccessMtd) SeqNext,
							(ExecScanRecheckMtd) SeqRecheck,
							NULL,
							NULL,
							NULL);
}

/*
 * Variant of ExecSeqScan() but when qual evaluation is required.
 */
static TupleTableSlot *
ExecSeqScanWithQual(PlanState *pstate)
{
	SeqScanState *node = castNode(SeqScanState, pstate);

	Assert(pstate->state->es_epq_active == NULL);
	Assert(pstate->qual != NULL);
	Assert(pstate->ps_ProjInfo == NULL);

	return ExecScanExtended(&node->ss,
							(ExecScanAccessMtd) SeqNext,
							(ExecScanRecheckMtd) SeqRecheck,
							NULL,
							pstate->qual,
							NULL);
}
```

`ExecScanExtended` 는 헤더의 `pg_always_inline` 함수다. 인자로 `NULL` 이 상수로 들어오면 컴파일러가 그 갈래를 지운다.

`src` / `include` / `executor` / `execScan.h` L159-L252 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/executor/execScan.h#L159-L252))

```c
// execScan.h L159-L252
static pg_always_inline TupleTableSlot *
ExecScanExtended(ScanState *node,
				 ExecScanAccessMtd accessMtd,	/* function returning a tuple */
				 ExecScanRecheckMtd recheckMtd,
				 EPQState *epqstate,
				 ExprState *qual,
				 ProjectionInfo *projInfo)
{
	ExprContext *econtext = node->ps.ps_ExprContext;

	/* interrupt checks are in ExecScanFetch */

	/*
	 * If we have neither a qual to check nor a projection to do, just skip
	 * all the overhead and return the raw scan tuple.
	 */
	if (!qual && !projInfo)
	{
		ResetExprContext(econtext);
		return ExecScanFetch(node, epqstate, accessMtd, recheckMtd);
	}

	/*
	 * Reset per-tuple memory context to free any expression evaluation
	 * storage allocated in the previous tuple cycle.
	 */
	ResetExprContext(econtext);

	/*
	 * get a tuple from the access method.  Loop until we obtain a tuple that
	 * passes the qualification.
	 */
	for (;;)
	{
		TupleTableSlot *slot;

		slot = ExecScanFetch(node, epqstate, accessMtd, recheckMtd);

		/*
		 * if the slot returned by the accessMtd contains NULL, then it means
		 * there is nothing more to scan so we just return an empty slot,
		 * being careful to use the projection result slot so it has correct
		 * tupleDesc.
		 */
		if (TupIsNull(slot))
		{
			if (projInfo)
				return ExecClearTuple(projInfo->pi_state.resultslot);
			else
				return slot;
		}

		/*
		 * place the current tuple into the expr context
		 */
		econtext->ecxt_scantuple = slot;

		/*
		 * check that the current tuple satisfies the qual-clause
		 *
		 * check for non-null qual here to avoid a function call to ExecQual()
		 * when the qual is null ... saves only a few cycles, but they add up
		 * ...
		 */
		if (qual == NULL || ExecQual(qual, econtext))
		{
			/*
			 * Found a satisfactory scan tuple.
			 */
			if (projInfo)
			{
				/*
				 * Form a projection tuple, store it in the result tuple slot
				 * and return it.
				 */
				return ExecProject(projInfo);
			}
			else
			{
				/*
				 * Here, we aren't projecting, so just return scan tuple.
				 */
				return slot;
			}
		}
		else
			InstrCountFiltered1(node, 1);

		/*
		 * Tuple fails qual, so free per-tuple memory and try again.
		 */
		ResetExprContext(econtext);
	}
}
```

`ExecScanFetch` 는 인터럽트를 확인하고 접근 함수를 부른다. EvalPlanQual 재검사 중일 때의 대체 경로는 이 흐름에 없어 줄였다.

`src` / `include` / `executor` / `execScan.h` L31-L135 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/executor/execScan.h#L31-L135))

```c
// execScan.h L31-L135
static pg_always_inline TupleTableSlot *
ExecScanFetch(ScanState *node,
			  EPQState *epqstate,
			  ExecScanAccessMtd accessMtd,
			  ExecScanRecheckMtd recheckMtd)
{
	CHECK_FOR_INTERRUPTS();

	// ... (L39-L129 생략: epqstate != NULL 일 때 EvalPlanQual 시험 행을 돌려주는 경로)

	/*
	 * Run the node-type-specific access method function to get the next tuple
	 */
	return (*accessMtd) (node);
}
```

`SeqNext` 가 table AM 경계다. 첫 호출에서 스캔을 열고, 이후에는 같은 스캔 기술자로 다음 행을 받는다.

`executor` / `nodeSeqscan.c` L50-L84 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeSeqscan.c#L50-L84))

```c
// nodeSeqscan.c L50-L84
static TupleTableSlot *
SeqNext(SeqScanState *node)
{
	TableScanDesc scandesc;
	EState	   *estate;
	ScanDirection direction;
	TupleTableSlot *slot;

	/*
	 * get information from the estate and scan state
	 */
	scandesc = node->ss.ss_currentScanDesc;
	estate = node->ss.ps.state;
	direction = estate->es_direction;
	slot = node->ss.ss_ScanTupleSlot;

	if (scandesc == NULL)
	{
		/*
		 * We reach here if the scan is not parallel, or if we're serially
		 * executing a scan that was planned to be parallel.
		 */
		scandesc = table_beginscan(node->ss.ss_currentRelation,
								   estate->es_snapshot,
								   0, NULL);
		node->ss.ss_currentScanDesc = scandesc;
	}

	/*
	 * get the next tuple from the table
	 */
	if (table_scan_getnextslot(scandesc, direction, slot))
		return slot;
	return NULL;
}
```

## 동작 흐름

```text
 ExecInitSeqScan (nodeSeqscan.c L207)
   L263  EPQ 중이면                          ExecSeqScanEPQ (일반 ExecScan)
   L267  qual 없음, projection 없음          ExecSeqScan
   L269  qual 없음, projection 있음          ExecSeqScanWithProject
   L274  qual 있음, projection 없음          ExecSeqScanWithQual
   L276  qual 있음, projection 있음          ExecSeqScanWithQualProject

 실행 (예: ExecSeqScanWithQual -> ExecScanExtended(node, SeqNext, SeqRecheck, NULL, qual, NULL))
   execScan.h
   L175  qual 도 projInfo 도 없으면 ExecScanFetch 한 번으로 끝
   L185  ResetExprContext                         직전 행의 식 계산 메모리를 비운다
   L191  for (;;)
   L195    slot = ExecScanFetch(...)
             L37   CHECK_FOR_INTERRUPTS()           취소 요청은 행마다 여기서 본다
             L134  (*accessMtd)(node) = SeqNext
                     L66  scandesc == NULL 이면
                     L72    table_beginscan(rel, es_snapshot, 0, NULL)   첫 행에서 스캔을 연다
                     L81  table_scan_getnextslot(scandesc, direction, slot)  --> [MVCC 가시성과 스냅샷]
                     L83  끝이면 NULL
   L203    빈 슬롯이면 그대로 (projection 이 있으면 결과 슬롯을 비워서) 돌려준다
   L214    econtext->ecxt_scantuple = slot
   L223    qual == NULL 또는 ExecQual 참이면
   L234      projInfo 가 있으면 ExecProject, 없으면 L241 원래 슬롯
   L245    거짓이면 InstrCountFiltered1 (EXPLAIN 의 Rows Removed by Filter)
   L250    ResetExprContext 후 다음 행
```

projection 유무는 `ExecAssignScanProjectionInfo` 가 정한다. 계획 노드의 targetlist 가 테이블 행 모양과 정확히 같으면(열 번호 순서의 `Var` 만 있고, 삭제된 열이나 `atthasmissing` 열이 없고, 타입이 맞으면) `ps_ProjInfo = NULL` 이다(execUtils.c L606-L611, 판정은 L630-L679 `tlist_matches_tupdesc`). 그래서 `SELECT * FROM t1 WHERE a > 10` 은 보통 `ExecSeqScanWithQual` 이지만, 열이 여럿인 t1 에서 `SELECT a FROM t1 WHERE a > 10` 처럼 일부 열만 뽑으면 `ExecSeqScanWithQualProject` 가 된다. 이 문서의 예시는 projection 이 없는 경우를 가정한다.

조건 검사는 스캔 노드 안에서 끝난다. 필터를 통과하지 못한 행은 부모 노드에 올라가지 않으므로, 부모가 한 번 당길 때 `SeqNext` 는 여러 번 불릴 수 있다.

```text
 ExecSeqScanWithQual 한 번의 호출 (t1 의 다음 행들 a = 3, 40, qual a > 10)

 ExecScanExtended            ExecScanFetch            SeqNext                 table AM
 ----------------            -------------            -------                 --------
 for 1바퀴
   ExecScanFetch  ------->   CHECK_FOR_INTERRUPTS
                             SeqNext  ------------>   getnextslot  -------->  (a=3) 슬롯에 담김
   ExecQual(a > 10)  거짓
   InstrCountFiltered1
   ResetExprContext
 for 2바퀴
   ExecScanFetch  ------->   ...  ---------------->   getnextslot  -------->  (a=40)
   ExecQual  참
 return slot(a=40)   ---> 부모 (ExecutePlan 또는 ExecModifyTable)
```

`SeqNext` 는 스캔 기술자를 노드에 들고 다닌다. 행을 꺼낼 때마다 테이블을 다시 열지 않고, 기술자 안의 위치(현재 블록과 줄)에서 이어 읽는다.

```text
 SeqScanState 가 들고 있는 것 (nodes/execnodes.h 의 ScanState)

 칸                       채우는 곳                        쓰임
 ss_currentRelation       ExecInitSeqScan L235             table_beginscan 의 대상
 ss_ScanTupleSlot         ExecInitSeqScan L241             SeqNext 가 행을 담는 슬롯
 ss_currentScanDesc       SeqNext L75 (first call)         다음 호출의 이어 읽기 위치
 ps.qual                  ExecInitSeqScan L254             ExecScanExtended 의 qual
 ps.ps_ProjInfo           ExecAssignScanProjectionInfo     projection 이 필요할 때만

 ExecEndSeqScan (L289) 이 table_endscan 으로 기술자를 닫는다
```

## 결과가 쓰이는 곳

```text
 돌려준 슬롯
      --> SELECT 면 [05] ExecutePlan 이 receiveSlot 으로 넘긴다
      --> INSERT ... SELECT 면 [08] ExecModifyTable 의 context.planSlot 이 된다 (L4280)
 ss_currentScanDesc
      --> 다음 ExecProcNode 에서 이어 읽고, ExecEndSeqScan 이 닫는다
 InstrCountFiltered1
      --> EXPLAIN ANALYZE 의 "Rows Removed by Filter"
```

## 다루지 않는 것

`table_scan_getnextslot` 아래(`heap_getnextslot`, 페이지 단위 가시성 판정, 동기화 스캔)는 다음 흐름 [MVCC 가시성과 스냅샷](../../mvcc-visibility/README.md)에서 다룬다. 병렬 순차 스캔(`ExecSeqScanInitializeDSM`), EvalPlanQual 재검사(`SeqRecheck`, `ExecScanFetch` 의 EPQ 경로), 식 평가기(`ExecQual`, `ExecProject` 의 내부)는 스캔 노드의 곁가지라 요약만 했다.
