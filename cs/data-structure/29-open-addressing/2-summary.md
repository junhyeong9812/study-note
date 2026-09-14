# data-structure/29-open-addressing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 지정 좌석 주차장.** 차(키)마다 번호판으로 계산한 지정 자리(홈)가 있다.
내 자리가 비어 있으면 거기 대면 끝. 차 있으면 **정해진 규칙대로 다음 자리를 찾아간다**.
찾을 때도 같은 규칙으로 걸으면 반드시 만난다 — 넣은 길과 찾는 길이 같아야 한다는 것이 전부의 핵심이다.
  - *해시(hash)*: 키를 숫자로 바꿔 "지정 자리 번호"를 만드는 계산.

```text
  D 를 넣는다. D 의 지정 자리(홈) = 1번 칸
   idx     0     1     2     3     4
        +-----+-----+-----+-----+-----+
        |     |  A  |  B  |  D  |     |
        +-----+-----+-----+-----+-----+
                 ^     ^     ^
               차있다 차있다  비었다 -> 여기!
```

이 문서의 다섯 구현이 **똑같은 구조다** — 다른 것은 "다음 자리를 찾는 규칙" 하나뿐이다:
옆칸으로 한 칸씩(선형) / 점점 멀리 건너뛰기(이차) / 차마다 다른 보폭(이중 해싱) / 멀리서 온 차에게 자리 양보(로빈후드) / 자리 둘만 정해 두고 뺏기(쿠쿠).
실무의 해시맵이 바로 이것이다 — 파이썬 dict 와 러스트 HashMap(로빈후드 계열)이 오픈 어드레싱을 쓴다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — ProbeMap (`src/main/java/com/datastructure/openaddr/ProbeMap.java`)

- `V put(K key, V value)`
- `V get(Object key)`
- `boolean containsKey(Object key)`
- `V remove(Object key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `Iterable<K> keys()`
- `int capacity()`
- `int lastProbeCount()`
- `default int maxProbeCount()`
- `default double loadFactor()`

## 보조 — (TODO 없는 보조 타입)

- `Hashing` (`Hashing.java`) — 역할:
- `Hashing.hash(Object key)` — 역할:
- `Hashing.mix(int h)` — 역할:
- `Hashing.tableSizeFor(int n)` — 역할:

## 구현 — ProbeSequenceMap (`src/main/java/com/datastructure/openaddr/ProbeSequenceMap.java`)

### 구조

선형·이차·이중 해싱 세 구현의 공통 골격이다. 그림을 읽는 데 필요한 말 넷.
  - *탐사(probing)*: 내 자리가 차 있을 때 정해진 규칙으로 다음 칸을 차례차례 들여다보는 것.
  - *슬롯(slot)*: 배열의 칸 하나. 키 하나가 들어가는 자리.
  - *부하율(load factor)*: 전체 칸 중 쓰인 칸의 비율. 꽉 찰수록 충돌이 늘어 느려진다.
  - *mask 와 2의 거듭제곱*: 용량을 8, 16, 32 처럼 2의 거듭제곱으로 잡으면, "나머지 연산" 대신 `& (capacity-1)` 한 번으로 자리 번호를 구할 수 있다. 그 `capacity-1` 이 mask 다.

```
ProbeSequenceMap - 슬롯 하나를 세 배열이 나눠 갖는다 (엔트리 객체 배열이 아니다)
+-------------------------------------------------------------------+
| size     = 3     (OCCUPIED 칸 수 = 실제 담긴 키 수)               |
| used     = 4     (OCCUPIED + TOMBSTONE. 리사이즈 판단은 이걸로)   |
| mask     = 7     (capacity - 1. capacity 가 2의 거듭제곱이라      |
|                   나머지를 & 한 번으로 구한다)                    |
| maxLoad  = 0.5   (DEFAULT_MAX_LOAD. 기본 capacity 는 8)           |
| lastProbes       (직전 연산이 들여다본 칸 수. 측정용)             |
+-------------------------------------------------------------------+

   idx      0     1     2     3     4     5     6     7
         +-----+-----+-----+-----+-----+-----+-----+-----+
  keys   |     |  A  |  B  |     |     |  C  |     |     |
         +-----+-----+-----+-----+-----+-----+-----+-----+
  values |     |  a  |  b  |     |     |  c  |     |     |
         +-----+-----+-----+-----+-----+-----+-----+-----+
  states |  E  |  O  |  O  |  T  |  E  |  O  |  E  |  E  |
         +-----+-----+-----+-----+-----+-----+-----+-----+
                              ^ 지웠던 자리. keys/values 는 null 이고 states 만 남는다

  states 는 byte 배열이고 값이 셋뿐이다
    E = EMPTY(0)      한 번도 안 쓴 칸. 탐사는 여기서 멈춘다
    O = OCCUPIED(1)   키가 들어 있는 칸
    T = TOMBSTONE(2)  지운 자리. 탐사는 통과하고, put 은 재사용 후보로만 기억한다

  capacity = keys.length = 8,  mask = 7,  tombstones() = used - size
  홈 슬롯      = Hashing.hash(key) & mask
                 (hash = key.hashCode() & 0x7fffffff. 일부러 안 섞는다 - 군집화를 먼저 보여주려고)
  i 번째 볼 칸 = probe(hash, i),  i = 0 이 홈
                 이 abstract 메서드 하나가 선형/이차/이중의 차이 전부다
