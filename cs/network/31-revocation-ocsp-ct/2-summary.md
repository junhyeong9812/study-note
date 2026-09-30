# network/31-revocation-ocsp-ct — 인증서 폐기와 투명성: CRL·OCSP·stapling·CT, 수명 단축 흐름 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

인증서는 유효기간(notAfter)까지 스스로 유효하다([30번](../30-x509-and-chain-validation/2-summary.md)).\
그 사이에 일이 생길 수 있다.

```text
  1. 개인키가 유출됐다        -> 공격자가 그 인증서로 서버 행세를 한다
  2. CA가 잘못 발급했다        -> 남의 도메인 인증서가 누군가에게 있다
  3. 도메인 주인이 바뀌었다     -> 옛 주인의 인증서가 아직 유효하다
```

필요한 것은 두 가지다.
- **폐기(revocation)**: "이 인증서는 만료 전이지만 더는 믿지 말라"를 알리는 길.
- **투명성(transparency)**: "누가 내 도메인 인증서를 몰래 발급받지 않았나"를 알아채는 길.

쉬운 예: 분실 신고한 신용카드다.\
카드에 적힌 유효기간은 아직 남았다.\
가맹점은 결제 때 카드사에 "이 카드 정지됐나?"를 묻거나(OCSP), 매일 받는 정지 카드 목록을 본다(CRL).\
카드사가 몰래 카드를 더 찍어 내지 않았는지는 공개 발급 장부(CT)로 감시한다.

똑같은 구조다.\
폐기는 "만료 전 무효화", CT는 "발급 사실의 공개 기록"이다.

실무 예:
- OCSP 응답기가 느려지자 hard-fail 설정 클라이언트가 전부 연결 실패한다.
- Let's Encrypt가 2025년에 OCSP를 끝냈다. 공인 인증서 최대 수명이 2026년부터 단계적으로 줄어든다.

## 동작·원리

### 1. CRL — 폐기 목록을 통째로 받는다

```text
  CA ---- 주기적으로 서명한 목록 게시 ----> http://crl.ca.example/r11.crl
                                                  |
  CertificateList (RFC 5280 §5)                   |  클라이언트가 내려받아 캐시
    thisUpdate   2026-09-30 00:00 (예시)           |
    nextUpdate   2026-10-07 00:00 (예시)           v
    revokedCertificates                     [로컬 검사: 이 serial 이 목록에 있나?]
      serial 0x3A..  2026-09-29  keyCompromise
      serial 0x7F..  2026-09-28  superseded
    CA 서명
```

- 인증서의 `cRLDistributionPoints` 확장이 CRL 위치를 알려 준다(§4.2.1.13).
- CRL 발급자는 `nextUpdate`를 반드시 넣는다(MUST, §5.1.2.5). 클라이언트는 그때까지 캐시한다.
- 폐기 사유 코드가 있다(§5.3.1). 예: `keyCompromise(1)`, `superseded(4)`, `cessationOfOperation(5)`, `certificateHold(6)`.
- 장점: 클라이언트가 **어느 사이트를 보는지 CA가 모른다**. 한 번 받으면 오프라인 검사다.
- 단점: 목록이 커지고, 받아 둔 CRL만 쓰는 동안은 새 폐기를 모른다.
  - `nextUpdate`는 다음 CRL이 **늦어도** 나오는 시각이다. 더 일찍 나올 수도 있다(§5.1.2.5).

### 2. OCSP — 한 장씩 실시간으로 묻는다

```text
  클라이언트                                   OCSP 응답기 (AIA 의 id-ad-ocsp URL)
     | 요청: CertID = (hashAlg, issuerNameHash, issuerKeyHash, serial)
     |------------------------------------------------>|
     |                                                  |
     |<------------------------------------------------|
     | 응답 (서명됨):
     |   certStatus   good | revoked(시각, 사유) | unknown
     |   thisUpdate   이 상태가 맞다고 확인된 시각
     |   nextUpdate   다음 정보가 나올 시각 (이때까지 캐시, 선택 필드)
     |   producedAt   응답기가 서명한 시각
```

