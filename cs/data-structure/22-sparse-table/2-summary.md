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

### 구조

```
table[k][i] = i 에서 시작하는 길이 2^k 구간 [i, i + 2^k - 1] 의 답 (0-base, 양끝 포함)

SparseTable (n = 8, min 을 예로)
+-------------------------------------------------------+
| n = 8            (원소 수)                             |
| levels = 4       (= log[n] + 1 = 3 + 1, 층 수)         |
| table ---+       (long[levels][n] - [층 k][시작칸 i])  |
| log ---+         (log[x] = floor(log2 x) 를 미리 채운 표) |
| values           (원본 복사본, get 용)                 |
+--------|----------------------------------------------+
         v
  values   idx   0    1    2    3    4    5    6    7
              +----+----+----+----+----+----+----+----+
              |  5 |  2 |  9 |  1 |  7 |  4 |  6 |  3 |
              +----+----+----+----+----+----+----+----+

  k = 0 : 길이 1 = values 그대로
      i ->    0    1    2    3    4    5    6    7
           +----+----+----+----+----+----+----+----+
 table[0]  |  5 |  2 |  9 |  1 |  7 |  4 |  6 |  3 |
           +----+----+----+----+----+----+----+----+

  k = 1 : 길이 2 = [i, i+1]        i + 2 <= 8 인 i 까지만 채운다 (i = 0..6)
           +----+----+----+----+----+----+----+
 table[1]  |  2 |  2 |  1 |  1 |  4 |  4 |  3 |
           +----+----+----+----+----+----+----+
             ^ [0..1]  ^ [2..3]            ^ [6..7]

  k = 2 : 길이 4 = [i, i+3]        i = 0..4
           +----+----+----+----+----+
 table[2]  |  1 |  1 |  1 |  1 |  3 |
           +----+----+----+----+----+
             ^ [0..3]            ^ [4..7]

  k = 3 : 길이 8 = [i, i+7]        i = 0 하나뿐
           +----+
 table[3]  |  1 |   [0..7]
           +----+

  한 칸이 덮는 구간 (k = 2, i = 1 을 예로)
      idx     0    1    2    3    4    5    6    7
           +----+----+----+----+----+----+----+----+
           |    |    |    |    |    |    |    |    |
           +----+----+----+----+----+----+----+----+
                |<-- table[2][1] -->|   -> [1..4] 를 덮는다

  칸 수 = levels * n = O(n log n) 메모리.
  값을 나중에 바꿀 수 없다 - 한 원소를 고치면 그 원소를 덮는 모든 층의 칸이 틀어진다(정적 구조).
```

### 동작 — 전처리

```
build() : 아래층 칸 두 개를 이어 붙여 위층 칸 하나를 만든다 (배증, doubling)

  table[k][i] = combine( table[k-1][i],  table[k-1][i + half] ),   half = 1 << (k-1)
                              ^ 앞 절반          ^ 뒤 절반 (half 칸 뒤에서 시작)

  k = 2, i = 1 을 만드는 장면 : 길이 4 = 길이 2 짜리 두 개
      half = 1 << (2-1) = 2  ->  i + half = 1 + 2 = 3
                +---------+   +---------+
      k = 1     | [1..2]  |   | [3..4]  |     table[1][1] = 2,  table[1][3] = 1
                |   = 2   |   |   = 1   |
                +---------+   +---------+
                     \             /
                    combine(2, 1) = min = 1
                            v
                +-----------------------+
      k = 2     |       [1..4] = 1      |     table[2][1]
                +-----------------------+

  k = 0 은 values 를 그대로 복사. k 는 1 부터 levels-1 까지,
  i 는 i + (1 << k) <= n 인 동안만 (구간이 배열 밖으로 나가면 안 만든다).
  붙이는 두 조각이 딱 맞닿아 겹치지 않으므로 전처리에서는 어떤 연산이든 문제없다.
  칸 수만큼 일하니 O(n log n) 시간, O(n log n) 메모리.

  log 표는 log[i] = log[i >> 1] + 1 로 미리 만들어 둔다(i = 2..n).
  쿼리에서 log2 를 매번 계산하지 않으려는 것 - 표를 보면 O(1).
```

### 동작 — 조회

