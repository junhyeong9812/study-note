# network/09-icmp-ping-traceroute — IP는 실패를 어떻게 알리고, ping·traceroute는 그걸 어떻게 이용하나 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

IP는 "최선을 다해 보내 볼게"라는 프로토콜이다.\
패킷이 중간에 버려져도 IP 자체는 아무 말도 하지 않는다.\
그러면 보낸 쪽은 "경로가 없어서"인지, "너무 커서"인지, "루프에 빠져서"인지 알 수 없다.

ICMP는 이런 사정을 **출발지에 되돌려 알려 주는** 통로다.

```text
  보낸 사람 ----[패킷]----> 라우터 R  "이 패킷은 못 보내요"
      ^                        |
      +----[ICMP: 이유 + 원래 패킷 머리]---+
```

쉬운 예: 반송된 우편물이다.\
우체국은 편지를 못 전하면 "수취인 불명" 도장을 찍어 돌려보낸다.\
봉투(원래 주소)가 함께 돌아오므로 어느 편지 얘기인지 알 수 있다.

똑같은 구조다.\
ICMP 오류 메시지는 **이유(type/code)**와 **원래 패킷의 앞부분**을 담아 돌아온다.\
받은 쪽 커널은 그 앞부분을 보고 어느 소켓의 일인지 찾는다.

단, 우체국이 항상 반송해 주지는 않는다.\
RFC 792도 ICMP가 IP를 신뢰성 있게 만드는 장치가 아니고, 오류 보고가 돌아온다는 보장도 없다고 적는다.

실무에서 이 지식이 필요한 순간
- `ping`은 되는데 서비스가 안 된다. 또는 그 반대다.
- `traceroute` 결과의 `* * *`와 중간 홉 손실을 해석한다.
- 보안팀이 "ICMP 전부 차단"을 제안한다. 그러면 큰 응답만 멈추는 장애가 생긴다(10번).

## 동작·원리

### ICMP의 자리 — IP 위에 실리지만 IP의 일부

```text
  +-----------------+-----------------------------------------------+
  | IP 헤더          | ICMP                                          |
  | protocol = 1    | type 1B | code 1B | checksum 2B | 나머지 4B     |
  |                 | 원래 IP 헤더 + 원래 데이터 앞부분 (오류 메시지일 때) |
  +-----------------+-----------------------------------------------+
```

- ICMP는 IP 헤더의 protocol 번호 1로 실린다(RFC 792). 모양은 상위 프로토콜 같지만, RFC 792는 "IP의 일부이고 모든 IP 모듈이 구현해야 한다"고 적는다.
- 오류 메시지에는 원래 패킷의 IP 헤더와 데이터 앞 64비트(8바이트)가 담긴다(RFC 792).
  - 8바이트면 TCP·UDP의 출발지·목적지 포트가 들어간다. 그래서 커널이 어느 연결의 일인지 찾을 수 있다.
  - 라우터는 터널링 때문에 이것으로는 부족하다고 보고, ICMP 전체가 576바이트를 넘지 않는 선에서 가능한 한 많이 담아야 한다(SHOULD, RFC 1812 §4.3.2.3).

### 주요 메시지

```text
  IPv4 type/code                            쓰임
  8 / 0   Echo Request                      ping 보내기
  0 / 0   Echo Reply                        ping 응답
  3 / 0   Destination Unreachable: net      망에 도달 불가
  3 / 1                        : host       호스트에 도달 불가
  3 / 3                        : port       UDP 포트에 받는 프로그램 없음 (traceroute 종착 신호)
  3 / 4                        : frag needed and DF set   너무 큰데 쪼개지 말라고 함 -> PMTUD (10번)
  11 / 0  Time Exceeded: TTL 초과(전달 중)     루프, traceroute 중간 홉
  11 / 1  Time Exceeded: 재조립 시간 초과      조각이 다 안 옴 (10번)
  5       Redirect                          "더 가까운 게이트웨이가 있다"
  4       Source Quench                     폐기됨 (RFC 6633)

  ICMPv6 (RFC 4443): 1 Destination Unreachable, 2 Packet Too Big, 3 Time Exceeded,
                     4 Parameter Problem, 128 Echo Request, 129 Echo Reply
```

