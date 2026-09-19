# Spring Boot 4.x (2025 ~)

> 원본: `~/project/java-history/spring/boot-4.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/애너테이션 이름·모듈 및 스타터 이름·수치·코드블록 4개와 원문이 직접 그린 `text` 블록 1개는 원문 그대로다.\
> ASCII 도식 2개(그중 1개는 원문의 mermaid 도식을 옮긴 것), 「한눈에」의 공구 가방 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Spring Framework 7.0 위에 빌드된 새 세대. **모놀리식 자동 설정 jar의 모듈화**, JSpecify 널 안정성, Jackson 3 기본화, HTTP API 버저닝을 받아들였다. Java 17 baseline을 유지하면서 Java 25를 1급 지원한다.

이 편의 첫 축을 비유로 읽으면 **공구를 전부 담은 통 하나를, 필요한 것만 골라 담는 가방으로 바꾼 일**이다.\
통은 해마다 무거워지지만 오늘 쓰는 공구는 그중 몇 개뿐이다.\
**Boot 4.0의 코드베이스 모듈화도 똑같은 구조다** — 원문이 "사용하지 않는 기술의 메타데이터를 싣지 않아"라고 적은 자리다.

본문 흐름에 쓰는 비유는 이 공구 가방 하나뿐이고, 나머지 축(널 안정성·Jackson 3·API 버저닝)은 비유 없이 원문 문장으로 읽는다.

| 비유 | 실체 |
|------|------|
| 공구를 전부 담은 통 하나 | 원문 도식의 "spring-boot-autoconfigure / (모든 기술 자동설정)" — 원문 산문으로는 "비대해진 단일 자동 설정 jar" |
| 필요한 것만 골라 담는 가방 | 원문 "이 단일 자동 설정 jar를 **기술별 작은 모듈들로 분리**(2차 출처 기준 약 47개)하고, 각 모듈이 자체 스타터를 갖는다" |
| 안 쓰는 공구는 아예 안 들고 간다 | 원문 "사용하지 않는 기술의 메타데이터를 싣지 않아 의존성 트리·시작 시간·네이티브 이미지가 개선된다" |

원문이 든 수치를 세로로 놓으면 이렇다.

```text
 spring-boot-autoconfigure — 원문이 적은 크기와 4.0의 답

  1.0 (2014)   182 KiB
     |
  3.5          약 2 MiB
     |
  4.0          기술별 작은 모듈들로 분리 (2차 출처 기준 약 47개) · 각 모듈이 자체 스타터
