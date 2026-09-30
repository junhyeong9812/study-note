# network/23-socket-api — 프로세스가 네트워크를 쥐는 손잡이, 소켓 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

TCP·IP는 커널 안에 있다.\
애플리케이션은 커널 메모리를 직접 만질 수 없다.\
그래서 "이 연결로 이 바이트를 보내 달라"고 커널에 부탁할 창구가 필요하다.\
그 창구가 **소켓 API**다.

```text
  +-----------------------------+
  |  내 프로세스                 |
  |   fd = 3  ------------------+----+   "fd 3번으로 보내 줘" (write)
  +-----------------------------+    |
  ============== 시스템콜 경계 ====== | ======================
  |  커널                            v                     |
  |   소켓 객체: [송신 버퍼] [수신 버퍼] [TCP 상태]          |
  |       TCP/IP 스택 -> NIC -> 네트워크                    |
  +--------------------------------------------------------+
```

- 소켓은 파일처럼 **정수 번호(fd)** 로 다룬다. `read`·`write`·`close`가 그대로 통한다.
  - *fd(file descriptor)*: 프로세스가 연 파일·소켓·파이프를 가리키는 작은 정수다. 커널 안 객체의 "번호표"다.

쉬운 예: 전화다.\
`socket()`은 전화기를 산다.\
`bind()`는 번호를 받는다.\
`listen()`은 벨소리를 켠다.\
`accept()`는 울리는 전화를 받는다. 받을 때마다 **새 통화선**이 생긴다.\
`connect()`는 상대 번호로 건다.

똑같은 구조다.\
서버는 "벨 울리는 전화기(리슨 소켓)" 하나와, 통화마다 새로 생기는 "통화선(연결 소켓)" 여러 개를 가진다.

실무 예:
- Java `ServerSocket`·`Socket`, Node `net.Server`·`net.Socket`, Netty·Tomcat 모두 속에서는 이 시스템콜을 부른다.
- "메시지가 가끔 잘린다", "재시작하니 `Address already in use`", "`Too many open files`"가 이 계층의 대표 장애다.

## 동작·원리

### 호출 순서 — 서버와 클라이언트

```text
        서버                                   클라이언트
  fd = socket(AF_INET, SOCK_STREAM)      fd = socket(AF_INET, SOCK_STREAM)
  bind(fd, 0.0.0.0:8080)                        |
  listen(fd, backlog)                           |
        |                                       |
        |     <--- SYN / SYN-ACK / ACK ------  connect(fd, 서버:8080)
        |          (커널이 처리, 15번)             (포트는 커널이 자동 배정)
  cfd = accept(fd)   <- 완성된 연결 하나 꺼냄      |
        |                                       |
  n = recv(cfd, ...)  <------ 데이터 ----------  send(fd, ...)
  send(cfd, ...)      ------- 데이터 --------->  recv(fd, ...)
  close(cfd)                                    close(fd)
```

- `socket()`: 소켓을 만들고 fd를 돌려준다. 새 fd는 **현재 열리지 않은 가장 작은 번호**다(socket(2)).
- `bind()`: 로컬 주소(IP:포트)를 붙인다.
- `listen()`: 이 소켓을 **수동(passive) 소켓**으로 표시한다. 연결 요청을 받는 용도다(listen(2)).
- `accept()`: 대기 큐의 첫 연결을 꺼내 **새 연결 소켓**을 만들고 새 fd를 돌려준다. 원래 리슨 소켓은 그대로다(accept(2)).
- `connect()`: 상대에게 연결한다. bind하지 않은 소켓이면 커널이 빈 포트를 자동으로 붙인다(ip(7)).
  - *임시 포트(ephemeral port)*: 클라이언트 쪽에 커널이 자동 배정하는 포트. 범위는 `ip_local_port_range`로 정한다.
- 실패 예: 상대 포트에 아무도 listen하지 않으면 `connect()`는 `ECONNREFUSED`다(connect(2)).

### 리슨 소켓 1개, 연결 소켓 N개

