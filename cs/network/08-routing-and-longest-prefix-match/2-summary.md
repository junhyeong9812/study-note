# network/08-routing-and-longest-prefix-match — 패킷은 다음에 어디로 가야 하는지 어떻게 정하나 — 정리 (힌트)

## 해결하는 문제

패킷 하나가 목적지 주소를 들고 라우터에 도착했다.\
라우터는 나가는 길(인터페이스)을 여러 개 갖고 있다.\
이 패킷을 **어느 길로, 누구에게** 넘겨야 하나?

라우터는 전체 경로를 모른다.\
"다음 한 걸음"만 정한다. 그다음 라우터가 또 한 걸음을 정한다.

```text
  출발 --> [R1] --> [R2] --> [R3] --> 목적지
           "R2로"   "R3로"   "직접 전달"     각자 자기 표만 보고 다음 홉만 정한다
```

쉬운 예: 고속도로 표지판이다.\
"부산 방면"이라는 큰 표지판과 "해운대 IC"라는 작은 표지판이 둘 다 보이면, 해운대로 가는 차는 **더 구체적인** 해운대 표지판을 따른다.\
어떤 표지판에도 없으면 "기타 방면"으로 간다.

똑같은 구조다.
- 표지판 = 라우팅 테이블의 한 줄(프리픽스)
- 더 구체적인 표지판 우선 = **최장 접두사 매칭(longest prefix match)**
- "기타 방면" = **기본 경로(default route, `0.0.0.0/0`)**

실무에서 이 지식이 필요한 순간
- VPN을 켰더니 사내 일부 대역이나 인터넷이 안 된다.
- 도커·쿠버네티스가 만든 경로가 사내 대역을 가로챈다(07번 장애 2).
- 클라우드 라우팅 테이블에 경로를 추가했는데 트래픽이 엉뚱한 곳으로 간다.
- `Time to live exceeded`, `Network is unreachable`, `No route to host`를 해석한다.

## 동작·원리

### 라우팅 테이블 한 줄

```text
  $ ip route          (리눅스 호스트 예시 출력)
  default via 10.0.1.1 dev eth0 metric 100
  10.0.1.0/24 dev eth0 proto kernel scope link src 10.0.1.23
  10.8.0.0/16 via 10.0.1.254 dev eth0
  172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1

  한 줄 = ( 목적지 프리픽스 | 다음 홉(via) | 나갈 인터페이스(dev) | 비용(metric) )
```

  - *다음 홉(next hop)*: 패킷을 넘겨줄 바로 옆 라우터의 주소다. 직접 연결된 망이면 다음 홉 없이 목적지로 바로 보낸다.
  - *기본 게이트웨이*: 기본 경로의 다음 홉이다. 위 예에서 `10.0.1.1`이다.
  - `proto kernel scope link` 줄은 인터페이스에 주소를 붙일 때 커널이 자동으로 만든 "직접 연결된 서브넷" 경로다.

### 호스트의 첫 결정 — 직접 보낼까, 게이트웨이에게 줄까

```text
  목적지 D, 내 주소 S, 내 마스크 M

  (D AND M) == (S AND M) ?
      예  -> 같은 망: ARP로 D의 MAC을 찾아 직접 보낸다
      아니오 -> 다른 망: 게이트웨이의 MAC을 찾아 게이트웨이에게 보낸다
```

- RFC 1122 §3.3.1.1은 호스트가 이 방식으로 판단해야 한다고 정한다(MUST).
- 리눅스는 이것을 따로 하지 않는다. 직접 연결된 서브넷도 라우팅 테이블의 한 줄이므로, 아래의 최장 접두사 매칭 한 번으로 둘 다 처리된다.

### 최장 접두사 매칭 — 가장 구체적인 줄이 이긴다

RFC 1812 §5.2.4.3의 예를 그대로 옮긴다.

```text
  목적지: 10.144.2.5

  테이블            앞 n비트가 목적지와 같나?   길이
  10.0.0.0/8        예                        8
  10.144.0.0/16     예                        16
  10.144.2.0/24     예                        24   <- 가장 길다 = 선택
  128.12.0.0/16     아니오 (탈락)
  0.0.0.0/0         예 (길이 0은 모든 주소와 맞는다)  0
```

1. **Basic Match**: 목적지와 앞 n비트가 같은 줄만 남긴다.
2. **Longest Match**: 남은 줄 중 프리픽스가 가장 긴 것을 고른다.

