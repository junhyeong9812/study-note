# security/10-authentication-basics — 인증 요소, MFA·TOTP·WebAuthn — 정리 (힌트)

## 해결하는 문제

서버는 요청을 보낸 "사람"을 볼 수 없다. 보이는 것은 네트워크로 온 바이트뿐이다.

```text
  사람(주체)  ──조작──>  브라우저·앱(대리자)  ──요청 바이트──>  서버(검증자)
                                                  "이 바이트를 보낸 쪽이 alice라는 증거는?"
```

- *인증(authentication)*: 요청한 쪽이 주장하는 신원이 맞는지 확인하는 일.
  - 흔한 오해: 인증과 인가는 같은 일이다 → 인가(authorization)는 "그 신원이 이것을 해도 되나"다. 인가는 [15-access-control-models](../15-access-control-models/2-summary.md)에서 다룬다.
- *주체(principal)*: 권한을 요청할 수 있는 보안상의 실체(사람, 그룹, 서비스). OSTEP 54장의 용어다.
- *자격 증명(credential)*: 주체가 내미는 증거(비밀번호, OTP, 서명). OSTEP은 시스템이 이미 내린 접근 결정을 기억해 두는 자료도 credential이라 부른다(세션이 그런 예다).

비밀번호 하나로는 부족하다. 사람은 같은 비밀번호를 여러 사이트에 쓴다.

- 다른 사이트에서 새어 나간 아이디·비밀번호 목록을 그대로 대입하는 공격이 *크리덴셜 스터핑(credential stuffing)* 이다.
- 23andMe의 SEC 공시(8-K/A, 2023-12-01)는 공격자가 "다른 사이트에서 이미 유출된 것과 같은 아이디·비밀번호"를 쓴 계정, 전체의 약 0.1%에 접근했다고 밝혔다. 약 1.4만 계정·약 690만 프로필이라는 숫자는 공시가 아니라 보도(2차)에 나온다.

쉬운 예: 은행 창구다.
- 통장 비밀번호(아는 것)만으로는 부족해서, 신분증(가진 것)이나 얼굴 대조(그 사람 자체)를 함께 본다.
- 하나가 새어도 다른 하나가 막는다. 이것이 다중 요소 인증이다.

## 동작·원리

### 1. 인증 요소 세 갈래와 MFA

```text
  아는 것 (knowledge)       가진 것 (possession)            그 사람 자체 (inherence)
  비밀번호·PIN              OTP 앱의 비밀 키, 보안 키,       지문·얼굴
                            휴대폰(푸시·SMS)                (보통 기기 안에서만 대조 → 기기 잠금 해제)
         \                         |                              /
          └──────── 서로 다른 갈래 2개 이상 = MFA(다중 요소 인증) ─────┘
  비밀번호 + 비밀 질문 = 둘 다 "아는 것" → MFA가 아니다
```

- OSTEP 54장은 이를 "what you know / what you have / what you are"로 나눈다.
- *MFA(multi-factor authentication)*: 서로 다른 갈래의 요소를 둘 이상 요구하는 인증.
- 요소가 많다고 다 같은 강도가 아니다. NIST SP 800-63B-4(2025-07 최종판)의 구분이 실무 기준이다.
  - OTP와 out-of-band(푸시·SMS)처럼 사람이 값을 옮겨 적거나 승인하는 방식은 **피싱 저항(phishing-resistant)이 아니다**(§3.2.5). 가짜 사이트에 OTP를 입력하면 공격자가 그 값을 바로 진짜 사이트에 쓴다.
  - 피싱 저항으로 인정되는 것은 채널 바인딩(클라이언트 인증 TLS)과 검증자 이름 바인딩(WebAuthn)이다(§3.2.5).
  - 전화망(PSTN) 경유 SMS·음성 OTP는 "restricted" 등급이다(§3.1.3.3, 요건은 §3.2.9). 쓸 수는 있지만 위험을 알리고 대안을 제공해야 한다.

