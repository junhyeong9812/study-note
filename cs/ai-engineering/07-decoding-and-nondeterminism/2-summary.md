# ai-engineering/07-decoding-and-nondeterminism — 디코딩과 비결정성: temperature·top-p 샘플링, 배치에 따라 달라지는 greedy — 정리 (힌트)

## 해결하는 문제

모델은 한 단계에 "다음 토큰 하나"의 **점수표**만 낸다. 그중 무엇을 고를지는 모델 밖의 규칙이 정한다.

```text
  지금까지: "주문 상태는"
  모델 출력(로짓, 예시):  "배송중" 4.0 │ "완료" 3.2 │ "취소" 2.9 │ ... │ "#$%" -2.0
                              │
                    디코딩 규칙 (greedy? 샘플링? temperature? top-p?)
                              │
                              ▼
  고른 토큰을 붙이고 다음 단계로:  "주문 상태는 배송중" → 다시 모델 → ...
```

- *디코딩(decoding)*: 모델이 낸 다음 토큰 분포에서 실제 토큰을 고르는 규칙. 토큰 하나를 고르면 그것이 다음 단계의 입력이 된다(자기회귀).
- 개방형 글 생성(이야기·이어 쓰기)에서 늘 가장 높은 것만 고르면(greedy) 글이 밋밋하고 반복되기 쉽다. Holtzman 외(ICLR 2020) 초록은 우도를 최대화하는 디코딩이 "밋밋하고 이상하게 반복적인" 글을 낸다고 적는다. 같은 논문 §2.2는 번역·요약처럼 입력이 출력을 좁히는 작업에서는 반복·평범함이 그만큼 문제가 아니라고 구분한다.
- 무작위로 고르면 다양해지지만, 확률 낮은 꼬리의 엉뚱한 토큰도 가끔 뽑힌다.

쉬운 예: 칸 크기가 다른 룰렛판이다.
- 칸 크기 = 확률. 매번 가장 큰 칸만 고르면(greedy) 결과가 늘 같다. 돌리면(샘플링) 매번 다르다.
- temperature는 칸 크기 차이를 키우거나 줄이는 손잡이, top-p는 작은 칸을 판에서 떼어 내는 가위다.

똑같은 구조다.\
그리고 같은 입력에 다른 출력이 나오는 주된 원인은 **두 가지**다. (1) 일부러 돌리는 샘플링, (2) 룰렛판(로짓) 자체가 서버 상황에 따라 미세하게 달라지는 것. 이 밖에 제공자 쪽 구현 버그·백엔드 변경도 원인이 된다(아래 Anthropic 사후 분석 — "같은 프롬프트가 한 요청에서는 잘 되고 다음 요청에서는 실패").

백엔드에서 터지는 곳
- "temperature 0이면 결정적"이라 믿고 출력 문자열을 스냅샷 테스트 → 가끔 실패([testing/09-flaky-tests](../../testing/09-flaky-tests/2-summary.md)).
- 출력 문자열로 캐시 키·중복 판정 → 재실행마다 불일치.
- temperature를 높이고 top-p도 1로 두어 긴 출력에 깨진 문자·무관한 단어가 섞임.

## 동작·원리

### 1. 한 단계의 디코딩 파이프라인

```text
  로짓 z (어휘 크기만큼)
     │  ① temperature:  p_i = exp(z_i / T) / Σ_j exp(z_j / T)
     ▼
  확률 p
     │  ② 절단:  top-k (상위 k개)  또는  top-p (누적 ≥ p인 최소 집합)  — 나머지 0
     │  ③ 재정규화: 남은 확률의 합이 1이 되게 나눔
     ▼
  확률 p'
     │  ④ 뽑기:  u ~ U[0,1),  누적합이 처음 u를 넘는 칸 (역CDF)
     ▼
  토큰 1개  →  입력 끝에 붙여 다음 단계
```

