# Spring AOP 프록시

`@Transactional`이나 `@Async`가 붙은 빈이 프록시로 바뀌고, 그 프록시를 호출했을 때 어드바이스가 실행되는 흐름을 위에서 아래로 따라간다. 두 갈래다. 하나는 빈이 만들어질 때 프록시를 **씌우는** 경로, 다른 하나는 메서드를 **호출할 때** 인터셉터 체인이 도는 경로다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 이 과정의 확장 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] 프록시를 씌우는 경로 (빈 생성 중)

 initializeBean 의 초기화 후 후처리기
 |
 +-- [01] AbstractAutoProxyCreator.postProcessAfterInitialization
        |
        +-- [01-01] wrapIfNecessary
               |
               +-- [01-01-01] findEligibleAdvisors     이 빈에 붙을 어드바이저 선별
               |                 후보 수집 --> 포인트컷 매칭 --> 정렬
               |                 = 비어 있으면 프록시를 만들지 않는다
               |
               +-- [01-01-02] buildProxy
                      ProxyFactory 구성 (인터페이스, 어드바이저, 타깃)
                      |
                      +-- [01-01-02-01] DefaultAopProxyFactory.createAopProxy
                             인터페이스 기반 --> JdkDynamicAopProxy
                             클래스 기반     --> ObjenesisCglibAopProxy
                      = 프록시 객체 반환 --> 이 객체가 컨테이너의 빈이 된다

 [B] 호출할 때의 경로

 프록시.someMethod()
 |
 +-- [02] JdkDynamicAopProxy.invoke      (JDK 프록시)
 +-- [03] CglibAopProxy.intercept        (CGLIB 프록시)
        공통으로
        |
        +-- [02-01] getInterceptorsAndDynamicInterceptionAdvice
        |      이 메서드에 적용할 인터셉터 목록 (메서드 단위 캐시)
        |      비어 있으면 --> 타깃 메서드를 바로 리플렉션 호출
        |
        +-- [02-02] ReflectiveMethodInvocation.proceed
               인터셉터를 하나씩 꺼내 invoke
               마지막에 invokeJoinpoint --> 타깃의 실제 메서드
```

## 단계

1. [AbstractAutoProxyCreator.postProcessAfterInitialization](01_AbstractAutoProxyCreator.postProcessAfterInitialization/README.md)이 빈 생성의 마지막에 끼어들어 프록시를 씌운다.
2. [JdkDynamicAopProxy.invoke](02_JdkDynamicAopProxy.invoke/README.md)가 JDK 프록시의 호출을 받아 인터셉터 체인을 돌린다.
3. [CglibAopProxy.DynamicAdvisedInterceptor.intercept](03_CglibAopProxy.intercept/README.md)가 CGLIB 프록시에서 같은 일을 한다.

## 어디에서 이어지는가

```text
 [빈 생성] initializeBean [4] 초기화 후 후처리기
     --> AbstractAutoProxyCreator 가 여기서 [A] 를 실행
     --> 반환된 프록시가 싱글톤 캐시에 들어가고, 다른 빈에도 이것이 주입된다

 [컨테이너 기동] @EnableTransactionManagement / @EnableAspectJAutoProxy
     --> ImportSelector / ImportBeanDefinitionRegistrar 가
         AutoProxyCreator 빈 정의를 등록 --> registerBeanPostProcessors 에서 처리기로 등록
```

시작점은 [빈 생성](../bean-creation/README.md)의 [initializeBean](../bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/03_AbstractAutowireCapableBeanFactory.initializeBean/README.md)이다.

## 다루지 않는 것

AspectJ 포인트컷 식을 파싱하고 매칭하는 내부(`AspectJExpressionPointcut`)와, `@Transactional` 어드바이스가 트랜잭션을 여닫는 내부는 각각 별도 주제다. 후자는 [트랜잭션](../transaction/README.md) 흐름에서 다룬다.

## 하위 메서드

- [01 AbstractAutoProxyCreator.postProcessAfterInitialization](01_AbstractAutoProxyCreator.postProcessAfterInitialization/README.md)
- [02 JdkDynamicAopProxy.invoke](02_JdkDynamicAopProxy.invoke/README.md)
- [03 CglibAopProxy.intercept](03_CglibAopProxy.intercept/README.md)
- [spi](spi/README.md) — 어드바이저, 어드바이스, 타깃 소스
