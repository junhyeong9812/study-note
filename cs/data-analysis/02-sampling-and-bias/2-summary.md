# data-analysis/02-sampling-and-bias — 모집단·표본·표본 추출·편향 — 정리 (힌트)

## 해결하는 문제

우리가 알고 싶은 것은 **전체**인데, 손에 든 것은 **일부**다.

```text
  알고 싶은 것   "전체 사용자의 평균 월 사용 시간"      ← 모집단
  손에 든 것     "설문에 답한 1,604명의 평균"           ← 표본
  질문           이 1,604명이 전체를 닮았나?
```

- 일부로 전체를 말하려면 일부가 전체를 **닮도록** 뽑아야 한다. 닮지 않게 뽑히면 아무리 많이 모아도 틀린다.
  - *모집단(population)*: 알고 싶은 대상 전체.
  - *표본(sample)*: 모집단에서 실제로 관찰한 일부.
  - *편향(bias)*: 뽑는 방식 때문에 표본의 값이 모집단 값에서 **한쪽으로** 체계적으로 어긋나는 것.

쉬운 예: 국 간을 볼 때 잘 저어서 한 숟가락 뜬다.\
안 젓고 위에서만 뜨면, 숟가락을 백 번 떠도 바닥에 가라앉은 소금 맛은 모른다.

똑같은 구조다.\
"잘 젓기"가 무작위 추출이다. "위에서만 뜨기"가 응답자만·생존자만·편한 대상만 보는 것이다. 숟가락을 더 뜨는 것(표본 크기)은 젓지 않은 문제를 고치지 못한다.

실무 예:
- 앱 내 설문 응답자만 보고 "사용자는 평균 22시간 쓴다"고 보고한다. 응답한 사람은 원래 많이 쓰는 사람이었다.
- 지금 남아 있는 고객만 분석해 "초기에 많이 쓰면 오래 남는다"고 결론 낸다. 떠난 고객은 데이터에 없다.
- 로그 샘플링을 "에러가 난 요청만 100% 저장"으로 설정해 두고, 그 로그로 전체 지연 분포를 그린다.

## 동작·원리

### 1. 모집단 → 표본 깔때기 — 편향이 들어오는 자리

```text
  모집단 (전체 사용자 100,000명)
      │  ① 표본 틀(frame): 연락 가능한 사람만?  ── 포함 편향
      ▼
  추출 대상 (무작위로 초대 10,000명)
      │  ② 응답: 누가 답하나?                    ── 무응답 편향 (응답 편향)
      ▼
  응답자 (1,604명)
      │  ③ 기록·생존: 누가 남아 있나?            ── 생존자 편향
      ▼
  분석에 쓴 행
```

- 각 단계에서 "남는 사람"이 관심 값과 관련 있으면 표본이 한쪽으로 기운다.
  - *표본 틀(sampling frame)*: 실제로 뽑을 수 있는 대상 목록. 모집단과 다를 수 있다(예: 푸시 알림을 켠 사용자만).
  - *무응답 편향(non-response bias)*: 응답하지 않은 사람이 응답한 사람과 달라서 생기는 편향. OpenIntro 1.3.3은 무작위로 뽑아도 무응답률이 높으면(예: 30%만 응답) 결과가 모집단을 대표하는지 불분명하다고 쓴다.
  - *편의 표본(convenience sample)*: 접근하기 쉬운 대상만 모은 표본. 어떤 부분 모집단을 대표하는지 알기 어렵다(OpenIntro 1.3.3).
  - *생존자 편향(survivorship bias)*: 어떤 걸러내기를 "통과한" 대상만 보는 편향. 탈락한 대상의 정보가 사라진다.
    - 흔한 오해: "데이터가 많으면 대표성이 생긴다." 아래 실험처럼 응답자 수를 10배, 100배 늘려도 오차는 거의 그대로다.
