# python/python-data-science/13 — 시계열 분석 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 7월 트렌드는 `ma_12` 의 첫 번째 값과 같다

**출력**

```text
MA(12): [102.75, 103.59, 104.2, 104.44, 104.23]
```

```text
   7   104.66   102.75     0.28     1.63
   8    92.16   103.59   -10.82    -0.61
   9    85.59   104.20   -18.42    -0.19
  10    85.08   104.44   -19.75     0.39
  11    88.84   104.23   -17.04     1.65
```

**왜 그런가**

- `trend[6]` 은 `data[0:12]` 의 평균이고, `ma_12[0]` 도 `data[0:12]` 의 평균이다.
- 일반적으로 `trend[i] = ma_12[i - 6]` 이다 — 8월 103.59, 9월 104.20(=104.2) 도 그대로 이어진다.
- 슬라이스 `data[i-6:i+6]` 는 `i-6` ~ `i+5` 라서, 「가운데 정렬」이라도 실제 가운데는 `i - 0.5` 다(2-summary 「동작 방식 (4)」, 「어디서 틀리나 6」).

### 2. `ema[1]` 은 102.39

**출력**

```text
원본 (처음 5): [99.28, 109.64, 117.76, 125.01, 118.68]
```

```text
EMA(α=0.3): [99.28, 102.39, 107.0, 112.4, 114.28]
```

**왜 그런가**

- `ema[0]` 은 원본 첫 값 99.28 그대로다.
- `ema[1] = 0.3 × 109.64 + 0.7 × 99.28 = 32.892 + 69.496 = 102.388` → 반올림해 102.39 다.
- 원본이 10 이상 뛰었는데 EMA 는 3 남짓만 따라 올라갔다 — 새 값의 몫이 30% 뿐이기 때문이다(2-summary 「동작 방식 (3)」).

### 3. 가장 작은 것은 `lag=6`, `lag=12` 는 그보다 훨씬 크다

**출력**

```text
  lag= 1:  0.8974 +██████████████████████████
  lag= 2:  0.7479 +██████████████████████
  lag= 3:  0.5520 +████████████████
  lag= 6:  0.1560 +████
  lag=12:  0.7451 +██████████████████████
  lag=24:  0.5221 +███████████████
```

**왜 그런가**

- `lag=6` 은 반 주기라 여름과 겨울이 짝지어진다 — 계절성끼리는 반대로 움직여 음의 상관을 만든다.
- 그런데 트렌드가 모든 lag 에 양의 상관을 얹으므로 둘이 맞서 0.1560 처럼 작은 양수가 된다(원본에 근거 없음 — 추론).
- `lag=12` 는 같은 달끼리 짝지어져 계절성이 같은 방향으로 움직이므로 0.7451 로 높다.
- `lag=1~3` 은 가까운 시점이라 크고, lag 가 커질수록 작아진다(2-summary 「동작 방식 (5)」).

### 4. 인덱스 0~5 와 114~119 가 `None` 이다

- 트렌드 루프가 `range(half, n - half)` = `range(6, 114)` 라서 앞 6칸(0~5)과 뒤 6칸(114~119)은 `[None] * n` 의 초깃값이 남는다.
- `seasonal` 은 `seasonal_avg[i % period]` 로 120칸을 **모두** 채우므로 그 자리에도 값이 있다.
- `residual` 은 `trend[i] is not None` 일 때만 구하므로 트렌드와 같은 자리에서 `None` 이다.
- 그래서 분해 표는 첫 유효 인덱스 6, 즉 7월부터 찍는다.

근거: 2-summary 「동작 방식 (4)」의 1 · 3 · 4단계.

### 5. 값이 있는데도 `N/A` 로 찍힌다

- `f"{residual[i]:.2f}" if residual[i] else "N/A"` 는 진리값으로 가른다.
- 파이썬에서는 `None` 뿐 아니라 `0.0` 도 거짓이다.
- 그러므로 잔차가 정확히 `0.0` 인 달은 계산된 값이 있는데도 `N/A` 로 찍힌다.
- `is not None` 으로 `None` 만 걸러야 바르게 찍힌다.

근거: 2-summary 「어디서 틀리나 5」, 「구현 세부사항 대 언어 보장」의 진리값 행.

### 6. 창이 크면 길이와 반응 속도를 잃고, α 가 크면 새 값의 몫이 커진다

