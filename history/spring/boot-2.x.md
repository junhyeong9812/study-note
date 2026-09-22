# Spring Boot 2.x (2018 ~)

> 원본: `~/project/java-history/spring/boot-2.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/애너테이션 이름·코드블록 5개·설정 키는 원문 그대로다.\
> ASCII 도식 3개(그중 2개는 원문의 mermaid 도식을 옮긴 것), 「한눈에」의 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Spring Framework 5 기반의 대약진. 리액티브(WebFlux), Micrometer 기반 관측성, 그리고 **Kotlin 1급 지원**으로 "현대 JVM 백엔드"의 표준을 다시 썼다.

이 편을 한 낱말로 잡으면 "**한 지붕 아래**"다 — 원문이 「영향과 의의」에서 직접 쓴 말이다.\
집 하나에 방이 둘 있고, 하는 일의 성격에 따라 어느 방에서 일할지 고른다.\
**Boot 2.x의 웹 스택도 똑같은 구조다** — 원문 표현으로 "명령형(MVC)과 리액티브(WebFlux)를 한 지붕 아래 두어, 워크로드 특성에 맞는 스택 선택을 표준화했다".

본문 흐름에 쓰는 비유는 원문의 이 「한 지붕」 하나뿐이다.

| 비유 | 실체 |
|------|------|
| 한 지붕 | 하나의 Spring Boot 2.x — 원문 "한 프레임워크에서 선택할 수 있게 했다" |
| 지붕 아래의 두 방 | 명령형(MVC)과 리액티브(WebFlux) — 원문 "명령형(MVC)과 리액티브(WebFlux)를 한 지붕 아래 두어" |
| 어느 방에서 일할지 고르는 기준 | 원문 "워크로드 특성에 맞는 스택 선택" |

그 지붕이 어디서 왔는지부터 두 칸으로 놓으면 이렇다.

```text
 Spring Framework 5.0 (2017)                 Spring Boot 2.0 (2018)
 +---------------------------------+        +----------------------------------+
 | Reactor 기반 리액티브 스택과    |        | 이 새 능력을 자동 설정으로 흡수  |
 | Kotlin 지원을 정식 도입         | --흡수-->| → 명령형(MVC)과 리액티브(WebFlux)|
 |                                 |        |   를 한 프레임워크에서 선택      |
 +---------------------------------+        +----------------------------------+
