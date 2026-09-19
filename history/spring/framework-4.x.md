# Spring Framework 4.x (2013 ~)

> 원본: `~/project/java-history/spring/framework-4.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/어노테이션 이름·JSR 번호·코드블록 6개(Java 5 · Groovy 1)·「릴리스 정보」와 「마이너 버전별 변화」의 목록은 원문 그대로다.\
> ASCII 도식 2개(그중 1개는 원문 mermaid 시퀀스 그림을 글자로 옮긴 것이다), 「한눈에」의 기초·건물 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 「재서술자 주」 1개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 8(람다·java.time)을 정식으로 받아들이고, `@RestController`·WebSocket·`@Conditional`을 도입한 세대. 같은 시기에 등장한 Spring Boot(2014)와 함께 "관례 우선" 시대를 연다.

이 편을 하나의 비유로 읽으면 **눈에 잘 띄는 건물이 아니라 그 아래 박아 둔 기초 이야기**다.\
사람들이 구경하는 것은 위에 올라간 건물인데, 그 건물이 설 수 있는 이유는 먼저 박아 둔 기초에 있다.\
**4.x와 Spring Boot의 관계도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 "4.x는 Boot라는 거대한 생태계를 떠받치는 토대 세대다"라고 적는다.

본문 흐름에 쓰는 비유는 이 기초·건물 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 땅에 먼저 박아 둔 기초 | 원문이 Boot가 "그 위에서" 동작한다고 든 것 — "4.x의 조건부 빈(`@Conditional`)·Java Config·`@Enable*` 기능" |
| 그 위에 올라간 건물 | Spring Boot 1.0의 "자동 구성(auto-configuration)"과 "내장 톰캣" |
| 조건이 맞을 때만 이어지는 배선 | `@Conditional` — 원문 표현으로 "환경/클래스패스/프로퍼티 등 조건에 따라 빈 등록 여부를 결정하는 일반화된 메커니즘" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **`@RestController`가 새로운 종류의 컨트롤러가 아니다.**\
  원문 정의는 "`@Controller` + `@ResponseBody`를 합친 합성 어노테이션"이다.
- **JSON으로 바꿔 주는 쪽이 `DispatcherServlet`이 아니다.**\
  원문이 그림 앞에서 직접 못 박은 그대로다 — "실제로는 `DispatcherServlet`이 직접 컨버터를 호출하지 않고, `RequestMappingHandlerAdapter`의 반환값 처리기(`RequestResponseBodyMethodProcessor`)가 컨버터를 사용한다."
- **`@GetMapping`은 4.0에 있던 것이 아니다.**\
  원문이 코드 주석에 적어 둔 그대로다 — "`@GetMapping`은 4.3부터이므로 4.1/4.2에서는 `@RequestMapping`을 쓴다".

## 릴리스 정보
- 최초 출시: 4.0 — 2013년 12월
- 주요 마이너 버전과 시기: 4.0(2013-12) → 4.1(2014-09) → 4.2(2015-07) → 4.3(2016-06)
- 최소 자바 버전(baseline): Java 6 이상(Java 7/8 권장). 4.0부터 Java 8 정식 지원, 4.3은 Java 6+/Servlet 2.5+ 요구의 마지막 세대.
- Java EE / Jakarta EE 기준: Java EE 6 기반(JPA 2.0, Servlet 3.0), Java EE 7 일부 지원(WebSocket·JMS 2.0 등)

## 시대적 배경

2014년 3월 Java 8이 출시되며 **람다 표현식·메서드 참조·`java.time`(JSR-310)·`Optional`**이라는 대형 언어 변화가 왔다.\
Spring 4.0은 이 변화에 맞춰 코드베이스를 정비하고 Java 8을 1급으로 지원했다.\
동시에 낡은 의존성(Java 5, Servlet 2.4 등)에 대한 지원을 정리했다.

> **재서술자 주:** 원문의 「릴리스 정보」는 4.0을 **2013년 12월**로 적는데, 이 문단은 "**2014년 3월** Java 8이 출시되며 … Spring 4.0은 이 변화에 맞춰 코드베이스를 정비"했다고 적는다 — 두 연월을 빼면 4.0 출시가 Java 8 출시보다 석 달 앞선다.\
> 원문이 「참고 출처」에 든 "Spring Framework 4.0.3 released - Java 8 support production-ready"(2014-03)로 미루어, 4.0에서 시작해 4.0.x에서 완성된 지원을 한 문단으로 묶어 적은 것으로 보인다.\
> 상류(원본 repo)에 확인을 요청할 자리다.

더 큰 사건은 **2014년 Spring Boot 1.0**의 등장이다.\
Boot는 4.x의 조건부 빈(`@Conditional`)·Java Config·`@Enable*` 기능 위에서 "자동 구성(auto-configuration)"과 "내장 톰캣"을 제공해, Spring 설정의 복잡함을 사실상 제거했다.\
4.x는 Boot라는 거대한 생태계를 떠받치는 토대 세대다.

바로 위 세 문장을 위아래 두 칸으로 놓으면 이렇다.

```text
+-------------------------------------------------------+
| Spring Boot 1.0 (2014)                                |
|   "자동 구성(auto-configuration)"과 "내장 톰캣"       |
|   Spring 설정의 복잡함을 사실상 제거                  |
+-------------------------------------------------------+
              ^
              |  떠받친다
              |
