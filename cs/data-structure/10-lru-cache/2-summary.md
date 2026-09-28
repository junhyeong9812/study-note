# data-structure/10-lru-cache — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.
> 2026-09-28: 통일 골격 양식으로 재배치 + 새 절 추가(Claude 작성 — 기존 본문은 이동만).

## 해결하는 문제

느린 저장소(DB·디스크·네트워크) 앞에 빠른 보관소를 두면 같은 것을 두 번 안 가져와도 된다. 그런데 빠른 보관소는 **자리가 유한**하다.\
자리가 차면 무엇을 버릴지 정해야 하고, "버릴 것 고르기"와 "찾기"가 둘 다 O(1)이 아니면 캐시가 병목이 된다.

```text
해시맵만                           이중 연결 리스트만              둘을 붙이면
"A 있어?"       O(1)               "A 있어?"      O(n) 훑기      "A 있어?"        O(1) 맵
"제일 오래된 건?" O(n) 전부 봐야     "제일 오래된 건?" O(1) 맨 앞    "제일 오래된 건?" O(1) 맨 앞
                                                                 서로의 약점을 정확히 메운다
```

LRU 캐시는 해시맵(어디 있나)과 이중 연결 리스트(언제 썼나)를 겹쳐, 찾기·넣기·버리기를 전부 O(1)로 만든다.\
쉬운 예: 자리가 3칸뿐인 책상 — 새 책이 필요하면 가장 오래 안 펼친 책을 책장으로 치운다.\
똑같은 구조다: Java `LinkedHashMap`에 `accessOrder=true`와 `removeEldestEntry`를 켠 것.\
실무 예: Redis의 `maxmemory-policy allkeys-lru` — 메모리가 차면 가장 오래 안 쓴 키부터 버린다.

  - *LRU(Least Recently Used)*: "가장 오래 안 쓴 것부터 버린다"는 교체 정책. 최근에 쓴 것을 또 쓸 것이라는 가정 위에 선다.

### 한눈에 — 쉽게 말하면

**비유: 자리가 3칸뿐인 책상 위.** 책장(느림)까지 가기 싫어서 자주 보는 책을 책상(빠름)에 올려 둔다.\
책상이 꽉 찼는데 새 책이 필요하면? **가장 오랫동안 안 펼친 책**을 책장으로 치운다.

**LRU 캐시가 바로 이 책상과 똑같은 구조다.** LRU = Least Recently Used, "가장 오래 안 쓴 것부터 버린다".

> **캐시(cache)** — 자주 쓰는 데이터를 빠른 곳에 복사해 두는 임시 보관소.\
> 예: 자리가 한정돼 있어서 "무엇을 버릴까"가 캐시의 핵심 문제가 된다.

- 두 가지 질문에 둘 다 즉답해야 한다: "그 책 책상에 있어?"(찾기) + "누가 제일 오래 방치됐어?"(버릴 순서).
- 그래서 자료구조 두 개를 붙인다: 해시맵(어디 있나) + 이중 연결 리스트(언제 썼나).

> **이중 연결 리스트(doubly linked list)** — 노드마다 앞(prev)·뒤(next) 둘 다 아는 줄.\
> 예: 노드를 손에 쥐고 있으면 그 노드를 줄 중간에서 빼내는 데 링크 네 줄이면 끝나 O(1)이다.

- 책을 펼치기만 해도(get) 그 책은 "방금 씀"이 되어 줄 맨 뒤로 이동한다 — 읽기처럼 보이는 쓰기.
- 실무에서 같은 구조: 브라우저 캐시, Redis의 maxmemory-policy(allkeys-lru), CPU 캐시 교체 정책.

> **적중/미스(hit/miss)** — 찾는 것이 캐시에 있었다 / 없었다.\
> 예: 100번 물어서 60번 있었으면 적중률은 hits ÷ 전체 접근 수 = 0.6 이다.

```text
    오래 방치됨 <-------------------> 방금 씀
    | A |  | B |  | C |     <- 꽉 찬 책상 (3칸)
      ^ 새 책이 오면 A부터 치운다
```

## 동작·원리

### 전체 흐름

