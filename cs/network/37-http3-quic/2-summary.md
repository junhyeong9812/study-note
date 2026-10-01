# network/37-http3-quic — HTTP/3와 QUIC: 스트림 독립·연결 마이그레이션·0-RTT — 정리 (힌트)

## 해결하는 문제

HTTP/2는 HTTP 층의 줄서기를 없앴지만 TCP 위에 있어서 세 가지가 남는다(36번).

```text
  1. TCP head-of-line   세그먼트 하나 손실 -> 그 뒤 데이터를 기다리는 스트림 전부 정지
  2. 연결 준비 비용       TCP 1 RTT + TLS 1.3 1 RTT = 요청 전 2 RTT
  3. 주소에 묶인 연결     연결 = (출발 IP, 출발 포트, 도착 IP, 도착 포트)
                        Wi-Fi -> LTE로 바뀌면 IP가 바뀌어 연결이 끊긴다
```

TCP는 운영체제 커널과 수많은 중간 장비에 박혀 있어 고치기 어렵다.\
그래서 QUIC은 UDP 위에 전송 기능(신뢰성·혼잡 제어·스트림)을 새로 만들고 TLS 1.3을 그 안에 넣었다.\
HTTP/3는 HTTP 의미론을 QUIC 위에 올린 것이다(RFC 9114).

  - *UDP*: 연결도 순서 보장도 없는 가장 단순한 전송 프로토콜이다. 포트 번호와 체크섬 정도만 있다(14번).

쉬운 예: 이사 짐을 트럭 한 대(TCP)에 싣고 상자마다 번호를 붙였다.\
3번 상자가 떨어지면 트럭 전체가 멈추고 3번을 다시 가져올 때까지 기다린다.\
QUIC은 오토바이 여러 대(스트림)가 같은 길을 나눠 쓰는 방식이다. 한 대가 멈춰도 다른 오토바이는 계속 간다.\
그리고 배달원을 주소가 아니라 휴대폰 번호(연결 ID)로 찾는다. 이사를 가도 번호는 그대로다.

실무 예:
- 모바일 앱이 Wi-Fi에서 LTE로 넘어가도 다운로드가 끊기지 않는다.
- 손실이 있는 망에서 무관한 자원 로딩이 서로 막지 않는다.
- 반대로 UDP를 막는 회사망에서는 HTTP/3가 안 되고 TCP로 되돌아가야 한다.

## 동작·원리

### 1. 계층 비교

```text
       HTTP/2                         HTTP/3
  +------------------+           +------------------+
  | HTTP 의미론       |           | HTTP 의미론       |
  +------------------+           +------------------+
  | HTTP/2 프레이밍   |           | HTTP/3 프레이밍   |
  | HPACK            |           | QPACK            |
  +------------------+           +------------------+
  | TLS 1.2/1.3      |           | QUIC             |
  +------------------+           |  - 스트림 다중화   |
  | TCP              |           |  - 신뢰성·혼잡제어 |
  |  - 신뢰성·혼잡제어 |           |  - TLS 1.3 내장   |
  +------------------+           +------------------+
  | IP               |           | UDP / IP         |
  +------------------+           +------------------+
```

- 스트림 다중화와 스트림별 흐름 제어는 HTTP/2에서는 HTTP 층이 했지만, HTTP/3에서는 QUIC이 맡는다(RFC 9114 §1.2).
- 신뢰성은 **스트림 단위**, 혼잡 제어는 **연결 전체** 단위다(§1.2).
- QUIC은 대부분 사용자 공간 라이브러리로 구현된다. 커널을 바꾸지 않고 배포할 수 있다.

### 2. 핸드셰이크 — 전송과 암호를 한 번에

RFC 9000 Figure 5를 줄인 그림이다.

