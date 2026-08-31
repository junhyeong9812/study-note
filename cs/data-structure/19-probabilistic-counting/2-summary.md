# data-structure/19-probabilistic-counting — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — FrequencyEstimator (`src/main/java/com/datastructure/sketch/FrequencyEstimator.java`)

- `void add(int item)`
- `void add(int item, long count)`
- `long estimateCount(int item)`
- `long totalCount()`
- `long memoryBytes()`

## 계약 — CardinalityEstimator (`src/main/java/com/datastructure/sketch/CardinalityEstimator.java`)

- `void add(int item)`
- `long estimate()`
- `long memoryBytes()`

## 구현 — ExactCounter (`src/main/java/com/datastructure/sketch/ExactCounter.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
HashMap<Integer, Long> - 원소마다 칸을 하나씩 잡고 정확한 횟수를 센다

  ExactCounter : 원소 종류 하나마다 엔트리 하나
    counts = { 7 -> 4,   19 -> 3,   23 -> 9,   ... }
      +------------+  +------------+  +------------+
      | key      7 |  | key     19 |  | key     23 |   ...  종류 수만큼 계속 늘어난다
      | value    4 |  | value    3 |  | value    9 |
      +------------+  +------------+  +------------+
      memoryBytes() = distinctCount() * 64 byte

  CountMinSketch : 칸 수가 처음부터 고정 (width x depth = 8 x 4 = 32 칸)
      +--+--+--+--+--+--+--+--+
      +--+--+--+--+--+--+--+--+   원소가 몇 종류 들어와도
      +--+--+--+--+--+--+--+--+   표 크기는 그대로다
      +--+--+--+--+--+--+--+--+

  종류가 1억 개면 엔트리도 1억 개 - 메모리가 원소 수에 비례해 커진다.
  대신 estimateCount 는 오차 없는 정확한 값이고, 삭제/감소도 자연스럽다.
  스케치는 그 반대다 : 메모리 고정, 답은 과대 쪽으로 틀릴 수 있음.
  둘의 답을 맞춰 보는 기준(정답지) 역할로도 쓴다.
```

### `필드`

- `static final long BYTES_PER_ENTRY = 64` 역할:
- `Map<Integer, Long> counts` 역할:
- `long total` 역할:

### `public void add(int item, long count)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public void add(int item)`

- 하는 일:
- 비용(왜):

### `public long estimateCount(int item)` / `public long totalCount()`

- 하는 일:
- 비용(왜):

### `public long memoryBytes()` / `public int distinctCount()`

- 하는 일:
- 논리(기준선으로서 무엇을 재려고 있는가):
- 비용(왜):

## 구현 — ExactCardinality (`src/main/java/com/datastructure/sketch/ExactCardinality.java`)

### 구조

```
HashSet<Integer> - 본 원소를 전부 담아 두고 크기를 답으로 낸다

  ExactCardinality : 본 원소를 전부 들고 있는다
    seen = { 7,  19,  23,  ... }
      +----+  +----+  +----+
      |  7 |  | 19 |  | 23 |   ...   서로 다른 원소 수만큼 자란다
      +----+  +----+  +----+
      memoryBytes() = seen.size() * 48 byte

  HyperLogLog (p = 4) : 버킷 16칸으로 고정
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |   registers = byte[16], 16 byte 고정
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

  중복을 걸러 내려면 "이미 봤는지"를 알아야 하고, 그러려면 본 것을 다 들고 있어야 한다.
  -> 정확하지만 메모리가 원소 종류 수에 비례한다.
  HyperLogLog 는 원소를 버리고 해시의 통계만 남겨 이 비례를 끊는다.
  대신 답은 추정값이고, 여기서는 estimate() 가 곧 정답이라 오차 비교의 기준이 된다.
```

### `필드`

- `static final long BYTES_PER_ELEMENT = 48` 역할:
- `Set<Integer> seen` 역할:

### `public void add(int item)` (TODO)

- 하는 일:
- 비용(왜):

### `public long estimate()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

## 구현 — CountMinSketch (`src/main/java/com/datastructure/sketch/CountMinSketch.java`)

### 구조