```text
[1] 용량이 자료구조의 일부                  [2] 두 구조를 겹친다 — 맵의 값은 V 가 아니라 "노드"
    capacity = 3, 꽉 차면 버려야 한다           index(HashMap)        줄(이중 연결 리스트, 센티널 head/tail)
    무엇을 버리나 = 정책 (여기서는 LRU)         "A" -> 노드A          head <-> A <-> B <-> C <-> tail
                                               "B" -> 노드B                 ^ 오래됨       최근 ^
              |                                "C" -> 노드C           키로 노드를 O(1)에 쥐면 unlink 도 O(1)
              v
[3] get = 읽기가 아니다                     [4] put 의 세 경우
    get("A"): 맵에서 노드A 찾기               있는 키   -> 값 바꾸고 맨 뒤로
              줄에서 unlink -> linkLast       새 키, 자리 있음 -> 맵에 넣고 맨 뒤에 linkLast
    head <-> B <-> C <-> A <-> tail           새 키, 꽉 참 -> head.next 를 맵과 줄 양쪽에서 지우고(evict) 넣는다
    "방금 씀"으로 옮기는 쓰기 4줄이 들어 있다
              |
              v
[5] 대가: 순차 스캔에서 0% · get 이 쓰기라 읽기 락 불가 · 맵/줄 한쪽만 지우면 조용히 어긋남
```

- [1] 지금까지 만든 구조는 넣으면 남아 있었다. 여기서는 용량이 계약이고, 무엇을 버릴지가 곧 자료구조의 정책이다.
- [2] 맵이 키를 노드로 바꿔 주고, 노드를 손에 쥐면 줄 어디서든 O(1)에 빼고 끼운다(02번의 "노드를 알면 O(1)").\
  센티널 두 개 덕에 "비었나·끝인가" 분기가 없다.
- [3] `get`은 값을 꺼내면서 그 노드를 줄 맨 뒤로 옮긴다 — 읽기처럼 보이는 쓰기다. 이 한 줄이 동시성 문제의 전부다.
- [4] `put`은 세 경우로 갈리고, 축출은 맵과 줄 **양쪽**에서 지워야 한다.
- [5] LRU는 시간 지역성이라는 가정 위에 서 있다. 가정이 반대로 틀리는 순차 스캔에서는 완전히 진다.

### 계약 — Cache (`src/main/java/com/datastructure/cache/Cache.java`)

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

### 구현 — LRUCache (`src/main/java/com/datastructure/cache/LRUCache.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

#### 구조

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

> **센티널/더미(sentinel) 노드** — 값이 없는 가짜 머리(head)·꼬리(tail) 노드.\
> 예: 실제 노드의 prev·next가 절대 null이 아니게 되어, unlink와 linkLast에서 "비었나 / 끝인가" 분기가 통째로 사라진다.

> **해시맵(hash map)** — 키를 계산으로 바로 자리에 꽂아 O(1)에 찾는 자료구조.\
> 예: 여기서는 값이 아니라 "키 → 그 키의 노드"를 담는 안내판(index)으로 쓴다.

#### 동작 — 조회

**언제 쓰나** — "그 키의 값 줘"(get).\
값을 주는 것에 더해, 그 항목을 "방금 씀" 자리로 옮기는 일까지 한다.

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

**그림에서 일어난 일 (쉽게)**

1. 해시맵(index)에게 "A가 어느 노드야?"를 물어 노드를 바로 손에 쥐었다 — 리스트를 훑지 않는다.
2. unlink: A의 양옆 이웃끼리 서로 직접 잇고 A를 줄에서 빼냈다.\
   노드를 이미 알고 있으니 O(1).
3. linkLast: 빼낸 A를 맨 뒤(tail 바로 앞) = "방금 씀" 자리에 끼웠다.

> **unlink / linkLast** — 노드를 줄에서 빼내는 수술 / 맨 뒤에 끼우는 수술.\
> 예: 각각 링크 네 줄로 끝나는데, linkLast는 `tail.prev`를 먼저 읽어 두지 않으면 원래 마지막 노드로 가는 길을 잃는다.

4. 요점: **get인데 자료구조가 바뀐다.**\
   이름은 읽기지만 실제로는 쓰기다 — 뒤의 ThreadSafe 절에서 이게 함정이 된다.

**비용** — 해시맵 조회 O(1) + 링크 고치기 O(1) = O(1).

#### 동작 — 추가와 축출

