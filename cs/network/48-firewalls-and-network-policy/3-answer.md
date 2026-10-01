# network/48-firewalls-and-network-policy — 정답

## 정답

### 1. netfilter 체인 경로

```text
  나에게 온 패킷:   PREROUTING -> (라우팅) -> INPUT -> 로컬 프로세스
  지나가는 패킷:    PREROUTING -> (라우팅) -> FORWARD -> POSTROUTING -> 송신
  내가 만든 패킷:   로컬 프로세스 -> OUTPUT -> POSTROUTING -> 송신
```

- `filter` 테이블의 내장 체인이 INPUT·FORWARD·OUTPUT이다(`iptables(8)`). DNAT는 PREROUTING, SNAT는 POSTROUTING에서 한다.

### 2. 상태 vs 무상태

- 서버가 외부 API(443)로 요청을 보내면, 응답은 외부 443 → 서버의 **임시 포트**(예: 51000)로 돌아온다.
- **상태 방화벽**: 나가는 요청을 conntrack이 기억한다. 응답은 ESTABLISHED로 분류되어 인바운드 규칙 없이 통과한다.
- **무상태 방화벽**(예: 네트워크 ACL): 응답 패킷도 인바운드 규칙에 맞아야 한다. 임시 포트 범위를 인바운드에서 열지 않으면 응답이 버려져 타임아웃이 난다.

### 3. DROP / REJECT / host-prohibited

| 방화벽 | 클라이언트가 받는 것 | 결과(리눅스) | 시간 |
|---|---|---|---|
| (a) DROP | 아무것도 없음 | SYN 재전송 뒤 `ETIMEDOUT` | `tcp_syn_retries` 기본 6 → 리눅스 6.5+ 기본값에서 약 131초(그 전 커널은 약 127초) |
| (b) REJECT 기본 | ICMP port unreachable | `ECONNREFUSED` | 즉시(1 RTT) |
| (c) icmp-host-prohibited | ICMP type 3 code 10 | `EHOSTUNREACH`("No route to host") | 즉시 |

- 근거: `iptables-extensions(8)`(IPv4 REJECT 기본 `icmp-port-unreachable`), 커널 `icmp_err_convert`(port unreachable → ECONNREFUSED, host prohibited → EHOSTUNREACH), `tcp_v4_err`(SYN_SENT에서 ICMP 오류 시 연결 시도 종료), `tcp(7)`(`tcp_syn_retries`), 커널 문서 `ip-sysctl`(`tcp_syn_retries`·`tcp_syn_linear_timeouts`).

### 4. 규칙 수와 지연

- iptables 체인은 규칙을 위에서부터 **선형으로** 비교한다. 수만 개면 연결의 첫 패킷마다 최악 수만 번 비교한다. softirq CPU와 첫 패킷 지연이 늘어난다.
- ipset(`hash:ip` 등)이나 nftables 집합은 원소를 해시·트리로 담는다. 규칙은 "주소가 집합에 있나" **하나**가 되고, 조회는 평균 상수 시간이다.
- nftables 판정 사상(`vmap`)은 "키 → 동작"을 한 번에 조회한다. kube-proxy nftables 모드가 이 방식으로 서비스 수와 무관한 지연을 얻었다(Kubernetes 블로그).

### 5. established 우선, invalid는 drop

- `established,related accept`를 맨 앞에 두면, 이미 허용된 연결의 패킷은 첫 규칙에서 끝난다. 긴 규칙 목록을 도는 것은 **연결의 첫 패킷**뿐이다.
- INVALID에 REJECT를 쓰면 안 되는 이유(`iptables-extensions(8)` 경고)
  - 오래 지연된 원래 패킷이 재전송 패킷보다 늦게 도착하면, 추적 항목과 맞지 않아 INVALID로 분류될 수 있다.
  - 거기에 RST·ICMP를 돌려보내면 멀쩡한 연결이 끊긴다. 그래서 INVALID는 조용히 DROP한다.

