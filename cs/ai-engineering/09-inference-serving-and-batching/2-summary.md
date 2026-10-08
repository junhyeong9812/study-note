# ai-engineering/09-inference-serving-and-batching — 추론 서빙과 배칭: 반복 단위 스케줄링, 페이지드 KV, 청크 프리필, 프리필·디코드 분리 — 정리 (힌트)

## 해결하는 문제

LLM 요청 하나는 GPU를 거의 놀린다.\
디코드 단계는 요청마다 토큰 **하나**만 계산하기 때문이다(Sarathi-Serve 초록: "decode iterations have low latency but also low compute utilization").\
그래서 서빙 시스템은 여러 요청을 한 번에 묶어 계산한다(배칭).

```text
  요청 하나씩                         여러 요청을 묶어서
  GPU  [r1 토큰 1개]  [r1 토큰 1개]    GPU  [r1 r2 r3 … r8 토큰 1개씩]  [r1 … r8]
       └ 가중치를 다 읽고 계산은 조금    └ 가중치를 한 번 읽어 8개 요청에 쓴다
```

그런데 LLM 요청은 일반 배치 작업과 두 가지가 다르다.

- **출력 길이를 미리 모른다.** 같은 배치 안에서 10토큰에 끝나는 요청과 500토큰짜리 요청이 섞인다.
- **메모리가 계속 자란다.** 토큰을 하나 만들 때마다 그 요청의 KV 캐시가 늘어난다([08-kv-cache-and-inference-memory](../08-kv-cache-and-inference-memory/2-summary.md)).

쉬운 예: 정원 8명인 셔틀버스다.
- 방식 1: 8명을 태우고, 마지막 승객이 내릴 때까지 차고로 돌아오지 않는다. 첫 정거장에서 내린 사람의 빈자리는 끝까지 빈다. 정류장의 다음 승객은 버스가 돌아올 때까지 기다린다.
- 방식 2: 정거장마다 내린 자리에 기다리던 승객을 바로 태운다.

똑같은 구조다.\
방식 1이 요청 단위(정적) 배칭, 방식 2가 반복 단위(연속) 배칭이다.\
좌석 대신 **KV 캐시 메모리**를 나눠 주는 방식도 같은 문제를 겪는다 — 최대 길이만큼 미리 잡으면 대부분 빈 채로 남는다.

백엔드 실무 예:
- 자체 호스팅한 모델 서버에서 "짧은 질문인데 가끔 몇 초씩 기다린다", "스트림이 중간에 0.5초씩 멈칫한다".
- API로만 호출해도 같은 현상이 보인다. 원인이 제공자 서버의 스케줄링이라는 것을 알아야 클라이언트 타임아웃·지표를 맞게 잡는다([10-inference-latency-metrics](../10-inference-latency-metrics/2-summary.md), [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md)).

## 동작·원리

### 1. 요청 하나 = 프리필 1번 + 디코드 여러 번

```text
  프롬프트 200토큰, 출력 5토큰인 요청

  반복(iteration) →   #1               #2      #3      #4      #5
                     [프리필]          [디코드] [디코드] [디코드] [디코드]
                     프롬프트 200개를   토큰 1개 토큰 1개 토큰 1개 토큰 1개
                     한꺼번에 계산      ...
                     → 첫 토큰 출력     → 2번째  → 3번째  → 4번째  → 5번째(끝)
  KV 캐시 크기        200              201     202     203     204    (토큰마다 1칸씩 자란다)
```

- *프리필(prefill)*: 프롬프트 전체를 병렬로 계산해 KV 캐시를 채우고 첫 출력 토큰을 내는 단계. 계산량이 커서 GPU 연산을 포화시킨다(Sarathi-Serve 초록).
- *디코드(decode)*: 이전 토큰을 넣어 다음 토큰 하나를 만드는 단계. 요청당 토큰 1개라 계산은 적다. 첫 토큰은 프리필이 내므로 반복 횟수는 출력 토큰 수 − 1이다(위 그림: 출력 5개 = 디코드 4번).
- *반복(iteration)*: 모델을 한 번 실행하는 단위. 배치 안 모든 요청이 이번 반복에서 토큰을 하나씩 얻는다.
- 프리필·디코드와 KV 캐시 크기 식은 [08](../08-kv-cache-and-inference-memory/2-summary.md)이 단일 출처다.

