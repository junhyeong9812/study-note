# ai-engineering/24-fine-tuning-vs-rag-decision — 파인튜닝 vs RAG: 지식은 검색, 형식은 프롬프트·어댑터, LoRA의 계산 — 정리 (힌트)

## 해결하는 문제

범용 모델은 우리 업무를 모른다. 그런데 "모른다"에는 두 종류가 있다.

```text
  (A) 사실·지식을 모른다            (B) 형식·말투·작업 방식을 모른다
  - 이번 달 요금제 가격              - 사내 JSON 스키마 그대로 출력
  - 개정된 환불 규정                 - 상담원 말투, 금지 표현
  - 고객사별 계약 조건               - 우리 기준의 문의 분류 라벨
     │                                  │
     ▼                                  ▼
  요청 때 찾아서 넣어 준다 (RAG)     지시·예시로 보여 준다 (프롬프트)
                                    그래도 안 되면 가중치를 고친다 (파인튜닝)
```

- 고치는 수단은 세 가지다.
  - *프롬프트*: 지시와 예시를 입력에 넣는다. 가중치는 그대로다.
  - *RAG(검색 증강 생성)*: 요청 때 관련 문서를 검색해 입력에 넣는다. 지식이 가중치 **밖**(색인)에 있다([15-rag-pipeline](../15-rag-pipeline/2-summary.md)).
  - *파인튜닝(fine-tuning)*: 우리 데이터로 모델 가중치를 추가 학습한다. 지식·행동이 가중치 **안**에 들어간다.

쉬운 예: 신입 사원 교육이다.
- 매주 바뀌는 가격표는 외우게 하지 않고 책상 위 최신 매뉴얼을 찾아보게 한다(RAG). 고객이 "근거가 뭐예요?" 하면 매뉴얼 쪽수를 짚는다.
- 응대 말투·서류 양식은 예시를 보여 주고(프롬프트), 그래도 몸에 안 배면 연수로 익히게 한다(파인튜닝). 연수로 익힌 것은 출처를 짚을 수 없고, 바뀌면 다시 연수해야 한다.

똑같은 구조다.\
Lewis 외(NeurIPS 2020, RAG 초록)는 파라미터에만 지식을 담은 모델에서 "결정의 출처 제공과 세계 지식 갱신"이 열린 문제라고 적고, 파라미터 메모리(seq2seq 모델)와 비파라미터 메모리(위키백과 밀집 벡터 색인)를 결합했다.

실무 예
- 요금·정책 문의 봇: 사실이 자주 바뀌고 출처가 필요하다 → RAG.
- 문의 자동 분류·특정 JSON 형식 출력: 지식이 아니라 행동이다 → 프롬프트·구조화 출력 먼저, 부족하면 파인튜닝.
- 둘 다 필요하면 결합한다(파인튜닝한 모델 + RAG).

## 동작·원리

### 1. 지식이 어디 사느냐가 갱신·출처·삭제를 정한다

```text
                 RAG                                   파인튜닝
  지식 위치     색인(문서 행·벡터)                      가중치(수십억 개 실수)
  갱신         문서 행 갱신 + 재임베딩 (분~시간)         데이터 준비 + 재학습 + 재평가 (일~주, 예시)
  출처 표기     검색된 문서 ID를 그대로 붙임             어느 학습 예제에서 왔는지 짚을 수 없음
  삭제 요청     행 삭제                                  가중치에서 특정 사실만 빼기 어려움 (해석)
  요청당 비용   검색 + 긴 프롬프트(검색 결과만큼 입력↑)   짧은 프롬프트 가능, 대신 학습·호스팅 비용
```

- 위 표의 "일~주"·"분~시간"은 규모 감을 위한 예시다. 실제 시간은 데이터·인프라에 따라 다르다.
- 삭제 줄은 해석이다. 근거: 파인튜닝은 가중치 전체에 학습 신호를 섞는다. RAG는 지식이 행 단위로 분리돼 있다.

