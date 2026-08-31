# data-structure/18-bitset — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — BitVector (`src/main/java/com/datastructure/bitset/BitVector.java`)

- `int size()`
- `boolean get(int index)`
- `void set(int index)`
- `void set(int index, boolean value)`
- `void clear(int index)`
- `void flip(int index)`
- `void clearAll()`
- `void flipAll()`
- `int cardinality()`
- `boolean isEmpty()`
- `int nextSetBit(int from)`
- `void and(BitVector other)`
- `void or(BitVector other)`
- `void xor(BitVector other)`
- `void andNot(BitVector other)`
- `List<Integer> toList()`
- `int unitCount()`
- `long memoryBytes()`

## 구현 — BooleanArrayBitSet (`src/main/java/com/datastructure/bitset/BooleanArrayBitSet.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
boolean[] 은 칸 하나가 1 byte 다 - 비트 하나를 저장하려고 8비트를 쓴다

  BooleanArrayBitSet : boolean[200]
     idx     0     1     2     3               199
          +-----+-----+-----+-----+   ...   +-----+
          |  1  |  0  |  0  |  1  |         |  0  |    칸 하나 = 1 byte = 8 bit
          +-----+-----+-----+-----+   ...   +-----+
          memoryBytes() = 200 byte,  unitCount() = 200 (칸 하나가 비트 하나)

  WordBitSet : long[4]
          +---------+---------+---------+---------+
          | long 64 | long 64 | long 64 | long 64 |    칸 하나 = 8 byte = 64 bit
          +---------+---------+---------+---------+
          memoryBytes() = 32 byte,  unitCount() = 4

  같은 200비트에 메모리 8배 차이 (1비트당 1바이트  대  1비트당 1비트)

  대신 코드는 단순하다. get/set 은 bits[index] 그대로라 마스크 계산이 없고,
  꼬리 비트 같은 것도 없다(칸이 곧 비트라 남는 자리가 생기지 않는다).
  and/or/xor 는 칸을 하나씩 돌아 200회 - WordBitSet 의 4회와 대비된다.
```

### `필드`

- `boolean[] bits` 역할:

### `public BooleanArrayBitSet(int size)`

- 하는 일:
- 비용(왜):

### `public int cardinality()` (TODO)

- 하는 일:
- 논리(배열을 전부 훑는 수밖에 없는 이유):
- 비용(왜):

### `public boolean get(int index)` / `public void set(int index)` / `public void set(int index, boolean value)` / `public void clear(int index)` / `public void flip(int index)`

- 하는 일:
- 비용(왜):

### `public void clearAll()` / `public void flipAll()`

- 하는 일:
- 비용(왜):

### `public boolean isEmpty()` / `public int nextSetBit(int from)`

- 하는 일:
- 비용(왜):

### `public void and(BitVector other)` / `or` / `xor` / `andNot`

- 하는 일:
- 논리:
- 비용(왜):

### `public List<Integer> toList()` / `public int size()` / `public int unitCount()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

## 구현 — WordBitSet (`src/main/java/com/datastructure/bitset/WordBitSet.java`)

### 구조

```
WordBitSet (size = 200)
+---------------------------------------------------+
| size  = 200        (논리적 비트 수)                |
| words ---+         (long[] - 64비트씩 묶은 배열)   |
+----------|----------------------------------------+
           v
   w          0         1         2         3
         +---------+---------+---------+---------+
         | long 64 | long 64 | long 64 | long 64 |
         +---------+---------+---------+---------+

   words.length = wordCountFor(200) = (200 + 63) / 64 = 4
   words[0] : 비트 0..63      words[1] : 비트 64..127
   words[2] : 비트 128..191   words[3] : 비트 192..255 (200..255 는 안 쓰는 꼬리)

비트 i 가 어디 있나
   워드 번호    w = i >>> 6        (= i / 64,   wordIndex)
   워드 안 자리 = i & 63           (= i % 64)
   마스크       = 1L << (i & 63)   (mask - 그 자리 하나만 1 인 long)

   예) i = 130 -> w = 130 >>> 6 = 2,   130 & 63 = 2,   mask = 1L << 2
       -> words[2] 의 2번 자리

words[0] 한 워드를 펼치면 (자리 번호가 커지는 쪽으로 그렸다.
2진수로 적을 때와는 좌우가 반대다 - 1L << 0 이 최하위 비트다)

   자리       0   1   2   3   4   5   6   7        62  63
            +---+---+---+---+---+---+---+---+ ... +---+---+
  words[0]  | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | ... | 0 | 0 |
            +---+---+---+---+---+---+---+---+ ... +---+---+
              ^       ^                                ^
         1L << 0   1L << 2 = mask(2)               1L << 63

   words[0] 에서 켜진 자리 1, 4 -> 전역 비트 번호도 1, 4  (w * 64 = 0)
   words[2] 의 자리 3 이 켜졌다면 전역 비트 번호는 2 * 64 + 3 = 131
```

