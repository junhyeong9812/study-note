# data-analysis/12-correlation-vs-causation — 상관계수·교란·심슨의 역설 — 정리 (힌트)

## 해결하는 문제

새 결제 화면을 점진 배포했다. 대시보드는 이렇게 말한다.

```text
                 새 화면     옛 화면
  전체 전환율      4.53%      7.04%     ← "새 화면이 전환을 2.5%p 떨어뜨렸다 → 롤백"
  모바일          3.53%      2.96%     ← 새 화면이 높다
  PC             8.52%      8.06%     ← 새 화면이 높다
  (합성 데이터, 실험 B)
```

- 기기별로 보면 두 기기 모두 새 화면이 낫다. 합치면 반대다. 어느 쪽을 믿어야 하나?
- 숫자만으로는 답이 안 나온다. **데이터가 어떻게 만들어졌는지(누가 새 화면을 받았는지)**를 알아야 한다.

쉬운 예: 아이스크림이 많이 팔리는 날 물놀이 사고도 많다. 아이스크림이 사고를 부르지 않는다. 더운 날씨가 둘 다를 늘린다.

똑같은 구조다.\
위 표에서는 "기기"가 새 화면 노출과 전환율을 둘 다 정했다.

실무 예:
- 캐시 미스가 많은 노드가 느리다 → 캐시를 키웠는데 그대로다. 트래픽이 많은 노드가 미스도 많고 느렸다.
- 프리미엄 기능을 쓰는 사용자의 잔존율이 높다 → 기능을 모두에게 켰는데 잔존율이 그대로다. 원래 열성 사용자가 기능을 썼다([03-observational-vs-experimental](../03-observational-vs-experimental/2-summary.md)).

## 동작·원리

### 1. 상관계수가 재는 것 — "직선에 얼마나 가까운가"

```text
   r ≈ +0.9          r ≈ 0             r = 0 인데 완전한 관계       r ≈ 0.94 (이상값 하나)
   y │      ••       y │ •  •  •        y │•                 •      y │                  •
     │    ••           │•  •  • •         │ •               •         │
     │  ••             │ • •  •  •        │   •           •           │
     │••               │•  •   • •        │      •     •              │ ••• (무관한 30쌍)
     └──────── x       └──────── x        └─────•──•──────── x        └──────────────── x
                                           y = x² (x = −5..5)
```

- *피어슨 상관계수 r*: 두 변수의 표준화 점수를 곱해 평균 낸 값. `r = (1/(n−1)) Σ ((xi − x̄)/sx)((yi − ȳ)/sy)`(OpenIntro 8.1.4 각주). −1~1이다.
  - 공분산을 두 표준편차로 나눈 것이다. 공분산은 [math/08](../../math/08-expectation-variance-tails/2-summary.md).
- r은 **직선 관계의 강도**만 잰다(OpenIntro 8.1.4). 곡선 관계는 강해도 r이 작을 수 있다.
- *스피어만 순위 상관*: 값을 순위로 바꾼 뒤 피어슨 r을 구한 것. 단조(한 방향으로만 증가·감소) 관계의 강도다. Python 3.12 `statistics.correlation(x, y, method='ranked')`가 이것이다(3.12에서 추가, 동점은 평균 순위).
- 상관은 방향이 없다. corr(X, Y) = corr(Y, X)다. 그래서 상관만으로는 **무엇이 원인인지** 말할 수 없다.

### 실험: r이 놓치는 것

```text
(E) y = x² (x=-5..5): Pearson = 0.000, Spearman = 0.000
    무관한 30쌍: Pearson = 0.046, Spearman = 0.030
    + 이상값 (20, 20) 하나: Pearson = 0.944, Spearman = 0.121
```

- 환경: 호스트 Python 3.12.3, `statistics.correlation`, seed 9. 코드 `e12_corr.py`.
- y = x²는 x로 y가 완전히 정해지는데 r = 0이다. 대칭이라 순위 상관도 0이다. **r = 0은 "관계 없음"이 아니라 "직선 관계 없음"**이다.
- 무관한 30쌍에 이상값 하나를 더하자 r이 0.046 → 0.944로 뛰었다. 순위 상관은 0.121로 덜 흔들렸다. 산점도를 먼저 봐야 하는 이유다(EDA, [data-analysis 06](../06-exploratory-data-analysis/2-summary.md)).

