# ai-engineering/06-transformer-and-attention — 셀프 어텐션·인과 마스크·멀티헤드·길이에 대한 제곱 비용 — 정리 (힌트)

## 해결하는 문제

다음 토큰을 예측하려면 앞 문맥 중 **어디를 참고할지** 정해야 한다. "그 요청은 재시도 후에 **그것**이 성공했다"에서 "그것"은 앞의 "요청"을 가리킨다.
고정된 앞 몇 단어만 보는 방식(n-gram, SLP3 3장)은 멀리 떨어진 단어를 볼 수 없다.

```text
  위치:   1      2      3     4      5      6      7
  토큰:  그     요청은  재시도  후에   그것이  성공   했다
                 ▲                      │
                 └──── 강하게 참고 ─────┘   (가중치는 학습이 정한다 — 그림은 예시)
```

- 셀프 어텐션은 각 위치가 문맥의 모든 (허용된) 위치를 보고, 관련도만큼 가중 평균한다(Vaswani 외 2017).
- 대가: 모든 쌍을 비교하므로 문맥 길이 n에 대해 연산·메모리가 n²로 는다.

쉬운 예: 회의록을 정리하는 사람.
- "그것"을 만나면 질문(무엇을 찾나)을 들고, 앞 문장들의 표제(무슨 내용인가)와 맞춰 본다.
- 잘 맞는 문장일수록 그 내용을 많이 가져와 섞는다.

똑같은 구조다.\
질문 = Query, 표제 = Key, 내용 = Value. 해시맵 조회가 키 하나를 정확히 고른다면, 어텐션은 모든 키와의 유사도로 값을 **부드럽게 섞는** 조회다.

실무 예:
- RAG로 관련 청크 20개를 프롬프트에 넣었는데, 중간에 둔 근거가 답에 반영되지 않는다(Lost in the Middle — 7절).
- 문맥 한도를 크게 늘린 모델로 바꾸고 긴 문서를 통째로 넣었더니 첫 토큰까지 시간(프리필)과 비용이 크게 늘었다(6절, [08편](../08-kv-cache-and-inference-memory/2-summary.md)).

## 동작·원리

### 1. 한 헤드의 계산 — softmax(QKᵀ/√d)V

```text
  입력 X (n × d_model)
     ├─ × W_Q → Q (n × d_k)   "무엇을 찾나"
     ├─ × W_K → K (n × d_k)   "나는 무엇인가"
     └─ × W_V → V (n × d_v)   "가져갈 내용"

  점수 S = Q·Kᵀ / √d_k          (n × n)   S[i][j] = 위치 i가 위치 j를 얼마나 볼지
  가중치 A = softmax(S, 행마다)  (n × n)   행 합 = 1
  출력  O = A · V               (n × d_v)  위치 i의 출력 = Σⱼ A[i][j] · V[j]
```

- Vaswani 외 3.2.1 식 (1): `Attention(Q, K, V) = softmax(QKᵀ/√d_k)V`. 논문은 이를 Scaled Dot-Product Attention이라 부른다.
- *셀프 어텐션(self-attention)*: Q·K·V가 모두 같은 곳(이전 층의 출력)에서 나오는 어텐션(Vaswani 외 3.2.3).
- 내적과 행렬곱은 [math/13](../../math/13-linear-algebra-essentials/2-summary.md), softmax의 수치 안정화(최댓값 빼기)는 [03](../03-cross-entropy-and-perplexity/2-summary.md) 5절.

### 2. 인과 마스크 — 미래를 보지 않는다

```text
          키 위치 j →   1      2      3      4      5
  질의 i  1          q1·k1   −∞     −∞     −∞     −∞
          2          q2·k1  q2·k2   −∞     −∞     −∞
          3          q3·k1  q3·k2  q3·k3   −∞     −∞
          4          …                            −∞
          5          q5·k1  …                   q5·k5
                      softmax 후 −∞ 칸은 0 → 하삼각만 남는다
```

- 생성 모델은 왼쪽에서 오른쪽으로 토큰을 만든다. 위치 i는 i 이하만 봐야 한다.
- Vaswani 외 3.2.3: 디코더는 왼쪽으로 흐르는 정보를 막으려고 softmax 입력에서 허용되지 않는 연결을 −∞로 가린다. SLP3 7장(2026-08-19판)도 상삼각 부분을 −∞로 두는 마스크를 보인다.
- 결과: 위치 i의 출력은 1..i의 토큰에만 의존한다. 뒤에 토큰이 붙어도 앞 위치의 K·V·출력은 그대로다 → 이전 계산을 저장해 재사용할 수 있다(KV 캐시 — [08](../08-kv-cache-and-inference-memory/2-summary.md)).

