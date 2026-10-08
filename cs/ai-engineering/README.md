# AI 엔지니어링 — `cs/ai-engineering/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §22에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 26 · 검수 완료 0

> **범위**: 백엔드 개발자가 LLM을 **느리고 비싸고 비결정적인 외부 의존성**으로 호출·서빙·검색·평가·보호하는 데 필요한 것. 원리(학습·어텐션·디코딩)는 이 목적에 필요한 동작 수준까지만 다룬다. **다루지 않는 것**: 비전·음성·강화학습·이미지 생성·정렬(alignment) 연구, 모델 사전학습, 특정 SDK·프레임워크 사용법. 다 읽으면 "잘린 응답·같은 입력 다른 답·첫 토큰 지연·429 폭주·검색 품질 붕괴·평가 점수 흔들림·간접 인젝션"을 증상으로 보고 원인 leaf를 짚을 수 있어야 한다.
> **단일 출처**(여기서 반복하지 않고 링크만): 엔트로피 = math/14 · 코사인·내적 = math/13 · 경사 하강 = data-analysis/22 · BM25·분석기 = database/46 · 백분위·히스토그램 = data-analysis/05 · 큐잉·리틀 법칙 = math/10 · 신뢰구간·검정 = data-analysis/08·09 · 타임아웃·재시도·서킷·멱등 = reliability/05·06·10·13 · 토큰 버킷 = reliability/11.
> **빠르게 바뀌는 사실**(API 동작·한도·가격·명세 버전)은 노트마다 확인 날짜를 적는다. 이 절의 📚 확인일은 2026-10-08이다. AIEFS(rohitg00/ai-engineering-from-scratch)는 근거로 쓰지 않고 "실습 참고" 링크로만 쓴다(report §5c 링크 금지 목록 준수).
> 뼈대: Jurafsky–Martin 『Speech and Language Processing』 3판 초안(2026-08-19판 — 2장 Words and Tokens·3장 N-gram LM·5장 Embeddings·6장 Neural Networks·7장 Transformers and Pretraining·8장 Post-training·11장 Information Retrieval and RAG), Goodfellow·Bengio·Courville 『Deep Learning』(2016 — 3.13·5장·6.2·6.5·8장), Vaswani 외 2017, Kwon 외 SOSP 2023(vLLM), Lewis 외 NeurIPS 2020(RAG), Zheng 외 NeurIPS 2023(LLM-as-a-judge), MCP 명세 2026-07-28, OWASP Top 10 for LLM Applications 2025, OpenTelemetry GenAI semantic conventions.

## 22.1 학습의 최소 원리

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `ml-in-one-page` | 학습 = 손실 최소화. 학습·검증·테스트 분리, 과적합·과소적합, 데이터 누설. 백엔드 독자가 "모델 품질 숫자"를 읽기 위한 최소 | 필수 | 초안(Claude) | [01-ml-in-one-page](01-ml-in-one-page/) |
| 02 | `gradient-descent-and-backprop` | 연쇄 법칙과 역전파(역방향 자동 미분), 학습률과 발산. 경사 하강 자체는 data-analysis/22 단일 출처 | 권장 | 초안(Claude) | [02-gradient-descent-and-backprop](02-gradient-descent-and-backprop/) |
| 03 | `cross-entropy-and-perplexity` | 교차 엔트로피 = 음의 로그우도(NLL), perplexity = exp(토큰당 평균 NLL). 토큰 단위가 다르면 비교할 수 없다. 엔트로피 정의는 math/14 단일 출처 | 권장 | 초안(Claude) | [03-cross-entropy-and-perplexity](03-cross-entropy-and-perplexity/) |

