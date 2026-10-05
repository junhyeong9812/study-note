# network/49-what-happens-when-url — 주소창에 URL을 치고 화면이 뜨기까지, 구간마다 어디서 깨지나 — 정리 (힌트)

## 해결하는 문제

사용자가 보내는 신고는 한 문장이다. "사이트가 안 떠요."\
그런데 그 뒤에는 브라우저, DNS, TCP, TLS, HTTP, 렌더링이라는 여섯 구간이 줄지어 있다.\
구간마다 실패 모양이 다르다. 어느 구간인지 모르면 엉뚱한 곳을 고친다.

이 노트는 **페이지 한 번 열기**를 시간 순서로 따라간다.\
구간마다 "무엇을 하고, 몇 RTT가 들고, 어떻게 깨지고, 무엇으로 보나"를 한 장에 모은다.\
각 구간의 원리는 해당 leaf 노트의 몫이다. 여기서는 **순서와 이음새, 그리고 구간별 실패 지도**만 본다.

쉬운 예: 처음 가는 식당에서 밥을 먹는 과정이다.

```text
  주소 찾기(지도 앱)  ->  찾아가기(길)  ->  신분 확인(예약자 맞나)  ->  주문  ->  상 차리기
     DNS                  TCP              TLS                       HTTP     렌더링
```

- 지도 앱이 옛 주소를 알려 주면 엉뚱한 곳에 간다(DNS 캐시).
- 길이 막히면 도착을 못 한다(TCP 타임아웃).
- 예약 명단에 이름이 없으면 들어가지 못한다(인증서 이름 불일치).
- 주방이 멈추면 주문만 받고 음식이 안 나온다(502·504).
- 음식이 다 나왔는데 수저가 안 와서 못 먹는다(렌더 차단 자원).

똑같은 구조다.\
**대체로 앞 구간의 결과가 다음 구간의 입력이고**, 실패 모양을 보면 몇 번째 구간인지 알 수 있다.\
다만 겹치는 곳도 있다. TLS 1.3은 Finished와 첫 요청을 함께 보내고, 브라우저는 HTML을 다 받기 전부터 파싱한다(아래 1·8절).

실무 예:
- 배포 뒤 "일부 사용자만" 옛 서버로 간다. DNS 캐시 구간 문제다(28번).
- 브라우저는 되는데 서버 간 호출만 TLS 에러다. 인증서 체인 구간 문제다(30번).
- 응답은 200인데 화면이 몇 초 동안 하얗다. 렌더링 구간 문제다.

### 26번과 무엇이 다른가

```text
  26 packet-journey  : 패킷 하나를 "공간"으로 따라감
                       프로세스 -> 커널 -> NIC -> 스위치 -> 라우터 -> ... -> 서버 프로세스
                       (장비·계층마다 헤더가 어떻게 바뀌나)

  49 (이 노트)        : 페이지 로드 하나를 "시간"으로 따라감
                       URL -> DNS -> TCP -> TLS -> HTTP -> 렌더링 -> (하위 자원마다 반복)
                       (프로토콜 단계마다 몇 RTT가 들고, 어디서 멈추나)
```

- 49의 TCP·TLS·HTTP 단계 **하나하나가** 26의 패킷 여행을 여러 번 한다.
- 그래서 49에서 "TCP 연결 타임아웃"을 만나면, 원인을 좁히는 일은 26번의 구간 지도로 내려가서 한다.

## 동작·원리

### 1. 한 장 타임라인 — 새 HTTPS 연결로 첫 페이지 열기

```text
 브라우저                                     네트워크                               서버 쪽
 --------                                     --------                               -------
 (0) URL 파싱, 검색어인가? IDN 변환, HSTS 확인, HTTP 캐시 확인      (네트워크 없음일 수도)
 (1) DNS   : 이름 -> IP         ---- 질의 ---->  재귀 해석기 (캐시 미스면 루트/TLD/권한)
                                <---- A/AAAA --                                          0 ~ 여러 RTT
 (2) TCP   : SYN               ---------------------------------------------->  커널
             SYN-ACK           <----------------------------------------------            1 RTT
             ACK
 (3) TLS   : ClientHello(SNI, ALPN, key_share) ------------------------------->  TLS 종단(LB·CDN·서버)
             ServerHello .. 인증서 .. Finished <-------------------------------          1 RTT (1.3)
             인증서 체인·호스트명 검증
 (4) HTTP  : Finished + GET /  ----------------------------------------------->  앱 처리
             응답 헤더 + 본문   <-----------------------------------------------          1 RTT + 서버 처리 시간
 (5) 렌더링 : HTML 파싱 -> DOM
             CSS·JS·이미지 발견 -> 하위 자원 요청  (출처가 새로우면 (1)~(4) 반복)
             스타일 -> 레이아웃 -> 페인트 -> 합성 -> 화면
```

