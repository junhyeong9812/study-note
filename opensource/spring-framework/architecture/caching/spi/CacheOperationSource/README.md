# CacheOperationSource

상위: [Spring 캐시 추상화](../../README.md) / [spi](../README.md)

메서드 하나에 붙은 캐시 연산을 찾아 준다. 트랜잭션의 `TransactionAttributeSource`와 같은 자리다.

## 실제 코드

`spring-context` / `org.springframework.cache.interceptor` / `CacheOperationSource.java` L35-L78 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/CacheOperationSource.java#L35-L78))

```java
// CacheOperationSource.java L35-L78
public interface CacheOperationSource {

    default boolean isCandidateClass(Class<?> targetClass) {
        return true;
    }

    default boolean hasCacheOperations(Method method, @Nullable Class<?> targetClass) {
        return !CollectionUtils.isEmpty(getCacheOperations(method, targetClass));
    }

    @Nullable Collection<CacheOperation> getCacheOperations(Method method, @Nullable Class<?> targetClass);

}
```

## 흐름에서 불리는 자리

```text
 CacheAspectSupport.execute L387
   getCacheOperations(method, targetClass)
     비어 있으면 캐시 처리를 건너뛴다
 프록시 생성 단계에서도 같은 판정이 쓰인다
   CacheOperationSourcePointcut 이 "프록시가 필요한가" 를 정한다
```

- [CacheAspectSupport.execute](../../01_CacheAspectSupport.execute/README.md)

## 구현 계층

```text
 CacheOperationSource
   +-- AbstractFallbackCacheOperationSource      탐색 순서 + 캐시
   |     +-- AnnotationCacheOperationSource      @Cacheable @CachePut @CacheEvict
   +-- CompositeCacheOperationSource
   +-- NameMatchCacheOperationSource             메서드 이름 패턴

 탐색 순서 (트랜잭션과 동일한 규칙)
   타깃 클래스 메서드 -> 타깃 클래스 -> 선언 클래스 메서드 -> 선언 클래스
```