```

그림 해설 — 왼쪽 칸은 원문 「시대적 배경」의 "기반 변화" 항목이고("Spring Framework 5.0(2017)이 Reactor 기반 리액티브 스택과 Kotlin 지원을 정식 도입했다"), 오른쪽 칸과 화살표 라벨은 그 바로 다음 문장이다.\
화살표는 원문이 "흡수해"라고 적은 그 관계 하나이고, 원문은 Boot 2.x의 "기반 Spring Framework 버전"을 5.x로 「릴리스 정보」에 따로 적어 둔다 — 오른쪽 칸이 왼쪽 칸을 대신한 것이 아니다.

## 릴리스 정보
- **최초 출시**: Spring Boot 2.0 GA — 2018년 3월 1일
- **주요 마이너 버전과 시기**:
  - 2.0 (2018-03) — Spring Framework 5, WebFlux, Micrometer, Kotlin 1급 지원, HikariCP 기본
  - 2.1 (2018-10)
  - 2.2 (2019-10) — Java 13 지원, RSocket, JUnit 5 기본
  - 2.3 (2020-05) — 메이븐·그레이들 플러그인 기반 OCI 이미지 빌드(Buildpacks), Liveness/Readiness 프로브, Graceful shutdown
  - 2.4 (2020-11) — `application.yml` 설정 파일 처리 방식 개편(config data API), 도커 이미지/k8s 강화
  - 2.5 (2021-05) — SQL 초기화 개편, 환경변수 prefix
  - 2.6 (2021-11) — Actuator 보강, 순환 참조 기본 금지
  - 2.7 (2022-05) — 2.x 마지막 피처 라인, 3.0 준비(점진적 마이그레이션 가이드 제공)
- **기반 Spring Framework 버전**: Spring Framework 5.x (2.0은 5.0, 2.7은 5.3)
- **최소 자바 버전**: **Java 8** (Java 8 베이스라인, 이후 9~17 지원 확대)

> **베이스라인(baseline)** — 이 버전을 돌리려면 최소한 있어야 하는 바닥 선.\
> 예: 원문이 2.x의 바닥을 Java 8로 적고, 그 위로 "9~17 지원 확대"라고 덧붙인다 — 바닥이 8이지 8만 된다는 말이 아니다.

## 시대적 배경 (왜 2.0인가)

1.x가 "설정 자동화"로 성공을 거둔 사이, JVM 생태계는 빠르게 변했다.

- **리액티브 프로그래밍**의 부상: 고동시성·논블로킹 I/O 수요가 커지며 Reactor/RxJava 기반 모델이 주목받았다.
- **관측성(Observability)** 요구 증가: 마이크로서비스가 보편화되며 Prometheus, Datadog 등 다양한 모니터링 백엔드와의 연동이 필수가 되었다.
- **Kotlin의 약진**: 2016년 Kotlin 1.0, 2017년 안드로이드 1급 언어 채택으로 JVM 진영에서 Kotlin이 급부상했다.
- **기반 변화**: Spring Framework 5.0(2017)이 Reactor 기반 리액티브 스택과 Kotlin 지원을 정식 도입했다.

Spring Boot 2.0은 이 Spring Framework 5의 새 능력을 자동 설정으로 흡수해, 명령형(MVC)과 리액티브(WebFlux)를 한 프레임워크에서 선택할 수 있게 했다.

> **논블로킹 I/O(non-blocking I/O)** — 입출력의 답을 기다리는 동안 그 자리를 붙들고 서 있지 않는 방식.\
> 예: 원문이 논블로킹 I/O와 나란히 든 수요가 "고동시성"이다 — 동시에 붙는 연결이 많은 상황이다.

> **관측성(Observability)** — 돌아가고 있는 시스템의 안을 밖에서 들여다볼 수 있게 해 두는 것.\
> 예: 원문이 이 항목에서 드는 것이 "Prometheus, Datadog 등 다양한 모니터링 백엔드와의 연동"이다.

## 핵심 기능

### Spring WebFlux (리액티브 웹 스택)
서블릿 블로킹 모델 대신 Reactor 기반 논블로킹 스택을 제공한다. `Mono`/`Flux`를 반환값으로 쓰며, 기본 서버는 Netty다. 애너테이션 방식과 함수형(WebFlux.fn) 방식을 모두 자동 설정한다.

```java
@RestController
public class UserController {
    private final UserRepository repo; // ReactiveCrudRepository
    public UserController(UserRepository repo) { this.repo = repo; }

    @GetMapping("/users")
    public Flux<User> all() {
        return repo.findAll();         // 논블로킹 스트림
    }

    @GetMapping("/users/{id}")
    public Mono<User> one(@PathVariable String id) {
        return repo.findById(id);
    }
}
```

> **`Mono` / `Flux`** — Reactor의 타입 둘. 원문은 WebFlux가 이 둘을 "반환값으로 쓰며"라고 적고, `Flux`가 나오는 자리에 "논블로킹 스트림"이라는 주석을 달아 두었다.\
> 예: 위 코드에서 목록을 주는 `all()`이 `Flux<User>`를, `id`로 하나를 집는 `one()`이 `Mono<User>`를 반환한다.

명령형(MVC)과 리액티브(WebFlux)가 한 프레임워크에서 어떤 스택 위에 놓이는지 비교하면 다음과 같다.

```text
 Spring MVC (명령형)
   Spring MVC      -->  서블릿 API  -->  Tomcat
   (블로킹 처리)                         (서블릿 컨테이너 + 스레드풀)

 Spring WebFlux (리액티브)
   Mono / Flux     -->  Reactor     -->  Netty
                        (논블로킹)
