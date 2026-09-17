# AbstractApplicationContext.registerBeanPostProcessors

상위: [AbstractApplicationContext.refresh](../README.md)

빈 정의 중 [BeanPostProcessor](../../spi/BeanPostProcessor/README.md) 타입을 모두 인스턴스로 만들어 팩토리의 처리기 체인에 등록한다. 이 체인은 이후 만들어지는 **모든 빈**의 생성 과정에 끼어든다(`@Autowired` 주입, `@PostConstruct` 호출, AOP 프록시 생성).

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L812-L814 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L812-L814))

```java
// AbstractApplicationContext.java L812-L814
protected void registerBeanPostProcessors(ConfigurableListableBeanFactory beanFactory) {
    PostProcessorRegistrationDelegate.registerBeanPostProcessors(beanFactory, this);
}
```

## 동작 흐름

```text
 registerBeanPostProcessors(beanFactory)
 |
 +-- PostProcessorRegistrationDelegate.registerBeanPostProcessors(beanFactory, this)
       우선순위별로 생성, 정렬, 등록
```

1. [PostProcessorRegistrationDelegate.registerBeanPostProcessors](01_PostProcessorRegistrationDelegate.registerBeanPostProcessors/README.md)가 처리기를 `PriorityOrdered`, `Ordered`, 나머지 순으로 등록하고 내부 처리기를 뒤로 옮긴다.

## 결과가 쓰이는 곳

```text
 beanFactory.beanPostProcessors (순서 있는 목록)
      --> 빈 생성 흐름의 모든 확장 지점에서 이 순서대로 호출
            인스턴스화 전   InstantiationAwareBeanPostProcessor
            주입 단계       AutowiredAnnotationBeanPostProcessor, CommonAnnotationBeanPostProcessor
            초기화 전/후    ApplicationContextAwareProcessor, @PostConstruct, AOP 프록시 생성기
      --> finishBeanFactoryInitialization 에서 만들어지는 일반 빈 전부에 적용

 이 단계 전에 만들어진 빈 (BeanFactoryPostProcessor 등)
      --> 체인이 없던 시점이라 적용을 받지 못함
```

## 하위 메서드

- [01 PostProcessorRegistrationDelegate.registerBeanPostProcessors](01_PostProcessorRegistrationDelegate.registerBeanPostProcessors/README.md)