## 22.2 모델이 텍스트를 다루는 방식

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `tokenization-and-token-cost` | BPE·바이트 수준 BPE. 같은 뜻이라도 언어(한국어 vs 영어)·토크나이저마다 토큰 수가 다르다. 토큰 = 과금 단위·문맥 한도 단위·생성 시간 단위 | 필수 | 초안(Claude) | [04-tokenization-and-token-cost](04-tokenization-and-token-cost/) |
| 05 | `embeddings-and-similarity` | 임베딩 = 텍스트 → 고정 길이 벡터. 코사인·내적·L2의 관계(정규화하면 순위가 같다). 임베딩 모델 교체 = 벡터 공간 교체. 코사인 정의는 math/13 단일 출처 | 필수 | 초안(Claude) | [05-embeddings-and-similarity](05-embeddings-and-similarity/) |
| 06 | `transformer-and-attention` | 셀프 어텐션 softmax(QKᵀ/√d)V, 멀티헤드, 인과 마스크, 위치 정보 — 동작 수준. 문맥 길이에 대해 어텐션 연산·메모리가 제곱으로 늘어난다 | 권장 | 초안(Claude) | [06-transformer-and-attention](06-transformer-and-attention/) |
| 07 | `decoding-and-nondeterminism` | 로짓 → softmax → temperature·top-k·top-p(nucleus) 샘플링, greedy. 같은 입력 다른 출력의 두 원인: 샘플링, 그리고 서버 배치 구성에 따라 달라지는 수치 연산 | 필수 | 초안(Claude) | [07-decoding-and-nondeterminism](07-decoding-and-nondeterminism/) |
| 08 | `kv-cache-and-inference-memory` | 프리필(프롬프트 전체를 병렬 처리) vs 디코드(토큰 하나씩). KV 캐시 크기 = 2 × 층 × KV 헤드 × 헤드 차원 × 원소 바이트 × 토큰 수. MQA·GQA로 KV 헤드를 줄인다 | 권장 | 초안(Claude) | [08-kv-cache-and-inference-memory](08-kv-cache-and-inference-memory/) |

## 22.3 서빙과 호출

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 09 | `inference-serving-and-batching` | 요청 단위 배칭 vs 반복(iteration) 단위 연속 배칭, 페이지드 KV(고정 크기 블록 할당), 청크 프리필, 프리필·디코드 분리 배치 | 심화 | 초안(Claude) | [09-inference-serving-and-batching](09-inference-serving-and-batching/) |
| 10 | `inference-latency-metrics` | TTFT(첫 토큰까지)·TPOT(첫 토큰 이후 토큰당)·ITL(연속 스트림 출력 사이)·종단 지연·goodput(지연 목표 달성률을 지키며 받을 수 있는 최대 요청률 — DistServe). 도구·규약마다 정의가 다르다 | 필수 | 초안(Claude) | [10-inference-latency-metrics](10-inference-latency-metrics/) |
| 11 | `llm-api-client-contract` | LLM 호출 클라이언트 계약: SSE 스트리밍 이벤트, 스트림 중간 오류, 타임아웃 층위(첫 토큰·토큰 사이·전체), 429·529/503과 Retry-After, 중단 사유 확인, 토큰·비용 상한 | 필수 | 초안(Claude) | [11-llm-api-client-contract](11-llm-api-client-contract/) |
| 12 | `prompt-and-semantic-caching` | 제공자 프롬프트(프리픽스) 캐시 — 정확히 같은 접두만 적중, TTL, 쓰기 비용 — vs 애플리케이션 의미 캐시 — 임베딩 유사도 임계값으로 적중, 오적중 위험 | 권장 | 초안(Claude) | [12-prompt-and-semantic-caching](12-prompt-and-semantic-caching/) |
| 13 | `model-routing-and-fallback` | LLM 게이트웨이, 난이도·비용 라우팅과 캐스케이드, 제공자·모델 폴백, 서킷 브레이커, 폴백 모델의 형식·품질 차이 | 권장 | 초안(Claude) | [13-model-routing-and-fallback](13-model-routing-and-fallback/) |
| 14 | `structured-output-and-tool-calling` | JSON 스키마로 출력 형식 강제(제약 디코딩) vs 프롬프트로 부탁하기, 검증 실패·거부·잘림 처리, 도구 호출 계약(이름·인자 스키마·결과) | 필수 | 초안(Claude) | [14-structured-output-and-tool-calling](14-structured-output-and-tool-calling/) |

## 22.4 검색 증강 생성(RAG)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `rag-pipeline` | 수집 → 청킹 → 임베딩 → 검색 → 프롬프트 조립 → 출처 표기. 파라미터 지식(모델 가중치) vs 비파라미터 지식(검색 인덱스) | 필수 | 초안(Claude) | [15-rag-pipeline](15-rag-pipeline/) |
| 16 | `vector-index-ann` | 전수(정확) 검색 vs 근사 최근접(ANN): HNSW(계층 근접 그래프)·IVFFlat(군집 목록). recall·지연·메모리·구축 시간의 절충, pgvector 파라미터(m·ef_construction·ef_search, lists·probes), 필터와의 상호작용 | 필수 | 초안(Claude) | [16-vector-index-ann](16-vector-index-ann/) |
| 17 | `hybrid-search-and-reranking` | 어휘 검색(BM25)과 밀집 검색(벡터)의 결합. 점수 척도가 달라 순위로 합성(RRF), 교차 인코더 재순위. BM25 식은 database/46 단일 출처 | 권장 | 초안(Claude) | [17-hybrid-search-and-reranking](17-hybrid-search-and-reranking/) |
| 18 | `index-freshness-and-reembedding` | 원천이 바뀌면 재청킹·재임베딩·재색인, 삭제 전파, 임베딩 모델 교체 시 이중 색인 후 전환, 신선도 지연 감지 | 권장 | 초안(Claude) | [18-index-freshness-and-reembedding](18-index-freshness-and-reembedding/) |

