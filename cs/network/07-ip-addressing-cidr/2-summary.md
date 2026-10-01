# network/07-ip-addressing-cidr — IP 주소는 어떻게 "망 부분"과 "호스트 부분"으로 나뉘고, 대역은 어떻게 설계하나 — 정리 (힌트)

## 해결하는 문제

MAC 주소는 "어느 장비인가"만 말해 준다.\
그 장비가 지구 어디에 있는지는 말해 주지 않는다.\
전 세계 장비 수십억 대의 MAC을 라우터가 하나하나 외울 수는 없다.

그래서 IP 주소는 **위치를 담은 계층형 주소**다.\
앞부분은 "어느 망인가", 뒷부분은 "그 망 안의 몇 번째 호스트인가"를 뜻한다.

```text
  우편 주소:   서울시 강남구 테헤란로 | 123
               (어느 동네 = 망)        (그 동네 안 집 = 호스트)

  IP 주소:     192.168.10 | .37      (/24일 때)
               망 부분       호스트 부분
```

쉬운 예: 택배 기사는 "서울시 강남구"까지만 보고 강남 물류센터로 보낸다.\
번지는 강남 센터가 알아서 찾는다.

똑같은 구조다.\
멀리 있는 라우터는 망 부분(프리픽스)만 보고 방향을 정한다.\
호스트 부분은 마지막 망에 도착해서야 쓴다.

실무에서 이 지식이 필요한 순간
- 클라우드 VPC·서브넷의 CIDR을 정한다. 한번 정하면 바꾸기 어렵다.
- 방화벽·보안 그룹·허용 목록에 `10.0.0.0/8` 같은 대역을 적는다.
- 사내망·VPN·도커 네트워크의 대역이 겹쳐 "특정 대역만 안 되는" 장애를 푼다.
- SSRF 방어에서 "이 주소가 내부 주소인가"를 판정한다.

## 동작·원리

### IPv4 주소 = 32비트 정수

```text
  192      .168      .10       .37
  11000000  10101000  00001010  00100101     <- 32비트
  |------------ 24비트 ------------|-- 8 --|
            망(프리픽스)               호스트

  /24 마스크: 11111111 11111111 11111111 00000000  = 255.255.255.0
```

- 점 네 개로 나눈 표기(dotted decimal)는 사람이 읽기 쉽게 쓴 것이다. 실제 값은 32비트 정수 하나다.
- `/24`는 "앞 24비트가 망 부분"이라는 뜻이다(RFC 4632 §3.1).
  - *프리픽스(prefix)*: 주소의 앞부분 중 망을 뜻하는 비트들이다. `/n`의 n이 그 길이(0~32)다.
  - *서브넷 마스크*: 프리픽스 길이만큼 1, 나머지는 0인 32비트 값이다. `/24` = `255.255.255.0`이다.
- 망 주소는 **주소 AND 마스크**로 구한다.

```text
  주소    11000000.10101000.00001010.00100101   192.168.10.37
  마스크  11111111.11111111.11111111.00000000   255.255.255.0
  AND   = 11000000.10101000.00001010.00000000   192.168.10.0   <- 망 주소
```

### 한 서브넷 안의 주소들

```text
  192.168.10.0/24  (2^(32-24) = 256개)

  192.168.10.0       망 주소 (호스트 부분 비트가 모두 0)
  192.168.10.1  ...
  ...                호스트에 줄 수 있는 주소
  192.168.10.254
  192.168.10.255     브로드캐스트 주소 (호스트 부분 비트가 모두 1)
```

- `/n` 블록에는 2^(32-n)개의 주소가 있다.
- 전통적으로 맨 앞(망 주소)과 맨 뒤(브로드캐스트 주소)는 호스트에 주지 않는다. 그래서 흔히 2^(32-n) − 2개를 쓴다.
- 예외가 있다.
  - `/31`: 점대점 링크에서는 두 주소를 모두 호스트에 쓸 수 있다(RFC 3021).
  - `/32`: 주소 하나다. "이 호스트 하나"를 가리키는 경로·규칙에 쓴다.
  - 클라우드는 더 뺀다. AWS는 서브넷마다 앞 4개와 마지막 1개, 총 5개를 예약한다. 그래서 `/28`(16개)에서 실제 쓸 수 있는 주소는 11개다(AWS "Subnet CIDR blocks").

