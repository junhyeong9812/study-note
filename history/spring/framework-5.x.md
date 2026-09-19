# Spring Framework 5.x (2017 ~)

> 원본: `~/project/java-history/spring/framework-5.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/어노테이션 이름·코드블록 8개(Java 4 · Kotlin 4)·「릴리스 정보」와 「마이너 버전별 변화」의 목록·`route()` 참고 인용구는 원문 그대로다.\
> ASCII 도식 3개(모두 원문 mermaid 그림을 글자로 옮긴 것이다), 「한눈에」의 식당 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 리액티브 프로그래밍(WebFlux/Reactor)과 **Kotlin 1급 지원**이라는 두 축을 동시에 도입한 세대. 명령형 일변도였던 Spring에 비동기·논블로킹과 함수형 스타일이 정식으로 들어왔다.

이 편의 첫째 축을 하나의 비유로 읽으면 **홀에서 손님을 받는 방식의 차이**다.\
한 팀마다 직원 한 명이 주방 앞에 서서 음식이 나올 때까지 기다리는 가게가 있고, 직원 몇이 주문만 주방에 걸어 두고 다른 테이블을 계속 도는 가게가 있다.\
**MVC와 WebFlux의 차이도 똑같은 구조다** — 원문 자신이 두 그림 앞에서 "MVC는 요청 하나가 스레드 하나를 결과가 나올 때까지 점유하고, WebFlux는 적은 수의 이벤트 루프 스레드가 Reactor 파이프라인으로 여러 요청을 논블로킹 처리한다"고 적는다.

본문 흐름에 쓰는 비유는 이 식당 하나뿐이고, 그것이 덮는 것은 첫째 축(WebFlux)이다.\
둘째 축인 Kotlin 절은 비유 없이 원문 문장과 코드로만 읽는다.

| 비유 | 실체 |
|---|---|
| 한 팀마다 직원 한 명이 주방 앞에 서서 기다리는 것 | Spring MVC — 원문 그림의 "스레드풀: 요청당 스레드 1개 점유"와 "DB/IO 호출 동안 스레드 블록 (대기)" |
| 직원 몇이 주문만 걸어 두고 다른 테이블을 도는 것 | Spring WebFlux — 원문 그림의 "Netty/Undertow 이벤트 루프 (소수 스레드)"와 "논블로킹 IO 등록 후 스레드 즉시 반환" |
| 음식이 준비되면 울리는 벨 | 원문 그림의 "데이터 준비되면 콜백/구독으로 재개" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **WebFlux가 MVC를 대체한 것이 아니다.**\
  원문은 WebFlux를 두고 "`spring-webmvc`와 공존하며 같은 어노테이션 모델도 쓸 수 있다"고 적고, 「영향과 의의」에서도 "단, 명령형 MVC가 사라진 것은 아니며 둘은 공존"이라고 못 박는다.
- **원문이 리액티브의 이점으로 든 말은 "빠르다"가 아니다.**\
  원문이 「시대적 배경」에서 배경 수요로 적은 것은 "**적은 스레드로 높은 동시성**을 처리하려는 수요가 커졌고"이고, 두 그림의 차이로 적은 것도 스레드를 점유하느냐 즉시 반환하느냐다.
- **Kotlin 지원은 "Kotlin에서도 돌아간다"가 아니다.**\
  원문 표현으로 "단순히 "Kotlin에서 호출 가능"한 수준이 아니라, **Kotlin 언어 기능에 맞춰 API와 DSL을 설계**했다".

## 릴리스 정보
- 최초 출시: 5.0 — 2017년 9월
- 주요 마이너 버전과 시기: 5.0(2017-09) → 5.1(2018-09) → 5.2(2019-09/10) → 5.3(2020-10, 장기 지원)
- 최소 자바 버전(baseline): Java 8 이상. 5.1에서 **Java 11** 정식 지원. 5.3.0 GA(2020-10)는 JDK 8-15 대응으로 출시됐고, **JDK 17 실행 지원은 이후 5.3.x 유지보수 라인에서 추가**됐다(5.3.x는 JDK 21에서도 실행 가능하나, 프레임워크 차원의 가상 스레드 지원은 6.1부터다).
- Java EE / Jakarta EE 기준: Java EE 7 베이스라인(Servlet 3.1, JPA 2.1, Bean Validation 1.1), Java EE 8 호환. **여전히 `javax.*` 네임스페이스 사용**(jakarta 전환은 6.0).

## 시대적 배경

2017년경 백엔드 화두는 **리액티브/논블로킹**이었다.\
Node.js의 이벤트 루프 모델, RxJava의 확산, 그리고 Reactive Streams 표준(JDK 9의 `java.util.concurrent.Flow`로 편입) 등이 배경이다.\
적은 스레드로 높은 동시성을 처리하려는 수요가 커졌고, Spring은 기존 서블릿 기반 `spring-webmvc`와 별개로 **논블로킹 웹 스택 `spring-webflux`**를 새로 만들었다.

> **블로킹 / 논블로킹(blocking / non-blocking)** — 결과가 나올 때까지 그 스레드를 그 자리에 붙들어 두는 방식 / 붙들지 않고 스레드를 돌려주는 방식.\
> 예: 원문 그림에서 MVC 쪽에 적힌 "DB/IO 호출 동안 스레드 블록 (대기)"가 앞쪽이고, WebFlux 쪽에 적힌 "논블로킹 IO 등록 후 스레드 즉시 반환"이 뒤쪽이다.

> **이벤트 루프(event loop)** — 준비된 이벤트를 차례로 꺼내 처리하는 소수의 스레드. 원문은 이것을 Node.js의 모델로 배경에 든다.\
> 예: 원문 그림에서 WebFlux의 둘째 칸이 "Netty/Undertow 이벤트 루프 (소수 스레드)"다.

또 하나의 큰 흐름은 **Kotlin**이다.\
2017년 Google이 Android 공식 언어로 Kotlin을 채택하며 JVM 진영에서 폭발적으로 성장했다.\
Spring 5는 Kotlin을 단순 호환이 아니라 **1급 시민(first-class)**으로 지원하기로 결정했다 — 널 안정성, 확장 함수, 함수형 빈/라우터 DSL까지.\
코드베이스 baseline도 Java 8로 올려 람다·`CompletableFuture`를 적극 활용했고, 테스트는 JUnit 5(Jupiter)를 지원했다.

> **1급 시민(first-class)** — 곁다리로 얹어 주는 대상이 아니라, 설계할 때부터 본래 대상과 같은 대접을 받는 것.\
> 예: 원문이 이 말을 풀어 적은 것이 "단순히 "Kotlin에서 호출 가능"한 수준이 아니라, Kotlin 언어 기능에 맞춰 API와 DSL을 설계했다"이다.

## 핵심 추가/변경 기능

### Spring WebFlux — 리액티브 웹 스택

*(「한눈에」의 두 가게가 갈리는 자리다.)*

서블릿 블로킹 모델에 의존하지 않는 완전 논블로킹 웹 프레임워크.\
**Reactor**(`Mono`/`Flux`)를 기본 리액티브 라이브러리로 사용하고, Netty/Undertow 같은 논블로킹 런타임 위에서 동작한다.\
`spring-webmvc`와 공존하며 같은 어노테이션 모델도 쓸 수 있다.

> **Reactor / `Mono` / `Flux`** — Spring이 기본으로 쓰는 리액티브 라이브러리 / 그 안에서 결과가 많아야 하나(0..1)인 타입 / 결과가 여럿(0..N)일 수 있는 타입.\
> 예: 원문이 마지막 그림에서 각각에 붙인 설명이 "`Mono<T>` (0..1)"과 "`Flux<T>` (0..N)"이다.

명령형(MVC) vs 리액티브(WebFlux) 비교:

```java
// 기존 Spring MVC — 블로킹, 반환은 구체 타입
@GetMapping("/{id}")
public Account get(@PathVariable long id) {
    return accountService.find(id);     // 스레드가 결과까지 블록
}
```

```java
// Spring WebFlux — 논블로킹, 반환은 Mono/Flux (어노테이션 모델)
@GetMapping("/{id}")
public Mono<Account> get(@PathVariable long id) {
    return accountService.find(id);     // 구독 시점에 비동기 실행
}

