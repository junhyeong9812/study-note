# data-analysis/03-observational-vs-experimental — 관찰 연구 vs 실험, 교란 변수 — 정리 (힌트)

## 해결하는 문제

"이 기능을 쓴 사용자는 잔존율이 28%p 높다." 그래서 기능을 모두에게 켜면 잔존율이 오를까?

```text
  관찰 데이터    기능 켠 사용자 잔존 64.9%   기능 안 켠 사용자 잔존 36.5%   차이 +28.4%p
  실험 데이터    무작위로 켠 쪽  잔존 43.0%   무작위로 끈 쪽     잔존 45.0%   차이 −1.9%p (잔존율은 반올림)
                 (같은 사용자 집단, 실험 출력 — 아래 실험 절)
```

- 관찰 데이터의 차이는 **기능의 효과**와 **원래 다른 사람들이 기능을 켰다**는 사실이 섞인 값이다. 둘을 데이터만으로 떼어 낼 수 없을 때가 많다.
  - *관찰 연구(observational study)*: 연구자가 처치를 정하지 않고, 일어난 대로 기록한 데이터로 하는 연구.
  - *실험(experiment)*: 연구자가 처치를 배정하는 연구. 배정을 무작위로 하면 *무작위 실험(randomized experiment)*이다(OpenIntro 1.4).
  - *처치(treatment)*: 효과를 알고 싶은 개입. 여기서는 "기능 켜기".

쉬운 예: "우산을 든 사람이 많은 날 교통사고가 많다." 우산이 사고를 일으키나?\
비가 우산과 사고를 **둘 다** 늘린다. 비를 모르면 우산이 범인처럼 보인다.

똑같은 구조다.\
"원래 많이 쓰는 사용자"가 비다. 그들이 새 기능을 더 많이 켜고, 원래 오래 남는다.

실무 예:
- "프리미엄 회원은 구매 전환이 3배" → 프리미엄이 전환을 만든 게 아니라 원래 살 사람이 프리미엄에 가입했다.
- "캐시를 켠 서비스가 장애가 적다" → 캐시를 켤 여유가 있는 팀이 원래 운영을 잘했다.
- "푸시 알림을 허용한 사용자는 잔존이 높다" → 알림 허용이 원인인지 관심의 표지인지 모른다.

## 동작·원리

### 1. 교란 변수 — 화살표 그림

```text
              교란 변수 Z
          (원래 많이 쓰는 사용자)
              │            │
              ▼            ▼
     처치 X (기능 켬)  ··?··▶  결과 Y (30일 잔존)

  관찰된 X–Y 연관 ← (X → Y 진짜 효과)와 (X ← Z → Y 뒷문 경로)가 섞인 것
```

- 위 식은 개념 그림이다. 효과를 숫자로 나누는 정확한 정의(효과 척도·대상 집단)는 data-analysis 25다.

- OpenIntro 1.3.4의 정의: *교란 변수(confounding variable)*는 설명 변수와 반응 변수 **둘 다와** 상관된 변수다. 숨은 변수(lurking variable)·교란 요인이라고도 부른다.
  - *설명 변수(explanatory variable)*: 원인이라고 의심하는 변수(X).
  - *반응 변수(response variable)*: 영향을 받는다고 의심하는 변수(Y).
- OpenIntro의 예: 선크림 사용과 피부암의 연관. 햇빛 노출이 둘 다를 늘린다.
- OpenIntro는 관찰 연구에서 인과를 말하려고 교란 변수를 다 찾아 통제하려 해도, **모든 교란 변수를 검토하거나 잴 수 있다는 보장이 없다**고 적는다.
- 이 그림을 정식으로 다루는 도구(인과 DAG, 뒷문 경로, 조정할 변수와 하면 안 되는 변수)는 [data-analysis 25](../25-causal-inference-basics/2-summary.md)(인과 추론 기초)다.

### 2. 관찰 연구의 두 모양

```text
  전향적(prospective)    지금 사람을 정해 ─────────▶ 앞으로 일어나는 일을 기록
  후향적(retrospective)  이미 쌓인 기록에서 ◀─────── 과거를 거슬러 모음 (대부분의 로그 분석)
```

- 정의는 OpenIntro 1.3.4. 서비스의 로그·DB 분석은 대부분 후향적 관찰 연구다. 한 데이터셋에 두 방식으로 모은 변수가 섞일 수도 있다(OpenIntro).

### 3. 실험 설계 네 원칙 (OpenIntro 1.4.1)