### 2. 로그인 한 번의 흐름

```text
  클라이언트                         검증자(서버)
  ── ① id, password ─────────────>  ② 저장된 salt로 느린 KDF 계산 → 저장값과 상수 시간 비교 (08번)
                                      실패 → 실패 횟수 +1 (계정·IP별)          ← 남용 제한
  <─ ③ "2차 요소 필요" ────────────
  ── ④ TOTP 6자리 / WebAuthn 서명 ─>  ⑤ 검증 + 같은 값 재사용 거부
  <─ ⑥ 새 세션 ID 쿠키 ─────────────  ⑦ 인증 수준이 바뀌었으니 세션 ID를 새로 발급 (11번)
```

- ②는 비밀번호 저장(08번)의 몫이다. 이 노트는 그 앞뒤, 즉 "무엇을 몇 개 확인하고 어떻게 실패를 다루나"를 본다.
- 실패 처리 규칙(NIST SP 800-63B-4 §3.2.2): 한 계정의 한 인증 수단에 대해 연속 실패를 **100회 이하**로 제한해야 한다(SHALL). 그 전에 봇 탐지 과제, 실패할수록 늘어나는 대기, 위험 기반 판단을 함께 쓸 수 있다.
- RFC 4226 §7.3도 OTP 검증 서버에 시도 횟수 제한(throttling)을 권하고, 지연·잠금이 **로그인 세션을 가로질러** 적용돼야 한다고 적는다(MUST). 병렬 세션으로 나눠 찍으면 세션별 제한은 소용없다.

### 3. HOTP·TOTP — HMAC에 카운터를 넣고 잘라 낸다

```text
  공유 비밀 K (등록 때 QR로 전달)          카운터 C (HOTP)  또는  T = floor((지금 − T0) / X)  (TOTP)
        │                                         │                    T0 = 0, X = 30초(권장 기본)
        └────────────── HMAC(K, C를 8바이트 빅엔디언) ──────────────┘
                               │  20바이트(SHA-1)
                 동적 절단: 마지막 바이트 하위 4비트 = offset(0~15)
                               │  offset부터 4바이트, 최상위 비트 버림 → 31비트 정수
                         mod 10^자릿수  →  "287082"
```

- *HOTP*(RFC 4226): 카운터 기반 일회용 비밀번호. 버튼을 누를 때마다 카운터가 하나 오른다.
- *TOTP*(RFC 6238): 카운터 대신 "30초 칸의 번호" T를 넣은 HOTP. 앱과 서버가 시계만 맞으면 같은 값을 계산한다.
- 최상위 비트를 버리는 이유: 부호 있는/없는 나머지 연산이 프로세서마다 달라서다(RFC 4226 §5.3).
- 자릿수는 최소 6이다(RFC 4226 §5.3 MUST, NIST SP 800-63B-4 §3.1.4.1).
- 시계 오차 처리(RFC 6238 §5.2·§6)
  - 네트워크 지연용 허용 칸은 "최대 한 칸"을 권한다(RECOMMEND).
  - 같은 칸 안에서 이미 성공한 OTP가 다시 오면 **받아서는 안 된다**(MUST NOT). 서버는 "마지막으로 쓴 T"를 저장해야 한다.

실험(OpenJDK 21.0.12 temurin, 2026-10-07) — RFC 6238 부록 B 벡터를 `javax.crypto.Mac`만으로 재현:

```text
  time        SHA1      SHA256(32B) SHA512(64B) | SHA256(20B키)
  59          94287082  46119246    90693936    | 32247374
  1111111109  07081804  68084774    25091201    | 34756375
  1111111111  14050471  67062674    99943326    | 74584430
  1234567890  89005924  91819424    93441116    | 42829826
  2000000000  69279037  90698825    38618901    | 78428693
  20000000000 65353130  77737706    47863826    | 24142410
  HOTP 6자리 count 0..2 = 755224 287082 359152
```

