# WebSocketHttpRequestHandler.handleRequest

상위: [Spring WebSocket과 STOMP](../README.md)

핸드셰이크 요청의 입구다. 이 지점까지는 평범한 HTTP 요청이고, 여기를 지나면 연결이 WebSocket으로 바뀐다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.server.support` / `WebSocketHttpRequestHandler.java` L160-L195 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/server/support/WebSocketHttpRequestHandler.java#L160-L195))

```java
// WebSocketHttpRequestHandler.java L160-L195
public void handleRequest(HttpServletRequest servletRequest, HttpServletResponse servletResponse)
        throws ServletException, IOException {

    ServerHttpRequest request = new ServletServerHttpRequest(servletRequest);
    ServerHttpResponse response = new ServletServerHttpResponse(servletResponse);

    HandshakeInterceptorChain chain = new HandshakeInterceptorChain(this.interceptors, this.wsHandler);
    HandshakeFailureException failure = null;

    try {
        if (logger.isDebugEnabled()) {
            logger.debug(servletRequest.getMethod() + " " + servletRequest.getRequestURI());
        }
        Map<String, Object> attributes = new HashMap<>();
        if (!chain.applyBeforeHandshake(request, response, attributes)) {
            return;
        }
        this.handshakeHandler.doHandshake(request, response, this.wsHandler, attributes);
        chain.applyAfterHandshake(request, response, null);
    }
    catch (HandshakeFailureException ex) {
        failure = ex;
    }
    catch (Exception ex) {
        failure = new HandshakeFailureException(
                "Uncaught failure for request " + request.getURI() + " - " + ex.getMessage(), ex);
    }
    finally {
        if (failure != null) {
            chain.applyAfterHandshake(request, response, failure);
            response.close();
            throw failure;
        }
        response.close();
    }
}
```

## 동작 흐름

```text
 handleRequest(servletRequest, servletResponse)
 |
 | L163 서블릿 요청/응답을 ServerHttpRequest/Response 로 감싼다
 | L166 HandshakeInterceptorChain 을 만든다 (인터셉터 + 핸들러)
 |
 +-- L173 attributes 맵을 만든다
 |        인터셉터가 여기에 담은 값이 세션 속성이 된다
 |
 +-- L174 chain.applyBeforeHandshake(...)
 |        하나라도 false 면 --> L175 승격하지 않고 그대로 반환
 |        인증 실패나 Origin 거부를 여기서 처리한다
 |
 | L177 handshakeHandler.doHandshake(요청, 응답, wsHandler, attributes)
 | L178 chain.applyAfterHandshake(요청, 응답, null)
 |
 +-- L180 HandshakeFailureException 이면 그대로 보관
 +-- L183 그 밖 예외는 HandshakeFailureException 으로 감싼다
 |
 +-- L187 finally
        실패가 있었으면 applyAfterHandshake(..., 실패) 후 응답을 닫고 다시 던진다
        성공이면 응답만 닫는다
```

```text
 인터셉터가 하는 일

 applyBeforeHandshake   승격 전 검사와 속성 심기
   HttpSessionHandshakeInterceptor  HTTP 세션 속성을 WebSocket 속성으로 복사
   OriginHandshakeInterceptor       허용된 Origin 인지 검사
 applyAfterHandshake    승격 후(또는 실패 후) 정리
```

1. 실제 승격 판정은 [AbstractHandshakeHandler.doHandshake](01_AbstractHandshakeHandler.doHandshake/README.md)에서 한다.

## 결과가 쓰이는 곳

```text
 attributes 맵
      --> 승격된 WebSocketSession 의 속성이 된다
      --> 인증 정보를 여기에 담아 메시지 처리 단계에서 꺼내 쓰는 패턴이 흔하다

 applyBeforeHandshake 가 false 를 돌려주면
      --> 응답은 인터셉터가 이미 채운 상태여야 한다 (상태 코드 등)
      --> 이 메서드는 아무것도 덧붙이지 않고 끝낸다

 HandshakeFailureException
      --> finally 에서 응답을 닫은 뒤 다시 던진다
      --> 서블릿 컨테이너의 오류 처리로 올라간다

 이 핸들러 자체
      --> HttpRequestHandler 라서 HttpRequestHandlerAdapter 가 호출한다
      --> 즉 MVC 요청 처리 흐름의 한 갈래로 들어와 있다
```

이 핸들러를 찾아 주는 매핑은 [MVC의 getHandler](../../webmvc-request-processing/02_DispatcherServlet.doDispatch/02_DispatcherServlet.getHandler/README.md)가 담당한다.

## 하위 메서드

- [01 AbstractHandshakeHandler.doHandshake](01_AbstractHandshakeHandler.doHandshake/README.md)
