# rohitg00/ai-engineering-from-scratch 분석 — study-note 적용 검토

- 일시: 2026-10-04. 대상: `rohitg00/ai-engineering-from-scratch`(이하 AIEFS), 클론 HEAD `3be078b`(2026-10-02, depth 1), MIT. 클론 위치는 세션 scratchpad(저장소 밖).
- 방법: 클론 파일을 직접 열고 셌다(Python으로 셈 — 저장소 스크립트는 실행하지 않음). 사실 점검은 1차 출처(arXiv 초록, MCP 명세 changelog, GPT-2 논문 PDF, NVIDIA·Anthropic 문서)와 대조했다. 저장소 활동은 GitHub REST API(익명 GET)로 확인했다. 분석은 Opus 워커, 저장·정리는 메인.
- 우리 쪽 기준: `cs/README.md` 「작성 규칙」, `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`, 예시 leaf `cs/api-design/06-pagination/`·`cs/testing/02-good-unit-tests/`, 파이프라인 `docs/plans/2026-10-04/api-design-writing/{requirement-spec,briefing,web-cross-sample}.md`.

---

## 1. 한눈에 보기

1. 수학부터 에이전트·서빙까지 20 phase·523 레슨이다. 레슨 수 523은 실제 폴더 수와 맞는다. 시간은 문서마다 다르다(README ~342h, ROADMAP 머리 ~323h, ROADMAP 끝 ~1,081h, 레슨 `Time:` 합계 1,168.75h).
2. 레슨 형식은 문제 → 개념 → Build It(밑바닥 구현) → Use It(라이브러리) → Ship It(재사용 산출물) → 연습 → 용어 → 더 읽기다. 우리 7절 골격과 달리 **장애 시나리오 절이 없고**, 근거는 "더 읽기" 목록에만 모인다.
3. 품질은 고르지 않다. 표본 7편 중 MCP·ReAct 레슨은 1차 출처와 맞았지만, KV 캐시 계산은 32배 틀렸고 RAG 레슨은 "Anthropic 권고"를 근거 없이 인용했으며 BFT 레슨은 논문 수치를 잘못 읽었다. 퀴즈 2,237문항 중 89.9%에서 정답이 가장 긴 보기다(저장소 자체 검사기도 기준선 0.84로 인정) — 자동 생성 흔적이 강하다.
4. 가져올 만한 것은 형식 세 가지다: 용어 칸의 "흔히 하는 말 vs 실제 뜻", 학습 경로의 "완료 증거·범위 밖" 명시, 그리고 자기 규칙을 숫자로 세는 검사기와 그 검사기가 놓친 드리프트가 주는 교훈. 산출물 중심(Ship It)과 자동 생성 퀴즈는 "cs = 지식 본문만"·사실 점검 원칙과 맞지 않는다.
5. 우리 커리큘럼에는 AI/ML 영역이 없다. 백엔드 개발자에게 먼저 필요한 쪽은 "LLM을 호출·서빙·검색·평가하는 시스템"이고, 기존 math·database·reliability·api-design·security·data-analysis와 접점이 많다. 다만 공부 우선순위(기본기 → 도메인 → api/ops → …)를 보면 지금은 **새 영역 착수 대신 NEXT 후보 등록**을 권한다(§6).

---

## 2. 저장소 구조와 수치 (직접 센 값)

### 2.1 최상위 구성

