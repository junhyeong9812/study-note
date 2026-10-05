# network/20-time-wait-and-close-wait — 끝난 연결이 남기는 두 가지 흔적 — 정리 (힌트)

## 해결하는 문제

19번 노트에서 본 4-way 종료는 두 쪽에 각각 "기다리는 상태"를 남긴다.

```text
  A (먼저 close = 능동 종료)                 B (나중에 close = 수동 종료)
  FIN-WAIT-1 --- FIN ---------------------> CLOSE-WAIT   <- B의 앱이 close()할 때까지 머묾
  FIN-WAIT-2 <-- ACK ----------------------
                                            (B 앱이 close())
  TIME-WAIT  <-- FIN ---------------------- LAST-ACK
  TIME-WAIT  --- ACK ---------------------> CLOSED
  (2MSL 대기) <- 커널이 스스로 기다림
  CLOSED
```

- **TIME-WAIT**는 먼저 닫은 쪽에 남는다. 커널이 **일부러** 기다리는 정상 상태다.
- **CLOSE-WAIT**는 상대가 먼저 닫았는데 **내 앱이 아직 close()하지 않은** 상태다. 커널이 기다리는 게 아니라 앱을 기다린다.

둘 다 `ss`에서 숫자가 불어나는 것으로 문제가 드러난다.\
그런데 뜻은 정반대다.

```text
  TIME-WAIT 많음   -> 대개 정상. 연결을 너무 자주 여닫는다는 신호. 클라이언트면 포트 고갈 위험
  CLOSE-WAIT 많음  -> 거의 항상 버그. 내 코드가 소켓을 안 닫는다. fd가 샌다
```

쉬운 예: 식당에서 손님이 나간 뒤다.\
TIME-WAIT는 직원이 "혹시 두고 간 물건 찾으러 올까" 잠깐 테이블을 비워 두는 것이다. 정해진 시간이 지나면 치운다.\
CLOSE-WAIT는 손님은 나갔는데 직원이 계산을 안 끝내 테이블을 계속 잡고 있는 것이다. 직원이 움직이기 전에는 영원히 안 치워진다.

실무 예:
- 서버가 외부 API를 요청마다 새 연결로 호출한다. 초당 수백 번이면 `connect()`가 `EADDRNOTAVAIL`(Cannot assign requested address)로 실패하기 시작한다.
- 응답 객체를 닫지 않는 HTTP 클라이언트 코드가 배포됐다. 며칠 뒤 `Too many open files`(`EMFILE`)로 서버가 새 연결을 못 받는다.

## 동작·원리

### 1. TIME-WAIT가 있는 이유 두 가지

**이유 1 — 마지막 ACK가 유실되면 다시 보내야 한다**

```text
  A (TIME-WAIT)                              B (LAST-ACK)
  <-- FIN ----------------------------------
  --- ACK ------------X  (유실)
                                             FIN 재전송 (ACK를 못 받았으니)
  <-- FIN ----------------------------------
  --- ACK ---------------------------------> CLOSED    <- A가 상태를 기억하고 있어서 가능

  만약 A가 곧바로 연결 정보를 지웠다면:
  <-- FIN ----------------------------------
  --- RST ---------------------------------> B: 정상 종료가 아니라 에러로 끝남
```

- 연결 정보가 없는 쪽은 RST가 아닌 세그먼트에 RST로 답한다(RFC 9293 §3.5.2). 그러면 B는 정상 종료를 에러로 받는다.

**이유 2 — 옛 연결의 늦은 세그먼트가 새 연결에 섞이지 않게 한다**

```text
  옛 연결 (10.0.0.1:50000 -> 10.0.0.2:80)   세그먼트 X가 망 어딘가에서 지연 중
  옛 연결 종료 후 곧바로
  새 연결 (10.0.0.1:50000 -> 10.0.0.2:80)   같은 4-튜플!
  X 도착 -> 시퀀스 번호가 우연히 새 연결의 윈도 안이면 새 데이터로 받아들여짐 (데이터 오염)
```

