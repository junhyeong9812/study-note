# Spring Framework 7.x (2025 ~)

> 원본: `~/project/java-history/spring/framework-7.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·패키지/클래스/애노테이션 이름·수치·코드블록 10개(모두 Java)·「릴리스 정보」와 「마이그레이션 관점 (6.x → 7.0)」의 목록·`maxRetries` 참고 인용구는 원문 그대로다.\
> ASCII 도식 1개(원문 mermaid 그림을 글자로 옮긴 것이다), 「한눈에」의 사무실 정비 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 「재서술자 주」 1개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 17 baseline을 유지하면서 **Jakarta EE 11·JSpecify 널 안정성·코어 내장 회복성(resilience)·REST API 버저닝**을 받아들인 새 세대의 시작. Spring Boot 4.0의 토대가 되는 버전이다.

이 편을 하나의 비유로 읽으면 **자리를 옮기는 이사가 아니라 쓰던 사무실을 정비하는 일**이다.\
사내에서만 통하던 양식을 업계 표준 양식으로 바꾸고, 밖에 맡기던 일을 내부 부서로 들이고, 서류마다 판 번호를 달아 옛 판과 새 판이 함께 돌아가게 한다.\
**7.0의 변화도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 6.0을 "토대를 놓은 세대", 7.0을 "그 위에서 생태계 표준에 맞춰 한 단계 더 정렬한 "새 세대의 시작""이라 적는다.

본문 흐름에 쓰는 비유는 이 사무실 정비 하나뿐이고, 그것이 덮는 것은 원문이 「시대적 배경」에 든 네 동인 중 앞의 셋이다.\
넷째(최신 OSS 생태계 정렬)는 비유 없이 원문 문장으로만 읽는다.

| 비유 | 실체 |
|---|---|
| 사내에서만 쓰던 양식을 업계 표준 양식으로 바꾸는 것 | 동인 1 — 원문 표현으로 "Spring 5에서 도입한 독자 애노테이션(`org.springframework.lang`, JSR 305 의미론)을 업계 표준 **JSpecify**로 옮긴다" |
| 밖에 맡기던 일을 내부 부서로 들이는 것 | 동인 2 — 원문 표현으로 "그동안 Spring Retry 등 별도 프로젝트에 있던 재시도·동시성 제한을 `spring-context` 코어로 들였다" |
| 서류마다 판 번호를 달아 옛 판과 새 판을 함께 굴리는 것 | 동인 3 — 원문 표현으로 "엔드포인트 버저닝을 매핑 애노테이션의 정식 속성으로 제공한다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **7.0을 쓰려고 Java 25를 깔아야 하는 것이 아니다.**\
  원문이 「릴리스 정보」에서 직접 부정한 그대로다 — "최신 LTS인 **Java 25를 권장**하며 최적화 — "Java 25 필수"가 아니라 17~25 범위 지원이다."
- **`@Retryable`의 속성 이름은 옛 블로그와 다르다.**\
  원문이 참고 블록에 적어 둔 그대로다 — "RC 이전 초기 블로그는 `maxAttempts`/`execute()` 표기를 썼으나, GA 공식 레퍼런스는 `maxRetries`/`invoke()`가 정본이다."
- **Jackson 3으로 가도 애노테이션 패키지까지 다 바뀌는 것은 아니다.**\
  원문 표현으로 "Jackson 3은 패키지가 `tools.jackson`으로 바뀌었다(애노테이션 클래스 `com.fasterxml.jackson.annotation`은 잔존)".

## 릴리스 정보
- 최초 출시: 7.0 GA — 2025년 11월 13일 (후속 7.0.1 — 2025년 11월 20일)
- 최소 자바 버전(baseline): **Java 17** (baseline 유지). 최신 LTS인 **Java 25를 권장**하며 최적화 — "Java 25 필수"가 아니라 17~25 범위 지원이다.
- Jakarta EE 기준: **Jakarta EE 11** (Jakarta Servlet 6.1, Jakarta Persistence 3.2, Jakarta Bean Validation 3.1, Jakarta WebSocket 2.2)
- 그 외 baseline: **Kotlin 2.2**, **GraalVM 25**, 테스트는 **JUnit 6.0** 기반
- 권장 런타임: Tomcat 11.0+ / Jetty 12.1+, Hibernate ORM 7.1+, Hibernate Validator 9.0+

## 시대적 배경

Spring Framework 6.0(2022)이 `javax.*` → `jakarta.*` 네임스페이스 전환과 AOT/네이티브 이미지의 토대를 놓은 세대였다면, 7.0은 그 위에서 생태계 표준에 맞춰 한 단계 더 정렬한 "새 세대의 시작"이다.\
변화의 동인은 네 가지다.

1. **널 안정성의 생태계 표준 수렴** — Spring 5에서 도입한 독자 애노테이션(`org.springframework.lang`, JSR 305 의미론)을 업계 표준 **JSpecify**로 옮긴다. 타입 사용 위치(제네릭 인자·배열 요소)까지 정밀하게 nullability를 표현하고, Kotlin의 네이티브 널 안정성으로 자동 변환된다.
2. **회복성(resilience)의 코어 내장** — 그동안 Spring Retry 등 별도 프로젝트에 있던 재시도·동시성 제한을 `spring-context` 코어로 들였다.
3. **REST API 버저닝의 1급화** — 엔드포인트 버저닝을 매핑 애노테이션의 정식 속성으로 제공한다.
4. **최신 OSS 생태계 정렬** — Jakarta EE 11, Kotlin 2.2, GraalVM 25, Jackson 3을 끌어안고 Java 25 LTS에 최적화한다.

> **널 안정성(null-safety) / nullability** — 값이 비어 있을 수 있는지를 타입으로 드러내 컴파일러·도구가 잡게 하는 것 / 그 "비어 있을 수 있음" 자체.\
> 예: 원문이 7.0에서 정밀해진 자리로 든 것이 "타입 사용 위치(제네릭 인자·배열 요소)"이고, 그것을 받아 쓰는 쪽으로 든 것이 "Kotlin의 네이티브 널 안정성"이다.

> **회복성(resilience)** — 실패했을 때 그대로 주저앉지 않고 버텨 내는 성질. 원문이 이 이름 아래 묶은 둘이 재시도와 동시성 제한이다.\
> 예: 원문이 그 둘이 "그동안" 있던 자리로 든 것이 "Spring Retry 등 별도 프로젝트"이고, 7.0이 옮겨 온 자리가 `spring-context` 코어다.

릴리스 정렬상 Spring Boot 3.5 / Spring Cloud 2025.0(2025-05)은 여전히 Framework 6.2 기반이고, **Spring Boot 4.0(2025-11)이 Framework 7.0 위에 빌드**된다.

## 핵심 추가/변경 기능

### JSpecify 기반 널 안정성 (org.springframework.lang → org.jspecify)

*(「한눈에」의 "업계 표준 양식"에 해당하는 자리다.)*

Spring 5의 `@Nullable`/`@NonNull`/`@NonNullApi`/`@NonNullFields`(`org.springframework.lang`)가 deprecated되고, 표준 스펙인 **JSpecify**(`org.jspecify.annotations`)로 대체된다.\
`@NullMarked`로 영역 전체 기본값을 non-null로 두고, null이 가능한 곳만 `@Nullable`로 표시한다.

> **deprecated(폐기 예정)** — 아직 동작하지만 앞으로 없앨 것이라고 미리 알려 두는 표시.\
> 예: 원문이 이 표시가 붙었다고 적은 대상이 Spring 5의 `@Nullable`/`@NonNull`/`@NonNullApi`/`@NonNullFields`(`org.springframework.lang`)다.

> **`@NullMarked`** — 그 영역 안의 기본값을 non-null로 정해 두는 표시. 그러면 비어 있을 수 있는 곳만 따로 표시하면 된다.\
> 예: 아래 첫 코드블록처럼 `package-info.java`에 붙여 패키지 전체의 기본을 non-null로 둔다 — 원문 주석이 "패키지 전체 기본을 non-null로"다.

```java
// package-info.java — 패키지 전체 기본을 non-null로
@NullMarked
package com.example.app;

