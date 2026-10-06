# math/07-probability-and-bayes — 확률 공리·조건부 확률·독립·베이즈 정리 — 정리 (힌트)

## 해결하는 문제

"99% 정확한 이상탐지"를 붙였다. 하루 알람이 1만 건을 넘는다. 열어 보면 대부분 정상이다.

```text
  하루 이벤트 1,000,000건 (예시)   진짜 이상 0.1% = 1,000건
                 │
       ┌─────────┴──────────┐
     이상 1,000            정상 999,000
       │ 99% 울림              │ 1% 잘못 울림
     알람 990              알람 9,990
       └─────────┬──────────┘
           알람 합계 10,980건 → 그중 진짜는 990건 = 9.0%
```

- 탐지기는 "이상이면 99% 울린다". 운영자가 묻는 것은 반대 방향이다. "울렸으면 진짜 이상일 확률은?"
- 두 확률은 다르다. 둘을 잇는 식이 베이즈 정리다. 그 사이에 **기저율**(원래 이상이 얼마나 드문가)이 들어간다.
  - *기저율(base rate)*: 아무 정보가 없을 때 사건의 확률. 여기서는 P(이상) = 0.1%.
    - 흔한 오해: "정확도 99%면 알람의 99%가 진짜다." 기저율이 낮으면 정상 쪽의 1%가 이상 쪽의 99%보다 건수가 많다.

쉬운 예: 유병률 0.1%인 병의 검사다. 민감도·특이도가 99%여도 양성 판정 중 진짜 환자는 약 9%다.

똑같은 구조다.\
"드문 것을 찾는 검사"는 전부 이 계산을 거친다.

실무 예:
- 이상탐지·보안 알람(IDS)의 오탐. Axelsson(2000)은 합리적인 가정 아래에서 침입 탐지 성능을 제한하는 요인이 탐지율이 아니라 **오경보율**임을 보였다(초록: "the false alarm rate is the limiting factor").
- 블룸 필터의 "아마 있다". 위양성 확률을 계산해 크기를 정한다.
- 스팸 필터(나이브 베이즈). 단어별 확률을 합쳐 "스팸일 확률"을 낸다.

## 동작·원리

### 1. 확률 공간과 공리

```text
  표본 공간 S (일어날 수 있는 모든 결과)
  ┌───────────────────────────────┐
  │   ┌───────┐                   │
  │   │   A   │──┐                │   P(S) = 1
  │   └───┬───┘  │ A∩B            │   P(A) ≥ 0
  │       └──┬───┘                │   A, B가 겹치지 않으면 P(A∪B) = P(A) + P(B)
  │          │   B                │
  └───────────────────────────────┘
```

- *표본 공간(sample space)*: 실험의 가능한 결과 전체의 집합. 예: 요청 하나 = {성공, 4xx, 5xx, 타임아웃}.
- *사건(event)*: 표본 공간의 부분집합. 예: "실패" = {5xx, 타임아웃}.
- 기본 규칙 세 개(MCS 17.5 "Set Theory and Probability" — 정의 17.5.2는 결과마다 확률 ≥ 0·합 1로 정의하고, 규칙 17.5.3 Sum Rule이 배반 사건의 합을 준다):
  - P(S) = 1.
  - 모든 사건 E에 P(E) ≥ 0.
  - 서로 겹치지 않는(배반) 사건들의 합집합 확률 = 각 확률의 합.
- 공리에서 바로 나오는 것
  - 여사건: `P(not A) = 1 − P(A)`.
  - 합집합: `P(A∪B) = P(A) + P(B) − P(A∩B)`.
  - 합집합 상한(union bound): `P(A∪B) ≤ P(A) + P(B)`. 겹침을 모를 때 쓰는 안전한 상한이다.
    - 예: 의존 서비스 3개가 각각 0.1% 확률로 실패한다. 하나라도 실패할 확률 ≤ 0.3%. 독립인지 몰라도 성립한다.

### 2. 조건부 확률 — 나무로 읽기

```text
  P(A|B) = P(A∩B) / P(B)        (P(B) > 0 일 때만 정의)

  확률 나무 (MCS 18.3 "Four-Step Method", 18.4 "Why Tree Diagrams Work")
                       ┌─ 울림   0.99   → P(이상∩울림) = 0.001 × 0.99   = 0.00099
          ┌─ 이상 0.001 ┤
          │            └─ 조용   0.01   → 0.001 × 0.01                   = 0.00001
  시작 ───┤
          │            ┌─ 울림   0.01   → P(정상∩울림) = 0.999 × 0.01   = 0.00999
          └─ 정상 0.999 ┤
                       └─ 조용   0.99   → 0.999 × 0.99                   = 0.98901
```

