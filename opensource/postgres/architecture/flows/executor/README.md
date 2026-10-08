# executor

상위: [PostgreSQL 아키텍처 지도](../../README.md)

planner 가 만든 계획 트리(`Plan`)를 받아 **같은 모양의 실행 상태 트리(`PlanState`)를 세우고, 꼭대기 노드에 "행 하나 달라"를 반복해서 결과를 뽑아내는** 흐름이다. 실행은 아래에서 밀어 올리는 방식이 아니라 위에서 당기는 방식(demand-pull, Volcano 모델)이다. `ExecutePlan` 이 꼭대기에 `ExecProcNode` 를 부르면 그 노드가 자식에게 다시 `ExecProcNode` 를 부르고, 맨 아래 스캔 노드가 테이블에서 행 하나를 꺼내 슬롯에 담아 돌려준다. 쓰기 문장도 같은 틀을 탄다. `INSERT ... SELECT` 의 꼭대기는 `ModifyTable` 노드이고, 이 노드가 자식(스캔)에게서 행을 당겨 올 때마다 `ExecInsert` 로 BEFORE 트리거, 제약 검사, 힙 삽입, 인덱스 삽입, AFTER 트리거 적재를 순서대로 한다. 흐름은 `ExecutorStart`(트리 세우기) -> `ExecutorRun`(당기기) -> `ExecutorFinish`(AFTER 트리거 실행) -> `ExecutorEnd`(정리) 네 단계로 나뉘고, 힙 한 줄을 실제로 쓰는 일은 [행 쓰기와 WAL 기록](../heap-insert-wal/README.md), 인덱스에 넣는 일은 [nbtree 삽입과 분할](../nbtree-insert/README.md), 스캔이 행을 고르는 일은 [MVCC 가시성과 스냅샷](../mvcc-visibility/README.md)으로 넘어간다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 backend 하나 (호출자: tcop/pquery.c)
   SELECT       PortalStart L518 -> ExecutorStart,  PortalRunSelect L921 -> ExecutorRun
   INSERT 등    PortalRunMulti L1272 -> ProcessQuery L137 -> Start, Run, Finish, End 를 차례로
 ------------------------------------------------------------------
 시작 - 트리 세우기
 [01] standard_ExecutorStart                          execMain.c L141
      +-- 읽기 전용 트랜잭션이면 쓰기 계획을 거부    L170
      +-- CreateExecutorState, es_query_cxt 로 전환   L175, L178
      +-- INSERT/UPDATE/DELETE/MERGE 면 es_output_cid L233  새 행에 찍을 command id
      +-- RegisterSnapshot(queryDesc->snapshot)       L245
      +-- AfterTriggerBeginQuery                       L256  AFTER 트리거 큐의 층을 하나 연다
      +-- [02] InitPlan                                L261
            +-- ExecCheckPermissions                   L851
            +-- ExecInitRangeTable, 초기 파티션 가지치기 L856, L871
            +-- 서브플랜마다 ExecInitNode              L978
            +-- [03] ExecInitNode(planTree)            L991  재귀로 PlanState 트리를 만든다
            |     +-- T_ModifyTable -> ExecInitModifyTable    execProcnode.c L176
            |     |     +-- ExecInitNode(자식)                nodeModifyTable.c L4882
            |     +-- T_SeqScan -> ExecInitSeqScan            execProcnode.c L209
            |     +-- ExecSetExecProcNode                     execProcnode.c L391
            |           ExecProcNode = ExecProcNodeFirst 로 감싼다
            +-- SELECT 에 junk 열이 있으면 JunkFilter  L1018
 ------------------------------------------------------------------
 실행 - 당기기
 [04] standard_ExecutorRun                            execMain.c L307
      +-- SELECT 이거나 RETURNING 이면 dest->rStartup L347-L351
      +-- [05] ExecutePlan                             L366
      |     for (;;)                                   L1703
      |       +-- ExecProcNode(꼭대기)                 L1711  --> [06] 첫 호출만 ExecProcNodeFirst
      |       |     SeqScan 이면   [07] ExecSeqScan    nodeSeqscan.c L110
      |       |                      -> SeqNext -> table_scan_getnextslot  --> [MVCC 가시성과 스냅샷]
      |       |     ModifyTable 이면 [08] ExecModifyTable nodeModifyTable.c L4175
      |       |                      +-- fireBSTriggers                        L4219
      |       |                      +-- for: ExecProcNode(자식)               L4280
      |       |                      |     +-- [09] ExecInsert                 L4509
      |       |                      |           +-- BEFORE ROW 트리거         L911
      |       |                      |           +-- ExecConstraints           L1096
      |       |                      |           +-- table_tuple_insert        L1234  --> [행 쓰기와 WAL 기록]
      |       |                      |           +-- ExecInsertIndexTuples     L1240  --> [nbtree 삽입과 분할]
      |       |                      |           +-- ExecARInsertTriggers      L1277  AFTER 는 큐에만 쌓는다
      |       |                      +-- fireASTriggers                        L4589
      |       +-- 빈 슬롯이면 끝                       L1717
      |       +-- dest->receiveSlot                    L1742  클라이언트로 보낸다
      +-- dest->rShutdown                              L383
 ------------------------------------------------------------------
 마무리
 [10] standard_ExecutorFinish                         execMain.c L415
      +-- ExecPostprocessPlan                          L439  CTE 안의 ModifyTable 을 끝까지 돌린다
      +-- AfterTriggerEndQuery                         L443  쌓아 둔 AFTER 트리거를 여기서 실행
      standard_ExecutorEnd                             execMain.c L475
      +-- ExecEndPlan                                  L504  노드 정리, 릴레이션 닫기
      +-- UnregisterSnapshot, FreeExecutorState        L507, L519
