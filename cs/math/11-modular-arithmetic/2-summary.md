# math/11-modular-arithmetic — 모듈러·GCD·모듈러 역원·빠른 거듭제곱, 그리고 언어별 나머지 — 정리 (힌트)

## 해결하는 문제

"나머지"는 백엔드 곳곳에서 칸 번호를 만든다. 샤드 번호, 해시 테이블 칸, 링 버퍼 위치, 순환하는 ID, 요일 계산이 다 그렇다.

```text
  수학의 나머지                    프로그램의 %
  −7 = 3·(−3) + 2  →  2            Java  : -7 % 3 == -1     (피제수 부호, JLS §15.17.3)
  0 ≤ r < |d|   (MCS 9.1.4)        Python: -7 % 3 ==  2     (제수 부호, Python 참조 6.7)
                                   같은 키, 같은 샤드 수인데 서비스마다 다른 샤드를 고른다
```

- 수학 정의와 언어 연산자가 다르다는 것을 모르면 음수에서 깨진다. 인덱스가 음수가 되거나, 두 언어의 서비스가 같은 키를 다른 샤드로 보낸다.
- 모듈러 산술의 성질(곱의 나머지 = 나머지의 곱, gcd와 역원)을 모르면 큰 수 거듭제곱이 조용히 넘치고, 특정 키 패턴이 몇 개 칸에만 몰린다.

쉬운 예: 시계다.
- 10시에서 5시간 뒤는 15시가 아니라 3시다. 12로 나눈 나머지만 본다.
- 2시에서 5시간 **전**은 −3시가 아니라 9시다. 나머지를 0~11에 넣어야 시계로 읽힌다.

똑같은 구조다.\
시계 칸 12개 = 샤드 n개, 시각 = 해시값, "5시간 전" = 음수 해시다. 시계로 읽으려면 floor 나머지(0~n−1)가 필요하다.

실무 예:
- `shards[key.hashCode() % n]`이 음수 해시를 가진 키에서만 `ArrayIndexOutOfBoundsException`을 낸다.
- `Math.abs(hash) % n`으로 고쳤는데 `hashCode()`가 `Integer.MIN_VALUE`인 키에서 여전히 음수가 나온다([algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) 실험: `"polygenelubricants"`).
- 키가 8의 배수뿐인 데이터를 칸 수 64(2의 거듭제곱)로 나누면 칸 8개만 쓴다.

## 동작·원리

### 1. 나눗셈 정리와 두 가지 "나머지"

```text
  나눗셈 정리 (MCS Theorem 9.1.4): d ≠ 0이면  n = q·d + r,  0 ≤ r < |d| 인 (q, r)이 유일하다

  수직선에서 −7 ÷ 3
     −9      −6      −3       0
  ────┼───────┼───────┼───────┼────
        ↑ −7
  floor(바닥) 몫: q = −3  (아래로 내림)  → r = −7 − (−9) =  2    Python %, Math.floorMod
  truncate(0쪽) 몫: q = −2 (0 쪽으로)    → r = −7 − (−6) = −1    Java·C의 /, %
```

| 식 | Java `/` `%` | `Math.floorDiv` `floorMod` | Python `//` `%` |
|---|---|---|---|
| −7, 3 | −2, **−1** | −3, **2** | −3, **2** |
| 7, −3 | −2, 1 | −3, **−2** | −3, **−2** |
| −7, −3 | 2, −1 | 2, −1 | 2, −1 |

- 두 언어 모두 "몫 × 제수 + 나머지 = 피제수"를 지킨다. Java는 `(a/b)*b + (a%b) == a`(JLS §15.17.3), Python은 `(a//b)*b + (a%b) == a`다(Python 참조 6.7 — Python 3의 `/`는 정수끼리도 실수 몫이라 `//`를 써야 한다). 다른 것은 몫을 어느 쪽으로 반올림하느냐다.
  - Java 정수 `/`: 0 쪽으로 버린다(JLS §15.17.2). 그래서 `%`의 부호는 **피제수**를 따른다.
  - Python `//`: 아래로 내린다. 그래서 `%`의 부호는 **제수**를 따른다(Python 참조: "always yields a result with the same sign as its second operand (or zero)").
  - `Math.floorMod(x, y)`: Python `%`와 같은 규칙. 결과 부호는 **제수 y**를 따른다(Java 21 `Math` 문서). 그래서 y > 0일 때만 0 ≤ r < y가 보장된다.
    - 흔한 오해: "`floorMod`는 항상 0 이상이다." 제수가 음수면 결과도 0 이하다(`floorMod(7, -3) == -2`, 아래 실험).

