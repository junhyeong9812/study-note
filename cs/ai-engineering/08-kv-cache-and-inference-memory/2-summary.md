# ai-engineering/08-kv-cache-and-inference-memory — 프리필·디코드, KV 캐시 크기 식, MQA·GQA — 정리 (힌트)

## 해결하는 문제

자체 서빙으로 7B 모델을 올린다. "가중치가 약 13 GB이니 80 GiB GPU면 넉넉하다"고 계산했다. 운영에서는 긴 문맥 요청이 몇 개만 몰려도 메모리가 모자라고 대기열이 쌓인다.

```text
  GPU 메모리
  ┌──────────────────────────┬──────────────────────────────────────────┬────┐
  │ 가중치 (고정)              │ KV 캐시 (요청마다, 토큰마다 자란다)        │여유│
  │ 6.7B × 2B ≈ 12.5 GiB      │ 요청 수 × 문맥 길이 × 토큰당 KV 바이트    │    │
  └──────────────────────────┴──────────────────────────────────────────┴────┘
  LLaMA-7B 구조, fp16: 토큰당 512 KiB → 32,768토큰 한 요청 = 16 GiB      (실험 A)
```

- 생성 중에는 이전 토큰들의 Key·Value 벡터를 저장해 두고 재사용한다. 이것이 *KV 캐시*다(SLP3 7.8).
- 이 캐시는 **동시 요청 수 × 문맥 길이**에 비례해 커진다. 가중치만 보고 산정하면 이 몫을 놓친다.

쉬운 예: 웹 서버의 세션 메모리.
- 서버 프로그램 크기는 고정이다. 접속마다 세션 버퍼가 있고, 대화가 길어질수록 버퍼가 커진다.
- 메모리 산정은 "프로그램 + 동시 접속 수 × 접속당 버퍼"다.

똑같은 구조다.\
프로그램 = 모델 가중치, 접속당 버퍼 = 요청마다의 KV 캐시, 대화 길이 = 문맥 토큰 수.

실무 예:
- vLLM 논문: A100 40GB에서 13B 모델을 서빙할 때 메모리의 약 65%가 가중치, 30% 가까이가 요청 상태(KV 캐시)였다(Kwon 외 2023 1절 그림 1).
- 같은 논문: OPT-13B는 토큰 하나의 KV 캐시가 800 KB, 2048토큰 요청 하나가 최대 1.6 GB다. 메모리를 전부 KV에 써도 수십 요청 정도다(3절).

## 동작·원리

### 1. 프리필과 디코드

```text
  시간 ──────────────────────────────────────────────────────────▶
  ┌──── 프리필 ────┐┌─디코드─┐┌─디코드─┐┌─디코드─┐ …  ┌─디코드─┐
  │ 프롬프트 n토큰  ││ 새 토큰 ││ 새 토큰 ││ 새 토큰 │     │ <eos>  │
  │ 한꺼번에 병렬   ││ 1개     ││ 1개     ││ 1개     │     │        │
  └───────┬───────┘└───┬────┘└───┬────┘└───┬────┘     └────────┘
          │ K·V n개 저장  │ +1개    │ +1개    │ +1개
          ▼              ▼         ▼         ▼
  KV 캐시:  n    →     n+1   →   n+2   →   n+3  …     (토큰마다 자란다)
  첫 토큰은 프리필이 끝나야 나온다
```

- *프리필(prefill)*: 프롬프트 토큰을 처리해 첫 새 토큰의 확률을 계산하고, 프롬프트 전체의 K·V를 만든다. 토큰이 모두 알려져 있어 행렬-행렬 곱으로 병렬 처리된다(Kwon 외 2.2 — 논문은 prompt phase라 부름).
  - 그림은 한 번에 처리하는 경우다. 프롬프트가 아주 길면 여러 조각(chunk)으로 나눠 캐시를 채울 수도 있다(Mistral 7B 논문 2절 "Pre-fill and Chunking" — 메모리 사용을 제한하려고). 조각 프리필 스케줄링은 [09편](../09-inference-serving-and-batching/2-summary.md).
