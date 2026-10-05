# 요구사항 명세서 — errata-fixes

> 작성일: 2026-10-05 · 작업 폴더: `docs/plans/2026-10-05/errata-fixes/` · 브랜치: main(로컬 log 커밋 1 포함, origin/main d9bc037c)에서 `docs/errata-fixes`.
> 선행: 영역 집필 사이클마다 NEXT에 "영역 밖 후속(보고만)"으로 쌓인 오류를 한 번에 정리한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "오류들 수정하자"
- Q/A (2026-10-05): 범위 **4묶음 전부** — ① 낡은 "미작성" 링크 전부 ② 사실 오류(노트 본문 — 원본·myway 노트 수정 포함) ③ 커리큘럼 본문 오기 ④ 원본 legal-standards 법령 갱신 · 검증 **가볍게, 합의 auto**

## 1. 목표·대상 (필수)

- **T1 낡은 링크**: `cs/**/*.md`(생성 문서 README·curriculum.md·index.md 제외)에서 "미작성"·`curriculum.md`/영역 README로만 가리키는 표기 중 **대상 노트가 이제 실재하는 것**을 실제 상대 링크로. 대상이 없는 것은 그대로(계수만).
- **T2 사실 오류**(NEXT N0-o·N0-r 등 누적):
  - Knight "45분에 4.6억" 축약 → SEC 34-70694 ¶1·¶17 기준(45분 = 주문 송출, 4.6억 = 결국 실현된 손실): `reliability/04` 2-summary·3-answer, `ops-patterns/failure-modes` 2-summary
  - `data-structure/03-stack` "수천 줄 반복"(HotSpot `MaxJavaStackTraceDepth` 기본 1024)
  - `foundations/data-structures-basics` §7 Python 재귀 "스택 오버플로" → RecursionError, 원본 코드 버그(후위 순회 오른쪽 호출·remove None 검사·"중복 불가" vs insert·full binary tree 용어·연결 리스트 삽입 조건) / `foundations/algorithm-basics`(§1 조건 없는 예·§4 binary_search 매번 sort·"10개면 3번"·§5 조기 종료 없음) — 새 leaf ds 01·alg 01의 "참고:" 줄이 근거
  - `data-structure/lsm-merge-model` "레벨당 파일 1개" → run 1개, "FTL과 정확히 같다" 과장
  - `os/31` 245행 engineering-practice 소속 오기(`36-profiling`·`20-performance-method-and-amdahl`)
  - 원본 `engineering/development-standards/operational-standards` 깨진 `../../straggler/` → 실제 경로
- **T3 커리큘럼 본문 오기**: NEXT N0-e 누적 항목 + §3 alg 03 ⚠ 과일반화 + GAO-14-694 `[?]` 제거(N0-l) → `gen_area_readme.py` 재실행(바뀐 생성 문서만 커밋).
- **T4 법령 갱신**: 원본 `engineering/development-standards/legal-standards/`(2-summary·3-answer·provisions.md 등)를 2026-09-11 시행 개인정보 보호법 개정(법률 제21445호)에 맞게 갱신. 근거는 law.go.kr 원문 + `cs/engineering-practice/17-legal-standards`(이미 대조된 조문).

## 2. 경계·불변식 (필수)

- **I1** 링크만 바꾸는 곳은 문장 의미를 바꾸지 않는다. 새로 깨는 링크 0(수정 파일 전수 검사).
- **I2** 사실 수정은 최소 문구 + 1차 출처(SEC 원문 사본·OpenJDK 소스·CPython 문서·RocksDB wiki·law.go.kr). 옛 형식 노트(myway·원본)의 구조·헤딩·문체는 유지하고 고치는 줄만 바꾼다.
- **I3** 생성 문서는 수기 수정 금지 — 커리큘럼 본문을 고치고 생성기로만.
- **I4** check_new: 새 형식 leaf를 건드렸으면 PASS 유지(옛 형식은 대상 아님).
- **I5** 법령 서술은 "해석·법률 자문 아님" 표기 유지, 조문 번호·시행일은 원문 그대로.

## 3. 기준소스 (필수)

- `docs/plans/NEXT.md`(N0-e·N0-i·N0-l·N0-m·N0-n·N0-o·N0-r 등), 각 작업 log의 영역 밖 목록, law.go.kr, SEC 34-70694 사본(`scratchpad/ep/fc-19/src/`), 새 leaf의 "참고:" 줄과 근거

## 4. 금지영역 (필수)

- `check_new.py`·생성기 코드, 생성 문서 수기 수정, 노트 구조 변경(헤딩·질문 수), 대상 없는 "미작성"을 추측 링크로 바꾸기, 저장소 루트 파일

## 5. 검증 방법 (필수)

- 수정 파일 상대 링크 전수 검사(깨짐 0) · 새 형식 leaf check_new PASS · `git diff` 셀프 리뷰(의도 외 변경 0) · T2 사실 수정은 Opus 워커가 1차 출처 대조 · **T4 법령은 stakes 중간으로 보고 diff에 codex 1회**(사용자 선택 '가볍게'보다 한 단계 높임 — 법령 조문 오류 위험) · 생성 문서 재생성 diff 확인

## 6. stakes (필수)

- **낮음**(T1·T3 링크·문구) / **중간**(T2 사실·T4 법령 — 학습 노트지만 법 조문·사고 수치 오류 위험)

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: "미작성" 표기의 대상은 대부분 slug로 실재 폴더를 찾을 수 있다(애매하면 바꾸지 않고 목록으로).
- **A2**: law.go.kr 원문을 curl로 열 수 있다(§17 작업에서 확인됨).

## 9. task 분해

| task | 목표 | 담당 |
|---|---|---|
| 01 | T1 낡은 링크 전수(T2·T4 대상 파일 제외) | Opus 워커 A |
| 02 | T2 사실 오류 | Opus 워커 B |
| 03 | T4 법령 갱신 + codex 1회 | Opus 워커 C → codex |
| 04 | T3 커리큘럼 + 생성기 | 메인 |
| 05 | 링크 전수·check·커밋·(확인 후) push·log·NEXT 정리·측정로그 | 메인 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-05)
- [x] auto