### 2. 전체 파인튜닝이 비싼 이유

- Hu 외(2021, LoRA 초록·4.2절): GPT-3 175B를 Adam으로 전체 미세조정하면 작업마다 1,750억 파라미터짜리 사본을 따로 배포해야 한다. 학습 때 VRAM은 1.2TB가 든다.
- 옵티마이저(Adam)는 파라미터마다 상태를 따로 들고 있다. 학습할 파라미터가 많을수록 메모리가 는다(LoRA 4.2절: 동결한 파라미터는 옵티마이저 상태가 필요 없어 VRAM이 최대 2/3 준다).

### 3. LoRA — 가중치 변화를 저랭크 행렬 두 개로

```text
  원래 층:   h = W0 · x                 W0 : d × k   (동결 — 학습 안 함)

  LoRA:      h = W0 · x  +  (α/r) · B · (A · x)
                            B : d × r    (0으로 시작)
                            A : r × k    (가우스 무작위로 시작)
                            r ≪ min(d, k)

         x ──┬──> [ W0 (동결) ] ──────────────┐
             │                                 (+) ──> h
             └──> [ A ] ──r차원──> [ B ] ── ×α/r ┘
                  (학습)           (학습)

  배포 때 병합:  W = W0 + (α/r)·B·A   → 추가 연산 없음 (원래 층과 같은 모양)
  작업 전환:    W − (α/r)·B·A + (α/r)·B'·A'
```

- Hu 외 4.1절
  - `W0 + ΔW = W0 + BA`, `B ∈ R^{d×r}`, `A ∈ R^{r×k}`, 랭크 `r ≪ min(d, k)`. W0는 동결되고 A·B만 학습한다.
  - A는 무작위 가우스, B는 0으로 초기화한다. 그래서 학습 시작 때 `ΔW = BA = 0`이고 출력이 원래 모델과 같다.
  - `ΔW x`를 `α/r`로 곱한다. α는 처음 시도한 r 값으로 두고 조정하지 않았다.
  - 배포 때 `W = W0 + BA`를 계산해 저장하면 추론 지연이 늘지 않는다. 다른 작업으로 바꿀 때는 BA를 빼고 B′A′를 더한다.
  - *랭크(rank)*: 행렬이 실제로 담는 독립 방향의 수. `BA`의 랭크는 r을 넘지 못한다.
- 학습 파라미터 수(5.1절): `|Θ| = 2 × L̂ × d_model × r`. L̂ = LoRA를 붙인 가중치 행렬 수. 정사각 `d_model × d_model` 행렬 하나에 A·B가 각각 `r × d_model`·`d_model × r`이라 2가 붙는다.
- 한계(4.2절): 지연을 없애려 BA를 W에 병합하면, 서로 다른 어댑터를 쓰는 요청을 한 배치로 묶기 어렵다. 병합하지 않고 요청마다 어댑터를 고르는 방법도 있다(지연이 덜 중요할 때).

### 4. QLoRA — 베이스를 4비트로 얼려 메모리를 더 줄인다

- Dettmers 외(2023, QLoRA 초록): 동결된 **4비트 양자화** 베이스 모델을 통과해 LoRA 어댑터로 그래디언트를 역전파한다. 65B 모델을 48GB GPU 한 장에서 미세조정하면서 16비트 전체 미세조정 성능을 유지했다고 보고한다.
  - 세 장치: 4비트 NormalFloat(NF4, 정규분포 가중치에 맞춘 데이터형), 이중 양자화(양자화 상수를 다시 양자화), 페이지드 옵티마이저(메모리 급증 관리).
  - *양자화(quantization)*: 실수를 적은 비트 수의 값으로 근사해 저장하는 것. 부동소수 표현은 [architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md).

### 5. 어댑터는 베이스 모델에 묶인다

