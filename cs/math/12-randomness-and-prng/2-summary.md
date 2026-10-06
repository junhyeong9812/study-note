# math/12-randomness-and-prng — 의사난수·시드·CSPRNG·셔플·샘플링 — 정리 (힌트)

## 해결하는 문제

장애 뒤 서버 100대가 재시도에 지터를 넣었다. 그런데 100대가 정확히 같은 순간에 다시 몰려왔다. 지터 난수의 시드가 설정 파일의 `42`였다.

```text
  인스턴스 100대, 지터 = random(0, 1000ms)   (실험 A)

  고정 시드 42          ████████████████████ 100대가 같은 10ms 칸
                       0ms ──────────────────── 891ms ── 1000ms

  기본 new Random()     ▂ ▁ ▃ ▁ ▂ ▁ ▂ ▃ ▁ ▂ ▁ ▂ ▁ ▃ ▁ ▂   한 칸 최대 4대
```

- 컴퓨터의 "난수"는 대부분 **의사난수**다. 시드가 같으면 수열 전체가 같다.
- 그래서 두 가지가 동시에 필요하다.
  - 흩어져야 할 곳(지터·샘플링·셔플)에서는 인스턴스마다 다른 시드.
  - 맞혀지면 안 되는 곳(토큰·키)에서는 출력을 봐도 다음을 알 수 없는 생성기(CSPRNG).

쉬운 예: 같은 순서로 섞어 둔 카드 덱 두 벌이다. 섞는 방법이 같고 시작 순서가 같으면 두 덱은 똑같이 나온다.

똑같은 구조다.\
PRNG는 "시드 = 시작 순서", "갱신 함수 = 섞는 방법"이다.

실무 예:
- 지터·백오프·샘플링·부하 분산의 무작위 선택(흩어지면 충분 — 빠른 PRNG).
- 비밀번호 재설정 토큰·세션 ID·API 키(예측되면 안 됨 — CSPRNG).
- A/B 테스트 배정·추첨·셔플(편향이 없어야 함 — 올바른 셔플 알고리즘).

## 동작·원리

### 1. PRNG = 상태 + 갱신 + 출력

```text
  시드 ──> [상태 s0] ──갱신 f──> [s1] ──f──> [s2] ──f──> ...
                            │           │
                         출력 g      출력 g
                            ▼           ▼
                           x1          x2         같은 시드 → 같은 x1, x2, ...

  주기(period): 상태가 처음으로 되풀이되기까지의 길이. 상태가 b비트면 주기 ≤ 2^b
```

- *의사난수 생성기(PRNG)*: 작은 시드에서 결정적으로 긴 수열을 만드는 알고리즘. 통계적으로 무작위처럼 보이는 것이 목표다.
- *시드(seed)*: 초기 상태를 정하는 값.
- *주기*: 수열이 반복되기 전 길이. 상태 수보다 길 수 없다.
- 결정성은 버그가 아니라 기능이다. 시뮬레이션·테스트를 같은 시드로 재현할 수 있다([algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md) 적용 3절).

### 2. LCG — `java.util.Random`

```text
  상태 48비트:  s ← (s × 0x5DEECE66D + 0xB) mod 2^48
  출력 next(bits) = s의 상위 bits비트      (s >>> (48 − bits))

  nextInt()     = next(32)
  nextDouble()  = (next(26) · 2^27 + next(27)) × 2^−53      ← 상태 두 번 전진
  setSeed(x)    : s = (x XOR 0x5DEECE66D) mod 2^48
```

- *선형 합동 생성기(LCG)*: `s ← (a·s + c) mod m`. Knuth TAOCP 2권 3.2.1. OpenJDK `Random` Javadoc이 이 절을 인용한다.
- OpenJDK 21 `Random.java`: "its period is only 2^48", "Instances of `java.util.Random` are not cryptographically secure".
- `Math.random()`은 처음 호출 때 `new Random()` 하나를 만들어 계속 쓴다(`Math.java` Javadoc·소스의 `RandomNumberGeneratorHolder`).
- 하위 비트가 약하다
  - 법이 2의 거듭제곱이고 a·c가 모두 홀수인 LCG(최대 주기 LCG가 그렇다)에서 최하위 비트는 주기 2로 0·1을 번갈아 낸다(`b' = (a·b + c) mod 2`, 아래 실험 D). c가 짝수면 최하위 비트는 아예 고정된다.
  - 그래서 `Random`은 상위 비트를 내보낸다. `nextInt(bound)`도 bound가 2의 거듭제곱이면 하위 비트 대신 상위 비트를 쓴다(Javadoc: LCG는 "short periods in the sequence of values of their low-order bits").