- 창을 키우면 더 많은 값을 섞어 노이즈가 서로 상쇄되므로 부드러워진다.
- 대가로 결과가 `window - 1` 개 짧아지고, 갑작스러운 변화가 평균 속에 묻혀 늦게 나타난다.
- EMA 는 `α · 새 값 + (1 − α) · 직전 EMA` 다.
- α 가 크면 새 값이 차지하는 몫이 커지고 과거 평균의 몫은 작아지므로 원본 변화에 빨리 따라붙는다.

근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 7. 세 겹 따옴표 문자열을 `print` 한 것이라서

- ARIMA 절 전체가 `print("""...""")` 의 문자열 안에 들어 있다.
- 파이썬은 문자열 안의 글을 코드로 해석하지 않으므로 `import` 줄도 글자로 찍힐 뿐이다.
- 그래서 `statsmodels` · `pmdarima` 가 없어도 이 절은 오류 없이 지나가고, 출력에는 결과 대신 코드 글자가 그대로 나온다.
- 실제로 돌리려면 그 코드를 떼어 내고 두 패키지와 `data` 를 마련해야 한다.

근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 8」.

### 8. ARIMA 는 정상 시계열을 전제로 하고, 이 데이터는 트렌드가 정상성을 깬다

- 원본 팁대로 ARIMA 를 적용하기 전에 반드시 정상성을 확인해야 한다.
- ARIMA 의 `d` 는 「비정상 → 정상」으로 바꾸는 차분 횟수라서, 정상인지 먼저 알아야 `d` 를 정할 수 있다.
- ADF 검정에서 p < 0.05 면 정상으로 보고, 아니면 `d=1` 차분을 적용한다.
- 이 데이터에서 정상성을 깨는 것은 `100 + 0.5 * t` 트렌드다 — 평균이 시간에 따라 오른다.
- 한 번 차분하면 매달 0.5 오르는 몫이 거의 일정한 값이 된다.

근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 2」.

### 9. `20 * sin(2π t / 12)` 를 되찾은 것이고, 합이 0 이 아닌 것은 정규화가 없고 트렌드 창이 반 칸 치우쳐서다

- 생성 함수의 계절성은 t=0..11 에서 0, 10, 17.3, 20, 17.3, 10, 0, −10, −17.3, −20, −17.3, −10 이다(손 계산).
- 분해 결과는 0.95, 8.9, 18.15, 17.9, 19.26, 10.13, 0.28, −10.82, −18.42, −19.75, −17.04, −6.62 로 모양과 크기가 거의 같다.
- 차이는 노이즈가 같은 달끼리 평균해도 다 사라지지 않은 몫이다.
- 12개 합은 2.92 다 — 이 코드는 계절성 합을 0 으로 맞추는 단계가 없다.
- 게다가 트렌드 창의 가운데가 `i − 0.5` 라 트렌드가 약 0.25 낮게 잡히고, 그 몫이 달마다 계절성으로 넘어가 12달이면 약 3 이 된다(원본에 근거 없음 — 추론).

근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」, 「어디서 틀리나 6 · 7」.

### 10. `SARIMAX` 의 `seasonal_order` 의 `s=12` 와 `auto_arima` 의 `m=12`

- `lag=12` 에서 자기상관이 높다는 것은 12개월 주기 계절성이 있다는 단서다.
- 계절성이 있으면 SARIMA 를 쓰고, `seasonal_order=(P, D, Q, s)` 의 `s` 에 12 를 넣는다.
- `auto_arima` 로 차수를 자동 선택할 때는 `seasonal=True, m=12` 로 같은 주기를 알려 준다.
- 워크플로우 4단계의 「ACF/PACF 로 p, q 결정」도 같은 그래프를 읽는 일이다.

근거: 2-summary 「동작 방식 (5) · (6)」, 「어디서 틀리나 3 · 4」.

## 실습 정답

