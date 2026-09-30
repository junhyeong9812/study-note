# Spring Framework 3.x (2009 ~)

> 원본: `~/project/java-history/spring/framework-3.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/어노테이션 이름·JSR 번호·코드블록 8개(XML 1 · Java 7)·「릴리스 정보」와 「마이너 버전별 변화」의 목록은 원문 그대로다.\
> ASCII 도식 1개(원문 mermaid 시퀀스 그림을 글자로 옮긴 것이다), 「한눈에」의 노트·부록 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 「재서술자 주」 1개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> XML 없이 자바 코드(`@Configuration`/`@Bean`)만으로 컨테이너를 구성할 수 있게 된 시대. SpEL, REST, 환경/프로파일 추상화까지 더해 현대 Spring의 골격이 완성됐다.

이 편을 하나의 비유로 읽으면 **본문과 따로 묶여 있던 부록에만 적을 수 있던 항목을, 본문에 같은 언어로 적을 수 있게 된 일**이다.\
2.5에서 이미 "내가 쓴 문단"은 본문에 적을 수 있었지만, 남이 만들어 준 항목은 여전히 부록에만 적혔다.\
**3.0의 Java Config도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 그 빈틈을 이렇게 적는다: "서드파티 객체처럼 어노테이션을 붙일 수 없는 빈을 자바 코드만으로 "정의"하는 수단(`@Configuration`/`@Bean`)은 아직 없어, 이런 빈은 여전히 XML `<bean>`의 몫이었다."

본문 흐름에 쓰는 비유는 이 노트 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 본문과 따로 묶여 있는 부록 | XML `<bean>` 정의 |
| 내가 쓴 문단에 직접 표시해 두는 것 | 2.5의 컴포넌트 스캔과 스테레오타입(`@Component` 등) — 원문 표현으로 "내가 작성한 빈은 XML 없이 등록" |
| 남이 만들어 줘서 표시를 새길 수 없는 항목 | 원문 표현으로 "서드파티 객체처럼 어노테이션을 붙일 수 없는 빈" |
| 그 항목까지 본문에 같은 언어로 적게 된 것 | 3.0의 `@Configuration`/`@Bean` — 원문 표현으로 "XML 한 줄 없이 자바 클래스로 컨테이너를 구성" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **`@Component` 계열과 `@Bean`은 하는 자리가 다르다.**\
  원문이 「시대적 배경」에서 나눠 적은 그대로다 — `@Component` 계열은 **내가 작성한 빈**을 스캔으로 등록하는 쪽이고, `@Configuration`/`@Bean`은 **어노테이션을 붙일 수 없는 빈까지 자바 코드로 "정의**"하는 쪽이다.
- **Java Config가 XML을 폐기한 것이 아니다.**\
  원문은 「설정 스타일의 변화」에서 이 시대에 "**세 가지 설정 스타일이 모두 완성**되어 공존하게 됐다"고 적고, 그 셋을 XML · 어노테이션+컴포넌트 스캔 · Java Config로 든다.
- **3.1의 `@Profile`은 아무 데나 붙지 않는다.**\
  원문이 코드 주석에 직접 적어 둔 그대로다 — "3.1의 @Profile은 @Target(TYPE) — 클래스(설정) 단위로만 붙일 수 있다. (@Bean 메서드 단위 @Profile은 Spring 4.0부터 가능)".

## 릴리스 정보
- 최초 출시: 3.0 — 2009년 12월
- 주요 마이너 버전과 시기: 3.0(2009-12) → 3.1(2011-12) → 3.2(2012-12)
- 최소 자바 버전(baseline): Java 5 이상 (Spring 최초로 Java 5를 정식 요구, 제네릭·어노테이션 전면 활용)
- Java EE / Jakarta EE 기준: J2EE 1.4 / Java EE 5와 호환(일부 Java EE 6 기능 지원). 서블릿 컨테이너도 Tomcat 5.0 / Jetty 5.1 등 구버전과 호환.

## 시대적 배경

2.5의 컴포넌트 스캔과 스테레오타입(`@Component` 등)으로 **내가 작성한 빈은 XML 없이 등록**할 수 있게 됐다.\
다만 서드파티 객체처럼 어노테이션을 붙일 수 없는 빈을 자바 코드만으로 "정의"하는 수단(`@Configuration`/`@Bean`)은 아직 없어, 이런 빈은 여전히 XML `<bean>`의 몫이었다.\
한편 자바 진영에는 Guice(Google) 같은 순수 코드 기반 DI 컨테이너가 등장해 "타입 안전한 자바 설정"의 매력을 보여줬다.\
Java 5가 충분히 보급된 2009년, Spring 3.0은 코드베이스를 Java 5 기준으로 재정비하고 **JavaConfig**를 코어에 정식 편입했다.\
이로써 "XML이냐 어노테이션이냐 자바냐"라는 세 가지 설정 스타일이 모두 갖춰졌다.

> **서드파티(third-party) 객체** — 내가 만든 것이 아니라 남이 만들어 배포한 라이브러리의 클래스. 소스가 내 손에 없으니 거기에 어노테이션을 새겨 넣을 수 없다.\
> 예: 원문이 이 자리에서 든 조건이 "어노테이션을 붙일 수 없는 빈"이고, 3.0 이전에는 이런 빈이 "여전히 XML `<bean>`의 몫이었다".

> **타입 안전(type-safe)** — 잘못 이어 붙인 것을 실행 전에 컴파일러·도구가 잡아 줄 수 있는 상태. 원문은 Guice가 보여 준 매력을 "타입 안전한 자바 설정"이라 적는다.\
> 예: 원문이 아래 Java Config 코드블록 주석에 직접 적어 둔 말이 "타입 안전, 리팩토링 친화적"이다.

## 핵심 추가/변경 기능

### Java 기반 설정 (@Configuration / @Bean) — 3.x의 핵심

*(「한눈에」의 "본문에 같은 언어로 적게 된 것"에 해당하는 자리다.)*

별도 프로젝트였던 JavaConfig가 코어로 들어오며, XML 한 줄 없이 자바 클래스로 컨테이너를 구성할 수 있게 됐다.

XML 방식 vs Java Config 방식 비교:

```xml
<!-- 기존 XML -->
<bean id="dataSource" class="...BasicDataSource" destroy-method="close">
    <property name="url"      value="jdbc:mysql://localhost/test"/>
    <property name="username" value="root"/>
