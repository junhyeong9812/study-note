# data-structure/16-red-black-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SortedTree (`src/main/java/com/datastructure/redblack/SortedTree.java`)

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

## 구현 — RedBlackTree (`src/main/java/com/datastructure/redblack/RedBlackTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static final boolean RED / BLACK` 역할:
- `Node<K,V> root` 역할:
- `int size` 역할:
- `Node.key` / `Node.value` / `Node.left` / `Node.right` / `Node.color` 역할:
- 불변식 4개(뿌리는 검다 · 빨간 링크는 왼쪽에만 · 빨강 연속 금지 · 검은 높이가 같다):

### `static boolean isRed(Node<K,V> node)`

- 하는 일:
- 논리(null 을 검정으로 보는 이유):

### `private Node<K,V> rotateLeft(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(링크만이 아니라 색도 옮기는 이유):
- 비용(왜):

### `private Node<K,V> rotateRight(Node<K,V> h)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void flipColors(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(대입이 아니라 반전이어야 하는 이유 · 넣기/지우기에서 방향이 반대인 것):
- 비용(왜):

### `private Node<K,V> balance(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(세 검사의 순서가 계약인 이유 · `else if` 가 아닌 이유):
- 비용(왜):

### `private Node<K,V> put(Node<K,V> h, K key, V value, Object[] old)` (TODO)

- 하는 일:
- 논리(새 노드를 빨강으로 넣는 이유 · 반환값을 부모에 다시 대입하는 방식):
- 비용(왜):

### `private Node<K,V> moveRedLeft(Node<K,V> h)` (TODO)

- 하는 일:
- 논리(내려가기 전에 미리 빨강을 확보 — 15번 B-트리의 "미리 채우기"와의 대응):
- 비용(왜):

### `private Node<K,V> deleteMin(Node<K,V> h)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private Node<K,V> delete(Node<K,V> h, K key)` (TODO)

- 하는 일:
- 논리(key 비교를 두 번 하는 이유):
- 비용(왜):

### `public K floorKey(K key)` (TODO)

- 하는 일:
- 논리("찾으면 바로 반환"이 안 되는 이유):
- 비용(왜):

### `public V put(K key, V value)`

- 하는 일:
- 논리(마지막에 뿌리를 검게 강제하는 이유):
- 비용(왜):

### `public V get(K key)`

- 하는 일:
- 비용(왜):

### `public V remove(K key)`

- 하는 일:
- 논리(시작 전 뿌리를 빨갛게 만드는 줄의 뜻 — 지워도 테스트가 통과한다는 기록):
- 비용(왜):

### `public K ceilingKey(K key)`

- 하는 일:
- 비용(왜):

### `public List<K> keys()`

- 하는 일:
- 비용(왜):

### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 비용(왜):

### `public int height()`

- 하는 일:
- 비용(왜):

### `public int blackHeight()`

- 하는 일:
- 논리(왼쪽 한 줄만 세도 되는 이유):
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 — RedBlackTreeMap (`src/main/java/com/datastructure/redblack/RedBlackTreeMap.java`)

TODO 없는 어댑터. 일은 전부 `RedBlackTree` 에 있고 여기는 `SortedTree` 계약으로 넘기기만 한다.

### `필드`

- `RedBlackTree<K,V> tree` 역할:

### `SortedTree 의 메서드 전부를 위임`

- 하는 일:
- 논리(같은 계약으로 여러 트리를 나란히 재기 위한 껍데기라는 것):

## 구현 — RedBlackTreeSet (`src/main/java/com/datastructure/redblack/RedBlackTreeSet.java`)

### `필드`

- `static final Object PRESENT` 역할:
- `RedBlackTreeMap<K, Object> map` 역할:

### `public boolean add(K key)` (TODO)

- 하는 일:
- 논리(별도 조회 없이 "새로 들어갔는지"를 아는 방법):
- 비용(왜):

### `public boolean remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean contains(K key)`

- 하는 일:
- 비용(왜):

### `public List<K> toList()` / `public K first()` / `public K last()` / `public K floor(K key)` / `public K ceiling(K key)`

- 하는 일:
- 비용(왜):

### `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 12번 스킵 리스트 (확률) | | | |
| 15번 B-트리 (뚱뚱한 노드, 위로 자라기) | | | |
| 16번 좌편향 레드블랙 트리 (회전, 보장) | | | |
| 고전적 레드블랙 트리 (좌우 모두 허용 = 2-3-4) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/16-red-black-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/16-red-black-tree/src/main/java/com/datastructure/redblack/`
- 테스트: `/home/jun/project/myway/data-structure/16-red-black-tree/src/test/java/com/datastructure/redblack/`
- 정답 구현: `/home/jun/project/myway/data-structure/16-red-black-tree/impl/`
