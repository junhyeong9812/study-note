# DefaultRestClient.exchangeInternal

상위: [Spring HTTP 클라이언트](../README.md)

`RestClient` 요청 한 번의 전 과정이다. URI와 헤더를 확정하고, 요청 객체를 만들고, 본문을 쓰고, 네트워크 호출을 하고, 응답을 변환하고, 자원을 닫는다. 모든 단계가 이 메서드 안에서 즉시 실행된다.

## 실제 코드

`spring-web` / `org.springframework.web.client` / `DefaultRestClient.java` L543-L608 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/client/DefaultRestClient.java#L543-L608))

```java
// DefaultRestClient.java L543-L608
private <T extends @Nullable Object> T exchangeInternal(ExchangeFunction<T> exchangeFunction, boolean close) {
    Assert.notNull(exchangeFunction, "ExchangeFunction must not be null");

    ClientHttpResponse clientResponse = null;
    Observation observation = null;
    Observation.Scope observationScope = null;
    URI uri = null;
    try {
        uri = initUri();
        String serializedCookies = serializeCookies();
        if (serializedCookies != null) {
            getHeaders().set(HttpHeaders.COOKIE, serializedCookies);
        }
        HttpHeaders headers = initHeaders();

        ClientHttpRequest clientRequest = createRequest(uri);
        if (headers != null) {
            clientRequest.getHeaders().addAll(headers);
        }
        Map<String, Object> attributes = getAttributes();
        clientRequest.getAttributes().putAll(attributes);
        ClientRequestObservationContext observationContext = new ClientRequestObservationContext(clientRequest);
        observationContext.setUriTemplate((String) attributes.get(URI_TEMPLATE_ATTRIBUTE));
        observation = ClientHttpObservationDocumentation.HTTP_CLIENT_EXCHANGES.observation(observationConvention,
                DEFAULT_OBSERVATION_CONVENTION, () -> observationContext, observationRegistry).start();
        observationScope = observation.openScope();
        if (this.body != null) {
            this.body.writeTo(clientRequest);
        }
        if (this.httpRequestConsumer != null) {
            this.httpRequestConsumer.accept(clientRequest);
        }
        clientResponse = clientRequest.execute();
        observationContext.setResponse(clientResponse);
        ConvertibleClientHttpResponse convertibleWrapper = new DefaultConvertibleClientHttpResponse(clientResponse, this.hints);
        T result = exchangeFunction.exchange(clientRequest, convertibleWrapper);
        if (close && isStreamingResult(result)) {
            close = false;
        }
        return result;
    }
    catch (IOException ex) {
        ResourceAccessException resourceAccessException = createResourceAccessException(uri, this.httpMethod, ex);
        if (observation != null) {
            observation.error(resourceAccessException);
        }
        throw resourceAccessException;
    }
    catch (Throwable error) {
        if (observation != null) {
            observation.error(error);
        }
        throw error;
    }
    finally {
        if (observationScope != null) {
            observationScope.close();
        }
        if (observation != null) {
            observation.stop();
        }
        if (close && clientResponse != null) {
            clientResponse.close();
        }
    }
}
```

요청 객체를 만드는 부분이다. 인터셉터가 있으면 팩토리 자체가 감싸진다.

`spring-web` / `org.springframework.web.client` / `DefaultRestClient.java` L694-L717 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/client/DefaultRestClient.java#L694-L717))

```java
// DefaultRestClient.java L694-L717
private ClientHttpRequest createRequest(URI uri) throws IOException {
    ClientHttpRequestFactory factory;
    if (DefaultRestClient.this.interceptors != null) {
        factory = DefaultRestClient.this.interceptingRequestFactory;
        if (factory == null) {
            factory = new InterceptingClientHttpRequestFactory(
                    DefaultRestClient.this.clientRequestFactory, DefaultRestClient.this.interceptors,
                    DefaultRestClient.this.bufferingPredicate);
            DefaultRestClient.this.interceptingRequestFactory = factory;
        }
    }
    else if (DefaultRestClient.this.bufferingPredicate != null) {
        factory = new BufferingClientHttpRequestFactory(
                DefaultRestClient.this.clientRequestFactory, DefaultRestClient.this.bufferingPredicate);
    }
    else {
        factory = DefaultRestClient.this.clientRequestFactory;
    }
    ClientHttpRequest request = factory.createRequest(uri, this.httpMethod);
    if (DefaultRestClient.this.initializers != null) {
        DefaultRestClient.this.initializers.forEach(initializer -> initializer.initialize(request));
    }
    return request;
}
```

## 동작 흐름

```text
 exchangeInternal(exchangeFunction, close)
 |
 | L551 initUri()          uriBuilderFactory 로 템플릿 확장, API 버전 삽입
 | L552 쿠키 직렬화 --> Cookie 헤더
 | L556 initHeaders()      기본 헤더 + 요청별 헤더 병합
 |
 | L558 createRequest(uri)
 |        인터셉터가 있으면 InterceptingClientHttpRequestFactory
 |        버퍼링 조건이 있으면 BufferingClientHttpRequestFactory
 |        그 밖에는 설정된 ClientHttpRequestFactory 그대로
 |
 | L564 관측(Observation) 컨텍스트 생성
 | L566 관측 시작, L568 스코프 개방
 |
 | L569 body 가 있으면 body.writeTo(clientRequest)
 |        HttpMessageConverter 가 객체를 바이트로 쓴다
 |
 | L575 clientRequest.execute()      <-- 블로킹 호출. 응답이 올 때까지 대기
 |
 | L577 응답을 ConvertibleClientHttpResponse 로 감싼다
 | L578 exchangeFunction.exchange(요청, 응답)
 |        retrieve().body(...) 라면 상태 판정 후 본문을 읽는 함수
 |        exchange(...) 를 직접 쓰면 사용자가 준 함수
 |
 +-- catch IOException --> ResourceAccessException 으로 변환 (연결 실패 등)
 +-- finally  관측 종료, close 가 true 면 응답 close
              스트리밍 결과면 close 를 미룬다 (본문을 아직 읽는 중)
```

1. 본문 읽기와 상태 판정은 [readBody](01_DefaultRestClient.readBody/README.md)에서 이뤄진다.

## 결과가 쓰이는 곳

```text
 반환값
      --> body(Class) 면 변환된 객체
      --> toEntity(...) 면 ResponseEntity
      --> exchange(...) 면 사용자 함수의 반환값

 close 처리
      --> 응답 스트림을 닫지 않으면 커넥션이 풀로 돌아가지 않는다
      --> 스트리밍(예: InputStream 반환)일 때만 호출자에게 책임이 넘어간다

 ResourceAccessException
      --> 연결 실패, 타임아웃 같은 I/O 오류
      --> 4xx/5xx 응답과는 다른 계열 (그쪽은 상태 처리기가 만든다)
```

## 하위 메서드

- [01 DefaultRestClient.readBody](01_DefaultRestClient.readBody/README.md)
