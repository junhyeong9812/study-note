# Spring — 그 뒤 (2026-09 기준)

> 이 문서는 재서술이 아니라 **새로 쓴 것**이다.\
> `history/spring/` 의 다른 편은 모두 원본 repo(`~/project/java-history/spring/`)를 정본으로 두고 옮긴 것이지만, 이 편만 원본이 없다.\
> 그래서 원문 대조 자리를 **출처 접지**가 대신한다 — 본문의 사실 주장은 전부 아래 「출처」 절의 항목으로 되돌아간다.\
> 기준일은 **2026-09-20** 이다.\
> 그 뒤의 일은 담기지 않았다.

## 원본이 멈춘 자리

원본 repo 의 마지막 두 편은 `framework-7.x.md` 와 `boot-4.x.md` 다.\
두 편 모두 **RC·마일스톤이 아니라 GA(정식 출시)까지** 다뤘다 — 원문에 적힌 대로 옮기면 이렇다.

| 원문 | 원문이 적은 마지막 사건 | 원문의 표현 |
|------|------------------------|-------------|
| `framework-7.x.md` | Spring Framework **7.0 GA — 2025년 11월 13일**, 후속 **7.0.1 — 2025년 11월 20일** | "최초 출시: 7.0 GA — 2025년 11월 13일 (후속 7.0.1 — 2025년 11월 20일)" |
| `boot-4.x.md` | Spring Boot **4.0 GA — 2025년 11월 20일**, 후속 **4.0.1 — 2025년 12월 18일** | "**최초 출시**: Spring Boot 4.0 GA — 2025년 11월 20일 (후속 4.0.1 — 2025년 12월 18일)" |

그래서 **원본이 멈춘 자리는 Spring Boot 4.0.1(2025-12-18)** 이다.\
이 문서가 메우는 간격은 그 뒤부터 기준일 **2026-09-20** 까지 — 약 9개월이다.

원문이 열어 둔 채로 끝낸 자리도 하나 있다.\
`boot-4.x.md` 의 「출시 시점 버전 상황」 절이 **"4.1은 GA 이후 별도 개발 라인(마일스톤)으로 진행된다"** 라고만 적고 끝난다.\
이 문서의 「원문이 「예정」이라 한 것은 어떻게 됐나」 절이 그 자리를 받는다.

> **GA (General Availability)** — 정식 출시. 프리뷰·RC(Release Candidate)·마일스톤(M1, M2…)을 거친 뒤 운영에 써도 된다고 공표하는 단계다.\
> 예: Spring Framework 7.0 은 2025-11-13 에 GA 가 됐고, 그 전의 7.0.0-M1~RC 는 GA 가 아니다.

## 그 뒤 무슨 일이 있었나

### 1. Spring Framework — 7.0.x 패치가 이어졌고, 7.1 은 아직 GA 가 아니다

원문이 7.0.1(2025-11-20)에서 끝낸 뒤 7.0.x 는 패치 라인으로 계속 나왔다.
스프링 블로그 릴리스 공지로 확인한 2026년 발표는 이렇다.

| 버전 | 발표일 | 출처 |
|------|--------|------|
| 7.0.3 | 2026-01-15 | spring.io 블로그 |
| 7.0.4 | 2026-02-12 | spring.io 블로그(6.2.16 과 동시) |
| 7.0.5 | 2026-02-18 | spring.io 블로그 |
| 7.0.6 | 2026-03-13 | spring.io 블로그(6.2.17 과 동시) |
| 7.0.7 | 2026-04-17 | spring.io 블로그(6.2.18 과 동시) |
| 7.0.8 | 2026-06-08 | spring.io 블로그(6.2.19 와 동시) |
| 7.0.9 | 2026-08-20 | GitHub releases(블로그 공지를 찾지 못했다) |

**7.0.9 에는 스프링 블로그의 개별 공지가 없다.**\
저장소의 releases 페이지가 v7.0.9 를 Latest 로, 같은 날짜의 v7.1.0-M1 을 Pre-release 로 싣는다.\
블로그의 릴리스 카테고리 목록은 전수가 아니다 — 패치 라인의 마감은 저장소의 releases/tags 로 확인해야 한다.

