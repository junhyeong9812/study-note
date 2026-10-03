# api-design/15-rpc-and-grpc — 질문

## 질문

1. (왜) RPC는 원격 호출을 함수 호출처럼 보이게 한다. 로컬 함수 호출에는 없고 원격 호출에만 있는 결과는 무엇이며, gRPC 핵심 개념 문서의 어떤 두 문장이 그것을 말하나?
2. (그림) gRPC 단항 호출 하나가 HTTP/2 위에서 어떤 모양인지 그려라 — `:path`, `content-type`, `grpc-timeout`, 메시지 프레이밍, 결과가 실리는 위치. 오류가 났을 때 HTTP 상태는 무엇인가?
3. (예측) 응답하지 않는 서버 메서드를 grpc-java 클라이언트가 (a) 데드라인 없이, (b) `withDeadlineAfter(500ms)`로 부른다. 각각 어떻게 되나? (b)에서 선 위의 `grpc-timeout`과 서버 `Context`는 무엇을 보나?
4. (예측) 바깥 데드라인 1000ms 요청을 받은 서버가 300ms 일한 뒤, 하류 스텁에 데드라인을 걸지 않고 다른 RPC를 부른다. grpc-java 1.72.0에서 하류 호출의 `grpc-timeout`은 대략 얼마이고, 바깥 데드라인이 지나면 하류 호출은 어떤 상태로 끝나나? 이 전파가 끊기는 경우는?
5. (경계) `UNAVAILABLE`·`ABORTED`·`FAILED_PRECONDITION`은 재시도 관점에서 어떻게 다른가? 서버 핸들러가 도메인 예외를 그대로 던지면 클라이언트는 어떤 코드와 문구를 받나?
6. (경계) `doc/http-grpc-status-mapping.md`의 HTTP → gRPC 표(예: 503 → `UNAVAILABLE`)는 언제 쓰는 것인가? 서버가 gRPC 상태를 HTTP 상태로 바꿀 때 써도 되나?
7. (예측) 같은 DNS 이름 뒤에 서버 2대가 있다. grpc-java 채널로 100번 부를 때 `pick_first`와 `round_robin`의 분포는? 이것이 L4 로드 밸런서 뒤의 gRPC와 어떻게 연결되나?
8. (장애 진단) 결제 RPC가 `DEADLINE_EXCEEDED` 뒤 재시도되어 이중 승인이 났다. 왜 이런 일이 가능하고, 무엇으로 막나?
9. (장애 진단) 데이터가 늘자 목록 조회 RPC가 `RESOURCE_EXHAUSTED: gRPC message exceeds maximum size 4194304`로 실패한다. 원인과, 한도를 올리기 전에 고려할 설계는?
10. (적용) grpc-java 클라이언트에 재시도 정책을 서비스 설정 `Map`으로 넣는다. `maxAttempts: 3`처럼 `Integer`를 넣으면 어떻게 되나? 재시도 대상 코드는 무엇으로 두나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
