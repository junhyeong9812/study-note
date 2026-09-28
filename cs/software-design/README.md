# 소프트웨어 설계 — `cs/software-design/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §12에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 49 · 원고 있음 5 · 초안(Claude) 2 · 검수 완료 0

> 복잡도 → 모듈 → 코드 수준 → OOP → 패턴 → 아키텍처 → 품질 속성. 소프트웨어 설계에서 "깨지면"은 크래시가 아니라 **변경 비용 폭증·조용한 결합**으로 보인다 — ⚠ 칸은 스멜과 변경 시 증상으로 적는다. 2026-09-28 병합으로 **설계를 코드로 옮기는 층**(12.2b)·**패턴 확장과 프레임워크 합성**(12.4b·12.4c)·**경계와 표현**(12.5b)·**유지보수성 판단**(12.1b·12.2a·12.5c — "언제·얼마나·어떤 순서로 바꾸나")을 더했다.
> 뼈대: Ousterhout 『A Philosophy of Software Design』 2판(이하 APOSD), Fowler 『Refactoring』 2판, Martin 『Clean Architecture』, GoF, Parnas 1972, ISO/IEC 25010:2023, SWEBOK v4 Design·Architecture KA.

## 12.1 복잡도와 모듈

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `complexity` | 복잡도의 3증상(변경 증폭·인지 부하·unknown unknowns)과 2원인(의존·모호) | 필수 | 미작성 | — |
| 02 | `modularity-coupling-cohesion` | 정보 은닉·결합도·응집도 (분해 기준 — 바뀔 결정을 숨긴다 — 은 37로 넘긴다) | 필수 | 미작성 | — |
| 03 | `deep-modules-and-abstraction` | 깊은 모듈·좋은 인터페이스·추상화 계층 | 권장 | 미작성 | — |

## 12.1b 변경 축 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `decompose-by-change` | 분해 기준 = **바뀔 결정을 숨긴다**. 처리 단계(흐름도)로 나누지 않는다. KWIC 두 분해 비교, 변동성 축 찾기(무엇이 어떤 이유로 얼마나 자주 바뀌나), 기능 분해의 함정 | 필수 | 미작성 | — |
| 05 | `connascence` | 결합을 **종류·강도·지역성·정도**로 재는 어휘다. 이름 → 타입 → 의미 → 위치 → 알고리즘(정적), 실행 순서 → 타이밍 → 값 → 동일성(동적). 강한 것은 약하게 바꾸고, 멀리 떨어질수록 약한 것만 허용한다 | 권장 | 미작성 | — |

## 12.2 코드 수준

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 06 | `clean-code` | 좋은 코드의 5속성(CLEAN — Cohesive·Loosely coupled·Encapsulated·Assertive·Nonredundant)과 속성 간 긴장 — 품질 검사표. 이름·함수·주석은 07·08·09로 분리 | 필수 | 초안(Claude) | [../engineering/clean-code](../engineering/clean-code/) |
| 10 | `code-smells` | 스멜 카탈로그(Shotgun Surgery·Divergent Change·Speculative Generality·Feature Envy 등) — Mäntylä 분류(Bloaters·OO Abusers·Change Preventers·Dispensables·Couplers) [?]로 묶고, 질문이 10개를 넘으면 05a(Change Preventers·Couplers)·05b(Bloaters·Dispensables)로 분할 | 필수 | 미작성 | — |
| 13 | `refactoring` | 동작 보존 변환·작은 단계·테스트 안전망 | 필수 | 미작성 | — |
| 15 | `error-handling-design` | fail-fast·예외 경계·에러 정의로 없애기 | 필수 | 미작성 | — |
| 19 | `immutability-and-value-objects` | 불변 객체·값 의미론 | 권장 | 미작성 | — |

## 12.2a 가독성 — 06 분할 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 07 | `naming` | 이름 = 추상화 수준의 첫 표현. 의도 드러내기, 도메인 어휘(ubiquitous language), 범위에 비례한 길이, 모호어(`data`·`info`·`manager`·`process`) 금지, 부정 boolean 피하기, 이름 붙이기 어렵다 = 책임이 불명확하다는 설계 신호 | 필수 | 미작성 | — |
| 08 | `function-design` | 함수 하나 = 한 추상화 수준(SLAP). 인자 수와 인자 객체, **플래그 인자 금지**, CQS(명령은 상태를 바꾸고, 질의는 값만 돌려준다), 출력 인자 금지, 가드 절, 함수 길이보다 깊이 | 필수 | 미작성 | — |
| 09 | `comments-and-conventions` | 주석이 필요한 자리: **왜**(결정·제약·외부 사정·버그 번호), 인터페이스 계약, 놀라운 동작. 불필요한 주석(what 반복·주석 처리된 코드·낡은 주석). 일관성: 팀 관례·포매터·린터로 논쟁 제거 | 권장 | 미작성 | — |

