# data-structure/23-splay-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SortedTree (`src/main/java/com/datastructure/splay/SortedTree.java`)

- `V put(K key, V value)`
- `V get(K key)`
- `boolean containsKey(K key)`
- `V remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `List<K> keys()`
- `K firstKey()`
- `K lastKey()`
- `K floorKey(K key)`
- `K ceilingKey(K key)`
- `int height()`

> 16번과 **같은 계약**이다. 인터페이스만 보면 "조회가 쓰기인 구현"이 앉아 있어도 타입이 그 차이를 말해주지 않는다.

## 구현 — SplayTree (`src/main/java/com/datastructure/splay/SplayTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
평범한 이진 탐색 트리다. 색도 높이도 균형 정보도 없다 -- Node 는 key / value / left / right 뿐.
대신 규칙이 하나 있다 : 건드린 키(get / put / remove / floorKey / ceilingKey)는 뿌리로 올라온다

Node<K,V>                         SplayTree
+---------------+                 +-------------------------------------------+
| key           |                 | root      -- 방금 건드린 키가 여기 있다   |
| value         |                 | size                                      |
| left   ---+   |                 | rotations -- 태어난 뒤 누적 회전 수       |
| right  ---|-+ |                 +-------------------------------------------+
+-----------|-|-+                 depthOf(key) 만은 트리를 건드리지 않는다(재는 자)

0 1 2 3 4 5 6 을 순서대로 put 한 결과 -- 완전히 한 줄로 기운다

      (6)         put 은 새 키를 뿌리에 얹고 이전 뿌리를 자식으로 내린다.
      /           그래서 오름차순으로 넣으면 왼쪽으로 늘어선 한 줄이 된다.
    (5)           height = 7, 최악의 BST 와 똑같은 모양이다
    /
  (4)             이것도 "정상"이다. 스플레이 트리는 어느 한 순간의 모양을 보장하지 않는다.
  /               보장하는 것은 m 번의 연산을 다 더한 총 비용이 O(m log n) 이라는 것뿐
(3)               (한 번 한 번은 O(n) 이 될 수 있다 -- 상환(amortized) 보장)
/
(2)               자주 쓰는 키가 저절로 위로 모인다(지역성). 이게 이 자료구조를 쓰는 이유다
/
(1)
/
(0)  <- 여기를 get(0) 하면 아래 [전체 시퀀스] 처럼 트리 모양 자체가 바뀐다
```

### 동작 — splay

```
splay(h, key) 는 key 를 h 부분트리의 뿌리로 끌어올린다. 재귀로 내려갔다가 돌아 나오며 회전한다.
어느 케이스인지는 "지금 노드 h(할아버지) / h 의 자식(부모) / 그 아래(찾는 키)" 세 세대의
방향이 같은지 다른지로 갈린다. 표기는 A < h < B < x < C 처럼 알파벳순이 아니라 키 크기순이다

[1] zig -- 찾는 키가 h 의 자식일 때. 한 번만 돈다 (경로 길이가 홀수라 마지막에 한 칸 남는 경우)
    코드에서는 cmpLeft == 0 이라 zig-zig / zig-zag 어느 가지도 안 타고 곧장 return rotateRight(h)

    before                         after
        (30)                          (20)
        /   \          ->            /    \
      (20)  (35)                  (10)    (30)
      /  \                                /  \
   (10)  (25)                          (25)  (35)
    회전 1 회

[2] zig-zig -- 할아버지 - 부모 - 찾는 키가 "같은 방향"으로 두 칸 (왼-왼 또는 오른-오른)
    코드 :  h.left.left = splay(h.left.left, key);
            h = rotateRight(h);        <- (1) 할아버지를 먼저 돈다   * 여기가 핵심 *
            return rotateRight(h);     <- (2) 그다음 부모를 돈다

    before                (1) rotateRight(30)            (2) rotateRight(20) = after
        (30)                   (20)                          (10)
        /   \                  /    \                        /   \
     (20)   (35)            (10)    (30)                  (5)    (20)
     /  \                   /  \    /  \                         /   \
  (10)  (25)             (5)  (15)(25)(35)                    (15)   (30)
  /  \                                                               /  \
(5) (15)                                                          (25)  (35)
    회전 2 회. 30 이 두 칸 내려가고 그 아래에 있던 25, 35 가 한 칸씩 올라온다
    -> 지나온 경로가 접혀서 반으로 눌린다(path halving). 이것이 상환 O(log n) 의 원천이다

