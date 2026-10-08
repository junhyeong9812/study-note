# parse_analyze_fixedparams

상위: [쿼리 실행 파이프라인](../README.md)

`RawStmt` 를 `Query` 로 바꾸는 **의미 분석의 입구**다. 여기서 처음으로 카탈로그를 읽는다. 테이블 이름은 OID 를 가진 range table 항목이 되고, 열 이름은 `Var` 가 되고, `=` 같은 연산자는 타입에 맞는 함수로 정해진다. SELECT, INSERT, UPDATE, DELETE, MERGE 같은 **최적화 대상 문장만 실제로 변환**하고, DDL 같은 나머지는 원래 트리를 `CMD_UTILITY` `Query` 에 매달기만 한다(L100-L102 주석).

## 위치

`parser` / `analyze.c` L105-L135 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/parser/analyze.c#L105-L135))

## 실제 코드

`parser` / `analyze.c` L105-L135 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/parser/analyze.c#L105-L135))

```c
// parser/analyze.c L105-L135
parse_analyze_fixedparams(RawStmt *parseTree, const char *sourceText,
						  const Oid *paramTypes, int numParams,
						  QueryEnvironment *queryEnv)
{
	ParseState *pstate = make_parsestate(NULL);
	Query	   *query;
	JumbleState *jstate = NULL;

	Assert(sourceText != NULL); /* required as of 8.4 */

	pstate->p_sourcetext = sourceText;

	if (numParams > 0)
		setup_parse_fixed_parameters(pstate, paramTypes, numParams);

	pstate->p_queryEnv = queryEnv;

	query = transformTopLevelStmt(pstate, parseTree);

	if (IsQueryIdEnabled())
		jstate = JumbleQuery(query);

	if (post_parse_analyze_hook)
		(*post_parse_analyze_hook) (pstate, query, jstate);

	free_parsestate(pstate);

	pgstat_report_query_id(query->queryId, false);

	return query;
}
```

최상위 문장만 할 수 있는 일(위치 정보 옮기기, `SELECT INTO` 바꾸기)을 하고 재귀 변환으로 들어간다.

`parser` / `analyze.c` L249-L305 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/parser/analyze.c#L249-L305))

```c
// parser/analyze.c L249-L305
transformTopLevelStmt(ParseState *pstate, RawStmt *parseTree)
{
	Query	   *result;

	/* We're at top level, so allow SELECT INTO */
	result = transformOptionalSelectInto(pstate, parseTree->stmt);

	result->stmt_location = parseTree->stmt_location;
	result->stmt_len = parseTree->stmt_len;

	return result;
}

/*
 * transformOptionalSelectInto -
 *	  If SELECT has INTO, convert it to CREATE TABLE AS.
 *
 * The only thing we do here that we don't do in transformStmt() is to
 * convert SELECT ... INTO into CREATE TABLE AS.  Since utility statements
 * aren't allowed within larger statements, this is only allowed at the top
 * of the parse tree, and so we only try it before entering the recursive
 * transformStmt() processing.
 */
static Query *
transformOptionalSelectInto(ParseState *pstate, Node *parseTree)
{
	if (IsA(parseTree, SelectStmt))
	{
		SelectStmt *stmt = (SelectStmt *) parseTree;

		/* If it's a set-operation tree, drill down to leftmost SelectStmt */
		while (stmt && stmt->op != SETOP_NONE)
			stmt = stmt->larg;
		Assert(stmt && IsA(stmt, SelectStmt) && stmt->larg == NULL);

		if (stmt->intoClause)
		{
// ... (L286-L299 생략: CreateTableAsStmt 조립)
			parseTree = (Node *) ctas;
		}
	}

	return transformStmt(pstate, parseTree);
}
```

문장 종류로 갈라 각자의 `transform*` 을 부른다.

`parser` / `analyze.c` L312-L429 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/parser/analyze.c#L312-L429))

