# study-note

공부한 내용을 **인출(retrieval) 기반**으로 복습하기 위한 노트 저장소.
읽어서 익숙해지는 게 아니라, 기억에서 꺼내서 굳히는 것이 목적이다.

## 공부 루프

1. **입력 + 즉석 출력** — 직접 치고, 곱씹고, 자기 말로 다시 설명하면서 이해한다.
2. **압축 출력** — 챕터의 핵심을 "질문"으로 뽑는다. 무엇이 중요한지 판별하는 것 자체가 훈련이다.
3. **지연 출력** — 시간 간격을 두고(내일 → 사흘 → 일주일) 기억만으로 질문에 답한다.
   약간 힘들게, 잊기 직전에 꺼낼수록 세게 굳는다.

> 한 줄 요약: **출력의 비중을 최대로, 출력의 시점을 점점 늦게.**

이 루프가 남들이 정리한 방법론과 어디서 겹치는지, 왜 이렇게 하는지는 [reference/learning/](reference/learning/README.md)에 적는다 (출처 1: 박문호 「빅퀘스천」 — 대칭화·모듈화·순서화, 맥락 기억).

> **기록을 남기기 전에** — study-note에 무엇을 어떤 골격으로 쓰는지는 [reference/study-note-guide.md](reference/study-note-guide.md)에 모여 있다.\
> 다른 프로젝트에서 내용을 이관할 때(사람이든 에이전트든) 그 문서 하나만 읽으면 된다.\
> 단 **cs 주제의 작성 규칙은 [cs/README.md](cs/README.md) 「작성 규칙」이 정본**이다(2026-09-27 개정 — cs에 관해서는 가이드 전체보다 우선).

## 폴더 구조

```
study-note/
├── README.md                  ← 이 파일 (공부 루프 + 규칙)
├── index.md                   ← 전체 색인 (최상위 지도, 구조 변경 시 갱신)
├── templates/                 ← 1-question / 2-summary / 3-answer 포맷 템플릿
├── reference/                 ← 작성 지침 (★ study-note-guide.md — 작성법 정본 · organize-guide.md · render-rules.md · writing/ — 문서 작성 근거 · learning/ — 공부 방법론 · tools/)
├── cs/                        ← 개념 지식(1/2/3): 커리큘럼 19영역 README(생성 문서) + 기존 컬렉션 제자리(myway 5종·foundations·systems·engineering) (작성 규칙 정본: cs/README.md)
├── languages/                 ← 언어 레퍼런스: <언어>/syntax(문법·API 3파일)·<언어>/언어-특성·web-api — 13개 언어 (cs 밖, 2026-09-28 이동)
├── issue/                     ← 실전 이슈 → 재사용 CS 패턴 카드 156 (형식 정본: issue/authoring-guide.md)
├── practice/                  ← 훈련(문제→풀이): programmers
├── project/                   ← 만든 것의 기록: db-engine·study-note-deploy-system·jun-bank
├── lab/                       ← 실험 프로젝트 포트폴리오 9건 (프로젝트=폴더+README, 규칙: lab/README.md)
├── opensource/                ← 오픈소스 기여·코드 읽기: spring-framework·spring-security·elasticsearch·nextjs·react·mysql·postgres·keycloak·nginx·redis
├── portfolio/                 ← 대외용 정리 — project·lab에서 추려 산문으로 (k-brand-guard·markview)
├── history/                   ← 기술 변천사 8주제 (database·java·js·network·python·rust·spring·web)
├── workflow/                  ← 이 저장소 배포 시스템의 동작 흐름 문서
├── 세미나/                     ← 컨퍼런스·세미나 후기 (예: nerdcon/nerdcon-5.md)
├── 독후감/                     ← 책 후기 — 책=폴더, 챕터별 기록 (규칙: 독후감/README.md)
├── docs/                      ← 작업 기록(plans/날짜/작업명 — spec·log)·측정 로그·NEXT
└── <주제>/                     ← 예: cs/systems/lsm-tree/
    ├── README.md              ← 그 주제의 공부 규칙
    ├── index.md               ← 챕터/주제 목록과 진행 상태 (상태 변경 시마다 갱신)
    └── <챕터>/                 ← 예: 08-01-wal-recovery/, solid-principles/
        ├── 1-question.md      ← 핵심 질문 목록
        ├── 2-summary.md       ← 흐름 정리 (힌트용)
        └── 3-answer.md        ← 정답
```

