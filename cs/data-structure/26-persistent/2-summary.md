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