- *RTT(Round-Trip Time)*: 패킷이 상대에게 갔다가 응답이 돌아오기까지의 시간이다.
- *출처(origin)*: 스킴 + 호스트 + 포트의 묶음이다. 브라우저는 연결·보안 정책을 출처 단위로 다룬다.
- *TLS 종단*: TLS 핸드셰이크를 실제로 받는 곳이다. 서버 앱이 아니라 CDN 엣지나 로드밸런서인 경우가 많다(46, 47번).

### 2. 구간별 한 줄 요약과 담당 노트

```text
 구간        하는 일                                      끝났다는 신호                     노트
 ---------  -------------------------------------------  -------------------------------  ------------
 0 브라우저   URL 파싱, HSTS로 http->https, 캐시 조회        캐시 적중이면 여기서 끝             34, (web-platform)
 1 DNS       stub -> 재귀 -> 권한, 캐시 계층               A/AAAA 응답                        27, 28
 2 TCP       3-way handshake (내부에 26번 여행 전체)        connect() 성공                     15, 26
 3 TLS       SNI·ALPN 협상, 키 교환, 인증서 검증             Finished 교환, 검증 통과            29, 30, 31
 4 HTTP      요청·응답, 리다이렉트, 압축·캐시 헤더           응답 본문 끝(길이·프레이밍)          33, 34, 39, 40
 5 렌더링     파싱, 하위 자원, 레이아웃·페인트               첫 화면 표시                       (web-platform)
 경로 위     CDN·LB·프록시·방화벽·NAT                        (각 구간 안에 끼어 있음)           46, 47, 48, 11
```

### 3. 구간 0 — 브라우저가 네트워크에 나가기 전에 하는 일

```text
  "example.com/뉴스"  --URL인가 검색어인가?-->  URL
        |
        v
  호스트명 IDN 변환 (비ASCII -> punycode "xn--...")
        |
        v
  HSTS 목록에 있나?  --있으면-->  http:// 를 https:// 로 바꿈 (80 -> 443)
        |
        v
  HTTP 캐시에 신선한 응답이 있나?  --있으면-->  네트워크 없이 표시
        |
        v
  (1) DNS로
```

- *HSTS(HTTP Strict Transport Security)*: "이 호스트는 HTTPS로만 접속하라"는 정책이다. 브라우저가 기억해 둔 호스트면 요청을 보내기 전에 스킴을 `https`로 바꿔야 한다(MUST, RFC 6797 §8.3).
  - HSTS 호스트에서는 TLS 오류가 나면 연결을 끊어야 한다(MUST, §8.4). 사용자가 경고를 무시하고 넘어가는 선택지도 두지 않는 것이 권고다(§12.1). 그래서 HSTS 사이트의 인증서 오류는 "우회 불가"로 보인다.
- 캐시 적중이면 1~4구간이 통째로 사라진다. "내 브라우저에서는 옛 화면이 보인다"는 이 구간 문제다(34번).
- 조건부 요청(`If-None-Match` → 304)이면 1~4구간은 거치되 본문은 받지 않는다(34번).

### 4. 구간 1 — DNS: 이름을 주소로

```text
  브라우저/OS 캐시 --미스--> 재귀 해석기 캐시 --미스--> 루트 -> TLD -> 권한 서버
       (0 RTT)                 (1 RTT to 해석기)            (해석기가 여러 번 왕복)
```

- 캐시 계층이 여럿이라 **걸리는 시간이 0부터 수백 ms까지** 넓게 퍼진다(28번).
- 앱이 받는 답은 A(IPv4)와 AAAA(IPv6) 두 종류일 수 있다.
  - 둘 다 있으면 *Happy Eyeballs*를 구현한 클라이언트(주요 브라우저, curl 등)는 한쪽이 느릴 때 다른 쪽으로 빨리 넘어간다. 구현하지 않은 런타임은 주소 목록을 순서대로 시도하기도 한다. AAAA 질의를 먼저 보내고 곧바로 A 질의를 보내야 한다(SHOULD). 연결 시도 사이 간격의 권장값 하나는 250ms다(RFC 8305 §3, §5).
