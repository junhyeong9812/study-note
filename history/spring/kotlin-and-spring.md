# Kotlin과 Spring: 도입사와 적용 방식

> 원본: `~/project/java-history/spring/kotlin-and-spring.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/애너테이션 이름·플러그인 이름·표 2개·코드블록 14개는 원문 그대로다.\
> ASCII 도식 3개(그중 2개는 원문의 mermaid 도식을 옮긴 것), 「한눈에」의 선로 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 「재서술자 주」 1개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 코틀린이 언제, 어떻게 Spring에 들어왔는가 — 그리고 자바와 코틀린이 같은 프로젝트에서 어떻게 공존하는가

이것을 하나의 비유로 읽으면 **같은 선로 위를 달리는 두 열차**다.\
선로와 역이 그대로이면 새 열차를 들여오는 데 공사가 필요 없다 — 같은 선로에 올려 같은 역에 세우면 된다.\
**자바와 코틀린도 똑같은 구조다** — 원문이 "자바 바이트코드로 컴파일되므로 기존 자바 라이브러리/프레임워크를 그대로 쓸 수 있다 — 이 점이 Spring이 코틀린을 빠르게 받아들일 수 있었던 토대다"라고 적은 자리다.

본문 흐름에 쓰는 비유는 이 선로 하나뿐이다.

| 비유 | 실체 |
|------|------|
| 같은 선로 | 자바 바이트코드 — 원문 "코틀린은 자바 바이트코드로 컴파일되므로" |
| 그 선로를 달리는 두 열차 | 자바 클래스와 코틀린 클래스 — 원문 "한 프로젝트에 자바 클래스와 코틀린 클래스를 섞어 둘 수 있다" |
| 같은 역과 같은 승강장 | 원문 "둘이 같은 Spring API와 같은 빈 컨테이너 위에서 동작한다" |

Spring이 코틀린을 받아들인 순서는 원문이 「타임라인」 표 아래 「주의」에서 직접 적어 두었다. 그것을 세로로 놓으면 이렇다.

```text
 원문 「주의」가 적은 정착 순서

 프로젝트 생성기에서 먼저 실험                        (start.spring.io — 원문 표기 "2016년경")
   |
 프레임워크 본체(5.0)에서 1급 지원                    (표: 2017-09)
   |
 Spring Boot 2.0에서 스타터·플러그인까지 정식 지원    (표: 2018-03)
   |
 그 다음 단계 — 코루틴(suspend) 1급 지원              (원문 표기 "Spring Framework 5.2(2019)")
