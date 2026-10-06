# network/15-tcp-handshake-and-backlog — 연결을 여는 3번의 인사, 그리고 accept 전에 줄 서는 두 개의 큐 — 정리 (힌트)

## 해결하는 문제

UDP는 바로 보낸다(14번).\
TCP는 데이터를 보내기 전에 양쪽이 먼저 합의해야 할 것이 있다.

```text
  합의할 것                              왜 필요한가
  "나는 시퀀스 번호 X부터 쓸게"            잃은 것·중복·순서를 번호로 가려내려면
  "너는 Y부터 쓴다는 것 확인했어"          양쪽 번호를 서로 알아야 한다
  "나는 한 세그먼트에 최대 M바이트 받아"     MSS·윈도 스케일 같은 옵션
  "지금 이 SYN은 옛날 것이 아니다"          오래 떠돌던 SYN이 새 연결을 만들면 안 된다
```

이 합의가 **3-way handshake**다.

그리고 서버 쪽에는 두 번째 문제가 있다.\
연결 요청은 애플리케이션이 `accept()`하기 **전에** 커널에 도착한다.\
그 사이 요청들은 어딘가에 줄을 서야 한다. 그 줄이 **SYN 큐와 accept 큐**다.

쉬운 예: 식당 입장이다.
- 손님이 "들어가도 돼요?"(SYN) → 직원 "네, 이름 적어 드릴게요"(SYN-ACK) → 손님 "네"(ACK). 이제 대기석에 앉는다.
- 대기석(accept 큐)에서 기다리다 홀 직원(`accept()`)이 자리로 안내한다.
- 대기석이 꽉 차면 문 앞 직원은 새 손님의 인사를 **못 들은 척**한다. 손님은 잠시 뒤 다시 인사한다.

똑같은 구조다.\
리눅스는 accept 큐가 차면 새 SYN을 거절하지 않고 **버린다**. 클라이언트는 재전송하느라 느려진다.

실무 예:
- 배포 직후 트래픽이 몰려 connect가 1초, 2초, 3초씩 걸린다(리눅스 6.5+ 클라이언트 기준, 아래 표). 서버 로그에는 아무것도 없다.
- 방화벽이 막은 포트로 connect하면 에러 없이 2분 넘게 멈춘다.
- 서버 프로세스가 죽은 포트로 connect하면 바로 `Connection refused`가 난다.

## 동작·원리

### 3-way handshake — 패킷 교환도

RFC 9293 Figure 6을 옮긴 것이다(시퀀스 번호는 RFC 예시값).

```text
      클라이언트 A                                        서버 B
  1.  CLOSED                                             LISTEN
  2.  SYN-SENT     --> <SEQ=100><CTL=SYN>             --> SYN-RECEIVED
  3.  ESTABLISHED  <-- <SEQ=300><ACK=101><CTL=SYN,ACK> <-- SYN-RECEIVED
  4.  ESTABLISHED  --> <SEQ=101><ACK=301><CTL=ACK>     --> ESTABLISHED
  5.  ESTABLISHED  --> <SEQ=101><ACK=301><CTL=ACK><DATA> --> ESTABLISHED
```

- 2: A가 "내 번호는 100부터"를 알린다. SYN은 시퀀스 번호 하나를 차지한다.
- 3: B가 "101을 기다린다"(A의 SYN 확인)와 "내 번호는 300부터"(B의 SYN)를 **한 세그먼트**에 담는다.
- 4: A가 B의 SYN을 확인한다(ACK=301).
- 5: 4와 5의 SEQ가 같다. ACK만 있는 세그먼트는 시퀀스 번호를 차지하지 않는다(RFC 9293 §3.5).

  - *SYN(synchronize)*: "내 시작 시퀀스 번호에 맞춰라"라는 제어 비트다.
  - *ISN(Initial Sequence Number)*: 연결의 첫 시퀀스 번호다. 위 예의 100과 300이다.

