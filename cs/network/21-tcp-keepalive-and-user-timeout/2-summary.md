# network/21-tcp-keepalive-and-user-timeout — 죽은 연결을 "먼저 말을 걸어" 찾아내는 법 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

19번 노트의 결론은 이것이었다.\
TCP는 **말을 걸어야** 상대가 없다는 걸 안다.\
아무것도 오가지 않는 연결은 상대가 사라져도, 중간 장비가 연결 기록을 지워도 ESTABLISHED로 남는다.

이 노트는 "언제, 누가, 어떻게 말을 걸게 할지"를 다룬다.\
상황은 둘로 나뉜다.

```text
  (가) 조용한 연결 — 보낼 것도 받을 것도 없다
       상대 소멸·NAT 기록 삭제 -> 아무도 모른다 -> read()는 영원히 대기
       도구: TCP keepalive, 앱 heartbeat

  (나) 보내는 중인 연결 — 내가 보낸 데이터가 ACK를 못 받는다
       write()는 성공 (커널 버퍼에 넣었을 뿐) -> 커널이 재전송만 반복
       -> 리눅스 기본으로 약 15분 이상 뒤에야 ETIMEDOUT
       도구: TCP_USER_TIMEOUT, 앱 요청 타임아웃
```

쉬운 예: 무전기다.\
오래 조용하면 "잘 들리나, 오버"라고 물어본다(keepalive).\
내가 말했는데 대답이 없으면, 몇 번 다시 말해 보고 정해진 시간이 지나면 채널을 끊는다(user timeout).

똑같은 구조다.\
keepalive는 **조용할 때** 확인하고, user timeout은 **보낸 게 확인 안 될 때** 포기 시점을 정한다.

실무 예:
- DB 커넥션 풀의 연결이 방화벽 idle timeout으로 조용히 끊겼다. 다음 쿼리가 `Connection reset`이나 긴 멈춤을 겪는다.
- 메시지 브로커 컨슈머가 몇 시간째 메시지를 못 받는데 연결은 ESTABLISHED로 보인다.
- 상대 서버 전원이 나갔는데 이쪽 요청이 15분 넘게 멈춰 있다.

## 동작·원리

### 1. TCP keepalive — 조용한 연결에 탐침을 보낸다

```text
  A (keepalive 켬)                                  B
  마지막 데이터·ACK 이후 KEEPIDLE 동안 아무것도 없음
  --- probe <SEQ=SND.NXT-1><ACK> ----------------->   (이미 받은 번호라 윈도 밖)
  <-- ACK -----------------------------------------   살아 있음 -> 타이머 리셋

  B가 재부팅됨 (연결 정보 없음)
  --- probe ------------------------------------->
  <-- RST -----------------------------------------   A: ECONNRESET으로 종료

  B가 사라짐 / 경로 단절 (응답 없음)
  --- probe ---X   (KEEPINTVL 뒤) --- probe ---X  ... KEEPCNT번
  A: 연결 종료, 앱에는 ETIMEDOUT
```

- probe는 보통 `SEG.SEQ = SND.NXT − 1`로 보낸다. 이미 받은 번호이므로 상대는 윈도 밖 세그먼트에 대한 규칙대로 ACK를 돌려준다(RFC 1122 §4.2.3.6 DISCUSSION, RFC 9293 §3.8.4).
- 데이터 없는 probe를 보내야 한다(SHOULD, SHLD-12). 오래된 구현과의 호환을 위해 쓰레기 1바이트를 넣는 설정도 허용한다(MAY-6).

**RFC 규칙 — 선택 기능이고, 기본은 꺼짐**

- keepalive는 구현해도 되고 안 해도 된다(MAY-5). RFC 1122는 좋은 연결을 끊을 수 있고, 대역폭을 쓰고, 비용이 들 수 있다는 이유로 TCP 명세에 넣지 않았다고 설명한다.
- 구현하면 연결별로 켜고 끌 수 있어야 하고(MUST-24), **기본은 꺼짐**이어야 한다(MUST-25).
- 보낸 데이터가 대기 중이 아니고, 일정 시간 동안 데이터·ACK를 받지 않았을 때만 보낸다(MUST-26).
- 간격은 설정할 수 있어야 하고(MUST-27), 기본값은 **2시간 이상**이어야 한다(MUST-28).
- probe 하나의 무응답을 연결 사망으로 보면 안 된다(MUST-29). 데이터 없는 ACK는 신뢰성 있게 전달되지 않기 때문이다.

