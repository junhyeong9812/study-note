# network/22-nagle-and-delayed-ack — 작은 쓰기 두 번이 왜 40ms를 먹나 — 정리 (힌트)

## 해결하는 문제

TCP 세그먼트 하나에는 헤더가 붙는다.\
IPv4 + TCP 헤더만 최소 40바이트다.\
1바이트를 보내려고 41바이트 패킷을 만들면 낭비가 크다.

```text
  키 입력 1개 = 1바이트 데이터
  +--------------------+---+
  | IP 20 + TCP 20     | 1 |   = 41바이트 패킷, 오버헤드 4000%   (RFC 896)
  +--------------------+---+
```

RFC 896(1984)은 이 문제를 "small-packet problem"이라 불렀다.\
붐비는 망에서는 이 작은 패킷들이 혼잡을 만들고, 손실·재전송까지 부른다고 적었다.

그래서 TCP에는 "덜 보내기" 장치가 두 개 들어갔다.

```text
  송신 쪽: Nagle 알고리즘   "앞서 보낸 게 확인 안 됐으면, 작은 조각은 모았다가 보낸다"
  수신 쪽: 지연 ACK         "ACK를 바로 보내지 말고 잠깐 기다렸다 응답·다른 ACK와 합친다"
```

각자는 좋은 장치다.\
문제는 둘이 **한 연결의 양 끝에서 동시에** 켜져 있을 때다.\
서로 상대를 기다리면서, 요청 하나에 수십 ms가 고정으로 붙는다.

쉬운 예: 택배 두 상자를 보내는데 규칙이 이렇다.\
보내는 사람: "첫 상자 도착 확인 문자를 받기 전엔 둘째 상자를 안 보낸다."\
받는 사람: "상자가 반만 왔네. 확인 문자는 나중에 몰아서 보내자."\
둘째 상자는 받는 사람의 "나중"이 올 때까지 창고에 묶인다.

똑같은 구조다.\
요청을 `write()` 두 번으로 나눠 보내면, 두 번째 조각은 첫 조각의 ACK를 기다린다.\
서버는 요청이 덜 와서 응답을 못 만들고, ACK도 미룬다.

실무 예:
- HTTP 클라이언트가 헤더와 본문을 따로 `write()`한다. 요청마다 약 40ms가 더해진다.
- Redis·DB 드라이버를 직접 짰는데, 명령을 여러 조각으로 써서 로컬에서도 느리다.
- 게임·실시간 앱에서 작은 이벤트가 뭉쳐서 늦게 도착한다.

## 동작·원리

### Nagle 알고리즘 — 송신 쪽

```text
  앱이 작은 데이터를 write() 했다
          |
          v
  +-----------------------------+   예   +-------------------+
  | 확인 안 된 데이터가 있나?    |------->| 모아 둔다 (보류)   |
  | (SND.NXT > SND.UNA)         |        | ACK가 오거나        |
  +-----------------------------+        | MSS만큼 차면 보냄   |
          | 아니오                        +-------------------+
          v
      바로 보낸다
```

- 규칙(RFC 9293 §3.7.4, RFC 1122 §4.2.3.4): 확인되지 않은 데이터가 있으면 새 데이터를 모은다.
  - 앞선 데이터가 확인(ACK)되거나, 꽉 찬 세그먼트(MSS)를 만들 수 있을 때 보낸다.
  - PSH 비트와 상관없이 모은다.
  - *MSS(Maximum Segment Size)*: 세그먼트 하나에 담을 수 있는 최대 데이터 크기다. 이더넷에서 흔히 1460바이트다(IPv4, 옵션 없음 기준).
  - *SND.UNA*: 보냈지만 아직 확인받지 못한 가장 오래된 바이트 번호.
  - *SND.NXT*: 다음에 보낼 바이트 번호. 둘이 다르면 "공중에 떠 있는 데이터"가 있다.
- 규범 수준
  - 구현은 Nagle을 **SHOULD** 구현한다(SHLD-7).
  - 앱이 연결별로 Nagle을 끌 수단은 **MUST** 있어야 한다(MUST-17). 그게 `TCP_NODELAY`다.
- 효과: RTT당 작은 세그먼트가 최대 하나만 떠 있다. 타이핑처럼 잘게 오는 데이터가 자동으로 뭉친다.

### 지연 ACK — 수신 쪽

