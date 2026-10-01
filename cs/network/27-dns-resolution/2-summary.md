# network/27-dns-resolution — 이름이 IP가 되기까지, 도메인 트리를 따라 내려가기 — 정리 (힌트)

## 해결하는 문제

패킷은 IP 주소로 간다.\
사람과 설정 파일은 `api.example.com` 같은 이름을 쓴다.\
그래서 "이름 → 주소" 표가 필요하다.

그런데 인터넷의 이름은 수억 개이고 매일 바뀐다.\
표 하나를 한 곳에 둘 수 없다.\
DNS는 이 표를 **나무 모양으로 쪼개 여러 관리자에게 나눠 맡긴** 분산 데이터베이스다.

```text
                         . (루트)
             +-----------+-----------+
            com         org          kr
         +---+---+                  +--+
      example  google              co
      +---+                         |
     www  api                     naver
```

- 이름은 오른쪽에서 왼쪽으로 읽으면 나무의 위에서 아래로 가는 경로다. `api.example.com.` = 루트 → `com` → `example` → `api`.
- 각 가지(영역)를 맡은 서버가 따로 있다. 루트는 "com은 저 서버에 물어봐"만 알고, `com`은 "example.com은 저 서버에 물어봐"만 안다.

쉬운 예: 큰 회사의 내선 번호 찾기다.\
안내 데스크(루트)에 물으면 "영업본부 비서실에 물어보세요"라고 한다.\
영업본부 비서실(TLD)은 "해외영업팀 막내에게 물어보세요"라고 한다.\
해외영업팀(권한 서버)이 최종 번호를 알려 준다.\
직원 대부분은 이걸 직접 돌지 않고, 비서(재귀 해석기)에게 "알아봐 줘"라고 한 번만 부탁한다.

똑같은 구조다.\
앱은 OS에 한 번 묻고, OS는 재귀 해석기에 한 번 묻고, 재귀 해석기가 나무를 따라 내려간다.

실무 예:
- `java.net.UnknownHostException`, Node `getaddrinfo ENOTFOUND`, `curl: (6) Could not resolve host`
- `dig`에서 `status: SERVFAIL` — 이름은 맞는데 권한 서버 쪽에 문제가 있다.
- 루트 도메인(`example.com`)에 CNAME을 걸려다 DNS 콘솔이 거부한다.

## 동작·원리

### 등장인물

```text
  [앱] --getaddrinfo()--> [스텁 해석기(OS 라이브러리)] --RD=1 질의--> [재귀 해석기(캐시)]
                           /etc/resolv.conf 읽음                     |  반복 질의(RD=0)
                                                                     +--> 루트 서버
                                                                     +--> TLD 서버 (com)
                                                                     +--> 권한 서버 (example.com)
```

- *스텁 해석기(stub resolver)*: 앱 옆의 작은 해석기다. 보통 OS 라이브러리(glibc 등)다. 스스로 나무를 따라가지 않고 재귀 해석기에 통째로 부탁한다.
- *재귀 해석기(recursive resolver)*: 사내 DNS, 통신사 DNS, 공용 DNS(8.8.8.8 등)다. 대신 나무를 따라가 답을 가져오고, 결과를 캐시한다.
- *권한 서버(authoritative server)*: 어떤 영역(zone)의 원본 데이터를 가진 서버다. 그 영역에 대해서는 "최종 답"을 준다.
- *영역(zone)*: 한 관리 주체가 맡는 나무의 한 덩어리다. 예: `example.com` 영역. 하위를 다른 곳에 떼어 주는 것을 *위임(delegation)* 이라 한다.

### 재귀 질의 vs 반복 질의

```text
  재귀(recursive):  "답을 가져와 줘"          -> 받는 쪽이 다른 서버에 대신 묻고 최종 답 또는 에러만 준다
  반복(iterative):  "아는 만큼만 알려 줘"      -> 받는 쪽이 답, 에러, 또는 "저 서버에 물어봐"(referral)를 준다
```

