# PortalRun

상위: [쿼리 실행 파이프라인](../README.md)

포털을 **전략대로 실행하는** 함수이자 이 흐름의 출구다. `ONE_SELECT` 는 이미 시작된 실행기에 `ExecutorRun` 으로 행을 요청하고, `ONE_RETURNING` 같은 전략은 먼저 끝까지 실행해 결과를 포털의 튜플 저장소에 모은 뒤 꺼내 주고, `MULTI_QUERY` 는 목록의 문장을 하나씩 `ProcessQuery`(실행기 시작부터 끝까지)나 `PortalRunUtility` 로 돌린다. 앞뒤의 저장/복원 코드는 VACUUM 처럼 **안에서 트랜잭션을 커밋하고 새로 여는** 유틸리티 때문에 있다(L721-L731 주석).

## 위치

`tcop` / `pquery.c` L685-L843 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L685-L843))

## 실제 코드

`tcop` / `pquery.c` L685-L843 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L685-L843))

```c
// tcop/pquery.c L685-L843
PortalRun(Portal portal, long count, bool isTopLevel,
		  DestReceiver *dest, DestReceiver *altdest,
		  QueryCompletion *qc)
{
	bool		result;
	uint64		nprocessed;
	ResourceOwner saveTopTransactionResourceOwner;
	MemoryContext saveTopTransactionContext;
	Portal		saveActivePortal;
	ResourceOwner saveResourceOwner;
	MemoryContext savePortalContext;
	MemoryContext saveMemoryContext;

	Assert(PortalIsValid(portal));

// ... (L700-L711 생략: 추적과 실행 통계)

	/*
	 * Check for improper portal use, and mark portal active.
	 */
	MarkPortalActive(portal);

// ... (L718-L731 생략: 주석)
	saveTopTransactionResourceOwner = TopTransactionResourceOwner;
	saveTopTransactionContext = TopTransactionContext;
	saveActivePortal = ActivePortal;
	saveResourceOwner = CurrentResourceOwner;
	savePortalContext = PortalContext;
	saveMemoryContext = CurrentMemoryContext;
	PG_TRY();
	{
		ActivePortal = portal;
		if (portal->resowner)
			CurrentResourceOwner = portal->resowner;
		PortalContext = portal->portalContext;

		MemoryContextSwitchTo(PortalContext);

		switch (portal->strategy)
		{
			case PORTAL_ONE_SELECT:
			case PORTAL_ONE_RETURNING:
			case PORTAL_ONE_MOD_WITH:
			case PORTAL_UTIL_SELECT:

// ... (L754-L758 생략: 주석)
				if (portal->strategy != PORTAL_ONE_SELECT && !portal->holdStore)
					FillPortalStore(portal, isTopLevel);

				/*
				 * Now fetch desired portion of results.
				 */
				nprocessed = PortalRunSelect(portal, true, count, dest);

// ... (L767-L771 생략: 주석)
				if (qc && portal->qc.commandTag != CMDTAG_UNKNOWN)
				{
					CopyQueryCompletion(qc, &portal->qc);
					qc->nprocessed = nprocessed;
				}

				/* Mark portal not active */
				portal->status = PORTAL_READY;

// ... (L781-L783 생략: 주석)
				result = portal->atEnd;
				break;

			case PORTAL_MULTI_QUERY:
				PortalRunMulti(portal, isTopLevel, false,
							   dest, altdest, qc);

				/* Prevent portal's commands from being re-executed */
				MarkPortalDone(portal);

				/* Always complete at end of RunMulti */
				result = true;
				break;

			default:
				elog(ERROR, "unrecognized portal strategy: %d",
					 (int) portal->strategy);
				result = false; /* keep compiler quiet */
				break;
		}
	}
	PG_CATCH();
	{
// ... (L807-L822 생략: MarkPortalFailed, 전역 변수 복원, 다시 던지기)
	}
	PG_END_TRY();

// ... (L826-L840 생략: 전역 변수 복원과 통계)

	return result;
}
```

`ONE_SELECT` 의 실행이다. 방향과 개수를 정해 `ExecutorRun` 을 부르고 커서 위치를 옮긴다.

`tcop` / `pquery.c` L864-L934 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L864-L934))

