# data-structure/07-heap — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Heap (`src/main/java/com/datastructure/heap/Heap.java`)

- `void insert(E element)`
- `E peek()`
- `E poll()`
- `int size()`
- `boolean isEmpty()`
- `void clear()`

## 구현 — BinaryHeap (`src/main/java/com/datastructure/heap/BinaryHeap.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `private static final int DEFAULT_CAPACITY = 8` — 역할:
- `private final Comparator<? super E> comparator` — 역할:
- `Object[] elements` — 역할:
- `int size` — 역할:

### `BinaryHeap(Comparator<? super E> comparator)`

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

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `void siftUp(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void siftDown(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void insert(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E poll()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — MinHeap (`src/main/java/com/datastructure/heap/MinHeap.java`)

### `필드`

- (없음 — `BinaryHeap<E>` 를 상속만 한다) — 역할:

### `MinHeap()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — MaxHeap (`src/main/java/com/datastructure/heap/MaxHeap.java`)

### `필드`

- (없음 — `BinaryHeap<E>` 를 상속만 한다) — 역할:

### `MaxHeap()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SortedListHeap (`src/main/java/com/datastructure/heap/SortedListHeap.java`)

### `필드`

- `private static final int DEFAULT_CAPACITY = 8` — 역할:
- `private final Comparator<? super E> comparator` — 역할:
- `Object[] elements` — 역할:
- `int size` — 역할:
- `long moves` — 역할:

### `SortedListHeap(Comparator<? super E> comparator)`

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

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `void insert(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E poll()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| SortedListHeap | | | |
| BinaryHeap | | | |

## 구현 — KthLargest (`src/main/java/com/datastructure/heap/KthLargest.java`)

### `필드`

- `private final int k` — 역할:
- `private final Heap<Integer> heap` — 역할:

### `KthLargest(int k, Heap<Integer> heap)`

- 하는 일:
- 논리:
- 비용(왜):

### `int add(int value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — MedianFinder (`src/main/java/com/datastructure/heap/MedianFinder.java`)

### `필드`

- `private final Heap<Integer> lower` — 역할:
- `private final Heap<Integer> upper` — 역할:
- `private int count` — 역할:

### `MedianFinder(Heap<Integer> lower, Heap<Integer> upper)`

- 하는 일:
- 논리:
- 비용(왜):

### `void add(int value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `double median()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int count()`

- 하는 일:
- 논리:
- 비용(왜):

## 문제 — HeapProblems (`src/main/java/com/datastructure/heap/HeapProblems.java`)

### 문제 1. 힙 정렬

> 문제 설명: 배열을 오름차순으로 정렬한다. 원본 배열을 직접 고친다.
> 생각할 것 — 전부 힙에 넣었다가 하나씩 꺼내면 정렬된 순서로 나온다. 왜 그런가? /
> 복잡도는? 넣기 n 번과 빼기 n 번이 각각 O(log n) 이다. /
> (제자리 정렬로 만들 수도 있다. 배열 자체를 힙으로 보고 뒤에서부터 채우는 방법이다.
> 여기서는 힙을 써서 푸는 것으로 충분하다.)
> 시그니처: `static void heapSort(int[] values, Heap<Integer> heap)` — `heap` 은 비어 있는 상태로 들어온다.

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

- 원본 README: `/home/jun/project/myway/data-structure/07-heap/README.md`
- 구현: `/home/jun/project/myway/data-structure/07-heap/src/main/java/com/datastructure/heap/`
- 테스트: `/home/jun/project/myway/data-structure/07-heap/src/test/java/com/datastructure/heap/`
- 참고 구현: `/home/jun/project/myway/data-structure/07-heap/impl/`