- 세그먼트가 망에 떠돌 수 있는 최대 시간이 MSL이다. RFC 9293은 MSL을 2분으로 잡는다(§3.4.2).
- 능동 종료 쪽은 TIME-WAIT에 2×MSL 머물러야 한다(MUST, MUST-13, §3.6.1). 그동안 같은 4-튜플로 새 연결을 만들지 않으니, 옛 세그먼트는 모두 사라진다.
  - *4-튜플*: (출발 IP, 출발 포트, 도착 IP, 도착 포트). 연결 하나를 식별하는 키다.
  - *MSL(Maximum Segment Lifetime)*: 세그먼트 하나가 망에 살아 있을 수 있는 최대 시간이다.

### 2. 리눅스의 TIME-WAIT

- 리눅스는 TIME-WAIT를 **60초**로 고정한다(`TCP_TIMEWAIT_LEN (60*HZ)`, `include/net/tcp.h`). RFC의 2MSL(4분)보다 짧다.
  - sysctl로 바꿀 수 없다(Bernat 2014).
  - `tcp_fin_timeout`은 TIME-WAIT 시간이 **아니다**. 앱이 놓아 버린(orphan) FIN-WAIT-2 소켓의 유지 시간이다(기본 60초, ip-sysctl). 이름 때문에 자주 혼동한다.
- TIME-WAIT 소켓은 **fd를 차지하지 않는다.** 앱은 이미 `close()`했고, 커널이 작은 "미니 소켓"으로만 들고 있다.
  - ss(8)은 time-wait를 "미니 소켓으로 유지되는 상태(bucket)"로 분류한다.
  - Bernat는 메모리 비용이 작다고 계산한다. 들어오는 연결 약 4만 개의 TIME-WAIT가 10MiB 미만이고, 나가는 연결이면 약 2.5MiB가 더 든다(Bernat 2014).
- 시스템 전체 상한은 `tcp_max_tw_buckets`다. 넘으면 TIME-WAIT 소켓을 즉시 없애고 경고를 남긴다(tcp(7)). 커널 문서는 이 값을 인위로 낮추지 말고, 필요하면 올리라고 한다(ip-sysctl).

### 3. TIME-WAIT가 문제가 되는 곳 — 클라이언트의 임시 포트

```text
  클라이언트 10.0.0.1  ---- connect ---->  서버 10.0.0.2:80 (고정)

  4-튜플 = (10.0.0.1, ???, 10.0.0.2, 80)
                      ^ 바꿀 수 있는 건 이것 하나: 임시 포트
  임시 포트 범위 (리눅스 기본 ip_local_port_range = 32768 ~ 60999) -> 28,232개

  각 연결이 끝나면 그 포트는 TIME-WAIT로 60초 묶임
  -> 같은 목적지로 초당 약 28,232 / 60 ≈ 470개 넘게 새 연결을 열면 포트가 바닥남
  -> connect() = -1, errno = EADDRNOTAVAIL
```

- `connect()`가 임시 포트를 고르려는데 범위의 모든 포트가 사용 중이면 `EADDRNOTAVAIL`이다(connect(2)).
  - *임시 포트(ephemeral port)*: `connect()` 때 커널이 자동으로 골라 주는 출발 포트다.
- 제한은 **목적지(IP, 포트)마다**다. 목적지가 다르면 같은 출발 포트를 다시 쓸 수 있다.
- 서버 쪽은 보통 문제가 안 된다. 서버의 4-튜플은 클라이언트 IP·포트가 다양해서 겹치지 않는다(Bernat 2014).
  - 단, 서버가 먼저 닫으면 TIME-WAIT가 서버에 쌓인다. 개수는 늘어도 포트를 소비하지는 않는다.
- 로드밸런서 → 백엔드처럼 **소수의 고정 목적지로 대량의 짧은 연결**을 여는 곳이 전형적인 위험 지점이다.

### 4. TIME-WAIT를 줄이는 장치들

```text
  장치                           어디에 효과              조건·주의
  ----------------------------   ---------------------   -------------------------------------------
  커넥션 재사용 (keep-alive·풀)    전부                     근본 해법. 연결 자체를 덜 만든다
  tcp_tw_reuse                   나가는 연결(클라이언트)    타임스탬프 필요. 기본 2 = loopback만
  SO_LINGER {1, 0} 후 close       전부                     RST로 끊음. TIME-WAIT 없음. 데이터 유실 위험
  목적지 늘리기 (IP·포트 여러 개)   클라이언트                4-튜플 공간 자체를 넓힘
  tcp_tw_recycle                 (삭제됨)                 NAT 뒤 클라이언트를 깨뜨려 Linux 4.12에서 제거
```