- *조건부 확률 P(A|B)*: B가 일어났다고 알 때 A의 확률. 표본 공간을 B로 줄이고 그 안에서 A의 비율을 본다.
- 나무의 한 경로 확률 = 가지 확률의 곱(곱셈 규칙 `P(A∩B) = P(B)·P(A|B)`).
- 잎 네 개의 합은 1이다. 위 그림에서 0.00099 + 0.00001 + 0.00999 + 0.98901 = 1.

### 3. 전확률 법칙과 베이즈 정리

```text
  P(울림) = P(울림|이상)·P(이상) + P(울림|정상)·P(정상)       ← 전확률 법칙 (MCS 18.5)
          = 0.99 × 0.001        + 0.01 × 0.999   = 0.01098

  P(이상|울림) = P(울림|이상)·P(이상) / P(울림)               ← 베이즈 정리 (MCS 정리 18.4.1)
             = 0.00099 / 0.01098 = 0.0902
```

- *전확률 법칙(law of total probability)*: 서로 겹치지 않고 전체를 덮는 경우들(이상/정상)로 나눠 더한다.
- *베이즈 정리*: `P(A|B) = P(B|A)·P(A) / P(B)`.
  - P(A): *사전 확률(prior)* — 증거를 보기 전의 믿음. 여기선 기저율 0.1%.
  - P(B|A): *가능도(likelihood)* — A가 참일 때 증거가 나올 확률. 여기선 민감도 99%.
  - P(A|B): *사후 확률(posterior)* — 증거를 본 뒤의 믿음. 여기선 9.0%.
- 검사 용어
  - *민감도(sensitivity, 재현율)*: P(울림|이상). 이상을 놓치지 않는 비율.
  - *특이도(specificity)*: P(조용|정상). 1 − 특이도 = 오경보율 P(울림|정상).
  - *PPV(양성 예측도, 정밀도)*: P(이상|울림). 운영자가 체감하는 "알람의 질".

### 실험: 기저율 — 같은 탐지기, 다른 기저율

이벤트 1,000만 건을 만들고, 각 이벤트를 기저율로 이상/정상으로 정한 뒤 탐지기를 통과시켰다.

```java
// scratchpad/math/07/e07/Bayes.java 핵심
boolean bad = r.nextDouble() < prev;
boolean alarm = bad ? r.nextDouble() < sens : r.nextDouble() >= spec;
if (alarm) { pos++; if (bad) tp++; }
double theory = sens * prev / (sens * prev + (1 - spec) * (1 - prev));   // 베이즈
```

(실험, OpenJDK 21.0.12 Temurin 컨테이너 `--cpus=2 --network none`, 시뮬레이션 `SplittableRandom` seed 42, 2026-10-07)

```text
(A) seed=42, N=10,000,000, 민감도 99%, 특이도 99%
유병률   양성(알람)   진짜양성   PPV(시뮬)   PPV(베이즈)
  0.1%      110142       9788      8.89%      9.02%
  1.0%      197896      99205     50.13%     50.00%
 10.0%     1079778     989755     91.66%     91.67%
```

- 관찰 1: 탐지기는 그대로인데 기저율이 0.1% → 10%로 바뀌자 PPV가 9% → 92%가 됐다. PPV(알람이 진짜일 확률)는 탐지기만의 성질이 아니다. 반면 전체 정확도는 민감도 = 특이도 = 99%라 기저율과 무관하게 99%다.
- 관찰 2: 기저율 1%에서 민감도 = 특이도 = 99%이면 PPV가 정확히 50%다. 진짜 알람(0.99 × 1%)과 오경보(0.01 × 99%)의 건수가 같기 때문이다.
- 시드 1·2·3으로 다시 돌린 0.1% 줄의 PPV는 8.88%·9.07%·8.86%였다. 진짜 양성이 1만 건 안팎이라 표본 오차가 ±0.1%p 수준이다. 이론값 9.02%는 그 범위 안이다.

### 4. 독립 — 곱해도 되는 조건

