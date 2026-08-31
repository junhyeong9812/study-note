# data-structure/13-segment-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — RangeQuery (`src/main/java/com/datastructure/segment/RangeQuery.java`)

- `int size()`
- `void update(int index, long value)`
- `long query(int from, int to)`
- `long get(int index)`

## 구현 — SegmentTree (`src/main/java/com/datastructure/segment/SegmentTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
SegmentTree (n = 8, values = [3,1,4,1,5,9,2,6], combine = 합)
+---------------------------------------------------------------+
| n = 8              (원소 개수)                                 |
| values ----+       (원본 값 배열, 0-base)                      |
| tree   ----|--+    (구간마다 combine 해둔 값, 노드 번호는 1-base) |
+------------|--|-----------------------------------------------+
             v
 values idx    0     1     2     3     4     5     6     7
            +-----+-----+-----+-----+-----+-----+-----+-----+
            |  3  |  1  |  4  |  1  |  5  |  9  |  2  |  6  |
            +-----+-----+-----+-----+-----+-----+-----+-----+

노드 번호 규약 -- 생성자가 build(1, 0, n-1) 로 시작한다
   뿌리 = tree[1] 이 구간 [0..7] 전체를 맡는다   (tree[0] 은 쓰지 않는다)
   왼쪽 자식  = node*2    -> 구간 [lo..mid]
   오른쪽 자식 = node*2+1 -> 구간 [mid+1..hi]      mid = (lo+hi) >>> 1
   lo == hi 면 리프 -> tree[node] = values[lo]

                               tree[1] = 31
                                 [0..7]
                 +------------------+------------------+
            tree[2] = 9                            tree[3] = 22
              [0..3]                                 [4..7]
        +--------+--------+                    +--------+--------+
   tree[4]=4          tree[5]=5           tree[6]=14         tree[7]=8
    [0..1]             [2..3]               [4..5]             [6..7]
    +--+--+            +--+--+              +--+--+            +--+--+
 t[8]=3  t[9]=1    t[10]=4 t[11]=1     t[12]=5 t[13]=9    t[14]=2 t[15]=6
  [0]      [1]       [2]     [3]         [4]     [5]        [6]     [7]

부모 값 = combine(왼쪽 자식, 오른쪽 자식).  31 = 9 + 22,  22 = 14 + 8
리프에만 원소 하나가 들어가고, 위로 갈수록 넓은 구간의 답이 미리 접혀 있다.
```

```
같은 트리를 배열 한 줄로 편 모습 (n = 8 은 2의 거듭제곱이라 1..15 가 빈틈없이 찬다)

 tree idx    0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
          +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
          |  - | 31 |  9 | 22 |  4 |  5 | 14 |  8 |  3 |  1 |  4 |  1 |  5 |  9 |  2 |  6 |
          +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
          ^    ^    ^---------^-------------------^---------------------------------------^
        안 씀  뿌리    깊이 1        깊이 2                     깊이 3 = 리프 8칸
                      (2칸)         (4칸)                        (8칸)

깊이 d 의 노드가 배열의 [2^d .. 2^(d+1)-1] 구간에 통째로 놓인다.
부모와 자식이 번호 계산만으로 오간다 -> 포인터도, 노드 객체도 필요 없다.
   자식 = node*2, node*2+1        부모 = node/2
tree[0] 을 비워두는 이유: 0*2 == 0 이라 이 공식이 0 에서 무너진다.
```

```
왜 tree 크기가 4*n 인가 -- n 이 2의 거듭제곱이 아니면 번호가 듬성듬성 커진다.

