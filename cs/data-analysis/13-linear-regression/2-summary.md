# data-analysis/13-linear-regression — 최소제곱·잔차·결정계수·회귀 추론 — 정리 (힌트)

## 해결하는 문제

부하 테스트에서 이용률 10~60% 구간을 재고 직선을 그었다. R² = 0.95다. 이 직선으로 "이용률 90%일 때 응답 시간"을 예측해 용량을 정해도 될까?

```text
  응답 시간(서비스 시간 단위)
   20 │                                              ● 실제 (ρ=0.95)
      │
   10 │                                     ● 실제 (ρ=0.9)
      │
    5 │                          ● 실제 (ρ=0.8)
    3 │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ○ 직선 예측 3.10 (ρ=0.9)
    2 │          ●●●●●●●●●●●●  ← 잰 구간(ρ 0.1~0.6)에서는 직선이 잘 맞는다
    1 │ ●●●●
      └────────────────────────────────────────────── 이용률 ρ
        0.1                 0.6        0.8   0.9 0.95
```

- 회귀는 잰 범위 안에서 x와 y의 관계를 요약하는 직선을 준다. 잰 범위 밖은 보장하지 않는다.
- 직선이 잘 맞는지, 한 점에 끌려가지 않았는지, 기울기가 우연인지를 따로 확인해야 한다.

쉬운 예: 아이 키를 나이로 예측하는 직선을 3~10세 자료로 그렸다. 이 직선으로 40세 키를 예측하면 터무니없는 값이 나온다.

똑같은 구조다.\
대기열 지연은 이용률이 1에 가까워질수록 1/(1−ρ)로 폭증한다([math/10](../../math/10-queueing-and-littles-law/2-summary.md)). 낮은 구간의 직선은 이 곡선을 모른다.

실무 예:
- 요청 수 대비 비용·CPU를 직선으로 적합해 다음 분기 인프라 예산을 잡는다.
- 확장 실험의 처리량을 USL 식으로 바꿔 최소제곱으로 계수를 푼다([reliability/21](../../reliability/21-scaling-principles/2-summary.md)).
- 대시보드의 추세선이 "다음 달 디스크가 찬다"고 말한다.

## 동작·원리

### 1. 직선과 잔차

```text
   y │                ● ↑
     │              ／  │ 잔차 e = y − ŷ  (양수: 점이 선 위)
     │           ／ ●   ↓
     │        ／ ↑
     │   ● ／    │ 잔차 (음수: 점이 선 아래)
     │  ／●      ↓
     │／
     └──────────────────── x
       ŷ = b0 + b1·x     (b0 = 절편, b1 = 기울기)
```

- *반응 변수 y*: 예측하려는 값. *설명 변수 x*: 예측에 쓰는 값.
- *적합값 ŷ*: 직선이 x에서 내놓는 값.
- *잔차(residual)*: 관측값에서 적합값을 뺀 것. `e = y − ŷ`(OpenIntro 8.1.3).

### 2. 최소제곱 — 잔차 제곱합을 가장 작게

```text
  목표:  Σ (yi − b0 − b1·xi)²  을 최소로 하는 b0, b1

  해:    b1 = Sxy / Sxx = r · sy / sx          Sxx = Σ(xi − x̄)²,  Sxy = Σ(xi − x̄)(yi − ȳ)
         b0 = ȳ − b1 · x̄                      → 직선은 항상 (x̄, ȳ)를 지난다

  해의 성질(정규방정식):  Σ ei = 0,   Σ xi·ei = 0
```

- *최소제곱(least squares)*: 잔차 제곱합을 최소로 하는 직선을 고르는 기준(OpenIntro 8.2.2).
- 기울기 = 상관계수 × (y의 표준편차 / x의 표준편차), 직선은 (x̄, ȳ)를 지난다(OpenIntro 8.2.4). 상관계수는 [12](../12-correlation-vs-causation/2-summary.md).
- 선형대수로 보면, y 벡터를 (1, x) 두 열이 만드는 평면에 내린 그림자를 찾는 문제다. 잔차 벡터가 두 열과 직교(내적 0)하는 것이 위 정규방정식이다. 내적·직교는 [math/13](../../math/13-linear-algebra-essentials/2-summary.md).
- 왜 제곱인가: 큰 잔차에 더 큰 벌점을 준다. 대가로 멀리 떨어진 점 하나에 민감하다(5절).