| 경로 | 내용 (실제로 연 파일 기준) |
|---|---|
| `phases/NN-*/NN-*/` | 레슨 폴더. `docs/en.md`·`code/`·`outputs/`·`quiz.json`(일부)·`notebook/`(비어 있음)·`assets/` |
| `LESSON_TEMPLATE.md`·`AGENTS.md`·`CONTRIBUTING.md` | 레슨 계약. 세 문서가 서로 어긋난다(§4.3) |
| `learning-paths/*.json` | 12개 경로. 주제 경로 6개(`lessons[]`), 직무 경로 6개(`kind: career-route`, `stages`·`portfolioProof`·`coverage`·`completionClaim`) |
| `glossary/terms.md`·`myths.md` | 용어 250개(그중 `Sources:` 있는 것 143개) / 오해 21개 |
| `skills/` | 튜터 스킬 10개 |
| `certifications/` | Claude 인증 4트랙(레슨 33편)·MCPA(레슨 34편). "비공식·문항 유출 없음" 고지 |
| `projects/` | 프로젝트 48개 폴더(+`_template`). README 기준 "100개 중 48개 준비" |
| `scripts/`·`.github/workflows/` | 감사·카운트 동기화·퀴즈 편향·번역·책 빌드. 워크플로 4개 |
| `i18n/<12개 언어>/README.md`·`docs/i18n.md` | README만 사람이 번역. 레슨은 NLLB-200 기계 번역으로 `translations` 브랜치에만 |
| `book/` | phases를 pandoc으로 6권 EPUB·PDF로 묶음 |

### 2.2 phase별 레슨 수·시간·선행

레슨 수 = 폴더 수 = `docs/en.md` 수(모두 일치, README phase 배지 20개와도 일치). 시간 A = ROADMAP phase 머리 값, 시간 B = 레슨 `**Time:**` 칸 합.

| # | phase | 레슨 | 시간 A | 시간 B | 선행 |
|---|---|---|---|---|---|
| 0 | setup-and-tooling | 12 | ~14h | 7.7h | — |
| 1 | math-foundations | 22 | ~23h | 31.8h | 0 |
| 2 | ml-fundamentals | 18 | ~21h | 26.2h | 1 |
| 3 | deep-learning-core | 13 | ~15h | 18.8h | 2 |
| 4 | computer-vision | 28 | ~27h | 31.2h | 3 |
| 5 | nlp-foundations-to-advanced | 29 | ~30h | 30.5h | 3 |
| 6 | speech-and-audio | 17 | ~18h | 18.5h | 3 |
| 7 | transformers-deep-dive | 16 | ~14h | 16.5h | 5 |
| 8 | generative-ai | 15 | ~14h | 15.5h | 7 |
| 9 | reinforcement-learning | 12 | ~13h | 13.8h | 3 |
| 10 | llms-from-scratch | 24 | ~26h | 32.9h | 7 |
| 11 | llm-engineering | 17 | ~19h | 20.5h | 10 |
| 12 | multimodal-ai | 25 | ~65h | 67.0h | 10 |
| 13 | tools-and-protocols | 31 | ~43h | 43.2h | 11 |
| 14 | agent-engineering | 54 | ~55h | 56.7h | 13 |
| 15 | autonomous-systems | 22 | ~20h | 20.0h | 14 |
| 16 | multi-agent-and-swarms | 25 | ~28h | 30.5h | 15 |
| 17 | infrastructure-and-production | 28 | ~32h | 29.2h | 14 |
| 18 | ethics-safety-alignment | 30 | ~31h | 31.2h | 15 |
| 19 | capstone-projects | 85 | ~620h | 627.0h | 16·17·18 |
| | **합** | **523** | ~1,128h | **1,168.75h** | |

- **"342시간"의 정체(추정)**: ROADMAP phase 0~13 시간 합이 정확히 342다 — phase 14 이후가 추가되기 전 값이 README에 남은 것으로 추정(depth 1이라 이력 미확인). `scripts/test_translate_workflow.py:121`은 번역 README에 "342"가 있는지 assert해 낡은 수치를 고정한다.
- 번호에 빈칸이 있다(phase 08: 14 다음 19, phase 19: 폴더 85개인데 번호는 87까지).

### 2.3 산출물·코드·퀴즈

