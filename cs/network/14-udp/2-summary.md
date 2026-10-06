# network/14-udp — 헤더 8바이트짜리 전송 계층: 보내고 잊는다 — 정리 (힌트)

## 해결하는 문제

IP는 패킷을 **호스트**까지만 데려다 준다.\
그 호스트의 **어느 프로세스**에게 줄지는 모른다.

```text
  IP 패킷: dst=10.0.0.9            호스트 10.0.0.9
                                   +-----------------------------+
                                   | DNS 서버 (53번)              |
                  ----- ? ----->   | 게임 서버 (27015번)          |
                                   | 메트릭 수집기 (8125번)        |
                                   +-----------------------------+
  UDP 헤더의 dst port = 53  -> "DNS 서버에게"
```

UDP는 여기에 딱 두 가지만 더한다.
- **포트**: 어느 프로세스(소켓)에게 줄지.
- **체크섬**: 오는 길에 깨졌는지.

그 밖에는 아무것도 안 한다.\
연결 수립도, 재전송도, 순서 보장도, 혼잡 제어도 없다(HPBN "Building Blocks of UDP").

  - *UDP(User Datagram Protocol)*: IP 위에 포트와 체크섬만 얹은 전송 프로토콜이다. RFC 768(1980)이 정의하고, 문서 전체가 3쪽이다.
  - *데이터그램(datagram)*: 독립적으로 전달되는 메시지 한 덩어리다. 앞뒤 메시지와 아무 관계가 없다.

쉬운 예: 엽서다.\
주소와 받는 사람만 쓰면 바로 보낸다.\
도착했는지 알려 주지 않는다. 두 장을 보내면 순서가 바뀌어 올 수도 있다.\
대신 봉투를 뜯고 확인하는 절차가 없어 빠르다.

똑같은 구조다.\
UDP 데이터그램 한 개가 엽서 한 장이다.

실무 예:
- **DNS**: 질문 하나에 답 하나. 연결을 맺는 비용이 질의 자체보다 크다.
- **QUIC(HTTP/3)**: 신뢰성·암호화를 UDP 위에서 직접 구현한다(RFC 9000).
- **실시간 음성·영상·게임**: 늦게 온 데이터는 버리는 편이 낫다. 재전송을 기다리면 오히려 끊긴다.
- **메트릭·로그 전송**(StatsD 등): 몇 개 잃어도 괜찮고, 보내는 쪽이 막히면 안 된다.

## 동작·원리

### 헤더 — 8바이트

```text
   0      7 8     15 16    23 24    31
  +--------+--------+--------+--------+
  |   Source Port   |    Dest Port    |
  +--------+--------+--------+--------+
  |     Length      |    Checksum     |
  +--------+--------+--------+--------+
  |          data octets ...          |
```

(RFC 768 "Format")

- **Source Port**: 선택 사항이다. 답장을 받을 포트다. 안 쓰면 0이다.
- **Length**: 헤더를 포함한 전체 길이(바이트)다. 최솟값은 8이다.
  - 16비트라 최대 65535다. IPv4 헤더 20바이트와 UDP 헤더 8바이트를 빼면 IPv4에서 페이로드 최대는 65507바이트다(계산값).
- **Checksum**: 아래 절.

TCP 헤더(옵션 없이 20바이트)와 비교하면 시퀀스 번호·ACK·윈도·플래그가 모두 없다.

### 체크섬 — 가짜 헤더까지 덮는다

```text
  체크섬 계산 범위
  +------------------------------------------+
  | 가짜 헤더(pseudo header)                   |  <- 실제로 전송되지 않는다
  |   출발 IP | 도착 IP | 0 | 프로토콜(17) | UDP 길이 |
  +------------------------------------------+
  | UDP 헤더 (체크섬 칸은 0으로 두고 계산)        |
  +------------------------------------------+
  | 데이터 (홀수면 0 한 바이트 덧붙임)            |
  +------------------------------------------+
  => 16비트 1의 보수 합의 1의 보수
```

