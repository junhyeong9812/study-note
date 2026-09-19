# Spring Framework 2.x (2006 ~)

> 원본: `~/project/java-history/spring/framework-2.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/어노테이션 이름·코드블록 6개(XML 3 · Java 3)·「릴리스 정보」와 「마이너 버전별 변화」의 목록은 원문 그대로다.\
> ASCII 도식 3개(그중 2개는 원문 mermaid 그림을 글자로 옮긴 것이다), 「한눈에」의 등록 서류·이름표 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> XML을 네임스페이스로 간소화하고, 어노테이션 기반 설정의 문을 연 전환기. 2.5에서 `@Autowired`와 컴포넌트 스캔이 등장하며 "XML 탈출"이 시작됐다.

이 편을 하나의 비유로 읽으면 **물건마다 등록 서류를 손으로 쓰던 창고가, 물건에 이름표를 붙이고 창고를 한 번 훑는 방식으로 바뀐 일**이다.\
서류를 아주 없앤 것이 아니라, 먼저 양식을 짧게 고치고(2.0) 그다음 이름표와 훑기를 들였다(2.5).\
**2.x의 설정도 똑같은 구조다** — 원문 자신이 「설정 스타일의 변화」에서 이 편을 **"XML 일색"에서 "XML + 어노테이션 혼합"으로** 넘어가는 과도기라고 적는다.

본문 흐름에 쓰는 비유는 이 창고 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 물건 하나마다 손으로 쓰던 등록 서류 | 빈을 XML에 일일이 등록하던 방식 — 원문이 "Spring 1.x의 가장 큰 불만"으로 든 **장황한 XML** |
| 자주 쓰는 항목에 전용 칸이 생긴 서류 양식 | XML 네임스페이스 — 원문 표현으로 "도메인별 전용 네임스페이스(`<context:>`, `<aop:>`, `<tx:>`, `<jee:>`, `<util:>`)" |
| 물건에 직접 붙인 이름표 | 스테레오타입 어노테이션 `@Component`/`@Service`/`@Controller`/`@Repository` |
| 창고를 한 번 훑어 이름표 붙은 것을 모으는 일 | `<context:component-scan>` — 원문 표현으로 "패키지 스캔으로 빈 자동 등록" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **어노테이션이 XML을 없앤 편이 아니다 — 이 편은 "혼합"이다.**\
  원문이 2.5에 대해 적은 것은 "XML에는 인프라성 설정과 `<context:component-scan>`만 남기는 스타일이 유행하기 시작"이다.
- **이 편의 어노테이션 등록은 `@Bean`이 아니다.**\
  원문은 2.5 설명 끝에 "(단, 빈을 100% 자바 코드로 정의하는 `@Configuration`/`@Bean`은 아직 없음 — 3.0에서 등장)"이라고 못 박는다.\
  이 편에서 어노테이션으로 등록되는 빈은 **내 클래스에 스테레오타입을 붙여 스캔에 걸리게 한 것**이다.
- **프록시 AOP에서 어드바이스가 붙는 경로는 원문이 그린 그 하나다.**\
  원문의 그림은 「호출자 → 프록시 → 타깃 빈」이고, 원문 설명은 "호출자는 타깃 빈을 직접 부르지 않고 프록시를 거치며, 프록시가 before/around/after 어드바이스(횡단 관심사)를 적용한 뒤 실제 타깃 메서드를 호출한다"이다.\
  그 밖의 호출 경로는 이 편의 원문이 그리지도, 적지도 않는다.

## 릴리스 정보
- 최초 출시: 2.0 — 2006년 10월
- 주요 마이너 버전과 시기: 2.0(2006-10) → 2.5(2007-11)
- 최소 자바 버전(baseline): 2.0은 J2SE 1.3 이상, 2.5에서 1.3 지원을 제거하고 J2SE 1.4.2 이상 (어노테이션·제네릭 기능은 Java 5에서 활성화)
- Java EE / Jakarta EE 기준: J2EE 1.3 이상 호환 유지(Servlet 2.3/2.4), 2.5에서 Java EE 5(Servlet 2.5) 지원 강화

## 시대적 배경

2006년은 Java 5(2004)가 보급되며 **어노테이션·제네릭**이 본격적으로 쓰이기 시작한 시점이다.\
같은 해 EJB 3.0이 발표되며 어노테이션과 DI를 받아들였는데, 이는 역설적으로 Spring이 옳았음을 증명했다.\
한편 Spring 1.x의 가장 큰 불만은 **장황한 XML**이었다.\
2.x는 이 두 흐름에 답한다.

1. XML을 더 읽기 쉽고 짧게 — XML 네임스페이스(스키마 기반 커스텀 태그) 도입
2. 어노테이션으로 XML 자체를 줄이기 — 2.5의 컴포넌트 스캔과 `@Autowired`

> **어노테이션(annotation)** — 클래스·메서드·필드에 붙여 두는 `@`로 시작하는 표시. 붙여 두면 그것을 읽는 쪽(여기서는 Spring)이 보고 동작을 정한다.\
> 예: 아래에 나오는 `@Repository`·`@Service`·`@Autowired`·`@Controller`가 그런 표시다.

원문이 든 두 갈래가 곧 이 편의 두 축이다 — 1번이 아래 「XML 네임스페이스」 절이고, 2번이 「어노테이션 기반 설정의 시작 (2.5)」 절이다.

## 핵심 추가/변경 기능

### XML 네임스페이스 (구성 간소화)

*(「한눈에」의 "전용 칸이 생긴 서류 양식"에 해당하는 자리다.)*

DTD 대신 XSD 스키마를 채택하고, 도메인별 전용 네임스페이스(`<context:>`, `<aop:>`, `<tx:>`, `<jee:>`, `<util:>`)를 도입했다.\
장황한 `ProxyFactoryBean`/`TransactionProxyFactoryBean` 선언이 한 줄로 줄었다.

> **XML 네임스페이스** — 한 XML 문서 안에서 태그를 출처별로 갈라 쓰게 해 주는 이름 구역. 접두어(`tx:`·`aop:` 등)가 그 구역을 가리킨다.\
> 예: 아래 XML의 `xmlns:tx="…/schema/tx"` 선언이 `tx:` 구역을 열고, 그 아래 `<tx:advice>`·`<tx:method>`가 그 구역의 태그다.

> **XSD 스키마** — XML 문서에 어떤 태그와 속성이 올 수 있는지 규정한 정의 파일. 1.x가 쓰던 DTD 자리를 2.0이 이것으로 바꿨다.\
> 예: 아래 XML의 `xsi:schemaLocation="..."`가 그 스키마 위치를 적는 자리다.

이전(1.x)과 비교 — 선언적 트랜잭션:

```xml
<!-- 2.x: tx 네임스페이스 + AOP 포인트컷 -->
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xmlns:tx="http://www.springframework.org/schema/tx"
       xsi:schemaLocation="...">

    <tx:advice id="txAdvice" transaction-manager="transactionManager">
        <tx:attributes>
            <tx:method name="get*" read-only="true"/>
            <tx:method name="*"    propagation="REQUIRED"/>
        </tx:attributes>
    </tx:advice>

    <aop:config>
        <aop:pointcut id="serviceOps"
            expression="execution(* com.example.service.*.*(..))"/>
        <aop:advisor advice-ref="txAdvice" pointcut-ref="serviceOps"/>
    </aop:config>
