# log — history 아카이브 이관

## 2026-09-18

| 시각 | 사건 | 결과 |
|---|---|---|
| — | 사용자 인터뷰 → requirement-spec.md 6칸 합의, 자율성 auto | SPEC=1 / MODE=auto |
| — | 브리핑 작성 `scratchpad/easy-rewrite/briefing-history.md` | 출력 골격 + 필수 5규칙 + 자체 검증 |
| — | database 6편 + README 재서술 (작성 워커 2) | 3,272줄 / 도식 61 / 용어 블록 124 |
| — | 작성 워커 자체 검증 | 사실 토큰 누락 0, 원문 코드블록 12개 일치, mermaid 5→ASCII 노드 보존 |
| — | Fable 검증 패스 01\~03 (작성자와 분리) | 높음 1 · 중간 5 · 낮음 13. 판정 "조건부 안전" |
| — | Fable 검증 패스 04\~06·README | S1(사실 왜곡) 0 · S2 7 · S3 17 · S4 0. 인용 층 오류 0건 |
| — | 브리핑에 규칙 A·B 추가 (도식 화살표 근거 / 보충 층 머리말 일괄 선언) | 79편 확장 전 파이프라인 보강 |
| — | 수정 워커 2개 병렬 (01\~03 / 04\~06·README) | 지적 전건 처리, 보류 0 |
| — | 02 §남긴 것 Redis 줄 (워커 보고분) 메인이 직접 처리 | `*(Claude 보강)*` 선언 부착 |
| — | 브리핑에 규칙 C + 검증 패스 규칙 추가 | 「갈림길·대가」 절 근거 의무 / 새 층만 읽는 리뷰 패스 |
| — | 형식 린트 7편 | 코드펜스 전부 짝수, 펜스 내 하드브레이크 0건 |
| — | 사용자 톤 확인 → database 커밋(114f3e1) + 명세·로그 커밋(9cd0737) | 확장 승인 |
| — | web 6편+README 작성 완료 | 원문 1,424 → 4,016줄 / 도식 86 / 용어 168 |
| — | Fable 검증 2패스 (01\~03 / 04\~06·README) | 지적 49건. **S1 1건**(01 「남긴 것」에서 표준화 방향이 원문과 정반대) |
| — | 검증에서 규칙 9개 추가 도출 → 브리핑 병합 | C′·D·E·F·G·H·I·J·K + A·B 보강. 맨 앞에 「제출 전 전수 훑기 6가지」 |
| — | 수정 워커 2개 병렬 | 지적 49건 전건 처리, 보류 0 |
| — | web 커밋 8eb93f9 | 4,037줄 |
| — | network 6편+README 워커 2개 착수 | 진행 중 |

## 리뷰 ledger

- 주제마다 Fable 검증 2패스(작성 워커와 컨텍스트 분리). 지적 원문은 세션 task 출력에 보존.

**두 주제 13편 누적 실측 — 일관됨:**

| 주제 | 인용 층 오류 | 새 층 지적 | S1 |
|---|---|---|---|
| database 7편 | **0건** | 26건 | 0 |
| web 7편 | **0건** | 49건 | 1 |

- 인용 항목(연도·인명·논문명·RFC·표준번호·코드블록·표)은 두 번 다 오류 0건. 기계 대조로 걸러진다.
- 지적 75건이 **전부 재서술자가 새로 만든 층**(도식·「갈림길」 표·「대가는 무엇인가」·「남긴 것」)에서 났다.
- **위험 지표는 총 증량 배율이 아니라 「새 층 ÷ 원문」 비율이다.** web 실측: 1.2\~1.5배 문서는 S1 0건, 2.7배 문서에서 S1과 인과 날조가 몰려 나왔다.
- 원인은 **원문의 성격**이다. 메커니즘형 원문(절차·전후 대비)은 도식이 원문 서술을 재렌더링할 뿐이라 안전하고, 서사형 원문(사건 나열)은 그릴 메커니즘이 없어 재서술자가 사건 *사이*를 그리다 없는 관계를 지어낸다.
- 규칙은 12개로 확장(A\~K + 보강). 워커가 다 내면화하기 어려워 브리핑 맨 앞에 「제출 전 전수 훑기 6가지」를 별도로 뒀다.

