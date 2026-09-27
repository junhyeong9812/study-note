# 갭 리서치 — 디자인 패턴과 설계 추상화 (2026-09-28, L0)

> **대상**: [`curriculum.md`](curriculum.md)(18영역·517 leaf) 중 GoF 이후 패턴 카탈로그와 "설계를 코드로 표현하는 추상화 수준"이 비어 있는 곳.
> **문제의식(사용자)**: "GoF 이후로 파생된 패턴이 훨씬 많고, 좋은 코드·TDD·DDD 같은 추상화 수준을 제대로 잡아야 실제 코드로 표현할 수 있다."
> **결론 한 줄**: GoF(12/13)와 복원력·분산 패턴(11.2·10.5)은 꽤 덮여 있다. 빈 곳은 **네 군데**다. ① PoEAA의 데이터 소스·매핑·오프라인 동시성 ② EIP 메시징 패턴 ③ 서버 동시성 아키텍처(POSA2) ④ **"설계를 코드로 옮기는 층"** — DI, 결과 타입, 불법 상태 차단, 패키지 구조, 아키텍처의 코드 표현, 패턴 쪽으로 리팩터링하기. ④가 사용자 문제의식의 핵심이다. 신규 leaf는 **29개**를 제안한다.
> **표기**: `[?]` = 이번 작업에서 원문을 직접 확인하지 못한 항목이다. 장 번호가 없는 서적 인용은 제목 수준에서만 주장한다. slug 번호는 **가안**이다. 영역 끝 번호 뒤에 붙였다(network 46~52를 추가할 때와 같은 관례). 마감 leaf(역색인·실사건)의 순서를 바꿀지는 이식할 때 정한다.

---

## 0. 조사 방법·근거

| 카탈로그 | 확인 수준 | 출처 |
|---|---|---|
| Fowler PoEAA | **목차 전체 확인**(범주 10개, 패턴 51개) | martinfowler.com/eaaCatalog |
| Hohpe–Woolf EIP | **목차 전체 확인**(범주 6개) | enterpriseintegrationpatterns.com/patterns/messaging |
| Richardson microservices.io | **목차 전체 확인** | microservices.io/patterns |
| Azure Cloud Design Patterns | **목차 전체 확인**(패턴 44개, 2026-05 판) + Azure 성능 안티패턴 10개 | learn.microsoft.com/azure/architecture/patterns · /antipatterns |
| POSA2 (Schmidt 외 2000) | 패턴 17개 이름 확인. 1·3·4·5권 목차는 `[?]` | dre.vanderbilt.edu/~schmidt/POSA/POSA2 · hillside.net |
| Nygard 『Release It!』 2판 | 안정성 패턴은 요약본 기준 8개를 확인했다. 원서에는 약 10개 `[?]`(Let It Crash·Shed Load·Create Back Pressure·Governor는 요약본에 없음). 안정성 안티패턴 10개 확인 | pragprog.com · github csabapalfi/release-it · 요약 블로그 |
| Meszaros 『xUnit Test Patterns』 | 테스트 스멜 4대(Obscure·Fragile·Erratic·Slow)와 Humble Object 확인. 전체 스멜 목록 18개는 `[?]` | xunitpatterns.com |
| Kerievsky 『Refactoring to Patterns』 | 대표 리팩터링 4개 이름 확인. 전체 27개 목록은 `[?]` | informit.com |
| 함수형·타입 | ROP(Wlaschin), Parse don't validate(King 2019), Functional Core/Imperative Shell(Bernhardt 2012) 확인 | fsharpforfunandprofit.com/rop · lexi-lambda.github.io · destroyallsoftware.com/talks/boundaries |
| 동시성 | DCL Broken Declaration(Pugh 외), RCU(McKenney, LWN 2007) 확인 | cs.umd.edu/~pugh · lwn.net/Articles/262464 |
| 프론트엔드 | Container/Presentational → Hooks 권장, Compound, Islands(Miller 2020), Flux(2014), Micro Frontends(Jackson, Fowler 사이트 2019) 확인 | patterns.dev · jasonformat.com · facebookarchive.github.io/flux · martinfowler.com/articles/micro-frontends.html |
| 패키지 구조·DI | Simon Brown "The Missing Chapter"(『Clean Architecture』 34장 — package by layer·feature·component), Seemann–van Deursen 『DI Principles, Practices, and Patterns』(Composition Root·Service Locator·Ambient Context 안티패턴) 확인 | O'Reilly ch34 · manning.com |

기존 노트는 다음을 확인했다. `cs/engineering/design-patterns-gof`(23개 패턴·Spring 흡수표), `cs/ops-patterns` 01~19, `cs/systems/server-design/11-antipatterns.md`(안티패턴 29개 — 구조·확장·복원력·상태·운영), `cs/engineering/data-access`(Data Mapper·UoW·Identity Map·Lazy Load 언급).

---

## 1. 카탈로그별 커버 점검표

범례: **있음**(slug) = 이미 그 leaf의 주제다 / **부분**(slug) = 그 leaf의 한 절로 흡수됐거나 언급만 있다 / **없음** / → `#n` = §2의 신규 제안 번호.

### 1.1 Fowler PoEAA

| 범주 | 패턴 | 판정 |
|---|---|---|
| 도메인 로직 | Transaction Script · Table Module · Domain Model | 부분(domain-modeling/09-anemic-vs-rich-model — "빈약 vs 풍부"만 다루고 **선택 기준으로서의 3택**은 없음) → #11 |
| | Service Layer | 부분(domain-modeling/01 📚 인용만) → #11 |
| 데이터 소스 | Table Data Gateway · Row Data Gateway · Active Record | 없음 → #12 |
| | Data Mapper | 부분(database/33 — `engineering/data-access` jpa·comparison에서 언급) → #12 |
| O-R 행위 | Unit of Work · Identity Map · Lazy Load | **있음**(database/33-orm-and-n-plus-one) |
| O-R 구조 | Identity Field · Foreign Key Mapping · Association Table Mapping · Dependent Mapping · Embedded Value · Serialized LOB · 상속 매핑 3종(Single·Class·Concrete Table) · Inheritance Mappers | 없음 → #13 |
| O-R 메타데이터 | Metadata Mapping · Query Object | 없음 → #12 |
| | Repository | 부분(domain-modeling/08 — DDD Repository. PoEAA 정의와의 차이는 없음) → #12 |
| 웹 프레젠테이션 | MVC · Page Controller · Front Controller · Template View · Transform View · Two Step View · Application Controller | 없음 → #9 |
| 분산 | Remote Facade · Data Transfer Object | 없음(api-design은 계약만, 객체 경계 매핑은 다루지 않음) → #10 |
| 오프라인 동시성 | Optimistic Offline Lock | 부분(database/24-occ-and-timestamp-ordering, api-design/13 — 버전 컬럼·ETag) → #14 |
| | Pessimistic Offline Lock · Coarse-Grained Lock · Implicit Lock | 없음 → #14 |
| 세션 상태 | Client · Server · Database Session State | 부분(security/11-sessions-and-cookie-security, reliability/20 무상태화, server-design/11 "스티키 세션 의존") — 신규 불필요 |
| 기반 | Value Object | **있음**(software-design/08, domain-modeling/04) |
| | Money | **있음**(domain-modeling/11-time-money-and-units) |
| | Special Case | 없음 → #4 |
| | Gateway · Service Stub · Separated Interface · Plugin · Registry | 없음 → #3(Separated Interface·Plugin·Registry) · #12(Gateway) · 테스트 대역은 testing/03 부분 |
| | Layer Supertype · Mapper · Record Set | 없음 — 가치가 낮아 #12·#10의 한 줄 언급으로 충분하다 |

