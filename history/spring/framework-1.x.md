# Spring Framework 1.x (2004 ~)

> 원본: `~/project/java-history/spring/framework-1.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/어노테이션 이름·코드블록 5개(XML 3 · Java 2)·「릴리스 정보」와 「마이너 버전별 변화」의 목록은 원문 그대로다.\
> ASCII 도식 3개(그중 2개는 원문 mermaid 그림을 글자로 옮긴 것이다), 「한눈에」의 조립 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> EJB 없이도 엔터프라이즈 자바를 만들 수 있다는 것을 증명한 출발점. IoC/DI 컨테이너와 AOP, 일관된 추상화 계층으로 "경량 컨테이너" 시대를 열었다.

이 편을 하나의 비유로 읽으면 **부품을 내가 직접 끼워 맞추던 일을 조립 담당에게 넘긴 것**이다.\
부품 자체는 아무 표시도 붙지 않은 평범한 부품이고, 무엇을 무엇에 끼울지는 종이에 적어 두며, 그 종이를 읽고 실제로 끼워 주는 쪽이 따로 있다.\
**Spring 1.x의 컨테이너도 똑같은 구조다** — 원문 자신이 「시대적 배경」 마지막 문장에서 "프레임워크가 객체의 생성과 의존성 연결을 책임지고(IoC), 개발자는 비즈니스 로직(POJO)에 집중한다"고 적는다.

본문 흐름에 쓰는 비유는 이 조립 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 아무 표시도 붙지 않은 평범한 부품 | POJO — 원문 표현으로 "어떤 Spring 인터페이스도 구현하지 않는 순수 POJO" |
| 무엇을 무엇에 끼울지 적어 둔 종이 | XML 빈 정의(`applicationContext.xml`) |
| 그 종이를 읽고 실제로 끼워 주는 조립 담당 | IoC 컨테이너 — 원문 표현으로 "객체(빈)의 생성·초기화·의존성 주입·소멸 생명주기를 컨테이너가 관리한다" |
| 부품 하나만 손에 들고 따로 확인해 보는 것 | 원문 표현으로 "컨테이너 없이도 `new`로 만들어 단위 테스트할 수 있다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **Spring을 쓴다고 `new`를 못 쓰게 되는 것이 아니다.**\
  원문은 IoC 절에서 "`AccountServiceImpl`은 어떤 Spring 인터페이스도 구현하지 않는 순수 POJO이며, 컨테이너 없이도 `new`로 만들어 단위 테스트할 수 있다"고 적는다.\
  제어의 역전이 바꾼 것은 `new`를 쓸 수 있느냐가 아니라, 원문 표현대로 **누가 "객체의 생성과 의존성 연결을 책임지"느냐**다.
- **의존성 주입이 곧 어노테이션인 것도 아니다.**\
  이 편에서 원문이 든 주입은 XML에 적힌 setter 주입(`<property>`)과 생성자 주입(`<constructor-arg>`)이다.\
  원문이 이 편에서 이름을 든 어노테이션은 1.2의 `@Transactional`이고, 원문은 1.2를 "이후 어노테이션 시대로 가는 징검다리"라고 부른다.
- **AOP의 공통 처리는 프록시를 거쳐 붙는다.**\
  원문은 1.x의 AOP를 "어노테이션이 아니라 XML + 프록시 기반으로 구성했다"고 적는다.

## 릴리스 정보
- 최초 출시: 1.0 GA — 2004년 3월 24일 (Apache 2.0 라이선스, 초기 코드 공개는 2003년 6월)
- 주요 마이너 버전과 시기: 0.9(2003-06-26 SourceForge 공개) → 1.0(2004-03) → 1.1(2004) → 1.2(2005) — 책 *Expert One-on-One J2EE*는 2002년 출간
- 최소 자바 버전(baseline): J2SE 1.3 / 1.4 (주류는 어노테이션·제네릭 미사용이나, 1.2부터 JDK 1.5에서 `@Transactional` 어노테이션 사용 가능)
- Java EE / Jakarta EE 기준: J2EE 1.3 / 1.4 (Servlet 2.3/2.4, EJB 2.x 시대)

## 시대적 배경

2000년대 초반 자바 엔터프라이즈 개발의 표준은 EJB(Enterprise JavaBeans) 2.x였다.\
EJB는 분산 트랜잭션·보안·영속성을 제공했지만, 다음과 같은 고질적 문제가 있었다.

- Home/Remote 인터페이스, 디플로이먼트 디스크립터(XML) 등 과도한 보일러플레이트
- 컨테이너에 강하게 결합되어 단위 테스트가 사실상 불가능
- 무거운 애플리케이션 서버가 반드시 필요

> **EJB(Enterprise JavaBeans)** — 원문이 "2000년대 초반 자바 엔터프라이즈 개발의 표준"이라 부른 서버 측 컴포넌트 규격.\
> 예: 원문이 EJB가 제공한 것으로 든 셋이 분산 트랜잭션·보안·영속성이다.

> **보일러플레이트(boilerplate)** — 하는 일에 비해 매번 똑같이 다시 적어야 하는 판박이 코드.\
> 예: 원문이 "과도한 보일러플레이트"로 든 것이 Home/Remote 인터페이스와 디플로이먼트 디스크립터(XML)다.

> **디플로이먼트 디스크립터(deployment descriptor)** — 애플리케이션을 서버에 올릴 때 무엇을 어떻게 배치할지 적어 두는 XML 서술 파일.\
> 예: 원문은 이것을 위 불릿에서 보일러플레이트의 한 축으로 든다.

Rod Johnson은 2002년 저서 *Expert One-on-One J2EE Design and Development*에서 "EJB 없이 POJO(Plain Old Java Object)로 엔터프라이즈 애플리케이션을 만들 수 있다"고 주장하며 직접 작성한 인프라 코드를 공개했다.\
이 코드가 발전하여 Spring Framework가 되었고, 1.0은 그 첫 정식 결과물이다.\
핵심 메시지는 단순했다. **프레임워크가 객체의 생성과 의존성 연결을 책임지고(IoC), 개발자는 비즈니스 로직(POJO)에 집중한다.**

> **POJO(Plain Old Java Object)** — 특정 프레임워크의 인터페이스를 구현하거나 상속하지 않은, 평범한 자바 객체.\
> 예: 원문이 든 `AccountServiceImpl`이 그것이다 — 원문 표현으로 "어떤 Spring 인터페이스도 구현하지 않는 순수 POJO".

## 핵심 추가/변경 기능

### IoC / DI 컨테이너 (BeanFactory, ApplicationContext)

*(「한눈에」의 조립 담당에 해당하는 자리다.)*

Spring의 심장.\
객체(빈)의 생성·초기화·의존성 주입·소멸 생명주기를 컨테이너가 관리한다.

- `BeanFactory`: 가장 기본적인 IoC 컨테이너 (지연 로딩)
- `ApplicationContext`: BeanFactory를 확장해 메시지 소스, 이벤트 발행, AOP, 리소스 로딩 등을 추가한 상위 컨테이너

> **IoC(Inversion of Control, 제어의 역전)** — 객체를 언제 만들고 무엇과 이어 붙일지를 내 코드가 아니라 프레임워크가 정하는 것.\
> 원문의 정의는 "프레임워크가 객체의 생성과 의존성 연결을 책임지고(IoC), 개발자는 비즈니스 로직(POJO)에 집중한다"이다.\
> 예: 아래 XML에서 `accountService`가 `accountDao`를 받는 대목 — 내가 `new`로 그 순서를 짜 넣는 대신 컨테이너가 XML을 읽고 주입한다.

> **DI(Dependency Injection, 의존성 주입)** — 어떤 객체가 쓸 다른 객체를 그 객체가 직접 찾아오는 대신 밖에서 넣어 주는 것.\
> 예: 아래 XML의 `<property name="dataSource" ref="dataSource"/>`가 `JdbcAccountDao`에 `dataSource`를 넣어 주는 자리다.

> **빈(bean)** — 컨테이너가 생명주기를 관리하는 객체. 원문은 그 생명주기를 "생성·초기화·의존성 주입·소멸"로 적는다.\
> 예: 아래 XML의 `id="dataSource"`·`id="accountDao"`·`id="accountService"` 셋이 각각 빈 하나다.

> **지연 로딩(lazy loading)** — 필요해지는 시점까지 만들어 두지 않는 방식.\
> 예: 원문이 이 말을 괄호로 붙여 둔 자리가 위 불릿의 `BeanFactory`다 — "가장 기본적인 IoC 컨테이너 (지연 로딩)".

대표적인 XML 빈 정의(setter 주입):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- applicationContext.xml -->
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN"
    "http://www.springframework.org/dtd/spring-beans.dtd">
<beans>

    <bean id="dataSource" class="org.apache.commons.dbcp.BasicDataSource"
          destroy-method="close">
        <property name="driverClassName" value="com.mysql.jdbc.Driver"/>
        <property name="url"             value="jdbc:mysql://localhost/test"/>
        <property name="username"        value="root"/>
        <property name="password"        value="secret"/>
    </bean>

    <bean id="accountDao" class="com.example.dao.JdbcAccountDao">
        <property name="dataSource" ref="dataSource"/>
    </bean>

    <!-- 생성자 주입(constructor injection)도 지원 -->
    <bean id="accountService" class="com.example.service.AccountServiceImpl">
        <constructor-arg ref="accountDao"/>
    </bean>

</beans>
```

