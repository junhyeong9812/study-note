# network/05-arp — ARP: IP 주소로 MAC 주소 찾기, ARP 캐시, gratuitous ARP — 정리 (힌트)

## 해결하는 문제

IP 계층은 "다음 홉은 10.0.0.1"까지 정한다.\
그런데 이더넷 프레임을 만들려면 목적지 **MAC 주소**가 필요하다([04-ethernet-and-mac](../04-ethernet-and-mac/2-summary.md)).\
IP 주소와 MAC 주소는 서로 관계없이 정해진다. 그래서 "이 IP를 쓰는 장비의 MAC은 무엇인가"를 물어볼 방법이 필요하다.\
IPv4에서 이 일을 하는 것이 ARP다(RFC 826).

  - *ARP(Address Resolution Protocol)*: 같은 링크 안에서 IPv4 주소를 MAC 주소로 바꿔 주는 프로토콜. IPv6는 같은 일을 NDP(RFC 4861)로 한다.

```text
  IP 계층: "10.0.0.20으로 보내라"
  링크 계층: "10.0.0.20의 MAC이 뭐지?"
         |
         +-- ARP 캐시에 있다   --> 바로 프레임 전송
         +-- 없다             --> 링크 전체에 "10.0.0.20 누구야?" 방송 -> 답을 받아 캐시에 저장
```

쉬운 예: 사무실에서 "김민수 씨 자리 어디예요?"라고 크게 묻는다.\
김민수 씨가 "여기요" 하고 손을 든다.\
다음부터는 기억해 두고 바로 간다. 김민수 씨가 자리를 옮기면 기억이 틀린다.

똑같은 구조다.\
ARP 요청은 모두에게 묻고(브로드캐스트), 대답은 당사자가 한다. 기억은 캐시다.

실무 예:
- 이중화된 서버의 가상 IP(VIP)가 대기 서버로 넘어갔다.
- 그런데 같은 망의 장비들이 **예전 MAC**을 기억하고 있어서, 한동안 죽은 서버로 계속 보낸다.
- 그래서 새로 VIP를 가진 서버는 "이 IP는 이제 내 MAC이다"라고 알린다. 이것이 gratuitous ARP다.

## 동작·원리

### 누구의 MAC을 찾나 — 목적지가 아니라 "다음 홉"

```text
  내 주소 10.0.0.5/24, 기본 게이트웨이 10.0.0.1

  목적지 10.0.0.20 (같은 서브넷)  --> ARP로 10.0.0.20의 MAC을 찾는다
  목적지 8.8.8.8   (다른 망)      --> ARP로 게이트웨이 10.0.0.1의 MAC을 찾는다
                                     (IP 헤더의 목적지는 8.8.8.8 그대로)
```

- ARP는 **같은 링크 안**에서만 쓴다. 다른 망의 호스트 MAC은 알 필요도, 알 방법도 없다.
- 다른 망으로 갈 때는 라우팅 테이블이 고른 **다음 홉(게이트웨이)의 MAC**으로 프레임을 보낸다(K&R 6.4.1).
- 그래서 "게이트웨이의 ARP 항목이 틀리면" 외부로 가는 트래픽 전체가 죽는다.

### 요청과 응답 — 패킷 교환도

```text
  A (10.0.0.5, MAC aa)                 링크의 모든 장비             B (10.0.0.20, MAC bb)

  --- 요청 (브로드캐스트) ---------------------------------------------------->
      이더넷 목적지 = FF-FF-FF-FF-FF-FF, EtherType 0x0806
      op=1(request)  sha=aa  spa=10.0.0.5  tha=00..00  tpa=10.0.0.20
                                       (C, D도 받지만 tpa가 자기가 아니라 답하지 않음)

  <-------------------------------------------------- 응답 (유니캐스트) -----
      이더넷 목적지 = aa
      op=2(reply)    sha=bb  spa=10.0.0.20  tha=aa  tpa=10.0.0.5

  A: 캐시에 10.0.0.20 -> bb 저장, 기다리던 IP 패킷을 bb로 전송
  B: 요청을 받으면서 이미 10.0.0.5 -> aa 도 저장했다 (RFC 826 수신 알고리즘)
```

