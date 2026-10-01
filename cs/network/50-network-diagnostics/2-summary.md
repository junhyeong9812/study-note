# network/50-network-diagnostics — 질문마다 맞는 도구: ss·tcpdump/Wireshark·curl -v·openssl s_client·dig·mtr·ip route — 정리 (힌트)

## 해결하는 문제

네트워크 장애 대응에서 가장 흔한 실수는 **도구 없이 추측하는 것**이다.\
"DNS 문제 같다", "방화벽이겠지", "일단 재시작"으로 시작하면 두 가지를 잃는다.
- 틀린 가설을 고치느라 시간을 쓴다.
- 재시작이 증거(쌓인 소켓 상태, 재현 조건)를 지운다.

진단 도구는 저마다 **한 위치에서 한 질문**에 답한다.\
질문을 먼저 정하고, 그 질문에 답하는 도구를 고르는 것이 이 노트의 목표다.

쉬운 예: 병원 검사다.\
열이 난다고 곧바로 수술하지 않는다. 혈액 검사, X-ray, CT는 각각 다른 것을 보고, 의사는 의심하는 부위에 맞는 검사를 고른다.

똑같은 구조다.
- `dig`은 이름 해석, `ip route get`은 커널의 경로 선택, `mtr`은 경로 위 손실을 본다.
- `tcpdump`는 선 위의 패킷, `ss`는 커널의 소켓 상태를 본다.
- `openssl s_client`는 TLS 협상, `curl -v`는 HTTP 요청 전체를 본다.

실무 예:
- "API가 느리다" → `curl -w`로 DNS·TCP·TLS·서버 처리 중 어디가 긴지 잰다. 그다음에 그 구간의 도구를 쓴다.
- "가끔 연결이 끊긴다" → 양쪽에서 `tcpdump`를 떠서 누가 먼저 RST·FIN을 보냈는지 본다. 추측으로 타임아웃 값을 바꾸지 않는다.

## 동작·원리

### 1. 도구 지도 — 무엇을, 어디서 보나

```text
   질문                                 도구                          보는 위치
   -----------------------------------  ----------------------------  ------------------------------
   이름이 어떤 주소로 풀리나?              getent hosts / dig            OS 해석 경로 / DNS 서버에 직접
   커널은 어느 길·출발 주소로 보내나?       ip route get                  내 커널 라우팅 표(FIB)
   경로의 어느 홉에서 손실·지연이 생기나?   mtr / tracepath               경로 위 라우터의 ICMP 응답
   패킷이 실제로 오가나? 누가 끊었나?       tcpdump / Wireshark           내 호스트의 캡처 지점
   소켓이 어떤 상태·큐·RTT를 갖나?         ss                            내 커널의 소켓 표
   TLS가 무엇을 협상하고 어떤 인증서를 주나? openssl s_client              TLS 핸드셰이크(클라이언트 입장)
   HTTP 요청이 구간별로 얼마나 걸리나?      curl -v / curl -w             앱 계층 전체(클라이언트 입장)
```

```text
  계층                 도구
  -----------------   --------------------------------------------
  HTTP                 curl -v, curl -w
  TLS                  openssl s_client, curl -v
  DNS(앱 계층)          dig, getent
  TCP 소켓 상태          ss
  TCP/IP 패킷           tcpdump, Wireshark
  IP 경로               ip route get, mtr, tracepath (, traceroute, ping)
```

- 도구마다 **보는 위치가 하나**다. `ss`는 이 호스트의 소켓만, `tcpdump`는 이 호스트의 캡처 지점만 본다.
- 그래서 "상대 쪽에서는 어떻게 보이나"는 상대 쪽에서 같은 도구를 한 번 더 돌려야 안다.

### 2. `dig` — DNS 서버에 직접 묻는다 (27, 28번)

```text
  (예시 — 작성 환경)
  ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 41504     <- NOERROR / NXDOMAIN / SERVFAIL
  ;; flags: qr rd ra; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ...     <- aa가 있으면 권한 서버의 답
  ;; ANSWER SECTION:
  example.com.   179   IN   A   104.20.23.154                    <- 179 = 남은 TTL(초)
  ;; SERVER: 127.0.0.53#53(127.0.0.53) (UDP)                      <- 누가 답했나
```

```bash
dig example.com A                    # 기본 해석기에
dig @8.8.8.8 example.com A           # 다른 해석기와 비교
dig +short example.com AAAA
dig +trace example.com               # 루트부터 위임을 따라 반복 질의
dig @ns1.example.net example.com A +norecurse   # 권한 서버에 직접
dig +cd example.com                  # DNSSEC 검증을 끄고 질의 -> SERVFAIL이 사라지면 DNSSEC 원인
dig +tcp example.com                 # TCP로
```

