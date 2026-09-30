# network/52-network-symptom-index — 에러 코드 사전: 증상(errno·예외·DNS 코드·TLS alert·HTTP 5xx) → 원인 leaf — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

네트워크 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"TIME-WAIT가 쌓이면 → `EADDRNOTAVAIL`이 난다"처럼 쓴다.\
그런데 장애 현장에서는 반대 방향이 필요하다.\
로그에 `ECONNRESET` 한 줄이 찍혔다. 이게 어느 노트의 이야기인지부터 찾아야 한다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                     이 노트 (역방향)
  원인 --> 메커니즘 --> 증상              증상 --> 층 --> 흔한 원인 --> 첫 명령 --> leaf 노트
  "NAT idle timeout이면 RST가 온다"       "ECONNRESET이 떴다. 후보는 셋이다. tcpdump로 RST 방향부터"
```

쉬운 예: 병원 접수처의 증상표다.\
"기침 + 열"이면 호흡기내과, "기침 + 가슴 통증"이면 순환기내과로 보낸다.\
접수처는 병을 고치지 않는다. **어느 과로 보낼지**만 정한다.

똑같은 구조다.\
`ECONNRESET` + "한동안 쉬었던 연결의 첫 요청" → 커넥션 관리(35번)로 보낸다.\
`ECONNRESET` + "배포 직후" → 종료·드레이닝 문제로 보낸다.

실무 예:
- 같은 증상이 런타임마다 **다른 이름**으로 보인다. 커널의 `ECONNREFUSED`는 Java에서 `ConnectException: Connection refused`, Node에서 `connect ECONNREFUSED`다.
- 이름이 같아도 **단계**가 다르면 뜻이 다르다. connect 중의 `ETIMEDOUT`은 SYN에 답이 없었다는 뜻이다. 연결이 선 뒤의 `ETIMEDOUT`은 재전송이 끝내 확인받지 못했거나, keepalive 탐침에 끝내 답이 없었다는 뜻이다.
- 에러가 **없는** 증상도 있다. 느림, 큰 응답만 멈춤, 200인데 잘린 본문이 그렇다.

## 동작·원리

### 0. 증상이 올라오는 길 — 어느 층이 만든 말인가

```text
  +--------------------------------------------------------------+
  | 애플리케이션 로그   "호출 실패" (원문을 버리면 여기서 끝)           |
  +--------------------------------------------------------------+
  | 런타임 번역         Java 예외 / Node err.code / curl 코드         |
  +--------------------------------------------------------------+
  | L7 프로토콜         HTTP 5xx  |  TLS alert  |  DNS RCODE          |
  |                    (프록시가 만든다) (TLS 라이브러리) (리졸버가 답한다) |
  +--------------------------------------------------------------+
  | libc / 시스템콜     errno: ECONNRESET, EPIPE, ETIMEDOUT ...     |
  |                    getaddrinfo: EAI_NONAME, EAI_AGAIN ...       |
  +--------------------------------------------------------------+
  | 커널 TCP/IP         RST 수신, 재전송 포기, ICMP 수신, 포트 고갈    |
  +--------------------------------------------------------------+
  | 경로               방화벽 DROP/REJECT, NAT 매핑 삭제, 경로 없음    |
  +--------------------------------------------------------------+
```

- 아래층 사건이 위층 이름으로 **번역**되어 올라온다. 번역하면서 정보가 줄어든다.
- 그래서 색인을 쓰기 전에 두 가지를 확보한다.
  - **원문**: 예외 타입, 메시지, cause 체인 끝, Node의 `code`·`syscall`.
  - **맥락**: 어느 단계(connect / 읽기 / 쓰기)였나, 실패까지 **얼마나 걸렸나**.

  - *errno*: 시스템콜이 실패했을 때 이유를 담는 정수다. 이름(`ECONNRESET`)과 문자열("Connection reset by peer")이 붙는다(errno(3)).
  - *RCODE*: DNS 응답 헤더의 결과 코드 4비트다(RFC 1035 §4.1.1).
  - *TLS alert*: TLS가 실패·종료 이유를 상대에게 알리는 1바이트 코드다(RFC 8446 §6).

### 1. 같은 증상, 다른 이름 — 번역표

리눅스 번호와 문자열은 이 노트 작성 환경(Linux, Python `errno`/`os.strerror`)에서 확인한 값이다. 번호는 OS마다 다르다.

| errno | 리눅스 번호 · 문자열 | Java (JDK NIO 소켓 구현) | Node `err.code` |
|---|---|---|---|
| `ECONNREFUSED` | 111 · Connection refused | `ConnectException` | `ECONNREFUSED` |
| `ETIMEDOUT` | 110 · Connection timed out | connect 중: `ConnectException`(앱 connect 타임아웃이 먼저 끝나면 `SocketTimeoutException: Connect timed out`) | `ETIMEDOUT` |
| `EHOSTUNREACH` | 113 · No route to host | `NoRouteToHostException` | `EHOSTUNREACH` |
| `EADDRNOTAVAIL` | 99 · Cannot assign requested address | `BindException` | `EADDRNOTAVAIL` |
| `EADDRINUSE` | 98 · Address already in use | `BindException` | `EADDRINUSE` |
| `ECONNRESET` | 104 · Connection reset by peer | 읽기: `SocketException: Connection reset` / 쓰기: `SocketException: Connection reset by peer` | `ECONNRESET` |
| `EPIPE` | 32 · Broken pipe | 쓰기: `SocketException: Broken pipe` | `EPIPE` |
| `EMFILE` | 24 · Too many open files | `socket()`: `SocketException: Too many open files` / `accept()`: `IOException: Too many open files` | `EMFILE` |

- Java 열의 근거는 OpenJDK `Net.c`의 `handleSocketErrorWithMessage`다.
  - `ECONNREFUSED`·`ETIMEDOUT`·`ENOTCONN` → `ConnectException`
  - `EHOSTUNREACH` → `NoRouteToHostException`
  - `EADDRINUSE`·`EADDRNOTAVAIL`·`EACCES` → `BindException`
  - `EPROTO` → `ProtocolException`, 나머지 → `SocketException`
  - 이 함수를 거치는 것은 `socket()`·`connect()`·`bind()` 같은 호출이다. `accept()` 실패는 `Net.c`가 errno 문자열로 `IOException`을 바로 던진다.
- 읽기 쪽은 `SocketDispatcher.c`가 `ECONNRESET`·`EPIPE`를 `ConnectionResetException`으로 바꾸고, `NioSocketImpl`이 이를 `SocketException("Connection reset")`으로 다시 던진다.
- 쓰기 쪽은 `IOUtil.c`의 `convertReturnVal`이 errno 문자열("Broken pipe", "Connection reset by peer")로 `IOException`을 만들고, `NioSocketImpl`이 같은 메시지의 `SocketException`으로 바꾼다(`asSocketException`).
- 이것은 `java.net.Socket`이 NIO 기반 구현을 쓰는 JDK(JEP 353, JDK 13부터)의 경로다. JDK 8 같은 옛 구현은 매핑이 다를 수 있다 [?].
- Node는 시스템 에러의 errno 이름을 `err.code` 문자열로 그대로 싣는다. Node `errors` 문서 "Common system errors" 목록에는 `EADDRINUSE`·`ECONNREFUSED`·`ECONNRESET`·`EMFILE`·`EPIPE`·`ETIMEDOUT`·`ENOTFOUND`가 있다. `EHOSTUNREACH`·`EADDRNOTAVAIL`은 그 목록에 없고 errno 이름 규칙을 따른 것이다. `ECONNREFUSED`·`ENOTFOUND`는 이 노트 작성 환경(Node 18)에서 재현했다.

### 2. 연결 수립(connect) 단계의 증상

```text
  클라이언트 SYN --->  ?
                      |
     +----------------+-----------------+------------------+-------------------+
     | 즉시 RST         | 아무 답 없음       | ICMP unreachable  | SYN을 내보내지도 못함   |
     v                 v                  v                  v
  ECONNREFUSED      ETIMEDOUT          port -> ECONNREFUSED EADDRNOTAVAIL
  (ms 단위)          (약 2분, 기본값)    host -> EHOSTUNREACH (내 쪽 임시 포트 고갈)
                                       net  -> ENETUNREACH
