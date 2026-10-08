# 요구사항 명세서 — legacy-format-conversion-2

> 작성일: 2026-10-08 · 작업 폴더: `docs/plans/2026-10-08/legacy-format-conversion-2/` · 브랜치: `docs/legacy-format-conversion-2`(main 210d2bd2). 선행: legacy-format-conversion(65편, push 0ee6675d) — 도구 `docs/plans/2026-10-08/legacy-format-conversion/tools/`.

## 0. 요구사항 원문 (인터뷰)

- 원문: "진행하자"(직전 보고의 남은 것 — 옛 형식 잔여·작은 오류 2건)
- Q/A (2026-10-08): 범위 **"85편 + 원고 33편 재구성"**(실측 36편) + NEXT 잔여 오류 2건. 검증은 직전 작업과 같이 가볍게·합의 auto(사용자 이전 선택 유지).

## 1. 목표·대상 (필수)

- **T1 과제 이식 컬렉션 85편**: `cs/algorithm/[0-9]*` 30 · `cs/domain-modeling/basic/[0-9]*` 30 · `cs/ops-patterns/[0-9]*` 19 · `cs/api-design/22~27-case-*` 6 — 직전 작업과 같은 규칙(번호 유지, C 항목 이어 번호, 그룹 굵은 줄, '쓰이는 곳' → '쓰이는 자료구조·알고리즘', metadata `형식 | 과제 이식`).
- **T2 단독 노트 36편**(목록 `scratchpad/lfc2/originals.txt` — systems 20·engineering 10·ops-patterns 3·domain-modeling 2·foundations 1·data-structure/lsm-merge-model): 7절 골격으로 **재구성**. 원래 절은 알맞은 7절 아래 `###`로 옮기고, 질문·답은 `N. `/`### N.` 번호로 짝을 맞춘다.
- **T3 잔여 오류 2건**: 원고 `systems/server-design/02-request-path.md` §3 표 Consistent Hashing '함정' 칸(장점이 들어감) · `algorithm/33:176` RFC 1951 최악 팽창 서술과 실측(+310B/1MB) 관계 판정 후 필요 시 정정 · `ops-patterns/failure-at-scale` 깨진 링크 `../multi-tenancy/`.

## 2. 경계·불변식 (필수)

- **I1 무손실**: T1은 토큰열 동일(verify.py). T2는 파일마다 원래 토큰 **다중집합이 새 파일에 모두 포함**(삭제 0) — 추가는 헤딩·번호와 아래 I3의 보충만.
- **I2 번호 보존**(T1) — 직전 작업과 같음.
- **I3 보충 최소**: T2에서 7절 중 원래 내용이 없는 절, 또는 질문이 6개 미만인 경우에만 노트 본문에 근거한 짧은 보충을 쓴다(새 사실·수치 금지 — 노트에 이미 있는 내용의 요약·참조). 보충 목록을 편별로 보고한다. 질문 10개 초과면 멈추고 보고.
- **I4** 새로 깨는 링크 0, 대상 밖 판정 불변, 생성기 집계 불변(단계 칸 그대로 — 원고는 원고).

## 3. 기준소스 (필수)

- `check_new.py`, 대상 노트 현재 본문, 직전 도구(convert.py·verify.py), 새 형식 예(`cs/data-structure/25-ring-buffer`, `cs/domain-modeling/advanced/27-ab-assign`), RFC 1951, `cs/network/46-load-balancers-and-proxies`

## 4. 금지영역 (필수)

- 본문 문장 수정·삭제(T3 제외), 사실 추가, 단계 칸 변경, 대상 밖 노트, 생성 문서 수기 수정, 검사기 추가 변경, 저장소 루트 파일

## 5. 검증 방법 (필수)

- T1 verify 85/85 + check PASS · T2 다중집합 포함 검사 36/36 + check PASS + 보충 목록 메인 확인 + 파일럿 2편 메인 검토 후 확대 · 전체 leaf 전후 비교 · 링크 · 생성기 diff

## 6. stakes (필수)

- **낮음~중간** — T1 기계적. T2는 원고 재배치라 보충 문장이 사실 오류를 낼 위험 → 보충은 노트 내용 범위로 한정, 메인이 목록 검토.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 직전 convert.py가 T1 85편을 대부분 처리한다(algorithm·ops-patterns의 '### A. 문제' 변형 정도).
- **A2**: 단독 노트는 대부분 질문 ≤10이다(초과 시 보고).

## 9. task 분해

| task | 목표 | 담당 |
|---|---|---|
| 01 | T1 85편 | Opus 워커 A |
| 02 | T2 파일럿 2편 + 대조 도구 | Opus 워커 B → 메인 검토 |
| 03 | T2 나머지 34편(파일럿 기준으로 3분할) | Opus 워커 B·C·D |
| 04 | T3 | Opus 워커 E |
| 05 | 검증·커밋·log·NEXT·측정로그·(확인 후) push | 메인 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 선택 "85편 + 원고 33편 재구성"(2026-10-08)
- [x] auto
