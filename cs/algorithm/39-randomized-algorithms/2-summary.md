# algorithm/39-randomized-algorithms — 라스베이거스·몬테카를로, 기대 복잡도 — 정리 (힌트)

## 해결하는 문제

결정적 알고리즘은 입력이 같으면 하는 일도 같다. 그래서 **최악의 입력이 정해져 있다.** 그 입력을 우연히(이미 정렬된 데이터) 만나거나, 누가 일부러 보내면 최악이 재현된다.

```text
  결정적 퀵정렬(마지막 원소 피벗)                    무작위 피벗 퀵정렬
  입력: 1 2 3 4 5 6 7 8   (이미 정렬)                 입력: 1 2 3 4 5 6 7 8
  피벗 8 → [1..7] | []                                피벗 = 무작위 → 대개 가운데 근처
  피벗 7 → [1..6] | []                                → 깊이 ~log n
  ... 깊이 n, 비교 n(n-1)/2                           비교 기대값 ~2n ln n
  최악 입력 = "정렬된 배열"로 고정                      최악은 "운이 나쁜 동전"이고, 입력이 고르지 못한다
```

- *무작위 알고리즘(randomized algorithm)*: 실행 중 난수를 써서 다음 행동을 고르는 알고리즘. 같은 입력이라도 실행마다 경로가 다를 수 있다.
- 무작위화가 하는 일: 최악의 원인을 **입력**에서 **동전 던지기**로 옮긴다. 입력을 고르는 사람(공격자 포함)은 동전을 고르지 못한다.

쉬운 예: 시험 자리 배치를 매번 같은 규칙(이름순)으로 하면 친구끼리 붙어 앉는 계획을 세울 수 있다. 매번 제비뽑기를 하면 계획이 통하지 않는다.

똑같은 구조다. 단, 제비뽑기 결과를 미리 아는 사람(시드를 아는 사람)에게는 다시 계획이 통한다.

또 하나의 쓰임: **조금 틀려도 되는 대신 훨씬 빠른** 답. 큰 수가 소수인지 확인할 때, 약수를 다 시도하는 대신 무작위 검사를 몇 번 해서 "합성수일 확률이 2^-100 이하"로 끝낸다.

실무 예:
- 정렬 전 셔플, 무작위 피벗, 스킵 리스트의 무작위 높이.
- RSA 키 생성의 확률적 소수 판정(`BigInteger.probablePrime`).
- 재시도 지터, 로그·트레이스 샘플링.

## 동작·원리

### 1. 두 종류 — 무엇이 무작위인가

```text
                      답                         실행 시간
  라스베이거스      정확하다                     무작위 (기대값으로 말한다)
  (Las Vegas)       예) 무작위 피벗 퀵정렬        예) 비교 수 기대값 ~2n ln n

  몬테카를로        틀릴 수 있다 (확률 상한)      상한이 정해져 있다
  (Monte Carlo)     예) Miller–Rabin 소수 판정    예) 라운드 수 × 거듭제곱 비용
```

- *라스베이거스 알고리즘*: 답은 정확하고, 걸리는 시간이 무작위인 알고리즘.
- *몬테카를로 알고리즘*: 시간은 정해져 있고, 답이 틀릴 확률이 있는 알고리즘. 반복하면 오류 확률이 곱으로 준다.
- 변환: 답을 싸게 검증할 수 있으면 몬테카를로를 "검증될 때까지 반복"으로 라스베이거스로 바꿀 수 있다.

### 2. "평균"과 "기대값"은 다르다

```text
  평균 실행 시간 (확률적 분석, CLRS 5.1~5.2)         기대 실행 시간 (무작위 알고리즘, CLRS 5.3)
  알고리즘: 결정적                                  알고리즘: 난수를 쓴다
  무작위인 것: 입력 (예: "입력 순열이 균등하다" 가정)     무작위인 것: 알고리즘의 동전
  가정이 깨지면(정렬된 입력) 보장이 사라진다             어떤 입력이 와도 같은 기대값 상한 보장(키가 서로 다를 때)
```

- 두 용어의 구분은 CLRS 5장의 관행이다. 수학적으로는 둘 다 기댓값(평균)이고, 차이는 **어느 확률분포**(입력 분포 vs 알고리즘의 난수)에 대해 평균을 내느냐다. Sedgewick 4판은 셔플한 퀵정렬도 "on the average"로 쓴다.