- 기본 경로 `0.0.0.0/0`은 길이가 0이라 모든 목적지와 맞는다. 하지만 더 긴 줄이 하나라도 맞으면 진다. 그래서 "최후의 수단"이다.
- 길이가 같은 줄이 여럿이면 다른 기준으로 고른다.
  - RFC 1812는 관리 우선순위·메트릭 등으로 정한다(§5.2.4.3 이후 규칙, §5.2.4.4).
  - 리눅스는 `metric`(= `preference`)이 **작은** 쪽을 고른다(ip-route(8)).
- 클라우드도 같은 규칙이다. AWS 라우팅 테이블은 가장 구체적인 경로(최장 접두사 매칭)로 보낸다. 예로 `10.10.2.15/32`가 `10.10.2.0/24`보다 우선한다(AWS "How route priority works").

### 홉마다 반복된다 — 바뀌는 것과 안 바뀌는 것

```text
  호스트 A ----> R1 ----> R2 ----> 호스트 B

  IP 헤더   출발지 A, 목적지 B, TTL 64 -> 63 -> 62   (주소는 끝까지 그대로, NAT 없을 때)
  이더넷    A->R1   R1->R2   R2->B                  (홉마다 새로 씌운다)
```

- 목적지 IP는 끝까지 같다. 매 홉마다 바뀌는 것은 **이더넷 헤더(MAC)**와 **TTL**이다.
- 각 라우터는 목적지 IP로 최장 접두사 매칭을 하고, 다음 홉의 MAC을 ARP로 찾아 새 프레임에 담는다.

### TTL — 루프가 영원히 돌지 않게

```text
  R1: 10.9.0.0/16 -> R2          R2: 10.9.0.0/16 -> R1       (잘못된 정적 경로, 예시)

  패킷(TTL 64)  R1 -> R2 -> R1 -> R2 -> ... 매 홉 TTL-1
  TTL 0 도달 --> 그 라우터가 패킷을 버리고 출발지에 ICMP Time Exceeded(code 0) 전송
```

- 라우터는 전달할 때마다 TTL을 **최소 1** 줄여야 한다(MUST, RFC 1812 §5.3.1).
- TTL이 0이 되면 패킷을 버린다. 목적지가 멀티캐스트가 아니면 출발지에 ICMP Time Exceeded, Code 0을 보내야 한다(MUST, 같은 절).
- RFC 1812는 이 ICMP가 traceroute 때문에라도 필요하다고 적는다. traceroute는 이 성질을 거꾸로 이용한다(09번).
- 리눅스가 보내는 패킷의 기본 TTL은 64다(`net.ipv4.ip_default_ttl`, kernel ip-sysctl 문서).
  - *TTL(Time To Live)*: IPv4 헤더의 8비트 필드다. 이름은 "시간"이지만 실제로는 홉 수 제한으로 쓰인다(RFC 1812 §5.3.1). IPv6에서는 이름이 Hop Limit이다.

### 경로가 없거나, 일부러 버릴 때

```text
  ip route 종류       패킷 처리                          로컬 프로그램이 보는 에러
  (맞는 줄 없음)       버림 + ICMP net unreachable        ENETUNREACH "Network is unreachable"
  unreachable         버림 + ICMP host unreachable       EHOSTUNREACH
  prohibit            버림 + ICMP admin prohibited       EACCES
  blackhole           조용히 버림 (ICMP 없음)              EINVAL
```

- 표의 아래 세 줄은 ip-route(8)의 설명 그대로다.
- 첫 줄의 ICMP는 전달(forwarding) 중인 라우터가 보낸다(Network Unreachable, 코드 0 — RFC 1812 §5.2.7.1). 리눅스는 포워딩이 켜진 인터페이스에서만 보낸다(`net/ipv4/route.c` `ip_error()`).
- **blackhole**은 원격 송신자에게 아무것도 알려주지 않는다. 밖에서 보면 "그냥 응답이 없다"다.
  - *블랙홀 라우트*: 해당 대역으로 가는 패킷을 알림 없이 버리는 경로다. 공격 트래픽 차단, 경로 집약 시 루프 방지용으로 쓴다.
- 기본 경로도 없고 맞는 줄도 없으면 `connect()`는 `ENETUNREACH`로 실패한다(connect(2)).

### 비대칭 라우팅 — 가는 길과 오는 길이 다르다