### 3. 다른 PRNG 계열 — 빠르지만 비암호

```text
  xorshift (Marsaglia 2003)   s ^= s << a;  s ^= s >>> b;  s ^= s << c;    시프트 3번 + XOR 3번
  SplittableRandom            s += GAMMA(홀수);  출력 = mix64(s)          주기 2^64, split()으로 상태를 공유하지 않는 스트림
  ThreadLocalRandom           스레드마다 상태, 같은 방식                     공유 경합 없음
  LXM (JDK 17+, JEP 356)      LCG + xorshift 계열 결합                     RandomGenerator.getDefault()
```

- Marsaglia, "Xorshift RNGs", Journal of Statistical Software 8(14), 2003: 시프트와 XOR만으로 만드는 생성기.
- OpenJDK 21 `SplittableRandom`·`ThreadLocalRandom` Javadoc: 주기 2^64, 둘 다 "not cryptographically secure".
- JDK 17의 JEP 356이 `RandomGenerator` 인터페이스와 LXM 계열을 넣었다. 이 실험 환경(OpenJDK 21.0.12)에서 `RandomGenerator.getDefault()`는 `L32X64MixRandom`이었다(실험 E 출력 `RandomGenerator.getDefault() = L32X64MixRandom`, OpenJDK 21 `java/util/random/RandomGenerator.java` 주석 "The default implementation selects L32X64MixRandom").
- Python `random`은 메르센 트위스터다(주기 2**19937−1, Python 3.12 `random` 모듈 문서 문자열). 보안 용도는 `secrets`(PEP 506).
- 주기가 길다 ≠ 예측 불가능하다. 위 생성기들은 예측 불가능성을 목표로 설계되지 않았다(Javadoc의 "not cryptographically secure"). `Random`은 실제로 `nextDouble()`(= `Math.random()`) 값 하나에서 상태가 복원된다(5절 실험 C). `nextInt()` 값 하나는 상위 32비트뿐이라 후보가 2^16개 남는다 — 출력이 둘 이상 필요하다.

### 4. 시드는 어디서 오나 — 같은 시드의 위험

| 시드 | 어디서 | 인스턴스끼리 |
|---|---|---|
| 상수(`new Random(42)`) | 코드·설정 | 전부 같다 |
| 시작 시각 ms | `System.currentTimeMillis()` | 같은 ms에 뜬 것끼리 같다 |
| `new Random()` 기본 | `seedUniquifier() ^ System.nanoTime()`(OpenJDK 21 소스) | 대체로 다르다 |
| `ThreadLocalRandom` | 시작 시 `seeder` — 기본은 시간 기반 mix, `java.util.secureRandomSeed=true`면 `SecureRandom.getSeed(8)` | 대체로 다르다 |

### 실험 A: 인스턴스 100개의 지터 — 시드별 동시 재시도

```java
// scratchpad/math/07/e12/Prng.java 핵심 — 인스턴스 i의 첫 지터 = random(0, 1000ms)
same[i]  = new Random(42).nextLong(1000);                           // 설정 파일의 고정 시드
ms[i]    = new Random(1_700_000_000_000L + i % 3).nextLong(1000);    // 시작 시각 시드, 3ms 안에 뜸
fresh[i] = new Random().nextLong(1000);                              // 기본 생성자
// 10ms 칸마다 몇 개가 겹치나 → 최댓값
```

(실험, OpenJDK 21.0.12 Temurin 컨테이너 `--cpus=2 --network none`, 2026-10-07, 3회 실행)

```text
(A) 인스턴스 100개, 지터 random(0,1000ms) 1회 — 10ms 칸 최대 동시 재시도 수
고정 시드 42          : 100개 (서로 다른 지터 값 1개)
시작 시각 ms 시드     :  34개 (서로 다른 지터 값 3개)
new Random() 기본     :   4개 (서로 다른 지터 값 96개)
```