- RFC 1034 §4.3.1
  - 모든 네임 서버는 비재귀 질의를 구현해야 한다(must).
  - 재귀 서비스는 선택이고, 서버는 누구에게 재귀를 해 줄지 제한할 수 있다.
- 헤더 비트 두 개로 합의한다.
  - *RD(Recursion Desired)*: 질의자가 "재귀로 해 줘"를 요청하는 비트.
  - *RA(Recursion Available)*: 서버가 "나는 재귀를 해 줄 수 있다"를 알리는 비트. 응답마다 켜거나 끈다.
  - 응답에 RD와 RA가 둘 다 켜져 있으면 재귀로 처리된 것이다.
- 스텁 → 재귀 해석기 구간은 재귀 질의다. 재귀 해석기 → 루트·TLD·권한 서버 구간은 반복 질의다.

### 따라 내려가기 — `www.example.com`의 A 레코드

```text
  재귀 해석기                                                   (캐시가 비어 있다고 가정)
   1 --> 루트 서버      "www.example.com A?"
     <-- "모른다. com은 이 서버들이 맡는다"  NS a.gtld-servers.net ... (+ 그 IP: glue)
   2 --> com TLD 서버   "www.example.com A?"
     <-- "모른다. example.com은 이 서버들이 맡는다"  NS ns1.example.net ... (+ glue)
   3 --> example.com 권한 서버  "www.example.com A?"
     <-- AA=1  www.example.com. 300 IN A 192.0.2.10      (TTL 300은 예시)
   4 --> 스텁 해석기에 답 전달, 캐시에 TTL 동안 보관
```

- 루트 서버를 찾는 출발점은 **루트 힌트** 파일이다. 루트 서버 이름·주소 목록이며, 많은 소프트웨어에 내장돼 있다(IANA).
- 루트 서버는 루트 영역에 **13개의 이름**(a~m.root-servers.net)으로 등록돼 있다. 실제 서버는 전 세계 수백 대다(IANA).
- *referral(위임 응답)*: "나는 모르지만 저 서버에 물어봐"라는 응답이다. NS 레코드로 온다.
- *glue*: NS 서버의 이름이 그 영역 안에 있을 때, 그 이름의 주소를 같이 넣어 주는 레코드다. 없으면 "주소를 알려면 그 서버에 물어야 하는" 순환에 빠진다(RFC 1034 §4.2.1).
- *AA(Authoritative Answer)*: 응답 헤더 비트다. 권한 서버가 준 답이면 켜진다.
- 캐시가 있으면 1·2단계를 건너뛴다. 실제로는 대부분의 질의가 캐시에서 끝난다. 캐시·TTL은 28번 노트의 몫이다.

### 메시지 — 작고 단순하다

```text
  +---------------------------------------------+
  | Header  ID | QR Opcode AA TC RD RA Z RCODE  |   12바이트
  +---------------------------------------------+
  | Question    QNAME, QTYPE, QCLASS             |   무엇을 묻나
  | Answer      RR ...                           |   답
  | Authority   RR ... (NS 등)                    |   누가 권한이 있나
  | Additional  RR ... (glue 등)                  |   덤
  +---------------------------------------------+
```

- 전송은 UDP·TCP 포트 53이다(RFC 1035 §4.2).
  - UDP 메시지는 원래 512바이트 이하다. 넘으면 잘라서 TC(truncated) 비트를 켠다(RFC 1035 §4.2.1). 클라이언트는 TC를 보고 TCP로 다시 묻는다(RFC 7766 §4).
  - EDNS(0)로 더 큰 UDP 크기를 협상할 수 있다(RFC 6891).
  - 범용 DNS 구현은 UDP와 TCP를 **둘 다** 지원해야 한다(MUST, RFC 7766 §5).
