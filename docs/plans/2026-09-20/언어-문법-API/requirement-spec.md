# 요구사항 명세 — 언어별 문법·API 학습 자료

작성 2026-09-20 · 대상: `cs/foundations/languages/syntax/` (신설)

## ① 목표·대상

언어 **8개**의 문법과 표준 API 를 **기능 단위**로 쪼개 3파일(질문·서머리·정답) 학습 자료로 만든다.

대상 **11개**: **C · C++ · C# · Go · Java · Kotlin · Rust · SQL · Python · JavaScript · TypeScript** (사용자 확정 2026-09-20)
기존 `languages/` 에 판단 기준 노트가 있는 7개(C·C++·C#·Go·Java·Kotlin·Rust)도 문법 쪽을 함께 만든다.

### 기존 `languages/` 와의 관계 — 축이 다르다

`cs/foundations/languages/` 의 기존 5개 노트(`c-cpp-csharp`·`go`·`java-jvm`·`kotlin`·`rust`)는
**「어떤 언어를 고를 것인가」** 를 다루는 판단 기준 노트다. 문법·API 자료가 아니다.
그래서 **폴더 경계로 가른다**(사용자 확정):

**언어 우선**으로 폴더를 잡고, 그 안에서 축을 가른다(사용자 확정 2026-09-20).

```text
cs/foundations/languages/
├── README.md                    두 축 안내
├── c-cpp-csharp.md              ← 세 언어를 한 파일에서 비교하므로 언어 폴더 밖에 남긴다
├── java/
│   ├── 언어-특성/README.md       ← 옛 java-jvm.md (내용 무수정, 링크만 갱신)
│   └── syntax/
│       ├── README.md            리스트업·우선순위·진행 현황
│       └── NN-<slug>/{1-question,2-summary,3-answer}.md
├── kotlin/ · go/ · rust/        ← 같은 모양 (기존 노트를 언어-특성/README.md 로 이동)
├── c/ · cpp/ · csharp/          ← syntax/ 만. 언어-특성은 위 비교 노트를 가리킨다
└── sql/ · python/ · js/ · ts/   ← syntax/ 만 (판단 기준 노트 없음)
```

`java/언어-특성/`(고를 때) ↔ `java/syntax/`(쓸 때)로 이름에서 갈린다.
**이 이동은 2026-09-20에 완료했다** — git rename 4건, 상대 링크 39개 전수 검사 후 깨짐 0.

### 단계

- **1단계 — 리스트업(이번 산출물).** 언어별 주제 후보를 전수로 뽑아 분류·우선순위·선행관계를 적고,
  기존 주제(`cs/**`·`history/**`)와 겹치는 곳을 표시한다. `syntax/README.md` + 언어별 `README.md`.
- **2단계 — 3파일 작성.** 1단계 목록을 사용자와 확정한 뒤 **배치로** 쓴다. 배치 단위·순서는 1단계 결과를 보고 정한다.

**이 명세는 1단계를 구속하고, 2단계는 목록 확정 후 재합의한다.**
규모가 **11개 언어 × 40\~60주제 = 440\~660주제 × 3파일 ≈ 1,300\~2,000파일**이라 한 번에 승인할 대상이 아니다 — history 이관 전체(83편)의 대여섯 배다.

## ② 경계·불변식

- **기능 단위**(사용자 확정) — 문법·API 하나가 한 주제. 언어당 40\~60주제를 기준선으로 잡되, 언어마다 실제 면적에 맞춘다.
- **기존 주제와 중복해 쓰지 않는다.** `cs/algorithm`·`cs/data-structure`·`cs/systems`·`history/**` 에 이미 있는 것은
  **목록에 「기존 주제 있음」으로 표시하고 링크**한다. 예: 자료구조 자체는 `data-structure/`, 언어 역사는 `history/`.
- **판단 기준 노트 5개는 건드리지 않는다.** `languages/README.md` 만 두 갈래 안내로 갱신한다.
- 3파일 형식은 repo 표준을 따른다 — `templates/{1-question,2-summary,3-answer}.md`,
  본보기 `cs/data-structure/01-dynamic-array/`.
- 폴더명은 `NN-<slug>` 2자리 번호 + 영문 kebab-case (기존 `cs/algorithm`·`cs/data-structure` 관례).

## ③ 기준소스

각 언어의 **1차 명세·공식 문서**만 기준으로 삼는다. 2차 블로그·요약 기사는 값의 근거로 쓰지 않는다.

| 언어 | 1차 기준 |
|---|---|
| C | **ISO/IEC 9899**(공개 초안), cppreference C 레퍼런스 |
| C++ | **ISO/IEC 14882**(공개 초안), cppreference |
| C# | **ECMA-334** / Microsoft Learn 공식 언어 레퍼런스 |
| SQL | ISO/IEC 9075 계열의 공개 요약 + **PostgreSQL 공식 문서**·**MySQL 공식 문서**(방언 차이는 둘로 대조) |
| Java | **Java Language Specification**, **Java SE API 문서**(21 기준, 17·25 차이 표기), JEP |
| Kotlin | **kotlinlang.org** 언어 레퍼런스·표준 라이브러리 API |
| Python | **docs.python.org** 언어 레퍼런스·표준 라이브러리, **PEP** |
| Go | **go.dev/ref/spec**, `pkg.go.dev` 표준 라이브러리 |
| Rust | **The Rust Reference**, **std 문서**, Rust By Example |
| JavaScript | **ECMA-262**(해당 판), **MDN**(웹 API 한정) |
| TypeScript | **TypeScript Handbook**·릴리스 노트(공식) |

## ④ 금지영역

- 기존 판단 기준 노트 5개 수정.
- `cs/` 의 다른 갈래, `history/`·`opensource/`·`portfolio/`·`lab/` 수정.
- **실행해 보지 않은 코드 예시를 「동작한다」로 적는 것**(⑤-2 참조).
- 버전 의존 기능을 버전 표기 없이 적는 것(Java record·sealed, Python match, TS satisfies 등).
- 커밋 메시지·발행 본문의 AI attribution.

## ⑤ 검증 방법

1. **1차 출처 접지** — 문법 규칙·API 시그니처·동작은 위 ③ 문서로 확인하고 출처를 남긴다.
2. ★ **코드 예시 실행 검증** — 실행 가능한 언어는 **실제로 돌려 출력을 확인**한다.
   현재 이 머신에서 **가능**: Java(sdkman 17·21·25, `javac` 있음) · Python 3.12.3 · Rust 1.92.0 + cargo · Node 18·20.
   현재 **불가**: Kotlin · Go · TypeScript(`npx tsc` 로 가능할 수 있음) · SQL(sqlite3·psql·mysql 모두 없음).
   → 불가한 언어는 **「실행 검증 안 됨」을 명시**한다. 지어내지 않는다.
   → 도구 설치는 사용자 환경 변경이므로 **임의로 하지 않고 제안만** 한다.
   → ★ **코드 예시는 직접 쓴 최소 예제**로 한다. 규칙·시그니처는 공식 문서로 접지하되
     **문서의 예제를 통째로 옮기지 않는다** — 짧은 인용은 규칙 문장에 한한다.
3. **버전 표기 검사** — 버전에 따라 달라지는 것은 어느 버전부터인지 적었는지 전수 확인.
4. **중복 검사** — 기존 `cs/**`·`history/**` 와 겹치는 주제가 목록에 링크 없이 들어가지 않았는지.
5. **형식 린트** — 3파일 구조, 코드펜스 짝, 표 칸 수, 복습 기록 표, 한 문장 한 줄.
6. **검증 패스 분리** — 작성자와 컨텍스트가 분리된 워커가 1\~5 를 점검한다.

## ⑥ stakes

**중간.**
되돌리기 쉽고(git) 불가역이 아니다.
다만 **학습 자료라 틀린 문법·API 설명이 그대로 인출 연습에 쓰인다.** 그리고 규모가 커서
한 번 잘못된 형식·분류로 대량 생산하면 되돌리는 비용이 크다 —
그래서 **1단계(리스트업)를 사용자와 확정한 뒤에 2단계로 간다.**

## 자율성

**auto.**

## load-bearing 가정 (착수 직후 실증)

1. **기능 단위로 쪼개면 언어당 40\~60주제 선에 들어온다.** — Java·SQL 두 언어로 먼저 뽑아 확인한다.
   크게 벗어나면(100주제 초과 등) 묶음 크기를 사용자와 재협의한다.
2. **기존 주제와의 중복이 관리 가능한 수준이다.** — 리스트업 때 `cs/**` 제목을 전수 대조해 확인한다.
   중복이 많으면 「새로 쓸 것」과 「기존을 가리킬 것」의 경계를 먼저 정한다.
