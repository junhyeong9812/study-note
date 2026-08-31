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

### 구조

```
LRUCache — "어디 있나"(해시맵)와 "언제 썼나"(이중 연결 리스트)를 붙여 만든다
+---------------------------------------------------------------+
| capacity = 3                                                  |
| index      Map<K, Node>  — 값이 아니라 "노드 자체"를 담는다      |
| head, tail 꼬리표(sentinel) 노드. key / value 가 없다           |
| hits, misses, evictions                                       |
+---------------------------------------------------------------+

    index (HashMap)                     리스트   오래된 쪽 <---------> 최근 쪽
    +-----+-----------+
    | "A" | -> 노드 A |     +------+    +------+    +------+    +------+    +------+
    | "B" | -> 노드 B |     | head |<-->| "A"  |<-->| "B"  |<-->| "C"  |<-->| tail |
    | "C" | -> 노드 C |     |(더미)|    | 1    |    | 2    |    | 3    |    |(더미)|
    +-----+-----------+     +------+    +------+    +------+    +------+    +------+
                                            ^                       ^
                                        head.next               tail.prev
                                  = 가장 오래 안 쓴 것       = 가장 최근에 쓴 것
                                    (다음에 축출될 것)

    왜 둘을 붙이나 — 각자 못 하는 것이 있다
        해시맵만 쓰면 : "어디 있나"는 O(1) 인데 "누가 제일 오래됐나"를 모른다 -> 전부 훑어 O(n)
        리스트만 쓰면 : 순서는 아는데 "그 키가 어느 노드인가"를 모른다 -> 찾는 데 O(n)
        index 가 키를 노드로 바꿔 주고, 노드를 손에 쥐면 unlink 가 O(1) 이다.
        02 장에서 "노드를 이미 알면 삭제가 O(1)" 이라고 했던 그 성질을 여기서 쓴다.
        05 장 LinkedHashMap 과 같은 조합인데, 순서 기준이 삽입 순서가 아니라 최근 사용 순서다

    head / tail 은 값이 없는 꼬리표(sentinel) 노드다
        덕분에 unlink 와 linkLast 안에 "비었나 / 끝인가" 분기가 하나도 없다.
        어떤 실제 노드든 prev 와 next 가 절대 null 이 아니기 때문이다
        (02 장 DoublyLinkedList 는 더미가 없어서 매번 null 검사 분기가 있었다)
```

### 동작 — 조회

```
get(key)
    index.get(key) == null   ->  misses++, null 반환. 리스트는 건드리지 않는다
    있으면                    ->  hits++, unlink(node) 하고 linkLast(node), value 반환

    get("A") — "A" 를 맨 뒤(가장 최근)로 옮긴다
    before  | head |<-->| "A" |<-->| "B" |<-->| "C" |<-->| tail |
                            ^ 가장 오래된 것

    (1) unlink("A")   앞뒤를 서로 직접 잇고 A 의 손을 놓는다
            | head |<-->| "B" |<-->| "C" |<-->| tail |          ( "A" 는 떨어져 나온 상태 )

    (2) linkLast("A")  tail 바로 앞에 끼워 넣는다
            | head |<-->| "B" |<-->| "C" |<-->| "A" |<-->| tail |
                                                  ^ 이제 가장 최근

    unlink 네 줄                         linkLast 네 줄
        node.prev.next = node.next;          node.prev = tail.prev;
        node.next.prev = node.prev;          node.next = tail;
        node.prev = null;                    tail.prev.next = node;
        node.next = null;                    tail.prev = node;

    앞 두 줄이 이웃끼리 직접 잇고, 뒤 두 줄이 떼어낸 노드의 손을 놓는다.
    linkLast 는 tail.prev 를 먼저 읽어 새 노드에 담은 뒤에 tail.prev 를 갈아끼운다 —
    순서를 뒤집으면 원래 마지막 노드로 가는 길을 잃는다 (02 장의 add 와 같은 함정)

    조회인데 자료구조가 바뀐다 — LRU 캐시의 특이한 점이 이것이다.
    이 get 은 이름만 읽기이고 실제로는 쓰기다
    containsKey 는 다르다 — 순서도 통계도 건드리지 않는다 (봤다고 "썼다"고 치지 않는다)
```

### 동작 — 추가와 축출

