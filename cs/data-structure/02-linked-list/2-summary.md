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

### 구조

```
SinglyLinkedList — 원소가 이웃해 있지 않다. "다음이 어디냐"는 next 참조에만 적혀 있다
+-------------------------------------------------+
| head ---+                                       |
| tail ---|-----------------------------------+   |
| size = 3|                                   |   |
+---------|-----------------------------------|---+
          v                                   v
      +---------+      +---------+      +---------+
      | item: A |      | item: B |      | item: C |
      | next   -+----> | next   -+----> | next    +----> null
      +---------+      +---------+      +---------+

배열의 elements[i] 처럼 인덱스로 바로 뛸 수가 없다.
node(index) 는 언제나 head 부터 index 번 걸어간다 -> 인덱스 접근 O(n)
대신 노드를 이미 손에 쥐고 있으면 삽입/삭제는 링크만 고치면 되므로 O(1)
tail 을 들고 있어 addLast 는 O(1). 그런데 tail 의 "앞" 노드는 아무도 모른다
```

### 동작 — 추가

```
[1] addFirst(X) : 새 노드가 옛 head 를 가리키게 하고 head 를 옮긴다. O(1)
    before  head -> +---+      +---+
                    | A +----> | B +----> null
                    +---+      +---+

    after   head -> +---+      +---+      +---+
                    | X +----> | A +----> | B +----> null
                    +---+      +---+      +---+
    head = new Node(X, head);        <- 옛 head 를 새 노드의 next 에 먼저 담고 head 를 갱신
    if (tail == null) tail = head;   <- 비어 있었을 때만

[2] addLast(Y) : tail 뒤에 붙이고 tail 을 옮긴다. O(1)
    before          +---+      +---+                    after   ... +---+      +---+
                    | A +----> | B +----> null                      | B +----> | Y +----> null
                    +---+      +---+                                +---+      +---+
                                 ^ tail                                          ^ tail
    tail.next = node;  tail = node;
    tail 필드가 없다면 마지막 노드를 찾으러 head 부터 걸어야 해서 O(n) 이 된다

[3] add(index, E) : index-1 노드(pred)를 찾아 그 뒤에 끼운다. 찾기 O(n) + 끼우기 O(1)
    add(1, X)
    before  +---+      +---+      +---+
            | A +----> | B +----> | C +----> null
            +---+      +---+      +---+
            pred = node(0)

    after   +---+      +---+      +---+      +---+
            | A +----> | X +----> | B +----> | C +----> null
            +---+      +---+      +---+      +---+
    (1) X.next = pred.next    <- B 로 가는 길을 먼저 새 노드에 옮겨 담는다
    (2) pred.next = X
    순서를 뒤집으면 B 로 가는 유일한 길이 끊겨 B, C 가 통째로 사라진다
```

### 동작 — 삭제

```
[1] removeFirst() : head 를 한 칸 옮기고, 떼어낸 노드의 참조를 끊는다. O(1)
    before  head -> +---+      +---+      +---+
                    | A +----> | B +----> | C +----> null
                    +---+      +---+      +---+

    after           +---+      +---+      +---+
                    | A |      | B +----> | C +----> null
                    +---+      +---+      +---+
                    버림         ^ head
    head = removed.next;  removed.next = null;  removed.item = null;
    next 를 안 끊으면 버린 노드가 B 를 붙잡고 있어 GC 가 사슬 전체를 못 치운다

[2] removeLast() : tail 을 알아도 그 "앞" 노드를 모른다 -> head 부터 다시 센다. O(n)
    before  +---+      +---+      +---+
            | A +----> | B +----> | C +----> null
            +---+      +---+      +---+
              ^          ^          ^ tail
              pred 시작   ...
            while (pred.next != tail) pred = pred.next;      <- 여기가 O(n)

    after   +---+      +---+
            | A +----> | B +----> null
            +---+      +---+
                         ^ tail
    tail.item = null;  pred.next = null;  tail = pred;

단방향의 대가는 이 한 줄이다: 뒤로 갈 길이 없다.
이 하나 때문에 노드마다 참조를 하나 더 두는 이중 연결이 나온다
```

### 동작 — 뒤집기

```
reverse() : 값을 옮기지 않고 next 가 가리키는 방향만 반대로 돌린다. O(n), 추가 메모리 O(1)
    prev = null   cur = head
       |            |
       v            v
     null         +---+      +---+      +---+
                  | A +----> | B +----> | C +----> null
                  +---+      +---+      +---+

    한 걸음:  next = cur.next    <- 끊기 전에 갈 길을 먼저 잡아둔다
              cur.next = prev    <- 이 순간 원래 다음 노드로 가는 길이 사라진다
              prev = cur;  cur = next

    after   head -> +---+      +---+      +---+
                    | C +----> | B +----> | A +----> null
                    +---+      +---+      +---+
                                            ^ tail (= 옛 head, 미리 잡아둔 oldHead)
```

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