- DNS의 HTTPS 레코드(RFC 9460)는 첫 접속 전에 `h3` 지원을 알릴 수 있다(37번).
- 실패는 `NXDOMAIN`(이름 없음)과 `SERVFAIL`(답을 못 만듦)로 갈린다. Java에서는 둘 다 `UnknownHostException` 하나로 뭉개진다. getaddrinfo를 쓰는 런타임(Node `dns.lookup` 등)에서는 NXDOMAIN이 `ENOTFOUND`, SERVFAIL이 `EAI_AGAIN`으로 갈리기도 한다(27번).

### 5. 구간 2 — TCP: 경로가 열리나

- `connect()`가 SYN을 보내고 SYN-ACK를 받으면 성공이다. 1 RTT가 든다(15번).
- 이 한 번의 왕복 **안에** 26번의 여행 전체가 들어 있다. 라우팅, ARP, NAT, 방화벽, 서버의 accept 큐를 모두 지난다.
- 실패 모양은 두 가지다.
  - 즉시 실패(`ECONNREFUSED`): 누군가 거절 응답을 돌려줬다. 서버 커널의 RST(포트 닫힘)일 수도 있고, 방화벽 REJECT의 ICMP port-unreachable(iptables 기본)이나 RST일 수도 있다. 리눅스는 둘 다 `ECONNREFUSED`로 바꾼다. REJECT 종류에 따라 `EHOSTUNREACH`가 나오기도 한다(15, 48번).
  - 한참 뒤 실패(`ETIMEDOUT`): SYN이 어딘가에서 조용히 버려졌다. 리눅스 기본값(`tcp_syn_retries`=6)에서는 SYN을 재전송하다 약 2분 뒤 포기한다. 6.5+ 기본 설정(`tcp_syn_linear_timeouts`=4)에서는 약 131초, 그 전 커널은 약 127초다(15번, 커널 문서 ip-sysctl, tcp(7)). 앱은 connect 타임아웃을 따로 걸어야 한다.

### 6. 구간 3 — TLS: 상대가 맞나, 무엇으로 말할까

```text
  ClientHello:  SNI = "example.com"      -> 서버가 어느 인증서를 줄지 고름
                ALPN = h2, http/1.1       -> 이 연결 위에서 쓸 HTTP 버전
                key_share                 -> 키 교환 값 (1.3은 추측해서 미리 보냄)
  서버 응답:    인증서 체인(리프 + 중간)     -> 클라이언트가 루트 스토어까지 경로 검증
                                           -> SAN에 "example.com"이 있나 (호스트명 검증)
```

- TLS 1.3 전체 핸드셰이크는 1 RTT, 1.2는 2 RTT다(29번).
- 체인 검증과 호스트명 검증은 **별개**다. 둘 중 하나만 틀려도 실패한다(30번).
- ALPN 결과가 4구간의 모양을 정한다. `h2`면 한 연결에서 여러 요청을 섞고(36번), `http/1.1`이면 연결당 한 번에 한 요청이다(35번).

### 7. 구간 4 — HTTP: 요청과 응답

```text
  GET / HTTP/2  (:authority example.com)
      |
      v
  [CDN 엣지] --캐시 적중--> 바로 응답                       (47)
      | 미스
      v
  [LB / 리버스 프록시] --> [앱 서버] --> DB·다른 서비스       (46)
      |
      v
  301/302 + Location  --> 새 URL로 구간 0부터 다시 (다른 호스트면 DNS부터)
  200 + 본문          --> 구간 5
  502/504             --> 게이트웨이가 상류 문제를 대신 알린 에러 (33)
  503                 --> 앱 자신의 과부하·점검일 수도, LB가 만든 것일 수도 (33)
```

- 리다이렉트는 구간 0으로 돌아가는 **루프**다. 호스트가 바뀌면 DNS·TCP·TLS를 다시 치른다.
- 응답의 끝은 TCP가 아니라 HTTP가 정한다. `Content-Length`, chunked, HTTP/2 `END_STREAM`이 "본문 끝"을 알린다(40번, 19번).
- 502·504는 앱이 아니라 **게이트웨이가 상류 문제를 대신 알리는** 코드다. 어느 층이 응답을 만들었는지부터 본다(33번).

### 8. 구간 5 — 렌더링: 바이트가 화면이 되기까지

```text
  HTML 바이트 --파싱--> DOM 트리
                           |  <link rel=stylesheet>  -> CSS 요청 (렌더 차단)
                           |  <script src> (async/defer 없음) -> 파싱 멈추고 받아서 실행 (파서 차단)
                           |  <img>, 폰트          -> 요청은 하되 파싱은 계속
                           v
  CSS --파싱--> CSSOM  --+--> 렌더 트리 -> 레이아웃 -> 페인트 -> 합성 -> 화면
```