**리눅스 기본값**

```text
  net.ipv4.tcp_keepalive_time   = 7200   (초, 첫 probe까지 idle)     소켓별: TCP_KEEPIDLE
  net.ipv4.tcp_keepalive_intvl  = 75     (초, probe 간격)           소켓별: TCP_KEEPINTVL
  net.ipv4.tcp_keepalive_probes = 9      (무응답 허용 횟수)          소켓별: TCP_KEEPCNT
  -> 끊긴 연결을 알아채기까지: 7200 + 75 × 9 = 7875초 ≈ 2시간 11분
```

- keepalive는 소켓에 `SO_KEEPALIVE`를 켰을 때만 동작한다(tcp(7)).
- tcp(7)도 "실제 연결 추적 장치와 앱 타임아웃은 이보다 훨씬 짧을 수 있다"고 경고한다.
- `TCP_KEEPIDLE`·`TCP_KEEPINTVL`·`TCP_KEEPCNT`는 리눅스 전용이다. 이식성 있는 코드에서는 쓰지 말라고 적혀 있다(tcp(7)).

### 2. 왜 기본 2시간은 실무에서 쓸모없나 — 중간 장비의 idle timeout

```text
  클라이언트 ----- [NAT/방화벽/LB: idle 350초면 연결 기록 삭제] ----- 서버
                                    |
  t=0      마지막 요청
  t=350s   장비가 기록 삭제  (양 끝은 모름)
  t=7200s  첫 keepalive probe  -> 이미 늦음
  t=1000s(예시) 다음 요청 -> 장비가 모르는 연결 -> RST 또는 drop
```

- 중간 장비는 "조용한 연결"을 일정 시간 뒤 잊는다.
  - AWS NLB의 TCP idle timeout 기본값은 350초다(60~6000초 설정 가능). 그 뒤 데이터를 보내면 클라이언트가 **RST**를 받는다. keepalive 패킷은 idle 타이머를 다시 시작시킨다(AWS NLB 문서).
  - RFC 5382는 NAT가 established TCP 연결을 idle로 버릴 때 그 시간이 **2시간 4분 이상**이어야 한다고 정한다(MUST NOT be less, REQ-5). 하지만 실제 장비·클라우드 설정은 이보다 짧은 경우가 많다(위 NLB 예).
  - 리눅스 conntrack의 established 기본 시간은 5일이다(`nf_conntrack_tcp_timeout_established` 432000, 커널 문서).
- 그래서 keepalive를 켜도 **KEEPIDLE이 경로의 가장 짧은 idle timeout보다 짧아야** 의미가 있다.
  - keepalive의 두 역할: 연결 기록을 **살려 두기**(장비 idle 타이머 리셋), 죽은 연결을 **찾아내기**.

### 3. keepalive가 못 하는 것 — 보내는 중일 때

```text
  A: write(요청)  -> 성공 (커널 송신 버퍼에 들어감)
  A 커널: 전송 ---X  재전송 ---X  재전송 ---X ...   (지수 백오프, 최대 15회 재전송 — RTO가 크면 더 적다)
         "보낸 데이터가 대기 중"이므로 keepalive probe는 안 나감 (MUST-26)
  A 앱:  read(응답)로 대기 중... 에러 없음
  약 15분+ 뒤: tcp_retries2 초과 -> ETIMEDOUT
```

- `write()`의 성공은 "상대가 받았다"가 아니라 "**내 커널 버퍼에 들어갔다**"다.
- 데이터가 대기 중이면 keepalive는 동작하지 않는다(RFC MUST-26). 리눅스에서는 이때 재전송 타이머("on")가 돌고 keepalive는 쉰다(Cloudflare).
- 포기 시점은 `tcp_retries2`(기본 15)가 정한다. 15는 고정 횟수가 아니라 시간 계산용 값이다. 커널은 "RTO 200ms에서 시작해 15번 재전송"한 가상 시간(924.6초)을 넘긴 첫 RTO에서 포기한다(커널 문서 ip-sysctl). 그래서 924.6초는 하한이고, RTO가 크면 재전송 횟수는 15보다 적다. tcp(7) 기준 약 13~30분이다. Cloudflare 측정에서는 약 940초였다.
- 커리큘럼의 "retries2 ≈ 15분"은 커널 문서의 924.6초 하한과 맞는다.

