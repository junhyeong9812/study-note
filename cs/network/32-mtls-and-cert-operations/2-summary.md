# network/32-mtls-and-cert-operations — 상호 TLS와 인증서 운영: 클라이언트 인증서, ACME 자동 갱신, 인벤토리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

보통의 TLS는 **서버만** 인증서로 자기를 증명한다([29번](../29-tls-handshake/2-summary.md), [30번](../30-x509-and-chain-validation/2-summary.md)).\
클라이언트가 누구인지는 TLS 위에서 비밀번호·API 키·토큰으로 따로 증명한다.\
그런데 API 키와 bearer 토큰은 **복사하면 그대로 쓸 수 있는 문자열**이다. 로그·설정 파일로 새면 끝이다.

mTLS(상호 TLS)는 클라이언트도 인증서를 내고, 그 개인키로 핸드셰이크에 서명하게 한다.\
신원이 "갖고 있는 문자열"이 아니라 "**내보내지 않는 개인키를 쥐고 있음**"에 묶인다.

두 번째 문제는 운영이다.\
인증서는 반드시 만료된다. 그리고 수명은 짧아지는 중이다([31번](../31-revocation-ocsp-ct/2-summary.md): 2029년 공인 인증서 최대 47일).\
사람이 달력을 보고 갱신하는 방식으로는 언젠가 반드시 놓친다.

쉬운 예: 회사 출입증이다.\
경비원(서버)이 내 출입증을 보는 것처럼 나도 경비원의 제복·신분증을 본다. 이것이 상호 인증이다.\
출입증에는 유효기간이 있다. 수천 명의 출입증을 한 명이 손으로 갱신하면 누군가는 월요일 아침에 문 앞에서 막힌다.

똑같은 구조다.\
mTLS = 양쪽 인증서 검증. 인증서 운영 = 발급·배포·갱신·교체·감시의 자동화.

실무 예:
- 마이크로서비스 간 호출을 서비스 메시의 mTLS로 보호한다.
- 금융·결제 API가 제휴사에 클라이언트 인증서를 요구한다.
- "인증서 만료로 전면 장애"는 대형 서비스에서도 반복되는 사고 유형이다.

## 동작·원리

### 1. TLS 1.3의 클라이언트 인증 흐름

```text
  Client                                              Server
  ClientHello                        -------->
                                                      ServerHello
                                                      {EncryptedExtensions}
                                                      {CertificateRequest}   <- "너도 인증서 내라"
                                                      {Certificate}             signature_algorithms (필수)
                                                      {CertificateVerify}       certificate_authorities (선택)
                                     <--------        {Finished}
  {Certificate}          <- 클라이언트 인증서 체인 (없으면 빈 목록)
  {CertificateVerify}    <- 지금까지의 transcript 에 클라이언트 개인키로 서명
  {Finished}                         -------->
                                                      서버: 체인 검증 + 신원 추출 + 인가
                                     <--------        실패 시 alert (예: certificate_required 116)
```

- 서버가 요청할 때만 클라이언트가 인증서를 보낸다. 요청은 EncryptedExtensions 바로 뒤에 온다(RFC 8446 §4.3.2).
  - `signature_algorithms` 확장은 반드시 들어 있다(MUST).
  - `certificate_authorities` 확장으로 "이 CA들이 발급한 것을 달라"고 힌트를 줄 수 있다.
- 알맞은 인증서가 없으면 클라이언트는 **빈 Certificate 메시지**를 보내고 Finished도 보낸다(MUST, §4.4.2).
- 서버의 선택(§4.4.2.4)
  - 빈 인증서면: 인증 없이 계속하거나, `certificate_required`(116) alert로 끊는다. 서버 재량(MAY)이다.
  - 체인이 받아들일 수 없으면(모르는 CA 등): 비인증 상태로 계속하거나 끊는다.
