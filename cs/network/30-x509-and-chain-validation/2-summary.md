# network/30-x509-and-chain-validation — X.509 인증서와 체인 검증: 구조·리프→중간→루트·루트 스토어·호스트명 검증 — 정리 (힌트)

## 해결하는 문제

TLS 핸드셰이크의 CertificateVerify는 "상대가 이 공개키의 개인키를 갖고 있다"를 증명한다([29번](../29-tls-handshake/2-summary.md)).\
하지만 그 공개키가 **정말 api.example.com의 것인지**는 따로 믿을 근거가 필요하다.\
공격자도 자기 키쌍을 만들어 "내가 api.example.com이다"라고 말할 수 있기 때문이다.

인증서는 "이 이름 ↔ 이 공개키" 묶음에 **믿을 만한 제3자(CA)가 서명**한 문서다.\
클라이언트는 그 서명을 따라 올라가 **자기가 원래 믿는 루트**에 닿는지 확인한다.

쉬운 예: 처음 보는 사람이 사원증을 보여 준다.\
사원증에는 회사 직인이 찍혀 있다. 회사는 내가 아는 곳이다.\
그러면 그 사람을 그 회사 직원으로 믿는다.\
직인이 모르는 회사 것이거나, 사원증 유효기간이 지났거나, 사원증 이름이 다른 사람이면 믿지 않는다.

똑같은 구조다.\
체인 검증 = 서명 확인 + 유효기간 확인 + CA 자격 확인 + 이름 확인을 루트까지 반복하는 것.

실무 예:
- 브라우저에서는 멀쩡한 사이트가 서버 간 호출(Java·curl)에서만 `PKIX path building failed`로 실패한다.
- 사내 CA로 발급한 인증서를 쓰는 내부 API를 부르려면 트러스트스토어에 사내 루트를 넣어야 한다.

## 동작·원리

### 1. 인증서 한 장의 구조

```text
  Certificate  (RFC 5280 §4.1, DER 인코딩 — PEM은 이것을 Base64로 감싼 것)
  +--------------------------------------------------------------+
  | tbsCertificate  ("서명될 부분")                                |
  |   version            v3                                       |
  |   serialNumber       CA 안에서 유일한 번호                      |
  |   signature          서명 알고리즘 (예: ecdsa-with-SHA256)      |
  |   issuer             발급자 이름  (CN=R11, O=Let's Encrypt ...) |
  |   validity           notBefore ~ notAfter                     |
  |   subject            주체 이름                                 |
  |   subjectPublicKeyInfo  공개키                                  |
  |   extensions                                                  |
  |     subjectAltName     DNS:api.example.com, DNS:*.example.com |
  |     basicConstraints   cA=FALSE  (CA면 TRUE, pathLen)          |
  |     keyUsage           digitalSignature (CA면 keyCertSign)     |
  |     extKeyUsage        serverAuth / clientAuth                |
  |     authorityKeyId     발급자 키 식별자 (체인 연결 힌트)          |
  |     subjectKeyId       내 키 식별자                             |
  |     authorityInfoAccess  caIssuers URL (발급자 인증서 받는 곳)   |
  |     crlDistributionPoints / SCT ...  (31번)                    |
  +--------------------------------------------------------------+
  | signatureAlgorithm                                            |
  | signatureValue   = 발급자 개인키로 tbsCertificate 에 서명한 값    |
  +--------------------------------------------------------------+
```

- 서명은 **tbsCertificate 전체**에 걸린다. 이름·유효기간·확장 중 한 비트만 바꿔도 서명 검증이 실패한다.
- *DER*: ASN.1 구조를 바이트로 쓰는 규칙이다. 태그-길이-값(TLV)의 중첩이다.
- *PEM*: DER을 Base64로 바꾸고 `-----BEGIN CERTIFICATE-----` 줄로 감싼 텍스트 형식이다.
- 유효기간은 notBefore부터 notAfter까지 **양 끝 포함**이다(§4.1.2.5).
- 확장에는 critical 표시가 있다. 이해하지 못하는 **critical 확장**이 있으면 인증서를 거부해야 한다(MUST, §4.2).