**왜 3번인가.**\
두 방향 각각 "내 번호 알림 + 상대 확인"이 필요하다. B의 확인과 B의 알림을 한 세그먼트로 합치면 3개가 된다.\
RFC 9293은 3-way handshake의 **주된 이유**를 "오래된 중복 SYN이 혼란을 일으키지 않게 하는 것"이라고 적는다(§3.5).

```text
  오래된 중복 SYN (RFC 9293 Figure 8 요약)
  A                                        B
  (예전에 보낸 SYN<SEQ=90>이 늦게 도착)  --> SYN-RECEIVED, SYN-ACK<ACK=91> 보냄
  A: "91? 난 그런 SYN 보낸 적 없는데"   <--
  A: RST<SEQ=91>                        --> B: LISTEN으로 돌아감
  (A의 진짜 SYN<SEQ=100>)               --> 정상 진행
```

- 2-way라면 B는 옛 SYN만 보고 연결을 열어 버린다.
- 3번째 세그먼트에서 A가 "이건 내 현재 연결이다"를 확인해 줘야 B가 확정한다.

**ISN은 왜 무작위에 가까운가.**
- ISN은 약 4마이크로초마다 1씩 오르는 32비트 "시계"를 바탕으로 한다(MUST-8, §3.4.1).
- 여기에 (주소·포트·비밀 키)의 의사난수 함수 값을 더하는 것을 권한다(SHLD-1). 그 함수는 밖에서 계산할 수 없어야 한다(MUST-9).
- 목적 두 가지
  - 같은 4-튜플의 이전 연결(incarnation)이 남긴 세그먼트와 번호가 겹치지 않게 한다.
  - 경로 밖 공격자가 번호를 추측해 가짜 세그먼트를 끼워 넣지 못하게 한다.

**SYN에서만 정하는 옵션.**
- MSS: "한 세그먼트에 받을 수 있는 최대 데이터". 기본값(IPv4 536, IPv6 1220)과 다르면 SYN에 실어야 한다(SHOULD, RFC 9293 §3.7.1).
- 윈도 스케일은 SYN 세그먼트에서만 보낸다(RFC 7323 §2.1). 한쪽이 안 보내면 이 연결 동안 쓸 수 없다(17번).
- SACK 허용·타임스탬프도 SYN에서 협상한다.

### 서버 쪽 — 두 개의 큐

```text
                              listen 소켓 (포트 8080)
  SYN 도착 --------------->  +--------------------------------------+
                             | SYN 큐 (half-open 요청들)               |  <- SYN-RECEIVED
    SYN-ACK 보냄 <---------- |  req(A)  req(C)  req(D) ...            |     SYN-ACK 재전송 담당
                             +--------------------------------------+
  마지막 ACK 도착 ---------->           | 완성되면 옮김
                             +--------------------------------------+
                             | accept 큐 (완성된 연결들, FIFO)          |  <- ESTABLISHED
                             |  conn(B)  conn(E) ...                  |
                             +--------------------------------------+
                                           | accept()
                                           v
                                      애플리케이션
```

- **SYN 큐**: SYN을 받았고 마지막 ACK를 기다리는 요청이다. SYN-ACK 재전송도 여기서 한다.
- **accept 큐**: 핸드셰이크가 끝나 `accept()`만 기다리는 연결이다.
- 핸드셰이크는 **커널이** 한다. 애플리케이션이 `accept()`를 부르지 않아도 연결은 ESTABLISHED가 된다.
- 그래서 클라이언트의 `connect()` 성공은 "서버 애플리케이션이 받았다"는 뜻이 아니다. "서버 커널의 accept 큐에 들어갔다"는 뜻이다.

(Cloudflare "SYN packet handling in the wild")

### backlog는 무엇의 크기인가

```text
  listen(fd, backlog)
     |
     v
  실제 accept 큐 크기 = min(backlog, net.core.somaxconn)
                         ^                 ^
                         앱이 준 값          넘으면 조용히 깎인다 (listen(2))

  SYN 큐 크기: net.ipv4.tcp_max_syn_backlog 등이 관여한다 (SYN cookie 켜지면 사실상 상한 없음)
```

