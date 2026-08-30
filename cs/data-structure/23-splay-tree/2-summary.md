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
