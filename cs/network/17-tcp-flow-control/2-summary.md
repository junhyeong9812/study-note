# network/17-tcp-flow-control — 받는 쪽이 "그만 보내"라고 말하는 법 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

받는 쪽 커널은 도착한 데이터를 **수신 버퍼**에 넣어 두고, 앱이 `read()`할 때 꺼내 준다.\
버퍼는 유한하다.\
보내는 쪽이 받는 쪽 앱의 소비 속도를 모른 채 계속 보내면, 버퍼가 넘쳐 받은 데이터를 버리게 된다.\
버린 데이터는 재전송해야 하니 망과 양쪽 호스트가 헛일을 한다(RFC 9293 §3.8.6).

```text
  송신 앱 --write--> [송신 버퍼] ==== 망 ====> [수신 버퍼] --read--> 수신 앱
                                                  ^
                                          여기가 차면 어떻게 하나?
```

쉬운 예: 물탱크에 물을 붓는 사람과 수도꼭지로 빼 쓰는 사람이 있다.\
탱크 주인이 "지금 남은 칸은 20리터"라고 계속 알려 주면, 붓는 사람은 그 이상 붓지 않는다.

똑같은 구조다.\
TCP 수신자는 ACK마다 "지금 더 받을 수 있는 양"(**수신 윈도**)을 실어 보낸다.\
송신자는 그 양을 넘겨 보내지 않는다.

실무 예:
- 느린 컨슈머(DB에 쓰느라 `read()`를 늦게 하는 서버)가 있으면, 보내는 쪽 `write()`가 막히거나 메모리 버퍼가 불어난다.
- 대륙 간 링크인데 전송이 몇 MB/s에서 멈춘다. 윈도 스케일링이 꺼져 64KB 윈도로 묶인 경우다.

## 동작·원리

### 1. 수신 윈도 — ACK에 실리는 "남은 칸"

```text
  수신 버퍼 (RCV.BUFF)
  +-------------------+------------------------------+---------+
  | 받았지만 앱이       |  광고한 빈 공간 (RCV.WND)       | 아직     |
  | 안 읽음 (RCV.USER)  |  = 송신자가 더 보내도 되는 양    | 미광고   |
  +-------------------+------------------------------+---------+
                      ^
                   RCV.NXT (다음 기대 바이트)

  수신자 -> 송신자:  <ACK=RCV.NXT><WIN=RCV.WND>
```

- 세그먼트의 윈도 필드는 "보내는 쪽(=데이터 수신자)이 지금 받을 준비가 된 시퀀스 범위"다(RFC 9293 §3.8.6).
  - *rwnd(receive window)*: 수신자가 광고한 윈도. 헤더의 16비트 Window 필드에 실린다.
  - *RCV.USER*: 받아서 ACK까지 했지만 앱이 아직 읽지 않은 데이터(§3.8.6.2.2 그림).
- 앱이 `read()`를 안 하면 RCV.USER가 늘고, 광고할 수 있는 빈 공간(RCV.WND)이 줄어든다.

### 2. 송신 측 — 윈도가 보낼 수 있는 양의 상한

```text
  송신 시퀀스 공간
          SND.UNA           SND.NXT            SND.UNA + SND.WND
             |                 |                     |
  ... 확인됨 | 보냈음, ACK 대기 |  보내도 됨 (usable)  | 보내면 안 됨 ...
             |<-------------- SND.WND -------------->|

  usable window  U = SND.UNA + SND.WND - SND.NXT      (RFC 9293 §3.8.6.2.1)
```

- ACK가 오면 왼쪽 끝(SND.UNA)이 오른쪽으로 가고, 새 윈도 값으로 오른쪽 끝도 다시 정해진다. 이것이 **슬라이딩 윈도**다.
- 실제로 보낼 수 있는 양은 혼잡 윈도와의 **작은 쪽**이다. `min(cwnd, rwnd)`(RFC 5681 §3.1).
  - 흐름 제어(rwnd)는 **받는 호스트**를 보호한다.
  - 혼잡 제어(cwnd)는 **중간 망**을 보호한다(18번).
