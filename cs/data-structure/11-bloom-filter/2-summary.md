# data-structure/11-bloom-filter — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — ProbabilisticSet (`src/main/java/com/datastructure/bloom/ProbabilisticSet.java`)

- `void add(T item)`
- `boolean mightContain(T item)`
- `long insertedCount()`
- `long bitSize()`
- `double expectedFalsePositiveRate()`
- `void clear()`

## 구현 — BloomFilter (`src/main/java/com/datastructure/bloom/BloomFilter.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

```
BloomFilter — 원소를 저장하지 않는다. "봤다"는 흔적만 비트로 남긴다
+---------------------------------------------------------------+
| bits = m        비트 개수                                      |
| hashCount = k   원소 하나가 세우는 비트 수                       |
| capacity = n    예상 삽입 개수 (생성자 입력)                     |
| words           long[] — 길이 (bits + 63) / 64                 |
| inserted        add 를 부른 횟수                                |
+---------------------------------------------------------------+

    words[0]  (64 비트)                              words[1]
    +---------------------------------------+   +-------------------------
    | 0 0 1 0 0 0 0 1 0 0 0 1 0 0 0 0 ...   |   | 0 0 1 0 0 0 ...
    +---------------------------------------+   +-------------------------
    idx  0 1 2 3 4 5 6 7 8 9 ...                idx 64 65 66 ...

    비트 하나 다루기 (BitSet 도 boolean[] 도 아니고 long[] 을 직접 다룬다)
        어느 long 인가   idx >>> 6      (= idx / 64)
        그 안 몇 번째    idx & 63       (= idx % 64)
        세우기           words[idx >>> 6] |= 1L << (idx & 63)
        읽기             (words[idx >>> 6] & (1L << (idx & 63))) != 0

    키도 값도 저장하지 않는다. 여기서 세 가지가 따라 나온다
        (1) 메모리가 원소 크기와 무관하다 — 1KB 짜리 문자열이든 세 글자든 비트 k 개
        (2) 원소를 되꺼낼 수 없다. 물을 수 있는 것은 "아마 있다 / 확실히 없다" 뿐이다
        (3) 지울 수 없다 — 비트를 내리면 그 비트를 함께 쓰던 다른 원소까지 지워진다

    크기 정하기 (생성자가 예상 개수 n 과 목표 오탐률 p 로 계산한다)
        m = ceil( -n * ln(p) / (ln 2)^2 )       필요한 비트 수
        k = max(1, round( m / n * ln 2 ))       원소당 세울 비트 수
        p 를 낮추면 m 이 커지고, m/n 이 커지면 k 도 커진다
```

### 동작 — k 개 자리 고르기

```
indexes(item) : 해시 함수를 k 개 만들지 않는다. 64비트 해시 하나를 반으로 갈라 쓴다 (이중 해싱)

    (1) h = mix64(item.hashCode())      splitmix64 — 32비트 해시를 64비트로 고루 흩는다
                            64 bits
        +--------------------------------+--------------------------------+
        |            상위 32             |             하위 32            |
        +--------------------------------+--------------------------------+
                        |                                 |
                        v                                 v
                h2 = (int)(h >>> 32)                 h1 = (int) h
                h2 == 0 이면 1 로 바꾼다
                (0 이면 i 를 아무리 바꿔도 늘 같은 자리를 가리켜 k 개가 한 점에 뭉친다)

    (2) i = 0 .. k-1 에 대해
            out[i] = Math.floorMod(h1 + i * h2, bits)

        h1 에서 출발해 h2 씩 건너뛰며 k 개 자리를 고른다
            i=0 : h1
            i=1 : h1 + h2
            i=2 : h1 + 2*h2   ...
        % 가 아니라 floorMod 인 이유 : h1 + i*h2 가 int 오버플로로 음수가 되기 때문이다
        (음수를 % 하면 음수 인덱스가 나온다)

    해시를 진짜로 k 번 계산하는 것과 통계적으로 거의 같은 성질을 내면서, 계산은 한 번만 한다
```