- RCODE(응답 코드, RFC 1035 §4.1.1)

```text
  0 NOERROR   오류 없음 (답이 비어 있을 수도 있다: "이름은 있는데 그 타입이 없음")
  1 FORMERR   질의 형식 오류
  2 SERVFAIL  서버 문제로 처리 못 함
  3 NXDOMAIN  (권한 서버 기준) 그 이름이 존재하지 않음
  4 NOTIMP    지원 안 함
  5 REFUSED   정책상 거부
```

- 크기 제한(RFC 1035 §2.3.4): 라벨 하나 63바이트, 이름 전체 255바이트.

### 레코드 종류

```text
  타입    번호  담는 것                         예
  A        1   IPv4 주소                        www.example.com.  A     192.0.2.10
  NS       2   이 영역의 권한 서버 이름           example.com.      NS    ns1.example.net.
  CNAME    5   별명 -> 정식 이름                  shop.example.com. CNAME shops.vendor.example.
  SOA      6   영역의 시작·관리 파라미터          example.com.      SOA   ns1... admin... (serial 등)
  MX      15   메일 서버 (우선순위 + 이름)        example.com.      MX    10 mail.example.com.
  TXT     16   임의 문자열 (SPF·도메인 소유 확인)  example.com.      TXT   "v=spf1 -all"
  AAAA    28   IPv6 주소                        www.example.com.  AAAA  2001:db8::10
```

- 번호는 RFC 1035 §3.2.2와 RFC 3596(AAAA)이다.
- *RR(Resource Record)*: DNS 데이터 한 줄. 이름·타입·클래스·TTL·데이터로 된다.
- MX·NS·CNAME의 값은 **이름**이다. IP가 아니다. 그래서 그 이름을 다시 A/AAAA로 찾아야 한다.

### CNAME의 규칙 — 그리고 apex 문제

- CNAME은 "이 이름은 저 이름의 별명"이다. 해석기는 CNAME을 만나면 정식 이름으로 다시 찾는다.
- **CNAME이 있는 이름에는 다른 데이터가 있으면 안 된다.**
  - RFC 1034 §3.6.2: "If a CNAME RR is present at a node, no other data should be present."(RFC 2119 이전 문서의 소문자 should)
  - RFC 2181 §10.1: 별명 이름에는 DNSSEC 레코드 외에 다른 데이터가 "may have no other data"라고 명확히 했다.
- 영역의 꼭대기(**apex**, 예: `example.com` 자체)에는 반드시 SOA와 NS가 있다(RFC 1034 §4.2.1 — 영역 최상위 노드의 NS·SOA).

```text
  example.com.  SOA  ...          <- apex에 필수
  example.com.  NS   ns1...       <- apex에 필수
  example.com.  CNAME lb.cdn...   <- 같은 이름에 다른 데이터가 있으므로 규칙 위반
```

- 그래서 apex에는 CNAME을 둘 수 없다.
- 우회는 표준이 아니라 **DNS 사업자 기능**이다.
  - Cloudflare "CNAME flattening": 사업자가 CNAME을 끝까지 따라가 최종 IP를 A/AAAA처럼 돌려준다.
  - AWS Route 53 alias 레코드: apex에서도 AWS 자원을 가리킬 수 있다.
  - 사업자를 옮기면 이 기능이 그대로 옮겨지지 않을 수 있다.

## 쓰이는 자료구조·알고리즘

- **도메인 트리 = 역순 라벨 트라이** — 이름을 `.`으로 자른 라벨을 **오른쪽부터** 키로 삼아 내려가는 트라이다.
  - `api.example.com` → [`com`, `example`, `api`] 순서로 간선을 따라간다.
  - 영역 경계(위임 지점)는 "여기부터는 다른 서버가 서브트리를 맡는다"는 표시다.
  - 재귀 해석기의 동작은 "캐시에 있는 **가장 깊은 조상**의 NS부터 시작해 내려간다"이다. 최장 접두사 매칭과 같은 모양의 "최장 접미사 매칭"이다.
  - 트라이 개념은 [트라이](../../data-structure/09-trie/2-summary.md) 참고.