### 실험: 직접 구현 vs `statistics.linear_regression` vs PostgreSQL `regr_*`

```python
def ols(x, y):
    n = len(x); mx, my = fmean(x), fmean(y)
    sxx = sum((xi - mx) ** 2 for xi in x)
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    b1 = sxy / sxx; b0 = my - b1 * mx
    res = [yi - (b0 + b1 * xi) for xi, yi in zip(x, y)]
    sse = sum(r * r for r in res); sst = sum((yi - my) ** 2 for yi in y)
    s = math.sqrt(sse / (n - 2))                      # 잔차 표준오차
    se_b1 = s / math.sqrt(sxx)
    lev = [1 / n + (xi - mx) ** 2 / sxx for xi in x]  # 레버리지
    return dict(b0=b0, b1=b1, r2=1 - sse / sst, s=s, se_b1=se_b1, t=b1 / se_b1, df=n - 2, res=res, lev=lev)
```

- 데이터(합성): 동시 요청 수 x ~ U(10, 100), 응답 시간 y = 20 + 0.8x + N(0, 8²), n = 200, seed 13. 환경: 호스트 Python 3.12.3. 코드 `e13_reg.py`.

```text
(B) 합성 y = 20 + 0.8x + N(0, 8²), n=200, seed 13
    직접 구현: b1=0.808062 b0=19.955791   statistics: slope=0.808062 intercept=19.955791
    R²=0.8805  corr²=0.8805  s=7.665  SE(b1)=0.0212  t=38.2  df=198
    b1 95% CI = (0.7663, 0.8498)
    잔차 합 = 7.89e-13, Σ x·잔차 = 4.54e-11   (정규방정식: 둘 다 0)
    거꾸로(x를 y로) 적합한 기울기 = 1.0896, 1/b1 = 1.2375, r²/b1 = 1.0896
```

- 같은 데이터를 PostgreSQL 17.11 `regr_*` 집계로 적합했다(`postgres:17` 컨테이너, `e13_pg.sql`).

```sql
SELECT regr_slope(y, x), regr_intercept(y, x), regr_r2(y, x), corr(y, x), regr_count(y, x),
       sqrt((regr_syy(y,x) - regr_slope(y,x)^2 * regr_sxx(y,x)) / (regr_count(y,x) - 2) / regr_sxx(y,x)) AS se_slope
FROM obs;
```

```text
  slope   | intercept |   r2   |   r    |  n  | se_slope
----------+-----------+--------+--------+-----+----------
 0.808062 | 19.955791 | 0.8805 | 0.9383 | 200 |   0.0212

 slope_x_on_y          ← regr_slope(x, y): 인자 순서를 바꾸면
--------------
       1.0896
```

- 세 방법의 기울기·절편이 소수 6자리까지 같다. 진짜 기울기 0.8이 95% 신뢰구간 (0.766, 0.850) 안에 있다.
- 잔차 합과 Σx·잔차가 부동소수 오차(10⁻¹¹) 수준의 0이다. 정규방정식이 성립한다.
- **x를 y로 적합한 기울기(1.0896)는 1/b1(1.2375)이 아니다.** r²/b1과 같다. |r| = 1일 때만 둘이 같다. PostgreSQL의 `regr_slope(Y, X)`는 첫 인자가 반응 변수다(9.21 표 9.61). 순서를 바꾸면 다른 직선이 나온다.

### 3. 결정계수 R² — 반응의 변동 중 직선이 설명한 몫

```text
  SST = Σ(yi − ȳ)²       전체 변동
  SSE = Σ ei²            직선이 못 설명한 변동
  R²  = 1 − SSE / SST    (설명 변수가 하나면 R² = r²)

  OpenIntro 8.2.7 Elmhurst:  s²(aid) ≈ 29.8백만,  s²(잔차) ≈ 22.4백만
                             (29.8 − 22.4) / 29.8 ≈ 0.25 = (−0.499)²
```