**언제 쓰나** — 새 값을 넣을 때(put).\
자리가 꽉 찼으면 가장 오래 안 쓴 것을 먼저 버린다(축출).

> **축출(eviction)** — 캐시가 자리를 만들려고 스스로 항목을 버리는 것.\
> 예: 사용자가 직접 부르는 remove와는 다른 사건이라, evictions 통계에 따로 센다.

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

**그림에서 일어난 일 (쉽게)**

1. 꽉 찬 상태에서 새 키 D가 왔다.\
   버릴 대상은 물어볼 것도 없이 head.next = 가장 오래 안 쓴 A.
2. **맵과 리스트 양쪽에서** A를 지웠다.\
   리스트만 끊으면 맵에 "있는 척하는 유령"이 남는다 — 두 구조를 붙여 쓰는 대가는 항상 둘을 같이 고쳐야 한다는 것.
3. 그다음에야 D를 맨 뒤에 넣었다.\
   순서를 뒤집으면(넣고 나서 버리면) 한순간 정원 초과가 된다.

**비용** — 버리기 O(1) + 넣기 O(1) = O(1).\
"누가 제일 오래됐나"를 찾는 비용이 0인 것이 이 설계의 존재 이유다.

> **O(1)** — 데이터가 몇 개든 일의 양이 똑같은 비용.\
> 예: 캐시에 항목이 3개든 30만 개든, 버릴 대상은 head.next 한 번 읽기로 나온다.

#### `필드`

- `static final class Node<K, V> { K key; V value; Node<K, V> prev; Node<K, V> next; }` — 역할:
- `private final int capacity` — 역할:
- `private final Map<K, Node<K, V>> index` — 역할:
- `final Node<K, V> head` — 역할:
- `final Node<K, V> tail` — 역할:
- `private long hits` — 역할:
- `private long misses` — 역할:
- `private long evictions` — 역할:

#### `LRUCache(int capacity)`

- 하는 일:
- 논리:
- 비용(왜):

#### `private void unlink(Node<K, V> node)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `private void linkLast(Node<K, V> node)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `V remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `List<K> keysInOrder()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

#### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

#### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long hits()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long misses()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long evictions()`

- 하는 일:
- 논리:
- 비용(왜):

### 구현 — LinkedHashMapLRU (`src/main/java/com/datastructure/cache/LinkedHashMapLRU.java`)

#### 구조 — 같은 일을 표준 라이브러리에 시킨다

방금 손으로 만든 "해시맵 + 순서 리스트" 조합은 사실 자바가 `LinkedHashMap`이라는 이름으로 이미 판다.\
스위치 두 개(accessOrder, removeEldestEntry)만 켜면 같은 캐시가 된다 — 직접 만들어 봤기에 그 스위치가 무슨 뜻인지 보인다.

> **accessOrder / removeEldestEntry** — LinkedHashMap의 스위치 두 개: 최근 사용 순 유지 / put 후 가장 오래된 항목 자동 삭제 여부.\
> 예: `accessOrder = true` 가 직접 짠 unlink + linkLast와 같은 일을, `removeEldestEntry` 가 head.next 축출과 같은 일을 대신한다.

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

#### `필드`

- `private final int capacity` — 역할:
- `private final LinkedHashMap<K, V> map` — 역할:
- `private long hits` — 역할:
- `private long misses` — 역할:
- `private long evictions` — 역할:

#### `LinkedHashMapLRU(int capacity)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `List<K> keysInOrder()`

- 하는 일:
- 논리:
- 비용(왜):

#### `V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

#### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

#### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long hits()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long misses()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long evictions()`

- 하는 일:
- 논리:
- 비용(왜):

### 구현 — ThreadSafeLRUCache (`src/main/java/com/datastructure/cache/ThreadSafeLRUCache.java`)

#### 구조 — 감싸기만 하는 데코레이터

여러 스레드가 동시에 캐시를 만지면 링크 수술 중인 리스트가 찢어진다.\
그래서 기존 캐시를 포장지처럼 감싸고, 출입문에 자물쇠(락) 하나만 단다.

> **스레드(thread)** — 한 프로그램 안에서 동시에 도는 작업 흐름 여러 개.\
> 예: 스레드 A가 노드를 떼어내는 중에 스레드 B가 같은 이웃 링크를 갈아끼우면 리스트가 찢어진다.

