# data-structure/35-allocator — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Allocator (`src/main/java/com/datastructure/allocator/Allocator.java`)

- `int FAIL = -1` (상수)
- `int allocate(int size)`
- `void free(int address)`
- `int capacity()`
- `int usedBytes()`
- `int freeBytes()`
- `int largestFreeBlock()`
- `int freeBlockCount()`
- `int wastedBytes()`

## 구현 — BumpAllocator (`src/main/java/com/datastructure/allocator/BumpAllocator.java`)

### 구조

```
BumpAllocator (capacity = 100)   -   상태가 int 네 개뿐이다

  capacity   전체 크기
  next       다음에 떼어줄 위치. 이 포인터 하나가 구조의 전부다
  handedOut  지금까지 떼어준 총량 (돌려받은 것을 빼지 않는다)
  freeCalls  free 가 불린 횟수 = 돌려주려 했지만 안 돌아간 횟수

  자유 블록 목록도, 합치기도, 고르는 규칙도 없다.

      0                    next                                        100
      +---------------------+------------------------------------------+
      |     떼어준 영역     |             아직 안 쓴 영역              |
      +---------------------+------------------------------------------+
                             ^ 남은 자리는 언제나 뒤쪽 한 덩어리다
                               largestFreeBlock() == freeBytes() == capacity - next
                               freeBlockCount() 는 0 아니면 1
                               "단편화가 아예 없다" 는 말이 이 뜻이다
```

### 동작 — 할당/리셋

```
allocate(size) :  지금 위치를 주고 그만큼 앞으로 민다
    next + size > capacity  ->  FAIL(-1) 을 돌려준다 (예외를 던지지 않는다)
    아니면  address = next ;  next += size ;  handedOut += size

  그림은 capacity 100 을 44 칸으로 그린 것이다.

  [1] before   next = 0
       0                                          100
       +--------------------------------------------+
       |                                            |
       +--------------------------------------------+
       ^next

  [2] allocate(30) -> 0        next = 30
       0            30                             100
       +-------------+------------------------------+
       |   A (30)    |                              |
       +-------------+------------------------------+
                     ^next

  [3] allocate(20) -> 30       next = 50
       0            30      50                      100
       +-------------+--------+---------------------+
       |   A (30)    | B (20) |                     |
       +-------------+--------+---------------------+
                              ^next

free(address) :  아무것도 안 한다. freeCalls++ 만 한다
    주소가 범위 밖이면(address < 0 또는 address >= next) 예외를 던진다
    회수는 안 하지만 던지지도 않는다 - 던지면 다른 할당자와 바꿔 끼울 수 없다.
    계약은 지키되 회수를 안 하는 것이 이 설계의 정직한 표현이다.

  free(0) 을 부른 뒤에도
       +-------------+--------+---------------------+
       |   A (30)    | B (20) |                     |
       +-------------+--------+---------------------+
       ^ 비었지만 다시 못 쓴다  ^next 는 그대로 50. A 의 30 바이트는 돌아오지 않는다
                               usedBytes() 도 그대로 50 (handedOut 을 깎지 않는다)
                               ignoredFrees() = 1 로 낭비량만 세어둔다

reset() :  전부 버리고 처음으로. 이 할당자가 회수하는 유일한 방법이다
       +--------------------------------------------+
       |                                            |   next = 0
       +--------------------------------------------+   handedOut = 0, freeCalls = 0
       ^next = 0

비용: allocate O(1), free O(1), reset O(1). 훑을 목록도 비교도 없다.
      수명이 다 같으면 관리할 것이 없다. 관리 비용은 수명이 제각각일 때 생긴다.
```

### 필드
- `capacity` — 역할:
- `next` — 역할:
- `handedOut` — 역할:
- `freeCalls` — 역할:

