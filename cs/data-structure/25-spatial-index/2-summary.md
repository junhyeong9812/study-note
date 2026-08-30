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
