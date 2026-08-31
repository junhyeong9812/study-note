# data-structure/26-persistent — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — PersistentList (`src/main/java/com/datastructure/persistent/PersistentList.java`)

- `PersistentList<E> prepend(E element)`
- `E head()`
- `PersistentList<E> tail()`
- `int size()`
- `boolean isEmpty()`
- `E get(int index)`
- `PersistentList<E> reverse()`
- `List<E> toList()`

## 계약 — PersistentMap (`src/main/java/com/datastructure/persistent/PersistentMap.java`)

- `PersistentMap<K, V> put(K key, V value)`
- `V get(K key)`
- `PersistentMap<K, V> remove(K key)`
- `boolean containsKey(K key)`
- `int size()`
- `default boolean isEmpty()`
- `List<K> keys()`

## 구현 — ConsList (`src/main/java/com/datastructure/persistent/ConsList.java`)

### 구조

```
ConsList : 셀 하나 = 머리 한 개 + 나머지 목록 하나. 그게 전부다.

  list = [A, B, C]

  +-------------+     +-------------+     +-------------+     +-------------+
  | head : A    |     | head : B    |     | head : C    |     | head : null |
  | tail  ------+---> | tail  ------+---> | tail  ------+---> | tail : null |
  | size : 3    |     | size : 2    |     | size : 1    |     | size : 0    |
  +-------------+     +-------------+     +-------------+     +-------------+
        ^                                                          EMPTY
      list                                          (private static 하나. 모두가 공유한다)

  세 필드가 전부 final 이다. 한 번 만든 셀은 영원히 안 바뀐다.
  -> 남이 그 셀을 가리켜도 뒤에서 내용이 바뀔 일이 없다. 이게 공유를 가능하게 하는 조건이다.

  size 를 셀마다 들고 있어서 (tail.size + 1) size() 가 O(1) 이다. 세러 가지 않는다.
  size == 0 인 셀만이 끝이다. head()/tail() 은 그때 NoSuchElementException.
  get(i) : 앞에서부터 tail 을 i 번 탄다 -> O(i). 인덱스 접근은 싸지 않다.
  of(...) : 뒤에서부터 prepend 를 반복해 순서를 맞춘다.
```

### 동작 — prepend (셀 공유)

```
prepend : 셀 하나만 새로 만들고, 나머지는 옛 목록을 그대로 가리킨다

before                                  after :  v2 = v1.prepend(A)

  v1 --> +------+   +------+   +-----+          v2 --> +------+
         |  B   +-->|  C   +-->|EMPTY|                 |  A   |   <- 새로 만든 셀은 이것 하나
         |size 2|   |size 1|   |size0|                 |size 3|
         +------+   +------+   +-----+                 +---+--+
                                                           |
                                                           v
                                       v1 --> +------+   +------+   +-----+
                                              |  B   +-->|  C   +-->|EMPTY|
                                              |size 2|   |size 1|   |size0|
                                              +------+   +------+   +-----+
                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                              한 글자도 안 건드렸다. v1 은 여전히 [B, C]

  코드는 한 줄이다 :  return new ConsList<>(element, this);
  새 셀의 size = tail.size + 1 = 3.

  비용 : 시간 O(1), 새 메모리 셀 1 개. 복사가 없다.
  v1 과 v2 가 [B, C] 부분을 같이 쓴다 = 구조 공유(structural sharing).
  가변 목록이었다면 v1 을 지키려고 통째로 복사해야 해서 O(n) 이었다.
```

### 동작 — reverse (여기서는 공유가 끊긴다)

