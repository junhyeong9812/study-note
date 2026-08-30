# data-structure/22-sparse-table — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — StaticRangeQuery (`src/main/java/com/datastructure/sparsetable/StaticRangeQuery.java`)

- `int size()`
- `long query(int from, int to)`
- `long get(int index)`

## 구현 — SparseTable (`src/main/java/com/datastructure/sparsetable/SparseTable.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `int n` 역할:
- `int levels` 역할:
- `long[][] table` 역할 (`table[k][i]` 가 덮는 구간):
- `int[] log` 역할:
- `long[] values` 역할:
- 요구 조건 — 멱등성 `f(x, x) = x` 가 필요한 이유:

### `protected SparseTable(long[] initial)`

- 하는 일:
- 논리:
- 비용(왜):

### `protected abstract long combine(long a, long b)`

- 하는 일:
- 논리:

### `protected abstract long identity()`

- 하는 일:
- 논리(13번과 달리 **빈 구간에서만** 쓰인다는 것 — 그래서 틀려도 티가 덜 나는 위험):

### `static int[] buildLogTable(int n)` (TODO)

- 하는 일:
- 논리(`Math.log` 를 쓰지 않는 진짜 이유 — 오차가 아니라 비용):
- 비용(왜):

### `private void build()` (TODO)

- 하는 일:
- 논리(2의 거듭제곱 길이 구간을 층마다 쌓는 것):
- 비용(왜):

### `public long query(int from, int to)` (TODO)

- 하는 일:
- 논리(두 조각으로 덮기 · 두 조각이 겹친다는 것 · `+1` 두 개의 함정):
- 비용(왜 O(1) 인가):

### `public long get(int index)` / `public int size()`

- 하는 일:
- 비용(왜):

### `public int levels()` / `public int unitCount()`

- 하는 일:
- 논리(메모리·걸음 수 측정용):
- 비용(왜):

## 구현 — MinSparseTable (`src/main/java/com/datastructure/sparsetable/MinSparseTable.java`)

### `protected long combine(long a, long b)` (TODO)

- 하는 일:
- 논리:

### `protected long identity()` (TODO)

- 하는 일:
- 논리:

## 구현 — MaxSparseTable (`src/main/java/com/datastructure/sparsetable/MaxSparseTable.java`)

### `protected long combine(long a, long b)` (TODO)

- 하는 일:
- 논리:

### `protected long identity()` (TODO)

- 하는 일:
- 논리:

## 구현 — GcdSparseTable (`src/main/java/com/datastructure/sparsetable/GcdSparseTable.java`)

### `protected long combine(long a, long b)` (TODO)

- 하는 일:
- 논리(유클리드 호제법):
- 비용(왜):

### `protected long identity()` (TODO)

- 하는 일:
- 논리:

## 구현 — DisjointSparseTable (`src/main/java/com/datastructure/sparsetable/DisjointSparseTable.java`)

### `필드`

- `int n` 역할:
- `int width` (패딩된 폭) 역할:
- `int levels` 역할:
- `long[][] table` 역할:
- `long[] values` 역할:
- `long identity` 역할:
- `LongBinaryOperator combine` 역할(상속 대신 인자로 받는 것 — 13번 GenericSegmentTree 와의 대비):

### `public DisjointSparseTable(long[] initial)` / `public DisjointSparseTable(long[] initial, long identity, LongBinaryOperator combine)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void build()` (TODO)

- 하는 일:
- 논리(층마다 블록의 가운데를 기준으로 좌우로 누적 · 누적 방향과 인자 순서가 비가환 연산에서만 티가 나는 것):
- 비용(왜):

### `public long query(int from, int to)` (TODO)

- 하는 일:
- 논리(두 조각이 **겹치지 않으므로** combine 이 무엇이든 되는 이유 · `l == r` 을 따로 빼야 하는 이유):
- 비용(왜):

### `public long get(int index)` / `public int size()` / `public int levels()` / `public int unitCount()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 13번 세그먼트 트리 (결합법칙) | | | |
| 17번 펜윅 트리 (역연산) | | | |
| SparseTable (멱등성) | | | |
| DisjointSparseTable (겹치지 않는 두 조각) | | | |
| 04번 덱 (고정 크기 슬라이딩 윈도우) | | | |

## 문제 — SparseTableProblems (`src/main/java/com/datastructure/sparsetable/SparseTableProblems.java`)

### 문제 1. 슬라이딩 윈도우 최솟값 — `static int[] slidingWindowMin(int[] values, int k)`

> 문제 설명: 크기 k 인 창을 왼쪽부터 한 칸씩 옮기며 각 창의 최솟값을 모은다.
> 결과 길이는 `n - k + 1` 이다.
> 04번에서 같은 문제를 덱으로 풀었다. 그쪽이 O(n) 이라 더 빠르다.
> 그런데 덱 풀이는 창이 한 방향으로만 움직이고 k 가 고정이라는 조건에 기대고 있다.
> k 가 바뀌면 처음부터 다시 훑어야 한다.
> 희소 테이블은 전처리 O(n log n) 을 먼저 내고 그 뒤로는 아무 구간이나 O(1) 이다.
> 창 크기가 여럿이거나 구간이 제멋대로면 이쪽이 이긴다.
> **같은 문제라도 질의 패턴이 자료구조를 정한다.**
> (values 가 null 이거나 비었으면 IllegalArgumentException, k <= 0 또는 k > n 이면 IllegalArgumentException)

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 구간 gcd 질의 — `static long[] rangeGcdQueries(int[] values, int[][] queries)`

> 문제 설명: 질의가 아주 많을 때의 구간 gcd. `queries[i] = {from, to}` 이고 결과의 i번째가 그 구간의 gcd 다.
> 여기가 이 자료구조를 고르는 이유가 드러나는 자리다.
> 세그먼트 트리로 하면 질의마다 O(log n) 이라 전체가 O(q log n) 이다.
> 희소 테이블은 O(n log n + q) 다. q 가 n 보다 훨씬 크면 그 차이가 그대로 남는다.
> (테스트가 걸음 수를 세어 보여준다 — n=4096, q=2000 에서 18배)
> 값이 바뀌지 않는다는 전제가 깔려 있다. 하나라도 바뀌면 전부 다시 지어야 한다.
> (values 가 null/빈 배열이면 IllegalArgumentException, queries 가 null 이면 IllegalArgumentException.
>  질의 검증: q 가 null 이거나 길이가 2 가 아니거나 `q[0] < 0` · `q[1] >= n` · `q[0] > q[1]` 이면 IllegalArgumentException)
> 생각할 것: 검증을 빼먹으면 무엇이 예외로 새어 나가고 무엇이 조용히 답이 되는가 — 어느 쪽이 더 나쁜가.

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/22-sparse-table/README.md`
- 구현: `/home/jun/project/myway/data-structure/22-sparse-table/src/main/java/com/datastructure/sparsetable/`
- 테스트: `/home/jun/project/myway/data-structure/22-sparse-table/src/test/java/com/datastructure/sparsetable/`
- 정답 구현: `/home/jun/project/myway/data-structure/22-sparse-table/impl/`