[3] zig-zag -- 할아버지 - 부모 - 찾는 키의 방향이 "엇갈릴 때" (왼-오른 또는 오른-왼)
    코드 :  h.left.right = splay(h.left.right, key);
            h.left = rotateLeft(h.left);   <- (1) 부모를 먼저 돈다  * [2] 와 반대 순서 *
            return rotateRight(h);         <- (2) 그다음 할아버지를

    before                (1) rotateLeft(10)             (2) rotateRight(30) = after
        (30)                   (30)                          (20)
        /   \                  /   \                        /    \
     (10)   (35)            (20)   (35)                  (10)    (30)
     /  \                   /  \                         /  \    /  \
   (5)  (20)             (10)  (25)                    (5) (15)(25)(35)
        /  \             /  \
     (15)  (25)        (5)  (15)                    회전 2 회. 결과는 좌우 균형이 잡힌다

  [2] 와 [3] 을 눈으로 가르는 법 : 조부모에서 목표까지 꺾이는 모양이
      같은 쪽으로 두 번  ( / 뒤 또 / )  -> zig-zig -> 할아버지부터 돈다
      한 번 꺾임         ( / 뒤 \    )  -> zig-zag -> 부모부터 돈다

[4] 전체 시퀀스 -- 깊은 노드 하나를 건드리면 지나온 경로 전체가 절반 깊이로 눌린다
    get(0) : 0 1 2 ... 6 을 순서대로 넣어 만든 한 줄짜리 트리에서 맨 아래를 꺼낸다
    (내려가는 길이 전부 왼쪽-왼쪽이므로 zig-zig 가 아래에서부터 3 번 이어 붙는다)

      before  height 7                  after  height 5
         (6)                                 (0)
         /                                      \
       (5)                                       (5)
       /                                        /   \
     (4)                     ->              (3)     (6)
     /                                       /  \
   (3)                                    (1)    (4)
   /                                         \
 (2)                                          (2)
 /
(1)                       회전 6 회 (깊이만큼). 깊이 변화 :
/                            키 0 : 6 -> 0     키 3 : 3 -> 2
(0)                          키 1 : 5 -> 3     키 4 : 2 -> 3
                             키 2 : 4 -> 4     키 6 : 0 -> 2
    한 번 비싸게(O(n)) 내려간 대가로 경로 위의 노드들이 대부분 절반 높이로 접힌다.
    그래서 같은 짓을 다시 해도 다시 비싸지지 않는다 -> 총합이 O(m log n) 으로 눌린다

splay 는 key 가 없어도 실패하지 않는다. 자식이 null 이면 그 자리에서 멈추므로,
끝나고 나면 key 의 이웃(직전 또는 직후 키)이 뿌리에 와 있다. get / put / remove 는 전부
"먼저 splay 하고, 뿌리의 키와 비교"로 시작한다
```

### 동작 — 추가

```
put(key, value) : splay 로 이웃을 뿌리에 올린 뒤, 새 노드를 그 위에 얹고 이전 뿌리를 자식으로 내린다

  1) root = splay(root, key)
  2) 뿌리 키가 같으면 값만 갈아끼우고 끝
  3) 다르면 새 노드 fresh 를 만들어 뿌리 자리를 뺏는다

  key < root.key 인 경우 (fresh 가 왼쪽 이웃을 밀어낸다)
     before                                after
        (root)                                (fresh)
        /    \                                /     \
      (L)    (R)          ->              (L)       (root)
                                                        \
      fresh.left  = root.left;   (L 전부가 key 보다 작다)  (R)
      fresh.right = root;
      root.left   = null;        <- 이 줄을 빠뜨리면 L 이 두 군데에 매달린다

  key > root.key 면 거울상 : fresh.right = root.right; fresh.left = root; root.right = null;

  왜 이게 맞나 : splay 뒤 뿌리는 key 의 바로 옆 키다. 그래서 뿌리의 한쪽 부분트리 전체가
  통째로 key 보다 작거나(또는 크거나) 하다 -- 쪼개 넣을 필요 없이 통째로 옮겨 달면 된다

