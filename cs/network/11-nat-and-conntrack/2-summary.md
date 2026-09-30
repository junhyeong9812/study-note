# network/11-nat-and-conntrack — 사설 주소가 인터넷에 나가는 법, 그리고 그 "기억"이 사라질 때 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

사설 주소는 인터넷에서 길을 찾을 수 없다.\
`10.0.0.5` 같은 주소는 수많은 회사·집에서 동시에 쓴다.\
그래서 인터넷의 라우터는 이 주소로 응답을 돌려보낼 수 없다.

  - *사설 주소(private address)*: 조직 내부에서만 쓰라고 떼어 둔 IPv4 대역이다. `10/8`, `172.16/12`, `192.168/16` 세 개다(RFC 1918 §3).

```text
  사설망                      경계 장비(NAT)                인터넷
  10.0.0.5:40000  --->  [ 출발지를 203.0.113.7:61001로 바꿈 ]  --->  93.184.216.34:443
                  <---  [ 목적지를 10.0.0.5:40000으로 되돌림 ] <---
                         ^ 이 짝을 "기억"하는 표가 있어야 되돌릴 수 있다
```

NAT가 두 가지 문제를 푼다.
- 공인 주소 하나를 여러 내부 호스트가 나눠 쓴다.
- 들어오는 응답을 원래 내부 호스트에게 돌려준다.

되돌리려면 "누가 누구에게 보냈는지"를 기억해야 한다.\
이 기억이 **연결 추적(connection tracking, conntrack)** 이다.

쉬운 예: 회사 대표번호와 교환원이다.\
직원이 밖으로 전화하면 상대 화면에는 대표번호가 뜬다.\
상대가 대표번호로 되걸면 교환원이 "방금 누가 걸었지?" 메모를 보고 연결해 준다.\
메모를 오래 안 쓰면 교환원이 지운다. 그 뒤에 온 전화는 누구에게 줄지 모른다.

똑같은 구조다.\
NAT 장비의 메모가 conntrack 표이고, 메모를 지우는 시간이 **idle timeout**이다.

실무 예:
- 사설 서브넷의 서버가 NAT 게이트웨이를 거쳐 외부 API를 부른다.
- 도커 컨테이너가 호스트 주소로 가장(masquerade)해 인터넷에 나간다(Docker 문서 "Packet filtering and firewalls").
- 로드밸런서·쿠버네티스 서비스처럼 목적지 주소를 바꿔 뒤쪽 서버로 넘긴다(DNAT).

## 동작·원리

### SNAT와 DNAT — 무엇을 바꾸나

```text
  SNAT (출발지 변환)  — 안에서 밖으로 나갈 때
    원래:  src=10.0.0.5:40000        dst=93.184.216.34:443
    변환:  src=203.0.113.7:61001     dst=93.184.216.34:443

  DNAT (목적지 변환)  — 밖에서 안으로 들어올 때
    원래:  src=198.51.100.9:52000    dst=203.0.113.7:80
    변환:  src=198.51.100.9:52000    dst=10.0.0.20:8080
```

  - *SNAT(Source NAT)*: 나가는 패킷의 출발지 주소(와 포트)를 바꾼다. 리눅스 iptables에서는 nat 테이블의 POSTROUTING 체인(과 INPUT 체인)에서 쓴다(iptables-extensions(8)).
  - *DNAT(Destination NAT)*: 들어오는 패킷의 목적지 주소(와 포트)를 바꾼다. nat 테이블의 PREROUTING·OUTPUT 체인에서 쓴다(iptables-extensions(8)).
  - *MASQUERADE*: SNAT의 한 형태다. 바꿀 출발지로 나가는 인터페이스의 현재 주소를 자동으로 쓴다. 주소가 자주 바뀌는 회선에 쓴다.

RFC 3022는 두 종류를 나눈다.
- **Basic NAT**: 주소만 1:1로 바꾼다.
- **NAPT**: 주소와 **포트**를 함께 바꿔, 여러 내부 주소가 공인 주소 하나를 나눠 쓴다(§2.2).

