# data-structure/25-spatial-index — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SpatialIndex (`src/main/java/com/datastructure/spatial/SpatialIndex.java`)

- `boolean insert(Point2D p)`
- `boolean contains(Point2D p)`
- `int size()`
- `void clear()`
- `default boolean isEmpty()`
- `List<Point2D> rangeSearch(Rectangle area)`
- `Point2D nearest(Point2D target)`
- `List<Point2D> nearestK(Point2D target, int k)`

## 계약 — VisitCounting (`src/main/java/com/datastructure/spatial/VisitCounting.java`)

- `long visits()`
- `void resetVisits()`

## 구현 — Point2D (`src/main/java/com/datastructure/spatial/Point2D.java`)

### 필드
- `x` — 역할:
- `y` — 역할:

### `Point2D(int x, int y)`
- 하는 일:
- 논리:
- 비용(왜):

### `int coordinate(int axis)`
- 하는 일:
- 논리:
- 비용(왜):

### `long squaredDistanceTo(Point2D other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `double distanceTo(Point2D other)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — Rectangle (`src/main/java/com/datastructure/spatial/Rectangle.java`)

### 필드
- `minX` / `minY` — 역할:
- `maxX` / `maxY` — 역할:

### `Rectangle(int minX, int minY, int maxX, int maxY)`
- 하는 일:
- 논리:
- 비용(왜):

### `int min(int axis)` / `int max(int axis)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(Point2D p)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean intersects(Rectangle other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `long squaredDistanceTo(Point2D p)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean canSubdivide()`
- 하는 일:
- 논리:
- 비용(왜):

### `Rectangle[] subdivide()`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — KNearest (`src/main/java/com/datastructure/spatial/KNearest.java`)

### 구조

```
KNearest : 지금까지의 최선 k 개를 담아두는 상자. 안은 최대 힙이다. (k = 3, target = T)

  비교자가 뒤집혀 있어서 T 에서 "가장 먼" 것이 머리로 온다

            +-----------+
            | d = 50    |  <- 머리 (heap.peek()) = 들고 있는 것 중 가장 먼 것
            +-----+-----+
                  |
        +---------+---------+
        |                   |
   +----+----+         +----+----+
   | d = 20  |         | d = 9   |
   +---------+         +---------+

   d = target.squaredDistanceTo(점)  (제곱거리. sqrt 를 안 쓴다)

  offer(candidate)
    [1] heap.size() < k                    -> 그냥 넣는다
    [2] 찼는데 머리보다 가깝다             -> poll() 로 머리를 버리고 넣는다
    [3] 찼는데 머리보다 멀거나 같다        -> 아무것도 안 한다

  radius()
    heap.size() < k  ->  Long.MAX_VALUE   (아직 아무것도 버릴 수 없다 = 가지치기 불가)
    heap.size() == k ->  머리까지의 제곱거리 = "이보다 먼 곳은 볼 필요 없다"는 경계선
    이 값이 KdTree / QuadTree 의 가지치기 반경으로 그대로 쓰인다

  drain() : 힙 내용을 꺼내 target 까지의 거리로 정렬해 돌려준다. O(k log k)
  왜 최대 힙인가 : 자주 하는 질문이 "가장 가까운 게 뭐냐"가 아니라
                   "지금 들고 있는 k 개 중 가장 먼 것보다 가까우냐"이기 때문이다.
                   그 가장 먼 것을 O(1) 에 보려면 머리에 최댓값이 있어야 한다.
```


### 필드
- `target` — 역할:
- `k` — 역할:
- `heap` — 역할:

### `KNearest(Point2D target, int k)`
- 하는 일:
- 논리:
- 비용(왜):

### `void offer(Point2D candidate)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `long radius()`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Point2D> drain()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — NaiveSpatialIndex (`src/main/java/com/datastructure/spatial/NaiveSpatialIndex.java`)

### 구조