```text
  서버 프로세스 fd 표
  +----+----------------------------------------------+
  | 0  | stdin                                        |
  | 1  | stdout                                       |
  | 2  | stderr                                       |
  | 3  | 리슨 소켓 0.0.0.0:8080   (LISTEN)             |---> accept 큐 [conn][conn][ ]
  | 4  | 연결 소켓 10.0.0.5:8080 <-> 10.0.0.9:51000    |
  | 5  | 연결 소켓 10.0.0.5:8080 <-> 10.0.0.7:40022    |
  +----+----------------------------------------------+
```

- 연결 소켓은 4-튜플(내 IP·포트, 상대 IP·포트)로 구분된다. 그래서 같은 8080 포트에 연결이 수만 개 붙을 수 있다.
- 연결마다 fd를 하나 쓴다. fd는 프로세스당 한도(`RLIMIT_NOFILE`)가 있다. 넘으면 `socket()`·`accept()`가 `EMFILE`이다(socket(2), accept(2)).

### accept 큐와 backlog

```text
  SYN 도착 -> [SYN 큐: 핸드셰이크 진행 중] -> ACK 도착 -> [accept 큐: 완성, 앱 대기] -> accept()
                  tcp_max_syn_backlog                       backlog (<= somaxconn)
```

- 리눅스 2.2부터 `backlog`는 **완성된 연결의 대기 큐 길이**다(listen(2) NOTES).
- `backlog`가 `net.core.somaxconn`보다 크면 **조용히** 그 값으로 잘린다. 기본값은 리눅스 5.4부터 4096, 그 전은 128이다(listen(2)).
- 큐가 차면 클라이언트는 `ECONNREFUSED`를 받거나, 요청이 무시돼 재시도 뒤 성공할 수 있다(listen(2)).
  - 리눅스 기본(`tcp_abort_on_overflow=0`)은 **무시** 쪽이다. 핸드셰이크 마지막 ACK를 버리고 요청을 SYN 큐에 남긴다(`net/ipv4/tcp_minisocks.c` `listen_overflow`).
  - 복구는 **서버**가 이끈다. 서버가 SYN-ACK를 재전송하고(`tcp_synack_retries`, 기본 5), 클라이언트는 다시 ACK한다. 그사이 자리가 나면 연결이 완성된다. 버스트였다면 지연으로 끝난다(tcp(7)).
  - 재전송 한도까지 자리가 안 나면 서버는 요청을 조용히 버린다(`net/ipv4/inet_connection_sock.c` `reqsk_timer_handler`). 클라이언트는 이미 ESTABLISHED라 모른다. 그 뒤 데이터를 보내면 RST(`ECONNRESET`)를 받거나, 서버가 먼저 말하는 프로토콜이면 응답 없이 기다리다 타임아웃이 난다. 자세한 내용은 [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md)의 몫이다.

### 송수신 버퍼 — `send`가 돌아왔다 ≠ 상대가 받았다

```text
  앱 send(100KB)                               상대 앱 recv()
      |  복사                                        ^  복사
      v                                              |
  [송신 버퍼 ########......]  -- TCP 세그먼트 -->  [수신 버퍼 ####......]
   커널이 ACK 받을 때까지 보관                       앱이 읽을 때까지 보관
```

- `send()`는 데이터를 **커널 송신 버퍼로 복사**하면 돌아온다. 상대에게 도착했다는 뜻이 아니다.
- 송신 버퍼에 자리가 없으면
  - 블로킹 소켓: `send()`가 자리가 날 때까지 멈춘다.
  - 논블로킹 소켓: `EAGAIN`/`EWOULDBLOCK`으로 바로 실패한다(send(2)).
- `recv()`는 **지금 있는 만큼, 요청 크기 이하로** 돌려준다. 요청한 만큼 다 올 때까지 기다리지 않는다(recv(2)).
- 버퍼 크기는 `SO_SNDBUF`·`SO_RCVBUF`로 바꾼다.
  - 커널은 설정값을 **두 배로** 잡는다(관리용 오버헤드 몫). `getsockopt()`도 두 배 값을 돌려준다(socket(7)).
  - 상한은 `net.core.wmem_max`·`rmem_max`다.