## 12.2b 코드로 표현하는 설계 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 16 | `error-strategy-exceptions-vs-results` | 예외 vs 결과 타입 선택 기준(예상 가능한 도메인 실패 vs 버그·인프라 장애), Railway-oriented 합성, Special Case/Null Object, 경계에서 에러 → HTTP·메시지로 번역 | 필수 | 미작성 | — |
| 17 | `error-messages-and-log-level-policy` | 로그 레벨의 조작적 정의(ERROR = 사람 조치 필요, WARN = 자동 복구됨 등), 사용자용·개발자용 메시지 분리, 에러 코드 체계, 한 번만 로깅 | 필수 | 미작성 | — |
| 18 | `absence-and-null-design` | "없음"의 설계: null 반환 vs 빈 컬렉션 vs `Optional` vs Null Object vs 예외. Optional 남용(필드·인자), null 경계 정하기(경계에서 제거하고 안쪽은 non-null 가정), 기본값의 의미 | 권장 | 미작성 | — |
| 24 | `types-as-invariants` | 원시 타입 집착 제거(ID·이메일·수량을 전용 타입으로), **parse, don't validate**(경계에서 한 번 파싱해 검증된 타입 반환), 불법 상태를 표현할 수 없게(합 타입·`sealed`, 필드 조합 대신 상태별 타입), 스마트 생성자·팩토리로 생성 시점에 불변식 확보 | 필수 | 미작성 | — |
| 25 | `dependency-injection-and-composition-root` | 생성자 주입·Composition Root(조립은 한 곳)·객체 수명(singleton/scoped/transient). 테스트하기 어려움 = 설계 신호 — 시계·난수·UUID 같은 **숨은 입력**도 주입한다. 안티패턴: Service Locator·Control Freak(`new` 숨김)·Ambient Context·정적 호출·Captive Dependency (Separated Interface·Plugin은 36) | 필수 | 미작성 | — |
| 26 | `functional-core-imperative-shell` | 결정은 순수 함수(코어), I/O·DB·시간은 바깥 껍질(셸). "읽기 → 결정 → 쓰기" 샌드위치, 값 파이프라인 합성, 결정을 명령 값으로 반환, "의존성 주입 대신 의존성 거부" | 권장 | 미작성 | — |

## 12.3 객체지향

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 20 | `oop-fundamentals` | 캡슐화·상속·다형성·추상 클래스, IS-A/HAS-A | 필수 | 원고 있음 | [../foundations/oop-basics](../foundations/oop-basics/) |
| 21 | `composition-over-inheritance` | 상속의 비용·취약한 기반 클래스·위임 | 권장 | 미작성 | — |
| 22 | `solid` | SRP·OCP·LSP·ISP·DIP | 필수 | 원고 있음 | [../engineering/solid-principles](../engineering/solid-principles/) |
| 23 | `design-by-contract` | 사전조건·사후조건·클래스 불변식 | 권장 | 미작성 | — |

## 12.4 패턴

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 27 | `design-patterns-gof` | 생성·구조·행위 패턴 23 | 필수 | 초안(Claude) | [../engineering/design-patterns-gof](../engineering/design-patterns-gof/) |
| 31 | `antipatterns` | God Object·싱글턴 남용·Big Ball of Mud·과설계 | 권장 | 미작성 | — |

## 12.4b 패턴 확장 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 28 | `taming-conditionals` | if 지옥 해소의 **도구 선택**: 가드 절 → 분해 → 테이블(맵) 기반 → 다형성(Strategy·State) → 규칙 엔진, 각각을 언제 쓰나. 같은 `switch`가 여러 곳에 반복되는 것이 진짜 신호. 설정 조합 폭발 (패턴 쪽 리팩터링 경로는 29) | 필수 | 미작성 | — |
| 29 | `refactoring-to-patterns` | 스멜에서 패턴 쪽으로(Replace Conditional with Strategy/State/Polymorphism, Replace Type Code with Class, Introduce Null Object, Move Accumulation to Collecting Parameter), **패턴에서 멀어지기**(Inline Singleton 등) | 권장 | 미작성 | — |
| 30 | `pattern-languages-and-catalogs` | 패턴의 형식(맥락·힘·해법·결과)과 카탈로그 지형(GoF → POSA → PoEAA → EIP → microservices.io → 클라우드 패턴), 패턴 언어. 카탈로그 → leaf 역링크 표를 갖는 **허브** leaf | 권장 | 미작성 | — |

