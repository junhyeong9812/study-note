# data-analysis/11-multiple-comparisons — 다중 비교·p-해킹·Bonferroni·BH 절차 — 정리 (힌트)

## 해결하는 문제

A/B 테스트 대시보드에 지표가 20개 있다. 그중 하나가 p = 0.03이다. "새 결제 버튼이 재구매율을 올렸다"고 발표해도 될까?

```text
  검정 1개                       검정 20개 (모두 진짜 효과 없음)
  ┌──────────┐                   ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
  │ p < 0.05 │ 5% 확률로 거짓 경보  │  │  │▓▓│  │  │  │  │  │  │  │  ← 하나쯤은 우연히 유의
  └──────────┘                   ├──┼──┼──┼──┼──┼──┼──┼──┼──┼──┤
                                 │  │  │  │  │  │  │  │  │  │  │
                                 └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
                                 하나 이상 유의할 확률 = 1 − 0.95^20 ≈ 0.64 (서로 독립일 때)
```

- 검정 하나는 5%만 틀리게 설계한다. 그런데 검정을 여러 번 하면 "어딘가 하나는 틀린다"의 확률이 쌓인다.
- 그중 유의한 것만 골라 보고하면, 그 보고는 우연을 발견처럼 보이게 만든다.

쉬운 예: 주사위를 한 번 던져 6이 나오면 1/6이다. 20번 던져 6이 한 번이라도 나오면 놀랍지 않다(1 − (5/6)^20 ≈ 0.97).

똑같은 구조다.\
지표 20개를 각각 α = 0.05로 보는 것은 "5% 확률 사건"을 20번 굴리는 것이다.

실무 예:
- 실험 리포트가 지표 20개 × 기기 3종 × 국가 5개를 보여 준다. 표 안에 300개의 비교가 숨어 있다.
- 효과가 없자 분석가가 "iOS 30대 신규 사용자"까지 쪼개 유의한 칸을 찾는다.
- 서비스 500개에 지표 3개씩 3σ 경보 규칙을 걸었더니 매번 몇 개씩 울린다(장애 시나리오 4).

## 동작·원리

### 1. 검정을 여러 번 하면 오류가 누적된다

```text
  모든 귀무가설이 참이고 검정끼리 독립일 때
  P(하나 이상 유의) = 1 − (1 − α)^m

  m (검정 수)     1      5      10     20     50     100
  α = 0.05      0.05   0.226  0.401  0.642  0.923  0.994
```

- *귀무가설(H0)*: "효과 없음" 같은, 반박하려고 세운 기준 가설. 자세한 절차는 [09-hypothesis-testing](../09-hypothesis-testing/2-summary.md).
- *p값*: 귀무가설과 모형 가정이 맞다고 할 때, 관측한 것만큼 또는 더 극단적인 결과가 나올 확률.
  - 흔한 오해: "p값은 귀무가설이 참일 확률이다." 아니다. ASA 2016 성명의 원칙 2가 정확히 이 오해를 짚는다.
- *가족(family)*: 한 결론을 내리려고 함께 보는 검정들의 묶음. 실험 하나의 지표 20개가 한 가족이다.
- *FWER(family-wise error rate)*: 가족 안에서 거짓 양성이 **하나라도** 나올 확률.
- 이 누적은 귀무가 참일 때 p값이 0~1에 고르게 퍼지기 때문에 생긴다. 균등이면 어떤 검정이든 p < 0.05일 확률이 5%다.
  - 전제: 검정 통계량이 연속형이고 귀무 분포를 정확히(또는 충분히 잘 근사해) 알고 있다. 이산 데이터(비율·건수)에서는 귀무 분포를 정확히 알아도 p값이 띄엄띄엄한 값만 가져 균등이 아니다. 이때는 P(p ≤ α) ≤ α만 보장되고, 1 − (1 − α)^m도 근삿값이다(예: n = 10 단측 정확 이항검정에서 P(p ≤ 0.05) = 0.0107, 계산).

### 실험: A/A 실험의 지표 20개

```python
# 두 그룹 모두 같은 전환율 → 진짜 효과 0. 지표마다 두 비율 z 검정
for p in BASE:                                   # 기준 전환율 2%~21% (예시) 20개
    y1 = rng.binomialvariate(n, p); y2 = rng.binomialvariate(n, p)   # n = 5000 (그룹당)
    ps.append(two_prop_p(y1, n, y2, n))
raw = [p < 0.05 for p in ps]
```

