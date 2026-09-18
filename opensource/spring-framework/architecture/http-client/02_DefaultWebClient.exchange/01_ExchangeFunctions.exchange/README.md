# ExchangeFunctions.exchange

상위: [DefaultWebClient.exchange](../README.md)

요청을 실제로 내보내는 가장 안쪽 단계다. 커넥터에 연결을 맡기고, 요청 본문을 쓰는 함수를 넘기고, 돌아온 응답을 `ClientResponse`로 감싼다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.function.client` / `ExchangeFunctions.java` L95-L119 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/function/client/ExchangeFunctions.java#L95-L119))

```java
// ExchangeFunctions.java L95-L119

@Override
public Mono<ClientResponse> exchange(ClientRequest clientRequest) {
    Assert.notNull(clientRequest, "ClientRequest must not be null");
    HttpMethod httpMethod = clientRequest.method();
    URI url = clientRequest.url();

    Mono<ClientHttpResponse> responseMono = this.connector
            .connect(httpMethod, url, httpRequest -> clientRequest.writeTo(httpRequest, this.strategies));
    if (logger.isDebugEnabled()) {
        responseMono = responseMono
                .doOnRequest(n -> logRequest(clientRequest))
                .doOnCancel(() -> logger.debug(clientRequest.logPrefix() + "Cancel signal (to close connection)"));
    }
    return responseMono
            .onErrorResume(WebClientUtils.WRAP_EXCEPTION_PREDICATE, t -> wrapException(t, clientRequest))
            .map(httpResponse -> {
                String logPrefix = getLogPrefix(clientRequest, httpResponse);
                logResponse(httpResponse, logPrefix);
                return new DefaultClientResponse(
                        httpResponse, this.strategies, logPrefix,
                        WebClientUtils.getRequestDescription(httpMethod, url),
                        () -> createRequest(clientRequest));
            });
}
```

## 동작 흐름

```text
 exchange(clientRequest)
 |
 | L102 connector.connect(method, url, httpRequest -> clientRequest.writeTo(httpRequest, strategies))
 |        커넥터가 연결을 열고, 넘긴 함수가 요청 헤더와 본문을 쓴다
 |        본문 쓰기는 HttpMessageWriter(인코더)가 담당
 |        반환은 Mono<ClientHttpResponse> — 응답 헤더까지 받은 시점에 신호
 |
 | L110 연결 계열 오류는 WebClientRequestException 으로 감싼다
 |
 +-- L111 DefaultClientResponse 로 감싸 반환
        응답 헤더/상태는 이미 있고, 본문은 아직 흐르지 않았다
        strategies(코덱)를 함께 담아 나중에 디코딩할 수 있게 한다
```

```text
 RestClient 와의 대비

 RestClient   request.execute()          응답 전체를 기다리는 블로킹 호출
 WebClient    connector.connect(...)     헤더까지만 받고 본문은 스트림으로 남긴다
                                          --> 본문은 bodyToMono 구독 시 흘러온다
```

## 결과가 쓰이는 곳

```text
 ClientResponse
      --> retrieve().bodyToMono(Type)
            상태 판정 --> Decoder 로 본문 디코딩
      --> exchangeToMono(...) 에서 사용자가 직접 다룬다

 본문을 읽지 않은 응답
      --> 커넥션이 반환되지 않는다
      --> exchangeToMono/Flux 는 releaseIfNotConsumed 로 이를 보완한다
          (retrieve() 를 쓰면 프레임워크가 알아서 소비한다)

 WebClientRequestException
      --> 연결 실패, DNS 오류 등 전송 계층 문제
      --> 4xx/5xx 는 정상 응답이므로 여기서 예외가 되지 않는다
          (WebClientResponseException 은 상태 판정 단계에서 만들어진다)
```
