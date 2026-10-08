# data-analysis/05-percentiles-and-latency-distributions — 백분위 계산·병합·히스토그램, 긴 꼬리 — 정리 (힌트)

## 해결하는 문제

서버 세 대의 p99를 각각 받아 평균을 냈다. 대시보드에는 "전체 p99 723ms"가 떴다. 사용자가 겪은 실제 p99는 155ms였다(실험 B).

```text
  인스턴스별 p99          A 64ms    B 251ms    C 1853ms
  avg(p99)               723ms     ← 대시보드 숫자 (틀림)
  요청 수 가중 avg(p99)    99ms     ← 이것도 틀림
  전체 원자료의 p99        155ms     ← 사용자가 겪은 값
```

- 평균만 보면 꼬리를 못 본다는 것은 [math/08](../../math/08-expectation-variance-tails/2-summary.md)에서 다뤘다(로그정규 지연: 평균 33ms, p99 205ms).
- 이 노트는 그다음 문제를 다룬다. **백분위를 어떻게 계산하고, 어떻게 합치고, 무엇으로 저장하나.**
  - *백분위(percentile)*: 값을 작은 것부터 줄 세웠을 때 비율 p 지점의 값. p99 = 99% 지점.
  - *분위수(quantile)*: 같은 개념을 비율(0~1)로 부르는 이름. p99 = 0.99 분위수.

쉬운 예: 반 세 개의 "상위 1% 커트라인"을 평균 내도 학년 전체의 상위 1% 커트라인이 되지 않는다.
- 인원이 적은 반 하나의 커트라인이 유난히 높으면 평균이 끌려간다.
- 학년 커트라인은 세 반 학생을 한 줄로 세운 뒤에야 나온다.

똑같은 구조다.\
백분위는 "줄 세운 순서"에서 나오는 값이라, 부분의 백분위를 더하거나 평균 내서 전체를 만들 수 없다.

실무 예:
- 서비스 p99 = `avg(인스턴스별 p99)`인 Grafana 패널. 트래픽 적은 인스턴스 하나가 숫자를 흔든다.
- Prometheus summary(앱이 미리 계산한 분위수)를 인스턴스끼리 평균 낸다([reliability/16](../../reliability/16-metrics-and-golden-signals/2-summary.md)).
- 버킷 경계가 `0.1s, 1s, 10s`뿐이라 p99가 `1s~10s` 한 칸에 떨어진 히스토그램에서 p99가 7.0s로 나온다. 실제는 2.14s였다(reliability/16 실험).
- 같은 데이터인데 Python과 SQL이 서로 다른 p90을 낸다(실험 A).

## 동작·원리

### 1. 백분위의 위치 — 줄 세우기

```text
  지연(ms)을 정렬한 1만 건
  1 ......................................... 5000 ........................... 9900 .... 10000
  ▕▁▁▂▂▃▃▄▅▆▇███████▇▆▅▄▃▃▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁ ▁ ▁
                    ↑ p50(중앙값)                                         ↑ p99   ↑ max
              요청 절반이 이보다 빠름                         100건 중 가장 느린 1건 언저리
```

- 오른쪽 꼬리가 긴 분포에서는 p50과 p99 사이가 멀다. 이 노트의 로그정규 예에서는 평균이 그 사이에 있었다. 꼬리가 극단적으로 무거우면 평균이 p99보다 클 수도 있다(로그정규에서 σ가 약 4.65보다 크면 — NIST 로그정규 평균식 `중앙값·e^(σ²/2)`로 계산). 어느 쪽이든 평균 하나는 꼬리 크기를 드러내지 않는다([math/08](../../math/08-expectation-variance-tails/2-summary.md) 5절).
  - *긴 꼬리(long tail)*: 드물지만 매우 큰 값이 분포 오른쪽에 길게 늘어선 모양. 지연·파일 크기·결제 금액에서 흔하다.
- p99는 "꼬리의 입구"다. 표본 1만 건이면 위로 100건이 p99 너머에 있다. 100건이면 1건뿐이다(4절).

### 2. 정의가 여러 개다 — 보간 방식