### 2. 합동과 Z_n — "나머지끼리 계산해도 된다"

```text
  mod 12 시계 = Z_12 = {0, 1, …, 11}
        0
    11     1
  10         2        10 + 5 ≡ 3   (mod 12)
   9         3        2 − 5  ≡ 9   (mod 12)
    8      4          7 × 5  ≡ 11  (mod 12)   35 = 2·12 + 11
        6  5
```

- *합동(congruence)*: a ≡ b (mod n) ⇔ n이 a − b를 나눈다(MCS 9.6). 나머지가 같다는 뜻이다(Lemma 9.6.1).
- 나머지 산술의 일반 원리(MCS Lemma 9.7.1)
  - rem(i + j, n) = rem(rem(i, n) + rem(j, n), n)
  - rem(i·j, n) = rem(rem(i, n)·rem(j, n), n)
- 쓰임: 큰 수 계산을 끝에서 한 번 줄이지 않고 **단계마다** 줄여도 답이 같다. 롤링 해시, 거듭제곱, 체크섬이 이 성질로 중간값을 작게 유지한다.
  - 단, "단계마다 줄인 값의 곱"이 자료형에 들어가야 한다(5절).
- 0..n−1과 덧셈·곱셈을 묶은 것을 *Z_n*(정수 모듈로 n의 환)이라 한다. 결합·교환·분배 법칙이 그대로 성립한다(MCS 9.7).

### 3. gcd — 몇 개 칸에 떨어지나

```text
  키 0, 8, 16, 24, …  (간격 s = 8)을 칸 n개에 key mod n으로
  n = 64:  0, 8, 16, …, 56, 0, 8, …      → 쓰는 칸 8개    = 64 / gcd(8, 64)
  n = 61:  0, 8, 16, …, 56, 3, 11, …     → 쓰는 칸 61개   = 61 / gcd(8, 61) = 61 / 1
  n = 60:  0, 8, …, 56, 4, 12, …         → 쓰는 칸 15개   = 60 / gcd(8, 60) = 60 / 4
```

- 간격 s인 키 a, a+s, a+2s, …가 쓰는 칸 수는 최대 n / gcd(s, n)이다(키가 K개면 min(K, n / gcd(s, n))). 키들의 나머지는 a와 gcd(s, n)를 법으로 합동인 값만 나오기 때문이다(a = 0이면 gcd의 배수만. gcd는 s와 n의 정수 일차결합으로 만들 수 있는 가장 작은 양수, MCS Theorem 9.2.2).
- 쓰임
  - 칸 수를 소수로 두면 간격 패턴(소수의 배수 제외)이 고르게 퍼진다. 칸 수를 2의 거듭제곱으로 두면 짝수 간격 키가 몰린다. 그래서 Java `HashMap`은 2의 거듭제곱 칸 + 해시 섞기(`h ^ (h >>> 16)`)를 쓴다([algorithm/12](../../algorithm/12-hash-functions/2-summary.md) 2절). 이 섞기는 위 16비트를 내리는 것이라, 값이 0 이상 2^16 미만인 `Integer` 키에는 효과가 없다(음수는 `>>>`가 위쪽 1비트를 끌어내려 값이 바뀐다, 아래 실험).
  - MySQL `PARTITION BY HASH`는 `MOD(id, N)`이라 규칙 있는 키가 쏠린다([database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md)).

### 4. 모듈러 역원 — "mod n에서 나누기"

```text
  3 · x ≡ 1 (mod 7)  →  x = 5   (15 = 2·7 + 1)
  6 · x ≡ 1 (mod 9)  →  해 없음  (6x mod 9는 0, 3, 6만 나온다 — gcd(6, 9) = 3)
```

- *모듈러 역원*: k·x ≡ 1 (mod n)인 x. 다음 셋이 같다(MCS Theorem 9.9.5, k ∈ [0..n)).
  1. gcd(k, n) = 1(서로소).
  2. k의 역원이 Z_n에 있다.
  3. k를 약분할 수 있다(k·a ≡ k·b이면 a ≡ b).