### `BumpAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int allocate(int size)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void free(int address)`
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int usedBytes()` / `int freeBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int largestFreeBlock()` / `int freeBlockCount()` / `int wastedBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int ignoredFrees()`
- 하는 일:
- 논리:
- 비용(왜):

### `void reset()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — FreeListAllocator (`src/main/java/com/datastructure/allocator/FreeListAllocator.java`)

### 구조

```
capacity = 100, 그림은 1 칸 = 2 바이트.  A(30) 과 C(10) 이 나가 있는 상태

      0               30         50    60                   100
      +---------------+----------+-----+--------------------+
      |    A (30)     | 자유 20  |C 10 |     자유 40        |
      +---------------+----------+-----+--------------------+
       할당됨            자유       할당됨      자유

  free : ArrayList<Block>   -  자유 블록만 담는다. 주소 오름차순으로 유지한다
         index 0 -> Block{ start=30, size=20 }   end() = 50
         index 1 -> Block{ start=60, size=40 }   end() = 100

  Block 이 담는 것은 start 와 size 둘뿐이다
      end() = start + size 는 계산해서 쓴다
      "자유 여부" 플래그가 없다 - 이 목록에 있으면 자유다
      "다음 포인터" 도 없다 - 연결 리스트가 아니라 ArrayList 이고,
                              인덱스 순서가 곧 주소 순서다

  allocated : HashMap<주소, 크기>       free(주소) 가 얼마를 돌려받아야 하는지 알아야 한다
         0  -> 30   (A)
         50 -> 10   (C)

  scanned : 자리를 고르느라 들여다본 자유 블록의 수. 전략별 비용을 재는 자다

왜 주소순인가
    인접한 자유 블록을 합치려면 이웃이 옆칸에 있어야 한다.
    크기순으로 들면 고르기는 빨라지지만 합치기가 불가능해진다.
    무엇을 정렬해 두느냐가 무엇을 할 수 있는지를 정한다.
```

### 동작 — 할당(분할)

```
allocate(16) :  맞는 자유 블록을 골라 앞부분을 떼어주고 나머지를 자유 블록으로 남긴다
                (어느 블록을 고르는지는 하위 클래스의 choose 가 정한다)

before   free = [ {30,20}, {60,40} ]
      0               30         50    60                   100
      +---------------+----------+-----+--------------------+
      |    A (30)     | 자유 20  |C 10 |     자유 40        |
      +---------------+----------+-----+--------------------+
                       ^ 이 블록을 골랐다

after    free = [ {46,4}, {60,40} ]      돌려준 주소 = 30
      0               30      46 50    60                   100
      +---------------+--------+--+-----+-------------------+
      |    A (30)     | 새 16  |  |C 10 |    자유 40        |
      +---------------+--------+--+-----+-------------------+
                       ^address = block.start
                                ^ 남은 4 바이트가 그대로 자유 블록으로 남는다
      block.start += size ;  block.size -= size ;   목록에서 빼지는 않는다
      allocated.put(address, size)                  돌려받을 양을 적어둔다

딱 맞는 경우 (자유 20 에 allocate(20))
      free 에서 그 블록을 통째로 remove 한다.
      0 바이트짜리 자유 블록을 남기면 목록이 쓸모없는 항목으로 불어나고
      freeBlockCount() 가 거짓말을 한다.

맞는 것이 없으면 choose 가 -1 을 주고 allocate 는 FAIL(-1) 을 돌려준다.
요청한 만큼만 떼어주므로 내부 낭비가 없다 -> wastedBytes() 는 늘 0.
그 대신 외부 단편화를 짊어진다.

비용: choose 가 목록을 훑는 O(F) + 자르기 O(1).   F = 자유 블록 수
```

### 동작 — 해제(병합 coalescing)

