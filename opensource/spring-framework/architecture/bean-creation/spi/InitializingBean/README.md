# InitializingBean

상위: [Spring 빈 생성](../../README.md) / [spi](../README.md)

초기화와 소멸 콜백을 인터페이스로 선언한다. 애노테이션(`@PostConstruct`, `@PreDestroy`)이나 정의의 메서드 이름 지정과 같은 자리를 차지하며, 호출 순서만 다르다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory` / `InitializingBean.java` L34-L46 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/InitializingBean.java#L34-L46))

```java
// InitializingBean.java L34-L46
public interface InitializingBean {

    void afterPropertiesSet() throws Exception;

}
```

`spring-beans` / `org.springframework.beans.factory` / `DisposableBean.java` L37-L46 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/DisposableBean.java#L37-L46))

```java
// DisposableBean.java L37-L46
public interface DisposableBean {

    void destroy() throws Exception;

}
```

## 흐름에서 불리는 자리

```text
 initializeBean [3] invokeInitMethods
   InitializingBean.afterPropertiesSet()
   그다음 init-method / @Bean(initMethod)
 registerDisposableBeanIfNecessary --> DisposableBeanAdapter
   컨테이너 close 시
     @PreDestroy --> DisposableBean.destroy() --> destroy-method
```

- [initializeBean](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/03_AbstractAutowireCapableBeanFactory.initializeBean/README.md)
- [registerDisposableBeanIfNecessary](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/04_AbstractBeanFactory.registerDisposableBeanIfNecessary/README.md)

## 구현 계층

```text
 초기화 3종 (호출 순서)
   1) @PostConstruct                      CommonAnnotationBeanPostProcessor
   2) InitializingBean.afterPropertiesSet 인터페이스
   3) init-method / @Bean(initMethod)     정의

 소멸 3종 (호출 순서)
   1) @PreDestroy
   2) DisposableBean.destroy
   3) destroy-method / @Bean(destroyMethod, 기본은 close/shutdown 추론)

 프로토타입 빈은 소멸 콜백이 불리지 않는다
```
