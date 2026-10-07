# data-analysis/14-ab-testing-design — A/B 테스트 설계: 무작위 배정·배정 단위·지표·기간 — 정리 (힌트)

## 해결하는 문제

새 결제 화면을 월요일에 내보냈더니 전환율이 올랐다. 화면 덕분일까?

```text
  전후 비교 (관찰, 예시)                      A/B 테스트 (실험, 예시)
  지난주 전환 4.8% ── 배포 ──> 이번주 5.3%      같은 주, 같은 사람들 중
        ↑                                      무작위 절반 → A(옛 화면) 4.9%
   그사이 바뀐 것: 급여일·광고·계절·경쟁사       무작위 절반 → B(새 화면) 5.3%
   → 화면 효과와 섞여 못 가른다                  → 바뀐 것은 화면 하나뿐
```

- 전후 비교에서는 화면 말고도 많은 것이 같이 바뀐다. 그 효과가 화면 효과와 섞인다(교란, [03 관찰 vs 실험](../03-observational-vs-experimental/2-summary.md)).
- 무작위로 나눈 두 그룹은 같은 기간을 같이 지난다. 배정·로깅이 제대로 되고 두 그룹이 서로 간섭하지 않는다면([15](../15-ab-pitfalls-srm-peeking/2-summary.md)), 두 그룹의 차이는 "처리" 아니면 "우연"뿐이다. 우연은 검정([09](../09-hypothesis-testing/2-summary.md))으로 걸러 낸다.
  - *A/B 테스트(온라인 통제 실험)*: 사용자를 무작위로 나눠 한쪽에만 변경을 보여 주고, 두 그룹의 지표를 비교하는 실험.
  - *처리(treatment)*: 실험에서 바꾼 것. 여기서는 새 화면이다. 바꾸지 않은 쪽은 *대조(control)*다.

쉬운 예: 비료 효과를 보려면 밭을 반으로 나눠 한쪽에만 비료를 준다. 작년 수확과 비교하면 날씨 차이가 섞인다.

똑같은 구조다.\
같은 해(같은 기간)에 무작위로 나눈 두 밭(두 그룹)을 비교한다.

실무 예:
- 추천 알고리즘 교체, 검색 순위 변경, 가격 표시 방식, 푸시 알림 문구.
- 기능 플래그 점진 배포([reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md))와 카나리([testing/19](../../testing/19-testing-in-production/2-summary.md))도 같은 배정 장치를 쓴다. 다만 목적이 "효과 측정"이 아니라 "위험 제한"이다.

이 노트는 **실험을 시작하기 전에 정할 것** 넷을 다룬다: 어떻게 나누나(배정), 무엇을 단위로 나누나(단위), 무엇을 재나(지표), 얼마나 돌리나(기간). 돌린 뒤의 함정(SRM·엿보기·간섭)은 [15](../15-ab-pitfalls-srm-peeking/2-summary.md)에서 다룬다.

## 동작·원리

### 1. 무작위 배정이 교란을 끊는다

```text
            활동성 높은 사람 ●●●●  낮은 사람 ○○○○
                         │ 무작위 배정 (동전 / 해시)
              ┌──────────┴──────────┐
         A: ●●○○                B: ●●○○        ← 활동성이 두 그룹에 고르게
              │                     │
           옛 화면                새 화면        ← 다른 점은 이것 하나
              ▼                     ▼
          전환 4.9%              전환 5.3%       차이 = 처리 효과 + 우연
```

- 무작위 배정은 사람이 고르지 않는다. 그래서 측정 못 한 성질(활동성·기기·요일 습관)도 평균적으로 두 그룹에 고르게 나뉜다.
  - "평균적으로"다. 한 번의 배정에서 우연히 치우칠 수 있다. 그 치우침의 크기를 재는 것이 표준오차와 검정이다([07](../07-sampling-distributions-and-clt/2-summary.md)·[09](../09-hypothesis-testing/2-summary.md)).
- OpenIntro Statistics 4판 1.4.1은 실험 설계 원칙 넷을 든다.
  - *통제(controlling)*: 처리 말고 다른 차이를 줄인다.
  - *무작위화(randomization)*: 통제 못 한 변수를 무작위로 고르게 나눈다.
  - *반복(replication)*: 사례를 충분히 모은다. 표본이 클수록 효과 추정이 정확해진다.
  - *블록화(blocking)*: 결과에 영향이 큰 변수(예: 신규/기존 사용자)로 먼저 묶고, 묶음 안에서 무작위로 나눈다.

### 2. 해시 기반 결정적 배정