- 상태 세 가지(RFC 6960 §2.2)
  - `good`: 그 serial의 인증서 중 유효기간 안에 있는 것이 폐기되지 않았다. **발급된 적이 있다는 뜻은 아니다.**
  - `revoked`: 폐기됐다. 발급한 적 없는 serial에 이 상태를 줄 수도 있다(MAY).
  - `unknown`: 이 응답기는 모른다. 보통 이 응답기가 담당하지 않는 발급자다.
- 오류 응답(`malformedRequest`, `internalError`, `tryLater`, `sigRequired`, `unauthorized`)은 **서명되지 않는다**(§2.3).
- 응답 서명자(§4.2.2.2)
  - 발급 CA가 직접 서명하거나, CA가 직접 발급한 위임 인증서(EKU `id-kp-OCSPSigning`)로 서명한다.
  - 클라이언트가 로컬 설정으로 따로 믿기로 한 응답기(Trusted Responder)도 된다(§2.2, §4.2.2.2).
- nonce 확장으로 요청·응답을 묶어 재전송 공격을 막을 수 있다(§4.4.1).

OCSP의 세 가지 문제:
1. **사생활**: 응답기(CA)가 "누가 어느 사이트에 접속하는지"를 본다. Let's Encrypt가 OCSP를 끝낸 이유 중 하나다.
2. **지연**: 캐시된 응답이 없으면 첫 연결마다 다른 서버에 한 번 더 묻는다.
3. **가용성**: 응답기가 죽으면 어떻게 할 것인가 — soft-fail 대 hard-fail(§4).

### 3. OCSP stapling — 서버가 대신 받아 붙여 준다

```text
  서버 --(주기적으로)--> OCSP 응답기 : 내 인증서 상태?
  서버 <--------------- 서명된 OCSP 응답 (nextUpdate 까지 캐시)

  클라이언트 ClientHello + status_request(ocsp)  ---->
             <----  Certificate
                      CertificateEntry(리프) + status_request 확장 = 리프의 OCSP 응답   (TLS 1.3)
```

- 클라이언트가 `status_request` 확장을 보내면 서버가 OCSP 응답을 핸드셰이크에 실어 준다(RFC 6066 §8).
  - TLS 1.2는 별도의 CertificateStatus 메시지로 보낸다.
  - TLS 1.3은 그 응답이 다루는 인증서의 CertificateEntry 확장에 넣는다(RFC 8446 §4.4.2.1). 보통은 리프다.
- 응답은 CA가 서명했으므로 서버가 위조할 수 없다. 사생활·지연 문제가 사라진다.
- 서버가 stapling을 **안 하면** 클라이언트는 모른다. 공격자는 스테이플을 빼고 보내면 된다.
  - 그래서 인증서에 "반드시 스테이플할 것"을 적는 **Must-Staple**(RFC 7633 TLS Feature 확장)이 나왔다.

### 4. soft-fail 대 hard-fail — 응답기가 안 보일 때

```text
                      응답기 무응답 / 타임아웃
                               |
              +----------------+----------------+
              v                                 v
         soft-fail: 통과                   hard-fail: 연결 거부
         - 폐기된 인증서를 쓰는 공격자가     - 캐시·스테이플이 없으면 응답기 장애 = 내 서비스 장애
           OCSP 요청만 막으면 통과          - CA 가용성에 내 가용성이 묶인다
```

- 폐기 확인이 가장 필요한 순간(중간자가 있는 순간)에 중간자는 OCSP 요청도 막을 수 있다. 그래서 soft-fail은 보안 효과가 약하다.
- hard-fail은 CA 장애를 그대로 내 장애로 만든다.
- 브라우저의 선택
  - Chrome은 온라인 OCSP·CRL 검사를 일반적으로 하지 않는다. 대신 CRLSet(선별한 폐기 목록)을 내려받는다(Chromium 문서).
  - Firefox는 137 버전부터 CRLite를 쓴다. CT 로그에 있는 인증서들의 폐기 상태를 압축 인코딩해 내려받아 로컬에서 검사한다(Mozilla Hacks, 2025).
