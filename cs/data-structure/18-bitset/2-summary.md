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
