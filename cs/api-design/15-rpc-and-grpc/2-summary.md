# api-design/15-rpc-and-grpc — RPC 의미론·gRPC·데드라인·상태 코드 — 정리 (힌트)

## 해결하는 문제

다른 서버의 기능을 쓰고 싶다. 매번 URL·메서드·본문 형식·에러 해석을 손으로 짜면 서비스가 늘수록 실수도 는다.

```text
  손으로 짜는 HTTP 호출                           RPC
  String body = mapper.writeValueAsString(req);   Resp r = stub.getOrder(req);   ← 함수 호출처럼
  HttpRequest.newBuilder(URI.create(base+"/..."))   (직렬화·경로·상태 해석은 생성된 코드가)
  if (status == 404) ... else if (status == 409) ...
```

- *RPC(Remote Procedure Call)*: 원격 기능을 로컬 함수 호출 모양으로 부르게 하는 방식.
  - *스텁(stub)*: 클라이언트 쪽에서 함수처럼 보이는 대리 객체. 인자를 직렬화해 보내고 응답을 되살린다.
  - *IDL(Interface Definition Language)*: 서비스·메서드·메시지를 언어 중립으로 적은 계약. gRPC는 `.proto`를 쓴다.
- 하지만 원격 호출은 함수가 아니다. 함수 호출에는 없는 결과가 하나 더 있다.

```text
  로컬 함수:  성공 | 예외
  원격 호출:  성공 | 실패 | 모름 ← 요청이 갔는지, 처리됐는지, 응답만 잃었는지 알 수 없다
```

쉬운 예: 전화 주문이다.
- 통화 중에 끊기면 주문이 들어갔는지 모른다. 다시 걸어 "아까 주문 들어갔나요?"를 물어야 한다.
- 상대가 전화를 안 받으면 언제까지 기다릴지 내가 정해야 한다.

똑같은 구조다.\
RPC 프레임워크가 해 주는 것은 "전화 거는 절차"다. "언제 포기하나(데드라인)"와 "끊겼을 때 다시 해도 되나(멱등)"는 설계자의 몫으로 남는다.

실무 예:
- 하류 서비스가 멈췄는데 호출 쪽 스레드가 전부 대기 상태로 묶여 상류까지 멈춘다 — 데드라인을 안 걸었다.
- 서버 Pod를 4개로 늘렸는데 부하가 한 Pod에만 몰린다 — L4 로드 밸런서 + 오래 사는 HTTP/2 연결.

## 동작·원리

### 1. RPC의 모양과 한계

```text
  클라이언트 프로세스                                서버 프로세스
  app ─ stub.getOrder(req)                          OrderService.getOrder(req, out)
         │ 직렬화(proto)                                 ▲ 역직렬화
         ▼                                               │
       채널(연결 풀·이름 해석·LB) ══ HTTP/2 스트림 ══▶ 서버 런타임
```

- gRPC 핵심 개념 문서의 두 문장이 RPC의 한계를 요약한다.
  - "클라이언트와 서버는 호출의 성공 여부를 각자 독립적으로, 국소적으로 판단하며, 그 결론은 다를 수 있다." 예) 서버는 성공으로 끝냈는데 클라이언트는 데드라인을 넘겨 실패로 본다.
  - "취소 전에 일어난 변경은 롤백되지 않는다."
- 그래서 "모름"이 생기는 호출(결제·주문 생성)은 재시도해도 안전하게 만들어야 한다 — 멱등 키([05-idempotency-keys](../05-idempotency-keys/2-summary.md), [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)).
- 네트워크를 로컬처럼 다루면 생기는 착각 목록은 [distributed/01-why-distributed-and-fallacies](../../distributed/01-why-distributed-and-fallacies/2-summary.md).

### 2. gRPC가 HTTP/2 위에 싣는 것

```text
  요청 HEADERS   :method POST
                 :path /exp.Exp/Slow                 ← /패키지.서비스/메서드
                 content-type application/grpc
                 grpc-timeout 498765u                ← 남은 시간(실험에서 본 값)
  요청 DATA      [압축 플래그 1B][길이 4B][protobuf 메시지]   ← 길이 접두 메시지
  응답 HEADERS   :status 200
  응답 DATA      [0][길이][메시지] ...
  응답 TRAILERS  grpc-status 0   grpc-message ...    ← 결과는 트레일러에
```