### 동작 — 추가와 조회

```
add(item) — 예시로 k = 3, bits = 16
    indexes("cat") = [ 2, 7, 11 ]
    before  idx  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
                 0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
    after        0  0  1  0  0  0  0  1  0  0  0  1  0  0  0  0
                       ^              ^           ^
    words[idx >>> 6] |= 1L << (idx & 63);   inserted++;
    이미 켜진 비트를 또 켜도 그대로다 -> 같은 원소를 두 번 넣어도 상태가 변하지 않는다
    (inserted 만 올라간다 — 그래서 inserted 는 "서로 다른 원소 수"가 아니다)

mightContain(item) : k 자리를 확인하다 하나라도 0 이면 즉시 false
    현재 상태   idx  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
                     0  0  1  0  0  0  0  1  0  0  0  1  0  0  0  0

    mightContain("dog"),  indexes = [ 4, 7, 15 ]
        idx 4 -> 0        <- 여기서 즉시 false. 나머지 자리는 보지도 않는다
        "확실히 없다" — 넣었다면 이 비트가 반드시 켜져 있었을 것이기 때문이다.
        거짓 음성(있는데 없다고 답하기)은 원리상 일어나지 않는다

    mightContain("cat"),  indexes = [ 2, 7, 11 ]
        2 -> 1,  7 -> 1,  11 -> 1       전부 켜짐 -> true
```

### 동작 — 위양성이 생기는 순간

```
"cat"[2, 7, 11] 과 "dog"[4, 7, 15] 를 넣은 상태
    idx  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
         0  0  1  0  1  0  0  1  0  0  0  1  0  0  0  1
               ^     ^        ^           ^           ^
             cat   dog    cat+dog 공용    cat        dog
                          (7번은 둘이 함께 쓴다)

이제 넣은 적 없는 "cow" 를 묻는다.  indexes("cow") = [ 4, 11, 15 ]
    idx  4 -> 1     (dog 가 켠 것)
    idx 11 -> 1     (cat 이 켠 것)
    idx 15 -> 1     (dog 가 켠 것)
    전부 켜져 있다 -> true 를 돌려준다. 그런데 "cow" 는 넣은 적이 없다

    남이 켜 둔 비트를 빌려 입어 우연히 세 자리가 다 채워진 것이다.
    그래서 답은 "아마 있다"이지 "있다"가 아니다

    전부 1        -> 아마 있다   (틀릴 수 있다 = 위양성)
    하나라도 0    -> 확실히 없다 (절대 틀리지 않는다)

    이 비대칭이 블룸 필터의 전부다. 그래서 쓰는 곳도 정해져 있다 —
    "없으면 비싼 조회를 건너뛴다" 같은 앞단 거름망. 있다고 나오면 실제 저장소를 확인하면 된다

    넣을수록 1 이 늘어 위양성률이 오른다
        expectedFalsePositiveRate = (1 - e^(-k * inserted / m))^k
        비트가 절반쯤 켜졌을 때가 대략 최적점이고, k 는 그 지점을 노려 계산된 값이다
```

### `필드`

- `private final int bits` — 역할:
- `private final int hashCount` — 역할:
- `private final int capacity` — 역할:
- `private final long[] words` — 역할:
- `private long inserted` — 역할:

### `BloomFilter(int expectedInsertions, double falsePositiveRate)`

- 하는 일:
- 논리:
- 비용(왜):

### `static int optimalBits(int n, double p)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `static int optimalHashCount(int m, int n)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int[] indexes(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void add(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean mightContain(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `long insertedCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long bitSize()`

- 하는 일:
- 논리:
- 비용(왜):

### `double expectedFalsePositiveRate()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — CountingBloomFilter (`src/main/java/com/datastructure/bloom/CountingBloomFilter.java`)

### 구조 — 비트 대신 계수기

