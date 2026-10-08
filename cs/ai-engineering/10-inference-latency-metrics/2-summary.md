# ai-engineering/10-inference-latency-metrics — 추론 지연 지표: TTFT·TPOT·ITL·종단 지연·goodput, 그리고 도구마다 다른 정의 — 정리 (힌트)

## 해결하는 문제

LLM 응답은 한 번에 오지 않고 토큰이 흘러나온다(스트리밍).\
그래서 "응답 시간 2초"라는 숫자 하나로는 사용자가 겪는 것을 설명하지 못한다.

```text
  같은 2초짜리 응답 두 개
  A  ·································▌첫 글자 1.9초 ▌▌  (오래 빈 화면, 그다음 한꺼번에)
  B  ·▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌    (0.1초에 시작, 꾸준히 흐름)
  종단 지연은 같다. 사용자 체감은 완전히 다르다.
```

쉬운 예: 동영상 스트리밍이다.
- 재생 버튼을 누르고 첫 화면이 나올 때까지의 시간(시작 지연)이 있다.
- 재생 중에 화면이 멈추는 끊김이 있다.
- 둘은 원인도 대책도 다르다. 평균 다운로드 속도 하나로는 끊김을 못 본다.

똑같은 구조다.\
LLM에서는 첫 토큰까지의 시간(TTFT), 토큰 사이 시간(TPOT·ITL), 전체 시간(종단 지연)을 따로 잰다.

백엔드 실무 예:
- 챗봇 SLO를 "p95 TTFT 1초 이하, p95 토큰 간 지연 100 ms 이하"처럼 두 개로 잡는다(수치는 예시).
- 서빙 엔진(vLLM)·관측 규약(OpenTelemetry)·벤치마크 도구가 같은 이름의 지표를 **다르게** 정의한다. 섞어 비교하면 회귀가 아닌 것을 회귀로 본다.

## 동작·원리

### 1. 한 요청의 시간축

```text
 클라이언트          게이트웨이·네트워크       모델 서버
 요청 보냄 ─────────────────────────────▶ 도착(arrival)
    │                                     대기열(queue)
    │                                     스케줄됨 → 프리필
    │                                     첫 토큰 생성 ──┐
 첫 청크 받음 ◀───────────────────────────────────────┘
    │  ◀── 청크 ── 청크 ── (멈칫) ── 청크 ── 청크          디코드
 마지막 받음 ◀──────────────────────────── 마지막 토큰

 |←──────── 클라이언트 TTFT ─────────→|
             |←── 서버 TTFT ─→|                        (서버 TTFT ≈ 입력 처리 + 대기열 + 프리필)
 |←──────────────────────── 종단 지연(E2E) ─────────────────────→|
                                      |←─ ITL ─→|            (스트림 출력 사이 간격, 하나하나)
```

- *TTFT(time to first token)*: 요청부터 첫 출력 토큰까지. 어디서부터 재느냐가 도구마다 다르다(§2).
- *TPOT(time per output token)*: 첫 토큰 이후 토큰 하나당 평균 시간. 요청 하나에 값 하나다.
  - vLLM 정의: `(종단 지연 − TTFT) / (출력 토큰 수 − 1)`.
- *ITL(inter-token latency)*: 연속한 스트림 출력 사이 간격. 요청 하나에 값이 여러 개다.
  - 흔한 오해: ITL과 TPOT가 같은 값이라는 생각. 출력 하나에 토큰이 여러 개 묶여 오면 둘이 갈린다(vLLM 문서 "Metrics").
- *종단 지연(E2E latency)*: 요청부터 마지막 토큰까지. 대략 `TTFT + (출력 토큰 수 − 1) × TPOT`이다.
- *goodput*: DistServe(OSDI 2024) §1의 정의는 "SLO 달성 목표(예: 90%)를 지키며 GPU 하나당 감당할 수 있는 최대 요청률"이다. 목표를 지킨 요청의 비율(SLO 달성률)이 아니라, 그 비율이 목표 이상인 동안 받을 수 있는 최대 부하다.
  - 흔한 오해: "목표를 지킨 요청 수 / 전체 요청 수"를 goodput이라 부르는 것. 그것은 SLO 달성률이다.