</bean>
<bean id="accountService" class="com.example.AccountServiceImpl">
    <constructor-arg ref="accountDao"/>
</bean>
```

```java
// Spring 3.0 Java Config — 타입 안전, 리팩토링 친화적
@Configuration
public class AppConfig {

    @Bean(destroyMethod = "close")
    public DataSource dataSource() {
        BasicDataSource ds = new BasicDataSource();
        ds.setUrl("jdbc:mysql://localhost/test");
        ds.setUsername("root");
        return ds;
    }

    @Bean
    public AccountDao accountDao() {
        return new JdbcAccountDao(dataSource());
    }

    @Bean
    public AccountService accountService() {
        return new AccountServiceImpl(accountDao());
    }
}
```

두 블록은 같은 구성을 두 언어로 적은 것이다(XML 쪽은 `accountDao`를 `ref`로만 가리킨다).\
위 XML에서 `<bean id="dataSource" …>`였던 것이 아래에서는 `dataSource()`라는 메서드가 되고, `<constructor-arg ref="accountDao"/>`였던 것이 `new AccountServiceImpl(accountDao())`라는 자바 호출이 된다.

> **`@Configuration`** — "이 클래스는 빈을 정의하는 곳이다"를 표시하는 어노테이션.\
> 예: 위 코드의 `AppConfig`가 그것이고, 원문은 이런 클래스로 "XML 한 줄 없이 자바 클래스로 컨테이너를 구성할 수 있게 됐다"고 적는다.

> **`@Bean`** — 그 메서드가 반환하는 객체를 빈으로 등록하라는 표시. 메서드 몸통은 내가 직접 쓴 자바 코드라, 남이 만든 클래스도 여기서 만들어 넘길 수 있다.\
> 예: 위 코드의 `dataSource()`가 `BasicDataSource`(원문이 XML 쪽에서 `...BasicDataSource`로 적은 그 클래스)를 만들어 반환한다.

```java
// 부트스트랩: XML이 아니라 클래스를 넘긴다
ApplicationContext ctx =
    new AnnotationConfigApplicationContext(AppConfig.class);
