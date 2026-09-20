# TcpOperations

상위: [Spring STOMP 브로커 릴레이](../../README.md) / [spi](../README.md)

TCP 연결을 여는 계약이다. 메서드가 셋뿐이고, 재연결까지 맡길지가 갈린다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.tcp` / `TcpOperations.java` L31-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/tcp/TcpOperations.java#L31-L60))

```java
// TcpOperations.java L31-L60
public interface TcpOperations<P> {

    CompletableFuture<@Nullable Void> connectAsync(TcpConnectionHandler<P> connectionHandler);

    CompletableFuture<@Nullable Void> connectAsync(TcpConnectionHandler<P> connectionHandler, ReconnectStrategy reconnectStrategy);

    CompletableFuture<@Nullable Void> shutdownAsync();

}
```

## 흐름에서 불리는 자리

```text
 startInternal  L469
   tcpClient.connectAsync(핸들러, FixedIntervalReconnectStrategy(5000))
     시스템 세션은 재연결까지 맡긴다
 handleMessageInternal  L587
   tcpClient.connectAsync(핸들러)
     클라이언트 세션은 한 번만 시도한다
```

- [startInternal](../../01_StompBrokerRelayMessageHandler.startInternal/README.md)
- [handleMessageInternal](../../02_StompBrokerRelayMessageHandler.handleMessageInternal/README.md)

## 구현 계층

```text
 TcpOperations<P>
   +-- ReactorNettyTcpClient<P>   유일한 프로덕션 구현
         Reactor Netty 로 연결을 만들고 코덱으로 프레임을 자른다
         ReactorNettyCodec<P> 가 STOMP 프레임 인코딩/디코딩을 담당한다
```

## 결과가 쓰이는 곳

```text
 connectAsync(handler)
      --> 연결되면 handler.afterConnected, 실패하면 afterConnectFailure
      --> 반환 CompletableFuture 는 "시도를 시작했다"는 신호에 가깝다

 connectAsync(handler, 전략)
      --> 끊길 때마다 전략이 정한 간격으로 다시 붙는다
      --> 시스템 세션이 서버 수명 내내 유지되는 근거다

 shutdownAsync()
      --> stopInternal 에서 불린다. 열린 연결을 모두 닫는다
```