- 리눅스 2.2부터 `backlog`는 **완성된 연결의 큐(accept 큐)** 길이다. 미완성 요청의 수가 아니다(listen(2)).
- `backlog`가 `somaxconn`보다 크면 조용히 `somaxconn`으로 깎인다. `somaxconn` 기본값은 리눅스 5.4부터 4096, 그 전에는 128이다(listen(2)).
- 미완성 요청(SYN 큐)의 최대 길이는 `tcp_max_syn_backlog`로 정한다. SYN cookie가 켜져 있으면 논리적 상한이 없다(listen(2)).
  - `tcp_max_syn_backlog`의 기본값은 문서마다 설명이 다르다. tcp(7)은 메모리에 따라 128·256·1024라고 적고, 커널 문서(ip-sysctl)는 "메모리에 비례"라고만 적는다. 작성 환경(Linux 7.0)에서는 4096이었다(예시).
  - 단, 현재 커널 코드에서 SYN cookie로 넘어가는 "SYN 큐 가득 참" 문턱은 `tcp_max_syn_backlog`가 아니라 listen 소켓의 min(backlog, somaxconn)이다. `tcp_max_syn_backlog`는 syncookies=0일 때 검증 안 된 상대의 SYN을 버리는 기준(3/4)에만 쓰인다(net/ipv4/tcp_input.c `tcp_conn_request`, `inet_csk_reqsk_queue_is_full`). 그래서 backlog가 작으면(Java 50) 작은 버스트에도 cookie 로그가 날 수 있다.
- 라이브러리·서버의 기본 backlog가 제각각이다.

| 무엇 | 기본 backlog | 근거 |
|---|---|---|
| Java `new ServerSocket(port)` | 50 | Java SE API 문서 |
| Node.js `server.listen()` | 511 | Node `net` 문서 |
| nginx `listen` (리눅스 등) | 511 | nginx `ngx_http_core_module` 문서 |
| Tomcat `acceptCount` | 100 | Tomcat HTTP Connector 문서 |

- Java 문서는 큐가 차면 "connection is refused"라고 적는다. 하지만 리눅스는 아래처럼 **버린다**. listen(2)도 "재전송을 지원하는 프로토콜이면 요청을 무시해 나중 재시도가 성공하게 할 수 있다"고 적는다.

### 큐가 가득 찼을 때 리눅스가 하는 일

```text
  accept 큐 가득 참 (앱이 accept를 못 따라감)
    새 SYN 도착        -> 버림 (ListenOverflows +1, ListenDrops +1)
                          클라이언트: SYN 재전송 (1초, 2초, 3초 ... 뒤; 6.5 이전은 1초, 3초, 7초 ...)   -> connect 지연
    마지막 ACK 도착     -> 무시 (tcp_abort_on_overflow=0, 기본)
                          서버: 나중에 SYN-ACK 재전송 -> 클라이언트 ACK 재전송 -> 자리 나면 완성
                          (tcp_abort_on_overflow=1이면 RST -> 클라이언트 ECONNRESET)

  SYN 큐 가득 참 (SYN flood 등)
    tcp_syncookies=1 (기본) -> SYN cookie로 상태 없이 SYN-ACK 응답
                               커널 로그: "Possible SYN flooding on port ... Sending cookies."
    tcp_syncookies=0        -> 요청 버림 ("... Dropping request.")
```

