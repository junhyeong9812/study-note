# data-structure/18-bitset — 정리 (힌트)

## 해결하는 문제

"켜짐/꺼짐" 100만 개를 Java `boolean[]`에 담으면 칸 하나가 1비트가 아니라 1바이트다 — 정보 1비트에 8비트를 쓴다.\
그런데 메모리 8배는 작은 문제다. 두 집합의 교집합을 구하려면 칸을 **하나씩** 100만 번 봐야 한다.

```text
boolean[8]  [1][0][0][1][0][0][0][0]   <- 8바이트, 교집합 = 칸 8번 비교
비트셋       10010000                   <- 1바이트, 교집합 = & 연산 1번

100만 비트:  boolean[]  1,000,000바이트 · 교집합 1,000,000걸음
             long[]       125,000바이트 · 교집합    15,625걸음   (한 걸음이 64비트)
```

비트셋은 켜짐/꺼짐을 64비트 정수(`long`)에 꽉꽉 눌러 담아, CPU 연산 한 번이 64칸을 동시에 처리하게 한다.\
쉬운 예: 방마다 다니며 불을 끄는 대신 64구짜리 스위치판을 탁 내린다.\
똑같은 구조다: 이 노트의 `WordBitSet`은 `long[]` 위에서 `i >>> 6`으로 워드를, `1L << (i & 63)`으로 자리를 찾는다.\
실무 예: DB 비트맵 인덱스 — "성별=남 AND 지역=서울 AND 등급=VIP"를 행을 하나씩 보는 대신 조건별 비트맵을 `and`해 워드 단위로 접는다.

  - *워드(word)*: CPU가 한 번에 다루는 정수 한 덩어리. 여기서는 `long` = 64비트.

### 한눈에 — 쉽게 말하면

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

## 동작·원리

### 전체 흐름

```text
[1] 자리 찾기: 비트 번호 i -> (워드, 자리)         [2] 켜기·끄기·읽기 = 마스크 하나
    워드 번호 = i >>> 6   (i / 64)                   mask = 1L << (i & 63)
    자리     = i & 63     (i % 64)                    set  : words[w] |=  mask
    i = 70 -> 워드 1, 자리 6                           clear: words[w] &= ~mask
    +--------64--------+--------64--------+            get  : (words[w] & mask) != 0
    | word 0           | word 1   ^자리 6  |            flip : words[w] ^=  mask
              |
              v
[3] 집합 연산 = 워드끼리 한 번에                     [4] 세기·건너뛰기
    and : words[k] &= other.words[k]    (k = 0..W-1)   cardinality : 워드마다 Long.bitCount (popcount)
    or  : |=     xor : ^=     andNot : &= ~            nextSetBit  : 0 인 워드는 통째로 건너뛰고
    걸음 수 = 워드 수 = n/64                                         Long.numberOfTrailingZeros 로 자리
              |
              v
[5] 꼬리 비트 (size 70 = 워드 2개 = 128비트, 58비트가 남는다)
    set() 은 범위 검사로 못 켜지만 flipAll() 은 워드째 뒤집어 켠다
    -> trimTail : 마지막 워드에 정리 마스크를 걸어 size 밖을 0 으로
                                                   [6] 희소하면: SparseBitSet — 0 이 아닌 워드만 TreeMap 에
```

- [1] 비트 번호 하나를 "몇 번째 워드의 몇 번째 자리"로 쪼갠다. 64가 2의 거듭제곱이라 나눗셈·나머지가 시프트·AND 한 번이다.
- [2] 읽기·켜기·끄기·뒤집기는 그 자리만 1인 마스크를 OR·AND·XOR로 겹치는 것이다. 전부 O(1).
- [3] 집합 연산은 워드끼리 한 번에 한다. 반복 횟수가 n이 아니라 n/64다 — 메모리보다 이것이 진짜 이유다.
- [4] 개수는 워드마다 popcount 명령 하나, "다음 켜진 비트"는 0인 워드를 통째로 건너뛴다.
- [5] 워드를 통째로 다루는 연산은 size 밖 자리까지 켠다. 정리 마스크가 그것을 지우고, 그 마스크 자체에도 함정이 둘 있다.
- [6] 켜진 비트가 워드의 1/6 미만이면 0인 워드의 자리마저 아까워 지도에 켜진 워드만 담는다.

