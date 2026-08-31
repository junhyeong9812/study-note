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

### 구조

```
ArrayUnionFind (n = 8) -- 배열 하나가 "포레스트(뿌리 여러 개인 숲)"를 표현한다

+-------------------------------------------------------------+
| int[] parent    (parent[i] = i 의 부모. 뿌리는 자기 자신)       |
| int[] treeSize  (그 원소가 뿌리일 때만 뜻이 있는 묶음 크기)      |
| int components  (묶음 개수. union 이 성공할 때마다 1 줄인다)     |
+-------------------------------------------------------------+

루트 표현 규약: parent[i] == i 이면 i 가 뿌리다 (음수나 -1 을 쓰지 않는다)
초기 상태는 전부 혼자 -- parent[i] = i, treeSize[i] = 1, components = n

union(0,1) union(2,3) union(1,3) union(4,5) union(6,7) union(5,7) 을 한 뒤

             0     1     2     3     4     5     6     7
          +-----+-----+-----+-----+-----+-----+-----+-----+
parent    |  0  |  0  |  0  |  2  |  4  |  4  |  4  |  6  |
          +-----+-----+-----+-----+-----+-----+-----+-----+
treeSize  |  4  |  1  |  2  |  1  |  4  |  1  |  2  |  1  |
          +-----+-----+-----+-----+-----+-----+-----+-----+
             ^                       ^     ^
           뿌리 (parent[0]==0)     뿌리   treeSize[2]=2 는 낡은 값이다
                                          (2 는 더 이상 뿌리가 아니다)

같은 것을 그림으로 (위가 부모. 배열이 저장하는 방향은 반대다 -- 자식이 부모를 가리킨다)

        0  (뿌리, treeSize 4)          4  (뿌리, treeSize 4)
      +-+-+                          +-+-+
      |   |                          |   |
      1   2                          5   6
          |                              |
          3                              7

  components = 2.  0 과 4 는 서로 다른 묶음이다.
  "같은 묶음인가?" = 뿌리가 같은가 = find(x) == find(y)
  묶음의 모양(누가 누구 밑인가)에는 의미가 없다. 뿌리가 누구냐만 뜻이 있다.
  sizeOf(x) 는 treeSize[find(x)] 로 읽는다 -- 뿌리 칸만 믿는다.
```

### 동작 — 찾기

```
find(x) : x 가 속한 묶음의 뿌리를 돌려주고, 오는 길을 뿌리에 직접 매단다 (경로 압축)

두 번 훑는다
  [1] parent[root] != root 인 동안 위로 올라가 뿌리를 찾는다
  [2] 다시 x 부터 올라가며 만나는 칸마다 parent[cur] = root 로 덮어쓴다
      (다음 칸을 먼저 next 에 담아둬야 한다 -- 덮어쓰면 길을 잃는다)

최적화 없이 붙이면 이런 사슬이 생긴다 (parent[0]=1, parent[1]=2, parent[2]=3, parent[3]=4)

             0     1     2     3     4
          +-----+-----+-----+-----+-----+              4  (뿌리)
parent    |  1  |  2  |  3  |  4  |  4  |              |
          +-----+-----+-----+-----+-----+              3
                                                       |
                                                       2     find(0) 은 뿌리까지 4걸음
                                                       |
                                                       1
                                                       |
                                                       0

find(0) 을 부른 뒤 (before -> after)

             0     1     2     3     4                 4  (뿌리)
          +-----+-----+-----+-----+-----+           +--+-+-+--+
parent    |  4  |  4  |  4  |  4  |  4  |           |    | |   |
          +-----+-----+-----+-----+-----+           0    1 2   3
   지나온 0, 1, 2 가 전부 뿌리 4 를 직접 가리킨다
   3 은 원래 parent[3] == 4 라 그대로다

이번 find 는 O(사슬 길이)를 냈지만, 그 값을 다음 호출들이 나눠 갖는다.
union by size 와 같이 쓰면 연산당 상환 비용이 거의 상수(역아커만 함수)로 떨어진다.
```

### 동작 — 합치기

