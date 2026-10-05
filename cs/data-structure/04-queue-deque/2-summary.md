# data-structure/04-queue-deque — 정리 (힌트)

## 해결하는 문제

"먼저 온 것을 먼저 처리한다"는 약속을 지키려면 넣는 쪽과 빼는 쪽이 **반대 끝**이어야 한다.\
스택(03)은 한쪽 끝만 써서 배열과 잘 맞았지만, 반대 끝에서 빼기 시작하는 순간 배열은 앞이 비어 간다.

```text
배열로 만든 줄: 앞에서 빼면 앞칸이 죽는다      원형으로 감으면 앞칸을 다시 쓴다
+---+---+---+---+---+                          +---+---+---+---+---+
|   |   | C | D | E | <- 넣기                   | F |   |   | D | E |
+---+---+---+---+---+                          +---+---+---+---+---+
  x   x   ^ head  (빈 두 칸은 영영 못 쓴다)        ^ 끝을 넘으면 0번으로 되감긴다
```

큐는 이 문제를 "한 칸씩 당기기(O(n))" 대신 "표지를 옮기고 끝에서 되감기"로 푼다 — 넣기·빼기 모두 O(1).\
덱은 여기에 "양 끝 모두에서 넣고 뺀다"를 더해, 스택과 큐를 한 구조로 흉내 낸다.\
쉬운 예: 급식 줄 — 뒤에 서고 앞에서 받는다.\
똑같은 구조다: Java `ArrayDeque` — 원형 배열 하나로 큐와 스택을 다 한다.\
실무 예: 서버의 요청 대기열·작업 큐 — 들어온 순서대로 워커가 꺼내 처리한다.

  - *되감기(wrap-around)*: 인덱스가 배열 끝을 넘으면 0번으로 돌아오는 것. `(head + i) % 길이` 한 줄이다.

### 한눈에 — 쉽게 말하면

**큐 = 급식 줄.**\
뒤로 와서 서고, 앞에서부터 받는다.\
먼저 온 사람이 먼저 받는다 — FIFO(First In, First Out, 선입선출).

```text
      받는다 <- [ A | B | C ] <- 와서 선다
      (앞, dequeue)          (뒤, enqueue)
```

**덱(deque) = 양쪽 문이 다 열리는 지하철 칸.**\
앞문으로도 뒷문으로도 타고 내릴 수 있다.\
큐(한쪽으로 타서 반대쪽으로 내림)와 스택(탄 문으로 도로 내림)을 둘 다 흉내 낼 수 있다.

```text
  타고/내리고 <-> [ A | B | C ] <-> 타고/내리고
  (addFirst/removeFirst)     (addLast/removeLast)
```

이 줄이 **똑같은 구조로** 큐다: 줄 선 사람 = 원소, 줄 앞 = head, 서기 = enqueue, 받기 = dequeue.\
프린터 인쇄 대기열, 서버의 요청 처리 대기열이 전부 이 줄이다.\
배열로 만들면 "앞이 비는 문제"가 생기는데, 그걸 푸는 과정이 이 문서의 줄거리다: ArrayQueue(문제 발견) → CircularQueue(원형으로 해결) → ArrayDeque(양쪽 끝으로 확장) → LinkedDeque(연결 리스트로 같은 것).

> **FIFO(선입선출)** — First In, First Out, 먼저 들어온 것이 먼저 나가는 규칙.\
> 예: 급식 줄에서 먼저 선 사람이 먼저 받는다 — 스택의 LIFO와 정반대다.

> **데크(deque, double-ended queue)** — 양쪽 끝에서 모두 넣고 뺄 수 있는 구조.\
> 예: 한쪽으로만 쓰면 스택이 되고, 한쪽으로 넣어 반대쪽으로 빼면 큐가 된다.

## 동작·원리

### 전체 흐름

