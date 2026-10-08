# PortalStart

상위: [쿼리 실행 파이프라인](../README.md)

포털을 **실행할 수 있는 상태(`PORTAL_READY`)로 만드는** 함수다. 먼저 `PlannedStmt` 목록의 모양을 보고 실행 전략 다섯 가지 중 하나를 고른다. 전략이 `PORTAL_ONE_SELECT` 일 때만 여기서 스냅샷을 잡고 `ExecutorStart` 까지 부른다. 나머지 전략은 결과 행의 모양(`tupDesc`)만 정해 두고 실행기 시작을 [10] `PortalRun` 으로 미룬다.

## 위치

`tcop` / `pquery.c` L434-L611 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L434-L611))

## 실제 코드

`tcop` / `pquery.c` L434-L611 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L434-L611))

```c
// tcop/pquery.c L434-L611
PortalStart(Portal portal, ParamListInfo params,
			int eflags, Snapshot snapshot)
{
	Portal		saveActivePortal;
	ResourceOwner saveResourceOwner;
	MemoryContext savePortalContext;
	MemoryContext oldContext;
	QueryDesc  *queryDesc;
	int			myeflags;

	Assert(PortalIsValid(portal));
	Assert(portal->status == PORTAL_DEFINED);

	/*
	 * Set up global portal context pointers.
	 */
	saveActivePortal = ActivePortal;
	saveResourceOwner = CurrentResourceOwner;
	savePortalContext = PortalContext;
	PG_TRY();
	{
		ActivePortal = portal;
		if (portal->resowner)
			CurrentResourceOwner = portal->resowner;
		PortalContext = portal->portalContext;

		oldContext = MemoryContextSwitchTo(PortalContext);

		/* Must remember portal param list, if any */
		portal->portalParams = params;

		/*
		 * Determine the portal execution strategy
		 */
		portal->strategy = ChoosePortalStrategy(portal->stmts);

		/*
		 * Fire her up according to the strategy
		 */
		switch (portal->strategy)
		{
			case PORTAL_ONE_SELECT:

				/* Must set snapshot before starting executor. */
				if (snapshot)
					PushActiveSnapshot(snapshot);
				else
					PushActiveSnapshot(GetTransactionSnapshot());

// ... (L483-L491 생략: 주석)
				/*
				 * Create QueryDesc in portal's context; for the moment, set
				 * the destination to DestNone.
				 */
				queryDesc = CreateQueryDesc(linitial_node(PlannedStmt, portal->stmts),
											portal->sourceText,
											GetActiveSnapshot(),
											InvalidSnapshot,
											None_Receiver,
											params,
											portal->queryEnv,
											0);

// ... (L505-L509 생략: 주석)
				if (portal->cursorOptions & CURSOR_OPT_SCROLL)
					myeflags = eflags | EXEC_FLAG_REWIND | EXEC_FLAG_BACKWARD;
				else
					myeflags = eflags;

				/*
				 * Call ExecutorStart to prepare the plan for execution
				 */
				ExecutorStart(queryDesc, myeflags);

				/*
				 * This tells PortalCleanup to shut down the executor
				 */
				portal->queryDesc = queryDesc;

				/*
				 * Remember tuple descriptor (computed by ExecutorStart)
				 */
				portal->tupDesc = queryDesc->tupDesc;

				/*
				 * Reset cursor position data to "start of query"
				 */
				portal->atStart = true;
				portal->atEnd = false;	/* allow fetches */
				portal->portalPos = 0;

				PopActiveSnapshot();
				break;

			case PORTAL_ONE_RETURNING:
			case PORTAL_ONE_MOD_WITH:

// ... (L543-L546 생략: 주석)
				{
					PlannedStmt *pstmt;

					pstmt = PortalGetPrimaryStmt(portal);
					portal->tupDesc =
						ExecCleanTypeFromTL(pstmt->planTree->targetlist);
				}

				/*
				 * Reset cursor position data to "start of query"
				 */
				portal->atStart = true;
				portal->atEnd = false;	/* allow fetches */
				portal->portalPos = 0;
				break;

			case PORTAL_UTIL_SELECT:

// ... (L565-L568 생략: 주석)
				{
					PlannedStmt *pstmt = PortalGetPrimaryStmt(portal);

					Assert(pstmt->commandType == CMD_UTILITY);
					portal->tupDesc = UtilityTupleDescriptor(pstmt->utilityStmt);
				}

				/*
				 * Reset cursor position data to "start of query"
				 */
				portal->atStart = true;
				portal->atEnd = false;	/* allow fetches */
				portal->portalPos = 0;
				break;

			case PORTAL_MULTI_QUERY:
				/* Need do nothing now */
				portal->tupDesc = NULL;
				break;
		}
	}
	PG_CATCH();
	{
		/* Uncaught error while executing portal: mark it dead */
		MarkPortalFailed(portal);

		/* Restore global vars and propagate error */
		ActivePortal = saveActivePortal;
		CurrentResourceOwner = saveResourceOwner;
		PortalContext = savePortalContext;

		PG_RE_THROW();
	}
	PG_END_TRY();

	MemoryContextSwitchTo(oldContext);

	ActivePortal = saveActivePortal;
	CurrentResourceOwner = saveResourceOwner;
	PortalContext = savePortalContext;

	portal->status = PORTAL_READY;
}
```

