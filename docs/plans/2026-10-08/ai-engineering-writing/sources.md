# 1차 출처 목록 — ai-engineering 26편 (task 01, 확인 2026-10-08)

> 방법: 2026-10-08에 curl로 원문을 받아 제목·날짜·저자와 핵심 문장을 직접 확인했다(arXiv는 abs 페이지의 citation 메타·초록·Comments 칸, PDF는 pdftotext, 문서 사이트는 HTML → 텍스트). 받은 파일은 세션 scratchpad에만 있고 저장소에는 없다.
> "확인한 것"은 원문에 있는 문장·값만 적었다. 원문에서 보지 못한 세부(장·절·게재처 등)는 `[?]`. 열지 못한 것은 "미확인".
> 빠르게 바뀌는 문서(API·명세·가격)는 노트에 쓸 때 다시 열고 날짜를 적는다.

## A. 논문 (arXiv abs 페이지 확인)

| # | 출처 | URL | 확인한 것 | 쓰는 leaf |
|---|---|---|---|---|
| 1 | Vaswani 외, "Attention Is All You Need" (arXiv 2017-06-12) | https://arxiv.org/abs/1706.03762 | 제목·저자·날짜. 초록: 순환·합성곱 없이 어텐션만, WMT14 영-독 28.4 BLEU, 영-불 41.8 BLEU(GPU 8개 3.5일). 게재처(NeurIPS 2017)는 abs 페이지에 없음 [?] | 06 |
| 2 | Sennrich·Haddow·Birch, "Neural Machine Translation of Rare Words with Subword Units" (arXiv 2015-08-31, Comments "accepted at ACL 2016") | https://arxiv.org/abs/1508.07909 | 초록: 희귀·미등록 단어를 subword 단위 시퀀스로, "byte pair encoding compression algorithm" 기반 분할, WMT15 영-독 +1.1·영-러 +1.3 BLEU | 04 |
| 3 | Kudo·Richardson, "SentencePiece" (arXiv 2018-08-19, EMNLP 2018 demo) | https://arxiv.org/abs/1808.06226 | 제목·Comments(EMNLP2018 demo) | 04 |
| 4 | Holtzman 외, "The Curious Case of Neural Text Degeneration" (arXiv 2019-04-22, Comments "Published in ICLR 2020") | https://arxiv.org/abs/1904.09751 | 초록: 우도를 디코딩 목표로 쓰면 밋밋하고 반복적, 같은 모델이라도 디코딩 전략만으로 품질이 크게 달라짐, Nucleus Sampling = 분포의 동적 nucleus에서 샘플링해 신뢰도 낮은 꼬리를 절단 | 07 |
| 5 | Shazeer, "Fast Transformer Decoding: One Write-Head is All You Need" (arXiv 2019-11-06) | https://arxiv.org/abs/1911.02150 | 초록: 증분 추론이 큰 K·V 텐서를 반복 로드하는 메모리 대역폭 비용 때문에 느림, multi-query attention = 모든 헤드가 K·V 공유 | 08 |
| 6 | Ainslie 외, "GQA" (arXiv 2023-05-22, Comments "Accepted at EMNLP 2023") | https://arxiv.org/abs/2305.13245 | 초록: MQA는 단일 KV 헤드, GQA는 쿼리 헤드 수보다 적고 1보다 많은 KV 헤드, 원 사전학습 계산의 5%로 uptraining, 품질은 MHA에 가깝고 속도는 MQA 수준 | 08 |
| 7 | Touvron 외, "LLaMA" (arXiv 2302.13971) | https://arxiv.org/abs/2302.13971 (PDF) | PDF 표 2: 7B = dimension 4096·n heads 32·n layers 32 (→ 헤드 차원 128). KV 계산: 2×32×32×128×2B = 524,288B = 512KiB/토큰, 32,768토큰 = 16GiB | 08 |
| 8 | Touvron 외, "Llama 2" (arXiv 2023-07-18) | https://arxiv.org/abs/2307.09288 (PDF) | 본문: 34B·70B만 GQA 사용(7B는 MHA) | 08 |
| 9 | Jiang 외, "Mistral 7B" (arXiv 2023-10-10) | https://arxiv.org/abs/2310.06825 (PDF) | PDF 파라미터 표: dim 4096·n_layers 32·head_dim 128·n_heads 32·n_kv_heads 8·window 4096·context_len 8192. KV = 2×32×8×128×2B = 128KiB/토큰 | 08 |
| 10 | Dao 외, "FlashAttention" (arXiv 2022-05-27) | https://arxiv.org/abs/2205.14135 | 초록: self-attention 시간·메모리가 길이에 제곱, IO-aware 정확 어텐션, 타일링으로 HBM↔SRAM 읽기·쓰기 감소. **KV 캐시는 초록에 없음**(report §4.1 #12와 일치) | 06 |
| 11 | Yu 외, "Orca" (OSDI 2022) | https://www.usenix.org/conference/osdi22/presentation/yu | USENIX 페이지: 저자(Gyeong-In Yu 외, 서울대·FriendliAI), iteration-level scheduling·selective batching, GPT-3 175B에서 FasterTransformer 대비 같은 지연에서 처리량 36.9배 | 09 |
| 12 | Kwon 외, "Efficient Memory Management for LLM Serving with PagedAttention" (arXiv 2023-09-12, Comments "SOSP 2023") | https://arxiv.org/abs/2309.06180 | 초록: KV 캐시가 크고 동적으로 늘고 줄어 단편화·중복으로 낭비, OS 가상 메모리·페이징에서 착안, KV 메모리 낭비 거의 0, 요청 안팎 KV 공유, 같은 지연에서 처리량 2~4배(FasterTransformer·Orca 대비). 공유 구현(참조 카운트·copy-on-write)은 본문 §4.4에서 확인(09 집필, 2026-10-08) | 09 |
| 13 | Agrawal 외, "Sarathi-Serve" (arXiv 2024-03-04) | https://arxiv.org/abs/2403.02310 | 초록: 프리필은 지연 크고 계산 포화, 디코드는 지연 작고 활용도 낮음, chunked-prefills·stall-free 스케줄. 게재처(OSDI 2024) abs 페이지에 없음 [?] | 09 |
| 14 | Zhong 외, "DistServe" (arXiv 2024-01-18, Comments "OSDI 2024") | https://arxiv.org/abs/2401.09670 | 제목 "…for Goodput-optimized…". 초록: 프리필 = TTFT, 디코드 = TPOT, 두 단계 간섭, 프리필·디코드를 다른 GPU에 배치. goodput 정의 문장은 초록에 없음 → 본문 확인 필요 [?] | 09·10 |
| 15 | Malkov·Yashunin, "Efficient and robust ANN search using HNSW graphs" (arXiv 2016-03-30) | https://arxiv.org/abs/1603.09320 | 초록: 근접 그래프의 계층 구조, 원소의 최대 층은 지수 감소 확률로 무작위 선택, 상위 층부터 탐색해 로그 복잡도, 이웃 선택 휴리스틱, 스킵 리스트와 유사. 학술지판(IEEE TPAMI 2020)은 미확인 [?] | 16 |
| 16 | Douze 외, "The Faiss library" (arXiv 2024-01-16) | https://arxiv.org/abs/2401.08281 | 초록: 벡터 유사도 검색 도구 모음, 색인·클러스터·압축, 검색 절충 공간 | 16 |
| 17 | Lewis 외, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (arXiv 2020-05-22, Comments "Accepted at NeurIPS 2020") | https://arxiv.org/abs/2005.11401 | 초록: 파라미터 메모리(seq2seq) + 비파라미터 메모리(위키백과 밀집 벡터 인덱스), 출처 제공·세계 지식 갱신이 열린 문제, 개방형 QA 3종 SOTA | 15·18·24 |
| 18 | Karpukhin 외, "Dense Passage Retrieval" (arXiv 2020-04-10, EMNLP 2020) | https://arxiv.org/abs/2004.04906 | 제목·Comments | 15 |
| 19 | Reimers·Gurevych, "Sentence-BERT" (arXiv 2019-08-27, EMNLP 2019) | https://arxiv.org/abs/1908.10084 | 제목·Comments | 05 |
| 20 | Kusupati 외, "Matryoshka Representation Learning" (arXiv 2022-05-26) | https://arxiv.org/abs/2205.13147 | 제목·날짜(게재처 미확인 [?]) | 05 |
| 21 | Nogueira·Cho, "Passage Re-ranking with BERT" (arXiv 2019-01-13) | https://arxiv.org/abs/1901.04085 | 제목·날짜 | 17 |
| 22 | Thakur 외, "BEIR" (arXiv 2021-04-17, NeurIPS 2021 D&B) | https://arxiv.org/abs/2104.08663 | 제목·Comments (선택 — 검색 평가) | 17·19 |
| 23 | Liu 외, "Lost in the Middle" (arXiv 2023-07-06, TACL 2024 — 12권 157–173쪽, ACL Anthology 2024.tacl-1.9; 판정 A1에서 2023→2024 정정) | https://arxiv.org/abs/2307.03172 | 초록: 관련 정보가 입력 앞·끝일 때 성능이 높고 중간이면 크게 떨어짐(긴 문맥 모델 포함) | 06·15 |
| 24 | Hu 외, "LoRA" (arXiv 2021-06-17) | https://arxiv.org/abs/2106.09685 | 초록: 사전학습 가중치 동결 + 층마다 학습 가능한 랭크 분해 행렬 주입, GPT-3 175B 대비 학습 파라미터 1만 분의 1·GPU 메모리 1/3, 추가 추론 지연 없음 | 24 |
| 25 | Dettmers 외, "QLoRA" (arXiv 2023-05-23) | https://arxiv.org/abs/2305.14314 | 제목·날짜 | 24 |
| 26 | Zheng 외, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (arXiv 2023-06-09, NeurIPS 2023 D&B) | https://arxiv.org/abs/2306.05685 | 초록: 위치·장황함·자기 강화 편향, 제한된 추론 능력, GPT-4 판정자와 사람 선호 일치 80% 초과(사람끼리 일치 수준) | 19 |
| 27 | Miller, "Adding Error Bars to Evals" (arXiv 2024-11-01) | https://arxiv.org/abs/2411.00640 | 초록: 평가 = 실험, 질문을 보이지 않는 초모집단에서 뽑은 것으로 보고 두 모델 차이·평가 설계 공식 제시 | 19 |
| 28 | Wang 외, "Self-Consistency" (arXiv 2022-03-21, ICLR 2023) | https://arxiv.org/abs/2203.11171 | 제목·Comments (선택 — 비결정 출력 다수결) | 07·19 |
| 29 | Yao 외, "ReAct" (arXiv 2022-10-06, ICLR camera ready) | https://arxiv.org/abs/2210.03629 | 초록: 추론 흔적과 행동을 교차 생성, ALFWorld·WebShop에서 절대 성공률 +34%·+10%(report #6과 일치) | 20 |
| 30 | Schick 외, "Toolformer" (arXiv 2023-02-09) | https://arxiv.org/abs/2302.04761 | 초록: 어떤 API를 언제 어떤 인자로 부를지 자기 지도 학습 | 14 |
| 31 | Greshake 외, "Not what you've signed up for: … Indirect Prompt Injection" (arXiv 2023-02-23) | https://arxiv.org/abs/2302.12173 | 초록: LLM 통합 앱은 데이터와 지시의 경계를 흐림, 검색될 데이터에 프롬프트를 심는 간접 인젝션, 데이터 탈취·웜, Bing GPT-4 Chat 등 실제 시스템에 시연 | 22·26 |
| 32 | Chen·Zaharia·Zou, "FrugalGPT" (arXiv 2023-05-09) | https://arxiv.org/abs/2305.05176 | 초록: API 가격이 두 자릿수 배 차이, 프롬프트 적응·LLM 근사·LLM 캐스케이드, 최고 모델 성능을 최대 98% 비용 절감으로 맞춤 | 13 |
| 33 | Ong 외, "RouteLLM" (arXiv 2024-06-26) | https://arxiv.org/abs/2406.18665 | 초록: 강·약 모델 사이 라우터, 사람 선호 데이터로 학습, 일부 경우 비용 2배 이상 절감 | 13 |
| 34 | Regmi·Pun, "GPT Semantic Cache" (arXiv 2411.05276) | https://arxiv.org/abs/2411.05276 | 제목·저자 | 12 |
| 35 | Inan 외, "Llama Guard" (arXiv 2023-12-07) | https://arxiv.org/abs/2312.06674 | 초록: 입력·출력 안전 분류 모델(선택 — 22) | 22 |
| 36 | Leviathan 외, "Speculative Decoding" (arXiv 2022-11-30, ICML 2023) | https://arxiv.org/abs/2211.17192 | 초록: 출력 분포를 바꾸지 않고 2~3배 가속(선택 — 09 확장) | 09 |
| 37 | Cormack·Clarke·Büttcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (SIGIR '09, 2009-07-19~23) | https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf (→ cormack.uwaterloo.ca) | PDF: RRFscore(d) = Σ 1/(k + r(d)), "k = 60 was fixed during a pilot investigation", k = 60이 거의 최적 | 17 |
| 38 | Robertson·Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond", Foundations and Trends in IR 3(4) 333–389 (2009) | https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf | PDF 1쪽: 서지·DOI 10.1561/1500000019. BM25 식 자체는 database/46 노트(Lucene BM25Similarity)가 단일 출처 | 17 |

## B. 교재

| # | 출처 | URL | 확인한 것 | 쓰는 leaf |
|---|---|---|---|---|
| 39 | Goodfellow·Bengio·Courville, 『Deep Learning』 (MIT Press 2016) | https://www.deeplearningbook.org/ (장: contents/prob.html·ml.html·mlp.html·optimization.html) | 목차와 절 제목: 3.13 Information Theory · 5.2 Capacity, Overfitting and Underfitting · 5.3 Hyperparameters and Validation Sets · 5.5 Maximum Likelihood Estimation · 5.9 Stochastic Gradient Descent · 6.2.1.1 Learning Conditional Distributions with Maximum Likelihood · 6.5 Back-Propagation and Other Differentiation Algorithms · 8.3 Basic Algorithms | 01·02·03 |
| 40 | Jurafsky·Martin, 『Speech and Language Processing』 3판 초안 (2026-08-19 공개판) | https://web.stanford.edu/~jurafsky/slp3/ | 장 목록: 1 Introduction · 2 Words and Tokens · 3 N-gram Language Models · 4 Logistic Regression and Text Classification · 5 Embeddings · 6 Neural Networks · 7 Transformers and Pretraining(옛 7·8장 병합 — 디코딩·샘플링 포함) · 8 Post-training · 11 Information Retrieval and RAG · 12 Agents("not written yet"). 인용 형식: "Online manuscript released August 19, 2026". **장 번호가 판마다 바뀐다** — 노트에는 판 날짜를 함께 적는다 | 01·02·03·04·05·06·07·15·24 |

## C. 명세·표준

| # | 출처 | URL | 확인한 것 | 쓰는 leaf |
|---|---|---|---|---|
| 41 | MCP 명세 2026-07-28 — Key Changes | https://modelcontextprotocol.io/specification/2026-07-28/changelog | 직전 판 2025-11-25 대비: 프로토콜 세션·Mcp-Session-Id 제거, initialize 핸드셰이크 제거("Make MCP stateless") — 요청마다 `_meta`에 protocolVersion·clientCapabilities, server/discover 추가(MUST 구현), subscriptions/listen, ping·logging/setLevel 제거, tasks는 확장으로, MRTR(InputRequiredResult)·resultType 필수, SSE 재개(Last-Event-ID) 제거 → 끊긴 요청은 새 ID로 재발행 MUST, tools/list 등에 ttlMs·cacheScope(CacheableResult), resource not found -32002 → -32602, 오류 코드 구간(-32020~-32099 명세 예약)·UnsupportedProtocolVersion -32004 → -32022, Roots·Sampling·Logging 폐기 예정, inputSchema/outputSchema는 JSON Schema 2020-12 | 21 |
| 42 | MCP Versioning | https://modelcontextprotocol.io/specification/versioning (→ docs/2026-07-28/learn/versioning) | "The current protocol version is 2026-07-28." `/specification/latest`가 2026-07-28로 이동 | 21 |
| 43 | MCP server/discover · Caching | https://modelcontextprotocol.io/specification/2026-07-28/server/discover · …/server/utilities/caching | discover 응답 예시에 `ttlMs: 3600000`, Caching 페이지의 Cacheable Results 목록에 server/discover 포함 → **server/discover도 캐시 가능**(report §4.1 #9 "미확인" 해소) | 21 |
| 44 | MCP Tools | https://modelcontextprotocol.io/specification/2026-07-28/server/tools | "there SHOULD always be a human in the loop with the ability to deny tool invocations", 도구 annotations는 신뢰한 서버가 아니면 untrusted로 간주(MUST) | 20·21·22 |
| 45 | MCP Security Best Practices | https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices (→ docs/2026-07-28/tutorials/security/…) | 절 제목: Confused Deputy Problem · Token Passthrough · Server-Side Request Forgery 등 | 22 |
| 46 | JSON-RPC 2.0 명세 | https://www.jsonrpc.org/specification | id 없는 요청 = Notification(응답 없음, 오류도 모름), 서버는 Notification 외에는 Response MUST, 오류 코드 -32700 등 | 21 |
| 47 | JSON Schema 2020-12 | https://json-schema.org/specification | "The current version is 2020-12!" Core·Validation 두 문서 | 14 |
| 48 | WHATWG HTML Living Standard — 9.2 Server-sent events | https://html.spec.whatwg.org/multipage/server-sent-events.html | text/event-stream, 연결이 닫히면 클라이언트가 재연결(204로 중단 지시), 재연결 시간, 9.2.4 Last-Event-ID 헤더 | 11 |
| 49 | RFC 6585 4절 429 Too Many Requests | https://www.rfc-editor.org/rfc/rfc6585.txt | "sent too many requests in a given amount of time", Retry-After MAY | 11 |
| 50 | RFC 9110 10.2.3 Retry-After | https://www.rfc-editor.org/rfc/rfc9110.txt | 값은 HTTP-date 또는 초 단위 지연, 503·3xx와 함께 쓸 때의 뜻 | 11 |
| 51 | OWASP Top 10 for LLM Applications 2025 | https://genai.owasp.org/llm-top-10/ | 최신판 = 2025("LLM TOP 10 FOR 2025"). LLM01 Prompt Injection · 02 Sensitive Information Disclosure · 03 Supply Chain · 04 Data and Model Poisoning · 05 Improper Output Handling · 06 Excessive Agency · 07 System Prompt Leakage · 08 Vector and Embedding Weaknesses · 09 Misinformation · 10 Unbounded Consumption. 한국어판 게시(2025-07-22). 사이트에 별도 "Agentic Security" 메뉴 있음(내용 미확인) | 22·16·23 |
| 52 | OWASP LLM01:2025 Prompt Injection | https://genai.owasp.org/llmrisk/llm01-prompt-injection/ | Direct·Indirect Prompt Injection 정의(외부 웹사이트·파일 속 내용) | 22 |
| 53 | OpenTelemetry GenAI semantic conventions — spans | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md | 상태 **Development**. 원 저장소(semantic-conventions/docs/gen-ai)는 "Moved" — 별도 저장소 semantic-conventions-genai로 이동. `gen_ai.usage.input_tokens`는 캐시 토큰 포함 SHOULD, `gen_ai.usage.cache_read.input_tokens` 별도. **갱신(23 집필, 2026-10-08)**: 클라이언트 추론 스팬은 `gen_ai.client.inference`("Client Inference" 문서) | 10·23 |
| 54 | OpenTelemetry GenAI semantic conventions — metrics | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md | 상태 Development. `gen_ai.client.operation.duration`, `gen_ai.server.request.duration`, `gen_ai.server.time_to_first_token`("Time to generate first token for successful responses"), `gen_ai.server.time_per_output_token`("…generated after the first token…"). **갱신(23 집필, 2026-10-08)**: 클라이언트 지표가 `gen_ai.client.inference.*`로 개명 — 토큰은 `gen_ai.client.token.usage` → `gen_ai.client.inference.usage.*` 카운터(#374, 2026-09-22), 추론 지연은 `gen_ai.client.operation.duration` → `gen_ai.client.inference.duration`(#521, 2026-10-06), 첫 청크 `gen_ai.client.inference.time_to_first_chunk` | 10·23 |

## D. 서빙 소프트웨어·라이브러리 문서

| # | 출처 | URL | 확인한 것 | 쓰는 leaf |
|---|---|---|---|---|
| 55 | pgvector README (v0.8.7 설치 안내 기준) | https://github.com/pgvector/pgvector (raw README) | 기본은 정확 최근접(완전 recall), 근사 인덱스 추가 후 결과가 달라짐. HNSW: m 기본 16, ef_construction 기본 64, hnsw.ef_search 기본 40, IVFFlat보다 속도-recall 좋고 구축 느리고 메모리 큼, 학습 단계 없음. IVFFlat: 데이터가 있을 때 생성, lists 시작점 rows/1000(1M 이하)·sqrt(rows)(1M 초과), probes 기본 1·시작점 sqrt(lists), probes = lists면 정확 검색. 필터는 인덱스 스캔 **후** 적용 — "condition matches 10% of rows … default hnsw.ef_search of 40, only 4 rows will match on average", 0.8.0부터 반복 스캔(hnsw.max_scan_tuples 기본 20,000). 멀티테넌시: 공유 근사 인덱스는 다른 테넌트 recall에 영향. 차원 한도 vector 2,000·halfvec 4,000·bit 64,000. Hybrid Search 절에서 RRF·교차 인코더 예제 링크. 로컬 이미지 `pgvector/pgvector:pg17`(2026-10-02 생성) 있음 — 실제 확장 버전은 실험 때 `SELECT extversion` 확인 | 16·17 |
| 56 | vLLM 문서 — Metrics(design) | https://docs.vllm.ai/en/latest/design/metrics/ | `vllm:time_to_first_token_seconds`, `vllm:inter_token_latency_seconds`(연속 스트림 출력 사이 — 출력당 토큰 1개일 때만 TPOT에 근사), `vllm:request_time_per_output_token_seconds` = (종단 − TTFT)/(출력 토큰 − 1), 출력 1개 이하면 0으로 기록, `vllm:kv_cache_usage_perc` | 10 |
| 57 | tiktoken README | https://github.com/openai/tiktoken | "fast BPE tokeniser", o200k_base 인코딩 예 | 04 |

## E. LLM API 제공자 문서 (모두 2026-10-08 확인 — 노트 집필 때 재확인)

| # | 출처 | URL | 확인한 것 | 쓰는 leaf |
|---|---|---|---|---|
| 58 | Anthropic — Streaming messages | https://platform.claude.com/docs/en/build-with-claude/streaming | SSE 이벤트 이름: message_start → content_block_start/delta/stop → message_delta → message_stop, ping 이벤트, 스트림 안 error 이벤트(overloaded_error — 비스트리밍이면 HTTP 529) | 11 |
| 59 | Anthropic — Errors | https://platform.claude.com/docs/en/api/errors | 400·413·429·500·504·529 의미, 429는 지출 한도 도달 시 retry-after 없음, "an error can occur after the API returns a 200 response"(SSE), request-id 헤더, 10분 넘는 요청은 스트리밍·Batches 권장 | 11 |
| 60 | Anthropic — Rate limits | https://platform.claude.com/docs/en/api/rate-limits | "The API uses the token bucket algorithm" — 고정 구간 리셋이 아니라 연속 보충, RPM·ITPM·OTPM, 초과 시 429 + retry-after, 대부분 모델에서 cache_read 토큰은 ITPM에 미포함(캐시 인지 ITPM), 60 RPM이 초당 1로 집행될 수 있음 | 11·12·23 |
| 61 | Anthropic — Prompt caching | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | 접두(prefix) 캐시, 기본 TTL 5분(사용 시 무료 갱신)·1시간 옵션, 5분 캐시 쓰기 = 기본 입력 가격 1.25배, 1시간 = 2배 | 12 |
| 62 | Anthropic — Structured outputs | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | constrained decoding으로 스키마 준수 보장, 새 스키마 첫 요청은 문법 컴파일 지연·24시간 캐시, 스키마·도구 집합 변경 시 캐시 무효 | 14 |
| 63 | Anthropic — Context windows | https://platform.claude.com/docs/en/build-with-claude/context-windows | 4.5 이후 모델: 입력 + max_tokens가 문맥 창을 넘어도 요청 수락, 생성이 한도에 닿으면 stop_reason "model_context_window_exceeded" | 04·11 |
| 64 | OpenAI — Streaming API responses | https://developers.openai.com/api/docs/guides/streaming-responses | Responses API는 의미 이벤트(response.output_text.delta, response.completed 등) | 11 |
| 65 | OpenAI — Rate limits | https://developers.openai.com/api/docs/guides/rate-limits | RPM·RPD·TPM·TPD, x-ratelimit-* 헤더, 429·503에 Retry-After 있을 수 있음(최소값으로 취급 + 지터), SDK가 429·503 자동 재시도 — 앱 재시도와 합산 주의, 429 `slow_down`과 503 `server_is_overloaded` 구분(11 집필·판정, 2026-10-08), "unsuccessful requests contribute to your per-minute limit", 한도 계산은 max_tokens와 추정 토큰 중 큰 값 | 11·13 |
| 66 | OpenAI — Error codes | https://developers.openai.com/api/docs/guides/error-codes | 429 종류(Rate limit reached·Slow down·spend limit·quota 등), 500, 503 Model temporarily overloaded | 11 |
| 67 | OpenAI — Structured Outputs | https://developers.openai.com/api/docs/guides/structured-outputs | refusal 필드로 거부 감지, max tokens 도달 시 incomplete 응답 처리 예, JSON mode와 구분, additionalProperties: false | 14 |
| 68 | OpenAI — Prompt caching | https://developers.openai.com/api/docs/guides/prompt-caching | cached_tokens 보고(128 단위 내림), prompt_cache_key로 캐시 라우팅 | 12·23 |
| 69 | OpenAI — Embeddings | https://developers.openai.com/api/docs/guides/embeddings | text-embedding-3-small·large, 출력 크기 조절 파라미터, 차원을 줄인 뒤 정규화 예제 코드 | 05·18 |
| 70 | Gemini API — Rate limits | https://ai.google.dev/gemini-api/docs/rate-limits | RPM·TPM(입력)·RPD, 한도는 API 키가 아니라 프로젝트 단위 | 11 |
| 71 | Gemini API — Troubleshooting | https://ai.google.dev/gemini-api/docs/troubleshooting | 429 RESOURCE_EXHAUSTED·503 UNAVAILABLE에 지수 백오프, 400·402·403은 재시도 금지, SDK 기본 자동 재시도 | 11 |
| 72 | Gemini API — Tokens | https://ai.google.dev/gemini-api/docs/tokens | "a token is equivalent to about 4 characters", "100 tokens is equal to about 60-80 English words"(영어 기준 — 한국어 수치는 없음) | 04 |

## F. 기술 블로그·사건 1차 자료

| # | 출처 | URL | 확인한 것 | 쓰는 leaf |
|---|---|---|---|---|
| 73 | He·Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference" (2025-09-10) | https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ | temperature 0이어도 API가 실제로 비결정적, "동시성 + 부동소수" 가설은 전부가 아님(같은 행렬곱 반복은 비트 동일), 원인 = 배치 불변성 부재. Qwen3-235B, temperature 0, 1000회 → 서로 다른 완성 80개(최빈 78회), 배치 불변 커널이면 1000개 동일 | 07 |
| 74 | Anthropic, "Contextual Retrieval" (2024-09-19) | https://www.anthropic.com/engineering/contextual-retrieval (구 news/contextual-retrieval) | 청크는 "usually no more than a few hundred tokens"(수치 권고 없음 — report §4.1 #4와 일치), 임베딩은 정확 일치("Error code TS-999")를 놓칠 수 있어 BM25 결합, Contextual Embeddings + Contextual BM25로 top-20 검색 실패율 49% 감소(5.7% → 2.9%), 재순위 결합 시 67% | 15·17 |
| 75 | Anthropic, "Building effective agents" (2024-12-19) | https://www.anthropic.com/engineering/building-effective-agents | workflows = 미리 정한 코드 경로, agents = 모델이 과정·도구를 동적으로 지시. 페이지 머리에 "tooling landscape … has changed since December 2024" 고지 | 20 |
| 76 | Anthropic, "A postmortem of three recent issues" (2025-09-17) | https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues | 2025-08~09 세 인프라 버그: ① 문맥 창 라우팅 오류(08-05 시작, Sonnet 4 요청 0.8% → 08-29 부하 분산 변경 후 최악 시간대 16%, 라우팅이 sticky) ② TPU 설정 오류로 출력 손상(영어 질문에 태국어·중국어 문자 등) ③ 근사 top-k XLA:TPU 컴파일러 버그. 대응: 롤백, 이상 문자 출력 탐지 테스트 추가, 정확 top-k로 교체 | 26·07·13 |
| 77 | Mata v. Avianca, Inc., No. 22-cv-1461 (PKC), S.D.N.Y. Opinion and Order on Sanctions (2023-06-22) | https://storage.courtlistener.com/recap/gov.uscourts.nysd.575368/gov.uscourts.nysd.575368.54.0_3.pdf | 1쪽: 변호사들이 ChatGPT가 만든 존재하지 않는 판례·가짜 인용을 제출하고 법원 명령 뒤에도 고수 → 제재 | 26 |

## 미확인 (열지 못했거나 이번에 열지 않음)

| 출처 | 사유 | 대체 |
|---|---|---|
| ~~Moffatt v. Air Canada, 2024 BCCRT 149~~ | task 01에서는 canlii.org·decisions.civilresolutionbc.ca 모두 403 | **확인됨**(26 집필·판정 A6, 2026-10-08): CRT 공식 결정 페이지, 결정 2024-02-14 |
| OpenAI "March 20 ChatGPT outage" | openai.com 403 | 26 후보에서 보류 |
| Radford 외 2019 GPT-2 논문(바이트 수준 BPE) | 이번에 열지 않음(report는 열었다고 기록) | cdn.openai.com PDF 재확인 |
| Malkov–Yashunin IEEE TPAMI 2020 학술지판 | 열지 않음 | arXiv 판으로 인용 |
| Vaswani 외 게재처(NeurIPS 2017)·Matryoshka 게재처 | abs 페이지에 게재처 없음 | 학회 페이지 확인 (Sarathi-Serve OSDI 2024는 09 집필에서 USENIX 페이지로 확인) |
| ~~DistServe의 goodput 정의 문장, vLLM 논문의 copy-on-write 세부~~ | task 01에서는 초록만 | **확인됨**(09·10 집필·판정 A3): DistServe §1 goodput 정의, vLLM §4.4 |
| DDIA 1판 11·12장 | 이번에 열지 않음(커리큘럼 기존 `[?]`와 같음) | — |
| OWASP "Agentic Security"(에이전트용 Top 10) | 메뉴만 확인, 내용 미열람 | 22·20 집필 때 확인 |
| 의미 캐시의 다른 1차 자료(GPTCache 등) | 찾지 않음 | 34번으로 충분한지 집필자 판단 |

## 집계

- 직접 열어 확인: **77건**(논문 38 · 교재 2 · 명세·표준 14 · 서빙 문서 3 · 제공자 문서 15 · 블로그·사건 5).
- 미확인: **9건**(위 표).
