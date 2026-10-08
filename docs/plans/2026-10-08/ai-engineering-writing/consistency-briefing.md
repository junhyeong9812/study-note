# 정합 브리핑 — AI 엔지니어링 26편 (2026-10-08)

> 모든 판정이 끝난 뒤 실행한다. 규칙 정본: `cs/README.md` 「작성 규칙」, 명세 I3·I4. 집필 규칙: 같은 폴더 `briefing.md`.

## A. 영역 안 (cs/ai-engineering/01~26)

1. 집필 시점에 형제 노트가 없어 **텍스트로만 적은 참조**를 실제 상대 링크로 바꾼다(예: 07·24의 `ai-engineering/14-…`·`26-…`, 15의 "14번"·"22번", 13의 26 링크 복원, W1 노트(01·02·03·06·08)의 04·05·07·09·10·12·15·17·19 언급). `grep -n "ai-engineering/[0-9][0-9]-\|[0-9][0-9]번" cs/ai-engineering/*/*.md`로 찾고, 링크는 실재 파일 기준.
2. 노트 간 수치·정의 모순 대조: KV 캐시 식·예시(08↔09↔10), TTFT/TPOT/ITL 정의(10↔11↔23), 캐시 단가 배수·TTL(12↔23), stop/finish reason 값(04↔11↔14↔20), 재시도·SDK 기본값(11↔13), OTel 이름(10↔23), MCP(20↔21), Lost in the Middle 연도 TACL 2024(06·15).
3. 25 색인의 `NN-k`·「…」 위치가 최종 leaf와 맞는지 다시 스크립트로 대조(A6가 이미 했으면 확인만).

## B. 커리큘럼 §22 (docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md) → 생성기 재실행

- 06행 📚 Liu 외 TACL **2024**.
- 05행 ⚠ "자른 뒤 재정규화 누락 → 코사인 순위 왜곡" → 내적(정규화 가정) 연산자를 쓸 때로 조건화.
- 09행 📚 KV 블록 공유 `[?]` 해소(vLLM §4.4 참조 카운트·copy-on-write), Sarathi-Serve 게재처 OSDI 2024.
- 11행 ⚠ "지출 한도 429" → Anthropic 사용 등급 월 상한 = 429(`rate_limit_error`, retry-after 없음, `error.details.error_code`) · 조직/워크스페이스 지출 한도 = 400.
- 26행 Moffatt v. Air Canada `[?]` 2개 해소(CRT 공식 결정 페이지, 2024-02-14).
- 03행 🔧 "log-sum-exp(math/15-numerical-stability)" — math/15에 log-sum-exp가 없다 → 🔧 칸을 "log-sum-exp(이 노트 — math/15는 수치 안정성 일반)"처럼 사실에 맞게.
- 그 밖에 노트 판정으로 커리큘럼 칸과 어긋나게 된 곳이 있으면 같은 방식으로. 표 셀 수 유지. 끝나면 `python3 scripts/notes/gen_area_readme.py` → `--check` 0.
- `sources.md`(같은 폴더): #23 TACL 2024, #53·#54 OTel 이동·개명(gen_ai.client.inference.*), #58 OpenAI 503 `server_is_overloaded`, Moffatt 확인됨으로 갱신.

## C. 영역 밖 링크 (I4 — 다른 영역 노트는 링크 한 줄 추가만, 문장 의미 불변)

- 각 대상 노트의 `## 관련 주제·근거` 절(옛 형식이면 그에 해당하는 관련 자료 목록)에 불릿 한 줄: `- 후속(AI 엔지니어링): [ai-engineering/NN-slug](상대경로/2-summary.md) — 한 구절 이유`. 이미 링크가 있으면 건너뛴다.
- 후보(집필·점검 packet에서 모음 — 실재 폴더 ls로 확인, 무리한 연결은 뺀다):
  - math/13 → 05·16 (§5 ANN "결정 보류" 자리 포함) · math/14 → 03 · math/15 → 03·07 · math/10 → 09
  - data-analysis/22 → 01·02 · data-analysis/05 → 10 · data-analysis/08·09 → 19
  - database/46 → 17·04 · database/48 → 18 · database/30·31·49 → 12
  - reliability/06·10 → 13 · reliability/07 → 11 · reliability/11 → 11 · reliability/13 → 20 · reliability/16·17 → 23 · reliability/29 → 12 · reliability/40 → 09
  - network/38 → 11 · testing/09 → 07 · security/18·19 → 22 · api-design/05 → 20 · api-design/07 → 21 · api-design/08 → 14 · software-design/23 → 14
  - os/10 → 09 · architecture/04 → 04 · architecture/11 → 08 · architecture/21 → 06 · algorithm/12-dfs → 02 · data-structure/32-inverted-index·12-skip-list → 16·17 · data-engineering/12 → 18
  - 종합: reliability·security·data-analysis의 symptom-index → 25, incidents → 26
- 수정한 영역 밖 파일마다 `git diff -U0 --word-diff=plain`으로 링크 한 줄 추가 외 변경 0 확인.

## D. 검증

- `python3 scripts/notes/check_notes.py --all` → 전부 PASS(WARN 수 보고) · `python3 scripts/notes/gen_area_readme.py --check` → 0.
- 반환: A·B·C 수정 목록(파일·무엇), 영역 밖 수정 파일 수·링크 수, 모순 대조 결과, 검사 결과.
