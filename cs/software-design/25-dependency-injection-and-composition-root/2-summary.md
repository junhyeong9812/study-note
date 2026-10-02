# software-design/25-dependency-injection-and-composition-root — 의존성 주입과 조립 지점 — 정리 (힌트)

## 해결하는 문제

클래스가 자기 협력 객체를 **스스로 만들거나 몰래 가져오면**, 바꿀 수도 시험할 수도 없다.

```text
 스스로 만든다 (Control Freak)                 받는다 (생성자 주입)
 class Billing {                               class Billing {
   repo  = new JdbcRepo(url)  ← 구체 고정        Billing(Repo repo, Clock clock)
   today = LocalDate.now()    ← 숨은 입력       }
 }                                             누가 무엇을 줄지는 바깥 한 곳(조립 지점)이 정한다
 시험: 진짜 DB·진짜 시계가 필요               시험: 가짜 Repo·Clock.fixed(...)를 넘긴다
```

- *의존성 주입(Dependency Injection, DI)*: 객체가 쓸 협력 객체를 스스로 만들지 않고 바깥에서 받는 것. Fowler(2004)가 "Inversion of Control은 너무 일반적인 말"이라며 이 이름을 붙였다.
- *숨은 입력(hidden input)*: 인자에 안 보이는데 결과를 바꾸는 값. 현재 시각·난수·UUID·환경 변수.
- *Composition Root(조립 지점)*: 객체 그래프를 조립하는 단 한 곳. Seemann 정의: "모듈을 함께 조립하는, (가급적) 유일한 위치" — 애플리케이션 진입점에 가깝게 둔다.

쉬운 예: 콘센트다. 전기 제품은 발전소를 직접 짓지 않고 플러그만 가진다. 어느 전기를 꽂을지는 벽(바깥)이 정한다.\
똑같은 구조다.\
실무 예: 결제 서비스가 `new TossClient()`를 직접 하면 PG를 바꿀 때 서비스 코드를 고쳐야 하고, 테스트마다 진짜 PG를 부른다. 생성자로 `PaymentGateway`를 받으면 조립 지점 한 줄만 바뀐다.

"테스트하기 어렵다"는 대개 **설계 신호**다. 테스트가 시계를 못 바꾼다면, 코드가 시계를 숨기고 있다.

## 동작·원리

### 1. 세 역할 — 사용, 조립, 수명

```text
 진입점 main() / Spring 컨테이너 기동
 ┌───────────────── Composition Root ─────────────────┐
 │ clock   = Clock.systemDefaultZone()                 │  ← 숨은 입력도 여기서 만든다
 │ repo    = new JdbcOrderRepo(dataSource)             │
 │ gateway = new TossGateway(httpClient)               │
 │ service = new OrderService(repo, gateway, clock)    │  ← new는 이 상자 안에만
 └─────────────────────────────────────────────────────┘
          │ 완성된 객체를 넘긴다
          v
 애플리케이션 코드: 생성자로 받은 것만 쓴다. 컨테이너를 모른다.
```

- 사용하는 코드는 **받기만** 한다. 만드는 코드는 조립 지점에 모인다(Fowler 2004 결론: "설정을 사용에서 분리하는 원칙"이 Service Locator와 DI 중 무엇을 고르느냐보다 중요하다).
- 시계는 `Clock.systemDefaultZone()`으로 만든다. `LocalDate.now()`가 쓰던 시계와 같다(JDK 21 javadoc: `now(Clock.systemDefaultZone())`와 같음). `Clock.systemUTC()`로 바꾸면 날짜 기준이 UTC가 된다. KST 서버라면 00:00~08:59에는 날짜가 전날로 나온다.
- Spring에서는 컨테이너가 조립 지점 역할을 한다. `@Configuration`·컴포넌트 스캔이 "무엇을 무엇에 꽂을지"의 선언이다.
- 조립 지점 밖의 `new`가 다 나쁜 것은 아니다. 값 객체(`Money`)·DTO처럼 바꿔 끼울 일이 없는 것은 그냥 만든다. 주입 대상은 Seemann–van Deursen이 *변동 의존(Volatile Dependency)* 이라 부르는 것이다 — 바뀔 수 있거나, 환경에 묶이거나(DB·네트워크·시계), 비결정적인 것. 용어는 5장 목차("Making a Volatile Dependency globally available")에서 확인했고, 세부 판정 기준은 책 본문을 열지 못했다 [?].

