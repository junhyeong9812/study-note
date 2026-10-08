# 커리큘럼 §22 초안 — AI 엔지니어링 (task 01, 2026-10-08)

> 이 파일은 초안이다. 메인이 검토한 뒤 `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`에 옮긴다. 아래 `## 22.` 줄부터 `---` 앞까지가 옮길 본문이다.
> 근거: `docs/plans/2026-10-04/aie-analysis/report.md` §5(b) 단원안 26행·§5(c)·§4.1. 1차 출처 URL과 확인 내용은 같은 폴더 `sources.md`. 📚 칸에서 `[?]` 없는 항목은 2026-10-08에 원문을 직접 열어 확인한 것이다.
> 생성기 호환: 머리 정규식 `^## (\d+[a-z]?)\. (.+?) \(\`([a-z-]+)/\`\)(.*)$`에 맞고, 머리말 인용문은 머리 다음 11줄 안에 있으며, 표 행은 `| NN-slug |`로 시작하고 9칸(앞뒤 빈 칸 포함)이다. 칸 안에 `|` 문자는 쓰지 않았다.

---

## 22. AI 엔지니어링 (`ai-engineering/`) — 신설 (2026-10-08)

> **범위**: 백엔드 개발자가 LLM을 **느리고 비싸고 비결정적인 외부 의존성**으로 호출·서빙·검색·평가·보호하는 데 필요한 것. 원리(학습·어텐션·디코딩)는 이 목적에 필요한 동작 수준까지만 다룬다. **다루지 않는 것**: 비전·음성·강화학습·이미지 생성·정렬(alignment) 연구, 모델 사전학습, 특정 SDK·프레임워크 사용법. 다 읽으면 "잘린 응답·같은 입력 다른 답·첫 토큰 지연·429 폭주·검색 품질 붕괴·평가 점수 흔들림·간접 인젝션"을 증상으로 보고 원인 leaf를 짚을 수 있어야 한다.
> **단일 출처**(여기서 반복하지 않고 링크만): 엔트로피 = math/14 · 코사인·내적 = math/13 · 경사 하강 = data-analysis/22 · BM25·분석기 = database/46 · 백분위·히스토그램 = data-analysis/05 · 큐잉·리틀 법칙 = math/10 · 신뢰구간·검정 = data-analysis/08·09 · 타임아웃·재시도·서킷·멱등 = reliability/05·06·10·13 · 토큰 버킷 = reliability/11.
> **빠르게 바뀌는 사실**(API 동작·한도·가격·명세 버전)은 노트마다 확인 날짜를 적는다. 이 절의 📚 확인일은 2026-10-08이다. AIEFS(rohitg00/ai-engineering-from-scratch)는 근거로 쓰지 않고 "실습 참고" 링크로만 쓴다(report §5c 링크 금지 목록 준수).
> 뼈대: Jurafsky–Martin 『Speech and Language Processing』 3판 초안(2026-08-19판 — 2장 Words and Tokens·3장 N-gram LM·5장 Embeddings·6장 Neural Networks·7장 Transformers and Pretraining·8장 Post-training·11장 Information Retrieval and RAG), Goodfellow·Bengio·Courville 『Deep Learning』(2016 — 3.13·5장·6.2·6.5·8장), Vaswani 외 2017, Kwon 외 SOSP 2023(vLLM), Lewis 외 NeurIPS 2020(RAG), Zheng 외 NeurIPS 2023(LLM-as-a-judge), MCP 명세 2026-07-28, OWASP Top 10 for LLM Applications 2025, OpenTelemetry GenAI semantic conventions.

**권장 학습 순서**: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → (09 심화) → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23 → (24 심화) → 25 → 26

- **백엔드 우선 경로**(원리를 뒤로 미루고 호출하는 쪽부터): 04 → 07 → 11 → 14 → 10 → 15 → 16 → 19 → 20 → 22 → 25. 원리 leaf(01~03·06·08)는 이 경로에서 막힐 때 당겨 읽는다. 이 경로의 선행은 모두 경로 안이나 다른 영역에 닫혀 있다(04·07의 선행 06은 "동작 수준"만 필요 — 막히면 06).