```

그림 해설 — 네 줄의 문구는 원문 「주의」 블록의 것이고, 오른쪽 괄호의 날짜 중 둘은 같은 문서 「타임라인」 표에서 가져온 보충이다.\
세로선에는 화살촉을 달지 않았다 — 원문 「주의」가 화살표로 이은 것은 앞의 세 단계까지이고, 넷째는 "그 다음 단계"라는 말로 따로 붙였기 때문이다.\
원문이 이 순서를 적어 둔 이유도 그 블록에 있다 — "'Boot 2.0에서 코틀린 지원이 모두 끝났다'는 의미는 아니다."

## 코틀린 언어 약사

코틀린(Kotlin)은 JetBrains(IntelliJ IDEA 제작사)가 만든 JVM 언어다. 이름은 러시아 상트페테르부르크 인근의 코틀린 섬에서 따왔다.

| 시기 | 사건 |
|------|------|
| 2011-07 | JetBrains가 JVM용 신규 언어 "Kotlin" 공개 발표 |
| 2012-02 | Apache License 2.0으로 오픈소스화 |
| 2016-02-15 | **Kotlin 1.0 출시** — 첫 공식 안정 버전, 하위 호환성 장기 보장 시작 |
| 2017-05 | Google I/O에서 **안드로이드 1급 언어로 공식 채택** (Android Studio 3.0, 2017-10부터 기본 포함) |
| 2018-10 | Kotlin 1.3 — **코루틴(coroutines) 안정화** |
| 2019-05 | Google, 안드로이드 개발에서 **"Kotlin 우선(Kotlin-first)"** 선언 |
| 2020 이후 | 1.4, 1.5, 1.6, 1.7, 1.8, 1.9 → 2.0(2024, K2 컴파일러) 으로 진화 |

코틀린의 핵심 매력은 **자바와의 100% 상호운용성**, **널 안정성(null-safety)**, **간결한 문법(data class, 확장 함수, 후행 람다 등)**, 그리고 **코루틴 기반 비동기**다. 자바 바이트코드로 컴파일되므로 기존 자바 라이브러리/프레임워크를 그대로 쓸 수 있다 — 이 점이 Spring이 코틀린을 빠르게 받아들일 수 있었던 토대다.

> **JVM 언어** — 자바 가상 머신(JVM) 위에서 도는 언어. 소스는 달라도 컴파일 결과가 자바 바이트코드라 같은 자리에서 돈다.\
> 예: 원문이 코틀린을 "JetBrains가 만든 JVM 언어"라 소개하고, 그 이점으로 "기존 자바 라이브러리/프레임워크를 그대로 쓸 수 있다"를 든다.

> **상호운용성(interoperability)** — 두 언어가 서로의 것을 그대로 불러 쓸 수 있는 성질.\
> 예: 원문이 코틀린의 핵심 매력 첫 항목으로 든 "자바와의 100% 상호운용성"이 그것이고, 뒤의 「같은 프로젝트에서 혼용」 절이 그 실제 모습이다.

> **바이트코드(bytecode)** — 소스를 JVM이 읽을 수 있는 명령 목록으로 바꿔 둔 것.\
> 예: 원문 문장 그대로 "자바 바이트코드로 컴파일되므로" 자바 쪽 자산을 그대로 쓸 수 있다.

## 타임라인: Spring의 Kotlin 채택

| 시기 | 사건 |
|------|------|
| 2016 초 | **start.spring.io에 Kotlin 언어 옵션이 (실험적으로) 추가** — Spring 진영의 첫 공식 코틀린 발자국 |
| 2017-01-04 | spring.io 블로그 "Introducing Kotlin support in Spring Framework 5.0" 게시 |
| 2017-09 | **Spring Framework 5.0 GA — Kotlin 1급 지원 정식 포함** (널 안정성 메타데이터, 확장 함수, 빈 DSL, 라우터 DSL) |
| 2018-03 | **Spring Boot 2.0 GA — Kotlin 1급 지원** (start.spring.io 정식 Kotlin 옵션, 컴파일러 플러그인/스타터 자동 구성) |
| 2019-04 | 블로그 "Going Reactive with Spring, Coroutines and Kotlin Flow" — 코루틴/Flow 통합 발표 |
| 2019-09 | **Spring Framework 5.2 — 코루틴(suspend 함수) 정식 지원** (WebFlux 코루틴, `Flow` ↔ `Flux` 연동) |
| 2022~ | Spring Framework 6 / Spring Boot 3 — Java 17·Jakarta 기반에서 Kotlin 지원 지속 (코루틴/DSL 강화) |

> 주의: start.spring.io의 Kotlin 옵션은 Spring Framework 5.0 발표보다 **앞서(2016년경)** 등장했다. 즉 "프로젝트 생성기에서 먼저 실험 → 프레임워크 본체(5.0)에서 1급 지원 → Spring Boot 2.0에서 스타터·플러그인까지 정식 지원"의 순서로 정착했다. 다만 코루틴(`suspend`) 1급 지원은 그 다음 단계인 Spring Framework 5.2(2019)에서 별도로 추가된 것이므로, "Boot 2.0에서 코틀린 지원이 모두 끝났다"는 의미는 아니다.

> **start.spring.io(프로젝트 생성기)** — 어떤 언어·의존성으로 시작할지 골라 프로젝트 뼈대를 받아 가는 웹 도구.\
> 예: 원문이 코틀린 채택의 첫 발자국으로 든 것이 바로 이 도구의 "언어 옵션"에 코틀린이 붙은 일이다.

## Spring이 제공하는 Kotlin 지원 기능

### 널 안정성(null-safety)과 플랫폼 타입
Spring은 모든 패키지에 **`@NonNull`/`@Nullable` 메타데이터**를 선언했다. 덕분에 코틀린 컴파일러가 Spring API의 널 가능성을 인식하고, 자바 타입을 "플랫폼 타입"으로 두루뭉술 넘기지 않고 정확한 코틀린 타입(`String` vs `String?`)으로 다룬다.

```kotlin
// Spring이 required 여부를 코틀린 널 가능성으로 추론한다.
@GetMapping("/greet")
fun greet(@RequestParam name: String): String = "Hi $name"      // 필수 파라미터
@GetMapping("/greet2")
fun greet2(@RequestParam name: String?): String = "Hi ${name ?: "stranger"}" // 선택 파라미터
```

`name: String`은 `required=true`, `name: String?`은 `required=false`로 자동 해석된다. 자바에서는 `@RequestParam(required=false)`를 명시해야 하는 부분이 타입으로 표현된다.

> **널 안정성(null-safety)** — 어떤 자리에 `null`이 올 수 있는지를 **타입으로** 구분해 두는 것. 코틀린에서 `String`과 `String?`이 서로 다른 타입인 것이 그 구분이다.\
> 예: 위 코드의 `name: String`과 `name: String?` 두 줄이 그 구분이고, 원문은 그것이 각각 `required=true`·`required=false`로 "자동 해석된다"고 적는다.

> **플랫폼 타입(platform type)** — 자바에서 온 타입인데 널 가능성 표시가 없어, 코틀린이 널이 될 수 있는지 아닌지를 정하지 못한 채 넘겨받은 타입. 원문은 이 상태를 "두루뭉술"이라 부른다.\
> 예: 원문은 Spring이 `@NonNull`/`@Nullable` 메타데이터를 선언해 둔 덕분에 Spring API가 이 상태로 넘어오지 **않고** 정확한 코틀린 타입으로 다뤄진다고 적는다.

### 코틀린 확장 함수 (Spring이 추가한 확장들)
Spring은 기존 API를 건드리지 않고 코틀린 **확장 함수**로 더 관용적인 사용법을 제공한다. reified 타입 파라미터로 `Class<T>` 인자를 없앤다.

```kotlin
// 자바: restTemplate.getForObject(url, User::class.java)
val user = restTemplate.getForObject<User>(url)             // reified 확장