### 실습 1. 합성 월별 시계열을 만들고 이동 평균 · 분해 · 자기상관으로 들여다보기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 시드 고정 | `random.seed(42)` |
| 2. 트렌드 + 계절성 + 노이즈 합성 | `generate_time_series` 의 `trend` · `seasonal` · `noise` · `data.append(round(..., 2))` |
| 3. 기본 정보 출력 | `len(data)` · `data[:12]` · `min(data)` · `max(data)` 를 찍는 `print` |
| 4. 단순 이동 평균 | `moving_average` 의 `range(len(data) - window + 1)` · `sum(data[i:i+window]) / window` |
| 5. 지수 이동 평균 | `exponential_moving_average` 의 `result = [data[0]]` · `alpha * data[i] + (1 - alpha) * result[-1]` |
| 6. 처음 5개 비교 출력 | `ma_3` · `ma_12` · `ema` 와 그 아래 `print` 여섯 줄 |
| 7. 트렌드 | `decompose_additive` 의 `trend = [None] * n` · `range(half, n - half)` · `data[i-half:i+half]` |
| 8. 트렌드 제거 · 계절성 | `detrended` · `range(m, n, period)` · `if values else 0` · `seasonal_avg[i % period]` |
| 9. 잔차 · 반환 | `residual[i] = round(data[i] - trend[i] - seasonal[i], 2)` · `return trend, seasonal, residual` |
| 10. 분해 표 · 계절성 패턴 | `for i in range(6, 18)` 의 `if trend[i] else "N/A"` · `seasonal[:12]` 출력 |
| 11. 자기상관 | `autocorrelation` 의 `mean` · `var` · `if var == 0` · `range(n - lag)` · `round(cov / var, 4)` |
| 12. ACF 막대 출력 | `for lag in [1, 2, 3, 6, 12, 24]` 의 `'█' * int(abs(acf) * 30)` · `sign` |
| 13. ARIMA 개념 문자열 | `print("""...""")` (안에 `adfuller` · `ARIMA` · `forecast` · `SARIMAX` · `auto_arima`) |
| 14. 워크플로우 7단계 | `=== 시계열 분석 워크플로우 ===` 아래 `print` 일곱 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/time-series.py`

```python
# [데이터 과학 & 수학] 시계열 분석
# 설명: 시계열 기본, 이동 평균, 분해, ARIMA 개념
# 팁: 이동 평균은 트렌드 추출과 노이즈 제거에 기본이다. ARIMA 적용 전 반드시 정상성을 확인해야 한다. 계절성이 있으면 SARIMA를 사용한다. auto_arima(pmdarima)로 최적 파라미터를 자동 선택할 수 있다.

# 시계열 분석 기본
# 난수 생성용
import random
# 수학 함수(sin, pi)용
import math
# (현재 코드에서 직접 사용하진 않지만 슬라이딩 윈도우 등 시계열 처리에 유용)
from collections import deque

# 재현 가능성을 위해 시드 고정
random.seed(42)

# 합성 시계열을 생성하여 분석 기법 시연
print("=== 시계열 데이터 생성 ===")
# 트렌드 + 계절성 + 노이즈 합성으로 실제 시계열을 모방
def generate_time_series(n=120):
    """월별 데이터 생성 (10년치)"""
    # 결과 시계열을 담을 리스트
    data = []
    for t in range(n):
        # 시간에 비례하는 선형 트렌드 (월별 +0.5)
        trend = 100 + 0.5 * t            # 상승 트렌드
        # 12개월 주기의 사인파 계절성
        seasonal = 20 * math.sin(2 * math.pi * t / 12)  # 12개월 주기
        # 가우시안 노이즈
        noise = random.gauss(0, 5)        # 노이즈
        # 가법 모형: trend + seasonal + noise
        data.append(round(trend + seasonal + noise, 2))
    return data

# 120개월(10년) 데이터 생성
data = generate_time_series(120)
# 기본 정보 출력
print(f"데이터 수: {len(data)}")
# 첫 1년치 미리보기
print(f"처음 12개 (1년): {data[:12]}")
# 전체 범위
print(f"최솟값: {min(data):.2f}, 최댓값: {max(data):.2f}")

# 줄바꿈 출력
print()
# 이동 평균: 단순 MA와 지수 MA로 트렌드 추출
print("=== 이동 평균 (Moving Average) ===")
def moving_average(data, window):
    """단순 이동 평균"""
    # 결과 저장 리스트
    result = []
    # 슬라이딩 윈도우로 평균 계산
    for i in range(len(data) - window + 1):
        # 현재 윈도우의 합/창 크기
        avg = sum(data[i:i+window]) / window
        result.append(round(avg, 2))
    return result

def exponential_moving_average(data, alpha=0.3):
    """지수 이동 평균: 최근 값에 더 큰 가중치"""
    # 첫 값은 원본 그대로 사용
    result = [data[0]]
    # 점화식: EMA_t = α * x_t + (1-α) * EMA_{t-1}
    for i in range(1, len(data)):
        ema = alpha * data[i] + (1 - alpha) * result[-1]
        result.append(round(ema, 2))
    return result

