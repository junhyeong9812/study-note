# 요구사항 명세서 — react-portal 학습 아카이브

> 작성일: 2026-11-04 · 작업 폴더: `docs/plans/2026-11-04/react-portal-archive/` · 원 프로젝트: `/home/jun/project/react-portal` (GitHub `junhyeong9812/react-portal`, main 27d95e9)

## 0. 요구사항 원문 (인터뷰 기록)

- 원문:
  - "이번 주제에 대해서 공부내용들 정리한거, /home/jun/project/study-note/ 여기 프로젝트에 해당 프로젝트 섹션에 내용 이전 및 정리부탁해. 여기 아카이브하고 있거든."
  - "스터디 노트쪽 아카이브하면서 프로젝트에 대해서는 git주로 링크는 걸어야될 꺼 같아."
  - "이걸하면서 발생한 이슈들은 이슈 프론트쪽에 기록하고 frontend쪽 개념은 cs쪽에 frontend를 만들어서 넣으면 되나."
  - "러닝문서랑 기타 docs에서 정의한 내용은 내부 /project쪽에 아카이브 해놔줄래?"
  - "프론트 문서보면 … 갈취 요약형태라서 디테일한 설명이 없는건 좀 아쉽네" / "그냥 스터디 노트 형태에 맞춰서 넣는게 더 나을수도 있겠다."
- Q/A:
  - 개념 위치 → **web-platform에 없는 것만 새 주제로**(cs/frontend 신설은 cs 20영역 규칙과 충돌해 선택 안 함). 기존 노트는 "실제 내용을 보고 보강이 필요하면 보강". 사용자가 이해해 온 방식(질문 → 처음 그림 vs 실제 그림)을 반영해 도식을 늘린다.
  - issue 카드 → **4건 모두 매칭 후 기록**(새 카드 / 방안 비교 / 무변경 판정).
  - 반영 → **브랜치 커밋, main 병합·push는 확인 후**.

## 1. 목표·대상 (필수)

study-note에 react-portal 학습 내용을 세 갈래로 반영한다.

| 갈래 | 경로 | 무엇 |
|---|---|---|
| 기록 — 구현 | `project/react-portal/` | 프로젝트 README(GitHub 저장소·PR·커밋 링크) + §2-B 이슈 폴더(결정 이유·후보·실커밋 스니펫) + 원 프로젝트 학습 문서(`docs/learning/`·`docs/frontend/`) 아카이브 |
| 훈련 — 개념 | `cs/web-platform/` | 새 주제 3개(25 portal-and-two-trees · 26 stacking-context-and-containing-block · 27 modal-dialog-behavior) — cs 작성 규칙 7절 골격·3파일·metadata·실험 출력. 커리큘럼 §16에 행 추가 → 생성 스크립트로 영역 표 갱신 |
| 실전 이슈 | `issue/` | 4건 매칭: ① portal 바깥 클릭 DOM 판정 ② 진행 중 이벤트에 같은 타입 리스너 추가 ③ 인스턴스별 전역 키 리스너(맨 위 없음) ④ 공유 자원 카운트 없는 해제 |

기존 cs 노트(web-platform/04, language/06·07·09·10)는 내용을 읽고 이번 이해 흐름과 비교해 **보강이 필요한 곳만** 보강한다(필요 없으면 근거를 log에 남기고 무변경).

## 2. 경계·불변식 (필수)

- cs 노트는 `cs/README.md` 작성 규칙을 따르고 `scripts/notes/check_notes.py`가 error 0, `gen_area_readme.py --check` 통과.
- cs 노트 안에는 프로젝트 진행 기록·원본 대응표를 두지 않는다(§5) — project/에 둔다.
- issue 카드는 `issue/authoring-guide.md` 형식 + 공개 안전선: 프로젝트명·파일 경로·실코드 대신 추상화 코드. 커밋 전 노출 스캔 0건.
- project/ 문서의 코드 스니펫은 react-portal 실파일에서 복사, 커밋 해시 명시. 원 프로젝트 파일 링크는 GitHub URL(`https://github.com/junhyeong9812/react-portal/blob/<sha>/…`).
- 실험 출력은 실제 실행 결과만(jsdom·Node 버전 라벨).
- 기존 노트 본문 수정 시 의미를 바꾸지 않는 보강(도식·설명 추가)만.

## 3. 기준소스 (필수)

react-portal main(27d95e9)의 코드·문서, study-note `reference/study-note-guide.md`·`cs/README.md`·`issue/authoring-guide.md`, WHATWG DOM/HTML·CSS 명세·WAI-ARIA APG(Dialog), react.dev `createPortal`.

## 4. 금지영역 (필수)

- 커리큘럼 생성 표(`cs/web-platform/README.md`) 직접 편집 금지 — 커리큘럼 수정 후 생성기로만.
- study-note의 무관한 파일, `git add -A`·`.` 금지(경로 지정 스테이징).
- main 직접 커밋·push는 사용자 확인 전 금지.

## 5. 검증 방법 (필수)

- `python3 scripts/notes/check_notes.py cs/web-platform/25-… 26-… 27-…` error 0 (+ 보강한 기존 노트).
- `python3 scripts/notes/gen_area_readme.py --check` 통과.
- 상대 링크 실재 검사(project/·issue/), issue 카드 노출 스캔(프로젝트명·경로·호스트) 0건.
- 실험: react-portal 저장소에서 jsdom으로 실행한 출력.

## 6. stakes (필수)

- 판정: **낮음** — 문서 저장소, 브랜치 작업, 되돌리기 쉬움. 공개 저장소이나 개인 학습 프로젝트 내용(비밀 없음). 노출 스캔으로 issue 안전선 확인.

## 7. 자율성

- [x] auto
- [ ] lazy

## 8. load-bearing 가정

- A1: 커리큘럼 §16에 행을 추가하고 `gen_area_readme.py`를 돌리면 web-platform 영역 표에 25~27이 생기고 `--check`가 통과한다(번호 체계·마감 주제 23·24 뒤에 붙여도 되는지). → 착수 직후 확인.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|---|---|---|---|
| 01 | 커리큘럼 행 추가 + 생성기 스모크(A1) | — | `--check` 통과 |
| 02 | project/react-portal (README·이슈 폴더·학습 문서 아카이브) | — | 링크 검사 0 |
| 03 | cs/web-platform 25·26·27 (3파일·metadata·실험) | 01 | check_notes error 0 |
| 04 | 기존 노트 비교·필요 시 보강 | 03 | check_notes error 0, 판정 log |
| 05 | issue 4건 매칭·기록 | — | 노출 스캔 0 |
| 06 | 인덱스(project/index.md 등) 갱신, 브랜치 커밋 → 사용자 확인 | 02~05 | — |

## 승인 상태

- [x] 필수 6칸 전부 기입
- [x] 사용자 합의 → SPEC=1 (2026-11-04)
- [ ] 자율성 선택 → MODE 기록