```
query(from, to) : 길이 len = to - from + 1,  k = log[len] = floor(log2 len)
    [from, from + 2^k - 1] 과 [to - 2^k + 1, to] 두 칸을 combine 한다. O(1)

  query(1, 6) : len = 6, k = log[6] = 2, 2^k = 4
     idx     0    1    2    3    4    5    6    7
          +----+----+----+----+----+----+----+----+
          |  5 |  2 |  9 |  1 |  7 |  4 |  6 |  3 |
          +----+----+----+----+----+----+----+----+
               |<-- table[2][1] -->|                  -> [1..4]
                         |<-- table[2][3] -->|        -> [3..6]
                         |<------->|   여기가 겹친다 - 3, 4 가 두 번 들어간다

     답 = combine( table[2][1], table[2][3] ) = min(1, 1) = 1
     실제 values[1..6] 의 min = min(2, 9, 1, 7, 4, 6) = 1

  왜 겹쳐도 되나
     min(a, a) = a  - 같은 값을 두 번 넣어도 답이 그대로다(멱등, idempotent).
     max, gcd 도 같다. 그래서 중복 계산이 답을 바꾸지 않는다.

  왜 두 칸이면 충분한가
     2^k <= len < 2^(k+1) 이므로 2^k > len/2 - 각 조각이 구간의 절반을 넘게 덮는다.
     왼쪽 끝에 붙인 조각과 오른쪽 끝에 붙인 조각이 가운데서 만나 빈틈이 없고,
     두 조각 모두 [from, to] 안에 있으니 밖의 값이 섞이지도 않는다.
     길이가 얼마든 combine 은 딱 2회 -> O(1).

  합(sum)에는 못 쓴다
     sum(a, a) = 2a  - 겹친 칸이 두 번 더해져 답이 커진다.
     위 예라면 3, 4 번 원소가 두 번 세어진다. 그래서 합은 DisjointSparseTable 로 간다.

  from > to 면 identity() 를 돌려준다 (min 은 Long.MAX_VALUE, max 는 Long.MIN_VALUE).
```

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

### 구조

```
gcd 도 멱등이라 SparseTable 의 "겹쳐도 되는" 조회를 그대로 쓴다 (별도 구조가 필요 없다)

     gcd(a, a) = a     -> 두 번 세도 답이 그대로   (min / max 와 같은 이유)
     sum(a, a) = 2a    -> 겹치면 틀린다            (그래서 합만 다른 구조가 필요하다)

  values   idx   0    1    2    3
              +----+----+----+----+
              | 12 | 18 |  6 | 24 |
              +----+----+----+----+

  query(0, 2) : len = 3, k = log[3] = 1, 2^k = 2
              |<------->|            -> [0..1]
                   |<------->|       -> [1..2]
                   |<-->|            -> 여기가 겹친다 (18 이 두 번)

     combine( gcd(12,18), gcd(18,6) ) = gcd(6, 6) = 6
     한 번만 세도  gcd(12, 18, 6) = 6  -  같다

  identity() = 0 : gcd(x, 0) = x 라서 빈 구간의 항등원은 0 이다
  combine 은 유클리드 호제법이라 상수 시간이 아니다. 조회는 combine 2회로 여전히
  "O(1) 번" 이지만 각 호출에 O(log 값) 이 붙고, 전처리도 그만큼 무거워진다.
```

### `protected long combine(long a, long b)` (TODO)

- 하는 일:
- 논리(유클리드 호제법):
- 비용(왜):

### `protected long identity()` (TODO)

- 하는 일:
- 논리:

## 구현 — DisjointSparseTable (`src/main/java/com/datastructure/sparsetable/DisjointSparseTable.java`)

### 구조

