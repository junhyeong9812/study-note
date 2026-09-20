# Spring SockJS

WebSocket을 쓸 수 없는 환경에서도 같은 `WebSocketHandler` 코드를 쓰게 해 주는 폴백 계층이다. 브라우저와 서버 사이에 HTTP 요청 여러 개를 엮어 "연결처럼 보이는 것"을 만든다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 서비스와 전송 계약 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 DispatcherServlet --> SockJsHttpRequestHandler (HttpRequestHandler)
 |
 +-- [01] handleRequest
 |        요청을 ServerHttpRequest 로 감싸 SockJsService 에 넘긴다
 |
 +-- [01-01] AbstractSockJsService.handleRequest
 |        URL 의 sockJsPath 로 무엇을 할지 가른다
 |          "/"                 --> "Welcome to SockJS!"
 |          "/info"             --> 서버 능력 정보 (JSON)
 |          "/iframe*.html"     --> 교차 출처용 iframe 문서
 |          "/websocket"        --> 순수 WebSocket 승격
 |          "/{server}/{session}/{transport}" --> 전송 요청
 |
 +-- [02] TransportHandlingSockJsService.handleTransportRequest
 |        transport 문자열로 TransportHandler 를 고른다
 |        세션이 없으면 만들고, 있으면 사용자 일치를 확인한다
 |
 +-- [03] AbstractHttpSendingTransportHandler.handleRequest   서버 --> 클라이언트
 |        새 세션이면 열기 프레임, 아니면 다음 요청을 매달아 둔다
 |
 +-- [04] AbstractHttpReceivingTransportHandler.handleRequest  클라이언트 --> 서버
          본문에서 메시지 배열을 읽어 세션에 넘긴다
          세션이 WebSocketHandler.handleMessage 를 호출한다
```

```text
 전송 방식 (TransportType)

 websocket        진짜 WebSocket. 나머지는 전부 HTTP 폴백이다
 xhr_streaming    긴 응답 하나에 프레임을 계속 흘린다
 xhr              서버가 보낼 것이 생길 때까지 응답을 잡아 둔다 (롱 폴링)
 xhr_send         클라이언트가 서버로 보낼 때 쓰는 별도 요청
 eventsource      Server-Sent Events
 htmlfile         iframe 스트리밍

 보내는 길과 받는 길이 서로 다른 요청이라는 점이 WebSocket 과 가장 다르다
```

## 어디에서 쓰이는가

```text
 [MVC 요청 처리] SockJS 요청도 전부 평범한 HTTP 요청이다
   WebSocketHandlerMapping 이 SockJsHttpRequestHandler 를 찾아 준다
 [WebSocket과 STOMP] 세션이 만들어지면 그 위는 같은 코드가 돈다
   SubProtocolWebSocketHandler 와 STOMP 처리는 전송 방식을 모른다
```

핸드셰이크와 프레임 처리는 [WebSocket과 STOMP](../websocket-stomp/README.md) 흐름에 있다. 이 흐름은 그 앞단에서 "연결처럼 보이는 것"을 만들어 준다.

## 단계

1. [SockJsHttpRequestHandler.handleRequest](01_SockJsHttpRequestHandler.handleRequest/README.md)가 요청을 받는다.
2. [AbstractSockJsService.handleRequest](01_SockJsHttpRequestHandler.handleRequest/01_AbstractSockJsService.handleRequest/README.md)가 URL로 갈래를 정한다.
3. [TransportHandlingSockJsService.handleTransportRequest](02_TransportHandlingSockJsService.handleTransportRequest/README.md)가 전송과 세션을 정한다.
4. [AbstractHttpSendingTransportHandler.handleRequest](03_AbstractHttpSendingTransportHandler.handleRequest/README.md)가 보내는 길을 연다.
5. [AbstractHttpReceivingTransportHandler.handleRequest](04_AbstractHttpReceivingTransportHandler.handleRequest/README.md)가 받은 메시지를 넘긴다.

## 결과가 쓰이는 곳

```text
 만들어진 SockJsSession
      --> WebSocketSession 을 구현한다. 위층은 차이를 모른다
      --> STOMP 핸들러, @MessageMapping 까지 그대로 동작한다

 세션 id 로 묶인 요청들
      --> 같은 세션에 보내는 길 요청과 받는 길 요청이 따로 온다
      --> 서버는 세션 맵으로 그 둘을 잇는다

 하트비트
      --> 프록시가 유휴 연결을 끊지 못하게 주기적으로 h 프레임을 보낸다

 세션 만료
      --> 정해진 시간 안에 다음 요청이 오지 않으면 세션을 닫는다
      --> 폴링 방식에서는 "연결이 끊겼다"를 이 시간으로만 알 수 있다
```

## 다루지 않는 것

전송 방식별 구현 세부(`XhrPollingTransportHandler`, `EventSourceTransportHandler` 등 각각의 프레임 포맷), 클라이언트 쪽 구현(`sockjs/client` 패키지), 하트비트와 세션 만료 스케줄링, iframe 문서 생성과 캐시 헤더는 같은 뼈대의 갈래라 요약만 했다. SockJS 프로토콜 규격 자체도 범위 밖이다.

## 하위 메서드

- [01 SockJsHttpRequestHandler.handleRequest](01_SockJsHttpRequestHandler.handleRequest/README.md)
- [02 TransportHandlingSockJsService.handleTransportRequest](02_TransportHandlingSockJsService.handleTransportRequest/README.md)
- [03 AbstractHttpSendingTransportHandler.handleRequest](03_AbstractHttpSendingTransportHandler.handleRequest/README.md)
- [04 AbstractHttpReceivingTransportHandler.handleRequest](04_AbstractHttpReceivingTransportHandler.handleRequest/README.md)
- [spi](spi/README.md) — 서비스, 전송 핸들러, 세션, 메시지 코덱, 전송 종류