- `dig`은 DNS 서버에 직접 묻는다. `/etc/hosts`·nsswitch는 거치지 않는다. 앱과 같은 경로는 `getent hosts`다(27번).
- `dig`은 기본적으로 검색 목록(search)을 쓰지 않는다(dig(1) `+search`). 짧은 이름이 앱에서만 풀리는 차이가 여기서 난다(28번).
- `+trace`에서 `@server`는 루트 서버 목록을 얻는 첫 질의에만 쓰인다(dig(1)).
- `+cd`는 CD(checking disabled) 비트를 켜 서버에 DNSSEC 검증을 하지 말라고 요청한다(dig(1)).

### 3. `ip route get` — 커널이 실제로 고를 경로 (08, 26번)

```text
  $ ip route get 1.1.1.1                                           (예시 — 작성 환경)
  1.1.1.1 via 192.168.45.1 dev wlo1 src 192.168.45.29 uid 1000
          ^^^ 다음 홉        ^^^ 나갈 인터페이스  ^^^ 출발 주소

  $ ip route get 1.1.1.1 fibmatch
  default via 192.168.45.1 dev wlo1 proto dhcp src 192.168.45.29 metric 600
  ^^^ 실제로 매칭된 표 항목(최장 접두사)
```

- `ip route get`은 목적지 하나에 대한 경로를 **커널이 보는 그대로** 출력한다(ip-route(8)).
- `fibmatch`는 해석된 목적지 항목 대신 매칭된 FIB 항목 전체를 돌려준다(ip-route(8)).
- `from`, `oif`, `mark`를 붙이면 출발 주소·인터페이스·방화벽 마크에 따른 정책 라우팅 결과도 볼 수 있다(ip-route(8)).
- `ip route show`로 표 전체를, `ip neigh`로 다음 홉의 ARP 상태를 함께 본다(05번).

### 4. `mtr`·`tracepath` — 경로의 홉마다 (09, 10번)

```text
  $ mtr -rwnc 3 1.1.1.1                                           (예시 — 작성 환경)
  HOST: ...                       Loss%   Snt   Last   Avg  Best  Wrst StDev
    1.|-- 192.168.45.1             0.0%     3    3.4   2.1   1.3   3.4   1.1
    2.|-- 192.168.55.1             0.0%     3    2.5   2.2   1.8   2.5   0.3
    3.|-- ???                     100.0     3    0.0   0.0   0.0   0.0   0.0    <- 중간 홉이 ICMP로 답하지 않음
   ...
   13.|-- 1.1.1.1                  0.0%     3    3.6   3.7   3.6   3.8   0.1    <- 목적지는 손실 0%
```

- `mtr`은 traceroute와 ping을 합친 도구다. 홉마다 탐침을 반복해 손실률과 지연 통계를 낸다.
- 위 예시처럼 **중간 홉만 100%이고 목적지는 0%** 면 경로에는 문제가 없다. 그 라우터가 ICMP 응답을 안 하거나 속도 제한을 건 것이다(09번). 손실은 **그 홉부터 끝까지 이어질 때만** 진짜다.
- 주요 옵션(mtr(8)): `-r` 보고서 모드, `-w` 넓은 보고서, `-c` 반복 횟수, `-n` 이름 풀이 안 함, `-z` AS 번호, `-T` ICMP Echo 대신 TCP SYN, `-P` 포트, `-u` UDP.
  - `-T -P 443`은 ICMP가 막힌 경로에서 실제 서비스 포트로 경로를 본다.
- `tracepath`는 경로를 따라가며 **경로 MTU**를 함께 찾는다. 슈퍼유저 권한이 필요 없다(tracepath(8)). "큰 것만 멈춤" 장애에서 먼저 쓴다(10번).

### 5. `ss` — 커널의 소켓 표 (15, 20, 21번)

```bash
ss -s                                   # 상태별 개수 요약 (estab, timewait, ...)
ss -ltnp                                # 리슨 중인 TCP + 프로세스
ss -tan state close-wait                # CLOSE-WAIT만 (앱이 close 안 한 연결)
ss -tan state syn-sent                  # 연결 시도 중 (SYN-ACK를 못 받는 중)
ss -tnio state established '( dport = :443 )'   # RTT·cwnd·재전송 + 타이머
ss -tnm                                 # 소켓 메모리(skmem)
```

```text
  (예시 — 작성 환경, -i 출력 일부)
  192.168.45.29:33786  151.101.2.132:443
     cubic wscale:9,10 rto:205 rtt:4.245/1.397 mss:1448 pmtu:1500 cwnd:10
     bytes_sent:1828 bytes_received:33055 ... lastsnd:373588 lastrcv:373582 ...
     ^ rtt = 평균/편차(ms), cwnd = 혼잡 윈도(세그먼트), lastsnd·lastrcv = 마지막 송수신 뒤 경과(ms)
```

