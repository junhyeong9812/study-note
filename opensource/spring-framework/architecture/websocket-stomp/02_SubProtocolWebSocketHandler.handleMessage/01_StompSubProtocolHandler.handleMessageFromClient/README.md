# StompSubProtocolHandler.handleMessageFromClient

상위: [SubProtocolWebSocketHandler.handleMessage](../README.md)

바이트를 STOMP 프레임으로 파싱하고, 스프링 `Message`로 바꿔 채널에 보낸다. TCP 경계와 프레임 경계가 다르다는 사실을 여기서 흡수한다.

## 실제 코드

먼저 바이트를 프레임으로 파싱한다.

`spring-websocket` / `org.springframework.web.socket.messaging` / `StompSubProtocolHandler.java` L248-L290 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/messaging/StompSubProtocolHandler.java#L248-L290))

```java
// StompSubProtocolHandler.java L248-L290
public void handleMessageFromClient(WebSocketSession session,
        WebSocketMessage<?> webSocketMessage, MessageChannel channel) {

    List<Message<byte[]>> messages;
    try {
        ByteBuffer byteBuffer;
        if (webSocketMessage instanceof TextMessage textMessage) {
            byteBuffer = ByteBuffer.wrap(textMessage.asBytes());
        }
        else if (webSocketMessage instanceof BinaryMessage binaryMessage) {
            byteBuffer = binaryMessage.getPayload();
        }
        else {
            return;
        }

        BufferingStompDecoder decoder = this.decoders.get(session.getId());
        if (decoder == null) {
            if (!session.isOpen()) {
                logger.trace("Dropped inbound WebSocket message due to closed session");
                return;
            }
            throw new IllegalStateException("No decoder for session id '" + session.getId() + "'");
        }

        messages = decoder.decode(byteBuffer);
        if (messages.isEmpty()) {
            if (logger.isTraceEnabled()) {
                logger.trace("Incomplete STOMP frame content received in session " +
                        session + ", bufferSize=" + decoder.getBufferSize() +
                        ", bufferSizeLimit=" + decoder.getBufferSizeLimit() + ".");
            }
            return;
        }
    }
    catch (Throwable ex) {
        if (logger.isErrorEnabled()) {
            logger.error("Failed to parse " + webSocketMessage +
                    " in session " + session.getId() + ". Sending STOMP ERROR to client.", ex);
        }
        handleError(session, ex, null);
        return;
    }
```

그다음 프레임마다 헤더를 채워 채널로 보낸다.

`spring-websocket` / `org.springframework.web.socket.messaging` / `StompSubProtocolHandler.java` L292-L340 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/messaging/StompSubProtocolHandler.java#L292-L340))

```java
// StompSubProtocolHandler.java L292-L340
SessionInfo info = this.sessions.get(session.getId());
MessageChannel channelToUse = (info != null ? info.getMessageChannelToUse() : null);

for (Message<byte[]> message : messages) {
    StompHeaderAccessor headerAccessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
    Assert.state(headerAccessor != null, "No StompHeaderAccessor");

    StompCommand command = headerAccessor.getCommand();
    boolean isConnect = (StompCommand.CONNECT.equals(command) || StompCommand.STOMP.equals(command));
    String sessionId = session.getId();
    boolean sent = false;

    try {
        if (isConnect) {
            channelToUse = (this.preserveReceiveOrder ? new OrderedMessageChannelDecorator(channel, logger) : channel);
            info = new SessionInfo(channelToUse, session.getPrincipal());
            SessionInfo prevInfo = this.sessions.putIfAbsent(sessionId, info);
            Assert.state(prevInfo == null, "Session already exists");
            headerAccessor.setUserChangeCallback(info);
        }
        else {
            Assert.state(channelToUse != null, "Unknown session: " + sessionId);
        }

        headerAccessor.setSessionId(sessionId);
        headerAccessor.setSessionAttributes(session.getAttributes());
        headerAccessor.setUser(getUser(session));
        headerAccessor.setHeader(SimpMessageHeaderAccessor.HEART_BEAT_HEADER, headerAccessor.getHeartbeat());

        if (!detectImmutableMessageInterceptor(channel)) {
            headerAccessor.setImmutable();
        }

        if (logger.isTraceEnabled()) {
            logger.trace("From client: " + headerAccessor.getShortLogMessage(message.getPayload()));
        }

        if (isConnect) {
            this.stats.incrementConnectCount();
        }
        else if (StompCommand.DISCONNECT.equals(command)) {
            this.stats.incrementDisconnectCount();
        }

        try {
            SimpAttributesContextHolder.setAttributesFromMessage(message);
            sent = channelToUse.send(message);

            if (sent) {
```

