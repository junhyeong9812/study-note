# 쿼리 실행 파이프라인

상위: [PostgreSQL 아키텍처 지도](../../README.md)

`'Q'` 메시지로 온 SQL 문자열 하나가 **파스 트리, 질의 트리, 계획, 포털로 차례로 모양을 바꿔 실행되기까지**의 흐름이다. 단계마다 자료구조가 하나씩 정해져 있다. 문법만 본 `RawStmt`, 카탈로그로 이름을 풀어 의미를 붙인 `Query`, 규칙으로 고쳐 쓴 `Query` 목록, 실행 방법을 고른 `PlannedStmt`, 그리고 그 계획을 들고 실행 상태를 쥐는 `Portal` 이다. 이 흐름은 한 backend 안에서 일어나고 프로세스 경계가 없다. 대신 **트랜잭션 경계**가 있다. 문자열 전체를 `start_xact_command` 와 `finish_xact_command` 가 감싸고, 문장이 여럿이면 암묵적 트랜잭션 블록으로 묶는다. 흐름은 [10] `PortalRun` 이 `ExecutorRun` 을 부르는 데서 [executor](../executor/README.md)로 넘어가고, `finish_xact_command` 의 `CommitTransactionCommand` 에서 [커밋](../commit/README.md)으로 이어진다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 PostgresMain 'Q'  (postgres.c L4770)  --> 연결과 backend 기동 흐름에서 넘어온다
 ------------------------------------------------------------------
 [01] exec_simple_query                         postgres.c L1012
      +-- start_xact_command                    L1046  트랜잭션 명령 시작
      +-- [02] pg_parse_query                   L1065  문자열 -> List<RawStmt>
      |     +-- raw_parser                      L613   (parser/parser.c L42, flex + bison)
      +-- foreach RawStmt                       L1095
      |     +-- 실패한 블록이면 COMMIT/ROLLBACK 말고 거부   L1134
      |     +-- start_xact_command              L1143
      |     +-- 여러 문장이면 BeginImplicitTransactionBlock  L1153
      |     +-- PushActiveSnapshot              L1163  분석과 계획이 쓸 스냅샷
      |     +-- [03] pg_analyze_and_rewrite_fixedparams  L1190
      |     |     +-- [04] parse_analyze_fixedparams     L683  RawStmt -> Query
      |     |     |     +-- transformTopLevelStmt        (parser/analyze.c L249)
      |     |     +-- [05] pg_rewrite_query              L692  Query -> List<Query>
      |     |           +-- QueryRewrite                 L818  (rewrite/rewriteHandler.c L4635)
      |     +-- pg_plan_queries                 L1193  List<Query> -> List<PlannedStmt>
      |     |     +-- [06] pg_plan_query        L995
      |     |           +-- planner             L901   (optimizer/plan/planner.c L300)
      |     |                 +-- [07] standard_planner      planner.c L316
      |     |                       +-- subquery_planner      L448
      |     |                       |     +-- [08] grouping_planner  L1258  Path 를 만든다
      |     |                       +-- create_plan           L454   Path -> Plan
      |     +-- PopActiveSnapshot               L1207
      |     +-- CreatePortal("")                L1216  이름 없는 포털
      |     +-- PortalDefineQuery               L1225  PlannedStmt 목록을 포털에
      |     +-- [09] PortalStart                L1235  전략 고르기, ExecutorStart
      |     +-- [10] PortalRun                  L1274  --> [executor] ExecutorRun
      |     +-- PortalDrop                      L1283
      |     +-- 마지막 문장이면 finish_xact_command    L1298
      |     |   TransactionStmt 면 finish_xact_command L1306
      |     |   아니면 CommandCounterIncrement         L1321
      |     +-- EndCommand                      L1337  CommandComplete 'C'
      +-- finish_xact_command                   L1349  --> [커밋]

 [01] [02] [03] [05] [06] 의 줄은 tcop/postgres.c, [04] 는 parser/analyze.c,
 [07] [08] 은 optimizer/plan/planner.c, [09] [10] 은 tcop/pquery.c 의 줄이다
