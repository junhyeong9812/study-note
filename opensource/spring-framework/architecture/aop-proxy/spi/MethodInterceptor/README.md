# MethodInterceptor

상위: [Spring AOP 프록시](../../README.md) / [spi](../README.md)

어드바이스의 실행 형태다. 호출을 가로채 앞뒤로 일하고, `invocation.proceed()`로 다음 단계로 넘긴다. 다른 어드바이스 종류(`@Before`, `@AfterReturning` 등)도 결국 이 인터페이스의 구현으로 변환되어 체인에 들어간다.

## 실제 코드

`spring-aop` / `org.aopalliance.aop` / `Advice.java` L26-L28 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/aopalliance/aop/Advice.java#L26-L28))

```java
// Advice.java L26-L28
public interface Advice {

}
```

`spring-aop` / `org.aopalliance.intercept` / `MethodInterceptor.java` L45-L59 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/aopalliance/intercept/MethodInterceptor.java#L45-L59))

```java
// MethodInterceptor.java L45-L59
public interface MethodInterceptor extends Interceptor {

    @Nullable Object invoke(MethodInvocation invocation) throws Throwable;

}
```

`spring-aop` / `org.aopalliance.intercept` / `MethodInvocation.java` L31-L41 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/aopalliance/intercept/MethodInvocation.java#L31-L41))

```java
// MethodInvocation.java L31-L41
public interface MethodInvocation extends Invocation {

    Method getMethod();

}
```

## 흐름에서 불리는 자리

```text
 호출 경로
   ReflectiveMethodInvocation.proceed
     체인에서 꺼낸 MethodInterceptor.invoke(this) 호출
     인터셉터가 proceed() 를 다시 부르면 다음 인터셉터로
     아무도 proceed() 를 부르지 않으면 타깃은 실행되지 않는다
```

- [ReflectiveMethodInvocation.proceed](../../02_JdkDynamicAopProxy.invoke/02_ReflectiveMethodInvocation.proceed/README.md)
- [getInterceptorsAndDynamicInterceptionAdvice](../../02_JdkDynamicAopProxy.invoke/01_AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice/README.md)

## 구현 계층

```text
 Advice (마커)
   +-- MethodInterceptor (AOP Alliance)
   |     +-- ExposeInvocationInterceptor       현재 MethodInvocation 을 ThreadLocal 노출 (체인 0번)
   |     +-- TransactionInterceptor            @Transactional
   |     +-- AsyncExecutionInterceptor         @Async
   |     +-- CacheInterceptor                  @Cacheable
   |     +-- AspectJAroundAdvice               @Around
   |     +-- MethodBeforeAdviceInterceptor     @Before 어드바이스를 감싼 것
   |     +-- AfterReturningAdviceInterceptor / ThrowsAdviceInterceptor
   +-- MethodBeforeAdvice / AfterReturningAdvice / ThrowsAdvice
         --> AdvisorAdapterRegistry 가 MethodInterceptor 로 변환해 체인에 넣는다
```
