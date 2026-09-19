# CacheManager

상위: [Spring 캐시 추상화](../../README.md) / [spi](../README.md)

이름으로 `Cache`를 찾아 주는 등록소다. 애플리케이션에는 보통 하나만 있고, 캐시 구현을 바꾸는 일은 이 빈을 바꾸는 일이 된다.

## 실제 코드

`spring-context` / `org.springframework.cache` / `CacheManager.java` L33-L78 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/CacheManager.java#L33-L78))

```java
// CacheManager.java L33-L78
public interface CacheManager {

    @Nullable Cache getCache(String name);

    Collection<String> getCacheNames();

    default void resetCaches() {
        for (String cacheName : getCacheNames()) {
            Cache cache = getCache(cacheName);
            if (cache != null) {
                cache.clear();
            }
        }
    }

}
```

## 흐름에서 불리는 자리

```text
 CacheResolver (기본 SimpleCacheResolver)
   연산의 cacheNames 로 cacheManager.getCache(name) 호출
   --> CacheOperationContext 의 캐시 목록
```

- [CacheAspectSupport.execute](../../01_CacheAspectSupport.execute/README.md)

## 구현 계층

```text
 CacheManager
   +-- AbstractCacheManager             이름->Cache 맵 관리
   |     +-- ConcurrentMapCacheManager  기본 (테스트/소규모)
   |     +-- CaffeineCacheManager
   |     +-- JCacheCacheManager
   +-- CompositeCacheManager            여러 매니저를 순서대로
   +-- NoOpCacheManager                 캐시를 끄는 용도 (항상 미스)

 설정
   @EnableCaching + CacheManager 빈 하나
   여러 개면 @Primary 또는 CachingConfigurer 로 지정
```