### 바이트 스트림 — 쓰기 경계는 보존되지 않는다

```text
  보낸 쪽:  send("HELLO")  send("WORLD")
  받는 쪽:  recv -> "HEL"   recv -> "LOWOR"   recv -> "LD"      (가능한 한 예)
            recv -> "HELLOWORLD"                                 (가능한 다른 예)
```

- TCP는 바이트의 **순서**만 보장한다. `send` 한 번이 `recv` 한 번이 되지 않는다.
- 쓰기도 마찬가지다. `write()`는 요청보다 **적게** 쓰고 돌아올 수 있다(write(2) "partial write").
  - 논블로킹 소켓에서 버퍼 여유가 모자랄 때
  - 블로킹 소켓이 일부 쓴 뒤 시그널에 끊겼을 때(write(2))
  - `SO_SNDTIMEO` 타임아웃이 일부 전송 뒤 걸렸을 때 — 전송한 양을 돌려준다(socket(7))
- 그래서 **반복문**이 필수다. "다 쓸 때까지 쓰기", "필요한 만큼 모일 때까지 읽기".
- 메시지 경계를 어디서 끊을지는 앱 프로토콜이 정한다(24번 프레이밍).

### close와 포트 재사용

- `close(fd)`는 fd를 닫는다. 그 소켓을 가리키는 마지막 fd였다면 커널이 보통 연결 종료(FIN)를 시작한다. 종료 절차는 19번 노트의 몫이다.
  - 예외(리눅스 `net/ipv4/tcp.c` `__tcp_close`): 앱이 안 읽은 수신 데이터가 남아 있거나 `SO_LINGER`를 켜고 linger 시간을 0으로 뒀다면 FIN 대신 **RST**로 즉시 끊는다(RFC 2525 §2.17). 이때는 TIME-WAIT도 남지 않는다.
- FIN으로 먼저 닫은 쪽은 TIME-WAIT로 한동안 남는다(20번).
- 이 동안 같은 로컬 주소로 `bind()`하면 막힌다.
  - "bind된 TCP 로컬 주소는 닫은 뒤 한동안 쓸 수 없다. `SO_REUSEADDR`를 설정했다면 예외다"(ip(7)).
  - `SO_REUSEADDR`를 켜면, 그 주소에 **리슨 중인 소켓이 없는 한** bind할 수 있다(socket(7)).
  - 리눅스는 **이전 프로그램과 새 프로그램 둘 다** `SO_REUSEADDR`를 켰을 때만 재사용을 허락한다. FreeBSD 등은 새 쪽만 켜면 된다(socket(7) NOTES).
- `SO_REUSEPORT`(리눅스 3.9+)는 다르다. 여러 소켓이 **같은 주소에 동시에** bind해 부하를 나눈다(socket(7)).

## 쓰이는 자료구조·알고리즘

- **fd 표 = 배열** — 프로세스마다 정수 인덱스 → 열린 파일 객체의 표. 새 fd는 "비어 있는 가장 작은 인덱스"다(socket(2)). 그래서 fd를 닫고 바로 새로 열면 같은 번호가 재사용된다.
- **소켓 버퍼 = 큐** — 송신 버퍼는 "보냈지만 ACK 안 된 것 + 아직 안 보낸 것", 수신 버퍼는 "도착했지만 앱이 안 읽은 것"이다.
  - 리눅스에서 수신 큐(`sk_receive_queue`)와 아직 안 보낸 송신 큐(`sk_write_queue`)는 `sk_buff`의 연결 리스트(FIFO)다(`include/net/sock.h`, 25번, [연결 리스트](../../data-structure/02-linked-list/2-summary.md)).
  - TCP의 "보냈지만 ACK 안 된" 재전송 큐(`tcp_rtx_queue`)와 순서가 어긋나 도착한 세그먼트 큐(`out_of_order_queue`)는 레드블랙 트리(`rb_root`)다(`include/net/sock.h`, `include/linux/tcp.h`).
