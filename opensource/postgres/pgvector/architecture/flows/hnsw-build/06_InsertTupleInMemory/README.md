# InsertTupleInMemory

상위: [HNSW 빌드](../README.md)

**메모리 그래프에 원소 하나를 넣는 동안 진입점을 지키는 함수다.** 보통은 진입점 잠금을 공유로 잡아 여러 일꾼이 동시에 넣게 한다. 새 원소의 층이 지금 진입점보다 높으면(또는 그래프가 비어 있으면) 이 원소가 새 진입점이 될 것이므로 잠금을 배타로 바꿔 잡는다. 이웃 찾기와 그래프 갱신은 잠금을 쥔 채 아래 두 함수에 맡긴다.

## 위치

`src` / `hnswbuild.c` L437-L480 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswbuild.c#L437-L480))

## 실제 코드

```c
// hnswbuild.c L434-L480
/*
 * Insert tuple in memory
 */
static void
InsertTupleInMemory(HnswBuildState * buildstate, HnswElement element)
{
	HnswGraph  *graph = buildstate->graph;
	HnswSupport *support = &buildstate->support;
	HnswElement entryPoint;
	LWLock	   *entryLock = &graph->entryLock;
	LWLock	   *entryWaitLock = &graph->entryWaitLock;
	int			efConstruction = buildstate->efConstruction;
	int			m = buildstate->m;
	char	   *base = buildstate->hnswarea;

	/* Wait if another process needs exclusive lock on entry lock */
	LWLockAcquire(entryWaitLock, LW_EXCLUSIVE);
	LWLockRelease(entryWaitLock);

	/* Get entry point */
	LWLockAcquire(entryLock, LW_SHARED);
	entryPoint = HnswPtrAccess(base, graph->entryPoint);

	/* Prevent concurrent inserts when likely updating entry point */
	if (entryPoint == NULL || element->level > entryPoint->level)
	{
		/* Release shared lock */
		LWLockRelease(entryLock);

		/* Tell other processes to wait and get exclusive lock */
		LWLockAcquire(entryWaitLock, LW_EXCLUSIVE);
		LWLockAcquire(entryLock, LW_EXCLUSIVE);
		LWLockRelease(entryWaitLock);

		/* Get latest entry point after lock is acquired */
		entryPoint = HnswPtrAccess(base, graph->entryPoint);
	}

	/* Find neighbors for element */
	HnswFindElementNeighbors(base, element, entryPoint, NULL, support, m, efConstruction, false);

	/* Update graph in memory */
	UpdateGraphInMemory(support, element, m, entryPoint, buildstate);

	/* Release entry lock */
	LWLockRelease(entryLock);
}
```

## 동작 흐름

```text
 InsertTupleInMemory(buildstate, element)            L437
   L450  entryWaitLock X 잡았다 바로 놓기     배타 대기자가 있으면 여기서 줄 선다
   L454  entryLock S
   L455  entryPoint = graph->entryPoint
   L458  entryPoint == NULL  또는  element->level > entryPoint->level ?
           예  L461  entryLock S 해제
               L464  entryWaitLock X       다른 일꾼이 새로 S 를 잡지 못하게
               L465  entryLock X           기존 S 보유자가 끝나길 기다린다
               L466  entryWaitLock 해제
               L469  entryPoint 다시 읽기   그 사이 바뀌었을 수 있다
   L473  [07] HnswFindElementNeighbors(base, element, entryPoint, NULL, ...)
                index = NULL -> 메모리 모드
   L476  [08] UpdateGraphInMemory
   L479  entryLock 해제
```

`entryWaitLock` 은 배타 잠금을 기다리는 쪽이 굶지 않게 하는 문지기다. 공유 잠금을 잡으려는 쪽도 먼저 문지기를 한 번 통과해야 하므로(L450-L451), 누군가 배타를 기다리는 동안에는 새 공유 잠금이 끼어들지 못한다.

```text
 진입점이 level 2 일 때 세 일꾼 A (level 0), B (level 3), C (level 1)

 1  A  wait 통과 -> entry S -> 이웃 찾기와 갱신 중
 2  B  wait 통과 -> entry S -> 3 > 2 라서 entry S 해제            L458-L461
 3  B  wait X 보유 -> entry X 요청, A 의 S 가 풀리길 기다린다     L464-L465
 4  C  wait X 요청 -> B 가 쥐고 있어 기다린다                      L450
       (entry S 로 바로 끼어들지 못한다)
 5  A  entry S 해제
 6  B  entry X 획득 -> wait 해제 -> 진입점 다시 읽기               L465-L469
 7  C  wait 통과 -> entry S 요청, B 의 X 가 풀리길 기다린다
 8  B  이웃 찾기, 갱신, graph->entryPoint = B -> entry X 해제
 9  C  entry S 획득 -> 새 진입점 B 에서 탐색을 시작한다
```

진입점보다 낮은 층의 원소는 진입점을 바꾸지 않으므로 공유 잠금으로 충분하다. 원소마다의 이웃 목록은 원소의 `lock`(LWLock) 으로 따로 지킨다(머리 주석 L20-L21).

## 결과가 쓰이는 곳

```text
 entryPoint (잠금 아래에서 읽은 값)
      --> [07] 이 맨 위층 탐색을 여기서 시작한다
      --> [08] 이 새 원소의 층이 더 높으면 graph->entryPoint 를 바꾼다
```

## 다루지 않는 것

디스크 단계와 INSERT 는 같은 일을 LWLock 대신 페이지 잠금 `HNSW_UPDATE_LOCK`(블록 0 번호를 잠금 이름으로 쓴다, hnsw.h L49-L51)으로 한다(`HnswInsertTupleOnDisk`, hnswinsert.c L711-L735). 그 경로는 범위 밖이다.
