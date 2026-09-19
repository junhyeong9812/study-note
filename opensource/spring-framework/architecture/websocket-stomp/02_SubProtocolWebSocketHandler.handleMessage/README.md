# SubProtocolWebSocketHandler.handleMessage

상위: [Spring WebSocket과 STOMP](../README.md)

승격된 세션으로 들어온 프레임 하나를 받아, 그 세션의 서브프로토콜 핸들러에게 넘긴다. WebSocket 계층과 메시징 계층의 경계다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.messaging` / `SubProtocolWebSocketHandler.java` L348-L358 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/messaging/SubProtocolWebSocketHandler.java#L348-L358))

```java
// SubProtocolWebSocketHandler.java L348-L358
public void handleMessage(WebSocketSession session, WebSocketMessage<?> message) throws Exception {
    WebSocketSessionHolder holder = this.sessions.get(session.getId());
    if (holder != null) {
        session = holder.getSession();
    }
    SubProtocolHandler protocolHandler = findProtocolHandler(session);
    protocolHandler.handleMessageFromClient(session, message, this.clientInboundChannel);
    if (holder != null) {
        holder.setHasHandledMessages();
    }
}
```

## 동작 흐름

```text
 handleMessage(session, message)
 |
 | L349 세션 id 로 보관해 둔 WebSocketSessionHolder 를 찾는다
 | L351 있으면 홀더가 들고 있는 세션(장식된 세션)으로 바꾼다
 |        동시 전송을 막는 ConcurrentWebSocketSessionDecorator 등이 여기 걸린다
 |
 | L353 findProtocolHandler(session)
 |        세션의 acceptedProtocol 로 핸들러를 고른다
 |        프로토콜이 없고 핸들러가 하나뿐이면 그것을 쓴다
 |
 | L354 protocolHandler.handleMessageFromClient(session, message, clientInboundChannel)
 |        여기서 프레임이 Message 로 바뀌어 채널로 간다
 |
 +-- L356 홀더에 "메시지를 처리했다"고 표시한다
        연결만 하고 아무 프레임도 안 보내는 세션을 걸러내는 데 쓰인다
        (timeToFirstMessage 안에 첫 메시지가 없으면 닫는다)
```

```text
 이 클래스가 겸하는 두 역할

 WebSocketHandler   클라이언트 --> 서버 프레임을 받는다 (이 메서드)
 MessageHandler     서버 --> 클라이언트 메시지를 받는다 (L364 의 동명 메서드)
                      clientOutboundChannel 의 구독자로 등록돼 있다

 이름이 같은 handleMessage 가 둘인 이유이고,
 양방향 경계가 한 클래스에 모여 있는 이유다
```

1. STOMP 프레임 파싱은 [StompSubProtocolHandler.handleMessageFromClient](01_StompSubProtocolHandler.handleMessageFromClient/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 고른 SubProtocolHandler
      --> 세션마다 고정이다. 핸드셰이크에서 정해진 프로토콜을 따른다
      --> STOMP 가 아니면 다른 구현이 들어올 수 있는 확장점이다

 clientInboundChannel
      --> 파싱된 메시지가 이 채널로 들어간다
      --> 채널 구독자(@MessageMapping 라우터, 브로커)가 이어서 처리한다

 hasHandledMessages 표시
      --> 세션 점검 작업이 "붙어만 있고 말이 없는" 연결을 정리하는 근거다
```

## 하위 메서드

- [01 StompSubProtocolHandler.handleMessageFromClient](01_StompSubProtocolHandler.handleMessageFromClient/README.md)
