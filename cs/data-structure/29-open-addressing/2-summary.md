# data-structure/29-open-addressing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — ProbeMap (`src/main/java/com/datastructure/openaddr/ProbeMap.java`)

- `V put(K key, V value)`
- `V get(Object key)`
- `boolean containsKey(Object key)`
- `V remove(Object key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `Iterable<K> keys()`
- `int capacity()`
- `int lastProbeCount()`
- `default int maxProbeCount()`
- `default double loadFactor()`

## 보조 — (TODO 없는 보조 타입)

- `Hashing` (`Hashing.java`) — 역할:
- `Hashing.hash(Object key)` — 역할:
- `Hashing.mix(int h)` — 역할:
- `Hashing.tableSizeFor(int n)` — 역할:

## 구현 — ProbeSequenceMap (`src/main/java/com/datastructure/openaddr/ProbeSequenceMap.java`)

### 필드
- `EMPTY` / `OCCUPIED` / `TOMBSTONE` (상태 상수) — 역할:
- `DEFAULT_CAPACITY` / `DEFAULT_MAX_LOAD` — 역할:
- `keys` — 역할:
- `values` — 역할:
- `states` — 역할:
- `size` — 역할:
- `used` — 역할:
- `mask` — 역할:
- `maxLoad` — 역할:
- `lastProbes` — 역할:

### `ProbeSequenceMap()` / `ProbeSequenceMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `abstract int probe(int hash, int i)`
- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object key)` (TODO 1)
- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO 2)
- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)` / `boolean containsKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `void resize()`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()` / `void clear()` / `Iterable<K> keys()`
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int lastProbeCount()` / `int tombstones()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinearProbeMap (`src/main/java/com/datastructure/openaddr/LinearProbeMap.java`)

### 필드
- (없음 — `ProbeSequenceMap` 의 것을 쓴다)

### `LinearProbeMap()` / `LinearProbeMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int probe(int hash, int i)` (TODO 3)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — QuadraticProbeMap (`src/main/java/com/datastructure/openaddr/QuadraticProbeMap.java`)

### 필드
- `triangular` — 역할:

### `QuadraticProbeMap()` / `QuadraticProbeMap(int capacity, double maxLoad)` / `QuadraticProbeMap(int capacity, double maxLoad, boolean triangular)`
- 하는 일:
- 논리:
- 비용(왜):

### `int probe(int hash, int i)` (TODO 4)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — DoubleHashMap (`src/main/java/com/datastructure/openaddr/DoubleHashMap.java`)

### 필드
- (없음 — `ProbeSequenceMap` 의 것을 쓴다)

### `DoubleHashMap()` / `DoubleHashMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int stepFor(int hash)` (TODO 5)
- 하는 일:
- 논리:
- 비용(왜):

### `int probe(int hash, int i)`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — RobinHoodMap (`src/main/java/com/datastructure/openaddr/RobinHoodMap.java`)

### 필드
- `DEFAULT_CAPACITY` / `DEFAULT_MAX_LOAD` — 역할:
- `keys` — 역할:
- `values` — 역할:
- `hashes` — 역할:
- `size` — 역할:
- `mask` — 역할:
- `maxLoad` — 역할:
- `lastProbes` — 역할:

### `RobinHoodMap()` / `RobinHoodMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int distanceOf(int slot)`
- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object key)` (TODO 6)
- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO 7)
- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)` (TODO 8)
- 하는 일:
- 논리:
- 비용(왜):

### `void resize()`
- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)` / `boolean containsKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()` / `void clear()` / `Iterable<K> keys()` / `int capacity()` / `int lastProbeCount()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — CuckooHashMap (`src/main/java/com/datastructure/openaddr/CuckooHashMap.java`)

### 필드
- `MAX_KICKS` — 역할:
- `MAX_REHASH` — 역할:
- `DEFAULT_CAPACITY` / `DEFAULT_MAX_LOAD` — 역할:
- `keys` — 역할:
- `values` — 역할:
- `half` — 역할:
- `mask` — 역할:
- `size` — 역할:
- `maxLoad` — 역할:
- `lastProbes` — 역할:
- `kicks` — 역할:
- `rehashes` — 역할:
- `cycleRehashes` — 역할:

### `CuckooHashMap()` / `CuckooHashMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int slot1(int hash)` / `int slot2(int hash)`
- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object key)` (TODO 9)
- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO 10)
- 하는 일:
- 논리:
- 비용(왜):

### `Object[] tryInsert(Object key, Object value)` (TODO 11, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void rehash(int newCapacity)` / `void giveUp(Object[] homeless, K key)`
- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)` / `boolean containsKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `long kickCount()` / `int rehashCount()` / `int cycleRehashCount()` / `void resetCounters()`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()` / `void clear()` / `Iterable<K> keys()` / `int capacity()` / `int lastProbeCount()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| LinearProbeMap (선형 탐사) | | | |
| QuadraticProbeMap (이차 탐사) | | | |
| DoubleHashMap (이중 해싱) | | | |
| RobinHoodMap (로빈후드) | | | |
| CuckooHashMap (쿠쿠) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/29-open-addressing/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/29-open-addressing/src/main/java/com/datastructure/openaddr/`
- 테스트: `/home/jun/project/myway/data-structure/29-open-addressing/src/test/java/com/datastructure/openaddr/`
- 정답 구현: `/home/jun/project/myway/data-structure/29-open-addressing/impl/`
