# AsyncExecutionInterceptor.invoke

상위: [Spring 스케줄링과 비동기](../README.md)

`@Async` 메서드 호출을 가로채 실행기에 넘긴다. 호출자는 즉시 반환하고, 실제 실행은 다른 스레드에서 일어난다. AOP 인터셉터이므로 [AOP 프록시](../../aop-proxy/README.md) 흐름 위에서 동작한다.

## 실제 코드

`spring-aop` / `org.springframework.aop.interceptor` / `AsyncExecutionInterceptor.java` L99-L128 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/interceptor/AsyncExecutionInterceptor.java#L99-L128))

```java
// AsyncExecutionInterceptor.java L99-L128
@Override
public @Nullable Object invoke(final MethodInvocation invocation) throws Throwable {
    Class<?> targetClass = (invocation.getThis() != null ? AopUtils.getTargetClass(invocation.getThis()) : null);
    final Method userMethod = BridgeMethodResolver.getMostSpecificMethod(invocation.getMethod(), targetClass);

    AsyncTaskExecutor executor = determineAsyncExecutor(userMethod);
    if (executor == null) {
        throw new IllegalStateException(
                "No executor specified and no default executor set on AsyncExecutionInterceptor either");
    }

    Callable<Object> task = () -> {
        try {
            Object result = invocation.proceed();
            if (result instanceof Future<?> future) {
                return future.get();
            }
        }
        catch (ExecutionException ex) {
            Throwable cause = ex.getCause();
            handleError(cause == null ? ex : cause, userMethod, invocation.getArguments());
        }
        catch (Throwable ex) {
            handleError(ex, userMethod, invocation.getArguments());
        }
        return null;
    };

    return doSubmit(task, executor, userMethod.getReturnType());
}
```

실행기를 고르는 부분이다.

`spring-aop` / `org.springframework.aop.interceptor` / `AsyncExecutionAspectSupport.java` L167-L190 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/interceptor/AsyncExecutionAspectSupport.java#L167-L190))

```java
// AsyncExecutionAspectSupport.java L167-L190
 */
protected @Nullable AsyncTaskExecutor determineAsyncExecutor(Method method) {
    AsyncTaskExecutor executor = this.executors.get(method);
    if (executor == null) {
        Executor targetExecutor;
        String qualifier = getExecutorQualifier(method);
        if (this.embeddedValueResolver != null && StringUtils.hasLength(qualifier)) {
            qualifier = this.embeddedValueResolver.resolveStringValue(qualifier);
        }
        if (StringUtils.hasLength(qualifier)) {
            targetExecutor = findQualifiedExecutor(this.beanFactory, qualifier);
        }
        else {
            targetExecutor = this.defaultExecutor.get();
        }
        if (targetExecutor == null) {
            return null;
        }
        executor = (targetExecutor instanceof AsyncTaskExecutor asyncTaskExecutor ?
                asyncTaskExecutor : new TaskExecutorAdapter(targetExecutor));
        this.executors.put(method, executor);
    }
    return executor;
}
```

제출과 오류 처리다.

`spring-aop` / `org.springframework.aop.interceptor` / `AsyncExecutionAspectSupport.java` L277-L293 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/interceptor/AsyncExecutionAspectSupport.java#L277-L293))

```java
// AsyncExecutionAspectSupport.java L277-L293
 */
protected @Nullable Object doSubmit(Callable<Object> task, AsyncTaskExecutor executor, Class<?> returnType) {
    if (CompletableFuture.class.isAssignableFrom(returnType)) {
        return executor.submitCompletable(task);
    }
    else if (Future.class.isAssignableFrom(returnType)) {
        return executor.submit(task);
    }
    else if (void.class == returnType || "kotlin.Unit".equals(returnType.getName())) {
        executor.submit(task);
        return null;
    }
    else {
        throw new IllegalArgumentException(
                "Invalid return type for async method (only Future and void supported): " + returnType);
    }
}
```

`spring-aop` / `org.springframework.aop.interceptor` / `AsyncExecutionAspectSupport.java` L306-L321 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/interceptor/AsyncExecutionAspectSupport.java#L306-L321))

```java
// AsyncExecutionAspectSupport.java L306-L321
 */
protected void handleError(Throwable ex, Method method, @Nullable Object... params) throws Exception {
    if (Future.class.isAssignableFrom(method.getReturnType())) {
        ReflectionUtils.rethrowException(ex);
    }
    else {
        // Could not transmit the exception to the caller with default executor
        try {
            this.exceptionHandler.obtain().handleUncaughtException(ex, method, params);
        }
        catch (Throwable ex2) {
            logger.warn("Exception handler for async method '" + method.toGenericString() +
                    "' threw unexpected exception itself", ex2);
        }
    }
}
```

## 동작 흐름

```text
 invoke(invocation)
 |
 | L101 타깃 클래스와 가장 구체적인 메서드 확정 (브리지 메서드 해소)
 |
 | L104 determineAsyncExecutor(userMethod)
 |        메서드별 캐시 조회
 |        @Async("qualifier") 가 있으면 그 이름의 Executor 빈
 |        없으면 기본 실행기 (AsyncConfigurer 또는 taskExecutor 빈)
 |        Executor 이지만 AsyncTaskExecutor 가 아니면 어댑터로 감싼다
 |        아무것도 없으면 IllegalStateException
 |
 | L110 Callable 로 감싼다
 |        invocation.proceed()  = 타깃 메서드 실행 (다른 스레드에서)
 |        결과가 Future 면 get() 으로 값을 꺼낸다
 |        예외는 handleError 로
 |
 +-- L127 doSubmit(task, executor, 반환 타입)
        CompletableFuture --> executor.submitCompletable(task)
        Future            --> executor.submit(task)
        void / Unit       --> executor.submit(task) 후 null 반환
        그 밖             --> IllegalArgumentException
                              (@Async 는 Future 또는 void 만 지원)

 handleError(ex, method, params)
   반환 타입이 Future --> 예외를 그대로 던져 Future 에 담기게 한다
   그 밖              --> AsyncUncaughtExceptionHandler 로 넘긴다
                          (기본 구현은 로그만 남긴다)
```

## 결과가 쓰이는 곳

```text
 호출자가 받는 값
      void             --> null (즉시 반환)
      Future/CompletableFuture --> 아직 완료되지 않은 핸들

 예외
      void 반환이면 호출자에게 전달되지 않는다
        --> AsyncUncaughtExceptionHandler 를 등록하지 않으면 로그로만 남는다
      Future 반환이면 get() 호출 시점에 ExecutionException 으로 드러난다

 스레드 전환
      --> ThreadLocal 기반 문맥(트랜잭션, 보안, 요청)이 전파되지 않는다
      --> TaskDecorator 로 복사하거나, 필요한 값을 인자로 넘겨야 한다

 자기 호출
      --> 프록시를 거치지 않으므로 비동기로 동작하지 않는다
          (@Scheduled 와 다른 지점)
```