- 생존자 편향의 고전 일화는 2차 대전 중 Wald의 항공기 피탄 분석이다(돌아온 비행기의 탄흔만 보면 안 된다). 원 보고서는 열지 않았고, Mangel·Samaniego(JASA 1984)를 인용한 Wikipedia "Survivorship bias"(2차)로 확인했다.

### 2. 무작위 추출 네 가지

```text
  단순 무작위            층화                    군집                    다단계
  ●○○●○○○●○○        [무료 ●○○○●○○○]       [반A ●●●●] 통째로     [반A ●○●○] 반 안에서
  ○○●○○●○○○●        [유료 ○●○○]            [반B ○○○○]            [반B ○○○○] 다시
  모두 같은 확률         층마다 단순 무작위      몇 군집을 통째로       무작위 추출
```

- 네 방법의 정의는 OpenIntro 1.3.5 "Four sampling methods"를 따른다.
  - *단순 무작위 추출(simple random sample)*: 모두가 같은 확률로 뽑히고, 한 명이 뽑혔다는 사실이 다른 누가 뽑혔는지 알려 주지 않는 추출.
  - *층화 추출(stratified sampling)*: 모집단을 비슷한 것끼리 *층(stratum)*으로 나누고 층마다 단순 무작위로 뽑는다. 층 안이 관심 값에 대해 비슷할 때 특히 유용하다(OpenIntro).
  - *군집 추출(cluster sampling)*: 모집단을 군집으로 나누고 몇 군집을 골라 그 안을 전부 본다.
  - *다단계 추출(multistage sampling)*: 군집을 고른 뒤 그 안에서 다시 무작위로 뽑는다.
- OpenIntro는 층화 표본의 분석이 단순 무작위보다 복잡하며, 책의 방법을 확장해야 한다고 적는다. 층화 추정은 층별 평균을 **모집단의 층 비율로 가중**해 합친다.

### 3. 오차는 두 종류 — 표본 크기는 한쪽만 줄인다

```text
  추정값 − 참값  =  편향 (체계적, 뽑는 방식)  +  우연 오차 (무작위, 표본 크기)
                    n을 늘려도 그대로          n을 늘리면 줄어든다

      참값                    참값
       │  ●●●                  │
       │ ●●●●●     편향 큼      ●●●     편향 0
       │  ●●●      퍼짐 작음   ●●●●●    퍼짐 큼 → n을 늘리면 좁아짐
```

- 우연 오차가 표본 크기에 따라 줄어드는 방식(표준오차)은 [data-analysis 07](../07-sampling-distributions-and-clt/2-summary.md)(표본 분포)에서 다룬다. 분산의 성질 자체는 [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md).

### 실험: 응답 편향·층화·생존자 (시뮬레이션)

합성 모집단 100,000명(`user_000000` 형식). 유료 10%, 월 사용 시간은 로그정규(유료 중앙값 30h, 무료 5h, σ=0.6). 응답 확률 = `min(0.9, 0.02 × 사용 시간)`(많이 쓸수록 잘 답한다는 가정).

```python
def survey(n_invite, seed):
    r = random.Random(seed)
    invited = r.sample(pop, n_invite)                       # 초대는 단순 무작위
    return [h for _, _, h in invited if r.random() < min(0.9, 0.02 * h)]   # 응답은 편향
# 층화: 층별 표본 평균을 층 비율로 가중
est = w_paid * st.fmean(r.sample(paid_pop, k)) + (1 - w_paid) * st.fmean(r.sample(free_pop, n - k))
```

(실험 환경: 호스트 Python 3.12.3과 `python:3.12-slim`(3.12.14)에서 출력 동일. 시드: 모집단 42, 설문 7, 층화·생존 123. 층화 비교는 2,000회 반복.)

