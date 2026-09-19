# spi

상위: [Spring WebSocket과 STOMP](../README.md)

두 계층의 계약이 섞여 있다. 앞의 넷은 WebSocket 계층(연결과 프레임), 뒤의 둘은 메시징 계층(채널과 메시지)이다. `SubProtocolHandler`가 두 계층을 잇는 자리다.

```text
 WebSocket 계층
   HandshakeHandler     HTTP 요청을 WebSocket 으로 승격할지 정한다
   WebSocketHandler     연결 수명과 프레임 수신 콜백
   WebSocketSession     열린 연결 하나. 프레임을 내보내는 통로

 경계
   SubProtocolHandler   프레임 <--> Message 변환

 메시징 계층
   MessageChannel       메시지를 보내는 통로
   MessageHandler       메시지를 받는 쪽
```

## 하위 인터페이스

- [HandshakeHandler](HandshakeHandler/README.md) — 승격 판정
- [WebSocketHandler](WebSocketHandler/README.md) — 연결과 프레임 콜백
- [WebSocketSession](WebSocketSession/README.md) — 열린 연결
- [SubProtocolHandler](SubProtocolHandler/README.md) — 프레임과 메시지의 경계
- [MessageChannel](MessageChannel/README.md) — 메시지 통로
- [MessageHandler](MessageHandler/README.md) — 메시지 수신자
