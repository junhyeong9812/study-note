# Spring Boot 1.x (2014 ~)

> 원본: `~/project/java-history/spring/boot-1.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/애너테이션 이름·코드블록 7개·의존성 좌표는 원문 그대로다.\
> ASCII 도식 5개(그중 2개는 원문의 mermaid 도식을 옮긴 것), 「한눈에」의 신청서 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 설정 지옥에 빠진 Spring을 "관례 우선(convention over configuration)"으로 구출한 최초의 Spring Boot. `java -jar` 한 줄로 웹 애플리케이션이 뜨는 시대를 열었다.

이것을 하나의 비유로 읽으면 **기본값이 미리 적혀 있는 신청서**다.\
빈칸마다 흔히 쓰는 값이 연하게 인쇄돼 있고, 내가 손으로 적은 칸은 그 인쇄된 값을 이긴다.\
그리고 나에게 해당 없는 항목은 애초에 인쇄되지 않는다.\
**Spring Boot의 자동 설정도 똑같은 구조다** — 원문이 핵심 철학 첫 줄에 "합리적인 기본값을 제공하고, 필요할 때만 덮어쓴다"라고 적은 것이 이것이다.

본문 흐름에 쓰는 비유는 이 신청서 하나뿐이다.

| 비유 | 실체 |
|------|------|
| 빈칸에 연하게 인쇄된 기본값 | 자동 설정 — 원문 "합리적인 기본값을 제공하고, 필요할 때만 덮어쓴다" |
| 내가 손으로 적은 칸이 이긴다 | 원문 "자동 설정은 사용자가 직접 정의한 빈이 있으면 물러난다(`@ConditionalOnMissingBean`). 즉, 기본값을 주되 강제하지 않는다" |
| 해당 없는 항목은 인쇄되지 않는다 | 원문 "클래스패스에 있는 라이브러리와 이미 정의된 빈을 감지해 필요한 빈을 **조건부로(`@Conditional`)** 자동 등록한다" |

Boot가 Spring의 어디에 놓이는지부터 그림으로 두면 이렇다.

```text
  Spring Boot   ─  설정을 자동화하는 층
                   (합리적 기본값 · 조건부 등록 · 사용자가 정의한 빈이 이긴다)
  ─────────────────────────────────────────────────────────────
  Spring        ─  그대로 아래에 있다
