# HandshakeHandler

상위: [Spring WebSocket과 STOMP](../../README.md) / [spi](../README.md)

HTTP 요청을 WebSocket으로 승격할지 정하고, 승격 자체를 수행한다. 메서드가 하나뿐이다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.server` / `HandshakeHandler.java` L35-L56 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/server/HandshakeHandler.java#L35-L56))

```java
// HandshakeHandler.java L35-L56
public interface HandshakeHandler {

    boolean doHandshake(ServerHttpRequest request, ServerHttpResponse response, WebSocketHandler wsHandler,
            Map<String, Object> attributes) throws HandshakeFailureException;

}
```

## 흐름에서 불리는 자리

```text
 WebSocketHttpRequestHandler.handleRequest  L177
   handshakeHandler.doHandshake(요청, 응답, wsHandler, attributes)
     false 면 승격 없이 끝난다 (응답은 이미 채워져 있다)
```

- [WebSocketHttpRequestHandler.handleRequest](../../01_WebSocketHttpRequestHandler.handleRequest/README.md)
- [AbstractHandshakeHandler.doHandshake](../../01_WebSocketHttpRequestHandler.handleRequest/01_AbstractHandshakeHandler.doHandshake/README.md)

## 구현 계층

```text
 HandshakeHandler
   +-- AbstractHandshakeHandler       검사와 협상 (doHandshake 가 final)
         +-- DefaultHandshakeHandler  생성자에서 Jetty 존재 여부로 전략을 고른다
                                     (ServletContextAware 전략에는 ServletContext 를 전달)

 RequestUpgradeStrategy
   이 커밋의 구현은 둘이다
     StandardWebSocketUpgradeStrategy  표준 Jakarta WebSocket API (Tomcat, Undertow 포함)
     JettyRequestUpgradeStrategy       Jetty 전용
   AbstractHandshakeHandler 가 골라 들고 있다
```

## 결과가 쓰이는 곳

```text
 true 를 돌려준 경우
      --> 연결이 WebSocket 으로 바뀌었다. 더 이상 HTTP 응답을 쓸 수 없다
      --> 이후 프레임은 넘겨준 WebSocketHandler 가 받는다

 false 를 돌려준 경우
      --> 상태 코드와 헤더는 구현이 이미 채워 두었다
      --> 호출자는 응답을 닫기만 한다

 attributes 맵
      --> 승격된 세션의 속성이 된다
      --> 인터셉터가 심은 값을 메시지 처리 단계까지 나른다
```