- 주요 옵션(ss(8)): `-t`/`-u` TCP/UDP, `-l` 리슨만, `-a` 전부, `-n` 숫자, `-p` 프로세스, `-i` TCP 내부 정보, `-m` 메모리, `-o` 타이머, `-s` 요약, `-K` 소켓 강제 종료.
- 상태 필터는 `state`/`exclude` 뒤에 `established`, `syn-sent`, `syn-recv`, `time-wait`, `close-wait` 등을 쓴다. 식은 `dport`·`sport`·`dst`·`src`를 `and`·`or`·`not`으로 묶는다(ss(8) STATE-FILTER·EXPRESSION).
- `-o`의 타이머 이름은 `on`(재전송 계열), `keepalive`, `timewait`, `persist`(zero window 탐침) 등이다(ss(8)). `persist`가 보이면 상대 수신 윈도가 0이다(17번).
- 리슨 소켓의 Recv-Q·Send-Q는 accept 큐 현재 길이·최대 길이다(15번). 연결 소켓에서는 읽지 않은·확인받지 않은 바이트다.

### 6. `tcpdump`·Wireshark — 선 위의 패킷 (25번)

```bash
tcpdump -ni any 'host 203.0.113.50 and tcp port 443'          # 보기
tcpdump -ni eth0 -w /tmp/cap.pcap -c 10000 'tcp port 443'     # 파일로 떠서 Wireshark로
tcpdump -nr /tmp/cap.pcap 'tcp[tcpflags] & tcp-rst != 0'      # 저장본에서 RST만
tcpdump -ni any -K udp port 53                                # 체크섬 검사 끔(오프로드 오탐 방지)
```

- 주요 옵션(tcpdump(1), Ubuntu는 8절): `-n` 이름·포트 변환 안 함, `-i` 인터페이스(`any` = 전부, 이때 promiscuous 모드 아님), `-w`/`-r` 파일 쓰기/읽기, `-c` 개수, `-s` 캡처 길이(기본 262144바이트), `-K` 체크섬 검사 끔, `-Q in|out` 방향, `-A`/`-X` 본문 출력.
- 종료 시 출력되는 `dropped by kernel`은 캡처 버퍼가 모자라 **캡처가** 놓친 수다(tcpdump(1)). 네트워크 손실과 구분한다.
- **캡처 지점의 한계**(25번)
  - 수신 탭은 netfilter보다 앞이다. "tcpdump에 보였다"는 "방화벽을 통과했다"가 아니다.
  - 송신 탭은 qdisc 뒤, 드라이버 직전이다. "보였다"는 "선에 나갔다"까지 보장하지 않는다.
- TLS 안의 HTTP는 암호화돼 보이지 않는다. 핸드셰이크(SNI·ALPN·alert)와 TCP 흐름까지만 본다.
- Wireshark는 캡처 필터(libpcap 문법, 캡처 시점)와 **표시 필터**(자체 문법, 분석 시점)가 다르다.
  - 표시 필터 예: `tcp.port == 443`, `ip.addr == 192.0.2.1`, `tcp.analysis.retransmission`, `tcp.analysis.zero_window`, `tcp.analysis.duplicate_ack`(Wireshark 사용자 안내서 "TCP Analysis").
  - TCP 분석 플래그는 재전송·zero window·중복 ACK를 표시해 준다. 16·17번 현상을 눈으로 확인하는 가장 빠른 길이다.

### 7. BPF 필터 — 필터는 커널 안에서 돈다

```text
  사용자가 쓴 식                         libpcap이 컴파일                   커널
  'tcp dst port 443'   ---pcap_compile--->  BPF 프로그램  ---SO_ATTACH_FILTER--->  패킷마다 실행
                                                                                  |
                                                  맞으면 캡처 버퍼로 복사 <--------+
                                                  안 맞으면 버림(사용자 공간으로 안 올라옴)
```

```text
  $ tcpdump -d 'tcp dst port 443'                    (예시 — 작성 환경, 이더넷 가정)
  (000) ldh      [12]                       ; 이더타입 읽기
  (001) jeq      #0x86dd   jt 2   jf 6      ; IPv6인가?
  (002) ldb      [20]                       ; IPv6 next header
  (003) jeq      #0x6      jt 4   jf 15     ; TCP인가?
  (004) ldh      [56]                       ; TCP 목적지 포트
  (005) jeq      #0x1bb    jt 14  jf 15     ; 443인가?
  (006) jeq      #0x800    jt 7   jf 15     ; IPv4인가?
  (007) ldb      [23]                       ; IPv4 protocol
  (008) jeq      #0x6      jt 9   jf 15
  (009) ldh      [20]
  (010) jset     #0x1fff   jt 15  jf 11     ; 첫 조각이 아니면 버림(포트 없음)
  (011) ldxb     4*([14]&0xf)               ; IPv4 헤더 길이
  (012) ldh      [x + 16]                   ; TCP 목적지 포트
  (013) jeq      #0x1bb    jt 14  jf 15
  (014) ret      #262144                    ; 맞음: 262144바이트까지 캡처
  (015) ret      #0                         ; 안 맞음: 버림
```