서브넷 나누기 — 비트를 하나 더 빌리면 반으로 쪼개진다

```text
  10.0.0.0/24  (256개)
     |
     +-- 10.0.0.0/25    10.0.0.0   ~ 10.0.0.127   (128개)
     +-- 10.0.0.128/25  10.0.0.128 ~ 10.0.0.255   (128개)
```

- 이 예는 AWS 문서의 서브넷 분할 예시와 같다.
- 블록은 항상 크기(2의 거듭제곱)의 배수에서 시작한다. `10.0.0.64/25`는 올바른 블록이 아니다. 64는 128의 배수가 아니기 때문이다.

### 클래스에서 CIDR로 — 크기를 자유롭게, 경로는 합쳐서

```text
  예전(클래스풀):  A = /8,  B = /16,  C = /24   세 가지 크기뿐
  CIDR(클래스리스): /0 ~ /32 어떤 길이든

  집약(aggregation) 예
    203.0.112.0/24 ┐
    203.0.113.0/24 │  연속된 /24 4개      ->  203.0.112.0/22 한 줄로 광고
    203.0.114.0/24 │  (앞 22비트가 같다)
    203.0.115.0/24 ┘
```

- 예전에는 A·B·C 세 크기만 있었다. 1,000대가 필요한 조직이 B(65,536개)를 받아 낭비했다.
- CIDR은 프리픽스 길이를 명시해 2의 거듭제곱 크기 블록을 자유롭게 준다(RFC 4632 §3.1).
- 연속된 블록은 짧은 프리픽스 하나로 합쳐 광고한다. 라우팅 테이블이 작아진다(RFC 4632 §4).
  - *CIDR(Classless Inter-Domain Routing)*: 클래스 대신 프리픽스 길이로 주소 블록을 나누고 합치는 방식이다.
  - *집약(aggregation)*: 여러 작은 블록을 공통 프리픽스 하나로 묶어 경로 한 줄로 표현하는 것이다.
- 위 예시 중 `203.0.113.0/24`는 문서용 예약 대역(TEST-NET-3, RFC 6890 표)이다. 나머지 셋은 설명을 위한 가상의 값이다(예시).

### 특별한 대역 — 외워 둘 것

```text
  대역               뜻                              근거
  10.0.0.0/8         사설                             RFC 1918
  172.16.0.0/12      사설 (172.16 ~ 172.31)            RFC 1918
  192.168.0.0/16     사설                             RFC 1918
  100.64.0.0/10      공유 주소 (통신사 CGN용)            RFC 6598
  127.0.0.0/8        루프백 (자기 자신)                  RFC 6890
  169.254.0.0/16     링크 로컬 (DHCP 실패 시 자동 할당 가능) RFC 3927
  0.0.0.0/8          "이 네트워크" (출발지로만)           RFC 6890
  255.255.255.255/32 제한 브로드캐스트                   RFC 6890
  192.0.2.0/24       문서용 (TEST-NET-1)                RFC 6890
```

- 사설 대역은 인터넷에서 의미가 없다. 그래서 조직 밖으로 경로를 광고하지 않고, 받으면 걸러야 한다(RFC 1918 §3).
- 사설 대역은 누구나 쓰므로 **조직끼리 합치거나 VPN으로 이으면 겹치기 쉽다.** 장애 시나리오 1·2의 뿌리다.
- `172.16.0.0/12`는 `172.16`부터 `172.31`까지다. 도커 기본 풀의 `172.17.0.0/16`도 이 안에 있다.
- 링크 로컬 자동 할당은 이를 구현·켠 OS만 한다. 고르는 범위는 `169.254.1.0`~`169.254.254.255`다. 앞뒤 256개는 고르면 안 된다(MUST NOT, RFC 3927 §2.1).
- `0.0.0.0/8`은 RFC상 출발지 전용이다. 그런데 리눅스는 목적지 `0.0.0.0`으로 연결하면 루프백(자기 자신)으로 보낸다(`net/ipv4/route.c` `ip_route_output_key_hash_rcu()`). 그래서 내부 주소 차단 목록에 넣어야 한다.
- AWS EC2는 링크 로컬 주소 `169.254.169.254`를 인스턴스 메타데이터 주소로 쓴다(AWS "Access instance metadata"). SSRF의 단골 표적이다.

