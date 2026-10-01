# network/52-network-symptom-index — 정답

## 정답

### 1. 증상 이름만으로 원인을 적으면 안 되는 이유

증상은 아래층 사건이 위층 이름으로 **번역**된 것이다. 번역하면서 정보가 줄어든다.\
그래서 한 이름에 원인 후보가 여럿이다. 예: `ECONNRESET`은 idle close 경합, NAT 매핑 삭제, 서버의 본문 미소비 close, `tcp_abort_on_overflow` 모두에서 난다.

함께 확보할 맥락:
- **원문**: 예외 타입·메시지·cause 체인 끝, Node의 `code`·`syscall`.
- **단계**: connect 중인가, 쓰는 중인가, 읽는 중인가.
- **걸린 시간**: 즉시(거절)인가, 계단형(SYN 재전송)인가, 약 2분·약 15분(침묵)인가. 직전 idle 시간도 함께.
- **방향**: RST·FIN·alert를 누가 보냈나(양쪽 `tcpdump`).

### 2. errno → JDK 예외

OpenJDK `Net.c`의 `handleSocketErrorWithMessage` 기준이다(`java.net.Socket`이 NIO 구현을 쓰는 JDK 13+, JEP 353).

| errno | 예외 |
|---|---|
| `ECONNREFUSED` | `ConnectException` |
| `ETIMEDOUT` | `ConnectException` |
| `EHOSTUNREACH` | `NoRouteToHostException` |
| `EADDRNOTAVAIL` | `BindException` |

- `BindException`이라는 이름은 "서버가 포트를 못 잡았다"로 읽힌다. 그래서 listen 쪽을 뒤진다.
- 하지만 connect도 내부에서 로컬 임시 포트를 bind한다. 클라이언트의 connect에서 난 `BindException: Cannot assign requested address`는 대개 **내 호스트의 임시 포트 고갈**이다.
- 옛 구현(JDK 8 등)의 매핑은 다를 수 있다. 확인하지 못했다.

### 3. connect의 `EADDRNOTAVAIL` vs bind의 `EADDRNOTAVAIL`

- connect: bind되지 않은 소켓에 임시 포트를 붙이려 했는데 **임시 포트 범위가 모두 사용 중**이다(connect(2)). 대개 요청마다 새 연결 + 내가 먼저 닫아 TIME-WAIT가 쌓인 결과다.
  - 첫 확인: `ss -tan state time-wait | wc -l`, 목적지 분포, `sysctl net.ipv4.ip_local_port_range`.
- bind: 요청한 주소가 **이 호스트의 주소가 아니다**(bind(2), ip(7)). 오타, 다른 노드로 옮겨 간 VIP 등이다.
  - 첫 확인: `ip -br addr`.
- 같은 errno, 다른 원인이다. 그래서 단계(어느 시스템콜)를 먼저 본다.

### 4. connect 실패까지 걸린 시간으로 가르기

- (a) 수 ms: 누군가 **거절**했다. RST나 ICMP port unreachable이면 `ECONNREFUSED`다. 포트에 listen 없음·`127.0.0.1`에만 bind·방화벽 REJECT(기본 응답이 ICMP port unreachable)다(15, 48번). 다른 ICMP는 종류에 따라 `EHOSTUNREACH`·`ENETUNREACH`다(01, 08번).
- (b) 약 1초·3초 뒤 성공: SYN이나 SYN-ACK가 유실돼 재전송됐다. 리눅스 6.5+ 기본은 1초 간격 5번 뒤 두 배씩(성공 시점 1·2·3·4·5·7초…), 이전 커널은 1초에서 두 배씩(1·3·7초…)이다. 서버 accept 큐 넘침에 새 SYN이 버려진 것이 흔한 원인이다(15, 16번).
- (c) 약 2분 뒤 실패: SYN에 **아무 답이 없었다**. 방화벽 DROP, 대상 꺼짐, conntrack 표 가득, 비대칭 경로 등이다. 리눅스 `tcp_syn_retries` 기본 6이 약 2분을 만든다(6.5+ 약 131초, 이전 약 127초, 15번).
- accept 큐 넘침: listen(2)은 refused 또는 무시 둘 다 허용한다. 리눅스는 기본으로 **무시** 쪽이라 클라이언트는 refused를 보지 않는다.
  - 새 SYN을 버리면 → 느린 connect(b).
  - 마지막 ACK를 버리면(`tcp_abort_on_overflow=0` 기본) → connect는 이미 성공했고, 서버의 SYN-ACK 재전송 동안 첫 요청이 지연된다(15, 23번). `=1`이면 대신 RST를 보낸다.