동전을 매 요청마다 던지면 같은 사람이 새로고침마다 다른 화면을 본다. 배정을 DB에 저장하면 첫 방문마다 쓰기가 생긴다. 그래서 보통 해시로 계산한다.

```text
  "exp-checkout" | "user_000123"  ──해시──>  64비트 수  ──mod 10,000──>  칸 3,721
                                                                         │
                                       B 비율 50% → 경계 5,000            ▼
                                       칸 < 5,000 → B,  아니면 A        → B
```

- 같은 입력(실험 salt + 단위 ID)이면 늘 같은 칸이 나온다. 저장 없이 다시 계산해도 같은 답이다.
  - *salt(씨앗)*: 실험마다 다르게 섞는 문자열. salt가 다르면 같은 사람도 다른 칸에 떨어진다.
- Fabijan 외(KDD 2019) 5.1이 꼽는 배정 서비스의 요구 세 가지:
  - 각 변형을 볼 확률이 설정과 같다(예: 50:50).
  - 같은 사용자를 다시 배정하면 같은 변형이 나온다.
  - 실험이 여럿이면 한 실험의 배정이 다른 실험의 배정 확률에 영향을 주지 않는다.
  - 같은 절의 예외: 두 처리를 함께 보면 충돌하는 실험(예: 둘 다 B면 앱이 죽음)은 독립이 아니라 *배타적으로* 배정한다. 같은 사용자가 두 실험에 동시에 들어가지 않게 모집단이나 기간을 나눈다.
- 이 배정 장치(열쇠·salt·비율 올리기)의 모델링은 [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md)이 자세히 다룬다. 여기서는 통계 쪽 요구만 본다.
- 같은 논문 5.1: salt 목록에서 무작위로 고르는 방식이면 salt 수가 아주 많아야 한다. 365개 중에서 고르면 실험 약 23개만으로 "같은 salt를 쓰는 실험 쌍이 적어도 하나" 생길 확률이 50%다(생일 문제, [math/05](../../math/05-counting-and-birthday-bound/2-summary.md)).

### 실험: 해시 배정 — 재계산 일치·분할·실험 간 독립·끝 글자만 다른 키

FNV-1a 64비트로 칸을 만들었다. 같은 코드에 MurmurHash3의 마무리 섞기(`fmix64`)를 덧붙인 판과 비교했다.

```java
// scratchpad/da/14/Assign.java 핵심 (JDK만 사용)
static long fnv1a64(String s) {
    long h = 0xcbf29ce484222325L;
    for (byte b : s.getBytes(StandardCharsets.UTF_8)) { h ^= (b & 0xff); h *= 0x100000001b3L; }
    return h;
}
static long fmix64(long k) {           // MurmurHash3 마무리 섞기
    k ^= k >>> 33; k *= 0xff51afd7ed558ccdL; k ^= k >>> 33; k *= 0xc4ceb9fe1a85ec53L; k ^= k >>> 33;
    return k;
}
static int bucket(String salt, String unitId) {
    long h = fnv1a64(salt + "|" + unitId);
    if (MIX) h = fmix64(h);
    return (int) Math.floorMod(h, 10_000L);          // 음수 해시도 0..9999로
}
```

(실험, OpenJDK 21.0.12 Temurin 컨테이너 `--cpus=2 --network none`, 사용자 ID `user_000000`~`user_099999` 합성, 세션 줄은 사용자 3만 명의 키 `user_<i>#s0`·`#s1`·`#s2`(i = 0~29,999, 0 채움 없음), 해시 입력은 `exp-checkout|` + 키, 2026-10-08)

```text
== 해시: FNV-1a 단독
재계산 일치: 100000 / 100000
50% 설정 → A 50012 : B 49988
같은 salt 두 실험 그룹 일치: 100000 / 100000
다른 salt 두 실험 그룹 일치: 49503 / 100000  (둘 다 B: 24661)
세션 단위 배정, s0·s1 같은 그룹: 19258 / 30000
세션 단위 배정, 세션 3개 사용자 중 세 세션이 같은 그룹: 4259 / 30000
== 해시: FNV-1a + fmix64
재계산 일치: 100000 / 100000
50% 설정 → A 50087 : B 49913
같은 salt 두 실험 그룹 일치: 100000 / 100000
다른 salt 두 실험 그룹 일치: 49597 / 100000  (둘 다 B: 24712)
세션 단위 배정, s0·s1 같은 그룹: 15002 / 30000
세션 단위 배정, 세션 3개 사용자 중 세 세션이 같은 그룹: 7496 / 30000
```