### 실험: 마스크 유무에 따라 앞 위치가 뒤 토큰에 흔들리나 (실험 A)

```python
# scratchpad ai/01/e06/attention.py 핵심
def attention(Q, K, V, causal):
    n, d = len(Q), len(Q[0]); out, weights = [], []
    for i in range(n):
        scores = [sum(q * k for q, k in zip(Q[i], K[j])) / math.sqrt(d) for j in range(n)]
        if causal:
            scores = [s if j <= i else float("-inf") for j, s in enumerate(scores)]
        w = softmax(scores)                    # 최댓값을 빼는 안정 softmax
        weights.append(w)
        out.append([sum(w[j] * V[j][c] for j in range(n)) for c in range(len(V[0]))])
    return out, weights
```

(실험, Python 3.12.14 python:3.12-slim 컨테이너, 2026-10-08 — n=5, d=4, 표준정규 Q·K·V, seed 6)

```text
[A] n=5, d=4, seed 6 — 인과 마스크 어텐션 가중치 (행 = 질의 위치, 열 = 키 위치)
    t1 1.000 0.000 0.000 0.000 0.000   합 1.000
    t2 0.308 0.692 0.000 0.000 0.000   합 1.000
    t3 0.149 0.290 0.561 0.000 0.000   합 1.000
    t4 0.392 0.123 0.329 0.156 0.000   합 1.000
    t5 0.068 0.391 0.167 0.067 0.307   합 1.000
    마스크 있음: 5번 토큰만 바꿨을 때 위치별 출력 최대 변화 t1=0 t2=0 t3=0 t4=0 t5=0.694
    마스크 없음: 5번 토큰만 바꿨을 때 위치별 출력 최대 변화 t1=0.0696 t2=0.271 t3=1.59 t4=0.469 t5=0.694
```

- 관찰 1: 마스크가 있으면 가중치 행렬은 하삼각이고 행마다 합이 1이다. 첫 위치는 자기 자신만 본다(1.000).
- 관찰 2: 마지막 토큰을 바꿔도 마스크가 있으면 1~4번 출력은 정확히 0만큼 변한다. 마스크가 없으면 모든 위치가 흔들린다(t3 최대 1.59).

### 3. √d_k로 나누는 이유

- Vaswani 외 3.2.1 각주 4: q·k의 성분이 평균 0·분산 1로 독립이면 내적의 분산은 d_k다. d_k가 크면 내적의 크기가 커져 softmax가 기울기가 아주 작은 영역으로 밀린다. 그래서 1/√d_k를 곱한다.

### 실험: 차원이 클 때 스케일 유무 (실험 B)

(실험, Python 3.12.14 python:3.12-slim 컨테이너, 2026-10-08 — 키 16개, 반복 2000, seed 8)

```text
[B] q·k 성분 평균 0·분산 1, 키 16개, 반복 2000, seed 8
        d    q·k 분산          최대 가중치(스케일 없음)        최대 가중치(1/√d)
        4       3.8                   0.426               0.234
       64      64.1                   0.845               0.245
      256     252.4                   0.919               0.243
     1024    1051.3                   0.966               0.248
```

- 관찰 1: 내적 분산이 d와 같은 크기로 는다(64 → 64.1, 1024 → 1051.3). 각주 4의 계산과 맞다.
- 관찰 2: 스케일이 없으면 d=1024에서 가장 큰 가중치가 평균 0.966이다. softmax가 거의 한 키에 몰린다(포화). 1/√d를 곱하면 d와 무관하게 0.23~0.25로 유지된다.

### 4. 멀티헤드 — 여러 관점을 나란히

```text
  X ─┬─ 헤드 1: Attention(XW_Q¹, XW_K¹, XW_V¹) ─┐
     ├─ 헤드 2: …                                ├─ 이어 붙임(Concat) ─ × W_O ─ 출력
     └─ 헤드 h: …                                ┘
```