## 22.5 평가·에이전트·보안·운영

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 19 | `llm-evaluation` | 평가셋 설계(골든셋·회귀셋), 정답 일치·루브릭·LLM 판정자, 판정자 편향(위치·장황함·자기 선호), 신뢰구간과 짝지은 비교, 배포 전 회귀 게이트 | 필수 | 초안(Claude) | [19-llm-evaluation](19-llm-evaluation/) |
| 20 | `agent-loop-and-tool-safety` | 에이전트 = 모델이 다음 도구 호출을 고르는 루프. 종료 조건·턴·토큰·시간 예산, 관측 정리, 부작용 도구의 멱등 키·사람 확인·최소 권한, 고정 경로 워크플로와의 선택 | 필수 | 초안(Claude) | [20-agent-loop-and-tool-safety](20-agent-loop-and-tool-safety/) |
| 21 | `mcp-protocol` | MCP = JSON-RPC 2.0 위의 도구·리소스·프롬프트 제공 규약. 2026-07-28판 무상태화(초기화 핸드셰이크·세션 제거, 요청마다 `_meta`로 버전·능력 전달), server/discover, 캐시 가능 결과(ttlMs·cacheScope), 오류 코드 할당 정책 | 권장 | 초안(Claude) | [21-mcp-protocol](21-mcp-protocol/) |
| 22 | `prompt-injection-and-llm-security` | 신뢰 경계: 지시와 데이터가 같은 채널(프롬프트)에 섞인다. 직접·간접 인젝션, 모델 출력도 신뢰하지 않기, 과도한 에이전시, 시스템 프롬프트 유출, 무제한 소비, 개인정보. 방어 원리 중심 | 필수 | 초안(Claude) | [22-prompt-injection-and-llm-security](22-prompt-injection-and-llm-security/) |
| 23 | `llm-observability-and-cost` | OTel GenAI 스팬·지표(gen_ai.* — 모델·토큰 사용량·TTFT), 요청 단위 비용 귀속(입력·캐시 쓰기·캐시 읽기·출력 토큰), 프롬프트·응답 기록과 개인정보, 품질 신호 | 권장 | 초안(Claude) | [23-llm-observability-and-cost](23-llm-observability-and-cost/) |
| 24 | `fine-tuning-vs-rag-decision` | 지식은 검색(RAG), 형식·말투·작업 방식은 프롬프트나 파인튜닝. LoRA(저랭크 어댑터)·QLoRA 개념, 선택 기준(갱신 빈도·출처 표기·비용·평가 데이터) | 심화 | 초안(Claude) | [24-fine-tuning-vs-rag-decision](24-fine-tuning-vs-rag-decision/) |

## 22.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 25 | `ai-symptom-index` | 역색인: 응답이 잘림·JSON 파싱 실패, 같은 입력 다른 답, 첫 토큰이 늦음·스트림 멈칫, 429가 안 끝남, 비용 급증, 검색이 엉뚱함·결과 수 부족, 모델 교체 뒤 품질 붕괴, 평가 점수 흔들림, 에이전트 반복, 모델이 문서 속 지시를 따름 | 필수 | 초안(Claude) | [25-ai-symptom-index](25-ai-symptom-index/) |
| 26 | `ai-incidents` | 실사건: Mata v. Avianca(2023 — 생성된 가짜 판례 인용 제재) · Anthropic 응답 품질 저하 3중 버그(2025-08~09 — 문맥 길이 라우팅 오류·TPU 출력 손상·근사 top-k 컴파일러 버그) · Greshake 외 간접 인젝션 시연(2023 — 실제 LLM 통합 앱) · Moffatt v. Air Canada(2024 — 챗봇 오안내 배상) | 권장 | 초안(Claude) | [26-ai-incidents](26-ai-incidents/) |