```

### 동작 — put(충돌 시 탐사)

**언제 쓰나**: 키-값을 넣을 때. 그림 먼저 — 위가 전 상태, 아래가 후 상태. 홈(1번)이 차 있어서 두 칸 밀려 3번에 앉았다.
  - *충돌(collision)*: 서로 다른 키가 같은 홈 자리를 배정받는 것.

```
put(D, d) : 홈이 차 있으면 probe(hash, 1), probe(hash, 2) ... 로 다음 칸을 본다
            (아래는 선형 탐사 = 홈 + i 로 그린 것)

 before   idx    0     1     2     3     4     5
              +-----+-----+-----+-----+-----+-----+
       keys   |     |  A  |  B  |     |     |     |     A, B, D 모두 홈이 1
              +-----+-----+-----+-----+-----+-----+
       states |  E  |  O  |  O  |  E  |  E  |  E  |
              +-----+-----+-----+-----+-----+-----+
                       ^     ^     ^
                      i=0   i=1   i=2
                     O,키다름 O,키다름  E -> 여기다

 after    idx    0     1     2     3     4     5
              +-----+-----+-----+-----+-----+-----+
       keys   |     |  A  |  B  |  D  |     |     |
              +-----+-----+-----+-----+-----+-----+
       states |  E  |  O  |  O  |  O  |  E  |  E  |    size++, used++, lastProbes = 3
              +-----+-----+-----+-----+-----+-----+

 탐사 중 만나는 것마다 할 일이 다르다
   OCCUPIED + 같은 키   -> 값만 갈아끼우고 이전 값 반환. size 는 안 는다
   OCCUPIED + 다른 키   -> 다음 칸으로
   TOMBSTONE           -> 첫 자리만 firstTombstone 에 기억하고 탐사는 계속한다
                          (여기서 멈추면 뒤에 이미 있는 같은 키를 못 봐서 중복이 생긴다)
   EMPTY               -> 같은 키가 없다고 확정된 순간. 넣는다
                          firstTombstone 이 있으면 그 자리에(used 그대로, 재사용)
                          없으면 이 칸에(used++)

 넣기 전에 먼저 잰다 : used + 1 > capacity * maxLoad 이면 resize()
 비용 : 충돌이 없으면 1칸. 부하율이 오를수록 덩어리가 길어져 탐사가 는다
```

### 동작 — get / 탐사 종료 조건

**언제 쓰나**: 키를 찾을 때(get/containsKey/remove 전부 이 걸음을 쓴다). 요점은 "언제 멈추나" — EMPTY 를 만나야 '없다'가 확정되고, TOMBSTONE(지운 흔적)은 통과해야 한다.

```
indexOf(key) : 탐사열을 그대로 따라가며 세 가지만 본다. 본 칸 수를 lastProbes 에 남긴다

   EMPTY 를 만났다        ->  없다. 즉시 -1  (넣을 때도 여기서 멈췄을 테니 뒤에 있을 수 없다)
   OCCUPIED + 키가 같다   ->  그 칸의 인덱스
   TOMBSTONE / 다른 키    ->  통과하고 다음 칸
   한 바퀴(capacity 회) 가 상한이다

               0     1     2     3     4     5
            +-----+-----+-----+-----+-----+-----+
     keys   |     |  A  |     |  C  |     |     |    A, B, C 는 홈이 전부 1
            +-----+-----+-----+-----+-----+-----+    B 가 2번에 있다가 지워졌다
     states |  E  |  O  |  T  |  O  |  E  |  E  |
            +-----+-----+-----+-----+-----+-----+

   get(C) : 1(O, A 아님) -> 2(T, 통과) -> 3(O, C) 찾음.  lastProbes = 3
                            ^
                            여기서 T 를 EMPTY 처럼 보고 멈추면 C 를 영영 못 찾는다.
                            C 는 "2번이 차 있어서" 3번까지 밀려 들어갔기 때문이다.

   get(Z) : 1 -> 2 -> 3 -> 4 가 EMPTY -> -1.  없는 키는 EMPTY 를 만나야 끝난다

 요점 : 탐사열은 넣을 때와 찾을 때가 반드시 같아야 한다. TOMBSTONE 은 그 사슬을 이어주는 표시다.
        대신 T 가 쌓일수록 조회가 길어진다. 그 양이 tombstones() = used - size 다.