## 12.4c 프레임워크가 돕는 합성 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 32 | `inversion-of-control-and-framework-flow` | 제어 역전 — 흐름은 프레임워크가 쥐고 내 코드는 불린다("Don't call us, we'll call you"). 템플릿 메서드(골격은 상위, 단계는 하위가 채움)와 콜백(함수를 넘겨 나중에 호출), 라이브러리(내가 부름) vs 프레임워크(나를 부름) | 필수 | 미작성 | — |
| 33 | `aop-and-proxies` | 횡단 관심사(트랜잭션·로깅·보안)를 프록시로 끼워 넣기: JDK dynamic proxy(인터페이스 기반) vs CGLIB(서브클래스 생성), Spring AOP(프록시 기반 메서드 가로채기), TS 데코레이터(클래스·메서드 래핑), 여러 어드바이스의 프록시 순서 | 필수 | 미작성 | — |
| 34 | `middleware-filter-interceptor-chains` | 요청 처리 파이프라인을 체인으로 합성: Servlet Filter, Spring HandlerInterceptor, Express·Koa(`next()`)·NestJS 미들웨어, 그 뼈대인 Chain of Responsibility. 등록 순서 = 실행 순서 | 필수 | 미작성 | — |
| 35 | `annotation-and-metadata-programming` | 선언(어노테이션)을 읽어 동작을 만드는 두 방식: 런타임 리플렉션(프레임워크가 기동 시 스캔) vs 컴파일 타임 어노테이션 처리(Lombok·MapStruct가 코드 생성). 보존 정책(`@Retention`) | 권장 | 미작성 | — |
| 36 | `extension-points-and-plugins` | 코드를 고치지 않고 기능을 끼우는 확장 지점: SPI(인터페이스는 공개, 구현은 외부), Java `ServiceLoader`, Spring Boot 자동 설정(조건부 빈), 이벤트 리스너, PoEAA Separated Interface·Plugin | 권장 | 미작성 | — |

## 12.5 아키텍처

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 37 | `architecture-styles` | 계층·이벤트 기반·마이크로커널·공간 기반·서비스 기반 등 | 필수 | 원고 있음 | [../systems/architecture-styles](../systems/architecture-styles/) |
| 38 | `layered-hexagonal-clean` | 의존 방향 규칙·포트와 어댑터·클린 아키텍처 | 필수 | 미작성 | — |
| 39 | `component-principles` | REP·CCP·CRP·ADP·SDP·SAP | 권장 | 미작성 | — |
| 45 | `monolith-vs-microservices` | 모듈러 모놀리스·서비스 분해·분산 모놀리스, 전환 시점(언제 쪼개나) | 필수 | 미작성 | — |
| 46 | `quality-attributes-and-tradeoffs` | 품질 속성(가용성·성능·확장성·유지보수성·동시성·UX)과 트레이드오프 | 필수 | 원고 있음 | [../engineering/engineering-axes](../engineering/engineering-axes/) |
| 47 | `architecture-decision-records` | ADR — 결정·맥락·결과 기록 | 권장 | 미작성 | — |
| 48 | `configuration-and-12factor` | 설정·환경 분리·12-factor | 권장 | 미작성 | — |
| 49 | `multi-tenancy` | 테넌트 격리 모델(사일로·풀·브리지)·noisy neighbor | 권장 | 원고 있음 | [../systems/multi-tenancy](../systems/multi-tenancy/) |

## 12.5b 경계와 표현 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 40 | `codebase-structure` | 패키지 배치: by layer vs by feature vs **by component**, 가시성(package-private·`public` 최소화)으로 경계 강제, "소리치는 아키텍처"(최상위 폴더가 도메인을 말한다), 공통(`common`·`util`) 폴더의 함정 (규칙의 자동 검증은 41) | 필수 | 미작성 | — |
| 41 | `architecture-fitness-rules` | 경계를 **테스트로 강제**한다. ArchUnit(Java)·dependency-cruiser(JS/TS)·import-linter(Python)로 계층·순환·명명 규칙 검사, 기존 위반 동결(baseline). 순환 **제거** 기법(DIP 역전, 공통부 추출, 합치기, 이벤트) | 권장 | 미작성 | — |
| 42 | `ui-architecture-patterns` | MVC 계보 — Smalltalk MVC → 서버 MVC(Front·Page Controller, Template View) → MVP·MVVM(양방향 바인딩) → 단방향(Flux/Elm) | 권장 | 미작성 | — |
| 43 | `data-across-boundaries` | DTO·Remote Facade·Assembler/Mapper, 계층 간 모델 분리(요청 모델·도메인·영속 모델), 엔티티 직렬화 금지 | 필수 | 미작성 | — |
| 44 | `architecture-in-code` | 유스케이스 하나를 **계층형·헥사고날·클린 세 방식으로 직접 구현**해 비교 — 포트 인터페이스 위치, 어댑터 방향, 매핑 비용, 트랜잭션·예외 경계 위치 | 필수 | 미작성 | — |