- **accept 큐 = FIFO** — 완성된 연결이 도착 순서대로 쌓이고 `accept()`가 앞에서 꺼낸다. 길이 상한이 backlog다.
- **4-튜플 해시 조회** — 도착 세그먼트를 연결 소켓에 연결할 때 (출발 IP·포트, 도착 IP·포트)로 찾는다. 개념은 [해시맵](../../data-structure/05-hashmap/2-summary.md) 참고.
- **반복 읽기·쓰기 루프** — 부분 전송을 누적 오프셋으로 이어 붙이는 단순 루프다. 메시지 파싱은 길이 접두 파서·상태 기계로 한다(24번).

## 적용 — 풀어나가는 법

### 1. C — "다 쓰기"와 "정확히 n바이트 읽기"를 먼저 만든다

```c
/* len 바이트를 다 보낼 때까지 반복. 성공 0, 실패 -1 */
int write_all(int fd, const char *buf, size_t len) {
    while (len > 0) {
        ssize_t n = send(fd, buf, len, MSG_NOSIGNAL);   /* SIGPIPE로 죽지 않게(19번) */
        if (n < 0) {
            if (errno == EINTR) continue;               /* 시그널에 끊김: 다시 */
            return -1;                                  /* EAGAIN은 논블로킹일 때 따로 처리 */
        }
        buf += n; len -= (size_t)n;                     /* 쓴 만큼 앞으로 */
    }
    return 0;
}

/* 정확히 len 바이트를 읽는다. 성공 0, 상대 FIN(EOF) 1, 실패 -1 */
int read_exact(int fd, char *buf, size_t len) {
    while (len > 0) {
        ssize_t n = recv(fd, buf, len, 0);
        if (n == 0) return 1;                           /* 중간에 끊김: 메시지 불완전 */
        if (n < 0) { if (errno == EINTR) continue; return -1; }
        buf += n; len -= (size_t)n;
    }
    return 0;
}
```

- 서버 소켓은 `bind()` 전에 `SO_REUSEADDR`를 켠다.

```c
int one = 1;
setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
bind(lfd, (struct sockaddr *)&addr, sizeof addr);
listen(lfd, 1024);   /* somaxconn보다 크면 조용히 잘린다 */
```

### 2. Java — 부분 읽기는 `readFully`/`readNBytes`, 부분 쓰기는 NIO에서 직접 처리

```java
try (ServerSocket ss = new ServerSocket()) {
    ss.setReuseAddress(true);          // 초기값은 "정의되지 않음"(Javadoc) — 명시한다
    ss.bind(new InetSocketAddress(8080), 1024);
    try (Socket s = ss.accept()) {     // 연결마다 새 Socket(새 fd)
        DataInputStream in = new DataInputStream(new BufferedInputStream(s.getInputStream()));
        int len = in.readInt();        // 4바이트 길이 접두(예시 프로토콜)
        byte[] body = new byte[len];
        in.readFully(body);            // len 바이트가 다 올 때까지 읽는다. 중간 EOF면 EOFException
    }
}
```

- `InputStream.read(b, off, len)`은 "len만큼 읽으려 시도하지만 **더 적게 읽을 수 있다**"(Javadoc).
- 블로킹 `OutputStream.write()`는 다 쓸 때까지 돌아오지 않는다.
- NIO `SocketChannel`은 논블로킹 모드에서 **버퍼 여유만큼만** 쓴다(`WritableByteChannel` Javadoc). 반복하거나 `OP_WRITE`를 기다린다.

```java
while (buf.hasRemaining()) {
    int n = channel.write(buf);        // 논블로킹이면 0일 수 있다
    if (n == 0) { /* selector에 OP_WRITE 등록 후 대기 */ break; }
}
```

### 3. Node — `'data'`는 메시지 단위가 아니다, `write()`의 false는 "잠깐 멈춰"

