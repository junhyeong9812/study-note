# network/04-ethernet-and-mac — 이더넷 프레임, MAC 주소, 충돌 도메인 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

IP는 "어느 호스트로 갈지"를 정한다.\
그런데 실제로 전선 위에 비트를 실어 **바로 옆 장비**에 건네는 일은 따로 필요하다.\
같은 선(또는 같은 스위치)에 여러 장비가 붙어 있으면 이런 문제가 생긴다.
- 이 비트 묶음은 **누구에게** 가는가?
- 어디서 시작해서 어디서 끝나는가?
- 가는 도중 비트가 깨졌는지 어떻게 아는가?
- 둘이 동시에 말하면 어떻게 하는가?

이더넷이 이 넷을 푼다. 주소(MAC), 경계(프레임), 오류 검사(CRC), 충돌 처리(CSMA/CD, 오늘날은 스위치와 전이중)다.

```text
  같은 링크 위의 장비들
   [PC-A]   [PC-B]   [서버]   [라우터]
      \        |        |        /
       +-------+-- 스위치 --+----+
  프레임: "목적지 MAC = 서버, 출발 MAC = PC-A, 안에 든 건 IPv4"
```

쉬운 예: 아파트 단지 안 택배다.\
동 호수(MAC)만 보고 문 앞까지 간다.\
다른 도시로 가는 택배는 단지 입구 택배함(라우터)까지만 이 방식으로 간다.

똑같은 구조다.\
이더넷은 **같은 링크 안**에서만 전달한다. 다른 망으로 갈 때는 라우터의 MAC으로 보낸다.

실무 예:
- 서버 한 대가 "가끔 느리다". 애플리케이션 에러는 없다.
- 알고 보니 스위치 포트와 NIC의 duplex 설정이 어긋나 프레임이 깨지고 있었다.
- TCP 재전송이 가려 줘서 위층에서는 "느림"으로만 보인다.

## 동작·원리

### 이더넷 프레임 구조

```text
  +----------+-----------+-----------+-----------+----------------------+---------+
  | 프리앰블  | 목적지 MAC | 출발 MAC  | EtherType | 데이터 (payload)      | FCS     |
  | 8        | 6         | 6         | 2         | 46 ~ 1500            | 4       |
  +----------+-----------+-----------+-----------+----------------------+---------+
             |<------------ 헤더 14 ------------->|                      |<-CRC-32->|
             |<------------- 프레임: 최소 64, 최대 1518바이트 ------------------------->|
```

- **프리앰블(8바이트)**: 앞 7바이트는 `10101010`, 마지막 바이트는 `10101011`이다. 받는 쪽 클록을 맞추고, 마지막 `11`로 "이제 진짜 프레임 시작"을 알린다(K&R 6.4.2).
- **목적지·출발 MAC(각 6바이트)**: 목적지가 **먼저** 온다.
- **EtherType(2바이트)**: payload가 무슨 프로토콜인지. IPv4 0x0800, ARP 0x0806, IPv6 0x86DD(RFC 7042).
  - 값이 0x0600 이상이면 EtherType이다(RFC 7042 §3). 1500(0x05DC) 이하면 IEEE 802.3 방식의 길이 필드로 읽는다.
- **데이터(46~1500바이트)**: IP 데이터그램이 들어간다.
  - 최대 1500이 이더넷 MTU다(RFC 894).
  - 46보다 작으면 0으로 채운다(padding). 채움 바이트는 IP 패킷의 일부가 아니다. IP 헤더의 Total Length에도 들어가지 않는다(RFC 894).
- **FCS(4바이트)**: 목적지 MAC부터 데이터까지에 대해 계산한 CRC-32 값이다.
  - *FCS(Frame Check Sequence)*: 받는 쪽이 같은 계산을 해서 값이 다르면 "프레임이 깨졌다"고 판단하는 검사 값.
- 최소 크기 64바이트 = 헤더 14 + 최소 데이터 46 + FCS 4다. 프리앰블은 세지 않는다.
- VLAN 태그(802.1Q)가 붙으면 출발 MAC과 EtherType 사이에 4바이트가 더 들어간다. 태그 식별값은 0x8100이다(RFC 7042). VLAN은 06번에서 다룬다.

### 이더넷은 "비연결·비신뢰" 서비스다

```text
  송신 NIC --- 프레임 ---> 수신 NIC
                          CRC 검사
                            | 맞음 --> EtherType 보고 위층(IP)으로
                            | 틀림 --> 조용히 버림. 송신자에게 알리지 않는다
```