- 구하는 법: 확장 유클리드로 k·x + n·y = 1인 x를 찾는다(gcd가 일차결합, MCS Theorem 9.2.2 — MCS는 "Pulverizer"라 부른다). x가 음수일 수 있어 `floorMod(x, n)`으로 0..n−1에 넣는다. 구현·단계 그림은 [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md).
- 오일러 정리(MCS Theorem 9.10.3): gcd(k, n) = 1이면 k^φ(n) ≡ 1 (mod n). n이 소수 p면 φ(p) = p − 1이라 k^(p−2)가 역원이다(페르마). **소수가 아닌 n에서는 k^(n−2)가 역원이라는 보장이 없어 조용히 틀릴 수 있다**(우연히 맞는 경우도 있다 — 예: n = 9, k = 8. [algorithm/28](../../algorithm/28-number-theory/2-summary.md) 장애 1).
  - *φ(n)*: 1..n 중 n과 서로소인 수의 개수(오일러 파이 함수).

### 5. 빠른 거듭제곱과 넘침 경계

```text
  a^13 mod m,  13 = 1101₂
  a¹ → a² → a⁴ → a⁸  (제곱하며 매번 mod m)
  답 = a⁸ · a⁴ · a¹  (켜진 비트만 곱하며 매번 mod m)       곱셈 O(log e)번

  매 곱셈의 피연산자 < m  →  곱 < m²
  long(부호 있는 64비트)에 들어갈 조건: (m − 1)² ≤ 2^63 − 1  ⇔  m ≤ 3,037,000,500
```

- 단계마다 mod를 하는 것은 2절의 성질 덕분이다. 알고리즘 단계 그림은 [algorithm/28](../../algorithm/28-number-theory/2-summary.md) 이진 거듭제곱 절, 분할정복 관점은 [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md).
- 경계 3,037,000,500은 √(2^63 − 1)의 정수 부분 3,037,000,499에 1을 더한 값이다(Python `math.isqrt`로 계산). m이 이보다 크면 `(a * a) % m`이 넘칠 수 있다.
- 대안: `BigInteger.modPow`(Java 문서: 음수 지수도 허용, m ≤ 0이거나 음수 지수인데 서로소가 아니면 `ArithmeticException`), 또는 `Math.multiplyHigh`로 128비트 곱을 조립.
- RSA 서명·암호화의 핵심 연산이 이 모듈러 거듭제곱이다([security/06-public-key-and-signatures](../../security/06-public-key-and-signatures/2-summary.md)).

### 6. 2의 보수의 비대칭 — `Math.abs`가 음수를 돌려주는 곳

```text
  int 범위: −2,147,483,648 … 2,147,483,647      음수 쪽이 하나 더 많다
  −(−2,147,483,648) = 2,147,483,648  → int에 없음 → 감겨서 다시 −2,147,483,648
```

- Java 21 `Math.abs(int)` 문서: 인자가 `Integer.MIN_VALUE`면 "the result is that same value, which is negative". `Math.absExact`(Java 15+)는 이 경우 `ArithmeticException`을 던진다.
- JLS §15.17.2: `Integer.MIN_VALUE / -1`은 넘쳐서 피제수 그대로가 되고 예외가 없다. `%`는 이 경우 0이다(§15.17.3).
- 이것은 모듈러 산술 그 자체다. 넘친 정수 곱·합의 결과는 수학적 결과의 하위 비트다(JLS §15.17.1·§15.18.2). 곧 `int` 연산은 2^32 모듈로 계산되고, 결과를 −2^31..2^31−1 범위의 대표값으로 읽는다. JLS §4.2.2는 "The integer operators do not indicate overflow or underflow in any way"라고 적는다.

### 7. 모듈로 편향 — 나머지가 고르지 않을 때

```text
  0..255(256가지)를 % 10
  나머지 0~5: 26번씩   (0,10,…,250 / 5,15,…,255)
  나머지 6~9: 25번씩   (256 = 25·10 + 6 → 앞의 6개가 한 번 더)
```