```
union(x, y) : 두 뿌리를 찾아 한쪽을 다른 쪽 밑에 매단다

  [1] rx = find(x), ry = find(y)
  [2] rx == ry 면 이미 한 묶음 -> false (아무것도 안 한다)
  [3] treeSize[rx] < treeSize[ry] 면 rx 와 ry 를 맞바꾼다  <- 항상 rx 가 큰 쪽
  [4] parent[ry] = rx ;  treeSize[rx] += treeSize[ry] ;  components--

왜 작은 쪽을 큰 쪽에 매다는가 -- 큰 묶음 {B,c,d,e} 와 작은 묶음 {A} 를 합칠 때

  [나쁨] 큰 쪽을 작은 쪽 밑에            [좋음] 작은 쪽을 큰 쪽 밑에 (코드가 하는 쪽)
   parent[B] = A                        parent[A] = B

        A   <- 새 뿌리                        B   <- 뿌리 그대로
        |                                  +-+-+-+
        B                                  |  |  |
      +-+-+                                c  d  A   <- A 만 깊이 0 -> 1
      |   |                                   |
      c   d                                   e
          |
          e                              c, d, e 의 깊이는 1, 1, 2 그대로
                                         깊어진 원소 = 1개
   c,d 는 1 -> 2, e 는 2 -> 3, B 는 0 -> 1
   깊어진 원소 = 4개. 최대 깊이도 2 -> 3

  어떤 원소의 깊이가 1 늘어나려면 그 원소가 속한 묶음의 크기가 최소 2배가 되어야 한다
  -> 크기는 n 을 못 넘으니 깊이는 log2(n) 을 못 넘는다 -> find 가 O(log n) 보장

  treeSize[ry] 는 지우지 않고 낡은 채로 둔다. 뿌리가 아닌 칸은 아무도 읽지 않는다.
  union 비용 = find 두 번 + 상수 대입.
```

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

### 구조

```
ArrayUnionFind 와 하는 일은 같다. 저장소만 배열 -> 해시맵으로 바뀐다.

  ArrayUnionFind                        MapUnionFind
  +---------------------------+         +-----------------------------------+
  | int[] parent   (길이 n)    |         | Map<Integer,Integer> parent        |
  | int[] treeSize (길이 n)    |         | Map<Integer,Integer> treeSize      |
  | int components            |         | int components                    |
  +---------------------------+         +-----------------------------------+
   0 .. n-1 만 담는다                     아무 int 나 담는다. 미리 크기를 안 정한다

             0     1     2     3                키 ->  7    100   4  ...
          +-----+-----+-----+-----+           +--------------------------+
parent    |  0  |  0  |  2  |  2  |           | 7    -> 7   (뿌리)        |
          +-----+-----+-----+-----+           | 100  -> 7                |
           연속 메모리, 인덱스로 즉시            | 4    -> 4   (뿌리)        |
                                             +--------------------------+
                                              해시로 찾아간다 (평균 O(1), 상수는 더 크다)

바뀌는 규약
  루트 표현은 그대로 parent.get(i) == i
  size() 가 "지금까지 등장한 원소 수" 다 (배열판은 처음부터 n 고정)
  find(x) 가 없는 x 를 만나면 add(x) 로 혼자짜리 묶음을 먼저 만든다
    -> 조회가 상태를 늘린다. 배열판에는 없는 성질이다
  경로 압축은 parent.put(cur, root) 로 같은 모양을 만든다 (묶음 구조 자체는 동일)

쓰는 자리: 원소가 0..n-1 이 아닐 때 (아이디, 좌표를 접은 값, 띄엄띄엄한 번호)
```

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

### 구조

```
DisjointSet<T> 는 union-find 를 새로 만들지 않는다. T 를 번호로 바꿔 MapUnionFind 에 넘긴다.

   사용자가 보는 것                     안에서 도는 것
  +--------------------+              +-----------------------------+
  | union("a", "b")    |   번호 매김   | uf.union(0, 1)              |
  | find("c")   -> "a" |  <-------->  | uf.find(2)  -> 0            |
  +--------------------+              +-----------------------------+

  Map<T,Integer> ids           List<T> items          MapUnionFind uf
  +----------------+           +---+---+---+          (14 장의 그 구조 그대로)
  | "a"  -> 0      |           | 0 | 1 | 2 |
  | "b"  -> 1      |           +---+---+---+
  | "c"  -> 2      |            "a" "b" "c"
  +----------------+            번호 -> 원래 값 (되돌리기용)
   원래 값 -> 번호
   (LinkedHashMap: 넣은 순서 유지)

  add(item) : 없으면 번호 = items.size() 를 새로 주고 items 에 덧붙인다
              -> 번호는 0,1,2,... 로 이어지고 한 번 준 번호는 안 바뀐다
  find(item) = items.get( uf.find( ids.get(item) ) )   -- 번호로 갔다가 값으로 돌아온다

두 겹으로 나눈 이유
  묶기 로직(경로 압축, union by size)은 int 로만 다루는 게 빠르고 단순하다
  T 를 다루는 일(널 검사, 번호 부여, groups() 로 묶음별 목록 만들기)은 이 층이 맡는다
  대가 = 원소 하나마다 해시맵 조회가 한 겹 더 붙는다
```

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

