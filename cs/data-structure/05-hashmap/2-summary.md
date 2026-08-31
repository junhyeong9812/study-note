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

### 구조

```
ChainingHashMap — 버킷 배열 하나 + 버킷마다 매달린 노드 사슬
+-----------------------------------------------------+
| size = 4                                            |
| buckets ---+     (capacity = 8, LOAD_FACTOR = 0.75) |
+------------|----------------------------------------+
             v
     idx  +-------+
       0  | null  |
          +-------+      +-----------+      +-----------+
       1  |   *---+----> | key   "B" |      | key   "J" |
          +-------+      | value  2  |      | value 10  |
       2  | null  |      | next    --+----> | next  null|
          +-------+      +-----------+      +-----------+
       3  |   *---+----> [ key "D" ] -> null      ^
          +-------+                               |
       4  | null  |             같은 칸에 떨어진 키들 = 충돌.
          +-------+             배열 안에서 자리를 다투지 않고 사슬로 매단다
       5  |   *---+----> [ key "P" ] -> null
          +-------+
       6  | null  |
          +-------+
       7  | null  |
          +-------+

키에서 칸 번호로
    bucketOf(key, capacity) = (key.hashCode() & 0x7fffffff) % capacity
        (1) hashCode()        임의의 int — 음수일 수 있다
        (2) & 0x7fffffff      부호 비트만 지운다 -> 언제나 0 이상
        (3) % capacity        0 .. capacity-1 로 접는다
    스프레딩(h ^ h>>>16)도, & (length-1) 비트마스킹도 쓰지 않는다. 순수 나머지 연산이다

이 구조가 O(1) 인 이유: 어디를 볼지 계산으로 알아낸다 (배열처럼 훑지도, 트리처럼 내려가지도 않는다)
무너지는 조건: 해시가 한 칸에 몰리면 사슬 하나가 길어져 사실상 연결 리스트가 된다 -> O(n)
```

### 동작 — 조회

```
get(key) / containsKey(key) : 칸을 계산하고, 그 칸의 사슬만 훑는다
    get("J")
        (1) bucketOf("J", 8) = 1
        (2) buckets[1] -> [ "B" ] -> [ "J" ] -> null
                             |          |
                             equals?    equals?
                             아니오      예 -> value 10

    해시가 같은 칸을 준다고 키가 같다는 뜻은 아니다 -> 반드시 equals 로 확인한다
    비용 = 그 칸의 사슬 길이. 고르게 흩어져 있으면 평균 O(1), 다 몰리면 O(n)
```

### 동작 — 추가

```
[1] 이미 있는 키 : 사슬에 새로 매달지 않고 값만 바꾼다. size 불변
        [ "B":2 ] -> [ "J":10 ] -> null      put("B", 9)
             ^ value 만 9 로 교체

[2] 새 키 : 사슬의 맨 앞에 꽂는다. 꼬리를 찾으러 걷지 않으므로 O(1)
    before  buckets[1] -> [ "B" ] -> [ "J" ] -> null
    after   buckets[1] -> [ "X" ] -> [ "B" ] -> [ "J" ] -> null
            buckets[b] = new Node(key, value, buckets[b]);   size++;
            (새 노드의 next 에 옛 head 를 먼저 담고 버킷 칸을 갈아끼운다)

[3] 리사이즈 : size > buckets.length * 0.75 가 되면 2배로 늘리고 전부 다시 계산해 옮긴다
    왜 "다시 계산"인가 — 칸 번호가 % capacity 로 정해지므로 capacity 가 바뀌면 갈 곳이 바뀐다
        해시가 26 인 키       26 % 8 = 2       ->      26 % 16 = 10
        해시가 18 인 키       18 % 8 = 2       ->      18 % 16 = 2

    before  capacity 8
        idx 2 -> [ P(26) ] -> [ Q(18) ] -> null

    after   capacity 16
        idx  2 -> [ Q(18) ] -> null      <- 같은 칸에 남는 것도 있고
        idx 10 -> [ P(26) ] -> null      <- 다른 칸으로 가는 것도 있다

    노드 객체는 재사용하고 next 만 다시 연결한다. 옮길 때도 새 버킷 앞에 꽂으므로
    같은 칸에 함께 남은 노드들끼리는 순서가 뒤집힌다 (keys() 순서는 약속된 것이 아니다)
    한 번은 O(n) 이지만 2배씩 늘리므로 put 한 번의 상환 비용은 O(1)
```