- 왼쪽 세 열의 18개 값이 부록 B 표와 모두 같다. 마지막 줄은 RFC 4226 부록 D(755224, 287082, 359152)와 같다.
- 오른쪽 열이 함정이다. 부록 B 본문은 비밀을 "12345678901234567890"(20바이트) 하나로 적지만, SHA-256·SHA-512 값은 32·64바이트로 늘린 비밀로 계산한 것이다. RFC 6238 부록 A 참조 코드의 `seed32`·`seed64`가 그 값이고, 승인된 정오표 2866이 이를 확인한다. 20바이트 키로 SHA-256을 돌리면 다른 값(32247374)이 나온다.

### 4. WebAuthn — 출처에 묶인 키 쌍으로 서명한다

```text
  등록                                              인증
  서버 ── challenge, rp.id="bank.example" ──>       서버 ── 새 challenge ──────────────>
  브라우저 → 인증기: rp.id 전용 키 쌍 생성            브라우저 → 인증기: rp.id의 키로 서명
  <── 공개키 + credential ID ─────────────           <── 서명( authenticatorData(rpIdHash, 플래그, 카운터)
  서버: 공개키 저장(비밀 아님)                                 ‖ hash(clientDataJSON{challenge, origin}) )
                                                    서버: origin·rpIdHash·challenge 확인 + 공개키로 서명 검증

  피싱 사이트 bank-login.example 에서는?  브라우저가 origin을 그대로 적고, 인증기는 rp.id가 다른 키를 내주지 않는다
                                         → 가짜 사이트가 받은 서명은 진짜 사이트에서 통하지 않는다
```

- *WebAuthn*: 브라우저 API로 공개키 자격 증명을 만들고 쓰는 W3C 표준(Level 2 권고 2021-04-08, Level 3 권고 2026-08-25).
- *패스키(passkey)*: 발견 가능한(discoverable) WebAuthn 자격 증명의 다른 이름(L3 §4 용어). 아이디 입력 없이도 인증기가 그 RP의 자격 증명을 찾아 쓴다. 여러 기기에 동기화되는 것과 한 기기에 묶인 것이 있다.
- 피싱 저항의 근거는 두 겹이다.
  - 자격 증명은 그 RP(relying party)에 속한 출처에서만 쓸 수 있다. 이 범위 제한은 브라우저와 인증기가 함께 강제한다(WebAuthn L3 §1).
  - 서명 대상에 브라우저가 채운 `origin`이 들어간다. 사람이 값을 옮겨 적는 단계가 없다.
- 서버가 가진 것은 공개키뿐이다. 서버 DB가 새도 로그인에 쓸 비밀이 나가지 않는다. 비밀번호·TOTP 비밀 키와 다른 점이다.
- 서명 카운터: 인증기 데이터의 카운터를 저장해 두면, 둘 중 하나라도 0이 아니면서 새 값이 저장값 **이하**일 때 복제 의심 신호로 쓸 수 있다(L3 §6.1.1). 같은 절은 카운터를 구현하지 않은 인증기가 값을 항상 0으로 둔다고 적는다. 그래서 카운터는 단독 판정 근거로 쓰지 않는다. 동기화 패스키가 실제로 0을 보내는지는 제품마다 다르다 `[?]`.

### 5. 깨지는 세 갈래