### 22.1 학습의 최소 원리

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 01-ml-in-one-page | 학습 = 손실 최소화. 학습·검증·테스트 분리, 과적합·과소적합, 데이터 누설. 백엔드 독자가 "모델 품질 숫자"를 읽기 위한 최소 | math/07-probability-and-bayes, data-analysis/22-multiple-and-logistic-regression | 평가 데이터가 학습·튜닝에 섞임(누설) → 오프라인 점수는 높은데 운영에서 급락. 검증셋으로 설정을 고른 뒤 같은 셋 점수를 최종 성능으로 보고 → 낙관 편향 | 무작위·층화 분할(data-analysis/02), 반복 최적화 루프 | Goodfellow 외 『Deep Learning』 5.2·5.3 · SLP3 4장 | 필수 | 신규 (연결: `data-analysis/02-sampling-and-bias`) |
| 02-gradient-descent-and-backprop | 연쇄 법칙과 역전파(역방향 자동 미분), 학습률과 발산. 경사 하강 자체는 data-analysis/22 단일 출처 | 01, math/13-linear-algebra-essentials | 학습률 과대 → 손실이 NaN·inf로 발산. 기울기 소실·폭주 → 손실이 멈추거나 튐(파인튜닝 작업 로그에서 보이는 모양) | 계산 그래프(DAG)를 위상 정렬 역순으로 순회(algorithm/18-dfs), 미분값 누적 | Goodfellow 외 6.5 · 8.3 · SLP3 6장 | 권장 | 신규 |
| 03-cross-entropy-and-perplexity | 교차 엔트로피 = 음의 로그우도(NLL), perplexity = exp(토큰당 평균 NLL). 토큰 단위가 다르면 비교할 수 없다. 엔트로피 정의는 math/14 단일 출처 | 01, math/14-information-theory-basics | 토크나이저(어휘)가 다른 두 모델의 perplexity를 나란히 비교 → 단위가 달라 결론 무의미. 확률 0에 log → 손실 inf(클리핑·log-softmax 누락) | log-sum-exp(math/15-numerical-stability) | Goodfellow 외 3.13 · 6.2.1.1 · SLP3 3장 | 권장 | 신규 |

### 22.2 모델이 텍스트를 다루는 방식

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 04-tokenization-and-token-cost | BPE·바이트 수준 BPE. 같은 뜻이라도 언어(한국어 vs 영어)·토크나이저마다 토큰 수가 다르다. 토큰 = 과금 단위·문맥 한도 단위·생성 시간 단위 | architecture/04-character-encoding-unicode | 글자 수로 비용·한도를 추정 → 한국어 입력에서 예산 초과·문맥 한도 초과(제공자에 따라 요청 거부 또는 생성 중단). 출력 한도에 잘린 응답(중단 사유 max_tokens·incomplete)을 성공으로 저장. 모델 교체로 토크나이저가 바뀌어 같은 프롬프트의 토큰 수·비용이 달라짐 | BPE 학습 = 인접 쌍 빈도표(data-structure/07-hashmap) + 최빈 쌍 반복 병합(data-structure/10-heap), 병합 규칙 순서 적용 | Sennrich 외 ACL 2016 · Kudo–Richardson EMNLP 2018 (SentencePiece) · Radford 외 2019 (GPT-2, 바이트 수준 BPE) [?] · SLP3 2장 · tiktoken README · Anthropic "Context windows" 문서 | 필수 | 신규 (연결: `database/46-full-text-search-and-analyzers` — 검색 토크나이저와 대비) |
| 05-embeddings-and-similarity | 임베딩 = 텍스트 → 고정 길이 벡터. 코사인·내적·L2의 관계(정규화하면 순위가 같다). 임베딩 모델 교체 = 벡터 공간 교체. 코사인 정의는 math/13 단일 출처 | 04, math/13-linear-algebra-essentials | 임베딩 모델(또는 차원)을 바꾼 뒤 옛 벡터와 새 벡터를 한 인덱스에 섞음 → 오류 없이 검색 품질만 붕괴. 정규화 안 된 벡터에 내적 연산자 → 노름 큰 벡터가 상위를 독점. 차원을 잘라 쓰는 모델에서 자른 뒤 재정규화 누락 → 코사인 순위 왜곡 | 내적·노름(math/13), 차원 절단(Matryoshka), 전수 최근접 = 상위 k 힙 | Reimers–Gurevych EMNLP 2019 (Sentence-BERT) · Kusupati 외 2022 (Matryoshka Representation Learning) · SLP3 5장 · OpenAI "Embeddings" 가이드 | 필수 | 신규 |
| 06-transformer-and-attention | 셀프 어텐션 softmax(QKᵀ/√d)V, 멀티헤드, 인과 마스크, 위치 정보 — 동작 수준. 문맥 길이에 대해 어텐션 연산·메모리가 제곱으로 늘어난다 | 05 | 긴 문맥의 중간에 둔 근거를 잘 못 씀("lost in the middle") → RAG로 관련 청크를 넣었는데 답에 반영 안 됨. 문맥 길이를 크게 늘림 → 프리필 시간·메모리 급증 | 행렬곱(math/13), softmax(log-sum-exp), 인과 마스크 = 하삼각 행렬, 타일링(FlashAttention) | Vaswani 외 2017 "Attention Is All You Need" · Liu 외 TACL 2023 (Lost in the Middle) · Dao 외 2022 (FlashAttention) · SLP3 7장 | 권장 | 신규 (연결: `architecture/21-simd-and-gpu`) |
| 07-decoding-and-nondeterminism | 로짓 → softmax → temperature·top-k·top-p(nucleus) 샘플링, greedy. 같은 입력 다른 출력의 두 원인: 샘플링, 그리고 서버 배치 구성에 따라 달라지는 수치 연산 | 06, math/12-randomness-and-prng | temperature 0이면 결정적이라 믿고 출력 스냅샷 테스트 → 간헐 실패(플래키 — 공개 실험: 같은 프롬프트 1000회 중 서로 다른 완성 80개). 출력 문자열을 캐시 키·중복 판정에 사용 → 재실행마다 불일치. temperature·top-p를 함께 크게 → 확률 꼬리의 무관한 토큰 출력 | 정렬 + 누적합 절단(nucleus), 역CDF 가중 무작위 선택, 시드 PRNG | Holtzman 외 ICLR 2020 (Nucleus Sampling) · He·Thinking Machines Lab 2025-09-10 "Defeating Nondeterminism in LLM Inference" · SLP3 7장 | 필수 | 신규 (연결: `testing/09-flaky-tests`) |
| 08-kv-cache-and-inference-memory | 프리필(프롬프트 전체를 병렬 처리) vs 디코드(토큰 하나씩). KV 캐시 크기 = 2 × 층 × KV 헤드 × 헤드 차원 × 원소 바이트 × 토큰 수. MQA·GQA로 KV 헤드를 줄인다 | 06 | 동시 요청 수 × 문맥 길이를 곱하지 않고 GPU 메모리 산정 → 긴 문맥 요청이 몰리면 OOM·대기열 적체. 계산에서 헤드 수를 빠뜨림 → 32배 과소 추정(LLaMA 7B급 MHA, fp16: 토큰당 512KiB, 32K 토큰 16GiB) | 캐시(이전 계산 재사용), 크기 계산 | Shazeer 2019 (MQA) · Ainslie 외 EMNLP 2023 (GQA) · Touvron 외 2023 (LLaMA 7B: 차원 4096·헤드 32·층 32) · Jiang 외 2023 (Mistral 7B: 층 32·KV 헤드 8·헤드 차원 128) | 권장 | 신규 (연결: `architecture/11-memory-hierarchy-and-locality`) |

