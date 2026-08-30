# data-structure/31-consistent-hashing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — HashRing (`src/main/java/com/datastructure/conshash/HashRing.java`)

- `void addNode(String node)`
- `void removeNode(String node)`
- `String getNode(String key)`
- `int nodeCount()`
- `List<String> nodes()`
- `int slotCount()`
- `default Map<String, Integer> keyCounts(Iterable<String> keys)`

## 계약 — RingHash (`src/main/java/com/datastructure/conshash/RingHash.java`)

- `long position(String name)`

## 보조

- `Hashing` (`src/main/java/com/datastructure/conshash/Hashing.java`) — 역할:
- `RingMetrics` (`src/main/java/com/datastructure/conshash/RingMetrics.java`) — 역할:

## 구현 — ModuloSharding (`src/main/java/com/datastructure/conshash/ModuloSharding.java`)

### 필드
- `nodes` — 역할:

### `void addNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `void removeNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `String getNode(String key)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int nodeCount()` / `List<String> nodes()` / `int slotCount()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — ConsistentHashRing (`src/main/java/com/datastructure/conshash/ConsistentHashRing.java`)

### 필드
- `DEFAULT_VIRTUAL_NODES` — 역할:
- `ring` — 역할:
- `placed` — 역할:
- `virtualNodes` — 역할:
- `hash` — 역할:

### `ConsistentHashRing()` / `ConsistentHashRing(int virtualNodes)` / `ConsistentHashRing(int virtualNodes, RingHash hash)`
- 하는 일:
- 논리:
- 비용(왜):

### `static String virtualName(String node, int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `int virtualNodes()` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `void addNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `void addSlots(String node, int count)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `void removeNode(String node)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `String getNode(String key)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int nodeCount()` / `List<String> nodes()` / `int slotCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `int slotsOf(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `SortedMap<Long, String> ringView()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — WeightedConsistentHashRing (`src/main/java/com/datastructure/conshash/WeightedConsistentHashRing.java`)

### 필드
- 자체 필드 없음 — `ConsistentHashRing` 의 `ring` / `placed` / `virtualNodes` / `hash` 를 상속해 쓴다. 역할:

### `WeightedConsistentHashRing()` / `WeightedConsistentHashRing(int virtualNodes)` / `WeightedConsistentHashRing(int virtualNodes, RingHash hash)`
- 하는 일:
- 논리:
- 비용(왜):

### `void addNode(String node, int weight)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — JumpConsistentHash (`src/main/java/com/datastructure/conshash/JumpConsistentHash.java`)

### 필드
- `nodes` — 역할:

### `static int jumpHash(long key, int numBuckets)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void addNode(String node)`
- 하는 일:
- 논리:
- 비용(왜):

### `void removeNode(String node)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `String getNode(String key)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int nodeCount()` / `List<String> nodes()` / `int slotCount()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ModuloSharding | | | |
| ConsistentHashRing | | | |
| WeightedConsistentHashRing | | | |
| JumpConsistentHash | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/31-consistent-hashing/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/31-consistent-hashing/src/main/java/com/datastructure/conshash/`
- 테스트: `/home/jun/project/myway/data-structure/31-consistent-hashing/src/test/java/com/datastructure/conshash/`
- 정답 구현: `/home/jun/project/myway/data-structure/31-consistent-hashing/impl/`