- 요청은 브로드캐스트, 응답은 보통 유니캐스트다(RFC 5227이 이 관례를 설명한다).
- ARP 패킷은 이더넷 위에 바로 실린다. EtherType은 0x0806이다(RFC 7042). IP 패킷이 아니다.

### ARP 패킷 형식

```text
  필드        크기(이더넷·IPv4)   뜻
  ar$hrd      2                 하드웨어 종류 (이더넷 = 1)
  ar$pro      2                 프로토콜 종류 (IPv4 = 0x0800)
  ar$hln      1                 하드웨어 주소 길이 (6)
  ar$pln      1                 프로토콜 주소 길이 (4)
  ar$op       2                 1 = request, 2 = reply
  ar$sha      6                 보낸 쪽 MAC
  ar$spa      4                 보낸 쪽 IP
  ar$tha      6                 대상 MAC (요청에서는 모름)
  ar$tpa      4                 대상 IP
                                합계 28바이트
```

- 필드 이름과 opcode 값은 RFC 826의 것이다.
- 주소 길이 필드(hln·pln)를 두어서 이더넷·IPv4가 아닌 조합에도 쓸 수 있게 했다.
- 28바이트는 이더넷 최소 데이터 46바이트보다 작다. 그래서 프레임에는 채움 바이트가 붙는다.

### 수신 알고리즘 — "아는 사이면 무조건 갱신"

RFC 826의 수신 처리는 이렇다.

```text
  ARP 패킷 수신
    |
    +-- (보낸 쪽 IP)가 이미 내 표에 있나?
    |      예 --> 그 항목의 MAC을 패킷의 sha로 갱신 (Merge_flag = true)
    |
    +-- 대상 IP(tpa)가 나인가?
    |      아니오 --> 끝
    |      예 --> 아직 표에 없으면(Merge_flag = false) 새로 추가
    |             op가 request면 --> 내 MAC을 채워 reply 전송
```

- 핵심: 보낸 쪽 IP가 표에 이미 있으면, **나에게 온 요청이 아니어도** MAC을 갱신한다.
- 이 규칙 덕분에 gratuitous ARP 하나로 이웃들의 캐시를 한꺼번에 고칠 수 있다.
- 같은 규칙 때문에 **위조한 ARP**로 남의 캐시를 바꿀 수도 있다. ARP에는 인증이 없다.

### ARP 캐시 — 얼마나 믿고, 언제 다시 묻나

- RFC 826은 캐시 만료를 프로토콜 범위 밖으로 둔다.
- RFC 1122 §2.3.2.1은 구현에 이것을 요구한다.
  - 오래된 항목을 비우는 방법이 **있어야 한다(MUST)**. 타임아웃 방식이면 값을 설정할 수 있어야 한다(SHOULD).
  - 같은 IP에 ARP 요청을 빠르게 반복하지 않게 막는 장치가 있어야 한다(MUST).
- 풀리지 않은 주소로 가는 패킷은 적어도 하나(가장 최근 것)를 버리지 말고 들고 있다가, 풀리면 보내야 한다(SHOULD, RFC 1122 §2.3.2.2).

리눅스는 IPv6 NDP와 같은 이웃 상태 기계(NUD)를 ARP에도 쓴다.

```text
               요청 전송                  응답 수신
  (없음) ---------------> INCOMPLETE ---------------> REACHABLE
                              |                        |  확인 없이 reachable 시간 경과
                              | 응답 없음               v
                              v                       STALE  <-- 아직 쓸 수는 있음
                            FAILED                      |  이 이웃에게 패킷을 보냄
                              ^                         v
                              |                       DELAY  (상위 계층 확인을 잠시 기다림)
                              |                         |  확인 없이 delay_first_probe_time 경과
                              |   유니캐스트 probe        v
                              +-- 전부 무응답 ------  PROBE ---- 응답 --> REACHABLE
```

  - *NUD(Neighbour Unreachability Detection)*: 이웃이 아직 닿는지 확인하는 절차. 상태 이름은 ip-neighbour(8)와 RFC 4861 §7.3.2에 있다.
