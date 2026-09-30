# network/02-encapsulation — 캡슐화: 헤더가 붙고 벗겨지는 과정 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

층마다 필요한 정보가 다르다.\
TCP는 포트와 순서 번호가 필요하고, IP는 출발·도착 IP가 필요하고, 이더넷은 옆 장비의 MAC 주소가 필요하다.\
이 정보를 한 덩어리에 섞어 두면 층을 따로 바꿀 수 없다.\
그래서 각 층은 **자기 정보만 헤더로 앞에 붙이고**, 그 안의 내용은 건드리지 않는다.

```text
  보낼 때: 위층 데이터를 통째로 "짐"으로 보고, 앞에 자기 헤더를 붙인다      (캡슐화)
  받을 때: 자기 헤더만 읽고 떼어 낸 뒤, 나머지를 위층에 넘긴다              (역캡슐화)
```

  - *캡슐화(encapsulation)*: 위층의 PDU 전체를 자기 층의 데이터(payload)로 담고 헤더를 붙이는 것.
  - *payload*: 헤더 뒤에 실린 "짐". 이 층은 내용을 해석하지 않는다.

쉬운 예: 편지 → 봉투 → 택배 상자 → 트럭 컨테이너다.\
봉투에는 받는 사람이, 상자에는 배송지 주소가, 컨테이너에는 다음 물류센터가 적힌다.\
물류센터는 컨테이너 표지만 보고 옮기고, 편지는 열지 않는다.

똑같은 구조다.\
라우터는 IP 헤더(목적지 주소)로 다음 홉을 정한다. TCP 헤더와 HTTP 본문은 고치지 않는다.\
다만 여러 경로에 나눠 보낼 때(ECMP 해시)나 ACL 검사 때는 포트까지 읽는 경우가 있다.

실무 예:
- VPN이나 쿠버네티스 오버레이 네트워크는 **패킷 전체를 또 다른 패킷 안에 넣는다**(터널).
- 헤더가 한 벌 더 붙으니, 원래 1500바이트짜리 패킷이 링크에 안 들어간다.
- 이 오버헤드를 모르면 "작은 요청은 되는데 큰 응답만 멈추는" 장애를 만난다.

## 동작·원리

### 송신 — 위에서 아래로 헤더가 붙는다

```text
  응용                                      [ HTTP 메시지 ]
                                                  |
  전송                            [TCP 헤더 20+][ HTTP 메시지 ]            = 세그먼트
                                                  |
  인터넷                [IP 헤더 20+][TCP 헤더][ HTTP 메시지 ]              = IP 데이터그램
                                                  |
  링크   [이더넷 헤더 14][IP 헤더][TCP 헤더][ HTTP 메시지 ][FCS 4]         = 프레임
                                                  |
  물리                              0101 1100 ... (비트)
```

- 각 층은 위층이 준 것을 통째로 payload로 담는다.
- 이더넷만 **뒤에도** 붙인다. FCS(오류 검사 값)가 프레임 끝에 온다(04번).
- 숫자는 헤더의 최소 크기(바이트)다. 아래 표를 본다.

### 수신 — 아래에서 위로 헤더가 벗겨진다

```text
  링크    이더넷 헤더 읽기: 목적지 MAC이 나인가? FCS 맞나? EtherType = 0x0800(IPv4)
            --> 헤더·FCS 떼고 IP 계층으로
  인터넷  IP 헤더 읽기: 목적지 IP가 나인가? Protocol = 6(TCP)
            --> 헤더 떼고 TCP로
  전송    TCP 헤더 읽기: 목적지 포트 443 --> 그 포트의 소켓 찾기
            --> 헤더 떼고 소켓 수신 버퍼로
  응용    read()로 HTTP 메시지를 받는다
```

- 각 층은 **다음에 누구에게 넘길지**를 자기 헤더의 필드로 안다.
  - 이더넷의 EtherType(RFC 7042), IP의 Protocol 필드(RFC 791), TCP/UDP의 목적지 포트.