@GetMapping("/stream")
public Flux<Account> stream() {
    return accountService.findAll();    // 0..N 스트리밍
}
```

두 블록의 `@GetMapping`과 메서드 이름은 같고, 달라진 자리는 반환 타입이다 — 위는 `Account`, 아래는 `Mono<Account>`다.\
원문이 두 블록 주석에 붙여 둔 대비도 그것이다: "반환은 구체 타입" / "반환은 Mono/Flux (어노테이션 모델)".

> **구독(subscribe)** — 리액티브 타입에 담긴 일이 실제로 굴러가기 시작하는 시점.\
> 예: 원문이 위 코드 둘째 블록에 단 주석이 "구독 시점에 비동기 실행"이다 — 메서드가 `Mono`를 반환한 그 순간이 아니다.

아래 두 다이어그램은 MVC(블로킹)와 WebFlux(논블로킹)의 요청 처리 방식 차이를 보여준다.\
MVC는 요청 하나가 스레드 하나를 결과가 나올 때까지 점유하고, WebFlux는 적은 수의 이벤트 루프 스레드가 Reactor 파이프라인으로 여러 요청을 논블로킹 처리한다.

```text
Spring MVC (블로킹)

요청 N개
   ↓
서블릿 컨테이너 (Tomcat)
   ↓