```
free(50) :  주소 순서에 맞는 자리에 꽂고, 양옆이 붙어 있으면 합친다

[0] 꽂기        free 를 앞에서부터 훑어 start 가 50 보다 작은 동안 i++  ->  i = 1 에 삽입
                free = [ {30,20}, {50,10}, {60,40} ]
      0               30         50    60                   100
      +---------------+----------+-----+--------------------+
      |    A (30)     | 자유 20  |빈 10|     자유 40        |
      +---------------+----------+-----+--------------------+
                                  ^ 방금 돌려받은 자리. 아직 셋이 따로 논다

[1] 오른쪽부터 합친다   free[1].end() == free[2].start  (50+10 == 60)
                        free[1].size += 40 ;  free.remove(2)
                free = [ {30,20}, {50,50} ]
      +---------------+----------+--------------------------+
      |    A (30)     | 자유 20  |        자유 50           |
      +---------------+----------+--------------------------+

[2] 그 다음 왼쪽      free[0].end() == free[1].start  (30+20 == 50)
                      free[0].size += 50 ;  free.remove(1)
                free = [ {30,70} ]
      +---------------+---------------------------------+
      |    A (30)     |           자유 70               |
      +---------------+---------------------------------+

왜 오른쪽부터인가
    왼쪽을 먼저 지우면 i 가 한 칸 밀려서 보정해야 한다.
    보정을 빼먹으면 오른쪽 이웃을 엉뚱한 자리에서 찾아 못 합친다. 취향이 아니라 이 이유다.
한쪽만 보면
    오른쪽만 보면 앞에서 돌려받은 자리와 안 합쳐지고, 왼쪽만 보면 그 반대다.
    어느 쪽이든 반쪽만 합쳐져서 천천히 부서진다.

합치지 않으면 (같은 상황)
      free = [ {30,20}, {50,10}, {60,40} ]   freeBytes() = 70 인데 largestFreeBlock() = 40
      allocate(50) 이 FAIL 한다. 예외도 안 나고 계약 테스트도 다 통과한다.
      남은 공간을 세는 자와 가장 큰 덩어리를 재는 자를 나란히 놓아야만 드러난다.

비용: 꽂을 자리를 찾느라 O(F), 합치기는 양옆 두 번 보는 O(1).
```

### 동작 — 단편화

```
외부 단편화 : 총 자유 공간은 충분한데 연속된 자리가 없어서 실패한다

      0     10    20    30    40    50                            100
      +------+------+------+------+------+------------------------------+
      |자유10| 사용 |자유10| 사용 |자유10|             사용             |
      +------+------+------+------+------+------------------------------+

      freeBytes()        = 30      <- 세어보면 30 바이트가 비어 있다
      largestFreeBlock() = 10      <- 그런데 한 덩어리로는 10 바이트뿐이다
      allocate(20)       = FAIL

      극단으로 가면 : 8 바이트짜리 자유 블록 100 개 = 800 바이트가 비어 있는데
                      9 바이트 요청이 실패한다.

  이 실패는 조용하다. 예외도 안 나고 usedBytes() / freeBytes() 도 멀쩡하다.
  freeBytes() 와 largestFreeBlock() 을 나란히 놓고 봐야 보인다.
  freeBlockCount() 가 계속 늘어나는 것도 같은 신호다.

  이 방식은 요청한 만큼만 떼어주므로 내부 낭비가 0 이다 (wastedBytes() == 0).
  외부 단편화가 그 대가다. BuddyAllocator 는 정확히 반대쪽을 고른다.
```

### 필드
- `capacity` — 역할:
- `free` — 역할:
- `allocated` — 역할:
- `scanned` — 역할:
- `Block.start` / `Block.size` / `Block.end()` — 역할:

### `FreeListAllocator(int capacity)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `abstract int choose(List<Block> blocks, int size)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `int allocate(int size)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void free(int address)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void insertAndCoalesce(Block block)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int usedBytes()` / `int freeBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int largestFreeBlock()` / `int freeBlockCount()` / `int wastedBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `long scanned()` / `void countScan(long n)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> freeBlocks()`
- 하는 일:
- 논리:
- 비용(왜):

