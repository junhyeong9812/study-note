# ai-engineering/03-cross-entropy-and-perplexity — 교차 엔트로피 = 평균 NLL, perplexity와 토큰 단위 — 정리 (힌트)

## 해결하는 문제

파인튜닝 보고서에 "val loss 1.98", 모델 비교표에 "perplexity A 7.2, B 2.7"이 있다. B가 훨씬 좋은 모델일까?

```text
  같은 모델, 같은 텍스트, 같은 확률
    단어 단위로 세면     400토큰   perplexity 7.2452
    두 조각씩 세면       800토큰   perplexity 2.6917     ← 숫자만 보면 "훨씬 좋다"
    바이트당 비트로 세면           0.4840 = 0.4840       ← 사실은 같다          (실험 B)
```

- 언어 모델의 손실(loss)·perplexity는 **토큰마다 평균**한 값이다. 토큰을 어떻게 자르느냐(토크나이저)가 바뀌면 같은 예측 능력이라도 숫자가 달라진다.
- 그리고 확률 0이 한 번만 나와도 손실은 무한이 된다.

쉬운 예: 일기예보 채점.
- 매일 "비 올 확률"을 말하고, 실제 날씨에 준 확률의 로그로 채점한다. 비 온 날 90%라고 했으면 −log 0.9 ≈ 0.105점 벌점, 10%라고 했으면 −log 0.1 ≈ 2.303점 벌점.
- "0%"라고 했는데 비가 오면 벌점은 무한이다.
- 하루 단위로 평균하느냐 반나절 단위로 평균하느냐에 따라 "하루 평균 벌점"과 "반나절 평균 벌점"은 다른 숫자다.

똑같은 구조다.\
날씨 = 실제 다음 토큰, 예보 확률 = 모델이 그 토큰에 준 확률, 채점 단위 = 토큰.

실무 예:
- 토크나이저가 다른 두 모델의 perplexity를 나란히 놓고 고른다 → 단위가 달라 결론이 무의미하다(⚠).
- 자체 평가 코드에서 `log(0)` 한 번으로 평균 손실이 `Infinity`, 순진한 softmax로 `NaN`이 나온다(실험 C·D).

## 동작·원리

### 1. 토큰마다 정답 토큰의 확률에 −log

```text
  문맥                 정답 다음 토큰   모델이 정답에 준 확률 p   NLL = −ln p
  "요청이"             "지연"           0.50                      0.693
  "요청이 지연"        "되어"           0.80                      0.223
  "요청이 지연되어"    "재시도"         0.05                      2.996   ← 놀란 만큼 크다
  ─────────────────────────────────────────────────────────────────────
  평균 NLL = (0.693 + 0.223 + 2.996)/3 = 1.304 nats      (예시 확률)
  perplexity = e^1.304 = 3.68
```

- *NLL(negative log-likelihood, 음의 로그우도)*: 정답에 준 확률의 음의 로그. 확률 1이면 0, 확률이 작을수록 커진다.
- 텍스트 전체 확률은 토큰 확률의 곱이다. 로그를 쓰면 곱이 합이 되고, 아주 작은 수의 곱이 0.0으로 사라지는 언더플로를 피한다(SLP3 3.1.3, 실험 A).
- 이 영역에서 `log`는 자연로그(ln)다. 단위는 nats. 밑 2를 쓰면 bits이고 `bits = nats / ln 2`.

### 2. 교차 엔트로피 = 학습이 줄이는 손실

```text
  H(P, Q) = −E_{x∼P} log Q(x)  =  H(P)  +  D_KL(P‖Q)
            데이터 분포 P에서 뽑은 정답에    줄일 수 없는 몫     모델이 데이터와
            모델 Q가 준 확률의 평균 NLL      (데이터 자체의 불확실성)  어긋난 몫(≥ 0)
```

- *교차 엔트로피(cross-entropy)*: P에서 나온 사건을 Q의 확률로 채점했을 때 평균 NLL. Goodfellow 외 3.13 식 3.51.
- H(P)는 Q와 무관하다. 그래서 Q에 대해 교차 엔트로피를 줄이는 것은 KL 발산을 줄이는 것과 같다(Goodfellow 외 3.13).
- 엔트로피·KL의 정의와 부호화 하한은 [math/14](../../math/14-information-theory-basics/2-summary.md)가 단일 출처다.
- Goodfellow 외 6.2.1.1: 최대 우도로 학습하면 비용 함수는 NLL이고, 이는 학습 데이터와 모델 분포 사이의 교차 엔트로피와 같다. 학습 로그의 "loss"가 대개 이것이다.
- 데이터에서 계산하는 값은 시험 텍스트 N개 토큰의 **평균 NLL**이다. SLP3 3.7 식 3.42는 충분히 긴 시퀀스로 교차 엔트로피를 근사한다.