```

### 동작 — 삭제와 구멍 문제

**언제 쓰나**: 키를 지울 때. 그냥 칸을 비우면(EMPTY) 왜 안 되는지를 틀린 방법 → 맞는 방법 순서로 보여준다.
  - *tombstone(묘비)*: "여기 뭔가 있었다"는 흔적 표시. 탐사 사슬이 끊기지 않게 지운 자리에 남겨 둔다.

```
지운 자리를 그냥 EMPTY 로 비우면 (틀린 방법)

 before        0     1     2     3     4          A, B, C 모두 홈 = 1
            +-----+-----+-----+-----+-----+       B 는 1이 차서 2로
     keys   |     |  A  |  B  |  C  |     |       C 는 1,2 가 차서 3으로 밀려 들어갔다
            +-----+-----+-----+-----+-----+
     states |  E  |  O  |  O  |  O  |  E  |
            +-----+-----+-----+-----+-----+

 after(틀림)   0     1     2     3     4
            +-----+-----+-----+-----+-----+       get(C) : 1(A) -> 2(EMPTY) -> -1
     keys   |     |  A  |     |  C  |     |       C 는 3번에 멀쩡히 있는데 없다고 답한다
            +-----+-----+-----+-----+-----+       예외도 안 나고 조용히 틀린다
     states |  E  |  O  |  E  |  O  |  E  |
            +-----+-----+-----+-----+-----+
                          ^ 사슬이 여기서 끊겼다

 실코드의 해법 = TOMBSTONE 을 남긴다 (backward shift 가 아니다. 그건 RobinHoodMap 쪽 해법이다)

 after(맞음)   0     1     2     3     4
            +-----+-----+-----+-----+-----+       keys[i] = null, values[i] = null 로
     keys   |     |  A  |     |  C  |     |       참조는 끊되 states[i] = TOMBSTONE
            +-----+-----+-----+-----+-----+       size-- (used 는 그대로!)
     states |  E  |  O  |  T  |  O  |  E  |
            +-----+-----+-----+-----+-----+
                          ^ 사슬은 이어져 있다 -> get(C) 성공

 size 는 줄고 used 는 안 준다. 그 칸이 여전히 탐사를 길게 만드는 값을 물고 있기 때문이다.
 그래서 리사이즈 판단도 size 가 아니라 used 로 한다.
 비용 : O(탐사 길이). 넣고 지우기를 반복하면 T 가 쌓여 점점 느려진다 -> resize 가 청소한다
```

### 동작 — resize/rehash

**언제 쓰나**: 테이블이 기준 이상으로 차면(put 이 넣기 전에 잰다). 더 큰 새 배열을 잡고 살아 있는 키만 골라 옮긴다 — tombstone 은 이때 청소된다.
  - *재해싱(rehash)*: 용량이 바뀌면 mask 가 바뀌어 모든 키의 홈 자리를 새로 계산해 다시 앉히는 것.
  - *상환 O(1) (amortized)*: resize 한 번은 비싸지만 가끔만 일어나서, 여러 번의 put 에 나눠 계산하면 한 번당 평균 비용은 일정하다는 계산법.

```
put 은 넣기 전에 먼저 잰다
      used + 1 > capacity * maxLoad   ->  resize()          (maxLoad 기본 0.5)

 새 용량을 정하는 규칙이 하나 더 있다
      size > capacity * maxLoad / 2   ->  용량 2배   (진짜 원소가 찬 것)
      아니면                          ->  같은 용량   (tombstone 청소만 한다)
      넣고 지우기만 반복할 때 배열이 무한정 커지는 것을 막는다

 before   capacity = 8, maxLoad = 0.5, size = 3, used = 4  ->  used+1 = 5 > 4 이므로 resize
             0     1     2     3     4     5     6     7
          +-----+-----+-----+-----+-----+-----+-----+-----+
   keys   |     |  A  |  B  |     |     |  C  |     |     |
          +-----+-----+-----+-----+-----+-----+-----+-----+
   states |  E  |  O  |  O  |  T  |  E  |  O  |  E  |  E  |
          +-----+-----+-----+-----+-----+-----+-----+-----+
             size 3 > 8 * 0.5 / 2 = 2   ->  용량을 2배로

                 O 인 것만 골라 옮긴다      T 는 안 옮긴다 (여기서 청소된다)
                    |     |     |
                    v     v     v
 after    capacity = 16, mask = 15, size = 3, used = 3
             0     1     2     3    ...                        15
          +-----+-----+-----+-----+     +-----+-----+     +-----+
   states |  E  |  E  |  O  |  E  | ... |  O  |  E  | ... |  O  |
          +-----+-----+-----+-----+     +-----+-----+     +-----+
             mask 가 7 -> 15 로 바뀌므로 홈 슬롯이 전부 다시 계산된다(재해싱).
             자리도 순서도 before 와 무관하게 새로 정해진다.

 옮길 때(insertFresh)는 전부 EMPTY 인 새 배열이라 중복도 tombstone 도 없다.
 그래서 키 비교 없이 첫 빈칸에 바로 놓는다.
 비용 : O(capacity). 가끔만 일어나므로 put 1회 상환은 O(1)
```

### 필드
- `EMPTY` / `OCCUPIED` / `TOMBSTONE` (상태 상수) — 역할:
- `DEFAULT_CAPACITY` / `DEFAULT_MAX_LOAD` — 역할:
- `keys` — 역할:
- `values` — 역할:
- `states` — 역할:
- `size` — 역할:
- `used` — 역할:
- `mask` — 역할:
- `maxLoad` — 역할:
- `lastProbes` — 역할:

### `ProbeSequenceMap()` / `ProbeSequenceMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `abstract int probe(int hash, int i)`
- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object key)` (TODO 1)
- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO 2)
- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)` / `boolean containsKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `void resize()`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()` / `void clear()` / `Iterable<K> keys()`
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int lastProbeCount()` / `int tombstones()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinearProbeMap (`src/main/java/com/datastructure/openaddr/LinearProbeMap.java`)

