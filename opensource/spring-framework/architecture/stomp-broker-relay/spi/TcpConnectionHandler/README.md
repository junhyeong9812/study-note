# TcpConnectionHandler

상위: [Spring STOMP 브로커 릴레이](../../README.md) / [spi](../README.md)

연결 수명 동안 일어나는 일을 받는 콜백 묶음이다. 릴레이의 세션별 핸들러가 이것을 구현한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.tcp` / `TcpConnectionHandler.java` L29-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/tcp/TcpConnectionHandler.java#L29-L60))

```java
// TcpConnectionHandler.java L29-L60
public interface TcpConnectionHandler<P> {

    void afterConnected(TcpConnection<P> connection);

    void afterConnectFailure(Throwable ex);

    void handleMessage(Message<P> message);

    void handleFailure(Throwable ex);

    void afterConnectionClosed();

}
```

## 흐름에서 불리는 자리

```text
 afterConnected(connection)     TCP 가 열렸다. CONNECT 프레임을 보낸다
 afterConnectFailure(ex)        붙지 못했다. 실패 처리
 handleMessage(message)         브로커가 프레임을 보냈다
 handleFailure(ex)              전송/수신 중 오류
 afterConnectionClosed()        연결이 닫혔다
```

- [afterConnected](../../03_RelayConnectionHandler.afterConnected/README.md)
- [handleMessage](../../04_RelayConnectionHandler.handleMessage/README.md)

## 구현 계층

```text
 TcpConnectionHandler<P>
   +-- StompTcpConnectionHandler<P>    STOMP 전용 확장 (연결 헤더를 노출한다)
         +-- RelayConnectionHandler          클라이언트 세션 하나
               +-- SystemSessionConnectionHandler  시스템 세션 (받는 쪽 처리를 재정의)
```

## 결과가 쓰이는 곳

```text
 세션 하나에 핸들러 하나
      --> 릴레이가 세션 id 로 핸들러 맵을 들고 있다
      --> 프레임을 어느 연결로 보낼지가 이 맵으로 정해진다

 afterConnectionClosed
      --> 맵에서 핸들러를 지우고 클라이언트에게 알린다
      --> 시스템 세션이면 브로커 사용 불가로 표시된다

 handleMessage 의 인자
      --> 이미 코덱이 STOMP 프레임으로 잘라 둔 Message 다
      --> 핸들러는 바이트를 다루지 않는다
```