```text
  데이터 세그먼트 도착
          |
          v
  바로 ACK?  ---- 아니다. 잠깐 기다린다 ----+
                                          |
     기다리는 동안 이 중 하나가 생기면 ACK를 보낸다
       (a) 앱이 응답을 써서 데이터에 ACK를 얹을 수 있다 (piggyback)
       (b) 꽉 찬 세그먼트가 하나 더 왔다 (2개마다 ACK)
       (c) 지연 ACK 타이머 만료
```

- 규칙(RFC 9293 §3.8.6.3, RFC 1122 §4.2.3.2)
  - 지연 ACK는 **SHOULD** 구현한다(SHLD-18).
  - 지연은 0.5초 미만이어야 한다(**MUST-40**).
  - 꽉 찬 세그먼트 2개(또는 2×RMSS 바이트)마다 최소 한 번은 ACK를 **SHOULD** 보낸다(SHLD-19).
  - *piggyback*: ACK를 따로 보내지 않고, 반대 방향 데이터 세그먼트의 ACK 필드에 얹어 보내는 것.
- 리눅스의 지연 ACK 타이머 범위
  - 커널 소스 `include/net/tcp.h`: `TCP_DELACK_MIN = HZ/25`, `TCP_DELACK_MAX = HZ/5`.
  - 즉 최소 40ms, 최대 200ms다. 커리큘럼의 "~40ms"는 이 최솟값이다.
  - 실제 값은 연결마다 조정된다. `ss -ti`의 `ato:` 필드가 현재 ack timeout(ms)이다(ss(8)).
  - 커널은 상황에 따라 즉시 ACK(quickack) 모드에 들어갔다 나온다(tcp(7) `TCP_QUICKACK`). 그래서 지연이 모든 요청에 똑같이 나타나지 않을 수 있다.

### 둘이 만나면 — write-write-read 교착

요청을 헤더 50바이트(예시), 본문 30바이트(예시)로 두 번 쓰는 클라이언트다.

```text
  클라이언트 (Nagle 켜짐)                       서버 (지연 ACK 켜짐)
  write(헤더 50B)
    공중에 뜬 데이터 없음 -> 바로 전송
    ----------- [헤더 50B] ---------------------->  받음. 요청이 덜 왔다
  write(본문 30B)                                  앱: 본문 기다리며 read() 중
    헤더가 아직 ACK 안 됨 -> 보류                   커널: 보낼 응답이 없으니 ACK 미룸
    ... 대기 ...                                   ... 지연 ACK 타이머 (리눅스 최소 40ms) ...
    <---------------- [ACK] ---------------------  타이머 만료, ACK 단독 전송
  ACK 받음 -> 보류하던 본문 전송
    ----------- [본문 30B] ---------------------->  요청 완성 -> 응답 생성
    <------------- [응답 + ACK] -----------------
```

- 두 규칙 모두 규격대로 동작했다. 버그가 아니라 **상호작용**이다.
- 지연은 "타이머 한 번"만큼 고정으로 붙는다. RTT가 0.1ms인 로컬에서도 요청당 수십 ms가 된다.
- RFC 9293 부록 A.3도 이 조합이 요청-응답형 앱의 성능을 떨어뜨릴 수 있다고 적는다.

같은 요청을 한 번에 쓰면 이렇게 된다.

```text
  write(헤더+본문 80B)  --- [80B] --->  요청 완성 -> 응답에 ACK 얹음
                        <-- [응답+ACK]
```

기다릴 "두 번째 조각"이 없으니 교착도 없다.

### Minshall 변형 — 리눅스가 쓰는 Nagle

- 원래 Nagle은 "확인 안 된 데이터가 **무엇이든** 있으면" 작은 조각을 보류한다.
- Minshall 변형은 "확인 안 된 **작은** 세그먼트가 있으면" 보류한다.
  - RFC 9293 부록 A.3은 이 변형을 참고 문헌(Minshall 등의 draft)으로 소개할 뿐, TCP 표준에는 넣지 않았다고 적는다. 규칙 자체는 리눅스 소스의 `tcp_minshall_check()`에서 확인할 수 있다.
- 리눅스 `tcp_output.c`의 `tcp_nagle_check()` 주석이 이 변형("all sent small packets are ACKed")을 적용한다고 밝힌다.
- 그래도 write-write-read는 막지 못한다.
  - 첫 조각(헤더)이 작은 세그먼트이기 때문이다.
  - 그래서 둘째 조각은 여전히 보류된다.