### IPv6 — 128비트, 표기 규칙부터

```text
  2001:0db8:0000:0000:0000:ff00:0042:8329     전체 (16비트 x 8그룹)
  2001:db8:0:0:0:ff00:42:8329                 각 그룹 앞자리 0 생략
  2001:db8::ff00:42:8329                      연속된 0 그룹을 :: 로 한 번만 생략
  |---- 보통 앞 64비트 ----|---- 인터페이스 ID 64비트 ----|
```

- "`::`"는 주소 안에서 한 번만 쓸 수 있다(RFC 4291 §2.2). 두 번 쓰면 몇 그룹이 생략됐는지 알 수 없다.
- 주요 종류(RFC 4291 §2.4, RFC 4193)

```text
  ::/128      지정 안 됨 (unspecified)
  ::1/128     루프백
  fe80::/10   링크 로컬 (모든 인터페이스가 자동으로 가진다)
  fc00::/7    고유 로컬 ULA (IPv6판 사설 대역에 해당)
  ff00::/8    멀티캐스트
  나머지       글로벌 유니캐스트
  ::ffff:0:0/96  IPv4-mapped (IPv4 주소를 IPv6 소켓에서 표현)
```

- IPv6에는 **브로드캐스트 주소가 없다.** 그 역할은 멀티캐스트가 맡는다(RFC 4291 §2).
- 유니캐스트 주소는(`000`으로 시작하는 것 제외) 인터페이스 ID가 64비트여야 한다(RFC 4291 §2.5.1). 그래서 LAN 서브넷은 보통 `/64`다.
  - *인터페이스 ID*: 주소 뒷부분으로, 그 링크 안에서 인터페이스 하나를 가리키는 값이다.
  - *IPv4-mapped 주소*: `::ffff:10.0.0.1`처럼 IPv4 주소를 IPv6 형식에 담은 것이다(RFC 4291 §2.5.5.2). 듀얼 스택 서버 로그에서 자주 보인다.

## 쓰이는 자료구조·알고리즘

- **비트 마스크** — 망 주소 = `addr & mask`, 포함 판정 = `(addr & mask) == net`이다. 정수 비트 연산 한두 번이면 끝난다. 개념: [비트 조작](../../algorithm/29-bit-manipulation/2-summary.md).
- **정렬된 구간** — CIDR 블록은 `[시작, 시작 + 2^(32-n))` 구간이다.
  - 두 CIDR은 "완전히 따로"이거나 "한쪽이 다른 쪽을 포함"하거나 둘 중 하나다. 부분 겹침은 없다. 블록이 크기의 배수에서 시작하기 때문이다.
  - 그래서 겹침 검사는 "짧은 프리픽스 기준으로 둘의 망 주소가 같은가"로 끝난다.
- **트라이(접두사 트리)** — 대역 목록에서 "이 주소를 포함하는 가장 긴 프리픽스"를 찾는 것은 라우팅의 핵심 연산이다. 다음 노트 [08](../08-routing-and-longest-prefix-match/2-summary.md)과 [radix 트라이](../../data-structure/20-radix-trie/2-summary.md)에서 다룬다.

## 적용 — 풀어나가는 법

### 1. 포함·겹침 판정 (Java)

```java
import java.net.InetAddress;

record Cidr(int net, int len) {          // IPv4 전용 (IPv6는 128비트라 long 두 개나 BigInteger가 필요)
    static Cidr parse(String s) throws Exception {
        String[] p = s.split("/");
        int len = Integer.parseInt(p[1]);
        return new Cidr(toInt(p[0]) & mask(len), len);   // 망 주소로 정규화
    }
    static int mask(int len) { return len == 0 ? 0 : -1 << (32 - len); }
    static int toInt(String ip) throws Exception {
        byte[] b = InetAddress.getByName(ip).getAddress();   // 숫자 IP만 넣는다 (이름이면 DNS 조회가 일어난다)
        return (b[0] & 0xff) << 24 | (b[1] & 0xff) << 16 | (b[2] & 0xff) << 8 | (b[3] & 0xff);
    }
    boolean contains(int ip)   { return (ip & mask(len)) == net; }
    boolean overlaps(Cidr o)   {                     // 짧은 쪽 마스크로 비교
        int m = mask(Math.min(len, o.len));
        return (net & m) == (o.net & m);
    }
}
// Cidr.parse("172.16.0.0/12").overlaps(Cidr.parse("172.17.0.0/16"))  -> true
```