```

계획 트리와 실행 상태 트리는 모양이 같다. `ExecInitNode` 가 계획 노드 하나마다 상태 노드 하나를 만들고, 상태 노드의 `plan` 이 계획 노드를 가리킨다. 계획은 읽기 전용으로 남고, 실행 중에 바뀌는 것은 전부 상태 노드에 있다.

```text
 INSERT INTO t2 SELECT * FROM t1 WHERE a > 10;

 계획 트리 (PlannedStmt.planTree, 읽기 전용)        실행 상태 트리 (queryDesc->planstate)

 ModifyTable                                         ModifyTableState
   operation = CMD_INSERT          <-- plan --       ExecProcNode = ExecModifyTable
   resultRelations = [t2]                            resultRelInfo (t2 를 연 ResultRelInfo)
   |  outerPlan                                      fireBSTriggers = true, mt_done = false
   v                                                 |  outerPlanState
 SeqScan                                             v
   scanrelid = t1                  <-- plan --       SeqScanState
   qual = (a > 10)                                   ss_currentRelation = t1
                                                     ss_currentScanDesc = NULL (첫 SeqNext 에서 연다)
                                                     ExecProcNode = ExecSeqScanWithQual (projection 이 없을 때, [07])

 둘 다 EState 하나를 공유한다 (es_snapshot, es_output_cid, es_processed, es_query_cxt ...)
```

당기는 쪽에서 보면 SELECT 와 INSERT 의 차이는 꼭대기 노드가 행을 몇 번 돌려주느냐다. SELECT 는 행마다 한 번씩 돌아오고, RETURNING 없는 INSERT 는 `ExecModifyTable` 이 자식을 다 비운 뒤 빈 슬롯을 한 번 돌려준다.

```text
 SELECT a FROM t1 WHERE a > 10   (행 3개가 조건을 통과한다고 하자)

 ExecutePlan              ExecSeqScan                  table_scan_getnextslot
 ------------             -----------                  ----------------------
 ExecProcNode  ------->   ExecScanFetch -> SeqNext --> r1 (a=5)      qual 거짓, 다시
                          ExecScanFetch -> SeqNext --> r2 (a=12)     qual 참
          <------- slot(r2)
 receiveSlot(r2)
 ExecProcNode  ------->   ...                      --> r3 (a=40) 참
          <------- slot(r3)
 receiveSlot(r3)
 ...                                                    (r4 통과)
 ExecProcNode  ------->   SeqNext                  --> false (끝)
          <------- 빈 슬롯
 break, es_processed = 3

 INSERT INTO t2 SELECT * FROM t1 WHERE a > 10   (RETURNING 없음)

 ExecutePlan              ExecModifyTable                         자식 SeqScanState
 ------------             ---------------                         -----------------
 ExecProcNode  ------->   fireBSTriggers
                          ExecProcNode(child) ----------------->  r2
                          ExecInsert(r2)  slot = NULL 이라 계속
                          ExecProcNode(child) ----------------->  r3
                          ExecInsert(r3)
                          ExecProcNode(child) ----------------->  r4
                          ExecInsert(r4)
                          ExecProcNode(child) ----------------->  빈 슬롯
                          fireASTriggers, mt_done = true
          <------- NULL
 break   (꼭대기 루프는 한 바퀴. es_processed = 3 은 ExecInsert 가 올렸다)
