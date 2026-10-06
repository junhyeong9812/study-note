# security/07-key-exchange-forward-secrecy — 키 교환: Diffie-Hellman·ECDHE와 전방 비밀성 — 정리 (힌트)

## 해결하는 문제

대칭키 암호(AEAD)는 빠르지만 **양쪽이 같은 키**를 먼저 가져야 한다.\
처음 만난 두 사람은 도청되는 길 위에서 그 키를 정해야 한다.

```text
  방법 A: 키 전송 (TLS 1.2의 정적 RSA)
    클라이언트: 비밀 premaster를 서버 RSA 공개키로 암호화해서 보낸다
    → 서버 개인키 하나가 지금까지의 연결 키를 다 풀 수 있다

  방법 B: 키 합의 (Diffie-Hellman)
    양쪽이 공개값만 주고받고, 각자 같은 비밀을 계산한다
    → 비밀 자체는 선 위로 지나가지 않는다
```

- *키 교환(key exchange)*: 두 당사자가 공유 비밀키를 정하는 절차. **키 전송**(한쪽이 만들어 암호화해 보냄)과 **키 합의**(양쪽이 함께 계산)로 나뉜다.
- *전방 비밀성(forward secrecy)*: 장기 키(서버 개인키 등)가 **나중에** 유출돼도, 그 전에 녹음된 트래픽은 풀리지 않는 성질.
  - 흔한 오해: "TLS면 전방 비밀성이 있다" — TLS 1.2의 `TLS_RSA_…` 암호군과 TLS 1.3의 `psk_ke` 재개에는 없다(RFC 8446 §1.2, 부록 E.1. 예외: 일회용 PSK를 쓰자마자 지우는 경우 — §8.1, 아래 장애 3).

쉬운 예: 둘이 섞은 물감이다.
- 공용 노랑(공개 g)에 각자 비밀 색을 섞어 상대에게 보낸다.
- 받은 색에 자기 비밀 색을 한 번 더 섞으면 두 사람의 결과가 같다.
- 도청자는 섞인 두 색만 봤다. 섞인 물감을 다시 분리하기는 어렵다.
- 대화가 끝나면 비밀 색을 버린다. 나중에 누가 집을 뒤져도 그날의 색은 없다(전방 비밀성).

똑같은 구조다.\
"섞기 = 쉬운 방향, 분리 = 어려운 방향"이 이산 로그 문제다.

실무 예:
- 정보기관·공격자가 암호문을 지금 녹음해 두고, 몇 년 뒤 서버 개인키를 얻으면 푼다(record now, decrypt later). 정적 RSA 키 교환은 이 위협에 열려 있다.
- 2014년 Heartbleed(CVE-2014-0160)는 NVD 설명대로 프로세스 메모리에서 **개인키를 읽어 낸** 사례가 보고됐다. 정적 RSA를 쓰던 서버라면 녹음된 과거 트래픽도 위험해진다(해석).

## 동작·원리

### 1. Diffie-Hellman 교환

```text
  공개: 소수 p, 생성원 g                      (또는 곡선과 기준점 G)

  Alice                         도청자가 보는 것            Bob
  비밀 a 선택                                               비밀 b 선택
  A = g^a mod p   ──────── A ──────────>   A, B           B = g^b mod p
                  <─────── B ───────────
  K = B^a mod p                                            K = A^b mod p
    = g^(ab)                                                 = g^(ab)
                        도청자: A, B만으로 g^(ab)를 계산하기 어렵다고 본다 (계산 DH 문제)
                        이산 로그로 a·b를 구하면 풀리지만, 그 밖의 길이 없다는 증명은 없다
```

장난감 수치로 계산한 결과(실험, OpenJDK 21.0.12 `BigInteger.modPow`) — p=23, g=5, a=6, b=15:

```text
toy DH: A=g^a=8 B=g^b=19  alice B^a=2  bob A^b=2
```

- 둘 다 2를 얻었다. 도청자는 8과 19만 봤다.
- 실제로는 p가 2048비트 이상이거나(유한체 DH — TLS용 표준 그룹은 RFC 7919의 `ffdhe2048`·`ffdhe3072` 등), 타원곡선을 쓴다.

### 2. 타원곡선 DH — X25519