- *BPF(Berkeley Packet Filter)*: 패킷마다 실행되는 작은 명령어 프로그램이다. 사용자 공간 프로그램이 소켓에 붙이면 커널이 그 필터를 통과한 데이터만 넘긴다(kernel docs "Linux Socket Filtering aka BPF").
- `tcpdump -d`는 컴파일된 필터를 사람이 읽는 형태로 출력하고 멈춘다(tcpdump(1)). 위처럼 IPv6·IPv4를 모두 검사한다.
- 필터 식 문법(pcap-filter(7))
  - 기본 단위는 **한정자 + 값**이다. 종류(`host`·`net`·`port`·`portrange`), 방향(`src`·`dst`), 프로토콜(`ether`·`ip`·`ip6`·`arp`·`tcp`·`udp`)을 조합한다. 예: `src host 10.0.0.5`, `tcp dst port 443`, `net 10.0.0.0/8`.
  - 헤더 바이트를 직접 볼 수 있다. `proto[offset:size]` 형식이다. 예: `tcp[tcpflags] & (tcp-syn|tcp-rst) != 0`, `icmp[icmptype] == icmp-timxceed`.
  - `and`·`or`·`not`과 괄호로 묶는다. 셸이 괄호·`&`를 먹지 않게 식 전체를 작은따옴표로 감싼다.
- **함정**: `tcp[...]`·`udp[...]` 같은 헤더 인덱스 연산은 IPv4에만 적용되고 IPv6에는 적용되지 않는다(pcap-filter(7)). `tcp[tcpflags]` 필터는 IPv6 연결의 RST를 놓친다. `tcp port 443` 같은 종류 한정자는 둘 다 잡는다.
- 필터를 좁게 쓰면 캡처 버퍼 부담과 `dropped by kernel`이 준다. 트래픽이 많은 서버에서 필터 없는 캡처는 캡처가 패킷을 놓친다.

### 8. `openssl s_client` — TLS 핸드셰이크를 직접 (29, 30, 31번)

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com -brief </dev/null
openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts </dev/null
openssl s_client -connect api.example.com:443 -servername api.example.com \
        -verify_return_error -verify_hostname api.example.com </dev/null
openssl s_client -connect api.example.com:443 -alpn h2,http/1.1 </dev/null | grep ALPN
openssl s_client -connect api.example.com:443 -status </dev/null      # OCSP stapling 응답 요청
```

```text
  (예시 — 작성 환경, OpenSSL 3.0.13)
  -brief:   Protocol version: TLSv1.3 / Ciphersuite: TLS_AES_256_GCM_SHA384 / Verification: OK
  기본:     Verify return code: 0 (ok)
  -verify_hostname wrong.example.org 추가:  Verify return code: 62 (hostname mismatch)
```

- `-servername`은 SNI 값을 정한다. 생략하면 `-connect`의 이름이 DNS 이름 형식일 때 그것이 SNI가 된다(OpenSSL 1.1.1부터). IP로 붙으면 SNI가 빠진다(openssl-s_client(1)).
- `-showcerts`는 서버가 **보낸 순서 그대로**의 목록이다. 검증된 체인이 아니다(openssl-s_client(1)). 리프가 루트에서 바로 발급된 드문 경우가 아니라면, 1장만 보일 때는 중간 인증서 누락을 먼저 의심한다(30번).
- s_client는 **검증 오류가 나도 핸드셰이크를 계속한다**. 오류에서 멈추게 하려면 `-verify_return_error`를 쓴다(openssl-s_client(1)).
- 호스트명 검증은 `-verify_hostname`을 줄 때만 한다. 위 예시처럼 `Verify return code: 0 (ok)`는 체인만 통과했다는 뜻일 수 있다.
- TLS 1.3 암호군은 `-ciphersuites`, 1.2 이하는 `-cipher`로 고른다(29번).

### 9. `curl -v`·`curl -w` — HTTP 요청 전체 (33, 35, 49번)

```text
  (예시 — 작성 환경, curl 8.5.0, 줄임)
  * Host example.com:443 was resolved.
  * IPv6: 2606:4700:10::ac42:93f3, ...          <- 1 DNS
  * IPv4: 172.66.147.243, 104.20.23.154
  *   Trying 172.66.147.243:443...
  * Connected to example.com (...) port 443      <- 2 TCP
  * ALPN: curl offers h2,http/1.1
  * TLSv1.3 (OUT), TLS handshake, Client hello (1):
  * TLSv1.3 (IN), TLS handshake, Server hello (2):
  * TLSv1.3 (IN), TLS handshake, Certificate (11):
  * SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519 ...
  * ALPN: server accepted h2                     <- 3 TLS (+ HTTP 버전 결정)
  *  subjectAltName: host "example.com" matched cert's "example.com"
  *  SSL certificate verify ok.
  > GET / HTTP/2 ...                             <- 4 HTTP 요청 / 응답