# 윈도우 3개월 단순 이동평균
ma_3 = moving_average(data, 3)
# 윈도우 12개월 - 계절성 제거 효과
ma_12 = moving_average(data, 12)
# 지수 이동평균 (최근 데이터 가중치 큼)
ema = exponential_moving_average(data, alpha=0.3)

# 처음 5개 비교 출력
print(f"원본 (처음 5): {data[:5]}")
print(f"MA(3): {ma_3[:5]}")
print(f"MA(12): {ma_12[:5]}")
print(f"EMA(α=0.3): {ema[:5]}")
# 윈도우 크기와 알파 값의 효과 설명
print("MA 창이 클수록 더 부드러움 (노이즈 제거)")
print("EMA는 최근 데이터에 더 반응 (α↑ → 더 민감)")

# 줄바꿈 출력
print()
# 시계열 분해: 가법 모형 Y = T + S + R
print("=== 시계열 분해 (Decomposition) ===")
def decompose_additive(data, period=12):
    """가법 분해: Y = Trend + Seasonal + Residual"""
    # 시계열 길이
    n = len(data)

    # 1. 트렌드 (이동 평균)
    # 가운데 정렬 이동평균을 위해 None으로 초기화
    trend = [None] * n
    # 양쪽 절반 길이
    half = period // 2
    # 가장자리는 트렌드 계산 불가 → None 유지
    for i in range(half, n - half):
        trend[i] = sum(data[i-half:i+half]) / period

    # 2. 계절성 제거된 데이터
    # 트렌드를 뺀 잔여 (계절성 + 잔차)
    detrended = [None] * n
    for i in range(n):
        if trend[i] is not None:
            detrended[i] = data[i] - trend[i]

    # 3. 계절성 패턴 (주기별 평균)
    # 같은 월(예: 1월)들을 모아 평균 → 계절성 추정
    seasonal_avg = []
    for m in range(period):
        # m, m+period, m+2*period, ... 위치의 detrended 값
        values = [detrended[i] for i in range(m, n, period)
                  if detrended[i] is not None]
        # 빈 리스트 방어 처리
        seasonal_avg.append(sum(values) / len(values) if values else 0)

    # 주기를 따라 계절성 시퀀스 확장
    seasonal = [round(seasonal_avg[i % period], 2) for i in range(n)]

    # 4. 잔차
    # 잔차 = 원본 - 트렌드 - 계절성
    residual = [None] * n
    for i in range(n):
        if trend[i] is not None:
            residual[i] = round(data[i] - trend[i] - seasonal[i], 2)

    return trend, seasonal, residual

# 분해 수행 (12개월 주기)
trend, seasonal, residual = decompose_additive(data, period=12)

# 표 형태로 일부 구간 결과 확인
print("분해 결과 (월 7~18):")
print(f"{'월':>4} {'원본':>8} {'트렌드':>8} {'계절성':>8} {'잔차':>8}")
# 6~17 인덱스 (7~18월) 출력
for i in range(6, 18):
    # None 처리: 가장자리 트렌드/잔차는 표시 불가
    t = f"{trend[i]:.2f}" if trend[i] else "N/A"
    r = f"{residual[i]:.2f}" if residual[i] else "N/A"
    print(f"{i+1:>4} {data[i]:>8.2f} {t:>8} {seasonal[i]:>8.2f} {r:>8}")

# 12개월 계절성 패턴 확인
print(f"\n계절성 패턴 (12개월): {seasonal[:12]}")
print("양수 = 평균 이상, 음수 = 평균 이하")

# 줄바꿈 출력
print()
# 자기상관: 시계열이 자신의 과거 값과 얼마나 상관되는지
print("=== 자기상관 (Autocorrelation) ===")
def autocorrelation(data, lag):
    """lag 시점의 자기상관계수"""
    # 길이
    n = len(data)
    # 평균
    mean = sum(data) / n
    # 분산 (모분산 N으로 나눔)
    var = sum((x - mean) ** 2 for x in data) / n
    # 0 분산 방어 처리
    if var == 0:
        return 0
    # lag 만큼 떨어진 값과의 공분산
    cov = sum((data[i] - mean) * (data[i + lag] - mean)
              for i in range(n - lag)) / n
    # 자기상관 = 공분산 / 분산
    return round(cov / var, 4)