### 2. 체인 — 리프 → 중간 → 루트

```text
                     루트 스토어 (클라이언트가 원래 믿는 목록)
                     +-------------------------------+
                     | ISRG Root X1 (자체 서명)        |  <- 신뢰 앵커
                     | ...                           |
                     +---------------+---------------+
                                     | 서명
  서버가 보내는 것                     v
  +-------------------------------------------------+
  | [0] 리프:  subject=api.example.com                 |  issuer = R11
  | [1] 중간:  subject=R11                             |  issuer = ISRG Root X1
  +-------------------------------------------------+
         루트는 보내지 않아도 된다 (클라이언트가 이미 갖고 있다)
```

- TLS 1.3의 Certificate 메시지 규칙(RFC 8446 §4.4.2)
  - 자기 인증서(리프)가 첫 번째여야 한다(MUST).
  - 다음 인증서는 바로 앞 인증서를 서명한 것이기를 권한다(SHOULD).
  - 신뢰 앵커(루트)는 생략해도 된다(MAY).
- **중간 인증서는 서버가 보내야 한다.** 클라이언트 루트 스토어에는 보통 루트만 있다.
  - nginx `ssl_certificate` 파일에는 리프를 먼저, 중간 인증서를 그 뒤에 이어 붙인다(nginx 문서).
- 루트가 아닌 중간 CA를 두는 이유: 루트 개인키를 오프라인에 보관하고, 일상 발급은 중간 CA가 한다. 중간 CA가 사고를 내면 그 중간만 폐기한다.

  - *신뢰 앵커(trust anchor)*: 검증의 출발점으로 무조건 믿는 공개키다. 보통 자체 서명 루트 인증서 형태로 루트 스토어에 들어 있다.
  - *자체 서명(self-signed)*: issuer와 subject가 같고 자기 개인키로 서명한 인증서다.

### 3. 경로 검증 — RFC 5280 §6.1

RFC 5280은 번호를 루트 쪽부터 매긴다. 인증서 1은 신뢰 앵커가 발급한 것, 인증서 n이 검증 대상(리프)이다.

```text
  신뢰 앵커의 공개키로 시작
     |
     v
  인증서 i (i = 1..n) 마다                              (§6.1.3)
    [a1] 서명이 "현재 작업 공개키"로 검증되나
    [a2] 지금 시각이 유효기간 안인가
    [a3] 폐기되지 않았나                    (31번)
    [a4] issuer 이름 == 직전 인증서의 subject
     |
     v  i < n (아직 CA 단계)이면                         (§6.1.4)
    [k] basicConstraints 가 있고 cA = TRUE
    [l][m] 경로 길이 제한(pathLenConstraint) 안인가
    [n] keyUsage 가 있으면 keyCertSign 비트
    -> 이 인증서의 공개키가 다음 "작업 공개키"가 된다
     |
     v
  i = n (리프)에서 끝 -> 경로 유효
```

- 한 인증서가 경로에 두 번 나오면 안 된다(MUST NOT).
- 체인 검증이 끝나도 **이름 확인은 따로**다. RFC 5280은 이름과 키의 묶음이 유효한지만 본다. "내가 접속하려던 이름이 맞나"는 호스트명 검증(§5)이 한다.
- `basicConstraints cA=FALSE`인 리프 인증서로 다른 인증서에 서명해도, [k] 단계에서 막힌다. 과거 일부 구현이 이 검사를 빠뜨려 CA가 아닌 인증서로도 아무 도메인 인증서를 서명할 수 있었던 사례가 있다(iOS 4.3.5 이전, CVE-2011-0228).

### 4. 경로 **구축**은 규격 밖 — 그래프 탐색

RFC 5280 §6.1은 "주어진 경로를 검증하는 법"만 정한다. 인증서 목록을 **어떻게 모아 경로로 엮을지**는 규격 밖이라고 적는다.