- 이더넷은 연결을 맺지 않고, 받았다는 확인(ACK)도 보내지 않는다(K&R 6.4.2).
- CRC가 틀린 프레임은 **그냥 버린다**. 재전송은 없다.
- 빠진 데이터를 채우는 것은 위층의 몫이다. TCP면 재전송으로 메우고, UDP면 앱이 모르고 지나갈 수 있다.
- 그래서 링크 오류는 위층에서 **재전송·지연**으로 나타난다. 에러 메시지로는 잘 안 보인다.

### MAC 주소

```text
  예: 3C-22-FB-12-34-56   (예시 주소)
      |<-- OUI -->|<- 제조사가 배정 ->|
       24비트        24비트

  첫 옥텟의 두 비트
      0x01 비트 (Group 비트)  0 = 유니캐스트(한 장비)   1 = 그룹(멀티캐스트·브로드캐스트)
      0x02 비트 (Local 비트)  0 = 전역 고유(제조사 배정) 1 = 로컬 관리(관리자·소프트웨어가 정함)
```

- MAC 주소는 48비트다. 앞 24비트는 제조사(조직) 식별자 *OUI*, 뒤 24비트는 그 조직이 배정한다(RFC 7042).
  - *OUI(Organizationally Unique Identifier)*: IEEE가 조직에 배정하는 24비트 번호.
- 첫 옥텟의 두 비트가 특별하다(RFC 7042 §2.1).
  - **Group 비트(0x01)**: 켜지면 그룹 주소다. 여러 장비가 받는다.
  - **Local 비트(0x02)**: 켜지면 로컬 관리 주소다. VM·컨테이너·무작위 MAC처럼 소프트웨어가 만든 주소가 흔히 여기 속한다.
- 특별한 주소
  - 브로드캐스트 `FF-FF-FF-FF-FF-FF`: 같은 링크의 모든 장비가 받는다. ARP 요청이 이것을 쓴다(05번).
  - IPv4 멀티캐스트 `01-00-5E-00-00-00` ~ `01-00-5E-7F-FF-FF`(RFC 7042 §2.1.1).
- MAC 주소는 **같은 링크 안에서만** 의미가 있다. 라우터를 넘으면 새 MAC으로 바뀐다(02번).
- "제조사가 박아 둔 고유 번호"라고 믿으면 안 된다. `ip link set dev eth0 address ...`로 바꿀 수 있다(ip-link(8)).

### NIC는 어떤 프레임을 받나

```text
  들어온 프레임의 목적지 MAC이
    내 MAC                    --> 받는다
    FF-FF-FF-FF-FF-FF         --> 받는다 (브로드캐스트)
    내가 가입한 멀티캐스트      --> 받는다
    그 외                     --> 버린다 (무차별 모드가 아니면)
```

- 이 거르기는 NIC(와 드라이버)가 한다. 그래서 남의 프레임은 CPU까지 오지 않는다.
- *무차별 모드(promiscuous mode)*: 목적지와 상관없이 모든 프레임을 받는 모드. `tcpdump`는 기본으로 인터페이스를 이 모드로 바꾼다. `-p`는 그러지 말라는 옵션이다(tcpdump(1)).

### 충돌 도메인 — 공유 매체에서 스위치로

```text
  (옛날) 허브 / 동축 버스: 모두 한 선을 공유
     [A]   [B]   [C]   [D]
      |     |     |     |
     =+=====+=====+=====+=====   <- 한 충돌 도메인. 둘이 동시에 보내면 충돌
                                   반이중(half-duplex), CSMA/CD로 조정

  (오늘) 스위치: 포트마다 따로
     [A]   [B]   [C]   [D]
      |     |     |     |
     [-------- 스위치 --------]   <- 포트마다 별도 링크. 전이중(full-duplex)이면 충돌 자체가 없음
```

  - *충돌 도메인(collision domain)*: 두 장비가 동시에 보내면 신호가 섞이는 범위.
  - *반이중(half-duplex)*: 한 번에 한쪽만 보낼 수 있는 방식. *전이중(full-duplex)*: 동시에 양방향으로 보낼 수 있는 방식.
  - *CSMA/CD*: 보내기 전에 선이 비었는지 듣고(Carrier Sense), 보내는 중 충돌을 감지하면(Collision Detection) 멈추고 무작위 시간 뒤 다시 보내는 규칙.
- 허브는 받은 비트를 모든 포트로 되풀이한다. 그래서 허브에 붙은 전체가 한 충돌 도메인이다.
- 스위치는 프레임을 목적지 포트로만 보낸다. 포트마다 충돌 도메인이 나뉜다.
- 스위치와 호스트가 전이중으로 연결되면 충돌이 생길 수 없다. CSMA/CD가 필요 없다(K&R 6.4.2).
- *브로드캐스트 도메인*은 다르다. 스위치는 브로드캐스트 프레임을 모든 포트로 내보낸다. 라우터나 VLAN이 이 범위를 나눈다(06번).