| 항목 | 값 | 비교 대상 주장 |
|---|---|---|
| `outputs/`에 파일이 있는 레슨 | 459/523 | README "Every lesson ships a reusable artifact" |
| 산출물 종류 | md 508(skill 417·prompt 99·agent 15 등), json 34, jsonl 6, py 9, sh 1 | "a prompt, a skill, an agent, an MCP server" |
| MCP 서버 산출물 | 0(`outputs/mcp-servers/`는 `.gitkeep`뿐, mcp 이름 13개는 모두 `skill-mcp-*.md` 문서) | 위와 같음 |
| 레슨 코드 언어(파일 수) | py 645, ts 129, jl 20, rs 10 | "Python, TypeScript, Rust, Julia" |
| `code/tests/`가 있는 레슨 | 84/523 | AGENTS.md "5+ unit tests minimum" |
| `notebook/` 폴더 / `.ipynb` | 295 / 0 | 템플릿 `notebook/lesson.ipynb` |
| `quiz.json` 레슨 · 문항 | 373 · 2,237. 6문항 규칙 준수 116개 | AGENTS.md "Exactly 6 questions" |
| 정답이 가장 긴 보기 | **89.9%**(1.25배 이상만 83.8%) | `check_quiz_bias.py` 기준선 0.84 |

---

## 3. 레슨 형식 분석

### 3.1 템플릿
- 머리: 모토, `**Type:** Build | Learn`, `**Languages:**`, `**Prerequisites:**`, `**Time:**`.
- 절: The Problem → The Concept → Build It → Use It → Ship It → Exercises(쉬움·중간·어려움) → Key Terms(표: Term | What people say | What it actually means) → Further Reading(링크 + 왜 읽을 가치가 있나). AGENTS.md는 Learning Objectives를 더한다.
- 절이 실제로 있는 레슨 수: Exercises 486, Further Reading 477, Key Terms 474, Use It 472, Ship It 444, The Problem 439, The Concept 433, **Build It 365**, Learning Objectives 357.

### 3.2 실제 레슨 표본
- **01-09 information-theory**(Learn, ~60분): 정보량 → 엔트로피 → 교차 엔트로피 → KL → 상호정보 → 레이블 스무딩 → perplexity. Build는 stdlib, Use는 NumPy. 장애 서술 없음. 우리 math/14(압축·CRC 중심)보다 손실 함수 쪽이 충실하다.
- **11-06 rag**(Build, ~90분): 4단계 그림, 파인튜닝 vs RAG 표, 임베딩·벡터 DB 표, "Real Numbers"(출처 없음). Build는 TF-IDF·코사인 전수 검색·**흉내 낸 생성**. Ship은 프롬프트·스킬 문서.
- **14-01 agent-loop + 13-06 mcp-fundamentals**: ReAct → 다섯 재료(메시지 버퍼·도구 레지스트리·종료 조건·턴 예산·관측 포매터) → 함정. MCP 레슨은 2026-07-28 무상태 모델을 요청 생애 9단계로 정리하고, 연습문제가 "버전을 바꿔 -32022 확인" 같은 **실행 예측형**이다(우리 "예측" 질문과 닮음).

### 3.3 우리 leaf와 비교

| 관점 | AIEFS | 우리 |
|---|---|---|
| 파일 | `docs/en.md` + 코드 + 산출물 + 퀴즈 JSON | 1-question·2-summary·3-answer·metadata |
| 장애 | 없음(일부 pitfalls) | 필수(현상 → 보이는 형태 → 원인 → 대처) |
| 근거 위치 | 끝 목록, 본문 수치 대부분 출처 없음 | 주장 옆 출처, 확인 못 하면 `[?]`, 실험 환경·버전 |
| 실증 | 학습자가 돌리는 장난감 코드, 출력은 문서에 없음 | 집필자가 돌린 **실제 출력** |
| 검수 | 구조 감사(CI) + 기여자 리뷰 | 사실 점검 → 2차 리뷰 → 웹 교차 표본 |

---

## 4. 품질 관찰

### 4.1 사실 표본 점검 (7편, 주장 15개)

