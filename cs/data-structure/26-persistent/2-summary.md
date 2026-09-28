# data-structure/26-persistent — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.
> 2026-09-28: 통일 골격 양식으로 재배치 + 새 절 추가(Claude 작성 — 기존 본문은 이동만).

## 해결하는 문제

지금까지의 자료구조는 전부 덮어썼다. `put`을 하면 이전 상태가 사라져 "5분 전 상태"를 물을 방법이 없다 — 시간 축이 없다.
버전마다 통째로 복사해 두면 시간 축은 생기지만 수정 하나가 O(n)이라 쓸모가 없다.

```text
덮어쓰기 (01~25)             통째 복사                    경로 복사 (26)
  v1 [50]                    v1 [50]     v2 [50]'          v1 [50]      v2 [50]*
      / \      put(45)          / \         / \                / \       /  \
   [30] [70]  ----->        [30][70]   [30]'[70]'         [30] [70]  [30]*  |
   v1 은 사라진다           전부 새로 = O(n)            /  \    ^______|    |
                                                       [20][40]*<- 옛 [40]  공유
                                                             \
                                                            [45]*
```

영속 자료구조는 바꾸지 않고 새 버전을 만든다. 비용은 바뀐 **길목**만 새로 만들고 나머지는 옛 버전과 공유해서 낸다 — 1023개 트리에 키 하나를 넣으면 새 노드 11개, 공유 1013개다.
공유가 안전한 이유는 노드가 불변이기 때문이다. 불변이 먼저이고 공유는 그 결과다.

- 쉬운 예: 수정 금지 공책 + 포스트잇 — 바뀐 부분만 새 종이에 쓰고 "3쪽부터는 옛 공책 그대로"라고 가리킨다.
- 똑같은 구조다: 이 노트의 `ConsList`(앞에 붙이면 셀 하나), `PersistentTreeMap`(경로 복사), `VersionedStore`(버전마다 뿌리만 보관).
- 실무 예: git 커밋(바뀐 파일만 새 객체), 편집기의 undo, Clojure·Scala의 불변 컬렉션.
  - *영속(persistent)*: 고칠 때마다 새 버전이 생기고 옛 버전도 그대로 읽히는 성질. 디스크 저장과는 다른 말이다.
  - *구조 공유(structural sharing)*: 두 버전이 안 바뀐 부분을 복사하지 않고 같은 객체를 함께 가리키는 것.

### 한눈에 — 쉽게 말하면

**비유: 수정 금지 공책 + 포스트잇.** 한 번 쓴 공책 페이지는 절대 지우거나 고치지 않는다.
내용을 바꾸고 싶으면 바뀐 부분만 새 종이에 쓰고, 안 바뀐 부분은 "3쪽부터는 옛날 공책 그대로 보세요"라고 가리킨다.
그래서 "어제 버전"과 "오늘 버전"이 둘 다 살아 있고, 겹치는 부분은 종이 한 장을 같이 쓴다.

- 영속(persistent) 자료구조 = 고칠 때마다 **새 버전**이 생기고, **옛 버전도 그대로 읽을 수 있는** 자료구조.
- 통째로 복사하면 너무 비싸니까, **바뀐 부분만 새로 만들고 나머지는 공유**한다(구조 공유).
- 리스트는 맨 앞에 붙일 때 셀 1개만, 트리는 바뀐 자리까지 가는 "길"만 새로 만든다(경로 복사).

```text
  v1(어제) --> [A]--+
                    |
                    +--> [B] --> [C]      <- 이 부분은 두 버전이 같이 쓴다
                    |
  v2(오늘) --> [X]--+
```

이 문서의 자료구조들이 **똑같은 구조다**: 바뀐 조각만 새로 만들고, 나머지는 옛 버전과 공유한다.
실무에서도 같은 아이디어를 쓴다 — git 은 커밋마다 바뀐 파일만 새로 저장하고 나머지는 이전 커밋 것을 가리키며, 편집기의 undo 도 매번 문서 전체를 복사하지 않는다.

## 동작·원리

### 전체 흐름