### 동작 — 삭제

```
remove(key) : 사슬을 훑으며 prev 를 들고 있다가, 찾으면 앞뒤를 직접 잇는다
    remove("B")
    before  buckets[1] -> [ "X" ] -> [ "B" ] -> [ "J" ] -> null
                            prev      찾은 노드

    after   buckets[1] -> [ "X" ] ---------->  [ "J" ] -> null
                                    ( "B" 노드는 next 를 끊고 버린다 )

    prev == null ? buckets[b] = n.next : prev.next = n.next;
    n.next = null;  size--;
    단일 연결 사슬이라 prev 를 따로 들고 다녀야 한다 (02 장 SinglyLinkedList 와 같은 사정)

축소(shrink)는 없다. clear() 도 버킷 배열 길이는 그대로 두고 칸만 null 로 채운다
```

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

### 구조

```
LinearProbingHashMap — 사슬이 없다. 자리가 차 있으면 옆 칸으로 밀려난다
+-----------------------------------------------------+
| size = 3    (OCCUPIED 칸 수 = 실제 원소 수)          |
| used = 4    (OCCUPIED + TOMBSTONE = 한 번이라도 쓴 칸)|
| keys ---+   values ---+   states ---+               |
+---------|-------------|-------------|---------------+
          v             v             v
  idx        0        1        2        3        4        5        6        7
  keys    [      ] [  "A" ] [  "B" ] [      ] [  "C" ] [      ] [      ] [      ]
  values  [      ] [   1  ] [   2  ] [      ] [   3  ] [      ] [      ] [      ]
  states  [EMPTY ] [ OCC  ] [ OCC  ] [ TOMB ] [ OCC  ] [EMPTY ] [EMPTY ] [EMPTY ]

  세 배열이 같은 인덱스를 공유한다. Entry 객체가 없다 (노드 하나당 객체 하나인 체이닝과 대비)

  states 의 세 값이 이 구조의 전부다
      EMPTY(0)      한 번도 쓴 적 없는 칸.  탐사가 여기서 "없다"로 끝난다
      OCCUPIED(1)   지금 키가 들어 있는 칸
      TOMBSTONE(2)  지웠던 칸.  "여기 있었지만 지금은 없다" = 지나가되, 채워도 되는 자리

  칸 번호   bucketOf(key, capacity) = (key.hashCode() & 0x7fffffff) % capacity   (체이닝과 동일)
  충돌 시   nextProbe(i) = (i + 1) % capacity     오른쪽 옆 칸. 끝에 닿으면 0 으로 되감긴다

  LOAD_FACTOR = 0.5 — 체이닝(0.75)보다 낮다.
  체이닝은 차도 사슬이 길어질 뿐이지만, 여기서는 빈 칸이 줄면 탐사 거리가 급격히 늘어난다
```

### 동작 — 조회

```
indexOf(key) : 제 칸부터 오른쪽으로 훑는다. EMPTY 를 만나면 없는 것이다
    get("C") — bucketOf("C") = 1 이라고 하자
    idx        1         2         3         4         5
            [  "A" ]  [  "B" ]  [ TOMB ]  [  "C" ]  [EMPTY ]
               (1)       (2)       (3)       (4)
               OCC       OCC       TOMB      OCC
               A!=C      B!=C      지나침    C 발견 -> 인덱스 4 반환
               ->옆칸    ->옆칸               (equals 로 확인)

    없는 키를 찾을 때
            [  "A" ]  [  "B" ]  [ TOMB ]  [  "C" ]  [EMPTY ]
                                                        ^ EMPTY 를 만나면 즉시 -1
    "여기까지 왔는데 한 번도 안 쓴 칸이 나왔다" = 그 키는 애초에 이 사슬에 들어온 적이 없다.
    EMPTY 가 탐사의 종료 표지다. 그래서 삭제가 어려워진다 (아래 삭제 항목)

    한 바퀴(capacity 스텝)를 상한으로 둔다 — 무덤만 가득한 배열에서 무한히 도는 것을 막는다
```