```

| 증상 | 층 | 흔한 원인 | 첫 명령 | leaf |
|---|---|---|---|---|
| `ECONNREFUSED` 즉시 | 전송 | 그 포트에 listen 없음, `127.0.0.1`에만 bind, 방화벽 REJECT(기본은 ICMP port unreachable, `tcp-reset`이면 RST) | 서버에서 `ss -ltnp`, 양쪽 `tcpdump`로 `[R.]` 또는 ICMP `port unreachable` 확인(필터에 `icmp`도 넣는다) | [15](../15-tcp-handshake-and-backlog/2-summary.md) · [48](../48-firewalls-and-network-policy/2-summary.md) · [23](../23-socket-api/2-summary.md) |
| connect `ETIMEDOUT`(수십 초~약 2분) | 경로·전송 | 방화벽·보안 그룹 DROP, 대상 꺼짐, 비대칭 경로, conntrack 표 가득, SNAT 포트 고갈 | `ss -tan state syn-sent`, `tcpdump`에서 SYN 재전송, `dmesg`의 `nf_conntrack: table full` | [15](../15-tcp-handshake-and-backlog/2-summary.md) · [48](../48-firewalls-and-network-policy/2-summary.md) · [11](../11-nat-and-conntrack/2-summary.md) · [08](../08-routing-and-longest-prefix-match/2-summary.md) |
| connect가 초 단위 계단으로 느림(6.5+ 기본 1·2·3·4·5·7초…, 이전 커널 1·3·7초…) | 전송 | SYN·SYN-ACK 유실, accept 큐 넘침(새 SYN을 버림) | 서버 `nstat`의 `TcpExtListenOverflows`, `ss -lnt`의 Recv-Q | [15](../15-tcp-handshake-and-backlog/2-summary.md) · [16](../16-tcp-reliability-retransmission/2-summary.md) |
| `EHOSTUNREACH` / `No route to host` | 네트워크 | 같은 링크에서 ARP 실패, 원격 라우터의 ICMP host unreachable·prohibited, `unreachable` 타입 경로 | `ip route get <목적지>`, `ip neigh` | [01](../01-layer-map-osi-tcpip/2-summary.md) · [08](../08-routing-and-longest-prefix-match/2-summary.md) · [05](../05-arp/2-summary.md) · [26](../26-packet-journey/2-summary.md) |
| `ENETUNREACH` | 네트워크 | 내 라우팅 테이블에 경로 자체가 없음(기본 경로 없음), 원격 라우터의 ICMP net unreachable | `ip route` | [01](../01-layer-map-osi-tcpip/2-summary.md) · [08](../08-routing-and-longest-prefix-match/2-summary.md) |
| `EADDRNOTAVAIL` (connect) | 내 호스트 | 임시 포트 범위 소진 — 대개 요청마다 새 연결 + TIME-WAIT | `ss -tan state time-wait \| wc -l`, `sysctl net.ipv4.ip_local_port_range` | [20](../20-time-wait-and-close-wait/2-summary.md) · [35](../35-http-connection-management/2-summary.md) |
| `EADDRNOTAVAIL` (bind) | 내 호스트 | 이 호스트에 없는 주소로 bind(오타, 옮겨 간 VIP) | `ip -br addr` | [23](../23-socket-api/2-summary.md) |
| `EADDRINUSE` (bind/listen) | 내 호스트 | 옛 연결이 TIME-WAIT, `SO_REUSEADDR` 없음, 또는 다른 프로세스가 LISTEN 중 | `ss -ltnp 'sport = :8080'` | [20](../20-time-wait-and-close-wait/2-summary.md) · [23](../23-socket-api/2-summary.md) |

- `ECONNREFUSED`: connect(2)는 "no one listening on the remote address"라고 적는다.
- connect의 `EADDRNOTAVAIL`: connect(2)는 "bind되지 않은 소켓에 임시 포트를 붙이려 했는데 임시 포트 범위의 포트가 모두 사용 중"이라고 적는다. bind의 `EADDRNOTAVAIL`은 "로컬이 아닌 주소"다(bind(2), ip(7)). **같은 errno, 다른 원인**이다.
- `EHOSTUNREACH`: ip(7)은 "맞는 라우팅 항목이 없음. 원격 라우터의 ICMP나 로컬 라우팅 테이블 때문일 수 있다"고 적는다.
  - 리눅스에서 로컬 경로가 아예 없으면 `ENETUNREACH`다(작성 환경에서 기본 경로가 없는 IPv6로 재현). 로컬 원인의 `EHOSTUNREACH`는 `unreachable` 타입 경로(ip-route(8), `fib_semantics.c`의 `RTN_UNREACHABLE` → `-EHOSTUNREACH`)나 이웃 해석 실패다.
  - ICMP는 종류에 따라 갈린다. port unreachable → `ECONNREFUSED`, net unreachable → `ENETUNREACH`, host unreachable·prohibited → `EHOSTUNREACH`(01번, `net/ipv4/icmp.c` `icmp_err_convert[]`).
- listen(2)는 큐가 가득 차면 `ECONNREFUSED`를 받거나 요청이 무시될 수 있다고 쓴다. **리눅스는 기본으로 무시 쪽**이라 클라이언트는 refused를 보지 않는다(15·23번).
  - 새 SYN이 오면 버린다(`tcp_conn_request`). 클라이언트는 느린 connect를 본다.
  - 핸드셰이크 마지막 ACK가 오면, 기본(`tcp_abort_on_overflow=0`)에서는 그 ACK를 버린다(`tcp_minisocks.c` `listen_overflow`). 클라이언트의 connect는 이미 **성공**했다. 서버가 SYN-ACK를 재전송(`tcp_synack_retries`)하는 동안 첫 요청이 지연된다.
  - `tcp_abort_on_overflow=1`이면 이 두 번째 경우에 RST를 보낸다(→ `ECONNRESET`).
- "약 2분"은 리눅스 `tcp_syn_retries` 기본 6에서 나온다(15번). 앱의 connect 타임아웃이 있으면 그 값에서 끝난다.
  - 6.5+ 기본(`tcp_syn_linear_timeouts=4`): SYN RTO가 1, 1, 1, 1, 1, 2, 4, …초다. 마지막 재전송 약 67초, 실패 약 131초(ip-sysctl). 작성 환경(Linux 7.0)에서 약 134초 뒤 `ETIMEDOUT`이 관찰됐다.
  - 6.5 이전: 1, 2, 4, …초로 두 배씩 늘어 약 127초(tcp(7)).

### 3. 연결 중(읽기·쓰기) 단계의 증상

```text
  상대(또는 중간 장비)가 보낸 것     내 read()                  내 write()
  ---------------------------   -----------------------   -----------------------------------
  FIN                           0 (EOF, Java -1)           아직 가능
  RST                           ECONNRESET                 리눅스: 첫 쓰기 ECONNRESET,
                                                            다음부터 EPIPE (+SIGPIPE)
  아무것도 없음 (half-open)        계속 대기 (타임아웃 없으면)    버퍼에 들어가면 "성공",
                                                            약 15분+ 뒤 ETIMEDOUT
