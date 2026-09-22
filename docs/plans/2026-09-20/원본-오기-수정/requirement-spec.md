# 요구사항 명세 — 원본 history repo 오기·불일치 수정

작성 2026-09-20 · 대상: `~/project/{network,rust,python,java}-history` 4개 repo
후속: `docs/plans/2026-09-18/history-이관/log.md` 의 「상류(원본 repo) 수정 요청」 표

## ① 목표·대상

이관 작업 중 재서술본에 「재서술자 주:」로만 표기하고 원본은 읽기만 했던 결함을 **원본 쪽에서 고친다.**

표는 31행이며(로그 본문의 「25건」은 집계 오류 — 이 작업에서 정정한다), 사용자 확정 범위는 **A+B 26건**이다.

### A · 명백한 오기·아티팩트 5건 (판단 불필요)

| # | 파일 | 고칠 것 |
|---|------|---------|
| A1 | `java-history/java/jdk-1.4.md` L10 | `JСР` 의 `С`·`Р` 가 키릴(U+0421·U+0420) → 라틴 `JCP` |
| A2 | `rust-history/06-핵심-개념-진화.md` 끝 | `</content>`·`</invoke>` 두 줄 삭제 |
| A3 | `rust-history/06-핵심-개념-진화.md` §4 | 「까지 않고」 → 「꺼내 보지 않고」 |
| A4 | `network-history/03-주소-DNS-라우팅.md` | `게이트마스크` → 문맥에 맞는 말로 |
| A5 | `python-history/03-현대-Python.md` 표 | 코드 스팬 안 `\|` 가 GFM 표 칸을 잘라 3.9·3.10 행 렌더링이 깨짐 → 이스케이프 |

### B · 내부 불일치 21건 (1차 출처로 값을 확정한 뒤 고친다)

network 1 · rust 3 · python 5 · java-history/spring 8 · java-history/java 4

| # | 파일 | 충돌 |
|---|------|------|
| B1 | `network-history/03-주소-DNS-라우팅.md` | 제목 「세 층」 vs 본문 「이 네 층은」 vs 표 4행 |
| B2 | `rust-history/03-소유권-시스템.md` L13·L136·L142 | lexical 시기 `~2018` / `~2015` / `1.0 ~ 2018` |
| B3 | `rust-history/02-에디션.md` | `async` 문법(1.39 전 에디션) vs 키워드 예약(2018 에디션) |
| B4 | `python-history/03-현대-Python.md` 3.6\~3.7 | 같은 `x: int` 를 「인스턴스 속성」 / 「클래스 변수」 |
| B5 | `python-history/03-현대-Python.md` | 「두 가지다」인데 불릿 셋 |
| B6 | `python-history/03-현대-Python.md` f-string | 산문 3가지와 코드 3가지의 구성원이 다름 |
| B7 | `python-history/05-데이터-ML-생태계.md` L3·L220·L222 | 「20여 년」 / 「30년 전 NumPy」 / 「30년」 |
| B8 | `python-history/06-핵심-개념-진화.md` L199 | PEP 342 연도 2005(작성) → 릴리스 연도 규칙상 2006 |
| B9 | `java-history/spring/boot-2.x.md` | 2.3 OCI 이미지 빌드의 빌드 도구 한정어가 세 곳 다름 |
| B10 | `java-history/spring/kotlin-and-spring.md` | 「플러그인 역할」 목록에 `dependencies` 항목이 섞이고 `kotlin-reflect` 누락 |
| B11 | `java-history/spring/boot-2.x.md` L115 | `runApplication` 을 「확장 함수」라 적음 (최상위 reified 함수) |
| B12 | `java-history/spring/README.md` ↔ `boot-3.x.md` | 타임라인이 3.1\~3.4 까지인데 본문은 3.5 |
| B13 | `java-history/spring/framework-4.x.md` | 4.0 을 2013-12 로 적고 배경은 2014-03 Java 8 에 맞췄다고 적음 |
| B14 | `java-history/spring/framework-7.x.md` L124↔L136 | 서버 `/account/{id}` vs 클라이언트 `/accounts/1` |
| B15 | `java-history/spring/framework-6.x.md` ↔ `7.x` | 「jakarta 전면 교체」 vs 「6.x 가 남긴 잔여 javax」 |
| B16 | `java-history/spring/framework-7.x.md` L10↔L154 | Hibernate 「7.1+」 vs 「7+」 |
| B17 | `java-history/java/java-17.md` | 같은 절에서 `Shape` 의 `permits` 목록이 넷 다 다름 |
| B18 | `java-history/java/jdk-1.2.md` L48 | `diamond` 를 J2SE 5.0 이라 적음 (Java SE 7) |
| B19 | `java-history/java/java-9.md` ↔ `java-11.md` | `BodyHandler.asString()` vs `BodyHandlers.ofString()` |
| B20 | `java-history/java/java-12.md` | switch 표현식 정식화 시점(Java 14, JEP 361) 누락 |
| B21 | `java-history/java/java-25.md` L35 | Scoped Values 를 「22\~24」로 세어 21의 1차 프리뷰 누락 |