## 생략한 검증

없음(빚 없음). ⑤-1 사실 토큰 대조·⑤-2 코드블록 대조는 작성 워커 자체 검증 + Fable 기계 대조로 2중 수행.

## 상류(원본 repo) 수정 요청

§7-A.11 에 따라 원문의 오기·자기모순은 고치지 않고 재서술본에 「재서술자 주:」로 표기했다. 원본 쪽에서 정합을 맞춰야 할 건들이다.

| 원본 파일 | 위치 | 내용 |
|---|---|---|
| `~/project/network-history/03-주소-DNS-라우팅.md` | — | 제목은 「세 층」인데 본문은 「이 네 층은」이고 표는 4행이다. 「세 가지 질문 / 네 메커니즘 / 다섯 변화」로 읽으면 3·5는 설명되나 「세 층」 제목과 「네 층은」이 충돌한다 |
| `~/project/network-history/03-주소-DNS-라우팅.md` | — | `게이트마스크` — 게이트웨이·서브넷 마스크의 오기로 보인다 |
| `~/project/rust-history/03-소유권-시스템.md` | L13 / L136 / L142 | 같은 단계의 시기가 세 곳에서 다르다 — 「한눈에 보기」 표 `(lexical, ~2018)` · mermaid `(lexical, ~2015)` · 절 제목 `(AST 기반, 1.0 ~ 2018)` |
| `~/project/rust-history/06-핵심-개념-진화.md` | 파일 끝 | `</content>`·`</invoke>` 두 줄이 붙어 있다 — 문서 내용이 아니라 저장 과정의 흔적으로 보인다 |
| `~/project/rust-history/06-핵심-개념-진화.md` | §4 | 「`Result`에는 `#[must_use]`가 붙어, **까지 않고** 버리면」 — 「꺼내 보지 않고」의 오기로 보인다 |
| `~/project/rust-history/02-에디션.md` | — | 「1.39에서 **모든 에디션에 동시에**」·mermaid 「(전 에디션)」 과, 같은 문서 2015 절의 「`let async = 1;` 합법 / 아직 키워드가 아니어서」가 모순이다. `async`/`await` **문법**은 1.39부터 전 에디션이지만 `async` **키워드 예약**은 2018 에디션부터다 |
| `~/project/rust-history/01-탄생-1.0.md` | 3)절 | 절 제목 「자체 호스팅 컴파일러와 첫 공개 릴리스 **(2010 \~ 2012)**」 vs 같은 절 본문 「**2009년부터 2012년 사이**」 — 제목의 범위가 절 전체의 대략 구간일 수 있어 단정은 보류 |
| `~/project/python-history/03-현대-Python.md` | 3.6\~3.7 | 같은 `x: int` 줄을 코드 주석은 「**인스턴스 속성** 어노테이션」, 바로 아래 3.7 본문은 「**클래스 변수** 어노테이션」이라 부른다 |
| `~/project/python-history/03-현대-Python.md` | — | 「주된 기법은 **두 가지**다」라 적고 불릿은 **셋**이다 |
| `~/project/python-history/03-현대-Python.md` | f-string 절 | 산문의 세 가지(`%`·`str.format()`·`string.Template`)와 코드의 세 가지(`%`·`.format()`·`.format(n=…)`)가 **구성원이 다르다** |
| `~/project/python-history/03-현대-Python.md` | 표 | 코드 스팬 안의 파이프(`` `X \| Y` ``)가 GFM 표 칸을 잘라 3.9·3.10 행 렌더링이 깨진다 |
| `~/project/python-history/05-데이터-ML-생태계.md` | L3·L220·L222 | 「20여 년」 / 「30년 전 NumPy」 / 「30년」이 서로 어긋난다(같은 문서가 NumPy 1.0을 2006년이라 적는다) |
| `~/project/python-history/06-핵심-개념-진화.md` | L199 | 「PEP 342, Python 2.5 / **2005**」 — 2005는 PEP 작성 연도다. 같은 절 다른 행은 전부 릴리스 연도라 2006이 규칙에 맞다 |
| `~/project/java-history/spring/boot-2.x.md` | 「릴리스 정보」 2.3 / 「마이너 버전별 변화」 2.3 / 「그 외」 | 같은 2.3 기능의 빌드 도구 한정어가 셋 다 다르다 — 「릴리스 정보」는 「**그레이들 기반** OCI 이미지 빌드(Buildpacks)」, 「마이너 버전별 변화」는 「Buildpacks 이미지 빌드」, 「그 외」가 드는 명령은 메이븐 `mvn spring-boot:build-image` 다 |
| `~/project/java-history/spring/kotlin-and-spring.md` | 「플러그인 역할」 목록 | 표제는 「**플러그인** 역할」인데 셋째 항목 `jackson-module-kotlin` 은 `plugins` 가 아니라 `dependencies` 블록이고, 같은 블록의 `kotlin-reflect` 는 목록에 없다 |
| `~/project/java-history/spring/boot-2.x.md` | L115 코드 주석 | 「Boot 가 제공하는 Kotlin **확장 함수**」(`runApplication`) — 확장 함수가 아니라 **최상위 reified 함수**로 보인다. 같은 repo 의 `kotlin-and-spring.md` 가 확장 함수를 정확히 정의·예시하므로 문서 간 불일치다 |
| `~/project/java-history/spring/README.md` ↔ `boot-3.x.md` | 「전체 타임라인」 2022\~ 행 | README 는 Boot 를 「3.0 / 3.1\~3.4」까지 적는데 `boot-3.x.md` 는 **3.5(2025-05)** 까지 다룬다 |
| `~/project/java-history/spring/framework-4.x.md` | 「릴리스 정보」 ↔ 「시대적 배경」 | 「릴리스 정보」는 4.0 을 **2013-12**로 적는데 「시대적 배경」은 「**2014년 3월** Java 8 이 출시되며 … Spring 4.0 은 이 변화에 맞춰 … 정비」라 적어, 4.0 이 Java 8 보다 석 달 앞선다. 원문 참고 출처의 *Spring Framework 4.0.3 released - Java 8 support production-ready*(2014-03)로 보아 4.0 에서 시작해 4.0.x 에서 완성된 지원을 한 문단으로 묶은 것으로 보인다 |
| `~/project/java-history/spring/framework-7.x.md` | L124 ↔ L136 (API 버저닝 절) | 같은 절의 코드블록 사이에서 경로가 다르다 — 서버 `@GetMapping(path = "/account/{id}", version = "1.1")` vs 클라이언트 `.uri("/accounts/1")` |
| `~/project/java-history/spring/framework-6.x.md` ↔ `framework-7.x.md` | 6.x L23·L143 / 7.x L151·L157 | 6.x 는 「Servlet, JPA, …, Annotations 등 **모든 표준 API import 가 바뀐다**」·「`jakarta.*` 로 **전면 교체**」라 적는데, 7.x 는 「**6.x 가 남겨둔 잔여 `javax.*`**」(`javax.annotation`·`javax.inject`)를 7.0 이 마저 정리한다고 적는다 |
| `~/project/java-history/spring/framework-3.x.md` | 「Spring MVC의 REST 지원」 흐름 서술·mermaid `alt`/`else` 라벨 | MVC 흐름 예제가 `@RestController` 를 쓰는데 `framework-4.x.md` 는 이를 **4.0 도입**으로 적는다. 3.x 편만 읽는 독자가 3.x 기능으로 오인할 수 있다 |
| `~/project/java-history/spring/framework-7.x.md` | L10 ↔ L154 | 「Hibernate ORM **7.1+**」(「릴리스 정보」의 권장 런타임) vs 「Hibernate ORM **7+**」(「마이그레이션 관점」) |
| `~/project/java-history/java/java-17.md` | 「sealed 클래스 정식화 (JEP 409)」·「switch 패턴 매칭 (JEP 406)」 절 | 같은 절 안에서 `Shape` 의 `permits` 목록이 넷 다 다르다 — 코드블록은 `permits Circle, Rectangle`, 바로 아래 mermaid classDiagram 은 `Circle`·`Square`·`Triangle`, switch 코드블록은 `case Circle c`/`case Rectangle r`, 그 아래 mermaid flowchart 는 `case Circle c`/`case Square s`/`case Triangle t` 다. 각각 다른 예로 든 것으로 보이나 같은 타입 이름이라 초보자에게 모순으로 읽힌다 |