- 프리필이 TTFT를, 디코드가 TPOT를 정한다(DistServe 초록). 두 단계가 어떻게 서로 간섭하는지는 [09-inference-serving-and-batching](../09-inference-serving-and-batching/2-summary.md)이 다룬다.

### 2. 같은 이름, 다른 정의

| 지표 | 정의(원문 요지) | 시작점 | 단위 |
|---|---|---|---|
| vLLM `vllm:time_to_first_token_seconds` | 첫 토큰까지. 프런트엔드 도착 시각(토크나이즈 시작) 기준 | 서버 도착 | 요청 |
| vLLM `vllm:request_time_per_output_token_seconds` | `(E2E − TTFT)/(출력 토큰 − 1)`, 토큰 1개 이하 요청은 **0으로 기록** | — | 요청 |
| vLLM `vllm:inter_token_latency_seconds` | 연속한 스트림 출력 사이 간격, 출력 이벤트마다 1표본 | — | 출력 이벤트 |
| OTel `gen_ai.server.time_to_first_token` | 성공 응답의 첫 토큰 생성 시간. 규약 설명: 대기열·프리필에 쓴 시간을 보는 데 도움 | 서버 | 요청 |
| OTel `gen_ai.server.time_per_output_token` | 요청 시간에서 첫 토큰 시간을 빼고 첫 토큰 이후 토큰 수로 나눔 | — | 요청 |
| OTel `gen_ai.client.inference.time_to_first_chunk` | 클라이언트가 요청을 보낸 때부터 첫 **청크**를 받을 때까지 | 클라이언트 | 요청 |
| OTel `gen_ai.client.inference.time_per_output_chunk` | 첫 청크 이후 청크마다, 이전 청크 끝부터 이번 청크 끝까지 | — | 청크 |

- 출처: vLLM 문서 "Metrics"(design), OpenTelemetry GenAI semantic conventions의 `gen-ai-metrics.md`·`client-inference.md`(모두 2026-10-08 확인).
- OTel GenAI 규약은 상태가 **Development**다. 이름·정의가 바뀔 수 있다. 원래 `semantic-conventions` 저장소에 있다가 `semantic-conventions-genai` 저장소로 옮겨졌다.
- 세 가지 함정이 이 표에 있다.
  - **서버 TTFT ≠ 클라이언트 TTFT.** 서버 쪽은 네트워크·게이트웨이·TLS 연결을 모른다. vLLM 문서도 프런트엔드는 엔진 안쪽 대기 시각을 직접 볼 수 없어 엔진이 시각을 기록한다고 적는다.
  - **토큰 ≠ 청크.** 클라이언트는 토큰이 아니라 SSE 이벤트(청크)를 받는다. 청크 하나에 토큰이 여러 개일 수 있다(예: speculative decoding — vLLM 문서).
  - **0으로 기록 vs 제외.** vLLM Prometheus 지표는 토큰 1개 이하 요청의 TPOT를 0으로 넣고, `vllm bench serve`는 TPOT 통계에서 뺀다. 그래서 둘의 TPOT가 다를 수 있다고 문서가 직접 적는다.

### 3. 평균이 숨기는 것 — 무엇을 단위로 모으나

```text
  토큰 40개, 평소 간격 20 ms, 20번째 토큰 앞에서 600 ms 멈칫

  ITL(간격 39개):  20 20 20 … 20 [620] 20 … 20      ← 최댓값·p99가 멈칫을 보여 준다
  TPOT(요청 1개):  (E2E − TTFT) / 39 ≈ 35 ms         ← 600 ms가 39칸에 나눠져 "조금 느림"으로 보인다
```

- TPOT는 요청 하나에 평균 하나다. 한 번의 긴 멈칫이 수십 개 토큰에 나눠진다.
- 사용자가 느끼는 끊김은 간격 하나하나다. 그래서 ITL의 분위·최댓값을 본다.
- 분위·히스토그램을 다루는 법은 [data-analysis/05-percentiles-and-latency-distributions](../../data-analysis/05-percentiles-and-latency-distributions/2-summary.md)가 단일 출처다.

### 실험: 로컬 SSE 모형 서버로 같은 응답을 여러 정의로 재기