- type·code 값은 RFC 792와 RFC 4443의 정의다.
- Source Quench는 RFC 6633이 폐기했다. RFC 9293도 TCP는 받은 Source Quench를 조용히 버려야 한다고 정한다(MUST-55).
- IPv6에서 "너무 크다"는 별도 타입(2, Packet Too Big)이다. IPv6 라우터는 조각내지 않으므로 이 메시지가 더 중요하다(10번).

### 오류에 대한 오류는 없다

RFC 1122 §3.2.2는 다음을 받았을 때 ICMP 오류를 보내면 **안 된다**(MUST NOT)고 정한다.

```text
  - ICMP 오류 메시지            (오류의 오류 -> 무한 반복 방지)
  - IP 브로드캐스트·멀티캐스트 목적지 패킷
  - 링크 계층 브로드캐스트로 온 패킷
  - 첫 조각이 아닌 조각
  - 출발지가 호스트 하나를 가리키지 않는 패킷 (0, 루프백, 브로드캐스트 등)
```

- 브로드캐스트에 오류로 답하면, 받은 호스트 전부가 한꺼번에 ICMP를 쏟아내 망이 마비된다. RFC 1122는 이것을 "broadcast storm" 방지 이유로 든다.

### ICMP 오류가 내 소켓에 닿는 길

```text
  ICMP 3/1 도착
     |
     v
  커널: 안에 담긴 "원래 IP 헤더 + 포트 8바이트" 읽기
     |  protocol=6(TCP), 10.0.1.23:51000 -> 203.0.113.10:443 (예시)
     v
  해당 TCP 연결 찾기 -> 에러 전달
```

- TCP는 ICMP 오류를 그 오류를 일으킨 연결로 돌려보내야 한다(MUST-54, RFC 9293 §3.9.2.2).
- RFC 9293은 ICMP 오류를 둘로 나눈다.
  - **소프트 오류**: Destination Unreachable code 0·1·5, Time Exceeded, Parameter Problem. 일시적일 수 있으므로 연결을 끊으면 **안 된다**(MUST-56). 앱에 알리는 것은 권장이다(SHLD-25).
  - **하드 오류**: Destination Unreachable code 2~4. 연결을 끊는 것이 권장이다(SHLD-26).
  - 다만 code 4(frag needed)는 실제로는 PMTUD 신호로 쓰인다. 보낼 크기를 줄이라는 뜻이다(RFC 1191, 10번).
- 그래서 연결 중 "host unreachable"을 한 번 받았다고 연결이 바로 끊기지는 않는다. 재전송을 계속하다가 결국 타임아웃으로 드러나는 경우가 많다.
- 단, **연결 수립 중**(SYN을 보낸 뒤)에는 소프트 오류도 하드 오류처럼 다루는 구현이 널리 퍼져 있다고 RFC 9293 같은 절이 적는다. 그래서 `connect()`는 ICMP host unreachable을 받자마자 `EHOSTUNREACH`로 실패할 수 있다.

### ping — Echo Request / Echo Reply

```text
  나                                           대상
  |-- ICMP 8/0  id=0x1a2b seq=1  [데이터 56B] --->|
  |<- ICMP 0/0  id=0x1a2b seq=1  [같은 데이터] ----|   RTT = 받은 시각 - 보낸 시각
  |-- ICMP 8/0  id=0x1a2b seq=2 ----------------->|
  |        (응답 없음)                             |   손실로 셈
```

- identifier와 sequence number는 요청과 응답을 짝짓는 데 쓴다(RFC 792).
  - identifier는 TCP·UDP의 포트처럼 "어느 ping 프로세스인가"를 가리키는 데 쓸 수 있다.
  - sequence number는 요청마다 하나씩 늘린다.
- 받은 쪽은 Echo Request의 데이터를 그대로 돌려줘야 한다(MUST, RFC 1122 §3.2.2.6). 모든 호스트는 Echo 서버 기능을 구현해야 한다(같은 절 MUST). 실제로는 방화벽이 막을 수 있다.
- 리눅스 `ping` 기본 데이터는 56바이트다. ICMP 헤더 8바이트를 더해 ICMP 64바이트가 된다(ping(8)).
- 응답은 **대상 커널**이 직접 한다. 애플리케이션은 관여하지 않는다. 이것이 "ping 된다 ≠ 서비스 된다"의 이유다.

### traceroute — TTL을 1부터 늘려 가며 한 홉씩 드러낸다

