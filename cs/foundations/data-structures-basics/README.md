# 자료구조 기초 (컴퓨터사이언스 부트캠프 with 파이썬 ch.11~13)

> 원고: computer_science repo의 따라 친 노트를 구조만 잡아 이관(2026-09-05). 내용 보강 없음 — 원문 유지, 오탈자만 교정.
> 심화판: [data-structure/](../../data-structure/) · [algorithm/](../../algorithm/) — 이 문서는 책 원고 이관본

## 목차 (파일→절 매핑)

| 원본 파일 | 절 |
|---|---|
| `chapter11/chapter11.py` | 1. 자료구조란 · 2. 추상 자료형(ADT) |
| `chapter11/chapter11-1.py` | 3. 연결 리스트 |
| `chapter11/chapter11-2.py` | 4. 스택 |
| `chapter11/chapter11-3.py` | 5. 큐 |
| `chapter11/chapter11-4.py` | 6. 자료구조 선택 기준 |
| `chapter12/chapter12.py` | 7. 재귀 함수 · 8. 트리와 이진 트리 |
| `chapter12/chapter12-1.py` | 9. 이진 트리 구현과 순회 |
| `chapter13/chapter13.py` | 10. 이진 탐색 트리 |

---

## 1. 자료구조란

출처: `computer_science/chapter/chapter11/chapter11.py`

자료 구조(data structure)란? 데이터(data, 자료)를 효율적으로 검색·변경·삭제할 수 있도록 저장/관리하는 방법을 말한다.

기본적인 자료 구조로는

```
=== 배열 (Array) ===

인덱스:  [0]   [1]   [2]   [3]   [4]
       +-----+-----+-----+-----+-----+
       | 10  | 20  | 30  | 40  | 50  |
       +-----+-----+-----+-----+-----+
       연속된 메모리 공간에 저장


=== 연결 리스트 (Linked List) ===

+------+---+    +------+---+    +------+---+    +------+------+
| 10   | ●-+-->| 20   | ●-+-->| 30   | ●-+-->| 40   | NULL |
+------+---+    +------+---+    +------+---+    +------+------+
[data|next]     [data|next]     [data|next]     [data|next]


=== 스택 (Stack) ===

       +------+
       |  50  |  ← TOP (push/pop)
       +------+
       |  40  |
       +------+
       |  30  |
       +------+
       |  20  |
       +------+
       |  10  |
       +------+
    LIFO (Last In, First Out)


=== 그래프 (Graph) ===

     (A)-------(B)
     / \         |
    /   \        |
  (C)   (D)     |
    \           |
     \         |
      (E)-----(F)

    정점(Vertex)과 간선(Edge)으로 구성


=== 트리 (Tree) ===

              (A)            ← 루트(Root)
             / | \
           /   |   \
        (B)   (C)   (D)     ← 레벨 1
        / \         / \
      (E) (F)    (G)  (H)   ← 레벨 2 (리프 노드)


=== 이진 탐색 트리 (Binary Search Tree) ===

              (50)
             /    \
          (30)    (70)
          /  \    /  \
       (20) (40)(60) (80)

    왼쪽 < 부모 < 오른쪽


=== 체이닝 (Chaining - 해시 테이블 충돌 해결) ===

  해시 테이블 (Hash Table)
  +--------+
  |  [0]   | → NULL
  +--------+
  |  [1]   | → [11|●] → [21|●] → [31|NULL]
  +--------+
  |  [2]   | → [12|●] → [22|NULL]
  +--------+
  |  [3]   | → [33|NULL]
  +--------+
  |  [4]   | → NULL
  +--------+

  같은 해시값을 가진 데이터를 연결 리스트로 연결
  예) 해시함수: key % 5
      11 % 5 = 1, 21 % 5 = 1, 31 % 5 = 1 → 버킷[1]에 체이닝
```

위와 같이 존재한다.

가장 기본적인 자료구조로 배열(array)이 존재한다.
배열은 같은 자료형을 가진 변수의 모임이다.
메모리에 순서대로 할당되므로 9장 3절에서 배운 캐시 히트가 일어날 확률이 매우 높다.
배열 안에 있는 변수 위치를 인덱스(index)로 나타내는데,
이 인덱스를 통해 변수에 매우 빠르게 접근한다.

상황에 따라 적절한 자료구조가 달라질 수 있으며,
데이터 검색은 빈번하게 일어나는데 새로운 데이터 삽입이 없다면 배열을 쓰는 게 가장 합리적이다.
합리적이란 즉 앞에서 배운 지역성과 캐시를 따져서 결정한다.
반면 데이터 검색에 비해 새로운 데이터 삽입이나 기존 데이터 삭제가 자주 일어나면
연결 리스트가 효율적이다.
이때 스택과 힙 세그먼트의 특징과 연계해보면 두 자료구조의 차이를 확실히 알 수 있다.

### 스택/힙 세그먼트와의 연계

이때 스택과 힙 세그먼트의 특징과 연계에 대한 이야기는 C와 C++ 기준으로 보면 차이가 명확하다.