- **캐시 = 해시 + 만료** — 키는 (이름, 타입, 클래스), 값은 RR 묶음과 만료 시각이다. 상세는 28번.
- **반복 탐색 + 재시도** — 한 서버가 응답하지 않으면 같은 영역의 다른 NS로 넘어간다. 스텁 해석기도 `resolv.conf`의 서버를 차례로 시도한다(timeout 기본 5초, attempts 기본 2, resolv.conf(5)).
- **메시지 압축** — 응답 안에서 반복되는 이름을 앞선 위치를 가리키는 포인터로 줄인다(RFC 1035 §4.1.4).

## 적용 — 풀어나가는 법

### 1. 앱과 같은 경로로 먼저, 그다음 DNS 자체를 본다

```bash
getent hosts api.example.com          # 앱과 같은 OS 해석 경로 (/etc/hosts + DNS, nsswitch 따름)
cat /etc/resolv.conf                  # 어느 재귀 해석기에 묻나, search·ndots

dig api.example.com A                 # 재귀 해석기에 질의 (기본 RD=1)
dig @8.8.8.8 api.example.com A        # 다른 해석기로 비교
dig +trace api.example.com A          # 루트부터 위임을 따라 반복 질의 (내가 재귀 해석기 역할)
dig @ns1.example.net api.example.com A +norecurse   # 권한 서버에 직접, 재귀 없이
dig +short example.com MX
dig api.example.com A +tcp            # TCP로 (UDP와 결과 비교)
```

- `dig` 출력에서 볼 곳: `status:`(RCODE), `flags:`(`qr aa rd ra`), ANSWER·AUTHORITY 절.
- `+trace`는 루트부터 위임 경로를 따라간다. 재귀는 자동으로 꺼진다(BIND dig 문서).

### 2. 코드 — 해석 실패를 구분한다

Java — OS 기본 해석기를 쓴다(JEP 418 "By default, InetAddress uses the operating system's native resolver").

```java
try {
    InetAddress[] addrs = InetAddress.getAllByName("api.example.com");
} catch (UnknownHostException e) {
    // "IP 주소를 알아낼 수 없다" — NXDOMAIN, SERVFAIL, 해석기 도달 불가가 모두 여기로 온다
    // 원인 구분은 같은 호스트에서 dig/getent로 한다
}
```

Node — `lookup`과 `resolve`는 경로가 다르다.

```js
const dns = require('node:dns').promises;

// OS 경로(getaddrinfo, /etc/hosts 포함). http.get·net.connect가 기본으로 쓰는 것
await dns.lookup('api.example.com');          // 실패: err.code === 'ENOTFOUND'(EAI_NONAME·EAI_NODATA) 또는 'EAI_AGAIN' 등

// DNS 프로토콜로 직접(c-ares). /etc/hosts를 보지 않는다
await dns.resolve4('api.example.com');        // 실패: err.code가 dns.NOTFOUND, dns.SERVFAIL 등
```

- `dns.lookup()`은 libuv 스레드풀에서 `getaddrinfo(3)`를 동기로 부른다. 느린 DNS가 스레드풀을 막아 파일 I/O까지 늦출 수 있다(Node `dns` 문서 "Implementation considerations").
- `ENOTFOUND`는 "이름이 없다"뿐 아니라 fd 부족 같은 다른 실패에도 나온다(Node `dns` 문서).

### 3. 레코드를 설계할 때

- apex(`example.com`)는 A/AAAA로 두거나, 사업자의 flattening·alias 기능을 쓴다. 서브도메인(`www`)은 CNAME을 쓸 수 있다.
- 권한 서버(NS)는 서로 다른 네트워크에 둘 이상 둔다. 하나가 죽어도 해석이 된다.
- 응답이 커지는 레코드(긴 TXT, 많은 A)는 TCP 53 경로가 열려 있는지 확인한다.

