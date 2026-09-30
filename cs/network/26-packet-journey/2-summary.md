# network/26-packet-journey — 내 프로세스의 바이트가 상대 프로세스에 닿기까지 한 장으로 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

네트워크 지식은 계층별로 따로 배운다.\
그런데 장애는 "어느 계층 문제인지 모르는 상태"로 온다.\
"요청이 안 간다"는 한 문장 뒤에 DNS, 라우팅, ARP, NAT, 방화벽, 소켓 큐 중 무엇이든 숨어 있을 수 있다.

이 노트는 패킷 **하나**를 처음부터 끝까지 따라간다.\
구간마다 "무엇이 바뀌고, 무엇으로 보이고, 어떻게 깨지나"를 한 장에 모은다.\
각 구간의 원리는 해당 노트의 몫이다. 여기서는 **이음새**만 본다.

쉬운 예: 국제 소포다.\
주소(최종 목적지)는 처음부터 끝까지 그대로다.\
그런데 구간마다 운송장은 새로 붙는다. "우리 동네 우체국 → 공항", "공항 → 상대국 공항", "상대국 공항 → 배달 트럭".

똑같은 구조다.\
**IP 주소는 끝에서 끝까지 거의 그대로**(NAT 예외), **MAC 주소는 홉마다 새로** 붙는다.

실무 예:
- `curl`이 멈췄다. SYN이 내 NIC를 떠났는지, 게이트웨이에 닿았는지, 상대가 RST를 보냈는지를 구간별로 좁혀야 한다.
- 사내망에서 클라우드 서버로 가는 요청이 가끔 끊긴다. 중간 NAT의 연결 추적 표가 원인일 수 있다.

## 동작·원리

### 무대 — 예시 네트워크

주소는 문서용 예시 대역(RFC 5737)과 사설 대역을 썼다.

```text
  [호스트 A]                  [스위치]        [라우터/NAT R1]                     [인터넷 라우터들]        [서버 B]
  10.0.1.10                                  안쪽 10.0.1.1                                              203.0.113.50
  MAC aa:..:0a  ---- 포트1 --[ SW ]-- 포트9 --- MAC aa:..:01                                           :443
                                             바깥 198.51.100.7  ---- R2 ---- R3 ---- ... ---- Rn ---- (NIC)
  프로세스: curl                                                                                     프로세스: 웹 서버
```

### 한 장 요약 — 송신 호스트에서 수신 프로세스까지

```text
 구간              하는 일                                         바뀌는 것                     관련 노트
 ---------------   --------------------------------------------   ---------------------------   -----------
 1 프로세스         이름 해석, socket/connect, write               -                             27, 23
 2 커널 TCP/IP      세그먼트화, IP 헤더, 라우팅(최장 접두사)          포트·SEQ·TTL=64 설정           15~18, 08
 3 커널 이웃/ARP    다음 홉(게이트웨이)의 MAC 찾기                   dst MAC = 게이트웨이 MAC       05
 4 커널 -> NIC      qdisc -> 드라이버 -> TX 링 -> DMA -> 선          -                             25
 5 스위치           MAC 표 조회, 해당 포트로만 전달(모르면 플러딩)     MAC·IP 안 바꿈(VLAN 태그 예외)  06
 6 라우터 R1        L2 벗김, TTL-1, NAT(src IP·포트 변경), 새 L2       TTL, src IP/port, MAC 전부      08, 11
 7 인터넷 라우터들   홉마다 L2 벗김, TTL-1, 최장 접두사로 다음 홉       TTL, MAC                      08, 13
 8 서버 쪽 경계      방화벽·LB(DNAT일 수도)                           (LB면 dst IP/port)             48, 46
 9 서버 NIC -> 커널  RX 링 -> softirq -> IP -> TCP -> 소켓 버퍼        -                             25
 10 서버 프로세스    accept/recv, 응답 write -> 역방향으로 1~9          -                             23
```

아래는 구간별 해설이다.

### 1~2. 프로세스와 커널 — "어디로 보낼지"는 커널이 정한다