### 동작 — 탐사 수열 (골격은 ProbeSequenceMap 과 같다)

**언제 쓰나**: 가장 단순한 규칙 — 차 있으면 바로 옆칸. 그림은 "홈이 3번인 키가 i번째로 보는 칸"이다.
  - *군집화(clustering)*: 찬 칸들이 서로 붙어 큰 덩어리로 자라는 현상. 덩어리가 길수록 탐사가 길어진다.
  - *캐시 지역성(cache locality)*: 방금 읽은 곳 바로 옆을 읽으면 CPU 캐시에 이미 있어서 빠른 성질. 옆칸 탐사의 숨은 장점.

```
probe(hash, i) = (hash + i) & mask        옆칸으로 한 칸씩

 홈 h = 3 인 키가 i 번째로 보는 칸 (capacity 8, mask 7). 칸 안의 수가 i 다
    idx      0     1     2     3     4     5     6     7
          +-----+-----+-----+-----+-----+-----+-----+-----+
          |  5  |  6  |  7  |  0  |  1  |  2  |  3  |  4  |   8칸 전부 한 번씩
          +-----+-----+-----+-----+-----+-----+-----+-----+
                             ^ 홈(i=0) 부터 오른쪽으로, 끝에서 되감긴다

 특성 : 일차 군집화(primary clustering)
   충돌한 키가 옆칸을 막고, 막힌 구간끼리 서로 붙어 하나의 덩어리로 자란다.
   길이 L 인 덩어리 앞으로 떨어진 "없는 키" 조회는 L+1 칸을 본다.
   다른 네 구현은 전부 이 수를 낮추려는 시도다.
 대신 다음 칸이 바로 옆이라 캐시 지역성은 다섯 중 제일 좋다.
```

### 필드
- (없음 — `ProbeSequenceMap` 의 것을 쓴다)

### `LinearProbeMap()` / `LinearProbeMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int probe(int hash, int i)` (TODO 3)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — QuadraticProbeMap (`src/main/java/com/datastructure/openaddr/QuadraticProbeMap.java`)

### 동작 — 탐사 수열 (골격은 ProbeSequenceMap 과 같다)

**언제 쓰나**: 선형의 덩어리 문제를 피하려고, 옆칸 대신 점점 멀리(+1, +3, +6, …) 건너뛴다. 그림 둘 — 위는 모든 칸을 도는 좋은 규칙(삼각수), 아래는 일부 칸에 영영 못 가는 나쁜 규칙(i²)이다.
  - *삼각수(triangular number)*: 1, 3, 6, 10, … 처럼 1+2+3+… 로 커지는 수. 용량이 2의 거듭제곱일 때 이 보폭이 모든 칸을 정확히 한 번씩 돈다.
  - *소수(prime)*: 1과 자기 자신으로만 나눠지는 수. "i² 탐사도 절반은 본다"는 보장은 용량이 소수일 때만 성립한다.

```
probe(hash, i) = (hash + offset) & mask       홈에서 점점 멀리 건너뛴다
   triangular = true  (기본)   offset = (i*i + i)/2  ->  +0, +1, +3, +6, +10, +15, +21, +28
   triangular = false (측정용) offset = i*i          ->  +0, +1, +4, +9, +16 ...

 홈 h = 3 인 키가 i 번째로 보는 칸 (capacity 8, mask 7). 칸 안의 수가 i 다

  triangular = true
    idx      0     1     2     3     4     5     6     7
          +-----+-----+-----+-----+-----+-----+-----+-----+
          |  6  |  3  |  5  |  0  |  1  |  4  |  2  |  7  |   8칸 전부 정확히 한 번씩
          +-----+-----+-----+-----+-----+-----+-----+-----+   -> 부하율이 얼마든 자리를 찾는다
                             ^ 홈(i=0)

  triangular = false
    idx      0     1     2     3     4     5     6     7
          +-----+-----+-----+-----+-----+-----+-----+-----+
          |  x  |  x  |  x  | 0,4 | 1,3 |  x  |  x  | 2,6 |   세 칸만 돌고 되풀이한다
          +-----+-----+-----+-----+-----+-----+-----+-----+
          x = 영영 못 가는 칸. 빈칸이 남아 있어도 못 넣어서 put 이 IllegalStateException 을 던진다
          ("이차 탐사는 절반을 본다"는 용량이 소수일 때 얘기다. 2의 거듭제곱에서는 훨씬 나쁘다)

 특성 : 일차 군집화는 사라진다. 건너뛰므로 덩어리가 서로 안 붙는다.
        대신 홈이 같은 키끼리는 여전히 같은 경로를 걷는다(이차 군집화). 그건 이중 해싱이 푼다.
```

### 필드
- `triangular` — 역할:

### `QuadraticProbeMap()` / `QuadraticProbeMap(int capacity, double maxLoad)` / `QuadraticProbeMap(int capacity, double maxLoad, boolean triangular)`
- 하는 일:
- 논리:
- 비용(왜):

