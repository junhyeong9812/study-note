# standard_ExecutorFinish

상위: [executor](../README.md)

**실행이 끝난 뒤 남은 일을 두 단계로 처리한다.** `ExecutorFinish` 는 아직 일이 남은 쓰기를 마무리한다. CTE 안의 `ModifyTable` 을 끝까지 돌리고, [09] 가 큐에 쌓아 둔 AFTER 트리거를 실행한다. 그다음 `ExecutorEnd` 가 `PlanState` 트리를 내려가며 스캔을 닫고 pin 을 풀고 릴레이션을 닫은 뒤 per-query 메모리를 통째로 버린다. 둘을 나눈 이유는 주석에 있다. EXPLAIN ANALYZE 가 AFTER 트리거 시간까지 실행 시간에 넣으려면 트리거 실행이 정리와 따로 있어야 한다.

## 위치

`executor` / `execMain.c` L415-L451 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L415-L451))

`standard_ExecutorEnd` 는 같은 파일 L475-L526 이다. 둘 다 이 문서에서 다룬다.

## 실제 코드

`ExecutorFinish` 의 주석이 두 함수를 나눈 이유를 적고 있다.

`executor` / `execMain.c` L391-L451 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L391-L451))

```c
// execMain.c L391-L451
/* ----------------------------------------------------------------
 *		ExecutorFinish
 *
 *		This routine must be called after the last ExecutorRun call.
 *		It performs cleanup such as firing AFTER triggers.  It is
 *		separate from ExecutorEnd because EXPLAIN ANALYZE needs to
 *		include these actions in the total runtime.
 *
 *		We provide a function hook variable that lets loadable plugins
 *		get control when ExecutorFinish is called.  Such a plugin would
 *		normally call standard_ExecutorFinish().
 *
 * ----------------------------------------------------------------
 */
void
ExecutorFinish(QueryDesc *queryDesc)
{
	if (ExecutorFinish_hook)
		(*ExecutorFinish_hook) (queryDesc);
	else
		standard_ExecutorFinish(queryDesc);
}

void
standard_ExecutorFinish(QueryDesc *queryDesc)
{
	EState	   *estate;
	MemoryContext oldcontext;

	/* sanity checks */
	Assert(queryDesc != NULL);

	estate = queryDesc->estate;

	Assert(estate != NULL);
	Assert(!(estate->es_top_eflags & EXEC_FLAG_EXPLAIN_ONLY));

	/* This should be run once and only once per Executor instance */
	Assert(!estate->es_finished);

	/* Switch into per-query memory context */
	oldcontext = MemoryContextSwitchTo(estate->es_query_cxt);

	/* Allow instrumentation of Executor overall runtime */
	if (queryDesc->totaltime)
		InstrStartNode(queryDesc->totaltime);

	/* Run ModifyTable nodes to completion */
	ExecPostprocessPlan(estate);

	/* Execute queued AFTER triggers, unless told not to */
	if (!(estate->es_top_eflags & EXEC_FLAG_SKIP_TRIGGERS))
		AfterTriggerEndQuery(estate);

	if (queryDesc->totaltime)
		InstrStopNode(queryDesc->totaltime, 0);

	MemoryContextSwitchTo(oldcontext);

	estate->es_finished = true;
}
```

`ExecPostprocessPlan` 은 주 쿼리가 다 읽지 않았을 수 있는 보조 `ModifyTable`(쓰는 CTE)을 끝까지 돌린다.

`executor` / `execMain.c` L1493-L1525 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L1493-L1525))

```c
// execMain.c L1493-L1525
static void
ExecPostprocessPlan(EState *estate)
{
	ListCell   *lc;

	/*
	 * Make sure nodes run forward.
	 */
	estate->es_direction = ForwardScanDirection;

	/*
	 * Run any secondary ModifyTable nodes to completion, in case the main
	 * query did not fetch all rows from them.  (We do this to ensure that
	 * such nodes have predictable results.)
	 */
	foreach(lc, estate->es_auxmodifytables)
	{
		PlanState  *ps = (PlanState *) lfirst(lc);

		for (;;)
		{
			TupleTableSlot *slot;

			/* Reset the per-output-tuple exprcontext each time */
			ResetPerTupleExprContext(estate);

			slot = ExecProcNode(ps);

			if (TupIsNull(slot))
				break;
		}
	}
}
```

`AfterTriggerEndQuery` 가 이 문장의 층에 쌓인 이벤트를 실행한다. 실행할 것과 미룰 것을 먼저 다 가른 뒤에 실행한다.

`commands` / `trigger.c` L5140-L5221 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/trigger.c#L5140-L5221))