### 계약 — BitVector (`src/main/java/com/datastructure/bitset/BitVector.java`)

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

### 구현 — BooleanArrayBitSet (`src/main/java/com/datastructure/bitset/BooleanArrayBitSet.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

#### 구조

```text
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

#### `필드`

- `boolean[] bits` 역할:

#### `public BooleanArrayBitSet(int size)`

- 하는 일:
- 비용(왜):

#### `public int cardinality()` (TODO)

- 하는 일:
- 논리(배열을 전부 훑는 수밖에 없는 이유):
- 비용(왜):

#### `public boolean get(int index)` / `public void set(int index)` / `public void set(int index, boolean value)` / `public void clear(int index)` / `public void flip(int index)`

- 하는 일:
- 비용(왜):

#### `public void clearAll()` / `public void flipAll()`

- 하는 일:
- 비용(왜):

#### `public boolean isEmpty()` / `public int nextSetBit(int from)`

- 하는 일:
- 비용(왜):

#### `public void and(BitVector other)` / `or` / `xor` / `andNot`

- 하는 일:
- 논리:
- 비용(왜):

#### `public List<Integer> toList()` / `public int size()` / `public int unitCount()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

### 구현 — WordBitSet (`src/main/java/com/datastructure/bitset/WordBitSet.java`)

#### 구조

먼저 알아야 할 것 세 줄:

- *워드(word)*: CPU가 한 번에 다루는 정수 한 덩어리. 여기선 long = 64비트.
- *시프트(`>>>`, `<<`)*: 비트를 왼쪽/오른쪽으로 미는 연산. `i >>> 6`은 64로 나눈 몫, `1L << k`는 k번 자리만 1인 수를 만든다.
- *마스크(mask)*: 원하는 자리만 1로 켠 값. 이걸 AND/OR/XOR로 겹쳐 "그 자리만" 읽거나 고친다.

```text
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

#### 동작 — 켜고 끄고 읽기

**언제 쓰나**: 비트 하나를 켜고(set)·읽고(get)·끄고(clear)·뒤집을(flip) 때. 네 동작 모두 같은 두 걸음이다 — ① 비트가 든 워드를 찾고 ② 마스크를 겹친다.

- *OR(`|`)*: 둘 중 하나라도 1이면 1 → 켜기에 쓴다. *AND(`&`)*: 둘 다 1이어야 1 → 읽기·끄기에. *XOR(`^`)*: 다르면 1 → 뒤집기에.
- *멱등*: 같은 일을 두 번 해도 결과가 한 번 한 것과 같다는 뜻. set을 두 번 해도 그냥 켜져 있다.

아래 그림 [1]~[4]가 각각 전 상태 → 마스크 → 후 상태다.

```text
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

#### 동작 — 집합 연산

**언제 쓰나**: 두 비트셋을 통째로 합치거나(합집합) 공통만 남기거나(교집합) 뺄 때. 비트 i가 "원소 i가 집합에 있다"를 뜻하므로, 비트 연산이 곧 집합 연산이 된다.

한 줄 요약 그림 — 전 상태 → 조작 → 후 상태:

```text
  전: 집합 A = 10110         조작: 워드끼리 & 한 번        후: A = 교집합으로 바뀜
      집합 B = 11010    ->   (64자리가 동시에 계산)   ->       A = 10010
                              A &= B                          (A에 제자리 덮어쓰기)
```

아래 그림이 워드 배열 전체에 이걸 적용하는 모습과, 꼬리 정리(trimTail)가 왜 필요한지다.

```text
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

#### `필드`

- `static final int BITS_PER_WORD = 64` 역할:
- `int size` 역할:
- `long[] words` 역할:
- 꼬리 비트(size 가 64의 배수가 아닐 때 남는 자리)가 문제가 되는 이유:

#### `public WordBitSet(int size)`

- 하는 일:
- 비용(왜):

#### `static int wordCountFor(int size)` (TODO)

- 하는 일:
- 논리(올림 나눗셈):
- 비용(왜):

#### `static int wordIndex(int bit)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `static long mask(int bit)` (TODO)