- *결정계수 R²*: 반응 변수의 변동 가운데 최소제곱선으로 설명되는 비율(OpenIntro 8.2.7). 0~1이다(절편이 있는 최소제곱일 때).
- 실험 (B)에서 R² = corr² = 0.8805로 같았다.
- R²가 높아도 직선이 맞는 모형이라는 보장은 없다(4절의 실험 E: R² 0.937인데 잔차가 U자).

### 4. 직선을 믿기 위한 조건 — 잔차를 본다

```text
  OpenIntro 8.2.3의 네 조건       잔차 그림에서 깨진 모양
  선형성                         잔차가 U자·∩자로 휜다
  잔차가 정규에 가까움              멀리 떨어진 잔차 몇 개(이상값)
                                 (영향점은 선을 끌어와 잔차가 작아 보일 수 있다 → 5절 레버리지·제외 재적합)
  일정한 산포                      x가 클수록 잔차 폭이 넓어진다(나팔 모양)
  관측 독립                        시간 순으로 잔차가 이어져 움직인다(시계열)

  잔차 그림(실험 E — 곡선에 직선을 적합)
   +5 │ ●●                                ●●
    0 │───●●───────────────────────────●●───
   −5 │      ●●●●●●●●●●●●●●●●●●●●●●●●●
      └──────────────────────────────────── x
```

### 실험: R²가 높아도 잔차가 말한다

- 데이터(합성): y = 0.05x² + N(0, 2²), x = 1..40. 직선 적합(seed 13에 이어서). 코드 `e13_reg.py` (E).

```text
(E) y = 0.05x² + 잡음(x=1..40) 직선 적합: R²=0.937
    x 구간별 평균 잔차: [1-10] +4.8 [11-20] -4.2 [21-30] -5.8 [31-40] +5.2
```

- R² 0.937로 "잘 맞는다"처럼 보이지만, 잔차가 양 끝에서 양수, 가운데서 음수다. 양 끝에서 체계적으로 과소 예측한다.
- 오른쪽 끝(x > 40)으로 갈수록 과소 예측이 커진다. 잔차의 휘어짐은 외삽이 위험하다는 신호다.

### 5. 이상값·레버리지·영향점

```text
   y │                                   ← 추세대로면 여기(340)
     │                     ●●●
     │              ●●●●●●       ╲ 원래 선(기울기 0.81)
     │       ●●●●●●            ─ ─ ─ ─ ─ 끌려간 선(기울기 0.47)
     │  ●●●●●
     │                                          ● (400, 100) 하나
     └──────────────────────────────────────────────── x
       10                 100                   400
```

- *레버리지(leverage)*: x가 점구름 중심에서 수평으로 멀수록 직선을 세게 당기는 정도(OpenIntro 8.3). 단순 회귀에서 `h_i = 1/n + (xi − x̄)² / Sxx`다. 모두 더하면 1 + Sxx/Sxx = 2(계수 개수)라서 평균은 2/n이다.
- *영향점(influential point)*: 레버리지가 높고 실제로 기울기를 크게 바꾼 점. 그 점을 빼고 적합하면 그 점이 선에서 아주 멀리 떨어진다(OpenIntro 8.3).
- OpenIntro는 이상값을 아주 좋은 이유 없이 지우지 말라고 한다. 예외적인 사례를 무시한 모형은 성능이 나쁠 수 있다.

### 실험: 같은 크기의 이탈, 다른 영향

```text
(C) x=400, y=100 점 하나 추가 (추세대로면 340)
    기울기 0.808 → 0.474, R² 0.880 → 0.572
    그 점의 레버리지 h=0.482 (평균 레버리지 2/n=0.0100), 나머지 최대 h=0.013
    그 점의 잔차 = -126.1 (적합선이 끌려와 잔차가 작아 보인다)
    같은 크기(-240)로 벗어난 점을 x=55(중앙)에 두면: 기울기 0.808 → 0.802, h=0.0051, 잔차 -239.2, R² 0.550
```

