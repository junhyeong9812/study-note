# security/03-symmetric-encryption-and-aead — 블록 암호, 운용 모드, AEAD(AES-GCM·ChaCha20-Poly1305) — 정리 (힌트)

## 해결하는 문제

DB 컬럼·파일·메시지를 **키가 있는 쪽만 읽게** 하고(기밀성), **중간에 바뀌면 알아채게**(무결성) 하고 싶다.

```text
  흔한 첫 구현                                       무엇이 잘못되나
  Cipher.getInstance("AES")  ← 모드를 안 적음          SunJCE 기본은 ECB → 같은 평문 블록 = 같은 암호문 블록
  고정 IV를 설정 파일에                                GCM이면 nonce 재사용 → 평문 XOR 노출 + 위조 가능
  CBC로 암호화만, 무결성 검사 없음                     IV(앞 암호문 블록) 비트를 뒤집으면 평문이 원하는 대로 바뀜
```

- 이 셋은 모두 "AES는 안전하다"는 사실과 무관하게 깨진다. 깨지는 곳은 **알고리즘이 아니라 사용법**(모드·nonce·인증)이다.
- 해법의 현재 표준: *AEAD*(Authenticated Encryption with Associated Data, 인증 암호화). 암호화와 위조 검사를 한 번에 하고, 검사에 실패하면 평문을 아예 돌려주지 않는다.
  - TLS 1.3은 AEAD 암호군만 쓴다([network/29](../../network/29-tls-handshake/2-summary.md)). 이 노트는 그 부품을 다룬다.

쉬운 예: 자물쇠 달린 상자 + 봉인 테이프다.
- 자물쇠(암호화)는 안을 못 보게 한다. 하지만 상자를 흔들거나 구멍을 내는 것은 못 막는다.
- 봉인 테이프(인증 태그)는 열었거나 손댔는지 보여 준다.
- AEAD는 둘이 한 몸인 상자다. 테이프가 찢겼으면 상자가 아예 안 열린다.

똑같은 구조다.\
단 이 상자는 **같은 열쇠로 같은 일련번호(nonce)를 두 번 쓰면** 테이프도 자물쇠도 같이 약해진다.

## 동작·원리

### 1. 블록 암호 — 16바이트를 16바이트로 섞는 키 있는 순열

```text
         키 K (128/192/256비트)
            │
  평문 블록 ─▶ [ AES ] ─▶ 암호문 블록      블록 = 128비트(16바이트) 고정
  16바이트                 16바이트          같은 K, 같은 입력 → 항상 같은 출력 (결정적)
```

- *블록 암호(block cipher)*: 고정 길이 블록을 키에 따라 다른 블록으로 바꾸는 함수. 키를 알면 역으로 되돌릴 수 있다.
- AES는 블록 128비트, 키 128·192·256비트다(FIPS 197).
- 블록 암호만으로는 16바이트밖에 못 다룬다. 긴 메시지를 어떻게 이어 붙이느냐가 *운용 모드(mode of operation)*다. 모드가 안전성을 좌우한다.

### 2. 운용 모드 네 가지

```text
  ECB  각 블록을 따로                 P1→[E]→C1   P2→[E]→C2   (P1=P2 이면 C1=C2)

  CBC  앞 암호문을 XOR 후 암호화       IV ─⊕─[E]─C1 ─⊕─[E]─C2
                                        P1      │   P2
                                                └──────┘ (체인)

  CTR  카운터를 암호화해 키스트림       E_K(N‖1)─⊕─C1  E_K(N‖2)─⊕─C2     ← 블록 암호를 스트림처럼
                                           P1             P2

  GCM  CTR 암호화 + GHASH 태그         CTR(N‖2부터)로 C 생성 → GHASH_H(AAD, C) ─⊕─ E(N‖1) = 태그 T
                                       H = E_K(0^128)  (해시 부분키)
                                       N‖1 = J₀는 96비트 nonce일 때. 다른 길이면 J₀ = GHASH_H(IV‖…)
```

- **ECB**(Electronic Codebook): 블록마다 독립이라 **같은 평문 블록이 같은 암호문 블록**이 된다. 패턴이 그대로 남는다.
- **CBC**(Cipher Block Chaining): 앞 암호문을 섞어 패턴을 지운다. IV는 예측 불가능해야 한다. 인증은 없다.
- **CTR**(Counter): `E_K(nonce‖카운터)`로 키스트림을 만들고 평문과 XOR. 블록 단위 병렬, 패딩 불필요. 인증 없음.
  - (nonce, 카운터)가 한 번이라도 겹치면 같은 키스트림 → 두 평문의 XOR이 드러난다.