오늘날 "NAT"라고 하면 대부분 NAPT다.

  - *NAPT(Network Address Port Translation)*: 포트 번호까지 바꿔서 (내부 주소, 내부 포트) 여러 개를 (공인 주소, 공인 포트) 여러 개로 대응시키는 방식이다.

### 변환표 — 한 연결에 두 방향

```text
  conntrack 항목 하나 (개념도)
  +------------------------------------------------------------------+
  | original: 10.0.0.5:40000   -> 93.184.216.34:443   (보낸 방향)      |
  | reply   : 93.184.216.34:443 -> 203.0.113.7:61001  (돌아올 방향)    |
  | 상태: ESTABLISHED    남은 시간(timeout): 431999초                  |
  +------------------------------------------------------------------+
       ^                                   ^
       |                                   +-- 응답은 이 튜플로 찾는다
       +-- 나가는 패킷은 이 튜플로 찾는다
```

- 리눅스 커널은 연결 하나(`struct nf_conn`)에 튜플을 두 개 둔다. 주석이 "original and reply"다(include/net/netfilter/nf_conntrack.h `tuplehash[IP_CT_DIR_MAX]`).
- 응답 패킷이 오면 reply 튜플로 항목을 찾는다. 그리고 목적지를 original의 출발지로 되돌린다.
- 같은 항목에 만료 시각(`timeout`)이 들어 있다. 패킷이 지나갈 때마다 늘어난다.

  - *튜플(tuple)*: 연결을 구분하는 값 묶음이다. 보통 (프로토콜, 출발 IP, 출발 포트, 도착 IP, 도착 포트)다.

### conntrack이 붙이는 상태

conntrack은 NAT만을 위한 것이 아니다.\
상태 기반 방화벽도 같은 표를 본다.

```text
  --ctstate    의미 (iptables-extensions(8))
  NEW          새 연결을 시작했거나, 아직 양방향 패킷을 못 본 연결
  ESTABLISHED  양방향 모두 패킷을 본 연결
  RELATED      새 연결이지만 기존 연결과 관련 있음 (FTP 데이터, ICMP 에러)
  INVALID      알려진 어떤 연결에도 속하지 않음
  UNTRACKED    raw 테이블에서 추적을 끈 패킷 (-j CT --notrack)
```

- 방화벽 규칙 "ESTABLISHED,RELATED 허용"은 이 상태를 본다.
- 그래서 conntrack 항목이 사라지면, 방화벽도 그 연결을 모르는 것이 된다.

### 포트 매핑 — 몇 개까지 동시에 되나

```text
  공인 IP 203.0.113.7 하나

  내부 10.0.0.5:40000 -> 93.184.216.34:443   =>  공인 포트 61001
  내부 10.0.0.6:40000 -> 93.184.216.34:443   =>  공인 포트 61002
  내부 10.0.0.5:40001 -> 93.184.216.34:443   =>  공인 포트 61003
  ...
  내부 10.0.0.9:40000 -> 198.51.100.1:443    =>  공인 포트 61004  (내부 끝점마다 자기 공인 포트)
```

- 위 그림은 RFC가 요구하는 Endpoint-Independent Mapping(EIM, 아래 "매핑 동작") NAT의 모습이다.
  - 공인 포트 하나는 목적지와 상관없이 내부 끝점(IP:포트) 하나에만 묶인다.
  - 그래서 동시 매핑 수가 목적지와 무관하게 공인 포트 수에 막힌다.
- 실제로는 목적지별로 공인 포트를 재사용하는 NAT가 흔하다(리눅스 SNAT·MASQUERADE, AWS NAT 게이트웨이).
  - 이런 NAT는 응답을 (공인 IP, 공인 포트, 목적지 IP, 목적지 포트, 프로토콜)로 구분한다.
  - 목적지가 다르면 다른 내부 호스트에게 같은 공인 포트(예: 61001)를 줄 수 있다. EIM은 아니다.
  - 그래서 **같은 목적지**로 가는 동시 연결 수가 공인 포트 수에 막힌다.