JDK `HttpServer`로 Anthropic Messages 스트림 이벤트(`message_start` → `content_block_delta` … → `message_delta` → `message_stop`)를 본뜬 모형 서버를 만들었다.\
서버는 게이트웨이 구간(100 ms, 서버 시계 밖) → 대기열 300 ms → 프리필 200 ms → 토큰 간격 20 ms로 응답한다. 서버는 자기 시계로 잰 TTFT를 마지막 이벤트에 넣는다(이 모형만의 필드).\
클라이언트는 JDK `HttpClient`로 이벤트 도착 시각을 `System.nanoTime()`으로 기록한다.

| 시나리오 | 서버 동작 |
|---|---|
| steady | 토큰 40개, 이벤트당 토큰 1개 |
| stall | steady와 같고, 20번째 토큰 앞에서 600 ms 멈춤 |
| bundle4 | 토큰 40개를 이벤트당 4개씩 묶어 80 ms마다 |
| one-token | 토큰 1개 |

```java
long t0 = System.nanoTime();
HttpResponse<InputStream> res = http.send(req, HttpResponse.BodyHandlers.ofInputStream());
// … SSE 줄 파서: 빈 줄마다 이벤트 하나, 도착 시각 기록 …
double ttft = (deltaTimes.get(0) - t0) / 1e6;                 // 클라이언트 TTFT
double e2e  = (stopAt - t0) / 1e6;
double tpot = tokens <= 1 ? 0.0 : (e2e - ttft) / (tokens - 1); // vLLM 식을 클라이언트 이벤트 시각에 적용(시각 기준은 vLLM과 다름)
for (int i = 1; i < deltaTimes.size(); i++)                    // ITL = 이벤트 간격
    itl.add((deltaTimes.get(i) - deltaTimes.get(i - 1)) / 1e6);
```

시나리오마다 5회, 표에는 1회차와 5회차를 적었다. 전체 실행을 2번 했다.

(실험, eclipse-temurin:21-jdk OpenJDK 21.0.12, `--network none --cpus=2`, 서버·클라이언트 모두 컨테이너 안 127.0.0.1, 2026-10-08)

```text
scenario       cTTFT     sTTFT       E2E      TPOT   ITLmean    ITLmax  events
steady         877.4     596.6    1673.6     20.42     19.94      32.0      40  (rep 1)
steady         645.4     501.7    1402.8     19.42     19.41      20.8      40  (rep 5)
stall          646.6     501.6    2004.9     34.83     34.82     620.3      40  (rep 1)
stall          644.7     501.1    1997.0     34.67     34.67     620.2      40  (rep 5)
bundle4        645.7     501.2    1328.3     17.50     75.81      80.5      10  (rep 1)
bundle4        645.9     501.2    1329.0     17.52     75.84      80.6      10  (rep 5)
one-token      645.9     501.3     645.9      0.00      0.00       0.0       1  (rep 1)
one-token      647.4     501.8     647.4      0.00      0.00       0.0       1  (rep 5)
전체 20요청 평균 TPOT(토큰 1개 응답=0 포함) 17.98 ms | 토큰 1개 응답 제외 23.97 ms
steady+stall 10요청: 평균 TPOT 27.20 ms, 최대 TPOT 34.84 ms
이벤트 간격(ITL) 435개: p50 20.4 ms, p99 620.2 ms, max 620.6 ms
```

- 두 번째 실행도 같은 모양이었다(평균 TPOT 18.01 / 24.02 ms, ITL p99 620.1 ms, 첫 요청 cTTFT 926.8 ms).
- **클라이언트 TTFT − 서버 TTFT ≈ 145 ms.** 게이트웨이 100 ms에 연결·전달 시간이 더해졌다. 첫 요청은 연결 수립·JIT 준비로 그 차이가 약 270~330 ms였다(재실행 포함). 서버 지표만 보면 이 구간이 통째로 안 보인다.
- **stall**: 600 ms 멈칫이 있었는데 TPOT는 34.8 ms("조금 느림")다. ITL 최댓값 620 ms가 멈칫을 보여 준다. 435개 간격 중 멈칫은 5개(약 1.1%)라 p99에 겨우 걸렸다 — 멈칫이 더 드물면 p99에도 안 걸린다. 최댓값이나 요청별 최대 ITL을 함께 본다.
- **bundle4**: 서버 속도는 steady와 비슷한데(TPOT 17.5 ms), 이벤트 간격 평균은 75.8 ms다. ITL로 TPOT 목표(예: 25 ms)를 판정하면 멀쩡한 서버를 3배 느리다고 본다.
- **one-token**: TPOT가 0으로 기록돼 20요청 평균을 17.98 ms로 끌어내렸다. 1토큰 응답을 빼면 23.97 ms다. 분류·예/아니오 응답처럼 짧은 응답의 비율이 바뀌기만 해도 평균 TPOT가 움직인다.