전략을 고르는 쪽이다. 목록 길이, `canSetTag`, 명령 종류, RETURNING 유무로 정한다.

`tcop` / `pquery.c` L209-L317 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/pquery.c#L209-L317))

```c
// tcop/pquery.c L209-L317
PortalStrategy
ChoosePortalStrategy(List *stmts)
{
	int			nSetTag;
	ListCell   *lc;

// ... (L215-L220 생략: 주석)
	if (list_length(stmts) == 1)
	{
		Node	   *stmt = (Node *) linitial(stmts);

// ... (L225-L246 생략: Query 노드 목록의 같은 판정)
		else if (IsA(stmt, PlannedStmt))
		{
			PlannedStmt *pstmt = (PlannedStmt *) stmt;

			if (pstmt->canSetTag)
			{
				if (pstmt->commandType == CMD_SELECT)
				{
					if (pstmt->hasModifyingCTE)
						return PORTAL_ONE_MOD_WITH;
					else
						return PORTAL_ONE_SELECT;
				}
				if (pstmt->commandType == CMD_UTILITY)
				{
					if (UtilityReturnsTuples(pstmt->utilityStmt))
						return PORTAL_UTIL_SELECT;
					/* it can't be ONE_RETURNING, so give up */
					return PORTAL_MULTI_QUERY;
				}
			}
		}
		else
			elog(ERROR, "unrecognized node type: %d", (int) nodeTag(stmt));
	}

// ... (L273-L277 생략: 주석)
	nSetTag = 0;
	foreach(lc, stmts)
	{
		Node	   *stmt = (Node *) lfirst(lc);

// ... (L283-L295 생략: Query 노드 목록의 같은 판정)
		else if (IsA(stmt, PlannedStmt))
		{
			PlannedStmt *pstmt = (PlannedStmt *) stmt;

			if (pstmt->canSetTag)
			{
				if (++nSetTag > 1)
					return PORTAL_MULTI_QUERY;	/* no need to look further */
				if (pstmt->commandType == CMD_UTILITY ||
					!pstmt->hasReturning)
					return PORTAL_MULTI_QUERY;	/* no need to look further */
			}
		}
		else
			elog(ERROR, "unrecognized node type: %d", (int) nodeTag(stmt));
	}
	if (nSetTag == 1)
		return PORTAL_ONE_RETURNING;

	/* Else, it's the general case... */
	return PORTAL_MULTI_QUERY;
}
```

전략과 상태의 정의, 그리고 포털이 들고 있는 것들이다.

`src` / `include` / `utils` / `portal.h` L89-L160 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/utils/portal.h#L89-L160))

```c
// utils/portal.h L89-L111
typedef enum PortalStrategy
{
	PORTAL_ONE_SELECT,
	PORTAL_ONE_RETURNING,
	PORTAL_ONE_MOD_WITH,
	PORTAL_UTIL_SELECT,
	PORTAL_MULTI_QUERY,
} PortalStrategy;

/*
 * A portal is always in one of these states.  It is possible to transit
 * from ACTIVE back to READY if the query is not run to completion;
 * otherwise we never back up in status.
 */
typedef enum PortalStatus
{
	PORTAL_NEW,					/* freshly created */
	PORTAL_DEFINED,				/* PortalDefineQuery done */
	PORTAL_READY,				/* PortalStart complete, can run it */
	PORTAL_ACTIVE,				/* portal is running (can't delete it) */
	PORTAL_DONE,				/* portal is finished (don't re-run it) */
	PORTAL_FAILED,				/* portal got error (can't re-run it) */
} PortalStatus;
```

```c
// utils/portal.h L115-L160
typedef struct PortalData
{
	/* Bookkeeping data */
	const char *name;			/* portal's name */
	const char *prepStmtName;	/* source prepared statement (NULL if none) */
	MemoryContext portalContext;	/* subsidiary memory for portal */
	ResourceOwner resowner;		/* resources owned by portal */
	void		(*cleanup) (Portal portal); /* cleanup hook */

// ... (L124-L134 생략: 서브트랜잭션 기록)
	/* The query or queries the portal will execute */
	const char *sourceText;		/* text of query (as of 8.4, never NULL) */
	CommandTag	commandTag;		/* command tag for original query */
	QueryCompletion qc;			/* command completion data for executed query */
	List	   *stmts;			/* list of PlannedStmts */
	CachedPlan *cplan;			/* CachedPlan, if stmts are from one */

	ParamListInfo portalParams; /* params to pass to query */
	QueryEnvironment *queryEnv; /* environment for query */

	/* Features/options */
	PortalStrategy strategy;	/* see above */
	int			cursorOptions;	/* DECLARE CURSOR option bits */

	/* Status data */
	PortalStatus status;		/* see above */
	bool		portalPinned;	/* a pinned portal can't be dropped */
	bool		autoHeld;		/* was automatically converted from pinned to
								 * held (see HoldPinnedPortals()) */

	/* If not NULL, Executor is active; call ExecutorEnd eventually: */
	QueryDesc  *queryDesc;		/* info needed for executor invocation */

	/* If portal returns tuples, this is their tupdesc: */
	TupleDesc	tupDesc;		/* descriptor for result tuples */
	/* and these are the format codes to use for the columns: */
```