**7.1 은 기준일(2026-09-20) 현재 GA 가 아니다.**\
GitHub 위키의 7.1 릴리스 노트가 스스로 이렇게 적는다 — "This is a preview page for Spring Framework 7.1.0, scheduled for November 2026."\
즉 **2026년 11월 예정**이고, 지금 나와 있는 건 마일스톤(**7.1.0-M1 — 2026-08-20**, 저장소 releases 에 Pre-release 로 표시)이다.

7.1 프리뷰 페이지가 예고한 것 중 눈에 띄는 것:

- **`RestTemplate` 의 공식 deprecated** — "RestTemplate and related types are formally deprecated as of 7.1. Their actual removal is scheduled for Spring Framework 8.0 (not yet scheduled)."\
  deprecated 는 **삭제가 아니다.**\
  실제 제거는 8.0 으로 잡혀 있고, 그 8.0 은 아직 일정조차 안 잡혔다("not yet scheduled").
- RFC 10008 의 **QUERY HTTP 메서드** 지원, `MultipartHttpMessageConverter` 신설(멀티파트를 쓰는 것뿐 아니라 **읽는** 것도 가능).
- 최소 요구 상향 — Jackson 3.1, Hibernate ORM 7.3, MockMvc 연동의 HtmlUnit 5.4.

### 2. Spring Boot — 4.1 이 GA 로 나왔다 (2026-06-10)

원문이 "마일스톤으로 진행된다"고만 적고 끝낸 4.1 이 **정식 출시됐다.**

- **4.1.0 GA — 2026년 6월 10일.** 그 전의 단계는 M1(2026-01-22) → M2(2026-02-19) → M3(2026-03-20) → M4(2026-03-26) → RC1(2026-04-23) 이었다.
- 릴리스 노트가 적는 4.1.0 의 의존 버전은 **Spring Framework 7.0.8** 이다 — **7.1 이 아니다.**\
  Boot 의 마이너 번호가 오른다고 Framework 의 마이너 번호가 따라 오르지는 않는다.
- 블로그가 적은 4.1 의 highlights: **Spring gRPC 지원**, Jackson 설정 프로퍼티·커스터마이즈 갱신, **`InetAddressFilter` 를 통한 HTTP 클라이언트 SSRF 완화**, OpenTelemetry 를 포함한 관측성 갱신, Log4j 의 파일 로테이션 지원.
- 릴리스 노트가 덧붙이는 것: `spring.config.import` 에 인코딩 지정, 비동기 메서드의 컨텍스트 전파, **MongoDB 를 쓰는 Spring Batch 자동 설정**, Redis 리스너 자동 설정, info 액추에이터의 프로세스 정보. 또 jOOQ 지원 버전이 3.20 으로 올라가면서 **그 의존성만은 Java 21 이상**을 요구한다.
- 이후 **4.1.1 — 2026년 8월 20일**(98건의 버그 수정·문서 개선·의존성 갱신), 4.0.x 라인도 **4.0.8 — 2026년 8월 20일**까지 이어졌다.
- **4.2.0-M1 — 2026년 8월 20일.** 이건 **마일스톤이지 GA 가 아니다.**\
  113건의 개선·수정을 담았고 AMQP 1.0 지원, Buildpacks 의 이미지 기반 빌드 캐시가 거론된다.\
  의존성으로 **Spring Framework 7.1.0-M1** 을 끌어온다.

**마일스톤 단계에서 들어갔다가 빠진 것도 있다.**\
4.1.0-M3(2026-03-20)이 AMQP 1.0 지원과 RabbitMQ Streams SSL 을 담았는데, 엿새 뒤 **M4(2026-03-26)가 그 Rabbit·AMQP 변경을 되돌리고 전달 시점을 Spring Boot 4.2 로 미뤘다.**\
M3 에서 올라오던 사용자는 AMQP 스타터 POM 을 되돌려야 했다.\
AMQP 1.0 은 그래서 4.1 이 아니라 **4.2.0-M1 의 항목으로 다시 나타난다.**\
「마일스톤에 있었다」가 「정식에 들어간다」가 아님을 보여 주는 자리다.

