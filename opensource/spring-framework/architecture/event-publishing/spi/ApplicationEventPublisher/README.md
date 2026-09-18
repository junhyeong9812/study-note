# ApplicationEventPublisher

상위: [Spring 이벤트 발행](../../README.md) / [spi](../README.md)

이벤트를 발행하는 쪽의 인터페이스다. `ApplicationContext`가 이것을 구현하므로, 빈은 컨텍스트 전체가 아니라 이 좁은 타입만 주입받아도 된다.

## 실제 코드

`spring-context` / `org.springframework.context` / `ApplicationEventPublisher.java` L35-L90 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/ApplicationEventPublisher.java#L35-L90))

```java
// ApplicationEventPublisher.java L35-L90
public interface ApplicationEventPublisher {

    default void publishEvent(ApplicationEvent event) {
        publishEvent((Object) event);
    }

    void publishEvent(Object event);

}
```

## 흐름에서 불리는 자리

```text
 주입
   @Autowired ApplicationEventPublisher publisher     (prepareBeanFactory 의 registerResolvableDependency)
   또는 ApplicationEventPublisherAware
 발행
   publisher.publishEvent(객체 또는 ApplicationEvent)
     --> AbstractApplicationContext.publishEvent
```

- [AbstractApplicationContext.publishEvent](../../01_AbstractApplicationContext.publishEvent/README.md)

## 구현 계층

```text
 ApplicationEventPublisher
   +-- ApplicationContext                    컨텍스트가 곧 발행자
   +-- (테스트에서는 목으로 대체하기 쉬운 지점)

 발행 형태 두 가지
   publishEvent(ApplicationEvent)   이벤트 클래스를 직접 정의
   publishEvent(Object)             임의 객체 --> PayloadApplicationEvent 로 감싸짐
```