## 동작 흐름

```text
 handleMessageFromClient(session, webSocketMessage, channel)
 |
 +-- [파싱] L254 TextMessage 면 바이트로, L257 BinaryMessage 면 그대로
 |     L260 둘 다 아니면 조용히 반환 (Ping/Pong 등)
 |
 | L264 세션별 BufferingStompDecoder 를 꺼낸다
 |        L266 없는데 세션이 닫혔으면 조용히 버린다
 |        L270 닫히지 않았는데 없으면 IllegalStateException
 |
 | L273 decoder.decode(byteBuffer)
 |        여러 프레임이 한 번에 올 수도, 한 프레임이 쪼개져 올 수도 있다
 |        L274 덜 왔으면 버퍼에 남겨 두고 이번에는 끝낸다
 |
 +-- L283 파싱 중 예외가 나면 handleError 로 STOMP ERROR 프레임을 돌려보낸다
 |
 +-- [프레임마다] L295 반복
       L299 StompCommand 를 꺼낸다
       L300 CONNECT 또는 STOMP 면 첫 프레임이다
         L306 순서 보존 설정이면 채널을 OrderedMessageChannelDecorator 로 감싼다
         L307 SessionInfo 를 만들어 등록 (이미 있으면 단언 실패)
       그 밖이면 L313 등록된 채널이 없으면 "Unknown session" 단언 실패
       |
       L316 세션 id, 세션 속성, 사용자, 하트비트를 헤더에 싣는다
       L321 불변 메시지 인터셉터가 없으면 헤더를 불변으로 잠근다
       |
       L338 channelToUse.send(message)   clientInboundChannel 로 보낸다
```

```text
 CONNECT 프레임이 특별한 이유

 세션 등록이 이때 일어난다
   등록 전에 다른 프레임이 오면 "Unknown session" 으로 막힌다
 순서 보존 데코레이터도 이때 씌운다
   preserveReceiveOrder 를 켜면 같은 세션의 메시지가 순서대로 처리된다
   켜지 않으면 실행기 스레드 수만큼 순서가 흐트러질 수 있다
```

## 결과가 쓰이는 곳

```text
 파싱된 Message
      --> STOMP 헤더가 MessageHeaders 로 옮겨진다
      --> destination 은 이후 라우팅의 기준이고,
          sessionId 는 응답을 어느 세션으로 보낼지의 기준이다

 세션 속성을 헤더에 싣는 것
      --> 핸드셰이크에서 심은 값이 @MessageMapping 메서드까지 따라온다

 헤더 불변화
      --> 채널을 지나며 여러 구독자가 같은 메시지를 보기 때문에
          중간에 헤더가 바뀌지 않도록 잠근다

 파싱 실패
      --> STOMP ERROR 프레임을 보낸 뒤 세션을 PROTOCOL_ERROR 로 닫는다 (L420, L544)
      --> 그냥 끊는 것과 달리 클라이언트가 끊긴 이유를 알 수 있다
```

보낸 메시지가 채널에서 어떻게 배달되는지는 [ExecutorSubscribableChannel.sendInternal](../../03_ExecutorSubscribableChannel.sendInternal/README.md)에 있다.