```text
  Client                                                   Server
  Initial[0]: CRYPTO[ClientHello]  ------------------------>
                                         Initial[0]: CRYPTO[ServerHello]
                                         Handshake[0]: CRYPTO[EE, CERT, CV, FIN]
                                    <--- 1-RTT[0]: STREAM (0.5-RTT 데이터)
  Handshake[0]: CRYPTO[FIN]
  1-RTT[0]: STREAM[0, "GET /"]     ------------------------>     (1 RTT 뒤 요청)
                                    <--- 1-RTT: HANDSHAKE_DONE, 응답
```

- TCP처럼 따로 연결을 맺는 왕복이 없다. 전송 핸드셰이크와 TLS 1.3 핸드셰이크가 합쳐져 있다(RFC 9000 §7).
- 그래서 새 연결은 **1 RTT 뒤** 요청을 보낸다. TCP + TLS 1.3은 2 RTT 뒤다.
- 이전 연결의 재개 정보가 있으면 **0-RTT**로 첫 패킷에 요청을 싣는다(Figure 6). 아래 7절의 대가가 따른다.
- 패킷 종류마다 다른 키로 보호한다. Initial 키는 클라이언트 첫 Initial의 Destination Connection ID에서 유도하므로 관찰자도 계산할 수 있다. 그래서 Initial은 기밀성·무결성 보호가 있다고 보지 않는다(RFC 9001 §5, §5.2). Handshake·1-RTT 키는 TLS 키 교환으로 얻은 비밀에서 나온다.

### 3. HTTP/3를 어떻게 알고 시작하나 — 발견과 폴백

```text
  1) 첫 접속은 TCP(HTTP/1.1 또는 h2)
     응답 헤더: Alt-Svc: h3=":443"; ma=86400
  2) 다음 요청부터 클라이언트가 UDP 443으로 QUIC 시도 (ALPN "h3")
  3) QUIC 실패(UDP 차단 등)  ->  TCP 기반 HTTP로 계속
```

- 서버는 `Alt-Svc` 응답 헤더나 HTTP/2 `ALTSVC` 프레임으로 HTTP/3 엔드포인트를 알린다(RFC 9114 §3.1.1).
  - `ma`(max-age)를 생략하면 24시간 동안 유효하다(RFC 7838 §3.1).
- DNS의 HTTPS 레코드(RFC 9460)로 첫 접속 전에 `h3` 지원을 알릴 수도 있다.
- UDP 차단 같은 연결 문제로 QUIC이 실패하면 클라이언트는 TCP 기반 HTTP를 시도해야 한다(SHOULD, RFC 9114 §3.1).
- RFC 9308 §2는 측정 연구에서 네트워크의 3~5%가 UDP를 전부 막았다고 인용한다. 그래서 폴백은 선택이 아니라 필수 설계다.

### 4. 스트림 독립 — 손실이 그 스트림만 막는다

```text
  UDP 데이터그램:  P10[s0 데이터]  P11[s4 데이터]  P12[s8 데이터]
  P11 손실

  QUIC 수신 측:
    s0 : P10 도착 -> 바로 앱에 전달
    s4 : P11 없음 -> s4만 대기 (재전송 기다림)
    s8 : P12 도착 -> 바로 앱에 전달       <- TCP였다면 여기서 막혔다
```

- 순서 보장은 **스트림마다** 따로 한다. 한 스트림 안에서는 바이트 순서대로 앱에 넘긴다(RFC 9000 §2.2).
- 스트림 ID는 62비트이고, 하위 2비트가 종류를 나타낸다(RFC 9000 §2.1).

```text
  하위 2비트   종류                        ID 예
  0x0         클라이언트 시작, 양방향        0, 4, 8, ...   <- HTTP/3 요청·응답
  0x1         서버 시작, 양방향              1, 5, 9, ...
  0x2         클라이언트 시작, 단방향        2, 6, 10, ...  <- 제어·QPACK 스트림 등
  0x3         서버 시작, 단방향              3, 7, 11, ...
```

- HTTP/2와 반대로 **클라이언트 양방향 스트림이 짝수**다. HTTP/3 요청 하나가 클라이언트 양방향 스트림 하나를 쓴다.
- 연결 설정(SETTINGS)은 단방향 제어 스트림으로 따로 보낸다(RFC 9114 §6.2.1).