### 2. 상관이 생기는 다섯 갈래

```text
  ① 인과        X ──▶ Y
  ② 역인과       X ◀── Y            (느린 노드에 운영자가 캐시를 더 붙였다)
  ③ 교란        X ◀── Z ──▶ Y      (트래픽이 미스와 지연을 둘 다 늘림)
  ④ 선택(충돌)   X ──▶ C ◀── Y      C로 걸러 본 데이터 안에서만 X–Y 상관이 생김
  ⑤ 우연        X     Y            지표를 많이 보면 하나쯤 (11 다중 비교)
```

- *교란 변수(confounding variable)*: 설명 변수와 반응 변수 둘 다와 상관된 변수(OpenIntro 1.3.4). 정의와 예는 [03](../03-observational-vs-experimental/2-summary.md)에서 다뤘다.
- *충돌 변수(collider)*: 두 화살표가 들어오는 변수. 그 값으로 걸러 보면 원래 무관한 X·Y가 상관된다(Pearl 외 Primer 2.3절 "Colliders" — 목차로 확인, 본문은 1장만 열람). 자세히는 [data-analysis 25](../25-causal-inference-basics/2-summary.md).
- 그림의 화살표는 데이터에 없다. 데이터는 ①~⑤ 어느 것이든 같은 상관을 낼 수 있다.

### 실험: 교란 변수만으로 생긴 상관

- Z(트래픽)가 X(캐시 미스 수)와 Y(지연)를 둘 다 만든다. X는 Y에 아무 영향이 없다. `X = Z + e1`, `Y = 2Z + e2`, n = 5000, seed 3.

```text
(D) Z→X, Z→Y, X→Y 없음 (n=5000, seed 3)
    corr(X, Y) = 0.635
    Z로 조정한 편상관 corr(X|Z, Y|Z) = 0.021
    Z가 거의 같은 층(|Z|<0.1, n=411)만: corr = 0.056
```

- 이론값(Z, e1, e2가 분산 1이고 서로 독립일 때 — 실험 코드가 그렇게 생성): Cov(X, Y) = 2, Var X = 2, Var Y = 5 → r = 2/√10 ≈ 0.632. 시뮬레이션 0.635와 맞는다.
- *편상관(partial correlation)*: X와 Y 각각에서 Z로 설명되는 부분(Z에 대한 선형 회귀 잔차)을 뺀 뒤 구한 상관. 0.021로 거의 사라졌다.
  - 흔한 오해: 편상관은 언제나 "Z를 고정했을 때의 상관(조건부 상관)"이다. 다변량 정규인 이 실험에서는 같지만, 일반적으로는 다를 수 있다(Baba·Sibuya 2005).
- Z가 비슷한 층만 보아도 0.056으로 작다. 단, **Z를 재고 있었기 때문에** 조정할 수 있었다.

### 3. 심슨의 역설 — 모든 부분군과 전체의 방향이 반대

```text
  Pearl·Glymour·Jewell 『Causal Inference in Statistics: A Primer』(2016) 표 1.1

                 약 복용               미복용
  남       81/87   = 93%        234/270 = 87%      복용이 높다
  여       192/263 = 73%        55/80   = 69%      복용이 높다
  합계      273/350 = 78%        289/350 = 83%      미복용이 높다  ← 반전

  왜? 복용자 350명 중 여성 263명(75%), 미복용자 350명 중 여성 80명(23%)
      여성은 약과 무관하게 회복률이 낮다
      → "복용" 열의 합계는 회복이 어려운 사람으로 채워져 있다
```

