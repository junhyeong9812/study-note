# math/15-numerical-stability — 부동소수 오차 누적·파국적 상쇄·Kahan 합 — 정리 (힌트)

## 해결하는 문제

부동소수 연산 한 번의 오차는 아주 작다(binary64에서 상대 오차 약 10⁻¹⁶).\
문제는 그 오차가 **쌓이거나**, 뺄셈 한 번에 **확대되는** 경우다.

쉬운 예: 저울 하나로 트럭 위 모래알 무게를 잰다.

```text
  트럭 10톤 위에 모래 1g 올림 → 저울 눈금 1kg 단위라 그대로 10톤
  모래 1g을 1000번 올림       → 매번 "변화 없음", 1kg이 사라짐
  모래끼리 먼저 모아 1kg을 만든 뒤 올림 → 10톤 1kg
```

- 큰 수 옆에서는 작은 수가 눈금(간격)보다 작아 반올림으로 사라진다.
- 같은 수들도 **더하는 순서**에 따라 결과가 달라진다.

똑같은 구조다.\
실무 예:
- 거래 1천만 건의 금액을 `double`로 더한 집계가 정수 센트로 더한 원장과 맞지 않는다.
- 같은 데이터로 병렬 집계를 돌렸는데 코어 수·병렬도 설정을 바꾸자 마지막 자리가 바뀌어 스냅샷 테스트가 깨진다.
- `E[X²] − E[X]²`로 분산을 구했더니 음수가 나와 표준편차가 `NaN`이 된다.

부동소수 형식(부호·지수·가수, 특수값)은 architecture 영역의 [03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md)(원고 [foundations/data-representation](../../foundations/data-representation/README.md) §2)에 있다. 돈 계산의 반올림 규칙은 [domain-modeling/14-money-arithmetic-rounding-allocation](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md)에 있다. 여기서는 **오차가 어떻게 자라고 어떻게 막는지**를 다룬다.

## 동작·원리

### 1. 간격(ulp)과 반올림 한 번의 오차

```text
  binary64 수직선 (가수 53비트) — 간격이 2배씩 커진다

  [1, 2)        간격 2⁻⁵²  ≈ 2.2×10⁻¹⁶
  [2, 4)        간격 2⁻⁵¹
  ...
  [2⁵³, 2⁵⁴)    간격 2         ← 9.007×10¹⁵ 이상에서는 홀수 정수를 못 담는다

  1e16 = 10,000,000,000,000,000 은 [2⁵³, 2⁵⁴) 구간 → 간격 2
  1e16 + 1 은 1e16 과 1e16+2 의 정확히 가운데 → 짝수 쪽(1e16)으로 반올림
```

- *ulp(unit in the last place)*: 그 수 근처에서 표현 가능한 이웃 수와의 간격. Java `Math.ulp(x)`.
- *반올림 단위 u*: binary64에서 `u = 2⁻⁵³ ≈ 1.1×10⁻¹⁶`. 기본 반올림(가장 가까운 값, 동률이면 짝수)에서 연산 한 번의 상대 오차 상한이다.
  - 흔한 오해: "머신 엡실론"을 책마다 다르게 쓴다. Java `Math.ulp(1.0)`·Python `sys.float_info.epsilon`은 2⁻⁵²(1 다음 수와의 간격)이고, 오차 분석 책은 2⁻⁵³(u)을 쓰기도 한다.
- *표준 모델*: 오버플로·언더플로가 없으면 `fl(a ⊕ b) = (a ⊕ b)(1 + δ)`, `|δ| ≤ u`. 덧셈 한 번은 정확한 값에 **상대 오차 u 이하**만 더한다(Higham — 장 번호 `[?]`, Goldberg 1991).
- 문제는 이 한 번이 아니다. ① 같은 누적 변수에 오차가 계속 쌓이는 것, ② 오차를 품은 두 수를 빼서 상대 오차가 확대되는 것이다.

#### 실험: 사라지는 작은 수

- 코드 핵심(`Numeric.java`):

```java
double big = 1e16; for (int i = 0; i < 1000; i++) big += 1.0;      // 1000을 더했다
float f = 0f; for (int i = 0; i < 20_000_000; i++) f += 1.0f;       // 2천만 번 1을 더했다
```

