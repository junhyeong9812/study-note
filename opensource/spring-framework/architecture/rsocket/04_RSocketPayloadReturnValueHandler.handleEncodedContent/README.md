# RSocketPayloadReturnValueHandler.handleEncodedContent

상위: [Spring RSocket](../README.md)

핸들러 메서드가 돌려준 값이 인코딩된 뒤, 응답으로 나갈 자리에 놓이는 마지막 지점이다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket.annotation.support` / `RSocketPayloadReturnValueHandler.java` L59-L67 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/annotation/support/RSocketPayloadReturnValueHandler.java#L59-L67))

```java
// RSocketPayloadReturnValueHandler.java L59-L67
@Override
protected Mono<Void> handleEncodedContent(
        Flux<DataBuffer> encodedContent, MethodParameter returnType, Message<?> message) {

    AtomicReference<Flux<Payload>> responseRef = getResponseReference(message);
    Assert.notNull(responseRef, "Missing '" + RESPONSE_HEADER + "'");
    responseRef.set(encodedContent.map(PayloadUtils::createPayload));
    return Mono.empty();
}
```

`spring-messaging` / `org.springframework.messaging.rsocket.annotation.support` / `RSocketPayloadReturnValueHandler.java` L70-L76 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/annotation/support/RSocketPayloadReturnValueHandler.java#L70-L76))

```java
// RSocketPayloadReturnValueHandler.java L70-L76
protected Mono<Void> handleNoContent(MethodParameter returnType, Message<?> message) {
    AtomicReference<Flux<Payload>> responseRef = getResponseReference(message);
    if (responseRef != null) {
        responseRef.set(Flux.empty());
    }
    return Mono.empty();
}
```

## 동작 흐름

```text
 handleEncodedContent(encodedContent, returnType, message)
 |
 | L63 헤더에서 RESPONSE_HEADER 로 심어 둔 AtomicReference 를 꺼낸다
 | L64 없으면 Assert.notNull 이 IllegalArgumentException("Missing 'rsocketResponse'")
 |        헤더 값이 AtomicReference 가 아니면 L81 에서 IllegalStateException
 |
 | L65 인코딩된 DataBuffer Flux 를 Payload Flux 로 바꿔 참조에 넣는다
 |
 +-- L66 Mono.empty() 를 돌려준다
        "내 할 일은 끝났다"는 신호일 뿐, 응답은 참조를 통해 전달된다

 handleNoContent(returnType, message)     반환값이 없을 때
 |
 +-- L72 참조가 있으면 빈 Flux 를 넣는다
        요청-응답인데 본문이 없으면 "응답은 왔고 비어 있다"가 된다
        참조가 없으면(fireAndForget) 아무것도 하지 않는다
```

```text
 RESPONSE_HEADER 라는 이름의 통로

 상수 이름은 "rsocketResponse" (L51)
 심는 쪽   MessagingRSocket.createHeaders
 읽는 쪽   이 처리기
 비우는 쪽 handleAndReply 의 thenMany

 메시징 계약(Mono<Void> 반환)을 깨지 않고
 응답 스트림을 돌려주기 위한 우회로다
```

## 결과가 쓰이는 곳

```text
 참조에 담긴 Flux<Payload>
      --> handleAndReply 가 꺼내 그대로 응답으로 흘린다
      --> requestStream 이면 원소마다 프레임 하나가 나간다

 참조가 없을 때의 IllegalArgumentException
      --> 응답 자리가 없는 프레임 타입인데 반환값 인코딩 경로로 들어온 경우의 방어다
      --> 정상 매칭 경로에서는 handleAndReply 가 참조를 심어 두므로 닿지 않는다

 handleNoContent 의 빈 Flux
      --> void 를 돌려준 requestResponse 핸들러의 응답이 된다
      --> 클라이언트는 "완료" 신호만 받는다

 인코딩 자체
      --> 상위 클래스가 RSocketStrategies 의 인코더로 이미 마쳤다
      --> 이 메서드는 DataBuffer 를 Payload 로 감싸기만 한다
```