스레드풀: 요청당 스레드 1개 점유
   ↓
@Controller 메서드 실행
   ↓
DB/IO 호출 동안 스레드 블록 (대기)
   ↓
결과 반환 후 스레드 반납
```

```text
Spring WebFlux (논블로킹)

요청 N개
   ↓
Netty/Undertow 이벤트 루프 (소수 스레드)
   ↓
핸들러가 Mono/Flux 파이프라인 구성
   ↓
논블로킹 IO 등록 후 스레드 즉시 반환
   ↓
데이터 준비되면 콜백/구독으로 재개
   ↓
Reactor가 결과 방출 → 응답 스트리밍
```

- 두 그림은 원문의 첫째·둘째 mermaid 그림을 각각 글자로 옮긴 것이다 — 원문이 두 그림으로 따로 그린 것을 여기서도 둘로 두었다.
- 칸은 각각 여섯, 화살표는 각각 다섯으로 원문과 같고, 방향도 원문과 같이 위에서 아래다.
- 맨 윗줄은 원문이 그 그림을 감싼 subgraph에 붙인 제목이고, 칸 안의 글자도 원문 노드 문구 그대로다(WebFlux 쪽 마지막 칸의 `→`도 원문 노드 글자다).
- 두 그림을 나란히 읽는 법은 바로 위 문단에 있다 — 둘째 칸부터 갈린다: 왼쪽은 "서블릿 컨테이너 (Tomcat)" → "스레드풀: 요청당 스레드 1개 점유", 오른쪽은 "Netty/Undertow 이벤트 루프 (소수 스레드)"다.

### 함수형 웹 엔드포인트 (RouterFunction)

어노테이션 대신 함수(라우터 + 핸들러)로 라우팅을 구성하는 새 모델.

> **라우팅(routing) / 라우터(router)** — 들어온 요청을 어느 처리기가 맡을지 정하는 일 / 그 규칙을 담은 것.\
> 예: 아래 코드에서 `.GET("/accounts/{id}", handler::get)` 한 줄이 경로 하나와 핸들러 하나를 짝지은 규칙이다.

```java
@Bean
public RouterFunction<ServerResponse> routes(AccountHandler handler) {
    return route()
        .GET("/accounts/{id}", handler::get)
        .GET("/accounts",      handler::list)
        .POST("/accounts",     handler::create)
        .build();
}
```

**언제 쓸 수 있게 됐나** — 원문이 이 코드 아래에 인용 블록으로 달아 둔 그대로다.

> 참고: 위 `route()` 플루언트 빌더는 Spring Framework **5.1**에서 추가됐다. 5.0에서는 `RouterFunctions.route(GET("/accounts/{id}"), handler::get).andRoute(...)` 형태를 사용했다.

### WebClient — 리액티브 HTTP 클라이언트

블로킹 `RestTemplate`을 대체하는 논블로킹 클라이언트.

```java
WebClient client = WebClient.create("https://api.example.com");

Mono<Account> account = client.get()
    .uri("/accounts/{id}", 42)
    .retrieve()
    .bodyToMono(Account.class);