- ① temperature(Holtzman 외 식 4): T < 1은 분포를 뾰족하게(높은 칸이 더 커짐), T > 1은 평평하게 만든다. T → 0이면 최댓값이 하나일 때 그 토큰에 확률이 몰려 greedy와 같아진다. 최댓값이 동점이면 동점 토큰들에 확률이 나뉘어 남는다(예: 로짓 [4, 4, 3] → 1/2·1/2·0).
  - *로짓(logit)*: softmax에 들어가기 전의 점수. 크기만 의미가 있고 합이 1이 아니다.
  - softmax와 엔트로피의 관계(평평할수록 엔트로피가 크다)는 [math/14](../../math/14-information-theory-basics/2-summary.md).
- ② top-k(Fan 외 2018에서 대중화 — Holtzman 3.2절 인용)는 늘 k개를 남긴다. 분포가 뾰족하든 평평하든 k는 같다.
- ② top-p(*nucleus sampling*, Holtzman 외 식 2): 확률 순으로 더해 누적이 p 이상이 되는 **가장 작은 집합**만 남긴다. 분포가 뾰족하면 몇 개, 평평하면 많이 남는다.

```text
  top-p = 0.9, T = 1.5 (아래 실험의 분포)

  토큰:   200    OK     성공   완료   됨     fine   바나나  #$%
  확률:  .382   .224   .184   .101   .052   .037   .014   .007
  누적:  .382   .606   .790   .891   .943 ← 처음으로 ≥ 0.9  → 여기까지 5개 남김
                                          │ fine·바나나·#$% 는 0
```

- ④ 뽑기는 시드가 있는 의사난수로 한다([math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md)). 서버 쪽 시드를 고정할 수 없으면 같은 확률표에서도 결과가 매번 다르다.

### 실험: 같은 로짓, 다른 설정 → 다른 출력 빈도