### 2. 주입의 세 형태

| 형태 | 모양 | 쓰는 자리 (Seemann–van Deursen 4장) |
|---|---|---|
| 생성자 주입 | `Service(Repo r)` | 기본. 필수 의존을 시그니처에 정적으로 선언 |
| 메서드 주입 | `apply(Order o, Clock c)` | 조립 지점 밖으로 의존을 넘길 때(4장 서두: "Passing Dependencies outside the Composition Root", 4.3.4 예제는 엔티티) |
| 프로퍼티(세터) 주입 | `setLogger(..)` | 선택적 의존(4장 서두: "Declaring optional Dependencies") |

- Spring Framework 문서: Spring 팀은 생성자 주입을 권한다. 불변 객체로 만들 수 있고, 필수 의존이 null이 아님을 보장하고, 완전히 초기화된 상태로 돌려준다.

### 3. 생성 순서 = 의존 그래프의 위상 정렬

```text
 등록 순서:  A, B, C
 의존:       A ──> B ──> C
 생성 순서:  C, B, A      (받는 쪽보다 주는 쪽이 먼저)
```

- *위상 정렬(topological sort)*: 방향 그래프의 노드를 "화살표가 가리키는 쪽이 먼저" 오게 줄 세우는 것. 순환이 있으면 줄을 세울 수 없다.

### 실험 A: Spring 컨테이너의 생성 순서와 순환