### 동작 — 켜고 끄고 읽기

```
아래는 한 워드의 64자리 중 앞 8자리만 잘라 그린 것이다. w = i >>> 6, mask = 1L << (i & 63)

[1] set(i) : words[w] |= mask - 그 자리만 1 로 올린다. 나머지 자리는 그대로. O(1)
    set(3) -> mask = 1L << 3
     자리     0   1   2   3   4   5   6   7            0   1   2   3   4   5   6   7
            +---+---+---+---+---+---+---+---+        +---+---+---+---+---+---+---+---+
  words[w]  | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |   ->   | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
            +---+---+---+---+---+---+---+---+        +---+---+---+---+---+---+---+---+
  mask      | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |                      ^ 여기만 켜졌다
            +---+---+---+---+---+---+---+---+
    OR 은 1 을 지우지 않는다 -> 이미 켜져 있었으면 아무 일도 안 일어난다(멱등)

[2] get(i) : (words[w] & mask) != 0 - 그 자리만 남기고 다 지운 뒤 0 인지 본다. O(1)
    get(4)
            +---+---+---+---+---+---+---+---+
  words[w]  | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
            +---+---+---+---+---+---+---+---+   AND
  mask      | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
            +---+---+---+---+---+---+---+---+
  결과      | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |   != 0  ->  true
            +---+---+---+---+---+---+---+---+
    get(5) 이면 결과가 통째로 0 -> false

[3] clear(i) : words[w] &= ~mask - 그 자리만 0 이고 나머지는 전부 1 인 값과 AND. O(1)
    clear(3)
     자리     0   1   2   3   4   5   6   7            0   1   2   3   4   5   6   7
            +---+---+---+---+---+---+---+---+        +---+---+---+---+---+---+---+---+
  words[w]  | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |   ->   | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
            +---+---+---+---+---+---+---+---+        +---+---+---+---+---+---+---+---+
  ~mask     | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 |                      ^ 여기만 꺼졌다
            +---+---+---+---+---+---+---+---+
    나머지 자리는 x & 1 = x 라 보존된다

[4] flip(i) : words[w] ^= mask - XOR 은 마스크가 1 인 자리만 뒤집는다. O(1)
    1 ^ 1 = 0,  0 ^ 1 = 1,  나머지 자리는 x ^ 0 = x 로 보존

    세 연산 모두 배열 첨자 한 번 + 산술 한 번이라 크기와 무관하게 O(1)
```

### 동작 — 집합 연산

```
and / or / xor / andNot : 워드 하나에 CPU 연산 한 번으로 64자리를 동시에 처리한다

  this.words   +--------+--------+--------+--------+
               |   w0   |   w1   |   w2   |   w3   |   size = 200
               +--------+--------+--------+--------+
                    |        |        |        |
                    op       op       op       op       op = & , | , ^ , &~
                    |        |        |        |
  other.words  +--------+--------+--------+--------+
               |   w0   |   w1   |   w2   |   w3   |
               +--------+--------+--------+--------+

  반복 횟수 = words.length = ceil(n / 64) = 4 회   (비트를 하나씩 돌면 200 회)
     and    : words[i] &= other.words[i]        (교집합)
     or     : words[i] |= other.words[i]        (합집합)
     xor    : words[i] ^= other.words[i]        (대칭차)
     andNot : words[i] &= ~other.words[i]       (this 에서 other 를 뺀다)

  여전히 O(n) 이지만 상수가 64배 작다. 상대가 WordBitSet 이 아니면
  이 지름길을 못 쓰고 비트를 하나씩 도는 느린 길로 간다.

꼬리 정리(trimTail) : size 가 64의 배수가 아니면 마지막 워드에 "없는 자리"가 남는다
  size = 200 이면 words[3] 의 자리 8..63 은 비트 200..255 - 존재하지 않는 비트
             +--------------+----------------------------+
  words[3]   |  유효 8자리  |  남는 56자리 (항상 0)      |
             +--------------+----------------------------+
  flipAll / or / xor 로 여기에 1 이 서면 cardinality 가 실제보다 커진다
  -> words[마지막] &= (1L << (size & 63)) - 1  로 꺼둔다

cardinality() : 워드마다 Long.bitCount 한 번씩 더한다. O(n / 64)
nextSetBit(from) : 시작 워드는 (-1L << (from & 63)) 로 앞자리를 지우고,
  0 이 아닌 워드를 만나면 Long.numberOfTrailingZeros 로 가장 낮은 켜진 자리를 뽑아
  w * 64 + tz 를 돌려준다. 0 인 워드는 64비트를 통째로 건너뛴다.
```

