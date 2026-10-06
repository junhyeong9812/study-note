# security/04-hash-functions-and-digests — 암호 해시의 3성질, SHA-2, Merkle–Damgård와 길이 확장 — 정리 (힌트)

## 해결하는 문제

긴 데이터를 짧은 **지문**으로 대신하고 싶다. 내려받은 파일이 맞는지, 서명할 문서가 바뀌지 않았는지, 두 요청 본문이 같은지.

```text
  지문이 지켜야 할 약속                          약속이 깨지면
  "같은 지문의 다른 두 입력을 찾기 어렵다"        MD5·SHA-1 충돌 → 같은 지문의 다른 인증서·파일 (4절)
  "지문에 키를 섞으면 위조 방지가 된다"?          H(key‖msg)를 MAC으로 쓰면 길이 확장에 취약 (3절)
```

- 기초 개념(digest라는 말, 세 저항성, SHA-256 절차, 쓰임새)은 원본에 있다: [foundations/security/sha256-and-digest.md](../../foundations/security/sha256-and-digest.md) §1~§4.
- 이 노트는 원본 위에 **비용 차이 실험·장애(⚠)·적용·질문**을 채운다. 원본과 다르게 쓴 곳은 그 자리에 `참고:`로 밝힌다.

쉬운 예: 택배 상자의 봉인 번호다.
- 내용물 전체를 다시 확인하는 대신, 보낸 쪽이 알려 준 봉인 번호와 받은 상자의 번호만 대조한다.
- 같은 번호의 봉인을 두 개 만들 수 있으면(충돌), 바꿔치기한 상자도 통과한다.

똑같은 구조다.\
해시 함수가 "같은 번호의 봉인 두 개"를 못 만들게 하는 한에서만 지문은 원본을 대신한다.

## 동작·원리

### 1. 세 저항성 — 공격 비용이 다르다

```text
                 상대가 쥔 것          만들어야 하는 것              n비트 출력의 일반 공격 비용
  역상 저항        h                    H(m) = h 인 m                  약 2^n
  2차 역상 저항    고정된 m1            H(m2) = H(m1), m2 ≠ m1         약 2^n
  충돌 저항        (없음, 둘 다 자유)    H(a) = H(b), a ≠ b             약 2^(n/2)   ← 생일 경계
```

- 정의는 원본 §2. 여기서는 **비용의 차이**를 실험으로 본다.
- *생일 경계(birthday bound)*: 값 공간이 N개일 때 무작위로 뽑으면 약 √N개쯤에서 처음 겹친다. 기대값은 √(πN/2).
  - 그래서 SHA-256(256비트)의 충돌 저항은 약 2^128이고, 2차 역상 저항은 약 2^256이다(짧은 메시지 기준).
  - 2차 역상은 메시지가 길수록 비용이 낮아진다. NIST 예시: 2^33비트(1GiB) 메시지의 SHA-256은 232비트(SP 800-107 Rev.1 부록 A).

로컬 재현(실험 E4 [C]) — SHA-256 출력의 **앞 n비트만** 쓰는 장난감 해시로 시도 횟수를 셌다.

```text
  (실험, OpenJDK 21.0.12 eclipse-temurin, --network none, 2026-10-07)
  [C] 24비트 충돌: 4,372 / 2,728 / 5,916번째 시도      기대값 sqrt(pi/2*2^24)=5,134
  [C] 32비트 충돌: 155,228 / 97,509 / 73,722번째 시도  기대값 sqrt(pi/2*2^32)=82,137
  [C] 24비트 2차 역상: 53,366,145 / 2,955,733 / 8,778,725번째 시도 (19.6 / 1.1 / 3.2초)  기대값 2^24=16,777,216
```