- **REACHABLE**: 최근에 닿는 것이 확인됐다. 유효 기간은 `base_reachable_time`(기본 30초)의 1/2~3/2 사이 무작위 값이다(arp(7)).
- **STALE**: 유효하지만 "의심스러운" 상태다(ip-neighbour(8)). 여전히 이 MAC으로 보낸다.
- **DELAY**: STALE인 이웃에게 보낸 뒤, 상위 계층이 확인해 주기를 잠깐 기다린다. 기본 5초다(arp(7) `delay_first_probe_time`).
  - "확인"은 ARP 응답만이 아니다. TCP에서 새 ACK가 오는 것처럼 **앞으로 나아가는(forward progress)** 신호도 확인으로 친다(RFC 4861 §7.3.1).
- **PROBE**: 유니캐스트로 직접 물어본다. 기본 3번이다(arp(7) `ucast_solicit`).
- **FAILED**: 확인에 실패했다.
- 그 밖의 기본값(arp(7))
  - `gc_stale_time` 60초: 오래된 항목을 확인하는 주기.
  - `gc_thresh1/2/3` 128 / 512 / 1024: 캐시 크기의 하한·소프트 상한·하드 상한.
  - `unres_qlen`: 풀리지 않은 주소 하나에 대기시킬 패킷 수. arp(7)은 기본 3이라 적지만, 이는 리눅스 3.3 이전 값이다. 3.3부터는 바이트 기준 `unres_qlen_bytes`가 쓰이고 `unres_qlen` 기본은 101이다(ip-sysctl).

### gratuitous ARP — "묻지 않았는데 알리기"

```text
  VIP 10.0.0.100 이 서버1(MAC 11)에서 서버2(MAC 22)로 넘어감

  서버2 --- 브로드캐스트 ARP 요청 ------------------------------------------>
            op=1  sha=22  spa=10.0.0.100  tpa=10.0.0.100   (보낸 IP = 대상 IP)

  이웃들: "10.0.0.100은 이미 내 표에 있다" --> MAC을 22로 갱신 (RFC 826 규칙)
```

- 보낸 쪽 IP와 대상 IP에 **모두 자기 IP**를 넣은 ARP다.
  - RFC 5227은 이것을 *ARP Announcement*라 부른다. 브로드캐스트 ARP 요청이고, sender IP와 target IP 모두 알리는 주소다.
  - RFC 5227은 전통적인 "gratuitous ARP"(한 번만 알림)는 주소 충돌 **검출**에는 부족하다고 적는다.
- 쓰이는 곳
  - **페일오버**: VRRP는 새 Master가 되면 각 가상 IP에 대해 gratuitous ARP 요청을 브로드캐스트한다(RFC 5798 §6.4 상태 기계 동작).
  - **인터페이스 기동·MAC 변경**: 리눅스 `arp_notify=1`이면 장치가 올라오거나 MAC이 바뀔 때 gratuitous ARP를 보낸다(기본 0, ip-sysctl).
- 리눅스가 gratuitous ARP를 받을 때
  - `arp_accept`는 **표에 없는** IP의 gratuitous ARP로 새 항목을 만들지 정한다(기본 0 = 만들지 않음).
  - 표에 **이미 있는** IP라면 설정과 상관없이 갱신한다(ip-sysctl). 페일오버에서 중요한 것은 이쪽이다.

### 주소 충돌 검출 — ARP Probe

- 새 IP를 쓰기 전에 "이 IP 쓰는 사람 있나?"를 먼저 묻는다(RFC 5227).
  - *ARP Probe*: sender IP를 **0.0.0.0**으로 둔 브로드캐스트 ARP 요청이다. 대상 IP가 확인할 주소다.
  - sender IP가 0이라 이웃들의 캐시를 오염시키지 않는다.