### 22.3 서빙과 호출

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 09-inference-serving-and-batching | 요청 단위 배칭 vs 반복(iteration) 단위 연속 배칭, 페이지드 KV(고정 크기 블록 할당), 청크 프리필, 프리필·디코드 분리 배치 | 08, math/10-queueing-and-littles-law, os/10-paging-and-tlb | 요청 단위 정적 배칭 → 짧은 요청이 같은 배치의 긴 요청이 끝날 때까지 대기(꼬리 지연). KV를 연속 공간으로 할당 → 단편화로 배치 크기 제한·처리량 저하. 긴 프롬프트의 프리필이 진행 중 디코드를 막음 → 스트림이 멈칫(토큰 간 지연 급등) | 블록 테이블 = 페이지 테이블(os/10), 반복 단위 스케줄러 큐, KV 블록 공유(참조 카운트) [?] | Yu 외 OSDI 2022 (Orca) · Kwon 외 SOSP 2023 (vLLM PagedAttention) · Agrawal 외 2024 (Sarathi-Serve, 게재처 [?]) · Zhong 외 OSDI 2024 (DistServe) | 심화 | 신규 (연결: `reliability/40-batching-and-round-trips`) |
| 10-inference-latency-metrics | TTFT(첫 토큰까지)·TPOT(첫 토큰 이후 토큰당)·ITL(연속 스트림 출력 사이)·종단 지연·goodput(지연 목표를 지킨 처리량). 도구·규약마다 정의가 다르다 | 08, data-analysis/05-percentiles-and-latency-distributions, reliability/02-slo-sli-error-budget | 평균 TPOT만 대시보드 → 일부 스트림의 멈칫(ITL 꼬리)을 놓침. 서버 측 TTFT(대기열 이후)와 클라이언트 측 TTFT(네트워크·대기열 포함), ITL과 TPOT을 섞어 비교 → 맞지 않는 회귀 경보. 토큰 1개 이하 응답의 TPOT을 0으로 기록하는 도구 → 평균이 끌려 내려감 | 히스토그램·분위 스케치(data-analysis/05) | vLLM 문서 "Metrics" · OpenTelemetry GenAI semantic conventions — metrics(상태 Development) · Zhong 외 OSDI 2024 (DistServe) | 필수 | 신규 (연결: `reliability/34-tail-latency-and-stragglers`) |
| 11-llm-api-client-contract | LLM 호출 클라이언트 계약: SSE 스트리밍 이벤트, 스트림 중간 오류, 타임아웃 층위(첫 토큰·토큰 사이·전체), 429·529/503과 Retry-After, 중단 사유 확인, 토큰·비용 상한 | 04, 07, network/38-websocket-sse-long-lived, reliability/06-retry-backoff-jitter | HTTP 200 뒤 스트림 안에 온 error 이벤트(예: overloaded)를 무시 → 반쪽 응답을 정상 처리. 중단 사유(max_tokens·incomplete) 미확인 → 잘린 문장·JSON을 성공으로 저장. 전체 타임아웃 하나로 긴 생성을 끊고 처음부터 재시도 → 이미 생성된 출력 토큰까지 다시 과금. 실패 요청도 분당 한도에 포함 → 즉시 재시도 폭주로 429 지속. 지출 한도 도달 429는 Retry-After 없이 계속 실패 → 재시도로는 안 풀림 | 토큰 버킷(제공자 한도 — reliability/11-rate-limiter), 지수 백오프 + 지터, SSE 줄 단위 파서(상태 기계) | WHATWG HTML Living Standard 9.2 Server-sent events · RFC 6585 4절 (429) · RFC 9110 10.2.3 (Retry-After) · Anthropic "Streaming messages"·"Errors"·"Rate limits" 문서 · OpenAI "Rate limits"·"Error codes" 가이드 · Gemini API "Troubleshooting" | 필수 | 신규 (연결: `reliability/05-timeouts-and-deadline-propagation`, `reliability/07-timeout-taxonomy-by-layer`, `api-design/14-rate-limit-and-quota-contracts`) |
| 12-prompt-and-semantic-caching | 제공자 프롬프트(프리픽스) 캐시 — 정확히 같은 접두만 적중, TTL, 쓰기 비용 — vs 애플리케이션 의미 캐시 — 임베딩 유사도 임계값으로 적중, 오적중 위험 | 05, 11, database/31-cache-key-versioning-and-serialization | 프롬프트 앞부분에 시각·요청 ID를 넣음 → 프리픽스 캐시 적중 0, 비용·지연 그대로. 의미 캐시 임계값이 느슨함 → 뜻이 반대인 비슷한 질문에 같은 답(오적중). 사용자·테넌트·권한을 캐시 키에 안 넣음 → 다른 사용자의 답 노출. 모델·프롬프트 버전을 키에 안 넣음 → 배포 후에도 옛 답 | 접두 해시 키, 최근접 탐색 + 임계값, TTL·LRU(data-structure/14-lru-cache) | Anthropic "Prompt caching" 문서 · OpenAI "Prompt caching" 가이드 · Regmi–Pun 2024 "GPT Semantic Cache" (arXiv 2411.05276) | 권장 | 신규 (연결: `database/30-caching-with-databases`, `database/49-multi-level-caching`, `reliability/29-cache-stampede`) |
| 13-model-routing-and-fallback | LLM 게이트웨이, 난이도·비용 라우팅과 캐스케이드, 제공자·모델 폴백, 서킷 브레이커, 폴백 모델의 형식·품질 차이 | 11, reliability/10-circuit-breaker | 폴백 모델의 토크나이저·문맥 한도·구조화 출력 지원이 달라 장애 때만 파싱 오류 급증. SDK 자동 재시도 × 앱 재시도 × 게이트웨이 재시도 중첩 → 요청 증폭. 어느 모델로 라우팅됐는지 기록 안 함 → 품질 회귀 원인 추적 불가 | 가중 무작위 라우팅, 캐스케이드(조건부 순차 호출), 서킷 상태 기계 | Chen 외 2023 (FrugalGPT) · Ong 외 2024 (RouteLLM) · OpenAI "Rate limits" 가이드(SDK 자동 재시도와 앱 재시도 한도) | 권장 | 신규 (연결: `api-design/19-api-gateway-and-bff`, `reliability/28-bulkhead`) |
| 14-structured-output-and-tool-calling | JSON 스키마로 출력 형식 강제(제약 디코딩) vs 프롬프트로 부탁하기, 검증 실패·거부·잘림 처리, 도구 호출 계약(이름·인자 스키마·결과) | 07, 11, api-design/08-schema-and-serialization | 스키마 검증 없이 파싱만 → 필드 누락·타입 불일치가 하류로 전파. 출력 한도로 잘린 구조화 출력을 부분 파싱. 거부(refusal) 응답을 스키마 오류로 오인해 재시도 반복. 새 스키마 첫 요청은 문법 컴파일로 지연 → 첫 호출만 타임아웃. 모델이 만든 도구 인자를 검증 없이 실행 → 엉뚱한 ID의 레코드 수정 | JSON 스키마 검증(트리 순회), 제약 디코딩 = 문법 상태 기계로 허용 토큰 마스킹 | JSON Schema 2020-12 (Core·Validation) · OpenAI "Structured Outputs" 가이드 · Anthropic "Structured outputs" 문서 · Schick 외 2023 (Toolformer) | 필수 | 신규 (연결: `software-design/23-design-by-contract`) |

