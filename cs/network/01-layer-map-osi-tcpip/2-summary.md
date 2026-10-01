# network/01-layer-map-osi-tcpip — 계층 지도: OSI 7계층과 TCP/IP 4계층, 계층별 PDU — 정리 (힌트)

## 해결하는 문제

"네트워크가 안 돼요"는 증상이 아니라 뭉뚱그린 말이다.\
실제로는 어느 한 층에서 무언가가 깨진다.\
층을 나눠 두면 "어디까지는 되고, 어디서부터 안 되나"를 차례로 좁혀 갈 수 있다.

```text
  "사이트가 안 열려요"
        |
        +-- 이름을 IP로 못 바꿨나?           (응용 계층: DNS)
        +-- IP까지 길이 없나?                (인터넷 계층: 라우팅)
        +-- 길은 있는데 포트가 닫혔나?        (전송 계층: TCP)
        +-- 연결은 됐는데 TLS·HTTP가 실패했나? (응용 계층)
        +-- 케이블·무선 자체가 죽었나?         (링크 계층)
```

쉬운 예: 택배다.\
주문서(내용물) → 상자에 송장 → 트럭에 실음 → 도로를 달림.\
택배가 안 오면 "주문이 안 들어갔나, 송장 주소가 틀렸나, 트럭이 고장 났나, 도로가 막혔나"를 나눠서 본다.

똑같은 구조다.\
각 층은 자기 일만 하고, 바로 아래층이 주는 서비스만 믿는다.\
그래서 층 하나를 따로 점검할 수 있다.

실무 예:
- 배포 뒤 API 호출이 실패한다.
  - `UnknownHostException`이면 DNS(응용 계층) 문제다. 서버는 멀쩡할 수 있다.
  - `Connection refused`면 대개 IP 경로는 살아 있다. 그 포트에서 듣는 프로세스가 없다(전송 계층). 단, 중간 방화벽의 REJECT도 같은 에러를 낸다(아래 장애 3).
  - `connect timed out`이면 패킷이 가다가 사라진다. 방화벽이나 경로(인터넷 계층 이하)를 본다.
- 이 셋을 모두 "네트워크 장애"라고 부르면 엉뚱한 팀을 부르게 된다.

## 동작·원리

### 두 개의 지도 — OSI 7계층과 TCP/IP 4계층

```text
  OSI 참조 모델 (7)          인터넷 교재 모델 (K&R, 5)     RFC 1122 (4)
  +----------------+        +----------------+          +----------------+
  | 7 응용          |        |                |          |                |
  | 6 표현          |  --->  | 응용            |  --->    | 응용 (Application) |
  | 5 세션          |        |                |          |                |
  +----------------+        +----------------+          +----------------+
  | 4 전송          |  --->  | 전송            |  --->    | 전송 (Transport)   |
  +----------------+        +----------------+          +----------------+
  | 3 네트워크      |  --->  | 네트워크        |  --->    | 인터넷 (Internet)  |
  +----------------+        +----------------+          +----------------+
  | 2 데이터 링크   |  --->  | 링크            |  --->    | 링크 (Link)        |
  | 1 물리          |  --->  | 물리            |          |                |
  +----------------+        +----------------+          +----------------+
```

- **OSI 모델**은 ISO가 만든 7계층 참조 모델이다(ISO/IEC 7498-1).
  - 표현(데이터 표현·암호화·압축)과 세션(대화 관리)을 따로 둔다.
  - 인터넷 프로토콜은 이 두 층을 따로 두지 않는다. 필요하면 응용이 직접 한다(K&R 1.5.1).
- **TCP/IP 모델**은 인터넷이 실제로 쓰는 구조다.
  - RFC 1122 §1.1.3은 호스트의 프로토콜을 응용·전송·인터넷·링크 4계층으로 나눈다.
  - 같은 절은 인터넷 응용 계층이 OSI의 "위 두 층(표현·응용)" 기능을 합친 것이라고 적는다. 세션 계층까지 응용에 묶는 것은 교재들의 관례적 대응이다.
  - K&R은 링크 아래 물리를 따로 떼어 5계층으로 가르친다(K&R 1.5.1).