```

- 이 표는 19번 노트의 표와 같은 내용이다. 에러 순서는 **구현 의존**이다.
- 이 노트 작성 환경(Linux, Python 소켓)에서 상대가 `SO_LINGER {1, 0}`으로 RST를 보내게 한 뒤 재현했다.
  - 첫 `send()` → `ECONNRESET`, 두 번째 `send()` → `EPIPE`.
  - `recv()` → `ECONNRESET`.
- 보류된 `ECONNRESET`(`sk_err`)은 먼저 호출한 쪽이 한 번만 꺼내 간다. `read()`나 `getsockopt(SO_ERROR)`가 먼저 가져갔다면 첫 쓰기부터 `EPIPE`다(19번, socket(7) `SO_ERROR`).
- CLOSE-WAIT(상대 FIN을 이미 받음) 상태에서 RST가 오면 리눅스는 `EPIPE`를 저장한다(`tcp_reset`). 이때도 첫 쓰기부터 `EPIPE`다. FIN만 받은 상태의 쓰기는 성공한다.

| 증상 | 층 | 흔한 원인 | 첫 명령 | leaf |
|---|---|---|---|---|
| `ECONNRESET` — 쉬었던 풀 연결의 첫 요청 | 전송(경로 장비가 원인일 수 있음) | 서버·LB의 keep-alive가 먼저 닫음(idle close 경합), NAT·LB idle timeout 뒤 RST | `tcpdump`로 **RST 방향과 직전 패킷**, 양쪽 idle timeout 표 | [35](../35-http-connection-management/2-summary.md) · [19](../19-tcp-termination-fin-rst-half-open/2-summary.md) · [11](../11-nat-and-conntrack/2-summary.md) · [21](../21-tcp-keepalive-and-user-timeout/2-summary.md) |
| `ECONNRESET` — 요청 본문 전송 중·직후 | 응용 | 서버가 본문을 다 읽지 않고 close, 크기 한도 초과 뒤 끊음 | 서버 로그의 413·한도, `curl -v` | [19](../19-tcp-termination-fin-rst-half-open/2-summary.md) · [42](../42-large-file-upload-patterns/2-summary.md) |
| `ECONNRESET` — connect 직후 첫 요청(피크 때) | 전송 | `tcp_abort_on_overflow=1`이 accept 큐 넘침에 RST | 서버 `sysctl net.ipv4.tcp_abort_on_overflow` | [15](../15-tcp-handshake-and-backlog/2-summary.md) |
| `EPIPE` / "Broken pipe", 네이티브 프로세스가 로그 없이 종료(종료 코드 141) | 전송·프로세스 | 닫힌(RST 받은·`shutdown` 한) 소켓에 쓰기 → `SIGPIPE` 기본 동작 = 종료 | 셸 종료 코드, `strace -e trace=network,signal` | [19](../19-tcp-termination-fin-rst-half-open/2-summary.md) |
| 데이터 전송 중 `ETIMEDOUT`(약 15분 이상 뒤) | 전송 | 상대가 조용히 사라짐(전원·방화벽 DROP·NAT 삭제), 재전송이 `tcp_retries2` 한도 도달 | `ss -tio`의 `timer:(on,…,N)`, `nstat`의 `TcpExtTCPAbortOnTimeout` | [16](../16-tcp-reliability-retransmission/2-summary.md) · [21](../21-tcp-keepalive-and-user-timeout/2-summary.md) · [19](../19-tcp-termination-fin-rst-half-open/2-summary.md) |
| 보낼 것 없던 idle 연결의 `ETIMEDOUT` | 전송 | `SO_KEEPALIVE` 탐침이 모두 무응답(리눅스 기본 7200 + 9 × 75초 ≈ 2시간 11분, tcp(7)) — 상대가 사라짐 | `ss -tio`의 `timer:(keepalive,…)` | [21](../21-tcp-keepalive-and-user-timeout/2-summary.md) |
| 에러 없이 멈춤, 연결은 ESTABLISHED | 전송·응용 | half-open(보낼 것이 없어 RST 받을 기회 없음), zero window(상대 앱이 안 읽음) | `ss -tno`의 Send-Q·Recv-Q·`timer:(persist…)`, 스레드 덤프 | [19](../19-tcp-termination-fin-rst-half-open/2-summary.md) · [17](../17-tcp-flow-control/2-summary.md) · [21](../21-tcp-keepalive-and-user-timeout/2-summary.md) |
| `ETIMEDOUT`로 수 초 만에 끊김 | 전송 | `TCP_USER_TIMEOUT`이 RTO 백오프보다 짧게 설정됨 | 소켓 옵션 설정 코드 | [21](../21-tcp-keepalive-and-user-timeout/2-summary.md) |
| Node `socket hang up`(`code: 'ECONNRESET'`) | 응용(HTTP 클라이언트) | 응답을 받기 전에 연결이 닫힘 — 대개 idle close 경합 | 서버 keep-alive timeout vs 클라이언트 idle | [35](../35-http-connection-management/2-summary.md) |

- tcp(7)의 `ETIMEDOUT`: "상대가 재전송된 데이터를 일정 시간 확인하지 않았다".
- send(2)의 `EPIPE`: "로컬 끝이 이미 닫힌 연결형 소켓. `MSG_NOSIGNAL`이 없으면 `SIGPIPE`도 받는다".
- JVM과 Node는 `SIGPIPE`를 무시하도록 설정해 두므로 프로세스가 죽지 않고 예외·에러로 받는다(19번).

### 4. 자원 고갈 증상

| 증상 | 층 | 흔한 원인 | 첫 명령 | leaf |
|---|---|---|---|---|
| `EMFILE` "Too many open files"(`accept`·`socket`) | 프로세스 | fd 누수(CLOSE-WAIT가 함께 쌓임), `RLIMIT_NOFILE`이 작음 | `ls /proc/<pid>/fd \| wc -l`, `ss -tanp state close-wait` | [20](../20-time-wait-and-close-wait/2-summary.md) · [23](../23-socket-api/2-summary.md) |
| `ENFILE` "Too many open files in system" | 커널 전체 | `/proc/sys/fs/file-max` 한도(errno(3)) | `cat /proc/sys/fs/file-nr` | [23](../23-socket-api/2-summary.md) |
| `nf_conntrack: table full, dropping packet` | 커널(넷필터) | 짧은 연결 폭증, 긴 상태 타임아웃 | `conntrack -S`, `sysctl net.netfilter.nf_conntrack_count` | [11](../11-nat-and-conntrack/2-summary.md) |
| `neighbor table overflow` | 커널(이웃 표) | 큰 평면 L2망, `gc_thresh3` 초과 | `ip neigh \| wc -l` | [05](../05-arp/2-summary.md) |
| AWS NAT `ErrorPortAllocation` > 0 | NAT | 한 목적지로의 동시 연결 상한 | 클라우드 지표, 연결 재사용 여부 | [11](../11-nat-and-conntrack/2-summary.md) |
| `Timeout waiting for connection from pool` | 응용(풀) | 응답 미반납 누수, 호스트당 한도 작음, 상류 느림 | 풀 지표(leased·pending), 스레드 덤프 | [35](../35-http-connection-management/2-summary.md) |

- errno(3): `EMFILE`은 흔히 `RLIMIT_NOFILE` 초과, `ENFILE`은 리눅스에서 `file-max` 한도다.
- 이 노트 작성 환경에서 `RLIMIT_NOFILE`을 20으로 줄인 뒤 소켓을 계속 만들어 `EMFILE`을 재현했다.

### 5. DNS 증상

```text
  앱이 "이름을 못 찾았다"
          |
          v
  같은 호스트에서 dig <이름>  --> status: 는?
          |
    +-----+--------------+---------------------+-------------------------+
    | NXDOMAIN            | NOERROR, 그 타입 답 없음 | SERVFAIL                  | 응답 없음 (timed out)
    v                     v                       v                           v
  이름이 없다            이름은 있는데 그 타입       리졸버가 답을 못 만들었다       리졸버에 못 닿음
  (오타·부정 캐시·        레코드가 없다(NODATA)     (권한 서버 불통·위임 오류·     (egress 차단·
   ndots 검색 목록)       (AAAA만 없음 등)          DNSSEC 검증 실패)             resolv.conf 오류)