- AWS NAT 게이트웨이는 IPv4 주소 하나당 "고유 목적지(목적지 IP·포트·프로토콜 조합)마다 최대 55,000개" 동시 연결을 지원한다고 적는다(AWS "NAT gateway basics").

  - *포트 고갈(port exhaustion)*: 같은 목적지로 가는 연결이 너무 많아 비어 있는 공인 포트가 없는 상태다. 새 연결의 SYN이 나가지 못한다.

### 매핑 동작 — RFC가 요구하는 것

RFC 4787(UDP)과 RFC 5382(TCP)는 NAT의 동작을 분류한다.

```text
  매핑 종류 (RFC 4787 §4.1)            같은 내부 X:x가 다른 목적지로 보내면
  Endpoint-Independent Mapping         같은 공인 포트를 재사용
  Address-Dependent Mapping            목적지 IP가 같을 때만 재사용
  Address and Port-Dependent Mapping   목적지 IP·포트가 같을 때만 재사용
```

- NAT는 Endpoint-Independent Mapping을 해야 한다. UDP는 RFC 4787 REQ-1, TCP는 RFC 5382 REQ-1이다(둘 다 MUST).
- 규범과 구현은 다르다. 리눅스 NAT는 새 연결의 응답 튜플이 기존 항목과 겹치는지만 검사해 포트를 고른다(`net/netfilter/nf_nat_core.c` `nf_nat_used_tuple()`). 그래서 EIM을 보장하지 않는다.
- 이유: STUN 같은 NAT 통과 기법은 "내 공인 주소·포트"를 알아내 상대에게 알려 준다. 목적지마다 매핑이 바뀌면 그 값이 쓸모없어지고 릴레이(TURN)를 써야 한다(RFC 4787 REQ-1 Justification, HPBN "Building Blocks of UDP").

### idle timeout — 기억은 언제 지워지나

```text
  시간 -->
  |--패킷--|--패킷--|..................(조용)..................|--패킷-->
                    ^                                         ^
                    마지막 패킷                                 NAT: "이 매핑 모름"
                    |<------------- idle timeout ------------->|
                                                               -> 드롭 또는 RST
```

표준이 정한 **최솟값**과 실제 장비 값은 다르다.

| 대상 | 값 | 근거 |
|---|---|---|
| RFC: TCP established | NAT가 idle 세션을 버린다면 2시간 4분 **이상**이어야 한다(MUST NOT be less) | RFC 5382 REQ-5 |
| RFC: TCP 연결 수립·종료 중(transitory) | 4분 이상 | RFC 5382 REQ-5 |
| RFC: UDP 매핑 | 2분 이상(MUST), 5분 이상 권장(RECOMMENDED). 목적지가 잘 알려진 포트(0~1023)면 더 짧아도 된다(MAY, REQ-5a) | RFC 4787 REQ-5 |
| 리눅스 conntrack TCP established | 432000초(5일) | kernel docs nf_conntrack-sysctl |
| 리눅스 conntrack UDP | 30초, 스트림으로 보이면 120초 | kernel docs nf_conntrack-sysctl |
| AWS NAT 게이트웨이 | 350초 idle이면 타임아웃 | AWS NAT 게이트웨이 트러블슈팅 |

- AWS NAT 게이트웨이의 350초는 RFC 5382의 최솟값(2시간 4분)보다 훨씬 짧다.
- 그래서 "RFC대로면 괜찮다"고 가정하면 안 된다. 경로에 있는 장비의 실제 값을 확인한다.
- AWS는 타임아웃된 연결을 계속 쓰려는 내부 쪽에 **RST**를 돌려준다. FIN은 보내지 않는다(AWS 트러블슈팅 "Internet connection drops after 350 seconds").
- 장비마다 다르다. 어떤 장비는 RST 없이 조용히 버린다[?]. 이 경우는 19번 노트의 half-open과 같은 모양이 된다.

### conntrack 표가 가득 차면

```text
  새 연결의 첫 패킷
        |
        v
  nf_conntrack_count < nf_conntrack_max ? ---예---> 새 항목 만들고 통과
        |
       아니오
        v
  근처 버킷의 ASSURED 아닌 항목 버리기(early drop) 시도 ---성공---> 새 항목
        |
       실패
        v
  패킷 드롭 + 커널 로그 "nf_conntrack: table full, dropping packet"
```