> **락(lock, ReentrantLock)** — 한 번에 한 스레드만 통과시키는 자물쇠. 다른 스레드는 앞에서 기다린다.\
> 예: 모든 메서드를 `lock.lock()` → `try { 위임 }` → `finally { lock.unlock() }` 로 감싸 준다.

> **데코레이터 패턴(decorator)** — 원본 객체를 바꾸지 않고 감싸서 기능(여기서는 잠금)만 덧붙이는 설계 방식.\
> 예: 감쌀 대상을 생성자로 받으므로 LRUCache든 LinkedHashMapLRU든 그대로 끼울 수 있다.

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

> **ReadWriteLock(읽기/쓰기 락)** — 읽기끼리는 동시에 통과시키는 락.\
> 예: 여기서는 쓸 수 없다 — get이 안에서 링크 네 개를 고쳐 쓰는 "읽기처럼 보이는 쓰기"이기 때문이다.

> **위임(delegate)** — 감싼 원본 객체에게 실제 일을 넘기는 것.\
> 예: capacity()만은 생성 후 변하지 않는 값이라 락 없이 바로 위임한다.

#### `필드`

- `private final Cache<K, V> delegate` — 역할:
- `private final ReentrantLock lock` — 역할:

#### `ThreadSafeLRUCache(int capacity)`

- 하는 일:
- 논리:
- 비용(왜):

#### `ThreadSafeLRUCache(Cache<K, V> delegate)`

- 하는 일:
- 논리:
- 비용(왜):

#### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

#### `List<K> keysInOrder()`

- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

#### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

#### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long hits()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long misses()`

- 하는 일:
- 논리:
- 비용(왜):

#### `long evictions()`

- 하는 일:
- 논리:
- 비용(왜):

## 쓰이는 곳

- **Java `LinkedHashMap(cap, 0.75f, true)` + `removeEldestEntry`** — 표준 라이브러리가 같은 조합을 이미 갖고 있다. 이 노트의 `LinkedHashMapLRU`가 그 4줄이다.
- **Redis `maxmemory-policy allkeys-lru` / `volatile-lru`** — 메모리 상한에 닿으면 LRU로 키를 버린다. 정확한 줄 대신 표본 몇 개(`maxmemory-samples`, 기본 5) 중 가장 오래된 것을 고르는 근사 LRU다(Redis 문서 "Key eviction").
- **DB 버퍼 풀·OS 페이지 캐시** — 디스크 페이지를 메모리에 두고 가득 차면 교체한다. 순차 스캔 오염을 막으려고 LRU 변형(MySQL InnoDB 버퍼 풀의 young/old 두 구역 — 새 페이지는 중간 지점에 넣는다, Linux 페이지 캐시의 active/inactive 리스트 — 6.1부터는 선택적으로 MGLRU)을 쓴다.
- **CPU 캐시 교체·TLB** — 하드웨어도 같은 문제를 푼다. 정확한 LRU는 비싸서 흔히 pseudo-LRU(트리 비트 몇 개로 흉내) 같은 근사를 쓴다. 구체 정책은 CPU마다 다르고 공개되지 않은 경우가 많다.
- **Caffeine·Guava 캐시(애플리케이션 캐시)** — 둘 다 `get`이 쓰기라는 문제를 접근 기록 버퍼로 미뤄 읽기를 동시에 통과시킨다. Guava는 세그먼트별 LRU이고, Caffeine은 순차 스캔 저항을 위해 빈도까지 보는 W-TinyLFU를 쓴다(Caffeine 설계 문서).
- **CDN·브라우저 캐시** — 원본 서버 앞의 유한한 저장소. 적중률이 곧 비용이라 문제 1의 시뮬레이션(용량을 두 배로 하면 적중률이 얼마나 오르나)이 실제로 쓰인다.
- **[ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md)** — 캐시 미스가 한꺼번에 원본으로 몰리는 장애. 축출 정책과 짝을 이루는 운영 문제다.

## 적용 — 풀어나가는 법