사분위수에서 정의가 갈리는 예는 [04-descriptive-statistics](../04-descriptive-statistics/2-summary.md)에 있다. 여기서는 꼬리 쪽 분위(p90·p99)에서 차이가 훨씬 커지는 것을 본다.

같은 10개 값 `[12, 15, 18, 20, 22, 25, 30, 41, 95, 300]`의 p90:

```text
  정렬 위치    1   2   3   4   5   6   7   8   9    10
  값          12  15  18  20  22  25  30  41  95   300
                                               ↑    ↑
  nearest-rank (ceil(0.9·10)=9번째)           95
  선형 보간 (위치 1+(n−1)·p = 9.1)             95 + 0.1·(300−95) = 115.5
  Python 기본 exclusive (위치 (n+1)·p = 9.9)  95 + 0.9·(300−95) = 279.5
```

| 계산 | p90 | 근거 |
|---|---|---|
| nearest-rank: `ceil(p·n)`번째 값 | 95 | 정의에서 바로 |
| PostgreSQL 17 `percentile_disc(0.9)` | 95 | 문서: 정렬 순서에서 위치가 비율 이상인 첫 값 |
| PostgreSQL 17 `percentile_cont(0.9)` | 115.5 (부동소수 출력 `115.49999999999993`) | 문서: 이웃 값 사이를 필요하면 보간 |
| Python 3.12 `statistics.quantiles(n=10, method='inclusive')` | 115.5 | 문서: i번째 값의 위치를 `(i−1)/(m−1)`로 |
| Python 3.12 `statistics.quantiles(n=10)` (기본 `exclusive`) | 279.5 | 문서: i번째 값의 위치를 `i/(m+1)`로 |

(실험 A — 위 표의 값은 실제 출력. Python 값은 호스트 Python 3.12.3, PostgreSQL 값은 실험 B-SQL과 같은 PostgreSQL 17.11 컨테이너)

- PostgreSQL `percentile_cont`와 Python `inclusive`는 이 데이터에서 같은 값을 냈다. 둘 다 최솟값을 0%, 최댓값을 100%로 놓는 선형 보간이다.
  - *보간(interpolation)*: 두 표본값 사이를 직선으로 이어 중간 값을 만드는 것.
- Python의 기본값 `exclusive`는 "모집단에 표본보다 극단인 값이 더 있을 수 있다"는 가정이다(Python 3.12 문서). 그래서 표본 끝 쪽 분위수를 더 바깥으로 민다.
  - 흔한 오해: "p90은 하나로 정해진 값이다" — 표본이 작으면 정의마다 크게 다르다. 위 예에서 95와 279.5는 3배 차이다.
- 분위 근처에 값이 촘촘한 데이터(연속 분포에서 뽑은 지연 등)는 표본이 크면 정의 사이 차이가 줄어든다. 이웃한 두 값의 간격이 좁아지기 때문이다. 분위가 값이 크게 뛰는 자리에 걸리면 표본이 커도 차이가 남는다(계산: 90%가 0, 10%가 1000인 1만 건의 p90은 nearest-rank 0, `inclusive` 100, `exclusive` 900). 그래서 **도구를 바꿔 비교할 때는 정의부터 맞춘다.**

### 3. 백분위는 합칠 수 없다 — 히스토그램은 합칠 수 있다

```text
  인스턴스 A (9만 건, 빠름)    ▕▃█▅▂▁                p99  64ms
  인스턴스 B (9천 건, 중간)    ▕ ▂▅█▄▂▁▁             p99 251ms
  인스턴스 C (1천 건, 느림)    ▕     ▁▃▆█▆▄▂▁▁▁      p99 1853ms
                              ─────────────────────▶ ms(로그 축)

  틀린 합치기:  avg(64, 251, 1853)            = 723
                (64·90000 + 251·9000 + 1853·1000) / 100000 = 99
  옳은 합치기:  10만 건을 한 줄로 세운 뒤 99,000번째 근처  = 155
                또는 같은 경계의 버킷 카운트를 더한 뒤 계산  = 154   (로그 버킷, 상대 오차 1% 이내)
```