- *확률적 분석(probabilistic analysis)*: 입력이 어떤 분포를 따른다고 가정하고 실행 시간의 평균을 구하는 분석(CLRS 5장).
- *기대 실행 시간(expected running time)*: 알고리즘 자신의 난수에 대한 기대값. 입력은 최악으로 골라도 된다.
  - 흔한 오해: "퀵정렬은 평균 O(n log n)이니 괜찮다." 결정적 피벗이면 그 "평균"은 입력 분포 가정 위에 있다. 정렬된 입력처럼 분포 가정이 깨진 데이터에서 O(n²)이 된다(아래 실험 A).
- 분석 도구: *지시 확률 변수(indicator random variable)*와 기댓값의 선형성(CLRS 5.2). 무작위 퀵정렬에서 i번째·j번째로 작은 원소가 비교될 확률은 `2/(j-i+1)`이고, 이를 전부 더하면 O(n log n)이다(CLRS 7.4.2 — 원소가 서로 다르다는 전제). 아래 Lomuto 코드는 `<`로만 왼쪽에 보내므로 키가 전부 같으면 시드와 무관하게 `n(n-1)/2`번 비교한다. 중복 키가 많으면 3방향 분할을 쓴다(Sedgewick 4판 2.3). 꼬리 부등식은 수학 영역 [08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md)에서 다룬다.

### 3. 무작위 피벗 퀵정렬

```java
static <T> void qs(T[] a, int lo, int hi, Comparator<T> c, Random rnd) {
    while (lo < hi) {
        int p = rnd == null ? hi : lo + rnd.nextInt(hi - lo + 1);   // null이면 고정 피벗(마지막 원소)
        T t = a[p]; a[p] = a[hi]; a[hi] = t;
        T pivot = a[hi]; int i = lo;
        for (int j = lo; j < hi; j++) {                              // Lomuto 분할: 비교 hi-lo번
            cmps++;
            if (c.compare(a[j], pivot) < 0) { T u = a[i]; a[i] = a[j]; a[j] = u; i++; }
        }
        t = a[i]; a[i] = a[hi]; a[hi] = t;
        if (i - lo < hi - i) { qs(a, lo, i - 1, c, rnd); lo = i + 1; }   // 작은 쪽만 재귀 → 스택 깊이 O(log n)
        else { qs(a, i + 1, hi, c, rnd); hi = i - 1; }
    }
}
```

- 작은 쪽만 재귀하고 큰 쪽은 반복으로 돈다. 비교 수가 n²이 되는 최악에서도 스택 깊이는 O(log n)이다. 이 처리가 없으면 고정 피벗 + 정렬된 입력에서 재귀 깊이가 n이 된다.

### 실험 A: 이미 정렬된 입력 — 고정 피벗 vs 무작위 피벗

(실험, OpenJDK 21.0.12 Temurin, `docker --cpus=2`, 2026-10-05 — random 열은 실행마다 다르다)

```text
[A] 이미 정렬된 입력: 비교 횟수
      n    fixed(last)         random    2n ln n
   2000        1999000          25291      30404
   4000        7998000          53521      66352
   8000       31996000         121942     143795
  16000      127992000         261352     309771
```

- 고정 피벗: 정확히 `n(n-1)/2`(2000 → 1,999,000). n이 두 배면 4배다. O(n²).
- 무작위 피벗: n이 두 배면 약 2.1~2.3배. O(n log n). 사실 점검 재실행에서는 23863 → 52742 → 127466 → 250059로 약 2.0~2.4배였다(실행마다 다르다).
- `2n ln n`은 점근 근사(Sedgewick 4판 2.3: "~2 N ln N compares … on the average")라 작은 n에서는 실제보다 크다. 같은 비교 규칙(분할당 n−1번)의 정확한 기대값은 점화식 `C(n) = (n−1) + (2/n)ΣC(k)`의 해 `2(n+1)H(n) − 4n`이다(H(n) = 조화수). n=10000이면 약 155,772.

### 실험 C: 같은 입력, 시드 1000개 — 라스베이거스의 "시간만 무작위"

