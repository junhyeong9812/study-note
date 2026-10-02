# reliability/07-timeout-taxonomy-by-layer — 정답

## 정답

### 1. 시간 조각과 타임아웃 이름

```text
 ① 풀 획득 대기   → 풀 acquire 타임아웃 (HikariCP connectionTimeout)
 ② DNS           → (대개 전체에만 포함)
 ③ TCP connect   → connect 타임아웃
 ④ TLS           → TLS 핸드셰이크 타임아웃 (Envoy·라이브러리에 따라 connect에 포함)
 ⑤ 요청 쓰기      → write 타임아웃
 ⑥ 첫 바이트      → response-header 타임아웃
 ⑦ 본문 읽기      → read(idle) 타임아웃 = 바이트 사이 간격
 ①~⑦ 전체        → call/total 타임아웃
```

- 새 연결일 때만: ②③④. 재사용 연결이면 건너뛴다.
- 호출 밖: 커넥션 idle 수명(놀고 있는 시간), 최대 수명(maxLifetime — 연결의 나이, 사용 중이면 반납될 때 닫음) — 풀의 연결을 언제 닫나.

### 2. SYN이 버려질 때

(실험, 커널 7.0, JDK 21.0.12)

- 2 → 7.2초, 3 → 19.7초, 5 → 68.2초에 `ConnectException: Connection timed out`.
- 이유: 처음 5번 간격은 1초(선형 4번 + 첫 지수 2^0), 그 뒤 2배씩이다. 포기는 재전송 수 ≥ `tcp_syn_retries + tcp_syn_linear_timeouts`이거나 경과 시간 ≥ `(2^(retries+1) - 1) × 1초`인 첫 타이머에서다(`tcp_timer.c`). tcpdump: 2일 때 SYN 6개(처음 + 재전송 5번)가 1초 간격으로 나가고 약 7초에 포기.
- 기본 6이면 계산상 마지막 재전송 67초, 포기 약 131초(직접 재지는 않았다. ip-sysctl `tcp_syn_retries` 설명·network/15와 같다).
- connect 타임아웃 1초: 세 경우 모두 1.0초에 `SocketTimeoutException: Connect timed out`.

### 3. slow drip

(실험)

- (a) 1초 간격보다 바이트가 자주 오므로 한 번도 안 터지고 약 6.0초 뒤 끝까지 받았다.
- (b) 응답 헤더는 바로 왔으므로 터지지 않고 6.15초(재실행 6.21초) 뒤 200으로 끝났다. 이 환경에서 요청 timeout은 헤더까지만 덮었다(헤더를 2초 늦춘 서버에는 1.0초에 `HttpTimeoutException`).
- (c) 헤더를 받은 뒤 본문을 읽는 도중 1.04초(재실행 1.03초)에 `TimeoutError`로 끊겼다. 신호가 본문 읽기까지 걸린다.

### 4. 같은 이름, 다른 뜻

- OkHttp `readTimeout`: 개별 읽기 연산의 상한(기본 10초).
- undici: 해당 개념은 `bodyTimeout` — 본문 청크 **사이** 간격(기본 300초). 헤더까지는 `headersTimeout`(기본 300초).
- JDK `HttpClient`: 읽기 타임아웃 설정이 따로 없다. 요청 `timeout`은 응답(헤더)까지.
- 전체 기본이 꺼진 것: JDK `HttpRequest.timeout`(미설정 = 무한), Go `DefaultClient`의 `Timeout`(0), OkHttp `callTimeout`(0).

### 5. Envoy

- cluster `connect_timeout`: 상류 TCP 연결 수립을 기다리는 시간. 상류가 TLS면 TLS 핸드셰이크를 포함. 기본 5초.
- route `timeout`: 하류(클라이언트) 요청을 **다 받은 뒤** 시작해 상류의 완전한 응답까지. 기본 15초. 스트리밍 응답에는 문제라 0으로 끄고 idle 타임아웃을 쓴다(Envoy FAQ).

### 6. 2초 타임아웃인데 30초

- 풀 획득 대기(①)를 의심한다. 호출 타임아웃은 연결을 받은 뒤부터 센다. 실제 지연 = 대기 + 호출.
- HikariCP `connectionTimeout` — 기본 30000ms(30초). 남은 예산 이하로 자른다. 풀이 마르는 원인(느린 쿼리·누수)을 먼저 찾는다.

### 7. 배포 직후만 나는 타임아웃

- 원인: 약 20ms 타임아웃의 타이머에 새 보안 연결(TLS) 수립이 들어 있었다. 연결은 재사용되므로 평소엔 문제없고, 새 서버 투입 직후 첫 요청들만 넘었다.
- 해결: 처음엔 새 연결을 맺는 경우 타임아웃을 늘렸고, 나중엔 트래픽을 받기 전 시작 단계에서 연결을 미리 맺었다.
- 일반화: 연결 수립 구간과 요청 구간의 상한을 나누고, 워밍업한다.

### 8. JDK `HttpClient`로 전체 3초

- `connectTimeout` + 요청 `timeout`(헤더까지)에 더해, 본문을 `ofInputStream`으로 받아 읽을 때마다 남은 시간을 검사한다. 또는 소켓 수준이면 실험 B의 (4)처럼 매번 `SO_TIMEOUT`을 `min(idle, 남은 전체)`로 줄인다.
- 빈틈: 검사는 `read()`가 돌아와야 실행된다. 바이트가 완전히 멈추면 `read()`에서 막혀 검사 코드에 닿지 못한다. 별도 타이머가 스트림·연결을 닫아 막힌 읽기를 깨워야 한다. 처음부터 전체 상한을 내장한 클라이언트(OkHttp `callTimeout`, Go `Client.Timeout`)를 쓰는 편이 쉽다.