### `필드`

- `static final int BITS_PER_WORD = 64` 역할:
- `int size` 역할:
- `long[] words` 역할:
- 꼬리 비트(size 가 64의 배수가 아닐 때 남는 자리)가 문제가 되는 이유:

### `public WordBitSet(int size)`

- 하는 일:
- 비용(왜):

### `static int wordCountFor(int size)` (TODO)

- 하는 일:
- 논리(올림 나눗셈):
- 비용(왜):

### `static int wordIndex(int bit)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static long mask(int bit)` (TODO)

- 하는 일:
- 논리(`bit & 63` 을 명시하는 이유 — 자바 시프트가 자동으로 나머지를 쓴다는 것):
- 비용(왜):

### `public int cardinality()` (TODO)

- 하는 일:
- 논리(popcount):
- 비용(왜):

### `public int nextSetBit(int from)` (TODO)

- 하는 일:
- 논리(꺼진 워드를 통째로 건너뛰는 것 · "크기 밖이면 -1" 검사가 도달 불가라는 기록):
- 비용(왜):

### `public void and(BitVector other)` (TODO)

- 하는 일:
- 논리(상대 타입에 따라 워드 단위 / 비트 단위로 갈리는 이유):
- 비용(왜):

### `private void trimTail()` (TODO)

- 하는 일:
- 논리(정리 마스크 자체의 함정):
- 비용(왜):

### `public void flipAll()` (TODO)

- 하는 일:
- 논리(왜 여기서 꼬리 정리가 필요해지는가):
- 비용(왜):

### `public boolean get(int index)` / `public void set(int index)` / `public void set(int index, boolean value)` / `public void clear(int index)` / `public void flip(int index)`

- 하는 일:
- 비용(왜):

### `public void clearAll()` / `public boolean isEmpty()`

- 하는 일:
- 비용(왜):

### `public void or(BitVector other)` / `xor` / `andNot`

- 하는 일:
- 논리:
- 비용(왜):

### `public List<Integer> toList()` / `public int size()` / `public int unitCount()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

## 구현 — SparseBitSet (`src/main/java/com/datastructure/bitset/SparseBitSet.java`)

### 구조

```
TreeMap<Integer, Long> - "0 이 아닌 워드"만 워드 번호를 키로 띄엄띄엄 담는다
(워드를 쪼개는 규칙은 WordBitSet 과 같다: 워드 번호 i >>> 6, 자리 1L << (i & 63))

  size = 1,000,000 (워드로는 15625개) 인데 켜진 비트가 3개뿐이라면

  WordBitSet   long[15625] : 0 인 워드까지 전부 자리를 차지한다 = 125,000 byte
     w     0     1     2     3          700          15624
        +-----+-----+-----+-----+ ... +-----+       +-----+
        |  0  |  0  |  V  |  0  |     |  V  |       |  0  |
        +-----+-----+-----+-----+ ... +-----+       +-----+
        (V = 0 이 아닌 워드. 그 밖의 칸은 전부 0 인데도 자리를 차지한다)

  SparseBitSet  TreeMap : 값이 있는 워드만 엔트리로 (없는 워드 = 전부 0 으로 간주)
        words = { 2 -> 어떤 long,  700 -> 어떤 long,  9001 -> 어떤 long }
                +------------+   +------------+   +------------+
                | key   2    |   | key  700   |   | key  9001  |
                | value long |   | value long |   | value long |
                +------------+   +------------+   +------------+
                엔트리 3개.  memoryBytes() = 엔트리 수 * 48 byte
                (키/값 박싱 + 트리 노드까지 쳐서 엔트리당 대략 48 byte)

  clear 로 워드가 0 이 되면 엔트리 자체를 지운다 -> 빈 워드는 남지 않는다
  get/set 은 배열 첨자 대신 트리 탐색 O(log 엔트리수),  isEmpty 는 맵이 비었는지만 본다
  nextSetBit 은 tailMap 으로 다음 엔트리를 바로 잡아 빈 구간을 통째로 건너뛴다

  약점 : 켜진 비트가 많아지면 워드가 다 생겨 오히려 무겁다(엔트리 48 byte 대 워드 8 byte).
         flipAll 은 대부분을 켜므로 희소하다는 전제 자체가 무너진다.
```