- CSS는 **렌더 차단** 자원이다. 뒤의 규칙이 앞 규칙을 덮을 수 있어서, CSSOM이 완성될 때까지 그리지 않는다(MDN "Critical rendering path").
- `async`·`defer`가 없는 스크립트는 **파서 차단**이다. 받아서 실행할 때까지 HTML 파싱이 멈춘다(MDN 같은 문서).
- 하위 자원마다 1~4구간이 다시 돈다.
  - 같은 출처에 놀고 있는 연결이 있으면 재사용한다. h2·h3는 대개 한 연결로 다중화한다(36번).
  - http/1.1에서 동시에 여러 자원을 받으면, 같은 출처라도 연결을 몇 개 더 열고 그 연결마다 TCP·TLS를 치른다(35번).
  - 새 출처(서드파티 스크립트, 폰트 CDN)면 DNS·TCP·TLS를 새로 치른다.
- 렌더링 파이프라인 자체의 원리는 web-platform 영역의 몫이다(아래 「관련 주제」).

### 9. RTT 셈 — 첫 바이트까지 몇 왕복인가

```text
  조건 (DNS 캐시 적중 가정)                       연결 준비        요청·응답     첫 바이트까지
  --------------------------------------------   ------------    ----------   -------------
  TCP + TLS 1.2, 새 연결                           1 + 2 RTT        1 RTT         4 RTT
  TCP + TLS 1.3, 새 연결                           1 + 1 RTT        1 RTT         3 RTT
  QUIC(HTTP/3), 새 연결                            1 RTT            1 RTT         2 RTT
  QUIC 또는 TLS 1.3 0-RTT 재개                      0 (요청 동봉)     1 RTT         1 RTT (+TCP면 1)
  이미 열린 연결 재사용                              0                1 RTT         1 RTT
```

- 근거는 29번(TLS 1.2 = 2-RTT, 1.3 = 1-RTT, 0-RTT)과 37번(QUIC = 전송+암호 핸드셰이크 1 RTT)이다.
- TCP 위 TLS 1.3 0-RTT도 TCP 핸드셰이크 1 RTT는 따로 든다.
- RTT가 100ms(예시)인 사용자에게 새 연결 TLS 1.2는 첫 바이트까지 최소 400ms, 재사용 연결은 100ms다. **연결 재사용이 가장 큰 절약**인 이유다.

## 쓰이는 자료구조·알고리즘

페이지 한 번 열기는 "캐시 조회 → 미스면 네트워크"의 연쇄다. 캐시마다 키와 만료 규칙이 다르다.

```text
  위치            캐시/구조                 키                            만료                    노트
  브라우저         HSTS 목록                 호스트명(하위 도메인 포함 옵션)   max-age                 (RFC 6797)
  브라우저         HTTP 캐시                  메서드 + URI + Vary 헤더 값     Cache-Control 수명       34
  브라우저·OS·해석기 DNS 캐시                  (이름, 타입)                   레코드 TTL               28
  브라우저         연결 풀                    출처(스킴·호스트·포트)          idle timeout            35
  TLS             세션 티켓 저장               서버                          티켓 수명               29
  HTTP/2          HPACK 동적 테이블           인덱스                        FIFO 축출               36
  렌더러           DOM 트리 / CSSOM           -                             -                      (web-platform)
```

- **해시 + TTL 만료**: DNS 캐시·HSTS 목록·연결 풀은 모두 "키로 찾고, 시간이 지나면 버린다"는 모양이다. 개념은 [해시맵](../../data-structure/05-hashmap/2-summary.md), 용량 한도가 붙으면 [LRU 캐시](../../data-structure/10-lru-cache/2-summary.md)다.
- **트리**: DNS 이름 공간은 트리이고, 재귀 해석기는 루트에서 잎으로 위임을 따라 내려간다(27번). DOM도 트리다.
- **의존 그래프**: 하위 자원은 "HTML → CSS → CSS가 부른 폰트"처럼 의존 관계를 가진다. 첫 화면까지의 시간은 이 방향 그래프에서 **가장 긴 차단 경로**가 정한다. 개념은 [그래프](../../data-structure/08-graph/2-summary.md).
- **상태 기계**: TCP 연결 상태(15, 19번)와 TLS 핸드셰이크 상태(29번)는 정해진 순서로만 전이한다. 순서가 어긋나면 RST나 alert로 끝난다.

## 적용 — 풀어나가는 법

### 1. 구간별 시간을 먼저 잰다 — `curl -w`

