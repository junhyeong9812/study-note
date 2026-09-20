# StompBrokerRelayMessageHandler.handleMessageInternal

상위: [Spring STOMP 브로커 릴레이](../README.md)

채널에서 온 메시지를 브로커로 중계하는 자리다. 내장 브로커가 구독자에게 직접 뿌리던 자리에서, 여기서는 "어느 TCP 연결로 흘려보낼지"를 정한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.simp.stomp` / `StompBrokerRelayMessageHandler.java` L504-L532 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/simp/stomp/StompBrokerRelayMessageHandler.java#L504-L532))

```java
// StompBrokerRelayMessageHandler.java L504-L532
protected void handleMessageInternal(Message<?> message) {
    String sessionId = SimpMessageHeaderAccessor.getSessionId(message.getHeaders());

    if (!isBrokerAvailable()) {
        if (sessionId == null || SYSTEM_SESSION_ID.equals(sessionId)) {
            throw new MessageDeliveryException("Message broker not active. Consider subscribing to " +
                    "receive BrokerAvailabilityEvent's from an ApplicationListener Spring bean.");
        }
        RelayConnectionHandler handler = this.connectionHandlers.get(sessionId);
        if (handler != null) {
            handler.sendStompErrorFrameToClient("Broker not available.");
            handler.clearConnection();
        }
        else {
            StompHeaderAccessor accessor = StompHeaderAccessor.create(StompCommand.ERROR);
            if (getHeaderInitializer() != null) {
                getHeaderInitializer().initHeaders(accessor);
            }
            accessor.setSessionId(sessionId);
            Principal user = SimpMessageHeaderAccessor.getUser(message.getHeaders());
            if (user != null) {
                accessor.setUser(user);
            }
            accessor.setMessage("Broker not available.");
            MessageHeaders headers = accessor.getMessageHeaders();
            getClientOutboundChannel().send(MessageBuilder.createMessage(EMPTY_PAYLOAD, headers));
        }
        return;
    }
```

명령별 분기는 뒤쪽에 있다.

`spring-messaging` / `org.springframework.messaging.simp.stomp` / `StompBrokerRelayMessageHandler.java` L569-L618 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/simp/stomp/StompBrokerRelayMessageHandler.java#L569-L618))

```java
// StompBrokerRelayMessageHandler.java L569-L618
if (StompCommand.CONNECT.equals(command) || StompCommand.STOMP.equals(command)) {
    if (this.connectionHandlers.get(sessionId) != null) {
        if (logger.isWarnEnabled()) {
            logger.warn("Ignoring CONNECT in session " + sessionId + ". Already connected.");
        }
        return;
    }
    if (logger.isDebugEnabled()) {
        logger.debug(stompHeaderAccessor.getShortLogMessage(EMPTY_PAYLOAD));
    }
    stompHeaderAccessor = (stompHeaderAccessor.isMutable() ? stompHeaderAccessor : StompHeaderAccessor.wrap(message));
    stompHeaderAccessor.setLogin(this.clientLogin);
    stompHeaderAccessor.setPasscode(this.clientPasscode);
    stompHeaderAccessor.setHost(getVirtualHost() != null ? getVirtualHost() : null);
    RelayConnectionHandler handler = new RelayConnectionHandler(sessionId, stompHeaderAccessor);
    this.connectionHandlers.put(sessionId, handler);
    this.stats.incrementConnectCount();
    Assert.state(this.tcpClient != null, "No TCP client available");
    this.tcpClient.connectAsync(handler);
}
else if (StompCommand.DISCONNECT.equals(command)) {
    RelayConnectionHandler handler = this.connectionHandlers.get(sessionId);
    if (handler == null) {
        if (logger.isDebugEnabled()) {
            logger.debug("Ignoring DISCONNECT in session " + sessionId + ". Connection already cleaned up.");
        }
        return;
    }
    this.stats.incrementDisconnectCount();
    handler.forward(message, stompHeaderAccessor);
}
else {
    RelayConnectionHandler handler = this.connectionHandlers.get(sessionId);
    if (handler == null) {
        if (logger.isDebugEnabled()) {
            logger.debug("No TCP connection for session " + sessionId + " in " + message);
        }
        return;
    }

    String destination = stompHeaderAccessor.getDestination();
    if (command != null && command.requiresDestination() && !checkDestinationPrefix(destination)) {
        // Not a broker destination but send a heartbeat to keep the connection
        if (handler.shouldSendHeartbeatForIgnoredMessage()) {
            handler.forward(HEARTBEAT_MESSAGE, HEART_BEAT_ACCESSOR);
        }
        return;
    }

    handler.forward(message, stompHeaderAccessor);
```

## 동작 흐름

```text
 handleMessageInternal(message)
 |
 +-- [브로커가 죽어 있다] L507
 |     세션 id 가 없거나 시스템 세션이면 --> MessageDeliveryException
 |       "Message broker not active..."
 |     클라이언트 세션이면
 |       연결 핸들러가 있으면 L514 ERROR 프레임을 보내고 연결을 정리
 |       없으면 L517 ERROR 프레임을 직접 만들어 clientOutboundChannel 로
 |
 | [헤더 접근자 확인] L537
 |     StompHeaderAccessor 면 그대로, SimpMessageHeaderAccessor 면 감싼다
 |     둘 다 아니면 IllegalStateException
 |
 +-- [세션 id 가 없다] L558
 |     SEND 가 아니면 오류 로그 후 무시한다
 |       = 서버 안에서 보낼 수 있는 것은 SEND 뿐이다
 |     맞으면 SYSTEM_SESSION_ID 로 채운다
 |
 +-- [CONNECT 또는 STOMP] L569
 |     이미 연결이 있으면 경고 후 무시 (L570)
 |     L579 가변 접근자로 감싼 뒤
 |     L580-L582 clientLogin / clientPasscode / virtualHost 로 덮어쓴다
 |     L583 RelayConnectionHandler 를 만들어 맵에 넣고
 |     L587 tcpClient.connectAsync(handler)  재연결 전략 없이 한 번만
 |
 +-- [DISCONNECT] L589
 |     연결 핸들러가 없으면 무시, 있으면 그 연결로 흘려보낸다
 |
 +-- [그 밖] L600
       연결 핸들러가 없으면 무시 (L602)
       L610 목적지가 필요한 명령인데 접두가 맞지 않으면
              L612 하트비트가 필요한 상태일 때만 L613 하트비트를 대신 보낸다
              아니면 아무것도 보내지 않고 끝낸다
       맞으면 L618 handler.forward(message, accessor)
```

```text
 로그인 정보가 두 벌인 이유

 systemLogin / systemPasscode   시스템 세션 전용
 clientLogin / clientPasscode   클라이언트 세션 전용 (클라이언트가 보낸 값을 덮어쓴다)

 클라이언트가 보낸 login/passcode 는 무시되고 릴레이가 설정한 값이 쓰인다
 레퍼런스 문서가 "They are ignored" 라고 명시한다
 클라이언트 인증은 HTTP/WebSocket 계층에서 따로 해야 한다
```

## 결과가 쓰이는 곳

```text
 세션별 연결 핸들러 맵
      --> 이후 그 세션의 모든 프레임이 같은 TCP 연결로 간다
      --> DISCONNECT 나 연결 실패 때 맵에서 지워진다

 브로커 불가 상태의 두 갈래
      --> 서버 발신(시스템 세션)은 예외를 던져 호출자에게 알린다
      --> 클라이언트 발신은 ERROR 프레임으로 그 클라이언트에게만 알린다

 접두가 맞지 않는 메시지
      --> 브로커로 보내지 않는다. /app 으로 간 메시지가 그 경우다
      --> 클라이언트가 하트비트를 협상했고 그 주기에 보낸 것이 없을 때만
          하트비트를 대신 보낸다. 시스템 세션은 항상 보내지 않는다

 "SEND 만 허용" 규칙
      --> 세션 id 없이 서버 안에서 보내는 메시지를 SEND 로 제한한다 (L558-L564)
      --> 세션 id 를 시스템 세션으로 명시한 메시지는 이 분기를 타지 않는다
      --> 시스템 세션 자체는 기본 구성에서 수신하지 않지만,
          systemSubscriptions 가 설정되면 SUBSCRIBE 를 보내고 그 목적지를 받는다 (L999)
```