```c
// trigger.c L5140-L5221
void
AfterTriggerEndQuery(EState *estate)
{
	AfterTriggersQueryData *qs;

	/* Must be inside a query, too */
	Assert(afterTriggers.query_depth >= 0);

	/*
	 * If we never even got as far as initializing the event stack, there
	 * certainly won't be any events, so exit quickly.
	 */
	if (afterTriggers.query_depth >= afterTriggers.maxquerydepth)
	{
		afterTriggers.query_depth--;
		return;
	}

	/*
	 * Process all immediate-mode triggers queued by the query, and move the
	 * deferred ones to the main list of deferred events.
	 *
	 * Notice that we decide which ones will be fired, and put the deferred
	 * ones on the main list, before anything is actually fired.  This ensures
	 * reasonably sane behavior if a trigger function does SET CONSTRAINTS ...
	 * IMMEDIATE: all events we have decided to defer will be available for it
	 * to fire.
	 *
	 * We loop in case a trigger queues more events at the same query level.
	 * Ordinary trigger functions, including all PL/pgSQL trigger functions,
	 * will instead fire any triggers in a dedicated query level.  Foreign key
	 * enforcement triggers do add to the current query level, thanks to their
	 * passing fire_triggers = false to SPI_execute_snapshot().  Other
	 * C-language triggers might do likewise.
	 *
	 * If we find no firable events, we don't have to increment
	 * firing_counter.
	 */
	qs = &afterTriggers.query_stack[afterTriggers.query_depth];

	for (;;)
	{
		if (afterTriggerMarkEvents(&qs->events, &afterTriggers.events, true))
		{
			CommandId	firing_id = afterTriggers.firing_counter++;
			AfterTriggerEventChunk *oldtail = qs->events.tail;

			if (afterTriggerInvokeEvents(&qs->events, firing_id, estate, false))
				break;			/* all fired */

			// ... (L5190-L5211 생략: 실행 중 큐가 재할당될 수 있어 qs 를 다시 잡고 다 쓴 chunk 를 지운다)
		}
		else
			break;
	}

	/* Release query-level-local storage, including tuplestores if any */
	AfterTriggerFreeQuery(&afterTriggers.query_stack[afterTriggers.query_depth]);

	afterTriggers.query_depth--;
}
```

정리 쪽이다. `ExecutorFinish` 를 건너뛰었는지 확인한 뒤 트리를 정리하고 스냅샷을 놓고 메모리를 버린다.

`executor` / `execMain.c` L474-L526 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L474-L526))

```c
// execMain.c L474-L526
void
standard_ExecutorEnd(QueryDesc *queryDesc)
{
	EState	   *estate;
	MemoryContext oldcontext;

	/* sanity checks */
	Assert(queryDesc != NULL);

	estate = queryDesc->estate;

	Assert(estate != NULL);

	if (estate->es_parallel_workers_to_launch > 0)
		pgstat_update_parallel_workers_stats((PgStat_Counter) estate->es_parallel_workers_to_launch,
											 (PgStat_Counter) estate->es_parallel_workers_launched);

	/*
	 * Check that ExecutorFinish was called, unless in EXPLAIN-only mode. This
	 * Assert is needed because ExecutorFinish is new as of 9.1, and callers
	 * might forget to call it.
	 */
	Assert(estate->es_finished ||
		   (estate->es_top_eflags & EXEC_FLAG_EXPLAIN_ONLY));

	/*
	 * Switch into per-query memory context to run ExecEndPlan
	 */
	oldcontext = MemoryContextSwitchTo(estate->es_query_cxt);

	ExecEndPlan(queryDesc->planstate, estate);

	/* do away with our snapshots */
	UnregisterSnapshot(estate->es_snapshot);
	UnregisterSnapshot(estate->es_crosscheck_snapshot);

	/*
	 * Must switch out of context before destroying it
	 */
	MemoryContextSwitchTo(oldcontext);

	/*
	 * Release EState and per-query memory context.  This should release
	 * everything the executor has allocated.
	 */
	FreeExecutorState(estate);

	/* Reset queryDesc fields that no longer point to anything */
	queryDesc->tupDesc = NULL;
	queryDesc->estate = NULL;
	queryDesc->planstate = NULL;
	queryDesc->totaltime = NULL;
}
```

`executor` / `execMain.c` L1539-L1573 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L1539-L1573))

```c
// execMain.c L1539-L1573
static void
ExecEndPlan(PlanState *planstate, EState *estate)
{
	ListCell   *l;

	/*
	 * shut down the node-type-specific query processing
	 */
	ExecEndNode(planstate);

	/*
	 * for subplans too
	 */
	foreach(l, estate->es_subplanstates)
	{
		PlanState  *subplanstate = (PlanState *) lfirst(l);

		ExecEndNode(subplanstate);
	}

	/*
	 * destroy the executor's tuple table.  Actually we only care about
	 * releasing buffer pins and tupdesc refcounts; there's no need to pfree
	 * the TupleTableSlots, since the containing memory context is about to go
	 * away anyway.
	 */
	ExecResetTupleTable(estate->es_tupleTable, false);

	/*
	 * Close any Relations that have been opened for range table entries or
	 * result relations.
	 */
	ExecCloseResultRelations(estate);
	ExecCloseRangeTableRelations(estate);
}
```

## 동작 흐름

