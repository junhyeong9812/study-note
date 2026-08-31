# data-structure/04-queue-deque — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Queue (`src/main/java/com/datastructure/queue/Queue.java`)

- `void enqueue(E element)`
- `E dequeue()`
- `E peek()`
- `int size()`
- `boolean isEmpty()`
- `void clear()`

## 계약 — Deque (`src/main/java/com/datastructure/queue/Deque.java`)

- `void addFirst(E element)`
- `void addLast(E element)`
- `E removeFirst()`
- `E removeLast()`
- `E peekFirst()`
- `E peekLast()`
- (extends `Queue<E>` — `enqueue` = `addLast`, `dequeue` = `removeFirst`, `peek` = `peekFirst`)

## 구현 — ArrayQueue (`src/main/java/com/datastructure/queue/ArrayQueue.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
ArrayQueue — 되감지 않는 나이브 버전. head 는 오른쪽으로만 간다
+-------------------------------------------------+
| head = 2     (첫 원소의 인덱스)                   |
| size = 3     (담긴 개수)                          |
| elements ---+                                   |
+-------------|-----------------------------------+
              v
    idx    0     1     2     3     4     5     6     7
        +-----+-----+-----+-----+-----+-----+-----+-----+
        |null |null |  C  |  D  |  E  |     |     |     |
        +-----+-----+-----+-----+-----+-----+-----+-----+
        |<- 버려진 칸 ->|<--- size = 3 --->|<- 앞으로 쓸 칸 ->|
                    ^ head            ^ 다음에 쓸 칸 = head + size

    논리 i번째 원소 = elements[head + i]     (모듈러 없음, 절대 인덱스)
    tail 인덱스 필드는 없다 — 뒤쪽 경계는 head + size 로 계산한다

FIFO — 한쪽 끝(head)에서 빼고 반대쪽 끝(head+size)에서 넣는다.
스택과 달리 양 끝을 다 써야 해서 "끝 하나만 보면 된다"가 성립하지 않는다
```

### 동작 — 추가

```
enqueue(F) : 뒤쪽 빈 칸에 쓰기만 한다. O(1)
        +-----+-----+-----+-----+-----+-----+        +-----+-----+-----+-----+-----+-----+
        |null |null |  C  |  D  |  E  |     |   ->   |null |null |  C  |  D  |  E  |  F  |
        +-----+-----+-----+-----+-----+-----+        +-----+-----+-----+-----+-----+-----+
                    ^head=2, size=3                              ^head=2, size=4
    ensureCapacity(head + size + 1);      <- 필요한 자리는 0..head+size 다 (head 왼쪽까지 포함)
    elements[head + size] = F;  size++;
```

### 동작 — 삭제

```
[1] dequeue() : 앞 칸을 비우고 head 를 오른쪽으로 한 칸. 원소를 당기지 않으므로 O(1)
    before  idx  0     1     2     3     4
                +-----+-----+-----+-----+-----+
                |null |  C  |  D  |  E  |     |    head = 1, size = 3
                +-----+-----+-----+-----+-----+
                        ^ head

    after       +-----+-----+-----+-----+-----+
                |null |null |  D  |  E  |     |    head = 2, size = 2
                +-----+-----+-----+-----+-----+
                              ^ head
    value = elements[head];  elements[head] = null;  head++;  size--;

    만약 "앞당김"으로 구현했다면 (head 를 늘 0 으로 유지)
                +-----+-----+-----+-----+-----+
                |  C  |  D  |  E  |     |     |
                +-----+-----+-----+-----+-----+
                   /     /     /
                +-----+-----+-----+-----+-----+
                |  D  |  E  |null |     |     |   D, E 를 전부 한 칸씩 당김
                +-----+-----+-----+-----+-----+
    -> dequeue 마다 O(n). head 를 두는 것은 이 시프트를 없애려는 선택이다

[2] 그 대신 치르는 대가 — head 왼쪽 칸은 영영 못 쓴다
    enqueue / dequeue 를 번갈아 반복하면 size 는 그대로인데 head 만 계속 오른쪽으로 간다
        +-----+-----+-----+ ... +-----+-----+
        |null |null |null | ... |null |     |    원소 0개인데 배열 2048칸
        +-----+-----+-----+ ... +-----+-----+
                                    ^ head = 2047
    ensureCapacity(head + size + 1) 이 계속 걸려 배열만 2배씩 커진다.
    앞쪽 빈 칸을 다시 쓰려면? 끝에 닿았을 때 앞으로 되감으면 된다 -> CircularQueue
