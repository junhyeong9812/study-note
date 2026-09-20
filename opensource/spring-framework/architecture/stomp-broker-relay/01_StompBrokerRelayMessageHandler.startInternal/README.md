# StompBrokerRelayMessageHandler.startInternal

상위: [Spring STOMP 브로커 릴레이](../README.md)

기동 때 브로커에 연결 하나를 미리 열어 두는 자리다. 이 연결이 서버가 보내는 모든 메시지의 출구가 된다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.simp.stomp` / `StompBrokerRelayMessageHandler.java` L445-L474 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/simp/stomp/StompBrokerRelayMessageHandler.java#L445-L474))

```java
// StompBrokerRelayMessageHandler.java L445-L474
protected void startInternal() {
    if (this.tcpClient == null) {
        this.tcpClient = initTcpClient();
    }

    if (logger.isInfoEnabled()) {
        logger.info("Starting \"system\" session, " + this);
    }

    StompHeaderAccessor accessor = StompHeaderAccessor.create(StompCommand.CONNECT);
    accessor.setAcceptVersion("1.1,1.2");
    accessor.setLogin(this.systemLogin);
    accessor.setPasscode(this.systemPasscode);
    accessor.setHeartbeat(this.systemHeartbeatSendInterval, this.systemHeartbeatReceiveInterval);
    accessor.setHost(getVirtualHost() != null ? getVirtualHost() : null);
    accessor.setSessionId(SYSTEM_SESSION_ID);
    if (logger.isDebugEnabled()) {
        logger.debug("Forwarding " + accessor.getShortLogMessage(EMPTY_PAYLOAD));
    }

    SystemSessionConnectionHandler handler = new SystemSessionConnectionHandler(accessor);
    this.connectionHandlers.put(handler.getSessionId(), handler);

    this.stats.incrementConnectCount();
    this.tcpClient.connectAsync(handler, new FixedIntervalReconnectStrategy(5000));

    if (this.taskScheduler != null) {
        this.taskScheduler.scheduleWithFixedDelay(new ClientSendMessageCountTask(), Duration.ofMillis(5000));
    }
}
```

## 동작 흐름

```text
 startInternal()
 |
 +-- L446 TCP 클라이언트가 없으면 initTcpClient() 로 만든다
 |        기본 구현은 Reactor Netty 기반이다
 |
 | L454 CONNECT 프레임 헤더를 짓는다
 |        L455 accept-version "1.1,1.2"
 |        L456-L457 systemLogin / systemPasscode
 |        L458 시스템 하트비트 주기
 |        L459 virtualHost (설정했다면)
 |        L460 sessionId = SYSTEM_SESSION_ID
 |
 | L465 SystemSessionConnectionHandler 를 만들어
 | L466 연결 핸들러 맵에 등록한다
 |
 +-- L469 tcpClient.connectAsync(handler, FixedIntervalReconnectStrategy(5000))
        비동기로 붙고, 끊기면 5초 간격으로 다시 시도한다
```

```text
 왜 시스템 세션이 따로 필요한가

 클라이언트 세션은 클라이언트가 CONNECT 할 때 생긴다
 그런데 서버 코드(SimpMessagingTemplate.convertAndSend)는
 어느 클라이언트에도 속하지 않는다
 그 메시지를 내보낼 출구가 필요해서 기동 때 하나를 열어 둔다
```

## 결과가 쓰이는 곳

```text
 시스템 세션 연결
      --> 세션 id 가 없는 메시지는 전부 이 연결로 나간다
      --> handleMessageInternal 이 sessionId 를 SYSTEM_SESSION_ID 로 채운다

 재연결 전략
      --> 클라이언트 세션에는 주지 않는다. 시스템 세션만 자동 재연결한다
      --> 클라이언트 연결이 끊기면 그 클라이언트가 다시 CONNECT 해야 한다

 연결 성공 여부
      --> 시스템 세션이 STOMP CONNECTED 를 받으면 브로커 가용으로 본다
      --> 그 변화가 BrokerAvailabilityEvent 로 발행된다

 비동기 연결
      --> startInternal 은 연결을 기다리지 않고 돌아온다
      --> 기동 직후 잠깐은 브로커 사용 불가 상태일 수 있다
```

연결이 열린 뒤 무엇을 하는지는 [RelayConnectionHandler.afterConnected](../03_RelayConnectionHandler.afterConnected/README.md)에 있다.
