# pg_analyze_and_rewrite_fixedparams

상위: [쿼리 실행 파이프라인](../README.md)

분석([04])과 재작성([05])을 **한 번에 잇는** 얇은 함수다. 입력은 `RawStmt` 하나, 출력은 `Query` 의 **목록**이다. 목록인 이유를 주석(L660-L661)은 "분석기나 재작성기가 질의 하나를 여럿으로 늘릴 수 있어서"라고 적는다. 다만 이 함수에서 분석([04])은 `Query` 하나를 돌려주므로, 실제로 개수가 바뀌는 자리는 규칙 재작성이다(0 개가 될 수도 있다). 이름의 `fixedparams` 는 `$n` 매개변수 타입이 미리 정해져 있다는 뜻이고, 단순 질의에서는 매개변수가 없으므로 `NULL, 0` 으로 불린다.

## 위치

`tcop` / `postgres.c` L666-L697 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L666-L697))

## 실제 코드

`tcop` / `postgres.c` L666-L697 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L666-L697))

```c
// tcop/postgres.c L666-L697
pg_analyze_and_rewrite_fixedparams(RawStmt *parsetree,
								   const char *query_string,
								   const Oid *paramTypes,
								   int numParams,
								   QueryEnvironment *queryEnv)
{
	Query	   *query;
	List	   *querytree_list;

	TRACE_POSTGRESQL_QUERY_REWRITE_START(query_string);

	/*
	 * (1) Perform parse analysis.
	 */
	if (log_parser_stats)
		ResetUsage();

	query = parse_analyze_fixedparams(parsetree, query_string, paramTypes, numParams,
									  queryEnv);

	if (log_parser_stats)
		ShowUsage("PARSE ANALYSIS STATISTICS");

	/*
	 * (2) Rewrite the queries, as necessary
	 */
	querytree_list = pg_rewrite_query(query);

	TRACE_POSTGRESQL_QUERY_REWRITE_DONE(query_string);

	return querytree_list;
}
```

같은 일을 하는 형제 함수가 둘 더 있다. 매개변수 타입을 다루는 방식만 다르다.

`tcop` / `postgres.c` L704-L750 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L704-L750))

```c
// tcop/postgres.c L704-L750
List *
pg_analyze_and_rewrite_varparams(RawStmt *parsetree,
								 const char *query_string,
								 Oid **paramTypes,
								 int *numParams,
								 QueryEnvironment *queryEnv)
{
	Query	   *query;
	List	   *querytree_list;

	TRACE_POSTGRESQL_QUERY_REWRITE_START(query_string);

	/*
	 * (1) Perform parse analysis.
	 */
	if (log_parser_stats)
		ResetUsage();

	query = parse_analyze_varparams(parsetree, query_string, paramTypes, numParams,
									queryEnv);

	/*
	 * Check all parameter types got determined.
	 */
	for (int i = 0; i < *numParams; i++)
	{
		Oid			ptype = (*paramTypes)[i];

		if (ptype == InvalidOid || ptype == UNKNOWNOID)
			ereport(ERROR,
					(errcode(ERRCODE_INDETERMINATE_DATATYPE),
					 errmsg("could not determine data type of parameter $%d",
							i + 1)));
	}

// ... (L739-L749 생략: 통계와 재작성은 fixedparams 와 같다)
}
```

## 동작 흐름

```text
 L675  TRACE QUERY_REWRITE_START
 L680  log_parser_stats 면 ResetUsage
 L683  query = [04] parse_analyze_fixedparams(parsetree, query_string, paramTypes, numParams, queryEnv)
         단순 질의: paramTypes = NULL, numParams = 0  (호출부 postgres.c L1190-L1191)
 L686  "PARSE ANALYSIS STATISTICS"
 L692  querytree_list = [05] pg_rewrite_query(query)
 L694  TRACE QUERY_REWRITE_DONE
 L696  return querytree_list
```

세 형제 함수는 분석 단계에서 `$n` 을 어떻게 다루는지만 다르고, 재작성은 똑같이 `pg_rewrite_query` 다.

```text
 분석 + 재작성 진입점 셋 (postgres.c)

 entry                                 analyze                     쓰는 곳
 pg_analyze_and_rewrite_fixedparams   parse_analyze_fixedparams   L666  단순 질의 (이 흐름)
 pg_analyze_and_rewrite_varparams     parse_analyze_varparams     L705  Parse 메시지 (L1520)
 pg_analyze_and_rewrite_withcb        parse_analyze_withcb        L759  SPI, SQL 함수, plancache

 varparams 는 분석 뒤 $n 타입이 하나라도 정해지지 않으면 ERROR (L728-L737)
   "could not determine data type of parameter $%d"
```

```text
 개수 변화

 RawStmt 1 개
   --> [04] 분석       Query 1 개              항상 1:1
   --> [05] 재작성     Query 0 개, 1 개, 여러 개
                       QueryRewrite 주석: "possibly returning 0 or many queries"
                       (rewrite/rewriteHandler.c L4628-L4629, 05 문서)
```

## 결과가 쓰이는 곳

```text
 List of Query
      --> [01] 이 pg_plan_queries 에 그대로 넘긴다 (postgres.c L1193)
      --> 원소마다 PlannedStmt 하나가 된다
```

## 다루지 않는 것

`TRACE_POSTGRESQL_*` 정적 추적점, `log_parser_stats` 의 자원 사용 보고(`ShowUsage`), `QueryEnvironment`(트리거의 전이 테이블 등)는 곁가지라 요약만 했다.