- 관찰 1: 고정 시드면 지터가 없는 것과 같다. 100대가 같은 ms에 돌아온다. 재시도를 몇 번 해도 수열이 같아 매번 같이 온다.
- 관찰 2: 시작 시각(ms)을 시드로 쓰면 같은 ms에 뜬 인스턴스끼리 묶인다. 오토스케일·재시작으로 한꺼번에 뜨면 흔하다.
- 관찰 3: 기본 생성자는 실행할 때마다 값이 다르다. 집필 3회와 점검 재실행 3회에서 칸 최대 3~4대, 서로 다른 값 91~96개였다. 서로 다른 값 수는 100개를 1000가지 값에 균등하게 던질 때의 기대(`1000·(1 − 0.999^100)` ≈ 95.2)와 맞고, 칸 최대는 100개를 100개의 10ms 칸에 던질 때 흔한 값이다(겹침은 생일 문제. Python `random` seed 1, 2만 회 시뮬레이션: 칸 최대 3~5가 약 95%).
- 지터 식 자체와 재시도 폭풍 실험은 [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md). 이 노트의 요점은 **지터의 난수가 인스턴스마다 달라야** 지터가 동작한다는 것이다.

### 5. CSPRNG — 출력을 봐도 다음을 모른다

```text
  Math.random() 값 하나 = 53비트 = 상태1의 상위 26비트 + 상태2의 상위 27비트
  모르는 것: 상태1의 하위 22비트 → 2^22 = 약 420만 후보
  후보마다 상태2를 계산해 상위 27비트가 맞는지 확인 → 어림으로는 틀린 후보가 남을 기대 수 2^22 / 2^27 = 1/32
  실제 Random 상수로 따지면: 하위 22비트 차이 d(0 < |d| < 2^22)에 대해 a·d mod 2^48이 ±2^21 안에 드는 d가 없다
  → 상위 27비트가 같은 두 후보는 생기지 않는다 → 후보는 언제나 1개
  → 내부 상태 복원 → 다음 Math.random()을 모두 예측
```

- *CSPRNG(암호학적으로 안전한 PRNG)*: 출력 일부를 봐도 다음(과 이전) 출력을 실현 가능한 계산으로 예측할 수 없는 생성기. Java `SecureRandom`, Linux `getrandom(2)`. 구조와 `setSeed` 함정은 [security/09-randomness-and-key-management](../../security/09-randomness-and-key-management/2-summary.md).
- 위 공격은 LCG의 수학 구조(상태 48비트, 출력이 상태의 상위 비트 그대로)에서 나온다. 시드를 몰라도 된다.

### 실험 C: `Math.random()` 하나로 다음 다섯 개 예측

```java
double d0 = Math.random();
long v = (long) (d0 * 0x1.0p53);
long hi26 = v >>> 27, hi27 = v & ((1L << 27) - 1);
for (long low = 0; low < (1L << 22); low++) {
    long s1 = (hi26 << 22) | low, s2 = (s1 * 0x5DEECE66DL + 0xBL) & ((1L << 48) - 1);
    if ((s2 >>> 21) == hi27) cand.add(s2);                 // 후보 상태
}
// 후보 상태에서 LCG를 두 번씩 돌려 다음 nextDouble을 계산 → 실제 Math.random()과 비교
```

(실험, 같은 환경, 3회 실행)

```text
(C) 관찰한 Math.random() = 0.9187266608632516 → 후보 상태 1개, 탐색 41ms
  예측 0.9628671827457721   실제 0.9628671827457721   일치
  예측 0.1088315207589845   실제 0.1088315207589845   일치
  예측 0.54508674735551     실제 0.54508674735551     일치
  예측 0.658914225123008    실제 0.658914225123008    일치
  예측 0.40518321130393986  실제 0.40518321130393986  일치
5개 중 5개 일치
```

- 집필 3회·점검 재실행 3회 모두 후보 1개, 5개 중 5개 일치였다. 탐색 시간은 32~43ms(이 제한 환경 `--cpus=2`의 값).
- 해석: 토큰에 `Math.random()` 반환값 전체가 드러나면, 공격자는 같은 JVM이 그 뒤에 만드는 값을 계산할 수 있다. 생성기는 JVM 안 모든 `Math.random()` 호출이 공유하므로 다른 호출이 섞이면 몇 칸 앞으로 더 돌려 보며 찾아야 한다. 토큰이 값 일부만 드러내면 후보가 여럿 남아 출력이 더 필요하다. 어느 쪽이든 토큰에 쓰면 안 된다는 결론은 같다.