- 서버 간 클라이언트(Java 등)는 폐기 검사 자체가 기본 꺼짐인 경우가 많다.
  - Java: `TrustManagerFactory.init(KeyStore)` 경로의 기본은 폐기 검사 비활성이다. `com.sun.net.ssl.checkRevocation=true`로 켠다(JSSE 가이드).
  - OCSP 조회는 `ocsp.enable` 보안 속성, CRL 배포점 사용은 `com.sun.security.enableCRLDP`로 켠다.

### 5. 흐름 — OCSP 퇴장, CRL 복귀, 수명 단축

```text
  2024-12-05  Let's Encrypt "Ending OCSP Support in 2025" 공지
  2025-01-30  LE: Must-Staple 요청 실패 (Must-Staple 인증서를 받은 적 있는 계정 제외)
  2025-04-11  CA/B Forum SC-081v3 통과
  2025-05-07  LE: 인증서에서 OCSP URL 제거, Must-Staple 요청 전부 실패
  2025-08-06  LE: OCSP 응답기 종료 -> CRL 로 대체
  2026-03-15  공인 TLS 인증서 최대 수명 398일 -> 200일
  2027-03-15                              -> 100일
  2029-03-15                              -> 47일   (도메인 검증 재사용 기간도 10일로)
```

- 논리: 폐기 전파가 잘 안 되니 **인증서 수명 자체를 줄여** 피해 창을 좁힌다.
- Let's Encrypt 계획(2025-12-02 공지)
  - `tlsserver` 프로필은 2026-05-13부터 45일 인증서.
  - 기본 `classic` 프로필은 2027-02-10에 64일, 2028-02-16에 45일.
  - 6일짜리 `shortlived` 프로필이 따로 있다.
- 아주 짧은 수명 인증서는 폐기 정보 자체를 내지 않을 수 있다. RFC 9608은 이를 알리는 `noRevAvail` 확장을 정했다.
- 결과: **갱신 주기가 빨라져 자동화가 필수**가 된다([32번](../32-mtls-and-cert-operations/2-summary.md)).

### 6. Certificate Transparency — 발급 사실의 공개 장부

```text
  CA --(사전 인증서 제출)--> CT 로그 A, 로그 B
  CA <--------- SCT (서명된 타임스탬프 = "넣겠다"는 약속)
  CA: SCT 를 인증서에 넣어 발급

  TLS 클라이언트: 인증서의 SCT 를 확인 (Chrome: 서로 다른 운영자의 로그 SCT 필요)
  모니터(도메인 주인·보안팀): 로그 전체를 계속 읽어
                          "내가 요청하지 않은 example.com 인증서"를 찾는다
```

- CT는 잘못된 발급을 **막지 않는다.** 잘못된 발급을 **보이게** 한다(RFC 9162 §1).
- 로그는 **추가 전용(append-only)**이다. 이 성질을 머클 트리로 증명한다.
- *SCT(Signed Certificate Timestamp)*: 로그가 "이 인증서를 정해진 시간(Maximum Merge Delay) 안에 로그에 넣겠다"고 서명한 약속이다.
- *사전 인증서(precertificate)*: SCT를 인증서에 넣으려면 발급 전에 로그에 내야 한다. 그래서 critical "poison" 확장을 넣어 TLS에 쓸 수 없게 만든 사본을 제출한다(RFC 6962 §3.1).
- SCT 전달 경로 세 가지(RFC 9162 §6): 인증서 확장, TLS 확장, stapled OCSP 응답.
- Chrome: 공인 TLS 인증서는 CT 정책을 만족해야 검증된다. 인증서에 넣는 SCT는 수명 180일 이하면 2개, 초과면 3개다(Chrome CT 정책).
- 규격: 현장에서 쓰는 것은 RFC 6962(CT 1.0)다. RFC 9162(CT 2.0, Experimental)가 6962를 대체 문서로 냈다.