```text
[1] 불변이 먼저다                          [2] 리스트 — 앞에 붙이면 셀 하나
    Node / 셀의 모든 필드가 final               v2 = v1.prepend(A)
    한 번 만든 조각은 영원히 안 바뀐다          v2 --> [A] --> v1 --> [B] --> [C] --> EMPTY
    -> 남이 가리켜도 뒤에서 변할 일이 없다       새로 만든 것 = [A] 하나. v1 은 그대로 [B, C]
              |                                   append / reverse 는 n 개 전부 새로 (공유 0)
              v
[3] 트리 — 경로 복사                        [4] 버전 저장소 — 뿌리만 보관
    v2 = v1.put(45)                              versions [ EMPTY | root1 | root2 | root3 ]  영원히 남는다
    뿌리 -> 45 자리까지의 길 위 노드만 새로       history  [   0   |   1   |   2   |   3   ]  undo/redo 의 길
    옆가지는 v1 의 참조를 그대로 넘긴다                                                 ^ cursor
    새 노드 = height + 1 개, 나머지 공유          undo = cursor 만 뒤로. 새 커밋 = cursor 뒤를 잘라낸다
              |
              v
[5] 대가
    균형을 못 잡는다 (회전이 없다) -> 정렬 입력이면 O(n) 조회 + O(n) 메모리 + 깊은 재귀
    버전을 아무도 안 보면 새 노드 전부가 GC 쓰레기 -> 영속이 이기는 것은 버전이 필요할 때뿐
    공유 여부는 값으로 검증할 수 없다 -> 참조 동일성(==) 을 세야 한다
```

- [1] 출발점은 불변이다. `final` 필드만 있는 노드는 만들어진 뒤 절대 안 바뀌므로, 여러 버전이 같은 노드를 가리켜도 안전하다. 순서를 뒤집어 "공유하니까 불변"이라고 하면 안 된다.
  - *불변(immutable)*: 한 번 만들면 내용이 절대 안 바뀌는 것. 바꾸고 싶으면 새것을 만든다.
- [2] 리스트는 셀 하나가 "값 + 나머지 목록"이라 맨 앞에 붙이는 것은 새 셀 하나로 끝난다(O(1)). 마지막 셀을 고칠 수 없으므로 뒤에 붙이기·뒤집기는 n개를 전부 새로 만든다.
  - *cons 셀*: `head`(값 하나) + `tail`(나머지 목록)로 된 리스트의 기본 조각.
- [3] 트리는 바뀐 자리까지 내려가는 길 위의 노드만 새로 만든다. 재귀가 되짚어 올라오며 층마다 새 노드를 만들고, 안 지나간 자식은 받은 참조를 그대로 넘긴다.
  - *경로 복사(path copying)*: 뿌리에서 바뀐 자리까지의 "길"만 복사하고 옆가지는 공유하는 방법. 새 노드 수 = 높이 + 1.
- [4] 버전 저장소는 버전마다 그 시점의 뿌리를 목록에 담는다. 뿌리는 서로 다른 객체지만 아래로 내려가면 대부분을 이웃 버전과 함께 쓴다. `versions`(만들어진 모든 상태)와 `history`(되돌리기 길)를 나눈 것이 요점이다.
  - *커서(cursor)*: `history` 안에서 지금 서 있는 자리. undo는 커서만 뒤로 옮기고 아무것도 지우지 않는다.
- [5] 회전을 못 쓰니 균형이 없고, 버전을 안 보면 상수 인자만 손해이며, 공유는 값이 아니라 참조로만 검증된다 — 셋 다 이 구조의 성질이다.

### 계약 — PersistentList (`src/main/java/com/datastructure/persistent/PersistentList.java`)

- `PersistentList<E> prepend(E element)`
- `E head()`
- `PersistentList<E> tail()`
- `int size()`
- `boolean isEmpty()`
- `E get(int index)`
- `PersistentList<E> reverse()`
- `List<E> toList()`

### 계약 — PersistentMap (`src/main/java/com/datastructure/persistent/PersistentMap.java`)

- `PersistentMap<K, V> put(K key, V value)`
- `V get(K key)`
- `PersistentMap<K, V> remove(K key)`
- `boolean containsKey(K key)`
- `int size()`
- `default boolean isEmpty()`
- `List<K> keys()`

### 구현 — ConsList (`src/main/java/com/datastructure/persistent/ConsList.java`)

#### 구조