### 2. 요청 단위 배칭 vs 반복 단위 배칭 (Orca)

```text
  슬롯 4개, 시간 →  (숫자 = 요청 ID, · = 빈 슬롯, ▲ = 새 요청 합류)

  요청 단위(정적) 배칭: 배치 안의 가장 긴 요청이 끝나야 다음 배치
  슬롯1  1 1 1 · · · · · · ·   ← r1은 3반복 만에 끝났지만 응답도 못 돌려주고 자리도 못 비움
  슬롯2  2 2 2 2 2 2 2 2 2 2
  슬롯3  3 3 · · · · · · · ·
  슬롯4  4 4 4 4 · · · · · ·
         ↑ r5, r6이 이 동안 대기열에서 기다린다

  반복 단위(연속) 배칭: 반복마다 끝난 요청을 빼고 기다리던 요청을 넣는다
  슬롯1  1 1 1 6▲6 6 6 · · ·
  슬롯2  2 2 2 2 2 2 2 2 2 2
  슬롯3  3 3 5▲5 5 5 5 5 · ·
  슬롯4  4 4 4 4 7▲7 7 · · ·
```

- Orca(Yu 외, OSDI 2022)가 기존 시스템의 문제를 이렇게 적었다: 배치에서 먼저 끝난 요청은 클라이언트로 돌아가지 못하고, 새로 도착한 요청은 현재 배치가 완전히 끝날 때까지 기다린다.
- 해법은 *반복 단위 스케줄링(iteration-level scheduling)*이다. 스케줄러가 엔진에 "이 배치로 반복 **한 번**만" 실행시키고, 반복마다 배치 구성을 다시 정한다.
  - *연속 배칭(continuous batching)*: 반복 단위 스케줄링의 흔한 다른 이름. 서빙 소프트웨어 문서에서 주로 쓴다.
- Orca는 배칭과 반복 단위 스케줄링을 트랜스포머에 함께 적용하려고, 선택한 일부 연산에만 배칭을 적용하는 *selective batching*을 썼다(USENIX 초록). 어떤 연산을 빼는지는 본문을 확인하지 않았다 [?].
- Orca 초록의 결과: GPT-3 175B에서 NVIDIA FasterTransformer 대비 같은 지연 수준에서 처리량 36.9배.

### 실험: 정적 배칭 vs 연속 배칭

Python 표준 라이브러리 이산 사건 시뮬레이션이다. 반복 1회 시간은 예시 비용 모형 `5 + 0.02 × (이번 반복의 프리필 토큰) + 0.1 × (디코드 중 요청 수)` ms다(실제 GPU 측정이 아니다).

```python
# 정적: 배치 전체가 가장 긴 요청만큼 돈다. 응답은 배치가 끝나야 돌려준다
steps = max(remain.values())
for s in range(steps):
    t += iter_cost(0, len(batch))
for r in batch:
    r['finish'] = t

# 연속: 반복마다 빈 슬롯에 대기 요청을 넣고, 끝난 요청은 바로 뺀다
while queue and len(running) + len(new) < B:
    new.append(queue.pop(0))
t += iter_cost(sum(r['prompt'] for r in new), len(running))
```

조건: 슬롯 8, 요청 2,000건(포아송 도착), 프롬프트 200토큰, 출력은 80%가 10~50토큰·20%가 400~600토큰, 시드 1·2·3.

(실험, python:3.12-slim Python 3.12.14 `--cpus=2`, 2026-10-08)

```text
도착 초당 2건, seed 1
정적 배칭        처리량     240 tok/s | 대기 평균     1270 ms | 짧은 요청 p50    2736 p99    7539 ms | 긴 요청 p50    4221 ms
연속 배칭        처리량     240 tok/s | 대기 평균        2 ms | 짧은 요청 p50     165 p99     275 ms | 긴 요청 p50    2655 ms
도착 초당 6건, seed 1
정적 배칭        처리량     364 tok/s | 대기 평균   157098 ms | 짧은 요청 p50  161171 p99  316763 ms | 긴 요청 p50  164357 ms
연속 배칭        처리량     717 tok/s | 대기 평균       25 ms | 짧은 요청 p50     183 p99     746 ms | 긴 요청 p50    2836 ms
```

