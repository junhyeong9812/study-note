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
