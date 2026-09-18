# AbstractAutoProxyCreator.wrapIfNecessary

상위: [AbstractAutoProxyCreator.postProcessAfterInitialization](../README.md)

이 빈을 프록시로 감쌀지 판단하고, 감쌀 것이면 만든다. 인프라 클래스와 제외 대상을 먼저 걸러 내고, 적용할 어드바이저를 찾아 하나라도 있으면 프록시를 만든다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAutoProxyCreator.java` L321-L345 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAutoProxyCreator.java#L321-L345))

```java
// AbstractAutoProxyCreator.java L321-L345
protected Object wrapIfNecessary(Object bean, String beanName, Object cacheKey) {
    if (StringUtils.hasLength(beanName) && this.targetSourcedBeans.contains(beanName)) {
        return bean;
    }
    if (Boolean.FALSE.equals(this.advisedBeans.get(cacheKey))) {
        return bean;
    }
    if (isInfrastructureClass(bean.getClass()) || shouldSkip(bean.getClass(), beanName)) {
        this.advisedBeans.put(cacheKey, Boolean.FALSE);
        return bean;
    }

    // Create proxy if we have advice.
    Object[] specificInterceptors = getAdvicesAndAdvisorsForBean(bean.getClass(), beanName, null);
    if (specificInterceptors != DO_NOT_PROXY) {
        this.advisedBeans.put(cacheKey, Boolean.TRUE);
        Object proxy = createProxy(
                bean.getClass(), beanName, specificInterceptors, new SingletonTargetSource(bean));
        this.proxyTypes.put(cacheKey, proxy.getClass());
        return proxy;
    }

    this.advisedBeans.put(cacheKey, Boolean.FALSE);
    return bean;
}
```

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAutoProxyCreator.java` L359-L368 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAutoProxyCreator.java#L359-L368))

```java
// AbstractAutoProxyCreator.java L359-L368
protected boolean isInfrastructureClass(Class<?> beanClass) {
    boolean retVal = Advice.class.isAssignableFrom(beanClass) ||
            Pointcut.class.isAssignableFrom(beanClass) ||
            Advisor.class.isAssignableFrom(beanClass) ||
            AopInfrastructureBean.class.isAssignableFrom(beanClass);
    if (retVal && logger.isTraceEnabled()) {
        logger.trace("Did not attempt to auto-proxy infrastructure class [" + beanClass.getName() + "]");
    }
    return retVal;
}
```

## 동작 흐름

```text
 wrapIfNecessary(bean, beanName, cacheKey)
 |
 +-- L322 targetSourcedBeans 에 있음   (커스텀 TargetSource 로 이미 프록시를 만든 빈)
 |      --> 원본 반환
 |
 +-- L325 advisedBeans 에 "대상 아님" 으로 기록돼 있음 --> 원본 반환
 |
 +-- L328 isInfrastructureClass | shouldSkip
 |      Advice, Pointcut, Advisor, AopInfrastructureBean 구현     --> 대상 아님
 |      AspectJ 자동 프록시라면 원본 애스펙트 빈 자신도 제외
 |      --> "대상 아님" 기록 후 원본 반환
 |
 +-- L334 getAdvicesAndAdvisorsForBean(빈 클래스, 빈 이름, null)
 |      = findEligibleAdvisors 의 결과 (빈 배열이면 DO_NOT_PROXY)
 |
 +-- 어드바이저 있음
 |      L336 "대상" 기록
 |      L337 createProxy(빈 클래스, 이름, 어드바이저들, new SingletonTargetSource(bean))
 |      L339 프록시 클래스 기록
 |      --> 프록시 반환
 |
 +-- 없음 --> "대상 아님" 기록 후 원본 반환
```

1. 어드바이저 선별은 [findEligibleAdvisors](01_AbstractAdvisorAutoProxyCreator.findEligibleAdvisors/README.md)가 한다.
2. 프록시 조립은 [buildProxy](02_AbstractAutoProxyCreator.buildProxy/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 SingletonTargetSource(bean)
      --> 프록시가 호출을 위임할 실제 객체 (타깃)
      --> 호출 경로에서 targetSource.getTarget() 으로 꺼낸다

 DO_NOT_PROXY 판정
      --> @Transactional 이 있는데도 프록시가 없는 경우의 첫 확인 지점
          (인프라 빈으로 분류됐거나, 포인트컷이 맞지 않았거나)

 advisedBeans / proxyTypes 캐시
      --> 같은 빈의 재검사 생략, 타입 예측에 사용
```