```

## 어디에서 쓰이는가

```text
 [쿼리 실행 파이프라인]  PortalStart / PortalRun 이 이 흐름의 네 진입점을 부른다
                          SELECT 는 PORTAL_ONE_SELECT 로 커서처럼 여러 번 ExecutorRun 할 수 있고
                          RETURNING 없는 INSERT 는 PORTAL_MULTI_QUERY 로 ProcessQuery 한 번에 끝난다
                          (pquery.c L258, L306)
 SPI, COPY TO, EXPLAIN ANALYZE, SQL 함수   같은 진입점을 부른다
                          (spi.c L2930, copyto.c L848, explain.c L565, functions.c L1389)
 [MVCC 가시성과 스냅샷]  [07] 의 SeqNext 가 es_snapshot 으로 table_beginscan 한다
 [행 쓰기와 WAL 기록]    [09] 의 table_tuple_insert 가 heapam_tuple_insert -> heap_insert 로 간다
 [nbtree 삽입과 분할]    [09] 의 ExecInsertIndexTuples 가 그 흐름의 [01] 이다
```

다음 흐름은 쓰기라면 [행 쓰기와 WAL 기록](../heap-insert-wal/README.md), 읽기라면 [MVCC 가시성과 스냅샷](../mvcc-visibility/README.md)이다.

## db-engine 에서는

같은 문제(연산자를 쌓아 한 행씩 당기기)를 db-engine 은 Kotlin `Sequence` 하나로 풀었다. 연산자마다 `iterator()` 가 지연 시퀀스를 돌려주고, 위 연산자가 아래 시퀀스를 `filter`, `map` 으로 감싼다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 연산자 인터페이스
   PostgreSQL  PlanState.ExecProcNode(node) 를 한 번 부르면 슬롯 하나. 빈 슬롯이면 끝
   db-engine   Operator.iterator(): Sequence<Tuple>. 소비자가 다음 원소를 당길 때 계산된다

 트리 세우기
   PostgreSQL  계획 트리(Plan)와 실행 상태 트리(PlanState)를 따로 둔다. ExecInitNode 가 재귀로 만든다
   db-engine   Filter(SeqScan(heap), pred) 처럼 생성자로 바로 쌓는다. 계획과 상태가 한 객체

 조건과 투영
   PostgreSQL  스캔 노드 안에 접어 넣는다. ExecScanExtended 가 qual 과 projection 을 같이 처리
   db-engine   Filter, Project 가 각각 독립 연산자다

 쓰기
   PostgreSQL  ModifyTable 도 계획 노드다. 자식에게서 행을 당겨 ExecInsert 한다
   db-engine   InsertOp 은 Operator 가 아니다. insertOne / insertMany 를 직접 부르는 명령형 API

 쓰기 한 행에 붙는 일
   PostgreSQL  BEFORE 트리거 -> 제약 -> 힙 -> 인덱스 -> AFTER 트리거 적재 -> RETURNING
   db-engine   TableHeap.insert 한 번 (제약 검사는 06-03 constraint-validator 가 따로)
```

db-engine 의 `TableHeap.scan` 은 페이지 하나의 튜플을 리스트로 다 꺼낸 뒤 pin 을 풀고 `yieldAll` 한다. PostgreSQL 의 `SeqNext` 는 스캔 기술자(`ss_currentScanDesc`)를 노드에 들고 다니며, 슬롯을 돌려준 뒤에도 다음 호출 때 이어서 읽는다. db-engine 의 impl 문서도 `Operator` 를 "Volcano(iterator) 모델"이라 부르고, 이 인터페이스가 있어야 `Filter` 가 `SeqScan` 을 감쌀 수 있다고 적었다. 챕터: [06-01-table-seqscan](../../../../../project/db-engine/06-01-table-seqscan/), [06-02-filter-project-expression](../../../../../project/db-engine/06-02-filter-project-expression/).

## 단계