</beans>
```

> **포인트컷(pointcut)** — 어드바이스를 "어디에" 걸 것인지 고르는 조건식.\
> 예: 위 XML의 `expression="execution(* com.example.service.*.*(..))"`가 그 조건이고, `<aop:advisor>`가 그 조건과 어드바이스를 짝지어 준다.

### AspectJ 통합 (@AspectJ 스타일 AOP)

Spring 자체 AOP(프록시 기반)를 그대로 유지하면서, AspectJ의 포인트컷 표현식과 `@Aspect`(@AspectJ) 어노테이션 스타일을 추가로 채택.\
AOP가 훨씬 강력하고 표현력 있게 바뀌었다.

아래는 프록시 기반 AOP의 동작이다.\
호출자는 타깃 빈을 직접 부르지 않고 프록시를 거치며, 프록시가 before/around/after 어드바이스(횡단 관심사)를 적용한 뒤 실제 타깃 메서드를 호출한다.

```text
(1) 호출자 (Caller)        --> 프록시 (Proxy)           메서드 호출
(2) 프록시 (Proxy)         --> 타깃 빈 (Target Bean)    어드바이스 적용 후 위임
(3) 타깃 빈 (Target Bean)  --> 프록시 (Proxy)           결과 반환
(4) 프록시 (Proxy)         --> 호출자 (Caller)          결과 반환

    프록시 (Proxy)        안에 적힌 것: before / around / after advice
    타깃 빈 (Target Bean) 안에 적힌 것: 비즈니스 로직