### `int probe(int hash, int i)` (TODO 4)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — DoubleHashMap (`src/main/java/com/datastructure/openaddr/DoubleHashMap.java`)

### 동작 — 탐사 수열 (골격은 ProbeSequenceMap 과 같다)

**언제 쓰나**: 홈이 같은 키들이 같은 길을 걷는 것(이차 군집화)까지 없애고 싶을 때. 두 번째 해시로 키마다 다른 보폭(step)을 만든다.
  - *gcd(최대공약수)*: 두 수를 동시에 나누는 가장 큰 수. 보폭과 용량의 gcd 가 1이어야 모든 칸을 밟는다 — 용량이 2의 거듭제곱이면 보폭을 홀수로만 만들면 된다(`| 1`).

```
stepFor(hash)  = Hashing.mix(hash) | 1        보폭. 마지막 or 1 로 반드시 홀수
probe(hash, i) = (hash + i * stepFor(hash)) & mask

 홈 h = 3, 보폭 d = 5 인 키가 i 번째로 보는 칸 (capacity 8, mask 7). 칸 안의 수가 i 다
    idx      0     1     2     3     4     5     6     7
          +-----+-----+-----+-----+-----+-----+-----+-----+
          |  1  |  6  |  3  |  0  |  5  |  2  |  7  |  4  |   3, 0, 5, 2, 7, 4, 1, 6
          +-----+-----+-----+-----+-----+-----+-----+-----+
                             ^ 홈(i=0). 이후 +d 씩, 끝에서 되감긴다

 홈이 같아도 보폭이 키마다 다르므로 두 번째 칸부터 경로가 갈라진다 -> 군집화가 두 단계 다 사라진다

 보폭에 조건이 붙는 이유
   보폭 0        -> 제자리를 무한히 본다
   gcd(d, m) > 1 -> i*d mod m 이 도는 칸이 m/gcd 개뿐이라 일부 칸에 영영 못 간다
   m 이 2의 거듭제곱이면 약수가 2 뿐이므로, d 를 홀수로 만들기만 하면 gcd 가 1 이 된다.
   or 1 이 붙인 그 한 비트가 "모든 칸을 본다"를 보장한다.

 캐시 지역성은 다섯 중 제일 나쁘다. 다음 칸이 배열의 아무 데나 있다.
 탐사 횟수가 적어도 실제 시간은 그만큼 안 줄어드는 이유다.
```

### 필드
- (없음 — `ProbeSequenceMap` 의 것을 쓴다)

### `DoubleHashMap()` / `DoubleHashMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int stepFor(int hash)` (TODO 5)
- 하는 일:
- 논리:
- 비용(왜):

### `int probe(int hash, int i)`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — RobinHoodMap (`src/main/java/com/datastructure/openaddr/RobinHoodMap.java`)

### 구조

이름의 뜻부터: 로빈 후드처럼 "잘 사는 키(홈 가까이 앉은 키)의 자리를 뺏어 가난한 키(멀리 밀려난 키)에게 준다". 걷는 규칙 자체는 선형 탐사와 같고, 자리 다툼 규칙 하나만 다르다.
  - *거리(distance)*: 그 키가 자기 홈에서 몇 칸 밀려나 앉았는지. 이 수를 고르게 만드는 것이 목적이다.
  - *backward shift(뒤에서 당기기)*: 지운 자리를 tombstone 없이, 뒤 칸의 키들을 한 칸씩 앞으로 당겨 메우는 삭제 방법.

```
RobinHoodMap - states 배열이 없다. 빈칸은 keys[i] == null 이다
+-------------------------------------------------------------------+
| size / mask / maxLoad(0.5) / lastProbes                           |
| hashes[] : 그 칸 주인의 hash 를 그대로 들고 있다.                 |
|            홈을 다시 계산하지 않으려고 들고 있는다.               |
+-------------------------------------------------------------------+

   idx        0     1     2     3     4     5     6     7
           +-----+-----+-----+-----+-----+-----+-----+-----+
  keys     |     |  A  |  B  |  C  |     |     |     |     |
           +-----+-----+-----+-----+-----+-----+-----+-----+
  values   |     |  a  |  b  |  c  |     |     |     |     |
           +-----+-----+-----+-----+-----+-----+-----+-----+
  hashes   |  -  |  1  |  1  |  2  |  -  |  -  |  -  |  -  |
           +-----+-----+-----+-----+-----+-----+-----+-----+
  홈       |     |  1  |  1  |  2  |     |     |     |     |   홈 = hashes[i] & mask
  거리     |     |  0  |  1  |  1  |     |     |     |     |   distanceOf(i)
           +-----+-----+-----+-----+-----+-----+-----+-----+     = (i - 홈) & mask

  거리 = "집에서 몇 칸이나 밀려났나". 되감김도 & mask 로 그대로 잰다.
  탐사 수열 자체는 선형 탐사와 똑같다(옆칸으로 한 칸씩). 다른 것은 자리 다툼의 규칙 하나뿐이다.
  삭제에 tombstone 이 없다. 뒤에서 당겨온다(backward shift).
    거리 0 인 키(자기 홈에 앉은 키)나 빈칸을 만나면 멈춘다.
    거리 0 을 당기면 그 키가 자기 홈보다 앞으로 가버려 영영 못 찾는다.
```