- 관찰 1: 재계산하면 10만 명 모두 같은 칸이다. 결정적 배정의 핵심 성질이다.
- 관찰 2: 같은 salt로 실험 둘을 돌리면 두 실험의 그룹이 10만 명 전원 같다. B를 본 사람이 두 실험에서 같은 사람들이라, 두 효과를 가를 수 없다.
- 관찰 3: 세션 ID(`user_7#s0`, `user_7#s1`)처럼 **끝 글자만 다른** 키에서 FNV-1a 단독은 독립이 아니었다.
  - 독립이면 두 세션이 같은 그룹일 비율은 50%(15,000), 세 세션이 모두 같을 비율은 25%(7,500) 근처여야 한다.
  - FNV-1a 단독: 19,258(64.2%)과 4,259(14.2%). 마무리 섞기를 더하면 15,002와 7,496으로 기대에 붙는다.
  - 원인(계산으로 확인): FNV-1a는 마지막 바이트를 XOR 한 번·곱 한 번으로만 섞는다. `'0'`(0x30)과 `'1'`(0x31)은 XOR 뒤 값이 정확히 1 차이라, 곱한 뒤 두 해시는 정확히 ±P(FNV 소수 `0x100000001b3`) 차이다. P mod 10,000 = 8,211이라 두 세션의 칸은 늘 ±1,789(= 10,000 − 8,211)만큼 떨어진다. 출발 칸이 0~9,999에 고르게 퍼져 있다고 가정하면, 경계 5,000의 같은 쪽에 남을 기대 비율은 1 − 2 × 0.1789 = 64.22%다. 관측값 19,258/30,000 = 64.19%와 맞는다.
  - 결정적인 것은 칸 사이 거리(±1,789)다. 64.22%는 이 키 형식(끝 한 글자만 다름)·칸 10,000개·경계 50%에서, 출발 칸이 고르게 퍼졌다는 조건의 기대값이다. 출발 칸이 경계 근처에 몰린 키 집합이면 일치율이 달라진다. 3만 쌍 전부가 ±P 차이, 칸 차이 1,789 또는 8,211인 것을 따로 확인했다(사실 점검 `scratchpad/da/fc-14/fnv_offset.py`, 호스트 Python 3.12.3). 칸 수나 경계가 바뀌면 비율도 바뀐다.
- salt 쪽도 봤다. Python으로 Java의 부호 있는 `floorMod`를 흉내 내고, 끝 글자만 다른 salt 8쌍(`exp-0a`/`exp-0b` …)의 그룹 일치 수를 셌다(`scratchpad/da/14/saltpairs.py`, 호스트 Python 3.12.3). salt는 해시 입력(`salt|사용자 ID`)의 **앞부분**이라, 다른 바이트 뒤로 `|user_000123` 12바이트가 더 섞인다. 그래서 효과는 세션 키보다 훨씬 약하고 쌍마다 다르다.

```text
fnv  [50537, 50771, 50378, 51192, 50287, 48737, 50341, 50817]
fmix [49868, 49970, 50111, 49773, 50150, 49994, 50061, 49945]
```

  - 독립이면 일치 수는 50,000 ± 158(표준편차, 이항 근사) 근처다. 이 실험에서 FNV-1a 단독은 8쌍 중 7쌍이 2 표준편차 밖이었고, 가장 큰 쌍은 1,263 벗어났다(약 8 표준편차, 일치율 48.7%). 세션 키의 64.2%보다는 훨씬 작은 어긋남이다. 마무리 섞기 판은 모두 ±230(약 1.4 표준편차) 안이다.
  - 위 Java 출력의 `exp-checkout`/`exp-banner`(앞부분부터 다름) 쌍은 49,503·49,597이다. 각각 약 −3.1·−2.5 표준편차다. 독립 이항 근사를 받아들이면 양측 p ≈ 0.0017·0.011로, 5% 기준에서는 둘 다 우연으로 보기 어려운 편차다. 다만 쌍 하나·연속 합성 ID라 원인(해시 구조 vs 이 ID 집합의 우연)은 이 실험만으로 가르지 않는다(계산 `scratchpad/da/adj-14r/calc14.py`).
- 교훈: 해시가 "결정적"인 것과 "서로 다른 키에 독립"인 것은 다른 성질이다. 배정용 해시는 키의 앞뒤 어디가 바뀌어도 칸이 고르게 흩어지는지 시험해야 한다. 해시 함수의 섞임(avalanche)은 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).

### 3. 배정 단위와 분석 단위 — 다르면 분산을 과소평가하기 쉽다(양의 상관일 때)