- gRPC over HTTP/2 명세(grpc/grpc `doc/PROTOCOL-HTTP2.md`)
  - `grpc-timeout`: 최대 8자리 정수 + 단위(H·M·S·m·u·n).
  - 메시지마다 1바이트 압축 플래그와 4바이트 길이가 앞에 붙는다.
  - 결과는 트레일러의 `grpc-status`·`grpc-message`에 있다. 정상 gRPC 응답의 HTTP 상태는 200이다.
- 그래서 HTTP 상태 코드만 세는 L7 지표·로그는 gRPC 오류를 놓친다. `grpc-status`를 따로 봐야 한다.
- 다중화·흐름 제어·GOAWAY 같은 HTTP/2 자체 동작은 [network/36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md).

### 3. 데드라인 — 기본값은 "없음"

```text
  데드라인 없음                               데드라인 500ms
  client ──Slow──▶ server(멈춤)               client ──Slow(grpc-timeout≈500ms)──▶ server
     │ 기다림…                                   │                                   │ Context deadline 496ms
     │ 기다림… (3초 뒤에도 done=false)            ├── 500ms ── DEADLINE_EXCEEDED        │
     │ 기다림… ∞                                  │                         서버 Context 취소 감지
```

- gRPC Deadlines 가이드: "기본적으로 gRPC는 데드라인을 설정하지 않으며, 클라이언트가 사실상 영원히 응답을 기다릴 수 있다." 그래서 현실적인 데드라인을 명시하라고 권한다.
- 데드라인을 넘기면 클라이언트는 `DEADLINE_EXCEEDED`로 실패한다. 서버 쪽 호출은 취소된다. 서버가 시작한 작업을 멈추는 것은 서버 애플리케이션 책임이다.
  - *데드라인(deadline)*: "이 시각까지"라는 절대 시각. *타임아웃*: "지금부터 이만큼"이라는 길이. gRPC는 선 위에 남은 시간(`grpc-timeout`)을 싣는다.

### 실험: 데드라인 없음 vs 500ms, 그리고 전파

```java
// 서버: 응답하지 않는 Slow (멈춘 하류 흉내)
@Override public void slow(Req req, StreamObserver<Resp> out) {
    Deadline d = Context.current().getDeadline();
    log("Slow 시작, Context deadline=" + (d == null ? "없음" : d.timeRemaining(MILLISECONDS) + "ms 남음"));
    Context.current().addListener(c -> log("Slow 취소 감지: " + c.cancellationCause()), Runnable::run);
}
// 서버: 받은 요청 안에서 300ms 일한 뒤 하류 Slow 호출 — 하류 스텁에 데드라인을 따로 걸지 않는다
@Override public void relay(Req req, StreamObserver<Resp> out) { Thread.sleep(300); self.slow(req); ... }

// 클라이언트
stub.slow(req);                                            // (1) 데드라인 없음
stub.withDeadlineAfter(500, MILLISECONDS).slow(req);       // (2) 500ms
stub.withDeadlineAfter(1000, MILLISECONDS).relay(req);     // (5) 1000ms → Relay → Slow
```

(실험, grpc-java 1.72.0 · protobuf-java 3.25.5, JDK 21.0.11, Netty 루프백, `--cpus=2`, 2026-10-04)

```text
  1508ms [server] exp.Exp/Slow grpc-timeout=null
  1518ms [server] Slow 시작, Context deadline=없음
  4024ms [client] 3초 경과: 데드라인 없는 호출 done=false (아직 대기 중)
  4035ms [server] Slow 취소 감지: io.grpc.InternalStatusRuntimeException: CANCELLED: RPC cancelled
  4038ms [client] 데드라인 없음 → 결국 CANCELLED (실험이 직접 취소)
  4050ms [server] exp.Exp/Slow grpc-timeout=498765u
  4057ms [server] Slow 시작, Context deadline=496ms 남음
  4550ms [server] Slow 취소 감지: java.util.concurrent.TimeoutException: context timed out
  4568ms [client] 데드라인 500ms → DEADLINE_EXCEEDED after 513ms, desc=CallOptions deadline exceeded after 0.499810021s. ...
  5248ms [server] exp.Exp/Relay grpc-timeout=999513u
  5250ms [server] Relay 시작, 받은 deadline=997ms 남음 → 300ms 일한 뒤 하류 Slow 호출(스텁에 데드라인 미지정)
  5556ms [server] exp.Exp/Slow grpc-timeout=696105u
  5558ms [server] Slow 시작, Context deadline=694ms 남음
  6248ms [server] Relay의 하류 호출 → CANCELLED
  6250ms [client] Relay(1000ms) → DEADLINE_EXCEEDED after 1003ms
```

