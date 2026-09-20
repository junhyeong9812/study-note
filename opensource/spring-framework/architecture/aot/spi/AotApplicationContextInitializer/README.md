# AotApplicationContextInitializer

상위: [Spring AOT 처리](../../README.md) / [spi](../README.md)

이 흐름에서 유일하게 런타임에 도는 것이다. 빌드 때 생성해 둔 초기화기를 찾아 컨텍스트에 적용한다.

## 실제 코드

`spring-context` / `org.springframework.context.aot` / `AotApplicationContextInitializer.java` L46-L90 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/aot/AotApplicationContextInitializer.java#L46-L90))

```java
// AotApplicationContextInitializer.java L46-L90
public interface AotApplicationContextInitializer<C extends ConfigurableApplicationContext>
        extends ApplicationContextInitializer<C> {

    static <C extends ConfigurableApplicationContext> AotApplicationContextInitializer<C> forInitializerClasses(
            String... initializerClassNames) {

        Assert.noNullElements(initializerClassNames, "'initializerClassNames' must not contain null elements");
        return applicationContext -> initialize(applicationContext, initializerClassNames);
    }

    private static <C extends ConfigurableApplicationContext> void initialize(
            C applicationContext, String... initializerClassNames) {

        Log logger = LogFactory.getLog(AotApplicationContextInitializer.class);
        ClassLoader classLoader = applicationContext.getClassLoader();
        logger.debug("Initializing ApplicationContext with AOT");
        for (String initializerClassName : initializerClassNames) {
            logger.trace(LogMessage.format("Applying %s", initializerClassName));
            instantiateInitializer(initializerClassName, classLoader).initialize(applicationContext);
        }
    }

    @SuppressWarnings("unchecked")
    static <C extends ConfigurableApplicationContext> ApplicationContextInitializer<C> instantiateInitializer(
            String initializerClassName, @Nullable ClassLoader classLoader) {
        try {
            Class<?> initializerClass = ClassUtils.resolveClassName(initializerClassName, classLoader);
            Assert.isAssignable(ApplicationContextInitializer.class, initializerClass);
            return (ApplicationContextInitializer<C>) BeanUtils.instantiateClass(initializerClass);
        }
        catch (BeanInstantiationException ex) {
            throw new IllegalArgumentException(
                    "Failed to instantiate ApplicationContextInitializer: " + initializerClassName, ex);
        }
    }

}
```

## 흐름에서 불리는 자리

```text
 런타임 기동 경로
   forInitializerClasses(클래스 이름들) 로 초기화기를 만든다
   그 초기화기가 컨텍스트에 적용되면
     생성된 코드가 빈 정의를 직접 등록한다
   이어지는 refresh 는 설정 파싱 없이 진행된다
```

- [컨테이너 기동](../../../container-refresh/README.md)

## 구현 계층

```text
 ApplicationContextInitializer<C>
   +-- AotApplicationContextInitializer<C>
         forInitializerClasses(String...) 정적 메서드로 만든다
         클래스 이름으로 생성된 초기화기를 로드해 순서대로 적용한다

 생성된 초기화기
   ApplicationContextInitializationCodeGenerator 가 만든 클래스가
   ApplicationContextInitializer 를 구현한다
```

## 결과가 쓰이는 곳

```text
 적용된 초기화기
      --> 빈 정의가 곧바로 등록된다
      --> @Configuration 파싱, 컴포넌트 스캔, 애노테이션 읽기가 생략된다

 기동 시간
      --> 정의를 만드는 단계가 통째로 빠져 기동이 빨라진다
      --> JVM 에서도 AOT 를 쓰면 이 이득만 따로 얻을 수 있다

 클래스 이름으로 찾는다는 점
      --> 빌드 도구가 생성된 클래스 이름을 런타임에 알려 준다
      --> 스프링 부트는 이 과정을 자동으로 엮어 준다

 생성물이 없으면
      --> JVM 에서는 spring.aot.enabled 를 켜지 않는 한 런타임 파싱 경로로 동작한다
      --> 네이티브 이미지에서는 선택지가 아니다
          AotDetector.useGeneratedArtifacts() 가 inNativeImage 만으로 참이 되고,
          자바독은 되돌아가는 대신 예외를 던지라고 못박는다
```