// WebClient
val users: Flow<User> = client.get().uri("/users")
    .retrieve().bodyToFlow<User>()

// ApplicationContext에서 빈 조회
val service = context.getBean<MyService>()
```

> **확장 함수(extension function)** — 남이 만든 타입에 내가 함수를 덧붙여, 원래 그 타입의 메서드였던 것처럼 쓰는 코틀린 문법. 원문 표현으로 "기존 API를 건드리지 않고".\
> 예: 위 코드의 `context.getBean<MyService>()`가 `ApplicationContext`에 그렇게 덧붙은 함수다.

> **reified 타입 파라미터** — 제네릭 타입을 실행 시점까지 남겨 두어, 타입을 인자로 따로 넘기지 않아도 되게 하는 코틀린 문법.\
> 예: 위 코드 첫 주석의 자바 쪽은 `User::class.java`를 인자로 넘기는데, 코틀린 쪽은 `getForObject<User>(url)`로 그 인자가 사라졌다 — 원문이 "`Class<T>` 인자를 없앤다"고 적은 것이 이 차이다.

### 빈 등록 DSL (`beans { }`)
함수형으로 빈을 등록하는 코틀린 DSL. 리플렉션/CGLIB 없이 명시적으로 빈을 구성할 수 있어 네이티브 이미지와도 궁합이 좋다.

```kotlin
val myBeans = beans {
    bean<UserRepository>()
    bean<UserService>()
    bean {
        UserController(ref())          // ref()로 의존성 주입
    }
}

fun main(args: Array<String>) {
    runApplication<DemoApplication>(*args) {
        addInitializers(myBeans)
    }
}
```

> **DSL(Domain Specific Language, 도메인 특화 언어)** — 어떤 한 가지 일을 적기 좋게 다듬어 둔 작은 표기법. 코틀린에서는 중괄호 블록으로 그런 표기를 만든다.\
> 예: 위 코드의 `beans { ... }` 블록 안이 "빈을 등록하는 일"만을 위한 표기이고, `bean<UserRepository>()` 한 줄이 그 안의 한 문장이다.

> **명시적 구성 vs 리플렉션** — 무엇을 등록할지 코드에 적어 두는 것 / 실행 중에 찾아내는 것. 원문은 이 DSL을 "리플렉션/CGLIB 없이 명시적으로"라고 적고, 그래서 "네이티브 이미지와도 궁합이 좋다"고 덧붙인다.\
> 예: 위 코드에서 등록될 빈 셋(`UserRepository`·`UserService`·`UserController`)이 전부 소스에 그대로 적혀 있다.

### 함수형 라우터 DSL (`router { }`, WebMvc.fn / WebFlux.fn)
애너테이션 대신 코틀린 DSL로 라우팅을 선언한다.

```kotlin
@Bean
fun routes(handler: UserHandler) = router {
    "/users".nest {
        GET("", handler::all)
        GET("/{id}", handler::byId)
        POST("", handler::create)
    }
}
```

> **라우팅(routing)** — 들어온 요청의 경로·메서드를 보고 어느 처리 함수로 보낼지 정하는 일.\
> 예: 위 코드의 `GET("/{id}", handler::byId)`가 `GET /users/{id}` 요청을 `handler`의 `byId`로 보내라고 적은 줄이다(바깥의 `"/users".nest { ... }` 안에 들어 있다).

### 코루틴 지원 (suspend 함수, Spring 5.2+ / WebFlux 코루틴)
Spring Framework 5.2부터 컨트롤러/핸들러에서 **`suspend` 함수**와 **`Flow`**를 직접 쓸 수 있다. 내부적으로 Reactor의 `Mono`/`Flux`와 양방향 변환된다. 리액티브의 성능을 명령형처럼 읽히는 코드로 얻는다.

```kotlin
@RestController
class UserController(private val repo: UserRepository) {

    @GetMapping("/users/{id}")
    suspend fun byId(@PathVariable id: Long): User =      // suspend: Mono<User> 대응
        repo.findById(id) ?: throw NotFoundException()

