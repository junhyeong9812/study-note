# network/48-firewalls-and-network-policy — 상태 방화벽·보안 그룹·iptables/nftables — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

서버에 열린 포트는 인터넷의 누구나 두드릴 수 있다.\
DB 포트(5432)가 외부에 열려 있으면 비밀번호 대입 공격을 받는다.\
방화벽은 "어떤 패킷을 들이고 내보낼지"를 규칙으로 정한다.

쉬운 예: 건물 출입 관리다.\
"직원증이 있으면 들어온다", "택배는 1층까지만"처럼 규칙이 있다.\
이미 안에서 나간 사람이 돌아오는 것은 따로 확인하지 않는다(기억하고 있으니까).

똑같은 구조다.\
규칙 = 출입 조건, **상태 추적** = "이 사람은 안에서 나갔다 돌아오는 중"을 기억하는 것.

실무 예:
- 리눅스 호스트의 iptables/nftables 규칙.
- 클라우드의 보안 그룹(인스턴스 단위)과 네트워크 ACL(서브넷 단위).
- 쿠버네티스 NetworkPolicy(파드 단위).
- 방화벽 설정 하나로 "연결 거부"와 "2분 동안 멈춤"처럼 전혀 다른 증상이 나온다.

## 동작·원리

### 1. 리눅스 netfilter — 패킷이 지나는 갈고리(hook)

```text
  NIC 수신
    |
  PREROUTING (nat: DNAT)
    |
  라우팅 결정 ---- 나에게 온 것 ----> INPUT (filter) ----> 로컬 프로세스(소켓)
    |                                                         |
    +-- 지나가는 것 --> FORWARD (filter)                       v
                          |                               OUTPUT (filter, nat)
                          v                                   |
                       POSTROUTING (nat: SNAT) <--------------+
                          |
                       NIC 송신
```

- iptables의 기본 테이블은 `filter`다. 내장 체인은 INPUT(로컬 소켓으로 가는 패킷), FORWARD(이 호스트를 지나가는 패킷), OUTPUT(로컬에서 만든 패킷)이다(`iptables(8)`).
- `nat` 테이블은 새 연결을 만드는 패킷에서 참조한다(`iptables(8)`).
- nftables는 같은 갈고리 위에 사용자가 테이블·체인을 직접 만든다. 기본 체인(base chain)에 `hook`과 `priority`를 준다(`nft(8)`).

### 2. 규칙 평가 — 위에서부터, 처음 맞는 것

```text
  체인 INPUT (정책: DROP)
   1. ct state established,related  -> ACCEPT
   2. ct state invalid              -> DROP
   3. tcp dport 22  saddr 10.0.0.0/8 -> ACCEPT
   4. tcp dport 443                 -> ACCEPT
   (끝까지 안 맞으면)                 -> 체인 정책 DROP
```

- 패킷이 규칙에 안 맞으면 다음 규칙을 본다. 맞으면 대상(target)이 운명을 정한다(`iptables(8)` TARGETS).
- 내장 체인 끝에 닿으면 **체인 정책**이 적용된다. iptables 정책은 ACCEPT나 DROP이다.
- nftables 기본 체인의 정책 기본값은 `accept`다(`nft(8)`).
- 규칙은 **선형 탐색**이다. 규칙이 N개면 최악의 경우 N번 비교한다.

### 3. 상태 추적 — 돌아오는 패킷을 기억한다

```text
  클라이언트 10.0.0.5:51000  ---SYN--->  서버 :443
     conntrack: [10.0.0.5:51000 -> :443]  상태 NEW
  클라이언트                 <--SYN/ACK--  서버
     같은 항목, 양방향을 봤으므로       ESTABLISHED
  이후 패킷                                 ESTABLISHED -> 규칙 1에서 바로 ACCEPT
```

conntrack 상태(`iptables-extensions(8)` conntrack):

