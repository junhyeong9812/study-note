# data-structure/08-graph — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Graph (`src/main/java/com/datastructure/graph/Graph.java`)

- `int vertexCount()`
- `int edgeCount()` (무방향에서 u-v 는 한 개로 센다)
- `boolean isDirected()`
- `void addEdge(int from, int to)` (가중치 1)
- `void addEdge(int from, int to, int weight)` (같은 간선이면 가중치 덮어쓰기 / 범위 밖 `IndexOutOfBoundsException` / 음수 가중치 `IllegalArgumentException`)
- `boolean hasEdge(int from, int to)`
- `int weight(int from, int to)` (간선이 없으면 `NO_EDGE = Integer.MAX_VALUE`)
- `Iterable<Integer> neighbors(int from)`

## 구현 — AdjacencyListGraph (`src/main/java/com/datastructure/graph/AdjacencyListGraph.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static class Edge { final int to; int weight; }` — 역할:
- `private final int vertexCount` — 역할:
- `private final boolean directed` — 역할:
- `List<Edge>[] adjacency` — 역할:
- `int edges` — 역할:

### `AdjacencyListGraph(int vertexCount, boolean directed)`

- 하는 일:
- 논리:
- 비용(왜):

### `int vertexCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `int edgeCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isDirected()`

- 하는 일:
- 논리:
- 비용(왜):

### `void addEdge(int from, int to)`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `void addEdge(int from, int to, int weight)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean hasEdge(int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int weight(int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<Integer> neighbors(int from)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — AdjacencyMatrixGraph (`src/main/java/com/datastructure/graph/AdjacencyMatrixGraph.java`)

### `필드`

- `private final int vertexCount` — 역할:
- `private final boolean directed` — 역할:
- `int[][] matrix` — 역할:
- `int edges` — 역할:

### `AdjacencyMatrixGraph(int vertexCount, boolean directed)`

- 하는 일:
- 논리:
- 비용(왜):

### `int vertexCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `int edgeCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isDirected()`

- 하는 일:
- 논리:
- 비용(왜):

### `void addEdge(int from, int to)`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `void addEdge(int from, int to, int weight)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean hasEdge(int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int weight(int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<Integer> neighbors(int from)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| AdjacencyListGraph | | | |
| AdjacencyMatrixGraph | | | |

## 문제 — GraphProblems (`src/main/java/com/datastructure/graph/GraphProblems.java`)

### 문제 1. 최단 거리 (간선 수 기준)

> 문제 설명: `start` 에서 각 정점까지 몇 개의 간선을 거쳐야 하는지. 못 가면 -1. 가중치는 무시한다.
> `0-1, 1-2, 0-3` 인 그래프에서 `start=0` -> `[0, 1, 2, 1]`
> 생각할 것 — 왜 너비 우선(BFS)인가? 깊이 우선으로 하면 왜 최단이 아닌가? /
> 큐가 필요하다. 04번에서 만든 것이 이것이다. /
> 방문 표시를 넣을 때 하는가, 꺼낼 때 하는가? 둘 다 답은 맞다.
> 다만 꺼낼 때 표시하면 같은 정점이 큐에 여러 번 들어가 메모리를 더 쓴다. 정확성이 아니라 비용의 문제다.
> 시그니처: `static int[] bfsDistances(Graph graph, int start)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 깊이 우선 방문 순서

> 문제 설명: `start` 에서 시작해 갈 수 있는 데까지 들어갔다가 되돌아 나오는 순서.
> 이웃은 `neighbors` 가 주는 순서대로 본다.
> 생각할 것 — 스택이 필요하다. 03번에서 만든 것이 이것이다. 재귀를 쓰면 호출 스택이 그 역할을 한다. /
> 재귀로 하면 깊은 그래프에서 StackOverflow 가 난다. 반복으로 하면 그 문제가 없다. /
> 반복으로 할 때 방문 순서를 재귀와 똑같이 맞추려면 이웃을 어떤 순서로 쌓아야 하는가?
> 시그니처: `static int[] dfsOrder(Graph graph, int start)` — 반복으로 구현하라(테스트에 깊은 그래프가 있다).

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 위상 정렬

> 문제 설명: 방향 그래프에서 "모든 간선이 앞에서 뒤로 가도록" 정점을 늘어놓는다.
> 빌드 의존성, 강의 선수과목, 작업 순서가 전부 이 문제다.
> `0->1, 0->2, 1->3, 2->3` -> `[0, 1, 2, 3]` (또는 `[0, 2, 1, 3]`)
> 순환이 있으면 순서를 정할 수 없다. `IllegalStateException` 을 던진다. 무방향 그래프면 `IllegalArgumentException`.
> 생각할 것 — 들어오는 간선이 하나도 없는 정점은 지금 당장 처리할 수 있다. 그 정점을 빼면 어떻게 되는가? /
> 큐를 쓰면 자연스럽다(Kahn 알고리즘). 답이 여러 개일 수 있으므로 테스트는 "순서가 유효한가"만 검사한다. /
> 다 처리했는데 정점이 남아 있으면 그건 무슨 뜻인가?
> 시그니처: `static int[] topologicalSort(Graph graph)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 4. 가중치 최단 거리 (다익스트라)

> 문제 설명: `start` 에서 각 정점까지의 가중치 합이 최소인 경로 비용. 못 가면 -1.
> 생각할 것 — BFS 는 왜 안 되는가? 간선 수가 적어도 가중치 합이 클 수 있다. /
> "지금까지 알아낸 것 중 가장 가까운 정점"을 반복해서 꺼내야 한다. 그게 07번 힙이다.
> (여기서는 `java.util.PriorityQueue` 를 쓴다. 모듈이 분리되어 있어서일 뿐, 07번에서 만든 것이 정확히 이 물건이다.) /
> 이미 확정된 정점을 다시 꺼내면 어떻게 되는가? 걸러내야 하는가? /
> 음수 간선이 있으면 왜 깨지는가? (그래서 `addEdge` 가 음수를 거부한다.)
> 시그니처: `static long[] shortestPaths(Graph graph, int start)`

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/08-graph/README.md`
- 구현: `/home/jun/project/myway/data-structure/08-graph/src/main/java/com/datastructure/graph/`
- 테스트: `/home/jun/project/myway/data-structure/08-graph/src/test/java/com/datastructure/graph/`
- 참고 구현: `/home/jun/project/myway/data-structure/08-graph/impl/`
