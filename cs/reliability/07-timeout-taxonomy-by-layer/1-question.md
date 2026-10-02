# reliability/07-timeout-taxonomy-by-layer — 질문

## 질문

1. (그림) HTTP 호출 하나의 시간 조각을 순서대로 그리고, 각 조각을 재는 타임아웃 이름을 붙여라. 새 연결일 때만 생기는 조각은 어느 것인가? 호출 밖에 있는 타임아웃은?
2. (예측) accept 큐가 가득 차 SYN이 버려지는 서버에 connect한다. `tcp_syn_retries`가 2·3·5일 때 타임아웃 없는 connect는 대략 몇 초 뒤 실패하나(리눅스 6.5+, `tcp_syn_linear_timeouts=4`)? 기본 6이면? connect 타임아웃 1초를 걸면?
3. (예측) 서버가 헤더를 즉시 보내고 본문 20바이트를 300ms마다 1바이트씩 보낸다. (a) `Socket.setSoTimeout(1000)`만 건 클라이언트 (b) JDK 21 `HttpClient`에 `HttpRequest.timeout(1s)` (c) Node `fetch` + `AbortSignal.timeout(1000)`은 각각 언제 끝나나?
4. (경계) "read 타임아웃"이라는 같은 이름이 OkHttp·undici·JDK `HttpClient`에서 각각 무엇을 뜻하나? 전체(call) 타임아웃의 기본값이 꺼져 있는 라이브러리 셋을 들어라.
5. (경계) Envoy의 cluster `connect_timeout`과 route `timeout`은 각각 언제 시작해 무엇을 덮나? 기본값은?
6. (연결) 호출 타임아웃을 2초로 걸었는데 사용자 지연이 30초를 넘는다. 어느 구간을 의심하나? HikariCP라면 어떤 설정이고 기본값은?
7. (장애 진단) 평소에는 타임아웃이 0인데 배포 직후 몇 분만 의존 서비스 호출 타임아웃이 난다. AWS Builders' Library 사례에서 원인과 해결은?
8. (적용) JDK `HttpClient`로 "본문 끝까지 포함한 전체 3초"를 보장하려면 무엇을 더 해야 하나? 그 방법에 남는 빈틈은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
