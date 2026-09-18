# ClientHttpRequestFactory

상위: [Spring HTTP 클라이언트](../../README.md) / [spi](../README.md)

동기 클라이언트가 요청 객체를 얻는 자리다. 어떤 HTTP 라이브러리를 쓸지는 이 구현이 정한다.

## 실제 코드

`spring-web` / `org.springframework.http.client` / `ClientHttpRequestFactory.java` L32-L45 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/http/client/ClientHttpRequestFactory.java#L32-L45))

```java
// ClientHttpRequestFactory.java L32-L45
public interface ClientHttpRequestFactory {

    ClientHttpRequest createRequest(URI uri, HttpMethod httpMethod) throws IOException;

}
```

## 흐름에서 불리는 자리

```text
 DefaultRestClient.createRequest (L694)
   인터셉터 있음 --> InterceptingClientHttpRequestFactory 로 감싼다
   버퍼링 필요   --> BufferingClientHttpRequestFactory
   그 밖         --> 설정된 팩토리
   factory.createRequest(uri, method) --> ClientHttpRequest
   request.execute() --> ClientHttpResponse
```

- [DefaultRestClient.exchangeInternal](../../01_DefaultRestClient.exchangeInternal/README.md)

## 구현 계층

```text
 ClientHttpRequestFactory
   +-- JdkClientHttpRequestFactory          java.net.http.HttpClient (기본 후보)
   +-- HttpComponentsClientHttpRequestFactory   Apache HttpClient 5
   +-- JettyClientHttpRequestFactory
   +-- ReactorClientHttpRequestFactory      Reactor Netty (동기 API 로 감싸 사용)
   +-- SimpleClientHttpRequestFactory       HttpURLConnection
   +-- InterceptingClientHttpRequestFactory 인터셉터 체인 래퍼
   +-- BufferingClientHttpRequestFactory    본문을 메모리에 버퍼링 (여러 번 읽기)

 설정
   RestClient.builder().requestFactory(...)
   타임아웃, 커넥션 풀 설정은 이 구현에서
```