- 실무에서 "L2·L3·L4·L7"이라 부르는 번호는 OSI 번호다.
  - L2 스위치, L3 라우터, L4 로드밸런서(TCP/UDP 포트 기준), L7 로드밸런서(HTTP 기준)처럼 쓴다.

  - *계층(layer)*: 아래층이 주는 서비스를 받아 위층에 새 서비스를 주는 한 묶음의 프로토콜.
  - *프로토콜(protocol)*: 같은 층끼리 주고받는 메시지의 형식과 순서, 그리고 받았을 때 할 행동의 약속.

### 각 층이 하는 일과 대표 프로토콜

```text
  층        하는 일                              대표 프로토콜            주소
  -------   ----------------------------------   ----------------------   -----------------
  응용      앱끼리 주고받을 메시지의 뜻            HTTP, DNS, SMTP, TLS*    도메인 이름·URL
  전송      프로세스 대 프로세스 전달(포트)          TCP, UDP (QUIC**)        포트 번호
  인터넷    호스트 대 호스트, 여러 망을 건너 전달    IP (v4/v6), ICMP        IP 주소
  링크      한 링크(같은 망) 안에서 옆 장비로 전달   이더넷, Wi-Fi, ARP***   MAC 주소
  (물리)    비트를 전기·빛·전파로                  케이블·광·무선 규격       —
```

- 전송 계층은 "프로세스"까지 간다. 그래서 포트가 필요하다.
- 인터넷 계층은 "호스트"까지만 간다. RFC 1122는 모든 전송 프로토콜이 IP로 출발 호스트에서 도착 호스트까지 데이터를 나른다고 적는다(§1.1.3).
- 링크 계층은 "바로 옆 장비"까지만 간다. 여러 홉을 건너는 것은 IP의 일이다.
- 표의 별표는 층이 딱 떨어지지 않는 경우다.
  - `*` TLS는 TCP 위, HTTP 아래에 있다. OSI로는 표현 계층 비슷하지만, TCP/IP 모델에서는 보통 응용 계층 쪽에 둔다.
  - `**` QUIC은 UDP 위에서 돈다. 그런데 신뢰 전송·혼잡 제어를 직접 하므로 스스로를 전송 프로토콜이라 부른다(RFC 9000).
  - `***` ARP는 IP 주소를 MAC 주소로 바꾼다. 인터넷과 링크 사이에 걸쳐 있다(05번).
- 모델은 지도이지 법이 아니다. "이 프로토콜은 몇 계층인가"보다 "누구의 서비스를 받아 누구에게 주나"가 중요하다.

### 계층별 데이터 단위 — PDU

```text
  응용      [          메시지 (message)           ]
  전송      [TCP 헤더][      메시지      ]            = 세그먼트 (segment)   / UDP는 데이터그램
  인터넷    [IP 헤더][TCP 헤더][ 메시지 ]             = IP 데이터그램 (패킷)
  링크      [이더넷 헤더][IP 헤더][TCP 헤더][메시지][FCS] = 프레임 (frame)
```

  - *PDU(Protocol Data Unit)*: 한 층이 한 번에 주고받는 데이터 단위. 층마다 이름이 다르다.

RFC 1122 §1.3.3의 정의는 이렇다.
- **segment**: TCP의 전송 단위. TCP 헤더 + 응용 데이터.
- **datagram**: IP의 전송 단위. IP 헤더 + 전송 계층 데이터.
- **packet**: 인터넷 계층과 링크 계층 사이 인터페이스로 넘어가는 데이터 단위.
- **frame**: 링크 계층의 전송 단위. 링크 헤더 + packet.

실무에서는 "패킷"을 층 구분 없이 막 쓴다.\
진단할 때는 이름을 정확히 쓰는 편이 낫다. "프레임이 깨진다"(링크)와 "세그먼트가 재전송된다"(전송)는 전혀 다른 곳을 가리킨다.\
헤더가 붙는 과정 자체는 [02-encapsulation](../02-encapsulation/2-summary.md)에서 다룬다.

### 누가 어느 층까지 보나

