# math/05-counting-and-birthday-bound — 경우의 수·비둘기집·이항계수·생일 한계 — 정리 (힌트)

## 해결하는 문제

ID·해시·키의 비트 수를 정할 때 "칸이 43억 개면 충분하겠지"라는 직관은 자주 틀린다.

```text
  직관                                   실제
  32비트 = 약 43억 칸                     무작위로 7.7만 개만 뽑아도 같은 값이 나올 확률 50%
  "43억 개 쓰기 전엔 안 겹친다"           칸 수 N이 아니라 √N 근처에서 충돌이 흔해진다
```

- 세기(counting)가 없으면 "몇 비트면 되나", "언제 처음 겹치나"에 답할 수 없다.
- 답을 못 하면 ID 충돌이 운영 중 **가끔** 나타난다. 재현이 안 돼 원인 찾기가 늦어진다.

쉬운 예: 생일 문제다.
- 한 반 23명이면 생일이 같은 쌍이 있을 확률이 50%를 넘는다(정확히 계산하면 0.5073 — 아래 실험).
- 365일에 비해 23명은 적어 보인다. 하지만 "쌍"의 수는 23·22/2 = 253개다.

똑같은 구조다.\
날짜 365개 = ID 공간 N, 학생 = 발급한 ID k개, 같은 생일 = ID 충돌이다.

실무 예:
- 32비트 무작위 정수를 PK로 쓰는 테이블이 수만 행에서 가끔 `duplicate key value violates unique constraint`(PostgreSQL)를 낸다.
- 짧은 해시 prefix(git 약어 SHA, 짧은 URL 코드, 8자리 hex 캐시 키)가 다른 대상끼리 겹친다.
- 반대로 비트를 아끼는 설계(Snowflake의 ms당 순번 12비트)는 곱 법칙으로 상한을 계산해 둬야 한다.

## 동작·원리

### 1. 곱 법칙·합 법칙 — ID 공간의 크기

```text
  Snowflake 64비트 ID (twitter-archive/snowflake README, 2010)
  [ 부호 1 ][ 시각 41비트 (ms) ][ machine 10비트 ][ sequence 12비트 ]
              2^41 ms ≈ 69.7년       2^10 = 1024대     2^12 = 4096개/ms/대

  서로 다른 ID 수 = 2^41 × 2^10 × 2^12 = 2^63        ← 곱 법칙
```

- *곱 법칙(product rule)*: 독립적으로 고르는 칸이 a, b, c가지면 조합은 a·b·c가지(MCS 15.2).
- *합 법칙(sum rule)*: 겹치지 않는 두 경우가 a, b가지면 합쳐 a + b가지.
- 쓰임: "한 머신이 1ms에 만들 수 있는 ID는 최대 4096개"가 곱 법칙의 마지막 칸에서 바로 나온다. 넘으면 다음 ms까지 기다린다([distributed/13-distributed-id-generation](../../distributed/13-distributed-id-generation/2-summary.md) 장애 4).
- 2^41 ms를 연으로 바꾸면 약 69.7년이다(README는 "69 years"). 사용자 정의 기준 시각(epoch)부터 센다.

### 2. 순열·조합 — 이항계수

```text
  n개에서 k개 고르기
  순서 있음(순열)    n·(n−1)·…·(n−k+1) = n! / (n−k)!
  순서 없음(조합)    C(n, k) = n! / (k!·(n−k)!)        ← 순열을 k!(같은 묶음의 줄 세우기 수)로 나눔

  k개 ID 사이의 "쌍" 수 = C(k, 2) = k(k−1)/2
     k = 23   → 253쌍
     k = 4096 → 8,386,560쌍
```

- *이항계수 C(n, k)*: n개 중 k개를 순서 없이 고르는 방법의 수(MCS 15.5). 나눗셈 규칙(division rule, MCS 15.4) — 같은 묶음을 k!번씩 셌으니 k!로 나눈다.
- 생일 문제의 핵심은 C(k, 2)다. ID는 k개지만 충돌 후보는 쌍이라 k²/2에 비례해 늘어난다.