### 제어 수단 — 소켓 옵션

```text
  옵션               쪽      효과                                              이식성
  TCP_NODELAY       송신    Nagle 끔. 작은 데이터도 즉시 전송                  표준 (MUST-17)
  TCP_CORK          송신    부분 프레임을 안 보냄. 해제 시 한꺼번에 전송        리눅스 전용
                            (최대 200ms 뒤 자동 전송)
  MSG_MORE (send)   송신    호출 한 번 단위로 CORK와 같은 효과                  리눅스 전용
  TCP_QUICKACK      수신    지금 quickack 모드로. 영구 설정 아님                리눅스 전용
```

- `TCP_NODELAY`: "segments are always sent as soon as possible"(tcp(7)).
  - `TCP_CORK`가 우선한다. 단 `TCP_NODELAY`를 설정하는 순간 쌓인 출력을 한 번 밀어낸다.
- `TCP_CORK`: 헤더를 먼저 쓰고 `sendfile(2)`로 본문을 붙일 때 쓰라고 tcp(7)이 설명한다.
  - 현재 구현은 코르크 시간이 최대 200ms다. 넘으면 자동으로 보낸다(tcp(7)).
  - *cork(코르크)*: 병마개. "마개를 막아 두었다가 뽑으면 한꺼번에 나간다"는 비유다.
- `TCP_QUICKACK`: "This flag is not permanent"(tcp(7)). 커널이 내부 판단으로 다시 지연 모드로 바꾼다. 그래서 읽을 때마다 다시 켜는 코드가 흔하다.
- `tcp_autocorking`(리눅스 3.14+, 기본 켜짐): 같은 흐름의 이전 패킷이 qdisc나 장치 큐에 남아 있으면 연속된 작은 쓰기를 커널이 합친다(tcp(7)).

### 런타임별 기본값

```text
  런타임                         Nagle 기본           근거
  C (소켓 그대로)                켜짐                 TCP_NODELAY 미설정이 기본
  Java Socket / NIO              켜짐                 StandardSocketOptions.TCP_NODELAY 기본 FALSE
  Node net.Socket                켜짐                 "it will have Nagle's algorithm enabled"
  Node http.createServer         꺼짐 (서버 쪽 소켓)   noDelay 기본 true (v18.0.0부터)
  Go net.TCPConn                 꺼짐                 SetNoDelay 문서 "The default is true"
```

- 같은 코드라도 런타임이 바뀌면 지연이 생기거나 사라진다.
- 예: Go 클라이언트에서 잘 되던 프로토콜을 Java로 옮기자 요청마다 40ms가 붙는다.

## 쓰이는 자료구조·알고리즘

- **버퍼 + 조건 트리거 flush(배칭)** — Nagle의 본체다.
  - 송신 큐에 조각을 모으다가 "ACK 도착" 또는 "MSS만큼 참" 중 하나가 되면 비운다.
  - 크기 트리거(MSS)와 이벤트 트리거(ACK)를 섞은 배칭이다. 지연 ACK는 여기에 시간 트리거(타이머)를 더한다.
  - 배칭의 일반 문제: 모으는 시간만큼 지연이 늘고, 대신 개수(패킷·호출)가 준다.
- **상태 비교 조건** — `SND.NXT > SND.UNA`는 "시퀀스 공간에서 떠 있는 구간이 있나"라는 구간 판정이다. 시퀀스 번호가 2^32에서 돌기 때문에 모듈러 비교를 쓴다(RFC 9293 §3.4).
- **연결별 타이머** — 지연 ACK 타이머(`ato`), CORK 상한(200ms). 연결 하나에 재전송·keepalive 타이머와 함께 여러 개가 붙는다.
- **적응형 값** — 리눅스는 `ato`를 연결마다 조정한다. 첫 데이터에서 `TCP_ATO_MIN`(40ms)으로 시작하고, 세그먼트 도착 간격에 따라 줄이거나 늘린다(`net/ipv4/tcp_input.c` `tcp_event_data_recv`). 타이머를 걸 때는 RTT와 상한으로 자른다(`net/ipv4/tcp_output.c` `tcp_send_delayed_ack`). 공식의 세부는 이 노트 범위 밖이다.

## 적용 — 풀어나가는 법

### 1. 먼저 앱에서 한 번에 쓴다 — 가장 좋은 해법