관찰
- 데드라인이 없으면 3초가 지나도 호출이 끝나지 않았다. 실험이 직접 취소하지 않았다면 계속 기다렸을 것이다.
- 500ms를 걸면 선 위에 `grpc-timeout=498765u`(마이크로초)가 실리고, 서버 `Context`가 남은 시간(496ms)을 안다. 513ms 뒤 `DEADLINE_EXCEEDED`(사실 점검 재실행 4회에서는 503~512ms).
- 서버의 취소 원인 문구는 실행마다 달랐다(`context timed out` 또는 `CANCELLED: RPC cancelled` — 클라이언트 RST와 서버 타이머 중 먼저 온 쪽).
- **전파**: 하류 스텁에 데드라인을 걸지 않았는데도, grpc-java 1.72.0은 서버 `Context`의 남은 시간(696ms ≈ 1000 - 300 - 왕복)을 하류 호출의 `grpc-timeout`으로 실었다. 바깥 데드라인이 끝나자 하류 호출도 끝났다. 끝 상태는 실행마다 달랐다 — 위 실행은 `CANCELLED`, 사실 점검 재실행 4회는 모두 `DEADLINE_EXCEEDED`. 하류 호출의 데드라인(전파된 696ms)과 바깥 `Context` 취소가 거의 같은 순간에 오기 때문으로 보인다(해석).
  - 이 자동 전파는 같은 `Context` 안에서 호출할 때의 grpc-java 동작이다. 별도 스레드 풀로 넘기면 `Context`가 따라가지 않을 수 있다([reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)). gRPC Deadlines 가이드는 자동 전파를 "일부 구현이" 지원한다고 쓰고, Java·Go는 기본으로 켜져 있고 C++ 등은 명시적으로 켜야 한다고 적는다.

### 4. 상태 코드 — 재시도 판단의 언어

```text
  0 OK                  5 NOT_FOUND           10 ABORTED            15 DATA_LOSS
  1 CANCELLED           6 ALREADY_EXISTS      11 OUT_OF_RANGE       16 UNAUTHENTICATED
  2 UNKNOWN             7 PERMISSION_DENIED   12 UNIMPLEMENTED
  3 INVALID_ARGUMENT    8 RESOURCE_EXHAUSTED  13 INTERNAL
  4 DEADLINE_EXCEEDED   9 FAILED_PRECONDITION 14 UNAVAILABLE
```

- gRPC Status codes 문서의 재시도 지침
  - `UNAVAILABLE`: 실패한 그 호출만 다시 해도 된다.
  - `ABORTED`: 더 높은 수준(예: 읽기-수정-쓰기 전체)에서 다시 해야 한다.
  - `FAILED_PRECONDITION`: 시스템 상태를 명시적으로 고치기 전에는 다시 하지 말라.
- 라이브러리가 만드는 코드: 데드라인 초과 → `DEADLINE_EXCEEDED`, 애플리케이션 예외 → `UNKNOWN`, 연결 실패 → `UNAVAILABLE`, 클라이언트 취소 → `CANCELLED`.
- HTTP 상태와의 관계(grpc/grpc `doc/http-grpc-status-mapping.md`)
  - 프록시 등이 `grpc-status` 없이 HTTP 오류를 돌려줄 때만 쓰는 표다: 404 → `UNIMPLEMENTED`, 429·502·503·504 → `UNAVAILABLE`, 401 → `UNAUTHENTICATED`, 403 → `PERMISSION_DENIED`, 400 → `INTERNAL`.
  - 서버가 이 표로 HTTP 상태를 만들면 안 된다(다대일·비대칭이라서).

(같은 실험 실행에서)

