# data-structure/05-hashmap — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Map (`src/main/java/com/datastructure/hashmap/Map.java`)

- `V put(K key, V value)`
- `V get(Object key)`
- `boolean containsKey(Object key)`
- `V remove(Object key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `Iterable<K> keys()`

## 구현 — ChainingHashMap (`src/main/java/com/datastructure/hashmap/ChainingHashMap.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static class Node<K, V> { final K key; V value; Node<K, V> next; }` — 역할:
- `static final int DEFAULT_CAPACITY = 8` — 역할:
- `static final double LOAD_FACTOR = 0.75` — 역할:
- `Node<K, V>[] buckets` — 역할:
- `int size` — 역할:

### `ChainingHashMap()`

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

### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(Object key)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)`

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V> findNode(Object key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void resize()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinearProbingHashMap (`src/main/java/com/datastructure/hashmap/LinearProbingHashMap.java`)

### `필드`

- `static final byte EMPTY = 0` — 역할:
- `static final byte OCCUPIED = 1` — 역할:
- `static final byte TOMBSTONE = 2` — 역할:
- `static final int DEFAULT_CAPACITY = 8` — 역할:
- `static final double LOAD_FACTOR = 0.5` — 역할:
- `Object[] keys` — 역할:
- `Object[] values` — 역할:
- `byte[] states` — 역할:
- `int size` — 역할:
- `int used` — 역할:

### `LinearProbingHashMap()`

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

### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(Object key)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)`

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void resize()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinkedHashMap (`src/main/java/com/datastructure/hashmap/LinkedHashMap.java`)

### `필드`

- `static class Entry<K> { final K key; Entry<K> prev; Entry<K> next; }` — 역할:
- `Entry<K> first` — 역할:
- `Entry<K> last` — 역할:
- `private final ChainingHashMap<K, Entry<K>> order` — 역할:

### `protected void afterPut(K key, boolean isNewKey)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `protected void afterRemove(Object key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `protected void afterClear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<K> keys()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ChainingHashMap | | | |
| LinearProbingHashMap | | | |
| LinkedHashMap | | | |

## 문제 — MapProblems (`src/main/java/com/datastructure/hashmap/MapProblems.java`)

### 문제 1. 빈도 세기

> 문제 설명: 각 값이 몇 번 나오는지 `counts` 에 담는다.
> `[1, 2, 2, 3, 3, 3]` -> `{1=1, 2=2, 3=3}`
> 생각할 것 — 처음 보는 값과 이미 본 값을 어떻게 구분하는가?
> 시그니처: `static void countFrequencies(int[] values, Map<Integer, Integer> counts)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 두 수의 합 (이 문제집의 함정)

> 문제 설명: 더해서 `target` 이 되는 서로 다른 두 인덱스를 찾아 `[작은인덱스, 큰인덱스]` 로 반환한다.
> 없으면 빈 배열. 답이 여러 개면 두 번째 인덱스가 가장 작은 것을 반환한다.
> `[2, 7, 11, 15], target=9` -> `[0, 1]` / `[3, 3], target=6` -> `[0, 1]` / `[1, 2], target=99` -> `[]`
> 함정 — 모든 쌍을 다 보면 O(n²) 이다. 테스트에 20만 개짜리 케이스와 시간 제한이 있다.
> 생각할 것 — 지금 값이 v 라면 짝은 무엇인가? 그 짝을 이미 봤는지 물을 수 있으면 한 번만 훑어도 된다. /
> `seen` 에 무엇을 키로, 무엇을 값으로 담아야 하는가? / 같은 값이 두 번 나오는 경우(`[3,3]`)를 어떻게 다루는가?
> 시그니처: `static int[] twoSum(int[] values, int target, Map<Integer, Integer> seen)` — O(n) 이어야 한다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 처음으로 한 번만 나온 문자의 인덱스

> 문제 설명: 문자열 전체에서 딱 한 번만 나오는 문자 중 가장 앞의 것의 인덱스. 없으면 -1.
> `"leetcode"` -> `0` (l) / `"aabb"` -> `-1` / `"abac"` -> `1` (b)
> 04번에서는 같은 문제를 큐로 풀었다. 거기서는 "스트림을 흘려보내며 매 시점의 답"이 필요했고
> 여기서는 "전체를 다 보고 난 뒤의 답"이 필요하다. 무엇이 필요한지가 자료구조를 정한다.
> 시그니처: `static int firstUniqueChar(String input, Map<Character, Integer> counts)` — 두 번 훑어도 O(n) 이다.

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

- 원본 README: `/home/jun/project/myway/data-structure/05-hashmap/README.md`
- 구현: `/home/jun/project/myway/data-structure/05-hashmap/src/main/java/com/datastructure/hashmap/`
- 테스트: `/home/jun/project/myway/data-structure/05-hashmap/src/test/java/com/datastructure/hashmap/`
- 참고 구현: `/home/jun/project/myway/data-structure/05-hashmap/impl/`