- accept 큐가 차면 SYN을 버리고 `LISTEN_OVERFLOWS` 카운터를 올린다(net/ipv4/tcp_input.c `tcp_conn_request`).
- 마지막 ACK가 왔는데 accept 큐가 차 있으면, 기본 설정에서는 그 ACK를 무시한다. 요청은 SYN 큐에 남는다(net/ipv4/tcp_minisocks.c `listen_overflow`).
- `tcp_abort_on_overflow`를 켜면 대신 RST를 보낸다. tcp(7)은 "클라이언트를 해칠 수 있으니 정말 확신할 때만 켜라"고 적는다.
- 버스트로 잠깐 넘친 것이면 재전송으로 결국 연결된다(tcp(7) `tcp_abort_on_overflow` 설명).

  - *SYN cookie*: SYN 큐에 상태를 저장하지 않고, 필요한 정보를 SYN-ACK의 시퀀스 번호에 암호학적으로 담는 기법이다. 마지막 ACK의 확인 번호로 상태를 복원한다(RFC 4987 §3.6).
    - 대가: 시퀀스 번호에 담을 자리가 좁아 일부 TCP 옵션을 잃을 수 있다(RFC 4987 §3.6). 리눅스는 타임스탬프 필드에 윈도 스케일·SACK 정보를 담아 보완한다(Cloudflare).
    - tcp(7)은 SYN cookie를 "최후 수단"이라 부르고, 과부하 서버의 튜닝 수단으로 쓰지 말라고 적는다.

### 클라이언트 쪽 — connect가 끝나는 세 가지 방법

```text
  connect() 결과              무슨 일이 있었나                              errno / 예외
  -------------------------   ------------------------------------------   ------------------------------
  성공                         SYN-ACK 받고 ACK 보냄 (서버 accept 큐에 들어감)   0
  즉시 실패                    서버 호스트가 RST로 응답 (그 포트에 listen 없음)   ECONNREFUSED
                                                                              Java ConnectException "Connection refused"
  오래 멈췄다 실패              SYN에 아무 응답 없음 (방화벽 DROP·호스트 다운)     ETIMEDOUT
                              -> SYN 재전송 tcp_syn_retries(기본 6)번 (+ 6.5+는 선형 4번)   Java ConnectException "timed out"
                              -> 약 131초 뒤 포기 (6.5+ 기본, ip-sysctl) / 6.5 이전 약 127초 (tcp(7))
```

- 없는 포트로 온 SYN에 커널은 RST로 답한다(RFC 9293 §3.5.2, 연결 없는 상태의 규칙).
- SYN-SENT 상태에서 RST를 받으면 리눅스는 에러를 `ECONNREFUSED`로 정한다(net/ipv4/tcp_input.c `tcp_reset`).
- SYN 재전송 간격은 커널 버전에 따라 다르다. 초기 RTO는 1초다(RFC 6298 §2.1).
  - 6.5 이전: 매번 두 배(RFC 6298 §5.5). 1, 2, 4, …, 64초 → 1 + 2 + … + 64 = 약 127초. tcp(7)의 "약 127초"는 이 값이다.
  - 6.5+: `tcp_syn_linear_timeouts`(기본 4)만큼 1초 간격을 유지한 뒤 두 배. 1, 1, 1, 1, 1, 2, 4, …, 64초 → 마지막 재전송 약 67초, 실패 약 131초(ip-sysctl `tcp_syn_retries`·`tcp_syn_linear_timeouts`). 작성 환경(Linux 7.0)은 4였다.
  - 서버의 SYN-ACK 재전송에는 선형 설정이 적용되지 않는다(ip-sysctl).
- 그래서 **connect 타임아웃을 직접 걸지 않으면** 방화벽에 막힌 호출 하나가 2분 넘게 스레드를 잡는다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블(SYN 큐)** — 마지막 ACK가 오면 4-튜플로 해당 요청을 찾아야 한다. 이름은 "큐"지만 조회는 해시다. 현재 리눅스는 요청(request sock)을 연결 해시 테이블(ehash)에 넣는다(net/ipv4/inet_connection_sock.c `reqsk_queue_hash_req` → `inet_ehash_insert`). tcp(7)도 예전 SYNACK 해시 테이블(`TCP_SYNQ_HSIZE`)을 언급한다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **FIFO 큐(accept 큐)** — 완성된 연결이 들어온 순서대로 `accept()`된다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **SYN cookie = 상태를 암호학적 토큰으로 바꾸기** — 서버가 기억하지 않고 클라이언트에게 들려 보낸 뒤, 돌아올 때 검증한다. 무상태 서버의 CSRF 토큰·서명 쿠키와 같은 발상이다.
- **의사난수 함수(ISN)** — `ISN = M + F(4-튜플, 비밀 키)`. F는 암호 해시로 구현할 수 있다(RFC 9293 §3.4.1).
- **지수 백오프** — SYN·SYN-ACK 재전송 간격을 두 배씩 늘린다(리눅스 6.5+ SYN은 처음 4번 선형 뒤 지수).
- **상태 기계** — CLOSED → SYN-SENT → ESTABLISHED(능동), LISTEN → SYN-RECEIVED → ESTABLISHED(수동). 동시 open이면 양쪽 다 SYN-SENT → SYN-RECEIVED → ESTABLISHED(RFC 9293 Figure 7).