- 하는 일:
- 논리(`bit & 63` 을 명시하는 이유 — 자바 시프트가 자동으로 나머지를 쓴다는 것):
- 비용(왜):

#### `public int cardinality()` (TODO)

- 하는 일:
- 논리(popcount):
- 비용(왜):

#### `public int nextSetBit(int from)` (TODO)

- 하는 일:
- 논리(꺼진 워드를 통째로 건너뛰는 것 · "크기 밖이면 -1" 검사가 도달 불가라는 기록):
- 비용(왜):

#### `public void and(BitVector other)` (TODO)

- 하는 일:
- 논리(상대 타입에 따라 워드 단위 / 비트 단위로 갈리는 이유):
- 비용(왜):

#### `private void trimTail()` (TODO)

- 하는 일:
- 논리(정리 마스크 자체의 함정):
- 비용(왜):

#### `public void flipAll()` (TODO)

- 하는 일:
- 논리(왜 여기서 꼬리 정리가 필요해지는가):
- 비용(왜):

#### `public boolean get(int index)` / `public void set(int index)` / `public void set(int index, boolean value)` / `public void clear(int index)` / `public void flip(int index)`

- 하는 일:
- 비용(왜):

#### `public void clearAll()` / `public boolean isEmpty()`

- 하는 일:
- 비용(왜):

#### `public void or(BitVector other)` / `xor` / `andNot`

- 하는 일:
- 논리:
- 비용(왜):

#### `public List<Integer> toList()` / `public int size()` / `public int unitCount()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

### 구현 — SparseBitSet (`src/main/java/com/datastructure/bitset/SparseBitSet.java`)

#### 구조

**언제 쓰나**: 자리는 100만 개인데 켜진 비트는 몇 개뿐일 때. "0이 아닌 워드만" 지도에 담아 빈 워드의 메모리를 아예 안 쓴다.

- *희소(sparse)*: 거의 다 비어 있고 값이 띄엄띄엄만 있다는 뜻.
- *TreeMap*: 키를 정렬된 순서로 담는 맵(내부는 레드-블랙 트리). "다음 켜진 워드"를 순서대로 찾을 수 있어 배열 대신 쓴다.
- *박싱(boxing)*: int·long 같은 원시값을 Integer·Long 객체로 감싸는 것. 감쌀 때마다 부가 메모리가 붙는다 — 엔트리당 48바이트의 출처.

```text
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

#### `필드`

- `static final int BYTES_PER_ENTRY = 48` 역할:
- `int size` 역할:
- `TreeMap<Integer, Long> words` 역할:
- 손익분기(워드의 1/6 미만이 켜질 때 유리하다)의 근거:

#### `public SparseBitSet(int size)`

- 하는 일:
- 비용(왜):

#### `public void set(int index)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

#### `public void clear(int index)` (TODO)

- 하는 일:
- 논리(워드가 비면 맵에서 지우는 이유):
- 비용(왜):

#### `public int nextSetBit(int from)` (TODO)

- 하는 일:
- 논리(있는 워드만 순서대로 보는 것 — TreeMap 이 필요한 이유):
- 비용(왜):

#### `public boolean get(int index)` / `public void set(int index, boolean value)` / `public void flip(int index)`

- 하는 일:
- 비용(왜):

#### `public void clearAll()` / `public void flipAll()`

- 하는 일:
- 논리(flipAll 이 희소성을 깨뜨리는 것):
- 비용(왜):

#### `public int cardinality()` / `public boolean isEmpty()`

- 하는 일:
- 비용(왜):

#### `public void and(BitVector other)` / `or` / `xor` / `andNot`

- 하는 일:
- 비용(왜):

#### `public List<Integer> toList()` / `public int size()` / `public int unitCount()` / `public long memoryBytes()`

- 하는 일:
- 비용(왜):

## 쓰이는 자료구조·알고리즘