import org.jspecify.annotations.NullMarked;
```

```java
public @Nullable String buildMessage(@Nullable String message,
                                     @Nullable Throwable cause) {
    // ...
}
```

기본이 non-null인 영역이므로, 위 코드에서 따로 표시된 세 자리(반환 타입과 인자 둘)가 "여기는 null일 수 있다"고 적은 곳이다.

JSpecify는 `@Target(TYPE_USE)`라 제네릭 타입 인자·배열 요소·varargs의 nullability까지 정밀하게 지정할 수 있다.

```java
@Nullable Object[] array              // 요소 nullable, 배열 자체는 non-null
Object @Nullable [] array             // 요소 non-null, 배열 자체 nullable
List<@Nullable String> list           // 제네릭 인자의 nullability
```

> **`@Target(TYPE_USE)`** — 타입이 쓰이는 자리마다 붙일 수 있게 한 애노테이션 지정. 클래스·메서드 같은 선언이 아니라 타입 자리에 붙는다.\
> 예: 위 코드의 첫 두 줄은 같은 `Object[] array`인데 `@Nullable`이 붙은 **자리**만 다르고, 원문 주석대로 뜻이 서로 반대다.

### 코어 내장 회복성 — @Retryable · @ConcurrencyLimit

*(「한눈에」의 "내부 부서로 들이는 것"에 해당하는 자리다.)*

재시도와 동시성 제한이 `spring-context`에 내장됐다.\
`@EnableResilientMethods`로 활성화하고, 선언적으로 `@Retryable`·`@ConcurrencyLimit`를, 프로그래밍 방식으로 `RetryTemplate` + `RetryPolicy`를 쓴다.

```java
@Configuration
@EnableResilientMethods
public class ResilienceConfig { }
```

```java
// 선언적 재시도 — 지수 백오프 + jitter
@Retryable(
    includes = MessageDeliveryException.class,
    maxRetries = 4,
    delay = 100,
    jitter = 10,
    multiplier = 2,
    maxDelay = 1000)