```text
  독립:   P(A∩B) = P(A)·P(B)       ⇔ P(A|B) = P(A)  (P(B) > 0)
  배반:   P(A∩B) = 0               (둘이 함께 일어날 수 없다)

  서로 독립인 공정한 두 동전 X, Y와 C = "X와 Y가 같다"
         X    Y    C
         앞   앞   참     P(X=앞)=1/2, P(C)=1/2, P(X=앞 ∩ C)=1/4 → 독립
         앞   뒤   거짓   Y와 C도 독립 (같은 계산)
         뒤   앞   거짓   그러나 X·Y를 알면 C가 정해진다
         뒤   뒤   참     P(X=앞 ∩ Y=앞 ∩ C) = 1/4 ≠ 1/8 → 셋은 상호 독립이 아님
```

- *독립(independence)*: 한 사건이 일어났다는 정보가 다른 사건의 확률을 바꾸지 않는다(MCS 18.7).
  - 흔한 오해: "배반이면 독립이다." 반대다. 확률이 양수인 두 배반 사건은 하나가 일어나면 다른 하나의 확률이 0이 되므로 **독립이 아니다**.
- *쌍별 독립 vs 상호 독립(mutual independence)*: 둘씩은 독립이어도 셋을 함께 보면 아닐 수 있다. 위 표가 그 예다. MCS 18.8.2는 동전 세 개의 "두 동전이 같다" 사건 셋으로 같은 현상을 보인다.
- 곱셈 `P(A)·P(B)`는 독립일 때만 맞다. 같은 AZ·같은 배포를 공유하는 두 서버의 동시 장애에 곱셈을 쓰면 크게 틀린다(08의 실험 D, [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md)).
- *조건부 독립*: C를 알 때 A와 B가 독립. `P(A∩B|C) = P(A|C)·P(B|C)`. 나이브 베이즈가 기대는 가정이다(6절).

### 5. 블룸 필터 위양성 — 베이즈가 아니라 "빈 칸 확률"의 곱

```text
  비트 m개, 해시 k개, 원소 n개를 넣은 뒤
  한 비트가 아직 0일 확률     = (1 − 1/m)^(k·n) ≈ e^(−k·n/m)
  넣지 않은 원소의 k칸이 전부 1일 확률 (위양성)
                           ≈ (1 − e^(−k·n/m))^k

  가정: k개 해시가 서로 독립이고 m칸에 균등 — 그 위에서 칸마다 "1일 확률"을 k번 곱한다
  주의: 해시가 독립이어도 "조회한 k칸이 1" 사건들은 같은 필터 상태를 공유해 독립이 아니다 → 이 곱은 근사
```

- 구조와 동작은 [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)에 있다. 여기서는 식이 어디서 나오는지만 본다.
- 크기 정하기(같은 가정에서 근사식)
  - 목표 위양성 p, 원소 n개 → `m = −n·ln p / (ln 2)²`, `k = (m/n)·ln 2`.
  - n = 100,000, p = 1% → m ≈ 958,506비트(약 117KiB), k = 6.64 → 7.
  - 최적 k에서는 비트의 약 절반이 1이다(`e^(−kn/m) = 1/2`).
- 근사의 한계: Bose 외(IPL 2008)는 고전식 `(1 − (1 − 1/m)^(kn))^k`가 k ≥ 2에서 실제 위양성의 **엄격한 하한**임을 보였다(k ≥ 2이면 실제 값이 이 식보다 크다). m이 크고 k가 작으면 그 차이는 무시할 만하다(저자 사본의 결론 절). Bose 외의 결과는 독립·균등 무작위 해시 모형에 대한 것이다. 아래 실험은 이중 해싱(`h1 + i·h2`)을 썼고, 설계 용량의 2배까지 세 줄이 0.02%p 안, 3배 줄이 0.12%p 차이였다.

### 실험: 블룸 필터 위양성 — 공식 vs 실측, 용량 초과

```java
// scratchpad/math/07/e07/Bayes.java 핵심 — 64비트 섞기 후 이중 해싱 h1 + i·h2
long h = mix(key); int h1 = (int) h, h2 = (int) (h >>> 32);
for (int i = 0; i < k; i++) { int idx = Math.floorMod(h1 + i * h2, m); bits[idx >>> 6] |= 1L << idx; }
double formula = Math.pow(1 - Math.exp(-(double) k * inserted / m), k);
```

(실험, 같은 환경, 넣지 않은 키 100만 개로 위양성 측정, 2026-10-07)

```text
(B) Bloom m=958,506 bits, k=7, 설계 n=100,000 (목표 FP 1%)
삽입 수    켜진 비트 비율   FP 공식      FP 실측(비회원 100만 개)
  50,000      30.57%         0.0251%      0.0248%
 100,000      51.78%         1.0039%      0.9878%
 200,000      76.80%        15.7453%     15.7293%
 300,000      88.83%        43.6038%     43.7225%
```