- early drop은 "가장 오래된" 항목을 찾지 않는다. 새 항목의 해시 버킷부터 최대 8개 버킷(`NF_CT_EVICTION_RANGE`)만 훑는다. 그 안에서 ASSURED 표시가 없는 항목을 지운다(net/netfilter/nf_conntrack_core.c `early_drop()`·`early_drop_list()`).
  - *ASSURED*: conntrack이 "정상적으로 오간 연결"로 표시한 항목이다. 예: TCP는 SYN_RECV 뒤 ESTABLISHED로 넘어가 연결 수립이 끝난 항목이다(nf_conntrack_proto_tcp.c). `conntrack -L`의 `[ASSURED]`다.
- 이 로그 문구는 커널 `__nf_conntrack_alloc()`에 그대로 있다(net/netfilter/nf_conntrack_core.c, `net_warn_ratelimited`). 초기 netns가 아닌 곳(컨테이너 등)에서는 `nf_conntrack: table full in netns <번호>, dropping packet`으로 찍힌다.
- 드롭은 **새 연결**의 첫 패킷에서 일어난다. 이미 있는 연결은 계속 된다.
- 그래서 증상이 "일부 새 요청만 타임아웃"으로 보인다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블** — conntrack 표 자체다.
  - 키는 튜플이다. 항목 하나가 original·reply 두 튜플로 두 번 걸린다. 어느 방향 패킷이 와도 O(1)에 찾는다.
  - 버킷 수(`nf_conntrack_buckets`)의 기본값은 메모리 크기에서 계산한다. 최대 항목 수(`nf_conntrack_max`)의 기본값은 버킷 수와 같다(kernel docs nf_conntrack-sysctl).
  - 64비트에서 메모리가 4GB를 넘으면 버킷 기본값을 262144로 고정한다(nf_conntrack_core.c `nf_conntrack_init_start`).
  - `max`만 크게 올리고 버킷을 그대로 두면 체인이 길어진다. 개념은 [해시맵](../../data-structure/05-hashmap/2-summary.md)의 로드 팩터와 같다.
- **타이머** — 항목마다 만료 시각이 있고, 패킷이 오면 갱신된다. 전형적인 "idle timeout" 패턴이다.
- **상태 기계** — TCP 항목은 SYN_SENT → ESTABLISHED → FIN_WAIT → TIME_WAIT 같은 conntrack 자체 상태를 따라가고, 상태마다 timeout이 다르다(nf_conntrack-sysctl의 `nf_conntrack_tcp_timeout_*`).
- **증분 체크섬 갱신** — 주소·포트를 바꾸면 IP·TCP·UDP 체크섬도 바뀐다. 전부 다시 계산하지 않고 "바뀐 값의 차이만 더한다"(RFC 3022 §4.2).

## 적용 — 풀어나가는 법

### 1. 경로에 NAT·상태 방화벽이 있는지부터 안다

- 클라우드 사설 서브넷 → NAT 게이트웨이 → 인터넷.
- 쿠버네티스 노드 → 노드의 iptables/conntrack → 서비스 백엔드.
- 사내망 → 방화벽 → 외부.

경로의 각 장비가 **idle timeout**을 갖는다.\
가장 짧은 값이 그 연결의 수명을 정한다.

### 2. 오래 쉬는 연결은 timeout보다 자주 "말을 건다"

Java — 커넥션 풀의 idle 연결을 NAT timeout보다 먼저 버리거나 keepalive를 켠다.

```java
Socket s = new Socket();
s.setKeepAlive(true);                                         // SO_KEEPALIVE
// JDK 11+ (리눅스·macOS): keepalive 간격을 소켓별로 조정
s.setOption(jdk.net.ExtendedSocketOptions.TCP_KEEPIDLE, 300);     // 300초(예시) 쉬면 probe
s.setOption(jdk.net.ExtendedSocketOptions.TCP_KEEPINTERVAL, 30);  // probe 간격(예시)
s.setOption(jdk.net.ExtendedSocketOptions.TCP_KEEPCOUNT, 3);      // 실패 허용 횟수(예시)
s.connect(new InetSocketAddress(host, 443), 3_000);
```