```text
[1] 큐 = 반대 끝에서 넣고 뺀다           [2] 나이브 배열 큐: head 가 오른쪽으로만 간다
    빼기 <- [ A | B | C ] <- 넣기            +---+---+---+---+
    head                  head+size          | x | x | C | D |   앞칸이 버려진다 -> 용량이 계속 는다
                                             +---+---+---+---+    (wastesSpace: 2048)
          |
          v
[3] 원형 큐: % 로 되감는다               [4] 왜 tail 을 안 두나
    idx  0   1   2   3   4                   head == tail 이 "꽉 참"인지 "빔"인지 모른다
       +---+---+---+---+---+                 size 하나면 모호함이 없다:
       | E |   |   | C | D |                    빔 = size == 0, 꽉 참 = size == length
       +---+---+---+---+---+
         ^ 감겨서 0번으로   ^ head
    논리 i번째 = elements[(head + i) % length]          (reusesSpace: 4)
          |
          v
[5] 확장은 감김을 풀면서                 [6] 덱 = 양 끝 모두
    감긴 상태로 통복사하면 순서가 깨진다     addFirst: head = (head - 1 + length) % length
    논리 순서대로 새 배열 0번부터 옮긴다             (head - 1 만 하면 -1)
    (01번의 Arrays.copyOf 가 여기서는 안 통함)   연결판(LinkedDeque): 되감기·확장·용량이 전부 없다
```

- [1] 넣는 끝과 빼는 끝이 다르다. 그래서 "끝 하나만 보면 된다"는 스택의 편의가 사라진다.
- [2] `head`를 옮기기만 하면 앞칸이 죽는다. 동작은 맞는데 같은 시나리오에서 용량이 2048까지 는다.
- [3] 끝과 처음을 이어 붙이면 죽는 칸이 없다. 나머지 연산 한 글자가 원형 큐의 전부다.
- [4] `tail` 대신 `size`를 두면 "꽉 참"과 "빔"이 구분된다. 한 칸 비워두기·플래그 방식보다 단순하다.
- [5] 확장할 때는 논리 순서대로 풀어서 옮긴다. 01번에서 통하던 통복사가 여기서 깨지는 이유가 감김이다.
- [6] 앞으로도 넣으려면 `head`를 뒤로 감아야 하고, 음수를 피하려면 길이를 더한 뒤 나머지를 취한다. 연결판은 이 계산이 아예 없다.

### 계약 — Queue (`src/main/java/com/datastructure/queue/Queue.java`)

- `void enqueue(E element)`
- `E dequeue()`
- `E peek()`
- `int size()`
- `boolean isEmpty()`
- `void clear()`

### 계약 — Deque (`src/main/java/com/datastructure/queue/Deque.java`)

- `void addFirst(E element)`
- `void addLast(E element)`
- `E removeFirst()`
- `E removeLast()`
- `E peekFirst()`
- `E peekLast()`
- (extends `Queue<E>` — `enqueue` = `addLast`, `dequeue` = `removeFirst`, `peek` = `peekFirst`)

### 구현 — ArrayQueue (`src/main/java/com/datastructure/queue/ArrayQueue.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

#### 구조

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

#### 동작 — 추가

```
enqueue(F) : 뒤쪽 빈 칸에 쓰기만 한다. O(1)
        +-----+-----+-----+-----+-----+-----+        +-----+-----+-----+-----+-----+-----+
        |null |null |  C  |  D  |  E  |     |   ->   |null |null |  C  |  D  |  E  |  F  |
        +-----+-----+-----+-----+-----+-----+        +-----+-----+-----+-----+-----+-----+
                    ^head=2, size=3                              ^head=2, size=4
    ensureCapacity(head + size + 1);      <- 필요한 자리는 0..head+size 다 (head 왼쪽까지 포함)
    elements[head + size] = F;  size++;
```

그림 해설 (한 단계씩):

- 줄 맨 뒤 자리(head + size)에 쓰고 size를 1 올린다.\
  아무도 안 움직이니 O(1).
- 확장 검사 때 "버려진 왼쪽 칸"까지 포함해 자리를 계산한다 — 왼쪽 칸은 있어도 못 쓰는 칸이기 때문.

#### 동작 — 삭제

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

그림 해설 (한 단계씩):

- [1] 앞사람이 받고 나가면, 뒷사람들을 전부 한 칸씩 당기는 대신(그건 O(n)) "줄 앞이 여기"라는 표지(head)만 오른쪽으로 옮긴다.\
  O(1).
- [2] 그 대가: head가 지나간 왼쪽 칸은 비어 있는데도 영영 못 쓴다.\
  넣고 빼기를 반복하면 원소는 몇 개 없는데 배열만 계속 커진다 — 이 낭비를 고치는 것이 다음 절의 원형 큐다.

#### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `Object[] elements` — 역할:
- `int head` — 역할:
- `private int size` — 역할:

#### `ArrayQueue()`

- 하는 일:
- 논리:
- 비용(왜):

#### `ArrayQueue(int initialCapacity)`

- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

#### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

#### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

