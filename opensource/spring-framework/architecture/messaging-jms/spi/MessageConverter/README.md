# MessageConverter

상위: [Spring 메시징 (JMS)](../../README.md) / [spi](../README.md)

자바 객체와 JMS 메시지를 서로 바꾼다. 송신에서는 객체를 메시지로, 수신에서는 메시지를 객체로 만든다.

## 실제 코드

`spring-jms` / `org.springframework.jms.support.converter` / `MessageConverter.java` L36-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/support/converter/MessageConverter.java#L36-L60))

```java
// MessageConverter.java L36-L60
public interface MessageConverter {

    Message toMessage(Object object, Session session) throws JMSException, MessageConversionException;

    @Nullable Object fromMessage(Message message) throws JMSException, MessageConversionException;

}
```

## 흐름에서 불리는 자리

```text
 송신: convertAndSend --> MessageCreator 안에서 toMessage(객체, 세션)
 수신: 어댑터의 toMessagingMessage --> fromMessage(jmsMessage)
       @JmsListener 메서드의 @Payload 타입으로 변환
```

- [doSend](../../01_JmsTemplate.execute/01_JmsTemplate.doSend/README.md)
- [MessagingMessageListenerAdapter.onMessage](../../02_AbstractMessageListenerContainer.executeListener/01_MessagingMessageListenerAdapter.onMessage/README.md)

## 구현 계층

```text
 MessageConverter
   +-- SimpleMessageConverter        String/byte[]/Map/Serializable (기본)
   +-- MappingJackson2MessageConverter   JSON TextMessage
   +-- MarshallingMessageConverter   XML (OXM)
   +-- MessagingMessageConverter     spring-messaging Message 와 상호 변환

 주의
   기본 변환기는 자바 직렬화를 쓴다 (버전 호환과 보안 측면에서 JSON 을 권장)
```