- Vaswani 외 3.2.2: h개 헤드가 각자 다른 투영으로 어텐션을 계산하고, 결과를 이어 붙여 W_O로 다시 투영한다. 한 헤드만 쓰면 평균이 정보를 뭉갠다.
- 논문 기본 모델은 h = 8, d_k = d_v = d_model/h = 64. 헤드마다 차원이 줄어 전체 계산량은 전체 차원의 단일 헤드와 비슷하다(같은 절).
- 헤드마다 K·V를 따로 저장해야 하는 것이 추론 메모리(KV 캐시)의 크기를 정한다. K·V 헤드 수를 줄이는 MQA·GQA는 [08](../08-kv-cache-and-inference-memory/2-summary.md).

### 5. 위치 정보

- 1절의 식에는 위치가 들어 있지 않다. 점수는 벡터 내용만으로 정해지므로, 위치 정보를 따로 넣지 않으면 입력 순서를 바꿔도 같은 쌍끼리 같은 점수가 나온다(해석 — 식에서 바로 나온다).
- Vaswani 외 3.5: 입력 임베딩에 사인·코사인 위치 인코딩을 더했다. 학습된 위치 임베딩도 거의 같은 결과였다(같은 절, 표 3 (E)).
- SLP3 7.8은 현재 모델들이 회전 위치 임베딩(RoPE) 같은 설정을 쓴다고 소개한다. 세부 방식은 모델마다 다르다.

### 6. 문맥 길이 n에 대한 제곱 비용

```text
  점수 행렬 S는 n × n — 헤드 1개·층 1개·fp16(2바이트)로 전부 만든다면 (계산)
    n =   4,096  →  n² × 2B =   32 MiB
    n =  32,768  →  n² × 2B =    2 GiB
    n = 131,072  →  n² × 2B =   32 GiB
  길이 2배 → 칸 4배 → 연산 약 4배
```

- Vaswani 외 표 1: 셀프 어텐션 층의 복잡도는 O(n²·d). SLP3 7장도 각 층에서 모든 쌍의 내적을 계산하므로 입력 길이에 제곱이라고 쓴다.
- FlashAttention(Dao 외 2022 초록): 시간·메모리가 길이에 제곱인 것이 긴 시퀀스의 병목이다. FlashAttention은 **정확한** 어텐션을 계산하면서 타일링으로 GPU HBM과 온칩 SRAM 사이 읽기·쓰기를 줄인다. 근사가 아니므로 같은 어텐션 식을 계산하고(부동소수 계산 순서가 달라 기준 구현과 작은 수치 오차는 날 수 있다 — 공식 저장소 README Tests 절은 "up to some numerical tolerance"로 검증), 줄이는 것은 메모리 이동이다.
  - 위 표처럼 점수 행렬을 통째로 만드는 구현은 단순 구현의 어림이다. 실제 서빙 엔진의 메모리 사용은 구현에 따라 다르다.
- 생성 단계에서 새 토큰 하나는 이전 n개와만 비교하므로 토큰당 비용은 n에 비례한다. 프롬프트 전체를 처리하는 프리필은 n² 쪽이다([08편](../08-kv-cache-and-inference-memory/2-summary.md) 프리필·디코드).

### 실험: 길이를 두 배로 할 때마다 (실험 C)

(실험, Python 3.12.14 python:3.12-slim 컨테이너 `--cpus=2`, 2026-10-08 — 1헤드, d=16, seed 9, 3회 중 최소)

```text
[C] 순수 Python 인과 어텐션 1헤드, d=16, seed 9, 3회 중 최소 시간
    n=128  점수 칸 n²=  16384  시간 0.136s
    n=256  점수 칸 n²=  65536  시간 0.549s  (직전 대비 ×4.05)
    n=512  점수 칸 n²= 262144  시간 2.396s  (직전 대비 ×4.36)
```

- 관찰: 길이를 2배로 하면 시간이 약 4배(×4.05, ×4.36)다. 같은 날 점검 재실행에서는 ×3.94, ×4.19였다 — 배율은 실행마다 약 3.9~4.4 범위에서 흔들린다(시간 측정이라 비결정적). 이 구현은 가려질 칸의 점수도 먼저 계산한 뒤 −∞로 바꾸므로 n² 칸을 모두 계산한다.
- 절댓값(초)은 순수 Python이라 실제 GPU 커널과 비교할 수 없다. 보이려는 것은 배율이다.

### 실험: 모든 칸이 가려진 행 (실험 D)

```text
[D] 전부 -inf인 행: v - max = [nan, nan, nan, nan]  exp = [nan, nan, nan, nan]  합 = nan  가중치 = [nan, nan, nan, nan]
```

