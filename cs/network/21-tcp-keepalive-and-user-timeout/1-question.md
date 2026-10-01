# network/21-tcp-keepalive-and-user-timeout — 질문

## 질문

1. (그림) keepalive probe를 보냈을 때 상대가 (a) 살아 있을 때, (b) 재부팅됐을 때, (c) 경로가 끊겼을 때 각각 무엇이 돌아오고 앱은 어떤 결과를 보나?
2. (규범) RFC는 keepalive에 대해 무엇을 MUST로 정하나? 기본 켜짐/꺼짐, 기본 간격, probe 하나 무응답의 해석을 말하라.
3. (계산) 리눅스 기본값으로 keepalive를 켰을 때, 상대가 사라진 idle 연결을 알아채기까지 얼마나 걸리나?
4. (왜) keepalive를 켰는데도 AWS NLB 뒤의 idle 연결이 몇 분 뒤 `ECONNRESET`으로 실패했다. 이유와 대처는?
5. (예측) 상대 서버 전원이 나간 직후 내가 `write()`로 요청을 보냈다. `write()`의 결과, keepalive의 동작, 최종 에러와 대략적 시점을 말하라.
6. (정의) `TCP_USER_TIMEOUT`은 정확히 무엇의 시간을 재나? 재전송 시점을 바꾸나? keepalive와 같이 쓰면 어떻게 되나?
7. (경계) TCP keepalive로 잡을 수 없고 앱 heartbeat가 필요한 경우 두 가지를 들어라.
8. (연결) HTTP/2, gRPC, WebSocket은 각각 어떤 방식으로 heartbeat를 하나? gRPC에서 ping을 너무 자주 보내면?
9. (장애 진단) `TCP_USER_TIMEOUT`을 도입한 뒤 순간적인 망 흔들림에도 연결이 끊긴다. 원인과 값을 정하는 기준은?
10. (연결) Java 표준 API와 Node에서 keepalive 세부 값을 설정하는 방법은? Java에서 user timeout이 필요하면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
