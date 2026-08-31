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

### 구조 — 트리를 배열에 담는 법

```
BinaryHeap — 트리처럼 생각하고 배열에 담는다. 참조(포인터)가 하나도 없다
+-----------------------------------------------------+
| size = 7                                            |
| comparator ---+   (무엇이 "앞선다"인지의 정의)         |
| elements ---+                                       |
+-------------|---------------------------------------+
              v
    idx     0     1     2     3     4     5     6     7
        +-----+-----+-----+-----+-----+-----+-----+-----+
        |  1  |  3  |  2  |  7  |  5  |  9  |  4  |     |
        +-----+-----+-----+-----+-----+-----+-----+-----+

    같은 배열을 트리로 보면 (레벨 순서로, 왼쪽부터 빈틈없이 채운 완전 이진 트리)

                          [0]=1
                       /         \
                  [1]=3           [2]=2
                 /     \         /     \
             [3]=7   [4]=5   [5]=9   [6]=4

    인덱스 규약 — 0-base 다. 0번 칸을 비우지 않고 루트로 쓴다
        parentOf(i) = (i - 1) / 2        (정수 나눗셈)
        leftOf(i)   = 2 * i + 1
        rightOf(i)  = 2 * i + 2

        확인   i=0 -> left 1, right 2
               i=1 -> left 3, right 4,  parent (1-1)/2 = 0
               i=2 -> left 5, right 6,  parent (2-1)/2 = 0     <- 1/2 = 0
               i=4 ->                   parent (4-1)/2 = 1     <- 3/2 = 1
               i=6 ->                   parent (6-1)/2 = 2     <- 5/2 = 2

    왜 이 계산이 성립하는가 — 레벨 순서로 빈틈없이 채웠기 때문이다
        레벨      0        1                2
        인덱스    0      1   2      3   4   5   6
        노드 수   1        2                4        ... 두 배씩 늘고, 중간에 빈칸이 없다
        그래서 "몇 번째 노드인가"만으로 부모와 자식이 어디인지 산수로 나온다.
        빈칸을 허용하는 순간(예: BST) 이 계산이 깨져서 left/right 참조를 저장할 수밖에 없다.
        힙이 참조 없이 배열 하나로 끝나는 이유가 "완전 이진 트리"라는 모양 제약 하나다

    힙 성질 (BST 와 다르다)
        부모는 두 자식보다 앞선다 (comparator 기준). 약속은 그게 전부다.
        형제 사이 순서도, 좌우 순서도 정해져 있지 않다 -> 전체 정렬이 아니다
        위 그림에서 [1]=3 이 [2]=2 보다 뒤인 것도 정상이다 (둘은 형제라 서로 약속이 없다)
        약속을 이만큼만 하기 때문에 삽입/삭제가 O(log n) 으로 끝난다.
        그리고 답(최우선 원소)은 언제나 elements[0] -> peek 은 O(1)
```

### 동작 — 삽입 (siftUp)

```
insert(0) : 배열 맨 끝 = 트리의 "다음 자리"에 놓고, 부모와 비교하며 위로 올린다

    (1) elements[size] = 0;  size++;      <- 완전 이진 트리를 깨지 않는 유일한 자리
    idx     0     1     2     3     4     5     6     7
        |  1  |  3  |  2  |  7  |  5  |  9  |  4  |  0  |
                                                    ^ 새 원소 (index 7)
                          [0]=1
                       /         \
                  [1]=3           [2]=2
                 /     \         /     \
             [3]=7   [4]=5   [5]=9   [6]=4
            /
        [7]=0        <- 여기. 부모는 (7-1)/2 = 3

    (2) siftUp(7) : 부모보다 앞서면 자리를 맞바꾸고 부모 자리로 올라간다
        i=7, parent=3 :  0 < 7  -> swap
            |  1  |  3  |  2  |  0  |  5  |  9  |  4  |  7  |
        i=3, parent=1 :  0 < 3  -> swap
            |  1  |  0  |  2  |  3  |  5  |  9  |  4  |  7  |
        i=1, parent=0 :  0 < 1  -> swap
            |  0  |  1  |  2  |  3  |  5  |  9  |  4  |  7  |
        i=0           :  루트 도달 -> 정지

    after                 [0]=0
                       /         \
                  [1]=1           [2]=2
                 /     \         /     \
             [3]=3   [4]=5   [5]=9   [6]=4
            /
        [7]=7

    멈추는 조건은 둘뿐 : index == 0 (루트에 닿음) 또는 부모가 이미 앞선다
    지나온 자리는 뿌리까지의 한 줄뿐이다 -> 이동 거리 = 높이 = O(log n).
    형제도, 다른 가지도 쳐다보지 않는다

    꽉 차면 ensureCapacity 가 2배 배열로 복사한다 (동적 배열과 같은 상환 O(1))
```

