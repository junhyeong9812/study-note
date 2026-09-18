# DefaultRestClient.readBody

상위: [DefaultRestClient.exchangeInternal](../README.md)

응답 본문을 원하는 타입으로 바꾼다. 그 전에 상태 처리기를 돌려 4xx/5xx면 예외를 던지게 한다. 본문 변환은 서버 쪽과 같은 `HttpMessageConverter` 목록을 쓴다.

## 실제 코드

`spring-web` / `org.springframework.web.client` / `DefaultRestClient.java` L793-L811 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/client/DefaultRestClient.java#L793-L811))

```java
// DefaultRestClient.java L793-L811
@Override
public <T> @Nullable T body(Class<T> bodyType) {
    return executeAndExtract((request, response) -> readBody(request, response, bodyType, bodyType, this.hints));
}

@Override
public <T> T requiredBody(Class<T> bodyType) {
    T body = body(bodyType);
    Assert.state(body != null, "The body must not be null");
    return body;
}

@Override
public <T> @Nullable T body(ParameterizedTypeReference<T> bodyType) {
    Type type = bodyType.getType();
    Class<T> bodyClass = bodyClass(type);
    return executeAndExtract((request, response) -> readBody(request, response, type, bodyClass, this.hints));
}

```

`spring-web` / `org.springframework.web.client` / `DefaultRestClient.java` L889-L896 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/client/DefaultRestClient.java#L889-L896))

```java
// DefaultRestClient.java L889-L896
private <T> @Nullable T readBody(
        HttpRequest request, ClientHttpResponse response, Type bodyType, Class<T> bodyClass,
        @Nullable Map<String, Object> hints) {

    return DefaultRestClient.this.readWithMessageConverters(
            response, () -> applyStatusHandlers(request, response), bodyType, bodyClass, hints);

}
```

`spring-web` / `org.springframework.web.client` / `DefaultRestClient.java` L898-L913 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/client/DefaultRestClient.java#L898-L913))

```java
// DefaultRestClient.java L898-L913
private void applyStatusHandlers(HttpRequest request, ClientHttpResponse response) {
    try {
        if (response instanceof DefaultConvertibleClientHttpResponse convertibleResponse) {
            response = convertibleResponse.delegate;
        }
        for (StatusHandler handler : this.statusHandlers) {
            if (handler.test(response)) {
                handler.handle(request, response);
                return;
            }
        }
    }
    catch (IOException ex) {
        throw new UncheckedIOException(ex);
    }
}
```

## 동작 흐름

```text
 body(Class) / body(ParameterizedTypeReference)
 |
 +-- executeAndExtract((request, response) -> readBody(...))
       = exchangeInternal 에 넘길 변환 함수
 |
 +-- readBody(request, response, bodyType, bodyClass, hints)
       |
       +-- readWithMessageConverters(response, 상태 처리 콜백, 타입, 클래스, 힌트)
             1) applyStatusHandlers(request, response)        <-- 먼저 상태를 본다
             |     statusHandlers 를 순서대로 test
             |       매칭되면 handle 호출 --> 보통 예외를 던진다
             |       기본 처리기: 4xx --> HttpClientErrorException
             |                    5xx --> HttpServerErrorException
             |     onStatus(...) 로 등록한 사용자 처리기가 앞선다
             |
             2) 응답 Content-Type 을 보고 읽을 수 있는 컨버터를 찾는다
                  canRead(타입, 미디어 타입) 인 첫 컨버터로 read
                  없으면 UnknownContentTypeException
```

## 결과가 쓰이는 곳

```text
 변환된 객체
      --> body(...) 의 반환값 --> 호출 코드

 상태 처리기가 던진 예외
      --> exchangeInternal 밖으로 전파
      --> RestClientResponseException 계열 (본문, 헤더, 상태 코드를 담고 있다)
      --> retrieve() 대신 exchange(...) 를 쓰면 상태 처리기가 적용되지 않는다
          (응답을 직접 다루겠다는 선언이므로)

 컨버터 선택
      --> 서버 쪽 @ResponseBody 쓰기와 같은 HttpMessageConverter 목록
      --> JSON 이면 Jackson 컨버터가 읽어 객체로
```

`retrieve()`와 `exchange()`의 차이가 여기서 갈린다. `retrieve()`는 상태 처리기를 적용해 오류를 예외로 바꾸고, `exchange()`는 응답을 그대로 넘겨 호출자가 판단하게 한다.