## 쓰이는 자료구조·알고리즘

- **CT = 머클 트리**([data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md))
  - 잎 해시 `HASH(0x00 || 항목)`, 내부 노드 `HASH(0x01 || 왼쪽 || 오른쪽)`이다. 접두 바이트를 달리해 잎과 내부 노드를 구별한다(2차 역상 방지, RFC 9162 §2.1.1).
  - **포함 증명(inclusion proof)**: 잎에서 뿌리까지 가는 길의 형제 노드 목록이다. 길이는 O(log n)이다. "이 인증서가 로그에 있다"를 로그 전체 없이 확인한다.
  - **일관성 증명(consistency proof)**: 옛 트리(m개)가 새 트리(n개)의 앞부분과 같음을 보인다. "로그가 과거 항목을 지우거나 바꾸지 않았다"를 증명한다.
  - *STH(Signed Tree Head)*: 로그가 서명한 (트리 크기, 뿌리 해시)다.
- **CRL = 폐기 항목 목록 → 집합 조회** — RFC는 목록의 정렬이나 조회 구조를 정하지 않는다(§5.1). 구현은 serial(여러 발급자를 담는 간접 CRL이면 발급자+serial)을 키로 집합을 만들 수 있다. 해시 셋이면 평균 O(1)에 조회한다.
- **CRLite = 확률적 집합의 연쇄** — 처음 설계는 거짓 양성이 없도록 블룸 필터를 층층이 쌓은 구조(다단 필터 캐스케이드)였다. 지금 Firefox 구현은 대역폭을 줄이려고 "Clubcard"라는 2단 Ribbon 필터 캐스케이드로 바꿨다(Mozilla Hacks, 2025-08). [블룸 필터](../../data-structure/11-bloom-filter/2-summary.md) 참고.
- **OCSP 응답 캐시 = TTL 캐시** — 키는 CertID, 만료는 보통 `nextUpdate`다. `nextUpdate`가 없는 응답은 "늘 더 새 정보가 있다"는 뜻이라, 얼마나 믿을지는 클라이언트 정책이다(RFC 6960 §4.2.2.1). stapling 서버와 클라이언트 모두 이것을 쓴다([28번](../28-dns-caching-and-ttl/2-summary.md)의 TTL 캐시와 같은 모양).

## 적용 — 풀어나가는 법

### 1. 인증서가 무엇을 제공하는지 본다

```bash
# OCSP URL (없으면 빈 줄 — Let's Encrypt 는 2025-05 부터 없음)
openssl x509 -in leaf.pem -noout -ocsp_uri
# CRL 배포점, SCT 목록
openssl x509 -in leaf.pem -noout -ext crlDistributionPoints,ct_precert_scts

# CRL 내용
curl -s http://crl.ca.example/r11.crl | openssl crl -inform DER -noout -text | head

# OCSP 직접 질의
openssl ocsp -issuer intermediate.pem -cert leaf.pem -url http://ocsp.ca.example -resp_text

# 서버가 스테이플하나
openssl s_client -connect api.example.com:443 -servername api.example.com -status </dev/null \
  | grep -A3 'OCSP response'
```

### 2. CT 로그 검색으로 도메인 발급 감시

- crt.sh 같은 CT 검색 서비스에서 `%.example.com`을 조회한다. 모르는 발급자·모르는 시점의 인증서가 있는지 본다.
- 정기 감시로 돌린다. 새 인증서가 나오면 알림을 받는다.
- DNS CAA 레코드로 "우리 도메인은 이 CA만 발급 가능"을 선언해 사전 차단을 더한다(RFC 8659).

### 3. 서버 설정 — stapling