```

그림 해설 — 위 두 줄은 원문이 적은 크기 그대로이고(`182 KiB`·`약 2 MiB`), 맨 아래 줄은 크기가 아니라 4.0이 택한 방법이다.\
세로선은 시간 순서를 뜻할 뿐이고, 세 줄이 같은 단위로 재어진 것이 아니다.\
"약 47개"라는 수에 원문이 "2차 출처 기준"이라는 단서를 달아 둔 것도 그대로 옮겼다.

## 릴리스 정보
- **최초 출시**: Spring Boot 4.0 GA — 2025년 11월 20일 (후속 4.0.1 — 2025년 12월 18일)
- **기반 Spring Framework 버전**: **7.0**
- **최소 자바 버전**: **Java 17** (호환 유지). 최신 LTS **Java 25를 1급(first-class) 지원**
- **Jakarta EE 기준**: **Jakarta EE 11** (Jakarta Servlet 6.1, Jakarta Persistence 3.2)
- **그 외 baseline**: Kotlin 2.2+, 네이티브 이미지는 GraalVM 25+, 빌드는 **Gradle 9 지원**(Gradle 8.x는 8.14+ 유지)

> **baseline(기준선)** — 이 버전을 쓰려면 최소한 맞춰 두어야 하는 주변 환경의 선.\
> 예: 원문이 이 절에 적은 선들이 Java 17, Jakarta EE 11, Kotlin 2.2+, GraalVM 25+, Gradle 9(또는 8.14+)이다.

> **1급 지원과 최소 버전은 다른 칸이다** — 원문은 최소 자바를 Java 17로 적고 "(호환 유지)"라는 단서를 붙인 뒤, 그와 별개로 "최신 LTS **Java 25를 1급(first-class) 지원**"이라고 적는다.\
> 예: 그래서 Java 17로도 4.0을 쓸 수 있고, Java 25는 그 위에서 따로 1급으로 받아들여진 판이다.

## 시대적 배경 (왜 4.0인가)

Spring Boot 3.x(2022~2025)는 **Jakarta EE 전환(javax→jakarta)·GraalVM 네이티브 이미지·Micrometer 기반 옵저버빌리티**를 골자로 한 세대였다. 4.0은 그 위에서 다음 축으로 넘어간다.

- **코드베이스 모듈화** — 비대해진 단일 자동 설정 jar를 잘게 쪼개 의존성 트리를 슬림화한다.
- **널 안정성 표준화** — Spring Framework 7의 JSpecify를 그대로 받아 포트폴리오 전반에 적용한다.
- **Jackson 3 기본화** — 직렬화 스택의 세대 교체.
- **API 버저닝의 자동 설정 통합** — Framework 7의 버저닝 기능을 프로퍼티로 손쉽게 켠다.
- **최신 플랫폼 정렬** — Jakarta EE 11, Java 25 1급 지원, Gradle 9.

공식 발표 문구대로 "**새로운 Spring Boot 세대의 시작**"이며, Spring Framework 7.0을 토대로 한다.

> **의존성 트리(dependency tree)** — 내가 넣은 의존성이 또 무엇을 끌어오는지를 이어 붙인 가지 모양의 목록.\
> 예: 원문이 첫 축의 목표로 적은 것이 이 가지를 "슬림화한다"이다 — 가지가 적어지면 딸려 오는 것도 줄어든다.

> **직렬화(serialization)** — 객체를 JSON 같은 형식으로 바꿔 내보내고, 반대로 읽어 들이는 일.\
> 예: 원문이 "직렬화 스택의 세대 교체"라 부른 대상이 Jackson이고, 그 자리가 2에서 3으로 바뀐다.

## 핵심 기능

### 코드베이스 모듈화 (모놀리식 자동 설정 jar의 분리)
2014년 1.0에서 182 KiB이던 `spring-boot-autoconfigure` jar는 3.5에서 약 2 MiB까지 비대해졌다. 4.0은 이 단일 자동 설정 jar를 **기술별 작은 모듈들로 분리**(2차 출처 기준 약 47개)하고, 각 모듈이 자체 스타터를 갖는다. 사용하지 않는 기술의 메타데이터를 싣지 않아 의존성 트리·시작 시간·네이티브 이미지가 개선된다.

```text
# Before (Boot 3.x)
spring-boot-autoconfigure  ──  모든 기술의 자동 설정이 한 jar에

# After (Boot 4.x) — 기술별 모듈 + 스타터로 분리
spring-boot-webmvc / spring-boot-webclient / spring-boot-data-jdbc
spring-boot-flyway / spring-boot-mongodb / ...
```

아래는 분리 구조를 단순화한 그림이다. 애플리케이션은 필요한 기술 모듈만 끌어와 의존성을 슬림하게 유지한다.

```text
 Boot 3.x — 모놀리식
 +---------------------------------+
 | spring-boot-autoconfigure       |
 | (모든 기술 자동설정)            |
 +---------------------------------+

 Boot 4.x — 모듈화
 애플리케이션
      |
      +--> spring-boot-webmvc
      |
      +--> spring-boot-data-jdbc
      |
      +--> spring-boot-flyway
```

그림 해설 — 두 제목과 다섯 칸의 문구, 세 화살표는 원문 도식의 것 그대로다.\
원문 도식에서도 위 묶음과 아래 묶음 사이에는 화살표가 없다 — 위가 아래로 변환된다는 뜻의 선은 원문에 없고, 두 시기의 구조를 나란히 둔 것이다.\
아래 묶음에 그려진 모듈이 셋인 것은 원문 도식이 셋만 그렸기 때문이고, 원문은 바로 위 `text` 블록에서 다른 이름들도 `...`과 함께 든다.

점진적 마이그레이션을 위해 **Classic Starter POM**(모듈형 자동 설정을 전이 의존성 없이 묶음)도 제공된다.

> **모놀리식(monolithic)** — 여럿으로 나뉘어 있지 않고 한 덩어리인 상태.\
> 예: 원문 `text` 블록의 `# Before (Boot 3.x)` 줄 아래에 적힌 "모든 기술의 자동 설정이 한 jar에"가 그 덩어리다.

> **메타데이터(metadata)** — 실제 데이터가 아니라 "무엇을 어떻게 다룰지"를 적어 둔 정보. 자동 설정 후보 목록과 조건이 여기에 해당한다.\
> 예: 원문이 개선의 이유로 적은 것이 "사용하지 않는 기술의 메타데이터를 싣지 않아"다.