| # | 레슨 | 주장 | 1차 출처 대조 | 판정 |
|---|---|---|---|---|
| 1 | 01-09 | 편향 동전 0.08bit, 1 nat = 1.4427bit 등 | 계산 | 일치 |
| 2 | 01-09 | "GPT-2 perplexity ~30 on common benchmarks" | GPT-2 논문 Table 3: 데이터셋별 8.63~42.16 | 모호 |
| 3 | 01-09 | 레이블 스무딩 식 | 표준 형태와 둘째 항 표기 다름 | 표기 부정확 |
| 4 | 11-06 | "256-512 token chunks … Anthropic's RAG guidelines recommend this range" | Anthropic "Contextual Retrieval"에 수치 권고 없음 | **근거 불일치** |
| 5 | 11-06 | "RAG wins every time" | — | 출처 없는 과잉 일반화 |
| 6 | 14-01 | ReAct ALFWorld +34, WebShop +10 | arXiv:2210.03629 초록 | 일치 |
| 7 | 14-01 | "Most 2026 agents run 40–400 steps" | 출처 없음 | 확인 불가 |
| 8 | 14-01 산출물 | "point to Lesson 09 (permissions + sandboxing)" | phase 14의 09는 mem0 메모리 | **교차 참조 오류** |
| 9 | 13-06 | 2026-07-28 무상태·`_meta`·`-32022` 등 | MCP changelog에 명시 | 일치(`server/discover` cacheable은 미확인) |
| 10 | 17-08 | TRT-LLM 기준값 TTFT 162ms·TPOT 7.33ms "NVIDIA reference" | 인용 페이지에 해당 수치 없음, LLMPerf는 2025-12 archived | 출처 확인 불가 |
| 11 | 17-08 | 평균 9ms, P99 65ms | 상위 1%가 모두 60ms라 P99 = 60ms | 내부 불일치 |
| 12 | 07-12 | KV 캐시와 FlashAttention "both from Dao et al." | FlashAttention 초록에 KV 캐시 없음 | **오류** |
| 13 | 07-12 | 7B KV: 토큰당 16KB, 32K에 512MB | 헤드 32를 곱하면 토큰당 512KiB, 32K에 16GiB | **32배 과소** |
| 14 | 16-14 | "CP-WBFT +85.71% BFT improvement" | arXiv:2511.10400: "85.7% fault rate" | **오독** |
| 15 | 16-14 | "Can AI Agents Agree?" 불일치 30% 초과 등 | 초록에 수치 없음, 강조점 다름 | 미확인 |

**종합.** 명세를 따라가는 레슨(MCP)과 고전 논문 인용(ReAct)은 정확했지만, 직접 계산한 곳과 최신 논문·벤더 수치를 옮긴 곳에서 오류·근거 없는 수치가 나왔다. 표본 7편 중 4편에 명확한 오류나 근거 불일치. 표본이 작아 일반화할 수는 없지만 **링크할 레슨은 편마다 골라야 한다**.

### 4.2 자동 생성·기계 번역 흔적
- 퀴즈 정답 최장 89.9%(정답만 자세히 쓰는 패턴). 저장소는 위치 셔플과 "더 나빠지지 않게" 검사만 둔다.
- 모토 → "2026 shift" → 다섯 개 목록 → "Hard rejects/Refusal rules" 산출물 구조가 phase를 가리지 않고 반복된다.
- 최근 100커밋 중 3개에 AI 공저 표기, 27개는 봇 자동 동기화.
- 레슨은 NLLB-200 기계 번역, README만 사람 번역. README "84% … 18%" 수치는 출처 없음.

### 4.3 자기 규칙과 실제의 드리프트