캐시 문제는 "무엇을 버릴지"와 "그 결정을 O(1)에 내릴 수 있는지"를 나눠 보면 풀린다.\
순서: ① 접근 패턴이 시간 지역성을 갖는지 확인한다(순차 스캔이면 LRU가 아니다) → ② 용량을 정하고 적중률을 시뮬레이션으로 잰다(문제 1), 상한은 Belady로 잰다(문제 2) → ③ 찾기·순서 갱신·축출이 각각 O(1)인지 자료구조로 확인한다 → ④ 동시 접근이 있으면 `get`이 쓰기라는 점부터 잠금 설계에 반영한다.\
아래 세 문제는 ②의 측정과, 캐시를 "최근 N개만 기억하는 집합"으로 쓰는 응용(문제 3)이다.

### 문제 — 이 챕터가 시키는 것

원본 README는 이 박스를 "**넣으면 남아 있다**는 전제가 처음 깨지는 박스"라고 소개한다.\
용량이 자료구조의 일부이고, **무엇을 버릴지가 곧 이 자료구조의 정책**이다 — LRU는 "가장 오래 안 쓴 것을 버린다"를 고르며, 그것은 시간 지역성이라는 **가정이지 정리가 아니다**.\
05번 해시맵(어디 있나 O(1))과 02번 이중 연결 리스트(가장 오래된 것 O(1))를 겹쳐 서로의 약점을 메우는 구조를 직접 엮고, 같은 동작을 표준 라이브러리(`LinkedHashMap`)로도 만들어 비교한 뒤, `get`이 실은 쓰기라서 생기는 동시성 문제까지 다루는 것이 과제다.

과제 목록 — `src/main/java/com/datastructure/cache/`의 TODO:

- `LRUCache` — TODO 1(`unlink`) · TODO 2(`linkLast`) · TODO 3(`get` — 순서 갱신) · TODO 4(`put` — 경우가 셋) · TODO 5(`remove` — 맵과 줄 양쪽) · TODO 6(`keysInOrder`)
- `LinkedHashMapLRU` — TODO 1(`accessOrder=true` + `removeEldestEntry`) · TODO 2(`get` + 통계) · TODO 3(`put` + 축출 세기)
- `ThreadSafeLRUCache` — TODO 1(`get` 잠금 — `try/finally`) · TODO 2(`put` 잠금)
- `LRUCacheProblems` — TODO 1: 문제 1(`hitRatio`) · TODO 2: 문제 2(`optimalHitRatio` — Belady) · TODO 3: 문제 3(`deduplicateStream`)

순서: `CacheContractTest.java`를 먼저 따라 친다(계약이 거기 있다) → `LRUCache` 6개 → `LinkedHashMapLRU` 3개 → `ThreadSafeLRUCache` 2개 → 문제 3개.\
실행: `cd ~/project/myway/data-structure && ./run.sh 10` — README 기준 **108개 중 101개가 실패**한다(통과하는 7개는 미리 채워둔 생성자·null 검사 테스트).

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| LRUCache | | | |
| LinkedHashMapLRU | | | |
| ThreadSafeLRUCache | | | |

### 문제 — LRUCacheProblems (`src/main/java/com/datastructure/cache/LRUCacheProblems.java`)

#### 문제 1. 이 접근 순서에서 LRU 의 적중률은 얼마인가

> 문제 설명: `accesses` 가 비었거나 null 이면 `0.0`.\
> 캐시 시뮬레이션은 실무에서 실제로 하는 일이다.\
> "캐시를 두 배로 늘리면 적중률이 얼마나 오르나"에 답하려면 이걸 돌려보는 수밖에 없다.\
> (돈이 걸린 질문이라 감으로 답하면 안 된다)\
> 방금 만든 `LRUCache` 를 쓰라. `hits()` 가 이미 세고 있다.\
> 생각할 것 — `get` 이 null 이면 `put` 한다. 그게 캐시를 쓰는 코드의 기본 모양이다. /\
> 적중률 = hits / 전체 접근 수. **정수 나눗셈을 조심하라**(07번에서 한 번 나왔다).\
> 시그니처: `static double hitRatio(int capacity, int[] accesses)`

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 2. 미래를 안다면 적중률은 얼마까지 오르나 (Belady 최적 알고리즘)

