# data-structure/05-hashmap — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**해시맵 = 이름으로 사물함 번호를 계산하는 사물함장.**

- "김철수 가방 어디 있어?" 하면 사물함을 하나씩 열어보는 게 아니라, 이름을 **공식에 넣어 번호를 계산**해서 그 칸으로 바로 간다. 예: 이름 글자값을 다 더해 사물함 개수로 나눈 나머지 = 칸 번호.
- 이 공식이 *해시 함수*, 계산된 번호의 칸이 *버킷*이다. 훑지 않고 계산으로 찾으니 평균 O(1).
- 문제는 서로 다른 이름이 같은 번호가 될 수 있다는 것(*충돌*). 이걸 어떻게 푸느냐가 구현을 가른다: 같은 칸에 줄줄이 매달기(체이닝) vs 옆 칸으로 밀려나기(오픈 어드레싱/선형 탐사).
- 사물함이 거의 다 차면 찾기가 느려지니, 일정 비율(적재율)을 넘으면 더 큰 사물함으로 전부 이사한다(리사이즈).

```text
    "김철수" --해시 공식--> 3번 칸
                             |
    사물함:  [0][1][2][3][4][5]
                       ^ 바로 여기만 연다 (다 안 훑는다)
```

이 사물함이 **똑같은 구조로** 해시맵이다: 이름 = 키(key), 가방 = 값(value), 공식 = hashCode() % capacity, 사물함 = 버킷 배열. Java의 `HashMap`, Python의 `dict`가 이렇게 동작한다.

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

  - *hashCode()*: 객체를 하나의 정수로 요약하는 함수. 같은 키는 항상 같은 숫자가 나온다(반대는 보장 안 됨 — 다른 키가 같은 숫자일 수 있다).
  - *부호 비트를 지운다(& 0x7fffffff)*: int의 맨 앞 비트는 음수 표시다. 그 비트만 0으로 꺼서 항상 0 이상으로 만든다 — 음수 % 는 음수가 나와 배열 인덱스로 못 쓰기 때문.
  - *스프레딩 / 비트마스킹*: JDK가 쓰는 최적화(해시 비트를 섞기, % 대신 & 쓰기). 이 구현은 배우기 쉽게 순수 나머지 연산만 쓴다.

## 사전 지식 — hashCode 와 equals 의 약속 (조회를 읽기 전에)

- 규칙 하나만 기억하면 된다: **equals로 같은 두 키는 hashCode도 반드시 같아야 한다.**
- 그래야 "같은 키는 반드시 같은 칸에 떨어진다"가 보장되고, 그 칸만 뒤지면 된다.
- 거꾸로는 성립 안 한다: hashCode가 같아도(같은 칸에 떨어져도) 다른 키일 수 있다 — 그래서 칸 안에서는 equals로 최종 확인한다.

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

그림 해설 (한 단계씩):

- (1) 키를 공식에 넣어 칸 번호를 계산한다 — 여기까지는 훑는 게 아니라 산수다.
- (2) 그 칸에 매달린 사슬만 한 명씩 equals로 대조한다. 다른 칸은 아예 안 본다.
- 비용은 "그 칸 사슬의 길이"다. 잘 흩어져 있으면 사슬이 짧아 평균 O(1).

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

그림 해설 (한 단계씩):

- [1] 이미 있는 키면 값만 갈아끼운다 — 한 키에 값은 하나라는 맵의 약속.
- [2] 새 키는 사슬 맨 앞에 꽂는다. 꼬리까지 걸어갈 필요가 없어 O(1) — 스택 push와 같은 요령.
- [3] 원소 수가 칸 수의 75%(적재율 0.75)를 넘으면 칸을 2배로 늘리고 전부 재배치한다.
  - *적재율(load factor)*: 사물함이 얼마나 찼는지의 비율 = size / 칸 수. 이 문턱을 넘으면 리사이즈.
  - "다시 계산"하는 이유: 칸 번호가 `% capacity`로 정해지므로, capacity가 바뀌면 같은 키라도 갈 칸이 바뀐다.
  - *상환(amortized) O(1)*: 리사이즈 순간만 O(n), 2배씩 늘려 드물게 일어나므로 put 1회 평균은 O(1).

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

그림 해설 (한 단계씩):

