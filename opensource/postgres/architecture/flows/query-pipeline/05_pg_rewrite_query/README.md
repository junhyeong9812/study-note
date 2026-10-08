# pg_rewrite_query

상위: [쿼리 실행 파이프라인](../README.md)

분석이 끝난 `Query` 하나에 **규칙 시스템을 적용해 `Query` 목록을 돌려주는** 단계다. 유틸리티 문장은 손대지 않고 한 칸짜리 목록에 담기만 하고, 나머지는 `QueryRewrite` 로 보낸다. `QueryRewrite` 는 세 단계다. INSERT/UPDATE/DELETE 규칙을 적용하고(질의 수가 바뀔 수 있다), 각 결과에 SELECT 규칙(RIR, 뷰 펼치기)을 적용하고, 완료 태그를 정할 질의 하나를 고른다.

## 위치

`tcop` / `postgres.c` L799-L875 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L799-L875))

## 실제 코드

`tcop` / `postgres.c` L799-L875 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L799-L875))

```c
// tcop/postgres.c L799-L875
pg_rewrite_query(Query *query)
{
	List	   *querytree_list;

	if (Debug_print_parse)
		elog_node_display(LOG, "parse tree", query,
						  Debug_pretty_print);

	if (log_parser_stats)
		ResetUsage();

	if (query->commandType == CMD_UTILITY)
	{
		/* don't rewrite utilities, just dump 'em into result list */
		querytree_list = list_make1(query);
	}
	else
	{
		/* rewrite regular queries */
		querytree_list = QueryRewrite(query);
	}

	if (log_parser_stats)
		ShowUsage("REWRITER STATISTICS");

// ... (L824-L868 생략: 디버그 빌드의 복사와 직렬화 왕복 점검)

	if (Debug_print_rewritten)
		elog_node_display(LOG, "rewritten parse tree", querytree_list,
						  Debug_pretty_print);

	return querytree_list;
}
```

규칙 시스템의 입구다. 세 단계가 주석으로 나뉘어 있다.

`rewrite` / `rewriteHandler.c` L4635-L4724 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/rewrite/rewriteHandler.c#L4635-L4724))

```c
// rewrite/rewriteHandler.c L4635-L4724
QueryRewrite(Query *parsetree)
{
	int64		input_query_id = parsetree->queryId;
	List	   *querylist;
	List	   *results;
	ListCell   *l;
	CmdType		origCmdType;
	bool		foundOriginalQuery;
	Query	   *lastInstead;

	/*
	 * This function is only applied to top-level original queries
	 */
	Assert(parsetree->querySource == QSRC_ORIGINAL);
	Assert(parsetree->canSetTag);

	/*
	 * Step 1
	 *
	 * Apply all non-SELECT rules possibly getting 0 or many queries
	 */
	querylist = RewriteQuery(parsetree, NIL, 0, 0);

	/*
	 * Step 2
	 *
	 * Apply all the RIR rules on each query
	 *
	 * This is also a handy place to mark each query with the original queryId
	 */
	results = NIL;
	foreach(l, querylist)
	{
		Query	   *query = (Query *) lfirst(l);

		query = fireRIRrules(query, NIL);

		query->queryId = input_query_id;

		results = lappend(results, query);
	}

// ... (L4677-L4692 생략: 주석)
	origCmdType = parsetree->commandType;
	foundOriginalQuery = false;
	lastInstead = NULL;

	foreach(l, results)
	{
		Query	   *query = (Query *) lfirst(l);

		if (query->querySource == QSRC_ORIGINAL)
		{
			Assert(query->canSetTag);
			Assert(!foundOriginalQuery);
			foundOriginalQuery = true;
#ifndef USE_ASSERT_CHECKING
			break;
#endif
		}
		else
		{
			Assert(!query->canSetTag);
			if (query->commandType == origCmdType &&
				(query->querySource == QSRC_INSTEAD_RULE ||
				 query->querySource == QSRC_QUAL_INSTEAD_RULE))
				lastInstead = query;
		}
	}

	if (!foundOriginalQuery && lastInstead != NULL)
		lastInstead->canSetTag = true;

	return results;
}
```