### 5. RST 뒤 두 번의 write

- 리눅스에서는 (보류된 에러를 `read()` 등이 먼저 꺼내 가지 않았다면) 첫 `write()`가 `ECONNRESET`, 두 번째가 `EPIPE`다.
  - RST 수신 때 커널이 `sk_err = ECONNRESET`을 저장하고, 첫 쓰기가 그것을 꺼내 반환한다. 그다음은 송신 방향이 닫혀 있어 `EPIPE`다(19번, `tcp_reset`·`sk_stream_error`).
  - 이 노트 작성 환경(Linux, Python)에서 재현했다.
  - `read()`가 먼저 `ECONNRESET`을 받았다면 첫 쓰기부터 `EPIPE`다(19번).
  - 상대 FIN을 이미 받은(CLOSE-WAIT) 상태에서 RST가 오면 리눅스는 `EPIPE`를 저장하므로 첫 쓰기부터 `EPIPE`다(`tcp_reset`). FIN만 받았을 때의 쓰기는 성공한다. 순서는 구현 의존이다.
- 두 번째(`EPIPE`)에서 `SIGPIPE`가 함께 온다(send(2)).
  - 네이티브 프로세스: 신호를 처리하지 않으면 **로그 없이 종료**된다. 셸 종료 코드 141(128 + 13).
  - JVM·Node: `SIGPIPE`를 무시하도록 설정해 두므로 죽지 않는다. Java(NIO 구현)는 `SocketException: Broken pipe`(쓰기 경로 `IOUtil.c` → `NioSocketImpl.asSocketException`), Node는 `EPIPE` 에러로 받는다.

### 6. `UnknownHostException`의 세 원인과 가르는 순서

Java는 **NXDOMAIN**(이름 없음), **SERVFAIL**(리졸버가 답을 못 만듦), **리졸버 불통**(53 차단·`resolv.conf` 오류)을 모두 `UnknownHostException`으로 올린다.

같은 호스트에서:
1. `getent hosts <이름>` — 앱과 같은 경로(NSS: `/etc/hosts`, search, ndots 반영)로 되는지.
2. `dig <이름>` — `status:`를 본다. NXDOMAIN이면 AUTHORITY 절의 SOA(부정 캐시 시간), SERVFAIL이면 `EDE:` 줄, timeout이면 리졸버 도달성.
3. `dig @<권한 NS> <이름> +norecurse` 또는 `dig +trace` — 권한 서버는 정상인데 리졸버만 틀리면 캐시(옛 값·부정 캐시)를 먼저 의심한다. DNSSEC 검증 실패(`dig +cd`로 비교, `EDE:` 줄)와 리졸버→권한 서버 도달성도 확인한다(RFC 4035 §5.5).

- NXDOMAIN → 27·28번(부정 캐시, 검색 목록), SERVFAIL → 27·28번(권한 서버·위임·DNSSEC), 불통 → 27·48번(egress 정책).
- Node `dns.resolve4`에서 SERVFAIL은 `err.code === 'ESERVFAIL'`(상수 `dns.SERVFAIL`)이다. 작성 환경(Node 18)에서 `dnssec-failed.org`를 `1.1.1.1`로 물어 확인했다.

### 7. 502·503·504와 nginx 로그의 숫자

