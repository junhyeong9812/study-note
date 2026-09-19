# AbstractMethodMessageHandler.handleMessage

상위: [Spring WebSocket과 STOMP](../README.md)

`@MessageMapping` 메서드를 찾아 부르는 라우터의 입구다. MVC의 `DispatcherServlet`이 하는 일을 메시지 세계에서 한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.handler.invocation` / `AbstractMethodMessageHandler.java` L430-L453 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/handler/invocation/AbstractMethodMessageHandler.java#L430-L453))

```java
// AbstractMethodMessageHandler.java L430-L453
public void handleMessage(Message<?> message) throws MessagingException {
    String destination = getDestination(message);
    if (destination == null) {
        return;
    }
    String lookupDestination = getLookupDestination(destination);
    if (lookupDestination == null) {
        return;
    }

    MessageHeaderAccessor headerAccessor = MessageHeaderAccessor.getMutableAccessor(message);
    headerAccessor.setHeader(DestinationPatternsMessageCondition.LOOKUP_DESTINATION_HEADER, lookupDestination);
    headerAccessor.setLeaveMutable(true);
    message = MessageBuilder.createMessage(message.getPayload(), headerAccessor.getMessageHeaders());

    if (logger.isDebugEnabled()) {
        logger.debug("Searching methods to handle " +
                headerAccessor.getShortLogMessage(message.getPayload()) +
                ", lookupDestination='" + lookupDestination + "'");
    }

    handleMessageInternal(message, lookupDestination);
    headerAccessor.setImmutable();
}
```

## 동작 흐름

```text
 handleMessage(message)
 |
 +-- L431 getDestination(message)
 |        STOMP 라면 destination 헤더다. 없으면 L433 조용히 반환
 |
 +-- L435 getLookupDestination(destination)
 |        설정된 접두(관례상 /app)로 시작하면 그 뒤만 남긴다
 |        접두가 하나도 안 맞으면 null --> L437 조용히 반환
 |        접두를 아예 설정하지 않으면 목적지가 그대로 통과한다 (기본값이 없다)
 |        = /topic/... 으로 보낸 메시지는 여기서 걸러지고 브로커만 처리한다
 |
 | L440 헤더를 가변 접근자로 복사해
 | L441 LOOKUP_DESTINATION_HEADER 에 잘라 낸 목적지를 싣고
 | L443 새 Message 를 만든다
 |
 +-- L451 handleMessageInternal(message, lookupDestination)
 |        목적지 패턴으로 핸들러 메서드를 찾아 인자를 풀어 호출한다
 |
 +-- L452 헤더를 다시 불변으로 잠근다
```

```text
 접두가 만드는 분기

 /app/greet   --> getLookupDestination 이 "/greet" 를 돌려준다
                  @MessageMapping("/greet") 가 걸린다
 /topic/chat  --> 접두가 안 맞아 null. 이 핸들러는 손대지 않는다
                  같은 채널의 브로커가 처리한다

 즉 "어디로 보냈느냐"가 곧 "누가 처리하느냐"다
```

## 결과가 쓰이는 곳

```text
 LOOKUP_DESTINATION_HEADER
      --> 매핑 조건(DestinationPatternsMessageCondition)이 이 값으로 비교한다
      --> 접두를 뗀 뒤라 @MessageMapping 에는 접두를 쓰지 않는다

 핸들러 메서드의 반환값
      --> @SendTo 가 있으면 그 목적지로, 없으면 규칙에 따라 브로커 채널로 간다
      --> 반환이 void 면 아무것도 보내지 않는다

 매칭 실패
      --> 예외 대신 조용히 끝난다 (요청-응답이 아니라 메시지이기 때문)
      --> 오타 난 목적지는 아무 반응 없이 사라진다. 디버깅 시 자주 만나는 지점이다

 헤더 잠금/해제
      --> 라우팅 동안만 가변으로 두고 끝나면 다시 잠근다
      --> 같은 메시지를 다른 구독자도 보기 때문이다
```

MVC에서 같은 일을 하는 자리는 [DispatcherServlet.doDispatch](../../webmvc-request-processing/02_DispatcherServlet.doDispatch/README.md)다.