(실험, Python 3.12.14 python:3.12-slim 컨테이너, 2026-10-08 — `attention.py --d-only`)

- 관찰: 패딩 위치처럼 한 행이 전부 −∞면 최댓값 빼기가 `−∞ − (−∞) = NaN`을 만든다. 안정 softmax도 이 경우는 따로 처리해야 한다(해석 — 가려진 행은 출력 0으로 두는 등).

### 7. 긴 문맥의 가운데를 잘 못 쓴다 — Lost in the Middle

```text
  관련 근거의 위치:   [ 맨 앞 ]  ……  [ 가운데 ]  ……  [ 맨 끝 ]
  성능(경향):            높음          크게 떨어짐        높음        (Liu 외 초록)
```

- Liu 외(TACL 2024) 초록: 여러 문서 질의응답·키-값 검색에서 관련 정보가 입력의 처음이나 끝에 있을 때 성능이 흔히(often) 가장 높고, 긴 문맥의 가운데에 있으면 크게 떨어진다. 긴 문맥용 모델도 마찬가지였다.
- "문맥 한도에 들어간다"와 "모델이 그 정보를 잘 쓴다"는 다른 문제다. 수치 크기는 모델·작업마다 다르므로 우리 작업에서 위치를 바꿔 가며 잰다([19편](../19-llm-evaluation/2-summary.md) 평가).

## 쓰이는 자료구조·알고리즘

| 구조·알고리즘 | 쓰임 | 이어지는 노트 |
|---|---|---|
| 행렬곱 | QKᵀ, A·V, 투영 W_Q·W_K·W_V·W_O | [math/13](../../math/13-linear-algebra-essentials/2-summary.md) |
| softmax + 최댓값 빼기 | 점수 → 가중치 | [03](../03-cross-entropy-and-perplexity/2-summary.md) 5절 |
| 하삼각 마스크 | 인과성(미래 차단) | 2절 |
| 타일링(블록 단위 계산) | FlashAttention의 메모리 이동 줄이기 | [architecture/11](../../architecture/11-memory-hierarchy-and-locality/2-summary.md) · [architecture/21](../../architecture/21-simd-and-gpu/2-summary.md) |
| 이전 K·V 저장 | 마스크 덕분에 가능한 재사용 | [08](../08-kv-cache-and-inference-memory/2-summary.md) |

## 적용 — 풀어나가는 법

### 1. 근거를 넣었는데 답에 반영되지 않을 때 — 증상 → 원리 → 확인

1. **증상**: RAG로 넣은 청크 중 정답이 든 청크가 있었는데 답이 그것을 무시한다.
2. **원리**: 긴 문맥 가운데의 정보는 덜 쓰이는 경향이 있다(Lost in the Middle).
3. **확인**: 같은 질문·같은 청크 집합에서 정답 청크의 위치만 바꿔 정답률을 잰다. 청크 수를 줄여도 재 본다([15편](../15-rag-pipeline/2-summary.md) RAG, [19편](../19-llm-evaluation/2-summary.md) 평가).
4. **완화(해석)**: 관련도가 높은 청크를 문맥의 양 끝에 둔다. 넣는 청크 수를 줄인다(재순위로 상위만 — [17편](../17-hybrid-search-and-reranking/2-summary.md)).

```java
// scratchpad ai/01/e06/EdgeOrder.java — 관련도 순위대로 앞·끝을 번갈아 채운다
static List<Chunk> edgeOrder(List<Chunk> rankedDesc) {
    List<Chunk> front = new ArrayList<>(), back = new ArrayList<>();
    for (int i = 0; i < rankedDesc.size(); i++) {
        if (i % 2 == 0) front.add(rankedDesc.get(i));    // 1·3·5위 → 앞에서부터
        else back.add(0, rankedDesc.get(i));             // 2·4·6위 → 끝에서부터
    }
    front.addAll(back);
    return front;
}
```

(실험, JDK 21.0.12 eclipse-temurin:21-jdk 컨테이너, 2026-10-08)

```text
관련도 순위 c1(최고)…c7 → 문맥 위치 1:c1 2:c3 3:c5 4:c7 5:c6 6:c4 7:c2
```

- 1·2위가 양 끝, 가장 낮은 c7이 가운데에 간다. 이 배치가 우리 작업에서 실제로 나은지는 위 3단계처럼 재서 정한다 — Liu 외는 위치에 따른 경향을 보였을 뿐 이 배치 방법을 검증한 것이 아니다.