- 클라이언트 인증서도 30번과 같은 체인 검증을 받는다. 다만 비교 대상이 호스트명이 아니라 **허용된 클라이언트 신원**이다.
- 주의: TLS 1.3에서는 클라이언트가 Finished를 보낸 시점에 이미 핸드셰이크가 끝났다고 볼 수 있다.
  - 서버의 거절 alert는 그 뒤에 도착한다.
  - 그래서 클라이언트 쪽 에러가 "연결" 단계가 아니라 **첫 읽기·쓰기**에서 드러나는 구현이 있다 [?].

  - *transcript*: 지금까지 주고받은 핸드셰이크 메시지 전체다. 여기에 서명하므로 다른 연결의 서명을 재사용할 수 없다.

### 2. 신원은 어디서 꺼내나 — 인증 뒤의 인가

```text
  클라이언트 인증서
    subject       CN=billing (옛 방식)
    SAN           URI:spiffe://prod.example/ns/billing/sa/api   <- SPIFFE ID
                  DNS:billing.internal
    extKeyUsage   clientAuth

  서버:  체인 OK  ->  신원 = SAN URI  ->  정책: billing 은 /payments 호출 가능?  ->  허용/거부
```

- mTLS는 **인증**(누구인가)만 한다. **인가**(무엇을 해도 되나)는 신원을 꺼내 정책과 대조하는 별도 단계다.
- 흔한 신원 표현
  - SPIFFE X.509-SVID: SAN에 URI 하나(`spiffe://...`)만 둔다. 둘 이상이면 거부해야 한다(SPIFFE 명세).
  - 리프는 `cA=false`, `digitalSignature`를 갖는다. EKU 확장은 넣는 것이 권고(SHOULD)이고, 넣으면 `serverAuth`·`clientAuth`를 둘 다 둔다(MUST).
- 사내 CA 하나가 발급한 인증서를 "그 CA면 누구든 통과"로 받으면, 그 CA로 발급받은 **모든** 워크로드가 서로 호출할 수 있다. 신원 단위의 인가가 필요하다.

### 3. TLS를 어디서 끝내나 — 종단 지점과 신원 전달

```text
  (a) 앱이 직접 종단          클라이언트 ===mTLS===> [앱]            앱이 인증서를 직접 본다
  (b) LB/프록시에서 종단      클라이언트 ===mTLS===> [LB] ---> [앱]   LB가 신원을 헤더로 넘긴다
                                                             예: Envoy x-forwarded-client-cert
  (c) 사이드카(서비스 메시)    [앱]->[사이드카] ===mTLS===> [사이드카]->[앱]
```

- (b)의 위험: 앱이 신원 헤더를 믿으면, LB를 거치지 않고 앱에 직접 닿는 요청이 **헤더를 위조**할 수 있다.
  - LB는 들어온 같은 이름 헤더를 지우고 다시 써야 한다.
  - 앱은 LB에서 온 연결만 받아야 한다.
- nginx에서 mTLS를 종단하면 인증서 없는 요청을 TLS alert가 아니라 **HTTP 400**으로 거절한다.
  - 내부 코드 496 "a client has not presented the required certificate", 495 "client certificate verification error"(nginx 문서).
  - 그래서 "alert 116"은 라이브러리·서버 구현에 따라 보이지 않을 수 있다.

### 4. 공인 CA는 클라이언트 인증서에서 빠지는 중

```text
  Chrome 루트 프로그램: 2026-06 까지 TLS 서버 인증 PKI 와 클라이언트 인증 PKI 분리 요구
  Let's Encrypt:
    2026-02-11  기본 classic 프로필에서 clientAuth EKU 제거
    2026-07-08  tlsclient 프로필 종료 -> clientAuth 인증서 발급 중단
```

- 결과: 공인 서버 인증서를 mTLS 클라이언트 인증서로 **재사용하던 구성은 갱신 시점에 깨진다.**
- Let's Encrypt 권고: 클라이언트 인증은 **사설 CA**가 더 맞는 경우가 많다.

### 5. ACME — 인증서 발급·갱신의 자동화 (RFC 8555)

