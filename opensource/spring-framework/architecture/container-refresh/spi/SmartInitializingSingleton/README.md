# SmartInitializingSingleton

상위: [Spring 컨테이너 기동](../../README.md) / [spi](../README.md)

lazy가 아닌 싱글톤이 **모두** 만들어진 직후 한 번 호출된다. 다른 빈 전체를 훑거나, 모든 빈이 준비된 뒤에만 가능한 등록 작업을 둘 자리다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory` / `SmartInitializingSingleton.java` L44-L58 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/SmartInitializingSingleton.java#L44-L58))

```java
// SmartInitializingSingleton.java L44-L58
public interface SmartInitializingSingleton {

    void afterSingletonsInstantiated();

}
```

## 흐름에서 불리는 자리

```text
 refresh
   --> finishBeanFactoryInitialization
         --> preInstantiateSingletons
               1) 모든 싱글톤 getBean
               2) 다시 순회하며 SmartInitializingSingleton.afterSingletonsInstantiated()
```

- [DefaultListableBeanFactory.preInstantiateSingletons](../../01_AbstractApplicationContext.refresh/09_AbstractApplicationContext.finishBeanFactoryInitialization/01_DefaultListableBeanFactory.preInstantiateSingletons/README.md)

## 구현 계층

```text
 SmartInitializingSingleton
   +-- EventListenerMethodProcessor         @EventListener 메서드를 리스너로 등록
   +-- ScheduledAnnotationBeanPostProcessor 컨텍스트 밖에서 쓰일 때 @Scheduled 등록
   +-- (JMS / Kafka 리스너 등록기 등)

 @PostConstruct 와의 차이
   @PostConstruct                   그 빈 하나가 초기화될 때 (다른 빈은 아직 없을 수 있음)
   afterSingletonsInstantiated      전체 싱글톤이 준비된 뒤 (lazy 빈은 제외)
```