- 같은 24비트에서 충돌은 수천 번, 2차 역상은 수백만~수천만 번이다. 2차 역상의 시도 수는 기하 분포라 표준편차가 평균만큼 크다. 충돌의 시도 수도 넓게 퍼진다(세 번만 돌렸다).
- 시도 횟수는 입력이 고정이라 재실행에서도 같았다. 걸린 시간은 환경 값이다(재실행 18.1 / 1.0 / 2.9초).
- 해석: 충돌 저항이 셋 중 **가장 먼저 깨지는** 이유가 이 비용 차이다. MD5·SHA-1도 충돌부터 무너졌다.
- 참고: 원본 §2는 역상 저항을 "비밀번호를 해시로 저장해도 되는 근거"로 든다. 비밀번호는 후보 공간이 작아서, 역상 저항이 있어도 후보를 차례로 해시해 대조하면 찾힌다. 비밀번호 저장에는 salt와 느린 KDF가 필요하다(원본 맨 끝 [Claude 추가]도 같은 점을 짚는다 — [security/08-password-storage-and-kdf](../08-password-storage-and-kdf/2-summary.md)).

### 2. 눈사태 효과 — 1비트가 출력 절반을 바꾼다

```text
  SHA-256("abc") = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad   ← FIPS 180-4 예제 값
  SHA-256("abb") = 715edf8ba8729420cd4d1ce85ed61954a9f531f8c548df728c407effe839296d   ('c'→'b' 1비트)
```

- 실험 E4 [B]: 무작위 64바이트 메시지 1000개에서 1비트씩 뒤집자 바뀐 출력 비트는 평균 127.4/256, 범위 103~153.
- 절반(128) 근처에 모인다. 해시끼리 비슷한지로 원본이 비슷한지 추정할 수 없다는 뜻이다.
- `openssl dgst`(OpenSSL 3.0.13)·`sha256sum`·Java `MessageDigest`가 같은 값을 냈다(실험 E4 [A]).

### 3. Merkle–Damgård와 길이 확장

```text
  M = 블록1 ‖ 블록2 ‖ ... ‖ 블록k ‖ [0x80 00..00 ‖ 64비트 길이]   ← 패딩(FIPS 180-4 §5.1.1)
        │         │                │
  IV ─▶[f]─▶ s1 ─▶[f]─▶ s2 ─ ... ─▶[f]─▶ sk ══ 출력 = 마지막 체인 상태 그대로
```

- SHA-256은 512비트 블록, 64라운드, 32비트 워드 8개 상태. SHA-512는 1024비트 블록, 80라운드. SHA-256 입력은 2^64비트 미만(FIPS 180-4 §1·§6). 절차는 원본 §3.
- **출력 = 마지막 체인 상태**다. 그래서 원본 §3이 설명하듯, `H(secret ‖ m)`을 아는 쪽은 secret 없이도 그 상태에서 블록을 더 처리한 값을 계산할 수 있다.
  - *길이 확장(length extension)*: 이 성질 때문에 `H(key ‖ msg)`를 MAC으로 쓰면 메시지 뒤에 덧붙인 값의 태그가 위조될 수 있다.
  - 대처는 MAC 전용 구성 HMAC이다(05번, RFC 2104).
- 이 성질이 없는 해시(구조에서 나오는 결론)
  - SHA-512/256·SHA-384: 출력이 내부 상태의 일부만이다.
  - SHA-3(FIPS 202): 스펀지 구조라 출력에 드러나지 않는 용량(capacity) 부분이 있다.
  - 그래도 키 있는 무결성에는 MAC 전용 구성(HMAC·KMAC)을 쓰는 것이 표준 관례다.

### 4. MD5·SHA-1이 무너진 기록 (공개 보고서 수준)

| 시점 | 사건 | 출처 |
|---|---|---|
| 2008-12-30 | MD5 충돌로 브라우저가 신뢰하는 위조 CA 인증서를 만들었다고 발표(25C3). PS3 200대 이상 사용. 악용 방지로 유효기간을 2004년 8월로 일부러 되돌려, 시계가 맞는 브라우저에선 만료로 거부된다 | Stevens 외 "MD5 considered harmful today" 페이지 |
| 2012-06-03 | Microsoft가 공격에 쓰인 무단 인증서를 이유로 중간 CA 신뢰 철회(보안 권고 2718704). MSRC는 Flame 악성코드가 MD5 충돌 공격을 썼다고 설명 | Microsoft 권고 2718704, MSRC 블로그(2012-06) |
| 2017-02-23 | SHAttered: 같은 SHA-1 값의 서로 다른 PDF 두 개 공개. "9,223,372,036,854,775,808"(약 9×10^18 = nine quintillion)회 넘는 SHA-1 계산, 단일 CPU 6,500년 + 단일 GPU 110년 상당. 생일 경계 무차별 대입보다 "100,000배" 빠름 | shattered.io 2017 보관본, Google 보안 블로그(2017-02-23) |
| 2020 | SHA-1 선택 접두 충돌. GnuPG 관련 CVE-2019-14855(2.2.18에서 수정) | sha-mbles.github.io, IACR ePrint 2020/014 |
| 2022-12-15 | NIST가 2030-12-31까지 모든 용도에서 SHA-1로 암호 보호를 하는 것을 퇴출한다고 발표. 그 전에 보호한 정보를 다룰 때는 이후에도 SHA-1이 필요할 수 있다고 함께 적음 | NIST CSRC 공지 |