```text
[모집단] N=100000 참 평균 사용 시간 8.99h (유료 비율 0.100)
[응답 편향] 초대   1000명 응답   173명 응답자 평균 21.72h (참 8.99h, 오차 +12.73)
[응답 편향] 초대  10000명 응답  1604명 응답자 평균 22.17h (참 8.99h, 오차 +13.18)
[응답 편향] 초대 100000명 응답 16972명 응답자 평균 21.10h (참 8.99h, 오차 +12.11)
[층화] 반복 2000회, n=500: 단순 무작위 추정 평균 9.00 표준편차 0.546 | 비례 층화 평균 8.99 표준편차 0.374 | 분산 비 0.47
[생존자 편향] 생존자 28608명 평균 16.86h vs 전체 8.99h
[역확률 가중] 응답자 16972명 가중 평균 8.94h (참 8.99h)
```

- 관찰 1: 응답자가 173명 → 16,972명으로 98배 늘어도 오차는 +12~13h 그대로다. 표본 크기는 편향을 고치지 못한다. 전원에게 보내도(초대 100,000) 응답자 평균은 틀린다.
- 관찰 2: 단순 무작위와 비례 층화 모두 평균은 참값(8.99) 근처다(둘 다 편향 없음). 층화의 추정 표준편차가 0.546 → 0.374, 분산이 47%로 줄었다. 층(유료/무료)이 사용 시간과 강하게 관련돼 있기 때문이다(해석). 시드를 바꿔(모집단 42·1·2 × 추출 123·7·99, 9조합) 다시 돌리면 분산 비는 0.42~0.47이었다 — 이 설정의 값이지 층화 일반의 상수가 아니다.
- 관찰 3: "생존 확률이 사용 시간에 따라 커지는"(`min(0.95, 0.03h + 0.05)`) 설정에서 생존자만 보면 평균이 16.86h로 거의 두 배다.
- 관찰 4: 응답 확률을 **정확히 아는** 시뮬레이션에서는 1/p 가중으로 8.94h까지 돌아온다. 실무에서는 p를 모르므로 응답 확률을 추정하는 모델이 맞아야 한다. 이 보정은 "관찰된 변수로 응답 여부가 설명된다"는 가정에 기댄다(해석).
  - *역확률 가중(inverse probability weighting)*: 뽑힐(응답할) 확률이 p인 관찰에 1/p 무게를 주어, 적게 뽑힌 쪽을 키워 모집단을 다시 맞추는 방법.

## 쓰이는 자료구조·알고리즘

