# CacheErrorHandler

상위: [Spring 캐시 추상화](../../README.md) / [spi](../README.md)

캐시 연산 자체가 실패했을 때의 정책이다. 기본은 예외를 그대로 던지므로 캐시 장애가 호출 실패가 된다.

## 실제 코드

`spring-context` / `org.springframework.cache.interceptor` / `CacheErrorHandler.java` L38-L89 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheErrorHandler.java#L38-L89))

```java
// CacheErrorHandler.java L38-L89
public interface CacheErrorHandler {

    void handleCacheGetError(RuntimeException exception, Cache cache, Object key);

    void handleCachePutError(RuntimeException exception, Cache cache, Object key, @Nullable Object value);

    void handleCacheEvictError(RuntimeException exception, Cache cache, Object key);

    void handleCacheClearError(RuntimeException exception, Cache cache);

}
```

## 흐름에서 불리는 자리

```text
 doGet / doPut / doEvict / doClear 에서 RuntimeException 이 나면
   getErrorHandler().handleCacheGetError(ex, cache, key) 등으로 넘어간다
 기본 SimpleCacheErrorHandler 는 예외를 다시 던진다
```

- [evaluate](../../01_CacheAspectSupport.execute/02_CacheAspectSupport.evaluate/README.md)
- [findCachedValue](../../01_CacheAspectSupport.execute/01_CacheAspectSupport.findCachedValue/README.md)

## 구현 계층

```text
 CacheErrorHandler
   +-- SimpleCacheErrorHandler     예외 재전파 (기본)
   +-- LoggingCacheErrorHandler    로그만 남기고 진행
   +-- (사용자 구현)

 등록
   CachingConfigurer.errorHandler()

 선택 기준
   캐시가 성능 최적화라면 로깅 후 진행이 안전하다
   캐시가 정합성의 일부라면 기본 동작이 맞다
```