```text
  TTL=1  나 --> R1 (TTL 0 -> 버림)         R1 --> 나: ICMP 11/0   "1홉은 R1"
  TTL=2  나 --> R1 --> R2 (TTL 0)          R2 --> 나: ICMP 11/0   "2홉은 R2"
  TTL=3  나 --> R1 --> R2 --> 목적지        목적지 --> 나: ICMP 3/3 (포트 없음)  "도착"
```

- 라우터는 TTL이 0이 되면 버리고 Time Exceeded를 보내야 한다(RFC 1812 §5.3.1). traceroute는 이 규칙을 이용한다.
- 리눅스 traceroute(8)의 기본 동작
  - UDP 탐침을 "쓰일 것 같지 않은" 포트 33434부터 하나씩 올려 가며 보낸다.
  - 목적지에 닿으면 ICMP port unreachable이 온다. TCP 방식(`-T`)이면 닫힌 포트는 RST, 열린 포트는 SYN-ACK가 온다(열린 포트에는 RST로 답해 연결을 버린다). 그것이 종료 신호다.
  - TTL마다 탐침 3개를 보내고, 최대 30홉까지 간다. 제한 시간 안에 응답이 없으면 `*`를 찍는다.
  - `-I`는 ICMP Echo, `-T`는 TCP SYN(기본 포트 80)을 탐침으로 쓴다. 방화벽이 UDP·ICMP를 막을 때 `-T -p 443`처럼 허용된 포트를 쓴다.
  - 결과 뒤에 `!H`(host unreachable), `!N`(net unreachable), `!X`(관리적 차단), `!F`(frag needed) 같은 표시가 붙을 수 있다.
- 각 홉에 찍히는 주소는 원칙상 그 라우터가 **ICMP를 내보낸 인터페이스**의 주소다(MUST, 단 "달리 정한 경우 제외" — RFC 1812 §4.3.2.4). 그래서 같은 라우터라도 방향에 따라 다른 주소로 보일 수 있다.
  - 실제 장비는 설정에 따라 **패킷이 들어온 인터페이스** 주소를 쓰기도 한다(리눅스 `icmp_errors_use_inbound_ifaddr=1`, kernel ip-sysctl 문서).

### traceroute 해석의 함정

```text
   1  10.0.1.1       0.5 ms   0.4 ms   0.5 ms
   2  192.0.2.1      9.8 ms   * 45.1 ms          <- 중간 홉만 느리고 손실
   3  198.51.100.7  10.2 ms  10.1 ms  10.3 ms    <- 그 뒤는 정상
   (출력은 예시)
```

- 2홉만 느리고 3홉이 정상이면, 2홉 라우터는 **데이터를 잘 전달하고 있다.**
  - 라우터는 ICMP 오류 생성 속도를 제한할 수 있어야 한다(SHOULD, RFC 1812 §4.3.2.8).
  - 리눅스도 기본으로 Destination Unreachable·Time Exceeded 등의 전송 간격을 대상별 1000ms로 제한한다(icmp(7) `icmp_ratelimit`, `icmp_ratemask`).
  - 즉 중간 홉의 `*`와 높은 RTT는 "ICMP를 늦게·덜 만든다"일 수 있다. 진짜 손실은 **마지막 홉까지 이어질 때**만 의미가 있다.
- 돌아오는 ICMP는 다른 경로로 올 수 있다. RTT는 "가는 길 + 오는 길"이다.
- 탐침마다 포트가 달라지면 부하 분산 장비가 탐침을 다른 경로로 보낼 수 있다. 그러면 존재하지 않는 경로가 이어 붙어 보인다 [?].

## 쓰이는 자료구조·알고리즘

- **점진적 탐색(TTL을 1씩 늘리기)** — 경로 길이를 모르므로 깊이를 1, 2, 3…으로 늘리며 한 단계씩 드러낸다. 깊이 제한을 늘려 가는 반복 심화(iterative deepening)와 같은 발상이다.
- **해시 맵(요청-응답 짝짓기)** — ping은 (identifier, sequence) → 보낸 시각을 기억했다가 응답이 오면 RTT를 계산한다. traceroute도 탐침(포트·TTL)과 돌아온 ICMP 안의 원래 헤더를 짝짓는다. 개념: [해시맵](../../data-structure/05-hashmap/2-summary.md).
- **토큰 버킷(속도 제한)** — 리눅스는 `icmp_ratemask`에 해당하는 ICMP의 호스트 전체 전송량을 `icmp_msgs_per_sec`(기본 10000)과 버킷 크기 `icmp_msgs_burst`(기본 10000)로 제한한다(kernel ip-sysctl 문서 "token bucket").
- **역다중화(demultiplexing)** — ICMP 오류에 담긴 원래 헤더의 (프로토콜, 주소, 포트)로 소켓을 찾는다. TCP 연결 조회와 같은 키다.

