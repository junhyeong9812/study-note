# security/06-public-key-and-signatures — 공개키 암호와 전자서명: RSA·타원곡선·ECDSA·Ed25519 — 정리 (힌트)

## 해결하는 문제

대칭키 암호와 HMAC은 **양쪽이 같은 비밀키**를 미리 나눠 가져야 한다.

```text
  대칭키만 있을 때
  서버 1개 ── 비밀키 K ── 클라이언트 100만 개
  → K를 100만 곳에 나눠 줘야 한다. 한 곳에서 새면 누구나 "서버인 척" 서명(MAC)할 수 있다.
  → 검증하는 쪽도 K를 가지므로, 검증자가 곧 위조자가 될 수 있다.
```

- 해법: 키를 **둘로 쪼갠다.**
  - *개인키(private key)*: 주인만 가진다. 서명하거나 복호화한다.
  - *공개키(public key)*: 누구에게 줘도 된다. 서명을 검증하거나 암호화한다.
  - 공개키에서 개인키를 계산하는 것은 현실적인 시간 안에 안 된다(아래 "어려운 문제").
- *전자서명(digital signature)*: 개인키로 메시지에 붙이는 값이다. 공개키를 가진 누구나 "이 메시지를 그 개인키 주인이 서명했고, 서명 뒤 한 비트도 안 바뀌었다"를 확인한다.
  - 흔한 오해: "서명 = 개인키로 암호화"는 교과서 RSA에서만 비슷하다. ECDSA·Ed25519에는 그런 암호화 단계가 없다.

쉬운 예: 도장과 인감증명서다.
- 도장(개인키)은 본인만 가진다.
- 인감증명서(공개키)는 누구나 떼어 볼 수 있다. 서류의 도장 자국이 증명서와 맞는지 대조한다.
- 증명서를 가졌다고 도장을 새길 수는 없다.

똑같은 구조다.\
검증하는 쪽에 비밀이 없으니, 검증자가 많아도 위조 위험이 늘지 않는다.

실무 예:
- TLS 1.3 서버는 인증서로 인증할 때 `Certificate` 메시지까지의 핸드셰이크 기록 해시에 서명한다(`CertificateVerify`, RFC 8446 §4.4.3). 브라우저는 인증서의 공개키로 검증한다([network/29](../../network/29-tls-handshake/2-summary.md)).
- JWT를 인증 서버가 RS256·ES256·EdDSA로 서명하고, API 서버 수십 대는 공개키(JWKS)만 들고 검증한다([security/12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md), [security/13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md)).
- 배포 산출물·컨테이너 이미지·git 커밋에 서명해 "누가 만든 것인지"를 확인한다([security/25-supply-chain-security](../25-supply-chain-security/2-summary.md)).

## 동작·원리

### 1. 서명과 검증의 흐름

```text
  서명자 (개인키 d)                                   검증자 (공개키 Q)
  메시지 M ──> 해시 H(M) ──> Sign(d, H(M)) = σ
                                    │
                   M, σ  ──────────────────────────────> H(M') 계산
                                                         Verify(Q, H(M'), σ) → true / false
  M' = 받은 메시지. 한 비트라도 바뀌면 H(M') ≠ H(M) → false
```

그림 해설:

- 서명은 메시지 전체가 아니라 **해시**에 건다. 해시가 긴 메시지를 고정 길이로 줄인다. 해시의 충돌 저항성이 깨지면 서명도 깨진다(MD5·SHA-1 충돌 → 위조 인증서 사례는 [security/04-hash-functions-and-digests](../04-hash-functions-and-digests/2-summary.md), 기초는 [원고 sha256-and-digest](../../foundations/security/sha256-and-digest.md)).
  - Ed25519는 예외적으로 메시지를 내부에서 SHA-512로 두 번 처리한다(RFC 8032 §5.1.6). 호출자는 해시를 따로 하지 않는다.
- 검증 결과는 참/거짓 하나다. "검증했는데 거짓이면 거부"를 코드가 실제로 하는지가 장애 시나리오의 대부분이다.
- 서명이 주는 것: **무결성 + 출처 인증 + 부인 방지**(개인키는 주인만 가지므로 "내가 안 했다"고 하기 어렵다). 기밀성은 주지 않는다. 메시지는 평문 그대로 간다.
  - *부인 방지(non-repudiation)*: 서명자가 나중에 서명 사실을 부정하기 어렵게 하는 성질. HMAC은 양쪽이 같은 키를 가지므로 이 성질이 없다([security/05-mac-and-hmac](../05-mac-and-hmac/2-summary.md)).

