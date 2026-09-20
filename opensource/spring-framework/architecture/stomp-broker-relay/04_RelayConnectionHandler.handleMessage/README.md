# RelayConnectionHandler.handleMessage

상위: [Spring STOMP 브로커 릴레이](../README.md)

브로커에서 온 프레임을 받는 자리다. 세션 정보를 채워 넣은 뒤 클라이언트 쪽 채널로 흘려보낸다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.simp.stomp` / `StompBrokerRelayMessageHandler.java` L758-L783 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/simp/stomp/StompBrokerRelayMessageHandler.java#L758-L783))

```java
// StompBrokerRelayMessageHandler.java L758-L783
@Override
public void handleMessage(Message<byte[]> message) {
    StompHeaderAccessor accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
    Assert.state(accessor != null, "No StompHeaderAccessor");
    accessor.setSessionId(this.sessionId);
    Principal user = this.connectHeaders.getUser();
    if (user != null) {
        accessor.setUser(user);
    }

    StompCommand command = accessor.getCommand();
    if (StompCommand.CONNECTED.equals(command)) {
        if (logger.isDebugEnabled()) {
            logger.debug("Received " + accessor.getShortLogMessage(EMPTY_PAYLOAD));
        }
        afterStompConnected(accessor);
    }
    else if (logger.isErrorEnabled() && StompCommand.ERROR.equals(command)) {
        logger.error("Received " + accessor.getShortLogMessage(message.getPayload()));
    }
    else if (logger.isTraceEnabled()) {
        logger.trace("Received " + accessor.getDetailedLogMessage(message.getPayload()));
    }

    handleInboundMessage(message);
}
```

내보내는 것은 세션 종류에 따라 갈린다.

`spring-messaging` / `org.springframework.messaging.simp.stomp` / `StompBrokerRelayMessageHandler.java` L752-L756 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/simp/stomp/StompBrokerRelayMessageHandler.java#L752-L756))

```java
// StompBrokerRelayMessageHandler.java L752-L756
protected void handleInboundMessage(Message<?> message) {
    if (this.isRemoteClientSession) {
        this.outboundChannel.send(message);
    }
}
```

## 동작 흐름

```text
 handleMessage(message)
 |
 | L760 StompHeaderAccessor 를 꺼낸다 (없으면 단언 실패)
 | L762 세션 id 를 채운다
 |        브로커는 이 서버의 세션 개념을 모른다. 여기서 되붙인다
 | L763 연결 헤더에 사용자가 있으면 함께 채운다
 |
 +-- L769 CONNECTED 프레임
 |        L773 afterStompConnected(accessor)
 |               STOMP 연결 성립 표시, 통계 증가
 |               L792 initHeartbeats 로 브로커가 제안한 주기를 반영
 |
 +-- L775 ERROR 프레임이면 오류 로그
 |
 +-- L782 handleInboundMessage(message)
        클라이언트 세션(L753)이면 outboundChannel.send(message)
        시스템 세션은 따로 재정의해, MESSAGE 이면서 목적지가
        systemSubscriptions 에 등록된 것만 처리한다 (L1052, L1054, L1061)
```

```text
 세션 종류가 다시 갈린다

 클라이언트 세션   받은 프레임을 그대로 clientOutboundChannel 로
                   --> StompSubProtocolHandler 가 WebSocket 프레임으로 내보낸다
 시스템 세션       서버가 구독한 목적지의 메시지를 받는 자리다
                   목적지가 없거나 등록되지 않은 목적지면 로그만 남기고 버린다
                   MESSAGE 가 아닌 프레임은 로그도 없이 버린다
```

## 결과가 쓰이는 곳

```text
 채워 넣은 세션 id
      --> clientOutboundChannel 의 구독자가 어느 WebSocket 세션인지 안다
      --> 이것이 없으면 보낼 곳을 알 수 없어 메시지가 버려진다

 CONNECTED 처리
      --> 이 시점부터 그 세션으로 프레임을 보낼 수 있다
      --> 시스템 세션이면 브로커 가용 상태가 된다

 하트비트 협상
      --> 브로커가 제안한 주기와 설정값 중 큰 쪽을 쓴다
      --> 너무 짧은 주기로 트래픽이 늘지 않게 하는 장치다

 ERROR 프레임
      --> 로그를 남기고 그대로 클라이언트에게도 전달된다
      --> 브로커가 거절한 이유를 클라이언트가 볼 수 있다
```

클라이언트로 나가는 마지막 구간은 [StompSubProtocolHandler.handleMessageToClient](../../websocket-stomp/06_StompSubProtocolHandler.handleMessageToClient/README.md)에 있다.
