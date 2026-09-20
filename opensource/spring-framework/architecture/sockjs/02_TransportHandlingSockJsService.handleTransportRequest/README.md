# TransportHandlingSockJsService.handleTransportRequest

상위: [Spring SockJS](../README.md)

전송 요청 하나를 받아 "어떤 전송 핸들러가, 어떤 세션에" 붙을지 정한다. HTTP 요청 여러 개를 세션 하나로 묶는 접합점이다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.transport` / `TransportHandlingSockJsService.java` L242-L320 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/TransportHandlingSockJsService.java#L242-L320))

```java
// TransportHandlingSockJsService.java L242-L320
protected void handleTransportRequest(ServerHttpRequest request, ServerHttpResponse response,
        WebSocketHandler handler, String sessionId, String transport) throws SockJsException {

    TransportType transportType = TransportType.fromValue(transport);
    if (transportType == null) {
        if (logger.isWarnEnabled()) {
            logger.warn(LogFormatUtils.formatValue("Unknown transport type for " + request.getURI(), -1, true));
        }
        response.setStatusCode(HttpStatus.NOT_FOUND);
        return;
    }

    TransportHandler transportHandler = this.handlers.get(transportType);
    if (transportHandler == null) {
        if (logger.isWarnEnabled()) {
            logger.warn(LogFormatUtils.formatValue("No TransportHandler for " + request.getURI(), -1, true));
        }
        response.setStatusCode(HttpStatus.NOT_FOUND);
        return;
    }

    SockJsException failure = null;
    HandshakeInterceptorChain chain = new HandshakeInterceptorChain(this.interceptors, handler);

    try {
        HttpMethod supportedMethod = transportType.getHttpMethod();
        if (supportedMethod != request.getMethod()) {
            if (request.getMethod() == HttpMethod.OPTIONS && transportType.supportsCors()) {
                if (checkOrigin(request, response, HttpMethod.OPTIONS, supportedMethod)) {
                    response.setStatusCode(HttpStatus.NO_CONTENT);
                    addCacheHeaders(response);
                }
            }
            else if (transportType.supportsCors()) {
                sendMethodNotAllowed(response, supportedMethod, HttpMethod.OPTIONS);
            }
            else {
                sendMethodNotAllowed(response, supportedMethod);
            }
            return;
        }

        SockJsSession session = this.sessions.get(sessionId);
        boolean isNewSession = false;
        if (session == null) {
            if (transportHandler instanceof SockJsSessionFactory sessionFactory) {
                Map<String, Object> attributes = new HashMap<>();
                if (!chain.applyBeforeHandshake(request, response, attributes)) {
                    return;
                }
                session = createSockJsSession(sessionId, sessionFactory, handler, attributes);
                isNewSession = true;
            }
            else {
                response.setStatusCode(HttpStatus.NOT_FOUND);
                if (logger.isDebugEnabled()) {
                    logger.debug("Session not found, sessionId=" + sessionId +
                            ". The session may have been closed " +
                            "(for example, missed heart-beat) while a message was coming in.");
                }
                return;
            }
        }
        else {
            Principal principal = session.getPrincipal();
            if (principal != null) {
                // Compare usernames, not full equality (different login timestamps)
                Principal currentPrincipal = request.getPrincipal();
                if (!principal.equals(currentPrincipal) &&
                        (currentPrincipal == null || !principal.getName().equals(currentPrincipal.getName()))) {
                    logger.debug("The user for the session and the request do not match.");
                    response.setStatusCode(HttpStatus.NOT_FOUND);
                    return;
                }
            }
            else {
                if (request.getPrincipal() != null) {
                    logger.debug("The request has a user, but the session does not.");
                    response.setStatusCode(HttpStatus.NOT_FOUND);
```

## 동작 흐름

```text
 handleTransportRequest(request, response, handler, sessionId, transport)
 |
 +-- L245 transport 문자열을 TransportType 으로 (모르면 404)
 +-- L254 그 타입의 TransportHandler 를 찾는다 (없으면 404)
 |
 | L264 HandshakeInterceptorChain 을 준비한다 (WebSocket 과 같은 인터셉터)
 |
 +-- L267 HTTP 메서드가 전송 타입이 기대하는 것과 다르면
 |      OPTIONS 이고 CORS 지원 전송이면 --> 204 + 캐시 헤더
 |      CORS 지원 전송이면 --> 405 (Allow: 기대 메서드, OPTIONS)
 |      아니면 --> 405 (Allow: 기대 메서드)
 |
 +-- L284 세션 맵에서 sessionId 로 찾는다
 |    |
 |    +-- 없다
 |    |     L286 핸들러가 SockJsSessionFactory 면
 |    |            L289 applyBeforeHandshake 로 인터셉터를 돌리고
 |    |            L292 createSockJsSession 으로 세션을 만든다
 |    |          아니면 L296 404
 |    |            = 보내는 길은 세션을 만들 수 있지만 받는 길은 못 만든다
 |    |
 |    +-- 있다
 |          L306 세션의 Principal 과 요청의 Principal 을 이름으로 비교
 |          다르면 404 (세션 도용 방지)
 |
 +-- 이어서 transportHandler.handleRequest(...) 로 넘긴다
```

```text
 전송 타입이 메서드를 정한다

 xhr, xhr_send, xhr_streaming  POST
 eventsource, htmlfile         GET
 websocket                       GET (업그레이드)

 그래서 같은 URL 이라도 메서드가 다르면 다른 전송으로 취급된다
```

1. 보내는 길은 [AbstractHttpSendingTransportHandler.handleRequest](../03_AbstractHttpSendingTransportHandler.handleRequest/README.md), 받는 길은 [AbstractHttpReceivingTransportHandler.handleRequest](../04_AbstractHttpReceivingTransportHandler.handleRequest/README.md)로 간다.

## 결과가 쓰이는 곳

```text
 만들어진 세션
      --> 세션 맵에 보관돼 이후 요청들이 같은 것을 찾는다
      --> WebSocketHandler.afterConnectionEstablished 도 이때 불린다

 인터셉터 체인
      --> WebSocket 핸드셰이크와 같은 HandshakeInterceptor 를 쓴다
      --> 그래서 인증과 속성 심기 코드를 전송 방식에 상관없이 공유한다

 Principal 비교
      --> 세션 id 만 알면 남의 세션에 붙을 수 있는 문제를 막는다
      --> 이름만 비교한다. 로그인 시각이 달라 객체가 달라질 수 있기 때문이다

 세션을 만들 수 없는 요청
      --> xhr_send 같은 받는 길 전송은 SockJsSessionFactory 가 아니다
      --> 세션이 이미 있어야만 동작한다. 없으면 404 다
```