### 동작 — 추가

```
put(key, value)
    (0) 먼저 리사이즈 검사:  used + 1 > keys.length * 0.5  이면 resize()
        기준이 size 가 아니라 used 다 — 무덤도 탐사를 길게 만드는 "쓰인 자리"이기 때문

    (1) bucketOf 부터 오른쪽으로 탐사하며 처음 만난 무덤 위치(firstTombstone)를 기억해 둔다
    (2) 같은 키(OCCUPIED + equals)를 만나면 -> values[i] 만 교체하고 끝. 자리 이동 없음
    (3) EMPTY 를 만나면 -> 여기까지 같은 키가 없었음이 확정된다
            기억해둔 무덤이 있으면  그 자리에 쓴다   (used 는 그대로 — 이미 쓴 자리를 재활용)
            없으면                  지금 칸에 쓴다   (used++)
        어느 쪽이든 size++

    무덤을 보자마자 채우지 않는 이유
    idx        1         2         3
            [ TOMB ]  [  "X" ]  [EMPTY ]        put("X", 9) 를 한다면
               ^ 여기 바로 쓰면 2번 칸의 "X" 와 키가 중복된 채 둘 다 살아남는다
    그래서 EMPTY 까지 끝까지 확인해 "같은 키가 없음"을 확정한 뒤, 되돌아와 무덤 자리를 쓴다
```

### 동작 — 삭제

```
remove(key) : 칸을 비우되 EMPTY 가 아니라 TOMBSTONE 으로 표시한다
    출발 상태 — "B", "C" 는 모두 칸 1 에서 밀려 온 것들이다
    idx        1         2         3         4
            [  "A" ]  [  "B" ]  [  "C" ]  [EMPTY ]
              OCC       OCC       OCC       EMPTY

    remove("A") 를 EMPTY 로 되돌리면 (틀린 방식)
            [EMPTY ]  [  "B" ]  [  "C" ]  [EMPTY ]
               ^ get("B") 가 칸 1 에서 EMPTY 를 보고 즉시 -1 을 낸다.
                 B, C 로 이어지던 탐사 사슬이 여기서 끊겨, 있는 키를 없다고 답한다

    실제 방식 — TOMBSTONE 을 남긴다
            [ TOMB ]  [  "B" ]  [  "C" ]  [EMPTY ]
            keys[i] = null;  values[i] = null;  states[i] = TOMBSTONE;
            size--;          used 는 줄지 않는다

    탐사는 무덤을 지나쳐 계속 간다 -> 사슬이 끊기지 않는다.
    대신 무덤이 쌓이면 실제 원소가 적어도 탐사만 길어진다. 청소는 resize 가 맡는다
```

### 동작 — 리사이즈

```
resize() : 새 용량이 항상 2배는 아니다. 무덤 청소용 재구축이라는 두 번째 얼굴이 있다
    capacity = (size > oldLength * LOAD_FACTOR / 2) ? oldLength * 2 : oldLength
             = (size > oldLength / 4)               ? 2배           : 같은 크기 재구축

    [경우 1] 무덤만 쌓인 상황 — 실제 원소는 적다
    before  capacity 8, size 2, used 5
        keys   [    ][ "A"][    ][    ][ "C"][    ][    ][    ]
        states [ E  ][ O  ][ T  ][ T  ][ O  ][ T  ][ E  ][ E  ]     무덤 3개

    after   capacity 8 (그대로), size 2, used 2
        keys   [    ][ "A"][    ][    ][ "C"][    ][    ][    ]
        states [ E  ][ O  ][ E  ][ E  ][ O  ][ E  ][ E  ][ E  ]     무덤이 사라졌다

    [경우 2] 실제 원소도 많은 상황 -> 길이를 2배로

    두 경우 모두 OCCUPIED 칸만 새 배열에 다시 넣는다 (무덤은 옮기지 않는다).
    재삽입은 중복 검사도 무덤 검사도 하지 않는다 — 새 배열에는 무덤도 중복도 없기 때문
```

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

