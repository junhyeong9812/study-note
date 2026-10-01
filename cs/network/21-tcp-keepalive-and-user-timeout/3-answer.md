# network/21-tcp-keepalive-and-user-timeout — 정답

## 정답

### 1. probe에 대한 세 가지 결과

```text
  (a) 살아 있음    probe -->   <-- ACK      타이머 리셋, 앱은 아무것도 모름
  (b) 재부팅됨     probe -->   <-- RST      연결 종료, 앱: ECONNRESET
  (c) 경로 단절    probe --X   (KEEPINTVL마다 KEEPCNT번 반복)
                                           연결 종료, 앱: ETIMEDOUT
```

- probe는 보통 `SEG.SEQ = SND.NXT − 1`로 보낸다. 상대가 이미 받은 번호라 상대는 ACK로 답한다(RFC 1122 §4.2.3.6).
- (b)는 연결 정보가 없는 쪽이 RST로 답하는 규칙 때문이다(RFC 9293 §3.5.2).

### 2. RFC의 keepalive 규칙

- 구현 여부는 선택이다(MAY-5).
- 구현하면 연결별로 켜고 끌 수 있어야 하고(MUST-24), **기본은 꺼짐**(MUST-25).
- 보낸 데이터가 대기 중이 아니고, 일정 시간 데이터·ACK를 받지 않았을 때만 보낸다(MUST-26).
- 간격은 설정 가능해야 하고(MUST-27), 기본값은 **2시간 이상**(MUST-28).
- probe 하나의 무응답을 사망으로 해석하면 **안 된다**(MUST-29). 데이터 없는 ACK는 신뢰성 있게 전달되지 않기 때문이다(RFC 9293 §3.8.4).

### 3. 리눅스 기본값의 탐지 시간

```text
  tcp_keepalive_time 7200초 + tcp_keepalive_intvl 75초 × tcp_keepalive_probes 9
  = 7200 + 675 = 7875초 ≈ 2시간 11분
```

- tcp(7)도 "idle 2시간 뒤 약 11분 더(75초 간격 9번)"라고 적는다.
- `SO_KEEPALIVE`를 켠 소켓에만 적용된다.

### 4. NLB 뒤 idle 연결의 `ECONNRESET`

- AWS NLB는 TCP 연결이 idle timeout(기본 350초) 동안 조용하면 추적을 멈춘다. 그 뒤 보낸 데이터에는 RST가 돌아온다(AWS 문서).
- 리눅스 기본 keepalive는 첫 probe가 7200초 뒤다. 350초 안에 probe가 한 번도 나가지 않아 NLB 기록이 사라졌다.
- 대처
  - `TCP_KEEPIDLE`을 350초보다 짧게(예: 60~120초 (예시)) 둔다. keepalive 패킷은 NLB의 idle 타이머를 다시 시작시킨다(AWS 문서).
  - 풀의 idle 연결 폐기 시간을 350초보다 짧게 둔다.
  - 멱등 요청은 한 번 재시도한다.

### 5. 전원이 나간 상대에게 `write()`

- `write()`는 **성공**한다. 데이터를 내 커널 송신 버퍼에 넣었을 뿐이다.
- 커널은 전송하고, ACK가 없으니 지수 백오프로 재전송한다. 상대는 전원이 꺼져 RST도 못 보낸다.
- **keepalive는 동작하지 않는다.** 보낸 데이터가 대기 중이면 probe를 보내지 않는다(MUST-26). 리눅스는 이때 재전송 타이머가 돈다.
- `tcp_retries2`(기본 15)로 계산한 가상 시간을 넘긴 첫 RTO에서 `ETIMEDOUT`이다(15는 고정 횟수가 아니다 — RTO가 크면 재전송은 더 적다). 커널 문서 기준 하한 약 924.6초(약 15분), tcp(7) 기준 약 13~30분이다.
- 앱이 `read()`로 응답을 기다리고 있었다면 그때 `ETIMEDOUT`을 받는다.

### 6. `TCP_USER_TIMEOUT`

- 재는 것(tcp(7))
  - 보낸 데이터가 **ACK 없이 남아 있는 시간**
  - 또는 zero window 때문에 버퍼 데이터를 **보내지 못한 시간**