메시지 하나(요청·응답 한 건)를 만들 때 버퍼에 다 담고 `write()`를 한 번만 부른다.\
그러면 Nagle을 켠 채로도 교착이 없다.\
작은 메시지가 여러 개면 모아서 한 번에 쓰는 것이 패킷 수도 줄인다.

Java — `BufferedOutputStream`에 모두 쓰고 `flush()`를 한 번 부른다.

```java
try (Socket s = new Socket(host, port)) {
    OutputStream out = new BufferedOutputStream(s.getOutputStream(), 8192);
    out.write(header);   // 아직 커널로 안 간다
    out.write(body);     // 아직 커널로 안 간다
    out.flush();         // 여기서 write 시스템콜 한 번(버퍼 크기 안이라면)
}
```

C — 흩어진 버퍼는 `writev(2)`로 한 번에 넘긴다.

```c
struct iovec iov[2] = {
    { .iov_base = hdr,  .iov_len = hdr_len  },
    { .iov_base = body, .iov_len = body_len },
};
ssize_t n = writev(fd, iov, 2);   /* 시스템콜 1번. 부분 쓰기(n < 합계)는 따로 처리해야 한다 */
```

Node — 조각을 `Buffer.concat`으로 합치거나, 같은 틱에서 `cork()`/`uncork()`로 묶는다.

```js
sock.cork();              // 스트림 수준 코르크(커널 TCP_CORK가 아니다)
sock.write(header);
sock.write(body);
process.nextTick(() => sock.uncork());   // 모인 쓰기를 한꺼번에 내려보낸다
```

- Node의 `socket.cork()`는 `Writable` 스트림 버퍼 수준의 기능이다. 커널 소켓 옵션 `TCP_CORK`와 다르다.

### 2. 지연에 민감한 요청-응답 프로토콜이면 `TCP_NODELAY`를 켠다

```java
socket.setTcpNoDelay(true);   // StandardSocketOptions.TCP_NODELAY
```

```js
const sock = net.connect({ host, port, noDelay: true });  // 또는 sock.setNoDelay(true)
```

```c
int one = 1;
setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
```

- 켠 뒤에도 앱이 잘게 쓰면 작은 패킷이 그대로 나간다. 1번(한 번에 쓰기)과 같이 한다.
- 라이브러리·런타임이 이미 켜 두었을 수도 있다(아래 표의 Go, Node `http` 서버). 내가 쓰는 라이브러리의 기본값부터 확인한다.

### 3. 대용량 응답은 코르크로 헤더와 본문을 붙인다(리눅스)

```c
int on = 1, off = 0;
setsockopt(fd, IPPROTO_TCP, TCP_CORK, &on, sizeof on);
write(fd, hdr, hdr_len);                   /* 헤더: 아직 안 나감 */
sendfile(fd, file_fd, NULL, file_len);     /* 파일 본문 */
setsockopt(fd, IPPROTO_TCP, TCP_CORK, &off, sizeof off);   /* 마개를 뽑는다 = 한꺼번에 전송 */
```

- 헤더만 담긴 작은 세그먼트가 따로 나가지 않는다.
- 해제를 잊으면 매번 200ms 상한까지 기다린다(아래 장애 4).

### 4. 진단 — "고정 지연"이 보이면 패킷 간격을 잰다

```bash
# 요청 한 건의 세그먼트 간격 보기 (-ttt: 이전 패킷과의 시간차)
tcpdump -ni any -ttt 'tcp port 8080'

# 앱이 write를 몇 번 부르는지 보기
strace -f -e trace=write,writev,sendto,sendmsg -p <pid>

# 지연 ACK 타이머 현재값(ato), rtt, mss 확인
ss -tin dst <서버IP>
```

tcpdump에서 이런 모양이면 이 노트의 문제다(시간은 예시).

```text
 0.000000 IP c.5000 > s.8080: Flags [P.], length 50      <- 헤더
 0.040xxx IP s.8080 > c.5000: Flags [.], length 0        <- 약 40ms 뒤 ACK 단독
 0.000050 IP c.5000 > s.8080: Flags [P.], length 30      <- 그제야 본문
 0.000300 IP s.8080 > c.5000: Flags [P.], length 200     <- 응답
```

- 단서는 세 가지다. 데이터 없는 ACK가 **일정한 간격** 뒤에 오고, 그 직후 클라이언트가 나머지 조각을 보내며, `strace`에 `write`가 요청당 2번 이상 찍힌다.

## 장애 시나리오와 대처