```

- `-v` 한 번으로 DNS 결과, 접속 IP, TLS 버전, ALPN, 인증서 이름 검증, 요청·응답 헤더가 순서대로 나온다. **멈춘 줄이 멈춘 구간**이다.
- `-w`의 `time_namelookup`·`time_connect`·`time_appconnect`·`time_starttransfer`·`time_total`은 시작부터의 누적 시간이다(curl(1)). 차이로 구간 시간을 구한다(49번).
- 격리 옵션(curl(1)): `--resolve host:port:addr`(DNS 건너뛰기), `--connect-to`(다른 서버에 연결하되 SNI·인증서 검증은 원래 이름), `-4`/`-6`, `--http1.1`/`--http2`/`--http3`.
  - `--http3`는 curl이 HTTP3 기능과 함께 빌드됐을 때만 쓸 수 있다. `curl -V`의 Features 줄에서 확인한다(작성 환경 8.5.0 빌드에는 없음).
- 시간 한도: `--connect-timeout`은 연결 단계(DNS와 TCP·TLS·QUIC 핸드셰이크)까지만, `-m`/`--max-time`은 전송 전체를 제한한다(curl(1)).
- `--trace-ascii 파일`은 주고받은 바이트까지 기록한다.

## 쓰이는 자료구조·알고리즘

- **BPF 프로그램 = 분기 그래프**: 필터는 레지스터 하나(A)와 인덱스 레지스터(X)를 쓰는 명령어 열이다. `jeq … jt/jf`로 앞쪽으로만 뛰어 **순환 없는 분기 그래프**를 이룬다(위 `-d` 출력). 모든 경로가 `ret`로 끝나므로 패킷마다 유한한 단계에 끝난다. 개념은 [그래프](../../data-structure/08-graph/2-summary.md).
- **캡처 링 버퍼**: 커널은 캡처한 패킷을 고정 크기 버퍼에 쌓고 tcpdump가 읽어 간다. 읽기가 느리면 새 패킷을 버린다(`dropped by kernel`). 25번의 RX 링과 같은 "넘치면 조용히 버리는 유계 버퍼"다.
- **소켓 조회 표**: `ss`가 읽는 것은 커널의 연결 표(4-튜플 해시)와 리슨 표다(23번). 개념은 [해시맵](../../data-structure/05-hashmap/2-summary.md).
- **EWMA**: `ss -i`의 `rtt:평균/편차`는 16번의 SRTT·RTTVAR, 즉 지수 가중 이동 평균이다.
- **TTL 증가 탐색**: traceroute·mtr은 TTL을 1, 2, 3…으로 늘리며 각 홉의 Time Exceeded를 받는다. 홉 수만큼의 선형 탐색이다(09번).
- **트리 순회**: `dig +trace`는 DNS 이름 트리를 루트에서 잎으로 위임을 따라 내려간다(27번).

## 적용 — 풀어나가는 법

### 1. 질문 → 첫 도구 결정 가이드

```text
  증상
   |
   +-- 이름 에러 (ENOTFOUND, UnknownHost, NXDOMAIN)
   |      -> getent hosts (앱과 같은 경로)  -> dig (서버 직접)  -> dig +trace / +cd
   |
   +-- 연결 실패
   |      +-- 즉시 거절 (ECONNREFUSED)
   |      |      -> 서버: ss -ltnp (리슨 중인가, 주소가 127.0.0.1만인가)
   |      |      -> tcpdump로 거절을 누가 보내나: 서버 커널의 RST?
   |      |         방화벽 REJECT의 ICMP port-unreachable(iptables 기본)·RST?
   |      |         필터에 icmp도 넣는다: 'tcp[tcpflags] & tcp-rst != 0 or icmp'
   |      +-- 타임아웃 (ETIMEDOUT)
   |             -> ip route get (경로·출발 주소)
   |             -> 클라이언트 tcpdump: SYN 재전송만? / 서버 tcpdump: SYN 도착?
   |             -> mtr -T -P <port> (경로 어디까지)
   |
   +-- TLS 에러 (handshake, 인증서)
   |      -> openssl s_client -servername -showcerts -verify_return_error -verify_hostname
   |
   +-- HTTP가 느림 / 5xx
   |      -> curl -w (구간별 시간) -> 긴 구간의 도구로
   |      -> curl -v --connect-to (CDN·LB 건너뛰고 원점 직접)
   |
   +-- 간헐 끊김·리셋 (ECONNRESET, socket hang up)
   |      -> 양쪽 tcpdump 'tcp[tcpflags] & (tcp-rst|tcp-fin) != 0' (IPv6면 종류 한정자로)
   |      -> ss -tnio (타이머·재전송), 경로 idle timeout 표 (11, 35)
   |
   +-- 큰 것만 멈춤 (TLS 인증서 교환, 큰 응답)
   |      -> tracepath (경로 MTU), ping -M do -s <크기>  (10)
   |
   +-- 소켓·fd가 쌓임 (EMFILE, EADDRNOTAVAIL)
          -> ss -s, ss -tan state close-wait / time-wait 의 상대 주소별 개수 (20)
