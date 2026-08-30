# data-structure/10-lru-cache — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Cache (`src/main/java/com/datastructure/cache/Cache.java`)

- `V get(K key)`
- `void put(K key, V value)`
- `boolean containsKey(K key)`
- `V remove(K key)`
- `int size()`
- `int capacity()`
- `boolean isEmpty()`
- `void clear()`
- `List<K> keysInOrder()`
- `long hits()`
- `long misses()`
- `long evictions()`

## 구현 — LRUCache (`src/main/java/com/datastructure/cache/LRUCache.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static final class Node<K, V> { K key; V value; Node<K, V> prev; Node<K, V> next; }` — 역할:
- `private final int capacity` — 역할:
- `private final Map<K, Node<K, V>> index` — 역할:
- `final Node<K, V> head` — 역할:
- `final Node<K, V> tail` — 역할:
- `private long hits` — 역할:
- `private long misses` — 역할:
- `private long evictions` — 역할:

### `LRUCache(int capacity)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void unlink(Node<K, V> node)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void linkLast(Node<K, V> node)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInOrder()` (TODO)

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

### `int capacity()`

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

### `long hits()`

- 하는 일:
- 논리:
- 비용(왜):

### `long misses()`

- 하는 일:
- 논리:
- 비용(왜):

### `long evictions()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinkedHashMapLRU (`src/main/java/com/datastructure/cache/LinkedHashMapLRU.java`)

### `필드`

- `private final int capacity` — 역할:
- `private final LinkedHashMap<K, V> map` — 역할:
- `private long hits` — 역할:
- `private long misses` — 역할:
- `private long evictions` — 역할:

### `LinkedHashMapLRU(int capacity)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInOrder()`

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)`

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

### `int capacity()`

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

### `long hits()`

- 하는 일:
- 논리:
- 비용(왜):

### `long misses()`

- 하는 일:
- 논리:
- 비용(왜):

### `long evictions()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — ThreadSafeLRUCache (`src/main/java/com/datastructure/cache/ThreadSafeLRUCache.java`)

### `필드`

- `private final Cache<K, V> delegate` — 역할:
- `private final ReentrantLock lock` — 역할:

### `ThreadSafeLRUCache(int capacity)`

- 하는 일:
- 논리:
- 비용(왜):

### `ThreadSafeLRUCache(Cache<K, V> delegate)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInOrder()`

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

### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

### `long hits()`

- 하는 일:
- 논리:
- 비용(왜):

### `long misses()`

- 하는 일:
- 논리:
- 비용(왜):

### `long evictions()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| LRUCache | | | |
| LinkedHashMapLRU | | | |
| ThreadSafeLRUCache | | | |

## 문제 — LRUCacheProblems (`src/main/java/com/datastructure/cache/LRUCacheProblems.java`)

### 문제 1. 이 접근 순서에서 LRU 의 적중률은 얼마인가

> 문제 설명: `accesses` 가 비었거나 null 이면 `0.0`.
> 캐시 시뮬레이션은 실무에서 실제로 하는 일이다.
> "캐시를 두 배로 늘리면 적중률이 얼마나 오르나"에 답하려면 이걸 돌려보는 수밖에 없다.
> (돈이 걸린 질문이라 감으로 답하면 안 된다)
> 방금 만든 `LRUCache` 를 쓰라. `hits()` 가 이미 세고 있다.
> 생각할 것 — `get` 이 null 이면 `put` 한다. 그게 캐시를 쓰는 코드의 기본 모양이다. /
> 적중률 = hits / 전체 접근 수. **정수 나눗셈을 조심하라**(07번에서 한 번 나왔다).
> 시그니처: `static double hitRatio(int capacity, int[] accesses)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 미래를 안다면 적중률은 얼마까지 오르나 (Belady 최적 알고리즘)

> 문제 설명: 축출할 때 "다음에 쓰일 시점이 가장 먼 것"을 버린다. 다시 안 쓰이는 것이 있으면 그것부터.
> 이건 실제로 쓸 수 있는 알고리즘이 아니다. 미래를 알아야 하기 때문이다.
> 그런데도 구현하는 이유는 **상한선**이기 때문이다.
> LRU 가 60%를 낸다면, 그게 좋은 건지 나쁜 건지는 최적이 65%인지 95%인지에 달렸다.
> 최적이 95%인데 LRU 가 60%라면 정책을 바꿀 여지가 크다는 뜻이다.
> 최적이 65%라면 정책이 아니라 용량이나 접근 패턴을 손봐야 한다.
> 여기서는 캐시 클래스를 쓰지 않아도 된다. 축출 정책이 다르기 때문이다.
> 생각할 것 — 각 키가 **다음에 언제 다시 나오는지**를 알아야 한다.
> 뒤에서부터 훑으며 키마다 등장 위치 목록을 만들어두면, 앞에서 진행하며 맨 앞을 하나씩 버리는 것으로
> "다음 등장"을 O(1) 에 알 수 있다(04번 큐가 여기서 쓰인다). /
> 축출 대상은 "다음 등장이 가장 먼 것", 다시 안 나오는 키는 무한대로 친다.
> 캐시 안을 전부 훑어 고르므로 축출 한 번이 O(용량)이다. 어차피 이론용이라 괜찮다.
> 시그니처: `static double optimalHitRatio(int capacity, int[] accesses)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 최근 capacity 개 안에서 이미 본 것은 버린다

> 문제 설명: 살아남은 것만 순서대로 반환한다.
> 이벤트 파이프라인의 중복 제거가 정확히 이 모양이다.
> 같은 이벤트가 재전송으로 두 번 오는데, 전체 이력을 들고 있을 수는 없어서
> 최근 N개만 기억한다. 메모리를 한정하는 대신 아주 오래된 중복은 놓친다.
> 09번 트라이 문제 3번과 대비된다. 거기서는 전부 기억해서 정확한 답을 냈고,
> 여기서는 **일부러 잊어서** 메모리를 한정한다. 무엇을 포기하느냐의 차이다.
> 생각할 것 — 본 적 있으면 건너뛰고, 처음 보면 결과에 담는다. /
> 다시 본 것은 **최근으로 갱신되어야 한다.** `get` 이 그 일을 이미 한다.
> (그래서 여기서 `containsKey` 를 쓰면 안 된다. 순서를 안 바꾸기 때문이다) /
> `stream` 이 비었거나 null 이면 빈 리스트.
> 시그니처: `static List<Integer> deduplicateStream(int capacity, int[] stream)`

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

- 원본 README: `/home/jun/project/myway/data-structure/10-lru-cache/README.md`
- 구현: `/home/jun/project/myway/data-structure/10-lru-cache/src/main/java/com/datastructure/cache/`
- 테스트: `/home/jun/project/myway/data-structure/10-lru-cache/src/test/java/com/datastructure/cache/`
- 참고 구현: `/home/jun/project/myway/data-structure/10-lru-cache/impl/`