| `~/project/java-history/java/jdk-1.2.md` | L48 코드 주석 | 「제네릭·diamond·for-each·오토박싱은 모두 J2SE 5.0부터다」 중 `diamond` 만 어긋난다 — `java-7.md` 가 「다이아몬드 연산자 (Diamond Operator, `<>`)」를 자기 절로 두고 `README` 표도 diamond 를 Java SE 7 행에 적는다. 나머지 셋(제네릭·for-each·오토박싱)은 `java-5.md` 와 맞는다 |
| `~/project/java-history/java/jdk-1.4.md` | L10 | 「참고: JСР(Java Community Process)…」의 `С`·`Р` 가 라틴 문자가 아니라 키릴 문자다(U+0421·U+0420). 같은 괄호가 "Java Community Process"로 풀어 적으므로 `JCP` 의 표기 오류로 보인다 — 겉모습이 같아 눈으로는 안 보이고 grep 에서만 어긋난다 |
| `~/project/java-history/java/java-5.md` ↔ `java-8.md` | java-5 L11 ↔ java-8 L10 | LTS 도입 기준점이 다르게 적힌다 — java-5 는 「LTS는 Java 8 이후 도입」, java-8 은 「현대적 LTS 모델(**Java 11부터 시작**) 이전 버전」, `README` 는 LTS 목록에 Java 8 을 포함한다. 소급 지정 vs 모델 시작으로 기준점을 나누면 설명되나 한 문장씩만 읽으면 충돌로 읽힌다(저강도 — 재서술본에는 교차 주로만 달았다) |
| `~/project/java-history/java/java-9.md` ↔ `java-11.md` | 9편 HTTP/2 클라이언트 절 코드 ↔ 11편 표준 HTTP 클라이언트 절 코드 | 같은 자리의 API 이름이 다르다 — 9편 `HttpResponse.BodyHandler.asString()` vs 11편 `HttpResponse.BodyHandlers.ofString()`. 인큐베이터 → 정식화 과정의 이름 변경으로 보이나 두 편 모두 그 사실을 적지 않아, 한 편만 읽으면 오타로 읽힌다 |
| `~/project/java-history/java/java-12.md` | 「switch 표현식 (JEP 325)」 절 | 12편은 1차 preview 와 "이후 Java 13의 2차 preview에서 `yield`로 대체된다"까지만 적고 **정식화 시점(Java 14, JEP 361)** 은 적지 않는다. 13편은 "(Java 14에서 정식화)", 14편은 "12·13의 두 차례 preview를 거쳐 정식 기능으로 확정됐다"라 적는다 |
| `~/project/java-history/java/java-14.md` ↔ `java-9.md`·`java-10.md` | 14편 「시대적 배경」 첫 문장 ↔ 9편·10편 「시대적 배경」 | 14편은 "Java는 9 버전부터 6개월 주기 릴리스 모델로 전환했고"라 적는데, 9편은 "Java 9는 옛 모델의 **마지막** 메이저 릴리스가 되었고, 6개월 뒤 Java 10(2018년 3월)이 새 모델의 **첫** 릴리스로 나왔다", 10편은 "Java 10이 그 첫 결과물"이라 적는다 (발견: java-7\~13 워커. 14편은 다른 워커 담당) |
| `~/project/java-history/java/java-25.md` | L35 | Scoped Values 절이 경로를 「**22\~24의** 여러 프리뷰를 거쳐」로 적어 `java-21.md` 의 1차 프리뷰(JEP 446)를 빠뜨린다. `java-21.md` L237 이 그 절을 「Scoped Values (JEP 446, Preview/1차 프리뷰)」로 적고 `java-24.md` 는 JEP 487 을 「4차 프리뷰」로 세므로, 1차부터 세면 21\~24 다 (발견: java-21\~26 워커) |
| `~/project/java-history/java/java-18.md` | lead(L3) ↔ L16·L18 | lead 가 「동시에 **Loom**/Panama/Amber 프로젝트의 프리뷰·인큐베이터 기능들이 다음 단계로 진행되었다」인데, L16 은 「Project Loom … 18에서는 **아직 직접적인 기능이 들어오지 않았지만**」, L18 은 「이 중 **Amber와 Panama**의 진행」이라 적는다 — lead 가 Loom 을 과포함한다. 본문이 바로 바로잡고 있어 재서술본에는 주를 달지 않았다 |