### 3. perplexity = exp(평균 NLL)

```text
  perplexity(W) = P(w₁…w_N)^(−1/N)  =  exp( (1/N) Σ −ln P(wᵢ | w<ᵢ) )  =  2^(bits/토큰)
                  확률의 N제곱근의 역수     평균 NLL(nats)의 지수              같은 값
```

- *perplexity(PPL)*: 시험 텍스트 확률의 역수를 토큰 수로 정규화한 값(SLP3 3.3 식 3.14). 낮을수록 좋다.
- SLP3 7.7.1: 텍스트의 perplexity는 그 텍스트의 평균 교차 엔트로피 손실의 지수(exp)다. 3.7 식 3.42는 밑 2로 같은 것을 쓴다.
- 직관: "매 토큰 평균 몇 갈래 중에서 고르는 셈인가". SLP3 3.3.1은 이를 가중 평균 분기 계수(weighted average branching factor)라 부른다.
- SLP3 3.3: perplexity를 계산하는 언어 모델은 시험셋을 몰라야 한다. 알면 인위적으로 낮아진다(누설 — [01](../01-ml-in-one-page/2-summary.md)).

### 실험: 평균 NLL·perplexity·bits가 같은 것을 가리키는지 (실험 A)

10개 단어 어휘(가중치 고정)에서 학습 5,000·시험 400토큰을 뽑고, 단어 유니그램 모델(add-1 평활)을 맞춘다.

```python
# scratchpad ai/01/e03/ppl.py 핵심
p_word = {w: (c[w] + 1) / (len(train) + V) for w in VOCAB}   # add-1 평활
nll = [-math.log(p_word[w]) for w in test]
ce = sum(nll) / len(nll)                                       # 평균 NLL (nats)
print(math.exp(ce), 2 ** (ce / math.log(2)))
```

(실험, Python 3.12.14 python:3.12-slim 컨테이너, 2026-10-08 — seed 3)

```text
[A] 단어 유니그램(add-1), 학습 5000·시험 400토큰, seed 3
    교차 엔트로피(평균 NLL) = 1.9803 nats = 2.8570 bits
    exp(평균 NLL) = 7.2452   (Π p)^(-1/N) = 7.2452   2^bits = 7.2452
    확률을 직접 곱하면 Π p = 0.0  (언더플로 — 로그 공간에서 더해야 하는 이유)
```

- 관찰 1: 세 식이 같은 7.2452다(같은 양을 다르게 쓴 것). nats → bits는 ln 2로 나누면 된다.
- 관찰 2: 400개 확률을 그냥 곱하면 `0.0`이다. 텍스트 확률 자체는 e^(−792) 수준이라 double로 표현할 수 없다.

### 4. 토큰 단위가 다르면 perplexity를 비교할 수 없다

```text
  텍스트 "서버 응답 …"  전체 log P = −792.13  (모델이 텍스트에 준 확률은 하나)
       ÷ 400 단어토큰   → 평균 NLL 1.98 → PPL 7.25
       ÷ 800 조각토큰   → 평균 NLL 0.99 → PPL 2.69  (= √7.25)
       ÷ 2361 바이트    → 0.484 bits/바이트 (토크나이저와 무관한 분모)
```

- SLP3 3.3: 두 언어 모델의 perplexity는 **어휘가 같을 때만** 비교할 수 있다.
- SLP3 7.7.1: perplexity는 텍스트의 토큰 수에 의존하므로 토크나이저 차이에 매우 민감하다. 토크나이저가 같은 모델끼리 비교할 때 가장 잘 쓰인다.
- 분모를 토크나이저와 무관한 단위(바이트·문자)로 바꾸면 비교 가능한 수가 된다. *bits per byte*는 텍스트 전체 NLL(bits)을 UTF-8 바이트 수로 나눈 것이다(정의 — 실험 B의 식).
- 한글 음절(가~힣)은 UTF-8에서 글자당 3바이트다(공백·ASCII는 1바이트 — [architecture/04](../../architecture/04-character-encoding-unicode/2-summary.md)). 분모가 문자인지 바이트인지도 함께 적는다.