```js
const net = require('node:net');
const server = net.createServer((sock) => {
  let acc = Buffer.alloc(0);
  sock.on('data', (chunk) => {             // chunk 경계 = TCP 도착 경계. 메시지 경계 아님
    acc = Buffer.concat([acc, chunk]);
    while (acc.length >= 4) {              // 4바이트 길이 접두(예시 프로토콜)
      const len = acc.readUInt32BE(0);
      if (acc.length < 4 + len) break;     // 아직 덜 옴: 다음 'data'를 기다린다
      handle(acc.subarray(4, 4 + len));
      acc = acc.subarray(4 + len);
    }
  });
});
server.listen(8080);                       // libuv가 bind 전에 SO_REUSEADDR를 켠다(소스 확인)
```

- `socket.write()`가 `false`를 돌려주면 데이터 일부가 사용자 메모리에 쌓였다는 뜻이다. `'drain'` 이벤트 뒤에 계속 쓴다(Node `net` 문서).
- 이를 무시하고 계속 쓰면 프로세스 메모리가 불어난다.

### 4. 진단 명령

```bash
ss -tlnp                         # 리슨 소켓과 소유 프로세스 (-l LISTEN, -p 프로세스)
ss -tnp state established        # 연결 소켓
ss -tm dst 10.0.0.9              # skmem: 송수신 버퍼 사용량 (ss(8) -m)
ls -l /proc/<pid>/fd | wc -l     # 프로세스가 연 fd 개수
cat /proc/<pid>/limits | grep -i 'open files'   # fd 한도
strace -f -e trace=network -p <pid>             # 소켓 시스템콜과 반환값(부분 쓰기 확인)
sysctl net.core.somaxconn net.core.wmem_max net.core.rmem_max
```

- `strace`에서 `sendto(5, ..., 65536, ...) = 21845`처럼 요청보다 작은 반환값이 보이면 부분 쓰기다(숫자는 예시).

## 장애 시나리오와 대처

### 1. 부분 쓰기 미처리 → 메시지가 잘린다

- **현상**: 큰 메시지를 보낼 때만 상대가 파싱 오류를 낸다. 작은 메시지는 괜찮다. 부하가 높을 때 잦다.
- **보이는 형태**
  - 상대 쪽 로그: "unexpected EOF", "invalid frame length", JSON 파싱 오류.
  - `strace`: `write`/`send` 반환값이 요청 길이보다 작다. 코드는 그 뒤를 다시 보내지 않는다.
- **원인**: 논블로킹 소켓(또는 시그널·`SO_SNDTIMEO`)에서 `write()`가 일부만 썼다. 코드가 반환값을 확인하지 않았다.
- **대처**
  - 반환값만큼 오프셋을 옮기며 반복한다(위 `write_all`).
  - 논블로킹이면 남은 데이터를 앱 버퍼에 두고 쓰기 가능 이벤트(epoll `EPOLLOUT`, NIO `OP_WRITE`, Node `'drain'`)를 기다린다.

### 2. 부분 읽기·붙어 읽기 가정 → 간헐 파싱 오류

- **현상**: 로컬·저부하 테스트는 통과한다. 운영에서 가끔 메시지가 깨지거나 두 개가 하나로 처리된다.
- **보이는 형태**: 파싱 오류가 부하·지연이 클 때만 난다. 재현이 어렵다.
- **원인**: `recv()` 한 번 = 메시지 하나라고 가정했다. `recv()`는 있는 만큼만 돌려주므로 메시지가 쪼개지거나 붙어서 온다(recv(2)).
- **대처**
  - 길이 접두·구분자 등 프레이밍을 정하고, 모일 때까지 누적해서 읽는다(24번).
  - Java `readFully`, C `read_exact` 같은 "정확히 n바이트" 도구를 쓴다.

### 3. 재시작하자 `Address already in use`

- **현상**: 서버를 재시작하자 기동이 실패한다. 잠시 기다렸다가(TIME-WAIT가 끝난 뒤) 다시 띄우면 된다.
- **보이는 형태**
  - C `bind: Address already in use`(`EADDRINUSE`)
  - Java `java.net.BindException: Address already in use`
  - Node `Error: listen EADDRINUSE`
  - `ss -tan`에 그 포트의 `TIME-WAIT` 연결이 남아 있다.
