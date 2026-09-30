# network/30-x509-and-chain-validation — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. CertificateVerify만으로 부족한 이유

- CertificateVerify는 "Certificate 메시지에 든 공개키의 개인키를 상대가 쥐고 있다"만 증명한다.
- 공격자도 자기 키쌍으로 "나는 api.example.com"이라는 인증서를 만들어 똑같이 증명할 수 있다.
- 필요한 것은 "이 공개키가 **정말 그 이름의 것**"이라는 제3자 보증이다.
  - 클라이언트가 원래 믿는 루트까지 서명을 따라 올라가 확인한다. 이것이 체인 검증이다.
  - 그 인증서의 이름이 내가 접속하려던 이름인지도 확인한다. 이것이 호스트명 검증이다.

### 2. 인증서 구조

```text
  tbsCertificate: version, serial, signature(alg), issuer, validity, subject, SPKI, extensions
  signatureAlgorithm
  signatureValue  = issuer 개인키로 tbsCertificate 에 서명
```

- 체인 검증에 쓰이는 확장
  - `basicConstraints`(cA, pathLen)
  - `keyUsage`(keyCertSign)
  - `authorityKeyIdentifier`/`subjectKeyIdentifier`(발급자 찾기)
  - `authorityInfoAccess`(caIssuers)
- 호스트명 검증에 쓰이는 확장
  - `subjectAltName`(DNS·IP 항목)
  - 넓게 보면 `extKeyUsage`(serverAuth — 서버 인증서 용도 확인)도 있다.

### 3. 체인과 루트 스토어

```text
  서버 전송:  [0] 리프 (api.example.com, issuer=중간)
              [1] 중간 (issuer=루트)
  클라이언트:  루트 스토어에 루트 (신뢰 앵커)
```

- 리프가 반드시 첫 번째다(MUST). 다음 인증서는 앞 인증서의 발급자이기를 권한다(SHOULD)(RFC 8446 §4.4.2).
- 신뢰 앵커(루트)는 생략해도 된다(MAY). 클라이언트가 이미 갖고 있어야 의미가 있기 때문이다.
- 중간 인증서는 생략하지 않는다. 클라이언트 루트 스토어에는 보통 없어서, 빠지면 AIA 조회 같은 보완이 없는 클라이언트는 검증에 실패한다.

### 4. 경로 검증 항목

인증서마다(§6.1.3 (a)):
1. 서명이 직전 단계의 작업 공개키로 검증된다.
2. 현재 시각이 유효기간 안이다.
3. 폐기되지 않았다(31번).
4. issuer 이름이 직전 인증서의 subject와 같다.

CA 단계(마지막 리프 제외, §6.1.4):
1. (k) `basicConstraints`가 있고 `cA=TRUE`다.
2. (l)(m) 경로 길이 제한(`pathLenConstraint`)을 넘지 않는다.
3. (n) `keyUsage`가 있으면 `keyCertSign` 비트가 켜져 있다.

그 밖에 이해하지 못하는 critical 확장이 있으면 거부한다(MUST, §4.2).

### 5. 브라우저는 되고 Java는 실패

- 원인: 서버가 **중간 인증서를 보내지 않는다**(리프만 설정).
- 브라우저가 멀쩡한 이유
  - Chrome은 리프의 AIA `caIssuers` URL에서 중간을 받아 온다.
  - Firefox는 신뢰된 중간 CA 인증서를 미리 내려받아 둔다(Mozilla, 2020).
  - Java는 AIA 사용이 기본 꺼짐이다(`com.sun.security.enableAIAcaIssuers`).
- 확인: `openssl s_client -connect host:443 -servername host -showcerts`에서 인증서가 1장뿐이고, `Verify return code: 20 (unable to get local issuer certificate)` 또는 `21 (unable to verify the first certificate)`가 나온다.
- 해결: 서버에 fullchain(리프 + 중간)을 설정한다. 배포 검사에 체인 길이 확인을 넣는다.

### 6. 와일드카드 예측