### 실험: 같은 모델, 토큰 단위만 바꾸기 (실험 B)

실험 A의 단어 모델을 그대로 두고, 각 단어를 "첫 글자 + 나머지" 두 토큰으로 센다. `P(첫 글자) · P(나머지 | 첫 글자) = P(단어)`가 되게 확률을 나눴으므로 텍스트 전체 확률은 그대로다.

```python
def logp_sub(w):  # P(첫 조각) · P(나머지 | 첫 조각) = P(단어)
    return math.log(p_first[w[0]]) + math.log(p_word[w] / p_first[w[0]])
```

(실험, Python 3.12.14 python:3.12-slim 컨테이너, 2026-10-08 — seed 3)

```text
[B] 같은 모델, 같은 시험 텍스트 — 토큰 단위만 다르게 센다
    텍스트 전체 log P: 단어 단위 -792.1346, 2조각 단위 -792.1346
    단위            토큰 수      PPL/토큰      bits/바이트
    단어             400      7.2452        0.4840
    2조각            800      2.6917        0.4840
    UTF-8 바이트 수 2361 (한글 단어 1글자 = 3바이트)
```

- 관찰: 예측 능력은 똑같은데 토큰당 perplexity가 7.25 → 2.69로 "개선"된다. 토큰이 2배라 평균 NLL이 절반, PPL은 제곱근이다.
- 바이트당 비트는 0.4840으로 같다. 토크나이저가 다른 모델은 이런 정규화 없이 PPL을 비교하지 않는다.

### 5. 확률 0과 수치 넘침

```text
  log(0) = −∞  →  NLL = +∞  →  평균 손실 = ∞           (한 토큰만 0이어도)
  softmax 순진 구현:  exp(1000) = ∞ → ∞/∞ = NaN
                      exp(−1000) = 0 → 0/0 = NaN,  exp(−800)/1 = 0 → log 0 = −∞
  log-sum-exp:        log Σ exp(zⱼ) = m + log Σ exp(zⱼ − m),  m = max zⱼ   → 가장 큰 항이 exp(0) = 1
```

- SLP3 3.6: 시험셋의 어떤 단어 확률이 0이면 시험셋 전체 확률이 0이고, perplexity는 계산할 수 없다. 그래서 *평활(smoothing)*으로 보지 못한 사건에 작은 확률을 나눠 준다.
- 신경망 언어 모델은 softmax 출력이라 확률이 수학적으로 0이 되지 않는다. 그래도 구현에서 `exp`가 넘치거나 0으로 사라지면 0·∞·NaN이 나온다(실험 D).
- Goodfellow 외 6.2.2.3: softmax는 모든 입력에 같은 상수를 더해도 출력이 같다. 그래서 `softmax(z) = softmax(z − maxᵢ zᵢ)`로 안정하게 계산한다. 로그 확률은 `zᵢ − log Σⱼ exp(zⱼ)`로 바로 쓴다(같은 절).
- 부동소수 넘침·언더플로·상쇄의 일반론은 [math/15](../../math/15-numerical-stability/2-summary.md).

### 실험: log(0)와 순진한 softmax (실험 C·D)

(실험, Python 3.12.14 python:3.12-slim 컨테이너, 2026-10-08 — 실험 C: 학습 앞 40토큰만으로 평활 없는 MLE)

```text
[C] 평활 없는 MLE(학습 40토큰) — 학습에 없던 단어 ['retry']
    Python math.log(0) → ValueError: math domain error
    float('-inf')로 바꿔 계속하면 평균 NLL = inf
```

```java
// scratchpad ai/01/e03/LogSoftmax.java 핵심
static double[] stableLogSoftmax(double[] z) {
    double m = Arrays.stream(z).max().orElseThrow();
    double s = 0;
    for (double v : z) s += Math.exp(v - m);       // 가장 큰 항이 exp(0) = 1 → 넘침 없음
    double lse = m + Math.log(s);                   // log Σ exp(z) = m + log Σ exp(z − m)
    double[] out = new double[z.length];
    for (int i = 0; i < z.length; i++) out[i] = z[i] - lse;
    return out;
}
```

(실험, JDK 21.0.12 eclipse-temurin:21-jdk 컨테이너, 2026-10-08 — 결정적 계산)