```text
  어댑터 = "베이스 W0에서 얼마나 움직일지"(ΔW = BA)
  베이스 v1 위에서 학습한 ΔW  ──X──>  베이스 v2 (W0′ ≠ W0)
       모양이 다르면: 붙일 수 없다 (차원 불일치 — 시끄러운 실패)
       모양이 같아도: W0′ + ΔW 는 학습한 적 없는 가중치 → 평가 없이 쓸 근거가 없다 (해석)
```

- `ΔW`는 특정 W0에 대해 학습한 차이다(4.1절 식). 베이스가 바뀌면 같은 ΔW를 더해도 학습 때와 다른 모델이 된다.
- 베이스 모델에는 수명이 있다. 예: Anthropic 문서는 모델마다 `retired`(퇴역) 상태를 표시한다(2026-10-08 "Prompt caching" 문서의 모델 목록). 제공자가 베이스를 내리면 그 위의 어댑터·미세조정 모델 계획도 다시 세워야 한다.

### 실험: LoRA 파라미터 수와 병합 동작

- 무엇: (1) GPT-3 175B 설정(d_model 12,288, 96층 — Brown 외 2020 표 2.1)으로 LoRA 파라미터 수를 계산해 논문의 "18M 예산"(7.1절 표 5)과 대조. (2) 48×48 작은 행렬로 B = 0 초기화, 병합 전후 출력, BA의 랭크, 병합 해제를 확인.
- 코드 핵심(`exp/24/lora.py`):

```python
theta = 2 * L * d * r                                   # |Θ| = 2 × L̂ × d_model × r
A = [[rng.gauss(0, 0.1) for _ in range(k)] for _ in range(r)]   # A: 가우스
B = [[0.0] * r for _ in range(d)]                                  # B: 0
def forward(B):                                          # h = W0 x + (α/r) B (A x)
    base = mv(W0, x); delta = mv(B, mv(A, x)); s = alpha / r
    return [b + s * dl for b, dl in zip(base, delta)]
Wm = [[W0[i][j] + (alpha / r) * BA[i][j] for j in range(k)] for i in range(d)]   # 병합
```

(실험, Python 3.12 `python:3.12-slim`, Docker `--network none --cpus=2`, 2026-10-08 — seed 24, 2회 실행 출력 동일)

```text
[1] 파라미터 수 |Θ| = 2 × L̂ × d_model × r  (Hu 외 2021 §5.1, Wq·Wv만 적용)
  GPT-3 175B (d_model 12288, 96층 — Brown 외 2020 표 2.1): 층당 행렬 2개, r=4 → L̂=192, |Θ|=18,874,368  (FP16 저장 37.7 MB)
  GPT-3 175B (d_model 12288, 96층 — Brown 외 2020 표 2.1): 층당 행렬 1개, r=8 → L̂=96, |Θ|=18,874,368  (FP16 저장 37.7 MB)
  GPT-3 175B (d_model 12288, 96층 — Brown 외 2020 표 2.1): 층당 행렬 4개, r=2 → L̂=384, |Θ|=18,874,368  (FP16 저장 37.7 MB)
  전체 미세조정 학습 파라미터 1.75e11 ÷ 18,874,368 = 9,272배
  한 행렬(d×d) 전체 갱신 150,994,944 vs LoRA r=4 98,304  (1536배 차이)

[2] 작은 행렬로 동작 확인 (d=k=48, r=4, α=8, seed=24)
  B=0일 때 |h - W0x| 최대 = 0.0
  비병합 W0x + (α/r)BAx  vs  병합 (W0 + (α/r)BA)x : 최대 차이 2.22e-16
  rank(BA) = 4 (≤ r=4),  rank(W0) = 48
  학습 파라미터: 전체 ΔW 2304 개 vs LoRA r(d+k) = 384 개
  병합 후 BA를 빼서 W0 복원: 최대 차이 5.55e-17
```

