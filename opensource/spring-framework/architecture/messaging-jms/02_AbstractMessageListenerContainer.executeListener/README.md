# AbstractMessageListenerContainer.executeListener

상위: [Spring 메시징 (JMS)](../README.md)

받은 메시지 하나를 리스너에게 넘기고, 결과에 따라 커밋하거나 롤백한다. 수신 루프는 하위 구현(`DefaultMessageListenerContainer`)이 돌리고, 메시지 하나의 처리 규칙은 여기에 있다.

## 실제 코드

`spring-jms` / `org.springframework.jms.listener` / `AbstractMessageListenerContainer.java` L685-L693 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/listener/AbstractMessageListenerContainer.java#L685-L693))

```java
// AbstractMessageListenerContainer.java L685-L693
 */
protected void executeListener(Session session, Message message) {
    try {
        doExecuteListener(session, message);
    }
    catch (Throwable ex) {
        handleListenerException(ex);
    }
}
```

`spring-jms` / `org.springframework.jms.listener` / `AbstractMessageListenerContainer.java` L721-L740 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/listener/AbstractMessageListenerContainer.java#L721-L740))

```java
// AbstractMessageListenerContainer.java L721-L740
 */
protected void doExecuteListener(Session session, Message message) throws JMSException {
    if (!isAcceptMessagesWhileStopping() && !isRunning()) {
        if (logger.isWarnEnabled()) {
            logger.warn("Rejecting received message because of the listener container " +
                    "having been stopped in the meantime: " + message);
        }
        rollbackIfNecessary(session);
        throw new MessageRejectedWhileStoppingException();
    }

    try {
        invokeListener(session, message);
    }
    catch (JMSException | RuntimeException | Error ex) {
        rollbackOnExceptionIfNecessary(session, ex);
        throw ex;
    }
    commitIfNecessary(session, message);
}
```

## 동작 흐름

```text
 executeListener(session, message)
 |
 +-- doExecuteListener(session, message)
 |     |
 |     | L723 컨테이너가 정지 중이고 정지 중 수신을 허용하지 않으면
 |     |        롤백 후 MessageRejectedWhileStoppingException
 |     |        --> 브로커가 다시 전달하게 둔다
 |     |
 |     | L733 invokeListener(session, message)
 |     |        MessageListener              --> onMessage(message)
 |     |        SessionAwareMessageListener  --> onMessage(message, session)
 |     |          (세션을 받아 응답을 보내거나 커밋을 제어할 수 있다)
 |     |
 |     | L735 예외 --> rollbackOnExceptionIfNecessary 후 다시 던짐
 |     |
 |     +-- L739 정상 --> commitIfNecessary(session, message)
 |            트랜잭션 세션이면 commit
 |            아니면 ack 모드에 따라 message.acknowledge()
 |
 +-- 예외를 잡아 handleListenerException 으로 (ErrorHandler 또는 로그)
```

1. `@JmsListener` 메서드는 [MessagingMessageListenerAdapter.onMessage](01_MessagingMessageListenerAdapter.onMessage/README.md)를 통해 호출된다.

## 결과가 쓰이는 곳

```text
 커밋 / ack
      --> 메시지가 큐에서 제거된다
      --> 처리 후에 커밋하므로, 처리 중 장애가 나면 재전달된다 (at-least-once)

 롤백
      --> 브로커가 재전달한다
      --> 같은 메시지가 반복 실패하면 브로커의 재전달 한도에 따라
          DLQ 로 이동하거나 무한 재시도가 된다 (컨테이너가 아니라 브로커 설정)

 handleListenerException
      --> 리스너 밖으로 나온 예외의 최종 처리
      --> ErrorHandler 를 등록하지 않으면 로그만 남는다
```

## 하위 메서드

- [01 MessagingMessageListenerAdapter.onMessage](01_MessagingMessageListenerAdapter.onMessage/README.md)
