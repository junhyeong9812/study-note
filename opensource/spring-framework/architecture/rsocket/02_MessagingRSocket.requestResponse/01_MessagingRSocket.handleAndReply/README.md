# MessagingRSocket.handleAndReply

상위: [MessagingRSocket.requestResponse](../README.md)

프레임을 메시지로 바꾸고, 응답이 돌아올 자리를 미리 마련해 두는 곳이다. 응답을 반환값으로 받지 않고 헤더에 심은 참조로 받는 구조가 여기서 정해진다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket.annotation.support` / `MessagingRSocket.java` L164-L182 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/annotation/support/MessagingRSocket.java#L164-L182))

```java
// MessagingRSocket.java L164-L182
@SuppressWarnings("deprecation")
private Flux<Payload> handleAndReply(Payload firstPayload, FrameType frameType, Flux<Payload> payloads) {
    AtomicReference<Flux<Payload>> responseRef = new AtomicReference<>();
    MessageHeaders headers = createHeaders(firstPayload, frameType, responseRef);

    AtomicBoolean read = new AtomicBoolean();
    Flux<DataBuffer> buffers = payloads.map(this::retainDataAndReleasePayload).doOnSubscribe(s -> read.set(true));
    Message<Flux<DataBuffer>> message = MessageBuilder.createMessage(buffers, headers);

    return Mono.defer(() -> this.messageHandler.handleMessage(message))
            .doFinally(s -> {
                // Subscription should have happened by now due to ChannelSendOperator
                if (!read.get()) {
                    firstPayload.release();
                }
            })
            .thenMany(Flux.defer(() -> responseRef.get() != null ?
                    responseRef.get() : Mono.error(new IllegalStateException("Expected response"))));
}
```

응답을 만들지 않는 경로는 더 단순하다.

`spring-messaging` / `org.springframework.messaging.rsocket.annotation.support` / `MessagingRSocket.java` L146-L155 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/annotation/support/MessagingRSocket.java#L146-L155))

```java
// MessagingRSocket.java L146-L155
private Mono<Void> handle(Payload payload, FrameType frameType) {
    MessageHeaders headers = createHeaders(payload, frameType, null);
    DataBuffer dataBuffer = retainDataAndReleasePayload(payload);
    int refCount = refCount(dataBuffer);
    Message<?> message = MessageBuilder.createMessage(dataBuffer, headers);
    return Mono.defer(() -> this.messageHandler.handleMessage(message))
            .doFinally(s -> {
                if (refCount(dataBuffer) == refCount) {
                    DataBufferUtils.release(dataBuffer);
                }
```

## 동작 흐름

```text
 handleAndReply(firstPayload, frameType, payloads)
 |
 | L166 응답을 담을 AtomicReference<Flux<Payload>> 를 만든다
 | L167 createHeaders(firstPayload, frameType, responseRef)
 |        메타데이터에서 라우트를 뽑아 헤더에 싣는다
 |        프레임 타입도 싣는다 (매핑 조건이 된다)
 |        responseRef 를 RESPONSE_HEADER 로 심는다
 |
 | L170 payloads 를 DataBuffer Flux 로 바꾸고 doOnSubscribe 로 "읽혔다"를 표시한다
 | L171 그 Flux 를 페이로드로 하는 Message 를 만든다
 |
 | L173 messageHandler.handleMessage(message)
 |        여기서 라우팅과 핸들러 호출이 일어난다
 |
 +-- L174 doFinally
 |        아무도 구독하지 않았으면 firstPayload 를 직접 해제한다
 |        = 매칭 실패 등으로 본문이 읽히지 않은 경우의 누수 방지
 |
 +-- L180 thenMany
        responseRef 가 채워져 있으면 그 Flux 를 응답으로 흘린다
        비어 있으면 IllegalStateException("Expected response")

 handle(payload, frameType)        응답이 없는 경로
        L147 헤더를 만들고 (responseRef 없이)
        L150 Message 를 만들어 L151 handleMessage
        L152 doFinally 에서 참조 카운트가 그대로면 버퍼를 해제한다
```

```text
 왜 반환값이 아니라 헤더의 참조인가

 반환값 처리기는 Mono<Void> 만 돌려준다 (메시징 계약)
 그래서 "응답 Flux" 를 돌려줄 자리가 없다
 대신 호출 전에 빈 상자를 헤더에 넣어 두고,
 처리기가 그 상자에 결과를 넣는다
 handleAndReply 가 처리 완료 후 상자를 열어 응답으로 쓴다
```

## 결과가 쓰이는 곳

```text
 responseRef 에 담긴 Flux<Payload>
      --> requestResponse 면 first 하나만, requestStream 이면 전부 나간다
      --> 채우는 쪽은 RSocketPayloadReturnValueHandler 다

 "Expected response" 예외
      --> 처리가 끝났는데 참조가 비어 있다는 뜻이다
      --> 기본 구성에서는 반환값 처리기가 빈 Flux 라도 넣으므로 닿지 않는다
          커스텀 처리기로 참조를 채우지 않았을 때를 막는 방어다

 참조 카운트 관리
      --> Netty 버퍼는 수동 해제가 필요하다
      --> 읽히지 않은 경우에만 해제해 이중 해제를 피한다

 라우트가 비어 있으면
      --> createHeaders 가 빈 문자열을 기본값으로 넣는다
      --> 빈 라우트에 매핑된 메서드가 있으면 그쪽이 호출된다
```

라우팅은 [AbstractMethodMessageHandler.handleMessage](../../03_AbstractMethodMessageHandler.handleMessage/README.md)가 이어받는다.