(실험, OpenJDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-07 — 결정적 연산, 3회 실행 같은 출력)

```text
0.1 + 0.2 = 0.30000000000000004   == 0.3 ? false
new BigDecimal(0.1) = 0.1000000000000000055511151231257827021181583404541015625
Math.ulp(1.0) = 2.220446049250313E-16   Math.ulp(1e16) = 2.0
1e16 에 1.0 을 1000번 더함 → 10000000000000000.0  (기대 10000000000001000.0)
float 0 에 1.0f 를 2천만 번 더함 → 16777216.0  (2^24 = 16777216)
```

- 관찰 1: `1e16`의 간격이 2라 `+1`은 매번 반올림으로 사라졌다. 1000번 더해도 그대로다.
- 관찰 2: `float`(가수 24비트)는 2²⁴ = 16,777,216에서 간격이 2가 된다. 그 뒤로 `+1.0f`는 아무 효과가 없다. 카운터가 1,677만에서 멈춘다.
- 관찰 3: `0.1`은 이진수로 정확히 표현되지 않는다. 저장된 값은 0.1보다 약 5.55×10⁻¹⁸ 크다(`new BigDecimal(0.1)`은 double 값을 그대로 10진으로 보여 준다).

### 2. 합산 오차는 항 수에 비례해 자란다

```text
  단순 합   s₁ = x₁
            s₂ = fl(s₁ + x₂)        ← 오차 δ₂
            s₃ = fl(s₂ + x₃)        ← 오차 δ₃  (이미 δ₂를 품은 s₂ 위에)
            ...
  먼저 더한 항일수록 이후의 모든 반올림을 겪는다

  Goldberg 1991 정리 8 (Kahan 합):  Σ xⱼ(1 + δⱼ) + O(N·ε²)·Σ|xⱼ|,  |δⱼ| ≤ 2ε   ← n과 무관
  같은 곳의 비교 문장 (단순 합):    Σ xⱼ(1 + δⱼ),  |δⱼ| < (n − j)·ε       ← 앞쪽 항은 최대 n·ε 만큼 흔들림
```

- 정리 8 자체는 Kahan 합의 식이다. 단순 합의 식은 Goldberg가 정리 바로 뒤에 비교로 든 것이다.
- 상자의 ε는 Goldberg의 기호로, 1절의 u(반올림 한 번의 상대 오차 상한, binary64에서 2⁻⁵³)와 같은 뜻이다.
- 단순 합의 오차 한계는 대략 `n · u · Σ|xⱼ|`에 비례한다. 1천만 개를 더하면 한 번 오차의 최대 1천만 배까지 갈 수 있다.
  - 이것은 **최악 한계**다. 반올림 오차가 위아래로 섞이면 실제 오차는 대개 훨씬 작다. 아래 실험의 단순 합 오차(약 2×10⁻⁴)도 한계보다 작다.
- 누적값 `s`가 커질수록 그 간격(ulp)도 커진다. 뒤에 오는 작은 항은 그 간격 단위로 반올림된다. 1절의 1e16 + 1이 극단적인 예다.
- 그래서 **누적 변수의 크기 vs 더하는 항의 크기** 비가 클수록 손실이 크다.

### 3. 순서가 결과를 바꾼다 — 결합법칙이 없다

```text
  수학:   (a + b) + c = a + (b + c)
  부동소수: (1e16 + 1) + 1 = 1e16          1e16 + (1 + 1) = 1e16 + 2

  병렬 합:  [x₁..x₄]  [x₅..x₈]  [x₉..x₁₂]  [x₁₃..x₁₆]     ← 조각 수 = 병렬도에 따라 달라짐
               s_a       s_b       s_c        s_d
                  \     /             \     /
                   s_ab                s_cd
                        \            /
                           합계        ← 나무 모양이 바뀌면 반올림 지점이 바뀐다
```