```text
            +---- FW-A (상태 추적) ----+
  클라이언트 |                          | 서버
            +---- FW-B (상태 추적) ----+

  SYN      클라이언트 -> FW-A -> 서버         FW-A: "새 연결" 기록
  SYN-ACK  서버 -> FW-B -> 클라이언트          FW-B: "SYN을 본 적 없음" -> 버림
```

- 라우팅은 방향마다 **따로** 결정된다. 가는 길과 오는 길이 같다는 보장이 없다.
- 순수하게 전달만 하는 라우터는 문제가 없다. 패킷마다 독립적으로 판단하기 때문이다.
  - 단, 역경로 검사(strict uRPF, RFC 3704)를 켠 라우터는 예외다. 아래 `rp_filter`와 같은 이유로 버린다.
- 문제는 **상태를 기억하는 장비**가 경로에 있을 때다(상태 방화벽, NAT, 로드밸런서).
  - 한쪽 방향만 본 장비는 반대 방향 패킷을 "모르는 연결"로 보고 버린다.
- 리눅스의 역경로 검사(`rp_filter`)도 비슷하게 버릴 수 있다.
  - strict 모드(1)는 "이 출발지로 되돌아가는 최선 경로가 들어온 인터페이스가 아니면" 패킷을 버린다.
  - 커널 기본값은 0(검사 안 함)이지만 일부 배포판은 시작 스크립트에서 켠다. 비대칭 라우팅에서는 loose 모드(2)를 권한다(kernel ip-sysctl 문서).
  - *상태 방화벽(stateful firewall)*: 연결마다 상태를 기록하고, 기록된 연결에 속한 패킷만 통과시키는 방화벽이다(48번).
  - *rp_filter(reverse path filter)*: 출발지 주소를 위조한 패킷을 걸러 내려고, 들어온 인터페이스가 그 출발지로 돌아가는 경로와 맞는지 검사하는 기능이다.

## 쓰이는 자료구조·알고리즘

- **트라이(접두사 트리)** — 최장 접두사 매칭의 표준 자료구조다.
  - 주소를 비트열로 보고, 프리픽스를 트리의 경로로 저장한다.
  - 목적지 비트를 따라 내려가며 "경로가 붙은 마지막 노드"를 기억하면 그것이 답이다.
  - 조회 비용은 테이블 크기가 아니라 **주소 길이(IPv4 32비트)**에 비례한다.
- **경로 압축(radix/PATRICIA 트라이)** — 가지가 없는 한 줄짜리 노드들을 건너뛰어 깊이를 줄인다. 개념: [radix 트라이](../../data-structure/20-radix-trie/2-summary.md), [트라이](../../data-structure/09-trie/2-summary.md).
- **리눅스 FIB = LC-trie** (kernel "LC-trie implementation notes")
  - 경로 압축: 갈라짐이 없는 비트들은 건너뛴다.
  - 레벨 압축: 꽉 찬 자식들을 한 단계 끌어올려, 한 노드가 비트 여러 개로 여러 자식을 한 번에 인덱싱한다.
  - 정확히 맞는 잎이 없으면 프리픽스 길이를 하나씩 줄이며 위로 **되돌아가(backtrack)** 최장 일치를 찾는다.
- **하드웨어 라우터** — 초당 수억 번 조회를 위해 TCAM(모든 줄을 병렬 비교하는 메모리)을 쓰기도 한다 [?].

## 적용 — 풀어나가는 법

### 1. 최장 접두사 매칭을 직접 구현한다 (TypeScript, 이진 트라이)