remove(key) : splay 로 지울 노드를 뿌리로 올린 뒤, 남은 두 부분트리를 잇는다(join)
     root = splay(root, key)           키가 다르면 없는 키 -> null 반환
     left = root.left;  right = root.right;
     left == null 이면 root = right 로 끝
     아니면 left = splay(left, key)    left 안에는 key 보다 작은 키만 있으므로
                                       splay 는 계속 오른쪽으로만 내려간다
                                       -> left 의 최대 키가 뿌리로 오고, 그 노드의 right 는 null
     left.right = right;  root = left;

        (40)                    (30)                     (30)
        /   \      뿌리 제거     /  \  splay(left,40)     /   \
     (30)   (70)      ->      (20)  x      ->         (20)   (70)
     /                        + (70) 따로              right 자리가 비어 있으므로
  (20)                                                 그대로 (70) 을 끼운다

비용 : 모두 splay 한 번 = 그 순간엔 O(n) 까지, 연속 m 번이면 총 O(m log n) -> 상환 O(log n)
```

### `필드`

- `Node<K,V> root` 역할:
- `int size` 역할:
- `long rotations` 역할(측정용):
- `Node.key` / `Node.value` / `Node.left` / `Node.right` — 여분 데이터가 하나도 없다는 것의 뜻:

### `private Node<K,V> rotateRight(Node<K,V> h)` / `private Node<K,V> rotateLeft(Node<K,V> h)`

- 하는 일:
- 논리(16번의 회전과 달리 색을 옮길 필요가 없는 이유):
- 비용(왜):

### `private Node<K,V> splay(Node<K,V> h, K key)` (TODO)

- 하는 일:
- 논리(부모 포인터 없이 재귀로 **두 층씩** 내려가는 것 · zig / zig-zig / zig-zag · zig-zig 에서 무엇을 먼저 돌리는가):
- 비용(왜 — 상환 O(log n) 이 나오는 이유):

### `public V put(K key, V value)` (TODO)

- 하는 일:
- 논리(splay 를 부르고 새 노드를 뿌리 자리에 놓는 것):
- 비용(왜):

### `public V remove(K key)` (TODO)

- 하는 일:
- 논리(splay 를 **두 번** 부르는 이유 — 06번처럼 후속자를 옮겨 심지 않는 것):
- 비용(왜):

### `public K floorKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public V get(K key)`

- 하는 일:
- 논리(조회가 구조를 바꾼다는 것 · 그래서 읽기 잠금을 못 쓴다는 것):
- 비용(왜):

### `public K ceilingKey(K key)`

- 하는 일:
- 비용(왜):

### `public int depthOf(K key)` / `public long rotations()`

- 하는 일:
- 논리(무엇을 재려고 열어둔 것인가):
- 비용(왜):

### `public List<K> keys()`

- 하는 일:
- 비용(왜):

### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 논리(이것도 구조를 바꾸는가):
- 비용(왜):

### `public int height()` / `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 — SplayTreeMap (`src/main/java/com/datastructure/splay/SplayTreeMap.java`)

TODO 없는 어댑터. `SplayTree` 를 `SortedTree` 계약으로 내보낸다.

### `필드`

- `SplayTree<K,V> tree` 역할:

### `SortedTree 의 메서드 전부를 위임`

- 하는 일:
- 논리(16번 RedBlackTreeMap 과 같은 껍데기 — 같은 계약으로 나란히 재기 위한 것):

## 구현 — SplayTreeSet (`src/main/java/com/datastructure/splay/SplayTreeSet.java`)

### `필드`

- `static final Object PRESENT` 역할:
- `SplayTreeMap<K, Object> map` 역할:

### `public boolean add(K key)` (TODO)

- 하는 일:
- 논리(별도 조회 없이 판별하는 이유 — `contains` 로 먼저 확인하면 무엇이 두 배가 되는가):
- 비용(왜):

### `public boolean remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean contains(K key)` / `public List<K> toList()` / `public K first()` / `public K last()` / `public K floor(K key)` / `public K ceiling(K key)`

- 하는 일:
- 비용(왜):

### `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 — MoveToRootTree (`src/main/java/com/datastructure/splay/MoveToRootTree.java`)

> 잘못된 순서(부모 먼저)를 **일부러** 구현해 둔 비교용 클래스다.

### 동작 — 조회