### HTTP 엔드포인트 API 버저닝 (자동 설정)
Spring Framework 7의 API 버저닝을 Boot가 자동 설정으로 통합한다. `spring.mvc.apiversion.*` / `spring.webflux.apiversion.*` 프로퍼티로 켜고, 고급 설정은 `ApiVersionResolver`·`ApiVersionParser`·`ApiVersionDeprecationHandler` 빈으로 한다.

```properties
spring.mvc.apiversion.use.header=API-Version
```

```java
@RestController
public class AccountController {
    @GetMapping(path = "/account/{id}", version = "1.1")
    public Account getAccount(@PathVariable Long id) { /* ... */ }
}
```

HTTP Interface Client(`@HttpExchange`)도 버전 속성을 지원하며, Boot가 classpath에 따라 RestClient 또는 WebClient 백엔드로 구현체를 자동 생성한다.

```java
@HttpExchange("/accounts")
public interface AccountService {
    @GetExchange(url = "/{id}", version = "1.1")
    Account getAccount(@PathVariable int id);
}
```

> **API 버저닝(API versioning)** — 같은 엔드포인트의 판을 여러 개 두고, 요청이 어느 판을 원하는지 가려 받는 것.\
> 예: 위 프로퍼티가 판 번호를 `API-Version` 헤더에서 읽으라고 정한 줄이고, 위 컨트롤러의 `version = "1.1"`이 그 메서드가 맡는 판이다.

> **HTTP Interface Client(`@HttpExchange`)** — 인터페이스만 선언해 두면 그 인터페이스를 부르는 HTTP 호출 구현을 대신 만들어 주는 방식.\
> 예: 위 인터페이스 `AccountService`에는 본문이 없고, 원문 말대로 Boot가 "classpath에 따라 RestClient 또는 WebClient 백엔드로 구현체를 자동 생성한다".

### JSpecify 널 안정성
포트폴리오 전반이 **JSpecify**(`org.jspecify.annotations`)를 채택하고, Spring 자체 `org.springframework.lang` 애노테이션은 deprecated된다. `package-info.java`에 `@NullMarked`를 선언해 기본 non-null로 두고 null 가능한 곳만 `@Nullable`로 표시한다.

```java
@NullMarked
package com.example.app;

import org.jspecify.annotations.NullMarked;
```

> Kotlin 프로젝트는 기존에 non-null로 가정하던 Spring API가 nullable로 표기되면서 타입 불일치 컴파일 오류가 날 수 있어 주의한다.

바로 위 인용 블록은 원문이 이 절에 직접 달아 둔 주의다 — 원문이 든 원인은 "기존에 non-null로 가정하던 Spring API가 nullable로 표기되면서"이고, 그 결과로 적은 범위는 "타입 불일치 컴파일 오류"까지다.

> **널 안정성 표기(null-safety annotation)** — 이 자리에 `null`이 올 수 있는지 없는지를 API 쪽이 표시로 밝혀 두는 것. 원문이 적은 방식은 "기본 non-null로 두고 null 가능한 곳만 `@Nullable`로 표시"다.\
> 예: 위 코드의 `@NullMarked`가 그 패키지 전체를 기본 non-null로 선언한 줄이다.

> **deprecated(폐기 예정)** — 아직 동작은 하지만 앞으로 없앨 예정이라고 표시해 두는 것.\
> 예: 원문이 이 표시를 붙인 대상이 Spring 자체의 `org.springframework.lang` 애노테이션이다.

### Jackson 3 기본화
**Jackson 3.0이 기본**이 되고, Jackson 2는 `spring-boot-jackson2` 모듈로 deprecated 형태(마이그레이션 유예용)만 제공된다. groupId가 `com.fasterxml.jackson` → **`tools.jackson`**으로 바뀌고, 일부 클래스가 리네임된다(예: `Jackson2ObjectMapperBuilderCustomizer` → `JsonMapperBuilderCustomizer`).

> **groupId** — 메이븐/그레이들 좌표에서 만든 쪽을 가리키는 앞자리.\
> 예: 원문이 적은 변경이 `com.fasterxml.jackson` → `tools.jackson`이다 — 라이브러리를 적어 넣던 좌표의 앞자리가 바뀐다.