- 수신자는 윈도의 오른쪽 끝을 왼쪽으로 당기면(윈도 축소) 안 된다(SHOULD NOT, SHLD-14). 송신자는 그래도 견뎌야 한다(MUST-34, §3.8.6).

### 3. zero window — "지금은 0칸"

```text
  송신자                                           수신자 (앱이 read 안 함)
  ---- data --------------------------------->    버퍼 가득
  <--- <ACK=5000><WIN=0> ----------------------   "0칸"
  (보낼 데이터가 있어도 멈춤, persist 타이머 시작)
            ... RTO 후 ...
  ---- zero-window probe (1바이트 또는 재전송) -->
  <--- <ACK=5000><WIN=0> ----------------------   아직 0칸
            ... 간격을 지수로 늘리며 반복 ...
                                                   앱이 read() -> 공간 생김
  <--- <ACK=5000><WIN=65535> ------------------   윈도 업데이트
  ---- data --------------------------------->    재개
```

- 수신자가 윈도 0을 광고하면 송신자는 새 데이터를 멈춘다.
- **윈도 업데이트 ACK는 데이터가 없는 ACK라서 유실돼도 재전송되지 않는다.**
  - 그래서 송신자가 가만히 기다리면, 업데이트가 유실됐을 때 양쪽이 영원히 서로 기다린다(교착).
  - 이를 막으려고 송신자가 주기적으로 **zero-window probe**를 보낸다. 지원은 필수다(MUST-36, §3.8.6.1).
- 첫 probe는 윈도가 RTO만큼 0이었을 때 보내고, 이후 간격은 지수로 늘린다(SHOULD, SHLD-29·30).
- 수신자는 윈도를 **무기한** 닫아 둘 수 있다(MAY-8). 수신자가 probe에 ACK로 계속 답하는 한, 송신자는 연결을 열어 둬야 한다(MUST-37).
  - RFC는 이것을 "프린터 종이가 떨어진" 상황을 위한 것이라고 설명한다(§3.8.6.1).
  - 그래서 **느린 소비자는 에러를 만들지 않는다.** 연결은 살아 있고, 그냥 멈춰 있다.
  - *persist 타이머*: zero-window probe를 언제 보낼지 정하는 타이머다. 리눅스 `ss -o`에 `timer:(persist,…)`로 보인다(ss(8)).

### 4. 윈도 스케일링 — 16비트의 한계를 넘는다

윈도 필드는 16비트다.\
그래서 광고할 수 있는 최대 윈도는 65,535바이트(약 64KB)다.

```text
  한 RTT에 보낼 수 있는 최대량 = 윈도
  처리량 상한 ≈ 윈도 / RTT

  예시) 윈도 65,535 B, RTT 100 ms
        65,535 × 8 / 0.1 s ≈ 5.2 Mbit/s     <- 링크가 1 Gbit/s여도 이 이상 못 낸다
```

- 링크를 꽉 채우려면 윈도가 **BDP(대역폭 × RTT)** 이상이어야 한다. 1 Gbit/s × 100ms면 약 12.5MB다(예시 계산). 03번 노트의 BDP와 같은 이야기다.

RFC 7323의 Window Scale 옵션이 이 한계를 푼다.

```text
  SYN       --> [MSS][SACK-perm][TS][WS shift=7]      "내 윈도 값은 2^7배 해서 읽어"
  SYN-ACK   <-- [MSS][SACK-perm][TS][WS shift=7]      "나도 스케일 쓸게"
  이후 모든 세그먼트:  실제 윈도 = 헤더 Window 필드 << shift
                       (예: 필드 512, shift 7 -> 512 × 128 = 65,536 B)
```

- 옵션은 **SYN에만** 싣는다. SYN이 아닌 세그먼트의 Window Scale 옵션은 무시해야 한다(MUST, RFC 7323 §2.2).
  - 그래서 스케일 값은 연결을 열 때 방향별로 고정된다(§2.1).
