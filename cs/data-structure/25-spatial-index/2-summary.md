# data-structure/25-spatial-index — 정리 (힌트)

## 해결하는 문제

점 (3, 7)과 (5, 2) 중 무엇이 더 큰가 — 정할 수 없다. x로 보면 앞이 작고 y로 보면 뒤가 작다.
2차원에는 전순서가 없어서, "왼쪽은 작고 오른쪽은 크다" 하나로 갈라 온 BST도, 이웃 관계를 버린 해시맵도 "이 사각형 안의 점"·"가장 가까운 점"에 답하지 못한다.

```text
전순서 없음 -> 전수 조사             공간을 조각내고 안 겹치는 조각을 버린다
  질의 1번 = 점 100만 개 전부         +-------+-------+
  * * * * * * * * * * * *             | 질의  |       |   오른쪽 절반은 x > 5
  * * * * * * * * * * * *             | 구역  |  x>5  |   질의 구역은 x <= 3
  * * * * * * * * * * * *             +-------+-------+   -> 통째로 안 본다
                                              x=5
```

공간 인덱스는 전순서 대신 **조각**을 새긴다 — 질의와 겹치지 않는 조각은 들여다보지 않는다(가지치기).
점이 선을 정하는 KD-트리와 칸이 먼저 있는 쿼드트리, 두 가지 조각내기를 만들고 방문한 노드 수로 가지치기가 실제로 일을 줄였는지 잰다.

- 쉬운 예: 지도를 동/서/남/북 구역으로 접어 두면 "가장 가까운 편의점"은 내 구역과 그 옆 구역만 보면 된다.
- 똑같은 구조다: 이 노트의 `KdTree`(축을 번갈아 반으로 가르기)와 `QuadTree`(칸이 넘치면 넷으로 쪼개기).
- 실무 예: "내 위치 반경 1km의 매장", 게임의 충돌 후보 좁히기, 지리 DB의 공간 인덱스.
  - *전순서(total order)*: 어떤 두 값이든 "누가 앞인가"를 정할 수 있는 순서. 1차원 수에는 있고 2차원 점에는 없다.
  - *가지치기(pruning)*: "이 아래엔 답이 있을 수 없다"가 확실한 서브트리를 통째로 건너뛰는 것.

### 한눈에 — 쉽게 말하면

**비유: 지도를 구역으로 접어 두기.** "지금 있는 곳에서 가장 가까운 편의점"을 찾는데 전국 편의점 목록을 처음부터 끝까지 다 훑는 사람은 없다. 지도를 동/서/남/북 구역으로 나눠 두면, 내 구역과 그 근처만 보면 되고 멀리 떨어진 구역은 **통째로 건너뛴다**. **공간 인덱스가 똑같은 구조다** — 평면을 미리 잘라 두고(KD-트리는 선으로 반씩, 쿼드트리는 칸을 넷으로), 질문 범위와 겹칠 수 없는 조각은 아예 들여다보지 않는다(가지치기). 실무로는 지도 앱의 "내 주변 검색", 게임의 충돌 판정, 위치 기반 추천이 이 위에서 돈다.

- 다루는 질문 세 가지: "이 사각형 안의 점 전부"(범위 검색), "가장 가까운 점"(nearest), "가까운 점 k개"(nearestK).
- 기준선은 NaiveSpatialIndex — 아무것도 안 나누고 전부 훑는 것. 트리가 실제로 덜 봤는지를 visits(들여다본 노드 수)로 잰다.
- 나누는 철학이 둘: KD-트리는 **점이 선을 정하고**(데이터가 분할을 만든다), 쿼드트리는 **칸이 먼저 있고 점이 들어간다**(공간이 분할을 만든다).

```text
질문: 왼쪽 위 사각형 안의 점은?        분할선 x=5 로 반 갈라 두었다

   +-------+-------+
   | 질문  |       |   오른쪽 절반의 점은 전부 x > 5
   | 구역  |  x>5  |   질문 구역은 x <= 3 까지뿐
   |       |       |   -> 오른쪽은 통째로 안 본다 (가지치기)
   +-------+-------+
           x=5
```

## 동작·원리

### 전체 흐름