```
NaiveSpatialIndex : 공간을 나누지 않는다. 그냥 목록이다. 무슨 질의든 전부 훑는다.

  points (ArrayList)
  +------+------+------+------+------+------+ ... +------+
  |  p0  |  p1  |  p2  |  p3  |  p4  |  p5  |     | pn-1 |
  +------+------+------+------+------+------+ ... +------+
     ^      ^      ^      ^      ^      ^            ^
     본다   본다   본다   본다   본다   본다          본다

  scan() 이 visits += points.size() 를 하고 목록을 그대로 돌려준다
  -> contains / rangeSearch / nearest / nearestK 모두 질의 1 회당 visits 가 정확히 n

  이 n 이 기준선이다.
    트리의 visits 가 n 보다 훨씬 작다  -> 가지치기가 먹었다
    트리의 visits 가 n 에 가깝다       -> 가지치기가 안 먹었다 (넓은 질의, 치우친 점 분포)

  시간이 아니라 visits 를 세는 이유 : 시간은 기계와 JIT 에 따라 흔들리지만
  들여다본 노드 수는 결정적이라 같은 입력이면 언제나 같은 수가 나온다.

  insert 는 먼저 contains 로 중복을 보므로 그 자체로 O(n) 이다.
  nearestK 는 전부 정렬하므로 O(n log n) 이다 (어차피 다 볼 것이라 힙을 쓸 이유가 없다).
```


### 필드
- `points` — 역할:
- `visits` — 역할:

### `boolean insert(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Point2D> rangeSearch(Rectangle area)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `Point2D nearest(Point2D target)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `List<Point2D> nearestK(Point2D target, int k)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `long visits()` / `void resetVisits()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — KdTree (`src/main/java/com/datastructure/spatial/KdTree.java`)

### 구조

```
KD-트리 : 깊이마다 비교 축을 번갈아 바꾸며 평면을 반씩 잘라 들어간다
          axis = depth & 1   (0 = x 로 비교, 1 = y 로 비교)
          왼쪽 = 그 축 좌표가 노드 이하 (같으면 왼쪽), 오른쪽 = 노드보다 큼

  넣은 순서 : A(5,5)  B(2,7)  C(8,2)  D(1,3)  E(7,6)

  y                                    대응 트리
  9 |          |   |
  8 |          |   |                              A(5,5)            깊이 0 : x 로 비교
  7 |----*-----+   |                             /      \
  6 |  |       |   *                       B(2,7)        C(8,2)     깊이 1 : y 로 비교
  5 |  |       *   |                        /                  \
  4 |  |       |   |                   D(1,3)                  E(7,6)   깊이 2 : x 로 비교
  3 |  *       |   |
  2 |  |       +---+-*--
  1 |  |       |
  0 +--+-------+---+----> x
     0 1       5   7 8 9

  A(5,5) 의 세로선 x=5 : 평면 전체를 좌우로 가른다 (루트)
  B(2,7) 의 가로선 y=7 : 왼쪽 반쪽(x <= 5)만 위아래로 가른다
  D(1,3) 의 세로선 x=1 : 그 아래 칸(x <= 5, y <= 7)만 다시 좌우로 가른다
  C(8,2) 의 가로선 y=2 : 오른쪽 반쪽(x > 5)만 위아래로 가른다
  E(7,6) 의 세로선 x=7 : 그 위 칸(x > 5, y > 2)만 다시 좌우로 가른다

  즉 트리의 노드 하나 = 평면의 사각형 하나 + 그 사각형을 가르는 선 하나.
  자기가 맡은 사각형 밖으로는 그 선의 효력이 없다.

  Node
  +---------------------------------------------+
  | point : 이 노드가 들고 있는 점 (= 분할점)   |
  | left  : 그 축 좌표가 point 이하인 점들      |
  | right : 그 축 좌표가 point 보다 큰 점들     |
  +---------------------------------------------+
  축은 노드에 저장하지 않는다. 내려가면서 depth 로 계산한다 (depth & 1).

  "같으면 왼쪽" 을 어기면 contains 가 점을 못 찾고 rangeSearch 가 빠뜨린다.
  균형 로직이 없으므로 넣는 순서가 나쁘면 높이가 n 까지 늘어난다.
  build(List) 는 축별로 정렬해 중앙값을 뿌리로 삼아 처음부터 균형 잡힌 트리를 만든다.
```

### 동작 — 삽입