```ts
type Route = { prefix: string; nextHop: string };

class Node { child: [Node | null, Node | null] = [null, null]; route: Route | null = null; }

const toBits = (ip: string) =>
  ip.split('.').reduce((acc, o) => (acc << 8) | Number(o), 0) >>> 0;   // IPv4 -> 32비트 부호 없는 정수

class Fib {
  private root = new Node();

  add(r: Route) {
    const [addr, lenStr] = r.prefix.split('/');
    const bits = toBits(addr), len = Number(lenStr);
    let n = this.root;
    for (let i = 0; i < len; i++) {
      const b = (bits >>> (31 - i)) & 1;
      n = n.child[b] ??= new Node();
    }
    n.route = r;                                   // 이 깊이(= 프리픽스 길이)에 경로를 단다
  }

  lookup(ip: string): Route | null {
    const bits = toBits(ip);
    let n: Node | null = this.root, best = this.root.route;   // /0 (기본 경로)
    for (let i = 0; i < 32 && n; i++) {
      n = n.child[(bits >>> (31 - i)) & 1];
      if (n?.route) best = n.route;                // 더 깊이 맞을수록 = 더 긴 프리픽스
    }
    return best;
  }
}

const fib = new Fib();
fib.add({ prefix: '0.0.0.0/0',     nextHop: 'isp' });
fib.add({ prefix: '10.0.0.0/8',    nextHop: 'r1' });
fib.add({ prefix: '10.144.0.0/16', nextHop: 'r2' });
fib.add({ prefix: '10.144.2.0/24', nextHop: 'r3' });
fib.lookup('10.144.2.5');   // r3  (RFC 1812의 예)
fib.lookup('10.9.9.9');     // r1
fib.lookup('8.8.8.8');      // isp (기본 경로)
```

- 조회는 최대 32단계다. 테이블에 경로가 백만 개여도 같다.

### 2. "이 패킷은 실제로 어디로 가나"를 묻는다

```bash
ip route get 10.144.2.5            # 커널이 실제로 고르는 줄 (dev, via, src)
ip route get 10.144.2.5 from 10.0.1.23 iif eth1   # 들어오는 패킷 기준 (rp_filter 판단 재현)
ip route show table all            # 정책 라우팅 테이블까지
ip rule                            # 어느 테이블을 먼저 볼지 (정책 라우팅)
ip -6 route                        # IPv6 테이블은 따로다
sysctl net.ipv4.ip_forward net.ipv4.conf.all.rp_filter
```

- 장애를 보면 먼저 `ip route get <목적지>`를 친다. 테이블을 눈으로 읽는 것보다 정확하다.
- 경로를 추가·삭제하는 예

```bash
ip route add 10.8.0.0/16 via 10.0.1.254 dev eth0
ip route add blackhole 192.0.2.0/24          # 문서용 대역 예시: 조용히 버리기
ip route del 10.8.0.0/16
```

### 3. 코드에서 에러를 해석한다

- Java: `connect`가 `java.net.NoRouteToHostException`을 던지면 커널이 `EHOSTUNREACH`를 돌려준 것이다(OpenJDK `Net.c`의 errno→예외 매핑). 원인은 경로가 `unreachable`이거나, 중간에서 ICMP host unreachable이 왔거나, 같은 서브넷에서 ARP 응답이 없는 경우 등이다 [?].
  - 같은 매핑에서 `ENETUNREACH`는 전용 예외가 없어 `SocketException`("Network is unreachable")으로 온다. `EACCES`(prohibit 경로)는 `BindException`으로 매핑된다.
- Node.js: `err.code`가 `ENETUNREACH`(맞는 경로 없음), `EHOSTUNREACH`(호스트 도달 불가)로 온다.
- 이 둘은 "서버가 죽었다"와 다르다. **경로 문제**다. `ip route get`부터 본다.

### 4. VPN·클라우드에서 경로를 설계할 때

- VPN이 `0.0.0.0/0`을 밀어 넣으면 모든 트래픽이 VPN으로 간다(full tunnel). 일부 대역만 넣으면 그 대역만 간다(split tunnel).
- 더 긴 프리픽스를 추가하면 기존 경로를 **덮어쓴다.** 추가 전에 기존 테이블과 겹치는지 본다.
- 클라우드 라우팅 테이블도 최장 접두사 매칭이다. `/32` 한 줄이 `/16` 규칙을 조용히 이긴다.

## 장애 시나리오와 대처

### 1. 라우팅 루프 — `Time to live exceeded`

- **현상**: 특정 대역으로 가는 요청이 모두 실패한다.
- **보이는 형태**
  - `ping` 출력에 `Time to live exceeded`가 찍힌다.
  - `traceroute`에서 같은 두세 개 주소가 번갈아 반복되다가 30홉에서 끝난다.
  - 두 라우터 사이 링크 트래픽이 이상하게 많다(같은 패킷이 TTL만큼 왕복).