| 공격 | 원리 | 보이는 형태 | 막는 쪽 |
|---|---|---|---|
| 크리덴셜 스터핑 | 다른 곳에서 샌 id·비밀번호 쌍 대입 | 로그인 실패율 급등, 다수 IP·소수 시도/IP, 성공 로그인 중 낯선 기기 | 유출 비밀번호 차단 목록, MFA, 남용 제한 |
| MFA 푸시 피로 | 비밀번호를 가진 공격자가 승인 요청을 계속 보냄 → 사용자가 결국 누름 | 한 계정에 짧은 시간 푸시 수십 건, 승인 직후 낯선 위치 세션 | 푸시 횟수 제한(SP 800-63B-4 §3.1.3.2 SHOULD), 번호 대조, 피싱 저항 인증기 |
| 계정 열거 | 실패 메시지·응답 시간·가입/재설정 응답이 계정 유무에 따라 다름 | "존재하지 않는 계정" 문구, 없는 계정이 유난히 빠른 응답 | 같은 메시지 + 같은 비용 경로 |

- 푸시 피로의 공개 사례: Uber 공식 발표(2022-09-19)는 공격자가 외주 직원 비밀번호를 (악성코드 감염 기기 경유로 유출된 것을 구매했을 가능성이 높다고) 얻은 뒤 로그인을 반복했고, 직원이 2단계 승인 요청을 "결국 하나 수락"했다고 적었다.
- 계정 열거 실험(OpenJDK 21.0.12 temurin, 2026-10-07) — 로컬 예제 로그인 함수, PBKDF2-HMAC-SHA256 10만 회(예시 값), 계정당 15회 측정, 3회 반복(아래 네 줄은 그중 한 번, 괄호는 별도 재실행 3회까지 합친 범위):

```text
  취약 id=alice   msg="비밀번호가 틀렸습니다"                  중앙값 90.4 ms
  취약 id=nobody  msg="존재하지 않는 계정입니다"                중앙값 0.0 ms
  고침 id=alice   msg="아이디 또는 비밀번호가 올바르지 않습니다"  중앙값 93.9 ms
  고침 id=nobody  msg="아이디 또는 비밀번호가 올바르지 않습니다"  중앙값 94.7 ms
  (6회 실행 합산: 취약판 alice 83.3~96.7 ms / nobody 0.0 ms, 고침판 두 계정 모두 81.1~95.4 ms)
```

- 취약판은 메시지로도, 시간으로도 계정 유무를 드러낸다. 없는 계정은 KDF를 건너뛰어 0.0 ms다.
- 고친 판은 같은 메시지를 내고, 없는 계정에도 더미 해시로 같은 비용의 KDF를 돌린다. 두 계정의 중앙값 차이(한 실행 안에서 0.8~3.4 ms)가 실행 간 흔들림(약 14 ms) 안에 든다.
- 이 측정은 한 컨테이너 안의 함수 호출 시간이다. 네트워크 너머 측정은 노이즈가 훨씬 크지만, 0 ms 대 90 ms 같은 차이는 반복 측정으로 드러날 수 있다.

## 쓰이는 자료구조·알고리즘

- **HMAC** — HOTP·TOTP의 몸통이다. 비밀 키와 카운터를 섞어 예측 못 하는 값을 만든다. 원리는 [foundations/security/hmac.md](../../foundations/security/hmac.md)와 [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md).
- **동적 절단 + 나머지 연산** — 20바이트 출력의 위치를 출력 자체(마지막 바이트)로 고르고, 31비트 정수를 `mod 10^d`로 줄인다. 6자리면 받아 주는 값이 하나일 때 추측 성공 확률이 시도당 1/10^6이다. 허용 칸이 두 개(현재 + 직전)면 약 2/10^6이다. 그래서 시도 횟수 제한이 함께 있어야 한다(RFC 4226 §7.3).
- **카운터·시간 칸** — TOTP의 T는 `floor(시각 / 30)`이다. 시계가 어긋나면 칸이 달라진다. 시계 동기화는 [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md).
- **전자서명(챌린지-응답)** — WebAuthn은 서버가 준 무작위 challenge에 개인키로 서명하게 해서 재전송을 막는다. 서명은 [06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md).
- **해시 접두 조회(k-익명성)** — 유출 비밀번호 목록 조회 서비스(Have I Been Pwned Pwned Passwords)는 SHA-1 해시의 앞 5글자만 보내고, 그 접두로 시작하는 해시 목록을 받아 로컬에서 대조한다. 비밀번호 자체를 보내지 않는다. 해시 함수는 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).
- **토큰 버킷·카운터 맵** — 계정·IP별 실패 횟수를 세고 속도를 제한한다. [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md).