- *심슨의 역설(Simpson's paradox)*: 전체에서 보이는 연관이 모든 부분군에서 뒤집히는 현상(Primer 1.2절).
- 합계는 부분군 비율의 **가중 평균**이다. 가중치(각 열의 남녀 구성)가 열마다 다르면, 부분군에서 이긴 쪽이 합계에서 질 수 있다.
  - 복용 78% = 93%×(87/350) + 73%×(263/350). 미복용 83% = 87%×(270/350) + 69%×(80/350).
- 같은 구성(전체 성비 357:343)으로 맞춰 다시 가중하면 복용 83.3%, 미복용 77.9%다(실험 A의 표준화 계산). 성별을 맞추면 약이 낫다.
  - *직접 표준화*: 비교하는 두 그룹에 같은 부분군 구성(가중치)을 씌워 다시 평균 내는 것.

### 4. 같은 숫자, 다른 정답 — 인과 이야기가 정한다

```text
  표 1.1 (부분군 = 성별)                  표 1.2 (부분군 = 복용 후 혈압, 숫자 배열 같음·열 제목 바뀜)

     성별 ──▶ 복용 여부                         복용 ──▶ 혈압 ──▶ 회복
       │         │                               │                ▲
       ▼         ▼                               └──── 독성 ───────┘
        회복 ◀────┘
  성별이 복용과 회복을 둘 다 정함 (교란)       혈압은 약이 회복에 이르는 길 (매개)
  → 부분군(성별별) 결과를 따른다              → 합계 결과를 따른다
```

- Primer 1.2절은 표 1.1과 **숫자 배열이 똑같은** 표 1.2를 보여 준다. 부분군 이름이 "복용 후 혈압"으로 바뀌고, "복용"·"미복용" 열 제목도 서로 바뀌었다. 그래서 표 1.2의 합계는 복용 289/350(83%), 미복용 273/350(78%)로 복용이 높다.
  - 약이 혈압을 낮춰서 회복을 돕는다면, 혈압으로 나누는 것은 약이 일하는 길을 막는 것이다. 이때는 합계가 맞다.
- *매개 변수(mediator)*: 원인이 결과에 이르는 중간 단계의 변수. 매개 변수로 층을 나누거나 조정하면 효과의 일부(또는 전부)를 지운다([03의 장애 시나리오 3](../03-observational-vs-experimental/2-summary.md)과 같은 함정).
- 결론(Primer 1.2절): 어느 표를 믿을지는 데이터 안에 없다. 변수가 처치 **전에** 정해졌는지, 처치의 **결과**인지 같은 인과 정보가 정한다.
  - 일반 원칙(OpenIntro 1.2.5): 연관은 인과를 뜻하지 않으며, 일반적으로 인과는 무작위 실험에서만 추론할 수 있다.

### 실험: 점진 배포가 만든 심슨의 역설

- 설정(모두 합성, 200,000명, seed 12): 기기 50:50. 모바일 기본 전환율 3%, PC 8%(예시). 새 화면의 진짜 효과는 +0.5%p. 점진 배포 때문에 새 화면 노출이 모바일 80%, PC 20%로 치우쳤다.

```python
mobile = rng.random() < 0.5
new_ui = rng.random() < (0.8 if mobile else 0.2)        # 배정이 기기에 따라 다름
conv = rng.random() < (0.03 if mobile else 0.08) + (0.005 if new_ui else 0.0)
```

```text
(B) 합성: 새 결제 화면 — 모바일 80%/PC 20% 노출, 진짜 효과 +0.5%p, 200,000명, seed 12
    전체  : 새 화면 4.53% (n=99884)  옛 화면 7.04% (n=100116)  차이 -2.50%
    모바일 : 새 화면 3.53% (n=79863)  옛 화면 2.96% (n=20077)  차이 +0.57%
    PC  : 새 화면 8.52% (n=20021)  옛 화면 8.06% (n=80039)  차이 +0.46%

(C) 같은 모집단, 배정만 무작위 50%: 새 화면 6.10%  옛 화면 5.47%  차이 +0.63%
```

- 기기별 차이(+0.57%p, +0.46%p)는 진짜 효과 +0.5%p 근처다. 전체 차이는 −2.50%p로 부호가 반대다.
- 원인: 새 화면 그룹의 80%가 전환율이 낮은 모바일이다. 기기가 "노출"과 "전환"을 둘 다 정했다(교란).
- 배정만 무작위로 바꾸면(C) 전체 차이가 +0.63%p로 진짜 효과 근처가 된다. 무작위 배정이 기기 → 노출 화살표를 끊는다. 0.13%p의 차이는 유한 표본의 우연 오차다(차이의 표준오차 약 0.1%p, 해석).

## 쓰이는 자료구조·알고리즘

- **피어슨 r**: 평균을 뺀 뒤 곱의 합. O(n). 큰 값의 합에서 상쇄 오차가 생길 수 있어 평균을 먼저 빼는 두 번 훑기 계산이 안정적이다([math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md)).
- **스피어만 r**: 정렬로 순위를 매기고(동점은 평균 순위) 피어슨 r. O(n log n). 정렬은 [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md).
- **층별 집계와 표준화**: `GROUP BY 부분군` 뒤 공통 가중치로 다시 평균. SQL의 `GROUPING SETS`로 전체와 부분군을 한 번에 낸다([database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md)).
- **인과 그림(DAG)**: 변수 = 꼭짓점, 직접 영향 = 방향 간선, 순환 없음. 그래프 기본은 [math/04-graph-theory-basics](../../math/04-graph-theory-basics/2-summary.md), 조정할 변수 고르기는 [data-analysis 25](../25-causal-inference-basics/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상 | 의심할 원리 | 확인 |
|---|---|---|
| 전체와 부분군의 방향이 반대 | 심슨의 역설(구성 차이) | 그룹별 부분군 구성비, 표준화 차이 |
| "X가 많은 곳에서 Y가 나쁘다 → X를 줄이자" | 교란·역인과 | X와 Y를 둘 다 늘리는 Z 후보 나열, Z로 층화·편상관 |
| r ≈ 0 → "관계 없음" | 비선형·이질 집단 | 산점도, 순위 상관, 구간별 평균 |
| r이 큼 → "강한 관계" | 이상값·집단 혼합 | 이상값 빼고 r, 순위 상관 |
| 층을 나누니 효과가 사라짐 | 매개 변수로 층화 | 그 변수가 처치 전에 정해졌나? |

### 2. SQL로 확인 — 전체와 부분군, 그리고 구성비 (PostgreSQL 17.11)

```sql
-- 전체와 기기별을 한 번에
SELECT coalesce(device, '(전체)') AS device,
       round(100.0 * avg(converted::int) FILTER (WHERE new_ui), 2)     AS new_pct,
       round(100.0 * avg(converted::int) FILTER (WHERE NOT new_ui), 2) AS old_pct,
       count(*) FILTER (WHERE new_ui) AS n_new, count(*) FILTER (WHERE NOT new_ui) AS n_old
FROM visit
GROUP BY GROUPING SETS ((device), ())
ORDER BY device NULLS FIRST;

-- 반전의 원인: 처리군과 대조군의 구성이 다르다
SELECT new_ui, round(100.0 * avg((device = 'mobile')::int), 1) AS mobile_share_pct
FROM visit GROUP BY new_ui ORDER BY new_ui DESC;

-- 기기 구성을 전체 비율로 맞춘 표준화 차이
WITH s AS (
  SELECT device,
         avg(converted::int) FILTER (WHERE new_ui)     AS p_new,
         avg(converted::int) FILTER (WHERE NOT new_ui) AS p_old,
         count(*)::numeric / sum(count(*)) OVER ()     AS w
  FROM visit GROUP BY device
)
SELECT round(100 * sum(w * p_new), 2) AS std_new_pct, round(100 * sum(w * p_old), 2) AS std_old_pct,
       round(100 * sum(w * (p_new - p_old)), 2) AS std_diff_pctpt
FROM s;
```

- 환경: `postgres:17` 컨테이너(PostgreSQL 17.11, `--network none`), `setseed(0.12)` 뒤 `random()`으로 실험 (B)와 같은 설정의 합성 데이터 200,000행. 코드 `e12_pg.sql`. 난수 생성기가 달라 Python 실험과 숫자는 조금 다르다.

```text
 device | new_pct | old_pct | n_new | n_old
--------+---------+---------+-------+--------
 (전체) |    4.45 |    6.94 | 99649 | 100351
 mobile |    3.45 |    2.99 | 79673 |  20162
 pc     |    8.43 |    7.94 | 19976 |  80189

 new_ui | mobile_share_pct
--------+------------------
 t      |             80.0
 f      |             20.1

 std_new_pct | std_old_pct | std_diff_pctpt
-------------+-------------+----------------
        5.94 |        5.46 |           0.48
```

- 구성비 표가 반전의 이유를 바로 보여 준다(모바일 비중 80.0% vs 20.1%). 표준화 차이 +0.48%p는 진짜 효과 +0.5%p 근처다.
- 표준화는 **잰 변수(기기)**만 맞춘다. 재지 않은 교란 변수가 남아 있으면 표준화 결과도 틀린다. 그래서 가능하면 무작위 배정(실험 C)으로 간다(A/B 설계는 [data-analysis 14](../14-ab-testing-design/2-summary.md)).

### 3. 인과를 말하기 전 체크리스트

1. 처치(X)는 누가·무엇이 정했나? 사람이 고르거나 배포 순서가 정했다면 관찰 데이터다.
2. X와 Y를 둘 다 늘릴 수 있는 변수(Z)를 적어 본다. 시간·트래픽·기기·사용자 등급이 흔한 후보다.
3. 그룹별 Z 구성비를 비교한다. 다르면 층화·표준화로 다시 본다.
4. 층을 나누는 변수가 X의 **결과**는 아닌지 확인한다(매개 변수면 나누지 않는다).
5. 결정이 비싸면 무작위 실험으로 확인한다.

## 장애 시나리오와 대처

### 1. 부분군별 추세와 전체 추세가 반대 → 잘못된 정책 결정 (⚠ 커리큘럼)

- 현상: 점진 배포한 새 결제 화면이 전체 전환율 −2.5%p로 보여 롤백했다.
- 보이는 형태: 대시보드 전체 행만 보면 하락. 기기별 행은 모두 상승(실험 B, SQL 출력).
- 원인: 노출이 모바일에 치우쳤고, 모바일은 원래 전환율이 낮다. 합계는 구성이 다른 가중 평균이다(심슨의 역설).
- 대처: 처리군·대조군의 구성비부터 본다. 기기로 표준화하거나 기기별로 판단한다. 다음 배포는 기기 안에서 무작위 배정(블록 무작위화)으로 한다.

### 2. 상관을 원인으로 읽고 엉뚱한 곳을 고침

- 현상: "캐시 미스가 많은 노드가 느리다(r ≈ 0.6)" → 캐시 메모리를 늘렸는데 지연이 그대로다.
- 보이는 형태: 미스 수와 지연의 산점도는 뚜렷한 우상향.
- 원인: 트래픽(Z)이 미스와 지연을 둘 다 늘렸다. 트래픽을 고정하면 상관이 거의 없다(실험 D: 0.635 → 편상관 0.021).
- 대처: Z 후보로 층화하거나 편상관을 본다. 원인이라고 의심하는 X만 바꾸는 실험(한 노드만 캐시 증설, 나머지 대조)으로 확인한다.

### 3. r ≈ 0을 보고 "관계 없음"으로 결론

- 현상: 배치 크기와 처리 시간의 r이 0.05라 배치 크기를 아무렇게나 정했다. 너무 작거나 너무 큰 배치에서 느려졌다.
- 보이는 형태: U자 모양의 산점도인데 상관계수 하나만 보고했다.
- 원인: r은 직선 관계만 잰다. U자·대칭 관계는 r ≈ 0(실험 E: y = x²에서 0.000).
- 대처: 산점도와 구간별 평균을 먼저 본다. 단조 관계면 순위 상관, 곡선이면 구간을 나눠 본다.

### 4. 이상값 하나가 만든 "강한 상관"

- 현상: 리포트가 "지표 A와 B의 상관 0.94"라며 A로 B를 관리하자고 제안했다.
- 보이는 형태: 점 30개는 흩어져 있고 오른쪽 위 끝에 점 하나가 떨어져 있다.
- 원인: 피어슨 r은 평균·표준편차 기반이라 극단값 하나에 크게 끌린다(실험 E: 0.046 → 0.944).
- 대처: 산점도 확인, 이상값 원인 조사(장애 시간대·로깅 오류인지), 순위 상관(0.121)과 함께 보고한다.

### 5. 매개 변수로 층을 나눠 효과를 지움

- 현상: "같은 장바구니 금액끼리 비교하면 추천 기능의 매출 효과가 0" → 기능 폐기.
- 보이는 형태: 층별 차이는 0 근처, 전체 차이는 양수.
- 원인: 추천 기능은 장바구니 금액을 키워서 매출을 올린다. 장바구니 금액이 매개 변수다. Primer 표 1.2처럼 이때는 합계가 맞다.
- 대처: 층화 변수는 처치 전에 정해진 것만 쓴다. 변수 사이의 화살표를 먼저 그린다(data-analysis 25).

## 핵심 문장

- 상관계수 r은 직선 관계의 강도만 잰다. r = 0은 "직선 관계 없음"이지 "관계 없음"이 아니고, 이상값 하나로 크게 바뀐다.
- 같은 상관을 인과·역인과·교란·선택·우연이 모두 만들 수 있다. 화살표 방향은 데이터에 없다.
- 심슨의 역설은 합계가 구성이 다른 부분군의 가중 평균이라서 생긴다. 그룹별 구성비를 먼저 본다.
- 부분군을 믿을지 합계를 믿을지는 숫자가 아니라 인과 이야기(교란 변수인가, 매개 변수인가)가 정한다.
- 잰 변수로 층화·표준화해도 재지 않은 교란은 남는다. 무작위 배정이 그 화살표를 끊는다.

## 관련 주제·근거

- 선행
  - [03-observational-vs-experimental](../03-observational-vs-experimental/2-summary.md) — 교란 변수 정의, 무작위 배정, 처치 후 변수 통제
  - [09-hypothesis-testing](../09-hypothesis-testing/2-summary.md) — 상관이 우연인지 따지는 틀
- 후속·연결
  - [13-linear-regression](../13-linear-regression/2-summary.md) — 기울기 = r·sy/sx, 결정계수 R² = r²
  - [11-multiple-comparisons](../11-multiple-comparisons/2-summary.md) — 부분군을 많이 쪼갤 때의 우연
  - [20-categorical-inference](../20-categorical-inference/2-summary.md) — 2×2 분할표와 독립성 검정
  - [06-exploratory-data-analysis](../06-exploratory-data-analysis/2-summary.md)(산점도 먼저) · [14-ab-testing-design](../14-ab-testing-design/2-summary.md)(무작위 배정) · [25-causal-inference-basics](../25-causal-inference-basics/2-summary.md)(인과 DAG·충돌 변수·조정 기준)
  - [data-analysis 27](../27-da-symptom-index/2-summary.md)(증상 색인 — 부분군 반전)
  - [math/07-probability-and-bayes](../../math/07-probability-and-bayes/2-summary.md) — 조건부 확률·조건부 독립, [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md) — 공분산
- 문헌
  - Pearl, Glymour, Jewell (2016) 『Causal Inference in Statistics: A Primer』 Wiley — 1장 공개 미리보기 <https://bayes.cs.ucla.edu/PRIMER/primer-ch1.pdf>: 1.2절 심슨의 역설, 표 1.1(성별)·표 1.2(복용 후 혈압, 같은 숫자), 운동–콜레스테롤 연속 예. 목차 <https://bayes.cs.ucla.edu/PRIMER/primer-toc.pdf>: 2.3 Colliders, 3.3 Backdoor Criterion(본문 미열람)
  - OpenIntro Statistics 4판 1.2.5(연관 ≠ 인과 상자), 1.3.4(교란 변수 정의), 8.1.4(상관계수 정의·식, 비선형 관계의 약한 r) <https://www.openintro.org/book/os/>
  - Python 3.12 `statistics.correlation`(3.10 추가, 3.12에서 `method='ranked'` 스피어만 추가)·`linear_regression` <https://docs.python.org/3.12/library/statistics.html>
  - PostgreSQL 17 7.2.4 GROUPING SETS <https://www.postgresql.org/docs/17/queries-table-expressions.html>, 4.2.7 Aggregate Expressions(`FILTER`) <https://www.postgresql.org/docs/17/sql-expressions.html>
- 실험 목록(모두 합성 데이터)
  - `e12_corr.py` (호스트 Python 3.12.3): (A) Primer 표 1.1 비율·성별 표준화, (B) 점진 배포 심슨의 역설(200,000명, seed 12), (C) 같은 모집단 무작위 배정(seed 12), (D) 교란 변수 상관·편상관·층 상관(n=5000, seed 3), (E) 비선형·이상값과 피어슨·스피어만(seed 9)
  - `e12_pg.sql` (postgres:17 컨테이너, PostgreSQL 17.11, `setseed(0.12)`): GROUPING SETS로 전체·기기별 전환율, 그룹별 구성비, 직접 표준화