```

같은 Boot 위에서 워크로드 특성에 따라 블로킹(MVC)과 논블로킹(WebFlux) 스택을 선택한다.

그림 해설 — 두 줄의 제목과 여섯 칸의 문구, 네 화살표는 원문 도식의 것 그대로이고, 원문 도식의 두 갈래(subgraph)를 위아래 두 줄로 놓았다.\
원문은 두 스택을 각각 세 칸의 사슬로 그려 나란히 비교한다.\
원문이 이 자리에 적은 선택 기준은 "워크로드 특성"이다.

함수형 라우터(WebFlux.fn) 예시:

```java
@Bean
RouterFunction<ServerResponse> routes(UserHandler handler) {
    return route(GET("/users"), handler::all)
        .andRoute(GET("/users/{id}"), handler::one);
}
```

> **함수형 라우터(WebFlux.fn)** — 애너테이션으로 URL을 붙이는 대신, 경로와 처리 함수를 짝지어 코드로 등록하는 방식.\
> 예: 위 코드의 `route(GET("/users"), handler::all)`이 `GET /users`라는 경로와 `handler`의 `all` 함수를 그 자리에서 짝지은 줄이다.

### Actuator 재설계 + Micrometer
2.0은 자체 메트릭 API를 버리고 **Micrometer**(메트릭 파사드, "메트릭계의 SLF4J")로 전면 교체했다. 하나의 계측 코드로 Prometheus, Datadog, Influx, Graphite, JMX, New Relic 등 다양한 백엔드에 내보낸다.

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health, info, metrics, prometheus
  metrics:
    export:
      prometheus:
        enabled: true
```

엔드포인트 경로도 `/actuator/*` 아래로 통일되고 노출 정책이 명시적(opt-in)으로 바뀌었다.

> **파사드(facade)** — 뒤에 무엇이 있든 앞에서는 한 가지 모양으로만 쓰게 해 주는 껍데기. 원문이 Micrometer에 붙인 별명이 "메트릭계의 SLF4J"다.\
> 예: 원문 문장 그대로 "하나의 계측 코드로 Prometheus, Datadog, Influx, Graphite, JMX, New Relic 등 다양한 백엔드에 내보낸다" — 코드는 그대로 두고 내보낼 곳만 갈아 끼운다.

> **opt-in(명시적 노출)** — 기본은 꺼 두고, 켜겠다고 적은 것만 켜지는 방식.\
> 예: 위 YAML의 `include: health, info, metrics, prometheus`가 그렇게 적어 넣은 목록이다.

Micrometer가 계측 파사드로 끼어들어 메트릭이 다양한 백엔드로 흘러가는 파이프라인은 다음과 같다.

```text
 애플리케이션         Micrometer         MeterRegistry
 (Actuator 계측) -->  (계측 파사드) -->  (레지스트리)
                                             |
                                             +--"pull: /actuator/prometheus scrape"--> Prometheus
                                             |
                                             +--"push"--> Datadog
                                             |
                                             +--"push"--> Influx / JMX 등
```

하나의 계측 코드(Micrometer)가 레지스트리를 거쳐 벤더 중립적으로 여러 모니터링 백엔드로 내보낸다. 단, 전송 방식은 백엔드마다 달라서 Prometheus는 애플리케이션이 노출한 `/actuator/prometheus` 엔드포인트를 Prometheus 서버가 **scrape**(pull)하고, Datadog·Influx 등은 애플리케이션이 **push**한다.

그림 해설 — 다섯 화살표와 그 라벨(`pull: /actuator/prometheus scrape`·`push`·`push`)은 원문 도식의 것 그대로다.\
위 캡션이 그 라벨 차이를 그대로 풀어 적은 자리다 — Prometheus 쪽 화살표는 실제로는 Prometheus 서버가 와서 긁어 가는 방향이고, 나머지 둘은 애플리케이션이 보내는 방향이다.

> **pull(scrape) / push** — 받는 쪽이 주기적으로 와서 긁어 가는 방식 / 보내는 쪽이 먼저 밀어 넣는 방식.\
> 예: 원문 그대로, Prometheus는 `/actuator/prometheus`를 "scrape(pull)"하고 Datadog·Influx 등에는 애플리케이션이 "push"한다.

### Kotlin 1급 지원
Spring Framework 5의 Kotlin 지원을 Boot 차원에서 흡수했다. **start.spring.io의 언어 선택지에 Kotlin이 정식 포함**되었고, 생성 시 `kotlin-spring`/`kotlin-jpa` 컴파일러 플러그인과 Kotlin용 스타터 의존성이 자동 구성된다.

```kotlin
@SpringBootApplication
class DemoApplication

fun main(args: Array<String>) {
    runApplication<DemoApplication>(*args)   // Boot가 제공하는 Kotlin 최상위 함수(reified 제네릭)
}

@RestController
class HelloController {
    @GetMapping("/")
    fun hello() = "Hello, Kotlin + Spring Boot 2"
}
```