```bash
curl -sS -o /dev/null https://example.com/ -w '
dns    %{time_namelookup}
tcp    %{time_connect}
tls    %{time_appconnect}
ttfb   %{time_starttransfer}
total  %{time_total}
http   %{http_version}  ip %{remote_ip}
'
```

```text
  (예시 — 작성 환경에서 example.com, 값은 모두 "시작부터 누적" 초)
  dns    0.001013
  tcp    0.033997      -> TCP 핸드셰이크 = 0.034 - 0.001 ≈ 33ms (≈ 1 RTT)
  tls    0.073087      -> TLS = 0.073 - 0.034 ≈ 39ms (≈ 1 RTT, TLS 1.3)
  ttfb   0.111480      -> 요청~첫 바이트 = 0.111 - 0.073 ≈ 38ms (1 RTT + 서버 처리)
  total  0.111515
  http   2  ip 172.66.147.243
```

- 각 변수는 **요청 시작부터의 누적 시간**이다(curl(1) `--write-out`). 구간 시간은 앞 값과의 차이로 구한다.
- 가장 큰 차이가 나는 구간이 범인 후보다. 도구별 상세는 [50-network-diagnostics](../50-network-diagnostics/2-summary.md).

### 2. 구간을 하나씩 건너뛰어 격리한다

```bash
# DNS를 건너뛴다: 이름은 그대로(SNI·Host 유지), 주소만 지정
curl -v --resolve example.com:443:203.0.113.50 https://example.com/

# 특정 서버(예: CDN을 거치지 않고 원점)로 직접 — TLS의 SNI·인증서 검증은 원래 이름 기준
curl -v --connect-to example.com:443:origin.internal:443 https://example.com/

# HTTP 버전을 바꿔 본다 (ALPN 결과에 따른 차이 확인)
curl -v --http1.1 https://example.com/
curl -v --http2   https://example.com/

# 리다이렉트를 따라가며 각 단계를 본다
curl -sSIL https://example.com/ | grep -Ei '^(HTTP|location)'
```

- `--resolve`로 되면 DNS 구간 문제다. 안 되면 DNS는 무죄다.
- `--connect-to`는 연결만 바꾸고 SNI·인증서 검증·Host는 원래 이름을 쓴다(curl(1)). 그래서 "원점에서도 같은 인증서 문제가 나나"를 볼 수 있다.

### 3. 브라우저 안에서는 개발자 도구와 Resource Timing

- 개발자 도구 Network 탭의 Timing은 Queueing, Stalled, DNS Lookup, Initial connection(TCP와 TLS 포함), Request sent, Waiting (TTFB), Content Download로 나눠 보여 준다(Chrome DevTools 문서).
- 코드로는 Resource Timing API로 같은 구간을 잰다.

```js
// 페이지가 받은 자원마다 구간별 시간(ms)을 뽑는다
for (const e of performance.getEntriesByType('resource')) {
  console.log(e.name, {
    dns:  e.domainLookupEnd - e.domainLookupStart,
    tcp:  e.connectEnd - e.connectStart,          // TLS 시간 포함
    tls:  e.secureConnectionStart > 0 ? e.connectEnd - e.secureConnectionStart : 0,
    ttfb: e.responseStart - e.requestStart,
    body: e.responseEnd - e.responseStart,
  });
}
// 다른 출처 자원은 그 서버가 Timing-Allow-Origin 헤더를 주지 않으면 세부 값이 0으로 나온다.
```

- dns·tcp가 0이면 캐시된 DNS나 재사용 연결이다. 그 자체로 정보다.

### 4. 설계 단계에서 줄일 수 있는 RTT

```text
  구간        줄이는 수단                                              노트
  DNS        TTL을 너무 짧게 두지 않기, dns-prefetch                    28, (web-platform 13)
  TCP·TLS    연결 재사용(keep-alive·풀), TLS 1.3, 세션 재개, preconnect   35, 29
  HTTP       h2/h3 다중화, CDN 엣지 캐시, 캐시 헤더로 재요청 없애기         36, 37, 47, 34
  렌더링      CSS 최소·인라인, 스크립트 defer/async, 서드파티 출처 줄이기     (web-platform 13)
```

## 장애 시나리오와 대처

### 0. 구간별 실패 지도 — 증상에서 구간으로