```

- 이 표는 "처음 볼 도구"다. 에러 문자열 전체 역색인은 [52-network-symptom-index](../52-network-symptom-index/2-summary.md), 구간 지도는 [49-what-happens-when-url](../49-what-happens-when-url/2-summary.md).

### 2. 진단의 순서 — 추측 대신 증거

1. **증상을 문장으로 적는다.** 누가, 어디서 어디로, 언제부터, 항상인가 가끔인가.
2. **재현 명령을 만든다.** 대부분 `curl -v`나 `dig` 한 줄이다. 앱 없이 재현되면 앱은 무죄다.
3. **바깥에서 안으로, 또는 아래에서 위로** 한 구간씩 좁힌다. 정상인 마지막 구간과 비정상인 첫 구간 사이가 범인이다(26번).
4. **양 끝에서 동시에 본다.** 클라이언트 tcpdump와 서버 tcpdump를 같이 뜨면 "보냈는데 안 왔다"와 "왔는데 답을 안 했다"가 갈린다.
5. **재시작 전에 증거를 뜬다.** `ss -s`, 상태별 소켓 목록, 짧은 pcap을 먼저 저장한다.

### 3. 환경별 주의

- 인터페이스에서 패킷을 읽으려면 특별한 권한이 필요할 수 있다(tcpdump(1), 세부는 pcap(3PCAP)). 저장된 파일(`-r`)을 읽을 때는 필요 없다. 그래서 운영 서버에서는 권한 있는 곳에서 `-w`로 뜨고, 분석은 파일로 한다.
- 컨테이너 안에는 도구가 없을 때가 많다. 호스트에서 `nsenter -t <PID> -n`으로 그 프로세스의 네트워크 네임스페이스에 들어가 호스트의 도구를 쓴다(nsenter(1) `-n`).
- 운영 서버에서 캡처할 때는 필터와 `-c`로 양을 제한한다. pcap에는 민감 데이터가 담길 수 있으니 보관·전달에 주의한다.

### 4. 코드 쪽에서 도구를 돕는 것

진단 도구가 구간을 보여 주려면 앱이 에러를 **뭉개지 않아야** 한다.

```js
// Node: 원인 코드를 잃지 않고 로그에 남긴다
try {
  await fetch(url, { signal: AbortSignal.timeout(5_000) });
} catch (e) {
  // e.cause?.code: ENOTFOUND(DNS) / ECONNREFUSED(TCP 거절) / 인증서 코드(TLS)
  // 연결 타임아웃: undici connectTimeout(기본 10초)이면 e.cause?.code === 'UND_ERR_CONNECT_TIMEOUT'
  // AbortSignal.timeout이 먼저 끝나면 e.name === 'TimeoutError'(DOMException) — cause·code가 없다
  console.error({ url, name: e.name, code: e.cause?.code, message: e.cause?.message });
  throw e;
}
```

- 로그에 원인 코드와 대상 주소·포트가 있으면 첫 도구를 바로 고를 수 있다.
- Node `fetch`(undici)는 connect 타임아웃(기본 10초)이 커널의 SYN 포기(약 2분)보다 먼저 끝난다. 그래서 TCP 무응답은 보통 `ETIMEDOUT`이 아니라 `UND_ERR_CONNECT_TIMEOUT`으로 보인다(undici `Client`·`Errors` 문서).

## 장애 시나리오와 대처

### 1. "DNS는 멀쩡하다" — `dig`은 되는데 앱은 이름을 못 푼다

- **현상**: 앱은 `UnknownHostException`을 내는데, 운영자가 `dig`을 쳐 보니 잘 풀린다. "DNS 문제 아님"으로 결론 내고 다른 곳을 판다.
- **보이는 형태**: `dig api`는 NOERROR인데 `getent hosts api`는 결과가 없다. 또는 그 반대다.
- **원인**: 도구와 앱이 **다른 해석 경로**를 쓴다. `dig`은 DNS 서버에 직접 묻고 기본적으로 검색 목록을 쓰지 않는다. 앱은 nsswitch·`/etc/hosts`·검색 목록·런타임 캐시를 거친다(27, 28번).
- **대처**
  - 앱과 같은 경로인 `getent hosts`를 먼저 쓴다.
  - 컨테이너 앱이면 그 네임스페이스 안에서(`nsenter -n` 또는 컨테이너 안) `/etc/resolv.conf`와 함께 확인한다.
  - `dig +search`로 검색 목록을 적용했을 때의 결과와 비교한다.

### 2. `mtr` 중간 홉 손실을 보고 ISP를 탓한다

- **현상**: 느리다는 신고에 `mtr`을 돌렸더니 5번 홉이 40% 손실이다. ISP에 장애 신고를 한다.
- **보이는 형태**: 5번 홉만 손실이 높고, 6번 이후와 목적지는 0%다.
- **원인**: 라우터는 자기 앞으로 온 ICMP에 답하는 일을 낮은 우선순위로 처리하거나 속도를 제한한다. 전달은 멀쩡하다(09번).
- **대처**
  - 손실이 **그 홉부터 목적지까지 이어질 때만** 진짜 손실로 본다.
  - `mtr -T -P 443`으로 실제 서비스 프로토콜로 다시 본다.
  - 양방향 경로가 다를 수 있으므로 가능하면 반대쪽에서도 `mtr`을 돌린다.

### 3. `openssl s_client`가 "0 (ok)"인데 앱은 인증서 실패

- **현상**: 앱은 인증서 오류를 내는데 `openssl s_client -connect 10.0.0.5:443`은 `Verify return code: 0 (ok)`다. "인증서 정상"으로 결론 낸다.
- **보이는 형태**: 앱 로그 `No subject alternative names matching ...`·`hostname mismatch` 류.
- **원인** (둘 중 하나 또는 둘 다)
  - s_client는 `-verify_hostname`이 없으면 **호스트명을 검증하지 않는다**. 체인만 통과해도 0이다.
  - IP로 붙어 SNI가 빠졌다. 서버가 기본 인증서를 줬고, 앱은 SNI를 보내 다른 인증서를 받았다(또는 그 반대)(29번).
- **대처**: 앱과 같은 조건으로 재현한다. `-servername 실제이름 -verify_hostname 실제이름 -verify_return_error`를 모두 준다. 앱이 보는 인증서를 보려면 `curl -v https://실제이름/`도 함께 본다.

