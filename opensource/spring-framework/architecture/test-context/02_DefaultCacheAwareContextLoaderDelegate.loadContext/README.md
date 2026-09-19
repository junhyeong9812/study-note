# DefaultCacheAwareContextLoaderDelegate.loadContext

상위: [Spring 테스트 컨텍스트](../README.md)

테스트용 `ApplicationContext`를 캐시에서 찾거나 새로 만든다. 테스트 스위트 전체의 실행 시간을 좌우하는 지점이다.

## 실제 코드

`spring-test` / `org.springframework.test.context.cache` / `DefaultCacheAwareContextLoaderDelegate.java` L138-L203 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/cache/DefaultCacheAwareContextLoaderDelegate.java#L138-L203))

```java
// DefaultCacheAwareContextLoaderDelegate.java L138-L203
@Override
public ApplicationContext loadContext(MergedContextConfiguration mergedConfig) {
    mergedConfig = replaceIfNecessary(mergedConfig);
    synchronized (this.contextCache) {
        try {
            ApplicationContext context = this.contextCache.get(mergedConfig);
            if (context != null) {
                if (logger.isTraceEnabled()) {
                    logger.trace("Retrieved ApplicationContext [%s] from cache with key %s".formatted(
                            System.identityHashCode(context), mergedConfig));
                }
                return context;
            }

            int failureCount = this.contextCache.getFailureCount(mergedConfig);
            if (failureCount >= this.failureThreshold) {
                throw new IllegalStateException("""
                        ApplicationContext failure threshold (%d) exceeded: \
                        skipping repeated attempt to load context for %s"""
                            .formatted(this.failureThreshold, mergedConfig));
            }

            return this.contextCache.put(mergedConfig, key -> {
                try {
                    ApplicationContext newContext;
                    if (key instanceof AotMergedContextConfiguration aotMergedConfig) {
                        newContext = loadContextInAotMode(aotMergedConfig);
                    }
                    else {
                        newContext = loadContextInternal(key);
                    }
                    if (logger.isTraceEnabled()) {
                        logger.trace("Storing ApplicationContext [%s] in cache under key %s".formatted(
                                System.identityHashCode(newContext), key));
                    }
                    return newContext;
                }
                catch (Exception ex) {
                    if (logger.isTraceEnabled()) {
                        logger.trace("Incrementing ApplicationContext failure count for " + key);
                    }
                    this.contextCache.incrementFailureCount(key);
                    Throwable cause = ex;
                    if (ex instanceof ContextLoadException cle) {
                        cause = cle.getCause();
                        for (ApplicationContextFailureProcessor contextFailureProcessor : this.contextFailureProcessors) {
                            try {
                                contextFailureProcessor.processLoadFailure(cle.getApplicationContext(), cause);
                            }
                            catch (Throwable throwable) {
                                if (logger.isDebugEnabled()) {
                                    logger.debug("Ignoring exception thrown from ApplicationContextFailureProcessor [%s]: %s"
                                            .formatted(contextFailureProcessor, throwable));
                                }
                            }
                        }
                    }
                    throw new IllegalStateException("Failed to load ApplicationContext for " + key, cause);
                }
            });
        }
        finally {
            this.contextCache.logStatistics();
        }
    }
}
```

테스트 쪽 진입점은 다음과 같다.

`spring-test` / `org.springframework.test.context.support` / `DefaultTestContext.java` L126-L141 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/support/DefaultTestContext.java#L126-L141))

```java
// DefaultTestContext.java L126-L141
@Override
public ApplicationContext getApplicationContext() {
    ApplicationContext context = this.cacheAwareContextLoaderDelegate.loadContext(this.mergedConfig);
    if (context instanceof ConfigurableApplicationContext cac) {
        Assert.state(cac.isActive(), () -> """
                The ApplicationContext loaded for %s is not active. \
                This may be due to one of the following reasons: \
                1) the context was closed programmatically by user code; \
                2) the context was closed during parallel test execution either \
                according to @DirtiesContext semantics or due to automatic eviction \
                from the ContextCache due to a maximum cache size policy."""
                    .formatted(this.mergedConfig));
    }
    this.cacheAwareContextLoaderDelegate.registerContextUsage(this.mergedConfig, this.testClass);
    return context;
}
```

## 동작 흐름

```text
 getApplicationContext()  (DefaultTestContext L127)
   --> loadContext(mergedConfig)
   --> 반환된 컨텍스트가 active 가 아니면 상태 오류
         (프로그램이 닫았거나, @DirtiesContext 또는 캐시 축출로 닫힌 경우)
   --> registerContextUsage 로 사용 표시

 loadContext(mergedConfig)
 |
 | L140 필요하면 설정을 AOT 모드용으로 교체
 | L141 캐시 전체를 잠근다 (같은 설정을 두 번 만들지 않기 위해)
 |
 +-- L143 contextCache.get(mergedConfig)
 |      있으면 그대로 반환                      <-- 컨텍스트 재사용
 |
 +-- L152 이 설정으로 실패한 횟수가 임계치 이상
 |      --> 반복 시도하지 않고 즉시 실패 (스위트가 같은 오류로 오래 도는 것을 막는다)
 |
 +-- L160 contextCache.put(mergedConfig, key -> {
        AOT 모드면 미리 생성된 초기화기로, 아니면 loadContextInternal
          --> SmartContextLoader 가 컨텍스트를 만들고 refresh 한다
        실패하면 실패 횟수를 올리고 원인을 감싸 던진다
      })
```

캐시 키는 `MergedContextConfiguration`이다. 다음 요소가 하나라도 다르면 다른 컨텍스트가 만들어진다.

```text
 설정 클래스 / XML 위치
 활성 프로파일 (@ActiveProfiles)
 프로퍼티 소스 (@TestPropertySource)
 컨텍스트 초기화기
 ContextCustomizer 들      <-- @MockitoBean, @DynamicPropertySource 등이 여기에 반영된다
 부모 컨텍스트
```

## 결과가 쓰이는 곳

```text
 반환된 컨텍스트
      --> DependencyInjectionTestExecutionListener 가 테스트 인스턴스에 주입
      --> @Autowired ApplicationContext 로 테스트가 직접 받을 수도 있다

 캐시 적중률
      --> 테스트 실행 시간의 대부분을 좌우한다
      --> 설정이 조금씩 다른 테스트가 많을수록 컨텍스트가 여러 개 만들어진다
      --> 기본 최대 크기(32)를 넘으면 LRU 로 축출되고, 축출된 컨텍스트는 닫힌다

 @DirtiesContext
      --> 테스트 후 캐시에서 제거하고 컨텍스트를 닫는다
      --> 이후 같은 설정의 테스트는 다시 만들게 된다
```