- `tcp_tw_reuse`: 프로토콜상 안전할 때 TIME-WAIT 소켓을 **새 나가는 연결**에 재사용한다.
  - 값: 0 끔, 1 전체, 2 loopback만. **기본값 2**(커널 문서 ip-sysctl).
  - tcp(7) 맨페이지는 기본값을 "disabled"로 적는데, 현재 커널 문서와 다르다. 커널 문서를 따른다.
  - 타임스탬프로 새 연결의 세그먼트를 옛것과 구별한다. 들어오는 연결(서버)에는 효과가 없다(Bernat 2014).
  - 재사용까지 최소 지연은 `tcp_tw_reuse_delay`(기본 1000ms)다(ip-sysctl).
- RFC 9293도 TIME-WAIT에서 새 SYN을 받아 연결을 다시 여는 것을 허용한다(MAY-2, §3.6.1). 새 ISN이 옛 연결의 최대 시퀀스보다 커야 한다. 타임스탬프를 쓰는 개선안(RFC 6191)은 구현을 권한다(SHOULD, SHLD-4).
- `tcp_tw_recycle`은 NAT 뒤의 여러 호스트를 한 호스트처럼 타임스탬프로 걸러 연결을 거부했다. Linux 4.12에서 완전히 제거됐다(tcp(7): Linux 2.4~4.11, Bernat 2014).
- **RST로 TIME-WAIT가 죽는 경우**: 리눅스는 기본으로 TIME-WAIT 중 RST를 받으면 기다리지 않고 소켓을 닫는다. RFC 1337("TIME-WAIT Assassination Hazards")을 따르는 동작은 `tcp_rfc1337=1`로 켠다(tcp(7)).

### 5. 서버 재시작 시 `Address already in use`

```text
  서버 프로세스 재시작
  bind(:8080) -> EADDRINUSE "Address already in use"
  원인: 이전 프로세스가 연 연결들이 :8080을 로컬 포트로 쓴 채 TIME-WAIT에 남아 있음
  해결: listen 소켓에 bind 전에 SO_REUSEADDR
```

- `SO_REUSEADDR`를 켜면 활성 리스닝 소켓이 없는 한 같은 주소에 bind할 수 있다(socket(7)).
- 대부분의 서버 프레임워크는 기본으로 켠다 [?]. 직접 소켓을 짤 때 챙긴다.

### 6. CLOSE-WAIT — 커널이 아니라 앱이 멈춘 상태

```text
  상대가 FIN을 보냄
  내 커널: ACK 보내고 CLOSE-WAIT로 전이. 내 앱의 read()가 0(EOF)을 받게 함
  내 앱:  0을 받고도 close()를 안 함   <---- 여기서 멈춤
  -> 연결은 CLOSE-WAIT에 무기한 머묾 (커널이 스스로 벗어날 방법 없음)
  -> fd가 열린 채 남음 -> 쌓이면 EMFILE
```

- RFC 상태 기계에서 CLOSE-WAIT를 벗어나는 길은 **사용자 CLOSE**(→ LAST-ACK)뿐이다. 그 밖에는 RST 수신이나 앱의 abort다(RFC 9293 §3.3.2 Figure 5, §3.6 Case 2).
  - 커널에 CLOSE-WAIT 전용 타이머는 없다. `tcp_fin_timeout`도 CLOSE-WAIT에는 해당하지 않는다(그건 orphan FIN-WAIT-2용).
  - 예외: 앱이 `SO_KEEPALIVE`를 켰다면 CLOSE-WAIT에서도 keepalive probe가 나간다(`net/ipv4/tcp_timer.c` `tcp_keepalive_timer`). 상대가 이미 사라졌으면 probe 실패나 RST로 TCP 상태는 정리될 수 있다.
  - 그래도 **fd는 앱이 `close()`할 때까지 남는다.** 그래서 fd 누수는 keepalive로 해결되지 않는다.