- `parse`에서 망 주소로 정규화하는 줄이 중요하다. `10.1.2.3/16`을 적어도 `10.1.0.0/16`으로 바뀐다. AWS도 CIDR을 이렇게 정규형으로 바꾼다(AWS "Subnet CIDR blocks").

### 2. 허용·차단 목록 (Node.js)

```js
const net = require('node:net');
const internal = new net.BlockList();
internal.addSubnet('10.0.0.0', 8);
internal.addSubnet('172.16.0.0', 12);
internal.addSubnet('192.168.0.0', 16);
internal.addSubnet('127.0.0.0', 8);
internal.addSubnet('169.254.0.0', 16);          // 링크 로컬·메타데이터
internal.addSubnet('100.64.0.0', 10);           // 공유 주소(CGN)
internal.addSubnet('0.0.0.0', 8);               // 리눅스는 목적지 0.0.0.0을 자기 자신으로 보낸다
internal.addAddress('::', 'ipv6');              // IPv6 unspecified
internal.addSubnet('::1', 128, 'ipv6');
internal.addSubnet('fc00::', 7, 'ipv6');
internal.addSubnet('fe80::', 10, 'ipv6');

internal.check('172.17.0.2');                    // true
internal.check('::ffff:10.0.0.1', 'ipv6');       // IPv4-mapped도 IPv4 규칙에 맞춰 판정
```

- Node 문서의 예시가 IPv4-mapped IPv6 주소도 IPv4 규칙으로 판정됨을 보여 준다(`net.BlockList`, v15.0.0+).
- SSRF 방어라면 "이름 → 주소 해석 뒤의 실제 주소"를 검사해야 한다. 이름만 검사하면 DNS rebinding으로 우회된다(security 영역).

### 3. 호스트에서 확인하는 명령

```bash
ip -br addr                      # 인터페이스별 주소/프리픽스 한눈에
ip -4 route                      # "10.0.1.0/24 dev eth0 proto kernel scope link" = 직접 연결된 서브넷
ip route get 172.17.5.10         # 이 주소로 가는 패킷이 실제로 어느 인터페이스로 나가나
docker network inspect bridge --format '{{json .IPAM.Config}}'   # 도커 기본 브리지 대역
```

### 4. 대역을 설계할 때

1. 사내망·VPN·다른 VPC·다른 환경(dev/stage/prod)이 쓰는 대역을 **먼저 모은다**.
2. 겹치지 않는 블록을 고른다. 나중에 VPC 피어링·VPN으로 이을 가능성까지 본다.
3. 서브넷은 넉넉히 잡는다. 클라우드 예약분(AWS 5개)과 오토스케일링 최대치를 더한다.
4. 도커·쿠버네티스 같은 도구의 기본 대역이 사내 대역과 겹치는지 확인한다.

## 장애 시나리오와 대처

### 1. VPC 피어링을 만들 수 없다 — CIDR 겹침

- **현상**: 두 VPC를 이으려는데 피어링 생성이 거절된다. 또는 VPN으로 이은 두 망 사이에서 일부 주소만 안 된다.
- **보이는 형태**: 피어링 요청 실패. 억지로 이은 경우 목적지 주소가 "내 VPC 안"으로 해석되어 패킷이 밖으로 나가지 않는다.
- **원인**
  - AWS는 IPv4·IPv6 CIDR이 같거나 겹치는 VPC끼리 피어링을 만들 수 없다.
  - VPC에 CIDR이 여러 개면 **하나라도** 겹치면 안 된다. 겹치지 않는 대역만 쓸 생각이어도 마찬가지다(AWS "How VPC peering connections work"의 "Overlapping CIDR blocks").
  - 근본적으로, 같은 주소가 두 곳에 있으면 라우터는 어느 쪽으로 보낼지 정할 수 없다.