- 관찰 1: 설계 용량(10만)에서 켜진 비트가 51.78%다. "최적 k면 절반이 켜진다"와 맞는다.
- 관찰 2: 용량의 2배를 넣으면 위양성이 1% → 15.7%, 3배면 43.6%가 된다. 선형이 아니라 k제곱으로 커진다.
- 관찰 3: 공식과 실측이 앞 세 줄은 0.02%p 안, 30만 줄은 0.12%p(실측이 더 큼) 차이다. 섞기 함수가 균등 가정을 잘 흉내 냈다는 뜻이다. 해시가 나쁘면 이 일치가 깨진다.
- 해석: 30만 줄의 차이는 비회원 100만 개의 표본 오차(약 ±0.05%p)보다 크다. 다만 이 실험은 이중 해싱이라 독립 해시 모형의 Bose 외(2008) 하한 정리로 차이를 설명할 수는 없다. 한 시드의 관찰로만 남긴다.

### 6. 나이브 베이즈 — 조건부 독립을 가정한 곱

```text
  단어 w1, w2, w3이 메일에 있다. 단어마다 "이 단어가 있을 때 스팸일 확률" p1, p2, p3
  사전 확률 P(스팸) = 1/2 로 두고, 단어들이 조건부 독립이라 가정하면

  P(스팸 | w1,w2,w3) = p1·p2·p3 / ( p1·p2·p3 + (1−p1)(1−p2)(1−p3) )

  예시) p = 0.99, 0.95, 0.20  →  0.18810 / (0.18810 + 0.00040) = 0.9979
```

- Graham "A Plan for Spam"(2002-08)은 메일마다 가장 두드러진 단어 15개의 확률을 이 식으로 합쳤다. 0.9를 넘으면 스팸으로 분류했다.
- 이 식은 단어들이 (스팸/정상 각각 안에서) 서로 독립이라는 가정에서 나온다. 실제 단어는 함께 나온다("free"와 "offer"). 그래서 확률값 자체는 과신 쪽으로 치우치기 쉽다. 분류 순서는 쓸 만해도, 출력값을 "보정된 확률"로 읽으면 안 된다(해석).
- 예시 계산: 0.20("스팸 아닌 쪽" 단어)이 있어도 0.99·0.95 두 단어가 결과를 0.998로 끌어올린다. 곱은 극단값에 끌린다.

## 쓰이는 자료구조·알고리즘