#### `private void ensureCapacity(int minCapacity)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void enqueue(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E dequeue()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### 구현 — CircularQueue (`src/main/java/com/datastructure/queue/CircularQueue.java`)

#### 구조

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

> **모듈러(%, 나머지 연산)** — 나눈 나머지.\
> 예: `6 % 5 = 1` — 시계가 12를 넘으면 1로 돌아오듯, 인덱스가 배열 끝을 넘으면 0으로 되감는 데 쓴다(원형 큐의 핵심 한 글자).

> **원형 배열(circular buffer)** — 배열의 끝과 처음을 이어 붙인 것처럼 쓰는 방식.\
> 예: head 가 앞으로 나아가도 빈 앞칸을 버리지 않고 다시 돌아와 채우므로, 배열 길이가 그대로여도 enqueue/dequeue 를 무한히 반복할 수 있다.

#### 동작 — 추가

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

그림 해설 (한 단계씩):

- 쓸 칸을 `(head + size) % 길이`로 그때그때 계산한다.\
  끝을 넘으면 나머지 연산이 앞쪽 빈 칸으로 되감아 준다 — ArrayQueue가 버리던 칸이 되살아난다.\
  O(1).
- 순서 주의: 확장(ensureCapacity)이 배열 길이를 바꿀 수 있으므로, 칸 계산은 반드시 확장 뒤에 한다.

#### 동작 — 삭제

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

그림 해설 (한 단계씩):

- 앞 칸을 읽고 null로 비운 뒤, head를 한 칸 옮긴다 — 단, `% 길이`를 붙여서 끝(4)에 닿으면 0으로 돌아오게.\
  O(1).
- ArrayQueue와의 차이는 `head++` 뒤에 `% len` 하나뿐인데, 이 한 글자가 "버려진 칸" 문제를 없앤다.

#### 동작 — 확장

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

그림 해설 (한 단계씩):

- 원형으로 감긴 상태에서는 배열에 저장된 순서(E F G C D)와 줄 선 순서(C D E F G)가 다르다.
- 그래서 통째로 복사하면 순서가 깨진다.\
  줄 선 순서대로(indexOf(i)를 따라) 한 명씩 새 배열의 0번부터 옮겨, 감김을 편다.
- 옮긴 뒤 head = 0. 확장은 그 순간만 O(n), 두 배씩 늘리므로 상환 O(1)은 그대로다.

#### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `Object[] elements` — 역할:
- `int head` — 역할:
- `private int size` — 역할:

#### `CircularQueue()`

- 하는 일:
- 논리:
- 비용(왜):

#### `CircularQueue(int initialCapacity)`

- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

#### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

#### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

#### `private void ensureCapacity(int minCapacity)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void enqueue(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E dequeue()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### 구현 — ArrayDeque (`src/main/java/com/datastructure/queue/ArrayDeque.java`)

#### 구조

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

#### 동작 — 앞쪽 끝

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

그림 해설 (한 단계씩):

- [1] 앞에 넣기: head를 왼쪽으로 한 칸 되감고 그 칸에 쓴다.\
  head가 0이면 한 칸 왼쪽은 배열의 맨 끝 — `(head - 1 + 길이) % 길이`로 되감는다.

> **`+ 길이`를 먼저 더하기(음수 되감기)** — 자바의 `%` 는 음수를 그대로 음수로 돌려주므로, 빼기 전에 길이를 더해 양수로 만드는 관용구.\
> 예: `0 - 1 = -1` 은 배열 인덱스로 쓸 수 없지만, 길이를 더해 `(0 - 1 + 8) % 8 = 7` 로 하면 안전하게 끝 칸이 나온다.

- [2] 앞에서 빼기: 원형 큐의 dequeue와 완전히 같다.

#### 동작 — 뒤쪽 끝

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

그림 해설 (한 단계씩):

- [3] 뒤에 넣기: 원형 큐의 enqueue와 같다 — `indexOf(size)` 칸에 쓴다.
- [4] 뒤에서 빼기: head는 그대로 두고, 마지막 칸(`indexOf(size-1)`)만 비우고 size를 줄인다.\
  O(1).
- 기억 규칙: **앞을 만지면 head가 움직이고, 뒤를 만지면 size만 변한다.**

#### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `Object[] elements` — 역할:
- `int head` — 역할:
- `private int size` — 역할:

#### `ArrayDeque()`

- 하는 일:
- 논리:
- 비용(왜):

#### `ArrayDeque(int initialCapacity)`

- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

#### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

#### `void enqueue(E element)`

- 하는 일:
- 논리:
- 비용(왜):