> **마일스톤(M) · RC · GA** — 한 버전이 정식이 되기까지의 단계다.\
> M1, M2… 는 개발 중 스냅샷, RC(Release Candidate)는 출시 후보, GA 가 정식이다.\
> 예: Boot 4.1 은 M1→M4→RC1 을 거쳐 2026-06-10 에 GA 가 됐고, Boot 4.2 는 기준일 현재 M1 까지만 나와 있다.

### 3. 지원 종료 — OSS 지원과 상용 지원은 다르다

이 갈래는 **두 종류의 「지원」을 섞으면 안 된다.**

> **OSS 지원 / 상용 지원** — OSS(오픈소스) 지원은 누구나 받을 수 있는 무상 패치다.\
> 상용 지원은 유료 구독자에게만 나가는 연장 패치다.\
> 예: Spring Boot 3.5 는 OSS 지원이 끝난 뒤에도 상용 지원 경로는 남아 있다.

기준일까지 스프링 블로그가 **1차 출처로 적은** 것은 다음 두 건이다.

| 라인 | 마지막 OSS 릴리스 | 블로그가 쓴 표현 |
|------|------------------|------------------|
| Spring Framework 6.2.x | **6.2.19 — 2026-06-08** | "6.2.19 is **most probably** the last OSS release of the 6.2.x generation, so please consider upgrading to 7.0.x at your earliest convenience" |
| Spring Boot 3.5.x | **3.5.16 — 2026-06-25** | "This is the last OSS release of the 3.5.x generation" — 4.0.x 나 4.1.x 로 올리라 권하고, **"commercial support is also available"** 이라 덧붙인다 |

표현 차이를 그대로 옮겼다 — Framework 쪽은 **"most probably"**(아마도)라고 여지를 남겼고, Boot 쪽은 단정했다.

**고정 날짜는 지원 정책 페이지가 아니라 프로젝트 페이지의 Support 탭에 있다.**\
spring.io 의 지원 정책 페이지(`spring.io/support-policy/`)는 **고정 날짜 표가 아니라 기간 규칙**만 적는다 — Spring Boot 의 마이너 릴리스는 최소 13개월(구독 시 25개월), 메이저는 최대 3년, 그리고 **한 메이저의 마지막 마이너에는 5년의 엔터프라이즈 지원이 추가**된다는 식이다.\
날짜 자체는 **프로젝트 페이지의 Support 탭**(`spring.io/projects/spring-boot#support` — 데이터는 `api.spring.io/projects/spring-boot/generations`)이 싣는다.\
위 표의 3.5.16 공지가 "last OSS release" 에 건 링크가 바로 그 Support 탭이다.

| 세대 | OSS 지원 종료 | 상용 지원 종료 |
|------|--------------|----------------|
| Spring Boot 3.5.x | 2026-06-30 | **2032-06-30** |
| Spring Boot 4.0.x | 2026-12-31 | 2027-12-31 |
| Spring Boot 4.1.x | 2027-07-31 | 2028-07-31 |

3.5.x 의 상용 지원만 2032년으로 멀다는 점이 눈에 띈다 — 출처가 적는 것은 날짜뿐이고, 이 문서는 그 날짜가 어느 규칙에서 나왔는지를 계산해 덧붙이지 않는다.

### 4. Spring AI — 2.0 이 GA 가 됐다 (2026-06-12)

원본 repo 의 어느 편도 Spring AI 를 다루지 않는다.\
기존 편의 몫이 아니므로 여기 적는다.