## 그 외 변경
- **OpenTelemetry 스타터 신설**: `spring-boot-starter-opentelemetry`로 OTLP를 통해 메트릭·트레이스를 내보낸다.
- **Kotlin 직렬화 지원**: `spring-boot-kotlinx-serialization-json` 모듈 + `spring-boot-starter-kotlin-serialization`.
- **테스트**: `RestTestClient` 지원(`@SpringBootTest`/`@AutoConfigureMockMvc`에서 autowire), 테스트 자동 설정도 모듈별로 분리(`@AutoConfigureDataJdbc` 등이 대응 모듈로 이동).
- **`@ConfigurationProperties`**: 다른 모듈의 타입을 참조할 수 있도록 `@ConfigurationPropertiesSource` 플래그 도입.
- **Redis**: Lettuce 한정 Static Master/Replica 자동 설정.
- **Actuator**: SSL health indicator가 `WILL_EXPIRE_SOON` 상태 대신 `expiringChains` 엔트리를 사용.
- 회복성(@Retryable·@ConcurrencyLimit) 등 Spring Framework 7의 코어 기능을 그대로 활용한다.

> **OTLP(OpenTelemetry Protocol)** — OpenTelemetry가 메트릭·트레이스를 실어 나르는 전송 규약.\
> 예: 원문이 새 스타터 `spring-boot-starter-opentelemetry`의 쓰임을 "OTLP를 통해 메트릭·트레이스를 내보낸다"로 적는다.

> **모듈별 분리가 테스트까지 간다** — 원문은 세 번째 항목에서 테스트 자동 설정도 같은 방식으로 나뉜다고 적는다.\
> 예: 원문이 든 것이 `@AutoConfigureDataJdbc` 등이 "대응 모듈로 이동"한 것이다.

## 마이그레이션 관점 (3.x → 4.0)
- **권장 경로**: 먼저 최신 **3.5.x로 올려 deprecation 경고를 모두 제거한 뒤** 4.0으로. 3.x에서 deprecated였던 클래스/메서드/프로퍼티는 4.0에서 제거된다.
- **Spring Framework 7.x·Jakarta EE 11(Servlet 6.1)** 요구.
- **Jackson 3 전환**: groupId/패키지(`tools.jackson`)와 리네임된 클래스 대응.
- **널 안정성**: `org.springframework.lang` → `org.jspecify.annotations`.
- **스타터/모듈 리네임 대응**: 예) `spring-boot-starter-web` → **`spring-boot-starter-webmvc`**, AOP 스타터 → `spring-boot-starter-aspectj`, `spring-boot-data-mongodb` → `spring-boot-mongodb`. 테스트는 `spring-boot-starter-<tech>-test` 형식. 전이 의존성 부담을 줄이려면 Classic Starter POM 사용 가능.
- **Kotlin 2.2+**, 네이티브는 **GraalVM 25+**.

첫 항목의 순서가 이 절의 요점이다 — 원문은 3.5.x에서 경고를 먼저 지우라고 적고, 그 이유로 "3.x에서 deprecated였던 클래스/메서드/프로퍼티는 4.0에서 제거된다"를 든다.

> **Classic Starter POM** — 원문 표현으로 "모듈형 자동 설정을 전이 의존성 없이 묶음"인 스타터. 원문은 이것을 "점진적 마이그레이션을 위해" 제공된다고 적는다.\
> 예: 원문이 이 절에서 드는 쓰임이 "전이 의존성 부담을 줄이려면 Classic Starter POM 사용 가능"이다.

## 출시 시점 버전 상황
- 2025-11-20 GA 시점에는 **4.0.0 단일**(4.0.x 라인), 이후 **4.0.1이 2025-12-18** 출시.
- **4.1**은 GA 이후 별도 개발 라인(마일스톤)으로 진행된다.

> **마일스톤(milestone)** — 정식 출시 전에 중간중간 내놓는 개발 판.\
> 예: 원문이 4.1을 "GA 이후 별도 개발 라인(마일스톤)으로 진행된다"고 적은 자리다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 네 줄은 원문의 네 불릿 그대로다.)*

- **의존성 다이어트**: 모놀리식 자동 설정을 모듈화해, 마이크로서비스가 미사용 기술 메타데이터를 싣지 않고 더 가벼워진다(시작 시간·네이티브 이미지 개선).
- **표준 수렴**: JSpecify 널 안정성·Jackson 3·Jakarta EE 11로 생태계 표준에 정렬했다.
- **API 진화 대응**: HTTP 엔드포인트 버저닝을 자동 설정으로 손쉽게 켜고, HTTP Interface Client를 1급으로 다룬다.
- 3.x의 클라우드 네이티브 토대 위에서 **모듈화·널 안정성·직렬화 세대 교체**라는 다음 단계로 넘어가는 분수령이다.

첫 불릿이 「한눈에」의 공구 가방이 가리키던 그 축이고, 넷째 불릿이 이 편 전체를 세 낱말로 줄여 놓은 자리다.

