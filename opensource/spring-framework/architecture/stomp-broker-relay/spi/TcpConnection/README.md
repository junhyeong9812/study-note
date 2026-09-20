# TcpConnection

상위: [Spring STOMP 브로커 릴레이](../../README.md) / [spi](../README.md)

열린 연결 하나다. 보내기와 유휴 감시, 닫기만 있다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.tcp` / `TcpConnection.java` L33-L64 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/tcp/TcpConnection.java#L33-L64))

```java
// TcpConnection.java L33-L64
public interface TcpConnection<P> extends Closeable {

    CompletableFuture<@Nullable Void> sendAsync(Message<P> message);

    void onReadInactivity(Runnable runnable, long duration);

    void onWriteInactivity(Runnable runnable, long duration);

    @Override
    void close();

}
```

## 흐름에서 불리는 자리

```text
 afterConnected  L697
   connection.onReadInactivity(콜백, MAX_TIME_TO_CONNECTED_FRAME)
     CONNECTED 가 안 오면 실패 처리
   L703 connection.sendAsync(CONNECT 프레임)
 CONNECTED 수신 후 (시스템 세션만)
   하트비트 주기로 onWriteInactivity / onReadInactivity 를 다시 건다 (L1014, L1023)
 연결 정리
   connection.close()
```

- [afterConnected](../../03_RelayConnectionHandler.afterConnected/README.md)

## 구현 계층

```text
 TcpConnection<P>
   +-- ReactorNettyTcpConnection<P>   Reactor Netty 연결을 감싼다
```

## 결과가 쓰이는 곳

```text
 sendAsync(message)
      --> 프레임을 인코딩해 소켓에 쓴다
      --> 실패하면 future 가 예외로 끝나고 실패 처리로 이어진다

 onReadInactivity / onWriteInactivity
      --> 하트비트의 실제 구현이다
      --> 읽기가 없으면 연결이 죽었다고 보고, 쓰기가 없으면 하트비트를 보낸다

 close()
      --> 소켓을 닫는다. 재연결 전략이 걸려 있으면 다시 붙는다
      --> 클라이언트 세션은 전략이 없어 그대로 끝난다
```
