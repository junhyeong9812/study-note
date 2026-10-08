# 요구사항 명세서 — ai-engineering-writing

> 작성일: 2026-10-08 · 작업 폴더: `docs/plans/2026-10-08/ai-engineering-writing/` · 브랜치: `docs/ai-engineering-writing`(docs/rules-checker 432fd4b5에서). 근거: `docs/plans/2026-10-04/aie-analysis/report.md` §5(b)·5(c)·6, NEXT N0-q.

## 0. 요구사항 원문 (인터뷰)

- 원문: "2번과 3번 진행하고 mysql은 다른 세션으로" — 3번 = AI 엔지니어링 영역 후보.
- Q/A (2026-10-08): **커리큘럼 등록 + 26편 집필**(단원안 26행, 앞 영역과 같은 파이프라인: 실험 → 사실 점검+실험 재실행 → codex(high) 2차 → 판정(출처 직접 열람) → 정합 → 웹 교차 표본) · 벡터 인덱스 실험 **pgvector 이미지 받기 허용**(`pgvector/pgvector:pg17`, 받음). 이전 합의 유지: 합의 auto, 동시 서브에이전트 ≤5, push는 끝에 한 번 확인.

## 1. 목표·대상 (필수)

- **T1 커리큘럼**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`에 `## 22. AI 엔지니어링 (\`ai-engineering/\`) — 신설` 절(머리말·뼈대 출처·권장 순서·소절 표 26행: slug·요지·선행·⚠·🔧·📚·등급·기존). §20 leaf 통계·§0의 영역 수 등 커리큘럼 안 집계 갱신. 생성기로 `cs/ai-engineering/README.md` 생성. `cs/README.md` 영역 목록 19 → 20.
- **T2 집필**: `cs/ai-engineering/NN-slug/{1-question,2-summary,3-answer,metadata}.md` 26편(단원안 01~26, 종합 25·26은 마지막). 백엔드 독자 기준 — LLM을 외부 의존성으로 호출·서빙 비용·지연·검색·평가·보안 설계 중심, 원리 leaf는 최소.
- **T3 정합**: 기존 노트(math/13 🔧 "임베딩 ANN" 등)가 이 영역을 가리켜야 하는 곳은 링크만 추가/교정.

## 2. 경계·불변식 (필수)

- **I1 형식**: `cs/README.md` 작성 규칙(10-08 정본) — `python3 scripts/notes/check_notes.py <폴더>` PASS(warning은 보고), 생성기 `--check` 0.
- **I2 근거**: 1차 출처만 — 논문(Vaswani 2017, Sennrich 2016 BPE, Holtzman 2019 top-p, Kwon 2023 PagedAttention, Yu 2022 Orca, Malkov–Yashunin HNSW, Lewis 2020 RAG, Cormack 2009 RRF, Hu 2021 LoRA, Zheng 2023 LLM-as-judge, Ainslie 2023 GQA 등), 공식 문서(pgvector README, OpenTelemetry GenAI semantic conventions, MCP 명세, OWASP Top 10 for LLM Applications, JSON Schema, 각 LLM API의 스트리밍·오류·한도 문서), 교재(Goodfellow 외 『Deep Learning』, Jurafsky–Martin SLP3 초안). AIEFS는 "실습 참고" 링크로만(report §5c 링크 금지 목록 준수). 기억으로 쓴 절·장·연도·수치에는 `[?]`. 빠르게 바뀌는 사실(API 동작·가격·명세 버전)은 확인 날짜 표기.
- **I3 중복 금지**: 엔트로피(math/14)·코사인(math/13)·경사 하강(data-analysis/22)·BM25(database/46)·백분위(data-analysis/05)·큐잉(math/10)은 단일 출처 링크.
- **I4 기존 보존**: 다른 영역 노트는 링크 추가/교정만(문장 의미 불변).
- **I5 재현 안전**: 전용 `sn-ai-w<NN>-*`(`--rm --pull never --cpus=2`, python/java/node는 `--network none -u $(id -u):$(id -g) -e HOME=/tmp`), 이미지는 있는 것만(pgvector/pgvector:pg17·postgres:17·python:3.12-slim·eclipse-temurin:21-jdk·node:22-*), pull·build·rmi·prune 금지, `--rm`만. 외부 LLM API 호출 금지(네트워크·비용·비밀값) — 모형 서버·시뮬레이션으로 보인다. 패키지 설치 금지(numpy 등 없음 — 표준 라이브러리). 프롬프트 인젝션은 **방어 원리·자기 로컬 모형까지**(공격 문자열 수집·무기화 금지). 개인정보 금지, 저장소 루트 파일 금지.
- **I6 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상(종합 선택), 시드·반복 수 기록. 예: 미니 BPE 토큰 수(한/영), 코사인·정규화, 어텐션 소형 계산, temperature·top-p 샘플링 분포, KV 캐시 크기 계산, 연속 배칭 큐 시뮬레이션, TTFT·TPOT 측정(로컬 SSE 모형 서버), 재시도·429·타임아웃 클라이언트, 의미 캐시 오적중, JSON 스키마 검증 실패 처리, RAG 소형 파이프라인(TF-IDF 임베딩), **pgvector 전수 vs HNSW·IVFFlat recall–지연**, RRF, 재임베딩 혼합 공간 오류, 평가 신뢰구간·judge 위치 편향 모형, 에이전트 턴 예산·멱등 도구, MCP JSON-RPC 로컬, 인젝션 신뢰 경계 모형.
- **I7 동시성**: 서브에이전트 ≤5.