```

- 이 그림은 원문의 첫 번째 mermaid 그림을 글자로 옮긴 것이다 — 화살표 넷으로 원문과 같고, 오른쪽에 적은 네 마디는 원문이 그 화살표에 붙여 둔 라벨 그대로다.
- 아래 두 줄은 원문이 프록시 칸과 타깃 빈 칸 안에 적어 둔 문구다.
- 바로 위 문단이 이 그림을 읽는 법이다 — 순서는 (1)에서 (4)로, 갔다가 되돌아온다.

> **프록시(proxy)** — 타깃 빈 앞에 서서 호출을 대신 받는 대역 객체. 원문은 이 절 첫 줄에서 Spring 자체 AOP를 "프록시 기반"이라 적는다.\
> 예: 위 그림의 (1)에서 호출자가 실제로 부르는 상대가 타깃 빈이 아니라 이 프록시다.

> **어드바이스(advice)** — 끼어들어 실행될 공통 처리 자체. 원문은 이것을 "횡단 관심사"라 부른다.\
> 예: 위 그림의 프록시 칸에 적힌 before / around / after advice가 그것이고, 아래 코드의 `logTime` 메서드가 그중 around 하나다.

```xml
<aop:aspectj-autoproxy/>
```

```java
@Aspect
public class LoggingAspect {

    @Around("execution(* com.example.service.*.*(..))")
    public Object logTime(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = pjp.proceed();
        System.out.println(pjp.getSignature() + " took "
            + (System.currentTimeMillis() - start) + "ms");
        return result;
    }
}
```

> **`@Aspect`(@AspectJ 스타일)** — 어드바이스와 포인트컷을 XML이 아니라 클래스에 어노테이션으로 적는 방식. 원문은 "자체 AOP(프록시 기반)를 그대로 유지하면서" 이것을 "추가로 채택"했다고 적는다.\
> 예: 위 클래스가 그렇게 적힌 것이고, `@Around(…)`의 괄호 안이 포인트컷 표현식이다.

> **`ProceedingJoinPoint` / `proceed()`** — around 어드바이스가 받아 드는 "지금 가로챈 그 호출"과, 그것을 실제로 진행시키는 호출.\
> 예: 위 코드에서 `pjp.proceed()` 앞뒤로 시각을 재는 것이 곧 "적용한 뒤 실제 타깃 메서드를 호출한다"의 코드 모양이다.

### 어노테이션 기반 설정의 시작 (2.5)

*(「한눈에」의 "이름표"와 "훑기"에 해당하는 자리다.)*

2.5는 Spring 역사에서 결정적인 전환점이다.\
**컴포넌트 스캔과 어노테이션 의존성 주입**이 도입되어, 빈을 더 이상 XML에 일일이 등록하지 않아도 됐다.

- `@Component`, `@Service`, `@Controller` — 2.5에서 추가된 스테레오타입 어노테이션 (`@Repository`는 이미 2.0부터 제공)
- `@Autowired` — 타입 기반 자동 주입
- `@Qualifier` — 동일 타입 다중 빈 구분
- `<context:component-scan>` — 패키지 스캔으로 빈 자동 등록

> **스테레오타입 어노테이션(stereotype annotation)** — "이 클래스는 이런 역할의 빈이다"를 표시해 스캔에 걸리게 하는 어노테이션.\
> 예: 원문이 든 넷이 `@Component`·`@Service`·`@Controller`·`@Repository`이고, 그중 `@Repository`만 2.0부터, 나머지 셋은 2.5부터다.

> **`@Autowired`** — 주입할 빈을 **타입을 보고** 컨테이너가 골라 넣는 표시(원문 표현: "타입 기반 자동 주입").\
> 예: 아래 `AccountServiceImpl`의 생성자에 붙은 `@Autowired`가 `AccountDao` 타입의 빈을 찾아 넣게 한다.

> **`@Qualifier`** — 같은 타입의 빈이 여럿일 때 어느 것인지 골라 주는 표시(원문 표현: "동일 타입 다중 빈 구분").\
> 예: 원문은 이 어노테이션을 위 불릿에서 `@Autowired` 바로 다음 줄에 둔다 — 타입만으로 갈리지 않는 경우를 위한 짝이다.

아래는 2.5의 컴포넌트 스캔 흐름이다.\
classpath를 훑어 스테레오타입 어노테이션이 붙은 클래스를 찾아내고, 각각을 BeanDefinition으로 만들어 컨테이너에 등록한다.

```text
classpath 스캔
(base-package)
        ↓