### 4. TCP_USER_TIMEOUT — "ACK 없이 버틸 최대 시간"

```text
  setsockopt(fd, IPPROTO_TCP, TCP_USER_TIMEOUT, &ms, sizeof ms);

  보낸 데이터가 ACK 없이 ms를 넘김                -> 커널이 연결을 닫고 ETIMEDOUT
  zero window 때문에 버퍼 데이터를 못 보낸 채 ms를 넘김 -> 같음
  keepalive와 함께 쓰면                          -> keepalive 실패 판정도 이 값이 결정
```

- 값은 밀리초이고, 0이면 시스템 기본(재전송 한도)을 쓴다(tcp(7)).
- 적용 범위(tcp(7))
  - 보낸 데이터가 ACK 없이 남아 있는 시간, **또는** zero window 때문에 보내지 못한 시간이 대상이다(17번).
  - 동기화된 상태(ESTABLISHED, FIN-WAIT-1·2, CLOSE-WAIT, CLOSING, LAST-ACK)에서만 효과가 있다.
  - `SO_KEEPALIVE`와 함께 쓰면 keepalive 실패로 연결을 닫는 시점도 이 값이 정한다(override).
  - **재전송 시점이나 keepalive probe를 보내는 시점은 바꾸지 않는다.** 포기 시점만 바꾼다.
  - 리스닝 소켓에 설정하면 `accept()`로 받은 소켓이 물려받는다.
  - 리눅스 2.6.37부터 있다.
- 줄이면 빨리 실패하고(fail fast), 늘리면 긴 단절도 버틴다(tcp(7)).
- 개념의 뿌리는 RFC 793의 연결별 "user timeout"이다. RFC 5482는 이 값을 상대에게 **알리는** TCP 옵션(UTO, kind 28)을 정의한다. 받은 쪽은 권고로만 쓴다(RFC 5482 §1·§3).
- keepalive와 같이 쓸 때의 권고
  - Cloudflare: `TCP_USER_TIMEOUT` ≈ `KEEPIDLE + KEEPINTVL × KEEPCNT`로 맞춘다. 그래야 KEEPCNT가 의미를 가진다.
  - RFC 5482 §4.2는 반대 방향을 경고한다. UTO 옵션을 쓰는 연결에서 keepalive를 켜면 keepalive 타이머를 user timeout보다 크게 두라고 한다(MUST). 일부 구현은 keepalive에 다른 중단 정책을 써서, 버틸 수 있었던 연결을 끊을 수 있기 때문이다.
  - 두 권고는 전제가 다르다. 리눅스에서는 user timeout이 keepalive 판정까지 덮어쓰므로, 두 값의 관계를 의식해서 함께 정한다.

### 5. 앱 heartbeat — 끝에서 끝까지, 앱까지 확인한다

```text
  TCP keepalive가 확인하는 것:   클라이언트 커널 <-> (가장 가까운 TCP 종단) 커널
  앱 heartbeat가 확인하는 것:    클라이언트 앱  <-> 서버 앱 (프록시 너머까지)

  클라이언트 --TCP-- [L7 프록시 / TLS 종단] --TCP-- 서버 앱
             ^ keepalive는 여기까지만           ^ 서버 앱이 멈춰도(교착·GC) 커널은 ACK함
```

- TCP keepalive는 **커널끼리** 확인한다. 상대 프로세스가 교착·무한 GC로 멈춰 있어도 상대 커널은 probe에 ACK한다.
- L7 프록시·TLS 종단이 중간에 있으면, keepalive는 그 프록시까지만 확인한다.
- 그래서 오래 사는 연결에는 **앱 수준 heartbeat**를 둔다.
  - HTTP/2 PING 프레임은 최소 RTT를 재거나 idle 연결이 여전히 동작하는지 확인하는 수단이다(RFC 9113 §6.7).
  - gRPC는 HTTP/2 PING으로 keepalive를 한다. 클라이언트 기본은 꺼짐, 서버 기본 2시간, 응답 대기 기본 20초다. 너무 자주 ping하면 서버가 `too_many_pings` GOAWAY로 끊는다(gRPC keepalive 가이드).
  - WebSocket Ping/Pong: Ping을 받으면 Pong으로 답해야 한다(MUST, RFC 6455 §5.5.2). Ping은 keepalive로도, 상대 응답성 확인으로도 쓸 수 있다.
  - 메시지 브로커·DB 프로토콜도 자체 heartbeat를 두는 경우가 많다(예: AMQP 0-9-1 heartbeat, RabbitMQ 문서 "Detecting Dead TCP Connections with Heartbeats").

