# Message

상위: [Spring 메시징 (JMS)](../../README.md) / [spi](../README.md)

`spring-messaging`의 메시지 추상화다. 페이로드와 헤더로 이뤄지며, JMS·STOMP·RSocket·Kafka 통합이 모두 이 타입으로 수렴한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging` / `Message.java` L28-L40 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/Message.java#L28-L40))

```java
// Message.java L28-L40
public interface Message<T> {

    T getPayload();

    MessageHeaders getHeaders();

}
```

`spring-messaging` / `org.springframework.messaging` / `MessageChannel.java` L26-L58 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/MessageChannel.java#L26-L58))

```java
// MessageChannel.java L26-L58
public interface MessageChannel {

    long INDEFINITE_TIMEOUT = -1;

    default boolean send(Message<?> message) {
        return send(message, INDEFINITE_TIMEOUT);
    }

    boolean send(Message<?> message, long timeout);

}
```

`spring-messaging` / `org.springframework.messaging` / `MessageHandler.java` L28-L37 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/MessageHandler.java#L28-L37))

```java
// MessageHandler.java L28-L37
public interface MessageHandler {

    void handleMessage(Message<?> message) throws MessagingException;

}
```

## 흐름에서 불리는 자리

```text
 JMS 수신
   MessagingMessageListenerAdapter 가 JMS 메시지를 Message<?> 로 바꿔
   @JmsListener 메서드에 넘긴다
 STOMP/WebSocket
   같은 Message 가 MessageChannel 을 통해 MessageHandler 로 흐른다
```

- [MessagingMessageListenerAdapter.onMessage](../../02_AbstractMessageListenerContainer.executeListener/01_MessagingMessageListenerAdapter.onMessage/README.md)

## 구현 계층

```text
 Message<T>
   +-- GenericMessage<T>        불변 구현
   +-- ErrorMessage             예외를 담은 메시지

 MessageChannel                 메시지를 보내는 파이프
   +-- SubscribableChannel      구독자에게 전달
   |     +-- ExecutorSubscribableChannel   비동기 전달
   +-- PollableChannel          받는 쪽이 꺼내 간다

 MessageHandler                 메시지를 받는 쪽
   +-- SimpAnnotationMethodMessageHandler   @MessageMapping (STOMP)
   +-- 브로커 릴레이 등
```
