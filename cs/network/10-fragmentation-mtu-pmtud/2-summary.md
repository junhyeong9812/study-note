# network/10-fragmentation-mtu-pmtud — 너무 큰 패킷은 어떻게 되고, "작은 건 되는데 큰 것만 멈추는" 장애는 왜 생기나 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

링크마다 한 번에 실어 나를 수 있는 최대 크기가 다르다.\
보내는 쪽 링크는 1500바이트를 허용해도, 중간의 VPN 터널은 1400바이트까지만 허용할 수 있다.\
그 좁은 구간을 만난 큰 패킷은 어떻게 해야 하나?

```text
  보낸 사람 ==1500==> R1 ==1500==> R2 --1400--> R3 ==1500==> 받는 사람
                                     ^
                                  좁은 구간 (경로 MTU = 1400)
```

쉬운 예: 큰 소파를 옮기는데 복도 중간에 좁은 문이 하나 있다.
- 방법 1: 그 문 앞에서 소파를 분해하고, 도착지에서 다시 조립한다 → **단편화(fragmentation)**
- 방법 2: 출발 전에 "가장 좁은 문이 몇 cm냐"를 알아내 거기 맞춰 작게 포장한다 → **경로 MTU 탐색(PMTUD)**

똑같은 구조다.\
IPv4는 두 방법을 다 허용하고, IPv6는 중간(라우터)에서의 분해를 없앴다.\
현대 인터넷은 분해를 피하고 방법 2를 쓴다. 그런데 방법 2는 "문이 좁다"는 알림(ICMP)이 돌아와야 동작한다.\
그 알림이 막히면 큰 소파만 문 앞에서 영영 멈춘다. 이것이 **PMTUD 블랙홀**이다.

실무에서 이 지식이 필요한 순간
- VPN·터널·오버레이(VXLAN 등)를 도입한 뒤 "작은 요청은 되는데 큰 응답이 멈춘다".
- TLS 핸드셰이크에서 서버 인증서가 오다가 멈춘다.
- 클라우드 VPC 안은 점보 프레임(9001), 인터넷은 1500처럼 구간마다 MTU가 다르다.

## 동작·원리

### MTU와 MSS — 헤더를 빼고 남는 것

```text
  이더넷 MTU 1500 (IP 패킷이 들어갈 수 있는 최대)
  +------------+------------+--------------------------------+
  | IPv4 20    | TCP 20     | 데이터 1460 = MSS               |
  +------------+------------+--------------------------------+
  |<------------------------ 1500 --------------------------->|

  IPv6이면: 1500 - 40(IPv6) - 20(TCP) = 1440
```

  - *MTU(Maximum Transmission Unit)*: 한 링크가 한 번에 나를 수 있는 IP 패킷의 최대 크기다. 이더넷은 보통 1500이다.
  - *경로 MTU(Path MTU, PMTU)*: 경로 위 모든 링크 MTU 중 **가장 작은 값**이다.
  - *MSS(Maximum Segment Size)*: TCP 세그먼트 하나에 실을 데이터의 최대 크기다. SYN 때 서로 알린다. 흔히 MTU − 40(IPv4) 또는 MTU − 60(IPv6)이다(iptables-extensions(8) TCPMSS 설명).

터널은 헤더를 하나 더 씌우므로 안쪽이 쓸 수 있는 크기가 준다.

```text
  VXLAN 예 (바깥 망 MTU 1500)
  +--------+-----+--------+-----------+----------------------------+
  | 바깥 IPv4 | UDP | VXLAN  | 안쪽 이더넷 | 안쪽 IP 패킷                  |
  |   20     |  8  |   8    |    14     |  1500 - 50 = 1450 까지        |
  +--------+-----+--------+-----------+----------------------------+
```

- VXLAN 헤더는 8바이트다(RFC 7348 §5). 바깥 IPv4·UDP와 안쪽 이더넷 헤더를 합치면 50바이트가 늘어난다. 이 수치는 위 헤더 크기를 더해 계산한 값이다.
- RFC 7348 §4.3은 VXLAN 터널 끝(VTEP)이 VXLAN 패킷을 조각내면 **안 된다**고 한다(MUST NOT). 받는 쪽은 조각을 조용히 버려도 된다(MAY). 그래서 바깥 망 MTU를 넉넉히 잡으라고 권한다(RECOMMENDED).