- 502 Bad Gateway: 게이트웨이·프록시가 상류에서 **잘못된(invalid) 응답**을 받았다(§15.6.3). 연결 거부·도중 끊김·깨진 응답.
- 503 Service Unavailable: 일시 과부하·점검으로 **지금 처리할 수 없다**(§15.6.4). LB에 건강한 대상이 없을 때도 쓰인다.
- 504 Gateway Timeout: 상류에서 **제때(timely) 응답**을 받지 못했다(§15.6.5).
- 괄호 속 숫자는 리눅스 errno 번호다. 110 = `ETIMEDOUT`, 104 = `ECONNRESET`(111 = `ECONNREFUSED`).
  - `upstream timed out (110…)` → 504. 상류 처리 시간과 `proxy_read_timeout`을 본다(33, 35번).
  - `recv() failed (104…)` → 502. 상류가 연결을 먼저 닫았다. 대개 keep-alive 불일치(35, 19번)나 상류 크래시다.

### 8. 새벽에만 나는 `ECONNRESET`

- 의심: **idle close 경합**. 서버(또는 LB·NAT)의 idle timeout이 클라이언트 풀의 idle 축출보다 짧다. 서버가 쉬던 연결을 닫는 순간 클라이언트가 재사용해 RST를 받는다. 트래픽이 적을수록 연결이 오래 쉬어서 더 자주 난다.
- RST는 연결 중단 또는 "그런 연결은 없다"는 알림이다. 그 자체로 상대 프로세스가 죽었다는 뜻이 아니다. 그래서 서버 쪽에는 에러가 없다.
- 단정하기 전에 볼 것: `tcpdump`에서 **RST의 방향과 직전 패킷**. 서버 FIN → 클라이언트 요청 → 서버 RST 순서면 경합이다. 중간 장비가 RST를 만들었다면 서버 캡처에는 요청이 아예 없다.
- 대처
  - 구간마다 "클라이언트 idle < 서버 keep-alive"로 맞춘다(35번).
  - NAT·LB가 원인이면 keepalive·풀 수명을 그 timeout보다 짧게 둔다(11, 21번).
  - 멱등 요청에 한해 재사용 연결에서 난 리셋을 한 번 재시도한다.

### 9. TLS alert는 방향부터

- alert 이름은 구현마다 고르는 방식이 달라 **힌트일 뿐**이다(29번). 방향은 확실한 정보다.
  - 서버가 보냈다 → 서버가 **내 제안**을 거절했다.
  - 클라이언트가 보냈다 → 클라이언트가 **서버의 응답**을 거절했다. 서버 인증서가 가장 흔하지만, 파라미터 선택(`illegal_parameter`)·Finished 검증(`decrypt_error`) 실패일 수도 있다(RFC 8446). alert 종류와 단계를 함께 본다.
- `unknown_ca`(48), `certificate_expired`(45): 대개 클라이언트가 서버 인증서를 거절하며 보낸다 → 30번(체인·중간 누락·루트 스토어), 32번(만료 운영). 교차 서명 루트 만료는 53번 사례.
- `no_application_protocol`(120): ALPN 목록이 안 겹칠 때 서버가 보낸다 → 29번, 36번(HTTP/2).
- `certificate_required`(116): TLS 1.3 mTLS에서 클라이언트 인증서가 없을 때 서버가 보낸다 → 32번.

### 10. 에러 없는 증상 넷

- 작은 요청은 되고 큰 응답·업로드·TLS 인증서 단계만 멈춘다 → PMTUD 블랙홀, 10·09번. 같은 큰 세그먼트의 재전송, `ping -M do -s <크기>`.
- 요청마다 약 40ms 고정 지연 → Nagle × delayed ACK, 22번. `tcpdump`의 ACK 단독 → 나머지 조각 모양.
- 에러율 0인데 p99만 높다 → 유실·재정렬로 인한 재전송, 16·04·25번. `nstat`의 `TcpRetransSegs`, `ss -ti`의 `retrans`.
- 200인데 본문이 잘렸다 → 헤더를 보낸 뒤 실패, 40번. 액세스 로그의 보낸 바이트, curl `(18)`.
- (그 밖) UDP 수신 버퍼 넘침(14번, `netstat -su`), 원거리 처리량이 윈도/RTT에 묶임(03·17번, SYN의 `wscale`).