public void sendNotification() {
    this.jmsClient.destination("notifications").send(payload);
}
```

> **재시도(retry) / 백오프(backoff)** — 실패한 호출을 다시 해 보는 것 / 다시 해 보기 전에 두는 대기.\
> 예: 원문이 위 코드 주석에 적은 방식이 "지수 백오프 + jitter"이고, 그 대기를 정하는 속성으로 적힌 것이 `delay`·`jitter`·`multiplier`·`maxDelay`다.

```java
// 동시 호출 수 제한 — 가상 스레드 환경에서 특히 유용
@ConcurrencyLimit(10)   // 동시 10개로 제한 (value=1이면 인스턴스 단위 직렬화)
public void heavyTask() { /* ... */ }
```

> **동시성 제한(concurrency limit)** — 같은 메서드를 한꺼번에 몇 개까지 돌릴지 상한을 두는 것.\
> 예: 원문이 위 코드 주석에 적은 그대로다 — `@ConcurrencyLimit(10)`은 "동시 10개로 제한"이고, "value=1이면 인스턴스 단위 직렬화"다.

```java
// 프로그래밍 방식 (GA 레퍼런스 기준 — maxRetries / invoke)
var retryPolicy = RetryPolicy.builder()
    .includes(MessageDeliveryException.class)
    .maxRetries(4)
    .delay(Duration.ofMillis(100))
    .build();