- **원인**
  - 이전 프로세스가 먼저 닫은 연결이 TIME-WAIT로 로컬 주소를 잡고 있다. `SO_REUSEADDR` 없이는 bind가 막힌다(ip(7)).
  - 리눅스에서는 이전 프로세스와 새 프로세스 **둘 다** `SO_REUSEADDR`를 켜야 한다(socket(7) NOTES).
  - 다른 가능성: 이전 프로세스가 아직 살아서 **LISTEN 중**이다. 이 경우는 `SO_REUSEADDR`로도 안 된다(socket(7)). `ss -tlnp`로 소유 프로세스를 확인한다.
- **대처**
  - 서버 리슨 소켓은 bind 전에 항상 `SO_REUSEADDR`를 켠다. Java `ServerSocket`은 초기값이 정의되지 않았으므로 명시한다.
  - `SO_REUSEPORT`와 혼동하지 않는다. 그것은 동시 bind로 부하를 나누는 옵션이다.

### 4. `Too many open files` (`EMFILE`)

- **현상**: 트래픽이 늘거나 시간이 지나면 새 연결을 못 받는다. 기존 연결은 동작한다.
- **보이는 형태**
  - `accept: Too many open files`, Java `java.net.SocketException: Too many open files`
  - `ls /proc/<pid>/fd | wc -l`이 `open files` 한도에 붙어 있다.
- **원인**
  - 연결마다 fd를 쓰는데 프로세스 한도(`RLIMIT_NOFILE`)가 작다.
  - 또는 fd 누수다. 예외 경로에서 소켓을 닫지 않았다. 이때 `CLOSE-WAIT`가 함께 쌓이는 경우가 많다(20번).
- **대처**
  - 누수부터 확인한다. try-with-resources(Java), `finally`/`destroy()`(Node)로 반드시 닫는다.
  - 필요하면 한도를 올린다(`ulimit -n`, systemd `LimitNOFILE=`).
  - 리눅스 `accept()`는 새 fd 번호를 먼저 확보한 뒤 큐에서 연결을 꺼낸다(`net/socket.c`, `include/linux/file.h`의 `FD_ADD`). 그래서 `EMFILE`로 실패하면 연결은 accept 큐에 그대로 남는다.
  - 레벨 트리거 epoll은 준비된 동안 계속 알리므로(epoll(7)), 리슨 fd가 매번 "읽기 가능"으로 깨어나는 바쁜 루프가 될 수 있다. libuv는 이를 피하려고 예비 fd를 닫고 대기 연결을 받아 바로 닫는 방법을 쓴다(`src/unix/stream.c` `uv__emfile_trick`).

### 5. backlog가 조용히 잘려 연결 지연·실패

- **현상**: 순간 트래픽이 몰릴 때 클라이언트 `connect()`가 느리거나 타임아웃이 난다. 서버 CPU는 여유가 있다.
- **보이는 형태**
  - `ss -tln`에서 해당 LISTEN 소켓의 Recv-Q가 Send-Q(큐 상한)에 붙는다. LISTEN 소켓에서 Recv-Q는 accept 큐의 현재 길이, Send-Q는 backlog 상한이다(`net/ipv4/tcp_diag.c`: `sk_ack_backlog`·`sk_max_ack_backlog`).
  - `nstat -az | grep -i listen`에서 `TcpExtListenOverflows`·`TcpExtListenDrops`가 오른다. accept 큐가 찬 상태에서 SYN이 오면 커널이 SYN을 버리고 두 카운터를 올린다(커널 문서 snmp_counter).
- **원인**
  - 앱이 `accept()`를 충분히 빨리 부르지 못해 accept 큐가 찼다.
  - 코드에 `listen(fd, 65535)`를 써도 `somaxconn`(구 커널 기본 128)으로 조용히 잘렸다(listen(2)).
- **대처**
  - accept 루프를 전용 스레드·이벤트 루프에서 빠르게 돌린다.
  - `somaxconn`과 앱 backlog를 함께 올린다. 상세는 15번 노트.

## 핵심 문장