(Kotlin 채택사와 적용 방식은 `kotlin-and-spring.md`에서 깊게 다룬다.)

> **1급 지원(first-class support)** — 곁다리로 되는 정도가 아니라, 공식 선택지로 넣고 필요한 설정까지 갖춰 주는 것. 원문이 이 절에서 드는 내용이 그 범위다.\
> 예: 원문이 든 두 가지가 "start.spring.io의 언어 선택지에 Kotlin이 정식 포함"과 "`kotlin-spring`/`kotlin-jpa` 컴파일러 플러그인과 Kotlin용 스타터 의존성이 자동 구성"이다.

> **최상위(top-level) 함수** — 클래스 안이 아니라 파일 바로 아래에 선언해, 어떤 타입에도 덧붙지 않고 그대로 부르는 Kotlin 함수.\
> 예: 위 코드의 `runApplication<DemoApplication>(*args)`가 그렇게 선언된 함수이고, 꺾쇠 안의 타입은 `reified` 제네릭이라 함수 안에서 실제 타입으로 읽힌다.

### HikariCP 기본 커넥션 풀
기본 JDBC 커넥션 풀이 Tomcat JDBC Pool에서 **HikariCP**로 교체되었다. 더 빠르고 가벼운 풀이 표준이 되었다.

> **커넥션 풀(connection pool)** — DB 연결을 미리 만들어 두고 돌려 쓰는 주머니. 쓸 때마다 새로 연결하지 않는다.\
> 예: 원문이 든 두 이름 `Tomcat JDBC Pool`과 `HikariCP`가 그 주머니를 맡던 구현들이고, 2.0에서 기본이 뒤쪽으로 바뀌었다.

### 설정 프로퍼티 바인딩 개선
2.0은 타입 안전 바인딩 엔진(Binder API)을 새로 작성해 relaxed binding 규칙을 정리했다. 이어 2.2에서 `@ConstructorBinding`을 통한 불변(immutable) 설정 객체 바인딩이 추가되었다.

```java
// @ConstructorBinding은 Spring Boot 2.2부터 사용 가능
@ConfigurationProperties("app")
@ConstructorBinding
public class AppProperties {
    private final String name;
    private final int retries;
    public AppProperties(String name, int retries) {
        this.name = name;
        this.retries = retries;
    }
}
```

> **바인딩(binding)** — 설정 파일·환경변수에 적힌 값을 자바 객체의 필드에 채워 넣는 일.\
> 예: 위 코드의 `@ConfigurationProperties("app")`가 `app`으로 시작하는 설정 값들을 이 객체의 `name`·`retries`에 채우라는 표시다.

> **불변(immutable) 객체** — 한 번 만들어진 뒤 값이 바뀌지 않는 객체.\
> 예: 위 코드의 두 필드가 `private final`이고 값은 생성자로만 들어간다 — 원문이 `@ConstructorBinding`에 "불변(immutable) 설정 객체"라는 말을 붙인 이유다.

### 그 외
- **Java 8 베이스라인**: 람다/스트림/`java.time` 전제. 이후 마이너에서 9~17까지 지원 확대.
- **OCI 이미지 빌드(2.3+)**: Dockerfile 없이 Cloud Native Buildpacks로 컨테이너 이미지를 생성(`mvn spring-boot:build-image`).
- **Graceful shutdown / Liveness·Readiness 프로브(2.3+)**: 쿠버네티스 환경 대응.

> **Buildpacks(Cloud Native Buildpacks)** — 소스에서 컨테이너 이미지를 만들어 주는 도구. 원문 표현으로 "Dockerfile 없이".\
> 예: 원문이 드는 명령이 `mvn spring-boot:build-image`이고, 그 결과물이 OCI 이미지다.

> **Graceful shutdown** — 종료 신호를 받았을 때 바로 끊지 않고 처리 중인 요청을 마무리한 뒤 내려가는 것.\
> 예: 원문은 이 기능과 Liveness·Readiness 프로브를 묶어 "쿠버네티스 환경 대응"이라 적는다.

> **Liveness / Readiness 프로브** — 컨테이너가 살아 있는지 / 지금 요청을 받아도 되는지를 바깥에서 물어보는 점검 지점.\
> 예: 원문이 이 둘을 2.3에 넣고 쿠버네티스를 그 쓰임으로 든다.