    @GetMapping("/users")
    fun all(): Flow<User> = repo.findAll()                // Flow: Flux<User> 대응
}
```

코루틴 기반 Spring Data 리포지토리(`CoroutineCrudRepository`)도 제공된다.

> **코루틴(coroutine) / `suspend` 함수** — 도중에 멈췄다가 그 자리에서 다시 이어질 수 있는 함수. `suspend`가 "여기서 멈출 수 있다"는 표시다.\
> 예: 위 코드의 `suspend fun byId(...)`가 그것이고, 원문은 이 함수가 Reactor 쪽 `Mono<User>`에 "대응"한다고 코드 주석에 적어 두었다.

> **`Flow`** — 여러 값이 시간을 두고 흘러나오는 코루틴 쪽 타입.\
> 예: 위 코드의 `fun all(): Flow<User>`가 그것이고, 원문 주석이 이것을 `Flux<User>`에 대응시킨다.

코루틴 구성요소와 Reactor 타입이 양방향으로 대응되는 브리지는 다음과 같다(Spring 5.2+).

```text
 suspend fun                    <-->  Mono<T>

 Flow<T>                        <-->  Flux<T>

 CoroutineCrudRepository        --"리액티브 인프라 위에서 동작"-->  Reactive 리포지토리 인프라
 (suspend / Flow API)                                              (Mono / Flux 기반)
```

`suspend ↔ Mono`, `Flow ↔ Flux`는 양방향으로 변환되는 타입 브리지다(`awaitSingle()`, `asFlow()`, `asFlux()` 등). 반면 `CoroutineCrudRepository`는 `ReactiveCrudRepository`와 서로 변환되는 관계가 아니라, **코루틴 API를 노출하는 별도 추상화**로서 리액티브 인프라 위에서 동작한다. 덕분에 명령형처럼 읽히는 코드로 리액티브 성능을 얻는다.

그림 해설 — 여섯 칸의 문구와 세 화살표(양방향 둘, 라벨 붙은 단방향 하나)는 원문 도식의 것 그대로다.\
위 두 줄과 아래 한 줄의 화살표 모양이 다른 것이 요점이고, 그 차이를 바로 위 원문 문단이 직접 설명한다 — 위 둘은 "양방향으로 변환되는 타입 브리지", 아래 하나는 "서로 변환되는 관계가 아니라" 그 위에서 동작하는 관계다.

## 자바와 코틀린의 공존

### 같은 프로젝트에서 혼용 (상호운용성)
코틀린은 자바 바이트코드로 컴파일되므로, **한 프로젝트에 자바 클래스와 코틀린 클래스를 섞어 둘 수 있다.** 코틀린에서 자바 빈을 주입받거나, 자바에서 코틀린 빈을 주입받는 데 제약이 거의 없다. 점진적 마이그레이션(자바 → 코틀린 부분 전환)이 가능한 이유다.

```kotlin
// 코틀린 서비스가 자바로 작성된 리포지토리를 주입받음
@Service
class OrderService(private val orderRepository: OrderRepository /* 자바 인터페이스 */) {
    fun total(id: Long): Long = orderRepository.findById(id).orElseThrow().amount
}
```

> **점진적 마이그레이션(incremental migration)** — 전부 한 번에 갈아엎지 않고 일부씩 옮겨 가는 방식.\
> 예: 원문이 괄호로 적은 모습이 "자바 → 코틀린 부분 전환"이고, 위 코드가 그 중간 상태다 — 서비스는 코틀린인데 주입받는 리포지토리는 주석대로 "자바 인터페이스"다.

### Gradle/Maven 설정 — 코틀린 + 스프링 플러그인
Spring Boot 프로젝트에서 코틀린을 쓰려면 보통 다음 플러그인을 함께 적용한다.

```kotlin
// build.gradle.kts
plugins {
    id("org.springframework.boot") version "3.x.x"
    id("io.spring.dependency-management") version "1.x.x"
    kotlin("jvm") version "1.9.x"
    kotlin("plugin.spring") version "1.9.x"   // = all-open 래퍼
    kotlin("plugin.jpa") version "1.9.x"      // = no-arg 래퍼 (JPA 사용 시)
}