### 2. 문맥 길이를 늘리기 전에 — 비용 어림

- 같은 요청에서 프롬프트 길이가 2배면 프롬프트 처리(프리필)의 어텐션 부분은 약 4배 쪽으로 간다(6절, 실험 C). 어텐션 밖의 연산(투영·피드포워드)은 길이에 비례하므로 전체 배율은 4배보다 작을 수 있다(해석).
- 서빙 쪽 메모리는 K·V 저장이 정한다([08편](../08-kv-cache-and-inference-memory/2-summary.md)). 첫 토큰까지 시간(TTFT)은 [10편](../10-inference-latency-metrics/2-summary.md) 지표로 잰다.
- "문맥 한도까지 다 넣기"보다 검색으로 관련 부분만 넣는 쪽이 비용·지연·정확성(7절) 모두에 유리할 수 있다. 우리 작업에서 재서 고른다.

## 장애 시나리오와 대처

### 1. 긴 문맥 가운데의 근거를 못 씀 (⚠ 커리큘럼)

- 현상: RAG로 관련 청크를 넣었는데 답에 반영이 안 된다. 같은 청크를 맨 앞에 두면 맞힌다.
- 보이는 형태: 정답률이 근거 위치에 따라 달라진다. 가운데일 때 가장 낮다.
- 원인: 긴 문맥의 가운데 정보를 덜 쓰는 경향(Liu 외 TACL 2024).
- 대처: 넣는 청크 수를 줄이고(재순위), 높은 관련도를 양 끝에 둔다(적용 1). 위치별 정답률을 평가셋에 넣어 회귀를 감시한다.

### 2. 문맥 길이를 크게 늘림 → 프리필 시간·메모리 급증 (⚠ 커리큘럼)

- 현상: 긴 문서를 통째로 넣기 시작한 뒤 첫 토큰까지 시간과 비용이 크게 늘었다. 자체 서빙이면 GPU 메모리 부족이 난다.
- 보이는 형태: 프롬프트 길이 대비 TTFT가 직선보다 가파르게 는다. 실험 C의 길이 2배 → 시간 약 4배(두 실행에서 ×3.94~×4.36).
- 원인: 어텐션은 모든 쌍을 비교해 길이에 제곱이다(Vaswani 외 표 1). 길이에 비례해 K·V 저장도 는다([08편](../08-kv-cache-and-inference-memory/2-summary.md)).
- 대처: 필요한 부분만 검색해 넣는다([15편](../15-rag-pipeline/2-summary.md)). 같은 앞부분을 재사용하면 프롬프트 캐시를 쓴다([12편](../12-prompt-and-semantic-caching/2-summary.md)). 자체 서빙이면 FlashAttention 같은 IO 인식 커널과 KV 메모리 관리([09편](../09-inference-serving-and-batching/2-summary.md))를 확인한다.

### 3. 자체 구현에서 인과 마스크 누락 → 학습·추론 불일치

- 현상: 작은 실험용 모델이 학습 손실은 매우 낮은데 생성은 엉망이다.
- 보이는 형태: 마스크 없는 모델은 앞 위치의 출력이 뒤 토큰에 따라 바뀐다(실험 A: 마스크 없음 t3 변화 1.59).
- 원인: 학습 때 각 위치가 정답(다음 토큰)을 볼 수 있었다. 추론 때는 미래가 없다.
- 대처: "뒤 토큰을 바꿔도 앞 위치 출력이 같아야 한다"를 단위 테스트로 둔다(실험 A의 검사).

### 4. 전부 가려진 행 → NaN 전파

- 현상: 배치에 길이가 다른 요청을 패딩해 넣었더니 일부 출력이 NaN이다.
- 보이는 형태: 패딩만 있는 위치의 어텐션 가중치가 전부 NaN(실험 D). 다음 층으로 NaN이 퍼진다.
- 원인: 행 전체가 −∞이면 최댓값 빼기에서 `−∞ − (−∞) = NaN`.
- 대처: 전부 가려진 행은 가중치 0으로 따로 처리하거나 그 위치 출력을 버린다. 라이브러리의 마스크 처리 규칙을 확인한다.

## 핵심 문장