### IPv4 단편화 — 라우터가 쪼개고, 목적지가 붙인다

IPv4 헤더의 세 필드가 단편화를 맡는다(RFC 791 §3.1).

```text
  | Identification 16비트 | 0 | DF | MF | Fragment Offset 13비트 |
                                 |    |    (단위: 8바이트)
                                 |    +-- MF(More Fragments): 뒤에 조각이 더 있다
                                 +------- DF(Don't Fragment): 쪼개지 마라
```

  - *Identification*: 같은 원본에서 나온 조각들이 공유하는 번호다. 조각날 수 있는 데이터그램이면 출발지·목적지·프로토콜 조합 안에서 유일해야 한다(RFC 791).
    - DF=1이고 조각이 아닌(atomic) 데이터그램은 유일할 필요가 없다. ID는 재조립에만 쓴다(RFC 6864 §4.1).
  - *Fragment Offset*: 이 조각의 데이터가 원본 데이터의 어디서 시작하는지를 8바이트 단위로 적는다.

예: 총 4000바이트(헤더 20 + 데이터 3980) 패킷이 MTU 1500 링크를 만나면(예시)

```text
  조각   데이터 크기   offset(×8바이트)   MF
  1      1480         0    (0 바이트)     1
  2      1480         185  (1480 바이트)  1
  3      1020         370  (2960 바이트)  0
  각 조각 = IPv4 헤더 20 + 데이터.  1480은 8의 배수여야 해서 고른 값이다.
```

- 조각은 **최종 목적지에서만** 다시 붙인다. 중간 라우터는 붙이지 않는다.
- 조각 하나라도 잃으면 원본 전체를 잃는다. 재조립 제한 시간 안에 다 모이지 않으면 버리고 ICMP 11/1(재조립 시간 초과)을 보낼 수 있다(RFC 792).
- DF가 켜져 있으면 쪼갤 수 없다. 버릴 수는 있다(RFC 791 §3.2).
- 모든 IP 모듈은 68바이트 패킷은 쪼개지 않고 전달할 수 있어야 한다. 헤더 최대 60 + 최소 조각 8이기 때문이다(RFC 791 §3.2).

### 단편화가 실전에서 나쁜 이유

Cloudflare "Broken packets: IP fragmentation is flawed"의 정리

```text
  조각 1: [IP][TCP/UDP 헤더 = 포트 있음][데이터...]
  조각 2: [IP][데이터...]                  <- 포트가 없다
  조각 3: [IP][데이터...]                  <- 포트가 없다
```

- 포트는 **첫 조각에만** 있다. 포트로 거르는 방화벽, 포트로 해시하는 부하 분산(ECMP)이 나머지 조각을 제대로 다루지 못한다.
  - 첫 조각과 나머지 조각이 다른 서버로 가면 재조립이 불가능하다.
- 재조립 전까지 조각을 메모리에 들고 있어야 한다. 메모리 고갈 공격의 표적이 된다.
- 조각 하나만 잃어도 전체를 다시 보내야 한다.

### IPv6 — 라우터는 쪼개지 않는다

- IPv6에서 단편화는 **출발지만** 한다. 라우터는 쪼개지 않는다(RFC 8200 §4.5).
- 모든 링크 MTU는 1280 이상이어야 한다(RFC 8200 §5 "IPv6 minimum link MTU").
- 경로 MTU 탐색(RFC 8201)을 강하게 권한다. 안 하는 최소 구현은 1280 이하로만 보내면 된다(RFC 8200 §5).
- 그래서 IPv6에서 너무 큰 패킷은 **버려지고 ICMPv6 Packet Too Big(type 2)**만 돌아온다. 이것이 막히면 우회로가 없다.

### PMTUD — DF를 켜고, "너무 크다"를 들으며 줄인다

```text
  보낸 사람                    R2 (다음 링크 MTU 1400)              받는 사람
  |-- 1500, DF=1 ---------->  |  못 보냄, 쪼갤 수도 없음
  |<- ICMP 3/4 "frag needed", Next-Hop MTU = 1400 --|
  |  이 목적지의 PMTU = 1400으로 기억, TCP는 MSS를 줄인다
  |-- 1400, DF=1 --------------------------------------------------->|
```

