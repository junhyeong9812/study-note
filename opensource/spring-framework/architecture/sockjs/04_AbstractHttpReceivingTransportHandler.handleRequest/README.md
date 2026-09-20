# AbstractHttpReceivingTransportHandler.handleRequest

상위: [Spring SockJS](../README.md)

클라이언트가 서버로 보내는 길이다. 보내는 길과 달리 요청 하나에 메시지 배열이 실려 오고, 바로 응답하고 끝낸다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.transport.handler` / `AbstractHttpReceivingTransportHandler.java` L50-L57 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/handler/AbstractHttpReceivingTransportHandler.java#L50-L57))

```java
// AbstractHttpReceivingTransportHandler.java L50-L57
public final void handleRequest(ServerHttpRequest request, ServerHttpResponse response,
        WebSocketHandler wsHandler, SockJsSession wsSession) throws SockJsException {

    Assert.notNull(wsSession, "No session");
    AbstractHttpSockJsSession sockJsSession = (AbstractHttpSockJsSession) wsSession;

    handleRequestInternal(request, response, wsHandler, sockJsSession);
}
```

`spring-websocket` / `org.springframework.web.socket.sockjs.transport.handler` / `AbstractHttpReceivingTransportHandler.java` L59-L92 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/handler/AbstractHttpReceivingTransportHandler.java#L59-L92))

```java
// AbstractHttpReceivingTransportHandler.java L59-L92
protected void handleRequestInternal(ServerHttpRequest request, ServerHttpResponse response,
        WebSocketHandler wsHandler, AbstractHttpSockJsSession sockJsSession) throws SockJsException {

    String[] messages;
    try {
        messages = readMessages(request);
    }
    catch (IOException ex) {
        logger.error("Failed to read message", ex);
        if (ex.getClass().getName().contains("Mapping")) {
            // for example, Jackson's JsonMappingException, indicating an incomplete payload
            handleReadError(response, "Payload expected.", sockJsSession.getId());
        }
        else {
            handleReadError(response, "Broken JSON encoding.", sockJsSession.getId());
        }
        return;
    }
    catch (Exception ex) {
        logger.error("Failed to read message", ex);
        handleReadError(response, "Failed to read message(s)", sockJsSession.getId());
        return;
    }
    if (messages == null) {
        handleReadError(response, "Payload expected.", sockJsSession.getId());
        return;
    }
    if (logger.isTraceEnabled()) {
        logger.trace("Received message(s): " + Arrays.toString(messages));
    }
    response.setStatusCode(getResponseStatus());
    response.getHeaders().setContentType(new MediaType("text", "plain", StandardCharsets.UTF_8));

    sockJsSession.delegateMessages(messages);
```

## 동작 흐름

```text
 handleRequest(request, response, wsHandler, wsSession)
 |
 | L53 세션이 없으면 단언 실패 (받는 길은 세션을 만들지 않는다)
 | L56 handleRequestInternal 로 위임
 |
 handleRequestInternal(...)
 |
 +-- L64 readMessages(request)
 |        전송 방식별로 본문에서 문자열 배열을 뽑는다
 |        이 커밋의 받는 길 구현은 XhrReceivingTransportHandler 하나이고
        본문 JSON 배열을 코덱으로 푼다
 |
 +-- L66 IOException
 |        예외 클래스 이름에 "Mapping" 이 들어가면 (잭슨의 불완전 페이로드)
 |          --> "Payload expected." 500
 |        아니면 --> "Broken JSON encoding." 500
 +-- L77 그 밖 예외 --> "Failed to read message(s)" 500
 +-- L82 메시지가 null --> "Payload expected." 500
 |
 | L89 전송 방식이 정한 상태 코드와 text/plain 을 쓴다
 |
 +-- L92 sockJsSession.delegateMessages(messages)
        메시지마다 WebSocketHandler.handleMessage 를 부른다
        도중에 세션이 닫히면 남은 메시지는 버리고 로그만 남긴다
```

```text
 두 길이 갈라져 있다는 뜻

 보내는 길 요청   응답을 매달아 두고 기다린다 (오래 열려 있다)
 받는 길 요청     즉시 처리하고 닫는다 (짧다)

 그래서 같은 세션의 메시지 순서는 받는 길 요청이 도착한 순서로 정해진다
 네트워크 사정으로 요청이 추월하면 순서가 뒤집힐 수 있다
```

## 결과가 쓰이는 곳

```text
 delegateMessages
      --> 위층에서 보면 WebSocket 프레임이 온 것과 구분되지 않는다
      --> STOMP 서브프로토콜 처리도 그대로 이어진다

 500 응답들
      --> 본문을 읽지 못한 경우다. 세션은 유지된다
      --> 클라이언트가 같은 메시지를 다시 보낼 수 있다

 응답 상태 코드
      --> 받는 길 전송은 xhr_send 하나이고 204(No Content)다
      --> 클라이언트 구현이 그 값을 기대한다

 예외 클래스 이름으로 분기하는 코드
      --> 잭슨에 직접 의존하지 않으려는 장치로 보인다
      --> 소스 주석은 잭슨의 JsonMappingException(불완전 페이로드)을 예로 든다
```

메시지가 흘러 들어가는 위층은 [WebSocket과 STOMP](../../websocket-stomp/README.md) 흐름에 있다.
