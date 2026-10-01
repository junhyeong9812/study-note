# 요구사항 명세서 (requirement-spec)

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "이슈 이동, cs 규칙 개정, 하네스 경로 수정 및 커밋까지만 우선 진행해보자." (커리큘럼·foundations 해체는 이번 범위 밖)
- 앞선 결정 (같은 세션):
  - "cs/issue도 그냥 issue로 최상위로 빼는 게 맞는 거 같아."
  - 하네스 경로 수정은 **이번 재편에 포함**.
  - CS 작성 규칙은 **전부 Claude 완성본으로 재작성**. 원고 우선 규칙은 폐기.
  - 서머리 골격은 **전 주제 통일**. 사용자 논리: "개념이든 자료구조·알고리즘이든 결국 어떤 문제를 해결하려는 것이고, 쓰면 어떤 장애가 생기는지가 다 나온다."
  - 알고리즘·자료구조·도메인 모델링·API 디자인은 **cs 유지 + 진행기록 분리**.
  - 퀴즈(1-question)·서머리(2-summary)·정답(3-answer) 구조로 전부 작성. 배포 사이트에서 읽으며 검수하고, LLM 질문으로 구체화.
  - 브랜치: study-note는 **현재 브랜치(docs/nextjs-app-render)에서 계속**.
  - 배포 사이트 채팅 기록(doc_path 키)은 **경로 마이그레이션 필요**. 별도 작업 C로 하고, 이번 작업은 path-map만 산출.

---

## 1. 목표·대상 (필수)

두 저장소에서 아래 상태가 되고, 각 저장소에 커밋되면 끝이다.

- **study-note**
  - `cs/issue/` 전체(92파일)를 최상위 `issue/`로 이동(`git mv`)하고, 내부·외부 상대 링크와 `cs/issue` 표기를 새 경로로 교정한다.
  - 루트 `index.md`·`README.md`에 `issue/` 입구를 추가한다.
  - `cs/README.md` 작성 규칙을 개정한다: Claude 완성본, 통일 골격, 3파일 전부 작성, cs는 지식 본문만.
- **claude-code-harness**
  - issue-archive 대상 경로를 `study-note/issue/`로 수정한다: `playbooks/issue-archive.md`, `src/core.md` §7, `README.md`, 커밋 메시지 접두 `docs(issue)`.
  - `HISTORY.md` 1행을 추가한다.

## 2. 경계·불변식 (필수)

- **I1 파일 보존**
  - 이동 전 `cs/issue` 파일 집합과 이동 후 `issue/` 파일 집합은 경로 접두만 다르고 1:1로 대응한다(92 = 92).
  - 본문 변경은 링크·경로 표기 교정뿐이다.
- **I2 링크 무손상**: 이동 후 저장소 전체에서 깨진 상대 링크 집합 ⊆ 이동 전 기준선의 깨진 링크 집합(경로 치환 후 비교). 새로 깨지는 링크는 0이다.
- **I3 잔존 0**: `cs/issue` 문자열이 다음 두 범위에서 0건이어야 한다. 과거 기록은 이력이라 보존한다.
  - study-note: `docs/plans/**`·`history/**` 제외
  - harness: `HISTORY.md`·`docs/plans/**` 제외
- **I4 규칙 단일 출처**
  - 카드 형식의 정본은 `issue/authoring-guide.md` 그대로이고, playbook은 절차만 둔다.
  - cs 작성 규칙의 정본은 `cs/README.md`다.
- **I5 커밋 범위**
  - study-note 커밋에는 이 작업 경로만 넣는다: `issue/`, `cs/issue` 삭제분, `cs/README.md`, `index.md`, `README.md`, 이 작업 폴더.
  - 브랜치에 있던 무관 미커밋분(`docs/measurement-log.md` 기존 수정, `docs/plans/2026-09-26/`, `docs/plans/NEXT.md`)은 섞지 않는다.

## 3. 기준소스 (필수)

- study-note 현 HEAD의 `cs/issue/` 트리(92파일)와 저장소 전체 상대 링크(이동 전 기준선을 스크립트로 기록).
- 하네스: `claude-code-harness` main HEAD의 `playbooks/issue-archive.md`·`src/core.md`·`README.md`.
- 경로 규칙: 배포 트리는 경로 범용 렌더링이다. `TreeBuilder.kt`에 폴더 허용 목록이 없음을 읽어서 확인했다.

## 4. 금지영역 (필수)

- `cs/` 안의 다른 폴더 재편: foundations 해체, 커리큘럼 반영, 진행기록 분리. 커리큘럼 확정 후 별도 작업이다.
- CS 본문 집필·재작성(작업 B…). 이번 README 개정은 규칙 문서만 바꾼다.
- `reference/organize-guide.md`: 다른 폴더도 참조하므로 수정하지 않는다. cs/README에서의 참조 관계만 조정한다.
- `deploy-study-note` 코드·DB(채팅 경로 마이그레이션 = 작업 C).
- 하네스 `deploy.sh` 실행과 두 저장소의 **push**. 사용자가 "커밋까지만"이라고 했다.
- harness `main` 직접 커밋. 작업 브랜치 `docs/issue-archive-toplevel-path`를 main에서 생성한다.
- 과거 기록(`docs/plans/**`·`HISTORY.md` 기존 행·`history/**`)의 `cs/issue` 표기.

