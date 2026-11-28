# python/python-data-science/13 — 시계열 분석 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 분해의 트렌드와 MA(12) 를 나란히 놓으면 (예측)

```python
# 질문용 발췌
ma_12 = moving_average(data, 12)       # ma_12[i] = mean(data[i : i+12])

half = 12 // 2
for i in range(half, n - half):
    trend[i] = sum(data[i-half:i+half]) / 12
```

- 분해 표 7월(인덱스 6)의 트렌드 값은 `ma_12` 리스트의 몇 번째 값과 같은가?

### 2. α=0.3 인 EMA 의 두 번째 값 (예측)

```python
# 질문용 발췌
# data[:2] 는 [99.28, 109.64] 다
ema = exponential_moving_average(data, alpha=0.3)
```

- `ema[1]` 은 소수 둘째 자리까지 얼마인가?

### 3. 여섯 lag 의 자기상관을 크기순으로 놓으면 (예측)

- lag 1 · 2 · 3 · 6 · 12 · 24 중 자기상관이 가장 작은 것은 어느 lag 인가?
- `lag=12` 의 값은 `lag=6` 보다 큰가 작은가?

### 4. 트렌드가 `None` 으로 남는 자리 (경계)

- 120개 데이터에서 `trend[i]` 가 `None` 인 인덱스는 어디어디인가?
- 그 자리에서 `seasonal` 과 `residual` 은 각각 값이 있는가?

### 5. `if residual[i]` 로 `N/A` 를 가르면 (경계)

- 잔차가 반올림해서 정확히 `0.0` 이 된 달은 표에 어떻게 찍히나?

### 6. 창 크기와 α 가 매끄러움을 바꾸는 이유 (왜)

- 단순 이동 평균의 창을 키우면 선이 부드러워지는 대신 무엇을 잃는가?
- α 를 키우면 EMA 가 원본 변화에 더 빨리 따라붙는 까닭은 무엇인가?

### 7. ARIMA 절의 `import statsmodels` 가 실행되지 않는 까닭 (왜)

- ARIMA 절에 적힌 `from statsmodels... import ARIMA` 줄이 실제 import 로 실행되지 않는 까닭은 무엇인가?

### 8. ARIMA 앞에 정상성 검정을 두는 까닭 (왜)

- ARIMA 를 맞추기 전에 ADF 검정을 하고, 비정상이면 차분을 하는 까닭은 무엇인가?
- 이 항목의 합성 데이터에서 정상성을 깨는 성분은 무엇인가?

### 9. 분해로 얻은 계절성과 생성 함수 (연결)

- 계절성 패턴 12개 값은 `generate_time_series` 의 어느 항을 되찾은 것인가?
- 그 12개 값을 더해도 0 이 되지 않는 까닭은 무엇인가?

### 10. `lag=12` 의 높은 자기상관과 SARIMA (연결)

- ACF 에서 `lag=12` 가 높게 나온 사실은 `SARIMAX` 와 `auto_arima` 의 어느 인자에 반영되나?

## 실습

### 실습 1. 합성 월별 시계열을 만들고 이동 평균 · 분해 · 자기상관으로 들여다보기

**만들 것** — 트렌드 + 계절성 + 노이즈로 120개월 시계열을 만들고, 이동 평균 · 가법 분해 · 자기상관을 표준 라이브러리만으로 구현해 결과를 찍는다. 끝에 ARIMA 개념과 분석 워크플로우를 글로 찍는다.

**준비물** — 표준 라이브러리(`random` · `math` · `collections`)만 있으면 된다. ARIMA 절의 `statsmodels` · `pmdarima` 코드는 실행하지 않고 문자열로 찍기만 하므로 설치하지 않아도 된다.

**요구 조건**

1단계 — 데이터 생성

1. `random.seed(42)` 로 시드를 고정한다.
2. `generate_time_series(n=120)` 은 각 `t` 마다 트렌드 `100 + 0.5 * t`, 계절성 `20 * sin(2π t / 12)`, 노이즈 `random.gauss(0, 5)` 를 더해 소수 둘째 자리로 반올림한 값을 리스트에 넣어 돌려준다.
3. 데이터 수, 처음 12개, 최솟값 · 최댓값을 찍는다.

2단계 — 이동 평균

4. `moving_average(data, window)` 는 창 시작점 `i` 마다 `data[i:i+window]` 의 평균을 반올림해 담고, 길이 `len(data) - window + 1` 의 리스트를 돌려준다.
5. `exponential_moving_average(data, alpha=0.3)` 는 첫 값을 그대로 두고, 다음부터 `alpha * data[i] + (1 - alpha) * 직전값` 을 반올림해 담는다.
6. 원본 · MA(3) · MA(12) · EMA(α=0.3) 의 처음 5개와 설명 두 줄을 찍는다.

3단계 — 가법 분해