```text
로짓 [2.0, 1.0, 0.1]
  순진  log-softmax [-0.4170300162778335, -1.4170300162778335, -2.3170300162778332]
  안정  log-softmax [-0.41703001627783376, -1.4170300162778338, -2.3170300162778337]
로짓 [1000.0, 999.0, 998.0]
  순진  log-softmax [NaN, NaN, NaN]
  안정  log-softmax [-0.40760596444442854, -1.4076059644444285, -2.4076059644444285]
로짓 [-1000.0, -1001.0, -1002.0]
  순진  log-softmax [NaN, NaN, NaN]
  안정  log-softmax [-0.40760596444442854, -1.4076059644444285, -2.4076059644444285]
로짓 [0.0, -800.0]
  순진  log-softmax [0.0, -Infinity]
  안정  log-softmax [0.0, -800.0]
정답이 1번(로짓 -800)일 때 NLL: 순진 Infinity, 안정 800.0
확률 0의 NLL: -Math.log(0) = Infinity, 클리핑 max(p,1e-12) = 27.631
```

- 관찰 1: 평범한 로짓에서는 두 구현이 끝자리 반올림만 다르다.
- 관찰 2: 로짓이 크거나(1000) 아주 작으면(−1000) 순진 구현은 NaN이다. 같은 차이(1씩)라 안정 구현은 두 경우 같은 값을 낸다 — softmax가 상수 이동에 불변이기 때문이다.
- 관찰 3: 로짓 차이가 800이면 순진 구현은 `exp(−800)`이 0으로 사라져 NLL이 Infinity다. 안정 구현은 정확히 800이다.
- 관찰 4: Python `math.log(0)`은 예외를 던지고, Java `Math.log(0)`은 `-Infinity`를 돌려준다. 언어마다 실패 모양이 다르다. 클리핑(`max(p, 1e-12)`)은 무한을 막지만 그 토큰의 손실을 27.6으로 잘라 실제보다 작게 보고한다(해석).

## 쓰이는 자료구조·알고리즘

| 구조·알고리즘 | 쓰임 | 이어지는 노트 |
|---|---|---|
| 로그 공간 누적합 | 확률 곱 대신 로그 합 — 언더플로 방지 | 실험 A, [math/15](../../math/15-numerical-stability/2-summary.md) |
| log-sum-exp(최댓값 빼기) | 안정한 softmax·log-softmax | 실험 D, Goodfellow 외 6.2.2.3 |
| 빈도 해시맵 + add-1 평활 | n-gram 확률, 보지 못한 사건에 확률 나누기 | [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), SLP3 3.6 |
| 단위 환산(nats ↔ bits, 토큰 ↔ 바이트) | 비교 가능한 분모 | 실험 B |

## 적용 — 풀어나가는 법

### 1. 두 모델의 perplexity·loss를 비교하기 전에

1. **증상**: 표에 "PPL A 7.2 vs B 2.7"만 있다.
2. **원리**: PPL·loss는 토큰당 평균이다. 토크나이저가 다르면 분모가 다르다(SLP3 3.3·7.7.1).
3. **확인**
   - 두 모델의 토크나이저(어휘)가 같은가? 같지 않으면 PPL을 비교하지 않는다.
   - 같은 시험 텍스트인가? 시험 텍스트가 학습에 쓰이지 않았나([01](../01-ml-in-one-page/2-summary.md))?
   - 로그 밑(nats·bits)과 분모(토큰·단어·바이트)가 적혀 있나?
   - 꼭 비교해야 하면 텍스트 전체 NLL을 바이트 수로 나눈 bits per byte로 바꾼다(실험 B).
   - 실제 작업 품질은 perplexity만으로 판정하지 않는다. SLP3 3.3: perplexity 개선이 작업 성능 개선을 보장하지 않으며 실제 작업 평가로 확인한다(같은 영역 [19편](../19-llm-evaluation/2-summary.md)).

### 2. 평가 코드에서 손실을 계산할 때 (Java 21)

- 확률을 받지 말고 로짓을 받아 `stableLogSoftmax`로 로그 확률을 직접 구한다(실험 D).
- 평균 손실을 내기 전에 `Double.isFinite`로 검사하고, 비유한 값이 나온 토큰 위치를 함께 기록한다. 클리핑은 무한을 숨긴다.
- 집계 단위를 이름에 넣는다: `loss_nats_per_token`, `bits_per_byte`.

### 3. 제공자 API에서 로그 확률을 받을 때