```
CountMinSketch (depth = 4 행, width = 8 열)
+-----------------------------------------------------+
| width = 8      (한 행의 칸 수)                       |
| depth = 4      (행 수 = 해시 개수)                   |
| seed           (해시 섞을 때 쓰는 값)                |
| total          (지금까지 더한 총합)                  |
| table ---+     (long[depth][width] - [행][열])       |
+----------|------------------------------------------+
           v
   열 ->      0    1    2    3    4    5    6    7
           +----+----+----+----+----+----+----+----+
   행 0    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |   <- 해시 0 이 쓰는 행
           +----+----+----+----+----+----+----+----+
   행 1    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |   <- 해시 1
           +----+----+----+----+----+----+----+----+
   행 2    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |   <- 해시 2
           +----+----+----+----+----+----+----+----+
   행 3    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |   <- 해시 3
           +----+----+----+----+----+----+----+----+

   원소 하나는 행마다 정확히 한 칸씩, 모두 depth 개 칸에 대응된다.
   원소를 저장하지 않는다 - 어떤 원소가 들어왔는지는 표에 남지 않는다.

   indexes(x) : 해시 하나로 depth 개 열을 만든다
       h  = mix64(x ^ seed)
       h1 = h 의 아래 32비트,   h2 = h 의 위 32비트 (0 이면 1 로 바꾼다)
       행 i 의 열 = floorMod(h1 + i * h2, width)

   메모리 = width * depth * 8 byte 로 고정 - 원소가 몇 종류 들어오든 늘지 않는다
   폭과 깊이는 오차에서 역산한다 : width = ceil(e / epsilon),  depth = ceil(ln(1 / delta))
```

### 동작 — 추가

```
add(x, c) : x 가 대응되는 칸을 행마다 하나씩 골라 전부 c 만큼 올린다. O(depth)
            total 도 c 만큼 늘어난다. 칸을 덮어쓰는 게 아니라 더한다.

  indexes(A) = [2, 5, 0, 6]  이라 하고 add(A) 한 번
                     before                                  after
            0  1  2  3  4  5  6  7                   0  1  2  3  4  5  6  7
          +--+--+--+--+--+--+--+--+                +--+--+--+--+--+--+--+--+
  행 0    | 0| 0| 0| 0| 0| 0| 0| 0|                | 0| 0| 1| 0| 0| 0| 0| 0|
          +--+--+--+--+--+--+--+--+                +--+--+--+--+--+--+--+--+
  행 1    | 0| 0| 0| 0| 0| 0| 0| 0|      ->        | 0| 0| 0| 0| 0| 1| 0| 0|
          +--+--+--+--+--+--+--+--+                +--+--+--+--+--+--+--+--+
  행 2    | 0| 0| 0| 0| 0| 0| 0| 0|                | 1| 0| 0| 0| 0| 0| 0| 0|
          +--+--+--+--+--+--+--+--+                +--+--+--+--+--+--+--+--+
  행 3    | 0| 0| 0| 0| 0| 0| 0| 0|                | 0| 0| 0| 0| 0| 0| 1| 0|
          +--+--+--+--+--+--+--+--+                +--+--+--+--+--+--+--+--+
     행 0 은 열 2, 행 1 은 열 5, 행 2 는 열 0, 행 3 은 열 6 - 행마다 정확히 한 칸씩 +1

  충돌 : indexes(B) = [2, 1, 4, 3] 이라 하자. 행 0 에서 B 도 열 2 를 쓴다.
  A 를 4번, B 를 3번 넣은 뒤
            0  1  2  3  4  5  6  7
          +--+--+--+--+--+--+--+--+
  행 0    | 0| 0| 7| 0| 0| 0| 0| 0|   <- A 의 4 와 B 의 3 이 한 칸에 섞였다
          +--+--+--+--+--+--+--+--+
  행 1    | 0| 3| 0| 0| 0| 4| 0| 0|      (A 는 열 5 = 4,  B 는 열 1 = 3)
          +--+--+--+--+--+--+--+--+
  행 2    | 4| 0| 0| 0| 3| 0| 0| 0|      (A 는 열 0 = 4,  B 는 열 4 = 3)
          +--+--+--+--+--+--+--+--+
  행 3    | 0| 0| 0| 3| 0| 0| 4| 0|      (A 는 열 6 = 4,  B 는 열 3 = 3)
          +--+--+--+--+--+--+--+--+

  칸은 남의 count 를 얹어 받을 뿐, 빼앗기지는 않는다
  -> 어떤 칸이든 값 >= 그 원소의 진짜 빈도. 오차는 항상 "많게" 한 방향뿐이다.
  삭제가 없는 이유도 같다 - 한 칸을 빼면 거기 섞인 남의 몫까지 깎여 과소가 생긴다.
```