### `static void requireSize(int size)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — FirstFitAllocator (`src/main/java/com/datastructure/allocator/FirstFitAllocator.java`)

### 동작 — 자리 고르기

```
세 전략은 choose 만 다르다. 같은 초기 상태에 allocate(10) 을 걸어 차이만 본다.

      0         20       40    52       70              100
      +----------+----------+------+---------+---------------+
      | 자유 20  |  A (20)  |자유12| B (18)  |    자유 30    |
      +----------+----------+------+---------+---------------+
  free = [ {0,20},        {40,12},       {70,30} ]
  index      0               1              2

first fit : 앞에서부터 보다가 처음으로 size 이상인 것을 만나면 즉시 멈춘다

  index 0 : 20 >= 10  ->  여기로 결정. index 1, 2 는 보지도 않는다
  scanned += 1                                     <- 셋 중 제일 적게 훑는다

  after     +-----+-----+----------+------+---------+---------------+
            |새10 |빈 10|  A (20)  |자유12| B (18)  |    자유 30    |
            +-----+-----+----------+------+---------+---------------+
            ^address = 0           free = [ {10,10}, {40,12}, {70,30} ]

단편화 경향 : 늘 앞에서부터 떼어가므로 앞쪽에 작은 조각이 쌓이고,
              그 조각들을 매번 다시 훑게 된다.
              실제 구현들이 "지난번에 멈춘 자리부터" 로 고치는 이유다 (next fit).
```

### 필드
- 없음 — `FreeListAllocator` 의 상태를 그대로 쓴다.

### `FirstFitAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int choose(List<Block> blocks, int size)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — BestFitAllocator (`src/main/java/com/datastructure/allocator/BestFitAllocator.java`)

### 동작 — 자리 고르기

```
세 전략은 choose 만 다르다. 같은 초기 상태에 allocate(10) 을 걸어 차이만 본다.

      0         20       40    52       70              100
      +----------+----------+------+---------+---------------+
      | 자유 20  |  A (20)  |자유12| B (18)  |    자유 30    |
      +----------+----------+------+---------+---------------+
  free = [ {0,20},        {40,12},       {70,30} ]
  index      0               1              2

best fit : 맞는 것 중 남는 조각이 가장 작은 것. 제일 작은 것을 찾으려면 전부 봐야 한다

  index 0 : 20 >= 10   후보 (남는 10)
  index 1 : 12 >= 10   더 작다 -> 후보 교체 (남는 2)
  index 2 : 30 >= 10   더 크다 -> 그대로
  scanned += 3                                     <- 만나도 안 멈춘다

  after     +----------+----------+-----+-+---------+---------------+
            | 자유 20  |  A (20)  |새10 | | B (18)  |    자유 30    |
            +----------+----------+-----+-+---------+---------------+
                                   ^address = 40
                                         ^ 2 바이트만 남았다 (한 칸도 안 되는 자투리)
                        free = [ {0,20}, {50,2}, {70,30} ]

단편화 경향 : 큰 자리를 아껴두자는 생각이고, 그럴듯한 만큼만 맞다.
              쓸모없이 작은 조각을 만든다. 남은 2 바이트는 앞으로 거의 아무 요청도 못 받는데
              목록에는 계속 남아 훑는 비용만 늘린다.
```

### 필드
- 없음 — `FreeListAllocator` 의 상태를 그대로 쓴다.

### `BestFitAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int choose(List<Block> blocks, int size)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — WorstFitAllocator (`src/main/java/com/datastructure/allocator/WorstFitAllocator.java`)

### 동작 — 자리 고르기