원본을 고치면 재서술본의 「재서술자 주:」 블록도 함께 정리한다.

검토했으나 **모순이 아니라고 판단해 위 표에 올리지 않은 것** 2건(감사용 메모 — 상류에 고칠 것이 없다).

- **LTS 표기** — `README` 「전체 타임라인」의 `✅` 가 11·17·21·25 넷에만 붙고 Java 8 행은 비어 있으나, 표 아래 주석이 LTS 를 「8, 11, 17, 21, 25」 다섯으로 적는다. `java-8.md` 가 스스로를 「현대적 LTS 모델(Java 11부터 시작) 이전 … 사실상 … "장기 지원"」이라 적고 `java-11.md` 가 자기를 「6개월 케이던스 도입 이후 첫 LTS」라 적으므로 **기준이 둘(소급 지정 vs 모델 시작)인 것이지 값이 어긋난 것이 아니다.** 재서술본 README 에는 두 기준을 나란히 적는 세 줄을 보충으로 달았다.
- **릴리스 모델 전환 시점** — 「6개월 모델의 첫 릴리스」를 9편·10편은 Java 10 으로, 14편은 「9 버전부터 전환」으로 적는다. 이는 **전환을 결정·발표한 시점(9)과 그 모델로 나온 첫 결과물(10)의 차이**이고, 이미 위 표 java-14 행으로 등재돼 있어 중복 등재하지 않는다.