```c
// tcop/pquery.c L864-L934
PortalRunSelect(Portal portal,
				bool forward,
				long count,
				DestReceiver *dest)
{
	QueryDesc  *queryDesc;
	ScanDirection direction;
	uint64		nprocessed;

// ... (L873-L876 생략: 주석)
	queryDesc = portal->queryDesc;

	/* Caller messed up if we have neither a ready query nor held data. */
	Assert(queryDesc || portal->holdStore);

// ... (L882-L887 생략: 주석)
	if (queryDesc)
		queryDesc->dest = dest;

// ... (L891-L901 생략: 주석)
	if (forward)
	{
		if (portal->atEnd || count <= 0)
		{
			direction = NoMovementScanDirection;
			count = 0;			/* don't pass negative count to executor */
		}
		else
			direction = ForwardScanDirection;

		/* In the executor, zero count processes all rows */
		if (count == FETCH_ALL)
			count = 0;

		if (portal->holdStore)
			nprocessed = RunFromStore(portal, direction, (uint64) count, dest);
		else
		{
			PushActiveSnapshot(queryDesc->snapshot);
			ExecutorRun(queryDesc, direction, (uint64) count);
			nprocessed = queryDesc->estate->es_processed;
			PopActiveSnapshot();
		}

		if (!ScanDirectionIsNoMovement(direction))
		{
			if (nprocessed > 0)
				portal->atStart = false;	/* OK to go backward now */
			if (count == 0 || nprocessed < (uint64) count)
				portal->atEnd = true;	/* we retrieved 'em all */
			portal->portalPos += nprocessed;
		}
	}
```

`MULTI_QUERY` 의 실행이다. 문장마다 실행기를 처음부터 끝까지 돌리거나 유틸리티를 부른다.

`tcop` / `pquery.c` L1185-L1350 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L1185-L1350))

```c
// tcop/pquery.c L1185-L1350
PortalRunMulti(Portal portal,
			   bool isTopLevel, bool setHoldSnapshot,
			   DestReceiver *dest, DestReceiver *altdest,
			   QueryCompletion *qc)
{
	bool		active_snapshot_set = false;
	ListCell   *stmtlist_item;

// ... (L1193-L1202 생략: 주석)
	if (dest->mydest == DestRemoteExecute)
		dest = None_Receiver;
	if (altdest->mydest == DestRemoteExecute)
		altdest = None_Receiver;

	/*
	 * Loop to handle the individual queries generated from a single parsetree
	 * by analysis and rewrite.
	 */
	foreach(stmtlist_item, portal->stmts)
	{
		PlannedStmt *pstmt = lfirst_node(PlannedStmt, stmtlist_item);

// ... (L1216-L1218 생략: 주석)
		CHECK_FOR_INTERRUPTS();

		if (pstmt->utilityStmt == NULL)
		{
// ... (L1223-L1236 생략: 주석)
			if (!active_snapshot_set)
			{
				Snapshot	snapshot = GetTransactionSnapshot();

				/* If told to, register the snapshot and save in portal */
				if (setHoldSnapshot)
				{
					snapshot = RegisterSnapshot(snapshot);
					portal->holdSnapshot = snapshot;
				}

// ... (L1248-L1256 생략: 주석)
				PushCopiedSnapshot(snapshot);

// ... (L1259-L1262 생략: 주석)

				active_snapshot_set = true;
			}
			else
				UpdateActiveSnapshotCommandId();

			if (pstmt->canSetTag)
			{
				/* statement can set tag string */
				ProcessQuery(pstmt,
							 portal->sourceText,
							 portal->portalParams,
							 portal->queryEnv,
							 dest, qc);
			}
			else
			{
				/* stmt added by rewrite cannot set tag */
				ProcessQuery(pstmt,
							 portal->sourceText,
							 portal->portalParams,
							 portal->queryEnv,
							 altdest, NULL);
			}

// ... (L1288-L1291 생략: 실행 통계)
		}
		else
		{
// ... (L1295-L1305 생략: 주석)
			if (pstmt->canSetTag)
			{
				Assert(!active_snapshot_set);
				/* statement can set tag string */
				PortalRunUtility(portal, pstmt, isTopLevel, false,
								 dest, qc);
			}
			else
			{
				Assert(IsA(pstmt->utilityStmt, NotifyStmt));
				/* stmt added by rewrite cannot set tag */
				PortalRunUtility(portal, pstmt, isTopLevel, false,
								 altdest, NULL);
			}
		}

// ... (L1322-L1324 생략: 주석)
		Assert(portal->portalContext == CurrentMemoryContext);

		MemoryContextDeleteChildren(portal->portalContext);

// ... (L1329-L1336 생략: 주석)
		if (portal->stmts == NIL)
			break;

// ... (L1340-L1343 생략: 주석)
		if (lnext(portal->stmts, stmtlist_item) != NULL)
			CommandCounterIncrement();
	}

	/* Pop the snapshot if we pushed one. */
	if (active_snapshot_set)
		PopActiveSnapshot();
```