- 평균 낸 p99(723)는 느린 인스턴스 C를 요청 수와 상관없이 1/3 무게로 센다. 요청의 1%뿐인 C가 숫자를 지배한다.
- 요청 수로 가중해도(99) 틀린다. 백분위는 순위에서 나오는 값이라 선형 결합이 아니다.
  - 전체 p99 위치(99,000번째) 근처의 요청은 대부분 B와 C의 중간 꼬리에서 온다. 어느 인스턴스의 p99와도 같지 않다.
- 옳은 방법은 두 가지다.
  1. 원자료를 모은다. 정확하지만 저장·전송 비용이 크다.
  2. **같은 버킷 경계를 쓰는 히스토그램**의 카운트를 더한다. 버킷 카운트는 더하기만 하면 되므로 합쳐도 정보가 더 사라지지 않는다. 오차는 버킷 폭만큼 남는다.
  - *히스토그램(histogram)*: 값의 범위를 구간(버킷)으로 나누고 구간마다 개수만 센 것.
- SQL(PostgreSQL 17.11)로 같은 모양의 합성 데이터를 만들어 반복했다. `avg_of_p99` 676.7, 요청 수 가중 97.5, 진짜 155.8이었다(실험 B-SQL). 숫자는 난수 생성기가 달라 조금 다르지만 모양은 같다.

### 4. 버킷 해상도 — 고정 경계 vs 로그 간격

```text
  고정 경계(사람이 정함, 12칸)
   |5|10|  25  |   50   |      100       |            250            |   ...   |
                                      p99=155가 100~250 칸 안에 있다 → 칸 안을 직선 보간 → 198 (+27.5%)

  로그 간격(이웃 경계 비 1.02, 331칸 사용)
   ||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
   어느 값이든 자기 크기의 약 1% 안에 칸 경계가 있다 → 154.4 (−0.6%)
```

(실험 C — 같은 10만 건에서)

| 분위 | 진짜 | 고정 버킷 12칸 | 로그 버킷(γ=1.02) |
|---|---|---|---|
| p50 | 20.9 | 21.5 (+2.7%) | 20.9 (+0.02%) |
| p99 | 155.4 | 198.1 (+27.5%) | 154.4 (−0.62%) |
| p99.9 | 697.2 | 799.2 (+14.6%) | 695.6 (−0.24%) |

- 고정 경계 히스토그램은 분위수를 **버킷 안 선형 보간**으로 추정한다. 오차는 분위수가 떨어진 버킷의 폭만큼 생길 수 있다(Prometheus 문서, [reliability/19](../../reliability/19-performance-measurement/2-summary.md)).
- 로그 간격 버킷은 경계를 `γ^k`로 둔다. 작은 값에는 좁은 칸, 큰 값에는 넓은 칸이 간다. 상대 오차가 일정하다.
  - 이 실험의 대표값 `2γ^k/(γ+1)`은 칸 `(γ^(k−1), γ^k]` 안 어느 값이든 상대 오차 `(γ−1)/(γ+1)` ≈ 0.99% 이내다(식에서 바로).
- **HdrHistogram**이 이 생각을 정밀하게 구현했다.
  - 문서 예: 0~3,600,000,000,000 범위의 정수를 유효 숫자 3자리로 기록하면, 양자화 오차가 어떤 값이든 그 값의 1/1000(0.1%) 이하다(HdrHistogram 소개 페이지).
  - 메모리는 범위와 정밀도로만 정해지고 기록 수와 무관하다. 기록 비용도 일정하다(같은 페이지).
  - `add(otherHistogram)`으로 다른 히스토그램을 더할 수 있다(Java API 문서 `AbstractHistogram`).
- 이 실험의 로그 버킷은 개념을 보이려고 단순화한 구현이다. HdrHistogram의 실제 버킷 배치와 같지 않다.

### 5. t-digest — 꼬리에 해상도를 몰아준 분위 스케치

```text
  t-digest의 중심점(centroid) 크기 (개념도)
  분위  0 ─────────────────── 0.5 ─────────────────── 1
  묶음  ·  •  ●  ⬤  ⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤⬤  ⬤  ●  •  ·
        양 끝: 작은 묶음(값 몇 개)        가운데: 큰 묶음           양 끝: 작은 묶음
```