아래 그림을 읽는 데 필요한 말 세 개만 먼저.
  - *셀(cons 셀)*: "값 하나 + 나머지 목록이 어디 있는지" 두 칸짜리 조각. 이게 사슬처럼 이어져 리스트가 된다.
  - *final*: 자바에서 "이 칸은 한 번 채우면 다시 못 바꾼다"는 표시.
  - *O(1) / O(i) / O(n)*: 일의 양이 항상 일정 / i번째까지 걸어간 만큼 / 전체 개수에 비례.

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

#### 동작 — prepend (셀 공유)

**언제 쓰나**: 리스트 맨 앞에 원소 하나를 붙이면서, 옛 리스트도 그대로 살려두고 싶을 때.
그림 먼저 — 왼쪽이 전 상태(v1), 오른쪽이 후 상태(v2). 새로 만든 것은 셀 딱 하나다.

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

그림에서 일어난 일을 문장으로 읽으면: 새 셀 A 하나를 만든다 → 그 셀의 tail 이 옛 리스트 v1 을 통째로 가리킨다 → 끝. v1 쪽은 아무것도 안 변했다.
  - *구조 공유(structural sharing)*: 두 버전이 안 바뀐 부분을 복사하지 않고 같은 조각을 함께 가리키는 것.
  - *가변(mutable)*: 만든 뒤에도 내용을 고칠 수 있는 것. 불변의 반대말.

#### 동작 — reverse (여기서는 공유가 끊긴다)

**언제 쓰나**: 리스트의 순서를 통째로 뒤집고 싶을 때. prepend 와 달리 이 연산은 셀을 하나도 공유하지 못한다 — 왜 그런지가 이 절의 요점이다.

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

#### 필드
- `EMPTY` (static) — 역할:
- `head` — 역할:
- `tail` — 역할:
- `size` — 역할:

#### `private ConsList()` / `private ConsList(E head, ConsList<E> tail)`
- 하는 일:
- 논리:
- 비용(왜):

#### `static <E> ConsList<E> empty()`
- 하는 일:
- 논리:
- 비용(왜):

#### `static <E> ConsList<E> of(E... elements)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()` / `boolean isEmpty()`
- 하는 일:
- 논리:
- 비용(왜):

#### `E head()`
- 하는 일:
- 논리:
- 비용(왜):

#### `ConsList<E> tail()`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<E> toList()`
- 하는 일:
- 논리:
- 비용(왜):

#### `ConsList<E> prepend(E element)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `E get(int index)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `ConsList<E> reverse()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — PersistentTreeMap (`src/main/java/com/datastructure/persistent/PersistentTreeMap.java`)

#### 구조

리스트는 "맨 앞"만 싸게 고칠 수 있었다. 아무 키나 싸게 넣고 빼려면 트리가 필요하다. 그림 앞에 말 세 개만.
  - *이진 탐색 트리(BST)*: 각 노드의 왼쪽에는 작은 키, 오른쪽에는 큰 키를 두는 트리. 비교하며 내려가면 자리가 나온다.
  - *Comparable*: "나와 남을 비교해 누가 큰지 말할 수 있다"는 자바 규약. 키 비교에 쓴다.
  - *중위 순회(inorder)*: 트리를 "왼쪽 → 자기 → 오른쪽" 순서로 도는 것. BST 에서는 결과가 정렬돼 나온다.

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

#### 동작 — put (경로 복사)

**언제 쓰나**: 맵에 키-값 하나를 넣으면서, 옛 버전 맵도 그대로 살려두고 싶을 때.
그림 먼저 — 왼쪽이 전 상태(v1), 오른쪽이 후 상태(v2). `*` 붙은 노드만 새로 만들었다.
  - *경로 복사(path copying)*: 바뀐 자리까지 내려간 "길" 위의 노드만 새로 만들고, 옆가지는 옛 트리 것을 그대로 가리키는 방법.
  - *재귀(recursion)*: 함수가 자기 자신을 다시 불러 "한 층 아래의 같은 문제"를 푸는 방식. put 이 층마다 자신을 부른다.

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

#### 동작 — 두 버전이 공존

