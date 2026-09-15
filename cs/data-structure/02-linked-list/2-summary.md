# data-structure/02-linked-list — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**연결 리스트 = 기차.**\
배열이 "번호 붙은 좌석이 붙어 있는 극장"이라면, 연결 리스트는 칸끼리 연결고리로만 이어진 기차다.

- 극장(배열)에서는 "37번 좌석"으로 바로 간다.\
  기차에서는 5번째 칸에 가려면 1번 칸부터 4번 걸어야 한다.
- 대신 기차는 중간에 칸을 끼우거나 빼기가 쉽다.\
  연결고리 두 개만 풀었다 다시 걸면 끝 — 다른 칸은 아무도 안 움직인다.\
  극장에서는 중간에 좌석을 끼우려면 뒷사람 전부가 한 칸씩 밀려야 했다.
- 각 칸이 "다음 칸이 어디인지"만 아는 게 단일 연결(singly), "앞 칸과 다음 칸을 둘 다" 아는 게 이중 연결(doubly)이다.

```text
배열(극장):  [A][B][C][D]        <- 붙어 있어서 번호로 바로 감
기차(리스트): [A]-o-[B]-o-[C]    <- 연결고리(o)를 따라가야만 다음 칸
```

이 기차가 **똑같은 구조로** 연결 리스트다: 기차 칸 = 노드(Node), 연결고리 = next 참조, 기관차 위치 = head, 마지막 칸 = tail.\
Java의 `LinkedList`가 이렇게 동작한다.

> **참조(포인터)** — "그 물건이 어디 있는지"를 가리키는 화살표.\
> 예: 노드 안의 next 칸에는 다음 노드를 가리키는 화살표가 담긴다.

> **노드(node)** — 리스트의 한 칸.\
> 예: 값(item)과 다음 칸을 가리키는 화살표(next)를 함께 담은 작은 상자가 노드 하나다.

> **head / tail** — 첫 칸과 마지막 칸을 가리키는 표지.\
> 예: 이 둘만 알면 리스트 전체에 들어갈 수 있다 — head 에서 걸어 나가고, tail 뒤에 바로 붙인다.

## 문제 — 이 챕터가 시키는 것

01번 동적 배열과 **같은 일을 하는데 저장 방식이 정반대인** 리스트를 직접 만든다.\
같은 `List` 계약을 단일 연결과 이중 연결 **두 가지**로 구현해서, "참조 하나를 더 두는 것"이 무엇을 바꾸는지 비교하는 것이 이 챕터의 본체다.\
`tail` 을 들고 있는데 왜 `removeLast` 가 O(n) 인지에 답할 수 있으면 단일 연결 리스트를 이해한 것이다.

**과제**

- `ListContractTest.java` 를 따라친다 → `SinglyLinkedList` 의 **TODO 15개** → `DoublyLinkedList` 의 **TODO 2개**(나머지는 채워져 있다) → `ListIterationContractTest.java`(reverse·iterator) 따라치기 → `ListProblems` 의 **TODO 3개** 순서.\
  단일을 먼저 한다 — 링크가 하나뿐이라 단순하고, 그 뒤에 이중을 하면 차이가 선명해진다.
- 응용 문제 3개 — `removeAllIf`(조건에 맞는 원소를 모두 제거, O(n)) / `findMiddle`(가운데 값, `size()` 금지 + 한 번만 훑기) / `mergeSorted`(정렬된 두 리스트 병합, O(n+m)).\
  셋 다 인덱스를 한 번도 쓰지 않고 `Iterator` 로 푼다.
- 성능·계약 제약 — `removeAllIf` 에 **10만 건 시간 제한**이 걸려 있다(테스트 `mustBeLinear`, 5초).\
  01번에서는 `remove` 의 **시프트** 때문에 O(n²)이었고, 여기서는 **탐색** 때문이다 — 증상은 같은데 원인이 다르다.
- 계약 테스트가 **내부를 본다** — `head`, `tail` 과 `Node` 필드가 패키지 공개라 이 이름들이 계약의 일부다.\
  `DoublyLinkedListTest.assertSound` 는 앞으로 훑은 결과와 뒤로 훑은 결과가 서로의 역순인지 검사한다(이게 없으면 `prev` 를 아예 안 잇는 구현도 대부분 통과한다).\
  `SinglyLinkedListTest` 쪽은 `tail` 이 정말 마지막 노드를 가리키는지를 본다.
- `Iterator` 는 이 문제집에서 여기에만 있다.\
  `get(i)` 를 반복하면 전체가 O(n²)이 되므로, 여기서 `Iterator` 는 문법 설탕이 아니라 **복잡도를 바꾸는 장치**다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

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

그림 해설 (한 단계씩):

- [1] 맨 앞 추가: 새 칸의 연결고리를 먼저 옛 첫 칸에 걸고, 그다음 "여기가 첫 칸" 표지(head)를 새 칸으로 옮긴다.\
  아무도 안 움직이니 O(1).
- [2] 맨 뒤 추가: tail이 마지막 칸을 항상 기억하고 있어서 바로 뒤에 건다.\
  O(1). tail이 없었다면 마지막 칸을 찾으러 처음부터 걸어야 해서 O(n).