- 출력 토큰의 로그 확률을 돌려주는 API가 있다. 이름·지원 범위·특수값은 제공자마다 다르므로 쓰기 전에 그 문서를 확인한다.
- 예: OpenAI Chat Completions 응답의 `choices[].logprobs.content[]`는 토큰마다 `token`·`bytes`(UTF-8 바이트)·`logprob`을 준다. `logprob`은 그 토큰이 상위 20위 안일 때의 로그 확률이고, 아니면 **−9999.0**을 넣는다(2026-10-08 확인, OpenAI API reference "Create chat completion").
  - 이 값을 그대로 평균하면 NLL이 터무니없이 커진다. −9999.0은 실제 로그 확률이 아니므로 평균에 넣지 않는다.
  - 센티널(−9999.0처럼 "실제 값이 아님"을 뜻하는 표식 값)을 빼고 낸 평균은 **남은 토큰만의 평균**이다. 텍스트 전체의 NLL·perplexity·bits per byte는 아니다 — 센티널 토큰 수를 함께 보고하고, 센티널이 하나라도 있으면 전체 값은 "계산 불가"로 둔다.
  - 모든 토큰의 `logprob`이 실제 값이고 `bytes`도 모두 있을 때만 `bytes` 길이의 합을 분모로 bits per byte를 계산할 수 있다. `bytes`는 토큰에 바이트 표현이 없으면 `null`일 수 있다(같은 문서, 2026-10-08 확인).
- 받은 값으로 계산한 NLL·PPL은 **그 모델의 토크나이저 단위**다. 다른 제공자 모델의 값과 나란히 비교하지 않는다.

## 장애 시나리오와 대처

### 1. 토크나이저가 다른 두 모델의 perplexity 비교 (⚠ 커리큘럼)

- 현상: "B 모델의 perplexity가 절반 이하"라는 비교표로 모델을 바꿨는데 작업 품질은 비슷하다.
- 보이는 형태: 같은 텍스트의 토큰 수가 모델마다 다르다. 실험 B처럼 같은 예측 능력에서도 토큰을 2배로 자르면 PPL이 제곱근(7.25 → 2.69)이 된다.
- 원인: PPL은 토큰당 정규화 값이라 분모(토큰 수)가 토크나이저에 따라 바뀐다(SLP3 3.3·7.7.1).
- 대처: 같은 토크나이저끼리만 PPL을 비교한다. 다르면 bits per byte로 바꾸거나, 실제 작업 평가로 판정한다.

### 2. 확률 0에 log → 손실 inf (⚠ 커리큘럼)

- 현상: 평가 작업의 평균 손실이 `Infinity`, 또는 Python에서 `ValueError: math domain error`로 중단.
- 보이는 형태: 대부분 토큰은 정상인데 한 토큰의 확률이 0이다(실험 C: 학습에 없던 `retry`).
- 원인: 평활 없는 빈도 모델, 또는 확률을 0~1로 받은 뒤 log를 따로 취하는 코드. SLP3 3.6: 확률 0이 하나면 시험셋 전체 확률이 0이다.
- 대처: 빈도 모델은 평활한다. 신경망 출력은 로짓에서 log-softmax로 바로 계산한다. 클리핑은 최후 수단이고, 쓰면 클리핑된 토큰 수를 따로 기록한다.

### 3. 순진한 softmax의 넘침 → NaN

- 현상: 어떤 입력에서만 평가 손실이 `NaN`이다.
- 보이는 형태: 로짓 절댓값이 큰 샘플(실험 D: 1000·−1000)에서 log-softmax가 전부 NaN.
- 원인: `exp(1000)`이 ∞로 넘쳐 ∞/∞, 또는 모두 0으로 사라져 0/0.
- 대처: 최댓값을 빼는 log-sum-exp(Goodfellow 외 6.2.2.3). 라이브러리의 log-softmax 함수를 쓴다.

### 4. 확률을 곱해서 텍스트 확률을 구함 → 0.0

- 현상: 문장 점수가 전부 0.0이라 순위가 무의미하다.
- 보이는 형태: 토큰 400개 확률의 곱이 `0.0`(실험 A).
- 원인: 언더플로. 작은 수의 곱이 double 최솟값 아래로 내려갔다.
- 대처: 로그 확률을 더한다(SLP3 3.1.3). 길이가 다른 텍스트를 비교하면 토큰 수로 나눈 평균을 쓴다.

### 5. 로그 밑 혼동 → 보고 숫자가 맞지 않음