#### `E dequeue()`

- 하는 일:
- 논리:
- 비용(왜):

#### `E peek()`

- 하는 일:
- 논리:
- 비용(왜):

#### `E peekFirst()`

- 하는 일:
- 논리:
- 비용(왜):

#### `E peekLast()`

- 하는 일:
- 논리:
- 비용(왜):

#### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

#### `void addFirst(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void addLast(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E removeFirst()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E removeLast()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### 구현 — LinkedDeque (`src/main/java/com/datastructure/queue/LinkedDeque.java`)

#### 구조

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

#### 동작 — 추가

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

그림 해설 (한 단계씩):

- 새 노드를 만들어 옛 첫 칸과 화살표로 잇고, first 표지를 새 노드로 옮긴다.\
  되감기도 %도 없다 — 이중 연결 리스트의 linkFirst와 같다.\
  O(1).
- 리스트가 비어 있었다면 새 노드가 처음이자 끝이므로 last도 함께 세운다.

#### 동작 — 삭제

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

그림 해설 (한 단계씩):

- last 표지를 한 칸 앞으로 당기고, 떼어낸 노드의 화살표를 끊는다.\
  이중 연결이라 "앞 칸"을 즉시 아니까 O(1).
- 떼어낸 노드에서 끊을 화살표는 한쪽뿐이다 — 끝 노드였으니 반대쪽은 원래 null이었다.

> **흩어진 메모리 접근(캐시 지역성)** — 쓸 데이터가 메모리에 붙어 있으면 CPU가 한꺼번에 미리 읽어 오고, 흩어져 있으면 매번 새로 찾아가야 하는 성질.\
> 예: 연결 리스트의 노드는 여기저기 흩어져 있어서, 같은 O(1)이라도 실측은 배열판이 빠른 편이다.

#### `필드`

- `static class Node<E> { E item; Node<E> prev; Node<E> next; }` — 역할:
- `Node<E> first` — 역할:
- `Node<E> last` — 역할:
- `private int size` — 역할:

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

#### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

#### `void enqueue(E element)`

- 하는 일:
- 논리:
- 비용(왜):

#### `E dequeue()`

- 하는 일:
- 논리:
- 비용(왜):

#### `E peek()`

- 하는 일:
- 논리:
- 비용(왜):

#### `E peekFirst()`

- 하는 일:
- 논리:
- 비용(왜):

#### `E peekLast()`

- 하는 일:
- 논리:
- 비용(왜):

#### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

#### `void addFirst(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void addLast(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E removeFirst()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `E removeLast()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### 구현 — RecentCounter (`src/main/java/com/datastructure/queue/RecentCounter.java`)

#### `필드`

- `public static final int WINDOW_MILLIS = 3000` — 역할:
- `private final Queue<Integer> requests` — 역할:

#### `RecentCounter(Queue<Integer> queue)`

- 하는 일:
- 논리:
- 비용(왜):

#### `int ping(int t)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

## 쓰이는 곳

- **Java `ArrayDeque`** — 원형 배열 하나로 `Deque`를 구현한다. JDK가 큐와 스택 양쪽에 권하는 클래스이고, 이 노트의 `ArrayDeque`가 그 축소판이다.
- **작업 큐·메시지 큐** — 요청을 들어온 순서로 워커에 넘긴다. 큐가 무한히 자라는 것을 막는 장치가 [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)다.
- **BFS의 프런티어** — 다음에 방문할 정점을 큐에 넣고 앞에서 꺼낸다([algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)). 그래서 가까운 정점부터 나온다.
- **링 버퍼** — 고정 크기 원형 큐. NIC의 송수신 디스크립터 링, 커널 로그 버퍼(printk ring buffer), Linux `io_uring`의 제출·완료 큐가 이 모양이다. 꽉 찼을 때 덮어쓸지 막을지가 정책이다.
- **슬라이딩 윈도우 최댓값** — 단조 덱으로 창의 최댓값을 O(n)에 구한다([algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md), 문제 2).
- **요율 제한의 슬라이딩 윈도우** — 최근 N초 안의 요청만 큐에 남기고 앞에서 만료를 빼는 것이 `RecentCounter`이고, [ops-patterns/04-rate-limiter](../../ops-patterns/04-rate-limiter/2-summary.md)의 슬라이딩 로그 방식과 같다.
- **스레드 풀의 작업 대기열** — Java `ThreadPoolExecutor`는 제출된 작업을 `BlockingQueue`에 쌓고 워커 스레드가 앞에서 꺼낸다(기본 구성은 FIFO).
- **작업 훔치기(work stealing) 덱** — 자기 작업은 한쪽 끝에서 넣고 빼고, 다른 워커는 반대 끝에서 훔친다. 양 끝이 필요한 대표 사례다(Java `ForkJoinPool`의 워커 큐, Chase–Lev 덱).