- 관찰 1: 세 조합(Wq·Wv r=4 / 한 종류 r=8 / 네 종류 r=2)이 모두 18,874,368개다. 논문 표 5의 "18M 예산"과 r 조합(8·4·2)이 정확히 맞는다.
- 관찰 2: 전체 미세조정 대비 약 9,272배 적다. 논문 초록의 "약 1만 배"와 같은 규모다. FP16 저장 37.7MB(≈ 36MiB)는 논문의 "약 35MB" 체크포인트와 같은 규모다.
- 관찰 3: B = 0이면 출력이 W0x와 정확히 같다(차이 0.0). 병합 전후 차이는 2.22e-16으로 float64 반올림 수준이다 — 병합해도 결과가 같고 연산은 원래 층 하나로 준다.
- 관찰 4: BA의 랭크는 r(4)이고, 원래 행렬은 48(꽉 찬 랭크)이다. LoRA는 "변화량이 저랭크면 충분하다"는 가정에 기대는 방법이다. Hu 외는 7절에서 이 가정을 실험으로 살폈다.
- 관찰 5: 병합한 W에서 BA를 빼면 W0로 돌아온다(차이 5.55e-17). 베이스 하나에 어댑터만 갈아 끼우는 배포가 가능한 이유다.

## 쓰이는 자료구조·알고리즘