- **Spring AI 2.0.0 GA — 2026년 6월 12일.** RC1(2026-06-06)·RC2(2026-06-09)를 거쳤다.
- 블로그가 명시하는 대응 관계: **"Spring AI 2.0 has been designed to be used with Spring Boot 4.0 / 4.1 and Spring Framework 7.0"**.
- 2.0 에서 바뀐 것으로 블로그가 드는 것: 코드베이스 전반의 **JSpecify** 널 안정성 애노테이션, Options 를 생성자 대신 **빌더로 만들고 불변으로** 두는 것, 툴 호출 루프를 개별 chat model 구현에서 꺼내 **advisor 체인의 1급 구성요소**로 옮긴 것, **Jackson 3** 전환과 `JsonHelper`, 공급자별 구현 변종 축소(예: OpenAI 가 3종 → SDK 기반 1종), 프로퍼티 키에서 인위적인 `.options` 마디 제거.
- GA 글은 `breaking`·`migration` 이라는 말을 쓰지 않는다.\
  대신 **1.x → 2.0.0 항목으로 가는 「Upgrade notes」 링크를 따로 둔다.**
- 이후 **2.0.1 — 2026년 8월 21일**.

Spring AI 는 `spring.io/projects/spring-ai` 에 등재된 **포트폴리오 안의 프로젝트**다 — 보안 블로그도 CVE 를 "across the portfolio" 로 셀 때 같은 틀에서 센다.\
2.0 이 든 변경 목록의 앞 두 항목(JSpecify 널 안정성·Jackson 3)은 Framework 7.0 이 든 두 축과 같은 항목이다.

### 5. 2026년 4~6월 — CVE 가 한꺼번에 쏟아졌다

기준일까지의 기간에서 릴리스 번호만큼이나 눈에 띄는 사건이다.

spring.io 블로그 "Spring and Security In The Times Of AI"(2026-06-01)가 숫자를 직접 적는다.

- "April saw a spike in announced CVEs from Spring when compared to the historic averages. In total we announced **26 new CVEs** across the portfolio"
- "March 2026 saw **55** new security reports submitted by the community"
- "April, utilizing new scanning capabilities, we received an unprecedented **482 new security reports across 65 scanned projects**"
- 그 482건 중 **370건은 내부 스캔, 112건은 커뮤니티**에서 왔고, **내부 스캔 결과의 37%는 중복이거나 무효**로 판정됐다.
- 5월의 커뮤니티 신고는 **72건**.

글이 드는 원인은 AI 다 — "AI models have drastically reduced the level of skill and knowledge required to identify potential code patterns that could be vulnerabilities."\
그 여파로 **5월 릴리스 트레인이 6월 8~14일로 밀렸다.**

실제로 그 창에 나온 보안 릴리스가 앞서 적은 6월 8~9일 묶음이다.

- Spring Framework **7.0.8 · 6.2.19** — 2026-06-08
- Spring Security **6.5.11 · 7.0.6 · 7.1.0** — 2026-06-09, **7건의 취약점**을 고쳤다(SAML 처리·XSS·오픈 리다이렉트·권한 없는 사용자 가장 등)\
  ※ 여기 나오는 **Spring Security 7.1.0 은 Spring Framework 7.1 과 별개의 번호**다.\
  두 프로젝트는 버전 번호를 따로 매긴다 — Security 7.1.0 은 2026-06-09 에 나왔고, Framework 7.1 은 기준일 현재 GA 가 아니다.
- Spring Authorization Server **1.5.8** — 2026-06-09\
  ※ 공지 제목은 「Spring Authorization Server 2026.06 Releases」인데, **2026.06 은 묶음 표기이고 실제 버전 번호는 1.5.8** 이다.\
  같은 공지가 상용 고객용으로 1.3.12·1.4.11 도 함께 든다.

> **오해하기 쉬운 자리** — 「CVE 26건」과 「37% 는 중복·무효」는 **분모가 다른 두 수치**다.\
> **26건은 확정·공지된 CVE 수**다 — 출처가 "we announced **26 new CVEs** across the portfolio" 라 적는다.\
> **37% 는 신고 단계의 비율**이다 — 4월에 내부 스캔으로 들어온 신고 **370건** 가운데 중복이거나 무효로 판정된 몫이다.\
> 그러니 37% 는 26건을 깎는 수치가 아니다.\
> 앞의 수는 공지까지 간 확정치이고, 뒤의 수는 그보다 앞 단계에서 걸러진 비율이다.\
> 출처는 이 폭증을 스캔 역량이 늘어난 결과로 설명한다.\
> 그 이상을 이 문서가 덧붙이지 않는다.

