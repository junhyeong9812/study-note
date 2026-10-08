# ExecutePlan

상위: [executor](../README.md)

**demand-pull 의 바깥 고리다.** 꼭대기 노드에 `ExecProcNode` 를 부르고, 빈 슬롯이 올 때까지 받은 슬롯을 수신자에게 넘기는 일을 반복한다. 트리 안에서 무슨 일이 일어나는지는 모른다. 조인이든 정렬이든 INSERT 든, 이 루프가 보는 것은 "슬롯 하나 또는 끝" 뿐이다.

## 위치

`executor` / `execMain.c` L1660-L1773 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L1660-L1773))

## 실제 코드

`executor` / `execMain.c` L1659-L1773 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L1659-L1773))

```c
// execMain.c L1659-L1773
static void
ExecutePlan(QueryDesc *queryDesc,
			CmdType operation,
			bool sendTuples,
			uint64 numberTuples,
			ScanDirection direction,
			DestReceiver *dest)
{
	EState	   *estate = queryDesc->estate;
	PlanState  *planstate = queryDesc->planstate;
	bool		use_parallel_mode;
	TupleTableSlot *slot;
	uint64		current_tuple_count;

	/*
	 * initialize local variables
	 */
	current_tuple_count = 0;

	/*
	 * Set the direction.
	 */
	estate->es_direction = direction;

	/*
	 * Set up parallel mode if appropriate.
	 *
	 * Parallel mode only supports complete execution of a plan.  If we've
	 * already partially executed it, or if the caller asks us to exit early,
	 * we must force the plan to run without parallelism.
	 */
	if (queryDesc->already_executed || numberTuples != 0)
		use_parallel_mode = false;
	else
		use_parallel_mode = queryDesc->plannedstmt->parallelModeNeeded;
	queryDesc->already_executed = true;

	estate->es_use_parallel_mode = use_parallel_mode;
	if (use_parallel_mode)
		EnterParallelMode();

	/*
	 * Loop until we've processed the proper number of tuples from the plan.
	 */
	for (;;)
	{
		/* Reset the per-output-tuple exprcontext */
		ResetPerTupleExprContext(estate);

		/*
		 * Execute the plan and obtain a tuple
		 */
		slot = ExecProcNode(planstate);

		/*
		 * if the tuple is null, then we assume there is nothing more to
		 * process so we just end the loop...
		 */
		if (TupIsNull(slot))
			break;

		/*
		 * If we have a junk filter, then project a new tuple with the junk
		 * removed.
		 *
		 * Store this new "clean" tuple in the junkfilter's resultSlot.
		 * (Formerly, we stored it back over the "dirty" tuple, which is WRONG
		 * because that tuple slot has the wrong descriptor.)
		 */
		if (estate->es_junkFilter != NULL)
			slot = ExecFilterJunk(estate->es_junkFilter, slot);

		/*
		 * If we are supposed to send the tuple somewhere, do so. (In
		 * practice, this is probably always the case at this point.)
		 */
		if (sendTuples)
		{
			/*
			 * If we are not able to send the tuple, we assume the destination
			 * has closed and no more tuples can be sent. If that's the case,
			 * end the loop.
			 */
			if (!dest->receiveSlot(slot, dest))
				break;
		}

		/*
		 * Count tuples processed, if this is a SELECT.  (For other operation
		 * types, the ModifyTable plan node must count the appropriate
		 * events.)
		 */
		if (operation == CMD_SELECT)
			(estate->es_processed)++;

		/*
		 * check our tuple count.. if we've processed the proper number then
		 * quit, else loop again and process more tuples.  Zero numberTuples
		 * means no limit.
		 */
		current_tuple_count++;
		if (numberTuples && numberTuples == current_tuple_count)
			break;
	}

	/*
	 * If we know we won't need to back up, we can release resources at this
	 * point.
	 */
	if (!(estate->es_top_eflags & EXEC_FLAG_BACKWARD))
		ExecShutdownNode(planstate);

	if (use_parallel_mode)
		ExitParallelMode();
}
```