### 6. 셔플 — Fisher–Yates와 흔한 실수

```text
  Fisher–Yates (Knuth 3.4.2 Algorithm P, CLRS 5.3 RANDOMIZE-IN-PLACE)
  for i = n−1 down to 1:  j = random(0..i);  swap(a[i], a[j])
     경우의 수 = n · (n−1) · … · 2 = n!   → 순열마다 정확히 한 경로 → 균등

  잘못된 셔플: for i = 0..n−1:  j = random(0..n−1);  swap(a[i], a[j])
     경우의 수 = n^n.  n=3이면 27 경로를 6 순열에 나눠야 한다 → 27은 6으로 안 나뉜다 → 균등 불가능
```

- `Collections.shuffle`(OpenJDK 21)은 Fisher–Yates를 뒤에서부터 돈다: `for (int i=size; i>1; i--) swap(list, i-1, rnd.nextInt(i));`. Javadoc: "All permutations occur with equal likelihood assuming that the source of randomness is fair."
- 잘못된 셔플이 균등할 수 없다는 논증은 CLRS 연습문제 5.3-3(풀이: Bodnar·Lohr)과 같다.
- 시드 공간의 한계: `Random`의 상태는 2^48 ≈ 2.8×10^14가지다. 17! ≈ 3.6×10^14이므로, `Random` 하나로 17장 이상을 섞으면 **나올 수 없는 순열**이 생긴다(경우의 수 비교에서 나오는 사실 — 추첨·카드 게임처럼 순열 공간 전체가 중요하면 상태가 큰 생성기를 쓴다).

### 실험 B: n=3 순열 빈도 — Fisher–Yates vs 잘못된 셔플

```java
for (int i = a.length - 1; i > 0; i--) { int j = r.nextInt(i + 1); swap(a, i, j); }   // Fisher–Yates
for (int i = 0; i < b.length; i++)      { int j = r.nextInt(b.length); swap(b, i, j); } // 잘못된 셔플
```

(실험, 같은 환경, 270만 회, `new Random(42)`)

```text
(B) n=3 셔플 2,700,000회(seed 42) — 균등이면 순열마다 450,000
순열         Fisher–Yates   잘못된 셔플   (잘못된 셔플 이론: 27가지 경로 중 4 또는 5 → ×100,000)
[1, 2, 3]      450,098       400,456
[1, 3, 2]      450,061       499,350
[2, 1, 3]      449,095       501,037
[2, 3, 1]      450,567       499,588
[3, 1, 2]      449,590       399,303
[3, 2, 1]      450,589       400,266
```

- 관찰 1: Fisher–Yates는 450,000 ± 1,000 안이다.
- 관찰 2: 잘못된 셔플은 27 경로 중 4개(400,000)·5개(500,000)로 갈린다. `[1,3,2]·[2,1,3]·[2,3,1]`이 25% 더 자주 나온다. seed 7에서도 같은 모양이었다.

### 실험 F: JS 비교자 셔플 `sort(() => Math.random() - 0.5)`

```js
// scratchpad/math/07/e12/sortshuffle.js
const k = [1, 2, 3].sort(() => Math.random() - 0.5).join('');
```

(실험, node:22-alpine 컨테이너 Node v22.23.2, 60만 회, 2회 실행)

```text
v22.23.2 T=600000 균등이면 각 100000
123 224834
132 37573
213 75215
231 37572
312 37543
321 187263
```

- 관찰: 원래 순서 `123`이 균등의 2.2배, `132·231·312`는 0.38배다. 2회째도 224,675·37,984·74,708·37,550·37,785·187,298로 같은 모양이었다.
- 해석: 비교자가 일관되지 않으면(같은 쌍에 다른 답) 정렬 알고리즘의 비교 순서가 그대로 편향이 된다. 편향의 모양은 엔진의 정렬 구현에 따라 달라진다.

### 7. 표집 — 길이를 모르는 스트림에서 k개