> **setter 주입 / 생성자 주입** — 이미 만든 객체의 설정 메서드로 값을 넣는 방식 / 객체를 만들 때 생성자 인자로 넣는 방식.\
> 예: 위 XML에서 `<property …/>`로 적힌 두 빈이 setter 주입이고, `<constructor-arg ref="accountDao"/>`로 적힌 `accountService`가 생성자 주입이다 — 원문이 그 줄 위에 "생성자 주입(constructor injection)도 지원"이라는 주석을 달아 두었다.

```java
// 컨테이너 부트스트랩
ApplicationContext ctx =
    new ClassPathXmlApplicationContext("applicationContext.xml");
AccountService service = (AccountService) ctx.getBean("accountService");
```

EJB와의 결정적 차이: `AccountServiceImpl`은 어떤 Spring 인터페이스도 구현하지 않는 순수 POJO이며, 컨테이너 없이도 `new`로 만들어 단위 테스트할 수 있다.

아래는 컨테이너가 관리하는 빈의 생명주기다.\
XML 빈 정의를 읽어 인스턴스를 만들고, 의존성을 주입한 뒤, 초기화 콜백을 거쳐 사용 가능 상태가 되며, 컨테이너 종료 시 소멸 콜백이 호출된다.

```text
빈 정의 로드 (XML)
        ↓
인스턴스화 (생성자 호출)
        ↓
의존성 주입 (populate)
        ↓
BeanPostProcessor 전처리
        ↓
초기화 (afterPropertiesSet / init-method)
        ↓
BeanPostProcessor 후처리
        ↓
사용 가능 (빈 제공)
        ↓
소멸 (destroy / destroy-method)
```