- *디코드(decode)*: 토큰을 하나씩 만든다. 각 걸음은 새 토큰 하나의 K·V만 계산하고 이전 것은 캐시에서 읽는다. 데이터 의존성 때문에 걸음끼리 병렬화되지 않고, 흔히 행렬-벡터 곱이라 GPU 계산을 덜 쓰며 메모리 대역폭에 묶인다(같은 절 — autoregressive generation phase, 한 요청 기준).
  - 여러 요청을 배치로 묶으면 가중치 읽기 비용이 요청들에 나뉘어, 배치가 충분히 크면 계산 비용이 더 커질 수 있다(Kwon 외 2.3). 그래서 "메모리 대역폭에 묶인다"는 단일 요청·작은 배치의 이야기다.
- 마스크 덕분에 앞 위치의 K·V가 뒤 토큰과 무관하다는 것이 재사용의 근거다([06](../06-transformer-and-attention/2-summary.md) 2절).
- Shazeer 2019 초록: 증분 추론(디코드)은 큰 K·V 텐서를 반복해서 읽는 메모리 대역폭 비용 때문에 느리다.

### 2. 무엇을 얼마나 저장하나

```text
  토큰 하나가 남기는 것 (층마다 반복)
  층 1:  K[헤드1](d_head) K[헤드2] … K[헤드 H_kv]   V[헤드1](d_head) … V[헤드 H_kv]
  층 2:  …
  층 L:  …
  ───────────────────────────────────────────────────────────────────
  토큰당 바이트 = 2(K와 V) × L(층) × H_kv(KV 헤드) × d_head(헤드 차원) × b(원소 바이트)
  요청당 바이트 = 토큰당 바이트 × T(그 요청의 토큰 수 = 프롬프트 + 지금까지 생성)
```

- 멀티헤드 어텐션(MHA)에서는 KV 헤드 수 = 쿼리 헤드 수다. Vaswani 외 설정에서는 `H × d_head = d_model`(은닉 차원)이다(3.2.2 — d_k = d_model/h). 이 등식이 성립하지 않는 모델도 있을 수 있으니 설정의 헤드 차원을 직접 확인한다(해석).
- 확인: Kwon 외 3절의 OPT-13B 계산은 `2 × 5120(은닉 차원) × 40(층) × 2(fp16 바이트) = 800 KB`다. 위 식에서 `H_kv × d_head = 5120`을 넣은 것과 같다(실험 A에서 800.0 KiB).

### 실험: 모델 설정표로 KV 캐시 계산 (실험 A)

```java
// scratchpad ai/01/e08/KvBudget.java 핵심
record Model(String name, int layers, int kvHeads, int headDim, int bytesPerElem) {
    long bytesPerToken() { return 2L * layers * kvHeads * headDim * bytesPerElem; }
}
```

(실험, JDK 21.0.12 eclipse-temurin:21-jdk 컨테이너, 2026-10-08 — 결정적 계산. 설정값 출처: LLaMA 논문 표 2, Mistral 7B 논문 표 1, vLLM 논문 3절)

```text
[A] fp16(원소 2바이트) 기준 토큰당 KV, 4K·32K 토큰 한 요청
  LLaMA-7B (MHA, 32층·32헤드·128)             토큰당 512.0 KiB  4,096토큰 2.000 GiB  32,768토큰 16.00 GiB
  Mistral-7B (GQA, 32층·KV 8헤드·128)         토큰당 128.0 KiB  4,096토큰 512.0 MiB  32,768토큰 4.000 GiB
  가상 MQA 변형 (32층·KV 1헤드·128) (예시)          토큰당 16.00 KiB  4,096토큰 64.00 MiB  32,768토큰 512.0 MiB
  OPT-13B (MHA, 40층·은닉 5120)               토큰당 800.0 KiB  4,096토큰 3.125 GiB  32,768토큰 25.00 GiB

[A'] 헤드 수를 빠뜨린 식: 토큰당 16.00 KiB → 실제의 1/32
[A''] Mistral-7B 32,768토큰: 전부 저장 4.000 GiB vs 롤링 버퍼(W=4096) 512.0 MiB → 8배
```