n = 6 의 실제 배치 (mid = (lo+hi) >>> 1 로 쪼갠 결과)

                        tree[1] [0..5]
                +-------------+-------------+
           tree[2] [0..2]              tree[3] [3..5]
          +------+------+             +------+------+
     tree[4]        tree[5]      tree[6]         tree[7]
      [0..1]          [2]         [3..4]           [5]
     +---+---+                   +---+---+
  t[8]     t[9]              t[12]     t[13]
   [0]      [1]                [3]       [4]
                    (tree[5], tree[7] 은 원소 1개짜리라 자식이 없다
                     -> 그 아래 번호 10, 11, 14, 15 가 통째로 빈다)

 tree idx    0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
          +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
          | -  | *  | *  | *  | *  | *  | *  | *  | *  | *  | .  | .  | *  | *  | .  | .  |
          +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
                                                            ^---------^
                                                            10, 11 은 빈 칸
                                                            (16..23 도 마찬가지)

  쓰는 최대 번호가 13 인데 2*n = 12 다 -> 2n 짜리 배열이면 넘친다.
  4*n 이면 어떤 n 에서도 넘치지 않는다 (마지막 단이 한 층 더 내려가도 감당되는 크기).
  대가 = 절반 넘게 빈 칸으로 버린다. 공간을 버려 인덱스 계산을 공짜로 얻은 것이다.
  실제 노드 개수는 2n-1 개 안쪽 -> build 는 O(n), 트리 높이는 O(log n)
```

### 동작 — 갱신

```
update(5, 7) : values[5] 를 9 -> 7 로 바꾼다

[1] 뿌리에서 리프까지 한 줄로 내려간다 (index <= mid 면 왼쪽, 아니면 오른쪽)
      node 1  [0..7]  mid=3  ->  5 >  3  ->  오른쪽 node*2+1 = 3
      node 3  [4..7]  mid=5  ->  5 <= 5  ->  왼쪽   node*2   = 6
      node 6  [4..5]  mid=4  ->  5 >  4  ->  오른쪽 node*2+1 = 13
      node 13 [5..5]  lo == hi 리프  ->  tree[13] = 7 대입

[2] 재귀에서 빠져나오며 combine 을 다시 한다 (<== 가 다시 계산되는 노드)

          before                                     after
        tree[1] = 31                               tree[1] = 29  <== 9 + 20
       /            \                             /            \
  tree[2]=9      tree[3]=22          ->      tree[2]=9      tree[3]=20  <== 12 + 8
                  /       \                                  /       \
            tree[6]=14   t[7]=8                        tree[6]=12   t[7]=8  <== 5 + 7
             /       \                                  /       \
        t[12]=5   tree[13]=9                       t[12]=5   tree[13]=7  <== 대입

건드리는 노드 = 뿌리에서 리프까지의 한 줄 = 트리 높이 = O(log n)
형제(t[2], t[7], t[12])는 값이 그대로라 다시 계산할 필요가 없다 -- 읽기만 한다.

values[index] 도 같이 갱신한다. tree 에는 combine 결과만 남아서
원래 값을 되돌려 읽을 수 없기 때문 (get(index) 는 values 를 본다 -> O(1)).
```

### 동작 — 조회

```
query(2, 6) : 구간 [2..6]. 노드마다 세 갈래로 갈린다.

  [1] 무교차   to < lo || hi < from     -> identity() 를 돌려주고 더 안 내려간다
  [2] 완전포함 from <= lo && hi <= to   -> tree[node] 를 통째로 쓰고 멈춘다
  [3] 부분겹침 그 밖                    -> 양쪽 자식으로 쪼개고 둘을 combine

                          node1 [0..7]  [3] 부분겹침 -> 쪼갠다
                +-----------------------+-----------------------+
        node2 [0..3]  [3] 쪼갬                        node3 [4..7]  [3] 쪼갬
      +---------+---------+                        +---------+---------+
 node4 [0..1]        node5 [2..3]            node6 [4..5]        node7 [6..7]
 [1] 무교차          [2] 완전포함             [2] 완전포함         [3] 쪼갬
 identity 반환       tree[5] = 5 사용         tree[6] = 14 사용    +-----+-----+
 (자식 안 봄)        (자식 안 봄)              (자식 안 봄)        |           |
                                                        node14 [6..6]  node15 [7..7]
                                                        [2] 완전포함    [1] 무교차
                                                        tree[14] = 2   identity

  결과 = combine(5, 14, 2) = 5 + 14 + 2 = 21
```

```
 values idx    0     1     2     3     4     5     6     7
            +-----+-----+-----+-----+-----+-----+-----+-----+
            |  3  |  1  |  4  |  1  |  5  |  9  |  2  |  6  |
            +-----+-----+-----+-----+-----+-----+-----+-----+
                        ^-----------^-----------^-----^
                          node5=5      node6=14  n14=2      -> 5 + 14 + 2 = 21

