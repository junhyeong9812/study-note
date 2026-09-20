# TransportHandler

상위: [Spring SockJS](../../README.md) / [spi](../README.md)

전송 방식 하나를 처리하는 계약이다. 보내는 길과 받는 길이 서로 다른 구현으로 갈라진다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.transport` / `TransportHandler.java` L32-L69 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/TransportHandler.java#L32-L69))

```java
// TransportHandler.java L32-L69
public interface TransportHandler {

    void initialize(SockJsServiceConfig serviceConfig);

    TransportType getTransportType();

    boolean checkSessionType(SockJsSession session);

    void handleRequest(ServerHttpRequest request, ServerHttpResponse response,
            WebSocketHandler handler, SockJsSession session) throws SockJsException;

}
```

## 흐름에서 불리는 자리

```text
 TransportHandlingSockJsService.handleTransportRequest
   L254 전송 타입으로 핸들러를 고른다
   L287 핸들러가 SockJsSessionFactory 면 세션을 만들 수 있다
   이어서 handleRequest(요청, 응답, wsHandler, 세션)
```

- [보내는 길](../../03_AbstractHttpSendingTransportHandler.handleRequest/README.md)
- [받는 길](../../04_AbstractHttpReceivingTransportHandler.handleRequest/README.md)

## 구현 계층

```text
 TransportHandler
   +-- AbstractTransportHandler                    공통 설정 보관
         +-- AbstractHttpSendingTransportHandler   서버 --> 클라이언트
         |     (SockJsSessionFactory 구현 — 아래 넷이 모두 상속한다)
         |     +-- XhrPollingTransportHandler
         |     +-- XhrStreamingTransportHandler
         |     +-- EventSourceTransportHandler
         |     +-- HtmlFileTransportHandler
         +-- AbstractHttpReceivingTransportHandler 클라이언트 --> 서버
         |     +-- XhrReceivingTransportHandler
         +-- WebSocketTransportHandler             WebSocket 승격 (SockJsSessionFactory)

 SockJsSessionFactory 를 함께 구현하는 핸들러만 세션을 만들 수 있다
 받는 길 핸들러는 구현하지 않는다 --> 세션이 없으면 404
```

## 결과가 쓰이는 곳

```text
 handleRequest 의 세션 인자
      --> 서비스가 찾아 두었거나 방금 만든 세션이다
      --> 핸들러는 세션 맵을 모른다. 관리는 서비스 몫이다

 initialize(SockJsServiceConfig)
      --> 하트비트 주기, 스트림 바이트 한도 같은 공통 설정을 받는다
      --> 전송 구현마다 그 값을 다르게 해석한다

 getTransportType()
      --> 서비스가 맵을 만들 때 키로 쓴다
      --> 한 타입에 핸들러 하나다
```