## 쓰이는 자료구조·알고리즘

- **히스토그램(고정 버킷 경계)** — OTel 규약이 지표마다 버킷 경계를 권한다. 예: `gen_ai.server.time_to_first_token`은 `[0.001, 0.005, …, 10.0]`초, `gen_ai.server.time_per_output_token`은 `[0.01, 0.025, …, 2.5]`초(2026-10-08 확인). 분위는 버킷에서 근사한다([data-analysis/05](../../data-analysis/05-percentiles-and-latency-distributions/2-summary.md)).
- **단조 시계** — 간격은 벽시계가 아니라 단조 시계로 잰다(Java `System.nanoTime()`). vLLM 문서도 같은 프로세스의 단조 타임스탬프로 간격을 계산해야 해서 엔진이 시각을 기록한다고 적는다.
- **요청 단위 vs 이벤트 단위 집계** — 같은 데이터를 요청마다 평균 하나로 모으느냐(TPOT), 간격마다 표본 하나로 모으느냐(ITL)가 결과를 바꾼다.

## 적용 — 풀어나가는 법

### 1. 클라이언트에서 네 시각을 남긴다

증상: "모델이 느려졌다"는 신고. 원리: 대기열·프리필·네트워크·디코드 중 어디가 늘었는지 시각을 나눠야 안다.

```java
record StreamTiming(long sentNs, long firstChunkNs, long lastChunkNs, long maxGapNs, int chunks, int outputTokens) {
    double ttftMs()   { return (firstChunkNs - sentNs) / 1e6; }
    double e2eMs()    { return (lastChunkNs - sentNs) / 1e6; }
    OptionalDouble tpotMs() {                                  // 토큰 1개 이하는 "없음"으로 — 0을 넣지 않는다
        return outputTokens <= 1 ? OptionalDouble.empty()
                : OptionalDouble.of((lastChunkNs - firstChunkNs) / 1e6 / (outputTokens - 1));
    }
    double maxGapMs() { return maxGapNs / 1e6; }               // 요청별 최대 청크 간격 — 멈칫 탐지
}
```

- `outputTokens`는 청크 수가 아니라 제공자가 응답 끝에 알려 주는 사용량(예: Anthropic `message_delta`의 `usage.output_tokens` — 누적값, 2026-10-08 확인)으로 채운다.
- 클라이언트 지표 이름은 OTel의 `gen_ai.client.inference.time_to_first_chunk`·`time_per_output_chunk`를 따르면 서버 지표와 섞이지 않는다.
- 단, OTel은 "응답 스트림에서 받은 첫 청크"까지로만 정의한다(2026-10-08 확인). Anthropic 스트림은 글자보다 `message_start` 이벤트가 먼저 온다. 첫 **글자**(첫 `content_block_delta`)까지를 재려면 OTel 이름과 섞지 말고 별도 이름(예: `ttft_first_content_client`)으로 두거나, 어느 이벤트를 첫 청크로 봤는지 함께 기록한다.

### 2. 대시보드는 정의를 이름에 붙여 나눠 둔다

```text
  ttft_client_p95        ttft_server_p95           ← 둘의 차이 = 네트워크·게이트웨이·연결
  tpot_p50 (n>1만)       count(n<=1)               ← 0을 섞지 않고, 짧은 응답 비율은 따로
  chunk_gap_p99          max_chunk_gap_per_request_p95   ← 멈칫
  e2e_p95                output_tokens_p50/p95     ← E2E가 늘면 출력 길이부터 확인
  slo_attainment = TTFT 목표와 토큰 간 지연 목표를 둘 다 지킨 요청 / 전체 요청
  goodput ≈ slo_attainment ≥ 목표(예: 90%)를 지킨 최대 요청률   ← 부하 시험·용량 계획에서 구한다
```