- 블룸 필터 크기·위양성 계산: [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md). 해시 독립·균등 가정은 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).
- 확률적 카운팅(HyperLogLog)의 오차 분석: [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md).
- 나이브 베이즈 분류기: 단어 빈도 해시맵 + 로그 확률 합(곱 대신 로그 합으로 언더플로를 피한다).
- 몬테카를로 알고리즘의 오류 확률 곱(독립 반복): [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md).
- 생일 문제·충돌 확률(세기에서 출발): [수학 05 counting-and-birthday-bound](../05-counting-and-birthday-bound/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 알람이 오탐투성이일 때 — 증상 → 식 → 코드

1. 증상: 알람 중 조치한 비율이 낮다. 지난 1주 알람마다 사후에 "진짜 이상이었나"를 판정해 실측 PPV를 낸다(조치 비율은 따로 본다 — 조치 안 한 진짜 이상, 조치한 오경보가 있을 수 있다).
2. 식으로 어림: `PPV = s·b / (s·b + (1−t)·(1−b))` (s 민감도, t 특이도, b 기저율).
   - b가 작으면 분모가 `(1−t)·(1−b)`에 지배된다. 민감도보다 **오경보율(1−t)을 낮추는 쪽**이 PPV를 올린다.
3. 코드로 확인:

```java
// 알람 판정 기록으로 실측 PPV와 기대 PPV를 나란히 본다
record Rates(double sens, double spec, double base) {
    double ppv() { return sens * base / (sens * base + (1 - spec) * (1 - base)); }
}
var r = new Rates(0.99, 0.99, 0.001);
System.out.printf("기대 PPV %.1f%%, 하루 1e6건이면 오경보 %.0f건%n", 100 * r.ppv(), 1e6 * (1 - r.base()) * (1 - r.spec()));
// → 기대 PPV 9.0%, 하루 1e6건이면 오경보 9990건
```

4. 대처 방향
   - 오경보율을 낮춘다: 임계 상향, 지속 시간 조건("5분 연속"), 증상 기반 알람(사용자 영향 SLO)으로 바꾼다([reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md)).
   - 두 번째 신호를 붙인다: 첫 탐지기의 사후 확률 9.0%를 사전 확률로 다시 베이즈를 돌린다. 오류가 (이상·정상 각각 안에서) **조건부 독립인** 두 번째 탐지기(99%/99%)가 또 울리면 `0.99×0.0902 / (0.99×0.0902 + 0.01×0.9098) = 90.75%`.
     - 두 탐지기가 같은 지표를 본다면 오류가 독립이 아니다. 그때는 이 계산이 PPV를 과대평가한다.

### 2. 블룸 필터를 쓸 때

- 설계: n(예상 원소 수)과 p(허용 위양성)로 m·k를 정한다(5절 식). 라이브러리(Guava `BloomFilter.create(funnel, expectedInsertions, fpp)` 등)도 같은 두 값을 받는다.
- 운영: 삽입 수를 지표로 낸다. 설계 n을 넘으면 위양성이 k제곱으로 커진다(실험 B). 재구성하거나 확장형 필터를 쓴다.

### 3. 독립인지 데이터로 확인

- 로그에서 `P(A)`, `P(B)`, `P(A∩B)`를 센다. `P(A∩B) / (P(A)·P(B))`가 1에서 멀면 독립이 아니다.
  - 예: 두 리전의 분당 에러 여부. 비가 1이면 독립, 10이면 함께 실패하는 경향이 강하다.
- 이 비는 표본이 작으면 흔들린다. 동시 발생 건수가 수십 건은 되어야 의미가 있다(해석).

## 장애 시나리오와 대처

### 1. "99% 정확한" 이상탐지가 알람 피로를 만든다 (⚠ 커리큘럼)

- 현상: 온콜이 알람을 무시하기 시작한다. 진짜 장애 알람도 묻힌다.
- 보이는 형태: 하루 알람 수천~수만 건, 조치 비율 한 자릿수 %(실측 PPV도 낮을 가능성의 신호). 알람 대부분이 "자동 해제".
- 원인: 기저율이 낮다(0.1%). 오경보율 1%가 정상 99.9%에 곱해져 진짜 알람의 10배가 된다(1절 그림, 실험 A).
- 대처: 3절 식으로 기대 PPV를 먼저 계산한다. 오경보율을 낮추고(지속 조건·SLO 기반), 독립인 두 번째 신호와 AND로 묶는다. 알람마다 "진짜 이상이었나"(사후 판정)를 기록해 PPV를 지표로 관리하고, 조치 비율은 별도 지표로 둔다.

### 2. 블룸 필터 용량 초과 → 위양성 급증

- 현상: 캐시 관통 방어용 블룸 필터를 뒀는데 DB 조회가 다시 늘었다. LSM 저장소의 읽기 지연이 올랐다.
- 보이는 형태: "필터가 있다고 했지만 실제로 없음" 비율 지표가 1% → 15%로 오른다(실험 B: 설계 2배 삽입).
- 원인: 설계 n을 넘겨 넣었다. 켜진 비트 비율이 50% → 77%가 되면서 k칸이 전부 1일 확률이 k제곱으로 커졌다.
- 대처: 삽입 수·켜진 비트 비율을 지표로 낸다. 설계 n의 상한에서 재구성하거나 확장형 블룸 필터([data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md) ScalableBloomFilter)로 바꾼다.

### 3. 조건부 확률의 방향을 뒤집는다

- 현상: "에러 요청의 70%가 Android에서 온다(예시)"를 보고 Android 앱 버그로 단정했다.
- 보이는 형태: 대시보드의 에러 분포. 그런데 전체 트래픽의 70%도 Android다.
- 원인: P(Android|에러)를 봤다. 원인을 가르려면 P(에러|Android)와 P(에러|iOS)를 비교해야 한다. 둘은 베이즈 식으로 기저율(트래픽 비율)을 통해 이어진다.
- 대처: 분포가 아니라 **비율**(세그먼트별 에러율)을 본다. 세그먼트 크기를 함께 표시한다.

### 4. 독립 가정이 깨진 곱셈

- 현상: 나이브 베이즈 점수가 0.999를 넘는데 오분류가 잦다. 또는 두 탐지기의 AND 알람이 계산보다 자주 오경보한다.
- 보이는 형태: 확률 출력의 보정 곡선이 대각선에서 멀다(0.99 구간의 실제 비율이 훨씬 낮다).
- 원인: 함께 나오는 단어·같은 원천을 보는 지표를 독립으로 곱했다. 같은 증거를 두 번 센 셈이다.
- 대처: 상관된 특징을 묶거나 하나만 쓴다. 출력을 확률로 쓰려면 검증 집합으로 보정한다. 알람은 원천이 다른 신호끼리 묶는다.

## 핵심 문장

- P(울림|이상)과 P(이상|울림)은 다르다. 둘을 잇는 것은 베이즈 정리이고, 그 사이에 기저율이 있다.
- 기저율이 낮으면 오경보율이 PPV를 정한다. 민감도 99%·특이도 99%·기저율 0.1%면 알람의 약 9%만 진짜다.
- 곱셈 `P(A)·P(B)`는 독립일 때만 맞다. 둘 다 확률이 양수인 배반 사건은 독립이 아니다.
- 블룸 필터 위양성 `(1 − e^(−kn/m))^k`는 해시가 독립·균등하다는 가정 위의 근사(그 가정에서도 k ≥ 2면 실제 값보다 약간 작다)이고, 설계 n을 넘기면 k제곱으로 커진다.
- 나이브 베이즈는 조건부 독립을 가정한 곱이다. 순위는 쓸 만해도 출력값을 그대로 확률로 믿지 않는다.

## 관련 주제·근거

선행·후속:
- 선행: [수학 05 counting-and-birthday-bound](../05-counting-and-birthday-bound/2-summary.md)(경우의 수·생일 한계).
- 후속: [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md)(기댓값·꼬리), [09-common-distributions](../09-common-distributions/2-summary.md), [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md). 정보 이론(14)·큐잉(10)은 [math README](../README.md).
- 다른 영역: [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md), [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md), [reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md), [reliability/01-fault-error-failure-availability](../../reliability/01-fault-error-failure-availability/2-summary.md)(독립 가정과 가용성). 데이터 분석의 베이즈 갱신(data-analysis 26)은 [data-analysis README](../../data-analysis/README.md).

근거:
- Lehman·Leighton·Meyer, 『Mathematics for Computer Science』(MIT 6.042, 2018-06-06판 PDF — https://courses.csail.mit.edu/6.042/spring18/mcs.pdf): 17장 Events and Probability Spaces(17.5 Set Theory and Probability), 18장 Conditional Probability(18.3 Four-Step Method, 18.4 Why Tree Diagrams Work·정리 18.4.1 Bayes' Rule, 18.5 Law of Total Probability, 18.7 Independence, 18.8 Mutual Independence). PDF 목차·본문에서 장·절 번호 확인.
- OpenIntro Statistics 3장 Probability(3.1 Defining probability, 3.2 Conditional probability) — https://www.openintro.org/book/os/ 목차(2026-10-07 열람).
- S. Axelsson, "The base-rate fallacy and the difficulty of intrusion detection", ACM TISSEC 3(3):186–205, 2000, doi:10.1145/357830.357849 (Crossref 초록 확인).
- B. H. Bloom, "Space/Time Trade-offs in Hash Coding with Allowable Errors", CACM 13(7), 1970.
- P. Bose 외, "On the false-positive rate of Bloom filters", Information Processing Letters 108(4):210–213, 2008, doi:10.1016/j.ipl.2008.05.018 — 저자 사본 https://cglab.ca/~morin/publications/ds/bloom-submitted.pdf (1절 기여 3, 결론 절).
- Guava `BloomFilter.create(Funnel, expectedInsertions, fpp)` Javadoc — fpp를 생략한 `create(Funnel, expectedInsertions)`의 기본 fpp는 3% — https://guava.dev/releases/snapshot-jre/api/docs/com/google/common/hash/BloomFilter.html (2026-10-07 열람).
- P. Graham, "A Plan for Spam", 2002-08 — https://paulgraham.com/spam.html (상위 15개 단어, 결합식, 0.9 임계).

실험 목록:
- 실험 A(기저율 PPV, 유병률 0.1·1·10%)·실험 B(블룸 필터 공식 vs 실측, 용량 1~3배): `scratchpad/math/07/e07/Bayes.java`, `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) eclipse-temurin:21-jdk java Bayes.java 42`(재실행 seed 1·2·3). OpenJDK 21.0.12 Temurin, 2026-10-07.
- 계산 보조: 두 번째 탐지기 사후 확률(90.75%), 블룸 m·k, 나이브 베이즈 예시(0.9979) — 호스트 Python 3.12.3 표준 라이브러리.