```
ConsList 에는 "중간을 바꾸는" 연산이 아예 없다.
계약이 prepend / head / tail / get / reverse / toList 뿐이고, 값을 고치는 것은 머리 쪽뿐이다.
머리가 아닌 곳을 건드리려면 그 앞부분을 전부 다시 만들어야 하기 때문이다.
reverse 가 그 경우를 그대로 보여준다.

  reverse() : 앞에서부터 훑으며 결과에 하나씩 prepend 한다

    this = [A, B, C]
      out = EMPTY
      A 를 보고  ->  out = [A]
      B 를 보고  ->  out = [B, A]
      C 를 보고  ->  out = [C, B, A]

  v1 --> [A]-->[B]-->[C]-->EMPTY        원본은 그대로 살아 있다
  v2 --> [C]-->[B]-->[A]-->EMPTY        하지만 셀은 하나도 공유하지 않는다

  비용 : 시간 O(n), 새 셀 n 개.
  prepend 만 O(1) 이고 공유가 되는 이유는, 그 연산만이 "기존 셀의 앞에 붙이는" 모양이라
  기존 셀을 그대로 tail 로 재사용할 수 있기 때문이다.
  뒤쪽이나 순서를 건드리는 연산은 그 재사용 조건이 깨진다.
  (뒤에 나오는 PersistentTreeMap 의 경로 복사가 이 문제를 O(log n) 으로 줄이는 답이다)
```


### 필드
- `EMPTY` (static) — 역할:
- `head` — 역할:
- `tail` — 역할:
- `size` — 역할:

### `private ConsList()` / `private ConsList(E head, ConsList<E> tail)`
- 하는 일:
- 논리:
- 비용(왜):

### `static <E> ConsList<E> empty()`
- 하는 일:
- 논리:
- 비용(왜):

### `static <E> ConsList<E> of(E... elements)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()`
- 하는 일:
- 논리:
- 비용(왜):

### `E head()`
- 하는 일:
- 논리:
- 비용(왜):

### `ConsList<E> tail()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<E> toList()`
- 하는 일:
- 논리:
- 비용(왜):

### `ConsList<E> prepend(E element)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `E get(int index)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `ConsList<E> reverse()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — PersistentTreeMap (`src/main/java/com/datastructure/persistent/PersistentTreeMap.java`)

### 구조

```
PersistentTreeMap : 값이 안 바뀌는 이진 탐색 트리. 균형 잡기(회전)는 없다.

  Node
  +-------------------------------------------------+
  | key   : 비교 기준 (Comparable, null 금지)       |
  | value : 값 (null 금지 - get 의 null 이 "없음")  |
  | left  : key 보다 작은 것들                       |
  | right : key 보다 큰 것들                         |
  | size  : 1 + sizeOf(left) + sizeOf(right)        |
  +-------------------------------------------------+
  다섯 필드 전부 final. 만들 때 size 를 계산해 굳혀둔다 -> size() 는 root.size 로 O(1).

  root
   |
   v
                    +--------+
                    | 50 : e |
                    +---+----+
                   /          \
            +--------+        +--------+
            | 30 : c |        | 70 : g |
            +---+----+        +---+----+
            /       \         /        \
      +------+   +------+  +------+  +------+
      |20 : b|   |40 : d|  |60 : f|  |80 : h|
      +------+   +------+  +------+  +------+

  get(key)  : 루트에서 key.compareTo(cur.key) 로 좌/우를 골라 내려간다. O(높이). 반복문이다.
  keys()    : 중위 순회 -> 정렬된 키 목록. O(n).
  EMPTY     : private static 하나를 empty() 가 캐스팅해 돌려준다 (빈 맵은 하나면 충분하다).
  균형 로직이 없으므로 키를 정렬된 순서로 넣으면 한 줄로 늘어져 높이가 n 이 된다.
  nodesCreated : "직전 연산이 새로 만든 노드 수". 공유가 실제로 먹었는지 재는 계기판이다.
```

### 동작 — put (경로 복사)

