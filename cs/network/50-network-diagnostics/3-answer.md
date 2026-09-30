# network/50-network-diagnostics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 도구 지도

```text
  도구              답하는 질문                                  보는 곳
  getent hosts      앱이 이 이름을 어떤 주소로 푸나?               OS 해석 경로(nsswitch·/etc/hosts·DNS)
  dig               DNS 서버는 무엇이라고 답하나? TTL·상태는?       DNS 서버에 직접
  ip route get      커널은 어느 다음 홉·인터페이스·출발 주소로 보내나? 내 커널 FIB
  mtr / tracepath   경로의 어느 홉에서 손실·지연? 경로 MTU는?        경로 위 라우터의 ICMP 응답
  tcpdump           패킷이 실제로 오가나? 누가 RST·FIN을 보냈나?     내 호스트의 캡처 지점
  ss                소켓 상태·큐·RTT·cwnd·타이머는?                내 커널 소켓 표
  openssl s_client  TLS 버전·암호군·ALPN·인증서 체인은?             TLS 핸드셰이크(클라이언트 입장)
  curl -v / -w      HTTP 요청이 어디서 멈추나, 구간별 몇 초인가?      앱 계층 전체(클라이언트 입장)
```

### 2. 추측 진단의 비용

- 틀린 가설을 고치느라 시간을 쓴다. 증상이 우연히 사라지면 틀린 수정이 "해결책"으로 남는다.
- 재시작은 증거를 지운다. CLOSE-WAIT 누적은 앱이 `close()`를 안 한 버그다. 재시작하면 프로세스의 fd가 모두 닫혀 CLOSE-WAIT 소켓이 사라진다.
- 그래서 어느 연결 코드가 문제였는지(상대 주소) 알 수 없게 되고, 며칠 뒤 `EMFILE`로 재발한다(20번).
- 재시작 전에 `ss -s`, `ss -tanp state close-wait`, fd 개수를 저장한다.

### 3. `dig` vs `getent`

- `dig`은 DNS 서버에 직접 묻는다. `/etc/hosts`·nsswitch를 거치지 않고, 기본적으로 검색 목록도 쓰지 않는다(dig(1) `+search`).
- 앱은 `getaddrinfo()`로 nsswitch 순서(`/etc/hosts` → DNS 등)와 `resolv.conf`의 검색 목록·ndots를 따른다. 런타임 캐시(JVM `InetAddress`)도 끼어 있다(27, 28번).
- 앱과 같은 OS 경로는 `getent hosts 이름`이다. 컨테이너 앱이면 그 네트워크 네임스페이스 안에서 확인한다.

### 4. 중간 홉만의 손실

- 경로에 손실은 없다. 목적지가 0%이므로 패킷은 5번 홉을 잘 **지나갔다**.
- 5번 라우터가 자기 앞으로 온 탐침(ICMP 응답 생성)을 낮은 우선순위로 처리하거나 속도 제한을 건 것이다(09번).
- 진짜 손실은 **그 홉부터 목적지까지 이어지는** 손실이다. 예: 5번 40%, 6번 40%, …, 목적지 40%.

### 5. BPF 필터

- libpcap이 필터 식을 BPF 프로그램으로 컴파일하고, 이를 커널의 소켓에 붙인다(`SO_ATTACH_FILTER`). 커널이 패킷마다 실행해 맞는 것만 캡처 버퍼로 넘긴다(kernel docs).
- `tcpdump -d`는 컴파일된 명령어 열을 사람이 읽는 형태로 출력하고 멈춘다(tcpdump(1)). 이더타입으로 IPv6/IPv4를 가르고, 프로토콜이 TCP인지, 목적지 포트가 443(0x1bb)인지 비교한 뒤 `ret #262144`(캡처) 또는 `ret #0`(버림)으로 끝난다.
- 좁은 필터는 맞지 않는 패킷이 사용자 공간으로 올라오지 않게 한다. 캡처 버퍼 부담이 줄어 `dropped by kernel`이 줄고, 분석할 양도 준다.

### 6. RST가 "없다"는 결론의 함정