```
insert(new Point2D(6, 4)) : 깊이마다 비교 축을 바꿔가며 내려가 빈 자리에 붙인다

  깊이 0   A(5,5)    axis = 0 (x)   6 <= 5 ?  아니다  -> 오른쪽
  깊이 1   C(8,2)    axis = 1 (y)   4 <= 2 ?  아니다  -> 오른쪽
  깊이 2   E(7,6)    axis = 0 (x)   6 <= 7 ?  그렇다  -> 왼쪽
  깊이 3   빈 자리                                    -> new Node((6,4)) , size++

before                                 after

           A(5,5)                              A(5,5)
          /      \                             /      \
    B(2,7)        C(8,2)                 B(2,7)        C(8,2)
     /                  \                 /                  \
D(1,3)                  E(7,6)       D(1,3)                  E(7,6)
                                                             /
                                                       (6,4)      <- 새 노드 (깊이 3)

  내려가면서 지나친 노드마다 visits++ 한다 (여기서는 A, C, E 세 개)
  이미 있는 점이면 (p.equals(node.point)) 그 노드를 그대로 돌려주고 아무것도 안 한다
  -> size 가 안 늘고 insert 는 false 를 돌려준다 (중복 거부)

  비용 : O(높이). 균형이 잡혀 있으면 O(log n), 한 줄로 늘어지면 O(n).
  기존 노드는 하나도 안 옮긴다. 새 점은 언제나 잎으로 붙는다.
```

### 동작 — 범위 검색 (가지치기)

```
rangeSearch(area) : 분할선과 질의 사각형을 견줘 한쪽 서브트리를 통째로 건너뛴다

  질의 사각형 area = x [1,3] , y [4,8]

                              루트 A(5,5) 의 분할선 x = 5
                                        |
       +-------------+                  |
       |    area     |                  |    오른쪽 서브트리(C, E)에 들어 있는 점은
       |  x [1,3]    |                  |    정의상 전부 x > 5 다.
       |  y [4,8]    |                  |    area 의 max x 는 3 이므로 하나도 걸릴 수 없다.
       +-------------+                  |    -> 그 아래로 아예 안 내려간다 = 가지치기
                                        |
   -------------------------------------+-------------------------------
        왼쪽 : x <= 5                    |          오른쪽 : x > 5

  판정 (rangeFrom) :  axis = depth & 1 ,  split = node.point.coordinate(axis)

      area.min(axis) <= split   이면 왼쪽으로 내려간다
      area.max(axis) >  split   이면 오른쪽으로 내려간다
      한쪽만 참이면 반대쪽은 통째로 생략된다. 둘 다 참이면 양쪽을 다 본다.
      (오른쪽이 >= 가 아니라 > 인 것은 "같으면 왼쪽" 규칙과 짝이다. >= 면 헛걸음이 는다)

  이 트리에서 :
      A(5,5) axis=x split=5 :  1 <= 5 참 -> 왼쪽 O  /  3 > 5 거짓 -> 오른쪽 X  (C, E 생략)
      B(2,7) axis=y split=7 :  4 <= 7 참 -> 왼쪽 O  /  8 > 7 참   -> 오른쪽 O  (비어 있다)
                               B 는 area 안이므로 담는다
      D(1,3) axis=x split=1 :  자식이 없다. y=3 은 area 밖이라 안 담는다

              A   본다
             / \
            B   C   안 봄
           /     \
          D       E   안 봄
        본다

  visits :  KdTree 3 (A, B, D)   vs   NaiveSpatialIndex 5 (n 개 전부)

  담는 것과 내려가는 것은 별개다. 노드는 자기가 area 안이면 담고,
  자식으로 내려갈지는 오로지 분할선과 area 의 겹침으로 정한다.
  사각형이 좁을수록 잘리는 가지가 많아진다. 반대로 사각형이 넓으면
  결국 다 봐야 하므로 visits 가 n 으로 수렴한다 (그때는 전수 조사보다 오히려 손해다).
```

### 동작 — k-최근접 (반경과 분할선 견주기)