- **대처**
  - 처음부터 조직 전체 대역 계획(IPAM)을 세운다.
  - 이미 겹쳤다면 한쪽을 재번호(re-IP)하거나, NAT로 주소를 바꿔 잇는다. 둘 다 비싸다.

### 2. 도커를 깐 뒤 사내 특정 대역만 접속이 안 된다

- **현상**: 개발 서버에 도커를 설치한 뒤, 사내의 `172.17.x.x` 대역 서버(예시)에만 접속이 안 된다. 다른 대역은 된다.
- **보이는 형태**
  - `curl`이 타임아웃난다.
  - `ip route get 172.17.5.10` 결과가 사내 게이트웨이가 아니라 `dev docker0`이다.
  - `ip route`에 `172.17.0.0/16 dev docker0`이 보인다.
- **원인**
  - 도커는 기본 주소 풀의 첫 대역 `172.17.0.0/16`을 쓴다(Docker "Networking overview" 기본 풀).
  - 이 경로는 기본 경로(`0.0.0.0/0`)보다 프리픽스가 길다. 그래서 사내 서버로 가야 할 패킷이 도커 브리지로 빨려 들어간다(최장 접두사 매칭, 08번).
- **대처**
  - `/etc/docker/daemon.json`의 `bip`(기본 브리지 대역)와 `default-address-pools`(새 네트워크 대역)를 사내 대역과 겹치지 않게 바꾸고 도커를 재시작한다(Docker bridge 문서).
  - 새 개발자 PC·CI 러너 이미지에 이 설정을 기본으로 넣는다.

### 3. 서브넷 주소가 바닥난다

- **현상**: 오토스케일링이 새 인스턴스를 못 띄운다. 파드·컨테이너가 주소를 못 받는다.
- **보이는 형태**: 인스턴스 시작이 실패한다. AWS EC2 API는 `InsufficientFreeAddressesInSubnet`("The specified subnet does not contain enough free private IP addresses") 에러를 돌려준다(EC2 API "Error codes"). 서브넷의 남은 주소 수(`AvailableIpAddressCount`)가 0이다.
- **원인**: 서브넷을 작게 잡았다. `/28`은 16개인데 AWS가 5개를 예약하므로 11개뿐이다. 워크로드마다 주소를 하나씩 쓰는 네트워크 방식이면 더 빨리 준다.
- **대처**
  - 새 서브넷을 추가하거나 VPC에 보조 CIDR을 붙인다.
  - 처음 설계할 때 최대 규모 × 여유분으로 잡는다. 서브넷 CIDR은 만든 뒤 바꾸기 어렵다.

### 4. 허용 목록·내부 주소 판정이 새어 나간다

- **현상**: "내부 주소면 거절" 검사를 넣었는데도 내부 서비스가 호출된다.
- **보이는 형태**: 로그에 `::ffff:127.0.0.1`, `100.64.x.x`, `169.254.169.254` 같은 주소가 찍힌다.
- **원인**
  - 목록이 불완전하다. `10/8`·`172.16/12`·`192.168/16`만 막고 루프백·링크 로컬·CGN·`0.0.0.0/8`·IPv6(`::`, `::1`, `fc00::/7`, `fe80::/10`)·IPv4-mapped를 빠뜨렸다.
  - 문자열 비교로 검사했다. `172.16.0.0/12`를 "172.16."으로 시작하는지로 검사하면 `172.20.1.1`을 놓친다.
- **대처**
  - 문자열이 아니라 **비트 마스크로** 판정한다. 라이브러리(`net.BlockList` 등)를 쓴다.
  - IPv6와 IPv4-mapped를 함께 처리한다.
  - 판정은 DNS 해석 뒤 실제로 연결할 주소에 한다.

## 핵심 문장