```text
  배정 단위 = 사용자                       분석 단위 = 세션 (세션마다 전환 0/1)
  user_1 (B) ─ 세션 ●○○○○○○○○             세션 9개 = "독립 표본 9개"로 세면
  user_2 (A) ─ 세션 ○                      user_1의 세션들은 같은 사람의 습관을 공유한다
  user_3 (B) ─ 세션 ●●●                    → 실제 정보량은 9개보다 적다 → 표준오차가 너무 작게 나온다
```

- *배정 단위(randomization unit)*: 무작위로 나누는 단위. 사용자·세션·기기·페이지뷰·매장 등.
- *분석 단위(analysis unit)*: 지표를 계산하는 단위. "세션당 전환율"이면 세션이다.
- 둘이 같으면 표준적인 검정이 맞다. 배정 단위가 분석 단위보다 크면(사용자로 배정, 세션으로 분석) 같은 사용자의 세션끼리 상관이 있다. 그 상관이 양(+)이면(사용자마다 성향이 달라 같은 사람의 세션이 비슷한 흔한 경우, Deng 외 식 (5)의 ρ > 0) 독립을 가정한 검정은 분산을 작게 잡는다. 음의 상관이면 반대로 크게 잡을 수 있다(Deng 외 2018 3.1 문제 설정, 3.3 수치 예에서 "naive" 추정이 분산을 과소추정).
  - 배정 단위는 분석 단위보다 잘게 나눌 수 없다. 그러면 한 분석 단위 안에 A와 B가 섞인다(같은 문서 3.1).
- 대처: 분산을 배정 단위로 계산한다.
  - 비율 지표 `R = Σ전환 / Σ세션`을 "사용자별 (전환 합, 세션 합) 쌍의 평균 둘의 비"로 본다.
  - 델타 방법(Deng 외 2018 3.2 식 (6)): `Var(R) ≈ [Var(S) − 2R·Cov(S,N) + R²·Var(N)] / (K·μ_N²)`. 여기서 S·N은 사용자별 전환 합·세션 합, K는 사용자 수.
  - *델타 방법*: 평균들의 함수(여기서는 비)의 분산을, 함수를 1차 근사해 구하는 방법. 근사이며 K가 클 때 맞는다.
  - 다른 길: 사용자별 지표(사용자당 전환 수)로 바꾸면 분석 단위 = 배정 단위가 된다. 다만 질문이 바뀐다(세션당 → 사용자당).

### 실험: 사용자로 배정, 세션으로 분석 — A/A에서 거짓 양성률

효과가 없는 A/A 실험을 2,000번 만들었다. 사용자마다 전환 성향(Beta(1,9), 평균 0.1)과 세션 수(1 + 지수분포 평균 4)를 다르게 줬다.

```python
# scratchpad/da/14/e14b_unit.py 핵심
g = 'A' if rng.random() < 0.5 else 'B'          # 사용자 단위 배정, 효과 없음
p = rng.betavariate(1, 9)                         # 사람마다 다른 전환 성향
k = 1 + int(rng.expovariate(1/4))                 # 세션 수
conv = sum(rng.random() < p for _ in range(k))
# (1) 세션을 독립 베르누이로 보고 두 비율 z 검정
# (2) 같은 비율 지표를 사용자 단위 델타 방법 분산으로 z 검정
```

(시뮬레이션, 호스트 Python 3.12.3 표준 라이브러리, 사용자 2,000명 × 2,000회, seed 1·2)

```text
seed=1 users=2000 reps=2000  거짓 양성률  세션 단위 z검정 0.128   사용자 단위(델타 방법) 0.051
seed=2 users=2000 reps=2000  거짓 양성률  세션 단위 z검정 0.127   사용자 단위(델타 방법) 0.053
```

- 관찰: 유의수준 5%로 검정했는데, 세션을 독립으로 센 검정은 효과가 없는데도 약 13%의 실험에서 "유의"를 냈다. 사용자 단위 분산으로 바꾸면 5% 근처로 돌아온다.
- 2,000회 시뮬레이션의 표본 오차는 약 ±1%p(5% 근처, 2 표준편차)다. 0.051·0.053은 그 안이다.
- 해석: 13%는 이 합성 설정(성향 분산·세션 수 분포)에서의 값이다. 사용자 간 성향 차이가 크고 세션이 많은 사용자가 많을수록 더 부풀 것이다.

### 4. 지표 — 무엇을 재나

