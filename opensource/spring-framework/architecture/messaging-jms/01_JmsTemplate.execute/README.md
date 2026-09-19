# JmsTemplate.execute

상위: [Spring 메시징 (JMS)](../README.md)

JMS의 상투적인 절차(커넥션과 세션 확보, 콜백 실행, 정리, 예외 변환)를 모은 템플릿 메서드다. JDBC의 `JdbcTemplate.execute`와 같은 구조다.

## 실제 코드

`spring-jms` / `org.springframework.jms.core` / `JmsTemplate.java` L519-L550 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jms/src/main/java/org/springframework/jms/core/JmsTemplate.java#L519-L550))

```java
// JmsTemplate.java L519-L550
@SuppressWarnings("resource")
public <T> @Nullable T execute(SessionCallback<T> action, boolean startConnection) throws JmsException {
    Assert.notNull(action, "Callback object must not be null");
    Connection conToClose = null;
    Session sessionToClose = null;
    try {
        Session sessionToUse = ConnectionFactoryUtils.doGetTransactionalSession(
                obtainConnectionFactory(), this.transactionalResourceFactory, startConnection);
        if (sessionToUse == null) {
            conToClose = createConnection();
            sessionToClose = createSession(conToClose);
            if (startConnection) {
                conToClose.start();
            }
            sessionToUse = sessionToClose;
        }
        if (logger.isDebugEnabled()) {
            logger.debug("Executing callback on JMS Session: " + sessionToUse);
        }
        if (MICROMETER_JAKARTA_PRESENT && this.observationRegistry != null) {
            sessionToUse = MicrometerInstrumentation.instrumentSession(sessionToUse, this.observationRegistry);
        }
        return action.doInJms(sessionToUse);
    }
    catch (JMSException ex) {
        throw convertJmsAccessException(ex);
    }
    finally {
        JmsUtils.closeSession(sessionToClose);
        ConnectionFactoryUtils.releaseConnection(conToClose, getConnectionFactory(), startConnection);
    }
}
```

## 동작 흐름

```text
 execute(action, startConnection)
 |
 | L525 ConnectionFactoryUtils.doGetTransactionalSession(...)
 |        트랜잭션에 묶인 세션이 있으면 그것을 재사용
 |        (JDBC 의 DataSourceUtils.getConnection 과 같은 역할)
 |
 +-- L527 없으면 직접 만든다
 |      createConnection() --> createSession(con)
 |      startConnection 이면 con.start()  (수신에 필요)
 |
 | L538 관측이 켜져 있으면 세션을 계측 프록시로 감싼다
 |
 | L541 action.doInJms(sessionToUse)      <-- 사용자 작업 (송신, 수신, 브라우징)
 |
 +-- L543 JMSException --> convertJmsAccessException 으로 JmsException 계층으로 변환
 |
 +-- finally
        직접 만든 세션만 닫고, 트랜잭션 세션은 닫지 않는다
        커넥션도 같은 규칙으로 반납
```

1. 송신 콜백이 하는 일은 [doSend](01_JmsTemplate.doSend/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 콜백 반환값
      --> send 계열은 없음, receive 계열은 받은 메시지
      --> browse 는 브라우징 결과

 세션 재사용 규칙
      --> @Transactional + JmsTransactionManager 조합이면 같은 세션을 쓴다
      --> 그래서 한 트랜잭션 안의 여러 send 가 함께 커밋된다

 JmsException
      --> JMSException(체크 예외)을 런타임 예외 계층으로 바꾼다
      --> JDBC 의 DataAccessException 과 같은 목적
```

## 하위 메서드

- [01 JmsTemplate.doSend](01_JmsTemplate.doSend/README.md)