```text
 구간      사용자·앱이 보는 것                                    먼저 볼 도구                        원인 노트
 -------  ----------------------------------------------------  --------------------------------   ---------
 0 브라우저 옛 화면이 보임 / HSTS 사이트 인증서 오류 우회 불가       강력 새로고침, 개발자 도구 캐시 표시    34, 29
 1 DNS    ERR_NAME_NOT_RESOLVED, UnknownHostException,          getent, dig, dig +trace             27, 28
          ENOTFOUND / 일부 사용자만 옛 IP로
 2 TCP    ECONNREFUSED(즉시) / ETIMEDOUT(기본 약 2분 뒤,          ip route get, tcpdump SYN, mtr      15, 48, 26
          앱 connect 타임아웃이 있으면 그 값),
          ERR_CONNECTION_TIMED_OUT
 3 TLS    인증서 이름 불일치, 체인 검증 실패, 만료,                 openssl s_client -servername        29, 30, 31
          handshake_failure alert, 프로토콜 버전 불일치
 4 HTTP   4xx·5xx, 502/504(게이트웨이), 리다이렉트 루프,            curl -v, curl -w, LB·CDN 로그        33, 35, 46, 47
          ERR_TOO_MANY_REDIRECTS, 응답 중간 끊김
 5 렌더링  200인데 하얀 화면, 스타일 없는 화면, 반쯤 그려지다 멈춤     개발자 도구 Network·Performance      (web-platform)
 전 구간   큰 것만 멈춤(인증서 교환·큰 응답)                         tracepath, ping -M do               10
```

- 표는 "처음 볼 곳"이지 확정이 아니다. 같은 에러가 다른 구간에서 날 수 있다.
- 에러 문자열별 역색인은 [52-network-symptom-index](../52-network-symptom-index/2-summary.md)가 맡는다.

### 1. DNS — 전환 뒤 일부 사용자만 옛 서버로 간다

- **현상**: 서버를 옮기고 DNS를 바꿨다. 대부분은 새 서버로 오는데 일부 사용자·일부 서비스는 계속 옛 서버로 간다.
- **보이는 형태**
  - 옛 서버 접근 로그에 트래픽이 줄지 않고 남는다.
  - `dig`은 새 IP를 주는데, 문제 호스트의 `getent hosts`나 앱은 옛 IP를 쓴다.
- **원인**: 캐시 계층마다 남은 TTL이 있다. JVM `InetAddress` 캐시처럼 레코드 TTL이 아니라 자체 정책으로 캐시하는 층도 있다(28번).
- **대처**
  - 전환 전에 TTL을 낮추고, **옛 TTL만큼** 기다린 뒤 바꾼다(28번).
  - 옛 서버는 옛 TTL이 지날 때까지 살려 둔다.
  - 런타임 캐시 설정(`networkaddress.cache.ttl` 등)을 확인한다.

### 2. TCP — 연결이 한참 멈췄다가 실패한다

- **현상**: 페이지 로드가 한참 멈췄다가 "연결 시간 초과"로 끝난다.
- **보이는 형태**
  - 브라우저 `ERR_CONNECTION_TIMED_OUT`, 앱 `ETIMEDOUT`·`connect timed out`.
  - 클라이언트 tcpdump에 SYN 재전송만 반복되고 SYN-ACK가 없다.
  - `curl -w`의 `time_connect`가 connect 타임아웃 값까지 늘어난다.
- **원인**: SYN이 경로 어딘가에서 조용히 버려졌다. 방화벽 DROP, 보안 그룹 누락, 라우팅 문제, 서버 accept 큐 넘침이 후보다(48, 15번).
- **대처**
  - 즉시 거절(`ECONNREFUSED`)인지 타임아웃인지부터 가른다. 거절이면 누군가 답을 했고, 타임아웃이면 아무도 답을 안 했다.
  - 타임아웃이면 26번의 구간 지도로 내려가 SYN이 어디까지 가는지 본다. 서버 쪽 tcpdump에 SYN이 오나가 첫 분기다.
  - 앱에는 connect 타임아웃을 짧게 따로 둔다(15번).

### 3. TLS — 브라우저는 되는데 서버 간 호출만 실패한다

- **현상**: 인증서 갱신 뒤 브라우저는 정상이다. 배치·백엔드 호출·`curl`만 TLS 에러다.
- **보이는 형태**
  - Java `PKIX path building failed`, curl `unable to get local issuer certificate`.
  - `openssl s_client -connect host:443 -servername host -showcerts`에 인증서가 1장만 보인다.
- **원인**: 서버가 중간 인증서를 보내지 않는다. 브라우저는 AIA로 받아 오거나(Chrome) 미리 받아 둔 중간 인증서로(Firefox) 빠진 중간을 채우는 경우가 많다. 서버 간 클라이언트(Java 기본값, OpenSSL 기반 curl 등)는 보통 그러지 않는다(30번).
- **대처**: 리프 + 중간(fullchain)을 설정한다. 배포 파이프라인에 체인 길이 검사를 넣는다(30번).
- **변형**: 같은 IP에 여러 도메인이 있는데 클라이언트가 SNI를 안 보내면 기본 인증서가 온다. 그 인증서에 이름이 없으면 호스트명 검증이 실패한다(29번).