### 동작 — 조회

```
estimateCount(x) : 같은 depth 개 칸을 다시 읽어 그 중 최솟값을 답으로 낸다. O(depth)

  estimateCount(A),  indexes(A) = [2, 5, 0, 6]
            0  1  2  3  4  5  6  7
          +--+--+--+--+--+--+--+--+
  행 0    | 0| 0| 7| 0| 0| 0| 0| 0|   ->  행 0 열 2 = 7   (B 와 겹쳐 부풀었다)
          +--+--+--+--+--+--+--+--+
  행 1    | 0| 3| 0| 0| 0| 4| 0| 0|   ->  행 1 열 5 = 4
          +--+--+--+--+--+--+--+--+
  행 2    | 4| 0| 0| 0| 3| 0| 0| 0|   ->  행 2 열 0 = 4
          +--+--+--+--+--+--+--+--+
  행 3    | 0| 0| 0| 3| 0| 0| 4| 0|   ->  행 3 열 6 = 4
          +--+--+--+--+--+--+--+--+
                                        min(7, 4, 4, 4) = 4  = A 의 진짜 빈도

  왜 min 인가
    칸 값 = (그 원소의 진짜 빈도) + (그 칸에서 겹친 남들의 몫 >= 0)
    -> 어느 칸도 진짜보다 작을 수 없다. 즉 답은 절대 과소가 아니다.
       한 행이라도 안 겹치면 그 칸이 정확한 값이고, min 이 그 칸을 집어낸다.
       모든 행에서 동시에 겹쳐야만 답이 커진다.

    열이 많을수록(width) 한 행에서 겹칠 확률이 낮아지고,
    행이 많을수록(depth) "전 행에서 동시에 겹칠" 확률이 낮아진다.
    오차 상한 errorBound() = epsilon * total,   epsilon = e / width,  delta = e^(-depth)

  A 대신 한 번도 넣지 않은 원소를 물어도 0 이 아닌 값이 나올 수 있다(과대).
  하지만 많이 들어온 원소를 놓치는 일은 없다 - heavy hitter 찾기에 맞는 성질이다.
```

### `필드`

- `static final int MAX_WIDTH` / `MAX_DEPTH` 역할:
- `int width` (w) 역할:
- `int depth` (d) 역할:
- `long seed` 역할(무작위를 주입받는 이유):
- `long[][] table` 역할:
- `long total` 역할:

### `public CountMinSketch(double epsilon, double delta)` / `public CountMinSketch(int width, int depth, long seed)`

- 하는 일:
- 논리(w 가 오차를, d 가 신뢰도를 정한다는 것):
- 비용(왜):

### `static int widthFor(double epsilon)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static int depthFor(double delta)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static long mix64(long z)`

- 하는 일:
- 논리:
- 비용(왜):

### `int[] indexes(int item)` (TODO)

- 하는 일:
- 논리(11번과 똑같은 이중 해싱 · `h2 == 0` 이면 무슨 일이 생기는가):
- 비용(왜):

### `public void add(int item, long count)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public long estimateCount(int item)` (TODO)

- 하는 일:
- 논리(왜 최소인가 · 평균/최대를 써도 과소평가는 안 하는 이유):
- 비용(왜):

### `public void add(int item)` / `public long totalCount()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

### `public int width()` / `public int depth()` / `public double epsilon()` / `public double delta()` / `public long errorBound()`

- 하는 일:
- 논리(오차 한계가 절대량이라는 것):
- 비용(왜):

## 구현 — HyperLogLog (`src/main/java/com/datastructure/sketch/HyperLogLog.java`)

### 구조

