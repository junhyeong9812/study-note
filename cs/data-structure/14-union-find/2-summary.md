# data-structure/14-union-find — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — UnionFind (`src/main/java/com/datastructure/unionfind/UnionFind.java`)

- `int find(int x)`
- `boolean union(int x, int y)`
- `boolean connected(int x, int y)`
- `int componentCount()`
- `int size()`
- `int sizeOf(int x)`

## 구현 — ArrayUnionFind (`src/main/java/com/datastructure/unionfind/ArrayUnionFind.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `int[] parent` 역할:
- `int[] treeSize` 역할:
- `boolean unionBySize` 역할:
- `boolean pathCompression` 역할:
- `int components` 역할:

### `public ArrayUnionFind(int n)`

- 하는 일:
- 논리:
- 비용(왜):

### `public int find(int x)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean union(int x, int y)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public int sizeOf(int x)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean connected(int x, int y)`

- 하는 일:
- 논리:
- 비용(왜):

### `public int componentCount()`

- 하는 일:
- 비용(왜):

### `public int size()`

- 하는 일:
- 비용(왜):

## 구현 — MapUnionFind (`src/main/java/com/datastructure/unionfind/MapUnionFind.java`)

### `필드`

- `Map<Integer, Integer> parent` 역할:
- `Map<Integer, Integer> treeSize` 역할:
- `int components` 역할:

### `public boolean add(int x)`

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean contains(int x)`

- 하는 일:
- 비용(왜):

### `public int find(int x)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean union(int x, int y)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean connected(int x, int y)`

- 하는 일:
- 비용(왜):

### `public int componentCount()` / `public int size()` / `public int sizeOf(int x)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — DisjointSet&lt;T&gt; (`src/main/java/com/datastructure/unionfind/DisjointSet.java`)

### `필드`

- `Map<T, Integer> ids` 역할:
- `List<T> items` 역할:
- `MapUnionFind uf` 역할:

### `public boolean add(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public Map<T, List<T>> groups()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean contains(T item)`

- 하는 일:
- 비용(왜):

### `public T find(T item)`

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean union(T a, T b)`

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean connected(T a, T b)`

- 하는 일:
- 논리:
- 비용(왜):

### `public int componentCount()` / `public int size()` / `public int sizeOf(T item)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — WeightedUnionFind (`src/main/java/com/datastructure/unionfind/WeightedUnionFind.java`)

### `필드`

- `int[] parent` 역할:
- `int[] treeSize` 역할:
- `long[] weight` 역할:
- `int components` 역할:

### `public WeightedUnionFind(int n)`

- 하는 일:
- 논리:
- 비용(왜):

### `public int find(int x)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean union(int x, int y, long w)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public long diff(int x, int y)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean connected(int x, int y)`

- 하는 일:
- 비용(왜):

### `public int componentCount()` / `public int size()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ArrayUnionFind (배열) | | | |
| MapUnionFind (맵) | | | |
| DisjointSet&lt;T&gt; (번호 매핑 + 포함) | | | |
| WeightedUnionFind (차이까지) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/14-union-find/README.md`
- 구현: `/home/jun/project/myway/data-structure/14-union-find/src/main/java/com/datastructure/unionfind/`
- 테스트: `/home/jun/project/myway/data-structure/14-union-find/src/test/java/com/datastructure/unionfind/`
- 정답 구현: `/home/jun/project/myway/data-structure/14-union-find/impl/`