var retryTemplate = new RetryTemplate(retryPolicy);
retryTemplate.invoke(() -> jmsClient.destination("notifications").send(payload));
```

> **선언적 방식 / 프로그래밍 방식** — 애노테이션으로 "이렇게 해 달라"고 적어 두는 쪽 / 코드로 직접 그 객체를 만들어 부르는 쪽.\
> 예: 원문이 이 절 둘째 문장에서 갈라 적은 짝이 그것이다 — 앞쪽이 `@Retryable`·`@ConcurrencyLimit`, 뒤쪽이 `RetryTemplate` + `RetryPolicy`다. 위의 `@Retryable` 블록과 `RetryPolicy` 블록이 같은 `MessageDeliveryException`·`4`회·`100`ms를 두 방식으로 적은 것이다.

**참고**

> 참고: RC 이전 초기 블로그는 `maxAttempts`/`execute()` 표기를 썼으나, GA 공식 레퍼런스는 `maxRetries`/`invoke()`가 정본이다. 기본값은 maxRetries=3(총 4회 시도)·delay 1초.

`Mono`/`Flux` 같은 리액티브 반환 타입은 Reactor의 retry 기능으로 파이프라인이 자동 데코레이트된다.

아래 흐름도는 `@Retryable` 메서드 호출이 `RetryPolicy`에 따라 재시도되는 경로를 보여준다.

```text
@Retryable 메서드 호출                  --> RetryTemplate.invoke()
RetryTemplate.invoke()                 --> 성공?
성공?  [예]                             --> 결과 반환
성공?  [예외 & 시도 < maxRetries]        --> delay·jitter·multiplier 적용 후 대기
delay·jitter·multiplier 적용 후 대기     --> RetryTemplate.invoke()      (여기서 되돌아간다 — 재시도 고리)
성공?  [예외 & 시도 = maxRetries]        --> 마지막 예외 전파
```

- 이 그림은 원문의 mermaid 그림을 글자로 옮긴 것이다 — 화살표 여섯으로 원문과 같고, 줄 순서도 원문이 적은 순서 그대로다.
- 칸 이름과 대괄호 안의 조건은 원문 노드·엣지 라벨 글자 그대로다(`성공?`은 원문이 마름모로 그린 갈림길이고, 대괄호 셋이 그 갈림길에서 나가는 세 갈래다).
- **다섯째 줄이 앞으로 가지 않고 둘째 칸으로 되돌아간다** — 원문에서도 이 엣지만 거꾸로 올라가며, 그래서 이 그림은 일직선이 아니라 고리다.

### REST API 버저닝 (version 속성)

*(「한눈에」의 "판 번호"에 해당하는 자리다.)*

`@RequestMapping` 계열(`@GetMapping` 등)에 `version` 속성이 생겼다.\
버전 해석 전략(헤더·쿼리 파라미터·경로 세그먼트·미디어 타입)은 `ApiVersionConfigurer`로 구성한다.\
Spring MVC와 WebFlux 양쪽을 지원한다.

> **API 버저닝 / 버전 해석 전략** — 같은 엔드포인트의 옛 판과 새 판을 함께 굴리기 위해 요청에 판 번호를 붙이는 것 / 그 판 번호를 요청의 어디서 읽을지 정하는 방식.\
> 예: 원문이 든 전략 넷이 헤더·쿼리 파라미터·경로 세그먼트·미디어 타입이고, 아래 코드는 그중 헤더를 골라 `configurer.useRequestHeader("API-Version")`으로 적는다.

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureApiVersioning(ApiVersionConfigurer configurer) {
        configurer.useRequestHeader("API-Version");
    }
}
```

```java
@RestController
public class AccountController {
    @GetMapping(path = "/account/{id}", version = "1.1")   // 버전별 매핑
    public Account getAccount(@PathVariable Long id) { /* ... */ }
}
```

```java
// 클라이언트 측 — RestClient가 버전 헤더를 자동 삽입
RestClient client = RestClient.builder()
    .baseUrl("http://localhost:8080")
    .apiVersionInserter(ApiVersionInserter.useHeader("API-Version"))
    .build();

Account account = client.get().uri("/accounts/1")
    .apiVersion(1.1)
    .retrieve()
    .body(Account.class);
```

위 세 블록 가운데 첫·셋째 블록이 같은 헤더 이름(`"API-Version"`)을 쓴다 — 서버가 그 헤더에서 읽겠다고 정하고(첫 블록), 클라이언트가 그 헤더를 넣어 보낸다(셋째 블록, 원문 주석대로 "RestClient가 버전 헤더를 자동 삽입").\
둘째 블록은 헤더 이름 없이 `version = "1.1"` 속성으로 핸들러의 판 번호를 달아, 셋째 블록의 `.apiVersion(1.1)`과 짝지어진다.

> **재서술자 주:** 위 둘째 블록의 서버 매핑은 `/account/{id}`인데 셋째 블록의 클라이언트 호출은 `/accounts/1`이다. 같은 절의 두 코드가 한 엔드포인트를 가리키려던 것이고 한쪽이 오기인 것으로 보인다.

요청 버전은 `major.minor.patch` 시맨틱 버전으로 파싱되며, `"1.2+"` 같은 baseline 버전(해당 핸들러가 그 이후 버전까지 커버)도 지원한다.

> **시맨틱 버전(`major.minor.patch`) / baseline 버전** — 세 자리로 끊어 적는 버전 표기 / 그 이후 버전까지 한 핸들러가 받아 주도록 적는 표기.\
> 예: 원문이 든 baseline 표기가 `"1.2+"`이고, 원문이 괄호로 붙인 뜻이 "해당 핸들러가 그 이후 버전까지 커버"다.

### Jackson 3 기본 지원

전체 스택이 **Jackson 3.x**를 기본으로 쓰고 Jackson 2.x로 폴백할 수 있다.\
Jackson 3은 패키지가 `tools.jackson`으로 바뀌었다(애노테이션 클래스 `com.fasterxml.jackson.annotation`은 잔존).\
직렬화 커스터마이저·`ObjectMapper` 설정 코드가 영향을 받는다.