```

그림 해설 — 두 칸은 위아래로 얹힌 관계이고, 아래 칸이 위 칸으로 바뀐 것이 아니다.\
원문이 시대적 배경 절 마지막에 적은 문장이 이 그림의 근거다 — "Spring Boot는 Spring을 대체하는 것이 아니라, **Spring 위에 얹는 설정 자동화 계층**이다."

## 릴리스 정보
- **최초 출시**: Spring Boot 1.0 GA — 2014년 4월 1일
- **주요 마이너 버전과 시기**:
  - 1.0 (2014-04) — 최초 GA
  - 1.1 (2014-06)
  - 1.2 (2014-12) — `@SpringBootApplication` 단축 애너테이션 도입
  - 1.3 (2015-11) — Developer Tools(devtools), 완전한 캐싱 자동 설정
  - 1.4 (2016-07) — 테스트 슬라이스(`@WebMvcTest`, `@DataJpaTest` 등), `@SpringBootTest` 재정비
  - 1.5 (2017-01) — 1.x 마지막 피처 라인, Actuator/Kafka 등 보강
- **기반 Spring Framework 버전**: Spring Framework 4.x (1.0은 4.0, 1.5는 4.3)
- **최소 자바 버전**: 초기 1.x(1.0~1.2)는 Java 6, 1.3부터는 Java 7이 기본 (Java 6은 추가 설정으로만 호환, 서블릿 3.0+ 컨테이너 필요)

> **GA(General Availability)** — 정식 출시. 실험판·후보판이 아니라 실제 서비스에 써도 된다고 공식적으로 내놓은 판.\
> 예: 원문이 적은 "Spring Boot 1.0 GA — 2014년 4월 1일"이 그 날짜다.

> **베이스라인(baseline, 최소 자바 버전)** — 이 버전을 돌리려면 최소한 이 자바가 있어야 한다는 바닥 선.\
> 예: 원문이 1.3부터의 바닥을 Java 7로 적고, Java 6은 "추가 설정으로만 호환"이라 단서를 붙였다.

## 시대적 배경 (왜 Boot가 등장했나 — Spring의 설정 복잡성 문제)

2000년대 후반~2010년대 초반의 Spring은 강력했지만 시작 비용이 컸다. 전형적인 Spring MVC 프로젝트를 띄우려면:

- `web.xml`에 `DispatcherServlet`, 리스너, 필터를 등록하고
- `applicationContext.xml` / `dispatcher-servlet.xml`에 수십~수백 줄의 빈 정의(데이터소스, 트랜잭션 매니저, 뷰 리졸버, JPA 팩토리 등)를 작성하고
- 의존 라이브러리(Spring, Hibernate, Jackson, 로깅)의 **호환되는 버전 조합**을 손으로 맞추고
- WAR로 패키징해 외부 Tomcat에 배포해야 했다.

> **빈(bean)** — Spring 컨테이너가 대신 만들어 들고 있다가 필요한 곳에 넣어 주는 객체.\
> 예: 위 목록의 "데이터소스, 트랜잭션 매니저, 뷰 리졸버, JPA 팩토리"가 그렇게 등록하던 것들이다.

> **WAR** — 웹 애플리케이션을 담아 서버에 올리는 묶음 파일 형식.\
> 예: 원문 마지막 항목의 "WAR로 패키징해 외부 Tomcat에 배포"가 그 방식이다 — 톰캣이 밖에 따로 설치돼 있고, 거기에 이 묶음을 얹는다.

애너테이션 기반 설정(`@Configuration`, JavaConfig)이 도입되며 XML은 줄었지만, "무엇을 어떻게 설정해야 하는가"라는 본질적 부담은 그대로였다. 같은 시기 Ruby on Rails, Node.js 등은 "최소 설정으로 바로 실행"을 무기로 빠르게 성장하고 있었다.

Spring 진영의 답이 **Spring Boot**였다. 핵심 철학은 두 가지다.

1. **관례 우선(Convention over Configuration)**: 합리적인 기본값을 제공하고, 필요할 때만 덮어쓴다.
2. **독립 실행형(Standalone)**: 서버를 애플리케이션 안에 내장해 `java -jar`로 실행한다.

Spring Boot는 Spring을 대체하는 것이 아니라, **Spring 위에 얹는 설정 자동화 계층**이다.

> **관례 우선(Convention over Configuration)** — 흔히 쓰는 쪽을 기본으로 정해 두고, 그와 다르게 하고 싶을 때만 적게 하는 방식. 원문 표현으로는 "합리적인 기본값을 제공하고, 필요할 때만 덮어쓴다".\
> 예: 원문이 바로 다음 절(자동 설정)에서 적은 "기본값을 주되 강제하지 않는다"가 이 원칙이 실제로 작동하는 모습이다.

## 핵심 기능

### 자동 설정 (Auto-configuration)
클래스패스에 있는 라이브러리와 이미 정의된 빈을 감지해 필요한 빈을 **조건부로(`@Conditional`)** 자동 등록한다. 예를 들어 H2와 Spring JDBC가 클래스패스에 있으면 인메모리 `DataSource`를 자동 구성한다.

```java
@SpringBootApplication // @Configuration + @EnableAutoConfiguration + @ComponentScan (1.2부터)
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
```

자동 설정은 사용자가 직접 정의한 빈이 있으면 물러난다(`@ConditionalOnMissingBean`). 즉, 기본값을 주되 강제하지 않는다.

> **클래스패스(classpath)** — 프로그램이 실행될 때 "여기 있는 클래스들을 쓸 수 있다"고 알려 주는 목록. 어떤 라이브러리를 의존성으로 넣었는지가 여기에 드러난다.\
> 예: 원문이 든 자리가 "H2와 Spring JDBC가 클래스패스에 있으면"이다 — 그 둘을 의존성으로 넣어 두었느냐가 조건이 된다.

> **자동 설정(auto-configuration)** — 클래스패스와 이미 등록된 빈을 보고, **조건이 맞을 때만** 빈을 대신 등록해 주는 것. 조건이 안 맞으면 그 자동 설정은 건너뛰고, 사용자가 같은 빈을 직접 정의했으면 물러난다.\
> 예: 원문의 두 조건이 그대로 예다 — "H2와 Spring JDBC가 클래스패스에 있으면 인메모리 `DataSource`를 자동 구성"하고, 내가 `DataSource`를 직접 정의해 두었으면 `@ConditionalOnMissingBean`에 걸려 자동 설정 쪽이 물러난다.

아래는 "classpath에 있으면 알아서 설정"되는 자동 설정의 동작 흐름이다.

```text
@SpringBootApplication
        |
        v
