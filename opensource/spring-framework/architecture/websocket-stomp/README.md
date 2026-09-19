# Spring WebSocket과 STOMP

HTTP 요청 하나가 WebSocket 연결로 승격되고, 그 위로 흐르는 STOMP 프레임이 메시지 채널을 거쳐 `@MessageMapping` 메서드와 브로커에 닿는 흐름이다. 요청-응답이 아니라 양방향 메시지라서, 앞의 요청 처리 흐름들과 달리 "누가 누구에게 언제" 보내는지가 중심이다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 핸들러와 채널 계약 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] 핸드셰이크 — HTTP 가 WebSocket 이 되는 순간

 DispatcherServlet --> WebSocketHandlerMapping --> HttpRequestHandlerAdapter
 |
 +-- [01] WebSocketHttpRequestHandler.handleRequest
 |        HandshakeInterceptor 체인을 먼저 돌린다 (인증, 속성 심기)
 |        하나라도 false 면 승격하지 않고 끝낸다
 |
 +-- [01-01] AbstractHandshakeHandler.doHandshake
          메서드, Upgrade/Connection 헤더, Sec-WebSocket-Key, 버전, Origin 검사
          서브프로토콜과 확장을 고른 뒤
          RequestUpgradeStrategy.upgrade(...) 로 컨테이너에 승격을 맡긴다

 [B] 수신 — 프레임이 메시지가 된다

 컨테이너가 프레임을 넘긴다
 |
 +-- [02] SubProtocolWebSocketHandler.handleMessage
 |        세션에 맞는 SubProtocolHandler 를 고른다
 |
 +-- [02-01] StompSubProtocolHandler.handleMessageFromClient
 |        BufferingStompDecoder 로 STOMP 프레임을 파싱한다
 |        프레임이 덜 왔으면 버퍼에 모아 두고 끝낸다
 |        파싱한 Message 를 clientInboundChannel 로 보낸다
 |
 +-- [03] ExecutorSubscribableChannel.sendInternal
          구독자마다 SendTask 를 만들어 실행기에 던진다
          실행기가 없으면 호출 스레드에서 그대로 돈다

 [C] 라우팅 — 채널의 구독자들

 clientInboundChannel 의 구독자
 |
 +-- [04] SimpAnnotationMethodMessageHandler (AbstractMethodMessageHandler.handleMessage)
 |        목적지 접두(/app)를 떼어 내고 @MessageMapping 메서드를 찾는다
 |
 +-- [05] SimpleBrokerMessageHandler.handleMessageInternal
          접두(/topic, /queue)가 맞으면 구독자에게 복제해 보낸다
          CONNECT 면 세션을 등록하고 CONNECT_ACK 를 돌려준다

 [D] 송신 — 메시지가 다시 프레임이 된다

 brokerMessagingTemplate.convertAndSend --> brokerChannel --> 브로커 --> clientOutboundChannel
 |
 +-- [06] StompSubProtocolHandler.handleMessageToClient
          Message 를 STOMP 프레임으로 인코딩해 session.sendMessage 로 내보낸다
```

```text
 채널 세 개가 경계를 만든다

 clientInboundChannel    클라이언트 --> 서버 (프레임을 메시지로 바꾼 뒤)
 clientOutboundChannel   서버 --> 클라이언트 (프레임으로 인코딩하기 전)
 brokerChannel           애플리케이션 코드 --> 브로커 (SimpMessagingTemplate)

 clientInbound / clientOutbound 에는 기본으로 실행기가 붙어
 수신 처리와 송신 처리가 다른 스레드에서 돈다
 brokerChannel 은 기본적으로 실행기가 없어 호출 스레드에서 돈다