## 동작 흐름

```text
 pg_rewrite_query (postgres.c)
 L803  debug_print_parse 면 분석 결과 트리를 로그에
 L810  commandType == CMD_UTILITY
 L813    list_make1(query)                  재작성하지 않는다
 L818  아니면 QueryRewrite(query)
 L870  debug_print_rewritten 면 재작성 결과를 로그에

 QueryRewrite (rewriteHandler.c)
 L4637  input_query_id = parsetree->queryId
 L4648  Assert(QSRC_ORIGINAL, canSetTag)
 L4656  Step 1  querylist = RewriteQuery(parsetree, NIL, 0, 0)
                  INSERT / UPDATE / DELETE 규칙. 0 개 또는 여러 개
 L4666  Step 2  foreach: fireRIRrules(query, NIL)
                  SELECT 규칙 (뷰 펼치기), 그리고 L4672 queryId 를 원래 값으로
 L4693  Step 3  canSetTag 를 누가 가질지
                  원래 질의(QSRC_ORIGINAL)가 남아 있으면 그것
                  없으면 원래와 같은 종류의 마지막 INSTEAD 질의 (L4720-L4721)
 L4723  return results
```

규칙이 없는 보통 테이블이면 목록은 한 칸이고 내용도 거의 그대로다. 뷰를 읽으면 Step 2 에서 range table 의 뷰 항목이 뷰 정의 질의로 바뀐다.

```text
 개수와 canSetTag (QueryRewrite 의 Step 1 과 Step 3)

 Step 1 result                 canSetTag 를 갖는 것                 경우
 [ orig ]                      orig                                 규칙 없는 테이블
 [ orig, rule ... ]            orig (L4701-L4705)                   원래 질의가 남고 규칙 질의가 붙음
 [ rule ... ]                  같은 종류의 마지막 INSTEAD 질의      INSTEAD 규칙이 원래를 대체
 [ ]                           없음                                 아무 질의도 남지 않음

 orig = 원래 질의 (QSRC_ORIGINAL), rule = 규칙이 만든 질의

 canSetTag 가 없으면 tcop 가 원래 질의의 기본 태그를 쓴다 (주석 L4684-L4687)
 결과 목록의 원소마다 PlannedStmt 하나가 되고, 원소가 둘 이상이면 [09] ChoosePortalStrategy 는
 RETURNING 이 있는 경우(PORTAL_ONE_RETURNING)가 아니면 PORTAL_MULTI_QUERY 를 고른다
```

```text
 뷰 하나를 읽을 때 Step 2 가 바꾸는 것

 분석 직후  Query
              rtable[1] = RangeTblEntry(RTE_RELATION, relid = 뷰의 OID, relkind 'v')
                 |
                 |  fireRIRrules -> ApplyRetrieveRule (rewriteHandler.c L2174, L1746)
                 v
 재작성 뒤  Query
              rtable[1] = RangeTblEntry(RTE_SUBQUERY, subquery = 뷰 정의의 Query)   L1883

 플래너의 subquery_planner 가 pull_up_subqueries 로 이 서브쿼리를 위로 끌어올릴 수 있다
   (optimizer/plan/planner.c L774)
```

## 결과가 쓰이는 곳

```text
 List of Query
      --> [01] pg_plan_queries 가 원소마다 [06] 을 부른다 (postgres.c L977-L1000)

 canSetTag
      --> 그 질의의 결과만 CommandComplete 태그와 행 수가 된다
      --> 나머지 질의의 출력은 altdest 로 간다 ([10] PortalRunMulti)

 queryId
      --> 재작성으로 생긴 질의들도 원래 질의의 queryId 를 그대로 가진다 (L4672)
```

## 다루지 않는 것

`RewriteQuery` 의 규칙 적용 세부(`fireRules`, `rewriteRuleAction`, 갱신 가능 뷰의 자동 재작성), `fireRIRrules` 의 뷰 펼치기 세부와 행 보안 정책(RLS) 적용, `AcquireRewriteLocks`, 규칙 정의(`CREATE RULE`) 저장 형식은 이 흐름의 곁가지라 요약만 했다.
