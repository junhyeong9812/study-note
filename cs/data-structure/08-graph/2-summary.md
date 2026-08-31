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

### 구조

```
아래 두 구현이 담는 그래프는 같은 것이다 (정점 5개, 무방향, 간선 4개)

        (4)
    v0 ----- v1              v0-v1 가중치 4
    |         |              v0-v3 가중치 2
 (2)|         |(5)           v1-v2 가중치 5
    |         |              v3-v4 가중치 1
    v3       v2
    |
 (1)|
    |
    v4
    정점은 0 .. V-1 정수다. 이름도 객체도 없다 — 그래서 배열 인덱스로 바로 쓸 수 있다

AdjacencyListGraph — 정점마다 "내가 닿는 곳" 목록을 들고 있다
+-----------------------------------------------------+
| vertexCount = 5, directed = false                   |
| edges = 4         (무방향 u-v 는 1개로 센다)          |
| adjacency ---+    (List<Edge>[] — 칸마다 ArrayList)   |
+--------------|--------------------------------------+
               v
    v0  [ Edge(to=1, w=4) ] -> [ Edge(to=3, w=2) ]
    v1  [ Edge(to=0, w=4) ] -> [ Edge(to=2, w=5) ]
    v2  [ Edge(to=1, w=5) ]
    v3  [ Edge(to=0, w=2) ] -> [ Edge(to=4, w=1) ]
    v4  [ Edge(to=3, w=1) ]

    가중치는 별도 배열이 아니라 Edge 객체 안에 to 와 나란히 들어 있다
    무방향 간선 하나 = Edge 객체 2개 (양쪽 목록에 하나씩) + edges 는 1 증가
    목록 순서 = 넣은 순서다 (정렬되어 있지 않다)
    전체 메모리는 O(V + E) — 간선이 없는 정점은 빈 리스트 하나로 끝난다
```

### 동작 — 간선 추가

```
addEdge(0, 3, 2) — 무방향
    (1) findEdge(0, 3) 으로 이미 있는지 본다 (v0 목록을 처음부터 훑는다) -> O(deg(0))
            있으면 : existing.weight = 2 로 덮어쓰고 반대쪽 Edge(3->0) 도 갱신. edges 는 그대로
            없으면 : 아래로

    (2) before  v0  [ to=1, w=4 ]
                v3  ( 비어 있음 )

        after   v0  [ to=1, w=4 ] -> [ to=3, w=2 ]      <- 양쪽 목록에 하나씩 추가한다
                v3  [ to=0, w=2 ]
                edges++    (1 증가다. Edge 객체는 2개지만 간선은 1개)

    무방향 셀프루프(from == to)는 Edge 를 하나만 넣는다 — 같은 목록에 두 번 넣으면 중복이 된다
    addEdge(from, to) 는 가중치 1 로 위임한다
```

### 동작 — 조회와 순회

```
hasEdge(0, 3) / weight(0, 3) : v0 목록을 처음부터 훑는다 -> O(deg(0))
    v0  [ to=1, w=4 ] -> [ to=3, w=2 ]
           x (1 != 3)      o 발견
    weight 는 못 찾으면 Graph.NO_EDGE 를 돌려준다 (예외가 아니다)
    "이 둘이 연결됐나"를 물을 때마다 목록 길이만큼 걸린다 — 이 표현의 약점이 여기다

neighbors(0) : 목록에서 e.to 만 뽑아 새 리스트로 복사해 준다 -> O(deg(0))
    v0  [ to=1, w=4 ] -> [ to=3, w=2 ]      =>      [ 1, 3 ]
                                                    (넣은 순서. 정렬이 아니다)

    이웃만 훑는 알고리즘(BFS / DFS / 다익스트라)이 이 표현을 좋아하는 이유가 이것이다.
    모든 정점의 이웃을 한 번씩 보면 정확히 O(V + E) — 없는 간선을 헛보지 않는다
```

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

### 구조