RFC 1191의 규칙
- 라우터는 ICMP 3/4의 하위 16비트에 다음 홉 MTU를 담아야 한다(MUST, §4).
- 호스트는 이 메시지를 받으면 PMTU 추정치를 줄여야 한다(MUST, §3).
- 호스트는 PMTU를 68 아래로 줄이면 안 되고, 이 메시지를 근거로 **늘려서도** 안 된다(MUST, §3).
- 경로가 바뀌어 PMTU가 커졌는지는 가끔만 확인한다. 줄어든 뒤 5분 안에 늘리려는 시도를 하면 안 되고(MUST NOT), 10분을 권한다(§3).
- 캐시된 PMTU는 10분 정도 줄지 않으면 첫 링크 MTU로 되돌린다(should, §6.3).

리눅스에서
- 기본 설정(`ip_no_pmtu_disc=0` → `IP_PMTUDISC_WANT`)에서 TCP(`SOCK_STREAM`) 소켓은 RFC 1191 PMTUD를 한다. 그래서 TCP 패킷에는 보통 DF가 켜진다(IP_MTU_DISCOVER(2const)).
  - `ip_no_pmtu_disc`를 켜거나 소켓에 `IP_PMTUDISC_DONT`를 주면 끌 수 있다(같은 문서).
- UDP에서 `IP_PMTUDISC_DO`를 켜면 알려진 PMTU보다 큰 데이터그램은 `EMSGSIZE`로 거절된다(같은 문서).
- 캐시된 PMTU는 `min_pmtu`(기본 552) 아래로 내려가지 않는다. 캐시 유지 시간은 `mtu_expires`다(kernel ip-sysctl 문서).
  - PTB가 `min_pmtu`보다 작은 값을 알리면 PMTU를 `min_pmtu`에 두고 그 경로 MTU를 **잠근다**. 잠긴 경로에서 `IP_PMTUDISC_WANT` 소켓은 DF를 끄고 보낸다. 그래서 중간에서 조각날 수 있다(`net/ipv4/route.c` `__ip_rt_update_pmtu()`, `include/net/ip.h` `ip_dont_fragment()`).

### PMTUD 블랙홀 — 알림이 오지 않으면

```text
  보낸 사람                   방화벽 (ICMP 전부 차단)     R2 (MTU 1400)
  |-- 1500, DF=1 -------------------------------------->| 버림
  |                         X<-- ICMP 3/4 ------------|  (방화벽이 버림)
  |-- 1500, DF=1 (재전송) ------------------------------>| 버림
  |-- 1500, DF=1 (재전송) ------------------------------>| 버림  ... 영영 안 줄인다
```

- RFC 8899는 이것을 **ICMP 블랙홀**이라 부른다. PTB(너무 크다) 메시지가 송신자에게 오지 않아, 패킷이 전달되지 않는다는 사실을 송신자가 모르는 상태다(§2).
- 작은 패킷은 MTU 아래라 멀쩡하다. 그래서 증상이 "**작은 건 되는데 큰 것만 멈춘다**"다.
  - 3-way handshake는 된다(작은 패킷).
  - 작은 요청·응답은 된다.
  - 큰 응답, TLS 서버 인증서, 파일 업로드·다운로드가 멈춘다.
- ICMP가 막히는 흔한 자리: 보안 정책상 ICMP 전면 차단, 클라우드 네트워크 ACL, ICMP를 다른 서버로 보내는 부하 분산(ECMP)(Cloudflare 글).

### 블랙홀을 피하는 방법

1. **ICMP 3/4, ICMPv6 Packet Too Big을 허용한다.** 근본 해결이다(09번).
2. **MSS 클램핑** — 경로 중간 장비가 SYN의 MSS 옵션을 줄여 쓴다. 양 끝이 애초에 작은 세그먼트만 보낸다.
   - iptables `TCPMSS --clamp-mss-to-pmtu`의 존재 이유가 바로 "ICMP Fragmentation Needed / Packet Too Big을 막는 ISP·서버"다. 문서가 드는 증상은 "웹 브라우저가 연결 후 데이터 없이 멈춤, 큰 메일만 멈춤, scp가 핸드셰이크 뒤 멈춤"이다(iptables-extensions(8)).
   - TCP에만 통한다. UDP(QUIC·DNS)는 따로 대처해야 한다.