```
[ 배열 - 스택 세그먼트에 생성 가능 ]

int arr[5] = {1, 2, 3, 4, 5};

스택 메모리:
+-----+-----+-----+-----+-----+
| 1   | 2   | 3   | 4   | 5   |  ← 연속된 공간, 함수 끝나면 자동 해제
+-----+-----+-----+-----+-----+
0x1000 0x1004 0x1008 0x100C 0x1010


[ 연결 리스트 - 힙 세그먼트에 생성 ]

Node* n1 = malloc(sizeof(Node));  // 힙
Node* n2 = malloc(sizeof(Node));  // 힙
Node* n3 = malloc(sizeof(Node));  // 힙

힙 메모리 (흩어져 있을 수 있음):
0x3000: [data|next] --+
                      |
0x7A00: [data|next] <-+  --+
                            |
0x5F00: [data|next] <------+
```

배열은 스택에 만들 수 있어서 → 연속 메모리 보장 → 지역성 좋음 → 캐시 히트 높음.
연결 리스트는 노드마다 malloc/new로 힙에 할당 → 노드들이 메모리 여기저기 흩어짐 → 지역성 나쁨 → 캐시 미스 가능성 높음.

이때 자바나 파이썬, C#의 경우 GC가 있는 언어에서는 배열도 힙에 만들어진다.

```
[ 힙에 만든 배열도 연속은 연속 ]

int* arr = malloc(sizeof(int) * 5);

힙이지만 여전히 연속:
0x5000 0x5004 0x5008 0x500C 0x5010
+-----+-----+-----+-----+-----+
| 1   | 2   | 3   | 4   | 5   |  ← 힙이어도 한 블록으로 연속 할당
+-----+-----+-----+-----+-----+


[ 연결 리스트는 힙에서 각각 따로 할당 ]

0x5000: [Node1]     ← malloc 1번째
0x8200: [Node2]     ← malloc 2번째 (멀리 떨어짐)
0x6100: [Node3]     ← malloc 3번째 (또 다른 곳)
```

이때 핵심 차이는 스택이냐 힙이냐가 아니라, 한 번에 연속된 블록으로 할당하느냐 vs 노드마다 개별 할당하느냐입니다.
교재가 "스택과 힙의 특징을 연계하라"고 한 건, C 기준으로 배열은 스택에 놓을 수 있다는 점을 강조한 것이고,
본질적으로는 연속 할당 vs 분산 할당의 차이가 캐시 성능 차이를 만든다고 이해하시면 된다.

### 자료구조를 공부하는 세 가지 관점

자료 구조를 공부할 때는 세 가지만 파악하면 된다.

1. 데이터를 어떻게 삽입(insert)하는가?
2. 데이터를 어떻게 검색(search)하는가?
3. 데이터를 어떻게 삭제(delete)하는가?

자료 구조별로 이 세 가지를 이해하고 구현하는 것이 목표이며,
이 책에서는 연결 리스트, 스택, 큐, 트리에 대해 공부하고 구현한다.
자료구조가 무엇이고 앞으로 어떻게 공부하는지에 대한 단서를 얻어보자.

## 2. 추상 자료형 (ADT)

출처: `computer_science/chapter/chapter11/chapter11.py`

자료 구조에는 추상 자료형이라는 개념이 있다.
흔히 ADT(Abstract Data Type)라고 부른다.
추상 자료형은 간단히 말해 자료 구조에서 삽입/탐색/삭제 등을 담당하는 함수들의 사용 설명서이다.

이름에 추상이 들어가는 이유는 추상 자료형은 인터페이스(함수의 이름, 인자, 반환형 등을 명시한 것)와 구현을 분리했기 때문이다.

리스트를 활용하여 추상 자료형을 이해해본다면
리스트에서 데이터를 삽입(insert)하는 append 함수를 보자.

```python
help(list.append)
# append(object) -> None -- append object to end
```

보면 함수 이름 append, 인자(object), 반환형(None)을 알 수 있다.
이 부분은 인터페이스이다.
이때 append는 어떻게 구현되었는지 알 수 없다.
알 필요가 없다.
알지 못해도 append() 함수를 이용하여 데이터를 삽입할 수 있기 때문에, 이러한 특징을 인터페이스와 구현이 분리되어 있다고 말한다.
이 두 가지를 분리하는 것을 즉 추상화라 부른다.

## 3. 연결 리스트

출처: `computer_science/chapter/chapter11/chapter11.py`, `computer_science/chapter/chapter11/chapter11-1.py`

연결 리스트는 데이터와 참조로 구성된 노드가 한 방향 혹은
양방향으로 쭉 이어진 자료구조이다.

노드란?
노드란 자료구조를 구현할 때 데이터를 담는 틀로,
단일 연결 리스트에서 사용할 노드는 데이터와 포인터를 통해 다음 노드를
가리키는 참조 구조로 이뤄져 있다.

```python
class Node:
    def __init__(self, data=None):
        # 노드는 데이터 부분과
        # 다음 노드를 가리키는 참조 부분을 가진다.
        self.__data = data
        self.__next = None
```