- 시드 2·3도 같은 모양이었다. 초당 2건에서 짧은 요청 p99는 정적 6,630~7,539 ms, 연속 271~275 ms다.
- 초당 2건은 두 방식 모두 감당한다. 처리량이 같고(도착이 정한다) 지연만 다르다. 짧은 요청이 같은 배치의 긴 요청을 기다리느라 p50부터 10배 넘게 길다.
- 초당 6건에서는 정적 배칭의 처리 능력(약 370 tok/s)이 도착(약 720 tok/s)을 못 따라간다. 대기열이 끝없이 자라 대기가 수 분이 된다. 연속 배칭은 같은 슬롯 8개로 따라간다.
- 해석: 정적 배칭에서는 빈 슬롯이 "일하지 않는 GPU"다. 출력 길이의 분산이 클수록 빈 슬롯이 많아진다.

### 3. KV 캐시 메모리 — 연속 할당의 세 낭비와 페이지드 KV (vLLM)

연속 배칭을 해도 동시에 돌릴 수 있는 요청 수는 KV 캐시 메모리가 정한다.\
기존 시스템은 요청마다 **최대 길이만큼 연속 공간**을 미리 잡았다.

```text
  연속 할당 (요청마다 최대 길이 2048칸 예약)
  r1 [■■■■■■□□□□□□□□□□□□□□□□□□□□□□□□]   ■ 실제 토큰  □ 예약했지만 아직(또는 끝내) 안 씀
  r2 [■■□□□□□□□□□□□□□□□□□□□□□□□□□□□□]
      빈 틈 ░░░░  ← 요청마다 크기가 달라 생긴 조각. 새 요청 하나가 들어갈 만큼 크지 않다

  페이지드 (16토큰 블록, 쓰는 만큼 하나씩)
  논리 블록      r1: [0][1][2]        r2: [0]
  블록 테이블    r1: 0→7, 1→1, 2→3    r2: 0→5          ← 프로세스의 페이지 테이블과 같은 역할
  물리 블록      [ ][r1:1][ ][r1:2][ ][r2:0][ ][r1:0] …  ← 흩어져 있어도 된다
                 낭비는 각 요청의 마지막 블록 안쪽뿐
```

- vLLM 논문(Kwon 외, SOSP 2023) §3이 기존 시스템의 KV 낭비를 세 가지로 나눴다(그림 3).
  - *예약(reserved)*: 앞으로 쓸 자리를 미리 잡아 둔 칸. 요청이 끝날 때까지 다른 요청이 못 쓴다.
  - *내부 단편화(internal fragmentation)*: 최대 길이로 잡았는데 실제 출력이 짧아 끝내 안 쓰는 칸.
  - *외부 단편화(external fragmentation)*: 요청마다 할당 크기가 달라 할당 사이에 생기는 쓸모없는 틈.
- 논문의 측정(그림 2, §1 본문): 기존 시스템에서 KV 캐시 메모리 중 실제 토큰 상태를 담는 비율은 20.4%~38.2%뿐이었다.
- *PagedAttention*: KV 캐시를 고정 크기 블록으로 나눠 물리적으로 흩어진 블록에 저장하고, 블록 테이블로 논리 순서를 찾는 어텐션 알고리즘. OS의 가상 메모리·페이징에서 착안했다(초록).
  - 블록은 필요할 때 하나씩 잡으므로 예약·외부 단편화가 없고, 내부 단편화는 마지막 블록 안으로 줄어든다.
- 블록 공유(§4.4): 한 프롬프트에서 출력 여러 개를 뽑을 때(parallel sampling) 프롬프트 블록을 여러 시퀀스가 함께 가리킨다.
  - 물리 블록마다 *참조 카운트*를 둔다. 공유 블록에 쓰려 할 때 참조 카운트가 1보다 크면 새 블록을 잡아 복사한 뒤 쓴다(블록 단위 copy-on-write).