- 기본 절차: 0~1초(`PROBE_WAIT`) 무작위로 기다린 뒤 probe 3번(`PROBE_NUM`). 응답이 없으면 announcement 2번(`ANNOUNCE_NUM`)을 2초 간격(`ANNOUNCE_INTERVAL`)으로 보낸다(RFC 5227).

## 쓰이는 자료구조·알고리즘

- **ARP 캐시 = 해시 테이블 + 타이머**
  - 키는 (인터페이스, IP), 값은 MAC과 상태다.
  - 리눅스 커널은 이웃 표를 해시 테이블(`struct neigh_hash_table`)로 두고, 항목마다 상태(`nud_state`)·확인 시각(`confirmed`)·타이머를 둔다(`include/net/neighbour.h`).
  - 개념은 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **유한 상태 기계** — INCOMPLETE·REACHABLE·STALE·DELAY·PROBE·FAILED의 NUD 상태 기계. 입력은 패킷 송신, 확인 수신, 타이머 만료다.
- **무작위화된 타임아웃** — REACHABLE 기간을 기준값의 0.5~1.5배로 흩뜨린다(RFC 4861 MIN/MAX_RANDOM_FACTOR, arp(7)). 여러 장비가 동시에 재확인하는 몰림을 피한다.
- **보류 큐** — 풀리지 않은 주소로 가는 패킷을 작은 큐(`unres_qlen`)에 잡아 두었다가 풀리면 보낸다. 큐가 차면 오래된 것을 버린다.
- **브로드캐스트 질의 + 유니캐스트 응답** — "모두에게 묻고 당사자만 답한다"는 발견(discovery) 패턴이다. DHCP(12번)도 같은 모양이다.

## 적용 — 풀어나가는 법

### 1. 캐시와 상태를 본다

```bash
ip neigh show                        # 이웃 표: IP, MAC(lladdr), 상태(REACHABLE/STALE/...)
ip neigh show dev eth0 nud failed    # 실패한 항목만
ip -s neigh show 10.0.0.1            # 사용·확인 시각 통계까지

sysctl net.ipv4.neigh.eth0.base_reachable_time_ms net.ipv4.neigh.default.gc_thresh3
```

- `ip neigh flush`는 permanent·noarp 항목을 빼고 지운다(ip-neighbour(8)). 잘못된 항목을 강제로 다시 풀게 할 때 쓴다.

### 2. ARP 교환을 캡처한다

```bash
tcpdump -eni eth0 arp
#  ARP, Request who-has 10.0.0.20 tell 10.0.0.5, length 28      (출력 모양 예시)
#  ARP, Reply 10.0.0.20 is-at 02:00:00:00:00:bb, length 28
```

- 같은 IP에 대해 **서로 다른 MAC이 번갈아 답하면** IP 충돌이나 스푸핑이다.
- 요청만 반복되고 답이 없으면 대상이 꺼져 있거나 다른 링크에 있다.

### 3. 직접 묻고, 직접 알린다

```bash
arping -I eth0 -c 3 10.0.0.20          # 그 IP의 MAC을 직접 물어보기
arping -D -I eth0 -c 3 10.0.0.100      # 중복 주소 검출(DAD): 응답이 없어야 성공(종료 코드 0)
arping -U -I eth0 -c 3 10.0.0.100      # 요청 형태로 알리기 (unsolicited ARP)
arping -A -I eth0 -c 3 10.0.0.100      # 응답 형태로 알리기
```

- `-U`는 이웃의 ARP 캐시를 갱신하는 unsolicited ARP 모드다. `-A`는 같은 일을 요청 대신 응답 패킷으로 한다(arping(8)).
- `-D`는 중복 주소 검출 모드다. 응답이 없으면 0을 돌려준다(arping(8)).
- 잘못 만든 ARP 구현은 요청하지 않은 reply를 무시할 수 있다. 그래서 RFC 5227 §3은 알림을 reply가 아니라 **request**로 보내라고 설명한다. 요청형·응답형을 둘 다 보내는 구현도 있다.