```

### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `Object[] elements` — 역할:
- `int head` — 역할:
- `private int size` — 역할:

### `ArrayQueue()`

- 하는 일:
- 논리:
- 비용(왜):

### `ArrayQueue(int initialCapacity)`

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

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `private void ensureCapacity(int minCapacity)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void enqueue(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E dequeue()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — CircularQueue (`src/main/java/com/datastructure/queue/CircularQueue.java`)

### 구조

```
CircularQueue — 배열의 끝과 처음을 이어 원처럼 쓴다. 필드는 ArrayQueue 와 똑같다
+-------------------------------------------------+
| head = 3     (첫 원소의 인덱스)                   |
| size = 3                                        |
| elements ---+   (capacity = 5)                  |
+-------------|-----------------------------------+
              v
    idx    0     1     2     3     4
        +-----+-----+-----+-----+-----+
        |  E  |     |     |  C  |  D  |
        +-----+-----+-----+-----+-----+
           ^                 ^ head
           논리 3번째 (감겨서 0번 칸으로 넘어왔다)

    감김을 펴서 보면 (같은 배열을 두 번 이어 붙인 그림)
    idx    0     1     2     3     4  |  0     1     2     3     4
        +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
        |  E  |     |     |  C  |  D  |  E  |     |     |  C  |  D  |
        +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
                                ^head  |<-- size=3 -->|
                                       ^ 여기서 % 로 0번 칸에 되감긴다

    논리 i번째 = elements[indexOf(i)],   indexOf(i) = (head + i) % elements.length
        i :   0        1        2
            C(3)     D(4)     E(0)          <- 괄호 안이 실제 배열 인덱스

tail 인덱스 필드를 두지 않는 이유
    head == tail 이 "꽉 참"인지 "빔"인지 구분되지 않는다. 그래서 size 를 쓴다
        빔     = (size == 0)
        꽉 참  = (size == elements.length)
    한 칸을 늘 비워두는 기법도 쓰지 않는다 — size 하나로 모호함이 사라지기 때문
```

### 동작 — 추가

```
enqueue(F) : "다음에 쓸 칸"을 필드로 들고 있지 않고 그때그때 계산해 쓴다. O(1)
    ensureCapacity(size + 1);         <- 배열 길이가 바뀔 수 있으므로 indexOf 보다 반드시 먼저
    elements[indexOf(size)] = F;  size++;

    head=3, size=3, capacity=5 -> 쓸 칸 = (3 + 3) % 5 = 1
    before  +-----+-----+-----+-----+-----+        after  +-----+-----+-----+-----+-----+
            |  E  |     |     |  C  |  D  |   ->          |  E  |  F  |     |  C  |  D  |
            +-----+-----+-----+-----+-----+               +-----+-----+-----+-----+-----+
                     ^ 여기                                        ^ size = 4
    ArrayQueue 라면 head+size = 6 -> 배열 밖이라 확장이 걸렸을 자리다
```

### 동작 — 삭제

```
dequeue() : 앞 칸을 비우고 head 를 되감아 한 칸 옮긴다. O(1)
    head = (head + 1) % elements.length;      <- 끝(4)에 닿으면 0 으로 돌아온다

    before  +-----+-----+-----+-----+-----+        after  +-----+-----+-----+-----+-----+
            |  E  |  F  |     |     |  D  |   ->          |  E  |  F  |     |     |null |
            +-----+-----+-----+-----+-----+               +-----+-----+-----+-----+-----+
                                    ^head=4               ^head=0   ( 4 -> 0 으로 되감김 )
    value = elements[head];  elements[head] = null;  head = (head+1) % len;  size--;
    ArrayQueue 의 head++ 가 여기서는 % 한 번 붙은 것뿐인데, 앞쪽 빈 칸이 되살아난다
```

### 동작 — 확장

```
꽉 참 -> 2배 확장. 여기서는 Arrays.copyOf 로 통복사하면 안 된다
    감긴 상태  capacity = 5, head = 3, size = 5
        idx    0     1     2     3     4
            +-----+-----+-----+-----+-----+
            |  E  |  F  |  G  |  C  |  D  |     실제 배열 순서 != 논리 순서
            +-----+-----+-----+-----+-----+     논리 순서는 C D E F G
                                 ^ head

    통복사하면        E F G C D _ _ _ _ _        <- 순서가 깨진다 (head 만 그대로 두면 더 엉킨다)

    indexOf 로 논리 순서대로 옮긴다
        for (i = 0; i < size; i++) moved[i] = elements[indexOf(i)];
        +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
        |  C  |  D  |  E  |  F  |  G  |     |     |     |     |     |   capacity = 10
        +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
        ^ head = 0        <- 감김을 풀어 0 부터 펴 놓는다

clear() 도 같은 이유로 indexOf(i) 를 따라 논리 순서로 지운 뒤 head = 0 으로 되돌린다
```

### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `Object[] elements` — 역할:
- `int head` — 역할:
- `private int size` — 역할:

### `CircularQueue()`

- 하는 일:
- 논리:
- 비용(왜):

### `CircularQueue(int initialCapacity)`

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

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `private void ensureCapacity(int minCapacity)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void enqueue(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E dequeue()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — ArrayDeque (`src/main/java/com/datastructure/queue/ArrayDeque.java`)

### 구조

```
ArrayDeque — CircularQueue 와 같은 (head + size) % length 구조에 "앞쪽 끝" 연산을 더한 것
    필드(elements, head, size)도 ensureCapacity 도 CircularQueue 와 동일하다.
    Queue 쪽 메서드는 위임한다:  enqueue = addLast,  dequeue = removeFirst,  peek = peekFirst

    idx    0     1     2     3     4
        +-----+-----+-----+-----+-----+
        |     |  C  |  D  |  E  |     |     head = 1, size = 3, capacity = 5
        +-----+-----+-----+-----+-----+
                 ^ head           ^ 뒤쪽 끝 = indexOf(size-1) = (1+2) % 5 = 3
        <---- addFirst / removeFirst      addLast / removeLast ---->
              (head 를 왼쪽으로 되감음)      (head 는 그대로, size 만 변함)

큐가 "한쪽에서 넣고 반대쪽에서 뺀다" 였다면, 덱은 양쪽 끝에서 다 넣고 뺀다.
그래서 되감기가 오른쪽뿐 아니라 왼쪽으로도 필요해진다
```

### 동작 — 앞쪽 끝

```
[1] addFirst(B) : head 를 왼쪽으로 되감고 그 칸에 쓴다. O(1)
    head = (head - 1 + elements.length) % elements.length;   <- 그냥 (head-1) 이면 -1 이 된다
    elements[head] = B;  size++;

    head = 0 인 경우가 되감기의 핵심이다
    before  +-----+-----+-----+-----+-----+        after  +-----+-----+-----+-----+-----+
            |  C  |  D  |     |     |     |   ->          |  C  |  D  |     |     |  B  |
            +-----+-----+-----+-----+-----+               +-----+-----+-----+-----+-----+
            ^ head = 0, size = 2                                                  ^ head = 4
                                     (0 - 1 + 5) % 5 = 4  — 배열 끝으로 넘어간다
    논리 순서는 B C D. 배열에서는 B 가 맨 뒤 칸에 있지만 indexOf(0) = 4 이므로 첫 원소다

    순서 주의: ensureCapacity 가 head 를 0 으로 바꿔놓을 수 있으므로
              되감기 계산은 반드시 ensureCapacity 뒤에 한다

[2] removeFirst() : elements[head] 를 비우고 head = (head + 1) % len. CircularQueue.dequeue 와 같다
```

### 동작 — 뒤쪽 끝

```
[3] addLast(F) : elements[indexOf(size)] = F. CircularQueue.enqueue 와 같다

[4] removeLast() : head 는 움직이지 않는다. 뒤쪽 끝 칸만 비우고 size 를 줄인다. O(1)
    int last = indexOf(size - 1);     head = 0, size = 3 -> last = (0 + 2) % 5 = 2
    before  +-----+-----+-----+-----+-----+        after  +-----+-----+-----+-----+-----+
            |  C  |  D  |  E  |     |     |   ->          |  C  |  D  |null |     |     |
            +-----+-----+-----+-----+-----+               +-----+-----+-----+-----+-----+
            ^head          ^ last                         ^head    ^ size = 2
    elements[last] = null;  size--;

정리
    앞에서 빼면 head 가 움직인다. 뒤에서 빼면 size 만 줄어든다.
    배열 하나로 양 끝을 모두 O(1) 로 만든 대가 = 접근할 때마다 붙는 % 연산과 되감기 분기
```

### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `Object[] elements` — 역할:
- `int head` — 역할:
- `private int size` — 역할:

### `ArrayDeque()`

- 하는 일:
- 논리:
- 비용(왜):

### `ArrayDeque(int initialCapacity)`

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

### `void enqueue(E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `E dequeue()`

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()`

- 하는 일:
- 논리:
- 비용(왜):

### `E peekFirst()`

- 하는 일:
- 논리:
- 비용(왜):

### `E peekLast()`

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

### `E removeFirst()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E removeLast()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinkedDeque (`src/main/java/com/datastructure/queue/LinkedDeque.java`)

### 구조

```
LinkedDeque — 용량도 되감기도 % 연산도 없다. 양 끝 노드를 직접 들고 있다
+---------------------------------------------------+
| first ---+                                        |
| last ----|-------------------------------------+  |
| size = 3 |                                     |  |
+----------|-------------------------------------|--+
           v                                     v
      +-------+         +-------+         +-------+
null <-+ prev  |<--------+ prev  |<--------+ prev  |
      | item C|         | item D|         | item E|
      | next  +-------->| next  +-------->| next  +--> null
      +-------+         +-------+         +-------+

필드 이름이 02 장과 다르다: 여기는 first / last (DoublyLinkedList 는 head / tail).
더미 노드는 없다 — 비면 first == last == null
Queue 쪽은 위임한다: enqueue = addLast, dequeue = removeFirst, peek = peekFirst
```

### 동작 — 추가

```
addFirst(B) : 새 노드를 앞에 매달고 옛 first 의 prev 를 채운다. O(1)
    oldFirst = first;
    node = new Node(null, B, oldFirst);        <- prev 는 null, next 는 옛 first
    first = node;
    oldFirst == null ? last = node : oldFirst.prev = node;   <- 비어 있었으면 last 도 세운다

    before  first -> +-------+         +-------+ <- last
                     | item C|<------->| item D|
                     +-------+         +-------+

    after   first -> +-------+         +-------+         +-------+ <- last
                     | item B|<------->| item C|<------->| item D|
                     +-------+         +-------+         +-------+

addLast(Y) 는 완전 대칭 (new Node(oldLast, Y, null), last 갱신, oldLast.next = node)
배열판이 % 로 풀던 "양 끝" 문제를 여기서는 참조 갈아끼우기로 푼다
```

### 동작 — 삭제

```
removeLast() : last 를 한 칸 앞으로 당기고, 떼어낸 노드의 prev 만 끊는다. O(1)
    removed = last;
    value = removed.item;
    last = removed.prev;
    last == null ? first = null : last.next = null;
    removed.item = null;  removed.prev = null;      <- next 는 이미 null 이었다

    before  +-------+         +-------+         +-------+ <- last
            | item B|<------->| item C|<------->| item D|
            +-------+         +-------+         +-------+

    after   +-------+         +-------+ <- last            ( item D 는 양쪽 다 끊긴 채 버려진다 )
            | item B|<------->| item C|
            +-------+         +-------+

    removeFirst 는 removed.next 만 끊고, removeLast 는 removed.prev 만 끊는다
    (각각 반대쪽은 그 노드가 끝이었으므로 원래 null 이다)

배열판과의 맞바꿈
    없어진 것 : 용량, 확장 복사, 되감기 계산, 감김을 푸는 재배치
    생긴 것   : 원소마다 노드 객체 하나 + 참조 두 개의 메모리, 흩어진 메모리 접근
```

### `필드`

- `static class Node<E> { E item; Node<E> prev; Node<E> next; }` — 역할:
- `Node<E> first` — 역할:
- `Node<E> last` — 역할:
- `private int size` — 역할:

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void enqueue(E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `E dequeue()`

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()`

- 하는 일:
- 논리:
- 비용(왜):

### `E peekFirst()`

- 하는 일:
- 논리:
- 비용(왜):

### `E peekLast()`

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

### `E removeFirst()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E removeLast()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ArrayQueue | | | |
| CircularQueue | | | |
| ArrayDeque | | | |
| LinkedDeque | | | |

## 구현 — RecentCounter (`src/main/java/com/datastructure/queue/RecentCounter.java`)

### `필드`

- `public static final int WINDOW_MILLIS = 3000` — 역할:
- `private final Queue<Integer> requests` — 역할:

### `RecentCounter(Queue<Integer> queue)`

- 하는 일:
- 논리:
- 비용(왜):

### `int ping(int t)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

## 문제 — QueueProblems (`src/main/java/com/datastructure/queue/QueueProblems.java`)

### 문제 1. 회문 판별

> 문제 설명: 알파벳과 숫자만 보고 대소문자는 무시한다.
> `"A man, a plan, a canal: Panama"` -> `true` / `"race a car"` -> `false` / `""` -> `true`
> 생각할 것 — 왜 데크인가? 양쪽 끝을 동시에 봐야 하기 때문이다. 큐로는 안 된다. /
> 원소가 하나 남았을 때는 어떻게 되는가?
> 시그니처: `static boolean isPalindrome(String input, Deque<Character> buffer)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 슬라이딩 윈도우 최댓값 (이 문제집의 함정)

> 문제 설명: 크기 k 인 창을 왼쪽부터 한 칸씩 옮기며 각 창의 최댓값을 모은다.
> `[1, 3, -1, -3, 5, 3, 6, 7], k=3` -> `[3, 3, 5, 5, 6, 7]`
> 함정 — 창마다 k 개를 훑으면 O(n*k) 다. 테스트에 20만 개 x k=1000 케이스와 시간 제한이 있다.
> 생각할 것 — 데크에 "아직 최댓값이 될 수 있는 후보"의 인덱스만 남기면 어떻게 되는가? /
> 새 값이 들어왔을 때, 그보다 작은 뒤쪽 후보들은 앞으로 영원히 답이 될 수 있는가? /
> 창을 벗어난 후보는 어느 쪽 끝에서 빠지는가? /
> 각 인덱스가 데크에 몇 번 들어가고 몇 번 나오는가? 그게 복잡도다.
> 시그니처: `static int[] slidingWindowMax(int[] values, int k, Deque<Integer> buffer)` — O(n) 이어야 한다. buffer 에는 인덱스를 담으면 편하다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 스트림에서 처음으로 한 번만 나온 문자

> 문제 설명: 문자열을 앞에서부터 읽으며, 그 시점까지 딱 한 번만 나온 문자 중 가장 먼저 나온 것을 기록한다.
> 없으면 `'#'` 을 넣는다.
> `"abcabc"` -> `"aaabc#"`
> `a` -> a / `ab` -> a 가 여전히 처음 / `abc` -> a / `abca` -> a 가 두 번 나왔다. b 가 답 /
> `abcab` -> b 도 두 번. c 가 답 / `abcabc` -> 전부 두 번씩. 남은 게 없으므로 #
> 이 문제는 Queue 만 받는다. 앞에서 빼고 뒤에 넣는 것만 필요하기 때문이다.
> 데크가 아니어도 풀린다는 것 자체가 정보다.
> 생각할 것 — 큐에는 무엇을 담아야 하는가? / 큐 앞에 있는 문자가 이미 두 번 나왔다면 어떻게 하는가?
> 시그니처: `static String firstUniqueStream(String input, Queue<Character> buffer)` — 문자는 소문자 알파벳만 들어온다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 4. k 칸 오른쪽으로 회전

> 문제 설명: `[1, 2, 3, 4, 5], k=2` -> `[4, 5, 1, 2, 3]`
> 01번(배열)에서는 세 번 뒤집었고, 02번(연결)에서는 링크 몇 개만 바꿨다.
> 데크에서는 세 번째 방법이 있다. 훨씬 단순하다.
> 생각할 것 — 뒤에서 하나 빼서 앞에 넣으면 무슨 일이 일어나는가? 그걸 몇 번 하면 되는가? /
> 그 방법의 복잡도는? k 가 아주 크면 어떻게 줄이는가?
> 시그니처: `static <E> void rotate(Deque<E> deque, int k)`

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

- 원본 README: `/home/jun/project/myway/data-structure/04-queue-deque/README.md`
- 구현: `/home/jun/project/myway/data-structure/04-queue-deque/src/main/java/com/datastructure/queue/`
- 테스트: `/home/jun/project/myway/data-structure/04-queue-deque/src/test/java/com/datastructure/queue/`
- 참고 구현: `/home/jun/project/myway/data-structure/04-queue-deque/impl/`
