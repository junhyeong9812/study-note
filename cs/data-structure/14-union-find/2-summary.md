# data-structure/14-union-find — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**유니온-파인드 = 팀 대표 따라가기.** 반 아이들이 여러 팀으로 나뉘어 있는데, 각자 "내가 따르는 사람" 한 명만 기억한다. 따라가다 보면 팀의 최종 대표가 나온다. "너희 둘 같은 팀이야?"는 각자 대표를 따라 올라가 같은 사람이 나오는지만 보면 되고(find), 두 팀을 합칠 때는 한 팀의 대표가 다른 팀 대표를 따르게만 하면 된다(union) — 팀원 전체 명단을 고칠 필요가 없다.

```text
   팀A       대표 0            팀B      대표 4
            /    \                      |
           1      2                     5
   "1과 5는 같은 팀?"  1->0,  5->4,  0 != 4  ->  다른 팀

   합치기: 4가 0을 따르게 한다     0
                                / | \
                               1  2  4
                                     |
                                     5     -> 이제 모두 한 팀
```

유니온-파인드는 이 방식과 똑같은 구조다 — "내가 따르는 사람"이 parent 배열 한 칸이고, 대표(뿌리)는 자기 자신을 가리킨다. 여기에 요령 두 개(따라 올라간 김에 모두 대표 직속으로 바꿔 달기 = 경로 압축, 작은 팀을 큰 팀 밑에 넣기 = union by size)를 더하면 연산 한 번이 사실상 상수 시간이 된다.

실무·알고리즘에서 "같은 그룹인지 빠르게 판정"이 필요한 곳마다 쓰인다 — 네트워크에서 두 컴퓨터가 연결돼 있는지, 이미지에서 같은 덩어리 픽셀인지, 최소 신장 트리(크루스칼)에서 사이클이 생기는지.

## 문제 — 이 챕터가 시키는 것

08번 그래프에서 "이 둘이 연결돼 있나"는 BFS 로 O(V+E) 에 답했지만, 간선이 하나씩 들어오면 매번 다시 돌려야 한다.\
그 질문에 증분적으로, 거의 O(1) 에 답하는 구조를 직접 만든다 — 대신 "경로를 모른다"와 "쪼갤 수 없다"를 포기한다.\
`UnionFindContractTest.java` 를 따라 친 뒤 TODO 10개를 채우는 것이 과제다(처음 돌리면 52개 중 49개가 실패한다).

- `ArrayUnionFind` — TODO 3개(`find`, `union`, `sizeOf`).\
  배열 두 개로 트리를 표현한다. 여기가 본체다.
- `MapUnionFind` — TODO 2개(`find`, `union`).\
  같은 알고리즘인데 저장소만 배열에서 맵으로 바뀐다.\
  원소 수를 미리 몰라도 되고 흩어진 아이디도 받는다.
- `DisjointSet<T>` — TODO 2개(`add`, `groups`).\
  아무 타입이나 받도록 번호를 붙여 안쪽 구현에 넘긴다.
- `WeightedUnionFind` — TODO 3개(`find`, `union`, `diff`).\
  연결 여부만이 아니라 값의 **차이**까지 관리한다. 제일 어렵다.
- 생각해볼 것 — 경로 압축 루프의 순서 함정 · 재귀 대신 반복 · `sizeOf` 는 뿌리 것만 정확 · `groups()` 가 O(n) 인 이유 · 배열이냐 맵이냐 · `find` 순서를 틀리면 조용히 틀린다 · 크기로 붙이기 때문에 weight 부호를 두 경우 다 · Integer 캐시 함정.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

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

- *포레스트(forest)*: 트리(나무)가 여러 그루 모인 것. 묶음 하나 = 트리 한 그루, 뿌리 = 그 묶음의 대표.
- *컴포넌트(component)*: 서로 연결된 원소들의 묶음. components 는 지금 묶음이 몇 개인지다.

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

**언제 쓰나**: "x의 대표가 누구인가"를 알아야 하는 모든 순간 — connected/union/sizeOf 전부 find 로 시작한다.

- *경로 압축(path compression)*: 대표를 찾으러 올라간 김에, 지나온 원소들을 전부 대표 직속으로 바꿔 다는 최적화. 다음 find 가 한 걸음이 된다.

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

그림에서 일어난 일을 풀면 —

1. 첫 훑기: x에서 부모를 따라 올라가 뿌리(대표)를 찾는다.
2. 둘째 훑기: 다시 x부터 올라가며 만나는 칸마다 "대표 직속"으로 덮어쓴다. 덮어쓰기 전에 다음 칸을 담아 둬야 길을 안 잃는다.
3. after 그림: 사슬이 납작해졌다 — 다음에 누가 find(0~2) 를 불러도 한 걸음이면 대표가 나온다.

**비용**: 이번 호출은 사슬 길이만큼 들지만, 납작해진 덕을 다음 호출들이 본다.
- *상환(amortized) 비용*: 연산 여러 번의 비용을 평균 낸 값. 한 번 비싸도 그 덕에 다음이 싸지면 평균은 낮다.
- *역아커만 함수 α(n)*: 상상 못 할 만큼 천천히 자라는 함수. 우주의 원자 수만큼 넣어도 5 이하 — 사실상 상수라는 뜻으로 쓴다.

