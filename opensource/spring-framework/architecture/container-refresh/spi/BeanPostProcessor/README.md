# BeanPostProcessor

상위: [Spring 컨테이너 기동](../../README.md) / [spi](../README.md)

빈 **인스턴스**가 만들어질 때마다 초기화 전후에 끼어들어 객체를 가공하거나 바꿔치기한다. 하위 인터페이스들이 인스턴스화 전, 주입 단계, 병합 정의 단계, 파괴 단계까지 확장 지점을 넓힌다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.config` / `BeanPostProcessor.java` L67-L111 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/config/BeanPostProcessor.java#L67-L111))

```java
// BeanPostProcessor.java L67-L111
public interface BeanPostProcessor {

    default @Nullable Object postProcessBeforeInitialization(Object bean, String beanName) throws BeansException {
        return bean;
    }

    default @Nullable Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException {
        return bean;
    }

}
```

## 흐름에서 불리는 자리

```text
 refresh
   --> registerBeanPostProcessors
         PriorityOrdered --> Ordered --> 나머지 --> internal(맨 뒤) --> ApplicationListenerDetector
   --> finishBeanFactoryInitialization --> preInstantiateSingletons --> getBean
         빈 생성 흐름 안에서 체인 순서대로 호출
```

- [AbstractApplicationContext.registerBeanPostProcessors](../../01_AbstractApplicationContext.refresh/05_AbstractApplicationContext.registerBeanPostProcessors/README.md)
- [PostProcessorRegistrationDelegate.registerBeanPostProcessors](../../01_AbstractApplicationContext.refresh/05_AbstractApplicationContext.registerBeanPostProcessors/01_PostProcessorRegistrationDelegate.registerBeanPostProcessors/README.md)
- [DefaultListableBeanFactory.preInstantiateSingletons](../../01_AbstractApplicationContext.refresh/09_AbstractApplicationContext.finishBeanFactoryInitialization/01_DefaultListableBeanFactory.preInstantiateSingletons/README.md)

## 구현 계층

```text
 BeanPostProcessor                                 초기화 전/후
   +-- InstantiationAwareBeanPostProcessor         인스턴스화 전/후, 프로퍼티 주입
   |     +-- SmartInstantiationAwareBeanPostProcessor   생성자 결정, 순환 참조용 조기 참조
   |           +-- AutowiredAnnotationBeanPostProcessor   @Autowired @Value @Inject
   |           +-- AbstractAutoProxyCreator               AOP 프록시 생성 (@Transactional @Async 기반)
   +-- MergedBeanDefinitionPostProcessor           병합 정의 후처리 (주입 메타데이터 캐시)
   +-- DestructionAwareBeanPostProcessor           파괴 직전
   |     +-- InitDestroyAnnotationBeanPostProcessor   @PostConstruct @PreDestroy
   |           +-- CommonAnnotationBeanPostProcessor  + @Resource
   |     +-- ApplicationListenerDetector           리스너 빈 등록
   |                                                (MergedBeanDefinitionPostProcessor 도 겸한다)
   +-- ApplicationContextAwareProcessor             *Aware 콜백
```