- 이렇게 헤더 필드로 위층을 고르는 것을 *역다중화(demultiplexing)*라 한다.
  - *역다중화*: 한 줄로 들어온 데이터를 헤더의 식별자를 보고 여러 위층 중 하나에 나눠 주는 것.

### 계층별 헤더 크기

```text
  헤더                크기(바이트)          근거
  -----------------   ------------------   ---------------------------------------------
  이더넷              14 (+FCS 4)          목적지 MAC 6 + 출발 MAC 6 + EtherType 2
  802.1Q VLAN 태그     +4                   TPID 0x8100 (RFC 7042)
  IPv4               20 ~ 60              IHL 4비트 × 4바이트, 최소 5 (RFC 791)
  IPv6               40 (고정)            + 확장 헤더 (RFC 8200)
  TCP                20 ~ 60              Data Offset 4비트 × 4바이트 (RFC 9293 §3.1)
  UDP                8 (고정)             포트 2+2, 길이 2, 체크섬 2 (RFC 768)
```

- IPv4의 IHL과 TCP의 Data Offset은 모두 "헤더 길이를 32비트(4바이트) 단위로 센 값"이다. 4비트이니 최대 15 × 4 = 60바이트다.
- 이더넷 payload(=IP 데이터그램)는 최대 1500바이트다(RFC 894). 이 1500이 이더넷의 **MTU**다.
  - *MTU(Maximum Transmission Unit)*: 링크가 한 프레임에 실을 수 있는 최대 payload 크기. 링크 헤더는 뺀 값이다.
- 그래서 옵션 없는 IPv4 + TCP면 한 세그먼트의 데이터는 최대 1500 − 20 − 20 = 1460바이트다.
  - 이 값이 TCP의 *MSS(Maximum Segment Size)*다. 한 세그먼트에 실을 수 있는 최대 데이터 크기다. TCP 헤더와 IP 헤더는 뺀 값이다.

### 헤더 = 고정 오프셋 레코드

헤더는 "몇 번째 바이트부터 몇 바이트가 무슨 필드"로 정해진 레코드다.

```text
  IPv4 헤더 (옵션 없음, 20바이트)
  오프셋  0        1        2        3
       +--------+--------+-----------------+
    0  |Ver|IHL |  TOS   |  Total Length   |
       +--------+--------+-----------------+
    4  |  Identification |Flags|Frag Offset|
       +--------+--------+-----------------+
    8  |  TTL   |Protocol| Header Checksum |
       +--------+--------+-----------------+
   12  |         Source Address            |
       +-----------------------------------+
   16  |       Destination Address         |
       +-----------------------------------+

  TCP 헤더 (옵션 없음, 20바이트)
       +-----------------+-----------------+
    0  |   Source Port   |    Dest Port    |
       +-----------------+-----------------+
    4  |          Sequence Number          |
       +-----------------------------------+
    8  |       Acknowledgment Number       |
       +--------+--------+-----------------+
   12  |DOff|rsv| Flags  |     Window      |
       +--------+--------+-----------------+
   16  |    Checksum     |  Urgent Pointer |
       +-----------------+-----------------+
```

- 필드 자리가 고정이라 파싱은 "오프셋으로 바로 읽기"다. 검색이 필요 없다.
- 가변 부분(옵션)이 있을 때는 길이 필드(IHL, Data Offset)를 먼저 읽고 다음 헤더의 시작점을 계산한다.
- 여러 바이트 필드는 **네트워크 바이트 순서(빅 엔디언)**로 적는다. 큰 자리 바이트가 먼저 온다(RFC 791 부록 B "Data Transmission Order" — 그림의 옥텟을 영어 읽는 순서대로 보낸다).

### 홉마다 바뀌는 헤더, 끝까지 가는 헤더

```text
  A ----[스위치]---- 라우터 R1 ---------- 라우터 R2 ---- B

  구간        이더넷 목적지 MAC     IP 출발/도착        IP TTL      TCP 포트
  A -> R1     R1의 MAC             A / B               64 (예시)   그대로
  R1 -> R2    R2의 MAC             A / B               63          그대로
  R2 -> B     B의 MAC              A / B               62          그대로
```