입력 = n=10000짜리 고정 순열 하나. 시드 0~999로 각각 정렬했다. 1000번 다 정렬 검사를 통과했다.

```text
[C] 같은 입력(n=10000 무작위 순열), 시드 1000개: 비교 횟수 분포 — 1000회 모두 정렬 검사 통과
  min=142147 p50=154979 p99=173658 max=185312 mean=155526  (2n ln n=184207)
```

- 1000회 각각 결과 배열의 정렬 여부를 검사했고, 전부 통과했다. 답은 같고 비교 수(시간)만 달랐다.
- 평균 155,526은 정확한 기대값 155,772와 0.2% 차이다. 최대(185,312)도 평균의 1.2배 안이다.
- Sedgewick 4판 2.3(algs4 사이트)은 실행 시간의 표준편차를 약 0.65N으로 적고, 그래서 N이 커질수록 실행 시간이 평균에 몰리며 평균에서 크게 벗어날 가능성은 작다고 설명한다.

### 4. 시드를 아는 공격자 — 무작위가 다시 결정적이 된다

```text
  McIlroy 1999 "A Killer Adversary for Quicksort"
  ① 값을 아직 정하지 않은 원소("gas")로 시작한다
  ② 정렬 함수가 두 gas를 비교하면, 한쪽을 "지금까지 확정된 것 중 다음으로 작은 값"으로 굳힌다
     이때 피벗 후보(가장 최근 비교에서 살아남은 gas)를 우선 굳힌다 → 피벗이 작은 값이 된다
  ③ 피벗이 매번 가장 작은 쪽이 되도록 답하며 정렬을 끝까지 돌린다
  ④ 그때 굳힌 값들이 곧 최악 입력이다
  만든 입력을 재사용하는 조건: 같은 시드 → 같은 피벗 순서 → 같은 비교 순서
```

- McIlroy 논문은 이 방법이 무작위화한 구현을 포함해 "very mild and realistic assumptions"를 만족하는 퀵정렬에 통한다고 했다. 적대자가 비교 함수를 쥐고 실행 중에 값을 정하면, 무작위 피벗이어도 시드를 몰라도 그 실행은 n²이 된다. 시드 지식이 필요한 것은 아래 실험 B처럼 그렇게 만든 입력을 **고정 입력으로 재사용**할 때다(같은 시드여야 같은 비교 순서가 나온다).

### 실험 B: 시드 42를 아는 공격자가 만든 입력

```java
Comparator<Integer> adv = (x, y) -> {           // McIlroy 적대자 (gas = 미확정)
    if (val[x] == gas && val[y] == gas) { if (x == candidate) val[x] = nsolid++; else val[y] = nsolid++; }
    if (val[x] == gas) candidate = x; else if (val[y] == gas) candidate = y;
    return Integer.compare(val[x], val[y]);
};
qs(idx, 0, n - 1, adv, new Random(42));         // 시드 42로 한 번 돌려 입력을 "만든다"
```

(실험, 같은 환경. `new Random()` 열은 실행마다 다르다)

```text
[B] 시드 42를 아는 공격자가 만든 입력(McIlroy 적대자)
      n        seed=42        seed=43   new Random()
   2000        1999000          23624          25126
   4000        7998000          53252          55407
   8000       31996000         118397         128579
  16000      127992000         265755         261935
```

- 시드 42로 정렬하면 비교 수가 정확히 `n(n-1)/2`다. 고정 피벗의 최악과 같다.
- 같은 입력을 시드 43이나 새 시드로 정렬하면, 측정한 네 크기에서 비교 수가 `n log n` 규모로 돌아왔다.
- 교훈: 무작위 알고리즘의 보장은 **공격자가 동전을 모른다**는 가정 위에 있다. 운영 코드에 `new Random(42)` 같은 고정 시드를 두면 그 가정이 깨진다.
- 참고: `java.util.Random`은 48비트 시드의 선형 합동 생성기이고, Javadoc이 "not cryptographically secure"라고 적는다. 공격자가 출력을 관찰할 수 있으면 시드가 고정이 아니어도 안전하다고 단정하지 않는다. 보안 경계에서는 `SecureRandom`이다.
- 다른 방어: OpenJDK 21의 `DualPivotQuicksort`(원시형 `Arrays.sort`)는 무작위화 대신, 분할 한 단계마다 `bits`에 `DELTA`(= 6)를 더해 `MAX_RECURSION_DEPTH`(= 64 × DELTA)를 넘으면(즉 분할 깊이 약 64단계) 그 구간을 힙 정렬로 바꾼다. 최악 O(n log n)을 결정적으로 막는 방식이다.

