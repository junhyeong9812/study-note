# SockJsSession

상위: [Spring SockJS](../../README.md) / [spi](../README.md)

`WebSocketSession`을 확장한 SockJS 세션이다. 위층이 전송 방식을 몰라도 되는 이유가 이 상속 관계에 있다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.transport` / `SockJsSession.java` L28-L44 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/SockJsSession.java#L28-L44))

```java
// SockJsSession.java L28-L44
public interface SockJsSession extends WebSocketSession {

    long getTimeSinceLastActive();

    void disableHeartbeat();

}
```

## 흐름에서 불리는 자리

```text
 TransportHandlingSockJsService  세션 맵에 보관하고 찾아 준다
 전송 핸들러                     handleRequest 인자로 받아 프레임을 쓴다
 받는 길                         delegateMessages 로 메시지를 위층에 넘긴다
 위층(STOMP 등)                  WebSocketSession 으로만 본다
```

- [전송 요청 처리](../../02_TransportHandlingSockJsService.handleTransportRequest/README.md)

## 구현 계층

```text
 WebSocketSession
   +-- SockJsSession
         +-- AbstractSockJsSession              프레임 쓰기, 하트비트, 종료 처리
               +-- AbstractHttpSockJsSession    요청을 매달아 두는 HTTP 계열
               |     +-- PollingSockJsSession   보낼 것이 생기면 응답을 닫는다
               |     +-- StreamingSockJsSession 한 응답에 계속 흘린다
               +-- WebSocketServerSockJsSession SockJS 프레이밍을 쓰는 WebSocket
```

## 결과가 쓰이는 곳

```text
 sendMessage(WebSocketMessage)
      --> AbstractSockJsSession 이 텍스트만 허용한다
      --> SockJS 프로토콜이 텍스트 프레임만 정의하기 때문이다

 delegateMessages(String...)
      --> 메시지마다 WebSocketHandler.handleMessage 를 부른다
      --> 도중에 세션이 닫히면 남은 것은 버리고 로그만 남긴다

 getTimeSinceLastActive()
      --> 세션 만료 판정에 쓴다
      --> 스트리밍 응답을 끊는 판단은 따로다. StreamingSockJsSession 이
          누적 바이트가 streamBytesLimit 에 닿으면 응답을 끊는다

 위층이 WebSocketSession 으로만 본다는 점
      --> 같은 STOMP 코드가 WebSocket 과 폴백 양쪽에서 돈다
      --> 이 흐름 전체의 목적이기도 하다
```
