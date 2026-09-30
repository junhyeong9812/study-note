# network/49-what-happens-when-url — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 구간 순서와 끝 신호

```text
 0 브라우저  URL 파싱·IDN·HSTS·HTTP 캐시 조회      끝: 캐시 적중이면 여기서 표시            (34)
 1 DNS      stub -> 재귀 -> 권한                 끝: A/AAAA 응답                         (27, 28)
 2 TCP      3-way handshake                      끝: connect() 성공                      (15, 26)
 3 TLS      SNI·ALPN·키 교환·인증서 검증            끝: Finished 교환 + 검증 통과             (29, 30)
 4 HTTP     요청·응답 (리다이렉트면 0으로)           끝: 본문 끝(Content-Length·chunked·END_STREAM) (33, 40)
 5 렌더링    파싱 -> DOM/CSSOM -> 레이아웃 -> 페인트   끝: 첫 화면 표시                         (web-platform)
```

- 하위 자원마다 1~4가 다시 돈다. 같은 출처에 놀고 있는 연결이 있으면 재사용으로 1~3을 건너뛴다. http/1.1에서 동시에 받으면 같은 출처라도 새 연결을 더 열어 2~3을 다시 치른다.

### 2. 26번과의 차이

- 26번은 패킷 하나를 **공간**으로 따라간다. 프로세스 → 커널 → NIC → 스위치 → 라우터 → 서버로 가며 헤더가 어떻게 바뀌는지 본다.
- 49번은 페이지 로드 하나를 **시간**으로 따라간다. 프로토콜 단계마다 RTT와 실패 모양을 본다.
- 49번의 "TCP 연결" 한 단계(SYN → SYN-ACK)는 26번의 여행을 왕복으로 한 번 한다. 라우팅·ARP·NAT·방화벽·accept 큐가 모두 그 안에 들어 있다.

### 3. 첫 바이트까지 RTT

```text
  TCP + TLS 1.2 새 연결 : TCP 1 + TLS 2 + 요청 1 = 4 RTT  -> 400ms
  TCP + TLS 1.3 새 연결 : TCP 1 + TLS 1 + 요청 1 = 3 RTT  -> 300ms
  QUIC 새 연결          : QUIC(전송+TLS) 1 + 요청 1 = 2 RTT -> 200ms
  이미 열린 연결 재사용   : 요청 1 = 1 RTT                  -> 100ms
```

- 서버 처리 시간은 제외한 최소값이다. 근거는 29번(1.2 = 2-RTT, 1.3 = 1-RTT)과 37번이다.
- 새 연결 TLS 1.2와 재사용 연결의 차이는 300ms다. 연결 재사용이 가장 큰 절약이다.

### 4. 브라우저 전처리와 HSTS

- 세 가지: URL인지 검색어인지 판단(+IDN 변환), HSTS 목록 확인, HTTP 캐시 조회.
- HSTS 호스트면 UA는 요청 전에 스킴을 `https`로 바꿔야 한다(MUST). 명시 포트 80은 443으로 바꾼다(RFC 6797 §8.3). 그래서 평문 HTTP 요청이 아예 나가지 않는다.
- TLS 오류가 나면 UA는 연결을 끊어야 한다(MUST, §8.4). 사용자에게 "그래도 진행" 선택지를 주지 않는 것이 권고다(§12.1). 사용자는 경고를 넘길 수 없다.

### 5. 렌더 차단과 파서 차단

- CSS(`<link rel=stylesheet>`)는 **렌더 차단**이다. 뒤 규칙이 앞 규칙을 덮을 수 있어 CSSOM이 완성될 때까지 그리지 않는다.
- `async`·`defer` 없는 `<script src>`는 **파서 차단**이다. 받아서 실행할 때까지 HTML 파싱이 멈춘다.
- 서드파티 스크립트 경로
  - 새 출처라 DNS(구간 1)부터 다시 한다. 그 출처의 DNS가 캐시에 없으면 여러 RTT가 든다.
  - TCP(2)와 TLS(3)로 2 RTT가 더 든다.
  - 요청(4)과 서버 처리 시간이 붙는다.
  - 그동안 파서가 멈춰 첫 화면도 멈춘다. 그 출처가 응답하지 않으면 TCP 타임아웃만큼 멈출 수 있다.

