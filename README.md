# study-note

공부한 내용을 **인출(retrieval) 기반**으로 복습하기 위한 노트 저장소.
읽어서 익숙해지는 게 아니라, 기억에서 꺼내서 굳히는 것이 목적이다.

## 공부 루프

1. **입력 + 즉석 출력** — 직접 치고, 곱씹고, 자기 말로 다시 설명하면서 이해한다.
2. **압축 출력** — 챕터의 핵심을 "질문"으로 뽑는다. 무엇이 중요한지 판별하는 것 자체가 훈련이다.
3. **지연 출력** — 시간 간격을 두고(내일 → 사흘 → 일주일) 기억만으로 질문에 답한다.
   약간 힘들게, 잊기 직전에 꺼낼수록 세게 굳는다.

> 한 줄 요약: **출력의 비중을 최대로, 출력의 시점을 점점 늦게.**

## 폴더 구조

```
study-note/
├── README.md                  ← 이 파일 (색인 + 규칙)
├── templates/                 ← 1-question / 2-summary / 3-answer 포맷 템플릿
├── reference/                 ← 작성 지침 (organize-guide.md · writing/ — README 색인 + evidence 원재료 10개)
├── 세미나/                     ← 컨퍼런스·세미나 후기 (예: nerdcon/nerdcon-5.md)
└── <주제>/                     ← 예: db-engine-lab/, cs/
    ├── README.md              ← 그 주제의 공부 규칙
    ├── index.md               ← 챕터/주제 목록과 진행 상태 (상태 변경 시마다 갱신)
    └── <챕터>/                 ← 예: 08-01-wal-recovery/, solid-principles/
        ├── 1-question.md      ← 핵심 질문 목록
        ├── 2-summary.md       ← 흐름 정리 (힌트용)
        └── 3-answer.md        ← 정답
```

- 챕터 폴더명은 원본 자료(impl 문서 등)의 파일명을 그대로 따라 대응시킨다.
- 파일을 3개로 물리적으로 나눈 이유: 정답이 실수로 눈에 들어오는 경로를 없애기 위해서다.
- 새 챕터는 `templates/`의 세 파일을 복사해서 시작한다.
- 서머리 작성(따라 친 노트 → 정리본 융합) 규칙은 `cs/README.md`와 `reference/organize-guide.md`를 따른다.

## 복습 규칙 (접근 순서)

```
1-question.md 을 연다
  → 맨기억으로 답을 시도한다        ← 여기서 애쓰는 시간이 곧 각인
  → 막히면: 2-summary.md 를 힌트로 보고 다시 시도
  → 그래도 막히면: 3-answer.md 를 본다
  → 정답을 봤어도: 닫고 자기 말로 한 번 재산출한다
```

- **정리(summary)를 먼저 읽고 답하지 않는다.** 그건 인출이 아니라 방금 읽은 걸 받아쓰는 것이다.
- 정답까지 봤던 질문은 "틀림" 표시를 하고 다음 회차의 우선 대상으로 삼는다.

## 작성 규칙

- **질문은 지도 수준으로.** 세부 암기("TAG_INSERT 값은?")가 아니라
  왜(why) · 예측(what if) · 경계(어느 계층의 책임인가) · 연결(이전 챕터와의 다리) 질문으로 만든다.
- **정답은 기억에서 먼저 쓴다.** 원본 문서에서 복사하지 않는다.
  기억으로 쓰고 → 실제 코드로 검증하고 → 틀린 부분만 고친다. 기준 소스는 문서가 아니라 코드다.
- 질문과 정답은 직접 작성한다. 이 판별과 산출 과정이 효과의 절반이다.

## 복습 기록

각 챕터의 `1-question.md` 하단에 한 줄씩 기록한다:

```markdown
## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| 2026-08-15 | 5/7 | Q3, Q6 | 2026-08-18 |
```

## 주제 색인

| 주제 | 원본 | 진행 |
|------|------|------|
| [db-engine-lab](db-engine-lab/) | `/home/jun/project/db-engine-lab` (impl/ 01~21) | [index](db-engine-lab/index.md) |
| [cs](cs/) | 프로젝트 무관 CS·설계 지식 (기준 문서는 주제마다 지정) | [index](cs/index.md) |
| [algorithm](algorithm/) | `/home/jun/project/myway/algorithm` (01~30) | [index](algorithm/index.md) |
| [data-structure](data-structure/) | `/home/jun/project/myway/data-structure` (01~35) | [index](data-structure/index.md) |
| [domain-modeling-basic](domain-modeling-basic/) | `/home/jun/project/myway/domain-modeling-basic` (01~30) | [index](domain-modeling-basic/index.md) |
| [domain-modeling-advanced](domain-modeling-advanced/) | `/home/jun/project/myway/domain-modeling-advanced` (01~30) | [index](domain-modeling-advanced/index.md) |
| [ops-patterns](ops-patterns/) | `/home/jun/project/myway/ops-patterns` (01~19) | [index](ops-patterns/index.md) |
| [api-design](api-design/) | `/home/jun/project/myway/api-design` (01~06, 확정 체크리스트 훈련) | [index](api-design/index.md) |
| [programmers](programmers/) | 프로그래머스 고득점 Kit (유형 10 · 문제 47) — 1-question.md / 3-answer.md (2-summary 없음) | — |
| [study-note-deploy-system](study-note-deploy-system/) | 이 저장소를 배포하는 시스템의 이슈별 구현 기록 (backend·front·llm — 골격: templates/project-issue.md) | — |
| [세미나](세미나/) | 컨퍼런스·세미나 후기 — nerdcon-5 (2026-08-22, AI 시대 개발자 성장 방향) | — |