```
put(45, "x") : 루트에서 45 가 들어갈 자리까지의 "길"에 있는 노드만 새로 만든다

before (v1)                              after (v2 = v1.put(45, "x"))

           50                                       [50]*
          /  \                                     /     \
        30    70                                [30]*      70
       /  \   /  \                              /   \      /  \
     20   40 60   80                          20    [40]* 60    80
                                                       \
                                                       [45]*

  [ ]* = 이번에 새로 만든 노드.  표시 없는 노드는 v1 의 그 객체를 그대로 가리킨다.

  길 : 50 -> (45 < 50, 왼쪽) 30 -> (45 > 30, 오른쪽) 40 -> (45 > 40, 오른쪽) 빈 자리
  새 노드 = 그 길 위의 노드 3 개 + 실제로 넣은 45 = 4 개
  공유 노드 = 20, 70, 60, 80 = 4 개  (70 을 공유하면 그 아래 60, 80 도 자동으로 딸려온다)

  왜 길 위의 노드까지 새로 만드나 :
    40 의 right 를 45 로 바꿔야 하는데 Node.right 가 final 이다. 그래서 40 을 새로 만든다.
    그러면 30 의 right 가 새 40 을 가리켜야 하니 30 도 새로 만든다. 루트까지 이 사슬이 올라간다.
    옆가지(20, 70)는 바뀔 이유가 없으므로 옛 객체를 그대로 넘겨준다.

  private put(node, key, value, created) 는 맨 위에서 created[0]++ 를 한 번 한다.
  = 재귀 호출 횟수 = 만든 노드 수. 그 값이 nodesCreatedByLastPut() 이다.

  비용 : 시간 O(높이), 새 메모리 O(높이) = 균형이 잡혀 있으면 O(log n).
         나머지 n - O(log n) 개는 복사하지 않는다.
  v1 은 전혀 손대지 않았다. 모든 필드가 final 이므로 손댈 방법도 없다.
  같은 키를 다시 put 하면 그 자리에서 new Node(key, value, node.left, node.right) 로
  값만 갈아끼운 새 노드를 만든다 (아래 서브트리는 통째로 공유).
```

### 동작 — 두 버전이 공존

```
put 이 끝난 뒤 v1 과 v2 는 둘 다 살아 있고, 트리의 대부분을 같이 쓴다

  v1 (v1.root = 50)                          v2 (v2.root = 50*)

            50                                        50*
           /  \                                     /     \
         30    70 (=)                             30*       70 (=)
        /  \   /   \                             /   \      /   \
   20 (=)   40  60(=)  80(=)                 20 (=)    40*   60(=)  80(=)
                                                         \
                                                         45*

   *   = v2 를 만들며 새로 만든 노드  (4 개 : 50*, 30*, 40*, 45*)
   (=) = 두 트리가 같은 객체를 가리키는 노드 (4 개 : 20, 70, 60, 80)
         70 하나를 공유하면 그 아래 60, 80 은 자동으로 딸려온다
   표시 없는 50, 30, 40 은 v1 에만 남는다
   (v2 는 안 쓰지만 v1 이 살아 있으므로 GC 도 안 된다 - 옛 버전을 들고 있는 값이다)

  countSharedNodes(before, after) 가 세는 것이 바로 이 "같은 객체" 수다.
  값이 같은 것이 아니라 == 인 것만 센다 (IdentityHashMap 이나 == 비교가 필요한 이유).
  1000 개짜리 맵에 키 하나를 넣으면 990 개가 넘게 공유된다
  = 새로 만든 것이 경로뿐이라는 직접 증거.

  읽기에 락이 필요 없는 이유도 여기 있다.
  옛 뿌리에서 내려가는 길에 있는 노드는 그 뒤로 절대 안 바뀐다.
  쓰는 쪽이 새 뿌리를 만드는 동안에도 읽는 쪽은 옛 뿌리로 일관된 스냅샷을 본다.
  바뀌는 것은 "어느 뿌리를 볼 것인가" 하나뿐이다.

  remove 는 조금 다르다. 없는 키면 newRoot == root 라서 this 를 그대로 돌려준다
  (새 버전을 만들지 않는다). 지울 것이 있으면 후계자(오른쪽 서브트리의 최솟값)를 끌어올리며
  그 길도 함께 복사한다.
```


### 필드
- `EMPTY` (static) — 역할:
- `root` — 역할:
- `nodesCreated` — 역할:
- `Node.key` / `Node.value` / `Node.left` / `Node.right` / `Node.size` — 역할:

### `static <K, V> PersistentTreeMap<K, V> empty()`
- 하는 일:
- 논리:
- 비용(왜):

### `static int sizeOf(Node<?, ?> node)` / `static void requireKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `int nodesCreatedByLastPut()`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()`
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

### `List<K> keys()` / `void inorder(Node<K, V> node, List<K> out)`
- 하는 일:
- 논리:
- 비용(왜):

### `int height()` / `int height(Node<K, V> node)`
- 하는 일:
- 논리:
- 비용(왜):

### `PersistentTreeMap<K, V> put(K key, V value)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V> put(Node<K, V> node, K key, V value, int[] created)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `PersistentTreeMap<K, V> remove(K key)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V> remove(Node<K, V> node, K key, int[] created)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V> removeMin(Node<K, V> node, int[] created)` (private)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — VersionedStore (`src/main/java/com/datastructure/persistent/VersionedStore.java`)

### 구조

```
VersionedStore : 버전마다 그때의 뿌리를 통째로 보관한다. 보관해도 싼 이유가 경로 복사다.

  versions (ArrayList<PersistentTreeMap>)  - 인덱스가 곧 버전 번호. 한 번 넣으면 절대 안 뺀다
    idx      0          1          2          3
         +----------+----------+----------+----------+
         |  EMPTY   |  root1   |  root2   |  root3   |
         +----+-----+----+-----+----+-----+----+-----+
              |          |          |          |
              v          v          v          v
           (빈 맵)    각 뿌리는 서로 다른 객체지만, 아래로 내려가면
                      노드의 대부분을 이웃 버전과 함께 쓴다
                      (root2 가 새로 만든 노드는 root1 로부터의 경로뿐)

  history (ArrayList<Integer>)  - 되돌리기 경로. 값은 versions 의 인덱스다
         +---+---+---+---+
         | 0 | 1 | 2 | 3 |
         +---+---+---+---+
                       ^
                     cursor = 3

  cursor        : history 안에서 지금 서 있는 자리
  currentVersion() = history.get(cursor)          지금 보고 있는 버전 번호
  versionCount()   = versions.size()              만들어진 버전 수 (history 길이와 다를 수 있다)
  nodesCreated  : 지금까지 만든 노드 수의 누적 합. 공유가 먹히는지 재는 계기판

  versions 와 history 를 나눈 것이 요점이다.
    versions = 만들어진 모든 상태 (영원히 남는다. 과거 조회의 근거)
    history  = 되돌리기 위해 걸어온 길 (undo 후 새로 쓰면 잘려나간다)
```

### 동작 — 커밋 / 조회