- *저수지 표집(reservoir sampling)*: 처음 k개를 담고, i번째(i > k) 원소를 확률 k/i로 저장소의 무작위 칸과 바꾼다. Knuth 3.4.2 Algorithm R(Waterman에게 귀속), Vitter(1985). 균등성 실험은 [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md) 6절.
- 로그·트레이스 샘플링(요청의 1%만 저장)에서는 요청마다 `nextDouble() < 0.01`로 고르거나, 트레이스 ID 해시로 고른다. 해시로 고르면 서비스들이 같은 트레이스를 함께 고른다(무작위성이 아니라 결정적 선택이 필요한 경우).

## 쓰이는 자료구조·알고리즘

- LCG(`java.util.Random`), xorshift·SplitMix(`SplittableRandom`), LXM(`RandomGenerator`), CSPRNG(`SecureRandom` — [security/09](../../security/09-randomness-and-key-management/2-summary.md)).
- Fisher–Yates 셔플(`Collections.shuffle`), 저수지 표집([algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md)).
- 무작위 피벗 퀵정렬([algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md)), 스킵 리스트의 동전 던지기([data-structure/12-skip-list](../../data-structure/12-skip-list/2-summary.md)).
- 재시도 지터([reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)), 확률적 조기 만료(XFetch, [reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md)), 셔플 샤딩([reliability/51-cells-stamps-and-blast-radius](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md)).
- 랜덤 식별자(UUIDv4 122비트): [security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 용도별 생성기 고르기

```text
  질문 1: 출력이 맞혀지면 피해가 있나? (토큰·키·nonce·세션 ID·추첨)
     예 → SecureRandom (Python: secrets)
     아니오 ↓
  질문 2: 재현이 필요한가? (시뮬레이션·테스트·실험 배정 재계산)
     예 → 시드를 받아 쓰는 생성기 + 시드를 로그에 남긴다 (SplittableRandom(seed) 등)
     아니오 ↓
  질문 3: 여러 인스턴스·스레드가 흩어져야 하나? (지터·샘플링)
     → ThreadLocalRandom.current() — 시드를 직접 주지 않는다
```

### 2. 코드

```java
// 지터: 인스턴스·스레드마다 다른 상태, 고정 시드 없음
long jitterMs = ThreadLocalRandom.current().nextLong(0, capMs + 1);

// 토큰: CSPRNG 128비트 이상 (security/09 적용 1절과 같은 원칙)
byte[] b = new byte[16];
SECURE.nextBytes(b);                                   // static final SecureRandom SECURE = new SecureRandom();
String token = Base64.getUrlEncoder().withoutPadding().encodeToString(b);

// 셔플: 직접 짜지 말고 Collections.shuffle — 보안·추첨이면 SecureRandom을 넘긴다
Collections.shuffle(list, SECURE);

// 재현 가능한 시뮬레이션: 시드를 기록
long seed = Long.getLong("sim.seed", System.nanoTime());
log.info("simulation seed={}", seed);
var rnd = new SplittableRandom(seed);
```

### 3. 진단 — "지터를 넣었는데 동시에 온다"

1. 증상: 재시도 도착 시각 히스토그램이 뾰족하다.
2. 어림: 인스턴스 N대가 독립 지터를 쓰면 칸 하나의 최댓값은 몇 대 수준이다(실험 A 기본 생성자: 100대 → 3~4). N대가 한 칸에 몰리면 시드가 같다고 의심한다.
3. 확인: 지터 생성 코드에서 `new Random(상수)`·`new Random(System.currentTimeMillis())`·설정 주입 시드를 찾는다. 두 인스턴스의 첫 지터 값을 로그로 비교한다.

## 장애 시나리오와 대처

### 1. 같은 시드의 인스턴스들이 같은 지터 → thundering herd 재발 (⚠ 커리큘럼)

- 현상: 장애 복구 직후 재시도가 한꺼번에 몰려 하류가 다시 쓰러진다. 백오프를 늘려도 반복된다.
- 보이는 형태: 하류 요청 수가 백오프 간격마다 뾰족한 봉우리. 인스턴스 로그의 재시도 시각이 ms 단위로 같다.
- 원인: 지터 난수를 `new Random(42)`(설정 상수) 또는 시작 시각 ms로 시드했다. 인스턴스들이 같은 수열을 낸다(실험 A: 100대가 한 칸).
- 대처: `ThreadLocalRandom` 또는 기본 생성자를 쓴다. 테스트용 고정 시드는 운영 설정에서 분리한다. 재시도 시각 분포를 지표로 본다.

### 2. `Math.random()` 토큰 → 예측 가능한 세션·재설정 링크 (⚠ 커리큘럼)

- 현상: 다른 사용자의 비밀번호 재설정 링크·세션이 탈취된다.
- 보이는 형태: 접근 로그에 유효한 토큰이 처음 시도에 맞는 요청. 무차별 대입 흔적(수많은 실패)이 없다.
- 원인: 토큰을 `Math.random()`·`java.util.Random`으로 만들었다. 토큰에 반환값 전체가 드러나면, 공격자가 자기 계정으로 토큰 하나를 받아 내부 상태를 복원하고 호출 순서를 따라가며 다음 토큰을 계산한다(실험 C: 값 하나로 40ms 안팎에 다음 5개 일치).
- 대처: `SecureRandom` 128비트 이상. 이미 발급한 토큰은 무효화하고 재발급한다. 정적 분석으로 보안 맥락의 `Math.random`·`new Random`을 찾는다.

### 3. 직접 짠 셔플이 편향 → 추첨·A/B 배정 불공정

- 현상: 추첨에서 특정 순번이 더 자주 당첨된다. A/B 그룹 크기가 설계와 다르다.
- 보이는 형태: 순번(또는 원래 위치)별 당첨 빈도의 카이제곱 검정에서 유의한 차이. n=3이면 특정 순열이 25% 더 많다(실험 B). JS 비교자 셔플은 원래 순서가 2.2배다(실험 F).
- 원인: `j = random(0..n−1)` 셔플(n^n 경로)이나 `sort(() => Math.random() − 0.5)` 같은 비교자 셔플. 경우의 수가 n!로 나뉘지 않는다(n^n 셔플은 n ≥ 3에서).
- 대처: Fisher–Yates(`Collections.shuffle`). 추첨처럼 공정성이 걸리면 CSPRNG를 넘기고, 순열 수가 2^48보다 크면(17장 이상) 상태가 큰 생성기를 쓴다.

### 4. 직접 만든 LCG의 하위 비트

- 현상: `rand() % 2`로 고른 A/B 배정이 번갈아 A, B, A, B로 나온다. 짝수 샤드에만 쓰기가 몰린다.
- 보이는 형태: 배정 순서에 주기 2 패턴(실험 D의 `0101…`).
- 원인: 법이 2^k이고 a·c가 홀수인 LCG의 최하위 비트 주기는 2다. `% 2`·`% 2^k`는 하위 비트만 본다.
- 대처: 표준 라이브러리 생성기의 `nextInt(bound)`를 쓴다(하위 비트 문제를 피해 구현됨). 직접 구현이 필요하면 상위 비트를 쓴다.

(실험 D, 같은 환경, 예시 상수 a=1664525, c=1013904223, m=2^32)

```text
(D) LCG x←(1664525x+1013904223) mod 2^32, 24단계
최하위 비트: 010101010101010101010101
최상위 비트: 001110011101101001011100
```

## 핵심 문장

- PRNG는 시드가 같으면 수열이 같다. 흩어져야 할 난수(지터)는 인스턴스마다 시드가 달라야 한다.
- 주기가 길다는 것과 예측할 수 없다는 것은 다르다. `Math.random()`(`Random.nextDouble()`) 값 하나로 `java.util.Random`의 상태가 복원된다.
- 맞혀지면 피해가 있는 값은 CSPRNG(`SecureRandom`, Python `secrets`)로 만든다.
- 셔플은 Fisher–Yates다. n! 경로가 각 순열에 하나씩이어야 균등하다. `random(0..n−1)` 교환은 n^n 경로라 n ≥ 3이면 균등할 수 없다(n−1이 n과 서로소라 n!이 n^n을 나누지 못한다. n=2는 우연히 균등).
- 법이 2^k인 LCG의 하위 비트는 주기가 짧다. 그래서 표준 구현은 상위 비트를 내보낸다.

## 관련 주제·근거

선행·후속:
- 선행: [09-common-distributions](../09-common-distributions/2-summary.md)(균등·지수 표본), [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md), [07-probability-and-bayes](../07-probability-and-bayes/2-summary.md).
- 후속: [security/09-randomness-and-key-management](../../security/09-randomness-and-key-management/2-summary.md)(CSPRNG 구조·키 관리), [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md). Debian OpenSSL PRNG 사건(시드가 프로세스 ID뿐이라 아키텍처별 난수 스트림 32,767개 — Debian wiki SSLkeys https://wiki.debian.org/SSLkeys)은 [수학 17 incidents](../17-math-incidents/2-summary.md)와 security/09 장애 3절.
- 다른 영역: [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md), [security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md), [reliability/29-cache-stampede](../../reliability/29-cache-stampede/2-summary.md).

근거:
- OpenJDK 21 소스(github.com/openjdk/jdk21u, 2026-10-07 열람): `java/util/Random.java`(48비트 LCG `(seed * 0x5DEECE66DL + 0xBL) & ((1L << 48) - 1)`, "period is only 2^48", Knuth 3.2.1 인용, 비암호, `nextDouble` 구현, `nextInt(bound)` 하위 비트 주석, 기본 생성자 `seedUniquifier() ^ System.nanoTime()`), `java/lang/Math.java`(`random()` = `RandomNumberGeneratorHolder`의 `new Random()`), `java/util/Collections.java`(`shuffle` 구현과 Javadoc), `java/util/SplittableRandom.java`·`java/util/concurrent/ThreadLocalRandom.java`(주기 2^64, 비암호, `secureRandomSeed`).
- D. E. Knuth, TAOCP 2권 『Seminumerical Algorithms』 3판: 3.2.1(선형 합동법 — `Random` Javadoc 인용으로 확인), 3.4.2(Random Sampling and Shuffling, Algorithm P·Algorithm R — 2차 출처로 확인, 본문 미열람 `[?]`).
- CLRS 3판 5.3(RANDOMIZE-IN-PLACE), 연습문제 5.3-3(n^n 경로 셔플) — 풀이: M. Bodnar, A. Lohr, https://sites.math.rutgers.edu/~ajl213/CLRS/Ch5.pdf (본문은 장 단위 인용).
- G. Marsaglia, "Xorshift RNGs", Journal of Statistical Software 8(14), 2003 — https://www.jstatsoft.org/v08/i14/
- JEP 356 "Enhanced Pseudo-Random Number Generators"(JDK 17) — https://openjdk.org/jeps/356
- Python 3.12 `random` 모듈 문서 문자열(메르센 트위스터, 주기 2**19937−1), `secrets`·PEP 506 — https://peps.python.org/pep-0506/
- J. S. Vitter, "Random Sampling with a Reservoir", ACM TOMS 11(1), 1985(algorithm/39에서 인용).

실험 목록:
- 실험 A(시드별 지터 동기화)·B(Fisher–Yates vs 잘못된 셔플, n=3, 270만 회)·C(`Math.random()` 상태 복원·예측)·D(LCG 하위 비트)·E(`RandomGenerator.getDefault()`): `scratchpad/math/07/e12/Prng.java`, `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) eclipse-temurin:21-jdk java Prng.java 42`(재실행 `7` 두 번). OpenJDK 21.0.12 Temurin, 2026-10-07.
- 실험 F(JS 비교자 셔플 편향): `scratchpad/math/07/e12/sortshuffle.js`, `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) node:22-alpine node sortshuffle.js`(2회). Node v22.23.2.
- 그림의 고정 시드 지터 값(`new Random(42).nextLong(1000)` = 891): `Seed42.java`, 같은 JDK.
- 계산 보조(17! vs 2^48): 호스트 Python 3.12.3.
- 후보 유일성 전수 확인(0 < d < 2^22에서 `|a·d mod 2^48|`(부호 있는 값)의 최솟값 = 34,316,557 > 2^21 — 음수 d는 대칭): `scratchpad/math/adj-07/uniq.c`, 호스트 gcc. 칸 최대 분포(100개 → 10ms 칸 100개, Python `random` seed 1, 2만 회): 3이 2,526·4가 11,500·5가 4,937회, 서로 다른 값 평균 95.21(이론 95.21), 호스트 Python 3.12.3. 2026-10-07.
