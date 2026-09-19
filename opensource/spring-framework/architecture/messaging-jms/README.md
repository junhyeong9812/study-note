# Spring 메시징 (JMS)

`jmsTemplate.convertAndSend(...)`로 메시지를 보내고, `@JmsListener` 메서드가 그것을 받기까지의 흐름을 위에서 아래로 따라간다. 송신은 JDBC와 같은 템플릿 구조이고, 수신은 컨테이너가 계속 돌며 메시지를 꺼내 리스너에게 넘기는 구조다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 메시징의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] 송신

 jmsTemplate.convertAndSend("queue", order)
 |
 +-- [01] JmsTemplate.execute(SessionCallback)
        트랜잭션 세션이 있으면 재사용, 없으면 Connection/Session 생성
        |
        +-- [01-01] doSend
               MessageProducer 생성
               MessageCreator 가 Message 생성 (MessageConverter 로 객체 -> 메시지)
               producer.send(message)
               로컬 트랜잭션 세션이면 commit
        |
        +-- finally  Session 닫기, Connection 반납

 [B] 수신

 컨테이너(SmartLifecycle) 가 기동 시 start --> 수신 루프
 |
 +-- [02] AbstractMessageListenerContainer.executeListener
        |
        +-- doExecuteListener
               정지 중이면 롤백 후 거부
               invokeListener --> 리스너 종류에 따라 분기
               예외면 롤백, 정상이면 커밋/ack
        |
        +-- [02-01] MessagingMessageListenerAdapter.onMessage
               JMS 메시지를 spring-messaging 의 Message 로 변환
               @JmsListener 메서드 호출 (인자 해석은 MVC 와 같은 계열)
               반환값이 있으면 응답 대상으로 전송 (@SendTo 또는 JMSReplyTo)
```

## 컨테이너의 위치

```text
 [컨테이너 기동] finishRefresh --> DefaultLifecycleProcessor.onRefresh
   --> SmartLifecycle 인 리스너 컨테이너가 start()
   --> 수신 스레드가 돌기 시작한다
 [종료] close --> phase 역순으로 stop() --> 수신 중단
```

자세한 것은 [컨테이너 기동](../container-refresh/01_AbstractApplicationContext.refresh/10_AbstractApplicationContext.finishRefresh/README.md)에 있다.

## 단계

1. [JmsTemplate.execute](01_JmsTemplate.execute/README.md)가 세션을 확보하고 콜백을 실행한다.
2. [AbstractMessageListenerContainer.executeListener](02_AbstractMessageListenerContainer.executeListener/README.md)가 받은 메시지를 리스너에게 넘기고 커밋/롤백을 결정한다.

## 결과가 쓰이는 곳

```text
 송신한 메시지
      --> 브로커의 큐/토픽
      --> 세션이 트랜잭션이면 커밋 시점에 실제로 나간다

 수신 처리 결과
      --> 정상: 커밋 또는 ack --> 메시지가 큐에서 제거된다
      --> 예외: 롤백 --> 브로커가 재전달한다 (재시도 한도는 브로커 설정)

 트랜잭션과의 관계
      --> sessionTransacted 이면 JMS 로컬 트랜잭션
      --> 외부 트랜잭션 매니저를 지정하면 그 경계 안에서 동작한다
      --> DB 트랜잭션과 JMS 는 별개다 (XA 없이는 원자성이 없다)
```

## 다루지 않는 것

STOMP/WebSocket 메시징(`spring-messaging`의 `SimpMessagingTemplate`, 브로커 릴레이)과 RSocket은 같은 `Message` 추상화를 쓰지만 경로가 달라 이 지도에서는 인터페이스만 언급한다. Kafka는 Spring Framework가 아니라 Spring Kafka의 영역이다.

## 하위 메서드

- [01 JmsTemplate.execute](01_JmsTemplate.execute/README.md)
- [02 AbstractMessageListenerContainer.executeListener](02_AbstractMessageListenerContainer.executeListener/README.md)
- [spi](spi/README.md) — 템플릿 연산, 리스너, 변환기, 메시지 추상화
