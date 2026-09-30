# network/09-icmp-ping-traceroute — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. IP의 침묵과 ICMP 오류의 내용

- IP는 최선 노력 전달이다. 버린 패킷에 대해 IP 자체는 아무것도 알려주지 않는다.
- ICMP 오류는 **type/code(이유)**와 **원래 패킷의 IP 헤더 + 데이터 앞 8바이트**를 담아 출발지로 돌아온다(RFC 792). 라우터는 576바이트 한도 안에서 더 많이 담는 것이 권장이다(RFC 1812 §4.3.2.3).
- 커널은 담긴 원래 헤더의 프로토콜·주소·포트로 **어느 소켓의 일인지 찾아** 에러를 전달한다(TCP는 MUST-54, RFC 9293 §3.9.2.2).
- 다만 ICMP 오류가 돌아온다는 보장은 없다(RFC 792 서론).

### 2. 용도별 ICMP

```text
ping                      8/0 Echo Request -> 0/0 Echo Reply   (IPv6: 128 -> 129)
traceroute 중간 홉          11/0 Time Exceeded (TTL exceeded in transit)
traceroute 종착(UDP 방식)   3/3 Destination Unreachable: port unreachable
PMTUD                      3/4 fragmentation needed and DF set (IPv6: type 2 Packet Too Big)
```

### 3. ICMP 오류를 보내면 안 되는 경우

RFC 1122 §3.2.2(MUST NOT)
- ICMP 오류 메시지에 대해
- IP 브로드캐스트·멀티캐스트 목적지 패킷에 대해
- 링크 계층 브로드캐스트로 온 패킷에 대해
- 첫 조각이 아닌 조각에 대해
- 출발지가 호스트 하나를 가리키지 않는 패킷에 대해

규칙이 없으면
- 오류에 대한 오류가 끝없이 오간다.
- 브로드캐스트 하나에 모든 호스트가 동시에 ICMP로 답해 망이 마비된다. RFC 1122는 이것을 broadcast storm 방지 이유로 든다.

### 4. traceroute 3홉

```text
TTL=1  -> R1에서 TTL 0 -> R1이 11/0 반환    "1: R1"
TTL=2  -> R2에서 TTL 0 -> R2가 11/0 반환    "2: R2"
TTL=3  -> 목적지 도착 -> 목적지가 3/3 반환   "3: 목적지, 종료"
```

- 리눅스 traceroute(8) 기본은 UDP 포트 33434부터 올려 가며 보낸다. TTL마다 3탐침, 최대 30홉이다.
- 도착 신호는 방식마다 다르다. UDP는 ICMP port unreachable, `-I`는 Echo Reply, `-T`는 SYN-ACK 또는 RST다.

### 5. 연결 중 ICMP 3/1

- **즉시 끊기지 않는다.**
- RFC 9293 §3.9.2.2는 Destination Unreachable code 0·1·5를 소프트 오류로 분류한다. 소프트 오류로 연결을 끊으면 안 된다(MUST-56). 앱에 알리는 것은 권장이다(SHLD-25).
- 일시적 경로 문제일 수 있기 때문이다. TCP는 재전송을 계속하고, 끝내 복구되지 않으면 재전송 타임아웃으로 실패가 드러난다.
- 예외: 연결 **수립 중**(SYN_SENT)이라면 소프트 오류도 하드 오류처럼 다루는 구현이 흔하다(RFC 9293 같은 절). 그래서 `connect()`는 곧바로 `EHOSTUNREACH`로 실패할 수 있다. 질문은 이미 연결된 소켓이므로 해당하지 않는다.
- 반면 code 2~4는 하드 오류로, 연결을 끊는 것이 권장이다(SHLD-26). 단 code 4는 실제로는 PMTUD 신호로 쓰인다.

### 6. ping과 서비스 상태가 다른 이유

- **ping 된다 ≠ 서비스 된다**
  - Echo Reply는 대상 **커널**이 보낸다.
  - 앱이 죽었거나, 멈췄거나, 포트가 방화벽에 막혀도 ping은 된다.
- **ping 안 된다 ≠ 서비스 안 된다**
  - 경로나 대상의 방화벽·보안 그룹이 ICMP Echo만 막을 수 있다.
  - TCP 443은 허용되어 있으면 서비스는 된다.
- 판단은 계층별로 한다: ping → traceroute → TCP 연결(`nc -vz`) → 앱 요청(`curl -v`).

### 7. 중간 홉만의 손실

- **장애라고 단정할 수 없다.** 오히려 정상일 가능성이 높다.
- 6번째 홉과 목적지가 정상이라는 것은 5번째 라우터가 패킷을 **잘 전달하고 있다**는 뜻이다.
- 5번째 홉의 손실·지연은 그 라우터가 **자기 앞으로 ICMP Time Exceeded를 만드는 일**을 속도 제한하거나 낮은 우선순위로 처리한 결과일 수 있다(RFC 1812 §4.3.2.8. 리눅스도 `icmp_ratelimit` 기본 1000ms).
- 진짜 손실은 그 홉부터 **최종 목적지까지 이어질 때**다.

### 8. ICMP 전면 차단 뒤 큰 응답만 멈춤

- 큰 패킷이 경로 중 MTU가 작은 링크(VPN·터널)를 만나면, 라우터는 DF 때문에 조각내지 못하고 ICMP 3/4("너무 크다, 다음 홉 MTU는 N")를 보낸다.
- 이 ICMP가 막혀 송신자는 크기를 줄이지 못한다. 같은 큰 세그먼트만 재전송하다 멈춘다(PMTUD 블랙홀).
- 작은 요청·응답은 MTU보다 작아서 영향이 없다. TLS 인증서 체인처럼 큰 응답이 먼저 걸린다.
- 최소한 다시 열 것
  - IPv4 ICMP type 3 code 4
  - IPv6 ICMPv6 type 2(Packet Too Big)
- RFC 4890은 ICMPv6 Destination Unreachable, Packet Too Big, Time Exceeded code 0, Parameter Problem code 1·2를 "버려서는 안 되는 트래픽"으로 분류한다.

### 9. `isReachable()`의 문제

- Javadoc 설명대로, ICMP Echo 권한이 있으면 Echo를 쓰고, 없으면 **TCP 7번(echo) 포트** 연결을 시도한다.
- 7번 포트가 닫혀 있는 것만으로는 false가 되지 않는다. OpenJDK 유닉스 구현은 연결이 되거나 RST(`ECONNREFUSED`)를 받아도 "도달했다"로 보고 true를 돌려준다(`Inet4AddressImpl.c` `tcp_ping4()`).
- false는 방화벽이 Echo·SYN을 조용히 버려 타임아웃될 때 나온다. 그래서 실제로 살아 있는데 false가 나올 수 있다.
- 반대로 true여도 앱이 정상이라는 뜻은 아니다.
- 대신 쓸 것
  - 실제 서비스 포트로 TCP 연결 시도(`Socket.connect(addr, timeout)`)
  - 가능하면 앱 수준 헬스 체크(HTTP `/health` 응답 내용 확인)
