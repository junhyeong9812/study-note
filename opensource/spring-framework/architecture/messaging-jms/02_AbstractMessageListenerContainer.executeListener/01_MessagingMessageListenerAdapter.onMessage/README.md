# MessagingMessageListenerAdapter.onMessage

상위: [AbstractMessageListenerContainer.executeListener](../README.md)

`@JmsListener` 메서드를 감싼 리스너다. JMS 메시지를 `spring-messaging`의 `Message`로 바꾸고, 인자를 해석해 메서드를 부르고, 반환값이 있으면 응답으로 보낸다.

## 실제 코드

`spring-jms` / `org.springframework.jms.listener.adapter` / `MessagingMessageListenerAdapter.java` L77-L90 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/listener/adapter/MessagingMessageListenerAdapter.java#L77-L90))

```java
// MessagingMessageListenerAdapter.java L77-L90
@Override
public void onMessage(jakarta.jms.Message jmsMessage, @Nullable Session session) throws JMSException {
    Message<?> message = toMessagingMessage(jmsMessage);
    if (logger.isDebugEnabled()) {
        logger.debug("Processing [" + message + "]");
    }
    Object result = invokeHandler(jmsMessage, session, message);
    if (result != null) {
        handleResult(result, jmsMessage, session);
    }
    else {
        logger.trace("No result object given - no result to handle");
    }
}
```

`spring-jms` / `org.springframework.jms.listener.adapter` / `MessagingMessageListenerAdapter.java` L92-L99 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/listener/adapter/MessagingMessageListenerAdapter.java#L92-L99))

```java
// MessagingMessageListenerAdapter.java L92-L99
protected Message<?> toMessagingMessage(jakarta.jms.Message jmsMessage) {
    try {
        return (Message<?>) getMessagingMessageConverter().fromMessage(jmsMessage);
    }
    catch (JMSException ex) {
        throw new MessageConversionException("Could not convert JMS message", ex);
    }
}
```

## 동작 흐름

```text
 onMessage(jmsMessage, session)
 |
 | L79 toMessagingMessage(jmsMessage)
 |       MessagingMessageConverter 가 JMS 메시지를 Message<?> 로
 |         본문 --> payload (MessageConverter 로 객체 변환)
 |         JMS 헤더/프로퍼티 --> MessageHeaders
 |
 | L83 invokeHandler(jmsMessage, session, message)
 |       InvocableHandlerMethod 가 인자를 해석해 메서드 호출
 |         @Payload      본문
 |         @Header       헤더 하나
 |         @Headers      헤더 전체
 |         Message<?>    메시지 그대로
 |         Session       세션
 |       = MVC 의 인자 리졸버와 같은 계열의 장치
 |       예외는 ListenerExecutionFailedException 으로 감싼다
 |
 +-- L84 반환값이 있으면 handleResult(result, jmsMessage, session)
        응답 대상 결정
          @SendTo 가 있으면 그 목적지
          없으면 요청 메시지의 JMSReplyTo
        MessageConverter 로 응답 메시지를 만들어 전송
        correlationId 를 이어 붙여 요청-응답을 연결한다
```

## 결과가 쓰이는 곳

```text
 메서드 반환값
      --> 응답 메시지 (요청-응답 패턴)
      --> 반환 타입이 void 면 응답을 보내지 않는다

 변환 실패
      --> MessageConversionException
      --> 리스너 호출 전에 나므로 롤백되고 재전달된다
          (역직렬화가 불가능한 메시지는 계속 재전달될 수 있다 -- DLQ 설정이 필요한 이유)

 ListenerExecutionFailedException
      --> 컨테이너의 doExecuteListener 로 올라가 롤백을 유발한다
```

`@JmsListener` 메서드는 컨테이너가 `JmsListenerAnnotationBeanPostProcessor`로 찾아 등록하고, 등록기가 컨테이너를 만들어 이 어댑터를 붙인다. 등록은 컨테이너 기동 시점에 이뤄진다.