```
HyperLogLog (p = 4  ->  m = 1 << 4 = 16 개 레지스터)
+-------------------------------------------------------+
| p = 4          (해시 앞에서 떼어 쓸 비트 수, 정밀도)   |
| m = 16         (= 1 << p, 버킷 수)                     |
| registers ---+ (byte[m], 버킷마다 값 1바이트)          |
+--------------|----------------------------------------+
               v
   버킷      0    1    2    3    4               15
          +----+----+----+----+----+   ...    +----+
          |  3 |  0 |  1 |  5 |  0 |          |  2 |
          +----+----+----+----+----+   ...    +----+
          각 칸 = 그 버킷에서 본 rank 의 최댓값 (0 = 아직 아무것도 안 들어옴)

   memoryBytes() = m byte. 원소가 100 개든 1억 개든 16 byte 그대로다.
   원소도, 해시도 저장하지 않는다 - 버킷마다 "가장 드물었던 정도" 하나만 남는다.

해시값 64비트를 두 토막으로 쪼갠다
   h = mix64(x)
   +--------+---------------------------------------------------------+
   | p 비트 |                    남은 64 - p 비트                     |
   +--------+---------------------------------------------------------+
     ^ 위쪽 p 비트                        ^ 여기서 앞쪽 0 의 개수를 센다
     index = h >>> (64 - p)               rank = (h << p) 의 선행 0 개수 + 1
     -> 어느 버킷인가                     -> 최대 64 - p + 1 로 잘라 담는다
                                          (1바이트에 들어가는 값이 된다)

   예) p = 4,  h = 0011 0001 0000 ...
       index = 0b0011 = 3
       h << 4 = 0001 0000 ...  -> 선행 0 이 3개 -> rank = 3 + 1 = 4
```

### 동작 — 추가

```
add(x) : 버킷 하나를 골라 rank 의 최댓값만 남긴다(덮어쓰기가 아니라 max 갱신). O(1)

  add(x) : index = 3, rank = 4
                    before                            after
   버킷    0    1    2    3    4             0    1    2    3    4
        +----+----+----+----+----+        +----+----+----+----+----+
        |  3 |  0 |  1 |  2 |  0 |   ->   |  3 |  0 |  1 |  4 |  0 |
        +----+----+----+----+----+        +----+----+----+----+----+
                          ^ 2 < 4 이므로 4 로 올린다

  add(y) : index = 3, rank = 1 이면
        |  3 |  0 |  1 |  4 |  0 |   ->   |  3 |  0 |  1 |  4 |  0 |   (1 < 4, 그대로)

  같은 원소를 다시 넣으면 해시가 같아 index 도 rank 도 같다 -> 값이 변하지 않는다.
  중복을 세지 않는 이유가 여기 있다(멱등). 그래서 "몇 종류인가"만 셀 수 있고
  "몇 번 나왔나"는 셀 수 없다.

merge(other) : 같은 p 끼리 버킷마다 큰 값을 취하면 두 스트림의 합집합이 된다. O(m)
   this   |  3 |  0 |  1 |  4 |        각 자리 max
   other  |  1 |  5 |  1 |  2 |   ->   |  3 |  5 |  1 |  4 |
   원본 스트림을 다시 보지 않고 합칠 수 있다 - 샤드별로 세고 나중에 합치는 게 가능해진다.
```

### 동작 — 세기

```
rank 가 크다 = 그만큼 드문 해시를 봤다 = 그 버킷에 많이 들어왔다는 신호
   해시가 고르다면 rank 1 이 나올 확률 1/2, rank 2 는 1/4, rank k 는 2^-k
   -> 한 버킷의 최대 rank 가 k 면 그 버킷에 대략 2^k 개쯤 들어왔다고 본다

   버킷      0    1    2    3
          +----+----+----+----+
          |  3 |  5 |  1 |  4 |   ->  2^-3 + 2^-5 + 2^-1 + 2^-4 을 모아 되돌린다
          +----+----+----+----+

rawEstimate() = alpha(m) * m * m / sum( 2^(-registers[i]) )
   sum 이 2^-r 들의 합이라 m * m / sum 은 조화평균에 m 을 곱한 꼴이다.
   산술평균이 아니라 조화평균이라야 큰 rank 하나가 전체를 끌고 가지 못한다.
   버킷을 m 개로 나눈 것도 같은 이유 - 한 번의 운을 m 번 나눠 재서 흔들림을 줄인다.
   alpha(m) 은 편향 보정 상수 :  m=16 -> 0.673,  m=32 -> 0.697,  m=64 -> 0.709,
                                 그 밖 -> 0.7213 / (1 + 1.079 / m)

estimate() = 작은 값 구간 보정
   raw <= 2.5 * m  이고  값이 0 인 빈 버킷이 zeros 개 남아 있으면
        m * ln(m / zeros)      <- 빈 버킷 수로 세는 방식으로 바꿔 낀다
   그 밖에는 raw 를 그대로 쓴다
   원소가 적으면 대부분의 버킷이 비어 조화평균 쪽 추정이 흔들리기 때문이다.
```