## 용어 풀이

- **GA / 4.0.x 라인** — 정식 출시 / 그 뒤로 이어지는 패치 번호대. 4.0 GA는 2025-11-20, 4.0.1은 2025-12-18이다.
- **baseline(기준선)** — 이 버전을 쓰려면 최소한 맞춰 두어야 하는 주변 환경의 선. 4.0은 Java 17, Jakarta EE 11, Kotlin 2.2+, GraalVM 25+, Gradle 9(8.x는 8.14+)이다.
- **1급(first-class) 지원** — 공식 선택지로 받아들이는 것. 원문은 최소 자바 17과 별개로 Java 25를 1급 지원이라 적는다.
- **모놀리식(monolithic)** — 여럿으로 나뉘지 않고 한 덩어리인 상태. 원문이 `spring-boot-autoconfigure`에 붙인 말이다.
- **자동 설정 jar / 기술별 모듈** — 자동 설정이 담겨 있던 한 덩어리 / 4.0이 그것을 쪼갠 단위. 2차 출처 기준 약 47개이고, 각 모듈이 자체 스타터를 갖는다.
- **메타데이터(metadata)** — "무엇을 어떻게 다룰지"를 적어 둔 정보. 안 쓰는 기술의 이것을 싣지 않는 것이 모듈화의 이득으로 적혀 있다.
- **의존성 트리(dependency tree)** — 내가 넣은 의존성이 또 무엇을 끌어오는지를 이어 붙인 가지 모양의 목록.
- **Classic Starter POM** — 모듈형 자동 설정을 전이 의존성 없이 묶은 스타터. 점진적 마이그레이션용이다.
- **API 버저닝(API versioning)** — 같은 엔드포인트의 판을 여러 개 두고 요청이 어느 판을 원하는지 가려 받는 것. 4.0은 `spring.mvc.apiversion.*` / `spring.webflux.apiversion.*`로 켠다.
- **`ApiVersionResolver` / `ApiVersionParser` / `ApiVersionDeprecationHandler`** — 원문이 "고급 설정은 … 빈으로 한다"며 든 세 빈.
- **HTTP Interface Client(`@HttpExchange`)** — 인터페이스 선언만으로 HTTP 호출 구현을 얻는 방식. Boot가 classpath에 따라 RestClient 또는 WebClient 백엔드로 구현체를 만든다.
- **JSpecify** — 4.0이 채택한 널 안정성 애노테이션 표준(`org.jspecify.annotations`).
- **`@NullMarked` / `@Nullable`** — 그 범위를 기본 non-null로 선언하는 표시 / 그중 null이 올 수 있는 자리에 붙이는 표시.
- **deprecated(폐기 예정)** — 아직 동작하지만 앞으로 없앤다고 표시해 두는 것. 3.x에서 이 표시였던 것들이 4.0에서 제거된다.
- **직렬화(serialization) / Jackson** — 객체를 JSON 같은 형식으로 주고받게 바꾸는 일 / 그 일을 맡는 라이브러리. 4.0의 기본은 Jackson 3.0이다.
- **groupId** — 메이븐/그레이들 좌표에서 만든 쪽을 가리키는 앞자리. Jackson의 것이 `com.fasterxml.jackson`에서 `tools.jackson`으로 바뀐다.
- **OpenTelemetry / OTLP** — 메트릭·트레이스의 표준 규격과 도구 모음 / 그것을 실어 나르는 전송 규약. 4.0에 `spring-boot-starter-opentelemetry`가 신설됐다.
- **마일스톤(milestone)** — 정식 출시 전에 내놓는 개발 판. 4.1이 그 라인으로 진행된다.

## 참고 출처
- [Spring Boot 4.0.0 available now (spring.io blog)](https://spring.io/blog/2025/11/20/spring-boot-4-0-0-available-now/)
- [Spring Boot 4.0 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes)
- [Spring Boot 4.0 Migration Guide (GitHub wiki)](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide)
- [Modularizing Spring Boot (spring.io blog)](https://spring.io/blog/2025/10/28/modularizing-spring-boot/)
- [Null-safe applications with Spring Boot 4 (spring.io blog)](https://spring.io/blog/2025/11/12/null-safe-applications-with-spring-boot-4/)
- [API Versioning in Spring (spring.io blog)](https://spring.io/blog/2025/09/16/api-versioning-in-spring/)
- [Spring Boot 4 Modularization — 47 jars (danvega.dev, 2차 출처)](https://www.danvega.dev/blog/spring-boot-4-modularization)