- 메모리가 모자라면 선점한다(§4.5). 스케줄은 FCFS이고, 선점할 때는 가장 늦게 온 요청부터 내보낸다. 한 시퀀스의 블록은 전부 내보내거나 하나도 안 내보낸다(all-or-nothing).
  - 되살리는 방법은 둘이다. CPU 메모리로 *스와핑*하거나, 다시 스케줄될 때 KV를 *재계산*한다.
  - 이것은 2023년 논문 기준이다. 현재 vLLM 문서 "Metrics"(2026-10-08 확인)는 V1에서 스와핑 선점 모드가 더는 쓰이지 않는다(`--swap-space` 제거)고 적는다.
  - vLLM 문서 "Metrics"(2026-10-08 확인)도 선점된 요청은 대기열로 돌아가 프리필을 다시 시작한다고 적는다.
- vLLM 초록의 결과: FasterTransformer·Orca 같은 시스템 대비 같은 지연에서 처리량 2~4배.

### 실험: KV 예산으로 동시 요청 수 어림

같은 출력 길이 분포로 KV 예산 16,384토큰(예시)을 나눠 준다. 산술 모형이다(선점·도착 순서는 반영하지 않는다).

(실험, python:3.12-slim Python 3.12.14, 2026-10-08)

```text
KV 예산 16384 토큰, 요청 최대 길이 2048, 실제 평균 길이 325 토큰
  연속 할당(최대 길이 예약): 동시 8개, 예약 공간 중 낭비 84.1%
  페이지 할당(블록 16 토큰): 평균 동시 49.2개, 마지막 블록 내부 낭비 2.4%
```

- 평균 325토큰짜리 요청에 2,048칸을 잡으면 84%가 빈다. 같은 메모리로 동시 요청이 약 6배 차이 난다.
- 실제 서버에서는 요청이 자라다 블록이 모자라면 선점이 일어난다. 그래서 "평균 동시 49개"는 상한에 가까운 어림이다.

### 4. 긴 프리필이 진행 중인 디코드를 막는다 — 청크 프리필 (Sarathi-Serve)

```text
  디코드 16개가 도는 중에 4,096토큰 프롬프트가 도착

  청크 없음   반복 … [d][d][ 프리필 4096 ─────────── ][d][d] …
                          └ 이 반복 동안 16개 스트림 전부가 멈춘다 (토큰 간 지연 급등)

  청크 512   반복 … [d+P512][d+P512][d+P512] … [d+P512][d] …
                    └ 반복마다 디코드와 프리필 조각을 함께 → 멈춤은 짧고, 새 요청의 첫 토큰은 조금 늦다
```

- Sarathi-Serve(Agrawal 외, OSDI 2024)는 두 단계의 성질 차이를 문제로 짚었다. 프리필 반복은 지연이 크고 연산을 포화시키며, 디코드 반복은 지연이 작고 연산을 덜 쓴다.
- 두 단계가 한 배치에 섞이면 처리량과 지연을 함께 잡기 어렵다(초록).
- *청크 프리필(chunked prefill)*: 프리필 요청을 거의 같은 크기의 조각으로 나눠 여러 반복에 걸쳐 처리한다.
- *stall-free 스케줄*: 진행 중인 디코드를 멈추지 않고 새 요청을 배치에 넣는 스케줄. 청크 프리필이 이를 가능하게 한다.
- 초록의 결과: vLLM 대비 Mistral-7B(A100 1장)에서 서빙 용량 2.6배, Yi-34B(A100 2장)에서 최대 3.7배.

### 실험: 청크 크기와 토큰 간 지연

(실험, python:3.12-slim Python 3.12.14, 2026-10-08 — 같은 예시 비용 모형)