| 규칙 (출처) | 실제 |
|---|---|
| "Exactly 6 questions" (AGENTS.md) | 116/373 — 검사기는 문항 수를 보지 않음 |
| "code/tests/ 5+ unit tests" | 84/523 |
| "Every fenced code block needs a language tag" | 태그 없는 블록 883개 |
| "Mermaid or SVG only … No ASCII"(AGENTS) vs "Use ASCII diagrams"(TEMPLATE) | 문서끼리 충돌 |
| glossary "60+ terms", "20 misconceptions" | 실제 250·21 |
| CI 레슨 테스트 | numpy·torch 의존 테스트를 설치 없이 "skipped" — 녹색이어도 미검증 |

### 4.4 유지보수 (GitHub API, 2026-10-04)
- 생성 2026-03-18, 마지막 push 2026-10-02, 커밋 1,813, stars 63,249, forks 10,813, 기여자 22명.
- 최근 100커밋: 소유자 64, 봇 27, 나머지 각 1~2 — **사실상 1인 + 봇**. 변경이 빨라 수치·링크가 쉽게 낡는다(§4.3).

---

## 5. 우리에게 적용

### 5(a) 형식·방법론

| 후보 | 판정 | 이유 |
|---|---|---|
| Key Terms "흔히 하는 말 / 실제 뜻" | **가져올 만함(변형)** | 용어 풀이(`  - *용어*: 설명`)에 "흔한 오해" 한 줄. 새 절은 만들지 않음(7절 골격 유지) |
| 학습 경로의 완료 증거·범위 밖 | **가져올 만함** | 커리큘럼 읽기 경로에 "다 읽으면 설명·진단할 수 있는 것"과 "다루지 않는 것". 범위 선언이라 사실 점검 부담 없음 |
| 자기 규칙을 세는 검사기 | **이미 있음 + 교훈** | `check_new.py`·생성기가 있다. 교훈: 규칙마다 검사 항목이 있는지 **대조표**를 둔다 |
| 퀴즈 정답 길이 편향 검사 | 부적용(참고) | 우리 질문은 서술형. 객관식을 만들 때만 |
| Build It → Use It | 부분 채택 | 출력 없는 장난감 코드는 버리고, "직접 짠 작은 판 vs 라이브러리 결과 대조"를 실험 설계 패턴으로 |
| Ship It 산출물 | 버림 | "cs = 지식 본문만"과 충돌 — 실행물은 project/·lab/·practice/ |
| 퀴즈 pre/check/post, 튜터 스킬 | 버림 | 질문·정답 분리와 복습 기록으로 대응 |
| 레슨 기계 번역 | 버림 | 한국어 원문이 정본. 사실 점검을 무력화 |

### 5(b) 내용 갭 — 새 영역 단원안 (초안)

**갭.** 커리큘럼 §1~§18a에 AI/ML 영역이 없다. 접점은 math/13(🔧 "임베딩 ANN"), math/14, data-structure/24·database/46(BM25), data-analysis/22(경사 하강)뿐이고, **벡터 인덱스(HNSW 등) leaf는 어디에도 없다.**

**방향.** Java 백엔드 독자에게는 AIEFS(수학 → 훈련 → 응용)와 반대로 **LLM을 외부 의존성으로 호출하고 서빙 비용·지연을 읽고 검색·평가·보안을 설계하는 것**부터. 원리 leaf는 최소로. 비전·음성·RL·이미지 생성·정렬 연구는 범위 밖. 임시 이름 `ai-engineering/`(이름·번호는 사용자 결정).