- `tcp[…]`·`udp[…]` 헤더 인덱스 연산은 IPv4에만 적용된다(pcap-filter(7)). 연결이 IPv6면 RST가 있어도 잡히지 않는다.
  - IPv6는 `ip6 and tcp`처럼 넓게 뜬 뒤 Wireshark 표시 필터 `tcp.flags.reset == 1`로 거른다. `tcpdump -d`로 필터가 무엇을 검사하는지 확인할 수 있다.
- 인터페이스 함정: 다른 인터페이스를 떴을 수 있다(본딩·VLAN·컨테이너 veth). `-i any`로 뜨거나 `ip route get`으로 실제 나가는 인터페이스를 확인한다.
- 추가로, 서버의 RST는 서버 쪽에서만 보일 수 있다. 중간 장비가 만든 RST는 한쪽에만 온다. 양쪽을 같이 떠야 한다.

### 7. s_client의 `0 (ok)`를 믿으면 안 되는 이유

- s_client는 `-verify_hostname`을 주지 않으면 **호스트명을 검증하지 않는다**. `0 (ok)`는 체인이 통과했다는 뜻일 뿐이다(작성 환경 예시: 같은 서버에 `-verify_hostname wrong.example.org`를 주면 `62 (hostname mismatch)`).
- IP로 붙으면 SNI가 빠진다(`-servername`은 `-connect`가 DNS 이름 형식일 때만 자동으로 채워진다). 서버는 기본 인증서를 주고, 앱은 SNI를 보내 다른 인증서를 받았을 수 있다.
- 또 s_client는 검증 오류가 나도 핸드셰이크를 계속한다.
- 재현 명령

```bash
openssl s_client -connect 10.0.0.5:443 -servername api.example.com \
        -verify_hostname api.example.com -verify_return_error -showcerts </dev/null
```

### 8. `curl -v`의 구간 줄과 격리 옵션

```text
  DNS  : "Host … was resolved." / "IPv4: …" 줄
  TCP  : "Trying ip:443..." -> "Connected to …" 줄
  TLS  : "TLSv1.3 (OUT) … Client hello" ~ "SSL connection using …", "ALPN: server accepted h2",
         "subjectAltName … matched", "SSL certificate verify ok."
  HTTP : ">" 요청 헤더, "<" 응답 헤더
```

- 멈춘 마지막 줄 다음 구간이 멈춘 구간이다.
- `--resolve host:port:addr`는 DNS 해석을 건너뛰고 지정 주소를 쓴다. 이름(Host·SNI)은 유지한다.
- `--connect-to`는 연결 대상만 바꾼다. SNI·인증서 검증·앱 프로토콜의 호스트명은 원래 이름을 유지한다(curl(1)). CDN·LB를 건너뛰고 원점을 직접 시험할 때 쓴다.

### 9. SYN이 보이는데 연결이 안 될 때

- 같은 캡처에서 **SYN-ACK가 나가는지** 본다.
  - 나가면 문제는 돌아오는 길이다. 클라이언트 쪽 캡처와 비대칭 경로를 본다(26번).
  - 안 나가면 방화벽과 리슨 상태를 본다. `nft list ruleset`·`iptables -vnL`의 카운터, `ss -ltn`(해당 포트·주소로 리슨 중인가), `nstat`의 리슨 드롭 카운터(15번).
- 수신 캡처 지점은 netfilter보다 **앞**이다(25번). 그래서 tcpdump에 보인 패킷도 그 뒤 방화벽에서 DROP될 수 있다. "보였다"는 "NIC·드라이버까지 왔다"는 뜻이다.

### 10. `persist` 타이머와 대량 timewait

- `persist`는 zero window 탐침 타이머다(ss(8)). 상대의 수신 윈도가 0이라 보내지 못하고 탐침만 보내는 중이다. 상대 앱이 읽지 않고 있다(17번).
  - 다음: 상대 쪽 `ss`에서 그 연결의 Recv-Q가 쌓였는지, 상대 앱이 멈췄는지 본다.
- timewait 수만 개는 **먼저 닫은 쪽**이 짧은 연결을 대량으로 열고 닫고 있다는 뜻이다(20번).
  - 다음: `ss -tan state time-wait`의 상대 주소·포트별 개수로 어느 목적지인지 본다. 클라이언트 쪽이면 임시 포트 고갈(`EADDRNOTAVAIL`) 위험이 있다. 연결 재사용(keep-alive·풀)이 1순위 대처다(20, 35번).