- **원인**: R1은 R2로, R2는 R1로 보내는 경로가 서로를 가리킨다. 정적 경로 오타, 경로 재분배 실수, 링크 장애 뒤 라우팅 프로토콜 수렴 중 일시 루프가 흔하다.
- **대처**
  - 반복되는 두 라우터에서 해당 목적지로 `ip route get`(또는 장비의 경로 조회)을 해 서로를 가리키는지 확인한다.
  - 잘못된 경로를 지운다. 수렴 중 일시 루프라면 프로토콜 수렴을 기다리며 모니터링한다(13번).
  - TTL 덕분에 루프는 "영원히"가 아니라 "TTL만큼"만 돈다. 그래도 링크 대역폭은 TTL배로 소비된다.

### 2. 블랙홀 라우트 — 에러 없이 조용히 사라진다

- **현상**: 특정 대역으로 가는 연결이 전부 타임아웃난다. 거절(RST)도, ICMP도 없다.
- **보이는 형태**
  - 클라이언트는 `connect` 타임아웃(`ETIMEDOUT`)만 본다. `ss -tan`에 `SYN-SENT`가 쌓인다.
  - `traceroute`가 어느 홉부터 `* * *`만 찍는다.
  - 경로를 가진 리눅스 장비에서 `ip route get <목적지>`가 경로를 보여 주지 않고 `RTNETLINK answers: Invalid argument`로 실패한다(blackhole 경로의 에러가 EINVAL이다, ip-route(8)). `ip route show table all`에 `blackhole 192.0.2.0/24` 같은 줄이 보인다.
- **원인**
  - 누군가 `blackhole` 경로를 넣었다(공격 차단 뒤 해제를 잊음).
  - 집약 경로를 광고하면서 실제로는 일부 하위 대역에 도달할 수 없다.
  - 다운된 터널 인터페이스로 경로가 향한다.
- **대처**
  - 경로마다 `ip route get`으로 추적하며 어디서 사라지는지 홉별로 찾는다.
  - 목적지 쪽에서 `tcpdump`로 패킷이 도착하는지 확인한다. 도착하지 않으면 경로 문제, 도착하는데 응답이 없으면 호스트 문제다.
  - 블랙홀 경로에는 이름표(주석·태그)와 만료 절차를 붙인다.

### 3. 비대칭 라우팅 + 상태 방화벽 — 응답만 막힌다

- **현상**: 요청은 서버에 도착하는데(서버 로그·`tcpdump`에 보임) 클라이언트는 응답을 못 받는다. 일부 흐름만, 또는 이중화 경로 한쪽이 바뀐 뒤부터 그렇다.
- **보이는 형태**
  - 서버 `tcpdump`: SYN 수신, SYN-ACK 송신이 보인다.
  - 클라이언트 `tcpdump`: SYN-ACK가 도착하지 않는다.
  - 방화벽 로그에 "상태 없는 패킷(invalid state) 드롭" 류가 찍힌다 [?].
- **원인**: 가는 길은 FW-A를, 오는 길은 FW-B를 지난다. FW-B는 SYN을 본 적이 없어 SYN-ACK를 버린다.
- **대처**
  - 상태를 가진 장비를 지나는 흐름은 **양방향이 같은 장비를 지나도록** 경로를 맞춘다. 대칭 라우팅, 소스 NAT, 방화벽 간 상태 동기화 중 하나를 쓴다.
  - 리눅스 호스트가 인터페이스 두 개로 비대칭을 만든다면 `rp_filter`를 확인한다. strict(1)면 loose(2)로 바꾸는 것을 검토한다(kernel ip-sysctl 문서).

### 4. 더 구체적인 경로가 트래픽을 가로챈다

- **현상**: VPN 연결, 도커 설치, 클라우드 경로 추가 뒤 특정 대역만 안 된다.
- **보이는 형태**: `ip route get <목적지>`의 `dev`가 예상(`eth0`)과 다르다(`tun0`, `docker0`, `br-xxxx`).
- **원인**: 새로 생긴 경로의 프리픽스가 기존 경로보다 길다. 최장 접두사 매칭 규칙대로 새 경로가 이긴다.
- **대처**
  - 새 경로의 대역을 바꾸거나(도커 `bip`·`default-address-pools`, 07번), 필요한 목적지에 더 긴 경로를 추가해 되찾는다.
  - VPN 클라이언트의 split tunnel 목록을 점검한다.

## 핵심 문장