```text
[C] 디코드 16개 진행 중 + 프롬프트 4096 토큰 도착
  청크  4096: 진행 중 디코드의 토큰 간 지연 최대   88.5 ms (평소 6.6 ms), 새 요청 TTFT   88.5 ms
  청크  1024: 진행 중 디코드의 토큰 간 지연 최대   27.1 ms (평소 6.6 ms), 새 요청 TTFT  108.3 ms
  청크   512: 진행 중 디코드의 토큰 간 지연 최대   16.8 ms (평소 6.6 ms), 새 요청 TTFT  134.7 ms
  청크   256: 진행 중 디코드의 토큰 간 지연 최대   11.7 ms (평소 6.6 ms), 새 요청 TTFT  187.5 ms
```

- 청크를 작게 하면 기존 스트림의 멈칫이 88.5 → 11.7 ms로 줄고, 새 요청의 TTFT는 88.5 → 187.5 ms로 늘어난다.
- 해석: 이 모형(대기열 없이 프롬프트 하나가 도착)에서 청크 크기는 "기존 스트림의 토큰 간 지연"과 "새 요청의 첫 토큰 지연"을 맞바꾸는 손잡이다. 반복마다 드는 고정비(모형의 5 ms) 때문에 청크가 작을수록 총 시간이 늘어난다.
- 논문도 방향은 같다. Sarathi-Serve §4.3은 토큰 예산이 작을수록 토큰 간 지연은 줄지만 청크가 잘게 나뉘어 오버헤드가 는다고 적는다(§5.4.1: 청크 512에서 프리필 오버헤드 최대 약 25%). 다만 실제 TTFT에는 대기열·배칭이 더해진다. 청크 프리필과 혼합 배칭을 함께 쓴 Sarathi-Serve는 표 4에서 각 기법만 쓴 경우와 비교해 TTFT와 토큰 간 지연을 함께 낮췄다 — 모형의 맞바꿈을 시스템 전체 법칙으로 읽지 않는다.

### 5. 프리필과 디코드를 다른 GPU에 — 분리 배치 (DistServe)

```text
  같은 GPU에 함께                      나눠서
  GPU0 [P][d d d][P][d d][P] …         프리필 GPU  [P][P][P][P]   ──KV 전송──▶  디코드 GPU [d d d d d d]
       └ 서로 간섭                                  TTFT 목표에 맞춰 배치·병렬도      TPOT 목표에 맞춰
```

- DistServe(Zhong 외, OSDI 2024) 초록: 두 단계를 같은 GPU에 두면 서로 간섭이 강하고, 자원 할당·병렬화 방식도 묶인다.
- 앱마다 중요한 지연이 다르다. 프리필은 TTFT, 디코드는 TPOT를 정한다(정의는 [10](../10-inference-latency-metrics/2-summary.md)).
- DistServe는 프리필과 디코드를 다른 GPU에 두고, TTFT·TPOT 목표에 맞춰 단계별로 자원과 병렬화를 따로 정한다. 대가는 KV 캐시를 GPU 사이로 옮기는 통신이다. 클러스터 대역폭을 보고 배치를 정해 이 통신을 줄인다.
- *goodput*: 논문 §1의 정의는 "SLO 달성 목표(예: 90%)를 지키며 GPU 하나당 감당할 수 있는 최대 요청률"이다. 요청 하나하나를 거르는 값이 아니라, 달성률 조건을 지키는 **최대 부하**다(예: 10건/초 중 90%가 목표를 지켰다고 goodput이 9건/초가 되는 것이 아니다).
- 초록의 결과: 지연 목표를 요청의 90% 넘게 지키면서 기존 시스템 대비 요청 7.4배, 또는 12.6배 엄격한 SLO.

## 쓰이는 자료구조·알고리즘

