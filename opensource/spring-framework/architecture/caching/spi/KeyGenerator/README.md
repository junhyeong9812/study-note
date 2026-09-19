# KeyGenerator

상위: [Spring 캐시 추상화](../../README.md) / [spi](../README.md)

캐시 키를 만든다. `key` 식을 쓰지 않았을 때의 기본 경로이고, 인자 조합으로 키를 만든다.

## 실제 코드

`spring-context` / `org.springframework.cache.interceptor` / `KeyGenerator.java` L33-L44 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/cache/interceptor/KeyGenerator.java#L33-L44))

```java
// KeyGenerator.java L33-L44
public interface KeyGenerator {

    Object generate(Object target, Method method, @Nullable Object... params);

}
```

## 흐름에서 불리는 자리

```text
 findCachedValue L497 generateKey
   key 식이 있으면 SpEL 평가 (KeyGenerator 를 쓰지 않는다)
   없으면 keyGenerator.generate(target, method, params)
 생성된 키는 컨텍스트에 보관되어 저장/제거에서 재사용
```

- [findCachedValue](../../01_CacheAspectSupport.execute/01_CacheAspectSupport.findCachedValue/README.md)

## 구현 계층

```text
 KeyGenerator
   +-- SimpleKeyGenerator        기본
   |     인자 0개 --> SimpleKey.EMPTY
   |     인자 1개이고 null 도 배열도 아니면 --> 그 값 자체
   |     여러 개  --> SimpleKey(인자들)
   +-- (사용자 구현: CachingConfigurer.keyGenerator 로 등록)

 주의
   키 객체는 equals/hashCode 가 제대로 있어야 한다
   분산 캐시라면 직렬화 가능해야 한다
```