- 가짜 헤더에 IP 주소가 들어간다. 그래서 엉뚱한 호스트로 잘못 배달된 데이터그램도 잡아낸다(RFC 768).
- 계산 결과가 0이면 모두 1(`0xFFFF`)로 보낸다. **0은 "체크섬 안 씀"** 이라는 뜻이다(RFC 768).
- IPv4와 IPv6가 다르다.
  - IPv4: 체크섬은 선택이다. 하지만 호스트는 체크섬 생성·검증을 구현해야 하고(MUST), 기본값은 켜짐이어야 한다(MUST, RFC 1122 §4.1.3.4).
  - IPv6: 체크섬이 **필수**다. 체크섬 0인 UDP 패킷은 버려야 한다(RFC 8200 §8.1). 예외는 터널 프로토콜의 zero-checksum 모드뿐이다.
- 체크섬이 틀리면 UDP는 **조용히 버린다**(MUST, RFC 1122 §4.1.3.4). 애플리케이션은 모른다.
- 16비트 합은 약한 검사다. 중요한 데이터는 애플리케이션이 따로 무결성을 검사하거나 암호화 계층(DTLS·QUIC)에 맡긴다.

  - *1의 보수 합(one's complement sum)*: 16비트씩 더하고, 넘친 자리올림을 다시 맨 아래에 더하는 덧셈이다. TCP도 같은 방식을 쓴다.

### 포트로 소켓 찾기 (역다중화)

```text
  도착한 데이터그램: dst=10.0.0.9:53
        |
        v
  리눅스 udp_table
    hash  : (로컬 포트)                           -> 소켓 목록
    hash2 : (로컬 포트, 로컬 주소)                  -> 소켓 목록
    hash4 : (로컬 포트, 로컬 주소, 원격 포트, 원격 주소) -> connect()한 소켓
        |
        +-- 찾음   -> 그 소켓의 수신 버퍼에 넣기 (가득 차면 버림)
        +-- 못 찾음 -> ICMP Port Unreachable (SHOULD, RFC 1122 §4.1.3.1)
```

- 리눅스는 UDP 소켓을 위 세 해시 테이블에 건다(include/net/udp.h `struct udp_table` 주석). hash4는 리눅스 6.13에서 추가됐다. 그 전 커널은 hash·hash2 두 단계다(kernelnewbies Linux_6.13).
- 포트를 연 소켓이 없으면 ICMP Port Unreachable을 보내야 한다(SHOULD). `netstat -su`의 "packets to unknown port received"가 이 경우다.

### 데이터그램 경계가 지켜진다 — 대신 잘릴 수 있다

```text
  보냄:  send(100B)   send(300B)   send(50B)

  TCP:   recv() -> 앞 150B      recv() -> 나머지 300B     (경계 없음, 바이트 스트림)
  UDP:   recv() -> 100B         recv() -> 300B      recv() -> 50B   (한 번에 한 데이터그램)
         (순서는 바뀔 수 있고, 일부는 안 올 수 있다)
```

- UDP의 수신 호출은 한 번에 **데이터그램 하나**만 돌려준다(udp(7)).
- 내 버퍼가 데이터그램보다 작으면 **남는 부분은 버려진다**. 리눅스는 `MSG_TRUNC` 플래그로 알려 준다(udp(7)).
- 그래서 UDP 애플리케이션은 메시지 최대 크기를 정하고 그만큼 버퍼를 잡는다.

### 수신 버퍼 — 조용한 손실이 생기는 곳

```text
  NIC -> 커널 -> [ 소켓 수신 버퍼 (rcvbuf) ] -> recv() -> 애플리케이션
                  ^                        ^
                  빠르게 들어옴              느리게 꺼냄
                  버퍼가 가득 차면 새 데이터그램은 버린다
                  -> UdpRcvbufErrors(= netstat -su "receive buffer errors") +1
```

- TCP는 버퍼가 차면 수신 윈도를 줄여 **보내는 쪽을 멈춘다**(17번). UDP에는 그런 되먹임이 없다.
- 그래서 UDP는 소비가 느리면 **에러 없이** 데이터그램이 사라진다.
- 리눅스 커널은 이 경우 `UDP_MIB_RCVBUFERRORS`를 올린다(net/ipv4/udp.c `__udp_queue_rcv_skb`, `-ENOMEM`일 때).
- 수신 버퍼 크기는 `SO_RCVBUF`로 정한다.
  - 기본값은 `/proc/sys/net/core/rmem_default`, 상한은 `rmem_max`다(socket(7)).
  - 커널은 설정한 값을 **두 배**로 잡는다. 관리용 오버헤드 몫이다. `getsockopt`도 두 배 값을 돌려준다(socket(7)).

### 에러는 늦게, 그리고 connect한 소켓에만 온다

```text
  unconnected 소켓: sendto(10.0.0.9:9999) -> 성공 반환 (보냈다는 뜻일 뿐)
                    상대 포트 닫힘 -> ICMP Port Unreachable 도착 -> 리눅스: 보고 안 함
  connected 소켓:   connect(10.0.0.9:9999); send() -> 성공 반환
                    ICMP Port Unreachable 도착 -> 다음 send/recv가 ECONNREFUSED
```

- `send()`가 성공했다는 것은 "커널이 받아서 내보냈다"는 뜻이다. 상대가 받았다는 뜻이 아니다.
- 리눅스 커널은 ICMP로 온 에러를, `IP_RECVERR`를 켜지 않은 소켓에는 **connect된 소켓일 때만** 넘긴다(net/ipv4/udp.c `udp_err`).
- 그 에러는 **나중** 호출에서 튀어나온다. udp(7)도 ECONNREFUSED가 "이전에 보낸 패킷 때문일 수 있다"고 적는다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블(포트 → 소켓)** — 도착 데이터그램의 소켓을 찾는다. 리눅스는 포트, (포트·주소), (4-튜플) 세 단계 해시를 둔다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **큐(수신 버퍼)** — 데이터그램 단위 FIFO다. 가득 차면 새로 온 것을 버린다(tail drop). [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **1의 보수 체크섬** — 16비트 단위 합산. 증분 갱신이 쉬워서 NAT가 주소만 바꾸고 체크섬을 차이만큼 고칠 수 있다(11번).
- **애플리케이션 몫의 알고리즘** — UDP가 안 해 주는 것은 쓰는 쪽이 만든다.
  - 재전송·타임아웃(DNS 클라이언트의 재질의), 순서 번호(RTP), 혼잡 제어(QUIC).
  - RFC 8085는 UDP 애플리케이션도 혼잡 제어를 해야 한다고 권고한다(§3.1).

## 적용 — 풀어나가는 법

### 1. UDP를 고를지 먼저 판단한다

```text
  질문                                               예 -> UDP 쪽
  늦게 온 데이터가 쓸모없나? (실시간)                   음성·영상·게임
  요청·응답이 한 번에 끝나고 작은가?                     DNS
  신뢰성·순서를 내 방식으로 직접 만들 건가?              QUIC
  몇 개 잃어도 되고, 보내는 쪽이 막히면 안 되나?         메트릭·로그
  위 어느 것도 아니다                                  -> TCP를 쓴다
```

### 2. 메시지 크기를 경로 MTU 안에 둔다

- IP 단편화가 생기면 조각 하나만 잃어도 데이터그램 전체를 잃는다. 조각을 버리는 NAT·방화벽도 있다(RFC 8085 §3.2).
- 그래서 경로 MTU를 넘는 데이터그램을 보내지 않아야 한다(SHOULD NOT, RFC 8085 §3.2).
- 옛 DNS가 UDP 메시지를 512바이트로 제한하고, 넘으면 TC 비트를 세워 잘라 보낸 것도 같은 맥락이다(RFC 1035 §4.2.1).
- QUIC 클라이언트는 Initial 패킷을 담은 데이터그램을 1200바이트 이상으로 채워야 한다(MUST, RFC 9000 §14.1). 경로가 적어도 그 크기는 통과시키는지 확인하려는 것이다.

### 3. 수신 쪽 코드 — 버퍼 크기와 타임아웃

Java — 수신 버퍼를 키우고, 받기에 타임아웃을 건다.

```java
try (DatagramSocket sock = new DatagramSocket(8125)) {
    sock.setReceiveBufferSize(4 * 1024 * 1024);      // 4MB(예시). 커널 rmem_max에 막힐 수 있다
    System.out.println(sock.getReceiveBufferSize()); // 실제로 잡힌 값을 반드시 확인한다
    sock.setSoTimeout(5_000);                        // 5초(예시) 동안 안 오면 SocketTimeoutException

    byte[] buf = new byte[1500];                     // 최대 메시지 크기에 맞춘다
    DatagramPacket p = new DatagramPacket(buf, buf.length);
    while (true) {
        sock.receive(p);                             // 데이터그램 하나. 버퍼보다 크면 잘린다
        handleQuickly(p.getData(), p.getLength());   // 느린 작업은 다른 스레드로 넘긴다
        p.setLength(buf.length);
    }
}
```

Node.js — `dgram` 소켓. 메시지 하나가 `'message'` 이벤트 하나다.

```js
const dgram = require('node:dgram');
const sock = dgram.createSocket({ type: 'udp4', recvBufferSize: 4 * 1024 * 1024 }); // 4MB(예시)
sock.on('message', (msg, rinfo) => {
  queue.push(msg);                     // 이벤트 루프를 막지 않게 빨리 넘긴다
});
sock.on('error', (err) => {            // connect한 소켓이면 ECONNREFUSED가 여기로 온다
  console.error(err.code);
});
sock.bind(8125);
```

- 버퍼 크기는 **설정한 값이 아니라 실제로 잡힌 값**을 확인한다. `rmem_max`보다 크게 요청하면 조용히 깎인다(socket(7)).
- 수신 루프에서는 꺼내기만 하고 처리는 뒤로 미룬다. 수신이 느려지면 커널 버퍼가 넘친다.

### 4. 진단 명령

```bash
# UDP 누적 통계 — receive buffer errors가 오르는가
netstat -su
#   Udp:
#       7775704 packets received
#       95722 packets to unknown port received
#       3209 packet receive errors
#       3209 receive buffer errors          <- 수신 버퍼 넘침 (값은 작성 환경 예시)

# 같은 값을 카운터 이름으로
nstat -az UdpRcvbufErrors UdpInErrors UdpNoPorts UdpInCsumErrors

# 소켓별 버퍼·드롭 — rb=버퍼 크기, d=소켓 드롭 수
ss -uanm
#   skmem:(r0,rb212992,t0,tb212992,f0,w0,o0,bl0,d0)

# 버퍼 상한·기본값
sysctl net.core.rmem_max net.core.rmem_default

# 패킷 확인 (-K: 하드웨어 체크섬 오프로드 때문에 보내는 쪽이 "bad cksum"으로 보이는 것을 막는다)
tcpdump -ni any -K udp port 8125
```

- `ss`의 `d<sock_drop>`은 소켓에 넣기 전에 버려진 패킷 수다(ss(8)).
- 보내는 호스트에서 tcpdump를 뜨면 체크섬이 틀려 보일 수 있다. NIC가 체크섬을 나중에 채우기 때문이다(tcpdump(1) `--dont-verify-checksums` 설명).

## 장애 시나리오와 대처

### 1. 수신 버퍼 넘침 — 에러 없이 데이터가 사라진다

- **현상**: 메트릭 수집기의 그래프가 트래픽 피크 때만 실제보다 낮다. 게임·영상이 피크 때 튄다.
- **보이는 형태**
  - 애플리케이션 로그에는 아무것도 없다.
  - `netstat -su`의 "receive buffer errors"(=`UdpRcvbufErrors`)가 증가한다.
  - `ss -uanm`의 `d` 값이 증가한다.
- **원인**
  - 수신 루프가 들어오는 속도를 못 따라간다(GC 멈춤, 동기 처리, 단일 스레드).
  - 수신 버퍼가 작다. UDP에는 보내는 쪽을 늦추는 흐름 제어가 없다.
- **대처**
  - 수신 루프는 꺼내기만 하고 처리는 큐·워커로 넘긴다.
  - `SO_RCVBUF`를 키운다. 필요하면 `net.core.rmem_max`도 올린다. 실제로 잡힌 값을 확인한다.
  - 수신 소켓을 여러 개로 나눈다(`SO_REUSEPORT`로 같은 포트를 여러 소켓이 나눠 받는다, socket(7)).
  - 손실을 **지표로 경보**한다. 카운터를 보지 않으면 영원히 모른다.

### 2. 반사·증폭 DDoS에 내 서버가 이용된다

- **현상**: 내 서버의 송신 트래픽이 폭증한다. 모르는 IP로 큰 응답을 대량으로 보낸다. 또는 반대로, 내가 피해자로 큰 UDP 응답을 받는다.
- **보이는 형태**: 작은 요청이 대량으로 들어오고, 요청의 출발지 IP가 한두 곳(피해자)에 몰린다. 응답 크기가 요청의 수십 배다.
- **원인**
  - UDP는 연결 수립이 없다. 그래서 출발지 IP를 **위조**한 요청에도 그대로 답한다.
  - 작은 요청에 큰 응답을 주는 서비스가 증폭기가 된다.
  - CISA 표 기준 증폭 배율: DNS 28~54, NTP 556.9, Memcached 10,000~51,000.
- **대처**
  - 인터넷에 열 필요 없는 UDP 서비스는 닫는다(memcached·SNMP 등).
  - 응답 속도를 제한한다(DNS response rate limiting).
  - 작은 인증 안 된 요청에 큰 응답을 주지 않게 설계한다(RFC 8085 §6 SHOULD).
  - 망 경계에서 위조 출발지를 걸러낸다(BCP 38).
  - QUIC 서버는 이 문제 때문에, 클라이언트 주소를 검증하기 전에는 받은 양의 **3배**까지만 보낸다(RFC 9000 §8).

### 3. NAT·방화벽 뒤에서 한동안 조용하면 끊긴다

- **현상**: 오래 쉬던 UDP 세션(VoIP, VPN, 게임)이 다시 말하면 상대가 못 받는다.
- **보이는 형태**: 보내는 쪽 카운터는 오르는데 받는 쪽에는 아무것도 안 온다. 에러도 없다.
- **원인**
  - UDP에는 연결 끝을 알리는 신호가 없다. 그래서 NAT는 **타이머로만** 매핑을 지운다(RFC 8085 §3.5).
  - RFC 4787은 2분 이상을 요구한다(잘 알려진 포트 0~1023은 예외 허용, REQ-5a). 하지만 더 짧게 쓰는 장비가 적지 않다(RFC 8085 §3.5).
  - 리눅스 conntrack UDP 기본값은 30초다. 양방향 스트림으로 보이면 120초다(11번).
- **대처**
  - 1순위: 끊김을 감지하면 세션을 다시 맺는 로직을 둔다(RFC 8085 §3.5 SHOULD).
  - 재동기화가 곤란한 응용(미디어 등)만 keepalive를 쓸 수 있다(MAY). 일반 용도로는 권장하지 않는다(NOT RECOMMENDED).
    - 쓴다면 15초보다 자주 보내지 않고, 가능하면 더 길게 둔다(SHOULD NOT·SHOULD, RFC 8085 §3.5).

### 4. 큰 데이터그램만 사라진다

- **현상**: 작은 메시지는 도착하는데 큰 메시지만 안 온다.
- **보이는 형태**: 리눅스 기본 소켓(`IP_PMTUDISC_WANT`)은 경로 MTU를 넘으면 커널이 **에러 없이 단편화해** 보낸다(ip(7) `IP_MTU_DISCOVER`). 그래서 대개 에러 없이 받는 쪽에 안 온다(조각 손실·조각을 버리는 장비).
  - `IP_PMTUDISC_DO`로 DF를 강제한 소켓이면 송신 쪽에서 `EMSGSIZE`가 난다(ip(7), net/ipv4/ip_output.c `__ip_append_data`). udp(7)의 "기본값에서 `EMSGSIZE`" 설명은 현재 코드와 다르다.
- **원인**: 데이터그램이 경로 MTU를 넘어 단편화됐다. 조각 하나가 사라지면 전체가 사라진다(RFC 8085 §3.2).
- **대처**: 메시지를 경로 MTU 안으로 나눈다. 큰 데이터는 TCP·QUIC을 쓴다(10번).

### 5. `sendto()`는 성공했는데 아무 일도 없다

- **현상**: 코드가 에러 없이 보냈는데 상대가 받지 못했다.
- **보이는 형태**: 송신 쪽 에러 없음. 상대 쪽 `netstat -su`의 "packets to unknown port received" 증가. 또는 connect한 소켓이면 **다음** 호출에서 `ECONNREFUSED`.
- **원인**: 상대 포트에 소켓이 없다(서비스 다운·포트 오타). UDP는 전달 확인이 없고, unconnected 소켓은 ICMP 에러를 받지 못한다(리눅스, `udp_err`).
- **대처**
  - 요청·응답형이면 응답 타임아웃과 재시도를 둔다.
  - 한 상대와만 통신하면 `connect()`한 소켓을 써서 ICMP 에러를 받는다.

## 핵심 문장

- UDP는 IP에 **포트와 체크섬만** 더한다. 연결·재전송·순서·혼잡 제어는 없고, 필요하면 애플리케이션이 만든다.
- 데이터그램 경계가 지켜진다. 한 번 받기에 하나씩 오고, 버퍼보다 크면 잘린다.
- 체크섬이 틀리거나 수신 버퍼가 차면 **조용히 버린다**. 그래서 `receive buffer errors` 같은 카운터를 지표로 봐야 한다.
- 출발지를 확인하지 않으므로 위조 요청에 큰 응답을 주는 서비스는 **반사·증폭 공격**의 도구가 된다.
- 연결 끝이 없어 NAT는 타이머로만 매핑을 지운다. 오래 쉬는 UDP 세션은 끊김을 감지해 다시 맺는 로직이 먼저고, keepalive는 재동기화가 곤란할 때만 쓴다.

## 관련 주제·근거

- 선행: [01-layer-map-osi-tcpip](../01-layer-map-osi-tcpip/2-summary.md) — 전송 계층의 자리.
- 후속·연결
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md) — UDP가 안 하는 연결 수립을 TCP는 어떻게 하나
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — UDP 매핑 timeout
  - [12-dhcp](../12-dhcp/2-summary.md) — UDP 67/68 위의 프로토콜
  - [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md) — 큰 데이터그램과 단편화.
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — UDP에 없는 흐름 제어.
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) — UDP의 대표 사용처.
  - [security/28-dos-and-abuse](../../security/28-dos-and-abuse/2-summary.md) — 반사·증폭 공격