## 적용 — 풀어나가는 법

### 1. TOTP 검증 — 창 한 칸, 재사용 거부

취약 예:

```java
// 창 ±10칸(±5분), 이미 쓴 코드 재사용 허용, 문자열 equals 비교
boolean verify(byte[] key, String code, long now) {
    long t = now / 30;
    for (long d = -10; d <= 10; d++)
        if (totp(key, t + d).equals(code)) return true;
    return false;
}
```

고친 예:

```java
// RFC 6238 §5.2: 지연 허용은 최대 한 칸, 같은 OTP 두 번째 수락 금지
boolean verify(UserOtp u, String code, long now) {
    long t = Math.floorDiv(now, 30L);
    for (long d = -1; d <= 0; d++) {                       // 현재 칸과 직전 칸만
        long step = t + d;
        if (step <= u.lastUsedStep()) continue;           // 이미 성공한 칸 이하 → 재사용
        byte[] expect = totp(u.key(), step).getBytes(StandardCharsets.US_ASCII);
        if (MessageDigest.isEqual(expect, code.getBytes(StandardCharsets.US_ASCII))) {
            u.markUsed(step);                             // 원자적으로 저장(동시 요청 대비)
            return true;
        }
    }
    u.countFailure();                                     // 계정 단위 실패 횟수 → 잠금·지연
    return false;
}
```

- `lastUsedStep` 갱신은 조건부 UPDATE(`WHERE last_used_step < ?`)로 한다. 같은 코드를 두 요청이 동시에 내도 하나만 성공한다.
- TOTP 비밀 키는 서버가 복호화할 수 있어야 한다(해시로 저장 불가). 그래서 키 관리(09번)로 암호화해 저장한다.

### 2. 로그인 실패 응답을 하나로

취약 예:

```java
if (user == null) throw new ResponseStatusException(NOT_FOUND, "존재하지 않는 계정");
if (!encoder.matches(raw, user.hash())) throw new ResponseStatusException(UNAUTHORIZED, "비밀번호 오류");
```

고친 예:

```java
// 없는 계정도 같은 비용의 해시 비교를 거치고, 같은 상태 코드·메시지를 낸다
String hash = (user != null) ? user.hash() : DUMMY_HASH;   // DUMMY_HASH = 앱 시작 때 encoder.encode(임의 문자열)
boolean ok = encoder.matches(raw, hash) && user != null;
if (!ok) throw new ResponseStatusException(UNAUTHORIZED, "아이디 또는 비밀번호가 올바르지 않습니다");
```

- Spring Security는 이것을 기본으로 한다(소스 기준).
  - `AbstractUserDetailsAuthenticationProvider.hideUserNotFoundExceptions` 기본값 `true` → 없는 계정도 `BadCredentialsException`.
  - `DaoAuthenticationProvider`는 `"userNotFoundPassword"`를 미리 인코딩해 두고, 계정이 없을 때 그 값과 비교한다(`mitigateAgainstTimingAttack`).
- 같은 정보가 다른 문으로 샌다. 회원 가입("이미 가입된 이메일")과 비밀번호 재설정("메일을 보냈습니다" vs "없는 이메일")도 같은 응답으로 맞춘다. 가입은 "확인 메일을 보냈습니다"로 통일하고, 이미 있는 계정이면 그 메일 안에서 안내한다.

### 3. MFA 푸시 승인 — 횟수 제한과 번호 대조