```

## 어디에서 쓰이는가

```text
 [MVC 요청 처리] 핸드셰이크 요청도 평범한 HTTP 요청이다
   WebSocketHandlerMapping 이 HandlerMapping 목록의 하나로 참여한다
 [이벤트 발행] 세션 연결/해제 시 SessionConnectedEvent 등을 발행한다
 [컨테이너 기동] 핸들러들과 채널 실행기가 SmartLifecycle 이라 refresh 끝에 시작된다
   (채널 자체는 Lifecycle 이 아니다)
```

핸드셰이크에 이르는 HTTP 경로는 [MVC 요청 처리](../webmvc-request-processing/README.md), 발행되는 이벤트는 [이벤트 발행](../event-publishing/README.md) 흐름에 있다.

## 단계

1. [WebSocketHttpRequestHandler.handleRequest](01_WebSocketHttpRequestHandler.handleRequest/README.md)가 승격 요청을 받는다.
2. [SubProtocolWebSocketHandler.handleMessage](02_SubProtocolWebSocketHandler.handleMessage/README.md)가 프레임을 서브프로토콜 핸들러에 넘긴다.
3. [ExecutorSubscribableChannel.sendInternal](03_ExecutorSubscribableChannel.sendInternal/README.md)이 구독자들에게 배달한다.
4. [AbstractMethodMessageHandler.handleMessage](04_AbstractMethodMessageHandler.handleMessage/README.md)가 `@MessageMapping`을 찾는다.
5. [SimpleBrokerMessageHandler.handleMessageInternal](05_SimpleBrokerMessageHandler.handleMessageInternal/README.md)이 구독자에게 뿌린다.
6. [StompSubProtocolHandler.handleMessageToClient](06_StompSubProtocolHandler.handleMessageToClient/README.md)가 프레임으로 내보낸다.

## 결과가 쓰이는 곳

```text
 승격된 WebSocketSession
      --> 그 뒤의 모든 프레임이 이 세션을 통해 오간다
      --> 핸드셰이크 때 심은 attributes 가 세션 수명 내내 따라다닌다

 파싱된 Message
      --> STOMP 헤더가 스프링 MessageHeaders 로 바뀐다
      --> destination, sessionId, subscriptionId 가 이후 라우팅의 입력이다

 채널 구독자 목록
      --> 같은 메시지가 라우팅 핸들러와 브로커에 함께 전달된다
      --> 그래서 /app 으로 보낸 메시지가 컨트롤러를 타고,
          /topic 으로 보낸 메시지가 브로커로 간다

 세션 단위 처리 순서
      --> 실행기를 쓰면 프레임 처리가 여러 스레드에 흩어진다
      --> 순서를 지켜야 하면 세션별 직렬화가 따로 필요하다
```

## 다루지 않는 것

SockJS 폴백(`SockJsHttpRequestHandler`와 전송 방식들), 외부 브로커 릴레이(`StompBrokerRelayMessageHandler`의 TCP 연결 관리), 하트비트 스케줄링, 사용자 목적지 변환(`UserDestinationMessageHandler`), 보안 연동은 같은 뼈대의 갈래라 요약만 했다. WebSocket 프로토콜 자체와 컨테이너별 업그레이드 구현도 범위 밖이다.

## 하위 메서드

- [01 WebSocketHttpRequestHandler.handleRequest](01_WebSocketHttpRequestHandler.handleRequest/README.md)
- [02 SubProtocolWebSocketHandler.handleMessage](02_SubProtocolWebSocketHandler.handleMessage/README.md)
- [03 ExecutorSubscribableChannel.sendInternal](03_ExecutorSubscribableChannel.sendInternal/README.md)
- [04 AbstractMethodMessageHandler.handleMessage](04_AbstractMethodMessageHandler.handleMessage/README.md)
- [05 SimpleBrokerMessageHandler.handleMessageInternal](05_SimpleBrokerMessageHandler.handleMessageInternal/README.md)
- [06 StompSubProtocolHandler.handleMessageToClient](06_StompSubProtocolHandler.handleMessageToClient/README.md)
- [spi](spi/README.md) — 핸들러, 세션, 핸드셰이크, 서브프로토콜, 채널