- 앱이 `close()`하지 않았으니 **fd가 열려 있다.** 이것이 TIME-WAIT와의 결정적 차이다.
  - 프로세스의 fd 한도(`RLIMIT_NOFILE`, `ulimit -n`)에 닿으면 `open()`·`socket()`·`accept()`가 `EMFILE`로 실패한다(getrlimit(2), accept(2)).
  - 메시지는 "Too many open files"다.
- 흔한 원인
  - 응답·스트림·커넥션 객체를 닫지 않는 코드 경로(특히 예외 경로).
  - `read()`가 0을 돌려준 것을 "데이터 없음"으로 오해하고 루프를 계속 도는 코드.
  - Node에서 `allowHalfOpen: true`로 만든 서버가 `'end'`를 받고도 `end()`를 부르지 않음(기본값 false면 Node가 자동으로 FIN을 보낸다, Node `net` 문서).
  - 풀에서 빌린 연결을 반납하지 않아 풀 밖에서 영원히 잡혀 있음.
- 상대 쪽에서는 이 연결이 **FIN-WAIT-2**로 보인다(19번 장애 5). 상대 리눅스는 orphan이면 `tcp_fin_timeout` 뒤 정리한다. 그러나 내 쪽 CLOSE-WAIT는 그대로 남는다.

### 7. 앱에서 보이는 모습

```text
  상태          fd 점유    누가 풀어 주나        쌓이면 앱이 보는 에러
  -----------  --------  -------------------  ------------------------------------------------
  TIME-WAIT    아니오     커널 (리눅스 60초)     클라이언트 connect(): EADDRNOTAVAIL
                                              서버 재시작 bind(): EADDRINUSE (SO_REUSEADDR 없을 때)
  CLOSE-WAIT   예         앱의 close()만        socket()/accept()/open(): EMFILE
```

## 쓰이는 자료구조·알고리즘

- **해시 테이블(4-튜플 → 연결)** — 커널은 도착 세그먼트를 4-튜플로 찾는다. TIME-WAIT 미니 소켓도 이 테이블에 남아 같은 4-튜플의 새 연결을 막는다.
  - 리눅스는 established·time-wait 연결을 같은 해시 테이블(ehash)로 관리한다(`net/ipv4/inet_timewait_sock.c`가 TIME-WAIT 소켓을 ehash 체인에 넣는다). 개념은 [해시맵](../../data-structure/05-hashmap/2-summary.md).
  - 임시 포트 선택은 "이 4-튜플이 테이블에 없는 포트"를 찾는 탐색이다. 범위가 거의 찰수록 탐색이 길어진다(Bernat가 CPU 비용으로 언급).
- **타이머 휠** — 수만 개의 TIME-WAIT가 각자 60초 뒤 만료된다. 리눅스는 TIME-WAIT 소켓마다 타이머(`tw_timer`)를 하나씩 건다(`net/ipv4/inet_timewait_sock.c`). 이 타이머들은 커널 공용 구조인 계층형 타이머 휠에 들어가서 싸게 관리된다(`kernel/time/timer.c`). [data-structure/26-timer-structures](../../data-structure/26-timer-structures/2-summary.md).
- **fd 테이블** — 프로세스마다 정수 fd → 열린 파일(소켓) 객체의 배열이다. 한도(`RLIMIT_NOFILE`)는 "가장 큰 fd 번호 + 1"이다(getrlimit(2)). [os/21-files-and-descriptors](../../os/21-files-and-descriptors/2-summary.md).
- **리소스 수명 관리(RAII·try-with-resources)** — CLOSE-WAIT 누수는 "획득한 자원을 모든 경로에서 해제"하지 못한 버그다.

## 적용 — 풀어나가는 법

### 1. 숫자부터 본다

```bash
# 상태별 개수
ss -tan | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn
ss -s                       # 요약: estab, timewait 등

# TIME-WAIT가 어느 목적지로 몰렸나 (클라이언트 포트 고갈 판단)
ss -tan state time-wait | awk 'NR>1 {print $4}' | sort | uniq -c | sort -rn | head

# CLOSE-WAIT를 가진 프로세스 (-p: 소유 프로세스)
ss -tanp state close-wait

# 그 프로세스의 fd 수와 한도
ls /proc/<PID>/fd | wc -l
grep 'open files' /proc/<PID>/limits

# 관련 커널 값
sysctl net.ipv4.ip_local_port_range net.ipv4.tcp_tw_reuse net.ipv4.tcp_max_tw_buckets
```

