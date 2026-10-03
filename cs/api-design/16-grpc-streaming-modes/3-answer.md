# api-design/16-grpc-streaming-modes — 정답

## 정답

### 1. 네 가지 모드

```text
  단항              client ──req──▶ server ──resp──▶                   rpc A(Req) returns (Resp);
  서버 스트리밍      client ──req──▶ server ──r1─r2─…─status──▶          rpc B(Req) returns (stream Resp);
  클라이언트 스트리밍 client ──q1─q2─…─half-close──▶ server ──resp──▶  rpc C(stream Req) returns (Resp);
  양방향            client ⇄ server, 두 방향이 독립                     rpc D(stream Req) returns (stream Resp);
```

- 순서 보장은 **한 RPC 호출 안**에서만이다(gRPC Core concepts). 서로 다른 호출 사이의 순서는 보장하지 않는다.
- 양방향은 두 스트림이 독립이라 읽기·쓰기 순서를 각자 정한다.

### 2. 중간 에러를 삼킨 클라이언트

- 실험 출력: `나쁜 예: 처리 완료로 기록, 받은 seq=[1, 2, 3, 4, 5] (요청은 10개)`.
- 5개는 이미 도착했고, 반복자가 다음 `hasNext()`에서 `UNAVAILABLE`을 던졌다. 이를 삼키면 부분 결과를 전체로 오인한다 — 조용한 절단.
- 기준: 끝 상태가 OK(`onCompleted`)일 때만 완료다. `onError`면 마지막 seq(실험: 5)를 재개 지점으로 기록하고 이어 받는다.

### 3. 스트림 + 데드라인 1초

- 10개를 받고 `DEADLINE_EXCEEDED`(실험, 두 모드 모두).
- 데드라인은 **호출 전체**의 시한이다. 메시지마다 새로 주어지는 것이 아니다.

### 4. 취소를 확인하지 않는 서버

- 클라이언트가 떠난 뒤에도 30번까지 생산했고 그중 19번의 `onNext`가 버려졌다(실험 — 재실행에서는 20번, 실행마다 1개쯤 다르다).
- grpc-java 1.72.0: `CANCELLED: call already cancelled. Use ServerCallStreamObserver.setOnCancelHandler() to disable this exception` 예외.
- 확인·정리: `setOnCancelHandler`로 자원(커서·쿼리·타이머)을 정리하고, 생산 루프에서 `isCancelled()`를 본다. 실험에서는 클라이언트 실패 뒤 0~12ms 안에 멈췄다.

### 5. HTTP/2 흐름 제어

- **수신자**가 스트림별·연결별 창(window) 크기를 광고하고, 송신자는 그 안에서만 보낸다. 흐름 제어는 한 홉 사이에서 동작한다.
- DATA 프레임만 창을 소비한다. 제어 프레임은 막히지 않는다.
- 초기 창: 스트림·연결 각각 65,535 옥텟(RFC 9113). `WINDOW_UPDATE`로 다시 연다.
- grpc-java 1.72.0 Netty 전송의 `DEFAULT_FLOW_CONTROL_WINDOW = 1048576`(1MiB, `javap`로 확인). 시작값이다 — 1.72.0은 BDP 기반 자동 조정(`autoFlowControl`)이 기본으로 켜져 있어 창이 커질 수 있다(소스).

### 6. blind vs ready (실험, 집필 3회 + 재실행 2회 범위)

| | (a) blind | (b) ready |
|---|---|---|
| 보낸 수 | 20,000 전부(1366~1624ms 안에) | 373(5회 모두) |
| `isReady=false`인데 보낸 호출 | 19,996 | 0, 멈춤 113~134회 |
| 클라이언트 4초 소비 | 271~284 | 281~307 |
| 프로세스 RSS | 81~83MB → 292~296MB | 최대 87~90MB |

- grpc-java `onNext`는 막히지 않고 버퍼에 쌓는다. 역압은 `isReady()`를 보는 애플리케이션이 지켜야 한다.
- 취소 뒤 `Stream closed before write could take place` 경고가 났다 — 쓰려던 메시지를 보낼 스트림이 사라졌다. 재실행에서는 ready 쪽에서도 났으므로, 누적 여부는 경고가 아니라 RSS와 `isReady=false`인데 보낸 수로 판단한다.

### 7. 장수 스트림과 LB

- 아니다. `round_robin`은 **새 스트림(호출)**을 어느 연결에 보낼지만 고른다. 시작된 스트림은 끝날 때까지 그 서버에 붙는다. 나중에 추가된 서버는 기존 스트림을 받지 못한다.
- 서버를 내리면 그 서버의 스트림이 한꺼번에 끊기고 재연결이 다른 서버로 몰린다.
- 대비: 서버 `MAX_CONNECTION_AGE`(기본 무한)로 연결을 주기적으로 갈기(GOAWAY로 정상 종료), 재연결 지터, 재개 토큰, 서버별 스트림 수 상한.

### 8. 구독이 일정 간격마다 끊긴다

- 원인: 공통 스텁 설정 등으로 단항용 데드라인이 장수 스트림에도 걸렸다. 데드라인은 호출 전체에 적용되므로 그 시간마다 `DEADLINE_EXCEEDED`(클라이언트)·`CANCELLED`(서버)로 끝난다.
- 대처: 장수 스트림의 데드라인을 따로 정한다(또는 걸지 않는다). 생존 확인은 keepalive(클라이언트 기본 꺼짐 — 켜서 주기 설정)나 애플리케이션 하트비트로 하고, 끊김은 재개 토큰으로 견딘다.

### 9. 10만 건 내보내기

- 단항 + 페이지네이션: 호출마다 LB가 다시 고르고 재시도가 단순하다. 페이지 경계에서 커서로 재개할 수 있다. 운영이 쉬워 기본 선택으로 무난하다.
- 서버 스트리밍: 왕복이 줄고 첫 행이 빨리 온다. 대신 끊김·역압·LB를 직접 다뤄야 한다.
- 서버 스트리밍을 고르면 꼭 넣을 것
  1. 서버: `setOnReadyHandler` + `isReady()` 루프(역압)와 `setOnCancelHandler`(정리).
  2. 클라이언트: `onCompleted`에서만 완료, `onError`는 재시도 대상으로.
  3. 양쪽: 재개 지점(`after_seq` 같은 커서)과 호출 전체 데드라인(예: 10분 — 예시).