```
nearest / nearestK : 가까운 쪽을 먼저 파고, 반대쪽은 지금까지의 반경과 견줘 결정한다

  axis = depth & 1
  gap  = target.coordinate(axis) - node.point.coordinate(axis)     (long 으로 올려 계산)
  near = gap <= 0 ? node.left : node.right      가까운 쪽 = target 이 있는 쪽
  far  = 그 반대쪽
  r    = 지금까지의 최선 제곱거리
           nearest  : target.squaredDistanceTo(best)
           nearestK : best.radius() = 힙 머리(들고 있는 k 개 중 가장 먼 것)까지의 제곱거리
                      아직 k 개가 안 찼으면 Long.MAX_VALUE 라 아무것도 못 자른다

  [1] gap*gap >= r   ->  far 는 안 본다

        T                          분할선
        |<---------- gap --------->|
        |<--- r --->|              |     반지름 r 이 분할선에 닿지도 못한다
                                         선 너머의 점은 전부 r 보다 멀다

  [2] gap*gap <  r   ->  far 도 본다

        T              분할선
        |<--- gap ---->|
        |<---------- r ---------->|      반지름 r 이 분할선을 넘는다
                                         선 너머에 더 가까운 점이 있을 수 있다

  순서가 핵심이다. near 를 먼저 내려가야 거기서 r 이 먼저 작아지고,
  그래야 돌아왔을 때 far 를 자를 확률이 커진다. far 를 먼저 보면 r 이 큰 채로 헤맨다.
  전부 제곱거리로 비교한다 (sqrt 호출 없음). 대소 관계는 제곱해도 그대로다.

  비용 : 점이 고르게 퍼져 있으면 평균 O(log n), 최악은 O(n) (차원이 높거나 분포가 치우칠 때).
```


### 필드
- `root` — 역할:
- `size` — 역할:
- `visits` — 역할:
- `Node.point` / `Node.left` / `Node.right` — 역할:

### `boolean insert(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node insertInto(Node node, Point2D p, int depth)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `static KdTree build(List<Point2D> points)`
- 하는 일:
- 논리:
- 비용(왜):

### `static Node buildRange(List<Point2D> points, int from, int to, int depth)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Point2D> rangeSearch(Rectangle area)`
- 하는 일:
- 논리:
- 비용(왜):

### `void rangeFrom(Node node, Rectangle area, int depth, List<Point2D> out)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `Point2D nearest(Point2D target)`
- 하는 일:
- 논리:
- 비용(왜):

### `Point2D nearestFrom(Node node, Point2D target, int depth, Point2D best)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `List<Point2D> nearestK(Point2D target, int k)`
- 하는 일:
- 논리:
- 비용(왜):

### `void nearestKFrom(Node node, Point2D target, int depth, KNearest best)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int height()`
- 하는 일:
- 논리:
- 비용(왜):

### `long visits()` / `void resetVisits()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — QuadTree (`src/main/java/com/datastructure/spatial/QuadTree.java`)

### 구조

```
쿼드트리 : 점이 아니라 "칸"을 먼저 정해두고, 칸이 넘치면 그 칸을 넷으로 쪼갠다
           new QuadTree(bounds = [0,15] x [0,15], capacity = 4)

  Rectangle.subdivide() 가 만드는 네 칸                     대응 트리

   15 +---------------+---------------+                        root
      |               |               |                   [0,15]x[0,15]
      |  children[2]  |  children[3]  |                  /    |    |    \
      | [0,7]x[8,15]  | [8,15]x[8,15] |                 /     |    |     \
      |   왼쪽 위     |   오른쪽 위   |               [0]    [1]  [2]    [3]
    8 +---------------+---------------+           (children 배열의 순서다)
    7 |               |               |
      |  children[0]  |  children[1]  |         midX = minX + (maxX - minX) / 2 = 7
      | [0,7]x[0,7]   | [8,15]x[0,7]  |         midY = minY + (maxY - minY) / 2 = 7
      |   왼쪽 아래   |  오른쪽 아래  |
    0 +---------------+---------------+         오른쪽/위 칸은 mid 가 아니라 mid + 1 에서
      0               7 8            15         시작한다. 정수 격자라 두 칸이 같은 좌표를
                                                가지면 점이 두 칸에 걸린다.

  네 칸은 부모를 빈틈없이, 겹치지 않게 덮는다. childIndex() 가 그것을 전제로
  bounds.contains(p) 인 칸을 찾고, 못 찾으면 IllegalStateException 을 던진다.

  Node
  +----------------------------------------------------------+
  | bounds   : 이 노드가 맡은 사각형. 만들 때 정해지고 안 변함|
  | points   : 잎일 때만 점을 담는다                          |
  | children : null 이면 잎, 아니면 길이 4                     |
  +----------------------------------------------------------+
  isLeaf() == (children == null)
  쪼갠 노드의 points 는 비어 있다. 점은 전부 잎에만 있다.

  KD-트리와의 차이 : KD-트리는 "점이 선을 정한다"(데이터가 분할을 만든다).
  쿼드트리는 "선이 먼저 있고 점이 칸에 들어간다"(공간이 분할을 만든다).
  그래서 쿼드트리는 bounds 밖의 점을 아예 못 받는다 (insert 가 false).
```