### 6. `curl -w`로 구간 시간

- 네 값은 모두 **요청 시작부터의 누적 시간**이다(curl(1)). 구간 시간은 앞 값과의 차이다.

```text
  DNS  = time_namelookup                         = 1ms
  TCP  = time_connect - time_namelookup           = 34 - 1  = 33ms
  TLS  = time_appconnect - time_connect           = 73 - 34 = 39ms
  TTFB = time_starttransfer - time_appconnect     = 111 - 73 = 38ms (요청 왕복 + 서버 처리)
```

- TCP·TLS·TTFB가 비슷하다. RTT가 약 33~39ms인 경로에서 TLS 1.3 1-RTT로 해석된다.

### 7. 구간 건너뛰기

- DNS 건너뛰기: `--resolve example.com:443:203.0.113.50`. 이름은 그대로 두고 주소만 지정한다. 되면 DNS가 범인이다.
- CDN 건너뛰기: `--connect-to example.com:443:origin.internal:443`. 원점에 직접 붙는다.
- `--connect-to`는 네트워크 연결에만 쓰이고 TLS의 SNI·인증서 검증·앱 프로토콜의 호스트명에는 영향을 주지 않는다(curl(1)). 그래서 "원점도 `example.com` 이름으로 올바른 인증서를 주나"를 그대로 시험할 수 있다.

### 8. 증상 → 구간 → 첫 도구

```text
  (a) ERR_NAME_NOT_RESOLVED      -> 1 DNS    -> getent hosts, dig, dig +trace          (27)
  (b) 즉시 ECONNREFUSED          -> 2 TCP    -> 서버 ss -ltn(리슨 중인가), 방화벽 REJECT   (15, 48)
                                               (tcpdump에 RST 또는 ICMP port-unreachable)
  (c) 30초+ 멈춤 뒤 시간 초과      -> 2 TCP    -> tcpdump로 SYN 재전송 확인, ip route get, mtr (15, 26)
  (d) 서버 간만 PKIX 실패          -> 3 TLS    -> openssl s_client -servername -showcerts (30)
  (e) 200인데 하얀 화면            -> 5 렌더링  -> 개발자 도구 Network(차단 자원 Timing)    (web-platform)
```

- (c)의 멈춤 길이는 앱·브라우저의 connect 타임아웃이 정한다. 타임아웃이 없으면 리눅스 기본값에서 약 2분(6.5+ 약 131초, 그 전 약 127초) 뒤 `ETIMEDOUT`이 난다(15번).
- 매핑은 "처음 볼 곳"이다. 확정은 도구 결과로 한다.

### 9. DNS 전환 뒤 옛 서버로 가는 일부

- 원인 층: DNS 캐시 계층(OS·재귀 해석기·브라우저)과 **자체 정책으로 캐시하는 런타임**(JVM `InetAddress`)이다. 남은 TTL 동안, 또는 런타임 정책 시간 동안 옛 IP를 쓴다(28번).
- 사전 대처 순서
  1. 전환 전에 TTL을 낮춘다.
  2. **옛 TTL만큼** 기다린다(낮춘 값이 퍼질 때까지).
  3. 레코드를 바꾼다.
  4. 옛 서버는 옛 TTL이 지날 때까지 살려 둔다.
  5. 런타임 캐시 설정(`networkaddress.cache.ttl`)을 확인한다.

### 10. 리다이렉트 루프

- 루프: 브라우저 → CDN은 HTTPS다. CDN → 원점은 HTTP다. 원점은 "HTTP로 왔다"고 보고 `https://`로 301을 준다. CDN은 그 301을 브라우저에 전달하고, 브라우저는 다시 HTTPS로 CDN에 온다. 이 과정이 반복된다.
- 확인: `curl -sSIL https://example.com/ | grep -Ei '^(HTTP|location)'`에 같은 URL로의 301/302가 반복된다. `--connect-to`로 원점에 직접 HTTP로 붙어 보면 원점이 리다이렉트를 만드는 것이 보인다.
- 수정: TLS 종단 위치를 정한다. 원점은 `X-Forwarded-Proto` 같은 전달 헤더로 원래 스킴을 판단하게 한다. 또는 CDN → 원점 구간도 HTTPS로 붙게 한다(46, 47번).