### 6. 세 도구의 역할 정리

```text
  도구                 확인 범위           언제 동작          잡아내는 것                      비용
  ------------------   ----------------   ----------------   ------------------------------   ---------------
  TCP keepalive        커널 <-> 커널       연결이 idle일 때    상대 소멸·재부팅, NAT 기록 유지    매우 작음
  TCP_USER_TIMEOUT     커널 (내 쪽)        데이터 미확인일 때  보내는 중의 단절 (빠른 포기)        없음 (포기 시점만)
  앱 heartbeat/타임아웃  앱 <-> 앱           앱이 정한 주기      위 전부 + 상대 앱 정지, 프록시 너머  프로토콜 설계 필요
```

- 셋은 겹치지 않는다. 오래 사는 연결에는 보통 **keepalive(또는 heartbeat) + user timeout(또는 요청 타임아웃)**을 같이 둔다.

## 쓰이는 자료구조·알고리즘

- **타이머** — 연결마다 keepalive 타이머, 재전송 타이머, persist 타이머가 있다.
  - 리눅스는 재전송·persist(zero window probe)를 한 타이머(`icsk_retransmit_timer`)에 용도를 바꿔 가며 걸고, keepalive는 별도 타이머(`icsk_keepalive_timer`)에 건다(`include/net/inet_connection_sock.h`).
  - `ss -o`는 이 중 하나를 골라 `on`·`persist`·`keepalive` 순서의 우선순위로 보여 준다(ss(8), `net/ipv4/inet_diag.c`). 그래서 재전송 중에는 `keepalive`가 아니라 `on`이 보인다.
  - 수십만 연결의 타이머를 다루는 구조(타이머 휠, 힙)는 data-structure `timer-structures` — 미작성([영역 표](../../data-structure/curriculum.md)). [힙](../../data-structure/07-heap/2-summary.md) 참고.
- **실패 탐지기(failure detector)** — "N번 연속 무응답이면 죽은 것으로 본다"는 규칙이다. 간격 × 횟수가 **탐지 시간**, 한 번의 무응답을 사망으로 보지 않는 것이 **오탐 방지**다(MUST-29).
  - 분산 시스템의 heartbeat 기반 실패 탐지와 같은 트레이드오프다. 빨리 잡으면 오탐이 늘고, 오탐을 줄이면 늦게 잡는다.
- **상태 기계** — 연결 상태(19번)와 별개로 "idle → probing → dead" 작은 상태 기계가 keepalive를 돈다.

## 적용 — 풀어나가는 법

### 1. 경로의 가장 짧은 idle timeout부터 찾는다

```text
  예시 경로:  앱 풀 --> NAT GW --> LB (350s) --> 서버 (keepalive 7200s)
  가장 짧은 값 = 350s
  -> KEEPIDLE < 350s (예: 60~120s), 풀의 idle 연결 폐기 시간 < 350s
```

- 클라우드 LB·NAT·방화벽의 idle timeout 문서를 확인한다. 값은 제품·설정마다 다르다.
- 커넥션 풀의 idle 폐기 시간을 그보다 짧게 둔다(35번).

### 2. 코드에서 켠다

Java — `SO_KEEPALIVE`와 세부 값(JDK 11+ `jdk.net.ExtendedSocketOptions`).

```java
import jdk.net.ExtendedSocketOptions;

Socket s = new Socket();
s.setKeepAlive(true);                                          // SO_KEEPALIVE
s.setOption(ExtendedSocketOptions.TCP_KEEPIDLE, 60);           // 초 (예시)
s.setOption(ExtendedSocketOptions.TCP_KEEPINTERVAL, 10);       // 초 (예시)
s.setOption(ExtendedSocketOptions.TCP_KEEPCOUNT, 3);           // 회 (예시)
s.connect(new InetSocketAddress(host, port), 3_000);
s.setSoTimeout(30_000);   // read 타임아웃: 앱 수준 방어선 (read에만 적용)
```