## 적용 — 풀어나가는 법

### 1. 계층별로 끊어서 확인한다

```text
  ping 대상        -> IP 도달성 (커널끼리)
  traceroute       -> 어느 홉까지 가나
  nc -vz 대상 443  -> TCP 포트가 열려 있나 (커널 accept 큐까지)
  curl -v https:// -> 앱이 실제로 응답하나
```

- 위에서 아래로 내려가며 "어디까지 되는가"를 찾는다. ping 하나로 결론 내지 않는다.

### 2. 명령 모음

```bash
ping -c 4 10.0.1.10                 # 4번만
ping -c 3 -t 1 8.8.8.8              # TTL=1: 첫 라우터가 Time Exceeded를 돌려준다
ping -M do -s 1472 -c 3 10.0.1.10   # DF 켜고 1472+8+20 = 1500바이트 (MTU 시험, 10번)

traceroute -n example.com           # 이름 풀이 없이 (빠름)
traceroute -n -I example.com        # ICMP Echo 탐침
traceroute -n -T -p 443 example.com # TCP SYN 443 탐침 (방화벽 우회)
tracepath -n example.com            # 권한 없이, 경로 MTU까지 표시

tcpdump -ni any icmp                                  # ICMP 전부
tcpdump -ni any 'icmp[icmptype] == icmp-timxceed'     # Time Exceeded만
tcpdump -ni any 'icmp[icmptype] == icmp-unreach'      # Destination Unreachable만
sysctl net.ipv4.icmp_ratelimit net.ipv4.icmp_ratemask net.ipv4.ping_group_range
```

- 리눅스는 ICMP datagram(ping) 소켓으로 root 없이 ping을 보낼 수 있다. 허용할 그룹은 `ping_group_range`로 정한다. 커널 기본값 `1 0`은 "아무 그룹도 허용 안 함"이다(icmp(7)). 배포판이 다르게 설정할 수 있다.

### 3. 코드로 "살아 있나"를 확인할 때 (Java)

```java
// (X) ping 흉내 — 권한이 없으면 TCP 7번(echo) 포트 연결로 대신한다 (Javadoc)
boolean up = InetAddress.getByName(host).isReachable(2_000);

// (O) 실제 서비스 포트로 TCP 연결을 시도한다
try (Socket s = new Socket()) {
    s.connect(new InetSocketAddress(host, 443), 2_000);   // 2초(예시)
    // 커널이 3-way handshake를 끝냈다 = 포트가 열려 있다 (앱이 건강한지는 별개)
} catch (ConnectException e) {          // RST: 포트 닫힘 (ECONNREFUSED)
} catch (NoRouteToHostException e) {    // 경로/호스트 도달 불가
} catch (SocketTimeoutException e) {    // 무응답: 방화벽 드롭·블랙홀·호스트 다운
}
```

- `isReachable`은 ICMP Echo를 쓸 권한이 있으면 쓰고, 없으면 TCP 7번 포트 연결을 시도한다. 방화벽 때문에 도달 가능해도 false가 나올 수 있다(Javadoc).
  - OpenJDK 유닉스 구현은 7번 포트에서 RST(connection refused)를 받아도 true다(`Inet4AddressImpl.c` `tcp_ping4()`). false는 조용히 버려져 타임아웃될 때 나온다.
- 헬스 체크는 가능한 한 **앱 수준 요청**(`/health` 같은 HTTP 요청)으로 한다.

## 장애 시나리오와 대처

### 1. ICMP 전면 차단 → PMTUD가 깨져 큰 응답만 멈춘다

- **현상**: 로그인·작은 API는 되는데 큰 파일 다운로드, 큰 JSON 응답, TLS 핸드셰이크(인증서 전송)에서 멈춘다. VPN·터널 구간에서 흔하다.
- **보이는 형태**
  - 연결은 되는데(3-way handshake 성공) 데이터가 오다가 멈춘다.
  - 송신 측 `tcpdump`에 같은 큰 세그먼트의 재전송만 반복된다.
  - 기대했던 ICMP 3/4(IPv6는 Packet Too Big)는 보이지 않는다.