### 6. 주변 프로젝트도 Boot 4 세대에 맞춰 붙었다

| 프로젝트 | 사건 | 날짜 |
|----------|------|------|
| Spring Cloud | **2025.1.1**(Oakwood) | 2026-01-29 |
| Spring Cloud | **2025.1.2** — "compatible with Spring Boot `4.0.7` and **introduces compatibility for Spring Boot `4.1.0`**" | 2026-06-11 |
| Spring Cloud | **2025.1.3**(Oakwood) — 공지가 적는 기반은 **Spring Boot 4.0.8** 이다 | 2026-08-20 |
| Spring Modulith | **2.1 GA**(2.0.7 · 1.4.12 동시) | 2026-06-11 |
| Spring Modulith | **2.2 M1**(2.1.1 · 2.0.8 · 1.4.13 동시) — M1 은 마일스톤이고, Boot **4.2 M1** · Framework **7.1 M1** 로 지원을 올렸다 | 2026-08-26 |
| Spring AI | **2.0.1** | 2026-08-21 |
| Spring Batch | **6.0.5** 및 **6.1.0-M1** | 2026-08-20 |
| Spring Data | **2026.1.0-M1 · 2026.0.1 · 2025.1.7** | 2026-08-20 |
| Spring Tools | **5.4.0** | 2026-09-09 |

Boot 4.1.0 호환은 **새 릴리스 트레인이 아니라 2025.1.x 의 패치 릴리스 2025.1.2** 에서 들어왔다.\
Boot 4.1.0 이 6월 10일, 2025.1.2 가 그 다음 날인 6월 11일이다.\
한 사례이므로 여기서 경향을 말하지 않는다.

## 원문이 「예정」이라 한 것은 어떻게 됐나

원본 두 편(`framework-7.x.md`·`boot-4.x.md`)에서 앞을 내다본 문장은 **한 줄뿐**이다.

| 원문의 문장 | 어떻게 됐나 | 근거 |
|-------------|-------------|------|
| `boot-4.x.md` — "**4.1**은 GA 이후 별도 개발 라인(마일스톤)으로 진행된다." | 그 마일스톤 라인이 **M1(2026-01-22) → M2 → M3 → M4(2026-03-26) → RC1(2026-04-23) → GA(2026-06-10)** 로 끝까지 갔다. 4.1 은 **정식 출시됐다.** | spring.io 릴리스 공지 |

원문이 "예정"이라 적은 것이 실제로 정식이 된, 드문 깔끔한 사례다.\
다만 **원문이 예상하지 않은 방향도 하나 있다** — 4.1 이 Framework **7.1 이 아니라 7.0.8** 위에 섰다는 것이다.

## 아직 안 끝난 것

기준일(2026-09-20) 현재 **정식이 아닌** 것들이다.\
정식으로 읽지 말 것.

- **Spring Framework 7.1** — GA 가 아니다.\
  릴리스 노트 페이지가 스스로 "This is a preview page for Spring Framework 7.1.0, **scheduled for November 2026**" 이라 적는다.\
  나와 있는 것은 7.1.0-M1 등 마일스톤이다.
- **Spring Boot 4.2** — GA 가 아니다.\
  **4.2.0-M1(2026-08-20)** 까지다.\
  AMQP 1.0 지원·Buildpacks 이미지 기반 빌드 캐시가 거론되지만 마일스톤 단계의 내용이다.
- **`RestTemplate` 의 제거** — 7.1 릴리스 노트 프리뷰가 "formally deprecated as of 7.1" 이라 적지만, 그 **7.1 자체가 아직 GA 가 아니다.**\
  그리고 deprecated 는 제거가 아니다 — "Their actual removal is scheduled for Spring Framework 8.0 (**not yet scheduled**)" 로, 8.0 자체의 일정이 없다.
- **Spring Framework 6.2.x 의 OSS 지원** — 블로그가 6.2.19(2026-06-08)를 **"most probably"** 마지막 OSS 릴리스라 적었다.\
  단정이 아니다.
- **Spring Modulith 2.2** — M1(2026-08-26)까지.\
  GA 가 아니다.
