# JmsTemplate.doSend

상위: [JmsTemplate.execute](../README.md)

세션 위에서 실제로 메시지를 만들어 보낸다. 객체를 메시지로 바꾸는 일은 `MessageConverter`가, 만들어진 메시지를 내보내는 일은 `MessageProducer`가 한다.

## 실제 코드

`spring-jms` / `org.springframework.jms.core` / `JmsTemplate.java` L632-L652 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/core/JmsTemplate.java#L632-L652))

```java
// JmsTemplate.java L632-L652
protected void doSend(Session session, Destination destination, MessageCreator messageCreator)
        throws JMSException {

    Assert.notNull(messageCreator, "MessageCreator must not be null");
    MessageProducer producer = createProducer(session, destination);
    try {
        Message message = messageCreator.createMessage(session);
        if (logger.isDebugEnabled()) {
            logger.debug("Sending created message: " + message);
        }
        doSend(producer, message);
        // Check commit - avoid commit call within a JTA transaction.
        if (session.getTransacted() && isSessionLocallyTransacted(session)) {
            // Transacted session created by this template -> commit.
            JmsUtils.commitIfNecessary(session);
        }
    }
    finally {
        JmsUtils.closeMessageProducer(producer);
    }
}
```

## 동작 흐름

```text
 doSend(session, destination, messageCreator)
 |
 | L636 createProducer(session, destination)
 |
 | L638 messageCreator.createMessage(session)
 |        convertAndSend 경로라면 MessageConverter 가 객체를 JMS 메시지로
 |          예: 문자열 --> TextMessage, 직렬화 가능 객체 --> ObjectMessage
 |              Jackson 변환기면 JSON TextMessage
 |        MessagePostProcessor 가 지정됐으면 헤더를 더 붙일 수 있다
 |
 | L642 doSend(producer, message)
 |        explicitQosEnabled(기본 false)가 켜져 있을 때만
 |          deliveryMode, priority, timeToLive 를 붙여 send
 |        아니면 producer.send(message)
 |
 | L644 세션이 트랜잭션이고 이 템플릿이 만든 세션이면 commit
 |        외부(JTA) 트랜잭션이면 여기서 커밋하지 않는다
 |
 +-- finally  MessageProducer 닫기
```

## 결과가 쓰이는 곳

```text
 보낸 메시지
      --> 브로커의 목적지(큐/토픽)
      --> 수신 측 리스너 컨테이너가 꺼내 간다

 로컬 트랜잭션 커밋
      --> sessionTransacted = true 이고 외부 트랜잭션이 없을 때
      --> 여러 번 send 하면 각각 커밋된다 (한 execute 안의 doSend 단위)

 변환기 선택
      --> 기본 SimpleMessageConverter 는 String/byte[]/Map/Serializable 을 다룬다
      --> JSON 으로 주고받으려면 JacksonJsonMessageConverter 등을 등록한다
```