### 4. 코드에서 보이는 모습

ARP는 커널이 알아서 한다. 애플리케이션 API에는 나오지 않는다.\
대신 ARP가 실패하면 연결 에러로 드러난다.

```c
/* 같은 서브넷의 꺼진 호스트로 connect: ARP가 풀리지 않는다 */
int fd = socket(AF_INET, SOCK_STREAM, 0);
if (connect(fd, (struct sockaddr *)&addr, sizeof addr) < 0) {
    if (errno == EHOSTUNREACH) { /* 리눅스: ARP 실패 -> 커널이 ICMP host unreachable을 스스로 만듦 -> "No route to host" */ }
    if (errno == ETIMEDOUT)    { /* 또는 SYN 재전송 끝에 타임아웃 */ }
}
```

- 리눅스 커널 소스에서 ARP 실패는 `arp_error_report()`(net/ipv4/arp.c) → `ipv4_link_failure()`(net/ipv4/route.c)가 ICMP host unreachable을 만들고, 이것이 `EHOSTUNREACH`로 바뀐다(net/ipv4/icmp.c `icmp_err_convert`).
- 같은 서브넷인데 `No route to host`가 나면 라우팅보다 **ARP 실패**를 먼저 의심한다. `ip neigh`에서 그 IP가 `FAILED`/`INCOMPLETE`인지 본다.

## 장애 시나리오와 대처

### 1. VIP 페일오버 뒤 stale ARP — 죽은 서버로 계속 보낸다

- **현상**: 액티브 서버가 죽고 VIP가 대기 서버로 넘어갔다. 그런데 일부 클라이언트·게이트웨이는 수십 초 동안 계속 실패한다.
- **보이는 형태**
  - 클라이언트 쪽 `ip neigh show 10.0.0.100`이 **예전 MAC**을 가리킨다. 상태는 REACHABLE이나 STALE이다.
  - 연결 시도는 SYN 재전송 끝에 타임아웃, 기존 연결은 응답 없음.
  - tcpdump에 새 서버의 gratuitous ARP가 **보이지 않는다**.
- **원인**
  - 이웃들이 VIP → 예전 MAC 항목을 캐시에 들고 있다.
  - 새 서버가 알리지 않으면, 이웃은 자기 NUD 절차가 돌 때까지 예전 MAC으로 보낸다. REACHABLE 만료(15~45초) + DELAY(5초) + PROBE 실패를 거쳐야 다시 브로드캐스트로 묻는다(리눅스 기본값 기준 계산).
- **대처**
  - 넘겨받은 쪽이 즉시 gratuitous ARP를 보내게 한다. VRRP 구현(keepalived 등)은 Master 전환 시 보낸다(RFC 5798). 수동이면 `arping -U`/`-A`.
  - 받는 쪽이 리눅스면, 이미 있는 항목은 `arp_accept`와 무관하게 갱신된다(ip-sysctl).
  - gratuitous ARP를 무시하는 장비가 있으면 그 장비의 ARP 타임아웃을 줄이거나 항목을 flush한다.
  - VRRP의 가상 MAC(`00-00-5E-00-01-{VRID}`, RFC 5798)을 쓰면 VIP의 MAC이 바뀌지 않는다. 이웃의 ARP 캐시는 그대로 맞고, 스위치의 MAC 학습만 새 포트로 옮기면 된다.
  - 클라우드 VPC는 L2 브로드캐스트·gratuitous ARP가 막혀 있는 경우가 많다 [?]. 그때는 클라우드 API로 IP를 옮긴다.

### 2. IP 충돌 — 두 장비가 같은 IP를 쓴다