### 22.4 검색 증강 생성(RAG)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 15-rag-pipeline | 수집 → 청킹 → 임베딩 → 검색 → 프롬프트 조립 → 출처 표기. 파라미터 지식(모델 가중치) vs 비파라미터 지식(검색 인덱스) | 05, 14 | 청크 경계에서 표·문단이 잘림 → 근거가 반쪽만 검색됨. 검색 결과가 없거나 점수가 낮아도 그대로 생성 → 근거 없는 답. 문서 권한을 검색 단계에서 거르지 않음 → 권한 없는 문서 내용이 답에 섞임. 출처를 생성 텍스트에서 파싱 → 존재하지 않는 출처 | TF-IDF·코사인 전수 검색, 슬라이딩 윈도 분할(algorithm/15-sliding-window), 상위 k 힙 | Lewis 외 NeurIPS 2020 (RAG) · Karpukhin 외 EMNLP 2020 (DPR) · Anthropic "Contextual Retrieval" (2024-09-19) · SLP3 11장 | 필수 | 신규 (연결: `database/46-full-text-search-and-analyzers`) |
| 16-vector-index-ann | 전수(정확) 검색 vs 근사 최근접(ANN): HNSW(계층 근접 그래프)·IVFFlat(군집 목록). recall·지연·메모리·구축 시간의 절충, pgvector 파라미터(m·ef_construction·ef_search, lists·probes), 필터와의 상호작용 | 15, database/08-btree-indexes | ANN 인덱스를 만든 뒤 같은 쿼리의 결과가 달라짐(정확 → 근사). WHERE 필터가 인덱스 탐색 후에 적용 → 선택도 10% 필터 + 기본 ef_search 40이면 평균 4행만 반환(LIMIT 10인데 4건, 반복 스캔으로 완화). 데이터 적재 전에 IVFFlat 생성 → recall 저하. 여러 테넌트가 인덱스 하나를 공유 → 한 테넌트의 벡터가 다른 테넌트의 recall·속도에 영향 | HNSW = 계층 그래프 탐욕 탐색(층 배정은 지수 감소 확률 — data-structure/22-skip-list와 닮음), 후보 목록 = 우선순위 큐(data-structure/10-heap), IVF = k-평균 군집 + 목록 | Malkov–Yashunin 2016 (HNSW, arXiv 1603.09320 — 학술지판 TPAMI 2020 [?]) · pgvector README v0.8.7 · Douze 외 2024 "The Faiss library" | 필수 | 신규 |
| 17-hybrid-search-and-reranking | 어휘 검색(BM25)과 밀집 검색(벡터)의 결합. 점수 척도가 달라 순위로 합성(RRF), 교차 인코더 재순위. BM25 식은 database/46 단일 출처 | 15, 16, database/46-full-text-search-and-analyzers | BM25 점수와 코사인 유사도를 그대로 더함 → 척도 차이로 한쪽이 순위를 독점. 밀집 검색만 사용 → 오류 코드·제품 번호 같은 정확 일치 질의 누락. 재순위 후보 수가 너무 작음 → 재순위가 살릴 문서가 후보에 없음 | RRF = 순위 역수 합 1/(k + rank)(원 논문 k = 60), 다중 목록 병합, 상위 k 힙 | Cormack–Clarke–Büttcher SIGIR 2009 (RRF) · Robertson–Zaragoza 2009 "The Probabilistic Relevance Framework: BM25 and Beyond" · Nogueira–Cho 2019 (BERT 재순위) · Anthropic "Contextual Retrieval" (2024-09-19) · pgvector README "Hybrid Search" | 권장 | 신규 (연결: `data-structure/32-inverted-index`) |
| 18-index-freshness-and-reembedding | 원천이 바뀌면 재청킹·재임베딩·재색인, 삭제 전파, 임베딩 모델 교체 시 이중 색인 후 전환, 신선도 지연 감지 | 15, data-engineering/01-system-of-record-and-derived-data | 원천에서 삭제된 문서(삭제 요청된 개인정보 포함)가 벡터 인덱스에 남아 답변에 등장. 임베딩 모델 교체를 문서별로 점진 반영 → 옛·새 벡터 혼재로 검색 품질 붕괴(오류는 없음). 재임베딩 배치가 중간에 실패한 뒤 재실행 → 같은 청크 중복 | 내용 해시 키 멱등 upsert, 인덱스 버전 별칭 전환(blue-green), 변경 데이터 캡처 | DDIA 1판 11·12장 (파생 데이터 재구축) [?] · OpenAI "Embeddings" 가이드(모델별 차원) · Lewis 외 2020 (비파라미터 메모리 교체로 지식 갱신) | 권장 | 신규 (연결: `database/48-search-index-sync-and-reindexing`, `data-engineering/08-idempotent-pipelines-and-backfill`, `data-engineering/12-data-retention-and-erasure`) |