### 동작 — 합치기

**언제 쓰나**: "x와 y는 이제 같은 묶음"이라는 사실이 생겼을 때(간선 추가, 팀 합병).

- *union by size*: 두 묶음을 합칠 때 항상 작은 쪽을 큰 쪽 밑에 매다는 규칙. 트리가 깊어지는 것을 막는다.

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

그림에서 일어난 일을 풀면 —

1. 두 대표를 찾는다. 이미 같은 대표면 할 일이 없다(false).
2. 작은 팀의 대표를 큰 팀의 대표 밑에 매단다 — 그러면 깊어지는 원소가 작은 팀 쪽 소수뿐이다. 반대로 하면 큰 팀 전원이 한 칸씩 깊어진다.
3. "깊이가 1 늘려면 소속 묶음 크기가 최소 2배"이므로, 깊이는 log2(n)을 못 넘는다 — find 의 O(log n) 보장이 여기서 나온다.

**비용**: find 두 번 + 상수 대입. 경로 압축과 합치면 연산당 사실상 상수(α(n)).

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

- *해시맵(hash map)*: 키를 해시 함수로 흩어 담아, 아무 값이나 키로 쓰면서 평균 O(1)에 찾는 저장소. 배열처럼 "0..n-1 연속 번호"일 필요가 없다.

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

- *제네릭 T*: "어떤 타입이든 담을 수 있게" 비워 둔 타입 자리. 문자열이든 객체든 T 에 끼워 쓴다.
- *LinkedHashMap*: 넣은 순서를 기억하는 해시맵.

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

**언제 쓰나**: "x와 y는 같은 묶음이고 값 차이가 w다" 같은 상대적 관계를 다룰 때 — 환율(A는 B의 2배), 위치 차이, 수지 차이 등. find 가 대표를 찾으면서 "대표와의 차이"도 함께 맞춰 둔다.

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

그림에서 일어난 일을 풀면 —

1. weight[x] 는 "부모와의 차이"만 담는다. 뿌리와의 차이가 아니다 — before 의 weight[3]=5 는 "2와의 차이"였다.
2. find(3) 이 재귀로 뿌리까지 올라갔다가 돌아 나오며, 부모 몫이 먼저 뿌리 기준으로 고쳐진 뒤 내 것에 더한다(5+13=18). 순서를 바꾸면 틀린다.
3. 경로 압축으로 3이 뿌리 직속이 되면서, weight[3] 도 "뿌리와의 차이 18"로 함께 바뀌었다 — 차이의 합은 경로를 어떻게 접든 같아서 압축해도 안 틀어진다.

**비용**: ArrayUnionFind 의 find 와 같은 O(α(n)) 상환 — 덧셈 하나가 더 붙을 뿐이다.

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

## 용어 풀이

본문에 등장한 자리에서 이미 푼 용어를 포함해, 이 문서의 전문용어를 한곳에 모았다.

- **유니온-파인드(union-find) / 서로소 집합(disjoint set)**: 겹치지 않는 묶음들을 관리하며 "합치기(union)"와 "대표 찾기(find)"만 빠르게 하는 자료구조.
- **컴포넌트(component)**: 서로 연결된 원소들의 묶음. componentCount 는 묶음 개수.
- **포레스트(forest)**: 트리가 여러 그루 모인 것. 묶음 하나 = 트리 한 그루.
- **뿌리(root)**: 트리 맨 위 = 묶음의 대표. 여기서는 parent[i] == i 인 원소.
- **경로 압축(path compression)**: find 하러 올라간 김에 지나온 원소를 전부 뿌리 직속으로 바꿔 다는 최적화.
- **union by size**: 합칠 때 작은 묶음을 큰 묶음 밑에 매다는 규칙. 깊이가 log2(n)을 못 넘게 한다.
- **상환(amortized) 비용**: 연산 여러 번의 평균 비용. 한 번 비싸도 다음이 싸지면 평균은 낮다.
- **역아커만 함수 α(n)**: 상상 못 할 만큼 천천히 자라는 함수. 현실의 어떤 n에도 5 이하 — "사실상 상수".
- **O(1), O(log n)**: 연산 횟수가 늘어나는 속도의 표기. 상수 / 원소 2배당 1번 추가.
- **해시맵(hash map)**: 아무 값이나 키로 쓰며 평균 O(1)에 찾는 저장소. 배열보다 유연하지만 상수 비용이 크다.
- **LinkedHashMap**: 넣은 순서를 기억하는 해시맵.
- **제네릭 T**: 어떤 타입이든 끼울 수 있게 비워 둔 타입 자리.
- **위임/포함(composition)**: 일을 안에 품은 다른 객체(MapUnionFind)에 넘기는 설계. DisjointSet 이 이 방식이다.
- **가중치(weight)**: 이 구현에서는 "부모와의 값 차이". 절대값이 아니라 상대값이다.
- **간선(edge)**: 그래프에서 두 점을 잇는 선. union 한 번 = 간선 하나 추가로 볼 수 있다.
- **최소 신장 트리 / 크루스칼(Kruskal)**: 모든 점을 최소 비용으로 잇는 간선 고르기 문제 / 그 대표 알고리즘. 사이클 판정에 유니온-파인드를 쓴다.