> 문제 설명: 축출할 때 "다음에 쓰일 시점이 가장 먼 것"을 버린다. 다시 안 쓰이는 것이 있으면 그것부터.\
> 이건 실제로 쓸 수 있는 알고리즘이 아니다. 미래를 알아야 하기 때문이다.\
> 그런데도 구현하는 이유는 **상한선**이기 때문이다.\
> LRU 가 60%를 낸다면, 그게 좋은 건지 나쁜 건지는 최적이 65%인지 95%인지에 달렸다.\
> 최적이 95%인데 LRU 가 60%라면 정책을 바꿀 여지가 크다는 뜻이다.\
> 최적이 65%라면 정책이 아니라 용량이나 접근 패턴을 손봐야 한다.\
> 여기서는 캐시 클래스를 쓰지 않아도 된다. 축출 정책이 다르기 때문이다.\
> 생각할 것 — 각 키가 **다음에 언제 다시 나오는지**를 알아야 한다.\
> 뒤에서부터 훑으며 키마다 등장 위치 목록을 만들어두면, 앞에서 진행하며 맨 앞을 하나씩 버리는 것으로\
> "다음 등장"을 O(1) 에 알 수 있다(04번 큐가 여기서 쓰인다). /\
> 축출 대상은 "다음 등장이 가장 먼 것", 다시 안 나오는 키는 무한대로 친다.\
> 캐시 안을 전부 훑어 고르므로 축출 한 번이 O(용량)이다. 어차피 이론용이라 괜찮다.\
> 시그니처: `static double optimalHitRatio(int capacity, int[] accesses)`

> **Belady 최적 알고리즘** — "다음에 쓰일 시점이 가장 먼 것을 버린다"는 이론상 최강 교체 정책.\
> 예: 미래를 알아야 해서 실제로는 못 쓰지만, LRU의 적중률이 좋은 편인지 나쁜 편인지 재는 상한선이 된다.

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 3. 최근 capacity 개 안에서 이미 본 것은 버린다

> 문제 설명: 살아남은 것만 순서대로 반환한다.\
> 이벤트 파이프라인의 중복 제거가 정확히 이 모양이다.\
> 같은 이벤트가 재전송으로 두 번 오는데, 전체 이력을 들고 있을 수는 없어서\
> 최근 N개만 기억한다. 메모리를 한정하는 대신 아주 오래된 중복은 놓친다.\
> 09번 트라이 문제 3번과 대비된다. 거기서는 전부 기억해서 정확한 답을 냈고,\
> 여기서는 **일부러 잊어서** 메모리를 한정한다. 무엇을 포기하느냐의 차이다.\
> 생각할 것 — 본 적 있으면 건너뛰고, 처음 보면 결과에 담는다. /\
> 다시 본 것은 **최근으로 갱신되어야 한다.** `get` 이 그 일을 이미 한다.\
> (그래서 여기서 `containsKey` 를 쓰면 안 된다. 순서를 안 바꾸기 때문이다) /\
> `stream` 이 비었거나 null 이면 빈 리스트.\
> 시그니처: `static List<Integer> deduplicateStream(int capacity, int[] stream)`

> **중복 제거(deduplication)** — 같은 것이 또 오면 걸러내는 것.\
> 예: 최근 N개만 기억하는 방식이라 그보다 오래전에 지나간 중복은 일부러 놓친다.

- 내 접근:
- 논리:
- 비용(왜):

## 장애 시나리오와 대처

**1. 순차 스캔 한 번에 캐시 전체가 오염된다**

- 현상: 배치 작업(전체 테이블 스캔·리포트 생성)이 한 번 돌고 나면 온라인 요청의 응답 시간이 한동안 나빠진다.
- 보이는 형태: 적중률 그래프가 배치 시각에 절벽처럼 떨어졌다가 서서히 회복한다. 미스가 몰려 원본 DB의 부하가 튄다.
- 원인: 한 번만 쓸 데이터가 n개 지나가면 LRU는 자주 쓰던 항목을 전부 밀어낸다 — "최근에 쓴 것을 또 쓴다"는 가정이 스캔에서는 정확히 반대로 틀린다(정답 10번의 0%가 이 형태로 나타난다).
- 대처: 스캔 경로는 캐시를 우회하게 한다(bypass 플래그). 또는 두 번 이상 접근된 것만 승격하는 두 구역 LRU·빈도 기반 정책(LFU·W-TinyLFU)으로 바꾼다.

**2. 용량이 워킹 셋보다 조금 작아 적중률이 절벽으로 떨어진다**

