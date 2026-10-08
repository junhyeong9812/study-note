# 요구사항 명세서 — rules-checker

> 작성일: 2026-10-08 · 작업 폴더: `docs/plans/2026-10-08/rules-checker/` · 브랜치: `docs/rules-checker`(main 0c49c2e0). 근거: `docs/plans/2026-10-05/engineering-practice-writing/rules-vs-checker.md`(대조표 32행·제안 §4), NEXT N0-p.

## 0. 요구사항 원문 (인터뷰)

- 원문: "2번과 3번 진행하고 mysql은 다른 세션으로" — 2번 = 작성 규칙·검사기 정비.
- Q/A (2026-10-08): 범위 **전부** — ① cs/README 작성 규칙 정본화(7절·브리핑 규칙) ② 위반 거의 0인 규칙을 error로(코드 언어 태그·제목 형식·metadata 날짜·생성 문서 `--check`) ③ warning 소수(장애 3~6·핵심 문장 3~6·'항상/반드시/절대') ④ 고정 위치 + 자동 실행 · 위치·자동 = **`scripts/` + GitHub Actions**(push·PR 때 전체 검사 + 생성 문서 --check, 실패는 빨간불 — 차단 아님).

## 1. 목표·대상 (필수)

- **T1 이동**: `docs/plans/2026-09-30/network-writing/check_new.py` → `scripts/notes/check_notes.py`, `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py` → `scripts/notes/gen_area_readme.py`(git mv). 인자 없이 `--all`이면 `cs/` 아래 `1-question.md`가 있는 폴더 전부. 생성 문서 머리의 생성기 경로가 바뀌므로 재생성.
- **T2 error 추가**: (a) 여는 코드 펜스 언어 태그 필수(기존 위반 수정 — 내용 불변, 태그만) (b) 제목 형식 `# <영역 경로>/<폴더명> — <질문|정리|정답>…`(측정 후 규칙 확정, 기존 위반은 제목 줄만 수정) (c) metadata 날짜 형식·단계 일관성(단계=검수면 검수 날짜 있음 등) (d) 생성기 `--check`(쓰기 없이 diff만, 다르면 exit 1) (e) 생성기의 metadata 없음 폴백을 실패로.
- **T3 warning**: 장애 절 항목 3~6 · 핵심 문장 불릿 3~6 · 펜스 밖 '항상·반드시·절대' — 출력만, exit code에 영향 없음. 옛 형식(`형식 | 과제 이식`·`원고 이관`)은 warning 제외.
- **T4 CI**: `.github/workflows/notes-check.yml`(push·pull_request, 비밀값 없음, python3만).
- **T5 정본화**: `cs/README.md` 「작성 규칙」을 7절 골격 + 브리핑에만 있던 형식 규칙(대조표 #9·10·14·16·18·19·20·21·30·31) + 검사기 위치·error/warning 구분 + 옛 형식 면제 규칙으로 갱신.

## 2. 경계·불변식 (필수)

- **I1** 이동 후 기존 규칙 판정 불변: 756편 기준 결과가 이동 전과 같다(새 error 추가 전 비교), 새 error는 기존 위반을 고친 뒤 756 PASS.
- **I2** 노트 수정은 형식 줄(펜스 언어 태그·제목 줄·metadata)만, 본문 의미 불변.
- **I3** warning은 exit code 0 유지. CI는 secret·네트워크 쓰기 없음, 기존 `sync.yml` 불변.
- **I4** 생성 문서는 생성기로만 — 머리 경로 변경도 재생성으로.

## 3. 기준소스 (필수)

- 대조표 `rules-vs-checker.md`, 현재 검사기·생성기 코드, `cs/README.md`, 최근 브리핑(`docs/plans/2026-10-08/data-analysis-writing/briefing.md`), `.github/workflows/sync.yml`

## 4. 금지영역 (필수)

- 노트 본문 문장, 커리큘럼 본문, `sync.yml`, 저장소 루트 파일(새 디렉토리 `scripts/`는 허용 — 사용자 선택), 사람 판단 규칙의 기계화(#1·2·13·15'모든'·17·21·22·23)

## 5. 검증 방법 (필수)

- 이동 전후 756편 판정 diff 0 · 새 error 반증(일부러 위반 넣어 FAIL 확인 후 복원) · warning이 exit 0 · `--check`가 수기 수정을 잡고 정상 시 0 · CI yml 문법(`python3 -c yaml` 불가 시 actionlint 대신 눈 검토)·로컬에서 같은 명령 실행 · **codex(high) 1패스 리뷰**(검사기·CI diff — stakes 중간) · README 셀프 리뷰

## 6. stakes (필수)

- **중간** — 검사 도구·CI(모든 이후 집필의 관문), 노트 형식 줄 수정. 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 대조표(10-05, 387편 표본) 이후 노트가 늘었어도 새 error 대상 위반은 소수다 — 착수 직후 756편 재측정으로 확인.

## 9. task 분해

| task | 목표 | 담당 |
|---|---|---|
| 01 | T1~T4 구현 + 측정 + 기존 위반 수정 | Opus 워커 |
| 02 | T5 README 초안 | Opus 워커(01과 병렬) |
| 03 | codex 리뷰 → 반영 · 검증 · 커밋 | 메인 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-08)
- [x] auto