7. `decompose_additive(data, period=12)` 는 `trend` 를 `None` 으로 채운 뒤 `range(half, n - half)` 의 `i` 에만 `data[i-half:i+half]` 의 평균을 넣는다.
8. 트렌드가 있는 자리만 `detrended = data - trend` 를 구하고, 같은 달(`m, m+period, …`)끼리 평균해 `seasonal_avg` 를 만든다(값이 없으면 0). 이것을 `i % period` 로 120칸에 깔고 반올림한다.
9. 트렌드가 있는 자리만 `residual = data - trend - seasonal` 을 반올림해 넣고, `(trend, seasonal, residual)` 을 돌려준다.
10. 인덱스 6~17 을 표로 찍되 트렌드 · 잔차가 없으면 `N/A` 를 찍고, 이어서 계절성 패턴 12개를 찍는다.

4단계 — 자기상관

11. `autocorrelation(data, lag)` 는 평균과 분산(÷n)을 구하고, 분산이 0 이면 0 을 돌려준다. 아니면 `n - lag` 쌍의 공분산(÷n)을 분산으로 나눠 소수 넷째 자리로 반올림한다.
12. lag `[1, 2, 3, 6, 12, 24]` 마다 값 · 부호 · `'█' × int(|acf| × 30)` 막대를 찍는다.

5단계 — ARIMA 개념과 워크플로우

13. ARIMA(p, d, q) 세 글자의 뜻과 ADF 검정 · ARIMA 피팅 · 예측 · SARIMAX · auto_arima 사용 흐름을 담은 여러 줄 문자열을 `print` 로 찍기만 한다.
14. 시각화 → 정상성 검정 → 차분 → ACF/PACF → 피팅 → 진단 → 예측의 7단계를 한 줄씩 찍는다.

**시작 코드**

```python
# 시계열 분석 기본 — 연습 파일
import random
import math
from collections import deque  # 정답과 맞춘 import (쓰지 않는다)

# TODO: 시드를 42 로 고정

print("=== 시계열 데이터 생성 ===")
def generate_time_series(n=120):
    """월별 데이터 생성 (10년치)"""
    data = []
    for t in range(n):
        # TODO: 트렌드 · 계절성 · 노이즈를 구해 더하고 반올림해 data 에 넣는다
        pass
    return data

data = generate_time_series(120)
# TODO: 데이터 수, 처음 12개, 최솟값·최댓값(:.2f) 출력

print()
print("=== 이동 평균 (Moving Average) ===")
def moving_average(data, window):
    """단순 이동 평균"""
    result = []
    # TODO: 창 시작점마다 평균을 내 반올림해 담는다
    return result

def exponential_moving_average(data, alpha=0.3):
    """지수 이동 평균: 최근 값에 더 큰 가중치"""
    # TODO: 첫 값은 그대로, 다음부터 점화식
    pass

ma_3 = moving_average(data, 3)
ma_12 = moving_average(data, 12)
ema = exponential_moving_average(data, alpha=0.3)

print(f"원본 (처음 5): {data[:5]}")
print(f"MA(3): {ma_3[:5]}")
print(f"MA(12): {ma_12[:5]}")
print(f"EMA(α=0.3): {ema[:5]}")
print("MA 창이 클수록 더 부드러움 (노이즈 제거)")
print("EMA는 최근 데이터에 더 반응 (α↑ → 더 민감)")

print()
print("=== 시계열 분해 (Decomposition) ===")
def decompose_additive(data, period=12):
    """가법 분해: Y = Trend + Seasonal + Residual"""
    n = len(data)
    # TODO 1. 트렌드 (가장자리는 None)
    # TODO 2. 트렌드 제거
    # TODO 3. 같은 달끼리 평균 → 계절성, i % period 로 확장
    # TODO 4. 잔차
    return trend, seasonal, residual

trend, seasonal, residual = decompose_additive(data, period=12)

print("분해 결과 (월 7~18):")
print(f"{'월':>4} {'원본':>8} {'트렌드':>8} {'계절성':>8} {'잔차':>8}")
for i in range(6, 18):
    t = ...  # TODO: 트렌드 문자열, 없으면 "N/A"
    r = ...  # TODO: 잔차 문자열, 없으면 "N/A"
    print(f"{i+1:>4} {data[i]:>8.2f} {t:>8} {seasonal[i]:>8.2f} {r:>8}")

print(f"\n계절성 패턴 (12개월): {seasonal[:12]}")
print("양수 = 평균 이상, 음수 = 평균 이하")

print()
print("=== 자기상관 (Autocorrelation) ===")
def autocorrelation(data, lag):
    """lag 시점의 자기상관계수"""
    # TODO: 평균, 분산(÷n), 분산 0 방어, 공분산(÷n), 비율 반올림
    pass

print("자기상관 (ACF):")
for lag in [1, 2, 3, 6, 12, 24]:
    # TODO: acf 값, 막대, 부호를 구해 f"  lag={lag:>2}: {acf:>7.4f} {sign}{bar}" 로 출력
    pass
print("lag=12에서 높은 상관 → 12개월 주기 계절성 확인")

print()
print("=== ARIMA 개념 ===")
# TODO: ARIMA(p,d,q) 설명과 statsmodels·pmdarima 사용 흐름을 여러 줄 문자열로 print

print()
print("=== 시계열 분석 워크플로우 ===")
# TODO: 7단계를 한 줄씩 출력
```

**확인 방법** — `python time-series.py` 로 돌려 `데이터 수: 120` · MA(3)/MA(12)/EMA 처음 5개 · 분해 표 12줄 · `lag=12` 막대가 `lag=6` 보다 훨씬 긴지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