**언제 쓰나**: put 이 끝난 직후의 세상을 보는 절이다. 옛 버전(v1)과 새 버전(v2)이 동시에 살아 있고, 대부분을 같이 쓴다.
  - *`==` 비교*: 값이 같은지가 아니라 "정말 같은 객체(같은 메모리)인지"를 따지는 비교.
  - *GC(가비지 컬렉션)*: 아무도 안 가리키는 객체를 자바가 알아서 치우는 것. 누군가 가리키는 한 안 치운다.
  - *락(lock)*: 동시에 여러 작업이 데이터를 건드릴 때 "한 번에 하나만"을 강제하는 자물쇠.

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

#### 필드
- `EMPTY` (static) — 역할:
- `root` — 역할:
- `nodesCreated` — 역할:
- `Node.key` / `Node.value` / `Node.left` / `Node.right` / `Node.size` — 역할:

#### `static <K, V> PersistentTreeMap<K, V> empty()`
- 하는 일:
- 논리:
- 비용(왜):

#### `static int sizeOf(Node<?, ?> node)` / `static void requireKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int nodesCreatedByLastPut()`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()` / `boolean isEmpty()`
- 하는 일:
- 논리:
- 비용(왜):

#### `V get(K key)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean containsKey(K key)`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<K> keys()` / `void inorder(Node<K, V> node, List<K> out)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int height()` / `int height(Node<K, V> node)`
- 하는 일:
- 논리:
- 비용(왜):

#### `PersistentTreeMap<K, V> put(K key, V value)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Node<K, V> put(Node<K, V> node, K key, V value, int[] created)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `PersistentTreeMap<K, V> remove(K key)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Node<K, V> remove(Node<K, V> node, K key, int[] created)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `Node<K, V> removeMin(Node<K, V> node, int[] created)` (private)
- 하는 일:
- 논리:
- 비용(왜):

#### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — VersionedStore (`src/main/java/com/datastructure/persistent/VersionedStore.java`)

#### 구조

불변 맵(위의 PersistentTreeMap)이 재료다. 버전마다 그 시점의 뿌리(root)를 목록에 담아두면 "몇 번 버전 보여줘"가 공짜가 된다.
  - *스냅샷(snapshot)*: 어느 한 시점의 모습을 통째로 보관한 것. 사진 찍어두기.
  - *커서(cursor)*: "지금 어디를 보고 있는지"를 가리키는 위치 표시 숫자 하나.

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

#### 동작 — 커밋 / 조회

**언제 쓰나**: put/remove 로 새 버전을 하나 확정(커밋)할 때, 그리고 아무 시점이나 다시 읽을 때. undo 뒤에 새로 쓰면 무슨 일이 나는지가 핵심 그림이다.
  - *방어 복사(defensive copy)*: 내부 데이터를 밖에 줄 때 남이 못 고치게 복사본을 주는 것. 여기서는 맵이 불변이라 원본을 그냥 줘도 안전하다.

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

#### 필드
- `versions` — 역할:
- `history` — 역할:
- `cursor` — 역할:
- `nodesCreated` — 역할:

#### `VersionedStore()`
- 하는 일:
- 논리:
- 비용(왜):

#### `int currentVersion()` / `int versionCount()` / `long nodesCreated()`
- 하는 일:
- 논리:
- 비용(왜):

#### `int put(K key, V value)` / `int remove(K key)`
- 하는 일:
- 논리:
- 비용(왜):

#### `V get(K key)` / `V get(int version, K key)`
- 하는 일:
- 논리:
- 비용(왜):

#### `PersistentTreeMap<K, V> snapshot(int version)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int commit(PersistentTreeMap<K, V> next)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean undo()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean redo()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

## 쓰이는 곳

