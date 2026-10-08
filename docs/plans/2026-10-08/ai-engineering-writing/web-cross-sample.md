# 웹 교차 표본 — ai-engineering (사실 점검 워커가 원문을 직접 열어 인용)

| 편 | 주장 | 출처 | 원문 인용 |
|---|---|---|---|
| 01 | 검증 오류는 일반화 오류를 과소 추정 | https://www.deeplearningbook.org/contents/ml.html | "the validation set error will underestimate the generalization error, though typically by a smaller amount than the training error does" |
| 01 | 80/20 분할 | 같은 URL | "Typically, one uses about 80 percent of the training data for training and 20 percent for validation." |
| 01 | 데이터 오염 | SLP3 3장 PDF (2026-08-19판) | "We call this situation training on the test set or also data contamination." |
| 02 | 역전파는 기울기 계산법만 | https://www.deeplearningbook.org/contents/mlp.html | "refers only to the method for computing the gradient" |
| 02 | 역방향 누적 | 같은 URL 6.5.9 | "It is a special case of a broader class of techniques called reverse mode accumulation" |
| 02 | 학습률 과대 | https://www.deeplearningbook.org/contents/optimization.html 8.3.1 | "If it is too large, the learning curve will show violent oscillations, with the cost function often increasing significantly." |
| 03 | PPL 비교 조건 | SLP3 3.3 | "the perplexity of two language models is only comparable if they use identical vocabularies." |
| 03 | 토크나이저 민감 | SLP3 7.7.1 | "perplexity is best used when comparing language models that use the same tokenizer." |
| 03 | logprob 센티널 | https://developers.openai.com/api/docs/api-reference/chat/create | "if it is within the top 20 most likely tokens. Otherwise, the value -9999.0 is used" |
| 06 | 내적 분산 d_k | https://arxiv.org/abs/1706.03762 각주 4 | "has mean 0 and variance dk" |
| 06 | 게재처 | 같은 PDF | "31st Conference on Neural Information Processing Systems (NIPS 2017)" |
| 06 | Lost in the middle | https://arxiv.org/abs/2307.03172 | "performance is often highest when relevant information occurs at the beginning or end of the input context" |
| 08 | OPT-13B KV 800KB/토큰 | https://arxiv.org/abs/2309.06180 §3 | "the KV cache of a single token demands 800 KB of space, calculated as 2 × 5120 × 40 × 2" |
| 08 | 롤링 버퍼 8배 | https://arxiv.org/abs/2310.06825 | "On a sequence length of 32k tokens, this reduces the cache memory usage by 8x" |
| 08 | vLLM KV 사용률 지표 | https://docs.vllm.ai/en/latest/design/metrics/ | "vllm:kv_cache_usage_perc (Gauge) - Fraction of used KV cache blocks (0–1)." |
| 04 | Opus 4.7 이후 토크나이저 약 30%↑ | https://platform.claude.com/docs/en/build-with-claude/token-counting | "The same input text produces approximately 30 percent more tokens than on earlier models." |
| 04 | 4.5 이후 문맥 초과 수락 | https://platform.claude.com/docs/en/build-with-claude/context-windows | "On Claude 4.5 models and newer, if input tokens plus max_tokens exceeds the context window size, the API accepts the request." |
| 04 | tiktoken 평균 4바이트 | https://github.com/openai/tiktoken | "On average, in practice, each token corresponds to about 4 bytes." |
| 05 | SBERT 65시간→5초 | https://arxiv.org/abs/1908.10084 | "from 65 hours with BERT / RoBERTa to about 5 seconds with SBERT" |
| 05 | `<#>` 음의 내적 | https://github.com/pgvector/pgvector | "`<#>` returns the negative inner product since Postgres only supports `ASC` order index scans on operators" |
| 05 | OpenAI 임베딩 정규화 | https://developers.openai.com/api/docs/guides/embeddings | "OpenAI embeddings are normalized to length 1" |
| 07 | Anthropic temperature 제한 | https://platform.claude.com/docs/en/api/messages/create | "Models released after Claude Opus 4.6 do not support setting temperature. A value of 1.0 will be accepted for backwards compatibility, all other values will be rejected with a 400 error." |
| 07 | temperature 0, 1,000회 | https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ | "we generate 80 unique completions, with the most common of these occuring 78 times." |
| 07 | OpenAI seed | OpenAI chat completions create reference | "Deprecated. This feature is in Beta. … Determinism is not guaranteed" |
| 12 | Anthropic 캐시 쓰기 배수 | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | "5-minute cache write tokens are 1.25 times the base input tokens price" |
| 12 | Anthropic TTL 시작점 | 같은 문서 | "The lifetime is measured from the start of the request that writes or reads the cache entry" |
| 12 | OpenAI GPT-5.6 이후 TTL | https://developers.openai.com/api/docs/guides/prompt-caching | "Use prompt_cache_options.ttl … The only supported value, 30m, is also the default." |
| 24 | LoRA 파라미터 식 | https://arxiv.org/pdf/2106.09685 §5.1 | "|Θ| = 2 × L̂LoRA × dmodel × r" |
| 24 | 18M 예산 | 같은 논문 §7.1 | "We set a parameter budget of 18M (roughly 35MB if stored …)" |
| 24 | QLoRA 규모 | https://arxiv.org/abs/2305.14314 | "finetune a 65B parameter model on a single 48GB GPU while preserving full 16-bit finetuning task performance" |
| 19 | Zheng 표 2 GPT-4 일관률 | arXiv 2306.05685 PDF | "default 65.0% 30.0% 5.0% 0.0%" |
| 19 | Zheng 표 3 반복 목록 실패율 | 같은 PDF | "Failure rate 91.3% 91.3% 8.7%" |
| 19 | Miller 3.3 temperature | arXiv 2411.00640 | "In neither case should the sampling temperature be adjusted for the sake of reducing variance" |
| 20 | 도구 루프 종료 사유 | platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works | "The loop exits on any other stop reason (`end_turn`, `max_tokens`, `stop_sequence`, or `refusal`)" |
| 20 | 최대 반복 조건 | anthropic.com/engineering/building-effective-agents | "common to include stopping conditions (such as a maximum number of iterations)" |
| 20 | 도구 오류 전달 | MCP 2026-07-28 server/tools | "Clients SHOULD provide tool execution errors to language models to enable self-correction." |
| 21 | `_meta` 필수 필드 누락 | MCP 2026-07-28 basic | "A request missing any required field is malformed; the server MUST reject it with JSON-RPC error code `-32602`" |
| 21 | 오류 코드 재번호 | MCP changelog | "`UnsupportedProtocolVersion` `-32004` → `-32022`" |
| 21 | 캐시 힌트 | MCP server/utilities/caching | "Servers MUST include caching hints on results … `server/discover`" |
| 22 | 인젝션 완전 방어 불명 | genai.owasp.org/llmrisk/llm01-prompt-injection/ | "it is unclear if there are fool-proof methods of prevention for prompt injection" |
| 22 | 시스템 프롬프트는 비밀 아님 | OWASP LLM07 | "the system prompt should not be considered a secret, nor should it be used as a security control" |
| 22 | CaMeL | arXiv 2503.18813 | "solving 77% of tasks with provable security (compared to 84% with an undefended system)" |
| 23 | input_tokens에 캐시 포함 | semantic-conventions-genai client-inference.md | "`gen_ai.usage.input_tokens`: This value SHOULD include all types of input tokens, including cached tokens." |
| 23 | 지표 개명 #521 | GitHub commits (2026-10-06) | "Use `gen_ai.client.inference.duration` metric instead of `gen_ai.client.operation.duration` … (#521)" |
| 23 | 원문 기록 기본 꺼짐 | gen-ai-spans.md | "OpenTelemetry instrumentations SHOULD NOT capture them by default" |
| 15 | Contextual Retrieval 실패율 | https://www.anthropic.com/engineering/contextual-retrieval | "Combining Contextual Embeddings and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 49% (5.7% → 2.9%)." |
| 15 | Lost in the Middle | https://arxiv.org/abs/2307.03172 | "performance is often highest when relevant information occurs at the beginning or end of the input context" |
| 15 | DPR 유사도 | https://arxiv.org/pdf/2004.04906 | "We define the similarity between the question and the passage using the dot product of their vectors" |
| 16 | 필터 결과 수 부족 | pgvector README | "If a condition matches 10% of rows, with HNSW and the default `hnsw.ef_search` of 40, only 4 rows will match on average." |
| 16 | 반복 스캔 | pgvector README | "Starting with 0.8.0, you can enable iterative index scans … (or it reaches `hnsw.max_scan_tuples` or `ivfflat.max_probes`)." |
| 16 | HNSW 층 배정 | https://arxiv.org/abs/1603.09320 | "The maximum layer in which an element is present is selected randomly with an exponentially decaying probability distribution." |
| 17 | RRF k=60 | https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf | "where k = 60 was fixed during a pilot investigation and not altered during subsequent validation" |
| 17 | 교차 인코더 입력 | https://arxiv.org/pdf/1901.04085 | "we feed the query as sentence A and the passage text as sentence B" |
| 17 | pgvector 하이브리드 | pgvector README | "You can use Reciprocal Rank Fusion or a cross-encoder to combine results." |
| 18 | 임베딩 기본 길이 | https://developers.openai.com/api/docs/guides/embeddings | "By default, the length of the embedding vector is 1536 for text-embedding-3-small or 3072 for text-embedding-3-large." |
| 18 | 차원 섞기 | pgvector README FAQ | "you can only create indexes on rows with the same number of dimensions (using expression and partial indexing)" |
| 18 | 인덱스 교체 | https://arxiv.org/pdf/2005.11401 | "Accuracy with mismatched indices is low (12% with the 2018 index and 2016 leaders, 4% with the 2016 index and 2018 leaders)." |
| 09 | Orca 처리량 36.9배 | https://www.usenix.org/conference/osdi22/presentation/yu | "36.9× throughput improvement at the same level of latency." |
| 09 | vLLM 선점 정책 | https://arxiv.org/abs/2309.06180 §4.5 | "it ensures that the earliest arrived requests are served first and the latest requests are preempted first." |
| 09 | DistServe goodput | https://arxiv.org/abs/2401.09670 §1 | "per-GPU goodput, defined as the maximum request rate that can be served adhering to the SLO attainment goal (say, 90%)" |
| 10 | vLLM TTFT 시작점 | https://docs.vllm.ai/en/latest/design/metrics/ | "Currently arrival_time starts when tokenization begins." |
| 10 | TPOT 0 기록 | 같은 문서 | "Requests that generate no more than one token are recorded with a TPOT of zero, while vllm bench serve excludes them" |
| 10 | OTel 서버 TTFT | semantic-conventions-genai gen-ai-metrics.md | "It helps measure the time spent in the queue and the prefill phase." |
| 11 | Anthropic 지출 상한 429 | https://platform.claude.com/docs/en/api/rate-limits | "The error type is `rate_limit_error`, the same as for a rate limit, but the response has no `retry-after` header." |
| 11 | OpenAI 스트림 뒤 오류 | https://developers.openai.com/api/docs/guides/rate-limits | "An error after streaming begins can arrive as a stream event; don't automatically replay a request after consuming output." |
| 11 | Anthropic SDK 재시도 | https://platform.claude.com/docs/en/api/errors | "The official SDK automatically retries transient failures … twice by default, honoring the `retry-after` header when present." |
| 13 | FrugalGPT 요금 차 | https://arxiv.org/abs/2305.05176 | "fees that can differ by two orders of magnitude" |
| 13 | RouteLLM 절감 | https://arxiv.org/abs/2406.18665 | "significantly reduces costs-by over 2 times in certain cases-without compromising the quality of responses" |
| 13 | sticky 라우팅 | https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues | "some users were affected more severely, as our routing is \"sticky\"." |
| 14 | Anthropic 미지원 키워드 | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | "Numerical constraints (such as `minimum`, `maximum`, `multipleOf`)" (Not supported) |
| 14 | 컴파일 타임아웃 | 같은 문서 | "the API also enforces a **compilation timeout of 180 seconds**" |
| 14 | OpenAI 호출 개수 | https://developers.openai.com/api/docs/guides/function-calling | "model responses can include zero, one, or multiple calls, it is best practice to assume there are several." |
| 25 | 일시 429에도 Retry-After 없을 수 있음 | https://developers.openai.com/api/docs/guides/rate-limits | "If it's missing or invalid, fall back to exponential backoff with jitter." |
| 25 | 지출 상한 429 구분 | https://platform.claude.com/docs/en/api/rate-limits | "The error type is rate_limit_error, the same as for a rate limit, but the response has no retry-after header." |
| 25 | 200의 의미 | RFC 9110 §15.3.1 | "The 200 (OK) status code indicates that the request has succeeded." |
| 26 | Anthropic 최악 시간대 16% | https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues | "At the worst impacted hour on August 31, 16% of Sonnet 4 requests were affected." |
| 26 | Mata 제재 | CourtListener Mata v. Avianca ECF 54 | "A penalty of $5,000 is jointly and severally imposed on Respondents" |
| 26 | Air Canada 챗봇 책임 | https://decisions.civilresolutionbc.ca/crt/crtd/en/item/525448/index.do ¶27 | "It makes no difference whether the information comes from a static page or a chatbot." |