## 12.5c 유지보수성 판단 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 11 | `when-to-abstract` | 추상화 **시점**: rule of three, "잘못된 추상화보다 중복이 훨씬 싸다", DRY = 지식의 단일 표현이지 글자 중복 제거가 아니다, 우연한 중복 판별(함께 바뀌나), 잘못된 추상화에서 되돌아가기(인라인 후 재추출) | 필수 | 미작성 | — |
| 12 | `simple-design-and-yagni` | Beck 단순 설계 4규칙(테스트 통과 → 의도 드러냄 → 중복 없음 → 요소 최소, 우선순위 순). YAGNI의 비용 4종(build·delay·carry·repair). **확장점은 두 번째 요구가 올 때** 만든다 | 필수 | 미작성 | — |
| 14 | `tidy-first` | **구조 변경과 동작 변경을 섞지 않는다.** 정리(tidying) 목록(가드 절·죽은 코드 삭제·대칭 맞추기·설명 변수 등), 정리 시점(먼저·나중·나중에 따로·안 함), 커밋·PR 분리, 결합과 응집의 경제학(옵션 가치) | 권장 | 미작성 | — |
| 50 | `legacy-migration-strangler-fig` | Strangler Fig, branch by abstraction, 병행 실행·결과 비교(shadow·Parallel Run), 라우팅 전환과 되돌리기, ACL·expand/contract와의 조합, 빅뱅 재작성의 위험 (코드 수준 변경 기법은 51) | 권장 | 미작성 | — |
| 51 | `legacy-change-techniques` | 레거시 변경 알고리즘(변경점 찾기 → 테스트 지점 → 의존 끊기 → 테스트 → 변경), seam 종류와 enabling point, **sprout method/class, wrap method/class**, 의존 끊기 기법(인터페이스 추출·매개변수화), 코드 인터페이스의 parallel change(expand → migrate → contract) | 필수 | 미작성 | — |
| 52 | `complexity-metrics` | 순환 복잡도(McCabe, 독립 경로 수 = 최소 테스트 수), 인지 복잡도(중첩 가중·선형 흐름 단절), 크기·중첩 깊이. **지표의 한계**(게이밍, 맥락 없음) | 권장 | 미작성 | — |
| 53 | `code-forensics-hotspots` | git 이력으로 보는 유지보수성: **핫스팟 = 변경 빈도 × 복잡도**, change coupling(함께 커밋되는 파일 = 숨은 결합), 지식 분포(bus factor), 부채 상환 우선순위 결정 | 권장 | 미작성 | — |
| 54 | `designing-for-deletion` | **지우기 쉬운 코드**: 결합이 적은 단위로 나누기, 확장보다 교체, 죽은 코드 찾기와 제거(미사용 탐지·호출 로그), 플래그 분기 코드 걷어내기, 주석 처리 코드 금지(git이 기억한다), 내부 deprecate 절차 | 권장 | 미작성 | — |

## 12.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 55 | `design-symptom-index` | 역색인: "작은 변경에 파일 N개", "테스트 작성 불가", "배포를 같이 해야 함", "이 클래스는 아무도 못 건드림" → 원인 스멜·원칙. 추가: 공통 함수 인자만 계속 늘어남(11), 테스트에 DB·mock 도배(25·26), 기능 하나에 폴더 4개(40), 리팩터링 어디부터?(53), 플래그·죽은 코드 누적(54), 불법 상태 행(24), NPE(18), switch 복제(28), `@Transactional` 미적용(33), 미들웨어 순서 역전(34) | 필수 | 미작성 | — |
| 56 | `design-incidents` | 실사건: Therac-25(1985–87, 재사용 코드의 하드웨어 인터록 가정 + 경쟁 조건) · Healthcare.gov 출시 장애(2013, 통합·아키텍처) | 권장 | 미작성 | — |