### 늦은 충돌(late collision)과 duplex 불일치

- 정상적인 반이중 망에서 충돌은 프레임의 **앞부분**에서만 일어난다. 충돌을 감지할 수 있는 시간 안에 끝나도록 최소 프레임 길이가 정해져 있기 때문이다.
- 그보다 뒤에서 난 충돌이 *늦은 충돌*이다. 10 Mbit/s 포트 기준으로 전송 시작 후 512비트 시간(=64바이트)보다 늦은 충돌을 말한다(Cisco).
- 한쪽이 전이중, 다른 쪽이 반이중이면 이런 일이 벌어진다.

```text
  전이중 쪽 (아무 때나 보냄)         반이중 쪽 (듣고 보내고, 충돌이면 멈춤)
     |--- 프레임 --->                   <--- 프레임 보내는 중 ---|
                                        "충돌이다!" 전송 중단·재시도
     반이중 쪽이 끊다 만 프레임 수신       늦은 충돌 카운터 증가
     -> runt(너무 짧은 프레임)              FCS·alignment 에러 급증
```

- Cisco 문서
  - 늦은 충돌은 **반이중 쪽**에서 보인다. 반이중 쪽이 보내는 동안 전이중 쪽이 차례를 기다리지 않고 같이 보내기 때문이다.
  - 반이중 쪽의 FCS·정렬(alignment) 에러 급증과 전이중 쪽의 runt도 duplex 불일치의 신호다.
  - 다른 자료(예: Wikipedia "Duplex mismatch" <https://en.wikipedia.org/wiki/Duplex_mismatch>)는 FCS/CRC 에러를 전이중 쪽에 둔다. 실무에서는 양쪽 에러 카운터를 모두 보고, 가장 뚜렷한 신호인 반이중 쪽의 늦은 충돌을 확인한다.
- 흔한 원인: 한쪽은 자동 협상(auto-negotiation), 다른 쪽은 속도·duplex를 고정했다.
  - 고정한 쪽은 협상에 응하지 않는다. 자동 쪽은 속도는 알아내도 duplex는 알아낼 방법이 없다(Cisco).
  - Cisco는 양쪽을 모두 자동으로 두거나, 양쪽을 모두 같은 값으로 고정하라고 권한다. 한쪽 자동·한쪽 고정은 잘못된 설정이다.

## 쓰이는 자료구조·알고리즘

- **CRC-32(순환 중복 검사)** — 프레임 비트열을 다항식으로 보고, 정해진 생성 다항식으로 나눈 나머지를 FCS로 붙인다(K&R 6.2.3).
  - 받는 쪽도 같은 나눗셈을 해서 나머지가 맞는지 본다.
  - 오류를 **검출**만 하고 고치지는 않는다. 틀리면 버린다.
  - 구현은 바이트 단위 조회 테이블(256칸)로 빠르게 한다 [?].
- **고정 오프셋 레코드** — 목적지 MAC(0~5), 출발 MAC(6~11), EtherType(12~13)은 자리가 고정이다. 목적지가 맨 앞이라 스위치는 앞 6바이트만 읽고도 어디로 보낼지 정할 수 있다.
- **MAC 테이블(해시)** — 스위치는 "MAC → 포트"를 표로 들고 있다. 06번에서 다룬다. 개념은 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **이진 지수 백오프** — CSMA/CD는 충돌이 반복될수록 재시도 대기 시간의 범위를 두 배씩 넓힌다(K&R 6.3.2). 같은 발상이 앱의 재시도 백오프다([ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 링크 상태를 본다

```bash
# 속도·duplex·자동 협상 상태
ethtool eth0

# 인터페이스 통계 — -s를 두 번 주면 RX 에러 세부(crc, frame 등)까지
ip -s -s link show eth0

# NIC·드라이버별 세부 카운터 — 이름은 드라이버마다 다르다
ethtool -S eth0 | grep -Ei 'crc|err|drop|collision'
```

- `ethtool 장치`는 현재 설정을 보여 준다. `-S`는 표준(IEEE·IETF 등) 통계나 NIC·드라이버 고유 통계를 조회한다. 그룹을 지정하지 않으면 고유 통계가 나온다(ethtool(8)). 고유 통계의 이름은 드라이버마다 제각각이다.
- `ip`의 `-s`는 여러 번 주면 정보가 더 늘어난다(ip(8)).
- **카운터는 한 번 보고 끝내지 않는다.** 몇 초 간격으로 두 번 보고 증가량을 본다. 누적값만 보면 과거의 에러인지 지금의 에러인지 모른다.

### 2. 프레임을 MAC까지 캡처한다

```bash
tcpdump -eni eth0 -c 10          # -e: MAC 주소와 EtherType까지 출력
tcpdump -eni eth0 'ether broadcast'  # 브로드캐스트 프레임만
```

- 캡처에는 FCS가 보통 안 보인다. NIC가 검사한 뒤 떼어 내고 넘기기 때문이다 [?]. CRC 에러 프레임은 캡처 이전에 버려지므로 카운터로 봐야 한다.

### 3. 코드로 MAC 주소를 다룬다

```java
// 로컬 인터페이스의 MAC과 두 특수 비트 확인
for (NetworkInterface ni : Collections.list(NetworkInterface.getNetworkInterfaces())) {
    byte[] mac = ni.getHardwareAddress();          // 루프백 등은 null
    if (mac == null) continue;
    boolean group = (mac[0] & 0x01) != 0;          // Group 비트
    boolean local = (mac[0] & 0x02) != 0;          // Local 비트
    System.out.printf("%s %s group=%b local=%b%n", ni.getName(),
        HexFormat.ofDelimiter("-").withUpperCase().formatHex(mac), group, local);
}
```

```java
// CRC가 비트 하나의 변화도 잡아내는 것 보기
CRC32 crc = new CRC32();
byte[] frame = "hello ethernet".getBytes(StandardCharsets.US_ASCII);
crc.update(frame);
long before = crc.getValue();
frame[3] ^= 0x01;                                  // 비트 하나 뒤집기
crc.reset(); crc.update(frame);
System.out.println(before != crc.getValue());      // true: 오류 검출
```

- `java.util.zip.CRC32`는 CRC-32를 계산한다(Javadoc). 이더넷 FCS와 같은 생성 다항식을 쓴다고 알려져 있다 [?].

## 장애 시나리오와 대처

### 1. duplex 불일치 — CRC 에러·늦은 충돌로 간헐적으로 느리다

- **현상**: 특정 서버만 가끔 느리다. 큰 전송일수록 심하다. 애플리케이션 에러는 거의 없다.
- **보이는 형태**
  - 반이중 쪽 인터페이스에서 late collision 카운터가 오른다(Cisco).
  - 반이중 쪽에서 FCS·CRC·alignment 에러가, 전이중 쪽에서 runt 카운터가 오른다(Cisco).
  - 호스트의 `ip -s -s link`에서 RX crc·frame 에러가 늘어난다.
  - TCP 재전송(`ss -ti`의 `retrans`, `nstat`의 재전송 카운터)이 늘어난다.
- **원인**: 한쪽은 자동 협상, 다른 쪽은 속도·duplex 고정이다. 자동 쪽이 duplex를 알아내지 못해 반이중으로 동작한다. 두 쪽의 규칙이 달라 프레임이 서로 깨진다.
- **대처**
  - `ethtool eth0`로 양쪽의 Speed·Duplex·Auto-negotiation을 확인한다.
  - 양쪽을 모두 자동 협상으로 두거나, 양쪽을 같은 값으로 고정한다(Cisco 권고).
  - 고친 뒤 에러 카운터의 **증가**가 멈췄는지 본다.

### 2. 케이블·포트·광모듈 불량 — CRC 에러가 계속 오른다

- **현상**: duplex는 맞는데도 에러 카운터가 계속 오른다. 링크가 가끔 down/up을 반복하기도 한다.
- **보이는 형태**: RX crc 에러 증가, 커널 로그의 `Link is Down`/`Link is Up` 반복 [?], TCP 재전송 증가.
- **원인**: 물리 계층 신호 품질 문제다. 수신 쪽 CRC 검사에서 프레임을 버린다. 이더넷은 재전송하지 않으니 TCP가 대신 재전송한다.
- **대처**: 케이블·포트·광모듈을 교체해 보고 카운터 증가가 멈추는지 확인한다. 본딩(이중화)이 있으면 문제 링크를 빼 둔다.

### 3. 같은 MAC 주소를 쓰는 두 장비 — 둘 다 번갈아 끊긴다

- **현상**: VM 이미지를 복제한 뒤, 두 VM이 번갈아 가며 통신이 끊긴다.
- **보이는 형태**
  - 같은 링크의 다른 장비에서 `ip neigh`로 보면 두 IP가 같은 MAC을 가리킨다.
  - 스위치의 MAC 테이블에서 같은 MAC이 두 포트 사이를 오간다(MAC flapping).
- **원인**: MAC은 "같은 링크 안에서 고유"하다는 가정 위에서 동작한다. 복제로 이 가정이 깨졌다. 스위치는 마지막으로 그 MAC을 보낸 포트로만 프레임을 보낸다.
- **대처**: 복제한 VM의 MAC을 새로 생성한다. 로컬 관리 비트(0x02)를 켠 주소를 쓰면 제조사 주소와 겹치지 않는다.

### 4. MTU(점보 프레임) 불일치 — 큰 프레임만 사라진다

- **현상**: 저장소 망에서 점보 프레임을 켰다. 작은 요청은 되는데 큰 전송만 멈춘다.
- **보이는 형태**: 호스트 MTU는 9000(예시)인데 중간 스위치 포트는 1500이다. 큰 프레임이 스위치에서 버려진다. `ping -M do -s 8972`(9000 − 28)가 실패한다.
- **원인**: 링크 계층에는 "너무 크니 줄여라"라는 알림이 없다. 같은 링크 안에서 MTU가 다르면 큰 프레임은 조용히 버려진다.
- **대처**: 한 링크(한 브로드캐스트 도메인)의 모든 장비 MTU를 같게 맞춘다. 끝에서 끝까지 `ping -M do`로 검증한다(02·10번).

## 핵심 문장

- 이더넷 프레임은 목적지 MAC·출발 MAC·EtherType(14바이트) + 데이터(46~1500) + FCS(4)다. 1500이 MTU다.
- 이더넷은 비연결·비신뢰다. CRC가 틀린 프레임은 조용히 버린다. 그래서 링크 오류는 위층에서 재전송과 지연으로 보인다.
- MAC 주소는 48비트, 앞 24비트가 OUI다. 첫 옥텟의 0x01은 그룹, 0x02는 로컬 관리 비트다. 같은 링크 안에서만 의미가 있다.
- 허브는 한 충돌 도메인, 스위치는 포트마다 충돌 도메인이다. 전이중이면 충돌이 없다. 브로드캐스트 도메인은 스위치로 나뉘지 않는다.
- duplex 불일치는 반이중 쪽의 늦은 충돌·FCS 에러와 전이중 쪽의 runt로 드러난다. 양쪽 설정을 같은 방식(둘 다 자동 또는 둘 다 고정)으로 맞춘다.

## 관련 주제·근거

- 선행: [02-encapsulation](../02-encapsulation/2-summary.md) — 이더넷 헤더가 붙는 자리
- 후속·연결
  - [05-arp](../05-arp/2-summary.md) — IP 주소로 목적지 MAC 찾기
  - [06-switching-and-vlan](../06-switching-and-vlan/2-summary.md) — 스위치의 MAC 학습·플러딩·VLAN
  - [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md) — MTU 불일치.
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) — MAC 테이블
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) — 지수 백오프
- RFC
  - RFC 894 — EtherType 0x0800, 데이터 46~1500, 채움 바이트는 IP 길이에 불포함 <https://www.rfc-editor.org/rfc/rfc894>
  - RFC 7042 — §2.1 48비트 MAC, OUI, Group 비트(0x01)·Local 비트(0x02) · §2.1.1 IPv4 멀티캐스트 01-00-5E-00-00-00~7F-FF-FF · §3 EtherType ≥ 0x0600 <https://www.rfc-editor.org/rfc/rfc7042>
- Cisco
  - "Troubleshoot Switch Port and Interface Problems" — late collision(512비트 시간), 반이중 쪽에서 보임, FCS-Err, 양쪽 설정 일치 권고 <https://www.cisco.com/c/en/us/support/docs/switches/catalyst-6500-series-switches/12027-53.html>
  - "Configure and Verify Ethernet 10/100/1000Mb Half/Full Duplex Auto-Negotiation" — 자동 협상 쪽이 duplex를 알 수 없음, FCS·alignment·runt <https://www.cisco.com/c/en/us/support/docs/lan-switching/ethernet/10561-3.html>
- Linux 문서
  - ethtool(8) <https://man7.org/linux/man-pages/man8/ethtool.8.html>
  - ip-link(8) `address` <https://man7.org/linux/man-pages/man8/ip-link.8.html>
  - tcpdump(1) `-e`, `-p` <https://www.tcpdump.org/manpages/tcpdump.1.html>
- Java `NetworkInterface.getHardwareAddress`, `java.util.zip.CRC32` Javadoc <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/zip/CRC32.html>
- Kurose & Ross 8판 6.2.3 CRC, 6.3.2 CSMA/CD, 6.4.2 "Ethernet"(프레임 구조, 비연결·비신뢰, 스위치와 전이중)