```text
  ACME 클라이언트 (certbot, cert-manager ...)            ACME 서버 (CA)
   1. newAccount (계정 키로 JWS 서명)            ----->
   2. newOrder  identifiers=[api.example.com]    ----->  authorizations + finalize URL
   3. 도전 과제 하나를 골라 준비                          (도메인 제어 증명)
        http-01   : http://api.example.com/.well-known/acme-challenge/<token>   (TCP 80)
        dns-01    : _acme-challenge.api.example.com  TXT "<digest>"
        tls-alpn-01: 443 에서 ALPN "acme-tls/1" 로 특수 인증서 제시 (RFC 8737)
   4. challenge 응답 "준비됐다"                   ----->  CA 가 직접 확인
   5. finalize (CSR 제출)                         ----->
   6. certificate URL 에서 체인 다운로드          <-----
```

- http-01은 **TCP 80**으로 확인한다(MUST, RFC 8555 §8.3). 80 포트가 막혀 있으면 실패한다.
- 와일드카드(`*.example.com`)는 Let's Encrypt에서 **dns-01만** 된다(LE "Challenge Types" 문서, 2026-02-12 갱신판 기준).
  - dns-01은 서버에 DNS API 자격 증명을 둬야 한다. 권한을 좁게 두거나 검증을 별도 서버에서 하라고 LE는 권한다.
- 갱신 시점
  - cert-manager 기본: 수명의 **2/3 지점**에서 갱신한다(기본 수명 90일). `renewBefore`·`renewBeforePercentage`로 바꾼다.
  - **ARI**(ACME Renewal Information, RFC 9773): CA가 "이 인증서는 이 시간대에 갱신하라"는 창을 알려 준다. CA가 대량 폐기를 해야 할 때 갱신을 앞당기게 할 수도 있다. Let's Encrypt는 수명 단축에 맞춰 ARI 사용을 권한다.

  - *CSR(Certificate Signing Request)*: "이 공개키와 이 이름으로 인증서를 달라"는 요청서다. 개인키로 서명해 키 보유를 증명한다. 개인키는 CA로 가지 않는다.

### 6. 인증서 인벤토리 — "우리가 가진 인증서"의 목록

```text
  인벤토리 한 줄 (예시)
  | 이름/SAN          | 배포 위치               | 발급자      | notAfter   | 갱신 방식     | 담당    |
  | api.example.com   | LB-prod, nginx-edge x4  | LE R11      | 2026-11-20 | cert-manager  | 플랫폼  |
  | partner-mtls      | billing-svc 클라이언트  | 사내 CA     | 2027-01-05 | 수동 (!)      | 결제팀  |

  수집 경로
    - CT 로그 검색: 공인 인증서는 도메인으로 전부 찾을 수 있다 (31번)
    - 엔드포인트 스캔: 사내 IP:443 에 접속해 제시되는 인증서 수집
    - 저장소 스캔: k8s Secret(type=kubernetes.io/tls), 키스토어 파일, 클라우드 인증서 관리 서비스
```

- 목적은 두 가지다.
  - "만료 전에 누가 무엇을 갱신해야 하나"를 안다.
  - 사고 때 "이 CA·이 키가 들어간 곳이 어디인가"를 즉시 안다.
- 감시 대상은 **제시되는 인증서**다. 파일은 갱신됐는데 프로세스가 옛 인증서를 계속 쓰는 경우가 있다(장애 §2).

## 쓰이는 자료구조·알고리즘