- **Java `java.util.BitSet`** — `long[]` 위의 표준 구현. `and`·`or`·`cardinality`·`nextSetBit`이 이 노트의 `WordBitSet`과 같은 모양이다.
- **DB 비트맵 인덱스·비트맵 스캔** — 카디널리티가 낮은 컬럼(성별·지역·등급)의 조건별 비트맵을 `and`/`or`해 여러 조건을 워드 단위로 접는다. Oracle의 비트맵 인덱스는 이 비트맵을 디스크에 저장해 두는 쪽이고, PostgreSQL은 비트맵 인덱스를 저장하지 않는 대신 비트맵 힙 스캔에서 여러 인덱스의 결과를 조회 시점에 메모리 비트맵으로 만들어 `and`/`or`한다.
- **Roaring Bitmap** — 희소·조밀 구간을 컨테이너별로 다르게 담는 압축 비트맵. Lucene/Elasticsearch(문서 ID 집합)·ClickHouse(`groupBitmap` 함수)·Spark·Druid 등이 쓴다(roaringbitmap.org 사용처 목록). 이 노트의 `SparseBitSet`이 그 발상의 가장 단순한 형태다.
- **운영체제의 할당 비트맵** — 파일시스템의 블록·inode 비트맵([33-filesystem](../33-filesystem/2-summary.md)), 페이지 할당기의 free 비트맵([35-allocator](../35-allocator/2-summary.md)). "비어 있는 칸 찾기"가 `nextSetBit`이다.
- **[11-bloom-filter](../11-bloom-filter/2-summary.md)** — 비트 배열을 쓰기만 하고 안 가르쳤던 곳. k개의 해시 자리를 켜고 읽는 것이 `set`·`get`이다.
- **권한·상태 플래그** — Unix 파일 모드(`rwx`), Java `Modifier`, 소켓 옵션처럼 "켜짐/꺼짐 여러 개"를 정수 하나에 담고 마스크로 검사한다.
- **비트마스크 DP·집합 열거** — 외판원 문제·집합 분할처럼 "부분집합"을 정수 하나로 표현하고 `(s - 1) & mask`로 열거한다. [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md) · [algorithm/22-dp-advanced](../../algorithm/22-dp-advanced/2-summary.md).
- **에라토스테네스의 체·집합 유사도** — 100만까지 소수 표가 125KB로 캐시에 들어가고, 추천 시스템의 자카드 유사도가 `and`·`or`·popcount 세 번이다.

## 적용 — 풀어나가는 법

비트셋 문제는 "이 집합을 워드 단위로 접을 수 있는가"에서 갈린다.\
순서: ① 원소가 0..n-1 정수로 번호 매겨지고 "있다/없다"만 필요한지 확인한다 — 값이 붙거나 번호 공간이 너무 크면 해시맵(05)이나 희소 변형이다 → ② 켜진 비율을 본다 — 워드의 1/6 미만이면 `SparseBitSet`, 아니면 `WordBitSet` → ③ 집합 연산(교집합·합집합·차집합·세기)을 워드 루프 하나로 쓴다 → ④ 워드를 통째로 다루는 연산(`flipAll`·`and`의 상대 타입) 뒤에 size 밖 자리가 켜지지 않았는지 정리한다 → ⑤ 0/0 같은 정의되지 않는 경계를 먼저 못 박는다.\
아래 과제(기준선 → 본체 → 희소 변형 → 응용 문제 3개)가 이 순서다.

### 문제 — 이 챕터가 시키는 것

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

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BooleanArrayBitSet (`boolean[]`) | | | |
| WordBitSet (`long[]`) | | | |
| SparseBitSet (켜진 워드만 TreeMap 에) | | | |

### 문제 — BitSetProblems (`src/main/java/com/datastructure/bitset/BitSetProblems.java`)

#### 문제 1. 에라토스테네스의 체 — `static BitVector sieve(int n)`

> 문제 설명: n 이하의 소수를 전부 찾는다. 반환한 비트셋의 i번 비트가 켜져 있으면 i 가 소수다.
> 비트셋의 고전적인 쓰임이다. 100만까지면 `boolean[]` 은 1MB, 비트셋은 125KB 다.
> 캐시에 들어가느냐 마느냐가 갈리는 크기다.
> (n < 2 이면 IllegalArgumentException)

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 2. 자카드 유사도 — `static double jaccard(BitVector a, BitVector b)`