### 1. 요청마다 ~40ms 고정 지연 (write-write-read)

- **현상**: 로컬·같은 랙인데도 요청 지연이 수십 ms로 일정하다. 부하와 상관없이 p50부터 높다.
- **보이는 형태**
  - 지연 히스토그램이 40ms(리눅스 지연 ACK 최소) 부근에 뾰족하게 몰린다.
  - 연결 하나로 직렬 요청을 보내면 처리량이 초당 약 25건(= 1000ms / 40ms, 계산상)에서 막힌다.
  - tcpdump에 위 모양(ACK 단독 → 나머지 조각)이 반복된다.
- **원인**: 클라이언트가 요청을 두 번 이상 나눠 쓰고(Nagle 켜짐), 서버는 요청이 덜 와서 응답도 ACK도 미룬다(지연 ACK).
- **대처**
  - 앱에서 요청을 한 번에 쓴다(버퍼링·`writev`).
  - 요청-응답형이면 클라이언트에 `TCP_NODELAY`를 켠다.
  - 서버가 응답을 두 번 나눠 쓰는 반대 방향도 같은 문제가 난다. 양쪽을 다 본다.

### 2. `TCP_NODELAY`를 켰더니 패킷 수 폭증·처리량 저하

- **현상**: 지연을 잡으려고 모든 소켓에 `TCP_NODELAY`를 켰다. CPU와 패킷 수가 늘고 대량 전송 처리량이 떨어졌다.
- **보이는 형태**
  - `ip -s link`·`sar -n DEV`에서 초당 패킷 수(pps)가 크게 늘었는데 바이트 수는 비슷하다.
  - tcpdump에 length가 수~수십 바이트인 세그먼트가 줄지어 있다.
- **원인**: 앱이 로그·스트림을 한 줄씩, 바이트 몇 개씩 쓴다. Nagle이 뭉쳐 주던 것을 끄자 RFC 896의 small-packet problem이 그대로 돌아왔다.
- **대처**
  - `TCP_NODELAY`는 "메시지를 한 번에 쓰는 앱"에 켠다. 잘게 쓰는 코드는 먼저 앱 버퍼링을 넣는다.
  - 대량 전송은 Nagle을 켜 두거나 `TCP_CORK`·`MSG_MORE`로 모은다.

### 3. 런타임·라이브러리를 바꿨더니 갑자기 느려짐

- **현상**: 같은 프로토콜 클라이언트를 Go에서 Java로(또는 Node HTTP 서버에서 raw `net` 서버로) 옮겼다. 요청당 수십 ms가 늘었다.
- **보이는 형태**: 기능 테스트는 통과한다. 부하·지연 테스트에서만 드러난다.
- **원인**: Nagle 기본값이 다르다. Go `TCPConn`과 Node `http` 서버는 Nagle을 끄고 시작한다. Java `Socket`과 Node `net.Socket`은 켜고 시작한다.
- **대처**
  - 소켓을 여는 코드에서 `TCP_NODELAY`를 명시적으로 설정한다. 기본값에 기대지 않는다.
  - 드라이버 설정(예: `tcpNoDelay` 옵션)을 문서에서 확인한다.

### 4. `TCP_CORK`를 풀지 않아 응답이 200ms씩 늦음

- **현상**: 정적 파일 서버 응답이 가끔 또는 늘 약 200ms 늦게 끝난다.
- **보이는 형태**: tcpdump에서 마지막 작은 세그먼트가 앞 세그먼트보다 약 200ms 뒤에 나간다.
- **원인**: 코드가 `TCP_CORK`를 켠 뒤 해제하지 않았다. 마지막 부분 프레임은 코르크 상한(200ms, tcp(7))이 지나서야 나간다.
- **대처**: 응답을 다 쓴 뒤 반드시 `TCP_CORK`를 0으로 되돌린다. 호출 단위로 쓰려면 `send(..., MSG_MORE)`를 쓴다(마지막 조각에는 플래그를 빼면 된다).

### 5. `TCP_QUICKACK`을 한 번 켰는데 지연이 다시 나타남

