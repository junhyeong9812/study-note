# Spring STOMP 브로커 릴레이

내장 브로커 대신 RabbitMQ나 ActiveMQ 같은 외부 메시지 브로커에 STOMP로 중계하는 흐름이다. [WebSocket과 STOMP](../websocket-stomp/README.md) 흐름의 브로커 자리에 다른 구현을 끼우는 갈래이고, 새로 생기는 것은 TCP 연결의 수명 관리다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 TCP 계약 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] 기동 — 시스템 세션 하나를 먼저 연다

 SmartLifecycle.start --> AbstractBrokerMessageHandler
 |
 +-- [01] StompBrokerRelayMessageHandler.startInternal
          TCP 클라이언트를 만들고
          CONNECT 프레임을 준비해 "system" 세션으로 브로커에 붙는다
          재연결 전략(5초 간격)을 함께 넘긴다

 [B] 나가는 길 — 메시지를 브로커로 중계

 clientInboundChannel / brokerChannel 의 구독자
 |
 +-- [02] handleMessageInternal
          브로커가 죽어 있으면 클라이언트 세션엔 ERROR 프레임,
          서버 발신엔 MessageDeliveryException
          세션 id 로 연결 핸들러를 찾는다
            CONNECT     --> 세션마다 TCP 연결을 새로 연다
            DISCONNECT  --> 그 연결로 흘려보낸다
            그 밖        --> 목적지 접두가 맞으면 흘려보낸다
                            아니면 필요할 때만 하트비트를 보내고 무시한다

 [C] 연결 수명

 +-- [03] RelayConnectionHandler.afterConnected
          TCP 가 열리면 CONNECT 프레임을 보낸다
          정해진 시간 안에 CONNECTED 가 안 오면 실패로 처리한다

 [D] 들어오는 길 — 브로커가 보낸 것을 클라이언트로

 +-- [04] RelayConnectionHandler.handleMessage
          브로커에서 온 프레임에 세션 id 와 사용자를 채워 넣고
          CONNECTED 면 하트비트를 맞춘 뒤
          clientOutboundChannel 로 내보낸다
```

```text
 연결이 두 종류다

 시스템 세션 (SYSTEM_SESSION_ID)
   기동 때 하나 열어 두고 끝까지 유지한다
   서버 코드가 SimpMessagingTemplate 으로 보내는 메시지가 이 연결로 나간다
   끊기면 BrokerAvailabilityEvent 로 "브로커 사용 불가"가 알려진다

 클라이언트 세션
   WebSocket 클라이언트가 STOMP CONNECT 할 때마다 TCP 연결을 하나씩 연다
   그래서 클라이언트 수만큼 브로커 연결이 생긴다
   인증 정보는 clientLogin/clientPasscode 로 덮어쓴다
```

```text
 내장 브로커와 비교

 SimpleBrokerMessageHandler     구독을 메모리에 들고 직접 뿌린다
                                서버가 여러 대면 구독이 공유되지 않는다
 StompBrokerRelayMessageHandler 구독과 전달을 브로커가 책임진다
                                서버는 중계만 한다. 서버를 늘려도 동작한다
 둘 다 AbstractBrokerMessageHandler 의 하위라 채널 계약은 같다
```

## 어디에서 쓰이는가

```text
 [WebSocket과 STOMP] 채널 구독자 자리에 이 핸들러가 들어간다
   clientInboundChannel 과 brokerChannel 을 구독한다
 [컨테이너 기동] SmartLifecycle 이라 refresh 끝에 startInternal 이 불린다
 [이벤트 발행] 브로커 가용성 변화를 BrokerAvailabilityEvent 로 알린다
```

채널과 프레임 처리의 뼈대는 [WebSocket과 STOMP](../websocket-stomp/README.md) 흐름에 있다. 이 흐름은 그중 브로커 자리만 바꾼다.

## 단계

1. [StompBrokerRelayMessageHandler.startInternal](01_StompBrokerRelayMessageHandler.startInternal/README.md)이 시스템 세션을 연다.
2. [handleMessageInternal](02_StompBrokerRelayMessageHandler.handleMessageInternal/README.md)이 메시지를 중계한다.
3. [RelayConnectionHandler.afterConnected](03_RelayConnectionHandler.afterConnected/README.md)가 TCP 연결 직후 CONNECT를 보낸다.
4. [RelayConnectionHandler.handleMessage](04_RelayConnectionHandler.handleMessage/README.md)가 브로커 응답을 클라이언트로 돌린다.

## 결과가 쓰이는 곳

```text
 세션별 TCP 연결
      --> 클라이언트 수만큼 브로커 연결이 열린다
      --> 클래스 javadoc 이 "CONNECT 마다 독립 TCP 연결"이라고 밝힌다

 시스템 세션
      --> 서버가 보내는 모든 메시지의 출구다
      --> 이 연결이 끊기면 서버 발신이 통째로 막힌다

 BrokerAvailabilityEvent
      --> 애플리케이션이 브로커 상태 변화를 알 수 있는 지점이다
      --> 끊긴 동안 온 메시지는 ERROR 프레임으로 거절된다

 목적지 접두
      --> 접두가 맞지 않는 메시지는 브로커로 보내지 않는다
      --> 하트비트가 필요한 상태일 때만 대신 하트비트를 보낸다
```

## 다루지 않는 것

TCP 클라이언트 구현(`ReactorNettyTcpClient`의 커넥션 풀과 코덱), 하트비트 스케줄링 세부, 시스템 세션의 구독 관리(`@SubscribeMapping` 대응), 브로커별 프로토콜 차이는 같은 뼈대의 갈래라 요약만 했다. STOMP 프로토콜 규격과 브로커 구현도 범위 밖이다.

## 하위 메서드

- [01 StompBrokerRelayMessageHandler.startInternal](01_StompBrokerRelayMessageHandler.startInternal/README.md)
- [02 StompBrokerRelayMessageHandler.handleMessageInternal](02_StompBrokerRelayMessageHandler.handleMessageInternal/README.md)
- [03 RelayConnectionHandler.afterConnected](03_RelayConnectionHandler.afterConnected/README.md)
- [04 RelayConnectionHandler.handleMessage](04_RelayConnectionHandler.handleMessage/README.md)
- [spi](spi/README.md) — TCP 연산, 연결, 연결 핸들러, 재연결 전략