- 부동소수 덧셈은 교환법칙은 성립하지만 결합법칙은 성립하지 않는다.
- JLS §15.7.3: 자바 구현은 결합법칙 같은 대수 항등식으로 식을 바꿔 쓰면 안 된다(가능한 모든 값에서 값과 부수 효과가 같다고 증명되는 경우만 예외). "수학적으로 결합적으로 보이는 부동소수 계산은 계산상 결합적이지 않을 가능성이 크다." 그래서 `javac`·JIT은 덧셈 순서를 바꾸지 않는다.
- 반면 C 컴파일러의 `-ffast-math` 같은 옵션은 재결합을 허용한다(아래 실험 — Kahan 보정이 사라진다).
- `DoubleStream.sum()` Javadoc: 합의 값은 입력과 **덧셈 순서**의 함수다. 이 메서드는 순서를 일부러 정하지 않았고, 보상 합(compensated summation)으로 구현될 수 있다. 그래서 "같은 입력에도 출력이 달라질 수 있다." API 노트: 절댓값이 작은 것부터 정렬하면 대체로 더 정확하다.

### 4. Kahan 보상 합 — 잃어버린 비트를 들고 다닌다

```text
  s = 누적합, c = 직전 덧셈에서 잃어버린 부분(보정값)

  y = x − c          ← 지난번에 잃은 만큼 미리 보정
  t = s + y          ← 큰 수 + 작은 수: y의 하위 비트가 잘림
  c = (t − s) − y    ← (t − s) = 실제로 더해진 양,  거기서 y를 빼면 = −(잘린 부분)
  s = t

  예) s = 1e16, y = 1:   t = 1e16,  t − s = 0,  c = 0 − 1 = −1   → 다음 항에 1을 더해 준다
```

- *보상 합(Kahan 1965)*: 덧셈마다 잘려 나간 부분을 별도 변수 `c`에 모아 다음 항에 되돌려 준다.
- Goldberg 정리 8: 각 항이 겪는 상대 섭동이 `2ε` 이하로 n과 무관하다(위 2절 상자). 다만 고차 항 `O(N·ε²)·Σ|xⱼ|`은 n에 비례한다 — ε²라 n이 아주 크지 않으면 무시할 만하다. 대가는 덧셈 4번(단순 합의 약 4배 연산)이다.
- 대수적으로 `c = ((s + y) − s) − y = 0`이다. 그래서 재결합을 허용하는 최적화는 `c`를 0으로 지워 알고리즘을 무력화한다(Goldberg가 같은 경고를 적는다).
- *쌍별 합(pairwise summation)*: 반씩 나눠 더한 뒤 합친다. 각 항이 겪는 덧셈 횟수가 n이 아니라 약 log₂ n이다. 병렬 리덕션의 나무 모양과 같다.
- *`math.fsum`(Python)*: 부분합 여러 개를 추적해 정밀도 손실을 피한다(문서). 반올림이 기본 모드(half-even)일 때를 전제한다.
  - Python 3.12부터 내장 `sum()`도 부동소수 합에 더 정확하고 교환에 덜 민감한 알고리즘을 쓴다(Python 문서 "Changed in version 3.12").

#### 실험: 1천만 건 금액 합 — 합산법·순서·병렬도

- 0.01~999.99원(소수 둘째 자리, `new Random(15)`) 1천만 건. 원장은 정수 센트 합, 기준값은 `BigDecimal`로 double 값들을 정확히 더한 것.
- 코드 핵심(`Numeric.java`):

```java
static double kahan(double[] x) {
    double s = 0, c = 0;
    for (double v : x) { double y = v - c; double t = s + y; c = (t - s) - y; s = t; }
    return s;
}
static double pairwise(double[] x, int lo, int hi) {
    if (hi - lo <= 8) { double s = 0; for (int i = lo; i < hi; i++) s += x[i]; return s; }
    int mid = (lo + hi) >>> 1; return pairwise(x, lo, mid) + pairwise(x, mid, hi);
}
```

(실험, OpenJDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-07)

