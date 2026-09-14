# data-structure/08-graph — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 지하철 노선도.** 역(동그라미)들과 그 사이를 잇는 선로가 있다. 어떤 역끼리는 바로 이어져 있고, 어떤 역은 갈아타며 가야 한다.

**그래프가 바로 이 노선도와 똑같은 구조다.** 역 = 정점, 선로 = 간선.
  - *정점(vertex)*: 그래프의 점 하나. 여기서는 0, 1, 2... 번호로만 부른다.
  - *간선(edge)*: 두 정점을 잇는 연결선. 요금(가중치)이 붙을 수 있다.

- 노선도를 종이에 적는 방법이 두 가지다:
  1. **역마다 "옆 역 목록"을 적는다** (인접 리스트) — 연결이 적으면 종이가 적게 든다.
  2. **모든 역 쌍의 표를 만들어 놓고 이어진 칸에 표시한다** (인접 행렬) — "A와 B 이어져 있어?"를 즉시 답한다.
- 어느 쪽이든 담는 노선도(그래프)는 같다. 종이(메모리)와 질문 속도의 거래만 다르다.
- 실무에서 같은 구조: SNS 친구 관계, 내비게이션 도로망, 빌드 의존성 그래프가 전부 이것이다.

```text
    노선도                        인접 리스트 (역마다 옆 역 목록)
    v0 --- v1                        v0: [v1, v3]
    |       |                        v1: [v0, v2]
    v3     v2                        v2: [v1]
    |                                v3: [v0, v4]
    v4                               v4: [v3]
```

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

**언제 쓰나** — 두 정점을 잇는 연결선을 등록할 때(addEdge). 같은 간선을 또 넣으면 가중치만 바뀐다.

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

**그림에서 일어난 일 (쉽게)**
1. 먼저 v0의 목록을 훑어 "0-3 간선이 벌써 있나" 확인했다 — 있으면 가중치만 고쳐 쓴다.
2. 없어서 **양쪽 목록에 하나씩** 적었다. "v0의 옆 역에 v3", "v3의 옆 역에 v0". 무방향이라 서로의 목록에 적어야 한다.
   - *무방향(undirected)*: 양방향 길. v0→v3으로도 v3→v0으로도 갈 수 있다.
3. 종이에 적은 줄(Edge 객체)은 2개지만 선로(간선)는 1개 — edges는 1만 올린다.

**비용** — 중복 확인 때문에 v0의 목록 길이만큼 = O(deg(0)).
  - *deg (차수, degree)*: 그 정점에 붙어 있는 간선의 개수. "옆 역이 몇 개인가".

### 동작 — 조회와 순회

**언제 쓰나** — "이 둘 이어져 있어?"(hasEdge) / "요금 얼마야?"(weight) / "여기서 갈 수 있는 곳 전부?"(neighbors).

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

**그림에서 일어난 일 (쉽게)**
1. hasEdge/weight: v0의 옆 역 목록을 앞에서부터 하나씩 대조했다. 목록이 길수록 오래 걸린다 — 이 표현의 약점.
2. neighbors: 목록에서 역 번호만 뽑아 돌려줬다. **내 옆 역만 보고 남의 목록은 안 본다** — 그래서 BFS/DFS/다익스트라처럼 "이웃 따라 걷는" 알고리즘이 이 표현을 좋아한다.
   - *BFS/DFS*: 그래프를 도는 두 가지 방법. BFS는 가까운 곳부터 물결처럼, DFS는 한 길로 끝까지 들어갔다 되돌아온다.

**비용** — 전부 그 정점의 목록 길이 = O(deg). 전체 순회는 O(V+E).

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

**언제 쓰나** — 리스트 쪽과 같은 일(addEdge). 다만 목록에 줄을 추가하는 대신 표의 칸에 적는다.

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

**그림에서 일어난 일 (쉽게)**
1. (0, 3) 칸이 비어 있는지(NO_EDGE) 보고, 비어 있었으면 간선 개수를 올렸다.
2. (0, 3) 칸에 2를 적었다. 무방향이라 대칭 칸 (3, 0)에도 같이 적었다 — 표가 대각선 기준 거울처럼 되는 이유.
3. 훑는 게 없다. 어느 칸인지 좌표로 바로 아니까 **표 읽고 쓰기 한 번** = O(1).

### 동작 — 조회와 순회

