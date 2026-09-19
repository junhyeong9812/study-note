# ResourceLoader

상위: [Spring 리소스와 환경](../../README.md) / [spi](../README.md)

위치 문자열을 `Resource`로 바꾸는 전략이다. `ApplicationContext`가 이 인터페이스를 구현하므로, 컨텍스트 자체가 리소스 로더다.

## 실제 코드

`spring-core` / `org.springframework.core.io` / `ResourceLoader.java` L43-L112 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/io/ResourceLoader.java#L43-L112))

```java
// ResourceLoader.java L43-L112
public interface ResourceLoader {

    String CLASSPATH_URL_PREFIX = ResourceUtils.CLASSPATH_URL_PREFIX;

    String CLASSPATH_ALL_URL_PREFIX = "classpath*:";

    Resource getResource(String location);

    @Nullable ClassLoader getClassLoader();

}
```

`spring-core` / `org.springframework.core.io.support` / `ResourcePatternResolver.java` L58-L71 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/io/support/ResourcePatternResolver.java#L58-L71))

```java
// ResourcePatternResolver.java L58-L71
public interface ResourcePatternResolver extends ResourceLoader {

    Resource[] getResources(String locationPattern) throws IOException;

}
```

`spring-core` / `org.springframework.core.io` / `ProtocolResolver.java` L33-L45 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/io/ProtocolResolver.java#L33-L45))

```java
// ProtocolResolver.java L33-L45
public interface ProtocolResolver {

    @Nullable Resource resolve(String location, ResourceLoader resourceLoader);

}
```

## 흐름에서 불리는 자리

```text
 context.getResource("classpath:app.yml")
   --> DefaultResourceLoader.getResource
 context.getResources("classpath*:**/*.xml")
   --> PathMatchingResourcePatternResolver.getResources
```

- [DefaultResourceLoader.getResource](../../01_DefaultResourceLoader.getResource/README.md)
- [컨테이너 기동의 prepareBeanFactory](../../../container-refresh/01_AbstractApplicationContext.refresh/03_AbstractApplicationContext.prepareBeanFactory/README.md)

## 구현 계층

```text
 ResourceLoader
   +-- DefaultResourceLoader                 기본 규칙
         +-- AbstractApplicationContext      컨텍스트가 곧 로더
         +-- (서블릿 환경에서는 "/" 해석이 달라진다)
   +-- ResourcePatternResolver               패턴으로 여러 개
         +-- PathMatchingResourcePatternResolver

 ProtocolResolver
   사용자 정의 접두사 지원 (가장 먼저 질의된다)
   DefaultResourceLoader.addProtocolResolver 로 등록

 주입
   @Autowired ResourceLoader
   @Value("classpath:app.yml") Resource   (ResourceEditor 가 변환)
```