## 후속 작업 — 「그 뒤」 문서 (사용자 요청 2026-09-20)

8주제 이관이 끝나면 **원본 이후의 변화를 오늘자 기준으로 조사해 추가**한다.

원본 repo 의 시점 실측(연도 언급 분포):

| 원본 | 2024 | 2025 | 2026 |
|---|---|---|---|
| database | 5 | 8 | 10 |
| js | 4 | 4 | 4 |
| rust | 34 | 12 | 2 |
| network | — | — | 3 |
| python | 14 | 5 | — |
| web | 1 | — | — |
| spring | 2025 까지 | | |
| java | 2026 까지 | | |

간격은 몇 년이 아니라 **몇 달**이고, 주제별 편차가 크다(web 2024 \~ database 2026).

**설계 결정(권고) — 재서술본에 섞지 말고 주제마다 별도 파일로 둔다.**
- 이 파이프라인이 인용 층 오류를 여섯 주제 연속 0건으로 낸 것은 **모든 문장이 원문으로 추적되는 구조** 덕분이다. 재서술본에 원문 밖 사실을 섞으면 그 구조가 깨진다.
- 원본 repo 가 계속 정본으로 남고, 나중에 원본이 갱신돼도 병합이 쉽다.
- 검증 방식이 다르다 — 대조할 원문이 없으므로 `cs/ops-patterns/deadline-propagation` 과 같이 **공식 문서·릴리스 노트로 확인하고 출처 링크를 단다.** 확인 못 한 것은 적지 않거나 `(확인 필요)`.
- 각 편에서 「그 뒤는 <파일>에」 한 줄로 연결한다.

대안(각 편 안에 `## [Claude 추가]`)은 13편 이상에서 원문 경계가 흐려지고 병합이 어려워 권하지 않는다.

**착수 전 확정할 것**: 파일명 규약 · 조사 범위(주제별 마지막 언급 시점 \~ 오늘) · 출처 표기 형식.

## 남은 일

- `history/README.md` · 루트 `index.md` 의 history 섹션 — 주제가 2개 이상 쌓인 뒤 한 번에 작성한다(현재 미작성).
- network 6 → js 6 → rust 6 → python 6 → spring 13 → java 28 (73편).