### 4. 캡처에 아무것도 안 보인다 / 보이는데 앱은 못 받았다

- **현상 A**: RST를 잡으려고 필터를 걸었는데 한 건도 없다. "RST는 없다"로 결론 낸다.
  - **원인**: 필터가 `tcp[tcpflags]`처럼 헤더 인덱스를 써서 **IPv4만** 본다. 실제 연결은 IPv6였다(pcap-filter(7)). 또는 다른 인터페이스를 떴다.
  - **대처**: `-i any`로 뜨고, `tcpdump -d '식'`으로 필터가 IPv6도 검사하는지 본다. IPv6 RST는 `ip6 and tcp`로 넓게 뜬 뒤 Wireshark 표시 필터 `tcp.flags.reset == 1`로 거른다(Wireshark 표시 필터 참조 `tcp` 필드).
- **현상 B**: 서버 tcpdump에 SYN이 들어오는데 연결이 안 된다. "서버 앱 문제"로 결론 낸다.
  - **원인**: 수신 캡처 지점은 netfilter보다 앞이다. 방화벽이 그 뒤에서 DROP했을 수 있다(25, 48번).
  - **대처**: SYN-ACK가 **나가는지**를 같은 캡처에서 본다. 안 나가면 방화벽 규칙 카운터(`nft list ruleset`, `iptables -vnL`)와 `ss -ltn`의 리슨 상태를 확인한다.

### 5. 추측으로 재시작해 증거를 지운다

- **현상**: 서비스가 새 연결을 못 받는다. "일단 재시작"으로 복구된다. 며칠 뒤 똑같이 재발한다.
- **보이는 형태**: 재발 때마다 `Too many open files`(`EMFILE`) 또는 응답 지연. 재시작 전 상태는 기록이 없다.
- **원인**: CLOSE-WAIT 누적 같은 앱 버그다. 상대가 닫았는데 앱이 `close()`를 안 한다. 재시작이 fd를 모두 닫아 원인을 지웠다(20번).
- **대처**
  - 재시작 전에 증거를 저장한다: `ss -s`, `ss -tanp state close-wait`의 상대 주소별 개수, `ls /proc/<PID>/fd | wc -l`.
  - CLOSE-WAIT의 상대 주소로 어느 연결 코드가 닫지 않는지 찾는다(20번).
  - 대응 절차서(runbook)에 "재시작 전 수집 명령"을 넣는다.

## 핵심 문장

- 진단 도구는 한 위치에서 한 질문에 답한다. 질문을 먼저 정하고 도구를 고른다. 추측으로 고치기 시작하지 않는다.
- `dig`은 DNS 서버, `getent`는 앱과 같은 OS 경로를 본다. 두 결과가 다르면 그 차이가 단서다.
- `mtr`의 중간 홉 손실은 목적지까지 이어질 때만 진짜다. `openssl s_client`의 `0 (ok)`는 `-verify_hostname` 없이는 호스트명 검증을 뜻하지 않는다.
- tcpdump의 수신 캡처는 방화벽보다 앞이고, BPF 필터는 커널 안에서 돈다. `tcp[...]` 인덱스 필터는 IPv6를 놓친다.
- `curl -v`는 멈춘 줄이 멈춘 구간이고, `curl -w`의 누적 시간 차이가 구간별 시간이다.
- 재시작 전에 `ss`와 짧은 pcap으로 증거를 뜬다. 재시작은 증거를 지운다.

## 관련 주제·근거

- 선행
  - [49-what-happens-when-url](../49-what-happens-when-url/2-summary.md) — 구간 지도(이 노트는 구간별 도구)
  - [26-packet-journey](../26-packet-journey/2-summary.md) — 패킷 경로를 구간으로 자르는 순서
