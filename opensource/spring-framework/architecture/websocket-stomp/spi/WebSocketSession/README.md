# WebSocketSession

상위: [Spring WebSocket과 STOMP](../../README.md) / [spi](../README.md)

열린 연결 하나다. 프레임을 내보내는 통로이자, 핸드셰이크 때 심어 둔 정보를 들고 다니는 상자다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket` / `WebSocketSession.java` L38-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/WebSocketSession.java#L38-L60))

```java
// WebSocketSession.java L38-L60
public interface WebSocketSession extends Closeable {

    String getId();

    @Nullable URI getUri();

    HttpHeaders getHandshakeHeaders();

```

## 흐름에서 불리는 자리

```text
 StompSubProtocolHandler.handleMessageToClient
   session.sendMessage(TextMessage)      프레임 전송
 StompSubProtocolHandler.handleMessageFromClient
   session.getId()                       세션별 디코더와 정보 조회
   session.getAttributes()               핸드셰이크에서 심은 값
   session.getPrincipal()                사용자
```

- [StompSubProtocolHandler.handleMessageToClient](../../06_StompSubProtocolHandler.handleMessageToClient/README.md)

## 구현 계층

```text
 WebSocketSession
   +-- AbstractWebSocketSession<T>
   |     +-- StandardWebSocketSession        표준 자카르타 WebSocket API
   |     +-- (컨테이너별 네이티브 세션 구현)
   +-- WebSocketSessionDecorator             장식 계열
         +-- ConcurrentWebSocketSessionDecorator  동시 전송 직렬화, 버퍼 한도
```

```text
 동시 전송이 문제인 이유

 WebSocket 규약상 한 연결에 프레임을 동시에 쓰면 안 된다
 브로커가 여러 스레드에서 같은 세션에 보내는 일이 흔하므로
 ConcurrentWebSocketSessionDecorator 가 전송을 직렬화하고
 버퍼나 전송 시간이 한도를 넘으면 SessionLimitExceededException 을 던진다 (기본 TERMINATE)
 그 예외를 받은 SubProtocolWebSocketHandler 가 세션을 닫는다 (L386)
 DROP 전략이면 닫지 않고 오래된 메시지를 버린다
```

## 결과가 쓰이는 곳

```text
 getId()
      --> STOMP 세션 등록부, 디코더 보관, 구독 등록부의 키다

 getAttributes()
      --> 핸드셰이크 인터셉터가 심은 값이 그대로 남아 있다
      --> 메시지 헤더로 옮겨져 @MessageMapping 메서드까지 간다

 sendMessage(WebSocketMessage)
      --> 실제 네트워크 쓰기다. 여기서 IOException 이 날 수 있다
      --> 실패하면 대개 세션을 닫는다

 isOpen()
      --> 닫힌 세션에 보내려는 시도를 거르는 기준이다
      --> 프레임 파싱 단계에서도 디코더가 없으면 이 값을 먼저 본다
```