## 적용 — 풀어나가는 법

### 1. 클라이언트: connect 타임아웃을 반드시 건다

Java — `connect(addr, timeout)`. 타임아웃 0은 무한이다(Java SE API).

```java
Socket s = new Socket();
try {
    s.connect(new InetSocketAddress(host, 8080), 3_000);   // 3초(예시). 0이면 무한 대기
} catch (ConnectException e) {
    // "Connection refused" = RST를 받았다. 서버 프로세스가 없거나 포트가 틀렸다. 빨리 실패
} catch (SocketTimeoutException e) {
    // 응답 없음 = 방화벽 DROP·호스트 다운·accept 큐 넘침. 재시도 정책으로 넘긴다
}
```

Node.js — `net.connect`의 `timeout` 옵션은 유휴 타임아웃(`socket.setTimeout`)이다. 시간이 지나면 `'timeout'` 이벤트만 내고 연결은 끊지 않는다(Node `net` 문서). 그래서 직접 끊는다.

```js
const net = require('node:net');
function connectWithTimeout(port, host, ms) {
  return new Promise((resolve, reject) => {
    const sock = net.connect({ port, host });
    const t = setTimeout(() => sock.destroy(new Error('connect timeout')), ms);
    sock.once('connect', () => { clearTimeout(t); resolve(sock); });
    sock.once('error', (err) => { clearTimeout(t); reject(err); }); // err.code === 'ECONNREFUSED' 등
  });
}
```

C — 논블로킹 connect에 poll로 시간 제한을 둔다.

```c
fcntl(fd, F_SETFL, O_NONBLOCK);
if (connect(fd, (struct sockaddr *)&addr, sizeof addr) < 0 && errno == EINPROGRESS) {
    struct pollfd p = { .fd = fd, .events = POLLOUT };
    if (poll(&p, 1, 3000) == 0) { /* 3초(예시) 타임아웃 */ }
    int err; socklen_t len = sizeof err;
    getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &len);   /* 0 = 성공, ECONNREFUSED 등 */
}
```

- 논블로킹 connect는 `EINPROGRESS`를 돌려주고, 쓰기 가능이 되면 `SO_ERROR`로 결과를 확인한다(connect(2)).

### 2. 서버: backlog와 accept 속도를 맞춘다

- 트래픽이 몰리는 서버는 backlog를 명시적으로 준다. `somaxconn`도 그 이상인지 확인한다.
- 근본은 accept 속도다. accept 스레드가 막히면(동기 작업, GC 멈춤) 큐가 찬다.
- 큐를 무작정 키우면 대기 시간만 길어진다. 클라이언트 타임아웃보다 오래 기다린 연결은 받아도 쓸모가 없다.

### 3. 진단 명령