- **양쪽 SYN에 모두** 옵션이 있어야 켜진다(MUST, §2.2). 한쪽이라도 없으면 양방향 모두 스케일 0이다(MUST, §2.3).
- SYN·SYN-ACK 자체의 윈도 필드는 스케일하지 않는다(MUST NOT, §2.2).
- shift는 최대 14다. 그러면 최대 윈도가 2^30 = 1GiB다. 14보다 큰 값을 받으면 14로 쓴다(MUST, §2.3).
- 스케일 값은 연결을 열 때의 최대 수신 버퍼로 정해진다(§2.1).
  - 그래서 리눅스에서 소켓 버퍼 크기는 `listen()`·`connect()` **전에** 정해야 효과가 있다(tcp(7)).
  - Java 문서도 64K보다 큰 수신 윈도가 필요하면 `setReceiveBufferSize`를 연결 전에(서버는 `ServerSocket` bind 전에) 호출하라고 한다(`java.net.Socket`).

### 5. 리눅스의 수신 버퍼와 자동 튜닝

```text
  net.ipv4.tcp_rmem = min  default  max
                      4K   131072   (RAM에 따라 131072 ~ 32MB)     <- 커널 문서 기본값
  tcp_moderate_rcvbuf = 1   -> 경로에 맞게 버퍼를 자동으로 키움 (max까지)
  setsockopt(SO_RCVBUF)     -> 그 소켓은 자동 튜닝 꺼짐
```

- 리눅스는 수신 버퍼를 자동으로 키운다(`tcp_moderate_rcvbuf` 기본 켜짐, tcp(7)).
- 앱이 `SO_RCVBUF`를 직접 설정하면 그 소켓의 자동 튜닝이 꺼진다(ip-sysctl `tcp_rmem`).
  - 작은 값을 박아 두면 고BDP 경로에서 처리량이 묶인다.
- 커널은 `SO_RCVBUF`로 준 값을 두 배로 잡는다. 관리용 오버헤드 몫이다(socket(7)).
- 수신 버퍼 전부가 윈도가 되지는 않는다. 일부는 오버헤드 몫으로 뺀다. 예전에는 `tcp_adv_win_scale`(tcp(7))로 그 비율을 정했지만, 이 sysctl은 리눅스 6.6부터 쓰지 않는다(ip-sysctl "Obsolete since linux-6.6").

### 6. Silly Window Syndrome — 조금씩 열리는 윈도의 함정

```text
  앱이 1바이트씩 read -> 윈도가 1바이트씩 열림 -> 송신자가 1바이트짜리 세그먼트 전송
  -> 40바이트 헤더에 1바이트 데이터: 효율이 극도로 나쁨
```

- 양쪽 모두에 회피 알고리즘이 필수다(MUST-38 송신, MUST-39 수신, §3.8.6.2).
  - 수신자: 빈 공간이 `min(버퍼의 1/2, MSS)` 이상 생길 때까지 윈도 오른쪽 끝을 옮기지 않는다(§3.8.6.2.2).
  - 송신자: MSS 하나를 채우거나, 최대 윈도의 절반을 보낼 수 있거나, 밀어 넣을 데이터를 한꺼번에 보낼 수 있을 때 보낸다(§3.8.6.2.1).
- 작은 쓰기를 모으는 Nagle 알고리즘과 짝을 이룬다(22번).

### 7. 앱 수준 흐름 제어로 이어진다

```text
  수신 앱이 느림 -> 수신 버퍼 가득 -> rwnd = 0 -> 송신 커널 멈춤
  -> 송신 버퍼 가득 -> 송신 앱의 write()가 블록 (또는 0/EAGAIN, Node는 write()가 false)
```

- TCP 흐름 제어는 **소켓 버퍼를 통해 앱까지 역압(backpressure)을 전달**한다.
- 앱이 이 신호를 무시하고 자기 메모리에 계속 쌓으면, TCP가 막아 준 문제를 앱이 다시 만든다.
  - *역압(backpressure)*: 뒤쪽이 느릴 때 앞쪽에 "속도를 늦춰라"를 전달하는 것. [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md) 참고.

