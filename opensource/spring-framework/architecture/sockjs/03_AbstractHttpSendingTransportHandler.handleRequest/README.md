# AbstractHttpSendingTransportHandler.handleRequest

상위: [Spring SockJS](../README.md)

서버가 클라이언트에게 보내는 길이다. HTTP는 서버가 먼저 말할 수 없으므로, 클라이언트가 보낸 요청을 잡아 두었다가 보낼 것이 생기면 그 응답에 실어 보낸다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.transport.handler` / `AbstractHttpSendingTransportHandler.java` L56-L68 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/handler/AbstractHttpSendingTransportHandler.java#L56-L68))

```java
// AbstractHttpSendingTransportHandler.java L56-L68
public final void handleRequest(ServerHttpRequest request, ServerHttpResponse response,
        WebSocketHandler wsHandler, SockJsSession wsSession) throws SockJsException {

    AbstractHttpSockJsSession sockJsSession = (AbstractHttpSockJsSession) wsSession;

    // https://github.com/sockjs/sockjs-client/issues/130
    // sockJsSession.setAcceptedProtocol(protocol);

    // Set content type before writing
    response.getHeaders().setContentType(getContentType());

    handleRequestInternal(request, response, sockJsSession);
}
```

`spring-websocket` / `org.springframework.web.socket.sockjs.transport.handler` / `AbstractHttpSendingTransportHandler.java` L70-L95 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/handler/AbstractHttpSendingTransportHandler.java#L70-L95))

```java
// AbstractHttpSendingTransportHandler.java L70-L95
protected void handleRequestInternal(ServerHttpRequest request, ServerHttpResponse response,
        AbstractHttpSockJsSession sockJsSession) throws SockJsException {

    if (sockJsSession.isNew()) {
        if (logger.isDebugEnabled()) {
            logger.debug(request.getMethod() + " " + request.getURI());
        }
        sockJsSession.handleInitialRequest(request, response, getFrameFormat(request));
    }
    else if (sockJsSession.isClosed()) {
        if (logger.isDebugEnabled()) {
            logger.debug("Connection already closed (but not removed yet) for " + sockJsSession);
        }
        writeFrame(SockJsFrame.closeFrameGoAway(), request, response, sockJsSession);
    }
    else if (!sockJsSession.isActive()) {
        if (logger.isTraceEnabled()) {
            logger.trace("Starting " + getTransportType() + " async request.");
        }
        sockJsSession.handleSuccessiveRequest(request, response, getFrameFormat(request));
    }
    else {
        if (logger.isDebugEnabled()) {
            logger.debug("Another " + getTransportType() + " connection still open for " + sockJsSession);
        }
        writeFrame(SockJsFrame.closeFrameAnotherConnectionOpen(), request, response, sockJsSession);
```

## 동작 흐름

```text
 handleRequest(request, response, wsHandler, wsSession)
 |
 | L59 세션을 AbstractHttpSockJsSession 으로 캐스팅
 | L65 전송 방식이 정한 Content-Type 을 먼저 쓴다
 | L67 handleRequestInternal 로 위임
 |
 handleRequestInternal(request, response, sockJsSession)
 |
 +-- L73 새 세션이다
 |        L77 handleInitialRequest(...)
 |              열기 프레임 "o" 를 보낸다
 |              스트리밍은 응답을 열어 둔 채 계속 흘리고,
 |              폴링(xhr)은 열기 프레임을 쓴 뒤 곧바로 응답을 닫는다
 |
 +-- L79 이미 닫힌 세션이다
 |        L83 close 프레임(GoAway)을 보낸다
 |
 +-- L85 열려 있지만 지금 붙어 있는 요청이 없다
 |        L89 handleSuccessiveRequest(...)
 |              이번 요청을 새 출구로 매달아 둔다
 |
 +-- L91 이미 다른 요청이 붙어 있다
          L95 close 프레임(AnotherConnectionOpen)을 보낸다
          = 한 세션에 보내는 길은 하나만 허용한다
```

```text
 스트리밍과 폴링

 xhr_streaming   응답을 열어 두고 프레임을 계속 흘린다
                 일정 바이트를 넘기면 응답을 닫고 클라이언트가 다시 연결한다
 xhr (폴링)      보낼 것이 생기면 응답을 닫는다. 매번 새 요청이 온다

 둘 다 같은 메서드를 지나고, 차이는 프레임 포맷과 닫는 시점뿐이다
```

## 결과가 쓰이는 곳

```text
 매달아 둔 요청(비동기)
      --> 서버가 session.sendMessage 를 부르면 그 응답에 프레임이 실린다
      --> 보낼 것이 없으면 하트비트 프레임이 주기적으로 나간다

 열기 프레임 "o"
      --> 클라이언트는 이걸 받아야 연결이 섰다고 판단한다
      --> 이때 WebSocketHandler.afterConnectionEstablished 가 이미 불린 상태다

 "다른 연결이 열려 있음" close 프레임
      --> 같은 세션에 보내는 길을 둘 만들려는 시도를 막는다
      --> 네트워크가 바뀌며 이전 요청이 남아 있을 때 흔히 발생한다

 Content-Type 을 먼저 쓰는 이유
      --> 본문을 쓰기 시작하면 헤더를 바꿀 수 없다
```

세션이 프레임을 쓰는 규칙은 [SockJsSession](../spi/SockJsSession/README.md)과 [SockJsMessageCodec](../spi/SockJsMessageCodec/README.md)에 있다.