- **Clojure · Scala의 불변 컬렉션** — 해시 맵·집합은 같은 경로 복사를 32갈래 해시 트라이(HAMT, Scala 2.13은 그 변형 CHAMP)에 적용해 정렬 입력의 편향 없이 얕은 깊이를 유지한다. 정렬 맵(Clojure `sorted-map`)은 영속 레드블랙 트리로, 회전까지 경로 복사로 처리해 균형을 잡는다. `assoc`/`updated`가 새 컬렉션을 돌려주는 것이 `put`의 반환형과 같다.
- **git 객체 저장소** — 커밋마다 바뀐 파일(blob)과 그 길 위의 tree만 새로 만들고 나머지는 이전 커밋의 객체를 가리킨다. 참조 대신 해시로 공유를 표현하는 것이 [27-merkle-tree](../27-merkle-tree/2-summary.md)다.
- **React 상태 관리 — Immer · Immutable.js** — 상태를 불변으로 두고 바뀐 경로만 새 객체로 만든다. 참조 비교 한 번으로 "바뀌었나"를 알 수 있어 재렌더링 판정이 싸진다 — React는 상태 변경을 `Object.is` 참조 비교로 판정하고, Immer는 바뀐 경로만 새 객체로 만들며 나머지를 공유한다(React·Immer 문서).
- **DB의 MVCC(다중 버전 동시성 제어)** — 갱신 시 옛 행을 덮지 않고 새 버전을 쓰고, 읽기 트랜잭션은 자기 시점의 버전을 본다. "조회에 잠금이 필요 없다"가 같은 생각이다(정답 3번 참고).
- **copy-on-write 파일시스템 스냅샷 — ZFS · Btrfs** — 블록을 덮어쓰지 않고 새로 쓰며 바뀐 길 위의 메타데이터만 갱신한다. 스냅샷 = 옛 뿌리를 붙잡아 두기(ZFS·Btrfs 설계 문서의 copy-on-write 설명). 공유는 객체 참조가 아니라 블록 포인터로 표현된다.
- **편집기의 undo/redo** — 문서 전체를 복사하지 않고 버전을 남긴다. `VersionedStore`의 `versions`/`history` 분리와 "undo 뒤 새 편집이 redo 경로를 잘라내는" 규칙이 그대로다.
- **이 노트가 가져다 쓰는 것** — [02-linked-list](../02-linked-list/2-summary.md)(`ConsList`의 원형), [06-binary-search-tree](../06-binary-search-tree/2-summary.md)(`PersistentTreeMap`의 탐색·삭제).

## 적용 — 풀어나가는 법

영속 구조 문제는 "버전을 누가 볼 것인가"를 먼저 묻는 데서 갈린다.
순서: ① 옛 버전을 읽을 일이 있는지 확인한다(없으면 가변 구조가 11배 싸다) → ② 연산이 어느 길목을 지나는지 그린다 — 그 길만 새로 만들고 옆가지는 참조를 넘긴다 → ③ 새로 만든 노드 수(`nodesCreated`)와 공유 노드 수를 참조 동일성으로 센다 — 값 비교로는 검증되지 않는다 → ④ 버전 목록과 되돌리기 길을 분리해 undo/redo와 시점 조회를 얹는다.
아래 과제 넷이 이 순서로 풀린다.

### 문제 — 이 챕터가 시키는 것

01번부터 25번까지 만든 것은 전부 덮어썼다.
`put` 을 하면 이전 상태가 사라져서 "5분 전 상태"를 물으면 답할 방법이 없었다 — 시간 축이 없었다.
여기서는 **바꾸지 않고 새 버전을 만드는** 자료구조를 만든다.
버전마다 통째로 복사하면 수정 하나가 O(n) 이라 쓸모가 없으므로, 바뀐 길목만 새로 만들고 나머지는 옛 버전과 공유한다(경로 복사).

**과제**

1. `ConsList` (TODO 3개) — 앞에만 붙이는 불변 목록. `prepend` 는 셀 하나만 만들고 꼬리로 옛 목록 자신을 가리킨다
2. `PersistentTreeMap` (TODO 2개) — 경로 복사로 만드는 불변 이진 탐색 트리. 지나간 길목만 새로 만들고 안 지나간 가지는 받은 참조를 그대로 넘긴다
3. `VersionedStore` (TODO 3개) — 버전을 전부 들고 있는 저장소. undo, redo, 그리고 아무 시점 조회
4. `PersistentProblems` (TODO 2개) — `replay`(명령 재생과 시점별 스냅샷), `countSharedNodes`(두 버전이 공유하는 노드 수)

순서는 `ConsList 3개 -> PersistentTreeMap 2개 -> VersionedStore 3개 -> PersistentProblems 2개` 다.
`./run.sh 26` 을 돌리면 처음에 **61개 중 55개가 실패한다.**
필드 이름 `root`, `Node` 의 `key, value, left, right, size`, `ConsList` 의 `head, tail, size` 는 테스트가 직접 들여다본다.

