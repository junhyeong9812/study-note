# data-structure/30-interval-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — IntervalStore (`src/main/java/com/datastructure/interval/IntervalStore.java`)

- `boolean insert(Interval iv)`
- `boolean remove(Interval iv)`
- `int size()`
- `void clear()`
- `default boolean isEmpty()`
- `Interval findAny(Interval query)`
- `List<Interval> findAll(Interval query)`
- `boolean anyOverlaps(Interval query)`
- `List<Interval> toList()`

## 계약 — VisitCounting (`src/main/java/com/datastructure/interval/VisitCounting.java`)

- `long visitedNodes()`

## 구현 — Interval (`src/main/java/com/datastructure/interval/Interval.java`)

### 필드
- `start` — 역할:
- `end` — 역할:

### `Interval(long start, long end)`
- 하는 일:
- 논리:
- 비용(왜):

### `static Interval of(long start, long end)`
- 하는 일:
- 논리:
- 비용(왜):

### `long length()`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean overlaps(Interval other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(long point)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int compareTo(Interval other)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — NaiveIntervalStore (`src/main/java/com/datastructure/interval/NaiveIntervalStore.java`)

### 필드
- `intervals` — 역할:
- `visitedNodes` — 역할:

### `boolean insert(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

### `Interval findAny(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> findAll(Interval query)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean anyOverlaps(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> toList()`
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedNodes()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — IntervalTree (`src/main/java/com/datastructure/interval/IntervalTree.java`)

### 필드
- `root` — 역할:
- `size` — 역할:
- `visitedNodes` — 역할:
- `Node.interval` — 역할:
- `Node.maxEnd` — 역할:
- `Node.left` / `Node.right` — 역할:

### `static long maxEndOf(Node node)`
- 하는 일:
- 논리:
- 비용(왜):

### `static void recomputeMaxEnd(Node node)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean insert(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node insertInto(Node node, Interval iv)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `Interval findAny(Interval query)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> findAll(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `void collectFrom(Node node, Interval query, List<Interval> out)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean anyOverlaps(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node removeFrom(Node node, Interval iv)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int height()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> toList()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedNodes()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — CoordinateCompressor (`src/main/java/com/datastructure/interval/CoordinateCompressor.java`)

### 필드
- `coordinates` — 역할:

### `CoordinateCompressor(List<Interval> intervals)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int size()`
- 하는 일:
- 논리:
- 비용(왜):

### `int compressPoint(long value)`
- 하는 일:
- 논리:
- 비용(왜):

### `long decompressPoint(int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `Interval compress(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `Interval decompress(Interval compressed)`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| NaiveIntervalStore | | | |
| IntervalTree | | | |
| 정렬 + 스위핑 (IntervalProblems) | | | |

## 문제 — IntervalProblems (`src/main/java/com/datastructure/interval/IntervalProblems.java`)

### 문제 1. merge — 겹치거나 맞닿은 구간을 합친다
> 문제 설명: 겹치거나 맞닿은 구간을 합친다. 결과는 start 오름차순이고 서로 안 겹친다.
> `intervals` 가 null 이면 IllegalArgumentException, 비어 있으면 빈 목록.
>
> 생각할 것
> - 정렬하고 나면 지금 들고 있는 하나와 다음 하나만 보면 된다. 왜 그것으로 충분한가.
> - 합치는 조건이 `overlaps` 와 다르다. `[9,11)` 과 `[11,13)` 은 안 겹치는데, 둘을 합한 점의 집합은 `[9,13)` 과 정확히 같다. 반개구간이라 빈틈이 없기 때문이다.
> - 다음 구간이 앞 구간 안에 통째로 들어가 있으면 end 가 줄면 안 된다.
> - 마지막 하나는 반복문 안에서 안 나온다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. maxConcurrent — 동시에 겹치는 구간의 최대 개수
> 문제 설명: 동시에 겹치는 구간의 최대 개수. 회의실이 몇 개 필요한가.
> 시작 이벤트와 끝 이벤트를 각각 정렬해놓고 이른 것부터 처리하는 스위핑이다.
> 빈 목록이면 0, null 이면 IllegalArgumentException.
>
> 생각할 것
> - 지금 열려 있는 개수를 세면서 그 최댓값을 기억한다.
> - 좌표가 같을 때 무엇을 먼저 처리해야 하는가. 반개구간이므로 `[9,11)` 이 끝나는 11 시에 `[11,13)` 이 시작해도 그 순간 방은 하나면 된다. 이 함정이 이 문제의 전부다.
> - 시작을 다 처리하면 끝난다. 남은 끝 이벤트는 최댓값을 못 바꾼다.

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/30-interval-tree/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/30-interval-tree/src/main/java/com/datastructure/interval/`
- 테스트: `/home/jun/project/myway/data-structure/30-interval-tree/src/test/java/com/datastructure/interval/`
- 정답 구현: `/home/jun/project/myway/data-structure/30-interval-tree/impl/`