원소 5개를 하나씩 더하지 않고, 이미 접혀 있는 덩어리 3개로 덮었다.
어느 깊이에서든 "쪼개야 하는" 노드는 구간의 왼쪽 끝과 오른쪽 끝 각각 1개뿐이다
(가운데 노드는 통째로 포함되거나 통째로 벗어난다)
-> 깊이마다 상수 개, 깊이는 log n 단 -> 방문 노드 O(log n)

identity() 의 뜻 = 무교차 가지에서 돌려줘도 결과를 바꾸지 않는 값 (combine 의 항등원)
   합이면 0, 최솟값이면 Long.MAX_VALUE
   그래서 from > to 인 빈 구간도 identity() 하나로 답이 된다.
```

### `필드`

- `int n` 역할:
- `long[] tree` 역할:
- `long[] values` 역할:

### `protected SegmentTree(long[] initial)`

- 하는 일:
- 논리:
- 비용(왜):

### `protected abstract long combine(long a, long b)`

- 하는 일:
- 논리:

### `protected abstract long identity()`

- 하는 일:
- 논리:

### `private void build(int node, int lo, int hi)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public void update(int index, long value)` / `private void update(int node, int lo, int hi, int index, long value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public long query(int from, int to)` / `private long query(int node, int lo, int hi, int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public long get(int index)`

- 하는 일:
- 논리:
- 비용(왜):

### `public int size()`

- 하는 일:
- 비용(왜):

## 구현 — SumSegmentTree (`src/main/java/com/datastructure/segment/SumSegmentTree.java`)

### `protected long combine(long a, long b)` (TODO)

- 하는 일:
- 논리:

### `protected long identity()` (TODO)

- 하는 일:
- 논리:

## 구현 — MinSegmentTree (`src/main/java/com/datastructure/segment/MinSegmentTree.java`)

### `protected long combine(long a, long b)` (TODO)

- 하는 일:
- 논리:

### `protected long identity()` (TODO)

- 하는 일:
- 논리:

## 구현 — MinMaxSegmentTree (`src/main/java/com/datastructure/segment/MinMaxSegmentTree.java`)

### 구조

```
SegmentTree 와 다른 점은 딱 하나 -- 노드 한 칸에 값이 두 개다.

  SegmentTree            long[] tree        노드 = 스칼라 1개
  MinMaxSegmentTree      MinMax[] tree      노드 = record MinMax(min, max)

노드 번호 규약(1-base, node*2 / node*2+1)과 4*n 크기는 그대로다.
values = [3,1,4,1,5,9,2,6]

                           tree[1] = (min 1, max 9)
                                   [0..7]
                 +-------------------+-------------------+
        tree[2] = (1, 4)                          tree[3] = (2, 9)
             [0..3]                                    [4..7]
        +--------+--------+                     +--------+--------+
  tree[4]=(1,3)     tree[5]=(1,4)        tree[6]=(5,9)      tree[7]=(2,6)
    [0..1]             [2..3]               [4..5]             [6..7]

  merge(a, b) = (min(a.min, b.min), max(a.max, b.max))
  IDENTITY    = (Long.MAX_VALUE, Long.MIN_VALUE)   <- 어느 쪽과 merge 해도 상대가 이긴다

한 번 훑어 두 답을 같이 얻는다. min 트리 + max 트리를 따로 두는 것과 답은 같지만
탐색 경로를 한 번만 밟고 캐시도 한 번만 건드린다.
값이 record 라 tree 는 객체 배열 -- long[] 처럼 한 덩어리로 붙어 있지 않다(참조 한 번 더).
```

### `필드`

- `int n` 역할:
- `MinMax[] tree` 역할:
- `long[] values` 역할:
- `record MinMax(long min, long max)` / `MinMax.IDENTITY` 역할:

### `MinMax merge(MinMax other)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public MinMaxSegmentTree(long[] initial)`

- 하는 일:
- 논리:
- 비용(왜):

### `public void update(int index, long value)`

- 하는 일:
- 논리:
- 비용(왜):

### `public MinMax query(int from, int to)` / `private MinMax query(int node, int lo, int hi, int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public int size()`

- 하는 일:
- 비용(왜):

## 구현 — GenericSegmentTree (`src/main/java/com/datastructure/segment/GenericSegmentTree.java`)

### 구조

```
SegmentTree 와 다른 점 -- 값의 타입과 combine 을 "상속"이 아니라 "인자"로 받는다.

  SegmentTree                     GenericSegmentTree<T>
  +---------------------+         +----------------------------------+
  | long[] tree         |         | Object[] tree     (T 를 담는다)   |
  | long[] values       |         | Object[] values                  |
  | combine() 추상 메서드 |         | BinaryOperator<T> combine  <- 필드 |
  | identity() 추상 메서드|         | T identity                 <- 필드 |
  +---------------------+         +----------------------------------+
   하위 클래스를 만들어야           new GenericSegmentTree<>(list, "", String::concat)
   연산이 정해진다                  처럼 만들 때 정해진다

노드 번호 규약(build(1, 0, n-1), 자식 = node*2 / node*2+1, 크기 4*n)은 완전히 같다.
바뀌는 것은 칸에 무엇이 들어가는가뿐이다.

           long[] tree                       Object[] tree
        +----+----+----+---+                +-----+-----+-----+---+
        | 31 |  9 | 22 |...|                | ref | ref | ref |...|
        +----+----+----+---+                +--|--+--|--+--|--+---+
         값이 배열 안에 그대로                    v     v     v
         (연속 메모리, 박싱 없음)              "abc" "ab"  "c"   힙에 흩어진 객체

대가: 원소마다 객체 참조 한 번 더 + 제네릭 소거 때문에 Object[] 로 두고 캐스팅한다.
얻는 것: 문자열 이어붙이기, 행렬 곱처럼 long 으로 못 접는 모노이드도 그대로 올릴 수 있다.
```

### `필드`

- `int n` 역할:
- `Object[] tree` 역할:
- `Object[] values` 역할:
- `T identity` 역할:
- `BinaryOperator<T> combine` 역할:

### `public GenericSegmentTree(List<T> initial, T identity, BinaryOperator<T> combine)`

- 하는 일:
- 논리:
- 비용(왜):

### `public void update(int index, T value)`

- 하는 일:
- 논리:
- 비용(왜):

### `public T query(int from, int to)` / `private T query(int node, int lo, int hi, int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public T get(int index)`

- 하는 일:
- 비용(왜):

### `public int size()`

- 하는 일:
- 비용(왜):

### `public List<T> toList()`

- 하는 일:
- 비용(왜):

## 구현 — LazySegmentTree (`src/main/java/com/datastructure/segment/LazySegmentTree.java`)

### 구조

```
LazySegmentTree (n = 4, initial = [1,2,3,4], 연산 = 구간 더하기 / 구간 합)
+-----------------------------------------------------------------+
| n = 4                                                           |
| tree ---+   (그 노드 구간의 합. 노드 번호 1-base, 크기 4*n)        |
| lazy ---|-+ (자식에게 아직 안 내려간 "구간 전체에 더할 값", 크기 4*n) |
+---------|-|-----------------------------------------------------+
          v v
                        tree[1] = 10   lazy[1] = 0
                            [0..3]
                 +------------+------------+
          tree[2] = 3                  tree[3] = 7
          lazy[2] = 0                  lazy[3] = 0
            [0..1]                       [2..3]
        +------+------+              +------+------+
   tree[4]=1     tree[5]=2      tree[6]=3      tree[7]=4
     [0]           [1]            [2]            [3]

lazy 의 규약 (apply 를 읽으면 정확히 이것이다)
   apply(node, lo, hi, delta):
       tree[node] += delta * (hi - lo + 1)   <- 이 노드 값에는 "이미" 반영
       lazy[node] += delta                   <- 자식들에게는 "아직" 안 내려감

   즉 lazy[node] != 0 은 "내 값은 맞다. 내 자식들 값이 그만큼 뒤처져 있다" 는 뜻이다.
   그래서 tree[node] 를 읽는 데는 push 가 필요 없고,
   자식으로 내려가기 직전에만 push 하면 된다.
```

### 동작 — 구간 더하기

```
rangeAdd(0, 2, +5) : 구간 [0..2] 의 모든 원소에 5 를 더한다

  node1 [0..3] : 부분겹침 -> push(1) (lazy 0, 할 일 없음) 후 쪼갠다
  node2 [0..1] : 완전포함 -> apply(2, 0, 1, +5) 하고 멈춘다. 자식 4, 5 는 건드리지 않는다
  node3 [2..3] : 부분겹침 -> push(3) 후 쪼갠다
     node6 [2..2] : 완전포함 -> apply(6, 2, 2, +5)
     node7 [3..3] : 무교차   -> 그냥 반환
  올라오며 tree[3] = tree[6] + tree[7],  tree[1] = tree[2] + tree[3]

        before                                    after
   tree[1]=10 lazy=0                        tree[1]=25 lazy=0
        [0..3]                                   [0..3]
      /        \                 ->            /        \
 tree[2]=3   tree[3]=7                   tree[2]=13   tree[3]=12
 lazy[2]=0   lazy[3]=0                   lazy[2]=5    lazy[3]=0
   /    \      /    \                      /    \       /    \
 t[4]=1 t[5]=2 t[6]=3 t[7]=4          t[4]=1 t[5]=2  t[6]=8  t[7]=4
                                       lazy=0 lazy=0  lazy[6]=5
                                       ^^^^^^^^^^^^^
                                       손대지 않았다 -- 값이 낡았지만
                                       lazy[2]=5 가 그 사실을 기억한다

 tree[2] = 3 + 5*2 = 13   (구간 폭 2 를 곱한다 -- 합이라서)
 tree[6] = 3 + 5*1 = 8

건드린 노드 = 구간을 덮는 O(log n) 개 + 그 위 경로. 원소가 몇 개든 O(log n).
(lazy 가 없으면 [0..2] 의 원소 3개를 각각 update 해야 한다 -> O(k log n))
```

### 동작 — 미룬 값 내리기

```
push(node, lo, hi) : lazy[node] 를 두 자식에게 apply 하고 자기 lazy 를 0 으로

이어서 rangeSum(1, 1) 을 부르면 node2 에서 자식으로 내려가야 하므로 push(2) 가 일어난다

        before push(2)                            after push(2)
     tree[2]=13  lazy[2]=5                     tree[2]=13  lazy[2]=0  <- 비웠다
        [0..1]                                     [0..1]
      /        \                  ->             /        \
 t[4]=1        t[5]=2                      t[4]=6         t[5]=7
 lazy[4]=0     lazy[5]=0                   lazy[4]=5      lazy[5]=5
 (낡은 값)     (낡은 값)                    1 + 5*1        2 + 5*1

  tree[2] = 13 은 그대로다. push 는 자식만 고친다
  (부모 값에는 이미 반영돼 있었으니까 -- 이것이 lazy 규약의 핵심)

  리프 4, 5 에도 lazy 가 5 로 남지만 내려보낼 자식이 없으니 아무 일도 하지 않는다.

push 를 하는 자리 = 자식으로 내려가기 직전 딱 두 곳 (rangeAdd 의 부분겹침, rangeSum 의 부분겹침)
-> 한 번의 질의에서 push 횟수도 경로 길이만큼 = O(log n)

읽기(rangeSum)가 쓰기(push)를 한다. "조회인데 상태가 바뀐다" 가 이 구조의 특징이다.
```

### `필드`

- `int n` 역할:
- `long[] tree` 역할:
- `long[] lazy` 역할:

### `public LazySegmentTree(long[] initial)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void push(int node, int lo, int hi)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void apply(int node, int lo, int hi, long delta)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public void rangeAdd(int from, int to, long delta)` / `private void rangeAdd(int node, int lo, int hi, int from, int to, long delta)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public long rangeSum(int from, int to)` / `private long rangeSum(int node, int lo, int hi, int from, int to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public long get(int index)`

- 하는 일:
- 논리:
- 비용(왜):

### `public int size()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| SumSegmentTree / MinSegmentTree (상속) | | | |
| MinMaxSegmentTree (묶음 값) | | | |
| GenericSegmentTree (인자로 주입) | | | |
| LazySegmentTree (미루기) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/13-segment-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/13-segment-tree/src/main/java/com/datastructure/segment/`
- 테스트: `/home/jun/project/myway/data-structure/13-segment-tree/src/test/java/com/datastructure/segment/`
- 정답 구현: `/home/jun/project/myway/data-structure/13-segment-tree/impl/`