3. **PLPMTUD / DPLPMTUD** — ICMP에 기대지 않고, 전송 계층이 크기를 바꿔 가며 탐침을 보내 성공·손실로 PMTU를 찾는다(RFC 4821 TCP용, RFC 8899 데이터그램용).
   - 리눅스 TCP: `tcp_mtu_probing` 기본 0(끔). 1은 ICMP 블랙홀을 감지했을 때만 켠다. 2는 항상 켠다(tcp(7)).
   - QUIC는 UDP 페이로드 1200바이트를 지원하지 못하는 경로에서는 쓰면 안 된다(MUST NOT, RFC 9000 §14). 그 위로는 DPLPMTUD로 탐색할 수 있다(§14.3).
4. **인터페이스 MTU를 낮춘다** — 터널 인터페이스의 MTU를 오버헤드만큼 줄여 애초에 큰 패킷을 만들지 않는다.

## 쓰이는 자료구조·알고리즘

- **목적지별 캐시 + 만료 타이머** — PMTU는 목적지(경로)마다 기억하고, 일정 시간 뒤 잊는다(RFC 1191 §6.2·§6.3, 리눅스 `mtu_expires`). 해시 테이블에 시간 필드를 붙인 구조다. 개념: [해시맵](../../data-structure/05-hashmap/2-summary.md).
- **재조립 큐** — 목적지는 (출발지, 목적지, 프로토콜, Identification)이 같은 조각을 한데 모은다. offset 순으로 빈틈을 채워 가며, 제한 시간이 지나면 통째로 버린다. 구간을 채우는 문제다.
- **탐색 구간 좁히기** — PLPMTUD는 "성공한 최대 크기(search_low)"와 "실패한 최소 크기(search_high)" 사이를 탐침으로 좁혀 간다. 리눅스 `tcp_base_mss`는 search_low의 초깃값이다(kernel ip-sysctl 문서). 정답이 구간 안의 한 값이라는 점에서 [이분 탐색](../../algorithm/06-binary-search/2-summary.md)과 같은 발상이다. 실제 탐침 크기 선택 방식은 구현마다 다르다 [?].
- **정수 산술** — offset은 8바이트 단위라 조각 데이터 크기는 (마지막 조각을 빼고) 8의 배수여야 한다.

## 적용 — 풀어나가는 법

### 1. 경로 MTU를 재 본다

```bash
# DF를 켜고 크기를 바꿔 가며 ping (IPv4: 데이터 + ICMP 8 + IP 20)
ping -M do -s 1472 -c 3 10.0.2.10     # 1500 바이트: 되면 경로 MTU >= 1500
ping -M do -s 1372 -c 3 10.0.2.10     # 1400 바이트
#  -> 로컬 인터페이스보다 크면 "message too long" 류 에러, 중간에서 막히면 "Frag needed" 응답 또는 무응답

tracepath -n 10.0.2.10                 # 홉별로 pmtu 변화를 보여 준다 (root 불필요)

ip link show eth0                      # 인터페이스 mtu
ip route get 10.0.2.10                 # 이 목적지로 캐시된 PMTU가 있으면 mtu가 함께 보인다 [?]
```

- `ping -M do`는 DF를 켜고 커널의 PMTU 검사를 받는다. `-M probe`는 DF를 켜되 PMTU 검사를 건너뛴다(ping(8)).
- 응답이 **아예 없으면**(에러도 없이) 그 크기에서 ICMP가 막히고 있을 가능성이 높다. 블랙홀의 신호다.

### 2. 패킷으로 블랙홀을 확인한다

```bash
# 송신 측: 큰 세그먼트가 같은 길이로 재전송만 반복되는지
tcpdump -ni eth0 'tcp and host 10.0.2.10 and greater 1400'

# ICMP "너무 크다"가 도착하는지 (IPv4 3/4, IPv6 Packet Too Big)
tcpdump -ni eth0 'icmp[icmptype] == icmp-unreach and icmp[icmpcode] == 4'
tcpdump -ni eth0 'icmp6 and ip6[40] == 2'
```

- `ss -ti dst 10.0.2.10`의 `mss`, `pmtu`, `retrans` 값도 함께 본다. 재전송이 오르는데 `mss`가 줄지 않으면 PTB가 안 오는 것이다.

### 3. 소켓에서 DF와 EMSGSIZE를 다룬다 (C, UDP)