1. [standard_ExecutorStart](01_standard_ExecutorStart/README.md)가 `EState` 를 만들고 스냅샷과 command id 를 박은 뒤 `InitPlan` 을 부른다.
2. [InitPlan](02_InitPlan/README.md)이 권한을 검사하고 range table 을 연 뒤 계획 트리 꼭대기에 `ExecInitNode` 를 부른다.
3. [ExecInitNode](03_ExecInitNode/README.md)가 노드 종류로 갈라 `ExecInitXxx` 를 부르고, 자식은 각 `ExecInitXxx` 가 재귀로 부른다.
4. [standard_ExecutorRun](04_standard_ExecutorRun/README.md)이 결과 수신자를 열고 `ExecutePlan` 을 부른다.
5. [ExecutePlan](05_ExecutePlan/README.md)이 꼭대기에 `ExecProcNode` 를 반복하고, 받은 슬롯을 수신자에게 넘긴다.
6. [ExecProcNodeFirst](06_ExecProcNodeFirst/README.md)가 노드의 첫 호출에서 스택 깊이를 검사하고 진짜 실행 함수로 갈아 끼운다.
7. [ExecSeqScan](07_ExecSeqScan/README.md)이 `SeqNext` 로 테이블에서 행을 꺼내고, 조건과 투영을 적용한다.
8. [ExecModifyTable](08_ExecModifyTable/README.md)이 문장 트리거를 쏘고, 자식에게서 행을 당겨 명령 종류별 함수로 보낸다.
9. [ExecInsert](09_ExecInsert/README.md)가 행 하나를 트리거, 제약, 힙, 인덱스, AFTER 트리거 순서로 넣는다.
10. [standard_ExecutorFinish](10_standard_ExecutorFinish/README.md)가 AFTER 트리거를 실행하고, `standard_ExecutorEnd` 가 트리를 정리한다.

## 결과가 쓰이는 곳

```text
 queryDesc->planstate (PlanState 트리)
      --> ExecutorRun 이 여러 번 불려도 같은 트리를 이어서 당긴다 (커서, FETCH)
      --> ExecutorEnd 의 ExecEndNode 가 같은 모양으로 내려가며 스캔을 닫고 pin 을 푼다

 estate->es_processed
      --> SELECT 는 ExecutePlan 이, INSERT 는 ExecInsert 가 올린다
      --> ProcessQuery 가 "INSERT 0 3" 같은 명령 완료 태그로 만든다 (pquery.c L174)

 dest->receiveSlot 으로 나간 슬롯
      --> 클라이언트로 가는 수신자면 printtup 이 DataRow 메시지로 만든다 (access/common/printtup.c L326)

 AFTER 트리거 이벤트 큐
      --> [09] 가 쌓고, [10] 의 AfterTriggerEndQuery 가 실행한다
      --> DEFERRED 로 미룬 이벤트는 전역 목록으로 옮겨져 커밋 때
          AfterTriggerFireDeferred 가 실행한다 (access/transam/xact.c L2262) --> [커밋]
```

## 다루지 않는 것

조인, 정렬, 집계 노드(`ExecNestLoop`, `ExecHashJoin`, `ExecSort`, `ExecAgg`)의 내부, 병렬 쿼리(`Gather` 와 parallel worker), JIT 로 컴파일된 식 평가(`ExecInterpExpr`, `llvmjit`), `EvalPlanQual` 재검사, UPDATE/DELETE/MERGE 경로(`ExecUpdate`, `ExecDelete`, `ExecMerge`), 파티션 라우팅(`ExecPrepareTupleRouting`), FDW 쓰기와 배치 삽입(`ExecBatchInsert`), `INSERT ... ON CONFLICT` 의 추측 삽입은 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 standard_ExecutorStart](01_standard_ExecutorStart/README.md)
- [02 InitPlan](02_InitPlan/README.md)
- [03 ExecInitNode](03_ExecInitNode/README.md)
- [04 standard_ExecutorRun](04_standard_ExecutorRun/README.md)
- [05 ExecutePlan](05_ExecutePlan/README.md)
- [06 ExecProcNodeFirst](06_ExecProcNodeFirst/README.md)
- [07 ExecSeqScan](07_ExecSeqScan/README.md)
- [08 ExecModifyTable](08_ExecModifyTable/README.md)
- [09 ExecInsert](09_ExecInsert/README.md)
- [10 standard_ExecutorFinish](10_standard_ExecutorFinish/README.md)