- 추세에서 240만큼 벗어난 점 하나가 x = 400(멀리)에 있으면 기울기가 0.808 → 0.474로 꺾인다. 레버리지 0.482는 평균의 48배다.
- 그 점의 잔차는 −126으로, 실제 이탈(−240)보다 작아 보인다. 직선이 그 점 쪽으로 끌려갔기 때문이다. **잔차만 보면 영향점을 놓친다.**
- 같은 이탈이 x 중앙(55)에 있으면 기울기는 거의 그대로다(0.802). R²는 둘 다 떨어진다. R²만으로는 두 경우를 구별하지 못한다.

### 6. 외삽 — 잰 범위 밖으로 선을 늘이기

- *외삽(extrapolation)*: 모형을 원래 데이터 범위 밖의 값에 적용하는 것. OpenIntro 8.2.6은 "믿을 수 없는 내기"라고 부른다.
- OpenIntro의 예: Elmhurst 장학금 직선 `aid = 24,319 − 0.0431 × 가구 소득`에 소득 100만 달러를 넣으면 −18,781달러(음수 장학금)가 나온다.

### 실험: 대기열 지연을 직선으로

- M/M/1 대기열의 평균 체류 시간을 서비스 시간 1 단위로 쓰면 W = 1/(1 − ρ)다([math/10](../../math/10-queueing-and-littles-law/2-summary.md)). ρ = 0.1~0.6의 11점(잡음 없음)에 직선을 적합했다.

```text
(D) 외삽: W=1/(1-ρ), ρ∈[0.1,0.6] 11점 직선 적합 R²=0.950
    ρ=0.6: 직선 예측 2.30  실제 2.50
    ρ=0.8: 직선 예측 2.83  실제 5.00
    ρ=0.9: 직선 예측 3.10  실제 10.00
    ρ=0.95: 직선 예측 3.23  실제 20.00
```

- 잰 구간 안에서도 R² 0.950이다. 그런데 ρ = 0.9에서 3배, 0.95에서 6배 넘게 과소 예측한다.
- 원인은 모양이다. 곡선 관계의 일부 구간만 보고 직선을 그렸다. 이론식(대기열·USL)이 있으면 그 식의 계수를 적합하고, 그래도 잰 범위 밖은 부하 테스트로 확인한다.

### 7. 회귀 추론 — 기울기가 우연인지

```text
  H0: β1 = 0 (x와 y에 직선 관계 없음)

  SE(b1) = s / √Sxx            s = √(SSE / (n − 2))   잔차 표준오차
  T = b1 / SE(b1)  ~  t 분포(df = n − 2)       ← 위 네 조건을 가정
  95% 신뢰구간:  b1 ± t*(df) × SE(b1)
```

- 자유도가 n − 2인 것은 계수 두 개(b0, b1)를 데이터로 추정했기 때문이다.
- OpenIntro 8.4 Elmhurst 출력(기울기 −0.0431, SE 0.0108, df 48)으로 직접 계산해 대조했다.

```text
(A) Elmhurst 요약 통계로: b1 = R·sy/sx = -0.0431, b0 = ȳ - b1·x̄ = 24328, R² = 0.249   (책: -0.0431, 24319, 0.25)
    기울기 t = -0.0431/0.0108 = -3.99, df=48, p = 0.0002; 95% CI = -0.0431 ± 2.01×0.0108 = (-0.0648, -0.0214)   (책: -3.98, 0.0002, (-0.0648, -0.0214))
    외삽: 소득 100만 달러 → -18,781 달러   (책: -18,781)
```