### 3. 비둘기집 원리 — "반드시 겹친다"의 문턱

```text
  비둘기 |A| 마리, 집 |B|개
  |A| > |B|        → 어느 함수 A→B든 같은 집에 둘 이상     (MCS Rule 15.8.1)
  |A| > k·|B|      → 어느 함수든 같은 집에 k+1 이상         (Rule 15.8.2)

  16비트(hex 4자리) prefix: 칸 65,536개
  객체 65,537개   → 겹치는 prefix가 반드시 있다 (비둘기집, 확률과 무관)
  객체 2,000개    → 비둘기집은 아무 말도 못 한다. 생일 한계는 "평균 30쌍 겹친다"고 말한다
```

- *비둘기집 원리(pigeonhole principle)*: 원소가 칸보다 많으면 어떤 배정이든 칸 하나에 둘 이상이 들어간다.
- 두 도구의 역할이 다르다.
  - 비둘기집: 확실성. "k > N이면 충돌은 피할 수 없다." 무작위성 가정이 필요 없다.
  - 생일 한계: 확률. "k ≈ √N이면 충돌이 흔하다." 균일·독립 가정이 필요하다.
- 실무 결론: 해시를 짧게 자르는 순간 충돌은 "확률이 낮은 사건"에서 출발해, 개수가 칸 수 2^b를 넘으면 "피할 수 없는 사건"이 된다. 자른 키로 대상을 특정하는 코드는 충돌 처리가 필요하다.

### 4. 생일 한계 — 정확식과 근사식

```text
  N칸에 k개를 균일·독립으로 넣을 때

  P(충돌 없음) = (1 − 0/N)(1 − 1/N)…(1 − (k−1)/N)                   정확 (MCS (17.5))
             < exp(−k(k−1)/2N)                                     1 − x < e^(−x) 사용 (MCS (17.7))

  ⇒  1 − exp(−k(k−1)/2N)  <  P(충돌 ≥ 1)  ≤  k(k−1)/2N              (k ≥ 2)
        아래 한계(근사로 많이 씀)                위 한계(합집합 한계, 작은 확률에서 정확)

  충돌 쌍 수의 기댓값 = C(k,2)/N = k(k−1)/2N                         정확(쌍마다 1/N, 기댓값 선형성)
  50%가 되는 k ≈ √(2N·ln 2) ≈ 1.177·√N                              근사
```

- 기호
  - *N*: 칸 수. b비트 ID면 N = 2^b.
  - *k*: 넣은 개수(발급한 ID 수).
  - *exp(x)*: e^x.
- 전제: 값이 **균일**하고 서로 **독립**이다. MCS 17.4도 이 가정을 명시하고, 해시 테이블 충돌이 이 모형에 잘 맞는다고 적는다.
  - 전제가 깨지는 운영 상황: 같은 시드로 시작한 PRNG 인스턴스들, 시각만으로 만든 ID, 분포가 치우친 해시. 이때는 생일 한계보다 **훨씬 빨리** 충돌한다(장애 3).
- MCS는 경험칙으로 "N일에 √(2N)명이면 충돌 확률 ≈ 1 − 1/e ≈ 0.632"를 든다(Birthday Principle). 365일이면 27명에서 정확값 0.6269(≈ 0.627)다(아래 실험).
- `1 − exp(−k²/2N)`(k−1 대신 k)은 위·아래 한계 어느 쪽도 아니다. 작은 N에서 정확값보다 커질 수 있다(아래 N=365 표의 k=23: 0.5155 > 0.5073).

### 실험: 정확값·근사·한계 비교 (계산)

`count05.py` — 정확값은 곱을 로그로 더해 계산했다. 시뮬레이션이 아니라 공식 계산이다.