### 동작 — 꺼내기 (siftDown)

```
poll() : 루트를 꺼내고, 마지막 원소를 루트에 올린 뒤 아래로 내린다

    시작    idx     0     1     2     3     4     5     6
                |  0  |  1  |  2  |  3  |  5  |  9  |  4  |      size = 7

    (1) top = elements[0] = 0                    <- 돌려줄 값을 먼저 잡는다
    (2) size--;
        elements[0] = elements[size];            <- 마지막 원소(4)를 루트 자리로
        elements[size] = null;                   <- 마지막 칸은 비운다 (참조 누수 방지)

                |  4  |  1  |  2  |  3  |  5  |  9  |null |      size = 6

                          [0]=4        <- 힙 성질이 깨진 상태
                       /         \
                  [1]=1           [2]=2
                 /     \         /
             [3]=3   [4]=5   [5]=9

    왜 하필 마지막 원소를 올리나
        완전 이진 트리를 유지한 채 없앨 수 있는 자리가 마지막 칸뿐이기 때문이다.
        "루트를 지우고 나머지를 앞으로 당긴다"는 배열식 사고는 부모-자식 관계를 통째로 흐트러뜨린다
        (인덱스가 하나씩 밀리면 2i+1 계산이 가리키는 노드가 전부 달라진다)

    (3) siftDown(0) : 두 자식 중 더 앞선 쪽과 비교해, 지면 그쪽과 자리를 바꾸고 내려간다
        i=0 : left=1(값 1), right=2(값 2) -> 더 앞선 자식은 1   |  4 > 1 -> swap
            |  1  |  4  |  2  |  3  |  5  |  9  |
        i=1 : left=3(값 3), right=4(값 5) -> 더 앞선 자식은 3   |  4 > 3 -> swap
            |  1  |  3  |  2  |  4  |  5  |  9  |
        i=3 : left = 2*3+1 = 7 >= size(6) -> 자식이 없다 -> 정지

    after                 [0]=1
                       /         \
                  [1]=3           [2]=2
                 /     \         /
             [3]=4   [4]=5   [5]=9

    반드시 "더 앞선 자식"과 바꿔야 한다
        아무 자식이나 올리면 올라간 쪽이 남은 형제보다 뒤처져 힙 성질이 다시 깨진다
    멈추는 조건 : 자식이 없다(left >= size) 또는 이미 두 자식보다 앞선다
    지나온 자리는 아래로 한 줄뿐이다 -> O(log n)

peek() = elements[0], O(1). "루트가 언제나 답"이라는 것이 힙의 전부다
```

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

### 구조 — 차이는 comparator 하나