```

> **HTTP 클라이언트** — 내 서버가 남의 서버를 부를 때 쓰는 쪽. 원문은 `RestTemplate`을 "블로킹", `WebClient`를 "논블로킹"이라 갈라 적는다.\
> 예: 위 코드의 반환 타입이 `Mono<Account>`인 것이 그 차이가 드러난 자리다.

---

### Kotlin 1급 지원 — Spring 5의 또 다른 핵심

Spring 5는 Kotlin을 깊이 통합했다.\
단순히 "Kotlin에서 호출 가능"한 수준이 아니라, **Kotlin 언어 기능에 맞춰 API와 DSL을 설계**했다.

**1) 널 안정성(null-safety)** — Spring API에 JSR-305 기반 `@Nullable`/`@NonNull` 메타 어노테이션을 부착해, Kotlin 컴파일러가 Spring API의 널 가능 여부를 타입 시스템으로 인식한다.

> **널 안정성(null-safety)** — 값이 비어 있을 수 있는지를 타입으로 드러내, 비어 있는 값을 잘못 쓰는 일을 컴파일러가 잡게 하는 것.\
> 예: 원문이 든 수단이 "JSR-305 기반 `@Nullable`/`@NonNull` 메타 어노테이션"이고, 그것을 읽는 쪽이 Kotlin 컴파일러다.

**2) 확장 함수(extension functions)** — Kotlin에서 더 자연스러운 API 제공. 예: `getBean<T>()` 처럼 reified 제네릭을 활용.

```kotlin
// Java: ctx.getBean(AccountService::class.java)
val service = ctx.getBean<AccountService>()   // Kotlin reified 확장 함수
```

> **확장 함수(extension function)** — 남이 만든 타입에 내가 메서드를 덧붙여 쓰는 것처럼 보이게 하는 Kotlin 문법.\
> 예: 위 코드에서 `ctx.getBean<AccountService>()`가 그렇게 덧붙인 모양이고, 원문이 주석으로 나란히 적어 둔 Java 쪽 표기는 `ctx.getBean(AccountService::class.java)`다.

**3) 함수형 빈 정의 DSL(bean definition DSL)** — `@Configuration`/`@Bean` 없이 람다로 빈을 등록.

```kotlin
val beans = beans {
    bean<AccountServiceImpl>()
    bean<JdbcAccountDao>()
    bean {
        WebClient.create("https://api.example.com")
    }
}
```

**4) 라우터 DSL(router function DSL)** — WebFlux 라우팅을 Kotlin DSL로.

```kotlin
val routes = router {
    "/accounts".nest {
        GET("/{id}", handler::get)
        GET("", handler::list)
        POST("", handler::create)
    }
}
```

> **DSL(Domain-Specific Language, 도메인 특화 언어)** — 한 가지 일에만 쓰도록 좁게 만든 표기법.\
> 예: 위 두 코드블록의 `beans { … }`와 `router { … }`가 각각 빈 등록용·라우팅용 표기다.

**5) 코루틴 지원(5.2)** — 컨트롤러/핸들러를 `suspend` 함수로 작성하면 Spring이 내부적으로 Reactor와 연결한다.

```kotlin
@GetMapping("/{id}")
suspend fun get(@PathVariable id: Long): Account =
    accountService.find(id)          // suspend, 논블로킹

@GetMapping("/stream")
fun stream(): Flow<Account> =        // Kotlin Flow (5.2+)
    accountService.findAll()
```

5.2부터 Spring은 코루틴과 Reactor 사이를 양방향으로 자동 변환한다.\
`suspend` 함수는 단일 비동기 결과인 `Mono`로, `Flow`는 0..N 스트림인 `Flux`로 대응되어 "리액티브를 명령형처럼" 작성할 수 있다.

> **코루틴(coroutine) / `suspend`** — 도중에 멈췄다 그 자리에서 이어질 수 있는 함수 / 그런 함수임을 Kotlin에서 표시하는 키워드.\
> 예: 위 코드의 `suspend fun get(...)`에 원문이 단 주석이 "suspend, 논블로킹"이다.

```text
Kotlin 코루틴                                                   Reactor

suspend fun (단일 결과)  <-- awaitSingle / Mono.asFlow -->  Mono<T> (0..1)