Node.js — 소켓 keepalive의 첫 probe 시점을 지정한다.

```js
const sock = net.connect({ host, port: 443 });
sock.setKeepAlive(true, 300_000);   // 300초(예시) idle 뒤 keepalive probe 시작
```

- AWS는 350초 문제에 "keepalive를 350초보다 짧게"를 권한다(AWS 트러블슈팅).
- 리눅스 keepalive 기본 idle은 7200초라 그대로는 쓸모가 없다(tcp(7)). 세부는 21번 노트.
- 더 단순한 방법: 풀의 idle 연결 최대 수명을 경로의 가장 짧은 idle timeout보다 짧게 둔다(35번 노트).

### 3. 진단 명령

```bash
# conntrack 사용량 — count가 max에 닿는지
sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max

# 표 내용 보기 / 특정 목적지 포트만 / 개수
conntrack -L -p tcp --dport 443
conntrack -C

# CPU별 통계 — drop·early_drop·insert_failed가 오르는지
conntrack -S

# 실시간 이벤트 (새로 생기고 사라지는 항목)
conntrack -E

# 커널 로그에서 표 가득 참 찾기
dmesg | grep 'nf_conntrack: table full'

# 상태별 timeout 값
sysctl -a 2>/dev/null | grep nf_conntrack_tcp_timeout
```

`conntrack -L` 한 줄의 모양(값은 예시):

```text
tcp  6 431999 ESTABLISHED src=10.0.0.5 dst=93.184.216.34 sport=40000 dport=443 \
     src=93.184.216.34 dst=203.0.113.7 sport=443 dport=61001 [ASSURED] mark=0 use=1
      ^ 남은 초            ^ original 튜플                          ^ reply 튜플 (NAT 후 주소가 보인다)
```

- reply 튜플의 목적지가 original의 출발지와 다르면 SNAT가 걸린 것이다.
- 클라우드 NAT 게이트웨이는 호스트에서 conntrack을 볼 수 없다. 대신 지표를 본다.
  - AWS: `ErrorPortAllocation`(출발지 포트 할당 실패), `IdleTimeoutCount`(350초 idle로 넘어간 연결 수)(AWS "NAT gateway metrics and dimensions").

## 장애 시나리오와 대처

### 1. 한동안 쉰 연결의 첫 요청이 `Connection reset` — NAT idle timeout

- **현상**: 새벽처럼 한가한 시간 뒤 첫 요청만 실패한다. 재시도하면 된다.
- **보이는 형태**
  - Java `SocketException: Connection reset`, Node `Error: read ECONNRESET`.
  - tcpdump에 요청 직후 RST가 돌아온다.
  - AWS `IdleTimeoutCount`가 오른다.
- **원인**: 커넥션 풀의 연결이 350초(AWS NAT GW) 넘게 놀았다. NAT가 매핑을 지웠다. 이쪽은 모르고 옛 연결에 썼고, NAT가 RST를 돌려줬다.
- **대처**
  - TCP keepalive를 NAT timeout보다 짧게 켠다.
  - 또는 풀의 idle 연결 수명을 NAT timeout보다 짧게 둔다.
  - 멱등 요청은 한 번 재시도한다.

### 2. RST도 없이 멈춘다 — 조용히 버리는 장비

- **현상**: 쉬었던 연결에 요청을 보냈는데 응답도 에러도 없다. 한참 뒤 타임아웃이다.
- **보이는 형태**: `ss -ti`에 Send-Q가 쌓이고 `retrans`가 오른다. 반대편 서버 로그에는 요청이 없다.
- **원인**: 중간 방화벽·NAT가 매핑을 지운 뒤, 모르는 패킷을 RST 없이 드롭한다. 이쪽 커널은 재전송만 반복한다(half-open, 19번).
- **대처**
  - 요청 단위 타임아웃을 반드시 둔다.
  - keepalive·heartbeat로 매핑을 살려 둔다.
  - 필요하면 `TCP_USER_TIMEOUT`으로 재전송 포기 시간을 줄인다(21번).

