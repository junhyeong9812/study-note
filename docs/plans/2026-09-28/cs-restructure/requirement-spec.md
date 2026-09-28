# 요구사항 명세서 — cs-restructure (rev.2: 제자리 유지 + 링크)

> 작성일: 2026-09-28 · 작업 폴더: `docs/plans/2026-09-28/cs-restructure/`
> 기준 설계: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`(642 leaf·19영역, §19 이식 매핑)

## 0. 요구사항 원문 (인터뷰)

- 원문: "명세부터 작성해보자" — 커리큘럼 기준 cs 재편
- Q/A (2026-09-28, rev.1 → rev.2 경위 포함)
  - 폴더 생성: 기존 노트는 그대로 두고, **영역 README에 전체 leaf 목록**을 둔다. 새 leaf 폴더는 집필할 때 만든다.
  - 번호: 학습 순서로 재번호한다. **curriculum.md를 새 번호로 갱신**하고 옛 → 새 대응표를 남긴다.
  - 규칙 참조 정리와 cs/README 코드 언어 규칙: **포함**한다.
  - 기초와 심화: "각각 존재하고, 심화에서 기초가 필요하면 링크" → 기초 노트를 독립 leaf로 인정한다. 커리큘럼의 "흡수 후 삭제 후보" 판정은 철회한다.
  - 흐름: 브랜치 → 검증·리뷰 → main ff → push
  - myway 5개 영역: 처음에는 "project로 이동"을 골랐다가 철회했다. 사용자 판단은 "저 5개 내용이 cs 자체고, 정리된 형태로 전부 cs에 있어야 한다"다.
    - 실측: 150노트 모두 3파일이 완비돼 있다.
    - 빈 곳 ①: data-structure 35편의 「핵심 문장」 빈 불릿
    - 빈 곳 ②: 질문·정답 대부분이 "Claude 초안 — 본인 검토" 상태
    - → **cs에 제자리 유지**한다.
  - ops-patterns: "둘 다 가지도록. ops 패턴에 두고 cs 링크를 걸면 된다" → **컬렉션을 유지하고 영역 README에서 링크**한다.
  - foundations·systems·engineering: "이것도 제자리 유지 + 링크"
  - 진행 기록 분리: rev.1에서 "이번에 함께"로 합의했다. 대상은 myway 원본 경로와 진도 칸이다(아래 §1-3).

## 1. 목표·대상 (필수)

study-note에서 **기존 노트 이동 0건**으로 아래가 되면 끝이다.

1. **커리큘럼 재번호**
   - curriculum.md의 모든 leaf를 영역별 권장 학습 순서로 다시 번호 매긴다.
   - 선행, 학습 순서, 성능·추적성 트랙, §19 매핑 참조도 모두 새 slug로 바꾼다.
   - 기초 노트 두 편(`foundations/data-structures-basics`, `foundations/algorithm-basics`)을 data-structure와 algorithm 영역의 「기초」 단원 leaf로 추가하고, 심화 leaf 선행과 연결한다.
   - 산출물: `slug-map.tsv`(옛 slug → 새 slug)
2. **영역 README 19개**
   - 영역마다 전체 leaf 표를 둔다. 열은 번호·slug, 요지, 등급, 상태, **노트 링크**다.
     - 노트 링크: 기존 노트 실제 경로. 예: `cs/ops-patterns/01-retry-backoff/`, `cs/foundations/process-thread/`
     - 상태: `미작성` / `원고 있음` / `초안(Claude)` / `검수 완료` 중 하나다. 기존 노트는 1-question·3-answer에 Claude 초안 표기가 있으면 `초안(Claude)`, 두 파일 모두 `✅ 검수 완료` 표식이면 `검수 완료`, 그 밖에는 `원고 있음`이다(리뷰 C1·C2 반영).
   - 표는 curriculum.md에서 **스크립트로 생성**한다.
   - 새 영역(15개)은 `cs/<area>/README.md`를 새로 만든다.
   - 기존 폴더와 이름이 같은 영역(algorithm, data-structure, domain-modeling, api-design)은 기존 README·index를 덮어쓰지 않는다. 생성 표를 `cs/<area>/curriculum.md`로 두고 README에서 링크한다.
3. **진행 기록 분리**
   - myway 대응 영역 index(algorithm, data-structure, domain-modeling basic·advanced, ops-patterns, api-design)의 원본 경로·진도 칸을 옮긴다.
   - 옮길 곳: `project/myway/README.md` 대응표(신설)와 project/index 행
   - cs 쪽 index에는 상태·설명만 남긴다.
4. **규칙·색인 정리**
   - cs/README: 코드 스니펫 언어(Java·JS·TS, 저수준은 C 등), 상태 어휘 4종, 구조(19영역 README와 기존 컬렉션이 공존하는 방식)
   - cs/index.md: 19영역 지도와 기존 컬렉션 목록
   - 루트 index·README 트리
   - 이연 정리 항목:
     - issue/authoring-guide의 "cs 컨벤션" 의존
     - reference/learning/README의 옛 인용
     - `cs/engineering/development-standards/README.md:5`
     - reference/study-note-guide §2·§2-1·§5·§7·§8의 cs 관련 본문
     - cs/index 상태 범례
     - templates의 cs 비적용 표기

## 2. 경계·불변식 (필수)

- **I1 이동 0**: 기존 노트 파일의 rename·삭제는 0건이다. 기존 노트 본문은 이번에 고치지 않는다. 예외는 규칙 참조 정리 대상 파일과 index의 진도 칸 제거다.
- **I2 링크**: 새로 깨지는 상대 링크 0. 생성 README의 노트 링크도 전부 실제로 있어야 한다.
- **I3 커리큘럼 단일 출처**: 영역 README 표는 생성물이다. 재생성했을 때 diff가 0이어야 한다. slug 중복 0, 선행 참조 불일치 0이다.
- **I4 트리 규칙**: 새 폴더는 README를 가진 영역 폴더뿐이다. 새로 생기는 리프에는 md만 둔다.
- **I5 범위**: 노트 본문 재작성과 빈 곳 채우기는 이 작업에서 하지 않는다. 바로 다음 작업 **「myway 5개 cs 주제 완성」**에서 한다. 그 작업의 사용자 지시는 "빈 곳도 전부 채워서 문서를 다 완성"이며 별도 명세로 진행한다.

## 3. 기준소스 (필수)

- curriculum.md(main a96e5277)와 현재 cs/ 트리

## 4. 금지영역 (필수)

- 기존 노트 이동·삭제·본문 수정(I1 예외 제외)
- issue/·languages/ 본문
- myway 원 저장소, deploy-study-note, 하네스

## 5. 검증 방법 (필수)

- V1: `git diff --name-status`에서 R·D 0이고, M은 규칙·색인 대상 목록과 일치한다.
- V2: linkcheck 신규 깨짐 0, 생성 README 링크 실존 100%
- V3: 커리큘럼 검증 스크립트 — slug 중복 0, 선행 불일치 0, 학습 순서 = 번호 순, leaf 수 644(= 642 + 기초 2)
- V4: 생성 스크립트 재실행 diff 0
- V5: 영역 README 상태 칸 집계가 기존 노트 수와 맞는다. 원고 있음 + 초안의 합이 §19 매핑 대상 수와 같다.
- V6: 리뷰 — 듀얼 1패스(Opus ∥ codex) + post-fix 재점검
- V7: 산출물 `slug-map.tsv`

## 6. stakes (필수)

- 판정: **중간**
- 근거: 파일 이동이 없어 blast radius가 작다. 규칙 문서 여러 개를 개정하고 커리큘럼 642 slug를 재번호한다. 되돌리기는 쉽다.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 영역별 권장 학습 순서 줄이 그 영역의 모든 leaf를 한 번씩 포함한다. 괄호 안 "심화" 묶음은 나열 순서를 따른다. 착수 직후 스크립트로 검증하고, 누락이나 중복이 있으면 멈추고 보고한다.
- **A2**: 커리큘럼 `기존` 칸의 경로가 실제 노트 폴더로 해석된다. 착수 직후 전수 확인하고, 해석되지 않는 경로는 목록으로 보고한 뒤 교정한다.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|---|---|---|---|
| 01 | A1·A2 검증 스크립트 | — | 누락·중복·미해석 0 또는 보고 |
| 02 | 브랜치 + curriculum 재번호·기초 leaf 추가 + slug-map | 01 | V3 |
| 03 | 영역 README·curriculum.md 생성 스크립트 → 19개 | 02 | V2·V4·V5 |
| 04 | 진행 기록 분리(project/myway/README, cs index 진도 칸 제거) | — | V1·V2 |
| 05 | 규칙·색인 정리 | 03 | V1·V2 |
| 06 | 듀얼 리뷰 → 수정 → 재점검 | 05 | V6 |
| 07 | main ff → push, log·NEXT(다음 작업: myway 5 주제 완성)·측정로그 | 06 | — |

## 승인 상태

- [x] 6칸
- [x] 합의: 2026-09-28 "우선 구조화하고 myway쪽 5개 cs 주제에 대해 우선 완성하자"
- [x] auto
