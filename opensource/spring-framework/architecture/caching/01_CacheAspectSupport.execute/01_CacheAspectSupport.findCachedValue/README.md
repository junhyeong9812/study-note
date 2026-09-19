# CacheAspectSupport.findCachedValue

상위: [CacheAspectSupport.execute](../README.md)

`@Cacheable` 연산마다 조건을 평가하고, 키를 만들고, 지정된 캐시들을 순서대로 조회한다. 하나라도 값을 찾으면 그 값을 돌려준다.

## 실제 코드

`spring-context` / `org.springframework.cache.interceptor` / `CacheAspectSupport.java` L494-L513 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheAspectSupport.java#L494-L513))

```java
// CacheAspectSupport.java L494-L513
private @Nullable Object findCachedValue(CacheOperationInvoker invoker, Method method, CacheOperationContexts contexts) {
    for (CacheOperationContext context : contexts.get(CacheableOperation.class)) {
        if (isConditionPassing(context, CacheOperationExpressionEvaluator.NO_RESULT)) {
            Object key = generateKey(context, CacheOperationExpressionEvaluator.NO_RESULT);
            Object cached = findInCaches(context, key, invoker, method, contexts);
            if (cached != null) {
                if (logger.isTraceEnabled()) {
                    logger.trace("Cache entry for key '" + key + "' found in cache(s) " + context.getCacheNames());
                }
                return cached;
            }
            else {
                if (logger.isTraceEnabled()) {
                    logger.trace("No cache entry for key '" + key + "' in cache(s) " + context.getCacheNames());
                }
            }
        }
    }
    return null;
}
```

`spring-context` / `org.springframework.cache.interceptor` / `CacheAspectSupport.java` L515-L554 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheAspectSupport.java#L515-L554))

```java
// CacheAspectSupport.java L515-L554
private @Nullable Object findInCaches(CacheOperationContext context, Object key,
        CacheOperationInvoker invoker, Method method, CacheOperationContexts contexts) {

    for (Cache cache : context.getCaches()) {
        if (CompletableFuture.class.isAssignableFrom(context.getMethod().getReturnType())) {
            CompletableFuture<?> result = doRetrieve(cache, key);
            if (result != null) {
                return result.exceptionallyCompose(ex -> {
                    if (!(ex instanceof RuntimeException rex)) {
                        return CompletableFuture.failedFuture(ex);
                    }
                    try {
                        getErrorHandler().handleCacheGetError(rex, cache, key);
                        return CompletableFuture.completedFuture(null);
                    }
                    catch (Throwable ex2) {
                        return CompletableFuture.failedFuture(ex2);
                    }
                }).thenCompose(value -> (CompletableFuture<?>) evaluate(
                        (value != null ? CompletableFuture.completedFuture(unwrapCacheValue(value)) : null),
                        invoker, method, contexts));
            }
            else {
                continue;
            }
        }
        if (this.reactiveCachingHandler != null) {
            Object returnValue = this.reactiveCachingHandler.findInCaches(
                    context, cache, key, invoker, method, contexts);
            if (returnValue != ReactiveCachingHandler.NOT_HANDLED) {
                return returnValue;
            }
        }
        Cache.ValueWrapper result = doGet(cache, key);
        if (result != null) {
            return result;
        }
    }
    return null;
}
```

## 동작 흐름

```text
 findCachedValue(invoker, method, contexts)
 |
 +-- for context in @Cacheable 연산들
       |
       | L496 isConditionPassing(context, NO_RESULT)
       |        condition SpEL 평가 (#root.args, 파라미터 이름 등)
       |        결과값은 아직 없으므로 NO_RESULT
       |        false --> 이 연산은 조회 자체를 하지 않는다 (캐시를 통째로 건너뛴다)
       |
       | L497 generateKey(context, NO_RESULT)
       |        key 식이 있으면 SpEL 평가
       |        없으면 KeyGenerator (기본 SimpleKeyGenerator: 인자 조합)
       |
       +-- L498 findInCaches(context, key, ...)
              for cache in context.getCaches()        cacheNames 순서대로
                반환 타입이 CompletableFuture 면 비동기 조회 경로
                그 밖 --> doGet(cache, key)
                  ValueWrapper 를 찾으면 즉시 반환 (null 값도 적중으로 친다)
                  조회 중 오류 --> CacheErrorHandler 가 처리 (기본은 예외 전파)
 |
 +-- 아무 캐시에도 없으면 null
```

캐시 적중과 "값이 null인 적중"은 다르다. `Cache.get`은 `ValueWrapper`로 감싸 돌려주므로, 래퍼가 있으면 값이 null이어도 적중이다. 이 구분이 "null을 캐시할 수 있는가"를 결정한다.

## 결과가 쓰이는 곳

```text
 반환값 (캐시된 값 또는 null)
      --> execute 가 evaluate 로 넘긴다
      --> null 이면 캐시 미스 --> 타깃 실행 + 저장 요청 수집
      --> ValueWrapper 이면 적중 --> 타깃을 부르지 않는다 (@CachePut 이 없다면)

 생성한 키
      --> 컨텍스트에 보관되어 저장/제거 단계에서 재사용
      --> 조회와 저장이 같은 키를 쓰도록 보장하는 지점

 condition 이 false 인 경우
      --> 조회도 저장도 하지 않는다
      --> unless 와 다르다. unless 는 결과를 보고 "저장만" 막는다
```