```text
[1] 기준선 — 전부 훑는다              [2] 조각내기 두 가지
    NaiveSpatialIndex                       KdTree                 QuadTree
    rangeSearch / nearest = 점 수 n           A(5,5) x로 가름          +-------+-------+
    visits = n, 언제나                        /      \                |       |       |
                                        B(2,7)      C(8,2) y로 가름   +-------+-------+
              |                         점이 선을 정한다              칸이 먼저, 점이 들어간다
              v                         깊이 = 넣은 순서              깊이 = 좌표 범위
[3] 질의 = 내려가며 겹치는 쪽만 본다
    rangeSearch(area)  : 분할선과 area 가 겹치는 자식만 재귀 (겹치지 않는 쪽 = 가지치기)
    nearest(target)    : 가까운 쪽 먼저 -> 최선 반경 r 확보 -> "r > 분할선까지 거리" 일 때만 먼 쪽
    nearestK(target,k) : 최대 힙 KNearest 가 k 개를 들고, 힙 머리(가장 먼 것)가 r 이 된다
              |
              v
[4] 대가 — visits 로 잰다
    가지치기 조건을 빼도 답은 맞고 느려질 뿐   -> 시간 대신 방문 노드 수를 계약으로
    모든 점이 같은 거리면 한 개도 못 건너뛴다   -> 최악은 "최단 거리 > 데이터 폭"
    KD 는 삭제·재균형이 없다 (build 로 재구축)   쿼드는 경계 밖을 표현하지 못한다
```

- [1] 아무것도 안 나누면 질의 한 번이 점 수만큼이다. 이 기준선이 있어야 트리가 "덜 봤다"를 증명할 수 있다.
  - *visits*: 질의 한 번에 실제로 들여다본 노드 수. JIT로 흔들리는 시간 대신 쓰는 결정적인 잣대.
- [2] KD-트리는 깊이마다 x·y를 번갈아 비교 축으로 써서 평면을 반씩 가른다(`depth & 1`). 노드 하나 = 점 하나 + 분할선 하나. 쿼드트리는 칸(`bounds`)이 먼저 있고 점이 `capacity`를 넘치면 넷으로 쪼갠다 — 점은 언제나 잎에만 산다.
  - *중앙값(median)*: 정렬했을 때 한가운데 값. `KdTree.build`는 축별로 정렬해 중앙값을 뿌리로 삼아 처음부터 균형을 잡는다.
- [3] 범위 검색은 분할선과 사각형이 겹치는 자식만 내려간다. 최근접은 가까운 쪽을 먼저 내려가 최선 반경을 확보한 뒤, 분할선까지의 거리가 그 반경보다 짧을 때만 먼 쪽을 본다. k개는 최대 힙이 "지금까지의 k개 중 가장 먼 것"을 반경으로 내준다.
  - *반경(radius)*: 지금까지 찾은 최선까지의 거리. 이보다 먼 곳은 볼 필요가 없다는 경계선. 비교만 하므로 제곱거리로 충분하다.
- [4] 가지치기 조건이 빠져도 정답은 나온다 — 그래서 방문 수를 재지 않으면 전수 조사와 같은 코드를 트리라고 부르게 된다. 최악 입력·삭제 부재·경계 제약은 고칠 수 없는 성질이다.

### 계약 — SpatialIndex (`src/main/java/com/datastructure/spatial/SpatialIndex.java`)

- `boolean insert(Point2D p)`
- `boolean contains(Point2D p)`
- `int size()`
- `void clear()`
- `default boolean isEmpty()`
- `List<Point2D> rangeSearch(Rectangle area)`
- `Point2D nearest(Point2D target)`
- `List<Point2D> nearestK(Point2D target, int k)`

### 계약 — VisitCounting (`src/main/java/com/datastructure/spatial/VisitCounting.java`)

- `long visits()`
- `void resetVisits()`

### 구현 — Point2D (`src/main/java/com/datastructure/spatial/Point2D.java`)

#### 필드
- `x` — 역할:
- `y` — 역할:

#### `Point2D(int x, int y)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int coordinate(int axis)`
- 하는 일:
- 논리:
- 비용(왜):

#### `long squaredDistanceTo(Point2D other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `double distanceTo(Point2D other)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — Rectangle (`src/main/java/com/datastructure/spatial/Rectangle.java`)