### 22.5 평가·에이전트·보안·운영

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 19-llm-evaluation | 평가셋 설계(골든셋·회귀셋), 정답 일치·루브릭·LLM 판정자, 판정자 편향(위치·장황함·자기 선호), 신뢰구간과 짝지은 비교, 배포 전 회귀 게이트 | 07, 15, data-analysis/08-confidence-intervals | 평가 100문항 정확도 1~2%p 차이로 모델 교체 → 신뢰구간 안의 잡음. 판정자에게 A·B 순서를 고정해 보여 줌 → 위치 편향이 승률을 만든다. 평가셋을 프롬프트 개발에 재사용 → 평가셋 과적합으로 운영 품질과 괴리. 비결정 출력을 1회만 채점 → 재실행마다 점수 흔들림 | 부트스트랩 재표집, 짝지은 차이(대응 표본), 순서 교환 2회 판정 | Zheng 외 NeurIPS 2023 Datasets and Benchmarks (LLM-as-a-judge) · Miller 2024 "Adding Error Bars to Evals" | 필수 | 신규 (연결: `data-analysis/09-hypothesis-testing`, `data-analysis/11-multiple-comparisons`, `testing/19-testing-in-production`) |
| 20-agent-loop-and-tool-safety | 에이전트 = 모델이 다음 도구 호출을 고르는 루프. 종료 조건·턴·토큰·시간 예산, 관측 정리, 부작용 도구의 멱등 키·사람 확인·최소 권한, 고정 경로 워크플로와의 선택 | 14, reliability/13-idempotency | 종료 조건·턴 예산 없음 → 같은 도구 반복 호출로 비용 폭주. 재시도 때 결제·메일 도구가 두 번 실행(멱등 키 없음). 도구 오류를 그대로 모델에 넘김 → 인자만 바꿔 끝없이 재시도. 사용자 요청이 타임아웃된 뒤에도 백그라운드 루프가 계속 돌며 부작용 발생 | 상태 기계·루프 불변식, 멱등 키 저장(해시맵), 예산 카운터 | Yao 외 ICLR 2023 (ReAct) · Anthropic "Building effective agents" (2024-12-19) · MCP 명세 2026-07-28 "Tools"(사람 확인 SHOULD) | 필수 | 신규 (연결: `reliability/09-cancellation-propagation`, `reliability/32-batch-and-job-time-bounds`, `api-design/05-idempotency-keys`) |
| 21-mcp-protocol | MCP = JSON-RPC 2.0 위의 도구·리소스·프롬프트 제공 규약. 2026-07-28판 무상태화(초기화 핸드셰이크·세션 제거, 요청마다 `_meta`로 버전·능력 전달), server/discover, 캐시 가능 결과(ttlMs·cacheScope), 오류 코드 할당 정책 | 14, api-design/01-api-as-contract | 버전 불일치 오류(UnsupportedProtocolVersion, -32022)를 일시 오류로 보고 재시도 반복. 2025-11-25 이전 판의 세션(Mcp-Session-Id)에 기대는 구현과 혼용 → 요청 사이 상태 유실. 끊긴 스트림의 재개(Last-Event-ID)를 기대 → 2026-07-28판에서 제거됨, 새 요청 ID로 다시 보내야 함. 신뢰하지 않은 서버의 도구 annotations(예: 읽기 전용 표시)를 믿고 확인 생략 | JSON-RPC 요청 ID ↔ 응답 대응(해시맵), 능력 협상, TTL 캐시 | MCP 명세 2026-07-28 (Key Changes·Versioning·Tools·server/discover·Caching) · JSON-RPC 2.0 명세 | 권장 | 신규 (연결: `api-design/07-versioning-and-compatibility`, `api-design/16-grpc-streaming-modes`) |
| 22-prompt-injection-and-llm-security | 신뢰 경계: 지시와 데이터가 같은 채널(프롬프트)에 섞인다. 직접·간접 인젝션, 모델 출력도 신뢰하지 않기, 과도한 에이전시, 시스템 프롬프트 유출, 무제한 소비, 개인정보. 방어 원리 중심 | 15, 20, security/18-injection | 검색된 문서·메일 안의 지시를 모델이 따름(간접 인젝션) → 도구로 데이터 외부 전송. 모델 출력을 HTML·SQL·셸에 그대로 넣음 → XSS·인젝션(출력 처리 부실). 시스템 프롬프트에 비밀값을 넣음 → 유출. 입력 길이·호출 수 상한 없음 → 비용 폭탄(무제한 소비) | 권한 최소화(도구 허용 목록), 출처 태깅(오염 추적), 레이트 리미터(reliability/11) | OWASP Top 10 for LLM Applications 2025 (LLM01·02·05·06·07·10) · Greshake 외 2023 (간접 인젝션) · MCP 2026-07-28 "Security Best Practices" | 필수 | 신규 (연결: `security/01-security-principles`, `security/19-xss-and-csp`, `security/25-supply-chain-security`, `security/27-pii-classification-masking-retention`) |
| 23-llm-observability-and-cost | OTel GenAI 스팬·지표(gen_ai.* — 모델·토큰 사용량·TTFT), 요청 단위 비용 귀속(입력·캐시 쓰기·캐시 읽기·출력 토큰), 프롬프트·응답 기록과 개인정보, 품질 신호 | 10, 19, reliability/17-distributed-tracing | 캐시 읽기 토큰이 입력 토큰에 포함되는지 규칙을 혼동 → 비용 대시보드 이중 계산·누락. 프롬프트 원문을 로그에 저장 → 개인정보·비밀 유출. 기능·테넌트 태그 없이 토큰만 집계 → 비용 급증 원인 추적 불가. 아직 Development 상태인 규약의 속성명이 바뀜 → 대시보드가 조용히 빈다 | 카운터·히스토그램, 태그별 집계(해시맵), 샘플링 | OpenTelemetry GenAI semantic conventions — spans·metrics(상태 Development, semantic-conventions-genai 저장소로 이동) · Anthropic "Rate limits"(캐시 인지 ITPM) · OpenAI "Prompt caching" 가이드(cached_tokens) | 권장 | 신규 (연결: `reliability/15-logging`, `reliability/16-metrics-and-golden-signals`) |
| 24-fine-tuning-vs-rag-decision | 지식은 검색(RAG), 형식·말투·작업 방식은 프롬프트나 파인튜닝. LoRA(저랭크 어댑터)·QLoRA 개념, 선택 기준(갱신 빈도·출처 표기·비용·평가 데이터) | 15, 19 | 자주 바뀌는 사실(가격·정책)을 파인튜닝으로 주입 → 바뀔 때마다 재학습, 그 사이 옛 사실 출력. 평가셋 없이 파인튜닝 → 개선인지 회귀인지 판정 불가. 베이스 모델을 바꾸면 그 위에 학습한 어댑터를 그대로 못 씀 | 저랭크 분해(행렬곱 BA — math/13) | Hu 외 2021 (LoRA) · Dettmers 외 2023 (QLoRA) · Lewis 외 NeurIPS 2020 (RAG — 출처 제공·지식 갱신) · SLP3 8장 | 심화 | 신규 (연결: `engineering-practice/13-build-vs-buy-and-adoption`) |