- 실험 전에 **판단 지표 하나**(또는 그 묶음)를 정한다. 끝난 뒤 여러 지표 중 유의한 것을 고르면 다중 비교다([11](../11-multiple-comparisons/2-summary.md)).
  - Kohavi·Tang·Xu(2020) 7장 제목은 "Metrics for Experimentation and the Overall Evaluation Criterion"이다(Cambridge 목차로 확인, 본문 미열람).
  - *OEC(종합 평가 기준)*: 실험의 성패를 판단하는 미리 정한 지표(들).
- *가드레일 지표*: 나빠지면 안 되는 것(지연·오류율·해지율). 판단 지표가 좋아도 가드레일이 나빠지면 내보내지 않는다. 설계는 [16 metrics-design](../16-metrics-design/2-summary.md).
- 지표의 분모를 배정 단위와 맞춘다(3절). "사용자당 매출"은 사용자 단위, "페이지뷰당 클릭"은 비율 지표라 델타 방법이 필요하다.

### 5. 기간과 표본 크기 — 얼마나 돌리나

```text
  필요한 표본 n  ∝  (z_{1-α/2} + z_{1-β})² × 분산 / (최소 탐지 효과)²
                           │                         │
                    유의수준·검정력              효과를 반으로 줄이면 n은 4배
```

- 표본 크기는 실험 **전에** 정한다. 검정력·최소 탐지 효과의 원리는 [10 power-and-sample-size](../10-power-and-sample-size/2-summary.md). OpenIntro 7.4.3은 검정력 80%(때로 90%)를 가장 흔한 목표로 든다.
  - *최소 탐지 효과(MDE)*: 이 실험이 잡아내려는 가장 작은 효과. 사업적으로 의미 있는 크기로 정한다.
- 두 비율 비교의 그룹당 n(정규 근사): `n = (z_{1-α/2}+z_{1-β})² · [p₁(1−p₁)+p₂(1−p₂)] / (p₂−p₁)²`. 근사식이다. 전환율이 아주 작거나 n이 작으면 맞지 않을 수 있다.

### 실험: 그룹당 표본 크기와 시뮬레이션 검정력

(계산·시뮬레이션, 호스트 Python 3.12.3 `statistics.NormalDist`, 검정력 시뮬레이션 seed 7·400회, `scratchpad/da/14/e14c_size.py`)

```text
기준 0.0500 → 0.0550 (상대 10%): 그룹당 n = 31,231
기준 0.0500 → 0.0525 (상대 5%): 그룹당 n = 122,121
기준 0.0500 → 0.0600 (상대 20%): 그룹당 n = 8,155
시뮬레이션 검정력(seed 7, 400회, n=31,231): 0.823
```

- 관찰: 탐지하려는 효과를 반으로 줄이면(10% → 5%) 필요한 n이 약 4배(31,231 → 122,121)가 된다.
- 근사식으로 정한 n에서 시뮬레이션 검정력은 0.823이었다. 400회의 표본 오차(약 ±0.04, 2 표준편차) 안에서 목표 0.80과 맞는다.
- 기간 = 그룹당 n ÷ 그룹당 하루 유입. 50:50 두 그룹이면 2n ÷ 전체 하루 유입이다(예시: 그룹당 31,231명, 전체 하루 유입 1만 명이면 약 6.2일). 계산이 3일이 나와도 요일 효과가 있으면 **온전한 주 단위**로 돌린다(예: 최소 1주). 월요일 사용자와 토요일 사용자가 다르기 때문이다.

신규성 효과 — 처음 며칠의 효과가 오래가지 않는다.

```text
  일별 B−A 차이 (예시 — 설명용 가정값)
  +8% │█
  +6% │█ █
  +4% │█ █ █
  +2% │█ █ █ █ █
  +1% │█ █ █ █ █ █ █ █ █ █ █ █ █ █
      └─────────────────────────────> 일
        1 2 3 4 5 6 7 ...          14
  3일 만에 멈추면 "+6%"로 보고 → 장기 효과 약 +1%
```

- *신규성 효과(novelty effect)*: 바뀐 것 자체가 눈에 띄어 처음에만 반응이 큰 현상. 반대로 익숙한 것을 바꿔 처음에 반응이 나빴다가 회복하는 것을 *초두 효과(primacy effect)*라 부른다.
- 확인: 일별(또는 노출 후 경과 일수별) 효과를 그려 본다. 기울기가 0으로 수렴하는지 본다. 신규 사용자만의 효과와 기존 사용자의 효과를 나눠 본다(신규 사용자에게는 "새로움"이 없다).
- Kohavi·Tang·Xu(2020) 23장 제목이 "Measuring Long-Term Treatment Effects"다(목차로 확인). 장기 효과 측정 방법의 세부는 본문 미열람이라 이 노트에서 다루지 않는다.

