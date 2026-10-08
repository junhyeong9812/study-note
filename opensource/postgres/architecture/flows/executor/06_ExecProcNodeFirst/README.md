# ExecProcNodeFirst

상위: [executor](../README.md)

**노드마다 딱 한 번만 지나는 입구다.** 첫 호출에서 스택 깊이를 검사하고, 노드의 `ExecProcNode` 칸을 진짜 실행 함수(계측이 켜져 있으면 계측 래퍼)로 바꿔 끼운 뒤 그 함수를 부른다. 두 번째 호출부터는 이 함수를 거치지 않는다. 행마다 드는 검사 비용을 첫 행 한 번으로 줄이는 장치다.

## 위치

`executor` / `execProcnode.c` L448-L470 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execProcnode.c#L448-L470))

## 실제 코드

모든 노드 호출은 헤더의 인라인 함수 `ExecProcNode` 를 지난다. 파라미터가 바뀌었으면 재스캔하고, 아니면 노드의 `ExecProcNode` 칸에 든 함수 포인터를 부른다.

`src` / `include` / `executor` / `executor.h` L302-L317 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/executor/executor.h#L302-L317))

```c
// executor.h L302-L317
/* ----------------------------------------------------------------
 *		ExecProcNode
 *
 *		Execute the given node to return a(nother) tuple.
 * ----------------------------------------------------------------
 */
#ifndef FRONTEND
static inline TupleTableSlot *
ExecProcNode(PlanState *node)
{
	if (node->chgParam != NULL) /* something changed? */
		ExecReScan(node);		/* let ReScan handle this */

	return node->ExecProcNode(node);
}
#endif
```

그 칸에 처음 들어 있는 함수가 이것이다.

`executor` / `execProcnode.c` L443-L470 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execProcnode.c#L443-L470))

```c
// execProcnode.c L443-L470
/*
 * ExecProcNode wrapper that performs some one-time checks, before calling
 * the relevant node method (possibly via an instrumentation wrapper).
 */
static TupleTableSlot *
ExecProcNodeFirst(PlanState *node)
{
	/*
	 * Perform stack depth check during the first execution of the node.  We
	 * only do so the first time round because it turns out to not be cheap on
	 * some common architectures (eg. x86).  This relies on the assumption
	 * that ExecProcNode calls for a given plan node will always be made at
	 * roughly the same stack depth.
	 */
	check_stack_depth();

	/*
	 * If instrumentation is required, change the wrapper to one that just
	 * does instrumentation.  Otherwise we can dispense with all wrappers and
	 * have ExecProcNode() directly call the relevant function from now on.
	 */
	if (node->instrument)
		node->ExecProcNode = ExecProcNodeInstr;
	else
		node->ExecProcNode = node->ExecProcNodeReal;

	return node->ExecProcNode(node);
}
```

계측이 켜져 있을 때 대신 들어가는 래퍼다. 행이 나왔는지(1.0) 끝인지(0.0)를 세고 시간을 잰다.

`executor` / `execProcnode.c` L473-L490 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execProcnode.c#L473-L490))

```c
// execProcnode.c L473-L490
/*
 * ExecProcNode wrapper that performs instrumentation calls.  By keeping
 * this a separate function, we avoid overhead in the normal case where
 * no instrumentation is wanted.
 */
static TupleTableSlot *
ExecProcNodeInstr(PlanState *node)
{
	TupleTableSlot *result;

	InstrStartNode(node->instrument);

	result = node->ExecProcNodeReal(node);

	InstrStopNode(node->instrument, TupIsNull(result) ? 0.0 : 1.0);

	return result;
}
```

## 동작 흐름

```text
 ExecProcNode(node)                             executor.h L310 (static inline)
   L312  chgParam != NULL 이면 ExecReScan(node)  상위에서 파라미터가 바뀌었다 (상관 서브쿼리 등)
   L315  return node->ExecProcNode(node)         함수 포인터 호출

 첫 호출이면 그 포인터가 ExecProcNodeFirst
   L457  check_stack_depth()                    재귀 깊이 검사 (첫 호출에서만)
   L464  instrument 가 있으면
   L465    node->ExecProcNode = ExecProcNodeInstr
   L467  아니면
           node->ExecProcNode = node->ExecProcNodeReal
   L469  return node->ExecProcNode(node)        바꿔 끼운 함수로 이번 호출을 처리
```

스택 검사를 첫 호출에만 하는 이유는 L450-L456 주석에 있다. 몇몇 아키텍처(예: x86)에서 이 검사가 싸지 않고, 같은 노드는 항상 비슷한 스택 깊이에서 불린다고 가정할 수 있기 때문이다.

```text
 SeqScanState 하나의 함수 포인터가 바뀌는 모습 (qual 있음, projection 없음, EXPLAIN ANALYZE 아님)

 node->ExecProcNode         node->ExecProcNodeReal     시점
 ExecSeqScanWithQual        -                          ExecInitSeqScan 직후 (nodeSeqscan.c L274)
 ExecProcNodeFirst          ExecSeqScanWithQual        ExecSetExecProcNode 뒤
 ExecSeqScanWithQual        ExecSeqScanWithQual        1번째 ExecProcNode 뒤. 이후로는 직행

 EXPLAIN ANALYZE 면 1번째 뒤부터 ExecProcNodeInstr -> ExecProcNodeReal 로 두 단계
```

이렇게 하면 실행 경로에 분기가 남지 않는다. 계측을 하지 않는 실행은 `ExecProcNode` 인라인 한 번과 노드 함수 호출 한 번이 전부다.

```text
 한 번의 당김이 지나는 호출 (2번째 행부터, 계측 없음)

 ExecutePlan L1711
   -> ExecProcNode (인라인)            chgParam 확인 한 번
     -> ExecModifyTable                 node->ExecProcNode 가 가리키는 함수
       -> ExecProcNode (인라인)
         -> ExecSeqScanWithQual
           -> ExecScanExtended (인라인) -> SeqNext -> table_scan_getnextslot
```

## 결과가 쓰이는 곳

```text
 node->ExecProcNode 칸
      --> 이후 모든 ExecProcNode(node) 호출이 노드 함수로 바로 간다
 node->instrument
      --> ExecProcNodeInstr 가 InstrStartNode / InstrStopNode 로 쌓은 행 수와 시간을 EXPLAIN ANALYZE 가 노드별로 보여 준다
```

## 다루지 않는 것

`ExecReScan` 과 `chgParam` 이 퍼지는 규칙, 계측 구조체(`Instrumentation`)의 필드, `MultiExecProcNode`(행 대신 해시 테이블이나 비트맵을 돌려주는 노드)는 호출 입구의 곁가지라 요약만 했다.