(실험, Python 3.12.3 표준 라이브러리, 2026-10-07)

```text
N=365:
  k= 23 exact=0.5073  1-exp(-k(k-1)/2N)=0.5000  1-exp(-k^2/2N)=0.5155  union k(k-1)/2N=0.6932
  k= 27 exact=0.6269  1-exp(-k(k-1)/2N)=0.6177  1-exp(-k^2/2N)=0.6316  union k(k-1)/2N=0.9616
  k= 57 exact=0.9901  1-exp(-k(k-1)/2N)=0.9874  1-exp(-k^2/2N)=0.9883  union k(k-1)/2N=4.3726
N=2^32 k=  1000 exact=0.000116 approx=0.000116 union=0.000116
N=2^32 k= 10000 exact=0.011573 approx=0.011573 union=0.011640
N=2^32 k= 77163 exact=0.500000 approx=0.499998 union=0.693143
N=2^32 k=200000 exact=0.990502 approx=0.990501 union=4.656590
```

- 아래 한계 `1 − exp(−k(k−1)/2N)`은 정확값보다 조금 작다. N이 크면(2^32) 소수 넷째 자리까지 같다. N이 작으면(365) 차이가 0.003~0.009다(k=57에서 0.003, k=27에서 0.009).
- 합집합 한계 k(k−1)/2N은 확률이 작을 때(≤ 0.01 근처)만 쓸 만하다. 크면 1을 넘어 의미가 없다.

### 실험: 32·48·64비트 무작위 ID 충돌 — 시뮬레이션 vs 이론

`Birthday05.java` 핵심 — b비트 값 k개를 뽑아 정렬하고 인접한 같은 값을 센다.

```java
long mask = bits == 64 ? -1L : (1L << bits) - 1;
for (int i = 0; i < k; i++) buf[i] = r.nextLong() & mask;     // SplittableRandom(seed)
Arrays.sort(buf, 0, k);
// 같은 값 c개가 연속이면 c(c-1)/2쌍
```

(실험, 시뮬레이션: `SplittableRandom` 시드 1·2·3, 32비트는 k마다 400회·48/64비트는 4회 반복, OpenJDK 21.0.12 Temurin 컨테이너 `--network none --cpus=2 -Xmx600m`, 2026-10-07. 아래는 시드 1, 다른 시드 범위는 글에)

```text
bits=32 k=10,000 trials=400 seed=1 | sim P(>=1)=0.010 exact=0.01157 approx=0.01157 | sim pairs/trial=0.010 expected=0.0116
bits=32 k=30,000 trials=400 seed=1 | sim P(>=1)=0.075 exact=0.09947 approx=0.09947 | sim pairs/trial=0.078 expected=0.105
bits=32 k=77,163 trials=400 seed=1 | sim P(>=1)=0.470 exact=0.5000 approx=0.5000 | sim pairs/trial=0.648 expected=0.693
bits=32 k=150,000 trials=400 seed=1 | sim P(>=1)=0.938 exact=0.9272 approx=0.9271 | sim pairs/trial=2.603 expected=2.62
bits=48 k=20,000,000 trials=4 seed=1 | sim P(>=1)=0.750 exact=0.5086 approx=0.5086 | sim pairs/trial=0.750 expected=0.711
bits=64 k=20,000,000 trials=4 seed=1 | sim P(>=1)=0.000 exact=1.084e-05 approx=1.084e-05 | sim pairs/trial=0.000 expected=1.08e-05
bits= 32  k50%≈7.716e+04   k for P=1e-6 ≈ 92.68
bits= 48  k50%≈1.975e+07   k for P=1e-6 ≈ 2.373e+04
bits= 64  k50%≈5.057e+09   k for P=1e-6 ≈ 6.074e+06
bits=122  k50%≈2.715e+18   k for P=1e-6 ≈ 3.261e+15
```

