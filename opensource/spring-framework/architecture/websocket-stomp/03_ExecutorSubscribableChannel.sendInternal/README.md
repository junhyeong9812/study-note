# ExecutorSubscribableChannel.sendInternal

상위: [Spring WebSocket과 STOMP](../README.md)

메시지 하나를 구독자 전부에게 배달한다. 실행기를 주면 비동기로, 주지 않으면 호출 스레드에서 돈다. 이 한 가지 선택이 STOMP 처리의 스레드 모델을 정한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.support` / `ExecutorSubscribableChannel.java` L96-L114 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/support/ExecutorSubscribableChannel.java#L96-L114))

```java
// ExecutorSubscribableChannel.java L96-L114
public boolean sendInternal(Message<?> message, long timeout) {
    for (MessageHandler handler : getSubscribers()) {
        SendTask sendTask = new SendTask(message, handler);
        if (this.executor != null) {
            try {
                this.executor.execute(sendTask);
            }
            catch (RejectedExecutionException ex) {
                // Probably on shutdown -> run send task locally instead
                sendTask.run();
            }
        }
        else {
            // No executor configured -> always run send tasks locally
            sendTask.run();
        }
    }
    return true;
}
```

## 동작 흐름

```text
 sendInternal(message, timeout)
 |
 +-- L97 구독자마다 반복
 |     L98 SendTask 를 만든다 (메시지 + 핸들러)
 |     |
 |     +-- L99 실행기가 있으면
 |     |     L101 executor.execute(sendTask)
 |     |     L103 RejectedExecutionException 이면 (대개 종료 중)
 |     |            L105 호출 스레드에서 직접 실행한다
 |     |
 |     +-- L109 실행기가 없으면 L111 호출 스레드에서 실행
 |
 +-- L114 항상 true 를 돌려준다
        = "배달을 시작했다"는 뜻이지 "처리에 성공했다"가 아니다
```

```text
 SendTask 가 하는 일

 ExecutorChannelInterceptor 의 beforeHandle 을 순서대로 부르고
 handler.handleMessage(message) 를 부른 뒤
 afterMessageHandled 를 역순으로 부른다
 (interceptorIndex 로 어디까지 성공했는지 기억한다 — 인터셉터 체인과 같은 방식)
```

## 결과가 쓰이는 곳

```text
 반환값 true
      --> send() 가 성공했다고 보고된다
      --> 실제 처리 결과는 알 수 없다. 비동기면 아직 시작도 안 했을 수 있다
      --> 그래서 STOMP 오류는 응답 프레임으로 돌려보내지 예외로 올리지 않는다

 구독자 목록
      --> clientInboundChannel 에는 @MessageMapping 라우터와 브로커가 함께 붙는다
      --> 같은 메시지가 둘 다에게 간다. 목적지 접두로 각자 걸러 낸다

 실행기 유무
      --> 있으면 프레임 수신 스레드가 곧바로 풀려난다 (처리량)
      --> 없으면 수신 순서대로 처리된다 (순서 보장)
      --> 기본 구성은 실행기를 두므로, 순서가 필요하면 별도 설정이 필요하다

 RejectedExecutionException 폴백
      --> 종료 중에도 메시지를 잃지 않으려는 장치다
```

채널 계약 자체는 [MessageChannel](../spi/MessageChannel/README.md)에, 구독자 쪽 계약은 [MessageHandler](../spi/MessageHandler/README.md)에 있다.