- **현상**: 수신 쪽에 `TCP_QUICKACK`을 설정해 지연이 사라졌다가, 시간이 지나자 다시 나타난다.
- **보이는 형태**: 연결 초반 요청은 빠르고, 이후 일부 요청에 40ms대 지연이 섞인다.
- **원인**: `TCP_QUICKACK`은 영구 설정이 아니다. 커널이 내부 판단으로 지연 ACK 모드로 되돌린다(tcp(7) "This flag is not permanent").
- **대처**
  - 송신 쪽 수정(한 번에 쓰기·`TCP_NODELAY`)이 근본 해법이다.
  - 수신 쪽만 고칠 수 있다면 `read` 직후마다 다시 설정하는 방식이 쓰인다. 이 옵션은 리눅스 전용이고 이식성이 없다.

## 핵심 문장

- Nagle은 "떠 있는 데이터가 있으면 작은 조각을 모은다", 지연 ACK는 "ACK를 잠깐 미뤄 합친다"이다. 각자는 패킷 수를 줄이는 좋은 장치다.
- 한 요청을 두 번 이상 나눠 쓰면, 둘째 조각은 첫 조각의 ACK를 기다리고 서버는 요청이 덜 와서 ACK를 미룬다. 그 결과 요청마다 지연 ACK 타이머만큼(리눅스 최소 40ms) 고정 지연이 붙는다.
- 1순위 해법은 앱에서 메시지를 한 번에 쓰는 것이고, 요청-응답형이면 `TCP_NODELAY`를 켠다.
- `TCP_NODELAY`는 앱이 잘게 쓰는 문제를 고치지 못한다. 켜면 작은 패킷이 그대로 나간다.
- Nagle 기본값은 런타임마다 다르다. 소켓을 열 때 명시적으로 정한다.

## 관련 주제·근거

- 선행: [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — 시퀀스·누적 ACK.
- 후속·연결
  - [23-socket-api](../23-socket-api/2-summary.md) — `write()`·`setsockopt()`, 부분 쓰기
  - `24-application-protocol-framing` — 메시지를 한 번에 쓰려면 경계를 알아야 한다. 초안: [systems/resp-protocol](../../systems/resp-protocol/2-summary.md)
  - [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) — SWS 회피(수신·송신 쪽).
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — HTTP 클라이언트·서버의 소켓 옵션.
- RFC 896 (Nagle, 1984) "Congestion Control in IP/TCP Internetworks" — small-packet problem, 41바이트·4000% <https://www.rfc-editor.org/rfc/rfc896>
- RFC 1122 <https://www.rfc-editor.org/rfc/rfc1122>
  - §4.2.3.2 When to Send an ACK Segment — 지연 ACK SHOULD, 0.5초 미만 MUST, 2세그먼트마다 SHOULD
  - §4.2.3.4 When to Send Data — Nagle SHOULD, 끌 수단 MUST
- RFC 9293 (TCP, 2022) <https://www.rfc-editor.org/rfc/rfc9293>
  - §3.7.4 Nagle Algorithm (SHLD-7, MUST-17)
  - §3.8.6.3 Delayed Acknowledgments (SHLD-18, MUST-40, SHLD-19)
  - 부록 A.3 Nagle Modification — Nagle × 지연 ACK의 나쁜 상호작용, Minshall 변형
- Linux man-pages
  - tcp(7) — `TCP_NODELAY`, `TCP_CORK`(200ms 상한), `TCP_QUICKACK`(영구 아님), `tcp_autocorking` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - send(2) — `MSG_MORE` <https://man7.org/linux/man-pages/man2/send.2.html>
  - ss(8) — `ato:` 필드 <https://man7.org/linux/man-pages/man8/ss.8.html>
- Linux 커널 소스
  - `include/net/tcp.h` — `TCP_DELACK_MIN (HZ/25)`, `TCP_DELACK_MAX (HZ/5)` <https://github.com/torvalds/linux/blob/master/include/net/tcp.h>
  - `net/ipv4/tcp_output.c` — `tcp_nagle_check()`의 Minshall 변형 <https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_output.c>
- Java `StandardSocketOptions.TCP_NODELAY` — 기본 FALSE <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/StandardSocketOptions.html>
- Node.js `net` — `socket.setNoDelay()`, `noDelay` 옵션 <https://nodejs.org/api/net.html> · `http.createServer` `noDelay` 기본 true(v18.0.0) <https://nodejs.org/api/http.html>
- Go `net.TCPConn.SetNoDelay` — "The default is true (no delay)" <https://pkg.go.dev/net#TCPConn.SetNoDelay>
- Stevens, 『TCP/IP Illustrated Vol.1』 2판 — Nagle·지연 ACK 절(장 번호 [?])