AccountService service = ctx.getBean(AccountService.class);
```

원문이 위 코드 첫 줄 주석에 적어 둔 것이 이 절의 요약이다 — "부트스트랩: XML이 아니라 클래스를 넘긴다".

### SpEL (Spring Expression Language)

빈 정의·어노테이션 안에서 런타임 표현식을 평가하는 통합 표현 언어.\
프로퍼티 조회, 메서드 호출, 컬렉션 조작 등이 가능하다.

> **SpEL(Spring Expression Language)** — 설정 자리에 값 대신 적어 두면 **실행 시점에** 계산되어 그 자리를 채우는 식.\
> 예: 아래 `@Value("#{systemProperties['user.region'] ?: 'KR'}")`가 시스템 프로퍼티를 조회하는 식이다 — 원문이 이 절에서 "가능하다"고 든 쓰임 가운데 "프로퍼티 조회"에 해당한다(`?:` 연산자의 뜻은 원문에 없다).

```java
@Value("#{systemProperties['user.region'] ?: 'KR'}")
private String region;

@Value("#{ T(java.lang.Math).random() * 100 }")
private double seed;
```

### Spring MVC의 REST 지원

RESTful 웹 서비스를 1급으로 지원.\
`@PathVariable`, 콘텐츠 협상, `@ResponseBody`/`HttpMessageConverter`(JSON/XML 자동 변환), `RestTemplate`(클라이언트) 등이 추가됐다.

> **`@PathVariable`** — URL 경로의 한 토막을 그대로 메서드 인자로 받아 오는 표시.\
> 예: 아래 코드의 `value = "/{id}"`의 `{id}`가 `@PathVariable("id") long id`로 들어온다.

> **`@ResponseBody` / `HttpMessageConverter`** — 반환값을 화면이 아니라 응답 본문으로 보내라는 표시 / 그 반환 객체를 JSON·XML로 바꿔 주는 변환기.\
> 예: 아래 코드의 `@ResponseBody`가 붙은 `get` 메서드에 원문이 단 주석이 "JSON으로 직렬화되어 응답"이다.

```java
@Controller
@RequestMapping("/accounts")
public class AccountRestController {

    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    @ResponseBody
    public Account get(@PathVariable("id") long id) {
        return accountService.find(id);   // JSON으로 직렬화되어 응답
    }
}
```

아래는 `DispatcherServlet`을 단일 진입점(Front Controller)으로 하는 Spring MVC 요청 처리 흐름이다.\
디스패처가 HandlerMapping으로 핸들러를 찾고, **HandlerAdapter**를 통해 컨트롤러를 호출한다.\
반환값이 뷰 기반(`ModelAndView`)이면 ViewResolver/View로 렌더링하고, REST(`@ResponseBody`/`@RestController`)면 ViewResolver를 거치지 않고 HttpMessageConverter가 본문을 직렬화한다.

```text
Client                        --> DispatcherServlet          HTTP 요청
DispatcherServlet             --> HandlerMapping             핸들러 조회
HandlerMapping                --> DispatcherServlet          핸들러(Controller) 반환
DispatcherServlet             --> HandlerAdapter             핸들러 실행 위임
HandlerAdapter                --> Controller (@RequestMapping)   컨트롤러 메서드 호출

  [갈래 1] 뷰 기반 (ModelAndView 반환)
    Controller (@RequestMapping) --> HandlerAdapter        ModelAndView (뷰 이름 + 모델)
    HandlerAdapter               --> DispatcherServlet     ModelAndView
    DispatcherServlet            --> ViewResolver          뷰 이름 해석
    ViewResolver                 --> DispatcherServlet     View 반환
    DispatcherServlet            --> View                  모델로 렌더링
    View                         --> DispatcherServlet     렌더링 결과

  [갈래 2] REST (@ResponseBody / @RestController)
    Controller (@RequestMapping) --> HandlerAdapter        객체 반환
    HandlerAdapter               --> HttpMessageConverter  객체 → JSON 직렬화 (ViewResolver 생략)
    HttpMessageConverter         --> HandlerAdapter        응답 본문
    HandlerAdapter               --> DispatcherServlet     완료