### 3. `nf_conntrack: table full, dropping packet`

- **현상**: 트래픽이 몰릴 때 일부 새 연결만 타임아웃이 난다. 이미 열린 연결은 멀쩡하다.
- **보이는 형태**
  - 커널 로그(dmesg, journal)에 `nf_conntrack: table full, dropping packet`.
  - `nf_conntrack_count`가 `nf_conntrack_max`에 붙어 있다.
  - `conntrack -S`의 `drop`이 오른다.
  - 클라이언트는 SYN 재전송 뒤 connect 타임아웃을 본다.
- **원인**
  - 짧은 연결이 폭증했거나, 항목이 오래 남는다.
  - TCP established 기본 5일, TIME_WAIT 120초 동안 항목이 남는다(nf_conntrack-sysctl).
  - UDP(특히 DNS)는 요청마다 새 항목이 생긴다.
- **대처**
  - `nf_conntrack_max`를 올린다. 버킷 수(`nf_conntrack_buckets`)도 함께 올려 체인 길이를 유지한다.
  - 필요 없는 상태 타임아웃을 줄인다(예: `nf_conntrack_tcp_timeout_established`).
  - 추적할 필요 없는 트래픽은 raw 테이블에서 `-j CT --notrack`으로 뺀다. 단, 그 트래픽에는 NAT·상태 규칙이 적용되지 않는다.
  - 연결을 재사용한다(keep-alive·풀).

### 4. SNAT 포트 고갈 — 같은 목적지로 새 연결이 안 열린다

- **현상**: 특정 외부 API 하나로만 새 연결이 실패한다. 다른 목적지는 된다.
- **보이는 형태**
  - AWS `ErrorPortAllocation` > 0.
  - 클라이언트는 connect 타임아웃·실패를 본다.
- **원인**
  - 공인 IP 하나로 한 목적지에 열 수 있는 동시 연결에는 상한이 있다(AWS: IP당 목적지별 55,000).
  - 요청마다 새 연결을 열고 닫는 코드가 흔한 원인이다. 닫힌 연결도 TIME_WAIT 동안 매핑을 잡는다[?].
- **대처**
  - 커넥션 풀·keep-alive로 연결을 재사용한다.
  - NAT에 공인 IP를 더 붙인다(AWS: 기본 1개 + 보조 7개 = 최대 8개. 공인 NAT의 탄력적 IP는 기본 2개까지라 쿼터 상향이 필요하다).
  - 트래픽을 여러 NAT 게이트웨이로 나눈다.

### 5. 응답만 막힌다 — 비대칭 경로와 상태 방화벽

- **현상**: SYN은 나가는데 SYN-ACK가 돌아오지 않는다. 또는 돌아와도 버려진다.
- **보이는 형태**: 한쪽 tcpdump에는 SYN-ACK가 보이는데, 상태 방화벽을 지난 뒤에는 없다. 방화벽 로그에 INVALID 드롭이 찍힌다.
- **원인**: 가는 길과 오는 길이 다른 장비를 탔다. 응답 경로의 장비는 NEW 패킷(SYN)을 본 적이 없다. 그래서 conntrack 항목이 없고 INVALID로 버린다.
- **대처**
  - 라우팅을 대칭으로 맞춘다(8번 노트).
  - NAT를 쓰는 경로라면 반드시 같은 NAT를 되돌아오게 한다.

## 핵심 문장

- NAT는 주소(와 포트)를 바꾸고, 되돌리기 위해 연결마다 원래 짝을 **conntrack 표**에 기억한다.
- conntrack 항목은 original·reply 두 튜플로 해시 테이블에 걸리고, 패킷이 올 때마다 만료 시각이 늘어난다.
- idle timeout이 지나면 기억이 사라진다. 그 뒤에 오는 패킷은 RST를 받거나 조용히 버려진다. RFC 최솟값이 아니라 **경로 장비의 실제 값**(예: AWS NAT GW 350초)이 연결 수명을 정한다.
- 오래 쉬는 연결은 가장 짧은 idle timeout보다 자주 말을 걸거나, 그 전에 스스로 버린다.
- conntrack 표가 차면 **새 연결만** 드롭되고 커널이 `table full, dropping packet`을 남긴다.