- 관찰
  - 32비트, k = 77,163에서 충돌 비율이 세 시드에서 0.470·0.515·0.528이었다. 이론값 0.5000 근처다(400회 표본이라 ±0.05 정도 흔들림은 표본 오차 범위 — 해석).
  - 48비트, k = 2천만에서 4회 중 충돌 회차가 시드별 3·1·2회(0.75·0.25·0.50)였다. 4회뿐이라 흔들림이 크지만 이론값 0.51과 같은 크기다.
  - 64비트, k = 2천만에서는 세 시드 모두 0이었다. 이론 기댓값 1.08×10⁻⁵쌍이다.
  - `k50%`·`k for P=1e-6` 줄은 공식 계산값(실측 아님)이다. 32비트 ID는 **93개**만 넘어도 충돌 확률이 백만분의 1을 넘는다.

### 실험: 32비트 PK로 넣다가 처음 실패하는 지점 (sqlite)

(실험, Python 3.12.3 `sqlite3`(SQLite 3.45.1), `random.Random(seed).getrandbits(32)`, 2026-10-07)

```text
seed=1 first failure after 61,451 rows: IntegrityError: UNIQUE constraint failed: t.id
seed=2 first failure after 101,404 rows: IntegrityError: UNIQUE constraint failed: t.id
seed=3 first failure after 47,563 rows: IntegrityError: UNIQUE constraint failed: t.id
seed=4 first failure after 102,983 rows: IntegrityError: UNIQUE constraint failed: t.id
seed=5 first failure after 59,993 rows: IntegrityError: UNIQUE constraint failed: t.id
```

- 첫 실패 지점이 4.8만~10.3만으로 크게 흔들린다. 운영에서는 "어느 날 갑자기 한 번" 보인다.
- 처음 충돌을 일으키는 값이 몇 번째인지(B)의 기댓값은 E(B) = √(πN/2) + 2/3 + O(N^(−1/2))이다(Flajolet·Sedgewick, *Analytic Combinatorics* Example II.10 식 (28) — Knuth TAOCP 1권 1.2.11.3을 같은 계산의 출처로 든다). N = 2^32면 √(πN/2) ≈ 82,137이다(근사).
  - 위 출력의 "after n rows"는 성공한 행 수라 B = n + 1이다. 다섯 시드 평균 74,679는 이 근처다. 표본이 5개뿐이고 B 자체가 실행마다 두 배 넘게 흔들려 평균도 크게 흔들린다(해석).

### 실험: 짧은 해시 prefix — git 약어 SHA

빈 저장소에 서로 다른 blob 2,000개를 넣고 hex 4자리(16비트) prefix를 셌다.

(실험, git 2.43.0, `LC_ALL=C`, 2026-10-07)

```text
objects=2000 distinct 4-hex prefixes=1971 colliding pairs=29 expected≈30.5
error: short object ID 821e is ambiguous
hint: The candidates are:
hint:   821e839 blob
hint:   821e952 blob
fatal: ambiguous argument '821e': unknown revision or path not in the working tree.
```

- 65,536칸에 2,000개 → 비둘기집은 아무것도 보장하지 않지만, 생일 한계 기댓값 C(2000, 2)/65536 ≈ 30.5쌍과 실측 29쌍이 맞다.
- git 문서는 `core.abbrev`가 없으면 저장소 객체 수로 약어 길이를 정해 "당분간" 유일하게 유지하려 한다고 적는다(git-config `core.abbrev`). 객체가 늘면 예전에 적어 둔 짧은 SHA가 모호해질 수 있다는 뜻이다(해석).

## 쓰이는 자료구조·알고리즘