```bash
# listen 소켓: Recv-Q = 지금 accept 큐에 있는 수, Send-Q = accept 큐 최대 크기(backlog)
ss -lnt 'sport = :8080'
#   State   Recv-Q  Send-Q   Local Address:Port
#   LISTEN  0       4096     0.0.0.0:8080          (값은 예시)

# accept 큐 넘침·SYN 드롭·SYN cookie 누적 카운터
nstat -az TcpExtListenOverflows TcpExtListenDrops TcpExtSyncookiesSent TcpExtTCPReqQFullDoCookies

# 핸드셰이크 중인 연결 (서버 SYN-RECV / 클라이언트 SYN-SENT)
ss -tan state syn-recv
ss -tan state syn-sent

# SYN·SYN-ACK·RST만 잡기
tcpdump -ni any 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0 and port 8080'

# 관련 커널 값
sysctl net.core.somaxconn net.ipv4.tcp_max_syn_backlog net.ipv4.tcp_syncookies \
       net.ipv4.tcp_syn_retries net.ipv4.tcp_synack_retries net.ipv4.tcp_abort_on_overflow
```

- listen 소켓에서 `ss`의 Recv-Q·Send-Q 뜻은 일반 소켓과 다르다(Cloudflare).
- tcpdump에서 같은 SYN이 반복되면 응답이 없는 것이다(드롭). 간격은 6.5+ 기본 1·1·1·1·1·2·4초…, 6.5 이전 1·2·4초…다.

## 장애 시나리오와 대처

### 1. 포트 닫힘 → `ECONNREFUSED`

- **현상**: 호출이 **즉시** 실패한다.
- **보이는 형태**
  - Java `java.net.ConnectException: Connection refused`, Node `Error: connect ECONNREFUSED 10.0.0.9:8080`.
  - tcpdump: `[S]` 다음 곧바로 `[R.]`.
- **원인**
  - 서버 호스트는 살아 있는데 그 포트에 listen 소켓이 없다(프로세스 다운·재시작 중·포트 오타·`127.0.0.1`에만 bind).
  - 또는 방화벽이 REJECT로 응답했다. iptables REJECT의 기본 응답은 ICMP port unreachable이고(`--reject-with tcp-reset`이면 RST, iptables-extensions(8)), 리눅스는 이 ICMP를 `ECONNREFUSED`로 바꾼다(net/ipv4/icmp.c `icmp_err_convert`). 이때 tcpdump에는 `[R.]` 대신 ICMP `port unreachable`이 보인다.
- **대처**
  - `ss -lnt`로 서버가 어느 주소·포트에 listen하는지 확인한다(`0.0.0.0`인지 `127.0.0.1`인지).
  - 배포 중 순간 거절이면 LB의 헬스 체크·드레이닝을 맞춘다.
  - 즉시 실패는 빠르다. 짧은 백오프 재시도가 통한다.

### 2. 방화벽 DROP → SYN 재전송 뒤 `ETIMEDOUT`

- **현상**: 호출이 오래 멈췄다가 실패한다. 타임아웃을 안 걸었으면 약 2분이다.
- **보이는 형태**
  - `ss -tan state syn-sent`에 연결이 머문다.
  - tcpdump에 같은 SYN이 반복되고 응답이 없다. 간격은 6.5+ 기본 1·1·1·1·1·2·4…초, 6.5 이전 1·2·4·8…초다.
  - 결국 `ETIMEDOUT`(Java `ConnectException: Connection timed out` — OpenJDK `Net.c`, connect 타임아웃을 걸었으면 `SocketTimeoutException`).
- **원인**: SYN이 방화벽·보안 그룹에서 조용히 버려지거나, 대상 호스트가 꺼져 있다. RST가 없으니 커널은 `tcp_syn_retries`(기본 6)번 재전송한다(6.5+는 선형 4번이 더해져 약 131초, 이전은 약 127초).
- **대처**
  - 모든 클라이언트에 connect 타임아웃을 건다(수 초 이내).
  - 보안 그룹·방화벽 규칙과 라우팅을 확인한다.
  - 스레드 풀이 이 대기로 고갈되지 않게 한다.

### 3. accept 큐 넘침 → 서버 로그 없이 connect가 느려진다

- **현상**: 트래픽 피크·배포 직후 connect가 1초, 2초, 3초씩 걸린다(6.5 이전 클라이언트는 1초, 3초, 7초). 일부는 connect 타임아웃이다. 서버 애플리케이션 로그에는 아무것도 없다.
- **보이는 형태**
  - `nstat`의 `TcpExtListenOverflows`·`TcpExtListenDrops`가 오른다.
  - `ss -lnt`에서 Recv-Q가 Send-Q에 붙어 있다.
  - 클라이언트 쪽 tcpdump에 SYN 재전송이 보인다.
