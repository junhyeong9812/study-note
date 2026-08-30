# data-structure/02-linked-list — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — List (`src/main/java/com/datastructure/linkedlist/List.java`)

- `int size()`
- `boolean isEmpty()`
- `void add(E element)`
- `void add(int index, E element)`
- `E get(int index)`
- `E set(int index, E element)`
- `E remove(int index)`
- `boolean remove(Object o)`
- `int indexOf(Object o)`
- `boolean contains(Object o)`
- `void clear()`
- `Object[] toArray()`
- `void reverse()`
- `Iterator<E> iterator()` (extends `Iterable<E>`)

## 구현 — SinglyLinkedList (`src/main/java/com/datastructure/linkedlist/SinglyLinkedList.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `static class Node<E> { E item; Node<E> next; }` — 역할:
- `Node<E> head` — 역할:
- `Node<E> tail` — 역할:
- `private int size` — 역할:

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(Object o)`

- 하는 일:
- 논리:
- 비용(왜):

### `E getFirst()`

- 하는 일:
- 논리:
- 비용(왜):

### `E getLast()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `void addFirst(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void addLast(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void add(E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `private Node<E> node(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void add(int index, E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E get(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E set(int index, E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E remove(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(Object o)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E removeFirst()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E removeLast()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object o)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Object[] toArray()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void reverse()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterator<E> iterator()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — DoublyLinkedList (`src/main/java/com/datastructure/linkedlist/DoublyLinkedList.java`)

### `필드`

- `static class Node<E> { E item; Node<E> prev; Node<E> next; }` — 역할:
- `Node<E> head` — 역할:
- `Node<E> tail` — 역할:
- `private int size` — 역할:

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void addFirst(E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `void addLast(E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `void add(E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `E getFirst()`

- 하는 일:
- 논리:
- 비용(왜):

### `E getLast()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(Object o)`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `private void linkFirst(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void linkLast(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private void linkBefore(E element, Node<E> succ)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E unlink(Node<E> node)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `private Node<E> node(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void add(int index, E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E get(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E set(int index, E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E remove(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(Object o)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E removeFirst()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E removeLast()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object o)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Object[] toArray()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void reverse()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Iterator<E> iterator()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| SinglyLinkedList | | | |
| DoublyLinkedList | | | |

## 문제 — ListProblems (`src/main/java/com/datastructure/linkedlist/ListProblems.java`)

### 문제 1. 조건에 맞는 원소를 모두 제거 (이 문제집의 함정)

> 문제 설명: `predicate` 가 true 인 원소를 전부 없애고 제거한 개수를 반환한다.
> 함정 — `for (int i = size-1; i >= 0; i--) if (test(get(i))) remove(i)` 가 가장 먼저 떠오른다.
> 답은 맞다. 그런데 `get(i)` 도 `remove(i)` 도 매번 앞에서부터 세므로 각각 O(n) 이고,
> 그걸 n 번 부르면 O(n²) 이다. 테스트에 10만 건 시간 제한이 있다.
> 01번 배열에서는 `remove` 의 시프트 때문에 O(n²) 이었다. 여기서는 탐색 때문이다.
> 증상은 같은데 원인이 다르다.
> 생각할 것 — 인덱스를 안 쓰고 훑을 방법이 있는가? / 훑으면서 지우려면 반복자에 무엇이 있어야 하는가?
> 시그니처: `static <E> int removeAllIf(List<E> list, Predicate<? super E> predicate)` — O(n) 이어야 한다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 가운데 값 찾기

> 문제 설명: 원소가 짝수 개면 뒤쪽 것을 반환한다.
> `[1, 2, 3]` -> `2` / `[1, 2, 3, 4]` -> `3`
> 조건 — `size()` 를 쓰지 말고 리스트를 한 번만 훑어서 찾아라. 길이를 모르는 스트림에서도 통하는 기법이다.
> 생각할 것 — 한 칸씩 가는 것과 두 칸씩 가는 것을 동시에 움직이면? / 인덱스가 없으니 반복자를 두 개 쓰면 된다.
> 시그니처: `static <E> E findMiddle(List<E> list)` — 비어 있으면 `NoSuchElementException`.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 정렬된 두 리스트 병합

> 문제 설명: 오름차순 리스트 둘을 합쳐 `result` 에 오름차순으로 담는다. `a` 와 `b` 는 건드리지 않는다.
> `result` 는 비어 있는 상태로 들어온다.
> 결과를 담을 리스트를 인자로 받는 이유가 있다. 여기서 `new DoublyLinkedList<>()` 라고 쓰면
> 이 코드가 한 구현에 묶인다. 어떤 구현을 쓸지는 호출자가 정한다.
> 생각할 것 — 양쪽을 동시에 훑어야 한다. 반복자 두 개를 어떻게 나란히 움직이는가? /
> `Iterator` 는 "다음 값을 미리 보기"가 없다. 어떻게 우회하는가?
> 시그니처: `static void mergeSorted(List<Integer> a, List<Integer> b, List<Integer> result)` — O(n+m) 이어야 한다.

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

- 원본 README: `/home/jun/project/myway/data-structure/02-linked-list/README.md`
- 구현: `/home/jun/project/myway/data-structure/02-linked-list/src/main/java/com/datastructure/linkedlist/`
- 테스트: `/home/jun/project/myway/data-structure/02-linked-list/src/test/java/com/datastructure/linkedlist/`
- 참고 구현: `/home/jun/project/myway/data-structure/02-linked-list/impl/`