- 회귀를 비교할 때는 같은 정의·같은 시작점·같은 출력 길이 분포끼리만 비교한다.
- E2E는 출력 토큰 수에 거의 비례한다. 프롬프트를 바꿔 답이 길어지면 모델이 그대로여도 E2E가 오른다.

### 3. 서빙 엔진 쪽은 엔진 지표로

- vLLM이면 `vllm:time_to_first_token_seconds`(서버 도착 기준), `vllm:inter_token_latency_seconds`(출력 사이), `vllm:request_queue_time_seconds`(대기열)를 함께 본다(vLLM 문서 "Metrics", 2026-10-08 확인).
- 대기열 시간이 TTFT 증가의 대부분이면 용량 문제, 프리필 시간이 늘었으면 프롬프트 길이 문제다([09](../09-inference-serving-and-batching/2-summary.md)).

## 장애 시나리오와 대처

### 1. 평균 TPOT만 보다가 스트림 멈칫을 놓친다 (⚠ 커리큘럼)

- 현상: 사용자는 "답이 중간에 멈춘다"고 하는데 대시보드는 정상이다.
- 보이는 형태: 평균 TPOT는 평소보다 조금 높을 뿐이다. 실험에서 600 ms 멈칫이 있는 요청의 TPOT가 34.8 ms(평소 19.4 ms)였다.
- 원인: TPOT는 요청마다 평균 하나라 한 번의 긴 간격이 수십 토큰에 나눠진다.
- 대처: 청크 간격의 p99와 요청별 최대 간격을 지표로 둔다. 멈칫이 드물면 p99에도 안 걸리므로 최댓값 분위도 본다.

### 2. 서버 TTFT와 클라이언트 TTFT를 섞어 비교 → 맞지 않는 회귀 경보 (⚠ 커리큘럼)

- 현상: 클라이언트 측 TTFT 경보가 울리는데 서빙 엔진의 TTFT는 그대로다. 또는 반대.
- 보이는 형태: 두 대시보드의 TTFT가 일정한 차이(실험에서 약 145 ms, 첫 요청은 그 이상)로 벌어진다.
- 원인: 서버 TTFT는 서버 도착부터 잰다. 게이트웨이·네트워크·TLS 연결 시간은 클라이언트에만 보인다.
- 대처: 지표 이름에 측정 위치를 붙인다(`_client`, `_server`). 경보는 사용자 체감인 클라이언트 쪽에, 원인 분석은 둘의 차이로 한다.

### 3. ITL과 TPOT를 같은 것으로 비교 → 멀쩡한 서버를 느리다고 판정 (⚠ 커리큘럼)

- 현상: 새 서빙 설정(또는 speculative decoding)을 켠 뒤 "토큰 간 지연"이 3~4배 나빠졌다.
- 보이는 형태: 출력 이벤트 수가 토큰 수보다 적다. 실험 bundle4에서 TPOT 17.5 ms, 이벤트 간격 평균 75.8 ms.
- 원인: 출력 이벤트 하나에 토큰이 여러 개 묶였다. ITL은 이벤트 사이, TPOT는 토큰 사이를 잰다.
- 대처: 목표가 "토큰 생성 속도"면 TPOT로, "화면 끊김"이면 청크 간격으로 정한다. 두 값을 한 그래프에 같은 이름으로 그리지 않는다.

### 4. 토큰 1개 이하 응답을 TPOT 0으로 기록 → 평균이 끌려 내려간다 (⚠ 커리큘럼)

- 현상: 기능 하나(분류·예/아니오)를 추가했더니 평균 TPOT가 "개선"됐다.
- 보이는 형태: 실험에서 20요청 중 5개가 1토큰 응답일 때 평균 TPOT 17.98 ms, 제외하면 23.97 ms.
- 원인: vLLM 지표는 토큰 1개 이하 요청의 TPOT를 0으로 넣는다. 짧은 응답의 비율이 평균을 움직인다.
- 대처: TPOT는 출력 2토큰 이상만 모으고, 짧은 응답 수를 따로 센다. 벤치마크(`vllm bench serve`는 제외)와 Prometheus 지표를 섞지 않는다.

### 5. 출력이 길어진 것을 모델이 느려졌다고 오인