- 무엇: 후보 8개의 고정 로짓(예시)에 temperature·top-p 조합 6가지를 적용하고 각 1만 번 뽑았다. 꼬리 2개(바나나·#$%)가 뽑힌 비율을 셌다.
- 코드 핵심(`exp/07/sampling.py`):

```python
def nucleus(p, top_p):
    order = sorted(range(len(p)), key=lambda i: -p[i])     # 확률 내림차순 정렬
    keep, acc = [], 0.0
    for i in order:
        keep.append(i); acc += p[i]
        if acc >= top_p:                                    # 누적이 처음 top_p 이상 → 멈춤
            break
    s = sum(p[i] for i in keep)
    return [p[i] / s if i in keep else 0.0 for i in range(len(p))]   # 재정규화

def sample(p, rng):                                         # 역CDF
    u, acc = rng.random(), 0.0
    for i, x in enumerate(p):
        acc += x
        if u < acc:
            return i
```

(실험, Python 3.12 `python:3.12-slim`, Docker `--network none --cpus=2`, 2026-10-08 — seed 7, 2회 실행 출력 동일)

```text
로짓 [4.0, 3.2, 2.9, 2.0, 1.0, 0.5, -1.0, -2.0], 표본 10000회, seed=7
  softmax T=0.2: 0.978 0.018 0.004 0.000 0.000 0.000 0.000 0.000
  softmax T=1.0: 0.498 0.224 0.166 0.067 0.025 0.015 0.003 0.001
  softmax T=1.5: 0.382 0.224 0.184 0.101 0.052 0.037 0.014 0.007
설정                      200     OK     성공     완료      됨   fine    바나나    #$%    꼬리2개
T=0.2  top_p=1.0         9782    178     39      1      0      0      0      0   0.00%
T=0.7  top_p=1.0         6214   1999   1286    371     83     44      2      1   0.03%
T=1.0  top_p=1.0         5018   2202   1655    669    261    149     40      6   0.46%
T=1.5  top_p=1.0         3880   2201   1808   1015    514    380    135     67   2.02%
T=1.5  top_p=0.9         4093   2340   1961   1052    554      0      0      0   0.00%
T=1.0  top_p=0.5         6885   3115      0      0      0      0      0      0   0.00%
greedy(argmax)는 설정과 무관하게 항상 '200' — 단, 로짓 자체가 같을 때만
```

- 관찰 1: 같은 로짓에서 T만 0.2 → 1.5로 올리니 1위 토큰 비율이 97.8% → 38.8%로 떨어졌다. 꼬리 2개 비율은 0% → 2.02%.
- 관찰 2: T=1.5라도 top-p 0.9를 걸면 꼬리 3개(fine·바나나·#$%)가 0회다. 위 누적 그림대로 5개만 남았다.
- 관찰 3: top-p 0.5는 1위(0.498)만으로는 0.5에 못 미쳐 2개를 남겼다. 경계 근처의 확률 한 자리 차이가 남는 집합을 바꾼다.
- 해석: 한 단계 2%는 작아 보이지만, 매 단계 같은 분포라고 단순화하면 200토큰 출력에서 꼬리 토큰이 한 번 이상 나올 확률은 `1 − 0.9798^200 ≈ 98%`다(예시 계산).

### 2. 원인 2 — greedy인데도 다른 출력: 배치 불변성

```text
  같은 요청 X
  ┌─ 한가한 시간: 배치 크기 1 ─────┐        ┌─ 붐비는 시간: 배치 크기 8 ─────┐
  │ 행렬곱 리덕션을 한 줄로 누적     │        │ 리덕션을 여러 조각으로 나눠 누적 │
  │ logit("Queens")   = 7.12345678 │        │ logit("Queens")   = 7.12345671 │
  │ logit("New York") = 7.12345675 │        │ logit("New York") = 7.12345673 │
  │ argmax → "Queens"              │        │ argmax → "New York"            │
  └───────────────────────────────┘        └───────────────────────────────┘
           (수치는 예시)                    한 토큰이 달라지면 그 뒤 생성 전체가 갈라진다
```

- 부동소수 덧셈은 결합법칙이 성립하지 않는다(`(a+b)+c ≠ a+(b+c)`). 같은 수를 다른 순서·묶음으로 더하면 마지막 자리가 달라진다. 원리는 [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md)가 단일 출처다.
- He·Thinking Machines Lab(2025-09-10)의 주장
  - 흔한 설명 "동시성 + 부동소수"(어느 코어가 먼저 끝나느냐)는 전부가 아니다. 같은 행렬곱을 반복하면 비트까지 같다(run-to-run 결정적).
  - 진짜 원인은 **배치 불변성(batch invariance)의 부재**다. 커널이 배치 크기에 따라 리덕션 전략(예: split-K)을 바꾸면, 내 요청의 결과가 같이 묶인 다른 요청 수에 따라 달라진다.
  - 서버의 배치 크기는 다른 사용자의 부하로 정해진다. 그래서 사용자 입장에서는 비결정적이다.
  - *배치 불변성*: 배치에 몇 개가 함께 들어 있든, 각 요소의 계산 결과가 비트 단위로 같은 성질.
- 같은 글의 실험: Qwen3-235B, temperature 0, 같은 프롬프트로 1,000개 완성(각 1,000토큰) → **서로 다른 완성 80개**, 가장 흔한 것이 78회. 102토큰까지 모두 같았고 103번째에서 처음 갈렸다(992개 "Queens, New York", 8개 "New York City"). 배치 불변 커널을 켜자 1,000개가 모두 같았다.

### 실험: 리덕션 분할만 바꾼 float32 내적에서 greedy 1위 뒤집힘

- 무엇: 1,024차원 float32 내적을 (a) 한 줄로 누적, (b) 8구간으로 나눠 각자 누적한 뒤 합침. 거의 동점인 후보 쌍 2,000개(두 번째 가중치 = 첫째 + N(0, 1e-4) 잡음)에서 로짓 값과 1위가 바뀌는지 셌다. float32 반올림은 `struct`로 흉내 냈다.

```python
def dot32(a, b, chunks):            # chunks개 구간으로 나눠 누적 (split reduction)
    ...
        for i in range(c * step, (c + 1) * step):
            s = f32(s + f32(a[i] * b[i]))
    ...
a1, a2 = dot32(h, w1, 1), dot32(h, w2, 1)     # 배치 작을 때: 한 줄 누적
b1, b2 = dot32(h, w1, 8), dot32(h, w2, 8)     # 배치 클 때: 8구간 분할 누적
flips += ((a1 > a2) != (b1 > b2))
```

(실험, 같은 환경, seed 11)

```text
[부동소수 덧셈 순서] 같은 숫자들을 다른 묶음으로 더하면 (float32 누적 모형)
  (0.1 + 1e20) - 1e20 = 0.0,  0.1 + (1e20 - 1e20) = 0.1
  거의 동점 후보 쌍 2000개 (차원 1024, seed=11): 로짓 값이 달라진 경우 1906, greedy 1위가 뒤집힌 경우 4
```

- 관찰: 입력·가중치가 비트까지 같은데 누적 묶음만 달라도 로짓이 95%(1,906/2,000) 경우에 달라졌다. 그중 거의 동점이던 4쌍은 **greedy 1위가 바뀌었다.**
- 해석: 실제 모델에서는 매 단계 어휘 수만큼의 후보가 있고 출력이 수백 토큰이다. 한 단계라도 1위가 바뀌면 그 뒤가 전부 갈라진다. 위 1,000회 중 80개 완성이라는 공개 실험과 같은 방향이다.

### 3. 제공자가 노출하는 손잡이 — 벤더마다 다르다 (2026-10-08 확인)

| | Anthropic Messages API | OpenAI Chat Completions |
|---|---|---|
| temperature | 기본 1.0, 범위 0.0~1.0. "0.0이어도 완전히 결정적이지 않다"고 명시. **Opus 4.6보다 뒤에 출시된 모델은 1.0 외 값을 400으로 거부**(deprecated) | 범위 0~2. temperature와 top_p 중 하나만 바꾸라고 권장 |
| top_p | Opus 4.6보다 뒤에 출시된 모델은 0.99 이상만 허용, 그 외 400 | 지원, 위와 같은 권장 |
| top_k | Opus 4.6보다 뒤에 출시된 모델은 값을 주면 400 | 없음(`top_logprobs`는 0~20, 로그 확률 반환용) |
| 재현 수단 | 문서에 없음 | `seed`(Deprecated·Beta, best effort, 결정성 보장 안 함) + `system_fingerprint`(역시 Deprecated)로 백엔드 변경 감지 |

- 결론: 제공자 API에서 "같은 입력 → 같은 출력"을 계약으로 기대할 근거가 없다. 재현이 필요하면 **출력을 저장**한다.
- 디코딩 단계 자체가 서버 버그로 깨진 사례도 있다. Anthropic 사후 분석(2025-09-17)의 세 번째 버그: 2025-08-25 샘플링 코드 변경이 XLA:TPU 컴파일러의 잠재 버그를 드러내, 근사 top-k가 특정 배치 크기·모델 설정에서 완전히 틀린 결과를 냈다. 그 배경에는 bf16/fp32 혼합 정밀도 때문에 최고 확률 토큰이 가끔 빠지던 문제(2024-12 우회책으로 가려져 있었다)가 얽혀 있다. 정확 top-k로 바꾸고 일부 연산을 fp32로 통일했다. 각주는 "top-p 경계 근처 토큰의 포함 여부가 약간 달라질 수 있다"고 적는다.

## 쓰이는 자료구조·알고리즘

- **softmax의 수치 안정화** — 지수 전에 최댓값을 뺀다(실험 코드 `m = max(z)`). 분자·분모에 같은 `exp(−m)`이 곱해져 값은 그대로이고, 지수의 인자가 0 이하라 큰 로짓에서도 넘치지 않는다. 부동소수 오차 일반은 [math/15](../../math/15-numerical-stability/2-summary.md).
- **정렬 + 누적합 절단(nucleus)** — 확률 내림차순 정렬 O(V log V) 뒤 누적합이 p를 넘는 지점에서 자른다. 실제 서버는 전체 정렬 대신 부분 선택(top-k)을 먼저 쓰기도 한다 — 위 사후 분석의 "근사 top-k"가 그 최적화다.
- **역CDF 가중 무작위 선택** — 누적합 배열에서 u가 처음 넘는 칸. 선형 탐색 O(V), 누적합에 이진 탐색이면 O(log V).
- **시드 PRNG** — 같은 시드 = 같은 u 나열. 로짓이 같을 때만 같은 출력을 보장한다([math/12](../../math/12-randomness-and-prng/2-summary.md)).
- **부동소수 리덕션 순서** — 결합법칙 부재 때문에 리덕션 분할 전략이 결과를 바꾼다. 배치 불변 커널은 행렬곱에서는 모든 모양에 한 커널 설정을 쓰고, 어텐션(split-KV)에서는 분할 개수 대신 분할 크기를 고정해 순서를 고정한다(Thinking Machines 글의 "fixed split-size").

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상 | 원리 | 확인 |
|---|---|---|
| temperature 0 스냅샷 테스트가 가끔 실패 | 배치 불변성 부재로 로짓이 흔들리고, 동점 근처에서 1위가 바뀜 | 같은 요청을 N회 보내 서로 다른 출력 수를 센다(공개 실험: 1,000회 → 80개) |
| 같은 질문인데 중복 판정·캐시가 안 맞음 | 출력 문자열을 키로 씀 | 키가 입력(모델·프롬프트 버전·파라미터·입력 해시)인지 확인 |
| 긴 출력 끝부분에 깨진 문자·무관한 단어 | 높은 T + top-p 1 → 꼬리 토큰이 길이만큼 누적 | 출력 길이별 이상 문자 비율, 요청 파라미터 로그 |
| 모델 업그레이드 뒤 요청이 400 | 새 모델이 temperature·top_p·top_k 설정을 거부(Anthropic, Opus 4.6보다 뒤에 출시된 모델) | 오류 메시지·요청 파라미터, 모델별 파라미터 호환표 |

### 2. 코드 — 재현은 저장으로, 검증은 계약으로 (Java 21)

```java
// 1) 재현이 필요하면 다시 생성하지 말고, 처음 생성한 것을 "입력 키"로 저장한다
record GenKey(String model, String promptVersion, String paramsJson, String inputSha256) {}
static final Map<GenKey, String> store = new ConcurrentHashMap<>();

static String generateOnce(GenKey key, Supplier<String> llmCall) {
    return store.computeIfAbsent(key, k -> llmCall.get());   // 출력 문자열은 키가 아니라 값
}

// 2) 테스트는 문자열 일치가 아니라 계약(형식·필수 사실)을 검사한다
static final Pattern ORDER_STATUS = Pattern.compile("주문\\s*(\\d+).*(배송중|배송완료|취소)");
static boolean satisfiesContract(String out, String orderId) {
    var m = ORDER_STATUS.matcher(out);
    return m.find() && m.group(1).equals(orderId);
}
```

(실험, OpenJDK 21.0.12 `eclipse-temurin:21-jdk`, 2026-10-08 — 모형 출력 3개로 실행)

```text
equals(첫 출력)=true  contract=true  | 주문 1001은 현재 배송중입니다.
equals(첫 출력)=false contract=true  | 고객님의 주문 1001: 배송중
equals(첫 출력)=false contract=true  | 주문1001 상태는 배송중이에요
generateOnce -> 주문 1001은 현재 배송중입니다.
generateOnce -> 주문 1001은 현재 배송중입니다.
generateOnce -> 주문 1001은 현재 배송중입니다.
실제 LLM 호출 수 = 1
```

- 문자열 일치(`equals`)는 3개 중 1개만 통과, 계약 검사는 3개 모두 통과한다. 형식이 중요한 출력은 구조화 출력·스키마 검증으로 계약을 강하게 만든다([14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md)).
- 품질 판정(뜻이 맞나)은 문자열로 못 한다. 평가셋과 채점기로 분포를 본다([19-llm-evaluation](../19-llm-evaluation/2-summary.md)).

### 3. 파라미터를 고르는 순서

1. 제공자·모델 문서에서 지원 파라미터와 범위를 확인한다. 모델을 바꾸면 다시 확인한다(위 표).
2. 사실 추출·분류처럼 다양성이 필요 없는 작업은 낮은 T(지원되면) 또는 기본값 + 구조화 출력. 다양성이 필요한 작업은 T 또는 top-p 중 **하나만** 조정한다(OpenAI 권장).
3. 결정성은 파라미터로 얻지 않는다. 필요하면 출력을 저장하고, 테스트는 계약·분포로 검사한다.

## 장애 시나리오와 대처

### 1. temperature 0 스냅샷 테스트의 간헐 실패 (⚠)

- **현상**: CI에서 LLM 출력 스냅샷 테스트가 가끔 빨개지고, 재실행하면 초록이 된다.
- **보이는 형태**: 기대 문자열과 앞부분은 같고 중간 어느 지점부터 다르다. 실패 비율이 시간대(서버 부하)에 따라 달라진다.
- **원인**: temperature 0이어도 서버의 배치 구성이 바뀌면 로짓 마지막 자리가 흔들리고, 동점 근처에서 1위가 바뀐다(공개 실험: 1,000회 중 80개 서로 다른 완성, 103번째 토큰에서 처음 갈림). Anthropic 문서도 "0.0이어도 완전히 결정적이지 않다"고 적는다.
- **대처**: 스냅샷 대신 계약 검사(형식·필수 사실). 외부 LLM 호출은 단위 테스트에서 녹화된 응답으로 대체한다. 품질은 평가셋으로 분포를 본다([testing/09-flaky-tests](../../testing/09-flaky-tests/2-summary.md)).

### 2. 출력 문자열을 캐시 키·중복 판정에 사용 (⚠)

- **현상**: 같은 문의를 다시 처리하면 "새 항목"으로 저장되고, 캐시 적중률이 0에 가깝다.
- **보이는 형태**: 뜻이 같은 출력이 표현만 달라 여러 행으로 쌓인다.
- **원인**: 출력은 샘플링·배치 불변성 부재로 매번 다를 수 있다. 출력 기반 키는 같은 입력에도 바뀐다.
- **대처**: 키는 입력 쪽(모델·프롬프트 버전·파라미터·입력 해시)으로 만든다. 첫 출력을 값으로 저장해 재사용한다(위 `generateOnce`). 뜻 기반 중복은 임베딩 유사도로 따로 판정한다([05](../05-embeddings-and-similarity/2-summary.md)).

### 3. 높은 temperature + top-p 1 → 확률 꼬리의 무관한 토큰 (⚠)

- **현상**: 긴 답의 뒷부분에 엉뚱한 단어·기호·다른 언어 문자가 섞인다.
- **보이는 형태**: 짧은 답에서는 드물고 출력이 길수록 잦다.
- **원인**: 꼬리를 자르지 않으면 단계마다 작은 확률로 꼬리 토큰이 뽑히고, 그 확률이 출력 길이만큼 쌓인다(실험: 단계당 2.02%, 200토큰이면 한 번 이상 약 98% — 매 단계 같은 분포라는 단순화).
- **대처**: T를 낮추거나 top-p로 꼬리를 자른다(실험: T=1.5 + top-p 0.9에서 꼬리 0회). 둘을 동시에 크게 바꾸지 않는다. 지원 여부는 모델별로 확인한다.

### 4. 모델 업그레이드 뒤 샘플링 파라미터가 400으로 거부

- **현상**: 모델 ID만 새 것으로 바꿨는데 모든 요청이 실패한다.
- **보이는 형태**: HTTP 400. 요청에 `temperature: 0.2`·`top_k`·`top_p: 0.9` 같은 값이 있다.
- **원인**: Anthropic Messages API에서 Opus 4.6보다 뒤에 출시된 모델은 temperature 1.0 외 값, top_p 0.99 미만, top_k를 거부한다(2026-10-08 확인 — 벤더·모델별 동작).
- **대처**: 모델별 파라미터 호환표를 설정으로 두고, 모델 교체 시 계약 테스트로 확인한다. 실패를 재시도하지 않는다(400은 재시도로 안 낫는다 — [11](../11-llm-api-client-contract/2-summary.md)).

### 5. 서버 쪽 디코딩 버그로 품질 저하

- **현상**: 우리 코드·프롬프트는 그대로인데 특정 기간 출력 품질이 떨어지고, 엉뚱한 언어 문자가 나온다.
- **보이는 형태**: 사용자 신고·평가 점수 하락이 특정 날짜부터 시작한다.
- **원인**: 제공자 쪽 샘플링 구현 문제일 수 있다. Anthropic 사후 분석(2025-09-17): 샘플링 코드 변경이 드러낸 근사 top-k XLA:TPU 컴파일러 버그(특정 배치 크기·모델 설정에서 틀린 결과, 혼합 정밀도 문제와 얽힘).
- **대처**: 고정 평가셋을 주기적으로 돌려 날짜별 점수를 남긴다([19](../19-llm-evaluation/2-summary.md)). 이상 문자 비율 같은 출력 지표를 둔다. 제공자 상태 페이지·공지와 대조한다. 사례 정리는 [26-ai-incidents](../26-ai-incidents/2-summary.md).

## 핵심 문장

- 모델은 다음 토큰의 점수표만 내고, 무엇을 고를지는 디코딩 규칙(greedy·temperature·top-k·top-p)이 정한다.
- temperature는 분포의 뾰족함을, top-p는 누적 확률 p까지의 최소 집합만 남겨 꼬리를 자른다. 같은 로짓에서도 설정에 따라 출력 빈도가 크게 다르다.
- 같은 입력 다른 출력의 원인은 둘이다. 일부러 하는 샘플링, 그리고 서버 배치 구성에 따라 리덕션 순서가 바뀌어 로짓 자체가 흔들리는 것(배치 불변성 부재).
- temperature 0은 결정성의 계약이 아니다. 재현이 필요하면 출력을 입력 키로 저장하고, 테스트는 문자열 대신 계약과 분포를 검사한다.
- 샘플링 파라미터의 지원 범위는 벤더·모델마다 다르고 바뀐다. 모델 교체 때 다시 확인한다.

## 관련 주제·근거

- 선행
  - [06-transformer-and-attention](../06-transformer-and-attention/2-summary.md) — 로짓이 어디서 나오나(동작 수준)
  - [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md) — 시드와 의사난수
- 연결
  - [math/14-information-theory-basics](../../math/14-information-theory-basics/2-summary.md) — 엔트로피(단일 출처)
  - [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) — 부동소수 결합법칙 부재, 합산 순서(단일 출처)
  - [testing/09-flaky-tests](../../testing/09-flaky-tests/2-summary.md) — 간헐 실패 테스트
  - [04-tokenization-and-token-cost](../04-tokenization-and-token-cost/2-summary.md) · [05-embeddings-and-similarity](../05-embeddings-and-similarity/2-summary.md) · [14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md) · [19-llm-evaluation](../19-llm-evaluation/2-summary.md) · [26-ai-incidents](../26-ai-incidents/2-summary.md)
- 논문·글
  - Holtzman 외, "The Curious Case of Neural Text Degeneration", ICLR 2020 — 식 2 top-p 어휘(누적 ≥ p인 최소 집합), 3.2 top-k(Fan 외 2018 인용), 3.3 식 4 temperature softmax <https://arxiv.org/abs/1904.09751>
  - He·Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference"(2025-09-10) — "동시성 + 부동소수" 가설 비판, 배치 불변성, split-K·split-KV, Qwen3-235B temperature 0 1,000회 → 80개, 103번째 토큰에서 갈림, 배치 불변 커널로 1,000개 동일 <https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/>
  - Anthropic, "A postmortem of three recent issues"(2025-09-17) — 근사 top-k XLA:TPU 컴파일러 버그, 정확 top-k로 전환, top-p 경계 각주 <https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues>
- 교재: Jurafsky·Martin, 『Speech and Language Processing』 3판 초안(2026-08-19판) 7장 Transformers and Pretraining(디코딩·샘플링 포함) <https://web.stanford.edu/~jurafsky/slp3/>
- 문서 (2026-10-08 확인)
  - Anthropic API reference "Create a Message" — temperature 기본 1.0·범위 0~1·"0.0이어도 완전히 결정적이지 않음", Opus 4.6보다 뒤에 출시된 모델의 temperature·top_p·top_k 제한 <https://platform.claude.com/docs/en/api/messages/create>
  - OpenAI API reference "Create chat completion" — temperature 0~2, temperature·top_p 둘 중 하나만 조정 권장, `seed`(Deprecated·Beta·best effort), `system_fingerprint`(Deprecated) <https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create>
- 실험 목록
  - temperature·top-p 샘플링 분포 시뮬레이션(8후보 × 6설정 × 1만 회) — Python 3.12 `python:3.12-slim`, seed 7, 2회 실행 동일
  - float32 리덕션 분할(1구간 vs 8구간)과 greedy 1위 뒤집힘(2,000쌍, 1,024차원) — 같은 환경, seed 11
  - 출력 저장(입력 키)·계약 검사 — OpenJDK 21.0.12 `eclipse-temurin:21-jdk`