> **폴백(fallback)** — 새것을 쓸 수 없을 때 옛것으로 되돌아가 쓰는 차선책.\
> 예: 원문 표현으로 "전체 스택이 Jackson 3.x를 기본으로 쓰고 Jackson 2.x로 폴백할 수 있다".

## 그 외 변경
- **신규 클라이언트/테스트 지원**: `JmsClient`(JMS 플루언트 API), `RestTestClient`, HTTP Interface Client(`@HttpExchange`) 설정 개선, 프로그래밍 방식 빈 등록(programmatic bean registration).
- **GraalVM 25 / AOT 개선**: 리소스 힌트가 정규식에서 glob 패턴으로 전환됐고, 타입에 reflection 힌트를 등록하면 메서드·생성자·필드 introspection이 자동 함의된다.
- **제거·변경**: `ListenableFuture`·`Theme` 지원·Undertow 전용 클래스 제거, `HttpHeaders`가 더 이상 `MultiValueMap`을 상속하지 않음, SpEL 식에 기본 10,000 연산 한도(DoS 방어) 적용.
- **`javax.annotation`·`javax.inject` 애노테이션 지원 완전 제거** → `jakarta.annotation.*`·`jakarta.inject.*`로 전환 필수(6.x가 남겨둔 잔여 `javax.*`를 마저 정리).

> **glob 패턴** — `*` 같은 기호로 이름의 모양을 적는 간단한 표기. 원문은 리소스 힌트가 "정규식에서 glob 패턴으로 전환됐"다고 적는다.\
> 예: 원문이 이 전환을 든 자리가 「GraalVM 25 / AOT 개선」 불릿이다.

> **DoS 방어** — 한 요청이 자원을 끝없이 먹어 서비스를 마비시키는 일을 막는 장치.\
> 예: 원문이 이 이름을 붙인 장치가 "SpEL 식에 기본 10,000 연산 한도"다.

## 마이그레이션 관점 (6.x → 7.0)
- **Jakarta EE 9/10 → 11**: Servlet 6.1·JPA 3.2·Bean Validation 3.1로 상향, Tomcat 11+·Hibernate ORM 7+·Validator 9+ 등 런타임 의존성 대거 상향.
- **널 안정성 애노테이션 교체**: `org.springframework.lang.*` → `org.jspecify.annotations.*`.
- **Jackson 3 전환**: `tools.jackson` 패키지 변경 대응.
- **잔여 `javax.*` 제거**: `javax.annotation`/`javax.inject` → `jakarta.*`.
- **API 시그니처 변경**: `HttpHeaders`의 `MultiValueMap` 비상속, `ListenableFuture`/`Theme`/Undertow 제거 등.
- 전반 기조는 파괴적 변경보다 **관리된 deprecation을 통한 부드러운 업그레이드 경로**다.

위 다섯 불릿이 바꿔야 할 목록이고, 마지막 한 줄이 원문이 그 목록에 붙인 기조다 — "파괴적 변경보다 관리된 deprecation을 통한 부드러운 업그레이드 경로".

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 네 불릿은 원문의 것이다.)*

- **널 안정성의 표준화**: 독자 애노테이션에서 JSpecify로 수렴하며, Kotlin과의 널 안정성 통합이 한층 매끄러워졌다.
- **회복성의 1급화**: 재시도·동시성 제한을 외부 라이브러리 없이 코어에서 선언적으로 다룰 수 있게 됐다(가상 스레드 환경의 `@ConcurrencyLimit`가 대표적).
- **REST 진화 대응**: API 버저닝이 프레임워크 기능으로 들어오며, 버전 공존·점진적 폐기를 표준 방식으로 다룬다.
- Spring Boot 4.0이 이 위에 빌드되어, 자동 설정·모듈화와 함께 새 세대의 기준선을 형성한다.

## 용어 풀이

