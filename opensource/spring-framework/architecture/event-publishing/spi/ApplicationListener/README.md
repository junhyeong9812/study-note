# ApplicationListener

상위: [Spring 이벤트 발행](../../README.md) / [spi](../README.md)

이벤트를 받는 쪽의 인터페이스다. 제네릭 타입이 곧 구독 대상이고, 하위 인터페이스가 타입 판정과 순서를 더 정밀하게 만든다.

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

`spring-context` / `org.springframework.context.event` / `SmartApplicationListener.java` L37-L74 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/SmartApplicationListener.java#L37-L74))

```java
// SmartApplicationListener.java L37-L74
public interface SmartApplicationListener extends ApplicationListener<ApplicationEvent>, Ordered {

    boolean supportsEventType(Class<? extends ApplicationEvent> eventType);

    default boolean supportsSourceType(@Nullable Class<?> sourceType) {
        return true;
    }

    @Override
    default int getOrder() {
        return LOWEST_PRECEDENCE;
    }

    default String getListenerId() {
        return "";
    }

}
```

`spring-context` / `org.springframework.context.event` / `GenericApplicationListener.java` L41-L71 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/GenericApplicationListener.java#L41-L71))

```java
// GenericApplicationListener.java L41-L71
public interface GenericApplicationListener extends SmartApplicationListener {

    @Override
    default boolean supportsEventType(Class<? extends ApplicationEvent> eventType) {
        return supportsEventType(ResolvableType.forClass(eventType));
    }

    boolean supportsEventType(ResolvableType eventType);

    static <E extends ApplicationEvent> GenericApplicationListener forEventType(Class<E> eventType, Consumer<E> consumer) {
        return new GenericApplicationListenerDelegate<>(eventType, consumer);
    }

}
```

## 흐름에서 불리는 자리

```text
 등록
   context.addApplicationListener(객체)             코드 등록
   ApplicationListener 타입 빈                      registerListeners 가 이름으로 등록
   ApplicationListenerDetector                      빈 생성 후 인스턴스 등록
 선별
   getApplicationListeners --> supportsEvent 로 타입 판정
 호출
   multicastEvent --> invokeListener --> onApplicationEvent
```

- [getApplicationListeners](../../02_SimpleApplicationEventMulticaster.multicastEvent/01_AbstractApplicationEventMulticaster.getApplicationListeners/README.md)
- [multicastEvent](../../02_SimpleApplicationEventMulticaster.multicastEvent/README.md)

## 구현 계층

```text
 ApplicationListener<E>
   +-- SmartApplicationListener               이벤트/소스 타입 질의 + Ordered
   |     +-- GenericApplicationListener       ResolvableType 으로 제네릭 판정
   |           +-- ApplicationListenerMethodAdapter        @EventListener 메서드
   |                 +-- TransactionalApplicationListenerMethodAdapter   @TransactionalEventListener
   +-- (람다로 등록한 리스너)                 제네릭 정보가 없어 런타임 판정이 느슨하다

 supportsAsyncExecution()
   기본 true. 문맥에 묶인 리스너는 false 로 두어 비동기 실행에서 제외된다
```