- 참고: 원본 §3의 "약 9경(nine quintillion)"은 단위 환산 오류다. nine quintillion = 9×10^18 = **약 900경**이다(1경 = 10^16).
- 참고: 원본 §3의 "무차별 대입보다 수만 배 빠른"은 원문과 다르다. 2017년 shattered.io FAQ는 "100,000 faster than the brute force attack"(무차별 대입은 GPU 1,200만 년), Google 보안 블로그는 "more than 100,000 times faster"로 적는다 — **약 10만 배**다.
- 주의: 지금(2026-10) `shattered.io` 도메인은 연구팀 사이트가 아니라 다른 주체의 기사 사이트로 바뀌었고, "thousands of times faster" 같은 다른 문구가 실려 있다. 인용은 Wayback 보관본(2017·2025-01 판 모두 원래 FAQ)과 Google 블로그로 한다.

## 쓰이는 자료구조·알고리즘

- **Merkle–Damgård 구조**: 고정 크기 압축 함수 f를 체인으로 반복. 길이를 패딩에 넣어(MD 강화) 길이가 다른 입력이 같은 블록열이 되지 않게 한다.
- **스펀지 구조(SHA-3)**: 상태를 rate(입출력)·capacity(숨김)로 나눠 흡수 → 짜내기.
- **생일 문제 = 해시 집합으로 충돌 찾기**: 실험 [C]는 지금까지 본 값을 `HashMap`에 넣고 처음 겹칠 때 멈춘다. 메모리 O(√N)([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), 계산은 math 영역 `05-counting-and-birthday-bound` — 미작성([math 영역 표](../../math/README.md))).
- **머클 트리**: 블록별 해시를 트리로 묶어 부분 검증([data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)).
- 암호 해시 vs 비암호 해시(해시 테이블·SipHash)의 구분은 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).

## 적용 — 풀어나가는 법

### 1. Java 21 — 파일 digest와 비교

```java
// 스트리밍 digest — 큰 파일을 메모리에 다 올리지 않는다
static byte[] sha256(Path p) throws IOException, NoSuchAlgorithmException {
    MessageDigest md = MessageDigest.getInstance("SHA-256");
    try (InputStream in = new DigestInputStream(Files.newInputStream(p), md)) {
        in.transferTo(OutputStream.nullOutputStream());
    }
    return md.digest();
}

// 취약: 약한 해시로 무결성 판정 + 16진 문자열 대소문자 혼동
boolean ok = md5Hex(file).equals(expectedHex);             // MD5 = 충돌 가능(CWE-328)

// 고친 판: SHA-256, 바이트 비교
boolean ok2 = MessageDigest.isEqual(sha256(file), HexFormat.of().parseHex(expectedHex));
```

- 공개된 digest 비교(배포 파일 검증)는 비밀이 아니라 상수 시간이 필수는 아니다. **비밀이 걸린 비교(MAC 태그)**는 상수 시간이어야 한다(05번).
- digest 자체는 "누가 만들었나"를 증명하지 않는다. digest를 같은 서버에서 같이 받으면 둘 다 바꿔치기될 수 있다 — 서명(06번) 또는 별도 신뢰 경로가 필요하다.

### 2. 키가 있는 무결성은 HMAC으로