```c
// parser/analyze.c L312-L429
transformStmt(ParseState *pstate, Node *parseTree)
{
	Query	   *result;

// ... (L316-L345 생략: 디버그 빌드 점검과 주석)
	switch (nodeTag(parseTree))
	{
			/*
			 * Optimizable statements
			 */
		case T_InsertStmt:
			result = transformInsertStmt(pstate, (InsertStmt *) parseTree);
			break;

		case T_DeleteStmt:
			result = transformDeleteStmt(pstate, (DeleteStmt *) parseTree);
			break;

		case T_UpdateStmt:
			result = transformUpdateStmt(pstate, (UpdateStmt *) parseTree);
			break;

		case T_MergeStmt:
			result = transformMergeStmt(pstate, (MergeStmt *) parseTree);
			break;

		case T_SelectStmt:
			{
				SelectStmt *n = (SelectStmt *) parseTree;

				if (n->valuesLists)
					result = transformValuesClause(pstate, n);
				else if (n->op == SETOP_NONE)
					result = transformSelectStmt(pstate, n);
				else
					result = transformSetOperationStmt(pstate, n);
			}
			break;

// ... (L380-L411 생략: RETURN, PL/pgSQL 대입, DECLARE CURSOR, EXPLAIN, CREATE TABLE AS, CALL)
		default:

			/*
			 * other statements don't require any transformation; just return
			 * the original parsetree with a Query node plastered on top.
			 */
			result = makeNode(Query);
			result->commandType = CMD_UTILITY;
			result->utilityStmt = (Node *) parseTree;
			break;
	}

	/* Mark as original query until we learn differently */
	result->querySource = QSRC_ORIGINAL;
	result->canSetTag = true;

	return result;
}
```

가장 흔한 SELECT 의 변환이다. 절마다 하나씩 바꿔 `Query` 필드에 채운다.

`parser` / `analyze.c` L1389-L1522 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/parser/analyze.c#L1389-L1522))

```c
// parser/analyze.c L1389-L1522
transformSelectStmt(ParseState *pstate, SelectStmt *stmt)
{
	Query	   *qry = makeNode(Query);
	Node	   *qual;
	ListCell   *l;

	qry->commandType = CMD_SELECT;

// ... (L1397-L1417 생략: WITH, INTO 검사, 잠금과 WINDOW 준비)

	/* process the FROM clause */
	transformFromClause(pstate, stmt->fromClause);

	/* transform targetlist */
	qry->targetList = transformTargetList(pstate, stmt->targetList,
										  EXPR_KIND_SELECT_TARGET);

	/* mark column origins */
	markTargetListOrigins(pstate, qry->targetList);

	/* transform WHERE */
	qual = transformWhereClause(pstate, stmt->whereClause,
								EXPR_KIND_WHERE, "WHERE");

	/* initial processing of HAVING clause is much like WHERE clause */
	qry->havingQual = transformWhereClause(pstate, stmt->havingClause,
										   EXPR_KIND_HAVING, "HAVING");

// ... (L1437-L1495 생략: 정렬, 그룹, DISTINCT, LIMIT, WINDOW 변환)
	/* resolve any still-unresolved output columns as being type text */
	if (pstate->p_resolve_unknowns)
		resolveTargetListUnknowns(pstate, qry->targetList);

	qry->rtable = pstate->p_rtable;
	qry->rteperminfos = pstate->p_rteperminfos;
	qry->jointree = makeFromExpr(pstate->p_joinlist, qual);

	qry->hasSubLinks = pstate->p_hasSubLinks;
	qry->hasWindowFuncs = pstate->p_hasWindowFuncs;
	qry->hasTargetSRFs = pstate->p_hasTargetSRFs;
	qry->hasAggs = pstate->p_hasAggs;

// ... (L1509-L1513 생략: FOR UPDATE 처리)

	assign_query_collations(pstate, qry);

	/* this must be done after collations, for reliable comparison of exprs */
	if (pstate->p_hasAggs || qry->groupClause || qry->groupingSets || qry->havingQual)
		parseCheckAggregates(pstate, qry);

	return qry;
}
```

결과 구조체의 주요 필드다.

`src` / `include` / `nodes` / `parsenodes.h` L117-L257 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/nodes/parsenodes.h#L117-L257))

```c
// nodes/parsenodes.h L117-L141
typedef struct Query
{
	NodeTag		type;

	CmdType		commandType;	/* select|insert|update|delete|merge|utility */

	/* where did I come from? */
	QuerySource querySource pg_node_attr(query_jumble_ignore);

// ... (L126-L135 생략: queryId 주석)
	int64		queryId pg_node_attr(equal_ignore, query_jumble_ignore, read_write_ignore, read_as(0));

	/* do I set the command result tag? */
	bool		canSetTag pg_node_attr(query_jumble_ignore);

	Node	   *utilityStmt;	/* non-null if commandType == CMD_UTILITY */
```

```c
// nodes/parsenodes.h L173-L183
	List	   *cteList;		/* WITH list (of CommonTableExpr's) */

	List	   *rtable;			/* list of range table entries */

// ... (L177-L180 생략: 주석)
	List	   *rteperminfos pg_node_attr(query_jumble_ignore);
	FromExpr   *jointree;		/* table join tree (FROM and WHERE clauses);
								 * also USING clause for MERGE */
```

```c
// nodes/parsenodes.h L198-L198
	List	   *targetList;		/* target list (of TargetEntry) */
```

## 동작 흐름

