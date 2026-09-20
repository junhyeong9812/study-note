# 메서드 보안

`@PreAuthorize` 가 붙은 메서드를 부르면 무슨 일이 일어나는가다. 웹 요청이 아니라 **메서드 호출**이 보호 대상이고, 장치도 필터가 아니라 **AOP 프록시**다. 인가 판정 자체는 [인가](../authorization/README.md) 흐름과 같은 `AuthorizationManager` 계약을 쓴다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 어드바이저와 판정 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [기동 시점]

 @EnableMethodSecurity
 |
 +-- [01] MethodSecuritySelector.selectImports
          어떤 설정 클래스를 들일지 고른다
          prePostEnabled 가 기본 true 라
          PrePostMethodSecurityConfiguration 이 들어온다
          그 설정이 인터셉터를 @Bean 으로 등록한다

 [호출 시점]

 service.doSomething()   <- 실제로는 프록시의 메서드
 |
 +-- Spring AOP 의 인터셉터 체인
 |
 +-- [02] AuthorizationManagerBeforeMethodInterceptor.invoke
 |        attemptAuthorization 에 그대로 위임한다
 |        판정하고, 거부면 핸들러로, 허용이면 원래 메서드로
 |
 +-- [03] PreAuthorizeAuthorizationManager.authorize
          @PreAuthorize 의 표현식을 꺼내 평가한다
          애노테이션이 없으면 null 을 돌려준다
```

```text
 인가와 같은 계약, 다른 대상

 웹 인가     AuthorizationManager<HttpServletRequest>
 메서드 보안 AuthorizationManager<MethodInvocation>

 인터페이스가 제네릭이라 같은 계약을 쓴다
 판정 결과도 같은 AuthorizationResult 다

 다른 것은 "무엇을 보호하는가"와 "어떻게 끼어드는가"다
   웹     필터 체인의 한 칸
   메서드 AOP 프록시의 인터셉터 체인
```

```text
 인터셉터가 곧 어드바이저다

 AuthorizationAdvisor extends
     Ordered, MethodInterceptor, PointcutAdvisor, AopInfrastructureBean

 보통 AOP 에서는 어드바이스와 어드바이저가 따로다
 여기서는 한 클래스가 둘을 겸한다
   PointcutAdvisor  어디에 붙일지 (포인트컷)
   MethodInterceptor 붙어서 무엇을 할지
   Ordered          여러 보안 인터셉터 사이의 순서
   AopInfrastructureBean 이 빈 자신은 프록시 대상이 아니라는 표시
```

```text
 Spring Framework 의 AOP 흐름과 만나는 지점

 빈 생성 -> AbstractAutoProxyCreator 가 Advisor 를 찾아 프록시를 씌운다
        -> 그 Advisor 중 하나가 이 인터셉터다
        -> 호출 시 인터셉터 체인이 돌면서 여기에 닿는다

 즉 @Transactional 이 도는 자리와 같은 구조다
 다른 것은 인터셉터가 하는 일뿐이다
```

## 어디에서 쓰이는가

```text
 [인가] 같은 AuthorizationManager 계약과 AuthorizationResult 를 쓴다
 [보안 컨텍스트] 판정의 입력인 Authentication 을 같은 ThreadLocal 에서 꺼낸다
 [AOP 프록시] 프록시가 씌워지고 인터셉터 체인이 도는 것은 그쪽 흐름이다
 [빈 생성] 인터셉터가 @Bean 으로 등록되어야 프록시가 만들어진다
```

판정 계약의 뿌리는 [인가](../authorization/README.md), 프록시가 씌워지는 과정은 Spring Framework 쪽 [AOP 프록시](../../../spring-framework/architecture/aop-proxy/README.md) 흐름에 있다.

## 단계

1. [MethodSecuritySelector.selectImports](01_MethodSecuritySelector.selectImports/README.md)가 설정 클래스를 고른다.
2. [AuthorizationManagerBeforeMethodInterceptor.invoke](02_AuthorizationManagerBeforeMethodInterceptor.invoke/README.md)가 호출을 가로챈다.
3. [PreAuthorizeAuthorizationManager.authorize](03_PreAuthorizeAuthorizationManager.authorize/README.md)가 표현식을 평가한다.

## 결과가 쓰이는 곳

```text
 판정 결과
      --> 허용이면 원래 메서드가 실행된다
      --> 거부면 원래 메서드가 아예 실행되지 않는다
      --> 웹 인가와 달리 예외를 던질지 다른 값을 돌려줄지 고를 수 있다

 null 결과
      --> 애노테이션이 없다는 뜻이다
      --> 인터셉터가 이것을 거부로 보지 않고 그냥 통과시킨다

 프록시를 거치지 않는 호출
      --> 같은 객체 안에서 this.otherMethod() 로 부르면
          프록시를 거치지 않아 보안이 적용되지 않는다
      --> AOP 프록시 방식 일반의 한계다 (Spring Framework 쪽 사실이다)

 인터셉터 순서
      --> AuthorizationInterceptorsOrder 가 정한다
      --> preFilter -> preAuthorize -> ... -> postAuthorize -> postFilter
```

## 다루지 않는 것

`@PostAuthorize` / `@PreFilter` / `@PostFilter` 의 처리(각각 별도 인터셉터), `@Secured` 와 JSR-250(`@RolesAllowed`) 경로, SpEL 평가의 세부(`DefaultMethodSecurityExpressionHandler`, `MethodSecurityExpressionRoot`), `AuthorizationProxyFactory` 와 반환값 프록시, 관측 연동, 리액티브 메서드 보안은 같은 뼈대의 곁가지라 요약만 했다. AOP 프록시가 만들어지는 과정 자체도 Spring Framework 소속이라 범위 밖이다.

## 하위 메서드

- [01 MethodSecuritySelector.selectImports](01_MethodSecuritySelector.selectImports/README.md)
- [02 AuthorizationManagerBeforeMethodInterceptor.invoke](02_AuthorizationManagerBeforeMethodInterceptor.invoke/README.md)
- [03 PreAuthorizeAuthorizationManager.authorize](03_PreAuthorizeAuthorizationManager.authorize/README.md)
- [spi](spi/README.md) — 인가 어드바이저, 거부 핸들러