### 22.6 영역 마감

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 25-ai-symptom-index | 역색인: 응답이 잘림·JSON 파싱 실패, 같은 입력 다른 답, 첫 토큰이 늦음·스트림 멈칫, 429가 안 끝남, 비용 급증, 검색이 엉뚱함·결과 수 부족, 모델 교체 뒤 품질 붕괴, 평가 점수 흔들림, 에이전트 반복, 모델이 문서 속 지시를 따름 | 전체 | — | — | 이 영역 leaf | 필수 | 신규 |
| 26-ai-incidents | 실사건: Mata v. Avianca(2023 — 생성된 가짜 판례 인용 제재) · Anthropic 응답 품질 저하 3중 버그(2025-08~09 — 문맥 길이 라우팅 오류·TPU 출력 손상·근사 top-k 컴파일러 버그) · Greshake 외 간접 인젝션 시연(2023 — 실제 LLM 통합 앱) · Moffatt v. Air Canada(2024 — 챗봇 오안내 배상) [?] | 25 | — | — | S.D.N.Y. 22-cv-1461 Opinion and Order on Sanctions (2023-06-22) · Anthropic "A postmortem of three recent issues" (2025-09-17) · Greshake 외 2023 · 2024 BCCRT 149 [?] | 권장 | 신규 |

