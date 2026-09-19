# SimpleBrokerMessageHandler.handleMessageInternal

상위: [Spring WebSocket과 STOMP](../README.md)

내장 브로커다. 구독을 기억했다가 목적지에 맞는 세션들에게 메시지를 복제해 보낸다. 외부 브로커 없이도 `/topic` 이 동작하는 이유다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.simp.broker` / `SimpleBrokerMessageHandler.java` L293-L350 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/simp/broker/SimpleBrokerMessageHandler.java#L293-L350))

```java
// SimpleBrokerMessageHandler.java L293-L350
protected void handleMessageInternal(Message<?> message) {
    MessageHeaders headers = message.getHeaders();
    String destination = SimpMessageHeaderAccessor.getDestination(headers);
    String sessionId = SimpMessageHeaderAccessor.getSessionId(headers);

    updateSessionReadTime(sessionId);

    if (!checkDestinationPrefix(destination)) {
        return;
    }

    SimpMessageType messageType = SimpMessageHeaderAccessor.getMessageType(headers);
    if (SimpMessageType.MESSAGE.equals(messageType)) {
        logMessage(message);
        sendMessageToSubscribers(destination, message);
    }
    else if (SimpMessageType.CONNECT.equals(messageType)) {
        logMessage(message);
        if (sessionId != null) {
            if (this.sessions.get(sessionId) != null) {
                if (logger.isWarnEnabled()) {
                    logger.warn("Ignoring CONNECT in session " + sessionId + ". Already connected.");
                }
                return;
            }
            long[] heartbeatIn = SimpMessageHeaderAccessor.getHeartbeat(headers);
            long[] heartbeatOut = getHeartbeatValue();
            Principal user = SimpMessageHeaderAccessor.getUser(headers);
            MessageChannel outChannel = getClientOutboundChannelForSession(sessionId);
            this.sessions.put(sessionId, new SessionInfo(sessionId, user, outChannel, heartbeatIn, heartbeatOut));
            SimpMessageHeaderAccessor connectAck = SimpMessageHeaderAccessor.create(SimpMessageType.CONNECT_ACK);
            initHeaders(connectAck);
            connectAck.setSessionId(sessionId);
            if (user != null) {
                connectAck.setUser(user);
            }
            connectAck.setHeader(SimpMessageHeaderAccessor.CONNECT_MESSAGE_HEADER, message);
            connectAck.setHeader(SimpMessageHeaderAccessor.HEART_BEAT_HEADER, heartbeatOut);
            Message<byte[]> messageOut = MessageBuilder.createMessage(EMPTY_PAYLOAD, connectAck.getMessageHeaders());
            getClientOutboundChannel().send(messageOut);
        }
    }
    else if (SimpMessageType.DISCONNECT.equals(messageType)) {
        logMessage(message);
        if (sessionId != null) {
            Principal user = SimpMessageHeaderAccessor.getUser(headers);
            handleDisconnect(sessionId, user, message);
        }
    }
    else if (SimpMessageType.SUBSCRIBE.equals(messageType)) {
        logMessage(message);
        this.subscriptionRegistry.registerSubscription(message);
    }
    else if (SimpMessageType.UNSUBSCRIBE.equals(messageType)) {
        logMessage(message);
        this.subscriptionRegistry.unregisterSubscription(message);
    }
}
```

## 동작 흐름

```text
 handleMessageInternal(message)
 |
 | L295 destination, L296 sessionId 를 헤더에서 꺼낸다
 | L298 세션 읽기 시각 갱신 (하트비트 판정용)
 |
 +-- L300 목적지 접두가 맞지 않으면 조용히 반환
 |        접두를 설정했으면(관례상 /topic, /queue) 그에 맞을 때만 처리하고
 |        설정하지 않았으면 사용자 목적지를 뺀 전부를 처리한다
 |
 +-- [메시지 종류별 분기] L304
 |
 +-- MESSAGE  L305
 |      L307 sendMessageToSubscribers(destination, message)
 |             구독 등록부에서 목적지에 맞는 (세션, 구독 id) 쌍을 찾아
 |             각각에게 복제본을 보낸다
 |
 +-- CONNECT  L309
 |      L312 이미 연결된 세션이면 경고 후 무시
 |      L318 하트비트 값을 읽고 L322 세션 정보를 등록한다
 |      L323 CONNECT_ACK 메시지를 만들어 clientOutboundChannel 로 보낸다
 |             이것이 클라이언트에게 CONNECTED 프레임으로 나간다
 |
 +-- DISCONNECT  L335
        세션 정보를 지우고 구독을 정리한다
```

```text
 SimpleBroker 와 외부 브로커

 SimpleBrokerMessageHandler       메모리에 구독을 들고 직접 뿌린다
   서버가 여러 대면 구독 정보가 공유되지 않는다
   재시작하면 구독이 사라진다

 StompBrokerRelayMessageHandler   RabbitMQ 등에 TCP 로 릴레이한다
   구독과 전달을 브로커가 책임진다
   둘 다 AbstractBrokerMessageHandler 의 하위라 채널 계약은 같다
```

## 결과가 쓰이는 곳

```text
 구독 등록부
      --> SUBSCRIBE 프레임이 (세션, 구독 id, 목적지)를 여기에 넣는다
      --> MESSAGE 를 보낼 때 이 표를 훑어 대상 세션을 정한다

 복제된 메시지
      --> 구독마다 subscription 헤더가 다르게 붙는다
      --> 클라이언트가 어느 구독에 대한 메시지인지 구분할 수 있다

 CONNECT_ACK
      --> clientOutboundChannel 로 가고, STOMP 핸들러가 CONNECTED 프레임으로 만든다
      --> 하트비트 협상 결과도 이때 함께 전달된다

 접두가 맞지 않는 메시지
      --> 브로커는 손대지 않는다. /app 으로 간 메시지가 그 경우다
```

메시지가 다시 프레임이 되는 지점은 [StompSubProtocolHandler.handleMessageToClient](../06_StompSubProtocolHandler.handleMessageToClient/README.md)다.