## 쓰이는 자료구조·알고리즘

| 구조·알고리즘 | 쓰임 | 이어지는 노트 |
|---|---|---|
| 해시 + mod 버킷 | 결정적 배정, 비율 경계 | [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md), [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md) |
| 마무리 섞기(fmix64) | 끝 글자만 다른 키의 상관 제거 | 위 실험 |
| 생일 한계 | salt 충돌 확률(365개 → 23개 실험에 50%) | [math/05](../../math/05-counting-and-birthday-bound/2-summary.md) |
| 의사난수 vs 해시 | 요청마다 새로 뽑는 동전(PRNG)은 같은 사용자의 배정을 고정하지 못한다(PRNG 자체는 시드·상태를 보존하면 같은 수열을 재현하지만, 그 수열이 요청 순서에 묶인다). 해시는 키만으로 재현 | [math/12](../../math/12-randomness-and-prng/2-summary.md) |
| 사용자별 (합, 개수) 집계 + 델타 방법 | 비율 지표의 분산 | 3절 |
| 블록(층) 안 무작위화 | 큰 변수의 치우침 제거 | [02 sampling-and-bias](../02-sampling-and-bias/2-summary.md)(층화 추출) |

## 적용 — 풀어나가는 법

### 1. 설계 체크리스트 (실험 시작 전)

| 정할 것 | 질문 | 틀리면 |
|---|---|---|
| 가설 | 무엇이 어느 방향으로 얼마나 바뀌어야 하나 | 끝나고 지표를 골라 "발견" |
| 배정 단위 | 사용자·기기·세션·조직 중 무엇인가. 로그인 전후로 ID가 바뀌나 | 같은 사람이 두 화면을 봄 |
| 분석 단위 | 판단 지표의 분모는 무엇인가. 배정 단위와 같은가 | 분산 과소(3절) |
| 판단 지표·가드레일 | 하나로 정했나. 나빠지면 안 되는 것은 | 다중 비교·나쁜 출시 |
| 표본·기간 | MDE·α·검정력으로 그룹당 n, (그룹당 n × 그룹 수)÷전체 유입으로 기간, 온전한 주 | 검정력 부족·요일 효과 |
| 배정 검증 | A/A 실험, SRM 검사([15](../15-ab-pitfalls-srm-peeking/2-summary.md)) | 배정 버그를 효과로 착각 |

### 2. 증상 → 원리 → 확인

- 증상: A/A 실험인데 "유의" 결과가 자주 나온다.
  - 원리: 분석 단위가 배정 단위보다 작아 분산이 과소다(3절). 또는 배정이 고르지 않다(SRM).
  - 확인: A/A를 여러 번(또는 과거 데이터에 가짜 배정을 여러 번) 돌려 p값 분포를 본다. 거짓 양성률이 α 근처인지 본다.
- 증상: 첫 주 효과가 둘째 주에 절반 이하로 준다.
  - 원리: 신규성 효과.
  - 확인: 노출 후 경과 일수별 효과, 신규/기존 사용자 분리.

### 3. SQL로 사용자 단위 집계 (PostgreSQL 17)

세션 로그를 먼저 사용자 단위로 접는다. 그다음에 그룹 비교를 한다.

```sql
-- session_log(user_id, variant, converted boolean)
WITH per_user AS (
  SELECT variant, user_id,
         count(*)                            AS sessions,
         count(*) FILTER (WHERE converted)   AS conv
  FROM session_log
  GROUP BY variant, user_id
)
SELECT variant,
       count(*)                                    AS users,
       sum(conv)::numeric / sum(sessions)          AS conv_per_session,   -- 비율 지표 R
       avg(conv)                                   AS conv_per_user,      -- 사용자 단위 지표
       var_samp(conv)                              AS var_s,
       var_samp(sessions)                          AS var_n,
       covar_samp(conv, sessions)                  AS cov_sn,
       avg(sessions)                               AS mean_n
FROM per_user
GROUP BY variant;
-- 델타 방법: Var(R) ≈ (var_s - 2*R*cov_sn + R^2*var_n) / (users * mean_n^2)
```

- 이 질의는 합성 데이터로 PostgreSQL 17.11에서 실행해 확인했다(실험 목록 참조).

## 장애 시나리오와 대처

### 1. 배정 단위 불일치로 분산 과소 (⚠ 커리큘럼)

