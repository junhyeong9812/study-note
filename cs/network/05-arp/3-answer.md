# network/05-arp — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 누구의 MAC을 찾나

- 10.0.0.20: 같은 /24 서브넷이다. **10.0.0.20 자신**의 MAC을 찾는다.
- 8.8.8.8: 다른 망이다. **게이트웨이 10.0.0.1**의 MAC을 찾는다.
- 8.8.8.8로 가는 패킷의 IP 목적지는 **8.8.8.8 그대로**다. 이더넷 목적지만 게이트웨이 MAC이다(K&R 6.4.1).

### 2. 요청과 응답

```text
요청: 이더넷 목적지 FF-FF-FF-FF-FF-FF (브로드캐스트)
      op=1  sha=내 MAC  spa=내 IP  tha=0(모름)  tpa=찾는 IP
응답: 이더넷 목적지 = 요청한 쪽 MAC (유니캐스트)
      op=2  sha=내 MAC  spa=내 IP  tha=요청자 MAC  tpa=요청자 IP
```

- EtherType은 0x0806이다. IP 패킷이 아니라 이더넷 위에 바로 실린다.
- 응답하는 쪽도 요청을 받으면서 요청자의 IP → MAC을 캐시에 넣는다(RFC 826).

### 3. Merge 규칙

- 받은 ARP의 **보낸 쪽 IP가 이미 내 표에 있으면**, 대상 IP가 내가 아니어도 그 항목의 MAC을 패킷의 sha로 갱신한다(RFC 826 Merge_flag).
- 좋은 결과: **gratuitous ARP** 한 번으로 이웃 전체의 캐시를 새 MAC으로 고칠 수 있다(페일오버).
- 나쁜 결과: 인증이 없으니 **위조 ARP**로 남의 캐시를 바꿀 수 있다(ARP 스푸핑).

### 4. NUD 상태 전이

```text
(없음) --요청 전송--> INCOMPLETE --응답--> REACHABLE
INCOMPLETE --응답 없음--> FAILED
REACHABLE --확인 없이 reachable 시간 경과--> STALE
STALE --이 이웃에게 패킷 전송--> DELAY
DELAY --상위 계층 확인--> REACHABLE
DELAY --delay_first_probe_time(기본 5초) 동안 확인 없음--> PROBE
PROBE --유니캐스트 probe에 응답--> REACHABLE
PROBE --ucast_solicit(기본 3번) 모두 무응답--> FAILED
```

- REACHABLE 기간은 `base_reachable_time`(기본 30초)의 0.5~1.5배 무작위다(arp(7)).
- **DELAY의 이유**: 바로 probe를 보내지 않고, 상위 계층이 "잘 되고 있다"고 확인해 줄 시간을 준다. TCP에서 새 ACK가 오면 그 이웃은 닿는 것이다(RFC 4861 §7.3.1 forward progress). 불필요한 ARP 트래픽을 줄인다.

### 5. Announcement vs Probe

| | sender IP | target IP | 용도 |
|---|---|---|---|
| ARP Announcement(gratuitous ARP) | 알리는 자기 IP | 같은 자기 IP | 이웃 캐시를 새 MAC으로 갱신(페일오버·기동·MAC 변경) |
| ARP Probe | **0.0.0.0** | 확인할 IP | 그 IP를 누가 쓰는지 확인(주소 충돌 검출) |

- 둘 다 브로드캐스트 ARP 요청이다(RFC 5227).
- Probe는 sender IP가 0이라 이웃 캐시를 건드리지 않는다.

### 6. VIP 페일오버 뒤 stale ARP

- **확인**
  - 실패하는 클라이언트(또는 그 게이트웨이)에서 `ip neigh show <VIP>`가 예전 서버 MAC을 가리키는지 본다.
  - `tcpdump -eni eth0 arp`로 새 서버의 gratuitous ARP가 나갔는지 본다.
- **원인**: 새 서버가 알리지 않았거나, 그 장비가 무시했다. 이웃은 NUD 절차(REACHABLE 만료 15~45초 + DELAY 5초 + PROBE 실패)가 돌 때까지 예전 MAC으로 보낸다(리눅스 기본값 기준).
- **막기**
  - 넘겨받은 쪽이 즉시 gratuitous ARP를 보낸다(VRRP는 Master 전환 시 보낸다, RFC 5798 §6.4). 수동이면 `arping -U`/`-A`.
  - 리눅스 이웃은 이미 있는 항목이면 `arp_accept`와 무관하게 갱신한다(ip-sysctl).
- **VRRP 가상 MAC**(`00-00-5E-00-01-{VRID}`)을 쓰면 VIP의 MAC이 페일오버 전후로 **같다**.
  - 이웃의 ARP 캐시는 그대로 맞다.
  - 대신 스위치가 그 MAC을 새 포트로 배워야 한다. Master가 보내는 패킷이 이를 일으킨다(RFC 5798).

### 7. IP 충돌

- **판단**: 같은 IP에 대해 **서로 다른 두 MAC**이 번갈아 reply(또는 announcement)한다.
- **예방**
  - 새 IP를 쓰기 전에 `arping -D`로 중복 주소 검출(DAD)을 한다. 응답이 없어야 성공이다(arping(8)).
  - RFC 5227의 ARP Probe 절차(probe 3번 후 announcement)를 따르는 구현을 쓴다.
  - DHCP 범위와 고정 IP 범위를 겹치지 않게 관리한다.

### 8. ARP 스푸핑

- **근본 이유**: ARP에는 **인증이 없다**. RFC 826은 이미 아는 IP면 받은 패킷의 MAC을 그대로 믿고 갱신한다.
- **L2 방어**: 스위치에서 ARP를 DHCP 할당 기록과 대조해 위조를 버리는 기능(제조사 기능)을 켠다. 또는 중요 호스트에서 게이트웨이 항목을 정적(`nud permanent`)으로 둔다.
- **L2 밖 방어**: TLS처럼 종단 간 암호화·서버 인증을 쓴다. 트래픽이 가로채져도 읽거나 바꾸지 못하고, 인증서 검증에서 드러난다.

### 9. neighbor table overflow

- **원인 설정**: 이웃 수가 `gc_thresh3`(기본 1024, ip-sysctl)를 넘었다. 새 이웃 항목을 만들지 못해 주소를 풀지 못한다.
- **대처**
  - `net.ipv4.neigh.default.gc_thresh1/2/3`을 실제 이웃 수에 맞게 올린다.
  - L2 도메인을 작게 나누거나 라우팅 기반 네트워크로 바꿔, 한 호스트가 직접 아는 이웃 수를 줄인다.