실행기 한 바퀴(시작, 실행, 마무리, 끝)를 한자리에서 하는 쪽이다.

`tcop` / `pquery.c` L137-L198 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L137-L198))

```c
// tcop/pquery.c L137-L198
ProcessQuery(PlannedStmt *plan,
			 const char *sourceText,
			 ParamListInfo params,
			 QueryEnvironment *queryEnv,
			 DestReceiver *dest,
			 QueryCompletion *qc)
{
	QueryDesc  *queryDesc;

// ... (L146-L148 생략: 주석)
	queryDesc = CreateQueryDesc(plan, sourceText,
								GetActiveSnapshot(), InvalidSnapshot,
								dest, params, queryEnv, 0);

// ... (L153-L155 생략: 주석)
	ExecutorStart(queryDesc, 0);

// ... (L158-L160 생략: 주석)
	ExecutorRun(queryDesc, ForwardScanDirection, 0);

// ... (L163-L165 생략: 주석)
	if (qc)
	{
		switch (queryDesc->operation)
		{
			case CMD_SELECT:
				SetQueryCompletion(qc, CMDTAG_SELECT, queryDesc->estate->es_processed);
				break;
			case CMD_INSERT:
				SetQueryCompletion(qc, CMDTAG_INSERT, queryDesc->estate->es_processed);
				break;
// ... (L176-L187 생략: UPDATE, DELETE, MERGE, 그 밖)
		}
	}

// ... (L191-L193 생략: 주석)
	ExecutorFinish(queryDesc);
	ExecutorEnd(queryDesc);

	FreeQueryDesc(queryDesc);
}
```

## 동작 흐름

```text
 PortalRun
 L704  qc 초기화
 L716  MarkPortalActive                             PORTAL_READY -> PORTAL_ACTIVE
 L732-L737  TopTransaction 자원 소유자, 컨텍스트, ActivePortal ... 저장
 L738  PG_TRY
 L740-L745  이 포털의 자원 소유자와 컨텍스트로
 L747    switch (portal->strategy)
           ONE_SELECT / ONE_RETURNING / ONE_MOD_WITH / UTIL_SELECT
 L759        ONE_SELECT 가 아니고 holdStore 가 없으면 FillPortalStore
               끝까지 실행해 결과를 튜플 저장소에 모은다
 L765        nprocessed = PortalRunSelect(portal, true, count, dest)
 L772        qc 에 명령 태그와 행 수
 L779        status = PORTAL_READY
 L784        result = atEnd                         다 가져왔으면 true
           MULTI_QUERY
 L788        PortalRunMulti(portal, isTopLevel, false, dest, altdest, qc)
 L792        MarkPortalDone                         다시 실행할 수 없다
 L795        result = true
 L805  PG_CATCH -> MarkPortalFailed, 전역 변수 복원, 다시 던지기
 L826-L835  전역 변수 복원. 원래 값이 TopTransaction 것이었으면 "지금의" TopTransaction 것으로

 PortalRunSelect (ONE_SELECT, 앞으로)
 L889  queryDesc->dest = dest                        매번 다시 정한다 (MOVE 는 DestNone)
 L904  atEnd 거나 count <= 0 이면 NoMovement
 L913  FETCH_ALL 이면 count = 0                      실행기에서 0 은 "전부"
 L920  PushActiveSnapshot(queryDesc->snapshot)
 L921  ExecutorRun(queryDesc, direction, count)     --> [executor]
 L922  nprocessed = estate->es_processed
 L930  count == 0 이거나 덜 가져왔으면 atEnd = true

 PortalRunMulti
 L1203  DestRemoteExecute 면 None_Receiver 로      (확장 프로토콜에서는 행을 보낼 수 없다)
 L1212  foreach PlannedStmt
 L1221    utilityStmt == NULL (계획된 문장)
 L1237      첫 문장이면 GetTransactionSnapshot 을 복사해 활성 스냅샷으로
 L1267      아니면 UpdateActiveSnapshotCommandId     같은 스냅샷, 명령 번호만 올린다
 L1269      canSetTag 면 ProcessQuery(..., dest, qc), 아니면 (..., altdest, NULL)
 L1293    유틸리티
 L1306      canSetTag 면 PortalRunUtility(..., dest, qc)   -> ProcessUtility
 L1327    MemoryContextDeleteChildren(portalContext)
 L1344    다음 문장이 있으면 CommandCounterIncrement
 L1349  PopActiveSnapshot

 ProcessQuery (L137)
 L149  CreateQueryDesc(plan, ..., GetActiveSnapshot(), ..., dest, ...)
 L156  ExecutorStart
 L161  ExecutorRun(ForwardScanDirection, 0)         전부
 L166  qc 에 CMDTAG_SELECT / INSERT / ... 와 es_processed
 L194  ExecutorFinish, L195 ExecutorEnd
 L197  FreeQueryDesc
```