```text
원장(정수 센트 합)        = 4999835704.52
double 값들의 정확한 합   = 4999835704.519999999974023
단순 for 합               = 4999835704.520197   정확한 합과 차이 +1.969e-04   원장과 차이 +1.969e-04
Kahan 보정 합             = 4999835704.520000   정확한 합과 차이 +4.578e-07   원장과 차이 +4.578e-07
pairwise 합             = 4999835704.520000   정확한 합과 차이 -4.959e-07   원장과 차이 -4.959e-07
DoubleStream.sum()     = 4999835704.520000   정확한 합과 차이 +4.578e-07   원장과 차이 +4.578e-07
stream reduce(0,+)     = 4999835704.520197   정확한 합과 차이 +1.969e-04   원장과 차이 +1.969e-04
  셔플 1: 단순 합 4999835704.519449   Kahan 4999835704.520000
  셔플 2: 단순 합 4999835704.519596   Kahan 4999835704.520000
  셔플 3: 단순 합 4999835704.520143   Kahan 4999835704.520000
  셔플 4: 단순 합 4999835704.519652   Kahan 4999835704.520000
  셔플 5: 단순 합 4999835704.519505   Kahan 4999835704.520000
  오름차순 정렬 후 단순 합 4999835704.519869   내림차순 4999835704.519163
```

- 관찰 1: 단순 합은 정확한 합에서 약 2×10⁻⁴ 벗어났다. Kahan·쌍별 합은 약 5×10⁻⁷로 약 400배 정확하다. 남은 5×10⁻⁷은 결과 5×10⁹ 근처의 ulp(약 9.5×10⁻⁷)보다 작다 — 마지막 반올림 한 번 수준이다.
- 관찰 2: `DoubleStream.sum()`은 Kahan과 같은 값을 냈다. `reduce(0, Double::sum)`은 단순 합과 같다. 이 JDK의 `sum()`은 보상 합으로 동작했다(Javadoc은 "그럴 수 있다"고만 적는다 — 구현 세부는 보장이 아니다).
- 관찰 3: 같은 1천만 개를 셔플만 바꿔 더하면 단순 합은 0.519449~0.520143으로 매번 다르다. Kahan은 5회 모두 같다.
- 관찰 4: 오름차순(작은 것부터) 단순 합 오차 1.3×10⁻⁴, 내림차순 8.4×10⁻⁴. 작은 것부터 더하는 쪽이 낫다는 API 노트와 맞다. 그래도 Kahan보다 훨씬 나쁘다.
- 이 실험에서는 단순 합도 센트 단위로 반올림하면 원장과 같다(오차 2×10⁻⁴ < 0.005). 그러나 반올림 전 값을 `BigDecimal.compareTo`로 원장과 비교하면 **불일치**다(`FloatAgg.java`: `false`). `float`로 누적하면 반올림해도 4,997,129,216.00으로 원장과 약 270만 원 차이가 났다.

```text
원장 4999835704.52
float 누적  4997129216.00
double 누적 4999835704.52  (반올림 전 4999835704.520197)
double 누적 == 원장(BigDecimal.compareTo) ? false
```

#### 실험: 병렬도만 바꾼 병렬 합

- 같은 1천만 개를 `DoubleStream.of(x).parallel()`로 더하고, ForkJoin 공용 풀 병렬도만 `-Djava.util.concurrent.ForkJoinPool.common.parallelism=p`로 바꿨다(`Par.java`).

(실험, OpenJDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-07)

```text
parallelism=1  parallel reduce 4999835704.520057  parallel sum() 4999835704.520000
parallelism=3  parallel reduce 4999835704.520033  parallel sum() 4999835704.520000
parallelism=7  parallel reduce 4999835704.520006  parallel sum() 4999835704.520000
parallelism=15  parallel reduce 4999835704.519991  parallel sum() 4999835704.520000
```

- 관찰 1: `reduce(0, Double::sum)`은 병렬도마다 마지막 자리가 다르다. 작업을 나누는 나무 모양이 바뀌어 반올림 지점이 바뀐 것이다.
- 관찰 2: 같은 병렬도에서 5번 돌린 `reduce`는 5번 모두 같은 값(0.520057)이었다(`Numeric.java` 3절). 이 실험에서 결과를 바꾼 것은 실행 회차가 아니라 분할 방식(병렬도)이다.
- 관찰 3: 병렬 `sum()`은 네 설정 모두 0.520000이었다. 보상 합이 순서 차이를 마지막 비트 아래로 눌렀다(이 데이터·이 JDK에서의 관찰 — Javadoc은 같은 값을 보장하지 않는다).

#### 실험: 최적화가 Kahan을 지운다 (C)

- 1e8 하나 + 0.1 천만 개를 C로 더했다(`kahan.c`). 같은 소스를 `-O2`와 `-O2 -ffast-math`로 컴파일했다.