```java
// 취약: H(key ‖ msg)를 태그로 — 길이 확장에 취약
byte[] tag = MessageDigest.getInstance("SHA-256").digest(concat(key, msg));

// 고친 판: HMAC
Mac mac = Mac.getInstance("HmacSHA256");
mac.init(new SecretKeySpec(key, "HmacSHA256"));
byte[] tag2 = mac.doFinal(msg);
```

### 3. 진단 — digest 출력 읽기

```bash
printf abc | openssl dgst -sha256          # SHA2-256(stdin)= ba7816bf...
printf abc | openssl dgst -sha512-256      # SHA2-512/256(stdin)= 53048e26...
printf abc | openssl dgst -sha3-256        # SHA3-256(stdin)= 3a985da7...
sha256sum -c SHA256SUMS                    # 배포 파일 일괄 검증
```

- 컨테이너 이미지는 태그 대신 digest(`image@sha256:...`)로 고정한다(원본 §6).
- 코드에서 `MD5`·`SHA-1`을 검색해 용도별로 분류: 비보안 용도(캐시 키·중복 감지 힌트)는 남길 수 있으나, 서명·인증서·무결성 판정이면 교체.

## 장애 시나리오와 대처

### 1. MD5/SHA-1 충돌 → 위조 인증서·파일 ⚠

- **현상**: 정상 서명이 붙은 것처럼 보이는 인증서·문서·바이너리가 실제로는 다른 내용이다.
- **보이는 형태**: 서명 검증은 통과. 인증서 서명 알고리즘 필드에 `md5WithRSAEncryption`·`sha1WithRSAEncryption`. 같은 digest의 서로 다른 파일 두 개.
- **원인**: 서명이 digest에 걸리는데, digest 함수의 충돌 저항이 깨졌다. 공격자가 두 문서를 미리 같은 digest로 맞춰 하나에 정당한 서명을 받고 다른 하나와 바꾼다.
- **대처**: SHA-256 이상으로 교체, 약한 해시 서명을 검증 단계에서 거부. 인증서 쪽은 [network/30](../../network/30-x509-and-chain-validation/2-summary.md). Git이 2.13.0부터 SHA-1 충돌 시도 감지 구현(sha1dc, Stevens·Shumow)을 기본으로 쓰는 것처럼 과도기 방어도 있다(Git 2.13.0 릴리스 노트).

### 2. `H(key‖msg)`를 MAC으로 → 길이 확장 ⚠

- **현상**: 서명 검증을 통과한 요청에 원래 없던 파라미터가 붙어 있다.
- **보이는 형태**: 본문 중간에 `0x80`과 0 바이트들이 낀 요청, 그 뒤에 덧붙은 파라미터. 검증 로그는 "valid".
- **원인**: Merkle–Damgård 해시에 키를 앞에 붙여 MAC으로 썼다.
- **대처**: HMAC으로 교체(05번). 서명 대상의 파싱 규칙을 엄격히(중복 키·제어 바이트 거부).

### 3. digest 대조가 아무것도 증명 못 함

- **현상**: 배포 서버가 변조됐는데 체크섬 검증이 통과했다.
- **보이는 형태**: 파일과 `SHA256SUMS`가 같은 경로·같은 서버에서 제공된다.
- **원인**: digest는 무결성 "대조"일 뿐 출처 증명이 아니다. 공격자가 둘 다 바꿨다.
- **대처**: digest 파일에 서명(06번), 또는 다른 신뢰 경로(소스 저장소·패키지 관리자 lock 파일)에서 digest를 받는다([security/25-supply-chain-security](../25-supply-chain-security/2-summary.md)).

### 4. 비밀번호를 SHA-256으로 저장

- **현상**: DB 유출 후 대부분의 비밀번호가 빠르게 복원됐다.
- **보이는 형태**: `password_hash` 컬럼이 64자 16진수 하나(salt 없음), 같은 비밀번호는 같은 값.
- **원인**: 빠른 해시는 후보 대입이 빠르다. 역상 저항은 큰 무작위 입력을 전제로 한 성질이다.
- **대처**: salt + 느린 KDF(bcrypt·scrypt·Argon2), 다음 로그인 때 재해시([security/08-password-storage-and-kdf](../08-password-storage-and-kdf/2-summary.md)).

## 핵심 문장