```
CountingBloomFilter — 비트 1개를 계수기 1바이트로 바꾼다. 그래서 삭제가 된다
    counters   byte[] — 길이 = bits. 계수기 하나가 8비트다 (니블 패킹은 하지 않는다)
    MAX_COUNT = 255,  bitsPerSlot() = 8,  bitSize() = bits * 8
    -> 원본 블룸 필터와 같은 자리 수를 쓰면서 메모리는 정확히 8배

    같은 자리를 "몇 명이 쓰는지"를 센다
        BloomFilter          idx 2  [ 1 ]      "누군가 켰다"만 안다
        CountingBloomFilter  idx 2  [ 3 ]      "셋이 이 자리를 쓴다"를 안다

    자리를 고르는 방식(mix64 + 이중 해싱)과 판정 규칙은 BloomFilter 와 똑같다
        mightContain : k 자리 중 하나라도 0 이면 즉시 false
```

### 동작 — 삭제와 포화

```
add(item)    : k 자리마다  c < 255 이면 c + 1
                           c == 255 면 올리지 않고 saturations++ 만 센다
remove(item) : 먼저 mightContain 으로 확인하고, false 면 아무것도 하지 않고 false 반환
               맞으면 k 자리마다  0 < c < 255 일 때만 c - 1,  inserted--

    remove("cat"),  indexes = [ 2, 7, 11 ]
    before   idx        2        7       11
             count    [ 3 ]    [ 1 ]    [ 2 ]
    after    idx        2        7       11
             count    [ 2 ]    [ 0 ]    [ 1 ]
                                 ^ 0 이 되었다 -> 이제 "확실히 없다" 판정에 쓰인다

    원본 블룸 필터에서 비트를 그냥 내렸다면
             idx        2        7       11
             bit      [ 1->0 ] [ 1->0 ] [ 1->0 ]
        2번과 11번을 함께 쓰던 다른 원소들까지 한꺼번에 없는 것이 된다.
        "몇 명이 쓰는지"를 세지 않으면 나 하나만 빼는 일이 불가능하다 — 그게 계수기를 두는 이유다

포화(saturation) — 255 에 닿은 자리는 다시 내려가지 않는다
             idx        2
             count    [ 255 ]        add 를 더 해도 그대로 (saturations++)
                      [ 255 ]        remove 를 해도 그대로 (얼어붙는다)

    왜 얼려 두나 — 올릴 때 멈춘 만큼은 내릴 때도 멈춰야 하기 때문이다.
    255 에서 멈춘 뒤에도 계속 내리면 실제 사용자 수보다 적게 세게 되고,
    결국 아직 쓰는 사람이 있는 자리가 0 이 되어 "있는데 없다"(거짓 음성)가 생긴다.
    블룸 필터가 주는 유일한 강한 보장이 "거짓 음성 없음"이므로 그것만은 지킨다.
    대신 그 자리는 영영 0 이 되지 못해 위양성 쪽으로만 손해를 본다 — 안전한 방향의 실패다
    saturations 계수기가 그런 일이 몇 번 있었는지 알려준다
```

### `필드`

- `static final int MAX_COUNT = 255` — 역할:
- `private final int bits` — 역할:
- `private final int hashCount` — 역할:
- `private final byte[] counters` — 역할:
- `private long inserted` — 역할:
- `private long saturations` — 역할:

### `CountingBloomFilter(int expectedInsertions, double falsePositiveRate)`

- 하는 일:
- 논리:
- 비용(왜):

### `void add(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean mightContain(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `long insertedCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long bitSize()`

- 하는 일:
- 논리:
- 비용(왜):

### `int bitsPerSlot()`

- 하는 일:
- 논리:
- 비용(왜):

### `double expectedFalsePositiveRate()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — ScalableBloomFilter (`src/main/java/com/datastructure/bloom/ScalableBloomFilter.java`)

### 구조 — 필터의 목록