- RFC
  - RFC 768 User Datagram Protocol — 헤더 형식, 가짜 헤더, 체크섬 0 = 안 씀 <https://www.rfc-editor.org/rfc/rfc768>
  - RFC 1122 §4.1.3.1 Port Unreachable(SHOULD) · §4.1.3.4 체크섬 기본 켜짐·틀리면 조용히 버림(MUST) <https://www.rfc-editor.org/rfc/rfc1122>
  - RFC 8200 §8.1 IPv6에서 UDP 체크섬 필수 <https://www.rfc-editor.org/rfc/rfc8200>
  - RFC 8085 UDP Usage Guidelines(BCP 145) — §3.1 혼잡 제어, §3.2 메시지 크기, §3.5 미들박스·keepalive 15초, §6 증폭 <https://www.rfc-editor.org/rfc/rfc8085>
  - RFC 4787 REQ-5 NAT UDP 매핑 2분 이상 <https://www.rfc-editor.org/rfc/rfc4787>
  - RFC 1035 §4.2.1 DNS over UDP 512바이트·TC 비트 <https://www.rfc-editor.org/rfc/rfc1035>
  - RFC 9000 QUIC — §8 anti-amplification 3배, §14.1 첫 데이터그램 1200바이트 <https://www.rfc-editor.org/rfc/rfc9000>
