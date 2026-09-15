# data-structure/18-bitset — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 방마다 다니며 불 끄기 vs 스위치판.** 방 200개의 불을 관리할 때, 방마다 찾아가 하나씩 끄면 200번 움직여야 한다. 복도에 64구짜리 스위치판이 있으면 판 하나를 탁 내려서 64개를 한 번에 끈다.

**비트셋이 똑같은 구조다.** "켜짐/꺼짐" 200개를 boolean 배열로 한 칸씩 두는 대신, 64비트 정수(long) 몇 개에 꽉꽉 눌러 담는다. 그러면 CPU 연산 한 번이 64칸을 동시에 처리한다. 실무에선 소수 찾기(에라토스테네스의 체), 권한 플래그, 추천 시스템의 집합 비교(자카드 유사도)에 쓴다.

- boolean 한 칸은 1바이트 = 8비트인데, 실제 정보는 1비트뿐이다. 8배 낭비.
  - *비트(bit)*: 0 아니면 1, 정보의 최소 단위. *바이트(byte)* = 비트 8개 묶음.
- long 하나는 64비트 — "켜짐/꺼짐" 64개를 한 칸에 담는다. 메모리가 1/8로 준다.
- and/or/xor 같은 집합 연산도 64칸씩 한꺼번에 — 반복 횟수가 1/64로 준다.
- 켜진 비트가 아주 드물면(희소) "0이 아닌 칸만" 지도에 담는 SparseBitSet 변형도 있다.

```text
  boolean[8]:  [1][0][0][1][0][0][0][0]   <- 8칸 = 8바이트
  비트셋:      10010000                    <- 같은 정보가 1바이트 안에
```

## 문제 — 이 챕터가 시키는 것

11번 블룸 필터에서 비트 배열을 **쓰기만 하고 안 가르쳤다.** 여기서 제대로 본다.
자바 `boolean[]` 은 원소 하나가 1비트가 아니라 1바이트라 100만 개면 1MB, 비트로 누르면 125KB — 8배 차이다.
**그런데 진짜 이유는 메모리가 아니다.** `a[i] & b[i]` 하나가 비트 64개를 처리해 교집합 걸음 수가 100만에서 15,625로 준다.
`BitVectorContractTest.java` 를 따라친 뒤 TODO 를 채운다(처음에는 98개 중 82개가 실패한다).

- `BooleanArrayBitSet` 의 TODO 1개 — `boolean[]` 그대로인 기준선. **어려울 게 없다는 것이 요점**이다.
- `WordBitSet` 의 TODO 8개 — `long[]` 에 눌러 담는 본체. `wordCountFor` · `wordIndex` · `mask` · `cardinality` · `nextSetBit` · `and` · `trimTail` · `flipAll`.
- `SparseBitSet` 의 TODO 3개 — 켜진 워드만 `TreeMap` 에. `set` · `clear` · `nextSetBit`.
- `BitSetProblems` 의 TODO 3개 — `sieve`(에라토스테네스의 체) · `jaccard`(자카드 유사도) · `enumerateSubsets`(부분집합 열거).
- 기준선 → 본체 → 희소 변형 → 응용 문제 순으로, **먼저 만들어 보고 무엇이 문제인지 본 다음** 고친다.
- 응용으로 따져볼 것: 꼬리 비트가 `set()` 에는 없고 `flipAll()` 에만 생기는 이유와 정리 마스크 자체의 함정 둘 · `and(other)` 의 비용이 상대 타입에 따라 64배 갈리는 것 · `1L << bit` 만 써도 우연히 맞지만 `bit & 63` 을 명시하는 이유 · `nextSetBit` 의 "크기 밖이면 -1" 이 `trimTail` 덕에 도달 불가라는 것(11번 `h2 == 0`, 16번 "뿌리를 빨갛게" 에 이어 **세 번째**) · 체의 `p*p` 가 답이 아니라 비용만 바꾼다는 것 · 자카드의 0/0 을 안 정하면 `NaN` 이 조용히 퍼지는 것 · 부분집합 열거의 종료 조건 함정.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

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

먼저 알아야 할 것 세 줄:

- *워드(word)*: CPU가 한 번에 다루는 정수 한 덩어리. 여기선 long = 64비트.
- *시프트(`>>>`, `<<`)*: 비트를 왼쪽/오른쪽으로 미는 연산. `i >>> 6`은 64로 나눈 몫, `1L << k`는 k번 자리만 1인 수를 만든다.
- *마스크(mask)*: 원하는 자리만 1로 켠 값. 이걸 AND/OR/XOR로 겹쳐 "그 자리만" 읽거나 고친다.

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

**언제 쓰나**: 비트 하나를 켜고(set)·읽고(get)·끄고(clear)·뒤집을(flip) 때. 네 동작 모두 같은 두 걸음이다 — ① 비트가 든 워드를 찾고 ② 마스크를 겹친다.

- *OR(`|`)*: 둘 중 하나라도 1이면 1 → 켜기에 쓴다. *AND(`&`)*: 둘 다 1이어야 1 → 읽기·끄기에. *XOR(`^`)*: 다르면 1 → 뒤집기에.
- *멱등*: 같은 일을 두 번 해도 결과가 한 번 한 것과 같다는 뜻. set을 두 번 해도 그냥 켜져 있다.

아래 그림 [1]~[4]가 각각 전 상태 → 마스크 → 후 상태다.

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