**언제 쓰나** — 같은 질문(hasEdge/weight/neighbors)을 표에서 답한다. "연결됐나"는 즉답, "이웃 전부"는 한 행 완주.

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

**그림에서 일어난 일 (쉽게)**
1. hasEdge/weight: (0, 3) 칸 하나만 읽으면 끝 = O(1). 리스트가 목록을 훑던 자리가 즉답이 됐다.
2. neighbors(0): 0번 행을 왼쪽부터 끝까지 훑으며 채워진 칸의 번호를 모았다. 이웃이 하나도 없어도 V칸을 다 봐야 한다 = O(V).
3. 거래 정리: 리스트는 "있는 것만" 저장해 메모리 O(V+E), 행렬은 빈칸까지 통째로 잡아 O(V²) 대신 즉답을 얻는다.
   - *희소(sparse)/밀집(dense)*: 가능한 간선 수 대비 실제 간선이 적으면 희소, 빽빽하면 밀집. 희소면 리스트, 밀집이거나 즉답이 잦으면 행렬.

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

## 용어 풀이

- **그래프(graph)**: 점(정점)들과 그 사이 연결(간선)로 관계를 표현하는 자료구조. 노선도·친구 관계·의존성이 전부 그래프다.
- **정점(vertex, V)**: 그래프의 점 하나. 이 구현에서는 0..V-1 정수 번호다.
- **간선(edge, E)**: 두 정점을 잇는 연결선.
- **가중치(weight)**: 간선에 붙는 숫자(거리·요금·비용). 이 구현은 음수를 거부한다(다익스트라가 깨져서).
- **방향/무방향(directed/undirected)**: 일방통행 길 / 양방향 길. 무방향 간선 하나는 리스트 양쪽에 한 줄씩 적힌다.
- **차수(degree, deg)**: 한 정점에 붙은 간선의 개수. "옆 역이 몇 개인가".
- **인접 리스트(adjacency list)**: 정점마다 "내가 닿는 곳 목록"을 들고 있는 표현. 메모리 O(V+E).
- **인접 행렬(adjacency matrix)**: V×V 표의 (from, to) 칸에 가중치를 적는 표현. 메모리 O(V²), 연결 확인 O(1).
- **희소/밀집(sparse/dense)**: 실제 간선이 가능한 수에 비해 적으면 희소, 빽빽하면 밀집.
- **셀프루프(self-loop)**: 자기 자신으로 가는 간선(from == to).
- **NO_EDGE / 센티널(sentinel)**: "간선 없음"을 나타내려고 정해 둔 특별한 값(여기서는 Integer.MAX_VALUE). 0을 쓰면 가중치 0인 진짜 간선과 구분이 안 된다.
- **순회(traversal)**: 그래프의 정점들을 규칙에 따라 빠짐없이 방문하는 것.
- **BFS(너비 우선 탐색)**: 가까운 곳부터 물결처럼 퍼지며 방문. 큐를 쓴다. 간선 수 기준 최단거리를 준다.
- **DFS(깊이 우선 탐색)**: 한 길로 끝까지 들어갔다가 막히면 되돌아 나오는 방문. 스택(또는 재귀)을 쓴다.
- **위상 정렬(topological sort)**: 방향 그래프에서 "모든 화살표가 앞→뒤가 되도록" 정점을 줄 세우는 것. 선수과목·빌드 순서 문제.
- **순환(cycle)**: 출발한 정점으로 되돌아오는 길. 순환이 있으면 위상 정렬이 불가능하다.
- **다익스트라(Dijkstra)**: 가중치 합 기준 최단거리 알고리즘. "지금까지 중 가장 가까운 정점"을 힙(우선순위 큐)으로 반복해 꺼낸다.
- **큐(queue)/스택(stack)**: 먼저 넣은 것이 먼저 나오는 줄 / 나중에 넣은 것이 먼저 나오는 더미. BFS는 큐, DFS는 스택.
- **재귀(recursion)**: 함수가 자기 자신을 부르는 것. DFS를 재귀로 쓰면 호출 스택이 스택 역할을 대신한다.
- **O(1) / O(deg) / O(V) / O(V+E) / O(V²)**: 일의 양 — 한 번 / 그 정점의 이웃 수만큼 / 정점 수만큼 / 정점+간선 전부 한 번씩 / 표 전체.
