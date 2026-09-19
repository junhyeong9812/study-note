# Spring RSocket

한 연결 위에서 요청-응답, 스트림, 채널, 단방향을 모두 쓰는 프로토콜을 스프링 메시징에 얹은 흐름이다. WebSocket/STOMP가 프레임을 텍스트 프로토콜로 해석했다면, 여기서는 프레임 타입 자체가 상호작용 방식이 된다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 요청자와 전략 계약 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] 보내는 쪽 — RSocketRequester

 requester.route("greet.{name}", "jun").data(req).retrieveMono(Res.class)
 |
 +-- [01] DefaultRSocketRequester.RequestSpec.retrieveMono
 |        라우트와 메타데이터를 인코딩해 Payload 를 만들고
 |        rsocketClient.requestResponse(payload) 를 부른다
 |        응답 Payload 를 디코더로 객체로 되돌린다
 |
 +-- 상호작용 방식은 호출한 메서드가 정한다
        send()          --> fireAndForget
        retrieveMono()  --> requestResponse
        retrieveFlux()  --> requestStream (보낼 것이 Flux 면 requestChannel)

 [B] 받는 쪽 — MessagingRSocket

 RSocketMessageHandler.responder() 가 만든 SocketAcceptor
 |
 +-- [02] MessagingRSocket.requestResponse / requestStream / requestChannel
 |        프레임 타입을 붙여 handleAndReply 로 보낸다
 |
 +-- [02-01] MessagingRSocket.handleAndReply
 |        메타데이터에서 라우트를 뽑아 MessageHeaders 를 만든다
 |        응답을 담을 AtomicReference 를 헤더에 심는다
 |        Message 를 만들어 messageHandler.handleMessage 로 보낸다
 |
 +-- [03] AbstractMethodMessageHandler.handleMessage  (리액티브 쪽)
 |        라우트로 @MessageMapping 메서드를 찾아 호출한다
 |
 +-- [04] RSocketPayloadReturnValueHandler.handleEncodedContent
          인코딩된 결과를 위에서 심어 둔 AtomicReference 에 넣는다
          handleAndReply 가 그 참조를 꺼내 응답 Flux 로 돌려준다
```

```text
 네 가지 상호작용

 fireAndForget     요청 1, 응답 0      Mono<Void>
 requestResponse   요청 1, 응답 1      Mono<Payload>
 requestStream     요청 1, 응답 N      Flux<Payload>
 requestChannel    요청 N, 응답 N      Flux<Payload>

 같은 @MessageMapping 메서드라도 프레임 타입이 다르면 다른 매핑이다
 RSocketFrameTypeMessageCondition 이 그 조건을 들고 있다
```

```text
 STOMP 와 나란히 보기

 STOMP                                  RSocket
 텍스트 프레임을 파싱해 command 결정      프레임 타입이 프로토콜 수준에 있다
 destination 헤더로 라우팅                메타데이터의 route 로 라우팅
 브로커가 구독자에게 뿌린다                응답이 요청자에게 직접 돌아간다
 MessageChannel 로 계층을 나눈다          핸들러를 직접 호출한다 (채널 없음)
 양쪽 모두 @MessageMapping 과 MessageHandler 계약을 공유한다
```

## 어디에서 쓰이는가

```text
 [빈 생성] RSocketMessageHandler 는 빈으로 등록돼 @MessageMapping 을 훑는다
 [WebFlux] RSocket 을 WebSocket 위에 얹으면 웹 계층과 한 서버를 공유한다
 [메시징] Message, MessageHeaders, HandlerMethod 골격을 STOMP 와 공유한다
```

프레임을 메시지로 바꿔 라우팅한다는 뼈대는 [WebSocket과 STOMP](../websocket-stomp/README.md)와 같다. 리액티브 타입을 다루는 방식은 [WebFlux 요청 처리](../webflux-request-processing/README.md)와 닮았다.

## 단계

1. [DefaultRSocketRequester.RequestSpec.retrieveMono](01_DefaultRSocketRequester.RequestSpec.retrieveMono/README.md)가 요청을 보낸다.
2. [MessagingRSocket.requestResponse](02_MessagingRSocket.requestResponse/README.md)가 프레임을 받는다.
3. [MessagingRSocket.handleAndReply](02_MessagingRSocket.requestResponse/01_MessagingRSocket.handleAndReply/README.md)가 메시지로 바꾼다.
4. [AbstractMethodMessageHandler.handleMessage](03_AbstractMethodMessageHandler.handleMessage/README.md)가 핸들러를 찾는다.
5. [RSocketPayloadReturnValueHandler.handleEncodedContent](04_RSocketPayloadReturnValueHandler.handleEncodedContent/README.md)가 응답을 돌려준다.

## 결과가 쓰이는 곳

```text
 요청자가 만든 Payload
      --> 데이터와 메타데이터가 한 프레임에 담긴다
      --> 라우트도 메타데이터의 한 항목이다 (헤더가 따로 없다)

 헤더에 심은 AtomicReference
      --> 반환값 처리기와 프레임 처리기를 잇는 통로다
      --> 요청-응답 계열에서만 심는다. fireAndForget 에는 없다

 프레임 타입 조건
      --> 같은 라우트라도 requestStream 과 requestResponse 가 다른 메서드로 간다
      --> @MessageMapping 만 보고는 어느 상호작용인지 알 수 없다

 연결 수명
      --> 한 연결이 양방향이다. 서버도 클라이언트에게 요청을 보낼 수 있다
      --> @ConnectMapping 이 연결 수립 시점을 다룬다
```

## 다루지 않는 것

메타데이터 인코딩/추출 세부(`MetadataEncoder`, `DefaultMetadataExtractor`의 복합 메타데이터 처리), 연결 수립 경로(`@ConnectMapping`, `DefaultRSocketRequesterBuilder.connect`), 선언형 클라이언트(`RSocketServiceProxyFactory`와 `@RSocketExchange`), 전송 계층(TCP, WebSocket)은 같은 뼈대의 갈래라 요약만 했다. RSocket 프로토콜 자체와 리액터 구현도 범위 밖이다.

## 하위 메서드

- [01 DefaultRSocketRequester.RequestSpec.retrieveMono](01_DefaultRSocketRequester.RequestSpec.retrieveMono/README.md)
- [02 MessagingRSocket.requestResponse](02_MessagingRSocket.requestResponse/README.md)
- [03 AbstractMethodMessageHandler.handleMessage](03_AbstractMethodMessageHandler.handleMessage/README.md)
- [04 RSocketPayloadReturnValueHandler.handleEncodedContent](04_RSocketPayloadReturnValueHandler.handleEncodedContent/README.md)
- [spi](spi/README.md) — 요청자, 전략, 메타데이터 추출, 프레임 조건, 선언형 교환