#### 필드
- `minX` / `minY` — 역할:
- `maxX` / `maxY` — 역할:

#### `Rectangle(int minX, int minY, int maxX, int maxY)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int min(int axis)` / `int max(int axis)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean contains(Point2D p)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean intersects(Rectangle other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `long squaredDistanceTo(Point2D p)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean canSubdivide()`
- 하는 일:
- 논리:
- 비용(왜):

#### `Rectangle[] subdivide()`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — KNearest (`src/main/java/com/datastructure/spatial/KNearest.java`)

#### 구조

```text
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

  - *힙(heap)*: "가장 큰(또는 작은) 것이 항상 머리에 오는" 반쯤 정렬된 나무(07번). 최대 힙은 최댓값이 머리.
  - *비교자(comparator)*: 무엇을 크다고 볼지 정해 주는 규칙. 여기서는 "target에서 먼 것 = 크다"로 뒤집어 놓았다.
  - *제곱거리*: 거리를 제곱한 값. 크고 작음만 비교할 거면 제곱근(sqrt)을 안 구해도 순서가 같아서, 느린 sqrt 호출을 아낀다.

#### 필드
- `target` — 역할:
- `k` — 역할:
- `heap` — 역할:

#### `KNearest(Point2D target, int k)`
- 하는 일:
- 논리:
- 비용(왜):

#### `void offer(Point2D candidate)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `long radius()`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Point2D> drain()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — NaiveSpatialIndex (`src/main/java/com/datastructure/spatial/NaiveSpatialIndex.java`)

#### 구조

