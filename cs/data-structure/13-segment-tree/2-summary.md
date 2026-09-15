# data-structure/13-segment-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**세그먼트 트리 = 소계를 미리 적어 둔 집계판.** 1반부터 8반까지 모은 성금을 자주 물어본다고 하자. 매번 8개 반을 다 더하는 대신, "1·2반 소계", "1~4반 소계", "전체 합"처럼 덩어리 합을 미리 적어 둔다. 그러면 "3반~7반 합은?" 같은 질문도 이미 적힌 소계 두세 개만 더하면 답이 나온다. 한 반의 금액이 바뀌면? 그 반이 속한 소계 몇 칸만 고치면 된다 — 전체를 다시 더하지 않는다.

```text
   전체        +------------- 31 -------------+
   절반 소계   +----- 9 -----+ +----- 22 -----+
   2칸 소계    [ 4 ] [ 5 ]     [ 14 ] [ 8 ]
   원본        3  1   4  1      5  9    2  6
```

세그먼트 트리는 이 집계판과 똑같은 구조다 — 맨 아래가 원본 배열, 위로 갈수록 넓은 구간의 답(합·최솟값 등)이 미리 접혀 있는 이진 트리다. 질문(query)도 수정(update)도 트리 높이만큼만 일하면 되니 둘 다 O(log n)이다.

- *구간 질의(range query)*: "i번째부터 j번째까지의 합(또는 최솟값)은?" 같은, 연속 구간에 대한 질문.
- *O(log n)*: 원소가 2배로 늘어도 일이 1번만 더 늘어나는 속도. 100만 개여도 약 20단이면 된다.

실무·대회에서 "값이 계속 바뀌는 배열에 구간 질문이 쏟아지는" 상황이 이 구조의 자리다 — 주식 구간 최고가, 게임 리더보드 구간 합, 알고리즘 대회의 구간 문제 대부분.

## 문제 — 이 챕터가 시키는 것

비워 둔 TODO 를 채워 세그먼트 트리 다섯 가지를 완성하는 과제다.
뼈대(`SegmentTree`)의 `build`·`update`·`query` 가 본체이고, 나머지 넷은 그 뼈대에 "무엇을 어떻게 접을 것인가"만 바꿔 끼운다.
시작 상태는 테스트 37개 중 35개 실패이며, `cd ~/project/myway/data-structure && ./run.sh 13` 으로 확인한다.

- `SegmentTree` — `build`, `update`, `query` 3개 (재귀 본체. 나머지 구현이 전부 여기에 의존한다)
- `SumSegmentTree` / `MinSegmentTree` — 각각 `combine`, `identity` 2개씩 (뼈대는 하나, 결합 함수와 항등원만 다르다)
- `MinMaxSegmentTree` — `merge`, `query` 2개 (접어 넣는 값이 스칼라일 필요가 없다는 것을 보여준다)
- `GenericSegmentTree` — `query` 1개 (같은 추상화를 상속 대신 생성자 인자로 받는다)
- `LazySegmentTree` — `push`, `apply`, `rangeAdd`, `rangeSum` 4개 (구간 전체 갱신을 O(log n)으로. 제일 어렵다)

README 가 특히 생각해 보라고 짚은 것 — `query` 세 경우의 분기, `update` 가 돌아오는 길에 할 일, 최소 트리의 항등원이 0 이면 안 되는 이유, 평균처럼 결합법칙이 없는 연산에 무엇을 같이 들고 다닐지, 상속이냐 인자냐, 미루기의 쪽지를 언제 누구에게 넘길지.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

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

- *리프(leaf)*: 트리의 맨 아래, 자식이 없는 노드. 여기에만 원소 하나가 그대로 들어간다.
- *combine*: 두 구간의 답을 하나로 합치는 연산. 합 트리면 `+`, 최솟값 트리면 `min`.
- *0-base / 1-base*: 번호를 0부터 세나 1부터 세나. 원본 배열은 0부터, 트리 노드는 1부터 센다.

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

구조 그림 세 장이 말한 것을 정리하면 —

1. 트리를 노드 객체가 아니라 배열 한 줄에 편다. 부모↔자식은 번호 계산(×2, ×2+1, ÷2)만으로 오간다 — 포인터(다른 노드 위치를 가리키는 화살표)가 필요 없다.
2. `tree[0]` 은 안 쓴다 — 0×2=0 이라 번호 공식이 0에서 무너지기 때문이다.
3. 배열 크기를 4n으로 넉넉히 잡는다 — n이 2의 거듭제곱이 아니면 번호가 듬성듬성 커져 2n으로는 넘친다. 공간을 버리고 계산의 단순함을 산다.