DispatcherServlet             --> Client                     HTTP 응답
```

- 이 그림은 원문의 mermaid 시퀀스 그림을 글자로 옮긴 것이다 — 화살표 열여섯으로 원문의 메시지 수와 같고, 순서와 방향도 원문과 같다.
- 왼쪽·가운데의 이름은 원문이 participant로 선언한 이름 그대로이고, 오른쪽에 적은 말은 원문이 그 화살표에 붙인 메시지 글자 그대로다(갈래 2 둘째 줄의 라벨 안에 있는 `→`도 원문 라벨의 글자다).
- 두 갈래는 원문이 `alt` / `else`로 나눠 둔 것이다 — 둘 중 하나만 일어난다.
- 바로 위 문단이 이 그림을 읽는 법이다 — 특히 "REST … 면 ViewResolver를 거치지 않고"가 갈래 2에 ViewResolver와 View가 없는 이유다.

> **재서술자 주:** 위 문단과 그림의 갈래 2에 나오는 `@RestController`는 같은 시리즈 `framework-4.x.md`가 4.0 도입으로 적는 어노테이션이다. 이 편의 코드 블록이 쓰는 것은 `@Controller` + `@ResponseBody`이고, `@RestController`는 여기서 REST 갈래를 설명하기 위해 함께 적힌 것으로 보인다.

> **`DispatcherServlet`(프런트 컨트롤러)** — 들어오는 요청을 한 군데서 먼저 받아 알맞은 처리기로 넘기는 입구. 원문은 이것을 "단일 진입점(Front Controller)"이라 부른다.\
> 예: 위 그림에서 첫 화살표와 마지막 화살표가 모두 이 칸에 닿는다.

> **`HandlerMapping` / `HandlerAdapter`** — 어느 핸들러가 이 요청을 맡는지 찾아 주는 쪽 / 그 핸들러를 실제로 실행해 주는 쪽.\
> 예: 위 그림의 둘째·셋째 화살표가 찾는 일이고, 넷째·다섯째 화살표가 실행을 위임하고 호출하는 일이다.

> **`ModelAndView`** — 뷰 이름과 화면에 넘길 데이터(모델)를 함께 담은 반환값.\
> 예: 위 그림 갈래 1의 첫 화살표 라벨이 "ModelAndView (뷰 이름 + 모델)"이다.

> **`ViewResolver` / `View`** — 뷰 이름을 실제 화면 객체로 풀어 주는 쪽 / 모델을 받아 화면을 그려 내는 쪽.\
> 예: 위 그림 갈래 1에서 "뷰 이름 해석" → "View 반환" → "모델로 렌더링" 순으로 이어지는 세 화살표가 그 일이다.

### 선언적 비동기 / 스케줄링 (@Async, @Scheduled)

`@Async`로 메서드를 비동기 실행, `@Scheduled`로 주기 작업을 어노테이션만으로 등록.

> **`@Async`** — 이 메서드는 부른 자리에서 끝날 때까지 붙들지 말고 따로 실행하라는 표시.\
> 예: 아래 `generate()`에 원문이 단 주석이 "별도 스레드 실행"이고, 그 반환 타입이 `Future<Report>`다.

> **`@Scheduled` / cron 식** — 정해진 주기에 스스로 실행되게 하는 표시 / 그 주기를 적는 문법.\
> 예: 아래 `@Scheduled(cron = "0 0 * * * *")`에 원문이 단 주석이 "매시 정각"이다.

```java
@Configuration
@EnableAsync
@EnableScheduling
public class TaskConfig { }

@Service
public class ReportService {

    @Async
    public Future<Report> generate() { /* 별도 스레드 실행 */ }

    @Scheduled(cron = "0 0 * * * *")
    public void hourlyCleanup() { /* 매시 정각 */ }
}
```

위 코드의 `TaskConfig`에 붙은 `@EnableAsync`·`@EnableScheduling`이 아래 「c: 네임스페이스, @EnableXxx 모듈 활성화」 절이 말하는 `@Enable*` 스타일의 실물이다 — 원문은 이 스타일을 "모듈 활성화 어노테이션"이라 부르고, 캐시 절의 같은 자리에는 "`@EnableCaching` 으로 활성화"라는 주석을 달아 둔다.

### 환경 추상화 / 프로파일 (@Profile) — 3.1

`Environment` 추상화와 `@Profile`로 개발/운영 등 환경별 빈 구성을 분리.\
프로퍼티 소스도 통합 관리(`@PropertySource`).

> **프로파일(profile)** — "개발용"·"운영용"처럼 환경에 이름을 붙여 두고, 그 이름이 켜졌을 때만 쓰이는 구성을 갈라 두는 장치.\
> 예: 아래 코드의 `@Profile("dev")`와 `@Profile("prod")`가 같은 `dataSource` 빈을 환경별로 갈라 놓는다.

```java
// 3.1의 @Profile은 @Target(TYPE) — 클래스(설정) 단위로만 붙일 수 있다.
// (@Bean 메서드 단위 @Profile은 Spring 4.0부터 가능)
@Configuration
@Profile("dev")
public class DevDataSourceConfig {