- 환경: 호스트 Python 3.12.3 표준 라이브러리(`random.binomialvariate`는 3.12 신규), 시뮬레이션 2000회, seed 20261008. 코드 `e11_multi.py`.
- 두 비율 z 검정의 전제(그룹 안·사이 독립, 성공·실패 건수 각 10 이상)는 이 설정에서 맞는다. 사용자를 독립으로 뽑았고, 가장 작은 기대 성공 수도 5000 × 0.02 = 100이다([20](../20-categorical-inference/2-summary.md)).

```text
(A) A/A, 지표 20개, 그룹당 n=5000, 반복 2000회, seed 20261008
    이론 1-0.95^20 = 0.642
    보정 없음: 하나 이상 유의 비율 = 0.630, 실험당 평균 유의 개수 = 1.00
    Bonferroni(0.05/20): 하나 이상 유의 = 0.047
    BH(q=0.05)        : 하나 이상 유의 = 0.048   (모두 귀무면 FDR = FWER)
    귀무 p값 분포(10칸): 0.102 0.097 0.102 0.100 0.102 0.098 0.099 0.099 0.100 0.101
    실험당 유의 개수 분포: {0: 740, 1: 717, 2: 401, 3: 102, 4: 34, 5: 4, 6: 2}
```

- 관찰
  - 효과가 전혀 없는데도 실험 2000번 중 1260번(63%)에서 "유의한 지표"가 하나 이상 나왔다. 이론값 0.642와 시뮬레이션 오차 안에서 맞는다.
  - 실험당 평균 유의 개수 1.00 = 20 × 0.05다. 기댓값의 선형성이라 독립이 아니어도 성립한다([math/08](../../math/08-expectation-variance-tails/2-summary.md)).
  - p값 10칸이 각각 약 10%씩이다. 귀무에서 p값이 균등하다는 것을 보여 준다.

### 2. 숨은 비교 — 고르고 나서 검정하기

```text
  보고서에 보이는 검정: 1개 ("B반 vs C반, p = 0.01")

  실제로 한 비교:
   반 20개를 눈으로 훑음 ──> 평균이 가장 높은 반과 가장 낮은 반을 고름 ──> 그 둘만 t 검정
   (비공식 비교 190쌍)                                                    (공식 검정 1개)
```

- *데이터 스누핑(data snooping)*: 데이터를 먼저 눈으로 본 뒤 차이가 커 보이는 것만 골라 공식 검정하는 것. OpenIntro 4판 예제 7.44가 이 이름으로 경고한다. 눈으로 한 비교도 비교다.
- *p-해킹(p-hacking)*: 유의한 결과가 나올 때까지 분석 선택(지표·구간·이상값 제거·세그먼트)을 바꾸는 것. ASA 2016 발표문은 'p-hacking'·'data dredging'을 작은 p값 찾기에 매달리는 관행으로 짚는다.
- 엿보기(중간에 여러 번 보고 유의하면 멈추기)도 같은 구조다. 시간 축의 다중 비교다. 자세히는 [data-analysis 15](../15-ab-pitfalls-srm-peeking/2-summary.md).

### 실험: 극단 두 반만 골라 검정

- 반 20개, 반마다 25명, 모든 반이 같은 분포 N(100, 15²)에서 나왔다. 평균이 가장 큰 반과 가장 작은 반만 골라 두 표본 t 검정(df 48). 2000회, seed 44.
- 데이터가 정규·독립이고 두 반의 크기·분산이 같아서, 미리 정한 두 반이었다면 t 검정의 전제가 다 맞는 설정이다.

```text
(C) 반 20개(각 25명, 모두 같은 분포), 극단 두 반만 골라 t 검정, 반복 2000회, seed 44
    p < 0.05 비율 = 0.891   (명목 0.05)
```

- 진짜 차이가 하나도 없는데 89%가 "유의"하다. 명목 5%의 약 18배다.
- 검정 자체는 맞게 계산했다. 틀린 것은 **어떤 둘을 비교할지 데이터를 보고 정한 것**이다.

### 3. Bonferroni — "하나라도 틀릴 확률"을 묶는다

```text
  가족의 검정 m개를 각각 α/m 로 검정한다
  m = 20, α = 0.05  →  각 검정의 문턱 0.0025

  근거(합집합 상한):  P(V ≥ 1) = P(A1 ∪ … ∪ Am) ≤ P(A1) + … + P(Am) ≤ m · α/m = α
                     Ai = "i번째 참인 귀무를 기각"
```