```text
  curl https://example.com
    |  (1) 이름 -> IP: getaddrinfo()/DNS  ....................... 27번
    |  (2) socket(), connect(203.0.113.50:443)  ................ 23번
    |      커널: SYN 전송, 3-way handshake  ...................... 15번
    |  (3) TLS 핸드셰이크 ........................................ 29번
    |  (4) write(HTTP 요청 바이트)
    v
  커널 TCP: 바이트를 세그먼트로 자름 (MSS 단위), 시퀀스 번호, 재전송 대비 보관
  커널 IP : src 10.0.1.10, dst 203.0.113.50, TTL 64 (리눅스 기본 ip_default_ttl)
            라우팅 조회 -> "dst가 10.0.1.0/24 밖이다 -> default via 10.0.1.1"
```

- 라우팅 표에서 목적지 주소와 **가장 길게 일치하는 접두사**의 항목을 고른다. 어디에도 안 맞으면 기본 경로(0.0.0.0/0)를 쓴다(08번).
- `ip route get 203.0.113.50`을 치면 커널이 실제로 고를 경로와 출발 주소가 나온다.

### 3. ARP — 서버의 MAC이 아니라 **게이트웨이의** MAC을 묻는다

```text
  A: "10.0.1.1 가진 사람 MAC 알려 줘" (브로드캐스트)  ---->  모든 LAN 호스트
  R1: "10.0.1.1은 aa:..:01"                         <----  (유니캐스트 응답)
  A의 이웃 캐시: 10.0.1.1 -> aa:..:01 (일정 시간 보관)
```

- 목적지 203.0.113.50은 다른 네트워크다. A는 서버의 MAC을 알 필요도 없고 알 수도 없다.
- 이더넷 프레임의 목적지 MAC은 **다음 홉(게이트웨이)** 의 MAC이다. IP 헤더의 목적지는 여전히 서버다.
- 캐시에 없으면 ARP가 끝날 때까지 패킷은 이웃 큐에서 기다린다(25번).

```text
  A가 내보내는 프레임
  +----------------------+----------------------------+------------------+---------+
  | Ethernet             | IP                         | TCP              | 데이터   |
  | dst aa:..:01 (R1)    | src 10.0.1.10              | src 51000        | TLS     |
  | src aa:..:0a (A)     | dst 203.0.113.50  TTL 64   | dst 443          | 레코드   |
  +----------------------+----------------------------+------------------+---------+
```

### 4. 커널 → NIC

- qdisc → 드라이버 → TX 링(DMA) → NIC가 선으로 보낸다. 상세는 25번 노트.
- 로컬 tcpdump의 송신 탭은 qdisc 뒤, 드라이버 직전이다. "tcpdump에 보였다 = 내 커널이 드라이버에 넘겼다"까지만 뜻한다(25번).

### 5. 스위치 — L2만 본다

```text
  MAC 표 (자가 학습)
  +---------------+------+
  | aa:..:0a (A)  | 포트1 |   <- A의 프레임이 포트1로 들어올 때 src MAC을 배움
  | aa:..:01 (R1) | 포트9 |
  +---------------+------+
  dst aa:..:01 -> 포트9로만 전달.  표에 없으면 모든 포트로 플러딩.
```

- 스위치는 MAC 주소·IP 헤더를 **바꾸지 않는다**. IP·TTL은 보지도 않는다(K&R 6.4).
  - 예외: 트렁크 포트로 내보낼 때 VLAN 태그(4바이트)를 붙이고, 액세스 포트로 내보낼 때 뗀다(K&R 6.4.4). 이때는 태그와 FCS(프레임 끝 오류 검사값)가 바뀐다.
- VLAN이 있으면 같은 스위치여도 VLAN이 다르면 다른 L2 망이다(06번).

### 6. 라우터 R1 (+NAT) — L2를 새로 쓰고, 주소를 바꾼다

```text
  들어온 프레임                                 나가는 프레임
  Eth dst R1-안쪽 / src A                       Eth dst R2 / src R1-바깥            <- MAC 전부 새로
  IP  src 10.0.1.10  dst 203.0.113.50 TTL 64    IP  src 198.51.100.7  dst 같음 TTL 63   <- NAT: src 변경, TTL -1
  TCP src 51000      dst 443                    TCP src 40001(예시)   dst 443          <- NAT: 포트 변경
                                                NAT 표: 198.51.100.7:40001 <-> 10.0.1.10:51000
```