```

| 증상 | 뜻 | 흔한 원인 | 첫 명령 | leaf |
|---|---|---|---|---|
| `status: NXDOMAIN` | 그 이름이 없다(RCODE 3) | 오타, 레코드 생성 전 조회가 **부정 캐시**됨, 검색 도메인이 붙은 이름 | `dig <이름>`의 AUTHORITY 절 SOA, `dig @<권한 NS> <이름>` | [27](../27-dns-resolution/2-summary.md) · [28](../28-dns-caching-and-ttl/2-summary.md) |
| `status: SERVFAIL` | 서버가 처리하지 못했다(RCODE 2) | 권한 서버 전부 불통, lame delegation, DNSSEC bogus | `dig +trace`, `dig @<각 NS> +norecurse`, 응답의 `EDE:` 줄 | [27](../27-dns-resolution/2-summary.md) · [28](../28-dns-caching-and-ttl/2-summary.md) · [13](../13-routing-protocols-ospf-bgp/2-summary.md) |
| `NOERROR` + 요청 타입 답 없음 (NODATA) | 이름은 있고 그 타입이 없다 | A는 있는데 AAAA 없음, TXT 없음 | `dig <이름> <타입>`, AUTHORITY 절의 SOA | [28](../28-dns-caching-and-ttl/2-summary.md) |
| `status: REFUSED` | 정책상 거부(RCODE 5) | 그 리졸버가 이 클라이언트의 재귀 질의를 받지 않음 | 다른 리졸버와 비교 | [27](../27-dns-resolution/2-summary.md) |
| `connection timed out; no servers could be reached` | 리졸버 불통 | egress 정책에 53 누락, `resolv.conf` 비었음 | `cat /etc/resolv.conf`, `dig @<리졸버>` | [27](../27-dns-resolution/2-summary.md) · [48](../48-firewalls-and-network-policy/2-summary.md) |
| 큰 응답만 실패, `dig +tcp`만 실패 | TC 비트 뒤 TCP 재시도 실패 | TCP 53 차단 | `dig +tcp <이름>` | [27](../27-dns-resolution/2-summary.md) · [10](../10-fragmentation-mtu-pmtud/2-summary.md) |

앱에서 보이는 이름:

| 런타임 | 보이는 형태 | 비고 |
|---|---|---|
| glibc `getaddrinfo` | `EAI_NONAME`("Name or service not known"), `EAI_NODATA`("No address associated with hostname"), `EAI_AGAIN`(일시 실패) | getaddrinfo(3): `EAI_AGAIN` = "네임 서버가 일시 실패를 알림" |
| Java | `UnknownHostException` 하나로 모인다 | NXDOMAIN·SERVFAIL·리졸버 불통을 구분하지 못한다(27번). 원인은 같은 호스트의 `dig`로 가른다 |
| Node `dns.lookup`(기본 경로) | `ENOTFOUND`, `EAI_AGAIN` | `ENOTFOUND`는 `EAI_NONAME`·`EAI_NODATA`에서 나온다(Node `errors` 문서) |
| Node `dns.resolve*` | `ENOTFOUND`, `ESERVFAIL` 등(`dns.NOTFOUND`, `dns.SERVFAIL` 상수) | 작성 환경(Node 18)에서 NXDOMAIN → `ENOTFOUND`, SERVFAIL(`dnssec-failed.org` @1.1.1.1) → `ESERVFAIL` 확인 |
| curl | `(6) Could not resolve host` | |

- glibc의 DNS 경로(nss_dns)에서는 SERVFAIL이 `TRY_AGAIN`을 거쳐 `EAI_AGAIN`으로 올라온다(glibc `resolv/res_query.c`의 `case SERVFAIL: ... TRY_AGAIN`, `nss/getaddrinfo.c`의 `TRY_AGAIN` → `EAI_AGAIN`). 27·28·48번도 같은 대응을 쓴다.
- 작성 환경에서 `dig @1.1.1.1 dnssec-failed.org`는 `SERVFAIL`과 `EDE: 9 (DNSKEY Missing)`을 돌려줬다. EDE(RFC 8914)가 있으면 SERVFAIL의 이유를 좁힐 수 있다.

  - *부정 캐시(negative caching)*: "없다"는 답도 정해진 시간 동안 캐시하는 것이다(RFC 2308).
  - *NODATA*: RCODE는 NOERROR인데 answer 절에 요청한 타입의 답이 없는 응답이다. 별도 RCODE가 아니다(RFC 2308 §2.2).
    - answer 절에 CNAME만 있어도 NODATA일 수 있다.
    - `+norecurse`로 권한 서버에 물을 때 오는 referral도 NOERROR·ANSWER 0이다. AUTHORITY 절에 SOA가 있으면 NODATA, NS만 있으면 referral이다(RFC 2308 §2.2).

### 6. TLS 증상

```text
  누가 alert를 보냈나?
    서버가 보냄   --> 서버가 내 제안(버전·암호군·SNI·ALPN·클라이언트 인증서)을 거절
    클라이언트가 보냄 --> 클라이언트가 서버의 응답을 거절 (서버 인증서가 가장 흔하다.
                         파라미터 선택·Finished 검증 실패일 수도 있다: RFC 8446)
  alert 이름은 힌트일 뿐이다. 구현마다 고르는 alert가 다르다 (29번)