- **블록 테이블 = 페이지 테이블** — 논리 블록 번호 → 물리 블록 번호. 연속이 아니어도 된다([os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md)).
- **빈 블록 목록과 참조 카운트 + copy-on-write** — 블록을 하나씩 주고 회수한다. 공유 블록은 쓰기 직전에 복사한다(vLLM §4.4, 프로세스 fork와 같은 기법).
- **반복 단위 스케줄러 큐** — 대기열(FCFS)에서 반복마다 빈 슬롯만큼 꺼낸다([data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)).
- **Little 법칙** — 동시 요청 수 = 도착률 × 체류 시간. KV 메모리 어림의 출발점이다([math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)).
- **배치 크기와 지연의 맞바꿈** — DB 배치와 같은 구조다([reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 호출하는 쪽(API 사용자)에서

증상 → 원리 → 할 일 순서다.

| 증상 | 서버 쪽 원리 | 클라이언트에서 할 일 |
|---|---|---|
| 짧은 질문인데 첫 토큰이 가끔 수 초 늦다 | 대기열·배치 적재(선점된 요청은 프리필을 다시 함) | 첫 토큰 타임아웃을 전체 타임아웃과 따로 둔다([11](../11-llm-api-client-contract/2-summary.md)) |
| 스트림이 중간에 0.1~1초 멈칫 | 다른 요청의 긴 프리필이 같은 반복에 끼어듦 | 평균 TPOT가 아니라 토큰 간 지연 분위를 본다([10](../10-inference-latency-metrics/2-summary.md)) |
| 긴 문서 요약이 몰리면 채팅 응답까지 느려진다 | 긴 프롬프트가 KV 메모리와 프리필 시간을 차지 | 긴 작업을 별도 풀·별도 배포로 나눈다(벌크헤드) |

긴 요청을 별도 칸으로 나누는 Java 예(동시 실행 수 상한은 예시):

```java
final class LlmBulkhead {
    private final Semaphore interactive = new Semaphore(32);   // 채팅 — 짧은 프롬프트
    private final Semaphore longJobs = new Semaphore(4);        // 문서 요약 — 긴 프롬프트

    <T> T call(int promptTokens, Callable<T> llmCall) throws Exception {
        Semaphore s = promptTokens > 8_000 ? longJobs : interactive;  // 기준 토큰 수는 예시
        if (!s.tryAcquire(200, TimeUnit.MILLISECONDS)) throw new RejectedExecutionException("LLM 칸 가득 참");
        try { return llmCall.call(); } finally { s.release(); }
    }
}
```

- 기준은 토큰 수다. 글자 수로 가르면 언어에 따라 크게 틀린다([04-tokenization-and-token-cost](../04-tokenization-and-token-cost/2-summary.md)).
- 칸 나누기의 일반 원리는 [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md)가 단일 출처다.

### 2. 직접 서빙하는 쪽에서 — 지표로 확인

vLLM 문서 "Metrics"(2026-10-08 확인)의 지표로 원인을 가른다.

```text
  vllm:num_requests_running / _waiting       실행 중 / 대기 중 요청 수   ← 대기가 쌓이면 용량 부족
  vllm:kv_cache_usage_perc                   KV 블록 사용률(0~1)         ← 1에 붙어 있으면 선점·대기 증가
  vllm:request_queue_time_seconds            대기열 시간 히스토그램
  vllm:inter_token_latency_seconds           스트림 출력 사이 간격      ← 꼬리가 길면 프리필 간섭 의심
  vllm:request_success_total{finished_reason="length"}   길이 한도로 끝난 요청 수
```

- 대기 시간이 늘고 KV 사용률이 1에 가까우면 메모리가 병목이다. 동시 요청 상한·최대 문맥 길이·인스턴스 수를 본다.
- 대기는 없는데 토큰 간 지연 꼬리만 길면 프리필 간섭이다. 청크 프리필 설정·긴 프롬프트 분리를 본다.

### 3. 용량 어림 — Little 법칙 × 토큰당 KV

```text
  동시 요청 수   = 도착률 × 평균 체류 시간           (math/10)
  필요 KV 메모리 = 동시 요청 수 × 요청당 평균 토큰 수 × 토큰당 KV 바이트   (08)

  예시: 초당 5건 × 4초 = 동시 20건
        20건 × 1,500토큰 × 128KiB(Mistral 7B, GQA, fp16 — 08의 계산) = 3,840,000 KiB ≈ 3.66 GiB
```

- 평균만으로 잡으면 긴 문맥 요청이 몰리는 순간을 못 버틴다. 요청당 토큰 수는 분포의 꼬리(p99)로도 한 번 계산한다.

## 장애 시나리오와 대처

### 1. 정적 배칭 → 짧은 요청이 긴 요청을 기다린다 (⚠ 커리큘럼)

- 현상: 짧은 질문의 응답 시간이 들쭉날쭉하고, p99가 긴 요청의 생성 시간에 붙는다.
- 보이는 형태: 클라이언트 타임아웃, "출력 20토큰짜리가 7초 걸림" 같은 로그. 실험에서 짧은 요청 p99가 연속 배칭 271~275 ms 대비 정적 6,630~7,539 ms였다.
- 원인: 배치 안의 가장 긴 요청이 끝날 때까지 배치를 바꾸지 않는다. 끝난 요청도 응답을 못 돌려준다.
- 대처: 반복 단위 스케줄링을 지원하는 서빙 소프트웨어를 쓴다. 정적 배칭밖에 안 되면 출력 길이가 비슷한 요청끼리 다른 큐로 나눈다.

### 2. KV를 연속 공간으로 잡아 단편화 → 배치가 작아지고 처리량이 떨어진다 (⚠ 커리큘럼)

- 현상: GPU 연산 사용률은 낮은데 대기열이 쌓인다.
- 보이는 형태: 메모리 부족으로 새 요청을 못 받는다는 로그, 동시 실행 수가 낮은 값에 고정.
- 원인: 요청마다 최대 길이만큼 연속 공간을 예약한다. vLLM 논문 측정에서 실제 토큰 상태를 담은 비율은 20.4~38.2%였고, 실험 모형에서는 예약 공간의 84.1%가 비었다.
- 대처: 페이지드 KV(블록 할당)를 쓴다. 쓸 수 없으면 최대 출력 길이(`max_tokens`)를 실제 필요에 맞게 낮춘다.

### 3. 긴 프롬프트의 프리필이 진행 중인 디코드를 막는다 → 스트림 멈칫 (⚠ 커리큘럼)

- 현상: 여러 사용자의 스트림이 같은 순간에 함께 멈췄다가 다시 흐른다.
- 보이는 형태: 토큰 간 지연 최댓값·p99가 평소의 몇 배~십수 배로 튄다(실험 모형: 6.6 → 88.5 ms, 약 13배). 평균 TPOT는 거의 그대로라 대시보드가 조용하다([10](../10-inference-latency-metrics/2-summary.md)).
- 원인: 한 반복에서 수천 토큰 프리필을 처리하는 동안 같은 배치의 디코드가 기다린다. 실험에서 4,096토큰 프리필 한 번에 토큰 간 지연이 6.6 → 88.5 ms가 됐다.
- 대처: 청크 프리필을 켜고 청크 크기를 정한다(실험 모형에서는 작을수록 기존 스트림은 매끄럽고 새 요청 TTFT는 늘어났다). 규모가 크면 프리필·디코드 분리 배치를 검토한다.

### 4. KV 메모리가 차서 선점 → 지연이 튀고 GPU 계산이 낭비된다

- 현상: 부하가 높을 때만 일부 요청의 첫 토큰·전체 시간이 크게 늘어난다.
- 보이는 형태: KV 사용률이 1 근처에 붙고, 대기 요청 수가 오르내린다.
- 원인: 생성 중 블록이 모자라 실행 중이던 요청을 내보냈다. 재계산 방식이면 프리필을 다시 한다(vLLM §4.5, vLLM 문서 "Metrics" — V1은 재계산 방식).
- 대처: 동시 요청 상한을 메모리에 맞게 낮추거나, 인스턴스를 늘리거나, 최대 문맥 길이를 줄인다. 앞단에서 부하를 거절하는 편이 선점보다 예측 가능하다([reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)).

### 5. 동시 요청 × 문맥 길이를 곱하지 않고 용량 산정 → 긴 문맥이 몰리면 대기열 적체

- 현상: 평소엔 괜찮다가 긴 문서 처리 배치가 돌 때 전체가 느려진다.
- 보이는 형태: 대기열 시간 히스토그램의 꼬리가 길어지고, 채팅 요청의 TTFT도 함께 오른다.
- 원인: KV 메모리를 평균 길이로 산정했다. 필요한 메모리는 동시 요청 수 × 토큰 수에 비례한다.
- 대처: 적용 3의 식으로 p99 길이까지 계산한다. 긴 작업을 별도 칸·별도 배포로 나눈다(적용 1).

## 핵심 문장

- 디코드는 요청당 토큰 하나라 GPU를 덜 쓴다. 그래서 서빙은 여러 요청을 묶는다.
- 요청 단위 배칭은 가장 긴 요청이 배치를 붙잡는다. 반복 단위(연속) 배칭은 반복마다 끝난 요청을 빼고 새 요청을 넣는다(Orca).
- KV 캐시를 최대 길이만큼 연속으로 잡으면 대부분이 빈다. 페이지드 KV는 고정 크기 블록과 블록 테이블로 OS 페이징처럼 관리한다(vLLM).
- 긴 프롬프트의 프리필은 같은 배치의 디코드를 멈추게 한다. 청크 프리필은 이 멈칫과 새 요청의 TTFT를 맞바꾼다.
- 프리필은 TTFT, 디코드는 TPOT를 정한다. 둘을 다른 GPU에 두면 각 지연 목표에 맞춰 따로 조정할 수 있다(DistServe).

## 관련 주제·근거

- 선행
  - [08-kv-cache-and-inference-memory](../08-kv-cache-and-inference-memory/2-summary.md) — 프리필·디코드, KV 캐시 크기 식(단일 출처)
  - [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md) — 대기열, Little 법칙
  - [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md) — 페이지 테이블
- 후속·연결
  - [10-inference-latency-metrics](../10-inference-latency-metrics/2-summary.md) — TTFT·TPOT·ITL·goodput 정의와 측정
  - [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md) — 첫 토큰·토큰 사이·전체 타임아웃
  - [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md) — 배치 크기와 지연
  - [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md), [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md), [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)
- 논문
  - Yu 외, "Orca: A Distributed Serving System for Transformer-Based Generative Models", OSDI 2022 — iteration-level scheduling, selective batching, 36.9배 <https://www.usenix.org/conference/osdi22/presentation/yu>
  - Kwon 외, "Efficient Memory Management for Large Language Model Serving with PagedAttention", SOSP 2023 — §1·§3.1·그림 2·3(세 낭비, 20.4~38.2%), §4.4(참조 카운트·copy-on-write), §4.5(FCFS·all-or-nothing·스와핑·재계산) <https://arxiv.org/abs/2309.06180>
  - Agrawal 외, "Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve", OSDI 2024(arXiv 2024-03-04) — chunked-prefills, stall-free, 2.6배·3.7배 <https://arxiv.org/abs/2403.02310> · <https://www.usenix.org/conference/osdi24/presentation/agrawal>
  - Zhong 외, "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving", OSDI 2024 — §1 goodput 정의, 7.4배·12.6배 <https://arxiv.org/abs/2401.09670>
  - (확장) Leviathan 외, "Fast Inference from Transformers via Speculative Decoding", ICML 2023 — 출력 분포를 바꾸지 않고 여러 토큰을 병렬 계산 <https://arxiv.org/abs/2211.17192>
- 문서
  - vLLM 문서 "Metrics"(design, 2026-10-08 확인) — 지표 이름, 선점 시 프리필 재시작, `block_size="16"` 예시 출력 <https://docs.vllm.ai/en/latest/design/metrics/>
- 실험 목록 (코드: scratchpad `ai/09/batching_sim.py`, `python:3.12-slim` Python 3.12.14, `--network none --cpus=2`, 2026-10-08)
  - [A] 정적 vs 연속 배칭 — 슬롯 8, 요청 2,000, 도착 초당 2·6건, 시드 1·2·3. 처리량·대기·짧은/긴 요청 지연 분위
  - [B] KV 예산 16,384토큰에서 연속 할당 vs 16토큰 블록 할당의 동시 요청 수·낭비(산술 모형)
  - [C] 디코드 16개 + 4,096토큰 프리필에서 청크 4096·1024·512·256의 최대 토큰 간 지연과 TTFT
  - 비용 모형(`5 + 0.02 × 프리필 토큰 + 0.1 × 디코드 수` ms)은 예시이며 실제 GPU 측정이 아니다