| # | slug | 요지 | 선행 | 우리 기존 노트 연결 | 등급(제안) |
|---|---|---|---|---|---|
| 01 | ml-in-one-page | 손실 최소화, 학습·검증·테스트 분리, 과적합·누설 | math/07, data-analysis/22 | data-analysis/22·02 | 필수 |
| 02 | gradient-descent-and-backprop | 경사 하강·연쇄 법칙·자동 미분 | 01, math/13 | math/06·13 | 권장 |
| 03 | cross-entropy-and-perplexity | 교차 엔트로피 = NLL, perplexity 한계 | 01, math/14 | math/14 | 권장 |
| 04 | tokenization-and-token-cost | BPE, 한국어 토큰 비용·문맥 한도 | 03 | data-structure/24·database/46 | 필수 |
| 05 | embeddings-and-similarity | 임베딩·코사인·정규화, 모델 교체 = 공간 교체 | 04, math/13 | math/13 | 필수 |
| 06 | transformer-and-attention | 셀프 어텐션·인과 마스크(동작 수준) | 05 | architecture/12 | 권장 |
| 07 | decoding-and-nondeterminism | temperature·top-p, 같은 입력 다른 출력 | 06 | math/12, testing/09 | 필수 |
| 08 | kv-cache-and-inference-memory | prefill vs decode, KV 크기 계산, GQA | 06 | architecture/12 | 권장 |
| 09 | inference-serving-and-batching | 연속 배칭·페이지드 KV·큐잉 | 08, math/10 | math/10, reliability/40 | 심화 |
| 10 | inference-latency-metrics | TTFT·TPOT·goodput, 도구별 정의 차이 | 09 | data-analysis/05, reliability/02·34 | 필수 |
| 11 | llm-api-client-contract | SSE 스트리밍, 타임아웃·재시도·429·토큰 한도·비용 상한 | 04, 07 | network/38, reliability/05·06·07, api-design/14 | 필수 |
| 12 | prompt-and-semantic-caching | 프리픽스 캐시 vs 의미 캐시, 오적중 | 05, 11 | database/30·31·49, reliability/29 | 권장 |
| 13 | model-routing-and-fallback | 게이트웨이·라우팅·폴백·서킷 | 11 | api-design/19, reliability/10·28 | 권장 |
| 14 | structured-output-and-tool-calling | JSON 스키마 강제, 검증 실패 처리, 도구 계약 | 07, 11 | api-design/08, software-design/23 | 필수 |
| 15 | rag-pipeline | 청킹·임베딩·검색·프롬프트 조립·출처 표기 | 05, 14 | database/46 | 필수 |
| 16 | vector-index-ann | 전수 vs HNSW·IVF, recall–지연, pgvector | 15 | **신설 필요**, database/08(대비) | 필수 |
| 17 | hybrid-search-and-reranking | BM25 + 밀집, RRF, 재순위 | 15, 16 | database/46, data-structure/24 | 권장 |
| 18 | index-freshness-and-reembedding | 재임베딩·재색인·지연 감지 | 15 | database/48, data-engineering/08 | 권장 |
| 19 | llm-evaluation | 평가셋, LLM-as-judge 편향, 신뢰구간, 회귀 게이트 | 07, 15 | data-analysis/08·09·11·14, testing/19 | 필수 |
| 20 | agent-loop-and-tool-safety | 턴 예산·종료 조건, 부작용 도구의 멱등·사람 확인 | 14 | reliability/13·32, api-design/05 | 필수 |
| 21 | mcp-protocol | JSON-RPC, 2026-07-28 무상태, 버전·권한 순서 | 14 | api-design/01·16 | 권장 |
| 22 | prompt-injection-and-llm-security | 신뢰 경계, 간접 인젝션, 권한 최소화, PII 유출 | 15, 20 | security/18·25·27 | 필수 |
| 23 | llm-observability-and-cost | OTel GenAI 추적, 토큰 비용, 품질 지표 | 10, 19 | reliability/16·17 | 권장 |
| 24 | fine-tuning-vs-rag-decision | LoRA 개념, 선택 기준 | 15, 19 | engineering-practice/13 | 심화 |
| 25 | ai-symptom-index | 역색인 | 01~24 | (영역 마감) | 필수 |
| 26 | ai-incidents | 공개 사고 → leaf 매핑 | 25 | — | 권장 |

- **중복**: 엔트로피(math/14), 코사인(math/13), 경사 하강(data-analysis/22), BM25(database/46), 백분위(data-analysis/05) — 단일 출처는 기존 leaf에 두고 링크만.
- **기초로 그대로 쓰이는 곳**: LLM 호출을 "느리고 비결정적이고 비싼 외부 의존성"으로 보면 reliability와 api-design이 절반을 덮는다.
- **백엔드 우선순위**: 11 → 14 → 10 → 15·16 → 19 → 20·22.