- **이더넷 헤더는 홉마다 새로 만든다.** 라우터는 받은 프레임의 이더넷 헤더를 버리고, 다음 홉용 헤더를 새로 붙인다.
- **IP 주소는 끝까지 그대로다.** 단, NAT 장비를 지나면 바뀐다(11번).
- **TTL은 홉마다 1씩 준다.** 그래서 IPv4 헤더 체크섬도 홉마다 다시 계산한다(RFC 791). IPv6는 이름이 Hop Limit이다(RFC 8200).
  - *TTL(Time To Live)*: 패킷이 거칠 수 있는 남은 홉 수. 0이 되면 버린다. 경로가 빙빙 도는(루프) 패킷을 없애기 위한 장치다.
- 스위치는 MAC 주소를 바꾸지 않는다. 목적지 MAC을 보고 포트로 내보낼 뿐이다(06번).
  - 단, VLAN 스위치는 포트 설정에 따라 802.1Q 태그(4바이트)를 붙이거나 뗀다. 프레임이 바뀌니 FCS도 다시 계산한다.

### 터널 — 패킷을 통째로 또 캡슐화

```text
  원래 패킷          [IP 20][TCP 20][데이터 1460]                        = 1500
  VXLAN으로 감싸면
  [외부 이더넷 14][외부 IP 20][UDP 8][VXLAN 8][내부 이더넷 14][원래 패킷 1500]
                  |<------- 외부 IP 데이터그램 = 1550 -------------------->|
```

- VXLAN은 이더넷 프레임 전체를 UDP 안에 담는다. 목적지 포트는 4789다(RFC 7348).
- 외부 링크 MTU가 1500이면 외부 IP 데이터그램도 1500을 넘을 수 없다.
  - 외부에 붙는 것은 외부 IP 20 + UDP 8 + VXLAN 8 + 내부 이더넷 14 = 50바이트다.
  - 그래서 안쪽 IP 패킷은 최대 1500 − 50 = **1450바이트**가 된다(외부가 IPv4이고 옵션이 없을 때).
- RFC 7348 §4.3은 VTEP(터널 끝점)이 VXLAN 패킷을 **단편화하면 안 된다(MUST NOT)**고 정한다. 그리고 물리망 MTU를 캡슐화로 커진 프레임이 들어가게 키우라고 권한다(RECOMMENDED). PMTUD도 쓸 수 있다(MAY).
  - 안쪽 MTU를 줄이는 것은 RFC 권고가 아니라 실무에서 흔히 쓰는 다른 대처다.
- IPsec·WireGuard·GRE 같은 다른 터널도 구조는 같다. 헤더 크기만 다르다.

## 쓰이는 자료구조·알고리즘

- **헤더 = 고정 오프셋 레코드** — C의 `struct`나 바이트 배열의 고정 위치로 읽는다. 길이 필드로 다음 헤더의 시작을 찾는 것은 TLV(Type-Length-Value) 파싱과 같다([24-application-protocol-framing](../README.md) — 영역 표 참고).
- **스택(push/pop)** — 송신은 헤더 push, 수신은 pop이다. 가장 나중에 붙은 헤더(링크)가 가장 먼저 벗겨진다. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md) 참고.
  - 리눅스 커널의 `sk_buff`는 버퍼 앞쪽에 여유 공간(headroom)을 두고, 아래층이 그 자리에 헤더를 앞으로 덧댄다. 데이터를 복사하지 않기 위해서다(kernel docs "struct sk_buff" — `headroom | data | tailroom` 배치).
- **역다중화 테이블** — EtherType·Protocol·포트 값으로 처리기를 찾는 "키 → 핸들러" 조회. 배열이나 해시 테이블([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md))로 구현한다.
- **인터넷 체크섬** — IPv4 헤더·TCP·UDP 체크섬은 16비트 1의 보수 합이다(RFC 1071). TTL처럼 필드 하나가 바뀌면 증분 갱신할 수 있다(RFC 1624).

## 적용 — 풀어나가는 법

