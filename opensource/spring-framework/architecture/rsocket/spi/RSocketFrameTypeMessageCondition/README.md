# RSocketFrameTypeMessageCondition

상위: [Spring RSocket](../../README.md) / [spi](../README.md)

같은 라우트를 프레임 타입으로 가르는 매핑 조건이다. HTTP의 메서드 조건에 해당한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket.annotation.support` / `RSocketFrameTypeMessageCondition.java` L43-L72 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/annotation/support/RSocketFrameTypeMessageCondition.java#L43-L72))

```java
// RSocketFrameTypeMessageCondition.java L43-L72
public class RSocketFrameTypeMessageCondition extends AbstractMessageCondition<RSocketFrameTypeMessageCondition> {

    public static final String FRAME_TYPE_HEADER = "rsocketFrameType";

    public static final RSocketFrameTypeMessageCondition CONNECT_CONDITION =
            new RSocketFrameTypeMessageCondition(FrameType.SETUP, FrameType.METADATA_PUSH);

    public static final RSocketFrameTypeMessageCondition REQUEST_FNF_OR_RESPONSE_CONDITION =
            new RSocketFrameTypeMessageCondition(FrameType.REQUEST_FNF, FrameType.REQUEST_RESPONSE);

    public static final RSocketFrameTypeMessageCondition REQUEST_RESPONSE_CONDITION =
            new RSocketFrameTypeMessageCondition(FrameType.REQUEST_RESPONSE);

    public static final RSocketFrameTypeMessageCondition REQUEST_STREAM_CONDITION =
            new RSocketFrameTypeMessageCondition(FrameType.REQUEST_STREAM);

    public static final RSocketFrameTypeMessageCondition REQUEST_CHANNEL_CONDITION =
            new RSocketFrameTypeMessageCondition(FrameType.REQUEST_CHANNEL);

    public static final RSocketFrameTypeMessageCondition EMPTY_CONDITION = new RSocketFrameTypeMessageCondition();

```

## 흐름에서 불리는 자리

```text
 매핑 등록 시
   @MessageMapping 메서드의 카디널리티로 조건을 정한다 (getCondition L193)
     인자 0~1 + 반환 0(void, Mono<Void>) --> REQUEST_FNF_OR_RESPONSE
     인자 0~1 + 반환 1(단건)             --> REQUEST_RESPONSE
     인자 0~1 + 반환 2(Flux)             --> REQUEST_STREAM
     인자 2(Flux)                        --> REQUEST_CHANNEL (반환과 무관)
   @ConnectMapping 이면 CONNECT_CONDITION
 매칭 시
   메시지 헤더의 프레임 타입과 비교한다
```

- [AbstractMethodMessageHandler.handleMessage](../../03_AbstractMethodMessageHandler.handleMessage/README.md)

## 구현 계층

```text
 AbstractMessageCondition<T>
   +-- RSocketFrameTypeMessageCondition

 미리 만들어 둔 조건들
   CONNECT_CONDITION                  SETUP, METADATA_PUSH
   REQUEST_FNF_OR_RESPONSE_CONDITION  REQUEST_FNF, REQUEST_RESPONSE
   REQUEST_RESPONSE_CONDITION
   REQUEST_STREAM_CONDITION
   REQUEST_CHANNEL_CONDITION
   EMPTY_CONDITION                    조건 없음

 CompositeMessageCondition 안에서
   라우트 조건과 함께 묶여 하나의 매핑이 된다
```

## 결과가 쓰이는 곳

```text
 같은 라우트, 다른 상호작용
      --> 서로 다른 메서드로 갈 수 있다
      --> @MessageMapping 만 보고는 어느 쪽인지 알 수 없고 시그니처를 봐야 한다

 시그니처로 조건을 추론한다는 점
      --> Mono<T> 를 돌려주면 요청-응답, Flux 를 돌려주면 스트림으로 잡힌다
      --> void 나 Mono<Void> 는 fireAndForget 과 요청-응답 둘 다에 매칭된다
      --> 인자가 Flux 면 반환이 무엇이든 채널로 잡힌다

 매칭 실패
      --> 라우트는 맞는데 프레임 타입이 안 맞는 경우가 흔한 함정이다
      --> 조용히 끝나지 않도록 RSocket 쪽은 라우트를 담은 예외를 만든다
```
