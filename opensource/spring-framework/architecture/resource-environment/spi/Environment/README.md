# Environment

상위: [Spring 리소스와 환경](../../README.md) / [spi](../README.md)

프로파일과 프로퍼티를 함께 다루는 컨테이너 수준 추상화다. 프로퍼티 조회는 `PropertyResolver` 계약을 이어받는다.

## 실제 코드

`spring-core` / `org.springframework.core.env` / `Environment.java` L72-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/env/Environment.java#L72-L120))

```java
// Environment.java L72-L120
public interface Environment extends PropertyResolver {

    String[] getActiveProfiles();

    String[] getDefaultProfiles();

    default boolean matchesProfiles(String... profileExpressions) {
        return acceptsProfiles(Profiles.of(profileExpressions));
    }

```

`spring-core` / `org.springframework.core.env` / `PropertyResolver.java` L30-L112 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/env/PropertyResolver.java#L30-L112))

```java
// PropertyResolver.java L30-L112
public interface PropertyResolver {

    boolean containsProperty(String key);

    @Nullable String getProperty(String key);

    String getProperty(String key, String defaultValue);

    <T> @Nullable T getProperty(String key, Class<T> targetType);

    <T> T getProperty(String key, Class<T> targetType, T defaultValue);

    String getRequiredProperty(String key) throws IllegalStateException;

    <T> T getRequiredProperty(String key, Class<T> targetType) throws IllegalStateException;

    String resolvePlaceholders(String text);

    String resolveRequiredPlaceholders(String text) throws IllegalArgumentException;

}
```

## 흐름에서 불리는 자리

```text
 [컨테이너 기동] prepareRefresh --> validateRequiredProperties
 [컨테이너 기동] prepareBeanFactory --> environment 싱글톤 등록
 @Value / @PropertySource / @Profile 판정
 getProperty --> PropertySourcesPropertyResolver
```

- [PropertySourcesPropertyResolver.getProperty](../../02_PropertySourcesPropertyResolver.getProperty/README.md)
- [컨테이너 기동의 prepareRefresh](../../../container-refresh/01_AbstractApplicationContext.refresh/01_AbstractApplicationContext.prepareRefresh/README.md)

## 구현 계층

```text
 PropertyResolver
   +-- ConfigurablePropertyResolver
         +-- AbstractPropertyResolver
               +-- PropertySourcesPropertyResolver
 Environment
   +-- ConfigurableEnvironment          getPropertySources / setActiveProfiles
         +-- AbstractEnvironment
               +-- StandardEnvironment          시스템 프로퍼티 + 환경 변수
                     +-- StandardServletEnvironment   + 서블릿 파라미터
                     +-- (Spring Boot 가 확장)

 프로파일
   acceptsProfiles / getActiveProfiles
   @Profile 은 Condition 으로 평가되어 빈 등록 여부를 가른다
```