## 마이너 버전별 변화
- **2.0 (2018)**: WebFlux, Micrometer, Kotlin 1급, HikariCP 기본, Actuator/바인딩 재설계.
- **2.1 (2018)**: 빈 오버라이딩 기본 비활성화, Actuator/JDBC 보강.
- **2.2 (2019)**: JUnit 5 기본, RSocket 지원, Java 13 대응, lazy initialization 옵션, `@ConstructorBinding` 및 `@ConfigurationProperties` 클래스패스 스캔(`@ConfigurationPropertiesScan`) 도입.
- **2.3 (2020)**: Buildpacks 이미지 빌드, k8s 프로브, graceful shutdown, layered jar.
- **2.4 (2020)**: 설정 파일 처리 방식(config data) 개편, `spring.config.import` 도입.
- **2.5 (2021)**: SQL 스크립트 초기화 정비, 환경변수 prefix, Docker 이미지 개선.
- **2.6 (2021)**: 순환 참조 기본 금지, Actuator 보강.
- **2.7 (2022)**: 2.x 마지막 라인. `spring.factories` 기반 자동 설정에서 신규 임포트 파일 방식으로의 전환을 시작하며 3.0 마이그레이션 길을 닦음.

> **layered jar** — jar 안을 바뀌는 정도에 따라 층으로 나눠 둔 것. 원문은 2.3의 항목으로 이름만 든다.\
> 예: 원문이 같은 2.3 줄에 Buildpacks 이미지 빌드를 함께 두었다 — 이름이 나온 자리가 거기까지다.

> **순환 참조(circular reference)** — 두 빈이 서로를 필요로 해서 만드는 순서를 정할 수 없게 되는 상태.\
> 예: 원문은 2.6에서 이것을 "기본 금지"로 바꿨다고 적는다 — 되던 것이 기본값에서 막히게 된 변화다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 네 줄은 원문의 네 불릿 그대로다.)*

- 명령형(MVC)과 리액티브(WebFlux)를 한 지붕 아래 두어, 워크로드 특성에 맞는 스택 선택을 표준화했다.
- Micrometer 채택으로 Spring 애플리케이션의 **관측성**이 벤더 중립적으로 표준화되었고, 이는 3.x의 분산 추적(Tracing)으로 이어진다.
- **Kotlin을 1급 시민으로 받아들여**, 이후 "Kotlin + Spring Boot"가 주류 조합 중 하나로 자리잡는 결정적 전환점이 되었다.
- 4년 반 동안(2018~2022) 사실상 업계 표준 백엔드 플랫폼으로 군림했다.

첫 불릿의 "한 지붕 아래"가 이 문서 「한눈에」에서 빌려 쓴 그 말이고, 둘째 불릿이 가리키는 다음 단계는 3.x 편에서 이어진다.

## 용어 풀이