## 동작 흐름

```text
 L1681 es_direction = direction                 스캔 노드가 읽는다 (SeqNext 의 estate->es_direction)

 L1690 이미 실행한 적 있거나 numberTuples != 0 이면 병렬 금지
         병렬 계획은 한 번에 끝까지 돌 때만 쓴다 (L1686-L1688 주석)
 L1694 already_executed = true
 L1698 병렬이면 EnterParallelMode

 L1703 for (;;)
 L1706   ResetPerTupleExprContext(estate)      직전 행의 식 계산 메모리를 비운다
 L1711   slot = ExecProcNode(planstate)        --> [06] (첫 호출) 또는 노드 함수 직행
 L1717   TupIsNull(slot) 이면 break            끝
 L1728   junk filter 가 있으면 ExecFilterJunk 숨은 열 제거
 L1735   sendTuples 면
 L1742     dest->receiveSlot(slot, dest)        false 면 수신자가 닫혔다고 보고 break
 L1751   SELECT 면 es_processed++               쓰기는 ModifyTable 이 센다
 L1759   current_tuple_count++
 L1760   numberTuples 에 닿으면 break           커서 FETCH n

 L1768 BACKWARD 플래그가 없으면 ExecShutdownNode    병렬 워커 등 자원을 일찍 놓는다
 L1772 병렬이면 ExitParallelMode
```

루프 한 바퀴의 메모리는 `ResetPerTupleExprContext` 로 비운다. 그래서 행마다 식을 계산하며 쓴 메모리가 행 수만큼 쌓이지 않는다.

```text
 메모리 수명 (실행 하나)

 es_query_cxt               PlanState 트리, 슬롯, 열린 릴레이션. [01] 부터 [10] 의 ExecutorEnd 까지
   per-tuple ExprContext    qual, projection 계산의 임시 값. 루프 한 바퀴
     L1706 에서 매 바퀴 리셋

 그래서 L1742 receiveSlot 은 슬롯 내용을 다음 바퀴 전에 다 써야 한다
 (printtup 은 받는 즉시 메시지로 직렬화한다)
```

이 루프가 꼭대기에서 한 번 당길 때 아래에서 몇 번의 당김이 일어나는지는 노드가 정한다. 필터가 행을 버리면 스캔은 여러 번 돌고, `ModifyTable` 은 자식을 다 비울 때까지 돌아오지 않는다.

```text
 SELECT * FROM t1 WHERE a > 10    (t1 = 5, 12, 3, 40, 18 순서)

 바퀴  돌아온 슬롯  receiveSlot  es_processed  SeqNext 로 꺼낸 행과 qual
 1     a=12         O            1             5 거짓, 12 참
 2     a=40         O            2             3 거짓, 40 참
 3     a=18         O            3             18 참
 4     empty        X            3             더 없음 -> break

 INSERT INTO t2 SELECT * FROM t1 WHERE a > 10

 바퀴  돌아온 슬롯  es_processed  ExecModifyTable 안에서 일어난 일
 1     NULL         3             12, 40, 18 을 ExecInsert, 자식이 빈 슬롯 -> fireASTriggers -> break
```

## 결과가 쓰이는 곳

```text
 dest->receiveSlot 으로 넘긴 슬롯
      --> 클라이언트, 튜플스토어, SPI 결과 등 수신자 종류마다 다르게 소비된다
 es_processed (SELECT)
      --> [04] 가 es_total_processed 에 더한다
 ExecShutdownNode
      --> Gather 노드면 병렬 워커를 이때 정리한다 (뒤로 읽을 일이 없을 때만)
```

## 다루지 않는 것

병렬 모드(`EnterParallelMode`, `parallelModeNeeded`)와 `ExecShutdownNode` 가 노드별로 하는 일, junk filter(`ExecFilterJunk`), 수신자가 `false` 를 돌려주는 경우(예: 클라이언트 연결 종료가 아닌 수신자 자체의 중단)는 루프의 곁가지라 요약만 했다.