```text
  교차 서명(cross-sign)이 있으면 경로가 여러 개다

        [ISRG Root X1]         [DST Root CA X3]  (2021-09-30 만료)
              |                       |
              |  서명                  |  서명 (교차 서명)
              v                       v
         [ISRG Root X1 자체]     [ISRG Root X1 교차본]
                    \              /
                     \            /
                      [중간 R3]
                          |
                      [리프]

  좋은 구현: 만료된 경로를 버리고 다른 경로를 탐색 (백트래킹)
  OpenSSL 1.0.x: 만료된 DST 경로를 고르고 실패 (Let's Encrypt 문서)
```

- 후보 발급자 찾기: 이름(issuer DN) 일치, authorityKeyId ↔ subjectKeyId 일치로 후보를 좁힌다.
- 후보가 여럿이면 하나를 골라 올라가 보고, 실패하면 되돌아와 다른 후보를 시도해야 한다.
- 중간 인증서가 빠졌을 때 구현마다 대응이 다르다.
  - Chrome: AIA `caIssuers` URL에서 빠진 중간 인증서를 받아 온다(AIA fetching, Chromium 논의).
  - Firefox: 그때그때 CA에서 받아 오는 대신, 신뢰된 중간 CA 인증서를 미리 내려받아 둔다(Mozilla 블로그 2020, Mozilla wiki "Intermediate Preloading").
  - Java: AIA 사용이 기본 꺼짐이다. `com.sun.security.enableAIAcaIssuers=true`로 켠다(Java PKI 가이드).
  - OpenSSL·Node·curl: 보통 AIA를 따라가지 않는다 [?].
- 그래서 **"브라우저는 되는데 서버 간 호출만 실패"**가 생긴다.

### 5. 호스트명 검증 — 체인과 별개의 두 번째 관문

```text
  접속하려던 이름:  api.example.com   (참조 식별자)
  인증서 SAN:      DNS:*.example.com, DNS:example.com   (제시 식별자)

  비교 규칙 (RFC 9525 §6.3)
    레이블 단위, 대소문자 무시
    와일드카드는 맨 왼쪽 레이블 전체일 때만, 레이블 하나에만 매치

    api.example.com      vs *.example.com   -> 매치
    a.b.example.com      vs *.example.com   -> 불일치 (두 레이블)
    example.com          vs *.example.com   -> 불일치 (레이블 없음)
```

- 서버 이름은 **subjectAltName(SAN)**에서 찾는다. subject의 CN(Common Name)을 이름으로 쓰는 방식은 RFC 9525가 없앴다(RFC 6125를 대체, 부록 A).
  - 단 구현에 따라 **DNS 타입 SAN이 하나도 없을 때만** CN으로 폴백한다. OpenSSL `X509_check_host()` 기본값, JDK `HostnameChecker`, Node `tls.checkServerIdentity`가 그렇다. DNS SAN이 하나라도 있으면 CN은 무시된다.
- IP로 접속하면 SAN의 IP 주소 항목과 비교한다(§6.4).
- 라이브러리 기본값을 확인해야 한다.
  - Java: raw `SSLSocket`·`SSLEngine`은 호스트명을 **자동으로 검사하지 않는다.** `HttpsURLConnection`은 호스트명을 검사하며, JDK 7부터는 핸드셰이크 중 HTTPS 엔드포인트 식별을 기본으로 한다. raw 소켓에는 `setEndpointIdentificationAlgorithm("HTTPS")`를 켠다(JSSE 가이드).
  - Node: `tls.connect`는 기본으로 `tls.checkServerIdentity`를 부른다. `rejectUnauthorized: false`는 체인 검증 실패와 호스트명 불일치를 모두 무시하게 만든다(`authorizationError`에만 남는다 — `lib/internal/tls/wrap.js` `onConnectSecure`).

### 6. 루트 스토어 — 누구를 처음부터 믿나

```text
  클라이언트                       기본 루트 스토어
  브라우저/OS                      OS·브라우저 루트 프로그램
  Java                            $JAVA_HOME/lib/security/cacerts  (jssecacerts 가 있으면 그것)
  Node                            번들된 Mozilla CA 목록 (+ NODE_EXTRA_CA_CERTS, --use-system-ca)
  curl/OpenSSL                    OS의 CA 번들 (예: /etc/ssl/certs)
```