- TIME-WAIT는 **목적지 하나에 몰렸는지**가 중요하다. 전체 개수가 많아도 목적지가 흩어져 있으면 포트는 남는다.
- CLOSE-WAIT는 개수보다 **증가 추세**를 본다. 계속 늘기만 하면 누수다.

### 2. CLOSE-WAIT 누수를 코드에서 막는다

Java — 모든 경로에서 닫는다.

```java
// 나쁜 예: 예외가 나면 close()를 건너뛴다 -> 상대가 FIN을 보내면 CLOSE-WAIT로 남는다
Socket s = new Socket(host, port);
process(s.getInputStream());      // 여기서 예외
s.close();

// 좋은 예: try-with-resources는 예외 경로에서도 close()를 부른다
try (Socket s = new Socket(host, port)) {
    InputStream in = s.getInputStream();
    byte[] buf = new byte[8192];
    int n;
    while ((n = in.read(buf)) != -1) {   // -1 = 상대 FIN. 여기서 루프를 끝내야 한다
        handle(buf, n);
    }
}   // 여기서 close() -> 내 FIN 전송 -> LAST-ACK -> CLOSED
```

Node.js — `allowHalfOpen`을 켰다면 직접 끝낸다.

```js
const net = require('node:net');
const server = net.createServer({ allowHalfOpen: true }, (sock) => {
  sock.on('data', (d) => { /* 요청 처리 */ });
  sock.on('end', () => {
    // 상대 FIN. allowHalfOpen: true면 Node가 자동으로 FIN을 보내지 않는다
    sock.end(finalResponse);   // 이걸 빠뜨리면 이 소켓은 CLOSE-WAIT에 남는다
  });
});
```

### 3. TIME-WAIT로 인한 포트 고갈을 막는다

순서대로 적용한다.

1. **연결을 재사용한다.** HTTP keep-alive, 커넥션 풀(35번). 대부분 이것으로 끝난다.
2. **누가 먼저 닫을지 정한다.** 먼저 닫는 쪽이 TIME-WAIT를 진다. 포트가 귀한 쪽(클라이언트·LB)이 먼저 닫지 않게 프로토콜을 설계한다(Bernat 2014).
3. **4-튜플 공간을 넓힌다.** 목적지 포트·IP를 여러 개로, 출발 IP를 여러 개로, `ip_local_port_range`를 넓힌다.
4. 클라이언트 쪽에서 `tcp_tw_reuse=1`을 검토한다. 타임스탬프가 켜져 있어야 한다.
5. `SO_LINGER {1, 0}`으로 RST 종료는 최후의 수단이다. 보내지 않은 데이터가 버려진다(19번).

- 출발 IP를 여러 개 쓸 때 `bind(IP, 0)`으로 먼저 고르면 그 시점에 포트를 예약해 버린다.
  - 리눅스 `IP_BIND_ADDRESS_NO_PORT`(4.2+)는 포트 선택을 `connect()`까지 미뤄, 4-튜플이 겹치지 않는 한 같은 출발 포트를 공유하게 한다(IP_BIND_ADDRESS_NO_PORT(2const)).

### 4. 서버 재시작 실패를 막는다

```c
int on = 1;
setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);   /* bind 전에 */
bind(lfd, (struct sockaddr *)&addr, sizeof addr);
listen(lfd, 128);
```

## 장애 시나리오와 대처

### 1. 외부 호출이 `Cannot assign requested address`로 실패한다 — 임시 포트 고갈

- **현상**: 트래픽이 늘자 외부 API·DB 호출이 간헐적으로 즉시 실패한다. 상대 서버는 멀쩡하다.
- **보이는 형태**
  - errno `EADDRNOTAVAIL`, 메시지 "Cannot assign requested address".
  - Node `Error: connect EADDRNOTAVAIL`. 현재 OpenJDK는 `EADDRNOTAVAIL`을 `java.net.BindException`으로 바꿔 던진다(`src/java.base/unix/native/libnio/ch/Net.c` `handleSocketError`).
  - `ss -tan state time-wait`의 목적지가 한두 곳에 몰려 있고 개수가 수만이다.