### 1.2 Hohpe–Woolf Enterprise Integration Patterns

| 범주 | 패턴 | 판정 |
|---|---|---|
| 채널 | Point-to-Point · Publish-Subscribe | 부분(distributed/24 큐 vs 로그, api-design/26) → #19 |
| | Dead Letter Channel · Invalid Message Channel | 부분(distributed/26 — DLQ·poison pill) → #19 |
| | Guaranteed Delivery | 부분(distributed/24 전달 의미론) |
| | Datatype Channel · Channel Adapter · Messaging Bridge · Message Bus | 없음 → #19 |
| 메시지 구성 | Command / Document / Event Message | 없음(이벤트 vs 명령의 구분이 어디에도 없음) → #19 |
| | Request-Reply · Return Address · Correlation Identifier | 부분(reliability/23 상관 ID는 로깅 관점만) → #19 |
| | Message Sequence · Message Expiration · Format Indicator | 없음 → #19 |
| 라우팅 | Pipes-and-Filters | 없음 → #20 |
| | Content-based Router · Message Filter · Dynamic Router · Recipient List · Splitter · Aggregator · Resequencer · Composed Message Processor · Scatter-Gather · Routing Slip | 없음 → #20 |
| | Process Manager | 부분(distributed/23 orchestration, distributed/20 saga) |
| | Message Broker | 부분(api-design/26) |
| 변환 | Message Translator · Envelope Wrapper · Content Enricher · Content Filter · Claim Check · Normalizer · Canonical Data Model | 없음 → #20 (Canonical Data Model은 domain-modeling/14 Published Language와 교차 링크) |
| 엔드포인트 | Competing Consumers · Polling / Event-driven Consumer · Selective Consumer · Durable Subscriber · Message Dispatcher · Service Activator · Messaging Gateway · Messaging Mapper | 없음 → #19 |
| | Transactional Client | 부분(distributed/21 outbox) |
| | Idempotent Receiver | **있음**(reliability/12-idempotency) — #19에서 링크만 |
| 시스템 관리 | Wire Tap · Message History · Message Store · Control Bus · Detour · Smart Proxy · Test Message · Channel Purger | 부분(reliability/25 분산 추적이 Message History 역할) → #20에서 Wire Tap·Message Store·Test Message만 언급 |

### 1.3 Richardson microservices.io

| 범주 | 패턴 | 판정 |
|---|---|---|
| 스타일 | Monolithic · Microservice | **있음**(software-design/18) |
| 서비스 경계 | Decompose by business capability / subdomain · Self-contained Service · Service per team | 부분(software-design/18 "서비스 분해", domain-modeling/13 서브도메인) → #21 |
| 서비스로 리팩터링 | Strangler Application | 없음 → #8 |
| | Anti-corruption layer | **있음**(domain-modeling/15) |
| 서비스 협업 | Database per Service · Shared database | 부분(server-design/11 "공유 데이터베이스" → reliability/32) → #21 |
| | Saga | **있음**(distributed/20) |
| | API Composition · Command-side replica | 없음 → #21 |
| | CQRS | **있음**(domain-modeling/17) |
| | Domain event | **있음**(domain-modeling/07) |
| | Event sourcing | **있음**(distributed/27) |
| 트랜잭셔널 메시징 | Transactional outbox · Transaction log tailing · Polling publisher | **있음**(distributed/21 — CDC·폴링 포함) |
| 테스트 | Consumer-driven contract test | **있음**(testing/08) |
| | Consumer-side contract test · Service component test | 부분(testing/08·07) |
| 배포 | Service instance per host / VM / Container · Serverless | 부분(os/33·34, reliability/27) — 신규 불필요 |
| 횡단 관심사 | Microservice chassis · Service Template | 없음 → #25(사이드카와 대비) |
| | Externalized configuration | **있음**(software-design/22) |
| 통신 | RPI · Messaging · Domain-specific protocol | **있음**(api-design/25·26, api-design/10) |
| | Idempotent Consumer | **있음**(reliability/12) |
| 외부 API | API gateway · Backend for front-end | 부분(network/39 L7 프록시만) → #24 |
| 서비스 디스커버리 | Client-side / Server-side discovery · Service registry · Self / 3rd party registration | 없음 → #25 |
| 신뢰성 | Circuit Breaker | **있음**(reliability/08) |
| 보안 | Access Token | **있음**(security/12·14) |
| 관측성 | Log aggregation · Application metrics · Distributed tracing · Health check API | **있음**(reliability/23·24·25, network/39) |
| | Audit logging | **있음**(security/25) |
| | Exception tracking · Log deployments and changes | 부분(reliability/23·27) |
| UI | Server-side page fragment composition · Client-side UI composition | 없음 → #30 |

### 1.4 Azure Cloud Design Patterns (44개)

| 패턴 | 판정 |
|---|---|
| Ambassador · Sidecar | 없음 → #25 |
| Anti-Corruption Layer | **있음**(domain-modeling/15) |
| Asynchronous Request-Reply | **있음**(api-design/14-long-running-operations) |
| Backends for Frontends · Gateway Aggregation · Gateway Offloading · Gateway Routing · Gatekeeper | 부분(network/39) → #24 |
| Bulkhead · Circuit Breaker · Retry · Rate Limiting · Throttling | **있음**(reliability/07~10) |
| Cache-Aside | **있음**(database/38) |
| Choreography | **있음**(distributed/23) |
| Claim Check | 부분(network/50 presigned URL은 업로드 관점만) → #20 |
| Compensating Transaction · Saga | **있음**(distributed/20) |
| Competing Consumers · Queue-Based Load Leveling · Priority Queue · Sequential Convoy | 부분(reliability/11 역압, distributed/26) → #19 |
| Compute Resource Consolidation | 없음 — 비용 최적화 성격이라 CS 기본기 밖으로 본다(제안 안 함) |
| CQRS · Event Sourcing · Materialized View | **있음**(domain-modeling/17, distributed/27). Materialized View는 부분 → #21 |
| Deployment Stamps · Geode | 부분(reliability/28 다중 AZ/리전) → #27 |
| External Configuration Store | **있음**(software-design/22) |
| Federated Identity | **있음**(security/14) |
| Health Endpoint Monitoring | **있음**(network/39, reliability/14) |
| Idempotent Consumer | **있음**(reliability/12) |
| Index Table | 부분(database/30 보조 인덱스) → #21 |
| Leader Election | **있음**(distributed/14) |
| Messaging Bridge · Pipes and Filters · Publisher-Subscriber | 없음 / 부분 → #19·#20 |
| Quarantine | 부분(security/24 공급망) |
| Scheduler Agent Supervisor | 부분(reliability/15, distributed/23) → #28(감독 개념) |
| Sharding | **있음**(database/30) |
| Static Content Hosting | **있음**(network/40) |
| Strangler Fig | 없음 → #8 |
| Valet Key | 부분(network/50 presigned URL) → #24에서 권한 위임 관점 링크 |