```
put(key, value) 세 갈래
    [1] 이미 있는 키    : 값을 갈아끼우고 맨 뒤로 옮긴다. 축출도 통계 변화도 없다
    [2] 새 키, 자리 있음 : 새 노드를 linkLast 하고 index 에 등록
    [3] 새 키, 꽉 참    : 먼저 버리고 나서 넣는다

    put("D", 4) — capacity 3, 이미 A B C 가 들어 있다
    before  | head |<-->| "A" |<-->| "B" |<-->| "C" |<-->| tail |
                            ^ head.next = 가장 오래 안 쓴 것

    (1) oldest = head.next                  -> "A"
    (2) index.remove("A")                   <- 맵에서도 지운다.
                                               리스트만 끊으면 맵에 유령 항목이 남는다
    (3) unlink(oldest);  evictions++;
            | head |<-->| "B" |<-->| "C" |<-->| tail |
    (4) 새 노드 D 를 linkLast 하고 index.put("D", 노드D)
    after   | head |<-->| "B" |<-->| "C" |<-->| "D" |<-->| tail |

    버리기를 넣기 "전에" 한다 — 넣고 나서 버리면 순간적으로 capacity + 1 개가 된다

remove(key) : 사용자가 직접 지운 것이므로 evictions 에 잡히지 않는다 (축출과 삭제는 다른 사건)

keysInOrder() : head.next 부터 tail 직전까지 훑는다 -> 오래된 것 먼저, 최근 것 마지막
    [ "B", "C", "D" ]        앞에서부터 곧 "버려질 순서"다

clear() : index.clear() 하고 head.next = tail, tail.prev = head 로 되돌린다.
          hits / misses / evictions 는 리셋하지 않는다 (통계는 캐시의 일생 기록이다)
```

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

### 구조 — 같은 일을 표준 라이브러리에 시킨다

```
LinkedHashMapLRU — 리스트를 직접 만들지 않고 java.util.LinkedHashMap 에 맡긴다

    new LinkedHashMap<>(16, 0.75f, true)
                                   ^ accessOrder = true
        get 할 때마다 그 항목을 내부 순서 리스트의 맨 뒤로 옮긴다
        <- LRUCache 의 unlink + linkLast 와 정확히 같은 일

    removeEldestEntry(eldest) { return size() > capacity; }
        put 이 끝날 때마다 라이브러리가 이 물음을 던지고, true 면 가장 오래된 항목을 알아서 버린다
        <- LRUCache 의 head.next 축출과 정확히 같은 일

    직접 구현                        LinkedHashMap 에 위임
    ---------------------------------------------------------
    index (HashMap)             ->   내부 해시 테이블
    head / tail 이중 연결 리스트  ->   내부 before / after 링크
    get 의 unlink + linkLast     ->   accessOrder = true
    put 의 head.next 축출        ->   removeEldestEntry

    남는 일은 통계뿐이다
        hits / misses : get 의 반환값이 null 인지로 직접 센다
        evictions     : "새 키였고, 넣기 전 size 가 capacity 였다" 로 판정해 직접 센다
                        라이브러리가 축출했다는 사실을 따로 알려주지 않기 때문이다

    keysInOrder() = new ArrayList<>(map.keySet())
        accessOrder 라 오래된 것부터 나온다 -> LRUCache 와 같은 순서 계약을 만족한다

    두 구현이 같은 Cache 계약을 만족하므로 테스트를 그대로 돌려 볼 수 있다.
    직접 만들어 본 뒤에야 라이브러리의 세 인자(초기 용량, 부하율, accessOrder)가 무슨 뜻인지 보인다
```

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

### 구조 — 감싸기만 하는 데코레이터

```
ThreadSafeLRUCache — 캐시를 새로 만들지 않는다. 다른 Cache 를 감싸고 락만 두른다
    +---------------------------------+
    | delegate ----> LRUCache (또는   |
    |                다른 Cache 구현) |
    | lock      ReentrantLock         |
    +---------------------------------+

    모든 메서드가 같은 모양이다
        lock.lock();
        try { delegate.xxx(...) }
        finally { lock.unlock(); }

    예외는 딱 하나 — capacity() 는 락 없이 바로 위임한다 (생성 후 변하지 않는 값이므로)

    왜 읽기/쓰기 락(ReadWriteLock)으로 나누지 않았나
        get 은 이름만 읽기다. 안에서 unlink + linkLast 로 링크 네 개를 고쳐 쓴다.
        읽기 락으로 여러 스레드가 get 을 동시에 통과하게 두면
            스레드 A 가 노드를 떼어내는 중에 스레드 B 가 같은 이웃 링크를 갈아끼운다
            -> 리스트가 찢어지고 index 와 리스트의 내용이 어긋난다
        "읽기처럼 보이는 쓰기"를 알아보는 것이 이 클래스의 요점이다.
        같은 이유로 hits / misses 증가도 잠금 안에서 일어나야 한다

    감싸는 대상을 생성자로 받으므로 LRUCache 든 LinkedHashMapLRU 든 그대로 끼울 수 있다
```

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