- 암호 해시의 세 저항성 중 충돌 저항이 가장 싸게 깨진다. n비트 출력의 충돌 비용은 생일 경계 때문에 약 2^(n/2)이다.
- 1비트 입력 변화는 출력 비트의 약 절반을 바꾼다. 해시의 유사성으로 원본의 유사성을 추정할 수 없다.
- SHA-256처럼 출력이 마지막 체인 상태 그대로인 Merkle–Damgård 해시는 `H(key‖msg)`를 MAC으로 쓰면 안 된다. 키 있는 무결성은 HMAC이다.
- MD5·SHA-1은 충돌이 실증됐고 NIST는 2030년 말까지 암호 보호용 SHA-1 퇴출을 정했다.
- digest는 대조만 한다. 누가 만들었는지는 서명이나 별도 신뢰 경로가 증명한다.

## 관련 주제·근거

- 기초(원본, 읽기만): [foundations/security/sha256-and-digest.md](../../foundations/security/sha256-and-digest.md) §1 digest, §2 세 저항성, §3 SHA-256·SHA-1 퇴출, §4 쓰임새
- 선행: [03-symmetric-encryption-and-aead](../03-symmetric-encryption-and-aead/2-summary.md)
- 후속(같은 영역 — [영역 표](../README.md))
  - [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md) — 길이 확장을 막는 구성
  - [security/06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md) — 서명은 digest의 충돌 저항에 기댄다
  - [security/08-password-storage-and-kdf](../08-password-storage-and-kdf/2-summary.md) — 비밀번호에는 느린 KDF
- 연결: [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md), [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md), [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md), [network/30-x509-and-chain-validation](../../network/30-x509-and-chain-validation/2-summary.md)
- 1차 출처
  - NIST FIPS 180-4 (2015-08) — SHA-1/2 블록·라운드·입력 길이 상한, 패딩 §5.1.1 <https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf>
  - NIST FIPS 202 — SHA-3 스펀지 <https://csrc.nist.gov/pubs/fips/202/final>
  - SHAttered (2017-02-23) — 원래 FAQ의 보관본 <https://web.archive.org/web/20170301000000/https://shattered.io/> · Google 보안 블로그 "Announcing the first SHA1 collision" <https://security.googleblog.com/2017/02/announcing-first-sha1-collision.html> (현재 `shattered.io` 도메인은 다른 사이트)
  - Git 2.13.0 릴리스 노트 — 충돌 감지 SHA-1(sha1dc) 기본화 <https://github.com/git/git/blob/master/Documentation/RelNotes/2.13.0.adoc>
  - "MD5 considered harmful today" — 위조 CA(2008-12-30, 25C3) <https://marc-stevens.nl/research/hashclash/rogue-ca/>
  - Microsoft 보안 권고 2718704 (2012-06-03) <https://learn.microsoft.com/en-us/security-updates/securityadvisories/2012/2718704> · MSRC "Flame malware collision attack explained" <https://www.microsoft.com/en-us/msrc/blog/2012/06/flame-malware-collision-attack-explained>
  - SHA-1 is a Shambles (선택 접두 충돌, CVE-2019-14855) <https://sha-mbles.github.io/>
  - NIST SP 800-107 Rev.1 부록 A — 긴 메시지의 실제 2차 역상 강도(1GiB SHA-256 = 232비트) <https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-107r1.pdf>
  - NIST CSRC 공지 (2022-12-15) — 2030-12-31까지 암호 보호용 SHA-1 퇴출 <https://csrc.nist.gov/news/2022/nist-transitioning-away-from-sha-1-for-all-apps>
  - RFC 2104 HMAC <https://www.rfc-editor.org/rfc/rfc2104>
  - CWE-328 Use of Weak Hash <https://cwe.mitre.org/data/definitions/328.html>
- 실험
  - E4 `Hash.java` — [A] SHA-256·SHA-512/256·SHA3-256 출력, [B] 눈사태 1000회, [C] 잘린 해시 충돌 vs 2차 역상 시도 수. OpenJDK 21.0.12(eclipse-temurin:21-jdk), `--network none`, 2026-10-07.
  - 호스트 `openssl dgst -sha256/-sha512-256/-sha3-256`(OpenSSL 3.0.13), `sha256sum` — Java와 같은 값.