## 적용 — 풀어나가는 법

큐·덱 문제는 "순서만 필요한가, 양 끝이 다 필요한가"에서 갈린다.\
순서: ① 넣는 끝과 빼는 끝을 정한다(한쪽만이면 스택, 반대 끝이면 큐, 양쪽이면 덱) → ② 파라미터는 필요한 만큼만 받는다(`Queue`로 받으면 호출자가 앞에 넣을 수 없어 의도가 드러난다) → ③ 창(window)이 있는 문제는 "아직 답이 될 수 있는 후보"만 덱에 남기고 앞에서 만료·뒤에서 탈락을 뺀다 → ④ 각 원소가 몇 번 들어가고 나오는지 세어 O(n)인지 확인한다.\
아래 네 문제와 `RecentCounter`가 모두 이 순서로 풀린다.

### 문제 — 이 챕터가 시키는 것

03번 스택(LIFO)과 정확히 반대인 선입선출(FIFO)을 직접 만든다.\
스택은 한쪽 끝만 건드리므로 배열과 잘 맞았지만, 큐는 넣는 쪽과 빼는 쪽이 반대라 배열 구현에서 문제가 생긴다.\
**그 문제를 일부러 만든 다음에 고치는 것이 이 과제의 본체다** — 1번을 건너뛰고 2번부터 하면 원형 배열은 그냥 복잡하기만 하다.

**과제**

- 순서대로 네 구현을 채운다(TODO 25개, 테스트 114개가 전부 실패인 상태에서 시작한다).\
  `ArrayQueue`(가장 먼저 떠오르는 방식 — 동작은 맞는데 한계가 있다) → `CircularQueue`(그 한계를 되감기로 고침) → `ArrayDeque`(원형을 양쪽 끝으로 확장) → `LinkedDeque`(노드 — 되감기도 확장도 용량도 없다).
- `Deque extends Queue` 라서 연결 기반 큐는 따로 만들지 않는다 — `LinkedDeque` 가 겸한다(누락이 아니라 중복 제거).
- 응용 문제 4개 (`QueueProblems`)\
  `isPalindrome(String, Deque<Character>)` — 양 끝에서 하나씩 빼며 회문 판정.\
  `slidingWindowMax(int[], int, Deque<Integer>)` — 창마다 최댓값. 이 문제집의 함정이다.\
  `firstUniqueStream(String, Queue<Character>)` — 스트림에서 처음으로 한 번만 나온 문자.\
  `rotate(Deque<E>, int)` — k 칸 오른쪽 회전. 01번(세 번 뒤집기)·02번(링크 재연결)에 이은 세 번째 방법.
- `RecentCounter.ping(int t)` — 최근 3000ms 안의 요청 수. 창이 양끝 포함이라 조건이 `< t - 3000` 이다(`<=` 로 쓰면 off-by-one).
- 성능·계약 제약\
  `slidingWindowMax` 는 100만 x k=5만을 5초 안에 — 창마다 k 개를 훑는 O(n·k) 구현은 통과하지 못한다(README 의 임계값 메모: 4.75e10 회).\
  `RecentCounter` 는 10만 번 호출을 5초 안에, 끝나고 3,001개만 남아야 한다.\
  `ArrayQueueTest.wastesSpace` 와 `CircularQueueTest.reusesSpace` 는 같은 시나리오인데 용량이 갈린다 — 그 대비가 2번을 만드는 이유다.\
  계약 테스트가 내부 필드를 직접 본다 — `elements`, `head`(배열판), `first`/`last`/`Node`(연결판) 이름이 사실상 계약의 일부다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ArrayQueue | | | |
| CircularQueue | | | |
| ArrayDeque | | | |
| LinkedDeque | | | |

### 문제 — QueueProblems (`src/main/java/com/datastructure/queue/QueueProblems.java`)

#### 문제 1. 회문 판별