### 동작 — 자리 뺏기

**언제 쓰나**: put 에서 충돌했을 때. 그림 먼저 — 전 상태에서 D 가 걸어오며 칸마다 "내 거리 vs 그 칸 주인의 거리"를 비교하고, 더 많이 걸었을 때만 자리를 뺏는다.
  - *분산 / 꼬리(tail)*: 거리들이 얼마나 들쭉날쭉한가 / 그중 최악(가장 밀려난 키). 로빈후드는 평균이 아니라 최악을 줄인다.

```
put(D) : 내가 걸어온 거리 > 그 칸 주인의 거리 이면 자리를 뺏고, 뺏긴 놈을 들고 계속 걷는다

 before  (D 를 넣는다. D 의 홈 = 1)
    idx      0     1     2     3     4     5
          +-----+-----+-----+-----+-----+-----+
  keys    |     |  A  |  B  |  C  |     |     |
          +-----+-----+-----+-----+-----+-----+
  홈      |     |  1  |  1  |  2  |     |     |
  거리    |     |  0  |  1  |  1  |     |     |
          +-----+-----+-----+-----+-----+-----+

  slot 1 : 내 거리 0  vs  A 의 거리 0  ->  안 뺏는다(더 커야 뺏는다). 옆칸으로
  slot 2 : 내 거리 1  vs  B 의 거리 1  ->  안 뺏는다. 옆칸으로
  slot 3 : 내 거리 2  vs  C 의 거리 1  ->  내가 더 걸었다. 뺏는다
           D 를 3번에 앉히고 C 를 들고 간다. 내 거리도 C 의 것(1)로 바꿔 이어 걷는다
           (뺏은 순간 원래 키가 테이블에 없다는 게 확정돼서 키 비교도 그만둔다)
  slot 4 : 비었다  ->  C 를 놓는다

 after
    idx      0     1     2     3     4     5
          +-----+-----+-----+-----+-----+-----+
  keys    |     |  A  |  B  |  D  |  C  |     |
          +-----+-----+-----+-----+-----+-----+
  홈      |     |  1  |  1  |  1  |  2  |     |
  거리    |     |  0  |  1  |  2  |  2  |     |
          +-----+-----+-----+-----+-----+-----+

 왜 분산이 주는가
   같은 입력을 선형 탐사에 넣으면 D 가 4번까지 밀려 거리 3 이 된다.  거리 합 0+1+1+3 = 5
   로빈후드는 배치만 바꾼다.                                        거리 합 0+1+2+2 = 5
   합(=평균)은 보존되고 최댓값만 3 -> 2 로 준다. 평균이 아니라 꼬리를 자르는 것이다.

 조회에서 이득이 하나 더 나온다
   indexOf 는 "내 거리 > 이 칸 주인의 거리"가 되는 순간 -1 을 반환한다.
   여기 있었다면 이 칸을 뺏었어야 하므로 더 볼 필요가 없다.
   덩어리 한가운데로 떨어진 없는 키 조회가 선형 탐사에서는 덩어리 끝까지 갔는데
   여기서는 몇 칸이면 끝난다.
```

### 필드
- `DEFAULT_CAPACITY` / `DEFAULT_MAX_LOAD` — 역할:
- `keys` — 역할:
- `values` — 역할:
- `hashes` — 역할:
- `size` — 역할:
- `mask` — 역할:
- `maxLoad` — 역할:
- `lastProbes` — 역할:

### `RobinHoodMap()` / `RobinHoodMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int distanceOf(int slot)`
- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object key)` (TODO 6)
- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO 7)
- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)` (TODO 8)
- 하는 일:
- 논리:
- 비용(왜):

### `void resize()`
- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)` / `boolean containsKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()` / `void clear()` / `Iterable<K> keys()` / `int capacity()` / `int lastProbeCount()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — CuckooHashMap (`src/main/java/com/datastructure/openaddr/CuckooHashMap.java`)

### 구조

이름의 뜻부터: 뻐꾸기(cuckoo)는 남의 둥지에 알을 낳아 원래 있던 알을 밀어낸다. 여기서는 키가 딱 두 자리만 가질 수 있고, 차 있으면 그 키를 밀어낸다.
  - *체이닝(chaining)*: 오픈 어드레싱의 반대 진영 — 충돌한 키들을 같은 칸에 사슬(연결 리스트)로 매다는 방식. 자바 HashMap 이 이쪽이다.