- **원인**
  - 애플리케이션의 `accept()` 속도가 연결 도착 속도를 못 따라간다(스레드 고갈, 이벤트 루프 막힘, GC 멈춤).
  - backlog가 작다(Java 기본 50, `somaxconn` 제한).
  - 리눅스는 이때 SYN을 **버린다**. 거절(RST)이 아니라서 클라이언트는 재전송하느라 늦어진다.
- **대처**
  - accept 루프를 가볍게 한다. 받은 연결의 처리는 워커로 넘긴다.
  - backlog를 명시하고 `somaxconn`을 확인한다.
  - 이 카운터에 경보를 건다. 애플리케이션 지표에는 안 보이는 장애다.
  - 인스턴스를 늘리거나 LB에서 연결 수를 제한한다.

### 4. SYN flood — SYN 큐가 가득 참

- **현상**: 정상 사용자의 연결이 느리거나 실패한다. 서버 CPU는 여유가 있다.
- **보이는 형태**
  - 커널 로그: `TCP: request_sock_TCP: Possible SYN flooding on port <주소>:<포트>. Sending cookies.` 형태다. `TCP: `는 tcp_input.c의 `pr_fmt`, `request_sock_TCP`는 request sock 슬랩 이름이다(net/ipv4/tcp_input.c `tcp_syn_flood_action`, 현재 master 기준).
  - `ss -tan state syn-recv` 개수가 폭증한다.
  - `TcpExtSyncookiesSent`가 오른다.
- **원인**: 위조 출발지로 SYN만 대량으로 보내 SYN 큐를 채운다. 마지막 ACK는 오지 않는다(RFC 4987).
- **대처**
  - `tcp_syncookies=1`(기본)을 유지한다. SYN cookie가 SYN 큐 없이 응답한다.
  - `tcp_synack_retries`를 줄여 가짜 요청이 큐에 머무는 시간을 줄인다(tcp(7)이 제시하는 대안 중 하나).
  - 대규모 공격은 망 앞단(DDoS 방어 서비스)에서 막는다(security/28).

### 5. `tcp_abort_on_overflow=1` → 클라이언트가 `Connection reset`

- **현상**: 피크 때 클라이언트가 connect 직후 첫 요청에서 `ECONNRESET`을 본다.
- **보이는 형태**: 서버 쪽 tcpdump에 3-way 직후 서버가 보낸 RST.
- **원인**: accept 큐가 넘칠 때 ACK를 무시하는 대신 RST를 보내도록 설정했다. 버스트로 잠깐 넘친 연결까지 모두 끊긴다(tcp(7) 경고).
- **대처**: 특별한 이유가 없으면 끈다(기본값 0). accept 속도·backlog 문제를 고친다.

## 핵심 문장

- 3-way handshake는 양쪽 ISN을 서로 확인하는 절차다. 3번째 세그먼트가 있어야 **오래된 중복 SYN**이 연결을 만들지 못한다.
- 핸드셰이크는 커널이 끝낸다. 연결은 SYN 큐(미완성) → accept 큐(완성)를 거쳐 `accept()`를 기다린다. `connect()` 성공은 "서버 앱이 받았다"가 아니다.
- `backlog`는 accept 큐 크기이고 `somaxconn`에서 조용히 깎인다. 리눅스는 큐가 차면 SYN을 **버린다**. 그래서 거절이 아니라 **지연**으로 보이고, 서버 로그에는 없다(`ListenOverflows`).
- RST가 오면 `ECONNREFUSED`로 즉시 실패하고, 응답이 없으면 SYN 재전송 끝에 약 2분(6.5+ 약 131초, 이전 약 127초) 뒤 `ETIMEDOUT`이다. connect 타임아웃은 직접 건다.
- SYN flood에는 SYN cookie가 상태 없이 응답한다. 대신 일부 옵션을 잃을 수 있는 최후 수단이다.