- 연속한 정수 0..R−1에서 균일하게 뽑은 값을 % n 하면 R이 n의 배수가 아닐 때 앞쪽 R mod n개 나머지가 한 번씩 더 나온다(값이 연속하지 않으면 — 예: {0, 3, 6, 9} % 3 — 편향은 이 식과 다르다).
- Java `RandomGenerator.nextInt(bound)` 기본 구현은 bound가 2의 거듭제곱이 아니면 범위 밖 값을 버리고 다시 뽑는다(Java 21 문서 "re-calculated by invoking nextInt() until …"). `Random`과 그 하위 클래스 `SecureRandom`은 `Random.nextInt(int bound)` 문서에 적힌 거절 루프("It rejects values that would result in an uneven distribution")를 쓴다. 직접 `% n`을 쓰지 말고 이 메서드를 쓴다. 난수 쪽은 [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md).

### 실험: 나머지 부호, MIN_VALUE, 편향, gcd, 거듭제곱 넘침, 역원

`Mod11.java` 핵심(전체는 scratchpad `math/04/Mod11.java`):

```java
static long powNaiveOverflow(long a, long e, long m) {        // long 곱 그대로 — m이 크면 넘친다
    long r = 1; a %= m;
    while (e > 0) { if ((e & 1) == 1) r = (r * a) % m; a = (a * a) % m; e >>= 1; }
    return r;
}
// 기준값: BigInteger.valueOf(a).modPow(BigInteger.valueOf(e), BigInteger.valueOf(m))
// 무작위 10만 건(SplittableRandom 시드 7, a ∈ [1, m), e ∈ [0, 2^40))
for (int i = 0; i < 10_000; i++) used.add(Math.floorMod(i * 8, m));   // 간격 8 키가 쓰는 칸
```

(실험, OpenJDK 21.0.12 Temurin, `eclipse-temurin:21-jdk` 컨테이너 `--network none --cpus=2`, 2026-10-07, 두 번 실행 — 출력 동일)

```text
-- 1. sign of remainder
-7 % 3 = -1, -7 / 3 = -2, floorMod(-7,3) = 2, floorDiv(-7,3) = -3, floorMod(7,-3) = -2
java.lang.ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 3
Math.abs(MIN_VALUE)=-2147483648, -MIN_VALUE=-2147483648, MIN_VALUE/-1=-2147483648, MIN_VALUE%-1=0
absExact: java.lang.ArithmeticException: Overflow to represent absolute value of Integer.MIN_VALUE
(MIN_VALUE & 0x7fffffff) % 10 = 0, floorMod(MIN_VALUE,10) = 2
-- 2. modulo bias: uniform byte (0..255) % 10, exact counts over all 256 values
counts per digit = [26, 26, 26, 26, 26, 26, 25, 25, 25, 25]
-- 3. buckets used = m / gcd(stride, m): keys 0, 8, 16, ... (10,000 keys)
m=64 gcd(8,m)=8 buckets used=8 (m/gcd=8)
m=61 gcd(8,m)=1 buckets used=61 (m/gcd=61)
m=60 gcd(8,m)=4 buckets used=15 (m/gcd=15)
-- 4. fast pow vs BigInteger.modPow (100,000 random cases each, seed 7)
m=1,000,000,007  naive(long) wrong=0  safe wrong=0
m=3,037,000,500  naive(long) wrong=0  safe wrong=0
m=3,037,000,501  naive(long) wrong=0  safe wrong=0
m=4,000,000,000  naive(long) wrong=87604  safe wrong=0
m=1,099,511,627,776  naive(long) wrong=25180  safe wrong=0
-- 5. modular inverse
egcd(3,7) = g=1 x=-2 y=1 -> inverse of 3 mod 7 = 5, check 3*5%7=1
BigInteger(3).modInverse(7) = 5
6 mod 9: java.lang.ArithmeticException: BigInteger not invertible.
egcd(6,9) g=3 -> no inverse
```

(같은 날, Python 3.12.3 호스트)

```text
>>> -7 % 3, -7 // 3, 7 % -3, divmod(-7, 3), pow(3, -1, 7)
2 -3 -2 (-3, 2) 5
>>> pow(6, -1, 9)
ValueError: base is not invertible for the given modulus
```

(실험, 같은 Java 환경, `--add-opens java.base/java.util=ALL-UNNAMED`로 `HashMap.table`을 읽음 — `Integer` 키 150개, 초기 용량 256)