### 5. 패킷 번호 공간과 손실 탐지

```text
  공간            담는 패킷              번호
  Initial        Initial              0, 1, 2 ...
  Handshake      Handshake            0, 1, 2 ...
  Application    0-RTT, 1-RTT         0, 1, 2, 3 ...   (재전송도 새 번호)

  TCP:  seq=1000 전송 -> 손실 -> seq=1000 재전송 -> ACK 1000 은 원본? 재전송?  (모호)
  QUIC: pn=7 전송 -> 손실 -> 같은 프레임을 pn=12로 재전송 -> ACK 12 = 재전송본  (명확)
```

- 패킷 번호는 공간마다 따로 세고, 한 공간 안에서 **단조 증가**하며 재사용하지 않는다(RFC 9000 §12.3, RFC 9002 §3).
- 잃은 데이터는 **새 패킷 번호**의 새 패킷에 다시 싣는다. 그래서 ACK가 원본용인지 재전송용인지 헷갈리지 않는다(RFC 9002 §4.2). TCP의 "재전송 모호성" 문제가 없다.
- 전송 순서는 패킷 번호가, 전달 순서는 STREAM 프레임의 오프셋이 맡는다.
- 손실 판정(RFC 9002 §6.1): 전제는 "그 패킷보다 **나중에 보낸 패킷이 확인(ACK)됐다**"이다. 그 위에서 둘 중 하나면 손실로 본다.
  - 패킷 임계: 확인된 패킷보다 번호가 3(`kPacketThreshold`, 권장값) 이상 앞선다. 확인된 뒤 패킷은 하나면 된다(예시: pn=7 미확인, pn=10 확인 → 7 손실).
  - 시간 임계: 보낸 지 `max(9/8 × max(smoothed_rtt, latest_rtt), 1ms)`가 지났다(§6.1.2).
  - 나중 패킷이 하나도 확인되지 않으면 이 판정은 쓰지 않고 PTO 경로로 간다(§6.2).
- TCP의 RTO 대신 PTO(Probe Timeout)로 탐침 패킷을 보낸다(RFC 9002 §4.7, §6.2).

### 6. 연결 ID와 마이그레이션

```text
  Wi-Fi  (192.0.2.10:51000)  ---- DCID=0xA1B2 ---->  Server
                                   |
                  (LTE로 전환, 주소가 바뀜)
                                   v
  LTE  (198.51.100.7:40123)  ---- DCID=0xC3D4 ---->  Server
                                                      "이 연결 ID는 아는 연결"
         <---- PATH_CHALLENGE(랜덤 8바이트) --------
         ----- PATH_RESPONSE(같은 값) ------------->   새 경로 검증 완료
         <---- 데이터 계속 -------------------------
```

- 연결은 4-튜플이 아니라 **연결 ID**로 식별된다(RFC 9000 §5.1). 주소가 바뀌어도 패킷이 같은 연결로 간다.
- 새 주소로 옮겨도 관찰자가 같은 연결임을 알아채지 못하게, 경로를 바꿀 때 다른 연결 ID를 쓴다(§5.1, §9.5).
- 마이그레이션은 핸드셰이크 확정 전에는 할 수 없다(MUST NOT, §9). 이 RFC에서는 **클라이언트만** 주소를 옮긴다(예외: 서버가 알린 `preferred_address`로 옮기는 경우, §9.6).
- 주소 변경을 감지하면 경로 검증(PATH_CHALLENGE/PATH_RESPONSE)을 해야 한다(MUST, §9, §8.2). 전에 이미 검증한 주소로 돌아온 경우는 예외다. 의도치 않은 변경(NAT rebinding)도 마찬가지다.
  - *NAT rebinding*: NAT 장비가 idle 뒤 같은 흐름에 새 외부 포트·IP를 배정하는 것이다.
- 서버가 마이그레이션을 받을 수 없는 구조면 `disable_active_migration` 전송 파라미터로 알린다(SHOULD, §5.2.3).
  - 예: 4-튜플 해시로만 분산하는 L4 로드밸런서 뒤. 주소가 바뀌면 다른 서버로 가기 때문이다.

