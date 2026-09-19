# StompSubProtocolHandler.handleMessageToClient

상위: [Spring WebSocket과 STOMP](../README.md)

서버가 만든 메시지를 STOMP 프레임으로 되돌려 세션에 내보낸다. 수신 경로의 거울상이다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.messaging` / `StompSubProtocolHandler.java` L460-L515 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/messaging/StompSubProtocolHandler.java#L460-L515))

```java
// StompSubProtocolHandler.java L460-L515
public void handleMessageToClient(WebSocketSession session, Message<?> message) {
    if (!(message.getPayload() instanceof byte[] payload)) {
        if (logger.isErrorEnabled()) {
            logger.error("Expected byte[] payload. Ignoring " + message + ".");
        }
        return;
    }

    StompHeaderAccessor accessor = getStompHeaderAccessor(message);
    StompCommand command = accessor.getCommand();

    if (StompCommand.MESSAGE.equals(command)) {
        if (accessor.getSubscriptionId() == null && logger.isWarnEnabled()) {
            logger.warn("No STOMP \"subscription\" header in " + message);
        }
        String origDestination = accessor.getFirstNativeHeader(SimpMessageHeaderAccessor.ORIGINAL_DESTINATION);
        if (origDestination != null) {
            accessor = toMutableAccessor(accessor, message);
            accessor.removeNativeHeader(SimpMessageHeaderAccessor.ORIGINAL_DESTINATION);
            accessor.setDestination(origDestination);
        }
    }
    else if (StompCommand.CONNECTED.equals(command)) {
        this.stats.incrementConnectedCount();
        accessor = afterStompSessionConnected(message, accessor, session);
        if (this.eventPublisher != null) {
            try {
                SimpAttributes simpAttributes = new SimpAttributes(session.getId(), session.getAttributes());
                SimpAttributesContextHolder.setAttributes(simpAttributes);
                Principal user = getUser(session);
                publishEvent(this.eventPublisher, new SessionConnectedEvent(this, (Message<byte[]>) message, user));
            }
            finally {
                SimpAttributesContextHolder.resetAttributes();
            }
        }
    }

    if (StompCommand.ERROR.equals(command) && getErrorHandler() != null) {
        Message<byte[]> errorMessage = getErrorHandler().handleErrorMessageToClient(
                MessageBuilder.createMessage(payload, accessor.getMessageHeaders()));
        if (errorMessage != null) {
            accessor = MessageHeaderAccessor.getAccessor(errorMessage, StompHeaderAccessor.class);
            Assert.state(accessor != null, "No StompHeaderAccessor");
            payload = errorMessage.getPayload();
        }
    }

    Runnable task = OrderedMessageChannelDecorator.getNextMessageTask(message);
    if (task != null) {
        Assert.isInstanceOf(ConcurrentWebSocketSessionDecorator.class, session);
        ((ConcurrentWebSocketSessionDecorator) session).setMessageCallback(m -> task.run());
    }

    sendToClient(session, accessor, payload);
}
```

## 동작 흐름

```text
 handleMessageToClient(session, message)
 |
 +-- L461 페이로드가 byte[] 가 아니면 오류 로그 후 반환
 |        채널을 지나며 이미 바이트로 변환돼 있어야 한다
 |
 | L468 StompHeaderAccessor 를 얻고 L469 command 를 꺼낸다
 |
 +-- MESSAGE  L471
 |      L472 subscription 헤더가 없으면 경고
 |      L475 ORIGINAL_DESTINATION 네이티브 헤더가 있으면
 |             그 값을 destination 으로 되돌린다
 |             = 사용자 목적지(/user/...) 변환을 원래 표기로 복원한다
 |
 +-- CONNECTED  L482
 |      L483 통계 증가
 |      L484 afterStompSessionConnected(...)  하트비트 등 마무리
 |      L490 SessionConnectedEvent 를 발행한다
 |             SimpAttributes 를 컨텍스트에 올려 두고 발행한 뒤 되돌린다
 |
 +-- ERROR  L498
        오류 핸들러가 있으면 클라이언트에게 보낼 오류 메시지로 바꾼다
```

```text
 이 메서드에 닿는 경로

 브로커         --> clientOutboundChannel --> SubProtocolWebSocketHandler.handleMessage
                                              --> 이 메서드
 @SendTo 반환값 --> brokerChannel --> 브로커 --> 같은 경로
 SimpMessagingTemplate.convertAndSend --> brokerChannel --> 같은 경로

 즉 서버에서 나가는 모든 STOMP 프레임이 여기를 지난다
```

## 결과가 쓰이는 곳

```text
 인코딩된 프레임
      --> session.sendMessage 로 나간다
      --> 동시 전송 보호가 필요하면 세션이 데코레이터로 감싸져 있다

 SessionConnectedEvent
      --> 애플리케이션이 "누가 접속했는지" 알 수 있는 지점이다
      --> 이벤트 발행 흐름을 그대로 탄다

 ORIGINAL_DESTINATION 복원
      --> 서버 내부에서는 /user/{세션}/queue/... 같은 실제 목적지를 쓰고
          클라이언트에게는 처음 구독한 /user/queue/... 로 돌려준다

 페이로드가 byte[] 여야 하는 제약
      --> 객체를 보내면 채널 앞단의 변환기가 바이트로 바꿔 둔다
      --> 그 단계를 건너뛴 메시지는 여기서 버려지고 오류 로그만 남는다
```

이벤트가 전달되는 경로는 [이벤트 발행](../../event-publishing/README.md) 흐름에 있다.