- 같은 서버라도 **클라이언트마다 루트 스토어가 달라** 결과가 다를 수 있다.
- Java: `javax.net.ssl.trustStore`를 지정하면 그 파일**만** 쓴다. 기본 `cacerts`와 합쳐지지 않는다(JSSE 가이드).
- Node: `ca` 옵션을 주면 기본 목록이 **완전히 대체**된다. 추가하려면 직접 합쳐야 한다(Node `tls` 문서). `NODE_EXTRA_CA_CERTS`는 기본 목록에 **더한다**. 단 `ca`를 명시하면 둘 다 쓰이지 않는다.

## 쓰이는 자료구조·알고리즘

- **체인 = 그래프 경로 탐색**
  - 정점은 인증서, 간선은 "A가 B에 서명했다"이다.
  - 리프에서 신뢰 앵커 집합의 어느 정점까지 가는 경로를 찾는다.
  - 교차 서명이 있으면 경로가 여럿이다. 만료·제약 위반 경로를 만나면 되돌아가 다른 후보를 본다(백트래킹 DFS).
  - [그래프](../../data-structure/08-graph/2-summary.md) · [DFS](../../algorithm/12-dfs/2-summary.md) 참고.
- **발급자 색인** — subject DN 또는 subjectKeyId → 인증서 목록의 해시 맵. 후보 발급자를 O(1)에 찾는다. [해시 맵](../../data-structure/05-hashmap/2-summary.md).
- **신뢰 앵커 집합** — 루트 스토어는 "이 키면 멈춰도 된다"를 판정하는 집합이다.
- **경로 검증 = 상태를 들고 가는 선형 순회** — 작업 공개키, 작업 발급자 이름, 남은 경로 길이(max_path_length)를 상태로 들고 인증서를 하나씩 처리한다(RFC 5280 §6.1.2 초기화 → §6.1.3·6.1.4 반복 → §6.1.5 마무리).
- **DER = TLV 중첩** — 길이를 먼저 적는 프레이밍이다. 파서 버그(길이 넘침)가 인증서 처리의 고전적 취약점 원천이다.
- **전자서명 검증** — 발급자 공개키로 tbsCertificate의 서명을 확인한다(`security/06-public-key-and-signatures`, 미작성 — [security 영역 표](../../security/README.md)).

## 적용 — 풀어나가는 법

### 1. 서버가 무엇을 보내는지 본다

```bash
# 체인 전체 보기: "Certificate chain" 의 0 s:/i: 줄, 끝의 Verify return code
openssl s_client -connect api.example.com:443 -servername api.example.com \
  -showcerts </dev/null

# 리프의 핵심 필드
openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName,basicConstraints

# 로컬 파일 체인 검증 (중간 인증서를 -untrusted 로 따로 준다)
openssl verify -CAfile root.pem -untrusted intermediate.pem leaf.pem

# 호스트명까지 검증
openssl verify -CAfile root.pem -untrusted intermediate.pem \
  -verify_hostname api.example.com leaf.pem
```

- `s_client`의 `Verify return code: 0 (ok)`가 아니면 코드와 문구를 본다. 예: `20 (unable to get local issuer certificate)`, `10 (certificate has expired)`.
- `depth=0`이 리프, 숫자가 커질수록 루트 쪽이다.

### 2. 서버 설정

- 인증서 파일에 **리프 + 중간**을 순서대로 넣는다(fullchain). 루트는 넣지 않아도 된다.
- 배포 뒤 `openssl s_client -showcerts`로 체인이 2장 이상 오는지 확인한다.

### 3. 클라이언트 코드 — 사내 CA 추가

Java — 기본 `cacerts`를 버리지 않고 사내 루트를 **더하려면** 두 트러스트 매니저를 합치거나, `cacerts` 사본에 사내 루트를 import한 파일을 쓴다.