- 관찰 1: LLaMA-7B 구조(차원 4096·헤드 32·층 32 → 헤드 차원 128)는 `2 × 32 × 32 × 128 × 2 = 524,288바이트 = 512 KiB`/토큰이다. 32,768토큰이면 16 GiB로 가중치(약 12.5 GiB)보다 크다. 토큰 수 32,768은 계산용 예시다.
- 관찰 2: 헤드 수를 빠뜨리면 16 KiB/토큰으로 **32배 과소 추정**한다(헤드 32개).
- 관찰 3: OPT-13B 800 KiB는 vLLM 논문의 800 KB와 같다 — 식을 독립 출처로 대조한 것이다. 논문 식의 값은 819,200바이트라 논문의 "KB"는 1024 단위(KiB)로 읽어야 맞는다(계산).
- 관찰 4: Mistral 7B는 KV 헤드가 8개라 LLaMA-7B 구조의 1/4이다. 논문은 슬라이딩 윈도(W = 4096)에 맞춘 롤링 버퍼 캐시를 써서 32k 토큰 시퀀스에서 캐시 메모리를 8배 줄였다고 쓴다. 계산(4 GiB → 512 MiB)도 8배다. 이처럼 모델마다 캐시 구조가 달라 "식 한 줄"에 모델 설정을 정확히 넣어야 한다.
  - Mistral 7B 표 1의 context_len은 8192다. 32k는 논문 문장의 예를 따른 계산이다.

### 3. MQA·GQA — K·V 헤드를 줄인다

```text
  MHA (H_kv = H)      Q1 Q2 Q3 Q4 Q5 Q6 Q7 Q8
                      K1 K2 K3 K4 K5 K6 K7 K8      ← 쿼리 헤드마다 K·V
  GQA (H_kv = G)      Q1 Q2 Q3 Q4 | Q5 Q6 Q7 Q8
                          K1     |     K2          ← 그룹마다 K·V 하나 (예: G = 2)
  MQA (H_kv = 1)      Q1 Q2 Q3 Q4 Q5 Q6 Q7 Q8
                                K1                 ← 모든 쿼리 헤드가 K·V 하나 공유
```

- *MQA(multi-query attention)*: 모든 헤드가 K·V를 공유한다. K·V 텐서가 작아져 증분 디코딩의 메모리 대역폭 요구가 크게 준다. 품질 저하는 작았다(Shazeer 2019 초록).
- *GQA(grouped-query attention)*: 쿼리 헤드를 G개 그룹으로 나누고 그룹마다 K·V 헤드 하나를 둔다. GQA-1 = MQA, GQA-H = MHA(Ainslie 외 2023 2.2). 초록: 품질은 MHA에 가깝고 속도는 MQA에 가깝다.
- 실제 모델: Llama 2는 34B·70B만 GQA이고 7B는 MHA다(Touvron 외 2023b). Mistral 7B는 GQA(KV 헤드 8)다. KV 계산 전에 그 모델의 KV 헤드 수를 설정 파일·논문에서 확인한다.

### 4. 동시 요청 수의 상한

```text
  동시 요청 상한 ≈ KV 풀 ÷ (토큰당 KV × 요청당 토큰 수)
  KV 풀 = GPU 메모리 − 가중치 − 실행 여유(활성값·런타임)
```

### 실험: 80 GiB GPU 한 장의 동시 요청 상한 (실험 B)

(실험, JDK 21.0.12 eclipse-temurin:21-jdk 컨테이너, 2026-10-08 — GPU 80 GiB·여유 10%는 예시 가정, 가중치 6.7B × 2바이트는 LLaMA 논문 표 2의 파라미터 수)

```text
[B] GPU 80 GiB(예시) − 가중치 12.48 GiB − 여유 10%(예시) = KV 풀 59.52 GiB
  모델                                            2,048토큰      8,192토큰     32,768토큰
  LLaMA-7B (MHA, 32층·32헤드·128)                     59개         14개          3개
  Mistral-7B (GQA, 32층·KV 8헤드·128)                238개         59개         14개
  가상 MQA 변형 (32층·KV 1헤드·128) (예시)                1904개        476개        119개
```