```text
  호스트 A              스위치           라우터             호스트 B
  +------+                                                +------+
  | 응용 |                                                | 응용 |
  | 전송 |                                                | 전송 |
  | 인터넷|                         +------+               | 인터넷|
  | 링크 | ----> +------+ ---->    | 인터넷| ---->  ...   | 링크 |
  | 물리 |       | 링크 |          | 링크 |               | 물리 |
  +------+       | 물리 |          | 물리 |               +------+
                 +------+          +------+
```

- 호스트는 모든 층을 구현한다.
- 스위치는 링크 계층까지만 본다. MAC 주소로 전달한다.
- 라우터는 인터넷 계층까지 본다. IP 주소로 다음 홉을 고른다.
- 이 구분이 K&R 1.5.2의 그림(호스트·스위치·라우터가 구현하는 층이 다름)이다.
- 그래서 스위치 장애는 같은 망 안의 통신을 깨고, 라우터 장애는 망을 건너는 통신을 깬다.
- 실제 장비는 이 선을 넘기도 한다. L4/L7 로드밸런서·NAT·방화벽은 라우터 자리에 있으면서 포트나 HTTP까지 들여다본다.

### 층을 나눠서 얻는 것과 잃는 것

- 얻는 것
  - 각 층을 따로 바꿀 수 있다. Wi-Fi를 이더넷으로 바꿔도 HTTP 코드는 그대로다.
  - 각 층을 따로 진단할 수 있다.
- 잃는 것
  - 층마다 헤더가 붙어 오버헤드가 생긴다(02번).
  - 아래층의 사정(패킷 크기, 지연)을 위층이 모른 채 일하다가 성능·장애가 생긴다. MTU 문제(10번)가 대표다.
  - 같은 기능이 여러 층에 겹치기도 한다. 예: 링크의 CRC, IP 헤더 체크섬, TCP 체크섬.

## 쓰이는 자료구조·알고리즘

- **계층 = 인터페이스 스택** — 각 층은 "아래층 인터페이스를 호출하고 위층 인터페이스를 제공"하는 추상화다.
  - 코드로 보면 `interface Transport { send(bytes) }` 위에 HTTP 클라이언트가 있고, 그 아래에 소켓이 있는 구조다.
  - 스택처럼 쌓여서 송신은 위→아래, 수신은 아래→위로 호출이 흐른다. 스택 자료구조는 [data-structure/03-stack](../../data-structure/03-stack/2-summary.md) 참고.
- **역다중화(demultiplexing) 키** — 받은 데이터를 어느 위층에 넘길지 헤더의 필드 하나로 고른다.
  - 링크: EtherType(0x0800이면 IPv4, RFC 7042)
  - 인터넷: IP의 Protocol 필드(6이면 TCP, 17이면 UDP)
  - 전송: 목적지 포트 번호
  - 이 선택은 "키 → 처리기" 조회라서 구현에서는 배열 인덱스나 해시 테이블로 한다.
- **이분 탐색식 진단** — 층을 아래부터(또는 위부터) 하나씩 확인해 "되는 층"과 "안 되는 층"의 경계를 찾는다.

## 적용 — 풀어나가는 법

### 1. 에러 메시지를 층에 대응시킨다

```text
  보이는 형태                                        층        뜻
  ------------------------------------------------   -------   ----------------------------------------
  Java UnknownHostException / Node ENOTFOUND         응용(DNS)  이름을 IP로 못 바꿈
  Java NoRouteToHostException / EHOSTUNREACH          인터넷    unreachable 경로·ARP 실패, 또는 중간에서 막힘(ICMP host unreachable)
  ENETUNREACH "Network is unreachable"                인터넷    내 라우팅 테이블에 경로가 없거나, 경로상 라우터가 ICMP 네트워크 도달 불가를 보냄
  Java ConnectException "Connection refused"          전송      그 포트에 듣는 프로세스 없음(RST 받음). 또는 방화벽 REJECT(RST나 ICMP port unreachable)
    / Node ECONNREFUSED
  connect timed out / ETIMEDOUT                       ?         응답이 안 옴 — 방화벽 DROP, 경로, 상대 과부하
  SSLHandshakeException / TLS alert                   응용(TLS)  연결은 됨. 인증서·프로토콜 협상 실패
  HTTP 502 / 504                                      응용       프록시 뒤 서버 문제(프록시까지는 정상)
```

