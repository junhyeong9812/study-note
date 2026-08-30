# data-structure/12-skip-list — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — OrderedMap (`src/main/java/com/datastructure/skiplist/OrderedMap.java`)

- `V put(K key, V value)`
- `V get(K key)`
- `boolean containsKey(K key)`
- `V remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `K firstKey()`
- `K lastKey()`
- `K floorKey(K key)`
- `K ceilingKey(K key)`
- `List<K> keys()`
- `List<K> keysInRange(K from, K to)`

## 계약 — OrderedSet (`src/main/java/com/datastructure/skiplist/OrderedSet.java`)

- `boolean add(K key)`
- `boolean contains(K key)`
- `boolean remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `K first()`
- `K last()`
- `K floor(K key)`
- `K ceiling(K key)`
- `List<K> toList()`
- `List<K> range(K from, K to)`

## 구현 — SkipList (`src/main/java/com/datastructure/skiplist/SkipList.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static final int MAX_LEVEL = 32` — 역할:
- `static final double P = 0.5` — 역할:
- `static final class Node<K, V> { final K key; V value; final Node<K, V>[] forward; }` — 역할:
- `final Node<K, V> head` — 역할:
- `private final Random random` — 역할:
- `int level` — 역할:
- `private int size` — 역할:

### `SkipList()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipList(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `int randomLevel()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V>[] findPredecessors(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K floorKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInRange(K from, K to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `int currentLevel()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SkipListMap (`src/main/java/com/datastructure/skiplist/SkipListMap.java`)

### `필드`

- `private final SkipList<K, V> list` — 역할:

### `SkipListMap()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipListMap(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K floorKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInRange(K from, K to)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SkipListSet (`src/main/java/com/datastructure/skiplist/SkipListSet.java`)

### `필드`

- `private static final Object PRESENT` — 역할:
- `private final SkipListMap<K, Object> map` — 역할:

### `SkipListSet()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipListSet(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean add(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `K first()`

- 하는 일:
- 논리:
- 비용(왜):

### `K last()`

- 하는 일:
- 논리:
- 비용(왜):

### `K floor(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `K ceiling(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> toList()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> range(K from, K to)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| SkipList | | | |
| SkipListMap | | | |
| SkipListSet | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/12-skip-list/README.md`
- 구현: `/home/jun/project/myway/data-structure/12-skip-list/src/main/java/com/datastructure/skiplist/`
- 테스트: `/home/jun/project/myway/data-structure/12-skip-list/src/test/java/com/datastructure/skiplist/`
- 참고 구현: `/home/jun/project/myway/data-structure/12-skip-list/impl/`
