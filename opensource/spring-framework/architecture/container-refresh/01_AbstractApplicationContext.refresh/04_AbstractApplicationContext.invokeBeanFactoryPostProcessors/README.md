# AbstractApplicationContext.invokeBeanFactoryPostProcessors

상위: [AbstractApplicationContext.refresh](../README.md)

빈 인스턴스를 만들기 전에 **빈 정의**를 고치거나 추가하는 [BeanFactoryPostProcessor](../../spi/BeanFactoryPostProcessor/README.md)들을 실행한다. 실행 순서는 정적 위임 클래스가 정하고, 이 메서드는 위임한 뒤 로드타임 위버 준비만 보탠다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L795-L805 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L795-L805))

```java
// AbstractApplicationContext.java L795-L805
protected void invokeBeanFactoryPostProcessors(ConfigurableListableBeanFactory beanFactory) {
    PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors(beanFactory, getBeanFactoryPostProcessors());

    // Detect a LoadTimeWeaver and prepare for weaving, if found in the meantime
    // (for example, through a @Bean method registered by ConfigurationClassPostProcessor)
    if (!NativeDetector.inNativeImage() && beanFactory.getTempClassLoader() == null &&
            beanFactory.containsBean(LOAD_TIME_WEAVER_BEAN_NAME)) {
        beanFactory.addBeanPostProcessor(new LoadTimeWeaverAwareProcessor(beanFactory));
        beanFactory.setTempClassLoader(new ContextTypeMatchClassLoader(beanFactory.getBeanClassLoader()));
    }
}
```

## 동작 흐름

```text
 invokeBeanFactoryPostProcessors(beanFactory)
 |
 +-- L796 PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors(
 |          beanFactory,
 |          getBeanFactoryPostProcessors())   context.addBeanFactoryPostProcessor() 로 코드에서 넣은 것
 |        --> 등록된 처리기 전부 실행, 빈 정의 목록 완성
 |
 +-- L800 처리기 실행 중에 loadTimeWeaver 빈이 새로 생겼고 (예: @EnableLoadTimeWeaving 의 @Bean)
          아직 임시 클래스로더가 없으면
          --> LoadTimeWeaverAwareProcessor 추가 + 임시 클래스로더 설정
          (prepareBeanFactory 의 같은 검사는 정의가 파싱되기 전이라 놓칠 수 있다)
```

1. [PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors](01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/README.md)가 처리기를 우선순위별로 찾아 실행한다. `@Configuration`을 처리하는 `ConfigurationClassPostProcessor`도 그중 하나인데, **가장 먼저는 아니다** — 코드로 직접 넣은 Registry 처리기가 그보다 앞이고, 같은 PriorityOrdered 그룹 안에서도 `getOrder()`가 `LOWEST_PRECEDENCE`라 뒤쪽이다(`ConfigurationClassPostProcessor` L210-212, 주석 `// within PriorityOrdered`). 다른 처리기가 없는 기본 구성에서만 결과적으로 첫 번째가 된다.

## 결과가 쓰이는 곳

```text
 완성된 빈 정의 목록
      --> registerBeanPostProcessors   정의 중 BeanPostProcessor 타입을 찾아 생성
      --> registerListeners            정의 중 ApplicationListener 타입의 이름 등록
      --> preInstantiateSingletons     정의 목록 전체를 순회하며 싱글톤 생성

 @Configuration 정의의 beanClass
      --> CGLIB 하위 클래스로 교체된 상태
          preInstantiateSingletons 에서 이 하위 클래스가 인스턴스화됨
```

## 하위 메서드

- [01 PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors](01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/README.md)