- *Bonferroni 보정*: 문턱을 α/m로 낮춰 FWER ≤ α를 보장한다(OpenIntro 7.5.6은 α* = α/K로 쓴다. K는 비교 수).
- 합집합 상한만 쓰므로 **검정끼리 독립일 필요가 없다**. Benjamini–Hochberg 1995 2절도 "각 가설을 α/m로 검정하면 P(V ≥ 1) ≤ α가 보장된다"고 적는다.
- 대가: 검정 수가 늘수록 문턱이 작아져 진짜 효과도 놓친다(검정력 하락). 지표끼리 상관이 클수록 실제 FWER이 α보다 훨씬 작아져, 필요 이상으로 보수적이 된다.

### 실험: 지표끼리 상관이 있으면

- 귀무가 참인 z 통계량 20개를 공통 성분으로 상관시켰다. `z_i = √ρ·Z0 + √(1−ρ)·e_i`. 20000회, seed 5.

```text
(E) 상관된 귀무 지표 20개(공통 성분 rho), 반복 20000회, seed 5
    rho=0.0: 보정 없음 FWER=0.640, Bonferroni FWER=0.0515
    rho=0.5: 보정 없음 FWER=0.421, Bonferroni FWER=0.0362
    rho=0.8: 보정 없음 FWER=0.227, Bonferroni FWER=0.0183
    rho=0.95: 보정 없음 FWER=0.112, Bonferroni FWER=0.0075
```

- 독립(ρ = 0)일 때 Bonferroni의 정확한 FWER은 1 − (1 − 0.0025)^20 = 0.0488이다. 시뮬레이션 0.0515는 표준오차(약 0.0015) 2배 안이다.
- 상관이 커질수록 보정 없는 FWER도 줄고, Bonferroni는 0.05보다 한참 아래로 내려간다. 같은 것을 20번 잰 셈이라 "실질 검정 수"가 20보다 작기 때문이다(해석).

### 4. BH 절차 — "발견 중 거짓의 비율"을 묶는다

```text
  Benjamini–Hochberg 1995 표 1 (가설 m개를 검정한 결과)
                       유의 아님   유의(발견)   합
  참인 귀무              U          V          m0
  거짓인 귀무            T          S          m − m0
  합                   m − R       R          m

  FWER = P(V ≥ 1)          FDR = E[ V / R ]   (R = 0이면 V/R = 0으로 둔다)
```

- *FDR(false discovery rate)*: 기각한 것(발견) 가운데 거짓 발견 비율의 기댓값(BH 1995 2.1절).
- 두 성질(BH 1995 2.1절)
  1. 모든 귀무가 참이면 FDR = FWER.
  2. 진짜 효과가 섞여 있으면 FDR ≤ FWER. 그래서 FDR만 묶으면 덜 엄격하고 검정력이 높아질 수 있다.
- 절차(BH 1995 3.1절, q는 목표 FDR)

```text
  p값을 작은 순으로 정렬: p(1) ≤ p(2) ≤ … ≤ p(m)
  p(k) ≤ (k/m)·q 인 가장 큰 k를 찾고, 1~k번째를 모두 기각한다

  m = 20, q = 0.05일 때 문턱선
   k        1       2       3       4       5     …   20
   k/m·q  0.0025  0.0050  0.0075  0.0100  0.0125  …  0.05
          ↑ Bonferroni 문턱과 같다           ↑ 순위가 낮을수록 문턱이 느슨해진다
```

- "가장 큰 k"라서, 중간에 문턱을 넘는 순위가 있어도 더 뒤의 순위가 문턱 아래면 그 앞은 모두 기각한다(step-up).
- 보장(BH 1995 정리 1과 그 보조정리): **검정 통계량이 서로 독립**이면, 거짓 귀무가 어떻게 섞여 있든 FDR ≤ (m0/m)·q ≤ q. 논문의 비고는 거짓 귀무 쪽 통계량끼리의 독립은 증명에 필요 없다고 적는다.
  - 독립이 아닐 때: Benjamini–Yekutieli 2001(Annals of Statistics 29(4)) 정리 1.2는 참인 귀무 쪽 통계량에 대한 **양의 회귀 의존(PRDS)**이면 같은 절차가 FDR ≤ (m0/m)·q를 지킨다고 증명한다. 임의의 의존에서는 q를 Σ(1/i)(i = 1..m)로 나눈 보수적 변형이 필요하다(같은 논문 정리 1.3).