# 다양한 lag에서 ACF 시각화 (텍스트 막대)
print("자기상관 (ACF):")
for lag in [1, 2, 3, 6, 12, 24]:
    acf = autocorrelation(data, lag)
    # 절댓값 비례 막대 길이
    bar = '█' * int(abs(acf) * 30)
    # 부호 표시
    sign = '+' if acf >= 0 else '-'
    print(f"  lag={lag:>2}: {acf:>7.4f} {sign}{bar}")
# 12에서 큰 양의 ACF → 12개월 주기 계절성 존재
print("lag=12에서 높은 상관 → 12개월 주기 계절성 확인")

# 줄바꿈 출력
print()
# ARIMA: AR(p) + I(d) + MA(q) 차수의 의미
print("=== ARIMA 개념 ===")
# statsmodels/pmdarima로 정상성 검정과 모델 피팅 흐름 안내
print("""
# ARIMA(p, d, q) - AutoRegressive Integrated Moving Average
# pip install statsmodels

# p: AR (자기회귀) 차수 - 과거 p개 시점의 값에 의존
# d: I (차분) 횟수 - 비정상 → 정상 시계열 변환
# q: MA (이동평균) 차수 - 과거 q개 오차에 의존

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import pandas as pd
import numpy as np

# 1. 정상성 검정 (ADF Test)
result = adfuller(data)
print(f"ADF 통계량: {result[0]:.4f}")
print(f"p-값: {result[1]:.4f}")
print(f"정상성: {'정상' if result[1] < 0.05 else '비정상 (차분 필요)'}")

# 2. ARIMA 모델 피팅
model = ARIMA(data, order=(1, 1, 1))  # ARIMA(1,1,1)
fitted = model.fit()
print(fitted.summary())

# 3. 예측
forecast = fitted.forecast(steps=12)  # 12개월 예측
print(f"예측값: {forecast}")

# 4. SARIMA (계절성 포함)
from statsmodels.tsa.statespace.sarimax import SARIMAX

model = SARIMAX(
    data,
    order=(1, 1, 1),              # ARIMA
    seasonal_order=(1, 1, 1, 12)  # 계절성 (P,D,Q,s)
)
fitted = model.fit(disp=False)
forecast = fitted.forecast(steps=12)

# 5. auto_arima로 자동 파라미터 선택
# pip install pmdarima
from pmdarima import auto_arima
best_model = auto_arima(
    data, seasonal=True, m=12,
    suppress_warnings=True
)
print(f"최적 모델: {best_model.order}, 계절: {best_model.seasonal_order}")
""")

# 줄바꿈 출력
print()
# 시계열 분석 표준 워크플로우 정리
print("=== 시계열 분석 워크플로우 ===")
# 1. 데이터 시각화로 패턴 파악
print("1. 시각화: 트렌드, 계절성, 이상치 확인")
# 2. 정상성 검정
print("2. 정상성 검정: ADF test (p<0.05면 정상)")
# 3. 차분으로 정상화
print("3. 차분: 비정상이면 d=1 차분 적용")
# 4. ACF/PACF 그래프로 차수 결정
print("4. ACF/PACF: p, q 파라미터 결정")
# 5. 모델 학습
print("5. 모델 피팅: ARIMA 또는 SARIMA")
# 6. 잔차 분석으로 적합도 평가
print("6. 진단: 잔차 분석 (정규성, 자기상관 없음)")
# 7. 예측 수행
print("7. 예측: forecast()로 미래 값 예측")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 시계열 데이터 생성 ===
데이터 수: 120
처음 12개 (1년): [99.28, 109.64, 117.76, 125.01, 118.68, 105.01, 104.66, 92.16, 85.59, 85.08, 88.84, 101.32]
최솟값: 83.23, 최댓값: 176.09

=== 이동 평균 (Moving Average) ===
원본 (처음 5): [99.28, 109.64, 117.76, 125.01, 118.68]
MA(3): [108.89, 117.47, 120.48, 116.23, 109.45]
MA(12): [102.75, 103.59, 104.2, 104.44, 104.23]
EMA(α=0.3): [99.28, 102.39, 107.0, 112.4, 114.28]
MA 창이 클수록 더 부드러움 (노이즈 제거)
EMA는 최근 데이터에 더 반응 (α↑ → 더 민감)