dependencies {
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin") // 코틀린 데이터 클래스 직렬화
    implementation("org.jetbrains.kotlin:kotlin-reflect")
}
```

플러그인 역할:
- **`kotlin-spring` (all-open 래퍼)**: 아래 "final class 문제" 참조.
- **`kotlin-jpa` (no-arg 래퍼)**: `@Entity`/`@Embeddable`/`@MappedSuperclass`에 합성 기본 생성자를 생성해 JPA의 "인자 없는 생성자" 요구를 충족.
- **`jackson-module-kotlin`**: data class를 기본 생성자 없이도 JSON 역직렬화.

> **재서술자 주:** 원문은 이 목록의 표제를 "플러그인 역할"이라 적고 셋을 드는데, 셋째 `jackson-module-kotlin`은 위 코드에서 `plugins` 블록이 아니라 `dependencies` 블록에 적힌 라이브러리다.\
> 또 같은 `dependencies` 블록의 `kotlin-reflect`는 이 목록에 들어 있지 않다.\
> 표제가 앞 두 항목(`plugin.spring`·`plugin.jpa`)에만 정확히 맞고, 셋째는 "함께 넣는 것"으로 묶인 것으로 보인다. 원문은 고치지 않고 이 자리에 표기만 해 둔다.

> **컴파일러 플러그인(compiler plugin)** — 컴파일하는 동안 코드에 손을 대는 부가 도구. 소스에는 없는 것을 결과물에 넣어 준다.\
> 예: 원문이 든 두 개가 `kotlin-spring`(all-open 래퍼)과 `kotlin-jpa`(no-arg 래퍼)이고, 각각 `open` 처리와 기본 생성자 합성을 맡는다.

> **역직렬화(deserialization)** — JSON 같은 형식으로 들어온 값을 객체로 되돌려 만드는 일.\
> 예: 원문이 `jackson-module-kotlin`의 역할로 적은 "data class를 기본 생성자 없이도 JSON 역직렬화"가 그 방향이다.

### 코틀린에서 Spring 어노테이션 사용 시 주의점 — final class 문제와 all-open
코틀린은 **클래스와 멤버가 기본적으로 `final`**이다. 그런데 Spring은 `@Configuration`, `@Transactional`, AOP 등에서 **CGLIB 프록시(서브클래싱)**를 만들기 때문에, final 클래스는 프록시를 만들 수 없어 문제가 된다.

`kotlin-spring`(all-open) 플러그인이 이를 해결한다. Spring 스테레오타입 애너테이션(`@Component`, `@Configuration`, `@Service`, `@Repository`, `@Controller`, `@RestController` 등 `@Component` 메타 애너테이션이 붙은 것)이 달린 클래스와 그 멤버를 **자동으로 `open` 처리**한다. 따라서 개발자가 일일이 `open class`라고 쓰지 않아도 된다.

```kotlin
// kotlin-spring 플러그인이 없으면 직접 open을 붙여야 한다:
open class MyService { open fun work() { } }

// 플러그인이 있으면 그냥 이렇게 써도 프록시가 동작한다:
@Service
class MyService { fun work() { } }
```

> **`final` / `open`** — 상속·재정의를 막아 둔 상태 / 열어 둔 상태. 원문이 적은 대로 코틀린은 "클래스와 멤버가 기본적으로 `final`"이다(자바는 그 반대로 기본이 열려 있다 — 이 대비는 원문 밖 보충이다).\
> 예: 위 코드 위쪽의 `open class MyService { open fun work() { } }`가 손으로 연 모습이고, 아래쪽은 같은 것을 플러그인이 대신 열어 주는 모습이다.

> **CGLIB 프록시(서브클래싱)** — 원래 클래스를 상속한 대역 클래스를 만들어 그 자리에 끼워 넣는 방식. 상속으로 만들기 때문에 대상이 `final`이면 만들 수 없다.\
> 예: 원문이 이 프록시가 쓰이는 자리로 드는 것이 `@Configuration`, `@Transactional`, AOP이고, 그래서 코틀린의 기본 `final`이 "문제가 된다"고 적는다.

> **스테레오타입 애너테이션(stereotype annotation)** — 이 클래스가 어떤 역할의 빈인지 표시하는 애너테이션 묶음.\
> 예: 원문이 괄호 안에 든 것이 `@Component`, `@Configuration`, `@Service`, `@Repository`, `@Controller`, `@RestController`이고, 묶는 기준으로 "`@Component` 메타 애너테이션이 붙은 것"을 적는다.

코틀린의 final 기본 문제를 컴파일러 플러그인이 어떻게 해결하는지 레이어로 보면 다음과 같다.

```text
                 Kotlin 소스
                      |
          +-----------+-----------+
          |                       |
          v                       v
 kotlin-spring (all-open)   kotlin-jpa (no-arg)
 @Component류 → open 처리    @Entity 기본 생성자 합성
          |                       |
          +-----------+-----------+
                      |
                      v
                   바이트코드
                      |
          +-----------+-----------+
          |                       |
          v                       v
 Spring: CGLIB 프록시 생성   Hibernate: 엔티티 인스턴스화