실험으로 본 모습(실험, OpenJDK 21.0.12 temurin, 2026-10-07) — 메시지 `pay 100 to bob`의 `1`(0x31)을 `9`(0x39)로, 즉 1비트만 바꿨다.

```text
m2 = pay 900 to bob
Ed25519 sig len=64, same msg twice equal=true, verify(m)=true, verify(m2)=false
ECDSA P-256 sig len=70/71, same msg twice equal=false, verify(m)=true, verify(m2)=false
RSA-3072 PSS sig len=384, verify(m)=true, verify(m2)=false
Ed25519 verifier + RSA key -> InvalidKeyException
```

- 세 방식 모두 1비트 변경을 거부했다.
- 서명 길이가 다르다. Ed25519 64바이트 고정, ECDSA P-256은 DER 인코딩이라 흔히 70~72바이트로 흔들린다(r·s의 앞자리가 작으면 더 짧을 수도 있다), RSA-3072은 384바이트(모듈러스 크기).
- 같은 메시지를 두 번 서명하면 Ed25519는 같은 값, ECDSA는 다른 값이 나왔다. 이 차이가 아래 §4의 핵심이다.

### 2. 어려운 문제 — 왜 공개키에서 개인키가 안 나오나

```text
  쉬운 방향 (빠름)                     어려운 방향 (현실적으로 불가)
  RSA : p, q 소수 → n = p·q             n → p, q 찾기 (소인수분해)
  DH  : g, x → g^x mod p                g^x mod p → x 찾기 (이산 로그)
  ECC : G, d → Q = d·G (점을 d번 더함)   Q → d 찾기 (타원곡선 이산 로그)
```

- *일방향 함수(one-way function)*: 한 방향 계산은 빠르고 반대 방향은 알려진 방법으로 너무 오래 걸리는 함수.
- 같은 안전 수준에서 키 크기가 다르다. NIST SP 800-57 Part 1 Rev.5 표 2:

| 보안 강도 | 대칭키 | RSA(모듈러스 k) | ECC(기준점 위수 n의 비트 길이 f) |
|---|---|---|---|
| 112비트 | (3TDEA) | 2048 | 224~255 |
| 128비트 | AES-128 | 3072 | 256~383 |

- 그래서 P-256(f=256)은 128비트 강도, RSA-2048은 112비트 강도로 분류된다.
- Ed25519·X25519는 체(field)가 255비트지만, 표의 f는 기준점 위수의 비트 길이다(SP 800-57 표 2 설명 5). 위수가 2^252 + …(RFC 7748 §4.1)라 f=253이고, 표의 224~255 = 112행에 들어간다. 다만 RFC 7748·8032는 "약 128비트 수준"을 목표로 한다고 적고, RFC 7748 §7은 "표준 128비트보다 약간 아래지만 받아들일 만하다"고 설명한다.

### 3. RSA — 모듈러 거듭제곱

```text
  키 생성:  소수 p, q → n = p·q,  φ = (p-1)(q-1)
            공개 지수 e (보통 65537),  개인 지수 d = e⁻¹ mod φ
  서명(교과서):  σ = h^d mod n          검증: σ^e mod n == h ?
  암호화(교과서): c = m^e mod n          복호: c^d mod n = m
```

장난감 수치로 계산한 결과(실험, OpenJDK 21.0.12, `BigInteger.modPow`/`modInverse`) — p=61, q=53, e=17:

```text
toy RSA n=3233 phi=3120 d=2753 sig=h^d mod n=588, sig^e mod n=65
```