```text
  NEW          새 연결을 시작하거나, 아직 양방향을 보지 못한 연결의 패킷
  ESTABLISHED  양방향 패킷을 본 연결의 패킷
  RELATED      기존 연결과 관련된 새 연결 (예: FTP 데이터, ICMP 오류)
  INVALID      알려진 연결에 속하지 않는 패킷
  UNTRACKED    추적하지 않기로 한 패킷 (raw 테이블의 --notrack)
```

- **상태 방화벽(stateful)**: 연결 상태를 기억한다. "나가는 요청을 허용하면 그 응답은 자동 허용"이 된다.
- **무상태 방화벽(stateless)**: 패킷 하나하나만 본다. 응답 방향도 규칙으로 따로 열어야 한다.
- conntrack 테이블은 해시 테이블이고, 항목마다 만료 타이머가 있다. 크기 한도(`nf_conntrack_max`)가 차면 새 연결을 못 받는다. 자세한 것은 [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md)에서 다룬다.

  - *conntrack*: 리눅스 커널의 연결 추적 모듈이다. 5-튜플(프로토콜·출발지·목적지 주소와 포트)로 연결을 식별한다.

### 4. drop vs reject — 증상이 완전히 다르다

```text
  DROP (조용히 버림)                      REJECT (거절 패킷을 돌려보냄)
  클라이언트 --SYN-->  X                  클라이언트 --SYN-->  방화벽
             --SYN--> X  (재전송)                     <--ICMP port-unreachable (기본)
             --SYN--> X  (재전송) ...                  또는 <--RST (--reject-with tcp-reset)
  약 131초 뒤 connect() 실패: ETIMEDOUT    즉시 connect() 실패: ECONNREFUSED 등
  (리눅스 6.5+ 기본값. 그 전 커널은 약 127초)
```

- `REJECT`는 오류 패킷을 돌려보낸다. 그 외에는 DROP과 같이 규칙 탐색을 끝낸다(`iptables-extensions(8)`).
  - iptables IPv4의 기본 응답은 `icmp-port-unreachable`이다. TCP 규칙에서는 `tcp-reset`으로 RST를 보낼 수 있다.
  - nftables `reject`의 흔한 기본값도 `port-unreachable`이다(`nft(8)`).
- 리눅스 클라이언트가 받는 errno(커널 `net/ipv4/icmp.c`의 `icmp_err_convert`):

```text
  받은 것                                 connect() 결과(리눅스)
  RST                                     ECONNREFUSED  "Connection refused"
  ICMP port unreachable (type 3 code 3)    ECONNREFUSED
  ICMP host prohibited  (code 10)          EHOSTUNREACH  "No route to host"
  ICMP admin prohibited (code 13)          EHOSTUNREACH
  아무것도 안 옴 (DROP)                     SYN 재전송 뒤 ETIMEDOUT
```

- 리눅스는 연결 중(SYN_SENT) ICMP 오류를 받으면 그 오류로 연결 시도를 바로 끝낸다(`tcp_v4_err`).
- SYN 재전송 횟수는 `tcp_syn_retries`(기본 6)이다. 리눅스 6.5+ 기본값에서 약 131초 뒤 실패한다(그 전 커널은 약 127초 — `tcp(7)`). 6.5+는 처음 몇 번을 1초 간격으로 재전송하기 때문이다(`tcp_syn_linear_timeouts` 기본 4, 커널 문서 `ip-sysctl`). 앱에 connect 타임아웃이 있으면 그 전에 끝난다.
- 앱에서 보이는 모양
  - Java: `ConnectException: Connection refused` vs `NoRouteToHostException: No route to host`(EHOSTUNREACH) vs `SocketTimeoutException: Connect timed out`(connect 타임아웃 설정 시). OpenJDK는 EHOSTUNREACH를 `ConnectException`이 아니라 `NoRouteToHostException`으로 바꾼다(`sun/nio/ch/Net.c` `handleSocketError`).
  - Node.js: `connect ECONNREFUSED 10.0.0.5:5432` vs `connect ETIMEDOUT 10.0.0.5:5432`.

### 5. 규칙이 많을 때 — 선형 탐색 vs 집합