- 소켓은 커널 안 TCP 연결을 가리키는 fd다. 리슨 소켓 하나에서 `accept()`할 때마다 새 연결 소켓(새 fd)이 생긴다.
- `send()`가 돌아왔다는 것은 커널 버퍼에 복사됐다는 뜻이지, 상대가 받았다는 뜻이 아니다.
- `read`·`write`는 요청보다 적게 처리하고 돌아올 수 있다. 반복 루프와 프레이밍 없이는 메시지가 잘리거나 붙는다.
- 재시작 시 `Address already in use`는 TIME-WAIT가 로컬 주소를 잡고 있어서다. 리슨 소켓은 bind 전에 `SO_REUSEADDR`를 켠다.
- 연결 하나 = fd 하나다. fd 한도와 누수가 곧 동시 연결 수의 한도다.

## 관련 주제·근거

- 선행
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md) — SYN 큐·accept 큐 상세.
  - `os/21-files-and-descriptors` — fd·open/close 의미. 미작성([os 영역 표](../../os/README.md))
- 후속·연결
  - `24-application-protocol-framing` — 바이트 스트림에서 메시지 경계 찾기. 초안: [systems/resp-protocol](../../systems/resp-protocol/2-summary.md)
  - [25-kernel-network-stack](../25-kernel-network-stack/2-summary.md) — `send()` 뒤 커널 안에서 벌어지는 일
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — `close()`·`recv()=0`·`EPIPE`
  - [20-time-wait-and-close-wait](../20-time-wait-and-close-wait/2-summary.md) — TIME-WAIT와 포트 재사용.
  - [22-nagle-and-delayed-ack](../22-nagle-and-delayed-ack/2-summary.md) — 작은 `write()` 여러 번의 비용
- Linux man-pages
  - socket(2) — 가장 작은 fd 번호, `EMFILE` <https://man7.org/linux/man-pages/man2/socket.2.html>
  - bind(2) — `EADDRINUSE` <https://man7.org/linux/man-pages/man2/bind.2.html>
  - listen(2) — backlog 의미(2.2+), `somaxconn` 상한과 기본값 4096(5.4+)/128 <https://man7.org/linux/man-pages/man2/listen.2.html>
  - accept(2) — 새 연결 소켓, `EMFILE` <https://man7.org/linux/man-pages/man2/accept.2.html>
  - connect(2) — `ECONNREFUSED` <https://man7.org/linux/man-pages/man2/connect.2.html>
  - send(2)·recv(2) — 블로킹/`EAGAIN`, "any data available, up to the requested amount", `MSG_WAITALL` <https://man7.org/linux/man-pages/man2/recv.2.html>
  - write(2) — partial write <https://man7.org/linux/man-pages/man2/write.2.html>
  - socket(7) — `SO_REUSEADDR`·`SO_REUSEPORT`·`SO_SNDBUF`/`SO_RCVBUF`(두 배)·`SO_SNDTIMEO`, NOTES(리눅스 재사용 조건) <https://man7.org/linux/man-pages/man7/socket.7.html>
  - ip(7) — 자동 bind, 닫은 뒤 로컬 주소 사용 불가 <https://man7.org/linux/man-pages/man7/ip.7.html>
  - ss(8) — `-l`, `-p`, `-m` <https://man7.org/linux/man-pages/man8/ss.8.html>
- Java
  - `ServerSocket.setReuseAddress` — 초기값 정의되지 않음 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/ServerSocket.html>
  - `InputStream.read` — 더 적게 읽을 수 있음 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/InputStream.html>
  - `WritableByteChannel.write` — 논블로킹 소켓 채널은 버퍼 여유만큼만 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/WritableByteChannel.html>
- Node.js `net` — `socket.write()` 반환값·`'drain'` <https://nodejs.org/api/net.html> · libuv `uv__tcp_bind`의 `SO_REUSEADDR` <https://github.com/libuv/libuv/blob/v1.x/src/unix/tcp.c>
- Beej's Guide to Network Programming <https://beej.us/guide/bgnet/>
- Bryant & O'Hallaron, 『CS:APP』 3판 11.4 "The Sockets Interface"
