# 네트워크 — `cs/network/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §7에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 1 · 초안(Claude) 52 · 검수 완료 0

> **프로세스 → 소켓 → 커널 스택 → NIC → 스위치(MAC) → 라우터(IP) → … → 역방향 디캡슐화**. 지도(계층·캡슐화)를 먼저 그리고 아래 계층부터 올라온 뒤, 소켓·커널 경로로 "내 프로세스"와 잇고, DNS·TLS·HTTP로 올라가 종합한다.
> 장애의 중심은 TCP(15~22). "TCP 통신 도중 끊기면?"의 본체가 19·20·21이다.
> 뼈대: Kurose & Ross 8판(이하 K&R — 9판도 1~5장 제목 동일 확인, 6~8장 번호는 8판 기준), Stevens 『TCP/IP Illustrated Vol.1』 2판(이하 Stevens — 13·14·17장 외 장 번호 `[?]`), Grigorik 『High Performance Browser Networking』(이하 HPBN — 장 제목으로 인용), Beej's Guide, RFC.

## 7.0 지도

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `layer-map-osi-tcpip` | OSI 7 vs TCP/IP 4계층, 계층별 프로토콜·PDU(세그먼트/패킷/프레임) | 필수 | 초안(Claude) | [01-layer-map-osi-tcpip](01-layer-map-osi-tcpip/) |
| 02 | `encapsulation` | 헤더가 붙고 벗겨지는 과정, 계층별 헤더 필드 | 필수 | 초안(Claude) | [02-encapsulation](02-encapsulation/) |
| 03 | `latency-bandwidth-bdp` | 지연 4요소(처리·큐잉·전송·전파), 대역폭 vs 지연, BDP | 필수 | 초안(Claude) | [03-latency-bandwidth-bdp](03-latency-bandwidth-bdp/) |

## 7.1 링크 계층

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `ethernet-and-mac` | 이더넷 프레임·MAC 주소·충돌 도메인 | 필수 | 초안(Claude) | [04-ethernet-and-mac](04-ethernet-and-mac/) |
| 05 | `arp` | IP→MAC 해석, ARP 캐시, gratuitous ARP | 필수 | 초안(Claude) | [05-arp](05-arp/) |
| 06 | `switching-and-vlan` | 허브 vs 스위치, 자가 학습·플러딩·에이징, VLAN, STP | 권장 | 초안(Claude) | [06-switching-and-vlan](06-switching-and-vlan/) |

## 7.2 네트워크 계층

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 07 | `ip-addressing-cidr` | IPv4/IPv6 주소, 서브넷·CIDR·사설 대역 | 필수 | 초안(Claude) | [07-ip-addressing-cidr](07-ip-addressing-cidr/) |
| 08 | `routing-and-longest-prefix-match` | 라우팅 테이블·**최장 접두사 매칭**·기본 게이트웨이·TTL | 필수 | 초안(Claude) | [08-routing-and-longest-prefix-match](08-routing-and-longest-prefix-match/) |
| 09 | `icmp-ping-traceroute` | ICMP 메시지·ping·traceroute 원리 | 필수 | 초안(Claude) | [09-icmp-ping-traceroute](09-icmp-ping-traceroute/) |
| 10 | `fragmentation-mtu-pmtud` | MTU·IP 단편화·DF·PMTUD | 필수 | 초안(Claude) | [10-fragmentation-mtu-pmtud](10-fragmentation-mtu-pmtud/) |
| 11 | `nat-and-conntrack` | SNAT/DNAT·포트 매핑·연결 추적·idle timeout | 필수 | 초안(Claude) | [11-nat-and-conntrack](11-nat-and-conntrack/) |
| 12 | `dhcp` | 주소 자동 할당·리스 | 권장 | 초안(Claude) | [12-dhcp](12-dhcp/) |
| 13 | `routing-protocols-ospf-bgp` | 링크 상태(OSPF) vs 거리 벡터 vs 경로 벡터(BGP) | 권장 | 초안(Claude) | [13-routing-protocols-ospf-bgp](13-routing-protocols-ospf-bgp/) |

## 7.3 전송 계층 — UDP

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 14 | `udp` | 무연결·포트 다중화·체크섬, 사용처(DNS·QUIC·스트리밍) | 필수 | 초안(Claude) | [14-udp](14-udp/) |