```text
  선형 규칙 (iptables 기본)                 집합 조회 (ipset, nftables set/map)
  1. saddr 1.1.1.1 DROP                    set blocklist { 1.1.1.1, 2.2.2.2, ... 5만 개 }
  2. saddr 2.2.2.2 DROP                    1. ip saddr @blocklist drop     <- 규칙 1개
  ...                                         (해시·트리 조회)
  50000. saddr ... DROP
  -> 패킷마다 최악 5만 번 비교              -> 패킷마다 조회 1번
```

- ipset의 hash 타입 집합은 해시로 원소를 저장한다(`ipset(8)`). iptables에서 `-m set --match-set 이름 src`로 쓴다(`iptables-extensions(8)`).
- nftables는 집합(set)과 사상(map)을 기본 기능으로 가진다(`nft(8)`).
  - 이름 있는 집합은 규칙을 바꾸지 않고 원소만 넣고 뺄 수 있다.
  - 판정 사상(verdict map, `vmap`)은 "키 → 판정(accept/drop/goto 체인)"을 한 번에 조회한다.
- 쿠버네티스 kube-proxy 사례
  - iptables 모드는 서비스 IP마다 규칙이 하나씩 있어 첫 패킷 처리 시간이 서비스 수에 대해 O(n)이다.
  - nftables 모드는 판정 사상 하나로 대략 O(1) 조회를 한다. 3만 서비스 클러스터에서 nftables의 p99 지연이 iptables의 p01보다도 낮았다고 보고한다(Kubernetes 블로그 2025-02-28).

### 6. 클라우드 — 보안 그룹과 네트워크 ACL

```text
  인터넷 -> [서브넷 경계: 네트워크 ACL (무상태, 번호순, 허용/거부)]
                 -> [인스턴스: 보안 그룹 (상태, 허용만, 전부 평가)] -> 앱
```

AWS 문서의 비교:

```text
  항목         보안 그룹                    네트워크 ACL
  적용 단위     인스턴스(ENI)                서브넷
  규칙 종류     허용만                       허용·거부
  평가          모든 규칙을 보고 판단          번호 오름차순, 처음 맞는 것
  응답 트래픽    자동 허용 (상태)              명시적으로 허용해야 (무상태)
```

- 보안 그룹은 연결 추적을 쓴다. 규칙을 바꿔도 **추적 중인 기존 연결은 즉시 끊기지 않는다**. 타임아웃될 때까지 허용된다. 즉시 끊으려면 네트워크 ACL을 쓴다(AWS 문서).
  - 예외: TCP·UDP 흐름이 한 방향 규칙에서 0.0.0.0/0(또는 ::/0)으로 허용되고, 반대 방향도 0.0.0.0/0·모든 포트로 응답을 허용하면 그 흐름은 추적하지 않는다(NAT 게이트웨이·NLB 등을 거치는 자동 추적 연결은 제외). 이 경우 규칙을 지우면 즉시 끊긴다.
- 인스턴스당 추적 연결 수에 한도가 있다. 넘으면 패킷이 버려진다. `conntrack_allowance_exceeded` 지표로 본다(AWS 문서).
- 추적 연결 유휴 타임아웃(TCP established)은 인스턴스 세대에 따라 기본 350초 또는 432,000초(5일)다(AWS 문서).

### 7. 쿠버네티스 NetworkPolicy

- NetworkPolicy는 **네트워크 플러그인(CNI)이 구현**한다. 지원하지 않는 플러그인이면 리소스를 만들어도 효과가 없다(쿠버네티스 문서).
- 기본은 격리되지 않음(모두 허용)이다. 어떤 정책이 파드를 ingress/egress 방향으로 고르면, 그 방향은 허용한 연결만 통과한다.
- 정책은 더해진다(합집합). 연결이 되려면 출발 파드의 egress와 도착 파드의 ingress가 **둘 다** 허용해야 한다.
- 허용된 연결의 응답은 암묵적으로 허용된다(상태 기반).

## 쓰이는 자료구조·알고리즘