```text
stride=1 keys=150 table=256 buckets used=150
stride=8 keys=150 table=256 buckets used=32
stride=7 keys=150 table=256 buckets used=150
```

- 관찰
  - 같은 `-7 % 3`이 Java −1, Python 2다. −1을 배열 인덱스로 쓰자 `Index -1 out of bounds`.
  - `Math.abs(MIN_VALUE)`는 음수 그대로다. `& 0x7fffffff`(부호 비트 지우기)는 0을, `floorMod`는 2를 준다. 둘 다 0..9 안이지만 **값이 다르다**. 샤드 함수를 바꾸면 기존 키의 샤드가 바뀐다.
  - 간격 8 키는 칸 64개 중 8개, 60개 중 15개만 썼다. 소수 61은 다 썼다. 실제 `HashMap`(256칸)도 8의 배수 `Integer` 키는 32칸만 썼다(= 256/8).
  - 거듭제곱: m ≤ 3,037,000,500은 이론상 안전하고 실제로 0건 틀렸다. m = 3,037,000,501은 이론상 넘칠 수 있지만 **무작위 10만 건에서 0건**이었다. 넘치려면 피연산자 둘이 m 근처여야 해서 무작위로는 거의 안 걸린다(해석). m = 40억에서는 87,604건, 2^40에서는 25,180건 틀렸다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블 칸 번호** — `(n − 1) & hash` = hash mod 2^k. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- **샤딩·파티셔닝** — `hash mod N`, 노드 수 변경 시 대량 이동은 일관 해싱으로 피한다. [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md), [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)