```text
  나쁜 설계: 로그인 시도마다 "승인/거절" 푸시를 무제한으로 보낸다
  고친 설계: ① 마지막 성공 이후 푸시 수 상한(SP 800-63B-4 §3.1.3.2)
             ② 로그인 화면에 무작위 번호 표시 → 휴대폰에서 그 번호를 입력해야 승인(§3.1.3.2: 최소 6자리 십진수 또는 동등, SHALL)
             ③ 거절이 연달아 오면 계정 잠그고 보안팀 알림
             ④ 관리자·운영 계정은 WebAuthn 보안 키로 (피싱 저항)
```

- 번호 대조는 "화면 앞에 있는 사람"과 "휴대폰을 든 사람"이 같다는 증거를 하나 더 받는 방식이다. 피싱 프록시가 번호까지 중계하면 막지 못한다. 그래서 끝 단계는 WebAuthn이다.

### 4. 비밀번호 정책은 길이와 차단 목록으로

- NIST SP 800-63B-4 §3.1.1.2
  - 비밀번호만으로 인증하면 최소 15자, MFA의 한 요소로 쓰면 최소 8자(SHALL).
  - 다른 조합 규칙(대문자·특수문자 강제)을 두지 않는다(SHALL NOT).
  - 주기적 변경을 요구하지 않는다. 유출 정황이 있을 때만 바꾸게 한다(SHALL NOT, 예외 조건 명시).
  - 흔한·예상 가능한·유출된 비밀번호 차단 목록과 대조한다.
- 저장 방식(salt·느린 KDF)은 [08-password-storage-and-kdf](../08-password-storage-and-kdf/2-summary.md).

### 5. 로그로 진단한다

```text
  크리덴셜 스터핑 의심
  - 로그인 실패율: 평소 5% → 70% (예시)
  - 실패 요청의 IP 수 급증, IP당 시도 수는 적음(1~3회)       → IP 단위 제한만으로는 안 걸린다
  - 실패 계정 중 "존재하지 않는 계정" 비율이 높음            → 다른 곳에서 가져온 목록
  - 성공 로그인 직후 결제수단·이메일 변경                    → 침해 계정 후속 행동
```

- 로그에 비밀번호·OTP·`Authorization` 헤더를 남기지 않는다(26번).

## 장애 시나리오와 대처

### 1. 크리덴셜 스터핑 — 로그인 폭주와 계정 탈취

- **현상**: 로그인 API 트래픽이 평소의 수십 배로 오르고, 며칠 뒤 "내 계정으로 누가 주문했다"는 문의가 온다.
- **보이는 형태**: 로그인 `401` 비율 급등. 실패 요청이 수천 IP에 흩어져 IP당 몇 건뿐이다. 성공한 소수 계정에서 낯선 기기·국가 세션.
- **원인**: 사용자가 다른 사이트에서 쓴 비밀번호를 재사용했다. 이 서비스의 저장 방식이 안전해도 막지 못한다.
- **대처**
  - 즉시: 이상 성공 세션 강제 종료, 해당 계정 비밀번호 재설정 요구, 로그인에 봇 탐지 과제.
  - 근본: MFA(가능하면 패스키), 가입·변경 시 유출 비밀번호 차단 목록, 계정 단위 + 전역 실패율 기반 제한.

### 2. MFA 푸시 피로 — 사용자가 결국 승인했다

- **현상**: 한 직원 계정으로 사내 시스템에 정상 로그인 기록이 있는데, 본인은 기억하지 못한다.
- **보이는 형태**: 인증 로그에 같은 계정 푸시 요청이 짧은 시간에 수십 건, 대부분 거절·무응답, 마지막 하나 승인. 승인 위치와 로그인 IP의 지역이 다르다.
- **원인**: 비밀번호는 이미 공격자 손에 있었다. 2차 요소가 "누르기만 하면 되는" 승인이라 피로와 착각에 약하다.
- **대처**: 푸시 횟수 상한, 번호 대조, 연속 거절 시 잠금·알림. 특권 계정은 WebAuthn 보안 키로 바꾼다. 사고 대응에서는 승인 직후 세션·토큰을 전부 폐기한다(17번).