- **GCM**(Galois/Counter Mode): CTR 암호화 + GF(2^128) 위의 다항식 해시 GHASH로 태그. NIST SP 800-38D(2007).

로컬 재현(실험 E3 [A]) — `"ATTACK AT DAWN!!"` 16바이트를 4번 반복한 평문, 교육용 고정 키:

```text
  (실험, OpenJDK 21.0.12 eclipse-temurin SunJCE, 2026-10-07)
  [A] ECB                                   [A'] GCM
    blk0 8a21cef935d8587bea999da471a91c41      blk0 c82d93f7c6bca140fe308dc90ab481c6
    blk1 8a21cef935d8587bea999da471a91c41      blk1 c75f6c6518a090e465c9523a2169ccf0
    blk2 8a21cef935d8587bea999da471a91c41      blk2 db7dcd41b15f3d3d996ff47dd4eaea1a
    blk3 8a21cef935d8587bea999da471a91c41      blk3 8dba5d1e3277f422b4820dda77a7a0c4
  [B] Cipher.getInstance("AES") == AES/ECB/PKCS5Padding ? true
```

- 호스트 `openssl enc -aes-128-ecb`(OpenSSL 3.0.13)로 같은 키·평문을 돌려도 첫 블록이 `8a21cef9 35d8587b ...`로 같았다.
- [B]: 모드를 안 적으면 SunJCE는 ECB를 고른다. Java `Cipher` 문서는 이를 "provider-specific default"라고만 적는다. **변환 문자열은 모드·패딩까지 전부 적는다.**

### 3. AEAD — 인터페이스와 보장

```text
  암호화  Seal(K, N, A, P) → C ‖ T          K 키, N nonce(유일), A 연관 데이터(암호화 안 함, 인증만), P 평문
  복호    Open(K, N, A, C ‖ T) → P  또는  ⊥ (실패 — 평문을 주지 않음)

          ┌──── 보호 범위 ────┐
          │ A(헤더·행 ID)  : 무결성만  │
          │ P → C          : 기밀성+무결성 │
          └────────────────┘
```

- *nonce*: "한 번만 쓰는 수". 같은 키에서 **유일**해야 한다. 비밀일 필요는 없고 보통 암호문 앞에 붙여 보낸다.
- *연관 데이터(AAD)*: 암호화하지 않지만 태그로 묶는 값. "이 암호문은 users 테이블 17번 행 것"처럼 문맥을 묶는다(실험 [G]).
- 두 표준 AEAD

| | AES-GCM | ChaCha20-Poly1305 |
|---|---|---|
| 정의 | NIST SP 800-38D | RFC 8439(7539 대체) |
| 키 | AES 128·192·256비트(TLS 1.3 암호군은 128·256) | 256비트 |
| nonce | 96비트 권장(800-38D §5.2.1.1) | 96비트 |
| 태그 | 128·120·112·104·96(특정 용도 64·32) | 128비트 |
| 강점 | AES-NI 같은 하드웨어 가속 | 소프트웨어만으로 빠름 |

- Java 21에서 둘 다 JDK 기본(`AES/GCM/NoPadding`, `ChaCha20-Poly1305`)이다(실험 E3).

### 4. GCM nonce 재사용 — 무엇이 깨지나

```text
  같은 K, 같은 N으로 두 메시지
    C1 = P1 ⊕ KS        KS = CTR 키스트림 (K, N에서만 결정)
    C2 = P2 ⊕ KS
    C1 ⊕ C2 = P1 ⊕ P2   ← 키를 몰라도 평문 XOR이 보인다. P2를 알면 P1이 나온다.

  게다가 두 기록(입력이 서로 다를 때)에서 GHASH 부분키 H를 알아낼 가능성이 높다
  → 같은 nonce로 임의 메시지의 유효 태그를 만든다(위조)
```

- SP 800-38D §8: 같은 키에서 IV가 **한 번이라도** 반복되면 위조 공격에 취약할 수 있고, 이 요구는 "실무에서 키의 비밀성에 **거의** 맞먹을 만큼 중요하다"(원문 "almost as important as the secrecy of the key").
- 부록 A: IV가 반복되면 공격자가 해시 부분키를 알아낼 가능성이 높고, 그러면 임의의 암호문·AAD에 유효한 태그를 만들 수 있어 "인증 보장이 사실상 사라진다".
- RFC 8439 §4: ChaCha20-Poly1305도 같은 키로 nonce를 반복하면 키스트림과 일회용 Poly1305 키가 같아져 평문 XOR이 드러난다.
- 로컬 재현(실험 E3 [C]):

