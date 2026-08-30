# data-structure/06-binary-search-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — SortedMap (`src/main/java/com/datastructure/bst/SortedMap.java`)

- `V put(K key, V value)`
- `V get(K key)`
- `boolean containsKey(K key)`
- `V remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `K firstKey()`
- `K lastKey()`
- `K floorKey(K key)`
- `K ceilingKey(K key)`
- `Iterable<K> keys()`
- `Iterable<K> keysInRange(K from, K to)`
- 타입 파라미터: `SortedMap<K extends Comparable<K>, V>`

## 구현 — BinarySearchTree (`src/main/java/com/datastructure/bst/BinarySearchTree.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static class Node<K, V> { K key; V value; Node<K, V> left; Node<K, V> right; }` — 역할:
- `Node<K, V> root` — 역할:
- `int size` — 역할:

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `int height()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V> findNode(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K floorKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<K> keys()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterable<K> keysInRange(K from, K to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 문제 — BSTProblems (`src/main/java/com/datastructure/bst/BSTProblems.java`)

### 문제 1. 가장 가까운 키

> 문제 설명: `target` 과 차이가 가장 작은 키를 반환한다. 비었으면 `NoSuchElementException`.
> 양쪽 차이가 같으면 작은 쪽을 반환한다.
> `{1, 5, 9}, target=6` -> `5`
> `{1, 5, 9}, target=7` -> `5` (차이 2 대 2 이므로 작은 쪽)
> `{1, 5, 9}, target=0` -> `1`
> 함정 — 10만 개 × 10만 질의 시간 제한이 있다. 전부 훑어 최소 차이를 찾으면 O(n) 이다.
> 생각할 것 — 전부 훑어서 최소 차이를 찾으면 O(n) 이다. `floorKey` 와 `ceilingKey` 를 쓰면? /
> 둘 중 하나가 없는 경우를 잊지 마라.
> 시그니처: `static Integer closestKey(SortedMap<Integer, ?> map, int target)` — O(log n) 이어야 한다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 구간 합

> 문제 설명: `from` 이상 `to` 이하인 키들의 값을 더한다. 값은 정수다.
> `{1=10, 5=50, 9=90}, from=1, to=5` -> `60`
> 생각할 것 — `keysInRange` 를 쓰면 볼 필요 없는 가지를 건너뛴다. / 답이 k 개면 전체 비용이 얼마인가?
> 시그니처: `static long rangeSum(SortedMap<Integer, Integer> map, int from, int to)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. k 번째로 작은 키 (1부터 센다)

> 문제 설명: `{1, 5, 9}, k=2` -> `5`
> k 가 범위를 벗어나면 `IndexOutOfBoundsException`.
> 생각할 것 — 정렬 순회를 하다가 k 번째에서 멈추면 된다. 전부 다 순회할 필요가 있는가? /
> (참고: 노드마다 "내 아래에 몇 개 있는지"를 들고 있으면 O(log n) 이 된다.
> 그건 17번 펜윅 트리에서 다시 만난다. 여기서는 순회로 충분하다.)
> 시그니처: `static Integer kthSmallest(SortedMap<Integer, ?> map, int k)`

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

- 원본 README: `/home/jun/project/myway/data-structure/06-binary-search-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/06-binary-search-tree/src/main/java/com/datastructure/bst/`
- 테스트: `/home/jun/project/myway/data-structure/06-binary-search-tree/src/test/java/com/datastructure/bst/`
- 참고 구현: `/home/jun/project/myway/data-structure/06-binary-search-tree/impl/`