- 현상: 사용자로 배정한 실험을 세션 단위로 분석해 "유의"로 출시했다. 다음 분기에 효과가 보이지 않는다.
- 보이는 형태: 리포트의 신뢰구간이 유난히 좁다. A/A 실험에서도 유의가 자주 뜬다(위 실험에서 5% 대신 약 13%).
- 원인: 같은 사용자의 세션은 독립이 아니다. 세션을 독립 표본으로 세면 정보량을 부풀린다.
- 대처: 분산을 배정 단위로 계산(델타 방법), 또는 지표를 배정 단위로 정의. 실험 플랫폼에 A/A 정기 실행을 둔다.

### 2. 신규성 효과를 장기 효과로 보고 (⚠ 커리큘럼)

- 현상: 3일 실험에서 +6%로 출시했는데, 한 달 뒤 지표가 거의 그대로다.
- 보이는 형태: 일별 효과 그래프가 첫날 최고에서 내려간다. 신규 사용자 부분군에서는 효과가 작거나 없다.
- 원인: 새것에 대한 호기심. 효과가 시간에 따라 바뀌는데, 짧은 실험은 초반만 본다.
- 대처: 온전한 주 단위 이상으로 돌린다. 경과 일수별 효과를 그려 수렴을 확인한다. 중요한 변경은 일부를 오래 남겨 장기 효과를 잰다(홀드아웃).

### 3. 실험 두 개가 같은 salt를 썼다

- 현상: 배너 실험과 결제 실험이 동시에 돌았다. 두 실험 모두 같은 크기의 효과가 나왔다.
- 보이는 형태: 두 실험의 B 그룹 사용자 목록이 같다(위 실험에서 10만 명 전원 일치).
- 원인: salt가 같으면 두 실험의 배정이 같다. 결제 효과와 배너 효과가 한 그룹에 겹친다.
- 대처: 실험 ID를 salt에 넣는다. 실험 시작 시 다른 실행 중 실험과의 배정 일치율을 자동 점검한다(독립이면 50:50 분할에서 약 50%).

### 4. 로그인 순간 배정 키가 바뀐다

- 현상: 익명 방문에서 A를 보던 사용자가 로그인 후 B를 본다.
- 보이는 형태: 로그인 전후 두 화면을 모두 본 사용자가 적지 않다. 이들이 양쪽 지표에 섞인다.
- 원인: 익명일 때 기기 ID, 로그인 후 회원 ID로 해시한다. 열쇠가 바뀌면 칸이 바뀐다([27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md) 규칙 1).
- 대처: 실험의 모집단을 "로그인 사용자"로 한정하거나, 기기 ID로 일관되게 배정한다. 두 화면을 다 본 사용자 수를 리포트에 표시한다.

### 5. 끝 글자만 다른 키에서 해시가 상관을 만든다

- 현상: 세션 단위 실험에서 같은 사용자의 세션들이 기대보다 자주 같은 그룹에 몰린다.
- 보이는 형태: 같은 사용자 세션 쌍의 그룹 일치율이 50% 대신 64%(위 실험, FNV-1a 단독).
- 원인: FNV-1a는 마지막 바이트를 XOR·곱 한 번으로만 섞는다. 키가 `user_7#s0`, `user_7#s1`처럼 끝 한 글자만 다르면 두 해시가 정확히 ±P 차이라 칸이 늘 같은 거리(이 실험에서 1,789칸)만큼 떨어진다.
- 대처: 마무리 섞기(fmix64 등)를 더하거나 섞임이 검증된 해시를 쓴다. 배포 전에 실제 키 형식으로 독립성 시험(일치율·χ²)을 돌린다.

## 핵심 문장

- 무작위 배정은 측정 못 한 차이까지 평균적으로 두 그룹에 고르게 나눈다. 그래서 차이가 "처리 또는 우연"으로 좁혀진다.
- 해시 배정은 결정적이어야 하고, 함께 노출해도 되는 실험끼리는 독립이어야 한다(서로 충돌하는 실험은 배타적으로 배정). 결정적인 것과 독립인 것은 다른 성질이라 따로 시험한다.
- 분석 단위가 배정 단위보다 작으면 독립 가정이 깨진다. 같은 사용자 안의 결과가 양의 상관이면(흔한 경우) 분산을 과소평가한다. 분산은 배정 단위로 계산한다.
- 판단 지표·가드레일·표본 크기·기간은 실험 전에 정한다. 기간은 온전한 주 단위로 잡는다.
- 처음 며칠의 효과는 신규성 효과일 수 있다. 경과 일수별 효과로 확인한다.

## 관련 주제·근거