```text
  [C] nonce 재사용: C1^C2 = 000000000000000000080909000000000c0d050f0a
                 P1^P2 = 000000000000000000080909000000000c0d050f0a  같음? true
      P2를 아는 쪽이 C1^C2^P2 로 얻은 P1 = "transfer 100 to alice"
```

- 라이브러리가 막아 주는 범위는 좁다.
  - 같은 `Cipher` 객체를 같은 IV로 다시 `init`하면 SunJCE가 거부한다: `InvalidAlgorithmParameterException: Cannot reuse iv for GCM encryption`(실험 [E]). ChaCha20-Poly1305도 `InvalidKeyException: Matching key and nonce from previous initialization`.
  - **새 객체**를 만들면 아무것도 막지 않는다(실험 [C]는 새 객체로 했다). 다른 프로세스·서버 사이의 재사용은 더더욱 모른다.
- nonce 생성 전략(SP 800-38D §8.2·§8.3)
  - 무작위 96비트: 한 키로 암호화 **2^32회 이하**. 넘기 전에 키를 바꾼다.
  - 결정적(고정 필드 + 카운터): 기기·인스턴스마다 다른 고정 필드, 카운터는 재시작 후에도 되돌아가면 안 된다.
  - 재사용 위험을 줄인 설계로 AES-GCM-SIV(RFC 8452)가 있다. 재사용 시 "같은 평문이었는지"만 드러난다(RFC 8452 §9, 같은 절의 사용량 한계 안에서).

### 5. 인증 없는 CBC — 가변성과 패딩 오라클

```text
  CBC 복호:  P1 = D_K(C1) ⊕ IV
  공격자가 IV의 i번째 바이트를 x만큼 XOR → P1의 i번째 바이트도 정확히 x만큼 바뀐다. 키 불필요.
```

- 로컬 재현(실험 E3 [F]): `"amount=100;to=bob"`을 CBC로 암호화한 뒤 IV 1바이트만 바꿨다.

```text
  [F] CBC IV 조작 후 복호 = "amount=900;to=bob" (예외 없음)
  [F'] GCM 같은 조작 -> Tag mismatch
```

- *가변성(malleability)*: 암호문을 바꾸면 평문이 예측 가능하게 바뀌는 성질. CTR·CBC 모두 그렇다(SP 800-38D 부록 A도 CTR의 이 성질을 GCM에 인증을 붙인 동기로 든다).
- *패딩 오라클(padding oracle)*: 서버가 복호 후 "패딩이 틀렸다"와 "그 밖의 오류"를 다르게 응답(에러 코드·메시지·시간)하면, 공격자는 암호문을 조금씩 바꿔 보내며 그 차이만으로 평문을 한 바이트씩 알아낸다. 원리는 Vaudenay(EUROCRYPT 2002). SSL 3.0의 POODLE(CVE-2014-3566)이 이 종류다.
- 대처는 인증이다: AEAD를 쓰거나, 꼭 CBC여야 하면 **암호화 후 MAC**(Encrypt-then-MAC)으로 MAC을 먼저 검사하고 실패하면 복호를 시작하지 않는다(05번).

## 쓰이는 자료구조·알고리즘