- t 분포 꼬리는 `dist.py`에서 정규화 불완전 베타 함수로 직접 계산했다(표준 라이브러리만). 계산법은 [21](../21-numerical-inference-t-anova/2-summary.md).
- b0 24328 vs 책 24319는 반올림된 요약 통계(R = −0.499 등)를, t −3.99 vs −3.98은 반올림된 기울기·표준오차(−0.0431, 0.0108)를 나눴기 때문이다(책은 원자료로 계산).
- OpenIntro 8.4의 주의: 소프트웨어는 방법이 적절한지(조건)를 검사하지 않는다. 조건 확인은 사람 몫이다.
- 기울기가 유의해도 인과는 아니다. 회귀 계수는 연관의 크기다([12](../12-correlation-vs-causation/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **최소제곱(선형대수)**: 정규방정식 `XᵀX b = Xᵀy`. 설명 변수 하나면 위의 닫힌 식 두 줄이다. 벡터·내적은 [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md). 여러 변수(다중 회귀)는 [data-analysis 22](../22-multiple-and-logistic-regression/2-summary.md).
- **누적 합(한 번 훑기)**: n·Σx·Σy·Σx²·Σxy만 모으면 기울기·절편을, Σy²까지 더하면 r도 구할 수 있다. 그래서 SQL 집계 `regr_*`가 행을 한 번만 읽고, 문서 표 9.61에서 부분 집계(Partial Mode, 병렬 집계)를 지원한다.
  - 주의: Σx²−(Σx)²/n 꼴은 값이 크고 분산이 작으면 파국적 상쇄가 생긴다. 평균을 먼저 빼는 계산(위 `ols`)이 안정적이다([math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md)).
- **레버리지 h_i**: 각 점이 자기 적합값에 주는 무게. 단순 회귀에서는 O(n)으로 모두 구한다.

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상 | 의심할 원리 | 확인 |
|---|---|---|
| 잰 범위 밖 예측이 실제와 크게 다름 | 외삽, 곡선 관계 | 예측 x가 데이터 범위 안인가, 잔차의 휘어짐 |
| 점 하나를 빼면 기울기가 크게 바뀜 | 레버리지·영향점 | h_i 상위 점, 그 점 제외 재적합 |
| R²는 높은데 끝에서 계속 틀림 | 비선형(잔차 패턴) | 구간별 평균 잔차, 잔차 그림 |
| SQL과 앱의 기울기가 다름 | `regr_slope` 인자 순서 | `regr_slope(Y, X)`인지 확인 |
| 시계열 회귀 기울기가 "매우 유의" | 관측 독립 위반 | 잔차를 시간 순으로 그려 이어지는지 |

### 2. 코드로 확인 — 잔차 진단 (Python 3.12)

```python
from statistics import linear_regression, fmean

slope, intercept = linear_regression(x, y)          # 3.10+, 표준 라이브러리 최소제곱
res = [yi - (slope * xi + intercept) for xi, yi in zip(x, y)]

# 1) 구간별 평균 잔차: 0 근처가 아니면 직선이 틀렸다
pairs = sorted(zip(x, res))
k = len(pairs) // 4
print([round(fmean(r for _, r in pairs[i * k:(i + 1) * k]), 2) for i in range(4)])

# 2) 레버리지 상위 점: 빼고 다시 적합해 기울기 변화를 본다
mx = fmean(x); sxx = sum((xi - mx) ** 2 for xi in x)
lev = [1 / len(x) + (xi - mx) ** 2 / sxx for xi in x]
top = max(range(len(x)), key=lev.__getitem__)
s2, _ = linear_regression(x[:top] + x[top + 1:], y[:top] + y[top + 1:])
print(f'h={lev[top]:.3f}, 기울기 {slope:.3f} → {s2:.3f}')

# 3) 예측하려는 x가 데이터 범위 안인가
assert min(x) <= x_new <= max(x), '외삽'
```

### 3. SQL로 확인 — PostgreSQL 17

```sql
-- 첫 인자가 반응 변수(Y), 둘째가 설명 변수(X)
SELECT regr_slope(latency_ms, concurrency)     AS slope,
       regr_intercept(latency_ms, concurrency) AS intercept,
       regr_r2(latency_ms, concurrency)        AS r2,
       min(concurrency) FILTER (WHERE latency_ms IS NOT NULL),   -- 예측 가능한 x 범위를 같이 기록
       max(concurrency) FILTER (WHERE latency_ms IS NOT NULL)    -- regr_*와 같은 행(두 열 모두 NOT NULL)만
FROM load_test_result;
```

- 범위(min·max)를 결과와 함께 저장해 두면, 나중에 범위 밖 예측을 막는 근거가 된다.
- `regr_*`는 두 입력이 모두 NULL이 아닌 행만 쓴다(PostgreSQL 17 9.21의 N 정의). 그래서 min·max에도 같은 조건을 건다.

### 4. 용량 계획에 쓸 때

1. 이론이 있으면(대기열·USL) 그 식을 선형으로 바꿔 계수를 적합한다([reliability/21](../../reliability/21-scaling-principles/2-summary.md)).
2. 예측하려는 부하 구간까지 실제로 부하 테스트한다([reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md)).
3. 기울기의 신뢰구간으로 불확실성을 같이 보고한다.

## 장애 시나리오와 대처

### 1. 외삽 → 용량 부족 (⚠ 커리큘럼)

- 현상: 이용률 60%까지 잰 직선으로 "90%에서도 응답 3배 이내"라 판단했다. 프로모션 날 응답 시간이 10배가 됐다.
- 보이는 형태: 계획서의 직선 예측(3.10)과 실측(10.00)이 이용률 0.9에서 3배 넘게 차이(실험 D).
- 원인: 지연은 1/(1−ρ)로 휘는데, 낮은 구간만 보고 직선을 그렸다. R² 0.95는 잰 구간 안의 적합도일 뿐이다.
- 대처: 예측 x를 데이터 범위 안으로 제한한다. 범위 밖이 필요하면 이론식을 적합하고 그 부하까지 테스트한다. 계획에 헤드룸을 둔다.

### 2. 이상값 레버리지로 기울기 왜곡 (⚠ 커리큘럼)

- 현상: 요청당 비용 회귀의 기울기가 지난달 0.81에서 0.47로 떨어져 "효율이 좋아졌다"고 보고했다.
- 보이는 형태: 데이터 200점 중 x가 혼자 400인 점 하나(장애 복구 중 재처리 폭주 등). 그 점의 잔차는 −126으로 크게 튀어 보이지 않는다(실험 C).
- 원인: x가 멀리 떨어진 점은 레버리지가 커서(h = 0.48) 직선을 자기 쪽으로 당긴다. 그래서 잔차가 작아 보인다.
- 대처: 레버리지 상위 점을 뽑아 빼고 다시 적합해 본다. 원인(장애·로깅 오류)을 확인한 뒤 제외 여부를 정하고, 제외했다면 보고서에 적는다.

### 3. 잔차 패턴 무시 (⚠ 커리큘럼)

- 현상: 디스크 사용량 추세선(R² 0.94)이 "6개월 뒤 80%"라 했는데 3개월 만에 찼다.
- 보이는 형태: 잔차가 처음과 최근에 양수, 중간에 음수(실험 E의 U자). 최근으로 올수록 실제가 선보다 위다.
- 원인: 증가가 가속하는 곡선인데 직선으로 요약했다. R²는 이 휘어짐을 숫자 하나에 묻는다.
- 대처: 구간별 평균 잔차·잔차 그림을 함께 본다. 휘어 있으면 변환(로그 등)이나 곡선 모형, 최근 구간만 쓴 적합을 비교한다. 시간 축 데이터는 [data-analysis 23](../23-time-series-basics/2-summary.md)(시계열).

### 4. `regr_slope` 인자 순서를 바꿈

- 현상: 앱(Python)의 기울기 0.81과 SQL 리포트의 기울기 1.09가 달라 어느 쪽이 맞는지 다툼이 났다.
- 보이는 형태: SQL이 `regr_slope(concurrency, latency_ms)`로 되어 있다.
- 원인: PostgreSQL `regr_slope(Y, X)`는 첫 인자가 반응 변수다. 바꾸면 "x를 y로 예측하는 직선"이 나오고, 그 기울기는 1/b1이 아니라 r²/b1이다(실험 B: 1.0896).
- 대처: 인자 순서를 `(Y, X)`로 고치고, 같은 데이터로 앱 결과와 대조하는 테스트를 둔다.

## 핵심 문장

- 최소제곱은 잔차 제곱합이 가장 작은 직선을 고른다. 기울기는 r·sy/sx이고, 직선은 (x̄, ȳ)를 지난다.
- R²는 반응 변동 중 직선이 설명한 몫이다. 높아도 잔차가 휘어 있으면 직선 모형이 틀렸다.
- x가 중심에서 먼 점은 레버리지가 커서 직선을 당긴다. 그래서 잔차만 보면 영향점을 놓친다.
- 회귀선은 잰 범위 안의 요약이다. 범위 밖 예측(외삽)은 곡선 관계에서 크게 틀린다.
- 기울기의 t 검정·신뢰구간(df = n − 2)은 선형성·정규 잔차·일정한 산포·독립을 가정한다. 소프트웨어는 그 조건을 검사해 주지 않는다.

## 관련 주제·근거

- 선행
  - [12-correlation-vs-causation](../12-correlation-vs-causation/2-summary.md) — 상관계수, 회귀 계수 ≠ 인과
  - [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md) — 벡터·내적(최소제곱의 직교 조건)
- 후속·연결
  - [21-numerical-inference-t-anova](../21-numerical-inference-t-anova/2-summary.md) — t 분포와 꼬리 확률 계산
  - [20-categorical-inference](../20-categorical-inference/2-summary.md) — 같은 방식의 카이제곱 꼬리 계산
  - [22-multiple-and-logistic-regression](../22-multiple-and-logistic-regression/2-summary.md)(다중·로지스틱 회귀) · [23-time-series-basics](../23-time-series-basics/2-summary.md)(시간 축 데이터)
  - [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md) — 1/(1−ρ) 곡선(외삽 실험)
  - [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) — 합 공식의 상쇄 오차
  - [reliability/21-scaling-principles](../../reliability/21-scaling-principles/2-summary.md) — USL 적합 = 최소제곱, [reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md)
- 문헌
  - OpenIntro Statistics 4판 8장: 8.1.3 잔차, 8.1.4 상관, 8.2.2 최소제곱 기준, 8.2.3 네 조건, 8.2.4 b1 = r·sy/sx와 (x̄, ȳ), 8.2.6 외삽(−18,781달러 예), 8.2.7 R²(29.8백만 → 22.4백만, 0.25), 8.3 레버리지·영향점, 8.4 회귀 추론(Elmhurst 출력 −0.0431·SE 0.0108·df 48·p 0.0002, 95% CI (−0.0648, −0.0214)) <https://www.openintro.org/book/os/>
  - Python 3.12 `statistics.linear_regression`(3.10 추가, 3.11 `proportional`)·`correlation` <https://docs.python.org/3.12/library/statistics.html>
  - PostgreSQL 17 9.21 Aggregate Functions — 표 9.61 Aggregate Functions for Statistics(`regr_slope(Y, X)`·`regr_intercept`·`regr_r2`·`regr_sxx`·`regr_syy`·`corr`, 부분 집계 지원) <https://www.postgresql.org/docs/17/functions-aggregate.html>
- 실험 목록(모두 합성 데이터, 책 대조는 공개 요약 통계)
  - `dist.py` + `e13_reg.py` (호스트 Python 3.12.3): (A) Elmhurst 요약 통계로 b0·b1·R²·t·p·CI·외삽 대조, (B) 직접 구현 vs `statistics.linear_regression`·정규방정식·역회귀 기울기(n=200, seed 13), (C) 레버리지(x=400 vs x=55), (D) 1/(1−ρ) 외삽, (E) 곡선 데이터의 잔차 패턴
  - `e13_pg.py` → `e13_pg.sql` (postgres:17 컨테이너, PostgreSQL 17.11): 같은 데이터의 `regr_*` 결과와 인자 순서를 바꾼 `regr_slope(x, y)`