- **널 안정성(null-safety) / nullability** — 값이 비어 있을 수 있는지를 타입으로 드러내 컴파일러·도구가 잡게 하는 것 / 그 "비어 있을 수 있음" 자체. 7.0이 정밀해졌다고 적은 자리가 제네릭 인자·배열 요소다.
- **JSpecify** — 원문이 "업계 표준"·"표준 스펙"이라 부르는 널 안정성 애노테이션 규격. 패키지는 `org.jspecify.annotations`다.
- **deprecated(폐기 예정)** — 아직 동작하지만 앞으로 없앨 것이라고 미리 알려 두는 표시. 7.0에서 이 표시가 붙은 것이 `org.springframework.lang`의 옛 애노테이션들이다.
- **`@NullMarked`** — 그 영역 안의 기본값을 non-null로 정해 두는 표시. 그러면 null이 가능한 곳만 `@Nullable`로 표시하면 된다.
- **`@Target(TYPE_USE)`** — 타입이 쓰이는 자리마다 붙일 수 있게 한 애노테이션 지정. 원문은 JSpecify가 이것이라서 "제네릭 타입 인자·배열 요소·varargs의 nullability까지 정밀하게 지정할 수 있다"고 적는다.
- **회복성(resilience)** — 실패했을 때 그대로 주저앉지 않고 버텨 내는 성질. 원문이 이 이름 아래 묶은 둘이 재시도와 동시성 제한이다.
- **재시도(retry) / 백오프(backoff)** — 실패한 호출을 다시 해 보는 것 / 다시 해 보기 전에 두는 대기. 원문이 든 방식이 "지수 백오프 + jitter"이고, 속성은 `delay`·`jitter`·`multiplier`·`maxDelay`다.
- **동시성 제한(concurrency limit)** — 같은 메서드를 한꺼번에 몇 개까지 돌릴지 상한을 두는 것. 원문 주석대로 `value=1`이면 인스턴스 단위 직렬화다.
- **선언적 방식 / 프로그래밍 방식** — 애노테이션으로 적어 두는 쪽 / 코드로 직접 객체를 만들어 부르는 쪽. 앞쪽이 `@Retryable`·`@ConcurrencyLimit`, 뒤쪽이 `RetryTemplate` + `RetryPolicy`다.
- **`maxRetries` / `invoke()`** — GA 공식 레퍼런스가 정본으로 삼는 표기. 원문은 RC 이전 초기 블로그의 `maxAttempts`/`execute()`와 갈라 적고, 기본값을 maxRetries=3(총 4회 시도)·delay 1초로 적는다.
- **API 버저닝 / 버전 해석 전략** — 같은 엔드포인트의 옛 판과 새 판을 함께 굴리기 위해 요청에 판 번호를 붙이는 것 / 그 번호를 요청의 어디서 읽을지 정하는 방식. 원문이 든 전략 넷이 헤더·쿼리 파라미터·경로 세그먼트·미디어 타입이다.
- **시맨틱 버전(`major.minor.patch`) / baseline 버전** — 세 자리로 끊어 적는 버전 표기 / 원문 표현으로 "해당 핸들러가 그 이후 버전까지 커버"하도록 적는 표기(`"1.2+"`).
- **폴백(fallback)** — 새것을 쓸 수 없을 때 옛것으로 되돌아가 쓰는 차선책. 원문은 Jackson 3 기본 + Jackson 2.x 폴백으로 적는다.
- **glob 패턴** — `*` 같은 기호로 이름의 모양을 적는 간단한 표기. 리소스 힌트가 정규식에서 이것으로 전환됐다.
- **DoS 방어** — 한 요청이 자원을 끝없이 먹어 서비스를 마비시키는 일을 막는 장치. 원문이 이 이름을 붙인 것이 SpEL 식의 기본 10,000 연산 한도다.
- **LTS(Long-Term Support)** — 오래 지원해 주기로 정해 둔 버전. 원문이 이 말을 붙인 것이 Java 25이고, baseline은 Java 17 그대로다.

## 참고 출처
- [Spring Framework 7.0 General Availability (spring.io blog)](https://spring.io/blog/2025/11/13/spring-framework-7-0-general-availability/)
- [Spring Framework 7.0 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-7.0-Release-Notes)
- [From Spring Framework 6.2 to 7.0 (spring.io blog)](https://spring.io/blog/2024/10/01/from-spring-framework-6-2-to-7-0/)
- [Core Spring Resilience Features (spring.io blog)](https://spring.io/blog/2025/09/09/core-spring-resilience-features/)
- [Resilience (Spring Framework Reference)](https://docs.spring.io/spring-framework/reference/core/resilience.html)
- [API Versioning in Spring (spring.io blog)](https://spring.io/blog/2025/09/16/api-versioning-in-spring/)
- [Null-safety (Spring Framework Reference)](https://docs.spring.io/spring-framework/reference/core/null-safety.html)