- **현상**: 특정 IP로의 연결이 됐다 안 됐다 한다. 가끔 엉뚱한 서버가 응답하거나 `Connection refused`/RST가 난다.
- **보이는 형태**
  - `tcpdump -eni eth0 arp`에서 같은 IP에 대해 **두 MAC**이 번갈아 reply한다.
  - `ip neigh`에서 그 IP의 MAC이 바뀌어 있다.
- **원인**: 수동 설정 실수, DHCP 범위와 고정 IP의 겹침, VM 복제 등이다. RFC 826 규칙상 마지막으로 들린 ARP가 캐시를 덮어쓴다.
- **대처**
  - `arping -D`로 새 IP를 쓰기 전에 중복을 검사한다(RFC 5227 방식).
  - 충돌한 MAC의 OUI로 장비 종류를 짐작하고, 스위치 MAC 테이블로 물리 포트를 찾는다.
  - IP 관리(IPAM)와 DHCP 예약으로 재발을 막는다.

### 3. ARP 스푸핑 — 게이트웨이 MAC이 공격자 것으로 바뀐다

- **현상**: 같은 망의 사용자들이 느려지거나, HTTPS 인증서 경고가 뜬다. 통신이 공격자를 거쳐 간다(중간자).
- **보이는 형태**
  - `ip neigh show 10.0.0.1`(게이트웨이)의 MAC이 평소와 다르다.
  - 서로 다른 여러 IP가 같은 MAC을 가리킨다.
  - tcpdump에 요청하지 않은 reply가 계속 들어온다.
- **원인**: ARP에는 인증이 없다. RFC 826 수신 알고리즘은 이미 아는 IP면 받은 패킷의 MAC으로 갱신한다. 공격자는 "게이트웨이 IP = 내 MAC"이라는 위조 ARP를 반복해 보낸다.
- **대처**
  - 스위치의 ARP 검사 기능(예: DHCP 스누핑 표와 대조해 위조 ARP를 버리는 기능 — 제조사 기능)을 켠다.
  - 중요한 호스트는 게이트웨이 항목을 정적(`ip neigh replace ... nud permanent`)으로 둔다.
  - 근본적으로는 L2 신뢰에 기대지 않는다. TLS 같은 종단 간 암호화·인증을 쓴다.

### 4. 이웃 표 넘침 — 큰 평면 L2망에서 새 연결이 간헐 실패

- **현상**: 컨테이너·VM이 많은 노드에서 새 연결이 가끔 실패한다. 기존 연결은 멀쩡하다.
- **보이는 형태**: 커널 로그에 `neighbour: arp_cache: neighbor table overflow!`(Red Hat KB, kubernetes/kops 이슈 사례).
- **원인**: 같은 링크의 이웃 수가 `gc_thresh3`(기본 1024, ip-sysctl)를 넘었다. 새 항목을 만들지 못해 주소를 풀지 못한다.
- **대처**
  - `net.ipv4.neigh.default.gc_thresh1/2/3`을 실제 이웃 수에 맞게 올린다.
  - L2 도메인을 쪼개거나(VLAN·서브넷) 라우팅 기반 네트워크로 바꿔 한 호스트가 직접 아는 이웃 수를 줄인다.

## 핵심 문장

- ARP는 같은 링크 안에서 IPv4 주소를 MAC으로 바꾼다. 찾는 대상은 최종 목적지가 아니라 **다음 홉**(같은 서브넷이면 목적지, 아니면 게이트웨이)이다.
- 요청은 브로드캐스트, 응답은 유니캐스트다. 결과는 캐시에 저장하고, 오래된 항목은 NUD 상태 기계로 재확인한다.
- RFC 826은 "이미 아는 IP면 받은 ARP의 MAC으로 갱신"한다. 그래서 gratuitous ARP로 페일오버를 알릴 수 있고, 같은 이유로 ARP 스푸핑이 된다.
- VIP를 옮긴 쪽이 gratuitous ARP를 보내지 않으면, 이웃은 NUD 절차가 돌 때까지 죽은 서버로 보낸다.
- 같은 서브넷인데 연결이 안 되면 `ip neigh`로 ARP 상태(FAILED·INCOMPLETE·엉뚱한 MAC)부터 본다.