이 박스의 계약은 `assertEquals` 로 검증할 수 없다.
`put` 이 안 지나간 부분트리를 통째로 복사하도록 고쳐도 답은 한 글자도 안 틀리고 **61개 중 56개를 통과**한다.
갈리는 것은 참조 동일성을 보는 다섯 개뿐이다(`assertSame` 하나와 `countSharedNodes` 넷).

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ConsList (cons 셀 공유) | | | |
| PersistentTreeMap (경로 복사) | | | |
| VersionedStore (버전 스냅샷 보관) | | | |

### 문제 — PersistentProblems (`src/main/java/com/datastructure/persistent/PersistentProblems.java`)

#### 문제 1. 명령 재생과 시점별 스냅샷 — `replay(List<String[]> commands)`

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

#### 문제 2. 두 버전이 공유하는 노드 수 — `countSharedNodes(PersistentTreeMap<K,V> before, PersistentTreeMap<K,V> after)`

> 문제 설명: 두 버전이 실제로 공유하는 노드의 수.
> 값이 같은 것이 아니라 같은 객체인 것만 센다.
> 1000개짜리 맵에 키 하나를 넣으면 990개가 넘게 나와야 한다.

- 내 접근:
- 논리:
- 비용(왜):

## 장애 시나리오와 대처

**1. 정렬된 키를 넣다가 스택이 터짐**

- 현상: 키를 오름차순으로 계속 넣으면 어느 순간 `put`이 죽는다.
- 보이는 형태: `StackOverflowError`. README 실측으로 이 기계 기본 스택에서 정렬 입력 1만 200개는 되고 1만 300개에서 터진다. 그 전부터 `nodesCreated`가 수정 한 번에 n에 가깝게 오른다.
- 원인: 균형이 없어 정렬 입력은 한 줄로 늘어져 높이 = 원소 수다. 경로 복사는 되짚어 올라오며 노드를 만들어야 해서 재귀를 반복문으로 바꾸기도 어렵다.
- 대처: 키 순서를 섞어 넣거나, 실무처럼 균형을 잡는 구조로 바꾼다(해시 맵이면 HAMT, 정렬 맵이면 영속 레드블랙 트리). 입력이 정렬됐다면 중앙값부터 넣어 균형을 만든다. 테스트가 정렬 입력을 1000개로 제한한 이유다(메모리 쪽은 정답 6번 참고).

**2. 버전을 영원히 붙잡아 메모리가 회수되지 않음**

- 현상: 오래 돌수록 힙이 늘고 결국 `OutOfMemoryError`. 옛 버전은 아무도 안 보는데도 줄지 않는다.
- 보이는 형태: 힙 덤프에서 `versions` 목록이 뿌리 수천 개를 붙잡고 있고, 각 뿌리 아래의 "그 버전만 쓰는" 노드들이 전부 살아 있다. `versionCount()`가 단조 증가한다.
- 원인: `VersionedStore`는 `versions`에 한 번 넣으면 절대 빼지 않는다 — 과거 조회의 근거라서다. 누군가 뿌리를 가리키는 한 GC는 그 아래를 치우지 못한다(커리큘럼 ⚠ "옛 버전 참조 → 메모리 회수 불가").
- 대처: 보관 정책을 둔다 — 버전 수 상한, 오래된 버전 버리기, 또는 필요한 시점만 스냅샷으로 남기고 나머지는 명령 로그(`replay`)로 재생한다. 옛 뿌리 참조를 끊는 순간 그 버전만의 노드는 GC가 회수한다.

**3. 값만 비교하는 테스트가 "공유하는 척"하는 구현을 통과시킴**

- 현상: 모든 기능 테스트가 초록인데 메모리가 O(n)씩 는다.
- 보이는 형태: `put`이 안 지나간 부분트리까지 통째로 복사해도 답은 한 글자도 안 틀려 61개 중 56개를 통과한다(README). 갈리는 것은 `assertSame` 하나와 `countSharedNodes` 넷뿐이다.
- 원인: 공유는 "값이 같다"가 아니라 "같은 객체다"의 문제라 `assertEquals`로는 보이지 않는다.
- 대처: `nodesCreated`(수정 한 번에 만든 노드 수 = 높이 + 1)와 `countSharedNodes`(참조 동일성, `IdentityHashMap`)를 계약에 넣는다(정답 2번 참고).

