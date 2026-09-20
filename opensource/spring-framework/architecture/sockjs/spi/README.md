# spi

상위: [Spring SockJS](../README.md)

SockJS 계층의 계약 모음이다. 서비스 하나가 전송 핸들러 여러 개를 들고 있고, 전송 핸들러가 세션을 만들며, 세션이 프레임을 쓴다.

```text
 SockJsService        요청 하나를 받아 처리 (구현이 URL 규약을 안다)
 TransportType        전송 종류와 그 HTTP 메서드
 TransportHandler     전송 방식 하나의 처리 (일부는 세션도 만든다)
 SockJsSession        WebSocketSession 을 구현한 SockJS 세션
 SockJsMessageCodec   메시지 배열 <--> JSON 문자열
```

## 하위 인터페이스

- [SockJsService](SockJsService/README.md) — 요청 처리 계약
- [TransportType](TransportType/README.md) — 전송 종류
- [TransportHandler](TransportHandler/README.md) — 전송별 처리
- [SockJsSession](SockJsSession/README.md) — 세션
- [SockJsMessageCodec](SockJsMessageCodec/README.md) — 메시지 인코딩