```
세 전략은 choose 만 다르다. 같은 초기 상태에 allocate(10) 을 걸어 차이만 본다.

      0         20       40    52       70              100
      +----------+----------+------+---------+---------------+
      | 자유 20  |  A (20)  |자유12| B (18)  |    자유 30    |
      +----------+----------+------+---------+---------------+
  free = [ {0,20},        {40,12},       {70,30} ]
  index      0               1              2

worst fit : 맞는 것 중 가장 큰 것. 이것도 전부 봐야 한다

  index 0 : 20 >= 10   후보
  index 1 : 12 >= 10   더 작다 -> 그대로
  index 2 : 30 >= 10   더 크다 -> 후보 교체
  scanned += 3

  after     +----------+----------+------+---------+-----+----------+
            | 자유 20  |  A (20)  |자유12| B (18)  |새10 | 자유 20  |
            +----------+----------+------+---------+-----+----------+
                                                    ^address = 70
                        free = [ {0,20}, {40,12}, {80,20} ]

단편화 경향 : 남는 조각을 크게 만들어 다음 요청도 받게 하자는 생각이다. 이것도 그럴듯하다.
              그런데 큰 자리를 제일 먼저 깎아먹는다. 큰 요청이 나중에 오면 받을 자리가 없다.
              셋 중 대체로 제일 나쁘다.

셋 다 "그럴듯한 이유"가 있는데 결과가 갈린다. 재기 전에는 어느 쪽이 맞는지 알 수 없다.
```

### 필드
- 없음 — `FreeListAllocator` 의 상태를 그대로 쓴다.

### `WorstFitAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int choose(List<Block> blocks, int size)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — BuddyAllocator (`src/main/java/com/datastructure/allocator/BuddyAllocator.java`)

### 구조

```
BuddyAllocator (capacity = 64 = 2^6)
    levels = Integer.numberOfTrailingZeros(64) = 6
    capacity 가 2의 거듭제곱이 아니면 생성자가 던진다. 아니면 짝 계산이 성립하지 않는다.

  freeByLevel : List<TreeSet<Integer>>    지수 -> 그 크기의 자유 블록 "주소" 집합
                크기별로 층을 나눠 들고 있다. TreeSet 이라 오름차순 = 답이 하나로 정해진다

    지수 6 (크기 64) : { 0 }      <- 처음에는 통짜 하나
    지수 5 (크기 32) : { }
    지수 4 (크기 16) : { }
    지수 3 (크기  8) : { }
    지수 2 (크기  4) : { }
    지수 1 (크기  2) : { }
    지수 0 (크기  1) : { }

  allocated : HashMap<주소, int[]{ 떼어준 크기, 요청한 크기 }>
              둘의 차이가 내부 단편화다 -> wastedBytes() 가 그 합을 낸다
  splits / merges : 쪼갠 횟수 / 합친 횟수

  자유 블록 목록 방식과 달리 이웃을 찾으려고 목록을 훑지 않는다.
  크기가 2의 거듭제곱이고 주소가 그 배수라서, 짝의 주소를 계산으로 구할 수 있다.
```

### 동작 — 분할

```
allocate(10) :  levelFor(10) = 4    (10 을 담는 가장 작은 2의 거듭제곱은 16 = 2^4)

  지수 4 부터 위로 올라가며 자유 블록이 있는 층을 찾는다
      지수 4 비었다 -> 지수 5 비었다 -> 지수 6 에 { 0 } 이 있다 (found = 6)
  거기서부터 필요한 층까지 반씩 쪼개 내려온다. 뒤쪽 반을 내놓고 앞쪽 반을 계속 쪼갠다.

  지수 6   [0 ................................ 64)        pollFirst() -> address = 0
             |
             |  쪼갠다 : freeByLevel[5].add(0 + 32)       splits++
             v
  지수 5   [0 ............ 32) | [32 ........... 64)  <- 자유
             |
             |  쪼갠다 : freeByLevel[4].add(0 + 16)       splits++
             v
  지수 4   [0 .... 16) | [16 .... 32)  <- 자유
             |
             v  found == level 이므로 멈춘다
           [0..16) 을 떼어준다.   address = 0

  after   지수 6 : { }        allocated : 0 -> { 떼어준 16, 요청 10 }
          지수 5 : { 32 }     splits = 2
          지수 4 : { 16 }     freeBlockCount() = 2,  largestFreeBlock() = 32

  내부 단편화 : 요청 10 에 16 을 준다 -> 6 바이트가 쓰이지도 돌려주지도 못한 채 갇힌다.
                요청 40 이면 64 를 준다 -> 24 바이트가 갇힌다.
                자유 블록 목록 방식에는 없던 낭비다 (그쪽은 wastedBytes() 가 늘 0).
                그 대신 외부 단편화가 크게 줄어든다. 요청 크기의 분포가 어느 쪽이 나은지 정한다.

  맞는 층도 그 위도 전부 비었으면 FAIL(-1).
비용: 층을 훑고 쪼개는 것이므로 O(log capacity).
```