- 현상: 데이터가 조금 늘었을 뿐인데 적중률이 갑자기 크게 떨어진다.
- 보이는 형태: 용량 3에 키 4개를 돌아가며 찍으면 0%, 용량 4면 100% — 경계 하나 차이로 극단이 갈린다. 실서비스에서는 사용자 수가 임계를 넘는 날 갑자기 DB 부하가 두 배가 된다.
  - *워킹 셋(working set)*: 어느 기간에 실제로 반복해서 쓰이는 데이터 집합.
- 원인: LRU는 워킹 셋이 용량에 들어가면 거의 다 맞히고, 조금이라도 넘치면 매번 "다음에 쓸 것"을 골라 버리는 패턴에 빠진다.
- 대처: 문제 1의 시뮬레이션을 실제 접근 로그로 돌려 용량-적중률 곡선을 미리 그린다. 워킹 셋 크기를 관측(고유 키 수)해 용량이 그보다 여유 있게 크도록 잡는다.

**3. 잠금을 `try/finally` 없이 잡아 예외 한 번에 전체가 멈춘다**

- 현상: 어느 순간부터 캐시를 쓰는 모든 요청이 응답하지 않는다. CPU는 한가하다.
- 보이는 형태: 스레드 덤프에서 스레드들이 전부 `ReentrantLock.lock()`에서 `WAITING`이다. 그 직전 로그에 캐시 안에서 난 예외(예: 키의 `hashCode`가 던진 것) 한 줄이 있다.
- 원인: `lock()` 뒤에 위임 호출이 예외를 던졌는데 `unlock()`이 `finally`에 없어 잠금이 영원히 안 풀린다.
- 대처: `lock(); try { … } finally { unlock(); }`를 예외 없이 지킨다. 테스트는 위임 객체가 예외를 던지게 하고 그 뒤 다른 스레드가 잠금을 얻는지 확인한다(`lockIsReleasedOnException`).

**4. 값이 큰 항목을 개수 기준 용량으로 관리해 메모리가 터진다**

- 현상: `size()`는 용량 이내인데 프로세스 메모리가 계속 늘다 `OutOfMemoryError`가 난다.
- 보이는 형태: 힙 덤프에서 캐시 노드 수는 적은데 몇 개의 값(큰 바이트 배열·리스트)이 힙 대부분을 차지한다.
- 원인: 이 노트의 용량은 **항목 개수**다. 항목마다 크기가 다르면 개수 상한이 메모리 상한이 되지 않는다.
- 대처: 항목의 무게(바이트)를 함께 세어 무게 합으로 축출하거나, 큰 값은 캐시에 넣지 않고 참조만 둔다. 메모리 사용량을 지표로 내보내 상한에 닿기 전에 알아챈다.

## 핵심 문장

- LRU 캐시는 용량이 계약인 첫 구조다 — 넣으면 남아 있다는 전제가 깨지고, 무엇을 버릴지가 곧 자료구조의 정책이 된다.
- 해시맵(어디 있나)과 이중 연결 리스트(언제 썼나)는 서로의 약점을 정확히 메운다 — 맵의 값이 노드여야 노드를 손에 쥔 채 줄에서 O(1)에 빼고 끼운다.
- `get`은 읽기가 아니다 — 값을 꺼내며 줄 맨 뒤로 옮기는 쓰기이므로 읽기 잠금으로 열 수 없고, 그 손상은 다음 순회에서야 무한 루프로 드러난다.
- 축출은 맵과 줄 양쪽에서 지워야 하고 한쪽만 지우면 조용히 어긋난다 — 매 연산마다 둘을 대조하는 테스트가 그것을 잡는다.
- LRU는 시간 지역성이라는 가정이지 정리가 아니다 — 순차 스캔에서 0%가 되고, "얼마나 좋은가"는 Belady 상한과 비교해야 답이 나온다.

## 관련 주제·근거