- 챕터 폴더명은 원본 자료(impl 문서 등)의 파일명을 그대로 따라 대응시킨다.
- 파일을 3개로 물리적으로 나눈 이유: 정답이 실수로 눈에 들어오는 경로를 없애기 위해서다.
- 새 챕터는 `templates/`의 세 파일을 복사해서 시작한다 — 단 cs 주제는 `cs/README.md` 「작성 규칙」의 골격을 따른다.
- cs 작성 규칙(Claude 완성본·통일 골격·검수 상태)은 `cs/README.md`가 정본이다. 따라 친 노트를 융합하는 `reference/organize-guide.md`는 cs 외 폴더에만 적용한다.

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
- **cs 주제는 예외** — Claude 완성본으로 3파일을 모두 쓰고 배포 사이트에서 검수한다. 규칙 정본은 [cs/README.md](cs/README.md) 「작성 규칙」.

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
| [project/db-engine](project/db-engine/) | `/home/jun/project/db-engine` (impl/ 01~21) | [index](project/db-engine/index.md) |
| [cs](cs/) | 개념 지식 전반 — 커리큘럼 19영역(영역 README) + 기존 컬렉션 | [index](cs/index.md) |
| [cs/systems](cs/systems/) | 시스템 개념 8주제 — kafka-why-fast·lsm-tree·nand-flash·striping·straggler·partitioning-vs-sharding·thrashing·Hysteresis | [index](cs/index.md) |
| [cs/engineering](cs/engineering/) | 설계·기준 — solid-principles·development-standards(품질·보안·운영·법률) | [index](cs/engineering/development-standards/index.md) |
| [cs/foundations](cs/foundations/) | CS 기초 9주제(python-basics → languages/python/basics) — 컴퓨터사이언스 부트캠프 원고 이관(변수·데이터 표현·OOP·하드웨어·메모리·프로세스/스레드·컴파일러 등) | [index](cs/foundations/index.md) |
| [cs/algorithm](cs/algorithm/) | myway 컬렉션 (01~30) — 원본·진도: [project/myway](project/myway/README.md) | [index](cs/algorithm/index.md) |
| [cs/data-structure](cs/data-structure/) | myway 컬렉션 (01~35) — 원본·진도: [project/myway](project/myway/README.md) | [index](cs/data-structure/index.md) |
| [cs/domain-modeling/basic](cs/domain-modeling/basic/) | myway 컬렉션 (01~30) — 원본·진도: [project/myway](project/myway/README.md) | [index](cs/domain-modeling/basic/index.md) |
| [cs/domain-modeling/advanced](cs/domain-modeling/advanced/) | myway 컬렉션 (01~30) — 원본·진도: [project/myway](project/myway/README.md) | [index](cs/domain-modeling/advanced/index.md) |
| [cs/ops-patterns](cs/ops-patterns/) | myway 컬렉션 (01~19) — 원본·진도: [project/myway](project/myway/README.md) | [index](cs/ops-patterns/index.md) |
| [cs/api-design](cs/api-design/) | myway 컬렉션 (01~06, 확정 체크리스트 훈련) — 원본·진도: [project/myway](project/myway/README.md) | [index](cs/api-design/index.md) |
| [languages](languages/) | 언어별 문법·표준 API·언어 특성 + 브라우저 Web API 레퍼런스 (cs/foundations에서 이동) | [README](languages/README.md) |
| [issue](issue/) | 실전 이슈 → 재사용 CS 패턴 카드 아카이브 (하네스 issue-archive 대상 — 형식 정본: authoring-guide) | [index](issue/README.md) |
| [portfolio/k-brand-guard](portfolio/k-brand-guard/) | `/home/jun/project/resume` 경력기술서 - K-브랜드 지킴이 사례 5건 | [index](portfolio/k-brand-guard/index.md) |
| [portfolio/markview](portfolio/markview/) | `/home/jun/project/resume` 경력기술서 - MarkView 사례 3건 | [index](portfolio/markview/index.md) |
| [practice/programmers](practice/programmers/) | 프로그래머스 고득점 Kit (유형 10 · 문제 47) — 1-question.md / 3-answer.md (2-summary 없음) | — |
| [project/study-note-deploy-system](project/study-note-deploy-system/) | 이 저장소를 배포하는 시스템의 이슈별 구현 기록 (backend·front·llm — 골격: templates/project-issue.md) | — |
| [lab](lab/) | 실험 프로젝트 포트폴리오 — 캐시·동시성·프로토콜·분산 로그 등 8종 | [index](lab/index.md) |
| [opensource](opensource/) | 오픈소스 기여 아카이브 — spring-framework(머지 17건~)·spring-security·elasticsearch | [index](opensource/index.md) |
| [세미나](세미나/) | 컨퍼런스·세미나 후기 — nerdcon-5 (2026-08-22, AI 시대 개발자 성장 방향) | — |
| [독후감](독후감/) | 책 후기 — 아키텍트-첫걸음 (읽는 중) | [index](독후감/index.md) |