- 관찰 1: 같은 GPU에서 요청당 토큰이 4배면 동시 요청 상한이 1/4이다(59 → 14 → 3). 토큰 수와 요청 수는 **곱**으로 메모리를 쓴다.
- 관찰 2: KV 헤드를 32 → 8로 줄이면(GQA) 같은 길이에서 4배 많은 요청을 담는다(59 → 238).
- 이 표는 모든 토큰의 K·V를 보관한다고 본 계산이다. Mistral 7B의 롤링 버퍼(W = 4096)를 쓰면 요청당 캐시가 4,096토큰분(512 MiB)에서 더 자라지 않으므로, 8,192·32,768토큰 칸은 둘 다 `59.52 GiB ÷ 512 MiB` ≈ 119개가 된다(계산). 엔진이 롤링 버퍼를 쓰는지는 엔진 설정으로 확인한다.
- 이 상한은 메모리가 연속 할당 낭비 없이 쓰인다고 본 계산이다. 실제 엔진은 요청의 최대 길이만큼 미리 잡는 방식이면 훨씬 적게 담는다(Kwon 외 3.1). 블록 단위 할당(PagedAttention)은 [09편](../09-inference-serving-and-batching/2-summary.md).

### 5. 캐시가 아끼는 일 (실험 C)

장난감 1층·1헤드 디코더(d=32, 무작위 가중치)로 같은 프롬프트에서 greedy 생성을 캐시 없이/있이 돌린다.

```python
# scratchpad ai/01/e08/kvdecode.py 핵심
if use_cache:
    q = matvec(Wq, EMB[toks[-1]]); h = attend(q, Ks, Vs)          # 캐시에서 읽기
else:
    Ks = [matvec(Wk, EMB[t]) for t in toks]; Vs = [matvec(Wv, EMB[t]) for t in toks]
    proj += len(toks)                                              # 매 걸음 전부 다시
    h = attend(matvec(Wq, EMB[toks[-1]]), Ks, Vs)
```

(실험, Python 3.12.14 python:3.12-slim 컨테이너 `--cpus=2`, 2026-10-08 — 프롬프트 64토큰, seed 10)

```text
[C] d=32, 프롬프트 64토큰, seed 10, greedy
       생성    캐시       K·V 투영 횟수     캐시 길이     시간(s)  출력 동일?
       64    없음            6112       127     2.786
       64    있음             128       128     0.164  True
      256    없음           49024       319    20.985
      256    있음             320       320     0.981  True
```

- 관찰 1: 출력 토큰열이 완전히 같다. 캐시는 결과를 바꾸지 않고 재계산만 없앤다.
- 관찰 2: K·V 투영 횟수는 캐시 없이 `Σ(64..64+s−1)` — 생성 256개면 49,024번, 캐시가 있으면 프롬프트 64 + 생성 256 = 320번이다. 시간도 20.985초 → 0.981초(같은 날 점검 재실행 23.303초 → 1.072초 — 시간은 실행마다 흔들리지만 약 20배 차이는 같다).
- 관찰 3: 대가로 캐시 길이(저장한 K·V 수)가 토큰 수만큼 자란다(320). 캐시 없는 쪽의 319는 마지막 생성 토큰의 K·V를 아직 계산하지 않았기 때문이다.

## 쓰이는 자료구조·알고리즘

| 구조·알고리즘 | 쓰임 | 이어지는 노트 |
|---|---|---|
| 캐시(계산 결과 재사용) | 이전 토큰 K·V 재계산 회피 | [architecture/11](../../architecture/11-memory-hierarchy-and-locality/2-summary.md) |
| 크기 식 `2·L·H_kv·d_head·b·T` | 용량 산정 | 실험 A |
| 링 버퍼(위치 i → i mod W) | Mistral 7B 롤링 버퍼 캐시 | [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) |
| 고정 크기 블록 할당(페이지) | 외부 단편화 제거·내부 단편화 감소(요청당 낭비는 마지막 블록 하나 이내로 남는다 — Kwon 외 1절·4절) — [09편](../09-inference-serving-and-batching/2-summary.md) | [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md) |
| 나눗셈 상한 | 동시 요청 수 | 실험 B, [math/10](../../math/10-queueing-and-littles-law/2-summary.md)(대기열) |