```c
int fd = socket(AF_INET, SOCK_DGRAM, 0);
int val = IP_PMTUDISC_DO;                               /* 항상 DF, 큰 데이터그램은 거절 */
setsockopt(fd, IPPROTO_IP, IP_MTU_DISCOVER, &val, sizeof val);
connect(fd, (struct sockaddr *)&dst, sizeof dst);

if (send(fd, buf, len, 0) < 0 && errno == EMSGSIZE) {
    int mtu; socklen_t sl = sizeof mtu;
    getsockopt(fd, IPPROTO_IP, IP_MTU, &mtu, &sl);      /* 커널이 아는 현재 경로 MTU */
    /* 앱이 메시지를 mtu - 28 (IPv4 20 + UDP 8) 이하로 나눠 다시 보낸다 */
}
```

- UDP 앱은 커널이 대신 나눠 주지 않는다(DF일 때). 크기 조절은 앱 책임이다.
- `IP_MTU`는 연결된(connect한) 소켓에서 현재 알려진 경로 MTU를 읽는다. `getsockopt` 전용이다(IP_MTU(2const)). IP_MTU_DISCOVER(2const)도 EMSGSIZE 뒤에 이 옵션으로 MTU를 읽으라고 안내한다.

### 4. 게이트웨이·터널에서 MSS를 클램핑한다

```bash
# 이 장비를 지나는 TCP SYN의 MSS를 나가는 경로 MTU에 맞게 줄인다
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
# 또는 고정값
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360
```

- 두 규칙은 iptables-extensions(8) TCPMSS 항목의 형식이다. `1360`은 예시 값이다.
- `--set-mss`는 이미 더 작은 MSS를 키우지 않는다(리눅스 2.6.25+).

### 5. 클라우드에서

- AWS VPC 안은 점보 프레임(9001)을 쓸 수 있다. 인터넷 게이트웨이·VPN 연결, 그리고 transit gateway를 쓰지 않는 리전 간 트래픽은 1500까지다. 리전 간 VPC 피어링은 8500까지다(AWS "Network MTU").
- 그 경계를 넘을 때 DF가 켜진 큰 패킷은 버려지고 ICMP 3/4가 돌아와야 한다. 보안 그룹과 **네트워크 ACL**이 이 ICMP를 막지 않는지 확인한다(같은 문서).

## 장애 시나리오와 대처

### 1. PMTUD 블랙홀 — VPN 너머에서 큰 응답만 멈춘다

- **현상**: VPN으로 붙은 사용자만, 로그인·작은 API는 되는데 목록 조회(큰 JSON), 파일 다운로드, 일부 페이지가 무한 로딩이다.
- **보이는 형태**
  - 클라이언트: 연결은 성립, 응답 헤더 일부만 오거나 아무것도 안 오다가 타임아웃.
  - 서버 `tcpdump`: 1500바이트 근처의 같은 세그먼트가 재전송된다. ICMP 3/4는 보이지 않는다.
  - `ss -ti`에 `retrans`가 오른다. `mss`는 처음 값 그대로다(예: 1460. TCP 타임스탬프 옵션을 쓰면 12바이트를 빼 1448).
- **원인**: 터널 오버헤드로 경로 MTU가 줄었다. 그런데 "너무 크다" ICMP가 방화벽·ACL에 막혀 서버가 크기를 줄이지 못한다.
- **대처**
  - 근본: 경로의 방화벽·보안 그룹·네트워크 ACL에서 ICMP 3/4(IPv6 type 2)를 허용한다.
  - 즉시 우회: VPN 게이트웨이에서 MSS 클램핑(`--clamp-mss-to-pmtu`)을 건다. 또는 터널 인터페이스 MTU를 낮춘다.
  - 보조: 리눅스 서버에 `tcp_mtu_probing=1`을 두면 블랙홀을 감지했을 때 탐침으로 크기를 줄인다(tcp(7)).

### 2. TLS 핸드셰이크가 인증서 단계에서 멈춘다

- **현상**: `curl`이 `TLS handshake` 단계에서 멈췄다가 타임아웃난다. 같은 서버에 `ping`, `nc -vz 443`은 된다.
- **보이는 형태**
  - `openssl s_client -connect host:443`이 ClientHello를 보낸 뒤 서버 응답을 기다리며 멈춘다.
  - 서버 쪽 캡처에서 인증서 체인을 담은 큰 세그먼트들이 재전송된다.
- **원인**
  - ClientHello는 작아서 통과한다.
  - 서버 인증서(체인)는 여러 개의 꽉 찬 세그먼트로 오므로 MTU 문제에 가장 먼저 걸린다.
  - 즉 시나리오 1과 같은 PMTUD 블랙홀이다. TLS 문제가 아니라 IP 계층 문제다.
