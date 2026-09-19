# JmsOperations

상위: [Spring 메시징 (JMS)](../../README.md) / [spi](../README.md)

`JmsTemplate`이 구현하는 연산 목록이다. 송신, 수신, 요청-응답, 브라우징이 모두 선언돼 있다.

## 실제 코드

`spring-jms` / `org.springframework.jms.core` / `JmsOperations.java` L49-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/core/JmsOperations.java#L49-L120))

```java
// JmsOperations.java L49-L120
public interface JmsOperations {

    <T> @Nullable T execute(SessionCallback<T> action) throws JmsException;

    <T> @Nullable T execute(ProducerCallback<T> action) throws JmsException;

    <T> @Nullable T execute(Destination destination, ProducerCallback<T> action) throws JmsException;

    <T> @Nullable T execute(String destinationName, ProducerCallback<T> action) throws JmsException;

    //---------------------------------------------------------------------------------------
    // Convenience methods for sending messages
    //---------------------------------------------------------------------------------------

    void send(MessageCreator messageCreator) throws JmsException;

    void send(Destination destination, MessageCreator messageCreator) throws JmsException;

    void send(String destinationName, MessageCreator messageCreator) throws JmsException;
```

`spring-jms` / `org.springframework.jms.core` / `MessageCreator.java` L39-L50 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/core/MessageCreator.java#L39-L50))

```java
// MessageCreator.java L39-L50
public interface MessageCreator {

    Message createMessage(Session session) throws JMSException;

}
```

## 흐름에서 불리는 자리

```text
 send / convertAndSend        --> execute(SessionCallback) --> doSend
 receive / receiveAndConvert   --> execute(SessionCallback, startConnection=true)
 sendAndReceive                --> 임시 큐로 요청-응답
```

- [JmsTemplate.execute](../../01_JmsTemplate.execute/README.md)
- [doSend](../../01_JmsTemplate.execute/01_JmsTemplate.doSend/README.md)

## 구현 계층

```text
 JmsOperations
   +-- JmsTemplate           기본 구현
 그 위의 API
   +-- JmsClient             fluent API (Spring 6.2+)
   +-- JmsMessagingTemplate  spring-messaging 의 Message 로 다룬다

 MessageCreator
   세션을 받아 Message 를 만드는 콜백
   convertAndSend 는 내부적으로 변환기를 호출하는 MessageCreator 를 쓴다
```