> 문제 설명: 두 비트셋의 자카드 유사도(교집합 크기 / 합집합 크기)를 구한다.
> 둘 중 하나라도 null 이면 IllegalArgumentException, 크기가 다르면 IllegalArgumentException.
> 생각할 것: 둘 다 비었을 때 이 값은 무엇으로 정의되는가.

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 3. 부분집합 열거 — `static List<Integer> enumerateSubsets(int mask)`

> 문제 설명: 마스크의 모든 부분집합을 내림차순으로 열거한다.
> 0부터 mask 까지 전부 돌며 `(i & mask) == i` 를 검사하면 2^32 번이다.
> 관용구를 쓰면 부분집합 개수만큼만 돈다. 켜진 비트가 4개면 16번이다.
> 쓰이는 곳: 비트마스크 DP(외판원 문제, 집합 분할), 조합 최적화.
> (mask < 0 이면 IllegalArgumentException)

- 내 접근:
- 논리:
- 비용(왜):

## 장애 시나리오와 대처

**1. 번호 공간이 큰 희소 ID에 고정 비트셋 — 메모리가 터진다**

- 현상: 사용자 ID(최대 20억)마다 "오늘 접속했는가"를 비트셋으로 뒀더니 비트셋 하나가 수백 MB이고, 세그먼트(그룹)마다 하나씩 두자 `OutOfMemoryError`가 난다.
- 보이는 형태: 켜진 비트는 몇만 개뿐인데 `memoryBytes()`가 `size / 8`(2³¹비트면 256MB)로 고정이다. 힙 덤프에 거대한 `long[]`이 여럿 보인다.
- 원인: 고정 비트셋의 메모리는 켜진 개수가 아니라 **번호 공간**에 비례한다. 0인 워드도 자리를 차지한다.
- 대처: 켜진 워드만 담는 `SparseBitSet`, 또는 구간별로 담는 방식을 바꾸는 Roaring 계열 압축 비트맵을 쓴다(2¹⁶개씩 끊은 구간마다 배열·비트맵·연속 구간 중 작은 쪽으로 담는다). ID를 조밀한 번호로 다시 매기는(재번호) 것도 답이다. 손익분기는 워드의 1/6이다(정답 8번 참고).

**2. `int` 시프트와 부호 확장 — 엉뚱한 비트가 켜지거나 음수 인덱스가 난다**

- 현상: 32번 이상 자리만 조용히 틀리거나, 음수 인덱스가 들어왔을 때 `ArrayIndexOutOfBoundsException: -1`처럼 음수 워드 번호가 난다.
- 보이는 형태: `1 << 40`을 마스크로 썼더니 40번이 아니라 8번 자리가 켜진다. `i >> 6`을 워드 번호로 썼더니 음수 `i`에서 음수 워드 번호가 나온다. 테스트는 작은 인덱스만 돌려서 통과한다.
- 원인: Java의 `int` 시프트는 시프트 수를 32로 나눈 나머지만 쓴다 — `1 << 40`은 `1 << 8`이다. `long`이 필요한 자리에 `int` 리터럴(`1`)을 썼다. `>>`는 부호를 그대로 끌어와 음수를 음수로 두고(부호 확장), `>>>`만 0을 채운다.
  - *부호 확장(sign extension)*: 오른쪽 시프트에서 맨 왼쪽(부호) 비트를 복사해 채우는 것. 음수가 음수로 남는다.
- 대처: 마스크는 늘 `1L << (i & 63)`으로 쓴다 — `L`과 `& 63`을 둘 다 명시한다(`& 63`은 우연히 맞는 코드를 확신할 수 있는 코드로 바꾼다). 워드 번호는 `>>>`로, 그리고 인덱스 범위 검사를 진입점에서 한다. 63번·64번·127번 같은 경계 인덱스를 테스트에 넣는다.

**3. 동시 갱신에서 비트가 사라진다 — 읽고-고치고-쓰기 경쟁**