## 동작 흐름

```text
 L445  Assert(portal->status == PORTAL_DEFINED)      PortalDefineQuery 가 끝난 포털
 L450-L452  ActivePortal, CurrentResourceOwner, PortalContext 를 저장
 L453  PG_TRY
 L455-L460  이 포털의 것으로 바꾼다
 L468    portal->strategy = ChoosePortalStrategy(portal->stmts)
 L473    switch (strategy)
           ONE_SELECT
 L478-L481   스냅샷: 받은 것이 있으면 그것, 없으면 GetTransactionSnapshot   (단순 질의는 없음)
 L496        queryDesc = CreateQueryDesc(PlannedStmt, ..., 활성 스냅샷, None_Receiver, ...)
 L510        스크롤 커서면 EXEC_FLAG_REWIND | EXEC_FLAG_BACKWARD
 L518        ExecutorStart(queryDesc, myeflags)          --> [executor]
 L523        portal->queryDesc = queryDesc
 L528        portal->tupDesc = queryDesc->tupDesc
 L533-L535   atStart = true, atEnd = false, portalPos = 0
 L537        PopActiveSnapshot
           ONE_RETURNING / ONE_MOD_WITH
 L550-L552   tupDesc 만 계획의 대상 목록에서 만든다. 실행기는 아직
           UTIL_SELECT
 L573        tupDesc = UtilityTupleDescriptor (SHOW, EXPLAIN 등의 결과 모양)
           MULTI_QUERY
 L586        tupDesc = NULL (돌려줄 행이 없다)
 L590  PG_CATCH -> MarkPortalFailed, 전역 변수 복원, 다시 던지기
 L606-L608  전역 변수 복원
 L610  portal->status = PORTAL_READY
```

전략은 `PlannedStmt` 목록의 모양만 보고 정해진다. 판정 순서대로 그리면 이렇다.

```text
 ChoosePortalStrategy (pquery.c L210, PlannedStmt 목록 기준)

 목록 길이 1 이고 canSetTag 인가                                    L221-L251
   +-- CMD_SELECT
   |     +-- hasModifyingCTE  -> PORTAL_ONE_MOD_WITH              L255-L256
   |     +-- 아니면           -> PORTAL_ONE_SELECT                 L258
   +-- CMD_UTILITY
         +-- 결과 행을 돌려주는 유틸리티 -> PORTAL_UTIL_SELECT     L262-L263
         +-- 아니면                      -> PORTAL_MULTI_QUERY     L265
 아니면 canSetTag 인 것을 센다                                       L278-L311
   +-- 정확히 하나이고 RETURNING 이 있음 -> PORTAL_ONE_RETURNING   L312-L313
   +-- 그 밖                             -> PORTAL_MULTI_QUERY     L316

 예
   SELECT * FROM t                       ONE_SELECT
   WITH d AS (DELETE ... RETURNING *) SELECT * FROM d    ONE_MOD_WITH
   INSERT ... RETURNING id               ONE_RETURNING  (길이 1 이지만 SELECT 가 아니라 아래 판정으로)
   INSERT INTO t VALUES (1)              MULTI_QUERY
   SHOW work_mem                         UTIL_SELECT
   CREATE TABLE t (...)                  MULTI_QUERY
```

```text
 포털 상태 (portal.h L103-L111)

 PORTAL_NEW -----> PORTAL_DEFINED -----> PORTAL_READY <----> PORTAL_ACTIVE -----> PORTAL_DONE
   CreatePortal      PortalDefineQuery    PortalStart          PortalRun 중
                     (postgres.c L1225)   (이 함수 L610)        (pquery.c L716)

 어느 상태에서든 오류면 PORTAL_FAILED (L593 MarkPortalFailed)
 ACTIVE 에서 READY 로 돌아오는 것은 끝까지 실행하지 않았을 때다 (커서의 FETCH 등)
```

## 결과가 쓰이는 곳

```text
 portal->strategy
      --> [10] PortalRun 의 switch 가 이 값으로 갈래를 고른다

 portal->queryDesc (ONE_SELECT 만)
      --> [10] PortalRunSelect 가 ExecutorRun 에 넘긴다
      --> 포털을 지울 때 PortalCleanup 이 ExecutorEnd 를 부르는 근거 (L520-L521 주석)

 portal->tupDesc
      --> PortalSetResultFormat (postgres.c L1257) 과 RowDescription 의 열 정보
```

## 다루지 않는 것

`CreateQueryDesc` 의 필드, `ExecutorStart` 의 내부([executor](../../executor/README.md)), 포털의 자원 소유자와 메모리 컨텍스트 관리(`portalmem.c`), 커서용 `holdStore` 와 `PortalSetResultFormat` 의 형식 코드는 곁가지라 요약만 했다.