```nginx
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/nginx/chain.pem;   # 발급자·중간·루트 (응답 검증용)
resolver 127.0.0.53;                            # OCSP 응답기 이름 해석
```

- nginx 기본값은 `ssl_stapling off`다.
- 발급자 인증서를 알아야 하고, 응답기 이름 해석을 위해 `resolver`가 필요하다(nginx 문서).
- 인증서에 OCSP URL이 없으면(예: Let's Encrypt 2025-05 이후) nginx는 어디에 물을지 모른다. `ssl_stapling_responder`로 응답기 주소를 주거나 `ssl_stapling_file`로 응답 파일을 줄 수 있다(nginx 문서). 다만 LE처럼 응답기 자체가 없어졌으면 스테이플할 것이 없다.

### 4. 클라이언트 정책 정하기

- 공개 웹 클라이언트는 브라우저·OS 정책을 따른다.
- 서버 간 통신에서 폐기 검사를 켤 때는 먼저 정한다.
  - 응답기 장애 시 soft-fail로 할지 hard-fail로 할지.
  - 타임아웃은 얼마로 할지.
  - 캐시는 어떻게 할지.
- Java는 `PKIXRevocationChecker`에 `SOFT_FAIL` 같은 옵션을 준다.

```java
CertPathBuilder cpb = CertPathBuilder.getInstance("PKIX");
PKIXRevocationChecker rc = (PKIXRevocationChecker) cpb.getRevocationChecker();
rc.setOptions(EnumSet.of(PKIXRevocationChecker.Option.PREFER_CRLS,   // CRL 우선
                         PKIXRevocationChecker.Option.SOFT_FAIL));   // 조회 실패 시 통과
PKIXBuilderParameters params = new PKIXBuilderParameters(trustStore, new X509CertSelector());
params.addCertPathChecker(rc);
TrustManagerFactory tmf = TrustManagerFactory.getInstance("PKIX");
tmf.init(new CertPathTrustManagerParameters(params));
```

## 장애 시나리오와 대처

### 1. OCSP 응답기 장애 → hard-fail 클라이언트 전면 실패

- **현상**: 서버·인증서는 멀쩡한데 특정 클라이언트군이 일제히 TLS 실패다. 시작 시각이 CA 장애 공지와 겹친다.
- **보이는 형태**
  - 핸드셰이크가 OCSP 타임아웃만큼 늘어진 뒤 실패한다.
  - Java `CertPathValidatorException: Unable to determine revocation status due to network error`류(OpenJDK `RevocationChecker` 소스의 문구).
  - 응답기가 `tryLater`를 준다(서명 없는 오류 응답).
- **원인**
  - 클라이언트가 hard-fail로 폐기 확인을 요구한다.
  - 서버가 stapling을 하지 않아 클라이언트가 직접 응답기에 묻는다.
- **대처**
  - 서버에서 stapling을 켜 CA 응답기 의존을 서버 한 곳의 캐시로 모은다.
  - 클라이언트 정책을 CRL 우선·캐시·soft-fail로 재검토한다.
  - Must-Staple 인증서라면 스테이플 갱신 실패가 곧 장애다. 스테이플 만료를 감시한다.

### 2. Must-Staple 인증서인데 서버가 스테이플을 못 붙임

- **현상**: 인증서 교체 뒤 Firefox 등 일부 클라이언트만 접속 실패다.
- **보이는 형태**
  - `openssl s_client -status` 출력에 `OCSP response: no response sent`.
  - Must-Staple을 지원하는 클라이언트는 Must-Staple 위반 에러를 낸다.
- **원인**
  - 서버의 stapling이 꺼져 있다.
  - 또는 OCSP 응답기 이름을 해석하지 못해(`resolver` 미설정) 응답을 못 받았다.
  - 또는 서버 재시작 직후 첫 연결이다. nginx는 첫 요청 때 응답을 가져오기 시작한다 [?].
- **대처**
  - stapling 설정과 `resolver`를 확인한다.
  - Let's Encrypt처럼 OCSP를 끝낸 CA라면 Must-Staple 없는 인증서로 바꾼다. LE는 2025-01-30부터(그 전에 Must-Staple 인증서를 받은 계정은 2025-05-07부터) Must-Staple 요청을 거절한다.

### 3. OCSP 종료·수명 단축 뒤 갱신 주기 압박

- **현상**: 수동 갱신하던 인증서가 연 1회에서 연 몇 회로 늘어나 누락이 생긴다.
- **보이는 형태**
  - 만료 알림 빈도 증가.
  - 어느 날 `certificate has expired`(30번).
  - 인증서에서 OCSP URL이 사라져 OCSP 기반 모니터링이 "상태 알 수 없음"을 낸다.
- **원인**
  - SC-081 일정으로 최대 수명이 200일(2026-03-15) → 100일(2027-03-15) → 47일(2029-03-15)로 준다.
  - Let's Encrypt는 45일로 간다.
  - OCSP URL이 제거되어 OCSP 전제 도구가 깨졌다.
- **대처**
  - ACME 자동 갱신으로 전환한다([32번](../32-mtls-and-cert-operations/2-summary.md)).
  - ARI(RFC 9773)로 CA가 제시하는 갱신 시점을 따른다.
  - 폐기 모니터링은 CRL 기반으로 바꾼다.

### 4. CT 로그에서 모르는 인증서 발견

- **현상**: CT 감시에서 우리 도메인에 대해 우리가 요청하지 않은 인증서가 발견된다.
- **보이는 형태**: crt.sh 등에 낯선 발급자·시각의 `api.example.com` 인증서.
- **원인**
  - 오발급(CA 실수).
  - 도메인 검증 우회(DNS·웹 서버 탈취).
  - 사내 다른 팀의 발급(인벤토리 누락).
- **대처**
  - 먼저 사내 발급인지 인벤토리로 확인한다(32번).
  - 아니면 해당 CA에 폐기를 요청하고 DNS·서버 침해 여부를 조사한다.
  - CAA 레코드로 허용 CA를 좁힌다.

### 5. SCT 부족으로 Chrome에서만 실패 (사설 발급 흐름 실수)

- **현상**: 공인 CA에서 받은 인증서인데 Chrome에서만 인증서 오류다.
- **보이는 형태**: Chrome의 CT 관련 오류(`NET::ERR_CERTIFICATE_TRANSPARENCY_REQUIRED` — Chromium `net_error_list.h`의 `CERTIFICATE_TRANSPARENCY_REQUIRED`(-214)).
- **원인**: 인증서나 TLS 확장에 Chrome CT 정책을 만족하는 SCT가 없다. 일부 발급 옵션에서 CT 기록을 뺀 경우다.
- **대처**
  - 정책을 만족하는 SCT를 포함해 재발급한다.
  - `openssl x509 -ext ct_precert_scts`로 SCT 수·로그를 확인한다.

## 핵심 문장

- 폐기는 "만료 전 무효화"이고, CRL은 목록을 통째로, OCSP는 한 장씩 실시간으로 묻는다.
- OCSP는 사생활·지연·가용성 문제가 있다. stapling은 서버가 CA 서명 응답을 대신 받아 붙여 이를 줄인다.
- soft-fail은 공격자가 OCSP만 막으면 뚫리고, hard-fail은 CA 장애를 내 장애로 만든다. 그래서 브라우저는 CRLSet·CRLite 같은 사전 배포 방식으로 옮겨 갔다.
- 업계는 폐기 전파 대신 **수명 단축**으로 간다. SC-081로 최대 수명이 2029년 47일까지 줄고, Let's Encrypt는 OCSP를 끝냈다.
- CT는 오발급을 막지 않고 **보이게** 한다. 추가 전용 로그를 머클 트리로 만들고, 포함 증명과 일관성 증명으로 확인한다.

## 관련 주제·근거

- 선행
  - [30-x509-and-chain-validation](../30-x509-and-chain-validation/2-summary.md) — 경로 검증의 "폐기되지 않았나" 단계
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) — CertificateEntry 확장, `status_request`
- 후속·연결
  - [32-mtls-and-cert-operations](../32-mtls-and-cert-operations/2-summary.md) — ACME 자동 갱신, ARI, 인벤토리
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
  - [28-dns-caching-and-ttl](../28-dns-caching-and-ttl/2-summary.md) — TTL 캐시 모양