### 7. 0-RTT와 증폭 방지

```text
  0-RTT:  Initial[ClientHello] + 0-RTT[요청]  --->   첫 비행에 요청이 실린다
          공격자가 녹화해 다시 보내면 서버가 한 번 더 처리할 수 있다 (재전송 공격)
```

- 0-RTT는 TLS 1.3 early data와 같은 재전송 위험이 있다(RFC 9001 §9.2). QUIC 프레임 처리 자체는 재전송돼도 안전하지만, 그 안의 **앱 요청**은 아니다.
- HTTP/3에서 0-RTT를 쓰면 RFC 8470의 재전송 대책(`Early-Data` 헤더, `425 Too Early`)을 적용해야 한다(MUST, RFC 9114 §10.9). 세부는 [29번](../29-tls-handshake/2-summary.md).
- 증폭 방지: 서버는 클라이언트 주소를 검증하기 전에는 받은 바이트의 **3배**까지만 보낸다(MUST, RFC 9000 §8.1).
  - 위조된 출발 주소로 작은 요청을 보내 큰 응답을 남에게 쏘는 공격을 막는다.
- 클라이언트의 Initial 패킷을 담은 데이터그램은 최소 1,200바이트로 채워야 한다(MUST, §14.1).
  - 그래서 경로가 1,200바이트 UDP 페이로드를 못 나르면 QUIC을 쓸 수 없다(MUST NOT, §14).
  - UDP 데이터그램은 IP 단편화하면 안 된다(MUST NOT, §14). 10번(MTU·PMTUD)과 이어진다.

### 8. QPACK — 순서가 보장되지 않는 곳의 헤더 압축

```text
  HPACK(HTTP/2): 동적 테이블 갱신이 "모든 스트림의 프레임 순서"에 의존
                 -> QUIC에서는 스트림 간 순서가 없으므로 그대로 쓰면 HoL 재발

  QPACK(HTTP/3): 동적 테이블 갱신을 별도 단방향 "인코더 스트림"으로 보냄
                 요청 스트림은 "필요한 삽입 수(Required Insert Count)"를 적음
                 아직 그 삽입이 안 왔으면 그 요청 스트림만 대기(blocked)
```

- HPACK을 HTTP/3에 쓰면 모든 스트림에 걸친 순서 가정 때문에 HoL이 생긴다(RFC 9204 §1).
- QPACK은 막힐 수 있는 스트림 수를 받는 쪽이 `SETTINGS_QPACK_BLOCKED_STREAMS`로 제한한다(§2.1.2). 기본값은 0이다(§5). 즉 설정을 올리지 않으면 동적 테이블을 "막힐 위험 없이"만 쓴다.
  - 동적 테이블 크기(`SETTINGS_QPACK_MAX_TABLE_CAPACITY`)도 기본값이 0이다(§5). 이것까지 올리지 않으면 동적 테이블 자체가 없고, 정적 테이블과 리터럴만 쓴다.
- 인코더는 압축률과 막힘 위험 사이에서 고른다. 확인된 항목만 참조하면 막히지 않지만 압축이 덜 된다(§2.1.2).

### 9. 중간 장비가 보는 QUIC

- QUIC은 헤더 대부분과 페이로드를 보호한다(Initial은 관찰자도 풀 수 있는 키, 2절). 방화벽은 TCP처럼 SYN·FIN·RST로 연결 시작·끝을 볼 수 없다.
- 그래서 상태 방화벽·NAT는 **타이머나 LRU 축출**로 QUIC 흐름 상태를 지운다(RFC 9312 §4.2).
  - RFC 4787은 UDP 상태 타임아웃을 대부분 2분 이상으로 요구하지만, 실제로 30~60초를 겪는다(RFC 9312 §4.2).
  - RFC 9312는 QUIC에 최소 2분을 권한다.
