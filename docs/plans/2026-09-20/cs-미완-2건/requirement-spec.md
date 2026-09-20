# 요구사항 명세 — cs/ 미완 2주제 완결

작성 2026-09-20 · 대상: `cs/systems/storage-media-workload` · `cs/engineering/failure-point-checklist`

## ① 목표·대상

`cs/` 의 잎 주제 184개 중 3파일이 안 갖춰진 **2건**을 완결한다.

### A. `cs/systems/storage-media-workload` — 1파일뿐

현재 `2-summary.md`(174줄)만 있고 **`1-question.md`·`3-answer.md` 가 없다.**
게다가 그 요약본 자체가 **Claude 초안**이며(머리말이 「본인 문장으로 교체한 뒤 이 줄을 지운다」라 적는다),
따라 친 원고가 없다 — 포트폴리오 사례를 일반화해 쓴 것이다.

할 일:
1. **요약본의 수치·주장을 1차 출처로 접지**하고 틀린 값을 고친다(사용자 확정 2026-09-20).
2. 그 값 위에 `1-question.md` 작성.
3. `3-answer.md` 작성.
4. 머리말의 「Claude 초안」 경고를 **실제 출처 표기로 교체**한다.

### B. `cs/engineering/failure-point-checklist` — 2파일

`1-question.md`(10문)·`2-summary.md`(198줄)는 있고 **`3-answer.md` 가 없다.**

할 일:
1. `3-answer.md` 작성 — **질문 10개 전부**에 답한다.
2. `2-summary.md` 의 **원고 경로가 낡았다** — `jun-bank/docs/study/notes/07-failure-point-checklist.md` 는 존재하지 않고
   실제 파일은 `jun-bank/docs-backup-2026-09-15/study/notes/07-failure-point-checklist.md`(78줄)다. 고친다.
3. `1-question.md` 의 「정답 파일 `3-answer.md`는 아직 없다 — 사용자 검토 후 확정한다」 문장을 현재 상태에 맞게 고친다.

## ② 경계·불변식

- **3-answer 는 repo 표준 형식을 따른다** — `# <주제> — 정답` + 「복습 시 이 파일은 **최후에만** 연다」 머리말 + `## 정답` + 번호별 답.
  본보기: `cs/engineering/solid-principles/3-answer.md` · `cs/systems/nand-flash/3-answer.md`.
- **B 의 정답은 원고 범위 안에서만 쓴다**(사용자 상시 규칙 — 「질문·정답은 원고 범위만」).
  원고에 없는 지식이 필요하면 `## [Claude 추가]` 절로 분리한다. 원고는 위 78줄짜리 절차 노트다.
- **A 의 요약본 수정은 「값 교정」까지다.** 문체·구성·절 순서를 바꾸지 않는다.
  SSD 내부(FTL·GC·Write Amplification)는 `cs/systems/nand-flash/` 가 정본이므로 접근 특성 수준까지만 다룬다 — 요약본이 이미 그렇게 선언했다.
- **질문 형식** — 「질문 하나 = "?" 하나 = 한 줄」, 세부 암기가 아니라 **지도 수준**(왜·예측·경계·연결).
  형제 주제의 질문 파일(`cs/systems/nand-flash/1-question.md` 등)을 본보기로 삼는다.
- **「Claude 초안」 경고를 달지 않는다**(사용자 확정 2026-09-20 — 확정본으로 쓴다).
  → 그래서 **틀린 값이 경고 없이 남는 것**이 이 작업의 주된 위험이다. ⑤-1 을 생략하지 않는다.
- 다른 주제·다른 갈래는 건드리지 않는다.

## ③ 기준소스

- A 요약본: `cs/systems/storage-media-workload/2-summary.md` (현재 내용)
- A 접지용 1차 출처: 제조사 데이터시트(HDD 스펙 시트의 탐색 시간·회전 속도, SSD 스펙 시트의 IOPS·지연),
  표준·1차 문서(NVMe·SATA 스펙, ATA 명령 집합), 학술·벤더 1차 자료.
  **2차 블로그·요약 기사는 값의 근거로 쓰지 않는다.**
- B 원고: `~/project/jun-bank/docs-backup-2026-09-15/study/notes/07-failure-point-checklist.md` (78줄) — **읽기만**
- B 요약본: `cs/engineering/failure-point-checklist/2-summary.md`
- 형식: `reference/study-note-guide.md` · `cs/engineering/solid-principles/3-answer.md` · `cs/systems/nand-flash/{1-question,3-answer}.md`

## ④ 금지영역

- `~/project/jun-bank/` 수정(원고는 읽기만).
- `cs/` 의 다른 주제, `history/`·`opensource/`·`portfolio/`·`lab/` 수정.
- B 의 정답에 원고 밖 지식을 `[Claude 추가]` 절 밖에 섞는 것.
- A 에서 확인하지 못한 수치를 그럴듯하게 적는 것 — **경고 줄이 없으므로 그대로 믿게 된다.**
- 커밋 메시지·발행 본문의 AI attribution.

## ⑤ 검증 방법

1. ★ **수치 접지(A)** — 요약본이 드는 값마다 1차 출처 URL 과 그 문서의 문장을 기록한다.
   확인 못 한 값은 **고치는 게 아니라 자릿수 표현으로 낮추거나 뺀다.** 검증 패스가 URL 을 직접 연다.
2. **원고 대조(B)** — 정답 10개의 각 항목이 원고의 어느 절·표 행에서 나왔는지 매핑한다.
   원고에 없는 문장은 `[Claude 추가]` 안에 있어야 한다.
3. **질문↔정답 대응(A·B)** — 질문 번호와 정답 번호가 1:1 인지, 질문이 묻는 것을 정답이 실제로 답하는지 훑는다.
4. **형식 린트** — 코드펜스 짝, 표 칸 수, 한 문장 한 줄, 머리말 형식, 복습 기록 표 존재.
5. **교차 참조 확인** — `nand-flash` 정본 선언과 겹치지 않는지, 링크가 실제로 존재하는 경로인지.
6. **검증 패스 분리** — 작성자와 컨텍스트가 분리된 워커가 1~5 를 점검한다.

## ⑥ stakes

**중간.**
되돌리기 쉽고(git) 불가역이 아니다.
다만 **「Claude 초안」 경고를 달지 않기로 했으므로**, 틀린 수치가 들어가면 경고 없이 정본으로 남아
나중에 그대로 인출 연습에 쓰인다. 그래서 ⑤-1(수치 접지)·⑤-2(원고 대조)는 생략하지 않는다.

## 자율성

**auto.**

## load-bearing 가정 (착수 직후 실증)

1. **요약본의 핵심 수치가 1차 출처로 접지된다.** — 먼저 HDD 탐색 시간·SSD 랜덤 읽기 지연 두 값으로 확인한다.
   상당수가 접지 불가면 사용자와 「자릿수 표현으로 낮출지」를 재협의한다.
2. **B 의 질문 10개가 원고 78줄 안에서 전부 답해진다.** — 착수 시 10문을 원고 절에 매핑해 확인한다.
   원고 밖으로 나가는 질문이 있으면 그 건만 `[Claude 추가]` 로 분리하고 보고한다.