- 도구가 보는 원리
  - [25-kernel-network-stack](../25-kernel-network-stack/2-summary.md) — tcpdump 캡처 지점, 드롭 카운터
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) · [28-dns-caching-and-ttl](../28-dns-caching-and-ttl/2-summary.md) — `dig`·`getent`
  - [09-icmp-ping-traceroute](../09-icmp-ping-traceroute/2-summary.md) · [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md) — `mtr`·`tracepath`
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md) · [16-tcp-reliability-retransmission](../16-tcp-reliability-retransmission/2-summary.md) · [17-tcp-flow-control](../17-tcp-flow-control/2-summary.md) · [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) · [20-time-wait-and-close-wait](../20-time-wait-and-close-wait/2-summary.md) · [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md) — `ss`·tcpdump로 보는 TCP
  - [23-socket-api](../23-socket-api/2-summary.md) — 소켓 표
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) · [30-x509-and-chain-validation](../30-x509-and-chain-validation/2-summary.md) · [31-revocation-ocsp-ct](../31-revocation-ocsp-ct/2-summary.md) — `openssl s_client`
  - [33-http-semantics](../33-http-semantics/2-summary.md) · [35-http-connection-management](../35-http-connection-management/2-summary.md) — `curl -v`
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) · [48-firewalls-and-network-policy](../48-firewalls-and-network-policy/2-summary.md) — 캡처에 보이는데 도달 안 하는 이유
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — `ip route`가 보여 주는 최장 접두사 매칭
- 후속
  - [52-network-symptom-index](../52-network-symptom-index/2-summary.md) — 에러 코드 역색인
  - [53-network-incidents](../53-network-incidents/2-summary.md) — 실사건
- man page (작성 환경 Ubuntu 24.04 로컬 man과 대조)
  - ss(8) — 옵션, STATE-FILTER, EXPRESSION, `-o` 타이머, `-m` skmem <https://man7.org/linux/man-pages/man8/ss.8.html>
  - tcpdump(1)(Ubuntu 8절) — `-i any`, `-d`, `-K`, `-Q`, `-s` 기본 262144, `dropped by kernel` <https://www.tcpdump.org/manpages/tcpdump.1.html>
  - pcap-filter(7) — 한정자, `proto[expr:size]`, `tcpflags`·`icmptype`, IPv6 인덱스 제약 <https://www.tcpdump.org/manpages/pcap-filter.7.html>
  - curl(1) 8.5.0 — `--write-out` 시간 변수, `--resolve`, `--connect-to`, `--connect-timeout`, `--http3` <https://curl.se/docs/manpage.html>
  - openssl-s_client(1) 3.0 — `-servername` 기본값, `-showcerts`는 검증된 체인이 아님, `-verify_return_error`, `-status` <https://docs.openssl.org/3.0/man1/openssl-s_client/>
  - dig(1) BIND 9.18 — `+trace`, `+search` 기본 꺼짐, `+cd`, `+norecurse` <https://bind9.readthedocs.io/en/stable/manpages.html>
  - mtr(8) 0.95 — `-r`·`-w`·`-c`·`-n`·`-z`·`-T`·`-P`·`-u` <https://github.com/traviscross/mtr>
  - ip-route(8) — `ip route get`, `fibmatch`, `from`·`oif`·`mark` <https://man7.org/linux/man-pages/man8/ip-route.8.html>
  - tracepath(8) — 경로 MTU 발견, 권한 불필요 <https://man7.org/linux/man-pages/man8/tracepath.8.html>
  - nsenter(1) — `-n` 네트워크 네임스페이스 진입 <https://man7.org/linux/man-pages/man1/nsenter.1.html>
  - iptables-extensions(8) REJECT — `--reject-with` 기본값 `icmp-port-unreachable`, `tcp-reset` <https://man7.org/linux/man-pages/man8/iptables-extensions.8.html>
  - undici `Client`(`connectTimeout` 기본 10e3 ms)·`Errors`(`ConnectTimeoutError`, `UND_ERR_CONNECT_TIMEOUT`) <https://github.com/nodejs/undici/tree/main/docs/docs/api>
  - MDN `AbortSignal.timeout()` — 시간 초과 시 `TimeoutError` DOMException <https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static>
- BPF
  - Linux kernel docs "Linux Socket Filtering aka Berkeley Packet Filter (BPF)" — `SO_ATTACH_FILTER`, tcpdump `-ddd` <https://docs.kernel.org/networking/filter.html>
  - McCanne & Jacobson, "The BSD Packet Filter: A New Architecture for User-level Packet Capture", USENIX Winter 1993
- Wireshark 사용자 안내서 — 캡처 필터(libpcap 문법) <https://www.wireshark.org/docs/wsug_html_chunked/ChCapCaptureFilterSection.html>, 표시 필터 <https://www.wireshark.org/docs/wsug_html_chunked/ChWorkBuildDisplayFilterSection.html>, TCP Analysis 플래그 <https://www.wireshark.org/docs/wsug_html_chunked/ChAdvTCPAnalysis.html>, 표시 필터 필드 참조(`tcp.flags.reset`) <https://www.wireshark.org/docs/dfref/t/tcp.html>