- **저랭크 분해(행렬곱 BA)** — d×k 행렬을 d×r과 r×k의 곱으로 근사한다. 파라미터 수가 d·k에서 r(d+k)로 준다. 행렬곱 비용·메모리 배치는 [math/13](../../math/13-linear-algebra-essentials/2-summary.md).
- **랭크 계산(가우스 소거)** — 실험에서 BA의 랭크를 확인한 방법.
- **양자화** — 4비트 NF4로 베이스 가중치를 압축 저장(QLoRA).
- **어댑터 레지스트리 = (베이스 모델·가중치 해시) → 어댑터 목록 맵** — 호환되는 조합만 배포하게 막는다(아래 Java).
- **RAG 쪽 자료구조**(색인·ANN·청크)는 [15](../15-rag-pipeline/2-summary.md)·[16](../16-vector-index-ann/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상에서 수단으로

| 증상(평가셋에서 관찰) | 원인 유형 | 먼저 쓸 수단 |
|---|---|---|
| 최신 가격·정책을 틀리게 말함, 근거를 못 댐 | 지식 부족·지식 낡음 | RAG(출처 표기 포함) |
| 사내 문서에만 있는 사실을 지어냄 | 지식 부족 | RAG + "문서에 없으면 모른다고" 지시 |
| 형식(JSON·필드)이 자주 어긋남 | 행동 | 구조화 출력·스키마 검증([14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md)) |
| 말투·분류 기준이 예시를 줘도 흔들림 | 행동 | 예시 늘리기 → 그래도 안 되면 파인튜닝(LoRA) |
| 긴 지시·예시 때문에 요청당 입력 토큰이 큼 | 비용 | 프리픽스 캐시([12](../12-prompt-and-semantic-caching/2-summary.md)) → 그래도 크면 파인튜닝으로 지시를 가중치에 |

### 2. 판단 순서 (이 노트의 권장)

1. **평가셋부터** 만든다. 개선인지 회귀인지 판정할 기준이 없으면 어떤 수단도 고를 수 없다([19-llm-evaluation](../19-llm-evaluation/2-summary.md)).
2. 프롬프트(지시·예시)로 기준선을 잰다.
3. 실패를 "지식"과 "행동"으로 나눈다. 지식이면 RAG, 행동이면 구조화 출력·예시.
4. 행동 실패가 남고, 학습 데이터(수백~수천 예시 — 예시 규모)와 평가셋이 있고, 그 작업이 오래 쓰일 때 파인튜닝을 검토한다.
5. 파인튜닝 결과는 베이스 대비 같은 평가셋에서 신뢰구간으로 비교한다([data-analysis/08-confidence-intervals](../../data-analysis/08-confidence-intervals/2-summary.md)).
6. 직접 학습·호스팅할지, 제공자의 미세조정 서비스를 쓸지는 도입 판단 일반 기준을 따른다([engineering-practice/13-build-vs-buy-and-adoption](../../engineering-practice/13-build-vs-buy-and-adoption/2-summary.md)).

### 3. 코드 — 어댑터를 베이스와 평가 결과에 묶어 배포 (Java 21)

```java
// 어댑터(ΔW = BA)는 특정 베이스 가중치 W0에 대한 차이다 → 베이스 모델 ID·해시와 한 몸
record Adapter(String id, String baseModel, String baseWeightsSha256, int rank, String evalReport) {}
record Deployment(String baseModel, String baseWeightsSha256) {}

static void checkCompatible(Adapter a, Deployment d) {
    if (!a.baseModel().equals(d.baseModel()) || !a.baseWeightsSha256().equals(d.baseWeightsSha256()))
        throw new IllegalStateException("adapter " + a.id() + " was trained on " + a.baseModel()
                + "@" + a.baseWeightsSha256().substring(0, 8) + ", deployment is " + d.baseModel()
                + "@" + d.baseWeightsSha256().substring(0, 8) + " → retrain and re-evaluate");
    if (a.evalReport() == null)
        throw new IllegalStateException("adapter " + a.id() + " has no evaluation report → do not deploy");
}
```

(실험, OpenJDK 21.0.12 `eclipse-temurin:21-jdk`, 2026-10-08 — `java AdapterRegistry.java`, 값은 예시)

```text
OK   tone-ko-v3
DENY adapter tone-ko-v2 was trained on base-7b-v1@41aa07c3, deployment is base-7b-v2@9f2c4e1a → retrain and re-evaluate
DENY adapter json-form-v1 has no evaluation report → do not deploy
```

### 4. 비용 어림 — 식만 고정하고 숫자는 실측

- RAG 요청당 입력 = 고정 프롬프트 + 검색 결과(청크 수 × 청크 토큰) + 질문. 검색 결과가 길수록 입력 비용·첫 토큰 지연이 는다.
- 파인튜닝 총비용 = 데이터 준비(라벨링) + 학습 + 평가 + 호스팅(전용 서빙이면 GPU 상시 비용) + **베이스가 바뀔 때마다 재평가, 대개 재학습**(데이터·평가셋은 재사용).
- 단가·GPU 시간은 제공자·날짜마다 바뀌므로 노트에 적지 않는다. 비교는 같은 평가셋 점수당 비용으로 한다([23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md)).

## 장애 시나리오와 대처

### 1. 자주 바뀌는 사실을 파인튜닝으로 주입 (⚠)

- **현상**: 요금제가 바뀐 뒤에도 봇이 옛 가격을 말한다. 재학습하는 몇 주 동안 계속된다.
- **보이는 형태**: 평가셋의 "최신 사실" 항목 정답률이 개정일 이후 떨어진다. 답에 출처가 없어 어디서 나온 숫자인지 추적이 안 된다.
- **원인**: 지식을 가중치에 넣었다. 갱신 = 재학습이고, 그 사이 옛 사실이 나온다. RAG였다면 문서 행 갱신으로 끝났다.
- **대처**: 자주 바뀌는 사실은 RAG로 옮기고 답에 출처 문서 ID를 붙인다. 파인튜닝은 형식·말투처럼 잘 안 바뀌는 행동에 쓴다.

### 2. 평가셋 없이 파인튜닝 (⚠)

- **현상**: 파인튜닝 모델을 배포했는데 좋아졌는지 나빠졌는지 아무도 말하지 못한다. 몇 주 뒤 다른 작업의 품질 저하 신고가 온다.
- **보이는 형태**: 학습 손실 그래프만 있고 베이스 대비 점수가 없다. 회귀는 사용자 신고로만 발견된다.
- **원인**: 개선·회귀를 판정할 고정 평가셋과 기준선이 없었다. 좁은 데이터로 학습하면 다른 능력이 떨어질 수 있는데 그것을 잴 항목도 없었다(해석).
- **대처**: 학습 전에 평가셋(목표 작업 + 지켜야 할 기존 능력)을 만든다. 베이스와 같은 평가셋에서 차이와 신뢰구간을 낸다. 평가 보고서 없는 어댑터는 배포를 막는다(위 Java의 `DENY`).

### 3. 베이스 모델을 바꿨는데 어댑터를 그대로 씀 (⚠)

- **현상**: 베이스 모델을 새 버전으로 올린 뒤 어댑터 로드가 실패하거나, 로드는 되는데 출력이 이상하다.
- **보이는 형태**: 차원 불일치 오류(모양이 다를 때) 또는 평가 점수 급락(모양이 같을 때).
- **원인**: 어댑터는 특정 W0에 대한 차이(ΔW)다. 베이스가 바뀌면 W0′ + ΔW는 학습한 적 없는 가중치다.
- **대처**: 어댑터에 베이스 모델 ID·가중치 해시를 함께 저장하고 배포 때 대조한다(위 Java). 베이스 교체 계획에 "새 베이스에서 재평가 → 기준 미달이면 어댑터 재학습"을 포함한다. 옛 어댑터를 그대로 얹으면 호환성 문제로 품질이 자주 떨어지고, 처음부터 재학습은 비싸 옛 어댑터를 출발점으로 재적응하는 연구도 있다(Xu 외 2026, ReLoRA 초록). 제공자 모델의 퇴역 일정을 추적한다.

### 4. 출처가 필요한 업무를 파인튜닝만으로 처리

- **현상**: 규정 질의에 그럴듯한 답이 나오는데, 감사·민원에서 "근거 조항이 뭐냐"에 답하지 못한다.
- **보이는 형태**: 답에 인용이 없거나, 모델이 지어낸 조항 번호를 댄다.
- **원인**: 가중치에 섞인 지식은 출처를 짚을 수 없다(Lewis 외 초록이 지적한 "출처 제공" 문제).
- **대처**: RAG로 검색한 문서를 근거로 답하게 하고, 인용한 문서 ID·조항을 응답에 구조화해 붙인다. 인용이 검색 결과에 실제로 있는지 검증한다([15](../15-rag-pipeline/2-summary.md)).

### 5. 학습 데이터에 개인정보가 섞임

- **현상**: 상담 기록으로 파인튜닝한 뒤, 삭제 요청을 받은 고객의 정보를 지울 방법이 없다.
- **보이는 형태**: 특정 질문에 실제 고객 이름·연락처 비슷한 문자열이 출력된다는 신고.
- **원인**: 학습 데이터가 가중치에 섞여 행 단위 삭제가 불가능하다(해석). OWASP Top 10 for LLM Applications 2025의 LLM02(민감 정보 노출)가 이 위험 범주다.
- **대처**: 학습 전에 개인정보를 분류·제거·가명 처리한다([security/27](../../security/27-pii-classification-masking-retention/2-summary.md)). 개인 데이터가 필요한 답은 RAG(행 단위 삭제 가능)로 처리한다. 보안 전반은 [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md).

## 핵심 문장

- "모른다"를 지식(사실)과 행동(형식·말투·작업 방식)으로 나눈다. 지식은 RAG로 가중치 밖에, 행동은 프롬프트·구조화 출력으로 먼저, 부족하면 파인튜닝으로.
- RAG는 갱신이 색인 갱신이고 출처를 붙일 수 있다. 파인튜닝은 갱신이 재학습이고 출처를 짚을 수 없다.
- LoRA는 동결한 W0 옆에 저랭크 행렬 B·A만 학습한다. 파라미터 수는 `d × k` 행렬 하나에 `r(d+k)`, 적용 행렬이 모두 `d_model × d_model`이면 `2 × L̂ × d_model × r`이고, 병합하면 추론 지연이 늘지 않는다.
- 어댑터는 특정 베이스 가중치에 대한 차이다. 베이스를 바꾸면 품질이 보장되지 않아 재평가가 필요하고, 그대로 쓰면 품질이 떨어지는 경우가 많아 대개 재학습(재적응)이 따른다.
- 평가셋 없이 어떤 수단도 고를 수 없다. 개선·회귀는 베이스 대비 같은 평가셋에서 판정한다.

## 관련 주제·근거

- 선행
  - [15-rag-pipeline](../15-rag-pipeline/2-summary.md) — 검색해서 넣는 쪽
  - [19-llm-evaluation](../19-llm-evaluation/2-summary.md) — 평가셋과 판정
- 연결
  - [12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md) · [14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md) · [16-vector-index-ann](../16-vector-index-ann/2-summary.md) · [18-index-freshness-and-reembedding](../18-index-freshness-and-reembedding/2-summary.md) · [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md) · [23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md)
  - [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md) — 행렬곱
  - [architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md) — 부동소수 표현(양자화의 바탕)
  - [data-analysis/08-confidence-intervals](../../data-analysis/08-confidence-intervals/2-summary.md) — 평가 점수 차이의 불확실성
  - [engineering-practice/13-build-vs-buy-and-adoption](../../engineering-practice/13-build-vs-buy-and-adoption/2-summary.md) — 직접 학습 vs 서비스 도입
  - [security/27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md)
- 논문
  - Hu 외, "LoRA: Low-Rank Adaptation of Large Language Models"(arXiv 2021-06-17) — 4.1절 `W0 + BA`·A 가우스/B 0 초기화·α/r·병합으로 추론 지연 없음, 4.2절 Wq·Wv 적용·VRAM 1.2TB → 350GB·체크포인트 350GB → 약 35MB·배치 한계, 5.1절 `|Θ| = 2 × L̂ × d_model × r`, 7.1절 표 5(18M 예산, 96층) <https://arxiv.org/abs/2106.09685>
  - Xu 외, "ReLoRA: Knowledge-Reusing Adaptation for Fast Rollout of Evolving LLM Services"(arXiv 2026-05-23) — 초록: 베이스 갱신이 기존 어댑터를 무효화할 수 있음, 옛 어댑터를 그대로 얹으면 품질이 자주 떨어지고 처음부터 재학습은 비쌈 → 옛 어댑터를 활용한 재적응 <https://arxiv.org/abs/2606.02606>
  - Dettmers 외, "QLoRA: Efficient Finetuning of Quantized LLMs"(arXiv 2023-05-23) — 4비트 동결 베이스 + LoRA, 65B를 48GB GPU 한 장에서, NF4·이중 양자화·페이지드 옵티마이저 <https://arxiv.org/abs/2305.14314>
  - Lewis 외, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", NeurIPS 2020 — 파라미터 + 비파라미터 메모리, 출처 제공·지식 갱신이 열린 문제 <https://arxiv.org/abs/2005.11401>
  - Brown 외, "Language Models are Few-Shot Learners"(GPT-3, arXiv 2020) 표 2.1 — GPT-3 175B: 96층, d_model 12,288 <https://arxiv.org/abs/2005.14165>
- 교재: Jurafsky·Martin, 『Speech and Language Processing』 3판 초안(2026-08-19판) 8장 Post-training <https://web.stanford.edu/~jurafsky/slp3/>
- 문서: OWASP Top 10 for LLM Applications 2025 — LLM02 Sensitive Information Disclosure <https://genai.owasp.org/llm-top-10/>
- 실험 목록
  - LoRA 파라미터 수(GPT-3 설정 3조합)·B=0 초기화·병합 전후 출력·BA 랭크·병합 해제 — Python 3.12 `python:3.12-slim`, seed 24, 2회 실행 동일
  - 어댑터–베이스 호환·평가 보고서 검사 — OpenJDK 21.0.12 `eclipse-temurin:21-jdk`