- **링 버퍼** — 위치 = 순번 mod 용량(용량이 2의 거듭제곱이면 마스크). [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)
- **유클리드 호제법·확장 유클리드·이진 거듭제곱** — [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md), [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md)
- **롤링 해시** — 다항식 해시를 mod p로 단계마다 줄인다. [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md)
- **RSA·서명** — 모듈러 거듭제곱과 역원. [security/06-public-key-and-signatures](../../security/06-public-key-and-signatures/2-summary.md)
- **원형 번호 비교** — PostgreSQL 32비트 XID를 2^32 모듈로 비교. [database/16-mvcc](../../database/16-mvcc/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 어림

- 음수 인덱스 예외, 특정 키에서만 실패, 서비스마다 다른 샤드, 일부 파티션만 뜨거움, 큰 수 계산이 가끔 틀림.
- 어림 질문
  1. 피제수가 음수일 수 있나? (해시값, 시각 차이, 오프셋) → 언어의 `%` 규칙 확인.
  2. 키 간격과 칸 수의 gcd는? → 쓰는 칸 = n / gcd.
  3. 곱하는 두 값이 m 미만이라도 m²이 자료형에 들어가나? → m ≤ 3,037,000,500(long).

### 2. 코드로 고정한다 (Java 21)

```java
// 샤드 번호: 0..n-1을 보장하고, 다른 언어 서비스와 같은 규칙(floor)을 쓴다
static int shardOf(String key, int n) {
    if (n <= 0) throw new IllegalArgumentException("n must be positive");
    return Math.floorMod(key.hashCode(), n);      // Python: hash_value % n 과 같은 규칙
}

// 모듈러 곱: m이 경계를 넘으면 BigInteger로
static long mulMod(long a, long b, long m) {
    if (m <= 3_037_000_500L) return Math.floorMod(a, m) * Math.floorMod(b, m) % m;
    return BigInteger.valueOf(a).multiply(BigInteger.valueOf(b)).mod(BigInteger.valueOf(m)).longValue();
}
```

- 여러 언어가 같은 샤드 함수를 쓰면 해시 함수 자체도 같아야 한다. `String.hashCode`(Java)와 Python `hash()`(문자열은 프로세스마다 무작위화, [algorithm/12](../../algorithm/12-hash-functions/2-summary.md) 실험)는 다르다. 언어 중립 해시(예: 명세가 있는 비암호 해시)를 정하고 `floor` 나머지로 맞춘다.
- 테스트에는 경계값을 넣는다: 음수 해시, `Integer.MIN_VALUE`(`"polygenelubricants"`), m = 3,037,000,501에서 a = b = m − 1. 무작위 테스트는 경계를 거의 못 찾는다(위 실험).

## 장애 시나리오와 대처

### 1. 음수 나머지 → 샤드 인덱스 `ArrayIndexOutOfBoundsException` (⚠ 커리큘럼)

- **현상**: 특정 키에서만 요청이 실패한다.
- **보이는 형태**: `java.lang.ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 3`(위 실험).
- **원인**: Java `%`는 피제수 부호를 따른다(JLS §15.17.3). 해시가 음수면 나머지도 음수다.
- **대처**: `Math.floorMod(h, n)`(n > 0). 음수 해시 키를 테스트에 넣는다.

### 2. 언어마다 다른 나머지 → 같은 키가 다른 샤드로

- **현상**: Java 서비스가 쓴 데이터를 Python 배치가 못 찾는다. 일부 키만 그렇다.
- **보이는 형태**: 음수 해시를 가진 키에서만 "없음". 두 서비스가 계산한 샤드 번호가 n만큼 차이 난다(Java −1, Python n−1).
- **원인**: Java `%`는 truncate, Python `%`는 floor다. 해시값이 같아도 음수에서 나머지가 다르다.
- **대처**: 샤드 규칙을 명세로 고정한다(해시 함수 + floor 나머지 + n). Java는 `floorMod`, Python은 `%`로 맞추고, 양쪽에 같은 테스트 벡터(음수 포함)를 둔다.

### 3. `Math.abs(Integer.MIN_VALUE)`가 음수 (⚠ 커리큘럼)

- **현상**: `Math.abs`로 고쳤는데 아주 드물게 같은 예외가 난다.
- **보이는 형태**: `Math.abs(MIN_VALUE) = -2147483648`, `Index -8 out of bounds for length 10`([algorithm/12](../../algorithm/12-hash-functions/2-summary.md) 실험).
- **원인**: 2의 보수 `int`는 음수 쪽이 하나 더 많다. −MIN_VALUE는 표현할 수 없어 다시 MIN_VALUE가 된다(Java `Math.abs` 문서).
- **대처**: `floorMod`를 쓴다. 넘침을 예외로 드러내고 싶으면 `Math.absExact`(Java 15+). 샤드 함수를 바꿀 때는 기존 데이터 재배치를 함께 계획한다(`& 0x7fffffff`와 `floorMod`는 결과가 다르다).

### 4. 모듈러 곱 넘침 → 조용히 틀린 해시·서명 검증값

- **현상**: 큰 모듈러를 쓰는 계산(커스텀 해시, 토큰 체크섬)이 가끔 다른 값을 낸다. 예외는 없다.
- **보이는 형태**: `BigInteger.modPow`와 비교하면 불일치(m = 40억에서 무작위 10만 건 중 87,604건). m이 경계 바로 위면 무작위 테스트로는 0건이라 지나친다.
- **원인**: `(a * a) % m`에서 a·a가 2^63을 넘어 감긴다. Java 정수 연산은 넘침을 알리지 않는다(JLS §4.2.2).
- **대처**: m ≤ 3,037,000,500이면 `long`, 넘으면 `BigInteger.modPow`·`Math.multiplyHigh`. 경계값(a = m − 1) 테스트를 둔다.

### 5. gcd 쏠림·모듈로 편향 → 뜨거운 칸, 치우친 코드

- **현상**: 파티션 몇 개만 부하가 높다. 또는 발급한 숫자 코드의 앞쪽 숫자가 더 자주 나온다.
- **보이는 형태**: 간격 있는 키(8의 배수 ID, 같은 접두 시각)가 최대 n / gcd(s, n)개 칸에만 분포(위 실험: 64칸 중 8칸). 바이트 % 10이면 0~5가 26/256, 6~9가 25/256.
- **원인**: 키 간격 s와 칸 수 n이 공약수를 가진다. 또는 난수 범위가 n의 배수가 아니다.
- **대처**: 칸에 넣기 전에 해시로 섞는다. 칸 수를 소수로 둘 수 있으면 둔다. 범위 난수는 `nextInt(bound)`(거절 표집)를 쓴다.

## 핵심 문장

- 수학의 나머지는 0 ≤ r < |d|지만, Java `%`는 피제수 부호(truncate)를, Python `%`와 `Math.floorMod`는 제수 부호(floor)를 따른다.
- 칸 번호에는 `Math.floorMod(h, n)`(n > 0)을 쓴다. `Math.abs(h) % n`은 `Integer.MIN_VALUE`에서 음수다.
- 합동 산술에서는 단계마다 나머지를 취해도 답이 같다. 단 단계마다의 곱이 자료형에 들어가야 하고, long이면 m ≤ 3,037,000,500이다.
- 역원은 gcd(k, n) = 1일 때만 있다. 확장 유클리드로 구하고, 페르마 식 k^(n−2)는 n이 소수일 때만 역원이 보장된다.
- 간격 s인 키는 최대 n / gcd(s, n)개 칸만 쓴다. 섞지 않은 키를 2의 거듭제곱 칸에 넣으면 쏠린다.
- 넘침·경계 버그는 무작위 테스트로는 거의 안 잡힌다. 경계값을 테스트에 직접 넣는다.

## 관련 주제·근거

- 선행
  - [05-counting-and-birthday-bound](../05-counting-and-birthday-bound/2-summary.md) — 칸 수와 충돌(해시값을 칸으로 줄이는 단계가 이 노트)
- 후속·연결
  - [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md) — 모듈로 편향, 선형 합동 생성기
  - [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md)(체·유클리드·역원·이진 거듭제곱 구현) · [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md) · [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) · [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md)
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) · [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)
  - [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md) · [database/16-mvcc](../../database/16-mvcc/2-summary.md) · [security/06-public-key-and-signatures](../../security/06-public-key-and-signatures/2-summary.md)