```text
 parse_analyze_fixedparams
 L109  pstate = make_parsestate(NULL)        분석 내내 들고 다니는 상태 (range table, 이름 공간 ...)
 L115  p_sourcetext = 원문                    오류 위치 표시용
 L117  매개변수가 있으면 setup_parse_fixed_parameters
 L122  query = transformTopLevelStmt(pstate, parseTree)
 L124  compute_query_id 가 켜져 있으면 JumbleQuery -> queryId
 L127  post_parse_analyze_hook               pg_stat_statements 가 여기 걸린다 (contrib, L475)
 L130  free_parsestate
 L132  pgstat_report_query_id

 transformTopLevelStmt (L249)
 L254  transformOptionalSelectInto
         SELECT ... INTO 면 CreateTableAsStmt 로 바꾼다 (L284-L301)
         -> transformStmt
 L256  result->stmt_location, stmt_len = RawStmt 의 값

 transformStmt (L312)
 L346  switch (nodeTag(parseTree))
         InsertStmt / DeleteStmt / UpdateStmt / MergeStmt   transform*Stmt
         SelectStmt     VALUES 만 있으면 transformValuesClause
                        집합 연산 없으면 transformSelectStmt
                        UNION 등이면 transformSetOperationStmt
         Return / PLAssign / DeclareCursor / Explain / CreateTableAs / Call
                        각자 전용 transform 함수 (L380-L410)
         그 밖 (default) makeNode(Query), CMD_UTILITY, utilityStmt = 원래 트리  (L418-L420)
 L425  querySource = QSRC_ORIGINAL,  L426 canSetTag = true
```

SELECT 하나의 절이 `Query` 의 어느 필드로 가는지 나란히 놓으면 이렇다. 원시 트리의 절 이름과 `Query` 의 필드 이름이 대부분 그대로 대응한다.

```text
 transformSelectStmt 의 절별 대응 (analyze.c)

 SelectStmt         line   transform                   Query field
 withClause         L1401  transformWithClause         cteList
 fromClause         L1420  transformFromClause         rtable, (p_joinlist)
 targetList         L1423  transformTargetList         targetList
 whereClause        L1430  transformWhereClause        (qual)
 havingClause       L1434  transformWhereClause        havingQual
 sortClause         L1443  transformSortClause         sortClause
 groupClause        L1449  transformGroupClause        groupClause
 distinctClause     L1466  transformDistinctClause     distinctClause
 limitOffset/Count  L1483  transformLimitClause        limitOffset, limitCount
 windowClause       L1492  transformWindowDefinitions  windowClause
 (FROM + WHERE)     L1502  makeFromExpr                jointree = FromExpr(p_joinlist, qual)
 lockingClause      L1511  transformLockingClause      rowMarks

 마지막에 L1515 assign_query_collations, 집계가 있으면 L1519 parseCheckAggregates
```

```text
 SELECT name FROM users WHERE id = 1 의 전과 후 (users.id 는 int4 라고 가정)

 RawStmt.stmt (SelectStmt)                 Query
 fromClause   RangeVar "users"     --->    rtable[1]  RangeTblEntry RTE_RELATION
                                             relid = pg_class 에서 찾은 users 의 OID
                                           jointree   FromExpr
                                             fromlist [ RangeTblRef 1 ]
 whereClause  A_Expr "="            --->     quals    OpExpr
                ColumnRef "id"                           Var(varno 1, varattno = id 의 열 번호)
                A_Const 1                                Const(int4, 1)
 targetList   ResTarget            --->    targetList [ TargetEntry Var(1, name 의 열 번호) ]
                ColumnRef "name"
                                           commandType CMD_SELECT, canSetTag true

 "users" 가 없으면 여기서 ERROR "relation ... does not exist" (parser/parse_relation.c L1498-L1501)
   파싱 단계가 아니라 분석 단계의 오류다
```

## 결과가 쓰이는 곳

```text
 Query
      --> [05] pg_rewrite_query 가 뷰와 규칙을 적용한다
      --> queryId 가 pg_stat_statements 와 pg_stat_activity 의 query_id 가 된다

 CMD_UTILITY Query
      --> 재작성과 계획을 건너뛰고 PlannedStmt.utilityStmt 로 실려 ProcessUtility 로 간다
          (postgres.c L810-L814, L982-L992)
```

## 다루지 않는 것

각 절의 변환 함수 내부(`transformFromClause` 의 range table 구성, 이름 해석 `colNameToVar`, 연산자 고르기 `make_op`, 타입 강제 변환), `transformInsertStmt` / `transformUpdateStmt` 등 다른 문장의 변환, `JumbleQuery` 의 queryId 계산, 집합 연산과 CTE 의 변환은 이 흐름의 곁가지라 요약만 했다.
