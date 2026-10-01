# network/15-tcp-handshake-and-backlog — 정답

## 정답

### 1. 3-way handshake 그림

```text
  A (클라이언트)                                         B (서버)
  CLOSED                                                LISTEN
  SYN-SENT     --> <SEQ=100><CTL=SYN>              -->  SYN-RECEIVED
  ESTABLISHED  <-- <SEQ=300><ACK=101><CTL=SYN,ACK> <--  SYN-RECEIVED
  ESTABLISHED  --> <SEQ=101><ACK=301><CTL=ACK>      -->  ESTABLISHED
```

- SYN은 시퀀스 번호 하나를 차지한다. 그래서 A의 SYN(100)에 대한 ACK가 101이다.
- 두 번째 세그먼트가 "A의 SYN 확인"과 "B의 SYN"을 함께 싣는다(RFC 9293 Figure 6).

### 2. 왜 3번째 세그먼트가 필요한가

- RFC 9293 §3.5: 3-way handshake의 주된 이유는 **오래된 중복 연결 시작(SYN)이 혼란을 일으키지 않게** 하는 것이다.
- 예: 예전에 보낸 SYN(SEQ=90)이 네트워크에 늦게 도착한다.
  - 2-way라면 B는 이 SYN만 보고 연결을 확정해 버린다. A는 그런 연결을 원하지 않는다.
  - 3-way에서는 B가 SYN-ACK(ACK=91)를 보낸다. A는 "91은 내 현재 시도가 아니다"를 알고 RST를 보낸다. B는 LISTEN으로 돌아간다(Figure 8).
- 즉 3번째 세그먼트는 "이 SYN은 지금 내가 보낸 것이 맞다"는 클라이언트의 확인이다.

### 3. ISN을 이렇게 고르는 이유

1. **이전 연결과 섞이지 않게**: 같은 4-튜플로 연결을 다시 열 때, 옛 연결의 세그먼트가 아직 떠돌 수 있다. 시계 기반 ISN(약 4µs마다 증가, 약 4.55시간 주기)은 새 연결의 번호가 옛 번호와 겹칠 가능성을 줄인다(RFC 9293 §3.4.1, MUST-8).
2. **추측 공격 방지**: 경로 밖 공격자가 ISN을 맞히면 가짜 세그먼트를 끼워 넣을 수 있다. 그래서 (4-튜플, 비밀 키)의 의사난수 함수 값을 더하고(SHLD-1), 그 함수는 밖에서 계산할 수 없어야 한다(MUST-9).

### 4. 두 큐와 connect 성공의 의미

- **SYN 큐**: SYN을 받고 SYN-ACK를 보냈으며 마지막 ACK를 기다리는 요청이다(SYN-RECEIVED).
- **accept 큐**: 핸드셰이크가 끝나 `accept()`만 기다리는 연결이다(ESTABLISHED).
- 핸드셰이크는 서버 **커널**이 끝낸다. 클라이언트의 `connect()` 성공은 "서버 커널의 accept 큐에 들어갔다"는 뜻이다.
- 서버 애플리케이션은 아직 `accept()`하지 않았을 수 있다. 클라이언트가 보낸 요청은 커널 수신 버퍼에 쌓여 기다린다.

### 5. 실제 accept 큐 크기

- `new ServerSocket(8080)`의 기본 backlog는 **50**이다(Java SE API). 실제 크기 = min(50, 4096) = **50**.
- `listen(fd, 10000)`이면 somaxconn에서 조용히 깎여 **4096**이다(listen(2)).
- 교훈: "somaxconn을 올렸다"만으로는 부족하다. 애플리케이션이 준 backlog도 확인한다.

### 6. accept 큐가 찬 상태의 새 SYN

- 리눅스는 그 SYN을 **버린다**(RST로 거절하지 않는다). `ListenOverflows`·`ListenDrops` 카운터가 오른다.
- 클라이언트는 SYN-ACK를 못 받아 **SYN을 재전송**한다. 리눅스 6.5+ 기본값은 처음 5번 재전송이 1초 간격이라 connect가 1초, 2초, 3초씩 느려지고(6.5 이전은 1초, 3초, 7초), 끝내 connect 타임아웃이 날 수 있다.
- 서버 애플리케이션은 이 연결을 본 적이 없다. 버린 것은 커널이다. 그래서 앱 로그·앱 지표에는 아무것도 남지 않는다.
- 이미 3-way를 끝냈는데 accept 큐가 차서 마지막 ACK가 무시된 경우도 있다. 클라이언트는 ESTABLISHED라고 믿고, 서버는 나중에 SYN-ACK를 재전송한다.