멤버 `__data`에는 데이터를 저장하고 멤버 `__next`는 다음 노드를 가리킨다.
두 멤버는 유심히 보면 `__`가 있는데 파이썬의 정보 은닉 기법이며
프로퍼티 기법을 통한 데이터 은닉화이다.

연결 리스트에는 여러 종류가 있는데
단일 연결 리스트의 노드에는 참조가 하나만 있다.
한 방향으로 참조하므로 단일 연결 리스트라 부른다.
이중 연결 리스트의 노드에는 다음 노드를 가리키는 참조와 이전 노드를 가리키는 참조가 있다.
그래서 이름이 이중 연결 리스트이다.

기본적으로 단일 연결 리스트의 첫 번째 데이터를 가리키는 head,
마지막 데이터를 가리키는 tail,
리스트에 저장된 데이터의 개수를 나타내는 d_size가 있다.

### 연결 리스트의 추상 자료형 (ADT)

구현하려면 함수의 사용법을 정의한 추상 자료형이 필요하다.
연결 리스트의 추상 자료형은 다음과 같다.

1. `S.append(data) -> None`
   데이터를 삽입하는 함수.
2. `S.search_target(target, start=0) -> (data, pos)`
   데이터를 검색하는 첫 번째 함수이다.
   데이터를 순회하면서 대상 데이터를 찾아 그 위치와 함께 반환한다.
   pos는 찾은 대상 데이터가 리스트에서 몇 번째인지 나타낸다.
   인덱스처럼 0부터 시작하지만
   pos는 인덱스와 달리 인덱싱처럼 바로 접근이 아닌, 그 데이터를 만나려면
   그만큼 순회해야 한다.
   찾는 데이터가 없으면 (None, None)을 반환한다.
   start는 시작 위치이다.
   시작 위치에서 단순히 순회를 통해 이동하고 이후 if문을 통해 탐색한다.
3. `S.search_pos(pos) -> data`
   데이터를 검색하는 두 번째 함수로, 인자로 위치를 전달하면
   연결 리스트에서 해당 위치에 있는 데이터를 반환한다.
   전달한 위치가 범위를 벗어나면 None을 반환한다.
   이 함수도 pos에 도달할 때까지 모든 데이터를 순회한다.
4. `S.remove(data) -> None`
   데이터를 삭제하는 함수이다.
   리스트에 대상 데이터가 있으면 첫 번째 데이터가 지워지면서 그 데이터를 반환하고,
   대상 데이터가 없으면 None을 반환한다.
5. `S.empty() -> bool`
   연결 리스트가 비었다면 참, 비어 있지 않다면 거짓을 반환한다.
6. `S.size() -> Integer`
   연결 리스트의 데이터 개수를 반환한다.

### 삽입 (append)

```python
def append(self, data):
    # 삽입할 노드를 만든다.
    new_node = Node(data)
    # 첫번째 경우
    # 리스트가 비어 있을 때
    if self.empty():
        self.head = new_node
        self.tail = new_node
        self.d_size += 1
    # 데이터가 한 개 이상 있을 때
    else:
        self.tail.next = new_node
        self.tail = new_node
        self.d_size += 1
```

저장하려는 데이터를 가진 노드를 생성한다.
연결 리스트가 비어 있다면 헤드와 테일이 새 노드를 가리킨다.
이때 사이즈를 증가시키고,
데이터가 있는 경우 새 노드를 테일을 가리키는 노드와 이어주고
테일을 새로운 노드로 옮긴다.

### 검색 (search_target / search_pos)

```python
def search_target(self, target, start=0):
    if self.empty():
        return None
    # 첫 노드를 가리킨다.
    pos = 0
    # 노드 순환 코드
    cur = self.head
    # pos가 탐색 시작 위치 start보다 클 때만
    # 대상 데이터와 현재 노드의 데이터를 비교
    if pos >= start and target == cur.data:
        return cur.data, pos

    while cur.next:
        pos += 1
        # 노드의 순회 코드
        # cur이 노드의 next를 통해 다음 노드로 이동
        cur = cur.next
        if pos >= start and target == cur.data:
            return cur.data, pos

    return None, None
```

cur을 head 위치로 이동시켜 순회를 시작한다.
다음 next를 통해 cur이 다음 노드를 참조한다.

```python
def search_pos(self, pos):
    # pos가 범위를 벗어나면 None을 반환
    if pos > self.size() - 1:
        return None
    cnt = 0
    cur = self.head
    if cnt == pos:
        return cur.data

    # cnt가 pos와 같아질 때 순회를 멈춘다.
    while cnt < pos:
        cur = cur.next
        cnt += 1

    return cur.data
```

### 삭제 (remove)