- 이 그림은 원문의 첫 번째 mermaid 그림을 글자로 옮긴 것이다 — 칸 여덟, 화살표 일곱으로 원문과 같다.
- 칸 안의 글자는 원문 노드 문구 그대로이고, 방향도 원문과 같이 위에서 아래다.
- 바로 위 문단이 이 그림을 읽는 법이다 — "XML 빈 정의를 읽어 인스턴스를 만들고, 의존성을 주입한 뒤, 초기화 콜백을 거쳐 사용 가능 상태가 되며, 컨테이너 종료 시 소멸 콜백이 호출된다".

`BeanFactory`와 `ApplicationContext`의 관계는 다음과 같다.\
`ApplicationContext`는 `BeanFactory`의 모든 기능을 포함하면서 메시지 소스, 이벤트, AOP, 리소스 로딩 등 엔터프라이즈 기능을 더한 상위 컨테이너다.

```text
BeanFactory
(기본 IoC, 지연 로딩)
      |
      | 확장
      v
ApplicationContext
(확장 컨테이너)
      |
      +--> 메시지 소스 (i18n)
      +--> 이벤트 발행/구독
      +--> AOP 통합
      +--> 리소스 로딩
```

- 이 그림은 원문의 두 번째 mermaid 그림을 글자로 옮긴 것이다 — 화살표 다섯(확장 하나 + 아래 넷)으로 원문과 같다.
- "확장"은 원문이 그 화살표에 붙여 둔 라벨이다.
- 아래 네 갈래는 원문 노드 문구 그대로이고, 바로 위 문단이 이를 "메시지 소스, 이벤트, AOP, 리소스 로딩 등 엔터프라이즈 기능"이라 읽는다.