- 라우터는 TTL을 **최소 1 줄여야 한다(MUST)**. 0이 되면 버리고 출발지에 ICMP Time Exceeded를 보내야 한다(MUST)(RFC 1812 §5.3.1).
- TTL이 바뀌므로 IPv4 헤더 체크섬도 다시 계산한다. 전체를 새로 계산하지 않고 바뀐 필드만 반영하는 증분 갱신 방법이 있다(RFC 1624).
- NAT는 사설 주소를 공인 주소로, 포트도 바꾼다. 응답이 돌아오면 표를 거꾸로 찾아 되돌린다. 표 항목이 사라지면 응답이 갈 곳이 없다(11번).

### 7. 인터넷 구간 — 홉마다 같은 일의 반복

```text
  홉:        A -> R1      R1 -> R2      R2 -> R3      ...     Rn -> B
  src MAC:   A            R1            R2                    Rn
  dst MAC:   R1           R2            R3                    B
  src IP:    10.0.1.10    198.51.100.7  198.51.100.7          198.51.100.7   (NAT 뒤 고정)
  dst IP:    203.0.113.50 (끝까지 같음)
  TTL:       64           63            62                    64 - (라우터 수)
```

- 각 라우터는 목적지 IP로 최장 접두사 매칭을 해서 다음 홉을 정한다.
- 라우터 사이의 경로 정보는 BGP·OSPF 같은 라우팅 프로토콜이 채운다(13번).
- `traceroute`는 TTL을 1, 2, 3…으로 보내 각 홉의 Time Exceeded를 받아 경로를 그린다(09번).

### 8~10. 서버 쪽 — 역순으로 벗겨 올라간다

```text
  서버 NIC -> RX 링(DMA) -> IRQ/NAPI -> [tcpdump 탭] -> IP(netfilter: 방화벽) -> TCP(4-튜플로 소켓 찾기)
           -> (SYN이면) SYN 큐 -> accept 큐 -> 앱 accept()
           -> (데이터면) 소켓 수신 버퍼 -> 앱 recv()
```

- 서버 앞에 L4 로드밸런서가 있으면 dst IP·포트가 바뀔 수 있다(DNAT). L7 프록시면 TCP 연결 자체가 둘로 나뉜다(46번).
- 서버 커널은 4-튜플로 연결 소켓을 찾는다. 없으면 RST로 답한다(19번).
- 응답은 같은 길을 거꾸로 간다. 이때 NAT 표·방화벽 상태 표에 **왕복 기록**이 남아 있어야 돌아온다.

### 캡슐화·역캡슐화 한 장

```text
  송신 호스트                                              수신 호스트
  [데이터]                                                 [데이터]            -> 앱
  [TCP|데이터]                                             [TCP|데이터]        -> 소켓 선택(포트)
  [IP|TCP|데이터]                                          [IP|TCP|데이터]     -> 나에게 온 것? (dst IP)
  [Eth|IP|TCP|데이터|FCS]  -> 스위치(Eth만) -> 라우터(Eth 교체, IP의 TTL만) ->  [Eth|IP|TCP|데이터|FCS]
```

- 호스트는 네 층을 다 붙이고 벗긴다.
- 스위치는 이더넷만, 라우터는 이더넷을 교체하고 IP까지만 본다(NAT·방화벽은 TCP 포트까지 본다).
- *FCS(Frame Check Sequence)*: 이더넷 프레임 끝의 CRC 값이다. 홉마다 L2를 새로 쓰므로 FCS도 홉마다 새로 계산된다.

## 쓰이는 자료구조·알고리즘

이 노트의 자료구조는 모두 "구간별 조회 표"다. 패킷 하나가 여행하는 동안 표를 여러 번 조회한다.

```text
  위치          표                         키                      자료구조            노트
  송신 커널      라우팅 표(FIB)              dst IP (최장 접두사)      트라이 계열          08
  송신 커널      이웃(ARP) 캐시              다음 홉 IP               해시 + 만료 타이머    05
  스위치         MAC 표                     dst MAC                  해시(CAM)            06
  라우터/NAT     NAT·conntrack 표           5-튜플                   해시 + idle 타이머   11
  수신 커널      소켓 조회 표                4-튜플 / 리슨 포트         해시                 23
  커널 전 구간   sk_buff 큐                  -                        연결 리스트          25
```

