# data-structure/29-open-addressing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

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