### 동작 — 갱신

**언제 쓰나**: 원소 하나의 값이 바뀌었을 때. 그 원소를 포함하는 소계들만 다시 계산한다.

- *재귀(recursion)*: 함수가 더 작은 범위에 대해 자기 자신을 다시 부르는 방식. 내려갈 때 좁혀 가고, 돌아 나오며 결과를 합친다.

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

그림에서 일어난 일을 풀면 —

1. 뿌리에서 출발해 "바꿀 자리가 왼쪽 절반인가 오른쪽 절반인가"만 보며 리프까지 한 줄로 내려간다.
2. 리프에 새 값을 대입한다.
3. 재귀에서 돌아 나오면서, 지나온 경로 위의 부모들만 자식 둘을 다시 combine 한다. 경로 밖의 형제들은 값이 안 변했으니 읽기만 한다.

**비용**: 건드리는 노드 = 뿌리→리프 한 줄 = 트리 높이 = O(log n).

### 동작 — 조회

**언제 쓰나**: "구간 [from..to] 의 합(또는 최솟값)은?" 이라는 질문에 답할 때.

- *항등원(identity)*: 그 연산에서 "더해도 결과가 안 변하는 값". 합이면 0, 최솟값이면 무한대(Long.MAX_VALUE).

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

그림에서 일어난 일을 풀면 —

1. 각 노드는 자기 담당 구간과 질문 구간을 비교해 셋 중 하나다: 전혀 안 겹침(항등원 반환, 끝) / 통째로 포함(내 소계를 그대로 쓰고 끝) / 걸쳐 있음(자식 둘로 쪼개서 다시 물음).
2. 원소 5개짜리 질문 [2..6] 이 "이미 접혀 있는 덩어리 3개"(node5=5, node6=14, node14=2)로 덮였다 — 하나씩 더하지 않았다.
3. 어느 깊이에서든 "쪼개야 하는" 노드는 구간 양 끝의 각 1개뿐이다(가운데는 통째로 포함되거나 통째로 벗어난다).

**비용**: 깊이마다 상수 개 × 깊이 log n = 방문 노드 O(log n).

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

- *record*: 자바에서 "값 몇 개를 묶은 작은 상자"를 한 줄로 정의하는 문법. 여기서는 (min, max) 쌍.
- *캐시(cache)*: CPU 가까이 있는 아주 빠른 임시 메모리. 붙어 있는 데이터를 한 번에 끌어오므로, 같은 경로를 두 번 밟는 것보다 한 번 밟는 쪽이 유리하다.

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

- *추상 메서드 / 상속*: 부모 클래스가 "이 메서드는 자식이 채워라"라고 비워 두는 것 / 그걸 채우는 자식 클래스를 만드는 것. SumSegmentTree 가 combine 을 `+` 로 채운다.
- *BinaryOperator\<T\>*: "T 두 개를 받아 T 하나를 돌려주는 함수"를 값처럼 들고 다니는 자바 타입. 상속 대신 생성자 인자로 연산을 주입한다.
- *제네릭 소거(type erasure)*: 자바 제네릭의 타입 정보 T 가 컴파일 후 지워지는 것. 그래서 `new T[]` 를 못 만들고 Object[] 에 담아 캐스팅한다.
- *박싱(boxing)*: long 같은 원시값을 Long 객체로 감싸는 것. 객체가 되면 메모리에 흩어져 참조를 한 번 더 따라가야 한다.
- *모노이드(monoid)*: "결합법칙이 성립하는 연산 + 항등원" 한 쌍. (합, 0), (min, +∞), (문자열 잇기, "") 전부 모노이드라 세그먼트 트리에 올릴 수 있다.

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

"구간 [0..2] 전체에 5씩 더해라" 같은 **구간 수정**이 오면, 보통 트리로는 원소마다 update 를 불러야 한다. 게으른(lazy) 트리는 "나중에 해도 되는 일은 쪽지로 남겨 두고 미룬다" — 방학 숙제를 몰아서 하되, 어디까지 안 했는지는 정확히 적어 두는 방식이다.

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

**언제 쓰나**: 연속 구간의 모든 원소에 같은 값을 더할 때. 원소 수가 몇이든 O(log n)에 끝내는 것이 목표다.

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

그림에서 일어난 일을 풀면 —