- `api.example.com` → **매치**. 와일드카드는 맨 왼쪽 레이블 하나에 매치한다.
- `a.b.example.com` → **불일치**. 레이블 두 개를 덮지 못한다(RFC 9525 §6.3).
- `example.com` → **불일치**. 와일드카드 자리에 대응할 레이블이 없다.
- CN에 `example.com`이 있어도 결과는 바뀌지 않는다.
  - RFC 9525는 CN으로 서버 신원을 표현하는 방식(CN-ID)을 없앴다. SAN만 본다.
  - CN 폴백을 하는 구현(OpenSSL `X509_check_host()` 기본값, JDK, Node)도 **DNS SAN이 하나도 없을 때만** CN을 본다. 이 인증서에는 DNS SAN(`*.example.com`)이 있으므로 CN은 무시된다.
  - 해결은 SAN에 `example.com`을 추가하는 것이다.

### 7. 경로 구축과 교차 서명

- RFC 5280 §6.1은 "주어진 인증서 순서가 유효한지"를 검사하는 알고리즘만 정한다. 인증서를 어디서 모아 **어떤 순서로 엮을지**(구축)는 규격 밖이다.
- 그래프로 보면 이렇다.
  - 정점 = 인증서, 간선 = "서명했다".
  - 교차 서명이 있으면 같은 중간에서 루트로 가는 경로가 둘 이상이다.
- 좋은 구현은 한 경로가 만료 등으로 실패하면 **되돌아가**(백트래킹) 다른 발급자 후보로 다시 탐색한다.
- 약한 구현은 처음 고른 경로만 검사하고 실패를 보고한다.
  - 2021-09-30 DST Root CA X3 만료 때 OpenSSL 1.0.x가 만료된 경로를 골라 실패했다(Let's Encrypt 문서).
  - 같은 인증서를 다른 구현은 ISRG Root X1 경로로 검증에 성공했다.

### 8. 트러스트스토어 대체

- Node `ca` 옵션은 기본 신뢰 목록을 **완전히 대체**한다(Node 문서). 사내 루트만 믿게 되어 공인 CA가 발급한 외부 API 인증서를 검증할 수 없다.
  - 고치기: `ca: [...tls.rootCertificates, corpRoot]`, 또는 `ca`를 빼고 `NODE_EXTRA_CA_CERTS=/path/corp.pem`(기본 목록에 추가).
- Java에서 같은 실수: `-Djavax.net.ssl.trustStore=corp.p12`로 사내 루트만 든 파일을 지정한다. 지정한 파일만 쓰고 `cacerts`와 합치지 않는다.
  - 고치기: `cacerts` 사본에 사내 루트를 `keytool -importcert`로 추가한 파일을 쓴다. 또는 두 TrustManager를 합성한다.

### 9. not yet valid

- 검증은 **클라이언트 시계**로 한다. 장비 시계가 인증서 notBefore보다 이르면 실패한다.
- 확인
  - `date -u`와 NTP 동기화 상태(`timedatectl`, `chronyc tracking` 등)를 본다.
  - `openssl x509 -noout -dates`로 notBefore를 확인한다.
- 반대로 시계가 미래로 가 있으면 멀쩡한 인증서가 `certificate has expired`로 보인다.
  - OCSP 응답·JWT 같은 다른 시간 검사도 함께 깨질 수 있다.

### 10. Java raw SSLSocket의 호스트명 검증

- **검증되지 않는다.** JSSE 문서: `SSLSocket`과 `SSLEngine`은 URL의 호스트명과 상대 인증서의 이름을 자동으로 맞춰 보지 않는다.
- `HttpsURLConnection`은 JDK 7부터 핸드셰이크 중 HTTPS 엔드포인트 식별을 기본으로 한다.
- raw 소켓에서는 `SSLParameters.setEndpointIdentificationAlgorithm("HTTPS")`를 설정한다.
- 체인 검증만 통과하면, 공인 CA에서 자기 도메인 인증서를 받은 공격자가 중간자가 될 수 있다.