### 5. 몬테카를로 — 소수 판정

```text
  페르마 검사: a^(n-1) ≡ 1 (mod n) 이면 "소수일 수도"
     → 카마이클 수(561 = 3·11·17 …)는 n과 서로소인 a에 전부 통과한다 = 반복해도 잘 안 잡힌다

  Miller–Rabin: n-1 = 2^s·d,  x = a^d mod n 에서 시작해 제곱을 반복
     → 1의 "비자명한 제곱근"이 나오면 합성수 확정
     → 홀수 합성수에 대해 거짓말쟁이 밑 a는 1/4 이하 (Rabin–Monier 1980)
     → k라운드 독립 반복: 오류 ≤ (1/4)^k
```

- *거짓말쟁이(liar)*: 합성수 n에 대해 검사를 통과시키는 밑 a.
- 한쪽 오류(one-sided error): "합성수"라는 답은 확실하다. "소수"라는 답만 틀릴 수 있다.

### 실험 D: 카마이클 수의 거짓말쟁이 비율, `BigInteger.isProbablePrime` 오류 수

(실험, OpenJDK 21.0.12 Temurin, `--cpus=2`, 2026-10-05)

```text
[1] 카마이클 수: 밑 a(2..n-2) 중 '소수일 수도'라고 잘못 답하는 비율
  n=  561  Fermat 거짓말쟁이  57.0%   Miller-Rabin 거짓말쟁이  1.4%
  n= 1105  Fermat 거짓말쟁이  69.5%   Miller-Rabin 거짓말쟁이  2.5%
  n= 1729  Fermat 거짓말쟁이  75.0%   Miller-Rabin 거짓말쟁이  9.3%
  n= 2465  Fermat 거짓말쟁이  72.7%   Miller-Rabin 거짓말쟁이  2.8%
  n= 2821  Fermat 거짓말쟁이  76.6%   Miller-Rabin 거짓말쟁이  9.5%
  n= 6601  Fermat 거짓말쟁이  80.0%   Miller-Rabin 거짓말쟁이  5.0%
  n= 8911  Fermat 거짓말쟁이  80.0%   Miller-Rabin 거짓말쟁이 20.0%
[2] 홀수 합성수 3 < n < 200000 에 BigInteger.isProbablePrime(certainty) — '소수'라고 틀린 개수
  certainty= 1 run1: 틀림 52 / 합성수 82016
  certainty= 1 run2: 틀림 50 / 합성수 82016
  certainty= 2 run1: 틀림 42 / 합성수 82016
  certainty= 2 run2: 틀림 53 / 합성수 82016
  certainty= 4 run1: 틀림 4 / 합성수 82016
  certainty= 4 run2: 틀림 0 / 합성수 82016
  certainty=10 run1: 틀림 0 / 합성수 82016
  certainty=10 run2: 틀림 0 / 합성수 82016
```

- 페르마 거짓말쟁이는 57~80%다. 카마이클 수에서는 n과 서로소인 밑이 전부 거짓말쟁이라, 잡히는 것은 n과 공약수가 있는 밑뿐이다.
- Miller–Rabin 거짓말쟁이는 최대 20%(8911)로 1/4 상한 안이다.
- `isProbablePrime`: Javadoc은 "the probability that this BigInteger is prime exceeds (1 - 1/2^certainty)"라고 약속한다. OpenJDK 21 `primeToCertainty`는 100비트 미만 수에 Miller–Rabin을 `(certainty+1)/2`라운드(최대 50) 돈다. 그래서 certainty 1·2는 1라운드, 4는 2라운드, 10은 5라운드다.
  - 같은 certainty에서도 실행마다 틀린 개수가 다르다(52 vs 50, 4 vs 0). 무작위 밑을 쓰기 때문이다. 사실 점검 재실행에서는 certainty 1이 44·54개, 4가 1·4개, 10이 0·0개였다.
  - 100비트 이상이면 Lucas 확률적 소수 판정을 더한다(같은 메서드, 소스의 메서드 이름은 `passesLucasLehmer` — Jacobi 기호와 Lucas 수열을 쓰며, 메르센 수용 Lucas–Lehmer 판정과는 다르다).

