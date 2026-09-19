# MessageListenerContainer

상위: [Spring 메시징 (JMS)](../../README.md) / [spi](../README.md)

메시지를 계속 받아 리스너에게 넘기는 컴포넌트다. `SmartLifecycle`이므로 컨테이너 기동과 종료에 맞춰 시작하고 멈춘다.

## 실제 코드

`spring-jms` / `org.springframework.jms.listener` / `MessageListenerContainer.java` L34-L75 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/listener/MessageListenerContainer.java#L34-L75))

```java
// MessageListenerContainer.java L34-L75
public interface MessageListenerContainer extends SmartLifecycle {

    void setupMessageListener(Object messageListener);

    @Nullable MessageConverter getMessageConverter();

    @Nullable DestinationResolver getDestinationResolver();

    boolean isPubSubDomain();

    boolean isReplyPubSubDomain();

    @Nullable QosSettings getReplyQosSettings();

}
```

`spring-jms` / `org.springframework.jms.listener` / `SessionAwareMessageListener.java` L46-L58 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/listener/SessionAwareMessageListener.java#L46-L58))

```java
// SessionAwareMessageListener.java L46-L58
public interface SessionAwareMessageListener<M extends Message> {

    void onMessage(M message, Session session) throws JMSException;

}
```

## 흐름에서 불리는 자리

```text
 [컨테이너 기동] finishRefresh --> SmartLifecycle.start()
   수신 루프 시작
 메시지 도착
   executeListener --> invokeListener --> 리스너 호출
 [종료] stop() --> 수신 중단
```

- [executeListener](../../02_AbstractMessageListenerContainer.executeListener/README.md)
- [컨테이너 기동의 finishRefresh](../../../container-refresh/01_AbstractApplicationContext.refresh/10_AbstractApplicationContext.finishRefresh/README.md)

## 구현 계층

```text
 MessageListenerContainer
   +-- AbstractMessageListenerContainer          메시지 하나의 처리 규칙
         +-- AbstractPollingMessageListenerContainer
         |     +-- DefaultMessageListenerContainer   폴링 기반 (가장 흔함)
         +-- SimpleMessageListenerContainer          JMS 표준 비동기 콜백

 리스너 종류
   MessageListener                 JMS 표준
   SessionAwareMessageListener     세션까지 받는다 (응답 전송에 유용)
   MessagingMessageListenerAdapter @JmsListener 메서드 래퍼
```
