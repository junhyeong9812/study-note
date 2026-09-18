# AbstractAutoProxyCreator.buildProxy

상위: [AbstractAutoProxyCreator.wrapIfNecessary](../README.md)

`ProxyFactory`를 구성해 프록시 객체를 만든다. 인터페이스 기반으로 갈지 클래스 기반으로 갈지 정하고, 어드바이저와 타깃을 붙인 뒤 실제 생성을 위임한다.

## 실제 코드

진입점은 얇은 위임이다.

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAutoProxyCreator.java` L428-L432 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAutoProxyCreator.java#L428-L432))

```java
// AbstractAutoProxyCreator.java L428-L432
protected Object createProxy(Class<?> beanClass, @Nullable String beanName,
        Object @Nullable [] specificInterceptors, TargetSource targetSource) {

    return buildProxy(beanClass, beanName, specificInterceptors, targetSource, false);
}
```

본체는 다음과 같다.

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAutoProxyCreator.java` L440-L494 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAutoProxyCreator.java#L440-L494))

```java
// AbstractAutoProxyCreator.java L440-L494
private Object buildProxy(Class<?> beanClass, @Nullable String beanName,
        Object @Nullable [] specificInterceptors, TargetSource targetSource, boolean classOnly) {

    if (this.beanFactory instanceof ConfigurableListableBeanFactory clbf) {
        AutoProxyUtils.exposeTargetClass(clbf, beanName, beanClass);
    }

    ProxyFactory proxyFactory = new ProxyFactory();
    proxyFactory.copyFrom(this);
    proxyFactory.setFrozen(false);

    if (shouldProxyTargetClass(beanClass, beanName)) {
        proxyFactory.setProxyTargetClass(true);
    }
    else {
        Class<?>[] ifcs = (this.beanFactory instanceof ConfigurableListableBeanFactory clbf ?
                AutoProxyUtils.determineExposedInterfaces(clbf, beanName) : null);
        if (ifcs != null) {
            proxyFactory.setProxyTargetClass(false);
            for (Class<?> ifc : ifcs) {
                proxyFactory.addInterface(ifc);
            }
        }
        if (ifcs != null ? ifcs.length == 0 : !proxyFactory.isProxyTargetClass()) {
            evaluateProxyInterfaces(beanClass, proxyFactory);
        }
    }

    if (proxyFactory.isProxyTargetClass()) {
        // Explicit handling of JDK proxy targets and lambdas (for introduction advice scenarios)
        if (Proxy.isProxyClass(beanClass) || ClassUtils.isLambdaClass(beanClass)) {
            // Must allow for introductions; can't just set interfaces to the proxy's interfaces only.
            for (Class<?> ifc : beanClass.getInterfaces()) {
                proxyFactory.addInterface(ifc);
            }
        }
    }

    Advisor[] advisors = buildAdvisors(beanName, specificInterceptors);
    proxyFactory.addAdvisors(advisors);
    proxyFactory.setTargetSource(targetSource);
    customizeProxyFactory(proxyFactory);

    proxyFactory.setFrozen(isFrozen());
    if (advisorsPreFiltered()) {
        proxyFactory.setPreFiltered(true);
    }

    // Use original ClassLoader if bean class not locally loaded in overriding class loader
    ClassLoader classLoader = getProxyClassLoader();
    if (classLoader instanceof SmartClassLoader smartClassLoader && classLoader != beanClass.getClassLoader()) {
        classLoader = smartClassLoader.getOriginalClassLoader();
    }
    return (classOnly ? proxyFactory.getProxyClass(classLoader) : proxyFactory.getProxy(classLoader));
}
```

## 동작 흐름

```text
 buildProxy(beanClass, beanName, specificInterceptors, targetSource, classOnly)
 |
 | L443 exposeTargetClass    빈 정의에 실제 타깃 클래스를 속성으로 기록
 |                            (주입 대상 타입 판정이 프록시가 아닌 타깃 기준이 되도록)
 | L447 ProxyFactory 생성, 현재 설정 복사
 |
 +-- L451 프록시 방식 결정
 |      shouldProxyTargetClass = true      (@EnableAspectJAutoProxy(proxyTargetClass = true) 등)
 |        --> 클래스 기반으로 고정
 |      아니면
 |        빈 정의에 노출할 인터페이스 정보가 있으면 그 인터페이스만 사용
 |        없으면 evaluateProxyInterfaces
 |          타깃이 구현한 인터페이스 중 "합리적인" 것이 있으면 인터페이스 기반
 |          없으면 proxyTargetClass = true 로 전환
 |
 | L468 클래스 기반인데 타깃이 이미 JDK 프록시이거나 람다
 |        --> 그 인터페이스들을 프록시에도 추가
 |
 | L478 buildAdvisors(beanName, specificInterceptors)
 |        공통 인터셉터 + 이 빈 전용 인터셉터를 Advisor 로 변환해 합침
 | L479 addAdvisors / L480 setTargetSource / L481 customizeProxyFactory
 | L483 setFrozen / L484 preFiltered 표시 (이미 포인트컷 매칭을 마친 어드바이저임)
 |
 +-- L493 proxyFactory.getProxy(classLoader)
        classOnly 면 클래스만 (AOT 용)
```

1. 실제 프록시 종류 선택은 [DefaultAopProxyFactory.createAopProxy](01_DefaultAopProxyFactory.createAopProxy/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 ProxyFactory (AdvisedSupport)
      --> 프록시 객체 안에 그대로 보관된다
      --> 호출 시 advised.getInterceptorsAndDynamicInterceptionAdvice 의 원천
      --> Advised 인터페이스로 캐스팅하면 런타임에 조회/수정 가능

 preFiltered = true
      --> 호출 시 클래스 필터 재검사를 건너뛴다 (메서드 매처만 본다)

 노출 인터페이스 목록
      --> JDK 프록시라면 이 인터페이스들로만 캐스팅 가능
          구체 클래스로 주입받으려 하면 실패 (프록시가 그 타입이 아님)
```