- JDK의 `ExtendedSocketOptions`에는 `TCP_USER_TIMEOUT`이 없다(Java SE 21 문서 기준). Netty epoll 전송은 `EpollChannelOption.TCP_USER_TIMEOUT`을 제공한다.

Node.js — `setKeepAlive`.

```js
const net = require('node:net');
const sock = net.connect({ host, port, keepAlive: true, keepAliveInitialDelay: 60_000 });
// 또는 sock.setKeepAlive(true, 60_000)
// Node는 v13.12/v12.17부터 keepalive를 켜면 TCP_KEEPCNT=10, TCP_KEEPINTVL=1초를 기본으로 설정한다
sock.setTimeout(30_000);
sock.on('timeout', () => sock.destroy(new Error('idle timeout')));
```

- `initialDelay`·`interval`은 밀리초로 받지만 커널에는 초 단위로 내림해 넣는다(Node `net` 문서).
- 최신 문서(v26.4.0 추가)에는 `interval`·`count` 인자도 있다. 쓰는 Node 버전의 문서를 확인한다.

C — 세부 값과 user timeout.

```c
int on = 1, idle = 60, intvl = 10, cnt = 3;           /* 예시 값 */
unsigned int uto = (idle + intvl * cnt) * 1000;        /* ms, Cloudflare 권고식 */
setsockopt(fd, SOL_SOCKET,  SO_KEEPALIVE,     &on,    sizeof on);
setsockopt(fd, IPPROTO_TCP, TCP_KEEPIDLE,     &idle,  sizeof idle);
setsockopt(fd, IPPROTO_TCP, TCP_KEEPINTVL,    &intvl, sizeof intvl);
setsockopt(fd, IPPROTO_TCP, TCP_KEEPCNT,      &cnt,   sizeof cnt);
setsockopt(fd, IPPROTO_TCP, TCP_USER_TIMEOUT, &uto,   sizeof uto);
```

### 3. 동작을 확인한다

```bash
# keepalive 타이머가 돌고 있나: timer:(keepalive,58sec,0)
ss -tno state established dst 10.0.0.9

# probe가 실제로 나가나: 데이터 길이 0 또는 1의 ACK가 KEEPIDLE 간격으로
tcpdump -ni eth0 'host 10.0.0.9 and tcp[tcpflags] == tcp-ack' -c 20

# 시스템 기본값
sysctl net.ipv4.tcp_keepalive_time net.ipv4.tcp_keepalive_intvl net.ipv4.tcp_keepalive_probes

# keepalive로 보낸 probe 수 (시스템 전체)
nstat -az TcpExtTCPKeepAlive
```

- `ss -o`의 타이머 이름이 `keepalive`가 아니라 `on`이면 데이터 재전송 중이다. 이때는 keepalive가 쉬고 user timeout·재전송 한도가 적용된다.

## 장애 시나리오와 대처

### 1. keepalive를 켰는데도 idle 연결이 끊긴다 — 기본 7200초 > 장비 idle timeout

- **현상**: 몇 분 쉰 풀 연결의 첫 요청이 실패한다. keepalive는 켜져 있다.
- **보이는 형태**
  - `ECONNRESET`(Java `SocketException: Connection reset`, Node `read ECONNRESET`), 또는 요청이 멈췄다가 한참 뒤 `ETIMEDOUT`.
  - tcpdump에 idle 중 probe가 한 번도 안 보인다.
  - `sysctl net.ipv4.tcp_keepalive_time`이 7200이다.
- **원인**: 첫 probe까지 2시간인데 경로 장비(예: AWS NLB 350초)가 그 전에 연결 기록을 지웠다. 장비에 따라 이후 패킷에 RST를 주거나(NLB) 조용히 버린다.
- **대처**
  - `TCP_KEEPIDLE`을 경로의 가장 짧은 idle timeout보다 짧게 둔다(소켓별 또는 sysctl).
  - 풀의 idle 연결 폐기 시간을 장비 timeout보다 짧게 두고, 멱등 요청은 한 번 재시도한다.

### 2. 상대가 사라졌는데 `write()`는 성공하고, 15분 뒤에야 `ETIMEDOUT`

