# ReconnectStrategy

상위: [Spring STOMP 브로커 릴레이](../../README.md) / [spi](../README.md)

끊긴 뒤 다음 재시도까지 얼마나 기다릴지 정한다. 메서드 하나뿐이다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.tcp` / `ReconnectStrategy.java` L28-L37 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/tcp/ReconnectStrategy.java#L28-L37))

```java
// ReconnectStrategy.java L28-L37
public interface ReconnectStrategy {

    @Nullable Long getTimeToNextAttempt(int attemptCount);

}
```

## 흐름에서 불리는 자리

```text
 startInternal  L469
   tcpClient.connectAsync(handler, new FixedIntervalReconnectStrategy(5000))
     시스템 세션만 재연결 전략을 받는다
```

- [startInternal](../../01_StompBrokerRelayMessageHandler.startInternal/README.md)

## 구현 계층

```text
 ReconnectStrategy
   +-- FixedIntervalReconnectStrategy   고정 간격 (릴레이가 쓰는 것)
   +-- (사용자 구현)                     지수 백오프 등을 직접 만들 수 있다
```

## 결과가 쓰이는 곳

```text
 getTimeToNextAttempt(attemptCount)
      --> null 을 돌려주면 더 시도하지 않는다
      --> 고정 간격 구현은 항상 같은 값을 돌려줘 무한 재시도가 된다

 시스템 세션에만 적용된다는 점
      --> 브로커가 잠깐 죽어도 서버는 계속 붙으려 한다
      --> 그동안 서버 발신은 예외로 거절된다

 클라이언트 세션
      --> 전략이 없어 한 번 실패하면 끝이다
      --> 클라이언트가 WebSocket 부터 다시 연결해야 한다
```