```
AdjacencyMatrixGraph — V x V 표를 깔아 놓고 (from, to) 칸에 가중치를 적는다
    담는 그래프는 인접 리스트 쪽과 똑같다 (v0-v1:4, v0-v3:2, v1-v2:5, v3-v4:1)
+-----------------------------------------------------+
| vertexCount = 5, directed = false                   |
| edges = 4                                           |
| matrix ---+   (int[][] — 없음을 NO_EDGE 로 적어 둔다)  |
+-----------|-----------------------------------------+
            v
                  to:  0     1     2     3     4
              from  +-----+-----+-----+-----+-----+
                 0  |  .  |  4  |  .  |  2  |  .  |
                    +-----+-----+-----+-----+-----+
                 1  |  4  |  .  |  5  |  .  |  .  |
                    +-----+-----+-----+-----+-----+
                 2  |  .  |  5  |  .  |  .  |  .  |
                    +-----+-----+-----+-----+-----+
                 3  |  2  |  .  |  .  |  .  |  1  |
                    +-----+-----+-----+-----+-----+
                 4  |  .  |  .  |  .  |  1  |  .  |
                    +-----+-----+-----+-----+-----+

    "." 은 Graph.NO_EDGE = Integer.MAX_VALUE 다. 0 도 -1 도 아니다.
        0 을 "없음"으로 쓰면 가중치가 0 인 정상 간선과 구분할 수 없기 때문이다
    별도의 boolean present 배열도 없다 — 한 칸이 "있느냐"와 "얼마냐"를 동시에 답한다
    생성자에서 모든 행을 NO_EDGE 로 채워 두는 것이 이 표현의 출발점이다

    무방향이면 표가 대각선 기준으로 대칭이다 (matrix[u][v] == matrix[v][u])
    칸 수는 언제나 V x V = 25 — 간선이 4개뿐이어도 25칸을 잡는다. 메모리 O(V^2)
```

### 동작 — 간선 추가

```
addEdge(0, 3, 2) — 무방향
    if (matrix[0][3] == NO_EDGE) edges++;    <- 이미 있던 간선이면 개수를 올리지 않는다
    matrix[0][3] = 2;
    무방향이면 matrix[3][0] = 2;               <- 대칭 칸도 같이 쓴다

    before   from 3  |  .  |  .  |  .  |  .  |  1  |
    after    from 3  |  2  |  .  |  .  |  .  |  1  |
                        ^ 여기 한 칸

    O(1) 이다 — 어느 칸을 고칠지 계산으로 알기 때문에 목록을 훑지 않는다.
    리스트 표현이 중복 확인 때문에 O(deg) 를 쓰던 자리가 여기서는 배열 한 번 읽기로 끝난다
```

### 동작 — 조회와 순회

```
hasEdge(0, 3) = matrix[0][3] != NO_EDGE          -> 배열 한 번 읽기. O(1)
weight(0, 3)  = matrix[0][3]                     -> O(1) (없으면 자연히 NO_EDGE 가 나온다)

neighbors(0) : 그 행 전체를 훑어 NO_EDGE 가 아닌 칸의 번호를 모은다 -> O(V)
              to:  0     1     2     3     4
        from 0  |  .  |  4  |  .  |  2  |  .  |
                   x     o     x     o     x
                                        =>   [ 1, 3 ]
    이웃이 0개인 정점이라도 V 칸을 전부 확인해야 한다 (없는 간선까지 헛보게 된다)
    결과 순서는 정점 번호 오름차순이다 — 리스트 표현의 "넣은 순서"와 다르다

같은 그래프, 다른 대가
                        메모리      addEdge / hasEdge / weight    neighbors(v)     전체 순회
    인접 리스트         O(V + E)    O(deg(v))                     O(deg(v))        O(V + E)
    인접 행렬           O(V^2)      O(1)                          O(V)             O(V^2)

    간선이 적은(희소) 그래프를 이웃 따라 훑는 일에는 리스트가,
    "이 둘이 연결됐나"를 무작위로 자주 묻거나 간선이 빽빽하면 행렬이 유리하다.
    같은 Graph 계약을 두 표현으로 구현해 두면 알고리즘 코드는 그대로 두고 표현만 갈아끼울 수 있다
```

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