```text
 standard_ExecutorFinish
 L429  es_finished 가 아직 false 인지 (한 번만 불려야 한다)
 L432  es_query_cxt 로 전환
 L439  ExecPostprocessPlan(estate)
         L1501  방향을 Forward 로
         L1508  es_auxmodifytables 의 각 ModifyTable 에
         L1519    빈 슬롯이 나올 때까지 ExecProcNode    (이미 끝난 노드는 mt_done 으로 바로 NULL)
 L442  SKIP_TRIGGERS 가 아니면
 L443    AfterTriggerEndQuery(estate)
           L5152  이벤트 스택을 만든 적도 없으면 depth-- 하고 끝
           L5180  for (;;)
           L5182    afterTriggerMarkEvents(&qs->events, &afterTriggers.events, true)
                      IMMEDIATE 는 실행 표시, DEFERRED 는 전역 목록으로 옮긴다
           L5187    afterTriggerInvokeEvents               표시한 것을 실행
                      트리거가 같은 층에 새 이벤트를 쌓으면 다시 돈다
           L5218  AfterTriggerFreeQuery
           L5220  query_depth--
 L450  es_finished = true

 standard_ExecutorEnd
 L496  es_finished 이거나 EXPLAIN_ONLY 인지 확인
 L504  ExecEndPlan(planstate, estate)
         L1547  ExecEndNode(planstate)           트리를 내려가며 노드별 ExecEndXxx
                  SeqScan 이면 ExecEndSeqScan -> table_endscan (nodeSeqscan.c L302)
         L1552  서브플랜들도 ExecEndNode
         L1565  ExecResetTupleTable             슬롯이 잡은 buffer pin 을 푼다
         L1571  ExecCloseResultRelations         결과 테이블의 인덱스를 닫는다
         L1572  ExecCloseRangeTableRelations     열었던 릴레이션을 닫는다 (잠금은 유지)
 L507  UnregisterSnapshot(es_snapshot), es_crosscheck_snapshot
 L519  FreeExecutorState(estate)                es_query_cxt 째로 메모리를 버린다
 L522  queryDesc 의 tupDesc, estate, planstate, totaltime 을 NULL 로
```

AFTER 트리거는 "문장이 다 끝난 뒤" 실행되지만 아직 같은 트랜잭션 안이고, `ExecutorEnd` 보다 먼저다. 그래서 트리거 안에서 ERROR 가 나면 문장 전체가 실패한다.

```text
 INSERT INTO t2 SELECT ... (행 3개) 의 시간축, ProcessQuery 기준 (pquery.c L156-L195)

 ExecutorStart   L156  AfterTriggerBeginQuery            큐 층 열기
 ExecutorRun     L161  BS 트리거 실행
                       r1: BR 실행, 힙, 인덱스, AR 적재
                       r2: BR 실행, 힙, 인덱스, AR 적재
                       r3: BR 실행, 힙, 인덱스, AR 적재
                       AS 적재
 (qc)            L174  SetQueryCompletion(INSERT, 3)
 ExecutorFinish  L194  AR(r1) AR(r2) AR(r3) AS 실행      여기서 ERROR 면 문장 실패
 ExecutorEnd     L195  스캔 닫기, pin 해제, 메모리 해제

 BS = BEFORE STATEMENT, BR = BEFORE ROW, AR = AFTER ROW, AS = AFTER STATEMENT
 DEFERRED 로 선언된 제약 트리거는 ExecutorFinish 에서 실행되지 않고 커밋 때 실행된다
```

릴레이션은 닫지만 잠금은 풀지 않는다. L1636 주석("We do not release any locks")대로, 실행 중에 잡은 테이블 잠금은 트랜잭션 끝까지 남는다.

```text
 ExecutorEnd 뒤에 남는 것과 사라지는 것

 사라지는 것
   PlanState 트리, 슬롯, 식 상태 (es_query_cxt 째로)
   스캔 기술자와 buffer pin (ExecEndNode, ExecResetTupleTable)
   스냅샷 등록 (UnregisterSnapshot)

 남는 것
   테이블 잠금 (RowExclusiveLock 등)
      --> 트랜잭션 끝에 [heavyweight lock] 의 LockReleaseAll
   힙, 인덱스에 쓴 행과 WAL 레코드
      --> [커밋] 이 commit 레코드를 쓰고 flush 한다
   DEFERRED 트리거 이벤트
      --> [커밋] 의 AfterTriggerFireDeferred
```

## 결과가 쓰이는 곳

```text
 AFTER 트리거 실행 결과
      --> 트리거가 다른 테이블을 바꿨다면 그 쓰기도 같은 트랜잭션의 일부다
 es_finished
      --> ExecutorEnd 의 Assert 가 ExecutorFinish 를 빼먹은 호출자를 잡는다 (L491-L497)
 queryDesc (estate, planstate 가 NULL)
      --> 호출자가 FreeQueryDesc 로 버린다 (pquery.c L197)
```

## 다루지 않는 것

AFTER 트리거 큐의 구조(이벤트 chunk, `AfterTriggerSharedData`)와 표시, 실행 규칙(`afterTriggerMarkEvents`, `afterTriggerInvokeEvents`), 전이 테이블 tuplestore 정리, 노드별 `ExecEndXxx` 와 `ExecShutdownNode` 의 차이, `ExecutorRewind` 는 마무리 단계의 곁가지라 요약만 했다.