## 쓰이는 자료구조·알고리즘

- **슬라이딩 윈도** — 송신 측은 [SND.UNA, SND.UNA+SND.WND) 구간만 보낼 수 있다. 수신 측은 [RCV.NXT, RCV.NXT+RCV.WND) 구간만 받아들인다(RFC 9293 §3.3.1).
  - 두 포인터(왼쪽 끝·오른쪽 끝)가 한 방향으로만 움직이는 구간이다.
- **링 버퍼(원형 버퍼)** — 소켓 송수신 버퍼는 개념상 "생산자가 쓰고 소비자가 읽는" 고정 용량 버퍼다.
  - 가득 차면 생산자를 멈추게 하는 정책이 곧 흐름 제어다. 리눅스 구현은 링 버퍼가 아니다. 수신 큐는 sk_buff 연결 리스트(`struct sk_buff_head sk_receive_queue`)이고, 재전송 큐·out-of-order 큐는 레드-블랙 트리(`rb_root`)다(include/net/sock.h, include/linux/tcp.h).
  - 개념은 data-structure `ring-buffer` — 미작성([영역 표](../../data-structure/curriculum.md)), 큐 일반은 [queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **비트 시프트(고정소수점 스케일)** — 16비트 필드에 30비트 값을 싣는 방법. `실제 = 필드 << shift`. 정밀도(2^shift 단위)를 범위와 맞바꾼다(RFC 7323 §2.3).
- **지수 백오프 타이머** — zero-window probe 간격(SHLD-30).

## 적용 — 풀어나가는 법

### 1. 앱에서 역압을 존중한다

Node.js — `write()`의 반환값과 `'drain'`을 따른다.

```js
const net = require('node:net');

function pump(source, sock) {
  source.on('data', (chunk) => {
    const ok = sock.write(chunk);     // false = 내부 버퍼가 highWaterMark를 넘었다
    if (!ok) {
      source.pause();                 // 더 읽어 오지 않는다
      sock.once('drain', () => source.resume());   // 버퍼가 비면 재개
    }
  });
}
// 스트림끼리는 source.pipe(sock) 또는 stream.pipeline()이 이 일을 대신한다
```

- Node 문서는 `socket.write()`가 항상 성공하고, 못 보낸 데이터는 내부에 쌓여 **메모리가 늘 수 있다**고 경고한다. 쌓이면 `pause()`/`resume()`으로 조절하라고 한다(Node `net` 문서).

Java NIO — 논블로킹 `write()`는 0을 돌려줄 수 있다.

```java
// 논블로킹 SocketChannel: 송신 버퍼의 빈 만큼만 쓴다 (0일 수도 있다)
int n = channel.write(buf);
if (buf.hasRemaining()) {
    // 다 못 썼다 = 상대가 느리거나 zero window. 남은 걸 들고 OP_WRITE를 기다린다
    key.interestOps(key.interestOps() | SelectionKey.OP_WRITE);
    // 그동안 이 연결로 보낼 새 데이터 생산을 멈춘다 (큐 상한을 둔다)
}
```

- `WritableByteChannel.write` 문서: 논블로킹 소켓 채널은 송신 버퍼의 빈 공간보다 많이 쓸 수 없다.

### 2. 고BDP 경로에서 윈도가 충분한지 본다

```bash
# 윈도 스케일링 켜져 있나 (1이 기본)
sysctl net.ipv4.tcp_window_scaling net.ipv4.tcp_rmem net.ipv4.tcp_wmem net.core.rmem_max

# 연결별: wscale:<송신>,<수신>  rcv_space  rtt  cwnd
ss -tin dst 203.0.113.10
#   wscale 필드가 없으면 스케일링이 협상되지 않은 것

# SYN에 wscale 옵션이 실렸는지
tcpdump -ni eth0 'tcp[tcpflags] & tcp-syn != 0 and host 203.0.113.10' -v
#   options [mss 1460,sackOK,TS val ... ecr 0,nop,wscale 7]
```

- 필요한 윈도 ≈ BDP. 예시로 RTT 150ms에 200 Mbit/s를 원하면 약 3.75MB다(예시 계산).
- `tcp_rmem` max와 `net.core.rmem_max`가 그보다 작으면 올린다.
- 앱 코드에서 `SO_RCVBUF`를 작게 박아 두지 않았는지 확인한다. 박으면 자동 튜닝이 꺼진다.

### 3. zero window를 확인한다

```bash
# 수신 쪽: Recv-Q가 버퍼만큼 차 있으면 앱이 안 읽는 중
ss -tn state established '( sport = :9000 )'

# 송신 쪽: persist 타이머 = zero window에 막혀 probe 중
ss -tno state established dst 10.0.0.7
#   timer:(persist,1.2sec,0)

# 패킷: 수신자가 win 0을 광고
tcpdump -ni eth0 'host 10.0.0.7 and tcp[14:2] = 0'     # TCP 헤더 Window 필드(오프셋 14) = 0

# 카운터: 윈도를 0으로 광고한 횟수
nstat -az TcpExtTCPToZeroWindowAdv TcpExtTCPFromZeroWindowAdv
```

- `tcp[14:2] = 0` 필터는 SYN이 아닌 세그먼트의 스케일 전 필드값이다. 스케일이 있어도 0은 0이다.

## 장애 시나리오와 대처

### 1. 느린 소비자 — zero window로 영원히 멈춘다(연결은 살아 있다)

- **현상**: 생산자 쪽 전송이 멈췄다. 에러·타임아웃은 없다. 연결은 ESTABLISHED다.
- **보이는 형태**
  - 수신 쪽 `ss`의 `Recv-Q`가 버퍼 크기만큼 차 있다.
  - 송신 쪽 `ss -o`에 `timer:(persist,…)`, `Send-Q`가 가득하다.
  - tcpdump에 `win 0` ACK와 주기적인 probe가 오간다.
  - 송신 앱: 블로킹 `write()`에서 스레드가 멈추거나, Node면 `writableLength`가 계속 늘어 메모리가 오른다.
- **원인**
  - 수신 앱이 `read()`를 멈췄다(처리 스레드 교착, 다운스트림 DB 대기, GC 정지).
  - 수신 커널은 probe에 계속 ACK하므로 연결은 살아 있다. RFC가 이 상태를 무기한 허용한다(MAY-8, MUST-37).
  - 이때 keepalive는 동작하지 않는다(Cloudflare "When TCP sockets refuse to die"). 리눅스 keepalive 타이머는 persist 타이머와 별개인데, 송신 큐에 못 보낸 데이터가 남아 있으면 probe를 보내지 않고 재예약만 하기 때문이다(net/ipv4/tcp_timer.c `tcp_keepalive_timer`).
- **대처**
  - 수신 앱의 멈춘 원인을 찾는다(스레드 덤프, 처리 큐 길이).
  - 송신 쪽에 **쓰기 타임아웃**을 둔다. Java `setSoTimeout`은 `read()`에만 적용된다(`java.net.Socket` 문서). 쓰기 쪽은 NIO + 타이머로 구현하거나, 일정 시간 진전이 없으면 연결을 닫는 감시자를 둔다.
  - `TCP_USER_TIMEOUT`은 "zero window 때문에 보내지 못하고 버퍼에 남은 데이터"에도 적용된다. 그 시간이 지나면 커널이 연결을 닫고 `ETIMEDOUT`을 준다(tcp(7)).
  - 앱 수준 큐에 상한을 두고, 넘으면 거절하거나 느린 연결을 끊는다.

### 2. 대륙 간 전송이 수 MB/s에서 멈춘다 — 64KB 윈도 상한

- **현상**: 1 Gbit/s 링크인데 원거리 전송이 몇 Mbit/s에서 더 오르지 않는다. 가까운 곳은 빠르다.
- **보이는 형태**
  - `ss -ti`에 `wscale` 필드가 없다.
  - tcpdump의 SYN 옵션에 `wscale`이 없거나 SYN-ACK에만 없다.
  - 처리량 ≈ 65,535B / RTT로 딱 맞아떨어진다(예: RTT 100ms → 약 5.2 Mbit/s).
- **원인**
  - 경로의 방화벽·프록시 같은 중간 장비가 SYN에서 Window Scale 옵션을 떼어 냈다. 한쪽 SYN에라도 없으면 스케일링이 양방향 모두 꺼진다(RFC 7323 §2.2).
  - 또는 한쪽 호스트에서 `tcp_window_scaling`이 꺼져 있다.
  - 변형: 옵션은 두되 shift 값을 0으로 바꾸는 장비도 보고됐다. 이 경우 한쪽은 스케일된 작은 값을 그대로 읽어 윈도가 훨씬 더 작아진다(LWN "TCP window scaling and broken routers").
- **대처**
  - 양 끝에서 SYN을 캡처해 옵션이 어디서 사라지는지 비교한다.
  - 해당 장비의 TCP 옵션 정규화·"TCP 정리" 기능을 끈다 [?].
  - 끌 수 없으면 병렬 연결 여러 개로 우회한다(연결당 64KB/RTT × N).

### 3. 수신 버퍼를 작게 고정해 처리량이 안 나온다

- **현상**: 같은 경로에서 어떤 앱은 빠르고, 우리 앱만 느리다.
- **보이는 형태**: `ss -tim`의 `skmem:(…,rb<rcv_buf>,…)`에서 수신 버퍼 크기(`rb`)가 작게 고정돼 있다(ss(8)). `ss -ti`의 `rcv_space`(자동 튜닝용 변수, ss(8))가 자라지 않는다.
- **원인**: 코드나 설정에서 `SO_RCVBUF`(Java `setReceiveBufferSize`, Netty `SO_RCVBUF`)를 작은 값으로 박았다. 그 소켓은 자동 튜닝이 꺼진다(ip-sysctl `tcp_rmem`).
- **대처**
  - 특별한 이유가 없으면 설정을 지우고 커널 자동 튜닝에 맡긴다.
  - 꼭 정해야 하면 BDP 이상으로, `listen()`·`connect()` 전에 설정한다(tcp(7)).

### 4. 앱 메모리가 계속 오른다 — 역압 무시

- **현상**: 느린 클라이언트가 붙으면 서버 메모리가 오르다 OOM이 난다.
- **보이는 형태**: Node `socket.writableLength`가 크다. 힙 덤프에 보낼 대기 버퍼가 가득하다.
- **원인**: TCP는 zero window로 멈췄는데, 앱이 `write()`의 반환값을 무시하고 계속 썼다. 앱 메모리가 사실상 무한 버퍼가 됐다.
- **대처**: `write()`가 false면 생산을 멈추고 `'drain'`을 기다린다. `pipeline()`을 쓴다. 연결당 대기 버퍼 상한을 두고, 넘으면 연결을 끊는다.

## 핵심 문장

- 흐름 제어는 **받는 호스트**를 보호한다. 수신자는 ACK마다 남은 버퍼(수신 윈도)를 알리고, 송신자는 `min(cwnd, rwnd)`를 넘겨 보내지 않는다.
- zero window는 에러가 아니다. 송신자는 probe로 윈도가 다시 열리는지 확인하며, 수신자가 답하는 한 연결은 무기한 살아 있다. 그래서 느린 소비자는 "조용한 정지"로 나타난다.
- 윈도 필드는 16비트라 처리량 상한이 64KB/RTT다. Window Scale 옵션(SYN 전용, 양쪽 모두 필요, shift ≤ 14)이 이를 1GiB까지 넓힌다.
- 링크를 채우려면 윈도가 BDP 이상이어야 한다. 리눅스는 버퍼를 자동 튜닝하며, `SO_RCVBUF`를 박으면 그 튜닝이 꺼진다.
- TCP의 역압은 소켓 버퍼를 거쳐 앱의 `write()`까지 온다. 앱이 그 신호를 무시하면 메모리가 대신 터진다.

## 관련 주제·근거

- 선행: [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — 시퀀스·ACK·슬라이딩 윈도의 바탕
- 연결
  - [03-latency-bandwidth-bdp](../03-latency-bandwidth-bdp/2-summary.md) — BDP와 윈도 크기
  - [18-tcp-congestion-control](../18-tcp-congestion-control/2-summary.md) — cwnd, `min(cwnd, rwnd)`의 다른 한쪽
  - [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md) — zero window에도 걸리는 `TCP_USER_TIMEOUT`
  - [22-nagle-and-delayed-ack](../22-nagle-and-delayed-ack/2-summary.md) — SWS 회피와 짝을 이루는 Nagle
  - [36-http2-multiplexing](../36-http2-multiplexing/2-summary.md) — HTTP/2의 스트림 단위 흐름 제어
  - [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md) — 앱 수준 역압
- RFC
  - RFC 9293 (TCP) <https://www.rfc-editor.org/rfc/rfc9293> — §3.3.1 송수신 시퀀스 공간 · §3.8.6 윈도 관리·축소 금지(SHLD-14, MUST-34) · §3.8.6.1 zero-window probe(MUST-36, MAY-8, MUST-37, SHLD-29·30) · §3.8.6.2 SWS 회피(MUST-38·39)
  - RFC 7323 (TCP Extensions for High Performance) <https://www.rfc-editor.org/rfc/rfc7323> — §2.1 스케일은 연결 수립 시 고정 · §2.2 SYN 전용, 양쪽 모두 필요, SYN 윈도는 스케일 안 함 · §2.3 한쪽 없으면 양방향 0, shift ≤ 14(1GiB)
  - RFC 5681 §3.1 — `min(cwnd, rwnd)`가 전송량을 정함 <https://www.rfc-editor.org/rfc/rfc5681>
- Linux
  - tcp(7) — `tcp_window_scaling`, `tcp_moderate_rcvbuf`, `tcp_adv_win_scale`(6.6부터 폐기, ip-sysctl), 버퍼는 listen/connect 전에 설정, `TCP_USER_TIMEOUT`(zero window 포함) <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - socket(7) — `SO_RCVBUF` 값 두 배 <https://man7.org/linux/man-pages/man7/socket.7.html>
  - 커널 문서 ip-sysctl `tcp_rmem`(기본값, `SO_RCVBUF`가 자동 튜닝을 끔) <https://docs.kernel.org/networking/ip-sysctl.html>
  - 커널 문서 snmp_counter — `TcpExtTCPToZeroWindowAdv` <https://docs.kernel.org/networking/snmp_counter.html>
  - ss(8) — `persist` 타이머, `wscale` <https://man7.org/linux/man-pages/man8/ss.8.html>
  - net/ipv4/tcp_timer.c `tcp_keepalive_timer` — 미확인·미전송 데이터가 있으면 keepalive probe 생략 <https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_timer.c>
- Node.js `net` 문서 — `socket.write()` 버퍼링 경고, `'drain'`, `pause()`/`resume()` <https://nodejs.org/api/net.html>
- Java SE `WritableByteChannel.write` — 논블로킹 소켓 채널은 버퍼 빈 공간만큼만 씀 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/WritableByteChannel.html>
- Java SE `java.net.Socket` — `setSoTimeout`은 read에만, `setReceiveBufferSize`는 64K 초과 윈도면 연결 전에 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/Socket.html>
- Cloudflare, "When TCP sockets refuse to die" — zero window 중 keepalive 미동작, `TCP_USER_TIMEOUT` 동작 <https://blog.cloudflare.com/when-tcp-sockets-refuse-to-die/>
- LWN, "TCP window scaling and broken routers"(2004) <https://lwn.net/Articles/92727/>
- 교재
  - Kurose & Ross 8판 3.5.5 "Flow Control"
  - Stevens, 『TCP/IP Illustrated Vol.1』 2판 15장 "TCP Data Flow and Window Management"