스테레오타입 탐지
@Component / @Service / @Controller / @Repository
        ↓
BeanDefinition 등록
        ↓
컨테이너 (ApplicationContext)
```

- 이 그림은 원문의 두 번째 mermaid 그림을 글자로 옮긴 것이다 — 칸 넷, 화살표 셋으로 원문과 같고, 방향도 원문과 같이 위에서 아래다.
- 칸 안의 두 줄짜리 글자는 원문 노드가 줄바꿈으로 나눠 적어 둔 것 그대로다.

> **컴포넌트 스캔(component scan)** — 지정한 패키지 아래 classpath를 훑어 스테레오타입이 붙은 클래스를 찾아 빈으로 등록하는 일.\
> 예: 아래 XML의 `<context:component-scan base-package="com.example"/>` 한 줄이 그 훑기를 지시한다.

> **`BeanDefinition`** — 어떤 클래스를 어떤 이름의 빈으로 만들지 적어 둔 "빈 설계 정보". 컨테이너는 이것을 받아 등록한다.\
> 예: 위 그림의 셋째 칸이 그 등록 단계이고, 1.x에서 XML `<bean>` 한 줄이 하던 몫을 여기서는 탐지 결과가 채운다.

```xml
<!-- XML은 스캔 지시만 남는다 -->
<beans xmlns:context="http://www.springframework.org/schema/context" ...>
    <context:component-scan base-package="com.example"/>
</beans>
```

```java
@Repository
public class JdbcAccountDao implements AccountDao { /* ... */ }

@Service
public class AccountServiceImpl implements AccountService {

    private final AccountDao accountDao;

    @Autowired
    public AccountServiceImpl(AccountDao accountDao) {
        this.accountDao = accountDao;   // 생성자 자동 주입
    }
}
```

위 자바 코드가 「한눈에」의 이름표다 — `@Repository`·`@Service`가 이름표이고, 그 이름표를 찾아 주는 훑기가 바로 위 XML 한 줄이다.

### 어노테이션 기반 Spring MVC 컨트롤러 (2.5)

1.x의 `Controller` 인터페이스 구현 방식을 대체하는 `@Controller` / `@RequestMapping` 모델 도입.\
오늘날 우리가 쓰는 Spring MVC의 원형이다.

```java
@Controller
public class AccountController {

    @Autowired
    private AccountService accountService;   // 타입 기반 자동 주입

