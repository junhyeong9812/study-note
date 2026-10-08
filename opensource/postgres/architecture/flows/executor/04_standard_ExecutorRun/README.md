# standard_ExecutorRun

상위: [executor](../README.md)

**결과를 받을 쪽(`DestReceiver`)을 열고 `ExecutePlan` 에 실행을 맡긴 뒤 다시 닫는 틀이다.** 행을 돌려주는 문장(SELECT, 또는 RETURNING 이 붙은 쓰기)일 때만 수신자를 연다. 한 `QueryDesc` 에 여러 번 불릴 수 있어서(커서의 FETCH), 이번 호출의 처리 행 수와 누적 행 수를 따로 센다.

## 위치

`executor` / `execMain.c` L307-L389 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L307-L389))

## 실제 코드

진입점은 `ExecutorStart` 와 같은 모양의 훅 껍데기다.

`executor` / `execMain.c` L296-L304 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L296-L304))

```c
// execMain.c L296-L304
void
ExecutorRun(QueryDesc *queryDesc,
			ScanDirection direction, uint64 count)
{
	if (ExecutorRun_hook)
		(*ExecutorRun_hook) (queryDesc, direction, count);
	else
		standard_ExecutorRun(queryDesc, direction, count);
}
```

본체다.

`executor` / `execMain.c` L306-L389 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L306-L389))

```c
// execMain.c L306-L389
void
standard_ExecutorRun(QueryDesc *queryDesc,
					 ScanDirection direction, uint64 count)
{
	EState	   *estate;
	CmdType		operation;
	DestReceiver *dest;
	bool		sendTuples;
	MemoryContext oldcontext;

	/* sanity checks */
	Assert(queryDesc != NULL);

	estate = queryDesc->estate;

	Assert(estate != NULL);
	Assert(!(estate->es_top_eflags & EXEC_FLAG_EXPLAIN_ONLY));

	/* caller must ensure the query's snapshot is active */
	Assert(GetActiveSnapshot() == estate->es_snapshot);

	/*
	 * Switch into per-query memory context
	 */
	oldcontext = MemoryContextSwitchTo(estate->es_query_cxt);

	/* Allow instrumentation of Executor overall runtime */
	if (queryDesc->totaltime)
		InstrStartNode(queryDesc->totaltime);

	/*
	 * extract information from the query descriptor and the query feature.
	 */
	operation = queryDesc->operation;
	dest = queryDesc->dest;

	/*
	 * startup tuple receiver, if we will be emitting tuples
	 */
	estate->es_processed = 0;

	sendTuples = (operation == CMD_SELECT ||
				  queryDesc->plannedstmt->hasReturning);

	if (sendTuples)
		dest->rStartup(dest, operation, queryDesc->tupDesc);

	/*
	 * Run plan, unless direction is NoMovement.
	 *
	 * Note: pquery.c selects NoMovement if a prior call already reached
	 * end-of-data in the user-specified fetch direction.  This is important
	 * because various parts of the executor can misbehave if called again
	 * after reporting EOF.  For example, heapam.c would actually restart a
	 * heapscan and return all its data afresh.  There is also some doubt
	 * about whether a parallel plan would operate properly if an additional,
	 * necessarily non-parallel execution request occurs after completing a
	 * parallel execution.  (That case should work, but it's untested.)
	 */
	if (!ScanDirectionIsNoMovement(direction))
		ExecutePlan(queryDesc,
					operation,
					sendTuples,
					count,
					direction,
					dest);

	/*
	 * Update es_total_processed to keep track of the number of tuples
	 * processed across multiple ExecutorRun() calls.
	 */
	estate->es_total_processed += estate->es_processed;

	/*
	 * shutdown tuple receiver, if we started it
	 */
	if (sendTuples)
		dest->rShutdown(dest);

	if (queryDesc->totaltime)
		InstrStopNode(queryDesc->totaltime, estate->es_processed);

	MemoryContextSwitchTo(oldcontext);
}
```

## 동작 흐름

```text
 L325  호출자가 es_snapshot 을 활성 스냅샷으로 걸어 두었는지 확인
 L330  es_query_cxt 로 전환                      [01] 이 만든 per-query 메모리
 L333  EXPLAIN ANALYZE 면 전체 시간 계측 시작

 L345  es_processed = 0                          이번 호출의 행 수
 L347  sendTuples = SELECT 이거나 hasReturning
 L351    dest->rStartup(dest, operation, tupDesc)  예: printtup 이면 RowDescription 전송

 L365  direction 이 NoMovement 가 아니면
 L366    ExecutePlan(queryDesc, operation, sendTuples, count, direction, dest)   --> [05]

 L377  es_total_processed += es_processed       여러 번 불린 합계
 L383  sendTuples 면 dest->rShutdown
 L386  계측 종료, L388 컨텍스트 복귀
```

`count` 는 "최대 몇 행"이다. 0 이면 끝까지 돈다. L279-L282 주석대로 이 상한은 돌려주는 행에만 걸리고, `ModifyTable` 이 넣거나 지운 행 수에는 걸리지 않는다.

```text
 같은 queryDesc 에 ExecutorRun 이 여러 번 오는 경우 (커서, 결과 행 10개)

 호출      count  direction    es_processed  es_total_processed  ExecutePlan 이 돌려준 행
 FETCH 4   4      Forward      4             4                   r1 r2 r3 r4
 FETCH 4   4      Forward      4             8                   r5 r6 r7 r8
 FETCH 4   4      Forward      2             10                  r9 r10, 그다음 빈 슬롯
 FETCH 4   0      NoMovement   0             10                  ExecutePlan 을 부르지 않는다

 3번째 호출에서 2 < 4 라 PortalRunSelect 가 atEnd = true 로 둔다 (pquery.c L930-L931)
 4번째 호출은 atEnd 라 NoMovement, count = 0 으로 바꿔 넘긴다 (pquery.c L904-L908)
 끝난 노드를 다시 부르면 heapam 이 스캔을 처음부터 다시 돌려줄 수 있어서다 (L356-L363 주석)
```

수신자를 열고 닫는 일은 이 함수가, 행마다 넘기는 일은 [05] 가 한다. 그래서 RETURNING 없는 INSERT 는 수신자 콜백을 하나도 부르지 않는다.

```text
 sendTuples 판정 (L347)

 문장                              operation    hasReturning   sendTuples   rStartup / receiveSlot
 SELECT ...                        CMD_SELECT   false          true         부른다
 INSERT ... SELECT ...             CMD_INSERT   false          false        부르지 않는다
 INSERT ... RETURNING id           CMD_INSERT   true           true         부른다
```

## 결과가 쓰이는 곳

```text
 estate->es_processed
      --> PortalRunSelect 가 nprocessed 로 읽어 커서 위치를 옮기고 (pquery.c L922)
          ProcessQuery 가 명령 완료 태그의 행 수로 쓴다 (pquery.c L174)
 estate->es_total_processed
      --> 여러 번의 FETCH 를 합친 수
 dest 의 rStartup / rShutdown
      --> printtup 수신자는 sendDescrip 이면 rStartup 에서 RowDescription 을 보낸다
          (access/common/printtup.c L136)
```

## 다루지 않는 것

`DestReceiver` 의 종류(클라이언트, 튜플스토어, SPI, `COPY TO`, `CREATE TABLE AS`)와 각각의 콜백, 계측(`Instrumentation`, `InstrStartNode`), 커서의 뒤로 읽기(`BackwardScanDirection`)와 `EXEC_FLAG_BACKWARD` 는 실행 틀의 곁가지라 요약만 했다.
