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