- ClientHello가 암호화되지 않은 경우, Initial 키를 계산해 SNI를 읽을 수는 있다(RFC 9312 §3.4.1). 하지만 버전별 절차가 필요해 오래된 장비는 못 한다.
- 보안 장비가 QUIC 내용을 검사하지 못해 UDP 443을 막고 TCP로 강제하는 운영도 흔하다 [?].

## 쓰이는 자료구조·알고리즘

- **패킷 번호 공간 3개** — 공간마다 독립 카운터와 "보낸 패킷 → 시각·크기·담은 프레임" 표를 둔다. ACK가 오면 표에서 지우고, 손실이면 담았던 프레임을 새 패킷으로 다시 만든다(RFC 9002 §3, 부록 A).
- **ACK 범위(range) 집합** — ACK 프레임은 받은 번호를 구간 목록으로 알린다. 구현은 정렬된 구간 목록을 병합하며 관리한다(RFC 9000 §13.2.3). [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- **손실 탐지 = 뒤 패킷 확인 + (패킷 임계(3) 또는 시간 임계(9/8 RTT))** — TCP fast retransmit·RACK과 같은 계열이다(RFC 9002 §6.1).
- **RTT 추정 = 지수 가중 이동 평균(EWMA)** — `smoothed_rtt = 7/8 × smoothed_rtt + 1/8 × 표본`, `rttvar = 3/4 × rttvar + 1/4 × |차이|`(RFC 9002 §5.3). TCP RTO 계산과 같은 형태다.
- **연결 ID → 연결 해시 맵** — 4-튜플 대신 연결 ID로 들어온 패킷의 연결을 찾는다. 서버 여러 대면 LB도 연결 ID로 라우팅해야 한다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **스트림 재조립 버퍼** — 오프셋 기반으로 도착한 조각을 끼워 넣고, 앞이 채워진 만큼만 앱에 넘긴다. 스트림마다 따로 있다.
- **QPACK 동적 테이블 + 삽입 카운트** — HPACK 테이블에 "몇 번째 삽입까지 받았나" 카운터를 더해 막힘 여부를 판정한다(RFC 9204 §2.1.2).

## 적용 — 풀어나가는 법

### 1. HTTP/3가 되는지 확인한다

```bash
# 서버가 h3를 광고하는가
curl -sI https://www.example.com/ | grep -i '^alt-svc'

# HTTP/3로 시도하되 안 되면 폴백 (curl이 HTTP/3 지원으로 빌드돼야 함)
curl -sI --http3 https://www.example.com/ -o /dev/null -w '%{http_version}\n'

# 폴백 없이 HTTP/3만 — UDP가 막혔는지 가르는 데 쓴다
curl -sI --http3-only https://www.example.com/ -o /dev/null -w '%{http_version}\n'

# DNS HTTPS 레코드 (HTTPS 타입을 아는 dig 필요)
dig +short www.example.com HTTPS

# UDP 443 패킷이 나가고 돌아오는가
tcpdump -nn -i any 'udp port 443'
```

- `--http3-only`가 타임아웃이고 `--http3`는 성공(HTTP/1.1·2로)하면 UDP 경로 문제일 가능성이 크다.
- 브라우저 개발자 도구의 Network 탭 "Protocol" 열에 `h3`가 보이면 HTTP/3다.

### 2. 서버 설정(nginx 예)

```nginx
server {
    listen 443 quic reuseport;     # UDP 443
    listen 443 ssl;                # TCP 443 — 폴백용, 같은 포트 권장
    http2 on;
    ssl_certificate     /etc/ssl/site.crt;
    ssl_certificate_key /etc/ssl/site.key;
    add_header Alt-Svc 'h3=":443"; ma=86400';
}
```

- nginx의 HTTP/3 모듈은 1.25.0부터 있고 문서상 "실험적"이다. `--with-http_v3_module`로 빌드해야 한다(nginx 문서).
- 방화벽·보안 그룹에서 **UDP** 443을 연다. TCP 443만 열어 두면 광고만 하고 실제로는 폴백한다.
- 로드밸런서가 UDP를 지원하는지, 연결 ID 기반 라우팅을 하는지 확인한다.

### 3. 코드에서

HTTP/3 클라이언트 지원은 런타임마다 다르다. 서버 쪽에서 광고 헤더를 붙이는 것은 어디서나 같다.

```ts
// Node/Express — TLS를 끝내는 앞단(CDN·LB)이 HTTP/3를 제공할 때 광고
app.use((req, res, next) => {
  res.setHeader('Alt-Svc', 'h3=":443"; ma=3600');   // ma를 짧게 두면 문제 시 빨리 철회된다
  next();
});
```

- 광고를 **철회**하려면 `Alt-Svc: clear`를 보낸다(RFC 7838 §3). 캐시된 광고가 남아 있는 동안은 클라이언트가 계속 시도할 수 있으니 `ma`를 짧게 두는 편이 운영에 안전하다.

### 4. 운영 점검 순서

1. UDP 443이 양방향으로 열려 있는가(보안 그룹·방화벽·LB).
2. 경로가 1,200바이트 이상 UDP 페이로드를 나르는가(터널·VPN 구간).
3. LB가 4-튜플 해시만 쓰면 마이그레이션·NAT rebinding 때 연결이 깨진다. 연결 ID 라우팅을 쓰거나 `disable_active_migration`을 켠다.
4. 0-RTT를 켰다면 비멱등 요청을 막는가(425 Too Early).
5. 중간 장비의 UDP 상태 타임아웃이 짧다면 idle 연결을 오래 두지 않는다.

## 장애 시나리오와 대처

### 1. UDP 차단망에서 폴백이 늦어 첫 로딩이 느리다

- **현상**: 특정 회사망·공공 Wi-Fi 사용자만 첫 페이지 로딩이 수 초 늦다. 두 번째부터는 괜찮거나 계속 느리다.
- **보이는 형태**
  - `curl --http3-only`는 타임아웃, `curl --http3`는 HTTP/2로 성공한다.
  - `tcpdump 'udp port 443'`에 클라이언트 Initial 패킷(약 1,200바이트)만 반복되고 응답이 없다.
  - 브라우저 Protocol 열이 `h2`다.
- **원인**
  - 네트워크가 UDP(또는 UDP 443)를 막는다. RFC 9308 §2가 인용하는 측정에서 3~5%의 네트워크가 UDP를 전부 막았다.
  - 클라이언트가 QUIC을 먼저 시도하고 실패를 판단할 때까지 기다린 뒤 TCP로 넘어가면 그 시간만큼 늦는다. 두 방식을 동시에 경주시키는지는 클라이언트 구현마다 다르다.
- **대처**
  - 서버는 TCP 경로를 항상 함께 제공한다. HTTP/3 전용 엔드포인트를 두지 않는다.
  - 클라이언트를 직접 만든다면 QUIC과 TCP를 짧은 간격으로 경주시키고 먼저 성공한 쪽을 쓴다.
  - 문제 구간이 확인되면 `Alt-Svc`의 `ma`를 줄이거나 `Alt-Svc: clear`로 광고를 철회한다.

### 2. 방화벽·NAT가 QUIC을 인식하지 못해 idle 뒤 연결이 조용히 죽는다

- **현상**: 앱을 잠깐 두었다가 다시 쓰면 첫 요청이 수 초 멈췄다가 실패하거나 재연결한다.
- **보이는 형태**
  - `tcpdump`에서 클라이언트가 보낸 1-RTT 패킷에 응답이 없다. 재전송(PTO 탐침)만 반복된다.
  - 서버 쪽에는 그 패킷이 도착하지 않는다.
  - 일정 시간(수십 초) 이상 쉬었을 때만 재현된다.
- **원인**
  - 상태 방화벽·NAT는 QUIC의 시작·끝 신호를 볼 수 없어 **타이머**로 상태를 지운다(RFC 9312 §4.2).
  - UDP 상태 타임아웃이 30~60초로 짧은 장비가 있다(RFC 9312 §4.2). 상태가 지워지면 서버로 가는 패킷이나 돌아오는 패킷이 버려진다.
  - NAT가 새 포트를 배정하면(NAT rebinding) 서버는 같은 연결 ID를 보고 경로 검증을 한다. 하지만 L4 LB가 4-튜플로 분산하면 다른 서버로 가서 연결이 끊긴다.
- **대처**
  - 응답을 기다리는 동안은 PING으로 연결을 유지한다. 오래 쉬는 연결은 굳이 유지하지 말고, 필요할 때 재개(0-RTT 포함)한다(RFC 9308 §3.2).
  - 방화벽 UDP 상태 타임아웃을 QUIC에 대해 2분 이상으로 둔다(RFC 9312 권고).
  - 서버 LB는 연결 ID 기반 라우팅을 쓰거나, 못 쓰면 `disable_active_migration`을 광고한다(RFC 9000 §5.2.3).

### 3. 보안 장비가 UDP 443을 막거나 통과시켜 정책이 어긋난다

- **현상 A**: 사내 보안팀이 "웹 필터를 우회하는 트래픽이 있다"고 보고한다.
- **현상 B**: 반대로 보안 장비 정책 때문에 HTTP/3가 전혀 안 된다.
- **보이는 형태**: A는 프록시·필터 로그에 없는 도메인 접속이 방화벽의 UDP 443 흐름으로만 보인다. B는 1번과 같은 폴백 증상이다.
- **원인**
  - 기존 TLS 검사 장비는 TCP 위 TLS를 전제로 만들어졌다. QUIC은 전송 헤더까지 암호화되어 같은 방식으로 검사할 수 없다.
  - Initial에서 SNI를 꺼내려면 QUIC 버전별 절차가 필요하다(RFC 9312 §3.4.1). 이를 지원하지 않는 장비는 QUIC을 "모르는 UDP"로 다룬다.
- **대처**
  - 조직 정책에 맞춰 명시적으로 결정한다. 검사가 필요하면 UDP 443을 막아 TCP로 폴백시키고, 서비스는 TCP 경로로 정상 동작하게 한다.
  - QUIC을 이해하는 장비로 교체하는 경우 SNI 기반 정책이 되는지 확인한다.

### 4. 작은 MTU 경로에서 핸드셰이크가 실패한다

- **현상**: VPN·터널을 거치는 사용자만 HTTP/3 연결이 안 된다. TCP는 된다.
- **보이는 형태**: 클라이언트 Initial(1,200바이트 이상) 데이터그램이 서버에 도착하지 않는다. ICMP "fragmentation needed"가 보이거나 아무 응답이 없다.
- **원인**: QUIC은 1,200바이트 이상 UDP 페이로드를 나를 수 있는 경로를 전제로 한다. 못 나르면 QUIC을 쓰면 안 된다(MUST NOT, RFC 9000 §14). IP 단편화도 금지다.
- **대처**: 터널 MTU를 늘리거나, 해당 경로에서는 TCP 폴백을 받아들인다. PMTUD 자체는 10번에서 다룬다.

### 5. 0-RTT 재전송으로 요청이 두 번 처리된다

- **현상**: 모바일 사용자에게서 드물게 같은 요청이 두 번 들어온다.
- **보이는 형태**: 같은 요청이 짧은 간격으로 두 번 로그에 찍히고, 하나가 early data로 들어왔다.
- **원인**: 0-RTT 데이터는 재전송 보호가 불완전하다(RFC 9001 §9.2). 공격자 재전송이나 클라이언트 재시도가 같은 요청을 다시 전달했다.
- **대처**: 0-RTT는 안전·멱등 요청에만 허용하고, 나머지는 `425 Too Early`로 돌려보낸다(RFC 8470, RFC 9114 §10.9). 쓰기 API는 멱등 키를 둔다([ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)).

## 핵심 문장

- QUIC은 UDP 위에 스트림·신뢰성·혼잡 제어를 만들고 TLS 1.3을 내장해, 새 연결을 1 RTT(재개 시 0-RTT)로 연다.
- 순서 보장이 스트림마다 따로라서, 패킷 손실은 그 데이터를 담은 스트림만 멈춘다. HTTP/2의 TCP head-of-line blocking이 사라진다.
- 연결을 4-튜플이 아니라 연결 ID로 식별해 클라이언트 주소가 바뀌어도 경로 검증 뒤 연결을 이어 간다.
- 패킷 번호는 공간별로 단조 증가하고 재전송도 새 번호를 쓰므로, TCP의 재전송 모호성 없이 손실을 판정한다.
- UDP 차단·짧은 UDP 상태 타임아웃·작은 MTU 때문에 QUIC은 실패할 수 있다. 그래서 TCP 기반 HTTP로의 폴백이 필수다.

## 관련 주제·근거

- 선행
  - `36-http2-multiplexing` — [36번](../36-http2-multiplexing/2-summary.md)
  - [14-udp](../14-udp/2-summary.md)
  - `29-tls-handshake` — TLS 1.3과 0-RTT. [29번](../29-tls-handshake/2-summary.md)
- 후속·연결
  - [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md) — 1,200바이트 요구와 단편화 금지.
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — UDP 상태 타임아웃.
  - [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) — 재전송 모호성과 비교.
  - [48-firewalls-and-network-policy](../48-firewalls-and-network-policy/2-summary.md)
  - `35-http-connection-management` — [35번](../35-http-connection-management/2-summary.md)
- RFC 9000 QUIC Transport <https://www.rfc-editor.org/rfc/rfc9000>
  - §2.1 스트림 ID 종류 · §2.2 스트림 내 순서 전달 · §5.1 연결 ID · §5.2.3 단순 LB 고려 · §7 결합 핸드셰이크(Figure 5·6)
  - §8.1 주소 검증과 3배 증폭 제한 · §8.2 경로 검증 · §9 연결 마이그레이션 · §10.1 idle timeout · §12.3 패킷 번호 공간 · §13.2.3 ACK 범위 · §14 데이터그램 크기(1,200바이트, 단편화 금지)
- RFC 9001 Using TLS to Secure QUIC §5·§5.2 패킷 보호와 Initial 키 · §9.2 0-RTT 재전송 <https://www.rfc-editor.org/rfc/rfc9001>
- RFC 9002 QUIC Loss Detection and Congestion Control <https://www.rfc-editor.org/rfc/rfc9002>
  - §3 설계 · §4.1 분리된 번호 공간 · §4.2 단조 증가 번호 · §4.7 PTO · §5.3 RTT EWMA · §6.1 손실 임계(3, 9/8)
- RFC 9114 HTTP/3 <https://www.rfc-editor.org/rfc/rfc9114>
  - §1.2 QUIC에 위임한 기능 · §3.1 발견과 TCP 폴백 · §3.1.1 Alt-Svc · §5.1 idle 연결 · §5.2 GOAWAY · §6.2.1 제어 스트림 · §10.9 Early Data
- RFC 9204 QPACK §1 · §2.1.2 blocked streams · §5 설정 기본값 <https://www.rfc-editor.org/rfc/rfc9204>
- RFC 7838 HTTP Alternative Services(`ma` 기본 24시간, `clear`) <https://www.rfc-editor.org/rfc/rfc7838>
- RFC 9460 SVCB·HTTPS DNS 레코드 <https://www.rfc-editor.org/rfc/rfc9460>
- RFC 8470 Using Early Data in HTTP <https://www.rfc-editor.org/rfc/rfc8470>
- RFC 9308 Applicability of QUIC §2 폴백 필요성(UDP 차단 3~5%) · §3.2 keep-alive vs 재개 <https://www.rfc-editor.org/rfc/rfc9308>
- RFC 9312 Manageability of QUIC §3.4.1 SNI 추출 · §4.2 상태 처리와 타임아웃 <https://www.rfc-editor.org/rfc/rfc9312>
- nginx `ngx_http_v3_module` <https://nginx.org/en/docs/http/ngx_http_v3_module.html>
- curl `--http3`·`--http3-only` <https://curl.se/docs/manpage.html>