```
구간을 겹치지 않게 두 조각으로 나눈다 - 그래서 합처럼 멱등하지 않은 연산도 O(1)

DisjointSparseTable (n = 8, 기본 combine = 합, identity = 0)
+---------------------------------------------------------+
| n = 8                                                   |
| width = 8      (n 이상인 2의 거듭제곱. 남는 칸은 identity 로 채운다) |
| levels = 3     (width 를 1 이 될 때까지 반으로 접은 횟수) |
| table ---+     (long[levels][width])                    |
| combine, identity  (생성자에서 받는다 - 기본은 Long::sum, 0) |
+----------|----------------------------------------------+
           v
  values   idx   0    1    2    3    4    5    6    7
              +----+----+----+----+----+----+----+----+
              |  5 |  2 |  9 |  1 |  7 |  4 |  6 |  3 |
              +----+----+----+----+----+----+----+----+

층마다 중앙선을 긋고, 중앙에서 바깥으로 향하는 누적값을 미리 적어 둔다.
(스파스 테이블은 "i 에서 시작하는 길이 2^k" 였지만, 여기는 "i 에서 중앙까지" 다)

  level 2 (range = 4) : 중앙 center = 4 하나. 블록 [0..7]
              idx    0    1    2    3    4    5    6    7
                  +----+----+----+----+----+----+----+----+
     table[2]     | 17 | 12 | 10 |  1 |  7 | 11 | 17 | 20 |
                  +----+----+----+----+----+----+----+----+
                  <----- [i..3] -----><----- [4..i] ----->
                                      ^ center = 4
        왼쪽 칸 i 는 [i..center-1] 의 합, 오른쪽 칸 i 는 [center..i] 의 합
        예) table[2][1] = 2+9+1 = 12,   table[2][6] = 7+4+6 = 17

  level 1 (range = 2) : 중앙 center = 2 와 6. 블록 [0..3], [4..7]
              idx    0    1    2    3    4    5    6    7
                  +----+----+----+----+----+----+----+----+
     table[1]     |  7 |  2 |  9 | 10 | 11 |  4 |  6 |  9 |
                  +----+----+----+----+----+----+----+----+
                  <-[i..1]-><-[2..i]-><-[i..5]-><-[6..i]->
                            ^ center = 2        ^ center = 6

  level 0 (range = 1) : 중앙 center = 1, 3, 5, 7. 사실상 원소 하나씩
              idx    0    1    2    3    4    5    6    7
                  +----+----+----+----+----+----+----+----+
     table[0]     |  5 |  2 |  9 |  1 |  7 |  4 |  6 |  3 |
                  +----+----+----+----+----+----+----+----+

  칸 수 = levels * width = O(n log n) - 스파스 테이블과 같은 규모다.
  대신 여기 저장되는 건 "고정 길이 구간의 답"이 아니라 "중앙까지의 누적"이다.
```

### 동작 — 조회

```
query(from, to) : from 과 to 가 처음으로 갈라지는 비트 자리가 곧 층 번호다
    level = 31 - numberOfLeadingZeros(from ^ to)     (= floor(log2(from ^ to)))
    답 = combine( table[level][from],  table[level][to] )        칸 두 개, O(1)

  query(1, 6)
     1 = 001,  6 = 110  ->  1 ^ 6 = 111  ->  가장 높은 1 은 2번 자리  ->  level = 2
     level 2 의 중앙은 4. 갈림 비트가 2번이라는 건 from 은 중앙 왼쪽,
     to 는 중앙 오른쪽에 있다는 뜻이다.

     idx     0    1    2    3    4    5    6    7
          +----+----+----+----+----+----+----+----+
          | 17 | 12 | 10 |  1 |  7 | 11 | 17 | 20 |   table[2]
          +----+----+----+----+----+----+----+----+
                 ^                        ^
        table[2][1] = [1..3] = 12    table[2][6] = [4..6] = 17

               |<--- [1..3] --->|<--- [4..6] --->|
           맞닿기만 하고 겹치는 칸이 하나도 없다

     답 = 12 + 17 = 29     (실제 2+9+1+7+4+6 = 29)

  왜 겹치지 않나
     같은 층에서 from 과 to 의 그 비트가 서로 다르다는 것은,
     그 층의 블록에서 from 은 왼쪽 절반, to 는 오른쪽 절반에 있다는 뜻이다.
     왼쪽 칸은 "중앙 직전까지", 오른쪽 칸은 "중앙부터"를 담으므로 정확히 맞물린다.
     겹치는 칸이 없으니 sum 처럼 멱등하지 않은 연산(합, 곱, 행렬곱)도 O(1) 로 답이 나온다.

  from == to 면 갈라지는 비트가 없다(from ^ to = 0) -> values[from] 을 그대로 돌려준다.
  from > to 면 identity 를 돌려준다.

  min/max 라면 SparseTable 로도 되지만, 합에는 이 구조가 필요하다는 것이 갈림점이다.
```

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
