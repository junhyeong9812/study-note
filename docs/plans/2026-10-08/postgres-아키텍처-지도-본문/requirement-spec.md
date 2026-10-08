# 요구사항 명세서 (requirement-spec)

> 작성일: 2026-10-08 · 작업 폴더: `docs/plans/2026-10-08/postgres-아키텍처-지도-본문/` (워크트리 `~/project/study-note-wt-postgres`, 브랜치 `docs/postgres-architecture-body`, main 24dba712 기준)

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "병합하고 다음도 진행하자" — 다음 = MySQL 과 같은 방식의 PostgreSQL 지도 본문.
- Q/A: push = 지금(완료, 24dba712). 범위 = 흐름 13 + 구조 6 + pgvector. 후속 포함 = PG vacuum 행 문구 정정 · `opensource/index.md` 상태 갱신 · 대조 스크립트를 레포로.
- 앞선 합의 승계: 도식화(ASCII) 위주, ES 형식 통일, db-engine 대응은 일치 흐름에만, 동시 워커 최대 4개, 작성자와 다른 워커가 검증.

---

## 1. 목표·대상 (필수)

A. `opensource/postgres/architecture/`: 흐름 13편(목록 단계 README 의 함수 목록이 출발점, 함수 문서 약 129편) + 구조 6편 + 지도 README·api-index 완성 갱신(링크·문서 수·"목록 단계" 문구 제거).
B. `opensource/postgres/pgvector/`: `~/project/pgvector` 에 원본 클론(포크 없음 — 분석용) 후 태그 `v0.8.7`(`f37c13f68b`) 고정. 지도 README 에 흐름 목록을 소스로 확정하고 흐름 4~5편 본문 + api-index(연산자·인덱스 옵션).
C. 후속: ①PG 지도 vacuum 행 db-engine 문구를 실제 근거(10-01 과제 3 답 L267, 10-03 MVCCTableHeap 주석 L58)로 정정 ②`opensource/index.md` 의 mysql·postgres 행 상태 문구 갱신 ③`reference/tools/arch-map/` 에 코드 블록 대조 스크립트(레포·커밋 인자 일반화)와 작성·검증 브리핑 두 편을 올린다.

## 2. 경계·불변식 (필수)

- 모든 코드 인용과 줄 번호는 실제로 연 소스에서 온다 — postgres `REL_18_6`(`724edf9bde`), pgvector `v0.8.7`(`f37c13f68b`). 코드 블록은 소스 그대로.
- 소스 레포(`~/project/postgres`, `~/project/pgvector`) 읽기 전용(pgvector 는 클론·체크아웃만).
- 형식: `reference/writing/README.md` + 완성된 MySQL 지도 밀도. 폴더명 `NN_함수`.

## 3. 기준소스 (필수)

위 두 태그 · 형식 = `opensource/mysql/architecture/`(완성본)·ES 지도 · db-engine 대응 = `~/project/db-engine/impl/*.md`.

## 4. 금지영역 (필수)

`opensource/postgres/`·`opensource/index.md`·`reference/tools/arch-map/`·이 작업 폴더·측정로그·NEXT 밖. 다른 opensource 도구 폴더(mysql 포함). 원래 체크아웃(다른 세션 작업 중). push 는 끝난 뒤 사용자 확인.

## 5. 검증 방법 (필수)

- 흐름·구조·pgvector 묶음마다 작성 워커와 다른 검증 워커가 코드 블록 기계 대조 + 줄 번호 전수 + 서술 반증. 검증 워커가 고친 줄 번호는 sed 한 줄 출력 첨부.
- 메인: 묶음마다 표본 재대조, 최종 전체 대조(bad 0)·상대 링크 0 broken·`@@` 0·소스 레포 status clean.
- 레포에 올리는 스크립트: MySQL 완성본(598블록 bad 0)과 PG 문서에 돌려 같은 결과가 나오는지 스모크.

## 6. stakes (필수)

- 판정: 낮음 — 학습 문서, 되돌리기 쉬움. 주된 실패모드는 날조(줄 번호·동작 서술)라 작성/검증 분리를 의무로 둔다.

---

## 7. 자율성

- [x] auto
- [ ] lazy

## 8. load-bearing 가정

- 목록 단계에서 확정한 PG 함수 정의 줄(표본 21개 일치)이 본문의 토대로 충분하다 — 첫 배치 검증으로 조기 실증.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|------|------|------|-----------|
| 01 | reference/tools/arch-map 스크립트·브리핑 + pgvector 클론·고정 | — | MySQL 598 bad 0 재현 |
| 02 | PG 흐름 13 작성(2개씩) → 각 검증 | 01 | bad 0, 검증 packet |
| 03 | PG 구조 6 작성(3개씩) → 검증 | 01 | 〃 |
| 04 | pgvector 목록 확정 + 본문 → 검증 | 01 | 〃 |
| 05 | 지도·api-index·index.md 갱신, vacuum 문구 정정, 기록 마감 | 02~04 | 링크 0 broken |

---

## 승인 상태

- [x] 필수 6칸 전부 기입
- [x] 사용자 합의 → SPEC=1
- [x] 자율성 선택 → MODE=auto