```text
  4916ms [client] Fail(throw) → UNKNOWN(2) desc=Application error processing RPC
  4925ms [client] Fail(notfound) → NOT_FOUND(5) desc=order 42 not found
  4934ms [client] Fail(precondition) → FAILED_PRECONDITION(9) desc=order already shipped
  4942ms [client] exp.Exp/Nope → UNIMPLEMENTED desc=Method not found: exp.Exp/Nope
  6797ms [client] 5MB 응답 → RESOURCE_EXHAUSTED desc=gRPC message exceeds maximum size 4194304: 5000007
```

- 서버가 `IllegalStateException("db password=s3cret ...")`을 던지면 클라이언트는 `UNKNOWN` + `Application error processing RPC`만 받았다. 예외 문구는 서버 로그(`SEVERE`)에만 남았다 — 내부 정보가 새지 않는 대신, 클라이언트는 재시도 여부를 판단할 정보가 없다.
- grpc-java 1.72.0의 기본 최대 수신 메시지 크기는 4194304바이트(4MiB, `GrpcUtil.DEFAULT_MAX_MESSAGE_SIZE`를 `javap`로 확인)였고, 넘으면 `RESOURCE_EXHAUSTED`였다.

### 5. 로드 밸런싱 — 연결 단위 vs 요청 단위

```text
  L4(연결 단위) LB                              요청 단위(L7 프록시 또는 클라이언트 측 LB)
  client ══ 연결 1개(HTTP/2, 오래 산다) ══▶ A    client ─ 요청1 ▶ A
                                         B(놀음)        ─ 요청2 ▶ B
  RPC가 전부 그 연결 위로 다중화된다                     ─ 요청3 ▶ A ...
```

- Kubernetes 블로그(2018-11-07, William Morgan): gRPC는 오래 사는 HTTP/2 연결 하나를 재사용하므로, kube-proxy 같은 L4 분산에서는 한 클라이언트의 트래픽이 한 Pod에 고정된다.
- gRPC 블로그(2017-06-15) "gRPC Load Balancing": 프록시(L7) LB는 클라이언트가 단순하고 신뢰할 수 없는 클라이언트에도 쓰지만 데이터 경로에 홉이 하나 는다. 클라이언트 측 LB는 홉이 없지만 클라이언트가 복잡해진다.

### 실험: 같은 이름 뒤 서버 2대, 정책별 100회 호출

```java
ManagedChannel ch = ManagedChannelBuilder.forTarget("dns:///grpcsrv:50051")
    .defaultLoadBalancingPolicy(policy)          // "pick_first" | "round_robin"
    .usePlaintext().build();
```

(실험, Docker 사용자 네트워크에서 서버 2대에 같은 별칭 `grpcsrv`, grpc-java 1.72.0, 2026-10-04 — 워밍업 1회 + 500ms 대기 후 3회 반복)

```text
DNS grpcsrv -> [grpcsrv/172.28.0.2, grpcsrv/172.28.0.3]
pick_first 100회 -> {srv-a=100}
round_robin 100회 -> {srv-a=50, srv-b=50}
```

- 집필 때 3회는 모두 같았다. 사실 점검 재실행 2회에서는 `pick_first`가 `{srv-b=100}`·`{srv-a=100}`(DNS가 먼저 돌려준 주소 쪽), `round_robin`이 `{srv-a=46, srv-b=54}`·`{srv-a=50, srv-b=50}`이었다 — 정확히 반반은 아니어도 두 서버에 퍼진다. 워밍업 없이 돌린 첫 실행은 `round_robin`이 `{srv-a=11, srv-b=89}`였다 — 두 번째 연결이 준비되기 전의 호출이 한쪽으로 갔다.
- grpc-java 기본 정책인 `pick_first`는 연결 하나만 쓴다. L4 LB 뒤에 있는 것과 같은 모양이 된다.

## 쓰이는 자료구조·알고리즘