    @Bean
    public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().build();   // H2 등 임베디드
    }
}

@Configuration
@Profile("prod")
public class ProdDataSourceConfig {

    @Bean
    public DataSource dataSource() {
        return jndiDataSource();                          // 운영 DB
    }
}
```

**언제 쓸 수 있게 됐나** — 원문이 위 코드 첫 두 줄 주석에 적어 둔 그대로다: 3.1의 `@Profile`은 클래스(설정) 단위로만, `@Bean` 메서드 단위는 Spring 4.0부터.

### 캐시 추상화 (@Cacheable) — 3.1

백엔드(EhCache, ConcurrentMap 등)와 무관한 선언적 캐싱.

> **캐시 추상화** — 어느 캐시 제품을 쓰든 같은 어노테이션으로 캐싱을 선언하게 해 주는 층. 원문 표현으로 "백엔드 … 와 무관한 선언적 캐싱"이다.\
> 예: 원문이 백엔드로 든 것이 EhCache와 ConcurrentMap인데, 아래 코드에는 그 이름이 나오지 않는다 — 캐싱을 선언한 것은 `@Cacheable("books")` 한 줄이다.

```java
@Service
public class BookService {
    @Cacheable("books")
    public Book findIsbn(String isbn) { /* 느린 조회 */ }
}
// @EnableCaching 으로 활성화
```

### c: 네임스페이스, @EnableXxx 모듈 활성화
- 3.1: 생성자 인자용 `c:` XML 네임스페이스 추가, `@Enable*` 스타일 모듈 활성화 어노테이션 정착.
- 3.0: 내장 검증(JSR-303 Bean Validation) 통합, OXM(Object/XML Mapping) 모듈.

> **`@Enable*` 스타일 모듈 활성화** — 그 기능을 쓰겠다고 설정 클래스에 한 줄로 선언해 켜는 어노테이션.\
> 예: 이 편에 나온 것이 `@EnableAsync`·`@EnableScheduling`·`@EnableCaching`·`@EnableWebMvc`다.

## 설정 스타일의 변화

이 시대에 **세 가지 설정 스타일이 모두 완성**되어 공존하게 됐다.
1. XML — 전통 방식, `c:`/`p:` 네임스페이스로 더 간결해짐
2. 어노테이션 + 컴포넌트 스캔 — 2.5에서 도입, 계속 발전
3. **Java Config(`@Configuration`/`@Bean`)** — 3.0의 핵심. 타입 안전하고 IDE 리팩토링·디버깅에 강함

3.1의 `@Profile`/`@PropertySource`/`@Enable*`이 더해지며 "XML 0줄" 구성이 현실적으로 가능해졌고, 이것이 곧 Spring Boot(2014)의 토대가 된다.

## 마이너 버전별 변화
- 3.0 (2009-12): **Java 5 베이스라인**, `@Configuration`/`@Bean`(Java Config), SpEL, REST 지원(`@PathVariable` 등), `@Async`, OXM, JSR-303 검증 통합.
- 3.1 (2011-12): **환경/프로파일 추상화(`@Profile`)**, 캐시 추상화(`@Cacheable`/`@EnableCaching`), `@PropertySource`, `c:` 네임스페이스, Java 기반 MVC 설정(`@EnableWebMvc`), 서블릿 3.0 기반 `WebApplicationInitializer`(web.xml 없는 부트스트랩), Servlet 3.0 기반 파일 업로드(`StandardServletMultipartResolver`).
- 3.2 (2012-12): **Spring MVC 비동기 처리(`Callable`/`DeferredResult`)**, `@ControllerAdvice` 전역 예외 처리, MVC 테스트 프레임워크(`MockMvc`), `@MatrixVariable`·콘텐츠 협상 개선, Gradle 빌드 전환.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

- **Java Config의 도입**으로 "설정도 코드다"라는 인식이 확산됐고, XML 의존을 끊을 수 있는 길이 열렸다.
- REST 지원 강화로 Spring MVC가 웹 API 개발의 사실상 표준 도구로 자리 잡았다.
- `@Profile`·`@Enable*`·`@PropertySource`·`WebApplicationInitializer` 등 3.1/3.2의 자바 기반 부트스트랩 기능은 **Spring Boot의 자동 구성(auto-configuration) 철학으로 직접 이어진다.** 3.x가 없었다면 Boot도 없었다.

## 용어 풀이

- **서드파티(third-party) 객체** — 남이 만들어 배포한 라이브러리의 클래스. 소스가 내 손에 없어 어노테이션을 새겨 넣을 수 없고, 3.0 이전에는 원문 표현대로 "여전히 XML `<bean>`의 몫이었다".
- **타입 안전(type-safe)** — 잘못 이어 붙인 것을 실행 전에 컴파일러·도구가 잡아 줄 수 있는 상태. 원문이 Guice의 매력으로 든 말이 "타입 안전한 자바 설정"이다.
- **JavaConfig / Java Config** — 빈을 자바 클래스로 정의하는 방식. 원문 표현으로 "별도 프로젝트였던 JavaConfig가 코어로 들어오며" 3.0에서 정식 편입됐다.
- **`@Configuration`** — 이 클래스가 빈을 정의하는 곳임을 표시하는 어노테이션.
- **`@Bean`** — 그 메서드가 반환하는 객체를 빈으로 등록하라는 표시. 메서드 몸통이 자바 코드라 남이 만든 클래스도 여기서 만들어 넘길 수 있다.
- **SpEL(Spring Expression Language)** — 설정 자리에 값 대신 적어 두면 실행 시점에 계산되어 그 자리를 채우는 식. 원문이 든 쓰임이 프로퍼티 조회·메서드 호출·컬렉션 조작이다.
- **`@PathVariable`** — URL 경로의 한 토막을 메서드 인자로 받아 오는 표시.
- **`@ResponseBody` / `HttpMessageConverter`** — 반환값을 화면이 아니라 응답 본문으로 보내라는 표시 / 그 객체를 JSON·XML로 바꿔 주는 변환기. 원문은 이 변환을 "JSON/XML 자동 변환"이라 적는다.
- **`RestTemplate`** — 원문이 REST 지원의 "클라이언트" 쪽으로 든 것.
- **`DispatcherServlet`(프런트 컨트롤러)** — 요청을 한 군데서 먼저 받아 알맞은 처리기로 넘기는 입구. 원문 표현으로 "단일 진입점(Front Controller)".
- **`HandlerMapping` / `HandlerAdapter`** — 어느 핸들러가 맡는지 찾아 주는 쪽 / 그 핸들러를 실제로 실행해 주는 쪽.
- **`ModelAndView`** — 뷰 이름과 화면에 넘길 모델을 함께 담은 반환값.
- **`ViewResolver` / `View`** — 뷰 이름을 실제 화면 객체로 풀어 주는 쪽 / 모델을 받아 화면을 그려 내는 쪽. REST 갈래에서는 원문 표현대로 "ViewResolver를 거치지 않"는다.
- **`@Async`** — 부른 자리에서 끝날 때까지 붙들지 말고 따로 실행하라는 표시. 원문 주석은 "별도 스레드 실행"이다.
- **`@Scheduled` / cron 식** — 정해진 주기에 스스로 실행되게 하는 표시 / 그 주기를 적는 문법.
- **프로파일(profile)** — 환경에 이름을 붙여 두고 그 이름이 켜졌을 때만 쓰이는 구성을 갈라 두는 장치. 3.1의 `@Profile`은 클래스(설정) 단위로만 붙는다.
- **캐시 추상화** — 어느 캐시 제품을 쓰든 같은 어노테이션으로 캐싱을 선언하게 해 주는 층. 원문이 백엔드로 든 것이 EhCache·ConcurrentMap이다.
- **`@Enable*` 스타일 모듈 활성화** — 그 기능을 쓰겠다고 설정 클래스에 한 줄로 선언해 켜는 어노테이션. 이 편에 나온 것이 `@EnableAsync`·`@EnableScheduling`·`@EnableCaching`·`@EnableWebMvc`다.

## 참고 출처
- [Spring Framework - Wikipedia](https://en.wikipedia.org/wiki/Spring_Framework)
- [Spring Framework 3.0: Releases, Release Date, EOL - versionlog](https://versionlog.com/spring-framework/3.0/)
- [Spring framework version history - codejava.net](https://www.codejava.net/frameworks/spring/spring-framework-version-history)
- [New Features and Enhancements in Spring Framework 4.0 (docs)](https://docs.spring.io/spring-framework/docs/4.2.x/spring-framework-reference/html/new-in-4.0.html)
- [Spring Framework Versions: Feature list by version](https://bluebirdinternational.com/spring-framework-versions/)