## 적용 — 풀어나가는 법

### 1. 자체 서빙 용량 산정 — 증상 → 원리 → 계산 → 측정

1. **증상**: 긴 문맥 요청이 몰리면 OOM 또는 대기열 적체. 짧은 요청만 올 때는 멀쩡하다.
2. **원리**: KV 캐시 = 동시 요청 수 × 요청당 토큰 × 토큰당 KV. 토큰당 KV는 모델 설정(L·H_kv·d_head)과 원소 바이트로 정해진다.
3. **계산**: 모델 설정 파일·논문에서 층 수·KV 헤드 수·헤드 차원을 확인해 실험 A의 식에 넣는다. GQA·슬라이딩 윈도 여부를 확인한다.
4. **측정**: 서빙 엔진의 KV 사용률 지표를 본다. 예: vLLM은 `vllm:kv_cache_usage_perc` 지표를 낸다(vLLM 문서 "Metrics", 2026-10-08 확인 — sources). 이름은 perc지만 문서 설명은 "Fraction of used KV cache blocks (0–1)"이라 값이 0~1 비율이다 — 경보 문턱을 80이 아니라 0.8로 잡는다. 계산한 상한과 실제 사용률·대기열 길이를 대조한다.

### 2. 산정 코드 (Java 21)

```java
// scratchpad ai/01/e08/KvBudget.java 실험 B 부분 — 동시 요청 상한 = KV 풀 / (토큰당 KV × 요청당 토큰 수)
double gpu = 80.0 * (1L << 30);                 // GPU 메모리 80 GiB (예시)
double weights = 6.7e9 * 2;                     // 파라미터 6.7B × fp16 2바이트
double overhead = 0.10 * gpu;                   // 활성값·런타임 여유 10% (예시)
double kvPool = gpu - weights - overhead;
for (int ctx : new int[]{2048, 8192, 32768})
    System.out.printf(" %10d개", (long) (kvPool / (m.bytesPerToken() * (double) ctx)));
```

- 요청당 토큰 수는 평균이 아니라 **분포의 꼬리**로 잡는다. 긴 요청 몇 개가 메모리를 먼저 채운다(분위는 [data-analysis/05](../../data-analysis/05-percentiles-and-latency-distributions/2-summary.md)).
- 원소 바이트는 KV 캐시의 실제 자료형으로 넣는다. 가중치와 KV의 자료형이 다를 수 있다(엔진 설정 확인).

### 3. API로 쓰는 쪽에서

- 제공자 API를 쓰면 KV 메모리는 제공자가 관리한다. 그래도 긴 프롬프트는 프리필 시간(첫 토큰 지연)과 입력 토큰 비용을 늘린다([10편](../10-inference-latency-metrics/2-summary.md) 지표, [04편](../04-tokenization-and-token-cost/2-summary.md) 토큰 비용).
- 같은 앞부분을 반복해서 보내면 제공자의 프롬프트(프리픽스) 캐시가 그 프리필을 재사용할 수 있다 — [12편](../12-prompt-and-semantic-caching/2-summary.md).

## 장애 시나리오와 대처

### 1. 동시 요청 수 × 문맥 길이를 곱하지 않고 산정 → OOM·대기열 적체 (⚠ 커리큘럼)