```

컴파일 단계에서 플러그인이 final/생성자 제약을 풀어주어, Spring과 Hibernate가 런타임에 프록시·인스턴스화를 정상 수행한다.

그림 해설 — 여섯 칸의 문구와 여섯 화살표는 원문 도식의 것 그대로다.\
가운데 `바이트코드`로 둘이 모였다가 다시 둘로 갈라지는 모양이 요점이다 — 왼쪽 갈래(`kotlin-spring`)가 Spring의 프록시 생성으로, 오른쪽 갈래(`kotlin-jpa`)가 Hibernate의 인스턴스화로 곧장 이어진다고 원문 도식이 선을 그어 둔 것은 아니고, 둘 다 같은 바이트코드를 거쳐 간다.

마찬가지로 JPA 엔티티는 `kotlin-jpa`(no-arg)가 없으면 기본 생성자가 없어 Hibernate가 인스턴스를 만들지 못한다. 다만 `kotlin-jpa`는 인자 없는 생성자만 합성할 뿐 클래스를 `open`으로 만들지는 않는다. 게다가 `@Entity`는 Spring 스테레오타입이 아니어서 `kotlin-spring`(all-open)의 기본 대상에도 포함되지 않는다. 따라서 Hibernate의 지연 로딩(프록시 서브클래싱) 등을 위해 엔티티를 non-final로 두려면, `allOpen` 설정에 JPA 애너테이션(`jakarta.persistence.Entity`/`MappedSuperclass`/`Embeddable`)을 직접 지정하거나 클래스에 `open`을 붙여야 한다.

바로 위 문단은 두 플러그인이 서로 덮지 못하는 빈칸을 짚는다. 원문이 든 근거는 둘이다 — `kotlin-jpa`는 "인자 없는 생성자만 합성할 뿐 클래스를 `open`으로 만들지는 않는다", 그리고 `@Entity`는 "Spring 스테레오타입이 아니어서 `kotlin-spring`(all-open)의 기본 대상에도 포함되지 않는다".\
그래서 원문이 내놓는 해법도 둘이다 — `allOpen` 설정에 JPA 애너테이션을 직접 지정하거나, 클래스에 `open`을 붙이는 것.

원문이 이 편에서 비용으로 적은 문장은 「코틀린에서 Spring 어노테이션 사용 시 주의점 — final class 문제와 all-open」 절의 "final 클래스는 프록시를 만들 수 없어 문제가 된다"이다 — 따로 표제를 세우지 않고 이 자리에서 가리킨다.

> **지연 로딩(lazy loading)** — 연관된 데이터를 실제로 쓸 때까지 읽어 오지 않고 미뤄 두는 것. 그 자리를 대역 객체(프록시)가 대신 채운다.\
> 예: 원문이 이것을 괄호로 "프록시 서브클래싱"이라 적으며, 그래서 엔티티를 non-final로 두어야 하는 이유로 든다.

## 자바 vs 코틀린: 같은 Spring 코드 비교

### 엔티티 (Entity)
```java
// Java
@Entity
public class User {
    @Id @GeneratedValue
    private Long id;
    private String name;
    private String email;