```java
// cacerts 사본 + 사내 루트 (keytool -importcert 로 미리 추가한 파일)
KeyStore ts = KeyStore.getInstance("PKCS12");
try (InputStream in = Files.newInputStream(Path.of("/etc/app/truststore.p12"))) {
    ts.load(in, password);
}
TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
tmf.init(ts);
SSLContext ctx = SSLContext.getInstance("TLS");
ctx.init(null, tmf.getTrustManagers(), null);

// raw 소켓이라면 호스트명 검증을 직접 켠다
SSLParameters p = new SSLParameters();
p.setEndpointIdentificationAlgorithm("HTTPS");
```

Node — `ca`는 대체, `NODE_EXTRA_CA_CERTS`는 추가다.

```js
const tls = require('node:tls');
const fs = require('node:fs');
// 기본 목록 + 사내 루트 (ca 에 사내 루트만 주면 공인 사이트가 전부 실패한다)
const ca = [...tls.rootCertificates, fs.readFileSync('/etc/app/corp-root.pem', 'utf8')];
const sock = tls.connect({ host: 'api.internal', port: 443, servername: 'api.internal', ca });
sock.on('secureConnect', () => console.log(sock.authorized, sock.authorizationError));
sock.on('error', (e) => console.error(e.code)); // UNABLE_TO_GET_ISSUER_CERT_LOCALLY 등
```

### 4. 진단 순서

1. 에러 문구로 분류한다: 발급자 못 찾음 / 만료·아직 유효 전 / 이름 불일치 / 자체 서명.
2. `openssl s_client -showcerts`로 서버가 보내는 체인을 본다.
3. 실패하는 클라이언트의 루트 스토어가 무엇인지 확인한다(Java `cacerts`, Node 번들, 컨테이너 CA 번들).
4. 양쪽 시계를 확인한다(`date -u`).

## 장애 시나리오와 대처

### 1. 중간 인증서 누락 — "브라우저는 되는데 서버 간 호출만 실패"

- **현상**: 인증서 갱신 뒤 브라우저는 정상인데, 배치·마이크로서비스·curl만 TLS 에러다.
- **보이는 형태**
  - Java `javax.net.ssl.SSLHandshakeException: PKIX path building failed: ... unable to find valid certification path to requested target`
  - OpenSSL/curl `unable to get local issuer certificate` 또는 `unable to verify the first certificate`
  - Node `UNABLE_TO_VERIFY_LEAF_SIGNATURE`·`UNABLE_TO_GET_ISSUER_CERT_LOCALLY`
  - `openssl s_client -showcerts`에 인증서가 **1장**만 보인다.
- **원인**
  - 서버 설정에 리프만 넣고 중간 인증서를 뺐다.
  - 브라우저는 AIA로 받아 오거나(Chrome) 미리 받아 둔 중간 인증서로(Firefox) 경로를 채운다.
  - 서버 간 클라이언트는 그러지 않는다.
- **대처**
  - fullchain(리프 + 중간)으로 교체한다.
  - 배포 파이프라인에 `openssl s_client -showcerts` 체인 길이 검사를 넣는다.
  - 클라이언트 쪽 AIA 켜기는 임시방편이다.

### 2. 만료 — `certificate has expired`

- **현상**: 특정 시각부터 모든 클라이언트가 동시에 실패한다.
- **보이는 형태**
  - OpenSSL `certificate has expired`(코드 10)
  - Java `CertificateExpiredException`이 원인에 포함된 `SSLHandshakeException`
  - Node `CERT_HAS_EXPIRED`
  - TLS alert `certificate_expired`(45)
- **원인**
  - 리프 갱신 누락이 가장 흔하다.
  - 중간·루트 만료도 있다. 교차 서명 루트 만료 때는 구현이 다른 경로를 못 찾아 실패했다(2021-09-30, DST Root CA X3, OpenSSL 1.0.x).
- **대처**
  - 자동 갱신과 만료 감시([32번](../32-mtls-and-cert-operations/2-summary.md)).
  - 체인 속 **모든** 인증서의 notAfter를 감시한다.
  - 오래된 클라이언트 라이브러리(경로 구축이 약한 것)를 올린다.

### 3. 시계 어긋남 — `not yet valid`