## 5. 검증 방법 (필수)

- **V1 (I1)**: `git diff --cached -M --name-status`에서 R(rename) 92건, 추가·삭제 0건. 파일 수 92 = 92.
- **V2 (I2)**: 스크래치 링크 검사 스크립트(repo 전체 md 상대 링크 해소)를 이동 전후에 실행한다.
  - 신규 깨짐 0을 확인한다.
  - 이동 전 기준선의 깨진 링크는 log에 기록한다. 기존 결함이며 이번에 고치지 않는다.
- **V3 (I3)**: `grep -rn "cs/issue"` 두 저장소 모두 제외 범위 밖 0건.
- **V4 하네스**: `hooks/tests/run.sh` 전체 통과(훅 무변경이지만 회귀 확인).
- **V5 스모크**
  - playbook 절차대로 새 경로에서 `issue/README.md` 인덱스와 `authoring-guide.md`가 열리는지 확인한다.
  - 배포 트리 관점에서 `issue/`가 리프 규칙(리프 폴더엔 md만)을 지키는지 `find`로 확인한다.
- **V6 리뷰**: 듀얼 1패스(Opus 워커 ∥ codex) → 종합 → post-fix 재점검 1회. 새 지적이 남으면 루프(≤3).
- **V7 산출물**: `path-map.tsv`(옛 경로 → 새 경로, 92행). 작업 C의 입력이다.

## 6. stakes (필수)

- 판정: **높음**
- 근거:
  - 하네스 정책 파일(`core.md`·playbook)을 변경한다. core §2에 따라 하네스·정책 변경은 높음이다.
  - 92파일을 이동한다.
- 완화 요인: git으로 되돌릴 수 있고, 변경이 기계적 경로 치환이다.
- 적용 강도: 외부 검색 불필요(내부 경로 변경, 사유 기록) · 듀얼 리뷰 루프 · 설계 선검증 생략(신설 동작 불변식 없음) · 테스트 설계는 스펙 기반 검사 스크립트(V1~V3)를 구현 전에 작성.

---

## 7. 자율성 (모드)

- [ ] auto (기본 권장)
- [ ] lazy

## 8. load-bearing 가정

- **A1**: 배포 사이트가 최상위 `issue/`를 추가 설정 없이 렌더링한다. `TreeBuilder.build`가 경로만으로 트리를 만든다는 것을 코드로 확인했다. 실배포 렌더 확인은 push 후라서 범위 밖이다.
- **A2**: `cs/issue` 밖에서 `cs/issue`를 가리키는 링크는 없다(grep 확인 rc=1). 따라서 교정 대상은 ① `issue/` 내부에서 밖을 향하는 상대 링크(깊이 −1)와 ② 파일 내 `cs/issue` 표기뿐이다. 착수 직후 V2 기준선으로 재확인한다.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|------|------|------|-----------|
| 01 | 검사 스크립트(V1~V3) + 이동 전 링크 기준선 | — | 기준선 log 기록 |
| 02 | `git mv cs/issue issue` + 링크·표기 교정 + 루트 index/README 입구 + path-map | 01 | V1·V2·V3 통과 |
| 03 | `cs/README.md` 규칙 개정 | — | 사용자 확인(개정안 diff) |
| 04 | 하네스 브랜치 생성 + 경로 수정 + HISTORY 1행 | — | V3(harness)·V4 |
| 05 | 듀얼 리뷰 → 수정 → 재점검 | 02·03·04 | 새 지적 0 |
| 06 | 커밋: study-note(현 브랜치, 경로 지정) + harness(작업 브랜치) | 05 | `git show --stat` 범위 확인 |
| 07 | 마감: measurement-log 1행, NEXT.md 갱신(작업 C·하네스 deploy·커리큘럼 재편 후보) | 06 | — |

### 03 개정안 요지 (합의 대상)

`cs/README.md`의 「문서가 만들어지는 흐름」·「융합 규칙」·「하지 말 것」을 교체한다.

1. **작성 주체**: cs 문서는 Claude 완성본으로 쓴다. 원고 문체 보존 규칙은 폐기한다.
   - 기존 원고는 입력 자료로만 쓴다.
   - 사실 주장은 교재·RFC 등 근거를 대조하고, 확인하지 못한 것은 `[?]`로 표시한다.
2. **통일 골격(2-summary)**: 해결하는 문제 → 동작·원리 → 쓰이는 자료구조·알고리즘 → 적용(풀어나가는 법) → 장애 시나리오(현상 → 보이는 형태 → 원인 → 대처) → 관련 주제.
3. **3파일 전부 작성**
   - 서머리를 먼저 쓰고, 같은 패스에서 1-question·3-answer를 작성한다.
   - "서머리와 질문·정답을 한 파일에 섞지 않는다"는 규칙은 유지한다.
4. **검수 상태**
   - 각 주제 index에 `초안(Claude)` → `검수 완료` 상태를 둔다.
   - 검수는 배포 사이트에서 읽기와 LLM 질문으로 한다.
5. **cs = 지식 본문만**: 진행 기록, 원본 저장소 대응표, 구현 연계는 project/·lab/·practice/로 보낸다. 실제 분리는 후속 작업이다.

---

## 승인 상태

- [x] 필수 6칸 전부 기입
- [ ] 사용자 합의 → SPEC=1
- [ ] 자율성 선택 → MODE 기록