```
SplayTree 와 코드가 딱 한 곳 다르다 -- zig-zig 가지에서 무엇을 먼저 도느냐

  SplayTree.splay      h.left.left = splay(h.left.left, key);
                       h = rotateRight(h);            <- 할아버지를 먼저
                       return rotateRight(h);            그다음 부모

  MoveToRootTree       h.left.left = moveToRoot(h.left.left, key);
                       h.left = rotateRight(h.left);  <- 부모를 먼저
                       return rotateRight(h);            그다음 할아버지
  (zig-zag 가지와 zig 는 두 클래스가 완전히 같다. 그래서 zig-zag 만 나오는 입력에서는 결과도 같다)

[1] 같은 입력에 zig-zig 한 번 -- 결과 트리가 갈린다
    before                     splay (할아버지 먼저)          move-to-root (부모 먼저)
        (30)                        (10)                          (10)
        /   \                       /   \                         /   \
     (20)   (35)                 (5)    (20)                    (5)   (30)
     /  \                               /   \                         /   \
  (10)  (25)          ->             (15)   (30)                   (20)   (35)
  /  \                                      /  \                   /  \
(5) (15)                                 (25)  (35)             (15)  (25)
    회전 2 회 (둘 다)          30 이 두 칸 내려간다          30 은 한 칸만 내려간다
                               = 경로가 접힌다               = 경로가 그대로 밀려 내려간다

[2] 그래서 긴 경로에서 차이가 벌어진다 -- spine(7) 에서 키 0 을 꺼낼 때
    (spine(n) 은 0..n-1 을 정렬 순서로 put 한 스플레이 트리와 같은 모양을 회전 없이 만든 것)

      before  height 7        splay 후  height 5            move-to-root 후  height 7
         (6)                       (0)                            (0)
         /                            \                              \
       (5)                             (5)                            (6)
       /                              /   \                           /
     (4)                           (3)     (6)                      (5)
     /              ->             /  \                              /
   (3)                          (1)    (4)                         (4)
   /                               \                                /
 (2)                                (2)                           (3)
 /                                                                 /
(1)                    회전 6 회                                 (2)
/                      경로가 절반으로 접힌다                     /
(0)                                                             (1)
                                                    회전 6 회 (같다!)
                                                    0 만 뿌리로 오고 나머지는 그대로 한 줄
                                                    = 다음번 깊은 접근도 여전히 비싸다

[3] 누적 비용 -- 한 줄짜리 트리에서 0, 1, 2, ... n-1 을 차례로 조회했을 때 총 회전 수

      n      splay      move-to-root
     ----   -------    -------------
      16         58              135
      32        138              527       n 이 2 배 될 때 splay 는 약 2 배,
      64        302            2,079       move-to-root 는 약 4 배로 는다
     128        638            8,255
     256      1,312           32,895       splay      = O(m log n)  -> 상환 O(log n)
                                           move-to-root = O(m n)    -> 상환 O(n) (보장 없음)

핵심 : "찾은 노드를 뿌리로 올린다"는 것만으로는 부족하다. 회전 순서를 zig-zig 로 잡아
       지나온 경로까지 같이 접어야(path halving) 비로소 상환 O(log n) 이 나온다.
       이 클래스는 그 순서를 일부러 틀리게 짜서 그 차이를 재기 위한 대조군이다
```

### `필드`

- `Node root` 역할:
- `long rotations` 역할:
- `Node.key` / `Node.left` / `Node.right` 역할:

### `public static MoveToRootTree spine(int n)`

- 하는 일:
- 논리(한 줄짜리 트리를 만들어 무엇을 재는가):
- 비용(왜):

### `private Node rotateRight(Node h)` / `private Node rotateLeft(Node h)`

- 하는 일:
- 비용(왜):

### `private Node moveToRoot(Node h, int key)` (TODO)

- 하는 일:
- 논리(`SplayTree.splay` 와 **한 곳만** 다른 것 — 그 한 곳이 무엇을 바꾸는가):
- 비용(왜):

### `public boolean get(int key)` / `public long rotations()` / `public int height()` / `public int depthOf(int key)`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 12번 스킵 리스트 (확률) | | | |
| 15번 B-트리 (위로 자라기) | | | |
| 16번 레드블랙 트리 (회전으로 보장) | | | |
| 23번 스플레이 트리 (상환 + 접근 지역성) | | | |
| MoveToRootTree (zig-zig 순서를 뒤집은 것) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/23-splay-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/23-splay-tree/src/main/java/com/datastructure/splay/`
- 테스트: `/home/jun/project/myway/data-structure/23-splay-tree/src/test/java/com/datastructure/splay/`
- 정답 구현: `/home/jun/project/myway/data-structure/23-splay-tree/impl/`