```text
  기준점 G (Curve25519의 u=9)
  Alice: 비밀 a (32바이트) → K_A = X25519(a, 9)       Bob: 비밀 b → K_B = X25519(b, 9)
  공유 K = X25519(a, K_B) = X25519(b, K_A)
```

- 지수 대신 점의 스칼라 곱을 쓴다([06 §4](../06-public-key-and-signatures/2-summary.md)). 공개값이 32바이트로 짧다.
- RFC 7748 §6.1 테스트 벡터를 Java로 재현했다(실험, OpenJDK 21.0.12, `KeyAgreement.getInstance("XDH")`).

```text
X25519 alice K = 4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742
X25519 bob   K = 4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742
RFC 7748 K     = 4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742  match=true
```

- RFC 7748 §6.1은 양쪽이 결과 K가 전부 0인지 확인하고 그러면 중단해도 된다고(MAY) 적는다. 작은 위수의 점을 입력으로 받으면 0이 나오기 때문이다.
- K를 바로 키로 쓰지 않는다. RFC 7748은 K·K_A·K_B를 넣은 키 유도 함수(KDF)로 대칭키를 만들라고 적는다. TLS 1.3은 HKDF를 쓴다.

### 3. 임시(ephemeral) 키가 전방 비밀성을 만든다

```text
  정적 RSA 키 전송 (TLS 1.2 TLS_RSA_*)            ECDHE (TLS 1.2 ECDHE_*, TLS 1.3)
  ┌ 녹음: Enc(서버RSA공개키, premaster)           ┌ 녹음: 임시 공개값 A, B (각 32바이트)
  │                                               │       + 서버 서명(인증용)
  └ 몇 년 뒤 서버 개인키 유출                     └ 몇 년 뒤 서버 개인키 유출
      → premaster 복호 → 세션 키 → 전부 복호          → 할 수 있는 것: 그 서명이 진짜였음을 확인
                                                       → 임시 개인키 a, b는 이미 지워짐 → 복호 불가
```

같은 상황을 Java로 흉내 냈다(실험, OpenJDK 21.0.12).

```text
static RSA: leaked long-term key recovers premaster = true
ECDHE: both sides equal = true, recorded = 2 public keys (32B each), long-term key not an input
```

- 정적 RSA: 녹음한 암호문 + 나중에 얻은 장기 개인키 = premaster 복구 성공.
- ECDHE: 장기 키는 공개값에 **서명**하는 데만 쓰인다(누구와 합의했는지 인증). 세션 키 계산의 입력이 아니다.
- *ECDHE*: Elliptic Curve Diffie-Hellman Ephemeral. 연결마다 새 키 쌍을 만들고 버린다.
- NIST SP 800-57 Part 1 Rev.5 표 1은 임시 키 합의 키의 수명을 "키 합의 한 번(One key-agreement transaction)"으로 적는다. 정적 키 합의 키는 1~2년이다.
- 전방 비밀성의 조건: RFC 8446 부록 E.1은 "장기 키가 핸드셰이크 뒤에 유출돼도, **세션 키 자체가 지워졌다면** 세션 키의 안전은 유지된다"고 적는다. 세션 키·임시 키를 메모리·디스크에 오래 남기면 성질이 약해진다.

### 4. 인증이 없는 DH는 중간자에 열려 있다

```text
  Alice ── A ──> Mallory ── M ──> Bob
  Alice <─ M' ── Mallory <─ B ─── Bob
  Alice는 Mallory와, Bob도 Mallory와 각각 키를 합의한다. 둘 다 눈치채지 못한다.
```

- DH 자체는 "누구와" 합의했는지 모른다. 그래서 공개값에 **서명**을 붙인다.
  - TLS 1.3: 인증서로 인증하는 핸드셰이크에서 서버가 `Certificate`까지의 기록 해시에 서명한다(`CertificateVerify`, RFC 8446 §4.4.3). PSK 재개는 서명 없이 PSK와 `Finished`로 인증한다. 키 합의(ECDHE) + 인증(서명)이 짝이다. 세부는 [network/29](../../network/29-tls-handshake/2-summary.md).
- 정리: 키 합의는 기밀성, 서명은 상대 확인. 둘 중 하나만으로는 부족하다.

### 5. TLS 버전별 키 교환 — 로컬에서 본 모습