같은 실행기 네 단계가 전략에 따라 다른 함수에 흩어져 있다. 단순 질의의 흔한 세 경우를 나란히 놓으면 이렇다.

```text
 실행기 단계가 불리는 자리 (단순 질의, count = FETCH_ALL)

 statement                  strategy        ExecutorStart      ExecutorRun           ExecutorEnd
 SELECT * FROM t            ONE_SELECT      PortalStart L518   PortalRunSelect L921  PortalCleanup
 INSERT INTO t VALUES (1)   MULTI_QUERY     ProcessQuery L156  ProcessQuery L161     ProcessQuery L195
 INSERT ... RETURNING id    ONE_RETURNING   ProcessQuery L156  ProcessQuery L161     ProcessQuery L195

 ONE_SELECT 만 실행기를 포털에 남겨 둔다. 그래서 커서처럼 조금씩 꺼낼 수 있다
   끝은 포털을 지울 때 PortalCleanup 이 ExecutorFinish / ExecutorEnd 를 부른다
   (commands/portalcmds.c L308-L309)
 ONE_RETURNING 은 L760 FillPortalStore -> PortalRunMulti(setHoldSnapshot = true) 로
   ProcessQuery 를 끝까지 돌려 결과를 튜플 저장소에 담고 (pquery.c L1012-L1023),
   L765 PortalRunSelect 가 그 저장소에서 꺼낸다
```

```text
 MULTI_QUERY 에서 문장 사이의 가시성 (규칙이 질의를 둘로 늘린 경우)

 portal->stmts = [ PlannedStmt A (canSetTag), PlannedStmt B (규칙이 붙인 것) ]

 L1239  snapshot = GetTransactionSnapshot, PushCopiedSnapshot   cid = n
 A      ProcessQuery(dest, qc)                                  qc 는 A 의 결과
 L1345  CommandCounterIncrement                                 cid = n + 1
 B      L1267 UpdateActiveSnapshotCommandId                     스냅샷의 cid 도 n + 1
        ProcessQuery(altdest, NULL)                             A 가 바꾼 행이 B 에 보인다
 L1349  PopActiveSnapshot
```

## 결과가 쓰이는 곳

```text
 ExecutorRun
      --> [executor] standard_ExecutorRun -> ExecutePlan 이 행을 만들어 DestReceiver 로 보낸다
          단순 질의의 DestReceiver 는 printtup, 행마다 DataRow 'D'

 qc (QueryCompletion)
      --> [01] EndCommand 가 "SELECT 3", "INSERT 0 1" 같은 CommandComplete 를 만든다

 반환값 (다 끝났는가)
      --> 단순 질의는 FETCH_ALL 이라 늘 끝까지. 확장 프로토콜 Execute 의 행 수 제한에서 의미가 있다
```

## 다루지 않는 것

`FillPortalStore` 와 `RunFromStore` 의 튜플 저장소, `PortalRunUtility` 와 `ProcessUtility` 이하 DDL 실행, `PortalRunFetch` 의 커서 이동(FETCH ABSOLUTE 등), 역방향 스캔, 실행기 내부([executor](../../executor/README.md)), printtup 의 행 직렬화는 이 흐름의 곁가지라 요약만 했다.
