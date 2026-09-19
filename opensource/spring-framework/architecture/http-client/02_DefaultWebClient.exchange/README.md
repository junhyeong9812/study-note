# DefaultWebClient.exchange

상위: [Spring HTTP 클라이언트](../README.md)

`WebClient` 요청 파이프라인을 조립한다. 요청 객체를 만들고 필터 체인으로 감싼 뒤 `Mono<ClientResponse>`를 돌려준다. 실제 호출은 구독 시점에 일어난다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.function.client` / `DefaultWebClient.java` L407-L411 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/client/DefaultWebClient.java#L407-L411))

```java
// DefaultWebClient.java L407-L411
@Override
public ResponseSpec retrieve() {
    return new DefaultResponseSpec(
            this.httpMethod, initUri(), exchange(), DefaultWebClient.this.defaultStatusHandlers);
}
```

`spring-webflux` / `org.springframework.web.reactive.function.client` / `DefaultWebClient.java` L442-L481 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/client/DefaultWebClient.java#L442-L481))

```java
// DefaultWebClient.java L442-L481
private Mono<ClientResponse> exchange() {
    ClientRequest.Builder requestBuilder = initRequestBuilder();
    return Mono.deferContextual(contextView -> {
        Observation observation = ClientHttpObservationDocumentation.HTTP_REACTIVE_CLIENT_EXCHANGES.observation(observationConvention,
                DEFAULT_OBSERVATION_CONVENTION, () -> new ClientRequestObservationContext(requestBuilder), observationRegistry);
        observation
                .parentObservation(contextView.getOrDefault(ObservationThreadLocalAccessor.KEY, null))
                .start();
        ExchangeFilterFunction filterFunction = new ObservationFilterFunction(observation.getContext());
        if (filterFunctions != null) {
            filterFunction = filterFunctions.andThen(filterFunction);
        }
        contextView.getOrEmpty(COROUTINE_CONTEXT_ATTRIBUTE)
                .ifPresent(context -> requestBuilder.attribute(COROUTINE_CONTEXT_ATTRIBUTE, context));
        ClientRequest request = requestBuilder.build();
        if (observation.getContext() instanceof ClientRequestObservationContext observationContext) {
            observationContext.setUriTemplate((String) request.attribute(URI_TEMPLATE_ATTRIBUTE).orElse(null));
            observationContext.setRequest(request);
        }
        final ExchangeFilterFunction finalFilterFunction = filterFunction;
        Mono<ClientResponse> responseMono = Mono.defer(
                        () -> finalFilterFunction.apply(exchangeFunction).exchange(request))
                .checkpoint("Request to " +
                        WebClientUtils.getRequestDescription(request.method(), request.url()) +
                        " [DefaultWebClient]")
                .switchIfEmpty(NO_HTTP_CLIENT_RESPONSE_ERROR);
        final AtomicBoolean responseReceived = new AtomicBoolean();
        return responseMono
                .doOnNext(response -> responseReceived.set(true))
                .doOnError(observation::error)
                .doFinally(signalType -> {
                    if (signalType == SignalType.CANCEL && !responseReceived.get() &&
                            observation.getContext() instanceof ClientRequestObservationContext observationContext) {
                        observationContext.setAborted(true);
                    }
                    observation.stop();
                })
                .contextWrite(context -> context.put(ObservationThreadLocalAccessor.KEY, observation));
    });
}
```

`spring-webflux` / `org.springframework.web.reactive.function.client` / `DefaultWebClient.java` L483-L495 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/client/DefaultWebClient.java#L483-L495))

```java
// DefaultWebClient.java L483-L495
private ClientRequest.Builder initRequestBuilder() {
    ClientRequest.Builder builder = ClientRequest.create(this.httpMethod, initUri())
            .headers(this::initHeaders)
            .cookies(this::initCookies)
            .attributes(attributes -> attributes.putAll(this.attributes));
    if (this.httpRequestConsumer != null) {
        builder.httpRequest(this.httpRequestConsumer);
    }
    if (this.inserter != null) {
        builder.body(this.inserter);
    }
    return builder;
}
```

## 동작 흐름

```text
 retrieve()
   --> DefaultResponseSpec(메서드, URI, exchange(), 기본 상태 처리기)
       상태 판정과 본문 디코딩은 bodyToMono/bodyToFlux 를 구독할 때

 exchange()
 |
 | L443 initRequestBuilder()
 |        URI 확장, 기본 헤더/쿠키 병합, 본문 삽입자(BodyInserter) 설정
 |
 +-- L444 Mono.deferContextual(...)          구독 컨텍스트를 보고 조립
       L445 관측 시작 (부모 관측을 컨텍스트에서 이어받는다)
       L450 관측 필터를 필터 체인 뒤에 붙인다
       L456 ClientRequest 생성 (여기서 불변 객체로 확정)
       |
       L462-L463 Mono.defer(() -> finalFilterFunction.apply(exchangeFunction).exchange(request))
       |      필터들이 ExchangeFunction 을 감싼 형태
       |      = 요청/응답을 가로채 헤더 추가, 인증, 재시도 등을 넣는 자리
       |
       L464 checkpoint(...)                  리액터 스택 트레이스에 이름 남기기
       L467 응답이 비어 있으면 오류
       L472 doFinally 에서 관측 종료 (취소면 L475 aborted 표시, L477 stop)
```

1. 실제 전송은 [ExchangeFunctions.exchange](01_ExchangeFunctions.exchange/README.md)가 커넥터에 위임한다.

## 결과가 쓰이는 곳

```text
 반환 Mono<ClientResponse>
      --> retrieve().bodyToMono(User.class)
            응답 상태 판정(onStatus) --> 본문 디코딩 --> Mono<User>
      --> exchangeToMono(response -> ...)
            사용자가 응답을 직접 다룬다. 다 쓴 뒤 본문 해제를 프레임워크가 보장

 구독 시점 실행
      --> exchange() 를 호출해도 아직 아무 요청도 나가지 않는다
      --> 구독하지 않으면 요청 자체가 없다 (WebClient 를 쓰다 흔히 겪는 지점)

 필터 체인
      --> ExchangeFilterFunction 은 요청 단위로 적용된다
      --> 관측 필터가 마지막에 붙어 실제 전송을 가장 가깝게 감싼다
```