@EnableAutoConfiguration
        |
        v
spring.factories 로드
(자동 설정 후보 목록)
        |
        v
@Conditional 조건 평가
        |
        v
< classpath에 클래스 존재?
  이미 등록된 빈 없음? >
        |
        +-- 조건 충족 ----> 빈 자동 등록
        |                   (예: DataSource)
        |
        +-- 조건 불충족 --> 해당 자동 설정 건너뜀
```

각 자동 설정 후보는 클래스패스와 기존 빈 상태를 조건으로 평가받고, 충족될 때만 빈을 등록한다.

그림 해설 — 위 네 칸은 원문 도식의 위→아래 순서를 그대로 옮긴 것이고, 마름모 자리의 두 물음과 갈래 라벨(「조건 충족」/「조건 불충족」), 괄호 안의 `(예: DataSource)`도 원문 도식의 문구다.\
갈래가 둘이라는 점이 요점이다 — 자동 설정은 무조건 실행되는 것이 아니라 아래쪽 갈래로 빠질 수 있다.

### 스타터 POM (Starter Dependencies)
서로 호환되는 의존성 묶음을 하나의 좌표로 제공한다. 버전 충돌 지옥에서 해방시킨 핵심 장치다.

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>1.5.22.RELEASE</version>
</parent>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

`spring-boot-starter-web` 하나면 Spring MVC, Jackson, 내장 Tomcat, 검증(validation)이 호환 버전으로 한꺼번에 들어온다.

> **스타터(starter)** — 기능 코드가 들어 있는 라이브러리가 아니라, 원문 표현대로 "서로 호환되는 **의존성 묶음**을 하나의 좌표로" 내놓은 것. 좌표 하나를 적으면 그 묶음이 따라온다.\
> 예: 원문이 든 것이 `spring-boot-starter-web`이고, 그 하나로 "Spring MVC, Jackson, 내장 Tomcat, 검증(validation)이 호환 버전으로 한꺼번에" 들어온다.

> **전이 의존성(transitive dependency)** — 내가 직접 적지 않았는데, 내가 적은 것이 필요로 해서 딸려 들어오는 의존성.\
> 예: 위 XML의 `<dependencies>`에 적힌 것은 `spring-boot-starter-web` 하나인데 Jackson과 내장 Tomcat이 함께 들어오는 것이 그렇게 딸려 온 것이다.

스타터 하나가 끌어오는 전이 의존성 묶음을 그림으로 보면 다음과 같다.

```text
                           +--> spring-webmvc
                           |
                           +--> jackson
                           |    (JSON 직렬화)
 spring-boot-starter-web --+
                           +--> 내장 Tomcat
                           |    (spring-boot-starter-tomcat)
                           |
                           +--> validation
                                (Bean Validation)
```

좌표 하나만 선언하면 호환 버전으로 검증된 라이브러리 묶음이 전이 의존성으로 따라온다.

그림 해설 — 네 화살표는 원문 도식의 네 갈래를 그대로 옮긴 것이고, 괄호 안 문구(`JSON 직렬화`·`spring-boot-starter-tomcat`·`Bean Validation`)도 원문 도식의 라벨이다.\
화살표는 원문이 "스타터 하나가 끌어오는"이라 적은 그 관계다 — 스타터는 원문 표현대로 "의존성 묶음"이라, 오른쪽 넷이 왼쪽 파일 안에 담긴 기능 코드라는 말이 아니다.

### 내장 서블릿 컨테이너 (Embedded Tomcat/Jetty/Undertow)
별도 WAS 설치/배포 없이 컨테이너를 애플리케이션에 내장한다. 결과물은 모든 의존성을 담은 실행 가능한 "fat jar"다.

```bash
mvn package
java -jar target/demo-1.0.0.jar   # 톰캣 내장, 8080 포트로 즉시 기동
```

기본은 Tomcat이며, 스타터 의존성을 교체해 Jetty나 Undertow로 바꿀 수 있다.

무엇이 달라졌는지 두 칸을 나란히 놓으면 이렇다.

```text
 Boot 이전                            Boot 1.x
 (원문 「시대적 배경」 마지막 항목)      (원문 이 절)
 +------------------------------+     +------------------------------+
 | WAR로 패키징                 |     | fat jar                      |
 |                              |     | (모든 의존성을 담은 실행 가능) |
 +------------------------------+     +------------------------------+
 | 외부 Tomcat에 배포           |     | java -jar demo-1.0.0.jar     |
 |                              |     | (컨테이너가 안에 들어 있다)   |
 +------------------------------+     +------------------------------+