- 현상: 같은 평가인데 팀마다 perplexity가 다르게 보고된다.
- 보이는 형태: 한쪽은 `exp(loss)`, 다른 쪽은 `2^loss`로 계산했는데 loss는 nats였다. 실험 A 값(1.9803 nats)이면 2^1.9803 ≈ 3.95로, 올바른 7.2452와 다르다(계산).
- 원인: loss의 밑(ln·log₂)과 지수의 밑이 다르다.
- 대처: loss 이름에 단위(nats·bits)를 넣고 PPL = exp(nats) = 2^(bits)로 맞춘다.

## 핵심 문장

- 교차 엔트로피는 정답 토큰에 준 확률의 평균 음의 로그(평균 NLL)이고, 학습 로그의 loss가 대개 이것이다.
- perplexity = exp(토큰당 평균 NLL) = 2^(토큰당 bits) — 같은 양을 다르게 쓴 것이다.
- perplexity는 토큰당 정규화 값이라 토크나이저(어휘)가 같은 모델끼리만 비교한다. 다르면 바이트당 비트 같은 공통 분모로 바꾼다.
- 확률 0이 한 번이면 손실은 무한이다. 빈도 모델은 평활하고, 신경망 출력은 로짓에서 log-sum-exp로 로그 확률을 바로 계산한다.
- 확률은 곱하지 말고 로그로 더한다 — 곱하면 0.0으로 사라진다.

## 관련 주제·근거

- 선행
  - [01-ml-in-one-page](../01-ml-in-one-page/2-summary.md) — 손실 최소화, 시험셋 누설
  - [math/14-information-theory-basics](../../math/14-information-theory-basics/2-summary.md) — 엔트로피·KL(단일 출처)
- 후속·연결
  - [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) — 넘침·언더플로 일반론
  - [architecture/04-character-encoding-unicode](../../architecture/04-character-encoding-unicode/2-summary.md) — UTF-8 바이트 수
  - [06-transformer-and-attention](../06-transformer-and-attention/2-summary.md) — 어텐션 안의 softmax(같은 안정화)
  - 같은 영역 [04편](../04-tokenization-and-token-cost/2-summary.md)(tokenization-and-token-cost) — 토크나이저와 토큰 수, [07편](../07-decoding-and-nondeterminism/2-summary.md)(decoding) — 로짓 → softmax → 샘플링, [19편](../19-llm-evaluation/2-summary.md)(llm-evaluation) — 작업 평가
- 교재·문서
  - Goodfellow·Bengio·Courville, 『Deep Learning』(2016) 3.13 Information Theory — 식 3.51 `H(P,Q) = H(P) + D_KL(P‖Q)`, 교차 엔트로피 최소화 = KL 최소화 <https://www.deeplearningbook.org/contents/prob.html> · 6.2.1.1 — NLL = 데이터와 모델 분포의 교차 엔트로피 · 6.2.2.3 Softmax Units — 상수 이동 불변, `softmax(z − maxᵢ zᵢ)`, `log softmax(z)ᵢ = zᵢ − log Σⱼ exp(zⱼ)` <https://www.deeplearningbook.org/contents/mlp.html> (2026-10-08 열람)
  - Jurafsky·Martin, SLP3 초안(2026-08-19판) 3.1.3 로그 확률 · 3.3 Perplexity(식 3.14, 어휘가 같을 때만 비교, 시험셋을 모르는 모델, 작업 평가로 확인) · 3.3.1 가중 평균 분기 계수 · 3.6 zeros와 평활 · 3.7 식 3.42 · 7.7.1 Evaluating LLMs: Perplexity(평균 교차 엔트로피 손실의 exp, 토크나이저 민감) <https://web.stanford.edu/~jurafsky/slp3/>
  - OpenAI API reference "Create chat completion" — `logprobs.content[]`의 `token`·`bytes`·`logprob`, 상위 20위 밖이면 −9999.0, `bytes`는 null일 수 있음 <https://developers.openai.com/api/docs/api-reference/chat/create> (2026-10-08 확인)
- 실험 목록(scratchpad `ai/01/e03/`, `sn-ai-w01-*` 일회용 컨테이너 `--network none`)
  - A. 단어 유니그램(add-1)의 평균 NLL·exp·2^bits·확률곱(seed 3) — `ppl.py`, Python 3.12.14
  - B. 같은 모델을 단어 단위 vs 2조각 단위로 셈 — PPL/토큰과 bits/바이트 — 같은 파일
  - C. 평활 없는 MLE(학습 40토큰)와 학습에 없던 단어 — 같은 파일
  - D. 순진한 log-softmax vs log-sum-exp, 로짓 네 경우와 log(0) — `LogSoftmax.java`, JDK 21.0.12