- **현상**: 요청을 보냈는데 응답도 에러도 없이 오래 멈춘다. 결국 연결 타임아웃 에러가 난다.
- **보이는 형태**
  - `ss -tio`에 `timer:(on,…,N)`에서 N이 계속 오르고 `Send-Q`가 쌓여 있다.
  - 약 15분 이상 뒤 `ETIMEDOUT`. `nstat`의 `TcpExtTCPAbortOnTimeout`이 오른다.
- **원인**
  - `write()`는 커널 버퍼에 넣었을 뿐이다.
  - 데이터가 대기 중이라 keepalive는 동작하지 않는다(MUST-26).
  - 포기 시점은 `tcp_retries2`(하한 약 924.6초)가 정한다.
- **대처**
  - `TCP_USER_TIMEOUT`을 요구 사항에 맞게(예: 30초 (예시)) 건다.
  - 앱 수준 요청 타임아웃을 반드시 둔다.

### 3. 연결은 살아 있는데 컨슈머가 아무것도 못 받는다 — 상대 앱 정지 또는 프록시 너머

- **현상**: 구독·스트리밍 연결이 ESTABLISHED인데 몇 시간째 메시지가 없다. keepalive는 정상이다.
- **보이는 형태**: keepalive probe에 ACK가 온다(tcpdump). 상대 서버는 스레드 교착 상태이거나, 중간 L7 프록시 뒤의 업스트림이 끊겼다.
- **원인**: TCP keepalive는 커널끼리, 가장 가까운 TCP 종단까지만 확인한다. 상대 앱의 정지나 프록시 너머 단절은 보지 못한다.
- **대처**
  - 앱 수준 heartbeat(HTTP/2 PING, gRPC keepalive, WebSocket Ping/Pong, 브로커 heartbeat)를 켠다.
  - "마지막 메시지 수신 후 N초 무소식이면 재연결"하는 수신 타임아웃을 둔다.

### 4. heartbeat를 너무 자주 보내 연결이 끊긴다

- **현상**: gRPC 클라이언트가 keepalive를 짧게 설정한 뒤 주기적으로 연결이 끊기고 재연결된다.
- **보이는 형태**: GOAWAY 프레임의 debug data가 `too_many_pings`다.
- **원인**: 서버가 허용하는 최소 ping 간격(서버 기본 5분)보다 자주 ping했다(gRPC keepalive 가이드).
- **대처**: 클라이언트 keepalive 간격을 서버 허용치 이상으로 두거나, 서버의 허용 간격 설정을 함께 조정한다.

### 5. user timeout을 너무 짧게 잡아 멀쩡한 연결이 끊긴다

- **현상**: 순간적인 망 흔들림(수 초)마다 연결이 `ETIMEDOUT`으로 끊긴다.
- **보이는 형태**: 재전송 몇 번 만에 연결 종료. 경로의 RTT·RTO에 비해 `TCP_USER_TIMEOUT`이 너무 작다.
- **원인**: user timeout은 "ACK 없이 버틸 시간"이다. RTO 백오프 몇 번보다 짧으면 일시적 유실도 사망으로 판정한다.
- **대처**: 경로의 RTO와 허용 가능한 단절 시간을 고려해 정한다. keepalive와 함께 쓰면 `KEEPIDLE + KEEPINTVL × KEEPCNT`에 맞추는 권고(Cloudflare)를 출발점으로 삼는다.

## 핵심 문장

- TCP keepalive는 **조용한 연결**에 탐침을 보내 상대 소멸을 찾고, 중간 장비의 연결 기록을 살려 둔다. RFC상 선택 기능이고 기본은 꺼짐, 기본 간격은 2시간 이상이다.
- 리눅스 기본(7200초 + 75초 × 9)은 약 2시간 11분이라, 수 분 단위인 NAT·LB idle timeout 앞에서는 쓸모가 없다. KEEPIDLE을 경로의 가장 짧은 idle timeout보다 짧게 둔다.
- 데이터를 **보내는 중**에는 keepalive가 돌지 않는다. `write()` 성공은 커널 버퍼에 넣었다는 뜻일 뿐이고, 상대가 사라지면 재전송 한도(약 15분 이상) 뒤에야 `ETIMEDOUT`이다.
- `TCP_USER_TIMEOUT`은 "ACK 없이(또는 zero window로) 버틸 최대 시간"을 연결별로 정해 그 포기를 앞당긴다. keepalive의 실패 판정도 덮어쓴다.
- 커널끼리의 확인으로는 상대 앱 정지와 프록시 너머의 단절을 못 본다. 오래 사는 연결에는 앱 heartbeat와 요청 타임아웃을 함께 둔다.