## 7.4 전송 계층 — TCP (장애의 중심)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `tcp-handshake-and-backlog` | 3-way handshake, SYN 큐·accept 큐(listen backlog) | 필수 | 초안(Claude) | [15-tcp-handshake-and-backlog](15-tcp-handshake-and-backlog/) |
| 16 | `tcp-reliability-retransmission` | 시퀀스·누적 ACK·RTO·fast retransmit·SACK | 필수 | 초안(Claude) | [16-tcp-reliability-retransmission](16-tcp-reliability-retransmission/) |
| 17 | `tcp-flow-control` | 수신 윈도·zero window·window scaling | 필수 | 초안(Claude) | [17-tcp-flow-control](17-tcp-flow-control/) |
| 18 | `tcp-congestion-control` | slow start·AIMD·fast recovery·CUBIC·BBR | 필수 | 초안(Claude) | [18-tcp-congestion-control](18-tcp-congestion-control/) |
| 19 | `tcp-termination-fin-rst-half-open` | 4-way 종료·상태 다이어그램, FIN vs RST, half-open | 필수 | 초안(Claude) | [19-tcp-termination-fin-rst-half-open](19-tcp-termination-fin-rst-half-open/) |
| 20 | `time-wait-and-close-wait` | TIME_WAIT의 존재 이유, CLOSE_WAIT의 의미 | 필수 | 초안(Claude) | [20-time-wait-and-close-wait](20-time-wait-and-close-wait/) |
| 21 | `tcp-keepalive-and-user-timeout` | keepalive·`TCP_USER_TIMEOUT`·앱 heartbeat | 필수 | 초안(Claude) | [21-tcp-keepalive-and-user-timeout](21-tcp-keepalive-and-user-timeout/) |
| 22 | `nagle-and-delayed-ack` | Nagle × delayed ACK 상호작용 | 권장 | 초안(Claude) | [22-nagle-and-delayed-ack](22-nagle-and-delayed-ack/) |

## 7.5 소켓과 커널 경로 — "프로세스가 NIC로 나가는 길"

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 23 | `socket-api` | socket/bind/listen/accept/connect/send/recv/close, 송수신 버퍼, fd | 필수 | 초안(Claude) | [23-socket-api](23-socket-api/) |
| 24 | `application-protocol-framing` | TCP는 바이트 스트림 — 길이 접두·구분자·TLV 프레이밍 | 필수 | 초안(Claude) | [../systems/resp-protocol](../systems/resp-protocol/) |
| 25 | `kernel-network-stack` | 송신: 소켓→TCP/IP→qdisc→드라이버→NIC(DMA) / 수신: NIC→DMA→IRQ→NAPI/softirq→IP→TCP→소켓 버퍼 | 권장 | 초안(Claude) | [25-kernel-network-stack](25-kernel-network-stack/) |
| 26 | `packet-journey` | 종합: 프로세스→소켓→커널→NIC→스위치→라우터→…→수신측 역방향 | 필수 | 초안(Claude) | [26-packet-journey](26-packet-journey/) |

## 7.6 DNS

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 27 | `dns-resolution` | 재귀·반복 질의, 루트/TLD/권한, 레코드(A/AAAA/CNAME/MX/NS/TXT) | 필수 | 초안(Claude) | [27-dns-resolution](27-dns-resolution/) |
| 28 | `dns-caching-and-ttl` | TTL·캐시 계층·부정 캐시·검색 도메인 | 필수 | 초안(Claude) | [28-dns-caching-and-ttl](28-dns-caching-and-ttl/) |
| 51 | `email-delivery-and-authentication` | SMTP 전달 경로, SPF·DKIM·DMARC(DNS TXT), 정렬(alignment), 바운스·수신 거부, 대량 발송자 요건 | 권장 | 초안(Claude) | [51-email-delivery-and-authentication](51-email-delivery-and-authentication/) |

## 7.7 TLS·인증서 (암호 기초는 security/03~07 선행)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 29 | `tls-handshake` | TLS 1.3 1-RTT·0-RTT, 1.2와 차이, SNI·ALPN | 필수 | 초안(Claude) | [29-tls-handshake](29-tls-handshake/) |
| 30 | `x509-and-chain-validation` | 인증서 구조·체인 검증(리프→중간→루트)·루트 스토어·호스트명 검증 | 필수 | 초안(Claude) | [30-x509-and-chain-validation](30-x509-and-chain-validation/) |
| 31 | `revocation-ocsp-ct` | CRL·OCSP·stapling·Certificate Transparency, 수명 단축 흐름 | 권장 | 초안(Claude) | [31-revocation-ocsp-ct](31-revocation-ocsp-ct/) |
| 32 | `mtls-and-cert-operations` | 상호 TLS, ACME 자동 갱신, 인증서 인벤토리 | 권장 | 초안(Claude) | [32-mtls-and-cert-operations](32-mtls-and-cert-operations/) |