- 현상: 여러 스레드가 같은 비트셋에 `set`을 부르는데, 켜져야 할 비트가 가끔 꺼진 채 남는다. 예외는 없다.
- 보이는 형태: `cardinality()`가 켠 횟수보다 작다. 단일 스레드에서는 재현이 안 된다.
- 원인: `words[w] |= mask`는 한 명령이 아니다 — 읽고, OR하고, 다시 쓴다. 두 스레드가 같은 워드를 동시에 읽으면 나중에 쓴 쪽이 앞의 갱신을 덮는다(lost update). 비트 64개가 한 워드에 있어 **다른 비트**를 켜도 충돌한다.
- 대처: 워드마다 `AtomicLongArray`의 CAS(`compareAndSet`) 루프로 갱신하거나, 비트셋을 스레드마다 따로 만들고 마지막에 `or`로 합친다. `java.util.BitSet`은 스레드 안전하지 않다는 것을 문서가 명시한다.
  - *CAS(compare-and-swap)*: "내가 읽은 값이 아직 그대로면 새 값으로 바꿔라"를 한 번에 하는 원자 명령. 실패하면 다시 읽어 재시도한다.

## 핵심 문장

- 비트셋의 진짜 이유는 메모리 1/8이 아니라 걸음 수 1/64다 — `a[i] & b[i]` 하나가 비트 64개를 처리하고, popcount 하나가 64개를 세고, 0인 워드는 통째로 건너뛴다.
- 비트 번호 하나는 "워드 번호(`i >>> 6`)와 자리(`i & 63`)"로 쪼개지고, 읽기·켜기·끄기·뒤집기는 그 자리만 1인 마스크를 겹치는 것이다.
- 워드를 통째로 다루는 연산은 size 밖의 꼬리 비트까지 켠다 — `set()`에는 없는 문제가 `flipAll()`에서 생기고, 정리 마스크가 그것을 지운다.
- 메모리는 켜진 개수가 아니라 번호 공간에 비례한다 — 켜진 비트가 워드의 1/6 미만이면 0인 워드마저 아까워 `SparseBitSet`으로 간다.
- `1L`·`& 63`·`>>>`처럼 우연히 맞는 코드를 확신할 수 있는 코드로 바꾸는 습관이 이 구조에서 특히 중요하다 — 테스트가 구별하지 못하는 방어 코드가 여기서 세 번째로 나온다.

## 관련 주제·근거

- 선행 — [11-bloom-filter](../11-bloom-filter/2-summary.md): 비트 배열을 쓰기만 했던 곳. [17-fenwick-tree](../17-fenwick-tree/2-summary.md): 구조를 계산으로 대신한 데서, 값 자체를 비트로 눕히는 데로.
- 후속 — [19-probabilistic-counting](../19-probabilistic-counting/2-summary.md): "있다/없다"의 정확한 답을 확률로 바꾸면 빈도·카디널리티까지 넓어진다.
- 응용 — [33-filesystem](../33-filesystem/2-summary.md)(블록 비트맵) · [35-allocator](../35-allocator/2-summary.md)(free 비트맵) · [05-hashmap](../05-hashmap/2-summary.md)(번호 공간이 클 때의 대안).
- 기법 — [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)(마스크·시프트·popcount·`(s-1) & mask`) · [algorithm/22-dp-advanced](../../algorithm/22-dp-advanced/2-summary.md)(비트마스크 DP) · [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md)(에라토스테네스의 체).
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `35-bitset` (선행 `03-dynamic-array`).
- 교재 — Chambi 외, "Better bitmap performance with Roaring bitmaps", Software: Practice and Experience 46(5), 2016 · Java `java.util.BitSet` 문서.
- myway 원본 — `/home/jun/project/myway/data-structure/18-bitset/` (README.md · impl/WordBitSet.java · impl/SparseBitSet.java · impl/BitSetProblems.java).

### 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/18-bitset/README.md`
- 구현: `/home/jun/project/myway/data-structure/18-bitset/src/main/java/com/datastructure/bitset/`
- 테스트: `/home/jun/project/myway/data-structure/18-bitset/src/test/java/com/datastructure/bitset/`
- 정답 구현: `/home/jun/project/myway/data-structure/18-bitset/impl/`

### 용어 풀이

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