### AOP (관점 지향 프로그래밍)

트랜잭션·로깅·보안 같은 횡단 관심사(cross-cutting concern)를 비즈니스 코드와 분리한다.\
1.x 시절에는 어노테이션이 아니라 XML + 프록시 기반으로 구성했다.

> **횡단 관심사(cross-cutting concern)** — 여러 기능에 가로질러 똑같이 끼어드는 일. 비즈니스 로직마다 따로 적으면 같은 코드가 온 데 흩어진다.\
> 예: 원문이 든 셋이 트랜잭션·로깅·보안이다.

> **프록시(proxy)** — 실제 객체 앞에 서서 호출을 대신 받는 대역 객체. 1.x의 AOP는 원문 표현으로 "XML + 프록시 기반"이다.\
> 예: 아래 XML의 `accountServiceProxy`가 그 대역이고, `target`으로 가리킨 `accountServiceTarget`이 실제 객체다.

```xml
<bean id="loggingAdvice" class="com.example.aop.LoggingInterceptor"/>

<bean id="accountServiceProxy"
      class="org.springframework.aop.framework.ProxyFactoryBean">
    <property name="target"            ref="accountServiceTarget"/>
    <property name="interceptorNames">
        <list>
            <value>loggingAdvice</value>
        </list>
    </property>
</bean>
```

`MethodBeforeAdvice`, `AfterReturningAdvice`, `MethodInterceptor` 등의 어드바이스 인터페이스를 구현하는 방식이었다.

> **어드바이스(advice)** — 끼어들어 실행될 그 공통 처리 자체. 1.x에서는 이것을 인터페이스 구현으로 적었다.\
> 예: 원문이 이름을 든 인터페이스가 `MethodBeforeAdvice`·`AfterReturningAdvice`·`MethodInterceptor`이고, 위 XML의 `loggingAdvice` 빈이 그런 구현을 가리킨다.

### 선언적 트랜잭션 추상화

EJB의 CMT(Container-Managed Transaction)를 대체.\
`PlatformTransactionManager` 인터페이스 하나로 JDBC, JTA, Hibernate 등 백엔드와 무관하게 동일한 방식으로 트랜잭션을 다룬다.\
1.x에서는 `TransactionProxyFactoryBean`으로 선언적 트랜잭션을 적용했다.

> **선언적 트랜잭션** — 트랜잭션을 여닫는 코드를 직접 적지 않고, 어디에 걸지를 설정에 "선언"해 두면 그 대상에 적용되는 방식.\
> 예: 아래 XML의 `<prop key="transfer*">`가 이름이 `transfer`로 시작하는 메서드를 그 대상으로 선언한 자리다.

> **CMT(Container-Managed Transaction)** — 트랜잭션 관리를 컨테이너에 맡기는 EJB 쪽 방식. 원문은 이 절의 기능을 그것의 "대체"라고 적는다.\
> 예: 원문이 이 절에서 CMT 자리에 놓은 것이 `PlatformTransactionManager`와 `TransactionProxyFactoryBean`이다.