- 교재
  - MIT 6.042 MCS(2018-06-06판 PDF <https://courses.csail.mit.edu/6.042/spring18/mcs.pdf>) — 9.1 Divisibility(Theorem 9.1.4 나눗셈 정리), 9.2 GCD(Theorem 9.2.2 일차결합, Pulverizer), 9.6 Modular Arithmetic(Lemma 9.6.1·9.6.4), 9.7 Remainder Arithmetic(Lemma 9.7.1, Z_n), 9.9 Multiplicative Inverses and Cancelling(Theorem 9.9.5), 9.10 Euler's Theorem(Theorem 9.10.3), 9.11 RSA
  - CLRS 3판 31장 Number-Theoretic Algorithms(31.2 GCD, 31.4 모듈러 일차 방정식, 31.6 거듭제곱, 31.7 RSA)
- 언어 명세·문서
  - JLS SE 21 §15.17.1(곱 넘침 = 하위 비트), §15.17.2 Division Operator(0 쪽 버림, MIN_VALUE/−1 넘침), §15.17.3 Remainder Operator(피제수 부호, 예제 15.17.3-1) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html>, §4.2.2 Integer Operations(넘침을 알리지 않음) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html>
  - Java 21 `Math` — `abs(int)`(MIN_VALUE 음수), `absExact`(Java 15+, `ArithmeticException`), `floorMod`·`floorDiv`(제수 부호, 예시 표) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Math.html>
  - Java 21 `BigInteger` — `modPow`, `modInverse`(서로소가 아니면 `ArithmeticException`) · `RandomGenerator.nextInt(int bound)`(재추첨) · `java.util.Random.nextInt(int bound)`(거절 루프) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Random.html>
  - Python 3 Language Reference 6.7 Binary arithmetic operations(`%`는 제수 부호, `x == (x//y)*y + (x%y)`) <https://docs.python.org/3/reference/expressions.html> · 내장 `pow(base, -1, mod)`(3.8+)
- 실험 목록
  - `Mod11.java` — 나머지 부호·`floorMod`·AIOOBE, MIN_VALUE 연산과 `absExact`, 바이트 % 10 편향(전수), 간격 8 키의 칸 수(m = 64·61·60), 이진 거듭제곱 long 버전 vs `BigInteger.modPow` 무작위 10만 건(m 5종, 시드 7), 확장 유클리드·`modInverse`. OpenJDK 21.0.12 Temurin 컨테이너(`--network none --cpus=2`), 2026-10-07, 두 번 실행.
  - `HmStride.java` — 실제 `HashMap`(256칸)에 간격 1·8·7 `Integer` 키 150개를 넣고 쓰인 칸 수(리플렉션). 같은 환경.
  - Python 3.12.3 — `-7 % 3`, `-7 // 3`, `7 % -3`, `divmod`, `pow(3, -1, 7)`, `pow(6, -1, 9)`의 `ValueError`.