---

## 메인 검토용 메모 (커리큘럼에는 옮기지 않음)

### 집계 (§20 반영용)

| # | 영역 | leaf | 증감 | 신규 | 기존 | 필수 | 권장 | 심화 |
|---|---|---|---|---|---|---|---|---|
| 22 | AI 엔지니어링 | 26 | +26 | 26 | 0 | 13 | 11 | 2 |

- 합계는 644 → 670, 신규 464 → 490, 필수 351 → 364, 권장 249 → 260, 심화 44 → 46(메인이 스크립트로 재집계할 것).
- 이 초안 행의 `[?]`: 7개·5행(04 Radford 2019, 09 KV 블록 공유·Sarathi 게재처, 16 TPAMI 2020, 18 DDIA, 26 Air Canada ×2).
- §0.6 끝 "AI·GIT·HCI·SEP는 이 트리에서 뺐다" 문장과 §0.3 층위 표(Part 0~6)는 영역 추가에 맞춰 메인이 고쳐야 한다(예: Part 7 "AI를 의존성으로 쓰는 법" 또는 Part 6 뒤). §0.6 영역 표에 `22 · AI 엔지니어링 · ai-engineering/ · (없음)` 행.
- 절 위치: §19(이식 매핑)·§20(통계)·§21(출처) 뒤에 `## 22.`를 두면 생성기는 문서 끝까지를 §22 본문으로 읽는다(다음 `## `가 없으므로). §22 뒤에 다른 `## ` 절을 붙이지 말 것. 18a처럼 §18 뒤에 `## 18b.`로 끼우는 방법도 있지만 명세가 `## 22.`로 정했다.