```

단계마다 손에 쥔 자료구조가 바뀐다. 한 단계의 출력이 다음 단계의 입력이고, 개수가 바뀔 수 있는 자리는 규칙 재작성 하나뿐이다.

```text
 SELECT name FROM users WHERE id = 1 하나가 거치는 모양

 const char *query_string
      |  [02] raw_parser            문법만 본다. 카탈로그를 읽지 않는다
      v
 List of RawStmt       (1 개)
   RawStmt.stmt = SelectStmt
     targetList  ResTarget(ColumnRef "name")
     fromClause  RangeVar "users"
     whereClause A_Expr "=" (ColumnRef "id", A_Const 1)
      |  [04] transformStmt         이름을 카탈로그로 푼다
      v
 Query                 (1 개)
   commandType  CMD_SELECT
   rtable       [ RangeTblEntry users (relid = users 의 OID) ]
   jointree     FromExpr( RangeTblRef 1, quals: OpExpr int4eq(Var 1.id, Const 1) )
   targetList   [ TargetEntry Var 1.name ]
      |  [05] QueryRewrite          뷰 펼치기, 규칙 적용. 0 개 또는 여러 개가 될 수 있다
      v
 List of Query         (보통 1 개)
      |  [06]-[08] planner          방법을 고른다 (Path 들 중 가장 싼 것)
      v
 List of PlannedStmt   (Query 마다 1 개)
   planTree     SeqScan 또는 IndexScan (users, qual id = 1)
   rtable       평평하게 편 range table
      |  CreatePortal + PortalDefineQuery
      v
 Portal ""             (RawStmt 마다 1 개)
   stmts        위 PlannedStmt 목록
   strategy     PORTAL_ONE_SELECT          [09] ChoosePortalStrategy
   queryDesc    ExecutorStart 가 만든 실행 상태
      |  [10] PortalRun -> ExecutorRun
      v
 DataRow 들이 DestReceiver 로 나간다

 노드 이름(SelectStmt, RangeVar, OpExpr ...)은 실제 타입 이름이고,
 int4eq 와 계획 노드 종류는 users.id 가 int4 이고 인덱스 유무에 따라 달라지는 예시다
```

트랜잭션 경계는 문자열 하나와 문장 하나의 두 겹이다. 문장 개수와 `BEGIN` 유무에 따라 커밋 자리가 바뀐다.

```text
 문자열 하나가 트랜잭션을 몇 개 만드는가

 query string                        xacts  commit at     설명
 "SELECT 1"                          1      L1298         블록 밖 문장 하나
 "INSERT ...; INSERT ..."            1      L1297-L1298   암묵 블록. 마지막 문장 뒤
 "BEGIN; INSERT ...; COMMIT"         1      L1298         명시 블록. COMMIT 이 마지막 문장이라
 "INSERT ...; COMMIT; INSERT ..."    2      L1306, L1298  COMMIT 이 암묵 블록을 닫고 WARNING
                                                          (xact.c L4065-L4077), 다음 문장은 새 트랜잭션
 "INSERT ..." (앞서 BEGIN 을 보냄)   -      -             열린 블록 안이라 커밋 안 함. 다음 'Z' 가 'T'
```

## 어디에서 쓰이는가

```text
 [연결과 backend 기동]  PostgresMain 의 'Q' 가 이 흐름의 유일한 입구다 (postgres.c L4770)
 [executor]             PortalStart 의 ExecutorStart, PortalRun 의 ExecutorRun 이 넘겨준다
 [MVCC 가시성과 스냅샷] L1163 의 GetTransactionSnapshot (분석/계획용),
                        PortalStart 의 GetTransactionSnapshot (실행용)
 [커밋]                 finish_xact_command -> CommitTransactionCommand
```

같은 단계들(분석, 재작성, 계획, 포털)은 확장 질의 프로토콜의 `exec_parse_message` / `exec_bind_message` / `exec_execute_message` 도 쓴다. 그쪽은 계획을 `CachedPlanSource` 에 담아 재사용한다는 점이 다르다.

## db-engine 에서는

db-engine 은 같은 파이프라인을 `DbEngine.execute` 하나에 일렬로 세웠다. 단계 수는 비슷하지만 의미 분석과 재작성 단계가 없고, 트랜잭션이 SQL 경로에 없다.

```text
 같은 파이프라인, 두 구현 (위 PostgreSQL / 아래 db-engine)

 파싱
   PostgreSQL  raw_parser (flex + bison) -> List of RawStmt. 여러 문장 가능
   db-engine   Lexer(sql).tokenize() -> Parser.parseStatement() -> Statement 하나
               손으로 쓴 재귀 하강 파서, AST 는 sealed class

 의미 분석
   PostgreSQL  transformStmt 가 카탈로그로 테이블, 열, 타입, 연산자를 푼다 -> Query
   db-engine   없음. 열 이름은 문자열로 흘러가고 물리 계획을 만들 때 처음 스키마를 만난다

 재작성
   PostgreSQL  QueryRewrite 가 뷰와 규칙을 적용한다
   db-engine   없음

 계획
   PostgreSQL  standard_planner -> Path 비교 -> create_plan -> PlannedStmt
   db-engine   Translator.toLogicalPlan -> SimpleOptimizer.optimize -> PhysicalPlan
               (Scan / Filter / Project 를 물리 연산자로 1:1 치환)

 실행 단위
   PostgreSQL  Portal (전략, 실행 상태, 커서 위치)
   db-engine   physical.root.iterator().toList()  결과를 한 번에 모은다

 트랜잭션
   PostgreSQL  start_xact_command / finish_xact_command 가 문자열을 감싼다
   db-engine   SQL 경로에 없음. wal.TransactionManager 를 코드에서 직접 쓴다