### 7. 즉시 거절 vs 2분 멈춤

- (a) 즉시 `Connection refused`
  - 서버 호스트가 SYN에 **RST**로 답했다. 그 포트에 listen 소켓이 없다.
  - 리눅스는 SYN-SENT에서 RST를 받으면 `ECONNREFUSED`로 보고한다.
  - tcpdump: `[S]` → `[R.]`.
- (b) 2분쯤 멈춤
  - SYN에 **아무 응답이 없다**. 방화벽 DROP이거나 호스트가 꺼졌다.
  - 커널은 SYN을 `tcp_syn_retries`(기본 6)번 재전송한다(6.5+는 `tcp_syn_linear_timeouts` 4번이 더해져 10번). 초기 RTO는 1초다.
  - 6.5 이전: 간격 1, 2, 4, …, 64초 → 1 + 2 + … + 64 = **약 127초** 뒤 `ETIMEDOUT`(tcp(7) "approximately 127 seconds").
  - 6.5+: `tcp_syn_linear_timeouts`(기본 4)만큼 1초 간격을 더 둔 뒤 두 배 → 간격 1, 1, 1, 1, 1, 2, 4, …, 64초, **약 131초** 뒤 `ETIMEDOUT`(ip-sysctl `tcp_syn_retries`). 어느 쪽이든 "2분쯤"이다.
- 대처: 모든 클라이언트에 connect 타임아웃을 직접 건다.

### 8. accept 큐 넘침 확인

- `nstat -az TcpExtListenOverflows TcpExtListenDrops` — 피크 때 오르는지 본다.
- `ss -lnt 'sport = :8080'` — listen 소켓에서
  - **Recv-Q** = 지금 accept 큐에 쌓인 연결 수.
  - **Send-Q** = accept 큐 최대 크기(실제 backlog).
  - Recv-Q가 Send-Q에 붙어 있으면 넘치고 있다.
- 클라이언트 쪽 tcpdump에서 SYN 재전송을 확인하면 확정이다.

### 9. SYN cookie

- SYN 큐에 요청 상태를 **저장하지 않는다**.
- 필요한 정보(MSS 등)를 비밀 키 기반 해시와 섞어 SYN-ACK의 **시퀀스 번호**에 담는다.
- 클라이언트의 마지막 ACK의 확인 번호(= 그 시퀀스 번호 + 1)를 검증하고, 거기서 상태를 복원해 연결을 만든다(RFC 4987 §3.6).
- 대가: 담을 비트가 적어 일부 TCP 옵션(윈도 스케일·SACK 등) 정보를 잃을 수 있다. 리눅스는 타임스탬프를 쓰면 그 필드에 추가 정보를 담아 보완한다(Cloudflare).
- tcp(7)은 이것을 **최후 수단**이라 부른다. 프로토콜 위반이고 TCP 확장과 충돌할 수 있어서다. 과부하에는 `tcp_max_syn_backlog`·`tcp_synack_retries`·`tcp_abort_on_overflow` 같은 대안을 먼저 보라고 한다.

### 10. `tcp_abort_on_overflow`

- 꺼짐(기본): accept 큐가 차서 마지막 ACK를 못 받아들이면 그 ACK를 **무시**한다. 요청은 SYN 큐에 남고, 서버가 SYN-ACK를 재전송한다. 자리가 나면 연결이 완성된다.
- 켜짐: 대신 **RST**를 보낸다. 클라이언트는 `ECONNRESET`을 본다.
- 기본이 꺼짐인 이유: 넘침은 대개 짧은 버스트다. 무시하면 재전송으로 스스로 회복한다(tcp(7) "the connection will recover"). 켜면 잠깐의 버스트에도 연결이 에러로 끝나 클라이언트를 해칠 수 있다(tcp(7) 경고).
