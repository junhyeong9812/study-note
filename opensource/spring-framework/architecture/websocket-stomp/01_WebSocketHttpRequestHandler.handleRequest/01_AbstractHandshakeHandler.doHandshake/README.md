# AbstractHandshakeHandler.doHandshake

상위: [WebSocketHttpRequestHandler.handleRequest](../README.md)

승격해도 되는 요청인지 검사하고, 서브프로토콜과 확장을 협상한 뒤, 컨테이너에 승격을 맡긴다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.server.support` / `AbstractHandshakeHandler.java` L169-L230 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/server/support/AbstractHandshakeHandler.java#L169-L230))

```java
// AbstractHandshakeHandler.java L169-L230
public final boolean doHandshake(ServerHttpRequest request, ServerHttpResponse response,
        WebSocketHandler wsHandler, Map<String, Object> attributes) throws HandshakeFailureException {

    WebSocketHttpHeaders headers = new WebSocketHttpHeaders(request.getHeaders());
    if (logger.isTraceEnabled()) {
        logger.trace("Processing request " + request.getURI() + " with headers=" + headers);
    }
    try {
        HttpMethod httpMethod = request.getMethod();
        if (HttpMethod.GET != httpMethod && !CONNECT_METHOD.equals(httpMethod)) {
            response.setStatusCode(HttpStatus.METHOD_NOT_ALLOWED);
            response.getHeaders().setAllow(Set.of(HttpMethod.GET, CONNECT_METHOD));
            if (logger.isDebugEnabled()) {
                logger.debug("Handshake failed due to unexpected HTTP method: " + httpMethod);
            }
            return false;
        }
        if (HttpMethod.GET == httpMethod) {
            if (!"WebSocket".equalsIgnoreCase(headers.getUpgrade())) {
                handleInvalidUpgradeHeader(request, response);
                return false;
            }
            List<String> connectionValue = headers.getConnection();
            if (!connectionValue.contains("Upgrade") && !connectionValue.contains("upgrade")) {
                handleInvalidConnectHeader(request, response);
                return false;
            }
            String key = headers.getSecWebSocketKey();
            if (key == null) {
                if (logger.isDebugEnabled()) {
                    logger.debug("Missing \"Sec-WebSocket-Key\" header");
                }
                response.setStatusCode(HttpStatus.BAD_REQUEST);
                return false;
            }
        }
        if (!isWebSocketVersionSupported(headers)) {
            handleWebSocketVersionNotSupported(request, response);
            return false;
        }
        if (!isValidOrigin(request)) {
            response.setStatusCode(HttpStatus.FORBIDDEN);
            return false;
        }
    }
    catch (IOException ex) {
        throw new HandshakeFailureException(
                "Response update failed during upgrade to WebSocket: " + request.getURI(), ex);
    }

    String subProtocol = selectProtocol(headers.getSecWebSocketProtocol(), wsHandler);
    List<WebSocketExtension> requested = headers.getSecWebSocketExtensions();
    List<WebSocketExtension> supported = this.requestUpgradeStrategy.getSupportedExtensions(request);
    List<WebSocketExtension> extensions = filterRequestedExtensions(request, requested, supported);
    Principal user = determineUser(request, wsHandler, attributes);

    if (logger.isTraceEnabled()) {
        logger.trace("Upgrading to WebSocket, subProtocol=" + subProtocol + ", extensions=" + extensions);
    }
    this.requestUpgradeStrategy.upgrade(request, response, subProtocol, extensions, user, wsHandler, attributes);
    return true;
}
```

## 동작 흐름

```text
 doHandshake(request, response, wsHandler, attributes)
 |
 +-- [검사] 하나라도 어긋나면 false 를 돌려주고 승격하지 않는다
 |     L178 GET 도 CONNECT 도 아니면 --> 405, Allow 헤더에 두 메서드
 |     L186 GET 인 경우
 |            Upgrade 헤더가 WebSocket 이 아니면 --> handleInvalidUpgradeHeader
 |            Connection 헤더에 Upgrade 가 없으면 --> handleInvalidConnectHeader
 |            Sec-WebSocket-Key 가 없으면 --> 400
 |     L205 지원하지 않는 버전 --> handleWebSocketVersionNotSupported
 |     L209 허용되지 않은 Origin --> 403
 |
 +-- L214 검사 중 IOException --> HandshakeFailureException
 |
 +-- [협상]
 |     L219 selectProtocol(...)      Sec-WebSocket-Protocol 중 하나를 고른다
 |     L220 요청한 확장과 지원 확장을 교집합으로 거른다
 |     L223 determineUser(...)       Principal 결정
 |
 +-- L228 requestUpgradeStrategy.upgrade(요청, 응답, 서브프로토콜, 확장, 사용자, 핸들러, 속성)
        컨테이너(Tomcat, Jetty 등)에 맞는 전략이 실제 승격을 수행한다
        L229 true 반환
```

```text
 GET 과 CONNECT

 L178 이 두 메서드만 허용한다
 GET      전통적인 WebSocket 핸드셰이크 (Upgrade 헤더 필요)
 CONNECT  HTTP/2, HTTP/3 위의 WebSocket (RFC 8441) — Upgrade 검사를 건너뛴다
```

## 결과가 쓰이는 곳

```text
 고른 서브프로토콜
      --> 승격 뒤 세션의 acceptedProtocol 이 된다
      --> SubProtocolWebSocketHandler 가 이 값으로 핸들러를 고른다
      --> STOMP 면 "v12.stomp" 같은 값이 들어온다

 determineUser 가 정한 Principal
      --> 세션의 사용자다. 사용자별 목적지(/user/...) 판정의 기준이 된다

 upgrade 호출 이후
      --> 같은 연결로 더 이상 HTTP 응답을 쓸 수 없다
      --> 이후 통신은 전부 WebSocket 프레임이다

 false 를 돌려준 경우
      --> 응답 상태는 이 메서드가 이미 채워 두었다
      --> 호출자는 추가로 아무것도 하지 않는다
```

승격 뒤 첫 프레임이 도착하면 [SubProtocolWebSocketHandler.handleMessage](../../02_SubProtocolWebSocketHandler.handleMessage/README.md)로 들어온다.