- IP 주소는 "망 부분 + 호스트 부분"이고, `/n`은 앞 n비트가 망이라는 뜻이다. 망 주소는 `주소 AND 마스크`다.
- `/n` 블록은 2^(32-n)개이고 크기의 배수에서 시작한다. 그래서 두 CIDR은 따로거나 포함 관계이지, 부분만 겹치지는 않는다.
- CIDR은 크기를 자유롭게 주고, 연속 블록을 합쳐 경로 수를 줄인다.
- 사설 대역(10/8, 172.16/12, 192.168/16)은 누구나 쓰므로 망을 이을 때 겹치기 쉽다. 대역 계획은 처음에 한다.
- IPv6는 128비트이고 브로드캐스트가 없다. LAN은 보통 `/64`이고, `::`는 한 번만 쓴다.

## 관련 주제·근거

- 선행: [01-layer-map-osi-tcpip](../01-layer-map-osi-tcpip/2-summary.md)
- 후속·연결
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — 프리픽스로 경로를 고르는 방법(도커 대역 충돌의 메커니즘)
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — 사설 주소가 인터넷으로 나가는 법, 겹친 대역을 NAT로 잇기
  - [12-dhcp](../12-dhcp/2-summary.md) — 주소 자동 할당, 실패 시 `169.254.x.x`
  - [06-switching-and-vlan](../06-switching-and-vlan/2-summary.md) — VLAN 하나에 서브넷 하나
  - security 영역 `22-ssrf` — 내부 주소 판정. 미작성([security 영역 표](../../security/README.md))
  - [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md) · [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md)
- RFC
  - RFC 791 — IPv4 <https://www.rfc-editor.org/rfc/rfc791>
  - RFC 4632 — CIDR. §3.1 프리픽스 표기, §4 집약 <https://www.rfc-editor.org/rfc/rfc4632>
  - RFC 1918 — 사설 대역 3개, §3 외부로 경로를 광고하지 않음 <https://www.rfc-editor.org/rfc/rfc1918>
  - RFC 6598 — `100.64.0.0/10` 공유 주소 <https://www.rfc-editor.org/rfc/rfc6598>
  - RFC 3927 — `169.254/16` 링크 로컬, §2.1 선택 범위 <https://www.rfc-editor.org/rfc/rfc3927>
  - RFC 6890 — 특수 목적 주소 레지스트리(0/8, 127/8, 192.0.2.0/24·203.0.113.0/24 문서용, 255.255.255.255) <https://www.rfc-editor.org/rfc/rfc6890>
  - RFC 3021 — `/31` 점대점 링크 <https://www.rfc-editor.org/rfc/rfc3021>
  - RFC 8200 — IPv6 <https://www.rfc-editor.org/rfc/rfc8200>
  - RFC 4291 — IPv6 주소 구조. §2 브로드캐스트 없음, §2.2 표기(`::` 한 번), §2.4 종류 표, §2.5.1 64비트 인터페이스 ID, §2.5.5.2 IPv4-mapped <https://www.rfc-editor.org/rfc/rfc4291>
  - RFC 4193 — `fc00::/7` 고유 로컬 주소 <https://www.rfc-editor.org/rfc/rfc4193>
- AWS 문서
  - EC2 API "Error codes" — `InsufficientFreeAddressesInSubnet` <https://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html>
  - "Subnet CIDR blocks" — 서브넷 `/16`~`/28`, 예약 주소 5개, 정규형 변환(`100.68.0.18/18` → `100.68.0.0/18`) <https://docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html>
  - "How VPC peering connections work" — 겹치는 CIDR 불가("Overlapping CIDR blocks" 항목) <https://docs.aws.amazon.com/vpc/latest/peering/vpc-peering-basics.html>
  - "Access instance metadata" — `169.254.169.254` <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html>
- Docker 문서
  - "Networking overview" — 기본 주소 풀(`172.17.0.0/16`부터) <https://docs.docker.com/engine/network/>
  - "Bridge network driver" — `daemon.json`의 `bip`, `fixed-cidr` <https://docs.docker.com/engine/network/drivers/bridge/>
- Node.js `net.BlockList` <https://nodejs.org/api/net.html>
- Linux `net/ipv4/route.c` `ip_route_output_key_hash_rcu()` — 목적지 0이면 루프백으로 보냄 <https://github.com/torvalds/linux/blob/master/net/ipv4/route.c>
- 교재: Kurose & Ross 8판 4.3 "The Internet Protocol (IP)"(IPv4 주소·CIDR, IPv6)