## 장애 시나리오와 대처

### 1. 권한 서버 장애 → `SERVFAIL`

- **현상**: 특정 도메인만 전부 해석이 안 된다. 다른 도메인은 된다.
- **보이는 형태**
  - `dig api.example.com` → `status: SERVFAIL`.
  - 확장 오류(EDE)를 지원하는 해석기면 `EDE: 22 (No Reachable Authority)`가 붙을 수 있다(RFC 8914 §4.23). 붙일지는 해석기 구현에 달렸다.
  - 앱: `UnknownHostException`, `dns.SERVFAIL` 코드(Node `resolve*`), `EAI_AGAIN`(getaddrinfo 일시 실패 — glibc는 SERVFAIL을 `TRY_AGAIN`으로, 그것을 `EAI_AGAIN`으로 바꾼다: `resolv/res_query.c`, `nss/getaddrinfo.c`).
- **원인**
  - 그 영역의 권한 서버에 모두 닿지 못했다. 재귀 해석기는 답을 만들 수 없어 SERVFAIL을 돌려준다.
  - 비슷한 원인: 부모 영역의 NS가 이미 없어진 서버를 가리킨다(lame delegation). DNSSEC 검증 실패도 SERVFAIL이 된다(검증 해석기는 RCODE 2를 돌려줘야 한다 MUST, RFC 4035 §5.5. EDE로는 6 "DNSSEC Bogus", RFC 8914 §4.7).
- **대처**
  - `dig +trace`로 어느 위임 단계에서 끊기는지 본다.
  - `dig @<각 NS> <이름> +norecurse`로 권한 서버를 하나씩 직접 친다.
  - 권한 서버를 서로 다른 네트워크·사업자에 분산한다.

### 2. apex에 CNAME을 못 건다

- **현상**: `example.com`을 CDN·LB 호스트명으로 향하게 하려고 CNAME을 만들었다. DNS 콘솔이 거부하거나, 존 파일 검사가 실패한다.
- **보이는 형태**: 콘솔 에러 "CNAME cannot coexist with other records" 류. BIND 등 존 로드 실패 메시지.
- **원인**: apex에는 SOA·NS가 반드시 있다. CNAME이 있는 이름에는 다른 데이터가 있으면 안 된다(RFC 1034 §3.6.2, RFC 2181 §10.1).
- **대처**
  - 사업자 기능(Cloudflare CNAME flattening, Route 53 alias)을 쓴다.
  - 또는 apex는 고정 IP(A/AAAA)로 두고 `www`만 CNAME으로 둔 뒤, apex에서 `www`로 HTTP 리다이렉트한다.

### 3. 해석기가 없는 컨테이너 → `UnknownHostException`

- **현상**: 같은 이미지가 로컬 도커에서는 되는데, 특정 런타임·네트워크 설정에서만 외부 이름을 못 찾는다. IP로 직접 접속하면 된다.
- **보이는 형태**
  - Java `java.net.UnknownHostException: api.example.com`, Node `getaddrinfo EAI_AGAIN`(해석기가 답을 못 줌 — 이름이 없다는 `ENOTFOUND`가 아니다), `curl: (6) Could not resolve host`.
  - 컨테이너 안 `/etc/resolv.conf`가 비었거나, 닿지 않는 주소를 가리킨다.
- **원인**
  - `resolv.conf`에 nameserver가 없으면 glibc는 **로컬 머신의 네임 서버**를 쓴다(resolv.conf(5)). 컨테이너 안에는 그런 서버가 없다.
  - 네트워크 격리로 설정된 해석기 주소에 UDP/TCP 53이 막혔다.