로컬 `openssl s_server`(127.0.0.1, 자체 서명 인증서)에 `s_client`로 붙었다(실험, OpenSSL 3.0.13, 2026-10-07).

```text
== TLS1.2 static RSA kx
    Protocol  : TLSv1.2
New, TLSv1.2, Cipher is AES128-GCM-SHA256
== TLS1.2 ECDHE
    Protocol  : TLSv1.2
New, TLSv1.2, Cipher is ECDHE-RSA-AES128-GCM-SHA256
Server Temp Key: X25519, 253 bits
== TLS1.3
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Server Temp Key: X25519, 253 bits
```

- `AES128-GCM-SHA256`(OpenSSL 이름, IANA 이름 `TLS_RSA_WITH_AES_128_GCM_SHA256`)에는 `Server Temp Key` 줄이 없다 → 임시 키가 없다 → 전방 비밀성 없음.
- ECDHE와 TLS 1.3에는 `Server Temp Key: X25519`가 있다.
- TLS 1.3 암호군 이름(`TLS_AES_256_GCM_SHA384`)에는 키 교환이 안 보인다. 1.3은 키 교환을 `key_share`로 따로 정하고, 정적 RSA·DH 암호군을 제거했다(RFC 8446 §1.2: "Static RSA and Diffie-Hellman cipher suites have been removed; all public-key based key exchange mechanisms now provide forward secrecy").

## 쓰이는 자료구조·알고리즘

- **이산 로그 문제** — g^x mod p에서 x 찾기(유한체), Q = d·G에서 d 찾기(타원곡선). 키 합의의 안전 근거.
- **모듈러 거듭제곱 / 스칼라 곱** — A = g^a mod p는 제곱-곱셈, X25519는 Montgomery ladder(RFC 7748 §5). [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md).
- **키 유도 함수(HKDF)** — 공유 비밀을 균일한 대칭키 여러 개로 늘린다. HMAC 기반([원고 hmac](../../foundations/security/hmac.md)).
- **임시 상태의 수명 관리** — 키를 연결 단위 객체에 두고 끝나면 버린다. 세션 재개 티켓·캐시가 이 수명을 늘리는 지점이다.

## 적용 — 풀어나가는 법

### 1. 서버 설정 — 정적 RSA 키 교환을 끈다

```nginx
# nginx (예시) — TLS 1.2는 ECDHE 암호군만, 1.3은 기본 암호군
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;
```

- 취약 예: `ssl_ciphers HIGH:!aNULL` 같은 넓은 목록은 정적 RSA 암호군을 남긴다(OpenSSL 3.0.13에서 펼치면 `AES256-GCM-SHA384 ... Kx=RSA` 등이 나온다). 실제 목록은 `openssl ciphers -v '<문자열>'`로 펼쳐서 `Kx=RSA` 줄이 있는지 본다.

```bash
openssl ciphers -v 'HIGH:!aNULL' | awk '$3=="Kx=RSA"' | head -3     # 줄이 나오면 정적 RSA가 남아 있다
openssl ciphers -v 'ECDHE+AESGCM' | awk '$3=="Kx=RSA"'              # 고친 목록: 비어 있어야 한다
```

### 2. Java 21 — 키 합의를 직접 쓸 때

```java
KeyPair mine = KeyPairGenerator.getInstance("X25519").generateKeyPair();   // 연결마다 새로
// ... mine.getPublic()을 상대에게 보내고, 상대 공개키 peerPub를 받는다 (서명으로 인증된 값이어야 한다)
KeyAgreement ka = KeyAgreement.getInstance("XDH");
ka.init(mine.getPrivate());
ka.doPhase(peerPub, true);
byte[] shared = ka.generateSecret();           // 그대로 키로 쓰지 않는다
// HKDF(salt, shared, info="app v1 enc") 로 키 유도 → AES-GCM 키 (JDK 21에는 HKDF 공개 API가 없어 HMAC으로 구현하거나 라이브러리 사용)
```

- 직접 프로토콜을 만들기보다 TLS(또는 검증된 프로토콜: Noise·HPKE `[?]`)를 쓰는 것이 먼저다.

### 3. 진단 — 지금 연결이 전방 비밀성을 갖는가

