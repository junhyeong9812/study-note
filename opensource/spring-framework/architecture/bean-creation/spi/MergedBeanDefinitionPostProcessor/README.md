# MergedBeanDefinitionPostProcessor

상위: [Spring 빈 생성](../../README.md) / [spi](../README.md)

병합된 빈 정의를 인스턴스화 직후에 한 번 보고, 주입 지점이나 콜백 메서드를 미리 스캔해 둔다. 정의당 한 번만 불린다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `MergedBeanDefinitionPostProcessor.java` L38-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/MergedBeanDefinitionPostProcessor.java#L38-L60))

```java
// MergedBeanDefinitionPostProcessor.java L38-L60
public interface MergedBeanDefinitionPostProcessor extends BeanPostProcessor {

    void postProcessMergedBeanDefinition(RootBeanDefinition beanDefinition, Class<?> beanType, String beanName);

    default void resetBeanDefinition(String beanName) {
    }

}
```

## 흐름에서 불리는 자리

```text
 doCreateBean [2] applyMergedBeanDefinitionPostProcessors
   인스턴스화 직후, 주입 전
   mbd.postProcessed 플래그로 정의당 1회 보장
```

- [AbstractAutowireCapableBeanFactory.doCreateBean](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/README.md)

## 구현 계층

```text
 MergedBeanDefinitionPostProcessor
   +-- AutowiredAnnotationBeanPostProcessor    @Autowired @Value 위치를 InjectionMetadata 로 캐시
   +-- InitDestroyAnnotationBeanPostProcessor  @PostConstruct @PreDestroy 메서드 수집
   |     +-- CommonAnnotationBeanPostProcessor + @Resource
   +-- ApplicationListenerDetector             리스너 빈 여부 기록

 여기서 캐시한 메타데이터를 쓰는 곳
   populateBean 의 postProcessProperties (주입)
   initializeBean 의 초기화 전 콜백 (@PostConstruct)
   registerDisposableBeanIfNecessary (@PreDestroy)
```