### 1. 패킷에서 헤더를 층별로 본다

```bash
# -e: 링크 헤더(MAC)까지 출력, -n: 이름 변환 안 함, -v: IP의 TTL·ID·길이까지
tcpdump -eni eth0 -v 'tcp port 443' -c 5

# -XX: 링크 헤더까지 포함해 16진수로 — 오프셋을 직접 세어 보는 연습
tcpdump -ni eth0 -XX 'tcp port 443' -c 1
```

- `-e`는 "각 줄에 링크 수준 헤더를 출력"한다(tcpdump(1)). 출발·도착 MAC과 EtherType이 보인다.
- `-XX` 출력의 처음 14바이트가 이더넷 헤더다. 그다음 `45`로 시작하면 IPv4(버전 4, IHL 5 = 20바이트)다.

### 2. 코드로 헤더를 읽는다 — 고정 오프셋

```java
// 이더넷 프레임 바이트에서 IPv4/TCP 헤더 필드 꺼내기 (옵션 길이 반영)
static void parse(byte[] frame) {
    ByteBuffer b = ByteBuffer.wrap(frame);             // 기본이 빅 엔디언 = 네트워크 바이트 순서
    int etherType = b.getShort(12) & 0xFFFF;           // 오프셋 12~13
    if (etherType != 0x0800) return;                   // IPv4만

    int ip = 14;                                       // IP 헤더 시작
    int ihl = (b.get(ip) & 0x0F) * 4;                  // IHL × 4바이트
    int ttl = b.get(ip + 8) & 0xFF;
    int proto = b.get(ip + 9) & 0xFF;                  // 6 = TCP
    if (proto != 6) return;

    int tcp = ip + ihl;                                // TCP 헤더 시작 = IP 헤더 길이만큼 뒤
    int srcPort = b.getShort(tcp) & 0xFFFF;
    int dstPort = b.getShort(tcp + 2) & 0xFFFF;
    int dataOff = ((b.get(tcp + 12) & 0xF0) >>> 4) * 4; // Data Offset × 4바이트
    int payload = tcp + dataOff;                       // 응용 데이터 시작
    System.out.printf("ttl=%d %d -> %d payload@%d%n", ttl, srcPort, dstPort, payload);
}
```

- Java `byte`는 부호가 있어서 `& 0xFF`, `& 0xFFFF`로 부호 없는 값으로 바꾼다.
- 옵션을 무시하고 "IP 헤더는 20바이트"로 고정하면 옵션이 있는 패킷에서 TCP 포트를 잘못 읽는다.

### 3. 터널을 쓰면 MTU를 계산해 둔다

```bash
ip link show eth0            # 물리 인터페이스 mtu
ip link show vxlan0          # 터널 인터페이스 mtu — 물리보다 오버헤드만큼 작아야 한다

# 경로가 실제로 몇 바이트까지 통과하나: DF 켜고 크기를 바꿔 가며
ping -M do -s 1472 -c 2 10.0.0.2    # 1472 + ICMP 8 + IP 20 = 1500
ping -M do -s 1422 -c 2 10.0.0.2    # 1422 + 8 + 20 = 1450 (VXLAN 안쪽 예시)
```

- `-M do`는 DF 플래그를 켠다. 너무 큰 패킷은 거부된다(ping(8)).
- `-s`는 ICMP 데이터 바이트 수다. ICMP 헤더 8바이트가 더 붙는다(ping(8)). 여기에 IP 헤더 20을 더하면 IP 패킷 크기다.
- TCP라면 경계 장비에서 SYN의 MSS를 줄이는 방법(MSS clamping)도 있다.
  - `iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu`(iptables-extensions(8) 예시)

## 장애 시나리오와 대처

### 1. 터널·VPN 헤더 때문에 MTU 초과 — 큰 패킷만 실패

- **현상**
  - 연결은 되고, 작은 요청(헬스체크)도 된다.
  - 큰 응답이나 파일 업로드만 멈췄다가 한참 뒤 끊긴다.
  - TLS라면 핸드셰이크 도중 멈추기도 한다. 서버 인증서가 담긴 응답이 커서다.
