# spi

상위: [Spring STOMP 브로커 릴레이](../README.md)

릴레이가 기대는 TCP 계층 계약이다. 스프링은 네 인터페이스만 정의하고, 실제 네트워킹은 Reactor Netty 구현이 맡는다.

```text
 TcpOperations          연결을 연다 (재연결 전략과 함께 열 수도 있다)
 TcpConnection          열린 연결 하나. 보내기와 유휴 감시
 TcpConnectionHandler   연결 수명 콜백 (연결됨, 실패, 메시지 수신, 종료)
 ReconnectStrategy      다음 재시도까지 얼마나 기다릴지
```

## 하위 인터페이스

- [TcpOperations](TcpOperations/README.md) — 연결 열기
- [TcpConnection](TcpConnection/README.md) — 열린 연결
- [TcpConnectionHandler](TcpConnectionHandler/README.md) — 수명 콜백
- [ReconnectStrategy](ReconnectStrategy/README.md) — 재연결 간격