```
CuckooHashMap - 배열 하나를 반으로 갈라 두 테이블로 쓴다 (keys/values 각각 하나씩)
   capacity = 8,  half = capacity/2 = 4,  mask = half - 1 = 3,  maxLoad = 0.45

               1번 테이블 (앞 절반)              2번 테이블 (뒤 절반)
   idx      0     1     2     3        |     4     5     6     7
         +-----+-----+-----+-----+     |  +-----+-----+-----+-----+
  keys   |     |  A  |     |     |     |  |     |  B  |     |     |
         +-----+-----+-----+-----+     |  +-----+-----+-----+-----+

 키 하나가 갈 수 있는 자리는 정확히 둘뿐이다
   slot1(hash) = hash & mask                         ->  0 .. half-1
   slot2(hash) = half + (Hashing.mix(hash) & mask)   ->  half .. capacity-1
   (두 번째 자리는 mix 로 섞은 해시를 쓴다. 첫 자리와 상관이 낮아야 의미가 있다)

   A --+--> 1번 1번칸   <- 지금 여기 있다
       +--> 2번 5번칸   <- 여기 있을 수도 있었다
   B --+--> 1번 2번칸
       +--> 2번 5번칸   <- 지금 여기 있다

 그래서 조회가 상수다
   indexOf 는 slot1 과 slot2, 딱 두 칸만 본다. 탐사 사슬이라는 것이 아예 없다.
   부하율이 얼마든 최악 O(1) 이고 lastProbes 는 2 를 넘지 않는다.
   삭제도 그냥 비우면 된다. tombstone 이 필요 없다 - 이 자리를 지나 뒤에 들어간 키가 없으니까.
   앞의 넷은 "찾을 때까지 걷는" 구조라 조회 상한이 부하율에 딸려 있었다. 그걸 여기서 끊는다.
```

### 동작 — 쫓아내기(kick)

**언제 쓰나**: put 에서 내 자리가 차 있을 때. 그림 먼저 — 전 상태에서 [1][2][3] 연쇄(내가 앉고, 쫓겨난 키는 자기 반대편 자리로)를 거쳐 후 상태가 된다.
  - *고리(cycle)*: 쫓아내기가 서로를 맴돌며 영영 안 끝나는 상황. 횟수 상한(MAX_KICKS)으로 감지하고 rehash 로 푼다.

```
put(D) : 새 항목은 언제나 1번 테이블의 자기 자리부터 본다 (tryInsert)
         D 의 자리 = 1번 1 / 2번 5,  A 의 자리 = 1번 1 / 2번 5,  B 의 자리 = 1번 2 / 2번 5

 before      1번 테이블                      2번 테이블
   idx    0     1     2     3        |     4     5     6     7
       +-----+-----+-----+-----+     |  +-----+-----+-----+-----+
       |     |  A  |     |     |     |  |     |  B  |     |     |
       +-----+-----+-----+-----+     |  +-----+-----+-----+-----+

  [1] D 를 1번 1 에 놓으려는데 A 가 있다  ->  A 를 쫓아내고 D 가 앉는다 (kicks++)
  [2] 쫓겨난 A 는 반대편 자리로 간다 = 2번 5. 거기 B 가 있다  ->  B 를 쫓아내고 A 가 앉는다
  [3] 쫓겨난 B 는 반대편 자리로 간다 = 1번 2. 비었다  ->  끝
      (1번에서 밀렸으면 2번으로, 2번에서 밀렸으면 1번으로. slot < half 로 어느 쪽인지 안다)

 after
   idx    0     1     2     3        |     4     5     6     7
       +-----+-----+-----+-----+     |  +-----+-----+-----+-----+
       |     |  D  |  B  |     |     |  |     |  A  |     |     |
       +-----+-----+-----+-----+     |  +-----+-----+-----+-----+
                ^     ^                          ^
              D 앉음  밀려온 B                   밀려온 A

 연쇄가 끝나지 않으면
   MAX_KICKS(32) 를 넘으면 고리로 본다. tryInsert 가 들고 있던 항목을 반환한다.
     이 반환값을 버리면 크기만 맞고 키가 사라지는 조용한 사고가 난다.
   put 은 그 항목을 받아 용량 2배로 rehash 하고 다시 넣는다 (cycleRehashes++).
   MAX_REHASH(4) 번 해도 못 넣으면 담을 수 없는 키다 -> giveUp 으로 나머지를 복구하고 예외.
     hashCode 가 같고 equals 가 다른 키 둘은 두 자리가 완전히 겹쳐서 용량을 키워도 안 된다.
     체이닝은 그런 키를 그냥 사슬에 매단다. 상수 조회를 얻고 이걸 내준 것이다.
   기본 부하율이 0.45 인 것도 같은 이유다. 0.5 근처에서 고리가 급증한다.

 값은 삽입이 치른다 : 조회 O(1) 보장을 삽입의 뺏기 연쇄로 산 것이다 (kickCount 로 잰다)
```

### 필드
- `MAX_KICKS` — 역할:
- `MAX_REHASH` — 역할:
- `DEFAULT_CAPACITY` / `DEFAULT_MAX_LOAD` — 역할:
- `keys` — 역할:
- `values` — 역할:
- `half` — 역할:
- `mask` — 역할:
- `size` — 역할:
- `maxLoad` — 역할:
- `lastProbes` — 역할:
- `kicks` — 역할:
- `rehashes` — 역할:
- `cycleRehashes` — 역할:

### `CuckooHashMap()` / `CuckooHashMap(int capacity, double maxLoad)`
- 하는 일:
- 논리:
- 비용(왜):

### `int slot1(int hash)` / `int slot2(int hash)`
- 하는 일:
- 논리:
- 비용(왜):