- **베이스라인(baseline)** — 이 버전을 돌리려면 최소한 있어야 하는 바닥 선. 2.x는 Java 8이고, 이후 마이너에서 9~17까지 지원이 확대됐다.
- **논블로킹 I/O(non-blocking I/O)** — 입출력의 답을 기다리는 동안 그 자리를 붙들고 서 있지 않는 방식. 원문이 이것과 나란히 든 수요가 고동시성이다.
- **관측성(Observability)** — 돌아가는 시스템의 안을 밖에서 들여다볼 수 있게 해 두는 것. 2.x에서는 메트릭이, 3.x에서는 분산 추적이 더해진다.
- **리액티브 웹 스택(WebFlux)** — 서블릿 블로킹 모델 대신 Reactor 기반 논블로킹 스택을 쓰는 웹 스택. 기본 서버는 Netty다.
- **`Mono` / `Flux`** — WebFlux가 "반환값으로 쓰며"라고 원문이 적은 Reactor의 타입 둘. 원문 코드에서 `Flux`가 나오는 자리에 "논블로킹 스트림" 주석이 붙어 있다.
- **Reactor / Netty** — WebFlux가 올라앉는 논블로킹 라이브러리 / 그 기본 서버.
- **함수형 라우터(WebFlux.fn)** — 애너테이션 대신 경로와 처리 함수를 짝지어 코드로 등록하는 방식. WebFlux는 이것과 애너테이션 방식을 모두 자동 설정한다.
- **Actuator** — 운영용 엔드포인트 묶음. 2.0에서 경로가 `/actuator/*` 아래로 통일되고 노출이 opt-in으로 바뀌었다.
- **Micrometer** — 원문 표현으로 "메트릭 파사드, 메트릭계의 SLF4J". 하나의 계측 코드로 여러 모니터링 백엔드에 내보낸다.
- **파사드(facade)** — 뒤에 무엇이 있든 앞에서는 한 가지 모양으로만 쓰게 해 주는 껍데기.
- **MeterRegistry** — 원문 도식에서 Micrometer와 백엔드 사이에 놓인 레지스트리.
- **pull(scrape) / push** — 받는 쪽이 와서 긁어 가는 방식 / 보내는 쪽이 밀어 넣는 방식. 원문 기준 Prometheus가 앞쪽, Datadog·Influx 등이 뒤쪽이다.
- **opt-in(명시적 노출)** — 기본은 꺼 두고 켜겠다고 적은 것만 켜지는 방식.
- **1급 지원(first-class support)** — 공식 선택지로 넣고 필요한 설정까지 갖춰 주는 것. Boot 2.0 Kotlin 지원의 범위는 start.spring.io 정식 옵션과 컴파일러 플러그인·스타터 자동 구성이다.
- **최상위(top-level) 함수 / `reified` 제네릭** — 클래스 밖, 파일 바로 아래에 선언해 어떤 타입에도 덧붙지 않고 부르는 Kotlin 함수 / 꺾쇠 안 타입 인자를 함수 안에서 실제 타입으로 읽게 해 주는 표시. `runApplication<DemoApplication>(*args)`가 둘을 함께 쓴 자리다.
- **커넥션 풀(connection pool)** — DB 연결을 미리 만들어 두고 돌려 쓰는 주머니. 2.0에서 기본이 Tomcat JDBC Pool에서 HikariCP로 교체됐다.
- **바인딩(binding) / relaxed binding** — 설정 값을 객체 필드에 채워 넣는 일 / 이름 표기가 조금 달라도 맞춰 주는 규칙. 2.0이 Binder API를 새로 써서 이 규칙을 정리했다.
- **`@ConstructorBinding`** — 생성자로만 값을 받아 불변 설정 객체를 만드는 애너테이션. 2.2부터 쓸 수 있다.
- **불변(immutable) 객체** — 한 번 만들어진 뒤 값이 바뀌지 않는 객체. 원문이 `@ConstructorBinding`에 "불변(immutable) 설정 객체 바인딩"이라는 말을 붙인 자리다.
- **Buildpacks(Cloud Native Buildpacks)** — Dockerfile 없이 소스에서 컨테이너 이미지를 만들어 주는 도구. 2.3+.
- **OCI 이미지** — 컨테이너 이미지의 표준 형식. Buildpacks의 결과물이 이것이다.
- **Graceful shutdown** — 종료 신호를 받고도 처리 중인 요청을 마무리한 뒤 내려가는 것. 2.3+.
- **Liveness / Readiness 프로브** — 살아 있는지 / 요청을 받아도 되는지를 바깥에서 묻는 점검 지점. 원문은 쿠버네티스 대응으로 든다.
- **layered jar** — jar 안을 바뀌는 정도에 따라 층으로 나눠 둔 것. 원문은 2.3의 항목으로 이름만 든다.
- **config data** — 2.4에서 개편된 설정 파일 처리 방식. 같은 줄에 `spring.config.import` 도입이 붙는다.
- **순환 참조(circular reference)** — 두 빈이 서로를 필요로 해 만드는 순서를 정할 수 없는 상태. 2.6에서 기본 금지가 됐다.

## 참고 출처
- [Spring Boot 2.0 goes GA (spring.io blog)](https://spring.io/blog/2018/03/01/spring-boot-2-0-goes-ga/)
- [Spring Boot 2.0 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.0-Release-Notes)
- [Spring releases Spring Boot 2.0 (SD Times)](https://sdtimes.com/webdev/spring-releases-spring-boot-2-0/)
- [Spring Boot 2.0 Goes GA — Phil Webb interview (InfoQ)](https://www.infoq.com/news/2018/03/spring-boot-2.0-release-ga-webb)
- [Spring Boot version history (codejava.net)](https://www.codejava.net/frameworks/spring-boot/spring-boot-version-history)
