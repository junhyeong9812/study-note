# Advisor

상위: [Spring AOP 프록시](../../README.md) / [spi](../README.md)

어드바이스(무엇을 할지)와 포인트컷(어디에 적용할지)을 한 쌍으로 묶은 단위다. 자동 프록시 생성기는 컨테이너의 `Advisor` 빈을 모아 빈마다 적용 여부를 판정한다.

## 실제 코드

`spring-aop` / `org.springframework.aop` / `Advisor.java` L36-L72 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/Advisor.java#L36-L72))

```java
// Advisor.java L36-L72
public interface Advisor {

    Advice EMPTY_ADVICE = new Advice() {};

    Advice getAdvice();

    default boolean isPerInstance() {
        return true;
    }

}
```

`spring-aop` / `org.springframework.aop` / `PointcutAdvisor.java` L26-L33 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/PointcutAdvisor.java#L26-L33))

```java
// PointcutAdvisor.java L26-L33
public interface PointcutAdvisor extends Advisor {

    Pointcut getPointcut();

}
```

`spring-aop` / `org.springframework.aop` / `Pointcut.java` L33-L53 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/Pointcut.java#L33-L53))

```java
// Pointcut.java L33-L53
public interface Pointcut {

    ClassFilter getClassFilter();

    MethodMatcher getMethodMatcher();

    Pointcut TRUE = TruePointcut.INSTANCE;

}
```

`spring-aop` / `org.springframework.aop` / `MethodMatcher.java` L61-L107 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/MethodMatcher.java#L61-L107))

```java
// MethodMatcher.java L61-L107
public interface MethodMatcher {

    boolean matches(Method method, Class<?> targetClass);

    boolean isRuntime();

    boolean matches(Method method, Class<?> targetClass, @Nullable Object... args);

    MethodMatcher TRUE = TrueMethodMatcher.INSTANCE;

}
```

## 흐름에서 불리는 자리

```text
 프록시 생성
   findCandidateAdvisors     컨테이너의 Advisor 빈 수집
   findAdvisorsThatCanApply  클래스 필터 + 메서드 매처로 이 빈에 맞는 것만
   sortAdvisors              @Order 로 정렬 = 체인 순서 확정
 호출
   getInterceptorsAndDynamicInterceptionAdvice
     메서드 매처를 다시 평가해 인터셉터 목록 구성
     isRuntime() 이면 호출 인자까지 보고 매번 재평가
```

- [findEligibleAdvisors](../../01_AbstractAutoProxyCreator.postProcessAfterInitialization/01_AbstractAutoProxyCreator.wrapIfNecessary/01_AbstractAdvisorAutoProxyCreator.findEligibleAdvisors/README.md)
- [getInterceptorsAndDynamicInterceptionAdvice](../../02_JdkDynamicAopProxy.invoke/01_AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice/README.md)

## 구현 계층

```text
 Advisor
   +-- PointcutAdvisor                        포인트컷으로 적용 범위 지정
   |     +-- DefaultPointcutAdvisor           포인트컷 + 어드바이스 직접 조합
   |     +-- AbstractBeanFactoryPointcutAdvisor
   |     |     +-- BeanFactoryTransactionAttributeSourceAdvisor   @Transactional
   |     +-- AsyncAnnotationAdvisor            @Async
   |     +-- AbstractAspectJAdvisorFactory 가 만드는 InstantiationModelAwarePointcutAdvisor  @Aspect 메서드
   +-- IntroductionAdvisor                    타입 자체를 추가 (믹스인)

 Pointcut
   +-- ClassFilter + MethodMatcher 한 쌍
   +-- AspectJExpressionPointcut              execution(...) 식
   +-- AnnotationMatchingPointcut             애노테이션 기준
   +-- StaticMethodMatcherPointcut            isRuntime() = false
```