- **보이는 형태**
  - `curl -v`가 특정 단계에서 진행이 없다.
  - tcpdump에 같은 큰 세그먼트의 재전송만 보이고 ACK가 없다.
  - 경계 장비가 ICMP를 막았다면 "Fragmentation Needed"(IPv4)나 "Packet Too Big"(IPv6)가 돌아오지 않는다.
- **원인**
  - 터널 헤더만큼 커진 패킷이 경로의 MTU를 넘는다. DF가 켜져 있으니 라우터가 버린다.
  - 라우터가 보낸 ICMP 알림이 방화벽에 막히면 송신자는 크기를 줄여야 한다는 걸 모른다. RFC 2923은 이를 "black hole"이라 부른다. 증상은 ping과 대화형 연결은 되는데 대량 전송은 첫 큰 패킷에서 막히는 것이다.
- **대처**
  - 터널 인터페이스·컨테이너 네트워크의 MTU를 오버헤드만큼 줄인다(VXLAN이면 1450).
  - 경계에서 TCP MSS clamping을 건다.
  - ICMP "Fragmentation Needed"/"Packet Too Big"은 막지 않는다.
  - 리눅스는 `tcp_mtu_probing`으로 ICMP 없이도 크기를 줄여 보게 할 수 있다(ip-sysctl).
  - 자세한 PMTUD는 [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md)에서 다룬다.

### 2. 오버레이 네트워크의 MTU 불일치 — 같은 클러스터 안에서만 간헐 실패

- **현상**: 파드 간 통신에서 큰 요청만 실패한다. 같은 노드 안에서는 되고, 노드를 건너면 실패한다.
- **보이는 형태**: 컨테이너 인터페이스 MTU는 1500인데 노드 간 경로는 VXLAN으로 감싸진다. 재전송·타임아웃이 늘어난다.
- **원인**: 같은 노드 안에서는 터널을 타지 않아 1500이 통과한다. 노드를 건너면 50바이트가 더 붙어 물리 MTU 1500을 넘는다. VTEP은 단편화하지 않는다(RFC 7348 MUST NOT).
- **대처**
  - 오버레이 쪽 MTU를 물리 MTU − 터널 오버헤드로 맞춘다.
  - 또는 물리망에 점보 프레임을 켜서 외부 MTU를 키운다(RFC 7348 권고).

### 3. 헤더를 고정 길이로 가정한 파서 — 옵션이 붙으면 엉뚱한 값

- **현상**: 패킷 분석 도구나 커스텀 프록시가 일부 트래픽에서만 포트·페이로드를 잘못 읽는다.
- **보이는 형태**: 포트 번호가 말이 안 되는 값으로 찍힌다. SYN 세그먼트(옵션이 많음)에서 특히 틀린다.
- **원인**: IP 헤더를 20바이트, TCP 헤더를 20바이트로 고정했다. 실제로는 IHL·Data Offset만큼 길어질 수 있다. SYN에는 MSS·Window Scale·SACK 같은 옵션이 흔히 붙는다.
- **대처**: 길이 필드(IHL, Data Offset)를 먼저 읽고 다음 헤더의 오프셋을 계산한다. 바이트 순서는 빅 엔디언으로 읽는다.

### 4. 오버헤드를 무시한 처리량 기대치

- **현상**: 1 Gbps 링크인데 응용 데이터는 1 Gbps가 안 나온다고 문의가 온다.
- **보이는 형태**: 인터페이스 카운터는 선로 속도에 가깝지만, 응용이 받는 바이트는 그보다 적다.
- **원인**: 프레임마다 헤더가 붙는다. 이더넷 14 + FCS 4 + IP 20 + TCP 20(옵션 제외)이 1460바이트 데이터마다 더해진다. 선로에는 프리앰블 등도 더 붙는다(04번).
- **대처**: 기대 처리량을 "데이터 ÷ (데이터 + 헤더)" 비율로 계산해 둔다. 터널을 쓰면 그만큼 더 뺀다.

