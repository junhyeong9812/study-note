# SockJsService

상위: [Spring SockJS](../../README.md) / [spi](../README.md)

SockJS 요청 하나를 처리하는 계약이다. 메서드가 하나뿐이고, URL 규약을 아는 것은 구현 쪽이다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs` / `SockJsService.java` L39-L63 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/SockJsService.java#L39-L63))

```java
// SockJsService.java L39-L63
public interface SockJsService {

    void handleRequest(ServerHttpRequest request, ServerHttpResponse response,
            @Nullable String sockJsPath, WebSocketHandler handler) throws SockJsException;

}
```

## 흐름에서 불리는 자리

```text
 SockJsHttpRequestHandler.handleRequest  L134
   sockJsService.handleRequest(요청, 응답, sockJsPath, wsHandler)
```

- [SockJsHttpRequestHandler.handleRequest](../../01_SockJsHttpRequestHandler.handleRequest/README.md)

## 구현 계층

```text
 SockJsService
   +-- AbstractSockJsService              URL 규약과 공통 설정 (handleRequest 가 final)
         +-- TransportHandlingSockJsService  전송 핸들러 맵을 들고 요청을 넘긴다
               +-- DefaultSockJsService      기본 전송 핸들러들을 미리 등록해 둔다

 설정 표면
   WebSocketHandlerRegistration.withSockJS()  --> SockJsServiceRegistration
     하트비트 주기, 세션 만료, 스트림 바이트 한도, 클라이언트 라이브러리 URL 등
```

## 결과가 쓰이는 곳

```text
 sockJsPath 인자
      --> 매핑 경로를 뺀 나머지 문자열이다
      --> 구현은 이 문자열만 보고 정보 요청과 전송 요청을 가른다

 WebSocketHandler 인자
      --> 세션이 만들어질 때 그 세션에 붙는다
      --> 전송 방식이 무엇이든 이 핸들러는 같은 것을 쓴다

 CorsConfigurationSource
      --> AbstractSockJsService 가 함께 구현한다
      --> 교차 출처 폴백을 위해 허용 출처를 설정으로 관리한다
```