## 3. 기준소스 (필수)

- report.md §5(b) 단원안·§5(c)·§4.1(AIEFS 오류 목록), I2 출처, 관련 기존 노트(math/10·12·13·14, data-analysis/05·08·09·11·14·22, database/08·30·31·46·48·49, data-structure/24, reliability/02·05·06·07·10·13·16·17·28·29·32·34·40, api-design/01·05·08·14·16·19, security/18·25·27, testing/09·19, network/38, architecture/12, software-design/23, data-engineering/08, engineering-practice/13)

## 4. 금지영역 (필수)

- 다른 영역 노트 본문(링크 추가/교정 제외), 검사기·생성기 코드(영역 추가에 필요한 최소 변경은 예외 — 로그 기록), 생성 문서 수기 수정, I5 금지 행위, 외부 LLM API 호출

## 5. 검증 방법 (필수)

- V1 check_notes PASS · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정(출처 직접 열람) · V4 정합(겹치는 영역 + 종합 색인은 leaf 판정 뒤 재대조) · V5 웹 교차 표본 50+, 링크 신규 깨짐 0, 생성기 --check 0, 정리 확인(sn-ai 컨테이너 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 26편, 빠르게 바뀌는 분야라 사실·버전 오류 위험이 큼. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 실제 LLM 없이(외부 API 금지·로컬 모델 없음) 표준 라이브러리 모형·시뮬레이션과 pgvector로 각 편의 핵심 주장을 실행으로 보일 수 있다 — 모델 품질 자체에 관한 주장은 1차 출처 인용으로만.
- **A2**: WebSearch 한도 소진 가능 — 브리핑에 1차 출처 URL을 미리 넣고 curl로 연다.

## 9. task 분해

| task | 목표 | 담당 |
|---|---|---|
| 01 | 커리큘럼 §22 초안 + 1차 출처 URL 목록(확인) | Opus 워커 → 메인 검토 |
| 02 | 브리핑 3종(data-analysis판 이식 + AI 실험·출처) · 생성기 영역 추가 확인 · README 영역 20 | 메인 |
| 03 | 집필 Opus 5워커(5·5·5·5·4) + 종합 25·26 | 26 PASS |
| 04 | 사실 점검 + 실험 재실행 → codex 2차 → 판정 → 정합 → 웹 | V2~V5 |
| 05 | 영역 표·정리·커밋·(확인 후) push·log·NEXT·측정로그 | 메인 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-08)
- [x] auto