=== 시계열 분해 (Decomposition) ===
분해 결과 (월 7~18):
   월       원본      트렌드      계절성       잔차
   7   104.66   102.75     0.28     1.63
   8    92.16   103.59   -10.82    -0.61
   9    85.59   104.20   -18.42    -0.19
  10    85.08   104.44   -19.75     0.39
  11    88.84   104.23   -17.04     1.65
  12   101.32   104.88    -6.62     3.06
  13   109.28   106.55     0.95     1.78
  14   117.05   106.93     8.90     1.22
  15   120.63   107.50    18.15    -5.02
  16   122.43   108.31    17.90    -3.78
  17   126.55   108.16    19.26    -0.87
  18   125.06   108.43    10.13     6.50

계절성 패턴 (12개월): [0.95, 8.9, 18.15, 17.9, 19.26, 10.13, 0.28, -10.82, -18.42, -19.75, -17.04, -6.62]
양수 = 평균 이상, 음수 = 평균 이하

=== 자기상관 (Autocorrelation) ===
자기상관 (ACF):
  lag= 1:  0.8974 +██████████████████████████
  lag= 2:  0.7479 +██████████████████████
  lag= 3:  0.5520 +████████████████
  lag= 6:  0.1560 +████
  lag=12:  0.7451 +██████████████████████
  lag=24:  0.5221 +███████████████
lag=12에서 높은 상관 → 12개월 주기 계절성 확인

=== ARIMA 개념 ===

# ARIMA(p, d, q) - AutoRegressive Integrated Moving Average
# pip install statsmodels

# p: AR (자기회귀) 차수 - 과거 p개 시점의 값에 의존
# d: I (차분) 횟수 - 비정상 → 정상 시계열 변환
# q: MA (이동평균) 차수 - 과거 q개 오차에 의존

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import pandas as pd
import numpy as np

# 1. 정상성 검정 (ADF Test)
result = adfuller(data)
print(f"ADF 통계량: {result[0]:.4f}")
print(f"p-값: {result[1]:.4f}")
print(f"정상성: {'정상' if result[1] < 0.05 else '비정상 (차분 필요)'}")

# 2. ARIMA 모델 피팅
model = ARIMA(data, order=(1, 1, 1))  # ARIMA(1,1,1)
fitted = model.fit()
print(fitted.summary())

# 3. 예측
forecast = fitted.forecast(steps=12)  # 12개월 예측
print(f"예측값: {forecast}")

# 4. SARIMA (계절성 포함)
from statsmodels.tsa.statespace.sarimax import SARIMAX

model = SARIMAX(
    data,
    order=(1, 1, 1),              # ARIMA
    seasonal_order=(1, 1, 1, 12)  # 계절성 (P,D,Q,s)
)
fitted = model.fit(disp=False)
forecast = fitted.forecast(steps=12)

# 5. auto_arima로 자동 파라미터 선택
# pip install pmdarima
from pmdarima import auto_arima
best_model = auto_arima(
    data, seasonal=True, m=12,
    suppress_warnings=True
)
print(f"최적 모델: {best_model.order}, 계절: {best_model.seasonal_order}")


=== 시계열 분석 워크플로우 ===
1. 시각화: 트렌드, 계절성, 이상치 확인
2. 정상성 검정: ADF test (p<0.05면 정상)
3. 차분: 비정상이면 d=1 차분 적용
4. ACF/PACF: p, q 파라미터 결정
5. 모델 피팅: ARIMA 또는 SARIMA
6. 진단: 잔차 분석 (정규성, 자기상관 없음)
7. 예측: forecast()로 미래 값 예측
````

**풀이 요점**

- 데이터는 가법 모형으로 만들었으므로 가법 분해로 거의 그대로 되찾을 수 있다.
- 이동 평균의 핵심은 슬라이스 `data[i:i+window]` 와 창 시작점의 범위 `len(data) - window + 1` 이다.
- 분해의 트렌드 창 `data[i-half:i+half]` 는 정확히 12개지만 가운데가 반 칸 앞이라, `trend[i]` 가 `ma_12[i-6]` 과 같아진다.
- 계산할 수 없는 자리는 `None` 으로 두고 확인한 뒤 쓴다 — 표에서 `if trend[i]` 로 가르면 `0.0` 도 `N/A` 가 되는 함정이 있다.
- 자기상관은 `lag=12` 에서 튀어 12개월 주기를 드러내고, 이것이 SARIMA 의 `s=12` · `auto_arima` 의 `m=12` 로 이어진다.
- ARIMA 절은 문자열 출력이라 외부 패키지 없이 돌아간다 — 실제 모델링은 그 코드를 떼어 내 따로 실행해야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