> 문제 설명: 알파벳과 숫자만 보고 대소문자는 무시한다.
> `"A man, a plan, a canal: Panama"` -> `true` / `"race a car"` -> `false` / `""` -> `true`
> 생각할 것 — 왜 데크인가? 양쪽 끝을 동시에 봐야 하기 때문이다. 큐로는 안 된다. /
> 원소가 하나 남았을 때는 어떻게 되는가?
> 시그니처: `static boolean isPalindrome(String input, Deque<Character> buffer)`

> **회문(palindrome)** — 앞으로 읽어도 뒤로 읽어도 같은 문장.\
> 예: "기러기", "다시 합창합시다".

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 2. 슬라이딩 윈도우 최댓값 (이 문제집의 함정)

> 문제 설명: 크기 k 인 창을 왼쪽부터 한 칸씩 옮기며 각 창의 최댓값을 모은다.
> `[1, 3, -1, -3, 5, 3, 6, 7], k=3` -> `[3, 3, 5, 5, 6, 7]`
> 함정 — 창마다 k 개를 훑으면 O(n*k) 다. 테스트에 20만 개 x k=1000 케이스와 시간 제한이 있다.
> 생각할 것 — 데크에 "아직 최댓값이 될 수 있는 후보"의 인덱스만 남기면 어떻게 되는가? /
> 새 값이 들어왔을 때, 그보다 작은 뒤쪽 후보들은 앞으로 영원히 답이 될 수 있는가? /
> 창을 벗어난 후보는 어느 쪽 끝에서 빠지는가? /
> 각 인덱스가 데크에 몇 번 들어가고 몇 번 나오는가? 그게 복잡도다.
> 시그니처: `static int[] slidingWindowMax(int[] values, int k, Deque<Integer> buffer)` — O(n) 이어야 한다. buffer 에는 인덱스를 담으면 편하다.

> **슬라이딩 윈도우(sliding window)** — 배열 위에 크기 k짜리 "창"을 대고 한 칸씩 밀며 창 안만 보는 기법.\
> 예: `[1, 3, -1, -3, ...]` 에 k=3 창을 대면 `[1,3,-1]` → `[3,-1,-3]` → … 처럼 한 칸씩 이동한다.

> **단조 데크(monotonic deque)** — 데크 안을 항상 한 방향 정렬 상태로 유지해, 답이 될 수 없는 후보를 그때그때 버리는 기법.\
> 예: 새 값보다 작은 뒤쪽 후보들은 앞으로 영원히 최댓값이 될 수 없으므로 뒤쪽 끝에서 빼 버린다 — 각 인덱스가 1번 들어가고 1번 나와 O(n)이 된다.

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 3. 스트림에서 처음으로 한 번만 나온 문자

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

#### 문제 4. k 칸 오른쪽으로 회전

> 문제 설명: `[1, 2, 3, 4, 5], k=2` -> `[4, 5, 1, 2, 3]`
> 01번(배열)에서는 세 번 뒤집었고, 02번(연결)에서는 링크 몇 개만 바꿨다.
> 데크에서는 세 번째 방법이 있다. 훨씬 단순하다.
> 생각할 것 — 뒤에서 하나 빼서 앞에 넣으면 무슨 일이 일어나는가? 그걸 몇 번 하면 되는가? /
> 그 방법의 복잡도는? k 가 아주 크면 어떻게 줄이는가?
> 시그니처: `static <E> void rotate(Deque<E> deque, int k)`

- 내 접근:
- 논리:
- 비용(왜):

## 장애 시나리오와 대처

**1. 소비가 생산을 못 따라가 큐가 무한히 자란다**

- 현상: 오래 돌수록 메모리가 늘고 응답이 느려지다가 프로세스가 죽는다.
- 보이는 형태: `java.lang.OutOfMemoryError: Java heap space`. 힙 덤프에 거대한 큐 하나. 죽기 전에는 큐 앞의 요청이 몇 분 전 것이라 처리해도 이미 늦은 상태(지연 누적)다.
  - *백프레셔(backpressure)*: 소비자가 못 따라가면 생산자를 늦추거나 막는 신호.
- 원인: 이 노트의 큐는 용량 상한이 없다 — 확장하거나(배열판) 노드를 계속 만든다(연결판). 넣는 속도가 빼는 속도보다 빠르면 끝없이 는다.
- 대처: 상한을 둔다. 꽉 찼을 때의 정책을 정한다 — 생산자를 막거나(블로킹), 거부하거나, 가장 오래된 것을 버린다(링 버퍼). Java `ArrayBlockingQueue`가 첫 번째 정책이다.

**2. `head`를 뒤로 감을 때 음수 인덱스**