    protected User() {}                      // JPA용 기본 생성자
    public User(String name, String email) { this.name = name; this.email = email; }
    public Long getId() { return id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getEmail() { return email; }
    // ... equals/hashCode/toString
}
```
```kotlin
// Kotlin (kotlin-jpa로 no-arg 생성자 생성;
//         지연 로딩 프록시를 쓰려면 allOpen에 @Entity 추가하거나 class에 open 필요)
@Entity
class User(
    var name: String,
    var email: String,
    @Id @GeneratedValue
    var id: Long? = null
)
```

두 블록을 견주어 읽는 자리는 셋이다.\
자바 쪽의 `protected User() {}`에는 원문이 "JPA용 기본 생성자"라는 주석을 달았고, 코틀린 쪽에는 그 줄이 없다 — 코틀린 주석이 적은 대로 `kotlin-jpa`가 그것을 합성하기 때문이다.\
자바 쪽의 게터·세터가 코틀린 쪽에서는 프로퍼티 선언(`var name: String` 등)으로 대신된다 — 원문이 이 대응으로 든 보일러플레이트는 "게터/세터/생성자" 셋이고, 자바 블록의 `// ... equals/hashCode/toString`에 해당하는 것은 코틀린 블록에 **없다**(원문 밖 보충 — 그 셋을 만들어 주는 것은 프로퍼티 선언이 아니라 `data class`인데, 이 엔티티는 그것을 쓰지 않는다).\
그리고 코틀린 쪽 엔티티는 `data class`가 아니라 `class`이며, 원문이 이 자리에 단 조건은 주석의 둘뿐이다 — "kotlin-jpa로 no-arg 생성자 생성"과 "지연 로딩 프록시를 쓰려면 allOpen에 @Entity 추가하거나 class에 open 필요".

> **프로퍼티(property)** — 값을 담는 자리와 그 값을 읽고 쓰는 통로를 한 번에 선언하는 코틀린 문법.\
> 예: 코틀린 블록의 `var name: String` 한 줄이, 자바 블록의 필드 `private String name;`과 `getName()`·`setName(...)` 세 줄에 해당하는 자리다.

### 컨트롤러 (Controller)
```java
// Java
@RestController
@RequestMapping("/users")
public class UserController {
    private final UserService service;
    public UserController(UserService service) { this.service = service; }

    @GetMapping("/{id}")
    public UserDto get(@PathVariable Long id) {
        return service.findById(id);
    }
}
```
```kotlin
// Kotlin
@RestController
@RequestMapping("/users")
class UserController(private val service: UserService) {

    @GetMapping("/{id}")
    fun get(@PathVariable id: Long): UserDto = service.findById(id)
}
```

애너테이션 두 줄(`@RestController`·`@RequestMapping("/users")`)과 `@GetMapping("/{id}")`은 두 블록이 같다.\
달라진 자리는 생성자다 — 자바 쪽의 필드 선언과 생성자 두 줄이, 코틀린 쪽에서는 클래스 이름 옆 괄호 `(private val service: UserService)` 하나로 들어갔다.

### 서비스 (Service)
```java
// Java
@Service
public class UserService {
    private final UserRepository repo;
    public UserService(UserRepository repo) { this.repo = repo; }

    public UserDto findById(Long id) {
        User u = repo.findById(id)
            .orElseThrow(() -> new NotFoundException(id));
        return new UserDto(u.getId(), u.getName(), u.getEmail());
    }
}
```
```kotlin
// Kotlin
@Service
class UserService(private val repo: UserRepository) {

    fun findById(id: Long): UserDto {
        val u = repo.findById(id).orElseThrow { NotFoundException(id) }
        return UserDto(u.id, u.name, u.email)
    }
}
```

생성자 주입은 코틀린에서 주 생성자(primary constructor)로 더 간결해지고, 보일러플레이트(게터/세터/생성자)는 data class/프로퍼티로 사라진다. 핵심은 **둘이 같은 Spring API와 같은 빈 컨테이너 위에서 동작**한다는 점이다.

> **주 생성자(primary constructor)** — 코틀린에서 클래스 이름 바로 옆 괄호에 적는 생성자.\
> 예: 위 코틀린 블록의 `class UserService(private val repo: UserRepository)`에서 괄호 부분이 그것이고, 자바 블록의 필드 선언 + 생성자 두 줄에 해당한다.

> **생성자 주입(constructor injection)** — 필요한 빈을 생성자의 인자로 받아 넣는 방식.\
> 예: 세 절(컨트롤러·서비스·`OrderService`)의 코틀린 코드가 모두 이 모양이고, 원문은 이것이 "주 생성자로 더 간결해진다"고 적는다.

> **보일러플레이트(boilerplate)** — 내용은 거의 같은데 클래스마다 매번 다시 적어야 하는 판박이 코드.\
> 예: 원문이 괄호로 든 "게터/세터/생성자"가 그것이고, 위 자바 엔티티 블록의 `getId()`·`getName()`·`setName(...)`·`getEmail()`이 실제 모습이다.

## 용어 풀이

- **JVM 언어** — 자바 가상 머신 위에서 도는 언어. 소스는 달라도 컴파일 결과가 자바 바이트코드다.
- **바이트코드(bytecode)** — 소스를 JVM이 읽을 수 있는 명령 목록으로 바꿔 둔 것. 코틀린이 자바 자산을 그대로 쓸 수 있는 토대다.
- **상호운용성(interoperability)** — 두 언어가 서로의 것을 그대로 불러 쓸 수 있는 성질. 원문은 코틀린의 첫 매력으로 "자바와의 100% 상호운용성"을 든다.
- **start.spring.io(프로젝트 생성기)** — 언어·의존성을 골라 프로젝트 뼈대를 받아 가는 웹 도구. Spring의 첫 코틀린 발자국이 여기 찍혔다.
- **널 안정성(null-safety)** — `null`이 올 수 있는 자리인지를 **타입으로** 구분해 두는 것. 코틀린에서 `String`과 `String?`이 다른 타입인 것이 그 구분이다.
- **플랫폼 타입(platform type)** — 자바에서 온 타입인데 널 가능성 표시가 없어 코틀린이 판단을 정하지 못한 채 넘겨받은 타입. 원문은 이 상태를 "두루뭉술"이라 부르고, Spring의 `@NonNull`/`@Nullable` 메타데이터 덕분에 Spring API는 이 상태로 넘어오지 않는다고 적는다.
- **확장 함수(extension function)** — 남이 만든 타입에 함수를 덧붙여 원래 그 타입의 메서드였던 것처럼 쓰는 코틀린 문법. 원문 표현으로 "기존 API를 건드리지 않고".
- **reified 타입 파라미터** — 제네릭 타입을 실행 시점까지 남겨 두어 타입을 인자로 따로 넘기지 않아도 되게 하는 문법. 원문 표현으로 "`Class<T>` 인자를 없앤다".
- **DSL(도메인 특화 언어)** — 한 가지 일을 적기 좋게 다듬어 둔 작은 표기법. 원문이 드는 것이 `beans { }`와 `router { }`다.
- **빈 등록 DSL(`beans { }`)** — 함수형으로 빈을 등록하는 코틀린 DSL. 원문은 "리플렉션/CGLIB 없이 명시적으로" 구성할 수 있어 네이티브 이미지와 궁합이 좋다고 적는다.
- **함수형 라우터 DSL(`router { }`)** — 애너테이션 대신 DSL로 라우팅을 선언하는 방식. WebMvc.fn / WebFlux.fn 양쪽에서 쓴다.
- **라우팅(routing)** — 들어온 요청의 경로·메서드를 보고 어느 처리 함수로 보낼지 정하는 일.
- **코루틴(coroutine) / `suspend` 함수** — 도중에 멈췄다가 그 자리에서 다시 이어질 수 있는 함수 / "여기서 멈출 수 있다"는 표시. Spring Framework 5.2부터 컨트롤러·핸들러에서 직접 쓸 수 있다.
- **`Flow`** — 여러 값이 시간을 두고 흘러나오는 코루틴 쪽 타입. 원문 주석이 `Flux<T>`에 대응시킨다.
- **`Mono` / `Flux`** — Reactor 쪽 타입 둘. 원문은 `suspend ↔ Mono`, `Flow ↔ Flux`를 "양방향으로 변환되는 타입 브리지"라 적는다(`awaitSingle()`, `asFlow()`, `asFlux()` 등).
- **`CoroutineCrudRepository`** — 코루틴 기반 Spring Data 리포지토리. 원문은 이것을 `ReactiveCrudRepository`와 "서로 변환되는 관계가 아니라" 코루틴 API를 노출하는 별도 추상화로서 리액티브 인프라 위에서 동작한다고 적는다.
- **점진적 마이그레이션(incremental migration)** — 전부 한 번에 갈아엎지 않고 일부씩 옮겨 가는 방식. 원문 표기로 "자바 → 코틀린 부분 전환".
- **컴파일러 플러그인(compiler plugin)** — 컴파일하는 동안 코드에 손을 대는 부가 도구. `kotlin-spring`(all-open 래퍼)과 `kotlin-jpa`(no-arg 래퍼)가 그것이다.
- **`kotlin-spring`(all-open)** — Spring 스테레오타입 애너테이션이 달린 클래스와 그 멤버를 자동으로 `open` 처리하는 플러그인.
- **`kotlin-jpa`(no-arg)** — `@Entity`/`@Embeddable`/`@MappedSuperclass`에 합성 기본 생성자를 생성하는 플러그인. 인자 없는 생성자만 합성할 뿐 클래스를 `open`으로 만들지는 않는다.
- **`final` / `open`** — 상속·재정의를 막아 둔 상태 / 열어 둔 상태. 코틀린은 클래스와 멤버가 기본적으로 `final`이다.
- **CGLIB 프록시(서브클래싱)** — 원래 클래스를 상속한 대역 클래스를 만들어 그 자리에 끼워 넣는 방식. 원문이 드는 쓰임새가 `@Configuration`·`@Transactional`·AOP다.
- **스테레오타입 애너테이션(stereotype annotation)** — 이 클래스가 어떤 역할의 빈인지 표시하는 애너테이션 묶음. 원문의 기준은 "`@Component` 메타 애너테이션이 붙은 것"이고, `@Entity`는 여기에 들지 않는다.
- **지연 로딩(lazy loading)** — 연관된 데이터를 실제로 쓸 때까지 읽어 오지 않고 미뤄 두는 것. 원문은 괄호로 "프록시 서브클래싱"이라 적는다.
- **역직렬화(deserialization)** — JSON 같은 형식으로 들어온 값을 객체로 되돌려 만드는 일. `jackson-module-kotlin`이 맡는 방향이다.
- **프로퍼티(property)** — 값을 담는 자리와 그 값을 읽고 쓰는 통로를 한 번에 선언하는 코틀린 문법.
- **주 생성자(primary constructor)** — 클래스 이름 바로 옆 괄호에 적는 코틀린 생성자. 원문은 생성자 주입이 이것으로 "더 간결해진다"고 적는다.
- **생성자 주입(constructor injection)** — 필요한 빈을 생성자의 인자로 받아 넣는 방식.
- **보일러플레이트(boilerplate)** — 매번 다시 적어야 하는 판박이 코드. 원문이 괄호로 든 것이 "게터/세터/생성자"다.

## 참고 출처
- [Introducing Kotlin support in Spring Framework 5.0 (spring.io, 2017-01)](https://spring.io/blog/2017/01/04/introducing-kotlin-support-in-spring-framework-5-0/)
- [Spring Framework 5 Kotlin APIs, the functional way (spring.io, 2017-08)](https://spring.io/blog/2017/08/01/spring-framework-5-kotlin-apis-the-functional-way/)
- [Going Reactive with Spring, Coroutines and Kotlin Flow (spring.io, 2019-04)](https://spring.io/blog/2019/04/12/going-reactive-with-spring-coroutines-and-kotlin-flow/)
- [Kotlin support — Spring Framework 5.0 Reference](https://docs.spring.io/spring-framework/docs/5.0.0.RELEASE/spring-framework-reference/kotlin.html)
- [Coroutines :: Spring Framework Reference](https://docs.enterprise.spring.io/spring-framework/reference/languages/kotlin/coroutines.html)
- [All-open compiler plugin (Kotlin docs)](https://kotlinlang.org/docs/all-open-plugin.html)
- [No-arg compiler plugin (Kotlin docs)](https://kotlinlang.org/docs/no-arg-plugin.html)
- [Kotlin — Wikipedia](https://en.wikipedia.org/wiki/Kotlin)
- [Android Announces Support for Kotlin (Android Developers Blog, 2017-05)](https://android-developers.googleblog.com/2017/05/android-announces-support-for-kotlin.html)
- [Spring Boot 2.0 goes GA (spring.io, 2018-03)](https://spring.io/blog/2018/03/01/spring-boot-2-0-goes-ga/)