### 구조

```
LinkedHashMap — ChainingHashMap 을 상속하고, "삽입 순서"를 담는 리스트를 옆에 하나 더 둔다
    부모(ChainingHashMap) : 키 -> 값. 버킷 사슬. keys() 가 버킷 순서로 나온다
    자식이 더하는 것      : 키만 담은 이중 연결 리스트 + 그 리스트를 O(1) 로 찾기 위한 색인

+-----------------------------------------------------------+
| (상속) buckets, size ...        <- 값(value)은 여기에 있다  |
| first ---+                                                |
| last ----|---------------------------------------+        |
| order ---|--- ChainingHashMap<K, Entry<K>>       |        |  <- 키 -> Entry 색인
+----------|---------------------------------------|--------+
           v                                       v
      +-------+         +-------+         +-------+
null <-+ prev  |<--------+ prev  |<--------+ prev  |
      | key A |         | key B |         | key C |     Entry 에는 key 만 있다
      | next  +-------->| next  +-------->| next  +--> null
      +-------+         +-------+         +-------+
      먼저 넣은 것                          나중에 넣은 것

    JDK 의 방식(Node 안에 before/after 를 다는 것)과 다르다.
    여기서는 순서 리스트의 Entry 와 버킷 사슬의 Node 가 서로 다른 객체다.
    그래서 키로 Entry 를 찾을 길이 따로 필요하고, 그게 order 다 (해시맵이 결국 두 개다)
```

### 동작 — 훅으로 갈아끼우기

```
부모의 put / remove / clear 본체는 그대로 쓰고, 비어 있던 훅 세 개만 재정의한다

    put(key, value)  ---- 부모가 버킷 사슬을 처리 ----> afterPut(key, isNewKey)
                                                          |
        isNewKey == false (값만 바뀜)  -> 아무것도 하지 않는다 (순서 불변)
        isNewKey == true  (새 키)      -> Entry 를 만들어 꼬리에 붙이고 order 에 등록

        before   first -> [ A ] <-> [ B ] <- last
        after    first -> [ A ] <-> [ B ] <-> [ C ] <- last      put("C", ...)
                                                ^ 언제나 꼬리에 붙는다

    remove(key)      ---- 부모가 버킷에서 제거 ----> afterRemove(key)
        order.remove(key) 로 Entry 를 꺼내고, 그 앞뒤를 직접 잇는다 (02 장 unlink 와 같은 그림)
        before   first -> [ A ] <-> [ B ] <-> [ C ] <- last      remove("B")
        after    first -> [ A ] <--------->  [ C ] <- last
        prev == null ? first = next : prev.next = next
        next == null ? last  = prev : next.prev = prev

    clear()          ----> afterClear() : first = last = null, order.clear()

    keys()  재정의 — 버킷 순서가 아니라 first -> next 를 따라 삽입 순서로 낸다
        부모의 keys()   : 버킷 0,1,2 ... 순서 (해시가 정하는 순서 = 사람이 예측할 수 없다)
        자식의 keys()   : A, B, C ... (넣은 순서)

order 가 없다면 afterRemove 가 리스트를 처음부터 훑어야 해서 O(n) 이 된다.
"해시맵 + 이중 연결 리스트" 이 조합을 10 장 LRU 캐시가 다시 쓴다 — 거기서는 순서 기준이
삽입 순서가 아니라 최근 사용 순서다
```

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