- [3] 중간 추가: 끼울 자리 "앞 칸"(pred)까지 걸어간 뒤(여기가 O(n)), 고리 두 개만 바꾼다(여기는 O(1)).\
  **순서가 생명** — 새 칸에 뒷길을 먼저 담지 않고 앞 칸 고리부터 바꾸면, 뒤쪽 전체로 가는 유일한 길이 끊긴다.

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

그림 해설 (한 단계씩):

- [1] 맨 앞 삭제: "첫 칸" 표지(head)를 둘째 칸으로 옮기면 끝.\
  O(1).\
  떼어낸 칸의 고리는 꼭 끊는다.

> **GC(가비지 컬렉터)** — 아무도 가리키지 않는 객체를 치우는 자동 청소부.\
> 예: 버린 노드의 next를 안 끊으면 그 노드가 뒤 칸들을 계속 붙잡아 청소가 안 된다.

- [2] 맨 뒤 삭제: tail이 어디인지는 알지만 **그 앞 칸**은 아무도 모른다.\
  앞 칸을 찾으러 처음부터 끝까지 걸어야 해서 O(n).\
  이 한 줄의 불편함이 이중 연결 리스트를 만든 이유다.

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

그림 해설 (한 단계씩):

- 값을 옮기는 게 아니라, 각 칸의 화살표 방향만 하나씩 반대로 돌린다.
- 한 칸에서 하는 일 세 가지: (1) 다음 갈 길을 먼저 메모해 두고(next) (2) 내 화살표를 뒤로 돌리고(cur.next = prev) (3) 한 칸 전진한다.
- (1)을 안 하면 화살표를 돌리는 순간 앞으로 갈 길이 사라진다 — 중간 삽입과 같은 교훈: "끊기 전에 갈 길부터 잡아라".
- 전체를 한 번 걷고 끝.\
  O(n), 새 칸을 만들지 않으니 추가 메모리 O(1).

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

> **불변식(invariant)** — 어떤 조작을 해도 항상 지켜져야 하는 약속.\
> 예: 여기서는 "양 끝은 항상 null로 닫힌다" — 조작이 끝날 때마다 이 약속이 참인지로 코드가 맞았는지 판정한다.

> **더미(sentinel) 노드** — 값 없이 자리만 지키는 가짜 노드.\
> 예: 이걸 양 끝에 두면 "빈 리스트" 같은 특수 경우 분기가 줄어드는데, 이 구현은 안 쓰기로 했다(그래서 head/tail null 분기가 코드에 남는다).

> **단일 연결(singly) / 이중 연결(doubly)** — 각 노드가 다음 칸만 아는가(next), 앞 칸도 아는가(prev+next)의 차이.\
> 예: 화살표 하나를 더 쓰는 대가로 removeLast 가 O(n)에서 O(1)로 떨어진다.

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

그림 해설 (한 단계씩):

- [1] 끝에 붙이기: 화살표가 양방향이므로 새 칸을 걸 때 **반대편 화살표(prev)도 같이** 채워야 한다.\
  그래도 만지는 건 끝 근처뿐이라 O(1).
- [2] 중간에 끼우기: 단일 연결은 고리 2개를 고쳤지만, 여기는 앞뒤 양방향이라 **4개**(pred.next, 새 노드의 prev/next, succ.prev)를 고친다.\
  대신 succ의 "앞 칸"을 succ.prev로 즉시 아니까, 단일 연결처럼 앞 칸을 찾으러 걸을 필요가 없다.
- [3] 인덱스 삽입 = 자리 찾기(node(index), O(n)) + 끼우기(O(1))의 조합.

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

그림 해설 (한 단계씩):

- 빼려는 칸(B)의 앞 칸과 뒤 칸을 서로 직접 잇는다.\
  B의 prev/next로 양쪽을 바로 아니까, 노드를 손에 쥐고 있으면 O(1).
- 떼어낸 B의 화살표(prev, next, item)는 전부 끊는다 — GC가 치울 수 있게.
- B가 맨 앞/맨 뒤 칸이었으면 이어줄 이웃이 없으니, 대신 head/tail 표지를 옮긴다(그래서 null 분기가 있다).

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

그림 해설 (한 단계씩):

- 찾는 번호가 앞쪽 절반이면 head에서 next로 걸어가고, 뒤쪽 절반이면 tail에서 prev로 거슬러 온다.
- 걷는 거리가 평균 절반이 될 뿐, 최악은 여전히 가운데까지 O(n) — "바로가기"는 끝내 없다.

> **`size >> 1`(오른쪽 시프트)** — 비트를 한 칸 밀어 2로 나눈 것.\
> 예: `size / 2`와 같다 — size 6이면 3, 7이면 3(소수점 버림).

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

> **predicate(조건 함수)** — 원소 하나를 받아 "지울까? 참/거짓"을 돌려주는 함수.\
> 예: `x -> x % 2 == 0` 을 넘기면 짝수만 지우라는 뜻이 된다.