### 3. 계정 열거 — 로그인·가입·재설정 응답이 계정 유무를 알려 준다

- **현상**: 보안 점검이나 버그 바운티에서 "이메일 존재 여부를 알 수 있다"는 보고를 받는다.
- **보이는 형태**: 없는 계정은 `404`·"존재하지 않는 계정", 있는 계정은 `401`·"비밀번호 오류". 메시지가 같아도 없는 계정의 응답만 유난히 빠르다(위 실험: 0.0 ms vs 약 90 ms).
- **원인**: 계정 조회 실패에서 일찍 반환하고, 해시 비교를 건너뛴다.
- **대처**: 같은 상태 코드·메시지, 더미 해시로 같은 비용, 가입·재설정 응답도 통일. 열거 자체를 막지 못하는 경우(공개 프로필 URL 등)에는 남용 제한으로 대량 수집 속도를 늦춘다(16번).

### 4. TOTP가 특정 사용자만 계속 틀린다

- **현상**: 일부 사용자가 "OTP가 맞는데 거절된다"고 한다.
- **보이는 형태**: 그 사용자들의 실패가 시간과 무관하게 지속된다. 서버 로그에 기대값과 받은 값이 한 칸(30초) 어긋나 있다.
- **원인 후보**
  - 휴대폰 시계가 수동 설정이라 30초 이상 틀렸다. 또는 서버 NTP가 멈춰 서버 시계가 밀렸다.
  - 앱과 서버의 알고리즘·자릿수·키 길이 설정이 다르다. 예: SHA-256을 쓰면서 RFC 6238 부록 B의 20바이트 키로 테스트해 "표와 다르다"며 엉뚱한 곳을 고친다(위 실험의 오른쪽 열).
- **대처**: 서버 시계 상태부터 확인한다(`chronyc tracking`). 허용 칸을 넓히기보다 사용자 기기 시계 자동 설정을 안내한다. RFC 6238 §6처럼 "마지막 성공 시 관측한 어긋남"을 사용자별로 기록해 재동기화하는 방법도 있다.

### 5. 인증 서버 장애 때 "일단 통과"

- **현상**: MFA 공급자 장애 중에 2단계 없이 로그인이 됐다.
- **보이는 형태**: 장애 시간대 로그인 성공 로그에 `mfa=skipped`. 코드에 `catch (Exception e) { return true; }`.
- **원인**: 외부 검증 실패를 허용으로 처리한 fail-open이다([01-security-principles](../01-security-principles/2-summary.md)).
- **대처**: 실패는 거부로 처리한다(fail-closed). 가용성은 대체 수단(백업 코드, 두 번째 인증기 등록)으로 확보한다. 장애 중 우회가 필요하면 사람이 승인하는 절차와 기록을 둔다.

## 핵심 문장

- 인증은 "주장한 신원이 맞나", 인가는 "그 신원이 이것을 해도 되나"다. 둘은 다른 단계다.
- MFA는 서로 다른 갈래(아는 것·가진 것·그 사람 자체)의 요소 두 개 이상이다. 같은 갈래 두 개는 MFA가 아니다.
- TOTP는 `HMAC(K, floor(시각/30))`을 잘라 6~8자리로 만든 값이다. 서버는 허용 칸을 좁히고, 이미 성공한 칸(과 그 이전 칸)의 OTP를 다시 받지 않는다.
- OTP와 푸시는 사람이 값을 옮기거나 승인하므로 피싱 저항이 아니다. WebAuthn은 출처에 묶인 키로 서명해 피싱 사이트에서 받은 응답이 쓸모없다.
- 로그인 실패는 계정 유무와 상관없이 같은 메시지·같은 비용으로 응답한다.
- 실패 횟수 제한은 계정 단위로, 세션을 가로질러 건다.