```

두 칸을 잇는 원문 문장은 "**별도 WAS 설치/배포 없이** 컨테이너를 애플리케이션에 내장한다"이다.\
같은 행끼리가 짝이다 — 위 행은 결과물의 형태(WAR ↔ fat jar), 아래 행은 그것을 돌리는 방법(외부 Tomcat에 배포 ↔ `java -jar`)이다.\
두 칸이 보여 주는 차이는 **패키징과 실행 방식**이다.

> **서블릿 컨테이너(servlet container) / WAS** — HTTP 요청을 받아 자바 웹 애플리케이션에 넘겨 주는 서버 소프트웨어. Tomcat·Jetty·Undertow가 그것이다.\
> 예: 원문이 "별도 WAS 설치/배포 없이"라고 적은 그 WAS가 이것이고, Boot 1.x는 이것을 애플리케이션 안에 넣는다.

> **fat jar** — 애플리케이션과 그것이 쓰는 모든 의존성을 한 파일에 담은 jar. 원문 표현으로 "모든 의존성을 담은 실행 가능한 fat jar".\
> 예: 위 명령의 `target/demo-1.0.0.jar`가 그것이고, 그래서 `java -jar` 한 줄로 실행된다.

### Actuator (운영 엔드포인트)
프로덕션 운영에 필요한 모니터링/관리 엔드포인트를 자동 제공한다.

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

`/health`, `/metrics`, `/info`, `/env`, `/beans`, `/mappings` 등을 통해 애플리케이션 상태를 들여다볼 수 있다. (1.x의 Actuator는 자체 메트릭 모델을 사용했고, 이는 2.0에서 Micrometer로 전면 교체된다.)

> **엔드포인트(endpoint)** — 바깥에서 접근할 수 있게 열어 둔 주소 하나하나.\
> 예: 원문이 나열한 `/health`, `/metrics`, `/info`, `/env`, `/beans`, `/mappings`가 Actuator가 열어 주는 주소들이다.

> **메트릭(metric)** — 애플리케이션의 상태를 숫자로 잰 값.\
> 예: 원문이 든 `/metrics`가 그 값들을 내보이는 엔드포인트이고, 원문은 1.x의 이 자리를 "자체 메트릭 모델"이라 적으며 "이는 2.0에서 Micrometer로 전면 교체된다"고 덧붙인다.

### 외부 설정 (Externalized Configuration)
`application.properties` 또는 `application.yml`로 환경별 설정을 코드 밖으로 분리한다. 우선순위(명령행 인자 > 환경변수 > 프로파일별 파일 > 기본 파일)가 정의되어 있다.

```yaml
server:
  port: 8081
spring:
  datasource:
    url: jdbc:mysql://localhost/app
    username: app
  profiles:
    active: dev
```

`@ConfigurationProperties`로 타입 안전한 바인딩도 가능하다.

원문이 괄호 안에 `>`로 적은 우선순위를 세로로 내려쓰면 이렇다.

```text
 센 쪽   명령행 인자
   |     환경변수
   |     프로파일별 파일
 약한 쪽 기본 파일