```
MinHeap / MaxHeap 은 BinaryHeap 을 그대로 상속하고 생성자 한 줄만 다르다
    MinHeap : super(Comparator.naturalOrder())
    MaxHeap : super(Comparator.<E>naturalOrder().reversed())

같은 순서로 5, 1, 9, 3 을 넣었을 때 (insert 순서가 같아도 모양이 다르다)

        MinHeap                              MaxHeap
             [0]=1                                [0]=9
            /     \                              /     \
        [1]=3     [2]=9                      [1]=3     [2]=5
        /                                    /
    [3]=5                                [3]=1

        |  1  |  3  |  9  |  5  |            |  9  |  3  |  5  |  1  |
        peek() = 1 (가장 작은 것)             peek() = 9 (가장 큰 것)

siftUp / siftDown 코드는 한 줄도 다르지 않다. 바뀌는 것은 "앞선다"의 정의뿐이다.
힙이 정하는 것은 "무엇이 먼저 나오는가"이지 "무엇이 작은가"가 아니다 —
그래서 우선순위 큐로 쓸 때 comparator 만 갈아끼우면 어떤 기준으로든 동작한다
```

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

### 구조

```
SortedListHeap — 트리가 아니라 "정렬을 유지하는 배열". 같은 계약, 다른 대가
+-----------------------------------------------------+
| size = 4                                            |
| comparator ---+                                     |
| elements ---+     moves = 3   (밀어낸 횟수 계수기)    |
+-------------|---------------------------------------+
              v
    idx     0     1     2     3     4     5     6     7
        +-----+-----+-----+-----+-----+-----+-----+-----+
        |  9  |  5  |  3  |  1  |     |     |     |     |
        +-----+-----+-----+-----+-----+-----+-----+-----+
          뒤로 갈수록 앞선다 ------------------->  ^
                                          peek / poll 이 보는 곳 = elements[size-1]

    정렬 방향 규약: 배열의 끝이 가장 우선순위 높은 원소다 (앞이 아니라 끝이 "머리")
    앞을 머리로 삼았다면 poll 마다 전체를 앞으로 당겨야 했다. 끝을 머리로 두면 그 시프트가 사라진다
    BinaryHeap 과 달리 여기서는 전체가 완전히 정렬되어 있다 — 그게 곧 비용이다
```

### 동작 — 삽입과 꺼내기

```
insert(4) : 자리를 찾아 뒤에서부터 한 칸씩 밀며 끼워 넣는다. O(n)
    i = size 에서 시작해, 앞 원소가 새 원소보다 뒤처지는 동안 계속 뒤로 민다

    before  |  9  |  5  |  3  |  1  |     |          size = 4, i = 4
                              ^ 1 은 4 보다 뒤처진다 -> 뒤로 민다 (moves++)
            |  9  |  5  |  3  |     |  1  |
                        ^ 3 은 4 보다 뒤처진다 -> 뒤로 민다 (moves++)
            |  9  |  5  |     |  3  |  1  |
                  ^ 5 는 4 보다 앞선다 -> 여기서 멈추고 빈자리에 쓴다
    after   |  9  |  5  |  4  |  3  |  1  |          size = 5

    최악에는 n 번을 밀어야 한다 -> O(n). moves 가 그 밀어낸 횟수를 그대로 센다
    (동적 배열의 중간 삽입과 정확히 같은 그림이다)

poll() : 끝에서 떼어낸다. 시프트가 없다. O(1)
    before  |  9  |  5  |  4  |  3  |  1  |          size = 5
                                        ^ elements[--size] 를 읽고 그 칸을 null 로
    after   |  9  |  5  |  4  |  3  |null |          size = 4

peek() = elements[size-1], O(1)

같은 계약, 다른 비용 배분
                        insert        peek        poll
    BinaryHeap          O(log n)      O(1)        O(log n)
    SortedListHeap      O(n)          O(1)        O(1)

    "항상 완전히 정렬해 둔다"의 대가가 insert 의 O(n) 이다.
    힙은 완전 정렬을 포기하고 "부모가 자식보다 앞선다"만 지켜서 양쪽을 O(log n) 으로 맞춘다.
    필요한 것이 최우선 원소 하나뿐이라면 전체를 줄 세울 이유가 없다 — 이것이 힙의 거래다
```

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
