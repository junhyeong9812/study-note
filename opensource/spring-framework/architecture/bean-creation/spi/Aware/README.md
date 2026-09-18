# Aware

상위: [Spring 빈 생성](../../README.md) / [spi](../README.md)

컨테이너가 가진 것을 빈에게 건네주는 콜백 인터페이스 묶음이다. 표시용 상위 인터페이스 `Aware` 자체에는 메서드가 없고, 하위 인터페이스마다 세터가 하나씩 있다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory` / `Aware.java` L35-L37 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/Aware.java#L35-L37))

```java
// Aware.java L35-L37
public interface Aware {

}
```

`spring-beans` / `org.springframework.beans.factory` / `BeanNameAware.java` L36-L52 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/BeanNameAware.java#L36-L52))

```java
// BeanNameAware.java L36-L52
public interface BeanNameAware extends Aware {

    void setBeanName(String name);

}
```

`spring-beans` / `org.springframework.beans.factory` / `BeanFactoryAware.java` L41-L55 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/BeanFactoryAware.java#L41-L55))

```java
// BeanFactoryAware.java L41-L55
public interface BeanFactoryAware extends Aware {

    void setBeanFactory(BeanFactory beanFactory) throws BeansException;

}
```

## 흐름에서 불리는 자리

```text
 initializeBean [1] invokeAwareMethods        (빈 팩토리가 직접 호출)
   BeanNameAware / BeanClassLoaderAware / BeanFactoryAware
 initializeBean [2] 초기화 전 후처리기
   ApplicationContextAwareProcessor 가 나머지를 호출
   EnvironmentAware, EmbeddedValueResolverAware, ResourceLoaderAware,
   ApplicationEventPublisherAware, MessageSourceAware, ApplicationStartupAware,
   ApplicationContextAware
```

- [initializeBean](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/03_AbstractAutowireCapableBeanFactory.initializeBean/README.md)
- [컨테이너 기동의 prepareBeanFactory](../../../container-refresh/01_AbstractApplicationContext.refresh/03_AbstractApplicationContext.prepareBeanFactory/README.md)

## 구현 계층

```text
 Aware (마커)
   +-- BeanNameAware            자기 빈 이름
   +-- BeanClassLoaderAware     클래스로더
   +-- BeanFactoryAware         자신을 만든 팩토리
   +-- ApplicationContextAware  컨텍스트 전체        (컨텍스트에서만)
   +-- EnvironmentAware / ResourceLoaderAware / ApplicationEventPublisherAware /
       MessageSourceAware / ApplicationStartupAware / EmbeddedValueResolverAware

 주의: Aware 계열은 컨테이너에 대한 결합을 만든다
       주입으로 대체할 수 있으면 주입이 낫다 (ApplicationContext 는 주입도 가능)
```