- 현상: 부하 시험(짧은 요청)은 통과했는데, 운영에서 긴 문서 요약 요청이 몰린 시간에 OOM이나 대기열 폭증이 난다.
- 보이는 형태: KV 사용률이 100%에 붙고 대기 요청 수가 는다. 실험 B로 보면 LLaMA-7B 구조는 32,768토큰 요청이 3개까지(16 GiB × 3 = 48 GiB) 들어가고 4개째는 59.52 GiB 풀에 들어가지 않는다.
- 원인: KV 캐시가 요청 수와 토큰 수의 곱으로 커진다. 가중치만으로 용량을 잡았다.
- 대처: 요청당 최대 토큰(프롬프트 + 출력 상한)을 정하고, 그 꼬리 기준으로 동시 요청 상한을 계산해 입장 제어한다([reliability/12](../../reliability/12-backpressure-and-load-shedding/2-summary.md)). 부하 시험에 긴 요청 비율을 넣는다([reliability/22](../../reliability/22-capacity-and-load-testing/2-summary.md)).

### 2. 계산에서 헤드 수를 빠뜨림 → 32배 과소 추정 (⚠ 커리큘럼)

- 현상: 설계 문서의 "토큰당 KV 16 KiB, 32K 토큰 512 MiB"를 믿고 배치 크기를 잡았다.
- 보이는 형태: 실제 512 KiB/토큰, 32K 토큰 16 GiB(LLaMA-7B 구조, fp16 — 실험 A′).
- 원인: `2 × 층 × 헤드 차원 × 바이트`만 곱하고 KV 헤드 수(32)를 빠뜨렸다.
- 대처: 식을 `2 × L × H_kv × d_head × b`로 쓰고, 독립 출처 값(OPT-13B 800 KB)으로 계산기를 대조하는 테스트를 둔다.

### 3. GQA·슬라이딩 윈도 모델에 MHA 식을 씀 → 과대 추정

- 현상: Mistral 7B를 올리면서 쿼리 헤드 32로 계산해 동시 요청 상한을 1/4로 잡았다. GPU가 놀았다.
- 보이는 형태: 계산한 상한의 4배를 받아도 KV 사용률에 여유가 있다(실험 B: 59 vs 238).
- 원인: KV 헤드(8)가 아니라 쿼리 헤드(32)를 넣었다. 롤링 버퍼 캐시까지 있으면 긴 시퀀스에서 차이가 더 크다(실험 A″: 8배).
- 대처: 설정의 KV 헤드 수(`n_kv_heads` 등)와 윈도·캐시 구조를 확인하고 넣는다. 측정치로 계산을 보정한다.

### 4. 출력이 길어지며 생성 도중 메모리 부족

- 현상: 시작할 때는 들어간 요청이 생성 도중 선점(preemption)되거나 실패한다.
- 보이는 형태: 긴 출력 요청의 실패·재시작이 많다. 대기열이 출렁인다.
- 원인: 디코드 중에도 토큰마다 KV가 자란다. Kwon 외 3절: 출력 길이가 늘면 KV 메모리도 늘어 들어오는 요청이나 진행 중 생성의 메모리를 고갈시킬 수 있고, 시스템은 일부 요청의 KV를 지우거나 내보내는 스케줄링 결정을 해야 한다.
- 대처: 출력 토큰 상한(`max_tokens` 류)을 요청마다 두고 산정에 포함한다. 선점·재계산 정책은 [09편](../09-inference-serving-and-batching/2-summary.md).

## 핵심 문장

- 생성은 프롬프트를 병렬로 처리하는 프리필(긴 프롬프트는 조각으로 나눌 수도 있다)과 토큰을 하나씩 만드는 디코드로 나뉘고, 디코드는 이전 토큰의 K·V를 KV 캐시에서 읽는다.
- KV 캐시 크기 = 2 × 층 × KV 헤드 × 헤드 차원 × 원소 바이트 × 토큰 수 — LLaMA-7B 구조 fp16은 토큰당 512 KiB, 32K 토큰 16 GiB다.
- KV 캐시는 동시 요청 수와 문맥 길이의 곱으로 커진다. 가중치만 보고 메모리를 산정하면 긴 요청이 몰릴 때 무너진다.
- MQA·GQA는 K·V 헤드를 줄여 KV 캐시를 줄인다. 계산에는 쿼리 헤드가 아니라 KV 헤드 수를 넣는다.
- 캐시는 결과를 바꾸지 않고 재계산만 없앤다 — 대가는 토큰마다 자라는 메모리다.