- 선행 — [02-linked-list](../02-linked-list/2-summary.md)(이중 연결·노드를 알면 O(1)) · [05-hashmap](../05-hashmap/2-summary.md)(`LinkedHashMap`의 순서 줄): 두 부품의 출처.
- 후속 — [11-bloom-filter](../11-bloom-filter/2-summary.md): 일부러 잊는 대신 틀릴 수 있게 해서 메모리를 수십 배 줄이는 쪽.
- 운영 — [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md): 미스가 한꺼번에 원본으로 몰리는 장애.
- 기초 — [foundations/memory-management](../../foundations/memory-management/): 페이지 교체가 같은 문제인 자리.
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `14-lru-cache` (선행 `07-hashmap`, `04-linked-list`).
- 교재 — OSTEP 22장 Beyond Physical Memory: Policies(LRU·Belady·순차 스캔).
- myway 원본 — `/home/jun/project/myway/data-structure/10-lru-cache/` (README.md · impl/LRUCache.java · impl/LinkedHashMapLRU.java · impl/ThreadSafeLRUCache.java · impl/LRUCacheProblems.java).

### 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/10-lru-cache/README.md`
- 구현: `/home/jun/project/myway/data-structure/10-lru-cache/src/main/java/com/datastructure/cache/`
- 테스트: `/home/jun/project/myway/data-structure/10-lru-cache/src/test/java/com/datastructure/cache/`
- 참고 구현: `/home/jun/project/myway/data-structure/10-lru-cache/impl/`

### 용어 풀이

- **캐시(cache)**: 자주 쓰는 데이터를 빠른 곳에 복사해 두는 임시 보관소. 자리가 한정돼 있어 "무엇을 버릴까"가 핵심 문제다.
- **LRU (Least Recently Used)**: "가장 오래 안 쓴 것부터 버린다"는 교체 정책.
- **축출(eviction)**: 캐시가 자리를 만들려고 스스로 항목을 버리는 것. 사용자가 지우는 remove와 구분해 센다.
- **적중/미스(hit/miss)**: 찾는 것이 캐시에 있었다/없었다. 적중률 = hits ÷ 전체 접근 수.
- **해시맵(hash map)**: 키를 계산으로 바로 자리에 꽂아 O(1)에 찾는 자료구조. 여기서는 "키 → 노드" 안내판(index) 역할.
- **이중 연결 리스트(doubly linked list)**: 노드마다 앞(prev)·뒤(next) 둘 다 아는 줄. 노드를 손에 쥐면 어느 위치든 O(1)에 빼고 끼울 수 있다.
- **노드(node)**: 리스트의 한 칸. 여기서는 key, value, prev, next를 담는다.
- **센티널/더미(sentinel) 노드**: 값 없는 가짜 머리(head)·꼬리(tail) 노드. 덕분에 "비었나/끝인가" null 검사 분기가 사라진다.
- **unlink / linkLast**: 노드를 줄에서 빼는 수술 / 맨 뒤에 끼우는 수술. 각각 링크 네 줄로 끝난다.
- **참조/포인터(reference/pointer)**: 다른 객체가 어디 있는지 가리키는 값. prev/next가 그것.
- **O(1) / O(n)**: 일의 양 — 데이터가 몇 개든 일정 / 개수에 비례해서 전부 훑기.
- **LinkedHashMap**: 자바 표준의 "해시맵 + 순서 리스트" 결합체. accessOrder=true면 get마다 그 항목을 맨 뒤로 옮긴다.
- **accessOrder / removeEldestEntry**: LinkedHashMap의 스위치 — 최근 사용 순 유지 / put 후 가장 오래된 항목 자동 삭제 여부.
- **스레드(thread)**: 한 프로그램 안에서 동시에 도는 작업 흐름. 여럿이 같은 자료구조를 만지면 충돌한다.
- **락(lock, ReentrantLock)**: 한 번에 한 스레드만 통과시키는 자물쇠. try/finally로 반드시 풀어 준다.
- **ReadWriteLock(읽기/쓰기 락)**: 읽기끼리는 동시 통과시키는 락. 여기서 못 쓰는 이유 = get이 사실은 쓰기라서.
- **데코레이터 패턴(decorator)**: 원본을 바꾸지 않고 감싸서 기능을 덧붙이는 설계. ThreadSafeLRUCache가 잠금을 덧붙인다.
- **위임(delegate)**: 감싼 원본 객체에게 실제 일을 넘기는 것.
- **Belady 최적 알고리즘**: "다음에 쓰일 시점이 가장 먼 것을 버린다"는 이론상 최강 정책. 미래를 알아야 해서 실사용은 불가 — 적중률의 상한선 측정용.
- **중복 제거(deduplication)**: 같은 것이 또 오면 걸러내는 것. 최근 N개만 기억하는 방식이 문제 3이다.