- **대처**: 시나리오 1과 같다. 추가로 `ping -M do -s <크기>`로 통과하는 최대 크기를 찾아 MSS 클램핑 값을 정한다.

### 3. 오버레이 네트워크(VXLAN 등)에서 파드·컨테이너 간 큰 요청만 실패

- **현상**: 같은 노드의 파드끼리는 되는데, 다른 노드의 파드로 가는 큰 요청만 실패하거나 느리다.
- **보이는 형태**: 노드 간 캡처에서 조각난 VXLAN 패킷이 보이거나, 큰 패킷이 아예 사라진다.
- **원인**
  - 파드 인터페이스 MTU가 1500인데 바깥 망도 1500이다.
  - VXLAN이 50바이트를 더하므로 1500을 넘는다.
  - VTEP은 조각내지 않고(RFC 7348 MUST NOT), 중간에서 조각나도 받는 쪽이 버릴 수 있다(MAY).
- **대처**
  - 오버레이 인터페이스 MTU를 바깥 MTU − 오버헤드(예: 1450)로 낮춘다.
  - 또는 바깥 망 MTU를 키운다(점보 프레임). RFC 7348도 바깥 MTU를 넉넉히 두라고 권한다.

### 4. 단편화된 UDP가 사라진다 — DNS 큰 응답·UDP 기반 프로토콜

- **현상**: 작은 UDP 메시지는 되는데 큰 메시지(예: 큰 DNS 응답)만 간헐적으로 실패하거나 TCP로 재시도되며 느려진다.
- **보이는 형태**: 송신 측은 조각 여러 개를 보냈는데, 수신 측에는 첫 조각만 오거나 아무것도 오지 않는다.
- **원인**: 방화벽이 포트 없는 뒤 조각을 버리거나, 부하 분산이 조각들을 다른 서버로 보낸다. Cloudflare 글이 인용한 측정에서는 IPv4 호스트 약 6%, IPv6 호스트 약 10%가 들어오는 조각을 막았다. 또 서버 30~55%가 단편화 헤더가 있는 IPv6 패킷을 버렸다.
- **대처**
  - UDP 애플리케이션은 단편화가 안 일어나는 크기로 보낸다. IPv6 최소 MTU 1280을 기준으로 잡는 것이 흔한 선택이다.
  - QUIC처럼 DPLPMTUD를 구현한 프로토콜을 쓴다(RFC 8899, RFC 9000 §14.3).

## 핵심 문장

- 경로 MTU는 경로 위 링크 MTU의 최솟값이다. TCP MSS는 대략 그 값에서 IP·TCP 헤더(IPv4 40, IPv6 60)를 뺀 것이다.
- IPv4 라우터는 DF가 꺼진 패킷을 쪼갤 수 있다. 조각은 목적지에서만 붙고, 하나라도 잃으면 전체를 잃는다. IPv6 라우터는 쪼개지 않는다.
- PMTUD는 DF를 켜고 "너무 크다"(IPv4 ICMP 3/4, IPv6 Packet Too Big)를 들으며 크기를 줄인다. 이 ICMP가 막히면 블랙홀이 된다.
- 블랙홀의 지문은 "**연결·작은 요청은 되는데 큰 응답·TLS 인증서·파일 전송만 멈춘다**"이다. 터널·VPN·오버레이가 있는 곳에서 가장 먼저 의심한다.
- 대처는 ICMP 허용(근본), MSS 클램핑·인터페이스 MTU 조정(우회), PLPMTUD·DPLPMTUD(ICMP에 기대지 않는 탐색)다.

## 관련 주제·근거

- 선행
  - [09-icmp-ping-traceroute](../09-icmp-ping-traceroute/2-summary.md) — ICMP 3/4, Packet Too Big, ICMP 필터링
  - [02-encapsulation](../02-encapsulation/2-summary.md) — 헤더가 쌓이는 구조, 터널 오버헤드