### 실험: 20개 중 5개만 진짜 효과

- 기준 전환율 17~21%인 지표 5개만 상대 +15% 효과, 나머지 15개는 귀무. 그룹당 5000명, 2000회, seed 7.

```text
(B) 20개 중 5개(기준 17~21%)만 상대 +15%, 반복 2000회, seed 7
    raw  : 실험당 참 발견 4.72/5 (검정력 0.94), 거짓 발견 0.74, FDR(평균 FDP) 0.119, FWER 0.536
    bonf : 실험당 참 발견 3.46/5 (검정력 0.69), 거짓 발견 0.04, FDR(평균 FDP) 0.010, FWER 0.041
    bh   : 실험당 참 발견 4.21/5 (검정력 0.84), 거짓 발견 0.20, FDR(평균 FDP) 0.035, FWER 0.172
```

- *FDP*: 한 번의 실험에서 실제로 나온 거짓 발견 비율 V/R. 그 평균이 FDR의 시뮬레이션 추정이다.
- 관찰
  - 보정 없음: 진짜 5개를 거의 다 찾지만, 실험 절반 이상(0.536)에서 거짓 발견이 섞인다.
  - Bonferroni: 거짓 발견은 거의 없지만(FWER 0.041), 진짜 효과의 31%를 놓친다.
  - BH: FDR 0.035로 정리 1의 상한 (15/20)·0.05 = 0.0375 아래다. 검정력은 Bonferroni보다 높다. 대신 FWER은 0.172로, "하나도 틀리지 않음"은 보장하지 않는다.
- 고르는 기준: 거짓 발견 하나가 비싸면(출시 결정 1차 지표) FWER. 후보를 추려 다음 단계에서 다시 확인하면(탐색 지표·스크리닝) FDR.

### 5. 유의한 결과 중 몇 개가 진짜인가 — Ioannidis 2005

```text
  R = (검정하는 관계 중 진짜 관계 수) / (진짜 아닌 관계 수)    ← 분야의 "사전 오즈"
  PPV = P(진짜 | 유의) = (1 − β)·R / (R − β·R + α)            (Ioannidis 2005)

  α = 0.05          검정력 0.8    검정력 0.2
  R = 1             0.941        0.800
  R = 0.25          0.800        0.500
  R = 0.1           0.615        0.286
  R = 0.01          0.138        0.038
```

- *PPV(positive predictive value)*: 유의하다고 나온 것 중 진짜인 비율.
- *검정력(1 − β)*: 진짜 효과가 있을 때 유의하게 나올 확률. 계산은 data-analysis 10([10-power-and-sample-size](../10-power-and-sample-size/2-summary.md)).
- 표는 식에 넣어 계산한 값이다(`e11_multi.py` (D)). 편향 u = 0, 독립 팀 1개를 가정한 기본식이다.
- [math/07](../../math/07-probability-and-bayes/2-summary.md)의 기저율 문제와 같은 구조다. 탐지기(검정)가 같아도, 찾는 것이 드물면(R 작음) 양성 대부분이 거짓이다.
- 논문의 따름정리 일부(Ioannidis 2005 원문)
  - 연구가 작을수록(검정력 낮음) 결과가 참일 가능성이 낮다(따름정리 1).
  - 검정한 관계가 많고 사전 선별이 적을수록 낮다(따름정리 3).
  - 설계·정의·결과 변수·분석 방법의 유연성이 클수록 낮다(따름정리 4). p-해킹이 이 유연성이다.

## 쓰이는 자료구조·알고리즘

- **Bonferroni**: 문턱 α/m 비교만 한다. O(m).
- **BH 절차**: p값 정렬 O(m log m) + 한 번 훑기. 정렬은 [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md).
  - SQL에서는 `row_number() OVER (ORDER BY p)`로 순위를 매기고 문턱선과 비교한다. 윈도 함수는 [database/05-window-functions-and-cte](../../database/05-window-functions-and-cte/2-summary.md).
