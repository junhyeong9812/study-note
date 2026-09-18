# spi

상위: [Spring HTTP 클라이언트](../README.md)

두 클라이언트의 확장 지점이다. 같은 역할이 동기 쪽과 리액티브 쪽에 하나씩 짝을 이룬다.

```text
 역할                     RestClient (동기)              WebClient (리액티브)
 전송 계층                ClientHttpRequestFactory       ClientHttpConnector
 가로채기                 ClientHttpRequestInterceptor   ExchangeFilterFunction
 요청->응답 함수          (없음, 직접 실행)               ExchangeFunction
 본문 변환                HttpMessageConverter           HttpMessageWriter / Reader
```

## 하위 인터페이스

- [ClientHttpRequestFactory](ClientHttpRequestFactory/README.md)
- [ClientHttpRequestInterceptor](ClientHttpRequestInterceptor/README.md)
- [ExchangeFunction](ExchangeFunction/README.md)
- [ClientHttpConnector](ClientHttpConnector/README.md)