선행·후속:
- 선행: [09 hypothesis-testing](../09-hypothesis-testing/2-summary.md), [10 power-and-sample-size](../10-power-and-sample-size/2-summary.md).
- 후속: [15 ab-pitfalls-srm-peeking](../15-ab-pitfalls-srm-peeking/2-summary.md), [16 metrics-design](../16-metrics-design/2-summary.md), [25 causal-inference-basics](../25-causal-inference-basics/2-summary.md)(무작위 배정을 쓸 수 없을 때), [26 bayesian-thinking](../26-bayesian-thinking/2-summary.md)(베이즈 A/B).
- 같은 영역: [03 observational-vs-experimental](../03-observational-vs-experimental/2-summary.md), [11 multiple-comparisons](../11-multiple-comparisons/2-summary.md).
- 다른 영역: [domain-modeling/advanced/27-ab-assign](../../domain-modeling/advanced/27-ab-assign/2-summary.md)(배정 모델링), [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md), [math/05-counting-and-birthday-bound](../../math/05-counting-and-birthday-bound/2-summary.md), [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md), [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md), [testing/19-testing-in-production](../../testing/19-testing-in-production/2-summary.md).

근거:
- OpenIntro Statistics 4판(https://www.openintro.org/book/os/ 무료 PDF): 1.4.1 Principles of experimental design(통제·무작위화·반복·블록화), 7.4.3 Determining a proper sample size(검정력 80%·90%가 흔한 목표). PDF 본문에서 확인.
- Kohavi·Tang·Xu, 『Trustworthy Online Controlled Experiments』, Cambridge University Press, 2020. 장 제목은 Cambridge 목차(https://www.cambridge.org/core/books/trustworthy-online-controlled-experiments/D97B26382EB0EB2DC2019A7A7B518F59)로 확인: 2장 Running and Analyzing Experiments, 3장 Twyman's Law and Experimentation Trustworthiness, 7장 Metrics for Experimentation and the OEC, 14장 Choosing a Randomization Unit, 15장 Ramping Experiment Exposure, 23장 Measuring Long-Term Treatment Effects. **본문은 열지 못했다** — 장 제목 이상의 내용은 이 책을 근거로 쓰지 않았다.
- A. Fabijan 외, "Diagnosing Sample Ratio Mismatch in Online Controlled Experiments: A Taxonomy and Rules of Thumb for Practitioners", KDD 2019, DOI 10.1145/3292500.3330722. 저자판 PDF(https://exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf) 5.1(배정 서비스의 세 요구, salt 365개·23개 실험의 생일 문제).
- A. Deng, U. Knoblich, J. Lu, "Applying the Delta Method in Metric Analytics: A Practical Guide with Novel Ideas", arXiv:1803.06336(2018), 3.1(배정 단위·분석 단위, 배정 단위는 분석 단위보다 잘게 나눌 수 없음), 3.2 식 (6)(비율 지표의 델타 방법 분산), 3.3(수치 예 — naive 추정의 분산 과소추정).

실험 목록:
- 해시 배정(재계산·분할·salt·세션 키): `scratchpad/da/14/Assign.java`, `docker run --rm --pull never --name sn-da-w14-java --cpus=2 --network none -u $(id -u):$(id -g) -e HOME=/tmp -v <scratchpad>/da/14:/w -w /w eclipse-temurin:21-jdk java Assign.java`. OpenJDK 21.0.12 Temurin, 2026-10-08.
- salt 8쌍 일치 수: `scratchpad/da/14/saltpairs.py`, 호스트 Python 3.12.3.
- 세션 키 해시 차이 ±P·칸 차이 1,789 확인(사실 점검 추가): `scratchpad/da/fc-14/fnv_offset.py`, 호스트 Python 3.12.3. 출력 `해시 차이 {'-P': 15000, '+P': 15000}`, `칸 차이 {1789: 15000, 8211: 15000}`, `같은 그룹 19258 / 30000`.
- 배정·분석 단위 불일치 A/A: `scratchpad/da/14/e14b_unit.py`, 호스트 Python 3.12.3, seed 1·2, 2,000회.
- 표본 크기·검정력: `scratchpad/da/14/e14c_size.py`, 호스트 Python 3.12.3, seed 7, 400회.
- 적용 3절 SQL: `scratchpad/da/14/e14d_peruser.sql`(같은 질의에 반올림만 더함), PostgreSQL 17.11 컨테이너(`postgres:17`, `--network none`, `docker exec -i … psql`), 합성 사용자 5,000명·세션 1~5개. 두 그룹이 각 2,507·2,493명, 세션당 전환 0.0962·0.1036으로 나왔다.