- 라우터는 전체 경로를 모른다. 목적지 IP로 "다음 홉" 하나만 정하고, 그 결정을 홉마다 되풀이한다.
- 여러 줄이 맞으면 **프리픽스가 가장 긴 줄**이 이긴다. 기본 경로 `0.0.0.0/0`은 모든 것과 맞지만 길이가 0이라 다른 줄이 하나라도 맞으면 진다. 그래서 최후의 수단이다.
- 홉마다 바뀌는 것은 MAC 헤더와 TTL이다. 목적지 IP는 (NAT가 없으면) 끝까지 같다.
- TTL은 홉마다 최소 1 줄고, 0이면 버려지며 출발지에 Time Exceeded가 간다. 루프의 피해를 유한하게 만들고, traceroute의 재료가 된다.
- 경로는 방향마다 따로 정해진다. 상태를 가진 장비가 한 방향만 보면 응답만 사라진다.
- 장애 진단의 첫 명령은 `ip route get <목적지>`다.

## 관련 주제·근거

- 선행
  - [07-ip-addressing-cidr](../07-ip-addressing-cidr/2-summary.md) — 프리픽스·마스크
  - [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md) — 경로 압축 트라이 (커리큘럼 선행 표기 `data-structure/13-radix-trie`는 현재 20번 노트다)
- 후속·연결
  - [09-icmp-ping-traceroute](../09-icmp-ping-traceroute/2-summary.md) — TTL 초과를 이용한 경로 추적
  - [05-arp](../05-arp/2-summary.md) — 다음 홉의 MAC 찾기
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — 상태를 가진 장비와 비대칭 경로
  - [13-routing-protocols-ospf-bgp](../13-routing-protocols-ospf-bgp/2-summary.md) — 테이블을 누가 채우나
  - [48-firewalls-and-network-policy](../48-firewalls-and-network-policy/2-summary.md) — 상태 방화벽
  - [data-structure/09-trie](../../data-structure/09-trie/2-summary.md)
- RFC
  - RFC 1812 — IPv4 라우터 요구사항 <https://www.rfc-editor.org/rfc/rfc1812>
    - §5.2.4.3 Next Hop Address: Basic Match → Longest Match, 예시 10.144.2.5
    - §5.2.4.4 Administrative Preference
    - §5.3.1 TTL: 최소 1 감소(MUST), 0이면 버리고 Time Exceeded Code 0(MUST), traceroute를 위해 필요
    - §5.2.7.1 Destination Unreachable: 경로 없음 → Network Unreachable(코드 0)
  - RFC 3704 §2.2 Strict / §2.4 Loose Reverse Path Forwarding <https://www.rfc-editor.org/rfc/rfc3704>
  - RFC 1122 §3.3.1.1 Local/Remote Decision — 호스트의 직접/게이트웨이 판단(MUST) <https://www.rfc-editor.org/rfc/rfc1122>
  - RFC 791 §3.1 — TTL 필드 <https://www.rfc-editor.org/rfc/rfc791>
- Linux
  - ip-route(8) — `unreachable`(EHOSTUNREACH), `blackhole`(EINVAL), `prohibit`(EACCES), `preference`(작을수록 우선), `ip route get` <https://man7.org/linux/man-pages/man8/ip-route.8.html>
  - connect(2) — `ENETUNREACH` <https://man7.org/linux/man-pages/man2/connect.2.html>
  - `net/ipv4/route.c` — `ip_route_input_slow()`의 `no_route:` → `RTN_UNREACHABLE`, `ip_error()`가 포워딩 인터페이스에서 `ICMP_NET_UNREACH` 전송 <https://github.com/torvalds/linux/blob/master/net/ipv4/route.c>
  - kernel "IP Sysctl" — `ip_default_ttl`(64), `rp_filter`(0/1 strict/2 loose, 기본 0), `ip_forward` <https://docs.kernel.org/networking/ip-sysctl.html>
  - kernel "LC-trie implementation notes" — FIB의 경로·레벨 압축, 백트래킹 <https://docs.kernel.org/networking/fib_trie.html>
- OpenJDK `src/java.base/unix/native/libnio/ch/Net.c` — `EHOSTUNREACH`→`NoRouteToHostException`, `ECONNREFUSED`→`ConnectException` <https://github.com/openjdk/jdk/blob/master/src/java.base/unix/native/libnio/ch/Net.c>
- AWS, "How route priority works" — 최장 접두사 매칭, `/32`가 `/24`보다 우선 <https://docs.aws.amazon.com/vpc/latest/userguide/route-tables-priority.html>
- 교재: Kurose & Ross 8판 4.2.1 "Input Port Processing and Destination-Based Forwarding"(최장 접두사 매칭)