(실험, Spring Framework 6.2.11, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/25/e25/src/Di.java`, 2026-10-02)

```java
static class A { A(B b) { System.out.println("  생성 A (B 받음)"); } }
static class B { B(C c) { System.out.println("  생성 B (C 받음)"); } }
static class C { C()    { System.out.println("  생성 C"); } }
ctx.register(A.class, B.class, C.class); ctx.refresh();

static class X { X(Y y) {} }   // 생성자 순환
static class Y { Y(X x) {} }
```

```text
[1] A→B→C 를 A,B,C 순서로 등록
  생성 C
  생성 B (C 받음)
  생성 A (B 받음)

[3] 생성자 순환 X(Y), Y(X)
  예외: UnsatisfiedDependencyException
    ...
    org.springframework.beans.factory.BeanCurrentlyInCreationException: Error creating bean with name 'di.X': Requested bean is currently in creation: Is there an unresolvable circular reference or an asynchronous initialization dependency?
```

- 등록은 A부터 했는데 생성은 C부터다. 컨테이너가 A를 만들려다 B가 필요해 B를 먼저, B는 C를 먼저 만든다(깊이 우선으로 따라가 위상 순서가 나온다).
- 생성자 순환은 **기동 시점에** 실패한다. 바깥 예외는 `UnsatisfiedDependencyException`이고 원인 사슬 끝에 `BeanCurrentlyInCreationException`이 있다. 문서도 이 예외를 적는다(「Circular dependencies」).
- Spring Boot 2.6부터 빈 순환 참조는 기본 금지다(2.6 릴리스 노트 「Circular References Prohibited by Default」). 세터·필드 주입 순환도 Boot에서는 기동이 막힌다.

### 4. 객체 수명(lifestyle)과 Captive Dependency

```text
 수명     Spring 대응           하나가 사는 기간
 Singleton  singleton(기본)     컨테이너 전체
 Scoped     request·session…    요청 하나(범위 하나)
 Transient  prototype           꺼낼 때마다 새로

 규칙: 오래 사는 것이 짧게 사는 것을 '붙잡으면' 안 된다
 Singleton ──붙잡음──> Scoped        → 그 Scoped 객체가 사실상 Singleton이 된다 (Captive Dependency)
```

- *Captive Dependency*: Seemann 정의 — "수명이 잘못 설정된 의존". 오래 사는 소비자가 짧게 살아야 할 의존을 필드로 붙잡아, 그 의존도 소비자만큼 산다. 이 효과는 전이된다(붙잡힌 것이 붙잡은 것도 함께 오래 산다).
- 책 『Dependency Injection Principles, Practices, and Patterns』(Seemann–van Deursen, Manning 2019) 8.4.1절이 "Bad Lifestyle choices"의 첫 항목으로 다룬다(livebook 목차 확인).

### 실험 B: 싱글턴이 요청 범위 객체를 붙잡으면

설정: Spring의 `SimpleThreadScope`를 `thread` 범위로 등록해 **스레드 하나 = 요청 하나**로 흉내 냈다(웹 컨테이너 없이 request 범위를 재현하려는 대역이다).

```java
@Bean @Scope("thread") RequestCtx requestCtx() { return new RequestCtx(); }     // 요청마다 하나
@Bean CaptiveService captive(RequestCtx c) { return new CaptiveService(c); }    // 싱글턴이 필드로 붙잡음
@Bean ProviderService provider(ObjectProvider<RequestCtx> p) { ... }            // 호출마다 p.getObject()
// 고친 판 2: @Scope(value = "thread", proxyMode = ScopedProxyMode.TARGET_CLASS)
```

(실험, 같은 환경, 2026-10-02 — `ctx#`는 생성 순번)

```text
[2] 싱글턴에 thread 범위 빈 주입 — 스레드 두 개 = 요청 두 개
  요청 alice: captive → ctx#1 user=alice | provider → ctx#2 user=alice
  요청 bob: captive → ctx#1 user=alice | provider → ctx#3 user=bob

[2b] 같은 주입을 범위 프록시로
  요청 alice: proxy → ctx#4 user=alice (주입된 클래스=Di$RequestCtx$$SpringCGLIB$$0)
  요청 bob: proxy → ctx#5 user=bob (주입된 클래스=Di$RequestCtx$$SpringCGLIB$$0)
```

- 붙잡은 판: bob의 요청에서 **alice의 컨텍스트(ctx#1)** 가 보였다. 요청 간 상태 누출이다. 에러는 없다.
- `ObjectProvider` 판: 요청마다 새 객체(ctx#2, ctx#3).
- 범위 프록시 판: 싱글턴은 CGLIB 프록시를 하나 붙잡고, 프록시가 호출마다 현재 범위의 진짜 객체(ctx#4, ctx#5)에 위임한다. Spring 문서 「Scoped Beans as Dependencies」가 이 두 방법(범위 프록시, `ObjectProvider`/JSR-330 `Provider`)을 적는다.

```text
 싱글턴 ──> [프록시] ──호출마다──> 현재 요청의 RequestCtx
              └ 클래스 = RequestCtx$$SpringCGLIB$$0 (서브클래스 프록시)
```

### 5. 안티패턴 — 의존을 숨기는 네 방식

Seemann–van Deursen 5장 「DI anti-patterns」(livebook 목차): 5.1 Control Freak · 5.2 Service Locator · 5.3 Ambient Context · 5.4 Constrained Construction.

```text
 Control Freak        class S { Repo r = new JdbcRepo(); }           구체를 직접 new
 Service Locator      Clock c = ctx.getBean(Clock.class);            필요할 때 전역 저장소에서 꺼냄
 Ambient Context      TimeProvider.current().now()                   전역 정적 접근점에 변동 의존을 둠
 정적 호출            LocalDate.now(), UUID.randomUUID()             숨은 입력을 전역에서 직접 가져옴 (해석: Ambient Context·Control Freak과 겹침)
 Constrained Constr.  "플러그인은 기본 생성자를 가져야 한다"          생성자 시그니처를 강제
```

- 책 5.3.1절 제목이 "Accessing time through Ambient Context"다(목차 확인). 시간 접근이 이 안티패턴의 대표 예라는 뜻이다. `LocalDate.now()` 같은 정적 호출을 책이 어느 항목으로 분류하는지는 본문을 열지 못해 확인하지 못했다 [?].
- Service Locator의 문제(Seemann 2010): 클래스의 의존을 숨겨 **컴파일 시점 오류 대신 실행 시점 오류**를 낳는다. 새 의존을 하나 더 꺼내도 시그니처가 안 바뀌어서, 그것이 깨지는 변경인지 알기 어렵다.
- 참고: Fowler(2004)는 Service Locator를 DI의 대안으로 소개했고 "둘 중 무엇이냐보다 설정과 사용의 분리가 중요하다"고 썼다. Seemann(2010)은 이를 안티패턴이라고 반박했다. 저자마다 평가가 다르다.

### 실험 C: 빈이 없을 때 — 생성자 주입 vs Service Locator

```java
static class CtorBilling    { CtorBilling(Clock clock) { ... } }
static class LocatorBilling { String bill() { Clock clock = ctx.getBean(Clock.class); ... } }
```

(실험, 같은 환경, 두 경우 모두 `Clock` 빈을 등록하지 않음, 2026-10-02)

```text
[4a] 생성자 주입 — Clock 빈 없음
  예외: UnsatisfiedDependencyException
    org.springframework.beans.factory.UnsatisfiedDependencyException: Error creating bean with name 'di.CtorBilling': Unsatisfied dependency expressed through constructor parameter 0: No qualifying bean of type 'java.time.Clock' available: expected at least 1 bean which qualifies as autowire candida...

[4b] Service Locator — Clock 빈 없음
  기동 성공 (문제 없어 보인다)
  예외: NoSuchBeanDefinitionException
    org.springframework.beans.factory.NoSuchBeanDefinitionException: No qualifying bean of type 'java.time.Clock' available
```

- 생성자 주입은 **기동 때** 실패했다. 배포 직후 헬스 체크에서 잡힌다.
- Service Locator는 기동에 성공했고 **첫 호출 때** 실패했다. 그 경로가 월말 정산 배치라면 월말에 터진다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프(방향 그래프)** — 노드 = 컴포넌트, 간선 = "생성자에 받는다". 컨테이너는 빈 정의에서 이 그래프를 만든다.
- **위상 정렬** — 생성 순서. 깊이 우선 탐색으로 의존을 먼저 만들고 돌아온다(실험 A: 등록 A,B,C → 생성 C,B,A). DFS·위상 정렬은 [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md).
- **순환 탐지** — 깊이 우선 탐색 중 "만드는 중" 표시가 된 노드를 다시 만나면 순환이다. Spring 6.2.11 `DefaultSingletonBeanRegistry`는 생성 중인 빈 이름 집합(`singletonsCurrentlyInCreation`, `javap`로 필드 확인)을 두고, 같은 이름이 다시 요청되면 `BeanCurrentlyInCreationException`을 던진다(실험 A 메시지 "Requested bean is currently in creation"). 순환 묶음 찾기는 [algorithm/18-scc](../../algorithm/18-scc/2-summary.md), 그래프 표현은 [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **레지스트리(타입 → 정의 맵)** — 컨테이너 내부의 빈 정의 저장소. Service Locator는 이 맵을 애플리케이션 코드에 노출한 것이다.
- **프록시(대리 객체, 인터셉터)** — 범위 프록시는 호출을 가로채 현재 범위의 대상으로 위임한다(실험 B의 `$$SpringCGLIB$$0`). 프록시 일반과 자기 호출 함정은 33 aop-and-proxies.

## 적용 — 풀어나가는 법

### 1. 순서

1. **변동 의존을 찾는다**: DB·네트워크·파일·시계·난수·UUID·환경 변수. 값 객체·순수 계산은 주입하지 않는다.
2. **생성자 인자로 올린다**: 필드 `new`·정적 호출·`getBean()`을 생성자 파라미터로 바꾼다. 시계는 `java.time.Clock`, 난수는 `RandomGenerator`, ID는 작은 인터페이스(`IdGenerator`)로.
3. **조립은 한 곳**: Spring이면 `@Configuration`/컴포넌트 스캔. 순수 Java면 `main`의 조립 메서드(Seemann의 "Pure DI").
4. **수명을 맞춘다**: 싱글턴이 짧은 수명의 것을 받아야 하면 `ObjectProvider`·범위 프록시, 또는 **메서드 인자로 넘긴다**.
5. **기동 시점에 깨지게 둔다**: 생성자 주입이면 빠진 빈이 기동 실패로 드러난다(실험 C). 통합 테스트 하나가 컨텍스트를 띄우기만 해도 조립 오류를 잡는다.
6. **생성자 인자가 많아지면 주입 문제가 아니라 책임 문제다**: Seemann–van Deursen 6.1 "Constructor Over-injection" — Facade 서비스로 묶거나 도메인 이벤트로 나눈다.

### 2. 숨은 입력 주입 — 시계

(실험 D, JDK 21 temurin, Mockito 5.20.0, `scratchpad/sd/25/e25/src/HiddenInput.java`, 2026-10-02 실행)

```java
// 버그: 청구일이 31일인 고객은 30일까지인 달에 청구되지 않는다
class StaticBilling { boolean isBillingDay(int day) { return LocalDate.now().getDayOfMonth() == day; } }
class ClockBilling  { final Clock clock; ...         return LocalDate.now(clock).getDayOfMonth() == day; }
class FixedBilling  { ... LocalDate d = LocalDate.now(clock);
                      return d.getDayOfMonth() == Math.min(day, d.lengthOfMonth()); }   // 없으면 말일
```

```text
오늘(시스템 시계) = 2026-10-02
StaticBilling.isBillingDay(오늘 일자) = true  ← 오늘 돌린 테스트는 초록
2026년 365일을 Clock.fixed로 훑음 — 청구일 31일 고객의 청구 횟수: 주입판(버그)=7회, 고친 판=12회
2026-04-30 고정: 버그판=false 고친 판=true
```

- 정적 호출 판은 **오늘** 돌린 테스트만 초록이다. 버그는 30일까지인 달의 말일에만 보인다.
- 시계를 주입하자 1년 365일을 밀리초 안에 훑을 수 있었다. 버그 판은 1년에 7번(31일이 있는 달), 고친 판은 12번 청구했다.
- 정적 호출을 그대로 두고 시험하는 길도 있다. Mockito `mockStatic(LocalDate.class)`는 이 실행에서 동작했다(2026-04-30 흉내 → `false`). 대가는 두 가지였다.
  - 실행 시 에이전트 자가 부착 경고가 찍혔다: `Mockito is currently self-attaching to enable the inline-mock-maker. This will no longer work in future releases of the JDK.`
  - 첫 시도에서 `thenReturn(LocalDate.of(2026, 4, 30))`처럼 **가로챈 클래스의 메서드를 스터빙 중에 부르자** `UnfinishedStubbingException`이 났다. 값을 블록 밖에서 미리 만들어야 했다.

### 3. 진단 — 숨은 의존 찾기

```bash
# 조립 지점 밖의 숨은 입력·Service Locator 호출 (예시 패턴)
grep -rnE 'LocalDate(Time)?\.now\(\)|Instant\.now\(\)|UUID\.randomUUID\(\)|new Random\(|getBean\(' src/main/java \
  | grep -v '/config/'
# 테스트 쪽 정적 모킹 개수 — 숨은 입력의 대리 지표
grep -rc 'mockStatic(' src/test/java | awk -F: '$2>0'
```

- `mockStatic`·`@MockBean`이 테스트마다 수북하면, 프로덕션 코드가 변동 의존을 숨기고 있다는 신호다.
- Spring 설정 점검: 싱글턴 빈의 생성자 인자에 request·session·prototype 범위 빈이 프록시 없이 들어가는지 본다.

## 장애 시나리오와 대처

### 1. 싱글턴에 요청 범위 객체 주입 → 요청 간 상태 누출 (⚠ 커리큘럼)

- 현상: 사용자 B의 화면에 사용자 A의 정보(테넌트·로케일·사용자 ID)가 보인다. 에러는 없다.
- 보이는 형태: 로그의 요청 ID와 처리 중인 컨텍스트 ID가 어긋난다. 실험 B처럼 두 번째 요청에서 첫 요청의 `ctx#1`이 나온다.
- 원인: 오래 사는 빈이 짧게 살아야 할 빈을 필드로 붙잡았다(Captive Dependency). 붙잡힌 객체는 붙잡은 빈의 수명을 따른다.
- 대처: 범위 프록시(`proxyMode = TARGET_CLASS`)나 `ObjectProvider`로 호출마다 꺼낸다. 더 단순하게는 요청 데이터를 **메서드 인자**로 넘긴다. 컨테이너가 수명 불일치를 검증해 주는지 확인한다(Seemann 글의 댓글: Simple Injector는 "lifestyle mismatch" 진단을 내장).

### 2. Service Locator·`getBean()` → 설정 누락이 운영 중 첫 호출에야 터진다 (⚠ 커리큘럼)

- 현상: 배포·헬스 체크는 통과했는데 특정 기능(정산·환불)을 처음 쓸 때 500.
- 보이는 형태: `NoSuchBeanDefinitionException: No qualifying bean of type '…' available`이 요청 처리 스택에서 나온다(실험 C의 4b).
- 원인: 의존이 시그니처에 없어 컨테이너가 기동 때 검사하지 못했다. 테스트도 그 빈을 등록할 필요를 몰랐다.
- 대처: 생성자 주입으로 바꿔 기동 시점 실패로 당긴다(4a). 조립 오류를 잡는 컨텍스트 로드 테스트를 하나 둔다.

### 3. 순환 주입 → 기동 실패 (⚠ 커리큘럼)

- 현상: 클래스 하나에 의존을 추가한 뒤 애플리케이션이 뜨지 않는다.
- 보이는 형태: `UnsatisfiedDependencyException` … `BeanCurrentlyInCreationException: … Requested bean is currently in creation: Is there an unresolvable circular reference …`(실험 A).
- 원인: A→B→A 순환. 대개 한 클래스가 두 책임을 가져 양쪽이 서로의 일부를 필요로 한다(Seemann–van Deursen 6.3.1 "Dependency cycle caused by an SRP violation").
- 대처: 공통 부분을 세 번째 클래스로 추출하거나, 한 방향을 이벤트로 바꾼다. 책 6.3.5절 제목은 "Last resort: Breaking the cycle with Property Injection"이다 — 세터(프로퍼티) 주입으로 순환을 끊는 것을 최후 수단이라 부른다. `@Lazy`·`spring.main.allow-circular-references=true`로 순환을 **허용**하는 것도 같은 부류로 본다(해석 — 책은 Spring 설정을 다루지 않는다).
  - 두 수단의 적용 범위는 다르다. 순환 허용 스위치는 세터·필드 주입 순환만 띄운다. 생성자 순환(실험 A의 X(Y), Y(X))은 스위치를 켜도 실패한다(문서 「Circular dependencies」: 생성자 순환은 "unresolvable"). `@Lazy`는 생성자 매개변수에 붙이면 지연 프록시를 주입해 생성자 순환도 띄운다(실험 E).

(실험 E, Spring Framework 6.2.11, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/adj-55/Cyc.java`, 2026-10-02 — Boot 없이 빈 팩토리의 `setAllowCircularReferences`를 직접 켜고 껐다. Boot 3.5.6은 `SpringApplication.prepareContext`에서 `spring.main.allow-circular-references` 값을 이 설정에 넣는다(소스). 경고 로그 제외)

```text
[1] 생성자 순환 X(Y),Y(X)         allowCircularReferences=false → 실패: BeanCurrentlyInCreationException
[2] 생성자 순환 X(Y),Y(X)         allowCircularReferences=true → 실패: BeanCurrentlyInCreationException
[3] 필드 주입 순환 P↔Q            allowCircularReferences=false → 실패: BeanCurrentlyInCreationException
[4] 필드 주입 순환 P↔Q            allowCircularReferences=true → 기동 성공
[5] 생성자 순환 + @Lazy LX(@Lazy LY) allowCircularReferences=false → 기동 성공 LX→LY
```

### 4. 서비스 단위 테스트에 DB·Redis·외부 API가 다 필요하고 `mockStatic` 도배 (⚠ 커리큘럼)

- 현상: 할인 규칙 하나를 시험하려고 Testcontainers를 띄우거나 정적 모킹을 다섯 개 건다. 테스트가 느리고 자주 깨진다.
- 보이는 형태: 테스트 파일마다 `@SpringBootTest`·`@MockBean`·`mockStatic` 다수. 테스트 시간 증가, 자기 부착 에이전트 경고(실험 D).
- 원인: 변동 의존을 `new`·정적 호출로 숨겼다(Control Freak·Ambient Context).
- 대처: 생성자 주입으로 바꾸고, 계산 부분을 I/O에서 떼어 순수 함수로 만든다 — 다음 단계는 26 functional-core-imperative-shell.

### 5. `LocalDate.now()` 직접 호출로 월말에만 실패 (⚠ 커리큘럼)

- 현상: 매달 말일(또는 2월 말·윤년)에만 청구·만료 처리가 빠진다. 평소 CI는 초록이다.
- 보이는 형태: 특정 날짜에만 "처리 0건". 실험 D에서 청구일 31일 고객이 1년 12번 중 7번만 청구됐다.
- 원인: 시간이 숨은 입력이라 테스트가 날짜를 고를 수 없었다.
- 대처: `Clock`을 주입하고(`Clock.systemDefaultZone()`은 조립 지점에서), 테스트에서 `Clock.fixed`로 경계 날짜(말일·윤일·DST 전환일)를 훑는다.

(자기 호출로 프록시가 우회되는 문제는 33 aop-and-proxies에서 다룬다.)

## 핵심 문장

- 의존성 주입은 "만들기"를 사용 코드에서 빼내 조립 지점 한 곳으로 모으는 것이다.
- 시계·난수·UUID 같은 숨은 입력도 의존이다. 주입하면 실험처럼 1년치 날짜를 테스트로 훑을 수 있다.
- 생성자 주입은 빠진 의존을 기동 시점에 드러내고, Service Locator는 첫 호출 때 드러낸다(실험 C).
- 오래 사는 객체가 짧게 사는 객체를 붙잡으면 Captive Dependency다. Spring 실험에서 두 번째 요청이 첫 요청의 컨텍스트를 봤다.
- 컨테이너의 생성 순서는 의존 그래프의 위상 정렬이고, 생성자 순환은 기동 때 `BeanCurrentlyInCreationException`으로 막힌다.
- 테스트하기 어려움은 설계 신호다. 정적 모킹이 늘어나면 숨은 의존을 찾는다.

## 관련 주제·근거

- 선행
  - [22-solid](../22-solid/2-summary.md) · 원본 [engineering/solid-principles](../../engineering/solid-principles/2-summary.md) 「DIP vs DI(의존성 주입)」: DIP는 소스 의존 방향, DI는 객체를 받는 방식. DI를 써도 DIP를 어길 수 있다.
  - testing/03-test-doubles — 미작성([testing README](../../testing/README.md))
- 후속·연결
  - [26-functional-core-imperative-shell](../26-functional-core-imperative-shell/2-summary.md) — 주입 대신 의존을 아예 바깥으로 밀어내기
  - [33-aop-and-proxies](../33-aop-and-proxies/2-summary.md)(프록시·자기 호출), [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md)(Separated Interface·Plugin·ServiceLoader)
  - [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) 「Spring이 대신 해주는 것」 — Singleton·Factory를 컨테이너가 흡수
  - testing/10-testing-time-and-concurrency — 미작성([testing README](../../testing/README.md))
- 글·문서
  - Mark Seemann, Steven van Deursen, 『Dependency Injection Principles, Practices, and Patterns』(Manning, 2019) — 4장 DI patterns(4.1 Composition Root, 4.2 Constructor Injection, 4.3 Method Injection), 5장 DI anti-patterns(5.1~5.4), 6장 Code smells(6.1 Constructor Over-injection, 6.3 cyclic Dependencies), 8장 Object lifetime(8.3 Lifestyle catalog, 8.4.1 Captive Dependencies) — livebook 목차로 절 구성 확인 <https://livebook.manning.com/book/dependency-injection-principles-practices-patterns/chapter-5>
  - Martin Fowler, "Inversion of Control Containers and the Dependency Injection pattern", 2004-01-23 <https://martinfowler.com/articles/injection.html>
  - Mark Seemann, "Composition Root"(2011) <https://blog.ploeh.dk/2011/07/28/CompositionRoot/> · "Service Locator is an Anti-Pattern"(2010) <https://blog.ploeh.dk/2010/02/03/ServiceLocatorisanAnti-Pattern/> · "Captive Dependency"(2014) <https://blog.ploeh.dk/2014/06/02/captive-dependency/>
  - Spring Framework 문서 「Dependency Injection」(생성자 주입 권장, Circular dependencies) <https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html> · 「Bean Scopes」의 「Scoped Beans as Dependencies」 <https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html>
  - Spring Boot 2.6 Release Notes 「Circular References Prohibited by Default」 <https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.6-Release-Notes>
- 실험 목록 (코드: scratchpad `sd/25/e25/src/`, 의존 jar는 Maven Central에서 받아 `sd/25/libs/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`)
  - A `Di.java` [1]·[3] — 생성 순서(위상 정렬), 생성자 순환 예외 (Spring 6.2.11)
  - B `Di.java` [2]·[2b] — Captive Dependency 재현, `ObjectProvider`·범위 프록시로 고침
  - C `Di.java` [4a]·[4b] — 빠진 빈: 생성자 주입은 기동 실패, Service Locator는 첫 호출 실패
  - D `HiddenInput.java` — `LocalDate.now()` 숨은 입력, `Clock.fixed`로 2026년 365일 훑기, Mockito 5.20.0 `mockStatic` 대안
  - E `sd/adj-55/Cyc.java` — 순환 허용 스위치(`setAllowCircularReferences`, Boot 속성이 켜는 것과 같은 빈 팩토리 설정) 켬/끔 × 생성자 순환·필드 주입 순환, 생성자 순환 + `@Lazy` (Spring 6.2.11). 출력: 생성자 순환은 켬·끔 모두 `BeanCurrentlyInCreationException`, 필드 순환은 끔 실패·켬 성공, `@Lazy`는 끔에서도 성공