### 4. HTTP — 간헐적인 502, 그리고 리다이렉트 루프

- **현상 A**: 트래픽이 많지 않은데 가끔 502가 난다. 재시도하면 된다.
  - **보이는 형태**: LB 로그의 502, 앱 서버 로그에는 해당 요청이 없다.
  - **원인**: LB가 재사용하려던 백엔드 연결을 백엔드가 idle timeout으로 막 닫았다. LB idle보다 백엔드 keep-alive가 짧은 역전 조합이다(35번).
  - **대처**: 구간마다 "재사용하는 쪽 idle < 받는 쪽 keep-alive"로 맞춘다(35번).
- **현상 B**: 브라우저가 `ERR_TOO_MANY_REDIRECTS`로 멈춘다.
  - **보이는 형태**: `curl -sSIL`에 같은 두 URL 사이 301/302가 반복된다.
  - **원인**: HTTP→HTTPS 전환을 두 층이 서로 다르게 판단한다. 예: CDN이 원점에 HTTP로 붙는데, 원점은 "HTTP로 왔으니 HTTPS로 가라"고 리다이렉트한다.
  - **대처**: TLS 종단 위치를 정하고, 원점은 `X-Forwarded-Proto` 같은 전달 헤더로 원래 스킴을 판단하게 한다(46, 47번).

### 5. 렌더링 — 응답은 200인데 화면이 몇 초 하얗다

- **현상**: 서버 응답 시간 지표는 정상인데 사용자는 하얀 화면을 오래 본다.
- **보이는 형태**
  - 개발자 도구 Network에서 HTML은 빨리 왔는데, `<head>`의 CSS나 동기 스크립트 하나가 늦게 끝난다.
  - 그 자원의 Timing에 DNS Lookup·Initial connection이 길다. 처음 보는 서드파티 출처라서다.
- **원인**
  - CSS는 렌더 차단, `async`·`defer` 없는 스크립트는 파서 차단이다(MDN).
  - 느린 출처 하나가 첫 화면 전체를 붙잡는다. 그 출처가 응답하지 않으면 TCP 타임아웃만큼 멈출 수도 있다.
- **대처**
  - 필수 CSS를 줄이거나 인라인한다. 스크립트는 `defer`·`async`로 바꾼다.
  - 꼭 필요한 서드파티 출처에는 `preconnect`를 둔다. 필수가 아니면 첫 화면 경로에서 뺀다.
  - 원리는 web-platform의 렌더링 파이프라인([web-platform/02-rendering-pipeline](../../web-platform/02-rendering-pipeline/2-summary.md))·크리티컬 패스([web-platform/13-critical-path-and-resource-loading](../../web-platform/13-critical-path-and-resource-loading/2-summary.md)) 주제에서 다룬다.

## 핵심 문장

- 페이지 로드는 브라우저 전처리 → DNS → TCP → TLS → HTTP → 렌더링 순서의 연쇄다. 대체로 앞 구간의 결과가 다음 구간의 입력이지만, TLS 1.3의 Finished+요청이나 HTML 점진 파싱처럼 겹치는 곳도 있다.
- 새 HTTPS 연결은 요청 전에 TCP 1 RTT와 TLS 1 RTT(1.3, 1.2는 2 RTT)를 치른다. 첫 바이트까지 3 RTT가 들고, 재사용 연결은 1 RTT다. 연결 재사용이 가장 큰 절약이다.
- 실패 모양이 구간을 알려 준다. 이름 에러는 DNS, 즉시 거절과 타임아웃은 TCP, 인증서·alert는 TLS, 상태 코드는 HTTP, "200인데 하얀 화면"은 렌더링이다.
- 리다이렉트와 하위 자원은 구간 0~4를 다시 돌린다. 새 출처 하나마다 DNS·TCP·TLS 비용이 새로 붙는다.
- `curl -w`의 누적 시간 차이로 구간별 시간을 재고, `--resolve`·`--connect-to`로 구간을 하나씩 건너뛰어 범인을 격리한다.

## 관련 주제·근거

이 노트는 종합편이다. 구간별 원리는 아래 노트가 맡는다.