- 칸을 계산해 그 사슬을 훑되, 지금 노드의 "앞 노드"(prev)를 계속 기억하며 걷는다 — 단일 연결이라 뒤로 못 돌아가기 때문.
- 찾으면 앞 노드와 뒤 노드를 직접 잇고, 떼어낸 노드의 next를 끊는다(GC를 위해).
- 지운 노드가 사슬의 첫 노드였다면 이어줄 앞이 없으니 버킷 칸 자체를 갈아끼운다 — null 분기의 정체.

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

  - *오픈 어드레싱(open addressing) / 선형 탐사(linear probing)*: 충돌한 키를 사슬에 매달지 않고 배열의 다른 칸에 넣는 방식. "옆 칸을 하나씩" 보는 게 선형 탐사다 — 내 사물함이 차 있으면 바로 옆 칸을 쓰는 것.
  - *탐사(probe)*: 빈 칸 또는 내 키를 찾아 칸을 하나씩 확인하는 걸음.
  - *묘비(TOMBSTONE)*: "여기 있었지만 지금은 없다"는 팻말. 왜 그냥 비우면 안 되는지는 아래 삭제 절이 보여준다.

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

그림 해설 (한 단계씩):

- 제 칸부터 오른쪽으로 한 칸씩 걷는다: 다른 키(OCC)면 지나가고, 무덤(TOMB)도 지나간다.
- 내 키를 만나면 찾은 것. **한 번도 쓴 적 없는 칸(EMPTY)을 만나면 "없다"가 확정**된다 — 넣을 때도 같은 길을 걸었을 테니, 있었다면 그 전에 나왔어야 한다.
- EMPTY가 탐사의 종료 표지라는 이 사실이, 삭제를 어렵게 만드는 원흉이다(아래 삭제 절).

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

그림 해설 (한 단계씩):

- (0) 넣기 전에 리사이즈부터 검사한다. 기준이 size가 아니라 used인 이유: 무덤도 탐사를 길게 만드는 "쓰인 자리"라서.
- (1) 제 칸부터 걸으며, 처음 본 무덤 위치는 "나중에 쓸 수도 있으니" 메모해 둔다.
- (2) 같은 키를 만나면 값만 교체하고 끝.
- (3) EMPTY까지 갔다면 같은 키가 없음이 확정 — 메모해 둔 무덤이 있으면 거기(재활용), 없으면 지금 칸에 쓴다.
- 무덤을 보자마자 쓰면 안 되는 이유: 그 뒤에 같은 키가 살아 있을 수 있다. 그러면 한 키가 두 자리에 존재하게 된다.

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

그림 해설 (한 단계씩):

- 지운 칸을 EMPTY로 되돌리면, 그 칸에서 밀려났던 뒤쪽 키들("B", "C")로 가는 탐사 길이 끊긴다 — 있는 키를 "없다"고 답하는 버그.
- 그래서 EMPTY 대신 묘비(TOMBSTONE)를 세운다: "지나가라, 하지만 여기서 멈추지는 마라".
- 값과 키는 null로 지워도(GC), 상태만은 묘비로 남는다. size는 줄지만 used는 안 준다.
- 묘비가 쌓이면 탐사만 길어지는데, 그 청소는 리사이즈가 맡는다(다음 절).

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

그림 해설 (한 단계씩):

- 리사이즈의 얼굴이 둘이다: 실제 원소가 많으면 "2배 확장", 무덤만 쌓였으면 "같은 크기로 재구축"(청소만).
- 어느 쪽이든 살아 있는 칸(OCCUPIED)만 새 배열에 다시 넣는다. 무덤은 버린다 — used가 size로 리셋된다.
- 새 배열엔 무덤도 중복도 없음이 확실하므로, 재삽입은 검사 없이 빈 칸만 찾으면 된다.

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

  - *상속(inheritance)*: 부모 클래스의 코드를 물려받고 필요한 부분만 고치는 것. LinkedHashMap은 ChainingHashMap의 put/remove를 그대로 쓴다.
  - *훅(hook) / 템플릿 메서드 패턴*: 부모가 일 순서를 정해두고 중간중간 "여기서 뭘 할지는 자식이 정하라"고 비워둔 메서드(afterPut 등). 자식은 그 빈 칸만 채워 행동을 바꾼다.

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

그림 해설 (한 단계씩):