Flow<T> (0..N 스트림)    <-- asFlux / Flux.asFlow -->       Flux<T> (0..N)
```

- 이 그림은 원문의 셋째 mermaid 그림을 글자로 옮긴 것이다 — 화살표 둘로 원문과 같고, 둘 다 원문처럼 양방향이다.
- 양쪽 머리의 `Kotlin 코루틴`·`Reactor`는 원문이 두 묶음에 붙인 제목이고, 네 칸의 글자와 화살표 위 라벨도 원문 그대로다(원문이 `&lt;`·`&gt;`로 적은 꺾쇠는 화면에 보이는 대로 `<`·`>`로 적었다).
- 같은 행에 놓인 둘이 대응 쌍인 것은 원문이 그렇게 이었기 때문이다 — 바로 위 문단이 "`suspend` 함수는 단일 비동기 결과인 `Mono`로, `Flow`는 0..N 스트림인 `Flux`로 대응"이라고 적는다.

---

### JUnit 5(Jupiter) 지원

새 `SpringExtension`으로 JUnit 5와 통합.\
`@ExtendWith(SpringExtension.class)` 또는 `@SpringJUnitConfig`로 테스트 컨텍스트를 구성한다(JUnit 4도 계속 지원).

### 기타
- 코어를 Java 8 baseline으로 정비(인터페이스 default 메서드, `@FunctionalInterface` 다수).
- `spring-jcl` 도입(자체 Commons Logging 브릿지), 로깅 의존성 정리.
- 5.1: Reactor Netty 0.8 기반 HTTP/2 지원, Kotlin beans DSL 정제, JDK 11 지원.
- 5.2: Kotlin 코루틴/`Flow`, R2DBC(리액티브 관계형 DB) 초기 통합, 성능 개선.
- 5.3: 데이터 바인딩·검증 개선, RSocket 안정화. (JDK 17 실행 지원은 GA 이후 5.3.x 유지보수 라인에서 추가)

> **R2DBC** — 원문이 괄호로 "리액티브 관계형 DB"라 적은 것. 5.2에서 초기 통합됐다.\
> 예: 원문은 「영향과 의의」에서 이것을 WebFlux·WebClient·RSocket과 함께 "풀 논블로킹 스택 구성"의 부품으로 든다.

## 설정 스타일의 변화

설정의 기본은 이미 4.x/Boot에서 **Java Config + 어노테이션 + Boot 자동 구성**으로 굳어졌다.\
5.x가 더한 것은 **함수형/DSL 스타일**이다.
- Java: `RouterFunction`로 라우팅을 함수로 표현.
- Kotlin: `beans { }` DSL과 `router { }` DSL로, 어노테이션 없이도 컨테이너와 웹 라우팅을 선언적으로 구성. 리플렉션·어노테이션 처리 비용을 줄여 시작 속도에도 유리.

즉 "XML → 어노테이션 → Java Config"의 흐름에 **"함수형 DSL"**이라는 선택지가 추가됐다.

> **리플렉션(reflection)** — 프로그램이 돌아가는 중에 클래스·메서드 같은 자기 구조를 들여다보고 다루는 기능.\
> 예: 원문은 Kotlin DSL의 이점으로 "리플렉션·어노테이션 처리 비용을 줄여 시작 속도에도 유리"하다고 적는다.

## 마이너 버전별 변화
- 5.0 (2017-09): **WebFlux/Reactor**, 함수형 라우팅, WebClient, **Kotlin 1급 지원(널 안정성·확장 함수·beans/router DSL)**, JUnit 5 지원, Java 8 baseline, `javax.*` 유지.
- 5.1 (2018-09): **JDK 11 지원**, Reactor Netty 0.8 기반 HTTP/2, Kotlin beans DSL 정제, 성능·로깅 개선.
- 5.2 (2019-09/10): **Kotlin 코루틴/`Flow` 지원**, R2DBC 통합, RSocket 지원, 관측용 Reactor checkpoint.
- 5.3 (2020-10): 장기 지원(LTS급) 버전. RSocket·데이터 바인딩·CORS 개선. GA 시점은 JDK 8-15 대응이고 **JDK 17 실행 지원은 이후 5.3.x 유지보수 라인에서 추가**됐다(5.3.x는 JDK 21에서 실행 가능하나, 프레임워크 차원의 가상 스레드 지원 API는 6.1부터).

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

- **리액티브 프로그래밍**을 Spring 생태계의 정식 옵션으로 만들었다. WebFlux·WebClient·R2DBC·RSocket로 풀 논블로킹 스택 구성이 가능해졌다(단, 명령형 MVC가 사라진 것은 아니며 둘은 공존).
- **Kotlin을 JVM 백엔드의 주류 언어로 끌어올린 분기점.** Spring의 1급 지원 덕분에 Kotlin + Spring Boot 조합이 실무에서 폭넓게 채택됐고, 코루틴 지원으로 "리액티브를 명령형처럼" 쓰는 길이 열렸다.
- 함수형 빈/라우터 DSL과 Java 8 baseline 정비는 6.x의 AOT·네이티브 이미지 최적화로 가는 사전 작업이기도 하다.

## 용어 풀이

- **블로킹 / 논블로킹(blocking / non-blocking)** — 결과가 나올 때까지 그 스레드를 붙들어 두는 방식 / 붙들지 않고 스레드를 돌려주는 방식. 원문 그림의 "스레드 블록 (대기)"와 "스레드 즉시 반환"이 그 짝이다.
- **이벤트 루프(event loop)** — 준비된 이벤트를 차례로 꺼내 처리하는 소수의 스레드. 원문이 배경으로 든 Node.js의 모델이고, WebFlux 그림의 둘째 칸이다.
- **Reactive Streams** — 원문이 배경으로 든 표준. "JDK 9의 `java.util.concurrent.Flow`로 편입"됐다고 적는다.
- **Reactor / `Mono` / `Flux`** — Spring이 기본으로 쓰는 리액티브 라이브러리 / 결과가 많아야 하나(0..1)인 타입 / 결과가 여럿(0..N)일 수 있는 타입.
- **구독(subscribe)** — 리액티브 타입에 담긴 일이 실제로 굴러가기 시작하는 시점. 원문 주석은 "구독 시점에 비동기 실행"이다.
- **`spring-webflux` / `spring-webmvc`** — 논블로킹 웹 스택 / 기존 서블릿 기반 웹 스택. 원문은 WebFlux를 후자와 "별개로" 새로 만든 것이라 적고, 둘이 "공존"한다고 적는다.
- **라우팅(routing) / 라우터(router)** — 들어온 요청을 어느 처리기가 맡을지 정하는 일 / 그 규칙을 담은 것. Java 쪽 모델이 `RouterFunction`이다.
- **HTTP 클라이언트** — 내 서버가 남의 서버를 부를 때 쓰는 쪽. 원문은 `RestTemplate`을 블로킹, `WebClient`를 논블로킹으로 갈라 적는다.
- **1급 시민(first-class)** — 곁다리가 아니라 설계할 때부터 본래 대상과 같은 대접을 받는 것. 원문이 Kotlin 지원에 붙인 말이다.
- **널 안정성(null-safety)** — 값이 비어 있을 수 있는지를 타입으로 드러내, 비어 있는 값을 잘못 쓰는 일을 컴파일러가 잡게 하는 것. 원문이 든 수단이 JSR-305 기반 `@Nullable`/`@NonNull` 메타 어노테이션이다.
- **확장 함수(extension function)** — 남이 만든 타입에 내가 메서드를 덧붙여 쓰는 것처럼 보이게 하는 Kotlin 문법. 원문이 든 예가 `getBean<T>()`다.
- **reified 제네릭** — 원문이 `getBean<T>()`의 밑바탕으로 든 Kotlin 기능. 원문은 이름만 들고 넘어간다.
- **DSL(Domain-Specific Language)** — 한 가지 일에만 쓰도록 좁게 만든 표기법. 5.x가 더한 것이 `beans { }`와 `router { }`다.
- **코루틴(coroutine) / `suspend`** — 도중에 멈췄다 그 자리에서 이어질 수 있는 함수 / 그런 함수임을 표시하는 Kotlin 키워드. 5.2부터 Spring이 이것과 Reactor 사이를 양방향으로 자동 변환한다.
- **`Flow`** — Kotlin 쪽의 0..N 스트림 타입. 원문은 이것을 `Flux`에 대응시킨다.
- **R2DBC** — 원문 표현으로 "리액티브 관계형 DB". 5.2에서 초기 통합됐다.
- **RSocket** — 원문이 5.2에서 "지원", 5.3에서 "안정화"라 적은 것. 풀 논블로킹 스택의 부품으로 든다.
- **`SpringExtension`** — JUnit 5와 Spring 테스트 컨텍스트를 잇는 새 장치. `@ExtendWith(SpringExtension.class)` 또는 `@SpringJUnitConfig`로 쓴다.
- **리플렉션(reflection)** — 실행 중에 클래스·메서드 같은 자기 구조를 들여다보고 다루는 기능. 원문은 Kotlin DSL이 이 비용을 줄여 "시작 속도에도 유리"하다고 적는다.

## 참고 출처
- [Spring Framework 5.0 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-5.0-Release-Notes)
- [Spring Framework 5.1 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-5.1-Release-Notes)
- [Spring Framework 5.2 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-5.2-Release-Notes)
- [Spring Framework 5.3 - versionlog](https://versionlog.com/spring-framework/5.3/)
- [Spring Framework - Wikipedia](https://en.wikipedia.org/wiki/Spring_Framework)