### 구조

```
WeightedUnionFind -- "같은 묶음인가" 에 더해 "값이 얼마나 차이 나는가" 까지 들고 있다

+---------------------------------------------------------------------+
| int[]  parent    (ArrayUnionFind 과 같다. 뿌리는 parent[i] == i)      |
| int[]  treeSize  (union by size 용)                                  |
| long[] weight    (weight[x] = value(x) - value(parent[x]))           |
| int    components                                                   |
+---------------------------------------------------------------------+

핵심 규약: weight 는 절대값이 아니라 "부모와의 차이" 다.
   뿌리는 weight = 0 (자기 자신과의 차이) -- 뿌리 값이 얼마인지는 아무도 모르고, 알 필요도 없다.
   parent[x] 가 뿌리면 weight[x] = value(x) - value(뿌리) 가 된다.
   diff(x, y) = weight[y] - weight[x]  (find 로 둘 다 뿌리 기준으로 맞춘 뒤에 뺀다)
                = (value(y)-value(r)) - (value(x)-value(r)) = value(y) - value(x)

union(0,1,3)  union(2,3,5)  union(1,2,10) 을 차례로 한 뒤
( "value(1) - value(0) = 3", "value(3) - value(2) = 5", "value(2) - value(1) = 10" 이라는 선언 )

             0     1     2     3                       0  (뿌리, weight 0)
          +-----+-----+-----+-----+                   / \
parent    |  0  |  0  |  0  |  2  |             w=3  /   \  w=13
          +-----+-----+-----+-----+                 1     2
weight    |  0  |  3  | 13  |  5  |                        \  w=5
          +-----+-----+-----+-----+                         3
treeSize  |  4  |  1  |  2  |  1  |
          +-----+-----+-----+-----+          value(0)=0 이라 치면 1=3, 2=13, 3=18

  weight[2] = 13 : union 이 d = w + weight[x] - weight[y] = 10 + 3 - 0 = 13 으로 계산했다
       (2 의 뿌리를 0 밑에 매달 때, 두 뿌리 사이의 차이로 환산해 넣는 값)
  weight[3] = 5  : 아직 부모가 2 라서 "2 와의 차이" 다. 뿌리 0 과의 차이가 아니다.
```

### 동작 — 찾기(가중치 누적)

```
find(x) : 뿌리를 찾으면서 weight 를 뿌리 기준으로 다시 접는다

   ArrayUnionFind      : 위로 훑어 뿌리 찾기 -> 다시 훑으며 parent 덮어쓰기 (반복문 2번)
   WeightedUnionFind   : 재귀로 뿌리까지 올라갔다가, 돌아 나오며 weight[x] += weight[p]
                         (부모의 weight 가 먼저 뿌리 기준으로 고쳐진 뒤에 더해야 한다
                          -> 반드시 뒤에서부터. 순서를 바꾸면 값이 틀린다)

find(3) 을 부르면

        before                                     after
             0                                         0
            / \                                    /   |   \
      w=3  /   \  w=13                      w=3  /   w=13   \  w=18
          1     2            ->                 1       2      3
                 \  w=5
                  3                       3 이 이제 뿌리를 직접 가리키고
                                          weight[3] 이 뿌리와의 차이로 바뀌었다
     3 -> 2 -> 0 (두 걸음)

             0     1     2     3                    0     1     2     3
          +-----+-----+-----+-----+              +-----+-----+-----+-----+
parent    |  0  |  0  |  0  |  2  |    ->        |  0  |  0  |  0  |  0  |
          +-----+-----+-----+-----+              +-----+-----+-----+-----+
weight    |  0  |  3  | 13  |  5  |              |  0  |  3  | 13  | 18  |
          +-----+-----+-----+-----+              +-----+-----+-----+-----+
                                ^                                     ^
                     "부모 2 와의 차이 5"              weight[3] += weight[2]
                                                        5 + 13 = 18 (뿌리와의 차이)

  경로가 짧아지는 것은 그대로고, 짧아진 만큼 차이값을 미리 합쳐 둔다.
  그래서 압축을 해도 diff 가 틀어지지 않는다 -- 차이의 "합"은 경로를 어떻게 접든 같다.

  union(x, y, w) 는 이미 한 묶음이면 매달지 않고 weight[y] - weight[x] == w 인지만 본다
  -> 모순된 선언을 false 로 걸러낸다 (여기서 자료구조가 "제약 검사기" 가 된다)
```

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