```python
def remove(self, target):
    if self.empty():
        return None

    # before는 current 노드의 이전 노드를 가리킨다.
    # 삭제할 때 요긴하게 쓰인다.
    bef = self.head
    cur = self.head

    # A. 삭제 노드가 첫번째 노드일 때
    if target == cur.data:
        # A-1. 데이터가 하나일 때
        if self.size() == 1:
            self.head = None
            self.tail = None
        # A-2. 데이터가 두 개 이상일 때
        else:
            self.head = self.head.next
        self.d_size -= 1
        return cur.data

    while cur.next:
        bef = cur
        cur = cur.next
        # B. 삭제 노드가 첫번째 노드가 아닐 때
        if target == cur.data:
            # B-1. 삭제 노드가 마지막 노드일 때
            if cur == self.tail:
                self.tail = bef
            # B-2. 일반적인 경우
            bef.next = cur.next
            self.d_size -= 1
            return cur.data

    return None
```

## 4. 스택

출처: `computer_science/chapter/chapter11/chapter11-2.py`

스택은 데이터를 차곡차곡 쌓아 올린 모습을 연상하게 한다.
보통 접시 쌓기에 비유하는데,
데이터를 추가할 때 맨 위에 추가하고 데이터를 꺼낼 때 맨 위에서 데이터를 꺼내는 모습 때문이며,
이와 같은 후입선출 방식을 LIFO(Last In, First Out)라 한다.

스택의 동작 방식:
스택이 동작할 때 삽입하는 동작을 push라 한다.
또한 데이터를 삭제하고 반환하는 것을 pop이라 한다.

스택의 추상 자료형을 먼저 보면

- `S.push -> None` — 데이터를 스택 맨 위에 추가한다.
- `S.pop -> data` — 스택의 맨 위에 있는 데이터를 삭제하면서 반환한다.
- `S.empty() -> bool` — 스택이 비었으면 참, 비어 있지 않다면 거짓을 반환한다.
- `S.peek() -> data` — 스택의 맨 위에 있는 데이터를 반환하되 삭제하지 않는다.

파이썬 리스트를 이용한 스택 구현:

```python
class Stack:
    def __init__(self):
        self.container = list()

    def push(self, data):
        self.container.append(data)

    def pop(self):
        return self.container.pop()

    def empty(self):
        if not self.container:
            return True
        else:
            return False

    def peek(self):
        return self.container[-1]
```

## 5. 큐

출처: `computer_science/chapter/chapter11/chapter11-3.py`

스택이 접시 쌓기라면 큐는 줄 서기.
큐는 제일 먼저 들어온 데이터가 가장 먼저 나간다.
가장 먼저 들어온 데이터가 가장 먼저 나가는 것을 FIFO(First In First Out) 선입선출이라 한다.
삽입은 인큐라 하고
꺼내는 것은 디큐라 한다.

큐의 기능 정의:

1. `Q.enqueue(data) -> None` — 큐의 마지막에 데이터를 추가한다.
2. `Q.dequeue() -> data` — 큐에서 가장 먼저 들어온 데이터를 삭제하면서 반환한다.
3. `Q.empty() -> bool` — 큐가 비어 있으면 참, 비어 있지 않으면 거짓을 반환한다.
4. `Q.peek() -> data` — 큐에서 가장 먼저 들어온 데이터를 반환하되 삭제하지는 않는다.

```python
class Queue:
    def __init__(self):
        self.container = list()

    def enqueue(self, data):
        self.container.append(data)

    def dequeue(self):
        return self.container.pop(0)

    def empty(self):
        if not self.container:
            return True
        else:
            return False

    def peek(self):
        return self.container[0]
```

## 6. 자료구조 선택 기준

출처: `computer_science/chapter/chapter11/chapter11-4.py`

자료구조는 어떻게 결정해야 될까?

배열은 데이터의 추가나 삭제보다 탐색이 잦을 때,
연결 리스트는 탐색보다는 데이터의 추가나 삭제가 빈번할 때 사용한다.
하지만 실제 프로그램을 개발할 때는 여러 가지 상황을 고려해 자료구조를 결정해야 한다.

실제 게임을 개발한다고 했을 때,
비행기 게임을 만든다고 했을 때 게임이 진행되면 특정 시점이나 상황일 때 적 비행기가
출현하고, 이때 한 장면에 나올 수 있는 적 비행기의 최대 개수는 100개를 넘을 수 없다면
한 장면에 출현한 적 비행기를 담을 자료구조는 어떤 게 좋을까?
적 비행기는 화면 아래로 이동하며 주인공 비행기에 미사일을 쏘고, 주인공 비행기가 쏜 미사일에 맞으면
터지면서 화면에서 사라진다.
수시로 화면에 등장하고 수시로 사라지는 적 비행기를 담는 데는 연결 리스트가 적당해 보이는데,
이때 수시로 나타났다가 사라지는 게 너무 많아 객체들이 생기고 사라진다.
객체를 만들었다가 지우는 건 리소스를 많이 먹기 때문에
이를 해결하기 위해 배열을 활용하여 객체 풀 기법을 사용한다.