- **현상**: 새로 띄운 VM·임베디드 장비·컨테이너 호스트에서만 방금 발급한 인증서가 거부된다.
- **보이는 형태**
  - OpenSSL `certificate is not yet valid`(코드 9, OpenSSL 3.6부터는 "or the system clock is incorrect"가 붙는다)
  - Java `CertificateNotYetValidException`
  - 장비의 `date -u`가 과거다.
- **원인**
  - 검증은 **클라이언트의 현재 시각**으로 한다(RFC 5280 §6.1.3 (a)(2)).
  - 시계가 notBefore보다 이르면 실패한다.
  - 반대로 시계가 미래로 가 있으면 멀쩡한 인증서가 "만료"로 보인다.
- **대처**
  - NTP 동기화를 부팅 초기에 보장한다([distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md)).
  - 인증서 발급 직후 즉시 배포할 때는 클라이언트 시계 편차를 고려한다.

### 4. 호스트명 불일치

- **현상**: 체인은 정상인데 이름 오류로 실패한다.
- **보이는 형태**
  - Java `CertificateException: No subject alternative DNS name matching x found`
  - Node `ERR_TLS_CERT_ALTNAME_INVALID`
  - OpenSSL `-verify_hostname` 사용 시 `hostname mismatch`(코드 62)
- **원인**
  - SAN에 그 이름이 없다.
  - SAN이 아예 없고 CN에만 이름이 있는 옛 인증서는 CN 폴백을 하지 않는 구현(RFC 9525를 따르는 구현, OpenSSL `X509_CHECK_FLAG_NEVER_CHECK_SUBJECT`)에서 실패한다.
  - 와일드카드가 두 단계 서브도메인을 덮는다고 착각했다(`*.example.com` ≠ `a.b.example.com`).
  - IP로 접속했는데 SAN에 IP 항목이 없다.
  - SNI 누락으로 기본 인증서가 왔다(29번).
- **대처**
  - 필요한 이름을 모두 SAN에 넣어 재발급한다.
  - 검증을 끄지 않는다. `rejectUnauthorized: false`, 모든 이름을 통과시키는 `HostnameVerifier`는 중간자 공격을 허용한다.

### 5. 트러스트스토어 교체로 공인 사이트 전부 실패

- **현상**: 사내 API 연결을 고치려고 트러스트스토어를 지정했더니, 이번엔 외부 결제·클라우드 API가 전부 실패한다.
- **보이는 형태**: 외부 호출에서 `PKIX path building failed`·`UNABLE_TO_GET_ISSUER_CERT_LOCALLY`.
- **원인**
  - Java `javax.net.ssl.trustStore`는 기본 `cacerts`를 **대체**한다.
  - Node `ca`도 기본 목록을 **대체**한다.
  - 사내 루트만 든 저장소가 됐다.
- **대처**
  - 기본 목록 + 사내 루트를 합친 저장소를 만든다.
  - Node는 `NODE_EXTRA_CA_CERTS` 또는 `[...tls.rootCertificates, corp]`.
  - 컨테이너 이미지의 CA 번들 갱신 여부도 확인한다.

## 핵심 문장

- 인증서는 CA가 "이 이름 ↔ 이 공개키"에 서명한 문서이고, 서명은 tbsCertificate 전체를 덮는다.
- 서버는 리프와 중간 인증서를 보내야 하고, 클라이언트는 자기 루트 스토어의 신뢰 앵커까지 경로를 찾는다. 경로 **구축**은 규격 밖이라 구현마다 다르다.
- 경로 검증은 인증서마다 서명·유효기간·폐기·발급자 이름을 보고, CA 단계에서는 `cA=TRUE`·경로 길이·`keyCertSign`을 본다(RFC 5280 §6.1).
- 체인 검증과 호스트명 검증은 별개다. 이름은 SAN에서 찾고(DNS SAN이 없을 때 CN 폴백은 구현 의존), 와일드카드는 맨 왼쪽 레이블 하나에만 매치한다(RFC 9525).
- "브라우저는 되는데 서버 간 호출만 실패"는 대개 중간 인증서 누락이다. 브라우저는 빠진 중간을 스스로 채우지만 서버 간 클라이언트는 그러지 않는다.

## 관련 주제·근거

