# api-design/15-rpc-and-grpc — 정답

## 정답

### 1. 원격 호출에만 있는 결과

- **모름**이다. 요청이 갔는지, 처리됐는지, 응답만 잃었는지 알 수 없다.
- gRPC Core concepts
  - "클라이언트와 서버는 호출의 성공 여부를 각자 독립적으로, 국소적으로 판단하며, 그 결론은 다를 수 있다."
  - "취소 전에 일어난 변경은 롤백되지 않는다."
- 그래서 부작용 있는 호출은 재시도해도 안전하게(멱등 키) 만들고, 기다림의 한계(데드라인)를 직접 정해야 한다.

### 2. 단항 호출의 선 위 모양

```text
  HEADERS  :method POST  :path /exp.Exp/Slow  content-type application/grpc  grpc-timeout 498765u
  DATA     [압축 플래그 1B][길이 4B][protobuf 메시지]
  ── 응답 ──
  HEADERS  :status 200
  DATA     [0][길이][메시지]
  TRAILERS grpc-status 0  (grpc-message …)
```

- 결과는 트레일러의 `grpc-status`에 있다. gRPC 서버가 낸 응답은 gRPC 오류여도 HTTP 상태가 200이다(PROTOCOL-HTTP2.md: "a gRPC error response, which uses status 200 (OK)"). 200이 아닌 HTTP 상태는 대개 중간 프록시가 낸 것이다(6번).
- 그래서 HTTP 상태만 세는 지표는 gRPC 오류를 놓친다.

### 3. 데드라인 없음 vs 500ms (실험, grpc-java 1.72.0)

- (a) 3초가 지나도 `done=false` — 끝나지 않는다. gRPC 기본값은 데드라인 없음이다. 서버 로그 `grpc-timeout=null`, `Context deadline=없음`.
- (b) 513ms 뒤 `DEADLINE_EXCEEDED`(재실행 4회는 503~512ms).
  - 선 위: `grpc-timeout=498765u`(마이크로초 단위 남은 시간).
  - 서버 `Context`: `deadline=496ms 남음`. 시간이 지나자 서버 쪽에서 취소를 감지했다(원인 문구는 실행마다 `context timed out` 또는 `CANCELLED: RPC cancelled`).

### 4. 데드라인 전파

- 하류 호출의 `grpc-timeout=696105u`(≈ 1000 - 300 - 왕복). 서버 `Context`의 남은 시간이 하류 호출에 자동으로 실렸다(실험).
- 바깥 데드라인(1003ms)에 클라이언트는 `DEADLINE_EXCEEDED`로 끝났다. 서버 안의 하류 호출도 함께 끝났는데, 끝 상태는 실행마다 `CANCELLED`(집필 실행) 또는 `DEADLINE_EXCEEDED`(재실행 4회)였다 — 전파된 데드라인과 바깥 취소가 거의 같은 순간에 온다.
- 끊기는 경우: 하류 호출을 다른 스레드 풀·비동기 콜백으로 넘기면서 `Context`를 함께 넘기지 않을 때. gRPC Deadlines 가이드는 자동 전파를 "일부 구현이" 지원한다고 쓴다 — Java·Go는 기본으로 켜져 있고, C++ 등은 명시적으로 켜야 한다.

### 5. 상태 코드와 재시도

| 코드 | 재시도 |
|---|---|
| `UNAVAILABLE` | 실패한 그 호출만 다시 해도 된다 |
| `ABORTED` | 더 높은 수준(트랜잭션·읽기-수정-쓰기 전체)에서 다시 |
| `FAILED_PRECONDITION` | 시스템 상태를 고치기 전에는 다시 하지 않는다 |

- 도메인 예외를 그대로 던지면 `UNKNOWN(2)` + `Application error processing RPC`(실험). 예외 문구(`db password=...`)는 서버 로그에만 남는다.
- 정보가 새지 않는 대신 클라이언트는 무엇을 할지 모른다 → 인터셉터에서 도메인 예외를 의미 있는 코드로 사상한다.

### 6. HTTP → gRPC 매핑 표

- `grpc-status` 없이 HTTP 오류가 돌아왔을 때(중간 프록시가 낸 502·503 등) 클라이언트가 gRPC 코드로 해석하는 용도다.
- 서버가 gRPC 상태를 HTTP 상태로 만드는 데 쓰면 안 된다. 문서가 매핑이 다대일·비대칭이라 그 용도가 아니라고 적는다. `grpc-status`가 있으면 그것이 우선이다.

### 7. `pick_first` vs `round_robin` (실험)

- `pick_first`: `{srv-a=100}` — 연결 하나에 RPC 100개 전부.
- `round_robin`: `{srv-a=50, srv-b=50}`(집필 때 워밍업 뒤 3회 동일, 사실 점검 재실행에서는 `{srv-a=46, srv-b=54}`도 나왔다 — 두 서버에 퍼진다). 워밍업 없이는 `{srv-a=11, srv-b=89}`였다 — 두 번째 연결이 준비되기 전 호출이 한쪽으로 갔다.
- L4 LB는 연결을 나누므로 gRPC 클라이언트 하나의 트래픽이 서버 하나에 고정된다 — `pick_first`와 같은 모양이다. 해법은 요청 단위 분산(클라이언트 측 `round_robin` 또는 L7 프록시)과 서버 `MAX_CONNECTION_AGE`.

### 8. `DEADLINE_EXCEEDED` 재시도로 이중 승인

- `DEADLINE_EXCEEDED`는 "실패"가 아니라 "모름"이다. 서버는 승인을 끝냈는데 응답이 늦었을 수 있다. 취소 전 변경은 롤백되지 않는다.
- 막는 법: 요청에 멱등 키를 넣고, 서버가 키별 결과를 저장해 같은 키의 재시도에는 저장된 결과를 돌려준다. 재시도 정책의 대상 코드에서 `DEADLINE_EXCEEDED`를 빼거나 멱등 메서드에만 둔다.

### 9. 4MiB 한도

- grpc-java 1.72.0 기본 최대 수신 메시지 크기 4194304바이트(4MiB). 5000007바이트 응답이 `RESOURCE_EXHAUSTED`로 거부됐다(실험).
- 한도를 올리기 전에: 응답 크기가 데이터 양에 비례하지 않게 설계한다 — 페이지네이션(페이지 크기 상한 + 커서), 또는 서버 스트리밍으로 나눠 보내기(16번).

### 10. 서비스 설정의 숫자 타입

- 실험에서 `maxAttempts`와 `backoffMultiplier`를 모두 `Integer`(3, 2)로 넣으면 채널 생성 때 `IllegalArgumentException: The value of the map entry 'backoffMultiplier=2' is of type 'class java.lang.Integer', which is not supported`(실험). 문구의 항목 이름은 실행마다 `maxAttempts=3`일 수도 있다(`Map.of` 순회 순서). `Double`(`3.0`, `2.0`)로 넣어야 한다.
- 재시도 대상은 `UNAVAILABLE`처럼 "그 호출만 다시 해도 되는" 코드로 둔다. 부작용 있는 메서드는 멱등 키가 있을 때만 재시도한다.
- 재시도 정책이 없어도, 요청이 서버 애플리케이션 로직에 닿지 않은 경우에는 gRPC가 투명 재시도를 한다(gRPC Retry 가이드). 채널에서 재시도를 끄면 투명 재시도도 꺼진다.
