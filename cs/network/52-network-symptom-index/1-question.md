# network/52-network-symptom-index — 질문

## 질문

1. (왜) 장애 로그에 증상 이름 하나만 있을 때 곧바로 원인을 적으면 안 되는 이유는 무엇인가? 증상 이름 말고 함께 확보해야 할 맥락 네 가지를 말하라.
2. (번역) 커널에서 `ECONNREFUSED`, `ETIMEDOUT`(connect 중), `EHOSTUNREACH`, `EADDRNOTAVAIL`이 났을 때 JDK의 NIO 기반 소켓 구현은 각각 어떤 예외 클래스로 올리나? `EADDRNOTAVAIL`의 예외 이름이 왜 오진을 부르나?
3. (경계) `EADDRNOTAVAIL`이 `connect()`에서 났을 때와 `bind()`에서 났을 때 원인은 각각 무엇인가? 첫 확인 명령도 하나씩 말하라.
4. (예측) 클라이언트가 connect에서 실패했다. (a) 수 ms 만에, (b) 약 1초·3초 뒤 성공, (c) 약 2분 뒤 실패. 각각 무엇을 의심하나? 리눅스에서 accept 큐가 넘치면 클라이언트는 refused를 보나?
5. (예측) 리눅스에서 상대가 RST를 보낸 연결에 내가 `write()`를 두 번 한다. 각 호출의 결과는? 네이티브 프로세스와 JVM·Node 프로세스는 두 번째 호출에서 어떻게 다르게 보이나?
6. (장애 진단) Java 서비스 로그에 `UnknownHostException`이 쌓인다. 이 예외 하나로는 구분되지 않는 원인 셋은 무엇이고, 같은 호스트에서 어떤 순서로 무엇을 쳐서 가르나? Node `dns.resolve4`라면 SERVFAIL이 어떤 코드로 보이나?
7. (구분) 502·503·504는 각각 무엇을 뜻하나(RFC 9110)? nginx 에러 로그 `upstream timed out (110: Connection timed out)`과 `recv() failed (104: Connection reset by peer)`의 괄호 속 숫자는 무엇이고, 어느 leaf로 가야 하나?
8. (장애 진단) 트래픽이 적은 새벽에만 요청 일부가 `ECONNRESET`으로 실패하고, 서버 쪽에는 에러·재시작 기록이 없다. 무엇을 의심하고, 무엇을 보기 전에는 원인을 단정하지 말아야 하나? 대처 셋을 말하라.
9. (연결) TLS 실패에서 "누가 alert를 보냈나"가 왜 첫 질문인가? `unknown_ca`·`certificate_expired`·`no_application_protocol`·`certificate_required`는 각각 어느 쪽이 보내는 경우가 많고, 어느 노트로 가나?
10. (연결) 에러 없이 나타나는 네트워크 증상을 넷 들고, 각각이 가리키는 leaf와 첫 확인 수단을 말하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