## 관련 주제·근거

- 선행: [07-ip-addressing-cidr](../07-ip-addressing-cidr/2-summary.md) — 사설 대역·CIDR
- 후속·연결
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — NAT가 매핑을 지운 뒤의 RST·half-open
  - [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md) — keepalive를 NAT timeout보다 짧게
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 풀 idle timeout 정렬
  - [14-udp](../14-udp/2-summary.md) — UDP는 연결 끝을 알 수 없어 NAT가 타이머로만 지운다
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — 비대칭 라우팅
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) — conntrack 표 = 튜플 키 해시 테이블
- RFC
  - RFC 1918 §3 사설 주소 대역 <https://www.rfc-editor.org/rfc/rfc1918>
  - RFC 3022 Traditional NAT — §2.2 NAPT, §4.2 체크섬 조정 <https://www.rfc-editor.org/rfc/rfc3022>
  - RFC 4787 NAT Behavioral Requirements for Unicast UDP — §4.1 매핑 분류, REQ-1 Endpoint-Independent Mapping, REQ-3 port overloading 금지, REQ-5 UDP 매핑 2분 이상·5분 권장·잘 알려진 포트 예외(5a) <https://www.rfc-editor.org/rfc/rfc4787>
  - RFC 5382 NAT Behavioral Requirements for TCP — REQ-1 Endpoint-Independent Mapping, REQ-5 established 2시간 4분·transitory 4분 <https://www.rfc-editor.org/rfc/rfc5382>
  - RFC 8085 §3.5 미들박스 통과 — UDP keepalive는 15초보다 자주 보내지 않는다(SHOULD NOT) <https://www.rfc-editor.org/rfc/rfc8085>
- Linux
  - Kernel docs "Netfilter Conntrack Sysfs variables" — `nf_conntrack_max`·`buckets`·`tcp_timeout_established`(432000)·`udp_timeout`(30) <https://docs.kernel.org/networking/nf_conntrack-sysctl.html>
  - net/netfilter/nf_conntrack_core.c — `table full, dropping packet`, `early_drop()`(최대 8버킷·ASSURED 아닌 항목), 버킷 기본값 계산 <https://github.com/torvalds/linux/blob/master/net/netfilter/nf_conntrack_core.c>
  - include/net/netfilter/nf_conntrack.h — `struct nf_conn`의 `tuplehash[IP_CT_DIR_MAX]`
  - net/netfilter/nf_nat_core.c — `nf_nat_used_tuple()`: 응답 튜플 충돌만 검사해 NAT 포트 선택 <https://github.com/torvalds/linux/blob/master/net/netfilter/nf_nat_core.c>
  - iptables-extensions(8) — conntrack `--ctstate`, SNAT·DNAT·MASQUERADE, CT `--notrack` <https://man7.org/linux/man-pages/man8/iptables-extensions.8.html>
  - conntrack(8) — `-L`·`-C`·`-S`·`-E`·`-D` <https://manpages.debian.org/testing/conntrack/conntrack.8.en.html>
- AWS VPC 사용 설명서
  - "NAT gateway basics" — IP당 목적지별 55,000 동시 연결, IP 최대 8개(1 + 보조 7), 탄력적 IP 기본 2개 <https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html>
  - "Troubleshoot NAT gateways" — 350초 idle timeout, 타임아웃 뒤 RST <https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html>
  - "NAT gateway metrics and dimensions" — `ErrorPortAllocation`, `IdleTimeoutCount` <https://docs.aws.amazon.com/vpc/latest/userguide/metrics-dimensions-nat-gateway.html>
- Grigorik, HPBN "Building Blocks of UDP" — UDP와 NAT, STUN·TURN·ICE <https://hpbn.co/building-blocks-of-udp/>