→ 100대가 최대이기에 길이가 100인 배열을 준비하고, 게임이 시작될 때 적 비행기 객체를 100개 생성해 배열에 담아 놓고
시점이나 상황이 발생하면 배열에 담아둔 객체 중 일부를 화면에 등장시키고,
비행기가 주인공 미사일에 맞으면 터지는 효과만 보여주되 실제 화면에서만 사라지고 실제로는 소멸하지 않는다.
그런 방식으로 시작과 끝에 객체 생성·삭제가 일어나도록 설계하는 기법이다.
즉 이러한 여러 상황을 고려해 가장 알맞은 자료구조를 선택해야 프로그램 도중 맞닥뜨리는 문제들을 해결하고
성능 좋은 프로그램을 만들 수 있다.

## 7. 재귀 함수

출처: `computer_science/chapter/chapter12/chapter12.py`

재귀(recursion)는 반복 또는 되풀이를 의미한다.
프로그래밍에서 재귀 함수란 함수 정의 도중에 같은 이름의 함수가 나오는 경우이다.
다시 말해 함수를 호출하면 자기 자신을 호출하여 계속 호출한다.
흔히 재귀 함수를 설명할 때 팩토리얼을 예로 많이 든다.

팩토리얼:

1. `n! = (n - 1)! x n`
2. `n = 0 or 1`이면 `n! = 1`

```python
# 1번 성질을 이용한 재귀 함수
# def factorial(n):
#     return factorial(n-1) * n
```

위와 같이 설계하면 재귀 함수가 계속해서 자기 자신을 호출하기 때문에 스택 프레임이 계속 생성되고
스택 오버플로가 발생한다.
이러한 사태를 막으려면 탈출 조건이 필요하고, 탈출 조건이란 함수 호출을 멈추는 조건이다.

```python
def factorial(n):
    # 탈출 조건
    if n <= 1:
        return 1
    return factorial(n-1) * n
```

### 피보나치 수

피보나치 수는 0과 1부터 시작해서 다음 수가 앞의 두 수를 더한 값이 되는 수열입니다.
이때 재귀 함수를 만들 단서는 "다음 수가 앞의 두 수를 더한 값"
이라는 문장에서 얻을 수 있고, 탈출 조건은 정의를 보면 맨 처음 수가 0과 1이다.
이 부분을 탈출 조건으로 써보자.

```python
def fibonacci(n):
    if n == 1:
        return 0
    elif n == 2:
        return 1

    return fibonacci(n - 2) + fibonacci(n - 1)
```

호출 구조를 정리해보면

```
fibonacci(5)
├── fibonacci(3)
│   ├── fibonacci(1) → 0
│   └── fibonacci(2) → 1
│   = 0 + 1 = 1
└── fibonacci(4)
    ├── fibonacci(2) → 1
    └── fibonacci(3)
    │   ├── fibonacci(1) → 0
    │   └── fibonacci(2) → 1
    │   = 0 + 1 = 1
    = 1 + 1 = 2

결과: 1 + 2 = 3
```

## 8. 트리와 이진 트리

출처: `computer_science/chapter/chapter12/chapter12.py`

트리의 정확한 정의는 사이클이 없는 연결 그래프이다.

트리의 정의를 이해하려면 "그래프", "연결", "사이클" 이 세 가지 개념을
먼저 알아야 한다.

그래프는 노드(정점)와 그 노드들을 잇는 간선(엣지)의 집합이다.
예를 들어 A, B, C라는 노드가 있고 A-B, B-C라는 간선이 있으면
그게 그래프이다.

연결 그래프란 어떤 노드에서 출발하든 다른 모든 노드에 도달할 수 있는
그래프이다. 만약 A-B, C-D처럼 두 그룹이 끊어져 있으면 연결 그래프가 아니다.

사이클은 어떤 노드에서 출발해서 같은 간선을 다시 지나지 않고도 다시 출발점으로
돌아올 수 있는 경로를 말한다.
예를 들어, AB, BC, CA 간선이 있으면 ABCA로 돌아올 수 있으니 사이클이 존재한다.
그래서 트리 = 사이클이 없는 연결 그래프라는 정의는 이 두 조건을 만족시켜야 한다는 뜻이다.

```
사이클 있음 + 연결됨 → 그냥 그래프 (트리 아님)

    A --- B
    |   / |
    | /   |
    C --- D

사이클 없음 + 연결 안 됨 → 포레스트 (트리 아님)

    A - B    C - D    (두 개의 분리된 트리)

사이클 없음 + 연결됨 → 트리 ✓

        A
       / \
      B   C
     / \
    D   E
```

이 정의에서 자연스럽게 따라오는 성질이 존재하는데,
노드가 N개인 트리는 간선이 항상 N-1개이다.
간선이 하나라도 더 있으면 반드시 사이클이 생기며
하나라도 적으면 연결이 끊어지기 때문이다.
또한 임의의 두 노드 사이의 경로가 정확히 하나만 존재한다.
경로가 두 개 이상이면 그 두 경로가 사이클을 형성한다.

우리가 흔히 보는 루트가 있는 트리는 일반적인 트리에서
특정 노드 하나를 루트로 지정하고 방향성을 부여한 형태이다.

트리를 하면 제일 먼저 떠오르는 이진 트리 중심으로 감을 잡아보자.

### 이진 트리

