# AbstractAdvisorAutoProxyCreator.findEligibleAdvisors

상위: [AbstractAutoProxyCreator.wrapIfNecessary](../README.md)

컨테이너에 등록된 모든 [Advisor](../../../spi/Advisor/README.md) 중에서 이 빈에 실제로 적용될 것만 고른다. 후보 수집, 포인트컷 매칭, 보강, 정렬의 네 단계다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAdvisorAutoProxyCreator.java` L96-L110 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAdvisorAutoProxyCreator.java#L96-L110))

```java
// AbstractAdvisorAutoProxyCreator.java L96-L110
protected List<Advisor> findEligibleAdvisors(Class<?> beanClass, String beanName) {
    List<Advisor> candidateAdvisors = findCandidateAdvisors();
    List<Advisor> eligibleAdvisors = findAdvisorsThatCanApply(candidateAdvisors, beanClass, beanName);
    extendAdvisors(eligibleAdvisors);
    if (!eligibleAdvisors.isEmpty()) {
        try {
            eligibleAdvisors = sortAdvisors(eligibleAdvisors);
        }
        catch (BeanCreationException ex) {
            throw new AopConfigException("Advisor sorting failed with unexpected bean creation, probably due " +
                    "to custom use of the Ordered interface. Consider using the @Order annotation instead.", ex);
        }
    }
    return eligibleAdvisors;
}
```

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAdvisorAutoProxyCreator.java` L116-L119 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAdvisorAutoProxyCreator.java#L116-L119))

```java
// AbstractAdvisorAutoProxyCreator.java L116-L119
protected List<Advisor> findCandidateAdvisors() {
    Assert.state(this.advisorRetrievalHelper != null, "No BeanFactoryAdvisorRetrievalHelper available");
    return this.advisorRetrievalHelper.findAdvisorBeans();
}
```

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAdvisorAutoProxyCreator.java` L130-L140 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAdvisorAutoProxyCreator.java#L130-L140))

```java
// AbstractAdvisorAutoProxyCreator.java L130-L140
protected List<Advisor> findAdvisorsThatCanApply(
        List<Advisor> candidateAdvisors, Class<?> beanClass, String beanName) {

    ProxyCreationContext.setCurrentProxiedBeanName(beanName);
    try {
        return AopUtils.findAdvisorsThatCanApply(candidateAdvisors, beanClass);
    }
    finally {
        ProxyCreationContext.setCurrentProxiedBeanName(null);
    }
}
```

AspectJ 자동 프록시에서는 보강 단계가 인터셉터 하나를 목록 맨 앞에 넣는다.

`spring-aop` / `org.springframework.aop.aspectj.autoproxy` / `AspectJAwareAdvisorAutoProxyCreator.java` L98-L100 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/aspectj/autoproxy/AspectJAwareAdvisorAutoProxyCreator.java#L98-L100))

```java
// AspectJAwareAdvisorAutoProxyCreator.java L98-L100
protected void extendAdvisors(List<Advisor> candidateAdvisors) {
    AspectJProxyUtils.makeAdvisorChainAspectJCapableIfNecessary(candidateAdvisors);
}
```

`spring-aop` / `org.springframework.aop.aspectj` / `AspectJProxyUtils.java` L49-L67 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/aspectj/AspectJProxyUtils.java#L49-L67))

```java
// AspectJProxyUtils.java L49-L67
public static boolean makeAdvisorChainAspectJCapableIfNecessary(List<Advisor> advisors) {
    // Don't add advisors to an empty list; may indicate that proxying is just not required
    if (!advisors.isEmpty()) {
        boolean foundAspectJAdvice = false;
        for (Advisor advisor : advisors) {
            // Be careful not to get the Advice without a guard, as this might eagerly
            // instantiate a non-singleton AspectJ aspect...
            if (isAspectJAdvice(advisor)) {
                foundAspectJAdvice = true;
                break;
            }
        }
        if (foundAspectJAdvice && !advisors.contains(ExposeInvocationInterceptor.ADVISOR)) {
            advisors.add(0, ExposeInvocationInterceptor.ADVISOR);
            return true;
        }
    }
    return false;
}
```

## 동작 흐름

```text
 findEligibleAdvisors(beanClass, beanName)
 |
 | [1] L97 findCandidateAdvisors
 |       BeanFactoryAdvisorRetrievalHelper 가 컨테이너의 Advisor 타입 빈을 모두 조회
 |       AspectJ 모드면 @Aspect 클래스의 어드바이스 메서드도 Advisor 로 변환해 추가
 |
 | [2] L98 findAdvisorsThatCanApply
 |       ProxyCreationContext 에 현재 빈 이름을 걸고
 |       AopUtils.findAdvisorsThatCanApply
 |         IntroductionAdvisor  --> 클래스 필터만 검사
 |         PointcutAdvisor      --> 클래스 필터 + 메서드 하나라도 매칭되는지 검사
 |       = 이 빈의 어떤 메서드에도 맞지 않으면 탈락
 |
 | [3] L99 extendAdvisors
 |       AspectJ 어드바이스가 하나라도 있으면
 |       ExposeInvocationInterceptor.ADVISOR 를 목록 0번에 삽입
 |       --> 어드바이스가 현재 MethodInvocation 을 ThreadLocal 로 얻을 수 있게 됨
 |
 +-- [4] L102 sortAdvisors
         @Order / Ordered / @Aspect 선언 순서로 정렬
         = 인터셉터 체인의 실행 순서가 여기서 확정된다
```

## 결과가 쓰이는 곳

```text
 반환한 어드바이저 목록
      +-- 비어 있음 --> DO_NOT_PROXY --> 프록시를 만들지 않음
      +-- 있음      --> buildProxy 의 proxyFactory.addAdvisors
                        --> 프록시 설정(AdvisedSupport)에 저장
                        --> 호출 시 getInterceptorsAndDynamicInterceptionAdvice 의 입력

 [4] 의 정렬 순서
      --> proceed() 가 도는 순서
      --> @Transactional 과 커스텀 어드바이스의 중첩 순서를 결정
          (예: 트랜잭션 안에서 로깅할지, 밖에서 할지)

 [3] 의 ExposeInvocationInterceptor
      --> 체인의 첫 인터셉터
      --> @Around 어드바이스의 ProceedingJoinPoint, @annotation 바인딩 등이 이것에 의존
```