### `필드`

- `static final int BYTES_PER_ENTRY = 48` 역할:
- `int size` 역할:
- `TreeMap<Integer, Long> words` 역할:
- 손익분기(워드의 1/6 미만이 켜질 때 유리하다)의 근거:

### `public SparseBitSet(int size)`

- 하는 일:
- 비용(왜):

### `public void set(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public void clear(int index)` (TODO)

- 하는 일:
- 논리(워드가 비면 맵에서 지우는 이유):
- 비용(왜):

### `public int nextSetBit(int from)` (TODO)

- 하는 일:
- 논리(있는 워드만 순서대로 보는 것 — TreeMap 이 필요한 이유):
- 비용(왜):

### `public boolean get(int index)` / `public void set(int index, boolean value)` / `public void flip(int index)`

- 하는 일:
- 비용(왜):

### `public void clearAll()` / `public void flipAll()`

- 하는 일:
- 논리(flipAll 이 희소성을 깨뜨리는 것):
- 비용(왜):

### `public int cardinality()` / `public boolean isEmpty()`

- 하는 일:
- 비용(왜):

### `public void and(BitVector other)` / `or` / `xor` / `andNot`

- 하는 일:
- 비용(왜):

### `public List<Integer> toList()` / `public int size()` / `public int unitCount()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BooleanArrayBitSet (`boolean[]`) | | | |
| WordBitSet (`long[]`) | | | |
| SparseBitSet (켜진 워드만 TreeMap 에) | | | |

## 문제 — BitSetProblems (`src/main/java/com/datastructure/bitset/BitSetProblems.java`)

### 문제 1. 에라토스테네스의 체 — `static BitVector sieve(int n)`

> 문제 설명: n 이하의 소수를 전부 찾는다. 반환한 비트셋의 i번 비트가 켜져 있으면 i 가 소수다.
> 비트셋의 고전적인 쓰임이다. 100만까지면 `boolean[]` 은 1MB, 비트셋은 125KB 다.
> 캐시에 들어가느냐 마느냐가 갈리는 크기다.
> (n < 2 이면 IllegalArgumentException)

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 자카드 유사도 — `static double jaccard(BitVector a, BitVector b)`

> 문제 설명: 두 비트셋의 자카드 유사도(교집합 크기 / 합집합 크기)를 구한다.
> 둘 중 하나라도 null 이면 IllegalArgumentException, 크기가 다르면 IllegalArgumentException.
> 생각할 것: 둘 다 비었을 때 이 값은 무엇으로 정의되는가.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 부분집합 열거 — `static List<Integer> enumerateSubsets(int mask)`

> 문제 설명: 마스크의 모든 부분집합을 내림차순으로 열거한다.
> 0부터 mask 까지 전부 돌며 `(i & mask) == i` 를 검사하면 2^32 번이다.
> 관용구를 쓰면 부분집합 개수만큼만 돈다. 켜진 비트가 4개면 16번이다.
> 쓰이는 곳: 비트마스크 DP(외판원 문제, 집합 분할), 조합 최적화.
> (mask < 0 이면 IllegalArgumentException)

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

- README: `/home/jun/project/myway/data-structure/18-bitset/README.md`
- 구현: `/home/jun/project/myway/data-structure/18-bitset/src/main/java/com/datastructure/bitset/`
- 테스트: `/home/jun/project/myway/data-structure/18-bitset/src/test/java/com/datastructure/bitset/`
- 정답 구현: `/home/jun/project/myway/data-structure/18-bitset/impl/`