### 동작 — 삽입 / 분할

```
insert(p) : 잎까지 내려가 담는다. capacity 를 넘기면 그 잎을 넷으로 쪼갠다. (capacity = 4)

before : (1,1) (2,2) (3,3) (4,4) 를 넣은 뒤 - 아직 4 개라 capacity 이하다

   15 +-------------------------------+       root (잎)
      |                               |         bounds   [0,15]x[0,15]
      |                               |         points   [(1,1),(2,2),(3,3),(4,4)]
      |                               |         children null
      | * * * *   <- (1,1) .. (4,4)   |
    0 +-------------------------------+       depth() = 1 , leafCount() = 1
      0                              15

insert(new Point2D(9, 9))
   -> points 가 5 개가 되어 capacity 4 를 넘는다 -> subdivide(node)

after :

   15 +---------------+---------------+       root (쪼개짐. points 는 비었다)
      |               |               |        |
      |  children[2]  |  children[3]  |        +-- children[0] [0,7]x[0,7]
      |    (빈 잎)    |    * (9,9)    |        |     points [(1,1),(2,2),(3,3),(4,4)]
    8 +---------------+---------------+        +-- children[1] [8,15]x[0,7]   (빈 잎)
    7 |               |               |        +-- children[2] [0,7]x[8,15]   (빈 잎)
      |  children[0]  |  children[1]  |        +-- children[3] [8,15]x[8,15]
      | * * * *       |    (빈 잎)    |        |     points [(9,9)]
    0 +---------------+---------------+       depth() = 2 , leafCount() = 4
      0               7 8            15

  subdivide(node) 가 하는 일
    1. Rectangle.subdivide() 로 네 칸을 만들어 children 에 채운다
    2. 원래 들고 있던 점을 전부 빼내고 (points.clear())
    3. 하나씩 childIndex() 가 가리키는 칸에 다시 넣는다 (재배치)
  2 번을 빼먹으면 점이 부모와 자식에 둘 다 남아 검색이 중복 결과를 낸다.

  비용 : 보통 O(깊이). 쪼갤 때만 그 잎에 있던 capacity+1 개를 다시 넣는다.

  최악 : 점들이 아주 좁은 곳에 몰려 있으면 쪼개도 또 같은 칸으로 몰려서
         칸이 1x1 이 될 때까지 연쇄로 쪼개진다. 깊이가 점 수가 아니라 좌표 비트 수로 정해진다.
         canSubdivide() 가 (maxX > minX && maxY > minY) 로 그 바닥을 막고,
         바닥 칸에서는 capacity 를 넘겨도 그냥 쌓인다 (더 쪼갤 공간이 없으므로).

  중복 : 잎에서 points.contains(p) 로 먼저 확인한다. 이미 있으면 false, size 도 안 는다.
  bounds 밖 : insert 가 아예 false. 쿼드트리는 자기 경계 밖을 표현할 수 없다.
```


### 필드
- `root` — 역할:
- `bounds` — 역할:
- `capacity` — 역할:
- `size` — 역할:
- `visits` — 역할:
- `Node.bounds` / `Node.points` / `Node.children` — 역할:

### `QuadTree(Rectangle bounds, int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `Rectangle bounds()` / `int capacity()`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean insert(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean insertInto(Node node, Point2D p)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void subdivide(Node node)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Point2D> rangeSearch(Rectangle area)`
- 하는 일:
- 논리:
- 비용(왜):

### `void rangeFrom(Node node, Rectangle area, List<Point2D> out)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `Point2D nearest(Point2D target)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Point2D> nearestK(Point2D target, int k)`
- 하는 일:
- 논리:
- 비용(왜):

### `void searchNearest(Node node, Point2D target, KNearest best)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int depth()` / `int leafCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `long visits()` / `void resetVisits()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| NaiveSpatialIndex | | | |
| KdTree | | | |
| QuadTree | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/25-spatial-index/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/25-spatial-index/src/main/java/com/datastructure/spatial/`
- 테스트: `/home/jun/project/myway/data-structure/25-spatial-index/src/test/java/com/datastructure/spatial/`
- 정답 구현: `/home/jun/project/myway/data-structure/25-spatial-index/impl/`