- 이 시간이 값(ms)을 넘으면 커널이 연결을 강제로 닫고 `ETIMEDOUT`을 준다.
- 재전송 시점이나 keepalive probe 시점은 **바꾸지 않는다.** 포기 시점만 바꾼다.
- `SO_KEEPALIVE`와 함께 쓰면 keepalive 실패로 연결을 닫는 시점도 이 값이 결정한다(override).
- 동기화된 상태에서만 효과가 있고, 리스닝 소켓에 걸면 accept한 소켓이 물려받는다.
- Cloudflare는 `KEEPIDLE + KEEPINTVL × KEEPCNT`에 맞추라고 권한다.

### 7. keepalive로 못 잡는 경우

- **상대 앱이 멈춤**: 교착·무한 GC로 앱은 멈췄지만 상대 커널은 살아 있어 probe에 ACK한다.
- **L7 프록시·TLS 종단 너머의 단절**: keepalive는 가장 가까운 TCP 종단(프록시)까지만 확인한다. 프록시와 업스트림 사이가 끊겨도 모른다.
- 이 둘은 앱 수준 heartbeat(요청-응답)나 "마지막 메시지 후 N초 무소식이면 재연결" 같은 수신 타임아웃으로 잡는다.

### 8. 프로토콜별 heartbeat

- HTTP/2: PING 프레임(type 0x6). 최소 RTT 측정과 idle 연결 동작 확인에 쓴다(RFC 9113 §6.7).
- gRPC: HTTP/2 PING 기반 keepalive. 클라이언트 기본 꺼짐, 서버 기본 2시간, PING 응답 대기 기본 20초. 서버 허용 최소 간격(기본 5분)보다 자주 보내면 서버가 `too_many_pings` GOAWAY로 연결을 끊는다(gRPC keepalive 가이드).
- WebSocket: Ping 프레임(opcode 0x9)을 받으면 Pong(0xA)으로 답해야 한다(MUST, RFC 6455 §5.5.2). Ping은 keepalive로도, 응답성 확인으로도 쓸 수 있다.

### 9. user timeout이 너무 짧을 때

- 원인: user timeout은 "ACK 없이 버틸 시간"이다. 경로의 RTO 백오프 몇 번(수 초)보다 짧으면, 곧 복구될 일시적 유실까지 연결 사망으로 판정한다.
- 기준
  - 경로의 RTT·RTO와, 서비스가 허용할 수 있는 최대 단절 시간을 같이 본다.
  - tcp(7): 줄이면 fail fast, 늘리면 긴 단절도 버틴다.
  - keepalive와 함께 쓰면 `KEEPIDLE + KEEPINTVL × KEEPCNT`(Cloudflare)를 출발점으로 삼는다.
  - RFC 5482 §4.2는 UTO 옵션을 쓰는 연결에서는 keepalive 타이머를 user timeout보다 크게 두라고 한다(MUST). 구현마다 keepalive 중단 정책이 달라 멀쩡한 연결을 끊을 수 있기 때문이다.

### 10. Java·Node 설정

- Java(JDK 11+)
  - `socket.setKeepAlive(true)`로 `SO_KEEPALIVE`를 켠다.
  - `socket.setOption(ExtendedSocketOptions.TCP_KEEPIDLE, 초)`, `TCP_KEEPINTERVAL`, `TCP_KEEPCOUNT`로 세부 값을 정한다(`jdk.net.ExtendedSocketOptions`).
  - JDK에는 `TCP_USER_TIMEOUT`이 없다(Java SE 21 문서). 필요하면 Netty epoll 전송의 `EpollChannelOption.TCP_USER_TIMEOUT`을 쓰거나, 앱 수준 요청 타임아웃으로 대신한다.
- Node
  - `socket.setKeepAlive(true, initialDelayMs)` 또는 `net.connect({ keepAlive: true, keepAliveInitialDelay })`.
  - v13.12/v12.17부터 keepalive를 켜면 `TCP_KEEPCNT=10`, `TCP_KEEPINTVL=1초`를 기본으로 설정한다. 최신 문서에는 `interval`·`count` 인자도 있다(v26.4.0 추가).
  - 밀리초로 받지만 커널에는 초로 내림해 넣는다.