- Linux
  - udp(7) — 무연결·재정렬·중복, 한 번에 한 패킷, `MSG_TRUNC`, `EMSGSIZE`, `ECONNREFUSED` <https://man7.org/linux/man-pages/man7/udp.7.html>
  - ip(7) `IP_MTU_DISCOVER` — `IP_PMTUDISC_WANT`는 필요하면 단편화, `IP_PMTUDISC_DO`는 `EMSGSIZE`로 거부 <https://man7.org/linux/man-pages/man7/ip.7.html>
  - socket(7) — `SO_RCVBUF`(두 배, rmem_default·rmem_max), `SO_REUSEPORT` <https://man7.org/linux/man-pages/man7/socket.7.html>
  - ss(8) — `skmem`의 `d<sock_drop>` <https://man7.org/linux/man-pages/man8/ss.8.html>
  - include/net/udp.h `struct udp_table`(hash·hash2·hash4), net/ipv4/udp.c `udp_err`·`__udp_queue_rcv_skb` <https://github.com/torvalds/linux/blob/master/net/ipv4/udp.c>
- CISA, "UDP-Based Amplification Attacks"(TA14-017A) — 프로토콜별 증폭 배율 <https://www.cisa.gov/news-events/alerts/2014/01/17/udp-based-amplification-attacks>
- Grigorik, HPBN "Building Blocks of UDP" <https://hpbn.co/building-blocks-of-udp/>
- Kurose & Ross 8판 3.3 "Connectionless Transport: UDP"