```c
double k = 0, c = 0;
for (int i = 0; i < n; i++) { double y = x[i] - c; double t = k + y; c = (t - k) - y; k = t; }
```

(실험, gcc 13.3.0 호스트, 2026-10-07)

```text
-O2              naive 100999999.940395  kahan 101000000.000000
-O2 -ffast-math  naive 100999999.940395  kahan 100999999.940395
```

- 관찰: `-ffast-math`에서 Kahan 결과가 단순 합과 똑같아졌다. 사실 점검에서 `gcc -S`로 어셈블리를 보니 `-ffast-math` 판의 Kahan 루프에는 `subsd`가 하나도 없고 단순 합 루프와 같은 `addsd`만 남았다(`-O2` 판은 `subsd` 3개). 컴파일러가 `c = (t − k) − y`를 0으로 정리해 보정을 지운 것이다. Java는 JLS §15.7.3 때문에 이런 재작성을 하지 않는다.

### 5. 파국적 상쇄 — 뺄셈이 오차를 키운다

```text
  a = 1.000000000123 (오차 ±1e−16 정도)
  b = 1.000000000000 (오차 ±1e−16 정도)
  a − b = 0.000000000123   ← 앞 자리 10개가 상쇄. 남은 유효 자리 중 상당수가 원래 오차에서 온 쓰레기

  상대 오차 확대율 ≈ |a| / |a − b|  (약 10¹⁰배)
```

- *파국적 상쇄(catastrophic cancellation)*: 거의 같은 두 수를 뺄 때, 두 수에 이미 있던 반올림 오차가 결과의 주된 부분이 되는 현상(Goldberg 1991 "Cancellation").
  - *양성 상쇄(benign cancellation)*: 정확히 알려진 두 수를 빼는 것. 결과 오차가 작다(같은 절).
- 해법은 **빼기 전에 식을 바꾸는 것**이다.
  - `1 − cos x` → `2 sin²(x/2)` (x가 작을 때)
  - 이차방정식 근 `(−b ± √(b² − 4ac)) / 2a` → 상쇄되는 쪽 근은 `2c / (−b ∓ √(b² − 4ac))`로(Goldberg 식 (5))
  - 분산 `E[X²] − E[X]²` → 웰퍼드(Welford) 갱신(평균과의 차이를 누적)

#### 실험: 상쇄 두 가지

(실험, OpenJDK 21.0.12 temurin, 2026-10-07 — 결정적, 3회 실행 같은 출력)

```text
== 4. 파국적 상쇄: (1 - cos x) / x^2 (참값 → 0.5)
  x=1e-04  직접 0.4999999970   2sin²(x/2)/x² 0.4999999996
  x=1e-06  직접 0.5000444503   2sin²(x/2)/x² 0.5000000000
  x=1e-08  직접 0.0000000000   2sin²(x/2)/x² 0.5000000000
== 5. 분산 공식: E[X²]−E[X]² vs 웰퍼드 (값 = 1e9 + {4,7,13,16})
  E[X²]−E[X]² = -128.0000   웰퍼드 = 22.5000   (참값 22.5)
```

- 관찰 1: x = 10⁻⁸이면 `cos x`가 1로 반올림되어 `1 − cos x = 0`이다. 답이 0.5인데 0이 나왔다. 바꾼 식은 0.5다.
- 관찰 2: 값이 10⁹ 근처면 `E[X²]`는 10¹⁸ 근처라 간격이 128이다. 분산 22.5는 그 간격보다 작아 사라지고 **음수 −128**이 나왔다. 여기에 `Math.sqrt`를 하면 `NaN`이다. 웰퍼드는 정확히 22.5다.

## 쓰이는 자료구조·알고리즘