- **만료 타이머 = 우선순위 큐** — (notAfter − 갱신 여유) 시각이 가장 이른 인증서부터 꺼내 처리한다. 인벤토리 전체를 매번 훑지 않고 다음 마감만 본다. [힙](../../data-structure/07-heap/2-summary.md) 참고.
- **갱신 창 계산** — 수명 × 2/3 지점(cert-manager 기본) 또는 ARI가 준 창 안에서 **무작위 시각**을 고른다. 모든 클라이언트가 같은 순간에 몰리지 않게 한다(RFC 9773이 서버 부하 분산을 목적으로 든다).
- **재시도 + 지수 백오프** — ACME 검증 실패·속도 제한에 대응한다. 만료까지 남은 시간이 줄수록 경보 수준을 올린다.
- **신원 → 권한 맵** — mTLS 인가는 SAN URI(신원)를 키로 허용 경로·메서드 목록을 찾는 조회다(해시 맵).
- **체인 검증 = 그래프 경로 탐색** — 클라이언트 인증서 체인도 30번과 같은 알고리즘을 쓴다.

## 적용 — 풀어나가는 법

### 1. 서버 설정 — nginx mTLS

```nginx
server {
    listen 443 ssl;
    ssl_certificate         /etc/nginx/tls/server-fullchain.pem;
    ssl_certificate_key     /etc/nginx/tls/server.key;

    ssl_client_certificate  /etc/nginx/tls/client-ca.pem;  # 클라이언트 인증서 발급 CA (목록이 클라이언트에 전송됨)
    ssl_verify_client       on;                            # 기본 off. optional 이면 없을 때도 통과
    ssl_verify_depth        2;                             # 기본 1 = 중간 CA 1단계까지 허용. 2단계 이상이면 늘린다

    location / {
        proxy_set_header X-Client-Verify $ssl_client_verify;   # SUCCESS / FAILED:... / NONE
        proxy_set_header X-Client-DN     $ssl_client_s_dn;
        proxy_pass http://app;
    }
}
```

- `ssl_verify_depth` 기본값은 **1**이다(nginx 문서). nginx는 이 값을 OpenSSL `SSL_CTX_set_verify_depth()`에 그대로 넘긴다.
  - OpenSSL(1.1.0 이후)에서 depth는 리프와 신뢰 앵커(루트) **사이**의 인증서 수 한도다. 리프와 루트는 세지 않는다(`SSL_CTX_set_verify(3)`).

```text
  depth 1:  리프 -> 중간 -> 루트              통과 (중간 1개)
            리프 -> 중간2 -> 중간1 -> 루트    실패 (중간 2개) -> depth 2 이상 필요
```
- 앱으로 넘기는 헤더는 nginx가 **덮어쓰므로** 클라이언트가 보낸 같은 이름 헤더는 무시된다. 단 앱은 nginx에서 온 요청만 받아야 한다.

### 2. 클라이언트 코드

Java — 키스토어(내 인증서 + 개인키)와 트러스트스토어(서버 CA)를 둘 다 준다.

```java
KeyStore ks = KeyStore.getInstance("PKCS12");
try (InputStream in = Files.newInputStream(Path.of("/etc/app/client.p12"))) { ks.load(in, pw); }
KeyManagerFactory kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
kmf.init(ks, pw);

SSLContext ctx = SSLContext.getInstance("TLS");
ctx.init(kmf.getKeyManagers(), trustManagers, null);   // trustManagers: 서버 검증용 (30번)

HttpClient client = HttpClient.newBuilder().sslContext(ctx).build();
```

Java 서버 쪽 요구: `sslEngine.setNeedClientAuth(true)`(필수) 또는 `setWantClientAuth(true)`(선택).

Node — 클라이언트는 `cert`·`key`, 서버는 `requestCert`·`rejectUnauthorized`.

```js
// 클라이언트
const https = require('node:https');
const fs = require('node:fs');
https.request({
  host: 'api.partner.example', port: 443, path: '/v1/pay', method: 'POST',
  cert: fs.readFileSync('client.crt'), key: fs.readFileSync('client.key'),
}, (res) => console.log(res.statusCode)).end();

// 서버
https.createServer({
  cert: fs.readFileSync('server.crt'), key: fs.readFileSync('server.key'),
  ca: [fs.readFileSync('client-ca.pem')],   // 클라이언트 인증서 발급 CA
  requestCert: true, rejectUnauthorized: true,
}, (req, res) => {
  const peer = req.socket.getPeerCertificate();
  res.end(`hello ${peer.subjectaltname}`);  // 신원을 꺼내 인가에 쓴다
}).listen(8443);
```