- **Spring Batch 6.1 · Spring Data 2026.1.0** — M1 까지.\
  GA 가 아니다.

### 확인하지 못한 것

- **상용 지원 종료일이 어느 정책 조항에서 나오는지.**\
  날짜 자체는 프로젝트 페이지 Support 탭(`api.spring.io` 의 generations 데이터)에서 1차로 확인해 위 3절에 적었다.\
  열어 본 것은 `spring.io/support-policy/` 와 그 Support 탭 둘인데, 정책 페이지 쪽은 기간 규칙만 싣기 때문에 그 날짜가 어떤 조항에서 계산돼 나오는지는 확인하지 못했다.
- **가상 스레드·GraalVM 쪽의 4.1 변경.**\
  검색 결과에는 관련 문장이 떠다녔으나, Spring Boot 4.1 릴리스 노트 위키 본문에서 해당 문장을 1차로 확인하지 못했다.\
  Boot 4.0 의 "GraalVM native-image v25 이상" 요구는 **원문이 이미 적은 것**이라 여기 다시 적지 않는다.
- **Spring Boot 4.0.2·4.0.5·4.0.7 의 개별 공지 날짜.**\
  4.0.3(2026-02-19)·4.0.4(2026-03-19)·4.0.8(2026-08-20)은 공지로 확인했다.\
  4.0.2 와 4.0.6 은 Framework 쪽 공지가 존재를 알려 준 것뿐이다 — 7.0.3 공지(2026-01-15)가 "This version will be shipped next week with Spring Boot `4.0.2`." 라 적고, 7.0.7 공지(2026-04-17)가 같은 형식으로 "This version will be shipped next week with Spring Boot `4.0.6`." 라 적는다.\
  나머지는 개별 공지를 열지 못했다.

## 용어 풀이

새로 나온 것만 적는다.\
GA·마일스톤·OSS/상용 지원은 본문 첫 등장 자리에 이미 풀어 두었다.

> **SSRF (Server-Side Request Forgery)** — 서버가 대신 요청을 보내 준다는 점을 악용해, 공격자가 서버만 닿을 수 있는 내부 주소로 요청을 보내게 만드는 공격이다.\
> 예: Spring Boot 4.1 이 HTTP 클라이언트에 `InetAddressFilter` 를 걸 수 있게 한 것이 이 완화책으로 소개됐다.

> **릴리스 트레인 (release train)** — 여러 프로젝트를 한 묶음의 버전으로 함께 내보내는 방식이다.\
> 개별 버전 대신 `2025.1.2` 같은 묶음 이름을 쓴다.\
> 예: Spring Cloud 2025.1.x(코드명 Oakwood)가 그 묶음이고, 2025.1.2 가 Spring Boot 4.1.0 호환을 들여왔다.

> **advisor 체인** — Spring AI 에서 모델 호출 앞뒤에 끼워 넣는 처리 단계를 이어 붙인 것이다.\
> 예: Spring AI 2.0 은 툴 호출 루프를 개별 chat model 구현에서 꺼내 이 체인의 1급 구성요소로 옮겼다.

> **QUERY HTTP 메서드** — RFC 10008 이 정의하는 HTTP 메서드로, Spring Framework 7.1 프리뷰가 지원 예정으로 적은 항목이다.\
> 예: 7.1 릴리스 노트 프리뷰 페이지가 "RFC 10008's QUERY HTTP method" 지원을 든다.

## 출처

**1차 출처** — spring.io 공식 블로그의 릴리스 공지, spring-projects GitHub 위키의 릴리스 노트, spring.io 의 지원 정책 페이지.

### Spring Framework