## 관련 주제·근거

- 선행: [04-ethernet-and-mac](../04-ethernet-and-mac/2-summary.md) — MAC 주소, 브로드캐스트, EtherType
- 후속·연결
  - [06-switching-and-vlan](../06-switching-and-vlan/2-summary.md) — 스위치의 MAC 학습, 브로드캐스트 도메인 나누기
  - [07-ip-addressing-cidr](../07-ip-addressing-cidr/2-summary.md) — "같은 서브넷인가"의 판단.
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — 다음 홉(게이트웨이) 결정.
  - [12-dhcp](../12-dhcp/2-summary.md) — 같은 브로드캐스트 발견 패턴, 주소 충돌.
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) — 이웃 표
- RFC
  - RFC 826 — ARP 패킷 필드, opcode(1 request, 2 reply), 수신 알고리즘(Merge_flag), 캐시 만료는 범위 밖 <https://www.rfc-editor.org/rfc/rfc826>
  - RFC 1122 §2.3.2.1 캐시 비우기 MUST·타임아웃 설정 SHOULD·ARP flooding 방지 MUST, §2.3.2.2 미해결 주소 패킷 보관 SHOULD <https://www.rfc-editor.org/rfc/rfc1122>
  - RFC 5227 — ARP Probe(sender IP 0)·ARP Announcement(sender = target IP), PROBE_WAIT·PROBE_NUM·ANNOUNCE_NUM·ANNOUNCE_INTERVAL <https://www.rfc-editor.org/rfc/rfc5227>
  - RFC 5798 VRRP — 가상 MAC 00-00-5E-00-01-{VRID}, Master 전환 시 gratuitous ARP <https://www.rfc-editor.org/rfc/rfc5798>
  - RFC 4861 §7.3 — NUD 상태와 forward progress 확인, 상수(REACHABLE_TIME 30,000 ms, DELAY_FIRST_PROBE_TIME 5 s, MAX_UNICAST_SOLICIT 3) <https://www.rfc-editor.org/rfc/rfc4861>
  - RFC 7042 — ARP EtherType 0x0806 <https://www.rfc-editor.org/rfc/rfc7042>
- Linux 문서
  - arp(7) — `base_reachable_time_ms`(30000), `delay_first_probe_time`(5), `ucast_solicit`/`mcast_solicit`(3), `gc_stale_time`(60), `gc_thresh1/2/3`(128/512/1024), `unres_qlen`(3 — 3.3 이전 값, 현재는 ip-sysctl 참고) <https://man7.org/linux/man-pages/man7/arp.7.html>
  - ip-neighbour(8) — NUD 상태, `ip neigh show/flush` <https://man7.org/linux/man-pages/man8/ip-neighbour.8.html>
  - ip-sysctl — `arp_notify`, `arp_accept`(이미 있는 항목은 설정과 무관하게 갱신), `gc_thresh3`, `unres_qlen`(기본 101)·`unres_qlen_bytes` <https://docs.kernel.org/networking/ip-sysctl.html>
  - arping(8) — `-U`, `-A`, `-D` <https://man7.org/linux/man-pages/man8/arping.8.html>
  - 커널 소스 `include/net/neighbour.h` — `struct neigh_hash_table`, `struct neighbour` <https://github.com/torvalds/linux/blob/master/include/net/neighbour.h>
  - 커널 소스 `net/ipv4/arp.c` `arp_error_report()`, `net/ipv4/route.c` `ipv4_link_failure()` — ARP 실패가 EHOSTUNREACH가 되는 경로 <https://github.com/torvalds/linux/blob/master/net/ipv4/arp.c>
- 이웃 표 넘침 사례: kubernetes/kops issue #4533 <https://github.com/kubernetes/kops/issues/4533>, Red Hat KB <https://access.redhat.com/node/7099503>
- Kurose & Ross 8판 6.4.1 "Link-Layer Addressing and ARP"