- 현상: 프롬프트 수정 배포 뒤 E2E p95가 40% 올랐다.
- 보이는 형태: TTFT·TPOT는 그대로, 출력 토큰 수 분포가 오른쪽으로 이동.
- 원인: E2E ≈ TTFT + (출력 토큰 − 1) × TPOT. 출력 길이가 늘면 E2E가 함께 늘어난다.
- 대처: E2E 회귀 경보에 출력 토큰 수 분위를 함께 띄운다. 길이 상한이 필요하면 `max_tokens`와 프롬프트로 조정하고, 잘린 응답 처리는 [11](../11-llm-api-client-contract/2-summary.md)을 따른다.

## 핵심 문장

- LLM 지연은 셋으로 나눠 잰다. 첫 토큰까지(TTFT), 토큰 사이(TPOT·ITL), 전체(종단 지연).
- 서버 TTFT는 주로 대기열 + 프리필이고(vLLM은 토크나이즈 같은 입력 처리도 포함), 클라이언트 TTFT는 여기에 게이트웨이·네트워크·연결이 더해진다.
- TPOT는 요청마다 평균 하나라 드문 긴 멈칫을 숨긴다. 끊김은 출력 간격의 분위·최댓값으로 본다.
- 클라이언트가 받는 단위는 토큰이 아니라 청크다. 청크에 토큰이 묶이면 ITL과 TPOT가 갈린다.
- 같은 이름의 지표라도 vLLM·OpenTelemetry·벤치마크 도구의 정의가 다르다. 정의를 확인하고 같은 정의끼리만 비교한다.

## 관련 주제·근거

- 선행
  - [08-kv-cache-and-inference-memory](../08-kv-cache-and-inference-memory/2-summary.md) — 프리필·디코드
  - [data-analysis/05-percentiles-and-latency-distributions](../../data-analysis/05-percentiles-and-latency-distributions/2-summary.md) — 분위·히스토그램(단일 출처)
  - [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md) — SLO·SLI
- 후속·연결
  - [09-inference-serving-and-batching](../09-inference-serving-and-batching/2-summary.md) — 지연을 만드는 서버 스케줄링
  - [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md) — 첫 토큰·토큰 사이·전체 타임아웃
  - [23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md) — OTel GenAI 스팬·비용 집계
  - [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md), [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md)
  - [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md) — SSE 와이어 형식
- 문서·논문
  - vLLM 문서 "Metrics"(design, 2026-10-08 확인) — 지표 목록, TTFT의 시작점(arrival_time, 토크나이즈 시작), ITL vs TPOT 차이, 1토큰 이하 TPOT 0 기록과 `vllm bench serve` 제외 <https://docs.vllm.ai/en/latest/design/metrics/>
  - OpenTelemetry GenAI semantic conventions — metrics(상태 Development, 2026-10-08 확인): `gen_ai.server.time_to_first_token`, `gen_ai.server.time_per_output_token`, `gen_ai.server.request.duration`, 버킷 경계 <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md>
  - 같은 저장소 client-inference(2026-10-08 확인): `gen_ai.client.inference.time_to_first_chunk`, `gen_ai.client.inference.time_per_output_chunk`, 속성 `gen_ai.response.time_to_first_chunk` <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md>
  - Zhong 외, "DistServe", OSDI 2024 — 프리필 = TTFT, 디코드 = TPOT, §1 goodput 정의 <https://arxiv.org/abs/2401.09670>
  - Anthropic "Streaming messages"(2026-10-08 확인) — 이벤트 흐름, `message_delta`의 usage는 누적값 <https://platform.claude.com/docs/en/build-with-claude/streaming>
- 실험 목록 (코드: scratchpad `ai/09/Mock.java`·`ai/09/Client10.java`)
  - 모형 SSE 서버 4시나리오(steady·stall·bundle4·one-token) × 5회, 전체 2회 실행 — `eclipse-temurin:21-jdk`(OpenJDK 21.0.12), `--network none --cpus=2`, 한 컨테이너 안 127.0.0.1, 2026-10-08. 명령: `java Mock.java 18080 & java Client10.java 18080`
  - 측정: 클라이언트 TTFT·서버 TTFT·E2E·TPOT(vLLM 식)·이벤트 간격 평균·최대, 전체 평균 TPOT(0 포함/제외), ITL p50·p99·max
