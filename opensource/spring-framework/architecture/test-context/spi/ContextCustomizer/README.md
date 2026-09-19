# ContextCustomizer

상위: [Spring 테스트 컨텍스트](../../README.md) / [spi](../README.md)

컨텍스트를 refresh 하기 직전에 손볼 기회를 준다. 동시에 캐시 키의 일부가 되므로, 커스터마이저가 다르면 컨텍스트도 달라진다.

## 실제 코드

`spring-test` / `org.springframework.test.context` / `ContextCustomizer.java` L41-L52 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/ContextCustomizer.java#L41-L52))

```java
// ContextCustomizer.java L41-L52
public interface ContextCustomizer {

    void customizeContext(ConfigurableApplicationContext context, MergedContextConfiguration mergedConfig);

}
```

## 흐름에서 불리는 자리

```text
 MergedContextConfiguration 구성 시
   ContextCustomizerFactory 들이 커스터마이저를 만들어 붙인다
 컨텍스트 생성 시
   customizeContext(context, mergedConfig) 가 refresh 전에 호출된다
```

- [loadContext](../../02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md)

## 구현 계층

```text
 대표 구현
   BeanOverrideContextCustomizer      @MockitoBean / @TestBean 등록
   DynamicPropertiesContextCustomizer @DynamicPropertySource
   (Spring Boot: 웹 환경, 프로퍼티 등 다수)

 캐시에 주는 영향
   equals/hashCode 가 캐시 키에 반영된다
   테스트마다 다른 목을 선언하면 컨텍스트가 그만큼 늘어난다
```