```bash
# 로컬 또는 자기 서버에만
openssl s_client -connect 127.0.0.1:8443 -tls1_2 </dev/null 2>/dev/null | grep -E 'Cipher is|Server Temp Key'
```

- `Server Temp Key`가 있으면 임시 키 합의(ECDHE·DHE)다. 없으면 임시 키 합의가 아니다. 정적 RSA인지는 암호군으로 확인한다(`openssl ciphers -v`의 `Kx=RSA` — TLS 1.2에는 PSK·정적 DH 암호군도 있다, RFC 4279·RFC 5246 §7.4.2).
- Java 클라이언트 쪽은 `-Djavax.net.debug=ssl:handshake`로 협상 결과를 볼 수 있다 `[?]`(출력 형식은 JDK 판마다 다름).

## 장애 시나리오와 대처

### 1. 정적 RSA 키 교환 + 개인키 유출 → 과거 트래픽 전부 복호화 (⚠ 커리큘럼)

- **현상**: 서버 개인키가 유출된 사고 뒤, 이미 지나간 몇 달치 통신 내용까지 노출 범위에 들어간다.
- **보이는 형태**: 사고 조사에서 협상된 암호군이 `TLS_RSA_WITH_…`(OpenSSL 이름 `AES128-GCM-SHA256` 등). `s_client`에 `Server Temp Key` 줄 없음.
- **원인**: premaster가 장기 RSA 공개키로 암호화돼 전송됐다. 녹음 + 개인키 = 복호(위 Java 실험).
- **대처**
  - TLS 1.3 우선, 1.2는 ECDHE 암호군만 허용(적용 §1).
  - 유출 대응: 인증서 폐기·키 교체([network/31](../../network/31-revocation-ocsp-ct/2-summary.md)·[network/32](../../network/32-mtls-and-cert-operations/2-summary.md)). 정적 RSA를 쓰던 기간의 트래픽은 노출된 것으로 보고 영향 범위를 산정한다.

### 2. 다운그레이드 → 약한 키 교환으로 협상 (Logjam, CVE-2015-4000)

- **현상**: 서버가 옛 호환용 약한 암호군을 켜 둔 채 운영된다.
- **보이는 형태**: 스캐너 보고서에 export 등급 DHE·짧은 DH 그룹. 사고 원문 수준: NVD는 "서버에 DHE_EXPORT가 켜져 있으면(클라이언트는 아니어도) 중간자가 ClientHello의 DHE를 DHE_EXPORT로, ServerHello의 DHE_EXPORT를 DHE로 바꿔 써서 암호군을 낮출 수 있다"고 적는다.
- **원인**: 키 교환 그룹 크기가 작으면 이산 로그를 실제로 풀 수 있다. 협상 과정이 이를 막지 못했다.
- **대처**: export·짧은 DH 그룹 제거, ECDHE(X25519·P-256) 우선. TLS 1.3으로 협상된 연결에는 export 암호군이 없다. 다만 ServerHello random의 다운그레이드 표시(RFC 8446 §4.1.3)는 1.3을 지원하는 양 끝이 1.2 이하로 끌려 내려가는 것만 "제한적으로" 막고, 정적 RSA에서는 보호하지 못한다. 1.2를 허용한다면 export 암호군·짧은 DH 그룹은 따로 꺼야 한다(network/29 참고).

### 3. 세션 재개가 전방 비밀성을 깎는다

- **현상**: 전체 핸드셰이크는 ECDHE인데, 재개 연결에서는 전방 비밀성이 없다.
- **보이는 형태**: TLS 1.3 PSK 재개 모드가 `psk_ke`. 또는 세션 티켓 암호화 키가 오래(수 주~수 달) 회전되지 않는다 `[?]`(제품별 기본값 미확인).
- **원인**: RFC 8446 부록 E.1 — `psk_ke` 모드에서는 전방 비밀성이 만족되지 않는다. 재사용되거나 오래 남는 PSK·티켓 키가 사실상 새 장기 키가 된다(일회용 PSK를 바로 지우는 §8.1 방식은 예외).
- **대처**: 재개는 `psk_dhe_ke`(PSK + ECDHE). 티켓 키를 짧게 회전하거나, 티켓을 일회용 DB 키로 쓰고 사용 즉시 지운다(RFC 8446 §8.1 Single-Use Tickets: 그렇게 하면 PSK 연결도 전방 비밀성을 누린다).