- 셀프 어텐션은 각 위치가 Query로 모든 Key와 내적해 softmax 가중치를 만들고, 그 가중치로 Value를 섞는 부드러운 키-값 조회다 — softmax(QKᵀ/√d_k)V.
- 인과 마스크는 미래 칸을 −∞로 가려, 위치 i의 출력이 1..i에만 의존하게 한다. 그래서 뒤에 토큰이 붙어도 앞 계산을 재사용할 수 있다(KV 캐시).
- √d_k로 나누지 않으면 차원이 클수록 내적이 커져 softmax가 한 키에 몰린다(d=1024에서 최대 가중치 0.966 vs 0.248).
- 어텐션은 모든 쌍을 비교하므로 문맥 길이에 제곱으로 비싸진다. FlashAttention은 근사 없이 같은 어텐션 식을 계산하면서(수치 오차 범위 안) 메모리 이동을 줄인다.
- 문맥에 넣은 것과 모델이 쓴 것은 다르다 — 긴 문맥의 가운데 근거는 덜 쓰이는 경향이 있으니 위치를 바꿔 잰다.

## 관련 주제·근거

- 선행
  - 같은 영역 [05편](../05-embeddings-and-similarity/2-summary.md)(embeddings-and-similarity) — 벡터와 내적 유사도
  - [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md) — 내적·행렬곱
  - [03-cross-entropy-and-perplexity](../03-cross-entropy-and-perplexity/2-summary.md) — softmax·log-sum-exp
- 후속·연결
  - [08-kv-cache-and-inference-memory](../08-kv-cache-and-inference-memory/2-summary.md) — 마스크 덕분의 재사용, K·V 메모리
  - 같은 영역 [07편](../07-decoding-and-nondeterminism/2-summary.md)(decoding) · [09편](../09-inference-serving-and-batching/2-summary.md)(serving) · [10편](../10-inference-latency-metrics/2-summary.md)(latency metrics) · [15편](../15-rag-pipeline/2-summary.md)(RAG) · [17편](../17-hybrid-search-and-reranking/2-summary.md)(재순위)
  - [architecture/21-simd-and-gpu](../../architecture/21-simd-and-gpu/2-summary.md) · [architecture/11-memory-hierarchy-and-locality](../../architecture/11-memory-hierarchy-and-locality/2-summary.md) — 데이터 병렬과 메모리 계층
- 논문·교재
  - Vaswani 외, "Attention Is All You Need", NIPS 2017 (arXiv 1706.03762v7) — 3.2.1 식 (1)·각주 4(내적 분산 d_k), 3.2.2 멀티헤드(h=8, d_k=d_v=64), 3.2.3 셀프 어텐션·−∞ 마스크, 3.5 위치 인코딩, 표 1 O(n²·d) <https://arxiv.org/abs/1706.03762> (PDF 2026-10-08 열람)
  - Liu 외, "Lost in the Middle: How Language Models Use Long Contexts", TACL 12권 157–173쪽(2024, arXiv 초고 2023) — 초록 <https://arxiv.org/abs/2307.03172> · <https://aclanthology.org/2024.tacl-1.9/> (2026-10-08 확인)
  - Dao 외, "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness" (arXiv 2022-05-27) — 초록: 제곱 복잡도, IO 인식 정확 어텐션, 타일링 <https://arxiv.org/abs/2205.14135> · 공식 저장소 README Tests 절(기준 구현과 같은 출력·기울기를 수치 허용 오차 안에서 검사) <https://github.com/Dao-AILab/flash-attention> (2026-10-08 확인)
  - Jurafsky·Martin, SLP3 초안(2026-08-19판) 7장 Transformers and Pretraining — 7.1 Attention, 7.3 상삼각 −∞ 마스크와 길이에 제곱, 7.4 RoPE 소개, 7.8 RoPE 등 현재 설정 <https://web.stanford.edu/~jurafsky/slp3/>
- 실험 목록(scratchpad `ai/01/e06/`, `sn-ai-w01-*` 일회용 컨테이너 `--network none`)
  - A. n=5·d=4 인과 마스크 가중치, 마지막 토큰 교체 시 위치별 출력 변화(마스크 유무, seed 6) — `attention.py`, Python 3.12.14
  - B. d=4·64·256·1024의 내적 분산, 스케일 유무 최대 softmax 가중치(키 16, 반복 2000, seed 8) — 같은 파일
  - C. n=128·256·512 순수 Python 인과 어텐션 시간(d=16, 3회 최소, seed 9, `--cpus=2`) — 같은 파일
  - D. 전부 −∞인 행의 softmax — `attention.py --d-only`
  - E. 관련도 순위 청크의 양 끝 배치 — `EdgeOrder.java`, JDK 21.0.12