```text
  ① 통제(controlling)     처치 말고 다른 차이는 연구자가 같게 맞춘다     (같은 화면·같은 시점)
  ② 무작위(randomization) 통제 못 하는 차이는 무작위 배정으로 고르게    (동전·해시)
  ③ 반복(replication)     충분히 많은 대상, 연구 자체의 재현            (표본 크기·재실험)
  ④ 블록(blocking)        영향이 큰 변수로 먼저 묶고 블록 안에서 무작위  (신규/기존 사용자)
```

- 무작위 배정이 교란을 끊는 이유: 배정이 동전으로 정해지면 **Z가 X를 정할 길이 없다.** 그래서 Z(잰 것이든 못 잰 것이든)가 두 그룹에 고르게 나뉜다 — 표본이 충분히 크면 평균적으로.
  - *블록(block)*: 결과에 영향이 크다고 아는 변수로 대상을 먼저 묶은 것. 블록마다 처치·대조를 같은 비율로 나눈다(OpenIntro의 예: 저위험/고위험 환자).
    - 흔한 오해: "무작위 배정이면 두 그룹이 똑같다." 작은 표본에서는 우연히 기울 수 있다. 그래서 큰 변수는 블록으로 맞추고, 배정 후 균형을 확인한다.
- 사람 대상 실험의 추가 장치(OpenIntro 1.4.2): 자기가 어느 그룹인지 모르게 하는 *맹검(blind)*, 가짜 처치인 *위약(placebo)*. 서비스 실험에서는 "새 기능임을 알리는 배지"가 기대 효과를 만들 수 있다는 점이 비슷하다(해석).

### 실험: 관찰 vs 무작위 배정 (시뮬레이션)

설정(모두 합성): 사용자 100,000명(`user_000000` 형식). 30%가 heavy(교란 변수). 기본 30일 잔존율 heavy 80%, light 30%. **기능의 진짜 효과는 −2%p**(설정값). 관찰 세계에서는 heavy의 70%, light의 10%가 스스로 기능을 켠다. 실험 세계에서는 `SHA-256("exp-feature-x:" + user_id)`의 상위 64비트 짝/홀로 배정한다.

```python
treated = ua < (0.70 if heavy else 0.10)          # 관찰: 스스로 켬 (Z가 X를 정함)
treated = bucket(uid) == 1                        # 실험: 해시 배정 (Z와 무관)
def retained(heavy, treated, u):
    return u < (0.80 if heavy else 0.30) + (TRUE_EFFECT if treated else 0.0)
```

(실험 환경: 호스트 Python 3.12.3과 `python:3.12-slim`(3.12.14)에서 출력 동일. 시드 42, 사용자마다 고정 난수 2개.)

```text
[관찰] 처치 28018명 잔존 0.649 | 대조 71982명 잔존 0.365 | 차이 +0.284 | heavy 비율 처치 0.75 대조 0.12
[관찰·층 heavy=True] 처치 0.776 대조 0.804 차이 -0.027
[관찰·층 heavy=False] 처치 0.272 대조 0.302 차이 -0.030
[실험] 처치 50044명 잔존 0.430 | 대조 49956명 잔존 0.450 | 차이 -0.019 | heavy 비율 처치 0.30 대조 0.30
같은 사용자 같은 버킷: True
```

- 관찰 1: 관찰 비교는 +28.4%p다. 진짜 효과(−2%p)와 **부호가 반대**다. 처치 그룹의 heavy 비율이 75%, 대조는 12%로 기울었기 때문이다.
- 관찰 2: 같은 관찰 데이터를 Z로 층을 나누면 두 층 모두 −2.7%p·−3.0%p로 진짜 효과 근처다. 단, **Z를 재고 있었기 때문에** 가능했다. 못 잰 교란 변수는 이렇게 고칠 수 없다.
- 관찰 3: 해시 배정 실험은 −1.9%p로 진짜 효과 근처다. heavy 비율이 두 그룹 모두 0.30이다 — 무작위 배정이 Z를 고르게 나눴다.
- 관찰 4: 층별 차이와 실험 차이가 −2%p에서 조금씩 어긋나는 것은 유한 표본의 우연 오차다(해석). 시드를 42·1·2·3·4로 바꿔 돌리면 관찰 차이는 +0.284~+0.295, 실험 차이는 −0.014~−0.024였다 — 부호 반전은 이 설정(heavy 70%·light 10% 채택, 잔존 80%/30%)에서 확인한 다섯 시드 모두에서 재현됐다. 우연 오차의 크기를 재는 법은 [data-analysis 07](../07-sampling-distributions-and-clt/2-summary.md)·[08](../08-confidence-intervals/2-summary.md)이다.

