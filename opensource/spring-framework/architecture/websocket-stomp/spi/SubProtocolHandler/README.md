# SubProtocolHandler

상위: [Spring WebSocket과 STOMP](../../README.md) / [spi](../README.md)

WebSocket 프레임과 스프링 `Message` 사이를 오가는 번역기다. 이 인터페이스 덕분에 STOMP가 아닌 다른 서브프로토콜도 같은 뼈대에 끼울 수 있다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.messaging` / `SubProtocolHandler.java` L44-L89 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/messaging/SubProtocolHandler.java#L44-L89))

```java
// SubProtocolHandler.java L44-L89
public interface SubProtocolHandler {

    List<String> getSupportedProtocols();

    void handleMessageFromClient(WebSocketSession session, WebSocketMessage<?> message, MessageChannel outputChannel)
            throws Exception;

    void handleMessageToClient(WebSocketSession session, Message<?> message) throws Exception;

    @Nullable String resolveSessionId(Message<?> message);

    void afterSessionStarted(WebSocketSession session, MessageChannel outputChannel) throws Exception;

    void afterSessionEnded(WebSocketSession session, CloseStatus closeStatus, MessageChannel outputChannel)
            throws Exception;

}
```

## 흐름에서 불리는 자리

```text
 SubProtocolWebSocketHandler.handleMessage   L354
   handleMessageFromClient(session, 프레임, clientInboundChannel)
 SubProtocolWebSocketHandler.handleMessage(Message)  L364 이후
   handleMessageToClient(session, 메시지)
 연결/해제 시
   afterSessionStarted / afterSessionEnded
```

- [StompSubProtocolHandler.handleMessageFromClient](../../02_SubProtocolWebSocketHandler.handleMessage/01_StompSubProtocolHandler.handleMessageFromClient/README.md)
- [StompSubProtocolHandler.handleMessageToClient](../../06_StompSubProtocolHandler.handleMessageToClient/README.md)

## 구현 계층

```text
 SubProtocolHandler
   +-- StompSubProtocolHandler    유일한 기본 구현
         ApplicationEventPublisherAware 도 구현해 세션 이벤트를 발행한다

 getSupportedProtocols()
   "v10.stomp", "v11.stomp", "v12.stomp" 같은 값을 돌려준다
   핸드셰이크에서 고른 프로토콜과 맞춰 핸들러를 고른다
```

## 결과가 쓰이는 곳

```text
 resolveSessionId(message)
      --> 서버 --> 클라이언트 메시지를 어느 세션으로 보낼지 정한다
      --> 헤더의 sessionId 가 없으면 보낼 곳을 알 수 없어 버려진다

 handleMessageFromClient 가 채널을 인자로 받는다는 점
      --> 핸들러가 채널을 들고 있지 않다는 뜻이다
      --> 세션마다 다른 채널(순서 보존 데코레이터)을 쓸 수 있는 여지가 된다

 afterSessionEnded
      --> STOMP 구현은 여기서 DISCONNECT 메시지를 만들어 채널로 보낸다
      --> 클라이언트가 DISCONNECT 없이 끊어도 서버는 정리할 수 있다
```