이진 트리는 한 노드가 자식 노드를 두 개 이하만 갖는 트리이다.
이진 트리의 노드도 데이터 부분과 참조 부분으로 이루어져 있으며,
이때 참조는 두 개이다.
왼쪽 자식 노드를 가리키는 참조와 오른쪽 자식 노드를 가리키는 참조.

부모 노드와 자식 노드:
이진 트리를 구성하는 요소에는 크게 부모 노드(parent node)와
자식 노드(child node)가 있다.

```
        A
       / \
      B   C
A가 부모 노드
B, C가 자식 노드
```

루트 노드와 리프 노드:

```
            1          ← 루트 노드
          /   \
        2       3      ← 내부 노드 (인터널 노드, 엣지로 연결)
       / \     / \
      4   5   6   7    ← 4는 내부 노드
     /
    8                  ← 리프 노드: 8, 5, 6, 7
```

트리에서 최상위에 위치한 노드를 루트 노드라 한다.
루트 노드는 트리의 시작점으로,
노드와 노드 사이를 연결하는 선을 에지(edge) 혹은 링크(link)라고
부른다.
자식 노드가 하나라도 있는 노드를 인터널(internal, 내부) 노드,
자식 노드가 하나도 없는 노드를 리프(leaf) 노드 혹은 단말 노드라 부른다.

서브 트리는 상위 트리를 구성하는 한 요소로 그 자체로도 독립적인 트리이다.

트리에서는 루트 노드로부터의 깊이(depth)를 레벨이라고 부르고, 한 노드의 높이는 그 노드에서 가장 길게 뻗어 나간 리프 노드까지의
길이라 한다.

### 포화 이진 트리와 완전 이진 트리

이진 트리 중 포화 이진 트리(full binary tree)와 완전 이진 트리(complete binary tree)가
존재한다.
포화 이진 트리는 모든 레벨이 꽉 차 있는 트리.
완전 이진 트리는 트리의 노드가 위에서 아래로, 왼쪽에서 오른쪽으로 채워지는 트리이다.

포화 이진 트리(Full Binary Tree)는 모든 레벨이 빈틈없이 꽉 찬 트리이다.
모든 노드가 자식을 0개 또는 2개 가지고, 리프 노드가 전부 같은 레벨에 있다.

```
         1
       /   \
      2     3
     / \   / \
    4   5 6   7
```

높이가 h일 때 노드 수는 항상 2^(h+1) - 1개이다.
위 예시는 높이가 2이므로 2^3 - 1 = 7이다.

완전 이진 트리(Complete Binary Tree)는 마지막 레벨을 제외한
모든 레벨이 꽉 차 있고, 마지막 레벨은 왼쪽부터 순서대로 채워진 트리이다.

```
         1
       /   \
      2     3
     / \   /
    4   5 6
```

마지막 레벨에 7이 빠져 있지만 왼쪽부터 순서대로 채워져 있으므로 완전 이진 트리이다.
반면 아래처럼 중간이 비면 완전 이진 트리가 아니다.

```
         1
       /   \
      2     3
     / \     \
    4   5     7    ← 6이 빠지고 7만 있음, 왼쪽부터 순서대로가 아님
```

정리하면 포화 이진 트리는 완전 이진 트리의 특수한 경우이며,
포화 이진 트리는 반드시 완전 이진 트리지만,
완전 이진 트리가 반드시 포화 이진 트리인 것은 아니다.
완전 이진 트리는 배열로 표현하기 좋아서 힙(Heap) 자료구조의 기반이 되기도 한다.

## 9. 이진 트리 구현과 순회

출처: `computer_science/chapter/chapter12/chapter12-1.py`

트리 노드는 데이터와 왼쪽·오른쪽 자식 참조로 구성되며, property 기법으로 캡슐화가 가능하다.

```python
class TreeNode:
    def __init__(self):
        self.__data = None
        self.__left = None
        self.__right = None
```

이진 트리 클래스는 루트 노드를 가리키는 root 하나를 멤버로 가지며,
노드 생성(make_node)·데이터 설정(set_node_data)·서브 트리 연결(make_left_sub_tree / make_right_sub_tree) 메서드로 트리를 구성한다.

```python
class BinaryTree:
    def __init__(self):
        # 맴버는 루트 노드를 가리키는 root 하나입니다.
        self.root = None

    # 전위 순회로 트리를 순회
    # 인자(cur: 방문 노드, func: 데이터 처리 함수)
    def preorder_traverse(self, cur, func):
        # 탈출 조건
        # 방문한 노드가 빈 노드일 때
        if not cur:
            return
        # 먼저 방문 노드의 데이터를 인자로 함수 호출
        func(cur.data)
        # 왼쪽 서브 트리 순회
        self.preorder_traverse(cur.left, func)
        # 오른쪽 서브 트리 순회
        self.preorder_traverse(cur.right, func)

    # 중위 순회로 트리를 순회
    def inorder_traverse(self, cur, func):
        if not cur:
            return
        # 먼저 왼쪽 서브 트리를 순회
        self.inorder_traverse(cur.left, func)
        # 왼쪽 서브 트리를 모두 순회한 후
        # 방문 노드의 데이터를 인자로 함수 호출
        func(cur.data)
        # 오른쪽 서브 트리 순회
        self.inorder_traverse(cur.right, func)

    # 후위 순회로 트리를 순회
    def postorder_traverse(self, cur, func):
        if not cur:
            return
        # 왼쪽 서브 트리 순회
        self.postorder_traverse(cur.left, func)
        # 오른쪽 서브 트리 순회
        self.preorder_traverse(cur.right, func)
        # 왼쪽 서브 트리와 오른쪽 서브 트리를 모두 순회한 후
        # 마지막으로 방문 노드의 데이터를 인자로 함수 호출
        func(cur.data)
```