+-------------------------------------------------------+
| Spring Framework 4.x                                  |
|   조건부 빈(@Conditional) · Java Config · @Enable*    |
+-------------------------------------------------------+
```

- 화살표는 하나이고, 원문의 "4.x의 … 기능 **위에서**"와 "Boot라는 거대한 생태계를 **떠받치는** 토대 세대"를 그대로 옮긴 것이다.
- 위 칸의 세 줄과 아래 칸의 한 줄은 모두 위 문단에서 따온 글자다.
- 아래 칸에 든 셋은 원문이 "4.x의 …"로 열거한 셋 그대로이고, 순서도 원문과 같다.

> **자동 구성(auto-configuration)** — 개발자가 설정을 적지 않아도 프레임워크가 상황을 보고 알아서 구성을 채워 넣는 방식.\
> 예: 원문은 Boot가 이것과 "내장 톰캣"을 제공해 "Spring 설정의 복잡함을 사실상 제거했다"고 적는다.

## 핵심 추가/변경 기능

### Java 8 1급 지원

람다/메서드 참조를 콜백 인터페이스에 직접 사용, `java.time` 타입을 컨버전·포매팅에서 지원, `Optional`을 컨트롤러 파라미터/주입에 활용.

> **람다 표현식(lambda) / 메서드 참조(method reference)** — 이름 없는 짧은 함수를 그 자리에 적는 문법 / 이미 있는 메서드를 함수 자리에 이름만으로 넘기는 문법.\
> 예: 아래 코드의 `(rs, rowNum) -> new Account(...)`가 람다이고, 원문은 이것을 "콜백 인터페이스에 직접 사용"하는 예로 든다.

```java
// JdbcTemplate에 람다로 RowMapper 전달 (Java 8)
List<Account> accounts = jdbcTemplate.query(
    "SELECT id, name FROM account",
    (rs, rowNum) -> new Account(rs.getLong("id"), rs.getString("name")));
```

```java
// java.time 지원
@DateTimeFormat(iso = ISO.DATE)
private LocalDate openDate;