## 관련 주제·근거

- 선행: [14-udp](../14-udp/2-summary.md) — 연결 없는 전송과의 대비
- 후속·연결
  - [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — 시퀀스 번호·RTO·재전송.
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — SYN에서 정한 윈도 스케일.
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — 여는 것의 반대편, RST 생성 규칙
  - [23-socket-api](../23-socket-api/2-summary.md) — listen·accept·connect 시스템 콜.
  - [13-routing-protocols-ospf-bgp](../13-routing-protocols-ospf-bgp/2-summary.md) — BGP 세션도 TCP 179 위의 핸드셰이크로 시작한다
  - [security/28-dos-and-abuse](../../security/28-dos-and-abuse/2-summary.md) — SYN flood
  - [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md)(connect 타임아웃의 자리)
- RFC
  - RFC 9293 TCP <https://www.rfc-editor.org/rfc/rfc9293>
    - §3.4.1 ISN — 4µs 시계(MUST-8), PRF(SHLD-1), 외부 계산 불가(MUST-9)
    - §3.5 3-way handshake — Figure 6(기본), Figure 7(동시 open), Figure 8(오래된 중복 SYN), "principal reason"
    - §3.5.2 RST 생성 규칙 · §3.7.1 MSS 옵션(기본 536/1220, SHLD-5)
  - RFC 7323 §2.1 윈도 스케일은 SYN에서만 <https://www.rfc-editor.org/rfc/rfc7323>
  - RFC 6298 §2.1 초기 RTO 1초, §5.5 백오프 <https://www.rfc-editor.org/rfc/rfc6298>
  - RFC 4987 TCP SYN Flooding Attacks and Common Mitigations — §3.6 SYN cookie <https://www.rfc-editor.org/rfc/rfc4987>
- Linux
  - listen(2) — backlog = 완성 연결 큐, somaxconn(5.4+ 4096), tcp_max_syn_backlog <https://man7.org/linux/man-pages/man2/listen.2.html>
  - connect(2) — `ECONNREFUSED`, `ETIMEDOUT`, `EINPROGRESS` <https://man7.org/linux/man-pages/man2/connect.2.html>
  - tcp(7) — `tcp_syn_retries`(6, 약 127초 — 6.5 이전 커널 기준), `tcp_synack_retries`(5), `tcp_syncookies`, `tcp_abort_on_overflow`, `tcp_max_syn_backlog` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - Kernel docs ip-sysctl — `somaxconn`(4096), `tcp_max_syn_backlog`, `tcp_syn_retries`(67초·131초), `tcp_syn_linear_timeouts`(기본 4, 6.5+) <https://docs.kernel.org/networking/ip-sysctl.html>
  - net/ipv4/tcp_input.c — `tcp_syn_flood_action`, `tcp_conn_request`(LISTEN_OVERFLOWS), `tcp_reset`(SYN-SENT → ECONNREFUSED) · net/ipv4/tcp_minisocks.c `listen_overflow` <https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_input.c>
- Cloudflare, "SYN packet handling in the wild" — 두 큐, `ss -lnt`의 Recv-Q/Send-Q, ListenOverflows <https://blog.cloudflare.com/syn-packet-handling-in-the-wild/>
- 라이브러리 기본값
  - Java SE `ServerSocket`(backlog 50), `Socket.connect(addr, timeout)`(0 = 무한) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/ServerSocket.html>
  - Node.js `net` — `server.listen` backlog 511 <https://nodejs.org/api/net.html>
  - nginx `ngx_http_core_module` `listen` — backlog 511(리눅스 등) <https://nginx.org/en/docs/http/ngx_http_core_module.html#listen>
  - Apache Tomcat HTTP Connector — `acceptCount` 100 <https://tomcat.apache.org/tomcat-10.1-doc/config/http.html>
- Stevens, 『TCP/IP Illustrated Vol.1』 2판 13장 "TCP Connection Management"