```
put / remove -> commit(next) 로 모인다

  commit(next)
    [1] next == current() 이면 (바뀐 게 없다) 버전을 늘리지 않고 지금 번호를 돌려준다
        remove 가 없는 키를 지우려 할 때 this 를 그대로 돌려주므로 여기로 온다
    [2] nodesCreated += next.nodesCreatedByLastPut()
    [3] versions 에 next 를 덧붙인다 (옛 버전은 그대로 남는다)
    [4] cursor 뒤에 남아 있던 history 를 잘라낸다
    [5] history 에 새 인덱스를 붙이고 cursor 를 끝으로 옮긴다

  undo 를 하고 나서 새로 커밋했을 때 :

  (a) 네 번 커밋한 상태
        versions : [ 0 , 1 , 2 , 3 ]
        history  : [ 0 , 1 , 2 , 3 ]
                                 ^ cursor = 3    ->  currentVersion() = 3

  (b) undo() 두 번  - cursor 만 뒤로 간다. 아무것도 안 지운다
        versions : [ 0 , 1 , 2 , 3 ]
        history  : [ 0 , 1 , 2 , 3 ]
                         ^ cursor = 1    ->  currentVersion() = 1

  (c) 여기서 put(...)  - 버려진 가지(2, 3)가 history 에서만 잘려나간다
        versions : [ 0 , 1 , 2 , 3 , 4 ]      <- 2 와 3 은 여기 그대로 남아 있다
        history  : [ 0 , 1 , 4 ]
                             ^ cursor = 2    ->  currentVersion() = 4

        redo() 는 이제 못 한다 (cursor 가 끝이다). 하지만
        snapshot(2) / get(2, key) 로는 버전 2 를 여전히 읽을 수 있다.
        "되돌리기 경로에서 빠진 것"과 "사라진 것"은 다르다.

  undo() : cursor == 0 이면 false, 아니면 cursor-- 하고 true
  redo() : cursor >= history.size() - 1 이면 false, 아니면 cursor++ 하고 true
           둘 다 트리를 만들지도 복사하지도 않는다. 정수 하나를 움직일 뿐이다. O(1).

  조회
    get(key)          = versions.get(currentVersion()).get(key)
    get(version, key) = snapshot(version).get(key)     어느 시점이든 O(높이)
    snapshot(version) = versions.get(version). 범위 밖이면 IndexOutOfBoundsException
                        돌려주는 맵 자체가 불변이라 그냥 내줘도 안전하다 (방어 복사가 필요 없다)

  버전 하나를 더 만드는 값 = 새 노드 O(log n) 개.
  가변 맵으로 매 시점 스냅샷을 남기려면 통째로 복사해서 버전당 O(n) 이다.
  m 번의 명령이면 O(m n) 대 O(m log n) - 그 차이를 테스트가 노드 수로 잰다.
```


### 필드
- `versions` — 역할:
- `history` — 역할:
- `cursor` — 역할:
- `nodesCreated` — 역할:

### `VersionedStore()`
- 하는 일:
- 논리:
- 비용(왜):

### `int currentVersion()` / `int versionCount()` / `long nodesCreated()`
- 하는 일:
- 논리:
- 비용(왜):

### `int put(K key, V value)` / `int remove(K key)`
- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)` / `V get(int version, K key)`
- 하는 일:
- 논리:
- 비용(왜):

### `PersistentTreeMap<K, V> snapshot(int version)`
- 하는 일:
- 논리:
- 비용(왜):

### `int commit(PersistentTreeMap<K, V> next)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean undo()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean redo()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ConsList (cons 셀 공유) | | | |
| PersistentTreeMap (경로 복사) | | | |
| VersionedStore (버전 스냅샷 보관) | | | |

## 문제 — PersistentProblems (`src/main/java/com/datastructure/persistent/PersistentProblems.java`)

### 문제 1. 명령 재생과 시점별 스냅샷 — `replay(List<String[]> commands)`

> 문제 설명: 명령을 하나씩 실행하며 매 시점의 맵을 전부 남긴다. 결과의 0번은 아무것도 실행하기 전,
> i+1번은 i번 명령을 실행한 뒤다.
> 명령은 두 가지다.
> ```
>   {"put", 키, 값}    값은 정수 문자열
>   {"remove", 키}
> ```
> 그 밖의 것, 칸 수가 안 맞는 것, 빈 명령은 IllegalArgumentException 이다.
> 생각할 것: 가변 맵으로 이 일을 하면 스냅샷마다 맵을 통째로 복사해야 해서 O(m n) 이다.
> 여기서는 O(m log n) 이다. 그 차이를 테스트가 노드 수로 잰다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 두 버전이 공유하는 노드 수 — `countSharedNodes(PersistentTreeMap<K,V> before, PersistentTreeMap<K,V> after)`

> 문제 설명: 두 버전이 실제로 공유하는 노드의 수.
> 값이 같은 것이 아니라 같은 객체인 것만 센다.
> 1000개짜리 맵에 키 하나를 넣으면 990개가 넘게 나와야 한다.

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/26-persistent/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/26-persistent/src/main/java/com/datastructure/persistent/`
- 테스트: `/home/jun/project/myway/data-structure/26-persistent/src/test/java/com/datastructure/persistent/`
- 정답 구현: `/home/jun/project/myway/data-structure/26-persistent/impl/`