- 근거
  - `ECONNREFUSED`: "no one listening on the remote address"(connect(2)).
  - `EHOSTUNREACH`: 맞는 라우팅 항목이 없음. 원격 라우터의 ICMP 메시지로도 생긴다(ip(7)).
    - 단 리눅스에서 로컬 경로가 아예 없으면 `ENETUNREACH`다. 로컬에서 `EHOSTUNREACH`가 나는 것은 `unreachable` 타입 경로(ip-route(8))나 같은 링크의 ARP 실패(05번)다.
  - 리눅스는 connect 중(SYN_SENT)에 받은 ICMP 도달 불가를 errno로 바꿔 connect를 실패시킨다(`net/ipv4/tcp_ipv4.c` `tcp_v4_err()`). 변환표는 `net/ipv4/icmp.c` `icmp_err_convert[]`다.
    - port unreachable → `ECONNREFUSED`
    - net unreachable·net unknown·net admin prohibited → `ENETUNREACH`
    - host unreachable·host admin prohibited·pkt filtered → `EHOSTUNREACH`
  - Node `ENOTFOUND`: DNS 실패(EAI_NODATA 또는 EAI_NONAME)다. POSIX 표준 에러가 아니다(Node errors 문서).
  - Java `NoRouteToHostException`: 방화벽이나 중간 라우터 때문에 원격 호스트에 닿지 못했다는 뜻이다(Javadoc).
- 타임아웃은 층을 알려 주지 않는다. "보냈는데 아무 답이 없다"는 사실만 말한다. 그래서 다른 층부터 확인해 좁힌다.

### 2. 아래에서 위로 확인한다

```bash
# 링크: 인터페이스가 살아 있고 에러 카운터가 늘지 않나
ip -s link show eth0

# 인터넷: 목적지로 가는 경로·출구 인터페이스·게이트웨이
ip route get 203.0.113.10
ping -c 3 203.0.113.10          # ICMP를 막는 망도 많다. 안 된다고 곧 장애는 아니다

# 전송: 그 포트에 TCP 연결이 되나
nc -vz 203.0.113.10 443
ss -tan state syn-sent          # 내 쪽 SYN이 답을 못 받고 쌓였나

# 응용: 이름 풀이, TLS, HTTP
dig api.example.com
curl -v https://api.example.com/health
```

- 주소 `203.0.113.10`은 문서용 예시 주소다(RFC 5737).
- `curl -v` 출력은 층 순서대로 나온다. 이름 풀이 → TCP 연결(`Connected to`) → TLS 핸드셰이크 → HTTP 요청·응답이다. 어디서 멈추는지가 곧 고장 난 층이다.

### 3. 코드에서 층별로 예외를 나눈다

```java
// 층을 한 단계씩 밟는 연결 점검 — 어디서 실패했는지가 곧 층이다
static String probe(String host, int port) {
    InetAddress ip;
    try {
        ip = InetAddress.getByName(host);                 // 응용(DNS)
    } catch (UnknownHostException e) {
        return "DNS 실패";                                  // 서버가 아니라 이름 풀이 문제
    }
    try (Socket s = new Socket()) {
        s.connect(new InetSocketAddress(ip, port), 3_000); // 전송(TCP). 3초는 예시
        return "TCP 연결 성공 — 이제 TLS·HTTP를 본다";
    } catch (NoRouteToHostException e) {
        return "경로 없음";                                  // 인터넷 계층
    } catch (ConnectException e) {
        return "연결 거부(refused 등)";                      // 대개 전송 계층: 포트에 듣는 프로세스 없음
    } catch (SocketTimeoutException e) {
        return "연결 타임아웃";                              // 층 불명: 방화벽 DROP·경로·과부하
    } catch (IOException e) {
        return "기타: " + e;
    }
}
```