**4. undo 뒤에 새로 쓰면 redo가 사라짐**

- 현상: 두 번 되돌리고 하나를 새로 쓴 뒤 `redo()`를 눌렀는데 아무 일도 안 일어난다.
- 보이는 형태: `redo()`가 `false`(또는 현재 버전 그대로)를 돌려준다. 되돌렸던 버전은 `versions`에 남아 있어 `snapshot(n)`으로는 여전히 읽힌다.
- 원인: 새 커밋은 `cursor` 뒤에 남아 있던 `history`를 잘라낸다 — 갈라진 두 미래를 한 줄의 되돌리기 길에 담을 수 없어서다. 편집기의 undo와 같은 규칙이다.
- 대처: 이것은 버그가 아니라 계약이다. 갈라진 미래가 필요하면 `history`를 한 줄이 아니라 트리로 만들거나, 버전 번호를 직접 들고 `snapshot(n)`으로 읽는다.

## 핵심 문장

- 영속 자료구조는 바꾸지 않고 새 버전을 만든다 — 버전마다 통째로 복사하는 대신 바뀐 길목만 새로 만들고 나머지는 옛 버전과 공유한다(경로 복사).
- 공유가 안전한 이유는 불변이기 때문이다: 불변이 먼저이고 공유는 그 결과다 — 순서를 뒤집으면 안 된다.
- 불변이 공짜로 주는 것은 리스트의 앞에 붙이기뿐이다. 뒤에 붙이기·뒤집기는 n개를 전부 새로 만들고, 트리는 수정 하나에 높이 + 1개를 만든다.
- 공유는 값으로 검증할 수 없다 — "같은 객체다"를 참조 동일성으로 세야 O(n) 메모리로 O(log n)인 척하는 구현이 걸러진다.
- 영속이 이기는 것은 버전이 필요할 때뿐이다: 아무도 안 볼 버전이면 상수 인자 11배가 손해이고, 시점 100개를 남기면 97배가 뒤집힌다. 그리고 옛 뿌리를 붙잡는 한 그 버전의 메모리는 돌아오지 않는다.

## 관련 주제·근거

- 선행 — [02-linked-list](../02-linked-list/2-summary.md) · [06-binary-search-tree](../06-binary-search-tree/2-summary.md): 가변 원형. `put`의 반환형이 "옛 값"에서 "새 자료구조"로 바뀌는 지점을 대조한다.
- 선행 — [16-red-black-tree](../16-red-black-tree/2-summary.md): 회전으로 균형을 잡는 방법. 불변 트리에서는 회전도 경로 위 노드를 새로 만들어 처리한다(Clojure `sorted-map`·Okasaki의 영속 레드블랙 트리) — 해시 맵은 HAMT로 균형 문제를 아예 피한다.
- 후속 — [27-merkle-tree](../27-merkle-tree/2-summary.md): 같은 불변성 위에서 "이게 그대로인가"에 답한다 — 참조 공유 대신 해시 요약.
- 연결 — [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md): 문제 1의 `replay`(명령 재생 + 시점 스냅샷)가 그 패턴의 축소판이다.
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `40-persistent` (선행 `09` · 원전 Driscoll 외 1989 · Okasaki 1998).
- myway 원본 — `/home/jun/project/myway/data-structure/26-persistent/` (README.md · impl/ConsList.java · impl/PersistentTreeMap.java · impl/VersionedStore.java · impl/PersistentProblems.java).

### 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/26-persistent/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/26-persistent/src/main/java/com/datastructure/persistent/`
- 테스트: `/home/jun/project/myway/data-structure/26-persistent/src/test/java/com/datastructure/persistent/`
- 정답 구현: `/home/jun/project/myway/data-structure/26-persistent/impl/`

### 용어 풀이

