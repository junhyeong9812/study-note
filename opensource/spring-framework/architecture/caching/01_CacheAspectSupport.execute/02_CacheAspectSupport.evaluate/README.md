# CacheAspectSupport.evaluate

상위: [CacheAspectSupport.execute](../README.md)

조회 결과를 보고 타깃을 부를지 정하고, 저장 요청과 실행 후 제거를 수행한다. `@Cacheable`, `@CachePut`, `@CacheEvict`가 한 메서드에 섞여 있을 때의 순서가 여기서 확정된다.

## 실제 코드

`spring-context` / `org.springframework.cache.interceptor` / `CacheAspectSupport.java` L556-L606 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheAspectSupport.java#L556-L606))

```java
// CacheAspectSupport.java L556-L606
private @Nullable Object evaluate(@Nullable Object cacheHit, CacheOperationInvoker invoker, Method method,
        CacheOperationContexts contexts) {

    // Re-invocation in reactive pipeline after late cache hit determination?
    if (contexts.processed) {
        return cacheHit;
    }

    Object cacheValue;
    Object returnValue;

    if (cacheHit != null && !hasCachePut(contexts)) {
        // If there are no put requests, just use the cache hit
        cacheValue = unwrapCacheValue(cacheHit);
        returnValue = wrapCacheValue(method, cacheValue);
    }
    else {
        // Invoke the method if we don't have a cache hit
        returnValue = invokeOperation(invoker);
        cacheValue = unwrapReturnValue(returnValue);
    }

    // Collect puts from any @Cacheable miss, if no cached value is found
    List<CachePutRequest> cachePutRequests = new ArrayList<>(1);
    if (cacheHit == null) {
        collectPutRequests(contexts.get(CacheableOperation.class), cacheValue, cachePutRequests);
    }

    // Collect any explicit @CachePuts
    collectPutRequests(contexts.get(CachePutOperation.class), cacheValue, cachePutRequests);

    // Process any collected put requests, either from @CachePut or a @Cacheable miss
    for (CachePutRequest cachePutRequest : cachePutRequests) {
        Object returnOverride = cachePutRequest.apply(cacheValue);
        if (returnOverride != null) {
            returnValue = returnOverride;
        }
    }

    // Process any late evictions
    Object returnOverride = processCacheEvicts(
            contexts.get(CacheEvictOperation.class), false, returnValue);
    if (returnOverride != null) {
        returnValue = returnOverride;
    }

    // Mark as processed for re-invocation after late cache hit determination
    contexts.processed = true;

    return returnValue;
}
```

저장과 제거를 실제로 수행하는 부분이다.

`spring-context` / `org.springframework.cache.interceptor` / `CacheAspectSupport.java` L672-L692 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheAspectSupport.java#L672-L692))

```java
// CacheAspectSupport.java L672-L692
private void performCacheEvicts(List<CacheOperationContext> contexts, @Nullable Object result) {
    for (CacheOperationContext context : contexts) {
        CacheEvictOperation operation = (CacheEvictOperation) context.metadata.operation;
        if (isConditionPassing(context, result)) {
            Object key = context.getGeneratedKey();
            for (Cache cache : context.getCaches()) {
                if (operation.isCacheWide()) {
                    logInvalidating(context, operation, null);
                    doClear(cache, operation.isBeforeInvocation());
                }
                else {
                    if (key == null) {
                        key = generateKey(context, result);
                    }
                    logInvalidating(context, operation, key);
                    doEvict(cache, key, operation.isBeforeInvocation());
                }
            }
        }
    }
}
```

`spring-context` / `org.springframework.cache.interceptor` / `CacheAspectSupport.java` L708-L716 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheAspectSupport.java#L708-L716))

```java
// CacheAspectSupport.java L708-L716
private void collectPutRequests(Collection<CacheOperationContext> contexts,
        @Nullable Object result, Collection<CachePutRequest> putRequests) {

    for (CacheOperationContext context : contexts) {
        if (isConditionPassing(context, result)) {
            putRequests.add(new CachePutRequest(context));
        }
    }
}
```

## 동작 흐름

```text
 evaluate(cacheHit, invoker, method, contexts)
 |
 | L560 이미 처리된 컨텍스트면 (리액티브 재진입) 그대로 반환
 |
 +-- [1] L567 타깃을 부를지 결정
 |      캐시 적중 + @CachePut 없음 --> 타깃 호출 없음, 캐시 값을 사용
 |      그 밖 (미스이거나 @CachePut 있음) --> invokeOperation(invoker) 로 타깃 실행
 |        = @CachePut 이 있으면 적중이어도 항상 실행된다
 |
 | [2] L580 캐시 미스였으면 @Cacheable 저장 요청 수집
 | [3] L585 @CachePut 저장 요청 수집
 |        이때 condition 을 평가한다 (한 번 평가하면 메모이즈된다, L900)
 |        결과값으로 거르는 것은 condition 이 아니라 unless 다
 |
 | [4] L588 수집한 요청을 순서대로 적용
 |        CachePutRequest.apply (L1022)
 |          unless 평가 --> 통과하면 doPut(cache, key, value)
 |          여러 캐시가 지정됐으면 모두에 저장
 |
 | [5] L596 beforeInvocation = false 인 @CacheEvict 수행
 |        performCacheEvicts (L672)
 |          allEntries = true --> doClear(cache)
 |          아니면 키로 doEvict(cache, key)
 |          condition 을 결과값과 함께 평가
 |
 +-- L603 처리 완료 표시 후 반환값 반환
```

```text
 한 메서드에 여럿이 붙었을 때의 순서

 @CacheEvict(beforeInvocation = true)   메서드 실행 전
 @Cacheable 조회
 (미스이거나 @CachePut 있으면) 메서드 실행
 @Cacheable 저장 (미스였을 때만)
 @CachePut 저장
 @CacheEvict(기본, beforeInvocation = false)   메서드 실행 후
```

## 결과가 쓰이는 곳

```text
 반환값
      --> execute 를 거쳐 호출자에게
      --> 저장 단계가 값을 바꿀 수 있다 (비동기 타입에서 래핑된 결과를 돌려주는 경우)

 doPut / doEvict / doClear
      --> Cache 구현에 위임 (ConcurrentMapCache, CaffeineCache, RedisCache 등)
      --> 오류는 CacheErrorHandler 로 간다
          기본 구현은 예외를 그대로 던지므로, 캐시 장애가 호출 실패로 이어진다
          (무시하려면 CachingConfigurer 로 다른 핸들러를 등록한다)

 beforeInvocation = false 인 제거
      --> 메서드가 예외를 던지면 제거가 일어나지 않는다
      --> 트랜잭션 롤백과 캐시 제거를 맞추려면 이 차이를 고려해야 한다
```