```xml
<bean id="transactionManager"
      class="org.springframework.jdbc.datasource.DataSourceTransactionManager">
    <property name="dataSource" ref="dataSource"/>
</bean>

<bean id="accountService"
      class="org.springframework.transaction.interceptor.TransactionProxyFactoryBean">
    <property name="transactionManager" ref="transactionManager"/>
    <property name="target"             ref="accountServiceTarget"/>
    <property name="transactionAttributes">
        <props>
            <prop key="transfer*">PROPAGATION_REQUIRED</prop>
            <prop key="get*">PROPAGATION_REQUIRED,readOnly</prop>
        </props>
    </property>
</bean>
```

원문의 "백엔드와 무관하게"가 이 XML에서 가리키는 자리는 `transactionManager` 빈의 `class`다.

### JDBC 추상화 (JdbcTemplate)

JDBC의 반복 코드(Connection/Statement/ResultSet 열고 닫기, 예외 처리)를 템플릿 메서드 패턴으로 제거.\
체크 예외인 `SQLException`을 런타임 예외 계층(`DataAccessException`)으로 변환해 일관성을 높였다.

바로 위 두 문장을 두 칸에 나눠 놓으면 이렇다.

```text
JDBC를 직접 쓸 때                     JdbcTemplate을 쓸 때
+-------------------------------+    +-------------------------------+
| Connection/Statement/         |    | 템플릿 메서드 패턴으로 제거   |
| ResultSet 열고 닫기, 예외 처리|    |                               |
+-------------------------------+    +-------------------------------+
| 체크 예외 SQLException        |    | 런타임 예외 계층              |
|                               |    | DataAccessException 으로 변환 |
+-------------------------------+    +-------------------------------+
```

- 두 행은 원문이 각각 짝지은 두 문장을 그대로 왼쪽/오른쪽에 나눈 것이다 — 첫 행이 "반복 코드 … 를 템플릿 메서드 패턴으로 제거", 둘째 행이 "체크 예외인 `SQLException`을 런타임 예외 계층(`DataAccessException`)으로 변환".
- 원문이 그 변환에 붙인 목적은 "일관성을 높였다"이다.

> **체크 예외 / 런타임 예외** — 잡거나 다시 던진다고 메서드마다 적어 두도록 컴파일러가 강제하는 예외 / 그런 강제가 없는 예외.\
> 예: 원문이 체크 예외로 든 것이 `SQLException`이고, 런타임 예외 계층으로 든 것이 `DataAccessException`이다.

> **템플릿 메서드 패턴** — 매번 같은 뼈대는 프레임워크 쪽이 쥐고, 매번 달라지는 부분만 넘겨받아 그 자리에 끼워 넣는 방식.\
> 예: 원문이 "제거"했다고 적은 반복 코드(Connection/Statement/ResultSet 열고 닫기, 예외 처리)가 아래 `getBalance`에 보이지 않는다 — `getBalance`가 `jdbcTemplate`에 넘기는 것은 SQL 문자열과 파라미터다.

```java
public class JdbcAccountDao {
    private JdbcTemplate jdbcTemplate;

    public void setDataSource(DataSource ds) {
        this.jdbcTemplate = new JdbcTemplate(ds);
    }

    public int getBalance(long id) {
        return jdbcTemplate.queryForInt(
            "SELECT balance FROM account WHERE id = ?",
            new Object[] { new Long(id) });
    }
}
```

`setDataSource`는 「한눈에」의 조립 담당이 끼워 주는 자리이기도 하다 — 앞의 XML에서 `accountDao` 빈이 받는 `<property name="dataSource" ref="dataSource"/>`가 바로 이 메서드로 들어온다.

### ORM / 데이터 접근 통합

Hibernate, JDO, iBATIS 등을 위한 통합 템플릿(`HibernateTemplate` 등)과 일관된 예외 변환을 제공했다.

### 경량 MVC (Spring Web MVC)

`DispatcherServlet`을 프런트 컨트롤러로 하는 웹 MVC 프레임워크.\
1.x에서는 `Controller` 인터페이스를 구현하고 XML에 핸들러 매핑을 등록하는 방식이었다(어노테이션 기반 컨트롤러는 2.5부터).

> **프런트 컨트롤러(front controller)** — 들어오는 요청을 한 군데서 먼저 받아 알맞은 처리기로 넘기는 입구.\
> 예: 원문이 그 자리에 놓은 것이 `DispatcherServlet`이다.