```
ScalableBloomFilter — 하나가 차면 새 필터를 덧붙인다. 필터 하나가 아니라 필터의 목록이다
    TIGHTENING = 0.5   (새 필터의 목표 오탐률을 절반으로 조인다)
    GROWTH = 2         (새 필터의 용량을 2배로 늘린다)

    filters    [ 필터 0 ]      [ 필터 1 ]       [ 필터 2 ]      ...
    용량         n0             n0 * 2           n0 * 4
    목표 오탐률   p0             p0 * 0.5         p0 * 0.25
                (봉인됨)        (봉인됨)         (지금 쓰는 것)

    원본 BloomFilter 는 생성자에서 정한 m 과 k 를 바꿀 수 없다.
    예상보다 많이 넣으면 비트가 다 켜져 오탐률이 1 에 가까워진다.
    이미 켠 비트를 되돌릴 수 없으니 늘리는 방법은 "새 필터를 옆에 두는 것"뿐이다
```

### 동작 — 커지기와 조회

```
add(item) : 언제나 마지막 필터에만 쓴다
    마지막 필터를 보고
        insertedCount() < capacity()   ->  그 필터에 add
        꽉 찼다                        ->  grow() 로 새 필터를 덧붙이고 새 필터에 add

    before   [ 필터 0 : 꽉 참 ]
    after    [ 필터 0 : 꽉 참 ] [ 필터 1 : 방금 만든 것, 새 원소 ]

    앞 필터들은 다시 쓰이지 않는다 — 봉인된 채 읽기 전용이 된다.
    그래서 여기서도 삭제는 여전히 불가능하다

mightContain(item) : 앞에서부터 물어보다 하나라도 true 면 즉시 true (논리 OR)
    [ 필터 0 ] -> false
    [ 필터 1 ] -> true     =>  즉시 true, 필터 2 는 보지 않는다
    전부 false 여야 false

    조회 비용이 필터 개수에 비례해 늘어난다 — 무한히 커질 수 있다는 것의 대가가 이것이다

왜 오탐률을 절반씩 조이나
    전체 오탐률 = 1 - (1 - p0)(1 - p1)(1 - p2) ...
    새 필터를 같은 p 로 계속 붙이면 이 값이 1 로 몰려간다 (필터를 더할수록 나빠진다).
    p 를 절반씩 줄이면 등비급수라 합이 수렴한다 -> 필터를 무한히 붙여도 전체 오탐률이 유한하다.
    대신 뒤로 갈수록 같은 개수를 담는 데 더 많은 비트를 쓰게 된다 (조인 만큼 비싸진다)
```

### `필드`

- `static final double TIGHTENING = 0.5` — 역할:
- `static final int GROWTH = 2` — 역할:
- `private final List<BloomFilter<T>> filters` — 역할:
- `private final int initialCapacity` — 역할:
- `private final double initialFpr` — 역할:
- `private int nextCapacity` — 역할:
- `private double nextFpr` — 역할:
- `private long inserted` — 역할:

### `ScalableBloomFilter(int initialCapacity, double falsePositiveRate)`

- 하는 일:
- 논리:
- 비용(왜):

### `private void grow()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void add(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean mightContain(T item)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int filterCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long insertedCount()`

- 하는 일:
- 논리:
- 비용(왜):

### `long bitSize()`

- 하는 일:
- 논리:
- 비용(왜):

### `double expectedFalsePositiveRate()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| BloomFilter | | | |
| CountingBloomFilter | | | |
| ScalableBloomFilter | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/11-bloom-filter/README.md`
- 구현: `/home/jun/project/myway/data-structure/11-bloom-filter/src/main/java/com/datastructure/bloom/`
- 테스트: `/home/jun/project/myway/data-structure/11-bloom-filter/src/test/java/com/datastructure/bloom/`
- 참고 구현: `/home/jun/project/myway/data-structure/11-bloom-filter/impl/`