```

| alert (번호, RFC 8446 §6) | 흔한 원인 | 클라이언트에서 보이는 형태 예 | 첫 명령 | leaf |
|---|---|---|---|---|
| `handshake_failure`(40) | 공통 암호군·그룹·서명 알고리즘 없음 | Java `SSLHandshakeException: Received fatal alert: handshake_failure` | `openssl s_client -tls1_2 -cipher …` / `-tls1_3 -ciphersuites …` | [29](../29-tls-handshake/2-summary.md) |
| `protocol_version`(70) | 버전 하한 불일치(옛 클라이언트) | `Received fatal alert: protocol_version` | `openssl s_client -tls1_2` / `-tls1_3` | [29](../29-tls-handshake/2-summary.md) |
| `unknown_ca`(48) · 발급자 못 찾음 | 중간 인증서 누락, 사설 CA 미등록, 트러스트스토어 교체 | Java `PKIX path building failed`, OpenSSL `unable to get local issuer certificate`, Node `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` | `openssl s_client -showcerts` (체인 장 수) | [30](../30-x509-and-chain-validation/2-summary.md) |
| `certificate_expired`(45) | 리프 갱신 누락, 중간·교차 서명 루트 만료, 클라이언트 시계 | OpenSSL `certificate has expired`, Node `CERT_HAS_EXPIRED` | `openssl x509 -noout -dates`, `date -u` | [30](../30-x509-and-chain-validation/2-summary.md) · [32](../32-mtls-and-cert-operations/2-summary.md) · [53](../53-network-incidents/2-summary.md) |
| (alert 전) 이름 불일치 | SAN에 이름 없음, SNI 누락으로 기본 인증서 | Java `No subject alternative DNS name matching`, Node `ERR_TLS_CERT_ALTNAME_INVALID` | `openssl s_client -servername <이름>` vs `-noservername` | [29](../29-tls-handshake/2-summary.md) · [30](../30-x509-and-chain-validation/2-summary.md) |
| `unrecognized_name`(112) | SNI의 이름에 맞는 가상 호스트 없음 | `alert unrecognized name` | `openssl s_client -servername` | [29](../29-tls-handshake/2-summary.md) |
| `no_application_protocol`(120) | ALPN 목록이 안 겹침(`h2` 미광고) | gRPC 연결 직후 실패 | `openssl s_client -alpn h2` 를 홉마다 | [29](../29-tls-handshake/2-summary.md) · [36](../36-http2-multiplexing/2-summary.md) |
| `certificate_required`(116) | mTLS에서 클라이언트 인증서 미제시 | 첫 읽기·쓰기에서 에러가 날 수 있음 | `openssl s_client -cert … -key …` | [32](../32-mtls-and-cert-operations/2-summary.md) |
| `bad_certificate`(42) · `unsupported_certificate`(43) | 클라이언트 인증서의 EKU·체인 문제 | OpenSSL `unsuitable certificate purpose` | `openssl x509 -noout -ext extendedKeyUsage` | [32](../32-mtls-and-cert-operations/2-summary.md) |
| alert 없이 핸드셰이크가 멈춤 | 인증서 체인이 담긴 큰 세그먼트가 PMTUD 블랙홀에 빠짐 | `curl -v`가 핸드셰이크 중간에서 멈춤 | `ping -M do -s <크기>` | [10](../10-fragmentation-mtu-pmtud/2-summary.md) · [26](../26-packet-journey/2-summary.md) |

- 인증서 폐기·CT 쪽 증상(OCSP 응답기 장애, Must-Staple, SCT 부족)은 [31](../31-revocation-ocsp-ct/2-summary.md)에 모여 있다.

### 7. HTTP 5xx — 누가 만든 5xx인가

```text
  클라이언트 --> [CDN] --> [LB / 리버스 프록시] --> [앱 서버] --> [DB·외부 API]
                  |              |                     |
               502/504         502/503/504            5xx (앱이 직접)
               (원점 문제)      (상류 문제를 대신 알림)

  502 Bad Gateway      상류에서 **잘못된 응답**을 받았다 (연결 거부·도중 끊김·깨진 응답)
  503 Service Unavail. 지금 처리할 수 없다 (과부하·점검, 또는 건강한 대상 없음)
  504 Gateway Timeout  상류에서 **제때 응답**을 받지 못했다
