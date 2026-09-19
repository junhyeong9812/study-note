# ContextCache

상위: [Spring 테스트 컨텍스트](../../README.md) / [spi](../README.md)

만들어진 컨텍스트를 설정별로 보관한다. 테스트 스위트의 속도가 이 캐시의 적중률에 달려 있다.

## 실제 코드

`spring-test` / `org.springframework.test.context.cache` / `ContextCache.java` L64-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/cache/ContextCache.java#L64-L120))

```java
// ContextCache.java L64-L120
public interface ContextCache {

    String CONTEXT_CACHE_LOGGING_CATEGORY = "org.springframework.test.context.cache";

    int DEFAULT_MAX_CONTEXT_CACHE_SIZE = 32;

    String MAX_CONTEXT_CACHE_SIZE_PROPERTY_NAME = "spring.test.context.cache.maxSize";

    String CONTEXT_CACHE_PAUSE_PROPERTY_NAME = "spring.test.context.cache.pause";

    boolean contains(MergedContextConfiguration key);

```

## 흐름에서 불리는 자리

```text
 DefaultCacheAwareContextLoaderDelegate.loadContext
   get(mergedConfig)      적중이면 재사용
   put(key, 생성 함수)    미스면 만들어 저장
   실패 횟수 기록으로 반복 실패를 차단
 @DirtiesContext --> remove(key, 모드)
```

- [loadContext](../../02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md)

## 구현 계층

```text
 ContextCache
   +-- DefaultContextCache        LRU, 기본 최대 32개 (DEFAULT_MAX_CONTEXT_CACHE_SIZE)

 캐시 키를 바꾸는 것들
   설정 클래스/XML, @ActiveProfiles, @TestPropertySource,
   ContextCustomizer (@MockitoBean, @DynamicPropertySource 등), 부모 컨텍스트

 축출
   최대 크기를 넘으면 가장 오래 쓰이지 않은 컨텍스트를 닫는다
   통계는 로그 레벨 DEBUG 로 확인할 수 있다 (hit/miss/size)
```
