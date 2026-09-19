# RSocketRequester

상위: [Spring RSocket](../../README.md) / [spi](../README.md)

RSocket 연결 하나를 감싼 요청 표면이다. 라우트와 메타데이터, 데이터를 실은 뒤 어떤 상호작용을 쓸지 마지막 메서드로 정한다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket` / `RSocketRequester.java` L53-L70 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/RSocketRequester.java#L53-L70))

```java
// RSocketRequester.java L53-L70
public interface RSocketRequester extends Disposable {

    RSocketClient rsocketClient();

    @Nullable RSocket rsocket();

```

## 흐름에서 불리는 자리

```text
 requester.route("greet.{name}", "jun")     RequestSpec
          .metadata(...)                    추가 메타데이터
          .data(request)                    본문
          .retrieveMono(Response.class)     상호작용 결정 + 실행
```

- [DefaultRSocketRequester.RequestSpec.retrieveMono](../../01_DefaultRSocketRequester.RequestSpec.retrieveMono/README.md)

## 구현 계층

```text
 RSocketRequester
   +-- DefaultRSocketRequester        유일한 구현 (package-private)
         DefaultRequestSpec           route(...) 가 돌려주는 내부 스펙

 만드는 방법
   RSocketRequester.builder()
     .rsocketStrategies(strategies)
     .dataMimeType(...) / .metadataMimeType(...)
     .tcp(host, port) / .websocket(uri) / .transport(...)
   기존 RSocket 을 감싸려면 RSocketRequester.wrap(...)
```

```text
 HTTP 클라이언트와 다른 점

 RestClient/WebClient  메서드(GET/POST)와 URI 가 요청을 정한다
 RSocketRequester      라우트는 메타데이터의 한 항목이고,
                       상호작용은 결과를 꺼내는 메서드가 정한다
 연결이 오래 살아 있어 요청마다 연결을 맺지 않는다
```

## 결과가 쓰이는 곳

```text
 route(...)
      --> 서버의 @MessageMapping 라우트와 맞춰진다
      --> {변수} 는 route() 호출 시점에 MetadataEncoder 가 확장한다

 rsocket() / rsocketClient()
      --> 기반 RSocket 에 직접 닿는 탈출구다
      --> 스프링이 감싸지 않은 API 를 쓸 때 연다

 연결 수명
      --> 요청자 하나가 연결 하나다. 끊기면 다시 만들어야 한다
      --> 서버가 이 연결로 역방향 요청을 보낼 수도 있다
```