- **대처**
  - 컨테이너 안에서 `cat /etc/resolv.conf`, `getent hosts <이름>`, `dig`를 차례로 친다.
  - 런타임·오케스트레이터의 DNS 설정(도커 `--dns`, 쿠버네티스 `dnsPolicy`/`dnsConfig`)을 확인한다.

### 4. 큰 응답만 실패 — TCP 53이 막혔다

- **현상**: 대부분의 이름은 되는데, TXT가 긴 이름이나 레코드가 많은 이름만 가끔 실패한다.
- **보이는 형태**
  - `dig`가 `;; Truncated, retrying in TCP mode.`를 찍은 뒤 타임아웃(`no servers could be reached` 류)으로 끝난다(BIND `bin/dig/dighost.c`).
  - `dig +tcp`만 실패한다.
- **원인**: UDP 응답이 잘려 TC 비트가 켜졌다(RFC 1035 §4.2.1). 클라이언트가 TCP로 다시 물었는데(RFC 7766 §4), 방화벽이 TCP 53을 막았다. DNS 구현은 TCP를 지원해야 한다(MUST, RFC 7766 §5). 그런데 네트워크 정책이 이를 막은 것이다.
- **대처**: 해석기·권한 서버 경로에서 TCP 53을 허용한다. 레코드 크기를 줄이는 것은 보조 수단이다.

### 5. 위임 불일치 — 어떤 해석기에선 되고 어떤 해석기에선 안 된다

- **현상**: DNS 사업자를 옮긴 뒤 일부 사용자만 옛 IP로 가거나 해석에 실패한다.
- **보이는 형태**: `dig @8.8.8.8`과 `dig @1.1.1.1`의 결과가 다르다. `dig +trace`의 TLD 단계 NS와 새 사업자의 NS가 다르다.
- **원인**
  - 등록기관(레지스트라)의 NS 변경이 TLD에 반영되기 전이다.
  - 또는 옛 NS 정보가 해석기 캐시에 남아 있다. NS 레코드에도 TTL이 있다(28번).
- **대처**
  - 옮기기 전에 새 권한 서버에 같은 데이터를 먼저 채운다.
  - 옛 서버를 옛 NS TTL이 지날 때까지 유지한다.
  - `+trace`로 TLD가 주는 NS를 확인한다.

## 핵심 문장

- DNS는 이름 나무를 영역으로 쪼개 위임한 분산 DB다. 루트는 TLD를, TLD는 권한 서버를 가리킬 뿐이다.
- 앱의 스텁 해석기는 재귀 해석기에 재귀 질의(RD=1)를 하고, 재귀 해석기는 루트→TLD→권한 서버로 반복 질의하며 referral을 따라 내려간다.
- `NXDOMAIN`은 "그 이름이 없다", `SERVFAIL`은 "답을 만들 수 없었다"다. 후자는 권한 서버 장애·위임 오류·DNSSEC 실패를 의심한다.
- CNAME이 있는 이름에는 다른 데이터가 올 수 없고, apex에는 SOA·NS가 있으므로 apex CNAME은 표준상 불가능하다.
- Java에서는 해석 실패가 `UnknownHostException` 하나로 뭉개진다. Node `lookup`은 `ENOTFOUND`(이름·레코드 없음 등)와 `EAI_AGAIN`(SERVFAIL·해석기 무응답)으로 나뉘지만, `ENOTFOUND`도 원인을 다 말해 주지 않는다. 원인은 같은 호스트에서 `getent`→`dig`→`dig +trace` 순으로 가른다.

## 관련 주제·근거

