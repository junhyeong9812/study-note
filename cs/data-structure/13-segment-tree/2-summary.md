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