- put: 부모가 버킷 일을 다 끝낸 뒤 afterPut이 불린다. 새 키였을 때만 순서 리스트 꼬리에 Entry를 붙인다(값 교체는 순서 불변).
- remove: 부모가 지운 뒤 afterRemove가 불린다. order 색인으로 Entry를 O(1)에 찾아, 02장 unlink 그림 그대로 앞뒤를 잇는다.
- keys(): 버킷 순서(예측 불가) 대신 first부터 next를 따라 걸어 "넣은 순서"로 낸다.
- 이 "해시맵(빠른 찾기) + 이중 연결 리스트(순서 유지)" 조합은 LRU 캐시의 뼈대다.

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

## 용어 풀이

- **맵(map)**: 키(이름표)로 값(내용물)을 찾는 자료구조. 한 키에 값은 하나.
- **키(key) / 값(value)**: 찾을 때 쓰는 이름표 / 그 이름표에 매달린 내용물.
- **해시 함수 / hashCode()**: 키를 하나의 정수로 요약하는 공식. 같은 키는 항상 같은 숫자. 다른 키가 같은 숫자일 수는 있다.
- **버킷(bucket)**: 해시로 계산된 번호의 칸. 사물함 한 칸.
- **충돌(collision)**: 서로 다른 키가 같은 칸 번호를 받는 일. 피할 수 없고, 다루는 방식이 구현을 가른다.
- **체이닝(chaining)**: 충돌한 키들을 같은 칸에 사슬(연결 리스트)로 매다는 방식.
- **오픈 어드레싱(open addressing) / 선형 탐사(linear probing)**: 충돌하면 배열의 다른 칸(선형 탐사는 바로 옆 칸)으로 밀려나는 방식. 사슬이 없다.
- **탐사(probe)**: 내 키나 빈 칸을 찾아 칸을 하나씩 확인하며 걷는 것.
- **묘비(tombstone)**: 오픈 어드레싱에서 지운 칸에 남기는 "여기 있었지만 지금은 없다" 팻말. EMPTY로 되돌리면 뒤로 밀려났던 키들로 가는 탐사 길이 끊기기 때문.
- **적재율(load factor)**: 칸이 얼마나 찼는지의 비율(size/칸 수). 문턱(체이닝 0.75, 선형 탐사 0.5)을 넘으면 리사이즈.
- **리사이즈(resize)**: 더 큰(또는 같은 크기의) 배열을 만들어 전부 다시 계산해 옮기는 것. 칸 수가 바뀌면 `% capacity` 결과가 바뀌므로 재계산이 필수.
- **equals**: 두 객체가 "내용상 같은가"의 판정. 규칙: equals로 같으면 hashCode도 같아야 한다.
- **모듈러(%, 나머지 연산)**: 나눈 나머지. 아무리 큰 해시값도 0..capacity-1 칸 번호로 접는 데 쓴다.
- **부호 비트(sign bit)**: int 맨 앞의 음수 표시 비트. `& 0x7fffffff`로 꺼서 항상 0 이상으로 만든다.
- **O(1), O(n), 평균/최악**: 걸리는 시간의 대략적 표기. 해시맵은 평균 O(1), 전부 한 칸에 몰리는 최악엔 O(n).
- **상환 분석(amortized, 분할상환)**: 가끔 드는 비싼 리사이즈를 여러 put에 나눠 평균 낸 것. 2배 확장이면 put 1회 평균 O(1).
- **GC(가비지 컬렉터)**: 아무도 가리키지 않는 객체를 치우는 자동 청소부. 지운 노드/칸의 참조를 null로 끊어야 청소된다.
- **노드(node) / 참조(reference)**: 사슬의 한 칸 / 값이 있는 곳을 가리키는 화살표.
- **상속(inheritance)**: 부모 클래스의 코드를 물려받아 일부만 고치는 것.
- **훅(hook) / 템플릿 메서드 패턴**: 부모가 일 순서를 정하고 중간에 비워둔 메서드를 자식이 채우는 디자인패턴. afterPut/afterRemove/afterClear가 훅이다.
- **이중 연결 리스트(doubly linked list)**: 각 칸이 앞뒤 화살표를 다 가진 리스트. LinkedHashMap이 삽입 순서를 기억하는 데 쓴다.
- **LRU 캐시**: 가장 오래 안 쓴 것부터 버리는 캐시. "해시맵 + 이중 연결 리스트" 조합의 대표 실무 사례(10장).
