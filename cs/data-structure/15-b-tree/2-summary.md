# data-structure/15-b-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SearchTree (`src/main/java/com/datastructure/btree/SearchTree.java`)

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
- `int height()`

## 구현 — BTree (`src/main/java/com/datastructure/btree/BTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `int minDegree` (t) 역할:
- `Node<K,V> root` 역할:
- `int size` 역할:
- `Node.keys` / `Node.values` / `Node.children` 역할:

### `public BTree(int minDegree)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void splitChild(Node<K,V> parent, int i)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private V insertNonFull(Node<K,V> node, K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void removeFrom(Node<K,V> node, K key)` (TODO)

- 하는 일:
- 논리(네 경우):
- 비용(왜):

### `private int fill(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리(우선순위와 반환값의 뜻):
- 비용(왜):

### `private void mergeChildren(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public V put(K key, V value)`

- 하는 일:
- 논리(뿌리가 꽉 찼을 때):
- 비용(왜):

### `public V get(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `public V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `public List<K> keys()`

- 하는 일:
- 비용(왜):

### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 비용(왜):

### `public int height()`

- 하는 일:
- 논리(왜 왼쪽 한 줄만 세면 되는가):
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 — BPlusTree (`src/main/java/com/datastructure/btree/BPlusTree.java`)

### `필드`

- `int order` 역할:
- `Node<K,V> root` 역할:
- `int size` 역할:
- `Node.leaf` / `Node.keys` / `Node.values` / `Node.children` / `Node.next` 역할:
- `record`성 보조 `Split<K,V>{ K key; Node right; }` 역할:

### `public BPlusTree(int order)`

- 하는 일:
- 논리:
- 비용(왜):

### `static int lowerBound(Node<K,V> node, K key)` (주어짐)

- 하는 일:
- 논리:
- 비용(왜):

### `static int childIndex(Node<K,V> node, K key)` (TODO)

- 하는 일:
- 논리(lowerBound 와 부등호가 왜 달라야 하는가):
- 비용(왜):

### `private Split<K,V> splitLeaf(Node<K,V> node)` (TODO)

- 하는 일:
- 논리(올려보낼 키를 잎에 남기는가):
- 비용(왜):

### `private Split<K,V> splitInternal(Node<K,V> node)` (TODO)

- 하는 일:
- 논리(가운데 키를 올려보내고 지우는 이유):
- 비용(왜):

### `public List<K> keysInRange(K from, K to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void fix(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void merge(Node<K,V> node, int i)` (TODO)

- 하는 일:
- 논리(잎 병합과 내부 병합의 차이 · `next` 이어주기):
- 비용(왜):

### `public V put(K key, V value)`

- 하는 일:
- 논리:
- 비용(왜):

### `public V get(K key)`

- 하는 일:
- 논리(왜 늘 잎까지 내려가는가):
- 비용(왜):

### `public V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `public List<K> keys()`

- 하는 일:
- 논리(사슬 걷기):
- 비용(왜):

### `public K firstKey()` / `public K lastKey()`

- 하는 일:
- 비용(왜):

### `public int height()`

- 하는 일:
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BTree (값이 모든 노드에) | | | |
| BPlusTree (값은 잎에만 + 잎 사슬) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/15-b-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/15-b-tree/src/main/java/com/datastructure/btree/`
- 테스트: `/home/jun/project/myway/data-structure/15-b-tree/src/test/java/com/datastructure/btree/`
- 정답 구현: `/home/jun/project/myway/data-structure/15-b-tree/impl/`
