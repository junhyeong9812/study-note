# DefaultRSocketRequester.RequestSpec.retrieveMono

상위: [Spring RSocket](../README.md)

요청자 쪽 끝이다. 어떤 메서드로 결과를 꺼내느냐가 곧 어떤 상호작용을 쓰느냐를 정한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket` / `DefaultRSocketRequester.java` L285-L296 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/DefaultRSocketRequester.java#L285-L296))

```java
// DefaultRSocketRequester.java L285-L296
@SuppressWarnings("unchecked")
private <T> Mono<T> retrieveMono(ResolvableType elementType) {
    Mono<Payload> payloadMono = rsocketClient.requestResponse(getPayloadMono());

    if (isVoid(elementType)) {
        return (Mono<T>) payloadMono.then();
    }

    Decoder<?> decoder = strategies.decoder(elementType, dataMimeType);
    return (Mono<T>) payloadMono.map(this::retainDataAndReleasePayload)
            .map(dataBuffer -> Objects.requireNonNull(decoder.decode(dataBuffer, elementType, dataMimeType, EMPTY_HINTS)));
}
```

여러 건을 받는 경로는 보낼 것이 하나인지 여럿인지로 갈린다.

`spring-messaging` / `org.springframework.messaging.rsocket` / `DefaultRSocketRequester.java` L308-L323 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/DefaultRSocketRequester.java#L308-L323))

```java
// DefaultRSocketRequester.java L308-L323
@SuppressWarnings("unchecked")
private <T> Flux<T> retrieveFlux(ResolvableType elementType) {

    Flux<Payload> payloadFlux = (this.payloadFlux != null ?
            rsocketClient.requestChannel(this.payloadFlux) :
            rsocketClient.requestStream(getPayloadMono()));

    if (isVoid(elementType)) {
        return payloadFlux.thenMany(Flux.empty());
    }

    Decoder<?> decoder = strategies.decoder(elementType, dataMimeType);
    return payloadFlux.map(this::retainDataAndReleasePayload).map(dataBuffer ->
            (T) Objects.requireNonNull(decoder.decode(dataBuffer, elementType, dataMimeType, EMPTY_HINTS)));
}

```

## 동작 흐름

```text
 retrieveMono(elementType)
 |
 | L287 rsocketClient.requestResponse(getPayloadMono())
 |        getPayloadMono 이 라우트와 메타데이터, 데이터를 한 Payload 로 만든다
 |        보낼 것이 Flux 면 여기서 IllegalStateException (상호작용이 맞지 않는다)
 |
 +-- L289 반환 타입이 void 면 응답 본문을 버리고 완료 신호만 넘긴다
 |
 +-- L293 그 밖이면 디코더로 Payload --> 객체
        strategies.decoder(타입, dataMimeType) 로 고른다

 retrieveFlux(elementType)
 |
 +-- L311 보낼 것이 Flux 면 requestChannel(payloadFlux)
 |      아니면 requestStream(getPayloadMono())
 |
 +-- L319 같은 방식으로 원소마다 디코딩
```

```text
 메서드 선택이 프로토콜을 정한다

 send()            --> fireAndForget    응답 없음
 retrieveMono()    --> requestResponse  응답 1
 retrieveFlux()    --> requestStream    응답 N
 data(Flux) 후 retrieveFlux() --> requestChannel  요청 N, 응답 N

 HTTP 클라이언트와 달리 "메서드와 본문"이 아니라
 "무엇을 기대하느냐"가 프레임 타입이 된다
```

## 결과가 쓰이는 곳

```text
 반환한 Mono/Flux
      --> 구독해야 프레임이 나간다. 조립만으로는 아무 일도 없다
      --> WebFlux 컨트롤러가 그대로 돌려주면 응답 시점에 구독된다

 디코더 선택
      --> RSocketStrategies 가 들고 있는 디코더 목록에서 고른다
      --> dataMimeType 은 연결 수립 때 정해져 연결 내내 고정이다

 상호작용 불일치
      --> Flux 를 보내면서 Mono 를 기대하면 조립 단계에서 예외가 난다
      --> 프로토콜 수준의 제약이 API 수준에서 드러난다

 라우트
      --> route("greet.{name}", "jun") 의 변수는 route() 를 부르는 순간
          MetadataEncoder 가 확장해 둔다 (인코딩 자체는 구독 시점)
      --> 서버는 이 문자열을 메타데이터에서 꺼내 라우팅에 쓴다
```

받는 쪽 입구는 [MessagingRSocket.requestResponse](../02_MessagingRSocket.requestResponse/README.md)다.