## 관련 주제·근거

- 선행
  - [08-password-storage-and-kdf](../08-password-storage-and-kdf/2-summary.md) — salt·느린 KDF, 비밀번호 저장
  - [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md), 원본 [foundations/security/hmac.md](../../foundations/security/hmac.md) — HMAC
- 후속·연결
  - [11-sessions-and-cookie-security](../11-sessions-and-cookie-security/2-summary.md) — 인증 뒤 상태를 어떻게 들고 다니나
  - [12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md), [14-oauth2-and-oidc](../14-oauth2-and-oidc/2-summary.md) — 인증 결과를 토큰으로, 다른 서비스에 위임
  - [15-access-control-models](../15-access-control-models/2-summary.md) — 인가
  - [16-identifiers-and-enumeration](../16-identifiers-and-enumeration/2-summary.md) — 열거와 식별자
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md), [network/32-mtls-and-cert-operations](../../network/32-mtls-and-cert-operations/2-summary.md) — 채널 바인딩(클라이언트 인증 TLS)
  - [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) — 남용 제한, [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md) — 시계
- 1차 출처
  - OSTEP 54 Authentication (Peter Reiher) — what you know / have / are <https://pages.cs.wisc.edu/~remzi/OSTEP/security-authentication.pdf>
  - RFC 4226 HOTP — §5.3 동적 절단·최소 6자리, §7.3 시도 제한(세션 가로질러 MUST), 부록 D 테스트 값 <https://www.rfc-editor.org/rfc/rfc4226>
  - RFC 6238 TOTP — §4 T0=0·X=30, §5.2 지연 허용 최대 한 칸·재사용 MUST NOT, §6 재동기화, 부록 B 테스트 벡터 <https://www.rfc-editor.org/rfc/rfc6238> · 정오표 2866(Verified, SHA-256/512 키 길이) <https://www.rfc-editor.org/errata/eid2866>
  - NIST SP 800-63B-4 (2025-07 최종판) — §3.1.1.2 비밀번호, §3.1.3.2 푸시 횟수 제한, §3.1.3.3·§3.2.9 PSTN restricted, §3.1.4 OTP, §3.2.2 실패 100회 이하, §3.2.5 피싱 저항 <https://pages.nist.gov/800-63-4/sp800-63b.html> · PDF <https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B-4.pdf>
  - W3C Web Authentication Level 3 (권고 2026-08-25 — §1 범위 제한, §6.1.1 서명 카운터), Level 2 (권고 2021-04-08) <https://www.w3.org/TR/webauthn-3/>
  - OWASP Authentication Cheat Sheet · Credential Stuffing Prevention Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html>
  - Have I Been Pwned API v3 — Pwned Passwords 범위 조회 <https://haveibeenpwned.com/API/v3#PwnedPasswords>
  - Spring Security 소스(main, 2026-10-07 조회) — `AbstractUserDetailsAuthenticationProvider.hideUserNotFoundExceptions = true`, `DaoAuthenticationProvider.mitigateAgainstTimingAttack`
- 사고 원문
  - 23andMe Form 8-K/A (2023-12-01) — 0.1% 계정, 재사용 비밀번호 <https://www.sec.gov/Archives/edgar/data/1804591/000119312523287449/d242666d8ka.htm>
  - Uber Security update (2022-09-19) — 반복 승인 요청 끝에 수락 <https://www.uber.com/newsroom/security-update/>
- 실험(2026-10-07, eclipse-temurin:21-jdk = OpenJDK 21.0.12, `--network none`)
  - RFC 6238 부록 B 18개 값·RFC 4226 부록 D 재현, 20바이트 키로 SHA-256을 돌리면 값이 달라짐
  - 로컬 로그인 함수의 계정 열거: 메시지 차이와 0.0 ms vs 약 90 ms, 고친 판은 같은 메시지·같은 비용