- 선행
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) — Certificate·CertificateVerify 메시지, 인증서 관련 alert
  - `security/06-public-key-and-signatures` — 전자서명. 미작성([security 영역 표](../../security/README.md))
- 후속
  - [31-revocation-ocsp-ct](../31-revocation-ocsp-ct/2-summary.md) — 체인 검증의 "폐기되지 않았나" 단계, CT
  - [32-mtls-and-cert-operations](../32-mtls-and-cert-operations/2-summary.md) — 클라이언트 인증서, 자동 갱신, 만료 감시
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- RFC 5280 <https://www.rfc-editor.org/rfc/rfc5280>
  - §4.1 인증서 필드 · §4.1.2.5 유효기간 · §4.2 critical 확장 거부(MUST) · §4.2.1.1–2 키 식별자 · §4.2.1.3 keyUsage · §4.2.1.6 SAN · §4.2.1.9 basicConstraints · §4.2.1.12 EKU · §4.2.2.1 AIA
  - §6.1 경로 검증(6.1.3 기본 처리, 6.1.4 CA 단계 (k)(l)(m)(n))
- RFC 9525 서비스 신원 검증(RFC 6125 대체) §6.3 DNS 이름 비교·와일드카드 · 부록 A CN-ID 폐지 <https://www.rfc-editor.org/rfc/rfc9525>
- RFC 8446 §4.4.2 Certificate 메시지 순서 · §4.4.2.4 · §6.2 alert(bad_certificate 42, certificate_expired 45, unknown_ca 48) <https://www.rfc-editor.org/rfc/rfc8446>
- RFC 4158 인증 경로 구축(Informational) <https://www.rfc-editor.org/rfc/rfc4158>
- OpenSSL 검증 오류 문구 `crypto/x509/x509_txt.c` <https://github.com/openssl/openssl/blob/master/crypto/x509/x509_txt.c> · `openssl-verify` <https://docs.openssl.org/3.0/man1/openssl-verify/>
- Oracle JSSE Reference Guide(트러스트스토어 선택 순서, 엔드포인트 식별) <https://docs.oracle.com/en/java/javase/21/security/java-secure-socket-extension-jsse-reference-guide.html>
- Oracle Java PKI Programmer's Guide(`com.sun.security.enableAIAcaIssuers`) <https://docs.oracle.com/en/java/javase/21/security/java-pki-programmers-guide.html>
- OpenSSL `X509_check_host(3)`(DNS SAN이 없을 때 subject DN 사용이 기본, `X509_CHECK_FLAG_NEVER_CHECK_SUBJECT`) <https://docs.openssl.org/3.0/man3/X509_check_host/> · JDK `sun/security/util/HostnameChecker.java` `matchDNS` · Node `lib/tls.js` `checkServerIdentity`
- Node.js `tls`(`ca` 대체, `checkServerIdentity`) <https://nodejs.org/api/tls.html> · CLI(`NODE_EXTRA_CA_CERTS`, `--use-system-ca`) <https://nodejs.org/api/cli.html>
- nginx `ssl_certificate`(리프 다음 중간) <https://nginx.org/en/docs/http/ngx_http_ssl_module.html>
- Mozilla "Preloading Intermediate CA Certificates into Firefox"(2020) <https://blog.mozilla.org/security/2020/11/13/preloading-intermediate-ca-certificates-into-firefox/> · Mozilla wiki "Intermediate Preloading" <https://wiki.mozilla.org/Security/CryptoEngineering/Intermediate_Preloading>
- CVE-2011-0228 — iOS의 basicConstraints 미검사 <https://nvd.nist.gov/vuln/detail/CVE-2011-0228>
- Chromium net-dev "AIA fetching" 논의 <https://groups.google.com/a/chromium.org/g/net-dev/c/H-ysp5UM_rk/m/TcKRw3pbDAAJ>
- Let's Encrypt "DST Root CA X3 Expiration (September 2021)" <https://letsencrypt.org/docs/dst-root-ca-x3-expiration-september-2021/>
- badssl.com — 만료·잘못된 이름·불완전 체인 등 실습용 서버 <https://badssl.com/>