- **블록·카운터 모드.** CTR은 "카운터 → 블록 암호 → 키스트림"으로 블록 암호를 스트림 암호로 바꾼다. 블록끼리 독립이라 병렬화·임의 위치 복호가 된다. CBC는 앞 블록에 의존하는 체인이라 암호화가 순차적이다.
- **XOR의 성질.** `a⊕k⊕k = a`, `(a⊕k)⊕(b⊕k) = a⊕b`. 스트림 암호의 복호와 nonce 재사용 사고가 모두 이 한 줄에서 나온다([algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)).
- **GHASH = GF(2^128) 위 다항식 평가.** 블록 X1..Xm을 계수로 `((X1·H ⊕ X2)·H ⊕ ...)·H`, 호너 방법. H와 그 nonce로 만든 유효한 (암호문, 태그) 하나를 알면 `E_K(J₀) = T ⊕ GHASH`가 나와, 같은 nonce로 임의 메시지의 태그를 계산할 수 있다. 그래서 nonce 재사용이 위조로 이어진다(SP 800-38D §7.1·부록 A).
- **Poly1305 = 소수 2^130−5 위 다항식 평가.** 메시지마다 ChaCha20에서 일회용 키를 뽑는다(RFC 8439).
- **패딩(PKCS#7/PKCS5Padding).** 남은 칸 수 n을 값 n으로 n바이트 채운다. 블록 경계에 맞으면 한 블록을 통째로 더한다. 이 "검사 가능한 구조"가 패딩 오라클의 발판이다.
- 정보 이론 쪽 배경(완전 비밀성·엔트로피)은 [math 영역 14-information-theory-basics](../../math/14-information-theory-basics/2-summary.md).

## 적용 — 풀어나가는 법

### 1. Java 21 — 필드 암호화 기본형

```java
// 취약: 모드 미지정(ECB), 고정 IV, 인증 없음
Cipher c = Cipher.getInstance("AES");                       // SunJCE → AES/ECB/PKCS5Padding

// 고친 판: AES-256-GCM, 호출마다 새 nonce, 행 문맥을 AAD로 묶음
static final SecureRandom RNG = new SecureRandom();

static byte[] seal(SecretKey k, byte[] pt, byte[] aad) throws GeneralSecurityException {
    byte[] n = new byte[12]; RNG.nextBytes(n);              // 96비트 무작위 nonce (키당 2^32회 이하)
    Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
    c.init(Cipher.ENCRYPT_MODE, k, new GCMParameterSpec(128, n));
    c.updateAAD(aad);                                       // 예: "users:id=17"
    return ByteBuffer.allocate(12 + pt.length + 16).put(n).put(c.doFinal(pt)).array(); // nonce‖ct‖tag
}

static byte[] open(SecretKey k, byte[] blob, byte[] aad) throws GeneralSecurityException {
    Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
    c.init(Cipher.DECRYPT_MODE, k, new GCMParameterSpec(128, blob, 0, 12));
    c.updateAAD(aad);
    return c.doFinal(blob, 12, blob.length - 12);           // 실패 시 AEADBadTagException, 평문 없음
}
```

- 실험 E3 [G]·[H] — 같은 코드로 돌린 결과:

```text
  [G] 같은 행에서 복호 = memo: demo-secret
  [G] 암호문을 id=42 행으로 복사 -> Tag mismatch
  [H] 같은 평문 두 번 seal: 암호문 같음? false  길이 45 = 12+17+16
```

- AAD 덕분에 "다른 사람 행의 암호문을 내 행에 복사"하는 공격이 막힌다. 길이는 평문 + 28바이트(nonce 12 + 태그 16).
- 저장 형식에 **키 버전**도 앞에 붙인다(예: `v2:` + base64). 키 회전 때 어떤 키로 열지 알아야 한다(09번).
- 직접 조립 대신 고수준 라이브러리(Google Tink의 AEAD 등)를 쓰면 nonce 관리·형식을 맡길 수 있다.

### 2. 진단 — 예외와 도구 출력 읽기

| 보이는 것 | 뜻 |
|---|---|
| `javax.crypto.AEADBadTagException: Tag mismatch` | 암호문·태그·AAD·nonce·키 중 하나가 다르다. 변조 또는 설정 불일치 |
| `InvalidAlgorithmParameterException: Cannot reuse iv for GCM encryption` | 같은 Cipher 객체에서 IV 재사용 시도 — 코드가 고정 IV를 쓰고 있다는 신호 |
| `BadPaddingException`(CBC) | 키 불일치 또는 변조. 이 예외를 클라이언트에 다르게 보이면 패딩 오라클 |
| `openssl enc ... -aes-128-gcm` → `enc: AEAD ciphers not supported` | OpenSSL 3.0.13의 `enc` 명령은 AEAD를 안 다룬다. GCM 데이터 점검은 코드로 |

- 암호문 패턴 점검(ECB 의심): 저장된 암호문을 16바이트씩 잘라 중복 블록 수를 센다. 중복이 있으면 ECB나 IV·nonce 재사용을 의심한다(단서이지 확정 판정은 아니다).

```bash
# 진단 예: 파일의 16바이트 블록 중복 수
xxd -p -c 16 data.enc | sort | uniq -d | wc -l
```

### 3. nonce 재사용을 구조로 막는다

- 고정 IV를 설정값으로 두지 않는다(코드 리뷰에서 `new byte[12]`·상수 IV 검색).
- 여러 인스턴스가 같은 키를 쓰면 무작위 nonce + 키당 암호화 횟수 상한, 또는 인스턴스별 고정 필드.
- 키 사용량을 세고 상한 전에 회전한다(SP 800-38D §8.3).

## 장애 시나리오와 대처

### 1. ECB로 암호화된 데이터에서 패턴이 보인다 ⚠

- **현상**: 암호화한 컬럼인데 같은 값끼리 암호문이 같아 "누가 같은 비밀번호 힌트·같은 등급인지"가 드러난다. 이미지면 윤곽이 보인다.
- **보이는 형태**: `GROUP BY encrypted_col`에서 같은 암호문이 여러 행. 16바이트 블록 중복(위 `uniq -d`가 0보다 큼).
- **원인**: `Cipher.getInstance("AES")`처럼 모드 미지정(SunJCE 기본 ECB — 실험 [B]), 또는 ECB를 명시.
- **대처**: AEAD로 재암호화 마이그레이션(옛 키로 복호 → 새 형식으로 seal, 버전 접두로 구분). 정적 분석 규칙으로 `"AES"`·`/ECB/` 문자열을 막는다(CWE-327).

### 2. GCM nonce 재사용 → 평문 XOR 노출·인증 위조 ⚠

- **현상**: 외부 신고나 감사에서 "같은 nonce가 다른 메시지에 쓰였다"가 발견된다. 사용자에게 보이는 오류는 없다 — **조용한 실패**다.
- **보이는 형태**: 저장 데이터의 nonce 필드에 중복. 코드에 상수 IV, 재시작 때 0부터 다시 세는 카운터, 인스턴스마다 같은 시드.
- **원인**: nonce를 "IV니까 아무거나"로 다뤘다. 카운터를 메모리에만 두었다. 여러 인스턴스가 같은 키·같은 카운터 규칙.
- **대처**
  - 즉시: 영향받은 키를 폐기하고 새 키로 재암호화. 그 키로 만든 태그는 더 이상 무결성 증거가 아니다(H 노출 가능).
  - 재발 방지: 무작위 96비트 nonce + 키당 2^32회 상한 + 회전, 또는 오용 저항 AEAD(AES-GCM-SIV, RFC 8452). 저장 데이터의 nonce 중복 검사를 정기 배치로(CWE-323).

### 3. 인증 없는 CBC → 패딩 오라클 ⚠

- **현상**: 암호화된 쿠키·토큰을 쓰는 서비스에서 같은 출처의 요청이 짧은 시간에 수천 건, 응답 코드가 섞여 나온다.
- **보이는 형태**: 같은 엔드포인트에 `400 invalid padding`과 `400 invalid token`(또는 응답 시간 차이)이 구분돼 나온다. 요청마다 암호문의 한두 바이트만 다르다.
- **원인**: CBC 복호 후 패딩 오류를 다른 오류와 구분해 응답했다. 인증(MAC)이 없거나 복호 **뒤에** 검사했다.
- **대처**: AEAD로 교체. 당장은 모든 복호 실패를 같은 응답·같은 경로로(구분 불가능하게) 만들고, 남용 제한을 건다. CBC를 유지해야 하면 Encrypt-then-MAC으로 MAC 검사를 먼저(05번).

### 4. 배포 후 갑자기 전부 `AEADBadTagException`

- **현상**: 공격이 아닌데 기존 데이터가 하나도 안 열린다.
- **보이는 형태**: 로그에 `Tag mismatch`가 모든 행에서. 새로 저장한 데이터는 열린다.
- **원인**: AAD 구성이 바뀌었다(테이블명 변경, `id` → `uuid`), 키 버전 매핑이 틀렸다, 태그 길이 설정(`GCMParameterSpec` 첫 인자)이 바뀌었다.
- **대처**: AAD·태그 길이·키 ID를 저장 형식의 **버전 계약**으로 문서화하고, 형식 버전별로 여는 코드를 둔다. 배포 전 옛 데이터 샘플 복호 테스트.

## 핵심 문장

- 블록 암호는 16바이트 순열일 뿐이고, 안전성은 운용 모드·nonce·인증 사용법이 정한다.
- ECB는 같은 평문 블록을 같은 암호문 블록으로 만들어 패턴을 남긴다. Java에서 `"AES"`만 적으면 SunJCE는 ECB를 고른다.
- 암호화만으로는 무결성이 없다. CBC·CTR 암호문은 키 없이도 평문을 예측대로 바꾸게 한다.
- AEAD는 암호화와 위조 검사를 한 번에 하고, 검사에 실패하면 평문을 돌려주지 않는다. AAD로 암호문을 문맥에 묶는다.
- GCM·ChaCha20-Poly1305에서 같은 키로 nonce를 한 번이라도 반복하면 평문 XOR이 드러나고, GCM은 H가 드러날 가능성이 높아 인증 보장까지 사실상 잃는다(SP 800-38D 부록 A).
- 무작위 96비트 nonce면 한 키로 2^32회까지만 암호화하고 키를 바꾼다.

## 관련 주제·근거

- 선행: [01-security-principles](../01-security-principles/2-summary.md) — 기밀성·무결성. [math/14-information-theory-basics](../../math/14-information-theory-basics/2-summary.md)
- 후속(같은 영역 — [영역 표](../README.md))
  - [04-hash-functions-and-digests](../04-hash-functions-and-digests/2-summary.md), [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md) — 무결성 부품, Encrypt-then-MAC
  - [security/07-key-exchange-forward-secrecy](../07-key-exchange-forward-secrecy/2-summary.md) — 이 대칭 키를 어떻게 합의하나
  - [security/09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — nonce·키 생성, 키 회전·KMS
- 연결
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md) — TLS 1.3 AEAD 암호군 5개(TLS 본문은 network에만)
  - [network/43-compression-side-channels](../../network/43-compression-side-channels/2-summary.md) — 암호화해도 길이는 샌다
  - [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md) — XOR
- 1차 출처
  - NIST SP 800-38D (2007-11) — GCM. §5.2.1.1 96비트 IV 권장, §5.2.1.2 태그 길이, `len(P) ≤ 2^39−256`, §8 IV 유일성 요구(확률 2^−32 이하), §8.3 호출 수 2^32 상한, 부록 A 재사용 결과 <https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf>
  - RFC 8439 (2018) ChaCha20 and Poly1305 for IETF Protocols — 키 32·nonce 12·태그 16바이트, §4 nonce 유일성 <https://www.rfc-editor.org/rfc/rfc8439>
  - FIPS 197 Advanced Encryption Standard — 블록 128, 키 128/192/256 <https://csrc.nist.gov/pubs/fips/197/final>
  - NIST SP 800-38A — ECB·CBC·CTR 정의 <https://csrc.nist.gov/pubs/sp/800/38/a/final>
  - RFC 8452 AES-GCM-SIV — nonce 오용 저항 AEAD <https://www.rfc-editor.org/rfc/rfc8452>
  - S. Vaudenay, "Security Flaws Induced by CBC Padding", EUROCRYPT 2002 — 패딩 오라클 원리
  - CVE-2014-3566 (POODLE) — "SSL 3.0 ... nondeterministic CBC padding ... padding-oracle attack" <https://nvd.nist.gov/vuln/detail/CVE-2014-3566>
  - Java SE 21 `javax.crypto.Cipher` — 변환 문자열, 모드 미지정 시 provider 기본값, GCM IV 유일성 주의 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/javax/crypto/Cipher.html>
  - OSTEP 56 "Cryptography"(Peter Reiher) <https://pages.cs.wisc.edu/~remzi/OSTEP/>
  - CWE-323 Reusing a Nonce, Key Pair in Encryption · CWE-327 Use of a Broken or Risky Cryptographic Algorithm · CWE-649 Reliance on Obfuscation or Encryption of Security-Relevant Inputs without Integrity Checking <https://cwe.mitre.org/>
- 실험(모두 교육용 고정 키·가짜 평문, `--network none`)
  - E3 `Aead.java` — [A] ECB vs GCM 블록, [B] `"AES"` 기본 = ECB, [C] GCM nonce 재사용 XOR, [D] 1비트 변조 → `AEADBadTagException`, [E] 같은 객체 IV 재사용 거부, [F] CBC 가변성 vs GCM. OpenJDK 21.0.12(eclipse-temurin:21-jdk), 2026-10-07.
  - E3 `Cc.java` — ChaCha20-Poly1305 길이(평문+16), 같은 키·nonce 재초기화 거부. 같은 환경.
  - E3 `Aad.java` — 무작위 nonce + AAD로 행 묶기, 다른 행 복사 거부. 같은 환경.
  - 호스트 `openssl enc -aes-128-ecb`(OpenSSL 3.0.13) — Java ECB와 같은 첫 블록, `-aes-128-gcm`은 `AEAD ciphers not supported`.