## 설정 스타일의 변화

이 시대의 주류는 **XML 구성**이다(Java 1.4 기준에서는 어노테이션·제네릭을 쓰지 않았다).\
다만 1.2부터 JDK 1.5 환경에서는 `@Transactional` 어노테이션을 쓸 수 있었다.\
대부분의 빈, 의존성, AOP, 트랜잭션은 XML에 명시적으로 선언되었다.\
DTD 기반 검증을 사용했으며, 이 장황함이 훗날 2.x의 XML 네임스페이스 간소화와 3.x의 Java Config 등장 동기가 된다.

> **DTD(Document Type Definition)** — XML 문서에 어떤 태그가 어떤 자리에 올 수 있는지 규정해 두고 검사하는 옛 방식의 정의 파일.\
> 예: 앞의 빈 정의 XML 맨 위에 있는 `<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN" …>` 줄이 그 DTD를 가리킨다.

**왜 2.x와 3.x가 나왔나** — 원문이 이 절 첫 문단의 마지막 줄에 적어 두었다.

## 마이너 버전별 변화
- 1.0 (2004-03): 첫 정식 릴리스. IoC 컨테이너, AOP, JDBC/트랜잭션 추상화, Web MVC, ORM 통합 등 핵심 모듈 확립.
- 1.1 (2004): 컨테이너·AOP 안정화 및 성능 개선.
- 1.2 (2005): JDK 1.5(Java 5) 런타임 지원 강화 및 **`@Transactional` 등 JDK 1.5 트랜잭션 어노테이션 도입**, AOP 개선. (소스 레벨 메타데이터 기반 Commons Attributes 트랜잭션은 1.0부터 제공됐다.) 이후 어노테이션 시대로 가는 징검다리.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

- **EJB 2.x의 대안**으로 자리 잡으며 "경량 컨테이너(lightweight container)" 패러다임을 대중화했다. 훗날 EJB 3.0(2006)이 의존성 주입·POJO·어노테이션을 받아들인 것은 Spring의 영향이 컸다.
- IoC/DI를 자바 엔터프라이즈의 표준 설계 원칙으로 정착시켰고, **테스트 가능성(testability)**을 1급 관심사로 끌어올렸다.
- JdbcTemplate·트랜잭션 추상화·예외 변환 등 "일관된 추상화 + 템플릿" 패턴은 이후 모든 Spring 모듈의 설계 철학이 되었다.

## 용어 풀이