```

db-engine 의 `execute` 는 `when (stmt)` 로 SELECT 만 옵티마이저를 거치고 INSERT, CREATE, DROP 은 바로 실행한다. PostgreSQL 에서 같은 구분은 `CMD_UTILITY` 다. CREATE 와 DROP 은 계획 없이 `PlannedStmt.utilityStmt` 에 실려 `ProcessUtility` 로 가고, INSERT 는 SELECT 처럼 계획을 거쳐 `ModifyTable` 노드가 된다. 챕터: [12-01-sql-parser](../../../../../project/db-engine/12-01-sql-parser/), [13-02-sql-translator](../../../../../project/db-engine/13-02-sql-translator/), [14-00-db-engine](../../../../../project/db-engine/14-00-db-engine/).

## 단계

1. [exec_simple_query](01_exec_simple_query/README.md)가 문자열 하나를 트랜잭션으로 감싸고, 문장마다 분석, 계획, 포털 실행을 돌린다.
2. [pg_parse_query](02_pg_parse_query/README.md)가 문법 분석만으로 `RawStmt` 목록을 만든다.
3. [pg_analyze_and_rewrite_fixedparams](03_pg_analyze_and_rewrite_fixedparams/README.md)가 분석과 재작성을 잇는다.
4. [parse_analyze_fixedparams](04_parse_analyze_fixedparams/README.md)가 `RawStmt` 를 `Query` 로 바꾼다.
5. [pg_rewrite_query](05_pg_rewrite_query/README.md)가 규칙 재작성으로 `Query` 목록을 만든다.
6. [pg_plan_query](06_pg_plan_query/README.md)가 `Query` 하나를 플래너에 넘겨 `PlannedStmt` 를 받는다.
7. [standard_planner](07_standard_planner/README.md)가 가장 싼 `Path` 를 골라 `Plan` 트리로 바꾸고 `PlannedStmt` 로 포장한다.
8. [grouping_planner](08_grouping_planner/README.md)가 스캔/조인 위에 집계, 정렬, LIMIT, ModifyTable 을 얹은 `Path` 를 만든다.
9. [PortalStart](09_PortalStart/README.md)가 실행 전략을 고르고 필요하면 `ExecutorStart` 를 부른다.
10. [PortalRun](10_PortalRun/README.md)이 전략대로 실행하고 `ExecutorRun` 으로 넘긴다.

## 결과가 쓰이는 곳

```text
 PlannedStmt
      --> [executor] ExecutorStart 의 InitPlan 이 planTree 를 PlanState 트리로 바꾼다

 Portal
      --> PortalRun 이 끝나면 L1283 PortalDrop 으로 사라진다 (이름 없는 포털)
      --> 확장 프로토콜과 커서(DECLARE)에서는 이름 있는 포털로 남아 여러 번 FETCH 된다

 QueryCompletion qc
      --> EndCommand 가 "SELECT 1", "INSERT 0 1" 같은 CommandComplete 를 보낸다

 트랜잭션 상태
      --> finish_xact_command 가 [커밋] 으로 넘기거나, 블록 안이면 CommandCounterIncrement 만 한다
      --> PostgresMain 의 다음 ReadyForQuery 가 'I' / 'T' / 'E' 로 알린다
```

## 다루지 않는 것

문법 파일(`gram.y`)과 어휘 분석기(`scan.l`)의 내부, 각 `transform*` 함수(FROM, WHERE, 대상 목록, 집계 검사), 규칙 시스템 내부(`RewriteQuery`, `fireRIRrules`), 플래너의 경로 탐색 본체(`query_planner`, 조인 순서, 비용 모델), `create_plan` 과 `set_plan_references`, 계획 캐시(`plancache.c`), 확장 질의 프로토콜 경로, `ProcessUtility` 이하 DDL 실행, 로그 관련 처리(`check_log_statement`, `check_log_duration`)는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 exec_simple_query](01_exec_simple_query/README.md)
- [02 pg_parse_query](02_pg_parse_query/README.md)
- [03 pg_analyze_and_rewrite_fixedparams](03_pg_analyze_and_rewrite_fixedparams/README.md)
- [04 parse_analyze_fixedparams](04_parse_analyze_fixedparams/README.md)
- [05 pg_rewrite_query](05_pg_rewrite_query/README.md)
- [06 pg_plan_query](06_pg_plan_query/README.md)
- [07 standard_planner](07_standard_planner/README.md)
- [08 grouping_planner](08_grouping_planner/README.md)
- [09 PortalStart](09_PortalStart/README.md)
- [10 PortalRun](10_PortalRun/README.md)