**Azure 성능 안티패턴 10개**: Busy Database · Busy Front End · Chatty I/O · Extraneous Fetching · Improper Instantiation · Monolithic Persistence · No Caching · Noisy Neighbor · Retry Storm · Synchronous I/O.
판정은 이렇다. Noisy Neighbor는 **있음**(software-design/19). Retry Storm은 **있음**(reliability/07). No Caching은 부분(database/38)이다. **나머지 7개는 없음**이다. reliability/32(server-design/11)는 구조·운영 안티패턴이라 코드 수준 성능 안티패턴은 다루지 않는다. → #26

### 1.5 Nygard 『Release It!』 2판

| 구분 | 패턴 | 판정 |
|---|---|---|
| 안정성 패턴 | Timeouts · Circuit Breaker · Bulkheads | **있음**(reliability/06·08·09) |
| | Shed Load · Create Back Pressure | **있음**(reliability/11) |
| | Steady State · Fail Fast · Let It Crash · Handshaking · Governor | 없음 → #28 |
| | Test Harness | 없음 → #28(또는 reliability/30 카오스와 링크) |
| | Decoupling Middleware | 부분(distributed/24) |
| 안정성 안티패턴 | Cascading Failures · Chain Reactions | 부분(reliability/33 역색인 "연쇄 장애", reliability/09) |
| | Integration Points · Blocked Threads · Slow Responses · Unbounded Result Sets · Self-Denial Attacks · Dogpile · Unbalanced Capacities · Scaling Effects | 부분 또는 없음(reliability/32에 "타임아웃 없음"·"동기 호출 체인"만 있음) → #26 |

### 1.6 POSA (1·2권 중심)

| 패턴 | 판정 |
|---|---|
| **POSA1** Layers · Pipes and Filters · Broker · Microkernel · MVC · PAC · Blackboard · Reflection `[?]`(권별 목차 미확인) | Layers·Microkernel은 **있음**(software-design/15). Pipes and Filters → #20, MVC → #9, Broker는 부분(api-design/26) |
| Reactor | 부분(os/21-event-based-concurrency — 이벤트 루프 수준) → #17 |
| Proactor · Asynchronous Completion Token | 부분(os/28 I/O 4분면, os/30 io_uring) → #17 |
| Acceptor-Connector · Half-Sync/Half-Async · Leader/Followers | 없음 → #17 |
| Active Object · Monitor Object | 부분(os/17 모니터 개념만) → #16 |
| Scoped Locking · Strategized Locking · Thread-Safe Interface | 없음 → #16 |
| Double-Checked Locking Optimization | 부분(language/14 메모리 모델 — happens-before는 있으나 DCL 함정 사례는 없음) → #16 |
| Thread-Specific Storage | 없음 → #16(ThreadLocal 누수 포함) |
| Wrapper Facade · Component Configurator · Interceptor · Extension Interface | 없음 — Interceptor만 #3(DI·AOP 프록시)에서 언급한다. 나머지는 C++ 프레임워크 특화라 제안하지 않는다 |
| **POSA3~5**(자원 관리 — Pooling·Caching·Leasing·Evictor 등, 분산 컴퓨팅 패턴 언어, 패턴 언어론) | `[?]` 목차 미확인. Pooling은 database/32, Leasing은 distributed/14·17, Caching은 data-structure/10에 흩어져 있다. 패턴 언어론은 → #1 |

### 1.7 동시성·함수형·타입

| 패턴 | 판정 |
|---|---|
| 생산자-소비자 | **있음**(os/18, data-structure/38-ring-buffer) |
| 스레드 풀·Executor(크기·거부 정책·큐 선택) | 부분(reliability/09 격벽, math/15) → #16 |
| Future/Promise·CompletableFuture 합성 | 부분(language/15 — "상태 기계로 변환된 Future" 언급) → #16 |
| 액터 | 부분(language/15) — 감독 트리(Let It Crash)는 → #28 |
| Read-Copy-Update · seqlock · Copy-on-Write 스냅샷 | 부분(data-structure/39 lock-free, data-structure/26 영속) — **신규 제안 안 함**(심화·커널 특화). #16에서 "읽기 위주 공유 상태 = 불변 스냅샷 + 원자 참조 교체"로만 다룬다 |
| Double-checked locking의 함정 | 부분(language/14) → #16 |
| 불변·순수 함수 | **있음**(language/10, software-design/08) |
| Result/Either·Option | 부분(language/09 — 언어 메커니즘만) → #4 |
| Railway-oriented programming | 없음 → #4 |
| 파이프라인·합성 | 부분(language/08·10) → #6 |
| Functional Core / Imperative Shell | 없음 → #6 |
| Parse, don't validate · 불법 상태를 표현 불가능하게 | 없음 → #5 |

### 1.8 프론트엔드

| 패턴 | 판정 |
|---|---|
| MVC·MVP·MVVM | 없음 → #9 |
| 컴포넌트 합성·Compound Components·Container/Presentational·Hooks·Render props/HOC | 없음 → #29 |
| Flux/단방향 데이터 흐름·상태 위치·서버 상태 캐시 | 없음 → #29 |
| Islands | 부분(web-platform/10-rendering-strategies — CSR·SSR·하이드레이션까지) → #30 |
| Micro-frontends · UI composition | 없음 → #30 |

### 1.9 테스트·리팩터링·안티패턴

| 패턴 | 판정 |
|---|---|
| 테스트 대역 5종 | **있음**(testing/03) |
| Test Data Builder·Object Mother·Fresh/Shared Fixture | **있음**(testing/14) |
| Erratic Test | **있음**(testing/11-flaky-tests) |
| Obscure · Fragile · Slow Test, Assertion Roulette, Mystery Guest, Conditional Test Logic 등 테스트 스멜 | 부분(testing/02 거짓 양성) → #22 |
| Humble Object · Test-Specific Subclass · Custom Assertion · Parameterized Test | 없음 → #22 |
| Outside-in(이중 루프) TDD·인수 테스트·Walking Skeleton | 없음(testing/05는 Canon TDD 단일 루프) → #23 |
| Refactoring to Patterns(패턴 쪽으로·패턴에서 멀어지기) | 없음 → #7 |
| 코드 안티패턴(God Object·싱글턴 남용·BBoM·과설계) | **있음**(software-design/14) |
| 서버 구조·운영 안티패턴 29개 | **있음**(reliability/32) |
| DI 안티패턴(Service Locator·Control Freak·Ambient Context·Captive Dependency) | 없음 → #3 |

### 1.10 설계 추상화 수준 (코드로 표현하기)

| 주제 | 판정 |
|---|---|
| 패키지 by layer / feature / component, 가시성으로 경계 강제 | 없음(software-design/17은 컴포넌트 원칙만 다룸) → #2 |
| 의존 규칙의 **자동 검증**(아키텍처 테스트·순환 검사) | 부분(software-design/17 SCC) → #2 |
| 계층형·헥사고날·클린의 **코드 수준** 차이(포트 위치·매핑 비용·트랜잭션 경계) | 부분(software-design/16 — 원리) → #15 |
| DI·Composition Root·객체 수명 | 없음 → #3 |
| 예외 vs 결과 타입 선택 전략 | 부분(software-design/07, language/09) → #4 |
| 불변식 강제(값 객체·팩토리·스마트 생성자) | 부분(software-design/08·12, domain-modeling/04·05·08) → #5 |
| 패턴 카탈로그 지형·패턴 형식(맥락·힘·해법) | 없음 → #1 |