```text
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

  - *기준선(baseline)*: 비교의 출발점이 되는 가장 단순한 방법. 트리의 성적은 이것 대비 얼마나 덜 봤는가로 잰다.
  - *JIT*: 자바가 실행 중에 코드를 기계어로 다시 굽는 장치. 실행 시간이 이것 때문에 들쭉날쭉해서, 시간 대신 결정적인 visits를 센다.

#### 필드
- `points` — 역할:
- `visits` — 역할:

#### `boolean insert(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean contains(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Point2D> rangeSearch(Rectangle area)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `Point2D nearest(Point2D target)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Point2D> nearestK(Point2D target, int k)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `long visits()` / `void resetVisits()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — KdTree (`src/main/java/com/datastructure/spatial/KdTree.java`)

#### 구조

```text
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

  - *축(axis)*: 어느 좌표로 비교할지 — x축이냐 y축이냐. 깊이가 짝수면 x, 홀수면 y로 번갈아 쓴다.
  - *depth & 1*: 깊이를 2로 나눈 나머지를 비트 연산으로 구한 것. 0이면 x, 1이면 y.
  - *중앙값(median)*: 정렬했을 때 한가운데 값. 이걸 뿌리로 삼으면 좌우 개수가 반반이라 균형이 잡힌다.

#### 동작 — 삽입

**언제 쓰나** — 점을 하나 추가할 때. 이미 있는 노드는 하나도 안 옮기고, 새 점은 언제나 잎으로 붙는다.

```text
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

**그림 해설** — 위 before/after에서 일어난 일:
1. 깊이 0에서는 x로, 깊이 1에서는 y로, 깊이 2에서는 다시 x로 — 축을 번갈아 비교하며 내려간다.
2. "작거나 같으면 왼쪽, 크면 오른쪽" 규칙대로 빈 자리에 닿으면 거기 새 노드를 단다.
3. 같은 점이 이미 있으면 아무것도 바꾸지 않고 false를 돌려준다(중복 거부).

#### 동작 — 범위 검색 (가지치기)

**언제 쓰나** — "이 사각형 안의 점을 전부 달라"는 질문(rangeSearch).

먼저 알아야 할 것 — **가지치기(pruning)**:
- 트리에서 "이 아래에는 답이 있을 수 없다"가 확실한 가지를 통째로 건너뛰는 것.
- 정원사가 가지 하나를 자르면 그 가지에 달린 잎을 일일이 안 떼도 되는 것과 같다.

```text
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

**그림 해설** — 위 판정에서 일어난 일:
1. 노드마다 두 가지를 따로 한다 — "나 자신이 사각형 안인가?"(안이면 담는다)와 "어느 자식으로 내려갈까?"(분할선과 사각형의 겹침으로만 정한다).
2. 질문 사각형이 분할선의 한쪽에만 있으면 반대쪽 서브트리는 통째로 건너뛴다 — A에서 오른쪽(C, E)이 잘린 이유.
3. 그래서 visits가 3(트리) vs 5(전수)로 갈린다. 사각형이 넓어지면 이 이득은 사라진다.

#### 동작 — k-최근접 (반경과 분할선 견주기)

**언제 쓰나** — "가장 가까운 점"(nearest) / "가까운 점 k개"(nearestK)를 물을 때. 범위 검색과 달리 사각형 대신 **지금까지 찾은 최선까지의 거리**(반경)로 가지를 자른다.

```text
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

**그림 해설** — 위 두 경우에서 일어난 일:
1. target이 있는 쪽(near)을 먼저 끝까지 파고 내려간다 — 거기서 반경 r이 빨리 작아진다.
2. 돌아 나오며 노드마다 묻는다: "지금 반경 r인 원이 분할선을 넘나?" gap(선까지의 거리)의 제곱과 r을 비교하면 된다.
3. 원이 선에 못 닿으면([1]) 선 너머는 전부 더 멀다 — 반대쪽 가지를 통째로 자른다. 닿으면([2]) 반대쪽도 봐야 한다.
4. nearestK에서는 r이 "지금 들고 있는 k개 중 가장 먼 것"까지의 거리(KNearest.radius())다. k개가 차기 전에는 아무것도 못 자른다.
  - *gap*: target에서 분할선까지의 수직 거리. 음수면 target이 왼쪽에 있다는 뜻이라 부호는 방향으로만 쓴다.
  - *long으로 올려 계산*: int끼리 곱하면 담을 수 있는 수의 한계를 넘칠 수 있어, 더 큰 그릇(long)으로 바꿔 곱한다(오버플로 방지).

#### 필드
- `root` — 역할:
- `size` — 역할:
- `visits` — 역할:
- `Node.point` / `Node.left` / `Node.right` — 역할:

#### `boolean insert(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Node insertInto(Node node, Point2D p, int depth)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `static KdTree build(List<Point2D> points)`
- 하는 일:
- 논리:
- 비용(왜):

#### `static Node buildRange(List<Point2D> points, int from, int to, int depth)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean contains(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Point2D> rangeSearch(Rectangle area)`
- 하는 일:
- 논리:
- 비용(왜):

#### `void rangeFrom(Node node, Rectangle area, int depth, List<Point2D> out)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `Point2D nearest(Point2D target)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Point2D nearestFrom(Node node, Point2D target, int depth, Point2D best)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Point2D> nearestK(Point2D target, int k)`
- 하는 일:
- 논리:
- 비용(왜):

#### `void nearestKFrom(Node node, Point2D target, int depth, KNearest best)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `int height()`
- 하는 일:
- 논리:
- 비용(왜):

#### `long visits()` / `void resetVisits()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — QuadTree (`src/main/java/com/datastructure/spatial/QuadTree.java`)

#### 구조

```text
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

  - *bounds(경계)*: 이 노드가 맡은 사각형 영역. 만들 때 정해지고 변하지 않는다.
  - *capacity(용량)*: 잎 하나가 쪼개지기 전까지 담을 수 있는 점의 최대 개수.
  - *잎(leaf)*: 자식이 없는 노드. 쿼드트리에서 점은 전부 잎에만 있다.

#### 동작 — 삽입 / 분할

**언제 쓰나** — 점을 추가할 때. 평소엔 잎에 그냥 담고, 잎이 용량을 넘기는 순간에만 그 잎을 넷으로 쪼갠다.

```text
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

**그림 해설** — 위 before/after에서 일어난 일:
1. 점 4개까지는 뿌리(잎 하나)에 그냥 쌓인다 — 아직 나눌 이유가 없다.
2. 5번째 점이 들어와 용량(4)을 넘는 순간, 그 잎의 사각형을 넷으로 자르고 자식 4칸을 만든다.
3. 원래 있던 점들을 전부 꺼내(points.clear()) 각자 자기 칸으로 다시 넣는다 — 이걸 빼먹으면 점이 부모와 자식 양쪽에 남아 검색이 중복 결과를 낸다.
4. 쪼갠 뒤 부모의 points는 빈다. 점은 언제나 잎에만 산다.
  - *재배치*: 쪼개는 순간 그 잎에 있던 점들을 새 네 칸에 다시 나눠 담는 일. capacity+1개만 옮기면 된다.

#### 필드
- `root` — 역할:
- `bounds` — 역할:
- `capacity` — 역할:
- `size` — 역할:
- `visits` — 역할:
- `Node.bounds` / `Node.points` / `Node.children` — 역할:

#### `QuadTree(Rectangle bounds, int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Rectangle bounds()` / `int capacity()`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean insert(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean insertInto(Node node, Point2D p)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `void subdivide(Node node)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean contains(Point2D p)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Point2D> rangeSearch(Rectangle area)`
- 하는 일:
- 논리:
- 비용(왜):

#### `void rangeFrom(Node node, Rectangle area, List<Point2D> out)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `Point2D nearest(Point2D target)`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Point2D> nearestK(Point2D target, int k)`
- 하는 일:
- 논리:
- 비용(왜):

#### `void searchNearest(Node node, Point2D target, KNearest best)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `int depth()` / `int leafCount()`
- 하는 일:
- 논리:
- 비용(왜):

#### `long visits()` / `void resetVisits()`
- 하는 일:
- 논리:
- 비용(왜):

## 쓰이는 자료구조·알고리즘

- **지리 DB의 공간 인덱스 — PostGIS(GiST/R-tree) · MySQL SPATIAL** — "반경 1km의 매장" 질의를 사각형 교차 가지치기로 좁힌다. PostGIS는 GiST 위의 R-tree 계열, MySQL InnoDB의 SPATIAL 인덱스는 R-tree다(각 공식 문서). R-tree는 쿼드트리처럼 공간을 고정 칸으로 자르지 않고, B-트리처럼 균형을 유지하며 서로 겹칠 수 있는 최소 경계 사각형(MBR)으로 묶는 구조다(Guttman 1984).
- **geohash · S2 · H3 셀** — 위경도를 문자열/정수 셀로 바꿔 해시맵·정렬 인덱스에 얹는 방식. geohash(위·경도 비트 교차 = Z-order)와 S2(정육면체 면 위 쿼드트리 + 힐베르트 곡선)는 쿼드트리의 "칸 번호"를 편 것과 같다. H3는 사각형이 아니라 육각형 계층이라 쿼드트리는 아니지만, 셀 경계 근처의 이웃 누락이라는 함정은 셋 다 같다(커리큘럼 ⚠).
- **게임·시뮬레이션의 충돌 후보 좁히기** — 매 프레임 "내 근처의 물체"만 검사한다. 물체가 움직이므로 쿼드트리를 프레임마다 다시 짓거나(정적 구축) 잎 용량을 넉넉히 둔다.
- **ML의 k-최근접 탐색 — scikit-learn `KDTree`·`BallTree`** — 저차원에서는 `nearestK`와 같은 가지치기, 고차원(수십 차원↑)에서는 차원의 저주로 무너져 근사(LSH·HNSW)로 간다(정답 6번 참고).
- **이미지·지형 압축의 쿼드트리** — 같은 색/높이인 칸은 더 쪼개지 않는다. "칸이 넘치면 쪼갠다"를 "칸이 균일하지 않으면 쪼갠다"로 바꾼 것.
- **이 노트가 가져다 쓰는 것** — [06-binary-search-tree](../06-binary-search-tree/2-summary.md)(1차원 가르기의 원형), [07-heap](../07-heap/2-summary.md)(`KNearest`의 최대 힙 — `KthLargest`와 같은 발상).

## 적용 — 풀어나가는 법

공간 질의 문제는 "무엇이 가지치기 조건인가"를 한 줄로 쓰는 데서 갈린다.
순서: ① 질의 종류를 정한다(범위 / 최근접 / k개) → ② 가지치기 조건을 적는다 — 범위는 "분할선과 사각형이 겹치는가", 최근접은 "최선 반경 > 분할선까지 거리인가" → ③ 같은 좌표를 어느 쪽에 둘지(`<=`는 왼쪽)를 삽입·조회·범위 모두 같은 규칙으로 맞춘다 → ④ 기준선(전수 조사)과 방문 수를 대조해 가지치기가 실제로 줄였는지 확인한다.
아래 과제 다섯이 이 순서로 풀린다.

### 문제 — 이 챕터가 시키는 것

2차원 점에는 전순서가 없어서 06번 BST도 05번 해시맵도 못 쓴다.\
그래서 "이 사각형 안의 점 전부"와 "가장 가까운 점"에 답하는 길이 전수 조사밖에 안 남는다.\
전순서를 포기하는 대신 공간을 조각내고 질의와 안 겹치는 조각을 통째로 버리는 구조(가지치기)를 두 가지 방식으로 만든다.\
그리고 그 가지치기가 실제로 일을 줄이는지, 언제 안 줄이는지를 방문한 노드 수로 직접 측정한다.

**과제**

1. `Point2D`, `Rectangle` (TODO 4개) — 제곱거리, 사각형의 점 포함·교차, 사각형에서 점까지의 거리
2. `KNearest` (TODO 1개) — 지금까지의 최선 k개를 담는 최대 힙의 `offer`
3. `NaiveSpatialIndex` (TODO 3개) — 전부 훑는 기준선의 `rangeSearch` / `nearest` / `nearestK`
4. `KdTree` (TODO 5개) — 축을 번갈아 가르는 삽입·일괄 구축과 가지치기하는 범위 조회·최근접
5. `QuadTree` (TODO 4개) — 칸이 넘치면 넷으로 쪼개는 삽입·분할과 가지치기하는 범위 조회·최근접

`cd ~/project/myway/data-structure && ./run.sh 25` — 113개 중 97개가 실패한다.\
테스트가 `root`와 노드의 `point`/`left`/`right`, `bounds`/`points`/`children`을 직접 읽는다 — 필드 이름이 계약이다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| NaiveSpatialIndex | | | |
| KdTree | | | |
| QuadTree | | | |

## 장애 시나리오와 대처

**1. 쿼드트리 경계 밖의 점이 조용히 버려짐**

- 현상: 넣은 점 수와 `size()`가 다르다. 어떤 지역의 점이 검색에 아예 안 나온다.
- 보이는 형태: 예외 없음 — `insert`가 `false`를 돌려주고 끝난다. 좌표가 음수이거나 `bounds`를 넘는 데이터(예: 경계를 `[0,1023]`로 잡았는데 좌표가 2000)에서 난다.
- 원인: 쿼드트리는 칸이 먼저다 — `bounds.contains(p)`가 아니면 표현할 자리가 없다. 중복 점도 같은 `false`라 둘이 구별되지 않는다.
- 대처: `insert`의 반환값을 버리지 않는다(`false`면 세어서 경고). 경계는 데이터의 실제 범위에서 정하고, 범위를 모르면 KD-트리를 쓴다 — 점이 선을 정하므로 경계가 없다.

**2. 같은 좌표를 어느 쪽에 두는지가 삽입과 조회에서 어긋남**

- 현상: 분명히 넣은 점을 `contains`가 못 찾고, `rangeSearch`가 일부를 빠뜨린다.
- 보이는 형태: 좌표 범위가 좁은 데이터(2000개를 40x40에)에서만 드러난다 — 같은 x나 y를 가진 점이 많아야 갈림길이 생기기 때문이다. 넓은 범위 테스트는 다 통과한다.
- 원인: 삽입은 `<=`를 왼쪽으로 보냈는데 조회나 범위 재귀는 `<`로 판단했다. 분할선 위의 점이 다른 쪽 서브트리에 있어 내려가지 않는다.
- 대처: "같으면 왼쪽" 한 규칙을 `insertInto`·`contains`·`rangeFrom`(`area.min <= split`이면 왼쪽, `area.max > split`이면 오른쪽) 셋에 같은 부호로 새긴다. 대조 테스트에 좁은 범위 데이터셋을 반드시 둔다.

**3. 가지치기 조건이 빠졌는데 테스트가 전부 통과**

- 현상: 정답은 다 맞는데 데이터가 커지면 전수 조사와 속도가 같다.
- 보이는 형태: 범위 조회 200번의 방문이 KD-트리 기대치 약 9,135가 아니라 기준선 800,000에 가깝다(README 실측). 정답 테스트는 113개가 다 통과하고 방문 수 측정 하나만 깨진다.
- 원인: `rangeFrom`의 "겹치는 쪽만" 조건이나 `nearestFrom`의 "반경 > 분할선 거리일 때만 먼 쪽" 조건이 없어도 답은 맞다 — 그냥 양쪽을 다 내려갈 뿐이다.
- 대처: 시간이 아니라 `visits()`를 계약에 넣는다. 기준선 대비 방문 수 상한을 테스트로 박아, 조건이 빠지면 빨갛게 만든다(정답 3번 참고).

**4. 제곱거리 계산이 `int`에서 넘쳐 엉뚱한 점이 최근접이 됨**

- 현상: 좌표가 큰 데이터(수만 이상)에서 `nearest`가 멀리 있는 점을 돌려준다.
- 보이는 형태: 예외 없음. `dx*dx + dy*dy`가 음수나 작은 값으로 뒤집혀 비교가 뒤바뀐다.
  - *오버플로(overflow)*: 계산 결과가 자료형의 범위를 넘쳐 엉뚱한 값이 되는 것. `int`는 약 21억까지라 좌표 차이가 5만이면 제곱 하나(25억)만으로 넘치고, 둘을 더하면 차이가 3만 3천 근처부터 넘친다.
- 원인: 좌표가 `int`라 곱셈도 `int`로 일어난다. 더한 뒤에 `long`으로 올리면 이미 늦다.
- 대처: `Point2D.squaredDistanceTo`처럼 빼기 **전에** `(long) x - other.x`로 올린다. 제곱근은 쓰지 않는다 — 비교만 할 것이면 제곱거리로 순서가 같고 부동소수점 오차도 없다.

## 핵심 문장

- 2차원 점에는 전순서가 없어서 BST도 해시맵도 "근처"에 답하지 못한다 — 공간 인덱스는 순서 대신 조각을 새기고, 질의와 겹치지 않는 조각을 통째로 버린다.
- 조각내는 철학이 둘이다: KD-트리는 점이 선을 정하고(깊이 = 넣은 순서), 쿼드트리는 칸이 먼저 있고 점이 들어간다(깊이 = 좌표 범위).
- 가지치기 조건은 두 줄뿐이다 — 범위는 "분할선과 사각형이 겹치는가", 최근접은 "최선 반경 > 분할선까지 거리인가". 이 조건이 빠져도 답은 맞으므로 시간이 아니라 방문 수를 계약으로 잰다.
- 최악은 직선이 아니라 "최단 거리가 데이터 폭보다 크다"일 때다 — 모든 점이 거의 같은 거리면 한 개도 못 건너뛰고, 차원이 오르면 그것이 기본이 된다.
- KD-트리는 삭제·재균형이 없어 정적으로 쓰거나 `build`로 재구축하고, 쿼드트리는 경계 밖을 표현하지 못한다 — 둘 다 고칠 수 없는 성질이다.

## 관련 주제·근거

- 선행 — [06-binary-search-tree](../06-binary-search-tree/2-summary.md): 1차원 가르기와 삽입 순서에 따른 편향. KD-트리가 축만 번갈아 쓴 같은 문제를 물려받는다.
- 선행 — [05-hashmap](../05-hashmap/2-summary.md): "옆에 뭐가 있나"를 버린 구조. geohash는 그 위에 칸 번호를 얹어 이웃을 되찾는 방식이다.
- 재료 — [07-heap](../07-heap/2-summary.md): `KNearest`의 최대 힙 — 머리가 "k개 중 가장 먼 것" = 가지치기 반경.
- 연결 — [11-bloom-filter](../11-bloom-filter/2-summary.md): 차원의 저주에서 정확한 최근접을 포기하고 근사(LSH·HNSW)로 가는 거래의 원형.
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `39-spatial-index` (선행 `16` · 원전 Guttman 1984 — R-tree).
- myway 원본 — `/home/jun/project/myway/data-structure/25-spatial-index/` (README.md · impl/KdTree.java · impl/QuadTree.java · impl/KNearest.java · impl/Point2D.java).

### 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/25-spatial-index/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/25-spatial-index/src/main/java/com/datastructure/spatial/`
- 테스트: `/home/jun/project/myway/data-structure/25-spatial-index/src/test/java/com/datastructure/spatial/`
- 정답 구현: `/home/jun/project/myway/data-structure/25-spatial-index/impl/`

### 용어 풀이

> 본문에서 이미 등장 자리마다 풀었지만, 복습용으로 한곳에 모은다. (중학생 수준 1~2줄)

- **공간 인덱스(spatial index)**: 2차원(이상) 좌표의 점들을 "근처만 보고 답하게" 정리해 둔 자료구조.
- **범위 검색(range search)**: "이 사각형 안의 점 전부"를 묻는 질의.
- **nearest / nearestK (k-최근접)**: 가장 가까운 점 하나 / 가까운 순서로 k개를 묻는 질의.
- **KD-트리**: 깊이마다 x축·y축을 번갈아 가며 평면을 반씩 자르는 이진 트리. 점이 분할선을 정한다.
- **쿼드트리(QuadTree)**: 칸이 넘치면 그 칸을 넷으로 쪼개는 트리. 공간(칸)이 먼저고 점이 들어간다.
- **축(axis)**: 비교에 쓰는 좌표 방향(x 또는 y). depth & 1(깊이를 2로 나눈 나머지)로 정한다.
- **분할선(split)**: 노드가 평면을 가르는 선. 자기가 맡은 사각형 안에서만 효력이 있다.
- **가지치기(pruning)**: "이 아래엔 답이 있을 수 없다"가 확실한 서브트리를 통째로 건너뛰는 것.
- **서브트리(부분트리)**: 어느 노드 아래에 매달린 나무 전체.
- **잎(leaf)**: 자식이 없는 노드. 쿼드트리에서 점은 전부 잎에만 있다.
- **bounds(경계) / capacity(용량)**: 노드가 맡은 사각형 / 잎이 쪼개지기 전까지 담는 점의 최대 개수.
- **subdivide(4분할)**: 사각형을 가운데에서 넷으로 자르는 것. 네 칸은 겹치지 않고 빈틈없이 부모를 덮는다.
- **재배치**: 잎을 쪼갤 때 그 잎의 점들을 새 칸들로 다시 나눠 담는 일.
- **중앙값(median)**: 정렬했을 때 한가운데 값. build가 균형 트리를 만들 때 뿌리로 삼는다.
- **균형**: 트리 좌우의 크기가 비슷해 높이가 log n에 머무는 상태. 이 KD-트리는 삽입 중 균형을 안 잡는다.
- **제곱거리**: 거리의 제곱. 크고 작음 비교만 할 거면 제곱근을 안 구해도 순서가 같다.
- **반경(radius)**: 지금까지 찾은 최선(또는 k개 중 가장 먼 것)까지의 거리. 이보다 먼 곳은 볼 필요가 없다는 경계선.
- **힙(heap) / 최대 힙**: 최댓값(또는 최솟값)이 항상 머리에 오는 반정렬 트리(07번). KNearest의 속이 최대 힙이다.
- **비교자(comparator)**: 무엇을 크다고 볼지 정하는 규칙. 뒤집으면 힙의 머리가 바뀐다.
- **visits**: 질의 한 번에 실제로 들여다본 노드 수. 시간 대신 쓰는 결정적인 잣대.
- **기준선(baseline)**: 비교의 출발점(여기서는 전부 훑는 NaiveSpatialIndex).
- **JIT**: 자바가 실행 중에 코드를 기계어로 다시 굽는 장치. 실행 시간을 들쭉날쭉하게 만든다.
- **오버플로(overflow)**: 계산 결과가 자료형이 담을 수 있는 범위를 넘치는 것. int 곱은 long으로 올려 막는다.
- **재귀**: 함수가 자기 자신을 호출해, 큰 문제를 같은 모양의 작은 문제로 줄여 푸는 방식.
- **O(log n), O(n) (빅오 표기)**: 입력이 커질 때 비용이 늘어나는 속도. log n은 반씩 줄여가는 속도, n은 비례.