- **시뮬레이션(A/A)**: 효과 0인 데이터를 반복 생성해 실제 거짓 양성률을 잰다. 난수 생성기 성질은 [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상 | 의심할 원리 | 확인 |
|---|---|---|
| 지표 수십 개 중 1~2개만 p < 0.05 | 다중 비교 누적 | 가족 크기 m을 세고, Bonferroni·BH로 다시 판정 |
| "이 세그먼트에서만 효과" | 숨은 비교(세그먼트 × 지표) | 분석 전에 정한 세그먼트였나? 쪼갠 칸 수를 m에 넣기. "에서만"은 세그먼트 간 효과 차이(상호작용)를 직접 검정(Gelman·Stern 2006) |
| 재실험하면 효과가 사라짐 | 우연이 골라졌다 | 새 표본에서 같은 1차 지표 하나만 다시 검정 |
| 유의한 결과가 너무 많고 크다 | 낮은 검정력 + 선택 보고 | PPV 표로 어림, 사전에 정한 분석인지 확인 |

- 첫 질문은 "검정을 몇 번 했나?"다. 보고서에 보이는 수가 아니라 **실제로 들여다본 비교 수**를 센다.

### 2. 코드로 확인 — Bonferroni·BH (Python 3.12)

```python
def bonferroni(ps, alpha):
    m = len(ps)
    return [p <= alpha / m for p in ps]

def bh(ps, q):
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    k = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= rank / m * q:
            k = rank                      # 조건을 만족하는 "가장 큰" 순위
    rej = [False] * m
    for rank, i in enumerate(order, 1):
        rej[i] = rank <= k
    return rej
```

### 3. SQL로 확인 — 실험 결과 테이블에서 BH (PostgreSQL 17.11)

```sql
WITH r AS (
  SELECT metric, truly_changed, p,
         row_number() OVER (ORDER BY p) AS k,
         count(*)     OVER ()           AS m
  FROM t
), cut AS (                                  -- p_(k) <= k/m * q 를 만족하는 가장 큰 k
  SELECT coalesce(max(k), 0) AS kmax FROM r WHERE p <= k::float8 / m * 0.05
)
SELECT metric, truly_changed, round(p::numeric, 5) AS p, k,
       round((k::float8 / m * 0.05)::numeric, 4) AS bh_line,
       p < 0.05 AS raw, p <= 0.05 / m AS bonferroni,
       k <= (SELECT kmax FROM cut) AS bh
FROM r WHERE k <= 10 ORDER BY k;
```

- 환경: `postgres:17` 컨테이너(PostgreSQL 17.11, `--network none`), 실험 (B) 설정의 1회분 p값 20개(seed 77). 코드 `e11_pg.py`·`e11_bh.sql`.

```text
  metric   | truly_changed |    p    | k  | bh_line | raw | bonferroni | bh
-----------+---------------+---------+----+---------+-----+------------+----
 metric_20 | t             | 0.00001 |  1 |  0.0025 | t   | t          | t
 metric_17 | t             | 0.00033 |  2 |  0.0050 | t   | t          | t
 metric_18 | t             | 0.00450 |  3 |  0.0075 | t   | f          | t
 metric_19 | t             | 0.01350 |  4 |  0.0100 | t   | f          | f
 metric_15 | f             | 0.05371 |  5 |  0.0125 | f   | f          | f
 metric_08 | f             | 0.07168 |  6 |  0.0150 | f   | f          | f
 metric_16 | t             | 0.09987 |  7 |  0.0175 | f   | f          | f
 metric_01 | f             | 0.20073 |  8 |  0.0200 | f   | f          | f
 metric_11 | f             | 0.20379 |  9 |  0.0225 | f   | f          | f
 metric_02 | f             | 0.25352 | 10 |  0.0250 | f   | f          | f
(10 rows)
```

- 이 1회분에서는 Bonferroni 2개, BH 3개, 보정 없음 4개를 발견했다. 셋 다 거짓 발견은 없었다. metric_16은 진짜 효과가 있지만 어느 방법으로도 못 찾았다(검정력 부족).
- `truly_changed`는 시뮬레이션이라 아는 정답이다. 실제 실험에는 이 열이 없다.

### 4. 설계로 막기

- 분석 전에 **1차 지표 하나**와 판단 기준을 정해 둔다. 나머지는 가드레일·탐색 지표로 나눈다(지표 설계는 [data-analysis 16](../16-metrics-design/2-summary.md)).
- 탐색에서 찾은 효과는 "가설"로 적고, 새 실험(새 표본)에서 그 하나만 다시 검정한다.
- 세그먼트 분석은 사전에 정한 몇 개만 하거나, 쪼갠 칸 수를 m에 넣고 보정한다.
- 결과 보고에 "몇 개를 검정했는지"를 함께 적는다(ASA 2016 원칙 4: 올바른 추론에는 완전한 보고와 투명성이 필요하다).

## 장애 시나리오와 대처

### 1. 지표 20개 중 1개 유의 → 우연을 발견으로 발표 (⚠ 커리큘럼)

- 현상: 새 기능 실험에서 1차 지표(전환율)는 변화 없음. 대시보드의 지표 20개 중 "평균 세션 수"만 p = 0.03.
- 보이는 형태: 리포트 제목이 "새 기능이 세션 수를 늘림". 다음 분기 재실험에서는 효과가 없다.
- 원인: 효과가 없어도 지표 20개면 하나 이상 유의할 확률이 약 64%다(독립 가정, 실험 A에서 63%). 그 하나만 보고했다.
- 대처: 1차 지표를 미리 정한다. 나머지 지표는 Bonferroni(0.05/20 = 0.0025)나 BH로 판정한다. 탐색 결과는 재실험으로 확인한다.

### 2. 효과가 없자 세그먼트를 쪼갬

- 현상: 전체 효과 없음 → 기기·국가·신규/기존·연령대로 쪼개 "iOS 신규 30대에서 +8%"를 찾음.
- 보이는 형태: 세그먼트 표에 셀이 수십~수백 개. 유의한 칸은 표본이 작은 칸에 몰린다.
- 원인: 쪼갠 칸 하나하나가 검정이다. 데이터를 보고 유의한 칸을 골랐다(데이터 스누핑, 실험 C의 89%).
- 대처: 세그먼트를 사전에 정하거나, 쪼갠 칸 수 전체를 m으로 보고 보정한다. 찾은 세그먼트는 그 세그먼트만 대상으로 새 실험을 한다.

### 3. 수백 개 지표에 Bonferroni → 진짜 효과도 다 놓침

- 현상: 지표 300개 전부에 Bonferroni(0.05/300 ≈ 0.00017). 몇 달째 "유의한 지표 없음".
- 보이는 형태: 효과 크기 추정치는 일관되게 양수인데 아무것도 문턱을 못 넘는다.
- 원인: Bonferroni는 독립이 아니어도 FWER을 묶지만, 상관이 큰 지표가 많으면 지나치게 보수적이다(실험 E: ρ = 0.8에서 실제 FWER 0.018). 검정력이 바닥이다.
- 대처: 결정에 쓰는 1차 지표는 소수로 줄인다. 탐색 지표는 FDR(BH)로 본다(의존 구조에 따른 보장 조건은 4절). 같은 것을 재는 지표(중복 지표)는 묶는다.

### 4. 서비스 500개 × 지표 3개 경보 → 매일 거짓 경보

- 현상: 지표마다 "평소 평균에서 3σ 벗어나면 경보"를 걸었다. 정상 상태에서도 평가 주기마다 몇 개씩 울린다.
- 보이는 형태: 온콜이 경보를 무시하기 시작한다(알람 피로).
- 원인: 정규·독립을 가정해도 3σ 양쪽 꼬리는 약 0.0027이다. 1500개를 동시에 보면 평가 한 번에 기대 약 4개가 우연히 넘는다(1500 × 0.0027 ≈ 4.0). 실제 지표는 꼬리가 더 무거워 더 많을 수 있다([math/09](../../math/09-common-distributions/2-summary.md)).
- 대처: 증상 기반 경보로 바꾸고 경보 수 자체를 줄인다([reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md)). 지속 시간 조건(여러 주기 연속)을 붙인다. 기저율 관점은 [math/07](../../math/07-probability-and-bayes/2-summary.md).

## 핵심 문장

- 검정 하나의 α는 5%여도, 효과 없는 검정 m개(독립)를 보면 하나 이상 유의할 확률은 1 − 0.95^m이다. m = 20이면 약 0.64다.
- 눈으로 훑고 고른 뒤 하는 검정도 다중 비교다. 보고서에 보이는 검정 수가 아니라 들여다본 비교 수를 센다.
- Bonferroni(α/m)는 독립 가정 없이 "하나라도 틀릴 확률(FWER)"을 α 이하로 묶는다. 대신 검정력을 잃는다.
- BH 절차는 정렬한 p값을 (k/m)·q 선과 비교해, 독립인 검정에서 "발견 중 거짓 비율의 기댓값(FDR)"을 q 이하로 묶는다.
- 유의한 결과가 진짜일 확률(PPV)은 α만이 아니라 검정력과 사전 오즈에 달렸다.

## 관련 주제·근거

- 선행
  - [09-hypothesis-testing](../09-hypothesis-testing/2-summary.md) — 귀무·대립·p값·1종/2종 오류
  - [10-power-and-sample-size](../10-power-and-sample-size/2-summary.md) — 검정력(PPV 식의 1 − β)
- 후속·연결
  - [20-categorical-inference](../20-categorical-inference/2-summary.md) — 실험에 쓴 두 비율 z 검정
  - [21-numerical-inference-t-anova](../21-numerical-inference-t-anova/2-summary.md) — ANOVA 뒤 쌍별 비교의 Bonferroni(OpenIntro 7.5.6 예제)
  - [12-correlation-vs-causation](../12-correlation-vs-causation/2-summary.md) — 부분군을 쪼갤 때 생기는 또 다른 함정(심슨의 역설)
  - [14-ab-testing-design](../14-ab-testing-design/2-summary.md) · [15-ab-pitfalls-srm-peeking](../15-ab-pitfalls-srm-peeking/2-summary.md)(엿보기 — 시간 축의 다중 비교) · [16-metrics-design](../16-metrics-design/2-summary.md)(1차·가드레일·탐색 지표)
  - [data-analysis 27](../27-da-symptom-index/2-summary.md)(증상 색인)
  - [math/07-probability-and-bayes](../../math/07-probability-and-bayes/2-summary.md) — 기저율(PPV와 같은 구조), [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md) — 기댓값의 선형성
  - [reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md) — 경보 수와 거짓 경보
  - [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md) — A/B 배정 구현
- 문헌
  - OpenIntro Statistics 4판 7.5.6 "Multiple comparisons and controlling Type 1 Error rate"(Bonferroni α* = α/K, K = k(k−1)/2), 예제 7.44(data snooping) — <https://www.openintro.org/book/os/> (커리큘럼의 "7.5C"는 이 판 PDF 목차에서는 7.5.6이다)
  - Benjamini, Hochberg (1995) "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing", JRSS B 57(1):289–300 — 표 1, 2.1절(FDR 정의와 두 성질), 3.1절(절차, 정리 1: 독립 검정 통계량에서 FDR ≤ (m0/m)q). JSTOR 스캔 사본으로 열람
  - Benjamini, Yekutieli (2001) "The control of the false discovery rate in multiple testing under dependency", Annals of Statistics 29(4):1165–1188 — 정리 1.2(PRDS에서 BH 절차의 FDR 통제), 정리 1.3(임의 의존에서 Σ1/i 변형). 저자 사본 <https://www.math.tau.ac.il/~ybenja/MyPapers/benjamini_yekutieli_ANNSTAT2001.pdf>
  - Ioannidis (2005) "Why Most Published Research Findings Are False", PLoS Med 2(8): e124 — R의 정의, PPV = (1 − β)R/(R − βR + α), 따름정리 1~6 <https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124>
  - ASA 보도자료(2016-03-07) "Statement on Statistical Significance and P-Values" — 6원칙(2: p값은 가설이 참일 확률이 아니다, 4: 완전한 보고와 투명성), 'p-hacking'·'data dredging' 언급 <https://www.amstat.org/docs/default-source/amstat-documents/p-valuestatement.pdf> (브리핑의 `/asa/files/pdfs/p-valuestatements.pdf` 주소는 2026-10-08에 404)
  - Python 3.12 `statistics.NormalDist`, `random.binomialvariate` <https://docs.python.org/3.12/library/statistics.html>
  - PostgreSQL 17 3.5 Window Functions·9.22 Window Functions
- 실험 목록(모두 합성 데이터)
  - `e11_multi.py` (호스트 Python 3.12.3): (A) A/A 지표 20개 FWER·p값 균등성(2000회, seed 20261008), (B) 5/20 진짜 효과에서 보정 없음·Bonferroni·BH의 검정력·FDR·FWER(2000회, seed 7), (C) 극단 두 반 골라 검정(2000회, seed 44), (D) Ioannidis PPV 표(계산), (E) 상관된 지표의 FWER(20000회, seed 5)
  - `e11_pg.py` + `e11_bh.sql` (postgres:17 컨테이너, PostgreSQL 17.11): 윈도 함수로 Bonferroni·BH 판정