```

그림 해설 — 네 줄은 원문 괄호 안의 순서와 문구 그대로다.\
원문이 이 순서를 "우선순위"라고 부르므로, 같은 설정 항목이 두 곳에 적혀 있으면 위쪽에서 읽은 값이 쓰인다.

> **외부 설정(externalized configuration)** — 환경마다 달라지는 값을 코드 안에 박지 않고 코드 밖 파일·환경변수로 빼 두는 것.\
> 예: 위 YAML의 `server.port: 8081`이나 `spring.datasource.url`처럼, 개발·운영에서 달라지는 값이 `application.yml`에 들어가 있다.

> **프로파일(profile)** — 환경 이름을 붙여 설정 묶음을 갈아 끼우는 장치.\
> 예: 위 YAML의 `spring.profiles.active: dev`가 그 이름을 `dev`로 고른 자리이고, 우선순위 그림의 "프로파일별 파일"이 그 이름에 맞춰 읽히는 파일이다.

> **`@ConfigurationProperties`** — 설정 파일의 값들을 자바 객체의 필드로 묶어 받는 애너테이션. 원문은 이것을 "타입 안전한 바인딩"이라 부른다.\
> 예: 위 YAML의 `spring.datasource.url`·`username` 같은 값을 낱개로 꺼내 쓰는 대신 한 객체의 필드로 받아 두는 방식이다. 원문이 이 절에서 드는 것은 이름까지이고, 실제로 붙은 클래스의 모습은 2.x 편의 `AppProperties`가 보여 준다.

### Spring Boot CLI
Groovy 스크립트로 프로토타입을 즉석 실행하는 명령행 도구.

```groovy
// app.groovy
@RestController
class Hello {
    @RequestMapping("/")
    String home() { "Hello World!" }
}
```
```bash
spring run app.groovy
```

> **CLI(Command Line Interface)** — 명령어를 쳐서 쓰는 도구.\
> 예: 위 `spring run app.groovy` 한 줄이 그 도구를 부르는 명령이다.

## 마이너 버전별 변화
- **1.0 (2014)**: 자동 설정, 스타터, 내장 컨테이너, Actuator, CLI 등 핵심 골격 완성.
- **1.2 (2014-12)**: `@SpringBootApplication` 도입(`@Configuration`+`@EnableAutoConfiguration`+`@ComponentScan` 결합), 서블릿 3.1/JTA 지원, 배너 커스터마이징.
- **1.3 (2015)**: `spring-boot-devtools`(자동 재시작/라이브 리로드), 완전한 캐시 자동 설정, fully executable jar.
- **1.4 (2016)**: 테스트 개편 — `@SpringBootTest`, `@WebMvcTest`/`@DataJpaTest` 등 슬라이스 테스트, `@MockBean`. 커스텀 자동 설정 작성 개선.
- **1.5 (2017)**: 1.x의 마지막 라인. Actuator 보안 개선, Kafka 지원, LDAP 자동 설정. 이후 개발 흐름은 2.0으로 이동.

> **슬라이스 테스트(test slice)** — 애플리케이션 전체를 띄우지 않고 한 겹만 띄워 보는 테스트.\
> 예: 원문이 든 `@WebMvcTest`·`@DataJpaTest`가 그 겹을 고르는 애너테이션이고, 원문은 이것을 "테스트 슬라이스"라 부르며 1.4에 넣었다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 줄은 원문의 세 불릿 그대로다.)*

- Spring Boot는 Java 백엔드 개발의 **사실상 표준 시작점**이 되었다. "Spring으로 개발한다"는 말이 곧 "Spring Boot로 개발한다"를 의미하게 만든 출발점이다.
- `web.xml`과 거대한 XML 설정, 외부 WAS 배포라는 무거운 관행을 걷어내고, **마이크로서비스 시대에 맞는 독립 실행형 jar** 패러다임을 정착시켰다.
- 스타터 + 자동 설정 모델은 이후 수많은 프레임워크가 모방한 설계가 되었으며, Spring Cloud 등 상위 생태계의 토대가 되었다.

둘째 불릿이 걷어냈다고 적은 셋은 이 문서 「시대적 배경」 목록의 첫·둘째·넷째 항목과 같은 것들이다.

## 용어 풀이

- **GA(General Availability)** — 정식 출시. 실험판·후보판이 아니라 실제 서비스에 써도 된다고 공식적으로 내놓은 판.
- **베이스라인(최소 자바 버전)** — 이 버전을 돌리려면 최소한 있어야 하는 자바의 바닥 선. 1.x는 초기(1.0~1.2)가 Java 6, 1.3부터 Java 7이 기본이다.
- **빈(bean)** — Spring 컨테이너가 대신 만들어 들고 있다가 필요한 곳에 넣어 주는 객체.
- **WAR** — 웹 애플리케이션을 담아 서버에 올리는 묶음 파일 형식. 원문 「시대적 배경」이 전형적인 Spring MVC 프로젝트의 Boot 이전 관행으로 든 배포 형식이다("WAR로 패키징해 외부 Tomcat에 배포해야 했다").
- **관례 우선(Convention over Configuration)** — 합리적인 기본값을 제공하고, 필요할 때만 덮어쓰는 방식. 원문이 든 Boot의 첫째 철학이다.
- **독립 실행형(Standalone)** — 서버를 애플리케이션 안에 내장해 `java -jar`로 실행하는 것. 원문이 든 Boot의 둘째 철학이다.
- **클래스패스(classpath)** — 실행 시 쓸 수 있는 클래스들의 목록. 어떤 라이브러리를 의존성으로 넣었는지가 여기에 드러난다.
- **자동 설정(auto-configuration)** — 클래스패스와 이미 등록된 빈을 보고 **조건이 맞을 때만** 빈을 대신 등록해 주는 것. 조건이 안 맞으면 건너뛰고, 사용자가 직접 정의한 빈이 있으면 물러난다.
- **`@Conditional` / `@ConditionalOnMissingBean`** — 자동 설정이 조건부로 동작하게 하는 애너테이션 / 그중 "같은 빈이 아직 없을 때만"이라는 조건.
- **스타터(starter)** — 기능 코드가 든 라이브러리가 아니라, 서로 호환되는 **의존성 묶음**을 하나의 좌표로 내놓은 것.
- **전이 의존성(transitive dependency)** — 내가 직접 적지 않았는데 내가 적은 것이 필요로 해서 딸려 들어오는 의존성.
- **서블릿 컨테이너 / WAS** — HTTP 요청을 받아 자바 웹 애플리케이션에 넘겨 주는 서버 소프트웨어. Tomcat·Jetty·Undertow.
- **fat jar** — 애플리케이션과 모든 의존성을 한 파일에 담은, 실행 가능한 jar.
- **Actuator** — 프로덕션 운영에 필요한 모니터링/관리 엔드포인트를 자동 제공하는 모듈. `spring-boot-starter-actuator`는 그 모듈을 끌어오는 스타터다.
- **엔드포인트(endpoint)** — 바깥에서 접근할 수 있게 열어 둔 주소 하나하나. `/health`·`/metrics` 등.
- **메트릭(metric)** — 애플리케이션의 상태를 숫자로 잰 값. 1.x의 Actuator는 자체 메트릭 모델을 썼다.
- **외부 설정(externalized configuration)** — 환경마다 달라지는 값을 코드 밖 파일·환경변수로 빼 두는 것.
- **프로파일(profile)** — 환경 이름을 붙여 설정 묶음을 갈아 끼우는 장치. `spring.profiles.active`로 고른다.
- **`@ConfigurationProperties`** — 설정 파일의 값들을 자바 객체의 필드로 묶어 받는 애너테이션. 원문 표현으로 "타입 안전한 바인딩".
- **devtools(`spring-boot-devtools`)** — 1.3에 들어온 개발용 도구. 자동 재시작/라이브 리로드를 해 준다.
- **슬라이스 테스트(test slice)** — 애플리케이션 전체를 띄우지 않고 한 겹만 띄워 보는 테스트. 1.4의 `@WebMvcTest`·`@DataJpaTest`.
- **CLI(Command Line Interface)** — 명령어를 쳐서 쓰는 도구. Boot의 것은 Groovy 스크립트를 즉석 실행한다.

## 참고 출처
- [Spring Boot 1.0 GA Released (spring.io blog)](https://spring.io/blog/2014/04/01/spring-boot-1-0-ga-released/)
- [Spring Boot 1.4 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-1.4-Release-Notes)
- [Spring Boot version history (codejava.net)](https://www.codejava.net/frameworks/spring-boot/spring-boot-version-history)
- [Creating Your Own Auto-configuration (Spring docs)](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html)
- [Spring Boot 1.0 — VersionLog](https://versionlog.com/spring-boot/1.0/)