- **EJB(Enterprise JavaBeans)** — 원문이 "2000년대 초반 자바 엔터프라이즈 개발의 표준"이라 부른 서버 측 컴포넌트 규격. 분산 트랜잭션·보안·영속성을 제공했다.
- **보일러플레이트(boilerplate)** — 하는 일에 비해 매번 똑같이 다시 적어야 하는 판박이 코드. 원문이 EJB의 문제 첫 줄로 든 것이다.
- **디플로이먼트 디스크립터(deployment descriptor)** — 애플리케이션을 서버에 올릴 때 무엇을 어떻게 배치할지 적어 두는 XML 서술 파일.
- **POJO(Plain Old Java Object)** — 특정 프레임워크의 인터페이스를 구현하거나 상속하지 않은 평범한 자바 객체. 원문 표현으로 "어떤 Spring 인터페이스도 구현하지 않는 순수 POJO".
- **IoC(Inversion of Control, 제어의 역전)** — 객체를 언제 만들고 무엇과 이어 붙일지를 내 코드가 아니라 프레임워크가 정하는 것. 원문 정의는 "프레임워크가 객체의 생성과 의존성 연결을 책임지고(IoC), 개발자는 비즈니스 로직(POJO)에 집중한다"이다. `new`를 못 쓴다는 뜻이 아니다 — 원문은 같은 객체를 "컨테이너 없이도 `new`로 만들어 단위 테스트할 수 있다"고 적는다.
- **DI(Dependency Injection, 의존성 주입)** — 쓸 객체를 스스로 찾아오는 대신 밖에서 넣어 주는 것. 이 편의 주입은 XML의 `<property>`와 `<constructor-arg>`로 적힌다.
- **빈(bean)** — 컨테이너가 생명주기를 관리하는 객체. 그 생명주기는 원문 표현으로 "생성·초기화·의존성 주입·소멸"이다.
- **`BeanFactory` / `ApplicationContext`** — 가장 기본적인 IoC 컨테이너(지연 로딩) / 그것을 확장해 메시지 소스, 이벤트 발행, AOP, 리소스 로딩 등을 추가한 상위 컨테이너.
- **지연 로딩(lazy loading)** — 필요해지는 시점까지 만들어 두지 않는 방식. 원문은 이 말을 `BeanFactory`에 붙인다.
- **setter 주입 / 생성자 주입** — 이미 만든 객체의 설정 메서드로 값을 넣는 방식 / 객체를 만들 때 생성자 인자로 넣는 방식. 원문은 생성자 주입도 "지원"한다고 적는다.
- **AOP(관점 지향 프로그래밍)** — 횡단 관심사를 비즈니스 코드와 분리하는 방식. 1.x에서는 원문 표현대로 "어노테이션이 아니라 XML + 프록시 기반으로 구성했다".
- **횡단 관심사(cross-cutting concern)** — 여러 기능에 가로질러 똑같이 끼어드는 일. 원문이 든 셋이 트랜잭션·로깅·보안이다.
- **프록시(proxy)** — 실제 객체 앞에 서서 호출을 대신 받는 대역 객체. 이 편의 실물은 `ProxyFactoryBean`이 만드는 `accountServiceProxy`다.
- **어드바이스(advice)** — 끼어들어 실행될 공통 처리 자체. 1.x에서는 `MethodBeforeAdvice`·`AfterReturningAdvice`·`MethodInterceptor` 같은 인터페이스를 구현해 적었다.
- **선언적 트랜잭션** — 트랜잭션을 여닫는 코드를 직접 적지 않고 어디에 걸지를 설정에 선언해 두는 방식. 1.x에서는 `TransactionProxyFactoryBean`으로 적용했다.
- **CMT(Container-Managed Transaction)** — 트랜잭션 관리를 컨테이너에 맡기는 EJB 쪽 방식. 원문은 이 절의 기능을 그것의 "대체"라고 적는다.
- **`PlatformTransactionManager`** — JDBC, JTA, Hibernate 등 백엔드와 무관하게 동일한 방식으로 트랜잭션을 다루게 하는 인터페이스.
- **체크 예외 / 런타임 예외** — 처리를 컴파일러가 강제하는 예외 / 강제하지 않는 예외. 원문이 든 짝이 `SQLException` → `DataAccessException`이다.
- **템플릿 메서드 패턴** — 같은 뼈대는 프레임워크가 쥐고 달라지는 부분만 넘겨받는 방식. 원문은 JDBC 반복 코드를 이것으로 "제거"했다고 적는다.
- **프런트 컨트롤러(front controller)** — 요청을 한 군데서 먼저 받아 알맞은 처리기로 넘기는 입구. 이 편에서 그 자리는 `DispatcherServlet`이다.
- **DTD(Document Type Definition)** — XML 문서의 구조를 규정하고 검사하는 옛 방식의 정의 파일. 원문은 1.x가 "DTD 기반 검증을 사용했"다고 적는다.

## 참고 출처
- [Spring Framework - Wikipedia](https://en.wikipedia.org/wiki/Spring_Framework)
- [History of Spring Framework and Spring Boot](https://www.quickprogrammingtips.com/spring-boot/history-of-spring-framework-and-spring-boot.html)
- [Introduction to the Spring Framework | TheServerSide](https://www.theserverside.com/news/1364527/Introduction-to-the-Spring-Framework)
- [Spring framework version history - codejava.net](https://www.codejava.net/frameworks/spring/spring-framework-version-history)
- [Spring Framework, History, and Its Structure - DEV Community](https://dev.to/jeanv0/spring-framework-history-and-its-structure-361)