**언제 쓰나**: 두 비트셋을 통째로 합치거나(합집합) 공통만 남기거나(교집합) 뺄 때. 비트 i가 "원소 i가 집합에 있다"를 뜻하므로, 비트 연산이 곧 집합 연산이 된다.

한 줄 요약 그림 — 전 상태 → 조작 → 후 상태:

```text
  전: 집합 A = 10110         조작: 워드끼리 & 한 번        후: A = 교집합으로 바뀜
      집합 B = 11010    ->   (64자리가 동시에 계산)   ->       A = 10010
                              A &= B                          (A에 제자리 덮어쓰기)
```

아래 그림이 워드 배열 전체에 이걸 적용하는 모습과, 꼬리 정리(trimTail)가 왜 필요한지다.

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

**언제 쓰나**: 자리는 100만 개인데 켜진 비트는 몇 개뿐일 때. "0이 아닌 워드만" 지도에 담아 빈 워드의 메모리를 아예 안 쓴다.

- *희소(sparse)*: 거의 다 비어 있고 값이 띄엄띄엄만 있다는 뜻.
- *TreeMap*: 키를 정렬된 순서로 담는 맵(내부는 레드-블랙 트리). "다음 켜진 워드"를 순서대로 찾을 수 있어 배열 대신 쓴다.
- *박싱(boxing)*: int·long 같은 원시값을 Integer·Long 객체로 감싸는 것. 감쌀 때마다 부가 메모리가 붙는다 — 엔트리당 48바이트의 출처.

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

## 용어 풀이

- **비트(bit) / 바이트(byte)**: 0 아니면 1인 정보의 최소 단위 / 비트 8개 묶음. boolean 한 칸은 1바이트를 쓰므로 정보 1비트당 8배 낭비다.
- **비트셋**: "켜짐/꺼짐" 나열을 비트 단위로 꽉꽉 눌러 담은 자료구조. 메모리 1/8, 집합 연산 반복 1/64.
- **워드(word)**: CPU가 한 번에 다루는 정수 한 덩어리. 이 구현에선 long = 64비트.
- **마스크(mask)**: 원하는 자리만 1로 켠 값. AND/OR/XOR로 겹쳐 그 자리만 읽거나 고친다.
- **AND(`&`) / OR(`|`) / XOR(`^`) / NOT(`~`)**: 비트 연산. 둘 다 1일 때 1 / 하나라도 1이면 1 / 다르면 1 / 전부 뒤집기. 집합으로 읽으면 교집합·합집합·대칭차·여집합.
- **andNot(`&~`)**: this에서 other에 있는 것을 빼는 차집합 연산.
- **시프트(`<<`, `>>>`)**: 비트를 옆으로 미는 연산. `1L << k`는 k번 자리만 1인 마스크, `i >>> 6`은 i를 64로 나눈 몫(워드 번호).
- **`i & 63`**: 64로 나눈 나머지를 비트 연산으로 구하는 관용구(64가 2의 거듭제곱이라 가능).
- **멱등**: 같은 일을 두 번 해도 한 번 한 것과 결과가 같다는 성질. OR로 켜기가 그렇다.
- **꼬리 비트(trimTail)**: size가 64의 배수가 아닐 때 마지막 워드에 남는 "존재하지 않는 자리". flipAll 등으로 여기에 1이 서면 개수가 틀어지므로 늘 0으로 꺼둔다.
- **popcount / `Long.bitCount`**: 켜진 비트의 개수를 세는 CPU 명령/메서드. cardinality가 이걸 워드마다 부른다.
- **`Long.numberOfTrailingZeros`**: 가장 낮은 켜진 비트가 몇 번 자리인지 알려주는 메서드. nextSetBit에 쓴다.
- **cardinality**: 집합의 크기, 즉 켜진 비트의 총 개수.
- **희소(sparse)**: 거의 다 0이고 값이 띄엄띄엄만 있는 상태. SparseBitSet의 전제.
- **TreeMap**: 키가 정렬된 순서로 유지되는 맵(내부는 레드-블랙 트리). 탐색·삽입 O(log n), tailMap으로 "이 키 이후 첫 엔트리"를 바로 찾는다.
- **박싱(boxing)**: 원시값(int·long)을 객체(Integer·Long)로 감싸는 것. 객체 머리말 때문에 메모리가 몇 배로 붙는다.
- **캐시 지역성**: CPU 옆의 작고 빠른 임시 메모리(캐시)에 데이터가 들어가면 훨씬 빠르다는 성질. 비트셋은 작아서 캐시에 통째로 들어가기 쉽다.
- **에라토스테네스의 체**: n 이하의 소수를 "배수 지우기"로 찾는 고전 알고리즘. 지웠는지 표시가 비트 하나면 충분해 비트셋의 대표 쓰임.
- **자카드 유사도**: 두 집합이 얼마나 겹치는가 = 교집합 크기 ÷ 합집합 크기. 0(전혀 다름)~1(완전 같음).
- **비트마스크 DP**: "어떤 원소를 골랐나"를 비트들로 표현해 정수 하나를 상태로 쓰는 동적 계획법. 부분집합 열거 관용구가 여기 쓰인다.
- **O(1) / O(n)**: 데이터가 n개일 때 걸리는 시간의 눈금. O(1)=항상 일정, O(n)=n에 비례. O(n/64)도 O(n)이지만 상수가 64배 작다.