1. 조회 때와 같은 세 갈래 판정으로 내려간다. 통째로 포함된 노드(node2)에서는 자기 값만 고치고(폭×5), "자식들 몫 5"는 lazy 쪽지에 적은 뒤 멈춘다 — 자식 4, 5는 손대지 않는다.
2. 그래서 t[4], t[5]의 값은 낡았지만, lazy[2]=5 가 "얘네가 5씩 뒤처져 있다"는 사실을 기억한다.
3. 올라오면서 경로 위의 부모들은 자식 합으로 다시 계산한다.

**비용**: 원소가 몇 개든 건드리는 노드는 O(log n)개.

### 동작 — 미룬 값 내리기

**언제 쓰나**: lazy 쪽지가 남아 있는 노드의 자식으로 내려가야 하는 순간 — 그 직전에 딱 한 번 쪽지를 자식에게 넘긴다(push).

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

그림에서 일어난 일을 풀면 —

1. rangeSum(1,1) 이 node2 의 자식으로 내려가려는 순간, 미뤄 둔 쪽지(lazy[2]=5)를 두 자식에게 적용하고 자기 쪽지는 비운다.
2. 부모 tree[2]=13 은 그대로다 — 부모 값에는 이미 반영돼 있었다는 것이 lazy 규약의 핵심이다. push 는 자식만 고친다.
3. 리프에 남은 lazy 는 내려보낼 자식이 없으니 무해하다.

**비용**: 한 번의 질의에서 push 는 경로 길이만큼 = O(log n).

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

## 용어 풀이

본문에 등장한 자리에서 이미 푼 용어를 포함해, 이 문서의 전문용어를 한곳에 모았다.

- **구간 질의(range query)**: 배열의 연속 구간에 대한 질문("i~j번째의 합/최솟값은?").
- **리프(leaf)**: 트리 맨 아래, 자식 없는 노드. 원소 하나가 그대로 들어간다.
- **뿌리(root)**: 트리 맨 위 노드. 여기서는 tree[1], 전체 구간을 맡는다.
- **combine**: 두 구간의 답을 하나로 합치는 연산(합이면 `+`, 최솟값이면 `min`).
- **항등원(identity)**: 그 연산에서 더해도 결과가 안 변하는 값. 합이면 0, min이면 Long.MAX_VALUE. 무교차 가지의 반환값.
- **모노이드(monoid)**: 결합법칙이 성립하는 연산 + 항등원의 쌍. 이 조건만 맞으면 어떤 연산이든 세그먼트 트리에 올릴 수 있다.
- **재귀(recursion)**: 함수가 더 작은 범위로 자기 자신을 다시 부르는 방식.
- **0-base / 1-base**: 번호를 0부터/1부터 세는 방식. values 는 0-base, tree 노드는 1-base.
- **`>>> 1`**: 비트를 오른쪽으로 한 칸 미는 연산 = 2로 나누기. mid 계산에 쓴다.
- **포인터/참조**: 다른 데이터가 메모리 어디에 있는지 가리키는 화살표. 배열 트리는 번호 계산으로 대신해 이것이 필요 없다.
- **O(1), O(log n), O(n)**: 연산 횟수가 어떻게 늘어나는지의 표기. 상수 / 트리 높이만큼 / 원소 수에 비례.
- **record**: 값 몇 개를 묶은 작은 상자를 한 줄로 정의하는 자바 문법. MinMax(min, max).
- **캐시 (지역성)**: CPU 옆의 빠른 임시 메모리. 붙어 있는 데이터를 한 번에 끌어오므로, 연속 배열(long[])이 흩어진 객체보다 빠르다.
- **추상 메서드 / 상속**: 부모가 비워 둔 메서드 / 자식 클래스가 그것을 채우는 것.
- **BinaryOperator\<T\>**: "T 둘을 받아 T 하나를 돌려주는 함수"를 값으로 들고 다니는 타입. 연산을 인자로 주입할 때 쓴다.
- **제네릭 소거(type erasure)**: 자바 제네릭의 타입 정보가 컴파일 후 지워지는 것. Object[] + 캐스팅이 필요한 이유.
- **박싱(boxing)**: 원시값(long)을 객체(Long)로 감싸는 것. 메모리가 흩어지는 비용이 따라온다.
- **lazy(게으른 전파)**: 구간 수정을 자식까지 즉시 내리지 않고 "자식들이 얼마나 뒤처졌는지" 쪽지(lazy 배열)로 남겨 두는 기법.
- **push**: 자식으로 내려가기 직전에 그 쪽지를 자식에게 적용하고 비우는 동작.
- **apply**: 한 노드에 "구간 전체에 delta 더하기"를 반영하는 동작 — 내 값은 즉시 고치고(폭×delta), 자식 몫은 lazy 에 적는다.