- 선행: [14-udp](../14-udp/2-summary.md) — DNS의 기본 전송.
- 후속·연결
  - [28-dns-caching-and-ttl](../28-dns-caching-and-ttl/2-summary.md) — TTL·부정 캐시·JVM DNS 캐시·`ndots`.
  - [51-email-delivery-and-authentication](../51-email-delivery-and-authentication/2-summary.md) — MX·TXT(SPF·DKIM·DMARC).
  - [26-packet-journey](../26-packet-journey/2-summary.md) — 요청 여행의 첫 구간
  - [49-what-happens-when-url](../49-what-happens-when-url/2-summary.md) · [52-network-symptom-index](../52-network-symptom-index/2-summary.md)(`SERVFAIL`·`NXDOMAIN`)
  - [data-structure/09-trie](../../data-structure/09-trie/2-summary.md) — 역순 라벨 트라이
- RFC
  - RFC 1034 "Domain Names — Concepts and Facilities" — §2.3(재귀·반복 개요), §3.6.2(CNAME), §4.2.1(영역 구성·apex의 NS·SOA·glue), §4.3.1(재귀/비재귀, RD·RA) <https://www.rfc-editor.org/rfc/rfc1034>
  - RFC 1035 "Domain Names — Implementation and Specification" — §2.3.4(크기 제한), §3.2.2(TYPE 값), §4.1.1(헤더·RCODE), §4.1.4(메시지 압축), §4.2.1(UDP 512·TC) <https://www.rfc-editor.org/rfc/rfc1035>
  - RFC 2181 §10.1 — CNAME 이름에는 다른 데이터 불가 <https://www.rfc-editor.org/rfc/rfc2181>
  - RFC 3596 — AAAA(타입 28) <https://www.rfc-editor.org/rfc/rfc3596>
  - RFC 6891 — EDNS(0) <https://www.rfc-editor.org/rfc/rfc6891>
  - RFC 7766 §4 — TC를 받으면 TCP로 재질의 · §5 — UDP·TCP 모두 지원 MUST <https://www.rfc-editor.org/rfc/rfc7766>
  - RFC 4035 §3.2.2 CD 비트 · §5.5 검증 실패 시 RCODE 2(SERVFAIL) <https://www.rfc-editor.org/rfc/rfc4035>
  - RFC 8914 — Extended DNS Errors(§4.7 DNSSEC Bogus, §4.23 No Reachable Authority) <https://www.rfc-editor.org/rfc/rfc8914>
- IANA "Root Servers" — 13개 이름, 루트 힌트 <https://www.iana.org/domains/root/servers>
- resolv.conf(5) — nameserver 최대 3, 없으면 로컬 머신, `timeout`(5)·`attempts`(2) <https://man7.org/linux/man-pages/man5/resolv.conf.5.html>
- BIND 9 `dig` 매뉴얼 — `+trace`, `+norecurse`, `+tcp`, `+short` <https://bind9.readthedocs.io/en/latest/manpages.html>
- Node.js `dns` — `lookup` vs `resolve*`, 스레드풀, `ENOTFOUND` <https://nodejs.org/api/dns.html>
- Node `lib/internal/errors.js` `DNSException` — `EAI_NODATA`·`EAI_NONAME`만 `ENOTFOUND`로, 나머지(`EAI_AGAIN` 등)는 원래 이름 <https://github.com/nodejs/node/blob/main/lib/internal/errors.js>
- JEP 418 — `InetAddress` 기본은 OS 네이티브 해석기 <https://openjdk.org/jeps/418>
- glibc `resolv/res_query.c`(SERVFAIL → `TRY_AGAIN`) · `nss/getaddrinfo.c`(`TRY_AGAIN` → `EAI_AGAIN`) <https://sourceware.org/git/?p=glibc.git;a=tree;f=resolv>
- BIND `bin/dig/dighost.c` — "Truncated, retrying in TCP mode." <https://gitlab.isc.org/isc-projects/bind9/-/blob/main/bin/dig/dighost.c>
- Cloudflare "CNAME flattening" <https://developers.cloudflare.com/dns/cname-flattening/> · AWS Route 53 "Choosing between alias and non-alias records" <https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html>
- Kurose & Ross 2.4 "DNS — The Internet's Directory Service"