- **길이 접두 프레이밍** — `[플래그 1B][길이 4B][본문]`. 스트림에서 메시지 경계를 찾는다.
- **절대 시각 → 남은 시간 변환** — 받은 `grpc-timeout`을 수신 시각에 더해 데드라인(절대)으로 들고, 나갈 때 다시 "남은 시간"으로 바꾼다. 서버 간 시계가 어긋나도 영향이 작다(gRPC Deadlines 가이드).
- **라운드 로빈 피커** — 준비된(READY) 서브채널 목록을 원형으로 돈다. 목록이 바뀌면 피커를 새로 만든다.
- **지수 백오프 + 지터** — gRPC 재시도 정책의 `initialBackoff`·`maxBackoff`·`backoffMultiplier`, 지연에 ±20% 지터(gRPC Retry 가이드). [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md).
- **varint 기반 메시지** — [08-schema-and-serialization](../08-schema-and-serialization/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **계약**: `.proto`로 서비스·메시지를 정의하고 진화 규칙(번호 재사용 금지·`reserved`)을 지킨다([08](../08-schema-and-serialization/2-summary.md)).
2. **데드라인**: 클라이언트 호출마다 데드라인을 건다. 값은 하류 지연 분포와 상류 예산에서 정한다([reliability/08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md)).
3. **취소 존중**: 서버는 긴 작업 중 `Context`/`isCancelled()`를 확인해 멈춘다([reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md)).
4. **상태 코드 설계**: 도메인 예외를 의미 있는 코드로 바꾼다. 아무 예외나 던지면 전부 `UNKNOWN`이다.
5. **재시도**: 재시도할 코드(`UNAVAILABLE` 등)만 서비스 설정으로 명시하고, 부작용 있는 메서드는 멱등 키와 함께.
6. **로드 밸런싱**: 연결 단위 L4 앞에 두지 않는다. 클라이언트 측 `round_robin`(헤드리스 서비스·DNS) 또는 L7 프록시. 서버에 `MAX_CONNECTION_AGE`를 두어 연결을 주기적으로 갈아 새 서버로 퍼지게 한다.

### 2. 클라이언트 — 데드라인과 재시도 설정 (Java, grpc-java 1.x)

```java
Map<String, Object> retry = Map.of(
    "methodConfig", List.of(Map.of(
        "name", List.of(Map.of("service", "shop.OrderService", "method", "GetOrder")),
        "retryPolicy", Map.of(
            "maxAttempts", 3.0, "initialBackoff", "0.1s", "maxBackoff", "1s",
            "backoffMultiplier", 2.0, "retryableStatusCodes", List.of("UNAVAILABLE")))));

ManagedChannel ch = ManagedChannelBuilder.forTarget("dns:///order-svc:50051")
    .defaultLoadBalancingPolicy("round_robin")
    .defaultServiceConfig(retry).enableRetry()
    .usePlaintext().build();

OrderReply r = OrderServiceGrpc.newBlockingStub(ch)
    .withDeadlineAfter(300, TimeUnit.MILLISECONDS)     // 호출마다 — 스텁을 재사용하면 시각이 고정되므로 매번 만든다
    .getOrder(OrderRequest.newBuilder().setId("ord_123").build());
```

- 서비스 설정 `Map`의 숫자는 `Double`로 넣는다. 같은 설정을 `Integer`로 넣었더니 grpc-java 1.72.0이 채널을 만들 때 거부했다(실험, `RetryCfg15`). 오류 문구에 찍히는 항목 이름은 실행마다 달랐다(`backoffMultiplier=2` 또는 `maxAttempts=3` — `Map.of`의 순회 순서가 JVM 실행마다 달라 먼저 검사된 항목이 찍힌다).

```text
maxAttempts=Double -> 호출 성공 (ok)
maxAttempts=Integer -> IllegalArgumentException: The value of the map entry 'backoffMultiplier=2' is of type 'class java.lang.Integer', which is not supported
```

- `withDeadlineAfter`는 그 시점부터 시각을 계산한다. 같은 스텁 객체를 오래 재사용하면 데드라인이 이미 지나 있을 수 있다.
- 재시도 정책을 설정하지 않아도 gRPC는 "요청이 서버 애플리케이션 로직에 닿지 않은 경우"에 한해 투명 재시도를 한다(gRPC Retry 가이드). 요청이 클라이언트를 떠나지 못했으면 횟수 제한 없이, 서버 gRPC 라이브러리까지만 닿았으면 한 번이다. 채널에서 재시도를 끄면(`disableRetry()`) 투명 재시도도 꺼진다(같은 가이드).

### 3. 서버 — 도메인 예외를 상태 코드로

- 단항 호출의 핸들러는 `onHalfClose` 안에서 불리므로 거기서 예외를 잡는다(코드 모양 — 이 블록은 실행하지 않았다).

```java
class StatusMappingInterceptor implements ServerInterceptor {
    public <Q, R> ServerCall.Listener<Q> interceptCall(ServerCall<Q, R> call, Metadata h, ServerCallHandler<Q, R> next) {
        ServerCall.Listener<Q> d = next.startCall(call, h);
        return new ForwardingServerCallListener.SimpleForwardingServerCallListener<>(d) {
            @Override public void onHalfClose() {
                try { super.onHalfClose(); }
                catch (OrderNotFound e) { call.close(Status.NOT_FOUND.withDescription(e.getMessage()), new Metadata()); }
                catch (AlreadyShipped e) { call.close(Status.FAILED_PRECONDITION.withDescription(e.getMessage()), new Metadata()); }
                // 그 밖의 예외는 내부 정보를 숨기고 INTERNAL·UNKNOWN으로, 상세는 서버 로그에만
            }
        };
    }
}
```

### 4. 진단

```bash
# 서비스·메서드 목록과 호출(서버 리플렉션이 켜져 있을 때) — grpcurl 사용 예
grpcurl -plaintext -max-time 0.5 localhost:50051 list
grpcurl -plaintext -max-time 0.5 -d '{"id":"ord_123"}' localhost:50051 shop.OrderService/GetOrder
# 연결 편중: 서버별 RPC 수 지표(이름은 예시)를 Pod별로 비교
#   grpc_server_handled_total{grpc_code!="OK"} by (pod)
```

- 오류 지표는 HTTP 상태가 아니라 `grpc-status`(코드별)로 본다. 정상 gRPC 응답의 HTTP 상태는 200이다.

## 장애 시나리오와 대처

### 1. 데드라인 미설정 → 하류 정지 시 무한 대기 (⚠ 커리큘럼)

- 현상: 재고 서비스가 GC로 멈추자 주문 서비스의 요청 스레드가 전부 대기에 묶이고, 주문 API 전체가 응답하지 않는다.
- 보이는 형태: 주문 서비스 스레드 덤프에 `blockingUnaryCall` 대기 스택이 쌓인다. 하류의 `grpc-timeout` 로그가 비어 있다(실험: `grpc-timeout=null`).
- 원인: gRPC 기본값은 데드라인 없음(gRPC Deadlines 가이드). 실험에서 3초 뒤에도 호출이 끝나지 않았다.
- 대처: 호출마다 데드라인. 서버 쪽에서도 `grpc-timeout` 없는 요청을 지표로 세어 누락을 찾는다.

### 2. L4 LB + 장수 HTTP/2 연결 → 부하 불균형 (⚠ 커리큘럼)

- 현상: Pod를 늘려도 새 Pod의 CPU가 놀고, 기존 Pod 하나가 포화된다.
- 보이는 형태: Pod별 RPC 수가 크게 다르다. 롤링 배포 직후 새 Pod에 트래픽이 거의 없다.
- 원인: L4는 연결을 나누고, gRPC 채널은 연결 하나에 여러 RPC를 다중화한다(실험: `pick_first` → 한 서버 100회).
- 대처: 클라이언트 측 `round_robin`(실험: 50/50) + 헤드리스 서비스, 또는 요청 단위 L7 프록시. 서버 `MAX_CONNECTION_AGE`로 연결을 주기적으로 끊어 재분산(gRPC Keepalive 가이드의 서버 옵션, 기본값 무한).

### 3. 모든 오류가 `UNKNOWN`이다

- 현상: 클라이언트 재시도 정책이 무엇을 다시 할지 정할 수 없다. 대시보드의 오류가 전부 `UNKNOWN`.
- 원인: 서버 핸들러가 도메인 예외를 그대로 던졌다(실험: `UNKNOWN` + `Application error processing RPC`).
- 대처: 인터셉터에서 도메인 예외를 `NOT_FOUND`·`FAILED_PRECONDITION`·`ABORTED` 등으로 사상한다. 내부 문구는 로그에만.

### 4. `DEADLINE_EXCEEDED`를 재시도했더니 두 번 실행됐다

- 현상: 결제 RPC가 타임아웃 뒤 재시도되어 이중 승인.
- 원인: `DEADLINE_EXCEEDED`는 "서버가 했는지 모름"이다. 핵심 개념 문서대로 취소 전 변경은 롤백되지 않는다.
- 대처: 부작용 있는 메서드는 요청에 멱등 키를 넣고 서버가 키-결과를 저장한다([reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)). 재시도 대상 코드에서 `DEADLINE_EXCEEDED`를 빼거나, 멱등 메서드에만 둔다.

### 5. 큰 응답이 `RESOURCE_EXHAUSTED`로 실패한다

- 현상: 데이터가 쌓이자 목록 조회 RPC가 갑자기 실패한다.
- 보이는 형태: `RESOURCE_EXHAUSTED: gRPC message exceeds maximum size 4194304: 5000007`(실험 문구).
- 원인: grpc-java 기본 최대 수신 메시지 4MiB.
- 대처: 한도를 늘리기 전에 페이지네이션([06-pagination](../06-pagination/2-summary.md))이나 서버 스트리밍([16](../16-grpc-streaming-modes/2-summary.md))으로 나눈다.

## 핵심 문장

- RPC는 원격 호출을 함수처럼 보이게 하지만, 결과에는 "모름"이 있다. 데드라인과 멱등은 프레임워크가 아니라 설계자의 몫이다.
- gRPC는 기본 데드라인이 없다. 실험에서 데드라인 없는 호출은 3초 뒤에도 끝나지 않았고, 500ms를 걸면 `DEADLINE_EXCEEDED`로 끝났다.
- grpc-java는 같은 `Context` 안의 하류 호출에 남은 시간을 `grpc-timeout`으로 실어 전파했다.
- 상태 코드는 재시도 판단의 언어다 — `UNAVAILABLE`은 그 호출만, `ABORTED`는 상위 단위로, `FAILED_PRECONDITION`은 상태를 고친 뒤에.
- gRPC는 오래 사는 연결 하나에 여러 RPC를 다중화한다. 연결을 나누는 L4 LB 뒤에서는 한 서버에 몰리므로, 요청 단위로 나누는 클라이언트 측 LB나 L7 프록시를 쓴다.

## 관련 주제·근거

- 선행: [08-schema-and-serialization](../08-schema-and-serialization/2-summary.md), [network/36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md)
- 후속·연결: [16-grpc-streaming-modes](../16-grpc-streaming-modes/2-summary.md), [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md), [reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md), [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md), [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md), [18-api-style-selection](../18-api-style-selection/2-summary.md), network/46-load-balancers-and-proxies(새 형식 노트 없음, 원고 [systems/server-design/02-request-path](../../systems/server-design/02-request-path.md) — [network 영역](../../network/README.md))
- 근거
  - gRPC Core concepts — https://grpc.io/docs/what-is-grpc/core-concepts/
  - gRPC Deadlines — https://grpc.io/docs/guides/deadlines/
  - gRPC Status codes — https://grpc.io/docs/guides/status-codes/
  - gRPC Retry — https://grpc.io/docs/guides/retry/
  - gRPC Keepalive — https://grpc.io/docs/guides/keepalive/ (서버 `MAX_CONNECTION_AGE` 기본 무한, 클라이언트 keepalive 기본 꺼짐)
  - gRPC over HTTP/2 — https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
  - HTTP → gRPC 상태 매핑 — https://github.com/grpc/grpc/blob/master/doc/http-grpc-status-mapping.md
  - gRPC 블로그 "gRPC Load Balancing"(2017-06-15) — https://grpc.io/blog/grpc-load-balancing/
  - Kubernetes 블로그 "gRPC Load Balancing on Kubernetes without Tears"(2018-11-07) — https://kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears/
  - grpc-java 1.72.0 jar 상수(`javap -constants`): `GrpcUtil.DEFAULT_MAX_MESSAGE_SIZE = 4194304`
- 실험 목록
  - 데드라인 없음 vs 500ms, 서버 `Context` 데드라인, 하류 자동 전파, 상태 코드(예외 → UNKNOWN, NOT_FOUND, FAILED_PRECONDITION, UNIMPLEMENTED), 4MiB 한도 — grpc-java 1.72.0, maven:3.9-eclipse-temurin-21(JDK 21.0.11), `--network none`, 루프백
  - 서비스 설정 `Map`의 숫자 타입(Double vs Integer) 수용 여부 — grpc-java 1.72.0
  - `pick_first` vs `round_robin` 분산 — Docker 사용자 네트워크, 서버 2대(eclipse-temurin:21-jdk, `--network-alias grpcsrv`), 클라이언트 1대
