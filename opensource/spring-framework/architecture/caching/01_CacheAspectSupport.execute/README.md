# CacheAspectSupport.execute

상위: [Spring 캐시 추상화](../README.md)

캐시 연산의 전체 순서를 정하는 곳이다. 조회 전 제거, 조회, 실행, 저장, 실행 후 제거의 다섯 마디로 되어 있다. 한 메서드에 여러 애노테이션이 붙어도 여기서 한 번에 처리된다.

## 진입: CacheInterceptor.invoke

`spring-context` / `org.springframework.cache.interceptor` / `CacheInterceptor.java` L47-L69 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheInterceptor.java#L47-L69))

```java
// CacheInterceptor.java L47-L69

@Override
public @Nullable Object invoke(final MethodInvocation invocation) throws Throwable {
    Method method = invocation.getMethod();

    CacheOperationInvoker aopAllianceInvoker = () -> {
        try {
            return invocation.proceed();
        }
        catch (Throwable ex) {
            throw new CacheOperationInvoker.ThrowableWrapper(ex);
        }
    };

    Object target = invocation.getThis();
    Assert.state(target != null, "Target must not be null");
    try {
        return execute(aopAllianceInvoker, target, method, invocation.getArguments());
    }
    catch (CacheOperationInvoker.ThrowableWrapper th) {
        throw th.getOriginal();
    }
}
```

## 실제 코드

`spring-context` / `org.springframework.cache.interceptor` / `CacheAspectSupport.java` L381-L396 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheAspectSupport.java#L381-L396))

```java
// CacheAspectSupport.java L381-L396
protected @Nullable Object execute(CacheOperationInvoker invoker, Object target, Method method, @Nullable Object[] args) {
    // Check whether aspect is enabled (to cope with cases where the AJ is pulled in automatically)
    if (this.initialized) {
        Class<?> targetClass = AopProxyUtils.ultimateTargetClass(target);
        CacheOperationSource cacheOperationSource = getCacheOperationSource();
        if (cacheOperationSource != null) {
            Collection<CacheOperation> operations = cacheOperationSource.getCacheOperations(method, targetClass);
            if (!CollectionUtils.isEmpty(operations)) {
                return execute(invoker, method,
                        new CacheOperationContexts(operations, method, args, target, targetClass));
            }
        }
    }

    return invokeOperation(invoker);
}
```

`spring-context` / `org.springframework.cache.interceptor` / `CacheAspectSupport.java` L412-L428 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheAspectSupport.java#L412-L428))

```java
// CacheAspectSupport.java L412-L428
private @Nullable Object execute(CacheOperationInvoker invoker, Method method, CacheOperationContexts contexts) {
    if (contexts.isSynchronized()) {
        // Special handling of synchronized invocation
        return executeSynchronized(invoker, method, contexts);
    }

    // Process any early evictions
    processCacheEvicts(contexts.get(CacheEvictOperation.class), true,
            CacheOperationExpressionEvaluator.NO_RESULT);

    // Check if we have a cached value matching the conditions
    Object cacheHit = findCachedValue(invoker, method, contexts);
    if (cacheHit == null || cacheHit instanceof Cache.ValueWrapper) {
        return evaluate(cacheHit, invoker, method, contexts);
    }
    return cacheHit;
}
```

## 동작 흐름

```text
 execute(invoker, target, method, args)                (L381)
 |
 | L384 타깃 클래스 확정 (프록시가 아닌 실제 클래스)
 | L387 cacheOperationSource.getCacheOperations(method, targetClass)
 |        @Cacheable / @CachePut / @CacheEvict 를 모아 CacheOperation 목록으로
 |        비어 있으면 --> invokeOperation(invoker) 즉, 그냥 타깃 실행
 |
 +-- L389 CacheOperationContexts 구성 후 아래 execute 로
       |
       | L413 sync = true 인 @Cacheable 이면 executeSynchronized
       |        캐시 구현의 get(key, valueLoader) 를 써서
       |        같은 키에 대해 계산이 한 번만 일어나도록 맡긴다
       |
       | L419 beforeInvocation = true 인 @CacheEvict 수행
       |        메서드 실행 전에 비운다 (실패해도 이미 비워진 상태가 된다)
       |
       | L423 findCachedValue(...)    @Cacheable 조회
       |
       +-- L424 evaluate(cacheHit, ...)
              적중 여부에 따라 타깃 실행과 저장을 결정
```

1. 조회는 [findCachedValue](01_CacheAspectSupport.findCachedValue/README.md)가 한다.
2. 실행과 저장, 실행 후 제거는 [evaluate](02_CacheAspectSupport.evaluate/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 반환값
      --> CacheInterceptor.invoke 를 거쳐 프록시 호출자에게
      --> 적중이면 타깃을 부르지 않았으므로 부수 효과도 없다

 CacheOperationContexts
      --> 각 연산의 캐시 목록, 조건 평가, 키 생성 결과를 담는다
      --> 같은 요청 안에서 키를 두 번 생성하지 않도록 캐시한다

 연산이 하나도 없을 때
      --> 인터셉터가 붙었어도 비용이 거의 없다
          (프록시는 씌워졌지만 매 호출마다 애노테이션을 다시 읽지 않는다. 소스가 캐시한다)
```

## 하위 메서드

- [01 findCachedValue](01_CacheAspectSupport.findCachedValue/README.md)
- [02 evaluate](02_CacheAspectSupport.evaluate/README.md)
