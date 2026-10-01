# 요구사항 명세서 — os-writing

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 영역 OS 명세부터 작성해보자"
- Q/A (2026-09-30)
  - 범위: **미작성 30 + 원고 7편 보강** → 보강 방식: **새 leaf 폴더 생성**(원고는 그대로, 링크로 이어받음) · 18 semaphores(기존 Claude 초안): **같은 방식으로 보강**
  - 검증: **네트워크와 같게** — 집필 → Opus 전수 사실 점검 → 2차 리뷰 → 판정·반영 → 노트 간 일관성 재점검
  - 2차 리뷰어: **codex 우선, 막히면 Opus 적대 리뷰**(대체 시 log 기록)
  - 로컬 재현: **허용** — scratchpad에서 작은 C 프로그램 컴파일·실행, strace·/proc 조회
  - 네트워크에서 이미 정한 것(재질문 안 함): 집필 모델 Opus, `cs/<area>/NN-slug/` 3파일, 통일 골격 7절, 코드 Java·JS·TS(저수준 C), "Claude 초안" 표기

## 1. 목표·대상 (필수)

- `cs/os/NN-slug/{1-question,2-summary,3-answer}.md` **38편**
  - 미작성 30: 01·02·03·05·06·12·13·14·16·17·19·20·21~36(27 포함)·37·38
  - 원고 보강 7: 04 process-and-lifecycle · 07 threads-and-context-switch · 08 cpu-scheduling · 09 address-space · 10 paging-and-tlb · 11 heap-allocation · 15 race-conditions — 원고(`cs/foundations/process-thread`, `cs/foundations/memory-management`)가 다룬 부분은 링크로 이어받고, 빈 곳(시스템 콜·리눅스 구현·장애·질문/정답)을 채운다.
  - 기존 초안 보강 1: 18 semaphores — `cs/systems/semaphore` 초안을 이어받아 새 leaf로.
- 영역 표 `cs/os/README.md` 재생성: 38 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 골격**: 2-summary 최상위 헤딩 7절 순서(해결하는 문제 → 동작·원리 → 쓰이는 자료구조·알고리즘 → 적용 — 풀어나가는 법 → 장애 시나리오와 대처 → 핵심 문장 → 관련 주제·근거). Q/A 번호 일치, 6~10개.
- **I2 근거**: RFC 대신 man-pages·커널 문서·커널/glibc 소스·OSTEP·CS:APP 3판·POSIX로 확인한 것만 사실로 쓴다. 확인 못 한 것은 `[?]`. 지어낸 수치·API·사례 0. **man 페이지가 최신 커널보다 뒤처질 수 있다**(네트워크 실측) — 기본값·동작은 커널 문서·소스와 대조하고 버전 조건을 붙인다.
- **I3 커리큘럼 일치**: curriculum.md §5 각 행의 요지·⚠·🔧·📚를 모두 다룬다. 선행 주제는 링크.
- **I4 기존 보존**: `cs/foundations/process-thread`·`memory-management`, `cs/systems/semaphore`와 다른 영역 노트는 **수정하지 않는다**(링크만). 새 leaf가 원고 내용을 되풀이하지 않고 이어받는다.
- **I5 링크·트리**: 노트 신규 깨진 링크 0, 리프 폴더에 md만.
- **I6 로컬 재현 안전**: 실행은 scratchpad 안에서만, root·sysctl 쓰기·시스템 설정 변경 금지. 노트에 넣는 출력은 "(예시, 리눅스 7.0)" 표기.

## 3. 기준소스 (필수)

- `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §5(운영체제) 각 leaf 행, `cs/os/README.md`
- OSTEP(장 번호 확인), CS:APP 3판 7~12장, Linux man-pages(signal(7)·epoll(7)·fsync(2) 등), kernel.org 문서, 커널·glibc 소스, POSIX
- 원고: `cs/foundations/process-thread/README.md`, `cs/foundations/memory-management/README.md`, `cs/systems/semaphore/`

## 4. 금지영역 (필수)

- OS 밖 영역 노트, 원고·기존 초안(I4), 커리큘럼 본문(필요하면 NEXT에 기록 — 네트워크 오기 3건은 별도 작업 N0-e)
- 생성 문서(`cs/<area>/README.md`) 수기 수정 — 생성기 재실행으로만
- 로컬 시스템 설정 변경(I6)

## 5. 검증 방법 (필수)

- **V1** `check_new.py`(네트워크 것 재사용) — 7절 순서·Q/A 일치·6~10·빈 곳 0·새 링크 실존·초안 표기
- **V2** Opus 전수 사실 점검(편별, 1차 출처·로컬 재현)
- **V3** 2차 리뷰: codex(high, stdin 인라인) 전수 — 한도 시 Opus 적대 리뷰 대체 → Opus 판정 워커가 1차 출처 재확인 후 채택/기각
- **V4** 노트 간 공통 사실 일관성 재점검(errno·시그널 번호·기본값·커널 버전 조건)
- **V5** 웹 교차 표본 20건 이상, linkcheck 노트 신규 깨짐 0, 영역 README 재생성

## 6. stakes (필수)

- 판정: **중간**
- 근거: 새 학습 자료 38편, 사실 오류 위험이 크다(네트워크에서 1차 점검 뒤에도 편당 수 건 잔존). 코드·데이터는 바꾸지 않고 되돌리기 쉽다.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 원고 7편·18 초안을 수정하지 않고도 새 leaf가 "이어받기 + 빈 곳 채우기"로 중복 없이 완결된 노트가 된다 — 첫 배치(04·07 포함)에서 확인.
- **A2**: 로컬 재현(C 컴파일·strace)이 사용자 권한 안에서 된다 — 착수 직후 스모크(`cc`·`strace` 존재, userns 불가는 이미 확인됨).

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(네트워크 briefing + OS 교훈·원고 이어받기 규칙·로컬 재현 규칙), 생성기에 "leaf 폴더 우선" 반영, 스모크(A2) | 브리핑·스모크 기록 |
| 02 | 집필(Opus 병렬, 5편 안팎/워커) + 종합 2편(37·38)은 후속 | 38 PASS |
| 03 | Opus 전수 사실 점검 | 편별 packet |
| 04 | 2차 리뷰(codex/대체) → 판정·반영 → 일관성 재점검 → 웹 표본 | V3~V5 |
| 05 | 링크 전환·README 재생성·커밋·(사용자 확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변 6건(2026-09-30)
- [x] auto
