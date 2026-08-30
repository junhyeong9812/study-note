# data-structure/11-bloom-filter — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — ProbabilisticSet (`src/main/java/com/datastructure/bloom/ProbabilisticSet.java`)

- `void add(T item)`
- `boolean mightContain(T item)`
- `long insertedCount()`
- `long bitSize()`
- `double expectedFalsePositiveRate()`
- `void clear()`

## 구현 — BloomFilter (`src/main/java/com/datastructure/bloom/BloomFilter.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `private final int bits` — 역할:
- `private final int hashCount` — 역할:
- `private final int capacity` — 역할:
- `private final long[] words` — 역할:
- `private long inserted` — 역할:

### `BloomFilter(int expectedInsertions, double falsePositiveRate)`

- 하는 일:
- 논리:
- 비용(왜):

### `static int optimalBits(int n, double p)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static int optimalHashCount(int m, int n)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int[] indexes(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void add(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean mightContain(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `long insertedCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long bitSize()`

- 하는 일:
- 논리:
- 비용(왜):

### `double expectedFalsePositiveRate()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — CountingBloomFilter (`src/main/java/com/datastructure/bloom/CountingBloomFilter.java`)

### `필드`

- `static final int MAX_COUNT = 255` — 역할:
- `private final int bits` — 역할:
- `private final int hashCount` — 역할:
- `private final byte[] counters` — 역할:
- `private long inserted` — 역할:
- `private long saturations` — 역할:

### `CountingBloomFilter(int expectedInsertions, double falsePositiveRate)`

- 하는 일:
- 논리:
- 비용(왜):

### `void add(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean mightContain(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `long insertedCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long bitSize()`

- 하는 일:
- 논리:
- 비용(왜):

### `int bitsPerSlot()`

- 하는 일:
- 논리:
- 비용(왜):

### `double expectedFalsePositiveRate()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — ScalableBloomFilter (`src/main/java/com/datastructure/bloom/ScalableBloomFilter.java`)

### `필드`

- `static final double TIGHTENING = 0.5` — 역할:
- `static final int GROWTH = 2` — 역할:
- `private final List<BloomFilter<T>> filters` — 역할:
- `private final int initialCapacity` — 역할:
- `private final double initialFpr` — 역할:
- `private int nextCapacity` — 역할:
- `private double nextFpr` — 역할:
- `private long inserted` — 역할:

### `ScalableBloomFilter(int initialCapacity, double falsePositiveRate)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void grow()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void add(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean mightContain(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int filterCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long insertedCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long bitSize()`

- 하는 일:
- 논리:
- 비용(왜):

### `double expectedFalsePositiveRate()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BloomFilter | | | |
| CountingBloomFilter | | | |
| ScalableBloomFilter | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/11-bloom-filter/README.md`
- 구현: `/home/jun/project/myway/data-structure/11-bloom-filter/src/main/java/com/datastructure/bloom/`
- 테스트: `/home/jun/project/myway/data-structure/11-bloom-filter/src/test/java/com/datastructure/bloom/`
- 참고 구현: `/home/jun/project/myway/data-structure/11-bloom-filter/impl/`