- RFC 5280 §4.2.1.13 CRL 배포점 · §5 CRL · §5.1.2.5 nextUpdate · §5.3.1 사유 코드 · §6.3 CRL 검증 <https://www.rfc-editor.org/rfc/rfc5280>
- RFC 6960 OCSP — §2.2 상태·Trusted Responder · §2.3 오류 응답 · §2.4 시각 필드 · §4.2.2.1 nextUpdate 없음의 뜻 · §4.2.2.2 위임 응답기 · §4.4.1 nonce <https://www.rfc-editor.org/rfc/rfc6960>
- RFC 6066 §8 `status_request` <https://www.rfc-editor.org/rfc/rfc6066> · RFC 8446 §4.4.2.1 TLS 1.3의 OCSP·SCT 위치 <https://www.rfc-editor.org/rfc/rfc8446>
- RFC 7633 TLS Feature 확장(Must-Staple) — §4.2.3.1 불일치 시 거부(SHOULD), 다른 경로로 확인하면 수락 가능(MAY) <https://www.rfc-editor.org/rfc/rfc7633>
- RFC 6962 CT 1.0 §3.1 사전 인증서 <https://www.rfc-editor.org/rfc/rfc6962> · RFC 9162 CT 2.0(Experimental) §1 · §2.1 머클 트리·증명 · §4.8 SCT · §6 SCT 전달 <https://www.rfc-editor.org/rfc/rfc9162>
- RFC 9608 `noRevAvail` <https://www.rfc-editor.org/rfc/rfc9608> · RFC 9773 ACME ARI <https://www.rfc-editor.org/rfc/rfc9773> · RFC 8659 CAA <https://www.rfc-editor.org/rfc/rfc8659>
- Let's Encrypt "Ending OCSP Support in 2025"(2024-12-05) <https://letsencrypt.org/2024/12/05/ending-ocsp/>
- Let's Encrypt "Decreasing Certificate Lifetimes to 45 Days"(2025-12-02) <https://letsencrypt.org/2025/12/02/from-90-to-45/>
- CA/Browser Forum Ballot SC-081v3(2025-04-11 통과) <https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/> · 일정 표: DigiCert 안내 <https://knowledge.digicert.com/alerts/public-tls-certificates-199-day-validity>
- Chromium "CRLSets" <https://www.chromium.org/Home/chromium-security/crlsets/> · Chrome CT 정책 <https://googlechrome.github.io/CertificateTransparency/ct_policy.html>
- Mozilla Hacks "CRLite: Fast, private, and comprehensive certificate revocation checking in Firefox"(2025-08) <https://hacks.mozilla.org/2025/08/crlite-fast-private-and-comprehensive-certificate-revocation-checking-in-firefox/>
- Oracle JSSE Reference Guide(`com.sun.net.ssl.checkRevocation`, stapling 속성) · Java PKI Programmer's Guide(`ocsp.enable`, `com.sun.security.enableCRLDP`)
- nginx `ssl_stapling`·`ssl_stapling_verify`·`ssl_trusted_certificate`·`ssl_stapling_responder`·`ssl_stapling_file` <https://nginx.org/en/docs/http/ngx_http_ssl_module.html>
- OpenJDK `sun/security/provider/certpath/RevocationChecker.java`(폐기 확인 실패 문구) · Chromium `net/base/net_error_list.h`(`CERTIFICATE_TRANSPARENCY_REQUIRED`)
