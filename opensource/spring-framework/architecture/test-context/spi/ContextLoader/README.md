# ContextLoader

상위: [Spring 테스트 컨텍스트](../../README.md) / [spi](../README.md)

테스트 설정으로부터 `ApplicationContext`를 만들어 낸다. 실제로는 하위 인터페이스 `SmartContextLoader`가 쓰인다.

## 실제 코드

`spring-test` / `org.springframework.test.context` / `ContextLoader.java` L45-L89 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/ContextLoader.java#L45-L89))

```java
// ContextLoader.java L45-L89
public interface ContextLoader {

    @Deprecated(since = "6.0")
    String[] processLocations(Class<?> clazz, String... locations);

    @Deprecated(since = "6.0")
    ApplicationContext loadContext(String... locations) throws Exception;

}
```

`spring-test` / `org.springframework.test.context` / `SmartContextLoader.java` L74-L179 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/SmartContextLoader.java#L74-L179))

```java
// SmartContextLoader.java L74-L179
public interface SmartContextLoader extends ContextLoader {

    void processContextConfiguration(ContextConfigurationAttributes configAttributes);

    ApplicationContext loadContext(MergedContextConfiguration mergedConfig) throws Exception;

    @Override
    @SuppressWarnings("deprecation")
    default String[] processLocations(Class<?> clazz, String... locations) {
        throw new UnsupportedOperationException("""
                SmartContextLoader does not support the ContextLoader SPI. \
                Call processContextConfiguration(ContextConfigurationAttributes) instead.""");
    }

    @Override
    @SuppressWarnings("deprecation")
    default ApplicationContext loadContext(String... locations) throws Exception {
        throw new UnsupportedOperationException("""
                SmartContextLoader does not support the ContextLoader SPI. \
                Call loadContext(MergedContextConfiguration) instead.""");
    }

}
```

## 흐름에서 불리는 자리

```text
 loadContext 의 캐시 미스 경로
   loadContextInternal --> SmartContextLoader.loadContext(mergedConfig)
     컨텍스트 생성 --> 초기화기 적용 --> refresh
   = 여기서 [컨테이너 기동] 흐름이 실행된다
```

- [loadContext](../../02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md)
- [컨테이너 기동](../../../container-refresh/README.md)

## 구현 계층

```text
 ContextLoader
   +-- SmartContextLoader                     MergedContextConfiguration 기반
         +-- AbstractGenericContextLoader
         |     +-- AnnotationConfigContextLoader     @ContextConfiguration(classes = ...)
         |     +-- GenericXmlContextLoader           XML 위치
         +-- AbstractGenericWebContextLoader
               +-- WebDelegatingSmartContextLoader 등 웹 컨텍스트

 Spring Boot 는 SpringBootContextLoader 로 대체한다
```
