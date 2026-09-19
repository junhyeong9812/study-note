# Cache

상위: [Spring 캐시 추상화](../../README.md) / [spi](../README.md)

캐시 저장소 하나의 계약이다. 이름, 조회, 저장, 제거가 전부이고, 만료나 크기 제한 같은 정책은 구현에 맡긴다.

## 실제 코드

`spring-context` / `org.springframework.cache` / `Cache.java` L43-L321 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/Cache.java#L43-L321))

```java
// Cache.java L43-L321
public interface Cache {

    String getName();

    Object getNativeCache();

    @Nullable ValueWrapper get(Object key);

    <T> @Nullable T get(Object key, @Nullable Class<T> type);

    <T> @Nullable T get(Object key, Callable<T> valueLoader);

    default @Nullable CompletableFuture<?> retrieve(Object key) {
        throw new UnsupportedOperationException(
                getClass().getName() + " does not support CompletableFuture-based retrieval");
    }

    default <T> CompletableFuture<T> retrieve(Object key, Supplier<CompletableFuture<T>> valueLoader) {
        throw new UnsupportedOperationException(
                getClass().getName() + " does not support CompletableFuture-based retrieval");
    }

    void put(Object key, @Nullable Object value);

    default @Nullable ValueWrapper putIfAbsent(Object key, @Nullable Object value) {
        ValueWrapper existingValue = get(key);
        if (existingValue == null) {
            put(key, value);
        }
        return existingValue;
    }

    void evict(Object key);

    default boolean evictIfPresent(Object key) {
        evict(key);
        return false;
    }

    void clear();

    default boolean invalidate() {
        clear();
        return false;
    }

    @FunctionalInterface
    interface ValueWrapper {

        @Nullable Object get();
    }

    @SuppressWarnings("serial")
    class ValueRetrievalException extends RuntimeException {

        private final @Nullable Object key;

        public ValueRetrievalException(@Nullable Object key, Callable<?> loader, @Nullable Throwable ex) {
            super(String.format("Value for key '%s' could not be loaded using '%s'", key, loader), ex);
            this.key = key;
        }

        public @Nullable Object getKey() {
            return this.key;
        }
    }

}
```

## 흐름에서 불리는 자리

```text
 findCachedValue --> doGet(cache, key)         조회
 evaluate --> doPut(cache, key, value)          저장
 performCacheEvicts --> doEvict / doClear       제거
 sync=true 경로 --> cache.get(key, valueLoader) 구현이 락을 관리
```

- [findCachedValue](../../01_CacheAspectSupport.execute/01_CacheAspectSupport.findCachedValue/README.md)
- [evaluate](../../01_CacheAspectSupport.execute/02_CacheAspectSupport.evaluate/README.md)

## 구현 계층

```text
 Cache
   +-- AbstractValueAdaptingCache        null 값을 NullValue 로 바꿔 저장
   |     +-- ConcurrentMapCache          기본, 메모리 Map
   |     +-- CaffeineCache               Caffeine
   |     +-- JCacheCache                 JSR-107
   |     +-- (RedisCache 는 Spring Data Redis)
   +-- TransactionAwareCacheDecorator    트랜잭션 커밋 후에 저장/제거를 반영

 ValueWrapper
   조회 결과를 감싸는 껍데기
   래퍼가 있으면 적중, null 이면 미스 -- 값이 null 인 적중과 구분하기 위한 장치
```