### 구조

```
DoublyLinkedList — 노드마다 prev 와 next 를 둘 다 가진다. 더미(sentinel) 노드는 쓰지 않는다
+---------------------------------------------------+
| head ---+                                         |
| tail ---|-------------------------------------+   |
| size = 3|                                     |   |
+---------|-------------------------------------|---+
          v                                     v
      +-------+         +-------+         +-------+
null <-+ prev  |<--------+ prev  |<--------+ prev  |
      | item A|         | item B|         | item C|
      | next  +-------->| next  +-------->| next  +--> null
      +-------+         +-------+         +-------+

불변식: head.prev == null, tail.next == null (양 끝은 항상 null 로 닫힌다)
빈 리스트 = head == tail == null

노드 하나당 참조를 하나 더 쓰는 대가로 얻는 것:
    (1) 노드를 손에 쥐면 그 "앞"을 즉시 알 수 있다 -> removeLast 가 O(n) -> O(1)
    (2) tail 에서 거슬러 올라올 수 있다 -> node(index) 의 평균 이동 거리가 절반
```

### 동작 — 추가

```
[1] linkLast(Y) : 끝에 붙이면서 반대편 참조도 같이 채운다. O(1)
    before   ... +-------+ <- tail        after   ... +-------+         +-------+ <- tail
                 | item C|                            | item C+-------->| item Y|
                 +-------+                            +-------+<--------+-------+
    (1) oldTail = tail
    (2) node = new Node(oldTail, Y, null)          <- 새 노드의 prev 는 생성자에서 끝난다
    (3) tail = node
    (4) oldTail == null ? head = node : oldTail.next = node    <- 비어 있었을 때만 head 를 세운다
    linkFirst 는 완전 대칭 (prev 를 null 로, next 를 옛 head 로)

[2] linkBefore(X, succ) : succ 앞에 끼운다 — 고칠 참조가 4개다
    linkBefore(X, B)
    before   +-------+         +-------+
             | item A+-------->| item B|
             +-------+<--------+-------+
              pred              succ

    after    +-------+     +-------+     +-------+
             | item A+---->| item X+---->| item B|
             +-------+<----+-------+<----+-------+
              pred          새 노드        succ
    (1) pred = succ.prev              <- 단일 연결은 이걸 찾으러 head 부터 걸어야 했다
    (2) node = new Node(pred, X, succ)    <- 새 노드의 양쪽 링크는 여기서 끝
    (3) succ.prev = node
    (4) pred == null ? head = node : pred.next = node    <- succ 가 head 였으면 head 갱신

[3] add(index, E) = index == size 면 linkLast, 아니면 linkBefore(E, node(index))
```

### 동작 — 삭제

```
unlink(node) : 앞뒤를 서로 직접 잇고, 떼어낸 노드의 참조를 끊는다. 노드를 알면 O(1)
    unlink(B)
    before   +-------+     +-------+     +-------+
             | item A+---->| item B+---->| item C|
             +-------+<----+-------+<----+-------+
              pred          node          succ

    after    +-------+                 +-------+
             | item A+---------------->| item C|
             +-------+<----------------+-------+
                          ( B 는 양쪽 다 끊긴 채 버려진다 )

    pred == null ? head = succ : (pred.next = succ, node.prev = null)
    succ == null ? tail = pred : (succ.prev = pred, node.next = null)
    node.item = null;  size--;
    끝 노드였던 쪽은 원래 null 이었으므로 끊을 것이 없다 -> 그래서 else 분기에만 null 대입이 있다

removeFirst() = unlink(head),  removeLast() = unlink(tail)
    단일 연결에서 tail 의 앞 노드를 찾던 while 루프가 통째로 사라진다 -> O(1)
```

### 동작 — 인덱스 접근

```
node(int index) : 절반을 넘어가면 tail 쪽에서 거슬러 온다. 최악은 여전히 O(n), 평균 이동은 절반
        idx     0     1     2     3     4     5
                A     B     C     D     E     F      size = 6
                >>>>>>>>>>>>>>>|<<<<<<<<<<<<<<<
                head 에서 next  |  tail 에서 prev
                                ^ size >> 1 = 3

    index < (size >> 1) : head 에서 next 로 index 번
    그 밖              : tail 에서 prev 로 (size - 1 - index) 번

    배열은 elements[index] 한 번 읽기로 끝나는 일이다.
    연결 리스트가 인덱스를 싫어하는 이유가 이 그림 전체다
```

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
