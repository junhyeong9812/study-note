# MessagingRSocket.requestResponse

상위: [Spring RSocket](../README.md)

RSocket 구현이 부르는 콜백 넷이 한자리에 있다. 하는 일은 프레임 타입을 이름표로 붙여 공통 처리로 넘기는 것뿐이다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket.annotation.support` / `MessagingRSocket.java` L114-L137 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/annotation/support/MessagingRSocket.java#L114-L137))

```java
// MessagingRSocket.java L114-L137
@Override
public Mono<Void> fireAndForget(Payload payload) {
    return handle(payload, FrameType.REQUEST_FNF);
}

@Override
public Mono<Payload> requestResponse(Payload payload) {
    return handleAndReply(payload, FrameType.REQUEST_RESPONSE, Flux.just(payload)).next();
}

@Override
public Flux<Payload> requestStream(Payload payload) {
    return handleAndReply(payload, FrameType.REQUEST_STREAM, Flux.just(payload));
}

@Override
public Flux<Payload> requestChannel(Publisher<Payload> payloads) {
    return Flux.from(payloads)
            .switchOnFirst((signal, innerFlux) -> {
                Payload firstPayload = signal.get();
                return firstPayload == null ? innerFlux :
                        handleAndReply(firstPayload, FrameType.REQUEST_CHANNEL, innerFlux);
            });
}
```

## 동작 흐름

```text
 RSocket 인터페이스 구현 네 개
 |
 +-- L115 fireAndForget(payload)
 |        handle(payload, REQUEST_FNF)        응답이 없으므로 handle
 |
 +-- L120 requestResponse(payload)
 |        handleAndReply(payload, REQUEST_RESPONSE, Flux.just(payload)).next()
 |        응답 Flux 의 첫 원소만 취한다
 |
 +-- L125 requestStream(payload)
 |        handleAndReply(payload, REQUEST_STREAM, Flux.just(payload))
 |
 +-- L130 requestChannel(payloads)
 |        L132 switchOnFirst 로 첫 payload 를 꺼낸 뒤
 |        L135 handleAndReply(첫 payload, REQUEST_CHANNEL, 첫 프레임까지 포함한 전체 Flux)
 |        = 스프링 요청자는 라우트 메타데이터를 첫 프레임에만 싣는다
 |
 +-- L140 metadataPush(payload)
        handle(payload, METADATA_PUSH)
```

```text
 handle 과 handleAndReply

 handle           응답을 만들지 않는다 (fireAndForget, metadataPush)
 handleAndReply   응답을 담을 자리를 헤더에 심고, 처리 후 그 자리를 읽는다

 requestChannel 이 switchOnFirst 를 쓰는 이유
   라우트가 첫 프레임의 메타데이터에만 있다
   첫 프레임을 봐야 어느 핸들러로 보낼지 정할 수 있다
   첫 프레임도 데이터로서 인자 스트림에 그대로 포함된다 (switchOnFirst 가 다시 방출한다)
```

1. 공통 처리는 [MessagingRSocket.handleAndReply](01_MessagingRSocket.handleAndReply/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 프레임 타입
      --> MessageHeaders 에 실려 매핑 조건이 된다
      --> 같은 라우트라도 타입이 다르면 다른 메서드가 선택된다

 requestResponse 의 .next()
      --> 응답이 여럿 와도 첫 원소만 쓴다
      --> 핸들러가 Flux 를 돌려줘도 프로토콜상 하나만 나간다

 metadataPush
      --> 라우팅은 다른 프레임과 똑같이 일어나고 @ConnectMapping 이 받는다
          (CONNECT_CONDITION 이 SETUP 과 METADATA_PUSH 를 함께 담고 있다)
      --> 다만 데이터 페이로드가 없어 소스 주석대로 활용도가 제한적이다
```