- **영속 자료구조(persistent data structure)**: 고칠 때마다 새 버전이 생기고, 옛 버전도 계속 읽을 수 있는 자료구조. "지우고 덮어쓰기"가 없다.
- **불변(immutable)**: 한 번 만들면 내용이 절대 안 바뀌는 것. 바꾸고 싶으면 새것을 만든다.
- **final**: 자바에서 "이 변수는 한 번 정해지면 다시 못 바꾼다"는 표시. 불변을 코드로 강제하는 장치.
- **구조 공유(structural sharing)**: 두 버전이 안 바뀐 부분을 복사하지 않고 같은 객체를 함께 가리키는 것.
- **경로 복사(path copying)**: 트리에서 바뀐 자리까지 내려가는 "길" 위의 노드만 새로 만들고, 옆가지는 그대로 공유하는 방법.
- **cons 셀**: "값 하나 + 나머지 목록 하나"로 된 리스트의 기본 조각. 셀들이 사슬처럼 이어져 리스트가 된다.
- **prepend**: 리스트 맨 앞에 원소 하나를 붙이는 연산.
- **head / tail**: 리스트의 맨 앞 원소(head)와, 그것을 뺀 나머지 전체(tail).
- **이진 탐색 트리(BST)**: 왼쪽에는 작은 키, 오른쪽에는 큰 키를 두는 트리. 키를 비교하며 내려가면 찾는 자리가 나온다.
- **노드(node)**: 트리나 리스트를 이루는 조각 하나. 값과 "다음/자식이 어디인지"를 담는다.
- **루트(root)**: 트리의 맨 위 노드. 모든 탐색이 여기서 시작한다.
- **서브트리**: 어떤 노드와 그 아래에 매달린 전체. 트리 안의 작은 트리.
- **중위 순회(inorder)**: BST를 "왼쪽 → 자기 → 오른쪽" 순서로 도는 것. 결과가 정렬된 순서로 나온다.
- **후계자(successor)**: 어떤 키 다음으로 큰 키. 트리에서 노드를 지울 때 그 자리를 메우는 데 쓴다.
- **스냅샷(snapshot)**: 어느 한 시점의 모습을 통째로 보관한 것. 사진 찍어두기.
- **undo / redo**: 한 단계 되돌리기 / 되돌린 것을 다시 앞으로 가기.
- **커서(cursor)**: "지금 어디를 보고 있는지"를 가리키는 위치 표시.
- **O(1) / O(log n) / O(n)**: 일의 양이 데이터 크기와 무관하게 일정 / 데이터가 2배 되어도 한 걸음만 늘어남 / 데이터 크기에 비례. n은 원소 개수.
- **O(높이)**: 트리의 위에서 아래까지 층수만큼 일한다는 뜻. 균형 잡힌 트리면 높이가 log n쯤이다.
- **재귀(recursion)**: 함수가 자기 자신을 다시 부르며 문제를 작은 조각으로 줄여 푸는 방식.
- **락(lock)**: 여러 작업이 동시에 데이터를 건드릴 때 "한 번에 하나만"을 강제하는 자물쇠. 불변 데이터는 안 바뀌니 읽을 때 락이 필요 없다.
- **GC(가비지 컬렉션)**: 아무도 안 가리키는 객체를 자바가 알아서 치우는 것. 누군가 가리키는 한 안 치운다.
- **`==` 비교 / IdentityHashMap**: 값이 같은지가 아니라 "같은 객체인지(같은 메모리인지)"를 따지는 비교. 공유를 셀 때 필요하다.
- **방어 복사(defensive copy)**: 내부 데이터를 밖에 내줄 때 남이 못 고치게 복사본을 주는 것. 불변이면 원본을 그냥 줘도 안전하다.
- **캐스팅(casting)**: 객체의 타입을 다른 타입으로 "간주"하는 것. 빈 맵 하나를 여러 타입으로 재사용할 때 쓴다.
- **static**: 객체마다가 아니라 클래스에 하나만 있는 것. EMPTY를 하나만 만들어 모두가 공유한다.
- **NoSuchElementException / IllegalArgumentException / IndexOutOfBoundsException**: "없는 걸 달라 했다 / 잘못된 값을 줬다 / 범위 밖 번호를 줬다"를 알리는 자바의 오류 신호.
- **amortized(분할상환)**: 가끔 비싼 연산이 있어도 여러 번 평균으로 나누면 싸다고 계산하는 방식.