### 3. 진단 명령

```bash
# 서버가 클라이언트 인증서를 요구하나 — "Acceptable client certificate CA names" 가 보이면 요구 중
openssl s_client -connect api.partner.example:443 -servername api.partner.example </dev/null

# 클라이언트 인증서를 내며 접속
openssl s_client -connect api.partner.example:443 -servername api.partner.example \
  -cert client.crt -key client.key </dev/null
curl -v --cert client.crt --key client.key https://api.partner.example/v1/health

# 인증서 용도 확인 (clientAuth 가 있나)
openssl x509 -in client.crt -noout -ext extendedKeyUsage,subjectAltName -dates

# 지금 "제시되는" 인증서의 만료 (파일이 아니라 실제 서빙 중인 것)
echo | openssl s_client -connect api.example.com:443 -servername api.example.com 2>/dev/null \
  | openssl x509 -noout -enddate
```

### 4. 운영 순서

1. 인벤토리를 만든다: CT 검색 + 엔드포인트 스캔 + 저장소 스캔.
2. 공인 서버 인증서는 ACME 자동화로 옮긴다. 갱신 뒤 **프로세스 재적재**까지 자동화한다.
3. 클라이언트 인증서(mTLS)는 사설 CA로 발급한다. 짧은 수명 + 자동 교체로 간다(서비스 메시, SPIFFE 구현 등).
4. 만료 감시는 **제시되는 인증서** 기준으로 한다. 남은 일수 임계값(예시: 수명의 1/3, 7일, 3일)으로 단계 경보를 둔다.
5. 갱신 실패를 조용히 넘기지 않는다. ACME 실패 로그·재시도 소진을 경보로 올린다.

## 장애 시나리오와 대처

### 1. 갱신 누락 → 만료 전면 장애

- **현상**: 특정 시각에 모든 클라이언트가 동시에 TLS 실패다. 트래픽이 절벽처럼 떨어진다.
- **보이는 형태**
  - 브라우저 `NET::ERR_CERT_DATE_INVALID`(Chromium `net_error_list.h`의 `CERT_DATE_INVALID`).
  - OpenSSL `certificate has expired`, Java `CertificateExpiredException`, Node `CERT_HAS_EXPIRED`.
  - `openssl x509 -enddate`가 과거 시각이다.
- **원인**
  - 수동 갱신 인증서가 인벤토리에 없었다.
  - 또는 자동 갱신이 **조용히** 실패하고 있었다. 흔한 원인은 이렇다.
    - 80 포트 차단(http-01).
    - DNS API 자격 증명 만료(dns-01).
    - CA 속도 제한.
    - 도메인 DNS 이관 후 검증 경로 변경.
- **대처**
  - 즉시: 수동 발급·배포로 복구한다.
  - 재발 방지: 인벤토리, 제시 인증서 기준 만료 감시, ACME 실패 경보, ARI 사용.
  - 수명 단축(31번) 뒤로는 갱신 실패가 드러날 여유가 짧아진다.

### 2. 파일은 갱신됐는데 프로세스는 옛 인증서를 서빙

- **현상**: 갱신 로그는 성공인데 만료일에 장애가 난다.
- **보이는 형태**
  - 디스크의 `fullchain.pem`은 새 notAfter다.
  - `openssl s_client`로 본 **제시 인증서**는 옛 notAfter다.
- **원인**
  - nginx·Java 등은 시작·재적재 때 인증서를 메모리에 읽는다. 갱신 뒤 reload를 하지 않았다.
  - 또는 LB·CDN에 올린 사본이 따로 있다.
- **대처**
  - 갱신 훅에서 reload한다(`nginx -s reload`, 앱의 키스토어 재적재).
  - 감시는 파일이 아니라 네트워크로 제시되는 인증서로 한다.