---

## 2. 신규 leaf 제안 (29개)

> 원칙: 패턴 하나에 leaf 하나를 두지 않고, **문제군** 단위로 묶었다. 한 leaf는 질문 5~8개로 닫혀야 한다(§0.4 규칙). 선행 칸은 전부 curriculum.md에 실제로 있는 slug다(같은 영역은 slug만 적었다).

### 2.1 software-design (`12.`) — 11개: "설계를 코드로 옮기는 층"

신설 단원 **12.4b 패턴 카탈로그 확장**(#1·#7·#8), **12.2b 코드로 표현하는 설계**(#2~#6), **12.5b 경계와 표현**(#9·#10·#15)으로 나눈다.

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 1 | 25-pattern-languages-and-catalogs | 패턴의 형식(맥락·힘·해법·결과)과 카탈로그 지형(GoF → POSA → PoEAA → EIP → microservices.io → 클라우드 패턴), 패턴 언어 | 13-design-patterns-gof | 이름만 빌리고 힘(forces)을 검토하지 않음 → 문제 없는 곳에 간접 계층 추가; **같은 이름 다른 뜻**(PoEAA Repository vs DDD Repository, Gateway vs API Gateway)으로 리뷰에서 서로 다른 것을 말함 | 패턴 관계 그래프(선행·대안·조합) | Alexander 『A Pattern Language』 1977 · Buschmann 외 POSA1 1996 · POSA5 "On Patterns and Pattern Languages" 2007 [?] · Azure "Combine patterns" 절 | 권장 | 신규 (연결: `engineering/design-patterns-gof` 우선순위표) |
| 2 | 26-package-structure-and-dependency-rules | package by layer·feature·component, `public` 최소화로 경계 강제, 아키텍처 테스트로 의존 규칙 자동 검증 | 17-component-principles, 16-layered-hexagonal-clean | 계층별 패키지 + 전부 `public` → 컨트롤러가 리포지토리를 직접 호출해 **서비스 계층 우회**가 조용히 누적; 기능 하나 수정에 패키지 5개 변경; 순환 의존으로 모듈 분리 불가 | 패키지 의존 그래프, **SCC 순환 탐지**(algorithm/18-scc), 가시성 규칙 | Simon Brown "The Missing Chapter"(『Clean Architecture』 34장) · ArchUnit 문서 [?] · Java 모듈 시스템(JEP 261) | 필수 | 신규 |
| 3 | 27-dependency-injection-and-composition-root | 생성자 주입·Composition Root·객체 수명(singleton/scoped/transient)·Separated Interface·Plugin, 안티패턴(Service Locator·Control Freak·Ambient Context·Captive Dependency) | 11-solid, 26 | 싱글턴 빈에 요청 범위 객체 주입(**captive dependency**) → 요청 간 상태 누출; Service Locator → 의존성이 시그니처에 안 보여 테스트 설정 누락 런타임 실패; 순환 주입 `BeanCurrentlyInCreationException`; 자기 호출 시 프록시 우회로 `@Transactional` 무시 | 의존 그래프 + 위상 정렬(생성 순서), 프록시(Interceptor) | Seemann–van Deursen 『Dependency Injection Principles, Practices, and Patterns』 2019 · Fowler "Inversion of Control Containers and the DI pattern" 2004 · PoEAA Separated Interface·Plugin | 필수 | 신규 (연결: `engineering/design-patterns-gof` "Spring이 대신 해주는 것") |
| 4 | 28-error-strategy-exceptions-vs-results | 예외 vs 결과 타입 선택 기준(예상 가능한 도메인 실패 vs 버그·인프라 장애), Railway-oriented 합성, Special Case/Null Object, 경계에서 에러 → HTTP·메시지로 번역 | 07-error-handling-design, language/09-error-handling-models | 도메인 실패("잔액 부족")를 예외로 → 흐름 제어에 예외 남용·트랜잭션 롤백 규칙 오작동; 결과 타입을 무시하고 `.get()`/`unwrap()` → 런타임 panic; 모든 실패를 500으로 번역 → 클라이언트가 재시도해 폭풍 | Result/Either의 bind 체인(모나드적 합성), 합 타입 에러 계층 | Wlaschin "Railway Oriented Programming" · PoEAA Special Case · APOSD 10장 · RFC 9457 | 필수 | 신규 |
| 5 | 29-making-illegal-states-unrepresentable | Parse don't validate, 스마트 생성자·팩토리로 불변식을 생성 시점에 강제, 합 타입(sealed)·원시값 집착 제거 | 12-design-by-contract, 08-immutability-and-value-objects, language/06-type-systems | 검증을 호출부마다 반복 → 한 경로 누락으로 **불법 상태 저장**(음수 금액·빈 이메일); `status` 문자열 + nullable 필드 조합 → "배송됐는데 주소 null"; 검증한 사실이 타입에 남지 않아 방어 코드 중복 | 합 타입(태그드 유니온), 정제 타입(newtype) | King "Parse, don't validate" 2019 · Minsky "Effective ML"(make illegal states unrepresentable) [?] · Wlaschin 『Domain Modeling Made Functional』 [?] | 필수 | 신규 (연결: `domain-modeling/04·05`) |
| 6 | 30-functional-core-imperative-shell | 순수한 결정 코어 + 부수효과 셸, 파이프라인 합성, "의존성 주입 대신 의존성 거부" | 29, language/10-functional-concepts | I/O가 비즈니스 결정 사이에 섞임 → 테스트마다 mock 5개 + 순서 검증(깨지기 쉬운 테스트); 시계·난수 직접 호출 → 재현 불가 버그 | 값 파이프라인(map/filter/fold), 결정 = 명령 값(Command 반환) | Bernhardt "Boundaries" SCNA 2012 · Seemann "Dependency rejection" 2017 [?] | 권장 | 신규 (연결: `testing/12-testing-time-and-concurrency`) |
| 7 | 31-refactoring-to-patterns | 스멜에서 패턴 쪽으로(Replace Conditional with Strategy/State/Polymorphism, Replace Type Code with Class, Introduce Null Object, Move Accumulation to Collecting Parameter), **패턴에서 멀어지기**(Inline Singleton 등) | 06-refactoring, 13-design-patterns-gof | 처음부터 패턴을 설계 → Speculative Generality; 분기 폭증을 방치 → 새 타입 추가마다 `switch` N곳 수정(Shotgun Surgery); 패턴을 제거하지 못해 간접 계층 화석화 | 조건 분기 → 다형 디스패치 테이블 | Kerievsky 『Refactoring to Patterns』 2004 · Fowler 『Refactoring』 2판 10장 [?] | 권장 | 신규 |
| 8 | 32-incremental-migration-strangler | Strangler Fig·Branch by Abstraction·Parallel Run(섀도 비교)·전환 스위치, ACL과 expand/contract와의 조합 | 18-monolith-vs-microservices, domain-modeling/15-anti-corruption-layer | 빅뱅 재작성 → 신·구 기능 격차로 출시 무기한 연기; 라우팅 전환 후 구 경로 제거 안 함 → 두 시스템 영구 병존; 이중 쓰기 비교 없이 전환 → 조용한 데이터 불일치 | 라우팅 규칙 표(경로 → 신/구), 결과 diff 비교기 | Fowler "StranglerFigApplication" 2004/2019 · Fowler "BranchByAbstraction" · Azure Strangler Fig · microservices.io Strangler Application | 권장 | 신규 (연결: `database/34-schema-migration`) |
| 9 | 33-ui-architecture-patterns | MVC 계보 — Smalltalk MVC → 서버 MVC(Front·Page Controller, Template View) → MVP·MVVM(양방향 바인딩) → 단방향(Flux/Elm) | 16-layered-hexagonal-clean | 컨트롤러에 규칙 집중(Massive Controller) → 규칙 재사용·테스트 불가; 양방향 바인딩 연쇄 → 값이 어디서 바뀌었는지 추적 불가; 뷰 템플릿에 로직 → 화면별 규칙 불일치 | 옵서버(데이터 바인딩), 디스패처 큐(Flux) | Fowler "GUI Architectures" 2006 · PoEAA 웹 프레젠테이션 패턴 · Flux 문서 "In-Depth Overview" | 권장 | 신규 |
| 10 | 34-data-across-boundaries | DTO·Remote Facade·Assembler/Mapper, 계층 간 모델 분리(요청 모델·도메인·영속 모델), 엔티티 직렬화 금지 | 16-layered-hexagonal-clean, api-design/09-schema-and-serialization | 엔티티를 그대로 JSON으로 → `LazyInitializationException`·**민감 필드 노출**·양방향 연관 무한 재귀; 세밀한 원격 인터페이스 → Chatty I/O(요청 1번에 왕복 수십 회); 매핑 코드 폭증 → 필드 추가 시 한 계층 누락 | 매퍼(필드 대응 표), 거친 입도(coarse-grained) 파사드 | PoEAA DTO·Remote Facade · Fowler "LocalDTO" 2004 [?] | 필수 | 신규 (연결: `database/33-orm-and-n-plus-one`) |
| 15 | 35-architecture-in-code | 유스케이스 하나를 **계층형·헥사고날·클린 세 방식으로 직접 구현**해 비교 — 포트 인터페이스 위치, 어댑터 방향, 매핑 비용, 트랜잭션·예외 경계 위치 | 16-layered-hexagonal-clean, 26, 27, 34 | "헥사고날" 폴더명만 있고 도메인이 JPA 엔티티를 import → 의존 방향 역전 실패; 포트를 기술 단위(`JpaPort`)로 만들어 교체 불가; 계층마다 1:1 매핑만 반복하는 의례적 구조 | 의존 그래프(DAG) 방향 검사 | Cockburn 2005 · Martin 『Clean Architecture』 22장 [?] · Graça "Explicit Architecture" 2017 [?] | 필수 | 신규 (연결: `domain-modeling/basic` 실습 1편을 예제로) |

### 2.2 domain-modeling (`13.`) — 1개

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 11 | 22-domain-logic-patterns-and-service-layer | Transaction Script·Table Module·Domain Model 3택의 선택 기준(복잡도 곡선), Service Layer = 유스케이스·트랜잭션 경계·권한 검사 위치, 명령-조회 분리(CQS) | 01-domain-vs-application-logic, 09-anemic-vs-rich-model | 규칙이 늘었는데 트랜잭션 스크립트 유지 → 같은 검증 N벌 복제; 단순 CRUD에 풍부한 모델 → 매핑 비용만 증가; 서비스 계층 없이 컨트롤러가 여러 리포지토리 호출 → 트랜잭션 경계가 요청마다 다름 | 유스케이스 = 명령 핸들러(입력 → 결과) | PoEAA 도메인 로직 패턴·Service Layer · Meyer CQS(『OOSC』) [?] | 필수 | 신규 |

### 2.3 database (`9.8 애플리케이션과 DB`) — 3개

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 12 | 41-data-source-patterns | Table/Row Data Gateway·Active Record·Data Mapper·Repository(PoEAA 정의)·Query Object·Metadata Mapping — "누가 SQL을 아는가" | 33-orm-and-n-plus-one, domain-modeling/08-repositories-and-factories | Active Record로 복잡한 도메인 → 저장 로직과 규칙이 한 클래스에 엉켜 DB 없이 테스트 불가; Data Mapper인데 도메인이 ORM 어노테이션 의존; 리포지토리가 `findByAAndBOrC…` 메서드 수십 개로 비대 | 메타데이터 매핑 표(필드 ↔ 컬럼), 쿼리 객체 = 조건 AST | PoEAA 데이터 소스 아키텍처·메타데이터 매핑 패턴 | 필수 | 신규 (연결: `engineering/data-access` comparison — Data Mapper 절) |
| 13 | 42-object-relational-structural-mapping | Identity Field(대리키 vs 자연키)·Embedded Value·Foreign Key / Association Table Mapping·Dependent Mapping·Serialized LOB·상속 매핑 3종(단일·클래스·구체 테이블) | 41, 03-normalization | 단일 테이블 상속 → nullable 컬럼 폭증·NOT NULL 제약 불가; 클래스 테이블 상속 → 조회마다 조인 N개; 값 객체를 별도 테이블 → 불필요한 식별자·고아 행; JSON LOB에 넣은 필드로 검색 요구 발생 → 풀스캔 | 조인 = 상속 계층 트리, 임베디드 값 = 컬럼 평탄화 | PoEAA O-R 구조 패턴 · JPA 명세 상속 전략 [?] | 권장 | 신규 |
| 14 | 43-offline-concurrency-patterns | 여러 요청에 걸친 **비즈니스 트랜잭션**의 동시성 — Optimistic / Pessimistic Offline Lock·Coarse-Grained Lock(aggregate 단위 버전)·Implicit Lock, 락 만료·해제 | 24-occ-and-timestamp-ordering, domain-modeling/05-aggregates-and-invariants | 편집 화면을 오래 연 사이 다른 사용자가 저장 → **lost update**(DB 트랜잭션은 이미 끝나 보호 안 됨); 비관적 오프라인 락 해제 누락 → "다른 사용자가 편집 중" 영구 표시; 자식만 수정해 루트 버전이 안 올라 aggregate 불변식 파괴 | 버전 번호 비교, 락 테이블(소유자·만료 TTL) | PoEAA 오프라인 동시성 패턴 | 권장 | 신규 (연결: `api-design/13-concurrency-control-in-apis`) |

### 2.4 language (`6.4 동시성 모델`) · os (`5.4`) — 2개

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 16 | language/22-concurrency-design-patterns | Executor·스레드 풀(크기·큐·거부 정책)·Future/Promise 합성·Active Object·Monitor Object·Scoped Locking(RAII/try-with-resources)·Thread-Specific Storage·**Double-Checked Locking의 함정**·불변 스냅샷 + 원자 참조 교체 | 15-concurrency-models, 14-language-memory-model, os/18-semaphores | 무한 큐 스레드풀 → 거부 없이 대기열 OOM; 공용 풀(ForkJoin common pool)에서 블로킹 → 전체 비동기 정지; `volatile` 없는 DCL → **반쯤 생성된 객체** 관측; 스레드풀에서 ThreadLocal 미정리 → 사용자 A 컨텍스트가 B 요청에 누출; `CompletableFuture` 예외 미처리 → 조용한 실패 | 블로킹 큐 + 워커, 완료 콜백 체인, CAS 참조 교체 | Schmidt 외 POSA2 2000 · Goetz 외 『Java Concurrency in Practice』 [?] · Pugh 외 "Double-Checked Locking is Broken" Declaration | 필수 | 신규 (연결: `data-structure/39-concurrent-data-structures`) |
| 17 | os/38-server-concurrency-architectures | 연결당 스레드 vs Reactor(단일·멀티 리액터) vs Proactor(IOCP·io_uring) vs Half-Sync/Half-Async(NIO 수신 + 워커 풀) vs Leader/Followers, Acceptor-Connector | 21-event-based-concurrency, 29-io-multiplexing-epoll, 30-zero-copy-and-io-uring | 연결당 스레드 → C10K에서 메모리·컨텍스트 스위칭 폭증; 리액터 스레드에서 DB 호출 → 모든 연결 동시 지연(Netty 이벤트 루프 블로킹); 반동기/반비동기 사이 큐 무한 → 지연 폭증 후 OOM | 준비 이벤트 디멀티플렉싱(epoll), 완료 큐(io_uring CQ), 핸드오프 큐 | Schmidt 외 POSA2 2000 · Kegel "The C10K problem" [?] · Netty 문서 [?] | 권장 | 신규 |

### 2.5 distributed (`10.5b 통합·메시징 패턴` 신설 단원) — 3개

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 19 | 33-message-types-channels-and-endpoints | 메시지 종류(Command·Event·Document), Correlation ID·Return Address·Expiration, 채널(P2P·Pub-Sub·Datatype·Dead Letter·Invalid Message), 소비 쪽 확장(Competing Consumers·Queue-Based Load Leveling·Priority Queue·Sequential Convoy·Selective Consumer) | 24-queues-logs-and-delivery-semantics, 26-consumer-failure-handling | 이벤트("주문됨")와 명령("결제하라")을 혼동 → 구독자가 늘 때마다 발행자 수정(결합 역전); Correlation ID 없는 요청-응답 → 응답을 엉뚱한 요청에 매칭; 경쟁 소비자로 순서 필요한 메시지 병렬 처리 → 상태 역행; 만료 없는 메시지 → 장애 복구 후 낡은 명령 일괄 실행 | 큐, **우선순위 큐(data-structure/07-heap)**, 키 해시 → 파티션(세션·순서 보장) | Hohpe–Woolf 『Enterprise Integration Patterns』 2003 · Azure Competing Consumers·Queue-Based Load Leveling·Priority Queue·Sequential Convoy | 필수 | 신규 (연결: `api-design/26-messaging-protocols`, `reliability/12-idempotency`) |
| 20 | 34-message-routing-and-transformation | Pipes-and-Filters, Content-based Router·Filter·Recipient List·Splitter/Aggregator·Resequencer·Scatter-Gather·Routing Slip, Translator·Enricher·Claim Check·Normalizer·Canonical Data Model, Wire Tap·Message Store | 33, 23-orchestration-vs-choreography | Aggregator 완료 조건 부재 → 영원히 기다리는 부분 집합이 메모리에 누적; 큰 페이로드를 브로커에 직접 → 메시지 크기 한도 초과·브로커 디스크 압박(Claim Check 누락); 필터 사이 공유 상태 → 파이프라인 병렬화 불가; Canonical 모델 강제 → 전사 공용 모델이 모든 팀 변경을 막음 | 파이프라인(필터 합성), 상관 키 → 버퍼 맵(Aggregator), **재정렬 버퍼 = 힙**(Resequencer) | Hohpe–Woolf EIP 2003 · Azure Claim Check·Pipes and Filters·Messaging Bridge | 권장 | 신규 (연결: `domain-modeling/14-context-mapping` Published Language) |
| 21 | 35-data-ownership-and-cross-service-queries | Database per Service vs Shared Database, API Composition·Command-side Replica·Materialized View·Index Table — 서비스 경계를 넘는 조회 | 21-outbox-and-dual-write, software-design/18-monolith-vs-microservices, domain-modeling/17-cqrs | 공유 DB → 한 팀의 스키마 변경이 다른 서비스 장애(분산 모놀리스); API Composition으로 목록 조회 → 서비스 N개 × 페이지 크기 호출(N+1의 분산판)·가장 느린 서비스가 전체 지연 결정; 복제 뷰 지연 → "주문했는데 목록에 없음" | 해시 조인(메모리 합성), 이벤트 → 프로젝션 폴드 | microservices.io Database per Service·API Composition·Command-side replica · Azure Materialized View·Index Table | 필수 | 신규 (연결: `reliability/32-server-design-antipatterns` "공유 데이터베이스") |

### 2.6 api-design (`15.3`) · reliability (`11.2·11.5`) — 5개

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 24 | api-design/27-api-gateway-and-bff | Gateway Routing·Aggregation·Offloading(인증·TLS·속도 제한)·Gatekeeper, BFF(클라이언트별 백엔드), Valet Key(직접 접근 위임) | 25-api-style-selection, network/39-load-balancers-and-proxies | 게이트웨이에 비즈니스 로직 축적 → 새 **분산 모놀리스**·배포 병목; 공용 게이트웨이 하나로 모바일·웹 요구 충돌 → 필드 과다 응답; 집계 호출에 타임아웃·부분 응답 정책 없음 → 하위 하나 지연이 전체 지연; 게이트웨이 SPOF | 경로 → 백엔드 라우팅 테이블(접두사 트리), 병렬 팬아웃 + 데드라인 | microservices.io API gateway·BFF · Azure Gateway Routing·Aggregation·Offloading·Gatekeeper·BFF·Valet Key · Newman "Backends For Frontends" 2015 [?] | 필수 | 신규 |
| 25 | reliability/36-sidecar-ambassador-and-service-mesh | Sidecar·Ambassador, 서비스 메시(데이터·컨트롤 플레인, mTLS·재시도·관측 위임), Microservice Chassis(라이브러리) vs 메시, 서비스 디스커버리(클라이언트·서버 측, 레지스트리, 자기·제3자 등록) | network/39-load-balancers-and-proxies, os/34-containers-namespaces-cgroups, 07-retry-backoff-jitter | 앱 재시도 + 메시 재시도 중복 → **곱셈 증폭**; 사이드카 준비 전 앱 시작 → 기동 직후 연결 실패; 레지스트리에 죽은 인스턴스 잔존 → 간헐적 연결 거부; 메시 설정 오류 하나가 전 서비스 장애 | 서비스 레지스트리(키-값 + TTL 하트비트), 프록시 체인 | Azure Sidecar·Ambassador · microservices.io Service discovery·Microservice chassis · Burns–Oppenheimer "Design Patterns for Container-based Distributed Systems" HotCloud 2016 [?] | 권장 | 신규 |
| 26 | reliability/35-performance-and-stability-antipatterns-in-code | 코드 수준 안티패턴 — Chatty I/O·Extraneous Fetching·Improper Instantiation(요청마다 HTTP 클라이언트·커넥션 생성)·Synchronous I/O·Busy Database·Busy Front End·Monolithic Persistence, Nygard의 Integration Points·Blocked Threads·Unbounded Result Sets·Self-Denial·Dogpile | 32-server-design-antipatterns, database/32-connection-pooling | 요청마다 `new HttpClient` → 소켓 고갈 `TIME_WAIT` 폭증·`EADDRNOTAVAIL`; `LIMIT` 없는 조회 → 데이터가 커진 어느 날 OOM; 스레드 풀 전부 느린 외부 호출에 묶임(Blocked Threads) → 헬스체크까지 실패; 자정 배치·쿠폰 공지 → 자기 트래픽이 DoS(Self-Denial·Dogpile) | 풀링(공유 인스턴스), 배치·페이지네이션 | Azure 성능 안티패턴 카탈로그 · Nygard 『Release It!』 2판 4장 "Stability Antipatterns" [?] | 필수 | 신규 (reliability/32와 구분 — 32는 구조·운영, 이쪽은 코드 수준) |
| 27 | reliability/37-cells-stamps-and-blast-radius | Deployment Stamps·셀 기반 아키텍처·Geode·셔플 샤딩 — 장애 반경을 구조로 제한 | 28-high-availability-topology, software-design/19-multi-tenancy | 전역 공유 구성 요소 하나 장애 → 전 고객 동시 중단; 셀 라우팅 계층 자체가 SPOF; 셀 간 데이터 이동(재배치) 절차 부재 → 대형 테넌트가 셀 하나를 포화 | 테넌트 → 셀 매핑(일관 해싱 data-structure/31), 셔플 샤딩 조합 | Azure Deployment Stamps·Geode · AWS Well-Architected "Reducing the Scope of Impact with Cell-Based Architecture" [?] · AWS Builders' Library "Workload isolation using shuffle-sharding" [?] | 권장 | 신규 |
| 28 | reliability/38-steady-state-fail-fast-and-supervision | Steady State(무한 증가 자원 정리 — 로그·세션·캐시·테이블), Fail Fast(입구 검증), Let It Crash + 감독 트리, Handshaking, Governor(자동화 속도 제한), Test Harness | 11-backpressure-and-load-shedding, 14-graceful-shutdown | 정리 작업 없음 → 수개월 뒤 디스크 풀·테이블 비대로 서서히 느려짐; 자원 부족을 끝까지 가서야 발견 → 이미 부분 처리된 작업 롤백; 손상된 상태로 계속 실행 → 오염 전파(재시작이 나았음); 자동 스케일-인·정리 스크립트 폭주 → 전 인스턴스 삭제(Governor 부재) | 감독 트리(재시작 전략 one_for_one 등), 보존 정책(TTL·링 버퍼) | Nygard 『Release It!』 2판 5장 "Stability Patterns" · Armstrong 박사논문 2003 (Erlang 감독) [?] | 권장 | 신규 (연결: `language/15-concurrency-models` 액터) |

### 2.7 testing (`14.`) — 2개

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 22 | 20-test-smells-and-xunit-patterns | 테스트 스멜(Obscure·Fragile·Slow Test, Assertion Roulette, Mystery Guest, Conditional Test Logic, Test Code Duplication)과 처방 패턴(Humble Object·Custom Assertion·Parameterized Test·Test-Specific Subclass·Delegated Setup) | 02-good-unit-tests, 14-test-data-and-fixtures | 무엇을 검증하는지 안 보이는 테스트 → 실패해도 원인 파악에 30분; 단언 10개 한 테스트 → 첫 실패에서 멈춰 나머지 결함 은폐; 테스트 안 `if` → 분기 한쪽만 검증; UI·프레임워크에 로직 → 테스트 불가(Humble Object 부재) | 파라미터 표(데이터 주도), 겸손한 객체 = 로직/접착 분리 | Meszaros 『xUnit Test Patterns』 2007 · xunitpatterns.com | 권장 | 신규 |
| 23 | 21-outside-in-tdd-and-acceptance-tests | 이중 루프 TDD(인수 테스트 → 단위 테스트), Walking Skeleton, 인수 테스트·BDD(Given-When-Then)의 추상화 수준, 협력 객체 발견을 위한 mock | 05-tdd, 04-classical-vs-london | 단위 테스트만 초록 → 기능 전체는 동작 안 함(조립 누락); UI 조작 단계로 쓴 인수 테스트 → 화면 변경마다 전부 파손(추상화 수준 오류); 골격 없이 계층별로 완성 → 통합 시점에 대량 불일치 | 테스트 DSL(도메인 동사 계층) | Freeman–Pryce 『Growing Object-Oriented Software, Guided by Tests』 2009 · North "Introducing BDD" 2006 [?] | 권장 | 신규 |

### 2.8 web-platform (`16.` — 「프론트엔드 설계」 단원 신설) — 2개

| # | slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|---|
| 29 | 14-component-and-state-patterns | 컴포넌트 합성(Compound·Container/Presentational → 커스텀 훅·Render props), 제어/비제어 컴포넌트, 단방향 데이터 흐름(Flux/Redux/Elm), 상태 위치 선정(로컬·끌어올리기·전역), **서버 상태 캐시 vs 클라이언트 상태**, 파생 상태 | 04-dom-and-event-model, 03-event-loop, software-design/33-ui-architecture-patterns | 서버 데이터를 전역 스토어에 복사 → 오래된 값·수동 무효화 누락; props를 state로 복사(파생 상태) → 부모 변경이 반영 안 됨; 전역 스토어 하나 변경에 전 트리 리렌더 → 입력 지연(INP); prop drilling 10단계 | 불변 상태 트리 + 리듀서(폴드), 구조 공유(data-structure/26), 키 기반 캐시 + stale-while-revalidate | patterns.dev (Container/Presentational·Hooks·Compound) · Flux 문서 · Redux 문서 "Three Principles" [?] | 권장 | 신규 |
| 30 | 15-islands-and-micro-frontends | Islands(서버 HTML + 부분 하이드레이션), Micro-frontends(빌드 타임 vs 런타임 통합 — iframe·Web Components·Module Federation), 서버·클라이언트 측 UI 조합 | 10-rendering-strategies, 09-js-modules-and-bundling, 29 | 마이크로 프론트엔드마다 React 사본 → 번들 중복·**싱글턴 라이브러리 두 벌**(훅 오류); 팀 간 CSS 충돌; 공유 상태를 전역 객체로 주고받음 → 숨은 결합; 섬 사이 통신 부재 → 같은 데이터 이중 fetch | 모듈 그래프 공유(dedupe), 이벤트 버스 | Miller "Islands Architecture" 2020 · Jackson "Micro Frontends" (martinfowler.com) 2019 · microservices.io Client-side UI composition | 심화 | 신규 |

> **번호 메모**: #18은 결번이다. 동시성의 RCU·seqlock leaf(os/39)를 검토했지만 심화·커널 특화라 **제안에서 뺐고**, #16의 "불변 스냅샷 + 원자 참조 교체" 절로 흡수했다. 최종 제안 수는 **29개**다(번호 1~30, #18 결번).

---

## 3. 패턴 지도 제안 — 어느 패턴군을 어디에

### 3.1 원칙

1. **패턴은 그 패턴이 푸는 "문제"가 사는 영역에 둔다.** 패턴 카탈로그 전용 영역은 만들지 않는다. 예: Unit of Work는 DB 영역, Competing Consumers는 분산 영역, Reactor는 OS 영역. 카탈로그 영역을 따로 만들면 ⚠ 칸(깨지면 보이는 형태)이 문제 영역에서 떨어져 나가 교육 철학(§0.1)과 충돌한다.
2. 대신 **허브 leaf 1개**(#1 `software-design/25-pattern-languages-and-catalogs`)가 카탈로그 → leaf 역링크 표를 갖는다. 위 §1 점검표가 그 표의 초안이다.
3. **software-design에 "설계를 코드로 옮기는 층"을 명시적인 단원으로 세운다.** 사용자 문제의식("추상화 수준을 잡아야 코드로 표현")에 직접 답하는 부분이다.

### 3.2 영역별 배치도

```text
software-design (12)
  12.1 복잡도와 모듈            01~03
  12.2 코드 수준                04~08
  12.2b 코드로 표현하는 설계 ★신설  26 패키지 구조 · 27 DI · 28 에러 전략 · 29 불법 상태 차단 · 30 함수형 코어
  12.3 객체지향                 09~12
  12.4 패턴                     13 GoF · 14 안티패턴
  12.4b 패턴 확장 ★신설          25 패턴 지형(허브) · 31 패턴 쪽으로 리팩터링 · 32 점진 이전(Strangler)
  12.5 아키텍처                 15~22
  12.5b 경계와 표현 ★신설        33 UI 아키텍처(MVC 계보) · 34 경계 넘는 데이터(DTO) · 35 아키텍처를 코드로(3방식 비교 실습)
domain-modeling (13)   13.1 기초 + 22 도메인 로직 패턴·Service Layer
database (9)           9.8 애플리케이션과 DB + 41 데이터 소스 · 42 O-R 구조 매핑 · 43 오프라인 동시성   ← PoEAA의 집
language (6)           6.4 동시성 모델 + 22 동시성 설계 패턴(POSA2 객체 수준)
os (5)                 5.4 영속성·I/O + 38 서버 동시성 아키텍처(POSA2 이벤트 처리)
distributed (10)       10.5b 통합·메시징 패턴 ★신설  33 메시지·채널·엔드포인트 · 34 라우팅·변환 · 35 데이터 소유·교차 조회   ← EIP·microservices.io의 집
api-design (15)        15.3 + 27 API 게이트웨이·BFF
reliability (11)       11.2 + 35 코드 수준 안티패턴 · 36 사이드카·메시 · 38 Steady State·감독
                       11.5 + 37 셀·스탬프·장애 반경                  ← Nygard·Azure의 집
testing (14)           + 20 테스트 스멜·xUnit 패턴 · 21 outside-in TDD
web-platform (16)      「프론트엔드 설계」 ★신설 단원  14 컴포넌트·상태 · 15 Islands·마이크로 프론트엔드
```

### 3.3 카탈로그 → 주 거처 요약

| 카탈로그 | 주 거처 | 보조 |
|---|---|---|
| GoF | software-design/13 | 31(리팩터링 경로), 27(DI가 흡수한 생성 패턴) |
| POSA1 | software-design/15(Layers·Microkernel) | distributed/34(Pipes and Filters), software-design/33(MVC) |
| POSA2 | language/22(객체 수준) · os/38(이벤트 처리) | os/17·21, language/14 |
| PoEAA | database/33·41·42·43 · domain-modeling/22 | software-design/33·34·27·28, domain-modeling/11(Money) |
| EIP | distributed/33·34 | distributed/21·23·24·26, reliability/12 |
| microservices.io | software-design/18·32 · distributed/35 · api-design/27 | reliability/36, testing/08 |
| Azure 클라우드 패턴 | reliability/06~13·36·37 | api-design/14·27, database/30·38 |
| Azure 성능 안티패턴 + Nygard 안티패턴 | reliability/35 | reliability/32·33 |
| Nygard 안정성 패턴 | reliability/06·08·09·11·38 | — |
| xUnit Test Patterns | testing/03·14·20 | testing/11 |
| 함수형·타입 패턴 | software-design/28·29·30 | language/09·10 |
| 프론트엔드 패턴 | web-platform/14·15 | software-design/33 |

### 3.4 신설 영역 필요성 판단

- **신설 영역은 필요 없다.** 18영역 구조가 문제 영역별로 이미 나뉘어 있어서 각 패턴군이 들어갈 자리가 있다.
- **신설 단원은 5개**다. software-design 12.2b·12.4b·12.5b, distributed 10.5b, web-platform 「프론트엔드 설계」. web-platform은 지금 "개념만" 영역으로 정의돼 있으므로, 프론트엔드 설계 단원을 넣으려면 영역 정의 한 줄(§16 머리말)을 바꿔야 한다. **사용자 결정 사항**이다.
- 제안을 모두 반영하면 leaf 수는 다음과 같이 바뀐다. software-design 24→35, database 40→43, distributed 32→35, reliability 34→38, testing 19→21, web-platform 13→15, language 21→22, os 37→38, domain-modeling 21→22, api-design 26→27. 합계 517→546이다.
- 필수 등급 신규는 **13개**다(#2·3·4·5·10·11·12·15·16·19·21·24·26). 나머지는 권장 15개, 심화 1개(#30)다.
- **학습 순서 권고**: software-design 12.2b(26 → 27 → 28 → 29)를 12.3 객체지향 **직후**, 12.4 패턴 **전**에 둔다. "패턴 이전에 경계·의존·에러·불변식을 코드로 쓰는 법"이 먼저 서야 패턴이 간접 계층 장식이 되지 않는다. 35(아키텍처를 코드로)는 12.5 아키텍처 뒤 실습으로 둔다.

---

## 4. 확인하지 못한 것 (`[?]` 모음)

- POSA 1·3·4·5권 목차. POSA1 패턴 목록은 기억에 기댄 것이라 재확인이 필요하다.
- 『Release It!』 2판 안정성 패턴의 정확한 수와 장 번호. 요약본에서는 8개를 확인했다. Let It Crash·Shed Load·Create Back Pressure·Governor는 원서에서 재확인해야 한다.
- 『xUnit Test Patterns』 테스트 스멜 전체 목록, Kerievsky 리팩터링 27개 전체 목록.
- ArchUnit·Netty·JPA 상속 전략 문서, Minsky "Effective ML", Wlaschin 『Domain Modeling Made Functional』, Seemann "Dependency rejection", Graça "Explicit Architecture", Newman BFF 글, Burns–Oppenheimer HotCloud 2016, AWS 셀 기반 아키텍처·셔플 샤딩 문서, Armstrong 박사논문, Goetz 『JCIP』, Kegel C10K, North BDD, Redux 문서 — 모두 제목 수준에서만 인용했다.
- 기존 노트 `cs/systems/server-design/11-antipatterns.md`는 절 제목만 확인했다. #26과 겹치지 않는다는 판정은 제목 수준 판정이다.