- **최장 접두사 매칭**: 주소 비트를 앞에서부터 따라 내려가며 가장 깊이 일치한 항목을 고른다. [트라이](../../data-structure/09-trie/2-summary.md)의 비트 버전이다.
- **해시 + 만료**: ARP 캐시·NAT 표·conntrack은 "키로 찾고, 일정 시간 안 쓰면 지운다"는 같은 모양이다. 만료가 곧 장애 원인이 되기도 한다(아래 4번). 해시 개념은 [해시맵](../../data-structure/05-hashmap/2-summary.md).
- **TTL = 홉 카운터**: 루프를 끊는 안전장치다. 값 하나를 매 홉 줄이고 0에서 버린다.

## 적용 — 풀어나가는 법

### 1. "안 된다"를 구간으로 자른다 — 아래 순서로 좁힌다

```bash
# 1 이름 해석이 되나 (27번)
getent hosts example.com        # OS 해석 경로 (앱과 같은 경로)
dig +short example.com          # DNS 서버에 직접

# 2 커널이 고를 경로와 출발 주소
ip route get 203.0.113.50

# 3 다음 홉의 MAC을 아나
ip neigh show 10.0.1.1          # REACHABLE/STALE = 앎, FAILED/INCOMPLETE = ARP 실패

# 4 패킷이 내 NIC를 떠나나 / 응답이 오나
tcpdump -ni eth0 'host 203.0.113.50 and tcp port 443'

# 5 경로상 어디서 끊기나
mtr -rwzc 20 203.0.113.50       # 홉별 손실·지연 (-T로 TCP SYN 모드)
traceroute -T -p 443 203.0.113.50   # TCP SYN 탐침. tcp 방식은 비특권 허용 방식이 아니라 root 필요(traceroute(8))

# 6 서버 쪽: 연결이 소켓까지 왔나
ss -tlnp 'sport = :443'         # 리슨 중인가
ss -tn state syn-recv           # SYN은 받았는데 핸드셰이크가 안 끝났나
```

- 각 명령의 결과가 **정상인 마지막 구간**과 **처음 비정상인 구간** 사이가 범인이다.

### 2. 에러 메시지로 구간을 추정한다

```text
  앱이 본 에러                               가장 먼저 의심할 구간
  UnknownHostException / ENOTFOUND           1 이름 해석 (27)
  EAI_AGAIN (Node, 해석 일시 실패)            1 이름 해석 — SERVFAIL·해석기 무응답 (27)
  ENETUNREACH "Network is unreachable"       2 라우팅 표에 경로 없음 (08)
  EHOSTUNREACH "No route to host"            3 ARP 실패(리눅스) 또는 ICMP host unreachable 수신
  ECONNREFUSED                               10 서버에 리슨 소켓 없음 -> RST (23, 19)
  ETIMEDOUT (connect)                        5~8 SYN이 어딘가에서 버려짐(방화벽·경로) (15)
  ECONNRESET (통신 중)                        6·8 NAT/방화벽 상태 만료 뒤 RST, 또는 상대 RST (11, 19)
  TLS 핸드셰이크 실패                          1 이후 전 구간 정상, 29번 영역
```

- 매핑은 "처음 볼 곳"이지 확정이 아니다. 같은 에러가 다른 구간에서 날 수 있다.

### 3. 코드에서 구간별 타임아웃을 따로 둔다

"하나의 요청 = 여러 구간"이라서 타임아웃도 구간별로 나눠야 원인이 보인다.

```java
HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(3))     // 구간 1~10 중 "연결 수립"까지 (예시값)
        .build();
HttpRequest req = HttpRequest.newBuilder(URI.create("https://example.com/"))
        .timeout(Duration.ofSeconds(10))           // 응답까지 (예시값)
        .build();
```

```js
// Node 18+: fetch 전체에 시한. 원인 구분은 err.cause.code(ENOTFOUND, ECONNREFUSED ...)로
const res = await fetch('https://example.com/', { signal: AbortSignal.timeout(10_000) });
```

## 장애 시나리오와 대처

### 1. 게이트웨이 ARP 실패 — 로컬 LAN을 못 벗어난다

- **현상**: 같은 서브넷 호스트끼리는 되는데, 외부로 나가는 모든 연결이 실패한다.
- **보이는 형태**
  - `ip neigh show <게이트웨이>`가 `FAILED` 또는 `INCOMPLETE`다.
  - tcpdump에 `ARP, Request who-has 10.0.1.1`만 반복되고 응답이 없다.
  - 리눅스에서는 ARP 실패가 로컬 ICMP host unreachable로 바뀌어, `connect`가 `EHOSTUNREACH`(`No route to host`)로 끝난다(커널 `net/ipv4/arp.c` `arp_error_report` → `route.c` `ipv4_link_failure`).