| 제목 | 발행일 | URL |
|------|--------|-----|
| Spring Framework 7.0.3 Available Now | 2026-01-15 | https://spring.io/blog/2026/01/15/spring-framework-7-0-3-available-now/ |
| Spring Framework 6.2.16 and 7.0.4 Available Now | 2026-02-12 | https://spring.io/blog/2026/02/12/spring-framework-6-2-16-and-7-0-4-available-now/ |
| Spring Framework 7.0.5 Available Now | 2026-02-18 | https://spring.io/blog/2026/02/18/spring-framework-7-0-5-available-now/ |
| Spring Framework 6.2.17 and 7.0.6 Available Now | 2026-03-13 | https://spring.io/blog/2026/03/13/spring-framework-6-2-17-and-7-0-6-available-now/ |
| Spring Framework 6.2.18 and 7.0.7 Available Now | 2026-04-17 | https://spring.io/blog/2026/04/17/spring-framework-6-2-18-and-7-0-7-available-now/ |
| Spring Framework 7.0.8 and 6.2.19 Available Now | 2026-06-08 | https://spring.io/blog/2026/06/08/spring-framework-7-0-8-and-6-2-19-available-now/ |
| Releases · spring-projects/spring-framework (GitHub) — v7.0.9(Latest) · v7.1.0-M1(Pre-release) | 둘 다 2026-08-20 | https://github.com/spring-projects/spring-framework/releases |
| Spring Framework 7.1 Release Notes (preview) | (기준일 현재 프리뷰) | https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-7.1-Release-Notes |
| Spring Framework Versions (wiki) | (수시 갱신) | https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-Versions |

### Spring Boot

| 제목 | 발행일 | URL |
|------|--------|-----|
| Spring Boot 4.1.0-M1 available now | 2026-01-22 | https://spring.io/blog/2026/01/22/spring-boot-4-1-0-M1-available-now/ |
| Spring Boot 4.0.3 available now | 2026-02-19 | https://spring.io/blog/2026/02/19/spring-boot-4-0-3-available-now/ |
| Spring Boot 4.1.0-M2 available now | 2026-02-19 | https://spring.io/blog/2026/02/19/spring-boot-4-1-0-M2-available-now/ |
| Spring Boot 4.0.4 available now | 2026-03-19 | https://spring.io/blog/2026/03/19/spring-boot-4-0-4-available-now/ |
| Spring Boot 4.1.0-M3 available now | 2026-03-20 | https://spring.io/blog/2026/03/20/spring-boot-4-1-0-M3-available-now/ |
| Spring Boot 4.1.0-M4 available now | 2026-03-26 | https://spring.io/blog/2026/03/26/spring-boot-4-1-0-M4-available-now/ |
| Spring Boot 4.1.0-RC1 available now | 2026-04-23 | https://spring.io/blog/2026/04/23/spring-boot-4-1-0-RC1-available-now/ |
| Spring Boot 4.1.0 available now | 2026-06-10 | https://spring.io/blog/2026/06/10/spring-boot-4/ |
| Spring Boot 3.5.16 available now (3.5.x 의 마지막 OSS 릴리스) | 2026-06-25 | https://spring.io/blog/2026/06/25/spring-boot-3-5-16-available-now/ |
| Spring Boot 4.0.8 available now | 2026-08-20 | https://spring.io/blog/2026/08/20/spring-boot-4-0-8-available-now/ |
| Spring Boot 4.1.1 available now | 2026-08-20 | https://spring.io/blog/2026/08/20/spring-boot-4-1-1-available-now/ |
| Spring Boot 4.2.0-M1 available now | 2026-08-20 | https://spring.io/blog/2026/08/20/spring-boot-4-2-0-M1-available-now/ |
| Spring Boot 4.1 Release Notes (wiki) | (수시 갱신) | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.1-Release-Notes |
| Spring Boot 4.2.0-M1 Release Notes (wiki) | (수시 갱신) | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.2.0-M1-Release-Notes |
| Spring Boot 4.0 Migration Guide (wiki) | (수시 갱신) | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide |

### 지원 정책 · 보안

| 제목 | 발행일 | URL |
|------|--------|-----|
| Spring Support Policy | (수시 갱신) | https://spring.io/support-policy/ |
| Spring Boot 프로젝트 페이지 Support 탭(세대별 OSS·상용 지원 종료일) | (수시 갱신) | https://spring.io/projects/spring-boot#support |
| Spring Boot generations API(위 Support 탭의 데이터 원본) | (수시 갱신) | https://api.spring.io/projects/spring-boot/generations |
| Spring and Security In The Times Of AI | 2026-06-01 | https://spring.io/blog/2026/06/01/spring_and_security_in_the_times_of_ai/ |
| Spring Security 2026.06 Releases - Contains CVE Fixes | 2026-06-09 | https://spring.io/blog/2026/06/09/spring-security-releases-2026-06/ |
| Spring Authorization Server 2026.06 Releases - Contains CVE Fixes (실제 버전 1.5.8) | 2026-06-09 | https://spring.io/blog/2026/06/09/spring-authorization-server-releases-2026-06/ |

