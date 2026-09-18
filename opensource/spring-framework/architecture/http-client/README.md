# Spring HTTP 클라이언트

`RestClient`와 `WebClient`가 요청을 보내고 응답을 객체로 바꾸기까지의 흐름을 위에서 아래로 따라간다. 둘은 같은 모양의 빌더 API를 쓰지만, 하나는 값을 즉시 돌려주고 하나는 `Mono`를 조립한다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 두 클라이언트의 확장 지점이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] RestClient  (동기, spring-web)

 restClient.get().uri("/users/{id}", 42).retrieve().body(User.class)
 |
 +-- [01] DefaultRestClient.exchangeInternal
        URI 확정, 헤더/쿠키 구성
        createRequest(uri) --> ClientHttpRequestFactory (인터셉터가 있으면 감싼 팩토리)
        body.writeTo(request)          HttpMessageConverter 로 요청 본문 쓰기
        request.execute()              <-- 여기서 실제 네트워크 호출 (블로킹)
        exchangeFunction.exchange(...) 응답을 원하는 형태로 변환
        finally 응답 close, 관측 종료
        |
        +-- [01-01] readBody --> 상태 코드 판정 --> HttpMessageConverter 로 본문 읽기
               4xx/5xx 이면 StatusHandler 가 예외를 던진다

 [B] WebClient  (리액티브, spring-webflux)

 webClient.get().uri("/users/{id}", 42).retrieve().bodyToMono(User.class)
 |
 +-- [02] DefaultWebClient.exchange
        ClientRequest 조립 (URI, 헤더, 본문 삽입자)
        ExchangeFilterFunction 체인으로 감싼 ExchangeFunction 적용
        |
        +-- [02-01] ExchangeFunctions.exchange
               connector.connect(method, url, request.writeTo(...))
                 --> 인코더로 요청 본문을 흘려보내고 응답 헤더를 기다린다
               ClientResponse 로 감싸 반환
        |
        +-- 응답 본문은 구독 시점에 디코딩된다 (bodyToMono / bodyToFlux)
```

두 클라이언트를 나란히 놓으면 이렇게 대응된다.

```text
 RestClient (동기)                      WebClient (리액티브)
 ClientHttpRequestFactory               ClientHttpConnector
 ClientHttpRequestInterceptor           ExchangeFilterFunction
 HttpMessageConverter                   Encoder / Decoder (HttpMessageWriter/Reader)
 retrieve().body(Type)                  retrieve().bodyToMono(Type)
 StatusHandler (예외 throw)             onStatus (Mono.error 로 신호)
 호출 즉시 실행                          구독할 때 실행
```

## 단계

1. [DefaultRestClient.exchangeInternal](01_DefaultRestClient.exchangeInternal/README.md)이 동기 요청 한 번을 끝까지 수행한다.
2. [DefaultWebClient.exchange](02_DefaultWebClient.exchange/README.md)가 리액티브 요청 파이프라인을 조립한다.

## 어디에서 쓰이는가

```text
 서비스 코드에서 직접 사용
 @HttpExchange 인터페이스 클라이언트
      --> HttpServiceProxyFactory 가 프록시를 만들고
          그 뒤에서 RestClient 또는 WebClient 가 실제 호출을 한다
 테스트
      --> MockRestServiceServer(RestClient/RestTemplate), MockWebServer 등으로 대체
```

## 다루지 않는 것

`RestTemplate`(구형 동기 클라이언트)과 `@HttpExchange` 프록시 생성 과정은 이 지도에서 다루지 않는다. 커넥터 구현(Reactor Netty, JDK HttpClient)의 내부도 범위 밖이다.

## 하위 메서드

- [01 DefaultRestClient.exchangeInternal](01_DefaultRestClient.exchangeInternal/README.md)
- [02 DefaultWebClient.exchange](02_DefaultWebClient.exchange/README.md)
- [spi](spi/README.md) — 요청 팩토리, 커넥터, 인터셉터, 필터