- **원인**: 게이트웨이 장애, VLAN 설정 오류, 게이트웨이 IP 오타, VIP 페일오버 뒤 이웃 캐시가 옛 MAC을 가리킴(05번).
- **대처**
  - `ip route`로 기본 게이트웨이 주소를 확인한다.
  - `arping`·`ip neigh flush`로 캐시를 갱신한다.
  - 페일오버 구성이면 gratuitous ARP가 나가는지 확인한다(05번).

### 2. 라우팅 루프 — TTL이 바닥난다

- **현상**: 특정 대역으로만 연결이 안 된다. 다른 곳은 된다.
- **보이는 형태**
  - `traceroute`에 같은 두세 개 라우터가 번갈아 반복된다.
  - 출발지에 ICMP `Time exceeded in-transit`이 돌아온다(tcpdump `icmp`).
- **원인**: 두 라우터가 서로를 다음 홉으로 가리킨다. 패킷은 TTL이 0이 될 때까지 돈다. 라우터는 TTL 0에서 버리고 Time Exceeded를 보낸다(RFC 1812 §5.3.1).
- **대처**: 루프 구간 라우터의 경로 표를 고친다. 정적 경로 설정 실수·라우팅 프로토콜 수렴 중이 흔한 원인이다(13번).

### 3. 큰 패킷만 사라진다 — 핸드셰이크는 되는데 응답이 멈춘다

- **현상**: TCP 연결과 작은 요청은 된다. 큰 응답·큰 업로드·TLS 인증서 교환에서 멈춘다.
- **보이는 형태**
  - tcpdump에 SYN/SYN-ACK는 있다. 그 뒤 큰(MTU 크기) 세그먼트만 재전송이 반복된다.
  - `curl -v`가 TLS 핸드셰이크 중간에서 멈춘다.
- **원인**: 경로 중간에 MTU가 작은 구간(터널·VPN)이 있다. 그런데 "조각내기 필요" ICMP가 방화벽에 막혀 PMTUD가 동작하지 않는다(10번).
- **대처**: ICMP "fragmentation needed"(IPv6 "Packet Too Big")를 허용한다. 또는 터널 구간에서 MSS를 줄인다(MSS clamping)(10번).

### 4. NAT 상태 만료 뒤 첫 요청 실패

- **현상**: 한동안 쉬었던 커넥션 풀 연결로 보낸 첫 요청이 실패한다. 재시도하면 된다.
- **보이는 형태**
  - `ECONNRESET` 또는 응답 없는 타임아웃이다.
  - 서버 쪽 tcpdump에 그 요청이 안 보이거나(NAT·방화벽이 버렸거나 RST를 만들었다), NAT가 새 매핑으로 내보내 **다른 출발 포트**로 도착해 서버가 RST로 답한다(NAT 구현 의존).
- **원인**: 구간 6의 NAT(또는 방화벽)의 연결 추적 항목이 idle timeout으로 지워졌다. 양 끝 호스트는 연결이 살아 있다고 믿는다(half-open, 19번).
- **대처**
  - 풀의 idle timeout을 NAT·LB의 idle timeout보다 짧게 둔다(35번).
  - 필요하면 keepalive 간격을 NAT timeout보다 짧게 한다(21번).

### 5. 요청은 서버에 닿았는데 응답이 안 돌아온다 — 비대칭 경로

- **현상**: 서버 tcpdump에 SYN이 보이고 SYN-ACK도 나간다. 그런데 클라이언트는 SYN-ACK를 못 받는다.
- **보이는 형태**: 클라이언트는 SYN 재전송만 반복하다 `ETIMEDOUT`이다.
- **원인**
  - 응답이 다른 경로(다른 NAT·방화벽)로 나갔다. 그쪽 상태 표에는 이 연결 기록이 없어 버려진다.
  - 또는 수신 호스트의 역경로 필터(`rp_filter` 엄격 모드)가 "이 인터페이스로 들어올 주소가 아니다"라며 버렸다(kernel docs ip-sysctl).
- **대처**
  - 출발 주소 기준 라우팅(policy routing)으로 왕복 경로를 맞춘다.
  - 비대칭 라우팅 환경이면 `rp_filter`를 느슨한 모드로 둔다(kernel docs ip-sysctl — RFC 3704 loose mode).