- **무작위 추출** — 크기를 아는 목록에서는 `random.sample`(비복원). 크기를 모르는 스트림에서 k개를 고르게 뽑으려면 저수지 표집. [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md) · [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md)(시드·PRNG 품질)
- **층화 추출** — 층 키로 그룹을 나누고(해시맵), 층마다 무작위 추출, 층 비율로 가중 합. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **해시 기반 결정적 샘플링** — `hash(user_id + salt) mod 100 < 10`으로 "사용자의 10%"를 매번 같은 사람으로 고른다(로그·트레이스 샘플링, 실험 배정). [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상(숫자가 틀린 모양) | 원리 | 확인 |
|---|---|---|
| 설문 결과가 사용 로그와 크게 다르다 | 무응답 편향 | 응답자 vs 비응답자의 **로그 지표**(사용 시간·가입 기간) 비교 |
| 남은 고객 분석이 "다 잘 된다"고 말한다 | 생존자 편향 | 분석 시작 시점 코호트 전체(이탈자 포함)로 다시 |
| 표본을 키워도 값이 안 움직인다 | 편향은 n과 무관 | 추출 경로(누가 행이 되나)를 그림으로 그려 본다 |
| 샘플링된 로그의 오류율이 이상하게 높다 | 오류 요청만 100% 보관 | 샘플링 규칙별 가중치로 다시 센다 |

### 2. 응답자가 모집단을 닮았나 — 로그로 대조

```sql
-- PostgreSQL 17: 초대 대상 중 응답자와 비응답자의 행동 지표 비교 (예시 스키마)
SELECT responded,
       count(*)                                                  AS users,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY monthly_hours) AS median_hours,
       avg(monthly_hours)                                         AS mean_hours
FROM survey_invite i JOIN user_usage u USING (user_id)
GROUP BY responded;
```

- 두 줄의 행동 지표가 크게 다르면 응답자 평균을 전체 평균이라고 쓰지 않는다. "응답자 기준"이라고 명시하거나 가중한다.
- 확인할 수 없는 변수(만족도 자체)는 대조할 수 없다. 관찰된 변수가 닮았다고 관심 변수까지 닮았다는 보장은 없다(해석).

### 3. 층화 추정 — 층 비율로 가중

```python
# Python 3.12: 층별 표본 평균을 모집단 층 비율로 가중
def stratified_mean(samples_by_stratum: dict[str, list[float]], weight: dict[str, float]) -> float:
    return sum(weight[s] * statistics.fmean(xs) for s, xs in samples_by_stratum.items())
```

- 층별로 뽑는 수를 일부러 다르게(작은 층을 더 많이) 했다면 반드시 이렇게 가중해 합친다. 그냥 다 합쳐 평균 내면 많이 뽑은 층 쪽으로 기운다.

### 4. 결정적 샘플링 (Java 21)

```java
// 사용자 10%를 매번 같은 사람으로: 해시 상위 64비트를 만분율 칸으로
static boolean sampled(String userId, String salt, int perTenThousand) throws Exception {
    byte[] h = java.security.MessageDigest.getInstance("SHA-256")
            .digest((salt + ":" + userId).getBytes(java.nio.charset.StandardCharsets.UTF_8));
    long v = java.nio.ByteBuffer.wrap(h, 0, 8).getLong();
    return Long.remainderUnsigned(v, 10_000) < perTenThousand;
}
```

- 실행 확인(OpenJDK 21.0.12, `eclipse-temurin:21-jdk`, `--network none`): `user_000000`~`user_099999` 10만 명에 `perTenThousand=1000`을 적용하자 9,962명(9.96%)이 뽑혔고, 같은 사용자를 다시 물으면 같은 답이었다.
- 시간·요청마다 동전을 던지면 한 사용자의 일부 행동만 남는다. 사용자 단위 지표(세션 수 등)를 보려면 **사용자 단위로** 뽑는다.

## 장애 시나리오와 대처

### 1. 설문 응답자 평균을 전체로 보고 (⚠ 커리큘럼: 응답 편향)

- 현상: "사용자 평균 월 22시간"으로 보고하고 서버 용량·요금제를 설계했다.
- 보이는 형태: 로그 기준 평균은 9시간. 무료 사용자 대상 기능 채택률이 예측의 절반에도 못 미친다.
- 원인: 많이 쓰는 사람이 더 잘 응답했다. 실험처럼 응답자를 늘려도 오차는 그대로다.
- 대처: 응답자/비응답자 로그 대조, "응답자 기준" 명시, 관찰 변수로 응답 확률을 모델링해 가중. 가능한 지표는 설문이 아니라 로그로 잰다.

### 2. 성공 사례만 분석 (⚠ 커리큘럼: 생존자 편향)

- 현상(예시): "1년 이상 남은 고객은 첫 주에 평균 17시간 썼다 → 첫 주 사용 시간을 늘리면 잔존이 오른다."
- 보이는 형태: 첫 주 사용을 늘리는 캠페인을 했는데 잔존율이 그대로다.
- 원인: 떠난 고객은 분석 테이블에 없었다. 생존자의 특성이 생존의 원인인지는 이 데이터로 알 수 없다(관찰 연구 — [03-observational-vs-experimental](../03-observational-vs-experimental/2-summary.md)).
- 대처: 시작 시점 코호트 전체(이탈자 포함)를 고정하고 비교한다. 인과가 궁금하면 실험으로 확인한다.

### 3. 편의 표본: 베타 테스터 = 사용자

- 현상: 사내·얼리어답터 베타에서 새 기능 만족도가 높아 전체 출시했다.
- 원인: 베타 참여자는 자원한 사람(자기 선택)이다. 어떤 부분 모집단을 대표하는지 알 수 없다.
- 대처: 출시 전 소수 비율 무작위 노출(점진 배포)로 대표 표본을 얻는다. 만족도를 설문으로 재면 응답자만 남는 무응답 편향이 다시 생기므로, 응답률을 보고 행동 지표와 함께 본다 — [data-analysis 14](../14-ab-testing-design/2-summary.md)(A/B 설계).

### 4. 샘플링 규칙이 섞인 로그로 비율 계산

- 현상: 대시보드의 오류율이 30%(예시)로 보인다. 실제 오류율은 1% 미만이다.
- 원인: "오류 요청은 100%, 정상 요청은 1%만 저장" 규칙의 로그를 그대로 셌다. 표본마다 뽑힌 확률이 달랐다.
- 대처: 행마다 샘플링 비율을 기록하고 1/비율로 가중해 센다. 규칙이 바뀐 시점을 대시보드에 표시한다.

## 핵심 문장

- 표본이 모집단을 닮게 하는 것은 표본 크기가 아니라 **뽑는 방식**이다.
- 편향은 체계적 오차라서 표본을 늘려도 줄지 않는다. 우연 오차만 표본 크기로 줄어든다.
- 응답자만·생존자만·편한 대상만 보면, 남은 이유가 관심 값과 관련될 때 결과가 한쪽으로 기운다.
- 층화 추출은 층 비율을 알고 층이 관심 값과 관련될 때(층 안은 비슷, 층끼리는 다름) 같은 표본 크기로 분산을 줄인다(비례 배분 기준). 합칠 때는 모집단 층 비율로 가중한다.
- 뽑힐 확률이 행마다 다르면 1/확률로 가중해야 한다. 그 확률을 모르면 보정은 모델 가정에 기댄다.

## 관련 주제·근거

- 선행: [01-data-types-and-measurement](../01-data-types-and-measurement/2-summary.md) · 후속: [03-observational-vs-experimental](../03-observational-vs-experimental/2-summary.md), 표본 분포·표준오차([07](../07-sampling-distributions-and-clt/2-summary.md))·A/B 설계([14](../14-ab-testing-design/2-summary.md))
- 다른 영역: [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md)(저수지 표집) · [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md) · [math/08-expectation-variance-tails](../../math/08-expectation-variance-tails/2-summary.md)(분산) · [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md)(해시 배정)
- 근거
  - OpenIntro Statistics 4판 1.3 "Sampling principles and strategies" — 1.3.1 모집단과 표본, 1.3.3 표본 추출(편향·무응답 편향·편의 표본), 1.3.5 네 가지 추출 방법(단순·층화·군집·다단계). 확인 경로: https://www.openintro.org/book/os/ 목차 + GitHub `OpenIntroStat/openintro-statistics` `ch_intro_to_data.tex` + 4판 PDF(Internet Archive 사본) 목차·본문(1.3.3의 "only 30% … respond", 1.3.5의 층화 분석이 "more complex")
  - Wald(1943) 항공기 취약성 메모 — 원문 미열람. Mangel, M. & Samaniego, F. (1984) "Abraham Wald's work on aircraft survivability", *JASA* 79(386):259–267 서지는 Wikipedia "Survivorship bias"(2차)로 확인
  - Python 3.12 `random.sample`·`statistics` 문서 https://docs.python.org/3.12/library/statistics.html
- 실험 목록
  - 해시 기반 10% 샘플링 `sampled()` — 10만 명 중 9,962명, 같은 사용자 같은 답 — OpenJDK 21.0.12(`eclipse-temurin:21-jdk`)
  - 응답 편향(초대 1,000/10,000/100,000), 단순 무작위 vs 비례 층화(n=500, 2,000회), 생존자 편향, 역확률 가중 — 합성 모집단 100,000명, 시드 42·7·123, Python 3.12.3(호스트)·3.12.14(`python:3.12-slim`, `--network none`) 출력 동일