- **원인**: 요청마다 새 연결을 열고 이쪽이 먼저 닫는다. 각 포트가 60초씩 TIME-WAIT에 묶여 같은 목적지용 임시 포트(기본 28,232개)가 바닥났다.
- **대처**
  - HTTP 클라이언트·DB 드라이버의 커넥션 풀·keep-alive를 켠다(근본).
  - 급하면 `ip_local_port_range`를 넓히고, 클라이언트에서 `tcp_tw_reuse=1`을 검토한다.
  - 목적지 IP·포트를 여러 개로 늘린다.

### 2. 며칠 뒤 `Too many open files` — CLOSE-WAIT 누수

- **현상**: 배포 후 시간이 지나면서 서버가 새 연결을 못 받는다. 재시작하면 한동안 괜찮다.
- **보이는 형태**
  - `accept()`·`socket()`이 `EMFILE`. Java `java.net.SocketException: Too many open files`, Node `Error: accept EMFILE`.
  - `ss -tanp state close-wait`의 개수가 특정 프로세스에서 단조 증가한다.
  - `/proc/<PID>/fd` 개수가 `open files` 한도에 붙어 있다.
- **원인**: 상대(클라이언트, 업스트림, DB)가 FIN을 보냈는데 앱이 그 소켓을 `close()`하지 않았다. 예외 경로의 누락, 반납 안 한 풀 연결, 닫지 않은 응답 스트림이 흔하다.
- **대처**
  - `ss -tanp`로 CLOSE-WAIT의 **상대 주소**를 보고 어느 클라이언트 코드인지 좁힌다.
  - 그 경로의 자원 해제를 try-with-resources·`finally`·`pipeline()`으로 고친다.
  - `ulimit -n`을 올리는 것은 시간을 버는 것일 뿐이다. 누수는 계속된다.

### 3. 서버 재시작이 `Address already in use`로 실패한다

- **현상**: 프로세스를 재시작하자마자 bind가 실패한다. 1분쯤 뒤에는 성공한다.
- **보이는 형태**: `bind: Address already in use`(`EADDRINUSE`). `ss -tan state time-wait '( sport = :8080 )'`에 옛 연결이 보인다.
- **원인**: 이전 프로세스의 연결들이 :8080을 로컬 포트로 쓴 채 TIME-WAIT에 남아 있다. 리스닝 소켓에 `SO_REUSEADDR`가 없다.
- **대처**: bind 전에 `SO_REUSEADDR`를 켠다(socket(7)). 그래도 실패하면 다른 프로세스가 실제로 LISTEN 중인지 `ss -ltnp`로 확인한다.

### 4. TIME-WAIT 수만 개가 경보를 울린다 — 대개 정상

- **현상**: 모니터링이 서버의 TIME-WAIT 5만 개를 경보로 띄웠다. 서비스는 정상이다.
- **보이는 형태**: TIME-WAIT의 로컬 포트가 서버의 리스닝 포트(:443 등)이고, 원격 주소가 다양하다.
- **원인**: 서버가 먼저 닫는 프로토콜(HTTP keep-alive idle 종료 등)이라 서버 쪽에 TIME-WAIT가 쌓였다. 서버 쪽 TIME-WAIT는 포트를 소비하지 않고 fd도 없다. 메모리 비용도 작다(Bernat 2014).
- **대처**
  - 대개 아무것도 하지 않는다. `tcp_max_tw_buckets`를 넘지 않는지만 본다. 넘으면 커널이 즉시 파기하고 경고를 남긴다(tcp(7)).
  - `tcp_tw_recycle`류 조작은 하지 않는다(제거됨, NAT 사용자 차단 문제).

## 핵심 문장

