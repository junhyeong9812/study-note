# WebSocketHandler

상위: [Spring WebSocket과 STOMP](../../README.md) / [spi](../README.md)

연결 하나의 수명 동안 일어나는 일을 받는 콜백 묶음이다. 연결, 메시지, 전송 오류, 종료 네 시점이 메서드로 나뉘어 있다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket` / `WebSocketHandler.java` L35-L80 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/WebSocketHandler.java#L35-L80))

```java
// WebSocketHandler.java L35-L80
public interface WebSocketHandler {

    void afterConnectionEstablished(WebSocketSession session) throws Exception;

    void handleMessage(WebSocketSession session, WebSocketMessage<?> message) throws Exception;

    void handleTransportError(WebSocketSession session, Throwable exception) throws Exception;

    void afterConnectionClosed(WebSocketSession session, CloseStatus closeStatus) throws Exception;

    boolean supportsPartialMessages();

}
```

## 흐름에서 불리는 자리

```text
 컨테이너가 프레임을 받으면
   handleMessage(session, message)
 연결 직후
   afterConnectionEstablished(session)
 연결 종료
   afterConnectionClosed(session, closeStatus)
```

- [SubProtocolWebSocketHandler.handleMessage](../../02_SubProtocolWebSocketHandler.handleMessage/README.md)

## 구현 계층

```text
 WebSocketHandler
   +-- AbstractWebSocketHandler           타입별 메서드로 나눠 준다
   |     +-- TextWebSocketHandler         바이너리 프레임을 거부
   |     +-- BinaryWebSocketHandler       텍스트 프레임을 거부
   +-- SubProtocolWebSocketHandler        STOMP 경로의 진입점
   |     (MessageHandler, SubProtocolCapable, SmartLifecycle 도 함께 구현)
   +-- WebSocketHandlerDecorator          장식 계열
         +-- LoggingWebSocketHandlerDecorator
         +-- ExceptionWebSocketHandlerDecorator
```

## 결과가 쓰이는 곳

```text
 supportsPartialMessages()
      --> true 면 큰 프레임이 조각난 채로 전달된다
      --> STOMP 경로는 false 다. 완전한 프레임만 받는다

 handleTransportError
      --> 전송 계층 오류다. 애플리케이션 오류와 구분된다
      --> 대개 세션을 닫는 것으로 끝낸다

 afterConnectionClosed
      --> 세션 정리, 구독 해제, 통계 갱신이 여기 걸린다
      --> 정상 종료와 비정상 종료를 CloseStatus 로 구분한다
```
