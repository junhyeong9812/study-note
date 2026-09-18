# EventListenerFactory

상위: [Spring 이벤트 발행](../../README.md) / [spi](../README.md)

`@EventListener` 메서드 하나를 `ApplicationListener` 구현으로 바꾸는 공장이다. 어떤 어댑터를 쓸지가 이 구현으로 갈린다.

## 실제 코드

`spring-context` / `org.springframework.context.event` / `EventListenerFactory.java` L30-L48 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/EventListenerFactory.java#L30-L48))

```java
// EventListenerFactory.java L30-L48
public interface EventListenerFactory {

    boolean supportsMethod(Method method);

    ApplicationListener<?> createApplicationListener(String beanName, Class<?> type, Method method);

}
```

## 흐름에서 불리는 자리

```text
 EventListenerMethodProcessor.processBean
   @EventListener 메서드를 찾고
   factories 를 순서대로 물어 supportsMethod 가 true 인 첫 공장이
   createApplicationListener 로 어댑터를 만든다
   --> context.addApplicationListener(어댑터)
```

- [ApplicationListenerMethodAdapter.processEvent](../../03_ApplicationListenerMethodAdapter.processEvent/README.md)
- [이벤트 발행 루트의 등록 절](../../README.md)

## 구현 계층

```text
 EventListenerFactory
   +-- DefaultEventListenerFactory              order 가 가장 낮음(마지막 후보)
   |     --> ApplicationListenerMethodAdapter
   +-- TransactionalEventListenerFactory        @TransactionalEventListener 전용, 우선순위 앞
         --> TransactionalApplicationListenerMethodAdapter

 등록
   AnnotationConfigUtils.registerAnnotationConfigProcessors 가
   DefaultEventListenerFactory 를 빈 정의로 등록한다
   트랜잭션 쪽 공장은 @EnableTransactionManagement 설정이 등록한다
```
