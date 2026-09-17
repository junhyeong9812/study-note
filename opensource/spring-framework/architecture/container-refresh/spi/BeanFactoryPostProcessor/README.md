# BeanFactoryPostProcessor

상위: [Spring 컨테이너 기동](../../README.md) / [spi](../README.md)

빈 인스턴스가 하나도 만들어지기 전에 **빈 정의**를 읽고 고친다. 하위 인터페이스 `BeanDefinitionRegistryPostProcessor`는 정의를 새로 **추가**할 수도 있고, 일반 처리기보다 먼저 실행된다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.config` / `BeanFactoryPostProcessor.java` L70-L82 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/config/BeanFactoryPostProcessor.java#L70-L82))

```java
// BeanFactoryPostProcessor.java L70-L82
public interface BeanFactoryPostProcessor {

    void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) throws BeansException;

}
```

`spring-beans` / `org.springframework.beans.factory.support` / `BeanDefinitionRegistryPostProcessor.java` L34-L56 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/BeanDefinitionRegistryPostProcessor.java#L34-L56))

```java
// BeanDefinitionRegistryPostProcessor.java L34-L56
public interface BeanDefinitionRegistryPostProcessor extends BeanFactoryPostProcessor {

    void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) throws BeansException;

    @Override
    default void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) throws BeansException {
    }

}
```

## 흐름에서 불리는 자리

```text
 refresh
   --> invokeBeanFactoryPostProcessors
         1부  BeanDefinitionRegistryPostProcessor.postProcessBeanDefinitionRegistry
              PriorityOrdered --> Ordered --> 나머지 (새로 안 나올 때까지)
              이어서 그들의 postProcessBeanFactory
         2부  BeanFactoryPostProcessor.postProcessBeanFactory
              PriorityOrdered --> Ordered --> 나머지
```

- [AbstractApplicationContext.invokeBeanFactoryPostProcessors](../../01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/README.md)
- [PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors](../../01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/README.md)

## 구현 계층

```text
 BeanFactoryPostProcessor
   +-- BeanDefinitionRegistryPostProcessor
   |     +-- ConfigurationClassPostProcessor      @Configuration, @ComponentScan, @Import, @Bean (PriorityOrdered)
   |     +-- (Spring Boot, MyBatis 등의 스캐너 등록기)
   +-- PropertySourcesPlaceholderConfigurer       ${...} 치환 (PriorityOrdered)
   +-- EventListenerMethodProcessor               @EventListener 팩토리 수집 (SmartInitializingSingleton 겸용)
   +-- CustomScopeConfigurer                      사용자 scope 등록
   +-- CustomEditorConfigurer                     PropertyEditor 등록

 주의: 이 단계의 처리기는 BeanPostProcessor 적용 전에 만들어진다
       @Bean 으로 선언한다면 static 메서드로
```