- **원인**: 방화벽이 ICMP를 전부 막았다. 경로 중간의 작은 MTU 링크가 "너무 크다(3/4)"를 보내도 송신자에게 닿지 않는다. 송신자는 크기를 줄이지 않고 계속 재전송한다(PMTUD 블랙홀, 10번).
- **대처**
  - 최소한 ICMP 3/4(IPv4)와 ICMPv6 type 2(Packet Too Big)는 허용한다. RFC 4890은 ICMPv6 Destination Unreachable, Packet Too Big, Time Exceeded code 0 등을 "버려서는 안 되는 트래픽"으로 분류한다.
  - AWS에서는 보안 그룹뿐 아니라 네트워크 ACL도 ICMP를 막을 수 있다(AWS "Network MTU").
  - 당장은 MSS 클램핑으로 우회한다(10번).

### 2. ping은 되는데 서비스는 안 된다

- **현상**: 모니터링은 "호스트 UP"인데 사용자는 접속이 안 된다.
- **보이는 형태**: `ping` 정상, `curl` 타임아웃 또는 `Connection refused`, 앱 로그에 요청 없음.
- **원인**: Echo Reply는 커널이 한다. 앱 프로세스가 죽었거나, 멈췄거나(스레드 고갈), 포트 방화벽이 막아도 ping은 된다.
- **대처**
  - 헬스 체크를 L4(TCP 연결) 이상, 가능하면 L7(HTTP 응답 내용)로 바꾼다.
  - 계층별 확인 순서(ping → traceroute → `nc -vz` → `curl -v`)로 어디서 끊기는지 찾는다.

### 3. ping은 안 되는데 서비스는 된다

- **현상**: "서버가 죽었다"는 신고. 실제로 웹은 잘 된다.
- **보이는 형태**: `ping` 100% 손실, `curl` 정상.
- **원인**: 대상 또는 중간 방화벽이 ICMP Echo를 막는다. 클라우드 보안 그룹에 ICMP 허용 규칙이 없는 경우가 흔하다.
- **대처**
  - 도달성은 `traceroute -T -p 443`이나 TCP 연결로 확인한다.
  - Echo를 허용할지는 정책으로 정한다. 단, Echo를 막더라도 오류 메시지(3/4, Packet Too Big)는 막지 않는다(시나리오 1).

### 4. traceroute 중간 홉의 손실·지연을 장애로 오판한다

- **현상**: 중간 라우터 한 곳에서 50% 손실, 200ms 지연이 보여 통신사에 장애를 신고했다.
- **보이는 형태**: 그 홉만 `*`가 섞이고 RTT가 높다. 그 뒤 홉과 최종 목적지는 정상이다.
- **원인**
  - 그 라우터가 ICMP 생성 속도를 제한하거나 낮은 우선순위로 처리한다(RFC 1812 §4.3.2.8).
  - 패킷 **전달**은 정상이고, **자기 앞으로 ICMP를 만드는 일**만 느리다.
- **대처**
  - 손실·지연이 **최종 목적지까지 이어지는지**로 판단한다.
  - 여러 번, 여러 방식(`-I`, `-T`)으로 반복해 본다.
  - 앱 지표(재전송률, RTT)와 함께 본다.

### 5. traceroute가 방화벽에서 `* * *`로 끝난다

- **현상**: 기본 traceroute가 어떤 홉 이후로 모두 `*`다. 그런데 서비스는 된다.
- **보이는 형태**: 기본(UDP 33434+)과 `-I` 모두 끊기지만, `-T -p 443`은 목적지까지 간다.
- **원인**: 경로 중간·목적지 방화벽이 "쓰이지 않는 UDP 포트"와 ICMP Echo를 막는다(traceroute(8) 설명).
- **대처**: 서비스가 실제로 쓰는 프로토콜·포트로 추적한다(`-T -p 443`, `-T -p 25` 등).

## 핵심 문장

- ICMP는 IP의 오류·진단 통로다. 오류 메시지에는 원래 패킷의 헤더와 앞부분이 담겨 있어, 커널이 어느 소켓의 일인지 찾는다.
- ICMP 오류는 보장되지 않는다. ICMP 오류에 대한 오류, 브로드캐스트에 대한 오류는 보내지 않는다.
- ping은 커널끼리의 Echo다. **ping 된다 ≠ 서비스 된다**, ping 안 된다 ≠ 서비스 안 된다.
- traceroute는 TTL을 1씩 늘려 각 라우터의 Time Exceeded로 한 홉씩 드러낸다. 끝은 port unreachable·echo reply·(TCP 방식이면) RST 또는 SYN-ACK로 안다.
- 중간 홉만의 손실은 ICMP 속도 제한일 수 있다. 끝까지 이어지는 손실만 진짜다.
- ICMP를 전부 막으면 PMTUD가 깨진다. "너무 크다"(IPv4 3/4, IPv6 Packet Too Big)는 막지 않는다.