// Optional 파라미터 (4.1+) — @GetMapping은 4.3부터이므로 4.1/4.2에서는 @RequestMapping을 쓴다
@RequestMapping(value = "/search", method = RequestMethod.GET)
public List<Account> search(@RequestParam Optional<String> keyword) { ... }
```

> **`Optional`** — 값이 있을 수도 없을 수도 있음을 타입 자체로 드러내는 Java 8의 래퍼.\
> 예: 위 코드의 `@RequestParam Optional<String> keyword`가 원문이 든 "컨트롤러 파라미터"에서의 쓰임이다.

**언제 쓸 수 있게 됐나** — 원문이 위 코드 주석에 적어 둔 그대로다: `Optional` 파라미터는 4.1+, `@GetMapping`은 4.3부터라 4.1/4.2에서는 `@RequestMapping`을 쓴다.

### @RestController

`@Controller` + `@ResponseBody`를 합친 합성 어노테이션.\
REST API 작성이 한층 간결해졌다.

> **합성 어노테이션(composed annotation)** — 여러 어노테이션을 한데 묶어 새 이름 하나로 쓰게 만든 어노테이션.\
> 예: 원문이 이 절 첫 줄에서 `@RestController`를 "`@Controller` + `@ResponseBody`를 합친" 것이라 적는다.

```java
@RestController                       // 모든 메서드 반환값이 응답 본문(JSON)
@RequestMapping("/accounts")
public class AccountApi {

    @GetMapping("/{id}")              // 4.3의 @GetMapping과 결합하면 더 간결
    public Account get(@PathVariable long id) {
        return accountService.find(id);
    }
}
```

다음은 `@RestController`/`@ResponseBody`가 뷰를 거치지 않고 `HttpMessageConverter`(Jackson)로 객체↔JSON을 변환해 응답하는 흐름이다.\
실제로는 `DispatcherServlet`이 직접 컨버터를 호출하지 않고, `RequestMappingHandlerAdapter`의 반환값 처리기(`RequestResponseBodyMethodProcessor`)가 컨버터를 사용한다.

```text
Client (JSON)                        --> DispatcherServlet                     HTTP 요청 (Accept: application/json)
DispatcherServlet                    --> HandlerAdapter / ReturnValueHandler   핸들러 실행 위임
HandlerAdapter / ReturnValueHandler  --> @RestController                       핸들러 메서드 호출 (@PathVariable 등 바인딩)
@RestController                      --> AccountService                        비즈니스 로직 호출
AccountService                       --> @RestController                       도메인 객체 (Account)
@RestController                      --> HandlerAdapter / ReturnValueHandler   반환값 (객체) — @ResponseBody 적용
HandlerAdapter / ReturnValueHandler  --> HttpMessageConverter (Jackson)        객체 → JSON 직렬화 (ReturnValueHandler가 호출)
HttpMessageConverter (Jackson)       --> HandlerAdapter / ReturnValueHandler   JSON 본문
HandlerAdapter / ReturnValueHandler  --> DispatcherServlet                     완료
DispatcherServlet                    --> Client (JSON)                         HTTP 응답 (뷰 해석 없이 데이터 직렬화)
```

- 이 그림은 원문의 mermaid 시퀀스 그림을 글자로 옮긴 것이다 — 화살표 열로 원문의 메시지 수와 같고, 순서와 방향도 원문과 같다.
- 양쪽의 이름은 원문이 participant로 선언한 이름 그대로이고, 오른쪽에 적은 말은 원문이 그 화살표에 붙인 메시지 글자 그대로다(일곱째 줄 라벨 안의 `→`도 원문 라벨의 글자다).
- 직렬화를 부르는 칸이 `DispatcherServlet`이 아니라 `HandlerAdapter / ReturnValueHandler`인 것이 바로 위 문단이 못 박은 대목이다.

`@RestController`는 `@Controller`+`@ResponseBody`의 합성이라 모든 반환값이 뷰가 아닌 응답 본문으로 처리되며, 요청 본문(JSON)도 같은 컨버터로 객체로 역직렬화된다.

> **직렬화 / 역직렬화(serialize / deserialize)** — 객체를 전송할 수 있는 형식(여기서는 JSON)으로 바꾸는 일 / 그 반대로 되돌리는 일.\
> 예: 바로 위 문장이 든 짝이 그것이다 — 반환값은 응답 본문으로 나가고, "요청 본문(JSON)도 같은 컨버터로 객체로 역직렬화된다".

### @Conditional — 조건부 빈 등록

환경/클래스패스/프로퍼티 등 조건에 따라 빈 등록 여부를 결정하는 일반화된 메커니즘.\
**Spring Boot 자동 구성의 핵심 엔진**(`@ConditionalOnClass`, `@ConditionalOnMissingBean` 등은 모두 이 위에 구현됨).

> **`@Conditional`** — 그 빈을 등록할지 말지를 조건에 맡기는 표시. 「한눈에」의 "조건이 맞을 때만 이어지는 배선"이 이것이다.\
> 예: 아래 코드의 `@Conditional(RedisAvailableCondition.class)`가 그 조건 클래스를 가리키고, 원문이 이 위에 구현됐다고 든 것이 `@ConditionalOnClass`·`@ConditionalOnMissingBean`이다.

```java
@Configuration
public class CacheConfig {