### 단원안(report §5b)에서 바꾼 것 — 판단 필요

1. **04 선행**: 단원안 `03` → 초안 `architecture/04-character-encoding-unicode`. 토큰화는 교차 엔트로피가 아니라 UTF-8 바이트를 알아야 읽히고, 백엔드 우선 경로(04가 첫 편)가 원리 leaf에 막히지 않게 하려는 것.
2. **07 선행**: 단원안 `06` → `06, math/12-randomness-and-prng`(단원안이 연결로 적은 math/12를 선행으로 올림).
3. **09 선행**: `os/10-paging-and-tlb` 추가(페이지드 KV = 페이지 테이블 비유가 요지).
4. **10 선행**: 단원안 `09`(심화) → `08, data-analysis/05-…, reliability/02-…`. 필수 leaf가 심화 leaf를 선행으로 요구하면 백엔드 우선 경로(…14 → 10)가 막힌다. 09는 요지·⚠에서 링크로만.
5. **11·12·13·14·16·17·18·19·20·22·23 선행**: 단원안의 "기존 노트 연결" 중 꼭 먼저 읽어야 하는 것 1~2개를 선행으로 올리고 나머지는 `기존` 칸 `(연결: …)`에 두었다.
6. **06의 연결**: 단원안은 `architecture/12`(cache-organization)였으나 어텐션과 직접 관련이 약해 `architecture/21-simd-and-gpu`로 바꿨다. 08은 `architecture/11-memory-hierarchy-and-locality` 연결.
7. **data-structure·algorithm 참조 slug**: 이 두 영역은 커리큘럼 slug(예: `data-structure/10-heap`, `data-structure/24-inverted-index`, `algorithm/18-dfs`, `algorithm/15-sliding-window`)와 실제 폴더(`cs/data-structure/07-heap`, `32-inverted-index` 등)가 다르다. 기존 커리큘럼 관례(database/46의 선행 `data-structure/24-inverted-index`, reliability/11의 `algorithm/15-sliding-window`)를 따라 🔧 칸에는 **커리큘럼 slug**로 적었다. 선행 칸에는 이 두 영역을 넣지 않았고, `기존` 칸 연결(17)만 실제 폴더 `data-structure/32-inverted-index`로 적었다.
8. **소절 나누기**: 단원안에는 소절이 없다. 원리(01~03) / 텍스트 처리(04~08) / 서빙·호출(09~14) / RAG(15~18) / 평가·에이전트·보안·운영(19~24) / 마감 6개로 나눴다. 22.5가 6행이라 "평가"(19)와 "에이전트·보안·운영"(20~24)으로 더 쪼갤 수 있다.
9. **등급**: 단원안 그대로(필수 13·권장 11·심화 2). 검토 후보 — 06(권장)은 07·08·10의 선행이라 사실상 필수 경로에 있음(백엔드 우선 경로는 06을 건너뛰게 둠). 13(권장) vs 12(권장)는 운영 비용 관점에서 12를 필수로 올릴 여지.
10. **범위 경계**: 24(파인튜닝)는 "선택 기준" 중심으로 두고 학습 절차는 범위 밖. 22는 I5에 따라 공격 문자열 없이 방어 원리·로컬 모형까지. 26의 Air Canada는 1차 출처(재판소 결정문)를 열지 못해(403) `[?]` — 대체 사건 또는 결정문 확인 필요.

### 기존 노트 쪽 후속 (T3 정합 후보 — 링크만)

- `math/13-linear-algebra-essentials` 🔧 "임베딩 근사 최근접 탐색(ANN)" → `ai-engineering/16-vector-index-ann`.
- `math/14-information-theory-basics` → `ai-engineering/03-cross-entropy-and-perplexity`(교차 엔트로피 응용).
- `data-analysis/22-multiple-and-logistic-regression`(경사 하강) → `ai-engineering/02`.
- `database/46-full-text-search-and-analyzers` → `ai-engineering/17`(하이브리드)·`04`(LLM 토크나이저와 대비).
- `reliability/11-rate-limiter` → `ai-engineering/11`(제공자 한도가 토큰 버킷 — Anthropic 문서 명시).
- `network/38-websocket-sse-long-lived` → `ai-engineering/11`(LLM 스트리밍).
- `testing/09-flaky-tests` → `ai-engineering/07`(비결정 출력).
- `security/18-injection` → `ai-engineering/22`.
- `data-structure` 커리큘럼 `22-skip-list`·`10-heap` 🔧 "쓰이는 곳"에 HNSW.