- **해시 테이블 충돌** — 버킷 수 N에 키 k개, 체이닝 길이·충돌 수가 이 계산이다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- **UUID·ULID·Snowflake 비트 설계** — 무작위 부분의 비트 수가 생일 한계를, 순번 비트가 곱 법칙 상한을 정한다. [security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md), [distributed/13-distributed-id-generation](../../distributed/13-distributed-id-generation/2-summary.md), [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md)
- **블룸 필터** — 비트 m개·해시 k개·원소 n개의 오탐률도 같은 세기에서 나온다. [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
- **문자열 해싱(지문)** — 롤링 해시 충돌 확률. [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md)
- **암호 해시의 생일 공격** — n비트 해시의 충돌 저항이 약 n/2비트인 이유. [security/04-hash-functions-and-digests](../../security/04-hash-functions-and-digests/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 어림

- 증상: 가끔 나는 `duplicate key`, 모호한 짧은 ID, 서로 다른 대상이 같은 캐시 항목을 가리킴.
- 어림 순서
  1. 공간 N = 2^b를 센다(무작위 부분 비트만 센다 — 시각·버전 비트는 빼고).
  2. 누적 발급 수 k(지금까지, 그리고 보존 기간 끝까지)를 센다. 단, ID에 시각 필드가 있으면(UUIDv7 — 상위 48비트가 ms 시각, RFC 9562 §5.7) 시각이 다른 ID끼리는 충돌하지 않는다. 그때는 같은 시각 칸(같은 ms)의 발급 수 k_t를 칸마다 센다.
  3. 기대 충돌 쌍을 계산한다. 시각 필드가 없으면 k(k−1)/2N, 있으면 칸별 합 Σ k_t(k_t−1)/2N(무작위 부분이 균일·독립일 때). 0.01보다 크면 "가끔 난다"가 정상이다.

### 2. 설계 → 필요한 비트 수

```text
  P(충돌) ≲ k²/2N ≤ p   ⇒   b = log₂N ≥ 2·log₂k + log₂(1/(2p))

  k = 10^6, p = 10^-6  → b ≥ 58.8 비트
  k = 10^9, p = 10^-6  → b ≥ 78.7 비트
  k = 10^12, p = 10^-6 → b ≥ 98.7 비트     (UUIDv4의 무작위 122비트는 여유가 있다)
```

- 위 수치는 공식 계산값이다. k가 10배 늘면 필요한 비트는 약 6.6비트(2·log₂10) 는다.

### 3. 코드로 확인 — 충돌을 전제로 쓴다

```java
// Java 21: 128비트 무작위 ID(UUIDv4: 무작위 122비트). 충돌 확률이 낮아도 DB 유니크 제약은 둔다
UUID id = UUID.randomUUID();   // Java 문서: "cryptographically strong pseudo random number generator"로 생성

// 어림 계산 도구
static double collisionLowerBound(double bits, double k) {   // 1 − exp(−k(k−1)/2N)
    double n = Math.pow(2, bits);
    return -Math.expm1(-k * (k - 1) / (2 * n));
}
```

- 유니크 제약은 "충돌이 나면 조용히 덮지 말고 실패하라"는 안전망이다. 충돌 시 재시도할지, 경보를 낼지 정한다.
- 짧은 외부 코드(사람이 입력하는 6자리 등)가 필요하면 발급 총량 k로 길이를 정하고, 그래도 남는 충돌은 "발급 시 유니크 검사 + 재시도"로 막는다. 짧은 코드에 겹쳐 둘 방어(만료·시도 상한)는 [security/16](../../security/16-identifiers-and-enumeration/2-summary.md) 적용 3.

## 장애 시나리오와 대처

### 1. 32비트 무작위 ID → 간헐 PK 중복 (⚠ 커리큘럼)

- **현상**: 수만 행 규모 테이블에서 INSERT가 가끔 실패한다. 재시도하면 성공한다.
- **보이는 형태**: PostgreSQL `duplicate key value violates unique constraint`, SQLite `UNIQUE constraint failed`(위 실험 4.8만~10.3만 행에서 첫 실패). 충돌 시 갱신(`ON CONFLICT … DO UPDATE`)하도록 쓴 upsert면 다른 대상의 행을 조용히 덮을 수 있다(`DO NOTHING`이면 덮지 않고 조용히 버린다 — SQLite UPSERT 문서).
- **원인**: 32비트 공간은 약 7.7만 개에서 충돌 확률 50%다(생일 한계, 균일 가정에서).
- **대처**: 무작위 부분을 122비트 이상(UUIDv4)으로 늘리거나, 순번 기반 ID(시퀀스·Snowflake)로 바꾼다. 유니크 제약을 유지하고 upsert 대상 키로 무작위 ID를 쓰지 않는다.

### 2. 짧은 해시 prefix 충돌 (⚠ 커리큘럼)

- **현상**: 짧은 URL·캐시 키·로그 상관 ID가 다른 대상을 가리킨다. 또는 도구가 모호하다며 거부한다.
- **보이는 형태**: `error: short object ID 821e is ambiguous`(git), 캐시에서 엉뚱한 사용자 데이터가 나옴.
- **원인**: 해시를 b비트로 자르면 칸이 2^b로 준다. 2^(b/2) 근처에서 충돌이 흔해지고, 2^b를 넘으면 비둘기집 원리로 피할 수 없다.
- **대처**: 식별에는 전체 해시를 쓰고 prefix는 표시용으로만 쓴다. 캐시 키는 자른 해시만 두지 말고 원래 키를 함께 저장해 비교한다.

### 3. 무작위성 가정 붕괴 → 생일 한계보다 훨씬 빨리 충돌

- **현상**: 계산상 수십억 년에 한 번이어야 할 UUID 충돌이 배포 직후 여러 번 난다.
- **보이는 형태**: 서로 다른 인스턴스가 같은 ID 시퀀스를 만든다. 충돌 ID들의 생성 호스트·시각이 짝을 이룬다.
- **원인**: 생일 한계는 "균일·독립" 전제다. 같은 시드로 시작한 PRNG(컨테이너 이미지에 고정 시드, 시각을 시드로 쓴 동시 기동)나 엔트로피가 부족한 생성기는 이 전제를 깬다. Debian OpenSSL 사고(2008)는 키 공간이 실제로 크게 줄었던 사례다([security/09](../../security/09-randomness-and-key-management/2-summary.md) 장애 3).
- **대처**: ID에는 OS CSPRNG 기반(`SecureRandom`, `UUID.randomUUID()`)을 쓰고, 시드를 직접 넣지 않는다. 의사난수 쪽 원리는 [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md).

### 4. 곱 법칙 상한을 넘는 발급 → 지연·중복

- **현상**: 트래픽 피크에 ID 발급이 느려지거나, worker ID 설정 실수로 ID가 겹친다.
- **보이는 형태**: Snowflake형 생성기에서 ms당 4096개를 넘는 요청이 다음 ms를 기다린다. worker ID가 같은 두 노드는 같은 ms·같은 순번에서 같은 ID를 낸다.
- **원인**: ID 공간 = 시각 × machine × 순번의 곱이다. 한 칸(순번 12비트)의 상한을 넘거나, 다른 칸(machine)의 유일성 전제가 깨졌다.
- **대처**: 피크 발급률을 곱 법칙 상한(4096/ms/worker)과 비교해 비트 배분을 정하고, worker ID는 중앙에서 리스로 배정한다([distributed/13](../../distributed/13-distributed-id-generation/2-summary.md)).

## 핵심 문장

- ID 공간 크기는 곱 법칙으로 세고, 충돌 후보는 개수 k가 아니라 쌍 C(k, 2) = k(k−1)/2로 센다.
- 비둘기집 원리는 "k > N이면 충돌은 피할 수 없다"는 확실성, 생일 한계는 "k ≈ √N이면 충돌이 흔하다"는 확률이다.
- 균일·독립 가정에서 1 − exp(−k(k−1)/2N) < P(충돌) ≤ k(k−1)/2N이다. 32비트는 약 7.7만 개에서 50%다.
- 필요한 비트 수 ≈ 2·log₂k + log₂(1/(2p))다. 발급 수가 10배 늘면 약 6.6비트가 더 필요하다.
- 생일 한계는 무작위성 가정 위에서만 성립한다. 시드·생성기 문제가 있으면 훨씬 빨리 충돌한다.
- 확률이 낮아도 유니크 제약은 둔다. 충돌은 조용한 덮어쓰기가 아니라 보이는 실패여야 한다.

## 관련 주제·근거

- 선행
  - [03-sets-relations-orders](../03-sets-relations-orders/2-summary.md) — 집합·함수(비둘기집은 "함수가 단사일 수 없다"는 말)
- 후속·연결
  - [11-modular-arithmetic](../11-modular-arithmetic/2-summary.md) — 해시값을 칸 번호로 줄이는 `mod`
  - [07-probability-and-bayes](../07-probability-and-bayes/2-summary.md), [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md) — 확률 공간, 기댓값 선형성(충돌 쌍 기댓값)
  - [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md) — 무작위성 가정이 깨지는 곳
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md) · [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) · [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md)
  - [security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md)(생일 경계·UUID 비트 배치·32비트 실험) · [security/09-randomness-and-key-management](../../security/09-randomness-and-key-management/2-summary.md) · [security/04-hash-functions-and-digests](../../security/04-hash-functions-and-digests/2-summary.md)
  - [distributed/13-distributed-id-generation](../../distributed/13-distributed-id-generation/2-summary.md) · [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md)
- 교재
  - MIT 6.042 MCS(2018-06-06판 PDF <https://courses.csail.mit.edu/6.042/spring18/mcs.pdf>) — 15.2 Counting Sequences(곱 법칙), 15.4 Division Rule, 15.5 Counting Subsets(이항계수), 15.8 Pigeonhole Principle(Rule 15.8.1·15.8.2), 17.4 The Birthday Principle(정확식 (17.5), 부등식 (17.7), √(2d)명 ≈ 1 − 1/e, 해시 테이블 충돌 모형)
  - CLRS 3판 5.4(생일 역설 소절 — 소절 번호 5.4.1은 확인 못 함 `[?]`)
  - P. Flajolet, R. Sedgewick, *Analytic Combinatorics*(Cambridge University Press, 2009; 저자 공개 PDF <https://algo.inria.fr/flajolet/Publications/book.pdf>) — Example II.10 Birthday paradox, 식 (28) E(B) = √(πr/2) + 2/3 + O(r^(−1/2))
- 문서·소스
  - twitter-archive/snowflake README(2010 브랜치) — 시각 41비트(69년), machine 10비트, sequence 12비트 <https://github.com/twitter-archive/snowflake/tree/snowflake-2010>
  - git-config `core.abbrev` — 객체 수로 약어 길이 자동 결정, 최소 4 <https://git-scm.com/docs/git-config>
  - RFC 9562(UUID) — UUIDv4 무작위 122비트(§5.4), 충돌 저항 권고(§6.7)는 [security/16](../../security/16-identifiers-and-enumeration/2-summary.md)에 정리
- 실험 목록
  - `count05.py` — N=365·2^32에서 정확값·아래 한계·k² 근사·합집합 한계 계산, C(4096,2)=8,386,560, sqlite 32비트 PK 첫 실패 지점(시드 1~5). Python 3.12.3, SQLite 3.45.1, 2026-10-07.
  - `Birthday05.java` — 32비트(k 1만·3만·77,163·15만, 400회), 48·64비트(k 2천만, 4회) 충돌 시뮬레이션, 시드 1·2·3. OpenJDK 21.0.12 Temurin 컨테이너(`--network none --cpus=2 -Xmx600m`), 실행당 약 80초.
  - git 2.43.0 — blob 2,000개의 hex 4자리 prefix 충돌 수, `short object ID ... is ambiguous` 확인(scratchpad 임시 저장소).