## 관련 주제·근거

- 선행
  - [06-transformer-and-attention](../06-transformer-and-attention/2-summary.md) — 어텐션·멀티헤드·인과 마스크
- 후속·연결
  - 같은 영역 [09편](../09-inference-serving-and-batching/2-summary.md)(serving and batching) — 연속 배칭·PagedAttention, [10편](../10-inference-latency-metrics/2-summary.md)(latency metrics) — TTFT·TPOT, [12편](../12-prompt-and-semantic-caching/2-summary.md)(prompt caching)
  - [architecture/11-memory-hierarchy-and-locality](../../architecture/11-memory-hierarchy-and-locality/2-summary.md) — 메모리 대역폭과 캐시
  - [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md) — 블록 할당의 원형
  - [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md) · [reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md) — 입장 제어·용량 시험
- 논문·문서
  - Kwon 외, "Efficient Memory Management for Large Language Model Serving with PagedAttention", SOSP 2023 (arXiv 2309.06180) — 1절 그림 1(13B·A100 40GB: 가중치 약 65%, KV 30% 가까이), 2.2 prompt phase·autoregressive generation phase(메모리 대역폭에 묶임), 2.3 배치가 충분히 크면 가중치 이동 비용이 나뉘어 계산 비용이 우세해질 수 있음, 1절 PagedAttention = 외부 단편화 제거·내부 단편화 감소, 3절 OPT-13B 800 KB/토큰·2048토큰 1.6 GB·출력 길이에 따른 증가, 3.1 최대 길이 선할당 <https://arxiv.org/abs/2309.06180> (PDF 2026-10-08 열람)
  - Shazeer, "Fast Transformer Decoding: One Write-Head is All You Need" (arXiv 1911.02150, 2019) — 초록 <https://arxiv.org/abs/1911.02150>
  - Ainslie 외, "GQA", EMNLP 2023 (arXiv 2305.13245) — 2.2 그룹·GQA-1 = MQA·GQA-H = MHA, 그림 2 <https://arxiv.org/abs/2305.13245>
  - Touvron 외, "LLaMA" (arXiv 2302.13971) 표 2 — 6.7B: 차원 4096·헤드 32·층 32 <https://arxiv.org/abs/2302.13971> · Touvron 외, "Llama 2" (arXiv 2307.09288) — 34B·70B만 GQA
  - Jiang 외, "Mistral 7B" (arXiv 2310.06825) 표 1 — 층 32·head_dim 128·헤드 32·KV 헤드 8·window 4096·context_len 8192, Rolling Buffer Cache(32k 토큰에서 8배 절감)·Pre-fill and Chunking(긴 프롬프트를 조각으로 프리필) <https://arxiv.org/abs/2310.06825>
  - Vaswani 외 2017 3.2.2 — d_k = d_model/h
  - Jurafsky·Martin, SLP3 초안(2026-08-19판) 7.8 — KV cache 소개(그림 7.23)
  - vLLM 문서 "Metrics"(design) — `vllm:kv_cache_usage_perc` <https://docs.vllm.ai/en/latest/design/metrics/> (2026-10-08 확인, 작업 폴더 sources.md #56)
- 실험 목록(scratchpad `ai/01/e08/`, `sn-ai-w01-*` 일회용 컨테이너 `--network none`)
  - A·A′·A″. 모델 설정표로 토큰당·요청당 KV(LLaMA-7B·Mistral-7B·가상 MQA·OPT-13B), 헤드 누락 오류, 롤링 버퍼 — `KvBudget.java`, JDK 21.0.12
  - B. 80 GiB(예시) GPU의 동시 요청 상한(2K·8K·32K 토큰) — 같은 파일
  - C. 장난감 디코더의 캐시 없음/있음 — 출력 동일성, K·V 투영 횟수, 시간(프롬프트 64, 생성 64·256, seed 10) — `kvdecode.py`, Python 3.12.14
