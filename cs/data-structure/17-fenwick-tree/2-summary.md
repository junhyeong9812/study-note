# data-structure/17-fenwick-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — PrefixSumTree (`src/main/java/com/datastructure/fenwick/PrefixSumTree.java`)

- `int size()`
- `void add(int index, long delta)`
- `void set(int index, long value)`
- `long get(int index)`
- `long prefixSum(int index)`
- `long rangeSum(int from, int to)`

## 구현 — FenwickTree (`src/main/java/com/datastructure/fenwick/FenwickTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `int n` 역할:
- `long[] tree` (크기 n+1) 역할:
- `tree[i]` 가 덮는 구간의 규칙 (`i & -i`):

### `public FenwickTree(int size)` / `public FenwickTree(long[] initial)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void buildFrom(long[] values)` (TODO)

- 하는 일:
- 논리(왜 한 번 훑기로 되는가):
- 비용(왜):

### `public void add(int index, long delta)` (TODO)

- 하는 일:
- 논리(`x += x & -x` 로 올라가는 이유):
- 비용(왜):

### `public long prefixSum(int index)` (TODO)

- 하는 일:
- 논리(`x -= x & -x` 로 내려가는 이유 · 걸음 수 = 1비트 개수):
- 비용(왜):

### `public long rangeSum(int from, int to)` (TODO)

- 하는 일:
- 논리(이 한 줄이 자료구조의 한계를 정하는 이유):
- 비용(왜):

### `public void set(int index, long value)` (TODO)

- 하는 일:
- 논리(대입을 직접 못 하는 이유):
- 비용(왜):

### `public int findPrefixIndex(long target)` (TODO)

- 하는 일:
- 논리(트리 칸 구조가 이미 이진 탐색의 모양이라는 것):
- 비용(왜):

### `public long get(int index)`

- 하는 일:
- 비용(왜):

### `public int size()`

- 하는 일:
- 비용(왜):

## 구현 — FenwickTree2D (`src/main/java/com/datastructure/fenwick/FenwickTree2D.java`)

### `필드`

- `int rows` / `int cols` 역할:
- `long[][] tree` (크기 (rows+1) x (cols+1)) 역할:

### `public FenwickTree2D(int rows, int cols)`

- 하는 일:
- 비용(왜):

### `public void add(int row, int col, long delta)` (TODO)

- 하는 일:
- 논리(안쪽 루프의 시작값을 매번 다시 잡아야 하는 이유):
- 비용(왜):

### `public long prefixSum(int row, int col)` (TODO)

- 하는 일:
- 논리(음수 경계에서 0 을 반환하는 것이 왜 포함-배제를 성립시키는가):
- 비용(왜):

### `public long rangeSum(int r1, int c1, int r2, int c2)` (TODO)

- 하는 일:
- 논리(포함-배제 · 마지막 항의 부호):
- 비용(왜):

### `public long get(int row, int col)` / `public void set(int row, int col, long value)`

- 하는 일:
- 비용(왜):

### `public int rows()` / `public int cols()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 13번 세그먼트 트리 (모노이드 일반성) | | | |
| FenwickTree (역연산 있는 연산만) | | | |
| FenwickTree2D (차원 겹치기) | | | |
| 누적합 배열 (갱신 없음) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/17-fenwick-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/17-fenwick-tree/src/main/java/com/datastructure/fenwick/`
- 테스트: `/home/jun/project/myway/data-structure/17-fenwick-tree/src/test/java/com/datastructure/fenwick/`
- 정답 구현: `/home/jun/project/myway/data-structure/17-fenwick-tree/impl/`