- 현상: `addFirst`가 빈 큐나 `head == 0`에서 죽는다.
- 보이는 형태: `ArrayIndexOutOfBoundsException: Index -1`. `head`가 0일 때만 나므로, 새 덱에 곧바로 `addFirst`하면 바로 터진다. 반대로 `addLast`·`pollFirst`로 `head`를 0에서 옮겨 둔 테스트만 돌리면 지나간다.
- 원인: `(head - 1) % length`는 `head == 0`일 때 -1이다. Java의 `%`는 피제수의 부호를 따르므로 음수가 그대로 나온다.
- 대처: `(head - 1 + length) % length`로 길이를 먼저 더한다. 빈 덱의 `addFirst`와 `head`를 거꾸로 감는 경우(테스트 `addFirstWrapsHeadBackwards`)를 테스트에 넣는다(정답 10번 참고).

**3. 창 경계의 off-by-one — 세지 않아야 할 것을 센다**

- 현상: `RecentCounter.ping`이 기대보다 1 크거나 작다. 대부분의 입력에서는 맞는다.
- 보이는 형태: 정확히 창 크기만큼 떨어진 요청(`t - 3000`)이 있을 때만 결과가 다르다. 예외는 없다.
- 원인: 창이 양끝 포함인데 만료 조건을 `<= t - 3000`으로 썼거나, 반대로 포함이 아닌데 `<`로 썼다. "포함/제외"를 계약에서 확인하지 않았다.
- 대처: 경계값을 딱 맞춘 테스트를 하나 둔다(`ping(1)`, `ping(3001)` → 2). 문제 문장의 "이상/초과"를 조건식 옆에 주석으로 옮겨 적는다.

**4. 감긴 원형 배열을 통째로 복사한 확장**

- 현상: 확장 뒤 큐의 순서가 뒤바뀌거나 `null`이 나온다.
- 보이는 형태: 용량 경계(4→8)를 넘긴 직후 `dequeue`가 엉뚱한 값을 준다. 그 전까지는 정상이다.
- 원인: 감긴 상태에서는 논리 순서와 배열의 물리 순서가 다르다. `Arrays.copyOf`는 물리 순서로 복사하므로 `head` 앞의 원소들이 새 배열 앞쪽에 가고 순서가 깨진다.
- 대처: 확장 시 논리 순서(`(head + i) % length`)대로 새 배열 0번부터 옮기고 `head = 0`으로 되돌린다. 감긴 상태에서 확장하는 테스트(원본의 `growsWhileWrapped`)를 둔다.

## 핵심 문장

- 큐는 넣는 끝과 빼는 끝이 반대다 — 그래서 스택과 달리 배열의 앞이 비고, 그 문제를 `head` 표지와 되감기(`%`)로 푼 것이 원형 큐다.
- `tail` 대신 `size`를 두면 "꽉 참"과 "빔"이 구분되고, 확장은 감김을 논리 순서대로 풀면서 옮겨야 한다 — 01번의 통복사가 여기서 깨지는 이유다.
- 덱은 양 끝을 다 열어 큐와 스택을 겸하며, `Deque extends Queue`이므로 연결 기반 큐를 따로 만들지 않는다. 파라미터는 필요한 능력만 받아 의도를 드러낸다.
- 창이 있는 문제는 덱에 "아직 답이 될 수 있는 후보"만 남기는 것이 핵심이고, 각 원소가 한 번 들어가고 한 번 나오면 O(n)이다(03번 단조 스택과 같은 상환 논리).
- 큐는 상한이 없으면 무한히 자란다 — 꽉 찼을 때의 정책(막기·거부·덮어쓰기)이 없는 큐는 운영에서 OOM으로 돌아온다.

## 관련 주제·근거

- 선행 — [03-stack](../03-stack/2-summary.md): 한쪽 끝만 쓰는 구조. 반대 끝을 쓰는 순간 무엇이 달라지는지 여기와 대조한다.
- 선행 — [01-dynamic-array](../01-dynamic-array/2-summary.md) · [02-linked-list](../02-linked-list/2-summary.md): 배열판의 확장과 연결판의 노드.
- 후속 — [05-hashmap](../05-hashmap/2-summary.md): 순서 구조의 한계("들어 있는가"가 O(n))가 키로 찾는 구조를 부른다.
- 응용 — [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) · [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md) · [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md) · [ops-patterns/04-rate-limiter](../../ops-patterns/04-rate-limiter/2-summary.md).
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `06-queue-deque` (후속 [25-ring-buffer](../25-ring-buffer/2-summary.md)).
- 교재 — CLRS 3판 10.1 스택과 큐.
- myway 원본 — `/home/jun/project/myway/data-structure/04-queue-deque/` (README.md · impl/ArrayQueue.java · impl/CircularQueue.java · impl/ArrayDeque.java · impl/LinkedDeque.java · impl/QueueProblems.java · impl/RecentCounter.java).