```

- RFC 9110 정의: 502는 게이트웨이·프록시가 상류에서 **invalid response**를 받았다(§15.6.3). 503은 일시 과부하·점검으로 처리할 수 없다(§15.6.4). 504는 상류에서 **timely response**를 받지 못했다(§15.6.5).

| 증상 | 흔한 원인 | 첫 확인 | leaf |
|---|---|---|---|
| 502 + nginx `connect() failed (111: Connection refused) while connecting to upstream` | 상류 프로세스 다운·재시작·포트 틀림 | 상류에서 `ss -ltnp` | [33](../33-http-semantics/2-summary.md) · [15](../15-tcp-handshake-and-backlog/2-summary.md) |
| 502 + `upstream prematurely closed connection` / `recv() failed (104: Connection reset by peer)` | 상류가 keep-alive를 LB보다 먼저 닫음(idle close 경합), 상류 크래시 | 구간별 idle timeout 표 | [35](../35-http-connection-management/2-summary.md) · [19](../19-tcp-termination-fin-rst-half-open/2-summary.md) |
| 502 + `no live upstreams` | 모든 상류가 실패로 표시됨 | 헬스체크·`max_fails` | [33](../33-http-semantics/2-summary.md) |
| 503 | 앱이 스스로 과부하·점검 응답, LB에 건강한 대상 없음 | LB 대상 상태, 헬스체크 로그 | [33](../33-http-semantics/2-summary.md) · [LB 원고](../../systems/server-design/02-request-path.md) |
| 504 + `upstream timed out (110: Connection timed out) while reading response header from upstream` | 상류 처리가 느림(느린 쿼리·외부 호출), 타임아웃 값 불일치 | 상류 처리 시간 vs `proxy_read_timeout` | [33](../33-http-semantics/2-summary.md) · [35](../35-http-connection-management/2-summary.md) |
| CDN 502/504 급증 직후 원점 부하 폭증 | 전체 퍼지·동시 만료로 원점 스탬피드 | CDN 미스율, 원점 요청 수 | [47](../47-cdn-and-edge/2-summary.md) |
| 200인데 본문이 잘림, curl `(18)` | 헤더를 보낸 뒤 서버 오류(상태 코드는 이미 확정) | 액세스 로그의 보낸 바이트 | [40](../40-chunked-and-streaming-responses/2-summary.md) |

- nginx 에러 로그 문자열의 근거는 nginx 소스(`ngx_http_upstream.c`의 `"upstream timed out"`·`"upstream prematurely closed connection"`·`"no live upstreams"`, `"connect() failed"`, 그리고 `src/os/unix/ngx_recv.c`의 `"recv() failed"`)다. 상류 타임아웃은 504, 나머지 상류 실패는 대개 502로 끝난다(`ngx_http_upstream_next`).
- 괄호 속 숫자는 리눅스 errno 번호다. 110 = `ETIMEDOUT`, 111 = `ECONNREFUSED`, 104 = `ECONNRESET`. **5xx 로그 안에 전송 계층 증상이 들어 있다.**
- AWS ALB는 LB가 만든 5xx(`HTTPCode_ELB_5XX_Count`)와 대상이 만든 5xx(`HTTPCode_Target_5XX_Count`)를 따로 센다(33번).

### 8. 에러가 없는 증상 — 조용한 실패

| 증상 | 흔한 원인 | 첫 확인 | leaf |
|---|---|---|---|
| 작은 요청은 되고 큰 응답·업로드·TLS 인증서 단계만 멈춤 | PMTUD 블랙홀(ICMP 차단 + 터널 MTU) | 같은 큰 세그먼트의 재전송, `ping -M do` | [10](../10-fragmentation-mtu-pmtud/2-summary.md) · [09](../09-icmp-ping-traceroute/2-summary.md) · [02](../02-encapsulation/2-summary.md) |
| 요청마다 약 40ms 고정 지연 | Nagle × delayed ACK(write-write-read) | `tcpdump`의 ACK 단독 → 나머지 조각 | [22](../22-nagle-and-delayed-ack/2-summary.md) |
| p99만 높고 에러율 0 | 유실·재정렬로 재전송, RTO 백오프 | `nstat`의 `TcpRetransSegs`, `ss -ti`의 `retrans` | [16](../16-tcp-reliability-retransmission/2-summary.md) · [04](../04-ethernet-and-mac/2-summary.md) · [25](../25-kernel-network-stack/2-summary.md) |
| 원거리 전송이 윈도/RTT에서 막힘 | window scale 누락, `SO_RCVBUF` 고정, 작은 cwnd | SYN의 `wscale`, `ss -ti`의 `cwnd`·`rcv_space` | [03](../03-latency-bandwidth-bdp/2-summary.md) · [17](../17-tcp-flow-control/2-summary.md) · [18](../18-tcp-congestion-control/2-summary.md) |
| UDP 데이터가 사라짐 | 수신 버퍼 넘침, 조각 손실 | `netstat -su`의 receive buffer errors | [14](../14-udp/2-summary.md) · [25](../25-kernel-network-stack/2-summary.md) |
| 개인 페이지가 다른 사용자에게 보임 | 캐시 키에 사용자 구분 없음, `private` 누락 | 응답의 `Age`, CDN HIT 헤더 | [34](../34-http-caching/2-summary.md) · [47](../47-cdn-and-edge/2-summary.md) |
| WebSocket `1006` / SSE 재접속이 일정 간격 | 프록시·LB idle timeout | 끊기는 간격 vs 경로 타임아웃 값 | [38](../38-websocket-sse-long-lived/2-summary.md) |
| HTTP/3만 실패·느림 | UDP 443 차단, UDP 상태 짧은 타임아웃, 작은 MTU | `curl --http3-only` vs `--http3` | [37](../37-http3-quic/2-summary.md) |
| 메일이 스팸함·거절 | SPF permerror, DMARC 정렬 실패 | `Authentication-Results` 헤더 | [51](../51-email-delivery-and-authentication/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인(inverted index)** — 이 노트 자체다. 정방향 "노트 → 증상 목록"을 뒤집어 "증상 → 노트 목록"으로 만든다. 검색 엔진이 "문서 → 단어"를 "단어 → 문서 목록"으로 뒤집는 것과 같은 구조다. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **해시 맵** — 증상 이름(`ECONNRESET`)을 키로 후보 목록을 O(1)에 찾는다. 로그 수집기의 "에러 코드별 집계"도 같은 구조다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **결정 트리** — 한 증상에 후보가 여럿이면 질문 몇 개로 가른다. "즉시였나 / 오래 걸렸나", "RST를 누가 보냈나", "쉬었던 연결인가". 위 §2·§5의 그림이 결정 트리다.
- **이분 탐색식 층 진단** — 층을 하나씩 확인해 "되는 층"과 "안 되는 층"의 경계를 찾는다([01](../01-layer-map-osi-tcpip/2-summary.md)).

```ts
// 역색인 + 결정 트리 한 단계 (개념 예시)
type Leaf = string;
const index = new Map<string, { when: (c: Ctx) => boolean; leaf: Leaf }[]>([
  ["ECONNRESET", [
    { when: c => c.idleBeforeMs > 30_000, leaf: "35 idle close 경합 / 11 NAT idle" },
    { when: c => c.phase === "upload",    leaf: "19 본문 미소비 close / 42 크기 한도" },
    { when: () => true,                   leaf: "19 RST 일반" },
  ]],
  ["ETIMEDOUT", [
    { when: c => c.phase === "connect",   leaf: "15 SYN 무응답 / 48 DROP / 11 conntrack" },
    { when: () => true,                   leaf: "16·21 재전송 포기" },
  ]],
]);
interface Ctx { phase: "connect" | "read" | "write" | "upload"; idleBeforeMs: number; }
const route = (code: string, c: Ctx) => index.get(code)?.find(r => r.when(c))?.leaf ?? "01 층 지도부터";
```

## 적용 — 풀어나가는 법

### 1. 원문을 잃지 않게 기록한다

증상 색인은 **원문**이 있어야 쓸 수 있다. "호출 실패"로 뭉개면 층이 사라진다(01번 장애 시나리오 1).

Java — cause 체인의 끝까지 남긴다.

```java
static String describe(Throwable t) {
    StringBuilder sb = new StringBuilder();
    for (Throwable c = t; c != null; c = c.getCause()) {
        sb.append(c.getClass().getName()).append(": ").append(c.getMessage()).append(" <- ");
    }
    return sb.toString();  // 예: SSLHandshakeException: ... <- CertPathValidatorException: ...
}
```

Node — `code`와 `syscall`을 남긴다. `message`만 남기면 단계가 빠진다.

```js
socket.on('error', (err) => {
  log.warn({ code: err.code, syscall: err.syscall, address: err.address, port: err.port,
             idleMs: Date.now() - lastUsedAt }, 'upstream socket error');
});
```

- 실패까지 걸린 시간과, 그 연결이 직전에 얼마나 쉬었는지(idle)를 함께 남긴다. 결정 트리의 첫 질문이 이것이다.

### 2. 걸린 시간으로 1차 분류한다

```text
  실패까지 걸린 시간           대개 뜻하는 것                             가 볼 곳
  ------------------------   ---------------------------------------   ---------------
  즉시 (ms)                   누군가 **거절**했다 (RST·ICMP·로컬 자원)      15, 48, 20, 23
  초 단위 계단                 SYN 재전송 (6.5+ 기본 1·2·3·4·5·7초…,        15, 16
                               이전 커널 1·3·7초…)
  약 2분 (connect)            SYN이 어딘가에서 조용히 버려졌다              15, 48, 11
  앱 타임아웃 값과 정확히 같음    내 타임아웃이 끊었다 (원인은 아직 모른다)      35, reliability 영역
  경로 장비 idle 값과 같음      LB·NAT·프록시가 idle 연결을 정리했다          35, 38, 11, 21
  약 15분 이상 (전송 중)        재전송이 `tcp_retries2` 한도에 닿았다         16, 21
  약 2시간 11분 (idle 연결)     keepalive 탐침이 모두 무응답 (기본값)         21
```

### 3. 단계와 방향을 본다

1. **단계**: connect 중인가, 요청을 쓰는 중인가, 응답을 읽는 중인가(Node `syscall`, Java 스택 트레이스의 `connect`·`read`·`write`).
2. **방향**: RST·FIN·alert를 **누가** 보냈나. 양쪽에서 동시에 잡는다.

```bash
# RST·FIN이 어느 쪽에서 왔나
tcpdump -ni any 'host 10.0.0.9 and tcp port 8080 and (tcp[tcpflags] & (tcp-rst|tcp-fin) != 0)'

# 연결 상태·타이머·재전송
ss -tanpio 'dst 10.0.0.9'

# 커널 카운터 (재전송·accept 큐·타임아웃 포기)
nstat -az | grep -E 'TcpRetransSegs|ListenOverflows|ListenDrops|TCPAbortOnTimeout'

# DNS: 앱과 같은 경로(NSS) vs DNS 자체
getent hosts api.example.com ; dig api.example.com ; dig +trace api.example.com

# TLS: 체인·이름·기간
openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts </dev/null