> **반복자(Iterator)** — 지금 어디까지 읽었는지를 기억한 채 "다음 것 주세요(next)"만 반복하는 책갈피 객체.\
> 예: 인덱스로 매번 처음부터 세지 않아도 이어서 걸을 수 있어서 n번 순회가 O(n)으로 끝난다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 가운데 값 찾기

> 문제 설명: 원소가 짝수 개면 뒤쪽 것을 반환한다.
> `[1, 2, 3]` -> `2` / `[1, 2, 3, 4]` -> `3`
> 조건 — `size()` 를 쓰지 말고 리스트를 한 번만 훑어서 찾아라. 길이를 모르는 스트림에서도 통하는 기법이다.
> 생각할 것 — 한 칸씩 가는 것과 두 칸씩 가는 것을 동시에 움직이면? / 인덱스가 없으니 반복자를 두 개 쓰면 된다.
> 시그니처: `static <E> E findMiddle(List<E> list)` — 비어 있으면 `NoSuchElementException`.

> **토끼와 거북이(fast/slow, runner)** — 한 칸씩 가는 주자와 두 칸씩 가는 주자를 같이 출발시키는 기법.\
> 예: 빠른 쪽이 끝에 닿았을 때 느린 쪽이 정확히 가운데다 — 길이를 세지 않고 한 번의 순회로 가운데를 찾는다.

> **스트림(stream)** — 길이를 미리 알 수 없고 흘러오는 대로 한 번만 읽을 수 있는 데이터 흐름.\
> 예: 네트워크로 들어오는 로그처럼, 되감아 다시 읽을 수 없어서 `size()` 를 물어볼 수가 없다.

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

> **결합(coupling)** — 코드가 특정 구현의 이름을 직접 알아서 다른 구현으로 못 갈아타게 되는 것.\
> 예: 안에서 `new DoublyLinkedList<>()` 라고 쓰면 이 코드가 그 한 구현에 묶인다.

> **의존성 주입(dependency injection)** — 인터페이스(List)만 알게 하고 실제 구현은 호출자가 골라 넣어 주는 것.\
> 예: `result` 를 인자로 받으면, 호출자가 단일 연결을 넣든 이중 연결을 넣든 이 코드는 그대로 돈다.

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

## 용어 풀이

- **노드(node)**: 리스트의 한 칸.\
  값(item)과 다음 칸을 가리키는 화살표(next)를 함께 담은 작은 상자.
- **참조 / 포인터(reference/pointer)**: 물건 자체가 아니라 "물건이 어디 있는지"를 가리키는 화살표.\
  `null`은 "아무것도 안 가리킴".
- **head / tail**: 첫 칸과 마지막 칸을 가리키는 표지.\
  이 둘만 알면 리스트 전체에 들어갈 수 있다.
- **단일 연결(singly) / 이중 연결(doubly)**: 각 노드가 다음 칸만 아는가(next), 앞 칸도 아는가(prev+next)의 차이.\
  화살표 하나를 더 쓰는 대가로 "뒤로 걷기"와 O(1) 맨 뒤 삭제를 얻는다.
- **O(1), O(n)**: 데이터가 n개일 때 걸리는 시간의 대략적 표기.\
  O(1)은 개수와 무관하게 즉시, O(n)은 개수에 비례.
- **불변식(invariant)**: 어떤 조작 후에도 항상 참이어야 하는 약속(예: head.prev == null).\
  코드가 맞았는지의 판정 기준.
- **GC(가비지 컬렉터)**: 아무도 가리키지 않는 객체를 자동으로 치우는 청소부.\
  떼어낸 노드의 화살표를 끊어야 청소가 된다.
- **더미/센티널(sentinel) 노드**: 값 없이 자리만 지키는 가짜 노드.\
  양 끝에 두면 빈 리스트 같은 특수 분기가 줄어든다(이 구현은 안 씀).
- **반복자(Iterator)**: "다음 것 주세요"를 반복할 수 있는 책갈피 객체.\
  어디까지 읽었는지 스스로 기억한다.
- **predicate(조건 함수)**: 원소 하나를 받아 참/거짓을 돌려주는 함수.
- **토끼와 거북이(fast/slow 포인터)**: 한 칸/두 칸씩 가는 두 책갈피를 같이 움직여, 한 번의 순회로 가운데(또는 순환)를 찾는 기법.
- **스트림(stream)**: 길이를 모른 채 흘러오는 대로 한 번만 읽는 데이터 흐름.
- **인터페이스(interface) / 결합(coupling) / 의존성 주입(dependency injection)**: 인터페이스는 "무엇을 할 수 있나"의 약속 목록.\
  코드가 특정 구현 이름을 직접 알면 결합이 생기고, 구현을 호출자가 골라 넣게 하면(주입) 결합이 풀린다.
- **제네릭(`<E>`)**: 담을 값의 타입을 나중에 정하는 틀.\
  `List<E>`는 "E 타입을 담는 리스트".
- **시프트(shift)**: 배열에서 중간 삽입/삭제 때 뒤 원소들을 한 칸씩 밀거나 당기는 일.\
  연결 리스트에는 없다 — 대신 "걸어가기"가 비싸다.
