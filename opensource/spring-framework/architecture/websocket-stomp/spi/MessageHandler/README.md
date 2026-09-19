# MessageHandler

상위: [Spring WebSocket과 STOMP](../../README.md) / [spi](../README.md)

채널에서 메시지를 받는 쪽이다. 메서드 하나뿐이라 구독자는 무엇이든 될 수 있다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging` / `MessageHandler.java` L28-L37 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/MessageHandler.java#L28-L37))

```java
// MessageHandler.java L28-L37
public interface MessageHandler {

    void handleMessage(Message<?> message) throws MessagingException;

}
```

## 흐름에서 불리는 자리

```text
 ExecutorSubscribableChannel.sendInternal
   구독자마다 SendTask 를 만들어 handler.handleMessage(message) 를 부른다
```

- [ExecutorSubscribableChannel.sendInternal](../../03_ExecutorSubscribableChannel.sendInternal/README.md)

## 구현 계층

```text
 MessageHandler
   +-- AbstractMethodMessageHandler<T>              목적지 --> 메서드 라우팅
   |     +-- SimpAnnotationMethodMessageHandler     @MessageMapping / @SubscribeMapping
   +-- AbstractBrokerMessageHandler                 브로커 공통
   |     +-- SimpleBrokerMessageHandler             내장 브로커
   |     +-- StompBrokerRelayMessageHandler         외부 브로커 릴레이
   +-- SubProtocolWebSocketHandler                  clientOutboundChannel 구독자
   +-- UserDestinationMessageHandler                /user 목적지 변환
```

```text
 한 채널에 여러 구독자

 clientInboundChannel 에는 라우터와 브로커가 함께 붙는다
 같은 메시지를 둘 다 받고, 각자 목적지 접두로 걸러 낸다
 그래서 "처리되지 않은 메시지"가 예외 없이 조용히 사라질 수 있다
```

## 결과가 쓰이는 곳

```text
 예외를 던지면
      --> SendTask 가 MessageDeliveryException 으로 감싼다
      --> 다른 구독자에게는 영향이 없다 (구독자마다 별도 태스크다)

 반환값이 없다는 점
      --> 요청-응답이 아니라 단방향 배달이다
      --> 응답이 필요하면 다른 채널로 새 메시지를 보낸다

 구독 시점
      --> 대부분 SmartLifecycle 로 기동 마지막에 채널에 등록된다
      --> 그전에 들어온 메시지는 받을 구독자가 없다
```