### 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/04-queue-deque/README.md`
- 구현: `/home/jun/project/myway/data-structure/04-queue-deque/src/main/java/com/datastructure/queue/`
- 테스트: `/home/jun/project/myway/data-structure/04-queue-deque/src/test/java/com/datastructure/queue/`
- 참고 구현: `/home/jun/project/myway/data-structure/04-queue-deque/impl/`

### 용어 풀이

- **큐(queue)**: 뒤로 들어와 앞으로 나가는 줄. enqueue(줄 서기) / dequeue(맨 앞이 나가기) / peek(맨 앞 보기).
- **FIFO(선입선출) / LIFO(후입선출)**: 먼저 온 것이 먼저 나감(큐) / 나중에 온 것이 먼저 나감(스택).
- **덱(deque, double-ended queue)**: 양쪽 끝 모두에서 넣고 뺄 수 있는 줄.\
  큐도 스택도 흉내 낼 수 있다.
- **head / first / last**: 줄 앞의 위치 표지.\
  배열판에서는 인덱스(숫자), 연결판에서는 노드 참조.
- **size / capacity**: 실제 담긴 개수 / 내부 배열의 칸 수(미리 잡아둔 여유).
- **O(1), O(n)**: 데이터가 n개일 때 걸리는 시간의 대략적 표기.\
  O(1)은 즉시, O(n)은 개수에 비례.\
  O(n*k)는 창(k)마다 훑는 비용까지 곱해진 것.
- **상환 분석(amortized, 분할상환)**: 가끔 드는 비싼 확장 복사를 여러 번의 싼 연산에 나눠 평균 낸 것.\
  두 배 확장이면 평균 O(1).
- **시프트(shift)**: 배열에서 원소들을 한 칸씩 밀거나 당기는 일. head 표지를 두는 이유가 이걸 없애기 위해서다.
- **모듈러(%, 나머지 연산)**: 나눈 나머지.\
  시계처럼 끝을 넘으면 처음으로 되감는 데 쓴다.\
  `(head + i) % 길이`가 원형 큐의 전부.
- **원형 큐(circular queue)**: 배열의 끝과 처음을 나머지 연산으로 이어 원처럼 쓰는 큐.\
  버려지는 칸이 없다.
- **논리 순서 vs 물리 순서**: 사용자 눈의 줄 순서 vs 배열에 실제 저장된 순서.\
  감긴 상태에선 둘이 다르다 — 확장 때 통복사하면 안 되는 이유.
- **되감기(wrap-around)**: 인덱스가 배열 끝을 넘거나 0 아래로 내려갈 때 반대쪽 끝으로 넘어가는 것.
- **노드(node) / 참조(reference)**: 연결 리스트의 한 칸 / 값이 있는 곳을 가리키는 화살표.\
  `null`은 "아무것도 안 가리킴".
- **GC(가비지 컬렉터)**: 아무도 가리키지 않는 객체를 치우는 자동 청소부.\
  뺀 칸/노드의 참조를 null로 끊어야 청소된다.
- **위임(delegation)**: 한 메서드가 일을 다른 메서드에 넘기는 것.\
  `enqueue = addLast`처럼 덱이 큐 계약을 자기 연산으로 구현한다.
- **인터페이스/계약(interface)**: "무엇을 할 수 있나"의 약속 목록.\
  Queue와 Deque는 계약이고, ArrayQueue 등은 그 계약의 구현이다.
- **캐시 지역성(cache locality)**: 메모리에 붙어 있는 데이터는 CPU가 한꺼번에 미리 읽어 빠르다.\
  배열판이 연결판보다 실측이 빠른 이유.
- **회문(palindrome)**: 앞뒤로 읽어도 같은 문장.
- **슬라이딩 윈도우(sliding window)**: 크기 k의 창을 한 칸씩 밀며 창 안만 보는 기법.\
  문제 2는 덱에 "아직 최댓값 후보"만 남겨 O(n)으로 푼다(단조 덱).
- **스트림(stream)**: 길이를 모른 채 흘러오는 대로 한 번만 읽는 데이터 흐름.