## 7.8 HTTP

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 33 | `http-semantics` | 메서드·상태코드·헤더·안전/멱등·쿠키 | 필수 | 초안(Claude) | [33-http-semantics](33-http-semantics/) |
| 34 | `http-caching` | Cache-Control·ETag·조건부 요청·Vary·휴리스틱 캐시 | 필수 | 초안(Claude) | [34-http-caching](34-http-caching/) |
| 35 | `http-connection-management` | keep-alive·커넥션 풀·idle timeout 정렬 | 필수 | 초안(Claude) | [35-http-connection-management](35-http-connection-management/) |
| 36 | `http2-multiplexing` | 스트림·프레임·HPACK·흐름 제어, TCP HoL | 권장 | 초안(Claude) | [36-http2-multiplexing](36-http2-multiplexing/) |
| 37 | `http3-quic` | QUIC 스트림 독립·연결 마이그레이션·0-RTT | 권장 | 초안(Claude) | [37-http3-quic](37-http3-quic/) |
| 38 | `websocket-sse-long-lived` | WebSocket·SSE·롱폴링 | 권장 | 초안(Claude) | [38-websocket-sse-long-lived](38-websocket-sse-long-lived/) |

## 7.8b 데이터 전송·압축·스트리밍 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 39 | `http-content-encoding` | `Accept-Encoding`/`Content-Encoding` 협상(gzip·br·zstd), `Vary`, 압축 수준↔CPU, 압축 대상 선택 | 필수 | 초안(Claude) | [39-http-content-encoding](39-http-content-encoding/) |
| 40 | `chunked-and-streaming-responses` | HTTP/1.1 chunked·HTTP/2 DATA 프레임·스트리밍 응답·백프레셔 | 필수 | 초안(Claude) | [40-chunked-and-streaming-responses](40-chunked-and-streaming-responses/) |
| 41 | `range-requests-and-resume` | `Range`·206·`If-Range`·다중 범위, 이어받기 | 필수 | 초안(Claude) | [41-range-requests-and-resume](41-range-requests-and-resume/) |
| 42 | `large-file-upload-patterns` | multipart/form-data·청크 업로드·재개 가능 업로드(tus)·멀티파트 업로드·presigned URL·청크 체크섬, 전송 경로(sendfile·zero-copy) | 필수 | 초안(Claude) | [42-large-file-upload-patterns](42-large-file-upload-patterns/) |
| 43 | `compression-side-channels` | 압축 + 암호화 + 비밀 반영 = 길이 사이드채널(CRIME·BREACH) | 권장 | 초안(Claude) | [43-compression-side-channels](43-compression-side-channels/) |
| 44 | `websocket-compression` | permessage-deflate, 컨텍스트 유지 여부 | 권장 | 초안(Claude) | [44-websocket-compression](44-websocket-compression/) |
| 45 | `adaptive-media-streaming` | HLS·DASH, 세그먼트·매니페스트, 적응형 비트레이트(ABR) | 심화 | 초안(Claude) | [45-adaptive-media-streaming](45-adaptive-media-streaming/) |

## 7.9 인프라·종합

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 46 | `load-balancers-and-proxies` | L4 vs L7, 리버스 프록시, 헬스체크, 연결 드레이닝 | 필수 | 원고 있음 | [../systems/server-design/02-request-path.md](../systems/server-design/02-request-path.md) |
| 47 | `cdn-and-edge` | CDN 캐시 계층·원점 보호·무효화 | 권장 | 초안(Claude) | [47-cdn-and-edge](47-cdn-and-edge/) |
| 48 | `firewalls-and-network-policy` | 상태 방화벽·보안 그룹·iptables/nftables | 권장 | 초안(Claude) | [48-firewalls-and-network-policy](48-firewalls-and-network-policy/) |
| 49 | `what-happens-when-url` | 종합: URL 입력 → DNS → TCP → TLS → HTTP → 렌더링 | 필수 | 초안(Claude) | [49-what-happens-when-url](49-what-happens-when-url/) |
| 50 | `network-diagnostics` | `ss`·`tcpdump`/Wireshark·`curl -v`·`openssl s_client`·`dig`·`mtr`·`ip route` | 필수 | 초안(Claude) | [50-network-diagnostics](50-network-diagnostics/) |

## 7.10 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 52 | `network-symptom-index` | **에러 코드 사전**: `ECONNRESET`·`EPIPE`·`ETIMEDOUT`·`ECONNREFUSED`·`EADDRNOTAVAIL`·`EMFILE`·`EHOSTUNREACH`·`SERVFAIL`·`NXDOMAIN`·TLS alert·502/503/504 → 원인 leaf | 필수 | 초안(Claude) | [52-network-symptom-index](52-network-symptom-index/) |
| 53 | `network-incidents` | 실사건: Facebook BGP·DNS 전면 장애(2021-10-04) · Let's Encrypt DST Root CA X3 만료로 구형 클라이언트 체인 실패(2021-09-30) · Pakistan Telecom YouTube BGP 하이재킹(2008-02) | 권장 | 초안(Claude) | [53-network-incidents](53-network-incidents/) |