### 6. 다른 무작위 도구

```text
  스킵 리스트: 새 노드 높이 = 동전 앞면이 나오는 동안 +1  → 기대 높이 O(log n)
  저수지 표집: 처음 k개는 그대로 채우고, i>k번째 원소는 확률 k/i로 저장소의 무작위 칸과 바꾼다 → 길이 모르는 스트림에서 균등 k개
  지터 재시도: 대기 = random(0, base·2^attempt)   → 동시에 재시도하는 무리를 흩는다
```

- 저수지 표집 실험(같은 환경, `ThreadLocalRandom`): 스트림 1..10에서 3개씩 30만 회 뽑았다. 기대 90,000회.

```text
스트림 1..10에서 3개씩 300000회 표집 — 각 원소가 뽑힌 횟수 (기대 90000)
1:89802  2:90176  3:89413  4:89976  5:90305  6:90066  7:90311  8:90247  9:89540  10:90164
```

## 쓰이는 자료구조·알고리즘

이 주제가 쓰는 하위 구조:
- 의사난수 생성기(`Random`, `ThreadLocalRandom`, `SecureRandom`).
- 기대값·꼬리 부등식(수학 영역 [08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md)).
- 분할(퀵정렬, [03-quick-sort](../03-quick-sort/2-summary.md)), 모듈러 거듭제곱([28-number-theory](../28-number-theory/2-summary.md)).