# HTTP: 단계별 시간
curl -sv -o /dev/null -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer}\n' https://api.example.com/
```

- 명령별 상세는 [50-network-diagnostics](../50-network-diagnostics/2-summary.md)가 모은다.

### 4. leaf로 간다

- 위 §2~§8 표에서 후보 leaf를 고른다. 후보가 여럿이면 **각 leaf의 "보이는 형태"** 와 내 관찰을 대조해 지운다.
- 후보가 하나도 맞지 않으면 [01 층 지도](../01-layer-map-osi-tcpip/2-summary.md)로 돌아가 아래층부터 다시 확인한다.

## 장애 시나리오와 대처

### 1. `ECONNRESET`을 "서버가 죽었다"로 읽는다 — 실제는 idle close 경합

- **현상**: 트래픽이 적은 시간에 요청 1% 미만이 `ECONNRESET`으로 실패한다. 서버팀은 "재시작 이력도 에러 로그도 없다"고 답한다. 서로 상대를 의심한다.
- **보이는 형태**
  - Java `SocketException: Connection reset`, Node `socket hang up`(`code: 'ECONNRESET'`), LB 뒤라면 사용자에게 502.
  - 실패한 요청은 모두 **한동안 쉬었던 풀 연결**의 첫 요청이다.
  - `tcpdump`에서 서버 FIN → 클라이언트 요청 → 서버 RST 순서가 보인다.
- **원인**
  - 서버(또는 LB·NAT)의 idle timeout이 클라이언트 풀의 idle 축출보다 짧다.
  - 서버가 닫는 순간 클라이언트가 그 연결을 재사용했다. 서버는 이미 닫은 소켓에 온 데이터에 RST로 답한다.
  - "reset"이라는 단어가 "상대가 비정상 종료했다"로 읽혀 오진했다. RST는 연결 중단 또는 "그런 연결은 없다"를 알릴 뿐, 그 자체로 프로세스 사망을 뜻하지 않는다.
- **대처**
  - 구간마다 "클라이언트 idle < 서버 keep-alive"로 맞춘다([35](../35-http-connection-management/2-summary.md)).
  - NAT·LB idle timeout이 원인이면 keepalive·풀 수명을 그보다 짧게 둔다([11](../11-nat-and-conntrack/2-summary.md), [21](../21-tcp-keepalive-and-user-timeout/2-summary.md)).
  - 멱등 요청만 "재사용 연결에서 난 리셋"을 한 번 재시도한다.
  - 판정 규칙: **RST의 방향과 직전 패킷**을 보기 전에는 원인을 적지 않는다([19](../19-tcp-termination-fin-rst-half-open/2-summary.md)).

### 2. connect `ETIMEDOUT`을 "상대 서버가 느리다"로 읽는다 — 실제는 조용한 DROP

- **현상**: DB 호출이 2분씩 멈췄다가 실패한다. DB팀은 "쿼리 지연 없음, 연결 시도 로그도 없음"이라고 한다.
- **보이는 형태**
  - Java `ConnectException: Connection timed out`, Node `connect ETIMEDOUT`.
  - `ss -tan state syn-sent`에 연결이 머문다. `tcpdump`에 SYN만 반복된다(6.5+ 기본은 1초 간격 5번 뒤 2·4·8…초, 이전 커널은 1·2·4·8…초 간격).
  - 서버 쪽 캡처에는 SYN이 **아예 없다**.
- **원인**
  - connect 단계의 타임아웃은 "서버가 느리다"가 아니라 "SYN에 아무 답이 없었다"다. 서버 앱은 연결을 본 적이 없다.
  - 새 보안 그룹 규칙이 DROP했다. 비슷한 모양: 비대칭 경로 + 상태 방화벽, `nf_conntrack` 표 가득, SNAT 포트 고갈.
- **대처**
  - SYN이 어디까지 가는지 양 끝에서 동시에 캡처한다.
  - 방화벽·보안 그룹·conntrack 카운터를 본다([48](../48-firewalls-and-network-policy/2-summary.md), [11](../11-nat-and-conntrack/2-summary.md)).
  - connect 타임아웃을 수 초로 짧게 둬서 DROP이 스레드 고갈로 번지지 않게 한다([15](../15-tcp-handshake-and-backlog/2-summary.md)).
  - refused와 timeout을 지표에서 따로 센다. 즉시 실패와 긴 실패는 원인 층이 다르다.

### 3. `EADDRNOTAVAIL`·`BindException`을 "상대·네트워크 문제"로 읽는다 — 실제는 내 호스트의 포트 고갈

- **현상**: 트래픽 피크에 외부 API 호출이 **즉시** 실패한다. 상대 API는 멀쩡하다. Java 로그의 `BindException`을 보고 "서버 포트 충돌"을 찾느라 시간을 쓴다.
- **보이는 형태**
  - errno `EADDRNOTAVAIL`, 메시지 "Cannot assign requested address". Java는 JDK NIO 구현에서 `BindException`으로 올라온다(`Net.c`).
  - `ss -tan state time-wait`가 수만 개이고 목적지가 한두 곳에 몰려 있다.
- **원인**
  - connect의 `EADDRNOTAVAIL`은 **내 쪽 임시 포트 범위가 바닥났다**는 뜻이다(connect(2)).
  - 요청마다 새 연결을 열고 먼저 닫아 포트가 TIME-WAIT에 묶였다.
  - `BindException`이라는 이름 때문에 listen 쪽 문제로 오해했다. connect도 내부적으로 로컬 포트를 bind한다.
- **대처**
  - 커넥션 풀·keep-alive로 재사용한다(근본, [35](../35-http-connection-management/2-summary.md)).
  - 급하면 `ip_local_port_range`를 넓히고 `tcp_tw_reuse`를 검토한다([20](../20-time-wait-and-close-wait/2-summary.md)).
  - 같은 errno라도 bind에서 났다면 "이 호스트에 없는 주소"다. 단계부터 확인한다.

### 4. `UnknownHostException`을 "DNS 서버 장애"로 읽는다 — 실제는 부정 캐시·정책·검색 목록

- **현상**: 새로 만든 `new.example.com`으로만 호출이 실패한다. 인프라팀은 "DNS 서버는 정상"이라고 한다.
- **보이는 형태**
  - Java `UnknownHostException`, Node `getaddrinfo ENOTFOUND`.
  - 앱 호스트의 `dig new.example.com`은 `NXDOMAIN`이고 AUTHORITY 절에 SOA가 있다. `dig @ns1 new.example.com`은 정상이다.
- **원인**
  - Java의 `UnknownHostException`은 NXDOMAIN·SERVFAIL·리졸버 불통을 **한 예외**로 합친다. 예외 이름만으로는 셋을 구분할 수 없다.
  - 이번 경우는 레코드를 만들기 전에 헬스체크가 조회해 NXDOMAIN이 **부정 캐시**됐다(RFC 2308).
  - 비슷한 모양: 쿠버네티스 egress 기본 거부로 53이 막힘(`EAI_AGAIN`), `ndots:5` 검색 목록, 컨테이너 `resolv.conf` 오류.
- **대처**
  - 같은 호스트에서 `getent hosts` → `dig` → `dig @권한서버` 순으로 status를 본다. NXDOMAIN·SERVFAIL·timeout은 가는 leaf가 다르다([27](../27-dns-resolution/2-summary.md), [28](../28-dns-caching-and-ttl/2-summary.md), [48](../48-firewalls-and-network-policy/2-summary.md)).
  - 레코드를 먼저 만들고 그다음 트래픽을 켠다. SOA MINIMUM을 과하게 두지 않는다.

### 5. 502를 "앱 버그"로, 504를 "앱이 죽었다"로 읽는다

- **현상**: "5xx 급증" 알림에 앱팀이 앱 로그를 뒤지는데 에러가 없다.
- **보이는 형태**
  - LB 지표에서 5xx가 **LB가 만든 쪽**(`HTTPCode_ELB_5XX_Count`)에만 잡힌다.
  - nginx 에러 로그: `upstream prematurely closed connection` 또는 `upstream timed out (110: Connection timed out)`.
- **원인**
  - 502·504는 **프록시가 만든** 코드다. 앱은 그 요청에 에러를 기록하지 않았을 수 있다.
  - 502는 상류와의 연결이 거부됐거나 도중에 끊긴 경우가 많다. 대표 원인은 1번과 같은 idle close 경합이다(ALB 문서가 "대상 keep-alive < LB idle timeout"을 502 원인으로 든다).
  - 504는 상류가 제때 답하지 않은 것이다. 앱은 살아 있고 느린 쿼리를 기다리는 중일 수 있다.
- **대처**
  - 대시보드를 "누가 만든 5xx인가"로 나눈다([33](../33-http-semantics/2-summary.md)).
  - 프록시 에러 로그의 괄호 속 errno(104·110·111)로 전송 계층 원인을 먼저 가른다.
  - 502면 연결 수명([35](../35-http-connection-management/2-summary.md)), 503이면 용량·헬스체크, 504면 상류 처리 시간과 타임아웃 사슬을 본다.

## 핵심 문장

- 이 노트는 **증상 → 층 → 흔한 원인 → 첫 명령 → leaf** 순서의 역색인이다. 병을 고치지 않고 어느 노트로 갈지 정한다.
- 같은 증상도 런타임마다 이름이 다르고(커널 `ECONNREFUSED` = Java `ConnectException` = Node `ECONNREFUSED`), 같은 이름도 단계가 다르면 원인이 다르다(connect의 `EADDRNOTAVAIL` = 포트 고갈, bind의 `EADDRNOTAVAIL` = 없는 주소).
- 가장 먼저 볼 것은 **원문·단계·걸린 시간·방향**이다. 즉시 실패는 거절, 긴 실패는 침묵이다.
- `ECONNRESET`은 "상대가 죽었다"가 아니다. 누군가 그 연결을 중단했거나 없다고 알렸을 뿐이고, 가장 흔한 원인은 idle timeout 불일치다.
- 502·504는 프록시가 만든 코드다. 로그 속 errno 번호가 전송 계층 원인을 알려 준다.
- Java `UnknownHostException`은 NXDOMAIN·SERVFAIL·리졸버 불통을 합친다. 구분은 같은 호스트의 `dig`로 한다.

## 관련 주제·근거

- 선행: 네트워크 영역 전체. 특히
  - [01-layer-map-osi-tcpip](../01-layer-map-osi-tcpip/2-summary.md) — 에러를 층에 대응시키는 표
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — FIN·RST·half-open과 errno 순서
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — idle close 경합
- 이 노트가 가리키는 leaf: 위 §2~§8 표의 링크 전부. 영역 표는 [../README.md](../README.md).
- 후속
  - [53-network-incidents](../53-network-incidents/2-summary.md) — 실사건에서 이 증상들이 어떻게 겹쳐 나타났나
  - [49-what-happens-when-url](../49-what-happens-when-url/2-summary.md) — URL 입력부터 렌더링까지 단계별로 어디서 어떤 증상이 나나
  - [50-network-diagnostics](../50-network-diagnostics/2-summary.md) — 이 노트의 "첫 명령"들의 상세
- Linux man-pages
  - errno(3) — 이름·POSIX 문자열, `EMFILE`(RLIMIT_NOFILE)·`ENFILE`(file-max) <https://man7.org/linux/man-pages/man3/errno.3.html>
  - connect(2) — `ECONNREFUSED`, `ETIMEDOUT`, `EADDRNOTAVAIL`(임시 포트 소진) <https://man7.org/linux/man-pages/man2/connect.2.html>
  - bind(2) · ip(7) — `EADDRNOTAVAIL`(로컬 아닌 주소), `EHOSTUNREACH` <https://man7.org/linux/man-pages/man2/bind.2.html> · <https://man7.org/linux/man-pages/man7/ip.7.html>
  - send(2) — `EPIPE`·`SIGPIPE`·`MSG_NOSIGNAL` <https://man7.org/linux/man-pages/man2/send.2.html>
  - tcp(7) — `ETIMEDOUT`(재전송 미확인), `EPIPE` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - accept(2) — `EMFILE`·`ENFILE` <https://man7.org/linux/man-pages/man2/accept.2.html>
  - listen(2) — 큐가 찼을 때 `ECONNREFUSED` 또는 무시 <https://man7.org/linux/man-pages/man2/listen.2.html>
  - getaddrinfo(3) — `EAI_AGAIN`·`EAI_NONAME`·`EAI_FAIL` <https://man7.org/linux/man-pages/man3/getaddrinfo.3.html>
- 커널·도구 문서
  - Kernel docs ip-sysctl — `tcp_syn_retries`(67초·131초), `tcp_syn_linear_timeouts`(기본 4, 6.5+) <https://docs.kernel.org/networking/ip-sysctl.html>
  - tcp(7) — `tcp_abort_on_overflow`, `tcp_keepalive_time`(7200)·`tcp_keepalive_intvl`(75)·`tcp_keepalive_probes`(9) · socket(7) — `SO_ERROR`(보류 에러를 꺼내고 지움) <https://man7.org/linux/man-pages/man7/socket.7.html>
  - iptables-extensions(8) — REJECT 기본 응답 ICMP port unreachable, `--reject-with tcp-reset` · ip-route(8) — `unreachable` 경로 타입
  - 리눅스 소스 `net/ipv4/tcp_input.c` `tcp_reset`(CLOSE-WAIT면 `EPIPE`)·`tcp_conn_request`, `net/ipv4/tcp_minisocks.c` `listen_overflow`, `net/ipv4/icmp.c` `icmp_err_convert[]`, `net/ipv4/fib_semantics.c`(`RTN_UNREACHABLE` → `-EHOSTUNREACH`)
- RFC 9293 §3.10.5(ABORT — 연결 중단에도 RST) <https://www.rfc-editor.org/rfc/rfc9293> · RFC 4035 §5.5(검증 실패 → RCODE 2) <https://www.rfc-editor.org/rfc/rfc4035>
- OpenJDK 소스
  - `src/java.base/unix/native/libnio/ch/Net.c` `handleSocketErrorWithMessage` — errno → 예외 클래스 <https://github.com/openjdk/jdk/blob/master/src/java.base/unix/native/libnio/ch/Net.c>
  - `src/java.base/unix/native/libnio/ch/SocketDispatcher.c` · `sun/nio/ch/NioSocketImpl.java` — 읽기의 "Connection reset"
  - JEP 353 "Reimplement the Legacy Socket API"(JDK 13) <https://openjdk.org/jeps/353>
- Node.js `errors` — Common system errors <https://nodejs.org/api/errors.html> · `dns` — 오류 코드 상수 <https://nodejs.org/api/dns.html>
- DNS: RFC 1035 §4.1.1(RCODE) <https://www.rfc-editor.org/rfc/rfc1035> · RFC 2308(부정 캐시, §2.2 NODATA) <https://www.rfc-editor.org/rfc/rfc2308> · RFC 8914(Extended DNS Errors) <https://www.rfc-editor.org/rfc/rfc8914>
- TLS: RFC 8446 §6 alert 목록·번호 <https://www.rfc-editor.org/rfc/rfc8446>
- HTTP: RFC 9110 §15.6.3(502)·§15.6.4(503)·§15.6.5(504) <https://www.rfc-editor.org/rfc/rfc9110>
- nginx 소스 `src/http/ngx_http_upstream.c` — 상류 오류 로그 문자열, `ngx_http_upstream_next`의 504/502 선택 <https://github.com/nginx/nginx/blob/master/src/http/ngx_http_upstream.c> · `src/os/unix/ngx_recv.c` — `recv() failed`
- 작성 환경 재현(2026-09-30, Linux 7.0 커널, Python 3, Node 18): `ECONNREFUSED`, RST 뒤 `ECONNRESET` → `EPIPE`, bind `EADDRNOTAVAIL`, `EMFILE`, Node `ENOTFOUND`·`ESERVFAIL`, `dig`의 SERVFAIL + EDE 9