## 핵심 문장

- 캡슐화는 위층 PDU 전체를 payload로 담고 자기 헤더를 앞에 붙이는 것이다. 각 층은 자기 헤더만 읽고 안은 열지 않는다.
- 받는 쪽은 헤더의 EtherType·Protocol·포트로 다음에 넘길 층을 고른다(역다중화).
- 헤더는 고정 오프셋 레코드다. 가변 부분은 길이 필드(IHL, Data Offset)로 건너뛴다.
- 이더넷 헤더는 홉마다 새로 붙고, IP 주소는 끝까지 간다(NAT 제외). TTL은 홉마다 줄어든다.
- 터널은 패킷을 한 번 더 캡슐화한다. 그 오버헤드만큼 안쪽 MTU를 줄이지 않으면 큰 패킷만 실패한다.

## 관련 주제·근거

- 선행: [01-layer-map-osi-tcpip](../01-layer-map-osi-tcpip/2-summary.md) — 층과 PDU 이름
- 후속·연결
  - [03-latency-bandwidth-bdp](../03-latency-bandwidth-bdp/2-summary.md) — 헤더가 붙은 프레임이 선로에 실리는 시간
  - [04-ethernet-and-mac](../04-ethernet-and-mac/2-summary.md) — 이더넷 헤더와 FCS
  - [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md) — MTU 초과 시 단편화·PMTUD·black hole.
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — IP·포트가 바뀌는 예외.
  - `24-application-protocol-framing` — 응용 계층의 길이 접두·TLV 프레이밍([영역 표](../README.md))
- RFC
  - RFC 791 IPv4 — 헤더 형식, IHL 최소 5, TTL·헤더 체크섬 재계산, 부록 B 바이트 순서 <https://www.rfc-editor.org/rfc/rfc791>
  - RFC 8200 IPv6 — 40바이트 고정 헤더, Next Header, Hop Limit <https://www.rfc-editor.org/rfc/rfc8200>
  - RFC 9293 TCP §3.1 — Data Offset, 헤더는 32비트의 정수배 <https://www.rfc-editor.org/rfc/rfc9293>
  - RFC 768 UDP — 8바이트 헤더 <https://www.rfc-editor.org/rfc/rfc768>
  - RFC 894 IP over Ethernet — EtherType 0x0800, 데이터 46~1500바이트 <https://www.rfc-editor.org/rfc/rfc894>
  - RFC 7042 — EtherType 목록, 802.1Q 0x8100 <https://www.rfc-editor.org/rfc/rfc7042>
  - RFC 7348 VXLAN — 8바이트 헤더, UDP 4789, VTEP 단편화 금지 <https://www.rfc-editor.org/rfc/rfc7348>
  - RFC 2923 — PMTUD black hole <https://www.rfc-editor.org/rfc/rfc2923>
  - RFC 1071 인터넷 체크섬 계산, RFC 1624 증분 갱신
- Linux man-pages·문서
  - kernel docs "struct sk_buff" <https://docs.kernel.org/networking/skbuff.html>
  - tcpdump(1) `-e`, `-XX`, `-v` <https://www.tcpdump.org/manpages/tcpdump.1.html>
  - ping(8) `-M do`, `-s` <https://man7.org/linux/man-pages/man8/ping.8.html>
  - iptables-extensions(8) TCPMSS <https://man7.org/linux/man-pages/man8/iptables-extensions.8.html>
  - ip-sysctl `tcp_mtu_probing`, `fib_multipath_hash_policy`(기본 0 = L3, 1 = L4) <https://docs.kernel.org/networking/ip-sysctl.html>
- RFC 2992 §2 — ECMP hash-threshold(흐름을 정하는 헤더 필드를 해시해 다음 홉 선택) <https://www.rfc-editor.org/rfc/rfc2992>
- bridge(8) — `pvid`(ingress 무태그 프레임의 VLAN)·`untagged`(egress에서 태그 제거) <https://man7.org/linux/man-pages/man8/bridge.8.html>
- Kurose & Ross 8판 1.5.2 "Encapsulation"