### 동작 — 병합

```
free(0) :  떼어준 크기 16 에서 지수를 되찾는다 (numberOfTrailingZeros(16) = 4)

  짝의 주소 = 주소 XOR 블록 크기        코드로는  buddy = address ^ (1 << level)
      크기가 2의 거듭제곱이고 주소가 그 배수라서 비트 하나만 뒤집으면 짝이 된다.
      이웃을 찾으려고 목록을 훑을 필요가 없다 -> 합치기가 O(1)

  지수 4   [0 .... 16) 돌려받음 + [16 .... 32) 자유
             짝 = 0 XOR 16 = 16  ->  지수 4 에 있다 -> remove 성공 -> 합친다 (merges++)
             address = min(0, 16) = 0        (합친 자리의 시작은 둘 중 앞쪽이다)
             |
             v
  지수 5   [0 ............ 32) + [32 ........... 64) 자유
             짝 = 0 XOR 32 = 32  ->  지수 5 에 있다 -> remove 성공 -> 합친다 (merges++)
             |
             v
  지수 6   [0 ................................ 64)     통짜로 돌아왔다
             level == levels 라 더 못 올라간다 -> freeByLevel[6].add(0) 하고 끝

  after   지수 6 : { 0 }   나머지 층 전부 비었다   merges = 2

  짝이 자유 목록에 없으면 remove 가 false -> 거기서 멈추고 그 층에 그대로 넣는다.

  붙어 있는데 못 합치는 자리가 있다
      [16..32) 과 [32..48) 은 주소가 맞닿아 있지만 서로의 짝이 아니다
          16 XOR 16 = 0     -> [16..32) 의 짝은 [0..16)
          32 XOR 16 = 48    -> [32..48) 의 짝은 [48..64)
      그래서 둘을 32 짜리 하나로 못 만든다. 이 제약이 O(1) 합치기의 값이다.
      (자유 블록 목록은 붙어 있기만 하면 합쳤다. 대신 이웃을 찾느라 목록을 훑었다.)

비용: 합쳐 올라가는 것이 최대 levels 번이므로 O(log capacity).
```

### 필드
- `capacity` — 역할:
- `levels` — 역할:
- `freeByLevel` — 역할:
- `allocated` — 역할:
- `splits` — 역할:
- `merges` — 역할:

### `BuddyAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int allocate(int size)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void free(int address)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int levelFor(int size)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int usedBytes()` / `int freeBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int largestFreeBlock()` / `int freeBlockCount()` / `int wastedBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `long splits()` / `long merges()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Integer> freeCountsByLevel()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BumpAllocator | | | |
| FirstFitAllocator | | | |
| BestFitAllocator | | | |
| WorstFitAllocator | | | |
| BuddyAllocator | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/35-allocator/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/35-allocator/src/main/java/com/datastructure/allocator/`
- 테스트: `/home/jun/project/myway/data-structure/35-allocator/src/test/java/com/datastructure/allocator/`
- 정답 구현: `/home/jun/project/myway/data-structure/35-allocator/impl/`