### `필드`

- `static final int MIN_PRECISION` / `MAX_PRECISION` 역할:
- `int p` (정밀도) 역할:
- `int m` (= 2^p, 레지스터 수) 역할:
- `byte[] registers` 역할:

### `public HyperLogLog(int p)`

- 하는 일:
- 비용(왜):

### `static double alpha(int m)`

- 하는 일:
- 논리:
- 비용(왜):

### `public void add(int item)` (TODO)

- 하는 일:
- 논리(레지스터 번호와 랭크를 뽑는 방법 · max 로만 남기는 이유 · 랭크 상한):
- 비용(왜):

### `public long rawEstimate()` (TODO)

- 하는 일:
- 논리(조화평균을 쓰는 이유):
- 비용(왜):

### `public long estimate()` (TODO)

- 하는 일:
- 논리(작은 카디널리티에서 조화평균이 무너지는 이유 · linear counting 보정):
- 비용(왜):

### `public void merge(HyperLogLog other)` (TODO)

- 하는 일:
- 논리(max 가 결합법칙·교환법칙을 지켜서 "비슷한 정도가 아니라 바이트 단위로 같다"는 것):
- 비용(왜):

### `public long memoryBytes()` / `public int precision()` / `public int registerCount()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ExactCounter (HashMap) | | | |
| CountMinSketch | | | |
| ExactCardinality (HashSet) | | | |
| HyperLogLog | | | |
| 11번 BloomFilter (멤버십) | | | |

## 문제 — SketchProblems (`src/main/java/com/datastructure/sketch/SketchProblems.java`)

### 문제 1. heavy hitters — `static List<int[]> heavyHitters(int[] stream, int k)`

> 문제 설명: 스트림에서 가장 많이 나온 k 개를 빈도 내림차순으로 구한다.
> 반환은 `{값, 추정빈도}` 의 목록이다. 동점이면 값이 작은 것이 먼저다.
> 스트림이 30만 개, 종류가 10만 개여도 계수기는 108KB 로 고정이다.
> (stream 이 null 이면 IllegalArgumentException, k < 1 이면 IllegalArgumentException.
>  상수 `HEAVY_HITTER_EPSILON = 0.001`, `HEAVY_HITTER_DELTA = 0.01`,
>  비교자 `WORST_FIRST` 가 주어져 있다 — 빈도가 작은 것이 먼저, 빈도가 같으면 값이 큰 것이 먼저.)
> 생각할 것: 스케치는 원소를 담지 않는데 후보 목록은 어디서 나오는가.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 샤드 병합 카디널리티 — `static long distinctAcrossShards(int[][] shards, int p)`

> 문제 설명: 샤드마다 따로 세고 병합해서 전체 카디널리티를 구한다.
> 요점은 원본을 하나도 안 옮긴다는 것이다. 샤드가 각자 2만 5천 개를 들고 있어도
> 오가는 것은 레지스터 16KB 씩이다.
> (shards 가 null 이면 IllegalArgumentException. 샤드가 null 이면 IllegalArgumentException.
>  빈 샤드는 길이 0.)
> 생각할 것: 결과가 "통째로 센 것과 비슷하다"가 아니라 **정확히 같다**는 것을 확인하라.
> 그리고 그 이유 때문에 이 함수의 존재 이유(네트워크 바이트)는 테스트가 볼 수 없다.

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

- README: `/home/jun/project/myway/data-structure/19-probabilistic-counting/README.md`
- 구현: `/home/jun/project/myway/data-structure/19-probabilistic-counting/src/main/java/com/datastructure/sketch/`
- 테스트: `/home/jun/project/myway/data-structure/19-probabilistic-counting/src/test/java/com/datastructure/sketch/`
- 정답 구현: `/home/jun/project/myway/data-structure/19-probabilistic-counting/impl/`