### 6. 보안 그룹 vs 네트워크 ACL

| | 보안 그룹 | 네트워크 ACL |
|---|---|---|
| 단위 | 인스턴스(ENI) | 서브넷 |
| 규칙 | 허용만 | 허용·거부 |
| 평가 | 모든 규칙 보고 판단 | 번호순, 처음 맞는 것 |
| 응답 | 자동 허용(상태) | 명시 허용(무상태) |

- "지금 당장" 끊으려면 **네트워크 ACL**에 거부 규칙을 넣는다.
- 보안 그룹은 규칙을 바꿔도 추적 중인 연결을 타임아웃까지 계속 허용한다. NACL은 무상태라 막는 즉시 기존 연결도 끊긴다(AWS 문서).

### 7. 응답만 사라지는 경우

- 가설: **비대칭 라우팅 + 상태 방화벽**. 요청은 방화벽 A를, 응답은 새 경로의 방화벽 B를 지난다. B는 SYN을 본 적이 없어 SYN/ACK를 INVALID로 버린다.
- 확인
  - 서버 `tcpdump`로 SYN/ACK가 어느 인터페이스·게이트웨이로 나가는지 본다.
  - 경로상 방화벽의 INVALID drop 카운터·로그를 본다.
  - 서버의 `ip route get <클라이언트IP>`로 응답 경로를 확인한다.
- 대처: 라우팅을 대칭으로 맞춘다. 요청과 응답이 같은 상태 장비를 지나게 한다.

### 8. NetworkPolicy 기본 거부와 DNS

- egress 기본 거부가 걸리면, 허용 목록에 없는 모든 목적지로 나가는 연결이 막힌다. **DNS 질의(53번 포트)도 그중 하나**다.
- 이름 해석이 실패하니 모든 호출이 `UnknownHostException`(Node는 `EAI_AGAIN` — 해석기 무응답이라 `ENOTFOUND`가 아니다)이 된다.
- 고치기: DNS 파드(또는 노드 로컬 DNS)로 가는 UDP·TCP 53번 egress를 먼저 허용하는 정책을 추가한다.
- 전제: 정책은 CNI 플러그인이 구현한다. 지원하지 않는 플러그인이면 정책 자체가 효과가 없다.

### 9. Java에서 DROP과 REJECT 구분

```java
try (Socket s = new Socket()) {
    s.connect(addr, 3_000);                       // 반드시 connect 타임아웃
} catch (SocketTimeoutException e) {              // DROP 계열: 응답 없음
    log.warn("connect timeout - DROP 의심", e);
} catch (ConnectException e) {                    // RST·ICMP port unreachable: refused
    log.warn("connect refused: {}", e.getMessage(), e);   // "Connection refused"
} catch (NoRouteToHostException e) {              // ICMP host/admin prohibited: EHOSTUNREACH
    log.warn("no route to host: {}", e.getMessage(), e);
}
```

- `SocketTimeoutException`(← `InterruptedIOException`)과 `ConnectException`·`NoRouteToHostException`(둘 다 ← `SocketException`)은 서로 상속 관계가 아니다. 그래서 catch 순서는 상관없다. 핵심은 경우별로 다른 메시지·지표로 남기는 것이다.
- OpenJDK는 EHOSTUNREACH를 `ConnectException`이 아니라 `NoRouteToHostException`으로 던진다(`sun/nio/ch/Net.c` `handleSocketError`). `ConnectException`만 잡으면 host-prohibited REJECT가 빠진다.
- **connect 타임아웃**을 반드시 설정한다. 없으면 DROP 경로에서 OS의 SYN 재시도(리눅스 6.5+ 기본값에서 약 131초, 그 전 커널은 약 127초) 동안 스레드가 묶이고, 결과 예외도 `ConnectException: Connection timed out` 형태가 되어 구분이 흐려진다(OpenJDK `Net.c`가 ETIMEDOUT을 `ConnectException`으로 바꾼다).