- TIME-WAIT는 **먼저 닫은 쪽**이 지는 정상 상태다. 마지막 ACK를 다시 보낼 수 있게 하고, 옛 연결의 늦은 세그먼트가 같은 4-튜플의 새 연결을 오염시키지 않게 한다(2MSL, 리눅스 60초).
- TIME-WAIT는 fd를 잡지 않는다. 문제는 **클라이언트가 한 목적지로 짧은 연결을 대량으로** 열 때의 임시 포트 고갈(`EADDRNOTAVAIL`)이고, 해법의 1순위는 연결 재사용이다.
- CLOSE-WAIT는 상대가 닫았는데 **내 앱이 close()를 안 한** 상태다. 커널에 이를 끝낼 타이머가 없어 앱이 닫을 때까지 남는다.
- CLOSE-WAIT는 fd를 잡는다. 계속 늘면 버그이고, 끝내 `EMFILE`(Too many open files)이 된다.
- `ss`의 상태별 개수와 상대 주소, 프로세스(-p)를 보면 둘 중 무엇이 어디서 생기는지 가를 수 있다.

## 관련 주제·근거

- 선행: [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — 4-way 종료·상태 기계·FIN과 RST
- 연결
  - [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md) — 끝난 줄 모르는 연결(half-open) 찾기
  - [23-socket-api](../23-socket-api/2-summary.md) — `bind`·`connect`·`close`와 fd
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 커넥션 풀로 TIME-WAIT 줄이기, idle timeout 정렬
  - [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md) — 종료 시 연결을 정리하는 순서
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) — 4-튜플 조회
- RFC
  - RFC 9293 (TCP) <https://www.rfc-editor.org/rfc/rfc9293> — §3.3.2 Figure 5 상태 기계 · §3.4.2 MSL 2분 · §3.5.2 연결 없는 쪽의 RST 응답 · §3.6 Case 2(수동 종료)·Figure 12 · §3.6.1 TIME-WAIT 2MSL(MUST-13), TIME-WAIT에서 새 SYN 허용(MAY-2), RFC 6191 권고(SHLD-4)
  - RFC 6191 (Reducing the TIME-WAIT State Using TCP Timestamps, BCP) <https://www.rfc-editor.org/rfc/rfc6191>
  - RFC 1337 (TIME-WAIT Assassination Hazards in TCP) <https://www.rfc-editor.org/rfc/rfc1337>
- Linux
  - tcp(7) — `tcp_max_tw_buckets`, `tcp_tw_reuse`, `tcp_tw_recycle`(2.4~4.11), `tcp_rfc1337`, `tcp_fin_timeout` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - 커널 문서 ip-sysctl — `tcp_tw_reuse`(기본 2), `tcp_tw_reuse_delay`, `tcp_max_tw_buckets`, `tcp_fin_timeout`(orphan FIN-WAIT-2), `ip_local_port_range`(32768~60999) <https://docs.kernel.org/networking/ip-sysctl.html>
  - `include/net/tcp.h` — `TCP_TIMEWAIT_LEN (60*HZ)` <https://github.com/torvalds/linux/blob/master/include/net/tcp.h>
  - connect(2) — `EADDRNOTAVAIL` <https://man7.org/linux/man-pages/man2/connect.2.html>
  - accept(2) — `EMFILE` <https://man7.org/linux/man-pages/man2/accept.2.html> · getrlimit(2) — `RLIMIT_NOFILE` <https://man7.org/linux/man-pages/man2/getrlimit.2.html>
  - socket(7) — `SO_REUSEADDR` <https://man7.org/linux/man-pages/man7/socket.7.html>
  - IP_BIND_ADDRESS_NO_PORT(2const) <https://man7.org/linux/man-pages/man2/IP_BIND_ADDRESS_NO_PORT.2const.html>
  - ss(8) — 상태 필터, `bucket`(time-wait 미니 소켓), `-p` <https://man7.org/linux/man-pages/man8/ss.8.html>
- Node.js `net` 문서 — `allowHalfOpen` <https://nodejs.org/api/net.html>
- Vincent Bernat, "Coping with the TCP TIME-WAIT state on busy Linux servers"(2014) <https://vincent.bernat.ch/en/blog/2014-tcp-time-wait-state-linux>
- 교재: Stevens, 『TCP/IP Illustrated Vol.1』 2판 13장 "TCP Connection Management"
