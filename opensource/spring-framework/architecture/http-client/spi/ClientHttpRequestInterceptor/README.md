# ClientHttpRequestInterceptor

상위: [Spring HTTP 클라이언트](../../README.md) / [spi](../README.md)

동기 클라이언트의 요청 가로채기다. 요청을 바꾸거나 응답을 감싸고, 체인을 통해 다음으로 넘긴다.

## 실제 코드

`spring-web` / `org.springframework.http.client` / `ClientHttpRequestInterceptor.java` L34-L92 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/http/client/ClientHttpRequestInterceptor.java#L34-L92))

```java
// ClientHttpRequestInterceptor.java L34-L92
public interface ClientHttpRequestInterceptor {

    ClientHttpResponse intercept(HttpRequest request, byte[] body, ClientHttpRequestExecution execution)
            throws IOException;

    default ClientHttpRequestInterceptor andThen(ClientHttpRequestInterceptor interceptor) {
        Assert.notNull(interceptor, "ClientHttpRequestInterceptor must not be null");
        return (request, body, execution) -> {
            ClientHttpRequestExecution nextExecution =
                    (nextRequest, nextBody) -> interceptor.intercept(nextRequest, nextBody, execution);
            return intercept(request, body, nextExecution);
        };
    }

    default ClientHttpRequestExecution apply(ClientHttpRequestExecution execution) {
        Assert.notNull(execution, "ClientHttpRequestExecution must not be null");
        return (request, body) -> intercept(request, body, execution);
    }

}
```

## 흐름에서 불리는 자리

```text
 createRequest 시점에 InterceptingClientHttpRequestFactory 가 체인을 만든다
 execute() 호출이 체인을 타고 내려간다
   인터셉터 1 --> 인터셉터 2 --> 실제 전송
 응답은 역순으로 돌아 나온다
```

- [DefaultRestClient.exchangeInternal](../../01_DefaultRestClient.exchangeInternal/README.md)

## 구현 계층

```text
 대표 사용
   인증 헤더 추가, 요청/응답 로깅, 재시도, 상관관계 ID 전파

 주의
   본문을 읽는 인터셉터는 BufferingClientHttpRequestFactory 와 함께 써야 한다
   (스트림은 한 번만 읽을 수 있다)

 WebClient 대응물
   ExchangeFilterFunction
```