### 그 밖의 포트폴리오

| 제목 | 발행일 | URL |
|------|--------|-----|
| Spring AI 프로젝트 페이지(포트폴리오 등재 확인) | (수시 갱신) | https://spring.io/projects/spring-ai |
| Spring AI 2.0.0-RC1 Available Now | 2026-06-06 | https://spring.io/blog/2026/06/06/spring-ai-2-0-0-RC1-available-now/ |
| Spring AI 2.0.0-RC2 Available Now | 2026-06-09 | https://spring.io/blog/2026/06/09/spring-ai-2-0-0-RC2-available-now/ |
| Spring AI 2.0.0 GA Available Now | 2026-06-12 | https://spring.io/blog/2026/06/12/spring-ai-2-0-0-GA-available-now/ |
| Spring AI 2.0.1 Available Now | 2026-08-21 | https://spring.io/blog/2026/08/21/spring-ai-2-0-1-available-now/ |
| Spring AI Upgrade Notes (2.0.0) | (수시 갱신) | https://docs.spring.io/spring-ai/reference/upgrade-notes.html |
| Spring Cloud 2025.1.1 (aka Oakwood) Has Been Released | 2026-01-29 | https://spring.io/blog/2026/01/29/spring-cloud-2025-1-1-aka-oakwood-has-been-released/ |
| Spring Cloud 2025.1.2 (aka Oakwood) Has Been Released | 2026-06-11 | https://spring.io/blog/2026/06/11/spring-cloud-2025-1-2-aka-oakwood-has-been-released/ |
| Spring Cloud 2025.1.3 (aka Oakwood) Has Been Released | 2026-08-20 | https://spring.io/blog/2026/08/20/spring-cloud-2025-1-3-has-been-released/ |
| Spring Modulith 2.1 GA, 2.0.7, and 1.4.12 released | 2026-06-11 | https://spring.io/blog/2026/06/11/spring-modulith-2-1-ga-2-0-7-and-1-4-12-released/ |
| Spring Modulith 2.2 M1, 2.1.1, 2.0.8, and 1.4.13 released | 2026-08-26 | https://spring.io/blog/2026/08/26/spring-modulith-2-2-m1-2-1-1-2-0-8-and-1-4-13-released/ |
| Spring Batch 6.0.5 and 6.1.0-M1 available now | 2026-08-20 | https://spring.io/blog/2026/08/20/spring-batch-6-0-5-and-6-1-0-M1-available-now/ |
| Spring Data 2026.1.0-M1, 2026.0.1 and 2025.1.7 released | 2026-08-20 | https://spring.io/blog/2026/08/20/spring-data-2026/ |
| Spring Tools 5.4.0 released | 2026-09-09 | https://spring.io/blog/2026/09/09/spring-tools-5-4-0-released/ |
| Spring 블로그 releases 카테고리(8~9월 목록 확인용) | (수시 갱신) | https://spring.io/blog/category/releases/ |

**2차 출처** — 이 문서는 본문 사실에 2차 출처를 쓰지 않았다.\
검색 결과에 섞여 있던 2차 출처(엔드오브라이프 집계 사이트·개인 블로그의 EOL 정리 등)는 1차로 가는 길잡이로만 썼고, 1차로 확인되지 않은 항목은 「확인하지 못한 것」으로 남겼다.

**원본 repo 인용** — 「원본이 멈춘 자리」와 「원문이 「예정」이라 한 것」 절이 인용한 문장의 출처는 `~/project/java-history/spring/` 의 `framework-7.x.md` · `boot-4.x.md` 다.\
읽기만 했고 고치지 않았다.
