# ApplicationListener

상위: [Spring 컨테이너 기동](../../README.md) / [spi](../README.md)

컨텍스트가 발행하는 이벤트를 받는다. 기동 중에는 멀티캐스터가 준비되기 전 이벤트를 버퍼에 모았다가 리스너 등록 직후 한꺼번에 전달한다.

## 실제 코드

`spring-context` / `org.springframework.context` / `ApplicationListener.java` L43-L76 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/ApplicationListener.java#L43-L76))

```java
// ApplicationListener.java L43-L76
public interface ApplicationListener<E extends ApplicationEvent> extends EventListener {

    void onApplicationEvent(E event);

    default boolean supportsAsyncExecution() {
        return true;
    }

    static <T> ApplicationListener<PayloadApplicationEvent<T>> forPayload(Consumer<T> consumer) {
        return event -> consumer.accept(event.getPayload());
    }

}
```

## 흐름에서 불리는 자리

```text
 refresh
   prepareRefresh                    earlyApplicationEvents 버퍼 켜기
   initApplicationEventMulticaster   전달자 준비
   registerListeners                 리스너 연결 + 버퍼 비우기(발행)
   preInstantiateSingletons          EventListenerMethodProcessor 가 @EventListener 등록
   finishRefresh                     ContextRefreshedEvent 발행
```

- [AbstractApplicationContext.prepareRefresh](../../01_AbstractApplicationContext.refresh/01_AbstractApplicationContext.prepareRefresh/README.md)
- [AbstractApplicationContext.initApplicationEventMulticaster](../../01_AbstractApplicationContext.refresh/07_AbstractApplicationContext.initApplicationEventMulticaster/README.md)
- [AbstractApplicationContext.registerListeners](../../01_AbstractApplicationContext.refresh/08_AbstractApplicationContext.registerListeners/README.md)
- [AbstractApplicationContext.finishRefresh](../../01_AbstractApplicationContext.refresh/10_AbstractApplicationContext.finishRefresh/README.md)

## 구현 계층

```text
 ApplicationListener<E>
   +-- SmartApplicationListener             이벤트 타입 / 소스 타입으로 필터, 순서
   |     +-- GenericApplicationListener     ResolvableType 으로 제네릭 이벤트 타입 필터
   |           +-- ApplicationListenerMethodAdapter  @EventListener 메서드를 감싼 어댑터
   +-- (FrameworkServlet.ContextRefreshListener  DispatcherServlet 초기화)

 기동 중 발행되는 대표 이벤트
   ContextRefreshedEvent   refresh 완료
   (close 시) ContextClosedEvent
```