### 5(c) 참고 링크 후보

- 라이선스 MIT("Copyright (c) 2026 Rohit Ghumare") — 링크는 조건 없음, 상당 부분 복사 시 고지·허가 문구 필요. 우리 근거 칸에는 교재·RFC·공식 문서만 두므로 AIEFS는 **"실습 참고" 링크로만**, 근거는 AIEFS가 인용한 1차 출처를 직접 확인해 적는다.

| 레슨 | 쓸 곳 | 메모 |
|---|---|---|
| 13-06 mcp-fundamentals | mcp-protocol | 명세와 일치 |
| 14-01 agent-loop | agent-loop 실습 참고 | "40–400 steps" 인용 금지, Lesson 09 참조 오류 |
| 01-09 information-theory | math/14 실습 참고 | 레이블 스무딩 식·GPT-2 perplexity 인용 금지 |
| `learning-paths/building-and-deploying-ai-applications.json` | 순서 설계 참고 | 단원안 11~23과 거의 같은 흐름 |
| **링크 금지** | 07-12(KV 계산 오류), 16-14(BFT 오독), 11-06의 "Real Numbers"·"Anthropic 권고" 절, 17-08 기준 수치 | §4.1 |

---

## 6. 권장안 (우선순위순)

1. **AI 영역은 지금 쓰지 않고 NEXT 후보로 등록한다.** 공부 우선순위가 기본기 → 도메인 → api/ops이고, 기존 영역에 미작성 leaf가 많다. 단원안은 reliability·api-design에 크게 기대므로 그 검수 뒤에 여는 편이 링크가 실재한다. 등록 시 §5b 표와 백엔드 우선 순서를 명시.
2. **ANN 벡터 인덱스 leaf 하나는 먼저 채울 후보.** math/13 🔧 칸이 가리키는데 받아 줄 leaf가 없다. 단 로컬에 pgvector 이미지가 없어(2026-10-04 확인) "새 이미지 받기 금지" 규칙과 충돌 — 착수 전 사용자 결정 필요(이미지 허용 또는 Java 단일 파일 HNSW 구현 실험).
3. **형식은 작게 두 가지만**: (a) 용어 풀이에 "흔한 오해" 한 줄(선택), (b) **문서 규칙 ↔ 검사기 항목 대조표** — `cs/README.md` 작성 규칙과 `check_new.py`를 1회 대조. 산출물 중심 설계·자동 생성 퀴즈·기계 번역은 가져오지 않는다.

---

## 7. 확인 못 한 것

- depth 1이라 커밋 이력 없음 — "342h = phase 0~13 합의 잔재"는 수치 일치에 근거한 추정.
- 523편 중 7편만 사실 점검. 퀴즈는 길이 편향만 셌고 정답의 옳고 그름은 미점검.
- "Can AI Agents Agree?" 본문, Anthropic의 다른 문서, NVIDIA의 다른 문서, MCP `server/discover` cacheable 여부, 사이트·책·번역 브랜치 품질, projects/ 48개 내용, README "84%/18%" 원출처.
- 우리 영역별 미작성 leaf 수는 집계하지 않음(영역 표 생성기로 확인 가능).

## 근거

- [MCP 2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) · [ReAct arXiv:2210.03629](https://arxiv.org/abs/2210.03629) · [FlashAttention arXiv:2205.14135](https://arxiv.org/abs/2205.14135) · [arXiv:2603.01213](https://arxiv.org/abs/2603.01213) · [CP-WBFT arXiv:2511.10400](https://arxiv.org/abs/2511.10400) · [GPT-2 paper PDF](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) · [NVIDIA NIM LLM benchmarking metrics](https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html) · [ray-project/llmperf](https://github.com/ray-project/llmperf) · [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
