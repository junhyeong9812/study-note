# MessageChannel

상위: [Spring WebSocket과 STOMP](../../README.md) / [spi](../README.md)

메시지를 보내는 통로다. 메서드는 사실상 `send` 하나이고, 구독자 관리는 하위 인터페이스가 맡는다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging` / `MessageChannel.java` L26-L58 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/MessageChannel.java#L26-L58))

```java
// MessageChannel.java L26-L58
public interface MessageChannel {

    long INDEFINITE_TIMEOUT = -1;

    default boolean send(Message<?> message) {
        return send(message, INDEFINITE_TIMEOUT);
    }

    boolean send(Message<?> message, long timeout);

}
```

## 흐름에서 불리는 자리

```text
 StompSubProtocolHandler.handleMessageFromClient  L338
   channelToUse.send(message)     clientInboundChannel 로
 브로커와 애플리케이션 코드
   clientOutboundChannel.send / brokerChannel.send
```

- [ExecutorSubscribableChannel.sendInternal](../../03_ExecutorSubscribableChannel.sendInternal/README.md)

## 구현 계층

```text
 MessageChannel
   +-- SubscribableChannel                 구독자 등록/해제
   +-- PollableChannel                     받는 쪽이 당겨 가는 채널
   +-- AbstractMessageChannel              인터셉터 체인 (InterceptableChannel 도 구현)
   |     +-- AbstractSubscribableChannel   (SubscribableChannel 구현)
   |           +-- ExecutorSubscribableChannel   STOMP 설정이 쓰는 구현
   +-- OrderedMessageChannelDecorator      세션별 순서 보존 장식
```

```text
 STOMP 설정이 만드는 채널 셋

 clientInboundChannel    수신 프레임 --> 라우터/브로커
 clientOutboundChannel   브로커/라우터 --> 송신 프레임
 brokerChannel           애플리케이션 --> 브로커
 각각 실행기와 인터셉터를 따로 설정할 수 있다
```

## 결과가 쓰이는 곳

```text
 send 의 반환값
      --> "배달을 시작했다"는 뜻이다. 처리 성공이 아니다
      --> 비동기 실행기를 쓰면 반환 시점에 아직 처리 전이다

 인터셉터
      --> ChannelInterceptor 로 메시지를 들여다보거나 바꿀 수 있다
      --> 인증 주입, 로깅, 메트릭이 여기 걸린다

 채널을 경계로 삼는 설계
      --> WebSocket 계층과 메시징 계층이 서로를 직접 알지 못한다
      --> 테스트에서 채널만 갈아 끼우면 WebSocket 없이 라우팅을 검증할 수 있다
```
