# AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice

상위: [JdkDynamicAopProxy.invoke](../README.md)

호출된 메서드 하나에 적용할 인터셉터 목록을 만든다. 어드바이저의 포인트컷을 메서드 단위로 평가해 통과한 것만 남기고, 결과를 캐시한다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework` / `AdvisedSupport.java` L516-L538 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/AdvisedSupport.java#L516-L538))

```java
// AdvisedSupport.java L516-L538
public List<Object> getInterceptorsAndDynamicInterceptionAdvice(Method method, @Nullable Class<?> targetClass) {
    List<Object> cachedInterceptors;
    if (this.methodCache != null) {
        // Method-specific cache for method-specific pointcuts
        MethodCacheKey cacheKey = new MethodCacheKey(method);
        cachedInterceptors = this.methodCache.get(cacheKey);
        if (cachedInterceptors == null) {
            cachedInterceptors = this.advisorChainFactory.getInterceptorsAndDynamicInterceptionAdvice(
                    this, method, targetClass);
            this.methodCache.put(cacheKey, cachedInterceptors);
        }
    }
    else {
        // Shared cache since there are no method-specific advisors (see below).
        cachedInterceptors = this.cachedInterceptors;
        if (cachedInterceptors == null) {
            cachedInterceptors = this.advisorChainFactory.getInterceptorsAndDynamicInterceptionAdvice(
                    this, method, targetClass);
            this.cachedInterceptors = cachedInterceptors;
        }
    }
    return cachedInterceptors;
}
```

`spring-aop` / `org.springframework.aop.framework` / `DefaultAdvisorChainFactory.java` L58-L112 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/DefaultAdvisorChainFactory.java#L58-L112))

```java
// DefaultAdvisorChainFactory.java L58-L112
public List<Object> getInterceptorsAndDynamicInterceptionAdvice(
        Advised config, Method method, @Nullable Class<?> targetClass) {

    // This is somewhat tricky... We have to process introductions first,
    // but we need to preserve order in the ultimate list.
    AdvisorAdapterRegistry registry = GlobalAdvisorAdapterRegistry.getInstance();
    Advisor[] advisors = config.getAdvisors();
    List<Object> interceptorList = new ArrayList<>(advisors.length);
    Class<?> actualClass = (targetClass != null ? targetClass : method.getDeclaringClass());
    Boolean hasIntroductions = null;

    for (Advisor advisor : advisors) {
        if (advisor instanceof PointcutAdvisor pointcutAdvisor) {
            // Add it conditionally.
            if (config.isPreFiltered() || pointcutAdvisor.getPointcut().getClassFilter().matches(actualClass)) {
                MethodMatcher mm = pointcutAdvisor.getPointcut().getMethodMatcher();
                boolean match;
                if (mm instanceof IntroductionAwareMethodMatcher iamm) {
                    if (hasIntroductions == null) {
                        hasIntroductions = hasMatchingIntroductions(advisors, actualClass);
                    }
                    match = iamm.matches(method, actualClass, hasIntroductions);
                }
                else {
                    match = mm.matches(method, actualClass);
                }
                if (match) {
                    MethodInterceptor[] interceptors = registry.getInterceptors(advisor);
                    if (mm.isRuntime()) {
                        // Creating a new object instance in the getInterceptors() method
                        // isn't a problem as we normally cache created chains.
                        for (MethodInterceptor interceptor : interceptors) {
                            interceptorList.add(new InterceptorAndDynamicMethodMatcher(interceptor, mm));
                        }
                    }
                    else {
                        interceptorList.addAll(Arrays.asList(interceptors));
                    }
                }
            }
        }
        else if (advisor instanceof IntroductionAdvisor ia) {
            if (config.isPreFiltered() || ia.getClassFilter().matches(actualClass)) {
                Interceptor[] interceptors = registry.getInterceptors(advisor);
                interceptorList.addAll(Arrays.asList(interceptors));
            }
        }
        else {
            Interceptor[] interceptors = registry.getInterceptors(advisor);
            interceptorList.addAll(Arrays.asList(interceptors));
        }
    }

    return interceptorList;
}
```

## 동작 흐름

```text
 getInterceptorsAndDynamicInterceptionAdvice(method, targetClass)
 |
 +-- 메서드별 포인트컷이 있는 설정 --> methodCache 에서 조회, 없으면 만들어 저장
 +-- 메서드 단위 구분이 필요 없는 설정 --> 설정 전체에 하나의 캐시
 |
 +-- 캐시 미스일 때 DefaultAdvisorChainFactory 가 목록 구성
       for advisor in advised.getAdvisors()
         |
         +-- PointcutAdvisor
         |     클래스 필터 검사 (preFiltered 면 생략)
         |     메서드 매처 검사
         |       매칭 실패 --> 제외
         |       매칭 성공 + isRuntime() 이 false
         |         --> 인터셉터를 그대로 목록에 추가 (정적 매칭)
         |       매칭 성공 + isRuntime() 이 true
         |         --> InterceptorAndDynamicMethodMatcher 로 감싸 추가
         |             (호출마다 인자까지 보고 다시 판정)
         |
         +-- IntroductionAdvisor
         |     클래스 필터만 검사 --> 인터셉터 추가
         |
         +-- 그 밖 --> 인터셉터 추가

       어드바이스 -> MethodInterceptor 변환은 AdvisorAdapterRegistry 가 한다
         @Before  --> MethodBeforeAdviceInterceptor
         @After   --> AfterReturningAdviceInterceptor 등
         @Around  --> 이미 MethodInterceptor
```

## 결과가 쓰이는 곳

```text
 반환 목록
      +-- 비어 있음 --> invoke / intercept 의 지름길 (타깃 직접 호출)
      +-- 있음      --> ReflectiveMethodInvocation 의 체인

 캐시
      --> 같은 메서드의 두 번째 호출부터는 포인트컷 평가 없음
      --> 어드바이스 구성이 바뀌면 adviceChanged() 가 캐시를 비운다

 목록 순서
      --> findEligibleAdvisors 의 정렬 결과 그대로
      --> proceed() 가 이 순서대로 실행하고, 역순으로 되돌아 나온다
```