## 관련 주제·근거

- 선행
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — half-open, "말을 걸어야 안다"
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — NAT·연결 추적의 idle timeout
- 연결
  - [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — 재전송 백오프와 `tcp_retries2`
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — zero window에도 걸리는 `TCP_USER_TIMEOUT`
  - [20-time-wait-and-close-wait](../20-time-wait-and-close-wait/2-summary.md) — 끝난 연결의 흔적
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 풀 idle timeout 정렬
  - [38-websocket-sse-long-lived](../38-websocket-sse-long-lived/2-summary.md) — 오래 사는 연결의 heartbeat
- RFC
  - RFC 9293 §3.8.4 (Keep-Alives: MAY-5, MUST-24~29, SHLD-12, MAY-6) · §3.8.3 (R1·R2) <https://www.rfc-editor.org/rfc/rfc9293>
  - RFC 1122 §4.2.3.6 TCP Keep-Alives (DISCUSSION: 명세에 넣지 않은 이유, probe 형식) <https://www.rfc-editor.org/rfc/rfc1122>
  - RFC 5482 (TCP User Timeout Option) <https://www.rfc-editor.org/rfc/rfc5482> — §1 user timeout 개념, §3 옵션(kind 28, 권고적), §4.2 keepalive와의 관계
  - RFC 5382 (NAT Behavioral Requirements for TCP) REQ-5 — established idle timeout ≥ 2시간 4분 <https://www.rfc-editor.org/rfc/rfc5382>
  - RFC 9113 §6.7 (HTTP/2 PING) <https://www.rfc-editor.org/rfc/rfc9113> · RFC 6455 §5.5.2~5.5.3 (WebSocket Ping/Pong) <https://www.rfc-editor.org/rfc/rfc6455>
- Linux
  - tcp(7) — `tcp_keepalive_time`(7200)·`intvl`(75)·`probes`(9), `TCP_KEEPIDLE`·`TCP_KEEPINTVL`·`TCP_KEEPCNT`, `TCP_USER_TIMEOUT`(2.6.37+, zero window 포함, keepalive override, accept 상속), `tcp_retries2` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - 커널 문서 ip-sysctl — `tcp_retries2`(924.6초 하한) <https://docs.kernel.org/networking/ip-sysctl.html>
  - 커널 문서 nf_conntrack-sysctl — `nf_conntrack_tcp_timeout_established`(432000) <https://docs.kernel.org/networking/nf_conntrack-sysctl.html>
  - 커널 문서 snmp_counter — `TcpExtTCPKeepAlive`, `TcpExtTCPAbortOnTimeout` <https://docs.kernel.org/networking/snmp_counter.html>
  - ss(8) — `-o` 타이머(`on`·`keepalive`·`persist`) <https://man7.org/linux/man-pages/man8/ss.8.html>
- 런타임·라이브러리
  - Java SE 21 `jdk.net.ExtendedSocketOptions` — `TCP_KEEPIDLE`·`TCP_KEEPINTERVAL`·`TCP_KEEPCOUNT`(JDK 11) <https://docs.oracle.com/en/java/javase/21/docs/api/jdk.net/jdk/net/ExtendedSocketOptions.html>
  - Node.js `net` — `setKeepAlive`, `keepAlive`·`keepAliveInitialDelay` <https://nodejs.org/api/net.html>
  - Netty `EpollChannelOption.TCP_USER_TIMEOUT` <https://netty.io/4.1/api/io/netty/channel/epoll/EpollChannelOption.html>
  - gRPC, "Keepalive" <https://grpc.io/docs/guides/keepalive/>
- AWS, Network Load Balancer — Connection idle timeout(350초, 이후 RST, keepalive가 타이머 리셋) <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/network-load-balancers.html>
- Cloudflare, "When TCP sockets refuse to die" — keepalive·`TCP_USER_TIMEOUT` 실험, 권고식, 약 940초 측정 <https://blog.cloudflare.com/when-tcp-sockets-refuse-to-die/>
- 교재: Stevens, 『TCP/IP Illustrated Vol.1』 2판 17장 "TCP Keepalive"