### `int indexOf(Object key)` (TODO 9)
- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO 10)
- 하는 일:
- 논리:
- 비용(왜):

### `Object[] tryInsert(Object key, Object value)` (TODO 11, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void rehash(int newCapacity)` / `void giveUp(Object[] homeless, K key)`
- 하는 일:
- 논리:
- 비용(왜):

### `V remove(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `V get(Object key)` / `boolean containsKey(Object key)`
- 하는 일:
- 논리:
- 비용(왜):

### `long kickCount()` / `int rehashCount()` / `int cycleRehashCount()` / `void resetCounters()`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `boolean isEmpty()` / `void clear()` / `Iterable<K> keys()` / `int capacity()` / `int lastProbeCount()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| LinearProbeMap (선형 탐사) | | | |
| QuadraticProbeMap (이차 탐사) | | | |
| DoubleHashMap (이중 해싱) | | | |
| RobinHoodMap (로빈후드) | | | |
| CuckooHashMap (쿠쿠) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/29-open-addressing/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/29-open-addressing/src/main/java/com/datastructure/openaddr/`
- 테스트: `/home/jun/project/myway/data-structure/29-open-addressing/src/test/java/com/datastructure/openaddr/`
- 정답 구현: `/home/jun/project/myway/data-structure/29-open-addressing/impl/`

## 용어 풀이

- **해시(hash) / hashCode**: 키를 숫자로 바꾸는 계산 / 자바 객체가 제공하는 그 숫자. 자리 번호의 재료.
- **오픈 어드레싱(open addressing)**: 충돌하면 같은 배열 안의 다른 칸을 규칙대로 찾아가는 해시맵 방식. 사슬을 안 만든다.
- **체이닝(chaining)**: 충돌한 키들을 같은 칸에 연결 리스트로 매다는 반대 방식.
- **홈 슬롯(home slot)**: 해시로 계산한 그 키의 원래 지정 자리.
- **탐사(probing) / 탐사 수열**: 차 있을 때 다음 칸을 차례로 보는 것 / 그 칸들의 순서(i번째로 볼 칸).
- **충돌(collision)**: 다른 키가 같은 홈을 배정받는 것.
- **부하율(load factor)**: 전체 칸 중 쓰인 칸의 비율. 리사이즈 기준.
- **mask / 2의 거듭제곱**: 용량이 2ⁿ이면 `& (capacity-1)` 한 번으로 나머지를 구한다. 그 `capacity-1` 이 mask.
- **tombstone(묘비)**: 지운 자리에 남기는 "여기 있었다" 표시. 탐사 사슬을 이어주지만 쌓이면 느려진다.
- **재해싱(rehash) / resize**: 더 큰 배열을 잡고 모든 키의 자리를 새로 계산해 옮기는 것.
- **상환/분할상환(amortized)**: 가끔 비싼 연산을 여러 번에 나눠 평균 내는 비용 계산법.
- **일차 군집화(primary clustering)**: 선형 탐사에서 찬 칸들이 붙어 덩어리로 자라는 현상.
- **이차 군집화(secondary clustering)**: 홈이 같은 키들이 똑같은 경로를 걷는 현상. 이중 해싱이 푼다.
- **삼각수(triangular number)**: 1, 3, 6, 10, … (1+2+3+…). 2의 거듭제곱 용량에서 모든 칸을 도는 이차 탐사 보폭.
- **소수(prime)**: 1과 자신으로만 나눠지는 수.
- **gcd(최대공약수)**: 두 수를 동시에 나누는 가장 큰 수. 보폭과 용량의 gcd 가 1이어야 모든 칸을 밟는다.
- **보폭(step)**: 이중 해싱에서 키마다 다르게 정하는 건너뛰기 간격.
- **캐시 지역성(cache locality)**: 방금 읽은 곳 근처를 읽으면 CPU 캐시 덕에 빠른 성질.
- **거리(distance, 로빈후드)**: 키가 자기 홈에서 몇 칸 밀려났는지.
- **backward shift**: tombstone 없이 뒤 칸을 앞으로 당겨 지운 자리를 메우는 삭제법.
- **꼬리(tail)**: 확률 분포의 최악 쪽 끝. 로빈후드는 평균이 아니라 이 최악 거리를 줄인다.
- **kick(쫓아내기) / 고리(cycle)**: 쿠쿠에서 앉은 키를 밀어내는 것 / 그 밀어내기가 맴돌아 안 끝나는 상황.
- **equals / hashCode 가 같고 equals 가 다른 키**: 값 비교는 다른데 해시 숫자만 같은 두 키. 쿠쿠의 아킬레스건.
- **abstract 메서드**: 골격 클래스가 "이 부분은 자식이 채워라"라고 비워 둔 메서드. probe() 하나로 다섯 구현이 갈린다.
- **O(1) / O(n) / 최악 O(1)**: 항상 일정한 일 / 개수에 비례하는 일 / 어떤 경우에도 일정(쿠쿠 조회는 항상 2칸).
- **IllegalStateException**: "지금 상태에서는 그 일을 할 수 없다"를 알리는 자바의 오류 신호.