### 트리 순회

순회에는 총 3가지 순회가 있는데

1. 전위 순회: 노드 → 왼쪽 서브 트리 → 오른쪽 서브 트리
2. 중위 순회: 왼쪽 서브 트리 → 노드 → 오른쪽 서브 트리
3. 후위 순회: 왼쪽 서브 트리 → 오른쪽 서브 트리 → 노드

```
=== 트리 구조 ===
          (1)
         /   \
       (2)    (3)
      /  \   /  \
    (4) (5)(6) (7)


=== 1. 전위 순회 (Preorder) : [노드] → 왼쪽 → 오른쪽 ===

              (1) ①
             /   \
        ②  (2)    (3) ⑤
          /  \   /  \
     ③ (4) (5)(6) (7)
              ④  ⑥   ⑦

순서: 1 → 2 → 4 → 5 → 3 → 6 → 7


=== 2. 중위 순회 (Inorder) : 왼쪽 → [노드] → 오른쪽 ===

              (1) ④
             /   \
        ②  (2)    (3) ⑥
          /  \   /  \
     ① (4) (5)(6) (7)
              ③  ⑤   ⑦

순서: 4 → 2 → 5 → 1 → 6 → 3 → 7


=== 3. 후위 순회 (Postorder) : 왼쪽 → 오른쪽 → [노드] ===

              (1) ⑦
             /   \
        ③  (2)    (3) ⑥
          /  \   /  \
     ① (4) (5)(6) (7)
              ②  ④   ⑤

순서: 4 → 5 → 2 → 6 → 7 → 3 → 1


=== 요약 ===

전위: [노드] 왼 오  → 1, 2, 4, 5, 3, 6, 7  (루트부터)
중위:  왼 [노드] 오  → 4, 2, 5, 1, 6, 3, 7  (왼쪽 끝부터)
후위:  왼  오 [노드] → 4, 5, 2, 6, 7, 3, 1  (리프부터)
```

## 10. 이진 탐색 트리

출처: `computer_science/chapter/chapter13/chapter13.py`

이진 탐색 트리는 두 가지 중요한 특징이 존재하는데,
첫 번째, 어떤 특정 노드를 선택했을 때 그 노드를 기준으로 왼쪽 서브 트리에 존재하는
노드의 모든 데이터는 기준 노드의 값보다 작고, 오른쪽 서브 트리에 있는 노드의 모든 데이터는
기준 노드의 값보다 크다는 것이다.

예시: BST에 [8, 3, 10, 1, 6, 14, 4, 7, 13] 삽입

```
                    8
                 /     \
               3        10
              / \          \
            1    6         14
                / \        /
               4   7     13

        ✅ 왼쪽 서브트리 (3, 1, 6, 4, 7) → 모두 8보다 작음
        ✅ 오른쪽 서브트리 (10, 14, 13)   → 모두 8보다 큼

        노드 3 기준으로도:
          - 왼쪽(1) < 3 ✅
          - 오른쪽(6, 4, 7) > 3 ✅
```

위와 같이 루트 노드의 왼쪽 자식 노드가 기준 노드일 때,
기준 노드의 왼쪽 서브 트리의 모든 데이터는 기준 노드의 데이터인 3보다 작다.
오른쪽 서브 트리의 모든 데이터는 3보다 크다.
기준 노드가 루트 노드의 오른쪽 자식 노드일 때도 같은 조건이 성립된다.
즉 특정 노드를 기준으로 그 노드의 서브 트리도 모두 이진 탐색 트리인 것도 알 수 있다.
이진 탐색 트리의 두 번째 특징은 이진 탐색 트리는 중복 데이터를 가질 수 없다.

결국 이진 탐색 트리는 이진 트리의 일종(IS-A)이므로 앞 장에서 만든 트리 클래스를 상속해야 되지만
상속하지 않고 구현해보자.

### 이진 탐색 트리의 추상 자료형

1. `BST.insert(data) -> None`
   이진 탐색 트리에 데이터를 삽입한다.
2. `BST.search(target) -> node`
   이진 탐색 트리에서 대상 데이터를 가진 노드를 반환한다. 데이터가 없으면 None을 반환한다.
3. `BST.remove(target) -> node`
   이진 탐색 트리에 대상 데이터가 있다면 데이터를 가진 노드를 삭제하면서 반환한다.
   데이터가 없으면 None을 반환한다.
