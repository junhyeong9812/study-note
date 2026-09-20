# AbstractSockJsService.handleRequest

상위: [SockJsHttpRequestHandler.handleRequest](../README.md)

SockJS 프로토콜의 URL 규약이 코드로 드러나는 자리다. 경로 문자열 하나로 정보 요청, iframe, 순수 WebSocket, 전송 요청이 갈린다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.support` / `AbstractSockJsService.java` L377-L437 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/support/AbstractSockJsService.java#L377-L437))

```java
// AbstractSockJsService.java L377-L437
public final void handleRequest(ServerHttpRequest request, ServerHttpResponse response,
        @Nullable String sockJsPath, WebSocketHandler wsHandler) throws SockJsException {

    if (sockJsPath == null) {
        if (logger.isWarnEnabled()) {
            logger.warn(LogFormatUtils.formatValue(
                    "Expected SockJS path. Failing request: " + request.getURI(), -1, true));
        }
        response.setStatusCode(HttpStatus.NOT_FOUND);
        return;
    }

    try {
        request.getHeaders();
    }
    catch (InvalidMediaTypeException ex) {
        // As per SockJS protocol content-type can be ignored (it's always json)
    }

    String requestInfo = (logger.isDebugEnabled() ? request.getMethod() + " " + request.getURI() : null);

    try {
        if (sockJsPath.isEmpty() || sockJsPath.equals("/")) {
            if (requestInfo != null) {
                logger.debug("Processing transport request: " + requestInfo);
            }
            if ("websocket".equalsIgnoreCase(request.getHeaders().getUpgrade())) {
                response.setStatusCode(HttpStatus.BAD_REQUEST);
                return;
            }
            response.getHeaders().setContentType(new MediaType("text", "plain", StandardCharsets.UTF_8));
            response.getBody().write("Welcome to SockJS!\n".getBytes(StandardCharsets.UTF_8));
        }

        else if (sockJsPath.equals("/info")) {
            if (requestInfo != null) {
                logger.debug("Processing transport request: " + requestInfo);
            }
            this.infoHandler.handle(request, response);
        }

        else if (sockJsPath.matches("/iframe[0-9-.a-z_]*.html")) {
            if (!CollectionUtils.isEmpty(getAllowedOrigins()) && !getAllowedOrigins().contains("*") ||
                    !CollectionUtils.isEmpty(getAllowedOriginPatterns())) {
                if (requestInfo != null) {
                    logger.debug("Iframe support is disabled when an origin check is required. " +
                            "Ignoring transport request: " + requestInfo);
                }
                response.setStatusCode(HttpStatus.NOT_FOUND);
                return;
            }
            if (CollectionUtils.isEmpty(getAllowedOrigins())) {
                response.getHeaders().add(XFRAME_OPTIONS_HEADER, "SAMEORIGIN");
            }
            if (requestInfo != null) {
                logger.debug("Processing transport request: " + requestInfo);
            }
            this.iframeHandler.handle(request, response);
        }

        else if (sockJsPath.equals("/websocket")) {
```

경로가 세 조각이면 전송 요청이다.

`spring-websocket` / `org.springframework.web.socket.sockjs.support` / `AbstractSockJsService.java` L450-L486 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/support/AbstractSockJsService.java#L450-L486))

```java
// AbstractSockJsService.java L450-L486
    String[] pathSegments = StringUtils.tokenizeToStringArray(sockJsPath.substring(1), "/");
    if (pathSegments.length != 3) {
        if (logger.isWarnEnabled()) {
            logger.warn(LogFormatUtils.formatValue("Invalid SockJS path '" + sockJsPath + "' - " +
                    "required to have 3 path segments", -1, true));
        }
        if (requestInfo != null) {
            logger.debug("Ignoring transport request: " + requestInfo);
        }
        response.setStatusCode(HttpStatus.NOT_FOUND);
        return;
    }

    String serverId = pathSegments[0];
    String sessionId = pathSegments[1];
    String transport = pathSegments[2];

    if (!isWebSocketEnabled() && transport.equals("websocket")) {
        if (requestInfo != null) {
            logger.debug("WebSocket disabled. Ignoring transport request: " + requestInfo);
        }
        response.setStatusCode(HttpStatus.NOT_FOUND);
        return;
    }
    else if (!validateRequest(serverId, sessionId, transport) || !validatePath(request)) {
        if (requestInfo != null) {
            logger.debug("Ignoring transport request: " + requestInfo);
        }
        response.setStatusCode(HttpStatus.NOT_FOUND);
        return;
    }

    if (requestInfo != null) {
        logger.debug("Processing transport request: " + requestInfo);
    }
    handleTransportRequest(request, response, wsHandler, sessionId, transport);
}
```

## 동작 흐름

```text
 handleRequest(request, response, sockJsPath, wsHandler)
 |
 +-- L380 sockJsPath 가 null --> 404
 |
 +-- [경로별 분기]
 |     L399 "" 또는 "/"        --> "Welcome to SockJS!" 평문
 |                                 Upgrade 가 websocket 이면 400 (L403)
 |     L411 "/info"             --> L415 infoHandler. 서버 능력을 JSON 으로
 |                                   (websocket 지원 여부, 세션 쿠키, origin 등)
 |     L418 "/iframe*.html"     --> L434 iframeHandler
 |                                   origin 검사가 켜져 있으면 404 (L419)
 |     L437 "/websocket"        --> L442 handleRawWebSocketRequest
 |                                   SockJS 프레이밍 없이 바로 승격한다
 |
 +-- [그 밖] L449 else 로 들어와 L450 경로를 "/" 로 쪼갠다
 |     조각이 셋이 아니면 404 (L451)
 |     L463 {serverId}/{sessionId}/{transport} 로 읽는다
 |     L467 websocket 전송인데 비활성이면 404
 |     L474 validateRequest / validatePath 실패면 404
 |     L485 handleTransportRequest(request, response, wsHandler, sessionId, transport)
 |
 +-- L487 응답을 닫는다
```

```text
 serverId 가 있는 이유

 /{server}/{session}/{transport}
   server    로드 밸런서가 같은 세션을 같은 서버로 보내게 하는 힌트
             스프링은 값 자체를 쓰지 않고 형식만 검사한다
   session   세션 맵의 키
   transport 어떤 전송 방식으로 이 요청을 처리할지
```

1. 전송 요청 처리는 [TransportHandlingSockJsService.handleTransportRequest](../../02_TransportHandlingSockJsService.handleTransportRequest/README.md)로 이어진다.

## 결과가 쓰이는 곳

```text
 /info 응답
      --> 클라이언트가 이 응답을 보고 어떤 전송을 쓸지 정한다
      --> websocket 이 false 면 처음부터 HTTP 폴백으로 간다

 /iframe*.html
      --> 교차 출처에서 쿠키와 같은 출처 제약을 우회하려고 쓴다
      --> origin 검사를 켜면 제공하지 않는다. 보안과 맞바꾸는 지점이다

 /websocket (순수)
      --> SockJS 프레이밍 없이 WebSocket 으로 바로 올라간다
      --> 이 경로는 WebSocket 흐름의 핸드셰이크와 같아진다

 404 를 돌려주는 경우들
      --> 경로 형식이 어긋났거나, 전송이 비활성이거나, 검증에 실패한 때다
      --> 클라이언트는 다른 전송 방식으로 다시 시도한다
```