- *분위 스케치(quantile sketch)*: 데이터 전부를 저장하지 않고 작은 요약만 남겨 분위수를 근사하는 자료구조.
- t-digest는 값들을 *중심점*(평균과 개수만 가진 작은 묶음)으로 요약한다. 양 끝 분위에는 작은 묶음을 둬 꼬리를 정확히 본다.
- Dunning–Ertl(arXiv 1902.04023) 초록이 주장하는 성질
  - 꼬리 근처에서 특히 정확하다. 초록 표현으로는 정확도가 절대 오차가 아니라 `max(q, 1−q)`에 상대적이다.
    - 주의: q가 0·1에 가까우면 `max(q, 1−q)`는 1에 가까워지므로, 이 표현만으로는 꼬리 정확도가 설명되지 않는다. 본문 2.8절의 근거는 묶음 크기 제한이다. 묶음 크기를 `√(q(1−q))`(k1)·`q(1−q)`(k2)·`min(q, 1−q)`(k3)에 비례하게 제한해, 양 끝일수록 묶음이 작다.
  - 따로 계산한 요약을 합쳐도 정확도 손실이 없다고 주장한다.
- 이 노트는 t-digest를 구현하지 않았다. 실측 비교는 하지 않았고, 위 성질은 논문(초록·2.8절)의 주장이다.

| 저장 방식 | 합치기 | 오차 | 메모리 |
|---|---|---|---|
| 원자료 | 이어 붙이기 | 정의 차이뿐 | 기록 수에 비례 |
| 고정 경계 히스토그램 | 같은 경계면 카운트 합 | 버킷 폭만큼(경계 설계에 달림) | 버킷 수 |
| HdrHistogram(로그 간격) | `add` | 설정한 유효 숫자(예: 0.1%) 상대 오차 | 범위·정밀도로 고정 |
| t-digest | 요약 병합 | 꼬리에서 작음(논문 주장) | 압축 계수로 조절 |
| 미리 계산한 분위수(summary) | **불가** | — | 분위수 몇 개 |

### 6. 작은 표본의 p99는 흔들린다

(실험 E — 로그정규 지연, 이론 p99 204.8ms, 표본 크기마다 2000번 반복, seed 7)

```text
  n=100     p99 추정 95% 범위  101 ─────────────●────────────────── 340
  n=1000    p99 추정 95% 범위            162 ───●──── 253
  n=10000   p99 추정 95% 범위                190 ●─ 220
                                               이론값 205
```