    @RequestMapping("/account/view")
    public String view(@RequestParam("id") long id, ModelMap model) {
        model.addAttribute("account", accountService.find(id));
        return "accountView";   // 뷰 이름
    }
}
```

> **`@RequestMapping`** — 어떤 요청 경로를 어느 메서드가 맡을지 적어 두는 표시.\
> 예: 위 코드의 `@RequestMapping("/account/view")`가 그 경로를 `view` 메서드에 붙인 자리다.

> **뷰 이름(view name)** — 컨트롤러가 반환하는, 화면을 가리키는 문자열.\
> 예: 위 코드의 `return "accountView";`가 그것이고, 원문이 그 줄에 붙여 둔 주석이 "뷰 이름"이다.

### JPA 지원

Java EE 5의 JPA(Java Persistence API)를 지원하는 `JpaTemplate`, `LocalContainerEntityManagerFactoryBean`, `@PersistenceContext` 주입 등을 제공.

> **JPA(Java Persistence API)** — 자바 객체와 관계형 DB 테이블을 잇는 표준 영속성 API. 원문은 이것을 "Java EE 5의 JPA"라 적는다.\
> 예: 원문이 이 절에서 이름을 든 지원 수단이 `JpaTemplate`·`LocalContainerEntityManagerFactoryBean`·`@PersistenceContext` 주입이다.

### 빈 스코프 확장

기존 `singleton`/`prototype`에 더해 웹 환경용 `request`, `session`, `globalSession` 스코프와 커스텀 스코프 등록 기능 추가.

> **빈 스코프(bean scope)** — 컨테이너가 그 빈을 몇 개, 언제까지 두고 쓸지를 정하는 범위.\
> 예: 원문이 "기존"으로 든 둘이 `singleton`과 `prototype`이고, 2.0이 더한 웹 환경용 셋이 `request`·`session`·`globalSession`이다.

> **`singleton` / `prototype`** — 컨테이너가 그 빈을 하나만 두고 돌려 쓰는 범위 / 달라고 할 때마다 새로 만들어 주는 범위.\
> 예: 원문은 이 둘을 "기존" 스코프로 적고, 웹 환경용 스코프를 그 위에 더한 것으로 적는다.

### 기타
- `<bean>`에 대한 라이프사이클 콜백 어노테이션(`@PostConstruct`/`@PreDestroy`, JSR-250) 지원
- 동적 언어(Groovy, JRuby, BeanShell)로 빈 작성 지원
- 메시지 기반 POJO 등 JMS 개선

> **라이프사이클 콜백(lifecycle callback)** — 의존성 주입이 끝난 뒤(초기화 단계), 또는 없어지기 직전에 컨테이너가 불러 주는 메서드.\
> 예: 원문이 이 불릿에서 든 짝이 `@PostConstruct`와 `@PreDestroy`(JSR-250)다.

## 설정 스타일의 변화

**"XML 일색"에서 "XML + 어노테이션 혼합"으로** 넘어가는 과도기.
- 2.0: 여전히 XML 중심이지만 네임스페이스로 훨씬 간결해짐.
- 2.5: 컴포넌트 스캔 + `@Autowired`로 빈 정의가 코드로 이동. XML에는 인프라성 설정과 `<context:component-scan>`만 남기는 스타일이 유행하기 시작. (단, 빈을 100% 자바 코드로 정의하는 `@Configuration`/`@Bean`은 아직 없음 — 3.0에서 등장)

위 두 불릿을 두 칸에 나란히 놓으면 이렇다.

```text
2.0                                  2.5
+---------------------------------+  +---------------------------------+
| 여전히 XML 중심이지만           |  | 컴포넌트 스캔 + @Autowired로    |
| 네임스페이스로 훨씬 간결해짐    |  | 빈 정의가 코드로 이동           |
|                                 |  |                                 |
|                                 |  | XML에는 인프라성 설정과         |
|                                 |  | <context:component-scan>만      |
|                                 |  | 남기는 스타일이 유행하기 시작   |
+---------------------------------+  +---------------------------------+
```

- 두 칸의 글자는 위 두 불릿의 문장을 그대로 옮긴 것이고, 칸 머리의 `2.0`·`2.5`도 원문이 그 불릿에 붙인 이름이다.
- 두 칸은 같은 항목의 전/후가 아니라 **원문이 따로 적은 두 시점**이다 — 원문의 표제 "「XML 일색」에서 「XML + 어노테이션 혼합」으로"가 그 사이의 방향이다.

**언제 쓸 수 있게 됐나** — 원문이 위 2.5 불릿 끝 괄호에 적어 두었다.

## 마이너 버전별 변화
- 2.0 (2006-10): XML 네임스페이스(`<aop:>`, `<tx:>` 등), `@AspectJ` 스타일 AOP, `@Repository`(예외 변환 스테레오타입), 새 빈 스코프, JPA 지원, 동적 언어 빈.
- 2.5 (2007-11): **`@Autowired`, `@Component`/`@Service`/`@Controller`(나머지 스테레오타입), 컴포넌트 스캔, 어노테이션 기반 MVC(`@RequestMapping`)**, JSR-250(`@PostConstruct`) 지원, 통합 테스트용 TestContext 프레임워크 도입.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

- XML 네임스페이스로 1.x의 가장 큰 약점(장황함)을 크게 완화했다.
- **2.5의 어노테이션 도입은 Spring 설정 패러다임의 분기점**이다. 이후 "설정을 어디에 둘 것인가(XML vs 어노테이션 vs Java Config)" 논쟁의 출발점이 되었고, 3.x의 Java Config와 훗날 Spring Boot의 "설정 최소화" 철학으로 이어진다.
- AspectJ 통합으로 AOP가 실무에서 본격적으로 쓰일 만큼 강력해졌다.

## 용어 풀이

- **어노테이션(annotation)** — 클래스·메서드·필드에 붙여 두는 `@`로 시작하는 표시. 붙여 두면 그것을 읽는 쪽이 보고 동작을 정한다.
- **XML 네임스페이스** — 한 XML 문서 안에서 태그를 출처별로 갈라 쓰게 해 주는 이름 구역. 원문이 든 것이 `<context:>`·`<aop:>`·`<tx:>`·`<jee:>`·`<util:>`다.
- **XSD 스키마** — XML에 어떤 태그와 속성이 올 수 있는지 규정한 정의 파일. 2.0이 DTD 자리를 이것으로 바꿨다.
- **포인트컷(pointcut)** — 어드바이스를 어디에 걸 것인지 고르는 조건식. 2.0이 AspectJ의 포인트컷 표현식을 채택했다.
- **어드바이저(advisor)** — 포인트컷과 어드바이스를 짝지어 등록하는 것. XML에서는 `<aop:advisor advice-ref=… pointcut-ref=…/>`가 그 자리다.
- **프록시(proxy)** — 타깃 빈 앞에 서서 호출을 대신 받는 대역 객체. 원문은 Spring 자체 AOP를 "프록시 기반"이라 적고, 그 경로를 「호출자 → 프록시 → 타깃 빈」으로 그린다.
- **어드바이스(advice)** — 끼어들어 실행될 공통 처리 자체. 원문의 그림에 적힌 것이 before / around / after advice다.
- **`@Aspect`(@AspectJ 스타일)** — 어드바이스와 포인트컷을 클래스에 어노테이션으로 적는 방식. 원문은 "자체 AOP(프록시 기반)를 그대로 유지하면서" 이것을 "추가로 채택"했다고 적는다.
- **`ProceedingJoinPoint` / `proceed()`** — around 어드바이스가 받아 드는 가로챈 호출과, 그것을 실제로 진행시키는 호출.
- **횡단 관심사(cross-cutting concern)** — 여러 기능에 가로질러 똑같이 끼어드는 일. 원문은 어드바이스를 이 말로 부른다.
- **스테레오타입 어노테이션(stereotype annotation)** — "이 클래스는 이런 역할의 빈이다"를 표시해 스캔에 걸리게 하는 어노테이션. `@Repository`는 2.0부터, `@Component`/`@Service`/`@Controller`는 2.5부터다.
- **컴포넌트 스캔(component scan)** — 지정한 패키지 아래 classpath를 훑어 스테레오타입이 붙은 클래스를 찾아 빈으로 등록하는 일. XML에서는 `<context:component-scan>` 한 줄이다.
- **`BeanDefinition`** — 어떤 클래스를 어떤 이름의 빈으로 만들지 적어 둔 빈 설계 정보. 스캔이 탐지한 클래스마다 이것이 만들어져 컨테이너에 등록된다.
- **`@Autowired`** — 주입할 빈을 타입을 보고 컨테이너가 골라 넣는 표시(원문 표현: "타입 기반 자동 주입").
- **`@Qualifier`** — 같은 타입의 빈이 여럿일 때 어느 것인지 골라 주는 표시(원문 표현: "동일 타입 다중 빈 구분").
- **`@RequestMapping`** — 어떤 요청 경로를 어느 메서드가 맡을지 적어 두는 표시. 2.5의 어노테이션 기반 MVC의 짝이다.
- **뷰 이름(view name)** — 컨트롤러가 반환하는, 화면을 가리키는 문자열. 원문이 `return "accountView";`에 붙인 주석이 그것이다.
- **JPA(Java Persistence API)** — 자바 객체와 관계형 DB를 잇는 표준 영속성 API. 원문은 "Java EE 5의 JPA"라 적는다.
- **빈 스코프(bean scope)** — 컨테이너가 그 빈을 몇 개, 언제까지 두고 쓸지를 정하는 범위.
- **`singleton` / `prototype`** — 컨테이너가 그 빈을 하나만 두고 돌려 쓰는 범위 / 달라고 할 때마다 새로 만들어 주는 범위. 원문은 이 둘을 "기존" 스코프로 든다.
- **라이프사이클 콜백(lifecycle callback)** — 의존성 주입이 끝난 뒤(초기화 단계), 또는 없어지기 직전에 컨테이너가 불러 주는 메서드. 원문이 든 짝이 `@PostConstruct`/`@PreDestroy`(JSR-250)다.

## 참고 출처
- [Spring Framework - Wikipedia](https://en.wikipedia.org/wiki/Spring_Framework)
- [Spring framework version history - codejava.net](https://www.codejava.net/frameworks/spring/spring-framework-version-history)
- [Spring Framework 2.0.8 Reference (PDF)](https://docs.spring.io/spring-framework/docs/2.0.8/spring-reference.pdf)
- [History of Spring Framework and Spring Boot](https://www.quickprogrammingtips.com/spring-boot/history-of-spring-framework-and-spring-boot.html)
- [Spring Framework Versions: Feature list by version](https://bluebirdinternational.com/spring-framework-versions/)
