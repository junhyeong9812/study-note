# spi

상위: [Spring 메시징 (JMS)](../README.md)

송신 템플릿과 수신 컨테이너가 기대는 인터페이스, 그리고 그 위에 있는 공통 메시지 추상화다.

```text
 송신 .............. JmsOperations (+ MessageCreator)
   객체 <-> 메시지 .. MessageConverter
 수신 .............. MessageListenerContainer
   리스너 .......... MessageListener / SessionAwareMessageListener
   @JmsListener .... MessagingMessageListenerAdapter --> Message (spring-messaging)
```

## 하위 인터페이스

- [JmsOperations](JmsOperations/README.md)
- [MessageListenerContainer](MessageListenerContainer/README.md)
- [MessageConverter](MessageConverter/README.md)
- [Message](Message/README.md)
