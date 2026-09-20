# RelayConnectionHandler.afterConnected

상위: [Spring STOMP 브로커 릴레이](../README.md)

TCP가 열린 직후 불린다. TCP 연결과 STOMP 연결은 다른 것이라, 여기서 CONNECT 프레임을 보내고 CONNECTED가 오기를 기다린다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.simp.stomp` / `StompBrokerRelayMessageHandler.java` L691-L704 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/simp/stomp/StompBrokerRelayMessageHandler.java#L691-L704))

```java
// StompBrokerRelayMessageHandler.java L691-L704
@Override
public void afterConnected(TcpConnection<byte[]> connection) {
    if (logger.isDebugEnabled()) {
        logger.debug("TCP connection " + connection + " opened in session=" + getSessionId());
    }
    this.tcpConnection = connection;
    connection.onReadInactivity(() -> {
        if (this.tcpConnection != null && !this.isStompConnected) {
            handleTcpConnectionFailure("No CONNECTED frame received in " +
                    MAX_TIME_TO_CONNECTED_FRAME + " ms.", null);
        }
    }, MAX_TIME_TO_CONNECTED_FRAME);
    connection.sendAsync(MessageBuilder.createMessage(EMPTY_PAYLOAD, this.connectHeaders.getMessageHeaders()));
}
```

## 동작 흐름

```text
 afterConnected(connection)
 |
 | L696 연결 객체를 보관한다
 |
 +-- L697 onReadInactivity 콜백을 건다
 |        MAX_TIME_TO_CONNECTED_FRAME 안에 읽을 것이 없고
 |        아직 STOMP 연결이 서지 않았으면
 |          --> handleTcpConnectionFailure("No CONNECTED frame received in ... ms.")
 |        = TCP 는 붙었는데 브로커가 STOMP 로 답하지 않는 경우를 잡는다
 |
 +-- L703 CONNECT 프레임을 비동기로 보낸다
        헤더는 만들 때 준비해 둔 connectHeaders 그대로다

 afterConnectFailure(ex)                L707
        handleTcpConnectionFailure("Failed to connect: ...")

 handleTcpConnectionFailure(error, ex)  L715
        클라이언트 세션이면 STOMP ERROR 프레임을 보내고
        연결을 정리한다 (클라이언트 세션만 맵에서 제거, 소켓 닫기)
        시스템 세션 핸들러는 맵에 남는다. 재연결 때 그대로 재사용된다
```

```text
 두 단계 연결

 1) TCP 연결      afterConnected 가 불린다. 아직 STOMP 는 아니다
 2) STOMP 연결    CONNECT 를 보내고 CONNECTED 를 받아야 선다

 사이에 끼어드는 실패가 흔하다
   방화벽이 TCP 는 통과시키지만 브로커가 응답하지 않는 경우
   자격 증명이 틀려 브로커가 ERROR 를 돌려주는 경우
 그래서 읽기 유휴 타임아웃을 따로 건다
```

## 결과가 쓰이는 곳

```text
 보관한 TcpConnection
      --> 이후 forward 가 이 연결로 프레임을 보낸다
      --> null 이면 아직 붙지 않았다는 뜻이다

 onReadInactivity 콜백
      --> 시스템 세션은 CONNECTED 를 받으면 하트비트 주기로 콜백을 교체한다 (L1003-L1026)
      --> 클라이언트 세션은 교체하지 않는다. isStompConnected 가 서면서
          이 콜백의 본문 조건이 거짓이 돼 사실상 무효가 된다

 연결 실패 처리
      --> 클라이언트 세션이면 그 클라이언트에게 ERROR 프레임이 간다
      --> 시스템 세션이면 브로커 사용 불가로 표시되고 재연결이 돈다

 비동기 전송
      --> sendAsync 의 결과를 여기서 확인하지 않는다 (future 를 버린다)
      --> CONNECT 전송 실패는 읽기 유휴 타임아웃이나 handleFailure 로 뒤늦게 드러난다
      --> 반면 forward 는 whenComplete 로 실패를 바로 잡는다 (L913-L929)
```

브로커가 보낸 응답을 받는 자리는 [RelayConnectionHandler.handleMessage](../04_RelayConnectionHandler.handleMessage/README.md)다.