- `NoRouteToHostException`과 `ConnectException`은 둘 다 `SocketException`의 하위 클래스다(Javadoc). 부모인 `IOException`보다 먼저 잡아야 구분된다.
- 로그에 예외 이름을 남기면 "어느 층에서 깨졌나"가 로그만으로 보인다.
- 메트릭도 같은 기준으로 나누면 좋다. 예: `dns_error`, `connect_refused`, `connect_timeout`, `tls_error`, `http_5xx`.

## 장애 시나리오와 대처

### 1. "네트워크 장애"로 뭉뚱그려 진단이 늦어진다

- **현상**: 외부 API 호출이 실패하자 "네트워크 문제"로 네트워크팀에 넘긴다. 원인 파악에 몇 시간이 걸린다.
- **보이는 형태**: 로그에 `IOException`만 찍혀 있다. 예외 종류·메시지를 버리고 "호출 실패"로만 적었다.
- **원인**: 증상의 층을 가리지 않았다. 실제로는 DNS 레코드 변경, 방화벽 규칙, 인증서 만료처럼 담당이 다른 문제일 수 있다.
- **대처**
  - 예외 타입과 원래 메시지를 그대로 로그에 남긴다.
  - 위 표처럼 에러를 층에 대응시키고, 아래 층부터 확인한다.
  - 장애 보고서에 "어느 층까지 정상이었나"를 한 줄로 적는다.

### 2. `UnknownHostException` / `ENOTFOUND` — 서버는 멀쩡한데 호출이 실패

- **현상**: 특정 호스트 이름으로만 실패한다. IP로 직접 부르면 된다.
- **보이는 형태**: Java `java.net.UnknownHostException: api.example.com`, Node `getaddrinfo ENOTFOUND api.example.com`(DNS 서버가 SERVFAIL이거나 응답이 없으면 `EAI_AGAIN`).
- **원인**: 응용 계층의 DNS 문제다. 레코드 삭제, 오타, 내부 DNS 장애, 컨테이너의 `resolv.conf` 설정 오류 등이다. IP 경로·TCP와는 무관하다.
- **대처**: `dig 이름`으로 직접 질의해 본다. 어느 DNS 서버가 무엇을 답하는지 확인한다(27·28번).

### 3. `Connection refused` vs `connect timed out`을 같은 것으로 본다

- **현상**: 둘 다 "연결 실패"로 묶어 같은 대응(재시작)을 한다.
- **보이는 형태**
  - refused는 즉시 실패한다. tcpdump에 SYN 다음 `[R.]`(RST)가 보인다. 방화벽 REJECT라면 RST 대신 ICMP port unreachable이 보일 수 있다.
  - timeout은 수 초~수십 초 뒤 실패한다. SYN만 반복되고 답이 없다.
- **원인**
  - refused: 상대 호스트까지는 닿았다(인터넷 계층 정상). 그 포트에 듣는 프로세스가 없어 커널이 RST로 답했다(전송 계층).
    - 예외: 중간 방화벽의 REJECT도 refused를 만든다. iptables `REJECT`의 기본 응답은 ICMP port unreachable이고(iptables-extensions(8)), 리눅스는 이를 `ECONNREFUSED`로 바꾼다. 이때 패킷은 상대 호스트에 닿지 않았다.
    - 그래서 tcpdump로 RST·ICMP를 누가 보냈는지(출발 IP) 확인해야 도착 여부를 판단할 수 있다.
  - timeout: SYN이 어딘가에서 버려졌다. 방화벽 DROP, 경로 없음, 상대 SYN 큐 과부하 등이다.
- **대처**
  - refused면 대상 프로세스가 떠 있는지, 포트·바인드 주소(`127.0.0.1`만 듣는지)를 본다. `ss -ltn`으로 확인한다.
  - timeout이면 경로·보안 그룹·방화벽을 본다. `tcpdump`로 SYN이 나가는지, 상대에 도착하는지 양쪽에서 잡는다.

### 4. 링크 계층 문제가 위층의 "간헐 느림"으로만 보인다

