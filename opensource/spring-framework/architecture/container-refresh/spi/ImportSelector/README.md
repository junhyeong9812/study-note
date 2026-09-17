# ImportSelector

상위: [Spring 컨테이너 기동](../../README.md) / [spi](../README.md)

`@Import` 대상으로 쓰여, 어떤 설정 클래스를 더 불러올지 **코드로** 정한다. 같은 자리에 쓰이는 `ImportBeanDefinitionRegistrar`는 클래스 이름 대신 빈 정의를 직접 등록한다. `@EnableXxx` 애노테이션 대부분이 둘 중 하나를 품고 있다.

## 실제 코드

`spring-context` / `org.springframework.context.annotation` / `ImportSelector.java` L62-L85 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ImportSelector.java#L62-L85))

```java
// ImportSelector.java L62-L85
public interface ImportSelector {

    String[] selectImports(AnnotationMetadata importingClassMetadata);

    default @Nullable Predicate<String> getExclusionFilter() {
        return null;
    }

}
```

`spring-context` / `org.springframework.context.annotation` / `ImportBeanDefinitionRegistrar.java` L61-L102 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ImportBeanDefinitionRegistrar.java#L61-L102))

```java
// ImportBeanDefinitionRegistrar.java L61-L102
public interface ImportBeanDefinitionRegistrar {

    default void registerBeanDefinitions(AnnotationMetadata importingClassMetadata, BeanDefinitionRegistry registry,
            BeanNameGenerator importBeanNameGenerator) {

        registerBeanDefinitions(importingClassMetadata, registry);
    }

    default void registerBeanDefinitions(AnnotationMetadata importingClassMetadata, BeanDefinitionRegistry registry) {
    }

}
```

## 흐름에서 불리는 자리

```text
 ConfigurationClassParser.processImports
   ImportSelector                 --> selectImports() 결과로 processImports 재귀
   DeferredImportSelector         --> 모든 설정 파싱 뒤 일괄 처리
   ImportBeanDefinitionRegistrar  --> 모델에 기록
 ConfigurationClassBeanDefinitionReader.loadBeanDefinitions
   ImportBeanDefinitionRegistrar  --> registerBeanDefinitions(import 한 클래스 메타데이터, registry)
```

- [ConfigurationClassParser.processImports](../../01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/01_ConfigurationClassParser.parse/01_ConfigurationClassParser.processImports/README.md)
- [ConfigurationClassBeanDefinitionReader.loadBeanDefinitions](../../01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/02_ConfigurationClassBeanDefinitionReader.loadBeanDefinitions/README.md)

## 구현 계층

```text
 ImportSelector
   +-- DeferredImportSelector              모든 사용자 설정 뒤에 처리 (Spring Boot 자동 설정)
   +-- AdviceModeImportSelector
         +-- AsyncConfigurationSelector     @EnableAsync
         +-- TransactionManagementConfigurationSelector   @EnableTransactionManagement
         +-- CachingConfigurationSelector   @EnableCaching
 ImportBeanDefinitionRegistrar
   +-- AspectJAutoProxyRegistrar           @EnableAspectJAutoProxy
   +-- (Spring Data 리포지토리 등록기 등)
 일반 클래스 import
   +-- SchedulingConfiguration             @EnableScheduling
```