4. `BST.insert_node(node) -> None`
   데이터가 아니라 노드를 삽입한다. remove에서 반환받은 노드의 데이터를 수정한 후 다시 삽입할 때
   사용한다.

BST에서 insert와 search 메서드는 구현하기 어렵지 않지만, remove 메서드는 구현하기 까다롭다.
이유는 삭제하는 노드가 리프인지 자식 노드가 있는지 알아야 되기 때문이다.

### 삽입 (insert)

```python
def insert(self, data):
    # 삽입할 노드 생성 및 데이터 설정
    new_node = TreeNode()
    new_node.data = data

    cur = self.root
    # 루트 노드가 없을 때
    if cur == None:
        self.root = new_node
        return

    # 삽입할 노드의 위치를 찾아 삽입
    while True:
        # parent는 현재 순회중인 노드의 부모 노드를 가리킴
        parent = cur
        # 삽입할 데이터가 현재 노드 데이터보다 작을 때
        if data < cur.data:
            cur = cur.left
            # 왼쪽 서브 트리가 None이면 새 노드를 위치시킨다.
            if not cur:
                parent.left = new_node
                return
        # 삽입할 데이터가 현재 노드보다 클 경우
        else:
            cur = cur.right
            # 오른쪽 서브 트리가 None이면 새 노드를 위치시킨다.
            if not cur:
                parent.right = new_node
                return
```

### 검색 (search)

```python
def search(self, target):
    cur = self.root

    while cur:
        # 대상 데이터를 찾으면 노드를 반환
        if target == cur.data:
            return cur
        # 대상 데이터가 노드 데이터보다 작으면
        # 왼쪽 자식 노드로 이동
        elif target < cur.data:
            cur = cur.left
        # 대상 데이터가 노드 데이터보다 크면
        # 오른쪽 자식 노드로 이동
        elif target > cur.data:
            cur = cur.right

    # while문을 빠져나온 경우 대상 데이터가 트리 안에 없다.
    return cur
```

### 삭제 (remove)

remove는 기본적으로 3가지 형태의 삭제 형태가 존재하는데

1. 삭제 노드가 리프 노드일 때
2. 삭제 노드의 자식 노드가 하나일 때
3. 삭제 노드의 자식 노드가 두 개일 때

```python
def remove(self, target):
    # 루트 노드의 변경 가능성이 있으므로
    # 루트를 업데이트해야 된다.
    self.root, removed_node = self.__remove_recursion(self.root, target)

    # 삭제된 노드의 자식 노드를 None으로 만든다.
    removed_node.left = removed_node.right = None

    return removed_node

def __remove_recursion(self, cur, target):
    # 탈출 조건 1
    # 대상 데이터가 트리 안에 없을 때
    if cur == None:
        return None, None
    # 대상 데이터가 노드 데이터보다 작으면
    # 노드의 왼쪽 자식에서 대상 데이터를 가진 노드를 지운다(재귀 함수 호출)
    elif target < cur.data:
        cur.left, rem_node = self.__remove_recursion(cur.left, target)
    # 대상 데이터가 노드 데이터보다 크면
    # 노드의 오른쪽 자식에서 대상 데이터를 가진 노드를 지운다(재귀 함수 호출)
    elif target > cur.data:
        cur.right, rem_node = self.__remove_recursion(cur.right, target)
    # 탈출 조건 2
    # target == cur.data
    else:
        # 1. 리프 노드일 때
        if not cur.left and not cur.right:
            rem_node = cur
            cur = None
        # 2-1. 자식 노드가 하나일 때: 왼쪽 자식이 있을 때
        elif not cur.right:
            rem_node = cur
            cur = cur.left
        # 2-2. 자식 노드가 하나일 때: 오른쪽 자식이 있을 때
        elif not cur.left:
            rem_node = cur
            cur = cur.right
        # 3. 자식 노드가 두개일 때
        else:
            # 4. 대체 노드를 찾는다.
            replace = cur.left
            while replace.right:
                replace = replace.right
            # 5. 삭제 노드와 대체 노드의 값을 교환한다.
            cur.data, replace.data = replace.data, cur.data
            cur.left, rem_node = self.__remove_recursion(cur.left, replace.data)

    # 삭제 노드가 루트 노드일 경우
    # 루트가 변경될 수 있기 때문에 삭제 후 현재 루트를 반환
    return cur, rem_node
```

### 노드 재삽입 (insert_node)

인자가 데이터가 아닌 노드다.
insert() 메서드에서 노드 생성 코드만 빼면
코드 흐름은 완전히 같다.
노드 생성에 따른 부담을 덜 수 있다.

```python
def insert_node(self, node):
    # 노드 생성 코드 없음
    cur = self.root

    # insert() 메서드와 다른 점: new_node -> node
    if cur == None:
        self.root = node
        return
    while True:
        parent = cur
        # insert() 메서드와 다른 점: data -> node.data
        if node.data < cur.data:
            cur = cur.left
            if not cur:
                parent.left = node
                return
        else:
            cur = cur.right
            if not cur:
                parent.right = node
                return
```
