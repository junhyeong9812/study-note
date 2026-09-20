# SockJsHttpRequestHandler.handleRequest

상위: [Spring SockJS](../README.md)

SockJS 요청의 입구다. 하는 일은 서블릿 요청을 감싸 `SockJsService`에 넘기는 것뿐이고, 실제 판단은 전부 그 아래에서 일어난다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.support` / `SockJsHttpRequestHandler.java` L127-L139 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/support/SockJsHttpRequestHandler.java#L127-L139))

```java
// SockJsHttpRequestHandler.java L127-L139
public void handleRequest(HttpServletRequest servletRequest, HttpServletResponse servletResponse)
        throws ServletException, IOException {

    ServerHttpRequest request = new ServletServerHttpRequest(servletRequest);
    ServerHttpResponse response = new ServletServerHttpResponse(servletResponse);

    try {
        this.sockJsService.handleRequest(request, response, getSockJsPath(servletRequest), this.webSocketHandler);
    }
    catch (Exception ex) {
        throw new SockJsException("Uncaught failure in SockJS request, uri=" + request.getURI(), ex);
    }
}
```

## 동작 흐름

```text
 handleRequest(servletRequest, servletResponse)
 |
 | L130 서블릿 요청/응답을 ServerHttpRequest/Response 로 감싼다
 |
 | L134 sockJsService.handleRequest(요청, 응답, sockJsPath, webSocketHandler)
 |        sockJsPath 는 매핑 경로를 뺀 나머지다 (L141)
 |        예: /ws/** 에 매핑했다면 "/123/abc/xhr" 같은 값
 |
 +-- L136 무슨 예외든 SockJsException 으로 감싸 던진다
```

```text
 WebSocket 쪽 입구와 비교

 WebSocketHttpRequestHandler   요청 하나가 승격 한 번
 SockJsHttpRequestHandler      요청 여러 개가 세션 하나를 이룬다
                               그래서 이 메서드는 세션 수명 동안 여러 번 불린다
```

1. URL로 갈래를 정하는 곳은 [AbstractSockJsService.handleRequest](01_AbstractSockJsService.handleRequest/README.md)다.

## 결과가 쓰이는 곳

```text
 sockJsPath
      --> 아래 단계가 이 문자열만 보고 정보 요청인지 전송 요청인지 가른다
      --> HandlerMapping 이 남긴 PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE 로 구한다

 CORS
      --> 이 핸들러는 CorsConfigurationSource 도 구현한다 (L148)
      --> SockJsService 가 CorsConfigurationSource 면 그 설정을 그대로 쓴다
      --> 교차 출처에서 HTTP 폴백을 쓰려면 필요한 부분이다

 이 핸들러 자체
      --> HttpRequestHandler 라서 HttpRequestHandlerAdapter 가 호출한다
      --> WebSocket 쪽과 마찬가지로 MVC 흐름의 한 갈래다
```

이 핸들러를 찾아 주는 매핑은 [MVC의 getHandler](../../webmvc-request-processing/02_DispatcherServlet.doDispatch/02_DispatcherServlet.getHandler/README.md)가 담당한다.

## 하위 메서드

- [01 AbstractSockJsService.handleRequest](01_AbstractSockJsService.handleRequest/README.md)