- 후속·연결
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) — 인증서 전송 단계에서 멈추는 증상
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — ECMP 등 경로 선택
  - [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — 블랙홀에서 보이는 재전송
  - [37-http3-quic](../37-http3-quic/2-summary.md) — UDP 위 DPLPMTUD, 1200바이트 최소
  - [50-network-diagnostics](../50-network-diagnostics/2-summary.md) — `tracepath`·`ss -ti`·`tcpdump`.
  - [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- RFC
  - RFC 791 — §3.1 Identification·DF·MF·Fragment Offset(8바이트 단위), §3.2 DF면 단편화 불가·68바이트 규칙·576바이트 수신 <https://www.rfc-editor.org/rfc/rfc791>
  - RFC 6864 §4.1 — atomic 데이터그램의 ID는 유일할 필요 없음, ID는 단편화·재조립에만 <https://www.rfc-editor.org/rfc/rfc6864>
  - RFC 792 — Time Exceeded code 1(재조립 시간 초과), Destination Unreachable code 4 <https://www.rfc-editor.org/rfc/rfc792>
  - RFC 1191 — PMTUD. §3 호스트 규칙(MUST: 줄이기, 68 하한, PTB로 늘리지 않기, 5분·1분 하한, 10분·2분 권장), §4 Next-Hop MTU 필드, §6.3 약 10분 뒤 캐시 되돌리기 <https://www.rfc-editor.org/rfc/rfc1191>
  - RFC 8200 — IPv6. §4.5 출발지만 단편화, §5 최소 링크 MTU 1280 <https://www.rfc-editor.org/rfc/rfc8200>
  - RFC 8201 — IPv6 PMTUD <https://www.rfc-editor.org/rfc/rfc8201>
  - RFC 4821 — PLPMTUD(TCP 등) <https://www.rfc-editor.org/rfc/rfc4821>
  - RFC 8899 — DPLPMTUD. §2 블랙홀·ICMP 블랙홀 정의 <https://www.rfc-editor.org/rfc/rfc8899>
  - RFC 7348 — VXLAN. §4.3 VTEP 단편화 금지(MUST NOT)·조각 버림 허용(MAY)·바깥 MTU 여유 권장, §5 VXLAN 헤더 8바이트 <https://www.rfc-editor.org/rfc/rfc7348>
  - RFC 9000 §14 — QUIC 최소 1200바이트, §14.3 DPLPMTUD <https://www.rfc-editor.org/rfc/rfc9000>
- Linux
  - IP_MTU_DISCOVER(2const) — `IP_PMTUDISC_WANT/DONT/DO/PROBE`, SOCK_STREAM은 PMTUD, `EMSGSIZE` <https://man7.org/linux/man-pages/man2/IP_MTU_DISCOVER.2const.html>
  - IP_MTU(2const) — 연결된 소켓의 현재 경로 MTU, getsockopt 전용 <https://man7.org/linux/man-pages/man2/IP_MTU.2const.html>
  - tcp(7) — `tcp_mtu_probing`(기본 0), `tcp_base_mss` <https://man7.org/linux/man-pages/man7/tcp.7.html>
  - kernel "IP Sysctl" — `min_pmtu`(552), `mtu_expires`, `tcp_mtu_probing`, `tcp_base_mss`(search_low) <https://docs.kernel.org/networking/ip-sysctl.html>
  - `net/ipv4/route.c` `__ip_rt_update_pmtu()`(min_pmtu 미만이면 lock), `include/net/ip.h` `ip_dont_fragment()`(WANT는 잠기지 않았을 때만 DF) <https://github.com/torvalds/linux/blob/master/net/ipv4/route.c>
  - iptables-extensions(8) — `TCPMSS`, `--clamp-mss-to-pmtu`, `--set-mss` <https://man7.org/linux/man-pages/man8/iptables-extensions.8.html>
  - ping(8) `-M do|want|probe|dont`, tracepath(8) <https://man7.org/linux/man-pages/man8/ping.8.html>
- Cloudflare, "Broken packets: IP fragmentation is flawed" — 첫 조각에만 포트, ECMP·방화벽 문제, 측정치 <https://blog.cloudflare.com/ip-fragmentation-is-broken/>
- AWS, "Network maximum transmission unit (MTU) for your EC2 instance" — 9001, 1500(IGW·VPN·TGW 없는 리전 간), 8500(리전 간 VPC 피어링), PMTUD, 네트워크 ACL <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/network_mtu.html>
- 교재: Kurose & Ross 8판 4.3 "The Internet Protocol (IP)"(IPv4 데이터그램 형식·IPv6). 단편화 설명이 실린 절 번호는 판마다 달라 확인하지 못했다 [?]