## 관련 주제·근거

- 선행: [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — TTL 감소와 Time Exceeded
- 후속·연결
  - [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md) — ICMP 3/4·Packet Too Big에 기대는 PMTUD와 블랙홀
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — ICMP 없이 조용히 사라진 상대와 재전송 타임아웃
  - [50-network-diagnostics](../50-network-diagnostics/2-summary.md) — 진단 명령 종합.
  - [48-firewalls-and-network-policy](../48-firewalls-and-network-policy/2-summary.md) — ICMP 허용 정책
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- RFC
  - RFC 792 — ICMP. 서론(IP의 일부, 신뢰성 보장 아님, ICMP에 대한 ICMP 없음), type/code 정의, 원래 헤더 + 64비트, Echo의 identifier·sequence <https://www.rfc-editor.org/rfc/rfc792>
  - RFC 1122 §3.2.2 — ICMP 오류를 보내면 안 되는 경우(MUST NOT), §3.2.2.6 Echo 서버 구현(MUST) <https://www.rfc-editor.org/rfc/rfc1122>
  - RFC 1812 — §4.3.2.3 원래 패킷을 576바이트까지(SHOULD), §4.3.2.4 ICMP 출발지 주소 = 내보내는 인터페이스(MUST), §4.3.2.8 속도 제한(SHOULD), §5.3.1 TTL과 Time Exceeded <https://www.rfc-editor.org/rfc/rfc1812>
  - RFC 9293 §3.9.2.2 — TCP의 ICMP 처리: MUST-54, Source Quench 무시(MUST-55), 소프트 오류로 끊지 않음(MUST-56), 하드 오류(SHLD-26), 연결 수립 중에는 소프트 오류를 하드로 다루는 구현이 흔함 <https://www.rfc-editor.org/rfc/rfc9293>
  - RFC 6633 — Source Quench 폐기 <https://www.rfc-editor.org/rfc/rfc6633>
  - RFC 4443 — ICMPv6 type 목록 <https://www.rfc-editor.org/rfc/rfc4443>
  - RFC 4890 §4.3.1 — ICMPv6 필터링 권고(정보성): 버려서는 안 되는 메시지 <https://www.rfc-editor.org/rfc/rfc4890>
- Linux man-pages
  - ping(8) — 기본 56바이트, `-M do`, `-t`, `-s` <https://man7.org/linux/man-pages/man8/ping.8.html>
  - traceroute(8) — 기본 UDP 33434+, TTL당 3탐침, 최대 30홉, `-I`, `-T`(기본 포트 80, 닫힌 포트 RST·열린 포트 SYN-ACK), `!H`·`!N`·`!X`·`!F` <https://man7.org/linux/man-pages/man8/traceroute.8.html>
  - tracepath(8) <https://man7.org/linux/man-pages/man8/tracepath.8.html>
  - icmp(7) — `icmp_ratelimit`(1000ms), `icmp_ratemask`, `ping_group_range`(기본 `1 0`) <https://man7.org/linux/man-pages/man7/icmp.7.html>
- kernel "IP Sysctl" — `icmp_msgs_per_sec`(10000), `icmp_msgs_burst`(토큰 버킷), `icmp_errors_use_inbound_ifaddr` <https://docs.kernel.org/networking/ip-sysctl.html>
- Java `InetAddress.isReachable` Javadoc — ICMP Echo 또는 TCP 7번 포트 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/InetAddress.html>
- OpenJDK `src/java.base/unix/native/libnet/Inet4AddressImpl.c` — `tcp_ping4()`: 연결 성공 또는 `ECONNREFUSED`면 true <https://github.com/openjdk/jdk/blob/master/src/java.base/unix/native/libnet/Inet4AddressImpl.c>
- AWS, "Network maximum transmission unit (MTU) for your EC2 instance" — 네트워크 ACL도 ICMP를 막을 수 있음 <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/network_mtu.html>
- 교재: Kurose & Ross 8판 5.6 "ICMP: The Internet Control Message Protocol"