- **규칙 리스트 선형 탐색** — iptables 체인은 규칙을 위에서부터 차례로 비교한다. 비용이 규칙 수에 비례한다.
- **해시 집합(ipset `hash:*`, nftables set)** — 주소·포트 조회를 평균 상수 시간으로 만든다. [05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **구간 집합(interval set)** — nftables는 CIDR·포트 범위를 구간 집합으로 담을 수 있다(`flags interval`). 겹치는 원소 자동 병합(`auto-merge`)도 있다(`nft(8)`). [30-interval-tree](../../data-structure/30-interval-tree/2-summary.md) 참고.
- **판정 사상(verdict map)** — 키 → 동작의 맵. 규칙 N개를 조회 1번으로 바꾼다.
- **conntrack = 해시 테이블 + 타이머** — 5-튜플 해시로 연결을 찾고, 상태별 타임아웃으로 지운다. 기본 버킷 수는 메모리 크기로 정해지고, 커널 5.15+에서는 `nf_conntrack_max` 기본값이 버킷 수와 같다(커널 문서 `nf_conntrack-sysctl`). 그 전 커널은 버킷의 4배 또는 8배였다(v5.10 `nf_conntrack_core.c`의 `max_factor`). 실제 값은 `sysctl net.netfilter.nf_conntrack_max`로 본다.
- **상태 기계** — conntrack의 TCP 추적은 SYN·FIN·RST를 보고 상태를 옮긴다. 상태마다 만료 시간이 다르다(예: established 기본 432,000초).

## 적용 — 풀어나가는 법

### 1. 증상에서 출발해 "누가 막았나"를 가른다

```text
  즉시 "Connection refused"  -> 대상 포트에 리스너 없음(RST) 또는 방화벽 REJECT
  즉시 "No route to host"    -> ICMP host/admin prohibited(방화벽) 또는 라우팅 문제
  오래 멈춘 뒤 타임아웃        -> 경로 어딘가에서 DROP (보안 그룹·NACL·호스트 방화벽)
```

```bash
# 1) 클라이언트 쪽: 5초 안에 응답이 오나
nc -vz -w 5 10.0.0.5 5432

# 2) 패킷을 본다: SYN만 반복되면 DROP, RST/ICMP가 오면 REJECT·리스너 없음
sudo tcpdump -ni any 'host 10.0.0.5 and (tcp port 5432 or icmp)'

# 3) 서버 쪽: 리스너가 있나
ss -ltnp 'sport = :5432'

# 4) 서버 쪽: SYN이 도착은 하나 (도착 안 하면 앞단 보안 그룹·NACL)
sudo tcpdump -ni eth0 'tcp dst port 5432 and tcp[tcpflags] & tcp-syn != 0'
```

### 2. 어느 규칙이 맞았는지 카운터로 본다

```bash
# iptables: 규칙별 패킷·바이트 카운터와 줄 번호
sudo iptables -L INPUT -n -v --line-numbers

# nftables: 전체 규칙
sudo nft list ruleset

# nftables 추적: 특정 패킷에 nftrace 표시 후 경로를 본다
sudo nft insert rule inet filter input tcp dport 5432 meta nftrace set 1   # insert = 체인 맨 앞에 넣어 앞 규칙에 먼저 걸리지 않게
sudo nft monitor trace

# conntrack 항목·통계
sudo conntrack -L -p tcp --dport 5432
sudo conntrack -S
```

### 3. 호스트 방화벽 기본 뼈대 (nftables)

```nft
table inet filter {
  set admin_nets { type ipv4_addr; flags interval; elements = { 10.0.0.0/8 } }

  chain input {
    type filter hook input priority filter; policy drop;
    ct state established,related accept      # 대부분의 패킷은 여기서 끝난다
    ct state invalid drop                    # INVALID는 reject 말고 drop
    iif lo accept
    ip saddr @admin_nets tcp dport 22 accept
    tcp dport { 80, 443 } accept
    meta l4proto tcp reject with tcp reset   # 내부망이면 빠른 실패를 위해 reject
  }
}
```

- `established,related`를 맨 앞에 두면, 규칙 목록 전체를 도는 것은 **연결의 첫 패킷**뿐이다.
- INVALID 패킷에 REJECT를 쓰지 않는다. 원래 패킷이 오래 지연돼 재전송본보다 늦게 도착하면 INVALID로 분류될 수 있다. 거기에 거절 패킷을 보내면 멀쩡한 연결이 끊긴다(`iptables-extensions(8)` 경고).
- 외부 공개 면에서는 DROP, 내부 서비스 간에는 REJECT를 고르는 경우가 많다. DROP은 스캐너에 정보를 덜 주지만, 내부에서는 장애 진단을 몇 분씩 늦춘다.

### 4. 코드에서 증상을 구분해 로그를 남긴다

```java
try (Socket s = new Socket()) {
    s.connect(new InetSocketAddress("10.0.0.5", 5432), 3_000);   // connect 타임아웃 3초
} catch (SocketTimeoutException e) {
    log.warn("connect timeout - 경로 어딘가 DROP 의심 (보안 그룹·NACL·방화벽)", e);
} catch (ConnectException e) {
    log.warn("connect refused - 리스너 없음 또는 REJECT(RST·port-unreachable): {}", e.getMessage(), e);
} catch (NoRouteToHostException e) {
    log.warn("no route to host - REJECT(host/admin prohibited) 또는 라우팅: {}", e.getMessage(), e);
}
```

- connect 타임아웃을 주지 않으면 DROP 경로에서 OS 재시도(리눅스 6.5+ 기본값에서 약 131초, 그 전 커널은 약 127초) 동안 스레드가 묶인다.

### 5. 클라우드·쿠버네티스 정책을 바꿀 때

- 보안 그룹에서 막아도 **추적 중인 기존 연결**은 남는다. 즉시 끊어야 하면 NACL이나 애플리케이션 쪽 차단을 쓴다.
- NACL은 무상태다. 서버가 밖으로 요청을 보낸다면, 응답이 돌아오는 **임시 포트 범위**도 인바운드에서 열어야 한다.
- 쿠버네티스에서 egress 기본 거부를 걸면 DNS(보통 kube-system의 DNS 파드, 53번 포트)도 막힌다. DNS egress를 먼저 허용한다.

## 장애 시나리오와 대처

### 1. drop과 reject를 구분하지 않아 오진한다

- **현상**: "DB가 죽었다"는 알림. 실제로 DB는 멀쩡하고 새 보안 규칙이 배포됐다. 또는 반대로 "방화벽 문제"로 몇 시간 헤맸는데 리스너가 없었다.
- **보이는 형태**
  - DROP: 요청이 수십 초~2분 멈춘 뒤 `ETIMEDOUT`/`SocketTimeoutException`. 스레드 풀이 connect 대기로 가득 찬다.
  - REJECT·리스너 없음: 즉시 `ECONNREFUSED`/`ConnectException: Connection refused`.
  - `tcpdump`: DROP이면 SYN 재전송만 보이고, REJECT면 RST나 ICMP unreachable이 돌아온다.
- **원인**: 증상 차이를 모르고 "연결 실패"로 뭉뚱그렸다. connect 타임아웃이 없어 DROP이 긴 멈춤으로 번졌다.
- **대처**
  - 에러 종류(refused/timeout/unreachable)별로 로그와 지표를 나눈다.
  - connect 타임아웃을 짧게 둔다.
  - 내부망 규칙은 REJECT로 빠르게 실패하게 하는 것을 검토한다.

### 2. 규칙 수천 개 → 선형 매칭 지연

- **현상**: 차단 목록을 매일 자동으로 추가했더니, 몇 달 뒤 새 연결 지연이 늘고 CPU softirq 사용률이 오른다.
- **보이는 형태**
  - `iptables -S | wc -l`이 수만 줄이다.
  - 첫 패킷 지연(연결 수립 시간)이 늘고, `top`의 `si`(softirq)가 높다.
  - 규칙 갱신(`iptables-restore`)이 몇 초씩 걸린다.
- **원인**: 체인 규칙은 선형 탐색이다. 연결의 첫 패킷마다 앞쪽 규칙을 전부 비교한다.
- **대처**
  - 주소 목록은 ipset `hash:ip`/`hash:net`이나 nftables 이름 있는 집합으로 옮긴다. 규칙은 하나만 남긴다.
  - 분기가 많으면 판정 사상(`vmap`)을 쓴다.
  - `established,related accept`를 맨 앞에 둔다.

### 3. 규칙을 지웠는데 트래픽이 계속 흐른다 (또는 반대로 즉시 끊긴다)

- **현상**: 침해 대응으로 보안 그룹에서 공격자 IP 허용을 지웠는데 기존 세션이 계속 살아 있다.
- **보이는 형태**: 규칙 변경 뒤에도 해당 연결의 패킷이 흐른다(흐름 로그·`ss`).
- **원인**
  - 상태 방화벽은 추적 중인 연결을 기존 판정으로 계속 통과시킨다. AWS 보안 그룹은 규칙이 바뀌어도 추적 연결을 즉시 끊지 않는다(AWS 문서).
  - 리눅스에서도 `established,related accept`가 앞에 있으면 기존 연결은 새 규칙을 거치지 않는다.
- **대처**
  - 클라우드: 네트워크 ACL로 거부 규칙을 추가한다(무상태라 기존 연결도 끊긴다).
  - 리눅스: `conntrack -D -s <IP>`로 해당 추적 항목을 지운다(`conntrack(8)`). 또는 앱에서 세션을 끊는다.
  - 반대 방향 주의: 추적하지 않는 흐름(양방향 0.0.0.0/0)은 규칙 변경 즉시 끊긴다.

### 4. 비대칭 라우팅 + 상태 방화벽 → 응답만 버려진다

- **현상**: 요청은 서버에 도착하는데 클라이언트는 타임아웃이다. 경로를 하나 추가한 뒤부터다.
- **보이는 형태**
  - 서버 `tcpdump`에는 SYN과 SYN/ACK가 모두 보인다. 클라이언트에는 SYN/ACK가 오지 않는다.
  - 방화벽 로그에 INVALID drop이 늘어난다.
- **원인**: 요청과 응답이 서로 다른 방화벽을 지난다. 응답 쪽 방화벽은 SYN을 본 적이 없어 연결 상태가 없다. 그래서 응답을 INVALID로 버린다.
- **대처**
  - 요청과 응답이 같은 상태 장비를 지나도록 라우팅을 대칭으로 맞춘다.
  - AWS도 비대칭 라우팅 토폴로지는 가능하면 피하라고 권한다(연결 추적 모범 사례).

### 5. 쿠버네티스 egress 기본 거부 → 이름 해석 실패

- **현상**: 네임스페이스에 "기본 거부" 정책을 건 직후, 모든 외부 호출이 실패한다.
- **보이는 형태**
  - Java `UnknownHostException`, Node `getaddrinfo EAI_AGAIN`(해석기 무응답 — 이름이 없다는 `ENOTFOUND`가 아니다, 52번).
  - IP로 직접 부르면 허용 규칙대로 동작한다.
- **원인**: egress가 격리되면 DNS 질의(53번 포트)도 허용 목록에 있어야 한다. 이를 빠뜨렸다.
- **대처**: DNS 파드(또는 노드 로컬 DNS)로 가는 UDP·TCP 53번 egress를 먼저 허용한다. 그 뒤 서비스별 egress를 연다.

## 핵심 문장

- 방화벽 규칙은 위에서부터 처음 맞는 것이 이기고, 끝까지 안 맞으면 체인 정책이 적용된다. 체인 규칙은 선형 탐색이다.
- 상태 방화벽은 conntrack으로 연결을 기억해 응답을 자동 허용한다. `established,related`를 맨 앞에 두면 긴 규칙 목록은 연결의 첫 패킷만 거친다.
- DROP은 조용히 버려 클라이언트가 SYN을 재전송하다 타임아웃(리눅스 6.5+ 기본값에서 약 131초, 그 전 커널은 약 127초)되고, REJECT는 즉시 `ECONNREFUSED`나 `EHOSTUNREACH`로 실패시킨다.
- 규칙이 수천 개면 ipset·nftables 집합·판정 사상으로 "규칙 N개의 선형 비교"를 "조회 1번"으로 바꾼다.
- 보안 그룹은 상태·허용만·인스턴스 단위, 네트워크 ACL은 무상태·번호순·서브넷 단위다. 상태 장비는 규칙을 바꿔도 추적 중인 연결을 바로 끊지 않는다.

## 관련 주제·근거

- 선행
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — conntrack 테이블·타임아웃
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — RST의 의미
  - [09-icmp-ping-traceroute](../09-icmp-ping-traceroute/2-summary.md) — ICMP 오류 메시지
- 연결
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md) — SYN 재전송·connect.
  - [50-network-diagnostics](../50-network-diagnostics/2-summary.md) — `tcpdump`·`ss`·`mtr`.
  - 46 로드밸런서·프록시 — [systems/server-design/02-request-path.md](../../systems/server-design/02-request-path.md)