## 쓰이는 자료구조·알고리즘

- 이 편의 커리큘럼 🔧 칸은 비어 있다(—). 실험을 만드는 데 쓰는 구조만 적는다.
- **해시 기반 결정적 배정** — `hash(salt + user_id)`로 저장 없이 같은 사용자를 같은 그룹에 둔다. salt를 실험마다 달리하면 실험끼리 배정이 독립에 가깝다. [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md) · [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- **층별 그룹 집계** — 교란 변수로 층을 나눠 층 안에서 비교한다(`GROUP BY z, treated`). [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md)
- **인과 그래프(DAG)** — 변수 사이 화살표. 정식 판정은 [data-analysis 25](../25-causal-inference-basics/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상(판단이 틀린 모양) | 원리 | 확인 |
|---|---|---|
| "X를 쓴 사람은 Y가 높다 → X를 늘리자" | 관찰 연관 ≠ 인과 | X를 **누가 정했나**? 사용자가 골랐으면 관찰 연구 |
| 처치/대조의 다른 특성(가입 기간·플랜)이 크게 다르다 | 교란 | 배정 전 특성의 균형표(아래 SQL) |
| 층을 나누니 차이가 줄거나 뒤집힌다 | 교란(극단은 심슨의 역설, data-analysis 12) | 층별 차이와 전체 차이 비교 |
| 기능을 전면 적용했더니 지표가 안 움직인다 | 관찰 효과를 인과로 오해 | 소규모 무작위 실험으로 재확인 |

### 2. 균형표 — 처치/대조가 원래 닮았나

```sql
-- PostgreSQL 17: 처치 여부별로 '처치 전' 특성 비교 (예시 스키마)
SELECT treated,
       count(*)                                                    AS users,
       avg((plan = 'paid')::int)                                   AS paid_ratio,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY pre_30d_sessions) AS median_pre_sessions
FROM feature_users
GROUP BY treated;
```

- 반드시 **처치 전**에 잰 특성만 넣는다. 처치 후 변수(처치의 결과일 수 있는 것)로 비교하거나 통제하면 오히려 편향이 생길 수 있다 — 매개·충돌 변수 문제, data-analysis 25.
- 균형표가 비슷해도 못 잰 변수까지 닮았다는 보장은 없다. 관찰 연구의 한계다.

### 3. 실험으로 바꾸는 법

```python
# Python 3.12: 해시 배정 (같은 사용자 → 같은 버킷, 저장 불필요)
def bucket(uid: str, salt: str = "exp-feature-x") -> int:
    return int.from_bytes(hashlib.sha256(f"{salt}:{uid}".encode()).digest()[:8], "big") % 2
```

- 배정 단위(사용자·세션·기기)와 결과 지표의 단위를 함께 설계한다. 사용자로 배정하고 세션 단위 지표를 보면 같은 사용자 세션끼리의 상관 때문에 분산을 델타 방법 등으로 따로 추정해야 한다(Deng·Lu·Litz WSDM 2017). 배정·지표 설계·기간·SRM은 [data-analysis 14](../14-ab-testing-design/2-summary.md)·[15](../15-ab-pitfalls-srm-peeking/2-summary.md)(A/B).
- 실험이 불가능하거나 비윤리적이면(요금 인상을 일부에게만 등) 관찰 연구를 하되, 단순 관찰 비교의 결론은 "연관"으로 쓰고 교란 후보를 명시한다. 인과로 말하려면 식별 가정(잰 변수로 뒷문 경로가 모두 막힌다 등)을 세우고 정당화해야 한다(data-analysis 25).

## 장애 시나리오와 대처

### 1. 관찰 데이터로 인과 주장 → 반대 결론 (⚠ 커리큘럼)

- 현상: "기능 X 사용자의 잔존이 +28%p" → 전체 기본값을 ON으로 바꿨다.
- 보이는 형태: 전면 적용 후 잔존이 오르지 않고 조금 내려갔다(실험 설정의 진짜 효과 −2%p).
- 원인: 원래 많이 쓰는 사용자가 기능을 켰다(교란). 관찰 차이의 부호가 진짜 효과와 반대였다.
- 대처: 기본값 변경 같은 결정은 무작위 실험으로 확인한다. 관찰 분석은 층별 비교 + 균형표 + "연관" 표기.

### 2. 자기 선택 베타 그룹을 대조군으로

- 현상: 베타 신청자(처치)와 미신청자(대조)를 비교해 "신규 결제 흐름이 전환 +15%(예시)".
- 원인: 신청 여부가 관심도라는 교란 변수와 묶였다. 신청자는 원래 전환이 높다.
- 대처: 신청자 **안에서** 무작위로 새 흐름/기존 흐름을 나눈다(블록 = 신청자). 비교는 같은 블록 안에서만.

### 3. 처치 후 변수로 "통제"

- 현상: "같은 세션 수를 가진 사용자끼리 비교하면 기능 효과가 0" → 기능을 폐기했다.
- 원인: 세션 수가 기능의 **결과**(매개 변수)였다. 결과의 일부를 통제해 효과를 지웠다.
- 대처: 통제·층화 변수는 처치 전에 정해진 것만 쓴다. 판단 기준은 data-analysis 25의 DAG.

### 4. 시점이 다른 그룹 비교 (전/후 비교)

- 현상: 기능 출시 전 주 vs 후 주의 전환을 비교해 효과를 주장했다.
- 원인: 시점 자체가 교란이다(계절성·캠페인·장애). 처치와 시점이 완전히 겹쳐 떼어 낼 수 없다.
- 대처: 같은 기간에 무작위로 나눈 대조군을 둔다. 불가능하면 영향을 안 받은 비교 그룹을 두고 차분의 차분(data-analysis 25)을 검토한다.

## 핵심 문장

- 관찰 데이터의 차이는 처치 효과와 "누가 처치를 받았나"의 차이가 섞인 값이다.
- 교란 변수는 설명 변수와 반응 변수 둘 다와 관련된 변수다. 모든 교란 변수를 찾아 잴 수 있다는 보장은 없다(OpenIntro 1.3.4).
- 무작위 배정은 교란 변수가 처치를 정할 길을 끊는다. 그래서 잰 변수와 못 잰 변수 모두 그룹 간에 평균적으로 고르게 나뉜다.
- 잰 교란 변수는 층을 나눠 비교하면 줄일 수 있다. 처치 후 변수는 통제하지 않는다.
- 결정(기본값 변경·전면 적용)의 근거가 인과라면 실험으로 확인한다. 실험이 불가능하면 단순 관찰 비교의 결론은 "연관"으로 쓴다(식별 가정을 세운 인과 추론은 data-analysis 25).

## 관련 주제·근거

- 선행: [02-sampling-and-bias](../02-sampling-and-bias/2-summary.md) · 후속: 상관과 인과·심슨의 역설([12](../12-correlation-vs-causation/2-summary.md)), 인과 추론 기초([25](../25-causal-inference-basics/2-summary.md)), A/B 설계([14](../14-ab-testing-design/2-summary.md))
- 다른 영역: [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md)(해시 배정 구현) · [math/07-probability-and-bayes](../../math/07-probability-and-bayes/2-summary.md)(조건부 확률·독립) · [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md)
- 근거
  - OpenIntro Statistics 4판 — 1.2.5 "Introducing observational studies and experiments", 1.3.4 "Observational studies"(교란 변수 정의, 선크림·햇빛 예, 전향적·후향적), 1.4 "Experiments"(1.4.1 통제·무작위·반복·블록, 1.4.2 맹검·위약). 확인 경로: https://www.openintro.org/book/os/ 목차 + GitHub `OpenIntroStat/openintro-statistics` `ch_intro_to_data.tex` + 4판 PDF(Internet Archive 사본) 목차·본문(교란 변수 각주 "Also called a lurking variable, confounding factor, or a confounder")
  - Python 3.12 `hashlib`·`statistics` 문서
  - Deng, Lu, Litz (2017) "Trustworthy Analysis of Online A/B Tests: Pitfalls, Challenges and Solutions", WSDM — 배정 단위보다 낮은 분석 단위 지표는 델타 방법으로 분산 추정 https://exp-platform.com/Documents/2017WSDMDengLuLitz.pdf
- 실험 목록
  - 관찰(자기 선택) vs 교란 변수 층별 비교 vs 해시 무작위 배정 — 합성 사용자 100,000명, 진짜 효과 −2%p 설정, 시드 42, Python 3.12.3(호스트)·3.12.14(`python:3.12-slim`, `--network none`) 출력 동일