- **Kahan 보상 합** — 누적합 + 보정값 두 변수. `DoubleStream.sum()`이 이 계열로 구현될 수 있다(Javadoc).
- **쌍별 합 = 분할 정복** — 반씩 나눠 더하기. 병렬 리덕션 나무와 같은 모양. [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md).
- **크기순 정렬 후 합** — 작은 것부터 더하면 대개 더 정확하다(Javadoc API 노트). 정렬 비용 O(n log n). [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md).
- **웰퍼드 온라인 평균·분산** — 한 번 훑으며 평균과 제곱 편차합을 갱신. 스트림 지표 집계.
- **정확한(또는 고정밀) 누적 — 정수 최소 단위·`BigDecimal`·`math.fsum`(고정밀, 결과는 float)** — 돈은 [domain-modeling/14](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md).
- **내적·행렬곱** — 덧셈 순서가 바뀌면 결과 비트가 달라진다. [13-linear-algebra-essentials](../13-linear-algebra-essentials/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 어림 → 확인

1. **증상**: 집계 합계가 원장과 소수 자리에서 다르다. 같은 데이터인데 실행 환경마다 마지막 자리가 다르다. 분산·표준편차가 음수·`NaN`이다.
2. **어림**
   - 누적합의 크기 S와 항 수 n을 본다. 단순 합 최악 오차 ≈ `n · u · Σ|x|`(u ≈ 1.1×10⁻¹⁶). 실제는 대개 이보다 작다.
   - `double` 누적값이 2⁵³(약 9×10¹⁵)을 넘거나 `float` 누적값이 2²⁴(약 1,677만)을 넘으면 정수 1 단위가 사라진다.
   - 거의 같은 두 수를 빼는 식(`1 − cos x`, `E[X²] − E[X]²`, `a − b` 비교)이 있는지 본다.
3. **확인**: 같은 데이터를 `BigDecimal`(저장된 double 값을 `new BigDecimal(double)`로 옮기면 정확한 합)이나 Python `math.fsum`(정확도가 높은 부동소수 합 — 결과도 float라 마지막 반올림이 있다)으로 더해 차이를 잰다. 순서를 셔플해 결과가 흔들리는지 본다.

### 2. 고르는 법

```text
  돈·건수처럼 정확해야 하는가?   예 → long 최소 단위 / BigDecimal (double 금지)
  통계 지표(평균·합)인가?        → DoubleStream.sum() 또는 Kahan, 분산은 웰퍼드
  재현성(같은 입력 = 같은 비트)이 계약인가?
                                 → 순서를 고정한 순차 합, 또는 정확한 누적(정수·BigDecimal)
  비교인가?                      → == 대신 허용 오차: |a − b| ≤ tol × max(|a|, |b|)
```

### 3. 코드

```java
/** 보상 합 — 직접 쓰는 경우. 재결합 최적화가 없는 Java에서는 그대로 동작한다. */
static double kahanSum(double[] xs) {
    double s = 0, c = 0;
    for (double x : xs) { double y = x - c; double t = s + y; c = (t - s) - y; s = t; }
    return s;
}

/** 웰퍼드: 한 번 훑어 평균·모분산. 값이 크고 분산이 작아도 음수가 나오지 않는다. */
static double[] meanVar(double[] xs) {
    double mean = 0, m2 = 0; int n = 0;
    for (double x : xs) { n++; double d = x - mean; mean += d / n; m2 += d * (x - mean); }
    return new double[]{mean, n > 0 ? m2 / n : Double.NaN};
}

/** 상대 허용 오차 비교. tol은 계산 경로의 오차 어림으로 정한다(예: 1e-12 — 예시). */
static boolean nearlyEqual(double a, double b, double tol) {
    return Math.abs(a - b) <= tol * Math.max(Math.abs(a), Math.abs(b));
}

/** 돈은 최소 단위 정수로 누적한다. 넘침은 예외로 드러낸다. */
static long sumCents(long[] cents) {
    long s = 0;
    for (long c : cents) s = Math.addExact(s, c);
    return s;
}
```

## 장애 시나리오와 대처

### 1. 집계 합계가 원장과 불일치 (⚠)

- 현상: 일 정산 리포트의 합계가 원장 합계와 다르다.
- 보이는 형태: 대사 작업이 "차이 0.01" 또는 수백만 원 차이를 보고. `double` 합을 `BigDecimal` 원장과 `compareTo`하면 0이 아니다(실험: 차이 1.969×10⁻⁴). `float` 누적이면 실험에서 약 270만 원 차이.
- 원인: 큰 누적값에 작은 항을 반복해 더하며 하위 비트가 잘렸다. 금액을 이진 부동소수로 다뤘다.
- 대처: 금액은 `long` 최소 단위 또는 `BigDecimal`로 누적한다(domain-modeling/14). 부동소수가 불가피한 통계 집계는 보상 합을 쓰고, 원장과 비교할 때는 통화 자릿수로 반올림한 뒤 비교한다.

### 2. 병렬 합산 순서마다 다른 결과 (⚠)

- 현상: 같은 데이터로 돌린 집계가 노드 수·병렬도·파티션 수를 바꾸자 마지막 자리가 바뀌었다.
- 보이는 형태: 스냅샷·골든 테스트 실패(`expected 4999835704.520057 but was 4999835704.520033`), 재처리 뒤 체크섬 불일치.
- 원인: 부동소수 덧셈은 결합법칙이 없다. 병렬 리덕션은 분할 방식에 따라 덧셈 나무가 달라진다(실험: 병렬도 1·3·7·15에서 네 가지 값).
- 대처: 재현성이 계약이면 정확한 누적(정수·`BigDecimal`)이나 순서 고정을 쓴다. 통계 지표면 보상 합(`DoubleStream.sum()`)으로 차이를 줄이고, 테스트는 허용 오차로 비교한다.

### 3. 분산·표준편차가 음수·NaN

- 현상: 지연 시간 표준편차 대시보드가 비거나 `NaN`이다. 이상 탐지 알람이 안 울린다.
- 보이는 형태: `NaN` 값, 또는 `Math.sqrt` 이전 분산이 음수(실험: −128). `NaN`과의 대소·`==` 비교는 거짓이라 문턱 알람이 조용히 꺼진다.
- 원인: `E[X²] − E[X]²` 공식의 파국적 상쇄. 값이 크고(예: 에포크 나노초 타임스탬프) 분산이 작을 때 일어난다.
- 대처: 웰퍼드 갱신을 쓰거나, 값에서 대표값(첫 값·기준 시각)을 빼고 계산한다. 결과가 음수·`NaN`이면 에러로 드러낸다(조용히 0으로 바꾸지 않는다).

### 4. 최적화 옵션이 보상 합을 지움

- 현상: 네이티브 라이브러리·C 확장의 합계가 기대만큼 정확하지 않다. 디버그 빌드와 릴리스 빌드 결과가 다르다.
- 보이는 형태: 같은 입력에서 빌드 옵션에 따라 다른 합계(실험: `-ffast-math`에서 Kahan = 단순 합).
- 원인: `-ffast-math` 류 옵션이 부동소수 재결합을 허용해 `c = (t − s) − y`를 0으로 정리했다.
- 대처: 수치 코드는 재결합 허용 옵션을 끈다. 보상 합 회귀 테스트(위 실험 같은 고정 입력)를 둔다. Java는 JLS §15.7.3으로 재결합을 금지한다.

### 5. float 카운터가 1,677만에서 멈춤

- 현상: 누적 카운터·지표가 어느 값 이후 더 이상 늘지 않는다.
- 보이는 형태: 그래프가 16,777,216 근처에서 평평해진다.
- 원인: `float` 가수는 24비트라 2²⁴ 이상에서 간격이 2다. `+1`이 반올림으로 사라진다(실험).
- 대처: 카운터는 정수(`long`)로 둔다. 부동소수가 필요하면 `double`로 하되 2⁵³ 한계를 기억한다.

## 핵심 문장

- 부동소수 연산 한 번의 상대 오차는 u(binary64 ≈ 1.1×10⁻¹⁶) 이하지만, 같은 누적 변수에 쌓이면 최악 n배까지 자란다.
- 큰 수 옆의 작은 수는 그 수의 간격(ulp)의 절반보다 작으면 사라진다(정확히 절반이면 짝수 쪽으로 반올림). `1e16 + 1 = 1e16`, `float`에서 `2²⁴ + 1 = 2²⁴`, 하지만 `1e16 + 1.5 = 1e16 + 2`.
- 부동소수 덧셈은 결합법칙이 없다. 순서·병렬 분할이 바뀌면 결과 비트가 바뀐다.
- Kahan 합은 잘린 부분을 보정값으로 들고 다녀 오차의 주된(1차) 항을 n과 무관하게 만든다(남는 고차 항은 `n·ε²` 수준). 재결합 최적화는 이를 지운다.
- 거의 같은 두 수의 뺄셈은 원래 오차를 확대한다. 빼기 전에 식을 바꾼다(`2 sin²(x/2)`, 웰퍼드).
- 돈과 재현성이 계약인 곳은 부동소수 합이 아니라 정수·`BigDecimal`로 누적한다.

## 관련 주제·근거

- 선행
  - [architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md). 원고 [foundations/data-representation](../../foundations/data-representation/README.md) §2(부동소수점·엡실론·0.1+0.2)
- 같은 영역·연결
  - [13-linear-algebra-essentials](../13-linear-algebra-essentials/2-summary.md) — 내적·행렬곱의 덧셈 순서
  - [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md) — 분산의 정의
  - [domain-modeling/14-money-arithmetic-rounding-allocation](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md) — 금액 반올림·배분, `BigDecimal`
  - [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md) · [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md)
  - [testing/09-flaky-tests](../../testing/09-flaky-tests/2-summary.md) — 환경에 따라 흔들리는 테스트
- 근거
  - D. Goldberg, "What Every Computer Scientist Should Know About Floating-Point Arithmetic", ACM Computing Surveys, 1991년 3월 — "Cancellation"(파국적·양성 상쇄, 이차방정식 70 ulp 예, 식 (5)), 정리 8(Kahan 합산 공식 `|δⱼ| ≤ 2ε`)과 그 바로 뒤의 단순 합 비교 `|δⱼ| < (n − j)ε`, 재결합 최적화 경고 <https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html>
  - W. Kahan, "Further remarks on reducing truncation errors", Communications of the ACM 8(1), p. 40, 1965 — 보상 합
  - N. J. Higham, 『Accuracy and Stability of Numerical Algorithms』 2판, SIAM 2002 — 부동소수 연산의 표준 모델, 합산(장 번호 `[?]` — 목차를 열지 못했다)
  - JLS SE 21 §15.7.3 "Evaluation Respects Parentheses and Precedence" <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html>
  - Java SE 21 `DoubleStream.sum()` Javadoc(순서 미정, 보상 합 가능, 출력이 달라질 수 있음, 크기순 정렬 API 노트), `reduce`는 결합법칙을 만족하는 연산을 요구 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/DoubleStream.html>
  - Python 3 문서 `math.fsum`(부분합 추적, half-even 전제) <https://docs.python.org/3/library/math.html>, 내장 `sum()`(3.12 변경) <https://docs.python.org/3/library/functions.html>
- 실험 목록
  - `Numeric.java` — 0.1+0.2·ulp, 1e16+1 반복, float 2²⁴, 1천만 건 금액의 단순·Kahan·쌍별·`DoubleStream.sum()`·`reduce` 비교, 셔플 5회·정렬 순서, 병렬 reduce 5회, `(1 − cos x)/x²`, 분산 공식 vs 웰퍼드. OpenJDK 21.0.12 temurin, Docker `--cpus=2 --network none`, `-Xmx1g`, 2026-10-07, 3회 실행(출력 동일).
  - `FloatAgg.java` — 같은 데이터의 float·double 누적 vs 원장. 같은 환경.
  - `Par.java` — ForkJoin 공용 풀 병렬도 1·3·7·15에서 병렬 `reduce`·`sum()`. 같은 환경.
  - `kahan.c` — gcc 13.3.0 `-O2` vs `-O2 -ffast-math`. 호스트. 사실 점검에서 재실행(같은 출력)하고 `gcc -S` 어셈블리로 보정 뺄셈이 사라진 것을 확인했다.
  - 사실 점검 재실행(2026-10-07): `Numeric.java`(집필 출력과 diff 없음), `FloatAgg.java`·`Par.java`(병렬도 1·3·7·15 같은 값), `fsum.py`(3.12.3·3.12.14 같은 값).
  - `fsum.py` — Python 3.12.3(호스트)·3.12.14(`python:3.12-slim`)에서 for 루프·`sum()`·`math.fsum` 비교: 100만 건 기준 for 루프만 2.4×10⁻⁵ 벗어나고 `sum()`·`fsum()`은 정수 센트 합과 같았다. `sum([0.1]*10) = 1.0`.