### 4. 인증 없는 키 합의 → 중간자

- **현상**: 직접 만든 "암호화 채널"이 프록시 하나에 통째로 읽힌다.
- **보이는 형태**: 양 끝에서 계산한 공유 키의 지문(해시)을 비교하면 다르다.
- **원인**: 공개값에 서명·인증서 검증이 없었다(§4 그림). 또는 TLS 클라이언트에서 인증서 검증을 끈 코드(`TrustManager`가 전부 허용).
- **대처**: 공개값 서명 + 공개키 신뢰 근거(인증서 체인·고정 키). Java에서 "전부 신뢰" `TrustManager`를 쓰는 코드를 금지 규칙으로 잡는다([engineering-practice/15](../../engineering-practice/15-security-standards/2-summary.md)의 정적 분석).

## 핵심 문장

- 키 전송은 비밀을 암호화해 보내고, 키 합의(DH)는 공개값만 주고받아 양쪽이 같은 비밀을 계산한다.
- 전방 비밀성은 연결마다 만든 임시 키를 버려서 얻으며, 장기 키는 그 공개값에 서명(인증)하는 데만 쓰인다.
- 정적 RSA 키 교환은 녹음된 트래픽 + 나중에 유출된 개인키 = 전부 복호다. TLS 1.3은 그 암호군을 제거했다.
- DH만으로는 상대를 모른다. 키 합의(기밀성)와 서명(상대 확인)이 짝이다.
- 세션 재개(`psk_ke`, 오래 사는 티켓 키)와 지워지지 않은 세션 키는 전방 비밀성을 깎는다.

## 관련 주제·근거

- 선행
  - [06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md) — 타원곡선 스칼라 곱, 서명으로 공개값 인증
- 후속·연결
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md) — TLS 1.3 핸드셰이크·`key_share`·PSK 모드(TLS 본문 단일 출처)
  - [network/31-revocation-ocsp-ct](../../network/31-revocation-ocsp-ct/2-summary.md) · [network/32-mtls-and-cert-operations](../../network/32-mtls-and-cert-operations/2-summary.md) — 키 유출 뒤 폐기·교체
  - [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — 임시 키의 난수, 키 수명(cryptoperiod)
  - [security/03-symmetric-encryption-and-aead](../03-symmetric-encryption-and-aead/2-summary.md) — 합의한 키로 쓰는 AEAD
- 1차 출처
  - RFC 7748 Elliptic Curves for Security — §6.1 X25519 ECDH와 테스트 벡터, 전부 0 검사(MAY) <https://www.rfc-editor.org/rfc/rfc7748>
  - RFC 8446 TLS 1.3 — §1.2(정적 RSA·DH 제거, 공개키 기반 키 교환은 전방 비밀성), 부록 E.1(장기 키 기준 전방 비밀성, `psk_ke` 예외, 세션 키 삭제 조건) <https://www.rfc-editor.org/rfc/rfc8446>
  - RFC 5246 TLS 1.2 — §7.4.7.1 RSA 암호화 premaster <https://www.rfc-editor.org/rfc/rfc5246>
  - NIST SP 800-57 Part 1 Rev.5 — 표 1 cryptoperiod(임시 키 합의 키 = 키 합의 1회) <https://doi.org/10.6028/NIST.SP.800-57pt1r5>
  - NVD CVE-2015-4000(Logjam), CVE-2014-0160(Heartbleed) <https://nvd.nist.gov/vuln/detail/CVE-2015-4000> · <https://nvd.nist.gov/vuln/detail/CVE-2014-0160>
- 실험(2026-10-07)
  - OpenJDK 21.0.12(eclipse-temurin:21-jdk, `--network none`) `Kx.java`: 장난감 DH(p=23), RFC 7748 §6.1 X25519 벡터 일치, 정적 RSA-OAEP 키 전송의 사후 복호 vs X25519 임시 합의
  - OpenSSL 3.0.13 로컬 `s_server`/`s_client`(127.0.0.1 임의 포트, 자체 서명): TLS 1.2 `AES128-GCM-SHA256`(Temp Key 없음) vs `ECDHE-RSA-AES128-GCM-SHA256`·TLS 1.3(`Server Temp Key: X25519, 253 bits`)