이 주제를 쓰는 곳(🔧):
- 랜덤 피벗·셔플 후 정렬([03-quick-sort](../03-quick-sort/2-summary.md)).
- 스킵 리스트([12-skip-list](../../data-structure/12-skip-list/2-summary.md)), 블룸 필터·HyperLogLog의 해시 기반 확률 구조([11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md), [19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)).
- 유니버설 해싱([12-hash-functions](../12-hash-functions/2-summary.md)), 롤링 해시의 무작위 base([27-string-hashing](../27-string-hashing/2-summary.md)).
- 샘플링, 재시도 지터([06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)), 속성 기반 테스트([14-property-based-testing](../../testing/14-property-based-testing/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 언제 무작위화를 고르나

```text
  최악 입력을 외부가 고를 수 있나? ──예──> 무작위화(시드는 예측 불가하게) 또는 결정적 최악 보장(인트로소트식 대체)
  정확한 답이 비싼가, 오류 확률을 수치로 허용할 수 있나? ──예──> 몬테카를로 + 반복 횟수로 오류 상한 조정
  재현이 필요한가(테스트·디버깅)? ──예──> 시드를 고정하지 말고 "기록"한다. 실패 시 그 시드로 재실행
```

### 2. Java 코드 습관

```java
// 정렬 전에 섞기 (Sedgewick 4판 2.3의 방식) — 결정적 퀵정렬을 라스베이거스로
Collections.shuffle(list, ThreadLocalRandom.current());

// 멀티스레드에서는 공유 Random 대신 ThreadLocalRandom (Random Javadoc: 공유 시 경합)
int i = ThreadLocalRandom.current().nextInt(n);

// 저수지 표집 (Algorithm R, Vitter 1985가 분석한 계열)
int[] res = new int[k]; int seen = 0;
for (int x : stream) {
    if (seen < k) res[seen] = x;
    else { int j = ThreadLocalRandom.current().nextInt(seen + 1); if (j < k) res[j] = x; }
    seen++;
}

// 확률적 소수: 오류 상한을 숫자로 정한다
boolean p = n.isProbablePrime(100);                       // 소수 아닐 확률 < 2^-100 (Javadoc)
BigInteger q = BigInteger.probablePrime(2048, new SecureRandom());   // 키 생성은 SecureRandom
```

### 3. 테스트에서의 시드

```java
long seed = Long.getLong("test.seed", System.nanoTime());
System.out.println("seed=" + seed);                       // 실패하면 -Dtest.seed=<값>으로 재현
Random rnd = new Random(seed);
```

- 시드를 고정하면 무작위 테스트가 늘 같은 경우만 본다. 매번 바꾸고 기록하는 편이 결함을 더 넓게 찾는다.

### 4. 진단 — "가끔만 느리다"가 무작위성 탓인가

- 같은 입력을 여러 번 돌려 시간 분포를 본다(실험 C처럼). 분포가 좁은데 특정 입력에서만 느리면 입력 쪽 원인이다.
- 특정 입력에서 매번 느리면 결정적 피벗·고정 시드를 의심한다. 비교 수를 세어 `n(n-1)/2`에 가까운지 본다.
- 깊은 재귀 스택(`StackOverflowError`, 덤프의 같은 프레임 수천 개)은 분할이 한쪽으로 쏠린다는 신호다.

## 장애 시나리오와 대처

### 1. 결정적 시드 → 적대적 입력에 최악 재현

- 현상: 특정 사용자가 올린 데이터에서만 정렬·처리 API가 수십~수천 배 느리다. 재시도해도 매번 같다.
- 보이는 형태: 해당 요청의 CPU 시간이 입력 크기의 제곱으로 는다. 프로파일에서 비교 함수가 상위. 같은 요청을 다시 보내면 똑같이 느리다.
- 원인: 무작위 피벗·셔플에 `new Random(42)` 같은 고정 시드를 썼다. 시드를 아는(소스·바이너리를 본) 공격자는 McIlroy 방식으로 최악 입력을 미리 만든다(실험 B: 시드 42에서 정확히 `n(n-1)/2`).
- 대처: 운영 코드에서 시드를 고정하지 않는다(`ThreadLocalRandom`, 보안 경계면 `SecureRandom`). 또는 결정적 최악 보장(힙 정렬 대체, OpenJDK `DualPivotQuicksort`의 `MAX_RECURSION_DEPTH`)을 더한다. 입력 크기 상한을 둔다.
- ⚠ 커리큘럼: "결정적 시드 → 적대적 입력에 최악 재현".

### 2. 고정 피벗 + 정렬된 입력 → O(n²)·스택 오버플로

- 현상: 어제 정렬해 저장한 데이터를 다시 정렬하는 배치가 갑자기 느려지거나 죽는다.
- 보이는 형태: 비교 수 `n(n-1)/2`(실험 A: 16000개 → 127,992,000). 재귀 구현이면 `java.lang.StackOverflowError`와 같은 프레임 수천 줄.
- 원인: "평균 O(n log n)"이 입력 순서가 무작위라는 분포 가정 위에 있었다. 이미 정렬된 입력은 그 가정을 깬다.
- 대처: 무작위 피벗 또는 정렬 전 셔플. 작은 쪽만 재귀. 실무에서는 직접 구현보다 `Arrays.sort`·`List.sort`를 쓴다.

### 3. 몬테카를로 오류 허용치를 낮게 잡았다

- 현상: 소수라고 판정한 수로 만든 키·해시 테이블 크기가 가끔 이상하다.
- 보이는 형태: 같은 입력 집합에서 실행마다 "소수" 판정이 달라진다(실험 D: certainty 1에서 홀수 합성수 82,016개 중 44~54개를 소수로 판정, 재실행 포함 네 번).
- 원인: `isProbablePrime(1)`은 오류 상한이 1/2이다. 이 구현에서 100비트 미만이면 Miller–Rabin 1라운드뿐이다.
- 대처: certainty를 용도에 맞게 높인다(암호 용도는 라이브러리 기본값·표준을 따른다). 작은 범위는 결정적 방법(체, 고정 밑 집합)을 쓴다.

### 4. 무작위 테스트가 가끔 실패하는데 재현이 안 된다

- 현상: CI에서 100번에 한 번 실패한다. 로컬에서 안 된다.
- 보이는 형태: 실패 로그에 입력이 없다. 재실행하면 통과한다.
- 원인: 시드를 기록하지 않았다. 또는 실제로 확률적 성질(예: "분포가 균등하다")을 고정 임계로 검사해 확률적으로 실패한다.
- 대처: 시드 출력·주입(적용 3절). 확률적 성질은 실패 확률을 계산해 임계를 정하고, 그 확률을 테스트 이름이나 주석에 적는다([09-flaky-tests](../../testing/09-flaky-tests/2-summary.md)).

### 5. 공유 `Random` 경합

- 현상: 스레드를 늘렸는데 난수 생성 구간 처리량이 늘지 않는다.
- 보이는 형태: 프로파일에서 `Random.next`의 CAS 재시도 비중이 크다.
- 원인: `java.util.Random`은 스레드 안전하지만, 같은 인스턴스를 여러 스레드가 쓰면 경합한다(OpenJDK 21 Javadoc).
- 대처: `ThreadLocalRandom.current()`.

## 핵심 문장

- 무작위화는 최악의 원인을 입력에서 동전으로 옮긴다. 입력을 고르는 사람은 동전을 고르지 못한다.
- 라스베이거스는 답이 정확하고 시간이 무작위다. 몬테카를로는 시간이 정해져 있고 답이 틀릴 확률이 있다.
- "평균"은 입력 분포에 대한, "기대값"은 알고리즘의 동전에 대한 기댓값이다(CLRS 용어). 정렬된 입력이 깨는 것은 앞쪽이다.
- 시드를 아는 공격자에게 무작위 알고리즘은 결정적 알고리즘이다. 운영 시드는 고정하지 않고, 테스트 시드는 기록한다.
- 몬테카를로의 오류는 반복으로 곱해 줄인다. Miller–Rabin은 라운드마다 1/4 이하라 k라운드면 (1/4)^k 이하다.

## 관련 주제·근거

선행·후속:
- 선행: 기대값·분산·꼬리(수학 영역 [08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md)), 퀵정렬([03-quick-sort](../03-quick-sort/2-summary.md)).
- 함께: 해시 함수·유니버설 해싱([12-hash-functions](../12-hash-functions/2-summary.md)), 스킵 리스트([12-skip-list](../../data-structure/12-skip-list/2-summary.md)), 확률적 카운팅([19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)).
- 후속: 복잡도 이론([40-complexity-p-np](../40-complexity-p-np/2-summary.md)) — 근사·휴리스틱이 "정확하지만 느린" 대신 무엇을 내주는지. 커리큘럼 표는 [../curriculum.md](../curriculum.md).

근거:
- CLRS 3판 5장(확률적 분석과 무작위 알고리즘, 5.2 지시 확률 변수, 5.3 무작위 알고리즘), 7.3(무작위 퀵정렬)·7.4(분석), 31.8(소수 판정).
- Sedgewick·Wayne 『Algorithms』 4판 2.3 — https://algs4.cs.princeton.edu/23quicksort/ ("~2 N ln N compares … on the average", "~N²/2 compares in the worst case, but random shuffling protects against this case").
- M. D. McIlroy, "A Killer Adversary for Quicksort", Software—Practice and Experience 29(4), 1999 — https://www.cs.dartmouth.edu/~doug/mdmspe.pdf
- Miller–Rabin 거짓말쟁이 1/4 상한(Rabin–Monier 1980): K. Conrad, "The Miller–Rabin Test" — https://kconrad.math.uconn.edu/blurbs/ugradnumthy/millerrabin.pdf
- J. S. Vitter, "Random Sampling with a Reservoir", ACM TOMS 11(1):37–57, 1985.
- OpenJDK 21 소스(github.com/openjdk/jdk21u): `java/math/BigInteger.java`(`isProbablePrime` Javadoc, `primeToCertainty`), `java/util/Random.java`(48비트 LCG, 스레드 경합·비암호 Javadoc, 기본 생성자 `seedUniquifier() ^ System.nanoTime()`), `java/util/DualPivotQuicksort.java`(`MAX_RECURSION_DEPTH = 64 * DELTA`, 힙 정렬 대체).

실험 목록(전부 2026-10-05, OpenJDK 21.0.12 Temurin 컨테이너 `--cpus=2 --network none`):
- 실험 A·B·C(정렬된 입력, McIlroy 적대 입력, 시드 1000개 분포): `QuickRand.java`(C만: `java QuickRand.java C`).
- 실험 D(카마이클 수 거짓말쟁이, `isProbablePrime` 오류 수): `Primality.java`.
- 저수지 표집 균등성: `Reservoir.java`.