- h=65에 d로 거듭제곱한 서명 588을 e로 거듭제곱하면 65로 돌아온다.
- **교과서 RSA를 그대로 쓰면 안 된다.** 패딩이 없으면 곱셈 성질(σ(a)·σ(b) = σ(a·b))로 위조가 생긴다. 실제로는 패딩 규격을 쓴다.
  - RFC 8017(PKCS #1 v2.2) §8: 서명은 RSASSA-PSS와 RSASSA-PKCS1-v1_5 두 가지다. "RSASSA-PKCS1-v1_5에 대해 알려진 공격은 없지만, 견고성을 위해 새 응용에서는 RSASSA-PSS가 REQUIRED"라고 적는다.
  - 암호화는 RFC 8017 §7: 새 응용은 RSAES-OAEP를 지원해야 하고(REQUIRED), RSAES-PKCS1-v1_5는 호환용이다. §7.2는 PKCS1-v1_5를 쓴다면 Bleichenbacher의 선택 암호문 공격(패딩 오라클)을 막는 조치를 취하라고(should) 적는다.
- 큰 수의 거듭제곱은 **제곱-곱셈(이진 거듭제곱)** 으로 지수의 비트 수만큼만 곱한다. [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md) 참고.

### 4. 타원곡선 — 점 덧셈과 스칼라 곱

```text
  y² = x³ + ax + b  (mod p) 위의 점들 + "무한원점 O"  → 덧셈이 정의된 군(group)

        P + Q : P와 Q를 잇는 직선이 곡선과 만나는 세 번째 점을 x축 대칭
        2P    : P의 접선으로 같은 작업
        d·G   : G를 d번 더함 → 2배·더하기(double-and-add)로 log₂d 단계
```

- 장난감 곡선 y² = x³ + 2x + 2 (mod 17), G = (5, 1)로 계산했다(실험, 호스트 Python 3.12.3).

```text
1G=(5, 1) 2G=(6, 3) 3G=(10, 6) 4G=(3, 1) ... 13G=(16, 4) ... 18G=(5, 16) 19G=None 20G=(5, 1)
13G via double-and-add = (16, 4)
```

- 19번 더하면 무한원점(None)이 되고 다시 G로 돌아온다. 이 19가 G의 *위수(order) n* 이다. 개인키 d는 1..n-1 사이 수, 공개키는 Q = d·G다.
- 실제 곡선은 p가 약 2^256이라 Q에서 d를 거꾸로 찾을 수 없다.
- 표준 곡선: P-256(secp256r1, NIST), Curve25519/Edwards25519(RFC 7748·8032).

### 5. ECDSA와 Ed25519 — 서명마다 쓰는 비밀 난수 k

```text
  ECDSA 서명 (곡선 위수 n, 개인키 d, 해시 z)
    1. 비밀 난수 k 선택            ← 서명마다 새로, 예측 불가해야 함
    2. r = (k·G).x mod n
    3. s = k⁻¹ (z + r·d) mod n      서명 = (r, s)

  k를 두 메시지에 재사용하면 r이 같아진다
    s₁ - s₂ = k⁻¹ (z₁ - z₂)  →  k = (z₁ - z₂)/(s₁ - s₂)  →  d = (s₁·k - z₁)/r
    → 공개된 서명 두 개만으로 개인키가 계산된다
```

- RFC 6979 §1: "DSA·ECDSA는 서명마다 새 난수 k가 필요하다. k는 암호학적으로 안전한 과정으로 균일하게 골라야 한다. 아주 작은 편향도 공격으로 바뀔 수 있다."
- 실제 사고(공개 발표 수준): 2010년 12월 27C3에서 fail0verflow가 PS3의 코드 서명 ECDSA가 서명마다 **같은 k**를 썼다고 발표했고, Sony 서명 개인키가 계산됐다(2차 보도: SiliconANGLE 2011-01-03 등. 발표 원문 미열람).
- 2008년 Debian OpenSSL 난수 결함(CVE-2008-0166) 공지 DSA-1571도 "영향받은 Debian 시스템에서 서명·인증에 **사용된** DSA 키는 전부 손상된 것으로 봐야 한다. DSA는 서명 생성 중 비밀 난수를 쓰기 때문"이라고 적었다. 다른 곳에서 만든 키라도 나쁜 난수로 서명하면 샌다([09](../09-randomness-and-key-management/2-summary.md)).
- 대책은 둘이다.
  - **결정적 k**: RFC 6979는 k를 HMAC_DRBG(개인키, 메시지 해시)로 유도한다. 같은 (개인키, 메시지 해시) → 같은 k, 해시가 다르면 사실상 다른 k(HMAC 출력이 겹칠 확률은 무시할 만큼 작다).
  - **Ed25519**: RFC 8032 §5.1.6이 처음부터 r = SHA-512(prefix ‖ M)로 정한다(prefix는 개인키 해시의 뒷절반). 그래서 위 실험에서 같은 메시지의 서명이 같았다.
- JDK 21의 `SHA256withECDSA`는 위 실험에서 같은 메시지에 다른 서명을 냈다 → 난수 k를 쓴다. 그 k의 품질은 `SecureRandom`에 기댄다.

### 6. 공개키 암호의 범위 — 이 노트와 다른 노트의 경계

```text
  공개키 쓰임          이 노트        다른 노트
  서명/검증            여기           JWT 서명(12), JWKS(13), 공급망 서명(25)
  키 합의 (DH/ECDH)    —              07
  키 전송 (RSA 암호화)  원리만         07 (전방 비밀성 문제)
  "이 공개키가 진짜 그 서버 것인가"  —  network/30 (X.509 인증서 체인)
```

- 서명은 "이 공개키의 주인이 서명했다"까지만 증명한다. **그 공개키가 누구 것인지**는 별도 신뢰 모델(인증서·JWKS 엔드포인트·키 고정)이 정한다. TLS의 인증서 체인은 [network/30](../../network/30-x509-and-chain-validation/2-summary.md)이 단일 출처다.

## 쓰이는 자료구조·알고리즘

- **모듈러 거듭제곱(제곱-곱셈)**, **확장 유클리드로 역원** — RSA의 d = e⁻¹ mod φ, 서명·검증의 h^d·σ^e. [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md). 수학 배경은 math/11-modular-arithmetic(미작성, [math/README](../../math/README.md)).
- **타원곡선 군 연산** — 점 덧셈, 2배, 스칼라 곱(double-and-add). 이진 거듭제곱과 같은 구조를 곱셈 대신 점 덧셈으로 한다.
- **암호 해시** — 서명 전 메시지 축약(SHA-256), Ed25519 내부 SHA-512, RFC 6979의 HMAC_DRBG. [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md), [원고 hmac](../../foundations/security/hmac.md).
- **DER(ASN.1) 인코딩** — ECDSA 서명 (r, s)를 정수 두 개로 감싼다. 정수를 최소 바이트로 적고 앞자리 0 바이트를 붙이기도 해서 길이가 흔히 70~72바이트로 흔들린다(실험 출력, 그보다 짧은 서명도 가능).

## 적용 — 풀어나가는 법

### 1. 알고리즘 고르기

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 새 시스템, 상대가 지원 | Ed25519 | 결정적 서명(k 실수 없음), 64바이트, 빠름 |
| FIPS·레거시 호환 | ECDSA P-256 + SHA-256 | 넓은 지원. 구현이 RFC 6979 또는 검증된 CSPRNG를 쓰는지 확인 |
| RSA가 필요한 생태계 | RSA-3072 이상 + PSS (호환 필요 시 PKCS1-v1_5) | SP 800-57 표 2 기준 128비트 강도 |

- 키 크기는 판단 근거(표준·조직 정책)를 적어 둔다. "2048이면 충분"은 112비트 강도 기준이다.

### 2. 취약 예 → 고친 예: 검증 알고리즘을 메시지가 고르게 두지 않는다

```java
// 취약: 메시지(토큰 헤더 등)가 알려 준 알고리즘 이름으로 검증한다
boolean verifyBad(String algFromMessage, PublicKey key, byte[] msg, byte[] sig) throws Exception {
    Signature v = Signature.getInstance(algFromMessage);   // 공격자가 고른 알고리즘
    v.initVerify(key); v.update(msg);
    return v.verify(sig);
}

// 고침: 키마다 허용 알고리즘을 미리 고정한다. 메시지의 alg는 "일치 확인"에만 쓴다
record TrustedKey(String kid, PublicKey key, String alg) {}

boolean verify(TrustedKey k, String algFromMessage, byte[] msg, byte[] sig) throws Exception {
    if (!k.alg().equals(algFromMessage)) return false;      // 불일치 = 거부
    Signature v = Signature.getInstance(k.alg());            // 예: "Ed25519"
    v.initVerify(k.key()); v.update(msg);
    return v.verify(sig);
}
```

- JDK는 키와 알고리즘이 안 맞으면 막아 준다(실험: Ed25519 검증기 + RSA 키 → `InvalidKeyException`).
- 그러나 JWT의 "HS256 + RSA 공개키를 HMAC 비밀로" 같은 혼동은 **라이브러리가 바이트열을 그대로 키로 받을 때** 생긴다. 키 객체에 알고리즘을 묶어 두는 것이 방어선이다([security/12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md)).

### 3. Java 21 기본 사용 — JDK만으로

```java
KeyPair kp = KeyPairGenerator.getInstance("Ed25519").generateKeyPair();

Signature s = Signature.getInstance("Ed25519");
s.initSign(kp.getPrivate());
s.update(message);
byte[] sig = s.sign();                                     // 64바이트

Signature v = Signature.getInstance("Ed25519");
v.initVerify(kp.getPublic());
v.update(message);
if (!v.verify(sig)) throw new SecurityException("bad signature");   // false를 무시하지 않는다
```

- `verify`가 `false`를 돌려주면 예외를 던지는 쪽으로 감싼다. 반환값을 버리는 코드가 "서명 검증 생략" 버그의 흔한 모양이다.

### 4. `openssl`로 진단하기 (로컬 파일)

```bash
openssl genpkey -algorithm ed25519 -out ed.key
openssl pkey -in ed.key -pubout -out ed.pub
openssl pkeyutl -sign   -inkey ed.key -rawin -in msg.txt -out sig.bin
openssl pkeyutl -verify -pubin -inkey ed.pub -rawin -in msg.txt -sigfile sig.bin
```

실험 출력(실험, OpenSSL 3.0.13, 2026-10-07):

```text
ed25519 same msg -> identical sig
64 sig1.bin
Signature Verified Successfully
Signature Verification Failure        ← 1비트 바꾼 msg2.txt, 종료 코드 1
ecdsa same msg -> different sig
 72 e1.bin
 71 e2.bin
Verified OK
Verification failure                  ← ECDSA도 1비트 변경 거부
```

- 셸 스크립트에서는 출력 문구가 아니라 **종료 코드**로 판정한다(`Verification failure` 때 종료 코드 1).

## 장애 시나리오와 대처

### 1. 서명 검증 생략 → 위조 데이터가 통과 (⚠ 커리큘럼)

- **현상**: 웹훅·토큰·업데이트 파일이 위조돼도 처리된다. 평소에는 아무 증상이 없다.
- **보이는 형태**: 테스트에 "잘못된 서명"이 없어서 CI는 초록. 사고 뒤 로그에 서명 검증 실패 로그가 한 줄도 없다.
- **원인**: `verify()`의 반환값을 무시, "개발 중 임시로" 끈 검증 플래그가 운영에 남음, 검증 예외를 잡아 삼킨 뒤 계속 진행(fail-open).
- **대처**: 검증 실패 = 예외로 감싼다. "잘못된 서명은 거부된다"는 음성 테스트를 둔다(1비트 바꾼 메시지 — 위 실험 형태). 검증 실패 횟수를 지표로 남긴다.

### 2. 알고리즘 혼동 → 공격자가 고른 알고리즘으로 통과 (⚠ 커리큘럼)

- **현상**: 공개키만 아는 공격자가 만든 토큰이 통과한다.
- **보이는 형태**: 토큰 헤더 `alg`가 평소(RS256·EdDSA)와 다른 값(HS256·none)인데 200 응답.
- **원인**: 검증 알고리즘을 메시지가 고르게 했다. RSA 공개키 바이트를 HMAC 키로 쓰면 공개키를 아는 누구나 "서명"을 만든다.
- **대처**: 키마다 알고리즘 고정(적용 §2), 허용 목록 밖 `alg` 거부. 세부는 [security/12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md).

### 3. ECDSA 난수 k 재사용·편향 → 개인키 유출 (⚠ 커리큘럼, PS3 2010)

- **현상**: 공개된 서명들만으로 제3자가 개인키를 계산해 임의 서명을 만든다. 서명 키 교체 외에는 복구 수단이 없다.
- **보이는 형태**: 같은 키의 서명들 중 `r` 값이 같은 쌍이 있다(같은 k 또는 n−k가 쓰였다는 강한 신호 — k·G와 −k·G는 x좌표가 같고, 둘 다 개인키 계산으로 이어진다). 진단으로 서명 로그에서 `r` 중복을 검사할 수 있다.
- **원인**: 고정 k(PS3), 시드가 약한 난수(Debian 2008), 가상 머신 스냅샷 복제로 같은 난수 상태 재사용 `[?]`(원리상 가능, 공개 사고 원문 미확인).
- **대처**: Ed25519 또는 RFC 6979 결정적 ECDSA를 쓰는 구현을 고른다. 키가 샌 것으로 보이면 즉시 회전하고, 그 키로 서명된 것을 다시 서명·폐기한다([security/13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md)).

### 4. 키 크기·알고리즘 정책 위반 → 클라이언트가 연결·검증 거부

- **현상**: 특정 클라이언트(최신 JDK·브라우저·FIPS 모드)만 서명 검증이나 TLS가 실패한다.
- **보이는 형태**: Java `java.security.cert.CertPathValidatorException: Algorithm constraints check failed`, OpenSSL `ee key too small` 류 `[?]`(정확한 문구는 판마다 다름).
- **원인**: RSA-1024·SHA-1 서명 같은 낡은 조합. 런타임의 보안 정책(JDK `jdk.certpath.disabledAlgorithms` 등)이 판마다 강해진다.
- **대처**: 서명 알고리즘·키 크기를 인벤토리로 관리하고 만료 전에 교체한다. 기준은 SP 800-57 표 2와 조직 정책.

## 핵심 문장

- 공개키 암호는 키를 개인키·공개키로 쪼개, 검증하는 쪽에 비밀이 없게 만든다.
- 서명은 무결성·출처·부인 방지를 주지만 기밀성은 주지 않고, "그 공개키가 누구 것인가"는 인증서·JWKS 같은 별도 신뢰 모델이 정한다.
- RSA는 모듈러 거듭제곱, ECC는 점의 스칼라 곱이고, 같은 128비트 강도에서 RSA-3072 대 256비트 곡선이다.
- ECDSA는 서명마다 비밀 난수 k가 필요하고, k를 재사용·편향하면 공개된 서명만으로 개인키가 나온다 — Ed25519와 RFC 6979는 k를 결정적으로 만든다.
- 검증 알고리즘은 키에 묶어 두고, 메시지가 고르게 하지 않는다.

## 관련 주제·근거

- 선행
  - [security/04-hash-functions-and-digests](../04-hash-functions-and-digests/2-summary.md) — 서명 전 해시, 충돌 저항성(기초: [원고 sha256-and-digest](../../foundations/security/sha256-and-digest.md))
  - math/11-modular-arithmetic(미작성, [math/README](../../math/README.md)) · [algorithm/28-number-theory](../../algorithm/28-number-theory/2-summary.md) — 모듈러 거듭제곱·역원
- 후속·연결
  - [07-key-exchange-forward-secrecy](../07-key-exchange-forward-secrecy/2-summary.md) — 공개키로 키를 합의하기
  - [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — k와 키 생성의 난수, 키 수명
  - [security/12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md) · [security/13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md) — 서명된 토큰과 공개키 배포
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md) · [network/30-x509-and-chain-validation](../../network/30-x509-and-chain-validation/2-summary.md) — TLS 안의 서명과 인증서 체인(TLS/PKI 단일 출처)
- 1차 출처
  - RFC 8017 PKCS #1 v2.2 — §7.1 RSAES-OAEP, §8 서명 방식(PSS REQUIRED in new applications) <https://www.rfc-editor.org/rfc/rfc8017>
  - RFC 8032 EdDSA — §5.1.6 Sign(r = SHA-512(dom2 ‖ prefix ‖ PH(M))) <https://www.rfc-editor.org/rfc/rfc8032>
  - RFC 6979 Deterministic DSA and ECDSA — §1 k의 요구, §3.2 k 생성 <https://www.rfc-editor.org/rfc/rfc6979>
  - RFC 7748 Elliptic Curves for Security(Curve25519) <https://www.rfc-editor.org/rfc/rfc7748>
  - NIST SP 800-57 Part 1 Rev.5 — 표 2 보안 강도 비교 <https://doi.org/10.6028/NIST.SP.800-57pt1r5>
  - Debian DSA-1571-1(2008-05-13), CVE-2008-0166 <https://lists.debian.org/debian-security-announce/2008/msg00152.html>
  - OSTEP 56(커리큘럼 표기, 본문 미대조 `[?]`)
  - PS3 ECDSA: fail0verflow 27C3 발표(2010-12) — 2차 보도 <https://siliconangle.com/2011/01/03/cryptography-fail-for-sony-playstation-3/>
- 실험(2026-10-07)
  - OpenJDK 21.0.12(eclipse-temurin:21-jdk, `--network none`) `Sig.java`: Ed25519·ECDSA P-256·RSA-3072 PSS 서명/검증, 1비트 변경 거부, 결정성 비교, 키-알고리즘 불일치 예외, 장난감 RSA
  - OpenSSL 3.0.13 `pkeyutl`·`dgst`: Ed25519·ECDSA 서명 결정성, 1비트 변경 시 `Verification failure`(종료 코드 1)
  - Python 3.12.3 `toyec.py`: y² = x³+2x+2 mod 17 점 덧셈·double-and-add·위수 19
