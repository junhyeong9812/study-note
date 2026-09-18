# ClientHttpConnector

상위: [Spring HTTP 클라이언트](../../README.md) / [spi](../README.md)

리액티브 클라이언트의 전송 계층이다. 연결을 열고, 요청 쓰기 함수를 실행하고, 응답을 스트림으로 돌려준다.

## 실제 코드

`spring-web` / `org.springframework.http.client.reactive` / `ClientHttpConnector.java` L34-L51 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/http/client/reactive/ClientHttpConnector.java#L34-L51))

```java
// ClientHttpConnector.java L34-L51
public interface ClientHttpConnector {

    Mono<ClientHttpResponse> connect(HttpMethod method, URI uri,
            Function<? super ClientHttpRequest, Mono<Void>> requestCallback);

}
```

## 흐름에서 불리는 자리

```text
 ExchangeFunctions.exchange L102
   connector.connect(method, url, request -> clientRequest.writeTo(request, strategies))
     반환 Mono<ClientHttpResponse> — 응답 헤더 수신 시점에 신호
     본문은 이후 구독으로 흘러온다
```

- [ExchangeFunctions.exchange](../../02_DefaultWebClient.exchange/01_ExchangeFunctions.exchange/README.md)

## 구현 계층

```text
 ClientHttpConnector
   +-- ReactorClientHttpConnector      Reactor Netty (기본)
   +-- JdkClientHttpConnector          java.net.http.HttpClient
   +-- JettyClientHttpConnector
   +-- HttpComponentsClientHttpConnector

 설정
   WebClient.builder().clientConnector(...)
   타임아웃, 커넥션 풀, HTTP/2 설정이 여기에

 RestClient 대응물
   ClientHttpRequestFactory
```