- **현상**: 특정 서버만 가끔 느리다. 애플리케이션 로그에는 에러가 없다.
- **보이는 형태**: TCP 재전송 증가(`ss -ti`의 `retrans`), 응답 시간 꼬리(p99) 상승. `ip -s link`의 RX errors·dropped 증가.
- **원인**: 케이블·포트 불량이나 duplex 불일치로 프레임이 깨진다. 수신 쪽이 CRC 검사에서 프레임을 버린다. TCP가 재전송으로 메워 주니 위에서는 "느림"으로만 보인다(04번).
- **대처**: 재전송이 늘면 링크 카운터부터 본다. `ethtool -S`, `ip -s link`로 에러 카운터가 오르는지 확인한다.

## 핵심 문장

- 계층은 "각 층은 바로 아래층 서비스만 믿는다"는 약속이다. 그래서 층 하나씩 따로 고치고 따로 진단할 수 있다.
- RFC 1122는 인터넷 호스트를 응용·전송·인터넷·링크 4계층으로 나눈다. 실무의 L2·L3·L4·L7 번호는 OSI 7계층 번호다.
- 전송 계층은 프로세스(포트)까지, 인터넷 계층은 호스트(IP)까지, 링크 계층은 바로 옆 장비(MAC)까지 데이터를 옮긴다.
- 같은 데이터가 층마다 세그먼트 → 데이터그램(패킷) → 프레임으로 이름이 바뀐다.
- 장애는 "어느 층까지 정상인가"로 좁힌다. 에러 이름(DNS 실패, refused, unreachable, timeout, TLS 실패)이 층을 가리킨다.

## 관련 주제·근거

- 후속
  - [02-encapsulation](../02-encapsulation/2-summary.md) — 층마다 헤더가 붙고 벗겨지는 과정
  - [03-latency-bandwidth-bdp](../03-latency-bandwidth-bdp/2-summary.md) — 층을 지나며 쌓이는 지연
  - [04-ethernet-and-mac](../04-ethernet-and-mac/2-summary.md) — 링크 계층
  - [26-packet-journey](../26-packet-journey/2-summary.md) — 모든 층을 한 번에 따라가는 종합편.
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) — `UnknownHostException`의 본체.
- RFC 1122 "Requirements for Internet Hosts — Communication Layers" <https://www.rfc-editor.org/rfc/rfc1122>
  - §1.1.3 4계층(Application·Transport·Internet·Link)
  - §1.3.3 용어(segment·datagram·packet·frame)
- RFC 7042 — EtherType 값(IPv4 0x0800, ARP 0x0806, IPv6 0x86DD) <https://www.rfc-editor.org/rfc/rfc7042>
- IANA "Assigned Internet Protocol Numbers" — TCP 6, UDP 17 <https://www.iana.org/assignments/protocol-numbers/>
- RFC 9000 — QUIC: 전송 프로토콜 <https://www.rfc-editor.org/rfc/rfc9000>
- RFC 5737 — 문서용 IPv4 주소 블록(203.0.113.0/24 등) <https://www.rfc-editor.org/rfc/rfc5737>
- ISO/IEC 7498-1 — OSI 기본 참조 모델
- Linux man-pages
  - connect(2) — `ECONNREFUSED`, `ENETUNREACH`, `ETIMEDOUT` <https://man7.org/linux/man-pages/man2/connect.2.html>
  - iptables-extensions(8) — `REJECT` 기본 `icmp-port-unreachable` <https://man7.org/linux/man-pages/man8/iptables-extensions.8.html>
- Linux 소스 — `net/ipv4/icmp.c` `icmp_err_convert[]`(ICMP 코드 → errno), `net/ipv4/tcp_ipv4.c` `tcp_v4_err()`(SYN_SENT에서 ICMP 오류 시 연결 실패) <https://github.com/torvalds/linux/blob/master/net/ipv4/icmp.c>
  - ip(7) — `EHOSTUNREACH` <https://man7.org/linux/man-pages/man7/ip.7.html>
- Node.js Errors 문서 — Common system errors(`ENOTFOUND`, `ECONNREFUSED`, `ETIMEDOUT`) <https://nodejs.org/api/errors.html>
- Java `NoRouteToHostException` Javadoc <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/NoRouteToHostException.html>
- Kurose & Ross 8판 1.5 "Protocol Layers and Their Service Models"(1.5.1 계층 구조, 1.5.2 캡슐화)