- 표본 100건의 p99는 nearest-rank로 99번째 값, 즉 두 번째로 느린 값이다(선형 보간이면 99·100번째 사이). 맨 끝 한두 건이 무엇이냐에 따라 101~340ms를 오간다.
- 지연처럼 오른쪽 꼬리가 긴 분포에서는 분위가 높을수록 같은 정확도에 더 많은 표본이 필요하다(실험 E). 값 단위 오차는 그 분위 근처에 값이 얼마나 촘촘한지(밀도)에도 달려 있어, 균등분포처럼 꼬리가 없는 분포에서는 그렇지 않다(표본 분위수의 점근 분산 `p(1−p)/(n·f²)`). 1분 창에 요청이 100건뿐인 엔드포인트의 p99.9 그래프는 거의 최댓값 그래프다(해석).
- 추정값이 얼마나 흔들리는지는 표본분포 문제다 → [07-sampling-distributions-and-clt](../07-sampling-distributions-and-clt/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **정렬 후 순위 읽기**: 원자료가 메모리에 있으면 정렬 O(n log n) 뒤 위치를 읽는다. 분위수 하나만 필요하면 퀵셀렉트로 평균 O(n)이다([algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md) 「퀵셀렉트」).
- **누적 카운트 히스토그램**: 버킷별 개수를 앞에서부터 더해, 순위 `p·n`이 들어가는 버킷을 찾는다. 누적 합 개념은 [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md).
- **로그 간격 버킷(HdrHistogram)**: 값 → 버킷 번호를 계산으로 바로 구한다(탐색 없음). 버킷 카운트 배열의 합 = 병합.
- **t-digest**: 중심점 목록을 크기 제한 규칙으로 병합하는 분위 스케치(Dunning–Ertl).
- 근사 집계 스케치 일반(HyperLogLog·Count-Min)은 [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md). 슬라이딩 창 집계는 [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md).

## 적용 — 풀어나가는 법

### 1. "p99가 이상하다" — 증상 → 원리 → 확인

1. **증상 확인**: 대시보드 p99가 어떤 계산으로 나왔나 본다.
   - `avg(...quantile...)`, summary의 `quantile` 라벨 평균, 인스턴스별 p99 표의 평균 → 병합 오류(3절).
   - 버킷 경계 목록을 본다. 관심 분위가 넓은 버킷 하나에 떨어지면 해상도 부족(4절).
   - 그 창의 요청 수를 본다. 100건 미만이면 p99는 최댓값과 비슷하다(6절).
2. **원리**: 백분위는 순위 통계다. 합치려면 원자료나 같은 경계의 버킷을 합친다.
3. **코드로 확인** — Python 3.12 표준 라이브러리만으로

```python
import math, statistics

def nearest_rank(sorted_xs, p):            # ceil(p·n)번째 값 (PostgreSQL percentile_disc와 같은 규칙)
    return sorted_xs[max(1, math.ceil(p * len(sorted_xs))) - 1]

per_instance = {"A": a_ms, "B": b_ms, "C": c_ms}        # 인스턴스별 원자료 (리스트)
p99s = {k: nearest_rank(sorted(v), .99) for k, v in per_instance.items()}
merged = sorted(x for v in per_instance.values() for x in v)
print("avg(p99) =", statistics.fmean(p99s.values()))    # 틀린 값
print("true p99 =", nearest_rank(merged, .99))          # 옳은 값
print("py default p99 =", statistics.quantiles(merged, n=100)[98])   # exclusive — 정의가 다르다
```

4. **SQL로 확인** — PostgreSQL 17

```sql
-- 틀린 것: 그룹별 p99의 평균
WITH per AS (
  SELECT inst, percentile_disc(0.99) WITHIN GROUP (ORDER BY ms) AS p99 FROM lat GROUP BY inst)
SELECT avg(p99) FROM per;
-- 옳은 것: 원자료 전체에서 한 번
SELECT percentile_disc(0.99) WITHIN GROUP (ORDER BY ms) FROM lat;
-- 원자료 없이: 로그 간격 버킷 카운트를 저장해 두었다가 합친 뒤 누적 합으로
WITH m AS (SELECT b, sum(c) c FROM hist GROUP BY b),
     cum AS (SELECT b, sum(c) OVER (ORDER BY b) acc, sum(c) OVER () n FROM m)
SELECT 2 * power(1.02, min(b)) / (1.02 + 1) AS p99 FROM cum WHERE acc >= 0.99 * n;
```

- 실험 B-SQL에서 버킷 682행(인스턴스 × 버킷)만으로 p99 154.4를 얻었다. 원자료 기준 155.8과 0.9% 차이다.
- 윈도 함수 `sum() OVER (ORDER BY ...)`는 [database/05-window-functions-and-cte](../../database/05-window-functions-and-cte/2-summary.md).

### 2. 지표를 설계할 때

- 서버마다 분위수를 계산해 내보내지 말고, **같은 경계의 히스토그램**을 내보낸다. 합칠 일이 있으면 summary는 피한다.
- 경계는 SLO 문턱 근처를 촘촘히 둔다. 모르면 로그 간격(native histogram, HdrHistogram)을 쓴다.
- 분위와 함께 **표본 수**를 같이 그린다. 표본이 적은 창의 p99.9는 신호가 아니라 잡음일 수 있다.
- SLI를 "X ms 이내 요청 비율"로 정의하면 합치기 쉽다. 비율은 분자·분모를 각각 더하면 된다([reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md)).

## 장애 시나리오와 대처

### 1. 인스턴스 p99를 평균 냈다 (⚠ 커리큘럼)

- 현상: 서비스 p99 패널이 사용자 체감, 부하 테스트 결과와 맞지 않는다.
- 보이는 형태: 트래픽이 적은 인스턴스 하나가 느려지면 패널 p99가 몇 배로 뛴다(실험 B: 진짜 155ms인데 723ms). 반대로 큰 인스턴스의 꼬리는 희석된다.
- 원인: 백분위는 순위에서 나오는 값이라 평균·가중 평균으로 합칠 수 없다.
- 대처: 히스토그램 버킷을 합친 뒤 분위수를 계산한다(`histogram_quantile(0.99, sum by (le) (...))`, [reliability/19](../../reliability/19-performance-measurement/2-summary.md)). 인스턴스별 p99는 "어느 인스턴스가 이상한가"를 찾는 용도로만 쓴다.

### 2. 버킷 해상도 부족 (⚠ 커리큘럼)

- 현상: p99가 계단처럼 움직이거나, 배포 전후 차이가 안 보인다.
- 보이는 형태: 고정 경계 12칸에서 p99 198ms(진짜 155ms, +27.5%, 실험 C). 값이 버킷 경계 사이를 직선으로 오간다.
- 원인: 분위수가 넓은 버킷 하나에 떨어지면 그 안의 위치를 직선 보간으로 추정한다.
- 대처: SLO 문턱 근처에 경계를 추가하거나 로그 간격 히스토그램을 쓴다. 경계를 바꾸면 이전 데이터와 합칠 수 없으니 전환 시점을 기록한다.

### 3. 도구마다 p90이 다르다

- 현상: 분석가의 Python 리포트와 SQL 대시보드의 p90·p99가 다르다.
- 보이는 형태: 작은 그룹(예: 하루 주문 10건인 상점)에서 차이가 크다. 실험 A에서 95 vs 115.5 vs 279.5.
- 원인: nearest-rank, 선형 보간(`percentile_cont`, `inclusive`), `exclusive`(Python 기본)가 서로 다른 정의다.
- 대처: 리포트에 정의를 적는다. 비교할 때 같은 정의로 맞춘다(Python이면 `method='inclusive'` ↔ PostgreSQL `percentile_cont`). 표본이 작은 그룹은 분위수 대신 원값이나 개수를 보여 준다.

### 4. 표본이 적은 창의 p99로 알람을 건다

- 현상: 새벽마다 p99 알람이 울렸다 꺼진다.
- 보이는 형태: 트래픽이 적은 시간대에만 p99가 출렁인다. 표본 100건짜리 p99는 101~340ms를 오간다(실험 E).
- 원인: 높은 분위수는 꼬리에 표본이 몇 개 없으면 크게 흔들린다.
- 대처: 창을 늘리거나, 최소 표본 수 조건을 붙이거나, "X ms 초과 요청 수/비율"로 알람한다([reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md)).

### 5. summary 분위수를 합쳐 SLO를 판정했다

- 현상: 분기 SLO 보고서의 p99가 어떤 원자료로도 재현되지 않는다.
- 보이는 형태: 쿼리가 `avg(http_server_requests_seconds{quantile="0.99"})` 모양이다.
- 원인: summary는 앱 안에서 미리 계산한 분위수라 합칠 수 없다(Prometheus 문서, [reliability/16](../../reliability/16-metrics-and-golden-signals/2-summary.md)).
- 대처: histogram으로 바꾼다. 과거 기간은 재계산할 수 없다는 한계를 보고서에 적는다.

## 핵심 문장

- 백분위는 줄 세운 순서에서 나오는 값이라, 부분의 백분위를 평균 내거나 가중 평균 내도 전체 백분위가 되지 않는다.
- 합칠 수 있는 것은 원자료와 같은 경계의 히스토그램 카운트다. 분위수는 합친 뒤에 계산한다.
- 고정 경계 히스토그램의 오차는 분위수가 떨어진 버킷의 폭이 정한다. 로그 간격 버킷은 상대 오차를 일정하게 묶는다.
- 같은 데이터라도 nearest-rank·선형 보간·Python 기본(`exclusive`)의 백분위가 다르다. 작은 표본일수록 차이가 크다.
- 지연처럼 꼬리가 긴 분포에서는 높은 분위수일수록 같은 정확도에 더 많은 표본이 필요하다. 100건의 p99는 가장 느린 한두 건이 정한다.

## 관련 주제·근거

- 선행
  - [04-descriptive-statistics](../04-descriptive-statistics/2-summary.md) — 중심·산포·사분위수
  - [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md) — 평균 vs 백분위, 로그정규 지연(실험 C), 꼬리 부등식
  - [math/09-common-distributions](../../math/09-common-distributions/2-summary.md) — 정규 가정으로 p99를 어림하면 과소(4절)
- 후속·연결
  - [07-sampling-distributions-and-clt](../07-sampling-distributions-and-clt/2-summary.md) — 추정값이 표본마다 흔들리는 정도
  - [08-confidence-intervals](../08-confidence-intervals/2-summary.md) — 부트스트랩으로 중앙값 구간 만들기
  - [reliability/19-performance-measurement](../../reliability/19-performance-measurement/2-summary.md) — 측정 방법이 백분위를 왜곡하는 경우(coordinated omission)
  - [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md) — histogram vs summary, 버킷 실험
  - [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md) — 팬아웃에서 꼬리가 커지는 이유
  - [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md) · [reliability/08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md)
  - [web-platform/08-web-performance-vitals](../../web-platform/08-web-performance-vitals/2-summary.md) — 페이지별 p75를 평균 내지 않기
  - [database/05-window-functions-and-cte](../../database/05-window-functions-and-cte/2-summary.md)
- 후속(AI 엔지니어링): [ai-engineering/10-inference-latency-metrics](../../ai-engineering/10-inference-latency-metrics/2-summary.md) — TTFT·TPOT·ITL 분위 집계
- 문서·논문
  - Dunning, Ertl, "Computing Extremely Accurate Quantiles Using t-Digests", arXiv 1902.04023 — 초록: 꼬리에서 높은 정확도, `max(q, 1−q)`에 상대적인 정확도, 따로 계산한 요약을 손실 없이 결합 <https://arxiv.org/abs/1902.04023>
  - HdrHistogram 소개 페이지 — 유효 숫자 3자리 = 0.1% 양자화, 고정 메모리·고정 기록 비용 <https://hdrhistogram.github.io/HdrHistogram/> · Java API `AbstractHistogram.add`, `getValueAtPercentile` <https://hdrhistogram.github.io/HdrHistogram/JavaDoc/org/HdrHistogram/AbstractHistogram.html>
  - Python 3.12 `statistics.quantiles` — 기본 `exclusive`(`i/(m+1)`), `inclusive`(`(i−1)/(m−1)`), 이웃 두 값 선형 보간 <https://docs.python.org/3.12/library/statistics.html#statistics.quantiles>
  - PostgreSQL 17 9.21 Aggregate Functions, 표 9.62 Ordered-Set Aggregate Functions — `percentile_cont`(보간), `percentile_disc`(위치가 비율 이상인 첫 값) <https://www.postgresql.org/docs/17/functions-aggregate.html>
  - Prometheus "Histograms and summaries" — summary 집계 불가, 버킷 폭 오차 <https://prometheus.io/docs/practices/histograms/>
- 실험 목록
  - A. 10개 값의 p90 — nearest-rank·선형 보간·Python `inclusive`/`exclusive`. 호스트 Python 3.12.3 표준 라이브러리.
  - B. 인스턴스 3대(9만·9천·1천 건, 로그정규, seed 42)의 avg(p99)·가중 평균·진짜 p99. 같은 환경.
  - B-SQL. 같은 모양의 합성 데이터를 PostgreSQL 17.11(Docker `postgres:17`, `--network none --cpus=2`, `setseed(0.42)`)에서 `percentile_cont`/`percentile_disc`·그룹 p99 평균·로그 버킷 병합 p99.
  - C. 고정 경계 12칸(선형 보간) vs 로그 간격(γ=1.02) 버킷의 p50·p99·p99.9 오차. 호스트 Python.
  - D. 인스턴스별 로그 히스토그램 병합 p99 = 전체 원자료 히스토그램 p99(154.4). 호스트 Python.
  - E. 표본 크기 100·1000·10000에서 p99 추정의 95% 범위(반복 2000, seed 7). 호스트 Python.