### 3. 클라이언트 인증서 미제시 → `certificate_required`

- **현상**: 새 배포 뒤 제휴사 API 호출이 전부 실패한다.
- **보이는 형태**
  - TLS 1.3 서버가 `certificate_required`(alert 116)로 끊는다(RFC 8446 §4.4.2.4 — 서버 재량).
  - 클라이언트 에러가 연결 직후가 아니라 첫 읽기·쓰기에서 나올 수 있다 [?].
  - nginx 종단이면 TLS는 성공하고 HTTP **400**이 온다. 기본 오류 페이지 제목이 "400 No required SSL certificate was sent"다(nginx 소스 `ngx_http_special_response.c`의 496 페이지).
- **원인**
  - 클라이언트 설정에서 키스토어가 빠졌다.
  - 또는 서버가 `certificate_authorities`로 요구한 CA와 클라이언트 인증서 발급자가 달라 라이브러리가 보낼 인증서를 못 골랐다(빈 Certificate 전송).
- **대처**
  - `openssl s_client -cert -key`로 직접 재현한다.
  - 서버가 받아들이는 CA 목록("Acceptable client certificate CA names")과 클라이언트 인증서의 issuer를 맞춘다.

### 4. 중간 CA로 발급한 클라이언트 인증서가 nginx에서 거부

- **현상**: 사설 CA 구조를 루트 → 중간으로 바꾼 뒤 새 클라이언트 인증서만 거부된다.
- **보이는 형태**
  - HTTP 400(nginx 495, 인증서 검증 오류).
  - `$ssl_client_verify`가 `FAILED:...`.
  - nginx 에러 로그에 검증 실패 사유가 남는다.
- **원인**
  - 중간 CA를 클라이언트가 보내지 않았고 서버 신뢰 파일에도 없다. 중간 1단계 구조라면 가장 먼저 의심한다.
  - 중간 CA가 **2단계 이상**인데 `ssl_verify_depth`가 기본값 1이다. 중간 1개(리프 → 중간 → 루트)는 기본값 1로도 통과한다.
- **대처**
  - 클라이언트가 체인(리프 + 중간)을 보내게 하거나, 서버 신뢰 파일에 중간을 넣는다.
  - 중간이 2단계 이상이면 `ssl_verify_depth`를 중간 CA 수 이상으로 올린다.

### 5. 공인 인증서를 클라이언트 인증서로 재사용 → 갱신 후 거부

- **현상**: 공인 CA에서 갱신받은 인증서를 mTLS 클라이언트 인증서로 쓰던 연동이 갱신 직후 실패한다.
- **보이는 형태**
  - 상대 서버가 `unsupported_certificate`(43)·`bad_certificate`(42) 등으로 거절한다.
  - OpenSSL 검증 문구 `unsuitable certificate purpose`.
  - `openssl x509 -ext extendedKeyUsage`에 `TLS Web Client Authentication`이 없다.
- **원인**
  - Chrome 루트 프로그램 요구로 공인 CA들이 서버 인증서에서 `clientAuth` EKU를 뺐다.
  - Let's Encrypt는 2026-02-11 기본 프로필에서 제거했고, 2026-07-08 이후로는 clientAuth 인증서를 발급하지 않는다.
- **대처**
  - 클라이언트 인증용 사설 CA(또는 클라이언트 인증 전용 PKI)로 옮긴다.
  - 상대 측과 신뢰 CA를 다시 합의한다.

## 핵심 문장

- mTLS는 클라이언트도 인증서를 내고 CertificateVerify로 개인키 보유를 증명하게 해, 신원을 복사 가능한 문자열이 아니라 개인키에 묶는다.
- 서버는 CertificateRequest로 요구하고, 클라이언트는 알맞은 인증서가 없으면 빈 Certificate를 보낸다. 거절 여부와 `certificate_required`(116) 사용은 서버 재량이다.
- mTLS는 인증일 뿐이다. SAN URI 같은 신원을 꺼내 정책과 대조하는 인가를 따로 해야 한다.
- 인증서 운영의 핵심은 인벤토리, ACME 자동 갱신, 프로세스 재적재, **제시되는 인증서** 기준 만료 감시다. 수명이 47일로 줄어드는 흐름에서 수동 갱신은 사고를 부른다.
- 공인 CA는 clientAuth EKU를 빼는 중이므로, mTLS 클라이언트 인증서는 사설 CA로 발급한다.