- 선행
  - [26-packet-journey](../26-packet-journey/2-summary.md) — 한 연결 안의 패킷 여행(공간 축). 이 노트의 TCP 구간을 쪼개 볼 때
  - [28-dns-caching-and-ttl](../28-dns-caching-and-ttl/2-summary.md) — 구간 1의 캐시 계층·TTL
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) — 구간 3의 RTT·SNI·ALPN
  - [33-http-semantics](../33-http-semantics/2-summary.md) — 구간 4의 메서드·상태 코드
- 구간별 노트
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) — 재귀·반복 질의, NXDOMAIN·SERVFAIL
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md) — connect의 성공·거절·타임아웃
  - [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — 응답 끝과 TCP 끝의 구분
  - [30-x509-and-chain-validation](../30-x509-and-chain-validation/2-summary.md) · [31-revocation-ocsp-ct](../31-revocation-ocsp-ct/2-summary.md) — 인증서 검증
  - [34-http-caching](../34-http-caching/2-summary.md) · [35-http-connection-management](../35-http-connection-management/2-summary.md) · [36-http2-multiplexing](../36-http2-multiplexing/2-summary.md) · [37-http3-quic](../37-http3-quic/2-summary.md)
  - [39-http-content-encoding](../39-http-content-encoding/2-summary.md) · [40-chunked-and-streaming-responses](../40-chunked-and-streaming-responses/2-summary.md)
  - [47-cdn-and-edge](../47-cdn-and-edge/2-summary.md) · [48-firewalls-and-network-policy](../48-firewalls-and-network-policy/2-summary.md) · [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) · [10-fragmentation-mtu-pmtud](../10-fragmentation-mtu-pmtud/2-summary.md)
  - `46-load-balancers-and-proxies` — 원고: [systems/server-design/02-request-path](../../systems/server-design/02-request-path.md)
  - 렌더링 구간: [web-platform/02-rendering-pipeline](../../web-platform/02-rendering-pipeline/2-summary.md)·[web-platform/13-critical-path-and-resource-loading](../../web-platform/13-critical-path-and-resource-loading/2-summary.md)·[web-platform/07-service-workers-and-offline](../../web-platform/07-service-workers-and-offline/2-summary.md)
- 후속
  - [50-network-diagnostics](../50-network-diagnostics/2-summary.md) — 구간별 도구
  - [52-network-symptom-index](../52-network-symptom-index/2-summary.md) — 에러 코드 역색인
  - [53-network-incidents](../53-network-incidents/2-summary.md) — 실사건
- RFC·문서
  - RFC 6797 §8.3(스킴 교체 MUST)·§8.4(오류 시 연결 종료 MUST)·§12.1(사용자 우회 없음) — HSTS <https://www.rfc-editor.org/rfc/rfc6797>
  - RFC 8305 §3·§5 — Happy Eyeballs v2(AAAA 먼저, 연결 시도 간격 권장 250ms) <https://www.rfc-editor.org/rfc/rfc8305>
  - RFC 9460 — DNS SVCB/HTTPS 레코드 <https://www.rfc-editor.org/rfc/rfc9460>
  - RFC 9110 §15.6.3·§15.6.4·§15.6.5 — 502·503·504 (503은 서버 자신의 일시적 처리 불가) <https://www.rfc-editor.org/rfc/rfc9110>
  - 커널 문서 ip-sysctl — `tcp_syn_retries`(6.5+ 기본에서 약 131초)·`tcp_syn_linear_timeouts`(기본 4) <https://docs.kernel.org/networking/ip-sysctl.html>
  - iptables-extensions(8) REJECT — `--reject-with` 기본값 `icmp-port-unreachable`, `tcp-reset` <https://man7.org/linux/man-pages/man8/iptables-extensions.8.html>
  - curl(1) `--write-out`(`time_namelookup`·`time_connect`·`time_appconnect`·`time_starttransfer`는 시작부터의 누적), `--resolve`, `--connect-to` <https://curl.se/docs/manpage.html>
  - MDN "Critical rendering path" — CSS 렌더 차단, 스크립트 파서 차단 <https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Critical_rendering_path>
  - W3C Resource Timing — `domainLookupStart` 등 속성, `Timing-Allow-Origin` <https://www.w3.org/TR/resource-timing/>
  - Chrome DevTools Network reference — Timing 단계 설명 <https://developer.chrome.com/docs/devtools/network/reference#timing-explanation>
- alex/what-happens-when — 키 입력부터 URL 파싱·HSTS·DNS·ARP·소켓·TLS·HTTP·HTML 파싱·렌더링까지 <https://github.com/alex/what-happens-when>
- Grigorik, 『High Performance Browser Networking』 — "Primer on Web Performance" 장(자원 워터폴·RTT 비용)