- `iptables(8)` — TARGETS, TABLES, `-L`·`-v`·`--line-numbers` <https://man7.org/linux/man-pages/man8/iptables.8.html>
- `iptables-extensions(8)` — conntrack(`--ctstate`), set(`--match-set`), REJECT(`--reject-with`, INVALID 경고) <https://man7.org/linux/man-pages/man8/iptables-extensions.8.html>
- `nft(8)` — 체인 정책, SETS·MAPS, REJECT STATEMENT, `meta nftrace`·`monitor trace` <https://manpages.debian.org/bookworm/nftables/nft.8.en.html>
- `conntrack(8)` — `-L`·`-D`·`-S`·`-s` <https://manpages.debian.org/bookworm/conntrack/conntrack.8.en.html>
- `ipset(8)` — hash 타입 <https://manpages.debian.org/bookworm/ipset/ipset.8.en.html>
- `tcp(7)` — `tcp_syn_retries` <https://man7.org/linux/man-pages/man7/tcp.7.html>
- 커널 문서 `ip-sysctl` — `tcp_syn_retries`(6.5+ 기본값에서 약 131초)·`tcp_syn_linear_timeouts`(기본 4) <https://docs.kernel.org/networking/ip-sysctl.html>
- 커널 문서 `nf_conntrack-sysctl`(5.15+: max = buckets) vs v5.10 `net/netfilter/nf_conntrack_core.c`(`max_factor` 8/4) <https://docs.kernel.org/networking/nf_conntrack-sysctl.html>
- Linux 소스 `net/ipv4/icmp.c`(`icmp_err_convert`) · `net/ipv4/tcp_ipv4.c`(`tcp_v4_err`) <https://github.com/torvalds/linux/tree/master/net/ipv4>
- OpenJDK `src/java.base/unix/native/libnio/ch/Net.c`(`handleSocketError`: ECONNREFUSED·ETIMEDOUT → `ConnectException`, EHOSTUNREACH → `NoRouteToHostException`) · `NioSocketImpl.java`("Connect timed out") <https://github.com/openjdk/jdk>
- Linux 커널 문서 `Documentation/networking/nf_conntrack-sysctl.rst` <https://docs.kernel.org/networking/nf_conntrack-sysctl.html>
- AWS VPC "Infrastructure security"(보안 그룹 vs 네트워크 ACL) <https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html>
- AWS EC2 "Security group connection tracking" <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html>
- Kubernetes "Network Policies" <https://kubernetes.io/docs/concepts/services-networking/network-policies/>
- Kubernetes 블로그 "NFTables mode for kube-proxy"(2025-02-28) <https://kubernetes.io/blog/2025/02/28/nftables-kube-proxy/>