## 핵심 문장

- IP 주소는 끝에서 끝까지 거의 그대로(NAT·LB 예외)이고, MAC 주소는 홉마다 새로 쓴다. 라우터는 TTL을 1씩 줄인다.
- 다른 네트워크로 보낼 때 ARP로 찾는 MAC은 목적지가 아니라 **다음 홉(게이트웨이)** 의 MAC이다.
- 여행 중 패킷은 라우팅 표, ARP 캐시, MAC 표, NAT·conntrack 표, 소켓 표를 차례로 조회한다. 표 하나가 틀리거나 만료되면 그 구간에서 끊긴다.
- 응답은 같은 상태 표(NAT·방화벽)를 거꾸로 지나야 돌아온다. 왕복 경로와 상태가 맞아야 연결이 된다.
- 장애는 "정상인 마지막 구간"과 "비정상인 첫 구간" 사이를 명령 하나씩으로 좁혀 찾는다.

## 관련 주제·근거

이 노트는 종합편이다. 구간별 원리는 아래 노트가 맡는다.

- 선행
  - [25-kernel-network-stack](../25-kernel-network-stack/2-summary.md) — 호스트 안 경로(구간 4·9)
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — 라우팅 표·기본 게이트웨이·TTL.
  - [05-arp](../05-arp/2-summary.md) — IP→MAC 해석, gratuitous ARP.
- 구간별 노트
  - [01-layer-map-osi-tcpip](../01-layer-map-osi-tcpip/2-summary.md)·[02-encapsulation](../02-encapsulation/2-summary.md) — 계층과 캡슐화.
  - [06-switching-and-vlan](../06-switching-and-vlan/2-summary.md) — MAC 표·플러딩·VLAN.
  - [09-icmp-ping-traceroute](../09-icmp-ping-traceroute/2-summary.md) · [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md) · [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) · [13-routing-protocols-ospf-bgp](../13-routing-protocols-ospf-bgp/2-summary.md)
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md)
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — RST·half-open
  - [23-socket-api](../23-socket-api/2-summary.md) — 구간 1·10의 시스템콜
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) — 구간 1의 이름 해석
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) — 연결 뒤 암호 채널
  - `46-load-balancers-and-proxies` — 원고: [systems/server-design/02-request-path](../../systems/server-design/02-request-path.md)
  - [49-what-happens-when-url](../49-what-happens-when-url/2-summary.md) · [50-network-diagnostics](../50-network-diagnostics/2-summary.md)
- RFC
  - RFC 1812 §5.3.1 — 라우터의 TTL 감소(MUST)·Time Exceeded <https://www.rfc-editor.org/rfc/rfc1812>
  - RFC 1624 — 인터넷 체크섬 증분 갱신 <https://www.rfc-editor.org/rfc/rfc1624>
  - RFC 5737 — 문서용 IPv4 주소 대역(192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) <https://www.rfc-editor.org/rfc/rfc5737>
- Linux
  - ip-sysctl — `ip_default_ttl`(기본 64), `rp_filter` <https://docs.kernel.org/networking/ip-sysctl.html>
  - connect(2) — `ENETUNREACH`, `ETIMEDOUT`, `ECONNREFUSED` <https://man7.org/linux/man-pages/man2/connect.2.html>
  - 커널 소스 — ARP 실패 → 로컬 ICMP host unreachable(`net/ipv4/arp.c` `arp_error_report`, `net/ipv4/route.c` `ipv4_send_dest_unreach`), SYN_SENT에서 ICMP 오류로 연결 종료(`net/ipv4/tcp_ipv4.c` `tcp_v4_err`) <https://github.com/torvalds/linux/tree/master/net/ipv4>
  - traceroute(8) — `-T` tcp 방식 <https://man7.org/linux/man-pages/man8/traceroute.8.html>
- Kurose & Ross, 『Computer Networking: A Top-Down Approach』 6.7 "Retrospective: A Day in the Life of a Web Page Request"(7판 목차로 확인, 8판 번호 [?]) · 6.4 스위치 자가 학습
- alex/what-happens-when — URL 입력부터 렌더링까지 <https://github.com/alex/what-happens-when>
- 『성공과 실패를 결정하는 1%의 네트워크 원리』(Tsutomu Tone) — 커리큘럼 지정 교재 [?]