### 손대지 않는 것 (사용자 확정)

- **C · 관점 차이 4건** — java-5↔8 LTS 기준점 · java-14 릴리스 모델 전환 · framework-3.x `@RestController` · java-18 lead 의 Loom 과포함.
- **D · 보류 1건** — `rust-history/01-탄생-1.0.md` 절 제목 (2010\~2012) vs 본문 (2009\~2012).

### 후속 (같은 작업에 포함)

원본을 고친 뒤 **study-note 재서술본의 「재서술자 주:」 블록을 정리한다** — 고쳐진 건의 주는 제거하고, 원본과 재서술본이 어긋나게 된 값이 있으면 재서술본도 맞춘다.

## ② 경계·불변식

- **저자의 서술 선택을 바꾸지 않는다.** 고치는 것은 *값이 어긋난 자리*와 *오기*뿐이다. 문체·구성·설명 방식은 그대로 둔다.
- **최소 개입.** 한 건당 고치는 범위는 그 문장·표 칸·코드 줄까지. 절을 다시 쓰지 않는다.
- B는 **어느 쪽이 맞는지 1차 출처로 확정한 뒤** 고친다. 확정하지 못하면 고치지 않고 「확정 실패」로 보고한다 — 추정으로 값을 넣지 않는다.
- 4개 repo 각각 **브랜치를 따서** 작업한다(main 직접 작업 금지). 커밋은 repo별로, push 는 사용자 확인 후.
- `java-history` 의 untracked (`.idea/`·`.mcp.json`·`docs/`) 는 스테이징하지 않는다.

## ③ 기준소스

- 결함 목록: `docs/plans/2026-09-18/history-이관/log.md` 「상류 수정 요청」 표
- 원문: `~/project/{network,rust,python,java}-history/**.md`
- 값 확정용 1차 출처 — JEP/JSR 페이지 · PEP 색인 · `rust-lang/rust` RELEASES.md · Rust 블로그 · Spring 공식 문서/블로그 · Python `whatsnew` · NumPy 릴리스 이력 · 각 repo 자신의 다른 편(문서 간 불일치는 repo 내부 대조로 확정되는 경우가 있다)
- 재서술본: `study-note/history/**`

## ④ 금지영역

- C·D 5건 수정.
- 원본 repo 의 문서 추가·삭제·재구성.
- `study-note` 의 `cs/`·`portfolio/`·`lab/`·`opensource/` 수정.
- 확정하지 못한 값을 추정으로 채우는 것.
- 커밋 메시지·발행 본문의 AI attribution.

## ⑤ 검증 방법

1. **1차 출처 접지(B 전건)** — 고친 값마다 URL 과 그 문서의 해당 문장을 기록한다. 검증 패스가 URL 을 직접 열어 대조한다.
2. **repo 내부 재대조** — 고친 뒤 같은 repo 안에서 그 값이 나오는 모든 자리를 grep 해 한 값으로 수렴했는지 확인한다(B 는 「한 곳만 고쳐 다른 곳과 또 어긋나는」 실패가 나기 쉽다).
3. **diff 전수 리뷰** — 26건 외의 변경이 섞이지 않았는지 `git diff` 를 줄 단위로 훑는다. 의도 외 변경 0 이어야 한다.
4. **렌더 확인(A5)** — GFM 표가 실제로 4칸으로 갈라지는지 확인한다.
5. **재서술본 동기화 확인** — 제거한 「재서술자 주」마다 원본이 실제로 고쳐졌는지 대조한다. 안 고친 건(C·D)의 주는 **남아 있어야** 한다.
6. **검증 패스 분리** — 작성자와 컨텍스트가 분리된 워커가 1\~5 를 점검한다.

## ⑥ stakes

**중간.**
되돌리기 쉽고(git, 4 repo 모두 clean 에서 출발) 불가역이 아니다.
다만 **「고친다」면서 틀린 값을 넣으면 원본이 오염된다** — 지금은 「문서 안에서 어긋난다」이지만 잘못 고치면 「틀린 값으로 통일됐다」가 되어 더 찾기 어렵다. 그래서 ⑤-1·⑤-2 는 생략하지 않는다.

## 자율성

**auto.**

## load-bearing 가정 (착수 직후 실증)

1. **B 21건의 값이 1차 출처로 확정 가능하다.** — 먼저 java 4건(diamond·permits·BodyHandlers·switch 정식화)으로 확인한다. 확정 안 되는 건이 절반을 넘으면 사용자와 범위를 재협의한다.
2. **로그 표의 줄 번호·인용이 현재 원본과 일치한다.** — 착수 시 `sed -n` 으로 전건 재출력해 확인한다. 표 작성 이후 원본이 바뀌었을 수 있다.