## 관련 주제·근거

- 선행
  - [30-x509-and-chain-validation](../30-x509-and-chain-validation/2-summary.md) — 체인·EKU·SAN 검증
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) — 핸드셰이크 흐름, CertificateVerify
- 연결
  - [31-revocation-ocsp-ct](../31-revocation-ocsp-ct/2-summary.md) — 수명 단축(SC-081), CT로 인벤토리 수집
  - [28-dns-caching-and-ttl](../28-dns-caching-and-ttl/2-summary.md) — dns-01 TXT 전파
  - `security/09-randomness-and-key-management` — 키 수명·회전. 미작성([security 영역 표](../../security/README.md))
  - [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) — 만료 타이머
- RFC 8446 (TLS 1.3) <https://www.rfc-editor.org/rfc/rfc8446>
  - §4.3.2 CertificateRequest · §4.4.2 Certificate(빈 목록 규칙) · §4.4.2.3 클라이언트 인증서 선택 · §4.4.2.4 수신 처리(`certificate_required`)
  - §4.6.2 핸드셰이크 뒤 인증 · §6.2 alert 목록(`certificate_required` 116)
- RFC 8740 HTTP/2에서 TLS 1.3 핸드셰이크 뒤 인증 금지 <https://www.rfc-editor.org/rfc/rfc8740>
- RFC 8555 ACME — §7.3 계정 · §7.4 주문·finalize · §7.4.2 다운로드 · §7.5 인가 · §8.3 http-01 · §8.4 dns-01 <https://www.rfc-editor.org/rfc/rfc8555>
- RFC 8737 tls-alpn-01 <https://www.rfc-editor.org/rfc/rfc8737> · RFC 9773 ARI <https://www.rfc-editor.org/rfc/rfc9773>
- Let's Encrypt "Challenge Types" <https://letsencrypt.org/docs/challenge-types/>
- Let's Encrypt "Ending TLS Client Authentication Certificate Support in 2026"(2025-05-14, 2026-03-16 갱신) <https://letsencrypt.org/2025/05/14/ending-tls-client-authentication>
- cert-manager "Certificate resource"(기본 수명 90일, 2/3 지점 갱신) <https://cert-manager.io/docs/usage/certificate/>
- SPIFFE X.509-SVID 명세 <https://github.com/spiffe/spiffe/blob/main/standards/X509-SVID.md>
- OpenSSL `SSL_CTX_set_verify(3)`(depth = 리프·신뢰 앵커 사이 인증서 수 한도) <https://docs.openssl.org/3.0/man3/SSL_CTX_set_verify/> · `crypto/x509/x509_vfy.c` `build_chain()`(`max_depth = depth + 1`) · nginx `src/event/ngx_event_openssl.c`(`SSL_CTX_set_verify_depth(ssl->ctx, depth)`)
- nginx `ssl_verify_client`·`ssl_verify_depth`(기본 1)·`ssl_client_certificate`·495/496 <https://nginx.org/en/docs/http/ngx_http_ssl_module.html> · 소스 `src/http/ngx_http_special_response.c`(495/496 오류 페이지 문구)
- Chromium `net/base/net_error_list.h`(`CERT_DATE_INVALID`)
- Oracle JSSE Reference Guide(`setNeedClientAuth`, 키스토어·트러스트스토어) <https://docs.oracle.com/en/java/javase/21/security/java-secure-socket-extension-jsse-reference-guide.html>
- Node.js `tls`(`requestCert`, `getPeerCertificate`) <https://nodejs.org/api/tls.html>
