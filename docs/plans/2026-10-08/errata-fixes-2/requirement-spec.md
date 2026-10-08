# 요구사항 명세서 — errata-fixes-2

> 작성일: 2026-10-08 · 작업 폴더: `docs/plans/2026-10-08/errata-fixes-2/` · 브랜치: main(1f78bfd7, origin 22e287c5 + 로컬 log 커밋 1)에서 `docs/errata-fixes-2`.
> 선행: 커리큘럼 집필 완료(미작성 0). 영역마다 NEXT에 "영역 밖 후속(고치지 않음)"으로 쌓인 오류(N0-u~N0-z·보안)를 정리한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다른 영역 오류들 수정하자"
- Q/A (2026-10-08): 범위 **노트 오류 12건 · 커리큘럼 본문 오기 ~12건 · 원고 오류 3건 · 옛 형식 노트 형식 전환** 전부 · 검증 **가볍게, 합의 auto**(수정 워커 + 1차 출처 재대조 + check·링크 검사, codex 2차 없음).
- 추가 Q/A: 옛 형식 2편은 컬렉션 전체(domain-modeling/advanced 30·data-structure 35)의 형식 → **"컬렉션 전체 전환"** 선택. 규모가 커서 **별도 작업 폴더**로 이 작업 뒤에 진행(이 작업은 그 2편의 사실 오류만).

## 1. 목표·대상 (필수)

- **T1 노트 오류**(최소 문구 수정):
  - `reliability/38-microbenchmarking/2-summary.md:161`(신뢰구간 정의)·`:162·168·248`(겹침 비교)
  - `domain-modeling/advanced/27-ab-assign/2-summary.md:27·251·276`("salt가 다르면 독립")
  - `math/08-expectation-variance-tails/2-summary.md:25`(오른쪽 꼬리 ⇒ 평균>중앙값 단정)
  - `algorithm/13-backtracking/2-summary.md:254·327`·`3-answer.md:272·281`, `algorithm/42-alg-symptom-index/2-summary.md:188·196`(Java `(a+)+$` 지수 단정)
  - `security/25-supply-chain-security/2-summary.md:127`(의존성 그래프 DAG 단정)
  - `architecture/14-cache-coherence-and-memory-ordering/2-summary.md:244`(this 유출 조건)
  - `database/19-wal-and-logging/2-summary.md:199`(슬롯 상한 양자택일)
  - `testing/13-contract-testing/2-summary.md:158`·`api-design/07-versioning-and-compatibility/2-summary.md:200`(레지스트리 판정 = 필드 집합 비교)
  - `systems/nand-flash/2-summary.md:145`(출처 없는 수치)
  - `security/24-memory-safety-exploits/2-summary.md:247`(`[?]` 해제)
  - `reliability/21-scaling-principles/2-summary.md:52`(스레드 200 = 이용률 1)
  - `algorithm/33-*/2-summary.md:179·417`(압축 팽창 서술)
- **T2 원고 오류 3건**: `systems/server-design/02-request-path.md` §3 EWMA '함정' 칸·Least Connections "가장 무난한 기본값" / `systems/server-design/01-scaling-principles.md` §2 스레드 200·식당 예 단위 / `foundations/data-representation/README.md:98` epsilon 정의.
- **T3 커리큘럼 본문**(`docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`): §18 06·11·28행(OpenIntro 절 번호, GFT 기간, PHE 15,841) · §6 19행 선행 32→34 · §18a 17행 Unity 2문제·`[?]` 3개 해제, 📚 CloudEvents·Beauchemin·Linstedt·Dehghani `[?]` 해제 · §4 14행 📚 CS:APP 12.5 · §1 머리 MCS `[?]` · §1 06행 ⚠ 이차형 · §8 17행 RFC 10017 · §8 머리 OWASP 2025 병기 → `gen_area_readme.py` 재생성.

## 2. 경계·불변식 (필수)

- **I1** 최소 문구 + 1차 출처(또는 이미 검증된 새 leaf의 실험·출처 — data-analysis/08·14, language/02·19, math, data-engineering/05·09, network/46 등). 옛 형식 노트·원고는 구조·헤딩·문체 유지, 고치는 줄만.
- **I2** 새로 깨는 링크 0. 생성 문서는 생성기로만.
- **I3** 새 형식 leaf는 check_new PASS 유지(옛 형식은 대상 아님).
- **I4** 수정 근거를 확인 못 하면 고치지 않고 목록에 남긴다(추측 수정 금지).

## 3. 기준소스 (필수)

- `docs/plans/NEXT.md` N0-u~N0-z·보안 항목, 각 작업 log·판정 표, 근거 leaf의 실험·출처, 1차 출처(JLS 17.5, Cox "Minimal Version Selection", Confluent Schema Registry 문서, PostgreSQL 17 문서, RFC 1952, rfc-editor RFC 10017, OpenIntro 4판 PDF, Lazer 외 2014, PHE 2020-10 발표, Unity Q1 2022 Prepared Remarks, CS:APP 3판 목차)

## 4. 금지영역 (필수)

- `check_new.py`·생성기 코드, 생성 문서 수기 수정, 노트 구조 변경(헤딩·질문 수), 형식 전환(별도 작업), 저장소 루트 파일, 컨테이너는 전용 `sn-err2-*`·`--rm`만(pull·build·prune 금지)

## 5. 검증 방법 (필수)

- 워커가 항목마다 1차 출처·근거 leaf를 다시 열어 대조(packet에 출처 기재) · 수정 파일 상대 링크 전수 검사 · 새 형식 leaf check_new PASS · `git diff -U0` 셀프 리뷰(의도 외 변경 0) · 생성기 재실행 diff 확인

## 6. stakes (필수)

- **낮음~중간** — 문구 수정, 되돌리기 쉬움. 사실 수정은 출처 재대조로 받친다(사용자 "가볍게" 선택).

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 각 오류의 근거는 이미 새 leaf 판정·웹 표본에서 확인됐다 — 워커는 재대조만 한다.
- **A2**: 커리큘럼 수정 후 생성기 재실행이 해당 영역 README만 바꾼다.

## 9. task 분해

| task | 목표 | 담당 |
|---|---|---|
| 01 | T1 통계·알고리즘(reliability/38·domain-modeling 27·math/08·algorithm 13·42·33) | Opus 워커 A |
| 02 | T1 나머지(security 24·25·architecture/14·database/19·testing/13·api-design/07·nand-flash·reliability/21) | Opus 워커 B |
| 03 | T2 원고 3건 | Opus 워커 C |
| 04 | T3 커리큘럼 → 재생성 | Opus 워커 D |
| 05 | 링크·check·diff 셀프 리뷰·커밋·(확인 후) push·log·NEXT·측정로그 | 메인 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-08)
- [x] auto