    @Bean
    @Conditional(RedisAvailableCondition.class)
    public CacheManager redisCacheManager() { ... }
}
```

### WebSocket / SockJS / STOMP

`spring-websocket` 모듈로 표준 WebSocket(JSR-356)과 SockJS 폴백, STOMP 메시징을 지원.\
실시간 양방향 통신을 위한 메시징 인프라(`spring-messaging`) 도입.

> **양방향 통신 / 폴백(fallback)** — 서버도 먼저 말을 걸 수 있는 연결 / 그것을 쓸 수 없을 때 대신 쓰는 차선책.\
> 예: 원문은 "실시간 양방향 통신"을 `spring-messaging` 인프라의 목적으로 적고, 그 앞줄에서 표준 WebSocket과 함께 "SockJS 폴백"을 든다.

```java
// 4.x의 WebSocketMessageBrokerConfigurer 인터페이스에는 default 메서드가 없어
// 직접 구현하면 모든 추상 메서드를 구현해야 한다. 필요한 메서드만 재정의하려면
// AbstractWebSocketMessageBrokerConfigurer를 상속한다. (인터페이스 default화는 5.0부터)
@Configuration
@EnableWebSocketMessageBroker
public class WsConfig extends AbstractWebSocketMessageBrokerConfigurer {

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws").withSockJS();
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic");
        registry.setApplicationDestinationPrefixes("/app");
    }
}
```

**언제 쓸 수 있게 됐나** — 원문이 위 코드 첫 세 줄 주석에 적어 둔 그대로다: 4.x에서는 `WebSocketMessageBrokerConfigurer`에 default 메서드가 없어 `AbstractWebSocketMessageBrokerConfigurer`를 상속하고, "인터페이스 default화는 5.0부터"다.

### Groovy DSL 빈 정의

XML/Java Config 외에 Groovy DSL로 빈을 정의하는 방식 추가.\
XML과 동일 개념이지만 훨씬 간결하다.

> **DSL(Domain-Specific Language, 도메인 특화 언어)** — 한 가지 일에만 쓰도록 좁게 만든 표기법.\
> 예: 아래 Groovy 코드가 빈 정의만을 위한 표기이고, 원문은 이것을 "XML과 동일 개념이지만 훨씬 간결하다"고 적는다.

```groovy
beans {
    dataSource(BasicDataSource) {
        url = 'jdbc:mysql://localhost/test'
        username = 'root'
    }
    accountService(AccountServiceImpl, ref('accountDao'))
}
```

### 기타
- **`@Repeatable`** 적용: `@PropertySource`, `@Scheduled` 등을 같은 요소에 반복 선언 가능(Java 8).
- 핵심 어노테이션의 메타 어노테이션화 → 합성 어노테이션 작성 용이.
- 4.1: 캐시 추상화 개선(`@CacheConfig`, JCache/JSR-107 지원), MVC `ResponseEntity`/`RequestEntity` 빌더, 정적 자원 처리 개선, 테스트의 SQL 스크립트(`@Sql`).
- 4.2: `@AliasFor`(어노테이션 속성 별칭), 어노테이션 기반 이벤트 리스너(`@EventListener`), CORS 지원, HTTP 스트리밍 개선.
- 4.3: **합성 매핑 어노테이션(`@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`)**, 단일 생성자 시 `@Autowired` 생략 가능(암묵적 생성자 주입), `@RequestScope`/`@SessionScope`. Spring 4 시리즈의 마지막이자 장기 지원 버전.

> **메타 어노테이션(meta-annotation)** — 다른 어노테이션에 붙는 어노테이션. 원문은 핵심 어노테이션이 이렇게 되면서 "합성 어노테이션 작성 용이"해졌다고 적는다.\
> 예: 원문이 든 합성의 결과가 `@RestController`이고, 4.3의 합성 매핑 어노테이션 `@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`이다.

> **암묵적 생성자 주입** — 생성자가 하나뿐이면 `@Autowired`를 적지 않아도 그 생성자로 주입되는 것(원문 표현: "단일 생성자 시 `@Autowired` 생략 가능").\
> 예: 같은 시리즈 `framework-2.x.md` 편의 `AccountServiceImpl`이 생성자 위에 `@Autowired`를 붙여 두는데, 4.3부터는 그 클래스처럼 생성자가 하나뿐이면 그 한 줄을 적지 않아도 된다.

## 설정 스타일의 변화

설정 스타일은 XML / 어노테이션 / Java Config / Groovy DSL 4종이 공존하되, **무게중심이 완전히 Java Config + 어노테이션으로 이동**했다.\
결정적 변화는 외부에서 왔다 — **Spring Boot**가 4.x의 `@Conditional`·`@Enable*`·Java Config를 활용해 "설정을 거의 작성하지 않는" 자동 구성 모델을 제시하면서, 실무 표준이 "XML 작성"에서 "스타터 의존성 추가 + 프로퍼티 몇 줄"로 바뀌었다.

> **스타터(starter) 의존성** — 원문이 실무 표준의 새 모습으로 든 표현 "스타터 의존성 추가 + 프로퍼티 몇 줄"의 앞쪽.\
> 예: 원문은 이 말을 "XML 작성"과 대비되는 자리에 놓고, Boot의 모델을 "설정을 거의 작성하지 않는" 자동 구성이라 부른다.

## 마이너 버전별 변화
- 4.0 (2013-12): **Java 8 지원(람다·`java.time`)**, `@RestController`, `@Conditional`, WebSocket/STOMP(`spring-websocket`, `spring-messaging`), Groovy DSL, Java EE 7 일부 지원.
- 4.1 (2014-09): JCache(JSR-107), `ResponseEntity`/`RequestEntity` 빌더, `@Sql` 테스트, MVC 뷰 해석 개선, WebSocket 개선, SpEL 컴파일러(compiler mode).
- 4.2 (2015-07): `@AliasFor`, `@EventListener`, 전역/메서드 CORS, HTTP 스트리밍.
- 4.3 (2016-06): `@GetMapping` 등 합성 매핑 어노테이션, 암묵적 생성자 주입, `@RequestScope`/`@SessionScope`. Java 6+/Servlet 2.5+ 지원의 마지막 세대(장기 지원).

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

- Java 8을 정식 수용하며 함수형 스타일 코드를 Spring 전반에 끌어들였다.
- `@RestController`와 합성 매핑 어노테이션은 오늘날 REST API 코드의 표준 형태를 확정했다.
- **`@Conditional`은 Spring Boot 자동 구성의 기반 기술**로, 4.x는 사실상 "Boot 시대를 떠받친 프레임워크 세대"다. 이후 개발자 경험의 중심은 Framework 직접 설정에서 Boot 스타터로 옮겨간다.

## 용어 풀이

- **람다 표현식(lambda) / 메서드 참조(method reference)** — 이름 없는 짧은 함수를 그 자리에 적는 문법 / 이미 있는 메서드를 함수 자리에 이름만으로 넘기는 문법. 원문은 이 둘을 "콜백 인터페이스에 직접 사용"한다고 적는다.
- **`java.time`(JSR-310)** — Java 8이 들여온 날짜·시각 타입 묶음. 원문은 이것을 "컨버전·포매팅에서 지원"한다고 적는다.
- **`Optional`** — 값이 있을 수도 없을 수도 있음을 타입으로 드러내는 Java 8의 래퍼. 원문이 든 쓰임은 컨트롤러 파라미터와 주입이고, 파라미터 쪽은 4.1+다.
- **합성 어노테이션(composed annotation)** — 여러 어노테이션을 한데 묶어 새 이름 하나로 쓰게 만든 어노테이션. 원문이 든 것이 `@RestController`(= `@Controller` + `@ResponseBody`)다.
- **메타 어노테이션(meta-annotation)** — 다른 어노테이션에 붙는 어노테이션. 핵심 어노테이션이 이렇게 되면서 합성 어노테이션을 만들기 쉬워졌다.
- **`@RestController`** — `@Controller` + `@ResponseBody`를 합친 합성 어노테이션. 원문 주석대로 "모든 메서드 반환값이 응답 본문(JSON)"이 된다.
- **`HttpMessageConverter`** — 객체와 JSON 사이를 바꿔 주는 변환기. 원문이 이 편에서 괄호로 든 구현이 Jackson이고, 이 컨버터를 부르는 쪽은 `DispatcherServlet`이 아니라 `RequestMappingHandlerAdapter`의 반환값 처리기(`RequestResponseBodyMethodProcessor`)다.
- **직렬화 / 역직렬화(serialize / deserialize)** — 객체를 전송 형식으로 바꾸는 일 / 그 반대로 되돌리는 일.
- **`@Conditional`** — 환경/클래스패스/프로퍼티 등 조건에 따라 빈 등록 여부를 결정하는 일반화된 메커니즘. 원문은 이것을 "Spring Boot 자동 구성의 핵심 엔진"이라 부른다.
- **자동 구성(auto-configuration)** — 설정을 적지 않아도 프레임워크가 상황을 보고 구성을 채워 넣는 방식. Boot가 이것과 내장 톰캣으로 "Spring 설정의 복잡함을 사실상 제거했다".
- **양방향 통신 / 폴백(fallback)** — 서버도 먼저 말을 걸 수 있는 연결 / 그것을 쓸 수 없을 때 대신 쓰는 차선책. 원문이 든 짝이 WebSocket(JSR-356)과 SockJS 폴백이다.
- **STOMP** — 원문이 `spring-websocket`의 지원 대상으로 WebSocket·SockJS와 나란히 든 메시징 방식.
- **DSL(Domain-Specific Language)** — 한 가지 일에만 쓰도록 좁게 만든 표기법. 4.0이 더한 것이 Groovy DSL 빈 정의다.
- **`@Repeatable`** — 같은 요소에 같은 어노테이션을 여러 번 붙일 수 있게 하는 Java 8 기능. 원문이 든 적용 대상이 `@PropertySource`·`@Scheduled` 등이다.
- **암묵적 생성자 주입** — 생성자가 하나뿐이면 `@Autowired`를 적지 않아도 그 생성자로 주입되는 것. 4.3의 변화다.
- **스타터(starter) 의존성** — 원문이 바뀐 실무 표준으로 든 "스타터 의존성 추가 + 프로퍼티 몇 줄"의 앞쪽.

## 참고 출처
- [Spring Framework - Wikipedia](https://en.wikipedia.org/wiki/Spring_Framework)
- [New Features and Enhancements in Spring Framework 4.0 (docs)](https://docs.spring.io/spring-framework/docs/4.2.x/spring-framework-reference/html/new-in-4.0.html)
- [Spring Framework 4.0.3 released - Java 8 support production-ready](https://spring.io/blog/2014/03/27/spring-framework-4-0-3-released-with-java-8-support-now-production-ready/)
- [Groovy Bean Configuration in Spring Framework 4](https://spring.io/blog/2014/03/03/groovy-bean-configuration-in-spring-framework-4/)
- [Spring framework version history - codejava.net](https://www.codejava.net/frameworks/spring/spring-framework-version-history)
