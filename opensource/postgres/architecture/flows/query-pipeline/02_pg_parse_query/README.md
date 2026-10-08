# pg_parse_query

상위: [쿼리 실행 파이프라인](../README.md)

문자열을 **문법만 보고** `RawStmt` 목록으로 바꾸는 단계다. 카탈로그를 전혀 읽지 않는다. 그래서 실패한 트랜잭션 안에서도 돌 수 있고, [01] 은 이 결과만 보고 `COMMIT` / `ROLLBACK` 인지 가려 그 밖의 문장을 거절한다(L596-L601 주석). 본체는 flex 어휘 분석기와 bison 문법을 묶은 `raw_parser` 다.

## 위치

`tcop` / `postgres.c` L604-L654 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L604-L654))

## 실제 코드

`tcop` / `postgres.c` L604-L654 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/postgres.c#L604-L654))

```c
// tcop/postgres.c L604-L654
pg_parse_query(const char *query_string)
{
	List	   *raw_parsetree_list;

	TRACE_POSTGRESQL_QUERY_PARSE_START(query_string);

	if (log_parser_stats)
		ResetUsage();

	raw_parsetree_list = raw_parser(query_string, RAW_PARSE_DEFAULT);

	if (log_parser_stats)
		ShowUsage("PARSER STATISTICS");

// ... (L618-L649 생략: 디버그 빌드의 copyObject 및 직렬화 왕복 점검)

	TRACE_POSTGRESQL_QUERY_PARSE_DONE(query_string);

	return raw_parsetree_list;
}
```

어휘 분석기와 문법 분석기를 묶는 쪽이다.

`parser` / `parser.c` L42-L86 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/parser/parser.c#L42-L86))

```c
// parser/parser.c L42-L86
raw_parser(const char *str, RawParseMode mode)
{
	core_yyscan_t yyscanner;
	base_yy_extra_type yyextra;
	int			yyresult;

	/* initialize the flex scanner */
	yyscanner = scanner_init(str, &yyextra.core_yy_extra,
							 &ScanKeywords, ScanKeywordTokens);

	/* base_yylex() only needs us to initialize the lookahead token, if any */
	if (mode == RAW_PARSE_DEFAULT)
		yyextra.have_lookahead = false;
// ... (L55-L71 생략: PL/pgSQL 용 다른 모드의 첫 토큰)

	/* initialize the bison parser */
	parser_init(&yyextra);

	/* Parse! */
	yyresult = base_yyparse(yyscanner);

	/* Clean up (release memory) */
	scanner_finish(yyscanner);

	if (yyresult)				/* error */
		return NIL;

	return yyextra.parsetree;
}
```

결과 목록의 원소다. 문장 하나의 원시 파스 트리와 원문에서의 위치만 담는다.

`src` / `include` / `nodes` / `parsenodes.h` L2081-L2089 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/nodes/parsenodes.h#L2081-L2089))

```c
// nodes/parsenodes.h L2081-L2089
typedef struct RawStmt
{
	pg_node_attr(no_query_jumble)

	NodeTag		type;
	Node	   *stmt;			/* raw parse tree */
	ParseLoc	stmt_location;	/* start location, or -1 if unknown */
	ParseLoc	stmt_len;		/* length in bytes; 0 means "rest of string" */
} RawStmt;
```

## 동작 흐름

```text
 pg_parse_query (postgres.c)
 L608   TRACE QUERY_PARSE_START
 L610   log_parser_stats 면 ResetUsage
 L613   raw_parsetree_list = raw_parser(query_string, RAW_PARSE_DEFAULT)
 L618-L649  디버그 빌드 옵션이면 트리를 복사, 직렬화 왕복해서 같은지 확인
 L653   return raw_parsetree_list

 raw_parser (parser.c)
 L49    scanner_init                 flex 스캐너, 키워드 표 ScanKeywords
 L53    RAW_PARSE_DEFAULT 면 미리 볼 토큰 없음
 L74    parser_init
 L77    base_yyparse                 bison 이 문법 규칙의 동작으로 노드를 만든다
 L80    scanner_finish
 L82    yyresult 가 0 이 아니면 NIL
          (문법 오류 보고는 base_yyerror -> parser_yyerror 몫, gram.y L18692-L18695)
 L85    yyextra.parsetree             List of RawStmt
```

문자열 안의 세미콜론마다 `RawStmt` 가 하나씩 생기고, 각자 원문에서의 시작 위치와 길이를 갖는다.

```text
 "SELECT 1; INSERT INTO t VALUES (2)" 를 파싱한 결과

 List (길이 2)
 +-- RawStmt
 |     stmt           SelectStmt
 |                      targetList [ ResTarget( A_Const 1 ) ]
 |     stmt_location  0
 |     stmt_len       8        "SELECT 1"
 +-- RawStmt
       stmt           InsertStmt
                        relation   RangeVar "t"
                        selectStmt SelectStmt( valuesLists [[ A_Const 2 ]] )
       stmt_location  10       "INSERT ..." 첫 토큰의 위치 @3 (공백 다음)
       stmt_len       0        0 은 "문자열 끝까지" (parsenodes.h L2088)

 길이는 gram.y 가 정한다 (L961-L979)
   makeRawStmt 는 stmt_len = 0 으로 만들고 (L18704)
   다음 ';' 를 만나면 updateRawStmtEnd 가 ';' 위치 - 시작 위치 = 8 - 0 = 8 로 고친다 (L18721)
   마지막 문장은 ';' 가 없으니 0 으로 남는다

 이름은 아직 문자열이다. "t" 가 어떤 테이블인지, 1 이 무슨 타입인지 모른다
 그 일은 [04] parse_analyze 가 카탈로그를 보며 한다
```

```text
 파싱이 카탈로그와 분리된 이유 (L596-L601 주석)

 실패한 트랜잭션 블록 안 (TBLOCK_ABORT)
   분석, 재작성, 계획은 테이블을 읽어야 해서 여기서 돌 수 없다
   파싱은 읽지 않으므로 돈다
     -> [01] L1134 IsTransactionExitStmt(parsetree->stmt) 로 COMMIT / ROLLBACK 만 통과
     -> 나머지는 ERROR "current transaction is aborted ..."
```

## 결과가 쓰이는 곳

```text
 List of RawStmt
      --> [01] 이 원소마다 루프를 돈다 (postgres.c L1095)
      --> CreateCommandTag(parsetree->stmt) 가 "SELECT", "INSERT" 같은 완료 태그를 정한다 (L1119)
      --> [04] transformTopLevelStmt 가 stmt_location / stmt_len 을 Query 에 옮긴다 (analyze.c L256-L257)
      --> 목록 길이 > 1 이면 암묵 트랜잭션 블록 (postgres.c L1090)
```

## 다루지 않는 것

`gram.y` 문법 규칙과 노드를 만드는 동작들, `scan.l` 어휘 분석, `base_yylex` 의 한 토큰 미리 보기 치환(`NOT_LA`, `WITH_LA` 등), 오류 위치 보고(`scanner_errposition`), PL/pgSQL 용 파싱 모드는 곁가지라 요약만 했다.
